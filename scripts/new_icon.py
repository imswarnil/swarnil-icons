#!/usr/bin/env python3
"""new_icon.py — add an icon to the set without hand-editing anything.

    npm run new -- <name> <category> '<path-d>' ['<shapes>']

    npm run new -- flag ui 'M6 4v16M6 5h11l-2 3 2 3H6'
    npm run new -- gauge status 'M12 12l4-3' 'circle:12,12,8'
    npm run new -- target frame '' 'circle:12,12,8|circle:12,12,4|#circle:12,12,1.5'

WHY THIS EXISTS. The geometry table at the top of author.py is the source of
truth for the whole set, and it has to stay that way — one table is what makes
the wrapper, the viewBox, the stroke and the cap/join identical on every icon
rather than 61 files slowly drifting apart. But "edit a Python dict literal in
the right category block, with the right column alignment" is a poor first step
for adding a drawing. So this writes that line for you, in the right place, and
then runs the same author -> validate pass you would have run by hand.

It is a front door to the table, NOT a second source of truth. The line it
writes is an ordinary line you can go and edit afterwards.

    ARGUMENTS
      name       kebab-case, named for WHAT IT IS, not what it does in one
                 product — `circle-check`, never `success`. See STYLE.md § 6.
      category   an existing folder under icons/, or a new one (it is created).
      path-d     SVG path data, drawn on the 24 grid. May be '' for an icon
                 made only of shapes.
      shapes     optional. `circle:cx,cy,r`, joined with `|`. A leading # means
                 FILLED — the record-dot signature. Circles live here rather
                 than in the path because a circle written as arcs is unreadable
                 and impossible to nudge later.

Geometry rules are in STYLE.md and enforced by validate.py, which runs at the
end of this script. If your icon breaks one, you will be told which rule and
the entry stays in the table for you to fix — nothing is silently reverted.
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
AUTHOR = ROOT / 'scripts' / 'author.py'

KEBAB = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
ENTRY = re.compile(r"^\s*'([a-z0-9-]+)':\s*\(\s*'([a-z0-9-]+)'")
CATBAR = re.compile(r'^\s*#\s*──')
# The column the opening paren of every tuple is aligned to, so a generated
# line is indistinguishable from a hand-written one.
COL = 22


def fail(msg):
    print(f'new_icon: {msg}', file=sys.stderr)
    return 1


def entry_line(name, cat, d, shapes):
    key = f"    '{name}':"
    pad = ' ' * max(1, COL - len(key))
    body = f"('{cat}', '{d}'"
    if shapes:
        body += f", '{shapes}'"
    return f'{key}{pad}{body}),\n'


def insert_at(lines, cat):
    """Where does an entry for `cat` belong?

    After the LAST existing entry of that category — so a category stays one
    contiguous block under its own banner comment, which is the only reason
    the table is readable at 60+ icons. The insertion point is the line after
    that entry ends, found by scanning to the next entry, banner or closing
    brace rather than assuming an entry is one line (several are two).

    Returns (index, needs_new_block).
    """
    last = None
    for i, ln in enumerate(lines):
        m = ENTRY.match(ln)
        if m and m.group(2) == cat:
            last = i

    if last is None:
        # A new category: place it at the end of the table, with its own banner.
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith('}'):
                return i, True
        return len(lines), True

    for i in range(last + 1, len(lines)):
        if ENTRY.match(lines[i]) or CATBAR.match(lines[i]) or lines[i].startswith('}'):
            return i, False
    return last + 1, False


def main(argv):
    if not (3 <= len(argv) <= 4):
        print(__doc__)
        return 1

    name, cat, d = argv[0], argv[1], argv[2]
    shapes = argv[3] if len(argv) == 4 else ''

    if not KEBAB.match(name):
        return fail(f"'{name}' is not kebab-case — lowercase words joined by hyphens")
    if not KEBAB.match(cat):
        return fail(f"'{cat}' is not a valid category name")
    if not d and not shapes:
        return fail('an icon needs geometry — give it path data, shapes, or both')
    if "'" in d or "'" in shapes:
        return fail("geometry cannot contain a single quote — it is written into a "
                    "single-quoted Python string")

    src = AUTHOR.read_text()
    lines = src.splitlines(keepends=True)

    for ln in lines:
        m = ENTRY.match(ln)
        if m and m.group(1) == name:
            return fail(f"'{name}' is already in the table ({m.group(2)}) — edit that "
                        f'line to change it, then run: python3 scripts/author.py')

    at, new_block = insert_at(lines, cat)

    block = ''
    if new_block:
        bar = '─' * max(3, 66 - len(cat))
        block = f'\n    # ── {cat} {bar}\n'
    block += entry_line(name, cat, d, shapes)

    lines.insert(at, block)
    AUTHOR.write_text(''.join(lines))
    print(f"added '{name}' to the {cat} block in scripts/author.py")

    # Author, then validate — the same two steps by hand, so this script has no
    # behaviour of its own to keep in sync. --strict matters: without it
    # validate.py REPORTS a broken icon and still exits 0, which would let this
    # script announce success over the top of its own error message.
    steps = (['python3', 'scripts/author.py'],
             ['python3', 'scripts/validate.py', '--strict'])
    for step in steps:
        sys.stdout.flush()          # keep our prints ahead of the child's
        r = subprocess.run(step, cwd=ROOT)
        if r.returncode:
            print(f"\n'{name}' is in the table but {pathlib.Path(step[1]).name} "
                  f'rejected it. The entry was left in place rather than reverted, '
                  f'so fix the geometry on that line in scripts/author.py and '
                  f're-run:\n    npm run new-check', file=sys.stderr)
            return r.returncode

    print(f'\nicons/{cat}/{name}.svg is written and valid. '
          f'Run `npm run build` to see it on the site.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
