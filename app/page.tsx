"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Item = {
  id: string;
  file: File;
  preview: string;
  caption: string;
  duration: number;
  zoom: "in" | "out";
};

const ASPECTS = [
  { key: "9:16", label: "9:16 Dikey (Reels)", w: 1080, h: 1920 },
  { key: "1:1", label: "1:1 Kare", w: 1080, h: 1080 },
  { key: "16:9", label: "16:9 Yatay", w: 1920, h: 1080 },
];

const TRACKS = [
  { id: "", name: "🔇 Müzik yok" },
  { id: "zafer", name: "Zafer — coşkulu" },
  { id: "duygusal", name: "Duygusal — yumuşak" },
  { id: "sinematik", name: "Sinematik" },
  { id: "epik", name: "Epik" },
  { id: "cosku", name: "Coşku — hızlı" },
  { id: "umut", name: "Umut" },
  { id: "dramatik", name: "Dramatik" },
  { id: "mars", name: "Marş" },
  { id: "huzun", name: "Hüzün" },
  { id: "enerji", name: "Enerji — tempolu" },
];

const FONTS = [
  { id: "sans", name: "Sans (Kalın)" },
  { id: "serif", name: "Serif (Klasik)" },
  { id: "modern", name: "Modern" },
  { id: "noto", name: "Yumuşak" },
];

const RENDER_URL = process.env.NEXT_PUBLIC_RENDER_URL || "https://sem120-reels-render.hf.space";

let uid = 0;
const nextId = () => `i${uid++}`;

export default function Editor() {
  const [items, setItems] = useState<Item[]>([]);
  const [aspect, setAspect] = useState(ASPECTS[0]);
  const [music, setMusic] = useState("zafer");
  const [font, setFont] = useState("sans");
  const [grade, setGrade] = useState(true);
  const [xfade, setXfade] = useState(1.0);
  const [defaultDur, setDefaultDur] = useState(3.5);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [fontScale, setFontScale] = useState(1.0);
  const [captionColor, setCaptionColor] = useState("#ffffff");
  const [captionPos, setCaptionPos] = useState("bottom");
  const [splash, setSplash] = useState<"show" | "hide" | "gone">("show");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const t1 = setTimeout(() => setSplash("hide"), 2000);
    const t2 = setTimeout(() => setSplash("gone"), 2900);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, []);

  const addFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;
      const arr = Array.from(files).filter((f) => f.type.startsWith("image/"));
      setItems((prev) => [
        ...prev,
        ...arr.map((f, i) => ({
          id: nextId(),
          file: f,
          preview: URL.createObjectURL(f),
          caption: "",
          duration: defaultDur,
          zoom: ((prev.length + i) % 2 === 0 ? "in" : "out") as "in" | "out",
        })),
      ]);
    },
    [defaultDur]
  );

  const update = (id: string, patch: Partial<Item>) =>
    setItems((p) => p.map((it) => (it.id === id ? { ...it, ...patch } : it)));
  const remove = (id: string) => setItems((p) => p.filter((it) => it.id !== id));
  const move = (i: number, dir: -1 | 1) =>
    setItems((p) => {
      const j = i + dir;
      if (j < 0 || j >= p.length) return p;
      const n = [...p];
      [n[i], n[j]] = [n[j], n[i]];
      return n;
    });
  const dropAt = (target: number) =>
    setItems((p) => {
      if (dragIndex === null || dragIndex === target) return p;
      const n = [...p];
      const [moved] = n.splice(dragIndex, 1);
      n.splice(target, 0, moved);
      return n;
    });
  const applyDurationToAll = (d: number) => {
    setDefaultDur(d);
    setItems((p) => p.map((it) => ({ ...it, duration: d })));
  };

  const totalDur = items.reduce((s, it) => s + it.duration, 0) - Math.max(0, items.length - 1) * xfade;

  async function generate() {
    if (items.length === 0) return;
    setBusy(true);
    setError(null);
    if (resultUrl) URL.revokeObjectURL(resultUrl);
    setResultUrl(null);
    try {
      const fd = new FormData();
      items.forEach((it) => fd.append("images", it.file, it.file.name));
      fd.append(
        "meta",
        JSON.stringify({
          items: items.map((it) => ({ caption: it.caption, duration: it.duration, zoom: it.zoom })),
          width: aspect.w,
          height: aspect.h,
          music: music || false,
          font,
          fontScale,
          captionColor,
          captionPos,
          grade,
          xfade,
        })
      );
      const res = await fetch(`${RENDER_URL}/generate`, { method: "POST", body: fd });
      if (!res.ok) {
        let msg = `Hata (${res.status})`;
        try {
          const j = await res.json();
          msg = (j.error || msg) + (j.detail ? `\n${j.detail}` : "");
        } catch {}
        throw new Error(msg);
      }
      const blob = await res.blob();
      setResultUrl(URL.createObjectURL(blob));
    } catch (e) {
      setError(
        e instanceof Error
          ? `${e.message}\n\nRender servisine ulaşılamıyor olabilir: ${RENDER_URL}`
          : String(e)
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      {splash !== "gone" && (
        <div
          className={`fixed inset-0 z-50 flex flex-col items-center justify-center overflow-hidden bg-black transition-all duration-[900ms] ease-in-out ${
            splash === "hide" ? "pointer-events-none scale-110 opacity-0 blur-md" : "opacity-100"
          }`}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/logo.jpg" alt="" className="absolute inset-0 h-full w-full object-cover animate-[kenburns_3s_ease-out_forwards]" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-black/55" />
          <div className="relative mt-auto mb-24 text-center">
            <h1 className="text-4xl font-extrabold tracking-tight text-white drop-shadow-[0_2px_14px_rgba(0,0,0,0.85)]">🎬 Reels Stüdyo</h1>
            <p className="mt-2 text-sm text-amber-300/90">sinematik video editörü</p>
            <div className="mx-auto mt-5 h-1 w-28 overflow-hidden rounded-full bg-white/20">
              <div className="h-full origin-left animate-[load_2s_ease-out_forwards] bg-amber-400" />
            </div>
          </div>
        </div>
      )}
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-neutral-800 bg-neutral-950/90 px-6 py-4 backdrop-blur">
        <div className="flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo.jpg"
            alt="Logo"
            className="h-11 w-11 rounded-full object-cover object-top ring-2 ring-amber-500/70"
          />
          <div>
            <h1 className="text-xl font-bold tracking-tight">🎬 Reels Stüdyo</h1>
            <p className="text-xs text-neutral-400">Resim yükle · altyazı yaz · sinematik video üret</p>
          </div>
        </div>
        <button
          onClick={generate}
          disabled={busy || items.length === 0}
          className="rounded-lg bg-amber-500 px-5 py-2.5 font-semibold text-black transition hover:bg-amber-400 disabled:opacity-40"
        >
          {busy ? "Üretiliyor…" : "▶ Videoyu Üret"}
        </button>
      </header>

      <main className="mx-auto grid max-w-5xl gap-6 px-6 py-6 lg:grid-cols-[1fr_320px]">
        <section>
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
            }}
            className="mb-4 rounded-xl border-2 border-dashed border-neutral-700 p-6 text-center transition hover:border-amber-500/60"
          >
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              multiple
              hidden
              onChange={(e) => {
                addFiles(e.target.files);
                e.target.value = "";
              }}
            />
            <button
              onClick={() => fileRef.current?.click()}
              className="rounded-lg bg-neutral-800 px-4 py-2 font-medium hover:bg-neutral-700"
            >
              + Resim Ekle
            </button>
            {items.length > 0 && (
              <button onClick={() => setItems([])} className="ml-2 rounded-lg px-3 py-2 text-sm text-neutral-400 hover:text-red-300">
                Tümünü temizle
              </button>
            )}
            <p className="mt-2 text-xs text-neutral-500">
              veya sürükle bırak · her resim bir sahne · <span className="text-neutral-400">⠿ tutup sürükleyerek sıralayabilirsin</span>
            </p>
          </div>

          {items.length === 0 && (
            <div className="py-16 text-center text-sm text-neutral-600">Henüz resim yok. Yukarıdan ekle.</div>
          )}

          <div className="space-y-3">
            {items.map((it, i) => (
              <div
                key={it.id}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => dropAt(i)}
                className={`flex gap-3 rounded-xl border bg-neutral-900 p-3 transition ${
                  dragIndex === i ? "border-amber-500 opacity-50" : "border-neutral-800"
                }`}
              >
                <span
                  draggable
                  onDragStart={() => setDragIndex(i)}
                  onDragEnd={() => setDragIndex(null)}
                  title="Sürükle"
                  className="flex cursor-grab select-none items-center text-lg text-neutral-600 hover:text-neutral-300 active:cursor-grabbing"
                >
                  ⠿
                </span>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={it.preview} alt="" className="h-28 w-20 shrink-0 rounded-lg bg-neutral-800 object-cover" />
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2 text-xs text-neutral-400">
                    <span className="rounded bg-neutral-800 px-1.5 py-0.5">Sahne {i + 1}</span>
                    <button onClick={() => move(i, -1)} disabled={i === 0} className="hover:text-white disabled:opacity-30">↑</button>
                    <button onClick={() => move(i, 1)} disabled={i === items.length - 1} className="hover:text-white disabled:opacity-30">↓</button>
                    <button onClick={() => remove(it.id)} className="ml-auto text-red-400 hover:text-red-300">Sil</button>
                  </div>
                  <textarea
                    value={it.caption}
                    onChange={(e) => update(it.id, { caption: e.target.value })}
                    placeholder="Altyazı (boş bırakılabilir) — Enter ile alt satır"
                    rows={2}
                    className="w-full resize-none rounded-lg bg-neutral-800 px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-amber-500"
                  />
                  <div className="flex items-center gap-3 text-xs">
                    <label className="flex items-center gap-1 text-neutral-400">
                      Süre
                      <input
                        type="number"
                        min={1}
                        max={10}
                        step={0.5}
                        value={it.duration}
                        onChange={(e) => update(it.id, { duration: Number(e.target.value) })}
                        className="w-16 rounded bg-neutral-800 px-2 py-1 text-center"
                      />
                      sn
                    </label>
                    <label className="flex items-center gap-1 text-neutral-400">
                      Zoom
                      <select
                        value={it.zoom}
                        onChange={(e) => update(it.id, { zoom: e.target.value as "in" | "out" })}
                        className="rounded bg-neutral-800 px-2 py-1"
                      >
                        <option value="in">İçeri</option>
                        <option value="out">Dışarı</option>
                      </select>
                    </label>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <aside className="space-y-4">
          <div className="space-y-3 rounded-xl border border-neutral-800 bg-neutral-900 p-4">
            <h2 className="text-sm font-semibold">Ayarlar</h2>

            <label className="block text-xs text-neutral-400">
              🎵 Müzik
              <select
                value={music}
                onChange={(e) => setMusic(e.target.value)}
                className="mt-1 w-full rounded-lg bg-neutral-800 px-3 py-2 text-sm text-neutral-100"
              >
                {TRACKS.map((t) => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </label>

            <label className="block text-xs text-neutral-400">
              🔤 Altyazı fontu
              <select
                value={font}
                onChange={(e) => setFont(e.target.value)}
                className="mt-1 w-full rounded-lg bg-neutral-800 px-3 py-2 text-sm text-neutral-100"
              >
                {FONTS.map((f) => (
                  <option key={f.id} value={f.id}>{f.name}</option>
                ))}
              </select>
            </label>

            <label className="block text-xs text-neutral-400">
              Altyazı boyutu: {Math.round(fontScale * 100)}%
              <input
                type="range"
                min={0.7}
                max={1.6}
                step={0.1}
                value={fontScale}
                onChange={(e) => setFontScale(Number(e.target.value))}
                className="mt-1 w-full accent-amber-500"
              />
            </label>

            <div className="grid grid-cols-2 gap-2">
              <label className="block text-xs text-neutral-400">
                Altyazı rengi
                <input
                  type="color"
                  value={captionColor}
                  onChange={(e) => setCaptionColor(e.target.value)}
                  className="mt-1 h-9 w-full cursor-pointer rounded-lg border-0 bg-neutral-800"
                />
              </label>
              <label className="block text-xs text-neutral-400">
                Konum
                <select
                  value={captionPos}
                  onChange={(e) => setCaptionPos(e.target.value)}
                  className="mt-1 w-full rounded-lg bg-neutral-800 px-3 py-2 text-sm text-neutral-100"
                >
                  <option value="bottom">Alt</option>
                  <option value="center">Orta</option>
                  <option value="top">Üst</option>
                </select>
              </label>
            </div>

            <label className="block text-xs text-neutral-400">
              Format
              <select
                value={aspect.key}
                onChange={(e) => setAspect(ASPECTS.find((a) => a.key === e.target.value)!)}
                className="mt-1 w-full rounded-lg bg-neutral-800 px-3 py-2 text-sm text-neutral-100"
              >
                {ASPECTS.map((a) => (
                  <option key={a.key} value={a.key}>{a.label}</option>
                ))}
              </select>
            </label>

            <label className="block text-xs text-neutral-400">
              Sahne süresi (tümü): {defaultDur.toFixed(1)} sn
              <input
                type="range"
                min={1.5}
                max={8}
                step={0.5}
                value={defaultDur}
                onChange={(e) => applyDurationToAll(Number(e.target.value))}
                className="mt-1 w-full accent-amber-500"
              />
            </label>

            <label className="block text-xs text-neutral-400">
              Geçiş süresi: {xfade.toFixed(1)} sn
              <input
                type="range"
                min={0.4}
                max={2}
                step={0.1}
                value={xfade}
                onChange={(e) => setXfade(Number(e.target.value))}
                className="mt-1 w-full accent-amber-500"
              />
            </label>

            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={grade} onChange={(e) => setGrade(e.target.checked)} className="accent-amber-500" />
              Sinematik renk
            </label>

            <div className="border-t border-neutral-800 pt-2 text-xs text-neutral-500">
              {items.length} sahne · ≈ {Math.max(0, totalDur).toFixed(1)} sn
            </div>
          </div>

          {error && (
            <pre className="whitespace-pre-wrap rounded-xl border border-red-900 bg-red-950/50 p-3 text-xs text-red-300">{error}</pre>
          )}

          {busy && (
            <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-4 text-sm text-neutral-300">
              <div className="animate-pulse">⏳ Video üretiliyor… (sahne başına ~15-25 sn sürebilir)</div>
            </div>
          )}

          {resultUrl && (
            <div className="space-y-3 rounded-xl border border-neutral-800 bg-neutral-900 p-4">
              <h2 className="text-sm font-semibold">✅ Hazır</h2>
              <video src={resultUrl} controls className="w-full rounded-lg bg-black" />
              <a
                href={resultUrl}
                download="reels.mp4"
                className="block rounded-lg bg-amber-500 px-4 py-2 text-center font-semibold text-black hover:bg-amber-400"
              >
                ⬇ İndir
              </a>
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}
