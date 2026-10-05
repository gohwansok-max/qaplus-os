import { interpolate, spring } from "remotion";
import { FPS } from "./theme";

export const pop = (frame: number, delay = 0) =>
  spring({ frame: frame - delay, fps: FPS, config: { damping: 14, stiffness: 140, mass: 0.8 } });

export const fade = (frame: number, delay = 0, len = 10) =>
  interpolate(frame - delay, [0, len], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

/** 씬 끝 0.25초 페이드아웃 */
export const sceneOut = (frame: number, duration: number) =>
  interpolate(frame, [duration - 8, duration], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
