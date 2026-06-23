# Reels Studio — Editor (frontend)

Next.js editor UI. Upload images, add a caption to each, pick a format, and generate
a cinematic vertical video. The heavy rendering runs on the separate render service.

See the [root README](../README.md) for the full picture and deploy steps.

## Run

```bash
npm install
npm run dev          # http://localhost:3000
```

Set the backend URL in `.env.local`:
```
NEXT_PUBLIC_RENDER_URL=http://localhost:8080
```

## Deploy on Vercel

Import the repo with **Root Directory = `web`** and set the `NEXT_PUBLIC_RENDER_URL`
environment variable to your deployed render-service URL.
