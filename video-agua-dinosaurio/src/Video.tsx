import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { SCENES, SFX, type Scene } from "./timings";
import { BG, F } from "./theme";
import { Captions } from "./components/Captions";
import { CTA } from "./components/CTA";
import {
  Caustics,
  Flash,
  Grade,
  Grain,
  KenBurns,
  LightRays,
  Particles,
  ProgressBar,
  Ripple,
  Vignette,
} from "./components/effects";

type KB = {
  from: number;
  to: number;
  panX?: number;
  panY?: number;
  rotate?: number;
  punch?: boolean;
};

const KB_BY_SCENE: Record<string, KB[]> = {
  s1: [{ from: 1.05, to: 1.26, panY: -26, rotate: 0.5 }],
  s2: [{ from: 1.1, to: 1.22, panX: 24, rotate: -0.5 }],
  s3: [{ from: 1.34, to: 1.12, panY: 18 }],
  s4: [
    { from: 1.26, to: 1.14, panX: -28, punch: true },
    { from: 1.28, to: 1.14, panX: 26, panY: -18, punch: true },
    { from: 1.3, to: 1.15, panX: -26, punch: true },
    { from: 1.26, to: 1.13, panY: 22, punch: true },
  ],
  s5: [{ from: 1.04, to: 1.24, panY: -24, rotate: 0.6 }],
  s6: [{ from: 1.07, to: 1.2, panX: -20 }],
  s7: [],
};

// --------------------------------------------------------- Escena visual
const SceneView: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame(); // relativo al inicio de la escena
  const base = F(scene.visualStart);

  // Sacudida de cámara en los impactos (braams) de esta escena
  let dx = 0;
  let dy = 0;
  let rot = 0;
  for (const ev of SFX) {
    if (
      (ev.type === "braam" || ev.type === "braamsoft") &&
      ev.t >= scene.visualStart &&
      ev.t < scene.visualEnd
    ) {
      const imp = F(ev.t) - base;
      if (frame >= imp) {
        const k = frame - imp;
        const amp = (ev.type === "braam" ? 17 : 9) * Math.exp(-k / 5.5);
        dx += Math.sin(k * 2.9) * amp;
        dy += Math.cos(k * 2.3) * amp * 0.6;
        rot += Math.sin(k * 1.7) * amp * 0.05;
      }
    }
  }

  const kbs = KB_BY_SCENE[scene.id] ?? [];

  return (
    <AbsoluteFill
      style={{
        transform: `translate(${dx}px, ${dy}px) rotate(${rot}deg)`,
      }}
    >
      {scene.id === "s7" ? (
        <CTA scene={scene} />
      ) : (
        scene.cuts.map((cut, i) => {
          const cf = F(cut.start) - base;
          const cd = F(cut.end) - F(cut.start);
          const kb = kbs[Math.min(i, kbs.length - 1)];
          return (
            <Sequence key={cut.img + i} from={cf} durationInFrames={cd}>
              <KenBurns
                src={staticFile(`img/${cut.img}`)}
                duration={cd}
                from={kb.from}
                to={kb.to}
                panX={kb.panX ?? 0}
                panY={kb.panY ?? 0}
                rotate={kb.rotate ?? 0}
                punch={kb.punch ?? false}
              />
            </Sequence>
          );
        })
      )}

      {/* Overlays por escena */}
      {scene.id === "s1" ? (
        <>
          <Caustics opacity={0.15} />
          <Particles mode="bubbles" count={14} seed="s1" opacity={0.55} />
          <Ripple at={F(scene.words[13].t) - base} y={1060} />
        </>
      ) : null}
      {scene.id === "s2" ? (
        <>
          <Caustics opacity={0.22} />
          <Particles mode="bubbles" count={26} seed="s2" opacity={0.8} />
        </>
      ) : null}
      {scene.id === "s3" ? (
        <>
          <Particles mode="dust" count={22} seed="s3" opacity={0.8} />
          <LightRays opacity={0.1} />
        </>
      ) : null}
      {scene.id === "s4" ? (
        <Sequence from={0} durationInFrames={F(scene.cuts[1].start) - base}>
          <Particles mode="rain" count={46} seed="lluvia" />
        </Sequence>
      ) : null}
      {scene.id === "s5" ? (
        <>
          <Particles mode="dust" count={30} seed="s5" opacity={0.9} />
          <Caustics opacity={0.1} />
        </>
      ) : null}
      {scene.id === "s6" ? (
        <>
          <LightRays opacity={0.2} />
          <Particles mode="dust" count={18} seed="s6" opacity={0.7} />
          <Particles mode="bubbles" count={10} seed="s6b" opacity={0.5} />
        </>
      ) : null}
    </AbsoluteFill>
  );
};

// -------------------------------------------------------------- Main
export const Main: React.FC = () => {
  // Flashes en cada corte (inicios de escena + subcortes del montaje s4)
  const flashFrames: number[] = [];
  SCENES.forEach((sc, i) => {
    if (i > 0) {
      flashFrames.push(F(sc.visualStart));
    }
    sc.cuts.forEach((c, j) => {
      if (j > 0) {
        flashFrames.push(F(c.start));
      }
    });
  });

  return (
    <AbsoluteFill style={{ background: BG, fontFamily: "'Montserrat', sans-serif" }}>
      {/* Escenas */}
      {SCENES.map((scene) => (
        <Sequence
          key={scene.id}
          from={F(scene.visualStart)}
          durationInFrames={F(scene.visualEnd) - F(scene.visualStart)}
        >
          <SceneView scene={scene} />
        </Sequence>
      ))}

      {/* Flashes de transición (frames absolutos) */}
      {flashFrames.map((f, i) => (
        <Flash key={i} at={f} />
      ))}

      {/* Subtítulos karaoke */}
      <Captions />

      {/* Acabado global */}
      <Grade />
      <Vignette />
      <Grain />
      <ProgressBar />

      {/* Audio: mezcla master (voz + música + SFX, -14 LUFS) */}
      <Audio src={staticFile("audio/master.wav")} />
    </AbsoluteFill>
  );
};
