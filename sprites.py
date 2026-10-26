"""Canvas sprites. Instructions are created once and only their numbers change each frame."""
import math
import random

from kivy.graphics import (Color, Ellipse, InstructionGroup, Line, PopMatrix, PushMatrix,
                           Rectangle, RoundedRectangle, Rotate, Scale, Translate, Triangle)
from kivy.utils import get_color_from_hex as hexc

DIE_TIME = .22  # seconds of the "pop" animation when a target is hit


def circle_rect(cx, cy, r, rx, ry, rw, rh):
    """Circle vs rectangle overlap test (target vs laser)."""
    nx = max(rx, min(cx, rx + rw))
    ny = max(ry, min(cy, ry + rh))
    return (cx - nx) ** 2 + (cy - ny) ** 2 <= r * r


class Spaceship:
    """Cute cartoon ship drawn around (0, 0); moved with a Translate + Rotate (lean)."""

    def __init__(self, layer):
        self.group = InstructionGroup()
        layer.add(self.group)
        self.u = 0

    def build(self, u):
        g, self.u = self.group, u
        g.clear()
        add = g.add
        add(PushMatrix())
        self.tr = Translate(0, 0)
        self.rot = Rotate(angle=0, axis=(0, 0, 1), origin=(0, 0))
        add(self.tr)
        add(self.rot)
        add(Color(.3, .9, 1, .16))                                        # engine glow
        add(Ellipse(pos=(-.75 * u, -1.75 * u), size=(1.5 * u, 1.5 * u)))
        add(Color(1, .5, .15, .95))                                       # flame (flickers)
        self.f_out = Ellipse(pos=(-.32 * u, -1.35 * u), size=(.64 * u, 1.0 * u))
        add(self.f_out)
        add(Color(1, .95, .5, 1))
        self.f_in = Ellipse(pos=(-.18 * u, -1.15 * u), size=(.36 * u, .7 * u))
        add(self.f_in)
        for sx in (-1, 1):                                                # wings: shade + colour
            add(Color(.72, .22, .45, 1))
            add(Triangle(points=[sx * .4 * u, -.28 * u, sx * 1.4 * u, -1.03 * u, sx * .3 * u, -.98 * u]))
            add(Color(1, .42, .62, 1))
            add(Triangle(points=[sx * .4 * u, -.2 * u, sx * 1.4 * u, -.95 * u, sx * .3 * u, -.9 * u]))
            add(Color(1, .9, .3, 1))
            add(Ellipse(pos=(sx * 1.3 * u - .1 * u, -.95 * u), size=(.2 * u, .2 * u)))
        add(Color(.5, .55, .95, 1))                                       # body shade
        add(Ellipse(pos=(-.48 * u, -1.05 * u), size=(1.0 * u, 2.0 * u)))
        add(Color(.94, .96, 1, 1))                                        # body
        add(Ellipse(pos=(-.5 * u, -.95 * u), size=(.98 * u, 2.0 * u)))
        add(Color(1, .42, .62, 1))                                        # nose cone
        add(Triangle(points=[-.38 * u, .62 * u, .38 * u, .62 * u, 0, 1.45 * u]))
        add(Color(.2, .3, .7, 1))                                         # window
        add(Ellipse(pos=(-.32 * u, .02 * u), size=(.64 * u, .64 * u)))
        add(Color(.35, .9, 1, 1))
        add(Ellipse(pos=(-.27 * u, .07 * u), size=(.54 * u, .54 * u)))
        add(Color(1, 1, 1, .85))
        add(Ellipse(pos=(-.18 * u, .38 * u), size=(.2 * u, .14 * u)))
        self.flash_c = Color(.7, 1, 1, 0)                                 # muzzle flash
        add(self.flash_c)
        add(Ellipse(pos=(-.4 * u, 1.2 * u), size=(.8 * u, .8 * u)))
        add(PopMatrix())

    def update(self, x, y, angle, t, flash):
        if not self.u:
            return
        u = self.u
        self.tr.x, self.tr.y = x, y
        self.rot.angle = angle
        f = 1 + .22 * math.sin(t * 38) + .1 * math.sin(t * 61)
        self.f_out.size = (.64 * u, 1.0 * u * f)
        self.f_out.pos = (-.32 * u, -.35 * u - 1.0 * u * f)
        self.f_in.size = (.36 * u, .7 * u * f)
        self.f_in.pos = (-.18 * u, -.35 * u - .7 * u * f)
        self.flash_c.a = min(1, flash / .07) * .9


class AlphabetTarget:
    """Floating letter bubble with depth, highlight, shadow, gentle sway and rotation."""

    def __init__(self, layer, letter, x, y, size, color, tex, speed):
        self.layer, self.letter = layer, letter
        self.x0 = self.x = x
        self.y = y
        self.speed = speed
        self.phase = random.uniform(0, 6.28)
        self.freq = random.uniform(.8, 1.4)
        self.dying, self.age = False, 0.0
        self.group = InstructionGroup()
        layer.add(self.group)
        self.build(size, color, tex)

    def build(self, size, color, tex):
        self.size, self.color = size, color
        r = self.r = size / 2
        self.hit_r = r * .88
        self.amp = size * .12
        g = self.group
        g.clear()
        c = hexc(color)
        self.cols = []  # (Color, base alpha) so the pop-out can fade everything

        def col(*rgba):
            cc = Color(*rgba)
            self.cols.append((cc, rgba[3]))
            g.add(cc)
        g.add(PushMatrix())
        self.tr = Translate(self.x, self.y)
        self.rot = Rotate(angle=0, axis=(0, 0, 1), origin=(0, 0))
        self.sc = Scale(1, 1, 1)
        for ins in (self.tr, self.rot, self.sc):
            g.add(ins)
        self.glow_c = Color(1, .85, .2, 0)                                # "this is the one" glow
        g.add(self.glow_c)
        g.add(Ellipse(pos=(-r * 1.4, -r * 1.4), size=(r * 2.8, r * 2.8)))
        self.ring_c = Color(1, .9, .4, 0)
        g.add(self.ring_c)
        g.add(Line(circle=(0, 0, r * 1.12), width=max(1.5, r * .07)))
        col(0, 0, 0, .28)                                                 # drop shadow
        g.add(Ellipse(pos=(-r + r * .12, -r - r * .16), size=(2 * r, 2 * r)))
        col(c[0] * .6, c[1] * .6, c[2] * .6, 1)                           # dark base (thickness)
        g.add(Ellipse(pos=(-r, -r), size=(2 * r, 2 * r)))
        col(c[0], c[1], c[2], 1)                                          # main face
        g.add(Ellipse(pos=(-r, -r + r * .08), size=(2 * r, 2 * r * .92)))
        col(1, 1, 1, .18)                                                 # soft inner light
        g.add(Ellipse(pos=(-r * .75, -r * .5), size=(r * 1.5, r * 1.2)))
        col(1, 1, 1, .6)                                                  # glossy highlight
        g.add(Ellipse(pos=(-r * .62, r * .3), size=(r * .55, r * .3)))
        col(1, 1, 1, .5)                                                  # rim
        g.add(Line(circle=(0, r * .04, r * .94), width=max(1, r * .04)))
        tw, th = tex.size
        col(0, 0, .2, .35)                                                # letter shadow
        g.add(Rectangle(texture=tex, pos=(-tw / 2 + r * .05, -th / 2 - r * .02), size=(tw, th)))
        col(1, 1, 1, 1)                                                   # letter
        g.add(Rectangle(texture=tex, pos=(-tw / 2, -th / 2 + r * .05), size=(tw, th)))
        g.add(PopMatrix())

    def set_glow(self, a):
        self.glow_c.a = a * .35
        self.ring_c.a = a

    def pop(self):
        self.dying, self.age = True, 0.0
        self.set_glow(0)

    def update(self, dt, t, w):
        if self.dying:
            self.age += dt
            f = min(1, self.age / DIE_TIME)
            self.sc.x = self.sc.y = 1 + .6 * f
            for cc, a in self.cols:
                cc.a = a * (1 - f)
            return
        self.y -= self.speed * dt
        self.x = max(self.r, min(w - self.r, self.x0 + self.amp * math.sin(t * self.freq + self.phase)))
        self.tr.x, self.tr.y = self.x, self.y
        self.rot.angle = 8 * math.sin(t * .9 + self.phase)

    def remove(self):
        self.layer.remove(self.group)


class LaserProjectile:
    """Pooled laser: glow + bright core. Hidden (alpha 0) when idle."""

    def __init__(self, layer):
        self.glow_c = Color(.3, .9, 1, 0)
        self.glow = RoundedRectangle(pos=(-999, -999), size=(1, 1), radius=[4])
        self.core_c = Color(1, 1, 1, 0)
        self.core = RoundedRectangle(pos=(-999, -999), size=(1, 1), radius=[3])
        for ins in (self.glow_c, self.glow, self.core_c, self.core):
            layer.add(ins)
        self.active, self.x, self.y, self.w, self.h = False, 0, 0, 1, 1

    def launch(self, x, y, w, h):
        self.active, self.x, self.y, self.w, self.h = True, x, y, w, h
        self.glow.radius = [w]
        self.glow.size = (w * 3, h * 1.25)
        self.core.size = (w, h)
        self.glow_c.a, self.core_c.a = .45, 1
        self.place()

    def place(self):
        self.glow.pos = (self.x - self.w * 1.5, self.y - self.h * .12)
        self.core.pos = (self.x - self.w / 2, self.y)

    def move(self, dy):
        self.y += dy
        self.place()

    def hide(self):
        self.active = False
        self.glow_c.a = self.core_c.a = 0
        self.glow.pos = self.core.pos = (-999, -999)


class _Particle:
    __slots__ = ('c', 'e', 'active', 'x', 'y', 'vx', 'vy', 'life', 'max', 'size', 'ring')


class ParticleEffect:
    """Fixed pool of sparkles/shock-rings; never grows, so it cannot leak."""

    def __init__(self, layer, n=60):
        self.free, self.active = [], []
        for _ in range(n):
            p = _Particle()
            p.c = Color(1, 1, 1, 0)
            p.e = Ellipse(pos=(-999, -999), size=(1, 1))
            layer.add(p.c)
            layer.add(p.e)
            p.active = False
            self.free.append(p)

    def burst(self, x, y, colors, n, speed, size, life=.7):
        for _ in range(n):
            if not self.free:
                return
            p = self.free.pop()
            ang, sp = random.uniform(0, 6.283), random.uniform(.35, 1) * speed
            p.x, p.y, p.vx, p.vy = x, y, math.cos(ang) * sp, math.sin(ang) * sp
            p.life = p.max = life * random.uniform(.6, 1)
            p.size, p.ring = size * random.uniform(.6, 1.2), False
            p.c.rgb = hexc(random.choice(colors))[:3]
            self.active.append(p)

    def ring(self, x, y, color, size):
        if self.free:
            p = self.free.pop()
            p.x, p.y, p.vx, p.vy, p.life, p.max = x, y, 0, 0, .4, .4
            p.size, p.ring = size, True
            p.c.rgb = hexc(color)[:3]
            self.active.append(p)

    def clear(self):
        for p in self.active:
            self._release(p)
        self.active = []

    def _release(self, p):
        p.c.a = 0
        p.e.pos = (-999, -999)
        self.free.append(p)

    def update(self, dt, gravity):
        for p in list(self.active):
            p.life -= dt
            if p.life <= 0:
                self.active.remove(p)
                self._release(p)
                continue
            f = p.life / p.max
            if p.ring:
                s, p.c.a = p.size * (1 + 2.4 * (1 - f)), f * .5
            else:
                p.x += p.vx * dt
                p.y += p.vy * dt
                p.vy -= gravity * dt
                s, p.c.a = p.size * (.4 + .6 * f), f
            p.e.size = (s, s)
            p.e.pos = (p.x - s / 2, p.y - s / 2)
