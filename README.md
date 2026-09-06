# Swarnil Icons

**61 icons on a 24 grid. Drawn from scratch, MIT, no dependencies.**

<https://icons.imswarnil.com>

Five weights and five animations generated from one geometry, so `bold` can
never drift away from `line`. Take any icon at any size, in any colour, as SVG,
PNG or JPG.

---

## Why another icon set

Because the two honest options were both worse.

Forking a permissively-licensed set and restyling it means inheriting somebody
else's geometry, their attribution requirements and their design decisions —
which then quietly become yours, and the "MIT, use it freely" line at the top of
this file stops being straightforwardly true.

And a generic rounded-rect set sitting beside the [Swarnil Design
System](https://design.imswarnil.com) — whose whole identity is a viewfinder and
a record light — would look borrowed, because it would be.

So the geometry is original, and [STYLE.md](STYLE.md) is the reason it is
consistent rather than merely new.

## Install

```bash
npm install @imswarnil/swarnil-icons
```

Or take the sprite straight off the site — one request for the whole set:

```html
<link rel="stylesheet" href="https://icons.imswarnil.com/swarnil-icons.css">

<svg class="ic ic-lg"><use href="https://icons.imswarnil.com/sprite.svg#i-camera"/></svg>
```

Or copy the markup for one icon out of the site and paste it. All three are the
same geometry.

## Sizes and weights

```html
<svg class="ic ic-sm"><use href="/sprite.svg#i-camera"/></svg>   <!-- 16px -->
<svg class="ic ic-lg ic-bold"><use href="/sprite.svg#i-camera"/></svg>
```

| Size | | Weight | |
| --- | --- | --- | --- |
| `ic-xs` | 14px | `ic-thin` | 1 |
| `ic-sm` | 16px | `ic-line` | 1.5 (default) |
| `ic-md` | 20px | `ic-bold` | 2 |
| `ic-lg` | 24px | `ic-solid` | filled |
| `ic-xl` | 32px | `ic-duo` | two-tone |
| `ic-2xl` | 48px | | |

The stroke does **not** scale with the size, deliberately. A 48px icon with a
proportionally scaled stroke reads as a fat 24px icon rather than as a large
one. Pick the weight for the size.

## Colour

By default an icon inherits `currentColor`, so it takes the colour of the text
beside it and never needs a theme of its own. When you want it to carry the
brand instead:

```html
<svg class="ic ic-lg ic-primary"><use href="/sprite.svg#i-heart"/></svg>
<svg class="ic ic-lg ic-solid ic-primary"><use href="/sprite.svg#i-heart"/></svg>
<svg class="ic ic-lg ic-fill-soft"><use href="/sprite.svg#i-heart"/></svg>
```

| Colour | | Fill | |
| --- | --- | --- | --- |
| `ic-primary` | the brand accent | `ic-fill-primary` | fill with the accent |
| `ic-muted` | quieter text | `ic-fill-soft` | fill with a wash of it |
| `ic-subtle` | quieter still | `ic-fill-current` | fill with the stroke colour |
| `ic-multi` | three-colour (below) | `ic-multi-fill` | its light-primary wash |
| `ic-success` `ic-info` | | `ic-fill-none` | back to outline |
| `ic-warning` `ic-danger` | | | |

Every helper sets `color`, not `stroke` — so stroke and fill move together, and
a line icon and its solid can never end up disagreeing about what colour they
are. `ic-solid ic-primary` is therefore a solid icon filled in the brand colour,
and `ic-fill-soft` is the two-tone case: an ink outline holding a wash of the
accent. The fill helpers only make sense on icons whose paths are closed — the
same ones that have a solid variant.

### Multicolour

One more class turns the whole set three-colour — black strokes, the primary on
the parts that carry meaning, and a light wash of the primary inside closed
shapes:

```html
<svg class="ic ic-lg ic-multi ic-multi-fill"><use href="/sprite.svg#i-file"/></svg>
```

`build.py` emits **one element per subpath**, which is what makes this possible:
most icons are authored as a single path whose data happens to contain several
shapes — a page and the fold on its corner, a tray and its lid — and CSS saw one
child where a reader sees two. Splitting on absolute `M` is lossless (the same
commands, redistributed), and it leaves 47 of the 61 icons with two or more
parts to colour.

`ic-multi-fill` is separate because it is the one part that is not universally
safe: filling an open path floods the area the path merely implies. Pair it with
a closed icon — the same ones that have a solid variant.

The per-part colour needs **inline** markup; a `<use>` reference has one child
and CSS cannot reach into its shadow content. A sprite still gets the ink
stroke, the primary marks and the wash, because those ride on inherited
properties — it just misses the fourth touch.

### The values track the design system

Each token reads the [Swarnil Design System](https://design.imswarnil.com)'s
token **first**, and falls back to the same value written out:

```css
--ic-primary: var(--accent, oklch(63% 0.190 34));
```

So one stylesheet does both jobs. Load the design system and the icons inherit
its `--accent` — repoint that one line and the icons rebrand along with
everything else, with no build step and no import. Load nothing at all and they
still render in the system's own signal red, because the fallback *is* the
design system's value, copied.

The copy is deliberate. A real dependency would make this package undeployable
on its own, and an invented default would be a second palette quietly drifting
away from the first.

For anything else, set the properties directly — per instance, inline:

```html
<svg class="ic ic-lg" style="color: var(--brand); --ic-fill: var(--brand-wash)">
```

The light/dark pairs need a `color-scheme` to choose from; declare
`:root { color-scheme: light dark; }` and the muted and status tones follow the
theme. `--ic-primary` is one colour in both, by design: a brand that shifts hue
between themes is two brands.

The source SVGs never carry colour at all — `validate.py` fails on a hard-coded
one. Colour is only ever this CSS layer, or the colour picker on the site, which
bakes your choice into the SVG, PNG or JPG you download.

## Motion

Five ways an icon can move, each with an in, an out and a loop. It is a second
stylesheet, so a project that wants none of it pays nothing:

```html
<link rel="stylesheet" href="swarnil-icons.css">
<link rel="stylesheet" href="swarnil-icons-motion.css">

<svg class="ic ic-lg ic-draw-in"><use href="/sprite.svg#i-heart"/></svg>
```

| | | Mode | |
| --- | --- | --- | --- |
| `draw` | the stroke draws itself on, like a pen | `-in` | plays once, ends **visible** |
| `fade` | opacity, with a small rise | `-out` | plays once, ends **hidden** |
| `pop` | scale with an overshoot — for a confirmation | `-loop` | repeats forever |
| `spin` | rotation | | |
| `pulse` | a slow breath, for something waiting | | |

So `ic-draw-in`, `ic-pop-loop`, `ic-fade-out` — fifteen classes. Four custom
properties tune them, set anywhere from a theme down to one element:

```html
<svg class="ic ic-lg ic-draw-in" style="--ic-dur: 1.2s; --ic-delay: 200ms">
```

`--ic-dur`, `--ic-delay`, `--ic-ease`, and `--ic-stagger` for `ic-stagger`,
which brings the parts of an inline icon in one after another.

### Why draw needs no JavaScript

Drawing a line on means animating `stroke-dashoffset` from the path's whole
length down to zero — and length is in user units, so the usual approach is to
measure every path with `getTotalLength()` at runtime and write the number back
per icon.

`build.py` stamps `pathLength="1"` on every path and circle in the generated
output instead, which redefines each one's length as **1**. `stroke-dashoffset:
1` is then "fully hidden" for every icon in the set regardless of its real
geometry, and two CSS rules animate all 61 of them.

The dash properties are inherited, which is what makes this work through
`<use>`: the rule sits on the `<svg>` and the value reaches the shadow content
of a sprite reference, where a child selector could never reach.

Draw needs a stroke to draw, so it does nothing on `ic-solid`. Everything is
switched off under `prefers-reduced-motion`, and left in its visible resting
state — an `-out` class must not leave an invisible icon behind for someone who
asked for less movement.

## The 49 icons without a solid variant

`build.py` reports them, and it is not an oversight. A solid variant is
generated by filling the source path, and that only works when the path is
**closed**. Filling an open path — an arrow, a chevron, a check — produces a
blob, not an icon. Those icons need their own declared solid geometry, which is
drawing work rather than build work.

Shipping 49 blobs to make a table look complete would be the wrong trade.

## Working on it

```bash
npm run new -- <name> <cat> '<path-d>' ['<shapes>']   # add an icon
python3 scripts/author.py      # write icons/ from the geometry table
python3 scripts/validate.py    # enforce STYLE.md — run this before committing
python3 scripts/build.py       # sprite, CSS, motion CSS, JSON, per-variant SVGs
npm run dev                    # build everything and serve on :8082
```

### Adding an icon

```bash
npm run new -- flag ui 'M6 4v16M6 5h11l-2 3 2 3H6'
npm run new -- gauge status 'M12 12l4-3' 'circle:12,12,8'
npm run new -- target frame '' 'circle:12,12,8|#circle:12,12,1.5'
npm run build
```

That writes the entry into the geometry table at the top of
`scripts/author.py`, in the right category block, then authors the SVG and
validates it against STYLE.md. A category that does not exist yet is created. A
name already in the set is refused rather than silently overwritten, and an icon
that breaks a rule is reported with the rule it broke and **left in the table**
for you to fix — re-run `npm run new-check` once you have.

The fourth argument is the shape list: `circle:cx,cy,r`, joined with `|`, and a
leading `#` means filled. Circles live there rather than in the path data
because a circle written as arcs is unreadable and impossible to nudge later.

It is a front door to the table, not a second source of truth — the line it
writes is an ordinary line, and editing that line by hand afterwards is the
normal way to adjust an icon. Keeping the geometry in one table rather than in
61 hand-edited files is what stops the wrapper, the viewBox and the stroke from
drifting apart.

`validate.py` walks every path and fails on: a wrong viewBox, geometry outside
the 2…22 live area, an undeclared stroke weight, a hard-coded colour, an
orthogonal line off a whole coordinate, a stylesheet hook, or a bad filename.
It has been tested by breaking each rule on purpose — an audit that has never
failed is an audit nobody has checked.

## Licence

MIT. Use them in anything, including commercially, without attribution.

If you redraw or extend the set, read [STYLE.md](STYLE.md) first — the value is
in the consistency, and consistency is easy to spend and slow to rebuild.
