"""Alphabet Galaxy 3D - app entry point (navigation, settings, lifecycle)."""
import os
import traceback

from kivy.base import ExceptionHandler, ExceptionManager
from kivy.core.window import Window
from kivy.uix.screenmanager import FadeTransition, ScreenManager
from kivy.utils import get_color_from_hex as hexc, platform
from kivymd.app import MDApp

import ui
from audio import AudioManager
from data import level_config, mission_config
from progress import ProgressManager
from screens import (GameScreen, HomeScreen, LettersScreen, LevelsScreen, ProgressScreen,
                     SettingsScreen, SummaryScreen)


class CrashGuard(ExceptionHandler):
    """Writes unexpected errors to crash.log and keeps the game running instead of closing it."""
    path, count = None, 0

    def handle_exception(self, inst):
        CrashGuard.count += 1
        try:
            if CrashGuard.path and (not os.path.exists(CrashGuard.path) or os.path.getsize(CrashGuard.path) < 200000):
                with open(CrashGuard.path, 'a') as f:
                    f.write(''.join(traceback.format_exception(type(inst), inst, inst.__traceback__)) + '\n')
        except Exception:
            pass
        # a one-off glitch is ignored; an error that repeats every frame is allowed to stop the app
        return ExceptionManager.PASS if CrashGuard.count < 25 else ExceptionManager.RAISE


class AlphabetGalaxyApp(MDApp):
    def build(self):
        self.title = 'Alphabet Galaxy'
        CrashGuard.path = os.path.join(self.user_data_dir, 'crash.log')
        ExceptionManager.add_handler(CrashGuard())
        self.theme_cls.theme_style = 'Dark'
        Window.clearcolor = hexc(ui.NAVY)
        self.progress = ProgressManager(os.path.join(self.user_data_dir, 'alphabet_galaxy.json'))
        self.audio = AudioManager(self.progress)
        ui.HOOKS['click'] = lambda: self.audio.play('click', gap=.05, volume=.6)

        self.sm = ScreenManager(transition=FadeTransition(duration=.18))
        self.game = GameScreen(self, name='game')
        for screen in (HomeScreen(self, name='home'), self.game,
                       LettersScreen(self, 'learn', name='learn'),
                       LettersScreen(self, 'mission', name='missions'),
                       LevelsScreen(self, name='levels'), ProgressScreen(self, name='progress'),
                       SettingsScreen(self, name='settings'), SummaryScreen(self, name='summary')):
            self.sm.add_widget(screen)
        Window.bind(on_keyboard=self.on_key)
        self.audio.music()  # only plays if the player enabled music
        return self.sm

    # ---- navigation ----
    def go(self, name):
        self.sm.current = name

    def start(self, cfg):
        self.game.cfg = cfg
        self.go('game')

    def start_level(self, n):
        self.start(level_config(n))

    def start_mission(self, letter):
        self.start(mission_config(letter))

    def restart(self, cfg):
        self.start_level(cfg['level']) if cfg['kind'] == 'level' else self.start_mission(cfg['letter'])

    def play_next(self):
        self.start_level(self.progress.next_level())

    def show_summary(self, cfg, res):
        self.sm.get_screen('summary').show(cfg, res)
        self.go('summary')

    def set_setting(self, key, value):
        self.progress.set_setting(key, value)
        if key == 'music':
            self.audio.music()

    # ---- Android lifecycle ----
    def on_key(self, window, key, *a):
        if key == 27:  # back button
            if self.sm.current == 'game':
                if self.game.overlay and not self.game.done:
                    self.game.resume_game()
                else:
                    self.game.pause_game()
                return True
            if self.sm.current != 'home':
                self.go('home')
                return True
        return False

    def on_pause(self):
        self.progress.save()
        self.audio.stop_music()
        if self.sm.current == 'game':
            self.game.pause_game()
        return True

    def on_resume(self):
        self.audio.music()

    def on_stop(self):
        self.game.world.cleanup()
        self.progress.save()
        self.audio.unload()


if __name__ == '__main__':
    if platform not in ('android', 'ios'):
        Window.size = (390, 780)  # portrait phone-shaped window for desktop testing
    AlphabetGalaxyApp().run()
