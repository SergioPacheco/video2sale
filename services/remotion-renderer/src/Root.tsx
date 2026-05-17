import React from "react";
import { Composition } from "remotion";
import { ProductVideo } from "./templates/ProductVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ProductVideo"
        component={ProductVideo}
        durationInFrames={900} // 30s * 30fps
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          scenes: [],
          template: "problema-solucao",
        }}
      />
    </>
  );
};
