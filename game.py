"""GameWorld: the canvas-based play field. It knows nothing about menus, HUD or saving;
it reports events through callbacks (on_correct / on_wrong / on_miss / on_fire)."""
import math
import random

from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, InstructionGroup, Line, PopMatrix, PushMatrix, Translate
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hexc

from data import PLANETS, letter_color
from sprites import (DIE_TIME, AlphabetTarget, LaserProjectile, ParticleEffect, Spaceship,
                     circle_rect)
from ui import Starfield, paint_background

FIRE_INTERVAL = .32   # seconds between laser shots (configurable)
MAX_LASERS = 14       # laser pool size (never grows)
MAX_PARTICLES = 60    # particle pool size (lower for very weak devices)


class _Planet:
    """Distant decorative planet; drifts slowly downwards."""

    def __init__(self, group, x, y, r, color, ring, speed):
        self.y, self.r, self.speed = y, r, speed
        c = hexc(color)
        group.add(PushMatrix())
        self.tr = Translate(x, y)
        group.add(self.tr)
        group.add(Color(c[0] * .5, c[1] * .5, c[2] * .5, .8))
        group.add(Ellipse(pos=(-r, -r), size=(2 * r, 2 * r)))
        group.add(Color(c[0], c[1], c[2], .8))
        group.add(Ellipse(pos=(-r * .92, -r * .85), size=(r * 1.7, r * 1.7)))
        group.add(Color(1, 1, 1, .22))
        group.add(Ellipse(pos=(-r * .6, r * .2), size=(r * .6, r * .35)))
        if ring:
            group.add(Color(1, 1, 1, .4))
            group.add(Line(ellipse=(-r * 1.6, -r * .35, r * 3.2, r * .7), width=dp(2)))
        group.add(PopMatrix())


class GameWorld(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.on_correct = self.on_wrong = self.on_miss = self.on_fire = None
        self.hud_h = 0                 # touches inside this top strip never move the ship
        self.running = False
        self._upd = self._fire_ev = None
        self.w = self.h = 0
        self.k, self.u, self.tsize = 1.0, 1.0, 1.0
        self.theme = PLANETS[0]
        self.pool, self.required, self.speed_dp, self.max_targets = ['A', 'B'], None, 40, 3
        self.targets, self.planets, self.tex = [], [], {}
        self.t, self.flash, self.spawn_cd, self.vx = 0.0, 0.0, 1.0, 0.0
        self.ship_x = self.target_x = self.ship_y = 0.0
        self.touch_x, self.touch_order = {}, []
        self.lite, self._ema, self._slow, self._frame = False, 1 / 60, 0.0, 0  # adaptive quality

        c = self.canvas
        c.add(PushMatrix())
        self._origin = Translate(0, 0)
        c.add(self._origin)
        self.L_bg, self.L_stars, self.L_planets, self.L_targets, self.L_lasers, \
            self.L_ship, self.L_fx = (InstructionGroup() for _ in range(7))
        for layer in (self.L_bg, self.L_stars, self.L_planets, self.L_targets,
                      self.L_lasers, self.L_ship, self.L_fx):
            c.add(layer)
        c.add(PopMatrix())

        self.stars = Starfield(self.L_stars)
        self.ship = Spaceship(self.L_ship)
        self.lasers = [LaserProjectile(self.L_lasers) for _ in range(MAX_LASERS)]
        self.fx = ParticleEffect(self.L_fx, MAX_PARTICLES)
        self.bind(pos=self._on_pos, size=self._on_size)

    # ------------------------------------------------------------ layout --
    def _on_pos(self, *a):
        self._origin.x, self._origin.y = self.x, self.y

    def _on_size(self, *a):
        w, h = self.size
        if w < 2 or h < 2:
            return
        ow, oh, ok = self.w, self.h, self.k
        self.w, self.h = w, h
        self.k = max(.7, min(2.2, min(w, h * .6) / dp(360)))  # works in portrait AND landscape/tablets
        self.u, self.tsize = dp(28) * self.k, dp(66) * self.k
        self.tex.clear()
        self.ship.build(self.u)
        self.ship_y = dp(34) * self.k + 1.5 * self.u
        if ow:  # keep everything where it was, proportionally
            rx, ry = w / ow, h / oh
            self.ship_x *= rx
            self.target_x *= rx
            for tg in self.targets:
                tg.x0 *= rx
                tg.x *= rx
                tg.y *= ry
                tg.speed *= self.k / ok
                tg.build(self.tsize, tg.color, self.texture(tg.letter))
        else:
            self.ship_x = self.target_x = w / 2
        self.paint()

    def paint(self):
        if not self.w:
            return
        paint_background(self.L_bg, self.theme, 0, 0, self.w, self.h)
        self.stars.build(0, 0, self.w, self.h)
        self.L_planets.clear()
        self.planets = [
            _Planet(self.L_planets, self.w * .18, self.h * .74, self.w * .15, self.theme['body'], False, dp(3)),
            _Planet(self.L_planets, self.w * .86, self.h * .36, self.w * .08, self.theme['neb'][0], True, dp(5))]

    def texture(self, letter):
        tex = self.tex.get(letter)
        if tex is None:
            cl = CoreLabel(text=letter, font_size=int(self.tsize * .6), bold=True)
            cl.refresh()
            tex = self.tex[letter] = cl.texture
        return tex

    # ----------------------------------------------------------- control --
    def reset(self, theme_index):
        self.pause()
        for tg in self.targets:
            tg.remove()
        self.targets = []
        for ls in self.lasers:
            ls.hide()
        self.fx.clear()
        self.theme = PLANETS[theme_index]
        self.required = None
        self.t = self.flash = self.vx = 0.0
        self.spawn_cd = 1.0
        self.lite, self._ema, self._slow, self._frame = False, 1 / 60, 0.0, 0
        self.ship_x = self.target_x = self.w / 2
        self.paint()

    def configure(self, pool, speed_dp, max_targets):
        self.pool, self.speed_dp, self.max_targets = list(pool), speed_dp, max_targets

    def start(self):
        """Start (or resume) updates and automatic firing."""
        self.pause()
        self.running = True
        self._upd = Clock.schedule_interval(self.update, 1 / 60)
        self._fire_ev = Clock.schedule_interval(self.fire, FIRE_INTERVAL)

    def pause(self):
        self.running = False
        for ev in (self._upd, self._fire_ev):
            if ev:
                ev.cancel()
        self._upd = self._fire_ev = None
        self.touch_x.clear()
        del self.touch_order[:]
        self.target_x = self.ship_x  # finger gone -> ship stays put

    def cleanup(self):
        self.pause()
        self.on_correct = self.on_wrong = self.on_miss = self.on_fire = None

    # ------------------------------------------------------------- input --
    def _clamp(self, x):
        m = 1.4 * self.u
        return max(m, min(self.w - m, x))

    def on_touch_down(self, touch):
        if not self.running or not self.collide_point(*touch.pos):
            return False
        if touch.y > self.top - self.hud_h:  # HUD strip: never starts a drag
            return False
        touch.grab(self)
        self.touch_x[touch.uid] = touch.x - self.x
        self.touch_order.append(touch.uid)
        self.target_x = self._clamp(touch.x - self.x)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self and touch.uid in self.touch_x:
            self.touch_x[touch.uid] = touch.x - self.x
            if self.touch_order and self.touch_order[-1] == touch.uid:  # newest finger wins
                self.target_x = self._clamp(touch.x - self.x)
            return True
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.touch_x.pop(touch.uid, None)
            if touch.uid in self.touch_order:
                self.touch_order.remove(touch.uid)
            if self.touch_order:
                self.target_x = self._clamp(self.touch_x[self.touch_order[-1]])
            else:
                self.target_x = self.ship_x  # releasing stops movement; firing continues
            return True
        return False

    # ----------------------------------------------------------- spawning --
    def set_required(self, letter):
        self.required = letter
        if letter and not any(t.letter == letter and not t.dying for t in self.targets):
            self._spawn(letter)

    def seed_wave(self, n):
        """Fill the upper screen with n targets (one is the required letter)."""
        letters = [self.required] + [self._pick(exclude_required=True) for _ in range(max(0, n - 1))]
        random.shuffle(letters)
        for i, l in enumerate(letters):
            self._spawn(l, y=self.h * (.5 + .4 * i / max(1, n - 1)))

    def _pick(self, exclude_required=False):
        present = {t.letter for t in self.targets if not t.dying}
        if not exclude_required and self.required and self.required not in present:
            return self.required
        choices = [l for l in self.pool if l != self.required and l not in present] or \
                  [l for l in self.pool if l != self.required] or [self.required or 'A']
        return random.choice(choices)

    def _spawn(self, letter, y=None):
        size, r = self.tsize, self.tsize / 2
        y0 = self.h + r * 1.2 if y is None else y
        alive = [t for t in self.targets if not t.dying]
        x = random.uniform(r * 1.2, max(r * 1.2, self.w - r * 1.2))
        for _ in range(12):
            cand = random.uniform(r * 1.2, max(r * 1.2, self.w - r * 1.2))
            if all(abs(cand - t.x0) > size * 1.2 or abs(y0 - t.y) > size * 1.5 for t in alive):
                x = cand
                break
        speed = dp(self.speed_dp) * self.k * random.uniform(.85, 1.15)
        self.targets.append(AlphabetTarget(self.L_targets, letter, x, y0, size,
                                           letter_color(letter), self.texture(letter), speed))

    # ----------------------------------------------------------- game loop --
    def fire(self, dt):
        if not self.w:
            return
        for ls in self.lasers:
            if not ls.active:
                ls.launch(self.ship_x, self.ship_y + 1.45 * self.u, dp(5) * self.k, dp(28) * self.k)
                self.flash = .07
                if self.on_fire:
                    self.on_fire()
                return

    def update(self, dt):
        if not self.w:
            return
        dt = min(dt, .05)
        self.t += dt
        t = self.t
        # weak phone? if frames stay slow for 2 s, drop some eye-candy instead of lagging
        self._ema += (dt - self._ema) * .05
        self._slow = self._slow + dt if self._ema > 1 / 38 else max(0.0, self._slow - dt)
        if self._slow > 2.0:
            self.lite = True
        self._frame += 1
        if not self.lite or self._frame % 2 == 0:
            self.stars.update(dt * (2 if self.lite else 1), t)
        for p in self.planets:
            p.y -= p.speed * dt
            if p.y < -p.r * 1.8:
                p.y = self.h + p.r * 1.8
            p.tr.y = p.y

        # spaceship follows the finger smoothly and leans into the movement
        old = self.ship_x
        self.ship_x = self._clamp(old + (self.target_x - old) * min(1, dt * 16))
        self.vx += ((self.ship_x - old) / dt - self.vx) * min(1, dt * 10)
        self.flash = max(0, self.flash - dt)
        self.ship.update(self.ship_x, self.ship_y, max(-14, min(14, -self.vx / self.w * 30)), t, self.flash)

        # targets
        dead, missed = [], []
        for tg in self.targets:
            tg.update(dt, t, self.w)
            if tg.dying:
                if tg.age >= DIE_TIME:
                    dead.append(tg)
            elif tg.y < -tg.r * 1.2:
                dead.append(tg)
                if tg.letter == self.required:
                    missed.append(tg.letter)
            else:
                tg.set_glow(.65 + .35 * math.sin(t * 6) if tg.letter == self.required else 0)
        for tg in dead:
            tg.remove()
            self.targets.remove(tg)

        # lasers + collisions (one laser can hit one target once; popped targets are ignored)
        step = self.h * 1.25 * dt
        for ls in self.lasers:
            if not ls.active:
                continue
            ls.move(step)
            if ls.y > self.h:
                ls.hide()
                continue
            for tg in tuple(self.targets):
                if not tg.dying and circle_rect(tg.x, tg.y, tg.hit_r, ls.x - ls.w / 2, ls.y, ls.w, ls.h):
                    ls.hide()
                    self._hit(tg)
                    break

        self.fx.update(dt, dp(120) * self.k)

        # keep the field populated
        self.spawn_cd -= dt
        if self.spawn_cd <= 0:
            if sum(1 for tg in self.targets if not tg.dying) < self.max_targets:
                self._spawn(self._pick())
            self.spawn_cd = random.uniform(.5, 1.0)

        for letter in missed:
            if self.on_miss:
                self.on_miss(letter)

    def _hit(self, tg):
        tg.pop()
        k = self.k
        if tg.letter == self.required:
            self.fx.burst(tg.x, tg.y, ['#FFE066', '#FFFFFF', '#FFB347', tg.color], 10 if self.lite else 22, dp(260) * k, dp(9) * k, .8)
            self.fx.ring(tg.x, tg.y, '#FFE066', tg.size * .8)
            if self.on_correct:
                self.on_correct(tg.letter)
        else:
            self.fx.burst(tg.x, tg.y, ['#BFE3FF', '#FFFFFF', tg.color], 5 if self.lite else 10, dp(150) * k, dp(7) * k, .6)
            self.fx.ring(tg.x, tg.y, '#7DD3FC', tg.size * .7)
            if self.on_wrong:
                self.on_wrong(tg.letter)
