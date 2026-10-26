# Alphabet Galaxy 3D

Portrait Android space shooter for learning A-Z (ages 3-7). Drag anywhere to fly the ship;
lasers fire automatically. Python + Kivy 2.3.1 + KivyMD 1.2.0, fully offline.

## Project structure
```
AlphabetGalaxy/
├── main.py            AlphabetGalaxyApp: screens, navigation, settings, Android lifecycle
├── screens.py         HomeScreen, LettersScreen (Learn A-Z / Mission mode), LevelsScreen,
│                      ProgressScreen, SettingsScreen, GameScreen (HUD + overlays), SummaryScreen
├── game.py            GameWorld: canvas play field, touch drag, auto-fire, collisions, spawning
├── sprites.py         Spaceship, AlphabetTarget, LaserProjectile, ParticleEffect
├── ui.py              Shared widgets: auto-fit labels, 3D buttons, starfield, space background
├── audio.py           AudioManager (SoundLoader, missing files ignored, laser throttled)
├── progress.py        ProgressManager (JSON save, corruption-safe)
├── data.py            Letters, words, planets/levels, badges (add new planets/modes here)
├── requirements.txt   Desktop dependencies
├── buildozer.spec     Android packaging
├── tools/make_sounds.py   Regenerates the placeholder sounds
├── tools/make_icon.py     Regenerates assets/icon.png + presplash.png
├── assets/audio/      Sounds (see assets/README.txt)
└── .github/workflows/build.yml   Debug APK build
```

## Run on Windows
```
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
A phone-shaped portrait window opens. Drag with the mouse to move the ship.
(Optional) `python tools/make_sounds.py` regenerates the sounds.

## Build the APK with GitHub Actions
1. Create a GitHub repository and push this whole folder (including the hidden `.github` folder) to `main`.
2. Open the repo's **Actions** tab -> **Build Android APK** -> **Run workflow** (pushes to `main` also start it).
3. First build takes 25-40 minutes (later ones are faster thanks to caching).
4. Open the finished run -> **Artifacts** -> download **AlphabetGalaxy-apk**, unzip, copy the `.apk` to your phone and install it (allow "install unknown apps").

Buildozer does not run natively on Windows; use GitHub Actions (or WSL2/Linux).

## How the game works
* Drag anywhere (below the top HUD strip) -> ship follows your finger horizontally; release -> it stops, firing continues.
* Mission: "HIT LETTER B". Correct hit = points + "B is for Ball!"; wrong letter = friendly hint, no penalty.
* A life is lost only when the required letter floats away. 3 lives; stars = lives left (1-3).
* 6 planets (levels) unlock one after another; Mission mode practises any single letter.

## Permissions
The game needs **no Android permissions** (offline, saves inside its private app folder, no camera/mic/storage).
Adding unused permissions would only make the install screen look scary, so none are requested.
Optional: to keep the screen awake while the app is open, uncomment the two `WAKE_LOCK` lines in `buildozer.spec`.

## Made to run on every device
* Android 5.0+ (`minapi 21`), 64-bit and 32-bit builds (`arm64-v8a`, `armeabi-v7a`).
* Layout scales from the screen's short side: small phones, big phones, tablets and landscape all work.
* Weak phones: if frames stay slow for 2 seconds the game switches itself to "lite" mode (fewer sparkles, lighter stars).
* If an unexpected error happens the game keeps running and writes it to `crash.log` in the app's data folder
  (an error that repeats every frame is allowed to stop the app so it never freezes silently).
* Back button pauses the game / returns to Home; locking the phone pauses and saves.

## Getting the APK onto a phone (no PC tools needed)
1. Unzip `AlphabetGalaxy.zip` and upload the folder contents to a new GitHub repo (keep the hidden `.github` folder - with
   GitHub Desktop or `git push` this is automatic; on the website drag the whole folder into "Upload files").
2. Actions -> **Build Android APK** -> Run workflow. Wait ~30 minutes.
3. Download artifact **AlphabetGalaxy-apk**, unzip, open the `.apk` on the phone, allow "Install unknown apps", install.
4. If the build fails, download the **build-log** artifact and check the last 50 lines.

## Troubleshooting
| Problem | Fix |
|---|---|
| `ModuleNotFoundError: kivymd` | `pip install -r requirements.txt` inside the activated venv. |
| Kivy fails to install on new Python | Use Python 3.10-3.12 (Kivy 2.3.1 wheels). |
| Black window on old PC / VM | Set `KIVY_GL_BACKEND=angle_sdl2` (Windows) before `python main.py`. |
| No sound | Settings -> Sound effects ON; check files exist in `assets/audio/`; on desktop install a working audio device. Music is OFF by default. |
| No letter voice | Voice files are not bundled - add `assets/audio/letters/a.ogg ... z.ogg`. |
| MDLabel text size looks odd | Text size is set by `fit()` in `ui.py`; tweak `BASE_SP` there. |
| APK build: `Cython`/`pyjnius` errors | Keep `cython==0.29.36` in the workflow; clear cache (Actions -> Caches) and re-run. |
| APK build: SDK/NDK/licence errors | Keep `android.api = 33`, `android.ndk = 25b`, `android.accept_sdk_license = True`. |
| APK build: `libtinfo5`/`libncurses` missing | Already installed in the workflow's apt step. |
| App closes at start on phone | Run `adb logcat -s python` and read the traceback; most often a version mismatch of kivy/kivymd in `buildozer.spec`. |
| Progress lost | It is saved in the app's private data dir; "Reset progress" in Settings clears it (two taps). |
