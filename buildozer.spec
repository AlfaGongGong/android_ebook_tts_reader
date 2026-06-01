[app]

# App metadata
title = Ebook TTS Reader
package.name = ebookttsreader
package.domain = org.alfagonggong

# Source
source.dir = .
source.include_exts = py,kv,png,jpg,atlas,json
source.exclude_dirs = tests,data/cache,.venv,venv,__pycache__,.git,.buildozer

version = 0.2.0

# ─── Requirements ──────────────────────────────────────────────────────────────
# Core runtime requirements for the Android build.
# Edge TTS runs as an online service, so the Android package keeps only the
# lightweight app/runtime dependencies here. INTERNET permission is required
# for synthesis.
requirements = python3,kivy==2.3.0,pyjnius,plyer,ebooklib,beautifulsoup4,lxml,platformdirs

# ─── Display ───────────────────────────────────────────────────────────────────
orientation = portrait
fullscreen = 0

# ─── Android ───────────────────────────────────────────────────────────────────
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET,MANAGE_EXTERNAL_STORAGE

# Target API 33 (Android 13).  Minimum API 24 (Android 7).
android.api = 33
android.minapi = 24

# NDK version (r25b is stable and well-tested with Buildozer 1.5+)
android.ndk = 25b
android.ndk_api = 24

# Accept the Android SDK licence automatically in CI
android.accept_sdk_license = True

# Build for 64-bit ARM (arm64-v8a) which covers most modern devices.
# Add armeabi-v7a for older 32-bit devices if needed.
android.archs = arm64-v8a

# Entry point
android.entrypoint = org.kivy.android.PythonActivity

# ─── Buildozer ─────────────────────────────────────────────────────────────────
[buildozer]
log_level = 2
warn_on_root = 1
