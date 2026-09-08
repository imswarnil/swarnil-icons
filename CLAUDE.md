# Swarnil Icons

`icons.imswarnil.com` — a 24-grid stroked icon set, drawn from scratch, MIT. It is a
**standalone** repo: no `file:` dependency on `design.imswarnil.com` or any other
component in the umbrella, so this folder can be cloned, worked on and shipped on its
own. (It shares the same visual language by hand, not by import — see README.md's "Why
another icon set".)

```
icons.imswarnil.com/          (repo root — this is the whole project)
├── icons/<category>/*.svg    hand-authored source geometry, one file per icon
├── scripts/author.py         the single geometry table — add an icon here
├── scripts/new_icon.py       writes a table entry for you (`npm run new`)
├── scripts/validate.py       enforces STYLE.md, --strict for CI
├── scripts/build.py          icons/ -> dist/ (sprite, css, motion css, json, svg)
├── scripts/demos.py          dist/ -> demo/ (the animated strips README embeds)
├── docs/build.py             dist/ -> site/ (three pages: pitch, browser, showcase)
├── demo/                     generated but COMMITTED — README points at it on main
├── dist/                     generated, gitignored
└── site/                     generated, gitignored — the whole Pages deploy artifact
```

Read `README.md` for the public-facing pitch and `STYLE.md` for the geometry rules
`validate.py` enforces — both are already thorough; don't duplicate them here.

## The site is three pages

`/` is the **pitch** — what this is and why it exists. `/icons/` is the **browser**:
search, filter, and one rail of controls over the grid — weight and size as segmented
button groups (joined, because those two axes have an order), style as toggles, colour
as two single-line swatch rows each ending in an eyedropper, animation as two dropdowns.
Every toggle draws a real icon in the state it selects. The default style is Scanline.
Picking either scanline reveals a flicker toggle; nothing else has sub-options.
`/usage/` is the **showcase** — what the set looks like once it has a job: marketing
cards (their marks flickering, each on its own `--ic-dur`), video thumbnails, interface
chrome, scroll-triggered sections, and the scanline still, rolling and flickering.

The rule for the showcase is that **every icon on it wears a class the package
ships**. `usage.css` styles the surrounding cards, tiles and panels; it never
restyles an icon. If a demo needs a rule in that file to look right, the demo is
lying about what a consumer would get. The one exception is `--ic-size`, which is
the package's own sizing token and fair game.

## Adding or fixing an icon

The short way, which does steps 1–3 for you:

```bash
npm run new -- <name> <category> '<path-d>' ['<shapes>']
npm run new -- flag ui 'M6 4v16M6 5h11l-2 3 2 3H6'
```

It writes the entry into the right category block of the geometry table,
creates the category if it is new, refuses a name already in the set, then
authors and validates. A rule violation is reported and the entry is **left in
the table** to fix — re-run `npm run new-check` after. It is a front door to the
table, not a second source of truth.

By hand, which is the same thing:

1. Add a line to the geometry table at the top of `scripts/author.py` (or edit an
   existing entry to fix one).
2. `python3 scripts/author.py` — writes/rewrites the file(s) under `icons/`.
3. `python3 scripts/validate.py` — must pass before committing. It enforces every rule
   in STYLE.md (viewBox, live-area bounds, stroke weight, whole-coordinate lines, no
   hard-coded colour, no `<style>`/class/id, kebab-case filename).
4. `python3 scripts/build.py && python3 docs/build.py` (or `npm run build`, which chains
   validate → build → docs) to regenerate `dist/` and `site/` and see the result.

Never hand-edit files under `icons/` for anything build.py or docs/build.py would
otherwise regenerate for you, and never hand-edit `dist/` or `site/` at all — both are
fully generated and gitignored.

**Three weights and nothing else.** `thin`, `line`, `bold` — all generated from one
path by changing the pen. There is no `solid` or `duo`; they were removed because a
fill cannot be derived (79 of 103 icons are open paths, and filling those gives you a
blob), so it would have been a second drawing per icon, free to drift. See README.md's
"Why there is no filled variant". Emphasis is `ic-bold`, colour is `ic-primary`, and a
wash inside a closed icon is `ic-multi-fill` — `icons.json` carries `closed` per icon
so a consumer knows where that is safe.

## Two things build.py will let you break quietly

**`raw` vs `body`.** build.py stamps `pathLength="1"` onto every path and circle in
the *generated* output, which is what lets the motion layer draw an icon on with no
JavaScript (README explains why). But `is_closed()` matches on the literal string
`<path d="`, and pathLength lands between the tag name and that attribute. It is
therefore handed `raw`, the unmeasured body; everything emitted is handed `body`.
Feed it `body` by mistake and no icon reports itself closed any more — every icon
silently loses the `ic-multi-fill` wash and the build still reports success. The
"24 of 103 icons enclose an area" line in the build output is the canary: if the
first number drops to 0, this is what happened.

**The scanline is one raster, and its pitch has a floor.** `max(1.2px, size/60)` at 65%
duty, in `scripts/build.py`'s `CSS` constant. Both halves matter: without the floor the
gap between lines goes sub-pixel on a small icon and the effect silently disappears
while still being "on"; without the fine ratio a big icon gets bars rather than a
raster. There is deliberately no coarse/fine class — that was tried and removed, since
a scanline with three thicknesses is three effects sharing a name. Consumers who want
another pitch set the custom property inline.

**Colour is a layer, never geometry.** The source SVGs carry no colour and
`validate.py` fails on a hard-coded one. `--ic-primary` and friends live in the
generated `swarnil-icons.css`, each reading the design system's token first —
`var(--accent, <the same value copied>)` — so the set adopts a loaded design system
and still works standalone. Those fallbacks are hand-synced from
`design.imswarnil.com/src/1-foundation/01-color.css`; this repo deliberately has no
dependency on it, so they are copied, not imported. If that palette moves, update
the `CSS` constant in `scripts/build.py`.

## Running it locally

```bash
npm run dev     # npm run build, then serves site/ on http://localhost:8082
```

No `npm install` needed — there are no JS dependencies; `npm` here is only a script
runner over the Python build. `engines.node >=18` in package.json is for the local
`http.server`/tooling convenience, not a build requirement.

## Deploying

`git push` to `main` is the entire release process:

- **`.github/workflows/ci.yml`** — runs `npm run validate` and `npm run build` on every
  push and PR. A STYLE.md violation or a broken build fails here.
- **`.github/workflows/pages.yml`** — on push to `main`, runs `npm run build` and
  deploys `site/` to GitHub Pages via `actions/deploy-pages`. `docs/build.py` writes
  `CNAME` (from the `SITE` constant, `docs/build.py:19`), `.nojekyll`, `robots.txt` and
  `sitemap.xml` into `site/`, so that directory is the entire deploy artifact — nothing
  else needs configuring in the workflow.
- GitHub repo Pages settings: source = **GitHub Actions**, custom domain =
  `icons.imswarnil.com` (kept in sync with the `CNAME` file `docs/build.py` writes).
- DNS: a CNAME record at the registrar/DNS provider for `imswarnil.com` —
  `icons` → `imswarnil.github.io` — is what makes the custom domain resolve. That
  record lives outside this repo; this repo only emits the `CNAME` file GitHub Pages
  checks against it.

To change the published domain, edit `SITE` in `docs/build.py`, rebuild, update the
repo's Pages custom-domain setting, and update the DNS record to match — all three have
to agree.

## npm package

Published as `@imswarnil/swarnil-icons` per `package.json` — the `files` field ships
`icons/`, `dist/`, `STYLE.md`, `README.md`, `LICENSE`. `dist/` has to exist (i.e. `npm
run build` has to have run) before `npm publish`, since `dist/` is gitignored and not
built by a `prepublishOnly` hook.
