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
    """Improved center-to-edge gradient with smooth transitions and natural highlights"""
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

    # Improved distance normalization with smoother falloff
    d_norm = (dist - dist_mask.min()) / (max(dist_mask.ptp(), 1e-6))
    d_norm = np.clip(d_norm, 0.0, 1.0)

    # Smooth falloff curve instead of linear - creates more natural gradient
    falloff = 1.0 - np.power(d_norm, 1.2)  # Slight curve for more natural transition

    # More subtle saturation/value variation for better visual quality
    local_sat = np.clip(sat * (0.92 + 0.16 * falloff), 0.0, 1.0)  # Less aggressive variation
    local_val = np.clip(val * (0.94 + 0.12 * falloff), 0.0, 1.0)  # More subtle brightness change

    hsv[..., 0] = hue
    hsv[..., 1] = local_sat
    hsv[..., 2] = np.clip(hsv[..., 2] * keep_value + local_val * (1.0 - keep_value), 0.0, 1.0)

    # Improved highlight system with multiple zones and smoother blending
    # Upper highlight zone (main)
    upper_zone = yy < (cy - 0.03 * h)  # Slightly larger zone
    # Additional subtle rim light
    rim_zone = (d_norm > 0.7) & (d_norm < 0.95)

    # Apply highlights with smooth blending
    highlight_strength = highlight * 0.12  # Reduced intensity for subtlety
    hsv[..., 2] = np.where(
        upper_zone & (mask01 == 1),
        np.clip(hsv[..., 2] + highlight_strength * (1.0 - d_norm * 0.5), 0.0, 1.0),
        hsv[..., 2],
    )

    # Subtle rim lighting for depth
    rim_strength = highlight * 0.08
    hsv[..., 2] = np.where(
        rim_zone & (mask01 == 1),
        np.clip(hsv[..., 2] + rim_strength, 0.0, 1.0),
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
    """Improved aurora effect with organic color shimmer and harmonious variations"""
    h, w = mask01.shape
    base = rgb[..., :3] / 255.0
    hsv = rgb_to_hsv_np(base)

    yy, xx = np.mgrid[0:h, 0:w]

    # More organic wave patterns with finer detail and better scaling
    # Primary wave (creates main flow)
    wave1 = np.sin((xx * 0.008 + yy * 0.005) * np.pi) * 0.35
    # Secondary wave (creates shimmer detail)
    wave2 = np.cos((xx * 0.012 - yy * 0.009) * np.pi) * 0.25
    # Tertiary wave (adds subtle complexity)
    wave3 = np.sin((xx * 0.006 + yy * 0.011) * np.pi) * 0.15

    # Combine waves for more natural aurora flow
    wave = wave1 + wave2 + wave3
    hue_offset = np.clip(wave * strength, -0.12, 0.12)  # Slightly reduced range

    # Apply hue variation with smooth wrapping
    hsv[..., 0] = (hue + hue_offset) % 1.0

    # More coherent saturation variation based on base saturation
    sat_wave = np.sin(xx * 0.007 + yy * 0.009) * 0.08 + np.cos(xx * 0.005) * 0.06
    # Keep saturation variation relative to the base and clamp reasonably
    hsv[..., 1] = np.clip(sat * (1.0 + sat_wave), 0.0, min(sat * 1.3, 0.8))

    # Value follows the same pattern as basic mode for consistency
    hsv[..., 2] = np.clip(hsv[..., 2] * keep_value + val * (1.0 - keep_value), 0.0, 1.0)

    # Add subtle additional brightness variation for aurora glow effect
    brightness_wave = np.sin(xx * 0.009 - yy * 0.007) * 0.04
    hsv[..., 2] = np.clip(hsv[..., 2] + brightness_wave * strength, 0.0, 1.0)

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
