/* BLOCKHAVEN -- the Pet Zone (templates/pet_zone.html).

   Her room, and looking after her: a virtual pet for the pet you own.  The
   room is ONE directed stage of PetStages (pets_shop.js) -- the shared
   offscreen renderer, not a second one -- and this file is its director:
   it builds the room round her (her colours on the walls, her cushion, her
   bowl, a shelf that fills with trophies as the bond grows), places the
   camera, dims the lights when she naps, paints the particles and the
   hand and brush over the frame, and decides, moment to moment, what she
   is doing.

   What she does comes from three places:
     * you -- a tap on her is a pat, a drag across her head strokes it,
       the bar along the bottom feeds her (a tray of treats, or drag one to
       her mouth), throws her a toy, brushes, tickles, cheers her on and
       puts her down for a nap;
     * how she is -- the four needs and the mood the server works out
       (app/models/pet_care.py): hungry, she rubs her tummy and begs at her
       bowl; sleepy, she nods off on her feet; sad, she mopes in a corner;
     * who she is -- her persona tags pick the reactions she loves and the
       ones she would rather you did not, and colour her idle moments.

   The server is the truth.  Every action shows at once (her reaction, the
   meters moving, the cooldown starting) and is then corrected by the
   answer to POST /api/pets/care, which carries her whole state; a refusal
   (she is stuffed, asleep, not sleepy, still busy) comes with her state
   too and is shown as her saying no.  Between answers the needs run down
   on the page at the server's own rates, so the meters are live, and she
   is re-read now and then, when the tab comes back and when she should
   have woken up by herself.

   Phone first: the room on top, a thumb-sized action bar along the bottom,
   trays that open up out of it, everything one-handed at 360px.  Rendering
   stops when the tab is hidden or the room is scrolled away, and
   prefers-reduced-motion calms the camera, the particles and the shakes. */
(function (global) {
  'use strict';

  var root = document.getElementById('pet-zone');
  if (!root || !global.Pet) return;
  var boot;
  try { boot = JSON.parse(document.getElementById('pz-boot').textContent); } catch (e) { return; }

  var $ = function (sel) { return root.querySelector(sel); };
  var $$ = function (sel) { return Array.prototype.slice.call(root.querySelectorAll(sel)); };

  // ----------------------------------------------------------------- bits
  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
  function lerp(a, b, k) { return a + (b - a) * k; }
  function smooth(t) { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); }
  function rand(a, b) { return a + Math.random() * (b - a); }
  function pick(list) { return list[(Math.random() * list.length) | 0]; }
  function now() { return performance.now() / 1000; }
  function angleTo(from, to, k) {
    var d = to - from;
    while (d > Math.PI) d -= Math.PI * 2;
    while (d < -Math.PI) d += Math.PI * 2;
    return from + d * k;
  }
  var RGB = {};
  function rgb(hex) {
    var c = RGB[hex];
    if (c) return c;
    var h = String(hex || '#ffffff').replace('#', '');
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var n = parseInt(h, 16) || 0;
    c = RGB[hex] = [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
    return c;
  }
  function mixHex(a, b, k) {
    var x = rgb(a), y = rgb(b);
    var out = '#';
    for (var i = 0; i < 3; i++) {
      var v = Math.round(lerp(x[i], y[i], k) * 255);
      out += (v < 16 ? '0' : '') + v.toString(16);
    }
    return out;
  }
  function esc(text) {
    return global.Site && Site.escape ? Site.escape(text) : String(text == null ? '' : text);
  }
  function store(key, value) {
    try {
      if (value === undefined) return global.localStorage.getItem(key);
      global.localStorage.setItem(key, value);
    } catch (e) { /* private mode: it just will not be remembered */ }
    return null;
  }

  var motion = global.matchMedia ? global.matchMedia('(prefers-reduced-motion: reduce)') : null;
  function calm() { return !!(motion && motion.matches); }

  // ---------------------------------------------------------- the catalogue
  var PETS = {};
  boot.pets.forEach(function (p) { PETS[p.inv_id] = p; });
  var TREATS = {}, TOYS = {}, ACTIONS = {};
  boot.treats.forEach(function (t) { TREATS[t.id] = t; });
  boot.toys.forEach(function (t) { TOYS[t.id] = t; });
  boot.actions.forEach(function (a) { ACTIONS[a.id] = a; });
  ACTIONS.wake = ACTIONS.wake || { id: 'wake', name: 'Wake', cooldown: 2 };
  var EFFECTS = boot.effects || {};
  var MOODS = boot.moodInfo || {};
  var LIMIT = boot.thresholds || { full: 95, tired: 10, notSleepy: 85, spotless: 98, groggy: 60 };
  var NEEDS = boot.needs || ['fullness', 'happiness', 'energy', 'cleanliness'];
  var NEEDY = { starving: 1, exhausted: 1, sad: 1, hungry: 1, sleepy: 1, grubby: 1, lonely: 1, bored: 1 };
  var VERB = { pat: 'Pats', feed: 'Treats', play: 'Games', brush: 'Brushes', tickle: 'Tickles',
               cheer: 'Cheers', nap: 'Naps', greet: 'Hellos' };
  var LOVE_WORDS = { pat: 'pats', feed: 'treats', play: 'playtime', brush: 'being brushed',
                     tickle: 'tickles', cheer: 'being cheered on', nap: 'naps' };

  var pet = PETS[boot.chosen] || boot.pets[0];
  var active = boot.active;
  var summary = boot.summary || {};

  // ============================================================== the sound
  /* Little synthesised sounds through the site's audio helper
     (engine/audio.js): no files, nothing to download.  A sound is a list of
     [delay ms, 'tone' | 'noise', options].  Nothing plays before the first
     tap (browsers would refuse anyway) or while the room is muted. */
  var SOUNDS = {
    pat: [[0, 'tone', { type: 'sine', freq: 620, freqEnd: 900, dur: 0.09, gain: 0.08 }]],
    stroke: [[0, 'noise', { filter: 'bandpass', freq: 1500, freqEnd: 800, dur: 0.22, gain: 0.04 }]],
    giggle: [[0, 'tone', { type: 'triangle', freq: 880, freqEnd: 1150, dur: 0.07, gain: 0.07 }],
             [85, 'tone', { type: 'triangle', freq: 1040, freqEnd: 1320, dur: 0.07, gain: 0.07 }],
             [170, 'tone', { type: 'triangle', freq: 960, freqEnd: 1250, dur: 0.07, gain: 0.07 }],
             [255, 'tone', { type: 'triangle', freq: 1180, freqEnd: 1480, dur: 0.09, gain: 0.07 }]],
    munch: [[0, 'noise', { filter: 'highpass', freq: 2400, dur: 0.05, gain: 0.1 }],
            [120, 'noise', { filter: 'highpass', freq: 2000, dur: 0.05, gain: 0.08 }]],
    yum: [[0, 'tone', { type: 'sine', freq: 523, dur: 0.12, gain: 0.09 }],
          [110, 'tone', { type: 'sine', freq: 784, dur: 0.2, gain: 0.09 }]],
    fave: [[0, 'tone', { type: 'triangle', freq: 523, dur: 0.1, gain: 0.08 }],
           [90, 'tone', { type: 'triangle', freq: 659, dur: 0.1, gain: 0.08 }],
           [180, 'tone', { type: 'triangle', freq: 784, dur: 0.1, gain: 0.08 }],
           [270, 'tone', { type: 'triangle', freq: 1047, dur: 0.26, gain: 0.09 }]],
    nope: [[0, 'tone', { type: 'square', freq: 230, freqEnd: 190, dur: 0.11, gain: 0.04 }],
           [140, 'tone', { type: 'square', freq: 200, freqEnd: 150, dur: 0.16, gain: 0.04 }]],
    toss: [[0, 'noise', { filter: 'bandpass', freq: 600, freqEnd: 2400, dur: 0.22, gain: 0.07 }]],
    boing: [[0, 'tone', { type: 'sine', freq: 280, freqEnd: 640, dur: 0.15, gain: 0.1 }]],
    bounce: [[0, 'tone', { type: 'sine', freq: 360, freqEnd: 560, dur: 0.09, gain: 0.06 }]],
    squeak: [[0, 'tone', { type: 'square', freq: 1150, freqEnd: 1600, dur: 0.07, gain: 0.03 }],
             [90, 'tone', { type: 'square', freq: 1500, freqEnd: 1050, dur: 0.08, gain: 0.03 }]],
    swish: [[0, 'noise', { filter: 'bandpass', freq: 1200, freqEnd: 3200, dur: 0.14, gain: 0.06 }]],
    brush: [[0, 'noise', { filter: 'bandpass', freq: 3200, freqEnd: 1700, dur: 0.24, gain: 0.035 }]],
    sparkle: [[0, 'tone', { type: 'sine', freq: 1568, dur: 0.1, gain: 0.045 }],
              [70, 'tone', { type: 'sine', freq: 2093, dur: 0.16, gain: 0.035 }]],
    cheer: [[0, 'tone', { type: 'triangle', freq: 392, dur: 0.1, gain: 0.08 }],
            [110, 'tone', { type: 'triangle', freq: 523, dur: 0.1, gain: 0.08 }],
            [220, 'tone', { type: 'triangle', freq: 659, dur: 0.1, gain: 0.08 }],
            [330, 'tone', { type: 'triangle', freq: 784, dur: 0.3, gain: 0.09 }]],
    yawn: [[0, 'tone', { type: 'sine', freq: 540, freqEnd: 250, dur: 0.75, gain: 0.06 }]],
    snore: [[0, 'noise', { filter: 'lowpass', freq: 340, freqEnd: 160, dur: 1.0, gain: 0.035 }]],
    lights: [[0, 'tone', { type: 'sine', freq: 330, freqEnd: 220, dur: 0.3, gain: 0.05 }]],
    wake: [[0, 'tone', { type: 'sine', freq: 659, dur: 0.12, gain: 0.07 }],
           [130, 'tone', { type: 'sine', freq: 784, dur: 0.12, gain: 0.07 }],
           [260, 'tone', { type: 'sine', freq: 988, dur: 0.24, gain: 0.07 }]],
    hello: [[0, 'tone', { type: 'triangle', freq: 659, dur: 0.1, gain: 0.09 }],
            [120, 'tone', { type: 'triangle', freq: 988, dur: 0.18, gain: 0.09 }]],
    growl: [[0, 'tone', { type: 'sawtooth', freq: 95, freqEnd: 62, dur: 0.5, gain: 0.04 }],
            [0, 'noise', { filter: 'lowpass', freq: 220, dur: 0.5, gain: 0.06 }]],
    hiss: [[0, 'noise', { filter: 'highpass', freq: 3000, dur: 0.5, gain: 0.05 }]],
    pop: [[0, 'tone', { type: 'sine', freq: 900, freqEnd: 320, dur: 0.08, gain: 0.07 }]],
    level: [[0, 'tone', { type: 'triangle', freq: 523, dur: 0.12, gain: 0.09 }],
            [120, 'tone', { type: 'triangle', freq: 659, dur: 0.12, gain: 0.09 }],
            [240, 'tone', { type: 'triangle', freq: 784, dur: 0.12, gain: 0.09 }],
            [360, 'tone', { type: 'triangle', freq: 1047, dur: 0.18, gain: 0.1 }],
            [520, 'tone', { type: 'triangle', freq: 1319, dur: 0.4, gain: 0.1 }],
            [520, 'tone', { type: 'sine', freq: 2093, dur: 0.3, gain: 0.03 }]],
    tick: [[0, 'tone', { type: 'square', freq: 1400, dur: 0.03, gain: 0.025 }]]
  };

  var Sound = {
    audio: null, heard: false,
    muted: store('bh-pz-muted') === '1',
    play: function (name) {
      if (this.muted || !this.heard || !global.GameAudio) return;
      var seq = SOUNDS[name];
      if (!seq) return;
      if (!this.audio) {
        this.audio = new GameAudio();
        this.audio.setVolume(0.55);
      }
      var a = this.audio;
      a.resume();
      seq.forEach(function (n) {
        var fire = function () { if (n[1] === 'tone') a.tone(n[2]); else a.noise(n[2]); };
        if (n[0]) setTimeout(fire, n[0]); else fire();
      });
    }
  };
  ['pointerdown', 'keydown'].forEach(function (name) {
    document.addEventListener(name, function () { Sound.heard = true; }, { once: true, capture: true });
  });

  // ============================================================= the models
  /* Everything in the room is a handful of the renderer's own shapes:
     [mesh, x, y, z, sx, sy, sz, colour, extra], extra being { r: [rx, ry,
     rz], a: alpha, m: material, e: emissive }.  A model is drawn about its
     own centre and placed with put(): moved, turned about Y and scaled. */
  var MAT = { metal: 1, neon: 2, glass: 3 };
  var Q = Math.PI / 2;

  function star(colour, r, s, z, kind) {
    var out = [];
    for (var i = 0; i < 5; i++) {
      var a = i * Math.PI * 2 / 5;
      out.push([kind || 'rbox', Math.sin(a) * r, Math.cos(a) * r, z || 0, s[0], s[1], s[2], colour,
                { r: [0, 0, -a] }]);
    }
    return out;
  }

  var MODELS = {
    cookie: star('#e0a84f', 0.09, [0.12, 0.19, 0.06]).concat([
      ['cyl', 0, 0, 0, 0.2, 0.065, 0.2, '#e8b45c', { r: [Q, 0, 0] }],
      ['cyl', 0, 0, 0.03, 0.09, 0.012, 0.09, '#fff2c8', { r: [Q, 0, 0] }],
      ['box', -0.05, 0.06, 0.034, 0.035, 0.035, 0.01, '#6b3d1f'],
      ['box', 0.06, -0.02, 0.034, 0.03, 0.03, 0.01, '#6b3d1f'],
      ['box', -0.02, -0.08, 0.034, 0.03, 0.03, 0.01, '#6b3d1f']]),
    berries: [
      ['cyl', 0, -0.05, 0, 0.34, 0.13, 0.34, '#e8f1ff'],
      ['torus', 0, 0.015, 0, 0.36, 0.3, 0.36, '#bcd0f0'],
      ['sph', -0.07, 0.05, 0.04, 0.1, 0.1, 0.1, '#e6334d'],
      ['sph', 0.07, 0.06, 0.02, 0.1, 0.1, 0.1, '#4a5bd8'],
      ['sph', 0, 0.07, -0.06, 0.1, 0.1, 0.1, '#8e3fbf'],
      ['sph', 0.02, 0.1, 0.07, 0.09, 0.09, 0.09, '#e6334d'],
      ['sph', -0.05, 0.11, -0.02, 0.09, 0.09, 0.09, '#4a5bd8'],
      ['box', 0.02, 0.15, 0.07, 0.02, 0.03, 0.02, '#3fae4a']],
    riceball: [
      ['sph', 0, 0.01, 0, 0.3, 0.27, 0.21, '#fbfbf5'],
      ['sph', 0, 0.11, 0, 0.17, 0.12, 0.16, '#fbfbf5'],
      ['box', 0, -0.07, 0.085, 0.15, 0.12, 0.05, '#1f3a2a']],
    carrot: [
      ['cone', 0, -0.03, 0, 0.13, 0.32, 0.13, '#ff8a2a', { r: [0, 0, Math.PI] }],
      ['box', 0.025, -0.02, 0.06, 0.04, 0.012, 0.012, '#d96c16'],
      ['box', -0.02, -0.09, 0.04, 0.03, 0.012, 0.012, '#d96c16'],
      ['rbox', 0, 0.17, 0, 0.035, 0.13, 0.035, '#3fae4a'],
      ['rbox', -0.04, 0.16, 0, 0.03, 0.12, 0.03, '#56c25e', { r: [0, 0, 0.45] }],
      ['rbox', 0.04, 0.16, 0, 0.03, 0.12, 0.03, '#56c25e', { r: [0, 0, -0.45] }]],
    pudding: [
      ['cyl', 0, -0.04, 0, 0.24, 0.15, 0.24, '#f2d27a'],
      ['cyl', 0, 0.05, 0, 0.21, 0.05, 0.21, '#8a4b1c'],
      ['sph', 0, 0.09, 0, 0.12, 0.07, 0.12, '#fffaf0'],
      ['sph', 0, 0.14, 0, 0.06, 0.06, 0.06, '#e6233d'],
      ['box', 0.01, 0.18, 0, 0.01, 0.04, 0.01, '#3fae4a']],
    pepper: [
      ['sph', 0, -0.02, 0, 0.14, 0.3, 0.14, '#e8281e', { r: [0, 0, 0.45] }],
      ['sph', -0.03, 0.04, 0.04, 0.05, 0.08, 0.03, '#ff7a6a', { r: [0, 0, 0.45] }],
      ['cyl', -0.07, 0.15, 0, 0.04, 0.08, 0.04, '#3fae4a', { r: [0, 0, 0.45] }]],
    mooncake: [
      ['cyl', 0, 0, 0, 0.28, 0.12, 0.28, '#d99a3c', { r: [Q, 0, 0] }],
      ['torus', 0, 0, 0.045, 0.3, 0.4, 0.3, '#c7852c', { r: [Q, 0, 0] }],
      ['cyl', 0, 0, 0.062, 0.19, 0.012, 0.19, '#f0c46a', { r: [Q, 0, 0] }],
      ['cyl', -0.01, 0.0, 0.07, 0.1, 0.008, 0.1, '#fff3b0', { r: [Q, 0, 0] }],
      ['cyl', 0.02, 0.025, 0.074, 0.085, 0.008, 0.085, '#f0c46a', { r: [Q, 0, 0] }]],
    bytebar: [
      ['rbox', 0, 0, 0, 0.3, 0.12, 0.08, '#2b1e4a'],
      ['box', -0.07, 0, 0, 0.035, 0.125, 0.085, '#4ff2ff', { m: MAT.neon }],
      ['box', 0.01, 0, 0, 0.035, 0.125, 0.085, '#ff4fd8', { m: MAT.neon }],
      ['box', 0.13, 0, 0, 0.07, 0.135, 0.09, '#c9c9d6', { m: MAT.metal }]],
    ball: [
      ['sph', 0, 0, 0, 0.4, 0.4, 0.4, '#ff5c93'],
      ['torus', 0, 0, 0, 0.415, 0.32, 0.415, '#ffffff'],
      ['torus', 0, 0, 0, 0.415, 0.32, 0.415, '#ffd23f', { r: [Q, 0, 0] }]],
    plush: star('#ffd23f', 0.13, [0.16, 0.24, 0.14]).concat([
      ['sph', 0, 0, 0, 0.27, 0.27, 0.17, '#ffdf5c'],
      ['box', -0.045, 0.02, 0.085, 0.03, 0.05, 0.02, '#2a1a0a'],
      ['box', 0.045, 0.02, 0.085, 0.03, 0.05, 0.02, '#2a1a0a'],
      ['box', -0.08, -0.03, 0.08, 0.04, 0.02, 0.02, '#ff8fb8'],
      ['box', 0.08, -0.03, 0.08, 0.04, 0.02, 0.02, '#ff8fb8'],
      ['box', 0, -0.035, 0.087, 0.03, 0.012, 0.02, '#2a1a0a']]),
    wand: [
      ['cyl', 0, -0.42, 0, 0.035, 0.84, 0.035, '#b07a4a'],
      ['cyl', 0, -0.78, 0, 0.06, 0.14, 0.06, '#ff5c93'],
      ['sph', 0, 0.02, 0, 0.07, 0.07, 0.07, '#ffd23f', { m: MAT.metal }],
      ['rbox', -0.08, 0.16, 0, 0.08, 0.34, 0.03, '#ff6b9a', { r: [0, 0, 0.45] }],
      ['rbox', 0, 0.2, 0, 0.08, 0.38, 0.03, '#6fd6ff'],
      ['rbox', 0.08, 0.16, 0, 0.08, 0.34, 0.03, '#c79bff', { r: [0, 0, -0.45] }]]
  };

  /* Push a model: at ``at``, turned ``yaw`` about Y (and ``tip`` about its
     own X, for a ball rolling or a treat tipped to her mouth), at ``scale``. */
  function put(renderer, model, at, yaw, scale, tip) {
    var cy = Math.cos(yaw || 0), sy = Math.sin(yaw || 0);
    var ct = Math.cos(tip || 0), st = Math.sin(tip || 0);
    var k = scale || 1;
    for (var i = 0; i < model.length; i++) {
      var p = model[i], x = p[8] || {};
      var lx = p[1] * k, ly = p[2] * k, lz = p[3] * k;
      if (tip) { var y2 = ly * ct - lz * st; lz = ly * st + lz * ct; ly = y2; }
      var r = x.r || [0, 0, 0];
      renderer.pushRaw(p[0], at[0] + lx * cy + lz * sy, at[1] + ly, at[2] - lx * sy + lz * cy,
                       r[0] + (tip || 0), r[1] + (yaw || 0), r[2], p[4] * k, p[5] * k, p[6] * k,
                       rgb(p[7]), x.a, 0, x.m || 0, x.e || 0);
    }
  }

  // ---------------------------------------------------------------- the room
  /* Where things are, in world units: she stands on the rug at the origin
     facing the camera (+Z); the back wall is at z = -3.2. */
  var WALL_Z = -3.2;
  var SPOT = {
    home: [0, 0], bed: [-2.45, -1.35], bowl: [2.15, -0.55], toybox: [3.35, -2.2],
    window: [1.6, -2.3], plant: [-3.6, -1.9]
  };
  var BED_Y = 0.31;

  function hourNow() { var d = new Date(); return d.getHours() + d.getMinutes() / 60; }
  function skyOf(h) {
    if (h >= 7 && h < 17.5) return 'day';
    if ((h >= 17.5 && h < 20) || (h >= 5.5 && h < 7)) return 'dusk';
    return 'night';
  }

  /* The room as a list of parts in the world, for her colours, her bond
     level (a trophy on the shelf for every milestone), whether her bowl has
     anything in it, the sky outside and whether the lamp is on. */
  function buildRoom(look) {
    var c = look.colors || {};
    var hair = c.hair || '#ff8fb8', outfit = c.outfit || '#c2185b', accent = c.accent || '#ffd6ea';
    var paper = mixHex(hair, '#fff4ec', 0.8), stripe = mixHex(hair, '#fff4ec', 0.68);
    var out = [];
    function add(kind, x, y, z, sx, sy, sz, colour, extra) {
      out.push([kind, x, y, z, sx, sy, sz, colour, extra || {}]);
    }
    // the floor: boards running away from you
    add('box', 0, -0.1, -0.6, 17, 0.2, 9.4, '#c99a6b');
    for (var x = -8.1; x <= 8.2; x += 0.78) add('box', x, 0.001, -0.6, 0.025, 0.004, 9.4, '#a97c53');
    for (var z = -2.6; z <= 3.5; z += 2.1) {
      for (var xx = -7.7 + (z % 2 ? 0.39 : 0); xx <= 8; xx += 2.34) {
        add('box', xx, 0.001, z, 0.76, 0.004, 0.025, '#b48659');
      }
    }
    // the rug she stands on, in her colours
    add('cyl', 0, 0.003, 0.15, 3.7, 0.006, 2.7, mixHex(outfit, '#ffffff', 0.25));
    add('cyl', 0, 0.006, 0.15, 3.2, 0.008, 2.25, mixHex(accent, '#ffffff', 0.45));
    add('cyl', 0, 0.009, 0.15, 1.5, 0.006, 1.05, mixHex(hair, '#ffffff', 0.55));
    // the back wall: wallpaper, a dado rail and a skirting board
    add('box', 0, 3, WALL_Z - 0.15, 17, 6, 0.3, paper);
    for (var sx = -7.8; sx <= 8; sx += 1.2) add('box', sx, 3.62, WALL_Z + 0.006, 0.34, 4.85, 0.01, stripe);
    add('box', 0, 0.6, WALL_Z + 0.05, 17, 1.2, 0.1, '#fff6ec');
    for (var px = -7.6; px <= 8; px += 1.6) add('box', px, 0.62, WALL_Z + 0.1, 1.2, 0.78, 0.02, '#f6e6d6');
    add('box', 0, 1.23, WALL_Z + 0.09, 17, 0.1, 0.18, '#e7d2bf');
    add('box', 0, 0.08, WALL_Z + 0.12, 17, 0.16, 0.14, '#d8b896');

    // the window, and what is outside it
    var wx = 1.6, wy = 2.95, sky = skyOf(look.hour);
    var pane = { day: '#9fd4ff', dusk: '#ffb38a', night: '#1c2350' }[sky];
    add('box', wx, wy, WALL_Z + 0.01, 1.7, 1.5, 0.02, pane, { e: 1 });
    if (sky === 'day') {
      add('rbox', wx - 0.35, wy + 0.3, WALL_Z + 0.025, 0.5, 0.16, 0.01, '#ffffff', { e: 1 });
      add('rbox', wx - 0.2, wy + 0.4, WALL_Z + 0.026, 0.3, 0.16, 0.01, '#ffffff', { e: 1 });
      add('rbox', wx + 0.42, wy - 0.25, WALL_Z + 0.025, 0.42, 0.12, 0.01, '#f2f8ff', { e: 1 });
      add('cyl', wx + 0.5, wy + 0.42, WALL_Z + 0.024, 0.26, 0.01, 0.26, '#fff2a8', { r: [Q, 0, 0], e: 1 });
    } else if (sky === 'dusk') {
      add('cyl', wx + 0.1, wy - 0.45, WALL_Z + 0.024, 0.5, 0.01, 0.5, '#ffe08a', { r: [Q, 0, 0], e: 1 });
      add('box', wx, wy - 0.6, WALL_Z + 0.03, 1.7, 0.3, 0.01, '#e98a6a', { e: 1 });
    } else {
      add('cyl', wx + 0.42, wy + 0.32, WALL_Z + 0.024, 0.32, 0.01, 0.32, '#fff4c2', { r: [Q, 0, 0], e: 1 });
      add('cyl', wx + 0.5, wy + 0.37, WALL_Z + 0.028, 0.26, 0.01, 0.26, pane, { r: [Q, 0, 0], e: 1 });
      [[-0.55, 0.45], [-0.2, 0.1], [-0.6, -0.3], [0.1, -0.45], [0.55, -0.2], [-0.05, 0.55]].forEach(function (s) {
        add('box', wx + s[0], wy + s[1], WALL_Z + 0.025, 0.04, 0.04, 0.01, '#ffffff', { e: 1 });
      });
    }
    add('box', wx, wy + 0.81, WALL_Z + 0.06, 1.94, 0.12, 0.1, '#ffffff');
    add('box', wx, wy - 0.81, WALL_Z + 0.06, 1.94, 0.12, 0.1, '#ffffff');
    add('box', wx - 0.91, wy, WALL_Z + 0.06, 0.12, 1.74, 0.1, '#ffffff');
    add('box', wx + 0.91, wy, WALL_Z + 0.06, 0.12, 1.74, 0.1, '#ffffff');
    add('box', wx, wy, WALL_Z + 0.05, 0.06, 1.5, 0.05, '#ffffff');
    add('box', wx, wy, WALL_Z + 0.05, 1.7, 0.06, 0.05, '#ffffff');
    add('box', wx, wy - 0.9, WALL_Z + 0.16, 2.2, 0.08, 0.32, '#f3e4d4');
    var drape = mixHex(outfit, '#ffffff', 0.3);
    add('rbox', wx - 1.14, wy - 0.05, WALL_Z + 0.12, 0.44, 1.95, 0.09, drape);
    add('rbox', wx + 1.14, wy - 0.05, WALL_Z + 0.12, 0.44, 1.95, 0.09, drape);
    add('box', wx - 1.14, wy - 0.25, WALL_Z + 0.18, 0.46, 0.08, 0.04, accent);
    add('box', wx + 1.14, wy - 0.25, WALL_Z + 0.18, 0.46, 0.08, 0.04, accent);
    add('box', wx, wy + 1.06, WALL_Z + 0.12, 2.9, 0.08, 0.08, '#d8b896');
    // a little cactus on the sill
    add('cyl', wx - 0.55, wy - 0.76, WALL_Z + 0.2, 0.18, 0.16, 0.18, '#c8643c');
    add('rbox', wx - 0.55, wy - 0.58, WALL_Z + 0.2, 0.12, 0.24, 0.12, '#58b368');

    // a picture of the two of you, more or less: a heart in her colours
    var fx = -2.0, fy = 3.35;
    add('box', fx, fy, WALL_Z + 0.03, 1.0, 0.82, 0.06, '#8a5a3a');
    add('box', fx, fy, WALL_Z + 0.04, 0.84, 0.66, 0.06, '#fff8f0');
    [[-1, 1], [1, 1], [-2, 0], [-1, 0], [0, 0], [1, 0], [2, 0], [-1, -1], [0, -1], [1, -1],
     [0, -2], [-2, 1], [2, 1]].forEach(function (h, i) {
      if ((h[0] === -2 || h[0] === 2) && h[1] === 1) return;
      add('box', fx + h[0] * 0.075, fy + 0.04 + h[1] * 0.075, WALL_Z + 0.08, 0.075, 0.075, 0.02,
          i < 2 ? mixHex(accent, '#ffffff', 0.4) : hair);
    });
    // the shelf, with a trophy for every bond milestone she has passed
    add('box', fx, 2.12, WALL_Z + 0.2, 2.7, 0.08, 0.36, '#b9875a');
    add('box', fx - 1.1, 2.0, WALL_Z + 0.08, 0.08, 0.2, 0.14, '#9a6c44');
    add('box', fx + 1.1, 2.0, WALL_Z + 0.08, 0.08, 0.2, 0.14, '#9a6c44');
    for (var t = 0; t < (look.level || 0); t++) {
      var tx = fx - 1.12 + t * 0.28, gold = t === look.level - 1 ? '#ffd86b' : '#f3bf3a';
      add('box', tx, 2.19, WALL_Z + 0.2, 0.16, 0.06, 0.14, '#8a5a3a');
      add('sph', tx - 0.035, 2.34, WALL_Z + 0.2, 0.09, 0.09, 0.07, gold, { m: MAT.metal });
      add('sph', tx + 0.035, 2.34, WALL_Z + 0.2, 0.09, 0.09, 0.07, gold, { m: MAT.metal });
      add('box', tx, 2.3, WALL_Z + 0.2, 0.09, 0.09, 0.07, gold, { r: [0, 0, Math.PI / 4], m: MAT.metal });
    }

    // her cushion, where she naps
    var b = SPOT.bed;
    add('cyl', b[0], 0.14, b[1], 2.0, 0.28, 1.65, outfit);
    add('torus', b[0], 0.27, b[1], 2.1, 1.0, 1.75, mixHex(outfit, '#000000', 0.12));
    add('cyl', b[0], 0.29, b[1], 1.65, 0.05, 1.3, mixHex(outfit, '#ffffff', 0.45));
    add('rbox', b[0] - 0.45, 0.42, b[1] - 0.25, 0.6, 0.2, 0.42, mixHex(accent, '#ffffff', 0.3),
        { r: [0, 0.4, 0.1] });
    // her bowl, which has something in it while she is well fed
    var w = SPOT.bowl;
    add('cyl', w[0], 0.11, w[1], 0.82, 0.22, 0.82, '#c9d3e0', { m: MAT.metal });
    add('torus', w[0], 0.22, w[1], 0.86, 0.5, 0.86, '#dde5ef', { m: MAT.metal });
    add('cyl', w[0], 0.222, w[1], 0.64, 0.01, 0.64, '#56606e');
    if (look.fed) {
      add('sph', w[0], 0.22, w[1], 0.58, 0.14, 0.58, '#c47a3a');
      add('sph', w[0] + 0.12, 0.27, w[1] + 0.05, 0.12, 0.08, 0.12, '#a85f26');
      add('sph', w[0] - 0.14, 0.26, w[1] - 0.06, 0.12, 0.08, 0.12, '#d88a48');
    }
    add('box', w[0], 0.12, w[1] + 0.42, 0.34, 0.1, 0.02, accent);
    // her toy box, a ball peeking out
    var tb = SPOT.toybox;
    add('rbox', tb[0], 0.42, tb[1], 1.3, 0.84, 0.86, mixHex(accent, '#ffffff', 0.15));
    add('box', tb[0], 0.42, tb[1] + 0.44, 1.12, 0.12, 0.02, hair);
    add('box', tb[0], 0.88, tb[1] - 0.2, 1.36, 0.08, 0.5, mixHex(accent, '#000000', 0.12),
        { r: [-0.5, 0, 0] });
    add('sph', tb[0] - 0.25, 0.92, tb[1] + 0.05, 0.38, 0.38, 0.38, '#6fdc7a');
    add('sph', tb[0] + 0.25, 0.9, tb[1] + 0.1, 0.3, 0.3, 0.3, '#ffd23f');
    // a plant in the corner
    var pl = SPOT.plant;
    add('cyl', pl[0] - 0.5, 0.3, pl[1] - 0.6, 0.6, 0.6, 0.6, '#c8643c');
    add('cyl', pl[0] - 0.5, 0.62, pl[1] - 0.6, 0.7, 0.1, 0.7, '#d97a50');
    add('sph', pl[0] - 0.5, 1.2, pl[1] - 0.6, 0.75, 0.95, 0.75, '#3f9a3a');
    add('sph', pl[0] - 0.78, 1.55, pl[1] - 0.55, 0.5, 0.62, 0.5, '#4fb04a');
    add('sph', pl[0] - 0.22, 1.5, pl[1] - 0.65, 0.48, 0.6, 0.48, '#58b85a');
    // the lamp by her cushion: on at night and while she sleeps
    var lx = -4.1, lz = -0.55, lit = look.lamp;
    add('cyl', lx, 0.03, lz, 0.55, 0.06, 0.55, '#6a4a3a');
    add('cyl', lx, 1.3, lz, 0.06, 2.6, 0.06, '#6a4a3a');
    add('cone', lx, 2.72, lz, 0.8, 0.55, 0.8, lit ? '#ffe9a8' : mixHex(accent, '#ffffff', 0.5),
        { e: lit ? 0.85 : 0 });
    if (lit) add('sph', lx, 2.5, lz, 0.22, 0.22, 0.22, '#fff6c8', { e: 1 });
    return out;
  }

  function pushRoom(renderer, parts) {
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i], x = p[8], r = x.r || [0, 0, 0];
      renderer.pushRaw(p[0], p[1], p[2], p[3], r[0], r[1], r[2], p[4], p[5], p[6], rgb(p[7]),
                       x.a, 0, x.m || 0, x.e || 0);
    }
  }

  // ================================================================== her
  /* What she is doing is a little script: a list of steps, each an action
     from pet.js's library for a while, optionally walked to first (``to``,
     a spot or a function giving one), hopped to (``hop``), with a line to
     say, a sound, and hooks at its start, every frame and its end.  A new
     script (perform) interrupts the old one and tidies up after it --
     a treat in her hands, a ball in the air.  With nothing to do she idles,
     and every few seconds does something that suits her mood and persona. */
  var her = {
    script: [], step: null, act: 'idle', t: 0, k: 0, moving: 0,
    pose: Pet.restPose(), head: [0, 0], glance: [0, 0], glanceT: 0, gaze: null,
    blinkAt: 1.5, blinkT: -1, idleIn: 2.5, asleep: false, cleanup: null, since: 0,
    stroking: null
  };
  var props = { held: null, ball: null, plush: null, wand: null };

  function pos() { return stage ? stage.pos : [0, 0, 0]; }
  function dist2(a, b) { var x = a[0] - b[0], z = a[1] - b[2]; return Math.sqrt(x * x + z * z); }
  function spotOf(s) { return typeof s === 'function' ? s() : s; }

  function perform(steps, opts) {
    opts = opts || {};
    var old = her.cleanup;
    her.cleanup = opts.cleanup || null;
    // what started it: something she thought of herself ("idle") gives way
    // to a stroke; anything you did for her does not
    her.kind = opts.kind || 'care';
    if (old) old();
    her.script = steps.slice();
    her.step = null;
    nextStep();
  }

  function nextStep() {
    var s = her.script.shift();
    her.step = s || null;
    if (s) { s.started = false; s.t = 0; return; }
    her.idleIn = rand(2.2, 4.5) * (has('energetic') || has('chatty') ? 0.7 : 1);
    if (her.cleanup) { var c = her.cleanup; her.cleanup = null; c(); }
  }

  function has(tag) { return (pet.tags || []).indexOf(tag) >= 0; }
  function busy() { return !!her.step; }

  /* The way to the camera from where she is, for facing you. */
  function yawToCamera() {
    var p = pos();
    return Math.atan2(cam.eye[0] - p[0], cam.eye[2] - p[2]) - 0.18;
  }

  // ---------------------------------------------------- moving about
  var WALK = 1.9, RUN = 4.2;

  function walkToward(dest, dt, speed) {
    var p = pos();
    var dx = dest[0] - p[0], dz = dest[1] - p[2], d = Math.sqrt(dx * dx + dz * dz);
    if (d < 0.06) { her.moving = 0; return true; }
    var step = Math.min(d, speed * dt);
    p[0] += dx / d * step;
    p[2] += dz / d * step;
    if (p[1] > 0) p[1] = Math.max(0, p[1] - dt * 2);
    stage.yaw = angleTo(stage.yaw, Math.atan2(dx, dz), Math.min(1, dt * 9));
    her.moving = speed;
    return false;
  }

  function gaitFor(speed) {
    var species = Pet.species(pet);
    var happy = !NEEDY[care.mood.id];
    var g = Pet.gait(species, speed * 3, happy);
    if (!happy && g === 'skip') g = 'walk';
    if (care.mood.id === 'sad' || care.mood.id === 'exhausted') g = species.gait === 'float' ? 'float' : 'sad_walk';
    return g;
  }

  // ---------------------------------------------------- her idle moments
  var LINES = {
    starving: ['My tummy is SO empty…', 'Food? Please?', '*grumble grumble*'],
    hungry: ['Is it snack time?', '*rumble*', 'I could eat…', 'Something smells nice…'],
    exhausted: ['So… sleepy…', '*yaaawn*', 'Can I have a nap?'],
    sleepy: ['*yawn*', 'Getting sleepy…', 'Nap time soon?'],
    sad: ['…', 'Nobody wants to play…', '*sniff*'],
    lonely: ['Pay me some attention?', 'Pat me?', 'Hey… over here!'],
    bored: ['Bored…', 'Can we play?', 'Throw something!', 'What shall we do?'],
    grubby: ['Itchy!', 'I need a good brush…', '*scratch scratch*'],
    ecstatic: ['Best day EVER!', 'I love it here!', 'La la la~', 'You are the best!'],
    happy: ['Hehe!', 'What a lovely day.', 'Hi {you}!', 'Hm hm hm~'],
    content: ['Hmm hm hm~', 'Nice and cosy.', '…', 'Ooh, what is that?'],
    asleep: ['Zzz…', 'mmm… cookies…', '*snore*', 'Zzz… five more minutes…']
  };
  var TAG_LINES = {
    chatty: ['Did I tell you about my dream?', 'Guess what!', 'Talk to me!'],
    shy: ['(…hi)', '*blush*'],
    feisty: ['Hmph!', 'Bring it on!'],
    dreamy: ['I wonder what clouds taste like…', 'Look at the sky…'],
    curious: ['What is THAT?', 'Hmm, interesting…'],
    showoff: ['Look at me!', 'Pretty, right?'],
    brave: ['Nothing scares me!'],
    clingy: ['Don’t go anywhere!', 'Stay with me?'],
    loyal: ['I’m right here.', 'Where you go, I go.'],
    energetic: ['Let’s GO!', 'Zoom zoom!'],
    playful: ['Tag, you’re it!', 'Catch me!'],
    cheerful: ['Yay!', 'Hello hello!'],
    sleepy: ['*yawn*'],
    clumsy: ['Oops!', 'Whoa—']
  };
  var SPECIES_LINES = {
    fern: ['My sprout loves the sun!', 'Photosynthesising…'],
    ember: ['Fired up!', 'Feeling toasty!'],
    luna: ['The stars are out…', 'Floaty~'],
    mochi: ['Boing!', '*ear twitch*'],
    pixel: ['Beep boop!', 'Systems: happy.']
  };

  function line(list) {
    return pick(list).replace('{you}', boot.user || 'you');
  }

  /* Something to do with nothing to do, for how she is feeling. */
  function idleThing() {
    var mood = care.mood.id, p = pos();
    var home = { to: SPOT.home, act: 'idle', dur: 0.2 };
    var talk = has('chatty') ? 0.6 : (has('shy') ? 0.2 : 0.38);
    var say = Math.random() < talk;
    var steps;
    function thought(text) { return say ? text : ''; }
    if (mood === 'starving' || mood === 'hungry') {
      steps = pick([
        [{ act: 'tummy', sound: 'growl', think: thought(line(LINES[mood])) }],
        [{ to: [SPOT.bowl[0] - 0.9, SPOT.bowl[1] + 0.35], act: 'sniff', face: SPOT.bowl },
         { act: 'beg', think: thought(line(LINES[mood])) }, home],
        [{ act: 'beg', think: thought(line(LINES[mood])) }]
      ]);
    } else if (mood === 'exhausted' || mood === 'sleepy') {
      steps = pick([
        [{ act: 'yawn', sound: 'yawn', think: thought(line(LINES[mood])) }],
        [{ act: 'nod_off', dur: 3.0 }],
        [{ act: 'stretch' }, { act: 'yawn', sound: 'yawn' }]
      ]);
    } else if (mood === 'sad') {
      steps = pick([
        [{ act: 'mope', dur: 5, think: thought(line(LINES.sad)) }],
        [{ act: 'sigh' }],
        [{ act: 'cry', think: thought('*sniff*') }]
      ]);
    } else if (mood === 'lonely' || mood === 'bored') {
      steps = pick([
        [{ act: 'sigh', think: thought(line(LINES[mood])) }],
        [{ act: 'pout', think: thought(line(LINES[mood])) }],
        [{ to: [SPOT.toybox[0] - 1.1, SPOT.toybox[1] + 0.9], act: 'inspect', face: SPOT.toybox,
           think: thought('Play with me?') }, home],
        [{ act: 'beg', think: thought(line(LINES[mood])) }]
      ]);
    } else if (mood === 'grubby') {
      steps = pick([
        [{ act: 'scratch', think: thought(line(LINES.grubby)), start: function () { dust(); } }],
        [{ act: 'sneeze', start: function () { dust(); } }],
        [{ act: 'shake', start: function () { dust(); } }]
      ]);
    } else {
      // happy, content or over the moon: her repertoire, and the room
      var pool = new Pet.Showcase(pet).repertoire();
      if (mood === 'ecstatic') pool = pool.concat(['dance', 'twirl', 'bliss', 'heart', 'sparkle']);
      var chatter = (LINES[mood] || LINES.content).slice();
      (pet.tags || []).forEach(function (t) { if (TAG_LINES[t]) chatter = chatter.concat(TAG_LINES[t]); });
      chatter = chatter.concat(SPECIES_LINES[pet.species] || []);
      var r = Math.random();
      var wander = has('curious') || has('energetic') || has('playful') ? 0.45 : 0.28;
      if (r < wander) {
        steps = pick([
          [{ to: [SPOT.window[0] - 0.2, SPOT.window[1] + 0.5], act: 'look', face: [SPOT.window[0], -3.2],
             think: thought(skyOf(hourNow()) === 'night' ? 'The stars are out…' : 'What a nice day out!') }, home],
          [{ to: [SPOT.plant[0] + 0.9, SPOT.plant[1] + 0.6], act: 'sniff', face: SPOT.plant,
             think: thought('Sniff sniff…') }, home],
          [{ to: [rand(-1.8, 1.8), rand(-1.2, 1.0)], act: pick(['look', 'inspect', 'hum']), dur: 2.2 }, home],
          [{ to: [SPOT.bed[0] + 0.95, SPOT.bed[1] + 0.55], act: 'idle', dur: 0.1 },
           { hop: [SPOT.bed[0], BED_Y, SPOT.bed[1]], act: 'jump', dur: 0.55 },
           { act: 'lounge', dur: rand(4, 7), think: thought('Comfy…') },
           { hop: [SPOT.bed[0] + 0.95, 0, SPOT.bed[1] + 0.55], act: 'jump', dur: 0.55 }, home]
        ]);
      } else {
        steps = [{ act: pick(pool), say: say ? line(chatter) : '' }];
      }
    }
    // somewhere other than home with nothing to go back for: go home
    if (dist2(SPOT.home, p) > 0.4 && steps[steps.length - 1] !== home) steps.push(home);
    perform(steps, { kind: 'idle' });
  }

  /* While she is asleep: a stream of z's, a soft snore now and then and,
     once in a while, a dream. */
  function sleepTick(dt) {
    her.zzz = (her.zzz || 0) - dt;
    if (her.zzz <= 0) {
      her.zzz = calm() ? 2.6 : 1.3;
      emit('zzz', headPoint(0.1), 1);
    }
    her.dream = (her.dream === undefined ? 6 : her.dream) - dt;
    if (her.dream <= 0) {
      her.dream = rand(12, 20);
      say(line(LINES.asleep), { think: true, dur: 3 });
      if (Math.random() < 0.5) Sound.play('snore');
    }
  }

  // ---------------------------------------------------- the pose
  /* The mood lays itself over whatever she is doing: drooping when she is
     sad or tired, glowing when she is over the moon. */
  function tone(p, act) {
    var mood = care.mood.id;
    var idleish = act === 'idle' || act === 'walk' || act === 'look' || act === 'hum';
    if (mood === 'sad' || mood === 'lonely') {
      if (!p.brows) p.brows = 'sad';
      p.perk = Math.min(p.perk, 0.3); p.earL -= 0.3; p.earR -= 0.3; p.flame *= 0.5; p.glow *= 0.6;
      if (idleish && p.mouth === 'smile') p.mouth = 'flat';
    } else if (mood === 'sleepy' || mood === 'exhausted') {
      if (idleish && (p.eyes === 'open' || p.eyes === 'happy')) p.eyes = 'half';
      p.perk = Math.min(p.perk, 0.4); p.flame *= 0.6;
    } else if (mood === 'starving' || mood === 'hungry') {
      if (idleish && p.mouth === 'smile') p.mouth = 'wavy';
      if (!p.brows && mood === 'starving') p.brows = 'worry';
    } else if (mood === 'ecstatic') {
      p.blush += 0.35; p.perk = Math.max(p.perk, 1); p.glow = Math.max(p.glow, 0.9);
      if (idleish && p.eyes === 'open') p.eyes = 'happy';
    } else if (mood === 'grubby') {
      if (idleish && p.mouth === 'smile') p.mouth = 'wavy';
    }
  }

  function headPoint(up) {
    return Pet.headTop(pos(), her.pose).map(function (v, i) { return i === 1 ? v + (up || 0) : v; });
  }
  function mouthPoint() {
    var p = pos(), y = stage ? stage.yaw : 0;
    var lift = (her.pose.bob || 0) + (her.pose.float || 0) - (her.pose.sit || 0) * 0.6;
    return [p[0] + Math.sin(y) * 0.5, p[1] + 1.62 + lift, p[2] + Math.cos(y) * 0.5];
  }
  function handsPoint(fwd, up) {
    var p = pos(), y = stage ? stage.yaw : 0;
    var lift = (her.pose.bob || 0) + (her.pose.float || 0) - (her.pose.sit || 0) * 0.6;
    return [p[0] + Math.sin(y) * (fwd || 0.55), p[1] + (up || 1.42) + lift, p[2] + Math.cos(y) * (fwd || 0.55)];
  }

  /* One frame of her: the script, then the pose it makes. */
  function think(dt) {
    var s = her.step, p = pos();
    her.since += dt;
    var faceYaw = null;
    if (s) {
      if (!s.started) {
        var dest = spotOf(s.to);
        if (dest && !walkToward(dest, dt, s.run ? RUN : WALK)) {
          her.act = gaitFor(s.run ? RUN : WALK);
          her.t += dt;
          return pose(dt, her.act, her.t, 0);
        }
        s.started = true;
        s.t = 0;
        s.from = p.slice();
        her.moving = 0;
        if (s.say || s.think) say(s.say || s.think, { think: !s.say });
        if (s.sound) Sound.play(s.sound);
        if (s.start) s.start(s);
      }
      s.t += dt;
      if (s.hop) {
        var u = smooth(s.t / (s.dur || 0.55));
        p[0] = lerp(s.from[0], s.hop[0], u);
        p[1] = lerp(s.from[1], s.hop[1], u) + Math.sin(u * Math.PI) * 0.5;
        p[2] = lerp(s.from[2], s.hop[2], u);
        stage.yaw = angleTo(stage.yaw, Math.atan2(s.hop[0] - s.from[0], s.hop[2] - s.from[2]) || stage.yaw,
                            Math.min(1, dt * 8));
      }
      if (s.tick) s.tick(dt, s.t, s);
      if (s.face) {
        var f = spotOf(s.face);
        if (f === 'cam') faceYaw = yawToCamera();
        else if (f) faceYaw = Math.atan2(f[0] - p[0], f[1] - p[2]);
      }
      var dur = s.dur !== undefined ? s.dur : (Pet.DURATION[s.act] || 1.6);
      her.act = s.act;
      her.t = s.t;
      her.k = s.k || 0;
      if (!s.hold && dur > 0 && s.t >= dur) {
        if (s.done) s.done(s);
        if (her.step === s) nextStep();
      }
    } else if (her.asleep) {
      her.act = Pet.species(pet).id === 'mochi' || has('sleepy') ? 'snooze' : 'nestle';
      her.t += dt;
      sleepTick(dt);
    } else {
      her.act = her.stroking ? 'stroked' : 'idle';
      her.k = her.stroking ? her.stroking.k : 0;
      her.t += dt;
      her.idleIn -= dt;
      if (her.idleIn <= 0 && !her.stroking && !drag.on) idleThing();
    }
    if (faceYaw === null && !her.moving && !(s && s.hop)) {
      faceYaw = her.asleep ? 0.35 : yawToCamera();
    }
    if (faceYaw !== null) stage.yaw = angleTo(stage.yaw, faceYaw, Math.min(1, dt * 5));
    return pose(dt, her.act, her.t, her.k);
  }

  function pose(dt, act, t, k) {
    var species = Pet.species(pet);
    var target = Pet.restPose();
    var grounded = act === 'nestle' || act === 'snooze' || act === 'lounge' || act === 'mope' ||
                   act === 'sit' || act === 'wake_up' || act === 'sleep';
    if (species.gait === 'float' && !grounded) Pet.act('float', her.since * 0.5, null, target);
    target.lean = 0; target.legL = target.legR = target.legL * 0.5;
    var dur = Pet.DURATION[act];
    Pet.act(act, dur ? Math.min(t, dur + 0.5) : t, k, target);
    if (species.eyes && target.eyes === 'open') target.eyes = species.eyes;
    if (species.mouth && target.mouth === 'smile') target.mouth = species.mouth;
    tone(target, act);
    // where she is looking: at something (a ball, a treat, your finger),
    // or about the room
    var p = pos(), hy = 0, hp = 0;
    var look = her.gaze;
    if (look && !her.asleep) {
      var lx = look[0] - p[0], lz = look[2] - p[2], ly = look[1] - (p[1] + 2.0);
      var raw = Math.atan2(lx, lz) - stage.yaw;
      while (raw > Math.PI) raw -= Math.PI * 2;
      while (raw < -Math.PI) raw += Math.PI * 2;
      hy = clamp(raw, -1.0, 1.0);
      hp = clamp(-Math.atan2(ly, Math.hypot(lx, lz) + 0.01), -0.6, 0.45);
    } else if (!her.asleep) {
      her.glanceT -= dt;
      if (her.glanceT <= 0) {
        her.glanceT = rand(1.2, 3.6);
        her.glance = Math.random() < 0.45 ? [0, 0] : [rand(-0.7, 0.7), rand(-0.25, 0.35)];
      }
      if (act === 'idle') hy = her.glance[0] * 0.3;
    }
    var ease = Math.min(1, dt * 6);
    her.head[0] = lerp(her.head[0], hy, ease);
    her.head[1] = lerp(her.head[1], hp, ease);
    target.headYaw += her.head[0];
    target.headPitch += her.head[1];
    target.lookX += clamp(her.head[0] * 0.6, -0.7, 0.7) + (look ? 0 : her.glance[0]);
    target.lookY += clamp(-her.head[1] * 0.8, -0.6, 0.8) + (look ? 0 : her.glance[1]);
    // blinks, now and then a double
    her.blinkAt -= dt;
    if (her.blinkAt <= 0) {
      her.blinkT = 0;
      her.blinkAt = Math.random() < 0.2 ? 0.28 : rand(1.8, 5) * (NEEDY[care.mood.id] ? 0.7 : 1);
    }
    if (her.blinkT >= 0) {
      her.blinkT += dt;
      target.blink = her.blinkT < 0.13 ? 1 : 0;
      if (her.blinkT > 0.13) her.blinkT = -1;
    }
    var snap = act === 'catch' || act === 'pounce' || act === 'tickled' ? 18 : 12;
    her.pose = Pet.blend(her.pose, target, Math.min(1, dt * snap));
    her.pose.spin = target.spin;
    return her.pose;
  }

  // ======================================================= camera and lights
  var canvas = document.getElementById('pz-canvas');
  var stageEl = document.getElementById('pz-stage');
  var FOV = 30;
  var cam = { eye: [0, 2.7, 8.7], target: [0, 1.25, 0], x: 0, z: 0, nap: 0, w: 1, h: 1, dt: 0 };
  var light = { dim: 0, night: skyOf(hourNow()) === 'night' ? 1 : 0 };

  /* Far enough back that she and a little of her room always fit -- a tall
     phone room is mostly her, a wide desktop one shows the room round her
     -- and following her about the room. */
  function placeCamera() {
    var aspect = Math.max(0.4, cam.w / Math.max(1, cam.h));
    var tan = Math.tan(FOV / 2 * Math.PI / 180);
    var dist = clamp(Math.max(5.3 / (2 * tan), 4.5 / (2 * tan * aspect)), 9, 14);
    var p = pos(), dt = cam.dt;
    // a tray open over the bottom of the room: step back and look a little
    // lower, so she stays in the part you can see
    var tray = root.querySelector('.pz-tray:not([hidden])');
    cam.cover = lerp(cam.cover || 0, tray ? clamp(tray.offsetHeight / cam.h, 0, 0.45) : 0, Math.min(1, dt * 6));
    dist *= 1 + cam.cover * 0.55;
    var reach = clamp(2.9 - (aspect - 0.8) * 1.6, 0.6, 2.8);
    cam.x = lerp(cam.x, clamp(p[0] * 0.85, -reach, reach), Math.min(1, dt * 2.2));
    cam.z = lerp(cam.z, clamp(p[2] * 0.5, -1, 0.6), Math.min(1, dt * 2));
    cam.nap = lerp(cam.nap, her.asleep ? 1 : 0, Math.min(1, dt * 1.5));
    var sway = calm() ? 0 : Math.sin(her.since * 0.27) * 0.06;
    var tilt = 0.17 + cam.nap * 0.05;
    var ty = 1.5 - cam.nap * 0.45 - cam.cover * dist * tan * 0.95;
    dist *= 1 - cam.nap * 0.08;
    cam.target = [cam.x, ty, cam.z];
    cam.eye = [cam.x + sway * dist * 0.4, ty + Math.sin(tilt) * dist, cam.z + Math.cos(tilt) * dist];
    return { eye: cam.eye, target: cam.target, fov: FOV };
  }

  function mix3(a, b, k) { return [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)]; }
  /* A warm room by day, a dimmer one at night, and nearly dark (with the
     lamp on) while she sleeps. */
  function setLights(renderer) {
    light.dim = lerp(light.dim, her.asleep ? 1 : 0, Math.min(1, cam.dt * (calm() ? 6 : 1.6)));
    var d = light.dim, n = light.night * 0.35;
    renderer.sunColor = mix3(mix3([1.0, 0.94, 0.85], [0.78, 0.7, 0.62], n), [0.26, 0.27, 0.5], d);
    renderer.skyAmbient = mix3(mix3([0.6, 0.56, 0.62], [0.45, 0.42, 0.55], n), [0.19, 0.2, 0.4], d);
    renderer.groundAmbient = mix3([0.34, 0.28, 0.26], [0.1, 0.1, 0.2], d);
    renderer.sky.sun = [0.3, 0.86, 0.6];
  }

  // ============================================================ the overlay
  /* What is painted over the finished frame, in the canvas's own pixels:
     particles (hearts, crumbs, bubbles, z's, confetti...), the hand that
     pats and strokes her, the brush, and the dark of the room while she
     naps.  Everything is placed by projecting a point in the room through
     this stage's own camera (kept from the last frame). */
  var VP = new Float32Array(16), INV = new Float32Array(16), haveVP = false;

  function project(w) {
    var x = w[0], y = w[1], z = w[2];
    var cx = VP[0] * x + VP[4] * y + VP[8] * z + VP[12];
    var cy = VP[1] * x + VP[5] * y + VP[9] * z + VP[13];
    var cw = VP[3] * x + VP[7] * y + VP[11] * z + VP[15];
    if (cw <= 0.0001) return [-999, -999, 0];
    return [(cx / cw * 0.5 + 0.5) * cam.w, (0.5 - cy / cw * 0.5) * cam.h, cw];
  }

  /* Where a point on the screen (CSS pixels in the room) meets the floor. */
  function floorAt(sx, sy) {
    if (!haveVP) return null;
    var nx = sx / cam.w * 2 - 1, ny = 1 - sy / cam.h * 2;
    function un(z) {
      var x = INV[0] * nx + INV[4] * ny + INV[8] * z + INV[12];
      var y = INV[1] * nx + INV[5] * ny + INV[9] * z + INV[13];
      var zz = INV[2] * nx + INV[6] * ny + INV[10] * z + INV[14];
      var w = INV[3] * nx + INV[7] * ny + INV[11] * z + INV[15];
      return [x / w, y / w, zz / w];
    }
    var a = un(-1), b = un(1);
    if (Math.abs(b[1] - a[1]) < 1e-6) return null;
    var t = -a[1] / (b[1] - a[1]);
    if (t < 0) return null;
    return [a[0] + (b[0] - a[0]) * t, 0, a[2] + (b[2] - a[2]) * t];
  }

  // --------------------------------------------------- pixel sprites
  function sprite(rows, palette) {
    var c = document.createElement('canvas');
    c.width = rows[0].length; c.height = rows.length;
    var g = c.getContext('2d');
    rows.forEach(function (row, y) {
      for (var x = 0; x < row.length; x++) {
        var col = palette[row[x]];
        if (!col) continue;
        g.fillStyle = col;
        g.fillRect(x, y, 1, 1);
      }
    });
    return c;
  }
  var HEART_ROWS = ['.KK.KK.', 'KRRKRRK', 'KRWRRRK', 'KRRRRRK', '.KRRRK.', '..KRK..', '...K...'];
  var SPRITES = {
    heart: sprite(HEART_ROWS, { K: '#7a1240', R: '#ff5c93', W: '#ffd6ea' }),
    heart2: sprite(HEART_ROWS, { K: '#6a1030', R: '#ff3d6e', W: '#ffc2da' }),
    gold: sprite(HEART_ROWS, { K: '#7a4a00', R: '#ffc83d', W: '#fff2b0' }),
    sparkle: sprite(['...W...', '...Y...', '..YWY..', 'WYWWWYW', '..YWY..', '...Y...', '...W...'],
                    { W: '#ffffff', Y: '#ffe066' }),
    note: sprite(['...KKKK', '...K..K', '...K..K', '...K..K', '.KKK.KK', 'KKKKKKK', '.KK.KK.'],
                 { K: '#5a3a8a' }),
    drop: sprite(['..K..', '.KBK.', 'KBWBK', 'KBBBK', '.KKK.'], { K: '#1d5d9b', B: '#6fc6ff', W: '#e6f6ff' }),
    star: sprite(['...K...', '..KYK..', 'KKYYYKK', 'KYYWYYK', '.KYYYK.', 'KYK.KYK', 'KK...KK'],
                 { K: '#7a4a00', Y: '#ffd23f', W: '#fff6c8' })
  };

  // --------------------------------------------------- particles
  var parts = [];
  var CONFETTI = ['#ff5c93', '#ffd23f', '#6fdc7a', '#6fd6ff', '#c79bff', '#ff9f43'];

  /* ``kind`` at a point in the room (or on the screen, with opts.screen). */
  function emit(kind, at, n, opts) {
    opts = opts || {};
    var s = opts.screen ? at : (haveVP ? project(at) : [cam.w / 2, cam.h / 2, 8]);
    if (s[0] < -500) return;
    var scale = clamp(9 / (s[2] || 9), 0.6, 1.6) * clamp(cam.h / 480, 0.75, 1.4);
    n = calm() ? Math.max(1, Math.ceil(n / 3)) : n;
    for (var i = 0; i < n && parts.length < 220; i++) {
      var p = { kind: kind, x: s[0] + rand(-8, 8) * scale, y: s[1] + rand(-6, 6) * scale, vx: 0, vy: 0,
                g: 0, life: 0, max: 1.4, size: 1, rot: 0, vr: 0, scale: scale, text: opts.text || '',
                colour: opts.colour || '' };
      switch (kind) {
        case 'heart': case 'heart2': case 'gold':
          p.vx = rand(-40, 40); p.vy = rand(-90, -50); p.max = rand(1.1, 1.7); p.size = rand(2.4, 3.6);
          p.wob = rand(0, 6); break;
        case 'sparkle': case 'star':
          p.x += rand(-30, 30) * scale; p.y += rand(-30, 30) * scale;
          p.vx = rand(-20, 20); p.vy = rand(-30, 10); p.max = rand(0.6, 1.0); p.size = rand(2, 3.4); break;
        case 'note':
          p.vx = rand(-30, 30); p.vy = rand(-70, -40); p.max = 1.6; p.size = 2.6; p.wob = rand(0, 6); break;
        case 'crumb':
          p.vx = rand(-60, 60); p.vy = rand(-60, 10); p.g = 380; p.max = 0.9; p.size = rand(2, 4);
          p.colour = p.colour || pick(['#c9873e', '#e0a84f', '#8a5a2a']); break;
        case 'bubble':
          p.x += rand(-26, 26) * scale; p.vx = rand(-25, 25); p.vy = rand(-50, -20); p.max = rand(0.9, 1.6);
          p.size = rand(4, 9); break;
        case 'zzz':
          p.vx = rand(10, 24); p.vy = -26; p.max = 2.6; p.size = 1; p.wob = rand(0, 6); break;
        case 'steam':
          p.x += rand(-10, 10); p.vx = rand(-12, 12); p.vy = rand(-60, -35); p.max = 1.2; p.size = rand(5, 9);
          p.colour = p.colour || 'rgba(255,255,255,'; break;
        case 'flame':
          p.vx = rand(-30, 30); p.vy = rand(-90, -50); p.max = 0.7; p.size = rand(3, 6); break;
        case 'confetti':
          p.x = rand(0, cam.w); p.y = rand(-40, -5); p.vx = rand(-30, 30); p.vy = rand(40, 120); p.g = 60;
          p.max = rand(1.8, 2.8); p.size = rand(4, 7); p.vr = rand(-8, 8); p.rot = rand(0, 6);
          p.colour = pick(CONFETTI); break;
        case 'pop':
          var a = (i / n) * Math.PI * 2;
          p.vx = Math.cos(a) * 120; p.vy = Math.sin(a) * 120; p.max = 0.45; p.size = 3;
          p.colour = p.colour || '#ffffff'; break;
        case 'dust':
          p.x += rand(-20, 20) * scale; p.vx = rand(-30, 30); p.vy = rand(-30, -5); p.max = 1.0; p.size = rand(4, 8);
          break;
        case 'feather':
          p.vx = rand(-80, 80); p.vy = rand(-120, -40); p.g = 90; p.max = 1.6; p.size = rand(5, 8);
          p.vr = rand(-4, 4); p.colour = pick(['#ff6b9a', '#6fd6ff', '#c79bff']); break;
        case 'text':
          p.vy = -40; p.max = 1.3; p.size = 1; break;
        case 'tear':
          p.vx = rand(-30, 30); p.vy = rand(-40, -10); p.g = 300; p.max = 0.8; p.size = 2.2; break;
      }
      if (calm()) { p.vx *= 0.2; p.vy *= 0.2; p.g *= 0.2; p.vr = 0; }
      parts.push(p);
    }
  }

  function drawParticles(g, k, dt) {
    var alive = [];
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i];
      p.life += dt;
      if (p.life >= p.max) continue;
      alive.push(p);
      p.vy += p.g * dt;
      p.x += p.vx * dt; p.y += p.vy * dt;
      p.rot += p.vr * dt;
      var f = p.life / p.max, fade = f < 0.75 ? 1 : 1 - (f - 0.75) / 0.25;
      var x = p.x * k, y = p.y * k, s = p.scale * k;
      g.globalAlpha = clamp(fade, 0, 1);
      switch (p.kind) {
        case 'heart': case 'heart2': case 'gold': case 'sparkle': case 'note': case 'star':
          var img = SPRITES[p.kind];
          var size = p.size * s * (p.kind === 'sparkle' ? (1 - Math.abs(f - 0.4)) : 1);
          if (p.wob !== undefined) x += Math.sin(p.life * 5 + p.wob) * 6 * k;
          g.drawImage(img, x - img.width * size / 2, y - img.height * size / 2, img.width * size, img.height * size);
          break;
        case 'crumb': case 'confetti':
          g.save(); g.translate(x, y); g.rotate(p.rot);
          g.fillStyle = p.colour;
          var cw = p.size * s, ch = p.kind === 'confetti' ? cw * 0.5 : cw;
          g.fillRect(-cw / 2, -ch / 2, cw, ch);
          g.restore(); break;
        case 'bubble':
          g.strokeStyle = 'rgba(120,190,255,.9)'; g.lineWidth = 1.5 * k;
          g.fillStyle = 'rgba(220,240,255,.35)';
          g.beginPath(); g.arc(x, y, p.size * s * (1 + f * 0.3), 0, Math.PI * 2); g.fill(); g.stroke();
          g.fillStyle = 'rgba(255,255,255,.95)';
          g.fillRect(x - p.size * s * 0.45, y - p.size * s * 0.45, 2 * k, 2 * k);
          break;
        case 'zzz':
          var zs = (10 + f * 12) * s;
          g.font = 'bold ' + Math.round(zs) + 'px Verdana, sans-serif';
          g.lineWidth = 3 * k; g.strokeStyle = 'rgba(30,20,70,.75)'; g.fillStyle = '#e9e4ff';
          var zx = x + Math.sin(p.life * 2 + p.wob) * 8 * k;
          g.strokeText('z', zx, y); g.fillText('z', zx, y);
          break;
        case 'steam': case 'dust':
          g.fillStyle = p.kind === 'dust' ? 'rgba(150,130,110,' + (0.45 * fade) + ')' : p.colour + (0.6 * fade) + ')';
          g.globalAlpha = 1;
          g.beginPath(); g.arc(x, y, p.size * s * (1 + f * 1.2), 0, Math.PI * 2); g.fill(); break;
        case 'flame':
          g.fillStyle = f < 0.4 ? '#ffe066' : (f < 0.7 ? '#ff9f43' : '#e8281e');
          var fs = p.size * s * (1 - f * 0.6);
          g.fillRect(x - fs / 2, y - fs / 2, fs, fs); break;
        case 'pop':
          g.fillStyle = p.colour;
          g.fillRect(x - 2 * k, y - 2 * k, 4 * k, 4 * k); break;
        case 'feather':
          g.save(); g.translate(x, y); g.rotate(p.rot + Math.sin(p.life * 6) * 0.6);
          g.fillStyle = p.colour;
          g.beginPath(); g.ellipse(0, 0, p.size * s * 0.35, p.size * s, 0, 0, Math.PI * 2); g.fill();
          g.restore(); break;
        case 'text':
          g.font = 'bold ' + Math.round(14 * s) + 'px Verdana, sans-serif';
          g.textAlign = 'center';
          g.lineWidth = 3.5 * k; g.strokeStyle = '#3a0f24'; g.fillStyle = p.colour || '#ffd6ea';
          g.strokeText(p.text, x, y); g.fillText(p.text, x, y);
          g.textAlign = 'start'; break;
        case 'tear':
          var dimg = SPRITES.drop;
          g.drawImage(dimg, x - 5 * s, y - 5 * s, 10 * s, 10 * s); break;
      }
    }
    g.globalAlpha = 1;
    parts = alive;
  }

  function dust() { emit('dust', [pos()[0], pos()[1] + 0.9, pos()[2]], 5); }

  // --------------------------------------------------- the hand and the brush
  /* A pixel-art hand that pats and strokes her, and a brush: drawn over the
     room where your finger is (or, from the buttons, by themselves). */
  var tool = { kind: '', x: 0, y: 0, t: 0, until: 0, auto: false };

  function drawHand(g, x, y, k, press) {
    var s = k * clamp(cam.h / 460, 0.8, 1.35);
    g.save();
    g.translate(x, y + press * 6 * s);
    g.lineWidth = 2.5 * s; g.strokeStyle = '#5a2a1a'; g.fillStyle = '#ffd9bf';
    function rr(x0, y0, w, h, r) {
      g.beginPath();
      g.moveTo(x0 + r, y0); g.arcTo(x0 + w, y0, x0 + w, y0 + h, r); g.arcTo(x0 + w, y0 + h, x0, y0 + h, r);
      g.arcTo(x0, y0 + h, x0, y0, r); g.arcTo(x0, y0, x0 + w, y0, r); g.closePath();
      g.fill(); g.stroke();
    }
    for (var f = 0; f < 4; f++) rr((-19 + f * 9.5) * s, -26 * s, 9 * s, 22 * s, 4.5 * s);
    rr(-21 * s, -12 * s, 40 * s, 26 * s, 9 * s);
    rr(13 * s, -6 * s, 16 * s, 9 * s, 4.5 * s);
    g.fillStyle = 'rgba(255,170,150,.55)';
    g.beginPath(); g.ellipse(-2 * s, 2 * s, 9 * s, 5 * s, 0, 0, Math.PI * 2); g.fill();
    g.restore();
  }

  function drawBrush(g, x, y, k, tilt) {
    var s = k * clamp(cam.h / 460, 0.8, 1.35);
    g.save();
    g.translate(x, y); g.rotate(-0.5 + tilt * 0.25);
    g.lineWidth = 2.5 * s; g.strokeStyle = '#3a1f12';
    g.fillStyle = '#b07a4a';
    g.fillRect(-5 * s, 4 * s, 10 * s, 38 * s); g.strokeRect(-5 * s, 4 * s, 10 * s, 38 * s);
    g.fillStyle = '#ff8fb8';
    g.fillRect(-16 * s, -10 * s, 32 * s, 15 * s); g.strokeRect(-16 * s, -10 * s, 32 * s, 15 * s);
    g.fillStyle = '#ffffff';
    for (var b = 0; b < 6; b++) g.fillRect((-14 + b * 5.2) * s, -20 * s, 3 * s, 10 * s);
    g.restore();
  }

  // --------------------------------------------------- the speech bubble
  var bubble = document.getElementById('pz-bubble');
  var talk = { until: 0, text: '' };
  function say(text, opts) {
    opts = opts || {};
    if (!text || !bubble) return;
    bubble.textContent = text;
    bubble.classList.toggle('think', !!opts.think);
    bubble.hidden = false;
    bubble.classList.remove('pop');
    void bubble.offsetWidth;
    bubble.classList.add('pop');
    talk.until = now() + (opts.dur || clamp(1.8 + text.length * 0.05, 2, 4.2));
    talk.text = text;
  }

  /* Paint everything over the frame, and keep the DOM bits (the bubble)
     over her head. */
  function overlay(g, st, renderer) {
    VP.set(renderer.viewProj);
    INV.set(renderer.invViewProj);
    haveVP = true;
    var k = canvas.width / Math.max(1, cam.w), dt = cam.dt;
    // the dark while she sleeps, and the lamp's warm pool by her cushion
    if (light.dim > 0.02) {
      g.fillStyle = 'rgba(14,12,44,' + (0.34 * light.dim) + ')';
      g.fillRect(0, 0, canvas.width, canvas.height);
      var lamp = project([-4.1, 2.4, -0.55]);
      var grad = g.createRadialGradient(lamp[0] * k, lamp[1] * k, 4, lamp[0] * k, lamp[1] * k, 260 * k);
      grad.addColorStop(0, 'rgba(255,214,140,' + (0.28 * light.dim) + ')');
      grad.addColorStop(1, 'rgba(255,214,140,0)');
      g.fillStyle = grad;
      g.fillRect(0, 0, canvas.width, canvas.height);
    }
    drawParticles(g, k, dt);
    // the hand or the brush
    if (tool.kind && now() < tool.until) {
      tool.t += dt;
      var tx = tool.x, ty = tool.y;
      if (tool.auto) {
        var h = project(headPoint(-0.25));
        tx = h[0] + Math.sin(tool.t * (tool.kind === 'brush' ? 7 : 3)) * (tool.kind === 'brush' ? 34 : 6);
        ty = h[1] + (tool.kind === 'brush' ? 26 : 0) + Math.abs(Math.sin(tool.t * 9)) * (tool.kind === 'hand' ? -16 : 4);
      }
      if (tool.kind === 'hand') drawHand(g, tx * k, ty * k, k, tool.auto ? 0 : Math.abs(Math.sin(tool.t * 9)) * 0.5);
      else drawBrush(g, tx * k, ty * k, k, Math.sin(tool.t * 7));
    } else if (tool.kind && !tool.held) {
      tool.kind = '';
    }
    // the bubble rides over her head
    if (bubble && !bubble.hidden) {
      if (now() > talk.until) { bubble.hidden = true; }
      else {
        var top = project(headPoint(0.25));
        var bw = bubble.offsetWidth || 120;
        var bx = clamp(top[0], bw / 2 + 6, cam.w - bw / 2 - 6);
        var by = Math.max(top[1], (bubble.offsetHeight || 30) + 54);
        bubble.style.left = bx + 'px';
        bubble.style.top = by + 'px';
      }
    }
    screenCache();
  }

  /* Where she and the things you can tap are on the screen this frame. */
  var scr = { head: [0, 0, 40], body: [0, 0, 40], mouth: [0, 0], bowl: [0, 0, 0], toybox: [0, 0, 0],
              bed: [0, 0, 0] };
  function screenCache() {
    var p = pos(), hp = project(headPoint(-0.55)), feet = project(p), top = project(headPoint(0));
    var r = Math.abs(feet[1] - top[1]);
    scr.head = [hp[0], hp[1], r * 0.26];
    var mid = project([p[0], p[1] + 0.95 + (her.pose.bob || 0), p[2]]);
    scr.body = [mid[0], mid[1], r * 0.22];
    var m = project(mouthPoint());
    scr.mouth = [m[0], m[1]];
    var b = project([SPOT.bowl[0], 0.2, SPOT.bowl[1]]);
    scr.bowl = [b[0], b[1], r * 0.18];
    var t = project([SPOT.toybox[0], 0.5, SPOT.toybox[1]]);
    scr.toybox = [t[0], t[1], r * 0.24];
    var bd = project([SPOT.bed[0], 0.25, SPOT.bed[1]]);
    scr.bed = [bd[0], bd[1], r * 0.3];
  }

  // ============================================================ her needs
  /* ``care`` is the server's last word on her (app/models/pet_care.py's
     describe()); between words the needs run down here at the server's
     own rates, and her mood follows, so the meters are live. */
  var care = boot.care;
  var careAt = now();

  function needsNow() {
    var el = Math.max(0, now() - careAt), n = {}, r = care.rates || {};
    var asleepFor = 0;
    NEEDS.forEach(function (k) { n[k] = care.needs[k]; });
    if (care.napping) {
      var gain = care.nap_gain || 0.2;
      asleepFor = Math.min(el, Math.max(0, (100 - n.energy) / gain));
      n.energy += gain * asleepFor;
      NEEDS.forEach(function (k) { if (k !== 'energy') n[k] -= (r[k] || 0) * (care.nap_slow || 0.5) * asleepFor; });
    }
    var awake = el - asleepFor;
    NEEDS.forEach(function (k) { n[k] = clamp(n[k] - (r[k] || 0) * awake, 0, 100); });
    return n;
  }

  /* app/models/pet_care.py's mood_of(), so her mood can change between
     answers (the next answer has the last word). */
  function moodOf(n, napping) {
    if (napping) return 'asleep';
    var f = n.fullness, h = n.happiness, e = n.energy, c = n.cleanliness;
    if (f < 15) return 'starving';
    if (e < 15) return 'exhausted';
    if (h < 20) return 'sad';
    if (f < 35) return 'hungry';
    if (e < 30) return 'sleepy';
    if (c < 25) return 'grubby';
    if (h < 40) return has('clingy') ? 'lonely' : 'bored';
    if (h >= 85 && Math.min(f, e, c) >= 60) return 'ecstatic';
    if (h >= 65 && Math.min(f, e, c) >= 40) return 'happy';
    return 'content';
  }

  function napLeft() {
    if (!care.napping) return 0;
    return Math.max(0, (care.nap_left || 0) - (now() - careAt));
  }
  function cooling(action) {
    return Math.max(0, ((care.cooldowns || {})[action] || 0) - (now() - careAt));
  }

  // ---------------------------------------------------------------- the HUD
  var hud = {
    meters: {}, acts: {}, live: document.getElementById('pz-live'),
    mood: $('#pz-mood'), moodLabel: $('#pz-mood-label'), moodLine: $('#pz-mood-line'),
    nap: $('#pz-nap'), napLeft: $('#pz-nap-left'), greet: $('#pz-greet'), offline: $('#pz-offline'),
    hint: $('#pz-hint')
  };
  $$('.pz-meter').forEach(function (li) {
    hud.meters[li.dataset.need] = { li: li, fill: li.querySelector('.pz-m-fill'), val: li.querySelector('.pz-m-val'),
                                   track: li.querySelector('.pz-m-track'), shown: -1 };
  });
  $$('.pz-act').forEach(function (b) {
    hud.acts[b.dataset.act] = { el: b, name: b.querySelector('.pz-act-name'), cd: b.querySelector('.pz-cd') };
  });

  function announce(text) { if (hud.live) hud.live.textContent = text; }

  function setMood(id) {
    var info = MOODS[id] || {};
    care.mood = { id: id, label: info.label || id, line: info.line || '', need: info.need || '',
                  needy: !!NEEDY[id] };
  }

  var lastMood = care.mood.id;
  function paint() {
    var n = needsNow();
    var mood = moodOf(n, care.napping);
    if (mood !== care.mood.id) setMood(mood);
    NEEDS.forEach(function (k) {
      var m = hud.meters[k];
      if (!m) return;
      var v = n[k], whole = Math.round(v);
      m.fill.style.width = v.toFixed(1) + '%';
      if (whole !== m.shown) {
        m.shown = whole;
        m.val.textContent = whole;
        m.track.setAttribute('aria-valuenow', whole);
      }
      m.li.classList.toggle('low', v < 25);
    });
    if (hud.mood) {
      hud.mood.className = 'pz-mood mood-' + care.mood.id;
      hud.mood.title = care.mood.line;
      hud.moodLabel.textContent = care.mood.label;
    }
    if (hud.moodLine) hud.moodLine.textContent = care.mood.line;
    if (care.mood.id !== lastMood) {
      var was = lastMood;
      lastMood = care.mood.id;
      moodChanged(was, care.mood.id);
    }
    // the buttons: cooling down, asleep, the one that would help
    var asleep = !!care.napping;
    root.classList.toggle('is-napping', asleep);
    Object.keys(hud.acts).forEach(function (a) {
      var b = hud.acts[a], key = a === 'nap' && asleep ? 'wake' : a;
      var left = cooling(key), full = (ACTIONS[key] || {}).cooldown || 1;
      b.el.classList.toggle('cooling', left > 0.05);
      if (b.cd) b.cd.style.setProperty('--cd', (left / full).toFixed(3));
      b.el.classList.toggle('off', asleep && a !== 'nap');
      b.el.classList.toggle('needed', !asleep && a === care.mood.need);
      b.el.classList.toggle('loved', (care.loves || []).indexOf(a) >= 0);
      var label = a === 'nap' ? (asleep ? 'Wake' : 'Nap') : (ACTIONS[a] || {}).name || a;
      if (b.name && b.name.textContent !== label) b.name.textContent = label;
      var tip = label + (left > 0.05 ? ' — ready in ' + Math.ceil(left) + 's' : '') +
                (asleep && a !== 'nap' ? ' — she is asleep' : '');
      b.el.setAttribute('aria-label', tip);
      b.el.title = tip;
    });
    // the treat tray knows when she is busy eating
    var feedLeft = cooling('feed');
    $$('#pz-tray-feed .pz-item').forEach(function (it) { it.classList.toggle('cooling', feedLeft > 0.05); });
    if (hud.nap) {
      hud.nap.hidden = !asleep;
      if (asleep) {
        var left = napLeft();
        hud.napLeft.textContent = left > 90 ? 'She’ll wake up in about ' + Math.round(left / 60) + ' minutes.'
          : (left > 5 ? 'She’ll wake up in a minute or so.' : 'She’s stirring…');
      }
    }
    if (hud.greet) hud.greet.hidden = !care.greet_ready || asleep;
    var flag = root.querySelector('.pz-who.on');
    if (flag) {
      flag.classList.toggle('needy', !!care.mood.needy);
      flag.title = pet.name + ' · ' + care.mood.label;
    }
  }

  function paintBond() {
    var b = care.bond;
    var set = function (sel, text) { var el = $(sel); if (el) el.textContent = text; };
    set('#pz-level-name', b.name);
    set('#pz-bond-lv', b.level + 1);
    set('#pz-bond-name', b.name);
    set('#pz-bond-blurb', b.blurb);
    var lvl = $('#pz-level');
    if (lvl) lvl.title = b.blurb;
    var bar = $('#pz-bond-bar');
    if (bar) {
      bar.setAttribute('aria-valuenow', Math.round(b.progress * 100));
      bar.querySelector('.pz-bond-fill').style.width = (b.progress * 100).toFixed(1) + '%';
    }
    var next = $('#pz-bond-next');
    if (next) {
      next.innerHTML = b.next ? b.points + ' / ' + b.next.at + ' to <b>' + esc(b.next.name) + '</b>'
        : b.points + ' &mdash; as close as two can be';
    }
    var today = $('#pz-bond-today');
    if (today) today.innerHTML = 'Bond today: <b>' + b.today + '</b> / ' + b.cap +
      (b.today >= b.cap ? ' &mdash; she&rsquo;s had all the fuss she can take today' : '');
    set('#pz-streak', care.streak > 1 ? care.streak + '-day streak' : '');
    $$('#pz-miles li').forEach(function (li, i) {
      var m = boot.milestones[i];
      li.classList.toggle('got', b.points >= m.at);
      li.classList.toggle('here', i === b.level);
    });
  }

  function names(list, table) {
    return list.map(function (id) { return (table[id] || {}).name || id; });
  }
  function paintAbout() {
    var set = function (sel, text) { var el = $(sel); if (el) el.textContent = text; };
    set('#pz-loves', (care.loves || []).length ? care.loves.map(function (a) { return LOVE_WORDS[a] || a; }).join(', ') : 'everything, a bit');
    set('#pz-dislikes', (care.dislikes || []).length ? care.dislikes.map(function (a) { return LOVE_WORDS[a] || a; }).join(', ') : 'nothing at all');
    set('#pz-fave-treat', (TREATS[care.favourite_treat] || {}).name || '—');
    set('#pz-fave-toy', (TOYS[care.favourite_toy] || {}).name || '—');
    $$('#pz-tray-feed .pz-item').forEach(function (it) { it.classList.toggle('fave', it.dataset.treat === care.favourite_treat); });
    $$('#pz-tray-play .pz-item').forEach(function (it) { it.classList.toggle('fave', it.dataset.toy === care.favourite_toy); });
    var mem = $('#pz-memories');
    if (mem) {
      var days = Math.max(1, Math.round((care.now - care.since) / 86400) + 1);
      var html = '<li>Together <b>' + days + '</b> day' + (days === 1 ? '' : 's') + '</li>';
      Object.keys(VERB).forEach(function (k) {
        var n = (care.counts || {})[k] || 0;
        if (n) html += '<li>' + VERB[k] + ' <b>' + n + '</b></li>';
      });
      if (care.streak > 1) html += '<li>Hello streak <b>' + care.streak + '</b></li>';
      mem.innerHTML = html;
    }
  }

  /* A new word from the server: take it, and redraw everything from it. */
  function receive(c) {
    if (!c || c.inv_id !== pet.inv_id) return;
    var levelBefore = care.bond ? care.bond.level : 0;
    care = c;
    careAt = now();
    lastMood = lastMood || c.mood.id;
    paint();
    paintBond();
    paintAbout();
    if (care.bond.level !== levelBefore) roomDirty = true;
    // she woke up by herself while nobody was looking
    if (!care.napping && her.asleep && !busy()) wakeUp(false);
    if (care.napping && !her.asleep && !busy()) tuckIn(true);
  }

  // ======================================================== looking after her
  /* Every action goes: is it possible right now (asleep? stuffed? still
     busy?) -- if not, she says so and nothing is sent; otherwise her
     reaction starts and the meters move at once, and the server's answer,
     which carries her whole state, then has the last word.  If the answer
     never comes, the meters go back to where they were. */
  var inflight = 0;
  var online = navigator.onLine !== false;
  var cappedSaid = false;

  function rebase() {
    var n = needsNow(), cd = {};
    Object.keys(care.cooldowns || {}).forEach(function (a) { cd[a] = cooling(a); });
    care.needs = n;
    care.cooldowns = cd;
    care.nap_left = napLeft();
    careAt = now();
  }

  function predict(action, item) {
    var fx;
    if (action === 'feed') fx = TREATS[item] || {};
    else if (action === 'play') fx = TOYS[item] || {};
    else if (action === 'greet') fx = { happiness: 10 };
    else fx = EFFECTS[action] || {};
    var loved = (care.loves || []).indexOf(action) >= 0 || (action === 'feed' && item === care.favourite_treat);
    var disliked = (care.dislikes || []).indexOf(action) >= 0;
    var out = {};
    NEEDS.forEach(function (k) {
      var v = fx[k] || 0;
      if (k === 'happiness' && v > 0) v *= (loved ? 1.5 : 1) * (disliked && !loved ? 0.5 : 1);
      out[k] = v;
    });
    return out;
  }

  function refusal(action, item) {
    var n = needsNow();
    if (care.napping && action !== 'wake') return 'asleep';
    if (action === 'wake' && !care.napping) return 'awake';
    if (action === 'greet') return care.greet_ready ? '' : 'greeted';
    if (cooling(action) > 0.05) return 'cooldown';
    if (action === 'feed' && n.fullness >= LIMIT.full) return 'full';
    if (action === 'play' && n.energy < LIMIT.tired) return 'tired';
    if (action === 'nap' && n.energy >= LIMIT.notSleepy) return 'not_sleepy';
    if (action === 'brush' && n.cleanliness >= LIMIT.spotless) return 'spotless';
    return '';
  }

  function nudge(action) {
    var b = hud.acts[action === 'wake' ? 'nap' : action];
    if (!b) return;
    b.el.classList.remove('nudge');
    void b.el.offsetWidth;
    b.el.classList.add('nudge');
  }

  /* She says no -- in her own way. */
  function sayNo(reason, action) {
    nudge(action);
    Sound.play('nope');
    switch (reason) {
      case 'asleep':
        say(pick(['Zzz…', 'mmf… zzz…']), { think: true });
        announce(pet.name + ' is asleep. Let her rest, or wake her up.');
        emit('zzz', headPoint(0.1), 1);
        break;
      case 'cooldown':
        var left = Math.ceil(cooling(action));
        announce('Give her a moment — ready in ' + left + ' seconds.');
        if (!busy()) say(pick(['One sec!', 'Hang on!', 'Wait wait!']), { dur: 1.4 });
        break;
      case 'full':
        perform([{ act: 'nope', say: pick(['I’m stuffed!', 'No more… I’m full!']) }, { act: 'tummy', dur: 1.2 }]);
        announce(pet.name + ' is full.');
        break;
      case 'tired':
        perform([{ act: 'yawn', sound: 'yawn', say: 'Too tired to play…' }]);
        announce(pet.name + ' is too tired to play. A nap would help.');
        break;
      case 'not_sleepy':
        perform([{ act: 'shake', say: 'I’m not sleepy!' }, { act: pick(['dance', 'fistpump', 'twirl']) }]);
        announce(pet.name + ' is not sleepy yet.');
        break;
      case 'spotless':
        perform([{ act: 'pose', say: 'Already spotless!', start: function () { emit('sparkle', headPoint(-0.4), 6); } }]);
        announce(pet.name + ' is spotless already.');
        break;
      case 'greeted':
        if (hud.greet) hud.greet.hidden = true;
        break;
    }
  }

  function api(body) {
    if (!global.Site) return Promise.resolve({ ok: false, offline: true });
    return Site.post('/api/pets/care', body).catch(function () { return { ok: false, offline: true }; });
  }

  /* Do ``action`` (with a treat or a toy), showing ``show`` straight away. */
  function act(action, item, show) {
    var no = refusal(action, item);
    if (no) { sayNo(no, action); return false; }
    if (!online) {
      say('…?', { think: true });
      Site.toast && Site.toast('You are offline — she will wait for you.', 'bad');
      return false;
    }
    var before = JSON.stringify(care), beforeAt = careAt;
    rebase();
    var guess = predict(action, item);
    NEEDS.forEach(function (k) { care.needs[k] = clamp(care.needs[k] + guess[k], 0, 100); });
    if (action !== 'greet') care.cooldowns[action] = (ACTIONS[action] || {}).cooldown || 3;
    if (action === 'nap') { care.napping = true; care.nap_left = Math.round((100 - care.needs.energy) / (care.nap_gain || 0.2)); }
    if (action === 'wake') care.napping = false;
    if (action === 'greet') care.greet_ready = false;
    paint();
    bump(guess);
    if (show) show();
    hideHint();
    inflight++;
    var forPet = pet.inv_id;
    api({ inv_id: forPet, action: action, item: item || undefined }).then(function (res) {
      inflight--;
      if (forPet !== pet.inv_id) return;
      if (res && res.ok) {
        setOnline(true);
        receive(res.care);
        landed(action, res.result || {});
        return;
      }
      if (res && res.care) {
        // she said no after all: her state, and her saying it
        receive(res.care);
        sayNo(res.reason, action);
        return;
      }
      care = JSON.parse(before);
      careAt = beforeAt;
      paint();
      if (res && res.offline) {
        setOnline(false);
        say('…?', { think: true });
      } else if (global.Site && Site.toast) {
        Site.toast((res && res.error) || 'Something went wrong. Try again in a moment.', 'bad');
      }
    });
    return true;
  }

  /* The meters' little jump, and what changed, as it happens. */
  function bump(deltas) {
    NEEDS.forEach(function (k) {
      var d = Math.round(deltas[k] || 0), m = hud.meters[k];
      if (!d || !m) return;
      m.li.classList.remove('bump');
      void m.li.offsetWidth;
      m.li.classList.add('bump');
      var tag = document.createElement('span');
      tag.className = 'pz-delta' + (d < 0 ? ' minus' : '');
      tag.textContent = (d > 0 ? '+' : '') + d;
      m.track.appendChild(tag);
      setTimeout(function () { tag.remove(); }, 1500);
    });
  }

  /* The server's answer to something that happened: the bond it was worth,
     a milestone, a streak. */
  function landed(action, result) {
    if (result.bond > 0) {
      setTimeout(function () {
        emit('text', headPoint(0.35), 1, { text: '+' + result.bond + ' ♥', colour: '#ffd6ea' });
      }, 500);
    }
    if (result.capped && !cappedSaid) {
      cappedSaid = true;
      Site.toast && Site.toast(pet.name + ' has had all the fuss she can take for today — the bond grows again tomorrow.', 'info');
    }
    var words = [];
    Object.keys(result.deltas || {}).forEach(function (k) {
      var d = result.deltas[k];
      if (Math.abs(d) >= 1) words.push((boot.needLabels || {})[k] + ' ' + (d > 0 ? '+' : '') + Math.round(d));
    });
    announce(pet.name + (result.loved ? ' loved that! ' : ': ') + words.join(', ') +
             (result.bond ? '. Bond +' + result.bond : '') + '.');
    if (action === 'greet' && result.streak > 1) {
      setTimeout(function () { say(result.streak + ' days in a row! ♥', { dur: 2.6 }); }, 2400);
    }
    if (result.milestone) milestone(result.milestone);
  }

  var burst = $('#pz-burst');
  function milestone(m) {
    if (!burst) return;
    $('#pz-burst-name').textContent = m.name;
    $('#pz-burst-blurb').textContent = m.blurb;
    burst.hidden = false;
    burst.style.animation = 'none';
    void burst.offsetWidth;
    burst.style.animation = '';
    Sound.play('level');
    emit('confetti', [0, 0, 0], 40, { screen: true });
    emit('gold', headPoint(0.2), 8);
    roomDirty = true;
    announce('Bond milestone: ' + m.name + '. ' + m.blurb);
    setTimeout(function () { perform([{ act: 'bliss', say: 'We’re ' + m.name + '!' }]); }, 600);
    clearTimeout(burst._t);
    burst._t = setTimeout(function () { burst.hidden = true; }, 3700);
  }

  var hinted = store('bh-pz-hinted') === '1';
  function hideHint() {
    if (hinted || !hud.hint) return;
    hinted = true;
    store('bh-pz-hinted', '1');
    hud.hint.classList.add('gone');
  }
  if (hinted && hud.hint) hud.hint.classList.add('gone');

  function setOnline(on) {
    online = on;
    if (hud.offline) hud.offline.hidden = on;
    root.classList.toggle('is-offline', !on);
  }

  // ============================================================ her reactions
  /* What each kind of care looks like.  They lean on her persona (the
     actions she loves and dislikes come with her state) and her species'
     favourite treat. */
  function loves(a) { return (care.loves || []).indexOf(a) >= 0; }
  function dislikes(a) { return (care.dislikes || []).indexOf(a) >= 0; }
  function hearts(n, kind) { emit(kind || 'heart', headPoint(-0.2), n); }
  function throwFrom() { return [cam.x + rand(-0.5, 0.5), 1.0, 3.6]; }
  function near(target, gap) {
    var p = pos(), dx = target[0] - p[0], dz = target[2] - p[2], d = Math.sqrt(dx * dx + dz * dz);
    if (d < gap + 0.07) return [p[0], p[2]];
    return [target[0] - dx / d * gap, target[2] - dz / d * gap];
  }
  function poof(at, colour) { emit('pop', at, 10, { colour: colour || '#ffffff' }); emit('sparkle', at, 4); Sound.play('pop'); }

  function showPat(byHand) {
    if (!byHand) { tool.kind = 'hand'; tool.auto = true; tool.t = 0; tool.until = now() + 1.5; }
    Sound.play('pat');
    hearts(3);
    var after;
    if (care.mood.id === 'sad' || care.mood.id === 'lonely') after = { act: 'heart', say: pick(['Thank you…', 'I needed that.']) };
    else if (loves('pat')) after = { act: 'bliss', say: pick(['Mmm, more!', 'Hehe~ ♥', 'Best pats!']), start: function () { hearts(5); } };
    else if (has('shy')) after = { act: 'shy', say: '*blush*' };
    else after = { act: pick(['giggle', 'nod', 'heart']), say: Math.random() < 0.4 ? pick(['Hehe!', '♥', 'Again?']) : '' };
    perform([{ act: 'patted', dur: 1.5 }, after]);
  }

  function showFeed(id, dropped) {
    var treat = TREATS[id] || {};
    var fave = id === care.favourite_treat;
    var from = throwFrom();
    var steps = [];
    if (!dropped) {
      Sound.play('toss');
      props.fly = { model: MODELS[id], from: from, t: 0, T: 0.55, arc: 0.9, to: function () { return handsPoint(0.5, 1.5); } };
      steps.push({ act: 'beg', dur: 0.55, start: function () { her.gaze = from; }, tick: function () {
        if (props.fly) her.gaze = props.fly.at || from;
      } });
    }
    steps.push({ act: 'munch', dur: 1.9, start: function () {
      props.fly = null;
      props.held = { model: MODELS[id], at: 'mouth', scale: 1.25, bite: 0 };
      her.gaze = null;
    }, tick: function (dt, t, s) {
      s.c = (s.c || 0) - dt;
      if (props.held) props.held.bite = t / 1.9;
      if (s.c <= 0) { s.c = 0.32; emit('crumb', mouthPoint(), 3); Sound.play('munch'); }
    }, done: function () { props.held = null; } });
    if (fave) {
      steps.push({ act: 'bliss', say: pick(['My favourite!!', 'The BEST!', 'More ' + (treat.name || 'please') + '!']),
                   start: function () { hearts(8); Sound.play('fave'); } });
    } else if (id === 'pepper') {
      steps.push({ act: 'spicy', say: 'HOT HOT HOT!', start: function () { Sound.play('hiss'); }, tick: function (dt, t, s) {
        s.c = (s.c || 0) - dt;
        if (s.c <= 0) { s.c = 0.12; emit('flame', mouthPoint(), 2); emit('steam', headPoint(0), 1); }
      } });
    } else if (id === 'pudding') {
      steps.push({ act: 'yum', say: 'Wobbly! …and a bit messy.', start: function () { Sound.play('yum'); hearts(2); } });
    } else {
      steps.push({ act: 'yum', say: pick(['Yum!', 'Delicious!', 'Nom nom!', 'Thank you!']),
                   start: function () { Sound.play('yum'); hearts(2); } });
    }
    perform(steps, { cleanup: function () {
      if (props.held || props.fly) poof(mouthPoint());
      props.held = null; props.fly = null; her.gaze = null;
    } });
  }

  // ---------------------------------------------------------------- toys
  var G = 16;
  function launch(from, to, T) {
    return [(to[0] - from[0]) / T, (to[1] - from[1]) / T + 0.5 * G * T, (to[2] - from[2]) / T];
  }

  function showPlay(id, landing) {
    var fave = id === care.favourite_toy;
    var happy = fave ? { act: 'bliss', say: 'My favourite toy!', start: function () { hearts(6); Sound.play('fave'); } }
      : { act: pick(['cheer', 'fistpump', 'giggle']), say: pick(['Again! Again!', 'That was fun!', 'Hehe!']) };
    var cleanup = function () {
      if (props.ball) poof(props.ball.p);
      if (props.plush) poof(props.plush.p);
      if (props.wand) poof(props.wand.at || pos());
      props.ball = props.plush = props.wand = null;
      props.held = null; her.gaze = null;
    };
    if (id === 'ball') {
      var p = pos();
      var reach = cam.w / cam.h > 1.2 ? 3.2 : 2.2;
      var land = landing ? [clamp(landing[0], -4.5, 4.5), 0.2, clamp(landing[2], -2.6, 2.2)]
        : [clamp(p[0] + rand(-1, 1) * reach, -reach, reach), 0.2, rand(-1.8, 1.0)];
      if (Math.abs(land[0] - p[0]) + Math.abs(land[2] - p[2]) < 1.2) land[0] = p[0] + (land[0] < p[0] ? -1.6 : 1.6);
      var from = throwFrom();
      perform([
        { act: 'ready', dur: 0.75, start: function () {
          Sound.play('toss');
          props.ball = { p: from.slice(), v: launch(from, land, 0.8), spin: 0, held: false, bounced: 0 };
        }, tick: function () { her.gaze = props.ball && props.ball.p; } },
        { to: function () { return props.ball ? near(props.ball.p, 0.75) : null; }, run: true, act: 'pounce', dur: 1.25,
          face: function () { return props.ball ? [props.ball.p[0], props.ball.p[2]] : null; },
          tick: function (dt, t) {
            if (props.ball) her.gaze = props.ball.p;
            if (t > 0.45 && t < 0.95 && props.ball && !props.ball.held) {
              var b = props.ball.p, q = pos(), dx = b[0] - q[0], dz = b[2] - q[2], d = Math.hypot(dx, dz);
              if (d > 0.3) { q[0] += dx / d * dt * 1.4; q[2] += dz / d * dt * 1.4; }
            }
            if (t > 0.8 && props.ball && !props.ball.held) { props.ball.held = true; Sound.play('squeak'); }
          } },
        { to: SPOT.home, act: happy.act, say: happy.say, start: function (s) {
          her.gaze = null;
          if (happy.start) happy.start(s);
          if (props.ball) {
            props.ball.held = false;
            props.ball.v = [rand(-1.5, 1.5), 3.5, 1.2];
            props.ball.p = handsPoint(0.7, 1.4);
            props.ball.fade = 1.6;
          }
        } }
      ], { cleanup: cleanup });
    } else if (id === 'plush') {
      var start = throwFrom();
      var target = handsPoint(0.4, 2.15);
      var T = 0.95;
      perform([
        { act: 'ready', dur: T - 0.4, start: function () {
          Sound.play('toss');
          props.plush = { p: start.slice(), v: launch(start, target, T), spin: 0, held: false };
        }, tick: function () { her.gaze = props.plush && props.plush.p; } },
        { act: 'catch', dur: 1.0, tick: function (dt, t) {
          if (t > 0.38 && props.plush && !props.plush.held) { props.plush.held = true; Sound.play('squeak'); hearts(2); her.gaze = null; }
        } },
        { act: 'cuddle', dur: 2.4, say: fave ? 'I love her!' : pick(['So soft!', 'Squishy!']), tick: function (dt, t, s) {
          s.c = (s.c || 0.2) - dt;
          if (s.c <= 0) { s.c = 0.45; hearts(1); }
        } },
        happy,
        { act: 'idle', dur: 0.1, start: function () { if (props.plush) poof(props.plush.p, '#ffd23f'); props.plush = null; } }
      ], { cleanup: cleanup });
    } else {
      var rounds = 3, side = Math.random() < 0.5 ? -1 : 1;
      props.wand = { side: side, t: 0, caught: false, at: null };
      var steps = [{ act: 'ready', dur: 0.8, start: function () { Sound.play('swish'); poof(wandAt(), '#c79bff'); },
                     face: function () { var w = wandAt(); return [w[0], w[2]]; },
                     tick: function () { her.gaze = wandAt(); } }];
      for (var r = 0; r < rounds; r++) {
        (function (last) {
          steps.push({ act: 'pounce', dur: 1.2, face: function () { var w = wandAt(); return [w[0], w[2]]; },
            start: function (s) { s.base = pos().slice(); s.dir = props.wand ? props.wand.side : 1; },
            tick: function (dt, t, s) {
              var q = pos(), u = Math.sin(clamp((t - 0.4) / 0.75, 0, 1) * Math.PI);
              q[0] = s.base[0] + s.dir * u * 0.45;
              if (props.wand) her.gaze = wandAt();
              if (t > 0.62 && props.wand && !s.flicked) {
                s.flicked = true;
                if (last) { props.wand.caught = true; Sound.play('squeak'); }
                else { props.wand.side = -props.wand.side; Sound.play('swish'); }
              }
            } });
          if (!last) steps.push({ act: 'ready', dur: 0.5, face: function () { var w = wandAt(); return [w[0], w[2]]; } });
        })(r === rounds - 1);
      }
      steps.push({ act: fave ? 'bliss' : 'giggle', say: fave ? 'My favourite toy!' : 'Got it!', start: function () {
        her.gaze = null;
        if (props.wand) emit('feather', props.wand.at || headPoint(-0.5), 10);
        Sound.play(fave ? 'fave' : 'giggle');
        if (fave) hearts(5);
      }, done: function () { if (props.wand) poof(props.wand.at || pos(), '#c79bff'); props.wand = null; } });
      perform(steps, { cleanup: cleanup });
    }
  }

  function wandAt() {
    var w = props.wand, p = pos();
    if (!w) return p;
    if (w.caught) return w.at = handsPoint(0.6, 1.5);
    w.at = [p[0] + w.side * 1.2 + Math.sin(w.t * 3) * 0.15, 1.45 + Math.sin(w.t * 7) * 0.28, p[2] + 0.75];
    return w.at;
  }

  function showBrush(byHand) {
    if (!byHand) { tool.kind = 'brush'; tool.auto = true; tool.t = 0; tool.until = now() + 2.4; }
    var after = dislikes('brush')
      ? { act: 'pout', say: pick(['Hmph. Fine.', 'Not the hair!']) }
      : { act: 'shake_off', start: function () { emit('sparkle', headPoint(-0.5), 8); Sound.play('sparkle'); } };
    perform([
      { act: 'brushed', dur: 2.3, tick: function (dt, t, s) {
        s.c = (s.c || 0) - dt;
        her.k = tool.auto || !tool.kind ? Math.sin(t * 7) : clamp((tool.x - scr.head[0]) / Math.max(10, scr.head[2]), -1, 1);
        if (s.c <= 0) {
          s.c = 0.22;
          emit('bubble', headPoint(-0.45 - Math.random() * 0.6), 1);
          if (Math.random() < 0.5) emit('sparkle', headPoint(-0.4), 1);
        }
        s.snd = (s.snd || 0) - dt;
        if (s.snd <= 0) { s.snd = 0.45; Sound.play('brush'); }
      } },
      after,
      loves('brush') ? { act: 'pose', say: 'So fluffy!', start: function () { hearts(4); } }
        : { act: 'sparkle', say: dislikes('brush') ? '' : pick(['So fluffy!', 'All clean!']) }
    ], { cleanup: function () { if (tool.kind === 'brush') tool.until = 0; } });
  }

  function showTickle() {
    if (dislikes('tickle')) {
      perform([{ act: 'tickled', dur: 1.2, start: function () { Sound.play('giggle'); } },
               { act: 'trip', say: 'Whoa—!' }, { act: 'pout', say: 'Not the tummy!' }]);
      return;
    }
    perform([
      { act: 'tickled', dur: 2.0, start: function () { Sound.play('giggle'); }, tick: function (dt, t, s) {
        s.c = (s.c || 0) - dt;
        if (s.c <= 0) { s.c = 0.3; emit('note', headPoint(-0.3), 1); emit('sparkle', [pos()[0], 1.0, pos()[2]], 1); }
        s.g = (s.g || 0.7) - dt;
        if (s.g <= 0) { s.g = 0.7; Sound.play('giggle'); }
      } },
      loves('tickle') ? { act: 'giggle', say: 'Again! Again!', start: function () { hearts(5); } }
        : { act: 'giggle', say: pick(['Hehehe!', 'That tickles!', 'Stop it! …don’t stop!']) }
    ]);
  }

  function showCheer() {
    Sound.play('cheer');
    emit('confetti', [0, 0, 0], 26, { screen: true });
    var step;
    if (dislikes('cheer')) step = { act: 'shy', say: 'Eep… everyone’s looking…' };
    else if (has('showoff')) step = { act: 'pose', say: 'Ta-da!' };
    else if (loves('cheer')) step = { act: 'dance', dur: 3.0, say: pick(['Woo-hoo!', 'Yay me!']), start: function () { hearts(4); } };
    else if (has('brave') || has('energetic') || has('feisty')) step = { act: 'fistpump', say: 'YEAH!' };
    else step = { act: 'cheer', say: pick(['Woo!', 'Yay!', 'I did it!']) };
    perform([step, { act: 'heart', dur: 1.0 }]);
  }

  /* Off to her cushion, and to sleep -- or, when the page opens on a pet
     already asleep, there already. */
  function tuckIn(instant) {
    var bed = SPOT.bed;
    if (instant) {
      perform([]);
      var p = pos();
      p[0] = bed[0]; p[1] = BED_Y; p[2] = bed[1];
      her.asleep = true;
      light.dim = 1;
      cam.nap = 1;
      cam.x = clamp(bed[0] * 0.85, -2.8, 2.8);
      roomDirty = true;
      return;
    }
    perform([
      { act: 'yawn', sound: 'yawn', say: loves('nap') ? 'Nap time! My favourite…' : '*yaaawn*' },
      { to: [bed[0] + 0.95, bed[1] + 0.6], act: 'idle', dur: 0.05 },
      { hop: [bed[0], BED_Y, bed[1]], act: 'jump', dur: 0.55 },
      { act: 'nestle', dur: 0.05, start: function () {
        her.asleep = true;
        her.zzz = 0.8; her.dream = 8;
        Sound.play('lights');
        roomDirty = true;
      } }
    ]);
  }

  function wakeUp(woken) {
    var bed = SPOT.bed;
    var groggy = woken && needsNow().energy < LIMIT.groggy;
    her.asleep = false;
    roomDirty = true;
    perform([
      { act: 'wake_up', dur: 2.4, start: function () { Sound.play('wake'); } },
      groggy ? { act: 'pout', say: 'Five more minutes…' }
        : { act: 'stretch', say: woken ? pick(['Morning!', 'I’m up, I’m up!']) : 'What a lovely nap!',
            start: function () { emit('sparkle', headPoint(-0.3), 5); } },
      { hop: [bed[0] + 0.95, 0, bed[1] + 0.6], act: 'jump', dur: 0.55 },
      { to: SPOT.home, act: 'idle', dur: 0.1 }
    ]);
  }

  function showGreet() {
    var line2 = care.streak >= 1 ? 'You came back! ♥' : 'Hi! Hi! Hi!';
    perform([
      { act: 'hop_hello', say: 'Hi ' + (boot.user || 'you') + '! ' + line2, start: function () { Sound.play('hello'); hearts(4); } },
      { act: 'heart', dur: 1.2, start: function () { hearts(3); } }
    ]);
  }

  /* When her mood turns by itself, she shows it. */
  function moodChanged(was, id) {
    if (busy() || her.asleep || id === 'asleep') return;
    if (id === 'hungry' || id === 'starving') perform([{ act: 'tummy', sound: 'growl', think: line(LINES[id]) }], { kind: 'idle' });
    else if (id === 'sleepy' || id === 'exhausted') perform([{ act: 'yawn', sound: 'yawn', think: line(LINES[id]) }], { kind: 'idle' });
    else if (id === 'sad' || id === 'lonely' || id === 'bored') perform([{ act: 'sigh', think: line(LINES[id]) }], { kind: 'idle' });
    else if (id === 'grubby') perform([{ act: 'scratch', start: dust }], { kind: 'idle' });
    else if (NEEDY[was]) perform([{ act: 'heart', say: 'I feel much better!', start: function () { hearts(4); } }], { kind: 'idle' });
    else if (id === 'ecstatic') perform([{ act: 'bliss', start: function () { hearts(3); } }], { kind: 'idle' });
  }

  // ================================================================ the stage
  var stage = null;
  var room = { parts: [], key: '', checked: 0 };
  var roomDirty = true;

  function roomLook() {
    var h = hourNow();
    light.night = skyOf(h) === 'night' ? 1 : 0;
    return { colors: pet.colors, level: care.bond.level, fed: needsNow().fullness > 55, hour: h,
             lamp: her.asleep || light.night === 1 };
  }

  function stepBall(b, dt, bouncy) {
    var r = 0.2;
    if (b.held) {
      b.p = bouncy ? handsPoint(0.66, 1.36) : handsPoint(0.42, 1.32);
      b.v = [0, 0, 0];
      return;
    }
    b.v[1] -= G * dt;
    b.p[0] += b.v[0] * dt; b.p[1] += b.v[1] * dt; b.p[2] += b.v[2] * dt;
    if (b.p[1] < r) {
      b.p[1] = r;
      if (bouncy && b.v[1] < -1.6) {
        b.v[1] = -b.v[1] * 0.55; b.v[0] *= 0.78; b.v[2] *= 0.78;
        Sound.play(b.bounced++ ? 'bounce' : 'boing');
        emit('dust', b.p, 2);
      } else {
        b.v[1] = 0;
      }
    }
    if (b.p[1] <= r + 0.001) {
      var f = Math.max(0, 1 - (bouncy ? 1.4 : 5) * dt);
      b.v[0] *= f; b.v[2] *= f;
    }
    if (b.p[2] < WALL_Z + r) { b.p[2] = WALL_Z + r; b.v[2] = Math.abs(b.v[2]) * 0.6; }
    if (b.p[2] > 2.6) { b.p[2] = 2.6; b.v[2] = -Math.abs(b.v[2]) * 0.6; }
    if (Math.abs(b.p[0]) > 6.2) { b.p[0] = 6.2 * Math.sign(b.p[0]); b.v[0] *= -0.6; }
    b.spin += Math.hypot(b.v[0], b.v[2]) * dt / r;
    if (b.fade !== undefined) {
      b.fade -= dt;
      if (b.fade <= 0) b.gone = true;
    }
  }

  /* Everything in the frame but her: the room, and whatever is flying
     about or in her hands. */
  function scene(renderer) {
    var dt = cam.dt, t = now();
    if (roomDirty || t - room.checked > 1) {
      room.checked = t;
      var look = roomLook();
      var key = [pet.inv_id, JSON.stringify(look.colors), look.level, look.fed, skyOf(look.hour), look.lamp].join('|');
      if (roomDirty || key !== room.key) { room.key = key; room.parts = buildRoom(look); }
      roomDirty = false;
    }
    pushRoom(renderer, room.parts);
    var faceCam = function (at) { return Math.atan2(cam.eye[0] - at[0], cam.eye[2] - at[2]); };
    if (props.fly) {
      var f = props.fly;
      f.t += dt;
      var u = clamp(f.t / f.T, 0, 1), to = f.to();
      f.at = [lerp(f.from[0], to[0], u), lerp(f.from[1], to[1], u) + Math.sin(u * Math.PI) * f.arc,
              lerp(f.from[2], to[2], u)];
      if (f.model) put(renderer, f.model, f.at, faceCam(f.at), 1.25, u * 6);
    }
    if (props.held) {
      var h = props.held;
      var at = h.at === 'mouth' ? handsPoint(0.6, 1.5) : handsPoint(0.55, 1.4);
      var k = h.scale * (1 - clamp(h.bite || 0, 0, 1) * 0.55);
      put(renderer, h.model, at, stage.yaw, k, -0.25);
    }
    if (props.ball) {
      stepBall(props.ball, dt, true);
      if (props.ball.gone) { poof(props.ball.p, '#ff5c93'); props.ball = null; }
      else put(renderer, MODELS.ball, props.ball.p, 0, 1, props.ball.spin);
    }
    if (props.plush) {
      stepBall(props.plush, dt, false);
      props.plush.spin += props.plush.held ? 0 : dt * 9;
      put(renderer, MODELS.plush, props.plush.p, props.plush.held ? stage.yaw : faceCam(props.plush.p),
          props.plush.held ? 1.5 : 1.3, props.plush.held ? 0 : props.plush.spin);
    }
    if (props.wand) {
      props.wand.t += dt;
      var w = wandAt();
      put(renderer, MODELS.wand, w, faceCam(w) + Math.sin(props.wand.t * 5) * 0.3, 1.5,
          props.wand.caught ? -0.6 : Math.sin(props.wand.t * 8) * 0.45);
    }
  }

  var director = {
    step: function (dt) { cam.dt = dt; return think(dt); },
    camera: function () { return placeCamera(); },
    light: function (renderer) { setLights(renderer); },
    scene: function (renderer) { scene(renderer); },
    overlay: function (g, st, renderer) { overlay(g, st, renderer); },
    pixels: function () { return [canvas.width, canvas.height]; }
  };

  /* The canvas is the room's size in device pixels (to a point: a big
     desktop room draws at a little under its full resolution). */
  function resize() {
    var w = Math.max(1, stageEl.clientWidth), h = Math.max(1, stageEl.clientHeight);
    var dpr = Math.min(global.devicePixelRatio || 1, 2);
    dpr = Math.min(dpr, 1600 / w, 1200 / h);
    cam.w = w; cam.h = h;
    var cw = Math.max(1, Math.round(w * dpr)), ch = Math.max(1, Math.round(h * dpr));
    if (canvas.width !== cw || canvas.height !== ch) { canvas.width = cw; canvas.height = ch; }
  }

  // ------------------------------------------------- portraits and icons
  var MAT_NAME = { 1: 'metal', 2: 'neon', 3: 'glass' };
  function modelParts(model, scale) {
    return model.map(function (p) {
      var x = p[8] || {};
      return { t: p[0], p: [p[1] * scale, p[2] * scale, p[3] * scale], s: [p[4] * scale, p[5] * scale, p[6] * scale],
               c: p[7], r: x.r || [0, 0, 0], m: MAT_NAME[x.m] };
    });
  }
  /* The switcher's faces and the trays' treats and toys, drawn once through
     the shared renderer. */
  function drawIcons() {
    if (!global.PetStages || !PetStages.still) return;
    $$('canvas[data-pz-thumb]').forEach(function (c) {
      var p = PETS[c.dataset.pzThumb];
      if (!p) return;
      var pose = Pet.restPose();
      pose.eyes = 'happy'; pose.mouth = 'smile'; pose.blush = 0.4;
      var parts = Pet.build(p, { position: [0, 0, 0], yaw: -0.25, pose: pose, time: 1 });
      PetStages.still(c, parts, { eye: [0.35, 2.1, 3.4], target: [0, 1.92, 0], fov: 30 });
    });
    $$('canvas[data-pz-icon]').forEach(function (c) {
      var bits = c.dataset.pzIcon.split(':'), id = bits[1], model = MODELS[id];
      if (!model) return;
      var far = id === 'wand' ? 2.4 : (bits[0] === 'toy' ? 1.15 : 1.2);
      var lift = id === 'wand' ? -0.22 : 0;
      PetStages.still(c, modelParts(model, 1), { eye: [far * 0.25, lift + far * 0.32, far], target: [0, lift, 0], fov: 30 });
    });
  }

  // =============================================================== the input
  function doPat(byHand) { return act('pat', null, function () { showPat(byHand); }); }
  function doFeed(id, dropped) { return act('feed', id, function () { showFeed(id, dropped); }); }
  function doPlay(id, landing) {
    var ok = act('play', id, function () { showPlay(id, landing); });
    if (ok) closeTrays();
    return ok;
  }
  function doBrush(byHand) { return act('brush', null, function () { showBrush(byHand); }); }
  function doNap() { closeTrays(); return act('nap', null, function () { tuckIn(false); }); }
  function doWake() { return act('wake', null, function () { wakeUp(true); }); }
  function doGreet() {
    if (hud.greet) hud.greet.hidden = true;
    return act('greet', null, showGreet);
  }

  /* What is under a point in the room: her head, the rest of her, one of
     the things you can tap, or just the floor. */
  function hit(x, y) {
    function inside(c, k) { var dx = x - c[0], dy = y - c[1]; return dx * dx + dy * dy < c[2] * c[2] * (k || 1); }
    if (inside(scr.head, 1.15)) return 'head';
    if (inside(scr.body, 1.2)) return 'body';
    if (inside(scr.bowl)) return 'bowl';
    if (inside(scr.toybox)) return 'toybox';
    if (inside(scr.bed)) return 'bed';
    return 'floor';
  }
  function local(e) {
    var r = canvas.getBoundingClientRect();
    return [e.clientX - r.left, e.clientY - r.top];
  }

  var finger = null;
  // a finger that lands on her keeps the page from scrolling under it
  stageEl.addEventListener('touchstart', function (e) {
    if (e.touches.length !== 1 || !haveVP) return;
    var r = canvas.getBoundingClientRect(), t = e.touches[0];
    var on = hit(t.clientX - r.left, t.clientY - r.top);
    if (on === 'head' || on === 'body') e.preventDefault();
  }, { passive: false });

  canvas.addEventListener('pointerdown', function (e) {
    if (e.button && e.button !== 0) return;
    var at = local(e), on = hit(at[0], at[1]);
    finger = { id: e.pointerId, x0: at[0], y0: at[1], x: at[0], y: at[1], on: on, travel: 0, mode: '',
               counted: false, beat: 0 };
    if (on === 'head' || on === 'body') {
      try { canvas.setPointerCapture(e.pointerId); } catch (err) { /* fine */ }
      var brushing = her.step && her.step.act === 'brushed';
      finger.mode = brushing ? 'brush' : 'pat';
      if (brushing) { tool.kind = 'brush'; tool.auto = false; tool.held = true; tool.x = at[0]; tool.y = at[1]; tool.until = now() + 60; }
    }
  });

  canvas.addEventListener('pointermove', function (e) {
    var at = local(e);
    if (!finger) {
      if (e.pointerType === 'mouse' && haveVP) {
        var on = hit(at[0], at[1]);
        canvas.style.cursor = on === 'head' || on === 'body' ? 'grab' : (on === 'floor' ? 'default' : 'pointer');
      }
      return;
    }
    if (finger.id !== e.pointerId) return;
    finger.travel += Math.hypot(at[0] - finger.x, at[1] - finger.y);
    finger.x = at[0]; finger.y = at[1];
    if (finger.mode === 'brush') { tool.x = at[0]; tool.y = at[1]; return; }
    if (finger.mode === 'pat' && finger.travel > 14) {
      if (care.napping) { finger.mode = 'none'; return; }
      if (busy() && her.kind !== 'idle') { finger.mode = 'none'; return; }
      finger.mode = 'stroke';
      if (busy()) perform([]);
      her.stroking = { k: 0 };
      canvas.classList.add('stroking');
      tool.kind = 'hand'; tool.auto = false; tool.held = true; tool.until = now() + 60;
      hideHint();
    }
    if (finger.mode === 'stroke') {
      tool.x = at[0]; tool.y = at[1];
      her.stroking.k = clamp((at[0] - scr.head[0]) / Math.max(12, scr.head[2]), -1, 1);
      finger.beat += Math.abs(e.movementX || 0) + Math.abs(e.movementY || 0) || 4;
      if (finger.beat > 70) {
        finger.beat = 0;
        hearts(1);
        Sound.play('stroke');
      }
      if (!finger.counted && finger.travel > 170) {
        finger.counted = true;
        if (refusal('pat') === '') {
          act('pat', null, function () { hearts(3); Sound.play('pat'); say(pick(['Mmmm…', 'Hehe~', '♥ ♥ ♥']), { dur: 1.6 }); });
        }
      }
    }
  });

  function lift(e) {
    if (!finger || (e && finger.id !== e.pointerId)) return;
    var f = finger;
    finger = null;
    canvas.classList.remove('stroking');
    if (f.mode === 'stroke') {
      her.stroking = null;
      tool.held = false; tool.until = now() + 0.2;
      if (f.counted && !busy()) perform([{ act: loves('pat') ? 'bliss' : 'heart', dur: 1.4 }]);
      her.idleIn = Math.max(her.idleIn, 2);
      return;
    }
    if (f.mode === 'brush') { tool.held = false; tool.auto = true; tool.until = Math.min(tool.until, now() + 0.6); return; }
    if (f.travel > 14 || (e && e.type === 'pointercancel')) return;
    // a tap
    if (f.on === 'head' || f.on === 'body') {
      if (care.greet_ready && !care.napping) { doGreet(); return; }
      if (care.napping) { say(pick(['mmf… zzz…', 'Zzz… cookies…']), { think: true }); emit('zzz', headPoint(0.1), 1); return; }
      if (cooling('pat') > 0.05) {
        hearts(1);
        Sound.play('pat');
        if (!busy() || her.kind === 'idle') perform([{ act: pick(['giggle', 'nod', 'ear_twitch']), dur: 1.0 }], { kind: 'idle' });
        return;
      }
      tool.kind = 'hand'; tool.auto = false; tool.held = false; tool.x = f.x; tool.y = f.y - 10; tool.t = 0;
      tool.until = now() + 0.8;
      doPat(true);
      return;
    }
    if (f.on === 'bowl') { openTray('feed'); return; }
    if (f.on === 'toybox') { openTray('play'); return; }
    if (f.on === 'bed') { if (care.napping) say('Zzz…', { think: true }); else doNap(); return; }
    // the floor: she goes to have a look
    var spot = floorAt(f.x, f.y);
    if (spot && !care.napping && (!busy() || her.kind === 'idle')) {
      emit('sparkle', [spot[0], 0.1, spot[2]], 3);
      var dest = [clamp(spot[0], -5, 5), clamp(spot[2], -2.4, 2.2)];
      perform([{ to: dest, act: pick(['sniff', 'look', 'inspect']), dur: 1.8,
                 say: Math.random() < 0.3 ? pick(['What’s over here?', 'Ooh!']) : '' },
               { to: SPOT.home, act: 'idle', dur: 0.2 }], { kind: 'idle' });
    }
  }
  canvas.addEventListener('pointerup', lift);
  canvas.addEventListener('pointercancel', lift);
  canvas.addEventListener('lostpointercapture', function (e) { if (finger && finger.id === e.pointerId) lift(e); });

  // ------------------------------------------------------------- the bar
  function closeTrays() {
    ['feed', 'play'].forEach(function (w) {
      var tray = $('#pz-tray-' + w);
      if (tray) tray.hidden = true;
      var b = hud.acts[w];
      if (b) { b.el.classList.remove('open'); b.el.setAttribute('aria-expanded', 'false'); }
    });
  }
  function openTray(which, toggle) {
    if (care.napping) { sayNo('asleep', which); return; }
    var tray = $('#pz-tray-' + which);
    if (!tray) return;
    var wasOpen = !tray.hidden;
    closeTrays();
    if (wasOpen && toggle) return;
    tray.hidden = false;
    hud.acts[which].el.classList.add('open');
    hud.acts[which].el.setAttribute('aria-expanded', 'true');
    Sound.play('tick');
  }
  ['feed', 'play'].forEach(function (w) {
    if (hud.acts[w]) hud.acts[w].el.setAttribute('aria-controls', 'pz-tray-' + w);
  });

  $('#pz-bar').addEventListener('click', function (e) {
    var b = e.target.closest('.pz-act');
    if (!b) return;
    var a = b.dataset.act;
    b.classList.add('pressed');
    setTimeout(function () { b.classList.remove('pressed'); }, 120);
    if (a === 'nap') { if (care.napping) doWake(); else doNap(); return; }
    if (care.napping) { sayNo('asleep', a); return; }
    if (a === 'feed' || a === 'play') { openTray(a, true); return; }
    closeTrays();
    if (a === 'pat') doPat(false);
    else if (a === 'brush') doBrush(false);
    else if (a === 'tickle') act('tickle', null, showTickle);
    else if (a === 'cheer') act('cheer', null, showCheer);
  });
  $$('.pz-tray [data-close]').forEach(function (x) { x.addEventListener('click', closeTrays); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeTrays(); });
  if (hud.greet) hud.greet.addEventListener('click', doGreet);

  // -------------------------------------------- treats and toys, dragged
  /* Tap a treat and it flies to her; or drag it (on a phone, the natural
     thing) to her mouth -- she watches it come, and opens wide.  A toy
     dragged into the room lands where it is let go. */
  var drag = { on: false, item: null, ghost: null, over: false, just: false };
  function dragEnd(ok) {
    if (drag.item) drag.item.classList.remove('lifted');
    if (drag.ghost) {
      var g = drag.ghost;
      if (!ok) { g.style.transition = 'opacity .25s, transform .25s'; g.style.opacity = '0'; g.style.transform = 'scale(.4)'; }
      setTimeout(function () { g.remove(); }, ok ? 0 : 260);
    }
    her.gaze = null;
    drag.on = false; drag.item = null; drag.ghost = null; drag.over = false;
  }
  $$('.pz-tray .pz-item').forEach(function (item) {
    item.addEventListener('pointerdown', function (e) {
      if (e.button && e.button !== 0) return;
      drag.item = item; drag.id = e.pointerId; drag.x0 = e.clientX; drag.y0 = e.clientY; drag.on = false;
      try { item.setPointerCapture(e.pointerId); } catch (err) { /* fine */ }
    });
    item.addEventListener('pointermove', function (e) {
      if (drag.item !== item || drag.id !== e.pointerId) return;
      if (!drag.on) {
        if (Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0) < 9) return;
        if (care.napping) return;
        drag.on = true;
        item.classList.add('lifted');
        var g = document.createElement('div');
        g.className = 'pz-drag';
        var src = item.querySelector('canvas'), copy = document.createElement('canvas');
        copy.width = src.width; copy.height = src.height;
        copy.getContext('2d').drawImage(src, 0, 0);
        g.appendChild(copy);
        document.body.appendChild(g);
        drag.ghost = g;
        closeTraysSoft(item);
      }
      drag.ghost.style.left = e.clientX + 'px';
      drag.ghost.style.top = e.clientY + 'px';
      var r = canvas.getBoundingClientRect(), lx = e.clientX - r.left, ly = e.clientY - r.top;
      var inRoom = lx >= 0 && ly >= 0 && lx <= r.width && ly <= r.height;
      if (item.dataset.treat) {
        var d = Math.hypot(lx - scr.mouth[0], ly - scr.mouth[1]);
        drag.over = inRoom && d < Math.max(48, scr.head[2] * 1.05);
        drag.ghost.classList.toggle('over', drag.over);
        if (inRoom && !busy()) {
          var p = pos();
          her.gaze = [p[0] + (lx - scr.head[0]) / Math.max(30, scr.head[2]) * 0.6, 1.0 + (scr.head[1] - ly) / Math.max(30, scr.head[2]) * 0.5 + 1.0, p[2] + 1.6];
        }
      } else {
        drag.over = inRoom;
        drag.ghost.classList.toggle('over', inRoom);
      }
    });
    function up(e) {
      if (drag.item !== item) return;
      var was = drag.on, over = drag.over;
      if (!was) { drag.item = null; return; }
      drag.just = true;
      setTimeout(function () { drag.just = false; }, 50);
      if (item.dataset.treat) {
        dragEnd(over);
        if (over) doFeed(item.dataset.treat, true);
        else say(pick(['Hey, come back!', 'Ooh, was that for me?']), { dur: 1.6 });
      } else {
        var r = canvas.getBoundingClientRect();
        var spot = over ? floorAt(e.clientX - r.left, e.clientY - r.top) : null;
        dragEnd(!!spot);
        if (spot) doPlay(item.dataset.toy, spot);
      }
    }
    item.addEventListener('pointerup', up);
    item.addEventListener('pointercancel', function () { if (drag.item === item) dragEnd(false); });
    item.addEventListener('click', function () {
      if (drag.just) return;
      if (item.dataset.treat) doFeed(item.dataset.treat, false);
      else doPlay(item.dataset.toy, null);
    });
  });
  /* A toy tray steps out of the way while a toy is dragged into the room. */
  function closeTraysSoft(item) {
    if (item.dataset.toy) { var t = $('#pz-tray-play'); if (t) t.style.opacity = '.35'; }
    setTimeout(function () { var t2 = $('#pz-tray-play'); if (t2) t2.style.opacity = ''; }, 1600);
  }

  // ========================================================= the switcher
  /* Another of your pets: her state from the server, her room in her
     colours, and in she comes. */
  var switching = 0;
  function switchTo(id) {
    id = +id;
    if (id === pet.inv_id || !PETS[id] || switching) return;
    switching = id;
    closeTrays();
    root.classList.add('is-loading');
    Site.get('/api/pets/care?pet=' + id).then(function (res) {
      switching = 0;
      root.classList.remove('is-loading');
      if (!res || !res.ok) { Site.toast((res && res.error) || 'Could not find her.', 'bad'); return; }
      setOnline(true);
      if (props.ball || props.plush || props.wand || props.held) perform([]);
      poof(headPoint(-0.6), (pet.colors || {}).accent);
      pet = PETS[id];
      care = res.care;
      careAt = now();
      lastMood = care.mood.id;
      cappedSaid = false;
      if (stage) stage.setPet(pet);
      her.asleep = false;
      light.dim = 0;
      paintPet();
      paint(); paintBond(); paintAbout();
      roomDirty = true;
      if (care.napping) {
        tuckIn(true);
      } else if (stage) {
        var p = pos();
        p[0] = -4.6; p[1] = 0; p[2] = 0.8;
        stage.yaw = Q;
        perform([{ to: SPOT.home, run: true, act: 'idle', dur: 0.05 },
                 care.greet_ready ? { act: 'wave', say: 'Hi ' + (boot.user || 'you') + '! Say hello?' }
                   : { act: NEEDY[care.mood.id] ? 'sigh' : 'hop_hello', say: NEEDY[care.mood.id] ? care.mood.line : 'Hi again!' }],
                { kind: 'idle' });
      }
      try { history.replaceState(null, '', '/pet-zone?pet=' + id); } catch (e) { /* fine */ }
    }).catch(function () {
      switching = 0;
      root.classList.remove('is-loading');
      setOnline(false);
    });
  }

  /* Everything on the page that is about who she is. */
  function paintPet() {
    var c = pet.colors || {};
    root.dataset.pet = pet.inv_id;
    root.style.setProperty('--pc', c.hair || '#ff8fb8');
    root.style.setProperty('--po', c.outfit || '#c2185b');
    root.style.setProperty('--pa', c.accent || '#ffd6ea');
    var set = function (sel, text) { var el = $(sel); if (el) el.textContent = text; };
    set('#pz-name', pet.name);
    set('#pz-species', pet.species_name);
    set('#pz-about-name', pet.name);
    set('#pz-about-species', pet.species_name);
    set('#pz-sig-text', ((boot.species || {})[pet.species] || {}).signature || '');
    canvas.setAttribute('aria-label', pet.name + ' in her room');
    var edit = $('#pz-edit');
    if (edit) edit.href = '/pet?pet=' + pet.inv_id;
    var tags = $('#pz-tags');
    if (tags) {
      tags.innerHTML = (pet.tag_info || []).map(function (t) {
        return '<li class="ptag ptag-' + esc(t.id) + '" tabindex="0" data-tip="' + esc(t.blurb) + '">' + esc(t.name) + '</li>';
      }).join('');
    }
    $$('.pz-who[data-pet-id]').forEach(function (b) {
      var on = +b.dataset.petId === pet.inv_id;
      b.classList.toggle('on', on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
      var s = summary[b.dataset.petId];
      if (!on && s) b.classList.toggle('needy', !!s.needy);
    });
    paintFollow();
  }

  function paintFollow() {
    var f = $('#pz-follow'), g = $('#pz-following');
    if (f) f.classList.toggle('hidden', pet.inv_id === active);
    if (g) g.classList.toggle('hidden', pet.inv_id !== active);
  }

  $$('.pz-who[data-pet-id]').forEach(function (b) {
    b.addEventListener('click', function () { switchTo(b.dataset.petId); });
  });
  var follow = $('#pz-follow');
  if (follow) follow.addEventListener('click', function () {
    follow.disabled = true;
    Site.post('/api/pets/active', { inv_id: pet.inv_id }).then(function (res) {
      follow.disabled = false;
      if (!res.ok) { Site.toast(res.error || 'Could not take her along.', 'bad'); return; }
      active = res.active;
      paintFollow();
      Sound.play('cheer');
      perform([{ act: 'salute', say: 'Adventure time! I’ll follow you everywhere.' }]);
      Site.toast(pet.name + ' will follow you in the worlds now.', 'info');
    }).catch(function () { follow.disabled = false; setOnline(false); });
  });

  var mute = $('#pz-mute');
  function paintMute() {
    if (!mute) return;
    mute.setAttribute('aria-pressed', Sound.muted ? 'true' : 'false');
    mute.title = Sound.muted ? 'Sound off' : 'Sound on';
  }
  if (mute) mute.addEventListener('click', function () {
    Sound.muted = !Sound.muted;
    store('bh-pz-muted', Sound.muted ? '1' : '0');
    paintMute();
    if (!Sound.muted) Sound.play('tick');
  });

  // =========================================================== keeping time
  /* The meters and cooldowns redraw four times a second; her state is
     re-read every minute and a half, when the tab comes back, when she
     ought to have woken up by herself and when the connection does. */
  var lastSync = now(), hiddenAt = 0, syncing = false;
  function sync() {
    if (syncing || inflight || switching) return;
    syncing = true;
    lastSync = now();
    var forPet = pet.inv_id;
    Site.get('/api/pets/care?pet=' + forPet).then(function (res) {
      syncing = false;
      if (res && res.ok) { setOnline(true); if (forPet === pet.inv_id) receive(res.care); }
    }).catch(function () { syncing = false; setOnline(false); });
  }

  setInterval(function () {
    if (document.hidden) return;
    paint();
    var t = now();
    if (t - lastSync > 90) sync();
    if (care.napping && napLeft() <= 0 && t - lastSync > 4) sync();
    // her picture and her state disagree, and she is free to fix it
    if (!busy() && !inflight) {
      if (care.napping && !her.asleep) tuckIn(true);
      else if (!care.napping && her.asleep) wakeUp(false);
    }
  }, 250);

  document.addEventListener('visibilitychange', function () {
    if (document.hidden) { hiddenAt = now(); return; }
    if (hiddenAt && now() - hiddenAt > 20) sync();
  });
  global.addEventListener('online', function () { setOnline(true); sync(); });
  global.addEventListener('offline', function () { setOnline(false); });

  // ================================================================== boot
  document.body.classList.add('pz-page');
  resize();
  if (global.ResizeObserver) new ResizeObserver(resize).observe(stageEl);
  else global.addEventListener('resize', resize);
  paintPet();
  paintMute();
  paint();
  paintBond();
  paintAbout();
  setOnline(online);
  stage = global.PetStages ? PetStages.add(canvas, pet, { director: director, drag: false, yaw: 0 }) : null;
  if (!stage) {
    stageEl.classList.add('no-gl');
    var note = document.createElement('p');
    note.className = 'pz-noscript';
    note.textContent = 'Your browser cannot draw her room (WebGL is off), but you can still look after her below.';
    stageEl.appendChild(note);
  } else {
    stage.yaw = 0;
    drawIcons();
    if (care.napping) {
      tuckIn(true);
    } else {
      var hello = care.greet_ready
        ? { act: 'wave', say: 'Hi ' + (boot.user || 'you') + '! Say hello?', start: function () { hearts(2); } }
        : (NEEDY[care.mood.id] ? { act: 'sigh', think: care.mood.line } : { act: 'wave', say: line(LINES[care.mood.id] || LINES.happy) });
      perform([{ act: 'idle', dur: 0.7 }, hello], { kind: 'idle' });
    }
  }
  // for the checks in tools/: what she is doing, and the room's own clock
  global.PetZone = {
    her: her, care: function () { return care; }, pet: function () { return pet; }, act: act,
    props: props, screen: scr, stage: function () { return stage; }, needs: needsNow, moodOf: moodOf
  };
})(window);
