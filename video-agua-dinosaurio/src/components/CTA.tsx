import React from "react";
import {
  AbsoluteFill,
  interpolate,
  random,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { type Scene } from "../timings";
import { AQUA, F } from "../theme";
import { LightRays, Particles } from "./effects";

const EMOJI_FONT = "'Archivo Black', 'Noto Color Emoji', sans-serif";

export const CTA: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const base = F(scene.visualStart);
  const likeAt = F(scene.words[7].t) - base;
  const followAt = F(scene.words[9].t) - base;

  const likeVisible = frame >= likeAt;
  const likeS = likeVisible
    ? spring({
        frame: frame - likeAt,
        fps,
        config: { damping: 9, stiffness: 230, mass: 0.7 },
      })
    : 0;
  const followVisible = frame >= followAt;
  const followS = followVisible
    ? spring({
        frame: frame - followAt,
        fps,
        config: { damping: 11, stiffness: 210, mass: 0.7 },
      })
    : 0;

  const ringT = frame - likeAt;
  const ringP = interpolate(ringT, [0, 26], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const miniHearts = new Array(7).fill(0).map((_, i) => {
    const start = likeAt + 4 + i * 5;
    const t = frame - start;
    if (t < 0 || t > 46) {
      return null;
    }
    const p = t / 46;
    const x = 540 + (random(`mh${i}`) - 0.5) * 460;
    const y = 760 - p * 420;
    const s = 0.5 + random(`ms${i}`) * 0.7;
    return (
      <div
        key={i}
        style={{
          position: "absolute",
          left: x,
          top: y,
          fontSize: 64 * s,
          fontFamily: EMOJI_FONT,
          opacity: (1 - p) * 0.9,
          transform: `rotate(${(random(`mr${i}`) - 0.5) * 40}deg)`,
        }}
      >
        {"❤️"}
      </div>
    );
  });

  const endPulse = 0.5 + 0.5 * Math.sin(frame / 7);

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(130% 90% at 50% 10%, #0B3E58 0%, #052032 48%, #010B12 100%)",
      }}
    >
      <LightRays opacity={0.12} />
      <Particles mode="bubbles" count={30} seed="cta" opacity={0.8} />

      {/* Corazón LIKE */}
      {likeVisible ? (
        <>
          <div
            style={{
              position: "absolute",
              left: 540 - 130,
              top: 620,
              width: 260,
              height: 260,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 205,
              fontFamily: EMOJI_FONT,
              transform: `scale(${0.4 + 0.68 * likeS}) rotate(${(1 - likeS) * -14}deg)`,
              filter: "drop-shadow(0 14px 34px rgba(255,60,90,0.45))",
            }}
          >
            {"❤️"}
          </div>
          {ringP < 1 ? (
            <div
              style={{
                position: "absolute",
                left: 540 - (140 + ringP * 300),
                top: 750 - (140 + ringP * 300),
                width: 280 + ringP * 600,
                height: 280 + ringP * 600,
                borderRadius: "50%",
                border: `5px solid rgba(255,120,140,${(1 - ringP) * 0.7})`,
              }}
            />
          ) : null}
          {miniHearts}
        </>
      ) : null}

      {/* Botón SEGUIR */}
      {followVisible ? (
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: 905,
            display: "flex",
            justifyContent: "center",
            transform: `scale(${0.5 + 0.5 * followS})`,
            opacity: Math.min(1, followS * 1.3),
          }}
        >
          <div
            style={{
              fontFamily: "'Montserrat', sans-serif",
              fontWeight: 900,
              fontSize: 56,
              letterSpacing: 2,
              color: "#04121C",
              background: "#FFFFFF",
              padding: "26px 66px",
              borderRadius: 999,
              boxShadow: `0 0 ${34 + endPulse * 26}px rgba(62,232,255,0.55), 0 14px 40px rgba(0,0,0,0.5)`,
              transform: `scale(${1 + 0.035 * Math.sin((frame - followAt) / 5)})`,
            }}
          >
            + SEGUIR
          </div>
        </div>
      ) : null}

      {/* Glow final */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(70% 40% at 50% 88%, rgba(62,232,255,${0.06 + endPulse * 0.05}), transparent 70%)`,
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: 150,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: "'Montserrat', sans-serif",
          fontWeight: 800,
          fontSize: 34,
          letterSpacing: 10,
          color: AQUA,
          opacity: 0.85,
        }}
      >
        💧 BEBIENDO TIEMPO
      </div>
    </AbsoluteFill>
  );
};
