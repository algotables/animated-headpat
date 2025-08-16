#!/usr/bin/env python3
"""
Simple web interface for generating head‑pat animations.

This script uses the ``gradio`` library to provide a drag‑and‑drop GUI. Users
can upload an image, adjust the character scale and optional squish effect,
and download the resulting WebM animation. Internally it leverages
``generate_headpat.py`` for the heavy lifting.

Run this inside your Codespace or locally with Python installed. When
running in a Codespace, GitHub will offer a port forward after the
interface launches.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import gradio as gr
from PIL import Image

from generate_headpat import load_hand_frames, create_headpat_frames, save_frames_as_webm

# Determine the location of the hand frames relative to this file
HAND_DIR = Path(__file__).parent / "assets" / "hand_frames"


def make_headpat(image: Image.Image, scale: float, squish: bool) -> tuple[str, str]:
    """Generate a head‑pat WebM from a PIL image.

    Parameters
    ----------
    image : PIL.Image.Image
        The uploaded character image.
    scale : float
        Character width relative to the hand frame (0–1).
    squish : bool
        Whether to apply the gentle squish effect.

    Returns
    -------
    Tuple[str, str]
        A tuple of (file path, downloadable filename) for Gradio to serve.
    """
    # Ensure RGBA
    char_img = image.convert("RGBA")
    hand_frames = load_hand_frames(HAND_DIR)
    frames = create_headpat_frames(hand_frames, char_img, scale, squish=squish)
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        save_frames_as_webm(frames, fps=30, size=512, crf=32, out_path=Path(tmp.name))
        # Provide a friendly filename for the user
        download_name = Path(tmp.name).with_suffix(".webm").name
        return tmp.name, download_name


with gr.Blocks(title="Head‑Pat Generator") as demo:
    gr.Markdown(
        """# Head‑Pat Generator

        Upload an image of your character, adjust the scale and squish settings,
        and get a looping head‑pat animation with a transparent background.
        """
    )
    with gr.Row():
        with gr.Column():
            inp = gr.Image(type="pil", label="Upload image", tool=None)
            scale_slider = gr.Slider(
                minimum=0.4,
                maximum=1.0,
                value=0.9,
                step=0.05,
                label="Character scale (fraction of canvas width)",
            )
            squish_checkbox = gr.Checkbox(
                value=True,
                label="Apply gentle squish effect",
            )
            generate_button = gr.Button("Generate head‑pat")
        with gr.Column():
            out_file = gr.File(label="Download your head‑pat WebM")

    def _generate(image, scale, squish):
        if image is None:
            raise gr.Error("Please upload an image.")
        return make_headpat(image, scale, squish)

    generate_button.click(
        _generate,
        inputs=[inp, scale_slider, squish_checkbox],
        outputs=[out_file],
    )

if __name__ == "__main__":
    # When run directly, launch on port 7860 without sharing by default.
    # In Codespaces, GitHub will prompt you to open the forwarded port.
    demo.launch()
