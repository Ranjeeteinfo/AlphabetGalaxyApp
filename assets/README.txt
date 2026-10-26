ASSETS
======
assets/audio/            Sound effects and music (loaded by audio.py, all optional)
  laser.wav click.wav correct.wav wrong.wav level.wav   short effects  (included)
  music.wav                                             8 s loop       (included, OFF by default)
  letters/a.ogg ... z.ogg                               letter pronunciation (NOT included)

The included .wav files are simple synthesized tones made by tools/make_sounds.py
(re-run it to regenerate). Replace any of them with your own recordings: keep the
same file name; .ogg, .wav and .mp3 all work (checked in that order).

Pronunciation: no voice recordings are bundled. Put your own files at
assets/audio/letters/a.ogg, b.ogg ... z.ogg (short, 1 second or less). Until you do,
"Letter voice" simply stays silent - nothing breaks. Keep files small (.ogg, mono).

There are no image files: ship, letters, planets and effects are drawn with Kivy canvas
instructions, so the APK stays small and nothing is downloaded at runtime.
