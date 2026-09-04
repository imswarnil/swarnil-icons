#!/usr/bin/env python3
"""build.py — turn icons/ into everything a consumer can use.

    dist/
      sprite.svg              one <symbol> per icon; one request for the set
      swarnil-icons.css       sizing, variants, alignment
      icons.json              the index the docs site and any tool reads
      svg/<variant>/<n>.svg   standalone files, one per variant

Variants are GENERATED from one source path, never redrawn, so `bold` cannot
drift away from `line`. That is the whole reason the geometry lives in one file.

    python3 scripts/build.py
"""
import json
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
ICONS = ROOT / 'icons'
DIST = ROOT / 'dist'

# name -> the stroke weight it renders at. `duo` is a weight plus a second,
# faded pass; `solid` is not a weight at all and is handled separately.
STROKE_VARIANTS = {'thin': '1', 'line': '1.5', 'bold': '2'}

BODY = re.compile(r'<svg[^>]*>(.*)</svg>', re.S)
CLOSED = re.compile(r'[zZ]\s*$')


def body_of(src):
    m = BODY.search(src)
    return m.group(1) if m else ''


def is_fillable(body):
    """Can this icon have a MECHANICALLY generated solid variant?

    Only if every path is closed. Filling an open path — an arrow, a chevron —
    produces a blob, not an icon. STYLE.md says solid cannot be purely
    mechanical; this is where that is decided rather than assumed.
    """
    paths = re.findall(r'<path d="([^"]+)"', body)
    if not paths and '<circle' in body:
        return True
    return bool(paths) and all(CLOSED.search(p) for p in paths)


def wrap(body, stroke):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" '
            f'stroke-linejoin="round">{body}</svg>\n')


def main():
    files = sorted(ICONS.rglob('*.svg'))
    if not files:
        print('no icons — run scripts/author.py first')
        return 1

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    index, symbols, no_solid = [], [], []

    for f in files:
        name, cat = f.stem, f.parent.name
        body = body_of(f.read_text())

        symbols.append(f'<symbol id="i-{name}" viewBox="0 0 24 24">{body}</symbol>')

        fillable = is_fillable(body)
        if not fillable:
            no_solid.append(name)

        variants = list(STROKE_VARIANTS)
        if fillable:
            variants.append('solid')
        variants.append('duo')

        index.append({'name': name, 'category': cat, 'body': body, 'variants': variants})

        for v, w in STROKE_VARIANTS.items():
            out = DIST / 'svg' / v
            out.mkdir(parents=True, exist_ok=True)
            (out / f'{name}.svg').write_text(wrap(body, w))

        if fillable:
            out = DIST / 'svg' / 'solid'
            out.mkdir(parents=True, exist_ok=True)
            solid = body.replace('<path d=', '<path fill="currentColor" stroke="none" d=')
            solid = re.sub(r'<circle (?![^>]*fill=)', '<circle fill="currentColor" stroke="none" ', solid)
            (out / f'{name}.svg').write_text(wrap(solid, '1.5'))

    (DIST / 'sprite.svg').write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" style="display:none">'
        + ''.join(symbols) + '</svg>\n')

    (DIST / 'icons.json').write_text(json.dumps(
        {'version': 1, 'grid': 24, 'count': len(index), 'icons': index},
        separators=(',', ':')))

    (DIST / 'swarnil-icons.css').write_text(CSS)

    cats = sorted({i['category'] for i in index})
    print(f'built {len(index)} icons · {len(cats)} categories · '
          f'{len(STROKE_VARIANTS) + 1} variants -> dist/')
    if no_solid:
        # Reported, not hidden. An open path cannot be filled mechanically, and
        # pretending otherwise would ship 20 blobs.
        print(f'  {len(no_solid)} icons have no solid variant (open paths — '
              f'a solid needs its own declared geometry):')
        print('    ' + ', '.join(no_solid))
    return 0


CSS = """/* =============================================================================
   SWARNIL ICONS
   A 24-grid stroked icon set. Colour comes from currentColor, so an icon
   inherits the text it sits beside and never needs a theme of its own.

   Use the sprite (one request for the whole set):

       <svg class="ic"><use href="/sprite.svg#i-camera"/></svg>

   or a standalone file, or inline the markup. All three are the same geometry.

   Docs: https://icons.imswarnil.com
   ========================================================================== */

.ic {
	--ic-size: 1.25rem;
	--ic-stroke: 1.5;
	inline-size: var(--ic-size);
	block-size: var(--ic-size);
	flex: none;
	fill: none;
	stroke: currentColor;
	stroke-width: var(--ic-stroke);
	stroke-linecap: round;
	stroke-linejoin: round;
}

/* ── Size ─────────────────────────────────────────────────────────────────
   The set is drawn on a 24 grid but sized in rem, so it scales with the text
   rather than with the viewport. */

.ic-xs { --ic-size: 0.875rem; }   /* 14px */
.ic-sm { --ic-size: 1rem; }       /* 16px — the floor every icon is checked at */
.ic-md { --ic-size: 1.25rem; }    /* 20px */
.ic-lg { --ic-size: 1.5rem; }     /* 24px — the drawn size */
.ic-xl { --ic-size: 2rem; }       /* 32px */
.ic-2xl { --ic-size: 3rem; }      /* 48px */

/* ── Weight ───────────────────────────────────────────────────────────────
   One geometry, three weights. Nothing is redrawn, so they cannot drift.

   The stroke does NOT scale with the icon, which is deliberate: a 48px icon
   with a proportionally scaled stroke reads as a fat 24px icon rather than as
   a large one. Pick the weight for the size. */

.ic-thin { --ic-stroke: 1; }
.ic-line { --ic-stroke: 1.5; }
.ic-bold { --ic-stroke: 2; }

/* ── Solid ────────────────────────────────────────────────────────────────
   Only for icons whose paths are closed. An open path — an arrow, a chevron —
   filled is a blob, so those icons have no solid variant rather than a bad
   one. build.py lists which. */

.ic-solid { fill: currentColor; stroke: none; }

/* ── Duo ──────────────────────────────────────────────────────────────────
   The whole icon at reduced opacity with the first path at full strength.
   For large decorative use, where a flat single weight looks thin. */

.ic-duo { opacity: 0.4; }
.ic-duo > :first-child { opacity: 2.5; }

/* ── Alignment ────────────────────────────────────────────────────────────
   An icon beside text sits a hair high, because the cap height of the text is
   shorter than the icon's box. This is the correction, and it is why icons in
   this set look seated rather than floating. */

.ic-inline {
	display: inline-block;
	vertical-align: -0.125em;
}

/* Colour helpers — the icon inherits currentColor, so these are just text
   colour. Included because "how do I colour an icon" is the first question. */

.ic-accent { color: var(--accent, currentColor); }
.ic-muted  { color: var(--fg-muted, currentColor); }

@media (prefers-reduced-motion: reduce) {
	.ic { transition: none; }
}
"""


if __name__ == '__main__':
    raise SystemExit(main())
