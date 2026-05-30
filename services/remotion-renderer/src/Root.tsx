import React from "react";
import { Composition } from "remotion";
import { ProblemaSolucao } from "./templates/ProblemaSolucao";
import { AntesDepois } from "./templates/AntesDepois";
import { ReviewHonesto } from "./templates/ReviewHonesto";
import { TresMotivos } from "./templates/TresMotivos";
import { ProdutoDestaque } from "./templates/ProdutoDestaque";

const FPS = 30;
const DURATION = 30; // 30 segundos

const defaultProps = {
  mode: "template" as const,
  template: "problema-solucao",
  productName: "Producto Demo",
  category: "Hogar",
  hook: "¿Cansado de este problema?",
  scenes: [
    { start: 0, end: 3, text: "¿Cansado de esto?", voiceover: "", visual: "" },
    { start: 3, end: 8, text: "Mira esta solución", voiceover: "", visual: "" },
    { start: 8, end: 15, text: "Funciona así", voiceover: "", visual: "" },
    { start: 15, end: 22, text: "Resultados reales", voiceover: "", visual: "" },
    { start: 22, end: 27, text: "Miles ya lo usan", voiceover: "", visual: "" },
    { start: 27, end: 30, text: "Link en bio 👇", voiceover: "", visual: "" },
  ],
  localImages: [] as string[],
  caption: "",
  hashtags: [] as string[],
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ProblemaSolucao"
        component={ProblemaSolucao}
        durationInFrames={DURATION * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={defaultProps}
      />
      <Composition
        id="AntesDepois"
        component={AntesDepois}
        durationInFrames={DURATION * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={defaultProps}
      />
      <Composition
        id="ReviewHonesto"
        component={ReviewHonesto}
        durationInFrames={DURATION * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={defaultProps}
      />
      <Composition
        id="TresMotivos"
        component={TresMotivos}
        durationInFrames={DURATION * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={defaultProps}
      />
      <Composition
        id="ProdutoDestaque"
        component={ProdutoDestaque}
        durationInFrames={DURATION * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={defaultProps}
      />
    </>
  );
};
