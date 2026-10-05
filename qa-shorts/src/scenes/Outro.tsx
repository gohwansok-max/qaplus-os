import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { OutroScene } from "../types";
import { COLOR, FONT } from "../theme";
import { fade, pop } from "../anim";

export const Outro: React.FC<{ s: OutroScene }> = ({ s }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ fontFamily: FONT, justifyContent: "center", alignItems: "center", padding: 70, paddingBottom: 380, wordBreak: "keep-all" }}>
      <div style={{ fontSize: 40, fontWeight: 900, color: COLOR.amber, letterSpacing: 6, opacity: fade(f), marginBottom: 36 }}>오늘의 한 줄</div>
      <div style={{ fontSize: 88, fontWeight: 900, color: COLOR.text, textAlign: "center", lineHeight: 1.22, letterSpacing: -2.5, transform: `scale(${0.9 + pop(f, 4) * 0.1})`, opacity: fade(f, 4) }}>{s.takeaway}</div>
      <div style={{ marginTop: 90, padding: "28px 52px", borderRadius: 999, background: COLOR.cyan, color: "#06202B", fontSize: 46, fontWeight: 900, opacity: fade(f, 22), transform: `translateY(${(1 - pop(f, 22)) * 40}px)` }}>{s.cta}</div>
      <div style={{ marginTop: 28, fontSize: 32, color: COLOR.dim, opacity: fade(f, 30) }}>법령·고시는 게시 전 최신 원문을 확인하세요</div>
    </AbsoluteFill>
  );
};
