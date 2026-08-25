/**
 * 숏츠 공통 디자인 토큰
 * - 색상: 경고(빨강) / 안전(초록) / 강조(노랑) 3색만 사용해 시선 분산 방지
 * - 폰트: 시스템 폰트(맑은 고딕) 기반 — 렌더 시 네트워크 의존 없음
 */

export const COLOR = {
  bg: "#0A1626",
  bgDeep: "#060E19",
  grid: "rgba(255,255,255,0.045)",
  text: "#FFFFFF",
  textDim: "rgba(255,255,255,0.62)",
  danger: "#FF3B30",
  safe: "#22C55E",
  accent: "#FFD60A",
  card: "rgba(255,255,255,0.07)",
  cardLine: "rgba(255,255,255,0.14)",
} as const;

export const FONT = {
  /** 후킹/큰 숫자용 — 굵게 */
  display: '"Malgun Gothic", "맑은 고딕", "Noto Sans KR", sans-serif',
  /** 본문용 */
  body: '"Malgun Gothic", "맑은 고딕", "Noto Sans KR", sans-serif',
} as const;

export const SIZE = {
  width: 1080,
  height: 1920,
  fps: 30,
  /** 세로 영상 안전 여백 (상단 UI/하단 자막 겹침 방지) */
  padX: 88,
  safeTop: 210,
  safeBottom: 300,
} as const;
