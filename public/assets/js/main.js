/* SGA creatives: progressive enhancement only. Everything works without this file. */
(function () {
  'use strict';
  window.sgaReady = true;

  var root = document.documentElement;
  root.classList.add('js');

  /* ---------------------------------------------------------- mobile menu */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  var mq = window.matchMedia('(max-width: 899px)');

  function focusables() {
    return [toggle].concat(Array.prototype.slice.call(nav.querySelectorAll('a[href]')));
  }

  function setOpen(open, returnFocus) {
    toggle.setAttribute('aria-expanded', String(open));
    var label = toggle.querySelector('.nav-toggle-label');
    label.textContent = open ? label.getAttribute('data-label-open') : label.getAttribute('data-label-closed');
    nav.classList.toggle('is-open', open);
    root.classList.toggle('menu-open', open);
    if (open) {
      var first = nav.querySelector('a[href]');
      if (first) first.focus();
    } else if (returnFocus) {
      toggle.focus();
    }
  }

  if (toggle && nav) {
    toggle.hidden = false;

    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true', true);
    });

    nav.addEventListener('click', function (event) {
      if (event.target.closest('a') && nav.classList.contains('is-open')) setOpen(false, false);
    });

    document.addEventListener('keydown', function (event) {
      if (!nav.classList.contains('is-open')) return;
      if (event.key === 'Escape') {
        event.preventDefault();
        setOpen(false, true);
        return;
      }
      if (event.key === 'Tab') {
        var items = focusables();
        var first = items[0];
        var last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    });

    var onChange = function (e) { if (!e.matches && nav.classList.contains('is-open')) setOpen(false, false); };
    if (mq.addEventListener) mq.addEventListener('change', onChange); else mq.addListener(onChange);
  }

  /* ---------------------------------------------------------- the logo always leads to the top of the home page */
  // A link to the page you are already on does not reliably scroll back up (some browsers keep the
  // position, and the swipe feed can snap back). On the home page the logo scrolls to the top itself;
  // elsewhere it loads the home page, which always opens at the top.
  Array.prototype.forEach.call(document.querySelectorAll('[data-home]'), function (link) {
    link.addEventListener('click', function (event) {
      if (location.pathname !== '/' || event.metaKey || event.ctrlKey || event.shiftKey) return;
      event.preventDefault();
      if (nav && nav.classList.contains('is-open')) setOpen(false, false);
      var calmNow = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      window.scrollTo({ top: 0, behavior: calmNow ? 'auto' : 'smooth' });
      if (location.hash) history.replaceState(null, '', '/');
    });
  });

  /* ---------------------------------------------------------- header border */
  var header = document.querySelector('[data-header]');
  if (header) {
    var ticking = false;
    var update = function () {
      header.classList.toggle('is-scrolled', window.scrollY > 8);
      ticking = false;
    };
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  /* ---------------------------------------------------------- reveal on scroll */
  var reveals = Array.prototype.slice.call(document.querySelectorAll('[data-reveal]'));
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-in'); });
  }
  // Anything targeted by an in-page link should be visible at once.
  window.addEventListener('hashchange', function () {
    reveals.forEach(function (el) {
      if (el.getBoundingClientRect().top < window.innerHeight * 1.5) el.classList.add('is-in');
    });
  });

  /* ---------------------------------------------------------- scroll-driven effects (one loop for all) */
  // [data-scroll=fill]    --f 0..1 as a process word travels from the bottom of the screen to above the middle
  // [data-scroll=parallax] --rv 0..1 reveal on the way in, --py -1..1 drift across the whole passage
  // Only elements near the viewport are measured (IntersectionObserver). Each frame reads every
  // position first and writes afterwards, and skips unchanged values, so the phone never has to
  // recalculate layout in between.
  var calm = window.matchMedia('(prefers-reduced-motion: reduce)');
  var effects = Array.prototype.slice.call(document.querySelectorAll('[data-scroll]'));
  if (effects.length && !calm.matches) {
    var active = new Set();
    var last = new Map();
    var queued = false;
    var clamp01 = function (v) { return Math.min(1, Math.max(0, v)); };
    var easeOut = function (v) { return 1 - Math.pow(1 - v, 3); };
    var set = function (el, name, value) {
      var memo = last.get(el) || {};
      if (memo[name] === value) return;
      memo[name] = value; last.set(el, memo);
      el.style.setProperty(name, value);
    };
    var frame = function () {
      queued = false;
      var vh = window.innerHeight;
      var reads = [];
      active.forEach(function (el) { reads.push([el, el.getBoundingClientRect()]); });
      reads.forEach(function (pair) {
        var el = pair[0], r = pair[1];
        if (el.getAttribute('data-scroll') === 'fill') {
          set(el, '--f', clamp01((vh * 0.92 - r.top) / (vh * 0.5)).toFixed(3));
        } else {
          var t = clamp01((vh - r.top) / (vh + r.height));
          set(el, '--rv', easeOut(clamp01(t / 0.32)).toFixed(3));
          set(el, '--py', (t * 2 - 1).toFixed(3));
        }
      });
    };
    var request = function () { if (!queued) { queued = true; window.requestAnimationFrame(frame); } };
    if ('IntersectionObserver' in window) {
      var watch = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) active.add(entry.target); else active.delete(entry.target);
        });
        request();
      }, { rootMargin: '30% 0px 30% 0px' });
      effects.forEach(function (el) { watch.observe(el); });
    } else {
      effects.forEach(function (el) { active.add(el); });
    }
    window.addEventListener('scroll', request, { passive: true });
    window.addEventListener('resize', request);
    request();
  }

  /* ---------------------------------------------------------- phones: the home page as a swipe feed */
  // On the home page, phones and tablets snap one screen at a time: the hero, each project, the
  // statement and the footer (html.is-feed, see main.css). Snapping stays on for the whole page:
  // turning it on and off while scrolling made the browser jump back to the last stop.
  // Swipe intent: plain snapping goes to the nearest stop, so a short swipe snapped back and had to
  // be repeated, which felt like the page correcting itself. A clear swipe always moves exactly one
  // stop in its direction, in one gliding movement.
  var feedHome = document.querySelector('.page-home .show-list');
  if (feedHome) {
    root.classList.add('is-feed');
    var stops = Array.prototype.slice.call(document.querySelectorAll('.page-home .hero, .show-item, .page-home .statement'));
    var phone = window.matchMedia('(max-width: 899px)');
    var start = null;
    var stopTops = function () {
      var pad = parseFloat(getComputedStyle(root).scrollPaddingTop) || 0;
      var max = root.scrollHeight - window.innerHeight;
      var tops = stops.map(function (el, i) {
        var top = i === 0 ? 0 : el.getBoundingClientRect().top + window.scrollY - pad;
        return Math.min(Math.max(0, Math.round(top)), max);
      });
      tops.push(max);   // the footer, at the very end
      return tops.filter(function (top, i) { return i === 0 || top - tops[i - 1] > 4; });
    };
    window.addEventListener('touchstart', function (event) {
      start = (phone.matches && event.touches.length === 1)
        ? { x: event.touches[0].clientX, y: event.touches[0].clientY, scroll: window.scrollY, t: Date.now() } : null;
    }, { passive: true });
    window.addEventListener('touchend', function (event) {
      if (!start || !event.changedTouches.length) return;
      var dy = start.y - event.changedTouches[0].clientY;   // finger up = scroll down
      var dx = start.x - event.changedTouches[0].clientX;
      var quick = Date.now() - start.t < 400;
      if (Math.abs(dy) < Math.abs(dx) || Math.abs(dy) < (quick ? 24 : 60)) { start = null; return; }
      var tops = stopTops();
      var from = 0;   // the stop the swipe started on
      tops.forEach(function (top, i) { if (Math.abs(top - start.scroll) < Math.abs(tops[from] - start.scroll)) from = i; });
      var to = Math.min(Math.max(from + (dy > 0 ? 1 : -1), 0), tops.length - 1);
      start = null;
      if (to === from) return;
      window.scrollTo({ top: tops[to], behavior: calm.matches ? 'auto' : 'smooth' });
    }, { passive: true });
  }

  /* ---------------------------------------------------------- "Get in touch": close on Escape or click outside */
  Array.prototype.forEach.call(document.querySelectorAll('details.reach'), function (reach) {
    document.addEventListener('click', function (event) {
      if (reach.open && !reach.contains(event.target)) reach.open = false;
    });
    reach.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && reach.open) {
        reach.open = false;
        reach.querySelector('summary').focus();
      }
    });
  });

  /* ---------------------------------------------------------- year */
  Array.prototype.forEach.call(document.querySelectorAll('[data-year]'), function (el) {
    el.textContent = String(new Date().getFullYear());
  });
})();
