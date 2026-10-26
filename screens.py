"""Menu screens, the game screen (HUD + overlays) and the mission summary."""
import math

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import InstructionGroup
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hexc

from data import BADGES, LETTERS, PLANETS, WORDS, letter_color
from game import GameWorld
from sprites import Spaceship
from ui import (CYAN, GLASS, GOLD, LAV, MAX_W, MINT, NAVY, PINK, Bar, Disc, Hearts, LetterBadge,
                Overlay, Pad, S, SpaceBg, StarIcon, Tap, Toggle, btn, lbl, scroll_grid, shadow_title)

OFF = '#5A5E8F'


def count_row():
    """Star icon + number."""
    row = BoxLayout(size_hint=(None, None), size=(S(110), S(44)), spacing=S(4))
    row.add_widget(StarIcon(size_hint=(None, 1), width=S(40)))
    row.lab = lbl('0', 'H5', halign='left')
    row.add_widget(row.lab)
    return row


def header(app, title):
    row = BoxLayout(size_hint_y=None, height=S(52), spacing=S(8))
    row.add_widget(btn('Back', MINT, lambda: app.go('home'), 'H6', size_hint=(None, 1), width=S(90)))
    row.add_widget(lbl(title, 'H5'))
    row.add_widget(Widget(size_hint_x=None, width=S(90)))
    return row


def settings_rows(app):
    """Sound / music / voice switches (used by Settings and the pause menu)."""
    rows = []
    for key, text in (('sfx', 'Sound effects'), ('music', 'Music'), ('voice', 'Letter voice')):
        row = BoxLayout(size_hint_y=None, height=S(46), spacing=S(8))
        row.add_widget(lbl(text, 'H6', halign='left'))
        row.add_widget(Toggle(active=app.progress.setting(key), pos_hint={'center_y': .5},
                              on_change=lambda v, k=key: app.set_setting(k, v)))
        rows.append(row)
    return rows


class MenuScreen(Screen):
    """Animated space background + a centred content column."""
    theme = 0

    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self.bg = SpaceBg(self.theme)
        self.add_widget(self.bg)
        self.frame = BoxLayout(orientation='vertical', size_hint=(None, 1), pos_hint={'center_x': .5},
                               padding=S(14), spacing=S(10))
        self.bg.bind(width=lambda b, w: setattr(self.frame, 'width', min(w, dp(MAX_W))))
        self.add_widget(self.frame)

    def on_pre_enter(self, *a):
        self.bg.start()
        self.refresh()

    def on_leave(self, *a):
        self.bg.stop()

    def refresh(self):
        pass


class ShipWidget(Widget):
    """The cartoon ship, bobbing gently (home screen mascot)."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.layer = InstructionGroup()
        self.canvas.add(self.layer)
        self.ship = Spaceship(self.layer)
        self.bob = 0.0
        self.bind(pos=self.redraw, size=self.redraw)
        self.ev = None

    def redraw(self, *a):
        if self.height < 2:
            return
        u = self.height * .27
        if abs(u - self.ship.u) > .5:
            self.ship.build(u)
        self.ship.update(self.center_x, self.center_y + self.bob * u * .18, self.bob * 4,
                         Clock.get_boottime(), 0)

    def start(self):
        if not self.ev:
            self.ev = Clock.schedule_interval(self.tick, 1 / 30)

    def stop(self):
        if self.ev:
            self.ev.cancel()
            self.ev = None

    def tick(self, dt):
        self.bob = math.sin(Clock.get_boottime() * 2.2)
        self.redraw()


class HomeScreen(MenuScreen):
    def __init__(self, app, **kw):
        super().__init__(app, **kw)
        f = self.frame
        top = BoxLayout(size_hint_y=None, height=S(44))
        top.add_widget(Widget())
        self.stars = count_row()
        top.add_widget(self.stars)
        f.add_widget(top)
        f.add_widget(shadow_title('ALPHABET', GOLD, size_hint_y=.12))
        f.add_widget(shadow_title('GALAXY', CYAN, size_hint_y=.12))
        self.ship = ShipWidget(size_hint_y=.2)
        f.add_widget(self.ship)
        f.add_widget(btn('PLAY', PINK, app.play_next, 'H3', size_hint_y=.13))
        for a, b in ((('Learn A-Z', CYAN, lambda: app.go('learn')), ('Mission Mode', LAV, lambda: app.go('missions'))),
                     (('Levels', GOLD, lambda: app.go('levels')), ('Progress', MINT, lambda: app.go('progress')))):
            row = BoxLayout(spacing=S(10), size_hint_y=.1)
            for text, col, cb in (a, b):
                row.add_widget(btn(text, col, cb, 'H6'))
            f.add_widget(row)
        f.add_widget(btn('Settings', '#B9C2FF', lambda: app.go('settings'), 'H6', size_hint_y=.08))

    def refresh(self):
        self.stars.lab.text = str(self.app.progress.total_stars)

    def on_pre_enter(self, *a):
        super().on_pre_enter(*a)
        self.ship.start()

    def on_leave(self, *a):
        super().on_leave(*a)
        self.ship.stop()


class LettersScreen(MenuScreen):
    """mode='learn': tap a letter to see/hear it.  mode='mission': tap a letter to practise it."""

    def __init__(self, app, mode, **kw):
        super().__init__(app, **kw)
        self.mode = mode
        f = self.frame
        f.add_widget(header(app, 'Learn A-Z' if mode == 'learn' else 'Mission Mode'))
        if mode == 'learn':
            card = Pad(orientation='horizontal', size_hint_y=.28, spacing=S(10))
            self.badge = LetterBadge('A', mult=3.4, size_hint_x=.4)
            col = BoxLayout(orientation='vertical')
            self.word = lbl('', 'H5')
            self.lower = lbl('', 'H4', CYAN)
            col.add_widget(self.word)
            col.add_widget(self.lower)
            card.add_widget(self.badge)
            card.add_widget(col)
            f.add_widget(card)
            self.show_letter('A')
        else:
            f.add_widget(lbl('Pick a letter to practise!', 'H6', size_hint_y=None, height=S(36)))
        sv, self.grid = scroll_grid(76, 84)
        f.add_widget(sv)

    def show_letter(self, l):
        self.badge.set(l)
        self.word.text = '%s is for %s' % (l, WORDS[l])
        self.lower.text = '%s %s' % (l, l.lower())

    def pick(self, l):
        if self.mode == 'mission':
            self.app.start_mission(l)
            return
        self.show_letter(l)
        self.app.audio.say(l)
        if self.app.progress.add_viewed(l):
            self.refresh()

    def refresh(self):
        p = self.app.progress.data
        self.grid.clear_widgets()
        for l in LETTERS:
            seen = p['letters'].get(l, 0) > 0 if self.mode == 'mission' else l in p['viewed']
            tile = Tap(bg=letter_color(l), radius=20, orientation='vertical',
                       on_release=lambda inst, l=l: self.pick(l))
            tile.add_widget(lbl(l, 'H4', NAVY))
            tile.add_widget(StarIcon(size_hint_y=.3, color=[1, 1, 1, 1] if seen else [1, 1, 1, 0]))
            self.grid.add_widget(tile)


class LevelsScreen(MenuScreen):
    def __init__(self, app, **kw):
        super().__init__(app, **kw)
        self.frame.add_widget(header(app, 'Choose a Planet'))
        sv = ScrollView(do_scroll_x=False)
        self.box = BoxLayout(orientation='vertical', spacing=S(10), size_hint_y=None, padding=S(4))
        self.box.bind(minimum_height=self.box.setter('height'))
        sv.add_widget(self.box)
        self.frame.add_widget(sv)

    def refresh(self):
        self.box.clear_widgets()
        p = self.app.progress
        for n, pl in enumerate(PLANETS, 1):
            ok = p.is_unlocked(n)
            card = Tap(bg=GLASS if ok else '#2A2D55AA', orientation='horizontal', size_hint_y=None,
                       height=S(92), spacing=S(10), on_release=lambda inst, n=n: self.pick(n))
            card.add_widget(Disc(color=hexc(pl['body']) if ok else [.5, .52, .65, 1], ring=(n % 2 == 0),
                                 size_hint_x=None, width=S(70)))
            col = BoxLayout(orientation='vertical')
            col.add_widget(lbl('%d. %s' % (n, pl['name']), 'H6', halign='left'))
            letters = ('Letters %s - %s' % (pl['letters'][0], pl['letters'][-1])) if pl['letters'] else 'Mixed letters'
            col.add_widget(lbl(letters, 'Subtitle1', CYAN, bold=False, halign='left'))
            card.add_widget(col)
            if ok:
                stars = p.level_stars(n)
                row = BoxLayout(size_hint_x=None, width=S(84))
                for i in range(3):
                    row.add_widget(StarIcon(color=[1, .85, .3, 1] if i < stars else [.45, .48, .7, .7]))
                card.add_widget(row)
            else:
                card.add_widget(lbl('Locked', 'Subtitle1', '#AEB4E0', size_hint_x=None, width=S(70)))
            self.box.add_widget(card)

    def pick(self, n):
        if self.app.progress.is_unlocked(n):
            self.app.start_level(n)


class ProgressScreen(MenuScreen):
    def __init__(self, app, **kw):
        super().__init__(app, **kw)
        f = self.frame
        f.add_widget(header(app, 'My Progress'))
        self.stats = GridLayout(cols=2, spacing=S(8), size_hint_y=None, height=S(150))
        f.add_widget(self.stats)
        f.add_widget(lbl('Badges', 'H5', GOLD, size_hint_y=None, height=S(34)))
        sv, self.grid = scroll_grid(150, 130)
        f.add_widget(sv)

    def refresh(self):
        p = self.app.progress
        d = p.data
        self.stats.clear_widgets()
        for value, text in ((d['high_score'], 'High score'), (p.total_stars, 'Stars'),
                            (d['points'], 'Total points'), ('%d / 26' % p.letters_learned(), 'Letters learned')):
            card = Pad(orientation='vertical')
            card.add_widget(lbl(str(value), 'H4', GOLD))
            card.add_widget(lbl(text, 'Subtitle1', bold=False))
            self.stats.add_widget(card)
        self.grid.clear_widgets()
        for bid, name, desc, col in BADGES:
            ok = bid in d['badges']
            card = Pad(orientation='vertical')
            card.add_widget(Disc(color=hexc(col) if ok else [.4, .42, .6, .8], size_hint_y=.45))
            card.add_widget(lbl(name, 'Subtitle1', GOLD if ok else '#AEB4E0', size_hint_y=.25))
            card.add_widget(lbl(desc, 'Caption', bold=False, size_hint_y=.3))
            self.grid.add_widget(card)


class SettingsScreen(MenuScreen):
    def __init__(self, app, **kw):
        super().__init__(app, **kw)
        f = self.frame
        f.add_widget(header(app, 'Settings'))
        self.rows = BoxLayout(orientation='vertical', spacing=S(6), size_hint_y=None, height=S(150))
        card = Pad(orientation='vertical', size_hint_y=None, height=S(190))
        card.add_widget(self.rows)
        f.add_widget(card)
        f.add_widget(lbl('Music is OFF by default.\nSound files live in assets/audio/', 'Subtitle1',
                         bold=False, size_hint_y=None, height=S(60)))
        self.reset = btn('Reset progress', '#FFB3C1', self.on_reset, 'H6', size_hint_y=None, height=S(60))
        f.add_widget(self.reset)
        f.add_widget(Widget())
        self.armed = False

    def refresh(self):
        self.rows.clear_widgets()
        for r in settings_rows(self.app):
            self.rows.add_widget(r)
        self.armed = False
        self.reset.lab.text = 'Reset progress'

    def on_reset(self):
        if not self.armed:  # two taps needed, so children cannot wipe progress by accident
            self.armed = True
            self.reset.lab.text = 'Tap again to confirm'
            return
        self.app.progress.reset()
        self.refresh()
        self.reset.lab.text = 'Progress reset!'


# ----------------------------------------------------------------- game --
class GameScreen(Screen):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app, self.cfg, self.overlay, self._ev, self.done = app, None, None, None, True
        self.world = GameWorld()
        self.add_widget(self.world)
        w = self.world
        w.on_correct, w.on_wrong, w.on_miss = self.on_correct, self.on_wrong, self.on_miss
        w.on_fire = lambda: app.audio.play('laser', gap=.22, volume=.5)

        # HUD: kept in the top strip, away from the drag area
        self.hud = Pad(bg=GLASS, radius=22, orientation='vertical', size_hint=(None, None),
                       pos_hint={'center_x': .5, 'top': .99}, padding=[S(10), S(8), S(10), S(12)], spacing=S(2))
        r1 = BoxLayout(size_hint_y=None, height=S(44), spacing=S(8))
        r1.add_widget(btn('II', GOLD, self.pause_game, 'H5', size_hint=(None, 1), width=S(44)))
        mission = BoxLayout(spacing=S(6))
        mission.add_widget(lbl('MISSION: HIT LETTER', 'H6', halign='right'))
        self.badge = LetterBadge('A', size_hint=(None, 1), width=S(44))
        mission.add_widget(self.badge)
        r1.add_widget(mission)
        self.snd = btn('Sound', MINT, self.toggle_sound, 'Subtitle1', size_hint=(None, 1), width=S(66))
        r1.add_widget(self.snd)
        r2 = BoxLayout(size_hint_y=None, height=S(28))
        self.score_l = lbl('Score 0', 'Subtitle1', halign='left', size_hint_x=.4)
        self.level_l = lbl('', 'Subtitle1', size_hint_x=.3)
        self.hearts = Hearts(size_hint_x=None, width=S(96))
        for x in (self.score_l, self.level_l, self.hearts):
            r2.add_widget(x)
        self.bar = Bar(size_hint_y=None, height=S(10))
        for x in (r1, r2, self.bar):
            self.hud.add_widget(x)
        self.add_widget(self.hud)

        self.banner = Pad(bg=GOLD, radius=24, size_hint=(.92, None), height=S(60), opacity=0,
                          pos_hint={'center_x': .5, 'center_y': .63})
        self.msg = lbl('', 'H5', NAVY)
        self.banner.add_widget(self.msg)
        self.add_widget(self.banner)
        self.bind(size=self.layout_hud)

    def layout_hud(self, *a):
        self.hud.width = min(self.width - S(16), dp(MAX_W))
        self.hud.height = S(108)
        self.world.hud_h = self.hud.height + S(14)

    # ---- session ----
    def on_enter(self, *a):
        if self.cfg:
            self.begin()

    def on_leave(self, *a):
        self.world.pause()
        self.clear_overlay()
        if self._ev:
            self._ev.cancel()
        self.done = True

    def ntargets(self):
        return min(self.cfg['max_targets'], 2 + self.i // 2)

    def begin(self):
        c = self.cfg
        self.done = False
        self.i = self.score = self.hits = self.wrong = self.misses = self.streak = self.best = 0
        self.lives, self.hit_letters = c['lives'], []
        self.world.reset(c['theme'])
        self.world.configure(c['pool'], c['speed'], self.ntargets())
        self.world.set_required(c['missions'][0])
        self.world.seed_wave(self.ntargets())
        self.badge.set(c['missions'][0])
        self.hearts.total = c['lives']
        self.update_hud()
        self.sound_btn()
        self.show_intro()

    def update_hud(self):
        c = self.cfg
        self.score_l.text = 'Score %d' % self.score
        self.level_l.text = ('Level %d' % c['level']) if c['kind'] == 'level' else c['name']
        self.hearts.value = self.lives
        self.bar.value = self.i / len(c['missions'])

    def next_mission(self):
        letter = self.cfg['missions'][self.i]
        self.world.max_targets = self.ntargets()
        self.world.set_required(letter)
        self.badge.set(letter)
        self.app.audio.say(letter)

    # ---- game events (called by the world) ----
    def on_correct(self, letter):
        if self.done:
            return
        self.hits += 1
        self.streak += 1
        self.best = max(self.best, self.streak)
        self.score += 10
        self.hit_letters.append(letter)
        self.i += 1
        self.app.audio.play('correct')
        self.show_msg('Great! %s is for %s!' % (letter, WORDS[letter]), 'good')
        self.update_hud()
        if self.i >= len(self.cfg['missions']):
            self.finish(True)
        else:
            self.next_mission()

    def on_wrong(self, letter):
        if self.done:
            return
        self.wrong += 1
        self.streak = 0
        self.app.audio.play('wrong')
        self.show_msg("Oops! That is %s. Find %s!" % (letter, self.cfg['missions'][self.i]), 'hint')

    def on_miss(self, letter):
        if self.done:
            return
        self.misses += 1
        self.streak = 0
        self.lives -= 1
        self.update_hud()
        self.app.audio.play('wrong')
        if self.lives <= 0:
            self.finish(False)
            return
        self.show_msg('%s floated away. Try again!' % letter, 'bad')
        self.world.set_required(letter)

    def finish(self, success):
        if self.done:
            return
        self.done = True
        self.world.pause()
        if success:
            self.score += self.lives * 20
        res = dict(success=success, score=self.score, stars=max(1, self.lives) if success else 0,
                   hits=self.hits, wrong=self.wrong, misses=self.misses, best_streak=self.best,
                   hit_letters=list(self.hit_letters), lives=self.lives,
                   practiced=sorted(set(self.cfg['missions'])),
                   accuracy=round(100 * self.hits / max(1, self.hits + self.wrong + self.misses)))
        res['badges'] = self.app.progress.finish_run(self.cfg, res)
        self.app.audio.play('level' if success else 'wrong')
        cfg = self.cfg
        self._ev = Clock.schedule_once(lambda dt: self.app.show_summary(cfg, res), .9)

    # ---- messages / overlays ----
    def show_msg(self, text, kind):
        self.banner.set_bg({'good': GOLD, 'hint': '#7DD3FC', 'bad': '#FFB3C1'}[kind])
        self.msg.text = text
        Animation.cancel_all(self.banner)
        self.banner.opacity = 0
        (Animation(opacity=1, d=.12) + Animation(opacity=1, d=1.4) + Animation(opacity=0, d=.3)).start(self.banner)
        self.banner.bounce('big')

    def set_overlay(self, ov):
        self.clear_overlay()
        self.overlay = ov
        self.add_widget(ov)

    def clear_overlay(self):
        if self.overlay:
            self.remove_widget(self.overlay)
            self.overlay = None

    def panel(self, height):
        return Pad(bg='#241B6BF2', radius=30, orientation='vertical', size_hint=(.88, None), height=S(height),
                   pos_hint={'center_x': .5, 'center_y': .5}, padding=S(14), spacing=S(8))

    def show_intro(self):
        ov, p = Overlay(), self.panel(340)
        first = self.cfg['missions'][0]
        p.add_widget(lbl(self.cfg['name'], 'H4', GOLD, size_hint_y=.16))
        p.add_widget(lbl('First mission: hit letter', 'H6', size_hint_y=.1))
        p.add_widget(LetterBadge(first, mult=2.6, size_hint_y=.3))
        p.add_widget(lbl('Drag your finger to fly.\nLasers fire by themselves!', 'H6', size_hint_y=.2))
        p.add_widget(btn("Let's Go!", PINK, self.start_play, 'H4', size_hint_y=.2))
        ov.add_widget(p)
        self.set_overlay(ov)

    def start_play(self):
        self.clear_overlay()
        self.world.start()
        self.app.audio.say(self.cfg['missions'][self.i])

    def pause_game(self):
        if self.done or self.overlay or not self.cfg:
            return
        self.world.pause()
        ov, p = Overlay(), self.panel(400)
        p.add_widget(lbl('Paused', 'H3', GOLD, size_hint_y=.18))
        for r in settings_rows(self.app):
            p.add_widget(r)
        p.add_widget(btn('Resume', MINT, self.resume_game, 'H4', size_hint_y=.16))
        p.add_widget(btn('Home', PINK, self.quit_home, 'H5', size_hint_y=.14))
        ov.add_widget(p)
        self.set_overlay(ov)

    def resume_game(self):
        self.clear_overlay()
        self.world.start()

    def quit_home(self):
        self.clear_overlay()
        self.world.pause()
        self.app.go('home')

    def toggle_sound(self):
        self.app.set_setting('sfx', not self.app.progress.setting('sfx'))
        self.sound_btn()

    def sound_btn(self):
        self.snd.set_bg(MINT if self.app.progress.setting('sfx') else OFF)


class SummaryScreen(MenuScreen):
    """Level / mission summary with a Continue button."""

    def __init__(self, app, **kw):
        super().__init__(app, **kw)
        self.cfg = self.res = None
        f = self.frame
        self.title = lbl('', 'H3', GOLD, size_hint_y=.12)
        self.sub = lbl('', 'H6', size_hint_y=.07)
        self.star_box = BoxLayout(size_hint_y=.14)
        self.info = Pad(orientation='vertical', size_hint_y=.28)
        self.rows = [lbl('', 'H6') for _ in range(4)]
        for r in self.rows:
            self.info.add_widget(r)
        self.badge_l = lbl('', 'H6', CYAN, size_hint_y=.1)
        self.b1 = btn('', PINK, self.primary, 'H4', size_hint_y=.12)
        self.b2 = btn('Levels', CYAN, lambda: app.go('levels'), 'H5', size_hint_y=.1)
        self.b3 = btn('Home', MINT, lambda: app.go('home'), 'H5', size_hint_y=.1)
        for x in (self.title, self.sub, self.star_box, self.info, self.badge_l, self.b1, self.b2, self.b3):
            f.add_widget(x)
        self._go = lambda: None

    def show(self, cfg, res):
        self.cfg, self.res = cfg, res

    def primary(self):
        self._go()

    def refresh(self):
        c, r, app = self.cfg, self.res, self.app
        if not r:
            return
        ok, is_level = r['success'], c['kind'] == 'level'
        self.title.text = ('Level Complete!' if is_level else 'Mission Complete!') if ok else 'Good try!'
        self.sub.text = c['name'] if ok else "Let's practise some more!"
        self.star_box.clear_widgets()
        self.star_box.add_widget(Widget())
        for i in range(3):
            self.star_box.add_widget(StarIcon(color=[1, .85, .3, 1] if i < r['stars'] else [.45, .48, .7, .7],
                                              size_hint=(None, 1), width=S(70)))
        self.star_box.add_widget(Widget())
        for lab, t in zip(self.rows, ('Score: %d' % r['score'],
                                      'Letters hit: %d   Accuracy: %d%%' % (r['hits'], r['accuracy']),
                                      'Best streak: %d' % r['best_streak'],
                                      'Practised: ' + ' '.join(r['practiced']))):
            lab.text = t
        names = {b[0]: b[1] for b in BADGES}
        self.badge_l.text = ('New badge: ' + ', '.join(names[b] for b in r['badges'])) if r['badges'] else ''
        if not ok:
            self.b1.lab.text = 'Try Again'
            self._go = lambda: app.restart(c)
        elif is_level and c['level'] < len(PLANETS):
            self.b1.lab.text = 'Next Level'
            self._go = lambda: app.start_level(c['level'] + 1)
        elif is_level:
            self.b1.lab.text = 'Play Again'
            self._go = lambda: app.restart(c)
        else:
            self.b1.lab.text = 'More Letters'
            self._go = lambda: app.go('missions')
