/**
 * Template: Problema → Solução
 * Estrutura: Hook (problema) → Apresenta produto → Demo → Resultado → CTA
 * Estilo: Fundo escuro com texto grande, transições rápidas
 */
import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { VideoProps } from "../types";
import { SceneText } from "../components/SceneText";
import { ProgressBar } from "../components/ProgressBar";
import { Background } from "../components/Background";
import { ProductImage } from "../components/ProductImage";

export const ProblemaSolucao: React.FC<VideoProps> = ({
  scenes,
  productName,
  hook,
  localImages,
}) => {
  const { fps } = useVideoConfig();

  // Cores por fase do vídeo
  const phaseColors: [string, string][] = [
    ["#1a0000", "#2d0000"], // Problema (vermelho escuro)
    ["#001a0a", "#002d12"], // Solução (verde escuro)
    ["#0a001a", "#12002d"], // Demo (roxo escuro)
    ["#001a1a", "#002d2d"], // Resultado (teal escuro)
    ["#1a0a00", "#2d1200"], // CTA (laranja escuro)
  ];

  return (
    <AbsoluteFill>
      {scenes.map((scene, i) => {
        const startFrame = scene.start * fps;
        const durationFrames = (scene.end - scene.start) * fps;
        const colors = phaseColors[i % phaseColors.length];
        const hasImage = localImages.length > 0 && i > 0;
        const imageIndex = (i - 1) % localImages.length;

        return (
          <Sequence key={i} from={startFrame} durationInFrames={durationFrames}>
            <AbsoluteFill>
              <Background variant={i === 0 ? "pulse" : "gradient"} colors={colors} />

              {/* Imagem do produto (se disponível, a partir da cena 2) */}
              {hasImage && (
                <ProductImage
                  src={localImages[imageIndex]}
                  effect={i % 2 === 0 ? "zoom-in" : "zoom-out"}
                  opacity={0.4}
                />
              )}

              {/* Overlay escuro sobre imagem */}
              {hasImage && (
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: "rgba(0,0,0,0.5)",
                  }}
                />
              )}

              {/* Emoji/ícone na primeira cena */}
              {i === 0 && (
                <div
                  style={{
                    position: "absolute",
                    top: "30%",
                    left: 0,
                    right: 0,
                    textAlign: "center",
                    fontSize: 80,
                  }}
                >
                  😤
                </div>
              )}

              {/* Texto principal */}
              <SceneText
                text={scene.text}
                fontSize={i === 0 ? 64 : 52}
                position={hasImage ? "bottom" : "center"}
                style={i === 0 ? "outline" : "shadow"}
              />

              {/* Nome do produto (cenas do meio) */}
              {i > 0 && i < scenes.length - 1 && (
                <div
                  style={{
                    position: "absolute",
                    top: 60,
                    left: 0,
                    right: 0,
                    textAlign: "center",
                    color: "rgba(255,255,255,0.6)",
                    fontSize: 24,
                    fontFamily: "'Inter', sans-serif",
                  }}
                >
                  {productName}
                </div>
              )}

              {/* CTA na última cena */}
              {i === scenes.length - 1 && (
                <div
                  style={{
                    position: "absolute",
                    bottom: 100,
                    left: 0,
                    right: 0,
                    textAlign: "center",
                  }}
                >
                  <div
                    style={{
                      display: "inline-block",
                      background: "#ff2d55",
                      color: "white",
                      padding: "16px 40px",
                      borderRadius: 50,
                      fontSize: 28,
                      fontWeight: 700,
                      fontFamily: "'Inter', sans-serif",
                    }}
                  >
                    🛒 Link en bio
                  </div>
                </div>
              )}
            </AbsoluteFill>
          </Sequence>
        );
      })}

      <ProgressBar color="#ff2d55" />
    </AbsoluteFill>
  );
};
