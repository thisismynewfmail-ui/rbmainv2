/* BLOCKHAVEN site -- 3D previews.
   One hidden WebGL canvas renders every item icon, avatar thumbnail and world
   preview on the page, then blits the result into the visible 2D canvases. */
(function (global) {
  'use strict';

  var Thumbs = {
    ready: false,
    catalog: null,
    avatarCache: {},
    imageCache: {},
    queue: [],
    working: false
  };

  var OFFSCREEN = 256;

  function ensureRenderer() {
    if (Thumbs.renderer || Thumbs.failed) return Thumbs.renderer;
    var canvas = document.createElement('canvas');
    canvas.width = OFFSCREEN;
    canvas.height = OFFSCREEN;
    // An explicit CSS size pins clientWidth, so the buffer below is exactly
    // OFFSCREEN square whatever the display's pixel ratio is.
    canvas.style.position = 'absolute';
    canvas.style.left = '-10000px';
    canvas.style.width = OFFSCREEN + 'px';
    canvas.style.height = OFFSCREEN + 'px';
    document.body.appendChild(canvas);
    var renderer = new Renderer(canvas, { preserveDrawingBuffer: true,
                                          antialias: true, transparent: true });
    if (renderer.failed) { Thumbs.failed = true; return null; }
    renderer.renderScale = 1;
    renderer.pixelRatio = 1;
    renderer.resize();
    renderer.far = 400;
    renderer.setSky({ top: '#a8cdea', horizon: '#f0f6fb', sun: [0.4, 0.8, 0.4],
                      clouds: 0.0, tint: '#ffffff' });
    renderer.fogColor = [0.94, 0.96, 0.98];
    Thumbs.renderer = renderer;
    Thumbs.particles = new Particles(renderer.gl);
    return renderer;
  }

  function fetchJSON(url) {
    return fetch(url, { headers: { 'X-Requested-With': 'fetch' } })
      .then(function (r) { return r.json(); });
  }

  Thumbs.loadCatalog = function () {
    if (Thumbs.catalogPromise) return Thumbs.catalogPromise;
    Thumbs.catalogPromise = fetchJSON('/api/catalog').then(function (data) {
      Thumbs.catalog = {};
      (data.items || []).forEach(function (item) { Thumbs.catalog[item.id] = item; });
      Thumbs.tiers = data.tiers || {};
      Thumbs.effects = data.effects || {};
      Thumbs.palette = data.palette || [];
      return Thumbs.catalog;
    }).catch(function () { Thumbs.catalog = {}; return {}; });
    return Thumbs.catalogPromise;
  };

  Thumbs.loadAvatar = function (username) {
    if (Thumbs.avatarCache[username]) return Promise.resolve(Thumbs.avatarCache[username]);
    return fetchJSON('/api/avatar/' + encodeURIComponent(username))
      .then(function (data) {
        Thumbs.avatarCache[username] = data.avatar || null;
        return data.avatar;
      }).catch(function () { return null; });
  };

  /* Characters are always shown against a night sky, in both themes.  The rig
     is lit for a dark background, the panels behind these canvases are dark in
     both palettes (see --preview-bg), and an avatar whose skin tone shifted
     every time somebody flipped the theme toggle read as a rendering fault
     rather than as a theme.  Item icons are the exception -- they sit on their
     own tier-coloured tile and keep the bright sky. */
  var AVATAR_SKY = { top: '#33455a', horizon: '#4a6180', sun: [0.4, 0.8, 0.35],
                     clouds: 0.0, tint: '#7b96b4' };
  var AVATAR_AMBIENT = '#6d86a2';

  var THUMB_FOV = 40;

  /* Place the camera so the subject's bounding box fits the frame exactly.

     Fitting a sphere (or, as before, guessing from the box's largest side)
     wastes room on a tall thin character and crops anything whose interesting
     surface sits near the camera -- a face decal is a head-radius closer than
     the centre the distance was measured from, which is what made every face
     thumbnail a close-up of one eye.  Projecting the eight corners into the
     camera basis and solving for the distance handles both: ``padding`` 1.0
     is a tight fit and anything above it is margin. */
  function frameCamera(renderer, parts, padding, angle, tilt) {
    var min = [1e9, 1e9, 1e9], max = [-1e9, -1e9, -1e9];
    parts.forEach(function (part) {
      for (var i = 0; i < 3; i++) {
        min[i] = Math.min(min[i], part.p[i] - part.s[i] * 0.5);
        max[i] = Math.max(max[i], part.p[i] + part.s[i] * 0.5);
      }
    });
    if (min[0] > max[0]) { min = [-1, -1, -1]; max = [1, 1, 1]; }
    var centre = [(min[0] + max[0]) / 2, (min[1] + max[1]) / 2, (min[2] + max[2]) / 2];
    var half = [Math.max(0.05, (max[0] - min[0]) / 2),
                Math.max(0.05, (max[1] - min[1]) / 2),
                Math.max(0.05, (max[2] - min[2]) / 2)];

    angle = angle === undefined ? -0.55 : angle;
    tilt = tilt === undefined ? 0.28 : tilt;
    // unit vector from the subject towards the camera
    var away = [Math.sin(angle) * Math.cos(tilt), Math.sin(tilt),
                Math.cos(angle) * Math.cos(tilt)];
    var forward = [-away[0], -away[1], -away[2]];
    var right = [-forward[2], 0, forward[0]];
    var rlen = Math.hypot(right[0], right[2]) || 1;
    right = [right[0] / rlen, 0, right[2] / rlen];
    var up = [
      right[1] * forward[2] - right[2] * forward[1],
      right[2] * forward[0] - right[0] * forward[2],
      right[0] * forward[1] - right[1] * forward[0]
    ];

    var tanY = Math.tan((THUMB_FOV * 0.5) * Math.PI / 180);
    var tanX = tanY * Math.max(0.2, renderer.aspect || 1);
    var distance = 0.1;
    for (var cx = -1; cx <= 1; cx += 2) {
      for (var cy = -1; cy <= 1; cy += 2) {
        for (var cz = -1; cz <= 1; cz += 2) {
          var v = [cx * half[0], cy * half[1], cz * half[2]];
          var px = v[0] * right[0] + v[1] * right[1] + v[2] * right[2];
          var py = v[0] * up[0] + v[1] * up[1] + v[2] * up[2];
          var pz = v[0] * forward[0] + v[1] * forward[1] + v[2] * forward[2];
          // a corner is in shot when |px| <= (d + pz) * tanX, and likewise in y
          distance = Math.max(distance, Math.abs(px) / tanX - pz,
                              Math.abs(py) / tanY - pz);
        }
      }
    }
    distance *= (padding === undefined ? 1.05 : padding);
    distance = Math.max(distance, half[2] + 0.4);
    var eye = [centre[0] + away[0] * distance,
               centre[1] + away[1] * distance,
               centre[2] + away[2] * distance];
    renderer.setCameraMatrix(eye, centre, THUMB_FOV);
    return { centre: centre, radius: Math.hypot(half[0], half[1], half[2]),
             distance: distance };
  }

  function renderParts(parts, options) {
    var renderer = ensureRenderer();
    if (!renderer) return null;
    options = options || {};
    renderer.setSky(options.sky || { top: '#bcdcf5', horizon: '#f4f9fc',
                                     sun: [0.45, 0.8, 0.35], clouds: 0, tint: '#ffffff' });
    renderer.buildStatic([]);
    renderer.beginFrame(0.016);
    parts.forEach(function (part) { renderer.push(part); });
    frameCamera(renderer, parts, options.padding, options.angle, options.tilt);
    if (options.effect && Thumbs.particles && Thumbs.effects) {
      var def = Thumbs.scaleEffect(Thumbs.effectDef(options.effect),
                                   options.effectScale);
      if (def) {
        Thumbs.particles.count = 0;
        Thumbs.particles.emitters = {};
        var anchor = options.anchor || [0, 0, 0];
        for (var step = 0; step < 90; step++) {
          Thumbs.particles.setEmitter('thumb', def, anchor);
          Thumbs.particles.update(1 / 60);
        }
      }
    }
    renderer.render();
    if (options.effect && Thumbs.particles) Thumbs.particles.draw(renderer);
    return renderer.canvas;
  }

  /* Keep a copy of a render at the source's own size.  Hard-coding a size
     here silently crops the picture whenever the WebGL buffer is larger. */
  function snapshot(source) {
    var copy = document.createElement('canvas');
    copy.width = source.width;
    copy.height = source.height;
    copy.getContext('2d').drawImage(source, 0, 0);
    return copy;
  }

  function blit(target, source) {
    var ctx = target.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, target.width, target.height);
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(source, 0, 0, target.width, target.height);
  }

  // --------------------------------------------------------- unusual effects
  /* An Unusual effect is authored for a whole character standing in a world.
     An item tile frames one hat from a couple of units away, so the same
     numbers would throw particles clean off the tile.  This shrinks the
     effect to the piece it is sitting on -- every length in the definition,
     so the plume keeps its shape instead of turning into a puff of confetti
     -- and the caller pads the camera to leave the plume somewhere to go. */
  var EFFECT_TILE_SCALE = 0.42;

  Thumbs.scaleEffect = function (def, factor) {
    if (!def) return null;
    if (!factor || factor === 1) return def;
    var out = {};
    for (var key in def) { if (def.hasOwnProperty(key)) out[key] = def[key]; }
    var size = def.size || [0.3, 0.5];
    var rise = def.rise || [0.5, 1.2];
    out.size = [size[0] * factor, size[1] * factor];
    out.rise = [rise[0] * factor, rise[1] * factor];
    out.radius = (def.radius === undefined ? 0.5 : def.radius) * factor;
    out.spread = (def.spread || 0.4) * factor;
    out.gravity = (def.gravity || 0) * factor;
    out.grow = (def.grow || 0) * factor;
    return out;
  };

  Thumbs.effectDef = function (effect) {
    if (!effect || !Thumbs.effects) return null;
    return Thumbs.effects[effect] || null;
  };

  /* Emit from the crown of the piece rather than from a fixed height, so a
     tall hat throws its flames from the top of the hat and a flat cap does
     not spit them out of its own brim. */
  function topOf(parts) {
    var top = -1e9, x = 0, z = 0, n = 0;
    parts.forEach(function (piece) {
      top = Math.max(top, piece.p[1] + piece.s[1] * 0.5);
      x += piece.p[0]; z += piece.p[2]; n++;
    });
    if (!n) return [0, 0.35, 0];
    return [x / n, top + 0.10, z / n];
  }

  // ------------------------------------------------------------ item icons
  Thumbs.itemParts = function (item, effect) {
    var slot = item.slot;
    var data = item.data || {};
    if (slot === 'hat' || slot === 'back') {
      var parts = (data.parts || []).map(function (piece) {
        return { t: piece.t || 'box', p: piece.p.slice(), s: piece.s.slice(),
                 c: piece.c, r: piece.r, m: piece.m, a: piece.a,
                 decSlot: piece.decal ? Textures.decal(piece.decal) : null };
      });
      if (!parts.length) parts.push({ t: 'box', p: [0, 0, 0], s: [1, 1, 1], c: '#c8cbcd' });
      // an effect needs headroom above the piece or the plume is guillotined
      return { parts: parts, angle: -0.62, tilt: 0.15,
               padding: effect ? 1.52 : 1.12,
               effectScale: EFFECT_TILE_SCALE,
               anchor: topOf(parts) };
    }
    if (slot === 'usable') {
      var weaponParts = (data.parts || []).map(function (piece) {
        return { t: piece.t || 'box', p: piece.p.slice(), s: piece.s.slice(),
                 c: piece.c, r: piece.r, m: piece.m };
      });
      return { parts: weaponParts, angle: -1.15, tilt: 0.42, padding: 1.08 };
    }
    // wearable clothing/faces are shown on a mannequin
    var descriptor = {
      colors: { head: '#f5cd30', torso: '#c8cbcd', left_arm: '#f5cd30',
                right_arm: '#f5cd30', left_leg: '#a3a2a5', right_leg: '#a3a2a5' },
      body_type: Thumbs.mannequinBody || 'male',
      items: {}
    };
    descriptor.items[slot] = { item_id: item.id, slot: slot, data: data,
                               tier: 'normal' };
    if (slot !== 'face') {
      descriptor.items.face = { item_id: 'face_smile', slot: 'face',
                                data: (Thumbs.catalog.face_smile || {}).data };
    }
    var faceOn = slot === 'face';
    var body = Avatar.build(descriptor, { position: [0, 0, 0],
                                          yaw: faceOn ? 0 : 0.4,
                                          pose: Avatar.pose('idle', 0, 0,
                                                            descriptor) });
    if (faceOn) {
      // head only, picked by rig tag rather than a height guess so the crop
      // survives any change to the proportions
      return { parts: body.filter(function (p) { return p.k === 'head'; }),
               angle: 0.0, tilt: 0.02, padding: 1.05 };
    }
    if (slot === 'pants') {
      return { parts: body, angle: -0.4, tilt: -0.1, padding: 1.06 };
    }
    return { parts: body, angle: -0.45, tilt: 0.18, padding: 1.06 };
  };

  Thumbs.renderItem = function (canvas, itemId, effect) {
    Thumbs.loadCatalog().then(function (catalog) {
      var item = catalog[itemId];
      if (!item) return;
      var key = 'item:' + itemId + ':' + (effect || '') + ':' +
        (Thumbs.mannequinBody || 'male');
      if (Thumbs.imageCache[key]) { blit(canvas, Thumbs.imageCache[key]); return; }
      var spec = Thumbs.itemParts(item, effect);
      var source = renderParts(spec.parts, {
        angle: spec.angle, tilt: spec.tilt, padding: spec.padding,
        effect: effect, effectScale: spec.effectScale, anchor: spec.anchor
      });
      if (!source) return;
      Thumbs.imageCache[key] = snapshot(source);
      blit(canvas, Thumbs.imageCache[key]);
    });
  };

  /* ---------------------------------------------------------- live effects
     A still frame is the right answer for a wall of item tiles -- it renders
     once and is cached -- but the moment a piece is the subject (the preview
     popup, a pinned item on a profile) a frozen puff of flame reads as a
     drawing rather than an effect.  These run the real emitter at frame rate
     against the shared offscreen renderer and blit it out, and they stop the
     moment the canvas leaves the page, so nothing keeps burning CPU behind a
     closed dialog. */
  var LIVE_MAX = 4;
  var live = [];
  var liveFrame = 0;
  var particlePool = [];

  function borrowParticles() {
    var renderer = ensureRenderer();
    if (!renderer) return null;
    var system = particlePool.pop();
    if (!system) system = new Particles(renderer.gl);
    system.count = 0;
    system.emitters = {};
    system.enabled = true;
    return system;
  }

  function releaseParticles(system) {
    if (!system) return;
    system.count = 0;
    system.emitters = {};
    if (particlePool.length < LIVE_MAX) particlePool.push(system);
  }

  function liveTick(now) {
    var renderer = Thumbs.renderer;
    if (!live.length || !renderer) { liveFrame = 0; return; }
    liveFrame = requestAnimationFrame(liveTick);
    for (var i = live.length - 1; i >= 0; i--) {
      var job = live[i];
      if (!job.canvas.isConnected) { Thumbs.stopLive(job.canvas); continue; }
      var dt = Math.min(0.05, (now - (job.last || now)) / 1000);
      job.last = now;
      // off-screen or in a hidden tab: keep the state, skip the work
      if (document.hidden || !job.canvas.offsetParent) continue;
      // renderWorld borrows the shared buffer at a different size; sit out
      // those frames rather than drawing an item into a 512x288 canvas
      if (renderer.canvas.width !== OFFSCREEN ||
          renderer.canvas.height !== OFFSCREEN) continue;
      renderer.setSky({ top: '#bcdcf5', horizon: '#f4f9fc',
                        sun: [0.45, 0.8, 0.35], clouds: 0, tint: '#ffffff' });
      renderer.buildStatic([]);
      renderer.beginFrame(dt);
      for (var n = 0; n < job.parts.length; n++) renderer.push(job.parts[n]);
      frameCamera(renderer, job.parts, job.padding, job.angle, job.tilt);
      job.particles.setEmitter('fx', job.def, job.anchor);
      job.particles.update(dt);
      renderer.render();
      job.particles.draw(renderer);
      blit(job.canvas, renderer.canvas);
    }
  }

  Thumbs.stopLive = function (canvas) {
    for (var i = 0; i < live.length; i++) {
      if (live[i].canvas !== canvas) continue;
      releaseParticles(live[i].particles);
      live.splice(i, 1);
      return true;
    }
    return false;
  };

  Thumbs.stopAllLive = function () {
    while (live.length) Thumbs.stopLive(live[live.length - 1].canvas);
  };

  /* Animate one item's Unusual effect into a canvas.  Falls back to the
     ordinary still icon when there is no effect, no WebGL, or when too many
     previews are already running. */
  Thumbs.animateItem = function (canvas, itemId, effect, options) {
    options = options || {};
    if (!canvas || !effect) {
      if (canvas && itemId) Thumbs.renderItem(canvas, itemId, effect);
      return;
    }
    Thumbs.stopLive(canvas);
    Thumbs.loadCatalog().then(function (catalog) {
      var item = catalog[itemId];
      if (!item || !ensureRenderer()) return;
      // draw the still first so the tile is never blank while we spin up
      Thumbs.renderItem(canvas, itemId, effect);
      var def = Thumbs.effectDef(effect);
      if (!def) return;
      if (live.length >= LIVE_MAX) return;
      var spec = Thumbs.itemParts(item, effect);
      var system = borrowParticles();
      if (!system) return;
      var job = {
        canvas: canvas,
        parts: spec.parts,
        angle: spec.angle,
        tilt: spec.tilt,
        padding: spec.padding,
        anchor: spec.anchor || [0, 0.35, 0],
        def: Thumbs.scaleEffect(def, options.scale || spec.effectScale),
        particles: system,
        last: 0
      };
      // a couple of seconds of pre-roll, so it opens mid-effect not empty
      for (var step = 0; step < 70; step++) {
        system.setEmitter('fx', job.def, job.anchor);
        system.update(1 / 60);
      }
      live.push(job);
      if (!liveFrame) liveFrame = requestAnimationFrame(liveTick);
    });
  };

  Thumbs.renderAvatarFor = function (canvas, username) {
    var key = 'avatar:' + username;
    if (Thumbs.imageCache[key]) { blit(canvas, Thumbs.imageCache[key]); return; }
    Promise.all([Thumbs.loadCatalog(), Thumbs.loadAvatar(username)])
      .then(function (results) {
        var descriptor = results[1];
        if (!descriptor) return;
        var parts = Avatar.build(descriptor, {
          position: [0, 0, 0], yaw: 0.35,
          pose: Avatar.pose('idle', 0, 0, descriptor)
        });
        var hat = (descriptor.items || {}).hat;
        var source = renderParts(parts, {
          angle: -0.35, tilt: 0.12, padding: 1.07, sky: AVATAR_SKY,
          effect: hat && hat.tier === 'unusual' ? hat.effect : '',
          anchor: hat ? Avatar.hatAnchor([0, 0, 0], 0, hat) : null
        });
        if (!source) return;
        Thumbs.imageCache[key] = snapshot(source);
        blit(canvas, Thumbs.imageCache[key]);
      });
  };

  // --------------------------------------------------------- world previews
  function worldScene(kind, colors) {
    var parts = [];
    function box(p, s, c, extra) {
      var part = { t: 'box', p: p, s: s, c: c };
      if (extra) { for (var k in extra) part[k] = extra[k]; }
      parts.push(part);
    }
    function tree(x, z, scale, leaf) {
      parts.push({ t: 'cyl', p: [x, 2.4 * scale, z], s: [1.2 * scale, 5 * scale, 1.2 * scale], c: '#7c503a' });
      parts.push({ t: 'sph', p: [x, 6.6 * scale, z], s: [6 * scale, 5.4 * scale, 6 * scale], c: leaf || '#287f47' });
    }
    box([0, -1, 0], [90, 2, 60], colors && colors[0] ? '#5aa84f' : '#5aa84f', { st: 1 });
    if (kind === 'ctf') {
      box([-26, 5, -8], [26, 10, 22], '#c8cbcd', { st: 1 });
      box([-26, 11, -8], [28, 2, 24], '#a3a2a5');
      box([-26, 13.5, -8], [6, 3, 6], '#c4281c');
      box([26, 5, -8], [26, 10, 22], '#c8cbcd', { st: 1 });
      box([26, 11, -8], [28, 2, 24], '#a3a2a5');
      box([26, 13.5, -8], [6, 3, 6], '#0d69ac');
      box([0, 0.2, 0], [12, 0.4, 60], '#d8d8d0');
      box([0, 3, 14], [22, 6, 22], '#a3a2a5', { st: 1 });
      box([-6, 8, 14], [2.4, 10, 2.4], '#c8cbcd');
      box([6, 8, 14], [2.4, 10, 2.4], '#c8cbcd');
      box([0, 13.5, 14], [16, 2, 3], '#c8cbcd');
      tree(-38, 18, 1.1); tree(36, 20, 0.9); tree(-14, 24, 0.8);
    } else if (kind === 'payload') {
      parts[0].c = '#c9b48b';
      box([0, 0.3, 0], [80, 0.6, 8], '#b09a72');
      for (var i = -34; i <= 34; i += 6) {
        box([i, 0.8, 0], [4.4, 0.6, 9], '#5f3d1e');
        box([i, 1.3, -3], [4.4, 0.5, 1], '#8f9296', { m: 'metal' });
        box([i, 1.3, 3], [4.4, 0.5, 1], '#8f9296', { m: 'metal' });
      }
      box([-4, 3.4, 0], [10, 5, 6], '#4a4a4a', { m: 'metal' });
      box([-4, 6.6, 0], [7, 2.4, 5], '#b8383b');
      box([-8.5, 1.6, 3.2], [2.6, 2.6, 1.2], '#22262b', { m: 'metal' });
      box([-8.5, 1.6, -3.2], [2.6, 2.6, 1.2], '#22262b', { m: 'metal' });
      box([28, 6, -16], [26, 12, 18], '#b8383b', { st: 1 });
      box([28, 12.6, -16], [28, 1.6, 20], '#8f2b2e');
      box([-30, 6, 16], [24, 12, 16], '#5885a2', { st: 1 });
      box([-30, 12.6, 16], [26, 1.6, 18], '#3f6580');
      box([12, 4, 18], [12, 8, 12], '#8a5a2b', { st: 1 });
    } else {
      box([-24, 1.2, 4], [40, 2.4, 34], '#cdd0d3', { st: 1 });
      box([-24, 8, -6], [30, 12, 16], '#c98b5e');
      box([-24, 14.6, -6], [33, 2, 19], '#c4281c', { st: 1 });
      box([-24, 18, 2], [18, 5, 1.4], '#f2b01e', { m: 'neon', dec: 'burger' });
      box([-24, 4, 10], [22, 3.4, 3], '#8a5a2b');
      box([-4, 4, 12], [6, 4, 5], '#a8adb2', { m: 'metal' });
      box([24, 1.2, 4], [36, 2.4, 30], '#cdd0d3', { st: 1 });
      box([24, 4, -2], [16, 6, 10], '#8f9296', { m: 'metal' });
      box([0, 0.4, -22], [90, 0.8, 14], '#b9b9b1');
      tree(38, 22, 1.0); tree(-44, 20, 0.9);
      box([6, 2.2, 22], [10, 4.4, 10], '#e2e2da', { st: 1 });
      box([6, 5, 22], [7, 1.6, 7], '#9fd8e8', { m: 'glass', a: 0.8 });
    }
    return parts;
  }

  var WORLD_SKIES = {
    ctf: { top: '#7fb2e5', horizon: '#e8f0f8', sun: [0.35, 0.7, -0.25], clouds: 0.5, tint: '#ffffff' },
    payload: { top: '#e8b46a', horizon: '#f7e4bd', sun: [0.5, 0.55, 0.2], clouds: 0.7, tint: '#ffe9c4' },
    burger: { top: '#8fc4ef', horizon: '#ffeec4', sun: [0.3, 0.75, 0.4], clouds: 0.42, tint: '#fff6e0' }
  };

  Thumbs.renderWorld = function (canvas, kind, colors) {
    var key = 'world:' + kind + ':' + canvas.width;
    if (Thumbs.imageCache[key]) { blit(canvas, Thumbs.imageCache[key]); return; }
    var renderer = ensureRenderer();
    if (!renderer) return;
    var parts = worldScene(kind, colors);
    renderer.transparentBackground = false;
    var previous = { w: renderer.canvas.width, h: renderer.canvas.height };
    renderer.canvas.width = 512;
    renderer.canvas.height = 288;
    renderer.width = 512; renderer.height = 288; renderer.aspect = 512 / 288;
    renderer.setSky(WORLD_SKIES[kind] || WORLD_SKIES.ctf);
    renderer.buildStatic([]);
    renderer.beginFrame(0.016);
    parts.forEach(function (part) { renderer.push(part); });
    renderer.setCameraMatrix([44, 34, 62], [0, 5, -2], 42);
    renderer.render();
    Thumbs.imageCache[key] = snapshot(renderer.canvas);
    blit(canvas, Thumbs.imageCache[key]);
    renderer.transparentBackground = true;
    renderer.canvas.width = previous.w;
    renderer.canvas.height = previous.h;
    renderer.width = previous.w; renderer.height = previous.h;
    renderer.aspect = previous.w / previous.h;
  };

  // ------------------------------------------------------- live 3D preview
  function LivePreview(container, descriptor) {
    this.container = container;
    this.descriptor = descriptor;
    this.canvas = document.createElement('canvas');
    this.canvas.style.width = '100%';
    this.canvas.style.height = '100%';
    container.insertBefore(this.canvas, container.firstChild);
    this.renderer = new Renderer(this.canvas, { antialias: true });
    if (this.renderer.failed) {
      container.innerHTML = '<div style="padding:20px;text-align:center;color:#6f8095">' +
        'Your browser could not start WebGL, so the 3D preview is unavailable.</div>';
      this.failed = true;
      return;
    }
    this.particles = new Particles(this.renderer.gl);
    this.applyTheme();
    this.renderer.far = 200;
    this.angle = -0.45;
    this.tilt = 0.2;
    this.distance = 12.5;
    this.spin = true;
    this.time = 0;
    this.poseState = 'idle';
    this.poseSpeed = 0;
    this.swapT = -1;        // >= 0 while a model swap is playing
    this.swapApply = null;
    this.glide = 0;         // easing the camera back without moving the angle
    this.markHome();
    this.bindInput();
    this.loop = this.loop.bind(this);
    requestAnimationFrame(this.loop);
  }

  LivePreview.prototype.bindInput = function () {
    var self = this;
    var dragging = false, decided = false, touch = false;
    var lastX = 0, lastY = 0, startX = 0, startY = 0;
    // On a touch screen the preview must not eat a vertical page scroll, so a
    // drag only claims the gesture once it is clearly sideways.
    this.canvas.style.touchAction = 'pan-y';
    this.canvas.addEventListener('pointerdown', function (e) {
      dragging = true;
      touch = e.pointerType === 'touch';
      decided = !touch;
      lastX = startX = e.clientX; lastY = startY = e.clientY;
      self.glide = 0;                 // the viewer takes the camera back
      if (!touch) {
        self.spin = false;
        self.canvas.setPointerCapture(e.pointerId);
      }
    });
    this.canvas.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      if (!decided) {
        var dx = Math.abs(e.clientX - startX);
        var dy = Math.abs(e.clientY - startY);
        if (dx < 6 && dy < 6) return;
        if (dy > dx) { dragging = false; return; }   // let the page scroll
        decided = true;
        self.spin = false;
        self.canvas.style.touchAction = 'none';
        try { self.canvas.setPointerCapture(e.pointerId); } catch (err) {}
      }
      self.angle -= (e.clientX - lastX) * 0.011;
      self.tilt = Math.max(-0.7, Math.min(0.95, self.tilt + (e.clientY - lastY) * 0.008));
      lastX = e.clientX; lastY = e.clientY;
    });
    ['pointerup', 'pointercancel', 'pointerleave'].forEach(function (name) {
      self.canvas.addEventListener(name, function () {
        dragging = false;
        decided = false;
        self.canvas.style.touchAction = 'pan-y';
      });
    });
    this.canvas.addEventListener('wheel', function (e) {
      e.preventDefault();
      self.glide = 0;
      self.distance = Math.max(6, Math.min(26, self.distance + e.deltaY * 0.012));
    }, { passive: false });
  };

  LivePreview.prototype.setDescriptor = function (descriptor) {
    // A different build walks differently, so easing out of the old one's
    // pose would be easing between two gaits.  Changing build starts the new
    // character in its own pose; everything else (a colour, a hat) keeps the
    // pose it is holding.
    if (Avatar.bodyType(descriptor) !== Avatar.bodyType(this.descriptor)) {
      Avatar.resetPose(this);
    }
    this.descriptor = descriptor;
  };

  /* The preview paints its own sky, and it is a night one whichever theme the
     page is wearing -- see AVATAR_SKY.  The welcome stage is a deeper blue so
     it sits inside the hero panel rather than on top of it. */
  LivePreview.prototype.applyTheme = function () {
    this.dark = true;
    if (this.skyMode === 'stage') {
      this.renderer.setSky({ top: '#0f2540', horizon: '#1d4570',
                             sun: [0.35, 0.85, 0.4], clouds: 0.0,
                             tint: '#7fb0e0' });
      this.renderer.setAmbient('#5b7ea8');
      return;
    }
    this.renderer.setSky(AVATAR_SKY);
    // keep a little ambient bounce so a dark scene does not crush the model
    this.renderer.setAmbient(AVATAR_AMBIENT);
  };

  LivePreview.prototype.loop = function (now) {
    if (this.failed) return;
    requestAnimationFrame(this.loop);
    if (!this.container.offsetParent && this.container.offsetWidth === 0) return;
    var dt = Math.min(0.05, (now - (this.last || now)) / 1000);
    this.last = now;
    this.time += dt;
    if (this.spin) this.angle += dt * 0.32;
    this.stepGlide(dt);
    var swap = this.stepSwap(dt);
    this.renderer.resize();
    var parts = Avatar.build(this.descriptor, {
      position: [0, swap.lift, 0], yaw: 0, time: this.time,
      // the preview keeps its own pose between frames, so switching the
      // posed state (or rolling a look with a different gait) eases across
      // instead of cutting
      pose: Avatar.smoothPose(this, this.poseState, this.time, this.poseSpeed,
                              this.descriptor, dt)
    });
    if (swap.alpha < 0.999) {
      for (var pi = 0; pi < parts.length; pi++) {
        var pt = parts[pi];
        pt.a = (pt.a === undefined ? 1 : pt.a) * swap.alpha;
      }
    }
    var hat = (this.descriptor.items || {}).hat;
    var unusual = (hat && hat.tier === 'unusual' && hat.effect_def) ? 1 : 0;
    // An Unusual effect plumes upward out of the hat, so a look wearing one
    // needs headroom a bare head does not.  A stage that asked for it buys
    // that headroom by aiming a fraction higher and easing back a fraction
    // further, smoothed so a roll that gains or loses an effect never jumps.
    // Only the welcome stage rolls its own looks, so only it asks.
    var wantRoom = this.roomForEffects ? unusual : 0;
    this.effectRoom = (this.effectRoom || 0) +
      (wantRoom - (this.effectRoom || 0)) * Math.min(1, dt * 3);
    // The projection fixes the vertical field of view, so a narrow panel is
    // the one that crops: pull the camera back until the character's width
    // fits again.  Wide panels are already fine and are left alone.
    var aspect = this.renderer.aspect || 1;
    var distance = this.distance * (1 + 0.055 * this.effectRoom) *
      Math.max(1, 0.78 / Math.max(0.2, aspect));
    this.renderer.beginFrame(dt);
    parts.forEach(function (part) { this.renderer.push(part); }, this);
    // Simple ground shadow.  It draws in the opaque pass, so during a swap it
    // closes up rather than fading -- same read, no see-through disc.
    var shadow = 0.25 + 0.75 * swap.alpha;
    this.renderer.pushRaw('cyl', 0, 0.02, 0, 0, 0, 0,
                          5.2 * shadow, 0.04, 4.0 * shadow,
                          [0.35, 0.42, 0.5], 0.32, 0, 0, 0.8, null);
    var centre = [0, (this.focusY === undefined ? 2.9 : this.focusY) +
                     0.36 * this.effectRoom, 0];
    var eye = [
      centre[0] + Math.sin(this.angle) * distance,
      centre[1] + Math.sin(this.tilt) * distance * 0.85 + 0.6,
      centre[2] + Math.cos(this.angle) * distance
    ];
    this.renderer.setCameraMatrix(eye, centre, 42);
    if (unusual && swap.alpha > 0.02) {
      this.particles.setEmitter('hat', hat.effect_def,
                                Avatar.hatAnchor([0, swap.lift, 0], 0, hat));
    } else {
      this.particles.clearEmitter('hat');
    }
    this.particles.update(dt);
    this.renderer.render();
    this.particles.draw(this.renderer);
  };

  /* Remember the current camera as "home".  Called once the caller has
     finished positioning the preview, so glideHome eases back to the framing
     the page asked for rather than the constructor's defaults. */
  LivePreview.prototype.markHome = function () {
    this.home = { angle: this.angle, tilt: this.tilt, distance: this.distance };
  };

  /* Ease the camera back to the framing the page asked for -- but leave the
     heading alone.  The turn is the one thing that must not jump: whichever
     way the character happens to be facing when the outfit changes is the way
     the next one carries on from, so the rotation reads as one unbroken take.
     A tilt or a zoom the viewer changed does come back, and it slides. */
  LivePreview.prototype.glideHome = function () {
    if (!this.home) return;
    this.glide = 1;
    this.spin = true;
  };

  LivePreview.prototype.stepGlide = function (dt) {
    if (!this.glide || !this.home) return;
    var k = Math.min(1, dt * 4.5);
    this.tilt += (this.home.tilt - this.tilt) * k;
    this.distance += (this.home.distance - this.distance) * k;
    if (Math.abs(this.home.tilt - this.tilt) < 0.002 &&
        Math.abs(this.home.distance - this.distance) < 0.02) {
      this.tilt = this.home.tilt;
      this.distance = this.home.distance;
      this.glide = 0;
    }
  };

  /* Hand over a new look without touching anything but the character.  The
     model dissolves, ``apply`` swaps what it is wearing at the low point, and
     the new one settles up into place.  The canvas, the stage behind it and
     the camera's turn are all left exactly as they were -- the old CSS fade
     moved the painted sky along with the character, which is precisely what
     made a swap read as the whole panel flinching. */
  var SWAP_OUT = 0.26, SWAP_IN = 0.34;

  LivePreview.prototype.swapModel = function (apply) {
    if (typeof apply !== 'function') return;
    if (this.failed) { apply(); return; }
    if (this.swapApply) this.swapApply();      // a rapid re-roll never skips one
    this.swapApply = apply;
    this.swapT = 0;
  };

  LivePreview.prototype.stepSwap = function (dt) {
    if (this.swapT < 0) return { alpha: 1, lift: 0 };
    this.swapT += dt;
    if (this.swapT < SWAP_OUT) {
      var k = this.swapT / SWAP_OUT;
      return { alpha: 1 - k * k, lift: -0.22 * k * k };
    }
    if (this.swapApply) {
      this.swapApply();
      this.swapApply = null;
      // the outgoing hat's particles go with it rather than raining on the
      // character that replaces it
      this.particles.clearEmitter('hat');
      this.particles.count = 0;
    }
    var j = Math.min(1, (this.swapT - SWAP_OUT) / SWAP_IN);
    var e = 1 - Math.pow(1 - j, 3);
    if (j >= 1) { this.swapT = -1; return { alpha: 1, lift: 0 }; }
    return { alpha: e, lift: -0.5 * (1 - e) };
  };

  LivePreview.prototype.setPose = function (state) {
    this.poseState = state || 'idle';
    this.poseSpeed = (state === 'run') ? 1 : (state === 'walk' ? 0.6 : 0);
  };

  Thumbs.LivePreview = LivePreview;

  // ----------------------------------------------------- random characters
  /* The welcome page shows one character rather than a shelf of them, so that
     character has to earn its place: every reload (and every Shuffle) rolls a
     fresh build, outfit, face and palette straight out of the live catalogue,
     with the same 3D rig the profile and the game use.  Nothing here is
     hand-drawn, so a hat added to the catalogue can turn up on the front page
     the same day. */
  // No sitting: there is no chair on the stage, so a seated pose reads as a
  // character floating in mid-air.
  var HERO_POSES = ['idle', 'walk', 'run', 'jump'];
  var HERO_POSE_LABELS = {
    idle: 'Standing by', walk: 'On the move', run: 'Sprinting',
    jump: 'Mid-jump'
  };

  function pick(list) {
    return list.length ? list[Math.floor(Math.random() * list.length)] : null;
  }

  function bySlot(slot) {
    var out = [];
    for (var id in Thumbs.catalog) {
      if (!Thumbs.catalog.hasOwnProperty(id)) continue;
      var item = Thumbs.catalog[id];
      if (item.slot !== slot) continue;
      // "No Shirt" and "No Pants" are catalogue entries meaning bare; a random
      // look that rolls them reads as an unfinished character, not a choice
      if (/_none$/.test(id)) continue;
      out.push(item);
    }
    return out;
  }

  // Used for the very first character, before /api/catalog has answered.
  var FALLBACK_PALETTE = ['#f5cd30', '#c4281c', '#0d69ac', '#2f9e55', '#8b3fd6',
                          '#d3592b', '#1b2a35', '#a3a2a5', '#f3cf9b', '#008f9c'];

  function paletteHex() {
    var list = Thumbs.palette;
    if (list && list.length) {
      var entry = pick(list);
      if (entry && entry.hex) return entry.hex;
    }
    return pick(FALLBACK_PALETTE);
  }

  Thumbs.randomLook = function (options) {
    options = options || {};
    var skin = paletteHex();
    var legs = paletteHex();
    var descriptor = {
      // every build in the rig gets a turn on the welcome stage, so a new
      // one shows up out front the day it ships
      body_type: pick(Avatar.BODY_TYPES),
      colors: {
        head: skin, torso: paletteHex(), left_arm: skin, right_arm: skin,
        left_leg: legs, right_leg: legs
      },
      items: {}
    };
    var chips = [];
    function wear(slot, chance) {
      var item = pick(bySlot(slot));
      if (!item || Math.random() > chance) return null;
      descriptor.items[slot] = { item_id: item.id, slot: slot, data: item.data,
                                 tier: 'normal', effect: '' };
      chips.push({ slot: slot, name: item.name, rarity: item.rarity });
      return item;
    }
    var face = wear('face', 1);
    var hat = wear('hat', 0.92);
    wear('shirt', 0.8);
    wear('pants', 0.72);
    wear('back', 0.34);
    // roughly one look in four wears an Unusual, which is the whole point of
    // the hat aisle and the thing worth showing a visitor
    var effectIds = Object.keys(Thumbs.effects || {});
    var unusual = '';
    if (hat && effectIds.length && Math.random() < (options.unusualChance || 0.28)) {
      unusual = pick(effectIds);
      descriptor.items.hat.tier = 'unusual';
      descriptor.items.hat.effect = unusual;
      descriptor.items.hat.effect_def = Thumbs.effects[unusual];
    }
    return {
      descriptor: descriptor,
      chips: chips,
      hat: hat,
      face: face,
      unusual: unusual,
      unusualName: unusual ? (Thumbs.effects[unusual] || {}).name : '',
      pose: options.pose || pick(HERO_POSES)
    };
  };

  Thumbs.heroPoses = HERO_POSES;
  Thumbs.posePreviewLabel = function (state) {
    return HERO_POSE_LABELS[state] || 'Standing by';
  };

  Thumbs.retheme = function () {
    document.querySelectorAll('.avatar-view').forEach(function (el) {
      if (el.__preview && el.__preview.applyTheme) el.__preview.applyTheme();
    });
  };

  // ---------------------------------------------------------------- boot
  function observe() {
    var observer = null;
    if (window.IntersectionObserver) {
      observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          observer.unobserve(entry.target);
          paint(entry.target);
        });
      }, { rootMargin: '160px' });
    }
    function schedule(el) {
      if (observer) observer.observe(el);
      else paint(el);
    }
    document.querySelectorAll('canvas.item-thumb[data-item]').forEach(schedule);
    document.querySelectorAll('canvas.avatar-thumb[data-user]').forEach(schedule);
    document.querySelectorAll('canvas.world-shot[data-world]').forEach(schedule);
  }

  function paint(el) {
    if (el.dataset.item !== undefined && el.classList.contains('item-thumb')) {
      if (!el.dataset.item) return;
      // a tile that asked for it runs the effect live instead of as a still
      if (el.dataset.liveEffect && el.dataset.effect) {
        Thumbs.animateItem(el, el.dataset.item, el.dataset.effect);
      } else {
        Thumbs.renderItem(el, el.dataset.item, el.dataset.effect);
      }
    } else if (el.dataset.user) {
      Thumbs.renderAvatarFor(el, el.dataset.user);
    } else if (el.dataset.world) {
      Thumbs.renderWorld(el, el.dataset.world, null);
    }
  }

  Thumbs.paint = paint;
  Thumbs.rescan = observe;

  /* Hand a hero stage a freshly rolled look.  The character itself dissolves
     and settles back in -- nothing else on the stage is touched -- and the
     caption changes on the same frame the model does, so the two never
     disagree.  A tilt or zoom the viewer left behind slides home; the turn
     carries straight on from wherever it had got to. */
  Thumbs.dressHero = function (el, options) {
    var preview = el && el.__preview;
    if (!preview || preview.failed) return null;
    var look = Thumbs.randomLook(options);
    function apply() {
      preview.setDescriptor(look.descriptor);
      preview.setPose(look.pose);
      el.__look = look;
      el.dispatchEvent(new CustomEvent('look', { bubbles: true, detail: look }));
    }
    if (el.__look) {
      preview.swapModel(apply);
    } else {
      apply();
    }
    preview.glideHome();
    return look;
  };

  document.addEventListener('DOMContentLoaded', function () {
    if (typeof Renderer === 'undefined') return;
    /* None of this waits on the catalogue.  Every painter below fetches it
       for itself and the hero starts on a character it can build without one,
       because hanging the whole page off a single request is what left a
       phone on a weak connection looking at empty panels. */
    observe();
    document.querySelectorAll('.avatar-view[data-avatar]').forEach(function (el) {
      var descriptor;
      try { descriptor = JSON.parse(el.dataset.avatar); } catch (e) { return; }
      el.__preview = new LivePreview(el, descriptor);
    });
    document.querySelectorAll('.avatar-view[data-avatar-hero]').forEach(function (el) {
      var look = Thumbs.randomLook();
      var preview = new LivePreview(el, look.descriptor);
      if (preview.failed) return;
      preview.skyMode = 'stage';
      preview.applyTheme();
      preview.setPose(look.pose);
      // Framed so the stage is filled rather than floated in: the character
      // is pulled in close enough to read at a glance, and the look-at point
      // sits above its waist so it stands on the lower half of the panel with
      // the headroom a tall hat and its effect need overhead.
      preview.distance = 12.9;
      preview.focusY = 2.95;
      preview.roomForEffects = true;
      preview.markHome();
      el.__preview = preview;
      el.__look = look;
      el.dispatchEvent(new CustomEvent('look', { bubbles: true, detail: look }));
      // ...then dress it properly once the catalogue turns up
      Thumbs.loadCatalog().then(function () { Thumbs.dressHero(el); });
    });
    Thumbs.loadCatalog().then(function () {
      document.querySelectorAll('.avatar-view[data-avatar-demo]').forEach(function (el) {
        el.__preview = new LivePreview(el, {
          body_type: Avatar.RIG.bodies[el.dataset.avatarDemo]
            ? el.dataset.avatarDemo : 'male',
          colors: { head: '#f5cd30', torso: '#c4281c', left_arm: '#f5cd30',
                    right_arm: '#f5cd30', left_leg: '#1b2a35', right_leg: '#1b2a35' },
          items: {
            face: { item_id: 'face_smile', slot: 'face',
                    data: (Thumbs.catalog.face_smile || {}).data },
            hat: { item_id: 'hat_red_cap', slot: 'hat', tier: 'unusual',
                   effect: 'burning',
                   effect_def: (Thumbs.effects || {}).burning,
                   data: (Thumbs.catalog.hat_red_cap || {}).data }
          }
        });
      });
    });
  });

  global.Thumbs = Thumbs;
})(window);
