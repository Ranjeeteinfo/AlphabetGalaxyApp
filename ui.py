"""Shared UI helpers for Alphabet Galaxy (menus, HUD, space background)."""
import math
import random

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import (Color, Ellipse, InstructionGroup, Line, Mesh, Point,
                           PopMatrix, PushMatrix, Rectangle, RoundedRectangle, Scale, Triangle)
from kivy.graphics.texture import Texture
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as hexc
from kivymd.uix.label import MDLabel

from data import PLANETS, letter_color

NAVY, PINK, CYAN, GOLD = '#0B1033', '#FF5FA2', '#4FE3FF', '#FFD84D'
MINT, LAV, WHITE, GLASS = '#6BE08C', '#9B7BFF', '#FFFFFF', '#1B1F5CE0'
MAX_W = 560  # dp: menu content never gets wider than this
HOOKS = {'click': None}  # set by the app: plays the button sound
BASE_SP = {'H3': 44, 'H4': 32, 'H5': 24, 'H6': 20, 'Subtitle1': 16, 'Caption': 13}


# ------------------------------------------------------------- responsive --
def scale():
    """1.0 on a 360dp-wide phone, bigger on larger screens (never below .85)."""
    return max(.85, min(1.6, min(Window.size) / dp(360)))


def S(n):
    return dp(n) * scale()


def fit(label, *a):
    """Choose the biggest font that fits the label; wrap to more lines if needed."""
    w, h = label.size
    if w < 2 or h < 2:
        return
    size, low = sp(BASE_SP[label.style]) * scale() * label.mult, sp(9)
    while size > low:
        lines = sum(max(1, math.ceil(len(t) * size * .6 / w)) for t in label.text.split('\n'))
        if lines * size * 1.3 <= h:
            break
        size *= .92
    label.font_size = max(size, low)


def lbl(text='', style='H5', color=WHITE, bold=True, mult=1.0, **kw):
    kw.setdefault('halign', 'center')
    label = MDLabel(text=text, font_style=style, valign='middle', bold=bold,
                    theme_text_color='Custom', text_color=hexc(color), **kw)
    label.style, label.mult = style, mult

    def resize(w, s):
        w.text_size = s
        fit(w)
    label.bind(size=resize, text=fit)
    return label


# ---------------------------------------------------------------- widgets --
class Pad(BoxLayout):
    """Rounded chunky 3D panel (darker bottom edge) with bounce animations."""

    def __init__(self, bg=GLASS, radius=24, **kw):
        kw.setdefault('padding', [S(8), S(8), S(8), S(14)])
        kw.setdefault('spacing', S(4))
        super().__init__(**kw)
        r = [S(radius)]
        with self.canvas.before:
            PushMatrix()
            self._sc = Scale(1, 1, 1)
            self._ce = Color()
            self._re = RoundedRectangle(radius=r)
            self._cf = Color()
            self._rf = RoundedRectangle(radius=r)
        with self.canvas.after:
            PopMatrix()
        self.set_bg(bg)
        self.bind(pos=self.fit_rects, size=self.fit_rects)

    def set_bg(self, bg):
        c = hexc(bg)
        self._cf.rgba = c
        self._ce.rgba = (c[0] * .65, c[1] * .65, c[2] * .75, c[3])

    def fit_rects(self, *a):
        (x, y), (w, h), e = self.pos, self.size, S(6)
        self._sc.origin = self.center
        self._re.pos, self._re.size = (x, y), (w, h)
        self._rf.pos, self._rf.size = (x, y + e), (w, max(h - e, 0))

    def bounce(self, kind='tap'):
        Animation.cancel_all(self._sc)
        if kind == 'big':
            seq = (Animation(x=1.12, y=1.12, d=.12, t='out_quad')
                   + Animation(x=1, y=1, d=.3, t='out_bounce'))
        else:
            seq = Animation(x=.92, y=.92, d=.05) + Animation(x=1, y=1, d=.12, t='out_back')
        seq.start(self._sc)


class Tap(ButtonBehavior, Pad):
    def on_press(self):
        self.bounce()
        if HOOKS['click']:
            HOOKS['click']()


def btn(text, bg, cb, style='H5', color=NAVY, **kw):
    """Big rounded button. cb() is called on release."""
    b = Tap(bg=bg, radius=26, on_release=lambda *_: cb(), **kw)
    b.lab = lbl(text, style, color)
    b.add_widget(b.lab)
    return b


class Overlay(FloatLayout):
    """Full-screen dimmed layer that swallows every touch (so nothing underneath reacts)."""

    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(0, 0, .05, .72)
            self._r = Rectangle()
        self.bind(pos=self._fit, size=self._fit)

    def _fit(self, *a):
        self._r.pos, self._r.size = self.pos, self.size

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        return True

    def on_touch_move(self, touch):
        super().on_touch_move(touch)
        return True

    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        return True


def star_points(cx, cy, R, inner=.52):
    v = [cx, cy, 0, 0]
    for k in range(11):
        a = math.pi / 2 + k * math.pi / 5
        r = R if k % 2 == 0 else R * inner
        v += [cx + r * math.cos(a), cy + r * math.sin(a), 0, 0]
    return v


class StarIcon(Widget):
    color = ListProperty([1, .85, .3, 1])

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self.draw, size=self.draw, color=self.draw)

    def draw(self, *a):
        self.canvas.clear()
        s = min(self.size) * .46
        if s <= 0:
            return
        cx, cy = self.center
        r, g, b = self.color[:3]
        with self.canvas:
            Color(r * .65, g * .65, b * .65, self.color[3])
            Mesh(vertices=star_points(cx, cy - s * .08, s), indices=list(range(12)), mode='triangle_fan')
            Color(*self.color)
            Mesh(vertices=star_points(cx, cy, s), indices=list(range(12)), mode='triangle_fan')
            Color(1, 1, 1, .35 * self.color[3])
            Ellipse(pos=(cx - s * .3, cy + s * .15), size=(s * .3, s * .2))


def star_row(n=0, total=3, size=34, **kw):
    """Row of `total` stars, the first `n` golden."""
    row = BoxLayout(**kw)
    for i in range(total):
        row.add_widget(StarIcon(color=[1, .85, .3, 1] if i < n else [.45, .48, .7, .7],
                                size_hint=(None, 1), width=S(size)))
    return row


class Disc(Widget):
    """Glossy 3D ball (planets, letter bubbles)."""
    color = ListProperty([1, 1, 1, 1])
    ring = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self.draw, size=self.draw, color=self.draw)

    def draw(self, *a):
        self.canvas.before.clear()
        s = min(self.size) * .9
        if s <= 0:
            return
        cx, cy = self.center
        r, g, b, a = self.color
        with self.canvas.before:
            Color(0, 0, 0, .25 * a)
            Ellipse(pos=(cx - s / 2 + s * .05, cy - s / 2 - s * .06), size=(s, s))
            Color(r * .6, g * .6, b * .6, a)
            Ellipse(pos=(cx - s / 2, cy - s / 2), size=(s, s))
            Color(r, g, b, a)
            Ellipse(pos=(cx - s / 2, cy - s / 2 + s * .06), size=(s, s * .94))
            Color(1, 1, 1, .45 * a)
            Ellipse(pos=(cx - s * .3, cy + s * .12), size=(s * .36, s * .22))
            if self.ring:
                Color(1, 1, 1, .5 * a)
                Line(ellipse=(cx - s * .7, cy - s * .16, s * 1.4, s * .32), width=dp(1.6))


class LetterBadge(FloatLayout):
    """Coloured bubble with a letter on it."""

    def __init__(self, letter='A', mult=1.0, **kw):
        super().__init__(**kw)
        self.disc = Disc()
        self.lab = lbl(letter, 'H5', NAVY, mult=mult)
        self.add_widget(self.disc)
        self.add_widget(self.lab)
        self.set(letter)

    def set(self, letter):
        self.disc.color = hexc(letter_color(letter))
        self.lab.text = letter


class Hearts(Widget):
    value = NumericProperty(3)
    total = NumericProperty(3)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self.draw, size=self.draw, value=self.draw, total=self.draw)

    def draw(self, *a):
        self.canvas.clear()
        n = int(self.total)
        if n <= 0 or self.width < 2:
            return
        s = min(self.height, self.width / n) * .8
        x0 = self.center_x - n * s * 1.1 / 2
        with self.canvas:
            for i in range(n):
                cx, cy = x0 + (i + .5) * s * 1.1, self.center_y
                Color(*((1, .3, .4, 1) if i < self.value else (.4, .42, .6, .6)))
                Ellipse(pos=(cx - s * .5, cy - s * .02), size=(s * .55, s * .55))
                Ellipse(pos=(cx - s * .05, cy - s * .02), size=(s * .55, s * .55))
                Triangle(points=[cx - s * .48, cy + s * .14, cx + s * .48, cy + s * .14, cx, cy - s * .46])


class Bar(Widget):
    value = NumericProperty(0)  # 0..1

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self.draw, size=self.draw, value=self.draw)

    def draw(self, *a):
        self.canvas.clear()
        w, h = self.size
        with self.canvas:
            Color(1, 1, 1, .18)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[h / 2])
            if self.value > 0:
                Color(*hexc(MINT))
                RoundedRectangle(pos=self.pos, size=(max(h, w * min(1, self.value)), h), radius=[h / 2])


class Toggle(ButtonBehavior, Widget):
    """Simple on/off switch."""
    active = BooleanProperty(False)

    def __init__(self, active=False, on_change=None, **kw):
        kw.setdefault('size_hint', (None, None))
        kw.setdefault('size', (S(64), S(34)))
        super().__init__(**kw)
        self.active, self.cb = active, on_change
        self.bind(pos=self.draw, size=self.draw, active=self.draw)
        self.draw()

    def on_release(self):
        self.active = not self.active
        if HOOKS['click']:
            HOOKS['click']()
        if self.cb:
            self.cb(self.active)

    def draw(self, *a):
        self.canvas.clear()
        (x, y), (w, h) = self.pos, self.size
        pad = h * .12
        with self.canvas:
            Color(*hexc(MINT if self.active else '#5A5E8F'))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[h / 2])
            Color(1, 1, 1, 1)
            Ellipse(pos=(x + (w - h if self.active else 0) + pad, y + pad), size=(h - 2 * pad, h - 2 * pad))


def scroll_grid(min_col, row_h):
    """Scrollable grid whose column count follows the available width."""
    grid = GridLayout(cols=2, spacing=S(10), padding=S(4), size_hint_y=None,
                      row_default_height=S(row_h), row_force_default=True)
    grid.bind(minimum_height=grid.setter('height'),
              width=lambda g, w: setattr(g, 'cols', max(2, int(w // S(min_col)))))
    sv = ScrollView(do_scroll_x=False)
    sv.add_widget(grid)
    return sv, grid


def shadow_title(text, color, **kw):
    """Big title with a dark 3D drop shadow."""
    box = FloatLayout(**kw)
    sh = lbl(text, 'H3', '#000033', mult=1.25, size_hint=(None, None))
    top = lbl(text, 'H3', color, mult=1.25, size_hint=(None, None))
    for w in (sh, top):
        box.add_widget(w)

    def place(*a):
        for w in (sh, top):
            w.size = box.size
        top.pos = box.pos
        sh.pos = (box.x + S(3), box.y - S(3))
    box.bind(pos=place, size=place)
    return box


# -------------------------------------------------------- space backdrop --
_GRAD = {}


def gradient_texture(top, bottom, n=64):
    key = (top, bottom)
    if key not in _GRAD:
        t = Texture.create(size=(1, n), colorfmt='rgba')
        a, b = hexc(top), hexc(bottom)
        buf = bytearray()
        for i in range(n):  # row 0 = bottom of the texture
            f = i / (n - 1)
            buf += bytes(int(max(0, min(255, (b[j] + (a[j] - b[j]) * f) * 255))) for j in range(4))
        t.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
        t.mag_filter = t.min_filter = 'linear'
        _GRAD[key] = t
    return _GRAD[key]


def paint_background(group, theme, x, y, w, h):
    """Deep blue/purple gradient + soft nebula clouds (drawn once per resize)."""
    group.clear()
    group.add(Color(1, 1, 1, 1))
    group.add(Rectangle(texture=gradient_texture(theme['top'], theme['bottom']), pos=(x, y), size=(w, h)))
    spots = ((.15, .82, .42), (.88, .55, .38), (.25, .18, .45), (.78, .1, .3))
    for i, (fx, fy, fr) in enumerate(spots):
        col = hexc(theme['neb'][i % len(theme['neb'])])
        r = min(w, h) * fr
        for s, a in ((1, .07), (.7, .08), (.42, .09)):
            group.add(Color(col[0], col[1], col[2], a))
            rr = r * s
            group.add(Ellipse(pos=(x + w * fx - rr, y + h * fy - rr * .8), size=(2 * rr, 1.6 * rr)))


class Starfield:
    """Three parallax layers of twinkling stars; each layer is ONE Point instruction."""
    SPEC = ((26, 1.6, 10, .55, '#FFFFFF'), (16, 2.6, 22, .8, '#FFF3B0'), (9, 3.8, 40, 1.0, '#BFF3FF'))

    def __init__(self, group):
        self.group, self.layers = group, []
        self.x = self.y = 0
        self.h = 1

    def build(self, x, y, w, h):
        self.group.clear()
        self.layers = []
        self.x, self.y, self.h = x, y, h
        for n, size, speed, alpha, col in self.SPEC:
            c = Color(*hexc(col)[:3], alpha)
            pts = []
            for _ in range(n):
                pts += [x + random.uniform(0, w), y + random.uniform(0, h)]
            pt = Point(points=pts, pointsize=dp(size) / 2)
            self.group.add(c)
            self.group.add(pt)
            self.layers.append([c, pt, pts, dp(speed), alpha])

    def update(self, dt, t):
        for i, (c, pt, pts, speed, alpha) in enumerate(self.layers):
            for j in range(1, len(pts), 2):
                yy = pts[j] - speed * dt
                if yy < self.y:
                    yy += self.h
                pts[j] = yy
            pt.points = pts
            c.a = alpha * (.78 + .22 * math.sin(t * (1.5 + i) + i * 2))


class SpaceBg(Widget):
    """Animated space background for menu screens (runs only while its screen is visible)."""

    def __init__(self, theme=0, **kw):
        super().__init__(**kw)
        self.theme = PLANETS[theme]
        self.g_bg, self.g_stars = InstructionGroup(), InstructionGroup()
        self.canvas.add(self.g_bg)
        self.canvas.add(self.g_stars)
        self.stars, self.ev, self.t = Starfield(self.g_stars), None, 0.0
        self.bind(pos=self.rebuild, size=self.rebuild)

    def rebuild(self, *a):
        if self.width < 2:
            return
        paint_background(self.g_bg, self.theme, self.x, self.y, self.width, self.height)
        self.stars.build(self.x, self.y, self.width, self.height)

    def start(self):
        if not self.ev:
            self.ev = Clock.schedule_interval(self.tick, 1 / 30)

    def stop(self):
        if self.ev:
            self.ev.cancel()
            self.ev = None

    def tick(self, dt):
        self.t += dt
        self.stars.update(dt, self.t)
