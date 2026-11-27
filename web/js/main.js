// config.js, color.js, map.js, data/data.js 를 먼저 불러온 뒤 실행된다 (index.html 의 <script> 순서).

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

function renderModal() {
  const item = state.ranked.find((district) => district.name === state.selected);
  if (!item) return;

  const row = item.row;
  const districts = window.WEB_DATA.districts;
  const average = (key) => districts.reduce((sum, district) => sum + district[key], 0) / districts.length;
  const formatNumber = (value, digits = 1) => Number(value).toLocaleString("ko-KR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });

  const statCard = (label, value, note = "") => `
    <div class="modal-stat">
      <span>${label}</span>
      <strong>${value}</strong>
      <small>${note}</small>
    </div>
  `;

  const compareBars = (metrics) => metrics.map(([label, key, unit, digits = 1]) => {
    const value = row[key];
    const mean = average(key);
    const max = Math.max(value, mean, 0.01) * 1.13;

    return `
      <div class="compare-item">
        <div class="compare-heading">
          <strong>${label}</strong>
          <span>${formatNumber(value, digits)} ${unit}</span>
        </div>
        <div class="compare-track"><span style="width:${value / max * 100}%"></span></div>
        <div class="compare-track average"><span style="width:${mean / max * 100}%"></span></div>
        <small>위: ${item.name} · 아래: 서울 25개 구 평균 ${formatNumber(mean, digits)} ${unit}</small>
      </div>
    `;
  }).join("");

  const scoreBars = (metrics) => metrics.map(([label, key]) => {
    const score = row[key] * 100;
    const width = Math.max(0, Math.min(100, score));
    return `
      <div class="score-row">
        <span>${label}</span>
        <div class="score-track"><i style="width:${width}%"></i></div>
        <strong>${formatNumber(score)}점</strong>
      </div>
    `;
  }).join("");

  let content = "";

  if (state.tab === "infra") {
    const metrics = [
      ["생활편의시설", "생활편의시설수", "개/km²"],
      ["버스정류소", "버스정류소수", "개/km²"],
      ["지하철역", "물리적_역수", "개/km²", 2],
      ["일상 의료시설", "일상의료시설수", "개/km²"],
      ["종합 의료시설", "종합의료시설수", "개/km²", 2],
    ];
    const strongest = [...metrics].sort((a, b) =>
      row[b[1]] / Math.max(average(b[1]), 0.0001) - row[a[1]] / Math.max(average(a[1]), 0.0001)
    )[0];

    content = `
      <h3>생활 인프라 비교</h3>
      <p class="modal-intro">생활편의시설·의료시설·교통시설을 서울 평균과 비교합니다.</p>
      <div class="compare-list">${compareBars(metrics)}</div>
      <p class="modal-insight">서울 평균과 비교했을 때 <b>${strongest[0]}</b> 밀도가 가장 높습니다.</p>
    `;
  } else if (state.tab === "housing") {
    const rent21 = row["환산월세_2021_만원"];
    const rent25 = row["환산월세_2025_만원"];
    const maxRent = Math.max(rent21, rent25, average("환산월세_2025_만원")) * 1.12;
    const difference = rent25 - average("환산월세_2025_만원");
    const rentComparison = Math.abs(difference) < 0.00001
      ? "서울 평균과 같은 수준"
      : `서울 평균보다 ${formatNumber(Math.abs(difference), 2)}만원 ${difference > 0 ? "높은" : "낮은"} 수준`;

    content = `
      <h3>주거비 변화</h3>
      <p class="modal-intro">2021년과 2025년 환산월세 및 변화율</p>
      <div class="modal-stats">
        ${statCard("2021년 환산월세", `${formatNumber(rent21)}만원`)}
        ${statCard("2025년 환산월세", `${formatNumber(rent25)}만원`)}
        ${statCard("2021~2025 변화율", `${formatNumber(row["변화율_2021_2025_퍼센트"])}%`)}
      </div>
      <div class="rent-chart">
        <div><span>2021</span><i style="width:${rent21 / maxRent * 100}%"></i><b>${formatNumber(rent21)}만원</b></div>
        <div><span>2025</span><i style="width:${rent25 / maxRent * 100}%"></i><b>${formatNumber(rent25)}만원</b></div>
      </div>
      <div class="modal-stats">
        ${statCard("생활물가지수", formatNumber(row["생활물가지수"]))}
        ${statCard("서울 평균 2025 환산월세", `${formatNumber(average("환산월세_2025_만원"))}만원`, "25개 구 단순 평균")}
      </div>
      <p class="modal-insight">2025년 환산월세는 ${rentComparison}입니다.</p>
    `;
  } else if (state.tab === "transit") {
    const metrics = [
      ["버스정류소", "버스정류소수", "개/km²"],
      ["지하철역", "물리적_역수", "개/km²", 2],
    ];
    const better = row["버스정류소수_정규화"] >= row["물리적_역수_정규화"]
      ? "버스정류소" : "지하철역";

    content = `
      <h3>대중교통 시설 밀도</h3>
      <p class="modal-intro">버스정류소·지하철역 밀도와 서울 평균</p>
      <div class="compare-list">${compareBars(metrics)}</div>
      <p class="modal-insight">두 교통 지표 중 <b>${better}</b> 점수가 더 높습니다.</p>
    `;
  } else {
    const metrics = [
      ["주거비", "주거비점수"],
      ["교통", "교통점수"],
      ["인프라", "인프라종합점수"],
      ["청년 집중도", "청년집중도점수"],
      ["생활환경", "생활환경점수"],
    ];
    const sorted = [...metrics].sort((a, b) => row[b[1]] - row[a[1]]);

    content = `
      <h3>종합 점수 비교</h3>
      <p class="modal-intro">주거비·교통·인프라·청년 집중도·생활환경 점수</p>
      <div class="score-list">${scoreBars(metrics)}</div>
      <div class="modal-stats">
        ${statCard("2025년 청년 1인가구", `${formatNumber(row["청년1인가구_2025"], 0)}가구`)}
        ${statCard("청년 집중도(LQ)", formatNumber(row["청년1인가구_LQ_2025"], 2))}
      </div>
      <p class="modal-insight">세부 점수 중 <b>${sorted[0][0]}</b>이(가) 가장 높고 <b>${sorted.at(-1)[0]}</b>이(가) 가장 낮습니다.</p>
    `;
  }

  $("#modal-content").innerHTML = `
    <div class="modal-kicker">${TABS[state.tab].label} 상세 정보</div>
    <h2 id="modal-title">${item.name} <span>${item.rank}위 / 25개 구</span></h2>
    <div class="modal-score">${fmtScore(item.score)}<small>점</small></div>
    ${content}
  `;
}

function main() {
  if (!window.WEB_DATA) {
    throw new Error("data/data.js 가 없습니다. python src/export_web_data.py 를 실행하세요.");
  }
  const rows = window.WEB_DATA.districts;
  const geojson = window.WEB_DATA.boundary;

  const setHover = (name) => {
    state.hovered = name;
    renderFocus(map);
  };
  const toggleSelect = (name) => {
    state.selected = state.selected === name ? null : name;
    renderFocus(map);
    if (state.selected) { renderModal(); openModal(); } else closeModal();
  };

  const map = drawMap($("#map"), geojson, { onHover: setHover, onSelect: toggleSelect });
  $("#legend-bar").style.background = legendGradient();

  const render = () => {
    state.ranked = rankRows(rows, TABS[state.tab].scoreKey);
    renderTabs();
    renderMap(map);
    renderRanking();
    renderFocus(map);
    if (state.selected) renderModal();
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

  const modal = $("#region-modal");
  const closeModal = () => { modal.hidden = true; document.body.classList.remove("modal-open"); };
  const openModal = () => { modal.hidden = false; document.body.classList.add("modal-open"); $(".region-modal").focus(); };
  $("#modal-close").addEventListener("click", closeModal);
  modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !modal.hidden) closeModal(); });
  render();
}

try {
  main();
} catch (err) {
  $("#detail").textContent = `데이터를 불러오지 못했어요. (${err.message})`;
  console.error(err);
}
