// GeoJSON 자치구 경계를 SVG 경로로 그린다. 서울 정도 범위는 위도 보정한 평면 투영으로 충분하다.

const SVG_NS = "http://www.w3.org/2000/svg";
const WIDTH = 800;
const PADDING = 12;

function rings(geometry) {
  return geometry.type === "Polygon" ? geometry.coordinates : geometry.coordinates.flat();
}

function createProjection(features) {
  let minLon = Infinity;
  let maxLon = -Infinity;
  let minLat = Infinity;
  let maxLat = -Infinity;

  for (const f of features) {
    for (const ring of rings(f.geometry)) {
      for (const [lon, lat] of ring) {
        minLon = Math.min(minLon, lon);
        maxLon = Math.max(maxLon, lon);
        minLat = Math.min(minLat, lat);
        maxLat = Math.max(maxLat, lat);
      }
    }
  }

  const kx = Math.cos((((minLat + maxLat) / 2) * Math.PI) / 180);
  const scale = (WIDTH - PADDING * 2) / ((maxLon - minLon) * kx);
  const height = (maxLat - minLat) * scale + PADDING * 2;

  const project = ([lon, lat]) => [
    PADDING + (lon - minLon) * kx * scale,
    PADDING + (maxLat - lat) * scale,
  ];

  return { project, height };
}

function pathData(geometry, project) {
  return rings(geometry)
    .map((ring) =>
      ring
        .map((pt, i) => {
          const [x, y] = project(pt);
          return `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
        })
        .join("") + "Z",
    )
    .join("");
}

// 가장 큰 고리의 면적 중심을 이름표 위치로 쓴다.
function labelPoint(geometry, project) {
  let best = null;

  for (const ring of rings(geometry)) {
    const pts = ring.map(project);
    let area = 0;
    let cx = 0;
    let cy = 0;
    for (let i = 0; i < pts.length - 1; i++) {
      const [x0, y0] = pts[i];
      const [x1, y1] = pts[i + 1];
      const cross = x0 * y1 - x1 * y0;
      area += cross;
      cx += (x0 + x1) * cross;
      cy += (y0 + y1) * cross;
    }
    area /= 2;
    if (!best || Math.abs(area) > Math.abs(best.area)) {
      best = { area, x: cx / (6 * area), y: cy / (6 * area) };
    }
  }

  return [best.x, best.y];
}

// 면적 중심이 이웃 구와 겹치거나 한쪽으로 쏠리는 곳만 손으로 옮긴다 (SVG 좌표 기준).
const LABEL_NUDGE = {
  중구: [0, 4],
  종로구: [0, 10],
  용산구: [0, -4],
};

function el(name, attrs = {}) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}

export function drawMap(svg, geojson, { onHover, onSelect }) {
  const { project, height } = createProjection(geojson.features);
  svg.setAttribute("viewBox", `0 0 ${WIDTH} ${height.toFixed(0)}`);

  const shapes = el("g");
  const outline = el("path", { class: "gu-outline", visibility: "hidden" });
  const labels = el("g");
  const byName = new Map();

  for (const feature of geojson.features) {
    const name = feature.properties.name;
    const d = pathData(feature.geometry, project);

    const path = el("path", { d, class: "gu", tabindex: "-1" });
    path.addEventListener("mouseenter", () => onHover(name));
    path.addEventListener("mouseleave", () => onHover(null));
    path.addEventListener("click", () => onSelect(name));
    shapes.append(path);

    let [x, y] = labelPoint(feature.geometry, project);
    const [dx, dy] = LABEL_NUDGE[name] ?? [0, 0];
    x += dx;
    y += dy;

    const label = el("text", { class: "gu-label", x: x.toFixed(1), y: (y - 7).toFixed(1) });
    label.textContent = name;
    const rank = el("text", { class: "gu-rank", x: x.toFixed(1), y: (y + 8).toFixed(1) });
    labels.append(label, rank);

    byName.set(name, { path, label, rank, d });
  }

  svg.append(shapes, outline, labels);

  return {
    paint(name, { fill, labelColor, rankText, title }) {
      const item = byName.get(name);
      item.path.style.fill = fill;
      item.label.style.fill = labelColor;
      item.rank.style.fill = labelColor;
      item.rank.textContent = rankText;
      item.path.setAttribute("aria-label", title);
    },

    focus(name) {
      svg.classList.toggle("has-focus", Boolean(name));
      for (const [n, item] of byName) item.path.classList.toggle("is-active", n === name);
      if (name) {
        outline.setAttribute("d", byName.get(name).d);
        outline.setAttribute("visibility", "visible");
      } else {
        outline.setAttribute("visibility", "hidden");
      }
    },
  };
}
