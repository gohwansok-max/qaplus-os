import React from "react";
import { AbsoluteFill } from "remotion";
import { Background } from "../components/Background";
import { SceneShell } from "../components/SceneShell";
import { FadeUp } from "../components/FadeUp";
import { Chip } from "../components/Chip";
import { COLOR, FONT } from "../theme";

const Row: React.FC<{
  delay: number;
  cause: string;
  effect: string;
}> = ({ delay, cause, effect }) => (
  <FadeUp delay={delay}>
    <div
      style={{
        padding: "36px 40px",
        borderRadius: 28,
        backgroundColor: COLOR.card,
        border: `3px solid ${COLOR.cardLine}`,
        borderLeft: `12px solid ${COLOR.danger}`,
      }}
    >
      <div
        style={{
          fontFamily: FONT.body,
          fontSize: 48,
          fontWeight: 700,
          color: COLOR.text,
          lineHeight: 1.34,
        }}
      >
        {cause}
      </div>
      <div
        style={{
          marginTop: 16,
          fontFamily: FONT.display,
          fontSize: 52,
          fontWeight: 800,
          color: COLOR.danger,
          letterSpacing: -1,
        }}
      >
        → {effect}
      </div>
    </div>
  </FadeUp>
);

/** 00:13-00:24 핵심 ① CCP = 마지막 방어선 */
export const SceneCore1: React.FC = () => (
  <AbsoluteFill>
    <Background tone="danger" />
    <SceneShell justify="center">
      <Chip text="핵심 ①" color={COLOR.accent} delay={0} />

      <FadeUp delay={8}>
        <div
          style={{
            fontFamily: FONT.display,
            fontSize: 88,
            fontWeight: 900,
            color: COLOR.text,
            lineHeight: 1.24,
            letterSpacing: -2,
          }}
        >
          CCP는
          <br />
          <span style={{ color: COLOR.accent }}>마지막 방어선</span>
        </div>
      </FadeUp>

      <Row
        delay={40}
        cause="가열 온도가 75℃ 미만이면"
        effect="세균 생존 · 식중독"
      />
      <Row
        delay={78}
        cause="금속검출기가 고장나면"
        effect="이물질 통과 · 소비자 피해"
      />

      <FadeUp delay={120} distance={16}>
        <div
          style={{
            fontFamily: FONT.body,
            fontSize: 36,
            fontWeight: 600,
            color: COLOR.textDim,
          }}
        >
          출처 · 식품위생법 HACCP 기준서 중요관리점(CCP) 항목
        </div>
      </FadeUp>
    </SceneShell>
  </AbsoluteFill>
);
