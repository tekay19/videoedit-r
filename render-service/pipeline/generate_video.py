#!/usr/bin/env python3
"""Manifest JSON -> sinematik slideshow video (Ken Burns + crossfade + altyazi + muzik).
Kullanim: python3 generate_video.py manifest.json

manifest:
{
  "images":[{"path":"a.jpg","caption":"Satir1\\nSatir2","duration":3.5,"zoom":"in"}],
  "output":"/abs/out.mp4", "workdir":"/abs/work",
  "width":1080,"height":1920,"fps":30,"xfade":1.0,
  "music":true,"grade":true
}
"""
import json, sys, os, subprocess, math, wave, glob
from array import array
from PIL import Image, ImageDraw, ImageFont, ImageFilter

m = json.load(open(sys.argv[1]))
W = int(m.get("width", 1080)); H = int(m.get("height", 1920))
FPS = int(m.get("fps", 30)); XF = float(m.get("xfade", 1.0))
WORK = m["workdir"]; os.makedirs(WORK, exist_ok=True)
IMAGES = m["images"]; OUT = m["output"]
USE_MUSIC = bool(m.get("music", True)); USE_GRADE = bool(m.get("grade", True))

GRADE = ("eq=contrast=1.06:saturation=1.10:gamma=0.985:brightness=0.01,"
         "curves=master='0/0.03 0.25/0.22 0.5/0.5 0.75/0.78 1/0.97',"
         "colorbalance=rs=-0.03:bs=0.04:rh=0.05:bh=-0.04,"
         "vignette=PI/4.5,noise=alls=5:allf=t,format=yuv420p") if USE_GRADE else "format=yuv420p"

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write("FFMPEG ERR:\n" + r.stderr[-1800:]); sys.exit(1)

def font(sz):
    for p in ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/Library/Fonts/Arial Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

# ---------- 1) Ken Burns klipleri ----------
clips = []
for i, im in enumerate(IMAGES):
    dur = float(im.get("duration", 3.5)); NF = max(2, round(dur*FPS))
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

# ---------- 2) xfade zinciri ----------
base = os.path.join(WORK, "base.mp4")
if len(clips) == 1:
    run(["ffmpeg","-y","-loglevel","error","-i", clips[0][0], "-c","copy", base])
    total = clips[0][1]
else:
    inputs, fc, prev, cum = [], [], "0:v", 0.0
    for k,(c,_) in enumerate(clips):
        inputs += ["-i", c]
    for k in range(1, len(clips)):
        cum += clips[k-1][1]
        off = cum - k*XF
        fc.append(f"[{prev}][{k}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{k}]")
        prev = f"x{k}"
    run(["ffmpeg","-y","-loglevel","error"]+inputs+["-filter_complex",";".join(fc),
         "-map",f"[{prev}]","-c:v","libx264","-profile:v","high","-crf","18",
         "-preset","medium","-pix_fmt","yuv420p","-r",str(FPS), base])
    total = sum(d for _,d in clips) - (len(clips)-1)*XF

# pencereler: klip i [start_i, start_{i+1})
starts, cum = [], 0.0
for k in range(len(clips)):
    starts.append(cum - k*XF)
    cum += clips[k][1]
starts.append(total)

# ---------- 3) altyazilar (Pillow PNG + overlay) ----------
CW, CH = W, int(H*0.24)
FT = font(int(W*0.066)); SP, STK = 14, 5
grad = Image.new("L",(1,CH))
for y in range(CH): grad.putpixel((0,y), int(165*(y/(CH-1))**1.5))
scrim = Image.merge("RGBA",(Image.new("L",(CW,CH),0),)*3+(grad.resize((CW,CH)),))
GOLD=(236,184,78,255)

cap_inputs, cap_filters, idx = [], [], 1
vlabel = "0:v"
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
        links.append(f"[{bl}][c{k}]overlay=(W-w)/2:H-h-{int(H*0.06)}{last}[o{k}]")
        bl = f"o{k}"
    graph = ";".join(cap_filters+links)
    run(["ffmpeg","-y","-loglevel","error","-i", base]+cap_inputs+
        ["-filter_complex", graph, "-map", f"[{bl}]", "-an",
         "-c:v","libx264","-profile:v","high","-crf","18","-preset","medium","-pix_fmt","yuv420p", subbed])
else:
    run(["ffmpeg","-y","-loglevel","error","-i", base, "-c","copy", subbed])

# ---------- 4) muzik (enerjik, kesintisiz) ----------
def make_music(path, dur):
    SR=44100; BEAT=0.5; CL=4.0; XFq=0.8; TP=2*math.pi; N=int(SR*(dur+1))
    PAD=[[261.63,329.63,392,523.25],[196,246.94,293.66,392],[220,261.63,329.63,440],[174.61,220,261.63,349.23]]
    BASS=[130.81,98,110,87.31]; APAT=[0,1,2,3,2,1,2,3]
    def ch(t): return int(t/CL)%4
    buf=[0.0]*N
    def pad(ci,t):
        s=0.0
        for f in PAD[ci]:
            ph=TP*f*t; s+=math.sin(ph)+0.18*math.sin(2*ph)
        return s*0.20
    for i in range(N):
        t=i/SR; ci=ch(t); bt=t-int(t/CL)*CL; cur=pad(ci,t)
        if bt<XFq:
            w=0.5-0.5*math.cos(math.pi*bt/XFq); buf[i]+=pad((ci-1)%4,t)*(1-w)+cur*w
        else: buf[i]+=cur
    for k in range(int((dur+1)/BEAT)):
        tb=k*BEAT; f=BASS[ch(tb)]; i0=int(tb*SR)
        for j in range(int(0.48*SR)):
            ix=i0+j
            if ix>=N: break
            lt=j/SR; e=math.exp(-3*lt)*(1-math.exp(-300*lt))
            buf[ix]+=0.40*e*(math.sin(TP*f*lt)+0.3*math.sin(2*TP*f*lt))
        for j in range(int(0.16*SR)):
            ix=i0+j
            if ix>=N: break
            lt=j/SR; pit=55+70*math.exp(-50*lt)
            buf[ix]+=0.38*math.exp(-24*lt)*math.sin(TP*pit*lt)
    b8=BEAT/2
    for k in range(int((dur+1)/b8)):
        ts=k*b8; ci=ch(ts); f=PAD[ci][APAT[k%8]]*2.0; i0=int(ts*SR)
        for j in range(int(0.32*SR)):
            ix=i0+j
            if ix>=N: break
            lt=j/SR; e=math.exp(-6*lt)*(1-math.exp(-400*lt))
            buf[ix]+=0.13*e*math.sin(TP*f*lt)
    pk=max(abs(x) for x in buf) or 1.0; g=0.85/pk
    for i in range(N): buf[i]=math.tanh(buf[i]*g*1.1)*0.92
    HA=12; inter=array('h', bytes(4*N))
    for i in range(N):
        l=buf[i]; r=buf[i-HA] if i>=HA else 0.0
        inter[2*i]=int(max(-1,min(1,l))*32200); inter[2*i+1]=int(max(-1,min(1,r*0.96))*32200)
    with wave.open(path,"wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(inter.tobytes())

fout = max(0.1, total-2.3)
if USE_MUSIC:
    mus = os.path.join(WORK, "music.wav"); make_music(mus, total)
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

print(json.dumps({"ok": True, "output": OUT, "duration": round(total,2), "count": len(IMAGES)}))
