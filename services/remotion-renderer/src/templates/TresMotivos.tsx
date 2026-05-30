/**
 * Template: 3 Motivos
 * Estrutura: Hook → Motivo 1 → Motivo 2 → Motivo 3 → CTA
 * Estilo: Numeração grande, cores vibrantes por motivo
 */
import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { VideoProps } from "../types";
import { SceneText } from "../components/SceneText";
import { ProgressBar } from "../components/ProgressBar";
import { ProductImage } from "../components/ProductImage";

export const TresMotivos: React.FC<VideoProps> = ({
  scenes,
  productName,
  localImages,
}) => {
  const { fps } = useVideoConfig();

  const motivoColors = ["#ff6b35", "#ffd700", "#00d4aa"];

  return (
    <AbsoluteFill>
      {scenes.map((scene, i) => {
        const startFrame = scene.start * fps;
        const durationFrames = (scene.end - scene.start) * fps;
        const hasImage = localImages.length > 0;
        const isMotivo = i >= 1 && i <= 3;
        const motivoIndex = i - 1;
        const motivoColor = isMotivo ? motivoColors[motivoIndex] || "#ffffff" : "#ffffff";

        return (
          <Sequence key={i} from={startFrame} durationInFrames={durationFrames}>
            <AbsoluteFill>
              {/* Background */}
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: isMotivo
                    ? `linear-gradient(180deg, #0a0a0a 0%, ${motivoColor}22 100%)`
                    : "linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%)",
                }}
              />

              {/* Imagem de fundo */}
              {hasImage && isMotivo && (
                <ProductImage
                  src={localImages[motivoIndex % localImages.length]}
                  effect="zoom-in"
                  opacity={0.25}
                />
              )}

              {/* Número grande do motivo */}
              {isMotivo && (
                <div
                  style={{
                    position: "absolute",
                    top: "15%",
                    left: 0,
                    right: 0,
                    textAlign: "center",
                  }}
                >
                  <span
                    style={{
                      fontSize: 180,
                      fontWeight: 900,
                      color: motivoColor,
                      opacity: 0.3,
                      fontFamily: "'Inter', sans-serif",
                    }}
                  >
                    {motivoIndex + 1}
                  </span>
                </div>
              )}

              {/* Hook (primeira cena) */}
              {i === 0 && (
                <div
                  style={{
                    position: "absolute",
                    top: "25%",
                    left: 0,
                    right: 0,
                    textAlign: "center",
                    padding: "0 40px",
                  }}
                >
                  <div
                    style={{
                      color: "#ff6b35",
                      fontSize: 28,
                      fontWeight: 700,
                      fontFamily: "'Inter', sans-serif",
                      marginBottom: 20,
                    }}
                  >
                    3 RAZONES PARA COMPRAR
                  </div>
                  <div
                    style={{
                      color: "white",
                      fontSize: 32,
                      fontWeight: 600,
                      fontFamily: "'Inter', sans-serif",
                    }}
                  >
                    {productName}
                  </div>
                </div>
              )}

              {/* Texto da cena */}
              <SceneText
                text={scene.text}
                fontSize={isMotivo ? 48 : 56}
                position={isMotivo ? "center" : i === 0 ? "bottom" : "center"}
                style="shadow"
                color={isMotivo ? motivoColor : "#ffffff"}
              />

              {/* CTA */}
              {i === scenes.length - 1 && (
                <div
                  style={{
                    position: "absolute",
                    bottom: 80,
                    left: 0,
                    right: 0,
                    textAlign: "center",
                  }}
                >
                  <div
                    style={{
                      display: "inline-block",
                      background: "linear-gradient(135deg, #ff6b35, #ffd700)",
                      color: "#0a0a0a",
                      padding: "14px 36px",
                      borderRadius: 50,
                      fontSize: 26,
                      fontWeight: 800,
                      fontFamily: "'Inter', sans-serif",
                    }}
                  >
                    🔥 Lo quiero
                  </div>
                </div>
              )}
            </AbsoluteFill>
          </Sequence>
        );
      })}

      <ProgressBar color="#ff6b35" />
    </AbsoluteFill>
  );
};
