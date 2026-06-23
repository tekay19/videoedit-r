FROM node:20-bookworm-slim

# ffmpeg + python3 + Pillow (PIL) + altyazi fontlari (Turkce karakter destekli)
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg \
      python3 \
      python3-pil \
      fonts-dejavu-core \
      fonts-liberation \
      fonts-noto-core \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --omit=dev

COPY . .

ENV PORT=8080
EXPOSE 8080
CMD ["node", "server.js"]
