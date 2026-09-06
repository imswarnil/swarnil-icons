/* =============================================================================
   icons.imswarnil.com — the browser and the export tool

   Rasterising happens HERE rather than in the build, and that is the important
   decision. A build that pre-renders PNGs has to guess which sizes anyone
   wants, ships thousands of files, and still cannot answer "give me this one
   at 137px". Drawing to a canvas on demand answers every size, in every
   format, from the SVG that is already on the page — and adds no dependency.
   ========================================================================== */
(function () {
	'use strict';

	var $ = function (s, r) { return (r || document).querySelector(s); };
	var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

	var ICONS = JSON.parse($('#icon-data').textContent);
	var STROKE = { thin: 1, line: 1.5, bold: 2, solid: 1.5, duo: 1.5 };

	// Categories are a flat field on each icon (the folder they live in).
	// Grouping two or more of them under one nav label is a display concern
	// only, kept here rather than in the data so adding a new flat category
	// never requires touching the build. Anything not listed here renders as
	// its own top-level item — empty for now, no categories need grouping.
	var GROUPS = [];
	var LABELS = { ui: 'UI' };
	var grouped = {};
	GROUPS.forEach(function (g) { g.categories.forEach(function (c) { grouped[c] = g; }); });

	function label(cat) {
		return LABELS[cat] || (cat.charAt(0).toUpperCase() + cat.slice(1));
	}

	var state = { q: '', cat: '', variant: 'line', size: 'md', color: 'mono' };
	var current = null, size = 24, panelVariant = 'line';

	/* ── Theme ───────────────────────────────────────────────────────────── */

	function themeLabel() {
		var el = $('[data-theme-label]');
		if (el) el.textContent = document.documentElement.dataset.theme === 'dark' ? 'Dark' : 'Light';
	}
	themeLabel();

	$('[data-theme-toggle]').addEventListener('click', function () {
		var next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
		document.documentElement.dataset.theme = next;
		try { localStorage.setItem('si-theme', next); } catch (e) {}
		themeLabel();
	});

	/* ── Building one icon's SVG ─────────────────────────────────────────── */

	function svgMarkup(icon, variant, px) {
		var solid = variant === 'solid';
		var body = icon.body;
		if (solid) {
			body = body.replace(/<path /g, '<path fill="currentColor" stroke="none" ')
			           .replace(/<circle (?![^>]*fill=)/g, '<circle fill="currentColor" stroke="none" ');
		}
		var op = variant === 'duo' ? ' opacity="0.45"' : '';
		return '<svg xmlns="http://www.w3.org/2000/svg" width="' + px + '" height="' + px + '"'
			+ ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="' + STROKE[variant] + '"'
			+ ' stroke-linecap="round" stroke-linejoin="round"' + op + '>' + body + '</svg>';
	}

	/* ── The sidebar ─────────────────────────────────────────────────────── */

	// Display order: ungrouped categories A→Z, then each group in GROUPS
	// order with its children A→Z. Counts come from the data, not hand-kept.
	var cats = {};
	ICONS.forEach(function (i) { cats[i.category] = (cats[i.category] || 0) + 1; });

	var ungrouped = Object.keys(cats).filter(function (c) { return !grouped[c]; }).sort();

	function navItem(cat, child) {
		return '<button class="nav__item' + (child ? ' nav__item--child' : '') + '" type="button"'
			+ ' data-cat="' + cat + '" aria-pressed="false">'
			+ '<span>' + label(cat) + '</span><span class="nav__count">' + cats[cat] + '</span></button>';
	}

	var nav = '<div class="nav__section">'
		+ '<button class="nav__item" type="button" data-cat="" aria-pressed="true">'
		+ '<span>All</span><span class="nav__count">' + ICONS.length + '</span></button>'
		+ '</div><div class="nav__section">' + ungrouped.map(function (c) { return navItem(c, false); }).join('') + '</div>';

	GROUPS.forEach(function (g) {
		var present = g.categories.filter(function (c) { return cats[c]; });
		if (!present.length) return;
		nav += '<div class="nav__section">'
			+ '<p class="nav__group">' + g.label + '</p>'
			+ present.map(function (c) { return navItem(c, true); }).join('')
			+ '</div>';
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

	/* ── The grid ────────────────────────────────────────────────────────── */

	var sections = $('[data-sections]');

	function cellsFor(rows) {
		return rows.map(function (i) {
			var v = state.variant;
			// An icon with no solid falls back to line rather than vanishing —
			// a hole in the grid would read as a missing icon, not a missing
			// variant.
			if (v === 'solid' && i.variants.indexOf('solid') === -1) v = 'line';
			return '<button class="cell" type="button" data-name="' + i.name + '" data-cat="' + i.category + '" title="' + i.name + '">'
				+ svgMarkup(i, v, 24)
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
					+ '<h2 class="section__title">' + label(cat) + ' <span class="section__count">' + inCat.length + '</span></h2>'
					+ '<div class="grid">' + cellsFor(inCat) + '</div></section>';
			}).join('');
		}

		$('[data-count]').textContent = rows.length + (rows.length === 1 ? ' icon' : ' icons');
		$('[data-empty]').hidden = rows.length > 0;
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

	function group(attr, onPick) {
		$$('[' + attr + ']').forEach(function (b) {
			b.addEventListener('click', function () {
				$$('[' + attr + ']').forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
				b.setAttribute('aria-pressed', 'true');
				onPick(b.getAttribute(attr));
			});
		});
	}

	group('data-variant', function (v) { state.variant = v; render(); });
	group('data-psize', function (v) { state.size = v; render(); });
	group('data-colormode', function (v) { state.color = v; render(); });

	/* ── The panel ───────────────────────────────────────────────────────── */

	var panel = $('[data-panel]');

	function paint() {
		if (!current) return;
		var v = panelVariant;
		var has = current.variants.indexOf('solid') !== -1;
		$('[data-panel-note]').hidden = !(v === 'solid' && !has);
		if (v === 'solid' && !has) v = 'line';

		var holder = $('[data-panel-icon]').parentNode;
		holder.innerHTML = svgMarkup(current, v, 64).replace('<svg ', '<svg class="panel__icon" data-panel-icon ');

		$('[data-size-out]').textContent = size + ' px';
		$('[data-panel-code]').textContent = svgMarkup(current, v, size);
	}

	function open(name) {
		current = ICONS.filter(function (i) { return i.name === name; })[0];
		if (!current) return;
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

	$('[data-size]').addEventListener('input', function (e) {
		size = parseInt(e.target.value, 10);
		paint();
	});

	/* ── Export ──────────────────────────────────────────────────────────── */

	function inkColour() {
		return getComputedStyle(document.body).color;
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
		// currentColor cannot survive leaving the page, so it is resolved to the
		// ink the viewer is actually looking at.
		return svgMarkup(current, v, size).replace(/currentColor/g, inkColour());
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
				save(b, current.name + '-' + panelVariant + '-' + size + (type === 'image/jpeg' ? '.jpg' : '.png'));
			}, type, 0.92);
		};
		img.src = url;
	}

	$$('[data-dl]').forEach(function (b) {
		b.addEventListener('click', function () {
			var kind = b.dataset.dl;
			if (kind === 'svg') {
				save(new Blob([currentSvg()], { type: 'image/svg+xml' }),
					current.name + '-' + panelVariant + '-' + size + '.svg');
			} else {
				raster(kind === 'jpg' ? 'image/jpeg' : 'image/png');
			}
		});
	});

	function flash(btn, word) {
		var was = btn.textContent;
		btn.textContent = word;
		setTimeout(function () { btn.textContent = was; }, 1200);
	}

	$('[data-copy-svg]').addEventListener('click', function () {
		var b = this;
		navigator.clipboard.writeText($('[data-panel-code]').textContent).then(function () { flash(b, 'Copied'); });
	});

	$('[data-copy-use]').addEventListener('click', function () {
		var b = this;
		var use = '<svg class="ic ic-lg"><use href="/sprite.svg#i-' + current.name + '"/></svg>';
		navigator.clipboard.writeText(use).then(function () { flash(b, 'Copied'); });
	});

	render();
}());
