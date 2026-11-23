// 탭별로 지도 색을 칠할 점수 컬럼과, 상세 패널에 보여줄 원지표

const PER_KM2 = "개/km²";

const TABS = {
  infra: {
    label: "인프라",
    scoreKey: "인프라종합점수",
    caption: "편의점·슈퍼마켓, 버스정류소, 지하철역, 일상·종합 의료시설의 면적당 개수를 평균한 점수",
    metrics: [
      { label: "생활편의시설", key: "생활편의시설수", unit: PER_KM2, digits: 1 },
      { label: "버스정류소", key: "버스정류소수", unit: PER_KM2, digits: 1 },
      { label: "지하철역", key: "물리적_역수", unit: PER_KM2, digits: 2 },
      { label: "일상 의료시설", key: "일상의료시설수", unit: PER_KM2, digits: 1 },
      { label: "종합 의료시설", key: "종합의료시설수", unit: PER_KM2, digits: 2 },
    ],
  },
  housing: {
    label: "주거비",
    scoreKey: "주거비점수",
    caption: "2025년 환산월세가 낮고 2021년 대비 상승률이 낮을수록 높은 점수",
    metrics: [
      { label: "환산월세 2025", key: "환산월세_2025_만원", unit: "만원", digits: 1 },
      { label: "환산월세 2021", key: "환산월세_2021_만원", unit: "만원", digits: 1 },
      { label: "상승률 2021 대비", key: "변화율_2021_2025_퍼센트", unit: "%", digits: 1 },
      { label: "생활물가지수", key: "생활물가지수", unit: "", digits: 1 },
    ],
  },
  transit: {
    label: "교통",
    scoreKey: "교통점수",
    caption: "면적당 버스정류소 수와 지하철역 수(환승역은 1개로 집계)를 평균한 점수",
    metrics: [
      { label: "버스정류소", key: "버스정류소수", unit: PER_KM2, digits: 1 },
      { label: "지하철역", key: "물리적_역수", unit: PER_KM2, digits: 2 },
    ],
  },
  total: {
    label: "통합",
    scoreKey: "종합점수",
    caption: "청년 집중도, 주거비, 생활환경, 교통, 의료·편의시설을 반영한 종합 점수",
    metrics: [
      { label: "주거비", key: "주거비점수", unit: "점", digits: 1, scale: 100 },
      { label: "교통", key: "교통점수", unit: "점", digits: 1, scale: 100 },
      { label: "인프라", key: "인프라종합점수", unit: "점", digits: 1, scale: 100 },
      { label: "청년 1인가구 집중도", key: "청년집중도점수", unit: "점", digits: 1, scale: 100 },
      { label: "생활환경", key: "생활환경점수", unit: "점", digits: 1, scale: 100 },
    ],
  },
};

const DEFAULT_TAB = "infra";
