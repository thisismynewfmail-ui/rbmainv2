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
  var SHUFFLE_MS = 10000;

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
      chips.unshift('<span class="chip body">' +
        (look.descriptor.body_type === 'female' ? 'Female' : 'Male') + '</span>');
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
      stage.classList.remove('swapping');
      void stage.offsetWidth;          // restart the fade on a rapid re-roll
      stage.classList.add('swapping');
      // dressHero puts the camera back where it started as well, so a viewer
      // who zoomed in or stopped the spin gets a clean look at the next one
      Thumbs.dressHero(stage);
      setTimeout(function () { stage.classList.remove('swapping'); }, 460);
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

  document.addEventListener('DOMContentLoaded', function () {
    bindCountdown();
    bindCounters();
    // thumbs.js builds the preview in its own DOMContentLoaded handler, which
    // runs before this one, so the stage is already there to listen to
    bindHero();
  });
})();
