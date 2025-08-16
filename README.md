# headpat2webm

Tiny CLI to convert head-pat GIFs (and friends) into **512×512 VP9 WebM with alpha**.  
Great for Telegram video stickers (≤512 px, no audio, transparent background).

## One-click use in GitHub Codespaces

1. **Upload this repo to your GitHub account.**
2. Click the green **Code** button → **Create codespace on main**.
3. When the Codespace opens, drop your inputs into the repo (drag files in the Explorer).
4. In the terminal, run for a single file:
   ```bash
   python headpat2webm.py path/to/in.gif --key-green
   ```
   Or batch convert a whole folder:
   ```bash
   python headpat2webm.py assets/ --key-green
   ```
5. Outputs appear in **.out/** as `.webm`.

## Common flags

- `--key-green` : remove #00FF00 green-screen to **true alpha**.
- `--scaler lanczos|neighbor` :
  - `lanczos` (default) → smooth anime/drawn art.
  - `neighbor` → crisp pixel edges (good for pixel-art).
- `--fps 30` : set FPS (or use `--fps keep` to preserve source).
- `--crf 32` : quality (lower = better = larger). Try 28–38.
- `--size 512` : square canvas (keeps aspect, pads transparent).
- `--speed 3` : VP9 encode speed (0 best/slowest … 8 fastest).

**Examples**
```bash
# Smooth upscale + greenscreen removal
python headpat2webm.py in.gif --key-green --scaler lanczos --fps 30 --crf 30

# Pixel-art crisp look
python headpat2webm.py in.gif --key-green --scaler neighbor --crf 34

# Keep original frame rate
python headpat2webm.py in.gif --fps keep
```

## Notes for Telegram
- Sticker videos must be ≤512×512. This tool centers the content and pads with **transparent** pixels.
- Codec: **VP9** with **alpha** (`yuva420p`) is supported.

## Why your 112→512 looked “low-res”
You’re scaling ~4.6×. That can look soft if you use a poor scaler or if chroma-keying leaves fringes.  
This tool:
- applies the right scaler (`lanczos` or `neighbor`),
- does **true** alpha instead of neon-green backgrounds,
- preserves aspect ratio and pads to square.
