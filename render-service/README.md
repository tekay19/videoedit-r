# Reels Render Service

ffmpeg + Python video-generation backend. The editor (on Vercel) uploads images here,
and this service renders the cinematic slideshow and returns it as an MP4.

## Endpoint

`POST /generate` — `multipart/form-data`
- `images`: image files (in order)
- `meta`: JSON string →
  ```json
  {
    "items": [{ "caption": "Line 1\nLine 2", "duration": 3.5, "zoom": "in" }],
    "width": 1080, "height": 1920, "fps": 30,
    "xfade": 1.0, "music": true, "grade": true
  }
  ```
- Response: `video/mp4` (binary)

`GET /` → health check.

## Run locally

Requires `node`, `ffmpeg`, `python3` + `Pillow`.

```bash
npm install
npm start          # http://localhost:8080
```

## Docker

```bash
docker build -t reels-render .
docker run -p 8080:8080 reels-render
```

## Deploy (Railway / Render / Fly)

All of them auto-detect the `Dockerfile` in this folder:

- **Railway:** New Project → Deploy from Repo → pick this folder → Docker build → expose a public domain.
- **Render:** New → Web Service → Docker → root = `render-service`. Port 8080.
- **Fly.io:** `fly launch` (detects the Dockerfile) → `fly deploy`.

After deploy, put the resulting URL into the editor: set **`NEXT_PUBLIC_RENDER_URL`**
in the Vercel project to this URL.

## Environment variables

- `PORT` (default 8080)
- `ALLOW_ORIGIN` (CORS; default `*` — set your Vercel domain in production)
- `PYTHON` (default `python3`)
