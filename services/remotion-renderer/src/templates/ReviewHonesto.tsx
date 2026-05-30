/**
 * Template: Review Honesto
 * Estrutura: Opinião pessoal → Prós → Contras → Veredicto → CTA
 * Estilo: Fundo neutro, estrelas de rating, tom conversacional
 */
import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { VideoProps } from "../types";
import { SceneText } from "../components/SceneText";
import { ProgressBar } from "../components/ProgressBar";
import { ProductImage } from "../components/ProductImage";

export const ReviewHonesto: React.FC<VideoProps> = ({
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
        const hasImage = localImages.length > 0;

        return (
          <Sequence key={i} from={startFrame} durationInFrames={durationFrames}>
            <AbsoluteFill>
              {/* Background neutro */}
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: "linear-gradient(180deg, #1a1a2e 0%, #16213e 100%)",
                }}
              />

              {/* Imagem do produto (cenas do meio) */}
              {hasImage && i > 0 && i < scenes.length - 1 && (
                <ProductImage
                  src={localImages[i % localImages.length]}
                  effect="static"
                  opacity={0.3}
                />
              )}

              {/* Header com nome do produto */}
              <div
                style={{
                  position: "absolute",
                  top: 60,
                  left: 0,
                  right: 0,
                  textAlign: "center",
                  padding: "0 40px",
                }}
              >
                <div
                  style={{
                    color: "rgba(255,255,255,0.7)",
                    fontSize: 22,
                    fontFamily: "'Inter', sans-serif",
                    fontWeight: 500,
                  }}
                >
                  Mi opinión honesta sobre
                </div>
                <div
                  style={{
                    color: "#ffffff",
                    fontSize: 30,
                    fontFamily: "'Inter', sans-serif",
                    fontWeight: 700,
                    marginTop: 8,
                  }}
                >
                  {productName}
                </div>
                {/* Stars */}
                <div style={{ marginTop: 12, fontSize: 28 }}>⭐⭐⭐⭐☆</div>
              </div>

              {/* Texto da cena */}
              <SceneText
                text={scene.text}
                fontSize={48}
                position="center"
                style="shadow"
              />

              {/* Indicador de seção */}
              {i > 0 && i < scenes.length - 1 && (
                <div
                  style={{
                    position: "absolute",
                    bottom: 160,
                    left: 0,
                    right: 0,
                    textAlign: "center",
                    color: "rgba(255,255,255,0.5)",
                    fontSize: 18,
                    fontFamily: "'Inter', sans-serif",
                  }}
                >
                  {i}/{scenes.length - 1}
                </div>
              )}

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
                      background: "linear-gradient(135deg, #667eea, #764ba2)",
                      color: "white",
                      padding: "14px 36px",
                      borderRadius: 50,
                      fontSize: 26,
                      fontWeight: 700,
                      fontFamily: "'Inter', sans-serif",
                    }}
                  >
                    🔗 Ver precio actual
                  </div>
                </div>
              )}
            </AbsoluteFill>
          </Sequence>
        );
      })}

      <ProgressBar color="#667eea" />
    </AbsoluteFill>
  );
};
