/* /parent_<name>/setup -- setting up a child's account, side by side.

   Eight panes, one state object, one request at the end: nothing is saved
   until the review pane's button posts it all to /api/family/children, so a
   parent can wander back and forth (or close the tab) without leaving a
   half-made account behind. */
(function () {
  'use strict';
  var FAM = window.FAM;
  var boot = FAM.boot || {};
  var $ = FAM.$;
  var $$ = FAM.$$;
  var wz = $('#wz');
  if (!wz) return;

  var LAST = 7;
  var panes = $$('.wz-pane', wz);
  var bar = $$('#wz-steps i');
  var foot = $('#wz-foot');
  var backBtn = $('#wz-back');
  var nextBtn = $('#wz-next');
  var meta = $('#wz-meta-step');

  function clone(o) { return JSON.parse(JSON.stringify(o || {})); }
  var base = boot.avatar || { colors: {}, body_type: 'male', items: {} };
  var state = {
    step: 0,
    first: '',
    year: '',
    username: '',
    nameOk: false,
    password: '',
    look: { body_type: base.body_type || 'male', colors: clone(base.colors) },
    controls: clone(boot.defaults_unknown),
    rulesTouched: false,
    child: null,
    busy: false
  };

  /* ------------------------------------------------------- the world
     The island above the card builds itself as the steps go by, and the
     sky behind it moves from dawn to night. */
  var build = $('#build');
  var buildParts = build ? $$('.bh-part', build) : [];
  var caption = $('#wz-build-caption span');
  var sky = $('#wz-sky');
  var SKY = ['dawn', 'dawn', 'day', 'day', 'gold', 'gold', 'night', 'night'];
  var brandName = (document.querySelector('.f-brand img') || {}).alt || 'NoogBlock';
  function captionFor(step) {
    var name = state.first || 'them';
    return [
      'Their world starts here',
      state.first ? 'A home for ' + state.first : 'A home of their own',
      state.username ? state.username + ' \u2014 that\u2019s them!' : 'Their name goes on the sign',
      state.first ? state.first + ', in their own colours' : 'Now they design themselves',
      'Locked with their own secret password',
      'Your rules \u2014 and up goes the shield',
      'Lights on. Ready when you are.',
      'Welcome to ' + brandName + ', ' + name + '!'
    ][step];
  }
  function paintWorld(step) {
    var stage = Math.min(step, 6);
    buildParts.forEach(function (part, i) { part.classList.toggle('on', i <= stage); });
    if (build) build.setAttribute('data-stage', String(stage));
    if (caption) {
      var text = captionFor(step);
      if (caption.textContent !== text) {
        caption.textContent = text;
        var pill = caption.parentNode;
        pill.classList.add('swap');
        void pill.offsetWidth;
        pill.classList.remove('swap');
      }
    }
    if (sky) {
      $$('.sky', sky).forEach(function (layer) { layer.classList.toggle('on', layer.classList.contains(SKY[step])); });
      sky.classList.toggle('is-night', SKY[step] === 'night');
    }
  }
  function paintSign() {
    var sign = $('#bh-name');
    if (sign) sign.textContent = state.username || 'Your name here';
  }
  function paintKid() {
    if (!build) return;
    build.style.setProperty('--k-skin', state.look.colors.head || '#f5cd30');
    build.style.setProperty('--k-shirt', state.look.colors.torso || '#0d69ac');
    build.style.setProperty('--k-pants', state.look.colors.left_leg || '#a4bd47');
  }
  function fireworks() {
    var fx = $('#bh-fx');
    if (!fx || (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches)) return;
    var colors = ['#ffd25e', '#ff8fb6', '#8fd0ff', '#8af0b6', '#c4a5ff'];
    var NS = 'http://www.w3.org/2000/svg';
    function burst(b) {
      var g = document.createElementNS(NS, 'g');
      g.setAttribute('transform', 'translate(' + (90 + Math.random() * 340).toFixed(0) + ' ' +
                     (30 + Math.random() * 110).toFixed(0) + ')');
      var inner = document.createElementNS(NS, 'g');
      inner.setAttribute('class', 'bh-burst');
      var color = colors[b % colors.length];
      for (var i = 0; i < 12; i++) {
        var a = i / 12 * Math.PI * 2;
        var line = document.createElementNS(NS, 'line');
        line.setAttribute('x1', (Math.cos(a) * 10).toFixed(1));
        line.setAttribute('y1', (Math.sin(a) * 10).toFixed(1));
        line.setAttribute('x2', (Math.cos(a) * 34).toFixed(1));
        line.setAttribute('y2', (Math.sin(a) * 34).toFixed(1));
        line.setAttribute('stroke', color);
        inner.appendChild(line);
      }
      g.appendChild(inner);
      fx.appendChild(g);
      setTimeout(function () { fx.removeChild(g); }, 1400);
    }
    for (var b = 0; b < 6; b++) setTimeout(burst.bind(null, b), b * 380);
  }

  /* -------------------------------------------------------- the names */
  $$('.wz-kid').forEach(function (n) { n.setAttribute('data-fallback', n.textContent); });
  function kid() { return state.first || 'your child'; }
  function possessive(name) { return /s$/i.test(name) ? name + '’' : name + '’s'; }
  function paintNames() {
    $$('.wz-kid').forEach(function (n) {
      var fallback = n.getAttribute('data-fallback');
      if (!state.first) { n.textContent = fallback; return; }
      n.textContent = /^Their$/.test(fallback) ? possessive(state.first) : state.first;
    });
  }

  function age() {
    if (!state.year) return null;
    var a = (boot.this_year || new Date().getFullYear()) - parseInt(state.year, 10);
    return a > 0 && a < 25 ? a : null;
  }

  /* ------------------------------------------------------- navigation */
  function show(step, backwards) {
    state.step = step;
    panes.forEach(function (pane) {
      var on = Number(pane.getAttribute('data-step')) === step;
      pane.classList.toggle('on', on);
      pane.classList.toggle('back', on && !!backwards);
    });
    bar.forEach(function (i, index) {
      i.classList.toggle('on', step > 0 && step < LAST && index === step - 1);
      i.classList.toggle('done', index < step - 1 || step === LAST);
    });
    var pane = panes[step];
    if (meta && pane) meta.textContent = step === 0 ? 'Before we start'
      : (step === LAST ? 'Ready to play' : 'Step ' + step + ' of 6 · ' + pane.getAttribute('data-title').replace('&rsquo;', '’'));
    foot.hidden = step === 0 || step === LAST;
    backBtn.style.visibility = step <= 1 ? 'hidden' : 'visible';
    nextBtn.innerHTML = step === 6
      ? FAM.esc(state.first ? 'Create ' + possessive(state.first) + ' account' : 'Create their account') +
        ' <svg class="f-ic f-arrow"><use href="#i-check"/></svg>'
      : 'Next <svg class="f-ic f-arrow"><use href="#i-arrow"/></svg>';
    paintWorld(step);
    if (step === 3) mountPreview();
    if (step === 5) renderRules();
    if (step === 6) renderReview();
    document.dispatchEvent(new CustomEvent('wz:step', { detail: { step: step } }));
    var focusable = pane && pane.querySelector('input:not([type=radio]), select');
    if (focusable && step > 0 && step < 6) setTimeout(function () { focusable.focus({ preventScroll: true }); }, 380);
    // back to the top, so the island can be seen taking its next piece
    if (window.scrollY > 0) window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function fieldMsg(name, text, bad) {
    var box = wz.querySelector('[data-field="' + name + '"]');
    if (!box) return;
    box.classList.toggle('is-bad', !!bad && !!text);
    var msg = box.querySelector('.f-fieldmsg');
    if (msg) msg.textContent = text || '';
  }

  function validate(step) {
    if (step === 1) {
      var ok = true;
      if (!state.first) { fieldMsg('first_name', 'Add their first name (only you see it).', true); ok = false; }
      if (!state.year) { fieldMsg('birth_year', 'Pick the year they were born.', true); ok = false; }
      return Promise.resolve(ok);
    }
    if (step === 2) {
      if (state.nameOk) return Promise.resolve(true);
      return checkName(true).then(function () { return state.nameOk; });
    }
    if (step === 4) {
      if (state.password.length < (boot.password_min || 6)) {
        fieldMsg('password', 'At least ' + (boot.password_min || 6) + ' characters, please.', true);
        return Promise.resolve(false);
      }
      if (state.password.toLowerCase() === state.username.toLowerCase()) {
        fieldMsg('password', 'It can’t be the same as the username.', true);
        return Promise.resolve(false);
      }
    }
    return Promise.resolve(true);
  }

  nextBtn.addEventListener('click', function () {
    if (state.busy) return;
    if (state.step === 6) { create(); return; }
    validate(state.step).then(function (ok) { if (ok) show(state.step + 1); });
  });
  backBtn.addEventListener('click', function () { if (state.step > 1) show(state.step - 1, true); });
  wz.addEventListener('click', function (e) {
    var go = e.target.closest('[data-go]');
    if (go) show(Number(go.getAttribute('data-go')), Number(go.getAttribute('data-go')) < state.step);
  });
  wz.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.target.matches('input.f-input') && state.step > 0 && state.step < 6) {
      e.preventDefault();
      nextBtn.click();
    }
  });

  var later = $('#wz-later');
  if (later) later.addEventListener('click', function () {
    later.classList.add('is-busy');
    FAM.post('/api/family/setup-later', {}).then(function (res) {
      location.href = (res && res.redirect) || boot.home || '/';
    });
  });

  /* --------------------------------------------------------- 1: who */
  var firstInput = $('#wz-first');
  var yearSelect = $('#wz-year');
  var ageNote = $('#wz-age');
  firstInput.addEventListener('input', function () {
    state.first = firstInput.value.replace(/\s+/g, ' ').trim().slice(0, 30);
    fieldMsg('first_name', '');
    paintNames();
    paintWorld(state.step);
    state.nameOk = false;
  });
  yearSelect.addEventListener('change', function () {
    state.year = yearSelect.value;
    fieldMsg('birth_year', '');
    var a = age();
    ageNote.textContent = a ? a + ' years old this year' : '';
    if (!state.rulesTouched) {
      var byAge = (boot.defaults_by_age || {})[String(a)];
      state.controls = clone(byAge || boot.defaults_unknown);
    }
  });

  /* ---------------------------------------------------- 2: username */
  var userInput = $('#wz-user');
  var avail = $('#wz-avail');
  var coach = $('#wz-coach');
  var coachBase = coach ? coach.innerHTML : '';
  var nameTimer = 0;
  var nameSeq = 0;
  function setAvail(kind, text) {
    avail.className = 'wz-avail ' + (kind || '');
    avail.innerHTML = text ? (kind === 'good' ? '<svg class="f-ic sm"><use href="#i-check"/></svg> ' : '') + FAM.esc(text) : '';
  }
  function checkName(now) {
    var value = userInput.value.trim();
    state.username = value;
    state.nameOk = false;
    if (!value) { setAvail('', ''); return Promise.resolve(); }
    if (!/^[A-Za-z0-9_]{3,20}$/.test(value)) {
      setAvail('bad', '3–20 letters, numbers or underscores.');
      return Promise.resolve();
    }
    setAvail('wait', 'Checking…');
    var seq = ++nameSeq;
    return FAM.post('/api/family/username', {
      kind: 'child', username: value, first_name: state.first, birth_year: state.year
    }).then(function (res) {
      if (seq !== nameSeq) return;
      if (!res.ok) { setAvail('bad', res.error || 'Couldn’t check that just now.'); return; }
      if (coach) {
        coach.innerHTML = (res.warnings || []).map(function (w) {
          return '<li class="warn">' + FAM.esc(w) + '</li>';
        }).join('') + coachBase;
      }
      if (res.available) {
        state.nameOk = true;
        setAvail('good', value + ' is free!' + ((res.warnings || []).length ? ' (see the tips below)' : ''));
      } else {
        setAvail('bad', res.problem || 'That one’s taken.');
        if (res.suggestions && res.suggestions.length) paintIdeas(res.suggestions);
      }
    });
  }
  userInput.addEventListener('input', function () {
    clearTimeout(nameTimer);
    state.nameOk = false;
    state.username = userInput.value.trim().slice(0, 20);
    paintSign();
    paintWorld(state.step);
    nameTimer = setTimeout(checkName, 360);
  });
  var ideas = $('#wz-ideas');
  function paintIdeas(list) {
    ideas.innerHTML = '';
    list.forEach(function (name, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'wz-idea';
      b.style.animation = 'f-pop .45s ' + (i * 0.06) + 's both var(--f-spring)';
      b.textContent = name;
      b.addEventListener('click', function () {
        userInput.value = name;
        state.username = name;
        paintSign();
        paintWorld(state.step);
        checkName(true);
      });
      ideas.appendChild(b);
    });
  }
  $('#wz-idea-btn').addEventListener('click', function () {
    FAM.get('/api/family/suggest').then(function (res) { if (res.ok) paintIdeas(res.suggestions || []); });
  });

  /* -------------------------------------------------------- 3: look */
  var PARTS = { skin: ['head', 'left_arm', 'right_arm'], shirt: ['torso'],
                pants: ['hips', 'left_leg', 'right_leg'] };
  var palette = (boot.palette || []).map(function (c) { return { name: c.name, hex: c.hex.toLowerCase() }; });
  var previewEl = $('#wz-preview');
  var preview = null;

  function descriptor() {
    var d = clone(base);
    d.colors = clone(state.look.colors);
    d.body_type = state.look.body_type;
    d.username = state.username || 'New player';
    return d;
  }
  function mountPreview() {
    $('#wz-preview-name').textContent = state.username || 'New player';
    if (preview || !window.Thumbs || !Thumbs.LivePreview || typeof Renderer === 'undefined') {
      if (preview) preview.setDescriptor(descriptor());
      return;
    }
    preview = new Thumbs.LivePreview(previewEl, descriptor());
    if (preview.failed) { preview = null; return; }
    preview.skyMode = 'stage';
    preview.applyTheme();
    preview.margin = 0.08;
    preview.markHome();
    previewEl.classList.add('live');
    if (Thumbs.loadCatalog) Thumbs.loadCatalog();
  }
  function paintSwatches() {
    $$('.wz-swatches').forEach(function (box) {
      var part = box.getAttribute('data-part');
      var current = state.look.colors[PARTS[part][0]];
      box.innerHTML = '';
      palette.forEach(function (c) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'wz-sw' + (c.hex === current ? ' on' : '');
        b.style.setProperty('--c', c.hex);
        b.setAttribute('role', 'radio');
        b.setAttribute('aria-checked', c.hex === current ? 'true' : 'false');
        b.setAttribute('aria-label', c.name);
        b.title = c.name;
        b.addEventListener('click', function () {
          PARTS[part].forEach(function (p) { state.look.colors[p] = c.hex; });
          paintSwatches();
          paintKid();
          if (preview) preview.setDescriptor(descriptor());
        });
        box.appendChild(b);
      });
    });
  }
  paintSwatches();
  $$('input[name="wz-body"]').forEach(function (r) {
    r.addEventListener('change', function () {
      state.look.body_type = r.value;
      if (preview) preview.setDescriptor(descriptor());
    });
  });
  $('#wz-shuffle').addEventListener('click', function () {
    var pick = function () { return palette[Math.floor(Math.random() * palette.length)].hex; };
    var skins = ['#f5cd30', '#cc8e69', '#a75fd1', '#e8bd8c', '#7c503a', '#f2f3f3', '#0d69ac'];
    var skin = skins[Math.floor(Math.random() * skins.length)];
    PARTS.skin.forEach(function (p) { state.look.colors[p] = skin; });
    var shirt = pick();
    PARTS.shirt.forEach(function (p) { state.look.colors[p] = shirt; });
    var pants = pick();
    PARTS.pants.forEach(function (p) { state.look.colors[p] = pants; });
    paintSwatches();
    paintKid();
    if (preview) preview.setDescriptor(descriptor());
  });

  /* ---------------------------------------------------- 4: password */
  var passInput = $('#wz-pass');
  passInput.addEventListener('input', function () {
    state.password = passInput.value;
    fieldMsg('password', '');
  });
  var WORDS_A = ['Tiger', 'Rocket', 'Pancake', 'Comet', 'Dragon', 'Otter', 'Pickle', 'Banana', 'Thunder',
                 'Cookie', 'Penguin', 'Bubble', 'Wizard', 'Cactus', 'Nugget', 'Planet', 'Mango', 'Puzzle'];
  var WORDS_B = ['Jump', 'Dance', 'Zoom', 'Party', 'Splash', 'Flip', 'Giggle', 'Sprint', 'Bounce',
                 'Wobble', 'Sparkle', 'Rumble', 'Twirl', 'Hop', 'Roar', 'Whistle'];
  $('#wz-make-pass').addEventListener('click', function () {
    var a = WORDS_A[Math.floor(Math.random() * WORDS_A.length)];
    var b = WORDS_B[Math.floor(Math.random() * WORDS_B.length)];
    passInput.value = a + '-' + b + '-' + (10 + Math.floor(Math.random() * 90));
    passInput.type = 'text';
    state.password = passInput.value;
    fieldMsg('password', '');
    passInput.classList.remove('wz-flash');
    void passInput.offsetWidth;
    passInput.classList.add('wz-flash');
  });

  /* ------------------------------------------------------- 5: rules */
  var rulesBox = $('#wz-rules');
  var labels = boot.labels || {};
  function chip(text, on, onClick) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'wz-chip' + (on ? ' on' : '');
    b.textContent = text;
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
    b.addEventListener('click', function () { state.rulesTouched = true; onClick(); renderRules(); });
    return b;
  }
  function card(icon, title, sub, extra) {
    var d = document.createElement('div');
    d.className = 'wz-rule';
    d.innerHTML = '<div class="wz-rule-head"><span class="ic"><svg class="f-ic"><use href="#i-' + icon +
      '"/></svg></span><div><h3>' + FAM.esc(title) + '</h3>' + (sub ? '<p>' + FAM.esc(sub) + '</p>' : '') +
      '</div></div>';
    if (extra) d.querySelector('.wz-rule-head').appendChild(extra);
    return d;
  }
  function switchEl(on, onChange, label) {
    var l = document.createElement('label');
    l.className = 'f-switch';
    l.innerHTML = '<input type="checkbox"' + (on ? ' checked' : '') + ' aria-label="' + FAM.esc(label) + '"><i></i>';
    l.querySelector('input').addEventListener('change', function (e) {
      state.rulesTouched = true;
      onChange(e.target.checked);
      renderRules();
    });
    return l;
  }
  function minuteChips(key) {
    var wrap = document.createElement('div');
    wrap.className = 'wz-chips';
    var current = state.controls[key];
    (boot.minutes || [15, 30, 45, 60, 90, 120, 180, 240]).forEach(function (m) {
      wrap.appendChild(chip(FAM.minutesLabel(m), current === m, function () { state.controls[key] = m; }));
    });
    wrap.appendChild(chip('No limit', current === null, function () { state.controls[key] = null; }));
    wrap.appendChild(chip('No games', current === 0, function () { state.controls[key] = 0; }));
    return wrap;
  }
  function choiceChips(key) {
    var wrap = document.createElement('div');
    wrap.className = 'wz-chips';
    var options = labels[key] || {};
    Object.keys(options).forEach(function (value) {
      wrap.appendChild(chip(options[value], state.controls[key] === value,
        function () { state.controls[key] = value; }));
    });
    return wrap;
  }
  function timeSelect(key, from, to) {
    var s = document.createElement('select');
    s.className = 'f-select';
    s.setAttribute('aria-label', key === 'quiet_start' ? 'Quiet hours start' : 'Quiet hours end');
    for (var h = from; h <= to; h++) {
      [0, 30].forEach(function (m) {
        var value = (h % 24 < 10 ? '0' : '') + (h % 24) + ':' + (m ? '30' : '00');
        var o = document.createElement('option');
        o.value = value;
        o.textContent = FAM.clock(value);
        if (value === state.controls[key]) o.selected = true;
        s.appendChild(o);
      });
    }
    if (!Array.prototype.some.call(s.options, function (o) { return o.selected; })) {
      var extra = document.createElement('option');
      extra.value = state.controls[key];
      extra.textContent = FAM.clock(state.controls[key]);
      extra.selected = true;
      s.insertBefore(extra, s.firstChild);
    }
    s.addEventListener('change', function () { state.rulesTouched = true; state.controls[key] = s.value; });
    return s;
  }
  function renderRules() {
    var c = state.controls;
    var a = age();
    var note = $('#wz-age-note span');
    if (note) note.textContent = a ? 'Suggested starting rules for a ' + a + '-year-old' : 'Suggested starting rules';
    rulesBox.innerHTML = '';
    var t1 = card('clock', 'Play time on school days', 'Monday to Friday');
    t1.appendChild(minuteChips('weekday_minutes'));
    rulesBox.appendChild(t1);
    var t2 = card('sun', 'Play time on weekends', 'Saturday and Sunday');
    t2.appendChild(minuteChips('weekend_minutes'));
    rulesBox.appendChild(t2);
    var q = card('moon', 'Quiet hours', 'No games at bedtime', switchEl(c.quiet, function (on) { c.quiet = on; }, 'Quiet hours'));
    if (c.quiet) {
      var times = document.createElement('div');
      times.className = 'wz-times';
      times.appendChild(document.createTextNode('From '));
      times.appendChild(timeSelect('quiet_start', 17, 23));
      times.appendChild(document.createTextNode(' until '));
      times.appendChild(timeSelect('quiet_end', 5, 10));
      q.appendChild(times);
    }
    rulesBox.appendChild(q);
    var f = card('user-check', 'New friends', (boot.help || {}).friends);
    f.appendChild(choiceChips('friends'));
    rulesBox.appendChild(f);
    var m = card('message', 'Private messages', (boot.help || {}).messages);
    m.appendChild(choiceChips('messages'));
    rulesBox.appendChild(m);
    var ch = card('chat-shield', 'In-game chat', (boot.help || {}).chat);
    ch.appendChild(choiceChips('chat'));
    rulesBox.appendChild(ch);
    var w = card('globe', 'Worlds they can play', 'Each comes with a short parent’s guide');
    (boot.worlds || []).forEach(function (world) {
      var row = document.createElement('div');
      row.className = 'wz-world';
      var allowed = c.worlds_blocked.indexOf(world.id) < 0;
      row.innerHTML = '<span class="wz-world-dot" style="--c:' + FAM.esc(world.color) + '"></span>' +
        '<span class="wz-world-text"><b>' + FAM.esc(world.name) + ' <span class="f-chip ' +
        (world.intensity === 'gentle' ? 'good' : world.intensity === 'intense' ? 'grape' : 'blue') + '">' +
        FAM.esc(world.intensity_label) + '</span></b><small>' + FAM.esc(world.kind) + ' · ' +
        FAM.esc(world.note) + '</small></span>';
      row.appendChild(switchEl(allowed, function (on) {
        var i = c.worlds_blocked.indexOf(world.id);
        if (on && i >= 0) c.worlds_blocked.splice(i, 1);
        if (!on && i < 0) c.worlds_blocked.push(world.id);
      }, 'Allow ' + world.name));
      w.appendChild(row);
    });
    rulesBox.appendChild(w);
    rulesBox.appendChild(card('coin', 'Spend play money', (boot.help || {}).spending,
      switchEl(c.spending, function (on) { c.spending = on; }, 'Spending')));
    rulesBox.appendChild(card('box', 'Open crates', (boot.help || {}).crates,
      switchEl(c.crates, function (on) { c.crates = on; }, 'Crates')));
  }

  /* ------------------------------------------------------ 6: review */
  function renderReview() {
    var c = state.controls;
    var a = age();
    var box = $('#wz-review');
    var dots = ['head', 'torso', 'left_leg'].map(function (p) {
      return '<span class="wz-world-dot" style="--c:' + FAM.esc(state.look.colors[p]) + ';width:28px;height:28px"></span>';
    }).join('');
    var allowed = (boot.worlds || []).filter(function (w) { return c.worlds_blocked.indexOf(w.id) < 0; }).length;
    function rc(label, value, step, extra) {
      return '<div class="wz-review-card"><div><div class="lbl">' + label + '</div><div class="val">' + value +
        '</div></div>' + (extra || '') + '<button class="f-btn f-btn-sm f-btn-ghost" type="button" data-go="' + step +
        '">Change</button></div>';
    }
    box.innerHTML =
      rc('Who', FAM.esc(state.first) + (a ? ' &middot; ' + a : ''), 1) +
      rc('Username', FAM.esc(state.username), 2) +
      rc('Password', '<span id="wz-review-pass">' + '•'.repeat(Math.min(12, state.password.length)) +
         '</span>', 4, '<button class="f-btn f-btn-sm f-btn-soft" type="button" id="wz-show-pass">Show</button>') +
      rc('Look', '<span style="display:inline-flex;gap:6px">' + dots + '</span>', 3) +
      '<div class="wz-review-rules">' +
        '<div><span>School days</span><b>' + FAM.esc(FAM.minutesLabel(c.weekday_minutes)) + '</b></div>' +
        '<div><span>Weekends</span><b>' + FAM.esc(FAM.minutesLabel(c.weekend_minutes)) + '</b></div>' +
        '<div><span>Quiet hours</span><b>' + (c.quiet ? FAM.esc(FAM.clock(c.quiet_start) + ' – ' + FAM.clock(c.quiet_end)) : 'Off') + '</b></div>' +
        '<div><span>New friends</span><b>' + FAM.esc((labels.friends || {})[c.friends] || c.friends) + '</b></div>' +
        '<div><span>Messages</span><b>' + FAM.esc((labels.messages || {})[c.messages] || c.messages) + '</b></div>' +
        '<div><span>Game chat</span><b>' + FAM.esc((labels.chat || {})[c.chat] || c.chat) + '</b></div>' +
        '<div><span>Worlds</span><b>' + allowed + ' of ' + (boot.worlds || []).length + ' on</b></div>' +
        '<div><span>Spending &middot; crates</span><b>' + (c.spending ? 'On' : 'Off') + ' &middot; ' + (c.crates ? 'On' : 'Off') + '</b></div>' +
      '</div>' +
      '<div style="text-align:right"><button class="f-btn f-btn-sm f-btn-ghost" type="button" data-go="5">Change the rules</button></div>';
    var showBtn = $('#wz-show-pass');
    if (showBtn) showBtn.addEventListener('click', function () {
      var span = $('#wz-review-pass');
      var hidden = span.textContent.charAt(0) === '•';
      span.textContent = hidden ? state.password : '•'.repeat(Math.min(12, state.password.length));
      showBtn.textContent = hidden ? 'Hide' : 'Show';
    });
  }

  var stepOf = { first_name: 1, birth_year: 1, username: 2, password: 4 };
  function create() {
    state.busy = true;
    nextBtn.classList.add('is-busy');
    var err = $('#wz-error');
    err.classList.add('f-hidden');
    FAM.post('/api/family/children', {
      first_name: state.first, birth_year: state.year, username: state.username,
      password: state.password, look: state.look, controls: state.controls
    }).then(function (res) {
      state.busy = false;
      nextBtn.classList.remove('is-busy');
      if (!res.ok) {
        if (res.field && stepOf[res.field]) {
          show(stepOf[res.field], true);
          if (res.field === 'username') { state.nameOk = false; setAvail('bad', res.error); }
          else fieldMsg(res.field, res.error, true);
        } else {
          err.querySelector('span').textContent = res.error || 'Something went wrong. Please try again.';
          err.classList.remove('f-hidden');
        }
        return;
      }
      state.child = res.child;
      $('#wz-card-site').textContent = location.host;
      $('#wz-card-user').textContent = res.child.username;
      $('#wz-card-pass').textContent = state.password;
      $('#wz-card-title').textContent = possessive(res.child.first_name) + ' sign-in';
      $('#wz-signin-label').textContent = 'Sign ' + res.child.first_name + ' in on this computer';
      $('#wz-dashboard').href = res.dashboard;
      if (res.slots_left > 0) $('#wz-another').classList.remove('f-hidden');
      show(LAST);
      confetti();
      fireworks();
    });
  }

  /* -------------------------------------------------------- 7: done */
  $('#wz-signin-here').addEventListener('click', function () {
    if (!state.child) return;
    var btn = this;
    btn.classList.add('is-busy');
    FAM.post('/api/family/child/' + state.child.id + '/signin-here', {}).then(function (res) {
      if (res.ok) { location.href = res.redirect || '/'; return; }
      btn.classList.remove('is-busy');
      FAM.toast(res.error || 'Couldn’t sign them in.', 'bad');
    });
  });
  $('#wz-print').addEventListener('click', function () { window.print(); });

  function confetti() {
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var box = document.createElement('div');
    box.className = 'wz-confetti';
    var colors = ['#2b67f6', '#ff5b4d', '#ffbf1f', '#18b06f', '#7a5af8', '#3fb8f5'];
    for (var i = 0; i < 140; i++) {
      var p = document.createElement('i');
      p.style.left = (Math.random() * 100) + 'vw';
      p.style.background = colors[i % colors.length];
      p.style.setProperty('--x', ((Math.random() - 0.5) * 240) + 'px');
      p.style.setProperty('--r', (360 + Math.random() * 720) + 'deg');
      p.style.setProperty('--t', (2 + Math.random() * 2.2) + 's');
      p.style.animationDelay = (Math.random() * 0.6) + 's';
      if (i % 3 === 0) p.style.borderRadius = '50%';
      box.appendChild(p);
    }
    document.body.appendChild(box);
    setTimeout(function () { box.remove(); }, 5200);
  }

  paintKid();
  paintSign();
  show(0);
})();
