#!/usr/bin/env python3
"""validate.py — make STYLE.md executable.

A style guide nobody can run is a wish. This walks every icon's actual geometry
and fails the build on a rule break, so "consistent" is a property of the set
rather than a claim about it.

    python3 scripts/validate.py            report
    python3 scripts/validate.py --strict   exit 1 on any error (CI)

Rules, in STYLE.md order:
  1  viewBox is exactly "0 0 24 24"
  2  geometry sits inside the 2…22 live area (circles may overshoot to 1.5)
  3  stroke-width is one of the declared weights
  4  fill="none" on the root; no hard-coded colour anywhere
  5  horizontal and vertical lines sit on whole coordinates
  6  no <style>, class or id — an icon is geometry, not a stylesheet
  7  filename is kebab-case
"""
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ICONS = ROOT / 'icons'

LIVE_MIN, LIVE_MAX = 2.0, 22.0
CIRCLE_OVERSHOOT = 1.5          # a circle may reach 0.5 … 23.5
WEIGHTS = {'1', '1.5', '2'}
KEBAB = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
NUM = re.compile(r'-?\d*\.?\d+(?:e-?\d+)?')
CMD = re.compile(r'([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)')
COLOUR = re.compile(r'(#[0-9a-fA-F]{3,8}\b|\brgb\(|\bhsl\(|\boklch\()')


def nums(s):
    return [float(n) for n in NUM.findall(s)]


def walk(d):
    """Yield (x, y, is_orthogonal_h, is_orthogonal_v) for every point a path
    reaches. Curves contribute their control points too — a control point
    outside the live area usually means the curve bulges outside it, and
    catching that is the whole reason to walk the path rather than regex it."""
    x = y = 0.0
    sx = sy = 0.0
    for cmd, raw in CMD.findall(d):
        a = nums(raw)
        rel = cmd.islower()
        c = cmd.upper()

        if c == 'Z':
            x, y = sx, sy
            yield x, y, False, False
            continue

        if c == 'M':
            for i in range(0, len(a) - 1, 2):
                x = x + a[i] if rel else a[i]
                y = y + a[i + 1] if rel else a[i + 1]
                if i == 0:
                    sx, sy = x, y
                yield x, y, False, False
        elif c == 'L':
            for i in range(0, len(a) - 1, 2):
                x = x + a[i] if rel else a[i]
                y = y + a[i + 1] if rel else a[i + 1]
                yield x, y, False, False
        elif c == 'H':
            for v in a:
                x = x + v if rel else v
                yield x, y, True, False      # horizontal: y must be whole
        elif c == 'V':
            for v in a:
                y = y + v if rel else v
                yield x, y, False, True      # vertical: x must be whole
        elif c in 'CS':
            step = 6 if c == 'C' else 4
            for i in range(0, len(a) - step + 1, step):
                seg = a[i:i + step]
                for j in range(0, len(seg) - 1, 2):
                    px = x + seg[j] if rel else seg[j]
                    py = y + seg[j + 1] if rel else seg[j + 1]
                    yield px, py, False, False
                x = x + seg[-2] if rel else seg[-2]
                y = y + seg[-1] if rel else seg[-1]
        elif c in 'QT':
            step = 4 if c == 'Q' else 2
            for i in range(0, len(a) - step + 1, step):
                seg = a[i:i + step]
                for j in range(0, len(seg) - 1, 2):
                    px = x + seg[j] if rel else seg[j]
                    py = y + seg[j + 1] if rel else seg[j + 1]
                    yield px, py, False, False
                x = x + seg[-2] if rel else seg[-2]
                y = y + seg[-1] if rel else seg[-1]
        elif c == 'A':
            for i in range(0, len(a) - 6, 7):
                x = x + a[i + 5] if rel else a[i + 5]
                y = y + a[i + 6] if rel else a[i + 6]
                yield x, y, False, False


def whole(v):
    return math.isclose(v, round(v), abs_tol=1e-6)


def check(path):
    src = path.read_text()
    name = path.stem
    errs = []

    # 7 · naming
    if not KEBAB.match(name):
        errs.append(f'filename "{name}" is not kebab-case')

    # 1 · viewBox
    vb = re.search(r'viewBox="([^"]+)"', src)
    if not vb or vb.group(1).strip() != '0 0 24 24':
        errs.append(f'viewBox is {vb.group(1) if vb else "missing"}, must be "0 0 24 24"')

    # 6 · no stylesheet hooks
    for bad in ('<style', ' class=', ' id='):
        if bad in src:
            errs.append(f'contains {bad.strip()} — an icon is geometry, not a stylesheet')

    # 4 · colour
    if 'fill="none"' not in src:
        errs.append('root must carry fill="none"')
    if COLOUR.search(src):
        errs.append('hard-coded colour — the set inherits currentColor')

    # 3 · stroke weight
    for w in re.findall(r'stroke-width="([^"]+)"', src):
        if w not in WEIGHTS:
            errs.append(f'stroke-width {w} is not one of {sorted(WEIGHTS)}')

    # 2 · live area + 5 · orthogonal coordinates
    for d in re.findall(r'\sd="([^"]+)"', src):
        for x, y, is_h, is_v in walk(d):
            if not (LIVE_MIN <= x <= LIVE_MAX and LIVE_MIN <= y <= LIVE_MAX):
                errs.append(f'point ({x:g},{y:g}) is outside the {LIVE_MIN:g}…{LIVE_MAX:g} live area')
                break
        for x, y, is_h, is_v in walk(d):
            if is_h and not whole(y):
                errs.append(f'horizontal line at y={y:g} — orthogonal strokes sit on whole coordinates')
                break
            if is_v and not whole(x):
                errs.append(f'vertical line at x={x:g} — orthogonal strokes sit on whole coordinates')
                break

    for cx, cy, r in re.findall(r'<circle cx="([^"]+)" cy="([^"]+)" r="([^"]+)"', src):
        cx, cy, r = float(cx), float(cy), float(r)
        lo, hi = LIVE_MIN - CIRCLE_OVERSHOOT, LIVE_MAX + CIRCLE_OVERSHOOT
        if not (lo <= cx - r and cx + r <= hi and lo <= cy - r and cy + r <= hi):
            errs.append(f'circle ({cx:g},{cy:g}) r={r:g} exceeds the live area even with overshoot')

    return errs


def main():
    strict = '--strict' in sys.argv
    files = sorted(ICONS.rglob('*.svg'))
    if not files:
        print('no icons found — run scripts/author.py first')
        return 1

    bad = {}
    for f in files:
        e = check(f)
        if e:
            bad[f] = e

    if not bad:
        print(f'style audit: clean — {len(files)} icons, every rule in STYLE.md holds')
        return 0

    print(f'style audit: {sum(len(v) for v in bad.values())} problem(s) in {len(bad)} of {len(files)} icons\n')
    for f, errs in bad.items():
        print(f'  {f.relative_to(ROOT)}')
        for e in errs:
            print(f'      {e}')
        print()
    return 1 if strict else 0


if __name__ == '__main__':
    sys.exit(main())
