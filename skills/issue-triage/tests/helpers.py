"""Test helpers shared across test modules."""

from __future__ import annotations

from datetime import datetime


class FrozenDatetime(datetime):
    """Datetime subclass with a frozen ``now()`` for deterministic tests.

    ``fromisoformat()`` and other constructors still work normally because
    we only override the class method ``now()``.
    """

    _frozen: datetime | None = None

    @classmethod
    def freeze(cls, dt: datetime) -> None:
        cls._frozen = dt

    @classmethod
    def now(cls, tz=None):  # noqa: ANN001
        if cls._frozen is not None:
            return cls._frozen
        return super().now(tz=tz)
