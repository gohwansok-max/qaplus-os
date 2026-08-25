/** CCP 한계기준 설정 및 유효성검증 본편 타임라인. */
export const LIMIT_FPS = 30;

const s = (seconds: number) => Math.round(seconds * LIMIT_FPS);

export const LIMIT_SCENES = [
  { id: "hook", label: "문제 제기", frames: s(10) },
  { id: "define", label: "한계기준 정의", frames: s(16) },
  { id: "map", label: "공정과 CCP 연결", frames: s(18) },
  { id: "criteria", label: "설정 조건", frames: s(20) },
  { id: "limit", label: "숫자로 고정", frames: s(22) },
  { id: "evidence", label: "근거 수집", frames: s(22) },
  { id: "example", label: "가열 공정 예시", frames: s(20) },
  { id: "validate", label: "유효성검증 설계", frames: s(24) },
  { id: "verify", label: "검증과 모니터링", frames: s(12) },
  { id: "deviation", label: "이탈 대응", frames: s(10) },
  { id: "summary", label: "최종 체크", frames: s(6) },
] as const;

export type LimitSceneId = (typeof LIMIT_SCENES)[number]["id"];

export const LIMIT_SCENE_START: Record<LimitSceneId, number> = (() => {
  const starts = {} as Record<LimitSceneId, number>;
  let cursor = 0;
  for (const scene of LIMIT_SCENES) {
    starts[scene.id] = cursor;
    cursor += scene.frames;
  }
  return starts;
})();

export const LIMIT_SCENE_FRAMES: Record<LimitSceneId, number> = LIMIT_SCENES.reduce(
  (acc, scene) => ({ ...acc, [scene.id]: scene.frames }),
  {} as Record<LimitSceneId, number>,
);

export const LIMIT_TOTAL_FRAMES = LIMIT_SCENES.reduce((total, scene) => total + scene.frames, 0);
