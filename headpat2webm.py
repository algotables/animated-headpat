#!/usr/bin/env python3
import argparse, shutil, subprocess, sys, os
from pathlib import Path

VALID_EXTS = {".gif", ".webp", ".apng", ".png", ".jpg", ".jpeg", ".mp4", ".mov", ".mkv"}

def which_ffmpeg():
    return shutil.which("ffmpeg")

def build_filter(key_green: bool, fps: str | None, size: int, scaler: str):
    parts = []
    if fps and str(fps).lower() != "keep":
        parts.append(f"fps={fps}")
    if key_green:
        parts.append("chromakey=0x00FF00:0.20:0.0")
    parts.append(f"scale={size}:-1:flags={scaler}:force_original_aspect_ratio=decrease")
    parts.append(f"pad={size}:{size}:(ow-iw)/2:(oh-ih)/2:color=black@0")
    parts.append("format=yuva420p")
    return ",".join(parts)

def out_name(in_path: Path, out_dir: Path) -> Path:
    return out_dir / (in_path.stem + ".webm")

def convert_one(inp: Path, out: Path, vf: str, crf: int, speed: int):
    cmd = [
        "ffmpeg", "-y", "-i", str(inp),
        "-vf", vf,
        "-c:v", "libvpx-vp9",
        "-pix_fmt", "yuva420p",
        "-b:v", "0",
        "-crf", str(crf),
        "-row-mt", "1",
        "-speed", str(speed),
        "-an",
        str(out)
    ]
    print(" ".join(cmd))
    subprocess.check_call(cmd)

def collect_inputs(path: Path):
    if path.is_dir():
        for p in sorted(path.rglob("*")):
            if p.suffix.lower() in VALID_EXTS and p.is_file():
                yield p
    else:
        yield path

def main():
    p = argparse.ArgumentParser(description="Convert GIF/vid → 512x512 VP9 WebM with alpha (great for Telegram video stickers)")
    p.add_argument("input", help="Input file OR directory")
    p.add_argument("-o", "--outdir", default=".out", help="Output directory (default: .out)")
    p.add_argument("--size", type=int, default=512, help="Square canvas size (default: 512)")
    p.add_argument("--fps", default="30", help="Target FPS (number) or 'keep' (default: 30)")
    p.add_argument("--crf", type=int, default=32, help="VP9 quality (lower=better/bigger). Typical 28-38 (default: 32)")
    p.add_argument("--speed", type=int, default=3, help="VP9 speed 0(slowest/best)-8(fastest/worst), default 3")
    p.add_argument("--scaler", choices=["lanczos", "neighbor"], default="lanczos", help="lanczos=smooth anime; neighbor=crisp pixel look")
    p.add_argument("--key-green", action="store_true", help="Chroma-key #00FF00 to transparent")
    args = p.parse_args()

    if not which_ffmpeg():
        sys.exit("ffmpeg not found. In Codespaces this should be preinstalled by the devcontainer.")

    in_path = Path(args.input)
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    vf = build_filter(args.key_green, args.fps, args.size, args.scaler)

    any_done = False
    for src in collect_inputs(in_path):
        dst = out_name(src, out_dir)
        try:
            convert_one(src, dst, vf=vf, crf=args.crf, speed=args.speed)
            any_done = True
        except subprocess.CalledProcessError as e:
            print(f"[WARN] Failed on {src}: {e}", file=sys.stderr)

    if not any_done:
        print("No valid inputs found.", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"Done. Files in: {out_dir.resolve()}")

if __name__ == "__main__":
    main()
