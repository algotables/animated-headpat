
# Headpat Generator (Squish-enabled)

This pack adds a new script `generate_headpat_plus.py` that **squishes/unsquishes** the character in sync with the pat cycle.
It also provides `app_plus.py` — a Gradio GUI exposing the squish controls.

## Quick start
1) Ensure `ffmpeg` is installed and in PATH (Codespaces devcontainer or `apt-get install -y ffmpeg`).
2) `pip install -r requirements.txt`
3) Run GUI: `python app_plus.py` (or use the CLI below).

## CLI
```
python generate_headpat_plus.py your_character.png   --size 512 --fps 30 --crf 32 --scale 0.9   --hand-dir assets/hand_frames   --squish-mode cosine --squish-min 0.88 --widen 0.12 --anchor top   -o outputs/headpat.webm
```
- **--squish-mode**: `cosine` (smooth), `triangle` (snappy), or `none`
- **--squish-min**: vertical scale at impact (0.88 = 12% squish)
- **--widen**: how much to widen horizontally at impact (set 0 for no widen)
- **--anchor**: `top` keeps the top of the character fixed (looks like head pressed under hand)

## How it works
For each hand frame, we compute a phase 0→1 and a squish amount. The character is anisotropically scaled:
- Vertical scale `sy` goes from 1.0 (no squish) down to `squish_min` at impact
- Horizontal scale `sx` widens in proportion to the squish so volume feels preserved
We then composite `char -> hand` and encode to VP9 with an alpha channel.
