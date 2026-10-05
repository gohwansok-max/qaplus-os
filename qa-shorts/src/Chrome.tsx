import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { COLOR, FONT } from "./theme";
import { Caption } from "./types";

/** 상단 브랜드바 + 진행바 */
export const TopBar: React.FC<{ badge: string }> = ({ badge }) => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const p = interpolate(f, [0, durationInFrames], [0, 100]);
  return (
    <>
      <div style={{ position: "absolute", top: 96, left: 64, right: 64, display: "flex", justifyContent: "space-between", alignItems: "center", fontFamily: FONT }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 54, height: 54, borderRadius: 14, background: COLOR.cyan, color: "#06202B", fontWeight: 900, fontSize: 30, display: "grid", placeItems: "center" }}>QA</div>
          <div style={{ color: COLOR.text, fontWeight: 900, fontSize: 36, letterSpacing: -0.5 }}>큐에이플러스</div>
        </div>
        <div style={{ color: COLOR.amber, fontWeight: 700, fontSize: 28, padding: "8px 20px", border: `2px solid ${COLOR.amber}`, borderRadius: 999 }}>{badge}</div>
      </div>
      <div style={{ position: "absolute", top: 0, left: 0, height: 10, width: `${p}%`, background: `linear-gradient(90deg, ${COLOR.cyan}, ${COLOR.amber})` }} />
    </>
  );
};

/** 하단 자막 — 씬 내부 프레임 기준 */
export const Captions: React.FC<{ captions: Caption[] }> = ({ captions }) => {
  const f = useCurrentFrame();
  const cur = captions.find((c) => f >= c.start && f < c.end);
  if (!cur) return null;
  const k = interpolate(f - cur.start, [0, 5], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 250 }}>
      <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 58, color: COLOR.text, textAlign: "center", lineHeight: 1.3, wordBreak: "keep-all", maxWidth: 940, padding: "18px 34px", borderRadius: 22, background: "rgba(4,10,20,0.72)", opacity: k, transform: `translateY(${(1 - k) * 14}px)`, textShadow: "0 3px 12px rgba(0,0,0,0.6)" }}>
        {cur.text}
      </div>
    </AbsoluteFill>
  );
};
