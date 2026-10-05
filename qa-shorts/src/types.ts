export type Caption = { text: string; start: number; end: number }; // 씬 내부 프레임

type Base = {
  narration: string;
  /** public/ 기준 상대경로 (TTS mp3) */
  audio?: string;
  /** 씬 시작 프레임(전체 타임라인 기준)과 길이 — 파이프라인이 TTS 길이로 채운다 */
  startFrame: number;
  durationFrames: number;
  captions: Caption[];
};

export type HookScene = Base & { type: "hook"; kicker: string; headline: string; sub: string };
export type StatScene = Base & { type: "stat"; label: string; value: string; caption: string; note?: string };
export type FlowScene = Base & { type: "flow"; title: string; steps: string[] };
export type CompareScene = Base & {
  type: "compare";
  title: string;
  bad: { label: string; items: string[] };
  good: { label: string; items: string[] };
};
export type ChecklistScene = Base & { type: "checklist"; title: string; items: string[] };
export type OutroScene = Base & { type: "outro"; takeaway: string; cta: string };

export type Scene = HookScene | StatScene | FlowScene | CompareScene | ChecklistScene | OutroScene;

export type ShortProps = {
  topic: string;
  badge: string;
  scenes: Scene[];
  totalFrames: number;
  bgm?: string;
  sfx?: string;
};
