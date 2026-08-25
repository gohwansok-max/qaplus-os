import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";
import { COLOR, SIZE } from "../theme";

/**
 * 배경 — 아주 느린 그라디언트 드리프트 + 그리드.
 * 무음 영상은 정적인 화면에서 이탈이 크므로, 시선을 붙잡는 최소한의 움직임만 준다.
 */
export const Background: React.FC<{ tone?: "neutral" | "danger" | "safe" }> = ({
  tone = "neutral",
}) => {
  const frame = useCurrentFrame();
  const drift = interpolate(frame % 300, [0, 300], [0, 40]);

  const glow =
    tone === "danger" ? COLOR.danger : tone === "safe" ? COLOR.safe : "#1D4ED8";

  return (
    <AbsoluteFill style={{ backgroundColor: COLOR.bgDeep }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% ${28 + drift / 10}%, ${glow}2E 0%, transparent 58%),
                       linear-gradient(180deg, ${COLOR.bg} 0%, ${COLOR.bgDeep} 100%)`,
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${COLOR.grid} 1px, transparent 1px),
                            linear-gradient(90deg, ${COLOR.grid} 1px, transparent 1px)`,
          backgroundSize: "90px 90px",
          backgroundPosition: `0px ${-drift}px`,
        }}
      />
      {/* 하단 비네트 — 자막 가독성 확보 */}
      <AbsoluteFill
        style={{
          background: `linear-gradient(180deg, transparent 55%, ${COLOR.bgDeep}D9 100%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 0,
          height: SIZE.safeBottom / 6,
        }}
      />
    </AbsoluteFill>
  );
};
