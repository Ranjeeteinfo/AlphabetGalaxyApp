"""Generates simple, soft placeholder sound effects + a music loop (pure Python, no deps).

Run:  python tools/make_sounds.py
Writes WAV files into assets/audio/. Replace them with your own recordings any time
(same names; .ogg/.wav/.mp3 all work). Letter pronunciations are NOT generated -
see assets/README.txt.
"""
import math
import os
import random
import struct
import wave

SR = 22050
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'audio')


def save(name, samples):
    os.makedirs(OUT, exist_ok=True)
    with wave.open(os.path.join(OUT, name + '.wav'), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, s)) * 30000)) for s in samples))


def tone(freq, dur, vol=.5, attack=.008, decay=6.0, f_end=None, harm=.25):
    """Sine (+octave) with fast attack, exponential decay and optional pitch sweep."""
    n, ph, out = int(SR * dur), 0.0, []
    for i in range(n):
        f = freq if f_end is None else freq + (f_end - freq) * i / n
        ph += 2 * math.pi * f / SR
        t = i / SR
        env = min(1, t / attack) * math.exp(-decay * t) * min(1, (dur - t) / .01)
        out.append(vol * env * (math.sin(ph) + harm * math.sin(2 * ph)))
    return out


def mix(parts):
    n = max(len(p) for p in parts)
    return [sum(p[i] for p in parts if i < len(p)) * .6 for i in range(n)]


def delayed(samples, sec):
    return [0.0] * int(SR * sec) + samples


C5, E5, G5, C6, E6, G6, G4, E4 = 523.25, 659.25, 783.99, 1046.5, 1318.5, 1568.0, 392.0, 329.63

save('laser', tone(1500, .15, .35, decay=9, f_end=520, harm=.4))
save('click', tone(880, .06, .4, decay=30))
save('correct', mix([delayed(tone(f, .35, .4, decay=7), i * .08) for i, f in enumerate((C5, E5, G5, C6))]))
save('wrong', mix([tone(G4, .28, .35, decay=5, harm=.1), delayed(tone(E4, .4, .35, decay=4, harm=.1), .2)]))
save('level', mix([delayed(tone(f, .5 if i < 5 else 1.0, .35, decay=3.5), i * .13)
                   for i, f in enumerate((C5, E5, G5, C6, E6, G6))]))

# Gentle 8 s music loop: soft pad chords + sparse pentatonic notes; every part fades to 0 at the loop point.
random.seed(7)
chords = [(261.63, 329.63, 392.0), (220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (196.0, 246.94, 293.66)]
pent = [523.25, 587.33, 659.25, 783.99, 880.0]
total = int(SR * 8)
music = [0.0] * total
seg = SR * 2
for ci, chord in enumerate(chords):
    for i in range(seg):
        t = i / SR
        env = math.sin(math.pi * i / seg) ** 2
        music[ci * seg + i] += .22 * env * sum(math.sin(2 * math.pi * f * t) for f in chord) / 3
for k in range(12):
    start = int(SR * (k * .6 + .1))
    for i, s in enumerate(tone(random.choice(pent), .5, .16, decay=5)):
        if start + i < total - int(SR * .2):
            music[start + i] += s
save('music', music)
print('Wrote sounds to', os.path.abspath(OUT))
