import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig, spring } from "remotion";

interface SceneTextProps {
  text: string;
  fontSize?: number;
  color?: string;
  position?: "center" | "bottom" | "top";
  style?: "bold" | "outline" | "shadow" | "gradient";
}

export const SceneText: React.FC<SceneTextProps> = ({
  text,
  fontSize = 56,
  color = "#ffffff",
  position = "center",
  style = "shadow",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = spring({ frame, fps, config: { damping: 20 } });
  const translateY = interpolate(frame, [0, 10], [30, 0], {
    extrapolateRight: "clamp",
  });

  const positionStyles: Record<string, React.CSSProperties> = {
    center: { top: "50%", transform: `translateY(calc(-50% + ${translateY}px))` },
    bottom: { bottom: "180px", transform: `translateY(${translateY}px)` },
    top: { top: "120px", transform: `translateY(${translateY}px)` },
  };

  const textStyles: Record<string, React.CSSProperties> = {
    bold: { fontWeight: 900 },
    outline: {
      fontWeight: 800,
      WebkitTextStroke: "2px rgba(0,0,0,0.8)",
    },
    shadow: {
      fontWeight: 800,
      textShadow: "3px 3px 6px rgba(0,0,0,0.9), 0 0 20px rgba(0,0,0,0.5)",
    },
    gradient: {
      fontWeight: 900,
      background: "linear-gradient(135deg, #ff2d55, #ff6b35)",
      WebkitBackgroundClip: "text",
      WebkitTextFillColor: "transparent",
    },
  };

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        padding: "0 60px",
        opacity,
        ...positionStyles[position],
      }}
    >
      <div
        style={{
          color,
          fontSize,
          textAlign: "center",
          lineHeight: 1.2,
          fontFamily: "'Inter', 'Noto Sans', sans-serif",
          ...textStyles[style],
        }}
      >
        {text}
      </div>
    </div>
  );
};
