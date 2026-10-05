import React from "react";
import { AbsoluteFill, Audio, Composition, Sequence, staticFile } from "remotion";
import { Background } from "./Background";
import { Captions, TopBar } from "./Chrome";
import { Checklist } from "./scenes/Checklist";
import { Compare } from "./scenes/Compare";
import { Flow } from "./scenes/Flow";
import { Hook } from "./scenes/Hook";
import { Outro } from "./scenes/Outro";
import { Stat } from "./scenes/Stat";
import { sceneOut } from "./anim";
import { FPS, H, W } from "./theme";
import { Scene, ShortProps } from "./types";
import { useCurrentFrame } from "remotion";

const Body: React.FC<{ s: Scene }> = ({ s }) => {
  switch (s.type) {
    case "hook": return <Hook s={s} />;
    case "stat": return <Stat s={s} />;
    case "flow": return <Flow s={s} />;
    case "compare": return <Compare s={s} />;
    case "checklist": return <Checklist s={s} />;
    case "outro": return <Outro s={s} />;
  }
};

const SceneWrap: React.FC<{ s: Scene }> = ({ s }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ opacity: sceneOut(f, s.durationFrames) }}>
      <Body s={s} />
      <Captions captions={s.captions} />
    </AbsoluteFill>
  );
};

export const QaShort: React.FC<ShortProps> = ({ scenes, badge, bgm, sfx }) => (
  <AbsoluteFill>
    <Background />
    {bgm ? <Audio src={staticFile(bgm)} volume={0.07} loop /> : null}
    {scenes.map((s, i) => (
      <Sequence key={i} from={s.startFrame} durationInFrames={s.durationFrames}>
        <SceneWrap s={s} />
        {s.audio ? <Audio src={staticFile(s.audio)} volume={1} /> : null}
        {sfx && i > 0 ? <Audio src={staticFile(sfx)} volume={0.25} endAt={20} /> : null}
      </Sequence>
    ))}
    <TopBar badge={badge} />
  </AbsoluteFill>
);

export const RemotionRoot: React.FC = () => (
  <Composition
    id="QaShort"
    component={QaShort}
    width={W}
    height={H}
    fps={FPS}
    durationInFrames={FPS * 45}
    defaultProps={{ topic: "", badge: "", scenes: [], totalFrames: FPS * 45 } as ShortProps}
    calculateMetadata={({ props }) => ({ durationInFrames: Math.max(30, props.totalFrames) })}
  />
);
