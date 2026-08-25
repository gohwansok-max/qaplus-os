export const IMAGE_ONE_MINUTE_FPS = 30;

const s = (seconds: number) => Math.round(seconds * IMAGE_ONE_MINUTE_FPS);

export const IMAGE_ONE_MINUTE_SCENES = [
  { id: "hook", frames: s(8) },
  { id: "measure", frames: s(12) },
  { id: "limit", frames: s(12) },
  { id: "validate", frames: s(12) },
  { id: "deviation", frames: s(8) },
  { id: "close", frames: s(8) },
] as const;

export type ImageOneMinuteSceneId = (typeof IMAGE_ONE_MINUTE_SCENES)[number]["id"];

export const IMAGE_ONE_MINUTE_START: Record<ImageOneMinuteSceneId, number> = (() => {
  const starts = {} as Record<ImageOneMinuteSceneId, number>;
  let cursor = 0;
  for (const scene of IMAGE_ONE_MINUTE_SCENES) {
    starts[scene.id] = cursor;
    cursor += scene.frames;
  }
  return starts;
})();

export const IMAGE_ONE_MINUTE_FRAMES: Record<ImageOneMinuteSceneId, number> = IMAGE_ONE_MINUTE_SCENES.reduce(
  (acc, scene) => ({ ...acc, [scene.id]: scene.frames }),
  {} as Record<ImageOneMinuteSceneId, number>,
);

export const IMAGE_ONE_MINUTE_TOTAL_FRAMES = IMAGE_ONE_MINUTE_SCENES.reduce(
  (total, scene) => total + scene.frames,
  0,
);
