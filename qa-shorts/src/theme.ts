export const COLOR = {
  bg: "#07111F",
  bgDeep: "#040A14",
  panel: "rgba(255,255,255,0.06)",
  line: "rgba(255,255,255,0.14)",
  text: "#FFFFFF",
  dim: "rgba(255,255,255,0.66)",
  cyan: "#22D3EE",
  amber: "#FBBF24",
  danger: "#FF4D4F",
  safe: "#34D399",
} as const;

// 시스템 폰트(Actions: fonts-noto-cjk) 사용 — 렌더 시 외부 네트워크 의존 제거
export const FONT = '"Noto Sans CJK KR", "Noto Sans KR", "NanumGothic", "Malgun Gothic", sans-serif';

export const W = 1080;
export const H = 1920;
export const FPS = 30;
