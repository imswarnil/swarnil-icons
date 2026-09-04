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

	var state = { q: '', cat: '', variant: 'line' };
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

	/* ── The grid ────────────────────────────────────────────────────────── */

	var grid = $('[data-grid]');

	function render() {
		var q = state.q.toLowerCase();
		var rows = ICONS.filter(function (i) {
			return (!state.cat || i.category === state.cat)
				&& (!q || i.name.indexOf(q) !== -1 || i.category.indexOf(q) !== -1);
		});

		grid.innerHTML = rows.map(function (i) {
			var v = state.variant;
			// An icon with no solid falls back to line rather than vanishing —
			// a hole in the grid would read as a missing icon, not a missing
			// variant.
			if (v === 'solid' && i.variants.indexOf('solid') === -1) v = 'line';
			return '<button class="cell" type="button" data-name="' + i.name + '" title="' + i.name + '">'
				+ svgMarkup(i, v, 24)
				+ '<span class="cell__name">' + i.name + '</span></button>';
		}).join('');

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

	group('data-cat', function (v) { state.cat = v; render(); });
	group('data-variant', function (v) { state.variant = v; render(); });

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

	grid.addEventListener('click', function (e) {
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
