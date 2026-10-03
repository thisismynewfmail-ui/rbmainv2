/* BLOCKHAVEN -- crates and keys.

   Everything the site does with a crate lives here, so the market and the
   inventory share one of each:

     Crates.showContents(series)   what is inside and the odds of each thing
     Crates.open(options)          the opening: crate, key, lock, lid, reel,
                                   reveal -- themed per series
     Crates.buy(button)            buying a key, a crate or a bundle, with the
                                   coin shower into the wallet

   The outcome is decided on the server the moment the key turns (the request
   goes out as the stage opens); everything on screen is the show around a
   result that is already fixed.  The reel is built by the server around the
   winner, so the strip you watch is the strip it really stopped on. */
(function (global) {
  'use strict';

  var Crates = {};
  var TAU = Math.PI * 2;

  function esc(text) { return global.Site ? Site.escape(text) : String(text); }
  function num(n) { return (parseInt(n, 10) || 0).toLocaleString(); }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function easeOut(t) { return 1 - Math.pow(1 - t, 3); }
  function easeInOut(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  function easeOutBack(t) { var c = 1.7; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); }
  function reduced() {
    return global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  var GRADE_COLORS = { common: '#9fb0c2', uncommon: '#4fc46e', rare: '#3d8bfd',
                       legendary: '#f2a93b', mythic: '#ff4d6d', unusual: '#b26bff' };
  var GRADE_LABELS = { common: 'Common', uncommon: 'Uncommon', rare: 'Rare',
                       legendary: 'Legendary', mythic: 'Mythic', unusual: 'Unusual' };
  var WEARABLE = { hat: 1, hair: 1, face: 1, shirt: 1, pants: 1, belt: 1, back: 1 };

  // ================================================================= sound
  /* Every sound is synthesised -- the platform ships without audio files --
     and the whole lot can be muted from the stage (remembered per browser). */
  var Sfx = { ctx: null, master: null };

  Sfx.muted = function () {
    try { return localStorage.getItem('blockhaven.crates.mute') === '1'; } catch (e) { return false; }
  };
  Sfx.setMuted = function (on) {
    try { localStorage.setItem('blockhaven.crates.mute', on ? '1' : '0'); } catch (e) {}
    if (Sfx.master) Sfx.master.gain.value = on ? 0 : 0.42;
  };
  Sfx.init = function () {
    if (Sfx.ctx) {
      if (Sfx.ctx.state === 'suspended') Sfx.ctx.resume();
      return Sfx.ctx;
    }
    var AC = global.AudioContext || global.webkitAudioContext;
    if (!AC) return null;
    try {
      Sfx.ctx = new AC();
      Sfx.master = Sfx.ctx.createGain();
      Sfx.master.gain.value = Sfx.muted() ? 0 : 0.42;
      Sfx.master.connect(Sfx.ctx.destination);
    } catch (e) { Sfx.ctx = null; }
    return Sfx.ctx;
  };
  Sfx.tone = function (freq, dur, opts) {
    var ctx = Sfx.ctx; if (!ctx) return;
    opts = opts || {};
    var t0 = ctx.currentTime + (opts.delay || 0);
    var osc = ctx.createOscillator(), gain = ctx.createGain();
    osc.type = opts.type || 'sine';
    osc.frequency.setValueAtTime(freq, t0);
    if (opts.to) osc.frequency.exponentialRampToValueAtTime(Math.max(20, opts.to), t0 + dur);
    if (opts.vibrato) {
      var lfo = ctx.createOscillator(), depth = ctx.createGain();
      lfo.frequency.value = opts.vibrato; depth.gain.value = freq * 0.03;
      lfo.connect(depth); depth.connect(osc.frequency); lfo.start(t0); lfo.stop(t0 + dur);
    }
    var vol = opts.vol === undefined ? 0.3 : opts.vol;
    gain.gain.setValueAtTime(0.0001, t0);
    gain.gain.exponentialRampToValueAtTime(vol, t0 + (opts.attack || 0.01));
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    osc.connect(gain); gain.connect(Sfx.master);
    osc.start(t0); osc.stop(t0 + dur + 0.05);
  };
  Sfx.noise = function (dur, opts) {
    var ctx = Sfx.ctx; if (!ctx) return;
    opts = opts || {};
    var t0 = ctx.currentTime + (opts.delay || 0);
    var len = Math.max(1, Math.floor(ctx.sampleRate * dur));
    var buffer = ctx.createBuffer(1, len, ctx.sampleRate);
    var data = buffer.getChannelData(0);
    for (var i = 0; i < len; i++) data[i] = Math.random() * 2 - 1;
    var src = ctx.createBufferSource(); src.buffer = buffer;
    var filter = ctx.createBiquadFilter();
    filter.type = opts.filter || 'bandpass';
    filter.frequency.setValueAtTime(opts.freq || 1200, t0);
    if (opts.to) filter.frequency.exponentialRampToValueAtTime(opts.to, t0 + dur);
    filter.Q.value = opts.q || 1.2;
    var gain = ctx.createGain();
    var vol = opts.vol === undefined ? 0.3 : opts.vol;
    gain.gain.setValueAtTime(0.0001, t0);
    gain.gain.exponentialRampToValueAtTime(vol, t0 + (opts.attack || 0.01));
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    src.connect(filter); filter.connect(gain); gain.connect(Sfx.master);
    src.start(t0); src.stop(t0 + dur + 0.05);
  };
  Sfx.play = function (name, opts) {
    if (!Sfx.ctx) return;
    opts = opts || {};
    var spooky = opts.theme === 'halloween';
    switch (name) {
      case 'drop':
        Sfx.tone(140, 0.35, { type: 'sine', to: 60, vol: 0.5 });
        Sfx.noise(0.18, { freq: 400, vol: 0.25, filter: 'lowpass' });
        break;
      case 'whoosh':
        Sfx.noise(0.6, { freq: 300, to: 2600, q: 0.8, vol: 0.22, attack: 0.25 });
        Sfx.tone(spooky ? 880 : 1320, 0.5, { type: 'triangle', vol: 0.06, delay: 0.45 });
        break;
      case 'insert':
        Sfx.noise(0.08, { freq: 3200, q: 3, vol: 0.25 });
        Sfx.tone(520, 0.12, { type: 'square', vol: 0.05 });
        break;
      case 'turn':
        Sfx.noise(0.07, { freq: 2200, q: 4, vol: 0.35 });
        Sfx.noise(0.09, { freq: 900, q: 3, vol: 0.4, delay: 0.12 });
        Sfx.tone(spooky ? 98 : 130, 0.4, { type: 'sine', vol: 0.4, delay: 0.12 });
        break;
      case 'rattle':
        for (var r = 0; r < 6; r++) {
          Sfx.noise(0.05, { freq: 600 + Math.random() * 900, q: 2, vol: 0.18 + r * 0.03,
                            delay: r * (0.16 - r * 0.012) });
        }
        if (spooky) Sfx.tone(330, 1.0, { type: 'sine', to: 220, vol: 0.1, vibrato: 6, attack: 0.3 });
        break;
      case 'open':
        Sfx.tone(spooky ? 70 : 90, 0.9, { type: 'sine', to: 38, vol: 0.6 });
        Sfx.noise(0.7, { freq: 2400, to: 300, q: 0.6, vol: 0.35, filter: 'lowpass' });
        Sfx.tone(spooky ? 523 : 784, 0.9, { type: 'triangle', vol: 0.1, delay: 0.05 });
        if (spooky) Sfx.tone(392, 1.6, { type: 'sine', to: 196, vol: 0.12, vibrato: 7, delay: 0.1 });
        break;
      case 'tick':
        Sfx.tone(opts.pitch || 1600, 0.035, { type: 'square', vol: 0.07, attack: 0.002 });
        break;
      case 'reveal':
        var chord = {
          common: [392, 494, 587], uncommon: [440, 554, 659], rare: [523, 659, 784],
          legendary: [587, 740, 880, 1175], mythic: [659, 831, 988, 1319],
          unusual: [523, 659, 784, 1047, 1319, 1568]
        }[opts.grade] || [440, 554, 659];
        chord.forEach(function (f, i) {
          Sfx.tone(f, 1.4, { type: i % 2 ? 'triangle' : 'sine', vol: 0.12,
                             delay: (opts.grade === 'unusual' || opts.grade === 'mythic') ? i * 0.07 : 0 });
        });
        if (opts.grade === 'unusual' || opts.grade === 'mythic' || opts.grade === 'legendary') {
          Sfx.noise(1.6, { freq: 6000, q: 0.5, vol: 0.06, attack: 0.4 });
        }
        break;
      case 'coin':
        Sfx.tone(1568, 0.12, { type: 'square', vol: 0.05 });
        Sfx.tone(2093, 0.2, { type: 'square', vol: 0.05, delay: 0.07 });
        break;
    }
  };
  Crates.sfx = Sfx;

  // ========================================================= the catalogue
  function catalogue() {
    return global.Thumbs ? Thumbs.loadCatalog() : Promise.resolve({});
  }
  function itemOf(id) { return (global.Thumbs && Thumbs.catalog && Thumbs.catalog[id]) || null; }

  // ============================================================== contents
  var contentsCache = {};

  Crates.showContents = function (series) {
    var got = contentsCache[series]
      ? Promise.resolve(contentsCache[series])
      : Site.get('/api/crates/contents?series=' + encodeURIComponent(series)).then(function (res) {
        if (res.ok) contentsCache[series] = res;
        return res;
      });
    return got.then(function (res) {
      if (!res || !res.ok) { Site.toast((res && res.error) || 'Could not open that list.', 'bad'); return; }
      var s = res.series;
      var bar = res.grades.map(function (g) {
        return '<i style="flex:' + g.chance + ';background:' + g.color + '" title="' +
          esc(g.label) + ' ' + g.chance + '%"></i>';
      }).join('');
      var key = res.grades.map(function (g) {
        return '<span><b style="background:' + g.color + '"></b>' + esc(g.label) + ' ' + g.chance + '%</span>';
      }).join('');
      var tiles = res.items.map(function (it) {
        return '<div class="cc-item" style="--g:' + it.color + '">' +
          '<canvas class="item-thumb" width="140" height="140" data-item="' + esc(it.item_id) + '"></canvas>' +
          '<b>' + esc(it.name) + '</b>' +
          '<span>' + esc(it.grade_label) + ' &bull; ' + esc(it.slot_label) + '</span>' +
          '<em>' + it.chance.toFixed(it.chance < 1 ? 2 : 1) + '%</em>' +
          (it.unusual_capable ? '<i class="cc-star" title="Can come out Unusual">&#9733;</i>' : '') +
          '</div>';
      }).join('');
      var fx = res.effects.map(function (e) {
        return '<span class="pill purple">' + esc(e.name) + '</span>';
      }).join(' ');
      var held = (Crates.stash || {})[series] || { crates: 0, keys: 0 };
      var body =
        '<div class="cc theme-' + esc(s.theme) + '" style="--accent:' + s.colors.accent + '">' +
        '<div class="cc-head"><canvas class="item-thumb" width="180" height="180" data-item="' +
        esc(s.crate) + '"></canvas><div><small>Series #' + s.number + '</small>' +
        '<h3>' + esc(s.name) + '</h3><p>' + esc(s.tagline) + '</p>' +
        '<p class="tiny">Opens with a <b>' + esc(s.key_name) + '</b>.</p></div></div>' +
        '<div class="mk-oddsbar big">' + bar + '</div><div class="mk-oddskey">' + key + '</div>' +
        '<div class="cc-grid">' + tiles + '</div>' +
        '<div class="cc-unusual"><b>&#9733; ' + res.unusual_chance + '% Unusual</b> &mdash; any hat out of ' +
        'this crate can come with a permanent effect. One of these:<div>' + fx + '</div></div>' +
        '</div>';
      var canOpen = held.crates > 0 && held.keys > 0;
      return Site.dialog({
        title: 'Inside the ' + s.name, tone: 'purple', bodyHtml: body, centered: true,
        confirm: canOpen ? 'Open one now' : 'Close', cancel: canOpen ? 'Later' : null
      }).then(function (yes) {
        if (yes && canOpen) Crates.open({ series: series });
      });
    });
  };

  // ================================================================ buying
  function coinShower(from) {
    var wallet = document.getElementById('mk-wallet') || document.getElementById('wallet-amount');
    if (!from || !wallet || reduced()) return;
    var a = from.getBoundingClientRect(), b = wallet.getBoundingClientRect();
    for (var i = 0; i < 9; i++) {
      (function (i) {
        var coin = document.createElement('span');
        coin.className = 'flying-coin';
        coin.style.left = (a.left + a.width / 2) + 'px';
        coin.style.top = (a.top + a.height / 2) + 'px';
        document.body.appendChild(coin);
        var dx = b.left + b.width / 2 - (a.left + a.width / 2);
        var dy = b.top + b.height / 2 - (a.top + a.height / 2);
        var arc = -80 - Math.random() * 90;
        var start = performance.now() + i * 45;
        function step(now) {
          var t = clamp((now - start) / 620, 0, 1);
          var e = easeInOut(t);
          coin.style.transform = 'translate(' + (dx * e + (Math.random() - 0.5) * 2) + 'px,' +
            (dy * e + arc * Math.sin(Math.PI * t)) + 'px) rotate(' + (t * 720) + 'deg) scale(' +
            (1 - t * 0.4) + ')';
          coin.style.opacity = t > 0.92 ? String(1 - (t - 0.92) / 0.08) : '1';
          if (t < 1) requestAnimationFrame(step);
          else coin.remove();
        }
        requestAnimationFrame(step);
      })(i);
    }
    setTimeout(function () {
      wallet.classList.remove('bump'); void wallet.offsetWidth; wallet.classList.add('bump');
    }, 600);
  }
  Crates.coinShower = coinShower;

  function countTo(node, target) {
    if (!node) return;
    var from = parseInt(String(node.textContent).replace(/[^0-9]/g, ''), 10) || 0;
    var start = performance.now();
    function step(now) {
      var t = clamp((now - start) / 700, 0, 1);
      node.textContent = num(Math.round(lerp(from, target, easeOut(t))));
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  /* Other pages can borrow a sound: the inventory turns its key with it. */
  Crates.sfx = function (name, opts) { Sfx.init(); Sfx.play(name, opts || {}); };

  Crates.setBalance = function (balance) {
    countTo(document.getElementById('wallet-amount'), balance);
    countTo(document.getElementById('mk-wallet'), balance);
    countTo(document.getElementById('wallet-big'), balance);
    if (global.BH && BH.user) BH.user.credits = balance;
  };

  Crates.setStash = function (stash) {
    if (!stash) return;
    Crates.stash = stash;
    Object.keys(stash).forEach(function (series) {
      var row = document.querySelector('.mk-stash-row[data-series="' + series + '"]');
      if (!row) return;
      var held = stash[series];
      ['crates', 'keys'].forEach(function (k) {
        var n = row.querySelector('[data-count="' + k + '"]');
        if (n && n.textContent !== String(held[k])) {
          n.textContent = held[k];
          n.classList.remove('pop'); void n.offsetWidth; n.classList.add('pop');
        }
      });
      var open = row.querySelector('[data-open-series]');
      if (open) open.classList.toggle('hidden', !(held.crates > 0 && held.keys > 0));
    });
    document.dispatchEvent(new CustomEvent('crates:stash', { detail: stash }));
  };

  /* Buy what a button describes: a key or crate (with a quantity), any other
     item, or a bundle.  Confirms in the site's own dialog with a live,
     turning preview of the thing, then rains coins into the wallet. */
  Crates.buy = function (button) {
    var itemId = button.dataset.buy, offer = button.dataset.offer;
    var price = parseInt(button.dataset.price, 10) || 0;
    var qty = 1;
    var qtyBox = itemId && document.querySelector('[data-qty-for="' + itemId + '"] input');
    if (button.dataset.stack === '1' && qtyBox) qty = clamp(parseInt(qtyBox.value, 10) || 1, 1, 10);
    var name = button.dataset.name || 'this';
    var total = price * qty;
    var balance = (global.BH && BH.user && BH.user.credits) || 0;
    var wallet = document.getElementById('wallet-amount');
    if (wallet) balance = parseInt(wallet.textContent.replace(/[^0-9]/g, ''), 10) || balance;
    var preview = itemId || (offer && button.closest('.mk-offer') &&
                              button.closest('.mk-offer').querySelector('canvas').dataset.item);
    var body =
      '<div class="buy-sheet">' +
      '<div class="buy-art"><canvas id="buy-spin" width="300" height="300"></canvas></div>' +
      '<div class="buy-info"><b>' + esc(name) + '</b>' +
      (qty > 1 ? '<span class="buy-qty">&times; ' + qty + '</span>' : '') +
      '<div class="buy-math"><span>Price</span><span><span class="coin"></span> ' + num(total) + '</span>' +
      '<span>Your Noogets</span><span>' + num(balance) + '</span>' +
      '<span>After</span><span class="' + (balance < total ? 'short' : '') + '">' +
      num(balance - total) + '</span></div>' +
      (balance < total ? '<p class="tiny" style="color:var(--bad-ink)">You are ' + num(total - balance) +
        ' Noogets short.</p>' : '') +
      (button.dataset.slot === 'crate' ? '<p class="tiny muted">Crates need a matching key to open.</p>' : '') +
      (button.dataset.slot === 'key' ? '<p class="tiny muted">One key opens one crate, then it is used up.</p>' : '') +
      '</div></div>';
    var spin = null;
    var dialog = Site.dialog({
      title: offer ? 'Grab this bundle?' : 'Buy ' + (qty > 1 ? qty + ' of these' : 'this') + '?',
      tone: 'gold', bodyHtml: body, confirm: balance < total ? 'Try anyway' : 'Buy it',
      cancel: 'Not now', centered: true,
      onClose: function () { if (spin && global.Thumbs) Thumbs.stopLive(spin); }
    });
    setTimeout(function () {
      spin = document.getElementById('buy-spin');
      if (spin && preview && global.Thumbs) Thumbs.animateItem(spin, preview, '', { spin: 0.9 });
    }, 30);
    return dialog.then(function (yes) {
      if (!yes) return null;
      Sfx.init();
      button.disabled = true;
      button.classList.add('busy');
      var request = offer
        ? Site.post('/api/market/bundle', { offer_id: offer })
        : Site.post('/api/market/buy', { item_id: itemId, qty: qty });
      return request.then(function (res) {
        button.disabled = false;
        button.classList.remove('busy');
        if (!res.ok) { Site.toast(res.error, 'bad'); return null; }
        Sfx.play('coin');
        coinShower(button);
        Crates.setBalance(res.balance);
        if (res.stash) Crates.setStash(res.stash);
        if (res.owned !== undefined) {
          document.querySelectorAll('[data-owned="' + itemId + '"]').forEach(function (flag) {
            flag.classList.remove('hidden');
            flag.textContent = 'x' + res.owned;
            flag.classList.remove('pop'); void flag.offsetWidth; flag.classList.add('pop');
          });
        }
        var stash = res.stash || Crates.stash || {};
        var ready = Object.keys(stash).filter(function (k) {
          return stash[k].crates > 0 && stash[k].keys > 0;
        });
        if (ready.length && (offer || button.dataset.slot === 'crate' || button.dataset.slot === 'key')) {
          var series = offer ? button.dataset.series :
            (ready.indexOf(button.dataset.series) >= 0 ? button.dataset.series : ready[0]);
          Crates.prompt(series || ready[0]);
        } else {
          Site.toast((qty > 1 ? qty + ' x ' : '') + name + ' is yours!' +
                     (button.dataset.slot === 'crate' ? ' Now grab a key.' :
                      button.dataset.slot === 'key' ? ' Now grab a crate.' : ''));
        }
        return res;
      });
    });
  };

  /* "You have a crate and a key -- open it?" as a little card that slides in
     at the bottom of the screen, rather than another dialog in the way. */
  Crates.prompt = function (series) {
    var old = document.getElementById('crate-ready');
    if (old) old.remove();
    var card = document.createElement('div');
    card.id = 'crate-ready';
    card.className = 'crate-ready theme-' + series;
    var info = (global.CRATE_SERIES || {})[series] || {};
    card.innerHTML =
      '<canvas class="item-thumb" width="120" height="120" data-item="' + esc(info.crate || '') + '"></canvas>' +
      '<div><b>Ready to open!</b><span>You have a crate and the key for it.</span></div>' +
      '<button class="mk-btn hot small" type="button"><span>&#128275; Open it</span></button>' +
      '<button class="crate-ready-x" type="button" aria-label="Later">&times;</button>';
    document.body.appendChild(card);
    if (global.Thumbs) Thumbs.rescan();
    requestAnimationFrame(function () { card.classList.add('in'); });
    card.querySelector('.mk-btn').addEventListener('click', function () {
      card.remove();
      Crates.open({ series: series });
    });
    card.querySelector('.crate-ready-x').addEventListener('click', function () { card.remove(); });
    setTimeout(function () { if (card.isConnected) card.classList.add('nudge'); }, 3500);
  };

  // ============================================================ the stage
  /* Matrix helpers matching the renderer's euler order (R = Ry * Rx * Rz),
     column major, so a whole model can be turned, swung and shaken and still
     hand the renderer plain {p, s, r} parts. */
  function eulerMat(r) {
    r = r || [0, 0, 0];
    var cx = Math.cos(r[0]), sx = Math.sin(r[0]), cy = Math.cos(r[1]), sy = Math.sin(r[1]);
    var cz = Math.cos(r[2]), sz = Math.sin(r[2]);
    return [cy * cz + sy * sx * sz, cx * sz, -sy * cz + cy * sx * sz,
            -cy * sz + sy * sx * cz, cx * cz, sy * sz + cy * sx * cz,
            sy * cx, -sx, cy * cx];
  }
  function mul(a, b) {
    var o = new Array(9);
    for (var c = 0; c < 3; c++) {
      for (var r = 0; r < 3; r++) {
        o[c * 3 + r] = a[r] * b[c * 3] + a[3 + r] * b[c * 3 + 1] + a[6 + r] * b[c * 3 + 2];
      }
    }
    return o;
  }
  function apply(m, v) {
    return [m[0] * v[0] + m[3] * v[1] + m[6] * v[2],
            m[1] * v[0] + m[4] * v[1] + m[7] * v[2],
            m[2] * v[0] + m[5] * v[1] + m[8] * v[2]];
  }
  function toEuler(m) {
    var rx = Math.asin(clamp(-m[7], -1, 1));
    return [rx, Math.atan2(m[6], m[8]), Math.atan2(m[1], m[4])];
  }
  function rotX(a) { return eulerMat([a, 0, 0]); }

  /* Copy a model's parts through a transform: ``pre`` (optional) acts on the
     parts flagged ``lid`` about ``hinge`` first, then scale ``k``, rotation
     ``rot`` and translation ``at`` act on everything. */
  function transform(parts, at, rot, k, lidAngle, hinge, glow) {
    var R = eulerMat(rot);
    var L = lidAngle ? rotX(lidAngle) : null;
    var out = [];
    for (var i = 0; i < parts.length; i++) {
      var q = parts[i];
      var p = q.p, m = eulerMat(q.r);
      if (L && q.lid) {
        var rel = [p[0] - hinge[0], p[1] - hinge[1], p[2] - hinge[2]];
        var turned = apply(L, rel);
        p = [hinge[0] + turned[0], hinge[1] + turned[1], hinge[2] + turned[2]];
        m = mul(L, m);
      }
      var wp = apply(R, [p[0] * k, p[1] * k, p[2] * k]);
      var part = {
        t: q.t || 'box', p: [at[0] + wp[0], at[1] + wp[1], at[2] + wp[2]],
        s: [q.s[0] * k, q.s[1] * k, q.s[2] * k], c: q.c, r: toEuler(mul(R, m)),
        m: q.m, a: q.a, dw: q.dw, decSlot: q.decSlot
      };
      if (glow && q.m === 'neon' && !q.lid) part.a = glow;
      out.push(part);
    }
    return out;
  }

  function modelParts(item) {
    return ((item && item.data && item.data.parts) || []).map(function (q) {
      return { t: q.t, p: q.p, s: q.s, c: q.c, r: q.r, m: q.m, a: q.a, dw: q.dw, lid: q.lid,
               lock: q.lock, decSlot: q.decal ? Textures.decal(q.decal) : null };
    });
  }

  function lockPoint(parts) {
    for (var i = 0; i < parts.length; i++) {
      if (parts[i].lock) return parts[i].p.slice();
    }
    return [0, 0.1, 0.6];
  }

  var THEMES = {
    classic: {
      sky: { top: '#2b1a0c', horizon: '#6a4320', sun: [0.3, 0.9, 0.5], clouds: 0, tint: '#ffd9a0' },
      ambient: '#8a6a48',
      burst: ['#fff3b0', '#ffd24a', '#ffae19', '#ffffff'],
      shapes: ['star', 'spark', 'star', 'ray'],
      pieces: [{ shape: 'star', colors: ['#fff3b0', '#ffd24a', '#ffae19'], blend: 'add' },
               { shape: 'spark', colors: ['#ffffff', '#ffe08a'], blend: 'add' },
               { shape: 'ray', colors: ['#fff6c9', '#ffd75e'], blend: 'add' }],
      seep: 'sunbeam', after: 'starstruck',
      beam: '#ffe9a8'
    },
    halloween: {
      sky: { top: '#0c0716', horizon: '#2b1640', sun: [0.2, 0.9, 0.6], clouds: 0, tint: '#b6a0ff' },
      ambient: '#6a5c96',
      burst: ['#6bff9a', '#c78bff', '#ff9a2e', '#ffffff'],
      shapes: ['ghost', 'bat', 'candycorn', 'wisp', 'pumpkin'],
      // each kind of thing that flies out keeps colours that make it what it
      // is: white ghosts, black bats, orange lanterns, green wisps
      pieces: [{ shape: 'ghost', colors: ['#ffffff', '#e9f4ff', '#c9e2ff'], blend: 'normal' },
               { shape: 'bat', colors: ['#3a2a55', '#1d1830', '#443a66'], blend: 'normal' },
               { shape: 'pumpkin', colors: ['#ffb347', '#ff8c1a', '#e8631a'], blend: 'normal' },
               { shape: 'candycorn', colors: ['#ffe08a', '#ffffff', '#ffb347'], blend: 'normal' },
               { shape: 'wisp', colors: ['#b8ffd2', '#6bff9a', '#2ea98a'], blend: 'add' }],
      seep: 'haunted_wisps', after: 'phantom_procession',
      beam: '#6bff9a'
    }
  };

  function Stage(options) {
    this.options = options;
    this.series = options.series;
    this.theme = THEMES[options.theme] ? options.theme : 'classic';
    this.T = THEMES[this.theme];
    this.skipped = false;
    this.done = false;
    this.phase = 'intro';
    this.t = 0;
    this.build();
  }

  Stage.prototype.build = function () {
    var self = this;
    var root = document.createElement('div');
    root.className = 'cs-stage theme-' + this.theme;
    root.innerHTML =
      '<div class="cs-bg"><i class="cs-rays"></i><i class="cs-moon"></i><i class="cs-stars"></i>' +
      '<i class="cs-fog a"></i><i class="cs-fog b"></i><i class="cs-vignette"></i>' +
      '<span class="cs-bats"><b></b><b></b><b></b><b></b></span></div>' +
      '<canvas class="cs-gl"></canvas>' +
      '<div class="cs-title"><small></small><b></b></div>' +
      '<div class="cs-reel"><div class="cs-reel-window"><div class="cs-reel-track"></div></div>' +
      '<div class="cs-marker"><i></i></div></div>' +
      '<div class="cs-reveal"></div>' +
      '<div class="cs-flash"></div>' +
      '<div class="cs-tools"><button type="button" class="cs-mute" title="Sound"></button>' +
      '<button type="button" class="cs-skip">Skip &#9654;&#9654;</button></div>';
    document.body.appendChild(root);
    document.body.classList.add('cs-open');
    this.root = root;
    this.canvas = root.querySelector('.cs-gl');
    this.track = root.querySelector('.cs-reel-track');
    this.reelBox = root.querySelector('.cs-reel');
    this.revealBox = root.querySelector('.cs-reveal');
    this.flashBox = root.querySelector('.cs-flash');
    this.titleBox = root.querySelector('.cs-title');
    var mute = root.querySelector('.cs-mute');
    function paintMute() { mute.innerHTML = Sfx.muted() ? '&#128263;' : '&#128266;'; }
    paintMute();
    mute.addEventListener('click', function () { Sfx.setMuted(!Sfx.muted()); paintMute(); });
    root.querySelector('.cs-skip').addEventListener('click', function () { self.skip(); });
    this.onKey = function (e) {
      if (e.key === 'Escape' || e.key === ' ') {
        e.preventDefault();
        if (self.phase === 'reveal') self.close(); else self.skip();
      }
    };
    document.addEventListener('keydown', this.onKey);
    requestAnimationFrame(function () { root.classList.add('in'); });

    // the 3D scene
    this.renderer = new Renderer(this.canvas, { antialias: true, transparent: true });
    if (this.renderer.failed) { this.renderer = null; return; }
    this.renderer.far = 600;
    this.renderer.setSky(this.T.sky);
    this.renderer.setAmbient(this.T.ambient);
    this.particles = new Particles(this.renderer.gl);
  };

  Stage.prototype.setTitle = function (small, big) {
    this.titleBox.querySelector('small').textContent = small || '';
    this.titleBox.querySelector('b').textContent = big || '';
  };

  Stage.prototype.flash = function (colour, strength) {
    var f = this.flashBox;
    f.style.background = colour || '#ffffff';
    f.style.setProperty('--o', String(strength === undefined ? 0.85 : strength));
    f.classList.remove('go'); void f.offsetWidth; f.classList.add('go');
  };

  Stage.prototype.shakeScreen = function (big) {
    this.root.classList.remove('shake', 'shake-big'); void this.root.offsetWidth;
    this.root.classList.add(big ? 'shake-big' : 'shake');
  };

  Stage.prototype.burst = function (at, count, power) {
    if (!this.particles) return;
    var T = this.T;
    for (var i = 0; i < count; i++) {
      var a = Math.random() * TAU, up = 0.4 + Math.random();
      var sp = power * (0.4 + Math.random() * 0.8);
      var piece = T.pieces[(Math.random() * T.pieces.length) | 0];
      this.particles.spawn({
        p: [at[0] + (Math.random() - 0.5) * 0.6, at[1], at[2] + (Math.random() - 0.5) * 0.4],
        v: [Math.cos(a) * sp, up * power * 1.4, Math.sin(a) * sp * 0.7],
        life: 0.9 + Math.random() * 1.1, size: 0.18 + Math.random() * 0.26, grow: -0.05,
        gravity: -3.2, spin: 4, blend: piece.blend,
        shape: piece.shape, colors: piece.colors, upright: true, wobble: 0.6
      });
    }
  };

  /* The scene for this frame: the crate, the key, the glow. */
  Stage.prototype.draw = function (dt) {
    var r = this.renderer;
    if (!r) return;
    r.resize();
    r.beginFrame(dt);
    var t = this.t;
    var s = this.scene;
    // the crate: drops in, bobs, shakes, and its lid swings open
    var drop = s.dropT === undefined ? 1 : clamp(s.dropT, 0, 1);
    var y = lerp(5.5, 0, easeOutBack(drop));
    var shake = s.shake || 0;
    var at = [Math.sin(t * 43) * 0.05 * shake, y + Math.sin(t * 1.7) * 0.04 + Math.abs(Math.sin(t * 37)) * 0.04 * shake,
              Math.cos(t * 31) * 0.03 * shake];
    var yaw = s.yaw + Math.sin(t * 0.9) * 0.06 + Math.sin(t * 29) * 0.05 * shake;
    var parts = transform(this.crateParts, at, [Math.sin(t * 23) * 0.03 * shake, yaw, Math.sin(t * 27) * 0.04 * shake],
                          1.25, -(s.lid || 0), this.hinge, s.seam);
    for (var i = 0; i < parts.length; i++) r.push(parts[i]);
    // the key
    if (s.key) {
      var kp = transform(this.keyParts, s.key.at, s.key.rot, s.key.k);
      for (var j = 0; j < kp.length; j++) r.push(kp[j]);
    }
    // a column of light once the lid is up
    if (s.beam) {
      var b = s.beam;
      r.pushRaw('cyl', 0, 1.0 + 3.0 * b, 0, 0, 0, 0, 1.3 * b + 0.3, 6.0 * b, 1.0 * b + 0.3,
                GLX.mat.hexToRgb(this.T.beam), 0.22 * b, 0, 2, 0, null);
      r.pushRaw('cyl', 0, 1.0 + 3.0 * b, 0, 0, 0, 0, 0.6 * b + 0.1, 6.4 * b, 0.5 * b + 0.1,
                [1, 1, 1], 0.28 * b, 0, 2, 0, null);
    }
    var eye = [2.6, 2.3, 5.6];
    var look = [0, 0.55, 0];
    r.setCameraMatrix(eye, look, 40);
    if (this.particles) {
      if (s.seep && Thumbs.effects && Thumbs.effects[this.T.seep]) {
        this.particles.setEmitter('seep', Thumbs.scaleEffect(Thumbs.effects[this.T.seep], 1.2),
                                  [0, 0.8 + at[1], 0]);
      } else this.particles.clearEmitter('seep');
      this.particles.update(dt);
    }
    r.render();
    if (this.particles) this.particles.draw(r);
  };

  /* Run the whole show.  ``result`` is a promise of the server's answer. */
  Stage.prototype.run = function (crateItem, keyItem, result) {
    var self = this;
    this.crateParts = modelParts(crateItem);
    this.keyParts = modelParts(keyItem);
    var hinge = (crateItem.data && crateItem.data.hinge) || [0, 0.5, -0.55];
    this.hinge = hinge;
    var lock = lockPoint(this.crateParts);
    this.scene = { yaw: -0.38, dropT: 0, lid: 0, shake: 0, seam: undefined };
    this.setTitle(this.theme === 'halloween' ? 'Something stirs inside...' : 'Unlocking',
                  crateItem.name);
    Sfx.init();
    var answer = null, failed = null;
    result.then(function (res) {
      if (res && res.ok) answer = res; else failed = (res && res.error) || 'The crate would not open.';
    }, function () { failed = 'Lost the connection to the server.'; });

    // where the lock is in world space at rest
    function lockWorld() {
      var R = eulerMat([0, self.scene.yaw, 0]);
      var w = apply(R, [lock[0] * 1.25, lock[1] * 1.25, lock[2] * 1.25]);
      return w;
    }

    var timeline = [
      // [start, end, fn(progress)]
      [0.0, 0.9, function (p) {
        self.scene.dropT = p;
        if (p >= 1 && !self._landed) { self._landed = 1; Sfx.play('drop'); self.shakeScreen(false);
          self.burst([0, 0.1, 0], 14, 2.2); }
      }],
      [0.9, 2.0, function (p) {
        if (!self._whoosh) { self._whoosh = 1; Sfx.play('whoosh', { theme: self.theme }); }
        var L = lockWorld();
        var e = easeInOut(p);
        var from = [4.2, 3.2, 3.6];
        var aim = [L[0] + 0.0, L[1], L[2] + 1.05];
        var mid = [2.2, 3.4, 3.0];
        var u = 1 - e;
        var pos = [u * u * from[0] + 2 * u * e * mid[0] + e * e * aim[0],
                   u * u * from[1] + 2 * u * e * mid[1] + e * e * aim[1],
                   u * u * from[2] + 2 * u * e * mid[2] + e * e * aim[2]];
        self.scene.key = { at: pos, rot: [lerp(4.0, 0, e), self.scene.yaw + Math.PI / 2 + lerp(2.6, 0, e), 0],
                           k: lerp(0.4, 0.95, e) };
        if (self.particles && Math.random() < 0.9) {
          self.particles.spawn({ p: pos, v: [0, 0.2, 0], life: 0.5, size: 0.22, grow: -0.3, gravity: 0,
            spin: 2, blend: 'add', shape: 'spark', colors: self.T.burst });
        }
      }],
      [2.0, 2.35, function (p) {
        var L = lockWorld();
        if (!self._insert) { self._insert = 1; Sfx.play('insert'); }
        var dir = apply(eulerMat([0, self.scene.yaw, 0]), [0, 0, 1]);
        var d = lerp(1.05, 0.62, easeOut(p));
        self.scene.key = { at: [L[0] + dir[0] * d, L[1], L[2] + dir[2] * d],
                           rot: [0, self.scene.yaw + Math.PI / 2, 0], k: 0.95 };
      }],
      [2.35, 2.75, function (p) {
        var L = lockWorld();
        var dir = apply(eulerMat([0, self.scene.yaw, 0]), [0, 0, 1]);
        self.scene.key = { at: [L[0] + dir[0] * 0.62, L[1], L[2] + dir[2] * 0.62],
                           rot: [easeOutBack(p) * Math.PI / 2, self.scene.yaw + Math.PI / 2, 0], k: 0.95 };
        if (p >= 0.6 && !self._turn) {
          self._turn = 1; Sfx.play('turn', { theme: self.theme });
          self.flash(self.T.beam, 0.25);
          self.burst(L, 10, 1.2);
        }
      }],
      [2.75, 3.9, function (p) {
        self.scene.shake = 0.2 + p * 1.1;
        self.scene.seam = 0.6 + 0.4 * Math.sin(p * 30);
        self.scene.seep = p > 0.25;
        if (!self._rattle) {
          self._rattle = 1; Sfx.play('rattle', { theme: self.theme });
          self.setTitle(self.theme === 'halloween' ? 'It is trying to get out...' : 'Here it comes...',
                        crateItem.name);
        }
        // the key fades as the lock lets go
        if (p > 0.7) self.scene.key = null;
      }]
    ];

    var last = performance.now();
    var waitStart = 0;
    function frame(now) {
      if (self.done) return;
      var dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      self.t += dt;
      if (self.phase === 'intro') {
        var t = self.t;
        timeline.forEach(function (step) {
          if (t >= step[0]) step[2](clamp((t - step[0]) / (step[1] - step[0]), 0, 1));
        });
        if (failed) { self.fail(failed); return; }
        if (t >= 3.9) {
          if (!answer) {
            // the server is slow: the crate keeps straining until it answers
            if (!waitStart) waitStart = t;
            self.scene.shake = 1.2 + Math.sin(t * 9) * 0.2;
          } else {
            self.phase = 'opening';
            self.openAt = t;
          }
        }
        if (self.skipped && answer) { self.phase = 'opening'; self.openAt = t; }
      }
      if (self.phase === 'opening') {
        var q = clamp((self.t - self.openAt) / 0.6, 0, 1);
        if (!self._boom) {
          self._boom = 1;
          self.scene.shake = 0; self.scene.seep = false; self.scene.key = null;
          Sfx.play('open', { theme: self.theme });
          self.flash('#ffffff', 0.9);
          self.shakeScreen(true);
          self.burst([0, 1.1, 0], 70, 3.4);
          if (self.particles && Thumbs.effects && Thumbs.effects[self.T.after]) {
            self.particles.setEmitter('after', Thumbs.scaleEffect(Thumbs.effects[self.T.after], 1.3),
                                      [0, 1.4, 0]);
          }
        }
        self.scene.lid = easeOutBack(q) * 1.95;
        self.scene.beam = easeOut(q);
        if (q >= 1 && !self._reel) {
          self._reel = 1;
          self.startReel(answer);
        }
      }
      if (self.phase === 'reel') self.stepReel(now);
      if (self.phase !== 'reveal' || self.revealSpin) self.draw(dt);
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  };

  Stage.prototype.skip = function () {
    this.skipped = true;
    Sfx.init();
    if (this.phase === 'reel') this.finishReel();
  };

  // --------------------------------------------------------------- reel
  var TILE = 132;     // tile width + gap, px

  Stage.prototype.startReel = function (answer) {
    var self = this;
    this.answer = answer;
    this.phase = 'reel';
    this.setTitle('Rolling...', answer.series.name);
    var html = answer.reel.map(function (tile, i) {
      var colour = GRADE_COLORS[tile.grade] || '#9fb0c2';
      if (tile.mystery) {
        return '<div class="cs-tile mystery" style="--g:' + colour + '"><span>&#9733;</span><em>?</em>' +
          '<b>Unusual</b></div>';
      }
      var item = itemOf(tile.item_id) || {};
      return '<div class="cs-tile' + (i === answer.win_index ? ' win' : '') + '" style="--g:' + colour + '">' +
        '<canvas width="120" height="120" data-reel="' + esc(tile.item_id) + '"></canvas>' +
        '<b>' + esc(item.name || '') + '</b></div>';
    }).join('');
    this.track.innerHTML = html;
    this.track.querySelectorAll('canvas[data-reel]').forEach(function (c) {
      if (global.Thumbs) Thumbs.renderItem(c, c.dataset.reel, '');
    });
    this.reelBox.classList.add('in');
    var windowW = this.reelBox.querySelector('.cs-reel-window').clientWidth || 800;
    var centre = windowW / 2;
    // stop somewhere inside the winning tile, not dead centre: a reel that
    // always lands perfectly reads as rigged
    var jitter = (Math.random() - 0.5) * (TILE - 40);
    this.reelTarget = answer.win_index * TILE + TILE / 2 - centre + jitter;
    this.reelOver = TILE * (0.28 + Math.random() * 0.22);   // the hook past it
    this.reelStart = performance.now();
    this.reelDur = reduced() ? 1500 : 6600;
    this.lastTile = -1;
    this.track.style.transform = 'translateX(0px)';
  };

  Stage.prototype.reelPos = function (u) {
    // fast, a long slow-down, a little past the stop, and back onto it
    var main = 0.9;
    if (u < main) {
      var v = u / main;
      return (this.reelTarget + this.reelOver) * (1 - Math.pow(1 - v, 4.2));
    }
    var w = (u - main) / (1 - main);
    return this.reelTarget + this.reelOver * (1 - easeInOut(w));
  };

  Stage.prototype.stepReel = function (now) {
    var u = clamp((now - this.reelStart) / this.reelDur, 0, 1);
    var x = this.reelPos(u);
    var speed = Math.abs(x - (this._lastX || 0));
    this._lastX = x;
    this.track.style.transform = 'translateX(' + (-x).toFixed(1) + 'px)';
    this.track.style.filter = speed > 26 ? 'blur(' + Math.min(3, (speed - 26) / 12).toFixed(1) + 'px)' : '';
    var windowW = this.reelBox.querySelector('.cs-reel-window').clientWidth || 800;
    var under = Math.floor((x + windowW / 2) / TILE);
    if (under !== this.lastTile) {
      this.lastTile = under;
      Sfx.play('tick', { pitch: 900 + Math.min(1400, speed * 30) });
      var marker = this.reelBox.querySelector('.cs-marker');
      marker.classList.remove('tick'); void marker.offsetWidth; marker.classList.add('tick');
    }
    if (u >= 1) this.finishReel();
  };

  Stage.prototype.finishReel = function () {
    if (this.phase !== 'reel') return;
    this.track.style.filter = '';
    this.track.style.transform = 'translateX(' + (-this.reelTarget).toFixed(1) + 'px)';
    var win = this.track.querySelector('.cs-tile.win');
    if (win) win.classList.add('lit');
    var self = this;
    this.phase = 'settle';
    setTimeout(function () { self.reveal(); }, this.skipped ? 80 : 650);
  };

  // ------------------------------------------------------------- reveal
  Stage.prototype.reveal = function () {
    var self = this;
    var res = this.answer;
    var it = res.item;
    var unusual = it.tier === 'unusual';
    var grade = unusual ? 'unusual' : it.grade;
    var colour = GRADE_COLORS[grade] || '#9fb0c2';
    this.phase = 'reveal';
    this.revealSpin = true;
    this.reelBox.classList.remove('in');
    this.reelBox.classList.add('out');
    this.root.classList.add('revealed', 'g-' + grade);
    this.setTitle('', '');
    var big = grade === 'unusual' || grade === 'mythic' || grade === 'legendary';
    Sfx.play('reveal', { grade: grade });
    this.flash(colour, big ? 0.95 : 0.6);
    if (big) this.shakeScreen(true);
    this.burst([0, 1.6, 0], big ? 110 : 40, big ? 4.2 : 2.6);
    var left = (res.left || {})[res.series.id] || { crates: 0, keys: 0 };
    var again = left.crates > 0 && left.keys > 0;
    var wearable = WEARABLE[it.slot];
    this.revealBox.innerHTML =
      '<div class="cs-card" style="--g:' + colour + '">' +
      '<i class="cs-card-rays"></i>' +
      (unusual ? '<div class="cs-unusual-banner">&#9733; UNUSUAL &#9733;</div>' : '') +
      '<div class="cs-card-art"><canvas id="cs-won" width="420" height="420"></canvas></div>' +
      '<div class="cs-card-grade">' + esc(GRADE_LABELS[grade] || grade) + '</div>' +
      '<h2 class="cs-card-name">' + esc(it.name) + '</h2>' +
      (unusual ? '<div class="cs-card-fx">Effect: <b>' + esc(it.effect_name) + '</b></div>' : '') +
      '<div class="cs-card-meta">' + esc(it.slot_label) + ' &bull; serial #' + num(it.serial) +
      ' &bull; from the ' + esc(res.series.name) + '</div>' +
      '<div class="cs-card-actions">' +
      (wearable ? '<button class="mk-btn hot" data-cs="wear"><span>Wear it now</span></button>' :
        (it.slot === 'usable' ? '<a class="mk-btn hot" href="/avatar#hotbar"><span>Put it on the hotbar</span></a>' : '')) +
      (again ? '<button class="mk-btn" data-cs="again"><span>&#128275; Open another (' + left.crates + ' left)</span></button>' : '') +
      '<button class="mk-btn ghost" data-cs="close"><span>Close</span></button>' +
      '</div></div>';
    if (unusual || grade === 'mythic' || grade === 'legendary') this.confetti(colour, unusual ? 90 : 50);
    requestAnimationFrame(function () { self.revealBox.classList.add('in'); });
    setTimeout(function () {
      var won = document.getElementById('cs-won');
      if (won && global.Thumbs) Thumbs.animateItem(won, it.item_id, it.effect || '', { spin: 0.7 });
    }, 40);
    // the scene dims behind the card
    setTimeout(function () { self.revealSpin = false; }, 1600);
    this.revealBox.addEventListener('click', function (e) {
      var b = e.target.closest('[data-cs]');
      if (!b) return;
      if (b.dataset.cs === 'close') self.close();
      else if (b.dataset.cs === 'again') { self.close(); Crates.open({ series: res.series.id }); }
      else if (b.dataset.cs === 'wear') {
        b.disabled = true;
        Site.post('/api/avatar/equip', { slot: it.slot, inv_id: it.inv_id }).then(function (r) {
          if (!r.ok) { Site.toast(r.error, 'bad'); b.disabled = false; return; }
          b.innerHTML = '<span>&#10003; Wearing it</span>';
          Site.toast('Equipped ' + it.name + '. Looking good.');
        });
      }
    });
    if (this.options.onResult) this.options.onResult(res);
    // every page that shows crates, keys or a feed listens for this
    document.dispatchEvent(new CustomEvent('crates:opened', { detail: res }));
    Crates.setStash(res.left);
    if (res.balance !== undefined) Crates.setBalance(res.balance);
  };

  Stage.prototype.confetti = function (colour, count) {
    if (reduced()) return;
    var box = document.createElement('div');
    box.className = 'cs-confetti';
    var colours = [colour, '#ffffff', '#ffd24a', '#b26bff', '#6bff9a'];
    for (var i = 0; i < count; i++) {
      var p = document.createElement('i');
      p.style.left = (Math.random() * 100) + '%';
      p.style.background = colours[i % colours.length];
      p.style.animationDelay = (Math.random() * 0.6) + 's';
      p.style.animationDuration = (2.2 + Math.random() * 1.8) + 's';
      p.style.setProperty('--drift', ((Math.random() - 0.5) * 240) + 'px');
      p.style.setProperty('--spin', ((Math.random() - 0.5) * 1440) + 'deg');
      box.appendChild(p);
    }
    this.root.appendChild(box);
  };

  Stage.prototype.fail = function (message) {
    this.phase = 'reveal';
    this.revealBox.innerHTML = '<div class="cs-card fail"><h2>The lock would not turn</h2><p>' + esc(message) +
      '</p><div class="cs-card-actions"><button class="mk-btn" data-cs="close"><span>Close</span></button></div></div>';
    this.revealBox.classList.add('in');
    var self = this;
    this.revealBox.addEventListener('click', function (e) {
      if (e.target.closest('[data-cs="close"]')) self.close();
    });
  };

  Stage.prototype.close = function () {
    if (this.done) return;
    this.done = true;
    var won = document.getElementById('cs-won');
    if (won && global.Thumbs) Thumbs.stopLive(won);
    document.removeEventListener('keydown', this.onKey);
    document.body.classList.remove('cs-open');
    // browsers only keep a handful of WebGL contexts alive; give this one back
    if (this.renderer && this.renderer.gl) {
      var lose = this.renderer.gl.getExtension('WEBGL_lose_context');
      var self = this;
      setTimeout(function () { if (lose) lose.loseContext(); self.renderer = null; }, 400);
    }
    var root = this.root;
    root.classList.remove('in');
    root.classList.add('leaving');
    setTimeout(function () { root.remove(); }, 380);
    if (this.options.onClose) this.options.onClose(this.answer);
  };

  /* Open a crate.  Give it the series (it will pick a crate and a key from
     what you hold) or the two inventory rows. */
  Crates.busy = false;
  Crates.open = function (options) {
    options = options || {};
    if (Crates.busy) return Promise.resolve(null);
    if (typeof Renderer === 'undefined') { Site.toast('Your browser cannot draw the crate.', 'bad'); return Promise.resolve(null); }
    Crates.busy = true;
    Sfx.init();
    var body = { series: options.series || '' };
    if (options.crateInv) body.crate_inv = options.crateInv;
    if (options.keyInv) body.key_inv = options.keyInv;
    var request = Site.post('/api/crates/open', body);
    return catalogue().then(function () {
      var series = options.series;
      var info = (global.CRATE_SERIES || {})[series] || {};
      var crateId = options.crateItem || info.crate;
      var keyId = options.keyItem || info.key;
      // the page may not know the series yet (an inventory row was clicked):
      // ask the answer, but start the show with what we can guess
      if (!crateId) crateId = series === 'halloween' ? 'crate_halloween' : 'crate_classic';
      if (!keyId) keyId = series === 'halloween' ? 'key_halloween' : 'key_standard';
      var crate = itemOf(crateId), key = itemOf(keyId);
      return new Promise(function (resolve) {
        var stage = new Stage({
          series: series, theme: info.theme || series,
          onClose: function (answer) { Crates.busy = false; resolve(answer); if (options.onClose) options.onClose(answer); },
          onResult: options.onResult
        });
        if (!stage.renderer) {
          // no WebGL: skip straight to the reel and the reveal
          request.then(function (res) {
            if (!res.ok) { stage.fail(res.error); return; }
            stage.startReel(res);
            (function loop(now) { if (stage.phase === 'reel') { stage.stepReel(now); requestAnimationFrame(loop); } })(performance.now());
          });
          return;
        }
        stage.run(crate || { name: 'Crate', data: { parts: [] } }, key || { data: { parts: [] } }, request);
      });
    });
  };

  // =========================================================== boot data
  document.addEventListener('DOMContentLoaded', function () {
    var data = document.getElementById('crate-data');
    if (data) {
      try {
        var parsed = JSON.parse(data.textContent);
        global.CRATE_SERIES = {};
        (parsed.series || []).forEach(function (s) { global.CRATE_SERIES[s.id] = s; });
        Crates.stash = parsed.stash || {};
      } catch (e) {}
    }
    document.addEventListener('click', function (e) {
      var c = e.target.closest('[data-contents]');
      if (c) { e.preventDefault(); Crates.showContents(c.dataset.contents); return; }
      var o = e.target.closest('[data-open-series]');
      if (o) { e.preventDefault(); Crates.open({ series: o.dataset.openSeries }); }
    });
  });

  global.Crates = Crates;
})(window);
