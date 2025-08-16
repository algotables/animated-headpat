
import gradio as gr
import subprocess
import tempfile
import os
import uuid
import sys
from datetime import datetime
from typing import Optional

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "generate_headpat_plus.py")
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "outputs")
DEFAULT_HAND_DIR = os.path.join("assets","hand_frames")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

def _run_plus(
    image_path: str,
    size: int,
    fps: int,
    crf: int,
    scale: float,
    hand_dir: str,
    squish_mode: str,
    squish_min: float,
    widen: float,
    anchor: str,
    custom_filename: Optional[str] = None,
):
    if not os.path.isfile(SCRIPT_PATH):
        return None, "generate_headpat_plus.py is missing. Put app_plus.py next to it."

    base = custom_filename.strip() if custom_filename else f"headpat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    out_path = os.path.join(OUTPUTS_DIR, base + ".webm")

    cmd = [
        sys.executable, SCRIPT_PATH, image_path,
        "--size", str(size),
        "--fps", str(fps),
        "--crf", str(crf),
        "--scale", str(scale),
        "--hand-dir", hand_dir or DEFAULT_HAND_DIR,
        "--squish-mode", squish_mode,
        "--squish-min", str(squish_min),
        "--widen", str(widen),
        "--anchor", anchor,
        "-o", out_path
    ]

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=True)
        with open(out_path + ".log.txt", "w", encoding="utf-8") as f:
            f.write(proc.stdout)
    except subprocess.CalledProcessError as e:
        return None, ("Generation failed:\n\n" + (e.stdout or "<no output>"))

    if not os.path.exists(out_path):
        return None, "No output file produced."

    msg = f"Done! Path: {os.path.relpath(out_path)}\nLog: {os.path.relpath(out_path + '.log.txt')}"
    return out_path, msg

def generate(image, size, fps, crf, scale, hand_dir, squish_mode, squish_min, widen, anchor, custom_filename):
    if image is None:
        return None, "Upload an image first."
    with tempfile.TemporaryDirectory() as td:
        in_path = os.path.join(td, "input.png")
        image.save(in_path)
        return _run_plus(in_path, size, fps, crf, scale, hand_dir, squish_mode, squish_min, widen, anchor, custom_filename)

def build_ui():
    with gr.Blocks(theme=gr.themes.Soft(), css=".gradio-container {max-width: 1000px !important;}") as demo:
        gr.Markdown("# Animated Headpat – GUI (with squish)")

        with gr.Row():
            with gr.Column():
                image = gr.Image(type="pil", label="Character image (PNG w/ alpha recommended)")
                hand_dir = gr.Textbox(value=DEFAULT_HAND_DIR, label="Hand frames dir")
                custom_filename = gr.Textbox(value="", label="Output filename (optional)")
            with gr.Column():
                size = gr.Slider(256, 1024, value=512, step=32, label="Canvas size")
                fps = gr.Slider(12, 60, value=30, step=1, label="FPS")
                crf = gr.Slider(18, 40, value=32, step=1, label="CRF (lower = better)")
                scale = gr.Slider(0.4, 1.2, value=0.9, step=0.01, label="Character height (relative)")

        with gr.Accordion("Squish settings", open=True):
            with gr.Row():
                squish_mode = gr.Dropdown(choices=["cosine","triangle","none"], value="cosine", label="Mode")
                squish_min = gr.Slider(0.7, 1.0, value=0.88, step=0.01, label="Min vertical scale at impact")
                widen = gr.Slider(0.0, 0.5, value=0.12, step=0.01, label="Horizontal widen at impact")
                anchor = gr.Dropdown(choices=["top","center"], value="top", label="Anchor")

        go = gr.Button("Generate ✨", variant="primary")
        video = gr.Video(label="Preview")
        status = gr.Markdown()

        go.click(
            fn=generate,
            inputs=[image, size, fps, crf, scale, hand_dir, squish_mode, squish_min, widen, anchor, custom_filename],
            outputs=[video, status],
        )

        gr.Markdown("Tip: Use **top** anchor to keep the head pressed under the hand while squishing.")

    return demo

if __name__ == "__main__":
    app = build_ui()
    port = int(os.environ.get("PORT","7860"))
    app.launch(server_name="0.0.0.0", server_port=port)
