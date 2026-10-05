import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { CompareScene } from "../types";
import { COLOR, FONT } from "../theme";
import { fade, pop } from "../anim";

const Card: React.FC<{ f: number; delay: number; label: string; items: string[]; color: string; mark: string }> = ({ f, delay, label, items, color, mark }) => (
  <div style={{ width: 920, borderRadius: 36, padding: "34px 44px", background: COLOR.panel, border: `3px solid ${color}`, opacity: fade(f, delay), transform: `translateX(${(1 - pop(f, delay)) * (mark === "✕" ? -120 : 120)}px)` }}>
    <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 20 }}>
      <div style={{ width: 70, height: 70, borderRadius: "50%", background: color, color: "#06121C", fontSize: 44, fontWeight: 900, display: "grid", placeItems: "center" }}>{mark}</div>
      <div style={{ fontSize: 50, fontWeight: 900, color }}>{label}</div>
    </div>
    {items.map((t, i) => (
      <div key={i} style={{ fontSize: 46, fontWeight: 500, color: COLOR.text, lineHeight: 1.35, margin: "12px 0", opacity: fade(f, delay + 10 + i * 6) }}>· {t}</div>
    ))}
  </div>
);

export const Compare: React.FC<{ s: CompareScene }> = ({ s }) => {
  const f = useCurrentFrame();
  const half = Math.floor(s.durationFrames * 0.4);
  return (
    <AbsoluteFill style={{ fontFamily: FONT, alignItems: "center", justifyContent: "center", paddingTop: 120, paddingBottom: 420, gap: 36 }}>
      <div style={{ fontSize: 58, fontWeight: 900, color: COLOR.text, opacity: fade(f), letterSpacing: -2, marginBottom: 6 }}>{s.title}</div>
      <Card f={f} delay={8} label={s.bad.label} items={s.bad.items} color={COLOR.danger} mark="✕" />
      <Card f={f} delay={Math.max(30, half)} label={s.good.label} items={s.good.items} color={COLOR.safe} mark="○" />
    </AbsoluteFill>
  );
};
