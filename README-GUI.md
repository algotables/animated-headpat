
# Animated Headpat – GUI Pack

This adds a simple Gradio GUI on top of `generate_headpat.py`. It lets you upload an image, tweak params, and export a 512×512 VP9 WebM (with alpha) suitable for Telegram and similar platforms.

## Files in this pack
- `app.py` — the GUI. Keep it in the repo root (same folder as `generate_headpat.py`).
- `requirements.txt` — adds `gradio` and `Pillow` (merge into your existing requirements if needed).
- `.devcontainer/devcontainer.json` — optional; installs ffmpeg and Python deps automatically in Codespaces.
- `Makefile` — optional shortcuts.
- `outputs/.gitkeep` — ensures the outputs directory exists in git.
- `.gitignore` — ignores build artifacts, outputs, and logs (merge as you wish).

## Quick start (local or Codespaces)
1. Ensure `ffmpeg` is installed.
   - Debian/Ubuntu: `apt-get update && apt-get install -y ffmpeg`
2. Install Python deps: `pip install -r requirements.txt`
3. Run the GUI: `python app.py`
4. Open the shown URL (in Codespaces, use the forwarded port).

## Notes
- By default, it expects hand frames at `assets/hand_frames` (same as the CLI). You can override the path in the GUI.
- Each render writes a `.log.txt` next to the output video for debugging.
