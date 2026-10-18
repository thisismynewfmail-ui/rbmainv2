/* BLOCKHAVEN -- pets on the web pages.

   PetStages runs every live pet on a page -- the adoption cards and the
   fitting room on the Pets shelf (templates/market_pets.html), the teaser on
   the market, the pet editor -- through ONE offscreen WebGL renderer, blitted
   into each stage's own 2D canvas.  Six pets on a page cost one context, not
   six, and a stage scrolled out of view or on a hidden tab costs nothing.

   Any <canvas class="pt-live" data-pet="{...}"> on the page becomes a stage
   by itself; the pet in it entertains herself (Pet.Showcase, chosen by her
   persona tags), can be turned by dragging, and waves when her card is
   hovered.  A stage can also be *directed* (PetStages.add's ``director``):
   something else decides where she stands and what she does, builds a room
   round her, places the camera, sets the lights and paints over the frame --
   the Pet Zone (pet_zone.js) is one.  A directed stage may ask for its own
   size in pixels; it is drawn into a corner of the shared canvas, which
   grows to fit the biggest, so it is still one context.  The rest of this
   file is the shop: try-on, looks, the wardrobe tabs and buying through the
   market's till (Crates.buy). */
(function (global) {
  'use strict';

  var OFF_W = 480, OFF_H = 560;     // 6:7, the shape of every pet stage
  var MAX_W = 1600, MAX_H = 1200;   // the most a directed stage may ask for
  var FOV = 30;
  var REST_YAW = -0.32;

  var PetStages = { list: [], renderer: null, failed: false, running: false, last: 0 };

  function reduced() {
    return global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function ensure() {
    if (PetStages.renderer || PetStages.failed) return PetStages.renderer;
    if (!global.Renderer || !global.Pet) { PetStages.failed = true; return null; }
    var canvas = document.createElement('canvas');
    canvas.width = OFF_W; canvas.height = OFF_H;
    canvas.style.cssText = 'position:absolute;left:-10000px;top:0;width:' + OFF_W +
      'px;height:' + OFF_H + 'px';
    canvas.setAttribute('aria-hidden', 'true');
    document.body.appendChild(canvas);
    var renderer = new Renderer(canvas, { preserveDrawingBuffer: true, antialias: true,
                                          transparent: true });
    if (renderer.failed) { PetStages.failed = true; return null; }
    renderer.renderScale = 1;
    renderer.pixelRatio = 1;
    renderer.resize();
    renderer.far = 120;
    renderer.setSky({ top: '#a8cdea', horizon: '#f0f6fb', sun: [0.35, 0.85, 0.5],
                      clouds: 0, tint: '#ffffff' });
    renderer.setAmbient('#9fb3c8');
    renderer.buildStatic([]);
    // the lights every stage starts from: a director that dims them for
    // its own stage has them put back before the next one draws
    PetStages.lights = { sun: renderer.sunColor.slice(), sky: renderer.skyAmbient.slice(),
                         ground: renderer.groundAmbient.slice(), dir: renderer.sky.sun.slice() };
    PetStages.renderer = renderer;
    return renderer;
  }

  /* Draw the next stage at w x h pixels: the shared canvas grows (once) to
     hold the biggest stage asked for, and each draws into its bottom-left
     corner -- which is where a WebGL viewport at the origin lands. */
  function fit(renderer, w, h) {
    var c = renderer.canvas;
    if (c.width < w || c.height < h) {
      c.width = Math.max(c.width, w);
      c.height = Math.max(c.height, h);
      c.style.width = c.width + 'px';
      c.style.height = c.height + 'px';
    }
    renderer.width = w;
    renderer.height = h;
    renderer.aspect = w / Math.max(1, h);
  }

  function restoreLights(renderer) {
    var L = PetStages.lights;
    if (!L) return;
    renderer.sunColor = L.sun.slice();
    renderer.skyAmbient = L.sky.slice();
    renderer.groundAmbient = L.ground.slice();
    renderer.sky.sun = L.dir.slice();
  }

  function parse(raw) {
    try { return JSON.parse(raw); } catch (e) { return null; }
  }

  /* One stage: a canvas, the pet in it and what she is doing.

     opts.director, for a stage something else runs (all optional):
       step(dt, stage)            -> her pose this frame; may move stage.pos
                                     and turn stage.yaw
       camera(stage)              -> { eye, target, fov }
       light(renderer, stage)     set the lights for this stage only
       scene(renderer, stage)     push whatever else is in the frame
       overlay(ctx, stage, renderer)  paint over the finished frame
       pixels(stage)              -> [w, h], the size to render at
     opts.drag === false leaves the pointer to the director. */
  function Stage(canvas, pet, opts) {
    opts = opts || {};
    this.canvas = canvas;
    this.pet = pet;
    this.show = new Pet.Showcase(pet, { only: opts.only, calm: opts.calm, tone: opts.tone });
    this.time = Math.random() * 10;
    this.yaw = opts.yaw === undefined ? REST_YAW : opts.yaw;
    this.restYaw = this.yaw;
    this.pos = [0, 0, 0];
    this.idleSince = 0;
    this.visible = true;
    this.dist = opts.dist || 6.9;
    this.focus = opts.focus || 1.52;
    this.tilt = opts.tilt === undefined ? 0.13 : opts.tilt;
    this.shadow = opts.shadow !== false;
    this.director = opts.director || null;
    if (opts.drag !== false) this.bindDrag();
  }

  Stage.prototype.setPet = function (pet) {
    var keep = this.show;
    this.pet = pet;
    this.show = new Pet.Showcase(pet, { only: keep.only, calm: keep.calm, tone: keep.tone });
    this.show.pose = keep.pose;           // no snap: she carries on from here
  };

  Stage.prototype.play = function (action) {
    if (this.show) this.show.play(action);
  };

  Stage.prototype.bindDrag = function () {
    var self = this, canvas = this.canvas;
    var down = false, decided = false, touch = false, sx = 0, sy = 0, lx = 0;
    canvas.style.touchAction = 'pan-y';
    canvas.addEventListener('pointerdown', function (e) {
      down = true; touch = e.pointerType === 'touch'; decided = !touch;
      sx = lx = e.clientX; sy = e.clientY;
      if (!touch) { try { canvas.setPointerCapture(e.pointerId); } catch (err) {} }
    });
    canvas.addEventListener('pointermove', function (e) {
      if (!down) return;
      if (!decided) {
        if (Math.abs(e.clientX - sx) < 6 && Math.abs(e.clientY - sy) < 6) return;
        if (Math.abs(e.clientY - sy) > Math.abs(e.clientX - sx)) { down = false; return; }
        decided = true;
        canvas.style.touchAction = 'none';
        try { canvas.setPointerCapture(e.pointerId); } catch (err) {}
      }
      self.yaw += (e.clientX - lx) * 0.014;
      lx = e.clientX;
      self.idleSince = 0;
      self.dragged = true;
    });
    ['pointerup', 'pointercancel', 'pointerleave'].forEach(function (name) {
      canvas.addEventListener(name, function () {
        down = false; decided = false; canvas.style.touchAction = 'pan-y';
      });
    });
  };

  Stage.prototype.draw = function (renderer, dt) {
    var d = this.director;
    this.time += dt;
    var pose;
    if (d && d.step) {
      pose = d.step(dt, this);
    } else {
      // a turned pet drifts back to face you after a while
      this.idleSince += dt;
      if (this.idleSince > 2.5) this.yaw += (this.restYaw - this.yaw) * Math.min(1, dt * 1.6);
      pose = this.show.step(dt);
    }
    var size = (d && d.pixels) ? d.pixels(this) : [OFF_W, OFF_H];
    var w = Math.max(1, Math.min(MAX_W, Math.round(size[0])));
    var h = Math.max(1, Math.min(MAX_H, Math.round(size[1])));
    fit(renderer, w, h);
    var at = this.pos;
    var parts = Pet.build(this.pet, { position: at, yaw: this.yaw, pose: pose,
                                      time: this.time });
    renderer.beginFrame(dt);
    for (var i = 0; i < parts.length; i++) renderer.push(parts[i]);
    if (this.shadow) {
      var lift = (pose.bob || 0) + (pose.float || 0);
      var k = Math.max(0.55, 1 - lift * 0.6);
      renderer.pushRaw('cyl', at[0], at[1] + 0.015, at[2], 0, 0, 0, 1.55 * k, 0.03, 1.3 * k,
                       [0.2, 0.16, 0.24], 0.3 * k, 0, 0, 0.9, null);
    }
    if (d && d.scene) d.scene(renderer, this);
    var cam = (d && d.camera) ? d.camera(this) : null;
    if (cam) {
      renderer.setCameraMatrix(cam.eye, cam.target, cam.fov || FOV);
    } else {
      var f = [0, this.focus, 0];
      var eye = [Math.sin(0) * this.dist, this.focus + Math.sin(this.tilt) * this.dist,
                 Math.cos(this.tilt) * this.dist];
      renderer.setCameraMatrix(eye, f, FOV);
    }
    if (d && d.light) d.light(renderer, this);
    renderer.render();
    if (d && d.light) restoreLights(renderer);
    var ctx = this.canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(renderer.canvas, 0, renderer.canvas.height - h, w, h,
                  0, 0, this.canvas.width, this.canvas.height);
    if (d && d.overlay) d.overlay(ctx, this, renderer);
  };

  function tick(now) {
    if (!PetStages.list.length) { PetStages.running = false; return; }
    requestAnimationFrame(tick);
    var dt = Math.min(0.05, (now - (PetStages.last || now)) / 1000);
    PetStages.last = now;
    if (document.hidden) return;
    var renderer = ensure();
    if (!renderer) return;
    // drop stages whose canvas has left the page (a closed dialog)
    PetStages.list = PetStages.list.filter(function (s) { return document.body.contains(s.canvas); });
    // reduced motion slows a showcase right down; a directed stage keeps
    // its own time (its director has things to finish) and calms itself
    var slow = reduced();
    PetStages.list.forEach(function (stage) {
      if (!stage.visible) return;
      stage.draw(renderer, slow && !stage.director ? dt * 0.35 : dt);
    });
  }

  function start() {
    if (PetStages.running) return;
    PetStages.running = true;
    PetStages.last = 0;
    requestAnimationFrame(tick);
  }

  var observer = global.IntersectionObserver ? new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      var stage = entry.target.__petStage;
      if (stage) stage.visible = entry.isIntersecting;
    });
  }, { rootMargin: '120px' }) : null;

  PetStages.add = function (canvas, pet, opts) {
    if (!canvas || !pet || !global.Pet) return null;
    if (canvas.__petStage) { canvas.__petStage.setPet(pet); return canvas.__petStage; }
    if (!ensure()) return null;
    var stage = new Stage(canvas, pet, opts);
    canvas.__petStage = stage;
    PetStages.list.push(stage);
    if (observer) observer.observe(canvas);
    start();
    return stage;
  };

  /* One still frame of a list of parts into a canvas, through the shared
     renderer: the portraits and icons on a page that already runs a stage,
     without a second context.  cam is { eye, target, fov }. */
  PetStages.still = function (canvas, parts, cam) {
    var renderer = canvas && ensure();
    if (!renderer) return false;
    var w = canvas.width, h = canvas.height;
    fit(renderer, w, h);
    renderer.beginFrame(0);
    for (var i = 0; i < parts.length; i++) renderer.push(parts[i]);
    renderer.setCameraMatrix(cam.eye, cam.target, cam.fov || FOV);
    renderer.render();
    var ctx = canvas.getContext('2d');
    if (!ctx) return false;
    ctx.clearRect(0, 0, w, h);
    ctx.drawImage(renderer.canvas, 0, renderer.canvas.height - h, w, h, 0, 0, w, h);
    return true;
  };

  /* Turn every canvas.pt-live[data-pet] on the page into a stage. */
  PetStages.scan = function (root) {
    (root || document).querySelectorAll('canvas.pt-live[data-pet]').forEach(function (canvas) {
      if (canvas.__petStage) return;
      var pet = parse(canvas.dataset.pet);
      if (!pet) return;
      PetStages.add(canvas, pet, {
        only: canvas.dataset.only || null,
        calm: canvas.dataset.calm === '1',
        dist: canvas.dataset.dist ? parseFloat(canvas.dataset.dist) : undefined,
        focus: canvas.dataset.focus ? parseFloat(canvas.dataset.focus) : undefined
      });
    });
  };

  global.PetStages = PetStages;

  // ================================================================ the shop
  /* Three looks per pet to try on the card: her own colours and two others,
     so a buyer can see she is theirs to colour before they buy her. */
  var LOOKS = {
    fern: [null,
      { hair: '#c8642a', outfit: '#7a3a1c', accent: '#f2b14a', eyes: '#e08a2a', legs: '#3a2418' },
      { hair: '#f4a6c8', outfit: '#e25d9a', accent: '#ffe1ef', eyes: '#d6448a', legs: '#ffffff' }],
    ember: [null,
      { hair: '#3a8cff', outfit: '#1c2238', accent: '#9ff3ff', eyes: '#6fd8ff', legs: '#141826' },
      { hair: '#c63bff', outfit: '#2a1636', accent: '#7dff8a', eyes: '#b26bff', legs: '#1c1022' }],
    luna: [null,
      { hair: '#f2f0ff', outfit: '#9c8cd8', accent: '#ffe58a', eyes: '#ffcf5a', legs: '#ffffff' },
      { hair: '#1a1a22', outfit: '#3a0f2a', accent: '#ff5c8a', eyes: '#ff3d6a', legs: '#1a1a22' }],
    mochi: [null,
      { hair: '#8a5a3a', outfit: '#c9a27a', accent: '#f2e4cf', eyes: '#6a3a1c', legs: '#f2e4cf' },
      { hair: '#9fd8ff', outfit: '#d5ecff', accent: '#ffffff', eyes: '#3a8cd8', legs: '#ffffff' }],
    pixel: [null,
      { hair: '#ff3d8f', outfit: '#1a1424', accent: '#ff7ad9', eyes: '#ff7ad9', legs: '#2a2236' },
      { hair: '#ffd23a', outfit: '#202a1c', accent: '#9cff4a', eyes: '#9cff4a', legs: '#2a3424' }]
  };

  function cloneWith(pet, patch) {
    var out = {};
    Object.keys(pet).forEach(function (k) { out[k] = pet[k]; });
    Object.keys(patch).forEach(function (k) { out[k] = patch[k]; });
    return out;
  }

  function bindCards(root) {
    root.querySelectorAll('.pt-card').forEach(function (card) {
      var canvas = card.querySelector('canvas.pt-live');
      var stage = canvas && canvas.__petStage;
      if (!stage) return;
      var base = stage.pet;
      var species = card.dataset.species;
      // paint the look buttons in their colours
      card.querySelectorAll('.pt-look').forEach(function (btn) {
        var look = (LOOKS[species] || [])[parseInt(btn.dataset.look, 10)];
        var colours = look || base.colors || {};
        btn.style.setProperty('--l1', colours.hair || '#888');
        btn.style.setProperty('--l2', colours.outfit || '#666');
        btn.style.setProperty('--l3', colours.accent || '#aaa');
        btn.addEventListener('click', function () {
          card.querySelectorAll('.pt-look').forEach(function (b) {
            b.classList.toggle('on', b === btn);
            b.setAttribute('aria-pressed', String(b === btn));
          });
          var colors = {};
          Object.keys(base.colors || {}).forEach(function (k) { colors[k] = base.colors[k]; });
          if (look) Object.keys(look).forEach(function (k) { colors[k] = look[k]; });
          stage.setPet(cloneWith(base, { colors: colors }));
          stage.play('twirl');
        });
      });
      var waved = 0;
      function greet() {
        var now = Date.now();
        if (now - waved < 2500) return;
        waved = now;
        stage.play(Math.random() < 0.7 ? 'wave' : 'curtsy');
      }
      card.addEventListener('pointerenter', function (e) { if (e.pointerType !== 'touch') greet(); });
      card.addEventListener('focusin', greet);
      canvas.addEventListener('click', function () {
        if (stage.dragged) { stage.dragged = false; return; }
        var pool = stage.show.repertoire();
        stage.play(pool[(Math.random() * pool.length) | 0]);
      });
    });
  }

  // ------------------------------------------------------------- fitting room
  function bindFitting(root) {
    var canvas = root.querySelector('#pt-fit');
    var stage = canvas && canvas.__petStage;
    if (!stage) return;
    var mine = parse((root.querySelector('#pt-mine') || {}).textContent || '') || null;
    var who = root.querySelector('#pt-fit-who');
    var model = stage.pet;
    var trying = {};
    function refresh(action) {
      var items = {};
      Object.keys(model.items || {}).forEach(function (k) { items[k] = model.items[k]; });
      Object.keys(trying).forEach(function (k) {
        if (trying[k]) items[k] = trying[k]; else delete items[k];
      });
      stage.setPet(cloneWith(model, { items: items }));
      if (action) stage.play(action);
      root.querySelectorAll('.pt-item').forEach(function (card) {
        var on = trying[card.dataset.slot] && trying[card.dataset.slot].item_id === card.dataset.try;
        card.classList.toggle('trying', !!on);
        card.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
    }
    root.querySelectorAll('.pt-who').forEach(function (btn) {
      btn.addEventListener('click', function () {
        if (!mine) return;
        model = mine[parseInt(btn.dataset.who, 10)] || model;
        root.querySelectorAll('.pt-who').forEach(function (b) {
          b.classList.toggle('on', b === btn);
          b.setAttribute('aria-pressed', String(b === btn));
        });
        if (who) who.textContent = 'Trying things on ' + model.name;
        refresh('wave');
      });
    });
    function tryOn(card) {
      var id = card.dataset.try, slot = card.dataset.slot;
      Thumbs.loadCatalog().then(function (catalog) {
        var item = catalog[id];
        if (!item) return;
        if (trying[slot] && trying[slot].item_id === id) {
          trying[slot] = null;              // tapping it again takes it off
          refresh('shake');
          return;
        }
        trying[slot] = { item_id: id, slot: slot, data: item.data, name: item.name };
        var cheer = { pet_hat: 'pose', pet_face: 'giggle', pet_neck: 'nod', pet_pin: 'heart',
                      pet_top: 'twirl', pet_back: 'twirl' }[slot] || 'wave';
        refresh(cheer);
        if (slot === 'pet_back') stage.yaw = Math.PI * 0.85;     // show her back
        stage.idleSince = 0;
        if (global.matchMedia && global.matchMedia('(max-width: 720px)').matches) {
          var fit = root.querySelector('.pt-fitting');
          if (fit && fit.getBoundingClientRect().bottom < 60) {
            fit.scrollIntoView({ behavior: reduced() ? 'auto' : 'smooth', block: 'start' });
          }
        }
      });
    }
    root.addEventListener('click', function (e) {
      if (e.target.closest('[data-buy], a')) return;
      var card = e.target.closest('.pt-item[data-try]');
      if (card) tryOn(card);
    });
    root.addEventListener('keydown', function (e) {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      var card = e.target.closest('.pt-item[data-try]');
      if (card && e.target === card) { e.preventDefault(); tryOn(card); }
    });
    var clear = root.querySelector('#pt-fit-clear');
    if (clear) clear.addEventListener('click', function () {
      Object.keys(trying).forEach(function (k) { trying[k] = null; });
      refresh('stretch');
    });
    PetStages.fitting = { stage: stage, tryOn: tryOn };
  }

  // ------------------------------------------------------------------ tabs
  function bindTabs(root) {
    root.querySelectorAll('[data-slot-tab]').forEach(function (tab) {
      tab.addEventListener('click', function () {
        var slot = tab.dataset.slotTab;
        root.querySelectorAll('[data-slot-tab]').forEach(function (t) {
          t.classList.toggle('on', t === tab);
          t.setAttribute('aria-selected', String(t === tab));
        });
        root.querySelectorAll('[data-slot-panel]').forEach(function (panel) {
          panel.classList.toggle('hidden', panel.dataset.slotPanel !== slot);
        });
        if (global.Thumbs) Thumbs.rescan();
        try { history.replaceState(null, '', '?slot=' + slot + '#wardrobe'); } catch (e) {}
      });
    });
  }

  // ---------------------------------------------------------------- buying
  function celebrate(name, species, invId) {
    var pet = { species: species, items: {}, tags: [] };
    var body = '<div class="pt-meet"><canvas class="pt-live pt-meet-stage" width="300" height="350" ' +
      'data-only="cheer" data-pet="' + Site.escape(JSON.stringify(pet)) + '"></canvas>' +
      '<p><b>' + Site.escape(name) + ' is yours!</b> She is following you already &mdash; into ' +
      'every world, at your side on your profile.</p><p class="tiny">Give her a name, pick her ' +
      'persona and dress her up in Edit Pet.</p></div>';
    var dialog = Site.dialog({ title: 'Welcome home, ' + name + '!', bodyHtml: body,
                               confirm: 'Dress her up', cancel: 'Keep shopping', centered: true });
    setTimeout(function () { PetStages.scan(document.querySelector('.modal-scrim')); }, 20);
    dialog.then(function (yes) {
      if (yes) global.location.href = '/pet' + (invId ? '?pet=' + invId : '');
    });
  }

  function markOwned(button, res) {
    var card = button.closest('.pt-card, .pt-item');
    if (!card) return;
    card.classList.add('owned');
    if (card.classList.contains('pt-card')) {
      var plate = document.createElement('a');
      plate.className = 'mk-btn vt-plate pt-edit';
      plate.href = '/pet' + (res && res.inv_id ? '?pet=' + res.inv_id : '');
      plate.innerHTML = '<span>Dress her up</span>';
      button.replaceWith(plate);
      var stage = card.querySelector('.pt-stage');
      if (stage && !stage.querySelector('.pt-owned')) {
        var chip = document.createElement('span');
        chip.className = 'vt-chip pt-owned';
        chip.innerHTML = '&#10003; Yours';
        stage.appendChild(chip);
      }
      var cv = card.querySelector('canvas.pt-live');
      if (cv && cv.__petStage) cv.__petStage.play('cheer');
    } else {
      var have = document.createElement('span');
      have.className = 'pt-have';
      have.textContent = 'In your wardrobe';
      button.replaceWith(have);
    }
  }

  function bindBuying(root) {
    root.addEventListener('click', function (e) {
      var button = e.target.closest('[data-buy]');
      if (!button || !global.Crates) return;
      e.preventDefault();
      Crates.buy(button).then(function (res) {
        if (!res) return;
        markOwned(button, res);
        if (button.dataset.slot === 'pet') {
          var card = button.closest && document.querySelector('.pt-card.owned[data-species]');
          var species = String(res.item_id || '').replace(/^pet_/, '');
          celebrate(res.name || 'She', species, res.inv_id);
        } else if (PetStages.fitting) {
          var item = root.querySelector('.pt-item[data-try="' + res.item_id + '"]');
          if (item && !item.classList.contains('trying')) PetStages.fitting.tryOn(item);
        }
      });
    });
  }

  /* Keep a tag's tooltip on the screen: one near either edge tips inwards. */
  function aimTips() {
    var w = global.innerWidth || document.documentElement.clientWidth;
    document.querySelectorAll('.ptag[data-tip]').forEach(function (tag) {
      var r = tag.getBoundingClientRect();
      var mid = (r.left + r.right) / 2;
      tag.classList.toggle('tip-left', mid > w - 120);
      tag.classList.toggle('tip-right', mid < 120);
    });
  }

  function boot() {
    PetStages.scan();
    aimTips();
    document.addEventListener('pointerover', function (e) {
      if (e.target.closest && e.target.closest('.ptag[data-tip]')) aimTips();
    });
    document.addEventListener('focusin', function (e) {
      if (e.target.closest && e.target.closest('.ptag[data-tip]')) aimTips();
    });
    var root = document.querySelector('.pt');
    if (root) {
      bindCards(root);
      bindFitting(root);
      bindTabs(root);
      bindBuying(root);
    }
    // the market's teaser: she peeks, she waves, she wants to come home
    var teaser = document.querySelector('.pt-teaser');
    if (teaser) {
      var cv = teaser.querySelector('canvas.pt-live');
      var stage = cv && cv.__petStage;
      if (stage) {
        var acts = ['wave', 'heart', 'twirl', 'cheer', 'peek', 'curtsy'];
        var n = 0;
        setInterval(function () {
          if (!document.hidden && stage.visible) stage.play(acts[n++ % acts.length]);
        }, 4200);
        teaser.addEventListener('pointerenter', function () { stage.play('cheer'); });
      }
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})(window);
