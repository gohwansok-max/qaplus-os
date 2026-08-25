import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { SCENE_START, SCENE_FRAMES } from "./lib/timeline";
import { ProgressBar, BrandTag } from "./components/Hud";
import { SceneHook } from "./scenes/SceneHook";
import { SceneDefine } from "./scenes/SceneDefine";
import { SceneCore1 } from "./scenes/SceneCore1";
import { SceneCore2 } from "./scenes/SceneCore2";
import { SceneCore3 } from "./scenes/SceneCore3";
import { SceneCta } from "./scenes/SceneCta";
import { COLOR } from "./theme";

/** CCP 숏츠 본편 — 무음(자막 전용), 1080x1920 */
export const CcpShort: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: COLOR.bgDeep }}>
    <Sequence from={SCENE_START.hook} durationInFrames={SCENE_FRAMES.hook}>
      <SceneHook />
    </Sequence>
    <Sequence from={SCENE_START.define} durationInFrames={SCENE_FRAMES.define}>
      <SceneDefine />
    </Sequence>
    <Sequence from={SCENE_START.core1} durationInFrames={SCENE_FRAMES.core1}>
      <SceneCore1 />
    </Sequence>
    <Sequence from={SCENE_START.core2} durationInFrames={SCENE_FRAMES.core2}>
      <SceneCore2 />
    </Sequence>
    <Sequence from={SCENE_START.core3} durationInFrames={SCENE_FRAMES.core3}>
      <SceneCore3 />
    </Sequence>
    <Sequence from={SCENE_START.cta} durationInFrames={SCENE_FRAMES.cta}>
      <SceneCta />
    </Sequence>

    {/* 전 구간 고정 HUD */}
    <ProgressBar />
    <BrandTag text="HACCP 20년 · 실무 노하우" />
  </AbsoluteFill>
);
