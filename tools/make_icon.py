"""Draws assets/icon.png and assets/presplash.png (pure Python, no dependencies).
Run:  python tools/make_icon.py"""
import math
import os
import struct
import zlib

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')


def write_png(path, size, rows):
    raw = b''.join(b'\x00' + bytes(r) for r in rows)

    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def star(cx, cy, R, r):
    return [(cx + (R if k % 2 == 0 else r) * math.cos(-math.pi / 2 + k * math.pi / 5),
             cy + (R if k % 2 == 0 else r) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(10)]


def inside(poly, x, y):
    c, n = False, len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def cover(poly, i, j, box):
    if not (box[0] <= i <= box[2] and box[1] <= j <= box[3]):
        return 0.0
    return sum(inside(poly, i + dx, j + dy) for dx in (.25, .75) for dy in (.25, .75)) / 4


def over(dst, rgb, a):
    da = dst[3] / 255
    oa = a + da * (1 - a)
    if oa <= 0:
        return dst
    return [(rgb[k] * a + dst[k] * da * (1 - a)) / oa for k in range(3)] + [oa * 255]


def render(size, with_bg):
    s = size
    poly = star(s * .5, s * .53, s * .36, s * .16)
    shadow = [(x + s * .012, y + s * .03) for x, y in poly]
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    box = (min(xs) - 2, min(ys) - 2, max(xs) + s * .03, max(ys) + s * .05)
    dots = ((.2, .2, .018), (.82, .16, .014), (.86, .78, .02), (.14, .8, .012))
    rows = []
    for j in range(size):
        row = bytearray()
        for i in range(size):
            if with_bg:
                t = j / s
                px = [11 + (90 - 11) * t, 16 + (42 - 16) * t, 51 + (156 - 51) * t, 255]
                g = max(0, 1 - math.hypot(i - s * .5, j - s * .5) / (s * .55)) ** 2 * .5
                px = over(px, (120, 90, 255), g)
            else:
                px = [0, 0, 0, 0]
            px = over(px, (5, 5, 40), .4 * cover(shadow, i, j, box))
            c = cover(poly, i, j, box)
            if c:
                f = (j - box[1]) / (box[3] - box[1])
                px = over(px, (255 - 0 * f, 220 - 55 * f, 80 - 40 * f), c)
            for fx, fy, fr in dots:
                d = math.hypot(i - fx * s, j - fy * s) - fr * s
                if d < 1:
                    px = over(px, (255, 255, 255), .85 * min(1, 1 - d))
            row += bytes(int(max(0, min(255, v))) for v in px)
        rows.append(row)
    return rows


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    write_png(os.path.join(OUT, 'icon.png'), 512, render(512, True))
    write_png(os.path.join(OUT, 'presplash.png'), 512, render(512, False))
    print('Wrote icon.png and presplash.png')
