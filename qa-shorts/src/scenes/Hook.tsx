import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { HookScene } from "../types";
import { COLOR, FONT } from "../theme";
import { fade, pop } from "../anim";

export const Hook: React.FC<{ s: HookScene }> = ({ s }) => {
  const f = useCurrentFrame();
  const lines = s.headline.split("\n");
  const pulse = 1 + Math.sin(f / 6) * 0.015;
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", fontFamily: FONT, padding: 70, paddingBottom: 380, wordBreak: "keep-all" }}>
      <div style={{ position: "absolute", width: 760, height: 760, borderRadius: "50%", border: `3px solid ${COLOR.danger}`, opacity: 0.25 * fade(f, 0, 12), transform: `scale(${0.6 + pop(f) * 0.5 * pulse})` }} />
      <div style={{ fontSize: 40, fontWeight: 900, color: "#fff", background: COLOR.danger, padding: "10px 30px", borderRadius: 999, transform: `scale(${pop(f)})`, marginBottom: 54 }}>{s.kicker}</div>
      {lines.map((l, i) => (
        <div key={i} style={{ fontSize: s.headline.split("\n").some((l) => l.length > 10) ? 96 : 112, fontWeight: 900, lineHeight: 1.16, textAlign: "center", color: i === lines.length - 1 ? COLOR.amber : COLOR.text, opacity: fade(f, 6 + i * 6), transform: `translateY(${(1 - pop(f, 6 + i * 6)) * 70}px)`, letterSpacing: -3 }}>{l}</div>
      ))}
      <div style={{ marginTop: 56, fontSize: 44, fontWeight: 500, color: COLOR.dim, textAlign: "center", opacity: fade(f, 28) }}>{s.sub}</div>
    </AbsoluteFill>
  );
};
