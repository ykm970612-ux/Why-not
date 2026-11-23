import { TABS, DEFAULT_TAB } from "./config.js";
import { greenAt, labelColorAt, legendGradient } from "./color.js";
import { drawMap } from "./map.js";

const $ = (sel) => document.querySelector(sel);

const state = {
  tab: TABS[location.hash.slice(1)] ? location.hash.slice(1) : DEFAULT_TAB,
  hovered: null,
  selected: null,
  ranked: [],
};

const fmtScore = (v) => (v * 100).toFixed(1);

function formatMetric(row, metric) {
  const value = row[metric.key] * (metric.scale ?? 1);
  return value.toLocaleString("ko-KR", {
    minimumFractionDigits: metric.digits,
    maximumFractionDigits: metric.digits,
  });
}

async function loadJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path} 불러오기 실패 (${res.status})`);
  return res.json();
}

function rankRows(rows, key) {
  const sorted = [...rows].sort((a, b) => b[key] - a[key]);
  const min = sorted.at(-1)[key];
  const max = sorted[0][key];
  return sorted.map((row, i) => ({
    row,
    name: row["자치구명"],
    rank: i + 1,
    score: row[key],
    t: max === min ? 1 : (row[key] - min) / (max - min),
  }));
}

function activeName() {
  return state.hovered ?? state.selected;
}

function renderTabs() {
  for (const btn of document.querySelectorAll(".tab")) {
    btn.setAttribute("aria-selected", String(btn.dataset.tab === state.tab));
  }
  $("#tab-caption").textContent = TABS[state.tab].caption;
}

function renderMap(map) {
  for (const item of state.ranked) {
    map.paint(item.name, {
      fill: greenAt(item.t),
      labelColor: labelColorAt(item.t),
      rankText: `${item.rank}위`,
      title: `${item.name} ${item.rank}위, ${fmtScore(item.score)}점`,
    });
  }

  const scores = state.ranked.map((d) => d.score);
  $("#legend-min").textContent = `${fmtScore(Math.min(...scores))}점`;
  $("#legend-max").textContent = `${fmtScore(Math.max(...scores))}점`;
}

function renderRanking() {
  const list = $("#rank-list");
  list.replaceChildren(
    ...state.ranked.map((item) => {
      const li = document.createElement("li");
      li.innerHTML = `
        <button class="rank-item" type="button" data-name="${item.name}">
          <span class="rank-num">${item.rank}</span>
          <span class="rank-name">${item.name}</span>
          <span class="rank-bar"><span style="transform: scaleX(${item.score.toFixed(3)}); background-color: ${greenAt(item.t)}"></span></span>
          <span class="rank-value">${fmtScore(item.score)}</span>
        </button>`;
      return li;
    }),
  );
}

function renderDetail() {
  const tab = TABS[state.tab];
  const item = state.ranked.find((d) => d.name === activeName()) ?? state.ranked[0];

  const metrics = tab.metrics
    .map(
      (m) => `
      <div class="metric">
        <dt>${m.label}</dt>
        <dd>${formatMetric(item.row, m)}${m.unit ? `<span>${m.unit}</span>` : ""}</dd>
      </div>`,
    )
    .join("");

  $("#detail").innerHTML = `
    <div class="detail-top">
      <h2 class="detail-name">${item.name}</h2>
      <span class="detail-rank">${tab.label} ${item.rank}위 / 25</span>
    </div>
    <p class="detail-score">${fmtScore(item.score)}<small>점</small></p>
    <dl class="metric-list">${metrics}</dl>`;
}

function renderFocus(map) {
  const name = activeName();
  map.focus(name);
  for (const btn of document.querySelectorAll(".rank-item")) {
    btn.classList.toggle("is-active", btn.dataset.name === name);
  }
  renderDetail();
}

async function main() {
  const [rows, geojson] = await Promise.all([
    loadJson("data/districts_2025.json"),
    loadJson("data/seoul_gu.geojson"),
  ]);

  const setHover = (name) => {
    state.hovered = name;
    renderFocus(map);
  };
  const toggleSelect = (name) => {
    state.selected = state.selected === name ? null : name;
    renderFocus(map);
  };

  const map = drawMap($("#map"), geojson, { onHover: setHover, onSelect: toggleSelect });
  $("#legend-bar").style.background = legendGradient();

  const render = () => {
    state.ranked = rankRows(rows, TABS[state.tab].scoreKey);
    renderTabs();
    renderMap(map);
    renderRanking();
    renderFocus(map);
  };

  for (const btn of document.querySelectorAll(".tab")) {
    btn.addEventListener("click", () => {
      state.tab = btn.dataset.tab;
      history.replaceState(null, "", `#${state.tab}`);
      render();
    });
  }

  window.addEventListener("hashchange", () => {
    const tab = location.hash.slice(1);
    if (TABS[tab] && tab !== state.tab) {
      state.tab = tab;
      render();
    }
  });

  const list = $("#rank-list");
  list.addEventListener("mouseover", (e) => {
    const btn = e.target.closest(".rank-item");
    if (btn && btn.dataset.name !== state.hovered) setHover(btn.dataset.name);
  });
  list.addEventListener("mouseleave", () => setHover(null));
  list.addEventListener("click", (e) => {
    const btn = e.target.closest(".rank-item");
    if (btn) toggleSelect(btn.dataset.name);
  });

  render();
}

main().catch((err) => {
  $("#detail").textContent = `데이터를 불러오지 못했어요. web 폴더에서 로컬 서버로 열어 주세요. (${err.message})`;
  console.error(err);
});
