import React from "react";
import { Composition } from "remotion";
import { Main } from "./Video";
import { FPS, HEIGHT, TOTAL_FRAMES, WIDTH } from "./timings";
import { loadFonts } from "./fonts";

loadFonts();

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="AguaJurasica"
      component={Main}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
  );
};
