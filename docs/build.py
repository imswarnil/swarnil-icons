#!/usr/bin/env python3
"""build.py — the icons.imswarnil.com site.

One page. It is a browser, not a manual: search, filter, pick a variant and a
size, copy the markup, download the file. The whole set is inlined as JSON so
the page works from a static host with no API and no build step for the reader.

    docs/    source
    site/    output — generated, gitignored

    python3 docs/build.py
"""
import hashlib
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
DIST = ROOT / 'dist'
OUT = ROOT / 'site'

SITE = 'https://icons.imswarnil.com'
NAME = 'Swarnil Icons'


# The stylesheets and script this page links. Long-lived at the edge, which is
# the whole problem below.
VERSIONED = ('/swarnil-icons.css', '/swarnil-icons-motion.css',
             '/assets/site.css', '/assets/site.js')


def fingerprint(page):
    """Stamp ?v=<content hash> onto every asset this page links.

    Without this a deploy ships a broken site for hours. index.html is not
    cached at the edge, so a new page goes live immediately — but the CSS and
    JS beside it are served with a long max-age and stay CACHED, so the new
    markup runs against the previous release's script. New HTML plus old
    JavaScript is worse than either alone: the sidebar's control holders never
    get filled, because the script that knows how to fill them is the old one.
    That is exactly what happened on the first deploy of this page.

    A content hash in the query string makes each release a NEW cache key, so
    the edge fetches it once and then caches it hard, which is what a long
    max-age is for in the first place. Nothing is renamed: the bare
    /swarnil-icons.css URL the README tells people to link keeps working and
    keeps its own cache lifetime.
    """
    for path in VERSIONED:
        f = OUT / path.lstrip('/')
        if not f.exists():
            continue
        h = hashlib.sha256(f.read_bytes()).hexdigest()[:10]
        page = page.replace(f'"{path}"', f'"{path}?v={h}"')
    return page


def main():
    data_file = DIST / 'icons.json'
    if not data_file.exists():
        print('dist/icons.json missing — run scripts/build.py first')
        return 1

    data = json.loads(data_file.read_text())
    icons = data['icons']

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    shell = (DOCS / 'templates' / 'index.html').read_text()
    # The sidebar and the grouped grid are both built client-side from
    # #icon-data (see site.js) — categories only need counting here, for
    # the kicker line ("N icons · N categories").
    catcount = len({i['category'] for i in icons})

    # The page's own chrome is built out of the set, so the sprite is inlined
    # rather than fetched — one request fewer, and no moment on load where the
    # buttons have no icons in them.
    sprite = (DIST / 'sprite.svg').read_text().strip()

    shutil.copytree(DOCS / 'assets', OUT / 'assets')
    for f in ('sprite.svg', 'icons.json', 'swarnil-icons.css', 'swarnil-icons-motion.css'):
        shutil.copy(DIST / f, OUT / f)
    shutil.copytree(DIST / 'svg', OUT / 'svg')

    page = (shell
            .replace('{name}', NAME)
            .replace('{site}', SITE)
            .replace('{count}', str(len(icons)))
            .replace('{catcount}', str(catcount))
            .replace('{sprite}', sprite)
            .replace('{data}', json.dumps(icons, separators=(',', ':'))))

    page = fingerprint(page)

    (OUT / 'index.html').write_text(page)

    (OUT / '.nojekyll').write_text('')
    (OUT / 'CNAME').write_text(SITE.split('//')[1] + '\n')
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n')
    (OUT / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'<url><loc>{SITE}/</loc></url></urlset>')

    print(f'built the icons site: {len(icons)} icons, {catcount} categories -> site/')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
