/* =============================================================================
   icons.imswarnil.com/usage

   Two jobs only: the theme toggle, and revealing the step row when it scrolls
   into view. Everything else on the page is CSS classes the package already
   ships — if this file were doing the animating, the demo would be proving
   something about this file rather than about the icon set.
   ========================================================================== */
(function () {
	'use strict';

	var $ = function (s, r) { return (r || document).querySelector(s); };
	var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

	/* ── Theme ───────────────────────────────────────────────────────────────
	   Same key as the browser page, so the choice carries across the two. */

	function themeIcon() {
		var dark = document.documentElement.dataset.theme === 'dark';
		var use = $('[data-theme-icon]');
		// The theme you would GET by clicking, not the one you are in.
		if (use) use.setAttribute('href', dark ? '#i-aperture' : '#i-moon');
		var btn = $('[data-theme-toggle]');
		if (btn) btn.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
	}
	themeIcon();

	var toggle = $('[data-theme-toggle]');
	if (toggle) {
		toggle.addEventListener('click', function () {
			var next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
			document.documentElement.dataset.theme = next;
			try { localStorage.setItem('si-theme', next); } catch (e) {}
			themeIcon();
		});
	}

	/* ── Reveal on scroll ────────────────────────────────────────────────────
	   The draw class is added when the row arrives and REMOVED when it leaves,
	   so scrolling past and back replays it. A one-shot reveal is the right
	   default in a product; on a page whose whole point is showing you the
	   animation, being able to see it twice matters more.

	   Reduced motion is honoured here as well as in the stylesheet: with the
	   class never added, the strokes are simply drawn, rather than added and
	   then neutralised by !important. */

	var reveal = $$('[data-reveal]');
	if (!reveal.length) return;

	var still = matchMedia('(prefers-reduced-motion: reduce)');

	function show(row) {
		row.classList.add('is-in');
		$$('[data-draw]', row).forEach(function (el) { el.classList.add('ic-draw-in'); });
	}

	function hide(row) {
		row.classList.remove('is-in');
		$$('[data-draw]', row).forEach(function (el) { el.classList.remove('ic-draw-in'); });
	}

	if (still.matches || !('IntersectionObserver' in window)) {
		reveal.forEach(show);
		return;
	}

	var io = new IntersectionObserver(function (entries) {
		entries.forEach(function (e) {
			if (e.isIntersecting) show(e.target); else hide(e.target);
		});
	}, { rootMargin: '0px 0px -15% 0px', threshold: 0.25 });

	reveal.forEach(function (row) { io.observe(row); });
}());
