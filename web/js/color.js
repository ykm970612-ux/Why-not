// 옅은 초록 → 진한 초록. OKLab에서 섞어서 단계가 고르게 보이게 한다.

// 두 색만 섞으면 중간이 회색빛이 돌아서, 채도 있는 중간 초록을 하나 끼운다.
const STOPS = ["#edf5e6", "#7cbf86", "#1b5e3a"];

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

const toLinear = (c) => {
  c /= 255;
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
};

const fromLinear = (c) => {
  const v = c <= 0.0031308 ? c * 12.92 : 1.055 * c ** (1 / 2.4) - 0.055;
  return Math.round(Math.min(1, Math.max(0, v)) * 255);
};

function rgbToOklab([r, g, b]) {
  [r, g, b] = [r, g, b].map(toLinear);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [
    0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  ];
}

function oklabToRgb([L, a, b]) {
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
  return [
    4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
  ].map(fromLinear);
}

const STOP_LABS = STOPS.map((hex) => rgbToOklab(hexToRgb(hex)));

/** t: 0(가장 낮은 점수) ~ 1(가장 높은 점수) */
export function greenAt(t) {
  const segments = STOP_LABS.length - 1;
  const pos = Math.min(Math.max(t, 0), 1) * segments;
  const i = Math.min(Math.floor(pos), segments - 1);
  const local = pos - i;
  const from = STOP_LABS[i];
  const to = STOP_LABS[i + 1];
  const lab = from.map((v, k) => v + (to[k] - v) * local);
  const [r, g, b] = oklabToRgb(lab);
  return `rgb(${r} ${g} ${b})`;
}

/** 칠한 색 위에 올릴 글자색 */
export function labelColorAt(t) {
  return t > 0.55 ? "#ffffff" : "#1f3a29";
}

export function legendGradient(steps = 6) {
  const stops = Array.from({ length: steps }, (_, i) => greenAt(i / (steps - 1)));
  return `linear-gradient(to right, ${stops.join(", ")})`;
}
