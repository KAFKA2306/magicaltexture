"""Simple feature flag system for experimental plugins.

The manager allows features to be enabled/disabled globally and also supports
per-user-group controls.  It is intentionally lightweight so that optional
features can be rolled out gradually without risking the stability of the
application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class FeatureManager:
    """Manage feature flags and user group visibility."""

    feature_flags: Dict[str, bool] = field(
        default_factory=lambda: {
            "core_eye_processing": True,
            "hair_texture": False,
            "ai_generation": False,
        }
    )
    user_group_flags: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "beta_users": ["hair_texture"],
            "alpha_users": ["hair_texture", "ai_generation"],
            "staff": ["all"],
        }
    )

    def is_feature_enabled(self, feature_name: str, user_group: str = "normal") -> bool:
        """Return ``True`` when ``feature_name`` is enabled for ``user_group``."""
        if not self.feature_flags.get(feature_name, False):
            return False
        if user_group == "staff":
            return True
        allowed = self.user_group_flags.get(user_group)
        if allowed is None:
            # Unknown groups inherit globally enabled features
            return True
        return feature_name in allowed or "all" in allowed
