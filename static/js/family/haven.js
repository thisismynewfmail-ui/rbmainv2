/* The haven: a little NoogBlock world under a glass dome.

   Wherever the dome appears -- the landing page (hero), the comparison card
   (mini), the sign-up page (panel) and the set-up wizard (build) -- this
   draws it, live, with the game's own engine (static/js/engine: the same
   renderer, studded plastic, lighting and sky as every world, and the same
   avatar builder as every player).  So it is not a picture of the game; it
   is the game's look, in miniature:

   * a floating island: a studded green baseplate with a sand rim over
     layers of dirt and rock, and a waterfall running off one edge
   * a little town on it: grey studded roads with sidewalks round a plaza
     and its fountain, a house, a glass tower, an apartment block or a
     lighthouse, a playground, a pond with a dock and ducks, a lemonade
     stand, a campfire, street lamps, benches, tiered pines and ball trees
   * kids in the classic blocky build, all in the classic yellow, wearing
     real catalogue faces, hats, hair and clothes (the page hands over a
     small wardrobe), who walk the sidewalks and swing, slide, seesaw,
     bounce, fish, dance, build brick towers, play catch, fly kites, buy
     lemonade, sit by the fire and wave
   * a dog, a cat on the roof, ducks, a car that stops for kids
   * the dome over all of it turns away what flies at it -- messages, rain

   A new little world every visit: the seed picks the layout (mirrored or
   not), the buildings and their colours, who is playing and what they
   wear.  The trees and the ground follow the real season, and events
   (fireworks, balloons, lanterns, bubbles, a dance party, a storm that
   can't get in, then a rainbow) turn up on their own.  A tap on a kid, the
   grass or the sky answers.

   It costs little: everything that stays still is batched once, the loop
   stops off screen and in a hidden tab, a slow device drops its resolution
   and prefers-reduced-motion gets one still frame.  Without WebGL (or the
   engine) the host keeps the still picture it was served with.

   Hooks: an element with data-haven="hero|panel|build|mini" is mounted
   automatically and its world is el.haven.  A blocked message fires
   "haven:blocked" on that element (detail: {icon, title, what} or
   {storm: true, title}).  Build mode takes setStage(n), setName(s),
   setLook({shirt, pants}), setLight(name) and celebrate().
   ?haven-season=spring|summer|autumn|winter, ?haven-seed=N and
   ?haven-light=day|dawn|gold|dusk|night preview a particular world. */
(function (global) {
  'use strict';

  var TAU = Math.PI * 2;
  var query = (function () {
    var out = {};
    var search = (global.location && global.location.search) || '';
    search.replace(/^\?/, '').split('&').forEach(function (kv) {
      if (!kv) return;
      var i = kv.indexOf('=');
      try {
        out[decodeURIComponent(i < 0 ? kv : kv.slice(0, i))] = i < 0 ? '' : decodeURIComponent(kv.slice(i + 1));
      } catch (e) { /* a malformed query is ignored */ }
    });
    return out;
  })();
  var reduced = !!(global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches);

  /* ============================================================ helpers */
  function mulberry(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function clamp(v, a, b) { return v < a ? a : (v > b ? b : v); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function smooth(t) { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); }
  function backOut(t) { t = clamp(t, 0, 1) - 1; return t * t * (2.70158 * t + 1.70158) + 1; }
  function pick(r, list) { return list[Math.floor(r() * list.length) % list.length]; }
  function shuffle(r, list) {
    list = list.slice();
    for (var i = list.length - 1; i > 0; i--) {
      var j = Math.floor(r() * (i + 1)), t = list[i];
      list[i] = list[j]; list[j] = t;
    }
    return list;
  }
  function wrapAngle(a) { a = (a + Math.PI) % TAU; if (a < 0) a += TAU; return a - Math.PI; }
  function turnTo(a, b, step) {
    if (!isFinite(b)) return a;
    if (!isFinite(a)) return b;
    var d = wrapAngle(b - a);
    return a + clamp(d, -step, step);
  }
  function hex2(n) { n = clamp(Math.round(n), 0, 255); return (n < 16 ? '0' : '') + n.toString(16); }
  function rgbOf(hex) {
    hex = String(hex || '#ffffff').replace('#', '');
    if (hex.length === 3) hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    var n = parseInt(hex, 16) || 0;
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function shade(hex, k) {
    var c = rgbOf(hex);
    var f = k >= 0 ? function (v) { return v + (255 - v) * k; } : function (v) { return v * (1 + k); };
    return '#' + hex2(f(c[0])) + hex2(f(c[1])) + hex2(f(c[2]));
  }
  function mixHex(a, b, t) {
    var x = rgbOf(a), y = rgbOf(b);
    return '#' + hex2(lerp(x[0], y[0], t)) + hex2(lerp(x[1], y[1], t)) + hex2(lerp(x[2], y[2], t));
  }
  function rgbf(hex) { var c = rgbOf(hex); return [c[0] / 255, c[1] / 255, c[2] / 255]; }
  function clock() { return (global.performance && performance.now) ? performance.now() : Date.now(); }
  function dist2(ax, az, bx, bz) { var dx = ax - bx, dz = az - bz; return Math.sqrt(dx * dx + dz * dz); }

  /* =========================================================== palettes */
  var SKIN = '#f5cd30';              // everyone in here wears the classic yellow
  var SHIRTS = ['#c4281c', '#0d69ac', '#287f47', '#da8541', '#6b327c', '#f2f3f3', '#1b2a35', '#008f9c', '#e8546e', '#3f7fd1'];
  var PANTS = ['#1b2a35', '#0d69ac', '#a4bd47', '#5b3a29', '#6c7a89', '#2b5fa8', '#343a40'];
  var WALLS = ['#f2f3f3', '#f4e3bd', '#d6e6f5', '#f3d3cf', '#d9ecd0', '#e8e0f5'];
  var ROOFS = ['#c4281c', '#2b5fa8', '#287f47', '#6b327c', '#4a4d55', '#da8541'];
  var BLOCKS = ['#c4281c', '#0d69ac', '#f5cd30', '#287f47', '#da8541', '#f2f3f3', '#6b327c'];
  var CARS = ['#c4281c', '#0d69ac', '#f5cd30', '#f2f3f3', '#287f47', '#da8541'];
  var ROAD = '#5d6168', SIDEWALK = '#b7bcc3', PLAZA = '#a7adb4', CURB = '#8c9198', SAND = '#e3cd8f';
  var DIRT = '#7b5a3c', WOOD = '#a0683a', DARK = '#34373d', METAL = '#8d939c', WATER = '#3d8ee3', WHITE = '#f2f3f3';
  var ROCKS = ['#8b8e93', '#77797e', '#66686d', '#a0a3a8'];

  var SEASON_OF_MONTH = ['winter', 'winter', 'spring', 'spring', 'spring', 'summer', 'summer', 'summer', 'autumn', 'autumn', 'autumn', 'winter'];
  var SEASONS = {
    spring: { grass: '#5cbd60', pine: ['#2f8a3e', '#37994a', '#2a7d38'], balls: ['#ff9ec8', '#ffb7d5', '#ffc9de', '#66c06a'],
              trunk: '#7a4e2c', flowers: ['#ff6fa8', '#ffd23f', '#ffffff', '#b48cff', '#ff9f43'], fall: 'petal' },
    summer: { grass: '#4caf50', pine: ['#2b7d36', '#33913f', '#287233'], balls: ['#3d9f45', '#4cb352', '#358f3d', '#57bb5a'],
              trunk: '#7a4e2c', flowers: ['#ff5a5f', '#ffd23f', '#ff9f1c', '#ffffff', '#b48cff'], fall: 'firefly' },
    autumn: { grass: '#82ad47', pine: ['#2b7d36', '#33913f', '#287233'], balls: ['#e8742a', '#d9442b', '#f2b630', '#c95f2a', '#a3b83a'],
              trunk: '#6e4426', flowers: ['#e8742a', '#c9302c', '#f2b630'], fall: 'leaf', pumpkins: true },
    winter: { grass: '#eef4fb', pine: ['#2c6e3f', '#327a47', '#28663a'], balls: ['#e3edf6', '#d9e6f2'],
              trunk: '#5e3d24', flowers: ['#ff5a5f'], fall: 'snow', snow: true }
  };
  var LIGHTS = {
    day:   { top: '#3a86d6', horizon: '#a8d3f4', clouds: 0.62, sun: [0.42, 0.82, 0.38], sunColor: [1.0, 0.97, 0.9], ambient: '#a9c8e4', night: 0 },
    dawn:  { top: '#6d7dcf', horizon: '#ffc6ab', clouds: 0.5, sun: [0.8, 0.36, 0.42], sunColor: [1.0, 0.84, 0.74], ambient: '#c9adc9', night: 0 },
    gold:  { top: '#5a8ad0', horizon: '#ffd795', clouds: 0.52, sun: [0.7, 0.42, 0.46], sunColor: [1.0, 0.88, 0.66], ambient: '#d8bd90', night: 0 },
    dusk:  { top: '#2e3d80', horizon: '#f2a07e', clouds: 0.36, sun: [0.74, 0.2, 0.5], sunColor: [0.96, 0.66, 0.56], ambient: '#8576aa', night: 0.6 },
    night: { top: '#0a1532', horizon: '#23366e', clouds: 0.16, sun: [0.3, 0.78, 0.42], sunColor: [0.46, 0.53, 0.8], ambient: '#3b4b82', night: 1 }
  };
  var THREATS = [
    { icon: 'at', what: 'an invite to another app', title: 'Safe Chat stopped an invite', text: 'add me on my other app' },
    { icon: 'phone', what: 'a phone number', title: 'Safe Chat blocked a phone number', text: 'whats ur number?' },
    { icon: 'pin', what: 'a home address', title: 'Safe Chat blocked an address', text: 'where do u live?' },
    { icon: 'camera', what: 'a request for photos', title: 'Safe Chat blocked a photo request', text: 'send me a pic' },
    { icon: 'link', what: 'a link to another site', title: 'Safe Chat blocked a link', text: 'click this link!!' }
  ];
  var CHAT = ['gg!', 'yay!', 'wanna build?', 'nice!', 'lol', 'so fun', 'race you!', 'tag!', 'woo!', 'hi!', 'look!', 'best day', ':D', 'again!'];

  /* What each kind of dome is: island radius, how many kids, how often a
     message flies at it, which sky, and how the camera sits. */
  var MODES = {
    hero:  { R: 40, kids: 10, threats: 4.6, events: true, critters: true, light: 'day', town: true,
             az: 0.62, sway: 0.42, pitch: 0.5, fov: 27, margin: 0.035 },
    panel: { R: 40, kids: 7, threats: 6.6, events: true, critters: true, light: 'gold', town: true,
             az: 0.62, sway: 0.42, pitch: 0.5, fov: 27, margin: 0.04 },
    build: { R: 19, kids: 0, threats: 0, events: false, critters: false, light: 'dawn', town: false,
             az: 0.5, sway: 0.3, pitch: 0.46, fov: 27, margin: 0.05 },
    mini:  { R: 14, kids: 1, threats: 0, events: false, critters: false, light: 'day', town: false,
             az: 0.42, sway: 0.18, pitch: 0.36, fov: 25, margin: 0.06 }
  };

  /* A smile, for when the page hands over no wardrobe at all. */
  var SMILE = { item_id: 'face_smile', slot: 'face', tier: 'normal', effect: '',
    data: { shapes: [{ k: 'ellipse', x: -0.22, y: -0.16, w: 0.11, h: 0.16, c: '#1a1a1a' },
                     { k: 'ellipse', x: 0.22, y: -0.16, w: 0.11, h: 0.16, c: '#1a1a1a' },
                     { k: 'arc', x: 0, y: 0.06, r: 0.3, a0: 0.08, a1: 0.42, w: 0.055, c: '#1a1a1a' }] } };

  var WARDROBE = null;
  function wardrobe() {
    if (WARDROBE) return WARDROBE;
    var raw = null;
    var el = global.document && document.getElementById('haven-wardrobe');
    if (el) { try { raw = JSON.parse(el.textContent || '{}'); } catch (e) { raw = null; } }
    raw = raw || {};
    function items(list, slot) {
      return (list || []).filter(function (it) { return it && it.data; }).map(function (it) {
        return { item_id: it.id, slot: slot, data: it.data, tier: 'normal', effect: '' };
      });
    }
    WARDROBE = {
      face: items(raw.face, 'face'), hat: items(raw.hat, 'hat'), hair: items(raw.hair, 'hair'),
      shirt: items(raw.shirt, 'shirt'), pants: items(raw.pants, 'pants'), back: items(raw.back, 'back')
    };
    if (!WARDROBE.face.length) WARDROBE.face = [SMILE];
    return WARDROBE;
  }
  function wearing(list, id) {
    for (var i = 0; i < list.length; i++) if (list[i].item_id === id) return list[i];
    return null;
  }

  /* ======================================================== the builder
     Parts in a prop's own frame (x across, z out of its front, y up from its
     base), placed and turned as one; and mirrored, when the whole island is.
     Every part is the engine's own: {t, p, s, r, c, st, m, a}. */
  function Builder(list, mirror) {
    this.parts = list || [];
    this.mir = mirror || 1;
    this.at(0, 0, 0, 0, 1);
  }
  Builder.prototype.at = function (x, y, z, yaw, k) {
    this.ox = x; this.oy = y; this.oz = z;
    this.yaw = yaw || 0;
    this.c = Math.cos(this.yaw); this.s = Math.sin(this.yaw);
    this.k = k === undefined ? 1 : k;
    return this;
  };
  Builder.prototype.add = function (t, dx, dy, dz, sx, sy, sz, c, o) {
    var k = this.k;
    if (k <= 0.001) return null;
    dx *= k; dy *= k; dz *= k;
    var wx = this.ox + dx * this.c + dz * this.s;
    var wz = this.oz - dx * this.s + dz * this.c;
    var p = { t: t, p: [wx * this.mir, this.oy + dy, wz], s: [sx * k, sy * k, sz * k], c: c };
    var r = o && o.r;
    if (r || this.yaw || this.mir < 0) {
      p.r = [r ? r[0] : 0, ((r ? r[1] : 0) + this.yaw) * this.mir, (r ? r[2] : 0) * this.mir];
    }
    if (o) {
      if (o.st) p.st = 1;
      if (o.m) p.m = o.m;
      if (o.a !== undefined) p.a = o.a;
    }
    this.parts.push(p);
    return p;
  };
  /* the same, from the bottom up: dy0 is where the part starts */
  Builder.prototype.box = function (dx, dy0, dz, sx, sy, sz, c, o) {
    return this.add((o && o.t) || 'box', dx, dy0 + sy / 2, dz, sx, sy, sz, c, o);
  };
  Builder.prototype.point = function (dx, dy, dz) {
    var k = this.k;
    dx *= k; dy *= k; dz *= k;
    return [(this.ox + dx * this.c + dz * this.s) * this.mir, this.oy + dy, this.oz - dx * this.s + dz * this.c];
  };

  /* =========================================================== the props */
  function island(B, R, S, r) {
    B.at(0, 0, 0, 0);
    var grass = S.grass;
    // the studded baseplate, a sand rim, then dirt and rock underneath
    B.add('cyl', 0, -1, 0, R * 2, 2, R * 2, grass, { st: 1 });
    B.add('cyl', 0, -1.7, 0, R * 2 + 3.4, 1.8, R * 2 + 3.4, S.snow ? '#e7eef6' : SAND, { st: 1 });
    B.add('cyl', 0, -4.8, 0, R * 2 + 1.6, 4.6, R * 2 + 1.6, DIRT);
    B.add('cyl', 0, -9.4, 0, R * 1.72, 5, R * 1.72, ROCKS[0]);
    B.add('cyl', 0, -14, 0, R * 1.24, 5, R * 1.24, ROCKS[1]);
    B.add('cone', 0, -21.5, 0, R * 0.86, 11, R * 0.86, ROCKS[2], { r: [Math.PI, 0, 0] });
    // rocks that break up the outline
    var n = Math.max(5, Math.round(R / 4.5));
    for (var i = 0; i < n; i++) {
      var a = (i / n) * TAU + r() * 0.5, rad = R * (0.62 + r() * 0.28), y = -7 - r() * 9;
      var w = 4 + r() * 6;
      B.add('rbox', Math.sin(a) * rad, y, Math.cos(a) * rad, w, w * (0.7 + r() * 0.6), w * (0.8 + r() * 0.4),
            pick(r, ROCKS), { r: [r() * 0.6, r() * TAU, r() * 0.6] });
    }
    for (var j = 0; j < 3; j++) {
      var b = r() * TAU, rr = R * (0.25 + r() * 0.35);
      B.add('cone', Math.sin(b) * rr, -17 - r() * 6, Math.cos(b) * rr, 4 + r() * 3, 8 + r() * 6, 4 + r() * 3,
            pick(r, ROCKS), { r: [Math.PI, 0, 0] });
    }
  }

  function pine(B, x, z, k, S, r) {
    B.at(x, 0, z, r() * TAU, k);
    var col = pick(r, S.pine);
    B.add('cyl', 0, 1.1, 0, 1.1, 2.2, 1.1, S.trunk);
    var tiers = [[6.4, 2.3, 1.8], [5.0, 2.1, 3.9], [3.6, 2.0, 5.8], [2.2, 1.7, 7.6]];
    for (var i = 0; i < tiers.length; i++) {
      var w = tiers[i][0], h = tiers[i][1], y = tiers[i][2];
      B.add('rbox', 0, y + h / 2, 0, w, h, w, shade(col, i * 0.05));
      if (S.snow) B.add('rbox', 0, y + h + 0.15, 0, w * 0.86, 0.45, w * 0.86, '#f7fbff');
    }
  }
  function ballTree(B, x, z, k, S, r) {
    B.at(x, 0, z, r() * TAU, k);
    B.add('cyl', 0, 2.2, 0, 1.2, 4.4, 1.2, S.trunk);
    var col = pick(r, S.balls);
    B.add('sph', 0, 7.2, 0, 7, 6.6, 7, col);
    if (S.snow) B.add('sph', 0, 8.7, 0, 5.4, 3.2, 5.4, '#ffffff');
  }
  function bush(B, x, z, k, S, r) {
    B.at(x, 0, z, r() * TAU, k);
    B.add('sph', 0, 1.0, 0, 3.2, 2.4, 3.0, S.snow ? '#e9f1f8' : shade(pick(r, S.pine), 0.12));
  }
  function flowers(B, x, z, S, r, n, spread) {
    spread = spread || 3;
    for (var i = 0; i < n; i++) {
      var fx = x + (r() - 0.5) * spread, fz = z + (r() - 0.5) * spread;
      B.at(fx, 0, fz, r() * TAU, 0.8 + r() * 0.4);
      B.add('cyl', 0, 0.45, 0, 0.16, 0.9, 0.16, '#3d8f3d');
      B.add('sph', 0, 1.0, 0, 0.62, 0.5, 0.62, pick(r, S.flowers));
    }
  }
  function lampPost(B, x, z, night) {
    B.at(x, 0, z, 0);
    B.add('cyl', 0, 0.25, 0, 0.9, 0.5, 0.9, DARK);
    B.add('cyl', 0, 3.6, 0, 0.36, 6.6, 0.36, DARK);
    B.add('box', 0, 7.0, 0, 1.5, 0.5, 1.5, DARK);
    B.add('sph', 0, 6.55, 0, 0.9, 0.7, 0.9, night ? '#fff1b8' : '#f4f1e6', night ? { m: 'neon' } : null);
  }
  function bench(B, x, z, yaw) {
    B.at(x, 0, z, yaw);
    B.box(-1.6, 0, 0, 0.3, 1.1, 1.2, DARK);
    B.box(1.6, 0, 0, 0.3, 1.1, 1.2, DARK);
    B.box(0, 1.1, 0, 4.2, 0.35, 1.3, WOOD);
    B.box(0, 1.5, -0.55, 4.2, 1.1, 0.25, WOOD);
  }
  function picket(B, x, z, yaw, len) {
    B.at(x, 0, z, yaw);
    var n = Math.max(2, Math.round(len / 1.1));
    for (var i = 0; i <= n; i++) B.box(-len / 2 + (i / n) * len, 0, 0, 0.3, 1.6, 0.3, WHITE);
    B.box(0, 0.5, 0, len, 0.25, 0.2, WHITE);
    B.box(0, 1.1, 0, len, 0.25, 0.2, WHITE);
  }

  /* the classic house: a studded foundation, walls, a gable roof from two
     wedges, a door, framed windows that light up at night, a chimney */
  function house(B, x, z, yaw, look, night, k) {
    B.at(x, 0, z, yaw, k);
    var wall = look.wall, roof = look.roof, glass = night ? '#ffd98a' : '#9fd3ff', gm = night ? { m: 'neon' } : null;
    B.box(0, 0, 0, 12.8, 0.6, 10.8, '#a3a7ad', { st: 1 });
    B.box(0, 0.6, 0, 12, 7, 10, wall);
    B.add('wedge', 0, 9.6, 2.75, 13.4, 4, 5.5, roof);
    B.add('wedge', 0, 9.6, -2.75, 13.4, 4, 5.5, roof, { r: [0, Math.PI, 0] });
    B.box(0, 11.5, 0, 13.6, 0.5, 0.9, shade(roof, -0.25));
    B.box(3.6, 9, -1.6, 1.6, 4, 1.6, '#9b5a43');
    B.box(3.6, 13, -1.6, 2, 0.4, 2, '#7d4634');
    // the door, a step and a knob
    B.box(0, 0.6, 5.05, 3.2, 5.6, 0.3, '#6b4226');
    B.add('sph', 1.0, 3.2, 5.3, 0.35, 0.35, 0.35, '#f2c230', { m: 'metal' });
    B.box(0, 0, 5.9, 4.6, 0.4, 1.6, '#a3a7ad', { st: 1 });
    // windows: front two, two each side
    var spots = [[-3.8, 5.02, 0], [3.8, 5.02, 0], [6.02, 2.4, Math.PI / 2], [6.02, -2.4, Math.PI / 2],
                 [-6.02, 2.4, -Math.PI / 2], [-6.02, -2.4, -Math.PI / 2]];
    for (var i = 0; i < spots.length; i++) {
      var w = spots[i];
      B.add('box', w[0], 4.4, w[1], 3.0, 2.8, 0.3, WHITE, { r: [0, w[2], 0] });
      B.add('box', w[0] + Math.sin(w[2]) * 0.08, 4.4, w[1] + Math.cos(w[2]) * 0.08, 2.4, 2.2, 0.3, glass, { r: [0, w[2], 0], m: gm && gm.m });
      B.add('box', w[0] + Math.sin(w[2]) * 0.12, 4.4, w[1] + Math.cos(w[2]) * 0.12, 0.2, 2.2, 0.3, WHITE, { r: [0, w[2], 0] });
    }
    // flower boxes under the front windows
    B.box(-3.8, 2.5, 5.45, 3.0, 0.7, 0.7, WOOD);
    B.box(3.8, 2.5, 5.45, 3.0, 0.7, 0.7, WOOD);
  }

  function glassTower(B, x, z, yaw, night, r) {
    B.at(x, 0, z, yaw);
    var h = 22, glass = '#4a86d4';
    B.box(0, 0, 0, 10.4, 0.6, 10.4, '#9da2a9', { st: 1 });
    B.box(0, 0.6, 0, 9, h, 9, glass, { m: 'metal' });
    for (var f = 1; f <= 5; f++) B.box(0, 0.6 + f * (h / 5.5) - 0.2, 0, 9.3, 0.4, 9.3, '#26364b');
    var cols = [-4.5, -1.5, 1.5, 4.5];
    for (var c = 0; c < cols.length; c++) {
      B.box(cols[c], 0.6, 4.55, 0.4, h, 0.3, '#26364b');
      B.box(cols[c], 0.6, -4.55, 0.4, h, 0.3, '#26364b');
      B.box(4.55, 0.6, cols[c], 0.3, h, 0.4, '#26364b');
      B.box(-4.55, 0.6, cols[c], 0.3, h, 0.4, '#26364b');
    }
    B.box(0, h + 0.6, 0, 9.6, 0.9, 9.6, '#26364b');
    B.box(-1.8, h + 1.5, 1.2, 3, 1.6, 2.4, '#aab0b8');
    B.add('cyl', 2.6, h + 4.6, -2, 0.3, 6, 0.3, METAL);
    B.add('sph', 2.6, h + 7.8, -2, 0.7, 0.7, 0.7, '#ff4d4d', { m: 'neon' });
    B.box(0, 0.6, 4.75, 3.2, 4.6, 0.3, '#9fd3ff', { m: 'metal' });
    if (night) {
      for (var w = 0; w < 14; w++) {
        var fl = 1 + Math.floor(r() * 5), col = Math.floor(r() * 3), side = Math.floor(r() * 2);
        var px = -3 + col * 3, py = 0.6 + fl * (h / 5.5) - 2.1;
        B.box(px, py, side ? 4.62 : -4.62, 2.4, 2.6, 0.2, '#ffe39a', { m: 'neon' });
      }
    }
  }

  function apartment(B, x, z, yaw, colour, night, r) {
    B.at(x, 0, z, yaw);
    B.box(0, 0, 0, 13.6, 0.6, 9.6, '#a3a7ad', { st: 1 });
    B.box(0, 0.6, 0, 13, 13, 9, colour);
    B.box(0, 13.6, 0, 13.6, 0.8, 9.6, shade(colour, -0.28));
    for (var fl = 0; fl < 3; fl++) {
      for (var c = 0; c < 4; c++) {
        if (fl === 0 && (c === 1 || c === 2)) continue;
        var lit = night && r() < 0.6;
        var px = -4.8 + c * 3.2, py = 1.8 + fl * 4;
        B.box(px, py, 4.55, 2.4, 2.6, 0.3, WHITE);
        B.box(px, py + 0.25, 4.62, 1.9, 2.1, 0.3, lit ? '#ffd98a' : '#9fd3ff', lit ? { m: 'neon' } : null);
        B.box(px, py, -4.55, 2.4, 2.6, 0.3, WHITE);
      }
    }
    B.box(0, 0.6, 4.6, 3.6, 5.2, 0.3, '#6b4226');
    B.box(0, 5.8, 5.2, 4.6, 0.3, 1.6, shade(colour, -0.3));
    B.box(-3.8, 14.4, -1.5, 2.6, 1.4, 2.2, '#aab0b8');
  }

  function lighthouse(B, x, z, night) {
    B.at(x, 0, z, 0);
    B.add('cyl', 0, 0.6, 0, 7.4, 1.2, 7.4, '#9da2a9', { st: 1 });
    var segs = 5, y = 1.2;
    for (var i = 0; i < segs; i++) {
      var d = lerp(5.2, 3.8, i / segs), h = 3.1;
      B.add('cyl', 0, y + h / 2, 0, d, h, d, i % 2 ? WHITE : '#c4281c');
      y += h;
    }
    B.add('cyl', 0, y + 0.25, 0, 5.4, 0.5, 5.4, DARK);
    B.add('torus', 0, y + 1.2, 0, 5.0, 5.0, 5.0, DARK);
    B.add('cyl', 0, y + 1.6, 0, 2.8, 2.6, 2.8, night ? '#fff0a8' : '#cfeaff', { a: night ? 1 : 0.55, m: night ? 'neon' : 'glass' });
    B.add('cone', 0, y + 3.8, 0, 3.6, 2.2, 3.6, '#c4281c');
    B.add('sph', 0, y + 5.1, 0, 0.6, 0.6, 0.6, '#f2c230', { m: 'metal' });
    B.box(0, 1.2, 2.4, 1.8, 3.2, 0.4, '#6b4226');
    return y + 1.6;
  }

  function lemonadeStand(B, x, z, yaw) {
    B.at(x, 0, z, yaw);
    B.box(0, 0, 0, 5.6, 3.0, 2.6, WHITE);
    B.box(0, 0.4, 1.32, 5.2, 2.2, 0.1, '#f5cd30');
    B.box(0, 3.0, 0, 6.0, 0.35, 3.0, WOOD);
    var posts = [[-2.8, -1.3], [2.8, -1.3], [-2.8, 1.3], [2.8, 1.3]];
    for (var i = 0; i < posts.length; i++) B.box(posts[i][0], 3.3, posts[i][1], 0.3, 3.4, 0.3, WHITE);
    for (var s = 0; s < 6; s++) {
      B.add('box', -2.5 + s, 7.1, 0.2, 1.0, 0.3, 3.8, s % 2 ? WHITE : '#e23b3b', { r: [-0.32, 0, 0] });
    }
    B.box(0, 7.6, -1.4, 4.4, 1.4, 0.3, '#f5cd30');
    B.add('cyl', -1.4, 3.85, 0.4, 0.9, 1.4, 0.9, '#ffe066', { a: 0.85, m: 'glass' });
    B.add('cyl', 0.6, 3.75, 0.6, 0.5, 0.9, 0.5, '#ffe066');
    B.add('cyl', 1.5, 3.75, 0.6, 0.5, 0.9, 0.5, '#ffe066');
  }

  function swingFrame(B, x, z, yaw, len) {
    B.at(x, 0, z, yaw);
    var a = 0.32;
    B.add('cyl', -len / 2, 3.7, 1.2, 0.45, 7.8, 0.45, '#c4281c', { r: [a, 0, 0] });
    B.add('cyl', -len / 2, 3.7, -1.2, 0.45, 7.8, 0.45, '#c4281c', { r: [-a, 0, 0] });
    B.add('cyl', len / 2, 3.7, 1.2, 0.45, 7.8, 0.45, '#c4281c', { r: [a, 0, 0] });
    B.add('cyl', len / 2, 3.7, -1.2, 0.45, 7.8, 0.45, '#c4281c', { r: [-a, 0, 0] });
    B.add('cyl', 0, 7.4, 0, 0.5, len + 0.6, 0.5, '#f5cd30', { r: [0, 0, Math.PI / 2] });
  }
  function slide(B, x, z, yaw) {
    B.at(x, 0, z, yaw);
    // ladder at the back, a platform, then the chute running out to +z
    B.box(-1.1, 0, -3.2, 0.3, 6.2, 0.3, '#0d69ac');
    B.box(1.1, 0, -3.2, 0.3, 6.2, 0.3, '#0d69ac');
    for (var i = 0; i < 5; i++) B.box(0, 0.8 + i * 1.1, -3.2, 2.2, 0.2, 0.25, '#f2f3f3');
    B.box(0, 5.0, -2.2, 2.8, 0.4, 2.4, '#0d69ac', { st: 1 });
    B.box(-1.3, 0, -1.1, 0.3, 5.0, 0.3, '#0d69ac');
    B.box(1.3, 0, -1.1, 0.3, 5.0, 0.3, '#0d69ac');
    B.add('wedge', 0, 2.7, 2.2, 2.4, 4.6, 6.4, '#e23b3b');
    B.add('wedge', -1.3, 3.1, 2.2, 0.3, 4.6, 6.4, '#f5cd30');
    B.add('wedge', 1.3, 3.1, 2.2, 0.3, 4.6, 6.4, '#f5cd30');
  }
  function seesawBase(B, x, z, yaw) {
    B.at(x, 0, z, yaw);
    B.add('wedge', 0, 0.8, 0.0, 1.6, 1.6, 0.8, '#f5cd30', { r: [0, Math.PI / 2, 0] });
    B.add('wedge', 0, 0.8, 0.0, 1.6, 1.6, 0.8, '#f5cd30', { r: [0, -Math.PI / 2, 0] });
  }
  function trampoline(B, x, z) {
    B.at(x, 0, z, 0);
    for (var i = 0; i < 4; i++) {
      var a = i * Math.PI / 2 + Math.PI / 4;
      B.add('cyl', Math.sin(a) * 2.6, 0.6, Math.cos(a) * 2.6, 0.3, 1.2, 0.3, DARK);
    }
    B.add('torus', 0, 1.25, 0, 7.0, 7.0, 7.0, '#0d69ac');
    B.add('cyl', 0, 1.2, 0, 6.0, 0.12, 6.0, '#22252a');
  }
  function sandbox(B, x, z, S) {
    B.at(x, 0, z, 0.2);
    B.box(0, 0, 0, 6, 0.8, 6, WOOD);
    B.box(0, 0.5, 0, 5.2, 0.5, 5.2, S.snow ? '#eef4fb' : SAND, { st: 1 });
    B.add('cyl', 1.2, 1.4, 0.8, 1.0, 1.0, 1.0, '#e23b3b');
    B.box(-1.2, 1.0, -1.0, 2, 1, 2, '#f5cd30', { st: 1 });
  }
  /* a ring of stones round the fire, and logs to sit on at the given angles
     (measured round from the front), lying round it rather than pointing in */
  function campfire(B, x, z, logs) {
    B.at(x, 0, z, 0);
    for (var i = 0; i < 10; i++) {
      var a = i / 10 * TAU;
      B.add('sph', Math.sin(a) * 2.0, 0.35, Math.cos(a) * 2.0, 1.0, 0.7, 1.0, i % 2 ? '#8b8e93' : '#a0a3a8');
    }
    B.add('cyl', 0, 0.45, 0, 0.6, 3.4, 0.6, '#6b4226', { r: [0, 0.6, Math.PI / 2] });
    B.add('cyl', 0, 0.45, 0, 0.6, 3.4, 0.6, '#5b3a1e', { r: [0, -0.9, Math.PI / 2] });
    for (var s = 0; s < logs.length; s++) {
      var b = logs[s];
      B.add('cyl', Math.sin(b) * 5.3, 0.55, Math.cos(b) * 5.3, 1.1, 3.8, 1.1, '#7a4e2c', { r: [0, b, Math.PI / 2] });
    }
  }
  /* the square's fountain: a studded stone basin, a column, a bowl, a spout */
  function fountain(B, x, z) {
    B.at(x, 0, z, 0);
    B.add('cyl', 0, 0.95, 0, 9.4, 1.9, 9.4, '#c7ccd2', { st: 1 });
    B.add('cyl', 0, 1.93, 0, 8.2, 0.12, 8.2, WATER, { m: 'glass' });
    B.add('cyl', 0, 3.2, 0, 1.4, 2.6, 1.4, '#b9bec5');
    B.add('cyl', 0, 4.75, 0, 4.4, 0.7, 4.4, '#c7ccd2', { st: 1 });
    B.add('cyl', 0, 5.13, 0, 3.7, 0.12, 3.7, WATER, { m: 'glass' });
    B.add('cyl', 0, 5.9, 0, 0.8, 1.6, 0.8, '#b9bec5');
    B.add('sph', 0, 6.85, 0, 1.3, 0.9, 1.3, '#c7ccd2');
  }
  function flagPole(B, x, z) {
    B.at(x, 0, z, 0);
    B.add('cyl', 0, 0.3, 0, 1.4, 0.6, 1.4, '#a3a7ad');
    B.add('cyl', 0, 6.3, 0, 0.32, 12, 0.32, WHITE, { m: 'metal' });
    B.add('sph', 0, 12.4, 0, 0.6, 0.6, 0.6, '#f2c230', { m: 'metal' });
    B.box(2.5, 9.0, 0, 4.6, 2.8, 0.15, '#2b67f6');
    B.add('star', 2.5, 10.4, 0.0, 1.6, 1.6, 0.3, '#f5cd30');
  }
  function boombox(B, x, z, yaw) {
    B.at(x, 0, z, yaw);
    B.box(0, 0, 0, 3.4, 2.0, 1.4, '#2a2d33');
    B.add('cyl', -0.95, 1.0, 0.7, 1.1, 0.2, 1.1, '#8d939c', { r: [Math.PI / 2, 0, 0] });
    B.add('cyl', 0.95, 1.0, 0.7, 1.1, 0.2, 1.1, '#8d939c', { r: [Math.PI / 2, 0, 0] });
    B.box(0, 2.0, 0, 2.4, 0.3, 0.3, '#2a2d33');
    B.box(0, 1.6, 0.72, 0.8, 0.3, 0.1, '#7dff9a', { m: 'neon' });
  }
  function buildPlate(B, x, z, size) {
    B.at(x, 0.5, z, 0.0);
    B.box(0, 0, 0, size, 0.35, size, '#2b67f6', { st: 1 });
    var pile = [[-1.0, 1.0, '#c4281c'], [-0.4, 1.2, '#f5cd30'], [-1.1, 0.4, '#287f47']];
    for (var i = 0; i < pile.length; i++) B.box(pile[i][0], 0.35, pile[i][1], 1.2, 0.6, 0.6, pile[i][2], { st: 1, r: [0, i * 0.4, 0] });
  }
  function pond(B, x, z, rad, S) {
    B.at(x, 0, z, 0);
    B.add('cyl', 0, 0.12, 0, rad * 2 + 2.2, 0.24, rad * 2 + 2.2, S.snow ? '#e7eef6' : SAND, { st: 1 });
    B.add('cyl', 0, 0.2, 0, rad * 2, 0.3, rad * 2, S.snow ? '#bfe0f6' : WATER, { m: 'glass' });
    if (!S.snow) {
      B.add('cyl', -rad * 0.4, 0.38, rad * 0.35, 1.6, 0.06, 1.6, '#4f9e45');
      B.add('cyl', rad * 0.2, 0.38, -rad * 0.5, 1.3, 0.06, 1.3, '#4f9e45');
      for (var i = 0; i < 5; i++) {
        var a = 2.4 + i * 0.25;
        B.add('cyl', Math.sin(a) * (rad + 0.4), 1.1, Math.cos(a) * (rad + 0.4), 0.18, 2.2, 0.18, '#6c8f3a');
      }
    }
  }
  function dock(B, x, z, yaw, len) {
    B.at(x, 0, z, yaw);
    for (var i = 0; i < Math.round(len / 1.2); i++) B.box(0, 0.45, 0.6 + i * 1.2, 3.2, 0.3, 1.0, i % 2 ? WOOD : shade(WOOD, -0.08));
    B.box(-1.5, 0, len, 0.4, 1.2, 0.4, '#6b4226');
    B.box(1.5, 0, len, 0.4, 1.2, 0.4, '#6b4226');
  }
  function mailbox(B, x, z, yaw) {
    B.at(x, 0, z, yaw);
    B.box(0, 0, 0, 0.3, 2.4, 0.3, WOOD);
    B.box(0, 2.4, 0, 0.9, 0.9, 1.6, '#2b67f6');
    B.box(0.5, 2.6, -0.4, 0.1, 0.9, 0.3, '#e23b3b');
  }
  function snowman(B, x, z, yaw) {
    B.at(x, 0, z, yaw);
    B.add('sph', 0, 1.5, 0, 3.2, 3.0, 3.2, '#ffffff');
    B.add('sph', 0, 3.8, 0, 2.3, 2.2, 2.3, '#ffffff');
    B.add('sph', 0, 5.5, 0, 1.7, 1.6, 1.7, '#ffffff');
    B.add('cone', 0, 5.5, 1.1, 0.35, 1.1, 0.35, '#ff8a1e', { r: [Math.PI / 2, 0, 0] });
    B.add('sph', -0.35, 5.8, 0.75, 0.22, 0.22, 0.22, DARK);
    B.add('sph', 0.35, 5.8, 0.75, 0.22, 0.22, 0.22, DARK);
    B.add('cyl', 0, 6.6, 0, 1.4, 0.2, 1.4, DARK);
    B.add('cyl', 0, 7.2, 0, 1.0, 1.2, 1.0, DARK);
    B.add('torus', 0, 4.75, 0, 1.9, 1.9, 1.9, '#e23b3b');
  }
  function pumpkin(B, x, z, r) {
    B.at(x, 0, z, r() * TAU, 0.8 + r() * 0.5);
    B.add('sph', 0, 0.7, 0, 1.8, 1.4, 1.8, '#f08a24');
    B.add('cyl', 0, 1.6, 0, 0.25, 0.6, 0.25, '#4e7a2c');
  }
  function crane(B, x, z, yaw, k) {
    B.at(x, 0, z, yaw, k);
    var Y = '#f5cd30';
    B.box(0, 0, 0, 3.4, 0.8, 3.4, '#a3a7ad', { st: 1 });
    for (var i = 0; i < 4; i++) {
      var cx = i % 2 ? 0.9 : -0.9, cz = i < 2 ? 0.9 : -0.9;
      B.box(cx, 0.8, cz, 0.3, 17, 0.3, Y);
    }
    for (var h = 1; h < 17; h += 2.4) {
      B.box(0, 0.8 + h, 0.9, 2.1, 0.25, 0.25, Y);
      B.box(0, 0.8 + h, -0.9, 2.1, 0.25, 0.25, Y);
      B.box(0.9, 0.8 + h, 0, 0.25, 0.25, 2.1, Y);
      B.box(-0.9, 0.8 + h, 0, 0.25, 0.25, 2.1, Y);
    }
    B.box(0, 17.8, 0, 2.6, 2.2, 2.6, '#2b2f36');
    B.box(-6.5, 20.0, 0, 18, 0.9, 1.2, Y);
    B.box(4.2, 18.5, 0, 3.2, 1.6, 2.0, '#6b6f78');
    B.box(-14.6, 18.0, 0, 0.12, 2.0, 0.12, DARK);
    B.box(-14.6, 17.6, 0, 0.9, 0.5, 0.9, '#c4281c');
  }
  function signpost(B, x, z, yaw, k) {
    B.at(x, 0, z, yaw, k);
    B.box(-1.9, 0, 0, 0.4, 4.6, 0.4, WOOD);
    B.box(1.9, 0, 0, 0.4, 4.6, 0.4, WOOD);
    B.box(0, 3.0, 0, 5.4, 2.2, 0.35, '#f2e7cc');
    B.box(0, 3.0, -0.05, 5.8, 2.6, 0.3, WOOD);
  }

  /* a stone planter on the square, flowers round whatever stands in it */
  function planter(B, x, z, S, r) {
    B.at(x, 0, z, 0);
    B.box(0, 0, 0, 1.7, 1.0, 1.7, '#9da2a9', { st: 1 });
    B.box(0, 1.0, 0, 1.42, 0.1, 1.42, '#5b3a29');
    for (var i = 0; i < 5; i++) {
      var a = i / 5 * TAU + r(), d = 0.42 + r() * 0.12;
      B.add('sph', Math.sin(a) * d, 1.32, Math.cos(a) * d, 0.5, 0.42, 0.5, pick(r, S.flowers));
    }
  }
  /* where a street ends: a striped barrier */
  function barrier(B, x, z, yaw, len) {
    B.at(x, 0, z, yaw);
    B.box(-len / 2 + 0.3, 0, 0, 0.4, 2.0, 0.4, WHITE);
    B.box(len / 2 - 0.3, 0, 0, 0.4, 2.0, 0.4, WHITE);
    for (var i = 0; i < 6; i++) B.box(-len / 2 + (i + 0.5) * len / 6, 1.1, 0, len / 6, 0.7, 0.25, i % 2 ? WHITE : '#e23b3b');
  }
  /* a car: one going round the square, or one parked (2.7 wide, 5.2 long) */
  function carModel(B, x, z, yaw, colour, lit) {
    B.at(x, 0, z, yaw);
    B.box(0, 0.7, 0, 2.7, 1.25, 5.2, colour);
    B.box(0, 1.95, -0.3, 2.4, 1.1, 2.8, '#bfe3ff', { m: 'metal' });
    B.box(0, 3.05, -0.3, 2.5, 0.2, 2.9, colour);
    var wheels = [[-1.4, 1.65], [1.4, 1.65], [-1.4, -1.65], [1.4, -1.65]];
    for (var i = 0; i < wheels.length; i++) B.add('cyl', wheels[i][0], 0.6, wheels[i][1], 1.2, 0.55, 1.2, '#1f2226', { r: [0, 0, Math.PI / 2] });
    var glow = lit ? { m: 'neon' } : null;
    B.box(-0.85, 0.95, 2.62, 0.55, 0.4, 0.1, '#fff6d0', glow);
    B.box(0.85, 0.95, 2.62, 0.55, 0.4, 0.1, '#fff6d0', glow);
    B.box(-0.85, 0.95, -2.62, 0.55, 0.4, 0.1, '#ff4d4d', glow);
    B.box(0.85, 0.95, -2.62, 0.55, 0.4, 0.1, '#ff4d4d', glow);
  }
  /* a dance floor of bright studded tiles */
  function danceFloor(B, x, z, w, d) {
    B.at(x, 0, z, 0);
    var cols = ['#ff5ad1', '#3cc8ff', '#7dff9a', '#ffd36a'], nx = Math.round(w / 2.25), nz = Math.round(d / 2.5);
    for (var i = 0; i < nx; i++) {
      for (var j = 0; j < nz; j++) {
        B.box(-w / 2 + (i + 0.5) * w / nx, 0, -d / 2 + (j + 0.5) * d / nz, w / nx - 0.08, 0.22, d / nz - 0.08, cols[(i + j) % 4], { st: 1 });
      }
    }
  }

  /* ======================================================== the world */
  function World(host, mode) {
    var cfg = MODES[mode] || MODES.hero;
    this.host = host;
    this.mode = mode;
    this.cfg = cfg;
    this.R = cfg.R;
    var seed = parseInt(query['haven-seed'] || host.getAttribute('data-seed') || '', 10);
    if (!(seed >= 0)) seed = (Math.random() * 4294967295) >>> 0;
    if (mode === 'build') {
      try {
        seed = parseInt(sessionStorage.getItem('haven.build') || '', 10) || seed;
        sessionStorage.setItem('haven.build', String(seed));
      } catch (e) { /* private mode */ }
    }
    this.seed = seed;
    this.rand = mulberry(seed);
    var month = new Date().getMonth();
    this.seasonName = SEASONS[query['haven-season']] ? query['haven-season']
      : (host.getAttribute('data-season') || SEASON_OF_MONTH[month]);
    this.S = SEASONS[this.seasonName] || SEASONS.summer;
    this.light = LIGHTS[query['haven-light']] ? query['haven-light'] : (host.getAttribute('data-light') || cfg.light);
    if (!LIGHTS[this.light]) this.light = cfg.light;
    this.lightFrom = this.light;
    this.lightMix = 1;
    this.night = LIGHTS[this.light].night;
    this.t = 0;
    this.stage = mode === 'build' ? 0 : 99;
    this.stageAt = {};
    this.name = '';
    this.domeK = mode === 'build' ? 0 : 1;
    this.kids = [];
    this.spots = [];
    this.nodes = [];
    this.links = [];
    this.obst = [];
    this.cross = [];
    this.edgeCross = {};
    this.flowers = [];
    this.ripples = [];
    this.threats = [];
    this.notes = [];
    this.hearts = [];
    this.balloons = [];
    this.lanterns = [];
    this.bubbles = [];
    this.party = 0;
    this.storm = null;
    this.rainbow = 0;
    this.badgeHit = 0;
    this.nextThreat = 2.4;
    this.nextEvent = 9 + this.rand() * 6;
    this.lastEvent = '';
    this.visible = true;
    this.slow = 0;
    this.frameMs = [];
    this.drag = 0;
    this.dragVel = 0;
    this.camYaw = cfg.az;
    this.mir = 1;
    this.build();
  }
  var WP = World.prototype;

  WP.build = function () {
    var host = this.host;
    if (!global.Renderer || !global.Avatar || !global.GLX || !global.Geometry) return;
    var canvas = document.createElement('canvas');
    canvas.className = 'haven-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    var overlay = document.createElement('canvas');
    overlay.className = 'haven-overlay';
    overlay.setAttribute('aria-hidden', 'true');
    host.appendChild(canvas);
    host.appendChild(overlay);
    var renderer;
    try {
      renderer = new Renderer(canvas, { antialias: true });
    } catch (e) { renderer = null; }
    if (!renderer || renderer.failed) {
      host.removeChild(canvas);
      host.removeChild(overlay);
      return;
    }
    this.canvas = canvas;
    this.overlay = overlay;
    this.ctx = overlay.getContext('2d');
    this.renderer = renderer;
    renderer.near = 1;
    renderer.far = 1400;
    this.particles = global.Particles ? new Particles(renderer.gl) : null;
    this.font = (global.getComputedStyle ? getComputedStyle(host).fontFamily : '') || 'Verdana, sans-serif';
    this.generate();
    this.applyLight(1);
    host.haven = this;
    host.classList.add('haven-live');
    this.bind();
    this.loop = this.loop.bind(this);
    this.last = 0;
    if (reduced) {
      this.warm(6);
      this.frame(0);
    } else {
      this.warm(1.5);
      this.raf = requestAnimationFrame(this.loop);
    }
  };

  /* ---------------------------------------------------------- the layout */
  WP.generate = function () {
    var r = this.rand;
    this.mir = (this.mode === 'build' || this.mode === 'mini') ? 1 : (r() < 0.5 ? 1 : -1);
    this.look = {
      wall: pick(r, WALLS), roof: pick(r, ROOFS), back: pick(r, ['tower', 'apartment', 'lighthouse']),
      apartment: pick(r, ['#c4281c', '#2b5fa8', '#e8a83a', '#d6dbe0', '#6b327c']), car: pick(r, CARS)
    };
    if (this.mode === 'build') this.layoutBuild();
    else if (this.mode === 'mini') this.layoutMini();
    else this.layoutTown();
    this.rebuildStatic();
    if (this.cfg.kids) this.spawnKids(this.cfg.kids);
  };

  /* A spot is somewhere a kid goes to do something.  Spots are written for
     the unmirrored island and mirrored here, with the way they face, the
     points a kid walks in by (via) and, for the slide, out by (exit). */
  WP.spot = function (kind, x, z, yaw, extra) {
    var mir = this.mir;
    var s = { kind: kind, x: x * mir, z: z, yaw: mir < 0 ? -yaw : yaw, user: null, y: 0, node: -1 };
    if (extra) for (var k in extra) s[k] = extra[k];
    if (s.ax !== undefined) s.ax *= mir;
    function pts(list) { return list.map(function (p) { return { x: p[0] * mir, z: p[1] }; }); }
    if (s.via) s.via = pts(s.via);
    if (s.exit) s.exit = pts(s.exit);
    if (s.off) s.off = { x: s.off[0] * mir, z: s.off[1] };
    this.spots.push(s);
    return s;
  };
  WP.join = function (a, b) {
    if (a === b || a < 0 || b < 0) return;
    if (this.nodes[a].n.indexOf(b) < 0) this.nodes[a].n.push(b);
    if (this.nodes[b].n.indexOf(a) < 0) this.nodes[b].n.push(a);
  };

  /* ======================================================== the town plan
     A square with the fountain in the middle and a road on every side of it:
     two long streets, left and right, that run out to the edges, and two
     short ones that close the square in front and behind.  So nothing drives
     or walks through the fountain -- the cars go round the square and the
     kids round its sidewalks, which run along both sides of every street and
     meet at zebra crossings.  Round about: the house, the lemonade stand,
     the pond and a brick plate on the left; the playground, a sandbox and a
     dance floor on the right; the campfire in front; the tall building
     behind.  Written for the unmirrored island, mirrored as it's placed. */
  var TOWN = { D: 13.8, road: 3.5, walk: 2.8, lane: 1.55, keep: 0.8 };
  var RIDES = { slide: 1, swing: 1, seesaw: 1, tramp: 1 };

  WP.layoutTown = function () {
    var R = this.R, D = TOWN.D, w = TOWN.road, sw = TOWN.walk, self = this, i;
    var c = D - w - sw / 2, o = D + w + sw / 2, inner = D - w - sw, outer = D + w + sw;
    var zEnd = Math.sqrt(Math.pow(R - 1.2, 2) - outer * outer), zE = zEnd - 2.3;
    this.town = { D: D, c: c, o: o, inner: inner, outer: outer, zEnd: zEnd };
    this.nodeIndex = {};
    this.cross = [];
    this.edgeCross = {};

    // the sidewalks, as chains of nodes a few studs apart
    function chain(pts) {
      var prev = -1;
      for (var a = 0; a < pts.length; a++) {
        if (a > 0) {
          var q = pts[a - 1], p = pts[a], n = Math.max(1, Math.ceil(dist2(q[0], q[1], p[0], p[1]) / 4.6));
          for (var b = 1; b < n; b++) {
            var mid = self.nodeAt(lerp(q[0], p[0], b / n), lerp(q[1], p[1], b / n));
            self.join(prev, mid);
            prev = mid;
          }
        }
        var id = self.nodeAt(pts[a][0], pts[a][1]);
        self.join(prev, id);
        prev = id;
      }
    }
    chain([[c, c], [c, 0], [c, -c], [0, -c], [-c, -c], [-c, 0], [-c, c], [0, c], [c, c]]);
    chain([[o, -zE], [o, -o], [o, -c], [o, 0], [o, c], [o, o], [o, zE]]);
    chain([[-o, -zE], [-o, -o], [-o, -c], [-o, 0], [-o, c], [-o, o], [-o, zE]]);
    chain([[-c, zE], [-c, o], [0, o], [c, o], [c, zE]]);
    chain([[-c, -zE], [-c, -o], [0, -o], [c, -o], [c, -zE]]);
    // zebra crossings join them: beside every junction, and halfway along
    var X = [[c, c, o, c], [c, -c, o, -c], [-c, c, -o, c], [-c, -c, -o, -c],
             [c, o, o, o], [c, -o, o, -o], [-c, o, -o, o], [-c, -o, -o, -o],
             [c, c, c, o], [-c, c, -c, o], [c, -c, c, -o], [-c, -c, -c, -o],
             [c, 0, o, 0], [-c, 0, -o, 0], [0, c, 0, o], [0, -c, 0, -o]];
    for (i = 0; i < X.length; i++) this.crossing(X[i][0], X[i][1], X[i][2], X[i][3]);

    this.planTown();
    this.linkSpots();
    this.plantTown();
    // the two cars' loops round the square: the inner lanes, the outer lanes
    this.loops = [this.loopPath(D - TOWN.lane, 2.4, false), this.loopPath(D + TOWN.lane, 6.0, true)];
    this.lapCrossings();
  };

  /* a sidewalk node (one per place), and which side of the streets it's on */
  WP.nodeAt = function (ux, z) {
    var key = Math.round(ux * 10) + ',' + Math.round(z * 10);
    if (this.nodeIndex[key] !== undefined) return this.nodeIndex[key];
    var T = this.town, e = 0.05, block;
    if (Math.abs(ux) <= T.c + e && Math.abs(z) <= T.c + e) block = 'square';
    else if (Math.abs(ux) <= T.c + e) block = z > 0 ? 'front' : 'back';
    else block = ux > 0 ? 'right' : 'left';
    this.nodes.push({ x: ux * this.mir, z: z, ux: ux, n: [], block: block });
    this.nodeIndex[key] = this.nodes.length - 1;
    return this.nodes.length - 1;
  };
  /* a zebra: an edge between the sidewalks either side of a road */
  WP.crossing = function (x1, z1, x2, z2) {
    var a = this.nodeAt(x1, z1), b = this.nodeAt(x2, z2), alongX = Math.abs(x2 - x1) > Math.abs(z2 - z1);
    this.join(a, b);
    var ux = (x1 + x2) / 2, z = (z1 + z2) / 2;
    var cr = { a: a, b: b, ux: ux, z: z, x: ux * this.mir, alongX: alongX,
               hx: alongX ? TOWN.road : 1.3, hz: alongX ? 1.3 : TOWN.road, laps: [] };
    this.cross.push(cr);
    this.edgeCross[a + '-' + b] = cr;
    this.edgeCross[b + '-' + a] = cr;
  };
  /* which part of the town a point is in -- its sidewalk included -- or
     'street' when it's out on a road */
  WP.blockOf = function (x, z) {
    var T = this.town, ux = x * this.mir, e = 0.3, near = T ? T.D - TOWN.road + e : 0, far = T ? T.D + TOWN.road - e : 0;
    if (!T) return 'street';
    if (Math.abs(ux) <= near && Math.abs(z) <= near) return 'square';
    if (Math.abs(ux) <= near && z >= far) return 'front';
    if (Math.abs(ux) <= near && z <= -far) return 'back';
    if (ux >= far) return 'right';
    if (ux <= -far) return 'left';
    return 'street';
  };

  /* -------------------------------------------- things nobody walks into
     Circles {r} and turned rectangles {hx, hz, yaw}, in the mirrored world.
     A spot's own (the bench it sits on, the swing it rides) lets through
     whoever is coming to that spot. */
  WP.rectOf = function (ux, z, hx, hz, yaw) {
    var y = (yaw || 0) * this.mir;
    return { k: 'r', x: ux * this.mir, z: z, hx: hx, hz: hz, yaw: y, cs: Math.cos(y), sn: Math.sin(y) };
  };
  WP.obRect = function (ux, z, hx, hz, yaw, tag) {
    var o = this.rectOf(ux, z, hx, hz, yaw);
    o.tag = tag;
    this.obst.push(o);
    return o;
  };
  WP.obCircle = function (ux, z, r, tag) {
    var o = { k: 'c', x: ux * this.mir, z: z, r: r, tag: tag };
    this.obst.push(o);
    return o;
  };
  function inRect(o, x, z, pad) {
    var dx = x - o.x, dz = z - o.z, lx = dx * o.cs - dz * o.sn, lz = dx * o.sn + dz * o.cs;
    return Math.abs(lx) < o.hx + pad && Math.abs(lz) < o.hz + pad;
  }
  function obInside(o, x, z, pad) {
    if (o.hole && inRect(o.hole, x, z, 0)) return false;
    if (o.k === 'c') return dist2(x, z, o.x, o.z) < o.r + pad;
    return inRect(o, x, z, pad);
  }
  /* the nearest place outside o (grown by pad), or null when already out */
  function obPush(o, x, z, pad) {
    if (o.hole && inRect(o.hole, x, z, 0)) return null;
    if (o.k === 'c') {
      var d = dist2(x, z, o.x, o.z), need = o.r + pad;
      if (d >= need) return null;
      if (d < 1e-4) return [o.x + need, o.z];
      return [o.x + (x - o.x) / d * need, o.z + (z - o.z) / d * need];
    }
    var dx = x - o.x, dz = z - o.z, lx = dx * o.cs - dz * o.sn, lz = dx * o.sn + dz * o.cs;
    var px = o.hx + pad - Math.abs(lx), pz = o.hz + pad - Math.abs(lz);
    if (px <= 0 || pz <= 0) return null;
    if (px < pz) lx = (lx < 0 ? -1 : 1) * (o.hx + pad);
    else lz = (lz < 0 ? -1 : 1) * (o.hz + pad);
    return [o.x + lx * o.cs + lz * o.sn, o.z - lx * o.sn + lz * o.cs];
  }
  function segDist(px, pz, ax, az, bx, bz) {
    var dx = bx - ax, dz = bz - az, l2 = dx * dx + dz * dz;
    var t = l2 > 0 ? clamp(((px - ax) * dx + (pz - az) * dz) / l2, 0, 1) : 0;
    return dist2(px, pz, ax + dx * t, az + dz * t);
  }
  WP.lineClear = function (ax, az, bx, bz, pad, own) {
    var n = Math.max(1, Math.ceil(dist2(ax, az, bx, bz) / 0.4));
    for (var i = 0; i <= n; i++) {
      var x = lerp(ax, bx, i / n), z = lerp(az, bz, i / n);
      for (var j = 0; j < this.obst.length; j++) {
        var o = this.obst[j];
        if (own && own.indexOf(o) >= 0) continue;
        if (obInside(o, x, z, pad)) return false;
      }
    }
    return true;
  };

  /* --------------------------------------------------------- what goes where */
  WP.planTown = function () {
    var R = this.R, look = this.look, T = this.town, i;
    var P = this.place = {
      house: [-27.1, -13.4], back: [0, -29.4], fire: [0, 29.0], pond: [-27.1, 12.0], ducks: [-28.9, 12.0],
      stand: [-25.3, -0.4], plate: [-25.3, 25.0], swings: [27.5, -6.2], seesaw: [26.1, 1.8], slide: [32.7, 6.4],
      tramp: [24.9, 8.0], sandbox: [24.7, 18.8], floor: [26.3, -19.6], boombox: [26.3, -16.3]
    };
    this.houseYaw = Math.PI / 2;
    var lane = -0.65;    // the way across the playground, between the swings and the seesaw

    // ---- the square: the fountain, planters at its corners, a bench either side
    this.obCircle(0, 0, 4.8, 'fountain');
    this.planters = [[5.8, 5.8, 'lamp'], [-5.8, 5.8, 'lamp'], [5.8, -5.8, 'tree'], [-5.8, -5.8, 'flag']];
    for (i = 0; i < 4; i++) this.obRect(this.planters[i][0], this.planters[i][1], 0.8, 0.8, 0, 'planter');
    // benches: one before the tall building, one watching the playground
    this.benches = [[4.0, -22.6, 0], [28.0, 23.6, Math.PI]];
    var bo = [this.obRect(4.0, -22.6, 2.25, 0.75, 0, 'bench'), this.obRect(28.0, 23.6, 2.25, 0.75, 0, 'bench')];
    this.spot('bench', 26.85, 23.5, Math.PI, { own: [bo[1]] });
    this.spot('bench', 29.15, 23.5, Math.PI, { own: [bo[1]] });
    this.spot('wish', -2.3, 5.75, 0, {});
    this.spot('wish', 2.3, 5.75, 0, {});
    this.spot('wish', 0, -6.0, 0, {});
    // where everybody dances at a party: round the fountain, clear of the benches
    this.partySlots = [];
    var angles = [0, 36, -36, 72, -72, 108, -108, 144, -144, 180];
    for (i = 0; i < angles.length; i++) {
      var pa = angles[i] * Math.PI / 180;
      this.partySlots.push({ x: Math.sin(pa) * 6.3 * this.mir, z: Math.cos(pa) * 6.3, node: -1, party: true });
    }

    // ---- in front: the campfire and its logs, two kids playing catch
    var F = P.fire;
    this.obCircle(F[0], F[1], 2.7, 'fire');
    this.logs = [0, Math.PI * 2 / 3, -Math.PI * 2 / 3];
    for (i = 0; i < 3; i++) {
      var la = this.logs[i], lx = F[0] + Math.sin(la) * 5.3, lz = F[1] + Math.cos(la) * 5.3;
      var lo = this.obRect(lx, lz, 2.0, 0.65, la, 'log');
      this.spot('fire', lx, lz, la + Math.PI, { fire: F, own: [lo] });
    }
    var cA = this.spot('catch', -3.4, 21.6, Math.PI / 2, {});
    var cB = this.spot('catch', 3.4, 21.6, -Math.PI / 2, {});
    cA.pair = cB; cB.pair = cA;

    // ---- behind: the tall building with a path to its door, a bench
    var Bk = P.back;
    if (look.back === 'tower') this.obRect(Bk[0], Bk[1], 5.4, 5.4, 0, 'building');
    else if (look.back === 'apartment') this.obRect(Bk[0], Bk[1] - 0.2, 7.0, 5.0, 0, 'building');
    else this.obCircle(Bk[0], Bk[1] - 0.4, 3.9, 'building');
    this.spot('bench', 2.85, -22.5, 0, { own: [bo[0]] });
    this.spot('bench', 5.15, -22.5, 0, { own: [bo[0]] });
    this.spot('wave', -4.6, -21.4, 0, {});

    // ---- on the left: the house, the lemonade stand, the pond and its dock,
    // the brick plate and a kite
    var H = P.house;
    this.obRect(H[0], H[1], 5.7, 6.3, 0, 'house');
    this.obCircle(-21.6, -5.4, 0.5, 'mailbox');
    var St = P.stand;
    this.obRect(St[0], St[1], 1.45, 3.1, 0, 'stand');
    this.spot('lemon', -22.2, St[1], -Math.PI / 2, { stand: St });
    var Pd = P.pond, pondOb = this.obCircle(Pd[0], Pd[1], 5.6, 'pond');
    pondOb.hole = this.rectOf(-22.75, Pd[1], 2.1, 1.6, 0);
    this.spot('fish', -23.8, Pd[1] - 1.1, -Math.PI / 2, { bob: [-28.9, Pd[1] - 1.7] });
    this.spot('fish', -23.8, Pd[1] + 1.1, -Math.PI / 2, { bob: [-29.1, Pd[1] + 1.7] });
    var pr = Math.sqrt(Pd[0] * Pd[0] + Pd[1] * Pd[1]), ux = Pd[0] / pr, uz = Pd[1] / pr;
    var s0 = pr + 4.4, s1 = R + 0.6, sm = (s0 + s1) / 2;
    this.stream = { ux: ux, uz: uz, s0: s0, s1: s1 };
    this.obRect(ux * sm, uz * sm, 2.0, (s1 - s0) / 2 + 0.4, Math.atan2(ux, uz), 'stream');
    var Pl = P.plate, plateOb = this.obRect(Pl[0], Pl[1], 1.9, 1.9, 0, 'plate');
    this.spot('build', Pl[0] + 2.2, Pl[1] - 2.2, 0, { plate: Pl, own: [plateOb] });
    this.spot('build', Pl[0] - 2.2, Pl[1] - 2.2, 0, { plate: Pl, own: [plateOb], via: [[-21.3, 21.2], [Pl[0] - 2.2, 21.2]] });
    this.spot('kite', -21.4, 29.8, 2.1, {});

    // ---- on the right: the playground, the sandbox, the dance floor
    var Sw = P.swings;
    for (i = 0; i < 4; i++) this.obCircle(Sw[0] + (i < 2 ? -5.2 : 5.2), Sw[1] + (i % 2 ? 2.45 : -2.45), 0.45, 'swing');
    var swZone = this.obRect(Sw[0], Sw[1], 4.4, 3.8, 0, 'swings');
    for (i = 0; i < 3; i++) {
      var sx = Sw[0] - 3 + i * 3;
      this.spot('swing', sx, Sw[1], 0, { pivot: 7.4, seat: 1.7, phase: i * 1.7, own: [swZone], via: [[21.1, lane], [sx, lane]] });
    }
    var Ss = P.seesaw, plank = this.obRect(Ss[0], Ss[1], 4.7, 0.7, 0, 'seesaw');
    this.spot('seesaw', Ss[0] - 4, Ss[1], Math.PI / 2, { end: -1, cx: Ss[0], len: 8, own: [plank] });
    this.spot('seesaw', Ss[0] + 4, Ss[1], -Math.PI / 2, { end: 1, cx: Ss[0], len: 8, own: [plank], via: [[21.1, lane], [Ss[0] + 4, lane]] });
    var Sl = P.slide, slideOb = this.obRect(Sl[0], Sl[1] + 1.0, 1.5, 4.8, 0, 'slide');
    this.spot('slide', Sl[0], Sl[1] - 4.1, 0, { prop: Sl, own: [slideOb], via: [[21.1, lane], [Sl[0], lane]],
                                               exit: [[Sl[0] - 1.8, Sl[1] + 7.4], [20.9, Sl[1] + 7.4]],
                                               off: [Sl[0], Sl[1] + 6.6] });
    var Tp = P.tramp, trampOb = this.obCircle(Tp[0], Tp[1], 3.7, 'tramp');
    this.spot('tramp', Tp[0], Tp[1], 0, { own: [trampOb] });
    var Sb = P.sandbox, sandOb = this.obRect(Sb[0], Sb[1], 2.5, 2.5, 0.2, 'sandbox');
    this.spot('sand', Sb[0], Sb[1] - 0.3, 0, { own: [sandOb] });
    var Bx = P.boombox;
    this.obRect(Bx[0], Bx[1], 1.9, 0.9, 0, 'boombox');
    this.spot('dance', 23.5, -20.0, 0, {});
    this.spot('dance', 26.3, -20.8, 0, { via: [[21.9, -23.2], [26.3, -23.2]] });
    this.spot('dance', 29.1, -20.0, 0, { via: [[21.9, -23.2], [29.1, -23.2]] });
    this.spot('wave', 22.0, 28.4, 0, {});

    // ---- the streets' ends, two parked cars, street lamps
    var D = T.D, zEnd = T.zEnd, a, b;
    for (a = -1; a <= 1; a += 2) for (b = -1; b <= 1; b += 2) this.obRect(a * D, b * (zEnd - 0.4), 2.9, 0.45, 0, 'barrier');
    this.parked = [[D + TOWN.lane + 0.05, 25.0, 0], [-D - TOWN.lane - 0.05, -25.5, Math.PI]];
    for (i = 0; i < this.parked.length; i++) this.obRect(this.parked[i][0], this.parked[i][1], 1.35, 2.6, 0, 'car');
    this.lampSpots = [[21.1, -12.8], [21.1, 16.8], [-21.1, 3.6], [-21.1, -23.6], [-21.1, 17.6], [7.0, 35.6], [-7.0, 35.6], [6.4, -25.6]];
    for (i = 0; i < this.lampSpots.length; i++) this.obCircle(this.lampSpots[i][0], this.lampSpots[i][1], 0.55, 'lamp');

    // every spot faces what it's for
    var m = this.mir;
    for (i = 0; i < this.spots.length; i++) {
      var sp = this.spots[i];
      if (sp.kind === 'fire') sp.yaw = Math.atan2(sp.fire[0] * m - sp.x, sp.fire[1] - sp.z);
      if (sp.kind === 'dance') sp.yaw = Math.atan2(Bx[0] * m - sp.x, Bx[1] - sp.z);
      if (sp.kind === 'build') sp.yaw = Math.atan2(sp.plate[0] * m - sp.x, sp.plate[1] - sp.z);
      if (sp.kind === 'wish') sp.yaw = Math.atan2(-sp.x, -sp.z);
    }
  };

  /* Each spot's way in: the nearest sidewalk node on its own side of the
     streets with a clear line to it (or to the first point of its way in). */
  WP.linkSpots = function () {
    var i, list = this.spots.concat(this.partySlots || []);
    for (i = 0; i < list.length; i++) {
      var s = list[i], first = s.via && s.via.length ? s.via[0] : s;
      s.node = this.accessNode(first.x, first.z, s.via && s.via.length ? null : (s.own || null));
      if (s.exit) s.exitNode = this.accessNode(s.exit[s.exit.length - 1].x, s.exit[s.exit.length - 1].z, null);
    }
  };
  /* the nearest node a point can walk to in a straight line, on its own side */
  WP.accessNode = function (x, z, own) {
    var block = this.blockOf(x, z), best = -1, bd = 1e9, near = -1, nd = 1e9;
    for (var j = 0; j < this.nodes.length; j++) {
      var n = this.nodes[j], d = dist2(n.x, n.z, x, z);
      if (d < nd) { nd = d; near = j; }
      if (d >= bd || (block !== 'street' && n.block !== block)) continue;
      if (!this.lineClear(n.x, n.z, x, z, 0.85, own)) continue;
      best = j; bd = d;
    }
    this.accessClear = best >= 0;
    return best >= 0 ? best : near;
  };
  /* back out of a spot the way in, from wherever along it the kid now is
     (called away to a party halfway to the swings, say) */
  WP.wayOut = function (k, s) {
    var line = [{ x: s.x, z: s.z }].concat((s.via || []).slice().reverse()), best = 0, bd = dist2(k.x, k.z, s.x, s.z);
    for (var i = 0; i < line.length - 1; i++) {
      var d = segDist(k.x, k.z, line[i].x, line[i].z, line[i + 1].x, line[i + 1].z);
      if (d < bd) { bd = d; best = i; }
    }
    if (bd > 2.5) return null;
    var pts = [];
    for (var j = best + 1; j < line.length; j++) pts.push({ x: line[j].x, z: line[j].z, out: true });
    return pts;
  };
  /* When no straight line will do -- a kid shoved into the corner behind
     the swings -- a way round things over one-stud squares, kept off the
     roads and the island's edge, then pulled straight wherever the line is
     clear.  Returns the corners to walk through (not the goal itself). */
  WP.gridWay = function (x, z, tx, tz, own) {
    var H = Math.ceil(this.R), N = H * 2 + 1, self = this, i, j;
    if (!this.grid) {
      var lim = (this.R - 1.6) * (this.R - 1.6);
      this.grid = [];
      for (i = 0; i < N * N; i++) {
        var cx = (i % N) - H, cz = Math.floor(i / N) - H, cell = null;
        if (cx * cx + cz * cz > lim || this.onRoad(cx, cz, 0.2)) cell = 'x';
        else for (j = 0; j < this.obst.length; j++) if (obInside(this.obst[j], cx, cz, 0.7)) (cell = cell || []).push(this.obst[j]);
        this.grid.push(cell);
      }
    }
    function free(c) {
      var g = self.grid[c];
      if (!g) return true;
      if (g === 'x' || !own) return false;
      for (var q = 0; q < g.length; q++) if (own.indexOf(g[q]) < 0) return false;
      return true;
    }
    function cellOf(px, pz) { return clamp(Math.round(pz) + H, 0, N - 1) * N + clamp(Math.round(px) + H, 0, N - 1); }
    var start = cellOf(x, z), goal = cellOf(tx, tz), prev = new Int32Array(N * N).fill(-2), queue = [start], head = 0;
    prev[start] = -1;
    while (head < queue.length && prev[goal] === -2) {
      var c = queue[head++], ccx = c % N, ccz = (c - ccx) / N;
      for (var dz = -1; dz <= 1; dz++) for (var dx = -1; dx <= 1; dx++) {
        var nx = ccx + dx, nz = ccz + dz, nc = nz * N + nx;
        if ((!dx && !dz) || nx < 0 || nz < 0 || nx >= N || nz >= N || prev[nc] !== -2) continue;
        if (nc !== goal && !free(nc)) continue;
        if (dx && dz && (!free(ccz * N + nx) || !free(nz * N + ccx))) continue;    // no cutting corners
        prev[nc] = c;
        queue.push(nc);
      }
    }
    if (prev[goal] === -2) return null;
    var cells = [];
    for (var at = goal; at >= 0; at = prev[at]) cells.unshift({ x: (at % N) - H, z: Math.floor(at / N) - H });
    cells[cells.length - 1] = { x: tx, z: tz };
    function clear(ax, az, bx, bz) {
      if (!self.lineClear(ax, az, bx, bz, 0.6, own)) return false;
      for (var u = 0, n = Math.ceil(dist2(ax, az, bx, bz) / 0.5); u <= n; u++) if (self.onRoad(lerp(ax, bx, u / n), lerp(az, bz, u / n), 0.2)) return false;
      return true;
    }
    var pts = [], fx = x, fz = z, idx = 0;
    while (idx < cells.length - 1) {
      var far = idx + 1;
      for (var t = cells.length - 1; t > idx + 1; t--) if (clear(fx, fz, cells[t].x, cells[t].z)) { far = t; break; }
      if (far === cells.length - 1) break;
      pts.push({ x: cells[far].x, z: cells[far].z });
      fx = cells[far].x; fz = cells[far].z; idx = far;
    }
    return pts;
  };
  WP.route = function (from, to) {
    // Dijkstra over the sidewalk network (a hundred-odd nodes)
    var N = this.nodes.length, dist = [], prev = [], done = [];
    if (from < 0 || to < 0) return null;
    for (var i = 0; i < N; i++) { dist[i] = 1e9; prev[i] = -1; done[i] = false; }
    dist[from] = 0;
    for (var it = 0; it < N; it++) {
      var u = -1, best = 1e9;
      for (var k = 0; k < N; k++) if (!done[k] && dist[k] < best) { best = dist[k]; u = k; }
      if (u < 0 || u === to) break;
      done[u] = true;
      var nu = this.nodes[u];
      for (var e = 0; e < nu.n.length; e++) {
        var v = nu.n[e], nv = this.nodes[v], d = dist[u] + dist2(nu.x, nu.z, nv.x, nv.z);
        if (d < dist[v]) { dist[v] = d; prev[v] = u; }
      }
    }
    if (dist[to] >= 1e9) return null;
    var path = [];
    for (var c = to; c >= 0; c = prev[c]) path.unshift(c);
    return path;
  };
  WP.nearestNode = function (x, z) {
    var best = 0, bd = 1e9;
    for (var j = 0; j < this.nodes.length; j++) {
      var d = dist2(this.nodes[j].x, this.nodes[j].z, x, z);
      if (d < bd) { bd = d; best = j; }
    }
    return best;
  };
  /* The points a walker follows along a run of nodes, kept to the right of
     the way it's going -- so two kids meeting pass side by side.  Round a
     corner the offset grows, so both legs keep their side.  A zebra runs from
     the curb on one side to the curb on the other, to the right of its middle
     line: the kid waits at the near curb while a car is close (that point is
     marked), on the edge of the sidewalk, out of the way of anyone walking
     past; and steps up onto the far curb before going on along the sidewalk. */
  WP.lanePath = function (ids, off, curb) {
    var pts = [], n = ids.length;
    if (curb === undefined) curb = TOWN.walk / 2 - 0.65;
    function onCurb(p, f, q, out) {
      var l = dist2(f.x, f.z, q.x, q.z) || 1, hx = (q.x - f.x) / l, hz = (q.z - f.z) / l, s = out ? curb : -curb;
      return { x: p.x + hx * s - hz * off, z: p.z + hz * s + hx * off };
    }
    for (var i = 0; i < n; i++) {
      var p = this.nodes[ids[i]], pt = { x: p.x, z: p.z };
      var crOut = i < n - 1 ? this.edgeCross[ids[i] + '-' + ids[i + 1]] : null;
      var crIn = i > 0 ? this.edgeCross[ids[i - 1] + '-' + ids[i]] : null;
      if (crIn || crOut) {
        // (at a corner between two zebras: up onto the curb, then over to the next one)
        if (crIn) { var up = onCurb(p, this.nodes[ids[i - 1]], p, false); up.across = true; pts.push(up); }
        if (crOut) { var wait = onCurb(p, p, this.nodes[ids[i + 1]], true); wait.cross = crOut; pts.push(wait); }
        continue;
      }
      var hx = 0, hz = 0, inX = 0, inZ = 0, miter = 1;
      if (i > 0) {
        var a = this.nodes[ids[i - 1]], l1 = dist2(a.x, a.z, p.x, p.z) || 1;
        inX = (p.x - a.x) / l1; inZ = (p.z - a.z) / l1;
        hx += inX; hz += inZ;
      }
      if (i < n - 1) {
        var b = this.nodes[ids[i + 1]], l2 = dist2(p.x, p.z, b.x, b.z) || 1;
        hx += (b.x - p.x) / l2; hz += (b.z - p.z) / l2;
      }
      var hl = Math.sqrt(hx * hx + hz * hz);
      if (hl > 0.2) {
        hx /= hl; hz /= hl;
        if (i > 0 && i < n - 1) miter = 1 / Math.max(0.6, hx * inX + hz * inZ);
      } else { hx = 0; hz = 0; }
      pt.x += -hz * off * miter;
      pt.z += hx * off * miter;
      pts.push(pt);
    }
    return pts;
  };
  /* how near a point comes to the sidewalks and to the ways in and out of the
     spots -- trees and flowers keep their distance */
  WP.edgeDist = function (x, z) {
    var best = 1e9;
    for (var i = 0; i < this.nodes.length; i++) {
      var a = this.nodes[i];
      for (var e = 0; e < a.n.length; e++) {
        if (a.n[e] < i) continue;
        var b = this.nodes[a.n[e]];
        best = Math.min(best, segDist(x, z, a.x, a.z, b.x, b.z));
      }
    }
    return best;
  };
  WP.wayDist = function (x, z) {
    var best = 1e9, list = this.spots.concat(this.partySlots || []);
    for (var i = 0; i < list.length; i++) {
      var s = list[i], n = this.nodes[s.node];
      var lines = [[n].concat(s.via || [], [s])];
      if (s.exit && s.off) lines.push([s.off].concat(s.exit, [this.nodes[s.exitNode]]));
      for (var l = 0; l < lines.length; l++) {
        var line = lines[l];
        for (var j = 1; j < line.length; j++) best = Math.min(best, segDist(x, z, line[j - 1].x, line[j - 1].z, line[j].x, line[j].z));
      }
    }
    return best;
  };

  /* Trees, bushes, flowers and the season's extras: wherever there's room,
     clear of the sidewalks, the ways in and out of the spots, and each other. */
  WP.plantTown = function () {
    var r = mulberry(this.seed + 17), R = this.R, self = this, i, a;
    this.trees = []; this.bushes = []; this.blooms = []; this.pumpkins = []; this.snowmanAt = null;
    function free(ux, z, rad, edge, way) {
      var x = ux * self.mir;
      if (Math.sqrt(ux * ux + z * z) > R - 1.6 - rad) return false;
      for (var j = 0; j < self.obst.length; j++) if (obInside(self.obst[j], x, z, rad)) return false;
      if (self.edgeDist(x, z) < edge) return false;
      if (self.wayDist(x, z) < way) return false;
      return true;
    }
    function apart(list, ux, z, gap) {
      for (var j = 0; j < list.length; j++) if (dist2(list[j][0], list[j][1], ux, z) < gap) return false;
      return true;
    }
    // trees: two rings, jittered, a pine now and then
    for (var ring = 0; ring < 2; ring++) {
      var rr = ring ? R - 9.5 : R - 4.6, step = ring ? 13 : 8.5;
      for (a = 0; a < 360; a += step) {
        var ang = (a + r() * step * 0.5) * Math.PI / 180, tr = rr + (r() - 0.5) * 1.6;
        var tx = Math.sin(ang) * tr, tz = Math.cos(ang) * tr;
        if (!free(tx, tz, 2.0, 4.6, 3.6) || !apart(this.trees, tx, tz, 6.4)) continue;
        var kind = r() < 0.38 ? 'pine' : 'ball', k = 0.82 + r() * 0.3;
        this.trees.push([tx, tz, kind, k]);
        this.obCircle(tx, tz, 1.1, 'tree');
      }
    }
    // bushes along the edge
    for (a = 4; a < 360; a += 11) {
      var ba = (a + r() * 5) * Math.PI / 180, br = R - 2.4 - r() * 1.2, bx = Math.sin(ba) * br, bz = Math.cos(ba) * br;
      if (!free(bx, bz, 1.3, 3.2, 2.6) || !apart(this.trees, bx, bz, 4.2) || !apart(this.bushes, bx, bz, 4.5)) continue;
      this.bushes.push([bx, bz, 0.85 + r() * 0.4]);
      this.obCircle(bx, bz, 1.3, 'bush');
    }
    // flowers: by the house, the square's sidewalk corners, the lots
    var spots = [[-21.2, -18.2, 1.0], [-21.2, -8.8, 1.0], [-2.6, 34.6, 2.4], [16.5, 29.5, 2.2], [-16.8, -29.6, 2.2],
                 [33.0, -12.0, 2.0], [-33.2, -4.0, 2.0], [-4.4, -33.6, 2.0], [4.6, 25.6, 1.6], [31.6, 17.2, 2.0]];
    for (i = 0; i < spots.length; i++) {
      var fs = spots[i];
      if (free(fs[0], fs[1], fs[2] * 0.5, 1.9 + fs[2] * 0.5, 1.6 + fs[2] * 0.5)) this.blooms.push(fs);
    }
    // the season's extras
    var extra = [[-33.4, 2.4], [33.6, 10.4], [-9.2, 34.0], [10.6, -33.0], [0, 36.2]];
    for (i = 0; i < extra.length && !this.snowmanAt; i++) {
      if (free(extra[i][0], extra[i][1], 1.8, 3.0, 2.6) && apart(this.trees, extra[i][0], extra[i][1], 4.4)) this.snowmanAt = extra[i];
    }
    var gourds = [[-21.3, -17.0], [-21.4, -10.0], [4.2, 24.0], [-4.6, 24.6], [30.6, -14.6], [-30.2, 21.6]];
    for (i = 0; i < gourds.length; i++) {
      if (free(gourds[i][0], gourds[i][1], 0.9, 1.9, 1.6) && apart(this.trees, gourds[i][0], gourds[i][1], 3.0)) this.pumpkins.push(gourds[i]);
    }
    if (this.snowmanAt) this.obCircle(this.snowmanAt[0], this.snowmanAt[1], 1.7, 'snowman');
    for (i = 0; i < this.pumpkins.length; i++) this.obCircle(this.pumpkins[i][0], this.pumpkins[i][1], 0.9, 'pumpkin');
  };

  WP.layoutBuild = function () {
    this.place = { house: [-1.5, -4.5] };
    this.buildSpots = [[3.2, 6.8], [-5.6, 7.6], [1.0, 10.4], [5.0, 2.6]];
  };
  WP.layoutMini = function () {
    this.place = { house: [-3.6, -3.4] };
  };

  /* Everything that does not move, batched once (again when the light, the
     stage or the season changes it). */
  WP.rebuildStatic = function () {
    var parts = [], B = new Builder(parts, this.mir), S = this.S, r = mulberry(this.seed + 11);
    var night = this.night > 0.5, R = this.R;
    island(B, R, S, r);
    if (this.mode === 'build') this.staticBuild(B, r, night);
    else if (this.mode === 'mini') this.staticMini(B, r, night);
    else this.staticTown(B, r, night);
    this.staticParts = parts;
    this.renderer.buildStatic(parts);
    this.staticNight = night;
    this.staticStage = this.stage;
  };

  WP.staticTown = function (B, r, night) {
    var R = this.R, S = this.S, T = this.town, look = this.look, P = this.place, i, a, b;
    var D = T.D, w = TOWN.road, sw = TOWN.walk, zEnd = T.zEnd, short = (D - w) * 2;
    B.at(0, 0, 0, 0);
    // the streets: two long ones to the edges, two short ones round the square
    B.box(D, 0, 0, w * 2, 0.3, zEnd * 2, ROAD, { st: 1 });
    B.box(-D, 0, 0, w * 2, 0.3, zEnd * 2, ROAD, { st: 1 });
    B.box(0, 0, D, short, 0.3, w * 2, ROAD, { st: 1 });
    B.box(0, 0, -D, short, 0.3, w * 2, ROAD, { st: 1 });
    // a sidewalk along both sides of every street
    var arm = zEnd - (D + w), armZ = (D + w + zEnd) / 2;
    B.box(T.o, 0, 0, sw, 0.45, zEnd * 2, SIDEWALK, { st: 1 });
    B.box(-T.o, 0, 0, sw, 0.45, zEnd * 2, SIDEWALK, { st: 1 });
    for (a = -1; a <= 1; a += 2) for (b = -1; b <= 1; b += 2) B.box(a * T.c, 0, b * armZ, sw, 0.45, arm, SIDEWALK, { st: 1 });
    B.box(0, 0, T.o, short, 0.45, sw, SIDEWALK, { st: 1 });
    B.box(0, 0, -T.o, short, 0.45, sw, SIDEWALK, { st: 1 });
    // the square: its own sidewalk, the paving, a ring of brick round the fountain
    B.box(0, 0, 0, short, 0.45, short, SIDEWALK, { st: 1 });
    B.box(0, 0, 0, T.inner * 2, 0.5, T.inner * 2, PLAZA, { st: 1 });
    B.add('cyl', 0, 0.535, 0, 14.6, 0.07, 14.6, S.snow ? '#d9dee5' : '#b8593f', { st: 1 });
    // lane lines between the crossings, and the zebras
    var dashes = [4.4, 22.6, 26.8, 31.0];
    for (i = 0; i < dashes.length; i++) {
      if (dashes[i] > zEnd - 1.8) continue;
      for (a = -1; a <= 1; a += 2) for (b = -1; b <= 1; b += 2) B.box(a * D, 0.3, b * dashes[i], 0.4, 0.04, 2.2, WHITE);
    }
    for (a = -1; a <= 1; a += 2) for (b = -1; b <= 1; b += 2) B.box(a * 4.4, 0.3, b * D, 2.2, 0.04, 0.4, WHITE);
    for (i = 0; i < this.cross.length; i++) {
      var cr = this.cross[i];
      for (var q = -w + 0.6; q <= w - 0.59; q += 1.16) {
        if (cr.alongX) B.box(cr.ux + q, 0.3, cr.z, 0.58, 0.04, 2.6, WHITE);
        else B.box(cr.ux, 0.3, cr.z + q, 2.6, 0.04, 0.58, WHITE);
      }
    }
    // barriers where the long streets end, two cars parked along them
    for (a = -1; a <= 1; a += 2) for (b = -1; b <= 1; b += 2) barrier(B, a * D, b * (zEnd - 0.4), 0, 5.8);
    var parkedCols = shuffle(mulberry(this.seed + 71), CARS.filter(function (c) { return c !== look.car; }));
    for (i = 0; i < this.parked.length; i++) carModel(B, this.parked[i][0], this.parked[i][1], this.parked[i][2], parkedCols[(i + 1) % parkedCols.length], false);

    // ---- the square: the fountain, and planters with two lamps, a little tree and the flag
    fountain(B, 0, 0);
    for (i = 0; i < this.planters.length; i++) {
      var pl = this.planters[i];
      planter(B, pl[0], pl[1], S, r);
      if (pl[2] === 'lamp') lampPost(B, pl[0], pl[1], night);
      else if (pl[2] === 'flag') flagPole(B, pl[0], pl[1]);
      else ballTree(B, pl[0], pl[1], 0.42, S, r);
    }
    // the benches: before the tall building, and by the playground
    for (i = 0; i < this.benches.length; i++) bench(B, this.benches[i][0], this.benches[i][1], this.benches[i][2]);

    // ---- in front: the campfire
    campfire(B, P.fire[0], P.fire[1], this.logs);

    // ---- behind: the tall building, a path to its door
    var Bk = P.back, door;
    if (look.back === 'tower') { glassTower(B, Bk[0], Bk[1], 0, night, r); door = Bk[1] + 5.2; }
    else if (look.back === 'apartment') { apartment(B, Bk[0], Bk[1], 0, look.apartment, night, r); door = Bk[1] + 4.8; }
    else { this.lampTop = lighthouse(B, Bk[0], Bk[1] - 0.4, night); door = Bk[1] + 3.3; }
    B.at(0, 0, 0, 0);
    B.box(Bk[0], 0, (door - T.outer) / 2, 3.2, 0.32, -T.outer - door, SIDEWALK, { st: 1 });

    // ---- on the left: the house (facing the street), the lemonade stand, the pond
    var H = P.house;
    house(B, H[0], H[1], this.houseYaw, look, night, 1);
    mailbox(B, -21.6, -5.4, Math.PI / 2);
    lemonadeStand(B, P.stand[0], P.stand[1], Math.PI / 2);
    pond(B, P.pond[0], P.pond[1], 5.4, S);
    dock(B, -20.9, P.pond[1], -Math.PI / 2, 3.6);
    var st = this.stream, ang = Math.atan2(st.ux, st.uz), sm = (st.s0 + st.s1) / 2;
    B.at(st.ux * sm, 0, st.uz * sm, ang);
    B.box(0, 0.05, 0, 3.4, 0.3, st.s1 - st.s0 + 1.4, S.snow ? '#bfe0f6' : WATER, { m: 'glass' });
    this.fall = { x: st.ux * (R + 0.6), z: st.uz * (R + 0.6), yaw: ang };
    buildPlate(B, P.plate[0], P.plate[1], 3.4);

    // ---- on the right: the playground on its sandy mat, the sandbox, the dance floor
    B.at(0, 0, 0, 0);
    B.box(27.9, 0, 1.5, 14.4, 0.22, 24.2, S.snow ? '#e7eef6' : '#e9c46a', { st: 1 });
    swingFrame(B, P.swings[0], P.swings[1], 0, 10.4);
    seesawBase(B, P.seesaw[0], P.seesaw[1], 0);
    slide(B, P.slide[0], P.slide[1], 0);
    trampoline(B, P.tramp[0], P.tramp[1]);
    sandbox(B, P.sandbox[0], P.sandbox[1], S);
    danceFloor(B, P.floor[0], P.floor[1], 9, 5);
    boombox(B, P.boombox[0], P.boombox[1], Math.PI);

    // ---- street lamps, trees, bushes, flowers, the season's extras
    for (i = 0; i < this.lampSpots.length; i++) lampPost(B, this.lampSpots[i][0], this.lampSpots[i][1], night);
    for (i = 0; i < this.trees.length; i++) {
      var tr = this.trees[i];
      if (tr[2] === 'pine') pine(B, tr[0], tr[1], tr[3], S, r);
      else ballTree(B, tr[0], tr[1], tr[3], S, r);
    }
    for (i = 0; i < this.bushes.length; i++) bush(B, this.bushes[i][0], this.bushes[i][1], this.bushes[i][2], S, r);
    for (i = 0; i < this.blooms.length; i++) flowers(B, this.blooms[i][0], this.blooms[i][1], S, r, 4, this.blooms[i][2]);
    if (S.snow && this.snowmanAt) snowman(B, this.snowmanAt[0], this.snowmanAt[1], -0.6);
    if (S.pumpkins) for (i = 0; i < this.pumpkins.length; i++) pumpkin(B, this.pumpkins[i][0], this.pumpkins[i][1], r);
  };

  WP.staticBuild = function (B, r, night) {
    var S = this.S;
    B.at(0, 0, 0, 0);
    // a stone path from the front to the door
    B.box(-1.5, 0, 4.6, 3.2, 0.32, 9.6, SIDEWALK, { st: 1 });
    B.box(5.0, 0, 9.0, 14, 0.32, 3.2, SIDEWALK, { st: 1 });
    crane(B, 10.2, -8.2, Math.PI * 0.78, 0.62);
    pine(B, -13.2, -6.0, 0.9, S, r);
    ballTree(B, -12.0, 6.6, 0.85, S, r);
    pine(B, 13.2, -1.6, 0.72, S, r);
    bush(B, 6.4, -1.0, 0.9, S, r);
    flowers(B, -6.4, 9.6, S, r, 5);
    flowers(B, 4.0, 12.6, S, r, 4);
    lampPost(B, 3.2, 6.6, night && this.stage >= 6);
    if (S.snow) snowman(B, -8.6, 11.2, 0.4);
    if (S.pumpkins) { pumpkin(B, 1.6, 1.8, r); pumpkin(B, -4.6, 1.6, r); }
  };
  WP.staticMini = function (B, r, night) {
    var S = this.S;
    B.at(0, 0, 0, 0);
    B.box(-3.6, 0, 3.6, 3.0, 0.3, 7.4, SIDEWALK, { st: 1 });
    house(B, -3.6, -3.4, 0, this.look, night, 0.62);
    ballTree(B, 7.4, -3.0, 0.75, S, r);
    pine(B, -10.2, 2.4, 0.66, S, r);
    flowers(B, 4.4, 5.4, S, r, 4);
    bush(B, 8.6, 3.2, 0.7, S, r);
  };

  /* ================================================================ kids */
  WP.makeKid = function (r, opts) {
    opts = opts || {};
    var W = wardrobe();
    var torso = opts.shirt || pick(r, SHIRTS), legs = opts.pants || pick(r, PANTS);
    var desc = {
      body_type: opts.body || (r() < 0.62 ? 'male' : 'female'),
      colors: { head: SKIN, torso: torso, left_arm: SKIN, right_arm: SKIN, left_leg: legs, right_leg: legs, hips: legs },
      items: {}
    };
    if (r() < 0.3 && !opts.plain) desc.colors.left_arm = desc.colors.right_arm = torso;
    var face = opts.face ? wearing(W.face, opts.face) : null;
    desc.items.face = face || pick(r, W.face);
    var roll = r();
    if (!opts.plain) {
      if (roll < 0.42 && W.hat.length) desc.items.hat = pick(r, W.hat);
      else if (W.hair.length) desc.items.hair = pick(r, W.hair);
      if (r() < 0.3 && W.shirt.length) desc.items.shirt = pick(r, W.shirt);
      if (r() < 0.22 && W.pants.length) desc.items.pants = pick(r, W.pants);
      if (r() < 0.12 && W.back.length) desc.items.back = pick(r, W.back);
    } else if (W.hair.length) {
      desc.items.hair = pick(r, W.hair);
    }
    return {
      desc: desc, x: opts.x || 0, z: opts.z || 0, y: 0, yaw: opts.yaw || 0, want: opts.yaw || 0,
      state: 'idle', pose: null, path: null, spot: null, act: null, actT: 0, idle: 0.5 + r() * 2,
      speed: 7.6 + r() * 1.6, jy: 0, vy: 0, say: null, sayT: 0, happy: 0, wave: 0, memory: {},
      seed: r() * 100, visible: opts.visible !== false, pop: 1, popT: 0, hold: null, holdT: 0,
      phase: r() * TAU, bricks: 0, id: this.kids.length
    };
  };
  WP.spawnKids = function (n) {
    var r = mulberry(this.seed + 31);
    if (this.mode === 'mini') {
      var k = this.makeKid(r, { x: 3.4 * this.mir, z: 3.2, yaw: 0.25, face: 'face_smile' });
      k.fixed = true;
      this.kids.push(k);
      return;
    }
    var spots = shuffle(r, this.spots.filter(function (s) { return s.kind !== 'catch' && s.kind !== 'look'; }));
    for (var i = 0; i < n; i++) {
      var kid = this.makeKid(r, {});
      var s = spots[i % spots.length];
      if (s && !s.user && i < spots.length) {
        kid.x = s.x; kid.z = s.z; kid.yaw = kid.want = s.yaw;
        this.claim(kid, s);
        this.begin(kid, s);
      } else {
        var node = this.nodes[Math.floor(r() * this.nodes.length)];
        kid.x = node.x; kid.z = node.z;
      }
      this.kids.push(kid);
    }
  };
  WP.claim = function (k, s) { s.user = k; k.spot = s; };
  WP.release = function (k) {
    if (k.spot && k.spot.user === k) k.spot.user = null;
    k.spot = null;
    k.act = null;
  };
  WP.say = function (k, text, secs) { k.say = text; k.sayT = secs || 2.4; };

  /* where a kid goes next */
  WP.choose = function (k) {
    var free = [], i, night = this.night > 0.5;
    for (i = 0; i < this.spots.length; i++) {
      var s = this.spots[i];
      if (s.user || s.kind === 'look') continue;
      if (s.kind === 'catch' && (!s.pair || s.pair.user)) continue;
      if (s.kind === 'fire' && !night && Math.random() < 0.6) continue;
      if (s.kind === 'kite' && night) continue;
      free.push(s);
    }
    // a pair of catch spots fills one at a time: the second goes to whoever
    // comes along, so wait for a partner only when one is already there
    for (i = 0; i < this.spots.length; i++) {
      var c = this.spots[i];
      if (c.kind === 'catch' && !c.user && c.pair && c.pair.user && free.indexOf(c) < 0) free.push(c, c);
    }
    if (!free.length) { k.idle = 1 + Math.random() * 2; return; }
    var target = free[Math.floor(Math.random() * free.length)];
    if (k.spot && k.spot.user === k) k.spot.user = null;     // off from the last one
    this.claim(k, target);
    this.walkTo(k, target);
  };
  /* The way somewhere: out of the spot a kid is leaving, the way it came
     in; along the sidewalks, kept to the right; and in by the spot's own
     way.  The points on the way out let the kid through its old spot's
     bench or plank; the curb before a zebra is where it may have to wait. */
  WP.walkTo = function (k, dest) {
    var pts = [], from, i, home = k.home, way, inRoad = this.onRoad(k.x, k.z, 0);
    k.home = null;
    k.leaving = null;
    if (home && home.exit && dist2(k.x, k.z, home.exit[0].x, home.exit[0].z) < 4.5) {
      // a spot with a way out of its own (the slide: off the end of the chute)
      for (i = 0; i < home.exit.length; i++) pts.push({ x: home.exit[i].x, z: home.exit[i].z, out: true });
      from = home.exitNode;
      k.leaving = home;
    } else if (home && home.node >= 0 && !inRoad && dist2(k.x, k.z, home.x, home.z) < 4.0 &&
               this.lineClear(k.x, k.z, home.x, home.z, 0.6, home.own || null)) {
      if (dist2(k.x, k.z, home.x, home.z) > 0.4) pts.push({ x: home.x, z: home.z, out: true });
      if (home.via) for (i = home.via.length - 1; i >= 0; i--) pts.push({ x: home.via[i].x, z: home.via[i].z, out: true });
      from = home.node;
      k.leaving = home;
    } else if (home && home.node >= 0 && !inRoad && (way = this.wayOut(k, home))) {
      pts = way;
      from = home.node;
      k.leaving = home;
    } else {
      // from wherever it is -- but off the road first if it's out on one
      // (called away halfway over a zebra): onto the nearer curb, then on
      var sx = k.x, sz = k.z, own = home ? home.own || null : null;
      if (inRoad) {
        var kerb = { x: sx, z: sz };
        this.offRoad(kerb, 0.7);
        pts.push({ x: kerb.x, z: kerb.z, across: true });
        sx = kerb.x; sz = kerb.z;
      }
      from = this.accessNode(sx, sz, own);
      if (home) k.leaving = home;
      if (!this.accessClear && from >= 0) {
        // boxed in where no straight line reaches a sidewalk: round things to it
        var fn = this.nodes[from], gw = this.gridWay(sx, sz, fn.x, fn.z, own);
        if (gw) pts = pts.concat(gw);
      }
    }
    var ids = this.route(from, dest.node);
    if (!ids) {
      // nowhere to go from here (it shouldn't happen): stay, and choose again
      if (k.spot === dest) this.release(k);
      k.path = null; k.target = null; k.idle = 1.5;
      return;
    }
    pts = pts.concat(this.lanePath(ids, TOWN.keep));
    if (dest.via) for (i = 0; i < dest.via.length; i++) pts.push({ x: dest.via[i].x, z: dest.via[i].z });
    pts.push({ x: dest.x, z: dest.z });
    k.path = pts;
    k.target = dest;
    k.lastPt = { x: k.x, z: k.z };
    k.stall = 0; k.stallD = undefined;
  };
  WP.begin = function (k, s) {
    k.act = s.kind;
    k.actT = 0;
    k.x = s.x; k.z = s.z;
    k.want = s.yaw;
    k.leaving = null;
    k.dur = ({ swing: 10, slide: 12, seesaw: 11, tramp: 8, fish: 14, dance: 10, build: 11, catch: 12, fire: 13,
               lemon: 3.4, kite: 14, bench: 10, wave: 3.2, wish: 7, sand: 12 })[s.kind] || 6;
    k.dur *= 0.8 + Math.random() * 0.5;
    if (s.kind === 'build') k.bricks = 0;
    if (s.kind === 'wish') k.coin = -1;
  };
  WP.finish = function (k) {
    var kind = k.act, s = k.spot;
    k.act = null;
    k.home = s;
    if (kind === 'lemon') { k.hold = 'cup'; k.holdT = 16; this.say(k, 'yum!'); }
    else if (Math.random() < 0.3) this.say(k, pick(Math.random, CHAT));
    k.idle = 0.6 + Math.random() * 1.6;
    k.state = 'idle';
  };

  WP.updateKid = function (k, dt) {
    var t = this.t;
    if (k.sayT > 0) { k.sayT -= dt; if (k.sayT <= 0) k.say = null; }
    if (k.happy > 0) k.happy -= dt;
    if (k.wave > 0) k.wave -= dt;
    if (k.holdT > 0) { k.holdT -= dt; if (k.holdT <= 0) k.hold = null; }
    // a hop (a tap, a cheer)
    if (k.vy || k.jy > 0) {
      k.vy -= 60 * dt;
      k.jy += k.vy * dt;
      if (k.jy <= 0) { k.jy = 0; k.vy = 0; }
    }
    if (this.mode === 'build') return this.updateBuildKid(k, dt);
    if (k.fixed) { k.state = 'idle'; k.yaw = turnTo(k.yaw, k.want, dt * 4); return; }
    // a party calls everyone to the square -- once they're off the rides
    if (this.party > 0 && !(k.act && RIDES[k.act])) return this.partyKid(k, dt);
    if (k.path) {
      var got = this.advance(k, dt, k.speed);
      if (got === 'arrived') {
        k.path = null;
        if (k.target && k.spot === k.target) this.begin(k, k.target);
        else { this.release(k); k.idle = 1 + Math.random() * 2; }
      } else this.watchProgress(k, dt, got);
      return;
    }
    if (k.act) {
      k.actT += dt;
      var s = k.spot;
      this.act(k, s, dt, t);
      if (k.act && k.actT >= k.dur && k.act !== 'slide') this.finish(k);
      return;
    }
    k.state = 'idle';
    k.y = 0;
    if (k.idle > 0) {
      k.idle -= dt;
      if (Math.random() < dt * 0.35) k.want = Math.random() * TAU;
      k.yaw = turnTo(k.yaw, k.want, dt * 4);
      return;
    }
    this.choose(k);
  };

  /* One step along a path, for a kid or the dog.  At the curb before a
     zebra it waits while a car is on the crossing or nearly there; behind
     someone walking the same way it keeps their pace. */
  WP.advance = function (a, dt, speed) {
    var next = a.path && a.path[0];
    if (!next) return 'arrived';
    var dx = next.x - a.x, dz = next.z - a.z, d = Math.sqrt(dx * dx + dz * dz);
    var hx = d > 1e-4 ? dx / d : Math.sin(a.yaw), hz = d > 1e-4 ? dz / d : Math.cos(a.yaw);
    var step = speed * dt * (a.isDog ? 1 : this.paceFor(a, hx, hz));
    var reach = Math.max(step, 0.02);
    if (next.across) { if (d < 2.0 && !this.onRoad(a.x, a.z, 0.6)) reach = 2.0; }
    else if (d < 2.4 && !this.onRoad(a.x, a.z) && this.pointTaken(next, a)) {
      // someone's already waiting on that curb: wait beside them, along it,
      // and leave the sidewalk free for whoever is walking past
      var slot = next.cross && !next.slot ? this.curbSlot(next, a) : null;
      if (slot) { next.x = slot[0]; next.z = slot[1]; next.slot = true; return 'moving'; }
      reach = 2.4;
    }
    if (d <= reach) {
      if (d <= Math.max(step, 0.02)) { a.x = next.x; a.z = next.z; }
      a.lastPt = { x: next.x, z: next.z, cross: next.cross, across: next.across };
      if (next.cross && !this.mayCross(next.cross)) {
        a.waiting = true;
        a.state = 'idle';
        var after = a.path[1];
        if (after) a.yaw = turnTo(a.yaw, Math.atan2(after.x - a.x, after.z - a.z), dt * 8);
        return 'waiting';
      }
      a.waiting = false;
      a.path.shift();
      if (a.leaving && !(a.path[0] && a.path[0].out)) a.leaving = null;
      return a.path.length ? 'moving' : 'arrived';
    }
    a.waiting = false;
    {
      var st = this.steerFor(a, hx, hz);
      if (st) {
        var sx = hx - hz * st, sz = hz + hx * st, sl = Math.sqrt(sx * sx + sz * sz) || 1;
        hx = sx / sl; hz = sz / sl;
      }
    }
    a.x += hx * step; a.z += hz * step;
    a.want = Math.atan2(hx, hz);
    a.yaw = turnTo(a.yaw, a.want, dt * 10);
    a.state = step > speed * dt * 0.3 ? 'walk' : 'idle';
    return 'moving';
  };
  /* Pushed against a lamp or a tree by someone passing, a walker can stop
     getting any nearer where it's going: then it finds a fresh way there,
     from wherever it now is. */
  WP.watchProgress = function (k, dt, got) {
    var next = k.path && k.path[0];
    if (!next || got === 'waiting') { k.stall = 0; k.stallD = undefined; return; }
    var d = dist2(k.x, k.z, next.x, next.z);
    if (k.stallD === undefined || d < k.stallD - 0.25) { k.stallD = d; k.stall = 0; k.stuckFor = 0; return; }
    k.stall = (k.stall || 0) + dt;
    k.stuckFor = (k.stuckFor || 0) + dt;
    if (k.stall < 0.9) return;
    k.stall = 0;
    var own = (k.target && k.target.own) || null, self = this;
    function clear(ax, az, bx, bz) { return self.lineClear(ax, az, bx, bz, 0.7, own) && self.peopleClear(ax, az, bx, bz, k); }
    var blockedBy = !this.lineClear(k.x, k.z, next.x, next.z, 0.7, own) ? 'thing' : (!this.peopleClear(k.x, k.z, next.x, next.z, k) ? 'kid' : '');
    if (!blockedBy && k.stuckFor < 3) return;
    k.stallD = undefined;
    // a step round whatever it is (people too if it can, things at least), else back
    // to where the way was clear, else a fresh way from here
    for (var pass = 0; pass < 2; pass++) {
      var best = null, bd = 1e9;
      for (var a = 0; a < 12; a++) {
        for (var r = 1.6; r <= 3.2; r += 1.6) {
          var px = k.x + Math.sin(a / 12 * TAU) * r, pz = k.z + Math.cos(a / 12 * TAU) * r;
          if (this.onRoad(px, pz, 0.65) && !next.across) continue;
          var cost = r + dist2(px, pz, next.x, next.z);
          if (cost >= bd) continue;
          var ok = pass === 0 ? clear(k.x, k.z, px, pz) && clear(px, pz, next.x, next.z)
                              : this.lineClear(k.x, k.z, px, pz, 0.7, own) && this.lineClear(px, pz, next.x, next.z, 0.7, own);
          if (ok) { bd = cost; best = { x: px, z: pz }; }
        }
      }
      if (best) { best.across = next.across; k.path.unshift(best); return; }
    }
    if (!next.across && k.stuckFor > 2) {
      var gw = this.gridWay(k.x, k.z, next.x, next.z, (k.leaving && k.leaving.own) ? (own || []).concat(k.leaving.own) : own);
      if (gw && gw.length && k.path.length < 40) { k.stuckFor = 0; for (var g = gw.length - 1; g >= 0; g--) k.path.unshift(gw[g]); return; }
    }
    // back to the last point it reached -- if that's this side of the road
    var lp = k.lastPt;
    if (lp && dist2(k.x, k.z, lp.x, lp.z) > 0.3 && dist2(next.x, next.z, lp.x, lp.z) > 0.3 && k.path.length < 40 &&
        this.blockOf(k.x, k.z) !== 'street' && this.blockOf(lp.x, lp.z) === this.blockOf(k.x, k.z)) { k.path.unshift(lp); return; }
    if (k.target) { k.home = null; this.walkTo(k, k.target); }
  };
  /* does a straight walk from a to b keep clear of everyone standing still? */
  WP.peopleClear = function (ax, az, bx, bz, k) {
    for (var i = 0; i < this.kids.length; i++) {
      var o = this.kids[i];
      if (o === k || !o.visible || (o.path && !o.waiting)) continue;
      if (segDist(o.x, o.z, ax, az, bx, bz) < 1.9) return false;
    }
    return true;
  };
  /* how much to bear right (+) or left (-) to pass whoever is just ahead:
     away from their side, and to the right when they're dead ahead */
  WP.steerFor = function (k, hx, hz) {
    var st = 0;
    k.room = null;
    for (var i = 0; i < this.kids.length; i++) {
      var o = this.kids[i];
      if (o === k || !o.visible) continue;
      var dx = o.x - k.x, dz = o.z - k.z, ahead = dx * hx + dz * hz;
      if (ahead <= 0.2 || ahead > 3.4) continue;
      var lat = dx * hz - dz * hx;                 // + : they're on our left
      if (Math.abs(lat) > 1.9) continue;
      // someone going our way at our pace needs no passing
      if (o.path && !o.waiting && Math.sin(o.yaw) * hx + Math.cos(o.yaw) * hz > 0.6) continue;
      var wgt = (1 - ahead / 3.4) * (1 - Math.abs(lat) / 1.9);
      // away from their side -- unless that's into a road or a lamp post: then
      // round their other side if they're mostly in the way, else straight on
      var dir = lat > 0.25 ? 1 : (lat < -0.25 ? -1 : 0);
      if (!dir) dir = this.roomOn(k, hx, hz, 1) || !this.roomOn(k, hx, hz, -1) ? 1 : -1;
      else if (!this.roomOn(k, hx, hz, dir)) dir = Math.abs(lat) < 0.9 && this.roomOn(k, hx, hz, -dir) ? -dir : 0;
      st += dir * wgt * 1.6;
    }
    k.room = null;
    return clamp(st, -0.9, 0.9);
  };
  /* is there room to step aside this way (+1 right, -1 left): not out into
     a road (unless crossing it), into a thing or off the island? */
  WP.roomOn = function (k, hx, hz, dir) {
    var memo = k.room || (k.room = {});
    if (memo[dir] !== undefined) return memo[dir];
    var px = k.x + hx * 0.9 - hz * dir * 1.5, pz = k.z + hz * 0.9 + hx * dir * 1.5, ok = true;
    var own = (k.target && k.target.own) || null;
    if (!(k.path && k.path[0] && k.path[0].across) && this.onRoad(px, pz, 0.2)) ok = false;
    else if (Math.sqrt(px * px + pz * pz) > this.R - 1.6) ok = false;
    else for (var i = 0; i < this.obst.length; i++) {
      if (own && own.indexOf(this.obst[i]) >= 0) continue;
      if (obInside(this.obst[i], px, pz, 0.5)) { ok = false; break; }
    }
    memo[dir] = ok;
    return ok;
  };
  /* a place on the curb beside whoever is waiting at p: along the curb,
     away from the zebra's middle if there's room (else the other way), and
     never in a road, a thing or someone else */
  WP.curbSlot = function (p, a) {
    var cr = p.cross, ux = cr.alongX ? 0 : 1, uz = cr.alongX ? 1 : 0, i;
    var side = (p.x - cr.x) * ux + (p.z - cr.z) * uz >= 0 ? 1 : -1;
    for (var t = 0; t < 2; t++) {
      var sg = t ? -side : side, x = p.x + ux * 1.9 * sg, z = p.z + uz * 1.9 * sg, ok = true;
      if (this.onRoad(x, z, 0.6) || Math.sqrt(x * x + z * z) > this.R - 1.5) continue;
      for (i = 0; i < this.obst.length && ok; i++) if (obInside(this.obst[i], x, z, 0.85)) ok = false;
      for (i = 0; i < this.kids.length && ok; i++) {
        var o = this.kids[i];
        if (o !== a && o.visible && dist2(o.x, o.z, x, z) < 1.6) ok = false;
      }
      if (ok) return [x, z];
    }
    return null;
  };
  /* is someone else standing on this point of a path? */
  WP.pointTaken = function (p, a) {
    for (var i = 0; i < this.kids.length; i++) {
      var o = this.kids[i];
      if (o !== a && o.visible && dist2(o.x, o.z, p.x, p.z) < 1.4) return true;
    }
    return false;
  };
  /* someone just ahead going the same way sets the pace (but out on a
     zebra a kid just keeps going) */
  WP.paceFor = function (k, hx, hz) {
    if (k.path && k.path[0] && k.path[0].across) return 1;
    var f = 1;
    for (var i = 0; i < this.kids.length; i++) {
      var o = this.kids[i];
      if (o === k || !o.visible || !o.path || o.waiting) continue;
      var dx = o.x - k.x, dz = o.z - k.z, ahead = dx * hx + dz * hz;
      if (ahead <= 0 || ahead > 3.4) continue;
      if (Math.abs(dx * hz - dz * hx) > 1.3) continue;
      var ox = Math.sin(o.yaw), oz = Math.cos(o.yaw);
      if (ox * hx + oz * hz < 0.4) continue;
      var keep = clamp((ahead - 2.0) / 1.4, 0, 1);
      f = Math.min(f, keep + (1 - keep) * Math.min(1, o.speed / k.speed));
    }
    return f;
  };

  /* what doing each thing looks like */
  WP.act = function (k, s, dt, t) {
    k.yaw = turnTo(k.yaw, k.want, dt * 6);
    k.y = 0;
    k.climb = false;
    switch (k.act) {
      case 'swing': {
        var th = Math.sin(t * 2.1 + s.phase) * 0.62;
        var L = s.pivot - s.seat;
        k.x = s.x; k.z = s.z + Math.sin(th) * L; k.y = s.pivot - Math.cos(th) * L - 1.1;
        k.state = 'sit';
        k.swing = th;
        break;
      }
      case 'slide': {
        // up the ladder, a moment at the top, down the chute, hop off -- and
        // round the side of the slide to the ladder for another go
        var px = s.prop[0] * this.mir, pz = s.prop[1], cyc = k.actT % 6.2;
        if (cyc < 1.4) {
          k.x = px; k.z = pz - 3.75; k.y = smooth(cyc / 1.4) * 5.0; k.state = 'walk'; k.climb = true; k.want = 0;
        } else if (cyc < 1.9) {
          k.x = px; k.z = pz - 2.3; k.y = 5.4; k.state = 'sit'; k.want = 0;
        } else if (cyc < 3.0) {
          var v = smooth((cyc - 1.9) / 1.1);
          k.x = px; k.z = lerp(pz - 1.6, pz + 5.0, v); k.y = lerp(5.3, 0.7, v); k.state = 'sit'; k.want = 0;
          if (v > 0.9 && !k.whee) { k.whee = true; if (Math.random() < 0.5) this.say(k, 'wheee!', 1.6); }
        } else if (cyc < 3.5) {
          k.whee = false;
          k.x = px; k.z = pz + 6.6; k.state = 'idle'; k.want = 0;
          if (k.actT > k.dur) { this.finish(k); return; }
        } else {
          var side = 2.5 * this.mir, way = [[px, pz + 6.6], [px + side, pz + 6.0], [px + side, pz - 3.4], [px, pz - 3.75]];
          var u = (cyc - 3.5) / 2.7, total = 0, seg = [], j;
          for (j = 1; j < way.length; j++) { seg.push(dist2(way[j - 1][0], way[j - 1][1], way[j][0], way[j][1])); total += seg[j - 1]; }
          var go = u * total;
          for (j = 0; j < seg.length - 1 && go > seg[j]; j++) go -= seg[j];
          var f = clamp(go / seg[j], 0, 1);
          k.x = lerp(way[j][0], way[j + 1][0], f); k.z = lerp(way[j][1], way[j + 1][1], f);
          k.want = Math.atan2(way[j + 1][0] - way[j][0], way[j + 1][1] - way[j][1]);
          k.state = 'walk';
        }
        break;
      }
      case 'seesaw': {
        var other = this.otherSeesaw(s), both = other && other.user && !other.user.path && other.user.act === 'seesaw';
        var tilt = both ? Math.sin(t * 1.8) * 0.3 : 0.3 * s.end;
        k.x = s.x; k.z = s.z; k.y = 1.6 + Math.sin(tilt) * (s.len / 2) * s.end * (this.mir < 0 ? -1 : 1) * -1;
        k.y = Math.max(0.4, k.y);
        k.state = 'sit';
        break;
      }
      case 'tramp': {
        var b = Math.abs(Math.sin(k.actT * Math.PI / 0.75));
        k.y = 1.2 + b * 4.2; k.state = b > 0.25 ? 'jump' : 'idle';
        break;
      }
      case 'fish':
        k.state = 'sit'; k.y = 0.5;
        if (Math.random() < dt * 0.12 && !this.fish) this.fishJump(s);
        break;
      case 'dance':
        k.state = 'idle';
        if (Math.random() < dt * 0.2) k.want = s.yaw + (Math.random() - 0.5) * 1.2;
        break;
      case 'build':
        k.state = 'idle';
        k.bricks = Math.min(6, Math.floor(k.actT / 1.4));
        if (k.bricks >= 6 && !k.cheered) { k.cheered = true; k.vy = 16; this.say(k, 'ta-da!', 1.8); }
        if (k.actT < 1) k.cheered = false;
        break;
      case 'catch':
        k.state = 'idle';
        k.want = Math.atan2(s.pair.x - s.x, s.pair.z - s.z);
        break;
      case 'fire':
        k.state = 'sit'; k.y = 0.62;
        if (Math.random() < dt * 0.05) this.say(k, pick(Math.random, CHAT));
        break;
      case 'bench':
        k.state = 'sit'; k.y = 0.95;
        if (Math.random() < dt * 0.05) this.say(k, pick(Math.random, CHAT));
        break;
      case 'kite':
        k.state = 'idle';
        break;
      case 'lemon':
        k.state = 'idle';
        k.want = Math.atan2(s.stand[0] * this.mir - s.x, s.stand[1] - s.z);
        break;
      case 'wave':
        k.state = 'idle';
        k.want = this.camYaw + Math.PI;
        k.wave = 0.5;
        break;
      case 'wish': {
        // a coin into the fountain every few seconds -- and a splash
        k.state = 'idle';
        k.want = s.yaw;
        var n = Math.floor(k.actT / 2.6);
        if (k.actT % 2.6 > 1.25 && k.coin !== n) {
          k.coin = n;
          var to = this.coinTarget(k);
          if (this.particles) this.particles.burst('impact', to, { color: '#bfe3ff' });
          this.sparkle([to[0], to[1] + 0.4, to[2]], 5);
          if (Math.random() < 0.35) this.say(k, pick(Math.random, ['make a wish!', 'wish wish!', 'pls pls pls', '✨']), 1.8);
        }
        break;
      }
      case 'sand':
        k.state = 'sit'; k.y = 0.55;
        break;
      default:
        k.state = 'idle';
    }
  };
  /* where a wished-on coin lands: in the water, between the kid and the spout */
  WP.coinTarget = function (k) {
    var d = Math.sqrt(k.x * k.x + k.z * k.z) || 1;
    return [k.x - k.x / d * 2.6, 1.98, k.z - k.z / d * 2.6];
  };
  WP.otherSeesaw = function (s) {
    for (var i = 0; i < this.spots.length; i++) {
      var o = this.spots[i];
      if (o !== s && o.kind === 'seesaw') return o;
    }
    return null;
  };

  /* the one kid of the set-up wizard (and two friends at the end) */
  WP.updateBuildKid = function (k, dt) {
    var vis = this.stage >= 3 || k.friend;
    if (vis && !k.visible) {
      k.visible = true; k.popT = this.t;
      this.sparkle([k.x, 2, k.z], 14);
      this.say(k, k.friend ? pick(Math.random, ['hi!', 'welcome!', 'play?']) : 'hi!');
      k.wave = 1.6;
    }
    if (!vis) { k.visible = false; return; }
    k.pop = backOut((this.t - (k.popT || 0)) / 0.6);
    if (k.friend) { k.state = 'idle'; k.yaw = turnTo(k.yaw, k.want, dt * 4); return; }
    if (k.path) {
      var next = k.path[0], dx = next.x - k.x, dz = next.z - k.z, d = Math.sqrt(dx * dx + dz * dz), step = 6.5 * dt;
      k.want = Math.atan2(dx, dz);
      k.yaw = turnTo(k.yaw, k.want, dt * 9);
      k.state = 'walk';
      if (d <= step) { k.x = next.x; k.z = next.z; k.path.shift(); if (!k.path.length) { k.path = null; k.idle = 1.5 + Math.random() * 2.5; k.want = this.camYaw + Math.PI + (Math.random() - 0.5); } }
      else { k.x += dx / d * step; k.z += dz / d * step; }
      return;
    }
    k.state = 'idle';
    k.yaw = turnTo(k.yaw, k.want, dt * 4);
    if (k.idle > 0) { k.idle -= dt; if (Math.random() < dt * 0.25) k.wave = 1.2; return; }
    var spots = this.buildSpots || [], goal = spots[Math.floor(Math.random() * spots.length)];
    if (goal) k.path = [{ x: goal[0], z: goal[1] }];
    else k.idle = 2;
  };

  /* a dance party: everybody to the square, round the fountain -- along the
     sidewalks like any other walk, at a run */
  WP.partyKid = function (k, dt) {
    if (!k.partySpot) {
      var slots = this.partySlots;
      if (!slots || !slots.length) {
        // no square here: a ring round the middle
        var i0 = this.kids.indexOf(k), a0 = (i0 / this.kids.length) * TAU;
        slots = [{ x: Math.sin(a0) * 6.2, z: Math.cos(a0) * 6.2, node: -1 }];
      }
      var slot = slots[this.kids.indexOf(k) % slots.length];
      if (k.spot && (k.act || k.path)) k.home = k.spot;
      this.release(k);
      k.path = null;
      k.partySpot = slot;
      if (slot.node >= 0) this.walkTo(k, slot);
      else k.path = [{ x: slot.x, z: slot.z }];
    }
    if (k.path) {
      var got = this.advance(k, dt, k.speed * 1.25);
      if (got === 'moving') k.state = 'run';
      if (got === 'arrived') k.path = null;
      else this.watchProgress(k, dt, got);
      k.y = 0;
      return;
    }
    k.state = 'idle';
    k.y = 0;
    k.want = Math.atan2(-k.x, -k.z) + Math.sin(this.t * 2 + k.seed) * 0.6;
    k.yaw = turnTo(k.yaw, k.want, dt * 5);
    k.dancing = true;
  };

  /* A kid's pose this frame: the engine's own walk/run/sit/jump, then
     whatever the moment adds -- a wave, a dance, arms up on the swing. */
  WP.kidPose = function (k, dt) {
    var base = Avatar.smoothPose(k.memory, k.state, this.t + k.seed, k.state === 'walk' ? 1 : 0, k.desc, dt);
    var p = {};
    for (var key in base) p[key] = base[key];
    var t = this.t + k.seed;
    var act = k.act;
    if (k.dancing || act === 'dance') {
      var s = Math.sin(t * 7);
      p.armL = -2.4 + s * 0.7; p.armR = -2.4 - s * 0.7;
      p.armLZ = 0.4; p.armRZ = -0.4;
      p.bob = Math.abs(Math.sin(t * 7)) * 0.35;
      p.legL = s * 0.25; p.legR = -s * 0.25;
    } else if (k.climb && act === 'slide') {
      p.armL = -2.6 + Math.sin(t * 9) * 0.4; p.armR = -2.6 - Math.sin(t * 9) * 0.4;
    } else if (act === 'swing') {
      p.armL = -2.7; p.armR = -2.7;
      p.legL = -1.3 + (k.swing || 0) * 0.8; p.legR = p.legL;
    } else if (act === 'seesaw') {
      p.armL = -1.2; p.armR = -1.2;
    } else if (act === 'tramp') {
      p.armL = -2.2 + Math.sin(t * 8) * 0.4; p.armR = -2.2 - Math.sin(t * 8) * 0.4;
    } else if (act === 'fish') {
      p.armL = -1.1; p.armR = -1.3;
      p.legL = -1.5; p.legR = -1.5;
    } else if (act === 'build') {
      var reach = Math.max(0, Math.sin(t * 4.5));
      p.armR = -1.4 - reach * 0.4; p.armL = -0.9;
      p.lean = 0.18;
    } else if (act === 'catch') {
      var ph = this.catchPhase(k);
      if (ph.throwing) { p.armR = -2.8 + ph.u * 2.6; }
      else { p.armL = -1.5; p.armR = -1.5; }
    } else if (act === 'kite') {
      p.armR = -2.3; p.armL = -1.7;
    } else if (act === 'fire') {
      p.armR = -1.2;
    } else if (act === 'lemon') {
      p.armR = -1.3;
    } else if (act === 'wish') {
      var ph = k.actT % 2.6;
      p.armR = ph < 0.5 ? -2.9 + (ph / 0.5) * 2.2 : -0.6;
      p.armL = -0.3;
    } else if (act === 'sand') {
      p.armR = -1.1 + Math.sin(t * 6) * 0.45; p.armL = -0.9;
      p.lean = 0.22;
    }
    if (k.hold === 'cup' && !act) { p.armR = -1.25; }
    if (k.wave > 0 || act === 'wave') {
      var w = Math.sin(t * 13);
      p.armR = -2.9; p.armRZ = -0.25 - w * 0.35;
    }
    if (k.happy > 0) { p.armL = -2.8; p.armR = -2.8; p.armLZ = 0.35; p.armRZ = -0.35; }
    return p;
  };

  WP.catchPhase = function (k) {
    var s = k.spot, a = s, b = s.pair;
    var period = 1.6, u = (this.t % (period * 2)) / period;
    var first = this.spots.indexOf(a) < this.spots.indexOf(b);
    var throwing = first ? u < 1 : u >= 1;
    return { throwing: throwing && (u % 1) < 0.25, u: (u % 1) / 0.25 };
  };

  /* ======================================================= the frame */
  WP.warm = function (secs) {
    var dt = 1 / 30;
    for (var s = 0; s < secs; s += dt) this.step(dt, true);
  };

  WP.loop = function (ts) {
    if (this.dead) return;
    this.raf = requestAnimationFrame(this.loop);
    if (!this.visible || (global.document && document.hidden)) { this.last = ts; return; }
    var dt = this.last ? Math.min(0.05, (ts - this.last) / 1000) : 0.016;
    this.last = ts;
    this.budget(dt);
    this.step(dt, false);
    this.frame(dt);
  };
  /* a device that can't keep up gets fewer pixels, not a stutter */
  WP.budget = function (dt) {
    this.frameMs.push(dt);
    if (this.frameMs.length < 90) return;
    var avg = this.frameMs.reduce(function (a, b) { return a + b; }, 0) / this.frameMs.length;
    this.frameMs = [];
    var rd = this.renderer;
    if (avg > 1 / 38 && rd.renderScale > 0.55) { rd.renderScale = Math.max(0.55, rd.renderScale - 0.15); }
    else if (avg < 1 / 55 && rd.renderScale < 1) { rd.renderScale = Math.min(1, rd.renderScale + 0.1); }
  };

  WP.step = function (dt, warming) {
    this.t += dt;
    var t = this.t;
    if (this.lightMix < 1) {
      this.lightMix = Math.min(1, this.lightMix + dt / 1.6);
      this.applyLight(this.lightMix);
    }
    if (this.badgeHit > 0) this.badgeHit = Math.max(0, this.badgeHit - dt);
    if (this.mode === 'build') this.stepBuild(dt);
    for (var i = 0; i < this.kids.length; i++) this.updateKid(this.kids[i], dt);
    this.separate(dt);
    if (this.cfg.critters) this.stepCritters(dt);
    if (this.cfg.town) this.stepCars(dt);
    if (this.cfg.events && !warming) this.stepEvents(dt);
    if (this.cfg.threats && !warming) this.stepThreats(dt);
    if (this.mode === 'mini' && !warming) this.stepMini(dt);
    this.stepThings(dt);
    if (!warming) this.ambient(dt);
    // the camera: a slow sway round the front, or where a drag left it
    if (!this.dragging) {
      this.drag *= Math.pow(0.35, dt);
      this.drag += this.dragVel * dt;
      this.dragVel *= Math.pow(0.05, dt);
    }
    var cfg = this.cfg;
    this.camYaw = cfg.az + Math.sin(t * TAU / 46) * cfg.sway + this.drag;
  };

  /* Kids keep out of each other's way.  Whoever is walking slides round
     whoever is standing or playing (they don't budge); two walkers meeting
     both step to their right; and afterwards nobody is left inside the
     fountain, a wall, a pond, a tree or off the edge. */
  WP.separate = function (dt) {
    var ks = this.kids, n = ks.length, MIN = 2.05, pull = Math.min(1, dt * 18), i, j;
    for (i = 0; i < n; i++) {
      var a = ks[i];
      if (!a.visible) continue;
      var ma = this.mobility(a);
      for (j = i + 1; j < n; j++) {
        var b = ks[j];
        if (!b.visible) continue;
        var mb = this.mobility(b);
        if (!ma && !mb) continue;
        var dx = b.x - a.x, dz = b.z - a.z, d = Math.sqrt(dx * dx + dz * dz);
        if (!(d < MIN)) continue;
        if (d < 1e-3) { dx = Math.sin(a.yaw + 1.5); dz = Math.cos(a.yaw + 1.5); d = 1e-3; }
        var nx = dx / Math.max(d, 1e-3), nz = dz / Math.max(d, 1e-3), pen = (MIN - d) * pull;
        var wa = ma / (ma + mb), wb = mb / (ma + mb);
        var pa = this.sidestep(a, -nx, -nz), pb = this.sidestep(b, nx, nz);
        a.x += pa[0] * pen * wa; a.z += pa[1] * pen * wa;
        b.x += pb[0] * pen * wb; b.z += pb[1] * pen * wb;
      }
    }
    if (this.dog) this.dogRoom();
    for (i = 0; i < n; i++) if (ks[i].visible && this.mobility(ks[i])) this.unstick(ks[i]);
  };
  WP.mobility = function (k) {
    if (k.fixed || k.friend || (k.act && !k.path)) return 0;
    if (k.path) return k.waiting ? 0.5 : 1;
    return 0.5;
  };
  /* a push on a walker turns into a step to the side, not back the way it came */
  WP.sidestep = function (k, px, pz) {
    if (!k.path || k.waiting) return [px, pz];
    var hx = Math.sin(k.yaw), hz = Math.cos(k.yaw), along = px * hx + pz * hz;
    var lx = px - along * hx, lz = pz - along * hz, ll = Math.sqrt(lx * lx + lz * lz);
    if (ll < 0.35) {                                    // head on: to its right, if there's room
      if (!this.roomOn(k, hx, hz, 1) && this.roomOn(k, hx, hz, -1)) { lx = hz; lz = -hx; } else { lx = -hz; lz = hx; }
      ll = 1;
      k.room = null;
    }
    var bx = lx / ll + hx * Math.max(0, along) * 0.3, bz = lz / ll + hz * Math.max(0, along) * 0.3;
    var bl = Math.sqrt(bx * bx + bz * bz) || 1;
    return [bx / bl, bz / bl];
  };
  /* out of anything solid (but into its own spot's bench or swing, and out
     of the one it's leaving), and onto the island */
  WP.unstick = function (k) {
    var own = (k.target && k.target.own) || (k.spot && k.spot.own) || null, old = k.leaving && k.leaving.own;
    for (var pass = 0; pass < 2; pass++) {
      for (var i = 0; i < this.obst.length; i++) {
        var o = this.obst[i];
        if ((own && own.indexOf(o) >= 0) || (old && old.indexOf(o) >= 0)) continue;
        var q = obPush(o, k.x, k.z, 0.85);
        if (q) { k.x = q[0]; k.z = q[1]; }
      }
    }
    if (k.waiting || !(k.path && k.path[0] && k.path[0].across)) this.offRoad(k, 0.6);
    var r = Math.sqrt(k.x * k.x + k.z * k.z), lim = this.R - 1.2;
    if (r > lim) { k.x *= lim / r; k.z *= lim / r; }
  };
  /* back onto the sidewalk: nobody but someone on a zebra stands in a road.
     The nearest point that is off every road -- which at a corner of the
     square can be the corner itself, out of both streets at once (stepping
     straight out of one street there only lands in the other). */
  WP.offRoad = function (k, pad) {
    var T = this.town, i, j, a, b;
    if (!T) return;
    if (!this.roads) {
      var D = T.D, w = TOWN.road;
      this.roads = [this.rectOf(D, 0, w, T.zEnd, 0), this.rectOf(-D, 0, w, T.zEnd, 0),
                    this.rectOf(0, D, D - w, w, 0), this.rectOf(0, -D, D - w, w, 0)];
    }
    var R = this.roads, inAny = false;
    for (i = 0; i < R.length && !inAny; i++) if (inRect(R[i], k.x, k.z, pad)) inAny = true;
    if (!inAny) return;
    // the streets are square to the axes: try every face line of every street,
    // across and along, and keep the nearest point clear of them all
    var xs = [k.x], zs = [k.z], best = null, bd = 1e9;
    for (i = 0; i < R.length; i++) {
      xs.push(R[i].x - R[i].hx - pad, R[i].x + R[i].hx + pad);
      zs.push(R[i].z - R[i].hz - pad, R[i].z + R[i].hz + pad);
    }
    for (a = 0; a < xs.length; a++) for (b = 0; b < zs.length; b++) {
      var d = dist2(xs[a], zs[b], k.x, k.z);
      if (d >= bd) continue;
      var ok = true;
      for (j = 0; j < R.length && ok; j++) if (inRect(R[j], xs[a], zs[b], pad - 0.01)) ok = false;
      if (ok) { bd = d; best = [xs[a], zs[b]]; }
    }
    if (best) { k.x = best[0]; k.z = best[1]; }
  };
  /* the dog gives everyone room, and keeps out of things too */
  WP.dogRoom = function () {
    var dog = this.dog;
    for (var i = 0; i < this.kids.length; i++) {
      var k = this.kids[i];
      if (!k.visible) continue;
      var dx = dog.x - k.x, dz = dog.z - k.z, d = Math.sqrt(dx * dx + dz * dz);
      if (d < 1.9 && d > 1e-3) {
        if (dog.path && !dog.waiting) {
          var side = this.sidestep(dog, dx / d, dz / d);
          dog.x += side[0] * (1.9 - d); dog.z += side[1] * (1.9 - d);
        } else { dog.x = k.x + dx / d * 1.9; dog.z = k.z + dz / d * 1.9; }
      }
    }
    for (var j = 0; j < this.obst.length; j++) {
      var q = obPush(this.obst[j], dog.x, dog.z, 0.8);
      if (q) { dog.x = q[0]; dog.z = q[1]; }
    }
    if (dog.waiting || !(dog.path && dog.path[0] && dog.path[0].across)) this.offRoad(dog, 0.6);
  };

  WP.applyLight = function (mix) {
    var a = LIGHTS[this.lightFrom] || LIGHTS.day, b = LIGHTS[this.light] || LIGHTS.day, t = smooth(mix);
    var rd = this.renderer;
    rd.setSky({
      top: mixHex(a.top, b.top, t), horizon: mixHex(a.horizon, b.horizon, t),
      sun: [lerp(a.sun[0], b.sun[0], t), lerp(a.sun[1], b.sun[1], t), lerp(a.sun[2], b.sun[2], t)],
      clouds: lerp(a.clouds, b.clouds, t), tint: '#ffffff'
    });
    rd.setAmbient(mixHex(a.ambient, b.ambient, t));
    rd.sunColor = [lerp(a.sunColor[0], b.sunColor[0], t), lerp(a.sunColor[1], b.sunColor[1], t), lerp(a.sunColor[2], b.sunColor[2], t)];
    this.night = lerp(a.night, b.night, t);
    var want = this.night > 0.5;
    if (this.staticParts && want !== this.staticNight) this.rebuildStatic();
  };

  /* ------------------------------------------------------- the camera */
  WP.fitCamera = function () {
    var rd = this.renderer, cfg = this.cfg, R = this.R;
    var aspect = rd.aspect || 1;
    // room above the dome for the shield badge the overlay draws there (about
    // 34 CSS pixels), whatever the size of the picture
    var room = Math.min(0.3, 36 / Math.max(60, (this.cssH || 300) / 2));
    if (this.fit && this.fit.aspect === aspect && this.fit.room === room && this.fit.yaw === Math.round(this.camYaw * 50)) return this.fit;
    var Rd = this.domeR(), top = Rd * 0.92, bottom = -(this.mode === 'mini' ? 12 : 22);
    var pts = [];
    for (var i = 0; i < 12; i++) {
      var a = i / 12 * TAU;
      pts.push([Math.sin(a) * (Rd + 0.5), 0, Math.cos(a) * (Rd + 0.5)]);
      pts.push([Math.sin(a) * Rd * 0.7, top * 0.72, Math.cos(a) * Rd * 0.7]);
      pts.push([Math.sin(a) * R * 0.7, bottom * 0.45, Math.cos(a) * R * 0.7]);
    }
    pts.push([0, top, 0], [0, bottom, 0]);
    var target = [0, (top + bottom) * 0.22, 0];
    var lo = R * 1.2, hi = R * 14, fov = cfg.fov;
    for (var it = 0; it < 22; it++) {
      var mid = (lo + hi) / 2;
      if (this.fitsAt(pts, target, mid, aspect, fov, cfg.margin, room)) hi = mid; else lo = mid;
    }
    this.fit = { aspect: aspect, room: room, yaw: Math.round(this.camYaw * 50), dist: hi, target: target };
    return this.fit;
  };
  WP.eyeAt = function (target, dist) {
    var p = this.cfg.pitch, y = this.camYaw;
    return [target[0] + Math.sin(y) * Math.cos(p) * dist, target[1] + Math.sin(p) * dist, target[2] + Math.cos(y) * Math.cos(p) * dist];
  };
  WP.fitsAt = function (pts, target, dist, aspect, fov, margin, room) {
    var rd = this.renderer, M = GLX.mat, eye = this.eyeAt(target, dist);
    var view = M.identity(), proj = M.identity(), vp = M.identity();
    M.lookAt(view, eye, target, [0, 1, 0]);
    M.perspective(proj, fov * M.toRad, aspect, rd.near, rd.far);
    M.multiply(vp, proj, view);
    var lim = 1 - margin;
    for (var i = 0; i < pts.length; i++) {
      var q = pts[i];
      var x = vp[0] * q[0] + vp[4] * q[1] + vp[8] * q[2] + vp[12];
      var y = vp[1] * q[0] + vp[5] * q[1] + vp[9] * q[2] + vp[13];
      var w = vp[3] * q[0] + vp[7] * q[1] + vp[11] * q[2] + vp[15];
      if (w <= 0) return false;
      if (Math.abs(x / w) > lim || Math.abs(y / w) > lim || y / w > lim - (room || 0)) return false;
    }
    return true;
  };
  /* world -> CSS pixels of the overlay */
  WP.project = function (p) {
    var vp = this.renderer.viewProj;
    var x = vp[0] * p[0] + vp[4] * p[1] + vp[8] * p[2] + vp[12];
    var y = vp[1] * p[0] + vp[5] * p[1] + vp[9] * p[2] + vp[13];
    var w = vp[3] * p[0] + vp[7] * p[1] + vp[11] * p[2] + vp[15];
    if (w <= 0.0001) return null;
    return { x: (x / w * 0.5 + 0.5) * this.cssW, y: (0.5 - y / w * 0.5) * this.cssH, w: w };
  };
  WP.domeR = function () { return this.R + (this.mode === 'mini' ? 3 : 3.6); };

  /* --------------------------------------------------------- drawing */
  WP.frame = function (dt) {
    var rd = this.renderer;
    rd.resize();
    this.sizeOverlay();
    rd.beginFrame(dt);
    var parts = [], B = new Builder(parts, 1);
    this.drawKids(parts, dt);
    this.drawDynamic(B);
    for (var i = 0; i < parts.length; i++) rd.push(parts[i]);
    this.drawDome();
    var fit = this.fitCamera();
    var eye = this.eyeAt(fit.target, fit.dist);
    rd.setCameraMatrix(eye, fit.target, this.cfg.fov);
    if (this.mode === 'build' && this.stage >= 2 && this.name) {
      rd.queueTag('name', this.name, '#ffffff', null, [this.signAt[0], 6.2, this.signAt[2]], 1.3);
    }
    if (this.particles) this.particles.update(dt);
    rd.render();
    if (this.particles) this.particles.draw(rd);
    this.drawOverlay();
  };
  WP.sizeOverlay = function () {
    var w = this.host.clientWidth || 300, h = this.host.clientHeight || 300, dpr = Math.min(2, global.devicePixelRatio || 1);
    if (this.cssW !== w || this.cssH !== h || this.dpr !== dpr) {
      this.cssW = w; this.cssH = h; this.dpr = dpr;
      this.overlay.width = Math.round(w * dpr);
      this.overlay.height = Math.round(h * dpr);
      this.fit = null;
    }
  };

  WP.drawKids = function (parts, dt) {
    for (var i = 0; i < this.kids.length; i++) {
      var k = this.kids[i];
      if (!k.visible) continue;
      var pose = this.kidPose(k, dt);
      var pop = k.pop === undefined ? 1 : k.pop;
      if (pop <= 0.01) continue;
      var built = Avatar.build(k.desc, { position: [k.x, k.y + k.jy, k.z], yaw: k.yaw, time: this.t + k.seed, pose: pose });
      if (pop < 0.999) {
        for (var j = 0; j < built.length; j++) {
          var q = built[j];
          q.p = [k.x + (q.p[0] - k.x) * pop, k.y + (q.p[1] - k.y) * pop, k.z + (q.p[2] - k.z) * pop];
          q.s = [q.s[0] * pop, q.s[1] * pop, q.s[2] * pop];
        }
      }
      for (var b = 0; b < built.length; b++) parts.push(built[b]);
      // a little shadow
      parts.push({ t: 'cyl', p: [k.x, 0.32 + (k.y > 0.3 ? k.y - (k.act === 'tramp' ? 0 : k.y) : 0), k.z], s: [2.6 * pop, 0.05, 1.8 * pop], c: '#20262e', a: 0.22 });
      this.drawHeld(parts, k);
    }
  };
  /* what a kid has in their hands, and what they're working on */
  WP.drawHeld = function (parts, k) {
    var B = new Builder(parts, 1), s = k.spot;
    var hand = this.handPoint(k);
    if (k.hold === 'cup' && !k.act) {
      parts.push({ t: 'cyl', p: [hand[0], hand[1] + 0.2, hand[2]], s: [0.55, 0.85, 0.55], c: '#ffe066' });
    }
    if (!s || !k.act || k.path) return;
    if (k.act === 'fish') {
      var bob = [s.bob[0] * this.mir, 0.42 + Math.sin(this.t * 3 + k.seed) * 0.08, s.bob[1]];
      var tip = [hand[0] + (bob[0] - hand[0]) * 0.55, hand[1] + 2.6, hand[2] + (bob[2] - hand[2]) * 0.55];
      this.stick(parts, hand, tip, 0.14, '#6b4226');
      this.stick(parts, tip, bob, 0.05, '#e9eef3');
      parts.push({ t: 'sph', p: bob, s: [0.45, 0.45, 0.45], c: '#e23b3b' });
    } else if (k.act === 'build') {
      var plate = [s.plate[0] * this.mir, 0.85, s.plate[1]];
      var side = this.spots.indexOf(s) % 2 ? 0.8 : -0.8;
      for (var b = 0; b < k.bricks; b++) {
        B.at(plate[0] + side * this.mir, plate[1] + b * 0.6, plate[2] + 0.5, (b % 2) * Math.PI / 2);
        B.box(0, 0, 0, 1.2, 0.6, 0.6, BLOCKS[(b + k.id) % BLOCKS.length], { st: 1 });
      }
    } else if (k.act === 'catch' && this.spots.indexOf(s) < this.spots.indexOf(s.pair)) {
      // one ball per pair, drawn by the first of the two
      var other = s.pair.user;
      if (other && !other.path && other.act === 'catch') {
        var period = 1.6, u = (this.t % (period * 2)) / period, fromA = u < 1, f = u % 1;
        var ha = this.handPoint(k), hb = this.handPoint(other);
        var a = fromA ? ha : hb, c = fromA ? hb : ha;
        parts.push({ t: 'sph', p: [lerp(a[0], c[0], f), lerp(a[1], c[1], f) + Math.sin(f * Math.PI) * 4.6, lerp(a[2], c[2], f)],
                     s: [0.9, 0.9, 0.9], c: '#e23b3b' });
      }
    } else if (k.act === 'kite') {
      var out = [Math.sin(k.yaw), Math.cos(k.yaw)];
      var kite = [k.x + out[0] * 11 + Math.sin(this.t * 0.9) * 1.6, 14 + Math.sin(this.t * 1.3) * 1.4, k.z + out[1] * 11];
      parts.push({ t: 'box', p: kite, s: [2.6, 2.6, 0.2], r: [0.3, k.yaw, Math.PI / 4 + Math.sin(this.t * 2) * 0.15], c: '#e23b3b' });
      parts.push({ t: 'box', p: [kite[0], kite[1], kite[2] - 0.05], s: [0.15, 3.4, 0.25], r: [0.3, k.yaw, 0], c: '#f5cd30' });
      var prev = hand;
      for (var q = 1; q <= 6; q++) {
        var f2 = q / 6, sag = Math.sin(f2 * Math.PI) * 1.6;
        var pt = [lerp(hand[0], kite[0], f2), lerp(hand[1], kite[1], f2) - sag, lerp(hand[2], kite[2], f2)];
        this.stick(parts, prev, pt, 0.06, '#f2f3f3');
        prev = pt;
      }
      for (var tl = 0; tl < 4; tl++) {
        parts.push({ t: 'box', p: [kite[0], kite[1] - 1.8 - tl * 0.9, kite[2]], s: [0.5, 0.3, 0.1], r: [0, k.yaw, Math.sin(this.t * 3 + tl) * 0.6], c: tl % 2 ? '#f5cd30' : '#0d69ac' });
      }
    } else if (k.act === 'fire') {
      var fire = [s.fire[0] * this.mir, 1.4, s.fire[1]];
      var tipF = [lerp(hand[0], fire[0], 0.72), 1.9, lerp(hand[2], fire[2], 0.72)];
      this.stick(parts, hand, tipF, 0.1, '#7a4e2c');
      parts.push({ t: 'sph', p: tipF, s: [0.5, 0.6, 0.5], c: '#fff8ec' });
    } else if (k.act === 'wish') {
      var ph = k.actT % 2.6;
      if (ph > 0.45 && ph < 1.25) {
        var f = (ph - 0.45) / 0.8, to = this.coinTarget(k);
        parts.push({ t: 'cyl', p: [lerp(hand[0], to[0], f), lerp(hand[1], to[1], f) + Math.sin(f * Math.PI) * 2.6, lerp(hand[2], to[2], f)],
                     s: [0.55, 0.12, 0.55], r: [this.t * 13, k.yaw, 0], c: '#f5cd30', m: 'metal' });
      }
    } else if (k.act === 'sand') {
      var lx = Math.cos(k.yaw), lz = -Math.sin(k.yaw), fx = Math.sin(k.yaw), fz = Math.cos(k.yaw);
      parts.push({ t: 'cyl', p: [k.x + lx * 1.6 + fx * 0.6, 1.5, k.z + lz * 1.6 + fz * 0.6], s: [0.95, 1.0, 0.95], c: '#e23b3b' });
      this.stick(parts, hand, [hand[0] + fx * 1.1, hand[1] - 1.3, hand[2] + fz * 1.1], 0.14, '#2b67f6');
    }
  };
  WP.handPoint = function (k) {
    var y = k.yaw, fx = Math.sin(y), fz = Math.cos(y), rx = Math.cos(y), rz = -Math.sin(y);
    var up = k.state === 'sit' ? 2.6 : 2.9;
    return [k.x + fx * 1.3 - rx * 1.0, k.y + k.jy + up, k.z + fz * 1.3 - rz * 1.0];
  };
  /* a thin rod from a to b (a fishing line, a kite string, a chain) */
  WP.stick = function (parts, a, b, w, c) {
    var dx = b[0] - a[0], dy = b[1] - a[1], dz = b[2] - a[2], len = Math.sqrt(dx * dx + dy * dy + dz * dz);
    if (len < 0.01) return;
    var yaw = Math.atan2(dx, dz), pitch = Math.atan2(Math.sqrt(dx * dx + dz * dz), dy);
    parts.push({ t: 'box', p: [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2], s: [w, len, w], r: [pitch, yaw, 0], c: c });
  };

  /* things that move and aren't kids */
  WP.drawDynamic = function (B) {
    var t = this.t, mir = this.mir, night = this.night > 0.5;
    if (this.cfg.town) {
      // swings
      for (var i = 0; i < this.spots.length; i++) {
        var s = this.spots[i];
        if (s.kind === 'swing') {
          var th = s.user && s.user.act === 'swing' && !s.user.path ? Math.sin(t * 2.1 + s.phase) * 0.62 : Math.sin(t * 0.7 + s.phase) * 0.05;
          var L = s.pivot - s.seat;
          var seat = [s.x, s.pivot - Math.cos(th) * L, s.z + Math.sin(th) * L];
          B.parts.push({ t: 'box', p: seat, s: [1.9, 0.25, 1.1], r: [th, 0, 0], c: '#2a2d33' });
          this.stick(B.parts, [s.x - 0.85, s.pivot, s.z], [seat[0] - 0.85, seat[1], seat[2]], 0.1, METAL);
          this.stick(B.parts, [s.x + 0.85, s.pivot, s.z], [seat[0] + 0.85, seat[1], seat[2]], 0.1, METAL);
        }
      }
      // the seesaw plank
      var a = this.spots.filter(function (q) { return q.kind === 'seesaw'; });
      if (a.length === 2) {
        var busyA = a[0].user && !a[0].user.path && a[0].user.act === 'seesaw', busyB = a[1].user && !a[1].user.path && a[1].user.act === 'seesaw';
        var tilt = busyA && busyB ? Math.sin(t * 1.8) * 0.3 : (busyA ? 0.3 : (busyB ? -0.3 : 0.3));
        var cx = a[0].cx * mir;
        B.parts.push({ t: 'box', p: [cx, 1.65, a[0].z], s: [a[0].len + 1.2, 0.35, 1.2], r: [0, 0, tilt * mir], c: '#0d69ac' });
        B.parts.push({ t: 'box', p: [cx - Math.cos(tilt) * 4.2 * mir, 1.65 + Math.sin(tilt * mir) * -4.2 * mir + 0.7, a[0].z], s: [0.25, 1.2, 1.0], r: [0, 0, tilt * mir], c: '#f5cd30' });
      }
      // the flame and its glow
      var fx = this.place.fire[0] * mir, fz = this.place.fire[1];
      for (var f = 0; f < 3; f++) {
        var h = 2.0 + Math.sin(t * 9 + f * 2.1) * 0.4;
        B.parts.push({ t: 'cone', p: [fx + (f - 1) * 0.5, 0.6 + h / 2, fz + (f % 2 ? 0.4 : -0.3)], s: [1.5 - f * 0.25, h, 1.5 - f * 0.25],
                       c: f === 1 ? '#ffd23f' : '#ff7a1e', m: 'neon' });
      }
      if (this.particles && Math.random() < 0.35) {
        this.particles.spawn({ p: [fx, 2.4, fz], v: [(Math.random() - 0.5) * 1.6, 4 + Math.random() * 2, (Math.random() - 0.5) * 1.6],
          life: 0.8 + Math.random() * 0.6, size: 0.25, grow: -0.2, gravity: 1, spin: 4, blend: 'add', shape: 'spark', colors: ['#ffd36a', '#ff7a1a'] });
      }
      // the fountain's spray
      if (this.particles && Math.random() < 0.8) {
        var ang = Math.random() * TAU;
        this.particles.spawn({ p: [0, 7.2, 0], v: [Math.sin(ang) * 2.0, 6 + Math.random() * 2, Math.cos(ang) * 2.0],
          life: 0.95, size: 0.32, grow: -0.1, gravity: -16, spin: 0, blend: 'normal', shape: 'puff', colors: ['#cfeaff', '#8fc8f5'] });
      }
      // and the bowl spills over its rim into the basin
      if (this.particles && Math.random() < 0.6) {
        var ra = Math.random() * TAU;
        this.particles.spawn({ p: [Math.sin(ra) * 2.25, 4.95, Math.cos(ra) * 2.25], v: [Math.sin(ra) * 0.8, 0, Math.cos(ra) * 0.8],
          life: 0.5, size: 0.26, grow: -0.1, gravity: -14, spin: 0, blend: 'normal', shape: 'puff', colors: ['#d8efff', '#9fd0f7'] });
      }
      // the waterfall: a sheet of water off the edge, and mist below
      if (this.fall) {
        var wf = this.fall;
        B.parts.push({ t: 'box', p: [wf.x * mir, -12.5, wf.z], s: [3.4, 25, 0.5], r: [0, wf.yaw * mir, 0], c: '#7cc0f5', a: 0.72, m: 'glass' });
        for (var st = 0; st < 3; st++) {
          var yy = -((t * 22 + st * 8.3) % 25);
          B.parts.push({ t: 'box', p: [wf.x * mir, yy, wf.z], s: [3.5, 1.2, 0.56], r: [0, wf.yaw * mir, 0], c: '#e8f6ff', a: 0.55 });
        }
        if (this.particles && Math.random() < 0.5) {
          this.particles.spawn({ p: [wf.x * mir + (Math.random() - 0.5) * 3, -25, wf.z], v: [(Math.random() - 0.5) * 3, 1.2, (Math.random() - 0.5) * 3],
            life: 1.4, size: 1.6, grow: 1.2, gravity: 0.3, blend: 'normal', shape: 'puff', colors: ['#f2f9ff', '#d6ecfb'] });
        }
      }
      // the lighthouse lamp turns, after dark
      if (this.look.back === 'lighthouse' && this.night > 0.3) {
        var ly = this.lampTop || 18, lx = this.place.back[0] * mir, lz = this.place.back[1] - 0.4, ba = t * 1.2;
        B.parts.push({ t: 'cone', p: [lx + Math.sin(ba) * 7, ly, lz + Math.cos(ba) * 7], s: [3.6, 14, 3.6], r: [Math.PI / 2, ba, 0], c: '#fff3b0', a: 0.18 * this.night, m: 'neon' });
      }
      this.drawCars(B);
      this.drawCritters(B);
    }
    if (this.mode === 'build') this.drawBuild(B);
    if (this.mode === 'mini') this.drawMiniThings(B);
    this.drawThings(B);
  };

  /* ------------------------------------------------------- the traffic
     Two cars go round the square, one each way -- the inner lanes one way,
     the outer lanes the other -- so they never meet.  Each looks a few car
     lengths ahead along its lane and stops for anyone on the road there (a
     kid on a zebra, or the dog); and kids wait at the curb while a car is
     on a crossing or nearly there. */
  WP.loopPath = function (h, rho, reverse) {
    var pts = [], step = 0.5, m = h - rho;
    function seg(x0, z0, x1, z1) {
      var n = Math.max(1, Math.round(dist2(x0, z0, x1, z1) / step));
      for (var i = 0; i < n; i++) pts.push({ ux: lerp(x0, x1, i / n), z: lerp(z0, z1, i / n), arc: false });
    }
    function arc(cx, cz, a0) {
      var n = Math.max(4, Math.round(rho * Math.PI / 2 / step));
      for (var i = 0; i < n; i++) {
        var a = a0 + (i / n) * Math.PI / 2;
        pts.push({ ux: cx + Math.cos(a) * rho, z: cz + Math.sin(a) * rho, arc: true });
      }
    }
    seg(h, -m, h, m); arc(m, m, 0);
    seg(m, h, -m, h); arc(-m, m, Math.PI / 2);
    seg(-h, m, -h, -m); arc(-m, -m, Math.PI);
    seg(-m, -h, m, -h); arc(m, -m, Math.PI * 1.5);
    if (reverse) pts.reverse();
    var s = 0;
    for (var i = 0; i < pts.length; i++) {
      var p = pts[i], q = pts[(i + 1) % pts.length];
      p.x = p.ux * this.mir;
      p.s = s;
      s += dist2(p.ux, p.z, q.ux, q.z);
    }
    return { pts: pts, len: s };
  };
  WP.loopAt = function (loop, s) {
    var L = loop.len, pts = loop.pts, lo = 0, hi = pts.length - 1;
    s = ((s % L) + L) % L;
    while (lo < hi) {
      var mid = (lo + hi + 1) >> 1;
      if (pts[mid].s <= s) lo = mid; else hi = mid - 1;
    }
    var p = pts[lo], q = pts[(lo + 1) % pts.length], len = (lo + 1 < pts.length ? q.s : L) - p.s;
    var t = len > 0 ? (s - p.s) / len : 0;
    return { x: lerp(p.x, q.x, t), z: lerp(p.z, q.z, t), arc: p.arc };
  };
  /* where along each loop a car is over each zebra */
  WP.lapCrossings = function () {
    for (var c = 0; c < this.cross.length; c++) {
      var cr = this.cross[c];
      cr.laps = [];
      for (var li = 0; li < this.loops.length; li++) {
        var pts = this.loops[li].pts, L = this.loops[li].len, n = pts.length, start = -1, run = -1, q, e;
        var inside = function (p) { return Math.abs(p.x - cr.x) <= cr.hx + 2.6 && Math.abs(p.z - cr.z) <= cr.hz + 2.6; };
        for (q = 0; q < n; q++) if (!inside(pts[q])) { start = q; break; }
        if (start < 0) continue;
        for (e = 1; e <= n; e++) {
          var idx = (start + e) % n, inn = inside(pts[idx]);
          if (inn && run < 0) run = idx;
          if (!inn && run >= 0) {
            cr.laps.push({ loop: li, s0: pts[run].s, len: ((pts[idx].s - pts[run].s) % L + L) % L });
            run = -1;
          }
        }
      }
    }
  };
  /* may a kid at the curb step onto this zebra now? */
  WP.mayCross = function (cr) {
    if (!this.cars) return true;
    for (var i = 0; i < this.cars.length; i++) {
      var car = this.cars[i], L = this.loops[car.loop].len;
      for (var j = 0; j < cr.laps.length; j++) {
        var lap = cr.laps[j];
        if (lap.loop !== car.loop) continue;
        var into = ((lap.s0 - car.s) % L + L) % L, past = ((car.s - lap.s0) % L + L) % L;
        if (past < lap.len + 3.0) return false;               // it's on the crossing
        if (into < 3.8 + car.v * 2.1) return false;            // or about to be
      }
    }
    return true;
  };
  /* is (x, z) out on a road (not the sidewalk)? */
  WP.onRoad = function (x, z, grow) {
    var T = this.town;
    if (!T) return false;
    var g = grow === undefined ? -0.2 : grow, ux = Math.abs(x), az = Math.abs(z), w = TOWN.road + g;
    if (Math.abs(ux - T.D) < w && az < T.zEnd) return true;
    return Math.abs(az - T.D) < w && ux < T.D - TOWN.road - g;
  };
  WP.stepCars = function (dt) {
    if (!this.loops) return;
    var i, j, q, T = this.town;
    if (!this.cars) {
      var cols = shuffle(mulberry(this.seed + 61), CARS.filter(function (c) { return c !== this.look.car; }, this));
      this.cars = [{ loop: 0, s: 0, v: 0, colour: this.look.car }, { loop: 1, s: this.loops[1].len * 0.5, v: 0, colour: cols[0] }];
      for (i = 0; i < this.cars.length; i++) this.placeCar(this.cars[i]);
      // the four junctions round the square: one car in each at a time
      this.junctions = [];
      for (var a = -1; a <= 1; a += 2) for (var b = -1; b <= 1; b += 2) this.junctions.push({ x: a * T.D, z: b * T.D, owner: -1 });
    }
    for (i = 0; i < this.cars.length; i++) {
      var car = this.cars[i], loop = this.loops[car.loop], block = 1e9;
      // anyone on the road ahead (not only in this lane: a kid crossing comes this way)
      for (var d = 0.5; d <= 14 && block > 1e8; d += 0.75) {
        var p = this.loopAt(loop, car.s + d);
        for (j = 0; j <= this.kids.length; j++) {
          var w = j < this.kids.length ? this.kids[j] : this.dog;
          if (!w || w.visible === false || w.waiting) continue;
          if (dist2(w.x, w.z, p.x, p.z) < 4.2 && this.onRoad(w.x, w.z, 0.35)) { block = d; break; }
        }
      }
      // the next junction: take it if it's free, else wait short of it
      var next = -1, nd = 1e9;
      for (var d2 = 0; d2 <= 11 && next < 0; d2 += 0.5) {
        var pj = this.loopAt(loop, car.s + d2);
        for (q = 0; q < this.junctions.length; q++) {
          var J = this.junctions[q];
          if (Math.abs(pj.x - J.x) < 4.5 && Math.abs(pj.z - J.z) < 4.5) { next = q; nd = d2; break; }
        }
      }
      for (q = 0; q < this.junctions.length; q++) {
        var Jq = this.junctions[q];
        if (Jq.owner === i && q !== next && (Math.abs(car.x - Jq.x) > 6.7 || Math.abs(car.z - Jq.z) > 6.7)) Jq.owner = -1;
      }
      if (next >= 0) {
        var Jn = this.junctions[next];
        if (Jn.owner < 0) Jn.owner = i;
        else if (Jn.owner !== i) block = Math.min(block, nd - 0.8);   // its nose stops short of the zebra
      }
      var vmax = (this.loopAt(loop, car.s).arc || this.loopAt(loop, car.s + 3.5).arc) ? 4.4 : 8.5;
      var want = block < 1e8 ? clamp((block - 4.6) * 1.9, 0, vmax) : vmax;
      car.v = Math.max(0, car.v + clamp(want - car.v, -dt * 26, dt * 5));
      car.s = (car.s + car.v * dt) % loop.len;
      this.placeCar(car);
    }
  };
  /* the body sits on the lane; it points along the chord between its axles */
  WP.placeCar = function (car) {
    var loop = this.loops[car.loop], at = this.loopAt(loop, car.s);
    var f = this.loopAt(loop, car.s + 1.6), b = this.loopAt(loop, car.s - 1.6);
    car.x = at.x; car.z = at.z; car.yaw = Math.atan2(f.x - b.x, f.z - b.z);
  };
  WP.drawCars = function (B) {
    if (!this.cars) return;
    var lit = this.night > 0.4;
    B.mir = 1;
    for (var i = 0; i < this.cars.length; i++) carModel(B, this.cars[i].x, this.cars[i].z, this.cars[i].yaw, this.cars[i].colour, lit);
  };

  /* ------------------------------------------------ dog, cat and ducks
     The dog trots the sidewalks like everyone else -- after a kid now and
     then -- and waits at the curb for the cars; the ducks paddle round the
     pond, clear of the dock; the cat sleeps on the roof. */
  WP.stepCritters = function (dt) {
    var r = Math.random;
    if (!this.dog) {
      var dr = mulberry(this.seed + 5), start = this.nodes.length ? this.nodes[Math.floor(dr() * this.nodes.length)] : { x: 7, z: 9 };
      this.dog = { x: start.x, z: start.z, yaw: 0, want: 0, path: null, wait: 1, wag: 0, jy: 0, vy: 0, isDog: true, state: 'idle',
                   colour: pick(dr, ['#c08a4d', '#f2f3f3', '#3a2c22', '#d9b779']) };
      this.ducks = [];
      for (var d = 0; d < 3; d++) this.ducks.push({ a: d * 2.1, r: 1.4 + d * 0.85, s: 0.3 + d * 0.06 });
    }
    var dog = this.dog;
    dog.wag += dt * 14;
    if (dog.vy || dog.jy > 0) { dog.vy -= 50 * dt; dog.jy += dog.vy * dt; if (dog.jy <= 0) { dog.jy = 0; dog.vy = 0; } }
    if (dog.path) {
      var got = this.advance(dog, dt, 8);
      dog.moving = got === 'moving';
      if (got === 'arrived') { dog.path = null; dog.wait = 1.2 + r() * 2.5; if (r() < 0.25) dog.vy = 10; }
      else if (got === 'moving' && dog.path[0]) {
        var dd = dist2(dog.x, dog.z, dog.path[0].x, dog.path[0].z);
        if (dog.stallD === undefined || dd < dog.stallD - 0.25) { dog.stallD = dd; dog.stall = 0; }
        else if ((dog.stall = (dog.stall || 0) + dt) > 2.5) { dog.path = null; dog.wait = 0.8; dog.stallD = undefined; }
      }
    } else {
      dog.moving = false;
      dog.wait -= dt;
      if (dog.wait <= 0 && this.nodes.length) {
        var walkers = this.kids.filter(function (k) { return k.path && k.visible; }), to;
        if (walkers.length && r() < 0.55) { var kw = walkers[Math.floor(r() * walkers.length)]; to = this.nearestNode(kw.x, kw.z); }
        else to = Math.floor(r() * this.nodes.length);
        var ids = this.route(this.accessNode(dog.x, dog.z, null), to);
        if (ids && ids.length > 1) { dog.path = this.lanePath(ids, TOWN.keep); dog.stall = 0; dog.stallD = undefined; }
        dog.wait = 1.5;
      }
    }
    for (var q = 0; q < this.ducks.length; q++) this.ducks[q].a += dt * this.ducks[q].s;
  };
  WP.drawCritters = function (B) {
    var dog = this.dog;
    if (!dog) return;
    var c = dog.colour, t = this.t;
    B.at(dog.x, dog.jy, dog.z, dog.yaw);
    B.mir = 1;
    var step = dog.moving ? Math.sin(t * 16) * 0.35 : 0;
    B.box(0, 1.0, 0, 1.3, 1.1, 2.6, c);
    B.box(0, 1.6, 1.5, 1.2, 1.1, 1.2, c);
    B.box(0, 1.55, 2.25, 0.7, 0.55, 0.5, shade(c, 0.25));
    B.add('sph', 0, 1.85, 2.5, 0.35, 0.3, 0.3, '#1b1b1b');
    B.box(-0.5, 2.5, 1.3, 0.3, 0.6, 0.4, shade(c, -0.3));
    B.box(0.5, 2.5, 1.3, 0.3, 0.6, 0.4, shade(c, -0.3));
    B.add('sph', -0.3, 1.95, 2.12, 0.18, 0.18, 0.1, '#1b1b1b');
    B.add('sph', 0.3, 1.95, 2.12, 0.18, 0.18, 0.1, '#1b1b1b');
    B.add('box', 0, 1.9, -1.45, 0.25, 0.25, 1.0, c, { r: [-0.7, Math.sin(dog.wag) * 0.6, 0] });
    var legs = [[-0.45, 0.9, step], [0.45, 0.9, -step], [-0.45, -0.9, -step], [0.45, -0.9, step]];
    for (var i = 0; i < legs.length; i++) B.add('box', legs[i][0], 0.45, legs[i][1], 0.35, 0.9, 0.35, shade(c, -0.12), { r: [legs[i][2], 0, 0] });
    // ducks paddle round the pond, on the far side from the dock
    var dc = this.place.ducks || this.place.pond, px = dc[0] * this.mir, pz = dc[1];
    for (var q = 0; q < this.ducks.length; q++) {
      var dk = this.ducks[q], x = px + Math.sin(dk.a) * dk.r, z = pz + Math.cos(dk.a) * dk.r;
      B.at(x, 0.35 + Math.sin(t * 3 + q) * 0.05, z, dk.a + Math.PI / 2);
      B.add('sph', 0, 0.5, 0, 1.0, 0.7, 1.4, q === 0 ? '#f2f3f3' : '#f5cd30');
      B.add('sph', 0, 1.1, 0.5, 0.65, 0.65, 0.65, q === 0 ? '#2e7d4f' : '#f5cd30');
      B.box(0, 0.9, 0.95, 0.35, 0.18, 0.45, '#ff8a1e');
    }
    // and a cat asleep on the roof, wherever the house faces
    var H = this.place.house, hy = this.houseYaw || 0, cb = new Builder([], this.mir);
    cb.at(H[0], 0, H[1], hy);
    var cp = cb.point(-2.8, 10.7, 1.4);
    B.at(cp[0], cp[1], cp[2], hy * this.mir + 0.3);
    B.add('sph', 0, 0.45, 0, 1.6, 0.8, 1.0, '#ef9a3c');
    B.add('sph', 0.75, 0.75, 0.05, 0.75, 0.7, 0.7, '#ef9a3c');
    B.box(0.6, 1.1, 0.05, 0.18, 0.3, 0.18, '#ef9a3c');
    B.box(0.95, 1.1, 0.05, 0.18, 0.3, 0.18, '#ef9a3c');
    B.add('box', -0.9, 0.5, 0.2, 0.2, 0.2, 1.2, '#ef9a3c', { r: [0, 0.6 + Math.sin(t * 1.5) * 0.4, 0] });
  };

  /* --------------------------------------------- the glass and its ripples */
  WP.drawDome = function () {
    var rd = this.renderer, k = this.domeK;
    if (k <= 0.01) return;
    var Rd = this.domeR() * (0.6 + 0.4 * backOut(k)), H = Rd * 0.92 * smooth(k);
    // the glass: nearly clear face on, bright at its edges (the engine's
    // glass adds a fresnel rim), sitting on the island
    rd.pushRaw('hemi', 0, 0.1 + H / 2, 0, 0, 0, 0, Rd * 2, H, Rd * 2, rgbf('#e6f5ff'), 0.03 + 0.05 * this.badgeHit, 0, 3, 0, null);
    // a glowing rim where it meets the ground, and a band higher up
    this.ring(rd, 0.35, Rd, 0.55, 0.32, '#6cc3ff', 0.9 * k);
    this.ring(rd, H * Math.sin(0.62), Rd * Math.cos(0.62), 0.18, 0.18, '#d6f0ff', 0.12 * k);
    for (var i = this.ripples.length - 1; i >= 0; i--) {
      var rp = this.ripples[i], u = rp.t / rp.life;
      var size = 1.5 + u * 9;
      rd.pushRaw('torus', rp.p[0], rp.p[1], rp.p[2], rp.phi, rp.az, 0, size, size, size, rgbf(rp.colour || '#8fd8ff'), 0.85 * (1 - u), 0, 2, 0.6, null);
    }
  };
  /* a thin glowing circle, from short segments (the engine's torus is a
     fat one at any size this big) */
  WP.ring = function (rd, y, radius, w, h, colour, alpha) {
    var n = 44, c = rgbf(colour), len = TAU * radius / n * 1.08;
    for (var i = 0; i < n; i++) {
      var a = (i + 0.5) / n * TAU;
      rd.pushRaw('box', Math.sin(a) * radius, y, Math.cos(a) * radius, 0, a, 0, len, h, w, c, alpha, 0, 2, 0.7, null);
    }
  };
  WP.domePoint = function (az, phi) {
    var Rd = this.domeR(), H = Rd * 0.92;
    var x = Math.sin(az) * Math.cos(phi) * Rd, z = Math.cos(az) * Math.cos(phi) * Rd, y = Math.sin(phi) * H;
    return [x, y, z];
  };
  WP.ripple = function (p, colour) {
    var Rd = this.domeR(), H = Rd * 0.92;
    var nx = p[0] / Rd, ny = p[1] / H, nz = p[2] / Rd, len = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
    nx /= len; ny /= len; nz /= len;
    this.ripples.push({ p: p, t: 0, life: 0.9, phi: Math.acos(clamp(ny, -1, 1)), az: Math.atan2(nx, nz), colour: colour });
    this.badgeHit = 0.7;
    if (this.particles) {
      for (var i = 0; i < 10; i++) {
        this.particles.spawn({ p: p, v: [nx * 6 + (Math.random() - 0.5) * 6, ny * 6 + (Math.random() - 0.5) * 6, nz * 6 + (Math.random() - 0.5) * 6],
          life: 0.5 + Math.random() * 0.3, size: 0.45, grow: -0.6, gravity: -6, blend: 'add', shape: 'spark', colors: ['#d8f2ff', '#7cc7ff'] });
      }
    }
  };

  /* ----------------------------------------- the things that come and go */
  WP.stepThings = function (dt) {
    var i;
    for (i = this.ripples.length - 1; i >= 0; i--) { this.ripples[i].t += dt; if (this.ripples[i].t > this.ripples[i].life) this.ripples.splice(i, 1); }
    for (i = this.flowers.length - 1; i >= 0; i--) { this.flowers[i].t += dt; if (this.flowers[i].t > 24) this.flowers.splice(i, 1); }
    for (i = this.hearts.length - 1; i >= 0; i--) { this.hearts[i].t += dt; if (this.hearts[i].t > 1.4) this.hearts.splice(i, 1); }
    for (i = this.notes.length - 1; i >= 0; i--) { this.notes[i].t += dt; if (this.notes[i].t > 2) this.notes.splice(i, 1); }
    var top = this.domeR() * 0.92;
    for (i = this.balloons.length - 1; i >= 0; i--) {
      var b = this.balloons[i];
      b.t += dt;
      b.y = Math.min(b.y + dt * b.v, top * Math.sqrt(Math.max(0, 1 - (b.x * b.x + b.z * b.z) / Math.pow(this.domeR(), 2))) - 1.8);
      b.x += Math.sin(this.t * 0.8 + b.s) * dt * 0.8;
      if (b.t > b.life) {
        if (this.particles) this.particles.burst('confetti', [b.x, b.y, b.z], { radius: 2.2 });
        this.balloons.splice(i, 1);
      }
    }
    for (i = this.lanterns.length - 1; i >= 0; i--) {
      var l = this.lanterns[i];
      l.t += dt; l.y += dt * 1.6; l.x += Math.sin(this.t + l.s) * dt * 0.5;
      if (l.t > l.life) this.lanterns.splice(i, 1);
    }
    for (i = this.bubbles.length - 1; i >= 0; i--) {
      var u = this.bubbles[i];
      u.t += dt; u.y += dt * u.v; u.x += Math.sin(this.t * 2 + u.s) * dt;
      if (u.t > u.life) { if (this.particles) this.particles.spawn({ p: [u.x, u.y, u.z], v: [0, 0, 0], life: 0.25, size: u.r * 1.4, grow: 2, gravity: 0, blend: 'add', shape: 'ring', colors: ['#e8f6ff'] }); this.bubbles.splice(i, 1); }
    }
    if (this.fish) { this.fish.t += dt; if (this.fish.t > 1.1) this.fish = null; }
    if (this.party > 0) {
      this.party -= dt;
      if (Math.random() < dt * 4) this.notes.push({ x: (Math.random() - 0.5) * 14, z: (Math.random() - 0.5) * 14, t: 0 });
      if (this.party <= 0) {
        for (var k = 0; k < this.kids.length; k++) {
          var pk = this.kids[k];
          if (pk.partySpot && pk.target === pk.partySpot) { pk.path = null; pk.target = null; pk.waiting = false; }
          pk.partySpot = null; pk.dancing = false; pk.idle = 0.5 + Math.random();
        }
      }
    }
    if (this.storm) this.stepStorm(dt);
    if (this.rainbow > 0) this.rainbow = Math.max(0, this.rainbow - dt / 9);
  };
  WP.drawThings = function (B) {
    var t = this.t, parts = B.parts, i;
    for (i = 0; i < this.flowers.length; i++) {
      var f = this.flowers[i], g = backOut(Math.min(1, f.t / 0.5)) * (f.t > 23 ? Math.max(0, 24 - f.t) : 1);
      parts.push({ t: 'cyl', p: [f.x, 0.6 * g, f.z], s: [0.2 * g, 1.2 * g, 0.2 * g], c: '#3d8f3d' });
      parts.push({ t: 'sph', p: [f.x, 1.3 * g, f.z], s: [0.95 * g, 0.7 * g, 0.95 * g], c: f.c });
    }
    for (i = 0; i < this.balloons.length; i++) {
      var b = this.balloons[i];
      parts.push({ t: 'sph', p: [b.x, b.y, b.z], s: [2.2, 2.6, 2.2], c: b.c });
      this.stick(parts, [b.x, b.y - 1.3, b.z], [b.x + Math.sin(t + b.s) * 0.4, b.y - 4.4, b.z], 0.06, '#f2f3f3');
    }
    for (i = 0; i < this.lanterns.length; i++) {
      var l = this.lanterns[i], fade = Math.min(1, l.t, (l.life - l.t) / 2);
      parts.push({ t: 'box', p: [l.x, l.y, l.z], s: [1.2, 1.5, 1.2], c: '#ffb347', m: 'neon', a: Math.max(0.05, fade) });
    }
    for (i = 0; i < this.bubbles.length; i++) {
      var u = this.bubbles[i];
      parts.push({ t: 'sph', p: [u.x, u.y, u.z], s: [u.r, u.r, u.r], c: '#e8f6ff', a: 0.32, m: 'glass' });
    }
    if (this.fish) {
      var fs = this.fish, q = fs.t / 1.1;
      parts.push({ t: 'box', p: [fs.x, 0.4 + Math.sin(q * Math.PI) * 3.2, fs.z + (q - 0.5) * 2.4], s: [0.5, 0.7, 1.4], r: [q * 3 - 1.5, 0, 0], c: '#ff8a1e' });
    }
    if (this.party > 0 && this.cfg.town) {
      // a disco ball over the plaza, and coloured beams
      var ds = Math.min(1, this.party / 1.5, (this.partyLen - this.party) / 1.5);
      parts.push({ t: 'sph', p: [0, 13, 0], s: [2.4 * ds, 2.4 * ds, 2.4 * ds], r: [0, t * 2, 0], c: '#dfe6ee', m: 'metal' });
      parts.push({ t: 'cyl', p: [0, 15.5, 0], s: [0.1, 5, 0.1], c: '#8d939c' });
      var cols = ['#ff5ad1', '#3cc8ff', '#7dff9a', '#ffd36a'];
      for (var c = 0; c < 4; c++) {
        var a = t * 1.4 + c * Math.PI / 2;
        parts.push({ t: 'cone', p: [Math.sin(a) * 3.6, 7.0, Math.cos(a) * 3.6], s: [4.2, 12, 4.2], r: [Math.sin(a * 0.7) * 0.4, a, 0], c: cols[c], a: 0.16 * ds, m: 'neon' });
      }
    }
    if (this.storm) this.drawStorm(parts);
    if (this.rainbow > 0) {
      var rk = Math.min(1, this.rainbow * 3), bands = ['#ff5a5f', '#ff9f1c', '#ffd23f', '#5cc95f', '#3c9df0', '#8a5cf6'];
      var back = this.camYaw + Math.PI, cx = Math.sin(back) * this.R * 0.55, cz = Math.cos(back) * this.R * 0.55;
      var ux = Math.cos(back), uz = -Math.sin(back);
      for (var bi = 0; bi < bands.length; bi++) {
        var rad = this.R * 1.05 - bi * 1.3;
        for (var sg = 0; sg < 22; sg++) {
          var aa = (sg + 0.5) / 22 * Math.PI, px = Math.cos(aa) * rad, py = Math.sin(aa) * rad;
          parts.push({ t: 'box', p: [cx + ux * px, py - 2, cz + uz * px], s: [rad * Math.PI / 22 * 1.1, 1.3, 0.4],
                       r: [0, back, aa + Math.PI / 2], c: bands[bi], a: 0.5 * rk, m: 'neon' });
        }
      }
    }
  };

  /* ------------------------------------------------------- the weather */
  WP.ambient = function (dt) {
    var P = this.particles;
    if (!P) return;
    var kind = this.S.fall, R = this.R, rate = this.mode === 'mini' ? 2 : 5;
    if (kind === 'firefly' && this.night < 0.3) kind = this.night > 0.1 ? 'firefly' : 'petalsun';
    if (Math.random() > dt * rate) return;
    var a = Math.random() * TAU, rr = Math.sqrt(Math.random()) * R * 0.9, x = Math.sin(a) * rr, z = Math.cos(a) * rr;
    if (kind === 'snow') {
      P.spawn({ p: [x, 22, z], v: [0.4, -3.2, 0.2], life: 6.5, size: 0.42, grow: 0, gravity: 0, spin: 1, blend: 'normal', shape: 'puff', colors: ['#ffffff', '#eef6ff'] });
    } else if (kind === 'leaf') {
      P.spawn({ p: [x, 16, z], v: [1.0, -2.2, 0.6], life: 6, size: 0.5, grow: 0, gravity: 0, spin: 3, blend: 'normal', shape: 'confetti', colors: ['#e8742a', '#d9442b', '#f2b630'] });
    } else if (kind === 'petal') {
      P.spawn({ p: [x, 16, z], v: [0.8, -1.8, 0.5], life: 7, size: 0.4, grow: 0, gravity: 0, spin: 3, blend: 'normal', shape: 'confetti', colors: ['#ffc1dc', '#ff9ec8', '#ffffff'] });
    } else if (kind === 'firefly') {
      P.spawn({ p: [x, 2 + Math.random() * 5, z], v: [(Math.random() - 0.5) * 1.2, 0.4, (Math.random() - 0.5) * 1.2], life: 3, size: 0.4, grow: -0.05, gravity: 0, blend: 'add', shape: 'spark', colors: ['#fff7a8', '#d8ff6a'] });
    }
  };

  /* ---------------------------------------------------------- events */
  WP.stepEvents = function (dt) {
    if (this.storm || this.party > 0) return;
    this.nextEvent -= dt;
    if (this.nextEvent > 0) return;
    var night = this.night > 0.5;
    var list = ['fireworks', 'balloons', 'party', 'bubbles', 'storm'];
    if (night || this.light === 'dusk') list.push('lanterns', 'fireworks');
    var e;
    do { e = list[Math.floor(Math.random() * list.length)]; } while (e === this.lastEvent && list.length > 1);
    this.lastEvent = e;
    this.event(e);
    this.nextEvent = 16 + Math.random() * 10;
  };
  WP.event = function (e) {
    var R = this.R, i, self = this;
    if (e === 'fireworks') {
      for (i = 0; i < 5; i++) (function (i) { setTimeout(function () { self.firework(); }, i * 420); })(i);
    } else if (e === 'balloons') {
      var cols = ['#e23b3b', '#f5cd30', '#2b67f6', '#2fb35a', '#ff66cc', '#ff8a1e'];
      for (i = 0; i < 7; i++) {
        var a = Math.random() * TAU, rr = Math.random() * 8;
        this.balloons.push({ x: Math.sin(a) * rr, y: 2, z: Math.cos(a) * rr, v: 3 + Math.random() * 2, c: cols[i % cols.length], t: 0, life: 9 + Math.random() * 4, s: Math.random() * 10 });
      }
      var kid = this.kids[Math.floor(Math.random() * this.kids.length)];
      if (kid) this.say(kid, 'balloons!!');
    } else if (e === 'lanterns') {
      for (i = 0; i < 8; i++) {
        var b = Math.random() * TAU, r2 = 4 + Math.random() * (R - 8);
        this.lanterns.push({ x: Math.sin(b) * r2, y: 1 + Math.random() * 3, z: Math.cos(b) * r2, t: -i * 0.5, life: 10, s: Math.random() * 10 });
      }
    } else if (e === 'bubbles') {
      for (i = 0; i < 16; i++) {
        this.bubbles.push({ x: (Math.random() - 0.5) * 10, y: 3 + Math.random() * 3, z: (Math.random() - 0.5) * 10, v: 1.6 + Math.random() * 1.6, r: 1 + Math.random() * 1.2, t: -i * 0.3, life: 6 + Math.random() * 3, s: Math.random() * 10 });
      }
    } else if (e === 'party') {
      this.party = this.partyLen = 11;
      for (i = 0; i < this.kids.length; i++) if (Math.random() < 0.5) this.say(this.kids[i], pick(Math.random, ['dance!', 'party!', 'woo!', '♪']));
    } else if (e === 'storm') {
      this.storm = { t: 0, life: 9, flashes: 0, flash: 0, told: false };
    }
  };
  WP.firework = function (at) {
    if (!this.particles) return;
    var Rd = this.domeR();
    var p = at || [(Math.random() - 0.5) * Rd * 1.4, Rd * (1.05 + Math.random() * 0.35), (Math.random() - 0.5) * Rd * 0.8];
    var cols = pick(Math.random, [['#ff5a5f', '#ffd36a'], ['#3cc8ff', '#ffffff'], ['#7dff9a', '#f5cd30'], ['#ff5ad1', '#b48cff'], ['#ffd36a', '#ff8a1e']]);
    for (var i = 0; i < 46; i++) {
      var a = Math.random() * TAU, e = Math.acos(2 * Math.random() - 1), sp = 9 + Math.random() * 6;
      this.particles.spawn({ p: p, v: [Math.sin(e) * Math.cos(a) * sp, Math.cos(e) * sp, Math.sin(e) * Math.sin(a) * sp],
        life: 1.1 + Math.random() * 0.5, size: 0.7, grow: -0.4, gravity: -7, spin: 0, blend: 'add', shape: 'spark', colors: cols });
    }
    this.particles.spawn({ p: p, v: [0, 0, 0], life: 0.35, size: 6, grow: 2, gravity: 0, blend: 'add', shape: 'ring', colors: [cols[1]] });
  };
  WP.sparkle = function (p, n) {
    if (!this.particles) return;
    for (var i = 0; i < (n || 12); i++) {
      this.particles.spawn({ p: [p[0] + (Math.random() - 0.5) * 2, p[1] + Math.random() * 2, p[2] + (Math.random() - 0.5) * 2],
        v: [(Math.random() - 0.5) * 3, 2 + Math.random() * 3, (Math.random() - 0.5) * 3], life: 0.8 + Math.random() * 0.5,
        size: 0.6, grow: -0.6, gravity: -2, blend: 'add', shape: 'star', colors: ['#fff3b0', '#ffd36a', '#ffffff'] });
    }
  };
  WP.fishJump = function (s) {
    this.fish = { x: s.bob[0] * this.mir + (Math.random() - 0.5) * 2, z: s.bob[1] + (Math.random() - 0.5) * 2, t: 0 };
    if (this.particles) this.particles.burst('impact', [this.fish.x, 0.5, this.fish.z], { color: '#bfe3ff' });
    if (s.user) { s.user.happy = 1.2; this.say(s.user, pick(Math.random, ['a fish!', 'whoa!', 'got one!'])); }
  };

  /* A storm outside: dark clouds round the dome, rain that runs off the
     glass, lightning that hits the shield -- and a rainbow after. */
  WP.stepStorm = function (dt) {
    var s = this.storm, P = this.particles, Rd = this.domeR(), H = Rd * 0.92;
    s.t += dt;
    var k = Math.min(1, s.t / 1.5, (s.life - s.t) / 1.5);
    s.k = Math.max(0, k);
    if (P && s.k > 0.2) {
      for (var i = 0; i < 6; i++) {
        var a = Math.random() * TAU, rr = Math.random() * Rd * 1.25, x = Math.sin(a) * rr, z = Math.cos(a) * rr;
        var inside = rr < Rd;
        var hitY = inside ? H * Math.sqrt(Math.max(0, 1 - (rr * rr) / (Rd * Rd))) : -14;
        var fall = 30;
        P.spawn({ p: [x, hitY + fall, z], v: [0, -fall / 0.6, 0], life: 0.6, size: 0.18, grow: 0, gravity: 0, blend: 'normal', shape: 'spark', colors: ['#cfe3f5', '#9fbfe0'] });
        if (inside && Math.random() < 0.35) P.spawn({ p: [x, hitY + 0.2, z], v: [0, 0.5, 0], life: 0.3, size: 0.7, grow: 1.6, gravity: 0, blend: 'normal', shape: 'ring', colors: ['#dff0ff'] });
      }
    }
    s.flash = Math.max(0, s.flash - dt * 3);
    if (s.t > 2 && s.t < s.life - 2 && Math.random() < dt * 0.6) {
      s.flash = 1;
      s.bolt = { az: this.camYaw + (Math.random() - 0.5) * 1.8, t: 0 };
      this.ripple(this.domePoint(s.bolt.az, 0.95 + Math.random() * 0.3), '#fff7c2');
      if (!s.told) {
        s.told = true;
        this.dispatch({ storm: true, title: 'A storm outside — sunny inside' });
      }
      var kid = this.kids[Math.floor(Math.random() * this.kids.length)];
      if (kid) this.say(kid, pick(Math.random, ['whoa!', 'cool!', 'we’re safe!']));
    }
    if (s.bolt) s.bolt.t += dt;
    if (s.t >= s.life) { this.storm = null; this.rainbow = 1; }
  };
  WP.drawStorm = function (parts) {
    var s = this.storm, Rd = this.domeR(), k = s.k || 0;
    if (k <= 0) return;
    for (var i = 0; i < 9; i++) {
      var a = i / 9 * TAU + this.t * 0.05, rr = Rd * (1.05 + (i % 3) * 0.12), y = Rd * (0.95 + (i % 2) * 0.18);
      parts.push({ t: 'sph', p: [Math.sin(a) * rr, y, Math.cos(a) * rr], s: [Rd * 0.7 * k, Rd * 0.28 * k, Rd * 0.5 * k], c: s.flash > 0.5 ? '#c9d2e0' : '#5d6675', a: 0.82 });
    }
    if (s.bolt && s.bolt.t < 0.3) {
      var p = this.domePoint(s.bolt.az, 1.0), top = [p[0] * 1.6, p[1] + 24, p[2] * 1.6];
      var prev = top;
      for (var j = 1; j <= 5; j++) {
        var f = j / 5, q = [lerp(top[0], p[0], f) + (Math.random() - 0.5) * 3, lerp(top[1], p[1], f), lerp(top[2], p[2], f) + (Math.random() - 0.5) * 3];
        if (j === 5) q = p;
        this.stick(parts, prev, q, 0.5, '#fff7c2');
        parts[parts.length - 1].m = 'neon';
        prev = q;
      }
    }
  };

  /* -------------------------------- the messages that fly at the dome */
  WP.stepThreats = function (dt) {
    this.nextThreat -= dt;
    if (this.nextThreat <= 0) {
      this.nextThreat = this.cfg.threats * (0.8 + Math.random() * 0.5);
      this.launch();
    }
    for (var i = this.threats.length - 1; i >= 0; i--) {
      var th = this.threats[i];
      th.t += dt / 1.15;
      if (th.t >= 1 && !th.hit) {
        th.hit = true;
        this.ripple(th.p);
        this.dispatch({ icon: th.spec.icon, what: th.spec.what, title: th.spec.title });
        var near = this.kids[Math.floor(Math.random() * this.kids.length)];
        if (near && Math.random() < 0.4) this.say(near, pick(Math.random, ['nope!', 'blocked!', 'lol bye']));
      }
      if (th.t > 1.7) this.threats.splice(i, 1);
    }
  };
  WP.launch = function () {
    var side = Math.random() < 0.5 ? -1 : 1;
    var az = this.camYaw + side * (0.9 + Math.random() * 0.5), phi = 0.35 + Math.random() * 0.55;
    var spec = THREATS[Math.floor(Math.random() * THREATS.length)];
    this.threats.push({ spec: spec, p: this.domePoint(az, phi), side: side, t: 0, hit: false, y0: 0.15 + Math.random() * 0.5 });
  };
  WP.dispatch = function (detail) {
    var host = this.host;
    try { host.dispatchEvent(new CustomEvent('haven:blocked', { detail: detail, bubbles: true })); } catch (e) { /* old browser */ }
  };

  /* ------------------------------------- the comparison card's little script */
  WP.stepMini = function (dt) {
    var m = this.mini || (this.mini = { t: 0, list: [], step: 0, approve: 0, prev: 0 });
    var cyc = 10.5, script = [[0.5, 'bad', 0], [2.6, 'bad', 1], [4.6, 'bad', 2], [6.4, 'good', 0]];
    m.t += dt;
    var lt = m.t % cyc;
    if (lt < m.prev) { m.step = 0; m.approve = 0; }
    m.prev = lt;
    var texts = [this.host.getAttribute('data-bad-1') || 'hey how old r u?', this.host.getAttribute('data-bad-2') || 'add me on my other app',
                 this.host.getAttribute('data-bad-3') || 'what school do u go to?'];
    while (m.step < script.length && lt >= script[m.step][0]) {
      var sc = script[m.step++], good = sc[1] === 'good';
      var side = sc[2] % 2 === 0 ? -1 : 1;
      var az = this.camYaw + side * (1.0 + Math.random() * 0.3), phi = 0.4 + Math.random() * 0.4;
      m.list.push({ text: good ? (this.host.getAttribute('data-good') || 'gg! wanna team up?') : texts[sc[2] % texts.length],
                    good: good, p: this.domePoint(good ? this.camYaw + 0.6 : az, good ? 0.5 : phi), side: good ? 1 : side, t: 0, hit: false });
    }
    if (lt > 8.1 && !m.approve) m.approve = m.t;
    for (var i = m.list.length - 1; i >= 0; i--) {
      var b = m.list[i];
      b.t += dt / (b.good ? 1.6 : 1.1);
      if (!b.good && b.t >= 1 && !b.hit) { b.hit = true; this.ripple(b.p); }
      if (b.good && b.t >= 1.55 && !b.hit) {
        b.hit = true;
        var k = this.kids[0];
        if (k) { k.happy = 1.6; k.vy = 14; this.heart(k); }
      }
      if (b.t > (b.good ? 2.6 : 1.6)) m.list.splice(i, 1);
    }
  };
  WP.drawMiniThings = function () { /* the house and the tree are static; the kid draws itself */ };
  WP.heart = function (k) {
    for (var i = 0; i < 3; i++) this.hearts.push({ x: k.x, y: 6.6 + i * 0.3, z: k.z, t: -i * 0.18, dx: (i - 1) * 14 });
  };

  /* ---------------------------------------------------------- build mode */
  WP.stepBuild = function (dt) {
    var target = this.stage >= 5 ? 1 : 0;
    this.domeK = target ? Math.min(1, this.domeK + dt / 1.6) : Math.max(0, this.domeK - dt * 2.5);
    if (!this.child) {
      var r = mulberry(this.seed + 41);
      this.child = this.makeKid(r, { x: 4.5, z: 6.5, yaw: 0.4, visible: false, plain: true, face: 'face_smile' });
      this.child.visible = false;
      this.kids.push(this.child);
    }
  };
  WP.drawBuild = function (B) {
    var at = this.stageAt, t = this.t, night = this.night > 0.5, P = this.place;
    // stage 1: the house builds itself, a piece at a time
    if (this.stage >= 1) {
      var u = clamp((t - (at[1] || -10)) / 2.4, 0, 1);
      B.mir = 1;
      if (u >= 1) {
        house(B, P.house[0], P.house[1], 0, this.look, night, 1);
      } else {
        var tmp = [], H = new Builder(tmp, 1);
        house(H, P.house[0], P.house[1], 0, this.look, night, 1);
        var n = tmp.length;
        for (var i = 0; i < n; i++) {
          var k = backOut(clamp(u * 1.6 - (i / n) * 0.6, 0, 1));
          if (k <= 0.01) continue;
          var q = tmp[i];
          q.p = [q.p[0], q.p[1] + (1 - k) * 6, q.p[2]];
          q.s = [q.s[0] * k, q.s[1] * k, q.s[2] * k];
          B.parts.push(q);
        }
        if (this.particles && Math.random() < 0.4) this.sparkle([P.house[0] + (Math.random() - 0.5) * 10, 1 + Math.random() * 8, P.house[1] + (Math.random() - 0.5) * 8], 2);
      }
    }
    // stage 2: their name on the sign
    this.signAt = [10.4, 0, 3.8];
    if (this.stage >= 2) {
      var s = backOut(clamp((t - (at[2] || -10)) / 0.6, 0, 1));
      B.mir = 1;
      signpost(B, this.signAt[0], this.signAt[2], 0.45, s);
    }
    // stage 4: a padlock on the door
    if (this.stage >= 4) {
      var l = clamp((t - (at[4] || -10)) / 0.9, 0, 1), drop = (1 - backOut(l)) * 5, shut = l > 0.75 ? 0 : 0.45;
      var dx = P.house[0] + 0.9, dz = P.house[1] + 5.45;
      B.parts.push({ t: 'rbox', p: [dx, 2.6 + drop, dz], s: [1.5, 1.3, 0.6], c: '#f2c230', m: 'metal' });
      B.parts.push({ t: 'torus', p: [dx, 3.55 + drop + shut, dz], s: [1.1, 1.1, 1.1], r: [Math.PI / 2, 0, 0], c: '#b9c0c8', m: 'metal' });
      if (l > 0.7 && !this.locked) { this.locked = true; this.sparkle([dx, 3, dz], 14); }
    } else this.locked = false;
  };

  /* ============================================================ overlay */
  WP.drawOverlay = function () {
    var ctx = this.ctx, dpr = this.dpr || 1, W = this.cssW, H = this.cssH, i;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'center';
    // the shield badge on top of the dome
    if (this.domeK > 0.6) {
      var top = this.project([0, this.domeR() * 0.92 * this.domeK + 0.2, 0]);
      if (top) this.drawBadge(ctx, top.x, top.y);
    }
    // what kids are saying
    ctx.font = 'bold 12px Verdana, ' + this.font;
    for (i = 0; i < this.kids.length; i++) {
      var k = this.kids[i];
      if (!k.say || !k.visible) continue;
      var hp = this.project([k.x, k.y + k.jy + 7.4, k.z]);
      if (hp) this.bubble(ctx, hp.x, hp.y, k.say, '#ffffff', '#1b2a35', Math.min(1, k.sayT * 3));
    }
    for (i = 0; i < this.hearts.length; i++) {
      var h = this.hearts[i];
      if (h.t < 0) continue;
      var p = this.project([h.x, h.y + h.t * 4, h.z]);
      if (p) this.heartShape(ctx, p.x + h.dx * h.t, p.y, 7, Math.max(0, 1 - h.t / 1.4));
    }
    for (i = 0; i < this.notes.length; i++) {
      var nt = this.notes[i], np = this.project([nt.x, 4 + nt.t * 5, nt.z]);
      if (!np) continue;
      ctx.globalAlpha = Math.max(0, 1 - nt.t / 2);
      ctx.fillStyle = ['#ff5ad1', '#3cc8ff', '#7dff9a', '#ffd36a'][Math.floor(nt.x * 10 + 20) % 4];
      ctx.font = 'bold 18px Verdana, sans-serif';
      ctx.fillText(nt.x > 0 ? '♪' : '♫', np.x, np.y);
      ctx.globalAlpha = 1;
    }
    // messages flying at the glass, and bouncing off it
    ctx.font = 'bold 12px Verdana, ' + this.font;
    for (i = 0; i < this.threats.length; i++) this.drawThreat(ctx, this.threats[i], W, H);
    if (this.mini) this.drawMini(ctx, W, H);
  };
  WP.drawBadge = function (ctx, x, y) {
    var s = 1 + this.badgeHit * 0.4 + Math.sin(this.t * 2) * 0.03;
    ctx.save();
    ctx.translate(x, y - 16);
    ctx.scale(s, s);
    ctx.beginPath(); ctx.arc(0, 0, 15, 0, TAU);
    var g = ctx.createLinearGradient(0, -15, 0, 15);
    g.addColorStop(0, '#5fa8ea'); g.addColorStop(1, '#1d5fae');
    ctx.fillStyle = g; ctx.fill();
    ctx.lineWidth = 2; ctx.strokeStyle = '#ffffff'; ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(0, -8); ctx.lineTo(7, -5); ctx.lineTo(6, 3); ctx.quadraticCurveTo(4, 8, 0, 10);
    ctx.quadraticCurveTo(-4, 8, -6, 3); ctx.lineTo(-7, -5); ctx.closePath();
    ctx.fillStyle = '#ffffff'; ctx.fill();
    ctx.beginPath(); ctx.moveTo(-3, 1); ctx.lineTo(-0.5, 3.6); ctx.lineTo(3.6, -1.6);
    ctx.strokeStyle = '#1d5fae'; ctx.lineWidth = 2.2; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
    ctx.restore();
  };
  WP.bubble = function (ctx, x, y, text, bg, ink, alpha) {
    var w = ctx.measureText(text).width + 14, h = 20;
    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.fillStyle = bg;
    ctx.strokeStyle = 'rgba(20,40,70,0.35)';
    ctx.lineWidth = 1;
    roundRect(ctx, x - w / 2, y - h - 6, w, h, 6);
    ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x - 4, y - 6.5); ctx.lineTo(x, y); ctx.lineTo(x + 4, y - 6.5); ctx.closePath(); ctx.fill();
    ctx.fillStyle = ink;
    ctx.fillText(text, x, y - h / 2 - 6 + 0.5);
    ctx.restore();
  };
  WP.drawThreat = function (ctx, th, W, H) {
    var hit = this.project(th.p);
    if (!hit) return;
    var x, y, a = 1, sc = 1;
    var sx = th.side < 0 ? -60 : W + 60, sy = H * th.y0;
    if (th.t < 1) {
      var e = smooth(th.t);
      x = lerp(sx, hit.x, e); y = lerp(sy, hit.y, e); a = Math.min(1, th.t * 4);
    } else {
      var b = Math.min(1, (th.t - 1) / 0.6);
      x = hit.x + (th.side < 0 ? -1 : 1) * 70 * b; y = hit.y - 26 * b + 60 * b * b; a = 1 - b; sc = 1 - 0.35 * b;
    }
    var text = th.spec.text, w = ctx.measureText(text).width + 34;
    ctx.save();
    ctx.globalAlpha = Math.max(0, a);
    ctx.translate(x, y); ctx.scale(sc, sc);
    ctx.fillStyle = '#ffffff';
    ctx.strokeStyle = '#c4281c';
    ctx.lineWidth = 1.5;
    roundRect(ctx, -w / 2, -12, w, 24, 4);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#c4281c';
    ctx.beginPath(); ctx.arc(-w / 2 + 12, 0, 7, 0, TAU); ctx.fill();
    ctx.fillStyle = '#ffffff'; ctx.font = 'bold 10px Verdana, sans-serif'; ctx.fillText('!', -w / 2 + 12, 0.5);
    ctx.fillStyle = '#22303c'; ctx.font = 'bold 12px Verdana, ' + this.font;
    ctx.fillText(text, 9, 0.5);
    if (th.t >= 1 && th.t < 1.25) {
      ctx.strokeStyle = '#c4281c'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(-w / 2 - 4, -15); ctx.lineTo(w / 2 + 4, 15); ctx.stroke();
    }
    ctx.restore();
  };
  WP.drawMini = function (ctx, W, H) {
    var m = this.mini, k = this.kids[0];
    for (var i = 0; i < m.list.length; i++) {
      var b = m.list[i], hit = this.project(b.p), x, y, a = 1, sc = 1;
      if (!hit) continue;
      if (b.good) {
        var kp = k ? this.project([k.x, 6.4, k.z]) : hit;
        var e = smooth(Math.min(1, b.t / 1.55));
        var sx = W + 40, sy = H * 0.2;
        x = lerp(sx, kp.x + 38, e); y = lerp(sy, kp.y - 4, e) - Math.sin(e * Math.PI) * 10;
        a = Math.min(1, b.t * 4, (2.6 - b.t) * 2);
      } else if (b.t < 1) {
        var e2 = smooth(b.t), sx2 = b.side < 0 ? -50 : W + 50;
        x = lerp(sx2, hit.x, e2); y = lerp(H * 0.25, hit.y, e2); a = Math.min(1, b.t * 4);
      } else {
        var bb = Math.min(1, (b.t - 1) / 0.55);
        x = hit.x + b.side * 50 * bb; y = hit.y - 18 * bb + 36 * bb * bb; sc = 1 - 0.4 * bb; a = 1 - bb;
      }
      ctx.font = 'bold 11px Verdana, ' + this.font;
      var tw = ctx.measureText(b.text).width + 16;
      ctx.save();
      ctx.globalAlpha = Math.max(0, a);
      ctx.translate(x, y); ctx.scale(sc, sc);
      ctx.fillStyle = b.good ? '#2f8f3f' : '#c4281c';
      roundRect(ctx, -tw / 2, -11, tw, 22, 4); ctx.fill();
      ctx.beginPath(); ctx.moveTo(-6, 10); ctx.lineTo(-10, 16); ctx.lineTo(1, 10); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#ffffff';
      ctx.fillText(b.text, 0, 0.5);
      ctx.restore();
    }
    if (m.approve) {
      var age = m.t - m.approve, pop = backOut(age / 0.4), fade = Math.min(1, (10.4 - (m.t % 10.5)) / 0.4);
      var label = this.host.getAttribute('data-approve') || 'You approved Leo';
      ctx.font = 'bold 11px Verdana, ' + this.font;
      var w = ctx.measureText(label).width + 40, x0 = 10, y0 = H - 38;
      ctx.save();
      ctx.globalAlpha = Math.max(0, Math.min(1, fade));
      ctx.translate(x0 + w / 2, y0 + 14); ctx.scale(pop, pop); ctx.translate(-(x0 + w / 2), -(y0 + 14));
      ctx.fillStyle = '#ffffff';
      ctx.strokeStyle = '#8fbf8f';
      roundRect(ctx, x0, y0, w, 28, 4); ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#2f8f3f';
      ctx.beginPath(); ctx.arc(x0 + 15, y0 + 14, 9, 0, TAU); ctx.fill();
      ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(x0 + 11, y0 + 14); ctx.lineTo(x0 + 14, y0 + 17); ctx.lineTo(x0 + 19.5, y0 + 11); ctx.stroke();
      ctx.fillStyle = '#1b3d5f'; ctx.textAlign = 'left';
      ctx.fillText(label, x0 + 29, y0 + 14.5);
      ctx.restore();
    }
  };
  WP.heartShape = function (ctx, x, y, s, a) {
    ctx.save();
    ctx.globalAlpha = a;
    ctx.fillStyle = '#ff4d6d';
    ctx.beginPath();
    ctx.moveTo(x, y + s * 0.9);
    ctx.bezierCurveTo(x - s * 1.4, y, x - s * 0.8, y - s * 1.1, x, y - s * 0.35);
    ctx.bezierCurveTo(x + s * 0.8, y - s * 1.1, x + s * 1.4, y, x, y + s * 0.9);
    ctx.fill();
    ctx.restore();
  };
  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  /* ========================================================= interaction */
  WP.bind = function () {
    var self = this, canvas = this.overlay;
    canvas.style.touchAction = 'pan-y';
    var down = null;
    canvas.addEventListener('pointerdown', function (e) {
      down = { x: e.clientX, y: e.clientY, t: clock(), drag: false, last: e.clientX };
    });
    canvas.addEventListener('pointermove', function (e) {
      if (!down || e.pointerType === 'touch') return;
      var dx = e.clientX - down.x;
      if (!down.drag && Math.abs(dx) > 6) { down.drag = true; self.dragging = true; try { canvas.setPointerCapture(e.pointerId); } catch (err) {} }
      if (down.drag) {
        var step = (e.clientX - down.last) * 0.008;
        self.drag -= step;
        self.dragVel = -step * 30;
        down.last = e.clientX;
        if (reduced) self.frame(0);
      }
    });
    function up(e) {
      if (!down) return;
      var was = down;
      down = null;
      self.dragging = false;
      if (!was.drag && clock() - was.t < 450) self.tap(e);
    }
    canvas.addEventListener('pointerup', up);
    canvas.addEventListener('pointercancel', function () { down = null; self.dragging = false; });
    if (global.ResizeObserver) {
      this.ro = new ResizeObserver(function () { self.fit = null; if (reduced) self.frame(0); });
      this.ro.observe(this.host);
    }
    if (global.IntersectionObserver) {
      this.io = new IntersectionObserver(function (entries) { self.visible = entries[0].isIntersecting; });
      this.io.observe(this.host);
    }
  };
  WP.tap = function (e) {
    var rect = this.overlay.getBoundingClientRect(), x = e.clientX - rect.left, y = e.clientY - rect.top;
    // a kid?
    var best = null, bd = 34;
    for (var i = 0; i < this.kids.length; i++) {
      var k = this.kids[i];
      if (!k.visible) continue;
      var p = this.project([k.x, k.y + 3, k.z]);
      if (!p) continue;
      var d = Math.hypot(p.x - x, p.y - y);
      if (d < bd) { bd = d; best = k; }
    }
    if (best) {
      best.vy = 16; best.happy = 1.2;
      this.say(best, pick(Math.random, ['hi!', 'yay!', ':D', 'hehe', 'wanna play?', '♥']));
      this.heart(best);
      if (reduced) this.frame(0);
      return;
    }
    // the ground?
    var hitp = this.groundAt(x, y);
    if (hitp && Math.hypot(hitp[0], hitp[2]) < this.R - 1) {
      if (this.flowers.length > 14) this.flowers.shift();
      this.flowers.push({ x: hitp[0], z: hitp[2], t: 0, c: pick(Math.random, this.S.flowers) });
      this.sparkle([hitp[0], 0.5, hitp[2]], 8);
      if (reduced) { this.flowers[this.flowers.length - 1].t = 1; this.frame(0); }
      return;
    }
    // the sky
    this.firework();
  };
  WP.groundAt = function (x, y) {
    var M = GLX.mat, inv = this.renderer.invViewProj, nx = x / this.cssW * 2 - 1, ny = 1 - y / this.cssH * 2;
    function un(z) {
      var v = [nx, ny, z, 1], o = [0, 0, 0, 0];
      for (var r = 0; r < 4; r++) o[r] = inv[r] * v[0] + inv[4 + r] * v[1] + inv[8 + r] * v[2] + inv[12 + r] * v[3];
      return [o[0] / o[3], o[1] / o[3], o[2] / o[3]];
    }
    var a = un(-1), b = un(1), dy = b[1] - a[1];
    if (Math.abs(dy) < 1e-6) return null;
    var tt = (0.4 - a[1]) / dy;
    if (tt < 0) return null;
    return [a[0] + (b[0] - a[0]) * tt, 0.4, a[2] + (b[2] - a[2]) * tt];
  };

  /* ====================================================== build mode API */
  WP.setStage = function (n) {
    n = Math.max(0, Math.min(7, n | 0));
    if (n === this.stage) return;
    var up = n > this.stage;
    for (var s = this.stage + 1; s <= n; s++) this.stageAt[s] = this.t;
    this.stage = n;
    if (up && n === 7) this.celebrate();
    if (n >= 3 && this.child && up && reduced) this.child.visible = true;
    if (reduced) { this.domeK = n >= 5 ? 1 : 0; this.warm(3); this.frame(0); }
  };
  WP.setName = function (name) {
    this.name = String(name || '').slice(0, 24);
    if (reduced) this.frame(0);
  };
  WP.setLook = function (look) {
    if (!look) return;
    if (!this.child && this.mode === 'build') this.stepBuild(0);
    var k = this.child;
    if (!k) return;
    if (look.shirt) { k.desc.colors.torso = look.shirt; }
    if (look.pants) { k.desc.colors.left_leg = k.desc.colors.right_leg = k.desc.colors.hips = look.pants; }
    if (reduced) this.frame(0);
  };
  WP.setLight = function (name) {
    if (!LIGHTS[name] || name === this.light) return;
    this.lightFrom = this.light;
    this.light = name;
    this.lightMix = reduced ? 1 : 0;
    this.applyLight(this.lightMix);
    if (reduced) this.frame(0);
  };
  WP.celebrate = function () {
    var self = this;
    if (!reduced) for (var q = 0; q < 6; q++) (function (q) { setTimeout(function () { self.firework(); }, q * 380); })(q);
    var k = this.child;
    if (k) { k.happy = 3; k.vy = 16; this.say(k, 'yay!'); this.heart(k); }
    if (!this.friendsCame && this.mode === 'build') {
      this.friendsCame = true;
      var r = mulberry(this.seed + 7);
      var spots = [[-7.5, 6.5], [9.0, 2.0]];
      for (var f = 0; f < 2; f++) {
        var fk = this.makeKid(r, { x: spots[f][0], z: spots[f][1], yaw: 0.3 });
        fk.friend = true; fk.visible = false;
        (function (fk, f) { setTimeout(function () { fk.ready = true; }, 500 + f * 400); })(fk, f);
        this.kids.push(fk);
      }
    }
  };
  var baseBuildKid = WP.updateBuildKid;
  WP.updateBuildKid = function (k, dt) {
    if (k.friend && !k.ready) { k.visible = false; return; }
    return baseBuildKid.call(this, k, dt);
  };
  WP.destroy = function () {
    this.dead = true;
    if (this.raf) cancelAnimationFrame(this.raf);
    if (this.ro) this.ro.disconnect();
    if (this.io) this.io.disconnect();
    if (this.canvas && this.canvas.parentNode) this.canvas.parentNode.removeChild(this.canvas);
    if (this.overlay && this.overlay.parentNode) this.overlay.parentNode.removeChild(this.overlay);
    this.host.classList.remove('haven-live');
    this.host.haven = null;
  };

  /* ============================================================ mounting */
  function mount(el) {
    if (!el || el.haven) return el && el.haven;
    var mode = el.getAttribute('data-haven') || 'hero';
    try {
      var w = new World(el, mode);
      return w.renderer ? w : null;
    } catch (err) {
      if (global.console && console.warn) console.warn('haven:', err);
      return null;
    }
  }
  function mountAll() {
    var els = document.querySelectorAll('[data-haven]');
    for (var q = 0; q < els.length; q++) mount(els[q]);
  }
  global.Haven = { mount: mount, mountAll: mountAll, World: World };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mountAll);
  else mountAll();
})(window);
