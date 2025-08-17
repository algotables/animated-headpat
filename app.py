import gradio as gr
import subprocess, tempfile, os, uuid, sys
from datetime import datetime

OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "outputs")
DEFAULT_HAND_DIR = os.path.join("assets","hand_frames")
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "generate_headpat.py")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

def run_cli(image_path, size, fps, crf, scale, hand_dir, squish_mode, squish_min, widen, anchor, offset_x, offset_y, custom_filename):
    base = custom_filename.strip() if custom_filename else f"headpat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    out_path = os.path.join(OUTPUTS_DIR, base + ".webm")
    cmd = [
        sys.executable, SCRIPT_PATH, image_path,
        "--size", str(size), "--fps", str(fps), "--crf", str(crf), "--scale", str(scale),
        "--hand-dir", hand_dir or DEFAULT_HAND_DIR,
        "--squish-mode", squish_mode, "--squish-min", str(squish_min), "--widen", str(widen),
        "--anchor", anchor, "--offset-x", str(offset_x), "--offset-y", str(offset_y),
        "-o", out_path
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    with open(out_path + ".log.txt", "w", encoding="utf-8") as f:
        f.write(proc.stdout)
    if proc.returncode != 0 or not os.path.exists(out_path):
        return None, "Generation failed. See log next to output."
    return out_path, f"Done! {os.path.relpath(out_path)}"

def generate(image, size, fps, crf, scale, hand_dir, squish_mode, squish_min, widen, anchor, offset_x, offset_y, custom_filename):
    if image is None:
        return None, "Upload a PNG with alpha for best results."
    with tempfile.TemporaryDirectory() as td:
        in_path = os.path.join(td, "input.png")
        image.save(in_path)
        return run_cli(in_path, size, fps, crf, scale, hand_dir, squish_mode, squish_min, widen, anchor, offset_x, offset_y, custom_filename)

def build_ui():
    with gr.Blocks(theme=gr.themes.Soft(), css=".gradio-container {max-width: 1024px !important;}") as demo:
        gr.Markdown("# Animated Headpat – GUI (squish-enabled)")
        with gr.Row():
            with gr.Column():
                image = gr.Image(type="pil", label="Character image (PNG w/ alpha recommended)")
                hand_dir = gr.Textbox(value=DEFAULT_HAND_DIR, label="Hand frames directory")
                custom_filename = gr.Textbox(value="", label="Output filename (optional)")
            with gr.Column():
                size = gr.Slider(256, 1024, value=512, step=32, label="Canvas size")
                fps  = gr.Slider(12, 60, value=30, step=1, label="FPS")
                crf  = gr.Slider(18, 40, value=32, step=1, label="CRF (lower = better)")
                scale= gr.Slider(0.4, 1.2, value=0.9, step=0.01, label="Character height (relative)")

        with gr.Accordion("Squish & placement", open=True):
            with gr.Row():
                squish_mode = gr.Dropdown(choices=["cosine","triangle","none"], value="cosine", label="Squish mode")
                squish_min  = gr.Slider(0.7, 1.0, value=0.88, step=0.01, label="Min vertical scale at impact")
                widen       = gr.Slider(0.0, 0.5, value=0.12, step=0.01, label="Horizontal widen at impact")
                anchor      = gr.Dropdown(choices=["top","center"], value="top", label="Anchor")
            with gr.Row():
                offset_x    = gr.Slider(-200, 200, value=0, step=1, label="Offset X (px)")
                offset_y    = gr.Slider(-200, 200, value=0, step=1, label="Offset Y (px)")

        go = gr.Button("Generate ✨", variant="primary")
        video = gr.Video(label="Preview (WebM)")
        status = gr.Markdown()
        go.click(fn=generate, inputs=[image,size,fps,crf,scale,hand_dir,squish_mode,squish_min,widen,anchor,offset_x,offset_y,custom_filename], outputs=[video,status])
        gr.Markdown("Tip: Use **top** anchor to keep the head pinned while squishing. Requires **ffmpeg** in PATH.")
    return demo

if __name__ == "__main__":
    app = build_ui()
    import os
    port = int(os.environ.get("PORT","7860"))
    app.launch(server_name="0.0.0.0", server_port=port)
