import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Background } from "./components/Background";
import { BrandTag, ProgressBar } from "./components/Hud";
import { Chip } from "./components/Chip";
import { FadeUp } from "./components/FadeUp";
import { SceneShell } from "./components/SceneShell";
import { COLOR, FONT, SIZE } from "./theme";
import {
  LIMIT_SCENE_FRAMES,
  LIMIT_SCENE_START,
  LIMIT_TOTAL_FRAMES,
} from "./lib/limitValidationTimeline";

const CodeLine: React.FC<{
  children: React.ReactNode;
  color?: string;
  dim?: boolean;
  indent?: number;
}> = ({ children, color = COLOR.text, dim = false, indent = 0 }) => (
  <div
    style={{
      paddingLeft: indent * 28,
      fontFamily: '"Cascadia Code", "Consolas", monospace',
      fontSize: 34,
      lineHeight: 1.55,
      color: dim ? COLOR.textDim : color,
      whiteSpace: "pre-wrap",
    }}
  >
    {children}
  </div>
);

const CodePanel: React.FC<{
  children: React.ReactNode;
  title?: string;
  delay?: number;
  accent?: string;
}> = ({ children, title = "ccp-validation.yaml", delay = 0, accent = COLOR.accent }) => (
  <FadeUp delay={delay} distance={28}>
    <div
      style={{
        border: `2px solid ${COLOR.cardLine}`,
        borderRadius: 18,
        backgroundColor: "rgba(4, 10, 20, 0.88)",
        overflow: "hidden",
        boxShadow: "0 18px 40px rgba(0,0,0,0.28)",
      }}
    >
      <div
        style={{
          padding: "18px 26px",
          display: "flex",
          alignItems: "center",
          gap: 14,
          borderBottom: `2px solid ${COLOR.cardLine}`,
          color: COLOR.textDim,
          fontFamily: '"Cascadia Code", "Consolas", monospace',
          fontSize: 30,
        }}
      >
        <span style={{ color: COLOR.danger }}>●</span>
        <span style={{ color: COLOR.accent }}>●</span>
        <span style={{ color: COLOR.safe }}>●</span>
        <span style={{ marginLeft: 8 }}>{title}</span>
      </div>
      <div style={{ padding: "28px 32px 34px" }}>{children}</div>
    </div>
  </FadeUp>
);

const Title: React.FC<{
  eyebrow: string;
  children: React.ReactNode;
  delay?: number;
  color?: string;
}> = ({ eyebrow, children, delay = 0, color = COLOR.accent }) => (
  <>
    <Chip text={eyebrow} color={color} delay={delay} />
    <FadeUp delay={delay + 10} distance={34}>
      <div
        style={{
          fontFamily: FONT.display,
          fontSize: 72,
          fontWeight: 900,
          color: COLOR.text,
          lineHeight: 1.24,
          letterSpacing: -1.5,
        }}
      >
        {children}
      </div>
    </FadeUp>
  </>
);

const Metric: React.FC<{
  label: string;
  value: string;
  color: string;
  delay: number;
}> = ({ label, value, color, delay }) => (
  <FadeUp delay={delay} distance={20}>
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "24px 28px",
        borderBottom: `2px solid ${COLOR.cardLine}`,
      }}
    >
      <span style={{ fontFamily: FONT.body, fontSize: 40, color: COLOR.textDim }}>{label}</span>
      <span style={{ fontFamily: FONT.display, fontSize: 48, fontWeight: 900, color }}>{value}</span>
    </div>
  </FadeUp>
);

const FlowNode: React.FC<{
  label: string;
  sub: string;
  active?: boolean;
  delay: number;
}> = ({ label, sub, active = false, delay }) => (
  <FadeUp delay={delay} distance={24}>
    <div
      style={{
        minWidth: 222,
        padding: "24px 20px",
        textAlign: "center",
        borderRadius: 16,
        border: `3px solid ${active ? COLOR.danger : COLOR.cardLine}`,
        backgroundColor: active ? "rgba(255,59,48,0.16)" : COLOR.card,
      }}
    >
      <div style={{ fontFamily: FONT.display, fontSize: 40, fontWeight: 900, color: active ? COLOR.danger : COLOR.text }}>
        {label}
      </div>
      <div style={{ marginTop: 8, fontFamily: FONT.body, fontSize: 28, color: COLOR.textDim }}>{sub}</div>
    </div>
  </FadeUp>
);

const Arrow: React.FC<{ delay: number }> = ({ delay }) => (
  <FadeUp delay={delay} distance={0}>
    <div style={{ color: COLOR.accent, fontFamily: FONT.display, fontSize: 54, fontWeight: 900 }}>→</div>
  </FadeUp>
);

const CheckRow: React.FC<{
  no: string;
  title: string;
  body: string;
  delay: number;
}> = ({ no, title, body, delay }) => (
  <FadeUp delay={delay} distance={20}>
    <div style={{ display: "flex", gap: 22, alignItems: "flex-start", padding: "18px 0" }}>
      <div
        style={{
          flexShrink: 0,
          width: 62,
          height: 62,
          borderRadius: 14,
          backgroundColor: COLOR.safe,
          color: COLOR.bgDeep,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: FONT.display,
          fontSize: 38,
          fontWeight: 900,
        }}
      >
        {no}
      </div>
      <div>
        <div style={{ fontFamily: FONT.body, fontSize: 42, fontWeight: 800, color: COLOR.text }}>{title}</div>
        <div style={{ marginTop: 6, fontFamily: FONT.body, fontSize: 31, color: COLOR.textDim, lineHeight: 1.35 }}>{body}</div>
      </div>
    </div>
  </FadeUp>
);

const SceneHook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stamp = spring({ frame: frame - 24, fps, config: { damping: 12, mass: 0.8, stiffness: 160 } });
  const flash = interpolate(frame, [0, 5, 12, 17, 24, 30], [0, 0.5, 0, 0.24, 0, 0], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <Background tone="danger" />
      <AbsoluteFill style={{ backgroundColor: COLOR.danger, opacity: flash }} />
      <SceneShell>
        <FadeUp delay={2}>
          <div style={{ fontFamily: FONT.display, fontSize: 88, fontWeight: 900, color: COLOR.text, lineHeight: 1.22 }}>
            CCP 심사에서
            <br />
            <span style={{ color: COLOR.danger }}>가장 먼저</span> 보는 것
          </div>
        </FadeUp>
        <FadeUp delay={18}>
          <div style={{ fontFamily: FONT.body, fontSize: 54, fontWeight: 700, color: COLOR.textDim, lineHeight: 1.35 }}>
            “한계기준이 왜 이 숫자인가?”
          </div>
        </FadeUp>
        <div
          style={{
            marginTop: 12,
            display: "inline-block",
            width: 640,
            padding: "22px 28px",
            border: `6px solid ${COLOR.accent}`,
            borderRadius: 14,
            backgroundColor: "rgba(255,214,10,0.12)",
            transform: `scale(${0.76 + stamp * 0.24}) rotate(${(1 - stamp) * -2}deg)`,
            opacity: interpolate(frame - 24, [0, 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          }}
        >
          <CodeLine color={COLOR.accent}>CCP_LIMIT = ?</CodeLine>
          <CodeLine color={COLOR.text}>VALIDATION = REQUIRED</CodeLine>
        </div>
        <FadeUp delay={66} distance={16}>
          <div style={{ fontFamily: FONT.body, fontSize: 42, fontWeight: 700, color: COLOR.text }}>
            오늘은 설정부터 증명까지 한 번에 정리합니다
          </div>
        </FadeUp>
      </SceneShell>
    </AbsoluteFill>
  );
};

const SceneDefine: React.FC = () => (
  <AbsoluteFill>
    <Background tone="neutral" />
    <SceneShell>
      <Title eyebrow="01 · 정의" delay={0}>
        한계기준은
        <br />
        <span style={{ color: COLOR.accent }}>경계값</span>입니다
      </Title>
      <CodePanel title="critical-limit.ts" delay={26}>
        <CodeLine color={COLOR.textDim}>type CriticalLimit = &#123;</CodeLine>
        <CodeLine indent={1} color={COLOR.accent}>parameter: "temperature" | "time" | "pH";</CodeLine>
        <CodeLine indent={1} color={COLOR.accent}>threshold: number;</CodeLine>
        <CodeLine indent={1} color={COLOR.safe}>decision: "pass" | "hold";</CodeLine>
        <CodeLine color={COLOR.textDim}>&#125;;</CodeLine>
      </CodePanel>
      <FadeUp delay={84}>
        <div style={{ fontFamily: FONT.body, fontSize: 42, color: COLOR.text, lineHeight: 1.36 }}>
          “적정”, “충분히”가 아니라
          <br />
          <span style={{ color: COLOR.accent, fontWeight: 900 }}>측정 가능하고 판정 가능해야</span> 합니다
        </div>
      </FadeUp>
      <FadeUp delay={126} distance={14}>
        <div style={{ fontFamily: FONT.body, fontSize: 30, color: COLOR.textDim }}>
          제품·공정·법규에 따라 값은 달라집니다. 아래 숫자는 이해를 위한 예시입니다.
        </div>
      </FadeUp>
    </SceneShell>
  </AbsoluteFill>
);

const SceneMap: React.FC = () => (
  <AbsoluteFill>
    <Background tone="safe" />
    <SceneShell justify="center">
      <Title eyebrow="02 · 공정 매핑" delay={0} color={COLOR.safe}>
        CCP는 공정도 위에
        <br />
        <span style={{ color: COLOR.safe }}>찍어야</span> 합니다
      </Title>
      <FadeUp delay={30}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 12 }}>
          <FlowNode label="원료" sub="입고" delay={32} />
          <Arrow delay={42} />
          <FlowNode label="가열" sub="CCP-1" active delay={52} />
          <Arrow delay={62} />
          <FlowNode label="냉각" sub="CP" delay={72} />
          <Arrow delay={82} />
          <FlowNode label="검출" sub="CCP-2" active delay={92} />
        </div>
      </FadeUp>
      <CodePanel title="process-map.json" delay={112} accent={COLOR.safe}>
        <CodeLine color={COLOR.textDim}>&#123; "step": "heating",</CodeLine>
        <CodeLine indent={1} color={COLOR.safe}>"hazard": "pathogen",</CodeLine>
        <CodeLine indent={1} color={COLOR.accent}>"control": "time + temperature" &#125;</CodeLine>
      </CodePanel>
      <FadeUp delay={166}>
        <div style={{ fontFamily: FONT.body, fontSize: 36, color: COLOR.textDim, textAlign: "center" }}>
          위해요소 → 관리수단 → CCP 후보 → 한계기준
        </div>
      </FadeUp>
    </SceneShell>
  </AbsoluteFill>
);

const SceneCriteria: React.FC = () => (
  <AbsoluteFill>
    <Background tone="neutral" />
    <SceneShell justify="center">
      <Title eyebrow="03 · 설정 조건" delay={0}>
        숫자를 정하기 전
        <br />
        <span style={{ color: COLOR.accent }}>세 가지 질문</span>
      </Title>
      <CodePanel title="ccp-decision.flow" delay={28}>
        <CodeLine color={COLOR.accent}>if (hazard.exists) &#123;</CodeLine>
        <CodeLine indent={1} color={COLOR.text}>  measurable = chooseParameter();</CodeLine>
        <CodeLine indent={1} color={COLOR.text}>  laterControl = checkNextStep();</CodeLine>
        <CodeLine indent={1} color={COLOR.safe}>  if (!laterControl) return "CCP";</CodeLine>
        <CodeLine color={COLOR.accent}>&#125;</CodeLine>
      </CodePanel>
      <CheckRow no="1" title="위해요소가 실제로 존재하는가" body="생물학적 · 화학적 · 물리적 위해를 근거로 적습니다." delay={84} />
      <CheckRow no="2" title="측정할 수 있는 파라미터인가" body="온도·시간·pH·수분활성도처럼 기록 가능한 값이어야 합니다." delay={110} />
      <CheckRow no="3" title="다음 공정에서 제거되는가" body="이후에 통제할 수 없다면 이 단계의 관리가 핵심입니다." delay={136} />
      <FadeUp delay={172}>
        <div style={{ fontFamily: FONT.body, fontSize: 30, color: COLOR.textDim }}>근거: Codex HACCP CCP 결정도 적용 원칙</div>
      </FadeUp>
    </SceneShell>
  </AbsoluteFill>
);

const SceneLimit: React.FC = () => {
  const frame = useCurrentFrame();
  const active = Math.min(2, Math.floor(Math.max(0, frame - 34) / 48));
  return (
    <AbsoluteFill>
      <Background tone="danger" />
      <SceneShell justify="center">
        <Title eyebrow="04 · 한계기준 설정" delay={0} color={COLOR.danger}>
          좋은 기준은
          <br />
          <span style={{ color: COLOR.danger }}>판정문</span>으로 읽힙니다
        </Title>
        <CodePanel title="limit-table.csv" delay={28} accent={COLOR.danger}>
          <CodeLine color={COLOR.textDim}>CCP,parameter,critical_limit,action</CodeLine>
          <CodeLine color={active === 0 ? COLOR.accent : COLOR.text}>CCP-1,temp,&gt;=75C/60s,hold</CodeLine>
          <CodeLine color={active === 1 ? COLOR.accent : COLOR.text}>CCP-2,metal,0 detected,stop</CodeLine>
          <CodeLine color={active === 2 ? COLOR.accent : COLOR.text}>CCP-3,pH,&lt;=4.2,hold</CodeLine>
        </CodePanel>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <Metric label="나쁜 표현" value="적정 온도" color={COLOR.danger} delay={94} />
          <Metric label="좋은 표현" value="≥ 75°C · 60초" color={COLOR.safe} delay={116} />
          <Metric label="판정 결과" value="PASS / HOLD" color={COLOR.accent} delay={138} />
        </div>
        <FadeUp delay={174}>
          <div style={{ fontFamily: FONT.body, fontSize: 30, color: COLOR.textDim }}>※ 예시 기준. 실제 적용 전 제품별 법규와 검증자료를 대조하세요.</div>
        </FadeUp>
      </SceneShell>
    </AbsoluteFill>
  );
};

const SceneEvidence: React.FC = () => (
  <AbsoluteFill>
    <Background tone="safe" />
    <SceneShell justify="center">
      <Title eyebrow="05 · 설정 근거" delay={0} color={COLOR.safe}>
        숫자는
        <br />
        <span style={{ color: COLOR.safe }}>근거의 교집합</span>에서 나옵니다
      </Title>
      <CodePanel title="evidence-stack.md" delay={28} accent={COLOR.safe}>
        <CodeLine color={COLOR.accent}>01  법령·고시</CodeLine>
        <CodeLine color={COLOR.text}>02  공인 가이드·표준</CodeLine>
        <CodeLine color={COLOR.text}>03  논문·시험성적서</CodeLine>
        <CodeLine color={COLOR.safe}>04  현장 유효성검증</CodeLine>
      </CodePanel>
      <FadeUp delay={98}>
        <div style={{ padding: "28px 30px", borderLeft: `10px solid ${COLOR.accent}`, backgroundColor: COLOR.card }}>
          <div style={{ fontFamily: FONT.body, fontSize: 40, color: COLOR.text, lineHeight: 1.35 }}>
            가장 엄격한 요구사항과
            <br />
            <span style={{ color: COLOR.accent, fontWeight: 900 }}>현장에서 지킬 수 있는 조건</span>을 함께 봅니다
          </div>
        </div>
      </FadeUp>
      <FadeUp delay={142}>
        <div style={{ fontFamily: '"Cascadia Code", "Consolas", monospace', fontSize: 36, color: COLOR.textDim }}>
          evidence[] → decision → approved_limit
        </div>
      </FadeUp>
      <FadeUp delay={176}>
        <div style={{ fontFamily: FONT.body, fontSize: 30, color: COLOR.textDim }}>문서 번호, 시험일, 장비 ID까지 연결해야 추적성이 생깁니다.</div>
      </FadeUp>
    </SceneShell>
  </AbsoluteFill>
);

const SceneExample: React.FC = () => {
  const frame = useCurrentFrame();
  const needle = interpolate(frame, [18, 150], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const reading = Math.round(70 + needle * 9);
  const pass = reading >= 75;
  return (
    <AbsoluteFill>
      <Background tone="danger" />
      <SceneShell justify="center">
        <Title eyebrow="06 · 예시" delay={0} color={COLOR.accent}>
          가열 CCP를
          <br />
          <span style={{ color: COLOR.accent }}>현장 언어</span>로 바꾸기
        </Title>
        <CodePanel title="heating-monitor.log" delay={26} accent={COLOR.accent}>
          <CodeLine color={COLOR.textDim}>product: sauce_batch_042</CodeLine>
          <CodeLine color={COLOR.textDim}>instrument: T-07 / calibrated: 2026-08-01</CodeLine>
          <CodeLine color={COLOR.accent}>critical_limit: core_temp &gt;= 75C for 60s</CodeLine>
          <CodeLine color={pass ? COLOR.safe : COLOR.danger}>reading: {reading}C / status: {pass ? "PASS" : "HOLD"}</CodeLine>
        </CodePanel>
        <div style={{ marginTop: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontFamily: FONT.body, fontSize: 34, color: COLOR.textDim }}>
            <span>70°C</span><span>75°C 한계</span><span>80°C</span>
          </div>
          <div style={{ position: "relative", height: 32, marginTop: 16, borderRadius: 999, backgroundColor: "rgba(255,255,255,0.12)" }}>
            <div style={{ position: "absolute", left: "50%", top: -14, bottom: -14, width: 6, backgroundColor: COLOR.accent }} />
            <div style={{ position: "absolute", left: `${Math.max(0, Math.min(100, (reading - 70) / 10 * 100))}%`, top: -12, width: 56, height: 56, borderRadius: "50%", backgroundColor: pass ? COLOR.safe : COLOR.danger, transform: "translateX(-50%)" }} />
          </div>
        </div>
        <FadeUp delay={168}>
          <div style={{ fontFamily: FONT.body, fontSize: 34, color: COLOR.text, lineHeight: 1.4 }}>
            숫자 하나만 적는 것이 아니라
            <br />
            <span style={{ color: COLOR.safe, fontWeight: 900 }}>측정 위치 · 유지시간 · 장비 ID</span>까지 고정합니다
          </div>
        </FadeUp>
      </SceneShell>
    </AbsoluteFill>
  );
};

const SceneValidate: React.FC = () => {
  const frame = useCurrentFrame();
  const pulse = 1 + Math.sin((frame / 30) * Math.PI * 2) * 0.015;
  return (
    <AbsoluteFill>
      <Background tone="safe" />
      <SceneShell justify="center">
        <Title eyebrow="07 · 유효성검증" delay={0} color={COLOR.safe}>
          검증은
          <br />
          <span style={{ color: COLOR.safe }}>“이 기준으로 실제 위해가 통제되는가?”</span>를 증명합니다
        </Title>
        <CodePanel title="validation-run.ts" delay={30} accent={COLOR.safe}>
          <CodeLine color={COLOR.accent}>const test = &#123;</CodeLine>
          <CodeLine indent={1}>worstCase: true,</CodeLine>
          <CodeLine indent={1}>instrument: "calibrated",</CodeLine>
          <CodeLine indent={1}>replicates: 3,</CodeLine>
          <CodeLine indent={1} color={COLOR.safe}>records: [before, during, after]</CodeLine>
          <CodeLine color={COLOR.accent}>&#125;;</CodeLine>
        </CodePanel>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <Metric label="최악조건" value="YES" color={COLOR.safe} delay={108} />
          <Metric label="반복시험" value="n ≥ 3" color={COLOR.accent} delay={120} />
          <Metric label="교정장비" value="ID 기록" color={COLOR.accent} delay={132} />
          <Metric label="판정" value="PASS" color={COLOR.safe} delay={144} />
        </div>
        <div style={{ transform: `scale(${pulse})` }}>
          <FadeUp delay={174}>
            <div style={{ padding: "24px 30px", borderRadius: 16, border: `3px solid ${COLOR.safe}`, backgroundColor: "rgba(34,197,94,0.12)", fontFamily: FONT.body, fontSize: 34, color: COLOR.text, textAlign: "center" }}>
              결과가 기준을 지지해야 승인합니다
            </div>
          </FadeUp>
        </div>
      </SceneShell>
    </AbsoluteFill>
  );
};

const SceneVerify: React.FC = () => (
  <AbsoluteFill>
    <Background tone="neutral" />
    <SceneShell justify="center">
      <Title eyebrow="08 · 운영 중 검증" delay={0}>
        유효성검증과
        <br />
        <span style={{ color: COLOR.accent }}>모니터링은 다릅니다</span>
      </Title>
      <CodePanel title="validation-vs-verification.md" delay={30}>
        <CodeLine color={COLOR.safe}>VALIDATION   기준이 위해를 통제하는지 사전 증명</CodeLine>
        <CodeLine color={COLOR.accent}>VERIFICATION  계획대로 운영되는지 정기 확인</CodeLine>
        <CodeLine color={COLOR.text}>MONITORING    CCP 값을 매 배치 측정·기록</CodeLine>
      </CodePanel>
      <FadeUp delay={112}>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 18, fontFamily: FONT.display, fontSize: 42, fontWeight: 900 }}>
          <span style={{ color: COLOR.safe }}>검증</span><span style={{ color: COLOR.accent }}>→</span><span style={{ color: COLOR.text }}>운영</span><span style={{ color: COLOR.accent }}>→</span><span style={{ color: COLOR.safe }}>재검증</span>
        </div>
      </FadeUp>
      <FadeUp delay={150}>
        <div style={{ fontFamily: FONT.body, fontSize: 34, color: COLOR.textDim, lineHeight: 1.4, textAlign: "center" }}>
          공정·원료·장비·법규가 바뀌면
          <br />
          기존 한계기준을 다시 검토합니다
        </div>
      </FadeUp>
    </SceneShell>
  </AbsoluteFill>
);

const SceneDeviation: React.FC = () => (
  <AbsoluteFill>
    <Background tone="danger" />
    <SceneShell justify="center">
      <Title eyebrow="09 · 이탈 대응" delay={0} color={COLOR.danger}>
        이탈이 생기면
        <br />
        <span style={{ color: COLOR.danger }}>제품보다 기록이 먼저</span>입니다
      </Title>
      <CodePanel title="deviation-handler.ts" delay={28} accent={COLOR.danger}>
        <CodeLine color={COLOR.danger}>if (reading &lt; criticalLimit) &#123;</CodeLine>
        <CodeLine indent={1}>hold(product);</CodeLine>
        <CodeLine indent={1}>assess(safety, affectedLots);</CodeLine>
        <CodeLine indent={1}>correct(process, equipment);</CodeLine>
        <CodeLine indent={1} color={COLOR.accent}>record(reason, action, disposition);</CodeLine>
        <CodeLine color={COLOR.danger}>&#125;</CodeLine>
      </CodePanel>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <CheckRow no="1" title="보류" body="영향받은 제품과 로트를 식별합니다." delay={110} />
        <CheckRow no="2" title="평가" body="재가공·폐기·출하 여부를 결정합니다." delay={130} />
        <CheckRow no="3" title="재발방지" body="원인과 조치 후 필요하면 재검증합니다." delay={150} />
      </div>
    </SceneShell>
  </AbsoluteFill>
);

const SceneSummary: React.FC = () => {
  const frame = useCurrentFrame();
  const glow = interpolate(frame, [24, 90], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <Background tone="safe" />
      <SceneShell justify="center">
        <FadeUp delay={0}>
          <div style={{ fontFamily: FONT.display, fontSize: 78, fontWeight: 900, color: COLOR.text, textAlign: "center", lineHeight: 1.25 }}>
            CCP 한계기준
            <br />
            <span style={{ color: COLOR.safe }}>설정 · 검증 · 기록</span>
          </div>
        </FadeUp>
        <div style={{ padding: "28px 30px", borderRadius: 18, border: `4px solid ${COLOR.accent}`, backgroundColor: `rgba(255,214,10,${0.1 * glow})`, boxShadow: `0 0 ${50 * glow}px rgba(255,214,10,0.24)` }}>
          <CodeLine color={COLOR.accent}>measure → compare → decide → record → revalidate</CodeLine>
        </div>
        <FadeUp delay={70}>
          <div style={{ fontFamily: FONT.body, fontSize: 38, color: COLOR.textDim, textAlign: "center" }}>
            기준표를 만들 때는 이 다섯 단어를 빠뜨리지 마세요
          </div>
        </FadeUp>
      </SceneShell>
    </AbsoluteFill>
  );
};

export const CcpLimitValidation: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: COLOR.bgDeep }}>
    <Sequence from={LIMIT_SCENE_START.hook} durationInFrames={LIMIT_SCENE_FRAMES.hook}><SceneHook /></Sequence>
    <Sequence from={LIMIT_SCENE_START.define} durationInFrames={LIMIT_SCENE_FRAMES.define}><SceneDefine /></Sequence>
    <Sequence from={LIMIT_SCENE_START.map} durationInFrames={LIMIT_SCENE_FRAMES.map}><SceneMap /></Sequence>
    <Sequence from={LIMIT_SCENE_START.criteria} durationInFrames={LIMIT_SCENE_FRAMES.criteria}><SceneCriteria /></Sequence>
    <Sequence from={LIMIT_SCENE_START.limit} durationInFrames={LIMIT_SCENE_FRAMES.limit}><SceneLimit /></Sequence>
    <Sequence from={LIMIT_SCENE_START.evidence} durationInFrames={LIMIT_SCENE_FRAMES.evidence}><SceneEvidence /></Sequence>
    <Sequence from={LIMIT_SCENE_START.example} durationInFrames={LIMIT_SCENE_FRAMES.example}><SceneExample /></Sequence>
    <Sequence from={LIMIT_SCENE_START.validate} durationInFrames={LIMIT_SCENE_FRAMES.validate}><SceneValidate /></Sequence>
    <Sequence from={LIMIT_SCENE_START.verify} durationInFrames={LIMIT_SCENE_FRAMES.verify}><SceneVerify /></Sequence>
    <Sequence from={LIMIT_SCENE_START.deviation} durationInFrames={LIMIT_SCENE_FRAMES.deviation}><SceneDeviation /></Sequence>
    <Sequence from={LIMIT_SCENE_START.summary} durationInFrames={LIMIT_SCENE_FRAMES.summary}><SceneSummary /></Sequence>
    <ProgressBar />
    <BrandTag text="CCP 한계기준 · 유효성검증 실무" />
  </AbsoluteFill>
);

export const CCP_LIMIT_DURATION = LIMIT_TOTAL_FRAMES;
