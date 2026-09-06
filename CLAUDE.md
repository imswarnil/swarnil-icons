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
├── scripts/validate.py       enforces STYLE.md, --strict for CI
├── scripts/build.py          icons/ -> dist/ (sprite, css, json, per-variant svg)
├── docs/build.py             dist/ -> site/ (the one-page browser at the domain)
├── dist/                     generated, gitignored
└── site/                     generated, gitignored — the whole Pages deploy artifact
```

Read `README.md` for the public-facing pitch and `STYLE.md` for the geometry rules
`validate.py` enforces — both are already thorough; don't duplicate them here.

## Adding or fixing an icon

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

A closed path gets a solid variant for free (build.py fills it); an open path (arrow,
chevron, check, …) does not — see README.md's "45 icons without a solid variant" for
why that's a deliberate gap, not a bug.

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
