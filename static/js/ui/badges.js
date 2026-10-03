/* BLOCKHAVEN site -- badges.

   Every page can show a badge: a profile's row of four, the Badge Inventory
   in the profile editor, the Badge tab of the avatar editor.  A page puts
   the cards it needs in a <script type="application/json" class="badge-data">
   block ({"cards": [...]}) -- each card is app/models/badges.card(), with its
   3D model -- and marks up tiles with:

     <canvas class="badge-3d" data-badge="br_flag_runner"></canvas>
         a still of that badge at the level in its card
     <... data-badge-pop="br_flag_runner">
         hovering (or focusing, or tapping) it opens the pop-up: the badge
         turning on a stand, draggable round, with its one-line description,
         its rank and how far it is to the next one

   It also draws the toast that says a badge was earned (Badges.toast), with
   the emblem painted onto a medal in the tier's metal. */
(function (global) {
  'use strict';

  var Badges = { cards: {} };

  function esc(t) { return global.Site ? Site.escape(t) : String(t == null ? '' : t); }
  function reduced() {
    return global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  // the sparkle round a Diamond or Mythic badge in its pop-up
  var GLINT = {
    diamond: { rate: 10, life: [0.6, 1.1], size: [0.06, 0.13], grow: -0.05, gravity: -0.1,
               spread: 0.5, rise: [0.05, 0.25], blend: 'add', spin: 3,
               colors: ['#ffffff', '#bff4ff', '#7fe3ff'], shape: 'star', radius: 0.62, orbit: 0.7 },
    mythic: { rate: 18, life: [0.8, 1.4], size: [0.07, 0.16], grow: -0.06, gravity: -0.25,
              spread: 0.62, rise: [0.1, 0.4], blend: 'add', spin: 4,
              colors: ['#ff4fd8', '#ffcf4a', '#ffffff', '#b26bff'], shape: 'star',
              radius: 0.74, orbit: 1.0 }
  };

  // ------------------------------------------------------------- the data
  Badges.load = function (root) {
    (root || document).querySelectorAll('script.badge-data').forEach(function (node) {
      if (node.dataset.read) return;
      node.dataset.read = '1';
      try {
        var data = JSON.parse(node.textContent);
        (data.cards || []).forEach(function (card) { Badges.add(card); });
      } catch (e) {}
    });
  };
  Badges.add = function (card) {
    if (!card || !card.id) return;
    Badges.cards[card.id] = card;
  };

  function view(card) {
    // a little off square, so the rim and the depth of the thing show
    return { angle: -0.36, tilt: 0.08, padding: 1.04 };
  }

  // ----------------------------------------------------------- the stills
  Badges.render = function (canvas, card) {
    card = card || Badges.cards[canvas.dataset.badge];
    if (!card || !card.parts || !global.Thumbs) return;
    var opts = view(card);
    Thumbs.renderPartsTo(canvas, card.parts, opts,
                         'badge:' + card.id + ':' + Math.max(1, card.level));
  };

  Badges.scan = function (root) {
    Badges.load(root);
    var list = (root || document).querySelectorAll('canvas.badge-3d[data-badge]');
    var queue = Array.prototype.slice.call(list);
    // a few per frame, so a page with twenty badges does not stall
    (function step() {
      var n = 0;
      while (queue.length && n < 4) { Badges.render(queue.shift()); n++; }
      if (queue.length) requestAnimationFrame(step);
    })();
  };

  // ------------------------------------------------------------ the pop-up
  var pop = null;      // { box, canvas, tile, job, hide }

  function progressHtml(card) {
    if (!card.earned) {
      var first = card.thresholds[0];
      return '<div class="bp-prog"><i style="width:' + card.pct + '%"></i></div>' +
        '<small>' + Number(card.value || 0).toLocaleString() + ' / ' + first.toLocaleString() +
        ' ' + esc(card.unit) + ' to earn it</small>';
    }
    if (card.next === null || card.next === undefined) {
      return '<div class="bp-prog max"><i style="width:100%"></i></div>' +
        '<small>Maxed out &mdash; ' + Number(card.value || 0).toLocaleString() + ' ' + esc(card.unit) + '</small>';
    }
    return '<div class="bp-prog"><i style="width:' + card.pct + '%"></i></div>' +
      '<small>' + Number(card.value || 0).toLocaleString() + ' / ' + card.next.toLocaleString() + ' ' +
      esc(card.unit) + ' to ' + esc(card.ranks[card.level] || 'the next rank') + '</small>';
  }

  function ladderHtml(card) {
    var out = '<div class="bp-ladder">';
    for (var i = 0; i < card.levels; i++) {
      out += '<i class="t-' + ['bronze', 'silver', 'gold', 'platinum', 'diamond', 'mythic'][i] +
        (i < card.level ? ' on' : '') + '" title="' + esc(card.ranks[i]) + ' (' +
        card.thresholds[i].toLocaleString() + ')"></i>';
    }
    return out + '</div>';
  }

  function place(box, tile) {
    var r = tile.getBoundingClientRect();
    var w = box.offsetWidth, h = box.offsetHeight;
    var x = r.left + r.width / 2 - w / 2;
    var y = r.top - h - 10;
    var below = y < 8;
    if (below) y = r.bottom + 10;
    x = Math.max(8, Math.min(global.innerWidth - w - 8, x));
    box.style.left = x + 'px';
    box.style.top = (y + global.scrollY) + 'px';
    box.classList.toggle('below', below);
    box.style.setProperty('--arrow', (r.left + r.width / 2 - x) + 'px');
  }

  Badges.show = function (tile) {
    var card = Badges.cards[tile.dataset.badgePop];
    if (!card || document.body.classList.contains('bi-dragging')) return;
    if (pop && pop.tile === tile) { clearTimeout(pop.hide); return; }
    Badges.hide(true);
    var box = document.createElement('div');
    box.className = 'badge-pop tier-' + card.tier + (card.earned ? '' : ' locked');
    box.style.setProperty('--tier', card.color);
    box.style.setProperty('--glow', card.glow);
    box.innerHTML =
      '<div class="bp-stage"><canvas width="320" height="320"></canvas>' +
      '<span class="bp-hint">drag to turn</span></div>' +
      '<div class="bp-info">' +
      '<b class="bp-name">' + esc(card.name) + '</b>' +
      '<span class="bp-tier">' + (card.earned
        ? esc(card.tier_label) + ' &bull; Rank ' + card.level + ': ' + esc(card.rank)
        : 'Not earned yet') + '</span>' +
      '<p>' + esc(card.description) + '</p>' +
      ladderHtml(card) + progressHtml(card) +
      '<span class="bp-game">' + esc(card.game_name) + '</span>' +
      '</div>';
    document.body.appendChild(box);
    place(box, tile);
    requestAnimationFrame(function () { box.classList.add('in'); });
    var canvas = box.querySelector('canvas');
    var opts = view(card);
    var job = null;
    if (global.Thumbs && card.parts) {
      Thumbs.renderPartsTo(canvas, card.parts, opts, null);
      if (!reduced()) {
        job = Thumbs.animateParts(canvas, card.parts, {
          angle: opts.angle, tilt: opts.tilt, padding: opts.padding * 1.08,
          spin: 0.7, def: card.earned ? (GLINT[card.tier] || null) : null
        });
      }
    }
    pop = { box: box, tile: tile, canvas: canvas, job: job, hide: 0 };
    bindDrag(canvas);
    box.addEventListener('pointerenter', function () { if (pop) clearTimeout(pop.hide); });
    box.addEventListener('pointerleave', function () { Badges.hide(); });
  };

  Badges.hide = function (now) {
    if (!pop) return;
    var current = pop;
    clearTimeout(current.hide);
    function go() {
      if (pop !== current) return;
      pop = null;
      if (global.Thumbs) Thumbs.stopLive(current.canvas);
      current.box.classList.remove('in');
      setTimeout(function () { current.box.remove(); }, 200);
    }
    if (now) go(); else current.hide = setTimeout(go, 160);
  };

  /* Drag the badge round on its stand; it carries on turning when let go. */
  function bindDrag(canvas) {
    var last = null;
    canvas.addEventListener('pointerdown', function (e) {
      var job = global.Thumbs && Thumbs.liveJob(canvas);
      if (!job) return;
      last = { x: e.clientX, y: e.clientY };
      job.held = true;
      try { canvas.setPointerCapture(e.pointerId); } catch (err) {}
      e.preventDefault();
    });
    canvas.addEventListener('pointermove', function (e) {
      if (!last) return;
      var job = Thumbs.liveJob(canvas);
      if (!job) return;
      job.angle -= (e.clientX - last.x) * 0.012;
      job.tilt = Math.max(-0.9, Math.min(0.9, job.tilt + (e.clientY - last.y) * 0.008));
      last = { x: e.clientX, y: e.clientY };
    });
    function up() {
      if (!last) return;
      last = null;
      var job = Thumbs.liveJob(canvas);
      if (job) job.held = false;
    }
    canvas.addEventListener('pointerup', up);
    canvas.addEventListener('pointercancel', up);
  }

  // ------------------------------------------------------------- the medal
  /* A flat medal for toasts and anywhere a WebGL context is too much: the
     tier's metal, a rim, and the badge's emblem painted on. */
  Badges.drawMedal = function (canvas, info) {
    var ctx = canvas.getContext('2d');
    if (!ctx) return;
    var w = canvas.width, h = canvas.height, r = Math.min(w, h) / 2 - 2;
    ctx.clearRect(0, 0, w, h);
    var g = ctx.createRadialGradient(w * 0.38, h * 0.32, r * 0.1, w / 2, h / 2, r);
    g.addColorStop(0, '#ffffff');
    g.addColorStop(0.35, info.color || '#f0bd45');
    g.addColorStop(1, 'rgba(0,0,0,0.55)');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(w / 2, h / 2, r, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = info.face || '#173a66';
    ctx.beginPath(); ctx.arc(w / 2, h / 2, r * 0.74, 0, Math.PI * 2); ctx.fill();
    if (global.Textures && Textures.paintEmblem && info.emblem) {
      var s = r * 1.2;
      Textures.paintEmblem(ctx, info.emblem, w / 2 - s / 2, h / 2 - s / 2, s);
    }
  };

  var FACES = { cog: '#173a66', shield: '#3a140c', star: '#2b1450', moon: '#1a0d26' };
  var TIER_COLORS = { bronze: '#b8743a', silver: '#c9d2da', gold: '#f0bd45',
                      platinum: '#f1eef8', diamond: '#8fe6ff', mythic: '#2c1440' };

  /* "Badge earned!" -- a card that slides up at the corner of the screen. */
  Badges.toast = function (note) {
    var data = note.data || {};
    var card = Badges.cards[data.badge] || {};
    var wrap = document.getElementById('badge-toasts');
    if (!wrap) {
      wrap = document.createElement('div');
      wrap.id = 'badge-toasts';
      document.body.appendChild(wrap);
    }
    var node = document.createElement('a');
    node.className = 'badge-toast tier-' + (data.tier || 'bronze') + (data.first ? ' first' : '');
    node.href = '/profile-editor#badges';
    node.innerHTML = '<canvas width="112" height="112"></canvas>' +
      '<div><small>' + (data.first ? 'New badge!' : 'Badge levelled up!') + '</small>' +
      '<b>' + esc(note.title) + '</b><span>' + esc(note.body) + '</span></div>';
    wrap.appendChild(node);
    Badges.drawMedal(node.querySelector('canvas'), {
      color: TIER_COLORS[data.tier] || card.color, emblem: data.emblem || card.emblem,
      face: FACES[data.family || card.family] || '#173a66'
    });
    requestAnimationFrame(function () { node.classList.add('in'); });
    setTimeout(function () {
      node.classList.remove('in');
      node.classList.add('out');
      setTimeout(function () { node.remove(); }, 500);
    }, 7000);
  };

  // ----------------------------------------------------------------- boot
  document.addEventListener('DOMContentLoaded', function () {
    Badges.scan(document);
    document.addEventListener('pointerover', function (e) {
      var tile = e.target.closest && e.target.closest('[data-badge-pop]');
      if (tile) Badges.show(tile);
    });
    document.addEventListener('pointerout', function (e) {
      var tile = e.target.closest && e.target.closest('[data-badge-pop]');
      if (!tile || !pop || pop.tile !== tile) return;
      if (e.relatedTarget && tile.contains(e.relatedTarget)) return;
      Badges.hide();
    });
    document.addEventListener('focusin', function (e) {
      var tile = e.target.closest && e.target.closest('[data-badge-pop]');
      if (tile) Badges.show(tile);
    });
    document.addEventListener('focusout', function (e) {
      var tile = e.target.closest && e.target.closest('[data-badge-pop]');
      if (tile) Badges.hide();
    });
    global.addEventListener('scroll', function () { if (pop) Badges.hide(true); }, { passive: true });
  });

  global.Badges = Badges;
})(window);
