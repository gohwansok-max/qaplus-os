import React from "react";
import { AbsoluteFill } from "remotion";
import { COLOR, FONT } from "./theme";

/** 숏츠 커버 이미지 (PNG로 뽑아 썸네일로 사용) */
export const Thumbnail: React.FC = () => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(circle at 50% 32%, ${COLOR.danger}33 0%, transparent 58%),
                   linear-gradient(180deg, ${COLOR.bg} 0%, ${COLOR.bgDeep} 100%)`,
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      alignItems: "center",
      padding: 90,
      gap: 44,
    }}
  >
    <div
      style={{
        fontFamily: FONT.display,
        fontSize: 88,
        fontWeight: 900,
        color: COLOR.text,
        textAlign: "center",
        lineHeight: 1.26,
        letterSpacing: -2,
      }}
    >
      HACCP 탈락
      <br />
      <span style={{ color: COLOR.danger }}>1순위 이유</span>
    </div>

    <div
      style={{
        padding: "34px 76px",
        border: `10px solid ${COLOR.danger}`,
        borderRadius: 30,
        backgroundColor: "rgba(255,59,48,0.12)",
        fontFamily: FONT.display,
        fontSize: 240,
        fontWeight: 900,
        color: COLOR.danger,
        letterSpacing: 8,
        lineHeight: 1,
      }}
    >
      CCP
    </div>

    <div
      style={{
        fontFamily: FONT.display,
        fontSize: 76,
        fontWeight: 900,
        color: COLOR.accent,
        textAlign: "center",
        letterSpacing: -1,
      }}
    >
      핵심 3가지
    </div>

    <div
      style={{
        marginTop: 10,
        fontFamily: FONT.body,
        fontSize: 44,
        fontWeight: 600,
        color: COLOR.textDim,
      }}
    >
      품질 20년차가 정리했습니다
    </div>
  </AbsoluteFill>
);
