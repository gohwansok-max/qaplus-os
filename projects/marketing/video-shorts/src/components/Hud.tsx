import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { COLOR, FONT, SIZE } from "../theme";
import { TOTAL_FRAMES } from "../lib/timeline";

/** 상단 진행 바 — 남은 길이를 보여줘 이탈률을 낮춘다. */
export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const pct = interpolate(frame, [0, TOTAL_FRAMES], [0, 100], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 118,
        left: SIZE.padX,
        right: SIZE.padX,
        height: 10,
        borderRadius: 999,
        backgroundColor: "rgba(255,255,255,0.12)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: `${pct}%`,
          height: "100%",
          borderRadius: 999,
          background: `linear-gradient(90deg, ${COLOR.accent}, ${COLOR.danger})`,
        }}
      />
    </div>
  );
};

/** 하단 고정 브랜드 워터마크 */
export const BrandTag: React.FC<{ text: string }> = ({ text }) => (
  <div
    style={{
      position: "absolute",
      bottom: 96,
      left: 0,
      right: 0,
      textAlign: "center",
      color: COLOR.textDim,
      fontFamily: FONT.body,
      fontSize: 40,
      fontWeight: 600,
      letterSpacing: 1,
    }}
  >
    {text}
  </div>
);
