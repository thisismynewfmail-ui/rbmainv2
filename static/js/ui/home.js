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
  var POSES = ['idle', 'walk', 'run', 'jump', 'sit'];

  function bindHero() {
    var stage = document.querySelector('.avatar-view[data-avatar-hero]');
    if (!stage) return;
    var nameNode = document.getElementById('hero-look-name');
    var chipNode = document.getElementById('hero-chips');
    var poseIndex = 0;
    var autoTimer = 0;
    var paused = false;

    function describe(look) {
      if (!look) return;
      if (nameNode) {
        var hat = look.hat ? look.hat.name : 'no hat';
        nameNode.textContent = look.unusual
          ? hat + ' — Unusual'
          : hat;
        nameNode.classList.toggle('unu', !!look.unusual);
      }
      if (chipNode) {
        var chips = look.chips.slice(0, 4).map(function (chip) {
          return '<span class="chip">' + escapeHtml(chip.name) + '</span>';
        });
        var body = look.descriptor.body_type === 'female' ? 'Female' : 'Male';
        chips.unshift('<span class="chip body">' + body + '</span>');
        if (look.unusual) {
          chips.push('<span class="chip unusual">' +
                     escapeHtml(look.unusualName) + '</span>');
        }
        var preview = stage.__preview;
        var pose = preview && Thumbs.posePreviewLabel
          ? Thumbs.posePreviewLabel(preview.poseState) : '';
        if (pose) chips.push('<span class="chip pose">' + escapeHtml(pose) + '</span>');
        chipNode.innerHTML = chips.join('');
      }
    }

    function escapeHtml(text) {
      var div = document.createElement('div');
      div.textContent = text == null ? '' : String(text);
      return div.innerHTML;
    }

    function shuffle(pose) {
      var preview = stage.__preview;
      if (!preview || !window.Thumbs || !Thumbs.randomLook) return;
      var look = Thumbs.randomLook(pose ? { pose: pose } : {});
      stage.__look = look;
      stage.classList.remove('swapping');
      // force the fade to restart even on a rapid second click
      void stage.offsetWidth;
      stage.classList.add('swapping');
      preview.setDescriptor(look.descriptor);
      preview.setPose(look.pose);
      poseIndex = Math.max(0, POSES.indexOf(look.pose));
      describe(look);
      setTimeout(function () { stage.classList.remove('swapping'); }, 460);
    }

    function nextPose() {
      var preview = stage.__preview;
      if (!preview) return;
      poseIndex = (poseIndex + 1) % POSES.length;
      preview.setPose(POSES[poseIndex]);
      describe(stage.__look);
    }

    stage.addEventListener('look', function (event) { describe(event.detail); });
    if (stage.__look) describe(stage.__look);

    document.addEventListener('click', function (event) {
      var button = event.target.closest('[data-hero]');
      if (!button) return;
      event.preventDefault();
      if (button.dataset.hero === 'shuffle') shuffle();
      else if (button.dataset.hero === 'pose') nextPose();
      restart();
    });

    // A character that only ever moves when you poke it is a screenshot.  It
    // rolls a new look on a slow timer as well, pausing while the pointer is
    // on the stage so nobody loses the outfit they were looking at.
    function restart() {
      clearInterval(autoTimer);
      autoTimer = setInterval(function () {
        if (paused || document.hidden) return;
        shuffle();
      }, 9000);
    }
    ['pointerenter', 'focusin'].forEach(function (name) {
      stage.addEventListener(name, function () { paused = true; });
    });
    ['pointerleave', 'focusout'].forEach(function (name) {
      stage.addEventListener(name, function () { paused = false; });
    });
    restart();
  }

  document.addEventListener('DOMContentLoaded', function () {
    bindCountdown();
    bindCounters();
    // the hero preview is created by thumbs.js once the catalogue lands
    if (window.Thumbs && Thumbs.loadCatalog) {
      Thumbs.loadCatalog().then(function () { setTimeout(bindHero, 0); });
    } else {
      bindHero();
    }
  });
})();
