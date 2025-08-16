#!/usr/bin/env python3
"""
Generate a head‑pat animation from a static image.

This script composites a series of floating hand overlay frames on top of a user
provided image to create a short looping animation. It then encodes the
resulting frames into a VP9 WebM with an alpha channel suitable for use as
video stickers (e.g. on Telegram). The hand overlay frames are stored as
PNG files under ``assets/hand_frames``. If you wish to swap out the hand
animation you can replace those PNGs with your own sequence.

Example usage::

    python generate_headpat.py cute.png

This will produce ``cute_headpat.webm`` in the current directory. Additional
arguments allow you to customise the scale of your image, the output size,
frame rate and quality.

Requires ``ffmpeg`` to be available on the PATH and Pillow installed.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image


def load_hand_frames(hand_dir: Path) -> list[Image.Image]:
    """Load overlay frames from a directory.

    Parameters
    ----------
    hand_dir : Path
        The directory containing numbered PNG files representing the hand
        animation. Frames are loaded in alphanumeric order.

    Returns
    -------
    list[Image.Image]
        A list of RGBA images.
    """
    frames: list[Image.Image] = []
    for fname in sorted(hand_dir.iterdir()):
        if fname.suffix.lower() == ".png":
            frame = Image.open(fname).convert("RGBA")
            frames.append(frame)
    if not frames:
        raise FileNotFoundError(f"No PNG overlay frames found in {hand_dir}")
    return frames


def create_headpat_frames(hand_frames: list[Image.Image], char_img: Image.Image, scale: float) -> list[Image.Image]:
    """Composite the character image with each hand overlay frame.

    The character is resized based on the ``scale`` factor relative to the
    overlay frame width. It is centred horizontally and aligned to the bottom
    of the canvas. Each hand frame is then pasted over the top.

    Parameters
    ----------
    hand_frames : list[Image.Image]
        A list of hand overlay frames.
    char_img : Image.Image
        The base image to pat.
    scale : float
        Character width as a fraction of the canvas width (0 < scale ≤ 1).

    Returns
    -------
    list[Image.Image]
        A list of composited frames.
    """
    if not (0 < scale <= 1):
        raise ValueError("scale must be between 0 and 1")
    base_w, base_h = hand_frames[0].size
    # Resize character to maintain aspect ratio and fit within the canvas
    char = char_img.convert("RGBA")
    target_w = int(base_w * scale)
    ratio = target_w / char.width
    target_h = int(char.height * ratio)
    char_resized = char.resize((target_w, target_h), Image.LANCZOS)
    frames: list[Image.Image] = []
    for hand in hand_frames:
        # Create a transparent canvas for compositing
        canvas = Image.new("RGBA", (base_w, base_h), (0, 0, 0, 0))
        # Position the character at the bottom centre
        x_offset = (base_w - target_w) // 2
        y_offset = base_h - target_h
        canvas.paste(char_resized, (x_offset, y_offset), char_resized)
        # Paste the hand overlay on top
        canvas.paste(hand, (0, 0), hand)
        frames.append(canvas)
    return frames


def save_frames_as_webm(frames: list[Image.Image], fps: int, size: int, crf: int, out_path: Path) -> None:
    """Encode a sequence of frames into a VP9 WebM using ffmpeg.

    Frames are written to a temporary directory as PNGs, then ffmpeg is
    invoked to produce a square video with transparent padding. The
    ``yuva420p`` pixel format retains the alpha channel.

    Parameters
    ----------
    frames : list[Image.Image]
        The composited frames to encode.
    fps : int
        Frames per second for the output.
    size : int
        The width and height of the final square canvas (e.g. 512).
    crf : int
        Quality factor for VP9 encoding (lower = better quality).
    out_path : Path
        Path where the resulting .webm will be written.
    """
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise RuntimeError("ffmpeg not found on PATH. Please install ffmpeg.")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write frames as numbered PNGs
        for idx, frame in enumerate(frames):
            frame_path = os.path.join(tmpdir, f"{idx:03d}.png")
            frame.save(frame_path)
        # Build ffmpeg command
        input_pattern = os.path.join(tmpdir, "%03d.png")
        vf_filters = [
            f"scale={size}:-1:flags=lanczos:force_original_aspect_ratio=decrease",
            f"pad={size}:{size}:(ow-iw)/2:(oh-ih)/2:color=black@0",
            "format=yuva420p"
        ]
        vf = ",".join(vf_filters)
        cmd = [
            ffmpeg_path,
            "-y",
            "-framerate", str(fps),
            "-i", input_pattern,
            "-vf", vf,
            "-c:v", "libvpx-vp9",
            "-pix_fmt", "yuva420p",
            "-b:v", "0",
            "-crf", str(crf),
            "-row-mt", "1",
            str(out_path)
        ]
        subprocess.check_call(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a head‑pat animation from a static image.")
    parser.add_argument("input", help="Path to the character image (PNG/JPG/etc.)")
    parser.add_argument("--output", "-o", help="Path to the output .webm (default: input name with _headpat.webm)")
    parser.add_argument("--hand-dir", default=None, help="Directory containing hand overlay frames (default: bundled assets)")
    parser.add_argument("--scale", type=float, default=0.9, help="Fraction of canvas width for the character (default: 0.9)")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second (default: 30)")
    parser.add_argument("--size", type=int, default=512, help="Output square canvas size (default: 512)")
    parser.add_argument("--crf", type=int, default=32, help="VP9 quality factor (lower = higher quality, default: 32)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_file():
        sys.exit(f"Input file not found: {input_path}")
    # Determine output path
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = input_path.with_name(input_path.stem + "_headpat.webm")
    # Resolve hand frame directory
    if args.hand_dir:
        hand_dir = Path(args.hand_dir)
    else:
        # Default to the bundled assets directory
        hand_dir = Path(__file__).parent / "assets" / "hand_frames"
    # Load overlays and character
    hand_frames = load_hand_frames(hand_dir)
    char_img = Image.open(input_path)
    frames = create_headpat_frames(hand_frames, char_img, args.scale)
    save_frames_as_webm(frames, args.fps, args.size, args.crf, out_path)
    print(f"Done → {out_path}")


if __name__ == "__main__":
    main()