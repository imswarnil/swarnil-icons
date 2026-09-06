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
	var STROKE = { thin: 1, line: 1.5, bold: 2, solid: 1.5, duo: 1.5 };

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
		editor: 'edit', status: 'record', social: 'heart'
	};
	var grouped = {};
	GROUPS.forEach(function (g) { g.categories.forEach(function (c) { grouped[c] = g; }); });

	function label(cat) {
		return LABELS[cat] || (cat.charAt(0).toUpperCase() + cat.slice(1));
	}

	var state = {
		q: '', cat: '', variant: 'line', size: 'md',
		color: 'mono', motion: 'off', mode: 'in'
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

	var MOTIONS = ['off', 'draw', 'fade', 'pop', 'spin', 'pulse'];
	var MODES = ['in', 'out', 'loop'];
	var MODEICON = { in: 'arrow-down', out: 'arrow-up', loop: 'refresh' };

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

	/* ── Building one icon's SVG ─────────────────────────────────────────── */

	function svgMarkup(icon, variant, px, cls) {
		var solid = variant === 'solid';
		var body = icon.body;
		if (solid) {
			body = body.replace(/<path /g, '<path fill="currentColor" stroke="none" ')
			           .replace(/<circle (?![^>]*fill=)/g, '<circle fill="currentColor" stroke="none" ');
		}
		var op = variant === 'duo' ? ' opacity="0.45"' : '';
		return '<svg xmlns="http://www.w3.org/2000/svg" width="' + px + '" height="' + px + '"'
			+ (cls ? ' class="' + cls + '"' : '')
			+ ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="' + STROKE[variant] + '"'
			+ ' stroke-linecap="round" stroke-linejoin="round"' + op + '>' + body + '</svg>';
	}

	// The class the motion layer wants, or '' for off. One place, because the
	// grid, the sidebar previews, the hero and the panel all need the same
	// answer and a second copy would drift.
	function motionClass(name, mode) {
		return (!name || name === 'off') ? '' : 'ic-' + name + '-' + mode;
	}

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

	var DEMO = byName('aperture');      // closed paths, so `solid` is real
	var MOVER = byName('activity');     // one open path, so `draw` reads clearly

	var OPTS = {
		variant: {
			values: ['thin', 'line', 'bold', 'solid', 'duo'],
			art: function (v) { return svgMarkup(DEMO, v, 20); }
		},
		psize: {
			values: ['sm', 'md', 'lg', 'xl'],
			// Drawn at the size it selects, capped so the rail stays a rail.
			art: function (v) { return svgMarkup(DEMO, 'line', { sm: 13, md: 16, lg: 20, xl: 26 }[v]); }
		},
		colormode: {
			values: ['mono', 'color'],
			label: { mono: 'Mono', color: 'Colour' },
			// The colour sample is drawn SOLID and tinted, because that is
			// exactly what the mode does to the grid — a stroked sample would
			// promise an outline and deliver a fill.
			art: function (v) {
				return v === 'color'
					? '<span class="is-tinted">' + svgMarkup(DEMO, 'solid', 20) + '</span>'
					: svgMarkup(DEMO, 'line', 20);
			}
		},
		motion: {
			values: MOTIONS,
			label: { off: 'None' },
			// Always previewed as a LOOP, whatever the play mode is set to: an
			// -in animation plays once and then the button sits there looking
			// broken. The mode buttons below say what the grid will do.
			art: function (v) {
				return svgMarkup(MOVER, 'line', 20, motionClass(v, 'loop'));
			}
		},
		mode: {
			values: MODES,
			art: function (v) {
				return '<svg class="ic ic-sm" aria-hidden="true"><use href="#i-' + MODEICON[v] + '"/></svg>';
			}
		}
	};

	// The panel repeats the two motion groups under their own attribute names,
	// so a click there cannot be mistaken for the sidebar's copy. Same config,
	// different data-attribute — aliased rather than duplicated.
	OPTS.pmotion = OPTS.motion;
	OPTS.pmode = OPTS.mode;

	// Groups that keep a written label beside the sample. The four sidebar
	// rails do not: they are icon-only rows, and the rail's heading names the
	// current choice instead — one word in one place beats five words repeated
	// under five buttons that are already showing you the answer.
	var LABELLED = { mode: 1, pmotion: 1, pmode: 1 };

	function optText(group, v) {
		var cfg = OPTS[group];
		return (cfg.label && cfg.label[v]) || v;
	}

	function optButton(group, v, pressed) {
		var text = optText(group, v);
		return '<button class="opt" type="button" data-' + group + '="' + v + '"'
			+ ' aria-pressed="' + pressed + '" title="' + text + '" aria-label="' + text + '">'
			+ '<span class="opt__art">' + OPTS[group].art(v) + '</span>'
			+ (LABELLED[group] ? '<span class="opt__label">' + text + '</span>' : '')
			+ '</button>';
	}

	// A group can appear more than once (the sidebar and the panel both show
	// motion), so this fills every holder that asks for it.
	function paintOpts(group, selected) {
		$$('[data-optgroup="' + group + '"]').forEach(function (holder) {
			holder.innerHTML = OPTS[group].values.map(function (v) {
				return optButton(group, v, String(v === selected));
			}).join('');
		});
		$$('[data-now="' + group + '"]').forEach(function (el) {
			el.textContent = optText(group, selected);
		});
	}

	paintOpts('variant', state.variant);
	paintOpts('psize', state.size);
	paintOpts('colormode', state.color);
	paintOpts('motion', state.motion);
	paintOpts('mode', state.mode);
	paintOpts('pmotion', panelMotion);
	paintOpts('pmode', panelMode);

	/* ── The grid ────────────────────────────────────────────────────────── */

	var sections = $('[data-sections]');

	function cellsFor(rows) {
		var mcls = motionClass(state.motion, state.mode);
		var colourful = state.color === 'color';
		return rows.map(function (i, n) {
			var v = state.variant;
			var canFill = i.variants.indexOf('solid') !== -1;
			// Colour mode means FILLED with colour, so it draws the solid form
			// wherever the geometry allows one. The icons that cannot be
			// filled — the open paths — keep their stroke and take the colour
			// on that instead, which is the only honest answer: a filled open
			// path is the blob this set refuses to ship.
			if (colourful && canFill) v = 'solid';
			// An icon with no solid falls back to line rather than vanishing —
			// a hole in the grid would read as a missing icon, not a missing
			// variant.
			if (v === 'solid' && !canFill) v = 'line';
			// A tiny per-cell delay so a grid of 61 icons arrives as a sweep
			// rather than as one flash. Capped, or the last cell waits a
			// second and a half to appear.
			var delay = state.motion === 'off' ? '' :
				' style="--ic-delay:' + Math.min(n * 18, 420) + 'ms"';
			return '<button class="cell" type="button" data-name="' + i.name + '" data-cat="' + i.category + '" title="' + i.name + '"' + delay + '>'
				+ svgMarkup(i, v, 24, mcls)
				+ '<span class="cell__name">' + i.name + '</span></button>';
		}).join('');
	}

	function render() {
		var q = state.q.toLowerCase();
		var rows = ICONS.filter(function (i) {
			return (!state.cat || i.category === state.cat)
				&& (!q || i.name.indexOf(q) !== -1 || i.category.indexOf(q) !== -1);
		});

		sections.dataset.size = state.size;
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
		$('[data-motion-note]').hidden = !(state.motion === 'draw' && state.variant === 'solid');
	}

	/* ── Filters ─────────────────────────────────────────────────────────── */

	$('[data-search]').addEventListener('input', function (e) {
		state.q = e.target.value.trim();
		render();
	});

	document.addEventListener('keydown', function (e) {
		if (e.key === '/' && !/^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName)) {
			e.preventDefault();
			$('[data-search]').focus();
		}
	});

	// One delegated listener for every generated control, rather than rebinding
	// after each repaint.
	document.addEventListener('click', function (e) {
		var b = e.target.closest('[data-variant],[data-psize],[data-colormode],[data-motion],[data-mode],[data-pmotion],[data-pmode]');
		if (!b) return;

		var group = ['variant', 'psize', 'colormode', 'motion', 'mode', 'pmotion', 'pmode']
			.filter(function (g) { return b.hasAttribute('data-' + g); })[0];
		var v = b.getAttribute('data-' + group);

		if (group === 'variant') state.variant = v;
		if (group === 'psize') state.size = v;
		if (group === 'colormode') state.color = v;
		if (group === 'motion') state.motion = v;
		if (group === 'mode') state.mode = v;
		if (group === 'pmotion') panelMotion = v;
		if (group === 'pmode') panelMode = v;

		paintOpts(group, v);
		if (group === 'pmotion' || group === 'pmode') paint(); else render();
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

	/* ── The panel ───────────────────────────────────────────────────────── */

	var panel = $('[data-panel]');

	function paint() {
		if (!current) return;
		var v = panelVariant;
		var has = current.variants.indexOf('solid') !== -1;
		$('[data-panel-note]').hidden = !(v === 'solid' && !has);
		if (v === 'solid' && !has) v = 'line';

		var holder = $('[data-panel-icon]').parentNode;
		holder.innerHTML = svgMarkup(current, v, 64, motionClass(panelMotion, panelMode))
			.replace('<svg ', '<svg data-panel-icon ');
		var ico = $('[data-panel-icon]');
		ico.classList.add('panel__icon');
		ico.style.color = panelColour === 'custom' ? customColour : COLOURS[panelColour];

		$('[data-size-out]').textContent = size + ' px';
		// Ink is the idiomatic form — the icon inherits its surroundings, so
		// the markup keeps currentColor and the reader can paste it anywhere.
		// Any OTHER choice is a deliberate colour, so it is baked in and the
		// snippet matches the file the download button writes.
		$('[data-panel-code]').textContent = panelColour === 'ink'
			? svgMarkup(current, v, size)
			: svgMarkup(current, v, size).replace(/currentColor/g, exportColour());
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
		var v = panelVariant;
		if (v === 'solid' && current.variants.indexOf('solid') === -1) v = 'line';
		// currentColor cannot survive leaving the page — there is no
		// surrounding text in a downloaded file to inherit from — so it is
		// always resolved, even when the picker is on ink.
		return svgMarkup(current, v, size).replace(/currentColor/g, exportColour());
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
}());
