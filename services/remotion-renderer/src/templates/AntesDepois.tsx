/**
 * Template: Antes → Depois
 * Estrutura: Mostra o "antes" (problema) e o "depois" (com produto)
 * Estilo: Split screen com transição de revelação
 */
import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { VideoProps } from "../types";
import { SceneText } from "../components/SceneText";
import { ProgressBar } from "../components/ProgressBar";
import { ProductImage } from "../components/ProductImage";

export const AntesDepois: React.FC<VideoProps> = ({
  scenes,
  productName,
  localImages,
}) => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill>
      {scenes.map((scene, i) => {
        const startFrame = scene.start * fps;
        const durationFrames = (scene.end - scene.start) * fps;
        const isBeforePhase = i < Math.floor(scenes.length / 2);
        const hasImage = localImages.length > 0;

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
                  background: isBeforePhase
                    ? "linear-gradient(180deg, #1a1a1a 0%, #2d1a1a 100%)"
                    : "linear-gradient(180deg, #1a2d1a 0%, #0a1a0a 100%)",
                }}
              />

              {/* Imagem (no "depois") */}
              {!isBeforePhase && hasImage && (
                <ProductImage
                  src={localImages[i % localImages.length]}
                  effect="zoom-in"
                  opacity={0.5}
                />
              )}

              {/* Overlay */}
              {!isBeforePhase && hasImage && (
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: "rgba(0,0,0,0.4)",
                  }}
                />
              )}

              {/* Label ANTES/DESPUÉS */}
              <div
                style={{
                  position: "absolute",
                  top: 80,
                  left: 0,
                  right: 0,
                  textAlign: "center",
                }}
              >
                <span
                  style={{
                    background: isBeforePhase ? "#ff4444" : "#44ff44",
                    color: isBeforePhase ? "white" : "#0a0a0a",
                    padding: "8px 24px",
                    borderRadius: 20,
                    fontSize: 22,
                    fontWeight: 700,
                    fontFamily: "'Inter', sans-serif",
                    letterSpacing: 2,
                  }}
                >
                  {isBeforePhase ? "❌ ANTES" : "✅ DESPUÉS"}
                </span>
              </div>

              {/* Texto da cena */}
              <SceneText
                text={scene.text}
                fontSize={52}
                position="center"
                style="shadow"
              />

              {/* Nome do produto */}
              {!isBeforePhase && (
                <div
                  style={{
                    position: "absolute",
                    bottom: 140,
                    left: 0,
                    right: 0,
                    textAlign: "center",
                    color: "#44ff44",
                    fontSize: 28,
                    fontWeight: 700,
                    fontFamily: "'Inter', sans-serif",
                  }}
                >
                  {productName}
                </div>
              )}

              {/* CTA última cena */}
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
                      background: "#44ff44",
                      color: "#0a0a0a",
                      padding: "14px 36px",
                      borderRadius: 50,
                      fontSize: 26,
                      fontWeight: 800,
                      fontFamily: "'Inter', sans-serif",
                    }}
                  >
                    👆 Consíguelo aquí
                  </div>
                </div>
              )}
            </AbsoluteFill>
          </Sequence>
        );
      })}

      <ProgressBar color="#44ff44" />
    </AbsoluteFill>
  );
};
