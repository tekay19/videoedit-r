# Reels Studio

Upload images → write a caption for each → generate a **cinematic vertical video**
with one click: Ken Burns zoom, smooth crossfades, burned-in captions, background
music, and a film color grade.

## Architecture

Two parts, because Vercel's serverless functions can't run `ffmpeg`/`python` (and
have execution-time / file-system limits), so the heavy rendering lives in a
separate Docker service that the editor calls.

| Part | Folder | Runs on | Role |
|------|--------|---------|------|
| **Editor** (frontend) | [`web/`](web) | **Vercel** | Upload & caption UI |
| **Render service** (backend) | [`render-service/`](render-service) | **Railway / Render / Fly / VPS** | `ffmpeg` + Python video generation |

## Local development

**1) Render service** (requires `ffmpeg`, `python3` + `Pillow`, `node`):
```bash
cd render-service
npm install
npm start            # http://localhost:8080
```

**2) Editor:**
```bash
cd web
npm install
npm run dev          # http://localhost:3000
```

`web/.env.local` points the editor at the render service:
```
NEXT_PUBLIC_RENDER_URL=http://localhost:8080
```

## Deploy

Deploy the **backend first**, get its URL, then deploy the **frontend** with that URL.

### Step 1 — Backend → Render (Docker)
This repo ships a [`render.yaml`](render.yaml) blueprint.

- **Render Dashboard → New → Blueprint → pick this repo.** Render reads `render.yaml`
  and builds `render-service/Dockerfile` automatically.
- Or manually: New → Web Service → Docker, **Root Directory = `render-service`**.
- When it's live you get a URL like `https://reels-render.onrender.com`. Copy it.

> The blueprint uses the **free** plan. If renders fail/OOM on long videos, bump the
> plan to `starter`/`standard` in Render (more RAM/CPU). (Also works on Railway / Fly.)

### Step 2 — Frontend → Vercel
1. Import this repo, set **Root Directory = `web`**.
2. Add an environment variable with the URL from Step 1:
   ```
   NEXT_PUBLIC_RENDER_URL = https://reels-render.onrender.com
   ```
3. Deploy.

> After Vercel gives you a domain, set `ALLOW_ORIGIN` on the Render service to that
> domain (instead of `*`) for tighter CORS.

## How it works

1. The editor collects images, captions, per-scene duration/zoom, and the output format.
2. It sends them to `POST {NEXT_PUBLIC_RENDER_URL}/generate` (multipart).
3. The service runs [`pipeline/generate_video.py`](render-service/pipeline/generate_video.py)
   and returns an MP4.
4. The editor plays the result and offers a download link.

## Stack

Next.js (App Router, TypeScript, Tailwind) · Express + multer · Python (Pillow) + ffmpeg.
