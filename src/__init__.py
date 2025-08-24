# __init__.py
# Package initialization for Magical Texture

from .core import (
    load_rgba, load_mask, rgb_to_hsv_np, hsv_to_rgb_np, mask_centroid,
    apply_basic, apply_gradient, apply_aurora, build_emission
)
from .config import PASTELS, PRETTY, COLOR_DESCRIPTIONS, EFFECT_DESCRIPTIONS
from .generators import generate_single, generate_batch
from .ui import create_ui

__all__ = [
    'load_rgba', 'load_mask', 'rgb_to_hsv_np', 'hsv_to_rgb_np', 'mask_centroid',
    'apply_basic', 'apply_gradient', 'apply_aurora', 'build_emission',
    'PASTELS', 'PRETTY', 'COLOR_DESCRIPTIONS', 'EFFECT_DESCRIPTIONS',
    'generate_single', 'generate_batch', 'create_ui'
]