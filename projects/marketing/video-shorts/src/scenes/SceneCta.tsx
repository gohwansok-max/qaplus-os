import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";
import { Background } from "../components/Background";
import { SceneShell } from "../components/SceneShell";
import { FadeUp } from "../components/FadeUp";
import { COLOR, FONT } from "../theme";

const SumLine: React.FC<{ delay: number; no: string; text: string }> = ({
  delay,
  no,
  text,
}) => (
  <FadeUp delay={delay} distance={22}>
    <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
      <div
        style={{
          fontFamily: FONT.display,
          fontSize: 52,
          fontWeight: 900,
          color: COLOR.accent,
          width: 52,
        }}
      >
        {no}
      </div>
      <div
        style={{
          fontFamily: FONT.body,
          fontSize: 50,
          fontWeight: 700,
          color: COLOR.text,
          lineHeight: 1.3,
        }}
      >
        {text}
      </div>
    </div>
  </FadeUp>
);

/**
 * 00:48-00:57 정리 + CTA
 * 숏폼 품질 기준(.claude/rules/품질기준.md)에 따라 CTA는 1개만 노출한다.
 * 컨설팅 안내는 설명란/고정댓글로 분리 → 화면에서는 전환 동선을 분산시키지 않는다.
 */
export const SceneCta: React.FC = () => {
  const frame = useCurrentFrame();

  // CTA 버튼 맥박 — 시선 유도
  const pulse = 1 + Math.sin(((frame - 120) / 30) * Math.PI * 2) * 0.022;
  const pulseOn = frame > 120 ? pulse : 1;
  const glow = interpolate(frame, [120, 150], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill>
      <Background tone="safe" />
      <SceneShell justify="center">
        <FadeUp delay={0}>
          <div
            style={{
              fontFamily: FONT.display,
              fontSize: 78,
              fontWeight: 900,
              color: COLOR.text,
              letterSpacing: -2,
            }}
          >
            오늘 하나만 기억하세요
          </div>
        </FadeUp>

        <div style={{ display: "flex", flexDirection: "column", gap: 28, marginTop: 12 }}>
          <SumLine delay={22} no="1" text="CCP는 마지막 방어선" />
          <SumLine delay={44} no="2" text="3가지 조건 다 맞으면 CCP" />
          <SumLine delay={66} no="3" text="기록 · 숫자 · 개선조치" />
        </div>

        <FadeUp delay={110}>
          <div
            style={{
              marginTop: 44,
              padding: "46px 40px",
              borderRadius: 34,
              border: `5px solid ${COLOR.accent}`,
              backgroundColor: `rgba(255,214,10,${0.12 * glow})`,
              textAlign: "center",
              transform: `scale(${pulseOn})`,
              boxShadow: `0 0 ${60 * glow}px rgba(255,214,10,0.28)`,
            }}
          >
            <div
              style={{
                fontFamily: FONT.body,
                fontSize: 42,
                fontWeight: 700,
                color: COLOR.textDim,
                marginBottom: 18,
              }}
            >
              CCP 요약본 PDF · 무료
            </div>
            <div
              style={{
                fontFamily: FONT.display,
                fontSize: 66,
                fontWeight: 900,
                color: COLOR.accent,
                lineHeight: 1.3,
                letterSpacing: -1,
              }}
            >
              댓글에 &quot;CCP&quot;
              <br />
              남겨주세요
            </div>
          </div>
        </FadeUp>
      </SceneShell>
    </AbsoluteFill>
  );
};
