"""Plugin package for optional features.

Currently includes a placeholder :class:`HairTexturePlugin` demonstrating the
expected interface.
"""

from .base import FeaturePlugin
from .hair import HairTexturePlugin

__all__ = ["FeaturePlugin", "HairTexturePlugin"]
