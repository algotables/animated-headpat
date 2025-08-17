#!/usr/bin/env python3
"""
generate_headpat.py
Squish-enabled headpat generator (WebM VP9 with alpha).

Usage:
  python generate_headpat.py char.png --size 512 --fps 30 --crf 32 --scale 0.9 \
    --hand-dir assets/hand_frames --squish-mode cosine --squish-min 0.88 \
    --widen 0.12 --anchor top -o outputs/headpat.webm
"""
import argparse, os, sys, tempfile, subprocess, math, re, glob, shutil
from PIL import Image

def natural_key(s): 
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

def list_hand_frames(hand_dir):
    exts = ('.png', '.webp')
    files = [f for f in glob.glob(os.path.join(hand_dir, '*')) if os.path.splitext(f)[1].lower() in exts]
    files.sort(key=natural_key)
    if not files:
        raise FileNotFoundError(f"No hand frames found in {hand_dir}")
    return files

def premultiply_alpha(img: Image.Image) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    r, g, b, a = img.split()
    r = Image.composite(r, Image.new("L", img.size, 0), a)
    g = Image.composite(g, Image.new("L", img.size, 0), a)
    b = Image.composite(b, Image.new("L", img.size, 0), a)
    return Image.merge("RGBA", (r, g, b, a))

def resize_keep_aspect(img: Image.Image, target_h: int, target_w: int = None) -> Image.Image:
    w, h = img.size
    if target_w is None:
        ratio = target_h / h
        target_w = max(1, int(round(w * ratio)))
    return img.resize((target_w, target_h), Image.BICUBIC)

def pat_curve_cosine(phase: float) -> float:
    # 0..1 smooth down-up
    return 0.5 * (1 - math.cos(2 * math.pi * phase))

def pat_curve_triangle(phase: float) -> float:
    x = phase % 1.0
    return 1.0 - abs((x * 2.0) - 1.0)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("image", help="Character image (PNG with alpha recommended)")
    p.add_argument("--size", type=int, default=512, help="Output canvas (square) size")
    p.add_argument("--fps", type=int, default=30, help="Frames per second")
    p.add_argument("--crf", type=int, default=32, help="VP9 quality (lower = better)")
    p.add_argument("--scale", type=float, default=0.9, help="Character base height / canvas (0..1)")
    p.add_argument("--hand-dir", type=str, default=os.path.join('assets','hand_frames'), help="Directory with hand frames (PNG/WebP)")
    p.add_argument("--squish-mode", choices=["none","cosine","triangle"], default="cosine", help="Animate squish shape")
    p.add_argument("--squish-min", type=float, default=0.88, help="Minimum vertical scale at impact")
    p.add_argument("--widen", type=float, default=0.12, help="Horizontal widen amount at impact (0..1)")
    p.add_argument("--anchor", choices=["center","top"], default="top", help="Anchor point during squish")
    p.add_argument("--offset-x", type=int, default=0, help="Nudge character horizontally (px)")
    p.add_argument("--offset-y", type=int, default=0, help="Nudge character vertically (px)")
    p.add_argument("-o","--output", default="outputs/headpat.webm", help="Output webm path")
    args = p.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    char = Image.open(args.image).convert("RGBA")
    char = premultiply_alpha(char)

    base_h = int(round(args.size * args.scale))
    base_char = resize_keep_aspect(char, base_h)
    base_w, base_h = base_char.size

    if args.anchor == "center":
        base_x = (args.size - base_w) // 2 + args.offset_x
        base_y = (args.size - base_h) // 2 + args.offset_y
    else:
        base_x = (args.size - base_w) // 2 + args.offset_x
        base_y = (args.size - base_h) // 2 + args.offset_y
        top_y_fixed = base_y

    hand_frames = list_hand_frames(args.hand_dir)
    N = len(hand_frames)

    curve_fn = pat_curve_cosine if args.squish_mode == "cosine" else (pat_curve_triangle if args.squish_mode == "triangle" else (lambda p: 0.0))

    tmpdir = tempfile.mkdtemp(prefix="headpat_frames_")
    try:
        for i, hand_path in enumerate(hand_frames):
            phase = i / N
            down = curve_fn(phase)
            sy = 1.0 - (1.0 - args.squish_min) * down
            sx = 1.0 + (args.widen * (1.0 - sy) / max(1e-6, (1.0 - args.squish_min))) if args.widen > 0 else 1.0

            fh = max(1, int(round(base_h * sy)))
            fw = max(1, int(round(base_w * sx)))
            char_frame = base_char.resize((fw, fh), Image.BICUBIC)

            canvas = Image.new("RGBA", (args.size, args.size), (0,0,0,0))
            if args.anchor == "center":
                x = (args.size - fw) // 2 + args.offset_x
                y = (args.size - fh) // 2 + args.offset_y
            else:
                x = (args.size - fw) // 2 + args.offset_x
                y = top_y_fixed + (0 if fh <= base_h else 0)  # keep top pinned
            canvas.alpha_composite(char_frame, (x, y))

            hand = Image.open(hand_path).convert("RGBA")
            if hand.size != (args.size, args.size):
                hand = hand.resize((args.size, args.size), Image.NEAREST)
            canvas.alpha_composite(hand, (0,0))

            frame_path = os.path.join(tmpdir, f"frame_{i:04d}.png")
            canvas.save(frame_path, "PNG")

        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(args.fps),
            "-i", os.path.join(tmpdir, "frame_%04d.png"),
            "-c:v", "libvpx-vp9",
            "-pix_fmt", "yuva420p",
            "-auto-alt-ref", "0",
            "-b:v", "0",
            "-crf", str(args.crf),
            "-row-mt", "1", "-cpu-used", "4",
            args.output,
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        with open(args.output + ".log.txt", "w", encoding="utf-8") as f:
            f.write(proc.stdout)
        if proc.returncode != 0 or not os.path.exists(args.output):
            raise SystemExit("ffmpeg failed; check log: " + args.output + ".log.txt")
        print("Wrote", args.output)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
