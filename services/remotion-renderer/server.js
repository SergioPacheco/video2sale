const express = require("express");
const { bundle } = require("@remotion/bundler");
const { renderMedia, selectComposition } = require("@remotion/renderer");
const path = require("path");
const fs = require("fs");
const { execSync } = require("child_process");
const https = require("https");
const http = require("http");

const app = express();
app.use(express.json({ limit: "10mb" }));

const PORT = 8002;
const BUNDLE_PATH = path.join(__dirname, "src", "index.ts");

let bundled = null;

// Pre-bundle on startup
async function prebundle() {
  console.log("[REMOTION] Bundling compositions...");
  bundled = await bundle({
    entryPoint: BUNDLE_PATH,
    webpackOverride: (config) => config,
  });
  console.log("[REMOTION] Bundle ready.");
}

// Download file from URL to local path
function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    const client = url.startsWith("https") ? https : http;
    client
      .get(url, (response) => {
        if (response.statusCode === 301 || response.statusCode === 302) {
          downloadFile(response.headers.location, dest).then(resolve).catch(reject);
          return;
        }
        response.pipe(file);
        file.on("finish", () => {
          file.close();
          resolve(dest);
        });
      })
      .on("error", (err) => {
        fs.unlink(dest, () => {});
        reject(err);
      });
  });
}

// Download assets to local temp dir
async function downloadAssets(urls, outputDir) {
  const localPaths = [];
  fs.mkdirSync(outputDir, { recursive: true });

  for (let i = 0; i < urls.length; i++) {
    const url = urls[i];
    if (!url) continue;
    const ext = path.extname(new URL(url).pathname) || ".jpg";
    const localPath = path.join(outputDir, `asset-${i}${ext}`);
    try {
      await downloadFile(url, localPath);
      localPaths.push(localPath);
    } catch (e) {
      console.warn(`[DOWNLOAD] Failed: ${url} — ${e.message}`);
    }
  }
  return localPaths;
}

app.get("/health", (req, res) => {
  res.json({ status: "ok", service: "remotion-renderer", bundled: !!bundled });
});

// =============================================================================
// UNIFIED RENDER ENDPOINT
// =============================================================================

app.post("/render", async (req, res) => {
  const startTime = Date.now();

  try {
    const {
      mode,
      week,
      product_id,
      template,
      product_name,
      category,
      hook,
      scenes,
      voiceover_path,
      image_urls,
      assets,
      caption,
      hashtags,
      provider,
    } = req.body;

    if (!bundled) {
      await prebundle();
    }

    const outputDir = `/output/${week}/${product_id}`;
    fs.mkdirSync(outputDir, { recursive: true });

    let videoPath, thumbnailPath, cost = 0, clipsCount = 0;

    if (mode === "ai_generative") {
      // === OPÇÃO 2: IA Generativa ===
      const result = await renderAIGenerative({
        provider,
        scenes,
        voiceover_path,
        outputDir,
        product_name,
        hook,
      });
      videoPath = result.videoPath;
      thumbnailPath = result.thumbnailPath;
      cost = result.cost;
      clipsCount = result.clipsCount;
    } else {
      // === OPÇÃO 1 (template) ou OPÇÃO 3 (hybrid) ===
      // Baixar imagens se fornecidas
      let localImages = [];
      const assetsDir = path.join(outputDir, "assets");

      if (mode === "hybrid" && assets) {
        const allUrls = [...(assets.images || []), ...(assets.videos || [])];
        localImages = await downloadAssets(allUrls, assetsDir);
      } else if (image_urls && image_urls.length > 0) {
        localImages = await downloadAssets(image_urls, assetsDir);
      }

      // Selecionar composição baseada no template
      const compositionId = getCompositionId(template || "problema-solucao", mode);

      const composition = await selectComposition({
        serveUrl: bundled,
        id: compositionId,
        inputProps: {
          mode: mode || "template",
          template: template || "problema-solucao",
          productName: product_name || "",
          category: category || "",
          hook: hook || "",
          scenes: scenes || [],
          localImages,
          caption: caption || "",
          hashtags: hashtags || [],
        },
      });

      // Renderizar
      const outputFile = path.join(outputDir, `video-${mode}-${Date.now()}.mp4`);

      await renderMedia({
        composition,
        serveUrl: bundled,
        codec: "h264",
        outputLocation: outputFile,
        inputProps: {
          mode: mode || "template",
          template: template || "problema-solucao",
          productName: product_name || "",
          category: category || "",
          hook: hook || "",
          scenes: scenes || [],
          localImages,
          caption: caption || "",
          hashtags: hashtags || [],
        },
        chromiumOptions: {
          enableMultiProcessOnLinux: true,
        },
      });

      videoPath = outputFile;

      // Gerar thumbnail (frame do segundo 2)
      thumbnailPath = path.join(outputDir, "thumbnail.png");
      try {
        execSync(
          `ffmpeg -y -i "${outputFile}" -ss 2 -vframes 1 -q:v 2 "${thumbnailPath}"`,
          { stdio: "pipe" }
        );
      } catch (e) {
        console.warn("[THUMBNAIL] Failed:", e.message);
        thumbnailPath = null;
      }

      // Mixar áudio se voiceover existe
      if (voiceover_path && fs.existsSync(voiceover_path)) {
        const finalPath = path.join(outputDir, `video-final-${Date.now()}.mp4`);
        try {
          execSync(
            `ffmpeg -y -i "${outputFile}" -i "${voiceover_path}" ` +
              `-c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest "${finalPath}"`,
            { stdio: "pipe" }
          );
          // Substituir pelo vídeo com áudio
          fs.unlinkSync(outputFile);
          videoPath = finalPath;
        } catch (e) {
          console.warn("[AUDIO MIX] Failed:", e.message);
          // Manter vídeo sem áudio
        }
      }
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`[RENDER] ${mode} done in ${elapsed}s → ${videoPath}`);

    res.json({
      status: "ok",
      video_path: videoPath,
      thumbnail_path: thumbnailPath,
      mode,
      template: template || null,
      cost,
      clips_count: clipsCount,
      elapsed_seconds: parseFloat(elapsed),
    });
  } catch (error) {
    console.error("[RENDER ERROR]", error);
    res.status(500).json({
      status: "error",
      error: error.message,
      stack: process.env.NODE_ENV === "development" ? error.stack : undefined,
    });
  }
});

// =============================================================================
// AI GENERATIVE RENDER (Opção 2)
// =============================================================================

async function renderAIGenerative({ provider, scenes, voiceover_path, outputDir, product_name, hook }) {
  const clipsDir = path.join(outputDir, "clips");
  fs.mkdirSync(clipsDir, { recursive: true });

  let totalCost = 0;
  const clipPaths = [];

  for (let i = 0; i < scenes.length; i++) {
    const scene = scenes[i];
    const clipPath = path.join(clipsDir, `clip-${i}.mp4`);

    console.log(`[AI-GEN] Scene ${i + 1}/${scenes.length}: ${scene.prompt.substring(0, 80)}...`);

    try {
      const result = await generateClip(provider, scene.prompt, scene.duration || 5, clipPath);
      clipPaths.push(clipPath);
      totalCost += result.cost;
    } catch (e) {
      console.error(`[AI-GEN] Scene ${i} failed: ${e.message}`);
      // Gerar placeholder (tela preta com texto)
      const duration = scene.duration || 5;
      execSync(
        `ffmpeg -y -f lavfi -i color=c=black:s=1080x1920:d=${duration} ` +
          `-vf "drawtext=text='${(scene.text_overlay || "").replace(/'/g, "")}':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2" ` +
          `-c:v libx264 -pix_fmt yuv420p "${clipPath}"`,
        { stdio: "pipe" }
      );
      clipPaths.push(clipPath);
    }
  }

  // Concatenar clips
  const concatFile = path.join(clipsDir, "concat.txt");
  const concatContent = clipPaths.map((p) => `file '${p}'`).join("\n");
  fs.writeFileSync(concatFile, concatContent);

  const rawVideo = path.join(outputDir, `video-ai-raw-${Date.now()}.mp4`);
  execSync(
    `ffmpeg -y -f concat -safe 0 -i "${concatFile}" -c:v libx264 -pix_fmt yuv420p "${rawVideo}"`,
    { stdio: "pipe" }
  );

  // Mixar áudio
  let finalPath = rawVideo;
  if (voiceover_path && fs.existsSync(voiceover_path)) {
    finalPath = path.join(outputDir, `video-ai-final-${Date.now()}.mp4`);
    try {
      execSync(
        `ffmpeg -y -i "${rawVideo}" -i "${voiceover_path}" ` +
          `-c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest "${finalPath}"`,
        { stdio: "pipe" }
      );
      fs.unlinkSync(rawVideo);
    } catch (e) {
      finalPath = rawVideo;
    }
  }

  // Thumbnail
  let thumbnailPath = path.join(outputDir, "thumbnail.png");
  try {
    execSync(`ffmpeg -y -i "${finalPath}" -ss 2 -vframes 1 -q:v 2 "${thumbnailPath}"`, { stdio: "pipe" });
  } catch (e) {
    thumbnailPath = null;
  }

  return {
    videoPath: finalPath,
    thumbnailPath,
    cost: totalCost,
    clipsCount: clipPaths.length,
  };
}

// Generate a single clip via AI provider
async function generateClip(provider, prompt, durationSec, outputPath) {
  switch (provider) {
    case "seedance":
      return await generateSeedance(prompt, durationSec, outputPath);
    case "runway":
      return await generateRunway(prompt, durationSec, outputPath);
    case "kling":
      return await generateKling(prompt, durationSec, outputPath);
    default:
      throw new Error(`Provider desconhecido: ${provider}`);
  }
}

// --- Seedance (ByteDance) ---
async function generateSeedance(prompt, durationSec, outputPath) {
  // Seedance não tem API pública oficial ainda.
  // Placeholder: gera vídeo placeholder com o prompt como texto.
  // Quando a API estiver disponível, substituir por chamada real.
  console.log(`[SEEDANCE] Placeholder — API não disponível publicamente`);

  execSync(
    `ffmpeg -y -f lavfi -i color=c=0x1a1a2e:s=1080x1920:d=${durationSec} ` +
      `-vf "drawtext=text='[Seedance]\\n${prompt.substring(0, 60).replace(/'/g, "")}':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=10" ` +
      `-c:v libx264 -pix_fmt yuv420p "${outputPath}"`,
    { stdio: "pipe" }
  );

  return { cost: 0, status: "placeholder" };
}

// --- Runway Gen-3 ---
async function generateRunway(prompt, durationSec, outputPath) {
  const apiKey = process.env.RUNWAY_API_KEY;
  if (!apiKey) {
    console.log(`[RUNWAY] No API key — generating placeholder`);
    execSync(
      `ffmpeg -y -f lavfi -i color=c=0x16213e:s=1080x1920:d=${durationSec} ` +
        `-vf "drawtext=text='[Runway]\\n${prompt.substring(0, 60).replace(/'/g, "")}':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=10" ` +
        `-c:v libx264 -pix_fmt yuv420p "${outputPath}"`,
      { stdio: "pipe" }
    );
    return { cost: 0, status: "placeholder" };
  }

  // Runway Gen-3 Alpha Turbo API
  // POST https://api.dev.runwayml.com/v1/image_to_video ou text_to_video
  const fetch = (await import("node-fetch")).default;

  const resp = await fetch("https://api.dev.runwayml.com/v1/text_to_video", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      "X-Runway-Version": "2024-11-06",
    },
    body: JSON.stringify({
      model: "gen3a_turbo",
      prompt: prompt,
      duration: Math.min(durationSec, 10),
      ratio: "9:16",
    }),
  });

  if (!resp.ok) {
    throw new Error(`Runway API error: ${resp.status} ${await resp.text()}`);
  }

  const data = await resp.json();
  const taskId = data.id;

  // Poll até completar
  let videoUrl = null;
  for (let attempt = 0; attempt < 60; attempt++) {
    await new Promise((r) => setTimeout(r, 5000));
    const statusResp = await fetch(`https://api.dev.runwayml.com/v1/tasks/${taskId}`, {
      headers: { Authorization: `Bearer ${apiKey}`, "X-Runway-Version": "2024-11-06" },
    });
    const statusData = await statusResp.json();

    if (statusData.status === "SUCCEEDED") {
      videoUrl = statusData.output[0];
      break;
    } else if (statusData.status === "FAILED") {
      throw new Error(`Runway task failed: ${statusData.failure}`);
    }
  }

  if (!videoUrl) throw new Error("Runway timeout");

  await downloadFile(videoUrl, outputPath);
  return { cost: 0.25, status: "generated" };
}

// --- Kling AI ---
async function generateKling(prompt, durationSec, outputPath) {
  const apiKey = process.env.KLING_API_KEY;
  if (!apiKey) {
    console.log(`[KLING] No API key — generating placeholder`);
    execSync(
      `ffmpeg -y -f lavfi -i color=c=0x0f3460:s=1080x1920:d=${durationSec} ` +
        `-vf "drawtext=text='[Kling]\\n${prompt.substring(0, 60).replace(/'/g, "")}':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=10" ` +
        `-c:v libx264 -pix_fmt yuv420p "${outputPath}"`,
      { stdio: "pipe" }
    );
    return { cost: 0, status: "placeholder" };
  }

  // Kling API (quando disponível)
  // Similar ao Runway: submit task → poll → download
  const fetch = (await import("node-fetch")).default;

  const resp = await fetch("https://api.klingai.com/v1/videos/text2video", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      prompt: prompt,
      duration: String(Math.min(durationSec, 5)),
      aspect_ratio: "9:16",
      model: "kling-v1",
    }),
  });

  if (!resp.ok) {
    throw new Error(`Kling API error: ${resp.status}`);
  }

  const data = await resp.json();
  const taskId = data.data?.task_id;

  let videoUrl = null;
  for (let attempt = 0; attempt < 60; attempt++) {
    await new Promise((r) => setTimeout(r, 5000));
    const statusResp = await fetch(`https://api.klingai.com/v1/videos/text2video/${taskId}`, {
      headers: { Authorization: `Bearer ${apiKey}` },
    });
    const statusData = await statusResp.json();

    if (statusData.data?.task_status === "succeed") {
      videoUrl = statusData.data.task_result?.videos?.[0]?.url;
      break;
    } else if (statusData.data?.task_status === "failed") {
      throw new Error("Kling task failed");
    }
  }

  if (!videoUrl) throw new Error("Kling timeout");

  await downloadFile(videoUrl, outputPath);
  return { cost: 0.10, status: "generated" };
}

// =============================================================================
// HELPERS
// =============================================================================

function getCompositionId(template, mode) {
  // Mapear template para composição Remotion
  const map = {
    "problema-solucao": "ProblemaSolucao",
    "antes-depois": "AntesDepois",
    "review-honesto": "ReviewHonesto",
    "3-motivos": "TresMotivos",
    "produto-destaque": "ProdutoDestaque",
  };
  return map[template] || "ProblemaSolucao";
}

// =============================================================================
// STARTUP
// =============================================================================

app.listen(PORT, async () => {
  console.log(`Remotion Renderer listening on port ${PORT}`);
  try {
    await prebundle();
  } catch (e) {
    console.error("[BUNDLE ERROR]", e.message);
    console.log("[REMOTION] Will bundle on first request.");
  }
});
