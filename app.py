# app.py
# Pastel Eye Colorizer — 単発/一括生成（Basic / Gradient / Aurora）＋一覧表示＋ZIP一括ダウンロード
# Gradio / NumPy / Pillow

from __future__ import annotations

import io
import os
import zipfile
import uuid
from typing import Optional, Tuple, List

import gradio as gr
import numpy as np
from PIL import Image


# ---------- ユーティリティ ----------
def load_rgba(img: Image.Image) -> np.ndarray:
    """PIL Image -> RGBA ndarray(uint8)"""
    return np.array(img.convert("RGBA"), dtype=np.uint8)


def load_mask(mask_img: Image.Image, size: Tuple[int, int]) -> np.ndarray:
    """PIL Image -> 2値マスク(0/1) ndarray(uint8), サイズは対象画像に合わせる"""
    if mask_img.size != size:
        mask_img = mask_img.resize(size, Image.Resampling.LANCZOS)
    m = np.array(mask_img.convert("L"), dtype=np.uint8)
    # 0/1 の二値化（白=1で適用）
    return (m > 32).astype(np.uint8)


def rgb_to_hsv_np(rgb: np.ndarray) -> np.ndarray:
    """RGB -> HSV (各0-1, float32), 形状は (..., 3) を維持"""
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
    denom = (maxc - minc) + 1e-12  # ゼロ割回避
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
    """HSV -> RGB (各0-1, float32), 形状は (..., 3) を維持"""
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
    """マスク領域の重心 (x, y) を返す。存在しない場合 None。"""
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return int(xs.mean()), int(ys.mean())


# パステル定義（HSV）
PASTELS = {
    "pastel_cyan": (0.50, 0.30, 0.92),
    "pastel_pink": (0.92, 0.25, 0.95),
    "pastel_lavender": (0.75, 0.20, 0.90),
    "pastel_mint": (0.40, 0.25, 0.92),
    "pastel_peach": (0.08, 0.30, 0.95),
    "pastel_lemon": (0.15, 0.25, 0.95),
    "pastel_coral": (0.02, 0.35, 0.90),
    "pastel_sky": (0.55, 0.20, 0.95),
    "deep_blue": (0.62, 0.48, 0.85),
}
PRETTY = {
    "pastel_cyan": "Cyan",
    "pastel_pink": "Pink",
    "pastel_lavender": "Lavender",
    "pastel_mint": "Mint",
    "pastel_peach": "Peach",
    "pastel_lemon": "Lemon",
    "pastel_coral": "Coral",
    "pastel_sky": "Sky",
    "deep_blue": "Deep Blue",
}


# ---------- 変換ロジック ----------
def apply_basic(
    rgb: np.ndarray,
    mask01: np.ndarray,
    hue: float,
    sat: float,
    val: float,
    keep_value: float = 0.7,
    sat_scale: float = 1.0,
) -> np.ndarray:
    """色相だけ置換する基本モード"""
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
    """中心→外周のグラデーション＋上部ハイライト"""
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

    # 内側→外側で彩度/明度を少し変える
    local_sat = np.clip(sat * (0.85 + 0.3 * (1.0 - d_norm)), 0.0, 1.0)
    local_val = np.clip(val * (0.90 + 0.2 * (1.0 - d_norm)), 0.0, 1.0)

    hsv[..., 0] = hue
    hsv[..., 1] = local_sat
    hsv[..., 2] = np.clip(hsv[..., 2] * keep_value + local_val * (1.0 - keep_value), 0.0, 1.0)

    # 上側ハイライト（少しだけ明るく）
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
    """波状の色相揺らぎでオーロラ風に"""
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
    """瞳孔周辺のリング発光マスク(L)を作成（相対半径指定）"""
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


# ---------- 単発生成（従来機能） ----------
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
    if eye_img is None or mask_img is None:
        raise gr.Error("eye_texture と mask の両方をアップロードしてください。")

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


# ---------- 一括生成 ----------
def _sanitize(s: str) -> str:
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
    if eye_img is None or mask_img is None:
        raise gr.Error("eye_texture と mask の両方をアップロードしてください。")
    if not selected_colors:
        raise gr.Error("少なくとも1つのパレットを選択してください。")
    if not selected_modes:
        raise gr.Error("少なくとも1つの効果モードを選択してください。")

    rgba = load_rgba(eye_img)
    mask01 = load_mask(mask_img, (rgba.shape[1], rgba.shape[0]))

    gallery_items = []  # [(PIL.Image, caption), ...]
    zip_buf = io.BytesIO()
    zip_name = f"{_sanitize(filename_prefix) or 'batch'}_{uuid.uuid4().hex[:8]}.zip"

    with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Emission（色非依存）を先に入れておく（任意）
        if make_emission:
            emi = build_emission(mask01, inner=ring_inner, outer=ring_outer, softness=ring_soft)
            emi_pil = Image.fromarray(emi, mode="L")
            b = io.BytesIO()
            emi_pil.save(b, format="PNG")
            zf.writestr("emission_mask.png", b.getvalue())

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

                fname = f"{_sanitize(filename_prefix) or 'eye'}_{ckey}_{mode.lower()}.png"
                buf = io.BytesIO()
                pil.save(buf, format="PNG")
                zf.writestr(fname, buf.getvalue())

    zip_buf.seek(0)
    zip_path = os.path.join(gr.utils.get_temp_dir(), zip_name)  # Gradioの一時ディレクトリへ保存
    with open(zip_path, "wb") as f:
        f.write(zip_buf.read())

    # Gallery は [(img, caption), ...] 形式を返す
    return gallery_items, zip_path


# ---------- UI ----------
with gr.Blocks(title="Pastel Eye Colorizer — 単発/一括") as demo:
    gr.Markdown("## Pastel Eye Colorizer｜マスク領域だけパステル化（Basic / Gradient / Aurora）＋一括生成")

    with gr.Tab("単発生成"):
        with gr.Row():
            eye_in = gr.Image(type="pil", label="Eye Texture (RGBA/RGB)")
            mask_in = gr.Image(type="pil", label="Mask (白=適用, 黒=非適用)")

        with gr.Row():
            preset = gr.Dropdown(choices=list(PASTELS.keys()), value="pastel_cyan", label="パレット")
            mode = gr.Radio(choices=["Basic", "Gradient", "Aurora"], value="Basic", label="効果モード")

        with gr.Accordion("調整（必要に応じて）", open=False):
            keep_value = gr.Slider(0.0, 1.0, value=0.7, step=0.05, label="明度保持率（元テクスチャをどれだけ残すか）")
            sat_scale = gr.Slider(0.5, 2.0, value=1.0, step=0.05, label="彩度スケール（Basic/Aurora）")
            highlight = gr.Slider(0.0, 1.0, value=0.4, step=0.05, label="ハイライト量（Gradient）")
            aurora_strength = gr.Slider(0.0, 0.6, value=0.3, step=0.02, label="オーロラ色揺らぎ（Aurora）")

        with gr.Accordion("発光マスクを作る（任意）", open=False):
            make_emission = gr.Checkbox(value=False, label="Emissionマスクも出力する")
            ring_inner = gr.Slider(0.02, 0.30, value=0.07, step=0.01, label="リング内半径（相対）")
            ring_outer = gr.Slider(0.05, 0.50, value=0.14, step=0.01, label="リング外半径（相対）")
            ring_soft = gr.Slider(0.01, 0.30, value=0.06, step=0.01, label="リングのぼかし（相対）")

        run_btn = gr.Button("生成する")
        out_img = gr.Image(type="pil", label="出力テクスチャ（PNG）")
        emi_img = gr.Image(type="pil", label="Emissionマスク（任意）")

        run_btn.click(
            fn=generate_single,
            inputs=[
                eye_in,
                mask_in,
                preset,
                mode,
                keep_value,
                sat_scale,
                highlight,
                aurora_strength,
                make_emission,
                ring_inner,
                ring_outer,
                ring_soft,
            ],
            outputs=[out_img, emi_img],
        )

    with gr.Tab("一括生成・一覧/ZIP"):
        with gr.Row():
            eye_in_b = gr.Image(type="pil", label="Eye Texture (RGBA/RGB)")
            mask_in_b = gr.Image(type="pil", label="Mask (白=適用, 黒=非適用)")

        colors_group = gr.CheckboxGroup(
            choices=list(PASTELS.keys()),
            value=["pastel_pink", "pastel_lavender", "pastel_mint", "pastel_peach"],
            label="一括パレット選択（複数選択可）",
        )
        modes_group = gr.CheckboxGroup(
            choices=["Basic", "Gradient", "Aurora"],
            value=["Gradient"],
            label="一括モード選択（複数選択可）",
        )
        filename_prefix = gr.Textbox(value="eye_color", label="出力ファイル名プレフィックス", placeholder="例: eye_color")

        with gr.Accordion("調整（必要に応じて）", open=False):
            keep_value_b = gr.Slider(0.0, 1.0, value=0.7, step=0.05, label="明度保持率（元テクスチャをどれだけ残すか）")
            sat_scale_b = gr.Slider(0.5, 2.0, value=1.0, step=0.05, label="彩度スケール（Basic/Aurora）")
            highlight_b = gr.Slider(0.0, 1.0, value=0.4, step=0.05, label="ハイライト量（Gradient）")
            aurora_strength_b = gr.Slider(0.0, 0.6, value=0.3, step=0.02, label="オーロラ色揺らぎ（Aurora）")

        with gr.Accordion("発光マスクを作る（任意）", open=False):
            make_emission_b = gr.Checkbox(value=False, label="EmissionマスクもZIPに同梱する")
            ring_inner_b = gr.Slider(0.02, 0.30, value=0.07, step=0.01, label="リング内半径（相対）")
            ring_outer_b = gr.Slider(0.05, 0.50, value=0.14, step=0.01, label="リング外半径（相対）")
            ring_soft_b = gr.Slider(0.01, 0.30, value=0.06, step=0.01, label="リングのぼかし（相対）")

        run_batch = gr.Button("一括生成する")
        gallery = gr.Gallery(label="生成一覧", columns=4, height=480, preview=True)
        zip_file = gr.File(label="一括ダウンロード（ZIP）")

        run_batch.click(
            fn=generate_batch,
            inputs=[
                eye_in_b,
                mask_in_b,
                colors_group,
                modes_group,
                filename_prefix,
                keep_value_b,
                sat_scale_b,
                highlight_b,
                aurora_strength_b,
                make_emission_b,
                ring_inner_b,
                ring_outer_b,
                ring_soft_b,
            ],
            outputs=[gallery, zip_file],
        )

# Hugging Face Spaces / ローカル両方で利用可能
if __name__ == "__main__":
    # 同時実行の安定性向上
    demo.queue().launch()
