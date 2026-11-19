/* Home page: the spotlight countdown, and the welcome screen's live
   character. */
(function () {
  'use strict';

  // ------------------------------------------------------------ countdown
  function bindCountdown() {
    var bar = document.querySelector('[data-countdown]');
    if (!bar) return;
    var remaining = parseInt(bar.dataset.countdown, 10) || 0;
    var fields = {
      d: bar.querySelector('[data-cd="d"]'),
      h: bar.querySelector('[data-cd="h"]'),
      m: bar.querySelector('[data-cd="m"]'),
      s: bar.querySelector('[data-cd="s"]')
    };
    function pad(value) { return value < 10 ? '0' + value : String(value); }
    function tick() {
      var left = Math.max(0, remaining);
      if (fields.d) fields.d.textContent = Math.floor(left / 86400);
      if (fields.h) fields.h.textContent = pad(Math.floor(left / 3600) % 24);
      if (fields.m) fields.m.textContent = pad(Math.floor(left / 60) % 60);
      if (fields.s) fields.s.textContent = pad(left % 60);
      remaining -= 1;
    }
    tick();
    setInterval(tick, 1000);
  }

  // -------------------------------------------------------- counting up
  /* The numbers on the welcome screen roll up to their real value once, when
     they scroll into view.  It is the cheapest way to make a static figure
     read as something the platform is actually doing. */
  function bindCounters() {
    var nodes = document.querySelectorAll('.hero-facts [data-count]');
    if (!nodes.length) return;
    var reduced = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    nodes.forEach(function (node) {
      var target = parseInt(node.dataset.count, 10) || 0;
      if (reduced || target <= 0) {
        node.textContent = target.toLocaleString();
        return;
      }
      var started = 0;
      var duration = 900;
      function step(now) {
        if (!started) started = now;
        var t = Math.min(1, (now - started) / duration);
        // ease-out so it decelerates into the real figure
        var eased = 1 - Math.pow(1 - t, 3);
        node.textContent = Math.round(target * eased).toLocaleString();
        if (t < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
  }

  // ------------------------------------------------------- the character
  /* The welcome character dresses itself.  Everything it wears is rolled out
     of the live catalogue by thumbs.js; this end names the look and keeps the
     rolls coming on a slow timer, pausing while somebody is actually looking
     at (or spinning) the one on screen. */
  var SHUFFLE_MS = 15000;

  function bindHero() {
    var stage = document.querySelector('.avatar-view[data-avatar-hero]');
    if (!stage) return;
    var nameNode = document.getElementById('hero-look-name');
    var chipNode = document.getElementById('hero-chips');
    var autoTimer = 0;
    var paused = false;

    function escapeHtml(text) {
      var div = document.createElement('div');
      div.textContent = text == null ? '' : String(text);
      return div.innerHTML;
    }

    function describe(look) {
      if (!look) return;
      if (nameNode) {
        nameNode.textContent = look.hat
          ? (look.unusual ? look.hat.name + ' \u2014 Unusual' : look.hat.name)
          : 'No hat today';
        nameNode.classList.toggle('unu', !!look.unusual);
      }
      if (!chipNode) return;
      var chips = look.chips.slice(0, 4).map(function (chip) {
        return '<span class="chip">' + escapeHtml(chip.name) + '</span>';
      });
      // named by the build the rig actually drew, so the chip cannot disagree
      // with the character standing on the stage
      var build = window.Avatar
        ? Avatar.BODY_LABELS[Avatar.bodyType(look.descriptor)] : '';
      chips.unshift('<span class="chip body">' +
        escapeHtml(build || 'Male') + '</span>');
      if (look.unusual) {
        chips.push('<span class="chip unusual">' +
                   escapeHtml(look.unusualName) + '</span>');
      }
      var pose = window.Thumbs && Thumbs.posePreviewLabel
        ? Thumbs.posePreviewLabel(look.pose) : '';
      if (pose) chips.push('<span class="chip pose">' + escapeHtml(pose) + '</span>');
      chipNode.innerHTML = chips.join('');
    }

    function shuffle() {
      if (!window.Thumbs || !Thumbs.dressHero) return;
      // The transition lives inside the preview now: the character dissolves
      // and settles back in on its own while the stage, its painted sky and
      // the camera's turn all carry on untouched.
      Thumbs.dressHero(stage);
    }

    stage.addEventListener('look', function (event) { describe(event.detail); });
    if (stage.__look) describe(stage.__look);

    autoTimer = setInterval(function () {
      if (paused || document.hidden) return;
      shuffle();
    }, SHUFFLE_MS);
    ['pointerenter', 'focusin'].forEach(function (name) {
      stage.addEventListener(name, function () { paused = true; });
    });
    ['pointerleave', 'focusout'].forEach(function (name) {
      stage.addEventListener(name, function () { paused = false; });
    });
  }

  // ------------------------------------------------------ jump back in
  /* The sort menu at the top right of "Jump back in" reorders the cards on
     the spot (with a little slide, so you can see where each one went) and
     leaves a cookie so the page comes back sorted the same way.  Without
     JavaScript it is a plain form and the server does the sorting. */
  function bindJumpSort() {
    var form = document.getElementById('jump-sort');
    var grid = document.getElementById('jump-grid');
    if (!form || !grid) return;
    var select = form.querySelector('select');
    var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    function num(card, key) { return parseFloat(card.getAttribute('data-' + key)) || 0; }
    function players(card) {
      var live = card.querySelector('[data-live-players]');
      return live ? parseInt(live.textContent, 10) || 0 : 0;
    }
    // the same words as the server's ago() (app/views/base.py)
    function ago(ts) {
      var s = Math.max(0, Math.floor(Date.now() / 1000 - ts));
      function n(v, unit) { return v + ' ' + unit + (v === 1 ? '' : 's') + ' ago'; }
      if (s < 60) return s + ' seconds ago';
      if (s < 3600) return n(Math.floor(s / 60), 'minute');
      if (s < 86400) return n(Math.floor(s / 3600), 'hour');
      if (s < 86400 * 30) return n(Math.floor(s / 86400), 'day');
      var d = new Date(ts * 1000);
      return 'on ' + d.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
    }
    function span(sec) {
      var m = Math.max(1, Math.floor(sec / 60));
      if (m < 60) return m + ' min played';
      var h = Math.floor(m / 60), r = m % 60;
      return r ? h + 'h ' + r + 'm played' : h + 'h played';
    }
    var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    function note(card, key) {
      if (key === 'recent') { var t = num(card, 'recent'); return t ? 'Played ' + ago(t) : ''; }
      if (key === 'playtime') { var p = num(card, 'playtime'); return p ? span(p) : ''; }
      if (key === 'newest') {
        var a = card.getAttribute('data-added') || '';
        var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(a);
        return m ? 'Added ' + MONTHS[parseInt(m[2], 10) - 1] + ' ' + parseInt(m[3], 10) : '';
      }
      if (key === 'popular') return num(card, 'visits').toLocaleString() + ' visits';
      if (key === 'rated') return num(card, 'votes') ? num(card, 'rating') + '% liked' : 'Not rated yet';
      if (key === 'favourites') return num(card, 'fav') >= 0 ? '★ Favourite' : '';
      return '';
    }
    var compare = {
      recent: function (a, b) { return num(b, 'recent') - num(a, 'recent'); },
      playtime: function (a, b) { return num(b, 'playtime') - num(a, 'playtime'); },
      newest: function (a, b) { return (b.getAttribute('data-added') || '').localeCompare(a.getAttribute('data-added') || ''); },
      popular: function (a, b) { return num(b, 'visits') - num(a, 'visits'); },
      rated: function (a, b) { return (num(b, 'rating') - num(a, 'rating')) || (num(b, 'votes') - num(a, 'votes')); },
      playing: function (a, b) { return players(b) - players(a); },
      favourites: function (a, b) {
        var fa = num(a, 'fav'), fb = num(b, 'fav');
        if ((fa < 0) !== (fb < 0)) return fa < 0 ? 1 : -1;
        return fa - fb;
      },
      name: function (a, b) { return (a.getAttribute('data-name') || '').localeCompare(b.getAttribute('data-name') || ''); }
    };
    function apply(key) {
      var cards = Array.prototype.slice.call(grid.querySelectorAll('.worldcard[data-order]'));
      if (!cards.length) return;
      var before = {};
      cards.forEach(function (c) { before[c.getAttribute('data-world-id')] = c.getBoundingClientRect(); });
      var cmp = compare[key] || compare.recent;
      cards.sort(function (a, b) { return cmp(a, b) || (num(a, 'order') - num(b, 'order')); });
      cards.forEach(function (c) {
        grid.appendChild(c);
        var n = c.querySelector('.sortnote');
        if (n) { var text = note(c, key); n.textContent = text; n.hidden = !text; }
      });
      grid.setAttribute('data-sort', key);
      if (reduced) return;
      // slide each card from where it was to where it is now
      cards.forEach(function (c) {
        var was = before[c.getAttribute('data-world-id')], now = c.getBoundingClientRect();
        if (!was) return;
        var dx = was.left - now.left, dy = was.top - now.top;
        if (!dx && !dy) return;
        c.style.transition = 'none';
        c.style.transform = 'translate(' + dx + 'px,' + dy + 'px)';
      });
      void grid.offsetWidth;
      grid.classList.add('sorting');
      cards.forEach(function (c) { c.style.transition = ''; c.style.transform = ''; });
      setTimeout(function () { grid.classList.remove('sorting'); }, 450);
    }
    select.addEventListener('change', function () {
      var key = select.value;
      apply(key);
      try {
        document.cookie = 'bh_jump=' + encodeURIComponent(key) + '; path=/; max-age=31536000; samesite=lax' +
          (location.protocol === 'https:' ? '; secure' : '');
      } catch (e) { /* cookies off: it still sorts, just not next time */ }
    });
    form.addEventListener('submit', function (e) { e.preventDefault(); apply(select.value); });
  }

  document.addEventListener('DOMContentLoaded', function () {
    bindCountdown();
    bindJumpSort();
    bindCounters();
    // thumbs.js builds the preview in its own DOMContentLoaded handler, which
    // runs before this one, so the stage is already there to listen to
    bindHero();
  });
})();
