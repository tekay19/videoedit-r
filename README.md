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

### Backend → Railway / Render / Fly (Docker)
`render-service/Dockerfile` is ready. Connect this repo, set the service root to
`render-service`, and deploy. You get a public URL, e.g. `https://xxx.up.railway.app`.

### Frontend → Vercel
1. Import this repo, set **Root Directory = `web`**.
2. Add an environment variable:
   ```
   NEXT_PUBLIC_RENDER_URL = https://your-render-url
   ```
3. Deploy.

> In production, set `ALLOW_ORIGIN` on the backend to your Vercel domain (CORS).

## How it works

1. The editor collects images, captions, per-scene duration/zoom, and the output format.
2. It sends them to `POST {NEXT_PUBLIC_RENDER_URL}/generate` (multipart).
3. The service runs [`pipeline/generate_video.py`](render-service/pipeline/generate_video.py)
   and returns an MP4.
4. The editor plays the result and offers a download link.

## Stack

Next.js (App Router, TypeScript, Tailwind) · Express + multer · Python (Pillow) + ffmpeg.
