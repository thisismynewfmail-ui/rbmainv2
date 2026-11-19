/* /parent_signup_l -- the landing page's living parts.

   The hero is the live little world under its shield (haven.js): the
   messages that fly at the shield bounce off it, and each one is answered
   here by the note a parent would get.  Below it: the dashboard demo, the
   live character, and "be the stranger", which runs the real Safe Chat
   filter.

   None of it is needed to read the page or to sign up: every call to
   action is a plain link, the questions are <details>, the 3D character
   loads only when somebody scrolls near it, every loop stops when it is off
   screen or the tab is hidden, and prefers-reduced-motion gets a still
   picture. */
(function () {
  'use strict';
  var FAM = window.FAM;
  var $ = FAM.$;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ------------------------------------------------- the bar and the CTA */
  var nav = $('#lp-nav');
  var sticky = $('#lp-sticky');
  var heroCta = $('#hero-cta');
  var finalSec = $('#start');
  var heroGone = false;
  var finalHere = false;
  function stickyUpdate() {
    if (!sticky) return;
    var show = heroGone && !finalHere;
    sticky.classList.toggle('show', show);
    sticky.setAttribute('aria-hidden', show ? 'false' : 'true');
    var link = sticky.querySelector('a');
    if (link) link.tabIndex = show ? 0 : -1;
  }
  function onScroll() { if (nav) nav.classList.toggle('is-scrolled', window.scrollY > 40); }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if ('IntersectionObserver' in window) {
    if (heroCta) new IntersectionObserver(function (entries) {
      heroGone = !entries[0].isIntersecting && entries[0].boundingClientRect.top < 0;
      stickyUpdate();
    }).observe(heroCta);
    if (finalSec) new IntersectionObserver(function (entries) {
      finalHere = entries[0].isIntersecting;
      stickyUpdate();
    }, { threshold: 0.15 }).observe(finalSec);
  }

  /* ------------------------------------------------------ ad conversions */
  document.addEventListener('click', function (e) {
    var cta = e.target.closest('[data-cta]');
    if (cta) FAM.track('Lead', { content_name: 'landing_' + cta.getAttribute('data-cta') });
  });
  var finalForm = $('[data-cta-form]');
  if (finalForm) finalForm.addEventListener('submit', function () {
    FAM.track('Lead', { content_name: 'landing_final_email' });
  });

  /* ============================================================ THE HERO */
  var hero = $('#hero');
  var heroVisible = true;
  if (hero && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) { heroVisible = entries[0].isIntersecting; })
      .observe(hero);
  }
  function running() { return heroVisible && !document.hidden; }

  /* ------------------------------------------------------------ the notes
     The world under the shield (haven.js) turns away the messages that fly
     at it; each one it stops comes here as a "haven:blocked" event and gets
     the note a parent would see.  Friendly notes come in between. */
  var notesBox = $('#lp-notes');
  var havenHost = hero ? hero.querySelector('[data-haven]') : null;
  var GOOD = [
    { ic: 'good', icon: 'user-check', title: 'You approved Leo', sub: 'Mia\u2019s new friend \u00b7 just now' },
    { ic: 'sun', icon: 'clock', title: '42 of 60 minutes today', meter: true },
    { ic: 'grape', icon: 'moon', title: 'Quiet hours at 8:00 pm', sub: 'Games rest until morning' },
    { ic: 'good', icon: 'pulse', title: 'Mia is playing Sky Sprint', sub: 'With 2 approved friends' }
  ];
  var goodIndex = 0;
  var side = 0;
  var lastBlocked = 0;

  function note(spec) {
    if (!notesBox) return;
    var n = document.createElement('div');
    n.className = 'lp-note' + (side++ % 2 ? ' right' : '');
    n.innerHTML = '<span class="lp-note-ic ' + spec.ic + '"><svg class="f-ic sm"><use href="#i-' + spec.icon +
      '"/></svg></span><span><b>' + FAM.esc(spec.title) + '</b>' +
      (spec.meter ? '<span class="lp-note-meter"><i></i></span>' : '<small>' + FAM.esc(spec.sub || '') + '</small>') +
      '</span>';
    notesBox.appendChild(n);
    while (notesBox.children.length > 2) notesBox.removeChild(notesBox.firstChild);
    setTimeout(function () {
      n.classList.add('out');
      setTimeout(function () { if (n.parentNode) n.parentNode.removeChild(n); }, 460);
    }, 3800);
  }
  if (havenHost) {
    havenHost.addEventListener('haven:blocked', function (e) {
      var spec = e.detail || {};
      var now = performance.now();
      if (now - lastBlocked < 1800) return;
      lastBlocked = now;
      note(spec.storm
        ? { ic: 'blue', icon: 'shield-check', title: spec.title, sub: 'Rain outside, sunshine in \u00b7 nothing got through' }
        : { ic: 'blue', icon: 'shield-check', title: spec.title, sub: 'Mia never saw it \u00b7 you\u2019ve been told' });
    });
  }

  /* -------------------------------------------- the friendly notes' clock */
  function boot() {
    if (reduce) { note(GOOD[0]); return; }
    setTimeout(function tick() {
      if (running()) note(GOOD[goodIndex++ % GOOD.length]);
      setTimeout(tick, 6800 + Math.random() * 1200);
    }, 900);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  /* ================================================= the dashboard demo */
  var demo = $('#demo');
  if (demo) {
    var count = demo.querySelector('[data-demo-count]');
    var ask = demo.querySelector('.lp-demo-item.ask');
    var yes = demo.querySelector('.lp-demo-yes');
    var timers = [];
    var looping = false;
    var play = function () {
      timers.forEach(clearTimeout);
      timers = [];
      demo.classList.remove('in');
      if (ask) ask.classList.remove('approved');
      if (count) count.textContent = '0';
      void demo.offsetWidth;
      demo.classList.add('in');
      FAM.countUp(count, 42, 1600);
      timers.push(setTimeout(function () { if (yes) yes.classList.add('press'); }, 2600));
      timers.push(setTimeout(function () {
        if (yes) yes.classList.remove('press');
        if (ask) ask.classList.add('approved');
      }, 3050));
    };
    if ('IntersectionObserver' in window) {
      var seen = false;
      new IntersectionObserver(function (entries) {
        var visible = entries[0].isIntersecting;
        if (visible && !seen) { seen = true; play(); }
        looping = visible;
      }, { threshold: 0.35 }).observe(demo);
      setInterval(function () { if (looping && !document.hidden && !reduce) play(); }, 11000);
    } else {
      play();
    }
  }

  /* ================================================== be the stranger */
  var tryForm = $('#try-form');
  if (tryForm) {
    var thread = $('#try-thread');
    var input = $('#try-text');
    var shieldLine = $('#try-shield');
    var alertCard = $('#try-alert');
    var alertText = $('#try-alert-text');
    var alertTimer = 0;
    var busy = false;
    var scrollDown = function () { thread.scrollTop = thread.scrollHeight; };
    var send = function (text) {
      text = (text || '').trim();
      if (!text || busy) return;
      busy = true;
      var bubble = document.createElement('div');
      bubble.className = 'lp-bubble stranger checking';
      bubble.innerHTML = '<b>Stranger</b>';
      bubble.appendChild(document.createTextNode(text));
      thread.appendChild(bubble);
      scrollDown();
      FAM.post('/api/family/safechat-demo', { text: text }).then(function (res) {
        busy = false;
        bubble.classList.remove('checking');
        if (!res.ok) {
          bubble.appendChild(Object.assign(document.createElement('span'), { className: 'lp-verdict', textContent: res.error || 'Try again in a moment.' }));
          return;
        }
        if (res.action === 'block') {
          bubble.className = 'lp-bubble blocked';
          bubble.innerHTML = '<b>🛡 Blocked by Safe Chat</b>';
          bubble.appendChild(document.createTextNode('It contained ' + res.what + '. Mia never saw it.'));
          shieldLine.classList.add('flash');
          setTimeout(function () { shieldLine.classList.remove('flash'); }, 1400);
          alertText.textContent = 'Safe Chat blocked ' + res.what + ' sent to Mia.';
          alertCard.classList.add('show');
          clearTimeout(alertTimer);
          alertTimer = setTimeout(function () { alertCard.classList.remove('show'); }, 4200);
        } else if (res.action === 'mask') {
          bubble.className = 'lp-bubble stranger masked';
          bubble.innerHTML = '<b>Stranger</b>';
          bubble.appendChild(document.createTextNode(res.masked));
          bubble.insertAdjacentHTML('beforeend', '<span class="lp-verdict">••• Strong language blanked out</span>');
        } else {
          bubble.className = 'lp-bubble stranger ok';
          bubble.insertAdjacentHTML('beforeend', '<span class="lp-verdict"><svg class="f-ic sm"><use href="#i-check"/></svg>' +
            (res.action === 'flag' ? ' Delivered — and you were told' : ' Delivered — nothing risky in it') + '</span>');
        }
        while (thread.children.length > 10) thread.removeChild(thread.firstChild);
        scrollDown();
      });
    };
    tryForm.addEventListener('submit', function (e) {
      e.preventDefault();
      send(input.value);
      input.value = '';
    });
    var chips = $('#try-chips');
    if (chips) chips.addEventListener('click', function (e) {
      var chip = e.target.closest('[data-try]');
      if (chip) send(chip.getAttribute('data-try'));
    });
  }

  /* ================================================ the live character */
  var stage = $('#lp-stage');
  var caption = $('#lp-look');
  function webglOK() {
    try {
      var c = document.createElement('canvas');
      return !!(c.getContext('webgl') || c.getContext('experimental-webgl'));
    } catch (e) { return false; }
  }
  function loadScripts(list) {
    // the page may already carry the engine (the dome draws with it)
    if (window.Renderer && window.Thumbs && window.Avatar) return Promise.resolve();
    return list.reduce(function (chain, src) {
      return chain.then(function () {
        return new Promise(function (resolve, reject) {
          var s = document.createElement('script');
          s.src = src;
          s.async = false;
          s.onload = resolve;
          s.onerror = reject;
          document.body.appendChild(s);
        });
      });
    }, Promise.resolve());
  }
  function describe(look) {
    if (!caption || !look) return;
    var names = (look.chips || []).slice(0, 3).map(function (c) { return c.name; });
    if (look.unusual && look.unusualName) names.push(look.unusualName + ' effect');
    caption.textContent = names.length
      ? 'Today’s look: ' + names.join(' · ') + '. Every piece comes from the real catalogue.'
      : 'Hats, faces, outfits and pets to mix and match.';
  }
  function mount() {
    if (!window.Thumbs || !Thumbs.LivePreview || typeof Renderer === 'undefined') return;
    // the brand's character only: yellow skin, a blue body
    var BRAND = { brand: true };
    var look = Thumbs.randomLook(BRAND);
    var preview = new Thumbs.LivePreview(stage, look.descriptor);
    if (preview.failed) return;
    preview.skyMode = 'stage';
    preview.applyTheme();
    preview.setPose(look.pose);
    preview.margin = 0.07;
    preview.markHome();
    stage.__preview = preview;
    stage.__look = look;
    stage.classList.add('live');
    if (Thumbs.rescan) Thumbs.rescan();
    stage.addEventListener('look', function (e) { describe(e.detail); });
    Thumbs.loadCatalog().then(function () { Thumbs.dressHero(stage, BRAND); });
    var inView = true;
    var held = false;
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) { inView = entries[0].isIntersecting; }).observe(stage);
    }
    stage.addEventListener('pointerdown', function () { held = true; });
    window.addEventListener('pointerup', function () { setTimeout(function () { held = false; }, 1500); });
    setInterval(function () {
      if (inView && !held && !document.hidden && Thumbs.dressHero) Thumbs.dressHero(stage, BRAND);
    }, 5600);
  }
  if (stage && webglOK()) {
    var list = [];
    try { list = JSON.parse(stage.getAttribute('data-engine') || '[]'); } catch (e) { list = []; }
    var started = false;
    var go = function () {
      if (started || !list.length) return;
      started = true;
      loadScripts(list).then(mount).catch(function () {});
    };
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) { io.disconnect(); go(); }
      }, { rootMargin: '600px 0px' });
      io.observe(stage);
    } else {
      window.addEventListener('load', go);
    }
  }
})();
