/* =============================================================================
   icons.imswarnil.com/usage

   One job: revealing the step row when it scrolls into view. The theme toggle
   and the bar's search live in site.js, which every page loads.

   Everything else on this page is CSS classes the package already ships — if
   this file were doing the animating, the demo would be proving something
   about this file rather than about the icon set.
   ========================================================================== */
(function () {
	'use strict';

	var $ = function (s, r) { return (r || document).querySelector(s); };
	var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

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
