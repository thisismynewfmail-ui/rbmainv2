/* The seasonal site skin (static/css/season.css, app/models/season.py).

   The server decides whether a skin is on, by the calendar, on every render;
   this file only makes the decoration behave:

   * the event chip's countdown, one tick a minute, and the skin coming off
     by itself when the event ends in a tab that stayed open;
   * the header's moon and floating ghosts, placed only in gaps the topbar's
     own controls leave free (measured, never guessed), so nothing ever sits
     behind a link or the search box;
   * ghosts that watch the mouse and shy away from it (desktop), say boo when
     tapped (everywhere), a ghost in the footer graveyard that rises when you
     scroll down to it, and a spider in the desktop gutter that lowers itself
     as you scroll;
   * a critter mute, kept in localStorage on this device only.

   Everything here is decoration: it reads no network, writes no cookie, never
   calls preventDefault and never touches the store's markup.  A failure
   leaves the static CSS skin in place and nothing else. */
(function () {
  'use strict';
  var root = document.documentElement;
  if (!window.BH || !BH.season || !root.hasAttribute('data-season')) return;

  var S = BH.season;
  var FX_KEY = 'blockhaven.season.fx';
  var DAY = 86400;
  var HOUR = 3600;
  var CRITTERS = { halloween: 'Halloween critters' };
  var BUBBLE_MS = 1400;
  var TRICK_MS = 4000;
  var MAX_BURSTS = 9;
  var MAX_RISES = 4;

  var skew = (Number(S.now) || 0) * 1000 - Date.now();
  var active = true;
  var interval = 0;
  var cleanups = [];
  var observers = [];
  var timers = [];
  var daysLeft = Number(S.days_left) || 0;

  var Season = window.Season = {
    active: true, check: tick, off: teardown, boo: booRandom, setFx: setFx,
    frames: 0
  };

  // ------------------------------------------------------------- helpers
  function each(sel, fn, scope) {
    Array.prototype.forEach.call((scope || document).querySelectorAll(sel), fn);
  }
  function make(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text) node.textContent = text;
    return node;
  }
  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
  function later(fn, ms) {
    var id = setTimeout(function () {
      timers = timers.filter(function (t) { return t !== id; });
      safe(fn)();
    }, ms);
    timers.push(id);
    return id;
  }
  function cancel(id) { if (id) clearTimeout(id); }
  function safe(fn) {
    return function () {
      try { return fn.apply(this, arguments); } catch (e) { /* decoration only */ }
    };
  }
  function listen(target, type, fn, opts) {
    var h = safe(fn);
    target.addEventListener(type, h, opts);
    cleanups.push(function () { target.removeEventListener(type, h, opts); });
    return h;
  }
  function media(q) {
    return window.matchMedia ? window.matchMedia(q) : { matches: false };
  }
  function onMedia(m, fn) {
    var h = safe(fn);
    if (m.addEventListener) m.addEventListener('change', h);
    else if (m.addListener) m.addListener(h);
    else return;
    cleanups.push(function () {
      if (m.removeEventListener) m.removeEventListener('change', h);
      else if (m.removeListener) m.removeListener(h);
    });
  }
  function watch(obs) { observers.push(obs); return obs; }
  function shown(node) {
    if (!node) return false;
    var r = node.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }

  var reduceQ = media('(prefers-reduced-motion: reduce)');
  var fineQ = media('(hover: hover) and (pointer: fine)');
  var wideQ = media('(min-width: 1180px)');
  var darkQ = media('(prefers-color-scheme: dark)');
  function reduced() { return !!reduceQ.matches; }
  function fxOn() { return root.getAttribute('data-season-fx') !== 'off'; }
  function lite() { return root.hasAttribute('data-season-lite'); }
  function phone() { return window.innerWidth <= 860; }
  function isDark() {
    if (window.Site && Site.isDark) return Site.isDark();
    var t = root.getAttribute('data-theme');
    return t === 'dark' || (t !== 'light' && !!darkQ.matches);
  }

  // --------------------------------------------------------------- clock
  /* Mirrors season.left_labels() in app/models/season.py exactly. */
  function leftLabels(left, forced) {
    if (forced) return ['PREVIEW', 'PREVIEW', 'PREVIEW'];
    left = Math.max(0, Math.floor(left));
    var d, h, m, text;
    if (left > 3 * DAY) {
      d = Math.floor(left / DAY); h = Math.floor((left % DAY) / HOUR);
      text = d + 'd ' + h + 'h';
      return [text, text, d + 'd'];
    }
    if (left > DAY) {
      d = Math.floor(left / DAY); h = Math.floor((left % DAY) / HOUR);
      text = d + 'd ' + h + 'h';
      return ['LAST 3 DAYS · ' + text, text, d + 'd'];
    }
    h = Math.floor(left / HOUR); m = Math.floor((left % HOUR) / 60);
    text = h + 'h ' + m + 'm';
    return ['ENDS IN ' + text, text, h ? h + 'h' : m + 'm'];
  }
  Season.leftLabels = leftLabels;

  function serverNow() { return Math.floor((Date.now() + skew) / 1000); }

  function tick(nowSec) {
    if (!active) return;
    var now = (typeof nowSec === 'number' && isFinite(nowSec)) ? Math.floor(nowSec) : serverNow();
    var forced = !!S.forced || !S.ends;
    if (!forced && now >= S.ends) { teardown(); return; }
    var left = forced ? 0 : S.ends - now;
    var labels = leftLabels(left, forced);
    each('[data-sn-left]', function (node) {
      var kind = node.getAttribute('data-sn-left');
      var text = kind === 'long' ? labels[0] : (kind === 'compact' ? labels[1] : labels[2]);
      if (node.textContent !== text) node.textContent = text;
    });
    each('.sn-chip', function (chip) {
      chip.classList.toggle('sn-hurry', !forced && left <= 3 * DAY);
      chip.classList.toggle('sn-final', !forced && left <= DAY);
    });
    daysLeft = forced ? -1 : Math.floor(left / DAY);
  }

  // ------------------------------------------------------------ teardown
  function teardown() {
    if (!active) return;
    active = false;
    Season.active = false;
    clearInterval(interval);
    timers.forEach(clearTimeout);
    timers = [];
    cleanups.forEach(function (fn) { try { fn(); } catch (e) {} });
    cleanups = [];
    observers.forEach(function (o) { try { o.disconnect(); } catch (e) {} });
    observers = [];
    unbindPointer();
    unbindScroll();
    ['data-season', 'data-season-lite', 'data-season-calm', 'data-season-fx'].forEach(function (a) {
      root.removeAttribute(a);
    });
    root.classList.remove('sn-hold');
    each('.hw-sky, .hw-yard, .hw-fx, .sn-chip, .sn-navtag, .sn-drawer-row, .sn-settings-row',
      function (node) { if (node.parentNode) node.parentNode.removeChild(node); });
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      meta.setAttribute('data-light', '#14548e');
      meta.setAttribute('data-dark', '#0a2b48');
      meta.setAttribute('content', isDark() ? '#0a2b48' : '#14548e');
    }
  }

  function applyMeta() {
    var meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) return;
    var dark = isDark();
    meta.setAttribute('content', meta.getAttribute(dark ? 'data-dark' : 'data-light') ||
                      meta.getAttribute('content'));
  }

  // --------------------------------------------------------------- nodes
  var bar = document.querySelector('.topbar');
  var row = document.querySelector('.topbar > .wrap');
  var sky = document.querySelector('.topbar > .hw-sky');
  var yard = document.querySelector('.hw-yard');
  var riser = yard && yard.querySelector('.hw-riser');
  var fx = document.querySelector('.hw-fx');
  var spider = fx && fx.querySelector('.hw-spider');
  var drifter = fx && fx.querySelector('.hw-drifter');
  var peeker = sky && sky.querySelector('.hw-peeker');
  var skyVisible = true;
  var yardVisible = false;

  /* A floater (or the moon) and where placeSlots() put it: x/y inside the
     sky, its size, and the free box it may wander in when spooked. */
  var slots = sky ? Array.prototype.map.call(sky.querySelectorAll('[data-hw-slot]'), function (node) {
    return { el: node, moon: node.getAttribute('data-hw-slot') === 'moon',
             flee: node.querySelector('.hw-flee'), placed: false,
             x: 0, y: 0, w: 0, h: 0, box: null, fx: 0, fy: 0, spooked: false };
  }) : [];
  function floaters() { return slots.filter(function (s) { return !s.moon; }); }

  // ------------------------------------------------------- slot packing
  /* The topbar's free horizontal gaps: between each pair of visible controls
     (8px kept clear on both sides), plus the side gutters on a wide screen.
     The moon goes first, then each floater, into the widest gap with room;
     whatever does not fit stays hidden. */
  function placeSlots() {
    if (!active || !sky || !row || lite()) return;
    var sr = sky.getBoundingClientRect();
    if (!sr.width || !sr.height) return;
    var W = sr.width;
    var H = sr.height;
    var small = phone();
    var M = 8;
    var kids = [];
    for (var c = row.firstElementChild; c; c = c.nextElementSibling) {
      var r = c.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) kids.push({ l: r.left - sr.left, r: r.right - sr.left });
    }
    kids.sort(function (a, b) { return a.l - b.l; });
    var gaps = [];
    for (var i = 0; i + 1 < kids.length; i++) {
      var a = Math.max(kids[i].r, i ? kids[i - 1].r : 0) + M;
      var b = kids[i + 1].l - M;
      if (b > a) gaps.push({ a: a, b: b });
    }
    if (window.innerWidth >= 1180) {
      var gutter = (W - 1024) / 2;
      if (gutter - M > 0) {
        gaps.push({ a: M, b: gutter });
        gaps.push({ a: W - gutter, b: W - M });
      }
    }
    gaps.sort(function (x, y) { return (y.b - y.a) - (x.b - x.a); });
    gaps.forEach(function (g) { g.cur = g.a; g.items = []; });
    var needMoon = small ? 36 : 52;
    var needGhost = small ? 30 : 38;
    slots.forEach(function (s) {
      s.placed = false;
      if (getComputedStyle(s.el).display === 'none') return;
      var need = s.moon ? needMoon : needGhost;
      for (var k = 0; k < gaps.length; k++) {
        if (gaps[k].b - gaps[k].cur >= need) {
          gaps[k].items.push({ s: s, need: need });
          gaps[k].cur += need;
          s.placed = true;
          return;
        }
      }
    });
    gaps.forEach(function (g) {
      if (!g.items.length) return;
      // the group sits in the middle of its gap rather than against one side
      var x = g.a + ((g.b - g.a) - (g.cur - g.a)) / 2;
      g.items.forEach(function (it) {
        var s = it.s;
        s.w = s.el.offsetWidth;
        s.h = s.el.offsetHeight;
        s.x = Math.round(x + (it.need - s.w) / 2);
        var y = s.moon ? (small ? 5 : 8) : Math.round((H - s.h) / 2);
        s.y = clamp(y, 0, Math.max(0, H - s.h));
        s.box = { x0: g.a, x1: g.b, h: H };
        x += it.need;
      });
    });
    slots.forEach(function (s) {
      if (s.placed) {
        s.el.style.setProperty('--x', s.x + 'px');
        s.el.style.setProperty('--y', s.y + 'px');
        s.el.classList.add('hw-placed');
      } else {
        s.el.classList.remove('hw-placed');
        s.el.classList.remove('hw-spooked');
        if (s.flee) { s.flee.style.removeProperty('--fx'); s.flee.style.removeProperty('--fy'); }
        s.fx = s.fy = 0;
      }
    });
  }

  var placeQueued = false;
  function queuePlace() {
    if (placeQueued || !active) return;
    placeQueued = true;
    requestAnimationFrame(function () { placeQueued = false; safe(placeSlots)(); });
  }
  var resizeTimer = 0;
  function onResize() {
    cancel(resizeTimer);
    resizeTimer = later(queuePlace, 150);
  }

  // -------------------------------------------------------------- eyes
  function look(node, dx, dy) {
    var d = Math.sqrt(dx * dx + dy * dy) || 1;
    var px = Math.round(dx / d * 16) / 10;
    var py = Math.round(dy / d * 16) / 10;
    if (node.__hwPx !== px) { node.style.setProperty('--px', px); node.__hwPx = px; }
    if (node.__hwPy !== py) { node.style.setProperty('--py', py); node.__hwPy = py; }
  }
  function unlook(node) {
    if (!node) return;
    node.style.removeProperty('--px');
    node.style.removeProperty('--py');
    node.__hwPx = node.__hwPy = undefined;
  }
  function setFlee(target, state, fxv, fyv) {
    fxv = Math.round(fxv); fyv = Math.round(fyv);
    if (state.fx !== fxv) { target.style.setProperty('--fx', fxv + 'px'); state.fx = fxv; }
    if (state.fy !== fyv) { target.style.setProperty('--fy', fyv + 'px'); state.fy = fyv; }
  }

  // ------------------------------------------------- pointer (desktop)
  var pointer = { x: -9999, y: -9999 };
  var pointerBound = false;
  var frameQueued = false;
  var duckTimer = 0;
  var drifterState = { fx: 0, fy: 0 };

  function wantPointer() {
    return active && !lite() && !reduced() && fxOn() && !!fineQ.matches;
  }
  function onPointerMove(e) {
    if (e.pointerType && e.pointerType !== 'mouse' && e.pointerType !== 'pen') return;
    pointer.x = e.clientX;
    pointer.y = e.clientY;
    if (!frameQueued) {
      frameQueued = true;
      requestAnimationFrame(safeFrame);
    }
  }
  var safeMove = safe(onPointerMove);
  var safeFrame = safe(frame);
  function bindPointer() {
    if (pointerBound) return;
    document.addEventListener('pointermove', safeMove, { passive: true });
    pointerBound = true;
  }
  function unbindPointer() {
    if (!pointerBound) return;
    document.removeEventListener('pointermove', safeMove, { passive: true });
    pointerBound = false;
    frameQueued = false;
    slots.forEach(function (s) {
      unlook(s.el);
      if (s.flee) setFlee(s.flee, s, 0, 0);
      s.el.classList.remove('hw-spooked');
    });
    if (peeker) { unlook(peeker); peeker.classList.remove('hw-duck'); }
    unlook(riser);
    if (drifter) {
      unlook(drifter);
      var df = drifter.querySelector('.hw-flee');
      if (df) setFlee(df, drifterState, 0, 0);
    }
  }
  function syncPointer() {
    if (wantPointer()) bindPointer(); else unbindPointer();
  }

  /* One pass a frame at most: every rect is read first, then the writes. */
  function frame() {
    frameQueued = false;
    if (!pointerBound || !active) return;
    Season.frames++;
    var px = pointer.x;
    var py = pointer.y;
    var sr = skyVisible && sky ? sky.getBoundingClientRect() : null;
    var pr = sr && peeker && fxOn() ? peeker.getBoundingClientRect() : null;
    var rr = yardVisible && riser ? riser.getBoundingClientRect() : null;
    var fxShown = scrollBound && drifter;
    var dr = fxShown ? drifter.getBoundingClientRect() : null;

    if (sr) {
      var inBar = py >= sr.top && py < sr.bottom && px >= sr.left && px < sr.right;
      slots.forEach(function (s) {
        if (s.moon || !s.placed || !s.flee) return;
        var cx = sr.left + s.x + s.w / 2;
        var cy = sr.top + s.y + s.h / 2;
        look(s.el, px - cx, py - cy);
        var dx = cx - px;
        var dy = cy - py;
        var d = Math.sqrt(dx * dx + dy * dy) || 1;
        var fxv = 0;
        var fyv = 0;
        var near = d < 90;
        if (near) {
          var push = 34 * (1 - d / 90) + 8;
          fxv = dx / d * push;
          fyv = dy / d * push;
        }
        fxv = clamp(fxv, s.box.x0 - s.x, s.box.x1 - s.x - s.w);
        fyv = clamp(fyv, Math.max(-8, -s.y), Math.min(8, s.box.h - s.y - s.h));
        setFlee(s.flee, s, fxv, fyv);
        if (near !== s.spooked) { s.el.classList.toggle('hw-spooked', near); s.spooked = near; }
      });
      if (pr && pr.width) {
        var pcx = pr.left + pr.width / 2;
        look(peeker, px - pcx, py - (pr.top + pr.height / 3));
        if (inBar && Math.abs(px - pcx) < 60) {
          cancel(duckTimer); duckTimer = 0;
          peeker.classList.add('hw-duck');
        } else if (peeker.classList.contains('hw-duck') && !duckTimer) {
          duckTimer = later(function () { duckTimer = 0; peeker.classList.remove('hw-duck'); }, 1200);
        }
      }
    }
    if (rr && rr.width) look(riser, px - (rr.left + rr.width / 2), py - (rr.top + rr.height / 3));
    if (dr && dr.width) {
      var flee = drifter.querySelector('.hw-flee');
      // the outer box does not move; .hw-flee carries the escape
      var bx = dr.left + dr.width / 2;
      var by = dr.top + dr.height / 2;
      var ex = bx + drifterState.fx;
      var ey = by + drifterState.fy;
      look(drifter, px - ex, py - ey);
      var ddx = bx - px;
      var ddy = by - py;
      var dd = Math.sqrt(ddx * ddx + ddy * ddy) || 1;
      var tx = 0;
      var ty = 0;
      if (dd < 140) {
        var shove = 70 * (1 - dd / 140) + 20;
        tx = ddx / dd * shove;
        ty = ddy / dd * shove;
      }
      var gutter = (window.innerWidth - 1024) / 2;
      tx = clamp(tx, 6 - dr.left, gutter - 6 - dr.right);
      ty = clamp(ty, Math.max(-120, 8 - dr.top), Math.min(120, window.innerHeight - 8 - dr.bottom));
      if (flee) setFlee(flee, drifterState, tx, ty);
      drifter.classList.toggle('hw-spooked', dd < 140);
    }
  }

  // --------------------------------------------------- bubbles and taps
  function lines() {
    var out = ['BOO!', 'EEK!', 'Trick or treat?'];
    if (daysLeft >= 0) {
      out.push(daysLeft === 0 ? 'Last day of ' + S.name + '!'
        : (daysLeft === 1 ? '1 day of ' + S.name + ' left'
          : daysLeft + ' days of ' + S.name + ' left'));
    }
    return out;
  }
  function shuffle(list) {
    for (var i = list.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = list[i]; list[i] = list[j]; list[j] = t;
    }
    return list;
  }

  /* A speech bubble beside a ghost, inside its own strip.  The line is
     picked from the ones that fit the free room beside it, so a bubble in a
     narrow phone gap says BOO rather than sliding under the wallet. */
  function bubble(container, ghostRect, room) {
    each('.hw-boo', function (old) { old.parentNode.removeChild(old); }, container);
    var cr = container.getBoundingClientRect();
    var gl = ghostRect.left - cr.left;
    var gr = ghostRect.right - cr.left;
    var x0 = room ? room.x0 : 0;
    var x1 = room ? room.x1 : cr.width;
    var rightSpace = x1 - gr - 8;
    var leftSpace = gl - x0 - 8;
    var node = make('span', 'hw-boo');
    container.appendChild(node);
    var options = shuffle(lines());
    var chosen = null;
    var width = 0;
    for (var i = 0; i < options.length; i++) {
      node.textContent = options[i];
      width = node.offsetWidth;
      if (width <= Math.max(rightSpace, leftSpace)) { chosen = options[i]; break; }
    }
    if (!chosen) {
      node.textContent = 'BOO!';
      width = node.offsetWidth;
    }
    var right = width <= rightSpace || (width > leftSpace && rightSpace >= leftSpace);
    node.classList.toggle('hw-boo-l', !right);
    var x = right ? gr + 8 : gl - 8 - width;
    x = clamp(x, 2, Math.max(2, cr.width - width - 2));
    var bh = node.offsetHeight;
    var y = ghostRect.top - cr.top + ghostRect.height * 0.32 - bh / 2;
    y = clamp(y, 1, Math.max(1, cr.height - bh - 1));
    node.style.left = Math.round(x) + 'px';
    node.style.top = Math.round(y) + 'px';
    later(function () { if (node.parentNode) node.parentNode.removeChild(node); }, BUBBLE_MS);
    return node;
  }

  function spin(ghost) {
    if (reduced()) return;
    ghost.classList.remove('hw-booing');
    void ghost.offsetWidth;
    ghost.classList.add('hw-booing');
    later(function () { ghost.classList.remove('hw-booing'); }, 900);
  }

  var trickTimer = 0;
  function trick() {
    var chip = document.querySelector('.sn-chip');
    if (!chip) return;
    var t = chip.querySelector('.sn-chip-trick');
    if (!t) {
      t = make('span', 'sn-chip-trick');
      t.appendChild(make('span', 'sn-trick-long', 'Trick or treat? Open a crate'));
      t.appendChild(make('span', 'sn-trick-short', 'Trick or treat?'));
      chip.insertBefore(t, chip.querySelector('.sn-chip-go'));
    }
    chip.classList.add('sn-trick');
    cancel(trickTimer);
    trickTimer = later(function () { chip.classList.remove('sn-trick'); }, TRICK_MS);
  }

  function burst(container, x, y, n) {
    if (reduced() || !fxOn() || !container) return;
    for (var i = 0; i < n; i++) {
      if (container.querySelectorAll('.hw-burst').length >= MAX_BURSTS) return;
      var b = make('span', 'hw-burst');
      var sx = Math.random() < 0.5 ? -1 : 1;
      b.style.left = Math.round(x) + 'px';
      b.style.top = Math.round(y) + 'px';
      b.style.setProperty('--dx', Math.round(sx * (30 + Math.random() * 30)) + 'px');
      b.style.setProperty('--dy', Math.round(-(30 + Math.random() * 30) * (Math.random() < 0.8 ? 1 : -1)) + 'px');
      container.appendChild(b);
      (function (node) {
        var gone = function () { if (node.parentNode) node.parentNode.removeChild(node); };
        node.addEventListener('animationend', gone);
        later(gone, 1200);
      })(b);
    }
  }

  /* The header ghosts a tap can land on: placed floaters and the peeker. */
  function headerGhosts() {
    var out = [];
    slots.forEach(function (s) { if (!s.moon && s.placed) out.push({ el: s.el, box: s.box }); });
    if (peeker) out.push({ el: peeker, box: null });
    return out.filter(function (g) { return shown(g.el); });
  }

  function booGhost(g) {
    var target = g.el.querySelector('.hw-flee') || g.el;
    spin(g.el);
    bubble(sky, target.getBoundingClientRect(), g.box);
    trick();
  }

  function booRandom() {
    if (!active || !sky || !fxOn()) return false;
    var list = headerGhosts();
    if (!list.length) return false;
    booGhost(list[Math.floor(Math.random() * list.length)]);
    return true;
  }

  var lastTap = 0;
  function onBarDown(e) {
    if (!active || !sky || lite()) return;
    var t = e.target;
    if (t && t.closest && t.closest('a,button,input,select,textarea,label,form,[role=button],.wallet')) return;
    var now = Date.now();
    if (now - lastTap < 600) return;
    lastTap = now;
    var x = e.clientX;
    var y = e.clientY;
    var hit = null;
    if (fxOn()) {
      headerGhosts().some(function (g) {
        var r = (g.el.querySelector('.hw-flee') || g.el).getBoundingClientRect();
        if (x >= r.left - 12 && x <= r.right + 12 && y >= r.top - 12 && y <= r.bottom + 12) {
          hit = g;
          return true;
        }
        return false;
      });
    }
    if (hit) { booGhost(hit); return; }
    var sr = sky.getBoundingClientRect();
    burst(sky, x - sr.left, y - sr.top, 3);
  }

  function onRiserDown() {
    if (!active || !riser || !fxOn()) return;
    var now = Date.now();
    if (now - lastTap < 600) return;
    lastTap = now;
    if (!reduced()) rise(1800);
    spin(riser);
    bubble(yard, (riser.querySelector('.hw-flee') || riser).getBoundingClientRect(), null);
    each('.hw-jack', function (j) {
      j.classList.add('hw-flare');
      later(function () { j.classList.remove('hw-flare'); }, 600);
    }, yard);
  }

  // ---------------------------------------------------------- the yard
  var rises = 0;
  var riseTimer = 0;
  function rise(ms) {
    if (!riser) return;
    riser.classList.add('hw-up');
    cancel(riseTimer);
    riseTimer = later(function () { riser.classList.remove('hw-up'); }, ms);
  }
  function syncStill() {
    if (riser) riser.classList.toggle('hw-still', reduced());
  }

  // ------------------------------------------------------- the gutters
  var scrollBound = false;
  var scrollQueued = false;
  var lastY = 0;
  var drop = 0;
  var climbTimer = 0;
  var swingTimer = 0;
  function fxShownNow() {
    return !!fx && active && getComputedStyle(fx).display !== 'none';
  }
  function onScroll() {
    if (!scrollQueued) {
      scrollQueued = true;
      requestAnimationFrame(safe(scrollFrame));
    }
  }
  var safeScroll = safe(onScroll);
  function scrollFrame() {
    scrollQueued = false;
    if (!scrollBound || !spider) return;
    var y = window.pageYOffset || document.documentElement.scrollTop || 0;
    var dy = y - lastY;
    lastY = y;
    if (dy > 0) drop = Math.min(130, drop + dy * 0.35);
    else drop = Math.max(0, drop + dy * 0.6);
    var sw = clamp(-dy * 0.2, -6, 6);
    spider.classList.remove('hw-climb');
    spider.style.setProperty('--drop', drop.toFixed(1));
    spider.style.setProperty('--sw', sw.toFixed(2));
    spider.classList.toggle('hw-on', y >= 160);
    cancel(swingTimer);
    swingTimer = later(function () { spider.style.setProperty('--sw', '0'); }, 180);
    cancel(climbTimer);
    climbTimer = later(function () {
      drop = 0;
      spider.classList.add('hw-climb');
      spider.style.setProperty('--drop', '0');
    }, 2000);
  }
  function bindScroll() {
    if (scrollBound) return;
    lastY = window.pageYOffset || 0;
    window.addEventListener('scroll', safeScroll, { passive: true });
    scrollBound = true;
    if (spider) spider.classList.toggle('hw-on', lastY >= 160);
  }
  function unbindScroll() {
    if (!scrollBound) return;
    window.removeEventListener('scroll', safeScroll, { passive: true });
    scrollBound = false;
    drop = 0;
    if (spider) {
      spider.style.setProperty('--drop', '0');
      spider.style.setProperty('--sw', '0');
      spider.classList.remove('hw-on');
    }
  }
  function syncFx() {
    if (fxShownNow() && !reduced()) bindScroll(); else unbindScroll();
  }

  // ----------------------------------------------------------- critters
  function syncSwitches() {
    var on = fxOn();
    each('.sn-fx-switch', function (sw) { sw.setAttribute('aria-checked', on ? 'true' : 'false'); });
  }
  function refresh() {
    if (!active) return;
    syncStill();
    syncPointer();
    syncFx();
    queuePlace();
  }
  function setFx(on) {
    if (!active) return;
    on = !!on;
    try { localStorage.setItem(FX_KEY, on ? 'on' : 'off'); } catch (e) {}
    if (on) root.removeAttribute('data-season-fx');
    else root.setAttribute('data-season-fx', 'off');
    syncSwitches();
    if (!on) each('.hw-boo, .hw-burst', function (n) { if (n.parentNode) n.parentNode.removeChild(n); });
    refresh();
    if (window.Site && Site.toast) {
      Site.toast(on ? 'The critters are back.'
                    : (CRITTERS[S.holiday] || 'The critters') + ' are off.');
    }
  }

  // --------------------------------------------------------- celebration
  /* An Unusual (or a legendary or mythic) out of a crate: once the opening
     stage has closed, every ghost in sight jumps for joy. */
  var pendingCheer = false;
  var cheerWatch = null;
  function cheer() {
    if (!pendingCheer || document.body.classList.contains('cs-open')) return;
    pendingCheer = false;
    if (cheerWatch) { cheerWatch.disconnect(); cheerWatch = null; }
    if (!fxOn() || !active) return;
    var ghosts = [];
    slots.forEach(function (s) { if (!s.moon && s.placed) ghosts.push(s.el); });
    [peeker, riser, drifter].forEach(function (g) { if (g) ghosts.push(g); });
    ghosts.filter(shown).forEach(function (g) {
      g.classList.remove('hw-cheer');
      void g.offsetWidth;
      g.classList.add('hw-cheer');
      later(function () { g.classList.remove('hw-cheer'); }, 1300);
    });
    if (riser && yardVisible && !reduced()) rise(1600);
    if (sky && skyVisible && !reduced()) {
      var w = sky.clientWidth;
      for (var i = 0; i < 3; i++) {
        burst(sky, w * (0.2 + 0.3 * i), 6 + Math.random() * 10, 2);
      }
    }
  }
  function onOpened(e) {
    var item = e && e.detail && e.detail.item;
    if (!item) return;
    if (item.tier !== 'unusual' && item.grade !== 'legendary' && item.grade !== 'mythic') return;
    pendingCheer = true;
    if (document.body.classList.contains('cs-open')) {
      if (!cheerWatch && window.MutationObserver) {
        cheerWatch = watch(new MutationObserver(safe(cheer)));
        cheerWatch.observe(document.body, { attributes: true, attributeFilter: ['class'] });
      }
    } else {
      cheer();
    }
  }

  // ---------------------------------------------------------------- boot
  function boot() {
    if (!active) return;
    // the clock: one interval, plus a re-check whenever the tab comes back
    tick();
    interval = setInterval(safe(tick), 60000);
    listen(document, 'visibilitychange', function () {
      root.classList.toggle('sn-hold', document.hidden);
      if (!document.hidden) tick();
    });
    listen(window, 'pageshow', function () { tick(); });
    onMedia(darkQ, function () {
      if ((root.getAttribute('data-theme') || 'auto') === 'auto') applyMeta();
    });

    // the critter switches (Settings and the phone drawer)
    syncSwitches();
    each('.sn-fx-switch', function (sw) {
      listen(sw, 'click', function () { setFx(sw.getAttribute('aria-checked') !== 'true'); });
    });

    // the drawer's pumpkins light up one row after another
    each('.tabbar .wrap > a', function (a, i) { a.style.setProperty('--sn-i', i); });

    if (lite()) return;     // the quiet pages: the clock and the end check only

    syncStill();
    if (sky) {
      placeSlots();
      listen(window, 'resize', onResize, { passive: true });
      if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(function () { queuePlace(); }, function () {});
      }
      var logo = document.querySelector('.topbar .brand-logo');
      if (logo && !logo.complete) listen(logo, 'load', queuePlace);
      if (window.MutationObserver && row) {
        watch(new MutationObserver(function () { queuePlace(); }))
          .observe(row, { childList: true, characterData: true, subtree: true });
      }
      if (window.IntersectionObserver && bar) {
        watch(new IntersectionObserver(function (entries) {
          entries.forEach(function (en) {
            skyVisible = en.isIntersecting;
            sky.classList.toggle('hw-idle', !en.isIntersecting);
          });
        }, { threshold: 0 })).observe(bar);
      }
      listen(bar || sky, 'pointerdown', onBarDown, { passive: true });
    }
    if (yard && riser) {
      if (window.IntersectionObserver) {
        watch(new IntersectionObserver(function (entries) {
          entries.forEach(function (en) {
            yardVisible = en.isIntersecting;
            yard.classList.toggle('hw-idle', !en.isIntersecting);
          });
        }, { threshold: 0 })).observe(yard);
        watch(new IntersectionObserver(function (entries) {
          entries.forEach(function (en) {
            if (en.intersectionRatio < 0.6 || rises >= MAX_RISES) return;
            if (reduced() || !fxOn() || riser.classList.contains('hw-up')) return;
            rises++;
            rise(3200);
          });
        }, { threshold: [0.6] })).observe(yard);
      }
      listen(riser, 'pointerdown', onRiserDown, { passive: true });
    }
    // lets iOS apply :active to the chip and the tabs
    listen(document, 'touchstart', function () {}, { passive: true });

    onMedia(reduceQ, refresh);
    onMedia(fineQ, refresh);
    onMedia(wideQ, refresh);
    listen(document, 'crates:opened', onOpened);
    syncPointer();
    syncFx();
  }

  function start() {
    try { boot(); } catch (e) { /* the static skin stays; nothing else is touched */ }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
