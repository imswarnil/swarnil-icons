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


SUBPATH = re.compile(r'M[^M]*')
PATH_EL = re.compile(r'<path((?:(?!/>)[^>])*?)\sd="([^"]+)"\s*/>')
MEASURABLE = re.compile(r'<(path|circle)\b(?![^>]*pathLength)')


def split_paths(body):
    """One <path> per subpath, so the parts of an icon can be styled apart.

    Most icons in this set are authored as a SINGLE path whose `d` happens to
    contain several subpaths — `M6 4h8l5 5v11H6zM14 4v5h5` is a page and the
    fold on its corner, in one element. Rendered, that is exactly right. But it
    means CSS sees one child where a reader sees two shapes, and a multicolour
    or staggered style has nothing to take hold of: two thirds of the set would
    only ever be one colour.

    Splitting on absolute M is lossless — the same commands, redistributed —
    so every stroke lands on the same pixel it did before. Only the number of
    elements changes, which is the point.

    Deliberately conservative: it splits only when the data starts with an
    absolute M and the parts rejoin to exactly the original string. A relative
    `m` continues from the previous point, so it is left inside its subpath
    rather than promoted to one; the worst case is a split that does not
    happen, never a shape that moves.
    """
    def one(m):
        attrs, d = m.group(1), m.group(2)
        if not d.startswith('M'):
            return m.group(0)
        parts = SUBPATH.findall(d)
        if len(parts) < 2 or ''.join(parts) != d:
            return m.group(0)
        return ''.join(f'<path{attrs} d="{p.strip()}"/>' for p in parts)

    return PATH_EL.sub(one, body)


def measured(body):
    """Stamp pathLength="1" onto every drawable element.

    This is what lets a stroke-draw animation be pure CSS. Drawing a line on is
    stroke-dasharray plus a dashoffset that animates to zero, and both are in
    USER UNITS — so without this you must measure each path with
    getTotalLength() in JavaScript and write the number back, per icon, at
    runtime. pathLength="1" redefines the path's own length as 1, so
    `stroke-dasharray: 1; stroke-dashoffset: 1` means "completely hidden" for
    every icon in the set regardless of its actual geometry, and one CSS rule
    animates all 61.

    It changes nothing else. pathLength is inert unless something asks for a
    dash pattern or a marker interval.
    """
    return MEASURABLE.sub(r'<\1 pathLength="1"', body)


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
        # RAW first, MEASURED second, and the order matters. is_fillable and
        # the solid generation below both match on `<path d="`, so they have
        # to see the geometry before pathLength is inserted between the tag
        # name and the d attribute — otherwise every path stops matching, no
        # icon looks fillable, and the whole set silently loses its solid
        # variant. The source file itself is never touched either way.
        raw = body_of(f.read_text())
        body = measured(split_paths(raw))

        symbols.append(f'<symbol id="i-{name}" viewBox="0 0 24 24">{body}</symbol>')

        fillable = is_fillable(raw)
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
            solid = raw.replace('<path d=', '<path fill="currentColor" stroke="none" d=')
            solid = re.sub(r'<circle (?![^>]*fill=)', '<circle fill="currentColor" stroke="none" ', solid)
            (out / f'{name}.svg').write_text(wrap(measured(split_paths(solid)), '1.5'))

    (DIST / 'sprite.svg').write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" style="display:none">'
        + ''.join(symbols) + '</svg>\n')

    (DIST / 'icons.json').write_text(json.dumps(
        {'version': 1, 'grid': 24, 'count': len(index), 'icons': index},
        separators=(',', ':')))

    (DIST / 'swarnil-icons.css').write_text(CSS)
    (DIST / 'swarnil-icons-motion.css').write_text(MOTION)

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
   inherits the text it sits beside and never needs a theme of its own — and
   when you want it to carry the brand instead, .ic-primary reads the design
   system's --accent. See the Colour section at the foot of this file.

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
	fill: var(--ic-fill, none);
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

.ic-solid { --ic-fill: currentColor; stroke: none; }

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

/* ── Colour ───────────────────────────────────────────────────────────────
   Two questions, and the second one is why this section exists.

   "Match the text it sits beside."  Do nothing — currentColor already does.
   "Make it the brand colour."       .ic-primary. And the solid variant fills
                                     with that colour too, because every helper
                                     below sets `color` rather than `stroke`,
                                     so stroke and fill move together and a
                                     line icon and its solid never disagree.

   ── WHERE THE VALUES COME FROM ────────────────────────────────────────────
   Every token reads the Swarnil Design System's token FIRST and falls back to
   the same value written out:

       --ic-primary: var(--accent, oklch(63% 0.190 34));

   So one stylesheet does both jobs. Load the design system and the icons
   inherit its --accent — repoint that one line and the icons rebrand with
   everything else, with no build step and no import. Load nothing at all and
   they still render in the system's own signal red, because the fallback IS
   the design system's value, copied.

   That copy is deliberate. A real dependency would make this package
   undeployable on its own, and a made-up default would be a second palette
   quietly drifting away from the first. Copying the value keeps the set
   standalone AND in the same visual language. The source SVGs stay
   colourless (validate.py enforces it) — colour is only ever this layer.

   ── DARK ──────────────────────────────────────────────────────────────────
   The light-dark() pairs below need a color-scheme to choose from. Declare it
   once on your root and the muted/semantic tones follow the theme:

       :root { color-scheme: light dark; }

   Without it every pair resolves to its light value, which is correct, just
   not adaptive. --ic-primary is one colour in both themes by design: the
   accent is the brand, and a brand that shifts hue between themes is two
   brands. */

/* On :root rather than on .ic, so a WRAPPER can carry the colour class —
   `<button class="ic-primary">` tinting the icon inside it — and so anything
   else on the page can read the same values. Every name is --ic- prefixed;
   nothing here can collide with yours. */

:root {
	--ic-primary:      var(--accent,     oklch(63% 0.190 34));
	--ic-primary-soft: var(--accent-soft, light-dark(oklch(96.5% 0.020 34), oklch(63% 0.19 34 / 0.16)));
	--ic-ink:          var(--fg-default, light-dark(oklch(23% 0.016 275), oklch(96.6% 0.004 275)));
	--ic-muted:        var(--fg-muted,   light-dark(oklch(39% 0.020 275), oklch(82% 0.009 275)));
	--ic-subtle:       var(--fg-subtle,  light-dark(oklch(48% 0.020 275), oklch(71% 0.013 275)));

	/* Status, on the design system's shared lightness ladder — so no state
	   reads louder than another purely because of its hue. */
	--ic-success: var(--success-fg, light-dark(oklch(46% 0.100 155), oklch(82% 0.105 155)));
	--ic-info:    var(--info-fg,    light-dark(oklch(46% 0.130 240), oklch(82% 0.090 240)));
	--ic-warning: var(--warning-fg, light-dark(oklch(48% 0.085 78),  oklch(82% 0.110 78)));
	--ic-danger:  var(--danger-fg,  light-dark(oklch(45% 0.160 15),  oklch(82% 0.090 15)));
}

/* The helpers. Each sets `color`, so it drives the stroke, the solid fill and
   any text in the same element at once. */

.ic-primary { color: var(--ic-primary); }
.ic-accent  { color: var(--ic-primary); }   /* the name this shipped under */
.ic-ink     { color: var(--ic-ink); }
.ic-muted   { color: var(--ic-muted); }
.ic-subtle  { color: var(--ic-subtle); }

.ic-success { color: var(--ic-success); }
.ic-info    { color: var(--ic-info); }
.ic-warning { color: var(--ic-warning); }
.ic-danger  { color: var(--ic-danger); }

/* Back to inheriting, for overriding a colour set further up. */
.ic-current { color: inherit; }

/* ── Multicolour ──────────────────────────────────────────────────────────
   Three colours out of one geometry: BLACK strokes, the PRIMARY on the marks
   that already carry meaning, and a LIGHT PRIMARY wash inside closed shapes.

   The trick is that it works through <use>. A sprite reference has one child,
   so no child selector can reach the parts inside it — but `stroke`, `fill`
   and `color` are all INHERITED, and the set already distinguishes its two
   kinds of geometry by hand: strokes are plain, while the deliberate marks
   (the record dot, the aperture centre, the alert full stop) are authored as
   fill="currentColor". So:

       stroke        -> ink        every drawn line
       color         -> primary    every filled mark, via its currentColor
       --ic-fill     -> soft       the wash, on shapes that enclose an area

   An element's own presentation attribute beats an inherited value, which is
   what keeps the marks on `color` while everything else takes the wash.

   The wash is a SEPARATE class because it is the one part that is not
   universally safe: filling an open path floods the region the path merely
   implies, and half this set is open paths. Pair it with a closed icon — the
   same ones that have a solid variant. */

.ic-multi {
	stroke: var(--ic-ink);
	color: var(--ic-primary);
}

/* The second colour, on the parts of the icon after the first. build.py emits
   one element per subpath precisely so this rule has something to hold: the
   page and its folded corner, the tray and its lid, the arrow's shaft and its
   head. 47 of the 61 icons have two or more parts.

   Child selectors cannot cross into the shadow content of a <use>, so this
   line applies to INLINE markup — what the site serves and what "Copy SVG"
   gives you. A sprite reference still gets the ink stroke, the primary marks
   and the wash from the inherited properties above; it just does not get this
   fourth touch. */
.ic-multi > :not(:first-child) { stroke: var(--ic-primary); }

/* Both, deliberately. --ic-fill is the composable hook that .ic reads, and
   the plain `fill` is what makes this work on a bare <svg> that never took the
   .ic class — a presentation attribute like fill="none" on the root loses to
   any CSS property, so the wash lands either way. */
.ic-multi-fill {
	--ic-fill: var(--ic-primary-soft);
	fill: var(--ic-primary-soft);
}

/* ── Scanline ─────────────────────────────────────────────────────────────
   The set sits beside a design system whose identity is a viewfinder and a
   record light, so the one decorative device that belongs here is the one a
   screen already makes: a raster line.

   It is a MASK, not geometry. Nothing is redrawn, so an icon in this style is
   the same icon — which is the same promise the five weights make.

   The stops are percentages, and that is the whole trick: percentages in a
   repeating gradient resolve against the element's own height, so this is
   always EIGHT lines whether the icon is rendered at 16px or 160px. A fixed
   pixel pitch would give you eight lines at one size and a grey smear at
   another.

   Being a mask, it cuts the strokes as well as the fills, which reads as
   deliberate at 24px and up and as broken below it. It is a display style —
   pair it with .ic-lg or larger, or with a fill. */

.ic-scan {
	-webkit-mask-image: repeating-linear-gradient(to bottom, #000 0 6.25%, transparent 6.25% 12.5%);
	        mask-image: repeating-linear-gradient(to bottom, #000 0 6.25%, transparent 6.25% 12.5%);
}

/* ── Two-tone ─────────────────────────────────────────────────────────────
   Stroke and fill pulled apart: the outline stays ink while the shape carries
   a wash of the accent. It is the one way to use colour on a stroked icon
   without shouting, and it only works on icons whose paths are CLOSED — the
   same ones that have a solid variant. On an open path the wash leaks out of
   the shape, so pair it with a closed icon or leave it off.

   These come after .ic-solid so `.ic-solid.ic-fill-primary` is a solid in the
   brand colour rather than a fight over one custom property. */

.ic-fill-primary { --ic-fill: var(--ic-primary); }
.ic-fill-soft    { --ic-fill: var(--ic-primary-soft); }
.ic-fill-current { --ic-fill: currentColor; }
.ic-fill-none    { --ic-fill: none; }

/* Anything else: set the property directly. This is the escape hatch, and it
   is a custom property rather than a class so it works inline, per instance.

       <svg class="ic ic-lg" style="color: var(--brand); --ic-fill: var(--brand-wash)">
*/

@media (prefers-reduced-motion: reduce) {
	.ic { transition: none; }
}
"""


MOTION = """/* =============================================================================
   SWARNIL ICONS · MOTION
   Five ways an icon can move, each with an in, an out and a loop.

       <link rel="stylesheet" href="swarnil-icons.css">
       <link rel="stylesheet" href="swarnil-icons-motion.css">

       <svg class="ic ic-lg ic-draw-in"><use href="/sprite.svg#i-heart"/></svg>

   ── THE MATRIX ────────────────────────────────────────────────────────────
     draw    the stroke draws itself on, like a pen
     fade    opacity, with a small rise
     pop     scale with an overshoot — the one for a confirmation
     spin    rotation
     pulse   a slow breath, for something that is waiting
     glitch  a signal dropping out for two frames and recovering

   times three:  -in    plays once and ends VISIBLE
                 -out   plays once and ends HIDDEN
                 -loop  repeats forever

   So: .ic-draw-in, .ic-draw-out, .ic-draw-loop, .ic-fade-in … fifteen classes.

   ── TIMING ────────────────────────────────────────────────────────────────
   Four custom properties, set anywhere — a theme, a component, one element:

       --ic-dur      600ms   how long
       --ic-delay    0ms     before starting
       --ic-ease             the curve
       --ic-stagger  90ms    gap between parts, inline SVG only (see below)

       <svg class="ic ic-lg ic-draw-in" style="--ic-dur: 1.2s">

   ── HOW DRAW WORKS, AND WHY IT NEEDS NO JAVASCRIPT ────────────────────────
   Drawing a line on means animating stroke-dashoffset from "the whole length"
   to zero — and length is in user units, so normally you measure every path
   with getTotalLength() and write the number back per icon at runtime.

   build.py stamps pathLength="1" on every path and circle in the set instead,
   which redefines each one's length as 1. `stroke-dashoffset: 1` is then
   "fully hidden" for every icon regardless of its real geometry, and the two
   rules below animate all of them.

   The dash properties are INHERITED, which is what makes this work through
   <use>: the rule sits on the <svg> and the value reaches the shadow content
   of a sprite reference, where a child selector could never go.

   Draw needs a stroke to draw, so it does nothing on .ic-solid.

   ── REPLAYING ─────────────────────────────────────────────────────────────
   A CSS animation runs when the class arrives. It plays on load; to play it
   again, take the class off and put it back:

       el.classList.remove('ic-pop-in');
       void el.offsetWidth;              // forces the restyle
       el.classList.add('ic-pop-in');

   Docs: https://icons.imswarnil.com
   ========================================================================== */

.ic-draw-in, .ic-draw-out, .ic-draw-loop,
.ic-fade-in, .ic-fade-out, .ic-fade-loop,
.ic-pop-in, .ic-pop-out, .ic-pop-loop,
.ic-spin-in, .ic-spin-out, .ic-spin-loop,
.ic-pulse-in, .ic-pulse-out, .ic-pulse-loop,
.ic-glitch-in, .ic-glitch-out, .ic-glitch-loop {
	animation-duration: var(--ic-dur, 600ms);
	animation-delay: var(--ic-delay, 0ms);
	animation-timing-function: var(--ic-ease, cubic-bezier(0.65, 0, 0.35, 1));
	animation-fill-mode: both;
	transform-origin: center;
}

/* ── Draw ─────────────────────────────────────────────────────────────────
   dasharray 1 = one dash the length of the whole path, so the offset is the
   only thing that has to move. */

.ic-draw-in, .ic-draw-out, .ic-draw-loop { stroke-dasharray: 1; }

.ic-draw-in   { animation-name: ic-draw-in; }
.ic-draw-out  { animation-name: ic-draw-out; }
.ic-draw-loop { animation-name: ic-draw-loop; animation-iteration-count: infinite; animation-duration: var(--ic-dur, 2.4s); }

@keyframes ic-draw-in  { from { stroke-dashoffset: 1; } to { stroke-dashoffset: 0; } }
/* Out runs the offset PAST zero to -1, so the line leaves from the end it was
   heading towards rather than reversing back the way it came. */
@keyframes ic-draw-out { from { stroke-dashoffset: 0; } to { stroke-dashoffset: -1; } }
@keyframes ic-draw-loop {
	0%, 4%    { stroke-dashoffset: 1; }
	46%, 64%  { stroke-dashoffset: 0; }
	100%      { stroke-dashoffset: -1; }
}

/* ── Fade ─────────────────────────────────────────────────────────────────── */

.ic-fade-in   { animation-name: ic-fade-in; }
.ic-fade-out  { animation-name: ic-fade-out; }
.ic-fade-loop { animation-name: ic-fade-loop; animation-iteration-count: infinite; animation-duration: var(--ic-dur, 1.8s); }

@keyframes ic-fade-in   { from { opacity: 0; transform: translateY(0.15em); } to { opacity: 1; transform: none; } }
@keyframes ic-fade-out  { from { opacity: 1; transform: none; } to { opacity: 0; transform: translateY(-0.15em); } }
@keyframes ic-fade-loop { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

/* ── Pop ──────────────────────────────────────────────────────────────────
   The overshoot is the point — this is the one for "saved", "sent", "done".
   Loop is a bump on a long pause rather than a constant throb, because a
   confirmation shape that never stops moving reads as an error. */

.ic-pop-in   { animation-name: ic-pop-in; }
.ic-pop-out  { animation-name: ic-pop-out; }
.ic-pop-loop { animation-name: ic-pop-loop; animation-iteration-count: infinite; animation-duration: var(--ic-dur, 2.6s); animation-timing-function: ease-in-out; }

@keyframes ic-pop-in {
	0%   { opacity: 0; transform: scale(0.5); }
	60%  { opacity: 1; transform: scale(1.08); }
	100% { opacity: 1; transform: scale(1); }
}
@keyframes ic-pop-out {
	0%   { opacity: 1; transform: scale(1); }
	30%  { opacity: 1; transform: scale(1.08); }
	100% { opacity: 0; transform: scale(0.5); }
}
@keyframes ic-pop-loop {
	0%, 70%, 100% { transform: scale(1); }
	78%  { transform: scale(1.15); }
	86%  { transform: scale(0.97); }
	93%  { transform: scale(1.04); }
}

/* ── Spin ─────────────────────────────────────────────────────────────────
   The loop is linear and slow — an easing curve on a full rotation makes a
   spinner look like it is struggling. */

.ic-spin-in   { animation-name: ic-spin-in; }
.ic-spin-out  { animation-name: ic-spin-out; }
.ic-spin-loop { animation-name: ic-spin-loop; animation-iteration-count: infinite; animation-duration: var(--ic-dur, 1.4s); animation-timing-function: linear; }

@keyframes ic-spin-in   { from { opacity: 0; transform: rotate(-150deg) scale(0.6); } to { opacity: 1; transform: none; } }
@keyframes ic-spin-out  { from { opacity: 1; transform: none; } to { opacity: 0; transform: rotate(150deg) scale(0.6); } }
@keyframes ic-spin-loop { from { transform: rotate(0); } to { transform: rotate(360deg); } }

/* ── Pulse ────────────────────────────────────────────────────────────────
   No overshoot anywhere, which is what separates it from pop: pulse is a
   thing waiting, pop is a thing that just happened. */

.ic-pulse-in   { animation-name: ic-pulse-in; }
.ic-pulse-out  { animation-name: ic-pulse-out; }
.ic-pulse-loop { animation-name: ic-pulse-loop; animation-iteration-count: infinite; animation-duration: var(--ic-dur, 2s); animation-timing-function: ease-in-out; }

@keyframes ic-pulse-in   { from { opacity: 0; transform: scale(0.88); } to { opacity: 1; transform: none; } }
@keyframes ic-pulse-out  { from { opacity: 1; transform: none; } to { opacity: 0; transform: scale(0.88); } }
@keyframes ic-pulse-loop { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.65; transform: scale(1.08); } }

/* ── Glitch ───────────────────────────────────────────────────────────────
   A signal dropping out for two frames and recovering. It is the other half of
   the same idea as the scanline: the design system is a record light, and this
   is what a record light does when the feed stutters.

   The restraint is the design. The loop sits PERFECTLY STILL for nine tenths
   of its cycle and breaks for the last tenth — a permanent shudder is a broken
   page, not a style. The displacement is in em so it tracks the icon's size,
   and the coloured fringe is drop-shadow in the accent, so a glitch inherits
   whatever the primary happens to be rather than hard-coding a cyan/magenta
   that would fight every palette.

   Off entirely under prefers-reduced-motion, with the rest. */

.ic-glitch-in   { animation-name: ic-glitch-in; }
.ic-glitch-out  { animation-name: ic-glitch-out; }
.ic-glitch-loop { animation-name: ic-glitch-loop; animation-iteration-count: infinite; animation-duration: var(--ic-dur, 3.2s); }

@keyframes ic-glitch-in {
	0%   { opacity: 0; transform: translateX(-0.12em); filter: drop-shadow(0.1em 0 var(--ic-primary)); }
	35%  { opacity: 1; transform: translateX(0.08em); filter: drop-shadow(-0.08em 0 var(--ic-primary)); }
	65%  { transform: translateX(-0.03em); filter: drop-shadow(0.03em 0 var(--ic-primary)); }
	100% { opacity: 1; transform: none; filter: none; }
}

@keyframes ic-glitch-out {
	0%   { opacity: 1; transform: none; filter: none; }
	40%  { opacity: 1; transform: translateX(0.08em); filter: drop-shadow(-0.08em 0 var(--ic-primary)); }
	100% { opacity: 0; transform: translateX(-0.12em); filter: drop-shadow(0.1em 0 var(--ic-primary)); }
}

@keyframes ic-glitch-loop {
	0%, 86%   { transform: none; filter: none; }
	88%       { transform: translateX(-0.07em); filter: drop-shadow(0.07em 0 var(--ic-primary)); }
	90%       { transform: translateX(0.06em); filter: drop-shadow(-0.06em 0 var(--ic-primary)); }
	92%       { transform: translateX(-0.03em); filter: drop-shadow(0.03em 0 var(--ic-primary)); }
	94%, 100% { transform: none; filter: none; }
}

/* ── Stagger ──────────────────────────────────────────────────────────────
   Parts of the icon arriving one after another rather than together. It reads
   beautifully on the multi-stroke icons and it is INLINE-SVG ONLY: a sprite
   reference has one child, <use>, and its shadow content cannot be reached by
   a child selector. Nothing breaks on a sprite — you just get no stagger. */

.ic-stagger > * { animation: inherit; }
.ic-stagger > :nth-child(2) { animation-delay: calc(var(--ic-delay, 0ms) + 1 * var(--ic-stagger, 90ms)); }
.ic-stagger > :nth-child(3) { animation-delay: calc(var(--ic-delay, 0ms) + 2 * var(--ic-stagger, 90ms)); }
.ic-stagger > :nth-child(4) { animation-delay: calc(var(--ic-delay, 0ms) + 3 * var(--ic-stagger, 90ms)); }
.ic-stagger > :nth-child(5) { animation-delay: calc(var(--ic-delay, 0ms) + 4 * var(--ic-stagger, 90ms)); }
.ic-stagger > :nth-child(6) { animation-delay: calc(var(--ic-delay, 0ms) + 5 * var(--ic-stagger, 90ms)); }

/* When the icon itself is staggering, the root must not also animate, or the
   whole thing plays once on top of its own parts. */
.ic-stagger { animation-name: none; }

/* ── Reduced motion ───────────────────────────────────────────────────────
   Everything off, and everything left in its VISIBLE resting state — an -out
   class must not leave an invisible icon behind for someone who asked for
   less movement, since they asked about motion, not about content. */

@media (prefers-reduced-motion: reduce) {
	.ic-draw-in, .ic-draw-out, .ic-draw-loop,
	.ic-fade-in, .ic-fade-out, .ic-fade-loop,
	.ic-pop-in, .ic-pop-out, .ic-pop-loop,
	.ic-spin-in, .ic-spin-out, .ic-spin-loop,
	.ic-pulse-in, .ic-pulse-out, .ic-pulse-loop,
	.ic-glitch-in, .ic-glitch-out, .ic-glitch-loop,
	.ic-stagger > * {
		animation: none !important;
		stroke-dasharray: none !important;
		stroke-dashoffset: 0 !important;
		opacity: 1 !important;
		transform: none !important;
		filter: none !important;
	}
}
"""

if __name__ == '__main__':
    raise SystemExit(main())
