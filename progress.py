"""ProgressManager: JSON save file (safe against missing/empty/corrupt files)."""
import json
import os

from data import BADGES, LETTERS, PLANETS

N_LEVELS = len(PLANETS)
BADGE_IDS = {b[0] for b in BADGES}


def _int(v, lo=0, hi=10 ** 9, default=0):
    if isinstance(v, int) and not isinstance(v, bool):
        return min(max(v, lo), hi)
    return default


class ProgressManager:
    def __init__(self, path):
        self.path = path
        self.data = self._default()
        self.load()

    @staticmethod
    def _default():
        return {'high_score': 0, 'points': 0, 'best_streak': 0, 'unlocked': 1,
                'levels': {}, 'missions': {}, 'letters': {}, 'viewed': [], 'badges': [],
                'settings': {'sfx': True, 'music': False, 'voice': True}}

    # ---- load / save ----
    def load(self):
        d = self._default()
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                self._merge(d, raw)
        except (OSError, ValueError):
            pass  # missing, empty or corrupted file -> start fresh
        self.data = d

    @staticmethod
    def _merge(d, raw):
        for k in ('high_score', 'points', 'best_streak'):
            d[k] = _int(raw.get(k))
        d['unlocked'] = _int(raw.get('unlocked'), 1, N_LEVELS, 1)
        for key, ok in (('levels', lambda k: k.isdigit() and 1 <= int(k) <= N_LEVELS),
                        ('missions', lambda k: len(k) == 1 and k in LETTERS)):
            src = raw.get(key)
            if isinstance(src, dict):
                for k, v in src.items():
                    if isinstance(k, str) and ok(k) and isinstance(v, dict):
                        d[key][k] = {'stars': _int(v.get('stars'), 0, 3), 'best': _int(v.get('best'))}
        src = raw.get('letters')
        if isinstance(src, dict):
            for k, v in src.items():
                if isinstance(k, str) and len(k) == 1 and k in LETTERS:
                    d['letters'][k] = _int(v)
        for key, ok in (('viewed', lambda x: isinstance(x, str) and len(x) == 1 and x in LETTERS),
                        ('badges', lambda x: x in BADGE_IDS)):
            src = raw.get(key)
            if isinstance(src, list):
                d[key] = [x for i, x in enumerate(src) if ok(x) and x not in src[:i]]
        src = raw.get('settings')
        if isinstance(src, dict):
            for k in d['settings']:
                if isinstance(src.get(k), bool):
                    d['settings'][k] = src[k]

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path) or '.', exist_ok=True)
            tmp = self.path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.data, f)
            os.replace(tmp, self.path)  # atomic: never leaves a half-written file
        except OSError:
            pass

    def reset(self):
        keep = dict(self.data['settings'])
        self.data = self._default()
        self.data['settings'] = keep
        self.save()

    # ---- settings ----
    def setting(self, name):
        return self.data['settings'][name]

    def set_setting(self, name, value):
        self.data['settings'][name] = bool(value)
        self.save()

    # ---- queries ----
    @property
    def total_stars(self):
        return sum(v['stars'] for v in self.data['levels'].values()) + \
            sum(v['stars'] for v in self.data['missions'].values())

    def level_stars(self, n):
        return self.data['levels'].get(str(n), {}).get('stars', 0)

    def is_unlocked(self, n):
        return n <= self.data['unlocked']

    def next_level(self):
        for n in range(1, self.data['unlocked'] + 1):
            if str(n) not in self.data['levels']:
                return n
        return N_LEVELS

    def letters_learned(self):
        return sum(1 for v in self.data['letters'].values() if v > 0)

    # ---- updates ----
    def add_viewed(self, letter):
        if letter not in self.data['viewed']:
            self.data['viewed'].append(letter)
            new = self._award()
            self.save()
            return new
        return []

    def finish_run(self, cfg, res):
        """Store the result of a finished (or failed) run; returns newly earned badge ids."""
        d = self.data
        d['points'] += res['score']
        d['high_score'] = max(d['high_score'], res['score'])
        d['best_streak'] = max(d['best_streak'], res['best_streak'])
        for l in res['hit_letters']:
            d['letters'][l] = d['letters'].get(l, 0) + 1
        if res['success']:
            is_level = cfg['kind'] == 'level'
            store = d['levels'] if is_level else d['missions']
            key = str(cfg['level']) if is_level else cfg['letter']
            old = store.get(key, {'stars': 0, 'best': 0})
            store[key] = {'stars': max(old['stars'], res['stars']), 'best': max(old['best'], res['score'])}
            if is_level:
                d['unlocked'] = min(N_LEVELS, max(d['unlocked'], cfg['level'] + 1))
        new = self._award()
        self.save()
        return new

    def _award(self):
        d = self.data
        got = {
            'first_hit': any(v > 0 for v in d['letters'].values()),
            'level1': '1' in d['levels'],
            'streak5': d['best_streak'] >= 5,
            'stars10': self.total_stars >= 10,
            'perfect': any(v['stars'] >= 3 for v in d['levels'].values()),
            'explorer': len(d['viewed']) >= 10,
            'abc': self.letters_learned() >= 26,
            'galaxy': len(d['levels']) >= N_LEVELS}
        new = [b for b, ok in got.items() if ok and b not in d['badges']]
        d['badges'] += new
        return new
