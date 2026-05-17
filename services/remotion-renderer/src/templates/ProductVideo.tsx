import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from "remotion";

interface Scene {
  start: number;
  end: number;
  text: string;
  voiceover: string;
  visual: string;
}

interface ProductVideoProps {
  scenes: Scene[];
  template: string;
}

export const ProductVideo: React.FC<ProductVideoProps> = ({
  scenes,
  template,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentSecond = frame / fps;

  // Encontrar cena atual
  const currentScene = scenes.find(
    (s) => currentSecond >= s.start && currentSecond < s.end
  );

  const opacity = interpolate(frame % 30, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0a0a0a",
        justifyContent: "center",
        alignItems: "center",
        fontFamily: "sans-serif",
      }}
    >
      {/* Texto principal */}
      {currentScene && (
        <div
          style={{
            opacity,
            color: "white",
            fontSize: 64,
            fontWeight: "bold",
            textAlign: "center",
            padding: "0 60px",
            textShadow: "2px 2px 8px rgba(0,0,0,0.8)",
          }}
        >
          {currentScene.text}
        </div>
      )}

      {/* Barra de progresso */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          height: 4,
          backgroundColor: "#ff2d55",
          width: `${(currentSecond / 30) * 100}%`,
        }}
      />
    </AbsoluteFill>
  );
};
