/* The haven: a little world under a glass dome, drawn live on a canvas.

   Wherever the dome appears -- the landing page, the sign-up page, the
   set-up wizard and the comparison card -- this draws it.  It's a floating
   island of studded plastic bricks, the same look as the game.  Yellow
   blocky kids swing, slide, fish, build, dance, fly kites and play catch;
   ducks paddle round the pond, a stream runs off the edge as a waterfall,
   and the glass dome over all of it turns away whatever flies at it from
   outside, rain included.

   It is a new little world every visit: the island, the buildings, who is
   playing and what they wear come from a fresh seed.  The trees and the
   weather follow the real season, and events (fireworks, lanterns,
   balloons, a storm that can't get in, a dance party) turn up in their own
   time.  It answers a pointer too: tap a kid, the grass, the pond, the
   house, the windmill, the campfire, the shield or the open sky.

   It costs nothing when nobody is looking: the terrain and every still
   prop are painted once and reused, the loop stops off screen and in a
   hidden tab, a slow device drops its resolution, and
   prefers-reduced-motion gets one still frame.

   Hooks: an element with data-haven="hero|panel|build|mini" is mounted
   automatically and its world is el.haven.  A blocked message fires
   "haven:blocked" on that element (detail: {icon, title, what}).  Build
   mode takes setStage(n), setName(s), setLook({shirt, pants}),
   setLight(name) and celebrate(). */
(function (global) {
  'use strict';

  var TAU = Math.PI * 2;
  var SQ2 = Math.SQRT2;
  var LEFT = 1, RIGHT = 2, TOP = 4;
  var DX = [1, 0, -1, 0], DY = [0, 1, 0, -1];      // facing +x, +y, -x, -y
  var EMPTY = {};
  var reduced = !!(global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var query = {};
  try {
    String(global.location.search || '').replace(/[?&]([^=&]+)=([^&]*)/g, function (m, k, v) {
      query[decodeURIComponent(k)] = decodeURIComponent(v);
    });
  } catch (e) { /* no query string */ }

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
  function hash(i, j, k) {
    var h = Math.sin(i * 127.1 + j * 311.7 + (k || 0) * 74.7) * 43758.5453;
    return h - Math.floor(h);
  }
  function clamp(v, a, b) { return v < a ? a : (v > b ? b : v); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function smooth(t) { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); }
  function backOut(t) { t = clamp(t, 0, 1) - 1; return t * t * (2.70158 * t + 1.70158) + 1; }
  function pick(r, list) { return list[Math.floor(r() * list.length) % list.length]; }
  function clock() { return (global.performance && performance.now) ? performance.now() : Date.now(); }

  var shades = {};
  function rgbOf(hex) {
    var n = parseInt(hex.slice(1), 16);
    return [n >> 16 & 255, n >> 8 & 255, n & 255];
  }
  /* k below 1 darkens toward black, above 1 lightens toward white */
  function shade(hex, k) {
    var key = hex + k;
    var v = shades[key];
    if (v) return v;
    var c = rgbOf(hex), r = c[0], g = c[1], b = c[2];
    if (k <= 1) { r *= k; g *= k; b *= k; } else { var t = k - 1; r += (255 - r) * t; g += (255 - g) * t; b += (255 - b) * t; }
    v = '#' + ((1 << 24) + (clamp(Math.round(r), 0, 255) << 16) + (clamp(Math.round(g), 0, 255) << 8) + clamp(Math.round(b), 0, 255)).toString(16).slice(1);
    shades[key] = v;
    return v;
  }
  function mix(a, b, t) {
    var x = rgbOf(a), y = rgbOf(b);
    var r = Math.round(lerp(x[0], y[0], t)), g = Math.round(lerp(x[1], y[1], t)), bl = Math.round(lerp(x[2], y[2], t));
    return '#' + ((1 << 24) + (r << 16) + (g << 8) + bl).toString(16).slice(1);
  }
  function rgba(hex, a) { var c = rgbOf(hex); return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a + ')'; }

  /* =========================================================== palettes */
  var SKIN = '#f5cd30';      // every kid in here wears the classic yellow
  var SHIRTS = ['#c4281c', '#0d69ac', '#287f46', '#da8541', '#6b327c', '#008f9c', '#ff66cc', '#f2f3f3',
                '#1b2a35', '#ffcf3a', '#e8463b', '#3c8dde', '#8b5cf6', '#14b8a6'];
  var PANTS = ['#0d69ac', '#1b2a35', '#a4bd47', '#5b3a29', '#343a40', '#2b5fa8', '#6b327c', '#7b8a99', '#c4281c'];
  var HAIRS = ['#3b2414', '#1b1b1b', '#e2b04a', '#a0522d', '#5c3a1e', '#2b1a10'];
  var HATS = ['#c4281c', '#0d69ac', '#287f46', '#ffcf3a', '#6b327c', '#ff66cc', '#14b8a6'];
  var BRICKS = ['#e8463b', '#ffcf3a', '#3c8dde', '#2fb35a', '#ff8a3d', '#8b5cf6', '#ff66cc', '#f2f3f3'];
  var ROOFS = ['#c4281c', '#2b5fa8', '#287f46', '#6b327c', '#da8541', '#d6336c'];
  var WALLS = ['#f3e7cf', '#e3edf8', '#f7e0e0', '#e5f0d8', '#fdf1c7'];
  var DIRT = '#8d5b36', STONE = '#7e8494', PATH = '#dcc593', SAND = '#d8c290', WATER = '#3f9ff0', PLANK = '#b5804b';
  var SEASON_OF_MONTH = ['winter', 'winter', 'spring', 'spring', 'spring', 'summer', 'summer', 'summer', 'autumn', 'autumn', 'autumn', 'winter'];
  var SEASONS = {
    spring: { grass: '#62c46e', turf: '#4ea95a', leaves: ['#ffb3d1', '#ff9cc2', '#ffc6dd', '#6cc06a'], trunk: '#7a4e2c',
              flowers: ['#ff6fa8', '#ffd23f', '#ffffff', '#b48cff', '#ff9f43'], fall: 'petal' },
    summer: { grass: '#54b65c', turf: '#42a04d', leaves: ['#3e9d48', '#4fb357', '#2f8a40', '#5cc05f'], trunk: '#7a4e2c',
              flowers: ['#ff5a5f', '#ffd23f', '#ff9f1c', '#4ecdc4', '#ffffff'], fall: 'firefly' },
    autumn: { grass: '#86b648', turf: '#6f9c3c', leaves: ['#e8742a', '#d9442b', '#f2b630', '#c95f2a', '#9fbf3b'], trunk: '#6e4426',
              flowers: ['#e8742a', '#c9302c', '#f2b630', '#ffffff'], fall: 'leaf' },
    winter: { grass: '#f1f6ff', turf: '#dce6f6', leaves: ['#2e7a4c', '#3a8b57', '#25693f'], trunk: '#5e3d24',
              flowers: ['#ff5a5f', '#ffffff'], fall: 'snow', snow: true }
  };
  var LIGHTS = {
    day:   { tint: null, glow: 0.15 },
    dawn:  { tint: ['rgba(255,160,180,0.10)', 'rgba(140,110,200,0.12)'], glow: 0.35 },
    gold:  { tint: ['rgba(255,190,90,0.13)', 'rgba(200,110,80,0.12)'], glow: 0.45 },
    dusk:  { tint: ['rgba(255,176,128,0.07)', 'rgba(70,50,160,0.13)'], glow: 0.85 },
    night: { tint: ['rgba(40,50,140,0.30)', 'rgba(20,24,90,0.42)'], glow: 1 }
  };
  var THREATS = [
    { icon: 'at', what: 'an invite to another app', title: 'Safe Chat stopped an invite' },
    { icon: 'phone', what: 'a phone number', title: 'Safe Chat blocked a phone number' },
    { icon: 'pin', what: 'a home address', title: 'Safe Chat blocked an address' },
    { icon: 'camera', what: 'a request for photos', title: 'Safe Chat blocked a photo request' },
    { icon: 'link', what: 'a link to another site', title: 'Safe Chat blocked a link' }
  ];
  var CHAT = ['gg!', 'yay!', 'wanna build?', 'nice!', 'lol', 'so fun', 'race you!', 'tag!', 'woo!', 'hi!', 'look!', 'best day'];

  var MODES = {
    hero:  { w: 600, h: 620, n: 18, tw: 35, cx: 300, cy: 338, depth: 7, pad: 0.75, hk: 1.12, kids: 8, threats: 3900,
             light: 'dusk', outside: true, events: true, critters: true },
    panel: { w: 600, h: 620, n: 16, tw: 38, cx: 300, cy: 338, depth: 6, pad: 0.75, hk: 1.12, kids: 6, threats: 6500,
             light: 'dusk', outside: true, events: true, critters: true },
    build: { w: 520, h: 380, n: 10, tw: 38, cx: 260, cy: 206, depth: 3.6, pad: 0.7, hk: 1.12, kids: 0, threats: 0,
             light: 'dawn', outside: false, events: false, critters: false },
    mini:  { w: 480, h: 240, n: 7, tw: 32, cx: 240, cy: 156, depth: 1.5, pad: 0.7, hk: 1.18, kids: 1, threats: 0,
             light: 'day', outside: false, events: false, critters: false }
  };

  /* ======================================================== projection
     Tile (i, j) covers [i, i+1] x [j, j+1]; z counts blocks, and a block is
     as tall as a tile is deep, so they read as cubes.  +x runs down to the
     right, +y down to the left; the faces you can see are the top, the +y
     face (left) and the +x face (right). */
  function Iso(tw, ox, oy) { this.tw = tw; this.hw = tw / 2; this.hh = tw / 4; this.bh = tw / 2; this.ox = ox; this.oy = oy; }
  Iso.prototype.sx = function (x, y) { return this.ox + (x - y) * this.hw; };
  Iso.prototype.sy = function (x, y, z) { return this.oy + (x + y) * this.hh - z * this.bh; };

  function quad(ctx, ax, ay, bx, by, cx, cy, dx, dy) {
    ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx, by); ctx.lineTo(cx, cy); ctx.lineTo(dx, dy); ctx.closePath(); ctx.fill();
  }
  /* an axis-aligned box with the game's lighting: lit top, mid left, dark right */
  function box(ctx, I, x, y, z, w, d, h, col, o) {
    o = o || EMPTY;
    var hw = I.hw, hh = I.hh, ox = I.ox, oy = I.oy, zt = (z + h) * I.bh, dn = h * I.bh;
    var ax = ox + (x - y) * hw,         ay = oy + (x + y) * hh - zt;
    var bx = ox + (x + w - y) * hw,     by = oy + (x + w + y) * hh - zt;
    var cx = ox + (x + w - y - d) * hw, cy = oy + (x + w + y + d) * hh - zt;
    var dx = ox + (x - y - d) * hw,     dy = oy + (x + y + d) * hh - zt;
    if (!o.noLeft && dn > 0) { ctx.fillStyle = o.left || shade(col, 0.8); quad(ctx, dx, dy, cx, cy, cx, cy + dn, dx, dy + dn); }
    if (!o.noRight && dn > 0) { ctx.fillStyle = o.right || shade(col, 0.64); quad(ctx, cx, cy, bx, by, bx, by + dn, cx, cy + dn); }
    if (!o.noTop) {
      ctx.fillStyle = o.top || col;
      quad(ctx, ax, ay, bx, by, cx, cy, dx, dy);
      if (o.studs) studs(ctx, I, x, y, z + h, w, d, o.studs, o.top || col);
    }
    if (o.edge && dn > 1) {
      ctx.strokeStyle = 'rgba(255,255,255,0.24)';
      ctx.lineWidth = Math.max(0.6, hw * 0.05);
      ctx.beginPath(); ctx.moveTo(dx, dy); ctx.lineTo(cx, cy); ctx.lineTo(bx, by); ctx.stroke();
    }
  }
  /* the studs on a brick's top, like the game's upward faces */
  function studs(ctx, I, x, y, z, w, d, per, col) {
    var nx = Math.max(1, Math.round(w * per)), ny = Math.max(1, Math.round(d * per));
    var cw = w / nx, cd = d / ny, r = Math.min(cw, cd) * 0.27;
    var rx = r * SQ2 * I.hw, ry = rx * 0.5, sh = Math.max(0.7, I.bh * 0.075);
    if (rx < 0.7) return;
    var lite = shade(col, 1.09), dark = shade(col, 0.84);
    for (var a = 0; a < nx; a++) {
      for (var b = 0; b < ny; b++) {
        var px = x + (a + 0.5) * cw, py = y + (b + 0.5) * cd;
        var sx = I.ox + (px - py) * I.hw, sy = I.oy + (px + py) * I.hh - z * I.bh;
        ctx.fillStyle = dark;
        ctx.beginPath(); ctx.ellipse(sx, sy, rx, ry, 0, 0, TAU); ctx.fill();
        ctx.fillRect(sx - rx, sy - sh, rx * 2, sh);
        ctx.fillStyle = lite;
        ctx.beginPath(); ctx.ellipse(sx, sy - sh, rx, ry, 0, 0, TAU); ctx.fill();
      }
    }
  }
  /* corners of a box's two visible side faces, u running left to right on
     screen and v running down: [ax, ay, bx, by, dx, dy] */
  function leftFace(I, x, y, z, w, d, h) {
    var Y = y + d, T = z + h;
    return [I.sx(x, Y), I.sy(x, Y, T), I.sx(x + w, Y), I.sy(x + w, Y, T), I.sx(x, Y), I.sy(x, Y, z)];
  }
  function rightFace(I, x, y, z, w, d, h) {
    var X = x + w, T = z + h;
    return [I.sx(X, y + d), I.sy(X, y + d, T), I.sx(X, y), I.sy(X, y, T), I.sx(X, y + d), I.sy(X, y + d, z)];
  }
  function topFace(I, x, y, z, w, d) {
    return [I.sx(x, y + d), I.sy(x, y + d, z), I.sx(x + w, y), I.sy(x + w, y, z), I.sx(x, y), I.sy(x, y, z)];
  }
  /* draw in a face's own unit square */
  function onFace(ctx, f, draw) {
    ctx.save();
    ctx.transform(f[2] - f[0], f[3] - f[1], f[4] - f[0], f[5] - f[1], f[0], f[1]);
    draw(ctx);
    ctx.restore();
  }
  function line(ctx, I, x1, y1, z1, x2, y2, z2) {
    ctx.beginPath(); ctx.moveTo(I.sx(x1, y1), I.sy(x1, y1, z1)); ctx.lineTo(I.sx(x2, y2), I.sy(x2, y2, z2)); ctx.stroke();
  }

  var glows = {};
  function glow(color) {
    var g = glows[color];
    if (g) return g;
    g = document.createElement('canvas');
    g.width = g.height = 64;
    var x = g.getContext('2d');
    var grd = x.createRadialGradient(32, 32, 0, 32, 32, 32);
    grd.addColorStop(0, rgba(color, 1));
    grd.addColorStop(0.22, rgba(color, 0.5));
    grd.addColorStop(0.55, rgba(color, 0.14));
    grd.addColorStop(1, rgba(color, 0));
    x.fillStyle = grd;
    x.fillRect(0, 0, 64, 64);
    glows[color] = g;
    return g;
  }
  /* the page's own icons (the sprite in icons.html), as white images */
  var icons = {};
  function icon(name) {
    if (icons[name] !== undefined) return icons[name];
    var sym = document.getElementById('i-' + name), img = null;
    if (sym) {
      var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="' + (sym.getAttribute('viewBox') || '0 0 24 24') +
        '" width="48" height="48" fill="none" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">' +
        sym.innerHTML + '</svg>';
      img = new Image();
      img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
    }
    icons[name] = img;
    return img;
  }
  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }
  function heartPath(ctx, x, y, s) {
    ctx.beginPath();
    ctx.moveTo(x, y + s * 0.35);
    ctx.bezierCurveTo(x - s * 1.1, y - s * 0.4, x - s * 0.45, y - s * 1.05, x, y - s * 0.45);
    ctx.bezierCurveTo(x + s * 0.45, y - s * 1.05, x + s * 1.1, y - s * 0.4, x, y + s * 0.35);
    ctx.closePath();
  }
  function starPath(ctx, x, y, r) {
    ctx.beginPath();
    for (var i = 0; i < 10; i++) {
      var a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.45 : r;
      if (i) ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); else ctx.moveTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr);
    }
    ctx.closePath();
  }
  function notePath(ctx, x, y, s) {
    ctx.beginPath(); ctx.ellipse(x, y, s * 0.42, s * 0.3, -0.4, 0, TAU); ctx.fill();
    ctx.fillRect(x + s * 0.3, y - s * 1.3, s * 0.13, s * 1.32);
    ctx.beginPath(); ctx.moveTo(x + s * 0.42, y - s * 1.3); ctx.quadraticCurveTo(x + s * 0.95, y - s * 1.05, x + s * 0.75, y - s * 0.62);
    ctx.lineTo(x + s * 0.42, y - s * 0.9); ctx.closePath(); ctx.fill();
  }
  function shieldPath(ctx, x, y, s) {
    ctx.beginPath();
    ctx.moveTo(x, y - s);
    ctx.lineTo(x + s * 0.82, y - s * 0.66);
    ctx.lineTo(x + s * 0.82, y - s * 0.05);
    ctx.quadraticCurveTo(x + s * 0.74, y + s * 0.72, x, y + s);
    ctx.quadraticCurveTo(x - s * 0.74, y + s * 0.72, x - s * 0.82, y - s * 0.05);
    ctx.lineTo(x - s * 0.82, y - s * 0.66);
    ctx.closePath();
  }

  /* ============================================================ terrain */
  function baseTop(G, i, j) {
    var t = G.top[i][j];
    if (t === null) return null;
    return t > 0 ? 0 : t;
  }
  function blockAt(G, i, j, L, full) {
    if (i < 0 || j < 0 || i >= G.n || j >= G.n) return false;
    var t = full ? G.top[i][j] : baseTop(G, i, j);
    if (t === null) return false;
    return L >= G.bot[i][j] && L < t;
  }
  function material(G, i, j, L, top) {
    if (L === top - 1) {
      if (G.water[i][j]) return 'sand';
      if (L < 0 && G.path[i][j]) return 'path';
      return 'grass';
    }
    if (L >= top - 3 && L >= -3) return 'dirt';
    return 'stone';
  }
  function paintBlock(ctx, w, i, j, L, top, faces) {
    var I = w.iso, G = w.G, S = w.S, mat = material(G, i, j, L, top);
    var hv = hash(i, j, L);
    var side, f;
    if (mat === 'stone') side = shade(L < -5 ? '#6b7182' : STONE, 0.94 + hv * 0.1);
    else side = shade(DIRT, 0.92 + hv * 0.12);
    if (faces & LEFT) {
      f = leftFace(I, i, j, L, 1, 1, 1);
      paintSide(ctx, w, f, mat, side, 0.82, hv, i, j, L);
    }
    if (faces & RIGHT) {
      f = rightFace(I, i, j, L, 1, 1, 1);
      paintSide(ctx, w, f, mat, side, 0.66, hv * 0.7 + 0.15, i, j, L + 50);
    }
    if (faces & TOP) {
      var t = L + 1;
      if (mat === 'grass') {
        var g = S.grass;
        box(ctx, I, i, j, L + 1, 1, 1, 0, g, { top: shade(g, 0.95 + hash(i, j, 9) * 0.1), studs: 2, noLeft: true, noRight: true });
        if (!S.snow && hash(i, j, 4) < 0.35) {
          ctx.strokeStyle = shade(g, 0.78);
          ctx.lineWidth = Math.max(0.6, I.hw * 0.06);
          var gx = i + 0.2 + hash(i, j, 5) * 0.6, gy = j + 0.2 + hash(i, j, 6) * 0.6;
          var sx = I.sx(gx, gy), sy = I.sy(gx, gy, t);
          ctx.beginPath(); ctx.moveTo(sx - 2, sy); ctx.lineTo(sx - 1, sy - 3); ctx.moveTo(sx, sy); ctx.lineTo(sx + 1, sy - 4);
          ctx.moveTo(sx + 2, sy); ctx.lineTo(sx + 3, sy - 2.5); ctx.stroke();
        }
      } else if (mat === 'path') {
        box(ctx, I, i, j, L + 1, 1, 1, 0, PATH, { top: shade(PATH, 0.96 + hash(i, j, 9) * 0.08), noLeft: true, noRight: true });
        for (var p = 0; p < 3; p++) {
          var px = i + 0.15 + hash(i, j, 20 + p) * 0.7, py = j + 0.15 + hash(i, j, 30 + p) * 0.7;
          ctx.fillStyle = p % 2 ? shade(PATH, 0.82) : shade(PATH, 1.12);
          ctx.beginPath(); ctx.ellipse(I.sx(px, py), I.sy(px, py, t), I.hw * 0.13, I.hw * 0.065, 0, 0, TAU); ctx.fill();
        }
      } else {
        box(ctx, I, i, j, L + 1, 1, 1, 0, SAND, { top: shade(SAND, 0.92 + hash(i, j, 9) * 0.1), noLeft: true, noRight: true });
      }
    }
  }
  function paintSide(ctx, w, f, mat, side, k, hv, i, j, L) {
    var S = w.S;
    ctx.fillStyle = mat === 'stone' ? shade(STONE, (0.94 + hv * 0.1) * k) : shade(DIRT, (0.92 + hv * 0.12) * k);
    quad(ctx, f[0], f[1], f[2], f[3], f[2] + f[4] - f[0], f[3] + f[5] - f[1], f[4], f[5]);
    onFace(ctx, f, function (c) {
      var r1 = hash(i, j, L * 3 + 1), r2 = hash(i, j, L * 3 + 2), r3 = hash(i, j, L * 3 + 3);
      if (mat === 'grass') {
        c.fillStyle = shade(S.turf, k * 1.04);
        c.beginPath(); c.moveTo(0, 0); c.lineTo(1, 0); c.lineTo(1, 0.3);
        for (var z = 0; z <= 6; z++) c.lineTo(1 - z / 6, z % 2 ? 0.42 : 0.3);
        c.closePath(); c.fill();
        c.fillStyle = 'rgba(255,255,255,0.16)';
        c.fillRect(0, 0, 1, 0.07);
      } else if (mat === 'path') {
        c.fillStyle = shade(PATH, k * 0.92);
        c.fillRect(0, 0, 1, 0.2);
      }
      if (mat === 'stone') {
        c.strokeStyle = 'rgba(0,0,0,0.18)';
        c.lineWidth = 0.04;
        c.beginPath(); c.moveTo(0.15 + r1 * 0.3, 0.1); c.lineTo(0.35 + r2 * 0.3, 0.45); c.lineTo(0.3 + r3 * 0.4, 0.9); c.stroke();
        if (r2 > 0.82) {
          c.fillStyle = r3 > 0.5 ? '#ffd34d' : '#6ee7ff';
          c.beginPath(); c.moveTo(0.6, 0.35); c.lineTo(0.7, 0.52); c.lineTo(0.6, 0.69); c.lineTo(0.5, 0.52); c.closePath(); c.fill();
        }
      } else {
        c.fillStyle = 'rgba(40,20,8,0.22)';
        c.fillRect(0.12 + r1 * 0.6, 0.5 + r2 * 0.35, 0.1, 0.07);
        c.fillRect(0.2 + r3 * 0.55, 0.62 + r1 * 0.25, 0.07, 0.06);
        c.fillStyle = 'rgba(255,230,200,0.16)';
        c.fillRect(0.55 * r2 + 0.1, 0.72, 0.09, 0.06);
      }
      c.strokeStyle = 'rgba(0,0,0,0.13)';
      c.lineWidth = 0.025;
      c.strokeRect(0, 0, 1, 1);
    });
  }
  function paintColumn(ctx, w, i, j, full) {
    var G = w.G, top = full ? G.top[i][j] : baseTop(G, i, j);
    var from = full ? 0 : G.bot[i][j], to = top - 1;
    for (var L = from; L <= to; L++) {
      var faces = 0;
      if (!blockAt(G, i, j + 1, L, full)) faces |= LEFT;
      if (!blockAt(G, i + 1, j, L, full)) faces |= RIGHT;
      if (L === to) faces |= TOP;
      if (faces) paintBlock(ctx, w, i, j, L, top, faces);
    }
  }
  function paintTerrain(ctx, w) {
    var G = w.G, n = G.n, I = w.iso;
    for (var s = 0; s <= 2 * (n - 1); s++) {
      for (var i = Math.max(0, s - n + 1); i <= Math.min(n - 1, s); i++) {
        var j = s - i;
        if (G.top[i][j] === null) continue;
        paintColumn(ctx, w, i, j, false);
        var b = G.bot[i][j];
        var rim = !blockAt(G, i, j + 1, b, false) || !blockAt(G, i + 1, j, b, false);
        if (hash(i, j, 77) < 0.3 && G.bot[i][j] < -1) {
          box(ctx, I, i + 0.25, j + 0.25, b - 0.5, 0.5, 0.5, 0.5, '#5f6576', { noTop: true });
        }
        if (rim && hash(i, j, 81) < 0.45) {
          ctx.strokeStyle = hash(i, j, 82) < 0.5 ? 'rgba(92,60,30,0.75)' : 'rgba(70,140,70,0.7)';
          ctx.lineWidth = Math.max(0.6, I.hw * 0.06);
          var rx = i + 0.3 + hash(i, j, 83) * 0.5, ry = j + 1;
          var len = 0.6 + hash(i, j, 84) * 1.4;
          ctx.beginPath();
          ctx.moveTo(I.sx(rx, ry), I.sy(rx, ry, -0.4));
          ctx.quadraticCurveTo(I.sx(rx, ry) + 3, I.sy(rx, ry, -0.4 - len * 0.5), I.sx(rx, ry) - 1, I.sy(rx, ry, -0.4 - len));
          ctx.stroke();
        }
        if (rim && b <= -4 && hash(i, j, 91) < 0.35) {
          var cz = b + 1 + hash(i, j, 92) * 1.5, cxw = i + 0.3 + hash(i, j, 93) * 0.4;
          var col = hash(i, j, 94) < 0.5 ? '#7fe7ff' : '#c4a5ff';
          crystal(ctx, I, cxw, j + 1.02, cz, col);
          G.crystals.push({ x: cxw, y: j + 1.05, z: cz + 0.2, c: col, p: hash(i, j, 95) * TAU });
        }
      }
    }
  }
  function crystal(ctx, I, x, y, z, col) {
    var sx = I.sx(x, y), sy = I.sy(x, y, z), s = I.hw * 0.32;
    var parts = [[0, 1.4, 0.32], [-0.42, 0.95, 0.25], [0.4, 1.05, 0.24]];
    for (var k = 0; k < parts.length; k++) {
      var p = parts[k], px = sx + p[0] * s, h = p[1] * s, wd = p[2] * s;
      ctx.fillStyle = shade(col, 0.82);
      ctx.beginPath(); ctx.moveTo(px - wd, sy); ctx.lineTo(px - wd, sy - h); ctx.lineTo(px, sy - h - wd * 1.3); ctx.lineTo(px, sy + wd * 0.4); ctx.closePath(); ctx.fill();
      ctx.fillStyle = col;
      ctx.beginPath(); ctx.moveTo(px, sy + wd * 0.4); ctx.lineTo(px, sy - h - wd * 1.3); ctx.lineTo(px + wd, sy - h); ctx.lineTo(px + wd, sy); ctx.closePath(); ctx.fill();
    }
  }

  /* ============================================================== props
     Each prop is painted once into its own little canvas (paint) and, when
     it has moving parts, gets a per-frame anim on top.  Positions are world
     units; z is the height of the ground under it. */
  var PROPS = {};
  PROPS.column = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, p.top]; },
    paint: function (ctx, I, p, w) { paintColumn(ctx, w, p.i, p.j, true); }
  };
  PROPS.tree = {
    box: function (p) { return [p.i - 0.1, p.j - 0.1, p.z, 1.2, 1.2, 2.8]; },
    paint: function (ctx, I, p, w) {
      var x = p.i, y = p.j, z = p.z, S = w.S, leaf = p.leaf, kind = p.kind;
      if (kind === 'pine') {
        box(ctx, I, x + 0.4, y + 0.4, z, 0.2, 0.2, 0.55, S.trunk);
        var tiers = [[0.06, 0.88, 0.45], [0.17, 0.66, 0.92], [0.28, 0.44, 1.38], [0.39, 0.22, 1.8]];
        for (var t = 0; t < tiers.length; t++) {
          var q = tiers[t];
          box(ctx, I, x + q[0], y + q[0], z + q[2], q[1], q[1], 0.48, shade(leaf, 1 - t * 0.04),
              { top: S.snow ? '#f6f9ff' : null, studs: t < 2 ? 2 : 1, edge: true });
        }
        return;
      }
      if (kind === 'bush') {
        box(ctx, I, x + 0.14, y + 0.14, z, 0.72, 0.72, 0.5, leaf, { studs: 2, edge: true, top: S.snow ? '#f6f9ff' : null });
        return;
      }
      box(ctx, I, x + 0.38, y + 0.38, z, 0.24, 0.24, 1.0, S.trunk);
      var tf = leftFace(I, x + 0.38, y + 0.38, z, 0.24, 0.24, 1.0);
      onFace(ctx, tf, function (c) { c.fillStyle = 'rgba(0,0,0,0.18)'; c.fillRect(0.3, 0.1, 0.12, 0.8); c.fillRect(0.68, 0.35, 0.1, 0.5); });
      box(ctx, I, x + 0.02, y + 0.02, z + 0.92, 0.96, 0.96, 0.78, leaf, { studs: 2, edge: true, top: S.snow ? '#f6f9ff' : null });
      box(ctx, I, x + 0.6, y + 0.12, z + 0.72, 0.38, 0.38, 0.36, shade(leaf, 0.9), { studs: 1 });
      box(ctx, I, x + 0.21, y + 0.21, z + 1.7, 0.58, 0.58, 0.42, shade(leaf, 1.06), { studs: 1, edge: true, top: S.snow ? '#ffffff' : null });
      if (p.fruit) {
        for (var f = 0; f < 4; f++) {
          var fx = x + 0.2 + hash(f, p.i, p.j) * 0.6, fz = z + 1.0 + hash(p.j, f, p.i) * 0.5;
          ctx.fillStyle = p.fruit;
          ctx.beginPath(); ctx.arc(I.sx(fx, y + 0.98), I.sy(fx, y + 0.98, fz), I.hw * 0.08, 0, TAU); ctx.fill();
        }
      }
    },
    sway: true
  };
  PROPS.house = {
    box: function (p) { return [p.i - 0.05, p.j - 0.1, 0, 2.1, 2.2, 3.5]; },
    paint: function (ctx, I, p) {
      var x = p.i, y = p.j, wall = p.wall, roof = p.roof;
      box(ctx, I, x + 0.04, y + 0.04, 0, 1.92, 1.92, 0.14, '#9aa0aa', { edge: true });
      box(ctx, I, x + 0.12, y + 0.12, 0.14, 1.76, 1.76, 1.34, wall, { noTop: true, edge: true });
      var lf = leftFace(I, x + 0.12, y + 0.12, 0.14, 1.76, 1.76, 1.34);
      var rf = rightFace(I, x + 0.12, y + 0.12, 0.14, 1.76, 1.76, 1.34);
      var doorLeft = p.door === 'left';
      [lf, rf].forEach(function (f, n) {
        onFace(ctx, f, function (c) {
          c.fillStyle = 'rgba(110,70,40,0.55)';
          c.fillRect(0, 0, 1, 0.05); c.fillRect(0, 0.95, 1, 0.05); c.fillRect(0, 0, 0.035, 1); c.fillRect(0.965, 0, 0.035, 1);
          c.fillRect(0, 0.5, 1, 0.03);
          var hasDoor = (n === 0) === doorLeft;
          if (hasDoor) {
            c.fillStyle = '#6b3f22'; c.fillRect(0.4, 0.4, 0.2, 0.6);
            c.fillStyle = '#4a2a16'; c.fillRect(0.4, 0.4, 0.2, 0.04);
            c.fillStyle = '#ffd34d'; c.fillRect(0.555, 0.7, 0.025, 0.035);
          }
          var wins = hasDoor ? [0.12, 0.72] : [0.16, 0.6];
          for (var k = 0; k < 2; k++) {
            var u = wins[k];
            c.fillStyle = '#f8f3e8'; c.fillRect(u - 0.02, 0.17, 0.2, 0.3);
            c.fillStyle = '#2d3f66'; c.fillRect(u, 0.2, 0.16, 0.24);
            c.fillStyle = '#f8f3e8'; c.fillRect(u + 0.07, 0.2, 0.02, 0.24); c.fillRect(u, 0.31, 0.16, 0.02);
            c.fillStyle = shade(roof, 0.9); c.fillRect(u - 0.03, 0.48, 0.22, 0.06);
            c.fillStyle = '#ff7eb6'; c.fillRect(u, 0.455, 0.04, 0.03);
            c.fillStyle = '#ffd23f'; c.fillRect(u + 0.07, 0.455, 0.04, 0.03);
            c.fillStyle = '#ffffff'; c.fillRect(u + 0.13, 0.455, 0.03, 0.03);
          }
        });
      });
      for (var k = 0; k < 4; k++) {
        var inset = k * 0.27;
        box(ctx, I, x - 0.02, y - 0.06 + inset, 1.48 + k * 0.3, 2.04, 2.12 - inset * 2, 0.3, shade(roof, 1 - k * 0.03),
            { studs: 2, edge: true });
      }
      box(ctx, I, x + 1.36, y + 0.42, 2.1, 0.3, 0.3, 0.9, '#9b4a36', { edge: true, studs: 1 });
      if (doorLeft) box(ctx, I, x + 0.75, y + 1.88, 0, 0.5, 0.3, 0.1, '#b9bec7');
      else box(ctx, I, x + 1.88, y + 0.75, 0, 0.3, 0.5, 0.1, '#b9bec7');
    },
    windows: function (p) {
      var x = p.i + 0.12, y = p.j + 0.12, z = 0.14, w = 1.76, h = 1.34, doorLeft = p.door === 'left', out = [];
      [['l', doorLeft ? [0.12, 0.72] : [0.16, 0.6]], ['r', doorLeft ? [0.16, 0.6] : [0.12, 0.72]]].forEach(function (s) {
        s[1].forEach(function (u) { out.push({ face: s[0], u: u, x: x, y: y, z: z, w: w, h: h }); });
      });
      return out;
    }
  };
  PROPS.windmill = {
    box: function (p) { return [p.i - 0.6, p.j - 0.6, p.z, 2.2, 2.2, 4.2]; },
    paint: function (ctx, I, p) {
      var x = p.i, y = p.j, z = p.z;
      box(ctx, I, x + 0.14, y + 0.14, z, 0.72, 0.72, 2.1, '#efe6d6', { noTop: true, edge: true });
      [leftFace(I, x + 0.14, y + 0.14, z, 0.72, 0.72, 2.1), rightFace(I, x + 0.14, y + 0.14, z, 0.72, 0.72, 2.1)].forEach(function (f, n) {
        onFace(ctx, f, function (c) {
          c.fillStyle = 'rgba(120,100,80,0.18)';
          for (var r = 0; r < 6; r++) c.fillRect(0, r / 6 + 0.06, 1, 0.025);
          if (n === 0) { c.fillStyle = '#6b3f22'; c.fillRect(0.36, 0.7, 0.28, 0.3); }
          c.fillStyle = '#2d3f66'; c.fillRect(0.4, 0.3, 0.2, 0.14);
        });
      });
      box(ctx, I, x + 0.06, y + 0.06, z + 2.1, 0.88, 0.88, 0.34, '#c4281c', { studs: 2, edge: true });
      box(ctx, I, x + 0.26, y + 0.26, z + 2.44, 0.48, 0.48, 0.3, '#a8231a', { studs: 1, edge: true });
    },
    anim: function (ctx, I, p, w, t) {
      p.rot = (p.rot || 0) + w.dt * (0.9 + (p.boost || 0) * 4);
      if (p.boost) p.boost = Math.max(0, p.boost - w.dt * 0.4);
      var alongY = p.face === 'right';
      var hx = alongY ? p.i + 0.9 : p.i + 0.5, hy = alongY ? p.j + 0.5 : p.j + 0.9, hz = p.z + 1.8;
      for (var k = 0; k < 4; k++) {
        var a = p.rot + k * Math.PI / 2, ca = Math.cos(a), sa = Math.sin(a);
        var L = 1.15, wd = 0.11;
        var p0 = [0.15 * ca, 0.15 * sa], p1 = [L * ca, L * sa];
        var o = [-sa * wd, ca * wd];
        var pts = [[p0[0], p0[1]], [p1[0], p1[1]], [p1[0] + o[0] * 2, p1[1] + o[1] * 2], [p0[0] + o[0] * 2, p0[1] + o[1] * 2]];
        ctx.fillStyle = k % 2 ? '#fff8ec' : '#f1e6d2';
        ctx.beginPath();
        for (var m = 0; m < 4; m++) {
          var q = pts[m], wx = alongY ? hx : hx + q[0], wy = alongY ? hy + q[0] : hy, wz = hz + q[1];
          if (m) ctx.lineTo(I.sx(wx, wy), I.sy(wx, wy, wz)); else ctx.moveTo(I.sx(wx, wy), I.sy(wx, wy, wz));
        }
        ctx.closePath(); ctx.fill();
        ctx.strokeStyle = '#7a4e2c'; ctx.lineWidth = Math.max(0.7, I.hw * 0.07);
        ctx.beginPath();
        var ax = alongY ? hx : hx + p0[0], ay = alongY ? hy + p0[0] : hy;
        var bx = alongY ? hx : hx + p1[0], by = alongY ? hy + p1[0] : hy;
        ctx.moveTo(I.sx(ax, ay), I.sy(ax, ay, hz + p0[1])); ctx.lineTo(I.sx(bx, by), I.sy(bx, by, hz + p1[1])); ctx.stroke();
      }
      ctx.fillStyle = '#5b3a29';
      ctx.beginPath(); ctx.arc(I.sx(hx, hy), I.sy(hx, hy, hz), I.hw * 0.12, 0, TAU); ctx.fill();
    }
  };
  PROPS.lighthouse = {
    box: function (p) { return [p.i, p.j, p.z, 1, 1, 3.6]; },
    paint: function (ctx, I, p) {
      var x = p.i, y = p.j, z = p.z;
      for (var k = 0; k < 4; k++) box(ctx, I, x + 0.2, y + 0.2, z + k * 0.55, 0.6, 0.6, 0.55, k % 2 ? '#e8463b' : '#f6f2ea', { noTop: k < 3, edge: true });
      box(ctx, I, x + 0.12, y + 0.12, z + 2.2, 0.76, 0.76, 0.12, '#3b4252', { studs: 2 });
      box(ctx, I, x + 0.26, y + 0.26, z + 2.32, 0.48, 0.48, 0.42, '#ffe7a3', { noTop: true });
      box(ctx, I, x + 0.2, y + 0.2, z + 2.74, 0.6, 0.6, 0.2, '#c4281c', { studs: 1, edge: true });
    },
    light: function (p) { return { x: p.i + 0.5, y: p.j + 0.5, z: p.z + 2.55, c: '#ffe7a3', r: 60 }; }
  };
  PROPS.stall = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 1.6]; },
    paint: function (ctx, I, p) {
      var x = p.i, y = p.j;
      box(ctx, I, x + 0.12, y + 0.3, 0, 0.76, 0.46, 0.56, PLANK, { edge: true });
      var f = leftFace(I, x + 0.12, y + 0.3, 0, 0.76, 0.46, 0.56);
      onFace(ctx, f, function (c) { c.fillStyle = '#ffcf3a'; c.fillRect(0.1, 0.2, 0.8, 0.32); c.fillStyle = '#e8742a'; c.fillRect(0.42, 0.26, 0.16, 0.2); });
      ctx.strokeStyle = '#7a4e2c'; ctx.lineWidth = Math.max(0.8, I.hw * 0.08);
      line(ctx, I, x + 0.14, y + 0.32, 0.5, x + 0.14, y + 0.32, 1.32); line(ctx, I, x + 0.86, y + 0.32, 0.5, x + 0.86, y + 0.32, 1.32);
      line(ctx, I, x + 0.14, y + 0.74, 0.5, x + 0.14, y + 0.74, 1.32); line(ctx, I, x + 0.86, y + 0.74, 0.5, x + 0.86, y + 0.74, 1.32);
      for (var s = 0; s < 5; s++) box(ctx, I, x + 0.04 + s * 0.184, y + 0.22, 1.32, 0.184, 0.62, 0.1, s % 2 ? '#ffffff' : '#e8463b', { edge: false });
      box(ctx, I, x + 0.3, y + 0.42, 0.56, 0.14, 0.14, 0.2, '#ffe680');
      box(ctx, I, x + 0.56, y + 0.46, 0.56, 0.08, 0.08, 0.1, '#f2f3f3');
      box(ctx, I, x + 0.68, y + 0.46, 0.56, 0.08, 0.08, 0.1, '#f2f3f3');
    }
  };
  PROPS.tent = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 1.2]; },
    paint: function (ctx, I, p) {
      var x = p.i, y = p.j, c1 = p.color || '#ff8a3d';
      ctx.fillStyle = shade(c1, 0.86);
      ctx.beginPath();
      ctx.moveTo(I.sx(x + 0.08, y + 0.5), I.sy(x + 0.08, y + 0.5, 1.0)); ctx.lineTo(I.sx(x + 0.92, y + 0.5), I.sy(x + 0.92, y + 0.5, 1.0));
      ctx.lineTo(I.sx(x + 0.92, y + 0.96), I.sy(x + 0.92, y + 0.96, 0)); ctx.lineTo(I.sx(x + 0.08, y + 0.96), I.sy(x + 0.08, y + 0.96, 0)); ctx.closePath(); ctx.fill();
      ctx.fillStyle = shade(c1, 0.66);
      ctx.beginPath();
      ctx.moveTo(I.sx(x + 0.92, y + 0.04), I.sy(x + 0.92, y + 0.04, 0)); ctx.lineTo(I.sx(x + 0.92, y + 0.5), I.sy(x + 0.92, y + 0.5, 1.0));
      ctx.lineTo(I.sx(x + 0.92, y + 0.96), I.sy(x + 0.92, y + 0.96, 0)); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#3a2a40';
      ctx.beginPath();
      ctx.moveTo(I.sx(x + 0.925, y + 0.3), I.sy(x + 0.925, y + 0.3, 0)); ctx.lineTo(I.sx(x + 0.925, y + 0.5), I.sy(x + 0.925, y + 0.5, 0.62));
      ctx.lineTo(I.sx(x + 0.925, y + 0.7), I.sy(x + 0.925, y + 0.7, 0)); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = Math.max(0.6, I.hw * 0.05);
      line(ctx, I, x + 0.08, y + 0.5, 1.0, x + 0.92, y + 0.5, 1.0);
    },
    light: function (p) { return { x: p.i + 0.9, y: p.j + 0.5, z: 0.3, c: '#ffcf7a', r: 26 }; }
  };
  PROPS.well = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 1.8]; },
    paint: function (ctx, I, p) {
      var x = p.i, y = p.j;
      box(ctx, I, x + 0.16, y + 0.16, 0, 0.68, 0.68, 0.46, '#9aa0aa', { edge: true, noTop: true });
      [leftFace(I, x + 0.16, y + 0.16, 0, 0.68, 0.68, 0.46), rightFace(I, x + 0.16, y + 0.16, 0, 0.68, 0.68, 0.46)].forEach(function (f) {
        onFace(ctx, f, function (c) { c.strokeStyle = 'rgba(0,0,0,0.2)'; c.lineWidth = 0.04; c.strokeRect(0.02, 0.02, 0.47, 0.47); c.strokeRect(0.5, 0.02, 0.48, 0.47); c.strokeRect(0.25, 0.5, 0.5, 0.48); });
      });
      box(ctx, I, x + 0.16, y + 0.16, 0.46, 0.68, 0.68, 0, '#3a6ea8', { top: '#2f5f99', noLeft: true, noRight: true });
      box(ctx, I, x + 0.24, y + 0.24, 0.46, 0.52, 0.52, 0, '#3f86c8', { noLeft: true, noRight: true });
      ctx.strokeStyle = '#7a4e2c'; ctx.lineWidth = Math.max(0.9, I.hw * 0.09);
      line(ctx, I, x + 0.2, y + 0.5, 0.46, x + 0.2, y + 0.5, 1.4); line(ctx, I, x + 0.8, y + 0.5, 0.46, x + 0.8, y + 0.5, 1.4);
      box(ctx, I, x + 0.04, y + 0.18, 1.4, 0.92, 0.32, 0.16, '#c4281c', { studs: 2, edge: true });
      box(ctx, I, x + 0.04, y + 0.5, 1.4, 0.92, 0.32, 0.16, '#a8231a', { studs: 2, edge: true });
      box(ctx, I, x + 0.43, y + 0.43, 0.75, 0.14, 0.14, 0.14, '#8b5a2b');
    }
  };
  PROPS.swing = {
    box: function (p) { return [p.i, p.j - 0.3, 0, 2, 1.6, 2.2]; },
    paint: function (ctx, I, p) {
      var x = p.i, y = p.j;
      ctx.lineCap = 'round';
      ctx.strokeStyle = '#8f1d14'; ctx.lineWidth = Math.max(1.4, I.hw * 0.16);
      [x + 0.06, x + 1.94].forEach(function (px) { line(ctx, I, px, y + 0.06, 0, px, y + 0.5, 1.7); line(ctx, I, px, y + 0.94, 0, px, y + 0.5, 1.7); });
      ctx.strokeStyle = '#e8463b'; ctx.lineWidth = Math.max(1, I.hw * 0.11);
      [x + 0.06, x + 1.94].forEach(function (px) { line(ctx, I, px, y + 0.06, 0, px, y + 0.5, 1.7); line(ctx, I, px, y + 0.94, 0, px, y + 0.5, 1.7); });
      ctx.strokeStyle = '#0a4f86'; ctx.lineWidth = Math.max(1.6, I.hw * 0.17);
      line(ctx, I, x + 0.06, y + 0.5, 1.7, x + 1.94, y + 0.5, 1.7);
      ctx.strokeStyle = '#3c8dde'; ctx.lineWidth = Math.max(1, I.hw * 0.1);
      line(ctx, I, x + 0.06, y + 0.5, 1.72, x + 1.94, y + 0.5, 1.72);
    },
    anim: function (ctx, I, p, w, t) {
      for (var s = 0; s < 2; s++) {
        var spot = p.spots[s], kid = spot.kid && spot.kid.ride === p ? spot.kid : null;
        var amp = kid ? 0.62 : 0.07, th = amp * Math.sin(t * (kid ? 2.5 : 1.3) + s * 1.7 + p.seed * 9);
        var sx = p.i + 0.5 + s, sy = p.j + 0.5 + Math.sin(th) * 1.08, sz = 1.68 - Math.cos(th) * 1.08;
        ctx.strokeStyle = 'rgba(70,60,60,0.85)'; ctx.lineWidth = Math.max(0.6, I.hw * 0.05);
        line(ctx, I, sx - 0.16, p.j + 0.5, 1.68, sx - 0.16, sy, sz + 0.03);
        line(ctx, I, sx + 0.16, p.j + 0.5, 1.68, sx + 0.16, sy, sz + 0.03);
        box(ctx, I, sx - 0.2, sy - 0.08, sz, 0.4, 0.16, 0.05, '#ffcf3a');
        if (kid) { kid.x = sx; kid.y = sy - 0.02; kid.z = sz + 0.03; kid.dir = 1; drawKid(ctx, I, kid, t, w); }
      }
    }
  };
  PROPS.slide = {
    box: function (p) { return [p.i, p.j - 0.2, 0, 1, 2.4, 2.4]; },
    paint: function (ctx, I, p) {
      var x = p.i, y = p.j;
      ctx.lineCap = 'round';
      ctx.strokeStyle = '#0a4f86'; ctx.lineWidth = Math.max(1, I.hw * 0.1);
      line(ctx, I, x + 0.28, y + 0.08, 0, x + 0.28, y + 0.08, 1.55); line(ctx, I, x + 0.72, y + 0.08, 0, x + 0.72, y + 0.08, 1.55);
      ctx.lineWidth = Math.max(0.7, I.hw * 0.06);
      for (var r = 1; r <= 5; r++) line(ctx, I, x + 0.28, y + 0.08, r * 0.24, x + 0.72, y + 0.08, r * 0.24);
      ctx.strokeStyle = '#8a95a8'; ctx.lineWidth = Math.max(1, I.hw * 0.09);
      line(ctx, I, x + 0.3, y + 0.55, 0, x + 0.3, y + 0.55, 1.2); line(ctx, I, x + 0.7, y + 0.55, 0, x + 0.7, y + 0.55, 1.2);
      box(ctx, I, x + 0.22, y + 0.06, 1.18, 0.56, 0.52, 0.1, '#3c8dde', { studs: 2, edge: true });
      ctx.strokeStyle = '#ffcf3a'; ctx.lineWidth = Math.max(0.8, I.hw * 0.07);
      line(ctx, I, x + 0.24, y + 0.1, 1.28, x + 0.24, y + 0.1, 1.62); line(ctx, I, x + 0.76, y + 0.1, 1.28, x + 0.76, y + 0.1, 1.62);
      line(ctx, I, x + 0.24, y + 0.1, 1.62, x + 0.76, y + 0.1, 1.62);
      var a1 = [x + 0.28, y + 0.58, 1.2], a2 = [x + 0.72, y + 0.58, 1.2], b1 = [x + 0.28, y + 1.96, 0.06], b2 = [x + 0.72, y + 1.96, 0.06];
      ctx.fillStyle = '#e8463b';
      ctx.beginPath(); ctx.moveTo(I.sx(a1[0], a1[1]), I.sy(a1[0], a1[1], a1[2])); ctx.lineTo(I.sx(a2[0], a2[1]), I.sy(a2[0], a2[1], a2[2]));
      ctx.lineTo(I.sx(b2[0], b2[1]), I.sy(b2[0], b2[1], b2[2])); ctx.lineTo(I.sx(b1[0], b1[1]), I.sy(b1[0], b1[1], b1[2])); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = '#9b1c13'; ctx.lineWidth = Math.max(1, I.hw * 0.1);
      line(ctx, I, a1[0], a1[1], a1[2] + 0.12, b1[0], b1[1], b1[2] + 0.12); line(ctx, I, a2[0], a2[1], a2[2] + 0.12, b2[0], b2[1], b2[2] + 0.12);
      ctx.strokeStyle = 'rgba(255,255,255,0.45)'; ctx.lineWidth = Math.max(0.6, I.hw * 0.05);
      line(ctx, I, x + 0.5, y + 0.62, 1.18, x + 0.5, y + 1.9, 0.08);
    },
    anim: function (ctx, I, p, w, t) {
      var kid = p.rider;
      if (kid && kid.ride === p) drawKid(ctx, I, kid, t, w);
    }
  };
  PROPS.seesaw = {
    box: function (p) { return [p.i - 0.2, p.j, 0, 2.4, 1, 1.6]; },
    paint: function (ctx, I, p) {
      box(ctx, I, p.i + 0.88, p.j + 0.4, 0, 0.24, 0.2, 0.34, '#e8463b', { studs: 1, edge: true });
    },
    anim: function (ctx, I, p, w, t) {
      var k0 = p.spots[0].kid, k1 = p.spots[1].kid;
      var both = k0 && k1 && k0.ride === p && k1.ride === p;
      var target = both ? 0.3 * Math.sin(t * 2.3) : (k0 && k0.ride === p ? -0.3 : (k1 && k1.ride === p ? 0.3 : -0.3));
      p.phi = p.phi === undefined ? target : lerp(p.phi, target, Math.min(1, w.dt * 6));
      var cx = p.i + 1, cy = p.j + 0.5, cz = 0.38, L = 0.95, c = Math.cos(p.phi), s = Math.sin(p.phi);
      var e0 = [cx - L * c, cz - L * s], e1 = [cx + L * c, cz + L * s];
      if (k0 && k0.ride === p) { k0.x = e0[0] + 0.12 * c; k0.y = cy; k0.z = e0[1] + 0.05; k0.dir = 0; drawKid(ctx, I, k0, t, w); }
      ctx.fillStyle = '#ffcf3a';
      ctx.beginPath();
      ctx.moveTo(I.sx(e0[0], cy - 0.11), I.sy(e0[0], cy - 0.11, e0[1])); ctx.lineTo(I.sx(e1[0], cy - 0.11), I.sy(e1[0], cy - 0.11, e1[1]));
      ctx.lineTo(I.sx(e1[0], cy + 0.11), I.sy(e1[0], cy + 0.11, e1[1])); ctx.lineTo(I.sx(e0[0], cy + 0.11), I.sy(e0[0], cy + 0.11, e0[1])); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#d9a514';
      ctx.beginPath();
      ctx.moveTo(I.sx(e0[0], cy + 0.11), I.sy(e0[0], cy + 0.11, e0[1])); ctx.lineTo(I.sx(e1[0], cy + 0.11), I.sy(e1[0], cy + 0.11, e1[1]));
      ctx.lineTo(I.sx(e1[0], cy + 0.11), I.sy(e1[0], cy + 0.11, e1[1] - 0.08)); ctx.lineTo(I.sx(e0[0], cy + 0.11), I.sy(e0[0], cy + 0.11, e0[1] - 0.08)); ctx.closePath(); ctx.fill();
      if (k1 && k1.ride === p) { k1.x = e1[0] - 0.12 * c; k1.y = cy; k1.z = e1[1] + 0.05; k1.dir = 2; drawKid(ctx, I, k1, t, w); }
    }
  };
  PROPS.fire = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 1.2]; },
    paint: function (ctx, I, p) {
      var x = p.i + 0.5, y = p.j + 0.5;
      for (var k = 0; k < 7; k++) {
        var a = k / 7 * TAU;
        box(ctx, I, x + Math.cos(a) * 0.32 - 0.07, y + Math.sin(a) * 0.32 - 0.07, 0, 0.14, 0.14, 0.12, '#9aa0aa');
      }
      box(ctx, I, x - 0.26, y - 0.06, 0.02, 0.52, 0.12, 0.1, '#6e4426');
      box(ctx, I, x - 0.06, y - 0.26, 0.02, 0.12, 0.52, 0.1, '#7d4f2c');
    },
    anim: function (ctx, I, p, w, t) {
      var sx = I.sx(p.i + 0.5, p.j + 0.5), sy = I.sy(p.i + 0.5, p.j + 0.5, 0.12), s = I.hw;
      var boost = 1 + (p.boost || 0);
      if (p.boost) p.boost = Math.max(0, p.boost - w.dt);
      var layers = [['#ff6a1c', 0.5], ['#ffb02e', 0.36], ['#fff1a6', 0.2]];
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      for (var k = 0; k < 3; k++) {
        var c = layers[k], h = s * (0.95 - k * 0.22) * boost * (1 + 0.14 * Math.sin(t * 13 + k * 2)), wd = s * c[1];
        ctx.fillStyle = c[0];
        ctx.beginPath();
        ctx.moveTo(sx - wd, sy);
        ctx.quadraticCurveTo(sx - wd * 0.9, sy - h * 0.5, sx + Math.sin(t * 7 + k) * wd * 0.35, sy - h);
        ctx.quadraticCurveTo(sx + wd * 0.9, sy - h * 0.5, sx + wd, sy);
        ctx.closePath(); ctx.fill();
      }
      ctx.restore();
      if (Math.random() < w.dt * 6 * boost) w.spark(p.i + 0.5, p.j + 0.5, 0.5);
    },
    light: function (p) { return { x: p.i + 0.5, y: p.j + 0.5, z: 0.4, c: '#ffa14a', r: 70, flicker: true }; }
  };
  PROPS.log = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 0.4]; },
    paint: function (ctx, I, p) {
      var along = p.along === 'x';
      if (along) box(ctx, I, p.i + 0.12, p.j + 0.36, 0, 0.76, 0.28, 0.24, '#7d4f2c', { edge: true });
      else box(ctx, I, p.i + 0.36, p.j + 0.12, 0, 0.28, 0.76, 0.24, '#7d4f2c', { edge: true });
      var f = along ? rightFace(I, p.i + 0.12, p.j + 0.36, 0, 0.76, 0.28, 0.24) : leftFace(I, p.i + 0.36, p.j + 0.12, 0, 0.28, 0.76, 0.24);
      onFace(ctx, f, function (c) { c.fillStyle = '#d8b07a'; c.beginPath(); c.ellipse(0.5, 0.5, 0.36, 0.36, 0, 0, TAU); c.fill(); c.strokeStyle = '#a77b4a'; c.lineWidth = 0.06; c.beginPath(); c.ellipse(0.5, 0.5, 0.18, 0.18, 0, 0, TAU); c.stroke(); });
    }
  };
  PROPS.build = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 1.6]; },
    paint: function (ctx, I, p) {
      box(ctx, I, p.i + 0.05, p.j + 0.05, 0, 0.9, 0.9, 0.06, '#9da3ad', { studs: 4, edge: true });
    },
    anim: function (ctx, I, p, w, t) {
      var b = p.bricks;
      for (var k = 0; k < b.length; k++) {
        var br = b[k], age = t - br.t0, sc = backOut(age / 0.45);
        if (br.out) { sc = 1 - smooth((t - br.out) / 0.5); if (sc <= 0) continue; }
        var cx = p.i + 0.07 + br.a * 0.43 + 0.2, cy = p.j + 0.07 + br.b * 0.43 + 0.2, z = 0.06 + br.l * 0.27 + (br.out ? (t - br.out) * 1.4 : 0);
        var s = 0.4 * sc;
        box(ctx, I, cx - s / 2, cy - s / 2, z, s, s, 0.27 * sc, br.c, { studs: 2.6 });
      }
    }
  };
  PROPS.boombox = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 0.8]; },
    paint: function (ctx, I, p) {
      box(ctx, I, p.i + 0.2, p.j + 0.36, 0, 0.6, 0.3, 0.36, '#2b2f3a', { edge: true });
      ctx.strokeStyle = '#8a95a8'; ctx.lineWidth = Math.max(0.7, I.hw * 0.06);
      line(ctx, I, p.i + 0.3, p.j + 0.5, 0.36, p.i + 0.3, p.j + 0.5, 0.5); line(ctx, I, p.i + 0.7, p.j + 0.5, 0.36, p.i + 0.7, p.j + 0.5, 0.5);
      line(ctx, I, p.i + 0.3, p.j + 0.5, 0.5, p.i + 0.7, p.j + 0.5, 0.5);
    },
    anim: function (ctx, I, p, w, t) {
      var f = leftFace(I, p.i + 0.2, p.j + 0.36, 0, 0.6, 0.3, 0.36), beat = p.playing ? 0.06 * Math.abs(Math.sin(t * 9)) : 0;
      onFace(ctx, f, function (c) {
        c.fillStyle = '#596173';
        c.beginPath(); c.ellipse(0.24, 0.55, 0.15 + beat, 0.3 + beat * 2, 0, 0, TAU); c.fill();
        c.beginPath(); c.ellipse(0.76, 0.55, 0.15 + beat, 0.3 + beat * 2, 0, 0, TAU); c.fill();
        c.fillStyle = p.playing ? '#7fe7ff' : '#3b4252'; c.fillRect(0.42, 0.25, 0.16, 0.16);
      });
      if (p.playing && Math.random() < w.dt * 2.2) w.note(p.i + 0.5, p.j + 0.5, 0.6);
    }
  };
  PROPS.flag = {
    box: function (p) { return [p.i - 0.2, p.j - 0.2, 0, 1.6, 1.6, 3]; },
    paint: function (ctx, I, p) {
      box(ctx, I, p.i + 0.38, p.j + 0.38, 0, 0.24, 0.24, 0.14, '#9aa0aa', { edge: true });
      box(ctx, I, p.i + 0.46, p.j + 0.46, 0.14, 0.08, 0.08, 2.5, '#dfe3e8');
      box(ctx, I, p.i + 0.43, p.j + 0.43, 2.64, 0.14, 0.14, 0.12, '#ffcf3a');
    },
    anim: function (ctx, I, p, w, t) {
      var alongX = p.face !== 'left', pts = [], N = 7, len = 0.95;
      for (var s = 0; s <= N; s++) {
        var u = s / N, wave = Math.sin(t * 4.2 - u * 5) * 0.09 * u, x, y;
        x = alongX ? p.i + 0.54 + u * len : p.i + 0.5 + wave;
        y = alongX ? p.j + 0.5 + wave : p.j + 0.54 + u * len;
        pts.push([x, y, Math.sin(t * 3.6 - u * 4) * 0.05 * u]);
      }
      ctx.fillStyle = '#2b67f6';
      ctx.beginPath();
      for (s = 0; s <= N; s++) { var q = pts[s]; if (s) ctx.lineTo(I.sx(q[0], q[1]), I.sy(q[0], q[1], 2.62 + q[2])); else ctx.moveTo(I.sx(q[0], q[1]), I.sy(q[0], q[1], 2.62 + q[2])); }
      for (s = N; s >= 0; s--) { q = pts[s]; ctx.lineTo(I.sx(q[0], q[1]), I.sy(q[0], q[1], 2.0 + q[2])); }
      ctx.closePath(); ctx.fill();
      var m = pts[4];
      ctx.fillStyle = '#ffffff';
      shieldPath(ctx, I.sx(m[0], m[1]), I.sy(m[0], m[1], 2.31 + m[2]), I.hw * 0.17);
      ctx.fill();
    }
  };
  PROPS.lamp = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 1.9]; },
    paint: function (ctx, I, p) {
      box(ctx, I, p.i + 0.4, p.j + 0.4, 0, 0.2, 0.2, 0.1, '#3b4252');
      box(ctx, I, p.i + 0.46, p.j + 0.46, 0.1, 0.08, 0.08, 1.24, '#2e3440');
      box(ctx, I, p.i + 0.36, p.j + 0.36, 1.34, 0.28, 0.28, 0.3, '#ffe7a3', { noTop: true });
      box(ctx, I, p.i + 0.33, p.j + 0.33, 1.64, 0.34, 0.34, 0.08, '#2e3440', { studs: 1 });
    },
    light: function (p) { return { x: p.i + 0.5, y: p.j + 0.5, z: 1.5, c: '#ffd98a', r: 44 }; }
  };
  PROPS.dock = {
    box: function (p) { return [p.i, p.j, -0.4, 2.2, 2.2, 0.6]; },
    paint: function (ctx, I, p) {
      var x = p.i, y = p.j;
      if (p.dir === 0) {
        box(ctx, I, x + 1.1, y + 0.26, -0.7, 0.1, 0.1, 0.62, '#5b3a29'); box(ctx, I, x + 1.1, y + 0.64, -0.7, 0.1, 0.1, 0.62, '#5b3a29');
        box(ctx, I, x + 0.5, y + 0.22, -0.12, 1.12, 0.56, 0.12, PLANK, { edge: true });
        onFace(ctx, topFace(I, x + 0.5, y + 0.22, 0, 1.12, 0.56), function (c) { c.fillStyle = 'rgba(80,45,20,0.35)'; for (var k = 1; k < 6; k++) c.fillRect(k / 6, 0, 0.02, 1); });
      } else {
        box(ctx, I, x + 0.26, y + 1.1, -0.7, 0.1, 0.1, 0.62, '#5b3a29'); box(ctx, I, x + 0.64, y + 1.1, -0.7, 0.1, 0.1, 0.62, '#5b3a29');
        box(ctx, I, x + 0.22, y + 0.5, -0.12, 0.56, 1.12, 0.12, PLANK, { edge: true });
        onFace(ctx, topFace(I, x + 0.22, y + 0.5, 0, 0.56, 1.12), function (c) { c.fillStyle = 'rgba(80,45,20,0.35)'; for (var k = 1; k < 6; k++) c.fillRect(0, k / 6, 1, 0.02); });
      }
    }
  };
  PROPS.rock = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 0.8]; },
    paint: function (ctx, I, p) {
      var a = p.seed;
      box(ctx, I, p.i + 0.14, p.j + 0.2, 0, 0.62, 0.56, 0.32, '#8e95a3', { studs: 1.6, edge: true });
      box(ctx, I, p.i + 0.36 + a * 0.1, p.j + 0.3, 0.32, 0.34, 0.34, 0.22, '#a3a9b5', { studs: 1, edge: true, top: a > 0.5 ? '#79b45a' : null });
    }
  };
  PROPS.mushroom = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 0.6]; },
    paint: function (ctx, I, p) {
      var x = p.i + 0.3 + p.seed * 0.3, y = p.j + 0.35;
      box(ctx, I, x, y, 0, 0.12, 0.12, 0.2, '#f4ead8');
      box(ctx, I, x - 0.1, y - 0.1, 0.2, 0.32, 0.32, 0.14, '#e8463b', { studs: 2.2 });
    }
  };
  PROPS.pumpkin = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 0.7]; },
    paint: function (ctx, I, p) {
      var x = p.i + 0.24, y = p.j + 0.24;
      box(ctx, I, x, y, 0, 0.5, 0.5, 0.36, '#f07f1b', { edge: true });
      [leftFace(I, x, y, 0, 0.5, 0.5, 0.36), rightFace(I, x, y, 0, 0.5, 0.5, 0.36)].forEach(function (f) {
        onFace(ctx, f, function (c) { c.fillStyle = 'rgba(150,60,0,0.3)'; c.fillRect(0.3, 0, 0.05, 1); c.fillRect(0.65, 0, 0.05, 1); });
      });
      box(ctx, I, x + 0.21, y + 0.21, 0.36, 0.08, 0.08, 0.12, '#4f7a2a');
    }
  };
  PROPS.hay = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 0.6]; },
    paint: function (ctx, I, p) {
      box(ctx, I, p.i + 0.1, p.j + 0.2, 0, 0.8, 0.6, 0.42, '#e3c158', { edge: true });
      [leftFace(I, p.i + 0.1, p.j + 0.2, 0, 0.8, 0.6, 0.42), rightFace(I, p.i + 0.1, p.j + 0.2, 0, 0.8, 0.6, 0.42)].forEach(function (f) {
        onFace(ctx, f, function (c) { c.fillStyle = 'rgba(150,100,20,0.35)'; c.fillRect(0, 0.3, 1, 0.06); c.fillRect(0, 0.68, 1, 0.06); });
      });
    }
  };
  PROPS.sunflower = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 1.6]; },
    paint: function (ctx, I, p) {
      for (var k = 0; k < 2; k++) {
        var x = p.i + 0.3 + k * 0.38, y = p.j + 0.4 + k * 0.2, h = 0.9 + k * 0.25;
        box(ctx, I, x, y, 0, 0.06, 0.06, h, '#4f8a32');
        var sx = I.sx(x + 0.03, y + 0.03), sy = I.sy(x + 0.03, y + 0.03, h + 0.15);
        ctx.fillStyle = '#ffcf3a';
        for (var a = 0; a < 10; a++) { ctx.beginPath(); ctx.ellipse(sx + Math.cos(a / 10 * TAU) * I.hw * 0.17, sy + Math.sin(a / 10 * TAU) * I.hw * 0.17, I.hw * 0.08, I.hw * 0.05, a / 10 * TAU, 0, TAU); ctx.fill(); }
        ctx.fillStyle = '#6b3f22'; ctx.beginPath(); ctx.arc(sx, sy, I.hw * 0.11, 0, TAU); ctx.fill();
      }
    }
  };
  PROPS.snowman = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 1.5]; },
    paint: function (ctx, I, p) {
      var x = p.i + 0.5, y = p.j + 0.5;
      box(ctx, I, x - 0.3, y - 0.3, 0, 0.6, 0.6, 0.5, '#f6f9ff', { edge: true, studs: 1.6 });
      box(ctx, I, x - 0.22, y - 0.22, 0.5, 0.44, 0.44, 0.4, '#ffffff', { edge: true });
      box(ctx, I, x - 0.24, y - 0.24, 0.72, 0.48, 0.48, 0.08, '#e8463b');
      box(ctx, I, x - 0.16, y - 0.16, 0.9, 0.32, 0.32, 0.32, '#ffffff', { edge: true });
      box(ctx, I, x - 0.18, y - 0.18, 1.22, 0.36, 0.36, 0.06, '#1b2a35');
      box(ctx, I, x - 0.11, y - 0.11, 1.28, 0.22, 0.22, 0.2, '#1b2a35', { studs: 1 });
      var f = leftFace(I, x - 0.16, y - 0.16, 0.9, 0.32, 0.32, 0.32);
      onFace(ctx, f, function (c) { c.fillStyle = '#1b2a35'; c.fillRect(0.25, 0.3, 0.12, 0.12); c.fillRect(0.63, 0.3, 0.12, 0.12); c.fillStyle = '#ff8a3d'; c.fillRect(0.44, 0.52, 0.12, 0.1); });
    }
  };
  PROPS.bench = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 0.6]; },
    paint: function (ctx, I, p) {
      var along = p.along === 'x';
      var x = p.i + (along ? 0.1 : 0.32), y = p.j + (along ? 0.32 : 0.1), w = along ? 0.8 : 0.36, d = along ? 0.36 : 0.8;
      box(ctx, I, x + 0.02, y + 0.02, 0, 0.08, 0.08, 0.22, '#3b4252'); box(ctx, I, x + w - 0.1, y + d - 0.1, 0, 0.08, 0.08, 0.22, '#3b4252');
      box(ctx, I, x, y, 0.22, w, d, 0.07, PLANK, { edge: true });
      if (along) box(ctx, I, x, y, 0.29, w, 0.07, 0.24, shade(PLANK, 0.92)); else box(ctx, I, x, y, 0.29, 0.07, d, 0.24, shade(PLANK, 0.92));
    }
  };
  PROPS.mailbox = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 1]; },
    paint: function (ctx, I, p) {
      box(ctx, I, p.i + 0.46, p.j + 0.46, 0, 0.08, 0.08, 0.6, '#7a4e2c');
      box(ctx, I, p.i + 0.34, p.j + 0.4, 0.6, 0.32, 0.2, 0.2, '#3c8dde', { studs: 1, edge: true });
      box(ctx, I, p.i + 0.62, p.j + 0.42, 0.72, 0.03, 0.03, 0.16, '#e8463b');
    }
  };
  PROPS.hedge = {
    box: function (p) { return [p.i, p.j, 0, 1, 1, 0.6]; },
    paint: function (ctx, I, p, w) {
      var s = p.side, c = w.S.snow ? '#3a7d50' : '#3f9a4b';
      var o = { studs: 2, edge: true, top: w.S.snow ? '#f6f9ff' : null };
      if (s === 'y') box(ctx, I, p.i, p.j + 0.72, 0, 1, 0.26, 0.38, c, o);
      else if (s === 'x') box(ctx, I, p.i + 0.72, p.j, 0, 0.26, 1, 0.38, c, o);
      else if (s === '-y') box(ctx, I, p.i, p.j + 0.02, 0, 1, 0.26, 0.38, c, o);
      else box(ctx, I, p.i + 0.02, p.j, 0, 0.26, 1, 0.38, c, o);
    }
  };
  PROPS.litpine = {
    box: function (p) { return [p.i - 0.1, p.j - 0.1, 0, 1.2, 1.2, 2.8]; },
    paint: function (ctx, I, p, w) { PROPS.tree.paint(ctx, I, { i: p.i, j: p.j, z: 0, leaf: '#2e7a4c', kind: 'pine' }, w); },
    anim: function (ctx, I, p, w, t) {
      var cols = ['#ff5a5f', '#ffd23f', '#7fe7ff', '#8af0b6', '#ff8fd6'];
      for (var k = 0; k < 12; k++) {
        var tier = k % 3, a = k * 1.7, r = 0.38 - tier * 0.11;
        var x = p.i + 0.5 + Math.cos(a) * r, y = p.j + 0.5 + Math.abs(Math.sin(a)) * r, z = 0.6 + tier * 0.46;
        var on = 0.5 + 0.5 * Math.sin(t * 3 + k * 1.3);
        ctx.fillStyle = rgba(cols[k % cols.length], 0.35 + on * 0.65);
        ctx.beginPath(); ctx.arc(I.sx(x, y), I.sy(x, y, z), I.hw * 0.06, 0, TAU); ctx.fill();
      }
      ctx.fillStyle = '#ffd23f';
      starPath(ctx, I.sx(p.i + 0.5, p.j + 0.5), I.sy(p.i + 0.5, p.j + 0.5, 2.35), I.hw * 0.16);
      ctx.fill();
    }
  };
  PROPS.sign = {
    box: function (p) { return [p.i - 0.6, p.j, 0, 2.2, 1, 1.6]; },
    paint: function (ctx, I, p) {
      box(ctx, I, p.i + 0.46, p.j + 0.5, 0, 0.09, 0.09, 0.78, '#7a4e2c');
      box(ctx, I, p.i - 0.45, p.j + 0.44, 0.7, 1.9, 0.12, 0.62, '#fff6e2', { edge: true, studs: 3 });
      box(ctx, I, p.i - 0.49, p.j + 0.42, 1.32, 1.98, 0.16, 0.08, '#c98b4f', { studs: 3 });
    },
    anim: function (ctx, I, p, w) {
      var f = leftFace(I, p.i - 0.45, p.j + 0.44, 0.7, 1.9, 0.12, 0.62);
      var cx = (f[0] + f[2]) / 2, cy = (f[1] + f[3]) / 2 + (f[5] - f[1]) * 0.5;
      ctx.save();
      ctx.translate(cx, cy);
      ctx.transform(1, (f[3] - f[1]) / (f[2] - f[0]), 0, 1, 0, 0);
      var text = w.name || 'Your name here', size = I.hw * 0.72;
      ctx.font = '800 ' + size.toFixed(1) + 'px ' + w.font;
      var tw = ctx.measureText(text).width, max = (f[2] - f[0]) * 0.86;
      if (tw > max) { size *= max / tw; ctx.font = '800 ' + size.toFixed(1) + 'px ' + w.font; }
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillStyle = '#5a3b22';
      ctx.fillText(text, 0, 0);
      ctx.restore();
      if (w.stage >= 4) {
        // their own lock, floating over their name
        var k = backOut((w.t - (w.stageAt[4] || 0)) / 0.6);
        var lx = I.sx(p.i + 0.5, p.j + 0.5), ly = I.sy(p.i + 0.5, p.j + 0.5, 2.05) + Math.sin(w.t * 2.2) * 2.2, s = I.hw * 0.46 * k;
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        ctx.globalAlpha = 0.55 * k;
        ctx.drawImage(glow('#ffd66b'), lx - s * 2.2, ly - s * 2.2, s * 4.4, s * 4.4);
        ctx.restore();
        ctx.strokeStyle = '#c28100'; ctx.lineWidth = s * 0.26; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.arc(lx, ly - s * 0.25, s * 0.4, Math.PI, 0); ctx.stroke();
        ctx.fillStyle = '#ffbf1f';
        roundRect(ctx, lx - s * 0.62, ly - s * 0.25, s * 1.24, s * 0.95, s * 0.22); ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.45)';
        roundRect(ctx, lx - s * 0.5, ly - s * 0.17, s * 0.42, s * 0.2, s * 0.08); ctx.fill();
        ctx.fillStyle = '#7a4e00';
        ctx.beginPath(); ctx.arc(lx, ly + s * 0.16, s * 0.14, 0, TAU); ctx.fill();
        ctx.fillRect(lx - s * 0.05, ly + s * 0.18, s * 0.1, s * 0.26);
        var tw = (w.t * 0.8) % 1;
        if (tw < 0.4) {
          ctx.fillStyle = 'rgba(255,255,255,' + (1 - tw / 0.4).toFixed(3) + ')';
          starPath(ctx, lx + s * 0.55, ly - s * 0.55, s * 0.22 * (0.5 + tw));
          ctx.fill();
        }
      }
    }
  };

  /* ============================================================== kids */
  var POOL = [];
  function part(n) { if (!POOL[n]) POOL[n] = {}; return POOL[n]; }
  function setPart(o, x, y, z, w, d, h, c, flags) { o.x = x; o.y = y; o.z = z; o.w = w; o.d = d; o.h = h; o.c = c; o.f = flags || 0; return o; }
  /* a part centred on (cx, cy): D is its depth along the facing, W its width */
  function oriented(o, k, cx, cy, z, D, W, h, c, flags) {
    var alongX = DX[k.dir] !== 0;
    var w = alongX ? D : W, d = alongX ? W : D;
    return setPart(o, cx - w / 2, cy - d / 2, z, w, d, h, c, flags);
  }
  var KID_PARTS = [];
  function drawKid(ctx, I, k, t, w) {
    if (!k.visible) return;
    var s = k.scale * (k.pop === undefined ? 1 : k.pop);
    if (s <= 0.02) return;
    var x = k.x, y = k.y, z = k.z + k.jz, dir = k.dir;
    var fx = DX[dir], fy = DY[dir], px = -fy, py = fx;
    var legH = 0.4 * s, bodyH = 0.44 * s, head = 0.36 * s, bodyW = 0.4 * s, bodyD = 0.22 * s, limb = 0.14 * s, armH = 0.4 * s;
    var walk = k.moving ? Math.sin(k.phase) : 0;
    var bob = k.moving ? Math.abs(Math.sin(k.phase)) * 0.035 * s : Math.sin(t * 2 + k.seed * 9) * 0.008;
    var pose = k.pose, n = 0, P = KID_PARTS;
    P.length = 0;
    // shadow on the ground under them
    if (k.z <= 0.05) {
      var gx = I.sx(x, y), gy = I.sy(x, y, k.z);
      ctx.fillStyle = 'rgba(20,30,60,' + (0.22 / (1 + k.jz * 2)).toFixed(3) + ')';
      ctx.beginPath(); ctx.ellipse(gx, gy, I.hw * 0.34 * s, I.hw * 0.17 * s, 0, 0, TAU); ctx.fill();
    }
    var hip = z + legH, sitting = pose === 'sit' || pose === 'sitFlat';
    if (sitting) hip = z + 0.06 * s;
    // legs
    for (var sd = -1; sd <= 1; sd += 2) {
      var lx = x + px * sd * 0.1 * s, ly = y + py * sd * 0.1 * s;
      if (sitting) {
        P.push(oriented(part(n++), k, lx + fx * 0.2 * s, ly + fy * 0.2 * s, hip - 0.02 * s, 0.38 * s, limb, limb, k.pants, 0));
        if (pose === 'sit') {
          var dangle = Math.sin(t * 3 + sd + k.seed * 5) * 0.04 * s;
          P.push(oriented(part(n++), k, lx + fx * (0.36 * s + dangle), ly + fy * (0.36 * s + dangle), hip - 0.32 * s, limb, limb, 0.32 * s, k.pants, 1));
        }
      } else {
        var sw = walk * sd * 0.12 * s, lift = Math.max(0, walk * sd) * 0.06 * s;
        if (pose === 'climb') { sw = 0; lift = Math.max(0, Math.sin(t * 9 + sd)) * 0.08 * s; }
        if (pose === 'dance') { lift = Math.max(0, Math.sin(t * 8 + sd * 1.6)) * 0.08 * s; }
        P.push(oriented(part(n++), k, lx + fx * sw, ly + fy * sw, z + lift, limb, limb, legH - lift, k.pants, 1));
      }
    }
    var torsoZ = hip + bob;
    var torso = oriented(part(n++), k, x, y, torsoZ, bodyD, bodyW, bodyH, k.shirt, 2);
    P.push(torso);
    // arms
    for (sd = -1; sd <= 1; sd += 2) {
      var ax = x + px * sd * (bodyW / 2 + limb / 2), ay = y + py * sd * (bodyW / 2 + limb / 2);
      var up = false, fwd = 0, az = torsoZ + bodyH - armH;
      if (pose === 'cheer' || pose === 'slideDown' || (pose === 'dance' && (Math.sin(t * 4 + sd) > 0))) up = true;
      if (pose === 'climb') up = Math.sin(t * 9 + sd) > -0.2;
      if ((k.wave > 0 || pose === 'wave') && sd === 1) up = true;
      if (pose === 'hold' && sd === 1) fwd = 0.16 * s;
      if (pose === 'roast') fwd = 0.14 * s;
      if (!up && k.moving) fwd = -walk * sd * 0.1 * s;
      if (up) {
        az = torsoZ + bodyH - 0.06 * s;
        var wig = (k.wave > 0 && sd === 1) ? Math.sin(t * 14) * 0.05 * s : 0;
        ax += px * sd * 0.02 * s + fx * wig; ay += py * sd * 0.02 * s + fy * wig;
      }
      P.push(oriented(part(n++), k, ax + fx * fwd, ay + fy * fwd, az, limb, limb, armH, k.shirt, 3));
      // the hand
      var hz = up ? az + armH : az - 0.02 * s;
      P.push(oriented(part(n++), k, ax + fx * fwd, ay + fy * fwd, up ? hz : az - 0.09 * s, limb * 0.9, limb * 0.9, 0.1 * s, SKIN, 3));
      if (sd === 1) { k.hx = ax + fx * (fwd + 0.05 * s); k.hy = ay + fy * (fwd + 0.05 * s); k.hz = up ? hz + 0.05 * s : az; }
    }
    var headZ = torsoZ + bodyH;
    var hd = oriented(part(n++), k, x, y, headZ, head, head, head, SKIN, 4);
    P.push(hd);
    // order: legs, then arms/torso by depth along the screen, then head and hat
    P.sort(kidOrder);
    for (var q = 0; q < P.length; q++) {
      var o = P[q];
      box(ctx, I, o.x, o.y, o.z, o.w, o.d, o.h, o.c, o.f === 1 ? NO_TOP : (o.f === 4 ? HEAD : EMPTY));
      if (o.f === 2 && k.logo) {
        var lf = dir === 0 ? rightFace(I, o.x, o.y, o.z, o.w, o.d, o.h) : (dir === 1 ? leftFace(I, o.x, o.y, o.z, o.w, o.d, o.h) : null);
        if (lf) onFace(ctx, lf, function (c) { c.fillStyle = k.logo; c.fillRect(0.38, 0.22, 0.24, 0.24); });
      }
    }
    // face, hair, hats
    var hx0 = hd.x, hy0 = hd.y, S = hd.w;
    if (dir === 0 || dir === 1) {
      var ff = dir === 0 ? rightFace(I, hx0, hy0, headZ, S, S, S) : leftFace(I, hx0, hy0, headZ, S, S, S);
      var happy = k.jz > 0.02 || pose === 'cheer' || k.happy > 0;
      onFace(ctx, ff, function (c) {
        c.fillStyle = '#1b2a35';
        if (k.blink > 0) { c.fillRect(0.23, 0.44, 0.15, 0.04); c.fillRect(0.62, 0.44, 0.15, 0.04); } else { c.fillRect(0.25, 0.35, 0.12, 0.17); c.fillRect(0.63, 0.35, 0.12, 0.17); }
        if (happy) { c.beginPath(); c.moveTo(0.3, 0.62); c.quadraticCurveTo(0.5, 0.92, 0.7, 0.62); c.closePath(); c.fill(); }
        else { c.strokeStyle = '#1b2a35'; c.lineWidth = 0.075; c.lineCap = 'round'; c.beginPath(); c.moveTo(0.3, 0.65); c.quadraticCurveTo(0.5, 0.82, 0.7, 0.65); c.stroke(); }
        c.fillStyle = 'rgba(255,120,120,0.35)'; c.fillRect(0.1, 0.6, 0.1, 0.07); c.fillRect(0.8, 0.6, 0.1, 0.07);
      });
    }
    var top = headZ + S;
    if (k.hat === 'cap') {
      box(ctx, I, hx0 - 0.01, hy0 - 0.01, top - 0.06 * s, S + 0.02, S + 0.02, 0.09 * s, k.hatColor, EMPTY);
      if (dir === 0) box(ctx, I, hx0 + S, hy0 + 0.03, top - 0.05 * s, 0.14 * s, S - 0.06, 0.03 * s, shade(k.hatColor, 0.86), EMPTY);
      else if (dir === 1) box(ctx, I, hx0 + 0.03, hy0 + S, top - 0.05 * s, S - 0.06, 0.14 * s, 0.03 * s, shade(k.hatColor, 0.86), EMPTY);
    } else if (k.hat === 'beanie') {
      box(ctx, I, hx0 - 0.015, hy0 - 0.015, top - 0.09 * s, S + 0.03, S + 0.03, 0.15 * s, k.hatColor, EMPTY);
      box(ctx, I, hx0 + S / 2 - 0.05 * s, hy0 + S / 2 - 0.05 * s, top + 0.06 * s, 0.1 * s, 0.1 * s, 0.08 * s, '#ffffff', EMPTY);
    } else if (k.hair) {
      if (dir === 2 || dir === 3) box(ctx, I, hx0 - 0.012, hy0 - 0.012, headZ + S * 0.42, S + 0.024, S + 0.024, S * 0.62, k.hair, EMPTY);
      else box(ctx, I, hx0 - 0.012, hy0 - 0.012, top - S * 0.24, S + 0.024, S + 0.024, S * 0.3, k.hair, dir === 0 ? NO_RIGHT : NO_LEFT);
    }
    k.sx = I.sx(x, y);
    k.sy = I.sy(x, y, top + 0.12 * s);
  }
  var NO_TOP = { noTop: true }, NO_RIGHT = { noRight: true }, NO_LEFT = { noLeft: true }, HEAD = { edge: false };
  function kidOrder(a, b) {
    if (a.f === 1 && b.f !== 1) return -1;
    if (b.f === 1 && a.f !== 1) return 1;
    if (a.f === 4 && b.f !== 4) return 1;
    if (b.f === 4 && a.f !== 4) return -1;
    var da = a.x + a.w / 2 + a.y + a.d / 2, db = b.x + b.w / 2 + b.y + b.d / 2;
    if (Math.abs(da - db) > 0.01) return da - db;
    return a.z - b.z;
  }

  /* ================================================= dogs, cats, ducks */
  function drawDog(ctx, I, d, t) {
    var k = { dir: d.dir };
    var x = d.x, y = d.y, fx = DX[d.dir], fy = DY[d.dir], px = -fy, py = fx, c = d.color, hop = d.jz || 0;
    ctx.fillStyle = 'rgba(20,30,60,0.2)';
    ctx.beginPath(); ctx.ellipse(I.sx(x, y), I.sy(x, y, 0), I.hw * 0.3, I.hw * 0.15, 0, 0, TAU); ctx.fill();
    var step = d.moving ? Math.sin(d.phase) * 0.05 : 0, parts = [];
    for (var a = -1; a <= 1; a += 2) for (var b = -1; b <= 1; b += 2) {
      parts.push(oriented({}, k, x + fx * a * 0.13 + px * b * 0.07 + fx * step * a * b, y + fy * a * 0.13 + py * b * 0.07 + fy * step * a * b, hop, 0.07, 0.07, 0.16, shade(c, 0.85), 1));
    }
    parts.push(oriented({}, k, x, y, hop + 0.16, 0.42, 0.2, 0.17, c, 2));
    parts.push(oriented({}, k, x + fx * 0.25, y + fy * 0.25, hop + 0.26, 0.18, 0.18, 0.17, c, 4));
    var wag = Math.sin(t * (d.happy > 0 ? 26 : 10)) * 0.06;
    parts.push(oriented({}, k, x - fx * 0.24 + px * wag, y - fy * 0.24 + py * wag, hop + 0.3, 0.06, 0.06, 0.14, shade(c, 0.9), 3));
    parts.sort(kidOrder);
    for (var q = 0; q < parts.length; q++) { var o = parts[q]; box(ctx, I, o.x, o.y, o.z, o.w, o.d, o.h, o.c, o.f === 1 ? NO_TOP : EMPTY); }
    var hdp = parts.filter(function (p) { return p.f === 4; })[0];
    if (hdp) {
      box(ctx, I, hdp.x + 0.01, hdp.y + 0.01, hdp.z + hdp.h, 0.05, 0.05, 0.06, shade(c, 0.7), EMPTY);
      box(ctx, I, hdp.x + hdp.w - 0.06, hdp.y + hdp.d - 0.06, hdp.z + hdp.h, 0.05, 0.05, 0.06, shade(c, 0.7), EMPTY);
      if (d.dir === 0 || d.dir === 1) {
        var f = d.dir === 0 ? rightFace(I, hdp.x, hdp.y, hdp.z, hdp.w, hdp.d, hdp.h) : leftFace(I, hdp.x, hdp.y, hdp.z, hdp.w, hdp.d, hdp.h);
        onFace(ctx, f, function (c2) { c2.fillStyle = '#1b2a35'; c2.fillRect(0.22, 0.3, 0.15, 0.18); c2.fillRect(0.63, 0.3, 0.15, 0.18); c2.fillRect(0.42, 0.6, 0.16, 0.14); });
      }
    }
  }
  function drawCat(ctx, I, c, t) {
    var x = c.x, y = c.y, z = c.z || 0, col = c.color;
    ctx.fillStyle = 'rgba(20,30,60,0.18)';
    if (!z) { ctx.beginPath(); ctx.ellipse(I.sx(x, y), I.sy(x, y, z), I.hw * 0.22, I.hw * 0.11, 0, 0, TAU); ctx.fill(); }
    box(ctx, I, x - 0.15, y - 0.1, z, 0.3, 0.2, 0.14, col, { studs: 0 });
    box(ctx, I, x + 0.06, y - 0.08, z + 0.1, 0.15, 0.15, 0.13, col);
    box(ctx, I, x + 0.07, y - 0.07, z + 0.23, 0.04, 0.04, 0.05, shade(col, 0.75)); box(ctx, I, x + 0.16, y + 0.02, z + 0.23, 0.04, 0.04, 0.05, shade(col, 0.75));
    var flick = Math.sin(t * 2.2 + c.seed * 7) * 0.08;
    ctx.strokeStyle = shade(col, 0.8); ctx.lineWidth = Math.max(0.8, I.hw * 0.07); ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(I.sx(x - 0.15, y), I.sy(x - 0.15, y, z + 0.08));
    ctx.quadraticCurveTo(I.sx(x - 0.32, y + flick), I.sy(x - 0.32, y + flick, z + 0.1), I.sx(x - 0.28, y + flick * 2), I.sy(x - 0.28, y + flick * 2, z + 0.3)); ctx.stroke();
    if (c.sleep) {
      ctx.fillStyle = 'rgba(255,255,255,0.8)';
      ctx.font = '800 ' + (I.hw * 0.4).toFixed(1) + 'px sans-serif';
      var zz = (t * 0.6 + c.seed) % 1;
      ctx.globalAlpha = 1 - zz;
      ctx.fillText('z', I.sx(x + 0.2, y) + zz * 6, I.sy(x + 0.2, y, z + 0.45) - zz * 10);
      ctx.globalAlpha = 1;
    }
  }
  function drawDuck(ctx, I, d, t) {
    var x = d.x, y = d.y, z = -0.2 + Math.sin(t * 3 + d.seed * 9) * 0.015, s = d.size;
    var k = { dir: d.dir }, fx = DX[d.dir], fy = DY[d.dir];
    ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = Math.max(0.6, I.hw * 0.04);
    ctx.beginPath();
    ctx.moveTo(I.sx(x - fx * 0.3 * s - fy * 0.2 * s, y - fy * 0.3 * s + fx * 0.2 * s), I.sy(x - fx * 0.3 * s - fy * 0.2 * s, y - fy * 0.3 * s + fx * 0.2 * s, -0.2));
    ctx.lineTo(I.sx(x, y), I.sy(x, y, -0.2));
    ctx.lineTo(I.sx(x - fx * 0.3 * s + fy * 0.2 * s, y - fy * 0.3 * s - fx * 0.2 * s), I.sy(x - fx * 0.3 * s + fy * 0.2 * s, y - fy * 0.3 * s - fx * 0.2 * s, -0.2));
    ctx.stroke();
    var b = oriented({}, k, x, y, z, 0.26 * s, 0.16 * s, 0.12 * s, d.color);
    box(ctx, I, b.x, b.y, b.z, b.w, b.d, b.h, b.c, EMPTY);
    var h = oriented({}, k, x + fx * 0.1 * s, y + fy * 0.1 * s, z + 0.1 * s, 0.1 * s, 0.1 * s, 0.11 * s, d.head || d.color);
    box(ctx, I, h.x, h.y, h.z, h.w, h.d, h.h, h.c, EMPTY);
    var bk = oriented({}, k, x + fx * 0.19 * s, y + fy * 0.19 * s, z + 0.13 * s, 0.07 * s, 0.05 * s, 0.03 * s, '#ff9f1c');
    box(ctx, I, bk.x, bk.y, bk.z, bk.w, bk.d, bk.h, bk.c, EMPTY);
  }

  /* ============================================================== world */
  function World(host, mode) {
    var cfg = MODES[mode] || MODES.hero;
    this.host = host;
    this.mode = mode;
    this.cfg = cfg;
    this.W = cfg.w;
    this.H = cfg.h;
    var seed = parseInt(query['haven-seed'] || host.getAttribute('data-seed') || '', 10);
    if (!(seed >= 0)) seed = (Math.random() * 4294967295) >>> 0;
    if (mode === 'build') {
      try { seed = parseInt(sessionStorage.getItem('haven.build') || '', 10) || seed; sessionStorage.setItem('haven.build', String(seed)); } catch (e) { /* private mode */ }
    }
    this.seed = seed;
    this.rand = mulberry(seed);
    var month = new Date().getMonth();
    this.seasonName = SEASONS[query['haven-season']] ? query['haven-season'] : (host.getAttribute('data-season') || SEASON_OF_MONTH[month]);
    this.S = SEASONS[this.seasonName] || SEASONS.autumn;
    this.light = cfg.light;
    this.lightMix = 1;
    this.prevLight = cfg.light;
    this.mirror = this.rand() < 0.5 ? 1 : -1;
    if (mode === 'build' || mode === 'mini') this.mirror = 1;
    this.font = (global.getComputedStyle ? getComputedStyle(host).fontFamily : '') || 'system-ui, sans-serif';
    this.iso = new Iso(cfg.tw, cfg.cx, cfg.cy - (cfg.n) * cfg.tw / 4);
    this.t = 0;
    this.dt = 0.016;
    this.stage = mode === 'build' ? 0 : 99;
    this.stageAt = {};
    this.domeK = mode === 'build' ? 0 : 1;
    this.name = '';
    this.kids = [];
    this.critters = [];
    this.parts = [];
    this.sky = [];
    this.threats = [];
    this.hits = [];
    this.bubbles = [];
    this.storm = null;
    this.rainbow = 0;
    this.flash = 0;
    this.badgeHit = 0;
    this.nextThreat = 2.2;
    this.nextEvent = 7 + this.rand() * 5;
    this.lastEvent = '';
    this.pointer = null;
    this.visible = true;
    this.dpr = Math.min(2, global.devicePixelRatio || 1);
    this.slow = 0;
    if (mode === 'mini') {
      this.badTexts = [host.getAttribute('data-bad-1') || 'hey how old r u?', host.getAttribute('data-bad-2') || 'add me on my other app',
                       host.getAttribute('data-bad-3') || 'what school do u go to?'];
      this.goodText = host.getAttribute('data-good') || 'gg! wanna team up?';
      this.approveText = host.getAttribute('data-approve') || 'You approved Leo';
    }
    this.generate();
    this.spawn();
    this.setup();
  }
  var WP = World.prototype;

  WP.grid = function (v) { var a = [], n = this.cfg.n; for (var i = 0; i < n; i++) { a.push([]); for (var j = 0; j < n; j++) a[i].push(v); } return a; };

  /* ---------------------------------------------------------- the island */
  WP.generate = function () {
    var cfg = this.cfg, r = this.rand, n = cfg.n, c = (n - 1) / 2, R = n / 2 - 0.55, self = this;
    var G = this.G = { n: n, c: c, R: R, top: this.grid(null), bot: this.grid(0), water: this.grid(false), path: this.grid(false),
                       occ: this.grid(null), props: [], spots: [], crystals: [], flowers: [], lily: [], exit: null, pond: [] };
    var p1 = r() * TAU, p2 = r() * TAU, p3 = r() * TAU, i, j;
    for (i = 0; i < n; i++) {
      for (j = 0; j < n; j++) {
        var dx = i - c, dy = j - c, d = Math.sqrt(dx * dx + dy * dy), a = Math.atan2(dy, dx);
        var rr = R * (1 + 0.07 * Math.sin(3 * a + p1) + 0.05 * Math.sin(5 * a + p2) + 0.03 * Math.sin(7 * a + p3));
        if (cfg.n <= 7) rr = R;
        if (d <= rr) {
          G.top[i][j] = 0;
          var k = Math.pow(Math.max(0, 1 - d / rr), 0.7);
          G.bot[i][j] = -(1 + Math.round(k * cfg.depth + hash(i, j, 3) * 1.1));
        }
      }
    }
    var mirror = this.mirror;
    function zone(u, v) { u *= mirror; return { i: Math.round(c + (u + v) / SQ2), j: Math.round(c + (v - u) / SQ2) }; }
    function inIsland(a, b) { return a >= 0 && b >= 0 && a < n && b < n && G.top[a][b] !== null; }
    function interior(a, b) { return inIsland(a + 1, b) && inIsland(a - 1, b) && inIsland(a, b + 1) && inIsland(a, b - 1); }
    function land(a, b) { return inIsland(a, b) && G.top[a][b] === 0 && !G.water[a][b]; }
    function free(a, b) { return land(a, b) && !G.occ[a][b] && !G.path[a][b]; }
    function fits(a, b, fw, fd, need) {
      for (var x = a; x < a + fw; x++) for (var y = b; y < b + fd; y++) if (!free(x, y) || !interior(x, y)) return false;
      return need ? need(a, b) : true;
    }
    function near(at, fw, fd, need, maxR) {
      if (!at) return null;
      for (var rad = 0; rad <= (maxR || 3); rad++) {
        for (var a = -rad; a <= rad; a++) for (var b = -rad; b <= rad; b++) {
          if (Math.max(Math.abs(a), Math.abs(b)) !== rad) continue;
          if (fits(at.i + a, at.j + b, fw, fd, need)) return { i: at.i + a, j: at.j + b };
        }
      }
      return null;
    }
    function prop(type, at, fw, fd, extra) {
      var p = { type: type, i: at.i, j: at.j, fw: fw, fd: fd, z: 0, stage: 0, seed: r(), obstacle: true };
      for (var key in extra) p[key] = extra[key];
      G.props.push(p);
      if (p.obstacle) for (var x = p.i; x < p.i + fw; x++) for (var y = p.j; y < p.j + fd; y++) if (inIsland(x, y)) G.occ[x][y] = p;
      return p;
    }
    function reserve(a, b) { if (inIsland(a, b) && !G.occ[a][b]) G.occ[a][b] = 'spot'; }
    function spot(act, x, y, dir, extra) {
      var s = { act: act, x: x, y: y, dir: dir, kid: null };
      for (var key in extra) s[key] = extra[key];
      G.spots.push(s);
      return s;
    }
    this.zone = zone; this.free = free; this.land = land; this.inIsland = inIsland;
    var big = cfg.n >= 15, S = this.S;

    if (big) {
      // a hill at the back, with the windmill or the lighthouse on it
      var hc = zone(2.3, -4.7), hill = [];
      for (i = 0; i < n; i++) for (j = 0; j < n; j++) {
        if (!inIsland(i, j)) continue;
        var hd = Math.sqrt((i - hc.i) * (i - hc.i) + (j - hc.j) * (j - hc.j));
        if (hd <= 2.25) { G.top[i][j] = hd <= 1.15 && cfg.n >= 17 ? 2 : 1; hill.push({ i: i, j: j, d: hd }); }
      }
      hill.sort(function (a, b) { return a.d - b.d; });
      if (hill.length) {
        var core = hill[0];
        var tower = prop(r() < 0.6 ? 'windmill' : 'lighthouse', core, 1, 1, { z: G.top[core.i][core.j], face: 'right' });
        var trees = 0;
        for (var hk = hill.length - 1; hk > 0 && trees < 3; hk--) {
          var ht = hill[hk];
          if (G.occ[ht.i][ht.j] || r() < 0.4) continue;
          prop('tree', ht, 1, 1, { z: G.top[ht.i][ht.j], kind: r() < 0.5 ? 'pine' : 'oak', leaf: pick(r, S.leaves) });
          trees++;
        }
        tower.depthBias = 0.02;
      }
      // the pond, and the stream that runs off the edge
      var pc = zone(3.3, 2.0);
      for (i = 0; i < n; i++) for (j = 0; j < n; j++) {
        if (!inIsland(i, j) || G.top[i][j] !== 0 || !interior(i, j)) continue;
        var pd = Math.sqrt((i - pc.i) * (i - pc.i) + (j - pc.j) * (j - pc.j));
        if (pd <= 1.75) { G.water[i][j] = true; G.top[i][j] = -1; G.bot[i][j] = Math.min(G.bot[i][j], -2); G.pond.push({ i: i, j: j }); }
      }
      if (G.pond.length) {
        var ex = mirror > 0 ? 1 : 0, ey = mirror > 0 ? 0 : 1, si = pc.i, sj = pc.j, guard = 0;
        while (inIsland(si + ex, sj + ey) && guard++ < n) {
          si += ex; sj += ey;
          if (!G.water[si][sj]) { G.water[si][sj] = true; G.top[si][sj] = -1; G.bot[si][sj] = Math.min(G.bot[si][sj], -2); }
        }
        G.exit = { i: si, j: sj, dir: ex ? 'x' : 'y' };
      }
    } else if (cfg.n >= 9) {
      var spc = zone(2.3, 1.2);
      for (i = spc.i; i <= spc.i + 1; i++) for (j = spc.j; j <= spc.j + 1; j++) {
        if (!inIsland(i, j) || !interior(i, j)) continue;
        G.water[i][j] = true; G.top[i][j] = -1; G.bot[i][j] = Math.min(G.bot[i][j], -2); G.pond.push({ i: i, j: j });
      }
      spc = { i: spc.i + 1, j: spc.j };
      if (G.pond.length) {
        var bi = spc.i, bj = spc.j, g2 = 0;
        while (inIsland(bi + 1, bj) && g2++ < n) { bi++; if (!G.water[bi][bj]) { G.water[bi][bj] = true; G.top[bi][bj] = -1; G.bot[bi][bj] = Math.min(G.bot[bi][bj], -2); } }
        G.exit = { i: bi, j: bj, dir: 'x' };
      }
    }

    var plaza = zone(0, 0);
    if (!land(plaza.i, plaza.j)) plaza = near(plaza, 1, 1) || plaza;
    var targets = [];

    if (this.mode === 'mini') {
      var mt = near(zone(-1.3, -1.0), 1, 1, null, 2);
      if (mt) prop('tree', mt, 1, 1, { kind: 'oak', leaf: pick(r, S.leaves) });
      var mb = near(zone(1.5, -0.8), 1, 1, null, 2);
      if (mb) prop('tree', mb, 1, 1, { kind: 'bush', leaf: pick(r, S.leaves) });
      this.flowers(1, 0.35);
      return;
    }
    if (this.mode === 'build') {
      var hs = near(zone(-0.7, -1.5), 2, 2, function (a, b) { return land(a, b + 2) && land(a + 1, b + 2); }, 2);
      if (hs) {
        var house = prop('house', hs, 2, 2, { wall: pick(r, WALLS), roof: pick(r, ROOFS), door: 'left', stage: 1 });
        reserve(hs.i, hs.j + 2); reserve(hs.i + 1, hs.j + 2);
        G.home = spot('home', hs.i + 1, hs.j + 2.45, 3, { house: house });
      }
      [[-2.7, -0.6, 'oak'], [2.4, -1.9, 'pine'], [-1.6, 2.2, 'bush'], [2.9, 0.1, 'oak']].forEach(function (z, idx) {
        var at = near(zone(z[0], z[1]), 1, 1, null, 2);
        if (at) prop('tree', at, 1, 1, { kind: z[2], leaf: pick(r, S.leaves), stage: 1 });
      });
      var sg = near(zone(1.4, 0.6), 1, 1, function (a, b) { return free(a - 1, b) || true; }, 2);
      if (sg) prop('sign', sg, 1, 1, { stage: 2, obstacle: true });
      [[-1.9, 1.3], [2.1, 1.9]].forEach(function (z) { var at = near(zone(z[0], z[1]), 1, 1, null, 2); if (at) prop('lamp', at, 1, 1, { stage: 6 }); });
      var fc = near(zone(0.2, 2.6), 1, 1, null, 2);
      if (fc) prop('fire', fc, 1, 1, { stage: 6 });
      this.flowers(1, 0.3);
      this.buildSpots = [zone(0.3, 1.0), zone(-0.6, 0.4), zone(1.0, 1.6), zone(-1.0, 1.8)].filter(function (z) { return land(z.i, z.j); });
      return;
    }

    // ---------------------------------------------------- the big island
    var hz = near(zone(-1.7, -2.5), 2, 2, function (a, b) {
      return mirror > 0 ? land(a, b + 2) && land(a + 1, b + 2) : land(a + 2, b) && land(a + 2, b + 1);
    }, 3);
    if (hz) {
      var h = prop('house', hz, 2, 2, { wall: pick(r, WALLS), roof: pick(r, ROOFS), door: mirror > 0 ? 'left' : 'right' });
      var door = mirror > 0 ? { i: hz.i + 1, j: hz.j + 2 } : { i: hz.i + 2, j: hz.j + 1 };
      reserve(door.i, door.j);
      G.home = spot('home', door.i + 0.5 - (mirror > 0 ? 0.5 : 0) * 0 , door.j + 0.5, mirror > 0 ? 3 : 2, { house: h, ti: door.i, tj: door.j });
      G.home.x = door.i + 0.5; G.home.y = door.j + 0.5;
      targets.push(door);
      var mbx = mirror > 0 ? { i: hz.i - 1, j: hz.j + 2 } : { i: hz.i + 2, j: hz.j - 1 };
      if (free(mbx.i, mbx.j)) prop('mailbox', mbx, 1, 1, {});
      if (r() < 0.75) G.catSpot = { x: hz.i + 1, y: hz.j + 1, z: 2.62, house: h };
    }
    var second = pick(r, ['stall', 'tent', 'well', 'stall']);
    var sz = near(zone(4.5, -2.0), 1, 1, function (a, b) { return land(a, b + 1); }, 3);
    if (sz) {
      prop(second, sz, 1, 1, { color: pick(r, ['#ff8a3d', '#14b8a6', '#8b5cf6']) });
      reserve(sz.i, sz.j + 1);
      if (second === 'stall') {
        spot('stall', sz.i + 0.5, sz.j + 1.45, 3, { ti: sz.i, tj: sz.j + 1 });
      } else {
        spot('wander', sz.i + 0.5, sz.j + 1.5, 3, { ti: sz.i, tj: sz.j + 1 });
      }
      targets.push({ i: sz.i, j: sz.j + 1 });
    }
    // the playground
    var sw = near(zone(-4.3, 0.5), 2, 1, function (a, b) { return land(a, b + 1) && land(a + 1, b + 1); }, 3);
    if (sw) {
      var swing = prop('swing', sw, 2, 1, {});
      swing.spots = [spot('swing', sw.i + 0.5, sw.j + 1.5, 3, { prop: swing, seat: 0, ti: sw.i, tj: sw.j + 1 }),
                     spot('swing', sw.i + 1.5, sw.j + 1.5, 3, { prop: swing, seat: 1, ti: sw.i + 1, tj: sw.j + 1 })];
      reserve(sw.i, sw.j + 1); reserve(sw.i + 1, sw.j + 1);
      targets.push({ i: sw.i, j: sw.j + 1 });
    }
    var sl = near(zone(-2.9, 2.7), 1, 2, function (a, b) { return land(a, b - 1) && land(a, b + 2); }, 3);
    if (sl) {
      var slide = prop('slide', sl, 1, 2, {});
      slide.spot = spot('slide', sl.i + 0.5, sl.j - 0.5, 1, { prop: slide, ti: sl.i, tj: sl.j - 1, exit: { i: sl.i, j: sl.j + 2 } });
      reserve(sl.i, sl.j - 1); reserve(sl.i, sl.j + 2);
      targets.push({ i: sl.i, j: sl.j - 1 });
    }
    var ss = near(zone(-5.1, 2.3), 2, 1, function (a, b) { return land(a, b + 1) || land(a, b - 1); }, 3);
    if (ss) {
      var see = prop('seesaw', ss, 2, 1, {});
      var approach = land(ss.i, ss.j + 1) ? 1 : -1;
      see.spots = [spot('seesaw', ss.i + 0.5, ss.j + 0.5 + approach, approach > 0 ? 3 : 1, { prop: see, end: 0, ti: ss.i, tj: ss.j + approach }),
                   spot('seesaw', ss.i + 1.5, ss.j + 0.5 + approach, approach > 0 ? 3 : 1, { prop: see, end: 1, ti: ss.i + 1, tj: ss.j + approach })];
      reserve(ss.i, ss.j + approach); reserve(ss.i + 1, ss.j + approach);
      targets.push({ i: ss.i, j: ss.j + approach });
    }
    // the campfire and its log seats
    var fz = near(zone(0.9, 4.2), 1, 1, function (a, b) { return land(a - 1, b) && land(a + 1, b) && land(a, b + 1); }, 3);
    if (fz) {
      var fire = prop('fire', fz, 1, 1, {});
      [[-1, 0, 0, 'y'], [1, 0, 2, 'y'], [0, 1, 3, 'x']].forEach(function (o) {
        var at = { i: fz.i + o[0], j: fz.j + o[1] };
        if (!free(at.i, at.j)) return;
        prop('log', at, 1, 1, { along: o[3], obstacle: false });
        G.occ[at.i][at.j] = 'spot';
        spot('fire', at.i + 0.5, at.j + 0.5, o[2], { prop: fire, ti: at.i, tj: at.j });
        targets.push(at);
      });
    }
    // the building site
    var bz = near(zone(-5.0, -1.9), 1, 1, function (a, b) { return mirror > 0 ? land(a - 1, b) : land(a, b - 1); }, 3);
    if (bz) {
      var build = prop('build', bz, 1, 1, { bricks: [] });
      var ba = mirror > 0 ? { i: bz.i - 1, j: bz.j } : { i: bz.i, j: bz.j - 1 };
      reserve(ba.i, ba.j);
      build.spot = spot('build', ba.i + 0.5, ba.j + 0.5, mirror > 0 ? 0 : 1, { prop: build, ti: ba.i, tj: ba.j });
      targets.push(ba);
    }
    // the dance spot and the flag
    var dz = near(zone(-0.4, 1.0), 1, 1, null, 2);
    if (dz) {
      var boom = prop('boombox', dz, 1, 1, {});
      [[1, 0, 2], [0, 1, 3], [1, 1, 3]].forEach(function (o) {
        var at = { i: dz.i + o[0], j: dz.j + o[1] };
        if (free(at.i, at.j)) { reserve(at.i, at.j); spot('dance', at.i + 0.5, at.j + 0.5, o[2], { prop: boom, ti: at.i, tj: at.j }); targets.push(at); }
      });
    }
    var fl = near(zone(1.3, -0.7), 1, 1, null, 2);
    if (fl) prop('flag', fl, 1, 1, { face: mirror > 0 ? 'right' : 'left' });
    // fishing
    if (G.pond.length) {
      var dock = null;
      for (var pk = 0; pk < G.pond.length && !dock; pk++) {
        var w0 = G.pond[pk];
        if (free(w0.i - 1, w0.j) && G.water[w0.i + 1] && G.water[w0.i + 1][w0.j] && interior(w0.i - 1, w0.j)) dock = { i: w0.i - 1, j: w0.j, dir: 0 };
        else if (free(w0.i, w0.j - 1) && G.water[w0.i][w0.j + 1] && interior(w0.i, w0.j - 1)) dock = { i: w0.i, j: w0.j - 1, dir: 1 };
      }
      if (dock) {
        prop('dock', dock, 1, 1, { dir: dock.dir, obstacle: false });
        G.occ[dock.i][dock.j] = 'spot';
        var fs = dock.dir === 0 ? { x: dock.i + 1.45, y: dock.j + 0.5 } : { x: dock.i + 0.5, y: dock.j + 1.45 };
        spot('fish', fs.x, fs.y, dock.dir, { ti: dock.i, tj: dock.j, bob: dock.dir === 0 ? { x: dock.i + 2.3, y: dock.j + 0.5 } : { x: dock.i + 0.5, y: dock.j + 2.3 } });
        targets.push(dock);
      }
      // ducks and lily pads
      for (var lp = 0; lp < G.pond.length; lp++) if (hash(G.pond[lp].i, G.pond[lp].j, 41) < 0.4) G.lily.push({ x: G.pond[lp].i + 0.2 + hash(lp, 3, 1) * 0.6, y: G.pond[lp].j + 0.2 + hash(lp, 5, 2) * 0.6, s: 0.7 + hash(lp, 7, 3) * 0.5, r: hash(lp, 9, 4) * TAU });
    }
    // the season's extras
    var extra = zone(4.9, -0.3);
    var placed = 0;
    if (this.seasonName === 'autumn') {
      ['pumpkin', 'pumpkin', 'hay', 'pumpkin'].forEach(function (tp) { var at = near({ i: extra.i + placed % 2, j: extra.j + (placed >> 1) }, 1, 1, null, 2); if (at) { prop(tp, at, 1, 1, { obstacle: tp === 'hay' }); placed++; } });
    } else if (this.seasonName === 'winter') {
      var sm = near(zone(1.6, 1.6), 1, 1, null, 2); if (sm) prop('snowman', sm, 1, 1, {});
      var lpn = near(zone(1.4, -2.0), 1, 1, null, 2); if (lpn) prop('litpine', lpn, 1, 1, {});
    } else if (this.seasonName === 'summer') {
      for (var sf = 0; sf < 3; sf++) { var sa = near({ i: extra.i + sf, j: extra.j }, 1, 1, null, 2); if (sa) prop('sunflower', sa, 1, 1, { obstacle: false }); }
    }
    // a bench or two by the plaza
    for (var bn = 0; bn < 2; bn++) {
      var bnz = near(zone(bn ? 2.2 : -2.4, bn ? 1.1 : -0.4), 1, 1, null, 2);
      if (bnz) { prop('bench', bnz, 1, 1, { along: bn ? 'x' : 'y' }); if (!G.benchSpot) G.benchSpot = { x: bnz.i + 0.5, y: bnz.j + 0.5, z: 0.3 }; }
    }
    // kite field, catch, garden and bubbles all want a little open grass
    var kz = near(zone(1.9, -2.8), 1, 1, null, 3);
    if (kz) { reserve(kz.i, kz.j); spot('kite', kz.i + 0.5, kz.j + 0.5, 1, { ti: kz.i, tj: kz.j }); targets.push(kz); }
    var cz1 = near(zone(-1.8, 3.6), 1, 1, null, 3), cz2 = near(zone(1.2, 2.4), 1, 1, null, 3);
    if (cz1 && cz2) {
      reserve(cz1.i, cz1.j); reserve(cz2.i, cz2.j);
      var catchA = spot('catch', cz1.i + 0.5, cz1.j + 0.5, 0, { ti: cz1.i, tj: cz1.j });
      var catchB = spot('catch', cz2.i + 0.5, cz2.j + 0.5, 2, { ti: cz2.i, tj: cz2.j });
      catchA.partner = catchB; catchB.partner = catchA;
      targets.push(cz1, cz2);
    }
    // paths from the plaza to everything worth walking to
    var self2 = this;
    targets.forEach(function (tg) {
      var route = self2.route(plaza, tg, true);
      if (route) route.forEach(function (st) { if (land(st.i, st.j) && !G.occ[st.i][st.j]) G.path[st.i][st.j] = true; });
    });
    // lamps along the paths
    var lamps = 0;
    for (i = 0; i < n && lamps < 6; i++) for (j = 0; j < n && lamps < 6; j++) {
      if (!G.path[i][j] || hash(i, j, 61) > 0.16) continue;
      var lspot = [[1, 0], [0, 1], [-1, 0], [0, -1]].map(function (o) { return { i: i + o[0], j: j + o[1] }; }).filter(function (o) { return free(o.i, o.j) && interior(o.i, o.j); })[0];
      if (lspot) { prop('lamp', lspot, 1, 1, {}); lamps++; }
    }
    // trees round the edge
    var want = cfg.n >= 17 ? 12 : 9, tries = 0, made = 0;
    while (made < want && tries++ < 400) {
      var ti = Math.floor(r() * n), tj = Math.floor(r() * n);
      if (!free(ti, tj)) continue;
      var edgeDist = Math.sqrt((ti - c) * (ti - c) + (tj - c) * (tj - c)) / R;
      if (edgeDist < 0.55 && r() < 0.8) continue;
      var kind = S.snow ? (r() < 0.75 ? 'pine' : 'oak') : (r() < 0.22 ? 'pine' : (r() < 0.2 ? 'bush' : 'oak'));
      prop('tree', { i: ti, j: tj }, 1, 1, { kind: kind, leaf: pick(r, S.leaves), fruit: kind === 'oak' && r() < 0.25 && !S.snow ? '#e8463b' : null });
      made++;
    }
    // rocks and mushrooms
    for (var rk = 0; rk < 5; rk++) {
      var ri = Math.floor(r() * n), rj = Math.floor(r() * n);
      if (free(ri, rj)) prop(r() < 0.6 ? 'rock' : 'mushroom', { i: ri, j: rj }, 1, 1, { obstacle: true });
    }
    // a hedge along part of the front edge, round the playground
    for (i = 0; i < n; i++) for (j = 0; j < n; j++) {
      if (!land(i, j) || G.occ[i][j] || G.path[i][j]) continue;
      var u = (i - j) * mirror;
      if (u > -2) continue;
      if (!inIsland(i, j + 1) && hash(i, j, 71) < 0.7) prop('hedge', { i: i, j: j }, 1, 1, { side: 'y', obstacle: false, front: true });
      else if (!inIsland(i + 1, j) && hash(i, j, 72) < 0.7) prop('hedge', { i: i, j: j }, 1, 1, { side: 'x', obstacle: false, front: true });
    }
    this.flowers(0, 0.16);
    G.plaza = plaza;
  };
  WP.flowers = function (stage, chance) {
    var G = this.G, n = G.n, S = this.S;
    if (!S.flowers.length) return;
    for (var i = 0; i < n; i++) for (var j = 0; j < n; j++) {
      if (!this.free(i, j) || hash(i, j, 51) > chance) continue;
      var count = 2 + Math.floor(hash(i, j, 52) * 3);
      for (var f = 0; f < count; f++) {
        G.flowers.push({ x: i + 0.15 + hash(i, j, 53 + f) * 0.7, y: j + 0.15 + hash(i, j, 63 + f) * 0.7, c: S.flowers[Math.floor(hash(i, j, 73 + f) * S.flowers.length)],
                         h: 0.16 + hash(i, j, 83 + f) * 0.14, p: hash(i, j, 93 + f) * TAU, stage: stage, s: 1 });
      }
    }
  };

  /* ---------------------------------------------------------- walking */
  WP.walkable = function (i, j) {
    var G = this.G;
    if (!this.land(i, j)) return false;
    var o = G.occ[i][j];
    return !o || o === 'spot' || !o.obstacle;
  };
  WP.route = function (from, to, carving) {
    var G = this.G, n = G.n, self = this;
    if (!from || !to) return null;
    var start = from.i * n + from.j, goal = to.i * n + to.j;
    if (start === goal) return [];
    var prev = {}, queue = [start], seen = {};
    seen[start] = true;
    while (queue.length) {
      var cur = queue.shift();
      if (cur === goal) break;
      var ci = Math.floor(cur / n), cj = cur % n;
      for (var k = 0; k < 4; k++) {
        var ni = ci + DX[k], nj = cj + DY[k], id = ni * n + nj;
        if (ni < 0 || nj < 0 || ni >= n || nj >= n || seen[id]) continue;
        var ok = id === goal || (carving ? (self.land(ni, nj) && (!G.occ[ni][nj] || G.occ[ni][nj] === 'spot' || !G.occ[ni][nj].obstacle)) : self.walkable(ni, nj));
        if (!ok) continue;
        seen[id] = true; prev[id] = cur; queue.push(id);
      }
    }
    if (!seen[goal]) return null;
    var out = [], node = goal;
    while (node !== start) { out.unshift({ i: Math.floor(node / n), j: node % n }); node = prev[node]; }
    return out;
  };
  WP.randomTile = function () {
    var G = this.G, n = G.n;
    for (var tries = 0; tries < 60; tries++) {
      var i = Math.floor(Math.random() * n), j = Math.floor(Math.random() * n);
      if (this.walkable(i, j) && G.occ[i][j] !== 'spot') return { i: i, j: j };
    }
    return null;
  };

  /* ------------------------------------------------------------- kids */
  WP.makeKid = function (r, opts) {
    var S = this.S, k = {
      x: 0, y: 0, z: 0, jz: 0, vz: 0, dir: 1, phase: 0, moving: false, pose: 'stand', visible: true, scale: 0.98 + r() * 0.12,
      shirt: pick(r, SHIRTS), pants: pick(r, PANTS), seed: r(), wave: 0, blink: 0, happy: 0, idle: 0.5 + r() * 2, act: null,
      path: null, speed: 1.45 + r() * 0.35, logo: r() < 0.3 ? pick(r, ['#ffffff', '#ffcf3a', '#1b2a35']) : null
    };
    var style = r();
    if (S.snow) { k.hat = 'beanie'; k.hatColor = pick(r, HATS); }
    else if (style < 0.32) { k.hat = 'cap'; k.hatColor = pick(r, HATS); }
    else if (style < 0.85) k.hair = pick(r, HAIRS);
    if (opts) for (var key in opts) k[key] = opts[key];
    if (k.shirt === k.pants) k.pants = '#1b2a35';
    return k;
  };
  WP.spawn = function () {
    var r = this.rand, cfg = this.cfg, G = this.G, self = this;
    var narrow = this.host.getBoundingClientRect().width < 420;
    var count = narrow && this.mode !== 'mini' ? Math.max(4, cfg.kids - 2) : cfg.kids;
    var spots = G.spots.slice().sort(function () { return r() - 0.5; });
    for (var n = 0; n < count; n++) {
      var k = this.makeKid(r);
      var s = null;
      for (var q = 0; q < spots.length; q++) { if (!spots[q].kid && spots[q].act !== 'wander' && spots[q].act !== 'home') { s = spots[q]; spots.splice(q, 1); break; } }
      var tile = s ? { i: s.ti, j: s.tj } : this.randomTile();
      if (!tile) continue;
      k.x = tile.i + 0.5; k.y = tile.j + 0.5;
      this.kids.push(k);
      if (s) this.begin(k, s);
    }
    if (this.mode === 'mini') {
      var mk = this.kids[0] || this.makeKid(r);
      if (!this.kids.length) this.kids.push(mk);
      mk.shirt = '#2b67f6'; mk.pants = '#1b2a35'; mk.hat = null; mk.hair = '#3b2414'; mk.logo = null;
      mk.x = G.c + 0.5 + 0.2; mk.y = G.c + 0.5 + 0.5; mk.dir = 1; mk.act = { mini: true }; mk.scale = 1.3;
      this.ball = { t0: 0 };
    }
    if (this.mode === 'build') {
      var bk = this.makeKid(r, { scale: 1.12, hat: null, hair: null });
      var home = this.buildSpots && this.buildSpots[0];
      if (home) { bk.x = home.i + 0.5; bk.y = home.j + 0.5; }
      bk.visible = false; bk.pop = 0; bk.isChild = true; bk.idle = 1;
      this.kids.push(bk);
      this.child = bk;
    }
    if (cfg.critters) {
      var dt = this.randomTile();
      if (dt) this.critters.push({ type: 'dog', x: dt.i + 0.5, y: dt.j + 0.5, dir: 1, phase: 0, moving: false, color: pick(r, ['#d9a066', '#f2f3f3', '#8b5a2b', '#3b3b3b']), seed: r(), idle: 1, happy: 0 });
      if (G.catSpot) this.critters.push({ type: 'cat', x: G.catSpot.x + 0.6, y: G.catSpot.y + 0.5, z: G.catSpot.z, color: pick(r, ['#ff9f43', '#7b8a99', '#3b3b3b', '#f2f3f3']), seed: r(), sleep: true, onRoof: G.catSpot.house });
      if (G.pond.length >= 4) {
        var mom = { type: 'duck', size: 1, color: '#f6f2ea', head: '#2f8a40', seed: r(), a: r() * TAU, lead: true };
        this.critters.push(mom);
        for (var dk = 0; dk < 3; dk++) this.critters.push({ type: 'duck', size: 0.62, color: '#ffd84a', seed: r(), follow: mom, lag: (dk + 1) * 0.55 });
        var sumI = 0, sumJ = 0;
        G.pond.forEach(function (p) { sumI += p.i; sumJ += p.j; });
        this.pondC = { x: sumI / G.pond.length + 0.5, y: sumJ / G.pond.length + 0.5 };
      }
      this.birds = [];
      for (var b = 0; b < 3; b++) this.birds.push({ a: r() * TAU, sp: 0.25 + r() * 0.2, rr: 0.4 + r() * 0.35, h: 0.18 + r() * 0.25, p: r() * TAU });
    }
  };

  /* ---------------------------------------------------------- activities
     A kid walks to a spot, then its activity runs until it says it is done. */
  var ACTS = {};
  ACTS.wander = {
    start: function (w, k) { k.actDur = 2 + Math.random() * 3; k.pose = 'stand'; },
    update: function (w, k, dt) { return (k.actT += dt) > k.actDur; }
  };
  ACTS.swing = {
    start: function (w, k, s) { k.ride = s.prop; k.pose = 'sit'; k.actDur = 7 + Math.random() * 5; },
    update: function (w, k, dt) { return (k.actT += dt) > k.actDur; },
    end: function (w, k, s) { k.ride = null; k.x = s.ti + 0.5; k.y = s.tj + 0.5; k.z = 0; k.pose = 'stand'; k.dir = 1; }
  };
  ACTS.slide = {
    start: function (w, k, s) { k.ride = s.prop; s.prop.rider = k; k.phaseN = 0; k.laps = 1 + Math.floor(Math.random() * 2); k.stepT = 0; },
    update: function (w, k, dt, s) {
      var p = s.prop, x = p.i + 0.5;
      k.stepT += dt;
      if (k.phaseN === 0) { // climbing the ladder
        var c = Math.min(1, k.stepT / 1.1);
        k.x = x; k.y = p.j - 0.02; k.z = c * 1.2; k.dir = 3; k.pose = 'climb';
        if (c >= 1) { k.phaseN = 1; k.stepT = 0; }
      } else if (k.phaseN === 1) { // at the top
        k.x = x; k.y = p.j + 0.4; k.z = 1.28; k.dir = 1; k.pose = 'cheer';
        if (k.stepT > 0.5) { k.phaseN = 2; k.stepT = 0; if (Math.random() < 0.5) w.say(k, pick(Math.random, ['wheee!', 'woo!', 'yay!'])); }
      } else if (k.phaseN === 2) { // down the chute
        var e = smooth(k.stepT / 0.85);
        k.x = x; k.y = lerp(p.j + 0.6, p.j + 2.05, e); k.z = lerp(1.26, 0.06, e); k.dir = 1; k.pose = 'slideDown';
        if (e >= 1) { k.phaseN = 3; k.stepT = 0; }
      } else { // hop off
        k.y = p.j + 2.05 + Math.min(1, k.stepT / 0.3) * 0.45; k.z = 0; k.pose = 'stand';
        if (k.stepT > 0.3) return true;
      }
      return false;
    },
    end: function (w, k, s) {
      k.ride = null; s.prop.rider = null; k.z = 0; k.pose = 'stand';
      k.x = s.exit.i + 0.5; k.y = s.exit.j + 0.5;
      if (--k.laps > 0 && w.claim(k, s)) w.goTo(k, { i: s.ti, j: s.tj }, s);
    }
  };
  ACTS.seesaw = {
    start: function (w, k, s) { k.ride = s.prop; k.pose = 'sitFlat'; k.actDur = 8 + Math.random() * 4; },
    update: function (w, k, dt) { return (k.actT += dt) > k.actDur; },
    end: function (w, k, s) { k.ride = null; k.z = 0; k.pose = 'stand'; k.x = s.ti + 0.5; k.y = s.tj + 0.5; }
  };
  ACTS.fire = {
    start: function (w, k, s) { k.pose = 'sitFlat'; k.dir = s.dir; k.actDur = 8 + Math.random() * 6; k.z = 0.05; },
    update: function (w, k, dt) {
      k.actT += dt;
      k.pose = Math.sin(k.actT * 0.7 + k.seed * 6) > 0.4 ? 'roast' : 'sitFlat';
      if (k.pose === 'roast') k.pose = 'sitFlat', k.roast = true; else k.roast = false;
      return k.actT > k.actDur;
    },
    end: function (w, k) { k.z = 0; k.roast = false; }
  };
  ACTS.build = {
    start: function (w, k, s) { k.dir = s.dir; k.pose = 'stand'; k.stepT = 0; var b = s.prop; if (b.bricks.length === 0 || b.done) w.newBuild(b); },
    update: function (w, k, dt, s) {
      var b = s.prop;
      k.stepT += dt;
      k.pose = k.stepT % 0.9 < 0.35 ? 'hold' : 'stand';
      if (b.done) { k.pose = 'cheer'; return k.stepT > 1.6; }
      if (k.stepT > 0.9) {
        k.stepT = 0;
        var next = b.plan.shift();
        if (next) { next.t0 = w.t; b.bricks.push(next); }
        if (!b.plan.length) { b.done = w.t; w.say(k, 'ta-da!'); w.sparkle(b.i + 0.5, b.j + 0.5, 1.4, 14); k.stepT = 0; }
      }
      return false;
    },
    end: function (w, k, s) { k.pose = 'stand'; var b = s.prop; if (b.done) b.bricks.forEach(function (br) { br.out = w.t + Math.random() * 0.3; }); setTimeout(function () { if (b.done) { b.bricks.length = 0; b.done = 0; } }, 1300); }
  };
  ACTS.dance = {
    start: function (w, k, s) { k.pose = 'dance'; k.actDur = 6 + Math.random() * 5; s.prop.playing = (s.prop.playing || 0) + 1; },
    update: function (w, k, dt) {
      k.actT += dt;
      k.jz = Math.max(0, Math.sin(k.actT * 8)) * 0.08;
      if (Math.floor(k.actT * 1.3) !== Math.floor((k.actT - dt) * 1.3)) k.dir = (k.dir + 1) % 4;
      return k.actT > k.actDur;
    },
    end: function (w, k, s) { k.jz = 0; k.pose = 'stand'; s.prop.playing = Math.max(0, (s.prop.playing || 1) - 1); }
  };
  ACTS.fish = {
    start: function (w, k, s) { k.pose = 'sit'; k.dir = s.dir; k.z = 0; k.actDur = 10 + Math.random() * 6; k.fishing = s; k.nextBite = 2.5 + Math.random() * 4; },
    update: function (w, k, dt, s) {
      k.actT += dt;
      k.pose = 'hold';
      k.pose = 'sit';
      k.holding = 'rod';
      if (k.actT > k.nextBite) { k.nextBite = k.actT + 4 + Math.random() * 5; w.fishJump(s.bob.x, s.bob.y, k); }
      return k.actT > k.actDur;
    },
    end: function (w, k) { k.holding = null; k.fishing = null; k.pose = 'stand'; }
  };
  ACTS.stall = {
    start: function (w, k, s) { k.dir = s.dir; k.pose = 'stand'; k.actDur = 3 + Math.random() * 2; },
    update: function (w, k, dt) {
      k.actT += dt;
      if (k.actT > 1.2 && !k.gotCup) { k.gotCup = true; w.say(k, '♥'); }
      return k.actT > k.actDur;
    },
    end: function (w, k) { k.gotCup = false; }
  };
  ACTS.home = {
    start: function (w, k, s) { k.actDur = 3 + Math.random() * 4; k.visible = false; s.house.lights = 1; },
    update: function (w, k, dt) { return (k.actT += dt) > k.actDur; },
    end: function (w, k, s) { k.visible = true; k.dir = s.dir === 3 ? 1 : 0; s.house.lights = 0; if (Math.random() < 0.5) w.say(k, 'hi!'); }
  };
  ACTS.kite = {
    start: function (w, k) { k.pose = 'hold'; k.holding = 'kite'; k.dir = 1; k.actDur = 10 + Math.random() * 6; k.kite = { a: Math.random() * TAU }; },
    update: function (w, k, dt) { k.actT += dt; k.pose = 'hold'; return k.actT > k.actDur; },
    end: function (w, k) { k.holding = null; k.kite = null; k.pose = 'stand'; }
  };
  ACTS.catch = {
    start: function (w, k, s) { k.dir = s.dir; k.pose = 'stand'; k.actDur = 9 + Math.random() * 4; },
    update: function (w, k, dt, s) {
      k.actT += dt;
      var mate = s.partner && s.partner.kid;
      if (!mate || mate.spot !== s.partner || mate.path) { k.pose = 'wave'; return k.actT > 7; }
      if (!w.ballGame || w.ballGame.a !== s && w.ballGame.b !== s) w.ballGame = { a: s, b: s.partner, t0: w.t, from: 0 };
      k.pose = 'stand';
      return k.actT > k.actDur;
    },
    end: function (w, k, s) { if (w.ballGame && (w.ballGame.a === s || w.ballGame.b === s)) w.ballGame = null; k.pose = 'stand'; }
  };

  WP.claim = function (k, s) {
    if (s.kid && s.kid !== k) return false;
    s.kid = k;
    k.spot = s;
    return true;
  };
  WP.release = function (k) {
    if (k.spot && k.spot.kid === k) k.spot.kid = null;
    k.spot = null;
  };
  WP.begin = function (k, s) {
    this.claim(k, s);
    k.x = s.x; k.y = s.y; k.dir = s.dir; k.act = ACTS[s.act] || ACTS.wander; k.actT = 0;
    k.act.start(this, k, s);
  };
  WP.goTo = function (k, tile, s) {
    var from = { i: clamp(Math.floor(k.x), 0, this.G.n - 1), j: clamp(Math.floor(k.y), 0, this.G.n - 1) };
    var route = this.route(from, tile, false);
    if (!route) { this.release(k); k.idle = 0.5; return false; }
    k.path = route; k.target = s || null;
    return true;
  };
  WP.choose = function (k) {
    var G = this.G, free = [], weights = { swing: 3, slide: 3, seesaw: 2, fire: this.light === 'day' ? 1 : 3, build: 3, dance: 2, fish: 3,
                                          stall: 2, home: 1, kite: 3, catch: 3, wander: 1 };
    for (var q = 0; q < G.spots.length; q++) {
      var s = G.spots[q];
      if (s.kid) continue;
      if (s.act === 'catch' && s.partner && !s.partner.kid && Math.random() < 0.5) continue;
      var wgt = weights[s.act] || 1;
      if (s.act === 'catch' && s.partner && s.partner.kid) wgt = 8;
      if (s.act === 'seesaw') { var other = s.prop.spots[s.end ? 0 : 1]; if (other.kid) wgt = 8; }
      free.push([s, wgt]);
    }
    var total = free.reduce(function (a, b) { return a + b[1]; }, 0) + 3;
    var roll = Math.random() * total;
    for (q = 0; q < free.length; q++) {
      roll -= free[q][1];
      if (roll <= 0) {
        var spot = free[q][0];
        if (this.claim(k, spot) && this.goTo(k, { i: spot.ti, j: spot.tj }, spot)) return;
        this.release(k);
      }
    }
    // a wander: somewhere random, or over to the dog
    var dog = this.critters.filter(function (c) { return c.type === 'dog'; })[0];
    if (dog && Math.random() < 0.18) {
      var dt = { i: Math.floor(dog.x), j: Math.floor(dog.y) }, best = null;
      for (var d = 0; d < 4; d++) { var ni = dt.i + DX[d], nj = dt.j + DY[d]; if (this.walkable(ni, nj)) { best = { i: ni, j: nj }; break; } }
      if (best && this.goTo(k, best, null)) { k.petting = dog; return; }
    }
    var tile = this.randomTile();
    if (tile) this.goTo(k, tile, null);
    else k.idle = 1;
  };
  WP.say = function (k, text) {
    if (!k || !k.visible) return;
    k.bubble = { text: text, t0: this.t, dur: 1.9 };
  };
  WP.newBuild = function (b) {
    var shapes = [
      [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1], [1, 1, 1], [0, 0, 2], [1, 1, 2], [0, 1, 3]],
      [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1], [0, 0, 2], [1, 1, 2]],
      [[0, 1, 0], [1, 1, 0], [1, 0, 0], [1, 1, 1], [1, 0, 1], [0, 1, 1], [1, 1, 2], [1, 1, 3]],
      [[0, 0, 0], [1, 1, 0], [0, 1, 0], [0, 1, 1], [1, 1, 1], [0, 1, 2], [0, 1, 3], [0, 0, 1]]
    ];
    var shape = shapes[Math.floor(Math.random() * shapes.length)], palette = BRICKS.slice().sort(function () { return Math.random() - 0.5; });
    b.plan = shape.map(function (s, n) { return { a: s[0], b: s[1], l: s[2], c: palette[n % 3] }; });
    b.plan.sort(function (p, q) { return p.l - q.l || (p.a + p.b) - (q.a + q.b); });
    b.bricks = [];
    b.done = 0;
  };

  WP.updateKid = function (k, dt) {
    if (k.blink > 0) k.blink -= dt;
    else if (Math.random() < dt * 0.35) k.blink = 0.13;
    if (k.wave > 0) k.wave -= dt;
    if (k.happy > 0) k.happy -= dt;
    // jumping
    if (k.vz || k.jz > 0) {
      if (!k.act || !ACTS.dance || k.act !== ACTS.dance) {
        k.vz -= 9.8 * dt;
        k.jz += k.vz * dt;
        if (k.jz <= 0) { k.jz = 0; k.vz = 0; }
      }
    }
    if (this.mode === 'mini') { this.updateMiniKid(k, dt); return; }
    if (this.mode === 'build') { this.updateBuildKid(k, dt); return; }
    if (k.path) {
      k.moving = true;
      if (!k.path.length) { this.arrive(k); return; }
      var next = k.path[0], tx = next.i + 0.5, ty = next.j + 0.5;
      var dx = tx - k.x, dy = ty - k.y, dist = Math.sqrt(dx * dx + dy * dy), step = k.speed * dt;
      if (Math.abs(dx) > Math.abs(dy)) k.dir = dx > 0 ? 0 : 2; else if (Math.abs(dy) > 0.001) k.dir = dy > 0 ? 1 : 3;
      if (dist <= step) { k.x = tx; k.y = ty; k.path.shift(); if (!k.path.length) this.arrive(k); }
      else { k.x += dx / dist * step; k.y += dy / dist * step; }
      k.phase += dt * k.speed * 7.5;
      return;
    }
    k.moving = false;
    if (k.act) {
      if (k.act.update(this, k, dt, k.spot)) {
        var act = k.act, s = k.spot;
        k.act = null;
        if (act.end) act.end(this, k, s);
        if (!k.path) this.release(k);
        if (!k.path) k.idle = 0.6 + Math.random() * 1.8;
        if (Math.random() < 0.28) this.say(k, pick(Math.random, CHAT));
      }
      return;
    }
    if (k.idle > 0) {
      k.idle -= dt;
      k.pose = 'stand';
      if (Math.random() < dt * 0.4) k.dir = Math.floor(Math.random() * 4);
      return;
    }
    this.choose(k);
  };
  WP.arrive = function (k) {
    k.path = null; k.moving = false;
    if (k.petting) {
      var dog = k.petting;
      k.petting = null;
      k.dir = Math.abs(dog.x - k.x) > Math.abs(dog.y - k.y) ? (dog.x > k.x ? 0 : 2) : (dog.y > k.y ? 1 : 3);
      dog.happy = 2.5; dog.jz = 0; dog.vz = 2.2; dog.idle = 2.5;
      this.say(k, '♥');
      k.idle = 1.6;
      return;
    }
    var s = k.target;
    k.target = null;
    if (s && k.spot === s) {
      k.act = ACTS[s.act] || ACTS.wander;
      k.actT = 0;
      k.x = s.x; k.y = s.y; k.dir = s.dir;
      k.act.start(this, k, s);
    } else {
      this.release(k);
      k.idle = 0.8 + Math.random() * 2.2;
    }
  };

  /* the one kid of the set-up wizard: wanders between a few favourite spots */
  WP.updateBuildKid = function (k, dt) {
    var vis = this.stage >= 3;
    if (vis && !k.visible) { k.visible = true; k.popT = this.t; this.sparkle(k.x, k.y, 0.8, 10); this.say(k, 'hi!'); k.wave = 1.6; }
    if (!vis) { k.visible = false; return; }
    k.pop = backOut((this.t - (k.popT || 0)) / 0.6);
    if (k.path) {
      k.moving = true;
      var next = k.path[0];
      if (!next) { k.path = null; return; }
      var tx = next.i + 0.5, ty = next.j + 0.5, dx = tx - k.x, dy = ty - k.y, dist = Math.sqrt(dx * dx + dy * dy), step = 1.3 * dt;
      if (Math.abs(dx) > Math.abs(dy)) k.dir = dx > 0 ? 0 : 2; else if (Math.abs(dy) > 0.001) k.dir = dy > 0 ? 1 : 3;
      if (dist <= step) { k.x = tx; k.y = ty; k.path.shift(); if (!k.path.length) { k.path = null; k.idle = 1.5 + Math.random() * 2; k.dir = Math.random() < 0.5 ? 0 : 1; } }
      else { k.x += dx / dist * step; k.y += dy / dist * step; }
      k.phase += dt * 9;
      return;
    }
    k.moving = false;
    k.pose = 'stand';
    if (k.idle > 0) { k.idle -= dt; if (Math.random() < dt * 0.25) k.wave = 1.2; return; }
    var spots = this.buildSpots || [];
    var goal = spots[Math.floor(Math.random() * spots.length)];
    if (goal) { var route = this.route({ i: Math.floor(k.x), j: Math.floor(k.y) }, goal, false); if (route && route.length) { k.path = route; return; } }
    k.idle = 2;
  };
  WP.updateMiniKid = function (k, dt) {
    k.moving = false;
    k.pose = k.happy > 0 ? 'cheer' : 'stand';
    var c = (this.t % 2.2) / 2.2;
    k.jz = k.happy > 0 ? Math.max(0, Math.sin(this.t * 9)) * 0.12 : 0;
    k.dir = 1;
    if (!this.ball) return;
    this.ball.h = Math.abs(Math.sin(c * Math.PI * 2)) * 0.9;
  };

  /* ----------------------------------------------------------- critters */
  WP.updateCritters = function (dt) {
    var self = this, t = this.t;
    this.critters.forEach(function (c) {
      if (c.type === 'dog') {
        if (c.happy > 0) c.happy -= dt;
        if (c.vz || c.jz > 0) { c.vz -= 9.8 * dt; c.jz = (c.jz || 0) + c.vz * dt; if (c.jz <= 0) { c.jz = 0; c.vz = 0; } }
        if (c.path && c.path.length) {
          c.moving = true;
          var nx = c.path[0], tx = nx.i + 0.5, ty = nx.j + 0.5, dx = tx - c.x, dy = ty - c.y, dist = Math.sqrt(dx * dx + dy * dy), st = (c.run ? 2.6 : 1.5) * dt;
          if (Math.abs(dx) > Math.abs(dy)) c.dir = dx > 0 ? 0 : 2; else if (Math.abs(dy) > 0.001) c.dir = dy > 0 ? 1 : 3;
          if (dist <= st) { c.x = tx; c.y = ty; c.path.shift(); } else { c.x += dx / dist * st; c.y += dy / dist * st; }
          c.phase += dt * 16;
          return;
        }
        c.moving = false; c.run = false;
        if ((c.idle -= dt) > 0) return;
        var buddy = self.kids[Math.floor(Math.random() * self.kids.length)];
        var goal = buddy && buddy.visible && Math.random() < 0.6 ? { i: Math.floor(buddy.x), j: Math.floor(buddy.y) } : self.randomTile();
        if (goal) {
          var route = self.route({ i: Math.floor(c.x), j: Math.floor(c.y) }, goal, false);
          if (route) { if (route.length > 1 && buddy) route.pop(); c.path = route; c.run = Math.random() < 0.35; }
        }
        c.idle = 1.5 + Math.random() * 3;
      } else if (c.type === 'duck') {
        var pc = self.pondC;
        if (!pc) return;
        if (c.lead) {
          c.a += dt * 0.32 * (c.rush ? 2.4 : 1);
          if (c.rush) { c.rush -= dt; if (c.rush < 0) c.rush = 0; }
          var rr = 0.62 + 0.25 * Math.sin(c.a * 0.7);
          var x = pc.x + Math.cos(c.a) * rr, y = pc.y + Math.sin(c.a) * rr * 0.85;
          if (self.waterAt(x, y)) { c.vx = x - (c.x || x); c.vy = y - (c.y || y); c.x = x; c.y = y; }
          c.hist = c.hist || [];
          c.hist.push({ x: c.x, y: c.y, t: t });
          if (c.hist.length > 400) c.hist.splice(0, 100);
        } else {
          var h = c.follow.hist || [], want = t - c.lag * (c.follow.rush ? 0.5 : 1), best = h[h.length - 1];
          for (var q = h.length - 1; q >= 0; q--) { if (h[q].t <= want) { best = h[q]; break; } }
          if (best) { c.vx = best.x - (c.x || best.x); c.vy = best.y - (c.y || best.y); c.x = best.x; c.y = best.y; }
        }
        if (c.vx !== undefined && Math.abs(c.vx) + Math.abs(c.vy) > 0.0001) c.dir = Math.abs(c.vx) > Math.abs(c.vy) ? (c.vx > 0 ? 0 : 2) : (c.vy > 0 ? 1 : 3);
      } else if (c.type === 'cat') {
        if (!c.sleep && Math.random() < dt * 0.05) c.sleep = true;
      }
    });
  };
  WP.waterAt = function (x, y) {
    var i = Math.floor(x), j = Math.floor(y), G = this.G;
    return i >= 0 && j >= 0 && i < G.n && j < G.n && G.water[i][j];
  };

  /* ========================================================== particles */
  WP.particle = function (o) { if (this.parts.length < (this.cfg.n >= 15 ? 260 : 140)) this.parts.push(o); return o; };
  WP.spark = function (x, y, z) {
    var I = this.iso;
    this.particle({ k: 'spark', x: I.sx(x, y) + (Math.random() - 0.5) * 6, y: I.sy(x, y, z), vx: (Math.random() - 0.5) * 14, vy: -30 - Math.random() * 30, life: 0, max: 0.9 + Math.random() * 0.6 });
  };
  WP.note = function (x, y, z) {
    var I = this.iso;
    this.particle({ k: 'note', x: I.sx(x, y), y: I.sy(x, y, z), vx: (Math.random() - 0.5) * 16, vy: -22, life: 0, max: 1.8, c: pick(Math.random, ['#ff6fa8', '#7fe7ff', '#ffd23f', '#8af0b6']) });
  };
  WP.sparkle = function (x, y, z, n) {
    var I = this.iso, sx = I.sx(x, y), sy = I.sy(x, y, z);
    for (var q = 0; q < (n || 8); q++) {
      var a = Math.random() * TAU, sp = 20 + Math.random() * 50;
      this.particle({ k: 'star', x: sx, y: sy, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - 20, life: 0, max: 0.7 + Math.random() * 0.5, c: pick(Math.random, ['#ffd23f', '#ffffff', '#7fe7ff', '#ff9fd0']), s: 2 + Math.random() * 2 });
    }
  };
  WP.hearts = function (sx, sy, n) {
    for (var q = 0; q < (n || 3); q++) this.particle({ k: 'heart', x: sx + (Math.random() - 0.5) * 10, y: sy, vx: (Math.random() - 0.5) * 18, vy: -26 - Math.random() * 14, life: 0, max: 1.3, s: 3 + Math.random() * 2 });
  };
  WP.splash = function (x, y, big) {
    var I = this.iso, sx = I.sx(x, y), sy = I.sy(x, y, -0.2);
    this.particle({ k: 'ring', x: sx, y: sy, life: 0, max: 1.1, s: big ? 1.4 : 1 });
    for (var q = 0; q < (big ? 9 : 5); q++) {
      var a = Math.random() * TAU;
      this.particle({ k: 'drop', x: sx, y: sy, vx: Math.cos(a) * 26, vy: -40 - Math.random() * 40, life: 0, max: 0.7, g: 160 });
    }
  };
  WP.fishJump = function (x, y, kid) {
    var I = this.iso, self = this;
    this.splash(x, y, false);
    this.particle({ k: 'fish', x0: I.sx(x, y), y0: I.sy(x, y, -0.2), life: 0, max: 0.95, dx: (Math.random() < 0.5 ? -1 : 1) * 14, c: pick(Math.random, ['#ff8a3d', '#ffcf3a', '#7fe7ff']),
                    done: function () { self.splash(x + 0.3, y + 0.1, false); } });
    if (kid) { kid.happy = 1.2; kid.vz = 2.6; this.say(kid, pick(Math.random, ['a fish!', 'whoa!', '!'])); }
  };
  WP.confetti = function (sx, sy, n) {
    for (var q = 0; q < (n || 24); q++) {
      var a = -Math.PI / 2 + (Math.random() - 0.5) * 1.8, sp = 60 + Math.random() * 90;
      this.particle({ k: 'confetti', x: sx, y: sy, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, life: 0, max: 2.4, c: pick(Math.random, BRICKS), r: Math.random() * TAU, vr: (Math.random() - 0.5) * 12 });
    }
  };
  WP.firework = function (fromX, fromY, toX, toY, color) {
    this.particle({ k: 'rocket', x: fromX, y: fromY, tx: toX, ty: toY, life: 0, max: 0.9 + Math.random() * 0.3, c: color || pick(Math.random, ['#ffd23f', '#ff6fa8', '#7fe7ff', '#8af0b6', '#c4a5ff']) });
  };
  WP.burst = function (x, y, c) {
    var c2 = pick(Math.random, ['#ffd23f', '#ff6fa8', '#7fe7ff', '#8af0b6', '#c4a5ff', '#ffffff']);
    for (var q = 0; q < 46; q++) {
      var a = q / 46 * TAU + Math.random() * 0.15, sp = 46 + Math.random() * 44;
      this.particle({ k: 'fw', x: x, y: y, px: x, py: y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, life: 0, max: 1.4 + Math.random() * 0.6, c: q % 3 ? c : c2, glit: Math.random() < 0.35 });
    }
    this.particle({ k: 'flash', x: x, y: y, life: 0, max: 0.45, c: c });
    this.domeRipple(x, y, 0.5);
  };
  WP.updateParticles = function (dt) {
    var list = this.parts, out = [];
    for (var q = 0; q < list.length; q++) {
      var p = list[q];
      p.life += dt;
      if (p.life >= p.max) { if (p.done) p.done(); if (p.k === 'rocket') this.burst(p.x, p.y, p.c); if (p.k === 'balloon' && p.pop) this.confetti(p.x, p.y, 12); continue; }
      switch (p.k) {
        case 'spark': p.x += p.vx * dt; p.y += p.vy * dt; p.vx *= 0.98; break;
        case 'note': p.x += Math.sin(p.life * 5) * 0.4 + p.vx * dt * 0.3; p.y += p.vy * dt; break;
        case 'star': case 'heart': p.x += p.vx * dt; p.y += p.vy * dt; p.vy += 30 * dt; p.vx *= 0.97; break;
        case 'drop': p.x += p.vx * dt; p.y += p.vy * dt; p.vy += p.g * dt; break;
        case 'confetti': p.x += p.vx * dt; p.y += p.vy * dt; p.vy += 90 * dt; p.vx *= 0.97; p.vy *= 0.97; p.r += p.vr * dt; p.x += Math.sin(p.life * 6 + p.r) * 0.4; break;
        case 'fw': p.px = p.x; p.py = p.y; p.x += p.vx * dt; p.y += p.vy * dt; p.vx *= 0.955; p.vy = p.vy * 0.955 + 30 * dt; break;
        case 'rocket': var e = p.life / p.max; p.x = lerp(p.x, p.tx, Math.min(1, dt * 3)); p.y = lerp(p.y, p.ty, Math.min(1, dt * 3.4)); if (Math.random() < 0.8) out.push({ k: 'trail', x: p.x, y: p.y, life: 0, max: 0.45, c: p.c }); break;
        case 'smoke': p.x += p.vx * dt + Math.sin(p.life * 1.5 + p.s) * 0.15; p.y += p.vy * dt; break;
        case 'mist': p.x += p.vx * dt; p.y += p.vy * dt; break;
        case 'leaf': case 'petal': p.x += Math.sin(p.life * 2 + p.s) * 0.5 + p.vx * dt; p.y += p.vy * dt; p.r += dt * 3; if (p.y > p.floor) { p.y = p.floor; p.vy = 0; p.vx = 0; p.landed = true; } break;
        case 'snow': p.x += Math.sin(p.life * 1.4 + p.s) * 0.25; p.y += p.vy * dt; if (p.y > p.floor) { p.y = p.floor; p.vy = 0; } break;
        case 'balloon': this.stepBalloon(p, dt); break;
        case 'lantern': this.stepLantern(p, dt); break;
        case 'bubble': p.x += Math.sin(p.life * 3 + p.s) * 0.4 + p.vx * dt; p.y += p.vy * dt; break;
        default: break;
      }
      out.push(p);
    }
    this.parts = out;
  };

  /* ============================================================== setup */
  WP.setup = function () {
    var host = this.host, self = this;
    var c = this.canvas = document.createElement('canvas');
    c.className = 'haven-canvas';
    c.setAttribute('aria-hidden', 'true');
    // positioned here as well as in haven.css, so the canvas can never push
    // its host's size around (and a resize can never feed on itself)
    c.style.cssText = 'position:absolute;left:0;top:0;width:100%;height:100%;display:block';
    if (global.getComputedStyle && getComputedStyle(host).position === 'static') host.style.position = 'relative';
    if (!host.style.aspectRatio && global.getComputedStyle && getComputedStyle(host).aspectRatio === 'auto' && host.getBoundingClientRect().height < 10) {
      host.style.aspectRatio = this.W + ' / ' + this.H;
    }
    host.appendChild(c);
    this.ctx = c.getContext('2d');
    if (!this.ctx) throw new Error('no canvas');
    host.classList.add('haven-live');
    host.haven = this;
    this.resize();
    if ('ResizeObserver' in global) {
      this.ro = new ResizeObserver(function () { self.resize(); });
      this.ro.observe(host);
    } else {
      global.addEventListener('resize', function () { self.resize(); });
    }
    if ('IntersectionObserver' in global) {
      this.io = new IntersectionObserver(function (es) { self.visible = es[0].isIntersecting; if (self.visible) self.kick(); }, { rootMargin: '80px' });
      this.io.observe(host);
    }
    document.addEventListener('visibilitychange', function () { if (!document.hidden) self.kick(); });
    if (!reduced) {
      c.addEventListener('pointermove', function (e) { self.onMove(e); });
      c.addEventListener('pointerleave', function () { self.pointer = null; c.style.cursor = ''; });
      c.addEventListener('click', function (e) { self.onTap(e); });
    }
    this.last = clock();
    if (reduced) {
      this.warm(6);
      this.draw();
    } else {
      this.warm(1.5);
      this.kick();
    }
  };
  /* run the simulation a little before the first frame so it starts alive */
  WP.warm = function (seconds) {
    var steps = Math.round(seconds / 0.05);
    for (var q = 0; q < steps; q++) this.step(0.05, true);
  };
  WP.resize = function () {
    var r = this.host.getBoundingClientRect();
    if (!r.width || !r.height) return;
    var dpr = Math.min(this.slow > 1 ? 1.25 : 2, global.devicePixelRatio || 1);
    var cw = Math.round(r.width * dpr), ch = Math.round(r.height * dpr);
    var scale = Math.min(r.width / this.W, r.height / this.H);
    if (this.canvas.width === cw && this.canvas.height === ch && Math.abs((this.scale || 0) - scale) < 0.001) return;
    this.canvas.width = cw;
    this.canvas.height = ch;
    this.cssW = r.width; this.cssH = r.height;
    this.dpr = dpr;
    this.scale = scale;
    this.offX = (r.width - this.W * scale) / 2;
    this.offY = (r.height - this.H * scale) / 2;
    this.prerender();
    if (reduced) this.draw();
  };
  /* everything that never moves, painted once at this resolution */
  WP.prerender = function () {
    var k = this.scale * this.dpr, self = this;
    var base = this.base || (this.base = document.createElement('canvas'));
    base.width = Math.ceil(this.W * k);
    base.height = Math.ceil(this.H * k);
    var bx = base.getContext('2d');
    bx.setTransform(k, 0, 0, k, 0, 0);
    bx.clearRect(0, 0, this.W, this.H);
    this.G.crystals.length = 0;
    paintTerrain(bx, this);
    this.G.props.forEach(function (p) { self.cacheProp(p, k); });
    this.glass = null;
  };
  WP.cacheProp = function (p, k) {
    var def = PROPS[p.type];
    if (!def || !def.paint) return;
    var b = def.box(p), I = this.iso, minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9;
    for (var a = 0; a < 2; a++) for (var c = 0; c < 2; c++) for (var e = 0; e < 2; e++) {
      var x = b[0] + a * b[3], y = b[1] + c * b[4], z = b[2] + e * b[5];
      var sx = I.sx(x, y), sy = I.sy(x, y, z);
      if (sx < minX) minX = sx; if (sx > maxX) maxX = sx; if (sy < minY) minY = sy; if (sy > maxY) maxY = sy;
    }
    minX -= 4; minY -= 6; maxX += 4; maxY += 4;
    var cv = p.cache || document.createElement('canvas');
    cv.width = Math.max(1, Math.ceil((maxX - minX) * k));
    cv.height = Math.max(1, Math.ceil((maxY - minY) * k));
    var cx = cv.getContext('2d');
    cx.setTransform(k, 0, 0, k, -minX * k, -minY * k);
    cx.clearRect(minX, minY, maxX - minX, maxY - minY);
    def.paint(cx, I, p, this);
    p.cache = cv;
    p.cx = minX; p.cy = minY; p.cw = maxX - minX; p.ch = maxY - minY;
    p.ax = I.sx(p.i + p.fw / 2, p.j + p.fd / 2);
    p.ay = I.sy(p.i + p.fw / 2, p.j + p.fd / 2, p.z || 0);
    var depth = (p.i + p.fw - 0.5) + (p.j + p.fd - 0.5) - 0.5 + (p.depthBias || 0);
    if (p.type === 'column') depth = p.i + p.j + 0.45;
    if (p.type === 'tree' && p.z) depth += 0.05;
    if (p.type === 'log' || p.type === 'dock' || p.type === 'sunflower' || p.type === 'pumpkin') depth = p.i + p.j + 0.2;
    if (p.front) depth = p.i + p.j + 1.45;
    p.depth = depth;
  };

  /* =========================================================== stepping */
  WP.kick = function () {
    if (this.raf || reduced) return;
    var self = this;
    this.last = clock();
    this.raf = requestAnimationFrame(function loop(now) {
      self.raf = 0;
      if (!self.visible || document.hidden || self.dead) return;
      var dt = Math.min(0.05, Math.max(0.001, (now - self.last) / 1000));
      self.last = now;
      var t0 = clock();
      try {
        self.step(dt, false);
        self.draw();
      } catch (err) {
        // one bad frame must not freeze the world: say so once, carry on
        if (!self.warned && global.console) { self.warned = true; console.warn('haven:', err); }
      }
      self.budget(clock() - t0);
      self.raf = requestAnimationFrame(loop);
    });
  };
  WP.budget = function (ms) {
    this.avg = this.avg ? this.avg * 0.95 + ms * 0.05 : ms;
    if (this.avg > 14 && this.slow < 2 && this.t > 3) { this.slow++; this.avg = 0; this.canvas.width = 0; this.resize(); }
  };
  WP.step = function (dt, warming) {
    this.dt = dt;
    this.t += dt;
    var self = this;
    if (this.lightMix < 1) this.lightMix = Math.min(1, this.lightMix + dt * 0.8);
    this.kids.forEach(function (k) { self.updateKid(k, dt); if (k.bubble && self.t - k.bubble.t0 > k.bubble.dur) k.bubble = null; });
    this.updateCritters(dt);
    this.updateParticles(dt);
    this.ambient(dt);
    if (this.mode === 'build') this.stepBuild(dt);
    if (this.mode === 'mini') this.stepMini(dt, warming);
    if (warming) return;
    if (this.cfg.threats && (this.nextThreat -= dt) <= 0) {
      if (this.threats.length < 2) this.launch();
      this.nextThreat = this.cfg.threats / 1000 * (0.8 + Math.random() * 0.5);
    }
    if (this.cfg.events && (this.nextEvent -= dt) <= 0) { this.event(); this.nextEvent = 16 + Math.random() * 12; }
    this.stepThreats(dt);
    this.stepStorm(dt);
    if (this.badgeHit > 0) this.badgeHit -= dt;
    if (this.flash > 0) this.flash -= dt * 2.5;
    if (this.rainbow > 0) this.rainbow -= dt;
    var hits = this.hits;
    for (var q = hits.length - 1; q >= 0; q--) if ((hits[q].life += dt) > 1.1) hits.splice(q, 1);
  };
  /* the background life: smoke, leaves or snow, fireflies, waterfall mist */
  WP.ambient = function (dt) {
    var I = this.iso, G = this.G, S = this.S, self = this, d = this.dome();
    G.props.forEach(function (p) {
      if (p.type === 'house' && p.stage <= self.stage && Math.random() < dt * 2.2) {
        self.particle({ k: 'smoke', x: I.sx(p.i + 1.51, p.j + 0.57), y: I.sy(p.i + 1.51, p.j + 0.57, 3.0), vx: 4 + Math.random() * 3, vy: -9 - Math.random() * 5, life: 0, max: 3.4, s: Math.random() * 6 });
      }
    });
    var fall = S.fall, rate = this.cfg.n >= 15 ? 3 : 1.4;
    if (fall === 'leaf' || fall === 'petal') {
      if (Math.random() < dt * rate) {
        var trees = G.props.filter(function (p) { return p.type === 'tree' && p.kind === 'oak' && p.stage <= self.stage; });
        var tr = trees[Math.floor(Math.random() * trees.length)];
        if (tr) {
          var sx = I.sx(tr.i + 0.2 + Math.random() * 0.6, tr.j + 0.2 + Math.random() * 0.6), sy = I.sy(tr.i + 0.5, tr.j + 0.5, (tr.z || 0) + 1.3);
          this.particle({ k: fall, x: sx, y: sy, vx: (Math.random() - 0.5) * 8, vy: 7 + Math.random() * 6, life: 0, max: 6, r: Math.random() * TAU, s: Math.random() * 6,
                          c: fall === 'leaf' ? pick(Math.random, S.leaves) : pick(Math.random, ['#ffc6dd', '#ffe1ee', '#ff9cc2']), floor: I.sy(tr.i + 0.5 + Math.random() * 1.5, tr.j + 0.5 + Math.random() * 1.5, 0) });
        }
      }
    } else if (fall === 'snow' && this.domeK > 0.5) {
      if (Math.random() < dt * rate * 3) {
        var a = Math.random() * Math.PI, rr = Math.random();
        var px = d.cx + Math.cos(a) * d.R * 0.85 * rr * (Math.random() < 0.5 ? -1 : 1);
        this.particle({ k: 'snow', x: px, y: d.by - d.H * 0.92 + Math.random() * 30, vy: 10 + Math.random() * 8, life: 0, max: 9, s: Math.random() * 6, r: 0.8 + Math.random() * 1.2, floor: d.by + Math.random() * 40 - 30 });
      }
    }
    if (G.exit && Math.random() < dt * 5) {
      var e = this.fallPoint();
      this.particle({ k: 'mist', x: e.x + (Math.random() - 0.5) * 12, y: e.y, vx: (Math.random() - 0.5) * 10, vy: -4 - Math.random() * 4, life: 0, max: 1.6, s: 4 + Math.random() * 5 });
    }
    if (this.storm === null && this.cfg.outside && this.light !== 'day') {
      // fireflies round the island at dusk
      if (!this.flies) {
        this.flies = [];
        for (var f = 0; f < (this.cfg.n >= 15 ? 14 : 6); f++) {
          var tile = this.randomTile();
          if (tile) this.flies.push({ x: tile.i + 0.5, y: tile.j + 0.5, z: 0.5 + Math.random(), a: Math.random() * TAU, p: Math.random() * TAU });
        }
      }
    }
    if (this.flies) this.flies.forEach(function (fl) { fl.a += (Math.random() - 0.5) * dt * 3; fl.x += Math.cos(fl.a) * dt * 0.25; fl.y += Math.sin(fl.a) * dt * 0.25; fl.z = clamp(fl.z + Math.sin(self.t + fl.p) * dt * 0.2, 0.3, 2.2); if (!self.inIsland(Math.floor(fl.x), Math.floor(fl.y))) fl.a += Math.PI; });
    if (this.birds) this.birds.forEach(function (b) { b.a += dt * b.sp; });
  };
  WP.fallPoint = function () {
    var G = this.G, e = G.exit, I = this.iso, b = G.bot[e.i][e.j] - 2.4;
    return e.dir === 'x' ? { x: I.sx(e.i + 1.05, e.j + 0.5), y: I.sy(e.i + 1.05, e.j + 0.5, b) } : { x: I.sx(e.i + 0.5, e.j + 1.05), y: I.sy(e.i + 0.5, e.j + 1.05, b) };
  };

  /* ------------------------------------------------------------ events */
  WP.event = function () {
    var list = ['fireworks', 'lanterns', 'balloons', 'storm', 'party', 'bubbles'];
    if (this.light === 'day') list = ['balloons', 'storm', 'party', 'bubbles'];
    var name;
    for (var tries = 0; tries < 8; tries++) { name = list[Math.floor(Math.random() * list.length)]; if (name !== this.lastEvent) break; }
    this.lastEvent = name;
    this['ev_' + name]();
  };
  WP.domeTarget = function () {
    var d = this.dome();
    var a = Math.PI * (0.2 + Math.random() * 0.6), rr = 0.35 + Math.random() * 0.4;
    return { x: d.cx + Math.cos(a) * d.R * rr, y: d.by - Math.sin(a) * d.H * (0.55 + Math.random() * 0.28) };
  };
  WP.ev_fireworks = function () {
    var self = this, I = this.iso, G = this.G;
    var launch = G.plaza ? { x: I.sx(G.plaza.i + 0.5, G.plaza.j + 0.5), y: I.sy(G.plaza.i + 0.5, G.plaza.j + 0.5, 0.3) } : { x: this.cfg.cx, y: this.cfg.cy };
    for (var q = 0; q < 5; q++) (function (q) { setTimeout(function () { var tg = self.domeTarget(); self.firework(launch.x, launch.y, tg.x, tg.y); }, q * 520); })(q);
    this.kids.forEach(function (k) { if (!k.ride && Math.random() < 0.6) { k.happy = 3; k.wave = 1; if (Math.random() < 0.4) self.say(k, pick(Math.random, ['ooh!', 'wow!', 'yay!'])); } });
  };
  WP.ev_lanterns = function () {
    var I = this.iso;
    for (var q = 0; q < 7; q++) {
      var tile = this.randomTile();
      if (!tile) continue;
      this.particle({ k: 'lantern', x: I.sx(tile.i + 0.5, tile.j + 0.5), y: I.sy(tile.i + 0.5, tile.j + 0.5, 1), vx: 0, vy: -10 - Math.random() * 6, life: -q * 0.7, max: 16, s: Math.random() * 6 });
    }
  };
  WP.ev_balloons = function () {
    var k = this.kids.filter(function (k) { return k.visible && !k.ride && !k.path; })[0];
    if (!k) return;
    this.say(k, 'up they go!');
    k.happy = 2;
    for (var q = 0; q < 3; q++) this.particle({ k: 'balloon', x: k.sx + (q - 1) * 6, y: k.sy, vx: (q - 1) * 6, vy: -18 - q * 3, life: 0, max: 14, c: pick(Math.random, ['#ff5a5f', '#ffd23f', '#7fe7ff', '#c4a5ff', '#8af0b6']), s: Math.random() * 6, pop: true });
  };
  WP.ev_storm = function () {
    if (!this.cfg.outside) return;
    var d = this.dome();
    this.storm = { t: 0, dur: 11, x: d.cx - d.R * 1.2, drops: [], slides: [], bolt: 3.5 + Math.random() * 4 };
    var k = this.kids[Math.floor(Math.random() * this.kids.length)];
    var self = this;
    setTimeout(function () { if (k) { k.wave = 2; self.say(k, 'can’t get us!'); } }, 2500);
  };
  WP.ev_party = function () {
    var self = this, I = this.iso, G = this.G;
    var at = G.plaza || { i: G.c, j: G.c };
    this.confetti(I.sx(at.i + 0.5, at.j + 0.5), I.sy(at.i + 0.5, at.j + 0.5, 1.4), 40);
    this.kids.forEach(function (k) { if (!k.ride && k.visible) { k.happy = 2.5; k.vz = 2.8; if (Math.random() < 0.4) self.say(k, pick(Math.random, ['party!', 'yay!', 'woo!'])); } });
  };
  WP.ev_bubbles = function () {
    var k = this.kids.filter(function (k) { return k.visible && !k.ride; })[0];
    if (!k) return;
    for (var q = 0; q < 12; q++) this.particle({ k: 'bubble', x: k.sx + 6, y: k.sy + 6, vx: 6 + Math.random() * 10, vy: -10 - Math.random() * 10, life: -q * 0.25, max: 3.5, s: Math.random() * 6, r: 2 + Math.random() * 3 });
  };
  WP.stepBalloon = function (p, dt) {
    var d = this.dome();
    p.x += Math.sin(p.life * 1.6 + p.s) * 0.3 + p.vx * dt;
    p.y += p.vy * dt;
    var nx = (p.x - d.cx) / (d.R * 0.92), ny = (d.by - p.y + 14) / (d.H * 0.92);
    if (ny > 0 && nx * nx + ny * ny > 1) { p.vy = Math.abs(p.vy) * 0.35; p.vx += (p.x > d.cx ? -1 : 1) * 4; p.bumped = (p.bumped || 0) + 1; if (p.bumped === 1) this.domeRipple(p.x, p.y - 14, 0.35); }
    else p.vy = Math.max(-20, p.vy - 6 * dt);
  };
  WP.stepLantern = function (p, dt) {
    if (p.life < 0) return;
    var d = this.dome();
    p.x += Math.sin(p.life * 0.9 + p.s) * 0.25;
    var ceil = d.by - d.H * 0.78 + Math.abs(p.x - d.cx) / d.R * d.H * 0.45;
    if (p.y > ceil) p.y += p.vy * dt;
  };
  WP.say2 = WP.say;

  /* ----------------------------------------------------------- threats */
  WP.dome = function () {
    var cfg = this.cfg, k = this.domeK, R = (this.G.R + cfg.pad) * SQ2 * this.iso.hw;
    return { cx: cfg.cx, by: cfg.cy + this.iso.hh * 0.6, R: R, Rb: R * 0.5, H: R * cfg.hk * (0.25 + 0.75 * smooth(k)), k: k };
  };
  WP.launch = function () {
    var d = this.dome(), spec = THREATS[Math.floor(Math.random() * THREATS.length)];
    var narrow = this.cssW < 420;
    var th = (24 + Math.random() * 132) * Math.PI / 180;
    var px = d.cx + d.R * Math.cos(th), py = d.by - d.H * Math.sin(th);
    var nx = Math.cos(th) / d.R, ny = -Math.sin(th) / d.H, len = Math.sqrt(nx * nx + ny * ny);
    nx /= len; ny /= len;
    var far = narrow ? 150 : 230;
    this.threats.push({ spec: spec, img: icon(spec.icon), px: px, py: py, nx: nx, ny: ny, sx: px + nx * far, sy: py + ny * far, t: 0, hit: false });
  };
  WP.stepThreats = function (dt) {
    var list = this.threats;
    for (var q = list.length - 1; q >= 0; q--) {
      var a = list[q];
      a.t += dt / 1.15;
      if (a.t >= 1 && !a.hit) {
        a.hit = true;
        this.domeRipple(a.px, a.py, 1);
        this.badgeHit = 0.7;
        for (var s = 0; s < 8; s++) {
          var ang = Math.atan2(a.ny, a.nx) + (s - 3.5) * 0.4, sp = 50 + Math.random() * 40;
          this.sky.push({ k: 'spark', x: a.px, y: a.py, vx: Math.cos(ang) * sp, vy: Math.sin(ang) * sp, life: 0, max: 0.55 });
        }
        try { this.host.dispatchEvent(new CustomEvent('haven:blocked', { detail: a.spec })); } catch (e) { /* old browsers */ }
      }
      if (a.t > 1.55) list.splice(q, 1);
    }
    var sky = this.sky;
    for (q = sky.length - 1; q >= 0; q--) {
      var p = sky[q];
      p.life += dt;
      if (p.life > p.max) { sky.splice(q, 1); continue; }
      p.x += p.vx * dt; p.y += p.vy * dt;
      if (p.k === 'rain') p.vy += 0;
      else { p.vx *= 0.94; p.vy *= 0.94; }
    }
  };
  WP.domeRipple = function (x, y, power) { this.hits.push({ x: x, y: y, life: 0, p: power || 1 }); };
  WP.stepStorm = function (dt) {
    var st = this.storm, q;
    if (!st) return;
    var d = this.dome();
    st.t += dt;
    st.x = lerp(d.cx - d.R * 1.25, d.cx + d.R * 1.25, st.t / st.dur);
    var raining = st.t > 1.2 && st.t < st.dur - 1.2;
    if (raining) {
      st.acc = (st.acc || 0) + dt * 170;
      while (st.acc >= 1) {
        st.acc -= 1;
        st.drops.push({ x: st.x + (Math.random() - 0.5) * 170, y: d.by - d.H - 48 + Math.random() * 12, vy: 330 + Math.random() * 90, vx: 34 });
      }
    }
    for (q = st.drops.length - 1; q >= 0; q--) {
      var p = st.drops[q];
      p.x += p.vx * dt; p.y += p.vy * dt;
      var nx = (p.x - d.cx) / d.R, ny = (d.by - p.y) / d.H;
      if (ny > 0 && nx * nx + ny * ny <= 1) {
        st.drops.splice(q, 1);
        var th = Math.atan2(ny, nx);
        if (st.slides.length < 160) st.slides.push({ th: th, v: 0, life: 0 });
        if (Math.random() < 0.3) this.sky.push({ k: 'spark', x: p.x, y: p.y, vx: (Math.random() - 0.5) * 30, vy: -20 - Math.random() * 20, life: 0, max: 0.3, rain: true });
        continue;
      }
      if (p.y > d.by + 140) st.drops.splice(q, 1);
    }
    for (q = st.slides.length - 1; q >= 0; q--) {
      var s = st.slides[q];
      s.life += dt;
      s.v += dt * 0.9;
      s.th += (s.th < Math.PI / 2 ? -1 : 1) * s.v * dt;
      if (s.th < 0.06 || s.th > Math.PI - 0.06) {
        st.slides.splice(q, 1);
        var bx = d.cx + Math.cos(s.th) * d.R, by = d.by - Math.sin(s.th) * d.H;
        st.drops.push({ x: bx, y: by + 2, vy: 140, vx: s.th < 1 ? 20 : -20, off: true });
      }
    }
    if (st.bolt > 0 && st.t > st.bolt) {
      st.bolt = 0;
      st.boltT = 0.35;
      this.flash = 1;
      this.badgeHit = 0.9;
      this.domeRipple(d.cx, d.by - d.H, 1.3);
      try { this.host.dispatchEvent(new CustomEvent('haven:blocked', { detail: { icon: 'shield-check', what: 'a storm', title: 'The dome kept the storm out', storm: true } })); } catch (e) { /* ok */ }
    }
    if (st.boltT > 0) st.boltT -= dt;
    if (st.t >= st.dur) { this.storm = null; this.rainbow = 7; }
  };

  /* ---------------------------------------------------- build and mini */
  WP.stepBuild = function (dt) {
    var target = this.stage >= 5 ? 1 : 0;
    this.domeK = target ? Math.min(1, this.domeK + dt / 1.6) : Math.max(0, this.domeK - dt * 2.5);
  };
  WP.stepMini = function (dt, warming) {
    var d = this.dome(), self = this;
    this.mini = this.mini || { t: 0, bubbles: [], approve: 0, step: 0 };
    var m = this.mini, cyc = 10.5;
    m.t += dt;
    var lt = m.t % cyc, script = [[0.5, 'bad', 0], [2.6, 'bad', 1], [4.6, 'bad', 2], [6.4, 'good', 0]];
    if (lt < (m.prev || 0)) { m.step = 0; m.approve = 0; }
    m.prev = lt;
    while (m.step < script.length && lt >= script[m.step][0]) {
      var sc = script[m.step++];
      var text = sc[1] === 'good' ? this.goodText : this.badTexts[sc[2] % this.badTexts.length];
      var fromLeft = sc[2] % 2 === 0;
      var th = sc[1] === 'good' ? 0.35 : (fromLeft ? Math.PI * (0.72 + Math.random() * 0.12) : Math.PI * (0.14 + Math.random() * 0.12));
      var px = d.cx + d.R * Math.cos(th), py = d.by - d.H * Math.sin(th);
      var nx = Math.cos(th) / d.R, ny = -Math.sin(th) / d.H, len = Math.sqrt(nx * nx + ny * ny);
      nx /= len; ny /= len;
      m.bubbles.push({ text: text, good: sc[1] === 'good', px: px, py: py, nx: nx, ny: ny, sx: px + nx * 150, sy: py + ny * 90, t: 0, hit: false });
    }
    if (lt > 8.1 && !m.approve) m.approve = m.t;
    for (var q = m.bubbles.length - 1; q >= 0; q--) {
      var b = m.bubbles[q];
      b.t += dt / (b.good ? 1.6 : 1.1);
      if (!b.good && b.t >= 1 && !b.hit) { b.hit = true; this.domeRipple(b.px, b.py, 0.8); this.badgeHit = 0.7; }
      if (b.good && b.t >= 1.55 && !b.hit) { b.hit = true; var k = this.kids[0]; if (k) { k.happy = 1.6; k.vz = 2.2; this.hearts(k.sx, k.sy, 3); } }
      if (b.t > (b.good ? 2.6 : 1.6)) m.bubbles.splice(q, 1);
    }
  };

  /* ============================================================ drawing */
  WP.draw = function () {
    var ctx = this.ctx, k = this.scale * this.dpr, t = this.t, I = this.iso, self = this;
    if (!ctx || !this.scale) return;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    var bob = reduced ? 0 : Math.sin(t * 0.9) * 3.5;
    ctx.setTransform(k, 0, 0, k, this.offX * this.dpr, (this.offY + bob * this.scale) * this.dpr);
    var d = this.dome();
    this.drawBack(ctx, d);
    ctx.drawImage(this.base, 0, 0, this.W, this.H);
    this.drawWater(ctx, t);
    this.drawSprites(ctx, t);
    this.drawParts(ctx, t, false);
    this.drawLight(ctx, t, d);
    this.drawParts(ctx, t, true);
    this.drawBubbles(ctx, t);
    if (this.domeK > 0.01) this.drawFront(ctx, d, t);
    if (this.mode === 'mini') this.drawMini(ctx, d, t);
    this.drawOutside(ctx, d, t);
    if (this.domeK > 0.5) this.drawBadge(ctx, d, t);
  };
  WP.drawBack = function (ctx, d) {
    var t = this.t;
    // the glow under the island
    var g = ctx.createRadialGradient(d.cx, d.by + 40, 10, d.cx, d.by + 40, d.R * 0.95);
    var pulse = 0.5 + 0.5 * Math.sin(t * 1.3);
    g.addColorStop(0, 'rgba(140,200,255,' + (0.16 + pulse * 0.08).toFixed(3) + ')');
    g.addColorStop(0.5, 'rgba(160,120,255,0.08)');
    g.addColorStop(1, 'rgba(160,120,255,0)');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.ellipse(d.cx, d.by + 40, d.R * 0.95, d.R * 0.55, 0, 0, TAU); ctx.fill();
    if (this.domeK <= 0.01) return;
    // the inside of the glass, faintly
    ctx.save();
    ctx.globalAlpha = d.k;
    this.domePath(ctx, d);
    var fill = ctx.createRadialGradient(d.cx, d.by - d.H * 0.5, d.R * 0.1, d.cx, d.by - d.H * 0.35, d.R * 1.05);
    var dayish = this.light === 'day';
    fill.addColorStop(0, dayish ? 'rgba(220,235,255,0.06)' : 'rgba(200,220,255,0.03)');
    fill.addColorStop(0.75, dayish ? 'rgba(150,185,255,0.12)' : 'rgba(150,170,255,0.09)');
    fill.addColorStop(1, dayish ? 'rgba(140,170,255,0.26)' : 'rgba(170,150,255,0.22)');
    ctx.fillStyle = fill;
    ctx.fill();
    ctx.strokeStyle = dayish ? 'rgba(91,140,255,0.35)' : 'rgba(200,215,255,0.32)';
    ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.ellipse(d.cx, d.by, d.R, d.Rb, 0, Math.PI, TAU); ctx.stroke();
    if (this.rainbow > 0) {
      var a = Math.min(1, this.rainbow / 1.5, (7 - this.rainbow) / 1.5) * 0.4;
      var cols = ['#ff5a5f', '#ff9f43', '#ffd23f', '#5fd068', '#3c8dde', '#8b5cf6'];
      ctx.globalAlpha = a * d.k;
      ctx.lineWidth = 5;
      for (var q = 0; q < cols.length; q++) {
        ctx.strokeStyle = cols[q];
        ctx.beginPath(); ctx.ellipse(d.cx, d.by - 10, d.R * (0.78 - q * 0.035), d.H * (0.72 - q * 0.03), 0, Math.PI * 1.08, Math.PI * 1.92); ctx.stroke();
      }
    }
    ctx.restore();
  };
  WP.domePath = function (ctx, d) {
    ctx.beginPath();
    ctx.ellipse(d.cx, d.by, d.R, d.H, 0, Math.PI, TAU);
    ctx.ellipse(d.cx, d.by, d.R, d.Rb, 0, 0, Math.PI);
    ctx.closePath();
  };
  WP.drawWater = function (ctx, t) {
    var G = this.G, I = this.iso, n = G.n;
    var z = -0.2;
    for (var i = 0; i < n; i++) for (var j = 0; j < n; j++) {
      if (!G.water[i][j]) continue;
      var v = hash(i, j, 11);
      ctx.fillStyle = 'rgba(' + (52 + v * 14 | 0) + ',' + (150 + v * 20 | 0) + ',236,0.86)';
      quad(ctx, I.sx(i, j), I.sy(i, j, z), I.sx(i + 1, j), I.sy(i + 1, j, z), I.sx(i + 1, j + 1), I.sy(i + 1, j + 1, z), I.sx(i, j + 1), I.sy(i, j + 1, z));
      // ripples drifting across
      ctx.strokeStyle = 'rgba(255,255,255,0.32)';
      ctx.lineWidth = 0.8;
      for (var w = 0; w < 2; w++) {
        var u = ((t * 0.18 + v + w * 0.5) % 1), sx = I.sx(i + u, j + 0.25 + w * 0.45), sy = I.sy(i + u, j + 0.25 + w * 0.45, z);
        ctx.beginPath(); ctx.moveTo(sx - 4, sy); ctx.quadraticCurveTo(sx, sy - 1.6, sx + 4, sy); ctx.stroke();
      }
      if (Math.sin(t * 2 + v * 40) > 0.97) {
        ctx.fillStyle = 'rgba(255,255,255,0.9)';
        ctx.fillRect(I.sx(i + 0.5, j + 0.5) - 0.8, I.sy(i + 0.5, j + 0.5, z) - 0.8, 1.6, 1.6);
      }
      // the water's own face at the edge of the island
      if (!this.inIsland(i, j + 1)) {
        ctx.fillStyle = 'rgba(70,160,240,0.7)';
        quad(ctx, I.sx(i, j + 1), I.sy(i, j + 1, z), I.sx(i + 1, j + 1), I.sy(i + 1, j + 1, z), I.sx(i + 1, j + 1), I.sy(i + 1, j + 1, -1), I.sx(i, j + 1), I.sy(i, j + 1, -1));
      }
      if (!this.inIsland(i + 1, j)) {
        ctx.fillStyle = 'rgba(60,140,225,0.7)';
        quad(ctx, I.sx(i + 1, j + 1), I.sy(i + 1, j + 1, z), I.sx(i + 1, j), I.sy(i + 1, j, z), I.sx(i + 1, j), I.sy(i + 1, j, -1), I.sx(i + 1, j + 1), I.sy(i + 1, j + 1, -1));
      }
    }
    // lily pads
    for (var q = 0; q < G.lily.length; q++) {
      var l = G.lily[q], lx = I.sx(l.x, l.y), ly = I.sy(l.x, l.y, z) + Math.sin(t * 1.4 + q) * 0.5;
      ctx.fillStyle = '#4fae4f';
      ctx.beginPath(); ctx.ellipse(lx, ly, I.hw * 0.2 * l.s, I.hw * 0.1 * l.s, 0, l.r, l.r + TAU * 0.86); ctx.lineTo(lx, ly); ctx.closePath(); ctx.fill();
      if (q % 3 === 0) { ctx.fillStyle = '#ff9fd0'; ctx.beginPath(); ctx.arc(lx + 1, ly - 1.5, 1.6, 0, TAU); ctx.fill(); }
    }
    if (G.exit) this.drawFall(ctx, t);
  };
  WP.drawFall = function (ctx, t) {
    var G = this.G, e = G.exit, I = this.iso, top = -0.2, bottom = G.bot[e.i][e.j] - 2.4;
    var A, B, C, D;
    if (e.dir === 'x') {
      var X = e.i + 1.03;
      A = [I.sx(X, e.j + 0.88), I.sy(X, e.j + 0.88, top)]; B = [I.sx(X, e.j + 0.12), I.sy(X, e.j + 0.12, top)];
      C = [B[0], I.sy(X, e.j + 0.12, bottom)]; D = [A[0], I.sy(X, e.j + 0.88, bottom)];
    } else {
      var Y = e.j + 1.03;
      A = [I.sx(e.i + 0.12, Y), I.sy(e.i + 0.12, Y, top)]; B = [I.sx(e.i + 0.88, Y), I.sy(e.i + 0.88, Y, top)];
      C = [B[0], I.sy(e.i + 0.88, Y, bottom)]; D = [A[0], I.sy(e.i + 0.12, Y, bottom)];
    }
    var g = ctx.createLinearGradient(0, A[1], 0, D[1]);
    g.addColorStop(0, 'rgba(150,215,255,0.92)');
    g.addColorStop(0.75, 'rgba(150,215,255,0.5)');
    g.addColorStop(1, 'rgba(150,215,255,0)');
    ctx.fillStyle = g;
    quad(ctx, A[0], A[1], B[0], B[1], C[0], C[1], D[0], D[1]);
    ctx.strokeStyle = 'rgba(255,255,255,0.55)';
    ctx.lineWidth = 1;
    var len = D[1] - A[1];
    for (var s = 0; s < 6; s++) {
      var u = (s + 0.5) / 6;
      var x0 = lerp(A[0], B[0], u), y0 = lerp(A[1], B[1], u);
      for (var m = 0; m < 3; m++) {
        var off = ((t * 0.9 + s * 0.37 + m / 3) % 1) * len;
        ctx.globalAlpha = 0.7 * (1 - off / len);
        ctx.beginPath(); ctx.moveTo(x0, y0 + off); ctx.lineTo(x0, y0 + off + 9); ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;
    ctx.fillStyle = 'rgba(255,255,255,0.8)';
    for (var f = 0; f < 4; f++) {
      var fu = (f + 0.5) / 4;
      ctx.beginPath(); ctx.arc(lerp(A[0], B[0], fu), lerp(A[1], B[1], fu) + Math.sin(t * 9 + f) * 0.8, 1.6, 0, TAU); ctx.fill();
    }
  };
  WP.drawSprites = function (ctx, t) {
    var list = this.drawList || (this.drawList = []), G = this.G, self = this, I = this.iso;
    list.length = 0;
    var stage = this.stage;
    G.props.forEach(function (p) { if (p.cache && (p.stage || 0) <= stage) list.push(p); });
    this.kids.forEach(function (k) { if (k.visible && !k.ride) { k.depth = k.x + k.y + 0.001; list.push(k); } });
    this.critters.forEach(function (c) {
      if (c.type === 'cat' && c.onRoof) return;
      if (c.x === undefined) return;
      c.depth = c.x + c.y + (c.type === 'duck' ? -0.4 : 0);
      list.push(c);
    });
    list.sort(function (a, b) { return a.depth - b.depth; });
    var flowersDrawn = false;
    this.drawFlowers(ctx, t);
    for (var q = 0; q < list.length; q++) {
      var o = list[q];
      if (o.cache) this.drawProp(ctx, o, t);
      else if (o.type === 'dog') drawDog(ctx, I, o, t);
      else if (o.type === 'cat') drawCat(ctx, I, o, t);
      else if (o.type === 'duck') drawDuck(ctx, I, o, t);
      else this.drawKidFull(ctx, o, t);
    }
  };
  WP.drawProp = function (ctx, p, t) {
    var def = PROPS[p.type], I = this.iso;
    var born = this.mode === 'build' ? this.propBorn(p) : 1;
    if (born <= 0.01) return;
    ctx.save();
    if (born < 1) { ctx.translate(p.ax, p.ay); ctx.scale(born, born); ctx.translate(-p.ax, -p.ay); }
    if (def.sway && !reduced) {
      var sk = Math.sin(t * 1.25 + p.seed * 9) * 0.018;
      ctx.translate(p.ax, p.ay); ctx.transform(1, 0, sk, 1, 0, 0); ctx.translate(-p.ax, -p.ay);
    }
    ctx.drawImage(p.cache, p.cx, p.cy, p.cw, p.ch);
    if (def.anim) def.anim(ctx, I, p, this, t);
    if (p.type === 'house') this.drawHouseExtras(ctx, p, t);
    ctx.restore();
  };
  WP.propBorn = function (p) {
    var st = p.stage || 0;
    if (st > this.stage) { p.shownAt = null; return 0; }
    if (p.shownAt === null || p.shownAt === undefined) p.shownAt = this.t + (p.seed || 0) * 0.35;
    return backOut((this.t - p.shownAt) / 0.6);
  };
  WP.drawHouseExtras = function (ctx, p, t) {
    var cat = this.critters.filter(function (c) { return c.type === 'cat' && c.onRoof === p; })[0];
    if (cat) drawCat(ctx, this.iso, cat, t);
  };
  WP.drawFlowers = function (ctx, t) {
    var G = this.G, I = this.iso, stage = this.stage;
    for (var q = 0; q < G.flowers.length; q++) {
      var f = G.flowers[q];
      if (f.stage > stage) continue;
      var k = this.mode === 'build' ? clamp((this.t - (this.stageAt[f.stage] || 0)) / 0.5 - (q % 7) * 0.08, 0, 1) : f.s;
      if (k <= 0) continue;
      var sx = I.sx(f.x, f.y), sy = I.sy(f.x, f.y, 0), h = f.h * I.bh * 2 * k;
      var sway = Math.sin(t * 1.8 + f.p) * 1.2;
      ctx.strokeStyle = '#3f8a3a';
      ctx.lineWidth = 0.9;
      ctx.beginPath(); ctx.moveTo(sx, sy); ctx.quadraticCurveTo(sx + sway * 0.3, sy - h * 0.5, sx + sway, sy - h); ctx.stroke();
      ctx.fillStyle = f.c;
      var r = 1.5 * k;
      ctx.beginPath(); ctx.arc(sx + sway - r, sy - h, r, 0, TAU); ctx.arc(sx + sway + r, sy - h, r, 0, TAU); ctx.arc(sx + sway, sy - h - r, r, 0, TAU); ctx.arc(sx + sway, sy - h + r, r, 0, TAU); ctx.fill();
      ctx.fillStyle = '#ffd23f';
      ctx.beginPath(); ctx.arc(sx + sway, sy - h, r * 0.7, 0, TAU); ctx.fill();
    }
  };
  WP.drawKidFull = function (ctx, k, t) {
    var I = this.iso;
    drawKid(ctx, I, k, t, this);
    if (k.holding === 'rod' && k.fishing) {
      var s = k.fishing, bx = I.sx(s.bob.x, s.bob.y), by = I.sy(s.bob.x, s.bob.y, -0.2) + Math.sin(t * 3 + k.seed * 5) * 1.2;
      var tipX = I.sx(k.hx + DX[k.dir] * 0.5, k.hy + DY[k.dir] * 0.5), tipY = I.sy(k.hx + DX[k.dir] * 0.5, k.hy + DY[k.dir] * 0.5, k.hz + 0.7);
      ctx.strokeStyle = '#5b3a29'; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(I.sx(k.hx, k.hy), I.sy(k.hx, k.hy, k.hz)); ctx.lineTo(tipX, tipY); ctx.stroke();
      ctx.strokeStyle = 'rgba(255,255,255,0.6)'; ctx.lineWidth = 0.6;
      ctx.beginPath(); ctx.moveTo(tipX, tipY); ctx.quadraticCurveTo((tipX + bx) / 2, by - 4, bx, by); ctx.stroke();
      ctx.fillStyle = '#ff5a5f'; ctx.beginPath(); ctx.arc(bx, by, 1.6, 0, TAU); ctx.fill();
    }
    if (k.holding === 'kite' && k.kite) this.drawKite(ctx, k, t);
    if (k.roast) {
      ctx.strokeStyle = '#7a4e2c'; ctx.lineWidth = 0.9;
      var hx = I.sx(k.hx, k.hy), hy = I.sy(k.hx, k.hy, k.hz);
      var ex = hx + (DX[k.dir] - DY[k.dir]) * 6, ey = hy + (DX[k.dir] + DY[k.dir]) * 3;
      ctx.beginPath(); ctx.moveTo(hx, hy); ctx.lineTo(ex, ey); ctx.stroke();
      ctx.fillStyle = '#fff6e2'; ctx.beginPath(); ctx.arc(ex, ey, 1.6, 0, TAU); ctx.fill();
    }
  };
  WP.drawKite = function (ctx, k, t) {
    var I = this.iso, d = this.dome();
    var hx = I.sx(k.hx, k.hy), hy = I.sy(k.hx, k.hy, k.hz);
    var a = t * 0.7 + k.kite.a;
    var kx = hx + Math.sin(a) * 26 + 18, ky = Math.max(d.by - d.H * 0.78, hy - 96 + Math.sin(a * 2) * 9);
    ctx.strokeStyle = 'rgba(255,255,255,0.65)'; ctx.lineWidth = 0.7;
    ctx.beginPath(); ctx.moveTo(hx, hy); ctx.quadraticCurveTo((hx + kx) / 2 + 10, (hy + ky) / 2 + 10, kx, ky + 6); ctx.stroke();
    var rot = Math.sin(a * 1.3) * 0.3;
    ctx.save(); ctx.translate(kx, ky); ctx.rotate(rot);
    ctx.fillStyle = '#ff5a5f'; ctx.beginPath(); ctx.moveTo(0, -9); ctx.lineTo(6, 0); ctx.lineTo(0, 0); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#ffd23f'; ctx.beginPath(); ctx.moveTo(0, -9); ctx.lineTo(-6, 0); ctx.lineTo(0, 0); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#3c8dde'; ctx.beginPath(); ctx.moveTo(-6, 0); ctx.lineTo(0, 9); ctx.lineTo(0, 0); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#8af0b6'; ctx.beginPath(); ctx.moveTo(6, 0); ctx.lineTo(0, 9); ctx.lineTo(0, 0); ctx.closePath(); ctx.fill();
    ctx.restore();
    ctx.strokeStyle = '#ff9fd0'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(kx, ky + 8);
    for (var s = 1; s <= 5; s++) ctx.lineTo(kx - s * 3 + Math.sin(t * 6 + s) * 2.5, ky + 8 + s * 5);
    ctx.stroke();
  };
  WP.drawParts = function (ctx, t, glowing) {
    var list = this.parts;
    for (var q = 0; q < list.length; q++) {
      var p = list[q], a = 1 - p.life / p.max;
      if (p.life < 0) continue;
      var isGlow = p.k === 'fw' || p.k === 'rocket' || p.k === 'trail' || p.k === 'lantern' || p.k === 'spark' || p.k === 'flash';
      if (isGlow !== glowing) continue;
      switch (p.k) {
        case 'smoke':
          ctx.fillStyle = 'rgba(235,235,245,' + (0.4 * a).toFixed(3) + ')';
          ctx.beginPath(); ctx.arc(p.x, p.y, 2 + (1 - a) * 6, 0, TAU); ctx.fill(); break;
        case 'spark': case 'trail':
          ctx.globalCompositeOperation = 'lighter';
          ctx.fillStyle = p.k === 'trail' ? rgba(p.c, 0.5 * a) : 'rgba(255,200,90,' + a.toFixed(3) + ')';
          ctx.fillRect(p.x - 0.9, p.y - 0.9, 1.8, 1.8);
          ctx.globalCompositeOperation = 'source-over'; break;
        case 'note':
          ctx.fillStyle = rgba(p.c, Math.min(1, a * 1.5)); notePath(ctx, p.x, p.y, 4); break;
        case 'star':
          ctx.fillStyle = rgba(p.c, a); starPath(ctx, p.x, p.y, p.s); ctx.fill(); break;
        case 'heart':
          ctx.fillStyle = 'rgba(255,90,120,' + a.toFixed(3) + ')'; heartPath(ctx, p.x, p.y, p.s); ctx.fill(); break;
        case 'drop':
          ctx.fillStyle = 'rgba(190,230,255,' + a.toFixed(3) + ')'; ctx.fillRect(p.x - 0.8, p.y - 0.8, 1.6, 1.8); break;
        case 'ring':
          ctx.strokeStyle = 'rgba(255,255,255,' + (0.7 * a).toFixed(3) + ')'; ctx.lineWidth = 1;
          var rr = (1 - a) * 14 * p.s;
          ctx.beginPath(); ctx.ellipse(p.x, p.y, rr, rr * 0.5, 0, 0, TAU); ctx.stroke(); break;
        case 'fish':
          var e = p.life / p.max, fx = p.x0 + p.dx * e, fy = p.y0 - Math.sin(e * Math.PI) * 26;
          ctx.save(); ctx.translate(fx, fy); ctx.rotate((e - 0.5) * 2.4 * (p.dx > 0 ? 1 : -1));
          ctx.fillStyle = p.c; ctx.beginPath(); ctx.ellipse(0, 0, 4.2, 2, 0, 0, TAU); ctx.fill();
          ctx.beginPath(); ctx.moveTo(-3.6, 0); ctx.lineTo(-6.5, -2.4); ctx.lineTo(-6.5, 2.4); ctx.closePath(); ctx.fill();
          ctx.restore(); break;
        case 'confetti':
          ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r); ctx.fillStyle = rgba(p.c, Math.min(1, a * 2)); ctx.fillRect(-1.6, -1, 3.2, 2); ctx.restore(); break;
        case 'fw':
          ctx.globalCompositeOperation = 'lighter';
          var tw = p.glit ? (Math.sin(p.life * 40 + p.x) > 0 ? 1 : 0.25) : 1;
          ctx.strokeStyle = rgba(p.c, 0.55 * a * tw); ctx.lineWidth = 1.6;
          ctx.beginPath(); ctx.moveTo(p.px - (p.x - p.px) * 3, p.py - (p.y - p.py) * 3); ctx.lineTo(p.x, p.y); ctx.stroke();
          ctx.globalAlpha = a * tw * 0.9;
          ctx.drawImage(glow(p.c), p.x - 4.5, p.y - 4.5, 9, 9);
          ctx.globalAlpha = 1;
          ctx.fillStyle = rgba('#ffffff', a * tw); ctx.fillRect(p.x - 0.8, p.y - 0.8, 1.6, 1.6);
          ctx.globalCompositeOperation = 'source-over'; break;
        case 'flash':
          ctx.globalCompositeOperation = 'lighter';
          ctx.globalAlpha = a;
          ctx.drawImage(glow(p.c), p.x - 34, p.y - 34, 68, 68);
          ctx.globalAlpha = 1;
          ctx.globalCompositeOperation = 'source-over'; break;
        case 'rocket':
          ctx.globalCompositeOperation = 'lighter';
          ctx.drawImage(glow(p.c), p.x - 6, p.y - 6, 12, 12);
          ctx.fillStyle = '#ffffff'; ctx.fillRect(p.x - 1.3, p.y - 1.3, 2.6, 2.6);
          ctx.globalCompositeOperation = 'source-over'; break;
        case 'mist':
          ctx.fillStyle = 'rgba(220,240,255,' + (0.3 * a).toFixed(3) + ')'; ctx.beginPath(); ctx.arc(p.x, p.y, p.s * (1.4 - a * 0.4), 0, TAU); ctx.fill(); break;
        case 'leaf': case 'petal':
          ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r); ctx.globalAlpha = Math.min(1, a * 3);
          ctx.fillStyle = p.c; ctx.beginPath(); ctx.ellipse(0, 0, p.k === 'leaf' ? 2.4 : 1.8, p.k === 'leaf' ? 1.3 : 1.1, 0, 0, TAU); ctx.fill(); ctx.restore(); break;
        case 'snow':
          ctx.fillStyle = 'rgba(255,255,255,' + Math.min(0.95, a * 3).toFixed(3) + ')'; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, TAU); ctx.fill(); break;
        case 'balloon':
          var ba = Math.min(1, a * 4);
          ctx.strokeStyle = 'rgba(255,255,255,' + (0.6 * ba).toFixed(3) + ')'; ctx.lineWidth = 0.6;
          ctx.beginPath(); ctx.moveTo(p.x, p.y + 6); ctx.quadraticCurveTo(p.x + 2, p.y + 12, p.x - 1, p.y + 18); ctx.stroke();
          ctx.fillStyle = rgba(p.c, ba); ctx.beginPath(); ctx.ellipse(p.x, p.y, 4.6, 5.8, 0, 0, TAU); ctx.fill();
          ctx.fillStyle = 'rgba(255,255,255,' + (0.5 * ba).toFixed(3) + ')'; ctx.beginPath(); ctx.ellipse(p.x - 1.5, p.y - 2, 1.2, 1.8, -0.4, 0, TAU); ctx.fill(); break;
        case 'lantern':
          var la = Math.min(1, p.life * 0.8, a * 3);
          ctx.globalAlpha = la;
          ctx.globalCompositeOperation = 'lighter';
          ctx.drawImage(glow('#ffb35a'), p.x - 18, p.y - 18, 36, 36);
          ctx.globalCompositeOperation = 'source-over';
          ctx.fillStyle = '#ffcf7a'; roundRect(ctx, p.x - 4, p.y - 5, 8, 10, 2.5); ctx.fill();
          ctx.fillStyle = '#fff1c4'; roundRect(ctx, p.x - 2, p.y - 3, 4, 6, 1.5); ctx.fill();
          ctx.fillStyle = '#ff8a3d'; ctx.fillRect(p.x - 4, p.y - 5.6, 8, 1.4); ctx.fillRect(p.x - 4, p.y + 4.4, 8, 1.2);
          ctx.globalAlpha = 1; break;
        case 'bubble':
          ctx.strokeStyle = 'rgba(255,255,255,' + (0.75 * a).toFixed(3) + ')'; ctx.lineWidth = 0.7;
          ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, TAU); ctx.stroke();
          ctx.strokeStyle = 'rgba(255,170,240,' + (0.5 * a).toFixed(3) + ')'; ctx.beginPath(); ctx.arc(p.x, p.y, p.r * 0.7, 3.6, 4.6); ctx.stroke(); break;
        default: break;
      }
    }
    if (!glowing && this.birds && this.domeK > 0.5) {
      var d = this.dome();
      ctx.strokeStyle = 'rgba(40,40,70,0.75)'; ctx.lineWidth = 1.1;
      this.birds.forEach(function (b) {
        var bx = d.cx + Math.cos(b.a) * d.R * b.rr, by = d.by - d.H * (0.55 + b.h) + Math.sin(b.a * 2) * 6, flap = Math.sin(t * 9 + b.p) * 2.2;
        ctx.beginPath(); ctx.moveTo(bx - 4, by - flap); ctx.quadraticCurveTo(bx - 2, by - 1, bx, by); ctx.quadraticCurveTo(bx + 2, by - 1, bx + 4, by - flap); ctx.stroke();
      });
    }
    if (!glowing && this.ballGame) this.drawBall(ctx, t);
    if (!glowing && this.mode === 'mini' && this.kids[0]) {
      var k = this.kids[0], I = this.iso;
      if (!k.happy || k.happy <= 0) {
        var c = (t % 1.4) / 1.4, bh = Math.abs(Math.sin(c * Math.PI)) * 0.9;
        var bx = I.sx(k.x + 0.45, k.y + 0.1), by = I.sy(k.x + 0.45, k.y + 0.1, 0.12 + bh);
        ctx.fillStyle = 'rgba(20,30,60,0.18)'; ctx.beginPath(); ctx.ellipse(I.sx(k.x + 0.45, k.y + 0.1), I.sy(k.x + 0.45, k.y + 0.1, 0), 3, 1.5, 0, 0, TAU); ctx.fill();
        ctx.fillStyle = '#ff5a5f'; ctx.beginPath(); ctx.arc(bx, by, 3.2, 0, TAU); ctx.fill();
        ctx.fillStyle = '#ffffff'; ctx.fillRect(bx - 3.2, by - 0.5, 6.4, 1);
      }
    }
  };
  WP.drawBall = function (ctx, t) {
    var g = this.ballGame, I = this.iso;
    var A = g.a.kid, B = g.b.kid;
    if (!A || !B || A.path || B.path) return;
    var period = 1.25, e = ((this.t - g.t0) % period) / period, leg = Math.floor((this.t - g.t0) / period) % 2;
    var from = leg ? B : A, to = leg ? A : B;
    var x = lerp(from.x, to.x, e), y = lerp(from.y, to.y, e), z = 0.95 + Math.sin(e * Math.PI) * 1.1;
    ctx.fillStyle = 'rgba(20,30,60,0.16)'; ctx.beginPath(); ctx.ellipse(I.sx(x, y), I.sy(x, y, 0), 2.6, 1.3, 0, 0, TAU); ctx.fill();
    ctx.fillStyle = '#ffcf3a'; ctx.beginPath(); ctx.arc(I.sx(x, y), I.sy(x, y, z), 2.8, 0, TAU); ctx.fill();
    ctx.fillStyle = '#e8463b'; ctx.beginPath(); ctx.arc(I.sx(x, y), I.sy(x, y, z), 2.8, 0.3, 1.9); ctx.lineTo(I.sx(x, y), I.sy(x, y, z)); ctx.fill();
    from.pose = e < 0.15 ? 'cheer' : 'stand'; to.pose = e > 0.8 ? 'cheer' : 'stand';
    from.dir = Math.abs(to.x - from.x) > Math.abs(to.y - from.y) ? (to.x > from.x ? 0 : 2) : (to.y > from.y ? 1 : 3);
    to.dir = (from.dir + 2) % 4;
  };
  /* the light: a tint for the time of day, then lamps, windows and the
     campfire glowing through it */
  WP.drawLight = function (ctx, t, d) {
    var L = LIGHTS[this.light] || LIGHTS.dusk, P = LIGHTS[this.prevLight] || L, m = this.lightMix, I = this.iso, self = this;
    var tint = function (spec, alpha) {
      if (!spec || alpha <= 0) return;
      var g = ctx.createLinearGradient(0, d.by - d.H, 0, d.by + 160);
      g.addColorStop(0, spec[0]); g.addColorStop(1, spec[1]);
      ctx.save();
      ctx.globalCompositeOperation = 'source-atop';
      ctx.globalAlpha = alpha;
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, self.W, self.H);
      ctx.restore();
    };
    if (m < 1) tint(P.tint, 1 - m);
    tint(L.tint, m);
    var power = lerp(P.glow, L.glow, m);
    if (power <= 0.05) return;
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    var stage = this.stage;
    this.G.props.forEach(function (p) {
      if ((p.stage || 0) > stage) return;
      var def = PROPS[p.type];
      if (def.light) {
        var l = def.light(p), f = l.flicker ? 0.75 + 0.25 * Math.sin(t * 17 + p.seed * 9) * Math.sin(t * 7.3) : 1;
        var born = self.mode === 'build' ? self.propBorn(p) : 1;
        var r = l.r * (0.85 + 0.15 * f);
        ctx.globalAlpha = Math.min(1, power * f * born) * 0.85;
        ctx.drawImage(glow(l.c), I.sx(l.x, l.y) - r, I.sy(l.x, l.y, l.z) - r, r * 2, r * 2);
        if (p.type === 'lighthouse') self.drawBeam(ctx, I.sx(l.x, l.y), I.sy(l.x, l.y, l.z), t, power);
      }
      if (p.type === 'house') self.drawWindows(ctx, p, t, power);
    });
    this.G.crystals.forEach(function (c) {
      ctx.globalAlpha = (0.35 + 0.35 * Math.sin(t * 1.6 + c.p)) * Math.max(0.35, power);
      ctx.drawImage(glow(c.c), I.sx(c.x, c.y) - 12, I.sy(c.x, c.y, c.z) - 12, 24, 24);
    });
    if (this.flies) {
      this.flies.forEach(function (f) {
        var a = 0.45 + 0.55 * Math.sin(t * 3 + f.p);
        ctx.globalAlpha = a * power;
        ctx.drawImage(glow('#ffe58a'), I.sx(f.x, f.y) - 5, I.sy(f.x, f.y, f.z) - 5, 10, 10);
      });
    }
    ctx.restore();
  };
  WP.drawWindows = function (ctx, p, t, power) {
    var I = this.iso, wins = PROPS.house.windows(p), born = this.mode === 'build' ? this.propBorn(p) : 1;
    var lit = Math.min(1, power * (p.lights ? 1.3 : 1)) * born;
    ctx.save();
    ctx.globalCompositeOperation = 'source-over';
    for (var q = 0; q < wins.length; q++) {
      var w = wins[q], f = w.face === 'l' ? leftFace(I, w.x, w.y, w.z, w.w, w.w, w.h) : rightFace(I, w.x, w.y, w.z, w.w, w.w, w.h);
      var flick = 0.85 + 0.15 * Math.sin(t * 2.3 + q * 1.7 + p.seed * 5);
      ctx.globalAlpha = lit * flick * 0.92;
      onFace(ctx, f, function (c) { c.fillStyle = '#ffd98a'; c.fillRect(w.u, 0.2, 0.16, 0.24); c.fillStyle = '#fff1c4'; c.fillRect(w.u + 0.02, 0.22, 0.05, 0.08); });
      var cx = lerp(f[0], f[2], w.u + 0.08), cy = lerp(f[1], f[3], w.u + 0.08) + (f[5] - f[1]) * 0.32;
      ctx.globalCompositeOperation = 'lighter';
      ctx.globalAlpha = lit * flick * 0.5;
      ctx.drawImage(glow('#ffc46b'), cx - 16, cy - 16, 32, 32);
      ctx.globalCompositeOperation = 'source-over';
    }
    ctx.restore();
  };
  WP.drawBeam = function (ctx, x, y, t, power) {
    var a = t * 0.8, len = 150;
    var ex = Math.cos(a) * len, ey = Math.sin(a) * len * 0.42;
    var px = -Math.sin(a) * 18, py = Math.cos(a) * 18 * 0.42;
    var g = ctx.createLinearGradient(x, y, x + ex, y + ey);
    g.addColorStop(0, 'rgba(255,240,190,' + (0.32 * power).toFixed(3) + ')');
    g.addColorStop(1, 'rgba(255,240,190,0)');
    ctx.globalAlpha = 1;
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + ex + px, y + ey + py); ctx.lineTo(x + ex - px, y + ey - py); ctx.closePath(); ctx.fill();
  };
  WP.drawBubbles = function (ctx, t) {
    var self = this;
    ctx.save();
    ctx.font = '800 9px ' + this.font;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    this.kids.forEach(function (k) {
      var b = k.bubble;
      if (!b || !k.visible || k.sx === undefined) return;
      var age = self.t - b.t0, pop = backOut(age / 0.3), fade = Math.min(1, (b.dur - age) / 0.3);
      if (fade <= 0) return;
      var heart = b.text === '♥';
      var tw = heart ? 10 : ctx.measureText(b.text).width + 10, h = 13;
      var x = k.sx, y = k.sy - 6 - age * 2;
      ctx.globalAlpha = fade;
      ctx.save();
      ctx.translate(x, y); ctx.scale(pop, pop);
      ctx.fillStyle = 'rgba(255,255,255,0.96)';
      roundRect(ctx, -tw / 2, -h - 3, tw, h, 6); ctx.fill();
      ctx.beginPath(); ctx.moveTo(-3, -3.5); ctx.lineTo(0, 1); ctx.lineTo(3, -3.5); ctx.closePath(); ctx.fill();
      if (heart) { ctx.fillStyle = '#ff4d6d'; heartPath(ctx, 0, -9, 3.2); ctx.fill(); }
      else { ctx.fillStyle = '#1b2a35'; ctx.fillText(b.text, 0, -h / 2 - 2.5); }
      ctx.restore();
    });
    ctx.restore();
  };
  /* the glass in front: a faint hex lattice brighter toward the rim, a
     shimmer passing over it, ripples where things hit, the rim light and
     the running lights round the base */
  WP.drawFront = function (ctx, d, t) {
    var dayish = this.light === 'day';
    if (!this.glass || this.glassH !== d.H) this.buildGlass(d);
    ctx.save();
    ctx.globalAlpha = d.k;
    ctx.beginPath(); ctx.ellipse(d.cx, d.by, d.R, d.H, 0, Math.PI, TAU); ctx.closePath();
    ctx.clip();
    ctx.globalAlpha = (dayish ? 0.24 : 0.3) * d.k;
    ctx.drawImage(this.glass, this.glassX, this.glassY, this.glassW, this.glassHt);
    // a shimmer band sweeping across
    var sweep = ((t * 0.12) % 1.6) - 0.3, bx = d.cx - d.R + sweep * d.R * 2;
    ctx.beginPath(); ctx.moveTo(bx - 40, d.by - d.H - 20); ctx.lineTo(bx + 10, d.by - d.H - 20); ctx.lineTo(bx - 60, d.by + d.Rb + 20); ctx.lineTo(bx - 110, d.by + d.Rb + 20); ctx.closePath();
    ctx.save(); ctx.clip(); ctx.globalAlpha = (dayish ? 0.5 : 0.8) * d.k; ctx.drawImage(this.glass, this.glassX, this.glassY, this.glassW, this.glassHt); ctx.restore();
    // ripples
    for (var q = 0; q < this.hits.length; q++) {
      var h = this.hits[q], e = h.life / 1.1;
      ctx.save();
      ctx.beginPath(); ctx.arc(h.x, h.y, 10 + e * 70 * h.p, 0, TAU); ctx.clip();
      ctx.globalAlpha = (1 - e) * d.k;
      ctx.drawImage(this.glass, this.glassX, this.glassY, this.glassW, this.glassHt);
      ctx.restore();
      ctx.strokeStyle = dayish ? 'rgba(80,130,255,' + (0.8 * (1 - e)).toFixed(3) + ')' : 'rgba(210,230,255,' + (0.9 * (1 - e)).toFixed(3) + ')';
      ctx.lineWidth = 2.4 * (1 - e) + 0.6;
      ctx.beginPath(); ctx.arc(h.x, h.y, 6 + e * 46 * h.p, 0, TAU); ctx.stroke();
      ctx.beginPath(); ctx.arc(h.x, h.y, Math.max(0, e - 0.15) * 70 * h.p, 0, TAU); ctx.stroke();
    }
    // a reflection on the upper left
    var rg = ctx.createRadialGradient(d.cx - d.R * 0.45, d.by - d.H * 0.72, 2, d.cx - d.R * 0.45, d.by - d.H * 0.72, d.R * 0.55);
    rg.addColorStop(0, 'rgba(255,255,255,0.12)'); rg.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.globalAlpha = d.k;
    ctx.fillStyle = rg;
    ctx.fillRect(d.cx - d.R, d.by - d.H, d.R * 2, d.H + d.Rb);
    ctx.restore();
    // the rim
    ctx.save();
    ctx.globalAlpha = d.k;
    var rimA = 0.75 + 0.25 * Math.sin(t * 1.4);
    var widths = [7, 3.5, 1.6], alphas = [0.08, 0.2, 0.85];
    for (var w = 0; w < 3; w++) {
      ctx.strokeStyle = dayish ? 'rgba(80,130,255,' + (alphas[w] * rimA).toFixed(3) + ')' : 'rgba(205,225,255,' + (alphas[w] * rimA).toFixed(3) + ')';
      ctx.lineWidth = widths[w];
      ctx.beginPath(); ctx.ellipse(d.cx, d.by, d.R, d.H, 0, Math.PI, TAU); ctx.stroke();
    }
    ctx.strokeStyle = 'rgba(255,255,255,0.6)'; ctx.lineWidth = 4.5; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.ellipse(d.cx, d.by, d.R * 0.88, d.H * 0.88, 0, Math.PI * 1.13, Math.PI * 1.3); ctx.stroke();
    ctx.lineWidth = 2.5; ctx.strokeStyle = 'rgba(255,255,255,0.4)';
    ctx.beginPath(); ctx.ellipse(d.cx, d.by, d.R * 0.88, d.H * 0.88, 0, Math.PI * 1.34, Math.PI * 1.39); ctx.stroke();
    // the base ring and its running lights
    ctx.lineCap = 'butt';
    ctx.strokeStyle = dayish ? 'rgba(80,130,255,0.55)' : 'rgba(150,200,255,0.55)';
    ctx.lineWidth = 2.2;
    ctx.beginPath(); ctx.ellipse(d.cx, d.by, d.R, d.Rb, 0, 0, Math.PI); ctx.stroke();
    ctx.setLineDash([3, 12]);
    ctx.lineDashOffset = -t * 30;
    ctx.strokeStyle = dayish ? 'rgba(255,255,255,0.95)' : 'rgba(200,240,255,0.95)';
    ctx.lineWidth = 2.6;
    ctx.beginPath(); ctx.ellipse(d.cx, d.by, d.R, d.Rb, 0, 0, Math.PI); ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();
  };
  WP.buildGlass = function (d) {
    var k = this.scale * this.dpr, pad = 4;
    var x0 = d.cx - d.R - pad, y0 = d.by - d.H - pad, w = d.R * 2 + pad * 2, h = d.H + d.Rb + pad * 2;
    var c = document.createElement('canvas');
    c.width = Math.max(1, Math.ceil(w * k)); c.height = Math.max(1, Math.ceil(h * k));
    var g = c.getContext('2d');
    g.setTransform(k, 0, 0, k, -x0 * k, -y0 * k);
    var size = this.cfg.n >= 15 ? 13 : 9, hh = size * Math.sqrt(3) / 2;
    g.strokeStyle = this.light === 'day' ? 'rgba(70,120,255,0.9)' : 'rgba(220,235,255,0.9)';
    g.lineWidth = 0.7;
    g.beginPath();
    for (var row = 0; row * hh < h + hh; row++) {
      for (var col = 0; col * size * 1.5 < w + size * 2; col++) {
        var cx = x0 + col * size * 1.5, cy = y0 + row * hh * 2 + (col % 2 ? hh : 0);
        for (var s = 0; s < 6; s++) {
          var a0 = s / 6 * TAU, a1 = (s + 1) / 6 * TAU;
          g.moveTo(cx + Math.cos(a0) * size * 0.98, cy + Math.sin(a0) * size * 0.98);
          g.lineTo(cx + Math.cos(a1) * size * 0.98, cy + Math.sin(a1) * size * 0.98);
        }
      }
    }
    g.stroke();
    // fade toward the middle, like light catching the curve of the glass
    g.globalCompositeOperation = 'destination-in';
    var mask = g.createRadialGradient(d.cx, d.by - d.H * 0.4, d.R * 0.2, d.cx, d.by - d.H * 0.3, d.R * 1.02);
    mask.addColorStop(0, 'rgba(0,0,0,0.12)');
    mask.addColorStop(0.7, 'rgba(0,0,0,0.45)');
    mask.addColorStop(1, 'rgba(0,0,0,1)');
    g.fillStyle = mask;
    g.fillRect(x0, y0, w, h);
    this.glass = c; this.glassX = x0; this.glassY = y0; this.glassW = w; this.glassHt = h; this.glassH = d.H;
  };
  WP.drawBadge = function (ctx, d, t) {
    var x = d.cx, y = d.by - d.H, hit = Math.max(0, this.badgeHit), s = 1 + Math.sin(t * 1.8) * 0.04 + (hit > 0 ? Math.sin((0.7 - Math.min(0.7, hit)) / 0.7 * Math.PI) * 0.28 : 0);
    var r = (this.cfg.n >= 15 ? 17 : 13) * s;
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = 0.5 + hit * 0.6;
    ctx.drawImage(glow('#9cc2ff'), x - r * 3, y - r * 3, r * 6, r * 6);
    ctx.restore();
    var ring = (t % 2.4) / 2.4;
    ctx.strokeStyle = 'rgba(160,200,255,' + (0.6 * (1 - ring)).toFixed(3) + ')';
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.arc(x, y, r + ring * 16, 0, TAU); ctx.stroke();
    ctx.fillStyle = '#ffffff';
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
    ctx.fillStyle = '#2b67f6';
    shieldPath(ctx, x, y, r * 0.62);
    ctx.fill();
    ctx.strokeStyle = '#ffffff'; ctx.lineWidth = r * 0.13; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath(); ctx.moveTo(x - r * 0.24, y + r * 0.02); ctx.lineTo(x - r * 0.04, y + r * 0.22); ctx.lineTo(x + r * 0.28, y - r * 0.18); ctx.stroke();
  };
  WP.drawOutside = function (ctx, d, t) {
    var st = this.storm;
    if (st) {
      var fade = Math.min(1, st.t / 1.2, (st.dur - st.t) / 1.2);
      ctx.save();
      ctx.globalAlpha = fade;
      ctx.strokeStyle = 'rgba(195,215,255,0.7)';
      ctx.lineWidth = 1.1;
      ctx.beginPath();
      for (var q = 0; q < st.drops.length; q++) { var p = st.drops[q]; ctx.moveTo(p.x, p.y); ctx.lineTo(p.x - p.vx * 0.03, p.y - p.vy * 0.034); }
      ctx.stroke();
      ctx.strokeStyle = 'rgba(210,230,255,0.7)';
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      for (q = 0; q < st.slides.length; q++) {
        var s = st.slides[q], x1 = d.cx + Math.cos(s.th) * d.R, y1 = d.by - Math.sin(s.th) * d.H;
        var back = (s.th < Math.PI / 2 ? 1 : -1) * Math.min(0.12, s.v * 0.08);
        var x2 = d.cx + Math.cos(s.th + back) * d.R, y2 = d.by - Math.sin(s.th + back) * d.H;
        ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
      }
      ctx.stroke();
      // the cloud
      var cy = d.by - d.H - 58, cx = st.x, flash = st.boltT > 0 ? 1 : 0;
      ctx.fillStyle = flash ? '#c9d2ee' : '#3e4766';
      var puffs = [[-46, 6, 22], [-20, -6, 28], [12, -10, 30], [42, 2, 24], [0, 10, 26], [-34, 14, 18], [30, 14, 20]];
      puffs.forEach(function (pf) { ctx.beginPath(); ctx.arc(cx + pf[0], cy + pf[1], pf[2], 0, TAU); ctx.fill(); });
      ctx.fillStyle = flash ? '#e8edff' : '#59627f';
      puffs.slice(0, 4).forEach(function (pf) { ctx.beginPath(); ctx.arc(cx + pf[0] - 3, cy + pf[1] - 6, pf[2] * 0.6, 0, TAU); ctx.fill(); });
      if (st.boltT > 0) {
        ctx.strokeStyle = '#fff6c8'; ctx.lineWidth = 2.4; ctx.lineJoin = 'round';
        ctx.beginPath(); ctx.moveTo(cx, cy + 18);
        var by = cy + 18, steps = 5, ty = d.by - d.H;
        for (var b = 1; b <= steps; b++) ctx.lineTo(lerp(cx, d.cx, b / steps) + (b < steps ? (b % 2 ? 9 : -9) : 0), lerp(by, ty, b / steps));
        ctx.stroke();
      }
      ctx.restore();
    }
    if (this.flash > 0) {
      ctx.save(); ctx.globalAlpha = this.flash * 0.18; ctx.fillStyle = '#dfe6ff'; ctx.fillRect(0, 0, this.W, this.H); ctx.restore();
    }
    // sparks off the glass
    for (q = 0; q < this.sky.length; q++) {
      var sp = this.sky[q], a = 1 - sp.life / sp.max;
      ctx.fillStyle = sp.rain ? 'rgba(210,230,255,' + a.toFixed(3) + ')' : 'rgba(255,224,138,' + a.toFixed(3) + ')';
      ctx.fillRect(sp.x - 1, sp.y - 1, 2, 2);
    }
    // the messages that fly at the dome
    for (q = 0; q < this.threats.length; q++) {
      var th = this.threats[q], x, y, sc = 1, o = 1, rot = 0;
      if (th.t < 1) {
        var e = smooth(th.t);
        x = lerp(th.sx, th.px, e); y = lerp(th.sy, th.py, e); o = Math.min(1, th.t * 4); rot = Math.sin(th.t * 9) * 0.1;
      } else {
        var bb = Math.min(1, (th.t - 1) / 0.55);
        x = th.px + th.nx * 70 * bb; y = th.py + th.ny * 70 * bb + 30 * bb * bb; sc = 1 - 0.5 * bb; o = 1 - bb; rot = -0.5 * bb;
      }
      ctx.save();
      ctx.globalAlpha = o;
      ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc);
      ctx.fillStyle = '#ff5b4d';
      ctx.shadowColor = 'rgba(255,80,60,0.5)'; ctx.shadowBlur = 10;
      roundRect(ctx, -19, -15, 38, 30, 10); ctx.fill();
      ctx.shadowBlur = 0;
      ctx.beginPath(); ctx.moveTo(-8, 14); ctx.lineTo(-13, 23); ctx.lineTo(2, 14); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 1; roundRect(ctx, -19, -15, 38, 30, 10); ctx.stroke();
      if (th.img && th.img.complete && th.img.naturalWidth) ctx.drawImage(th.img, -9, -9, 18, 18);
      else { ctx.fillStyle = '#fff'; ctx.font = '900 14px ' + this.font; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('!', 0, 0); }
      ctx.restore();
    }
  };
  WP.drawMini = function (ctx, d, t) {
    var m = this.mini;
    if (!m) return;
    ctx.save();
    ctx.font = '800 11px ' + this.font;
    ctx.textBaseline = 'middle';
    for (var q = 0; q < m.bubbles.length; q++) {
      var b = m.bubbles[q], x, y, o = 1, sc = 1;
      if (b.good) {
        var e = smooth(Math.min(1, b.t / 1.55)), k = this.kids[0];
        var tx = k ? k.sx + 34 : d.cx + 40, ty = k ? k.sy - 6 : d.by - 40;
        x = lerp(b.sx, tx, e); y = lerp(b.sy, ty, e) - Math.sin(e * Math.PI) * 10;
        o = Math.min(1, b.t * 4, (2.6 - b.t) * 2);
      } else if (b.t < 1) {
        var e2 = smooth(b.t);
        x = lerp(b.sx, b.px, e2); y = lerp(b.sy, b.py, e2); o = Math.min(1, b.t * 4);
      } else {
        var bb = Math.min(1, (b.t - 1) / 0.55);
        x = b.px + b.nx * 50 * bb; y = b.py + b.ny * 40 * bb + 20 * bb * bb; sc = 1 - 0.4 * bb; o = 1 - bb;
      }
      var tw = ctx.measureText(b.text).width + 16;
      ctx.save();
      ctx.globalAlpha = Math.max(0, o);
      ctx.translate(x, y); ctx.scale(sc, sc);
      ctx.fillStyle = b.good ? '#18b06f' : '#ff6a5c';
      roundRect(ctx, -tw / 2, -11, tw, 22, 11); ctx.fill();
      ctx.beginPath(); ctx.moveTo(-6, 10); ctx.lineTo(-10, 17); ctx.lineTo(1, 10); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#ffffff'; ctx.textAlign = 'center';
      ctx.fillText(b.text, 0, 0.5);
      ctx.restore();
    }
    if (m.approve) {
      var age = m.t - m.approve, pop = backOut(age / 0.4), fade = Math.min(1, (10.4 - (m.t % 10.5)) / 0.4);
      var label = this.approveText;
      ctx.font = '800 11px ' + this.font;
      var w = ctx.measureText(label).width + 40, x0 = 14, y0 = this.H - 40;
      ctx.save();
      ctx.globalAlpha = Math.max(0, Math.min(1, fade));
      ctx.translate(x0 + w / 2, y0 + 14); ctx.scale(pop, pop); ctx.translate(-(x0 + w / 2), -(y0 + 14));
      ctx.fillStyle = 'rgba(255,255,255,0.96)';
      ctx.shadowColor = 'rgba(20,40,90,0.25)'; ctx.shadowBlur = 12; ctx.shadowOffsetY = 4;
      roundRect(ctx, x0, y0, w, 28, 14); ctx.fill();
      ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
      ctx.fillStyle = '#e3f7ec'; ctx.beginPath(); ctx.arc(x0 + 15, y0 + 14, 9, 0, TAU); ctx.fill();
      ctx.strokeStyle = '#18b06f'; ctx.lineWidth = 2; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(x0 + 11, y0 + 14); ctx.lineTo(x0 + 14, y0 + 17); ctx.lineTo(x0 + 19.5, y0 + 11); ctx.stroke();
      ctx.fillStyle = '#16233b'; ctx.textAlign = 'left';
      ctx.fillText(label, x0 + 29, y0 + 14.5);
      ctx.restore();
    }
    ctx.restore();
  };

  /* ======================================================= interaction */
  WP.toWorld = function (e) {
    var r = this.canvas.getBoundingClientRect();
    var bob = reduced ? 0 : Math.sin(this.t * 0.9) * 3.5;
    return { x: (e.clientX - r.left - this.offX) / this.scale, y: (e.clientY - r.top - this.offY) / this.scale - bob };
  };
  WP.kidAt = function (p) {
    var best = null, bestD = 1e9;
    for (var q = 0; q < this.kids.length; q++) {
      var k = this.kids[q];
      if (!k.visible || k.sx === undefined) continue;
      var dx = p.x - k.sx, dy = p.y - (k.sy + 12);
      if (Math.abs(dx) < 10 && dy > -16 && dy < 18) { var dd = dx * dx + dy * dy; if (dd < bestD) { bestD = dd; best = k; } }
    }
    return best;
  };
  WP.tileAt = function (p, z) {
    var I = this.iso;
    var A = (p.x - I.ox) / I.hw, B = (p.y - I.oy + z * I.bh) / I.hh;
    return { i: Math.floor((A + B) / 2), j: Math.floor((B - A) / 2), x: (A + B) / 2, y: (B - A) / 2 };
  };
  WP.insideDome = function (p) {
    var d = this.dome(), nx = (p.x - d.cx) / d.R, ny = (d.by - p.y) / d.H;
    if (p.y > d.by) return ((p.x - d.cx) * (p.x - d.cx)) / (d.R * d.R) + ((p.y - d.by) * (p.y - d.by)) / (d.Rb * d.Rb) <= 1;
    return nx * nx + ny * ny <= 1;
  };
  WP.onMove = function (e) {
    var p = this.toWorld(e);
    this.pointer = p;
    var k = this.kidAt(p), d = this.dome(), bdx = p.x - d.cx, bdy = p.y - (d.by - d.H);
    var hot = !!k || (bdx * bdx + bdy * bdy < 400) || this.insideDome(p);
    if (k && k.wave <= 0) { k.wave = 1.3; if (!k.ride && !k.act && !k.path) k.dir = p.x < k.sx ? 1 : 0; }
    this.canvas.style.cursor = hot && this.mode !== 'mini' ? 'pointer' : '';
  };
  WP.onTap = function (e) {
    if (this.mode === 'mini') return;
    var p = this.toWorld(e), d = this.dome(), self = this, I = this.iso, G = this.G;
    // the shield: everybody waves
    var bdx = p.x - d.cx, bdy = p.y - (d.by - d.H);
    if (this.domeK > 0.5 && bdx * bdx + bdy * bdy < 420) {
      this.badgeHit = 0.8;
      this.domeRipple(d.cx, d.by - d.H, 1.4);
      this.kids.forEach(function (k) { if (k.visible) { k.wave = 2; k.happy = 1.5; } });
      return;
    }
    var k = this.kidAt(p);
    if (k) {
      k.vz = 3.1; k.happy = 1.4;
      this.hearts(k.sx, k.sy, 3);
      this.say(k, pick(Math.random, ['hi!', 'hehe', 'yay!', '♥', 'wheee!']));
      return;
    }
    // props by their footprint on the ground
    var hit = null;
    for (var z = 2.6; z >= 0 && !hit; z -= 0.4) {
      var tt = this.tileAt(p, z);
      if (tt.i < 0 || tt.j < 0 || tt.i >= G.n || tt.j >= G.n) continue;
      var o = G.occ[tt.i][tt.j];
      if (o && o !== 'spot' && ['house', 'windmill', 'fire', 'boombox', 'lighthouse', 'flag'].indexOf(o.type) >= 0 && (o.stage || 0) <= this.stage) hit = o;
    }
    if (hit) {
      if (hit.type === 'house') {
        hit.lights = hit.lights ? 0 : 1;
        this.sparkle(hit.i + 1, hit.j + 1, 1.6, 10);
        var visitor = this.kids.filter(function (kk) { return kk.act === ACTS.home && kk.spot && kk.spot.house === hit; })[0];
        if (visitor) visitor.actT = visitor.actDur;
      } else if (hit.type === 'windmill') hit.boost = 1.5;
      else if (hit.type === 'fire') { hit.boost = 1.2; for (var s = 0; s < 14; s++) this.spark(hit.i + 0.5, hit.j + 0.5, 0.4); }
      else if (hit.type === 'boombox') { hit.playing = (hit.playing || 0) + 1; setTimeout(function () { hit.playing = Math.max(0, hit.playing - 1); }, 5000); for (var n = 0; n < 6; n++) this.note(hit.i + 0.5, hit.j + 0.5, 0.6); }
      else this.sparkle(hit.i + 0.5, hit.j + 0.5, 2.2, 10);
      return;
    }
    var w = this.tileAt(p, -0.2);
    if (this.waterAt(w.x, w.y)) {
      this.splash(w.x, w.y, true);
      if (Math.random() < 0.6) this.fishJump(w.x + 0.2, w.y, null);
      this.critters.forEach(function (c) { if (c.lead) c.rush = 2; });
      return;
    }
    var g = this.tileAt(p, 0);
    if (this.land(g.i, g.j) && G.top[g.i][g.j] === 0) {
      // plant a flower
      var S = this.S, col = S.flowers.length ? pick(Math.random, S.flowers) : '#ff5a5f';
      G.flowers.push({ x: g.x, y: g.y, c: col, h: 0.18 + Math.random() * 0.12, p: Math.random() * TAU, stage: 0, s: 0 });
      var fl = G.flowers[G.flowers.length - 1];
      var grow = function () { fl.s = Math.min(1, fl.s + 0.08); if (fl.s < 1) requestAnimationFrame(grow); };
      grow();
      if (G.flowers.length > 220) G.flowers.splice(0, 1);
      this.sparkle(g.x, g.y, 0.2, 5);
      return;
    }
    if (this.insideDome(p) && this.domeK > 0.5) {
      // a firework, launched by whoever is nearest
      var near = null, nd = 1e9;
      this.kids.forEach(function (kk) { if (kk.visible && kk.sx !== undefined) { var dd = Math.abs(kk.sx - p.x); if (dd < nd) { nd = dd; near = kk; } } });
      var from = near ? { x: near.sx, y: near.sy } : { x: d.cx, y: d.by };
      this.firework(from.x, from.y, p.x, p.y);
      if (near) { near.happy = 1.5; near.wave = 1; }
    }
  };

  /* ====================================================== build mode API */
  WP.setStage = function (n) {
    n = Math.max(0, Math.min(7, n | 0));
    if (n === this.stage) return;
    var up = n > this.stage;
    for (var s = this.stage + 1; s <= n; s++) this.stageAt[s] = this.t;
    this.stage = n;
    if (up && n === 7) this.celebrate();
    if (reduced) { this.domeK = n >= 5 ? 1 : 0; this.draw(); }
    this.kick();
  };
  WP.setName = function (name) { this.name = String(name || ''); if (reduced) this.draw(); };
  WP.setLook = function (look) {
    var k = this.child;
    if (!k || !look) return;
    if (look.shirt) k.shirt = look.shirt;
    if (look.pants) k.pants = look.pants;
    if (reduced) this.draw();
  };
  WP.setLight = function (name) {
    if (!LIGHTS[name] || name === this.light) return;
    this.prevLight = this.light;
    this.light = name;
    this.lightMix = reduced ? 1 : 0;
    this.glass = null;
    if (reduced) this.draw();
  };
  WP.celebrate = function () {
    var d = this.dome(), self = this;
    if (reduced) return;
    for (var q = 0; q < 6; q++) (function (q) { setTimeout(function () { var tg = self.domeTarget(); self.firework(d.cx + (Math.random() - 0.5) * 40, d.by - 10, tg.x, tg.y); }, q * 380); })(q);
    var k = this.child;
    if (k) { k.happy = 3; k.vz = 3; this.say(k, 'yay!'); this.hearts(k.sx || d.cx, k.sy || d.by - 40, 5); }
    // two friends arrive to say hello
    if (!this.friendsCame && this.buildSpots) {
      this.friendsCame = true;
      var r = mulberry(this.seed + 7);
      for (var f = 0; f < 2; f++) {
        var spot = this.buildSpots[(f + 1) % this.buildSpots.length];
        if (!spot) continue;
        var fk = this.makeKid(r, { x: spot.i + 0.5, y: spot.j + 0.5, pop: 0, popT: this.t + 0.5 + f * 0.4, isFriend: true });
        fk.visible = true;
        this.kids.push(fk);
      }
    }
  };
  WP.destroy = function () {
    this.dead = true;
    if (this.raf) cancelAnimationFrame(this.raf);
    if (this.ro) this.ro.disconnect();
    if (this.io) this.io.disconnect();
    if (this.canvas && this.canvas.parentNode) this.canvas.parentNode.removeChild(this.canvas);
    this.host.classList.remove('haven-live');
    this.host.haven = null;
  };

  // friends who arrive in build mode pop in and then wander like the child
  var baseUpdate = WP.updateBuildKid;
  WP.updateBuildKid = function (k, dt) {
    if (k.isFriend) {
      k.pop = this.t < k.popT ? 0 : backOut((this.t - k.popT) / 0.6);
      if (k.pop > 0 && !k.greeted) { k.greeted = true; this.say(k, pick(Math.random, ['hi!', 'welcome!', 'play?'])); k.wave = 2; }
      k.moving = false;
      k.pose = k.wave > 0 ? 'stand' : 'stand';
      if (Math.random() < dt * 0.3) k.dir = Math.random() < 0.5 ? 0 : 1;
      return;
    }
    baseUpdate.call(this, k, dt);
  };

  /* ============================================================ mounting */
  function mount(el) {
    if (!el || el.haven) return el && el.haven;
    var mode = el.getAttribute('data-haven') || 'hero';
    try {
      return new World(el, mode);
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
  mountAll();
})(window);
