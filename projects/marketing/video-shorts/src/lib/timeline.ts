/**
 * 씬 타임라인 (단일 소스)
 * - 무음 영상이므로 "읽는 속도"가 기준. 한 줄당 약 1.1~1.4초 확보.
 * - 총 길이 57초 → 유튜브 숏츠 규격(3분 이내) 충족, 무음 텍스트 영상의 체류 한계 고려.
 */

export const FPS = 30;

const s = (sec: number) => Math.round(sec * FPS);

export const SCENES = [
  { id: "hook", label: "후킹", frames: s(5) },
  { id: "define", label: "CCP 정의", frames: s(8) },
  { id: "core1", label: "핵심1 마지막 방어선", frames: s(11) },
  { id: "core2", label: "핵심2 설정 기준", frames: s(13) },
  { id: "core3", label: "핵심3 실무 실수", frames: s(11) },
  { id: "cta", label: "정리 + CTA", frames: s(9) },
] as const;

export type SceneId = (typeof SCENES)[number]["id"];

/** 각 씬의 시작 프레임 */
export const SCENE_START: Record<SceneId, number> = (() => {
  const out = {} as Record<SceneId, number>;
  let acc = 0;
  for (const sc of SCENES) {
    out[sc.id] = acc;
    acc += sc.frames;
  }
  return out;
})();

export const SCENE_FRAMES: Record<SceneId, number> = SCENES.reduce(
  (acc, sc) => ({ ...acc, [sc.id]: sc.frames }),
  {} as Record<SceneId, number>,
);

export const TOTAL_FRAMES = SCENES.reduce((a, b) => a + b.frames, 0);
