"""Static game data (pure Python, no Kivy): letters, words, planets/levels, badges."""
import random

LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
WORDS = {
    'A': 'Apple', 'B': 'Ball', 'C': 'Cat', 'D': 'Dog', 'E': 'Elephant', 'F': 'Fish',
    'G': 'Grapes', 'H': 'Hat', 'I': 'Ice cream', 'J': 'Juice', 'K': 'Kite', 'L': 'Lion',
    'M': 'Moon', 'N': 'Nest', 'O': 'Orange', 'P': 'Pig', 'Q': 'Queen', 'R': 'Rainbow',
    'S': 'Sun', 'T': 'Tree', 'U': 'Umbrella', 'V': 'Van', 'W': 'Whale', 'X': 'Xylophone',
    'Y': 'Yo-yo', 'Z': 'Zebra'}
LETTER_COLORS = ['#FF6B8B', '#FFB347', '#FFE066', '#6BE08C', '#4FC3F7', '#9B7BFF', '#FF8FD8', '#5EEAD4']

# Each planet = one level. 'letters' empty -> mixed review level.
# Adding a new planet/mode later only means adding an entry here.
PLANETS = [
    dict(name='Candy Moon', letters='ABCDE', top='#16105E', bottom='#5A2A9C',
         neb=['#FF5FA2', '#7C4DFF', '#29B6F6'], body='#FF8FB3', speed=36, targets=3),
    dict(name='Sunny Planet', letters='FGHIJ', top='#12206B', bottom='#7A3C9D',
         neb=['#FFB347', '#FF5FA2', '#29B6F6'], body='#FFD54F', speed=42, targets=4),
    dict(name='Jelly Planet', letters='KLMNO', top='#0F2A6B', bottom='#4A2C9E',
         neb=['#5EEAD4', '#7C4DFF', '#FF8FD8'], body='#7CE0A4', speed=48, targets=4),
    dict(name='Ice Planet', letters='PQRST', top='#0B1F5E', bottom='#2F4FB5',
         neb=['#4FE3FF', '#6C7BFF', '#FFFFFF'], body='#A6E3FF', speed=54, targets=5),
    dict(name='Rainbow Planet', letters='UVWXYZ', top='#1D0F5E', bottom='#8A2F9A',
         neb=['#FF5FA2', '#FFB347', '#4FE3FF'], body='#FF9A5A', speed=60, targets=5),
    dict(name='Galaxy Star', letters='', top='#0A0A3F', bottom='#3A1B8F',
         neb=['#FFD84D', '#FF5FA2', '#4FE3FF'], body='#FFD84D', speed=66, targets=6)]

BADGES = [  # id, name, description, colour
    ('first_hit', 'First Hit', 'Hit your first correct letter', '#FF6B8B'),
    ('level1', 'Planet Explorer', 'Finish Candy Moon', '#FFB347'),
    ('streak5', 'Sharp Shooter', '5 correct letters in a row', '#6BE08C'),
    ('stars10', 'Star Collector', 'Collect 10 stars', '#FFE066'),
    ('perfect', 'Perfect Mission', 'Finish a level with 3 stars', '#4FC3F7'),
    ('explorer', 'Letter Explorer', 'Look at 10 letters in Learn A-Z', '#9B7BFF'),
    ('abc', 'Alphabet Hero', 'Hit all 26 letters', '#FF8FD8'),
    ('galaxy', 'Galaxy Master', 'Finish every planet', '#5EEAD4')]


def letter_color(letter):
    return LETTER_COLORS[LETTERS.index(letter) % len(LETTER_COLORS)]


def make_missions(letters, reps):
    """Each letter `reps` times, shuffled, never the same letter twice in a row."""
    out = []
    for _ in range(reps):
        block = list(letters)
        random.shuffle(block)
        if out and len(block) > 1 and block[0] == out[-1]:
            block.append(block.pop(0))
        out += block
    return out


def level_config(n):
    p = PLANETS[n - 1]
    if p['letters']:
        letters = list(p['letters'])
        pool = list(LETTERS[:LETTERS.index(p['letters'][-1]) + 1])  # only letters seen so far
    else:
        letters, pool = random.sample(LETTERS, 8), list(LETTERS)
    return dict(kind='level', level=n, id='L%d' % n, name=p['name'], theme=n - 1,
                missions=make_missions(letters, 2), pool=pool, speed=p['speed'],
                max_targets=p['targets'], lives=3)


def mission_config(letter):
    others = random.sample([c for c in LETTERS if c != letter], 6)
    return dict(kind='mission', letter=letter, id='M' + letter, name='Letter ' + letter,
                theme=LETTERS.index(letter) % len(PLANETS), missions=[letter] * 5,
                pool=sorted(others + [letter]), speed=40, max_targets=4, lives=3)
