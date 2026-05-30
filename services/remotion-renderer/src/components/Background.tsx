import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

interface BackgroundProps {
  variant?: "dark" | "gradient" | "pulse" | "split";
  colors?: [string, string];
}

export const Background: React.FC<BackgroundProps> = ({
  variant = "dark",
  colors = ["#0a0a0a", "#1a1a2e"],
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const gradientAngle = interpolate(frame, [0, durationInFrames], [0, 360]);
  const pulse = interpolate(frame % 60, [0, 30, 60], [0.3, 0.6, 0.3]);

  const styles: Record<string, React.CSSProperties> = {
    dark: {
      background: `linear-gradient(180deg, ${colors[0]} 0%, ${colors[1]} 100%)`,
    },
    gradient: {
      background: `linear-gradient(${gradientAngle}deg, ${colors[0]}, ${colors[1]}, ${colors[0]})`,
    },
    pulse: {
      background: colors[0],
      boxShadow: `inset 0 0 ${200 * pulse}px ${100 * pulse}px ${colors[1]}`,
    },
    split: {
      background: `linear-gradient(180deg, ${colors[0]} 0%, ${colors[0]} 50%, ${colors[1]} 50%, ${colors[1]} 100%)`,
    },
  };

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        ...styles[variant],
      }}
    />
  );
};
