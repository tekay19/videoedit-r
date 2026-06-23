FROM node:20-bookworm-slim

# ffmpeg + python3 + Pillow (PIL) + DejaVu fonts (Turkce karakterler icin)
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg \
      python3 \
      python3-pil \
      fonts-dejavu-core \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --omit=dev

COPY . .

ENV PORT=8080
EXPOSE 8080
CMD ["node", "server.js"]
