const express = require("express");
const multer = require("multer");
const cors = require("cors");
const { spawn } = require("child_process");
const fs = require("fs/promises");
const path = require("path");
const os = require("os");
const crypto = require("crypto");

const app = express();
app.use(cors({ origin: process.env.ALLOW_ORIGIN || "*" }));

const upload = multer({
  dest: path.join(os.tmpdir(), "rs_uploads"),
  limits: { fileSize: 30 * 1024 * 1024, files: 40 },
});

app.get("/", (_req, res) => res.json({ ok: true, service: "reels-render" }));

app.post("/generate", upload.array("images", 40), async (req, res) => {
  const files = req.files || [];
  try {
    if (!files.length) return res.status(400).json({ error: "En az bir görsel gerekli." });
    const meta = JSON.parse(req.body.meta || "{}");
    const items = meta.items || [];

    const id = crypto.randomBytes(6).toString("hex");
    const job = path.join(os.tmpdir(), "rs_jobs", id);
    const work = path.join(job, "work");
    await fs.mkdir(work, { recursive: true });

    const images = [];
    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      const ext = (f.originalname.split(".").pop() || "jpg").toLowerCase().replace(/[^a-z0-9]/g, "") || "jpg";
      const p = path.join(job, `img_${String(i).padStart(2, "0")}.${ext}`);
      await fs.rename(f.path, p);
      const it = items[i] || {};
      images.push({
        path: p,
        caption: (it.caption || "").toString(),
        duration: Number(it.duration) > 0 ? Number(it.duration) : 3.5,
        zoom: it.zoom === "out" ? "out" : i % 2 === 0 ? "in" : "out",
      });
    }

    const output = path.join(job, "out.mp4");
    const manifest = {
      images, output, workdir: work,
      width: Number(meta.width) || 1080,
      height: Number(meta.height) || 1920,
      fps: Number(meta.fps) || 30,
      xfade: meta.xfade != null ? Number(meta.xfade) : 1.0,
      music: meta.music ?? true,
      grade: meta.grade !== false,
      font: meta.font || "sans",
      fontScale: meta.fontScale != null ? Number(meta.fontScale) : 1.0,
      captionPos: meta.captionPos || "bottom",
      captionColor: meta.captionColor || "#ffffff",
    };
    const manPath = path.join(job, "manifest.json");
    await fs.writeFile(manPath, JSON.stringify(manifest));

    const py = path.join(__dirname, "pipeline", "generate_video.py");
    const r = await new Promise((resolve) => {
      const ps = spawn(process.env.PYTHON || "python3", [py, manPath]);
      let out = "", err = "";
      ps.stdout.on("data", (d) => (out += d.toString()));
      ps.stderr.on("data", (d) => (err += d.toString()));
      ps.on("close", (code) => resolve({ code, out, err }));
      ps.on("error", (e) => resolve({ code: 1, out: "", err: String(e) }));
    });

    if (r.code !== 0) {
      console.error("render failed:", r.err);
      await fs.rm(job, { recursive: true, force: true }).catch(() => {});
      return res.status(500).json({ error: "Render başarısız.", detail: r.err.slice(-1200) });
    }

    const data = await fs.readFile(output);
    res.setHeader("Content-Type", "video/mp4");
    res.setHeader("Content-Disposition", `attachment; filename="reels_${id}.mp4"`);
    res.send(data);
    fs.rm(job, { recursive: true, force: true }).catch(() => {});
  } catch (e) {
    console.error(e);
    for (const f of files) fs.rm(f.path, { force: true }).catch(() => {});
    res.status(500).json({ error: String(e) });
  }
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log("reels render service listening on :" + PORT));
