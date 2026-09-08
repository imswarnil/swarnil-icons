/* =============================================================================
   icons.imswarnil.com — the browser and the export tool

   Rasterising happens HERE rather than in the build, and that is the important
   decision. A build that pre-renders PNGs has to guess which sizes anyone
   wants, ships thousands of files, and still cannot answer "give me this one
   at 137px". Drawing to a canvas on demand answers every size, in every
   format, from the SVG that is already on the page — and adds no dependency.

   The second decision is that every control in the sidebar is BUILT FROM THE
   DATA and renders a real icon in the state it selects. The weight buttons are
   drawn at their weight; the motion buttons play their animation. A control
   that shows its answer needs no label explaining it, and it cannot fall out
   of step with what the set actually does, because it is the set doing it.
   ========================================================================== */
(function () {
	'use strict';

	var $ = function (s, r) { return (r || document).querySelector(s); };
	var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

	var ICONS = JSON.parse($('#icon-data').textContent);
	// Present only on /icons/. Declared here rather than beside the grid code
	// because the guard further down reads it, and a `var` assigned later
	// would still be undefined at that point — every page would take the
	// early return, including the one that needs the grid.
	var sections = $('[data-sections]');
	var STROKE = { thin: 1, line: 1.5, bold: 2 };

	function byName(n) {
		for (var i = 0; i < ICONS.length; i++) if (ICONS[i].name === n) return ICONS[i];
		return ICONS[0];
	}

	// Categories are a flat field on each icon (the folder they live in).
	// Grouping two or more of them under one nav label is a display concern
	// only, kept here rather than in the data so adding a new flat category
	// never requires touching the build. Anything not listed here renders as
	// its own top-level item — empty for now, no categories need grouping.
	var GROUPS = [];
	var LABELS = { ui: 'UI' };
	// One icon per category, from the set. A category with no entry here still
	// works — it just gets the generic one — so adding a category never breaks
	// the nav.
	var CATICON = {
		ui: 'menu', media: 'play', frame: 'capture',
		editor: 'edit', status: 'record', social: 'heart',
		travel: 'plane', country: 'italy', ai: 'sparkle',
		dev: 'terminal', writing: 'book'
	};
	var grouped = {};
	GROUPS.forEach(function (g) { g.categories.forEach(function (c) { grouped[c] = g; }); });

	function label(cat) {
		return LABELS[cat] || (cat.charAt(0).toUpperCase() + cat.slice(1));
	}

	/* The browser opens ON the scanline, because it is the thing about this set
	   that a grid of glyphs cannot tell you — every other style here is one an
	   icon set is assumed to have.

	   The raster holds at every size — its pitch has a pixel floor — so the
	   size default is free to be whatever browses best, which is md. */
	var state = {
		q: '', cat: '', variant: 'line', size: 'md',
		color: 'scan', flicker: 'off',
		motion: 'off', mode: 'in'
	};
	var current = null, size = 24, panelVariant = 'line';
	var panelMotion = 'off', panelMode = 'in';

	// The export colours, named for the CLASS each one corresponds to in
	// swarnil-icons.css. They are read as custom properties rather than
	// hard-coded here, so the picker shows whatever the loaded stylesheet
	// says --ic-primary is — including a design system that has repointed it.
	var COLOURS = {
		ink:     'var(--ic-ink)',
		primary: 'var(--ic-primary)',
		muted:   'var(--ic-muted)',
		success: 'var(--ic-success)',
		info:    'var(--ic-info)',
		warning: 'var(--ic-warning)',
		danger:  'var(--ic-danger)'
	};
	var panelColour = 'ink', customColour = '#e2593a';

	function stored(key, fallback) {
		try { return localStorage.getItem(key) || fallback; } catch (e) { return fallback; }
	}
	var primary = stored('si-primary', 'signal');
	var secondary = stored('si-secondary', 'ink');
	// The two eyedroppers. They keep their own hex so switching to a named hue
	// and back returns the colour you mixed rather than a default.
	var primaryCustom = stored('si-primary-custom', '#e2593a');
	var secondaryCustom = stored('si-secondary-custom', '#3a6ee2');

	/* The design system's tier-1 hues at their ~63% "full voice" step — one
	   shared lightness ladder, so swapping between them changes the hue and
	   nothing else. Signal is the system's own accent and the default here.

	   Picking one sets --accent on :root, and because swarnil-icons.css reads
	   `var(--accent, <signal>)` for --ic-primary, the icons rebrand along with
	   the page. That is the same mechanism a real consumer gets by loading the
	   design system; this rail is just proving it. */
	var PALETTE = {
		signal: 'oklch(63% 0.190 34)',
		craft:  'oklch(66% 0.110 78)',
		mint:   'oklch(64% 0.130 155)',
		teal:   'oklch(65% 0.105 195)',
		azure:  'oklch(62% 0.145 240)',
		iris:   'oklch(62% 0.170 285)',
		rose:   'oklch(60% 0.185 15)'
	};
	// Secondary is the ink the strokes are drawn in. Default is the text
	// colour, which is the whole point of the set — it disappears into its
	// surroundings unless told otherwise.
	var INKS = { ink: '', signal: PALETTE.signal, azure: PALETTE.azure,
	             iris: PALETTE.iris, mint: PALETTE.mint, craft: PALETTE.craft };

	// What the two rails are actually SET to, named hue or mixed hex. Every
	// reader goes through these rather than indexing the tables directly, so
	// `custom` needs no special case anywhere else.
	function primaryHue() { return primary === 'custom' ? primaryCustom : (PALETTE[primary] || PALETTE.signal); }
	function secondaryHue() { return secondary === 'custom' ? secondaryCustom : INKS[secondary]; }

	var MOTIONS = ['off', 'draw', 'fade', 'pop', 'spin', 'pulse', 'tv'];
	var MODES = ['in', 'out', 'loop'];

	/* ── Theme ───────────────────────────────────────────────────────────── */

	function themeIcon() {
		var dark = document.documentElement.dataset.theme === 'dark';
		var use = $('[data-theme-icon]');
		// Show the theme you would GET by clicking, not the one you are in —
		// a button that pictures the current state looks like a status light.
		if (use) use.setAttribute('href', dark ? '#i-aperture' : '#i-moon');
		var btn = $('[data-theme-toggle]');
		if (btn) btn.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
	}
	themeIcon();

	$('[data-theme-toggle]').addEventListener('click', function () {
		var next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
		document.documentElement.dataset.theme = next;
		try { localStorage.setItem('si-theme', next); } catch (e) {}
		themeIcon();
	});

	/* ── The palette ─────────────────────────────────────────────────────── */

	function applyPalette() {
		var root = document.documentElement.style;
		var c = primaryHue();

		root.setProperty('--accent', c);
		// The two derived accent tones are mixed from the chosen hue rather
		// than listed per colour, so adding a hue above needs nothing here.
		// --accent-soft is an alpha wash, which lands correctly on a light or
		// a dark ground; --accent-fg is pulled toward the page's own text
		// colour so it stays readable in both themes.
		root.setProperty('--accent-soft', 'color-mix(in oklab, ' + c + ' 14%, transparent)');
		root.setProperty('--accent-fg', 'color-mix(in oklab, ' + c + ' 72%, var(--fg-default))');
		// --ic-primary-soft reads --accent-soft, which is now an alpha wash;
		// give the icons a slightly stronger one so a fill still reads as a
		// fill rather than as a smudge.
		root.setProperty('--ic-primary-soft', 'color-mix(in oklab, ' + c + ' 20%, transparent)');

		var ink = secondaryHue();
		if (ink) root.setProperty('--ic-ink', ink);
		else root.removeProperty('--ic-ink');

		try {
			localStorage.setItem('si-primary', primary);
			localStorage.setItem('si-secondary', secondary);
			localStorage.setItem('si-primary-custom', primaryCustom);
			localStorage.setItem('si-secondary-custom', secondaryCustom);
		} catch (e) {}
	}
	applyPalette();

	/* ── Building one icon's SVG ─────────────────────────────────────────── */

	function svgMarkup(icon, variant, px, cls, style) {
		return '<svg xmlns="http://www.w3.org/2000/svg" width="' + px + '" height="' + px + '"'
			+ (cls ? ' class="' + cls + '"' : '')
			+ (style ? ' style="' + style + '"' : '')
			+ ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="' + STROKE[variant] + '"'
			+ ' stroke-linecap="round" stroke-linejoin="round">' + icon.body + '</svg>';
	}

	/* A scanline sample.

	   It states no pitch of its own: .ic-scan floors at 1.2px and a rail button
	   draws at 20px, so the class already gives the sample the same raster the
	   grid behind it is showing. That is what the floor bought — before it,
	   this function had to state an exaggerated pitch in pixels to have
	   anything to display at all, and a control showing an exaggeration of its
	   answer is a control that can lie. */
	function scanSample(extra) {
		return svgMarkup(DEMO, 'bold', 20, ('ic-scan ' + extra).trim());
	}

	// The class the motion layer wants, or '' for off. One place, because the
	// grid, the sidebar previews, the hero and the panel all need the same
	// answer and a second copy would drift.
	function motionClass(name, mode) {
		return (!name || name === 'off') ? '' : 'ic-' + name + '-' + mode;
	}

	/* ── Filters ─────────────────────────────────────────────────────────── */

	/* ── Search ──────────────────────────────────────────────────────────────
	   Two answers to one query, because they are different questions. The grid
	   below filters, which answers "what is there" — you browse the result. The
	   dropdown lists the closest few, which answers "the one I already had in
	   mind" — you take it and go. A set this size needs both. */

	var input = $('[data-search]');
	var ac = $('[data-ac]');
	var box = $('[data-searchbox]');
	var hits = [], cursor = -1;

	function score(icon, q) {
		var n = icon.name;
		if (n === q) return 0;
		if (n.indexOf(q) === 0) return 1;          // prefix beats
		if (n.indexOf(q) !== -1) return 2;         // anywhere in the name
		if (icon.category.indexOf(q) !== -1) return 3;
		return -1;
	}

	function closeAc() {
		ac.hidden = true;
		box.setAttribute('aria-expanded', 'false');
		cursor = -1;
	}

	function markCursor() {
		$$('.ac__row', ac).forEach(function (el, i) {
			el.setAttribute('aria-selected', String(i === cursor));
		});
	}

	function openAc(q) {
		hits = ICONS.map(function (i) { return { i: i, s: score(i, q) }; })
			.filter(function (r) { return r.s !== -1; })
			.sort(function (a, b) { return a.s - b.s || a.i.name.localeCompare(b.i.name); })
			.slice(0, 8)
			.map(function (r) { return r.i; });

		if (!hits.length) return closeAc();

		ac.innerHTML = hits.map(function (i, n) {
			return '<li class="ac__row" role="option" aria-selected="false" data-pick="' + i.name + '" id="ac-' + n + '">'
				+ svgMarkup(i, 'line', 20)
				+ '<span class="ac__name">' + i.name + '</span>'
				+ '<span class="ac__cat">' + label(i.category) + '</span></li>';
		}).join('');
		ac.hidden = false;
		box.setAttribute('aria-expanded', 'true');
		cursor = -1;
		markCursor();
	}

	// Off the browser page there is no grid to filter, only the dropdown.
	function pick(name) {
		if (sections) { open(name); return; }
		location.href = '/icons/#' + name;
	}

	input.addEventListener('input', function (e) {
		state.q = e.target.value.trim();
		if (sections) render();
		if (state.q) openAc(state.q.toLowerCase()); else closeAc();
	});

	input.addEventListener('keydown', function (e) {
		if (ac.hidden) return;
		if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
			e.preventDefault();
			cursor = (cursor + (e.key === 'ArrowDown' ? 1 : -1) + hits.length + 1) % (hits.length + 1);
			// The extra slot is "nothing selected", so arrowing past the end
			// returns you to the raw query rather than wrapping silently.
			if (cursor === hits.length) cursor = -1;
			markCursor();
			input.setAttribute('aria-activedescendant', cursor < 0 ? '' : 'ac-' + cursor);
		} else if (e.key === 'Enter' && cursor > -1) {
			e.preventDefault();
			pick(hits[cursor].name);
			closeAc();
		} else if (e.key === 'Escape') {
			closeAc();
		}
	});

	ac.addEventListener('mousedown', function (e) {
		// mousedown, not click: the input's blur would hide the row before a
		// click ever landed on it.
		var row = e.target.closest('[data-pick]');
		if (!row) return;
		e.preventDefault();
		pick(row.dataset.pick);
		closeAc();
	});

	document.addEventListener('click', function (e) {
		if (!box.contains(e.target)) closeAc();
	});

	document.addEventListener('keydown', function (e) {
		if (e.key === '/' && !/^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName)) {
			e.preventDefault();
			input.focus();
		}
	});

	/* One route in, whatever the control was.

	   The rail is two kinds of widget — toggles and dropdowns — and a colour
	   can also be driven from the eyedropper beside its row rather than from a
	   toggle at all. Every one of them lands here, so the rule for what a
	   selection DOES is written once and cannot be half-implemented on the
	   control that was added last. */
	var GROUPS_ = ['variant', 'psize', 'colormode', 'flicker',
	               'motion', 'mode', 'primary', 'secondary', 'pmotion', 'pmode'];

	function choose(group, v) {
		if (group === 'variant') state.variant = v;
		if (group === 'psize') state.size = v;
		if (group === 'colormode') state.color = v;
		if (group === 'flicker') state.flicker = v;
		if (group === 'motion') state.motion = v;
		if (group === 'mode') state.mode = v;
		if (group === 'primary') primary = v;
		if (group === 'secondary') secondary = v;
		if (group === 'pmotion') panelMotion = v;
		if (group === 'pmode') panelMode = v;

		repaintControl(group, v);
		if (group === 'primary' || group === 'secondary') {
			applyPalette();
			// The sidebar samples are drawn markup, not live classes, so they
			// have to be redrawn for the new hue to reach them.
			paintOpts('colormode', state.color);
			paintOpts('primary', primary);
			paintOpts('secondary', secondary);
		}
		if (group === 'pmotion' || group === 'pmode') paint(); else render();
	}

	function repaintControl(group, v) {
		if (SELECTS[group]) paintSelect(group, v);
		else paintOpts(group, v);
	}

	// One delegated listener for every generated control, rather than rebinding
	// after each repaint.
	document.addEventListener('click', function (e) {
		var b = e.target.closest(GROUPS_.map(function (g) { return '[data-' + g + ']'; }).join(','));
		if (!b || !b.classList.contains('opt')) return;

		var group = GROUPS_.filter(function (g) { return b.hasAttribute('data-' + g); })[0];
		choose(group, b.getAttribute('data-' + group));
	});

	document.addEventListener('input', function (e) {
		var el = e.target;
		// The eyedroppers. Setting the hex and selecting `custom` are one
		// action — a colour you mixed and then had to click again to apply
		// would be a bug report.
		var c = el.getAttribute('data-custom');
		if (c === 'primary') { primaryCustom = el.value; choose('primary', 'custom'); }
		if (c === 'secondary') { secondaryCustom = el.value; choose('secondary', 'custom'); }
	});

	document.addEventListener('change', function (e) {
		var g = e.target.getAttribute('data-select-input');
		if (g) choose(g, e.target.value);
	});

	/* ── The hero showcase ───────────────────────────────────────────────── */

	// Seven icons drawing themselves on a loop, staggered. It is the motion
	// layer running, not a screenshot of it.
	var SHOW = ['capture', 'activity', 'aperture', 'heart', 'camera', 'star', 'live'];
	var showcase = $('[data-showcase]');
	if (showcase) {
		showcase.innerHTML = SHOW.map(function (n, i) {
			return '<span class="showcase__cell" style="--ic-delay:' + (i * 160) + 'ms">'
				+ svgMarkup(byName(n), 'line', 40, 'ic-draw-loop') + '</span>';
		}).join('');
	}

	/* ── Everything above runs on all three pages. ───────────────────────
	   The bar, its search and the hero showcase are shared; the rail, the
	   grid and the export panel exist only on /icons/, so the rest of this
	   file is skipped everywhere else rather than guarded line by line. */

	if (!sections) return;

	/* ── The sidebar ─────────────────────────────────────────────────────── */

	var cats = {};
	ICONS.forEach(function (i) { cats[i.category] = (cats[i.category] || 0) + 1; });
	var ungrouped = Object.keys(cats).filter(function (c) { return !grouped[c]; }).sort();

	function catIcon(cat) {
		return '<svg class="ic ic-sm" aria-hidden="true"><use href="#i-'
			+ (CATICON[cat] || 'box') + '"/></svg>';
	}

	function navItem(cat, child) {
		return '<button class="nav__item' + (child ? ' nav__item--child' : '') + '" type="button"'
			+ ' data-cat="' + cat + '" aria-pressed="false">'
			+ catIcon(cat)
			+ '<span class="nav__label">' + label(cat) + '</span>'
			+ '<span class="nav__count">' + cats[cat] + '</span></button>';
	}

	var nav = '<p class="rail__head">Categories</p>'
		+ '<button class="nav__item" type="button" data-cat="" aria-pressed="true">'
		+ '<svg class="ic ic-sm" aria-hidden="true"><use href="#i-box"/></svg>'
		+ '<span class="nav__label">All</span>'
		+ '<span class="nav__count">' + ICONS.length + '</span></button>'
		+ ungrouped.map(function (c) { return navItem(c, false); }).join('');

	GROUPS.forEach(function (g) {
		var present = g.categories.filter(function (c) { return cats[c]; });
		if (!present.length) return;
		nav += '<p class="nav__group">' + g.label + '</p>'
			+ present.map(function (c) { return navItem(c, true); }).join('');
	});

	$('[data-catnav]').innerHTML = nav;

	function setActiveCat(cat) {
		$$('[data-catnav] [data-cat]').forEach(function (b) {
			b.setAttribute('aria-pressed', String(b.dataset.cat === cat));
		});
	}

	$('[data-catnav]').addEventListener('click', function (e) {
		var b = e.target.closest('[data-cat]');
		if (!b) return;
		state.cat = b.dataset.cat;
		setActiveCat(state.cat);
		render();
	});

	/* ── The display controls ────────────────────────────────────────────────
	   Every one of these is generated, and every one previews itself. */

	var DEMO = byName('aperture');      // a ring and a dot: reads at 20px
	var MOVER = byName('activity');     // one open path, so `draw` reads clearly

	var OPTS = {
		variant: {
			values: ['thin', 'line', 'bold'],
			// `line` is the class name the package ships and `Regular` is what
			// a weight in the middle is called. Both are true; the label is
			// for the reader and the value is for the stylesheet.
			label: { thin: 'Thin', line: 'Regular', bold: 'Bold' },
			art: function (v) { return svgMarkup(DEMO, v, 20); }
		},
		psize: {
			values: ['sm', 'md', 'lg', 'xl'],
			label: { sm: 'S', md: 'M', lg: 'L', xl: 'XL' },
			// Drawn at the size it selects, capped so the rail stays a rail.
			art: function (v) { return svgMarkup(DEMO, 'line', { sm: 13, md: 16, lg: 20, xl: 26 }[v]); }
		},
		colormode: {
			values: ['mono', 'multi', 'scan', 'scan-roll'],
			label: { mono: 'Mono', multi: 'Multi', scan: 'Scanline', 'scan-roll': 'Scanline rolling' },
			// Each sample is the real class doing the real thing, so a toggle
			// cannot promise one look and deliver another.
			art: function (v) {
				if (v === 'multi') return svgMarkup(DEMO, 'line', 20, 'ic-multi ic-multi-fill');
				if (v === 'scan') return scanSample('');
				if (v === 'scan-roll') return scanSample('ic-scan-roll');
				return svgMarkup(DEMO, 'line', 20);
			}
		},
		flicker: {
			values: ['off', 'on'],
			label: { off: 'Steady', on: 'Flicker' },
			art: function (v) {
				return v === 'on' ? scanSample('ic-flicker') : svgMarkup(DEMO, 'bold', 20);
			}
		},
		primary: {
			values: Object.keys(PALETTE),
			// `custom` is never one of `values` — it is what the eyedropper
			// sets — but the rail heading still has to have a word for it.
			label: { signal: 'Signal', craft: 'Craft', mint: 'Mint', teal: 'Teal',
			         azure: 'Azure', iris: 'Iris', rose: 'Rose', custom: 'Custom' },
			art: function (v) { return '<span class="dot" style="background:' + PALETTE[v] + '"></span>'; },
			pick: function () { return picker('primary', primaryCustom); }
		},
		secondary: {
			values: Object.keys(INKS),
			label: { ink: 'Ink', signal: 'Signal', azure: 'Azure', iris: 'Iris',
			         mint: 'Mint', craft: 'Craft', custom: 'Custom' },
			art: function (v) {
				return '<span class="dot' + (v === 'ink' ? ' dot--ink' : '') + '"'
					+ (INKS[v] ? ' style="background:' + INKS[v] + '"' : '') + '></span>';
			},
			pick: function () { return picker('secondary', secondaryCustom); }
		},
		motion: {
			values: MOTIONS,
			label: { off: 'None', draw: 'Draw', fade: 'Fade', pop: 'Pop',
			         spin: 'Spin', pulse: 'Pulse', tv: 'TV' }
		},
		mode: {
			values: MODES,
			label: { in: 'In', out: 'Out', loop: 'Loop' }
		}
	};

	// The panel repeats the two motion groups under their own attribute names,
	// so a click there cannot be mistaken for the sidebar's copy. Same config,
	// different data-attribute — aliased rather than duplicated.
	OPTS.pmotion = OPTS.motion;
	OPTS.pmode = OPTS.mode;

	// Which groups are dropdowns. Motion is the one axis with no useful sample
	// at rail size, and the two of them together were ten buttons deciding one
	// thing; a pair of selects says it in two lines.
	var SELECTS = { motion: 1, mode: 1, pmotion: 1, pmode: 1 };

	function optText(group, v) {
		var cfg = OPTS[group];
		return (cfg.label && cfg.label[v]) || v;
	}

	/* ── The two renderers ────────────────────────────────────────────────
	   Toggles and dropdowns read the same OPTS entry, so a group moves between
	   them by naming it in SELECTS above rather than by rewriting its markup.
	   `values` is the order in both cases, which is what the segmented weight
	   and size groups need and what a select gets for free. */

	function optButton(group, v, pressed) {
		var text = optText(group, v);
		return '<button class="opt" type="button" data-' + group + '="' + v + '"'
			// aria-label only — no title. A native tooltip would open on top of
			// the styled one and say the same word twice.
			+ ' aria-pressed="' + pressed + '" aria-label="' + text + '">'
			+ '<span class="opt__art">' + OPTS[group].art(v) + '</span></button>';
	}

	// The eyedropper that closes a colour row. A <label> wrapping a colour
	// input rather than a button, because that is the one control the platform
	// will open a real colour picker for — so it takes a class instead of
	// aria-pressed, which a screen reader cannot report on a label.
	function picker(group, hex) {
		var on = (group === 'primary' ? primary : secondary) === 'custom';
		return '<label class="opt opt--pick' + (on ? ' is-on' : '') + '" aria-label="Custom">'
			+ '<input class="opt__pick" type="color" value="' + hex + '" data-custom="' + group + '" />'
			+ '<span class="u-sr-only">Custom ' + group + ' colour</span></label>';
	}

	// A group can appear more than once (the sidebar and the panel both show
	// motion), so this fills every holder that asks for it.
	function paintOpts(group, selected) {
		var cfg = OPTS[group];
		$$('[data-optgroup="' + group + '"]').forEach(function (holder) {
			holder.innerHTML = cfg.values.map(function (v) {
				return optButton(group, v, String(v === selected));
			}).join('') + (cfg.pick ? cfg.pick() : '');
		});
		showNow(group, selected);
	}

	function paintSelect(group, selected) {
		$$('[data-select="' + group + '"]').forEach(function (holder) {
			holder.innerHTML = '<select class="sel__input" data-select-input="' + group + '">'
				+ OPTS[group].values.map(function (v) {
					return '<option value="' + v + '"' + (v === selected ? ' selected' : '') + '>'
						+ optText(group, v) + '</option>';
				}).join('') + '</select>';
		});
		showNow(group, selected);
	}

	function showNow(group, selected) {
		$$('[data-now="' + group + '"]').forEach(function (el) {
			el.textContent = optText(group, selected);
		});
	}

	repaintControl('variant', state.variant);
	repaintControl('psize', state.size);
	repaintControl('colormode', state.color);
	repaintControl('flicker', state.flicker);
	repaintControl('primary', primary);
	repaintControl('secondary', secondary);
	repaintControl('motion', state.motion);
	repaintControl('mode', state.mode);
	repaintControl('pmotion', panelMotion);
	repaintControl('pmode', panelMode);

	/* ── The grid ────────────────────────────────────────────────────────── */

	// Is the scanline moving? Both the roll and the flicker are declared with
	// the animation SHORTHAND, so either of them and a motion class on the same
	// element is one animation cancelling the other rather than two playing.
	// This is the test the grid and the note below both ask.
	function scanMoving() {
		return state.color === 'scan-roll' || (isScan() && state.flicker === 'on');
	}
	function isScan() { return state.color === 'scan' || state.color === 'scan-roll'; }

	// The scanline as a class list: the mask, and whichever of the two
	// movements are on. Assembled once here so the grid, the note and the
	// export all describe the same icon.
	function scanClasses() {
		if (!isScan()) return [];
		var cls = ['ic-scan'];
		if (state.color === 'scan-roll') cls.push('ic-scan-roll');
		if (state.flicker === 'on') cls.push('ic-flicker');
		return cls;
	}

	function cellsFor(rows) {
		var mcls = scanMoving() ? '' : motionClass(state.motion, state.mode);
		var multi = state.color === 'multi';
		var scan = scanClasses();
		return rows.map(function (i, n) {
			// Every style is added as CLASSES on one drawing rather than by
			// swapping in a different one, so they compose with whatever weight
			// the weight group is on instead of overriding it. That is the whole
			// reason the set has three weights and no fourth "solid" form: a
			// style should change how an icon is dressed, never which icon it
			// is.
			var cls = [mcls];
			if (multi) {
				cls.push('ic-multi');
				// The wash only goes on icons that enclose an area; on an open
				// path it would flood the region the path merely implies.
				if (i.closed) cls.push('ic-multi-fill');
			}
			cls = cls.concat(scan);
			// A tiny per-cell delay so a grid of 103 icons arrives as a sweep
			// rather than as one flash. Capped, or the last cell waits a
			// second and a half to appear.
			var delay = state.motion === 'off' ? '' :
				' style="--ic-delay:' + Math.min(n * 18, 420) + 'ms"';
			return '<button class="cell" type="button" data-name="' + i.name + '" data-cat="' + i.category + '" title="' + i.name + '"' + delay + '>'
				+ svgMarkup(i, state.variant, 24, cls.filter(Boolean).join(' '))
				+ '<span class="cell__name">' + i.name + '</span></button>';
		}).join('');
	}

	function render() {
		var q = state.q.toLowerCase();
		var rows = ICONS.filter(function (i) {
			return (!state.cat || i.category === state.cat)
				&& (!q || i.name.indexOf(q) !== -1 || i.category.indexOf(q) !== -1);
		});

		// gridsize, not size: the panel's range input is [data-size], and
		// `sections` sits before the dialog in document order, so a bare
		// [data-size] lookup would find this div instead of the slider.
		sections.dataset.gridsize = state.size;
		sections.dataset.colormode = state.color;

		if (state.cat) {
			// One category already named in the sidebar — a repeated header
			// above the grid would just say the same word twice.
			sections.innerHTML = '<div class="grid">' + cellsFor(rows) + '</div>';
		} else {
			var order = ungrouped.slice();
			GROUPS.forEach(function (g) { order = order.concat(g.categories); });
			sections.innerHTML = order.map(function (cat) {
				var inCat = rows.filter(function (i) { return i.category === cat; });
				if (!inCat.length) return '';
				return '<section class="section">'
					+ '<h2 class="section__title">' + catIcon(cat) + ' ' + label(cat)
					+ ' <span class="section__count">' + inCat.length + '</span></h2>'
					+ '<div class="grid">' + cellsFor(inCat) + '</div></section>';
			}).join('');
		}

		$('[data-count]').textContent = rows.length + (rows.length === 1 ? ' icon' : ' icons');
		$('[data-empty]').hidden = rows.length > 0;

		// The scanline's own controls, present only while it is the style.
		$('[data-scanopts]').hidden = !isScan();

		/* There used to be a warning here about the raster going invisible
		   below a certain size. It is gone because the condition it warned
		   about is gone: .ic-scan's pitch has a 1.2px floor, so the gap between
		   scan lines is 0.42px at every size this page can show. A warning for
		   an impossible state is a warning people learn to ignore. */
		var note = $('[data-motion-note]');
		if (scanMoving()) {
			note.textContent = 'A moving scanline is already an animation, so it '
				+ 'overrides the one chosen here. Set it to Steady, or use the '
				+ 'static Scanline, to have both.';
			note.hidden = false;
		} else {
			note.hidden = true;
		}
	}

	/* ── The panel ───────────────────────────────────────────────────────── */

	var panel = $('[data-panel]');

	function paint() {
		if (!current) return;
		var v = panelVariant;

		// Rendered AT the chosen size, not at a fixed preview size — dragging
		// the slider has to change what you are looking at, or the number is
		// the only feedback you get. The stage caps how large it can draw
		// (see .panel__icon); the readout keeps reporting the real value.
		var holder = $('[data-panel-icon]').parentNode;
		holder.innerHTML = svgMarkup(current, v, size, motionClass(panelMotion, panelMode))
			.replace('<svg ', '<svg data-panel-icon ');
		var ico = $('[data-panel-icon]');
		ico.classList.add('panel__icon');
		ico.style.color = panelColour === 'custom' ? customColour : COLOURS[panelColour];

		$('[data-size-out]').textContent = size + ' px';
		// Ink is the idiomatic form — the icon inherits its surroundings, so
		// the markup keeps currentColor and the reader can paste it anywhere.
		// Any OTHER choice is a deliberate colour, so it is baked in and the
		// snippet matches the file the download button writes.
		var snippet = panelColour === 'ink'
			? svgMarkup(current, v, size)
			: svgMarkup(current, v, size).replace(/currentColor/g, exportColour());
		// innerHTML, because highlight() returns markup. It escapes its input
		// first, so the icon's own angle brackets can never become elements.
		$('[data-panel-code]').innerHTML = highlight(snippet);
	}

	function open(name) {
		current = byName(name);
		$('[data-panel-name]').textContent = current.name;
		$('[data-panel-cat]').textContent = current.category;
		paint();
		panel.showModal();
	}

	sections.addEventListener('click', function (e) {
		var cell = e.target.closest('.cell');
		if (cell) open(cell.dataset.name);
	});

	$$('[data-pvariant]').forEach(function (b) {
		b.addEventListener('click', function () {
			$$('[data-pvariant]').forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
			b.setAttribute('aria-pressed', 'true');
			panelVariant = b.dataset.pvariant;
			paint();
		});
	});

	/* ── Colour ──────────────────────────────────────────────────────────── */

	var customLabel = $('.swatch--custom');

	function setColour(which) {
		panelColour = which;
		$$('[data-pcolor]').forEach(function (o) {
			o.setAttribute('aria-pressed', String(o.dataset.pcolor === which));
		});
		// The custom control is a <label> around a colour input rather than a
		// button, so it takes a class instead of aria-pressed — a pressed
		// state on a label is not something a screen reader can report.
		if (customLabel) customLabel.classList.toggle('is-on', which === 'custom');
		paint();
	}

	$$('[data-pcolor]').forEach(function (b) {
		b.addEventListener('click', function () { setColour(b.dataset.pcolor); });
	});

	var customInput = $('[data-pcolor-custom]');
	if (customInput) {
		customInput.addEventListener('input', function () {
			customColour = customInput.value;
			setColour('custom');
		});
	}

	$('[data-size]').addEventListener('input', function (e) {
		size = parseInt(e.target.value, 10);
		paint();
	});

	/* ── Syntax highlighting ─────────────────────────────────────────────────
	   Forty lines instead of a highlighting library, because this set has no
	   dependencies and one code block is not a reason to acquire one. It only
	   has to handle SVG, which is a far smaller problem than "any language".

	   ORDER MATTERS and it is the only subtle part. Everything is escaped
	   first, so the source's own < and > become entities. Attributes are
	   wrapped next, and tags last — and the tag pattern matches `&lt;name`,
	   which the real <span> tags just inserted cannot look like. Wrap tags
	   first and the attribute pass would happily mangle class="t-tag". */
	function highlight(src) {
		var out = src.replace(/[&<>]/g, function (c) {
			return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c];
		});
		out = out.replace(/([a-zA-Z-:]+)="([^"]*)"/g,
			'<span class="t-attr">$1</span>=<span class="t-val">"$2"</span>');
		out = out.replace(/(&lt;\/?)([a-zA-Z][\w-]*)/g,
			'$1<span class="t-tag">$2</span>');
		return out;
	}

	/* ── Export ──────────────────────────────────────────────────────────── */

	/* The colour the picker is currently showing, as a plain sRGB hex.

	   Two conversions happen here and both matter. First the custom property
	   is resolved — --ic-primary is only a name until something computes it.
	   Then the result is pushed through a 1x1 canvas and read back as a pixel,
	   which flattens whatever colour space it was written in down to sRGB hex.

	   That second step is the portable one. The tokens are authored in
	   oklch(), and an SVG file carrying `stroke="oklch(63% 0.19 34)"` renders
	   in a current browser and fails silently in plenty of design tools that
	   still parse CSS Color 3. A hex opens everywhere, and the canvas is doing
	   the same gamut clamp the screen already did. */
	function exportColour() {
		var el = $('[data-panel-icon]');
		var css = el ? getComputedStyle(el).color : getComputedStyle(document.body).color;

		var c = document.createElement('canvas');
		c.width = c.height = 1;
		var ctx = c.getContext('2d');
		ctx.fillStyle = '#000';
		ctx.fillStyle = css;          // left at #000 if the value won't parse
		ctx.fillRect(0, 0, 1, 1);
		var d = ctx.getImageData(0, 0, 1, 1).data;
		return '#' + [d[0], d[1], d[2]].map(function (n) {
			return (n < 16 ? '0' : '') + n.toString(16);
		}).join('');
	}

	function save(blob, filename) {
		var url = URL.createObjectURL(blob);
		var a = document.createElement('a');
		a.href = url;
		a.download = filename;
		document.body.appendChild(a);
		a.click();
		a.remove();
		setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
	}

	function currentSvg() {
		// currentColor cannot survive leaving the page — there is no
		// surrounding text in a downloaded file to inherit from — so it is
		// always resolved, even when the picker is on ink.
		return svgMarkup(current, panelVariant, size).replace(/currentColor/g, exportColour());
	}

	// name-variant-colour-size. The colour is in there because exporting the
	// same icon in three colours otherwise writes the same filename three
	// times and the browser silently appends (1), (2).
	function stem() {
		return current.name + '-' + panelVariant
			+ (panelColour === 'ink' ? '' : '-' + panelColour) + '-' + size;
	}

	function raster(type) {
		var markup = currentSvg();
		var img = new Image();
		var svgBlob = new Blob([markup], { type: 'image/svg+xml;charset=utf-8' });
		var url = URL.createObjectURL(svgBlob);

		img.onload = function () {
			var c = document.createElement('canvas');
			// Render at 2x and scale down: a 24px icon exported at 24 CSS px is
			// unusably soft on any modern display.
			c.width = size * 2;
			c.height = size * 2;
			var ctx = c.getContext('2d');
			if (type === 'image/jpeg') {
				// JPEG has no alpha; without this the transparent ground turns
				// black rather than white.
				ctx.fillStyle = getComputedStyle(document.body).backgroundColor || '#fff';
				ctx.fillRect(0, 0, c.width, c.height);
			}
			ctx.drawImage(img, 0, 0, c.width, c.height);
			URL.revokeObjectURL(url);
			c.toBlob(function (b) {
				save(b, stem() + (type === 'image/jpeg' ? '.jpg' : '.png'));
			}, type, 0.92);
		};
		img.src = url;
	}

	$$('[data-dl]').forEach(function (b) {
		b.addEventListener('click', function () {
			var kind = b.dataset.dl;
			if (kind === 'svg') {
				save(new Blob([currentSvg()], { type: 'image/svg+xml' }), stem() + '.svg');
			} else {
				raster(kind === 'jpg' ? 'image/jpeg' : 'image/png');
			}
		});
	});

	function flash(btn, word) {
		var was = btn.innerHTML;
		btn.textContent = word;
		setTimeout(function () { btn.innerHTML = was; }, 1200);
	}

	// The class list the current selections add up to. This is the thing you
	// actually paste into an existing component, so it is worth its own button.
	function classList() {
		return ['ic', 'ic-lg']
			.concat(panelVariant === 'line' ? [] : ['ic-' + panelVariant])
			.concat(panelColour === 'ink' || panelColour === 'custom' ? [] : ['ic-' + panelColour])
			.concat(motionClass(panelMotion, panelMode) || [])
			.join(' ');
	}

	$('[data-copy-svg]').addEventListener('click', function () {
		var b = this;
		navigator.clipboard.writeText($('[data-panel-code]').textContent).then(function () { flash(b, 'Copied'); });
	});

	$('[data-copy-use]').addEventListener('click', function () {
		var b = this;
		var use = '<svg class="' + classList() + '"><use href="/sprite.svg#i-' + current.name + '"/></svg>';
		navigator.clipboard.writeText(use).then(function () { flash(b, 'Copied'); });
	});

	$('[data-copy-class]').addEventListener('click', function () {
		var b = this;
		navigator.clipboard.writeText(classList()).then(function () { flash(b, 'Copied'); });
	});

	render();

	// Arriving from the bar's search on another page. The hash is the icon's
	// name, so the panel opens on the one that was actually chosen rather than
	// dropping the reader into 61 tiles to find it again.
	if (location.hash.length > 1) {
		var wanted = decodeURIComponent(location.hash.slice(1));
		if (ICONS.some(function (i) { return i.name === wanted; })) open(wanted);
	}
}());
