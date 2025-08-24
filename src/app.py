# app.py
# Magical Texture - Eye Color Generator
# Transform eye textures with beautiful pastel colors using three different artistic effects
# Built with Gradio, NumPy, and Pillow for fast, deterministic image processing

from __future__ import annotations

import io
import os
import zipfile
import uuid
from typing import Optional, Tuple, List

import gradio as gr
import numpy as np
from PIL import Image


# ---------- Utility Functions ----------
def load_rgba(img: Image.Image) -> np.ndarray:
    """Convert PIL Image to RGBA ndarray(uint8)"""
    return np.array(img.convert("RGBA"), dtype=np.uint8)


def load_mask(mask_img: Image.Image, size: Tuple[int, int]) -> np.ndarray:
    """Convert PIL Image to binary mask(0/1) ndarray(uint8), resize to target image size"""
    if mask_img.size != size:
        mask_img = mask_img.resize(size, Image.Resampling.LANCZOS)
    m = np.array(mask_img.convert("L"), dtype=np.uint8)
    # Binary threshold (white=1 for application)
    return (m > 32).astype(np.uint8)


def rgb_to_hsv_np(rgb: np.ndarray) -> np.ndarray:
    """RGB -> HSV (each 0-1, float32), maintains shape (..., 3)"""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maxc = np.max(rgb, axis=-1)
    minc = np.min(rgb, axis=-1)
    v = maxc
    s = np.zeros_like(v)
    nz = maxc != 0
    s[nz] = (maxc[nz] - minc[nz]) / (maxc[nz] + 1e-12)

    h = np.zeros_like(v)
    mask = maxc != minc
    rc = np.zeros_like(r)
    gc = np.zeros_like(g)
    bc = np.zeros_like(b)
    denom = (maxc - minc) + 1e-12  # Avoid division by zero
    rc[mask] = (maxc[mask] - r[mask]) / denom[mask]
    gc[mask] = (maxc[mask] - g[mask]) / denom[mask]
    bc[mask] = (maxc[mask] - b[mask]) / denom[mask]

    rmax = (maxc == r) & mask
    gmax = (maxc == g) & mask
    bmax = (maxc == b) & mask
    h[rmax] = bc[rmax] - gc[rmax]
    h[gmax] = 2.0 + rc[gmax] - bc[gmax]
    h[bmax] = 4.0 + gc[bmax] - rc[bmax]
    h = (h / 6.0) % 1.0
    return np.stack([h, s, v], axis=-1).astype(np.float32)


def hsv_to_rgb_np(hsv: np.ndarray) -> np.ndarray:
    """HSV -> RGB (each 0-1, float32), maintains shape (..., 3)"""
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    c = v * s
    h6 = (h * 6.0) % 6.0
    x = c * (1 - np.abs((h6 % 2) - 1))
    z = np.zeros_like(h)

    rgbp = np.zeros(hsv.shape, dtype=hsv.dtype)
    conds = [
        (0 <= h6) & (h6 < 1),
        (1 <= h6) & (h6 < 2),
        (2 <= h6) & (h6 < 3),
        (3 <= h6) & (h6 < 4),
        (4 <= h6) & (h6 < 5),
        (5 <= h6) & (h6 < 6),
    ]
    rgbs = [
        (c, x, z),
        (x, c, z),
        (z, c, x),
        (z, x, c),
        (x, z, c),
        (c, z, x),
    ]
    for cond, (rr, gg, bb) in zip(conds, rgbs):
        rgbp[..., 0] = np.where(cond, rr, rgbp[..., 0])
        rgbp[..., 1] = np.where(cond, gg, rgbp[..., 1])
        rgbp[..., 2] = np.where(cond, bb, rgbp[..., 2])

    m = v - c
    rgb = rgbp + np.stack([m, m, m], axis=-1)
    return rgb.astype(np.float32)


def mask_centroid(mask: np.ndarray) -> Optional[Tuple[int, int]]:
    """Returns centroid (x, y) of mask region. None if no region exists."""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.mean()), int(ys.mean())


# Pastel color definitions (HSV)
PASTELS = {
    "pastel_cyan": (0.50, 0.30, 0.92),
    "pastel_pink": (0.92, 0.25, 0.95),
    "pastel_lavender": (0.75, 0.20, 0.90),
    "pastel_mint": (0.40, 0.25, 0.92),
    "pastel_peach": (0.08, 0.30, 0.95),
    "pastel_lemon": (0.15, 0.25, 0.95),
    "pastel_coral": (0.02, 0.35, 0.90),
    "pastel_sky": (0.55, 0.20, 0.95),
    "deep_blue": (0.65, 0.60, 0.80),  # Added deeper blue as requested
}

# User-friendly color names and descriptions
PRETTY = {
    "pastel_cyan": "Aqua Dream",
    "pastel_pink": "Soft Blossom", 
    "pastel_lavender": "Mystic Lavender",
    "pastel_mint": "Fresh Mint",
    "pastel_peach": "Warm Peach",
    "pastel_lemon": "Sunny Lemon",
    "pastel_coral": "Ocean Coral",
    "pastel_sky": "Sky Blue",
    "deep_blue": "Ocean Depths",
}

# Detailed descriptions for UI
COLOR_DESCRIPTIONS = {
    "pastel_cyan": "💧 Aqua Dream - Cool blue-green like tropical waters",
    "pastel_pink": "🌸 Soft Blossom - Gentle pink like cherry blossoms", 
    "pastel_lavender": "💜 Mystic Lavender - Light purple with magical charm",
    "pastel_mint": "🌿 Fresh Mint - Soft green like spring leaves",
    "pastel_peach": "🍑 Warm Peach - Orange-pink like sunset clouds",
    "pastel_lemon": "🍋 Sunny Lemon - Light yellow like morning sunshine",
    "pastel_coral": "🪸 Ocean Coral - Pink-orange like coral reefs",
    "pastel_sky": "☁️ Sky Blue - Light blue like clear summer sky",
    "deep_blue": "🌊 Ocean Depths - Rich deep blue like midnight waters",
}

# Effect mode descriptions for users
EFFECT_DESCRIPTIONS = {
    "Basic": "Simple, uniform color change - clean and consistent",
    "Gradient": "Smooth color transitions from center to edge with subtle highlights", 
    "Aurora": "Magical color shimmer effect like northern lights"
}


# ---------- Color Transformation Logic ----------
def apply_basic(
    rgb: np.ndarray,
    mask01: np.ndarray,
    hue: float,
    sat: float,
    val: float,
    keep_value: float = 0.7,
    sat_scale: float = 1.0,
) -> np.ndarray:
    """Basic mode: Simple hue replacement with uniform color"""
    a = rgb[..., 3:4] / 255.0
    base = rgb[..., :3] / 255.0
    hsv = rgb_to_hsv_np(base)
    hsv[..., 0] = hue
    hsv[..., 1] = np.clip(sat * sat_scale, 0.0, 1.0)
    hsv[..., 2] = np.clip(hsv[..., 2] * keep_value + val * (1.0 - keep_value), 0.0, 1.0)
    recolor = hsv_to_rgb_np(hsv)
    out_rgb = np.where(mask01[..., None] == 1, recolor, base)
    out = np.concatenate([out_rgb, a], axis=-1)
    return (np.clip(out * 255.0, 0.0, 255.0).astype(np.uint8))


def apply_gradient(
    rgb: np.ndarray,
    mask01: np.ndarray,
    hue: float,
    sat: float,
    val: float,
    keep_value: float = 0.7,
    highlight: float = 0.4,
) -> np.ndarray:
    """Gradient mode: Center to edge gradient with upper highlights"""
    h, w = mask01.shape
    cxcy = mask_centroid(mask01)
    base = rgb[..., :3] / 255.0
    hsv = rgb_to_hsv_np(base)
    if cxcy is None:
        return rgb

    cx, cy = cxcy
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    dist_mask = dist[mask01 == 1]
    d_norm = (dist - dist_mask.min()) / (max(dist_mask.ptp(), 1e-6))
    d_norm = np.clip(d_norm, 0.0, 1.0)

    # Inner to outer: vary saturation/value slightly
    local_sat = np.clip(sat * (0.85 + 0.3 * (1.0 - d_norm)), 0.0, 1.0)
    local_val = np.clip(val * (0.90 + 0.2 * (1.0 - d_norm)), 0.0, 1.0)

    hsv[..., 0] = hue
    hsv[..., 1] = local_sat
    hsv[..., 2] = np.clip(hsv[..., 2] * keep_value + local_val * (1.0 - keep_value), 0.0, 1.0)

    # Upper highlight (slightly brighter)
    top = yy < (cy - 0.05 * h)
    hsv[..., 2] = np.where(
        top & (mask01 == 1),
        np.clip(hsv[..., 2] + highlight * 0.15, 0.0, 1.0),
        hsv[..., 2],
    )

    recolor = hsv_to_rgb_np(hsv)
    out_rgb = np.where(mask01[..., None] == 1, recolor, base)
    a = rgb[..., 3:4] / 255.0
    out = np.concatenate([out_rgb, a], axis=-1)
    return (np.clip(out * 255.0, 0.0, 255.0).astype(np.uint8))


def apply_aurora(
    rgb: np.ndarray,
    mask01: np.ndarray,
    hue: float,
    sat: float,
    val: float,
    keep_value: float = 0.7,
    strength: float = 0.3,
) -> np.ndarray:
    """Aurora mode: Wave-like hue fluctuations for magical shimmer effect"""
    h, w = mask01.shape
    base = rgb[..., :3] / 255.0
    hsv = rgb_to_hsv_np(base)

    yy, xx = np.mgrid[0:h, 0:w]
    wave = (
        np.sin((xx + yy) * 0.02) * 0.4
        + np.cos(xx * 0.015) * 0.3
        + np.sin(yy * 0.02) * 0.3
    )
    hue_offset = np.clip(wave * strength, -0.15, 0.15)

    hsv[..., 0] = (hue + hue_offset) % 1.0
    hsv[..., 1] = np.clip(sat + (np.sin(xx * 0.01 + yy * 0.015) * 0.1 + 0.1), 0.0, 0.6)
    hsv[..., 2] = np.clip(hsv[..., 2] * keep_value + val * (1.0 - keep_value), 0.0, 1.0)

    recolor = hsv_to_rgb_np(hsv)
    out_rgb = np.where(mask01[..., None] == 1, recolor, base)
    a = rgb[..., 3:4] / 255.0
    out = np.concatenate([out_rgb, a], axis=-1)
    return (np.clip(out * 255.0, 0.0, 255.0).astype(np.uint8))


def build_emission(
    mask01: np.ndarray,
    inner: float = 0.07,
    outer: float = 0.14,
    softness: float = 0.06,
) -> np.ndarray:
    """Create ring-shaped emission mask (L) around pupil area with relative radius"""
    h, w = mask01.shape
    cxcy = mask_centroid(mask01)
    if cxcy is None:
        return (mask01 * 255).astype(np.uint8)

    cx, cy = cxcy
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)

    ys, xs = np.nonzero(mask01)
    rx = (xs.max() - xs.min()) / 2.0 + 1e-6
    ry = (ys.max() - ys.min()) / 2.0 + 1e-6
    r = float(np.hypot(rx, ry))

    d = dist / r
    ring_in = np.clip((d - inner) / max(softness, 1e-6), 0.0, 1.0)
    ring_out = 1.0 - np.clip((d - outer) / max(softness, 1e-6), 0.0, 1.0)
    ring = np.clip(ring_out * (1.0 - ring_in), 0.0, 1.0) * mask01
    return (ring * 255).astype(np.uint8)


# ---------- Single Generation (Original Feature) ----------
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
):
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
    else:
        out = apply_aurora(rgba, mask01, hue, sat, val, keep_value=keep_value, strength=aurora_strength)

    out_img = Image.fromarray(out, mode="RGBA")

    if make_emission:
        emi = build_emission(mask01, inner=ring_inner, outer=ring_outer, softness=ring_soft)
        emi_img = Image.fromarray(emi, mode="L")
        return out_img, emi_img

    return out_img, None


# ---------- Batch Generation ----------
def _sanitize(s: str) -> str:
    """Sanitize filename string"""
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in s)


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
):
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


# ---------- User Interface ----------
def format_color_choice(key):
    """Format color choice for dropdown display"""
    return COLOR_DESCRIPTIONS[key]

with gr.Blocks(title="Magical Texture - Eye Color Generator", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎨 Magical Texture - Eye Color Generator
    
    Transform your eye textures with beautiful pastel colors! Upload your eye image and mask, 
    then choose from 8 stunning color palettes and 3 artistic effects.
    
    **Perfect for:** Avatar creators, game developers, VTubers, and digital artists
    """)

    with gr.Tab("🎯 Single Generation"):
        gr.Markdown("""
        ### How to use:
        1. **Upload your eye texture** - The main image you want to colorize
        2. **Upload a mask** - White areas will be colored, black areas stay unchanged
        3. **Choose a color and effect** - Pick your favorite combination
        4. **Generate!** - Your new eye texture will appear below
        """)
        
        with gr.Row():
            eye_in = gr.Image(
                type="pil", 
                label="🖼️ Eye Texture",
                info="Upload your eye image (PNG/JPG with or without transparency)"
            )
            mask_in = gr.Image(
                type="pil", 
                label="🎭 Color Mask", 
                info="White areas = will be colored, Black areas = stay original"
            )

        with gr.Row():
            preset = gr.Dropdown(
                choices=[(format_color_choice(k), k) for k in PASTELS.keys()], 
                value="pastel_cyan", 
                label="🎨 Color Palette",
                info="Choose your favorite pastel color - each has its own magical charm!"
            )
            mode = gr.Radio(
                choices=[("Basic - " + EFFECT_DESCRIPTIONS["Basic"], "Basic"),
                        ("Gradient - " + EFFECT_DESCRIPTIONS["Gradient"], "Gradient"),
                        ("Aurora - " + EFFECT_DESCRIPTIONS["Aurora"], "Aurora")], 
                value="Gradient", 
                label="✨ Effect Style",
                info="Select the artistic style for your color transformation"
            )

        with gr.Accordion("⚙️ Advanced Settings (Optional - Default values work great!)", open=False):
            gr.Markdown("**Fine-tune the effect intensity - only adjust if you want a different look**")
            keep_value = gr.Slider(
                0.0, 1.0, value=0.7, step=0.05, 
                label="💡 Original Brightness",
                info="How much of the original texture brightness to keep (0.7 = 70% original)"
            )
            sat_scale = gr.Slider(
                0.5, 2.0, value=1.0, step=0.05, 
                label="🌈 Color Intensity (Basic/Aurora)",
                info="Make colors more vivid (>1.0) or more subtle (<1.0)"
            )
            highlight = gr.Slider(
                0.0, 1.0, value=0.4, step=0.05, 
                label="✨ Highlight Strength (Gradient)",
                info="Add bright highlights to the upper area for extra sparkle"
            )
            aurora_strength = gr.Slider(
                0.0, 0.6, value=0.3, step=0.02, 
                label="🌟 Magic Shimmer (Aurora)",
                info="Control how much the colors dance and shimmer"
            )

        with gr.Accordion("💫 Glow Effect (Optional - For 3D engines that support emission)", open=False):
            gr.Markdown("**Create a separate glow mask for realistic light emission in 3D applications**")
            make_emission = gr.Checkbox(
                value=False, 
                label="🔥 Generate Glow Mask",
                info="Creates a ring-shaped glow effect around the pupil area"
            )
            ring_inner = gr.Slider(
                0.02, 0.30, value=0.07, step=0.01, 
                label="Inner Ring Size",
                info="How close to the center the glow starts"
            )
            ring_outer = gr.Slider(
                0.05, 0.50, value=0.14, step=0.01, 
                label="Outer Ring Size",
                info="How far from center the glow extends"
            )
            ring_soft = gr.Slider(
                0.01, 0.30, value=0.06, step=0.01, 
                label="Glow Softness",
                info="How smooth the glow edge appears"
            )

        run_btn = gr.Button("🚀 Generate My Eye Color!", variant="primary", size="lg")
        
        gr.Markdown("### 🎉 Your Results:")
        with gr.Row():
            out_img = gr.Image(
                type="pil", 
                label="🖼️ Colored Eye Texture",
                info="Right-click to save this image"
            )
            emi_img = gr.Image(
                type="pil", 
                label="💫 Glow Mask (if enabled)",
                info="Use this in your 3D software's emission channel"
            )

        run_btn.click(
            fn=generate_single,
            inputs=[
                eye_in, mask_in, preset, mode, keep_value, sat_scale, 
                highlight, aurora_strength, make_emission, ring_inner, ring_outer, ring_soft
            ],
            outputs=[out_img, emi_img],
        )

    with gr.Tab("🎨 Batch Generation & Gallery"):
        gr.Markdown("""
        ### Create Multiple Variations at Once!
        
        Generate many different color and effect combinations in one go. Perfect for:
        - Trying out different looks quickly
        - Creating color variants for characters
        - Building a library of eye textures
        
        **You'll get:** A gallery preview + ZIP file with all variations for download
        """)
        
        with gr.Row():
            eye_in_b = gr.Image(
                type="pil", 
                label="🖼️ Eye Texture",
                info="Upload your eye image (same as single mode)"
            )
            mask_in_b = gr.Image(
                type="pil", 
                label="🎭 Color Mask",
                info="White areas will be colored in all variations"
            )

        with gr.Row():
            colors_group = gr.CheckboxGroup(
                choices=[(format_color_choice(k), k) for k in PASTELS.keys()],
                value=["pastel_pink", "pastel_lavender", "pastel_mint", "pastel_peach"],
                label="🎨 Colors to Generate",
                info="Select multiple colors - each will be generated with your chosen effects"
            )
            modes_group = gr.CheckboxGroup(
                choices=[("Basic - " + EFFECT_DESCRIPTIONS["Basic"], "Basic"),
                        ("Gradient - " + EFFECT_DESCRIPTIONS["Gradient"], "Gradient"),
                        ("Aurora - " + EFFECT_DESCRIPTIONS["Aurora"], "Aurora")],
                value=["Gradient"],
                label="✨ Effects to Apply",
                info="Choose which artistic effects to create for each color"
            )
        
        filename_prefix = gr.Textbox(
            value="magical_eye", 
            label="📁 File Name Prefix",
            placeholder="e.g., character_eyes, avatar_v1",
            info="This will be added to the beginning of each generated file name"
        )

        with gr.Accordion("⚙️ Batch Settings (Optional - Uses same settings for all generations)", open=False):
            keep_value_b = gr.Slider(
                0.0, 1.0, value=0.7, step=0.05, 
                label="💡 Original Brightness",
                info="Applied to all generations"
            )
            sat_scale_b = gr.Slider(
                0.5, 2.0, value=1.0, step=0.05, 
                label="🌈 Color Intensity",
                info="Applied to Basic and Aurora effects"
            )
            highlight_b = gr.Slider(
                0.0, 1.0, value=0.4, step=0.05, 
                label="✨ Highlight Strength",
                info="Applied to Gradient effects"
            )
            aurora_strength_b = gr.Slider(
                0.0, 0.6, value=0.3, step=0.02, 
                label="🌟 Magic Shimmer",
                info="Applied to Aurora effects"
            )

        with gr.Accordion("💫 Glow Effect for Batch (Optional)", open=False):
            make_emission_b = gr.Checkbox(
                value=False, 
                label="🔥 Include Glow Mask in ZIP",
                info="Adds one emission mask file that works with all color variations"
            )
            ring_inner_b = gr.Slider(0.02, 0.30, value=0.07, step=0.01, label="Inner Ring Size")
            ring_outer_b = gr.Slider(0.05, 0.50, value=0.14, step=0.01, label="Outer Ring Size")
            ring_soft_b = gr.Slider(0.01, 0.30, value=0.06, step=0.01, label="Glow Softness")

        run_batch = gr.Button("🎨 Generate All Combinations!", variant="primary", size="lg")
        
        gr.Markdown("### 🖼️ Your Gallery:")
        gallery = gr.Gallery(
            label="Generated Variations", 
            columns=4, 
            height=600, 
            preview=True,
            info="Click on any image to view it larger. All images are also saved in the ZIP file below."
        )
        
        gr.Markdown("### 📦 Download Everything:")
        zip_file = gr.File(
            label="ZIP Download", 
            info="Contains all generated images with descriptive filenames. Perfect for organizing your texture library!"
        )

        run_batch.click(
            fn=generate_batch,
            inputs=[
                eye_in_b, mask_in_b, colors_group, modes_group, filename_prefix,
                keep_value_b, sat_scale_b, highlight_b, aurora_strength_b,
                make_emission_b, ring_inner_b, ring_outer_b, ring_soft_b
            ],
            outputs=[gallery, zip_file],
        )

# Launch configuration for both Hugging Face Spaces and local use
if __name__ == "__main__":
    # Improve stability for concurrent use
    demo.queue().launch()