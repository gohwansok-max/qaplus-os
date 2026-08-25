import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";
import { Background } from "../components/Background";
import { SceneShell } from "../components/SceneShell";
import { FadeUp } from "../components/FadeUp";
import { COLOR, FONT } from "../theme";

/** 00:00-00:05 후킹 — "탈락" 불안 자극 + 주제어 CCP 각인 */
export const SceneHook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // "CCP" 스탬프 — 살짝 오버슈트하며 찍히는 느낌
  const stamp = spring({
    frame: frame - 42,
    fps,
    config: { damping: 12, mass: 0.9, stiffness: 180 },
  });
  const stampOpacity = interpolate(frame - 42, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // 경고 플래시 — 2회 짧게
  const flash = interpolate(
    frame,
    [0, 4, 10, 14, 20, 26],
    [0, 0.5, 0, 0.32, 0, 0],
    { extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill>
      <Background tone="danger" />
      <AbsoluteFill style={{ backgroundColor: COLOR.danger, opacity: flash }} />

      <SceneShell>
        <FadeUp delay={4}>
          <div
            style={{
              fontFamily: FONT.display,
              fontSize: 96,
              fontWeight: 800,
              color: COLOR.text,
              lineHeight: 1.28,
              letterSpacing: -2,
            }}
          >
            HACCP 인증
            <br />
            <span style={{ color: COLOR.danger }}>탈락하는 업체</span>
          </div>
        </FadeUp>

        <FadeUp delay={20}>
          <div
            style={{
              fontFamily: FONT.body,
              fontSize: 72,
              fontWeight: 700,
              color: COLOR.text,
              lineHeight: 1.35,
            }}
          >
            절반이 <span style={{ color: COLOR.accent }}>이거</span> 몰라서
            <br />
            떨어집니다
          </div>
        </FadeUp>

        <div
          style={{
            marginTop: 24,
            opacity: stampOpacity,
            transform: `scale(${0.7 + stamp * 0.3}) rotate(${(1 - stamp) * -6}deg)`,
            transformOrigin: "left center",
          }}
        >
          <div
            style={{
              display: "inline-block",
              padding: "28px 64px",
              border: `9px solid ${COLOR.danger}`,
              borderRadius: 28,
              fontFamily: FONT.display,
              fontSize: 190,
              fontWeight: 900,
              color: COLOR.danger,
              letterSpacing: 6,
              lineHeight: 1,
              backgroundColor: "rgba(255,59,48,0.10)",
            }}
          >
            CCP
          </div>
        </div>

        <FadeUp delay={92} distance={18}>
          <div
            style={{
              fontFamily: FONT.body,
              fontSize: 54,
              fontWeight: 600,
              color: COLOR.textDim,
            }}
          >
            1분 안에 완전히 정리해드릴게요
          </div>
        </FadeUp>
      </SceneShell>
    </AbsoluteFill>
  );
};
