
# Animated Headpat (clean build)

Fresh repo with:
- **Squish-enabled CLI**: `generate_headpat.py`
- **Gradio GUI**: `app.py`
- **Sample hand frames** under `assets/hand_frames/` (public domain placeholders — replace with your own art)
- Devcontainer that installs **ffmpeg** + Python deps

## Quick start
```bash
# Codespaces: just open the repo; devcontainer installs ffmpeg + deps.
# Local:
sudo apt-get update && sudo apt-get install -y ffmpeg
pip install -r requirements.txt
```

### GUI
```bash
python app.py
```
Upload a PNG with transparency, tweak squish params, hit **Generate** → preview + file in `outputs/`.

### CLI
```bash
python generate_headpat.py your.png   --size 512 --fps 30 --crf 32 --scale 0.9   --hand-dir assets/hand_frames   --squish-mode cosine --squish-min 0.88 --widen 0.12 --anchor top   -o outputs/headpat.webm
```

**Flags**
- `--squish-mode {cosine,triangle,none}` – animation curve
- `--squish-min` – vertical scale at impact (0.85–0.92 good)
- `--widen` – widen on impact (0.08–0.18 feels weighty)
- `--anchor {top,center}` – keep head pinned (`top`) or centered
- `--offset-x/--offset-y` – nudge placement

> Replace the placeholder `assets/hand_frames` with your real hand art for best results.
