/* The market: the event hero, the live drop feed, the crate hall, the
   spotlight and the aisles.  Buying and opening are crates.js (Crates.buy,
   Crates.open); this file is the page around them. */
(function () {
  'use strict';

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function esc(t) { return Site.escape(t); }
  function reduced() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  // ------------------------------------------------------------ countdown
  function bindCountdown() {
    var hero = $('[data-event-ends]');
    if (!hero) return;
    var ends = parseInt(hero.dataset.eventEnds, 10) || 0;
    var serverNow = parseInt(($('#market') || {}).dataset ? $('#market').dataset.now : 0, 10) || 0;
    var skew = serverNow ? serverNow - Math.floor(Date.now() / 1000) : 0;
    function pad(n) { return n < 10 ? '0' + n : String(n); }
    function tick() {
      var left = Math.max(0, ends - (Math.floor(Date.now() / 1000) + skew));
      var parts = { d: Math.floor(left / 86400), h: pad(Math.floor(left / 3600) % 24),
                    m: pad(Math.floor(left / 60) % 60), s: pad(left % 60) };
      Object.keys(parts).forEach(function (k) {
        var node = hero.querySelector('[data-cd="' + k + '"]');
        if (node && node.textContent !== String(parts[k])) {
          node.textContent = parts[k];
          if (k === 's') { node.classList.remove('flip'); void node.offsetWidth; node.classList.add('flip'); }
        }
      });
    }
    tick();
    setInterval(tick, 1000);
  }

  // ------------------------------------------------------------ the hero
  function bindHero() {
    var canvas = $('#hero-crate');
    if (!canvas || !window.Thumbs) return;
    Thumbs.loadCatalog().then(function () {
      Thumbs.animateItem(canvas, canvas.dataset.item, 'haunted_wisps',
                         { spin: 0.45, scale: 1.1, padding: 1.3 });
    });
    canvas.addEventListener('click', function () { Crates.showContents('halloween'); });
  }

  // ----------------------------------------------------------- spotlight
  /* One piece at a time on a turntable, trying on Unusual effects: the
     thing a crate might hand you, shown the way it would look. */
  var SPOT_EFFECTS = {
    classic: ['burning', 'starstruck', 'void_mist', 'frostbite', 'circuitry', 'sunbeam',
              'static_charge', 'ember_storm', 'scorching'],
    halloween: ['phantom_procession', 'trick_or_treat', 'flying_skulls', 'bat_swarm',
                'jack_o_lanterns', 'haunted_wisps', 'cursed_runes']
  };

  function bindSpotlight() {
    var canvas = $('#spot-canvas');
    var list = $('#spot-list');
    if (!canvas || !list || !window.Thumbs) return;
    var picks = $$('[data-spot]', list);
    var index = 0, timer = 0, effectIndex = 0;
    function show(i, keepEffect) {
      index = (i + picks.length) % picks.length;
      var pick = picks[index];
      picks.forEach(function (p) { p.classList.toggle('on', p === pick); });
      var crate = pick.dataset.crate;
      var pool = SPOT_EFFECTS[crate] || SPOT_EFFECTS.classic;
      if (!keepEffect) effectIndex = Math.floor(Math.random() * pool.length);
      var effect = pool[effectIndex % pool.length];
      var item = (Thumbs.catalog || {})[pick.dataset.spot];
      var hatLike = item && item.slot === 'hat';
      var fx = $('#spot-fx');
      if (fx) {
        fx.innerHTML = hatLike
          ? '&#9733; Shown Unusual: <b>' + esc((Thumbs.effects[effect] || {}).name || '') + '</b>'
          : 'Not a hat &mdash; but a <b>' + esc(pick.dataset.rarity) + '</b> pull';
        fx.classList.remove('pop'); void fx.offsetWidth; fx.classList.add('pop');
      }
      var copy = $('#spot-copy');
      if (copy) {
        copy.innerHTML = '<b>' + esc(pick.dataset.name) + '</b><span class="r-' + esc(pick.dataset.rarity) + '">' +
          esc(pick.dataset.rarity) + '</span><p>' + esc(pick.dataset.desc) + '</p>' +
          '<button class="mk-link" data-contents="' + esc(crate) + '">Comes out of the ' +
          (crate === 'halloween' ? 'Hallowed Harvest' : 'Blockhaven Hat') + ' Crate &rarr;</button>';
      }
      Thumbs.animateItem(canvas, pick.dataset.spot, hatLike ? effect : '', { spin: 0.55 });
    }
    function schedule() {
      clearInterval(timer);
      if (reduced()) return;
      // the effect changes every few seconds, the piece every other time
      var beats = 0;
      timer = setInterval(function () {
        beats++;
        if (beats % 2) { effectIndex++; show(index, true); } else show(index + 1);
      }, 3600);
    }
    picks.forEach(function (pick, i) {
      pick.addEventListener('click', function () { show(i); schedule(); });
    });
    Thumbs.loadCatalog().then(function () { show(0); schedule(); });
  }

  // ------------------------------------------------------------ live feed
  function bindFeed() {
    var track = $('#drop-track');
    if (!track) return;
    var seen = {};
    function key(d) { return d.username + '|' + d.at + '|' + d.item_id; }
    function chip(d) {
      var span = document.createElement('span');
      span.className = 'mk-drop' + (d.tier === 'unusual' ? ' unusual' : '') + ' fresh';
      span.style.setProperty('--g', d.color);
      span.innerHTML = '<b>' + esc(d.username) + '</b> unboxed <i>' +
        (d.tier === 'unusual' ? 'Unusual ' + esc(d.effect_name) + ' ' : '') + esc(d.name) +
        '</i><small>' + esc(d.grade_label) + '</small>';
      return span;
    }
    function poll(first) {
      Site.get('/api/crates/feed?limit=14').then(function (res) {
        if (!res.ok) return;
        var count = $('#opened-count');
        if (count) count.textContent = (res.stats.opened || 0).toLocaleString();
        var fresh = res.feed.filter(function (d) { return !seen[key(d)]; });
        res.feed.forEach(function (d) { seen[key(d)] = 1; });
        if (first) return;
        if (fresh.length) {
          var empty = track.querySelector('.mk-drop.empty');
          if (empty) empty.remove();
        }
        fresh.reverse().forEach(function (d) {
          track.insertBefore(chip(d), track.firstChild);
          if (d.tier === 'unusual' && BH.user && d.username !== BH.user.name) {
            Site.toast('★ ' + d.username + ' just unboxed an UNUSUAL ' + d.effect_name + ' ' + d.name + '!', 'info');
          }
        });
        while (track.children.length > 30) track.removeChild(track.lastChild);
      }).catch(function () {});
    }
    poll(true);
    setInterval(function () { if (!document.hidden) poll(false); }, 9000);
    document.addEventListener('crates:opened', function () { setTimeout(function () { poll(false); }, 400); });
  }

  // ----------------------------------------------------------- odds bars
  function bindOdds() {
    $$('[data-oddsbar]').forEach(function (bar) {
      var series = bar.dataset.oddsbar;
      Site.get('/api/crates/contents?series=' + encodeURIComponent(series)).then(function (res) {
        if (!res.ok) return;
        bar.innerHTML = res.grades.map(function (g) {
          return '<i style="flex:' + g.chance + ';background:' + g.color + '" title="' +
            esc(g.label) + ' ' + g.chance + '%"></i>';
        }).join('');
        var key = $('[data-oddskey="' + series + '"]');
        if (key) {
          key.innerHTML = res.grades.map(function (g) {
            return '<span><b style="background:' + g.color + '"></b>' + esc(g.label) + ' ' + g.chance + '%</span>';
          }).join('');
        }
      });
    });
  }

  // --------------------------------------------------------- tilt + shine
  /* Cards lean towards the pointer and a sheen follows it across, so the
     shelf feels like it has things on it rather than pictures of things. */
  function bindTilt() {
    if (reduced() || !window.matchMedia('(hover: hover)').matches) return;
    $$('[data-tilt]').forEach(function (card) {
      card.addEventListener('pointermove', function (e) {
        var r = card.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
        card.style.setProperty('--ry', ((x - 0.5) * 12).toFixed(2) + 'deg');
        card.style.setProperty('--rx', ((0.5 - y) * 10).toFixed(2) + 'deg');
        card.style.setProperty('--mx', (x * 100).toFixed(1) + '%');
        card.style.setProperty('--my', (y * 100).toFixed(1) + '%');
        card.classList.add('tilting');
      });
      card.addEventListener('pointerleave', function () {
        card.classList.remove('tilting');
        card.style.setProperty('--ry', '0deg');
        card.style.setProperty('--rx', '0deg');
      });
    });
  }

  // ---------------------------------------------------------- quantities
  function bindQty() {
    $$('[data-qty-for]').forEach(function (box) {
      var input = box.querySelector('input');
      box.addEventListener('click', function (e) {
        var b = e.target.closest('[data-step]');
        if (!b) return;
        var v = Math.max(1, Math.min(10, (parseInt(input.value, 10) || 1) + parseInt(b.dataset.step, 10)));
        input.value = v;
        var buy = document.querySelector('[data-buy="' + box.dataset.qtyFor + '"].small');
        if (buy) buy.querySelector('span').textContent = v > 1 ? 'Buy ' + v : 'Buy';
      });
      input.addEventListener('change', function () {
        input.value = Math.max(1, Math.min(10, parseInt(input.value, 10) || 1));
      });
    });
  }

  // ---------------------------------------------------------------- boot
  document.addEventListener('DOMContentLoaded', function () {
    bindCountdown();
    bindHero();
    bindSpotlight();
    bindFeed();
    bindOdds();
    bindTilt();
    bindQty();
    document.addEventListener('click', function (e) {
      var b = e.target.closest('[data-buy], [data-offer]');
      if (!b || b.disabled) return;
      e.preventDefault();
      if (window.Crates) Crates.buy(b);
    });
    // a crate opened from this page changes the feed and the counts
    if (window.Crates) {
      var open = Crates.open;
      Crates.open = function (options) {
        options = options || {};
        var done = options.onResult;
        options.onResult = function (res) {
          document.dispatchEvent(new CustomEvent('crates:opened', { detail: res }));
          if (done) done(res);
        };
        return open(options);
      };
    }
  });
})();
