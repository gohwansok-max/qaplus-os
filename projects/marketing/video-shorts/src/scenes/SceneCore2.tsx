import React from "react";
import { AbsoluteFill } from "remotion";
import { Background } from "../components/Background";
import { SceneShell } from "../components/SceneShell";
import { FadeUp } from "../components/FadeUp";
import { Chip } from "../components/Chip";
import { COLOR, FONT } from "../theme";

const CheckItem: React.FC<{
  delay: number;
  no: string;
  question: string;
  verdict: string;
}> = ({ delay, no, question, verdict }) => (
  <FadeUp delay={delay}>
    <div
      style={{
        display: "flex",
        gap: 30,
        alignItems: "flex-start",
        padding: "34px 38px",
        borderRadius: 28,
        backgroundColor: COLOR.card,
        border: `3px solid ${COLOR.cardLine}`,
      }}
    >
      <div
        style={{
          flexShrink: 0,
          width: 84,
          height: 84,
          borderRadius: 20,
          backgroundColor: COLOR.safe,
          color: COLOR.bgDeep,
          fontFamily: FONT.display,
          fontSize: 54,
          fontWeight: 900,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {no}
      </div>
      <div>
        <div
          style={{
            fontFamily: FONT.body,
            fontSize: 50,
            fontWeight: 700,
            color: COLOR.text,
            lineHeight: 1.32,
          }}
        >
          {question}
        </div>
        <div
          style={{
            marginTop: 12,
            fontFamily: FONT.body,
            fontSize: 40,
            fontWeight: 700,
            color: COLOR.safe,
          }}
        >
          {verdict}
        </div>
      </div>
    </div>
  </FadeUp>
);

/** 00:24-00:37 핵심 ② CCP 설정 3대 조건 */
export const SceneCore2: React.FC = () => (
  <AbsoluteFill>
    <Background tone="safe" />
    <SceneShell justify="center">
      <Chip text="핵심 ②" color={COLOR.accent} delay={0} />

      <FadeUp delay={8}>
        <div
          style={{
            fontFamily: FONT.display,
            fontSize: 84,
            fontWeight: 900,
            color: COLOR.text,
            lineHeight: 1.24,
            letterSpacing: -2,
          }}
        >
          이 <span style={{ color: COLOR.safe }}>3가지 다</span> 맞으면
          <br />
          CCP입니다
        </div>
      </FadeUp>

      <CheckItem
        delay={38}
        no="1"
        question="위해 요소가 있나요?"
        verdict="생물학적 · 화학적 · 물리적"
      />
      <CheckItem
        delay={74}
        no="2"
        question="이후 공정에서 제거되나요?"
        verdict="안 된다 → CCP"
      />
      <CheckItem
        delay={110}
        no="3"
        question="여기서 안 잡으면 위험한가요?"
        verdict="그렇다 → CCP"
      />

      <FadeUp delay={150} distance={16}>
        <div
          style={{
            fontFamily: FONT.body,
            fontSize: 36,
            fontWeight: 600,
            color: COLOR.textDim,
          }}
        >
          출처 · Codex HACCP 적용 지침 (CCP 결정도)
        </div>
      </FadeUp>
    </SceneShell>
  </AbsoluteFill>
);
