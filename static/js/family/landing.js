/* /parent_signup_l -- the landing page's living parts.

   The hero is a haven at dusk: stars and shooting stars on a canvas,
   fireflies round the island, and the live little world under its dome
   (haven.js), where the messages that fly at the dome bounce off it, each
   one answered here by the note a parent would get.  Below it: the dashboard demo, the live
   character, and "be the stranger", which runs the real Safe Chat filter.

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
  var DPR = Math.min(2, window.devicePixelRatio || 1);

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

  /* ---------------------------------------------------------- the stars */
  var starCanvas = $('#lp-stars');
  var stars = [];
  var shooting = null;
  var nextShoot = 0;
  function sizeCanvas(c) {
    var r = c.getBoundingClientRect();
    c.width = Math.max(1, Math.round(r.width * DPR));
    c.height = Math.max(1, Math.round(r.height * DPR));
    return r;
  }
  function seedStars() {
    if (!starCanvas) return;
    var r = sizeCanvas(starCanvas);
    var count = Math.round(Math.min(220, (r.width * r.height) / 5200));
    stars = [];
    for (var i = 0; i < count; i++) {
      var big = Math.random() < 0.08;
      stars.push({
        x: Math.random() * starCanvas.width,
        y: Math.pow(Math.random(), 1.5) * starCanvas.height * 0.82,
        r: (big ? 1.3 + Math.random() * 0.9 : 0.35 + Math.random() * 0.9) * DPR,
        p: Math.random() * Math.PI * 2,
        s: 0.6 + Math.random() * 1.8,
        warm: Math.random() < 0.18,
        big: big
      });
    }
  }
  function drawStars(t) {
    if (!starCanvas) return;
    var ctx = starCanvas.getContext('2d');
    ctx.clearRect(0, 0, starCanvas.width, starCanvas.height);
    for (var i = 0; i < stars.length; i++) {
      var st = stars[i];
      var a = reduce ? 0.8 : 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(st.p + t * 0.001 * st.s));
      ctx.globalAlpha = a;
      ctx.fillStyle = st.warm ? '#ffe8b8' : '#ffffff';
      ctx.beginPath();
      ctx.arc(st.x, st.y, st.r, 0, Math.PI * 2);
      ctx.fill();
      if (st.big) {
        ctx.globalAlpha = a * 0.35;
        ctx.fillRect(st.x - st.r * 4, st.y - 0.5 * DPR, st.r * 8, DPR);
        ctx.fillRect(st.x - 0.5 * DPR, st.y - st.r * 4, DPR, st.r * 8);
      }
    }
    ctx.globalAlpha = 1;
    if (reduce) return;
    if (!shooting && t > nextShoot) {
      shooting = { x: Math.random() * starCanvas.width * 0.7 + starCanvas.width * 0.15,
                   y: Math.random() * starCanvas.height * 0.3, t0: t,
                   dx: (Math.random() < 0.5 ? -1 : 1) * (5 + Math.random() * 3) * DPR,
                   dy: (2.2 + Math.random() * 1.5) * DPR };
      nextShoot = t + 5000 + Math.random() * 7000;
    }
    if (shooting) {
      var k = (t - shooting.t0) / 16.7;
      var hx = shooting.x + shooting.dx * k;
      var hy = shooting.y + shooting.dy * k;
      var life = 1 - k / 70;
      if (life <= 0) { shooting = null; return; }
      var grad = ctx.createLinearGradient(hx, hy, hx - shooting.dx * 18, hy - shooting.dy * 18);
      grad.addColorStop(0, 'rgba(255,255,255,' + (0.9 * life) + ')');
      grad.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.6 * DPR;
      ctx.beginPath();
      ctx.moveTo(hx, hy);
      ctx.lineTo(hx - shooting.dx * 18, hy - shooting.dy * 18);
      ctx.stroke();
    }
  }

  /* ------------------------------------------------------ the fireflies */
  var flyCanvas = $('#lp-flies');
  var flies = [];
  function seedFlies() {
    if (!flyCanvas) return;
    sizeCanvas(flyCanvas);
    var n = window.innerWidth < 700 ? 16 : 26;
    flies = [];
    for (var i = 0; i < n; i++) {
      flies.push({ x: Math.random(), y: 0.2 + Math.random() * 0.7, a: Math.random() * 6.28,
                   sp: 0.00015 + Math.random() * 0.00025, r: (1.2 + Math.random() * 1.8) * DPR,
                   ph: Math.random() * 6.28, turn: (Math.random() - 0.5) * 0.002 });
    }
  }
  function drawFlies(t, dt) {
    if (!flyCanvas) return;
    var ctx = flyCanvas.getContext('2d');
    var w = flyCanvas.width, h = flyCanvas.height;
    ctx.clearRect(0, 0, w, h);
    for (var i = 0; i < flies.length; i++) {
      var f = flies[i];
      if (!reduce) {
        f.a += f.turn * dt + Math.sin(t * 0.0007 + f.ph) * 0.01;
        f.x += Math.cos(f.a) * f.sp * dt;
        f.y += Math.sin(f.a) * f.sp * dt * 0.7;
        if (f.x < 0.02 || f.x > 0.98) f.a = Math.PI - f.a;
        if (f.y < 0.12 || f.y > 0.95) f.a = -f.a;
      }
      var glow = 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(t * 0.003 + f.ph));
      var px = f.x * w, py = f.y * h;
      var g = ctx.createRadialGradient(px, py, 0, px, py, f.r * 6);
      g.addColorStop(0, 'rgba(255,240,170,' + (0.9 * glow) + ')');
      g.addColorStop(0.3, 'rgba(255,214,107,' + (0.35 * glow) + ')');
      g.addColorStop(1, 'rgba(255,200,90,0)');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(px, py, f.r * 6, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  /* ------------------------------------------------------------ the notes
     The world under the dome (haven.js) turns away the messages that fly at
     it; each one it stops comes here as a "haven:blocked" event and gets the
     note a parent would see.  Friendly notes come in between. */
  var notesBox = $('#lp-notes');
  var havenHost = hero ? hero.querySelector('[data-haven]') : null;
  var GOOD = [
    { ic: 'good', icon: 'user-check', title: 'You approved Leo', sub: 'Mia’s new friend · just now' },
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
        ? { ic: 'blue', icon: 'shield-check', title: spec.title, sub: 'Rain outside, sunshine in · nothing got through' }
        : { ic: 'blue', icon: 'shield-check', title: spec.title, sub: 'Mia never saw it · you’ve been told' });
    });
  }

  /* --------------------------------------------------------- parallax */
  var layers = hero ? Array.prototype.slice.call(hero.querySelectorAll('.lp-layer[data-depth]')) : [];
  var fine = window.matchMedia && matchMedia('(pointer: fine)').matches;
  if (hero && fine && !reduce) {
    hero.addEventListener('pointermove', function (e) {
      var r = hero.getBoundingClientRect();
      var dx = (e.clientX - r.left) / r.width - 0.5;
      var dy = (e.clientY - r.top) / r.height - 0.5;
      layers.forEach(function (layer) {
        var d = parseFloat(layer.getAttribute('data-depth')) || 0;
        layer.style.transform = 'translate3d(' + (-dx * 40 * d).toFixed(1) + 'px,' + (-dy * 24 * d).toFixed(1) + 'px,0)';
      });
    });
    hero.addEventListener('pointerleave', function () {
      layers.forEach(function (layer) { layer.style.transform = ''; });
    });
  }

  /* --------------------------------------------------------- the loop */
  var last = performance.now();
  var nextGood = performance.now() + 900;
  var frame = 0;
  function loop(now) {
    requestAnimationFrame(loop);
    var dt = Math.min(64, now - last);
    last = now;
    if (!running()) return;
    frame++;
    if (frame % 2 === 0) drawStars(now);
    drawFlies(now, dt);
    if (now > nextGood) {
      note(GOOD[goodIndex++ % GOOD.length]);
      nextGood = now + 6800 + Math.random() * 1200;
    }
  }
  function boot() {
    seedStars();
    seedFlies();
    if (reduce) {
      drawStars(0);
      drawFlies(0, 0);
      note(GOOD[0]);
      return;
    }
    requestAnimationFrame(loop);
  }
  var resizeTimer = 0;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () { seedStars(); seedFlies(); if (reduce) { drawStars(0); drawFlies(0, 0); } }, 200);
  });
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
