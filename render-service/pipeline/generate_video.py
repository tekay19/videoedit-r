#!/usr/bin/env python3
"""Manifest JSON -> sinematik slideshow (Ken Burns + crossfade + altyazi + secilebilir muzik/font).
Kullanim: python3 generate_video.py manifest.json

manifest.music: false | true | "<track id>"   (MUSIC sozlugundeki id)
manifest.font:  "sans" | "serif" | "modern" | "noto"  (FONTS sozlugundeki id)
"""
import json, sys, os, subprocess, math, wave, re
from array import array
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# =================== MUZIK PRESETLERI (10 parca) ===================
MUSIC = {
    "zafer":     {"name": "Zafer",     "prog": [("C4","maj"),("G3","maj"),("A3","min"),("F3","maj")], "beat": 0.50, "kick": True,  "arp": True,  "lead": True},
    "duygusal":  {"name": "Duygusal",  "prog": [("A3","min"),("F3","maj"),("C4","maj"),("G3","maj")], "beat": 0.60, "kick": False, "arp": True,  "lead": True},
    "sinematik": {"name": "Sinematik", "prog": [("D4","min"),("Bb3","maj"),("F3","maj"),("C4","maj")], "beat": 0.55, "kick": True,  "arp": False, "lead": True},
    "epik":      {"name": "Epik",      "prog": [("E3","min"),("C4","maj"),("G3","maj"),("D4","maj")], "beat": 0.50, "kick": True,  "arp": True,  "lead": True},
    "cosku":     {"name": "Coşku",     "prog": [("C4","maj"),("A3","min"),("F3","maj"),("G3","maj")], "beat": 0.45, "kick": True,  "arp": True,  "lead": False},
    "umut":      {"name": "Umut",      "prog": [("F3","maj"),("C4","maj"),("G3","maj"),("A3","min")], "beat": 0.55, "kick": False, "arp": True,  "lead": True},
    "dramatik":  {"name": "Dramatik",  "prog": [("A3","min"),("G3","maj"),("F3","maj"),("E4","maj")], "beat": 0.55, "kick": True,  "arp": False, "lead": True},
    "mars":      {"name": "Marş",      "prog": [("G3","maj"),("D4","maj"),("E3","min"),("C4","maj")], "beat": 0.50, "kick": True,  "arp": True,  "lead": True},
    "huzun":     {"name": "Hüzün",     "prog": [("C4","min"),("Ab3","maj"),("Eb4","maj"),("Bb3","maj")], "beat": 0.65, "kick": False, "arp": True,  "lead": True},
    "enerji":    {"name": "Enerji",    "prog": [("D4","maj"),("A3","maj"),("B3","min"),("G3","maj")], "beat": 0.42, "kick": True,  "arp": True,  "lead": False},
}

_PC = {"C":0,"C#":1,"DB":1,"D":2,"D#":3,"EB":3,"E":4,"F":5,"F#":6,"GB":6,
       "G":7,"G#":8,"AB":8,"A":9,"A#":10,"BB":10,"B":11}
def _freq(n):
    m = re.match(r"^([A-Ga-g][#b]?)(-?\d+)$", n.strip())
    pc = _PC[m.group(1).upper()]
    midi = (int(m.group(2)) + 1) * 12 + pc
    return 440.0 * (2 ** ((midi - 69) / 12.0))
def _chord(root, qual):
    r = _freq(root)
    third = r * (2 ** ((3 if qual == "min" else 4) / 12.0))
    fifth = r * (2 ** (7 / 12.0))
    return r / 2.0, [r, third, fifth], [r, third, fifth, r * 2.0]

def make_music(path, dur, preset_id):
    P = MUSIC.get(preset_id, MUSIC["zafer"])
    prog = P["prog"]; beat = P["beat"]; KICK, ARP, LEAD = P["kick"], P["arp"], P["lead"]
    SR = 44100; TP = 2 * math.pi; CL = 8 * beat; XFq = min(0.8, CL * 0.2)
    N = int(SR * (dur + 1)); nC = len(prog)
    CT = [_chord(r, q) for (r, q) in prog]; APAT = [0, 1, 2, 3, 2, 1, 2, 3]
    def ci(t): return int(t / CL) % nC
    buf = [0.0] * N
    def pad(idx, t):
        s = 0.0
        for f in CT[idx][1]:
            ph = TP * f * t; s += math.sin(ph) + 0.18 * math.sin(2 * ph)
        return s * 0.20
    for i in range(N):
        t = i / SR; idx = ci(t); bt = t - int(t / CL) * CL; cur = pad(idx, t)
        if bt < XFq:
            w = 0.5 - 0.5 * math.cos(math.pi * bt / XFq)
            buf[i] += pad((idx - 1) % nC, t) * (1 - w) + cur * w
        else:
            buf[i] += cur
    for k in range(int((dur + 1) / beat)):
        tb = k * beat; f = CT[ci(tb)][0]; i0 = int(tb * SR)
        for j in range(int(min(0.48, beat * 0.95) * SR)):
            ix = i0 + j
            if ix >= N: break
            lt = j / SR; e = math.exp(-3 * lt) * (1 - math.exp(-300 * lt))
            buf[ix] += 0.40 * e * (math.sin(TP * f * lt) + 0.3 * math.sin(2 * TP * f * lt))
    if KICK:
        for k in range(int((dur + 1) / beat)):
            i0 = int(k * beat * SR)
            for j in range(int(0.16 * SR)):
                ix = i0 + j
                if ix >= N: break
                lt = j / SR; pit = 55 + 70 * math.exp(-50 * lt)
                buf[ix] += 0.38 * math.exp(-24 * lt) * math.sin(TP * pit * lt)
    if ARP:
        b8 = beat / 2
        for k in range(int((dur + 1) / b8)):
            ts = k * b8; arp = CT[ci(ts)][2]; f = arp[APAT[k % 8]] * 2.0; i0 = int(ts * SR)
            for j in range(int(0.32 * SR)):
                ix = i0 + j
                if ix >= N: break
                lt = j / SR; e = math.exp(-6 * lt) * (1 - math.exp(-400 * lt))
                buf[ix] += 0.12 * e * math.sin(TP * f * lt)
    if LEAD:
        for i in range(N):
            t = i / SR; idx = ci(t); gate = max(0.0, min(1.0, (t - 3.0) / 3.0))
            if gate <= 0: continue
            lf = CT[idx][1][2] * 2.0 * (1 + 0.006 * math.sin(TP * 5 * t))
            buf[i] += 0.08 * gate * math.sin(TP * lf * t)
    pk = max(abs(x) for x in buf) or 1.0; g = 0.85 / pk
    for i in range(N):
        t = i / SR; dyn = 0.6 + 0.4 * max(0.0, min(1.0, t / 3.0))
        buf[i] = math.tanh(buf[i] * g * dyn * 1.1) * 0.92
    HA = 12; inter = array("h", bytes(4 * N))
    for i in range(N):
        l = buf[i]; r = buf[i - HA] if i >= HA else 0.0
        inter[2 * i] = int(max(-1, min(1, l)) * 32200)
        inter[2 * i + 1] = int(max(-1, min(1, r * 0.96)) * 32200)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(inter.tobytes())

# =================== ALTYAZI FONTLARI ===================
FONTS = {
    "sans":   ["/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
               "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "serif":  ["/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
               "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
    "modern": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               "/System/Library/Fonts/Supplemental/Futura.ttc",
               "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"],
    "noto":   ["/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
               "/System/Library/Fonts/Supplemental/Verdana Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
}
def font(sz, family="sans"):
    for p in FONTS.get(family, FONTS["sans"]):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except Exception: pass
    return ImageFont.load_default()

# =================== VIDEO PIPELINE ===================
def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write("FFMPEG ERR:\n" + r.stderr[-1800:]); sys.exit(1)

def main():
    m = json.load(open(sys.argv[1]))
    W = int(m.get("width", 1080)); H = int(m.get("height", 1920))
    FPS = int(m.get("fps", 30)); XF = float(m.get("xfade", 1.0))
    WORK = m["workdir"]; os.makedirs(WORK, exist_ok=True)
    IMAGES = m["images"]; OUT = m["output"]
    USE_GRADE = bool(m.get("grade", True))
    FONTFAM = m.get("font", "sans")
    mv = m.get("music", True); USE_MUSIC = bool(mv)
    PRESET = mv if (isinstance(mv, str) and mv in MUSIC) else "zafer"

    GRADE = ("eq=contrast=1.06:saturation=1.10:gamma=0.985:brightness=0.01,"
             "curves=master='0/0.03 0.25/0.22 0.5/0.5 0.75/0.78 1/0.97',"
             "colorbalance=rs=-0.03:bs=0.04:rh=0.05:bh=-0.04,"
             "vignette=PI/4.5,noise=alls=5:allf=t,format=yuv420p") if USE_GRADE else "format=yuv420p"

    clips = []
    for i, im in enumerate(IMAGES):
        dur = float(im.get("duration", 3.5)); NF = max(2, round(dur * FPS))
        comp = os.path.join(WORK, f"comp_{i}.png")
        run(["ffmpeg","-y","-loglevel","error","-i", im["path"], "-filter_complex",
             f"[0:v]scale={2*W}:{2*H}:force_original_aspect_ratio=increase,crop={2*W}:{2*H},"
             f"boxblur=60:4,eq=brightness=-0.20[bg];"
             f"[0:v]scale={2*W}:{2*H}:force_original_aspect_ratio=decrease:force_divisible_by=2[fg];"
             f"[bg][fg]overlay=(W-w)/2:(H-h)/2[o]", "-map","[o]","-frames:v","1", comp])
        ss = f"(pow(on/{NF}\\,2)*(3-2*(on/{NF})))"
        z = f"1.0+0.12*{ss}" if im.get("zoom","in") == "in" else f"1.12-0.12*{ss}"
        dx = 60 if i % 2 == 0 else -60
        vf = (f"zoompan=z='{z}':d={NF}:x='iw/2-(iw/zoom/2)+{dx}*((on/{NF})-0.5)':"
              f"y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},{GRADE}")
        clip = os.path.join(WORK, f"clip_{i}.mp4")
        run(["ffmpeg","-y","-loglevel","error","-i", comp, "-vf", vf,
             "-frames:v", str(NF), "-r", str(FPS),
             "-c:v","libx264","-profile:v","high","-crf","18","-preset","medium","-an", clip])
        clips.append((clip, dur))

    base = os.path.join(WORK, "base.mp4")
    if len(clips) == 1:
        run(["ffmpeg","-y","-loglevel","error","-i", clips[0][0], "-c","copy", base]); total = clips[0][1]
    else:
        inputs, fc, prev, cum = [], [], "0:v", 0.0
        for c, _ in clips: inputs += ["-i", c]
        for k in range(1, len(clips)):
            cum += clips[k-1][1]; off = cum - k*XF
            fc.append(f"[{prev}][{k}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{k}]"); prev = f"x{k}"
        run(["ffmpeg","-y","-loglevel","error"]+inputs+["-filter_complex",";".join(fc),
             "-map",f"[{prev}]","-c:v","libx264","-profile:v","high","-crf","18",
             "-preset","medium","-pix_fmt","yuv420p","-r",str(FPS), base])
        total = sum(d for _, d in clips) - (len(clips)-1)*XF

    starts, cum = [], 0.0
    for k in range(len(clips)):
        starts.append(cum - k*XF); cum += clips[k][1]
    starts.append(total)

    CW, CH = W, int(H*0.24)
    FT = font(int(W*0.066), FONTFAM); SP, STK = 14, 5
    grad = Image.new("L",(1,CH))
    for y in range(CH): grad.putpixel((0,y), int(165*(y/(CH-1))**1.5))
    scrim = Image.merge("RGBA",(Image.new("L",(CW,CH),0),)*3+(grad.resize((CW,CH)),))
    GOLD = (236,184,78,255)
    cap_inputs, cap_filters, idx = [], [], 1
    for i, im in enumerate(IMAGES):
        txt = (im.get("caption") or "").strip()
        if not txt: continue
        img = scrim.copy(); d = ImageDraw.Draw(img); cy = CH*0.60
        bb = d.multiline_textbbox((CW/2,cy), txt, font=FT, anchor="mm", align="center", spacing=SP, stroke_width=STK)
        d.rounded_rectangle([CW/2-46, bb[1]-24, CW/2+46, bb[1]-18], radius=3, fill=GOLD)
        sh = Image.new("RGBA",(CW,CH),(0,0,0,0))
        ImageDraw.Draw(sh).multiline_text((CW/2+3,cy+4), txt, font=FT, fill=(0,0,0,150), anchor="mm",
            align="center", spacing=SP, stroke_width=STK, stroke_fill=(0,0,0,150))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(6)))
        ImageDraw.Draw(img).multiline_text((CW/2,cy), txt, font=FT, fill=(255,255,255,255), anchor="mm",
            align="center", spacing=SP, stroke_width=STK, stroke_fill=(0,0,0,235))
        p = os.path.join(WORK, f"cap_{i}.png"); img.save(p)
        s, e = starts[i]+0.15, starts[i+1]-0.15
        cap_inputs += ["-loop","1","-t", f"{total+0.1:.3f}", "-i", p]
        cap_filters.append(f"[{idx}:v]format=rgba,fade=t=in:st={s:.3f}:d=0.35:alpha=1,"
                           f"fade=t=out:st={max(s,e-0.35):.3f}:d=0.35:alpha=1[c{idx}]")
        idx += 1

    subbed = os.path.join(WORK, "subbed.mp4")
    if cap_inputs:
        links, bl = [], "0:v"
        for k in range(1, idx):
            last = ":shortest=1" if k == idx-1 else ""
            links.append(f"[{bl}][c{k}]overlay=(W-w)/2:H-h-{int(H*0.06)}{last}[o{k}]"); bl = f"o{k}"
        run(["ffmpeg","-y","-loglevel","error","-i", base]+cap_inputs+
            ["-filter_complex", ";".join(cap_filters+links), "-map", f"[{bl}]", "-an",
             "-c:v","libx264","-profile:v","high","-crf","18","-preset","medium","-pix_fmt","yuv420p", subbed])
    else:
        run(["ffmpeg","-y","-loglevel","error","-i", base, "-c","copy", subbed])

    fout = max(0.1, total - 2.3)
    if USE_MUSIC:
        mus = os.path.join(WORK, "music.wav"); make_music(mus, total, PRESET)
        run(["ffmpeg","-y","-loglevel","error","-i", subbed, "-i", mus, "-filter_complex",
             f"[0:v]fade=t=in:st=0:d=0.5,fade=t=out:st={max(0,total-0.55):.3f}:d=0.55[v];"
             f"[1:a]highpass=f=35,afade=t=in:st=0:d=1.2,afade=t=out:st={fout:.3f}:d=2.0,volume=0.92[a]",
             "-map","[v]","-map","[a]","-c:v","libx264","-profile:v","high","-crf","18","-preset","medium",
             "-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart", OUT])
    else:
        run(["ffmpeg","-y","-loglevel","error","-i", subbed, "-vf",
             f"fade=t=in:st=0:d=0.5,fade=t=out:st={max(0,total-0.55):.3f}:d=0.55",
             "-an","-c:v","libx264","-profile:v","high","-crf","18","-preset","medium",
             "-movflags","+faststart", OUT])

    print(json.dumps({"ok": True, "output": OUT, "duration": round(total,2),
                      "count": len(IMAGES), "music": PRESET if USE_MUSIC else None, "font": FONTFAM}))

if __name__ == "__main__":
    main()
