import React from "react";
import { COLOR, FONT } from "../theme";
import { FadeUp } from "./FadeUp";

/** 씬 상단의 작은 라벨 (예: "핵심 ①", "출처") */
export const Chip: React.FC<{
  text: string;
  color?: string;
  delay?: number;
}> = ({ text, color = COLOR.accent, delay = 0 }) => (
  <FadeUp delay={delay} distance={20}>
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 14,
        padding: "16px 32px",
        borderRadius: 999,
        border: `3px solid ${color}`,
        backgroundColor: `${color}1F`,
        color,
        fontFamily: FONT.display,
        fontSize: 46,
        fontWeight: 800,
        letterSpacing: -0.5,
      }}
    >
      {text}
    </div>
  </FadeUp>
);
