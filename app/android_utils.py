"""Android-specific helpers: permission requests and file picker.

Platform detection
------------------
``is_android()`` checks for the ``android`` module that is only present
when the app is packaged by Buildozer / python-for-android.

Permissions
-----------
On Android API ≤ 32 the legacy ``READ_EXTERNAL_STORAGE`` permission is used.
On API 33+ the more granular ``READ_MEDIA_AUDIO`` / ``READ_MEDIA_VIDEO`` /
``READ_MEDIA_IMAGES`` permissions are needed; this module requests all of them
so books on external storage are reachable regardless of API level.
On non-Android platforms the call is a no-op.

File picker
-----------
``open_file_picker`` uses **plyer**'s ``filechooser`` which:
  * on desktop Linux/macOS/Windows opens a native OS file dialog
  * on Android (API < 30) opens an ``Intent.ACTION_GET_CONTENT`` dialog

Limitation: on Android 11+ with scoped storage, some paths returned by the
file picker may be content:// URIs that need to be resolved before use.
A best-effort path extraction is attempted; if resolution fails the raw URI
string is passed to the caller so it can handle or display it.
"""

from __future__ import annotations

import logging
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


def is_android() -> bool:
    """Return ``True`` when running inside a Buildozer/p4a Android package."""
    try:
        import android  # type: ignore  # noqa: F401
        return True
    except Exception:
        return False


def request_storage_permissions(callback: Optional[Callable[[bool], None]] = None) -> None:
    """Request storage / media-read permissions on Android.

    On non-Android platforms this is a no-op that immediately calls *callback*
    with ``True``.
    """
    if not is_android():
        if callback:
            callback(True)
        return

    try:
        from android.permissions import (  # type: ignore
            Permission,
            request_permissions,
            check_permission,
        )

        perms = [Permission.READ_EXTERNAL_STORAGE]
        # API 33+ granular media permissions (harmless to add on older versions)
        for attr in ("READ_MEDIA_AUDIO", "READ_MEDIA_VIDEO", "READ_MEDIA_IMAGES"):
            p = getattr(Permission, attr, None)
            if p:
                perms.append(p)

        def _on_permissions(permissions: List[str], grants: List[bool]) -> None:
            granted = all(grants)
            logger.info("Storage permissions granted: %s", granted)
            if callback:
                callback(granted)

        request_permissions(perms, _on_permissions)
    except Exception as exc:
        logger.warning("Could not request Android permissions: %s", exc)
        if callback:
            callback(False)


def open_file_picker(
    on_selection: Callable[[List[str]], None],
    filters: Optional[List[str]] = None,
) -> None:
    """Open a platform-native file picker for ebook files.

    *on_selection* is called with a list of selected file paths (may be empty
    if the user cancels).  The call is asynchronous on Android.

    Filters example: ``["*.epub", "*.txt"]``
    """
    _filters = filters or ["*.epub", "*.txt"]

    try:
        from plyer import filechooser  # type: ignore

        def _on_sel(selection: List[str]) -> None:
            resolved = [_resolve_uri(p) for p in (selection or [])]
            on_selection([p for p in resolved if p])

        filechooser.open_file(
            on_selection=_on_sel,
            filters=_filters,
            title="Select an ebook",
            multiple=False,
        )
    except Exception as exc:
        logger.warning("File picker unavailable: %s", exc)
        on_selection([])


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _resolve_uri(path: str) -> str:
    """Best-effort conversion of Android content:// URIs to real paths.

    If the path is already a regular filesystem path it is returned as-is.
    If resolution fails the original string is returned unchanged.
    """
    if not path.startswith("content://"):
        return path
    if not is_android():
        return path
    try:
        from jnius import autoclass  # type: ignore
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Uri = autoclass("android.net.Uri")
        uri = Uri.parse(path)
        cursor = PythonActivity.mActivity.getContentResolver().query(
            uri, None, None, None, None
        )
        if cursor and cursor.moveToFirst():
            idx = cursor.getColumnIndex("_data")
            if idx >= 0:
                real = cursor.getString(idx)
                cursor.close()
                if real:
                    return real
            cursor.close()
    except Exception as exc:
        logger.debug("URI resolution failed for %s: %s", path, exc)
    return path

