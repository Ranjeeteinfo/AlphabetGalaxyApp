[app]
title = Alphabet Galaxy
package.name = alphabetgalaxy
package.domain = org.kidsgames
source.dir = .
source.include_exts = py,png,webp,jpg,wav,ogg,mp3
source.include_patterns = assets/*,assets/audio/*,assets/audio/letters/*
source.exclude_dirs = tools,bin,.buildozer,.github,venv,__pycache__
version = 1.0.0

# Only what the game needs (all supported by python-for-android).
requirements = python3,kivy==2.3.1,kivymd==1.0.2,pillow


icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/presplash.png
android.presplash_color = #0B1033

orientation = portrait
fullscreen = 0

# The game is offline and saves into its private app folder, so it needs NO permissions.
# (Adding unused permissions only scares parents/app stores.)
# Optional - keep the screen awake while the app is open (uncomment both lines):
#   android.permissions = WAKE_LOCK
#   android.wakelock = True
android.permissions =

# minapi 21 = Android 5.0+ ; 64-bit and 32-bit phones/tablets are both built.
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
