import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  random,
  useCurrentFrame,
} from "remotion";
import { TOTAL_FRAMES } from "../timings";
import { AQUA, GOLD } from "../theme";

const W = 1080;
const H = 1920;

// ---------------------------------------------------------------- Grain
const NOISE_SVG = `<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter><rect width='300' height='300' filter='url(#n)'/></svg>`;
const NOISE_URL = `url("data:image/svg+xml,${encodeURIComponent(NOISE_SVG)}")`;

export const Grain: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        backgroundImage: NOISE_URL,
        backgroundSize: "300px 300px",
        backgroundPosition: `${(frame * 53) % 300}px ${(frame * 97) % 300}px`,
        opacity: 0.09,
        mixBlendMode: "overlay",
        pointerEvents: "none",
      }}
    />
  );
};

// -------------------------------------------------------------- Vignette
export const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        "radial-gradient(ellipse 90% 70% at 50% 42%, transparent 52%, rgba(0,0,0,0.5) 100%)",
      pointerEvents: "none",
    }}
  />
);

// ------------------------------------------------------- Grade cinemático
export const Grade: React.FC = () => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <AbsoluteFill
      style={{
        background:
          "linear-gradient(180deg, rgba(0,45,70,0.16), transparent 32%, transparent 68%, rgba(10,0,35,0.22))",
        mixBlendMode: "multiply",
      }}
    />
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(80% 45% at 50% 8%, rgba(120,210,255,0.10), transparent 70%)",
        mixBlendMode: "screen",
      }}
    />
  </AbsoluteFill>
);

// ------------------------------------------------------------- LightRays
export const LightRays: React.FC<{ opacity?: number }> = ({
  opacity = 0.14,
}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ overflow: "hidden", pointerEvents: "none" }}>
      <div
        style={{
          position: "absolute",
          left: W / 2 - 1400,
          top: -1750,
          width: 2800,
          height: 2800,
          background: `repeating-conic-gradient(from ${frame * 0.06}deg at 50% 50%, rgba(190,240,255,0.16) 0deg 5deg, transparent 5deg 16deg)`,
          filter: "blur(26px)",
          mixBlendMode: "screen",
          opacity,
        }}
      />
    </AbsoluteFill>
  );
};

// -------------------------------------------------------------- Caustics
export const Caustics: React.FC<{ opacity?: number }> = ({
  opacity = 0.18,
}) => {
  const frame = useCurrentFrame();
  const x1 = Math.sin(frame / 38) * 150;
  const y1 = Math.cos(frame / 47) * 110;
  const x2 = Math.cos(frame / 44) * 170;
  const y2 = Math.sin(frame / 31) * 120;
  return (
    <AbsoluteFill
      style={{ mixBlendMode: "screen", opacity, pointerEvents: "none" }}
    >
      <div
        style={{
          position: "absolute",
          inset: -220,
          background:
            "radial-gradient(34% 24% at 30% 32%, rgba(80,205,255,0.6), transparent 70%)",
          filter: "blur(34px)",
          transform: `translate(${x1}px, ${y1}px)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: -220,
          background:
            "radial-gradient(30% 22% at 68% 62%, rgba(60,180,255,0.5), transparent 70%)",
          filter: "blur(38px)",
          transform: `translate(${x2}px, ${y2}px)`,
        }}
      />
    </AbsoluteFill>
  );
};

// ----------------------------------------------------------------- Flash
export const Flash: React.FC<{
  at: number;
  color?: string;
  peak?: number;
}> = ({ at, color = "210,245,255", peak = 0.7 }) => {
  const frame = useCurrentFrame();
  if (frame < at - 1 || frame > at + 10) {
    return null;
  }
  const o = interpolate(frame, [at - 1, at + 1, at + 9], [0, peak, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 45%, rgba(${color},${o}), rgba(${color},${o * 0.45}) 45%, transparent 82%)`,
        pointerEvents: "none",
      }}
    />
  );
};

// ---------------------------------------------------------------- Ripple
export const Ripple: React.FC<{ at: number; x?: number; y?: number }> = ({
  at,
  x = W / 2,
  y = 1010,
}) => {
  const frame = useCurrentFrame();
  const rings = [0, 6, 13];
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {rings.map((off, i) => {
        const t = frame - at - off;
        if (t < 0 || t > 40) {
          return null;
        }
        const p = interpolate(t, [0, 40], [0, 1], {
          easing: Easing.out(Easing.cubic),
        });
        const size = 240 + p * 1250;
        const o = (1 - p) * 0.55;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - size / 2,
              top: y - size / 2,
              width: size,
              height: size,
              borderRadius: "50%",
              border: `${4 - i}px solid rgba(140,225,255,${o})`,
              boxShadow: `0 0 40px rgba(80,200,255,${o * 0.5}) inset`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// ----------------------------------------------------------- ProgressBar
export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const w = (frame / TOTAL_FRAMES) * 100;
  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        height: 6,
        width: `${w}%`,
        background: `linear-gradient(90deg, ${AQUA}, ${GOLD})`,
        boxShadow: `0 0 14px ${AQUA}`,
        borderRadius: 3,
      }}
    />
  );
};

// ------------------------------------------------------------- Particles
type Mode = "bubbles" | "dust" | "rain";

export const Particles: React.FC<{
  mode: Mode;
  count?: number;
  seed?: string;
  opacity?: number;
}> = ({ mode, count = 24, seed = "p", opacity = 1 }) => {
  const frame = useCurrentFrame();
  const items: React.ReactNode[] = [];
  for (let i = 0; i < count; i++) {
    const rx = random(`${seed}-x${i}`);
    const ry = random(`${seed}-y${i}`);
    const rs = random(`${seed}-s${i}`);
    const rv = random(`${seed}-v${i}`);
    const ro = random(`${seed}-o${i}`);
    if (mode === "rain") {
      const speed = 36 + rv * 26;
      const len = 90 + rs * 140;
      const y = ((frame * speed + ry * (H + 400)) % (H + 400)) - 220;
      const x = rx * (W + 260) - 130 - (y / H) * 150;
      items.push(
        <div
          key={i}
          style={{
            position: "absolute",
            left: x,
            top: y,
            width: 2.6,
            height: len,
            background:
              "linear-gradient(180deg, rgba(195,235,255,0), rgba(195,235,255,0.45))",
            transform: "rotate(10deg)",
            opacity: 0.2 + ro * 0.35,
          }}
        />
      );
    } else if (mode === "bubbles") {
      const speed = 1.3 + rv * 2.8;
      const size = 7 + rs * 24;
      const y = H + 160 - ((frame * speed + ry * (H + 320)) % (H + 320));
      const x = rx * W + Math.sin((frame / 30) * (0.6 + rv) + i) * 30;
      items.push(
        <div
          key={i}
          style={{
            position: "absolute",
            left: x,
            top: y,
            width: size,
            height: size,
            borderRadius: "50%",
            background:
              "radial-gradient(circle at 32% 28%, rgba(225,250,255,0.9), rgba(140,220,255,0.15) 58%, transparent 72%)",
            opacity: 0.15 + ro * 0.3,
            filter: "blur(0.4px)",
          }}
        />
      );
    } else {
      const speed = 0.25 + rv * 0.65;
      const size = 2.5 + rs * 5.5;
      const y = H + 70 - ((frame * speed + ry * (H + 120)) % (H + 120));
      const x = rx * W + Math.sin((frame / 42) * (0.5 + rv) + i * 2) * 44;
      const tw = 0.6 + 0.4 * Math.sin(frame / 9 + i * 1.7);
      items.push(
        <div
          key={i}
          style={{
            position: "absolute",
            left: x,
            top: y,
            width: size,
            height: size,
            borderRadius: "50%",
            background: "rgba(255,232,185,0.85)",
            opacity: (0.1 + ro * 0.28) * tw,
            filter: "blur(1px)",
          }}
        />
      );
    }
  }
  return (
    <AbsoluteFill style={{ opacity, pointerEvents: "none" }}>
      {items}
    </AbsoluteFill>
  );
};

// -------------------------------------------------------------- KenBurns
export const KenBurns: React.FC<{
  src: string;
  duration: number;
  from?: number;
  to?: number;
  panX?: number;
  panY?: number;
  rotate?: number;
  punch?: boolean;
}> = ({
  src,
  duration,
  from = 1.08,
  to = 1.2,
  panX = 0,
  panY = 0,
  rotate = 0,
  punch = false,
}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, Math.max(duration, 1)], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.sin),
  });
  const scale = punch
    ? interpolate(frame, [0, 9, Math.max(duration, 10)], [from + 0.12, from, to], {
        extrapolateRight: "clamp",
        easing: Easing.out(Easing.cubic),
      })
    : from + (to - from) * p;
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      {/* eslint-disable-next-line @remotion/warn-native-media-tag */}
      <img
        src={src}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translate(${panX * p}px, ${panY * p}px) rotate(${rotate * p}deg)`,
        }}
      />
    </AbsoluteFill>
  );
};
