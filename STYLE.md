# Swarnil Icons — the style specification

**This file is the icon set. Everything else is an implementation of it.**

An icon set is not a folder of drawings; it is one set of geometric decisions
applied consistently enough that thirty different pictures look like they were
drawn by one hand on one afternoon. When a set looks "off", it is almost never
the drawing — it is a stroke that is 1.6 somewhere and 1.5 everywhere else, or
a circle at r=7 next to one at r=7.5.

So: every rule here is a number, and `scripts/validate.py` fails the build when
an icon breaks one. A style guide that is not executable is a wish.

---

## 0 · Provenance

**Drawn from scratch. Nothing here is traced, forked or re-licensed from another
icon set.**

That is a deliberate constraint, not a boast. This set ships MIT for anyone to
use, and a set assembled out of somebody else's geometry cannot honestly do that
— it inherits their licence, their attribution requirements, and their design
decisions, which then quietly become yours. The geometry below is the reason the
set can be given away cleanly.

It also has to *belong* to the design system it sits beside. Frame & Signal is a
viewfinder and a record light; a generic rounded-rect icon set would sit next to
that and look borrowed.

---

## 1 · The canvas

```
┌────────────────────────┐  24 × 24    the canvas
│  ┌──────────────────┐  │
│  │                  │  │  20 × 20    the LIVE AREA — all geometry lives here
│  │                  │  │
│  │                  │  │   2         the optical margin, on all four sides
│  └──────────────────┘  │
└────────────────────────┘
```

- **viewBox** is always `0 0 24 24`. No exceptions, ever — a set with two grids
  is two sets.
- **Live area** is `2 … 22` on both axes. Nothing touches the canvas edge, so an
  icon never collides with the text beside it.
- **Overshoot** is allowed to `1.5` for a circle only, because a circle at the
  same bounding box as a square reads visibly smaller. This is the one place the
  eye beats the arithmetic.

## 2 · Stroke

| | Value | Why |
| --- | --- | --- |
| Default weight | `1.5` | Reads at 16px and still has presence at 32px |
| Cap | `round` | |
| Join | `round` | |
| Fill | `none` | Colour comes from `currentColor` on the stroke |
| Alignment | centred on the grid | |

**Orthogonal strokes sit on whole coordinates.** `M4 12h16`, not `M4.5 12h15`.

A word on why, because the usual advice says the opposite. The half-pixel trick
is real but it is a rule for **1px strokes at 1× zoom**: a 1px stroke centred on
a whole coordinate straddles a boundary, so you nudge it to `.5`. A 1.5 stroke
centred on `12` spans `11.25–12.75` and is not pixel-aligned either way, and the
set is rendered at 16, 20, 24, 32 and 48px, so there is no single grid to snap
to. Chasing crispness with coordinates would only trade one blurry size for
another while making every path harder to read.

Whole coordinates instead buy the thing that actually matters: geometry you can
reason about, and shapes that stay concentric when you scale the stroke for the
`thin` and `bold` variants. `validate.py` enforces it.

## 3 · Geometry

- **Angles are 90° or 45°.** Nothing else. An arbitrary 37° line is the fastest
  way to make one icon look like a guest in the set.
- **Corner radius** is `2` on shapes and `3` on containers. Two values, no more.
- **Circles**: `r=1.5` (a dot), `r=3` (a small node), `r=7.5` (a ring).
- **Node economy**: draw it with the fewest points that express the idea. If two
  paths can be one path, they are one path.
- **Concentricity**: nested shapes share a centre at `12,12` unless the idea
  requires otherwise.

## 4 · The signature — what makes these *ours*

Three devices, used sparingly. They are the reason the set reads as Frame &
Signal rather than as another Feather.

### The 45° cut

Where a shape needs a corner accent, it is **cut at 45°**, not rounded. It is the
clipped corner of a film frame and a clapperboard, and it is the set's most
recognisable move.

```
   rounded (everyone)        cut (ours)
   ╭─────────              ╱─────────
   │                      │
```

Used on: file, folder, card, note, document, archive.

### The record dot

Anything meaning **live, active, recording or on** carries a filled dot at
`r=1.5`. It is the only filled element in an otherwise stroked set, so it always
reads as state rather than as drawing.

Used on: record, live, broadcast, status, notification.

### Bracket corners

Two opposed corner brackets, at `4` long, for anything meaning **frame, capture,
crop, select or focus** — the viewfinder, straight out of the design system's
frame layer.

Used on: capture, crop, focus, select, scan.

## 5 · Variants

Every icon ships in five weights from one source path. They are generated, not
redrawn, so they can never drift apart.

| Variant | How | Use |
| --- | --- | --- |
| `line` | stroke `1.5` | the default |
| `thin` | stroke `1` | dense UI, tables, 16px |
| `bold` | stroke `2` | emphasis, 32px and up |
| `solid` | fill `currentColor`, no stroke | selected / active states |
| `duo` | primary stroke + secondary at `0.35` opacity | large decorative use |

`solid` is the one that cannot be purely mechanical — a stroked outline filled in
becomes a blob. Icons that need a genuinely different solid path declare one; the
rest are generated. `validate.py` reports which is which so it stays honest.

## 6 · Naming

`kebab-case`, named for **what it is**, not what it does in one product.

- `camera`, not `record-video-button`
- `arrow-right`, not `next`
- `circle-check`, not `success`

The meaning belongs to the consumer. An icon named `success` cannot be reused for
"verified", and then someone draws a second, near-identical tick.

Directional icons are `-up -down -left -right`. Filled circles wrapping a glyph
are `circle-*`.

## 7 · Optical alignment

Arithmetic centring is not optical centring:

- A **triangle** (play) sits ~`0.5` right of centre, or it reads as leaning left.
- A **circle** overshoots a square by `1.5` at the same weight.
- **Diagonal-heavy** glyphs get slightly more margin than orthogonal ones.

These are judgement calls the validator cannot make. They are listed here so they
are made deliberately rather than by accident.

## 8 · The floor

Every icon is checked at **16px** before it ships. If a detail disappears at
16px, the detail is wrong, not the size — remove it. That is the same argument as
the design system's thumbnail rule: if the idea does not survive being small, the
idea is wrong.

---

## What the validator enforces

`python3 scripts/validate.py`

1. viewBox is exactly `0 0 24 24`
2. all geometry inside the `2 … 22` live area (circles may overshoot to `1.5`)
3. stroke weight is one of the five declared values
4. `fill="none"` on stroked icons; no hard-coded colour anywhere
5. horizontal and vertical lines sit on whole coordinates
6. no `<style>`, no `class`, no `id` — an icon is geometry, not a stylesheet
7. filename is kebab-case and matches the set index

Everything else is taste, and taste is what this document is for.
