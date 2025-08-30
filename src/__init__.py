"""Magical Texture package.

This file exposes high level helpers and feature management tools used by the
application.  The core processing code lives in modules such as
:mod:`core` while optional functionality can be developed as plugins under
:mod:`plugins`.
"""

from .feature_manager import FeatureManager
from .plugins.base import FeaturePlugin

__all__ = ["FeatureManager", "FeaturePlugin"]
