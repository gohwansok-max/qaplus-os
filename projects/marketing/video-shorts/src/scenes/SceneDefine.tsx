import React from "react";
import { AbsoluteFill } from "remotion";
import { Background } from "../components/Background";
import { SceneShell } from "../components/SceneShell";
import { FadeUp } from "../components/FadeUp";
import { Chip } from "../components/Chip";
import { COLOR, FONT } from "../theme";

/** 00:05-00:13 CCP 정의 — 영문 풀네임 → "쉽게 말하면" 번역 (Y3 기준) */
export const SceneDefine: React.FC = () => (
  <AbsoluteFill>
    <Background tone="neutral" />
    <SceneShell>
      <Chip text="CCP가 뭐냐면" color={COLOR.accent} delay={2} />

      <FadeUp delay={12}>
        <div
          style={{
            fontFamily: FONT.display,
            fontSize: 74,
            fontWeight: 800,
            color: COLOR.text,
            lineHeight: 1.3,
            letterSpacing: -1.5,
          }}
        >
          <span style={{ color: COLOR.accent }}>C</span>ritical{" "}
          <span style={{ color: COLOR.accent }}>C</span>ontrol{" "}
          <span style={{ color: COLOR.accent }}>P</span>oint
        </div>
      </FadeUp>

      <FadeUp delay={34}>
        <div
          style={{
            fontFamily: FONT.body,
            fontSize: 48,
            fontWeight: 700,
            color: COLOR.textDim,
          }}
        >
          중요관리점
        </div>
      </FadeUp>

      <FadeUp delay={56}>
        <div
          style={{
            marginTop: 20,
            padding: "48px 44px",
            borderRadius: 32,
            backgroundColor: COLOR.card,
            border: `3px solid ${COLOR.cardLine}`,
          }}
        >
          <div
            style={{
              fontFamily: FONT.body,
              fontSize: 44,
              fontWeight: 700,
              color: COLOR.accent,
              marginBottom: 22,
            }}
          >
            쉽게 말하면
          </div>
          <div
            style={{
              fontFamily: FONT.display,
              fontSize: 68,
              fontWeight: 800,
              color: COLOR.text,
              lineHeight: 1.36,
              letterSpacing: -1,
            }}
          >
            여기서 실수하면
            <br />
            <span style={{ color: COLOR.danger }}>식중독 나는 지점</span>
          </div>
        </div>
      </FadeUp>
    </SceneShell>
  </AbsoluteFill>
);
