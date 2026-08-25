import React from "react";
import { AbsoluteFill } from "remotion";
import { Background } from "../components/Background";
import { SceneShell } from "../components/SceneShell";
import { FadeUp } from "../components/FadeUp";
import { Chip } from "../components/Chip";
import { COLOR, FONT } from "../theme";

const Mistake: React.FC<{
  delay: number;
  bad: string;
  fix: string;
}> = ({ delay, bad, fix }) => (
  <FadeUp delay={delay}>
    <div
      style={{
        padding: "32px 38px",
        borderRadius: 28,
        backgroundColor: COLOR.card,
        border: `3px solid ${COLOR.cardLine}`,
      }}
    >
      <div
        style={{
          fontFamily: FONT.body,
          fontSize: 48,
          fontWeight: 700,
          color: COLOR.text,
          lineHeight: 1.3,
        }}
      >
        <span style={{ color: COLOR.danger, fontWeight: 900 }}>✕ </span>
        {bad}
      </div>
      <div
        style={{
          marginTop: 14,
          fontFamily: FONT.body,
          fontSize: 44,
          fontWeight: 700,
          color: COLOR.safe,
          lineHeight: 1.3,
        }}
      >
        <span style={{ fontWeight: 900 }}>✓ </span>
        {fix}
      </div>
    </div>
  </FadeUp>
);

/** 00:37-00:48 핵심 ③ 심사에서 가장 많이 지적받는 3가지 */
export const SceneCore3: React.FC = () => (
  <AbsoluteFill>
    <Background tone="neutral" />
    <SceneShell justify="center">
      <Chip text="핵심 ③" color={COLOR.accent} delay={0} />

      <FadeUp delay={8}>
        <div
          style={{
            fontFamily: FONT.display,
            fontSize: 80,
            fontWeight: 900,
            color: COLOR.text,
            lineHeight: 1.24,
            letterSpacing: -2,
          }}
        >
          심사에서 제일 많이
          <br />
          <span style={{ color: COLOR.danger }}>지적받는 3가지</span>
        </div>
      </FadeUp>

      <Mistake
        delay={38}
        bad="모니터링 기록 누락"
        fix="매일 체크했으면 매일 기록까지"
      />
      <Mistake
        delay={70}
        bad='한계기준이 "적정 온도"'
        fix='"75℃ 이상" 숫자로 확정'
      />
      <Mistake
        delay={102}
        bad="개선조치 계획 없음"
        fix="이탈 시 조치를 미리 문서화"
      />

      <FadeUp delay={140} distance={16}>
        <div
          style={{
            fontFamily: FONT.body,
            fontSize: 36,
            fontWeight: 600,
            color: COLOR.textDim,
          }}
        >
          출처 · 식약처 HACCP 평가 매뉴얼
        </div>
      </FadeUp>
    </SceneShell>
  </AbsoluteFill>
);
