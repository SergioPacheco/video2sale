/**
 * Template: Produto Destaque (ideal para modo Híbrido)
 * Estrutura: Foco total no produto com imagens reais, zoom, detalhes
 * Estilo: Fundo limpo, produto em destaque, texto mínimo
 */
import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import { VideoProps } from "../types";
import { SceneText } from "../components/SceneText";
import { ProgressBar } from "../components/ProgressBar";
import { ProductImage } from "../components/ProductImage";

export const ProdutoDestaque: React.FC<VideoProps> = ({
  scenes,
  productName,
  category,
  localImages,
}) => {
  const { fps } = useVideoConfig();

  const effects: Array<"zoom-in" | "zoom-out" | "pan" | "static"> = [
    "zoom-in",
    "zoom-out",
    "pan",
    "zoom-in",
    "zoom-out",
    "static",
  ];

  return (
    <AbsoluteFill>
      {scenes.map((scene, i) => {
        const startFrame = scene.start * fps;
        const durationFrames = (scene.end - scene.start) * fps;
        const hasImage = localImages.length > 0;
        const imageIndex = i % Math.max(localImages.length, 1);
        const effect = effects[i % effects.length];

        return (
          <Sequence key={i} from={startFrame} durationInFrames={durationFrames}>
            <AbsoluteFill>
              {/* Background base */}
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: "linear-gradient(180deg, #0f0f0f 0%, #1a1a1a 100%)",
                }}
              />

              {/* Imagem do produto (fullscreen com efeito) */}
              {hasImage && (
                <ProductImage
                  src={localImages[imageIndex]}
                  effect={effect}
                  opacity={0.85}
                />
              )}

              {/* Gradient overlay (bottom) para legibilidade do texto */}
              <div
                style={{
                  position: "absolute",
                  bottom: 0,
                  left: 0,
                  right: 0,
                  height: "50%",
                  background: "linear-gradient(transparent, rgba(0,0,0,0.85))",
                }}
              />

              {/* Gradient overlay (top) para nome do produto */}
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  right: 0,
                  height: "20%",
                  background: "linear-gradient(rgba(0,0,0,0.6), transparent)",
                }}
              />

              {/* Categoria + Nome (top) */}
              {i === 0 && (
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
                      color: "#ff2d55",
                      fontSize: 20,
                      fontWeight: 600,
                      fontFamily: "'Inter', sans-serif",
                      textTransform: "uppercase",
                      letterSpacing: 2,
                    }}
                  >
                    {category}
                  </div>
                  <div
                    style={{
                      color: "white",
                      fontSize: 32,
                      fontWeight: 800,
                      fontFamily: "'Inter', sans-serif",
                      marginTop: 8,
                    }}
                  >
                    {productName}
                  </div>
                </div>
              )}

              {/* Texto da cena (bottom) */}
              <SceneText
                text={scene.text}
                fontSize={i === 0 ? 56 : 44}
                position="bottom"
                style="shadow"
              />

              {/* Indicador de imagem (dots) */}
              {hasImage && localImages.length > 1 && (
                <div
                  style={{
                    position: "absolute",
                    top: "50%",
                    right: 20,
                    display: "flex",
                    flexDirection: "column",
                    gap: 8,
                  }}
                >
                  {localImages.map((_, dotIdx) => (
                    <div
                      key={dotIdx}
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        background: dotIdx === imageIndex ? "#ff2d55" : "rgba(255,255,255,0.3)",
                      }}
                    />
                  ))}
                </div>
              )}

              {/* CTA última cena */}
              {i === scenes.length - 1 && (
                <div
                  style={{
                    position: "absolute",
                    bottom: 60,
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
                      fontWeight: 800,
                      fontFamily: "'Inter', sans-serif",
                      boxShadow: "0 4px 20px rgba(255,45,85,0.4)",
                    }}
                  >
                    🛒 Comprar ahora
                  </div>
                </div>
              )}
            </AbsoluteFill>
          </Sequence>
        );
      })}

      <ProgressBar color="#ff2d55" height={5} />
    </AbsoluteFill>
  );
};
