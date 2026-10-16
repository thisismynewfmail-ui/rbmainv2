/* The Crate Vault (/market): the page's own behaviour around the shelves.

   Buying and opening are crates.js (Crates.buy, Crates.open); the countdown,
   the hero turntable, the spotlight and the drop feed are market.js.  This
   file is the rest of the vault:

     the toolbar        jumps to a section, lights the one you are in
     the Crate Hall     one tab per holiday wing, keyboard and hash driven,
                        remembered for the day
     the stash          keeps the Event Console, the Key Ring and the owned
                        flags right as crates and keys come and go
     the buy bar        the console's buttons, pinned to the bottom of a
                        phone once the console has scrolled away
     sealed shelves     count down to the day they unseal
     the ghost          the Halloween console's ghost, and its opinions
     tooltips           what a piece is, where it comes from, on desktop

   It opens no WebGL of its own and never rescans thumbnails: thumbs.js
   paints a hidden canvas when it is shown. */
(function () {
  'use strict';

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function reduced() {
    return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }
  function hover() {
    return !!(window.matchMedia && window.matchMedia('(hover: hover)').matches);
  }
  function store(key, value) {
    try {
      if (value === undefined) return JSON.parse(localStorage.getItem(key) || 'null');
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) { /* private mode, or storage full: the vault works without it */ }
    return null;
  }
  function today() { return new Date().toISOString().slice(0, 10); }

  // -------------------------------------------------------------- toolbar
  function bindToolbar() {
    var tools = $$('.vt-tool');
    if (!tools.length) return;
    tools.forEach(function (tool) {
      tool.addEventListener('click', function (e) {
        var target = $(tool.getAttribute('href'));
        if (!target) return;
        e.preventDefault();
        target.scrollIntoView({ behavior: reduced() ? 'auto' : 'smooth', block: 'start' });
      });
    });
    var topbar = $('.topbar');
    if (topbar && getComputedStyle(topbar).position === 'sticky') {
      document.documentElement.style.setProperty('--vt-stick', topbar.offsetHeight + 'px');
    }
    if (!('IntersectionObserver' in window)) return;
    var seen = {};
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { seen[en.target.id] = en.isIntersecting; });
      var lit = false;
      tools.forEach(function (tool) {
        var id = (tool.getAttribute('href') || '').slice(1);
        var on = !lit && !!seen[id];
        tool.classList.toggle('on', on);
        if (on) lit = true;
      });
    }, { rootMargin: '-30% 0px -55% 0px' });
    ['console', 'hall', 'stash-bar', 'aisles', 'odds'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) io.observe(el);
    });
  }

  // ------------------------------------------------------- the Crate Hall
  function bindWings() {
    var tabs = $$('.vt-wing-tab');
    if (!tabs.length) return;
    var KEY = 'blockhaven.vault.wing';
    function panelOf(id) { return document.getElementById('hall-' + id); }
    function idOf(tab) { return tab.id.replace(/^tab-/, ''); }
    function select(id, opts) {
      opts = opts || {};
      if (!panelOf(id)) return false;
      tabs.forEach(function (tab) {
        var on = idOf(tab) === id;
        tab.setAttribute('aria-selected', on ? 'true' : 'false');
        tab.setAttribute('tabindex', on ? '0' : '-1');
        var panel = panelOf(idOf(tab));
        if (panel) panel.hidden = !on;
      });
      if (opts.focus) document.getElementById('tab-' + id).focus();
      if (opts.push) {
        store(KEY, { wing: id, day: today() });
        try { history.replaceState(null, '', '#hall-' + id); } catch (e) { /* file:// and friends */ }
      }
      return true;
    }
    function openShelf(seriesId) {
      var shelf = document.getElementById('ed-' + seriesId);
      if (!shelf) return false;
      var wing = shelf.closest('.vt-wing');
      if (wing) select(wing.id.replace(/^hall-/, ''));
      var loot = $('details.vt-loot', shelf);
      if (loot) loot.open = true;
      shelf.scrollIntoView({ behavior: reduced() ? 'auto' : 'smooth', block: 'start' });
      return true;
    }
    function fromHash() {
      var h = location.hash;
      var m = /^#hall-([a-z0-9_]+)$/.exec(h);
      if (m) return select(m[1]);
      m = /^#ed-([a-z0-9_]+)$/.exec(h);
      if (m) return openShelf(m[1]);
      return false;
    }
    if (!fromHash()) {
      var kept = store(KEY);
      if (kept && kept.day === today()) select(kept.wing);
    }
    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function (e) {
        e.preventDefault();
        select(idOf(tab), { push: true });
      });
      tab.addEventListener('keydown', function (e) {
        var to = null;
        if (e.key === 'ArrowRight') to = tabs[(i + 1) % tabs.length];
        else if (e.key === 'ArrowLeft') to = tabs[(i - 1 + tabs.length) % tabs.length];
        else if (e.key === 'Home') to = tabs[0];
        else if (e.key === 'End') to = tabs[tabs.length - 1];
        if (!to) return;
        e.preventDefault();
        select(idOf(to), { focus: true, push: true });
      });
    });
    window.addEventListener('hashchange', fromHash);
  }

  // ------------------------------------------------------------ the stash
  function needOf(held) {
    if (held.crates > 0 && held.keys > 0) return 'open';
    if (held.crates > 0) return 'key';
    if (held.keys > 0) return 'crate';
    return 'buy';
  }
  function pop(node, text) {
    if (!node || node.textContent === String(text)) return;
    node.textContent = text;
    node.classList.remove('pop'); void node.offsetWidth; node.classList.add('pop');
  }
  function bindStash() {
    document.addEventListener('crates:stash', function (e) {
      var stash = e.detail || {};
      // the Event Console and the phone buy bar follow its crate's counts
      var console_ = $('#console[data-sid]');
      if (console_ && window.BH && BH.user) {
        var held = stash[console_.dataset.sid] || { crates: 0, keys: 0 };
        var need = needOf(held);
        console_.dataset.need = need;
        var bar = $('#vt-buybar');
        if (bar) bar.dataset.need = need;
        pop($('[data-held="crates"]', console_), held.crates);
        pop($('[data-held="keys"]', console_), held.keys);
        $$('[data-ready]').forEach(function (n) { n.textContent = Math.min(held.crates, held.keys); });
      }
      // the Key Ring: a row shows while it holds anything, flagged with
      // whatever its pair is missing
      $$('.vt-ringrow[data-series]').forEach(function (row) {
        var h = stash[row.dataset.series] || { crates: 0, keys: 0 };
        var was = row.classList.contains('empty');
        var empty = !(h.crates > 0 || h.keys > 0);
        row.classList.toggle('empty', empty && !row.classList.contains('pinned'));
        row.classList.toggle('vt-need-key', h.crates > h.keys);
        row.classList.toggle('vt-need-crate', h.keys > h.crates);
        if (was && !empty) {
          row.classList.remove('vt-in'); void row.offsetWidth; row.classList.add('vt-in');
        }
      });
      // owned flags on every crate and key on the page
      var series = window.CRATE_SERIES || {};
      Object.keys(stash).forEach(function (id) {
        var s = series[id];
        if (!s) return;
        [[s.crate, stash[id].crates], [s.key, stash[id].keys]].forEach(function (pair) {
          if (!pair[0]) return;
          $$('[data-owned="' + pair[0] + '"]').forEach(function (flag) {
            flag.textContent = 'x' + pair[1];
            flag.classList.toggle('hidden', !pair[1]);
          });
        });
      });
    });
  }

  // ---------------------------------------------------------- the buy bar
  function bindBuybar() {
    var bar = $('#vt-buybar');
    var slot = $('#console .vt-arcade-slot');
    if (!bar || !slot || !('IntersectionObserver' in window)) return;
    var away = false, frame = 0;
    function apply() {
      frame = 0;
      var show = away && window.innerWidth <= 760;
      bar.hidden = !show;
      bar.classList.toggle('on', show);
      document.body.classList.toggle('vt-buybar-on', show);
    }
    new IntersectionObserver(function (entries) {
      away = !entries[0].isIntersecting;
      apply();
    }).observe(slot);
    window.addEventListener('resize', function () {
      if (!frame) frame = requestAnimationFrame(apply);
    });
  }

  // ----------------------------------------------------- sealed shelves
  function bindUnseal() {
    var labels = $$('[data-unseal]');
    if (!labels.length) return;
    var root = $('#market');
    var serverNow = parseInt((root && root.dataset.now) || '0', 10) || 0;
    var skew = serverNow ? serverNow - Math.floor(Date.now() / 1000) : 0;
    function tick() {
      if (document.hidden) return;
      var now = Math.floor(Date.now() / 1000) + skew;
      labels.forEach(function (label) {
        if (!label.isConnected) return;
        var left = (parseInt(label.dataset.unseal, 10) || 0) - now;
        if (left <= 0) {
          var shelf = label.closest('[data-series]');
          var a = document.createElement('a');
          a.href = '/market#ed-' + (shelf ? shelf.dataset.series : '');
          a.textContent = 'Unsealed! Reload the Vault';
          label.replaceWith(a);
          return;
        }
        label.textContent = Math.floor(left / 86400) + 'd ' + Math.floor((left % 86400) / 3600) + 'h';
      });
    }
    tick();
    setInterval(tick, 60000);
  }

  // ------------------------------------------------------------ the ghost
  var BOO_TAPS = ['Boo! …sorry. Habit.', 'Psst. The odds are posted — peek inside.',
                  'Get the pair. A crate without its key is just a box.'];
  function bindBoo() {
    var root = $('#market[data-holiday="halloween"]');
    var boo = $('.vt-boo');
    if (!root || !boo) return;
    var says = $('.vt-boo-says');
    var live = $('#vt-boo-live');
    var stage = $('#console');
    var crate = $('#hero-crate');
    var tapN = 0, timer = 0;
    function say(line, move) {
      if (says) {
        says.textContent = line;
        says.classList.add('on');
      }
      if (live) live.textContent = line;
      if (move && !reduced()) {
        boo.classList.remove('vt-hop', 'vt-spin'); void boo.offsetWidth; boo.classList.add(move);
      }
      clearTimeout(timer);
      timer = setTimeout(function () { if (says) says.classList.remove('on'); }, 3500);
    }
    boo.addEventListener('click', function () {
      say(BOO_TAPS[tapN++ % BOO_TAPS.length], 'vt-hop');
    });
    document.addEventListener('crates:bought', function (e) {
      var d = e.detail || {};
      var kit = d.offer || d.slot === 'crate' || d.slot === 'key';
      say(kit ? 'Into your Key Ring it goes!' : 'Looks good on you.', 'vt-hop');
    });
    document.addEventListener('crates:opened', function (e) {
      var item = (e.detail || {}).item || {};
      if (item.tier === 'unusual') say('B-by the Pumpkin King! An Unusual!', 'vt-spin');
      else if (item.grade === 'legendary' || item.grade === 'mythic') say('Now THAT is a pull.', 'vt-hop');
    });
    if (root.classList.contains('vt-last')) {
      setTimeout(function () { say('Last call! The Harvest packs up soon.'); }, 1800);
    }
    // the eyes follow the pointer, and the sky drifts a little behind it
    if (!stage || !hover() || reduced() || !('IntersectionObserver' in window)) return;
    var eyes = $('.vt-eyes', boo);
    var visible = false, frame = 0, last = null;
    new IntersectionObserver(function (en) { visible = en[0].isIntersecting; }).observe(stage);
    function draw() {
      frame = 0;
      if (!last) return;
      var r = stage.getBoundingClientRect();
      var px = Math.max(-1, Math.min(1, (last.x - (r.left + r.width / 2)) / (r.width / 2)));
      var py = Math.max(-1, Math.min(1, (last.y - (r.top + r.height / 2)) / (r.height / 2)));
      stage.style.setProperty('--px', px.toFixed(3));
      stage.style.setProperty('--py', py.toFixed(3));
      if (eyes) {
        var b = boo.getBoundingClientRect();
        var ex = Math.max(-1.5, Math.min(1.5, (last.x - (b.left + b.width / 2)) / 60));
        var ey = Math.max(-1.5, Math.min(1.5, (last.y - (b.top + b.height / 2)) / 60));
        eyes.setAttribute('transform', 'translate(' + ex.toFixed(2) + ' ' + ey.toFixed(2) + ')');
      }
      if (crate) {
        var c = crate.getBoundingClientRect();
        var dx = last.x - (c.left + c.width / 2), dy = last.y - (c.top + c.height / 2);
        boo.classList.toggle('vt-duck', dx * dx + dy * dy < 120 * 120);
      }
    }
    stage.addEventListener('pointermove', function (e) {
      if (!visible) return;
      last = { x: e.clientX, y: e.clientY };
      if (!frame) frame = requestAnimationFrame(draw);
    }, { passive: true });
  }

  // ------------------------------------------------------------- tooltips
  var SLOT_NAMES = { hat: 'Hat', face: 'Face', hair: 'Hair', back: 'Back', shirt: 'Shirt',
                     pants: 'Pants', belt: 'Belt', usable: 'Usable', crate: 'Crate', key: 'Key' };
  function bindTips() {
    if (!hover()) return;
    var tip = null, showTimer = 0;
    function make() {
      tip = document.createElement('div');
      tip.id = 'vt-tip';
      tip.className = 'vt-tip';
      tip.setAttribute('role', 'tooltip');
      tip.hidden = true;
      document.body.appendChild(tip);
      return tip;
    }
    function hide() {
      clearTimeout(showTimer);
      if (tip) tip.hidden = true;
    }
    function content(el) {
      var canvas = $('canvas[data-item]', el);
      var id = el.dataset.item || (canvas && canvas.dataset.item) || '';
      var cat = (window.Thumbs && Thumbs.catalog && Thumbs.catalog[id]) || {};
      var nameEl = $('.vt-name', el);
      var name = (nameEl && nameEl.textContent.trim()) || cat.name || '';
      if (!name) return '';
      var grade = (cat.rarity || '').toLowerCase();
      var slot = SLOT_NAMES[cat.slot] || '';
      var bits = ['<b class="g-' + Site.escape(grade || 'common') + '">' + Site.escape(name) + '</b>'];
      var small = [slot, grade ? grade.charAt(0).toUpperCase() + grade.slice(1) : ''].filter(Boolean).join(' · ');
      if (small) bits.push('<small>' + Site.escape(small) + '</small>');
      if (cat.slot === 'hat') bits.push('<span>★ Can come out Unusual</span>');
      else if ($('.vt-lock', el)) bits.push('<span>Only comes out of the crate</span>');
      var shelf = el.closest('.vt-shelf');
      if (shelf && shelf.dataset.title) bits.push('<span>From ' + Site.escape(shelf.dataset.title) + '</span>');
      if (cat.price > 0) bits.push('<span>Sells back for ' + Math.floor(cat.price * 0.4) + '</span>');
      return bits.join('');
    }
    function place(el) {
      var html = content(el);
      if (!html) return;
      (tip || make()).innerHTML = html;
      tip.hidden = false;
      var r = el.getBoundingClientRect(), t = tip.getBoundingClientRect();
      var x = r.left + r.width / 2 - t.width / 2;
      var y = r.top - t.height - 8;
      if (y < 8) y = r.bottom + 8;
      x = Math.max(8, Math.min(window.innerWidth - t.width - 8, x));
      tip.style.left = Math.round(x + window.scrollX) + 'px';
      tip.style.top = Math.round(y + window.scrollY) + 'px';
    }
    function over(e) {
      var el = e.target.closest && e.target.closest('.vt-piece, .vt-slotcard, .mk-chase-item');
      if (!el || $('.modal-scrim')) return;
      clearTimeout(showTimer);
      showTimer = setTimeout(function () { place(el); }, 120);
    }
    function out(e) {
      var el = e.target.closest && e.target.closest('.vt-piece, .vt-slotcard, .mk-chase-item');
      if (el && (!e.relatedTarget || !el.contains(e.relatedTarget))) hide();
    }
    document.addEventListener('pointerover', over);
    document.addEventListener('focusin', over);
    document.addEventListener('pointerout', out);
    document.addEventListener('focusout', out);
    window.addEventListener('scroll', hide, { passive: true });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') hide(); });
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (!$('#market.vt')) return;
    bindToolbar();
    bindWings();
    bindStash();
    bindBuybar();
    bindUnseal();
    bindBoo();
    bindTips();
  });
})();
