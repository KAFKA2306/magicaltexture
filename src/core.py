# core.py
# Core image processing functions for Magical Texture

from __future__ import annotations
from typing import Optional, Tuple
import numpy as np
from PIL import Image


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