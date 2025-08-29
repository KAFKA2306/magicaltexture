"""Base classes for optional feature plugins.

Plugins inherit from :class:`FeaturePlugin` and implement the
:py:meth:`process`, :py:meth:`health_check` and :py:meth:`fallback_process`
methods.  The :py:meth:`run` helper provides a safe execution wrapper that
falls back to :py:meth:`fallback_process` when dependencies are missing or
when the plugin raises an exception.

This design allows experimental features to be added without risking the
stability of the core application – if a plugin fails, the core behaviour
continues unaffected.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class FeaturePlugin(ABC):
    """Abstract base class for optional feature plugins."""

    @abstractmethod
    def process(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the plugin's main behaviour."""

    @abstractmethod
    def health_check(self) -> bool:
        """Return ``True`` if the plugin is ready to run."""

    @abstractmethod
    def fallback_process(self, *args: Any, **kwargs: Any) -> Any:
        """Fallback behaviour when processing fails."""

    def log_error(self, error: Exception) -> None:
        """Basic error logger. Plugins may override for custom logging."""
        print(f"{self.__class__.__name__} error: {error}")

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Safely execute the plugin.

        If :py:meth:`health_check` fails or :py:meth:`process` raises an
        exception, this method returns the result of
        :py:meth:`fallback_process` instead of propagating errors to the
        caller.
        """

        if not self.health_check():
            return self.fallback_process(*args, **kwargs)

        try:
            return self.process(*args, **kwargs)
        except Exception as exc:  # pragma: no cover - simple pass through
            self.log_error(exc)
            return self.fallback_process(*args, **kwargs)
