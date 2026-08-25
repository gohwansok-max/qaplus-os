import React from "react";
import {
  AbsoluteFill,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { Chip } from "./components/Chip";
import { FadeUp } from "./components/FadeUp";
import { BrandTag } from "./components/Hud";
import { COLOR, FONT, SIZE } from "./theme";
import {
  IMAGE_ONE_MINUTE_FRAMES,
  IMAGE_ONE_MINUTE_START,
  IMAGE_ONE_MINUTE_TOTAL_FRAMES,
} from "./lib/imageOneMinuteTimeline";

type SceneTone = "amber" | "green" | "red" | "blue";

const TONE_COLOR: Record<SceneTone, string> = {
  amber: COLOR.accent,
  green: COLOR.safe,
  red: COLOR.danger,
  blue: "#60A5FA",
};

const CaptionPanel: React.FC<{
  children: React.ReactNode;
  tone: SceneTone;
  delay?: number;
}> = ({ children, tone, delay = 0 }) => (
  <FadeUp delay={delay} distance={28}>
    <div
      style={{
        alignSelf: "stretch",
        padding: "26px 30px 30px",
        borderLeft: `8px solid ${TONE_COLOR[tone]}`,
        backgroundColor: "rgba(5, 12, 24, 0.78)",
        boxShadow: "0 18px 44px rgba(0, 0, 0, 0.28)",
      }}
    >
      {children}
    </div>
  </FadeUp>
);

const CodePill: React.FC<{
  text: string;
  tone?: SceneTone;
  delay?: number;
}> = ({ text, tone = "amber", delay = 0 }) => (
  <FadeUp delay={delay} distance={16}>
    <div
      style={{
        display: "inline-flex",
        padding: "14px 20px",
        border: `2px solid ${TONE_COLOR[tone]}`,
        backgroundColor: "rgba(5, 12, 24, 0.78)",
        color: TONE_COLOR[tone],
        fontFamily: '"Cascadia Code", "Consolas", monospace',
        fontSize: 30,
        fontWeight: 700,
        letterSpacing: 0.5,
      }}
    >
      {text}
    </div>
  </FadeUp>
);

const Progress: React.FC<{ duration: number }> = ({ duration }) => {
  const frame = useCurrentFrame();
  const width = interpolate(frame, [0, duration], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        left: SIZE.padX,
        right: SIZE.padX,
        top: 104,
        height: 8,
        backgroundColor: "rgba(255,255,255,0.28)",
        zIndex: 10,
      }}
    >
      <div style={{ width: `${width}%`, height: "100%", backgroundColor: COLOR.accent }} />
    </div>
  );
};

const VisualScene: React.FC<{
  asset: string;
  kicker: string;
  title: React.ReactNode;
  body: React.ReactNode;
  tone: SceneTone;
  duration: number;
  code?: string;
  children?: React.ReactNode;
}> = ({ asset, kicker, title, body, tone, duration, code, children }) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [0, duration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scale = interpolate(progress, [0, 1], [1.06, 1.14]);
  const x = interpolate(progress, [0, 1], [0, -1.4]);
  const y = interpolate(progress, [0, 1], [0, -0.8]);
  const wash = interpolate(frame, [0, 14], [0.88, 0.42], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{ backgroundColor: COLOR.bgDeep }}>
      <Img
        src={staticFile(`assets/${asset}`)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translate(${x}%, ${y}%)`,
        }}
      />
      <AbsoluteFill style={{ backgroundColor: `rgba(3, 9, 20, ${wash})` }} />
      <AbsoluteFill style={{ backgroundColor: `${TONE_COLOR[tone]}12` }} />
      <Progress duration={duration} />
      <div
        style={{
          position: "absolute",
          top: 144,
          left: SIZE.padX,
          right: SIZE.padX,
          zIndex: 5,
          display: "flex",
          flexDirection: "column",
          gap: 22,
        }}
      >
        <Chip text={kicker} color={TONE_COLOR[tone]} delay={4} />
        {code ? <CodePill text={code} tone={tone} delay={12} /> : null}
      </div>
      <div
        style={{
          position: "absolute",
          left: SIZE.padX,
          right: SIZE.padX,
          bottom: SIZE.safeBottom + 80,
          zIndex: 5,
          display: "flex",
          flexDirection: "column",
          gap: 22,
        }}
      >
        <CaptionPanel tone={tone} delay={18}>
          <div
            style={{
              fontFamily: FONT.display,
              fontSize: 68,
              lineHeight: 1.2,
              fontWeight: 900,
              color: COLOR.text,
              letterSpacing: -1,
            }}
          >
            {title}
          </div>
          <div
            style={{
              marginTop: 18,
              fontFamily: FONT.body,
              fontSize: 38,
              lineHeight: 1.36,
              fontWeight: 700,
              color: "rgba(255,255,255,0.84)",
            }}
          >
            {body}
          </div>
        </CaptionPanel>
        {children}
      </div>
      <BrandTag text="HACCP · CCP FIELD NOTES" />
    </AbsoluteFill>
  );
};

const Hook: React.FC = () => (
  <VisualScene
    asset="factory-line.png"
    kicker="CCP FIELD NOTES / 01"
    tone="amber"
    duration={IMAGE_ONE_MINUTE_FRAMES.hook}
    code="risk → control → proof"
    title={<>안전은<br /><span style={{ color: COLOR.accent }}>숫자에서 시작됩니다</span></>}
    body={<>한계기준을 제대로 세우면<br />현장의 판단이 흔들리지 않습니다.</>}
  />
);

const Measure: React.FC = () => (
  <VisualScene
    asset="thermal-probe.png"
    kicker="CCP-1 / MEASURE"
    tone="green"
    duration={IMAGE_ONE_MINUTE_FRAMES.measure}
    code="core_temp >= 75°C / 60s"
    title={<>‘적정’이 아니라<br /><span style={{ color: COLOR.safe }}>측정 가능한 값</span></>}
    body={<>온도·시간·pH처럼<br />누가 측정해도 같은 판정이 나와야 합니다.</>}
  >
    <FadeUp delay={82} distance={16}>
      <div style={{ display: "flex", gap: 12 }}>
        <CodePill text="measure" tone="green" />
        <CodePill text="compare" tone="amber" />
        <CodePill text="decide" tone="blue" />
      </div>
    </FadeUp>
  </VisualScene>
);

const Limit: React.FC = () => (
  <VisualScene
    asset="factory-line.png"
    kicker="CCP LIMIT / SET"
    tone="red"
    duration={IMAGE_ONE_MINUTE_FRAMES.limit}
    code="PASS | HOLD | STOP"
    title={<>한계기준은<br /><span style={{ color: COLOR.danger }}>판정문</span>으로 씁니다</>}
    body={<>“적정 온도”는 해석이고,<br /><b style={{ color: COLOR.accent }}>75°C 이상 · 60초</b>는 기준입니다.</>}
  >
    <FadeUp delay={86} distance={18}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <CodePill text="vague: 적정" tone="red" />
        <CodePill text="valid: ≥75°C" tone="green" />
      </div>
    </FadeUp>
  </VisualScene>
);

const Validate: React.FC = () => (
  <VisualScene
    asset="qa-review.png"
    kicker="VALIDATION / PROVE IT"
    tone="blue"
    duration={IMAGE_ONE_MINUTE_FRAMES.validate}
    code="worst-case + replicate x3"
    title={<>왜 이 숫자인지<br /><span style={{ color: "#60A5FA" }}>증명해야 합니다</span></>}
    body={<>최악조건에서 반복 시험하고<br />교정된 장비와 기록으로 승인합니다.</>}
  >
    <FadeUp delay={86} distance={18}>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <CodePill text="evidence" tone="blue" />
        <CodePill text="record" tone="green" />
        <CodePill text="revalidate" tone="amber" />
      </div>
    </FadeUp>
  </VisualScene>
);

const Deviation: React.FC = () => (
  <VisualScene
    asset="detector-shipping.png"
    kicker="DEVIATION / ACT NOW"
    tone="red"
    duration={IMAGE_ONE_MINUTE_FRAMES.deviation}
    code="hold → assess → correct → record"
    title={<>이탈이 보이면<br /><span style={{ color: COLOR.danger }}>제품을 먼저 보류</span></>}
    body={<>영향 로트를 식별하고<br />조치와 판정을 남깁니다.</>}
  />
);

const Close: React.FC = () => (
  <VisualScene
    asset="qa-review.png"
    kicker="CCP FIELD NOTES / FINAL"
    tone="green"
    duration={IMAGE_ONE_MINUTE_FRAMES.close}
    code="measure → decide → prove"
    title={<>설정하고,<br /><span style={{ color: COLOR.safe }}>검증하고, 기록하세요</span></>}
    body={<>한계기준은 문서가 아니라<br />현장을 움직이는 약속입니다.</>}
  >
    <FadeUp delay={76} distance={14}>
      <div style={{ fontFamily: FONT.body, fontSize: 30, color: COLOR.textDim, textAlign: "center" }}>
        HACCP 실무 · CCP 한계기준 & 유효성검증
      </div>
    </FadeUp>
  </VisualScene>
);

export const CcpImageOneMinute: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: COLOR.bgDeep }}>
    <Sequence from={IMAGE_ONE_MINUTE_START.hook} durationInFrames={IMAGE_ONE_MINUTE_FRAMES.hook}><Hook /></Sequence>
    <Sequence from={IMAGE_ONE_MINUTE_START.measure} durationInFrames={IMAGE_ONE_MINUTE_FRAMES.measure}><Measure /></Sequence>
    <Sequence from={IMAGE_ONE_MINUTE_START.limit} durationInFrames={IMAGE_ONE_MINUTE_FRAMES.limit}><Limit /></Sequence>
    <Sequence from={IMAGE_ONE_MINUTE_START.validate} durationInFrames={IMAGE_ONE_MINUTE_FRAMES.validate}><Validate /></Sequence>
    <Sequence from={IMAGE_ONE_MINUTE_START.deviation} durationInFrames={IMAGE_ONE_MINUTE_FRAMES.deviation}><Deviation /></Sequence>
    <Sequence from={IMAGE_ONE_MINUTE_START.close} durationInFrames={IMAGE_ONE_MINUTE_FRAMES.close}><Close /></Sequence>
  </AbsoluteFill>
);

export const CCP_IMAGE_ONE_MINUTE_DURATION = IMAGE_ONE_MINUTE_TOTAL_FRAMES;
