
#!/usr/bin/env python3
"""
generate_headpat_plus.py
- Standalone generator for animated headpat WebM with optional squish/unsquish of the character.
- Requires: Pillow, ffmpeg in PATH
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
    """Resize keeping original aspect ratio to exact target_h and proportional width if target_w is None."""
    w, h = img.size
    if target_w is None:
        ratio = target_h / h
        target_w = max(1, int(round(w * ratio)))
    return img.resize((target_w, target_h), Image.BICUBIC)

def lerp(a, b, t): return a + (b - a) * t

def pat_curve_cosine(phase: float) -> float:
    """Returns 0..1: 0 = hand up, 1 = maximal down. Cosine ease for natural patting."""
    return 0.5 * (1 - math.cos(2 * math.pi * phase))

def pat_curve_triangle(phase: float) -> float:
    x = phase % 1.0
    return 1.0 - abs((x * 2.0) - 1.0)  # up -> down -> up, linear

def main():
    p = argparse.ArgumentParser()
    p.add_argument("image", help="Character image (PNG recommended with alpha)")
    p.add_argument("--size", type=int, default=512, help="Output square canvas size")
    p.add_argument("--fps", type=int, default=30, help="Frames per second")
    p.add_argument("--crf", type=int, default=32, help="VP9 quality (lower = better)")
    p.add_argument("--scale", type=float, default=0.9, help="Character base height relative to canvas (0..1)")
    p.add_argument("--hand-dir", type=str, default=os.path.join("assets","hand_frames"), help="Directory of hand PNGs")
    p.add_argument("--squish-mode", choices=["none","cosine","triangle"], default="cosine", help="How to animate squish")
    p.add_argument("--squish-min", type=float, default=0.88, help="Minimum vertical scale at impact (e.g., 0.88)")
    p.add_argument("--widen", type=float, default=0.12, help="Horizontal widening when squished (0..1). Set 0 to disable.")
    p.add_argument("--anchor", choices=["center","top"], default="top", help="Anchor for character during squish")
    p.add_argument("--bg", default="transparent", help="Background: 'transparent' or hex like #00000000/#RRGGBBAA/#RRGGBB")
    p.add_argument("-o", "--output", default="headpat.webm", help="Output webm path")
    args = p.parse_args()

    # Load character
    char = Image.open(args.image).convert("RGBA")
    char = premultiply_alpha(char)

    # Output dirs
    out_path = args.output
    tmpdir = tempfile.mkdtemp(prefix="headpat_frames_")
    try:
        # Prep base canvas background
        if args.bg == "transparent":
            bg_color = (0,0,0,0)
        else:
            hexv = args.bg.lstrip("#")
            if len(hexv) == 6:
                r = int(hexv[0:2], 16); g = int(hexv[2:4], 16); b = int(hexv[4:6], 16); a = 255
            elif len(hexv) == 8:
                r = int(hexv[0:2], 16); g = int(hexv[2:4], 16); b = int(hexv[4:6], 16); a = int(hexv[6:8], 16)
            else:
                raise SystemExit("Invalid bg hex; use #RRGGBB or #RRGGBBAA")
            bg_color = (r,g,b,a)

        # Determine target base size of character
        base_h = int(round(args.size * args.scale))
        base_char = resize_keep_aspect(char, base_h)
        base_w, base_h = base_char.size

        # Placement top-left for base (unsquished) frame
        if args.anchor == "center":
            base_x = (args.size - base_w) // 2
            base_y = (args.size - base_h) // 2
        else:  # top
            base_x = (args.size - base_w) // 2
            base_y = (args.size - base_h) // 2  # keep top consistent
            top_y_fixed = base_y

        # Load hand frames
        hand_frames = list_hand_frames(args.hand_dir)
        N = len(hand_frames)

        # Pick curve
        curve_fn = pat_curve_cosine if args.squish_mode == "cosine" else pat_curve_triangle

        # Render frames
        for i, hand_path in enumerate(hand_frames):
            phase = i / N
            down = curve_fn(phase) if args.squish_mode != "none" else 0.0

            # Vertical squish: 1.0 -> args.squish_min
            sy = 1.0 - (1.0 - args.squish_min) * down
            # Horizontal widening: widen proportionally to squish amount
            sx = 1.0 + (args.widen * (1.0 - sy) / max(1e-6, (1.0 - args.squish_min))) if args.widen > 0 else 1.0

            # Scale character for this frame
            fh = max(1, int(round(base_h * sy)))
            fw = max(1, int(round(base_w * sx)))
            char_frame = base_char.resize((fw, fh), Image.BICUBIC)

            # Compose on canvas
            canvas = Image.new("RGBA", (args.size, args.size), bg_color)
            if args.anchor == "center":
                x = (args.size - fw) // 2
                y = (args.size - fh) // 2
            else:  # top anchored
                x = (args.size - fw) // 2
                # keep top constant: y stays at top_y_fixed
                y = top_y_fixed
            canvas.alpha_composite(char_frame, (x, y))

            # Overlay hand
            hand = Image.open(hand_path).convert("RGBA")
            # If hand frames are not the same size as canvas, center them; otherwise, paste at 0,0
            if hand.size != (args.size, args.size):
                # scale hand to canvas while preserving size
                hand = hand.resize((args.size, args.size), Image.NEAREST)
            canvas.alpha_composite(hand, (0, 0))

            frame_path = os.path.join(tmpdir, f"frame_{i:04d}.png")
            canvas.save(frame_path, "PNG")

        # Encode with ffmpeg
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate", str(args.fps),
            "-i", os.path.join(tmpdir, "frame_%04d.png"),
            "-c:v", "libvpx-vp9",
            "-pix_fmt", "yuva420p",
            "-auto-alt-ref", "0",
            "-b:v", "0",
            "-crf", str(args.crf),
            "-row-mt", "1",
            "-cpu-used", "4",
            out_path,
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        with open(out_path + ".log.txt", "w", encoding="utf-8") as f:
            f.write(proc.stdout)

        if proc.returncode != 0 or not os.path.exists(out_path):
            raise SystemExit("ffmpeg failed; see log: " + out_path + ".log.txt")

        print("Wrote", out_path)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
