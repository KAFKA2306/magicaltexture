"""Example hair texture plugin demonstrating failure isolation."""

from __future__ import annotations

from typing import Any

from .base import FeaturePlugin


class HairTexturePlugin(FeaturePlugin):
    """Placeholder hair texture processor.

    The actual hair processing implementation is intentionally minimal to
    illustrate how experimental features can operate independently from the
    stable eye-processing core.
    """

    def __init__(self) -> None:
        self._dependencies_ready = self._check_dependencies()

    def _check_dependencies(self) -> bool:
        try:  # pragma: no cover - optional dependency check
            import cv2  # noqa: F401
            import numpy  # noqa: F401
        except Exception:
            return False
        return True

    # ------------------------------------------------------------------
    # FeaturePlugin implementations
    # ------------------------------------------------------------------
    def health_check(self) -> bool:  # pragma: no cover - trivial
        return self._dependencies_ready

    def process(self, hair_image: Any, color_scheme: Any) -> Any:
        if not self._dependencies_ready:
            return self.fallback_process(hair_image)
        # Real processing would go here; return input for now
        return hair_image

    def fallback_process(self, hair_image: Any, *_: Any, **__: Any) -> Any:
        """Return original image when processing is unavailable."""
        return hair_image
