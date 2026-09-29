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

  /* ---------------------------------------------------------- year */
  Array.prototype.forEach.call(document.querySelectorAll('[data-year]'), function (el) {
    el.textContent = String(new Date().getFullYear());
  });
})();
