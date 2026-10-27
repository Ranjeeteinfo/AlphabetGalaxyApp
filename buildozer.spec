
[app]

# Android par app ka display name
# title = My KivyMD App

# Package ID ke do parts:
# package.domain = in.reteco
# package.name = mykivymdapp
# Final ID = in.reteco.mykivymdapp
# package.name = mykivymdapp
# package.domain = in.reteco

title = Alphabet Galaxy
package.name = alphabetgalaxy
package.domain = com.reteco

# App version; main.py mein __version__ bhi maintain karein.
version = 1.0.0

# Android build mein include hone wali files
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,atlas,ttf,json
source.include_patterns = assets/*,assets/audio/*,assets/audio/letters/*
source.exclude_dirs = tools,bin,.buildozer,.github,venv,__pycache__


# Android dependencies.
# Yeh requirements.txt se alag setting hai.
# requirements = python3,kivy,kivymd

requirements = python3,kivy==2.3.1,kivymd==1.0.2,plyer

# Minimum Android API
# android.minapi = 24

# Native compilation API
# android.ndk_api = 24

# Python-for-Android ka updated development branch
p4a.branch = develop

# App screen settings
orientation = portrait
fullscreen = 0

# Internet permission tab rakhein jab app ko zaroorat ho.
android.permissions = INTERNET

# Supported Android API levels


# Device CPU architectures
# android.archs = arm64-v8a, armeabi-v7a

# Android SDK licenses accept karne ki setting
# android.accept_sdk_license = True

# Build output formats
android.debug_artifact = apk
android.release_artifact = aab

[buildozer]

# Build logs ki detail
log_level = 2

# Root user par build warning
warn_on_root = 1


# minapi 21 = Android 5.0+ ; 64-bit and 32-bit phones/tablets are both built.
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True
android.logcat_filters = *:S python:D
