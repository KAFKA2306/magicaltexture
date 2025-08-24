# generators.py
# High-level generation functions that coordinate the image processing

from __future__ import annotations

import io
import os
import zipfile
import uuid
from typing import List, Tuple

import gradio as gr
from PIL import Image

from .core import load_rgba, load_mask, apply_basic, apply_gradient, apply_aurora, build_emission
from .config import PASTELS, PRETTY


def _sanitize(s: str) -> str:
    """Sanitize filename string"""
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in s)


def generate_single(
    eye_img: Image.Image,
    mask_img: Image.Image,
    preset: str,
    mode: str,
    keep_value: float,
    sat_scale: float,
    highlight: float,
    aurora_strength: float,
    make_emission: bool,
    ring_inner: float,
    ring_outer: float,
    ring_soft: float,
) -> Tuple[Image.Image, Image.Image]:
    """Generate a single colored eye texture"""
    if eye_img is None or mask_img is None:
        raise gr.Error("Please upload both an eye texture and a mask image! 🖼️")

    rgba = load_rgba(eye_img)
    mask01 = load_mask(mask_img, (rgba.shape[1], rgba.shape[0]))
    hue, sat, val = PASTELS[preset]

    if mode == "Basic":
        out = apply_basic(rgba, mask01, hue, sat, val, keep_value=keep_value, sat_scale=sat_scale)
    elif mode == "Gradient":
        out = apply_gradient(rgba, mask01, hue, sat, val, keep_value=keep_value, highlight=highlight)
    else:  # Aurora
        out = apply_aurora(rgba, mask01, hue, sat, val, keep_value=keep_value, strength=aurora_strength)

    out_img = Image.fromarray(out, mode="RGBA")

    if make_emission:
        emi = build_emission(mask01, inner=ring_inner, outer=ring_outer, softness=ring_soft)
        emi_img = Image.fromarray(emi, mode="L")
        return out_img, emi_img

    return out_img, None


def generate_batch(
    eye_img: Image.Image,
    mask_img: Image.Image,
    selected_colors: List[str],
    selected_modes: List[str],
    filename_prefix: str,
    keep_value: float,
    sat_scale: float,
    highlight: float,
    aurora_strength: float,
    make_emission: bool,
    ring_inner: float,
    ring_outer: float,
    ring_soft: float,
) -> Tuple[List[Tuple[Image.Image, str]], str]:
    """Generate multiple color and effect combinations"""
    if eye_img is None or mask_img is None:
        raise gr.Error("Please upload both an eye texture and a mask image! 🖼️")
    if not selected_colors:
        raise gr.Error("Please select at least one color palette! 🎨")
    if not selected_modes:
        raise gr.Error("Please select at least one effect mode! ✨")

    rgba = load_rgba(eye_img)
    mask01 = load_mask(mask_img, (rgba.shape[1], rgba.shape[0]))

    gallery_items = []  # [(PIL.Image, caption), ...]
    zip_buf = io.BytesIO()
    zip_name = f"{_sanitize(filename_prefix) or 'magical_eyes'}_{uuid.uuid4().hex[:8]}.zip"

    with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Emission (color-independent) added first if requested
        if make_emission:
            emi = build_emission(mask01, inner=ring_inner, outer=ring_outer, softness=ring_soft)
            emi_pil = Image.fromarray(emi, mode="L")
            b = io.BytesIO()
            emi_pil.save(b, format="PNG")
            zf.writestr("emission_glow_mask.png", b.getvalue())

        # Generate all color and mode combinations
        for ckey in selected_colors:
            hue, sat, val = PASTELS[ckey]
            for mode in selected_modes:
                if mode == "Basic":
                    out = apply_basic(
                        rgba, mask01, hue, sat, val, keep_value=keep_value, sat_scale=sat_scale
                    )
                elif mode == "Gradient":
                    out = apply_gradient(
                        rgba, mask01, hue, sat, val, keep_value=keep_value, highlight=highlight
                    )
                else:  # Aurora
                    out = apply_aurora(
                        rgba, mask01, hue, sat, val, keep_value=keep_value, strength=aurora_strength
                    )

                pil = Image.fromarray(out, mode="RGBA")
                caption = f"{PRETTY.get(ckey, ckey)} · {mode}"
                gallery_items.append((pil, caption))

                # Save to ZIP with descriptive filename
                fname = f"{_sanitize(filename_prefix) or 'eye'}_{ckey}_{mode.lower()}.png"
                buf = io.BytesIO()
                pil.save(buf, format="PNG")
                zf.writestr(fname, buf.getvalue())

    zip_buf.seek(0)
    zip_path = os.path.join(gr.utils.get_temp_dir(), zip_name)
    with open(zip_path, "wb") as f:
        f.write(zip_buf.read())

    return gallery_items, zip_path