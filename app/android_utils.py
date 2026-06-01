"""Android-specific helpers and placeholders."""

from __future__ import annotations


def is_android() -> bool:
    try:
        import android  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False


def request_storage_permissions() -> bool:
    """Placeholder for runtime storage/media permissions.

    Future Android implementation should request the appropriate read permissions
    depending on Android API level and storage access strategy.
    """

    return True
