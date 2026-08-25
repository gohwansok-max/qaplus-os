import React from "react";
import { AbsoluteFill } from "remotion";
import { SIZE } from "../theme";

/** 모든 씬의 공통 레이아웃 — 세로 영상 안전 영역 안에 콘텐츠를 배치 */
export const SceneShell: React.FC<{
  children: React.ReactNode;
  justify?: React.CSSProperties["justifyContent"];
}> = ({ children, justify = "center" }) => (
  <AbsoluteFill
    style={{
      paddingLeft: SIZE.padX,
      paddingRight: SIZE.padX,
      paddingTop: SIZE.safeTop,
      paddingBottom: SIZE.safeBottom,
      display: "flex",
      flexDirection: "column",
      justifyContent: justify,
      gap: 40,
    }}
  >
    {children}
  </AbsoluteFill>
);
