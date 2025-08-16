
import gradio as gr
import subprocess
import tempfile
import os
import uuid
import sys
from datetime import datetime
from typing import Optional

# Paths inside the repo
DEFAULT_HAND_DIR = os.path.join("assets", "hand_frames")
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "generate_headpat.py")
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "outputs")

os.makedirs(OUTPUTS_DIR, exist_ok=True)


def _ensure_generate_script():
    if not os.path.isfile(SCRIPT_PATH):
        raise FileNotFoundError(
            "generate_headpat.py not found next to app.py. Make sure you run this from the repo root."
        )


def _run_headpat_cli(
    image_path: str,
    size: int = 512,
    fps: int = 30,
    crf: int = 32,
    scale: float = 0.9,
    hand_dir: str = DEFAULT_HAND_DIR,
    custom_filename: Optional[str] = None,
):
    """Call the repo's CLI to produce a WebM with alpha and return the output path."""
    _ensure_generate_script()

    # Final output path
    if custom_filename:
        base = os.path.splitext(os.path.basename(custom_filename))[0]
    else:
        base = f"headpat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    out_path = os.path.join(OUTPUTS_DIR, base + ".webm")

    # Build the command. We use the current Python to run the script.
    cmd = [
        sys.executable,
        SCRIPT_PATH,
        image_path,
        "--size",
        str(size),
        "--fps",
        str(fps),
        "--scale",
        str(scale),
        "--crf",
        str(crf),
        "--hand-dir",
        hand_dir,
        "-o",
        out_path,
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
            text=True,
        )
        # Optional: write logs alongside the output
        with open(out_path + ".log.txt", "w", encoding="utf-8") as f:
            f.write(proc.stdout)
    except FileNotFoundError as e:
        # Common case: ffmpeg not installed or wrong Python
        return None, (
            "Command failed to start. Ensure dependencies are installed.\n\n"
            f"Details: {e}\n\n"
            "If this is ffmpeg-related, install it in your devcontainer or machine.\n"
            "Debian/Ubuntu: apt-get update && apt-get install -y ffmpeg\n"
        )
    except subprocess.CalledProcessError as e:
        return None, (
            "Headpat generation failed. Here's the CLI output to help debug:\n\n"
            + (e.stdout or "<no output>")
        )

    if not os.path.exists(out_path):
        return None, "Generation finished but output file is missing."
    return out_path, None


def generate(
    image,
    size,
    fps,
    crf,
    scale,
    hand_dir,
    custom_filename,
):
    """Gradio handler: save the uploaded image, call CLI, return a playable WebM."""
    if image is None:
        return None, "Please upload an image (preferably PNG with transparency)."

    # Save the uploaded image to a temp file as PNG to be safe
    with tempfile.TemporaryDirectory() as td:
        in_path = os.path.join(td, "input.png")
        image.save(in_path)
        out_path, err = _run_headpat_cli(
            in_path,
            size=size,
            fps=fps,
            crf=crf,
            scale=scale,
            hand_dir=hand_dir or DEFAULT_HAND_DIR,
            custom_filename=custom_filename.strip() if custom_filename else None,
        )

    if err:
        return None, err

    # Return the video path for preview + a friendly message
    msg = (
        "Done! Preview below. File is also saved under 'outputs/'.\n\n"
        f"Path: {os.path.relpath(out_path)}\n"
        f"Log: {os.path.relpath(out_path + '.log.txt')}\n"
    )
    return out_path, msg


def build_ui():
    with gr.Blocks(theme=gr.themes.Soft(), css=".gradio-container {max-width: 980px !important;}") as demo:
        gr.Markdown(
            """
            # Animated Headpat – GUI
            Upload a character image and generate a 512×512 WebM with alpha (VP9) using the repo's CLI.

            **Tip:** PNG with transparent background gives the best results. Adjust scale if the hand feels too big/small.
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                image = gr.Image(type="pil", label="Character image (PNG recommended)")
                hand_dir = gr.Textbox(value=DEFAULT_HAND_DIR, label="Hand frames directory", placeholder="assets/hand_frames")
                custom_filename = gr.Textbox(value="", label="Output filename (optional, without extension)")
            with gr.Column(scale=1):
                size = gr.Slider(256, 1024, value=512, step=32, label="Canvas size (pixels)")
                fps = gr.Slider(12, 60, value=30, step=1, label="FPS")
                crf = gr.Slider(18, 40, value=32, step=1, label="CRF (quality; lower is better)")
                scale = gr.Slider(0.5, 1.5, value=0.9, step=0.01, label="Character scale under hand")

        go = gr.Button("Generate headpat ✨", variant="primary")

        with gr.Row():
            video = gr.Video(label="Preview (WebM with alpha)")
        status = gr.Markdown()

        go.click(
            fn=generate,
            inputs=[image, size, fps, crf, scale, hand_dir, custom_filename],
            outputs=[video, status],
            api_name="generate",
        )

        gr.Markdown(
            """
            ### Troubleshooting
            - **ffmpeg not found?** Install it (e.g., `apt-get update && apt-get install -y ffmpeg`).
            - **No output / errors?** Check the `outputs/*.log.txt` next to your rendered file.
            - **Codespaces:** Forward the port shown in the console (defaults to 7860) and open in browser.
            """
        )

    return demo


if __name__ == "__main__":
    app = build_ui()
    # For Codespaces, bind to 0.0.0.0 and use the PORT env if provided
    port = int(os.environ.get("PORT", "7860"))
    app.launch(server_name="0.0.0.0", server_port=port)
