"""AudioManager: loads local sounds lazily, ignores missing files, throttles repeats."""
import os
import time

from kivy.core.audio import SoundLoader

AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'audio')


class AudioManager:
    def __init__(self, progress):
        self.p = progress
        self.cache, self.last = {}, {}

    def _get(self, rel):
        """Sound for assets/audio/<rel>.(ogg|wav|mp3), or None if it does not exist."""
        if rel not in self.cache:
            snd = None
            for ext in ('.ogg', '.wav', '.mp3'):
                path = os.path.join(AUDIO_DIR, rel + ext)
                if os.path.exists(path):
                    try:
                        snd = SoundLoader.load(path)
                    except Exception:
                        snd = None
                    break
            self.cache[rel] = snd
        return self.cache[rel]

    def play(self, name, gap=0.0, volume=1.0):
        if not self.p.setting('sfx'):
            return
        now = time.monotonic()
        if now - self.last.get(name, -99.0) < gap:
            return  # keeps the laser from becoming annoying
        snd = self._get(name)
        if snd:
            self.last[name] = now
            snd.volume = volume
            snd.stop()
            snd.play()

    def say(self, letter):
        """Optional pronunciation: assets/audio/letters/<a-z>.(ogg|wav|mp3)."""
        if self.p.setting('voice'):
            snd = self._get('letters/' + letter.lower())
            if snd:
                snd.stop()
                snd.play()

    def music(self):
        """Start or stop the background loop to match the current setting."""
        snd = self._get('music')
        if not snd:
            return
        if self.p.setting('music'):
            if snd.state != 'play':
                snd.loop = True
                snd.volume = 0.3
                snd.play()
        else:
            snd.stop()

    def stop_music(self):
        snd = self._get('music')
        if snd:
            snd.stop()

    def unload(self):
        for snd in self.cache.values():
            if snd:
                snd.stop()
                snd.unload()
        self.cache.clear()
