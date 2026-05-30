import React from "react";
import { Img, interpolate, useCurrentFrame, spring, useVideoConfig, staticFile } from "remotion";

interface ProductImageProps {
  src: string;
  effect?: "zoom-in" | "zoom-out" | "pan" | "static";
  opacity?: number;
}

export const ProductImage: React.FC<ProductImageProps> = ({
  src,
  effect = "zoom-in",
  opacity = 1,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  let scale = 1;
  let translateX = 0;

  switch (effect) {
    case "zoom-in":
      scale = interpolate(frame, [0, durationInFrames], [1, 1.15], {
        extrapolateRight: "clamp",
      });
      break;
    case "zoom-out":
      scale = interpolate(frame, [0, durationInFrames], [1.15, 1], {
        extrapolateRight: "clamp",
      });
      break;
    case "pan":
      translateX = interpolate(frame, [0, durationInFrames], [-50, 50], {
        extrapolateRight: "clamp",
      });
      break;
  }

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        overflow: "hidden",
        opacity,
      }}
    >
      <Img
        src={src}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale}) translateX(${translateX}px)`,
        }}
      />
    </div>
  );
};
