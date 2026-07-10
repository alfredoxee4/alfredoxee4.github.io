import React from 'react';
import {Composition} from 'remotion';
import {DinosaurWater} from './DinosaurWater';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="DinosaurWater"
      component={DinosaurWater}
      durationInFrames={990}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{}}
    />
  );
};
