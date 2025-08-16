# headpat_app

Generate your own **head‑pat animation** from any static picture. This tiny
command–line tool composites a pre‑drawn floating hand over your image, then
encodes the result as a VP9 WebM sticker with transparency – perfect for
Telegram or anywhere that accepts video stickers up to 512×512 pixels.

## Features

- **Simple CLI**: just point it at an image and it will produce a looping
  animation with the head‑pat gesture.
- **Bundled assets**: hand animation frames are included in
  `assets/hand_frames` – no need to find your own.
- **Customisable**: adjust the scale of your character, frame rate, output
  resolution and quality via flags.
- **Clean alpha**: output videos include true transparency (no green screen)
  thanks to VP9’s `yuva420p` pixel format.

## Quick start in Codespaces

1. **Upload this repo** to your GitHub account.
2. Click the **Code** button → **Create codespace on main**.
3. Drop your image into the repository (drag files into the Explorer).
4. Open a terminal and run:

   ```bash
   python generate_headpat.py my_image.png
   ```

   By default this writes `my_image_headpat.webm` in the working directory. You
   can pass `-o` to choose a different filename.

After a few seconds you will find your 512×512 head‑pat animation in WebM
format. The hand will gently pat your character’s head forever!

## Options

```
usage: generate_headpat.py [-h] [--output OUTPUT] [--hand-dir HAND_DIR]
                          [--scale SCALE] [--fps FPS] [--size SIZE]
                          [--crf CRF] input

positional arguments:
  input                 Path to the character image (PNG/JPG/etc.)

options:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Path to the output .webm (default: input name with
                        _headpat.webm)
  --hand-dir HAND_DIR   Directory containing hand overlay frames (default:
                        bundled assets)
  --scale SCALE         Fraction of canvas width for the character (default:
                        0.9)
  --fps FPS             Frames per second (default: 30)
  --size SIZE           Output square canvas size (default: 512)
  --crf CRF             VP9 quality factor (lower = higher quality,
                        default: 32)
```

## Advanced usage

- **Change the character size**: Lower `--scale` to make your image appear
  smaller relative to the hand; increase it (up to 1) to make it fill more
  of the canvas.
- **Use your own hand animation**: Replace the PNGs in
  `assets/hand_frames` with your own numbered sequence, or point
  `--hand-dir` at another directory containing PNGs of equal dimensions.
- **Adjust quality**: Use `--crf` (constant rate factor) to trade off
  between file size and quality. A lower number produces a higher quality
  (but larger) file.
- **Different output size**: Use `--size` to change the final video
  resolution. For example `--size 256` creates a 256×256 output instead of
  512×512.

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for
details.