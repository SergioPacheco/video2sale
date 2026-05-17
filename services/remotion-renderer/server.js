const express = require("express");
const { bundle } = require("@remotion/bundler");
const { renderMedia, selectComposition } = require("@remotion/renderer");
const path = require("path");
const fs = require("fs");

const app = express();
app.use(express.json());

const PORT = 8002;

app.get("/health", (req, res) => {
  res.json({ status: "ok", service: "remotion-renderer" });
});

app.post("/render-video", async (req, res) => {
  try {
    const { week, product_id, template, creative_pack_path, voiceover_path } =
      req.body;

    // TODO: Implementar renderização real com Remotion
    // 1. Ler creative-pack.json
    // 2. Selecionar template
    // 3. Renderizar com @remotion/renderer
    // 4. Exportar MP4

    const outputDir = `/output/${week}/${product_id}`;
    fs.mkdirSync(outputDir, { recursive: true });

    // Placeholder — será substituído pela renderização real
    const videoPath = path.join(outputDir, "video-final.mp4");
    const thumbnailPath = path.join(outputDir, "thumbnail.png");

    res.json({
      status: "OK",
      video_path: videoPath,
      thumbnail_path: thumbnailPath,
      template: template || "problema-solucao",
    });
  } catch (error) {
    res.status(500).json({ status: "ERROR", error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Remotion Renderer listening on port ${PORT}`);
});
