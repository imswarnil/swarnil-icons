#!/usr/bin/env python3
"""build.py — turn icons/ into everything a consumer can use.

    dist/
      sprite.svg              one <symbol> per icon; one request for the set
      swarnil-icons.css       sizing, variants, alignment
      icons.json              the index the docs site and any tool reads
      svg/<weight>/<n>.svg    standalone files, one per weight

The three weights are GENERATED from one source path, never redrawn, so `bold`
cannot drift away from `line`. That is the whole reason the geometry lives in
one file.

    python3 scripts/build.py
"""
import json
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
ICONS = ROOT / 'icons'
DIST = ROOT / 'dist'

# name -> the stroke weight it renders at. This is the whole variant axis: the
# set is stroked, and a weight is the only thing a stroke has. `solid` and `duo`
# used to sit alongside these and no longer do — a filled variant is a second
# drawing wearing the first one's name, and half the set could never have one.
STROKE_VARIANTS = {'thin': '1', 'line': '1.5', 'bold': '2'}

BODY = re.compile(r'<svg[^>]*>(.*)</svg>', re.S)
CLOSED = re.compile(r'[zZ]\s*$')


def body_of(src):
    m = BODY.search(src)
    return m.group(1) if m else ''


def is_closed(body):
    """Does every path in this icon close?

    It decides one thing: whether the icon encloses an area, and so whether a
    FILL can be put inside it. `.ic-multi-fill` washes that area with the soft
    primary; on an open path — an arrow, a chevron — the wash floods the region
    the path merely implies, which is why it is a separate class rather than
    part of `.ic-multi`. The answer travels to consumers as `closed` in
    icons.json so nobody has to re-derive it from the path data.
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
    animates all 100.

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

    index, symbols, open_paths = [], [], []

    for f in files:
        name, cat = f.stem, f.parent.name
        # RAW first, MEASURED second, and the order matters. is_closed matches
        # on `<path d="`, so it has to see the geometry before pathLength is
        # inserted between the tag name and the d attribute — otherwise no path
        # matches, every icon reports itself open, and the multicolour wash
        # silently disappears from the whole set. The source file itself is
        # never touched either way.
        raw = body_of(f.read_text())
        body = measured(split_paths(raw))

        symbols.append(f'<symbol id="i-{name}" viewBox="0 0 24 24">{body}</symbol>')

        closed = is_closed(raw)
        if not closed:
            open_paths.append(name)

        index.append({'name': name, 'category': cat, 'body': body,
                      'variants': list(STROKE_VARIANTS), 'closed': closed})

        for v, w in STROKE_VARIANTS.items():
            out = DIST / 'svg' / v
            out.mkdir(parents=True, exist_ok=True)
            (out / f'{name}.svg').write_text(wrap(body, w))

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
          f'{len(STROKE_VARIANTS)} weights -> dist/')
    # Reported, not hidden: these are the icons `.ic-multi-fill` must be kept
    # off, and the count is the canary for the raw/body ordering above. If it
    # ever jumps to the size of the set, `closed` is being computed against the
    # measured body instead of the raw one.
    print(f'  {len(index) - len(open_paths)} of {len(index)} icons enclose an '
          f'area and take the multicolour wash; {len(open_paths)} are open paths')
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
   One geometry, three weights, and that is the entire variant axis. Nothing is
   redrawn, so they cannot drift: `bold` IS `line` with a wider pen.

   `ic-line` is the default and needs no class. It has one because a weight you
   can only get by omitting a class is a weight you cannot switch BACK to.

   The stroke does NOT scale with the icon, which is deliberate: a 48px icon
   with a proportionally scaled stroke reads as a fat 24px icon rather than as
   a large one. Pick the weight for the size. */

.ic-thin { --ic-stroke: 1; }
.ic-line { --ic-stroke: 1.5; }
.ic-bold { --ic-stroke: 2; }

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
   "Make it the brand colour."       .ic-primary. Every helper below sets
                                     `color` rather than `stroke`, so the
                                     stroke and any fill move together and the
                                     two can never disagree.

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
   implies, and half this set is open paths. Pair it with a closed icon —
   icons.json says which, in `closed`. */

.ic-multi {
	stroke: var(--ic-ink);
	color: var(--ic-primary);
}

/* The second colour, on the parts of the icon after the first. build.py emits
   one element per subpath precisely so this rule has something to hold: the
   page and its folded corner, the tray and its lid, the arrow's shaft and its
   head. 85 of the 100 icons have two or more parts.

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
   the same icon — the same promise the five weights make.

   ── PITCH ────────────────────────────────────────────────────────────────
   Built as a ONE-PERIOD gradient tiled by mask-size, rather than a repeating
   gradient with percentage stops. Two reasons, and the second is the one that
   matters: a tile has a real height, so the pattern can be SCROLLED by
   animating mask-position exactly one pitch, which loops seamlessly. A
   percentage-stop gradient has nothing to move. That is .ic-scan-roll, in the
   motion layer.

   ── ONE RASTER, AND IT IS VERY FINE ──────────────────────────────────────
   Sixty lines across the icon — but never finer than 1.2px, and that `max()`
   is the whole design.

   Deriving the pitch from the icon's size alone is the obvious move and it is
   wrong at both ends. Pitch and duty together decide the width of the GAP, and
   the gap IS the effect: a gap is only visible from about half a CSS pixel —
   one device pixel on a 2x screen — so a 60th-of-the-size pitch on a 24px icon
   leaves 0.18px, which is arithmetically a scanline and visually a plain icon.
   That is this style's one failure mode and it looks exactly like nothing
   being wrong. Coarsening the pitch to fix the small end then ruins the large
   end, where the whole point is a raster too fine to count.

   The floor fixes both at once, and it is also the truer model. A real tube's
   raster belongs to the SCREEN, not to the picture on it — shrink the picture
   and the scan lines do not shrink with it. So: 1.2px, always, until the icon
   is big enough that sixty lines are coarser than that, at which point the
   line count takes over and holds steady as it scales.

       ic-md   20px   pitch 1.20px   gap 0.42px
       ic-2xl  48px   pitch 1.20px   gap 0.42px
       96px           pitch 1.60px   gap 0.56px
       240px          pitch 4.00px   gap 1.40px

   ── DUTY ─────────────────────────────────────────────────────────────────
   65%, and the number was chosen by looking rather than by arithmetic. Nearer
   half maximises the CONTRAST of the pattern, which is the textbook answer and
   the wrong one here: at 24px it takes so much out of a 1.5-unit stroke that
   the icons stop looking scanned and start looking eroded — thin, patchy,
   like a bad render. Much higher and the raster is gone by 48px. 65% is where
   an icon keeps its weight at 24px and still shows a clear raster at 48px,
   which is the range these are actually browsed at.

   There is no coarse variant and no fine variant, because a scanline with
   three thicknesses is three effects sharing a name — and the coarse one was
   never a scanline at all: it was a set of bars lying across a picture. */

.ic-scan {
	--ic-scan-pitch: max(1.2px, calc(var(--ic-size, 1.5rem) / 60));
	--ic-scan-duty: 65%;

	-webkit-mask-image: linear-gradient(to bottom, #000 0 var(--ic-scan-duty), transparent var(--ic-scan-duty) 100%);
	        mask-image: linear-gradient(to bottom, #000 0 var(--ic-scan-duty), transparent var(--ic-scan-duty) 100%);
	-webkit-mask-size: 100% var(--ic-scan-pitch);
	        mask-size: 100% var(--ic-scan-pitch);
	-webkit-mask-repeat: repeat;
	        mask-repeat: repeat;
}

/* Both are still custom properties, so a project that genuinely wants a
   coarser screen sets them — per instance, inline, without a class:

       <svg class="ic ic-2xl ic-scan" style="--ic-scan-pitch: 4px">

   That is the escape hatch, and it is deliberately not a shipped class. */

/* ── Two-tone ─────────────────────────────────────────────────────────────
   Stroke and fill pulled apart: the outline stays ink while the shape carries
   a wash of the accent. It is the one way to use colour on a stroked icon
   without shouting, and it only works on icons whose paths are CLOSED. On an
   open path the wash leaks out of the shape it merely implies, so pair it with
   a closed icon or leave it off — icons.json carries a `closed` flag per icon
   precisely so a consumer can decide that without parsing path data. */

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
   Six ways an icon can move, five of them with an in, an out and a loop.

       <link rel="stylesheet" href="swarnil-icons.css">
       <link rel="stylesheet" href="swarnil-icons-motion.css">

       <svg class="ic ic-lg ic-draw-in"><use href="/sprite.svg#i-heart"/></svg>

   ── THE MATRIX ────────────────────────────────────────────────────────────
     draw    the stroke draws itself on, like a pen
     fade    opacity, with a small rise
     pop     scale with an overshoot — the one for a confirmation
     spin    rotation
     pulse   a slow breath, for something that is waiting
     tv      a tube switching on, switching off, or humming

   times three:  -in    plays once and ends VISIBLE
                 -out   plays once and ends HIDDEN
                 -loop  repeats forever

   So: .ic-draw-in, .ic-draw-out, .ic-draw-loop, .ic-fade-in … eighteen classes.

   Plus one that is not a motion so much as a surface: .ic-scan-roll scrolls
   the .ic-scan mask, which is what turns a scanline from a texture into a
   screen. It is listed with the TV section below, because they are the same
   idea at two volumes.

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
.ic-pulse-in, .ic-pulse-out, .ic-pulse-loop {
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

@keyframes ic-fade-in   { from { opacity: 0; transform: translateY(calc(var(--ic-size, 1.5rem) * 0.15)); } to { opacity: 1; transform: none; } }
@keyframes ic-fade-out  { from { opacity: 1; transform: none; } to { opacity: 0; transform: translateY(calc(var(--ic-size, 1.5rem) * -0.15)); } }
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

/* ── TV ───────────────────────────────────────────────────────────────────
   A cathode tube switching on, switching off, and sitting there humming. The
   other half of the scanline's idea: if the mask makes an icon look like a
   screen, this is the screen behaving like one.

   `loop` runs TWO animations at once. One scrolls the scanline mask by exactly
   one pitch — which is why .ic-scan is built as a tiled one-period gradient
   rather than a repeating one, and why the loop is seamless rather than
   snapping back. The other is the flicker, on a steps() timeline so the dips
   are abrupt the way a real dropout is, and rare: the tube sits perfectly
   steady for nine tenths of its cycle. Constant flicker is a fault, not a
   style.

   The roll is a no-op without .ic-scan — there is no mask to move — so
   .ic-tv-loop is safe on any icon and simply becomes the flicker alone.

   .ic-scan-roll is the roll WITHOUT the flicker, .ic-flicker is the flicker
   without the roll, and .ic-scan-roll.ic-flicker is both. The roll is the one
   to reach for by default, and it is the reason the pitch is as fine as it is:
   at 34 lines to the icon the moving mask is a SHIMMER passing over a surface,
   where a coarse one would be a set of bars visibly crawling up the picture.
   Slow it or speed it with --ic-scan-dur.

   `in` and `out` are the power stroke: the picture collapsing to a scan line
   and away, or blooming out of one.

   NOTE these use the animation SHORTHAND, so combining .ic-tv-loop with
   another motion class means the later rule wins rather than both playing.
   Pick one. */

.ic-tv-in  { animation: ic-tv-in var(--ic-dur, 520ms) cubic-bezier(0.2, 0.8, 0.2, 1) both; }
.ic-tv-out { animation: ic-tv-out var(--ic-dur, 420ms) cubic-bezier(0.6, 0, 0.9, 0.4) both; }

.ic-tv-loop {
	animation: ic-tv-roll var(--ic-scan-dur, 1.8s) linear infinite,
	           ic-tv-flicker var(--ic-dur, 5s) steps(1, end) infinite;
}

/* The TV's two halves, separately, because you will want one without the
   other: a roll with no flicker is a working screen, a flicker with no roll is
   a failing bulb, and .ic-tv-loop is both at once.

   They cannot simply be listed together on an element — each is an animation
   SHORTHAND, so the second would replace the first rather than join it. Hence
   the combined rule, last, which is what actually plays when both classes are
   present. Three rules for two flags is the price of the shorthand; the
   alternative is longhand lists that no longer read as one effect. */

.ic-flicker   { animation: ic-tv-flicker var(--ic-dur, 5s) steps(1, end) infinite; }

/* Slower by default than the TV's, because without the flicker to punctuate it
   the movement is the only thing there is. */
.ic-scan-roll { animation: ic-tv-roll var(--ic-scan-dur, 2.6s) linear infinite; }

.ic-scan-roll.ic-flicker {
	animation: ic-tv-roll var(--ic-scan-dur, 2.6s) linear infinite,
	           ic-tv-flicker var(--ic-dur, 5s) steps(1, end) infinite;
}

/* One pitch exactly — any other distance and the pattern jumps at the wrap. */
@keyframes ic-tv-roll {
	from { -webkit-mask-position: 0 0; mask-position: 0 0; }
	to   { -webkit-mask-position: 0 var(--ic-scan-pitch, 0); mask-position: 0 var(--ic-scan-pitch, 0); }
}

@keyframes ic-tv-flicker {
	0%, 90%, 100% { opacity: 1; }
	91%  { opacity: 0.45; }
	92%  { opacity: 1; }
	94%  { opacity: 0.72; }
	95%  { opacity: 1; }
}

@keyframes ic-tv-in {
	0%   { opacity: 0; transform: scaleY(0.02) scaleX(1.35); filter: brightness(2.5); }
	45%  { opacity: 1; transform: scaleY(0.06) scaleX(1.1); filter: brightness(1.6); }
	100% { opacity: 1; transform: none; filter: none; }
}

@keyframes ic-tv-out {
	0%   { opacity: 1; transform: none; filter: none; }
	55%  { opacity: 1; transform: scaleY(0.05) scaleX(1.15); filter: brightness(1.8); }
	100% { opacity: 0; transform: scaleY(0.01) scaleX(0.25); filter: brightness(3); }
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
	.ic-tv-in, .ic-tv-out, .ic-tv-loop,
	.ic-scan-roll, .ic-flicker,
	.ic-stagger > * {
		animation: none !important;
		stroke-dasharray: none !important;
		stroke-dashoffset: 0 !important;
		opacity: 1 !important;
		transform: none !important;
		filter: none !important;
		clip-path: none !important;
	}
}
"""

if __name__ == '__main__':
    raise SystemExit(main())
