#!/usr/bin/env python3
"""author.py — write the icon source files from one geometry table.

Every icon in the set is defined here as path data, then written out as an
individual SVG. Keeping the geometry in one table rather than in 40 hand-edited
files is what makes the set consistent: the wrapper, the viewBox, the stroke and
the cap/join are emitted identically every time and cannot drift.

The SVGs in icons/ are the published source. This script writes them; it is not
part of the build. Run it when adding an icon, then run validate.py.

    python3 scripts/author.py

Geometry rules are in STYLE.md and enforced by scripts/validate.py.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'icons'

# name: (category, path-data, optional solid-path override)
# Path data only — the wrapper is generated. `#` prefixed entries are filled
# shapes (the record dot signature) rather than strokes.
ICONS = {
    # ── ui ─────────────────────────────────────────────────────────────────
    'arrow-right':    ('ui', 'M4 12h16M13 5l7 7-7 7'),
    'arrow-left':     ('ui', 'M20 12H4M11 5l-7 7 7 7'),
    'arrow-up':       ('ui', 'M12 20V4M5 11l7-7 7 7'),
    'arrow-down':     ('ui', 'M12 4v16M5 13l7 7 7-7'),
    'chevron-right':  ('ui', 'M9 5l7 7-7 7'),
    'chevron-left':   ('ui', 'M15 5l-7 7 7 7'),
    'chevron-down':   ('ui', 'M5 9l7 7 7-7'),
    'chevron-up':     ('ui', 'M5 15l7-7 7 7'),
    'check':          ('ui', 'M4 13l5 5L20 7'),
    'x':              ('ui', 'M6 6l12 12M18 6L6 18'),
    'plus':           ('ui', 'M12 4v16M4 12h16'),
    'minus':          ('ui', 'M4 12h16'),
    'menu':           ('ui', 'M4 7h16M4 12h16M4 17h16'),
    'search':         ('ui', 'M17 17l3 3', 'circle:10,10,6'),
    'settings':       ('ui', 'M4 8h8M16 8h4M4 16h4M12 16h8', 'circle:14,8,2|circle:8,16,2'),
    'external-link':  ('ui', 'M14 4h6v6M20 4l-8 8M18 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6'),
    'trash':          ('ui', 'M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M6 7v12a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V7M10 11v5M14 11v5'),
    'download':       ('ui', 'M12 4v11M7 11l5 5 5-5M4 20h16'),
    'upload':         ('ui', 'M12 16V5M7 9l5-5 5 5M4 20h16'),
    'refresh':        ('ui', 'M20 5v5h-5M4 19v-5h5M19 10a7.5 7.5 0 0 0-13-3l-2 3M5 14a7.5 7.5 0 0 0 13 3l2-3'),

    'box':            ('ui', 'M12 3l8 4.5v9L12 21l-8-4.5v-9zM12 12v9M12 12L4 7.5M12 12l8-4.5'),
    'activity':       ('ui', 'M4 12h4l2-5 3 10 2-5h5'),
    'browser':        ('ui', 'M4 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zM4 9h16'),
    'type':           ('ui', 'M4 7h16M4 12h10M4 17h13'),
    'moon':           ('ui', 'M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z'),

    'home':           ('ui', 'M4 12l8-8 8 8v7a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1zM9 20v-6h6v6'),
    'grid':           ('ui', 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z'),
    'eye':            ('ui', 'M3 12c3-4.5 6-6.5 9-6.5s6 2 9 6.5c-3 4.5-6 6.5-9 6.5s-6-2-9-6.5z', 'circle:12,12,3'),
    'calendar':       ('ui', 'M4 8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zM4 10h16M8 4v4M16 4v4'),
    'chart-bar':          ('ui', 'M4 20h16M8 20V13M12 20V7M16 20V10'),
    # ── media ──────────────────────────────────────────────────────────────
    'play':           ('media', 'M9 5v14l11-7z'),
    'pause':          ('media', 'M9 5v14M15 5v14'),
    'camera':         ('media', 'M4 9a2 2 0 0 1 2-2h2l2-3h4l2 3h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z',
                       'circle:12,13,3'),
    'video':          ('media', 'M4 8a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zM15 11l5-3v8l-5-3z'),
    'image':          ('media', 'M4 7a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v10a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3zM4 16l5-4 4 3 3-2 4 3',
                       'circle:9,9,1.5'),
    'mic':            ('media', 'M12 4a3 3 0 0 1 3 3v5a3 3 0 0 1-6 0V7a3 3 0 0 1 3-3zM6 12a6 6 0 0 0 12 0M12 18v3'),
    'volume':         ('media', 'M4 10v4h3l4 4V6l-4 4zM15 10a3 3 0 0 1 0 4M18 8a6 6 0 0 1 0 8'),
    'headphones':     ('media', 'M4 15v-2a8 8 0 0 1 16 0v2M4 14h3v6H6a2 2 0 0 1-2-2zM20 14h-3v6h1a2 2 0 0 0 2-2z'),

    'clapperboard':   ('media', 'M4 8h16v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zM4 8V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v2M9 4l-4 4M14 4l-4 4M19 4l-4 4'),
    'film':           ('media', 'M4 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zM8 5v14M16 5v14M4 9h4M4 15h4M16 9h4M16 15h4'),
    'playlist':       ('media', 'M14 15v6l5-3zM4 6h12M4 11h12M4 16h6'),
    'waveform':       ('media', 'M4 10v4M8 7v10M12 4v16M16 7v10M20 10v4'),
    # ── frame · the signature bracket icons ────────────────────────────────
    'capture':        ('frame', 'M4 9V6a2 2 0 0 1 2-2h3M15 4h3a2 2 0 0 1 2 2v3M20 15v3a2 2 0 0 1-2 2h-3M9 20H6a2 2 0 0 1-2-2v-3',
                       'circle:12,12,3'),
    'focus':          ('frame', 'M4 9V6a2 2 0 0 1 2-2h3M15 4h3a2 2 0 0 1 2 2v3M20 15v3a2 2 0 0 1-2 2h-3M9 20H6a2 2 0 0 1-2-2v-3',
                       '#circle:12,12,1.5'),
    'scan':           ('frame', 'M4 9V6a2 2 0 0 1 2-2h3M15 4h3a2 2 0 0 1 2 2v3M20 15v3a2 2 0 0 1-2 2h-3M9 20H6a2 2 0 0 1-2-2v-3M4 12h16'),
    'crop':           ('frame', 'M7 3v14h14M3 7h14v14'),
    'aperture':       ('frame', '', 'circle:12,12,8|#circle:12,12,3'),
    'maximise':       ('frame', 'M4 9V5a1 1 0 0 1 1-1h4M15 4h4a1 1 0 0 1 1 1v4M20 15v4a1 1 0 0 1-1 1h-4M9 20H5a1 1 0 0 1-1-1v-4'),

    # ── editor · the 45-degree cut signature ───────────────────────────────
    'file':           ('editor', 'M6 4h8l5 5v11H6zM14 4v5h5'),
    'note':           ('editor', 'M6 4h8l5 5v11H6zM14 4v5h5M9 13h6M9 16h4'),
    'folder':         ('editor', 'M4 7a1 1 0 0 1 1-1h4l2 2h8a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1z'),
    'archive':        ('editor', 'M4 5h16v4H4zM6 9v10a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V9M10 13h4'),
    'code':           ('editor', 'M9 8l-4 4 4 4M15 8l4 4-4 4M13 5l-2 14'),
    'link':           ('editor', 'M10 14a4 4 0 0 0 6 0l3-3a4 4 0 0 0-6-6l-1 1M14 10a4 4 0 0 0-6 0l-3 3a4 4 0 0 0 6 6l1-1'),
    'bookmark':       ('editor', 'M6 4h12v16l-6-4-6 4z'),
    'edit':           ('editor', 'M4 20l1-4L16 5a2 2 0 0 1 3 3L8 19zM14 7l3 3'),

    # ── status ─────────────────────────────────────────────────────────────
    'record':         ('status', '', 'circle:12,12,8|#circle:12,12,3'),
    'live':           ('status', 'M8 8a5 5 0 0 0 0 8M16 16a5 5 0 0 0 0-8M5 5a9 9 0 0 0 0 14M19 19a9 9 0 0 0 0-14',
                       '#circle:12,12,1.5'),
    'circle-check':   ('status', 'M8 12l3 3 5-6', 'circle:12,12,8'),
    'circle-alert':   ('status', 'M12 8v5', 'circle:12,12,8|#circle:12,16,1'),
    'circle-info':    ('status', 'M12 16v-5', 'circle:12,12,8|#circle:12,8,1'),
    'clock':          ('status', 'M12 7v5l3 2', 'circle:12,12,8'),

    # ── social ─────────────────────────────────────────────────────────────
    'heart':          ('social', 'M12 20s-8-4.7-8-9.5A4.5 4.5 0 0 1 12 8a4.5 4.5 0 0 1 8 2.5C20 15.3 12 20 12 20z'),
    'star':           ('social', 'M12 4l2.5 5.5 6 .7-4.5 4.1 1.2 5.9L12 17.3 6.8 20.2 8 14.3 3.5 10.2l6-.7z'),
    'message':        ('social', 'M4 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-7l-5 4v-4H6a2 2 0 0 1-2-2z'),
    'user':           ('social', 'M5 20a7 7 0 0 1 14 0', 'circle:12,8,3.5'),
    'users':          ('social', 'M3 20a6 6 0 0 1 12 0M16 14a6 6 0 0 1 5 6', 'circle:9,8,3.5|circle:17,9,2.5'),
    'mail':           ('social', 'M4 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zM4 8l8 5 8-5'),
    'share':          ('social', 'M9 11l6-3M9 13l6 3', 'circle:17,7,2.5|circle:7,12,2.5|circle:17,17,2.5'),
    'bell':           ('social', 'M6 10a6 6 0 0 1 12 0v5l2 3H4l2-3zM10 21h4'),

    'thumbs-up':      ('social', 'M8 20V10l4-6a2 2 0 0 1 2 2v4h4a2 2 0 0 1 2 2l-1 6a2 2 0 0 1-2 2zM3 11h5v9H3z'),
    'send':           ('social', 'M21 3L3 10l8 3 3 8zM11 13l10-10'),
    # ── ai ────────────────────────────────────────────────────────────────
    'sparkle':        ('ai', 'M10 3l2 5 5 2-5 2-2 5-2-5-5-2 5-2zM18 14l1 2 2 1-2 1-1 2-1-2-2-1 2-1z'),
    'bot':            ('ai', 'M8 8h8a3 3 0 0 1 3 3v4a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3v-4a3 3 0 0 1 3-3zM12 5v3M3 12v2M21 12v2M9 12v2M15 12v2', '#circle:12,3.5,1.5'),
    'brain':              ('ai', 'M12 6c-1.5-1.5-4-1.5-5 .5-2 0-3.5 1.5-3 3.5-1.5 1-1.5 3 0 4 0 2 1.5 3.5 3.5 3 1 1.5 3 1.5 4.5 0zM12 6c1.5-1.5 4-1.5 5 .5 2 0 3.5 1.5 3 3.5 1.5 1 1.5 3 0 4 0 2-1.5 3.5-3.5 3-1 1.5-3 1.5-4.5 0z'),
    'message-sparkle': ('ai', 'M4 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-7l-5 4v-4H6a2 2 0 0 1-2-2zM12 8l1 2 2 1-2 1-1 2-1-2-2-1 2-1z'),
    'wand':           ('ai', 'M13 4l1.2 2.8 2.8 1.2-2.8 1.2-1.2 2.8-1.2-2.8-2.8-1.2 2.8-1.2zM4 20l7-7'),
    'network':        ('ai', 'M7.5 7.5l2.5 2.5M7.5 16.5l2.5-2.5M14.5 12h1.5', 'circle:6,6,2|circle:6,18,2|circle:12,12,2.5|circle:18,12,2'),

    # ── dev ───────────────────────────────────────────────────────────────
    'terminal':       ('dev', 'M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zM8 10l3 3-3 3M13 16h4'),
    'braces':         ('dev', 'M9 4H8a2 2 0 0 0-2 2v4l-2 2 2 2v4a2 2 0 0 0 2 2h1M15 4h1a2 2 0 0 1 2 2v4l2 2-2 2v4a2 2 0 0 1-2 2h-1'),
    'bug':            ('dev', 'M8 10a4 4 0 0 1 8 0v3a4 4 0 0 1-8 0zM9 7l-2-2M15 7l2-2M8 11H4M16 11h4M8 15l-3 3M16 15l3 3'),
    'database':       ('dev', 'M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 6c0 1.7 3.6 3 8 3s8-1.3 8-3-3.6-3-8-3-8 1.3-8 3M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3'),
    'server':         ('dev', 'M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zM4 16a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z', '#circle:8,7,1|#circle:8,17,1'),
    'cpu':            ('dev', 'M6 8a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2zM10 10h4v4h-4zM10 3v3M14 3v3M10 18v3M14 18v3M3 10h3M3 14h3M18 10h3M18 14h3'),
    'git-branch':     ('dev', 'M6 8.5v7M6 10h8l4 4v1.5', 'circle:6,6,2.5|circle:6,18,2.5|circle:18,18,2.5'),
    'git-merge':      ('dev', 'M6 8.5v7M18 8.5V10l-4 4H6', 'circle:6,6,2.5|circle:6,18,2.5|circle:18,6,2.5'),
    'rocket':         ('dev', 'M12 3c3 2.5 4.5 6 4.5 9.5L14 16h-4L7.5 12.5C7.5 9 9 5.5 12 3zM10 16l-2 4 3-1M14 16l2 4-3-1', 'circle:12,10,2'),

    # ── travel ────────────────────────────────────────────────────────────
    'plane':          ('travel', 'M12 3a2 2 0 0 1 2 2v5l7 4v2l-7-2v3l2 2v2l-4-1-4 1v-2l2-2v-3l-7 2v-2l7-4V5a2 2 0 0 1 2-2z'),
    'map-pin':        ('travel', 'M12 21c-4-4.5-7-7.5-7-11a7 7 0 1 1 14 0c0 3.5-3 6.5-7 11z', 'circle:12,10,2.5'),
    'map':            ('travel', 'M3 7l6-3 6 3 6-3v13l-6 3-6-3-6 3zM9 4v13M15 7v13'),
    'globe':          ('travel', 'M12 4c2.5 3 2.5 13 0 16-2.5-3-2.5-13 0-16zM4 12h16', 'circle:12,12,8'),
    'compass':        ('travel', 'M15 9l-2 4-4 2 2-4 4-2', 'circle:12,12,8'),
    'luggage':        ('travel', 'M3 9a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M9 11v6M15 11v6'),
    'mountain':       ('travel', 'M9 13l3 3 3-3M2 20L12 10l10 10z'),

    # ── writing ───────────────────────────────────────────────────────────
    'book':           ('writing', 'M4 5a1 1 0 0 1 1-1h6v16H5a1 1 0 0 0-1 1zM20 5a1 1 0 0 0-1-1h-6v16h6a1 1 0 0 1 1 1z'),
    'newspaper':      ('writing', 'M4 6h12v14H5a1 1 0 0 1-1-1zM16 9h4v9a2 2 0 0 1-2 2M7 10h6M7 14h6'),
    'rss':            ('writing', 'M5 12a7 7 0 0 1 7 7M5 6a13 13 0 0 1 13 13', '#circle:6,18,1.5'),
    'quote':              ('writing', 'M9 6a3 3 0 1 0 0 6c0 2-1.5 3.5-3 4M18 6a3 3 0 1 0 0 6c0 2-1.5 3.5-3 4'),
    'tag':            ('writing', 'M4 11V5a1 1 0 0 1 1-1h6l9 9-7 7z', '#circle:8,8,1.5'),
    'hash':           ('writing', 'M9 4v16M15 4v16M4 9h16M4 15h16'),
}

WRAP = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
        'stroke-linejoin="round">{body}</svg>\n')


def shapes(spec):
    """`circle:12,12,8|#circle:12,16,1` -> svg elements.

    A leading # means FILLED — the record-dot signature, and the only filled
    geometry in the set, so a fill always reads as state rather than drawing.
    """
    out = []
    for part in spec.split('|'):
        if not part:
            continue
        filled = part.startswith('#')
        part = part.lstrip('#')
        kind, _, args = part.partition(':')
        if kind == 'circle':
            cx, cy, r = args.split(',')
            extra = ' fill="currentColor" stroke="none"' if filled else ''
            out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}"{extra}/>')
    return ''.join(out)


def main():
    OUT.mkdir(exist_ok=True)
    written = 0
    for name, spec in sorted(ICONS.items()):
        cat, d = spec[0], spec[1]
        extra = spec[2] if len(spec) > 2 else ''
        body = (f'<path d="{d}"/>' if d else '') + shapes(extra)
        folder = OUT / cat
        folder.mkdir(exist_ok=True)
        (folder / f'{name}.svg').write_text(WRAP.format(body=body))
        written += 1
    cats = sorted({v[0] for v in ICONS.values()})
    print(f'authored {written} icons across {len(cats)} categories: {", ".join(cats)}')


if __name__ == '__main__':
    main()
