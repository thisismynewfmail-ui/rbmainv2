/* Calamity Coast -- the Game View half of disaster survival
   (app/game/worlds/calamity_coast.py).

   The server runs the disasters; this draws them.  Rising water and lava
   (and the world seen through them when you are under), warning circles
   with whatever is about to come out of the sky on top of them -- meteors,
   lightning, lava bombs, hail, coconuts, debris, boulders -- a tornado's
   funnel walking the high street, avalanches and rockslides sweeping their
   lanes, houses burning, sinkholes cracking open, the ground shaking, gusts
   of wind, and the weather to go with it all: rain, snow, hail and a sky
   that turns as the disaster comes in.  Frost creeps in at the edges of the
   screen as you get cold.

   Stranded townsfolk wave for help until somebody carries them off over
   their shoulders; supply crates parachute in during the calm, with a beam
   of light to find them by; the evacuation points glow.

   Four arrival scenes, one per town, are registered at the bottom. */
(function (global) {
  'use strict';
  var Arena = global.Arena || { register: function () {} };

  var TEAM = { red: '#e8502a', blue: '#2a8ad8' };
  var TEAM_LIGHT = { red: '#ffab8a', blue: '#9ecbff' };
  var PICKUP_REACH = 5.5;
  var POWERS = {
    ring: ['LIFE RING', '#ff6a3a', 'floats you in water'],
    hat: ['HARD HAT', '#f2c230', 'stops one hit from above'],
    coat: ['RAINCOAT', '#f2e040', 'keeps out the cold and the hail'],
    shoes: ['RUNNING SHOES', '#3ad0ff', 'quick feet for a while']
  };
  // the sky and the light each disaster brings in with it
  var MOODS = {
    tsunami: { top: '#4a5a6a', horizon: '#a8b4bc', clouds: 0.85, tint: '#d8e0e8', ambient: '#8a96a4' },
    flood: { top: '#4a5462', horizon: '#9aa4ac', clouds: 0.95, tint: '#d0d8e0', ambient: '#86909c' },
    lightning: { top: '#1a1f2a', horizon: '#525a68', clouds: 1.0, tint: '#a8b0c8', ambient: '#646c7a' },
    hurricane: { top: '#262c34', horizon: '#64707c', clouds: 1.0, tint: '#b0b8c0', ambient: '#707884' },
    tornado: { top: '#343c2e', horizon: '#8a9478', clouds: 0.95, tint: '#c8d0b0', ambient: '#767e6c' },
    meteors: { top: '#24163a', horizon: '#c8604a', clouds: 0.35, tint: '#ffb090', ambient: '#86707a' },
    blizzard: { top: '#9aa4b0', horizon: '#e8ecf0', clouds: 1.0, tint: '#e8f0ff', ambient: '#b8c0cc' },
    avalanche: { top: '#7a8a9a', horizon: '#e0e8f0', clouds: 0.8, tint: '#eef4ff', ambient: '#aab4c0' },
    eruption: { top: '#3a1a14', horizon: '#d0602a', clouds: 0.9, tint: '#ffa070', ambient: '#9a6a58' },
    fire: { top: '#4a2a1a', horizon: '#d8803a', clouds: 0.7, tint: '#ffb880', ambient: '#9a7a64' },
    hail: { top: '#363e4c', horizon: '#86909c', clouds: 1.0, tint: '#c0c8d8', ambient: '#7a828e' },
    quake: { top: '#6a7080', horizon: '#d8c8a8', clouds: 0.6, tint: '#f0e0c8', ambient: '#a49c90' },
    rockslide: { top: '#6a6a70', horizon: '#d0c0a0', clouds: 0.7, tint: '#f0e0c8', ambient: '#a09888' },
    sinkholes: { top: '#5a7a9a', horizon: '#d8d0b0', clouds: 0.6, tint: '#f8e8c8', ambient: '#a8a498' }
  };
  // the townsfolk: skin, shirt, trousers, hair (or hat), hat?
  var LOOKS = [
    ['#f2c8a0', '#3aa04a', '#5a4a3a', '#4a2a1a', 0],
    ['#c88a5a', '#f2c230', '#2a3a5a', '#f2c230', 1],
    ['#8a5a3a', '#d84a8a', '#3a3a3a', '#1a1a1a', 0],
    ['#f2d0b0', '#f2f0ea', '#4a6a9a', '#c8c8c8', 0],
    ['#e0b090', '#2a6ad0', '#8a6a3a', '#d8402a', 1],
    ['#a86a4a', '#f08a2a', '#2a2a2a', '#6a3a1a', 0]
  ];

  function rgb(hex) {
    var n = parseInt(String(hex).slice(1), 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
  }
  function hex(c) {
    function h(v) { return ('0' + Math.round(Math.max(0, Math.min(1, v)) * 255).toString(16)).slice(-2); }
    return '#' + h(c[0]) + h(c[1]) + h(c[2]);
  }
  function mixHex(a, b, k) {
    var x = rgb(a), y = rgb(b);
    return hex([x[0] + (y[0] - x[0]) * k, x[1] + (y[1] - x[1]) * k, x[2] + (y[2] - x[2]) * k]);
  }
  function esc(text) {
    return String(text == null ? '' : text).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function now() { return performance.now() / 1000; }
  function hash(n) { var x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }

  /* A polyline on the ground, walked by distance (the server's Path). */
  function Path(points) {
    this.pts = points;
    this.cum = [0];
    for (var i = 1; i < points.length; i++) {
      this.cum.push(this.cum[i - 1] + Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]));
    }
    this.length = this.cum[this.cum.length - 1] || 1;
  }
  Path.prototype.at = function (d) {
    d = Math.max(0, Math.min(this.length, d));
    for (var i = 0; i < this.pts.length - 1; i++) {
      if (d <= this.cum[i + 1] || i === this.pts.length - 2) {
        var a = this.pts[i], b = this.pts[i + 1], seg = (this.cum[i + 1] - this.cum[i]) || 1;
        var f = (d - this.cum[i]) / seg;
        return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, (b[0] - a[0]) / seg, (b[1] - a[1]) / seg];
      }
    }
    return [this.pts[0][0], this.pts[0][1], 1, 0];
  };

  // ============================================================ plugin
  Arena.register('calamity_coast', function (arena) {
    var client = arena.client;
    var centre = [0, 0, 0], areaRect = [-150, 150, -150, 150], specs = [], marks = {};
    var cc = { stage: 'setup', n: 0, of: 3, id: '', name: '', line: '', big: false, left: 0,
               points: { red: 0, blue: 0 }, alive: { red: 0, blue: 0 }, stranded: 0 };
    var stageAt = now();
    var ax = {};                         // the last snapshot's extra
    var warns = {};                      // strike id -> {p, r, what, at, total}
    var scorches = [], bolts = [], chunks = [], puffs = [];
    var cracks = {};                     // sinkhole index -> {p, r, at, total}
    var crates = {}, seenCrate = {};     // id -> [x, y, z]; id -> first seen
    var burnt = {}, wasBurning = {};
    var shake = { until: 0, power: 0 };
    var gust = { until: 0, dir: [1, 0] };
    var siren = 0, roarAt = 0, rumbleAt = 0, fireAt = 0, rainAt = 0;
    var drops = [], streaks = [], roofs = { at: -9, cells: {}, eye: [0, 0, 0] };
    var groundCache = {}, groundCount = 0;
    var baseSky = null, baseAmbient = '#a8b4c4', skyNow = null, skyAt = 0;
    var veil = null;

    function spec() {
      for (var i = 0; i < specs.length; i++) if (specs[i].id === cc.id) return specs[i];
      return null;
    }
    function parts(kind) {
      var s = spec();
      return ((s && s.parts) || []).filter(function (p) { return p.kind === kind; });
    }
    function stageLeft() { return Math.max(0, (cc.left || 0) - (now() - stageAt)); }
    function active() { return arena.phase === 'active' && cc.stage === 'active'; }
    function inPlay() { return !!client.myTeam && !arena.me.out && client.local.alive; }
    function myPos() { return client.local.pos; }
    function eyePos() {
      var cam = client.cameraPosition ? client.cameraPosition() : null;
      return cam ? cam.eye : [myPos()[0], myPos()[1] + 5, myPos()[2]];
    }
    function audible(p) {
      var me = myPos();
      var d = p ? Math.hypot(p[0] - me[0], p[1] - me[1], p[2] - me[2]) : 0;
      return Math.max(0.1, Math.min(1, 1.15 - d / 160));
    }
    function play(name, p, vol) { client.audio.play(name, { volume: (vol || 1) * audible(p) }); }
    function local(p) { return [p[0] + centre[0], p[1], p[2] + centre[2]]; }
    function rectOf(r) {
      if (!r) return areaRect;
      return [r[0] + centre[0], r[1] + centre[0], r[2] + centre[2], r[3] + centre[2]];
    }

    /* the height of whatever is under (x, z), looking down from ``top`` */
    function groundAt(x, z, top) {
      var key = Math.round(x / 2) + ',' + Math.round(z / 2);
      var hit = groundCache[key];
      if (hit !== undefined) return hit;
      var phys = client.physics;
      top = top === undefined ? 140 : top;
      var y = 0;
      if (phys) y = top - phys.rayDistance([x, top, z], [0, -1, 0], top + 40);
      if (++groundCount > 4000) { groundCache = {}; groundCount = 0; }
      groundCache[key] = y;
      return y;
    }

    // ---------------------------------------------------------- the map
    function loadMap(map) {
      var mk = (map && map.markers) || {};
      centre = mk.centre || [0, 0, 0];
      areaRect = mk.area_rect || [centre[0] - 150, centre[0] + 150, centre[2] - 150, centre[2] + 150];
      specs = ((mk.extra || {}).disasters) || [];
      marks = mk.points || {};
      baseSky = map && map.sky ? map.sky : null;
      baseAmbient = (map && map.ambient) || '#a8b4c4';
      skyNow = null;
      reset();
      groundCache = {}; groundCount = 0;
      roofs = { at: -9, cells: {}, eye: [0, 0, 0] };
    }

    function reset() {
      warns = {}; scorches = []; bolts = []; chunks = []; puffs = []; cracks = {};
      crates = {}; seenCrate = {}; burnt = {}; wasBurning = {}; ax = {};
      shake = { until: 0, power: 0 }; gust = { until: 0, dir: [1, 0] }; siren = 0;
    }

    function applyState(s) {
      if (!s) return;
      var was = cc.stage;
      cc = s;
      stageAt = now();
      if (cc.stage === 'calm' && was === 'active') { burnt = {}; wasBurning = {}; cracks = {}; }
      roleChip();
    }

    // -------------------------------------------------------- the veil
    function makeVeil() {
      if (veil) return veil;
      var host = document.querySelector('#game-root .hud') || document.body;
      veil = document.createElement('div');
      veil.id = 'cc-veil';
      veil.style.cssText = 'position:absolute;left:0;top:0;right:0;bottom:0;pointer-events:none;' +
        'opacity:0;transition:opacity .25s;z-index:1';
      host.insertBefore(veil, host.firstChild);
      return veil;
    }

    function updateVeil() {
      var v = makeVeil();
      var eye = eyePos();
      var under = submerged(eye);
      var cold = arena.me.cold || 0;
      if (under) {
        v.style.background = under === 'lava'
          ? 'radial-gradient(ellipse at 50% 50%, rgba(255,140,40,0.55), rgba(140,30,0,0.92))'
          : 'linear-gradient(180deg, rgba(40,110,170,0.55), rgba(10,40,80,0.85))';
        v.style.opacity = '1';
      } else if (cold > 0.05 && !arena.me.out) {
        var a = Math.min(0.85, cold * 0.85);
        v.style.background = 'radial-gradient(ellipse at 50% 50%, rgba(255,255,255,0) ' +
          Math.round(70 - cold * 30) + '%, rgba(200,230,255,' + a.toFixed(2) + ') 100%)';
        v.style.opacity = '1';
      } else {
        v.style.opacity = '0';
      }
    }

    function submerged(p) {
      var lv = ax.lv || [];
      for (var i = 0; i < lv.length; i++) {
        var r = rectOf(lv[i][2]);
        if (p[1] < lv[i][0] && p[0] >= r[0] && p[0] <= r[1] && p[2] >= r[2] && p[2] <= r[3]) return lv[i][1];
      }
      return '';
    }

    // ------------------------------------------------------- the sky
    function moodSky(dt) {
      var r = client.renderer;
      if (!r || !r.setSky || !baseSky) return;
      var target = baseSky, amb = baseAmbient;
      var mood = MOODS[cc.id];
      var coming = cc.stage === 'active' || (cc.stage === 'calm' && siren > 0);
      if (mood && coming && arena.phase === 'active') {
        target = { top: mood.top, horizon: mood.horizon, sun: baseSky.sun, clouds: mood.clouds, tint: mood.tint };
        amb = mood.ambient;
      }
      if (!skyNow) skyNow = { top: baseSky.top, horizon: baseSky.horizon, clouds: baseSky.clouds || 0.5,
                              tint: baseSky.tint || '#ffffff', ambient: baseAmbient };
      var k = Math.min(1, dt * 0.7);
      var next = {
        top: mixHex(skyNow.top, target.top, k), horizon: mixHex(skyNow.horizon, target.horizon, k),
        clouds: skyNow.clouds + ((target.clouds === undefined ? 0.5 : target.clouds) - skyNow.clouds) * k,
        tint: mixHex(skyNow.tint, target.tint || '#ffffff', k), ambient: mixHex(skyNow.ambient, amb, k)
      };
      var moved = next.top !== skyNow.top || next.horizon !== skyNow.horizon || next.ambient !== skyNow.ambient ||
        Math.abs(next.clouds - skyNow.clouds) > 0.004;
      skyNow = next;
      if (moved && now() - skyAt > 0.1) {
        skyAt = now();
        r.setSky({ top: next.top, horizon: next.horizon, sun: baseSky.sun, clouds: next.clouds, tint: next.tint });
        if (r.setAmbient) r.setAmbient(next.ambient);
      }
    }

    // ------------------------------------------------------- drawing
    function raw(renderer, kind, x, y, z, sx, sy, sz, colour, o) {
      o = o || {};
      renderer.pushRaw(kind, x, y, z, o.rx || 0, o.yaw || 0, o.rz || 0, sx, sy, sz,
                       typeof colour === 'string' ? rgb(colour) : colour,
                       o.a === undefined ? 1 : o.a, 0, o.m || 0, 0, null);
    }

    /* A stranded townsperson: standing and waving, or over a carrier's shoulders. */
    function townsfolk(renderer, x, y, z, yaw, look, carried, time, id) {
      var L = LOOKS[look % LOOKS.length];
      var skin = L[0], shirt = L[1], legs = L[2], hair = L[3];
      var cs = Math.cos(yaw), sn = Math.sin(yaw);
      function put(kind, lx, ly, lz, sx, sy, sz, colour, rx, rz, extra) {
        var px = x + lx * cs + lz * sn, pz = z - lx * sn + lz * cs;
        renderer.pushRaw(kind, px, y + ly, pz, rx || 0, yaw, rz || 0, sx, sy, sz, rgb(colour), 1, 0, extra || 0, 0, null);
      }
      if (carried) {
        // lying on their side across the back of the carrier's shoulders,
        // head to the carrier's right, arms dangling
        var sway = Math.sin(time * 6 + id) * 0.06;
        put('rbox', 0.2, 4.6 + sway, -1.15, 2.0, 1.5, 1.0, shirt);
        put('rbox', -1.9, 4.25 + sway, -1.15, 2.0, 0.7, 0.8, legs);
        put('rbox', -1.9, 4.95 + sway, -1.15, 2.0, 0.7, 0.8, legs);
        put('rbox', 1.8, 4.65 + sway, -1.15, 1.15, 1.15, 1.15, skin);
        put('rbox', 2.45, 4.7 + sway, -1.15, 0.3, 1.2, 1.2, hair);
        var flail = Math.sin(time * 7 + id) * 0.25;
        put('rbox', 0.9, 3.4 + sway, -0.95, 0.55, 1.5, 0.55, skin, flail, 0);
        put('rbox', 0.5, 3.45 + sway, -1.4, 0.55, 1.5, 0.55, skin, -flail, 0);
        return;
      }
      var bob = Math.abs(Math.sin(time * 5 + id)) * 0.25;
      var wave = Math.sin(time * 9 + id) * 0.6;
      put('rbox', -0.42, 1.0, 0, 0.78, 2.0, 0.85, legs);
      put('rbox', 0.42, 1.0, 0, 0.78, 2.0, 0.85, legs);
      put('rbox', 0, 3.0 + bob * 0.3, 0, 1.75, 2.0, 0.95, shirt);
      // both arms up, waving
      put('rbox', -1.15, 4.5 + bob * 0.3, 0, 0.6, 1.9, 0.6, skin, 0, -0.35 + wave * 0.5);
      put('rbox', 1.15, 4.5 + bob * 0.3, 0, 0.6, 1.9, 0.6, skin, 0, 0.35 + wave * 0.5);
      put('rbox', 0, 4.65 + bob * 0.3, 0, 1.15, 1.15, 1.15, skin);
      if (L[4]) {
        put('cyl', 0, 5.35 + bob * 0.3, 0, 1.35, 0.35, 1.35, hair);
        put('cyl', 0, 5.5 + bob * 0.3, 0.25, 1.0, 0.1, 1.5, hair);
      } else {
        put('rbox', 0, 5.3 + bob * 0.3, -0.1, 1.2, 0.35, 1.2, hair);
      }
      put('sph', -0.24, 4.75 + bob * 0.3, 0.56, 0.16, 0.2, 0.06, '#1a1a1a');
      put('sph', 0.24, 4.75 + bob * 0.3, 0.56, 0.16, 0.2, 0.06, '#1a1a1a');
      put('cyl', 0, 4.35 + bob * 0.3, 0.57, 0.3, 0.3, 0.06, '#5a1a1a', Math.PI / 2, 0);
    }

    function drawStranded(renderer, time) {
      var list = ax.st || [];
      var me = myPos();
      list.forEach(function (s) {
        var id = s[0], state = s[4], by = s[5], look = s[6];
        if (state === 'carried') {
          var carrier = by === client.myId ? null : client.players[by];
          if (by === client.myId) {
            if (!client.thirdPerson) return;    // over your own shoulders: out of view
            townsfolk(renderer, me[0], me[1], me[2], client.local.yaw, look, true, time, id);
          } else if (carrier && carrier.alive) {
            townsfolk(renderer, carrier.pos[0], carrier.pos[1], carrier.pos[2], carrier.yaw || 0, look,
                      true, time, id);
          }
          return;
        }
        var yaw = Math.atan2(me[0] - s[1], me[2] - s[3]);
        townsfolk(renderer, s[1], s[2], s[3], yaw, look, false, time, id);
        var d = Math.hypot(me[0] - s[1], me[2] - s[3]);
        if (renderer.queueTag) {
          renderer.queueTag('cc_st' + id, 'HELP!', '#ff6a4a', d > 30 ? Math.round(d) + ' studs' : 'hold E',
                            [s[1], s[2] + 7.4 + Math.sin(time * 4 + id) * 0.2, s[3]], d > 60 ? 1.4 : 1);
        }
        // a flare of red over their heads, to find them by
        raw(renderer, 'cyl', s[1], s[2] + 18, s[3], 0.5, 24, 0.5, '#ff5a3a', { a: 0.22 + Math.sin(time * 5 + id) * 0.08, m: 2 });
      });
    }

    function drawCrates(renderer, time) {
      var list = ax.cr || [];
      var t = now();
      var live = {};
      list.forEach(function (c) {
        var id = c[0];
        live[id] = 1;
        crates[id] = [c[1], c[2], c[3]];
        if (!seenCrate[id]) seenCrate[id] = t;
        var fall = Math.max(0, 1 - (t - seenCrate[id]) / 2.6);
        var y = c[2] + fall * fall * 70;
        var spin = time * 0.6 + id;
        raw(renderer, 'box', c[1], y + 1.1, c[3], 2.2, 2.2, 2.2, '#a87a3a', { yaw: spin });
        raw(renderer, 'box', c[1], y + 1.1, c[3], 2.3, 0.35, 2.3, '#5a3a1a', { yaw: spin });
        raw(renderer, 'box', c[1], y + 1.1, c[3], 0.35, 2.3, 2.3, '#5a3a1a', { yaw: spin });
        raw(renderer, 'box', c[1], y + 2.24, c[3], 1.2, 0.1, 0.4, '#e8e8e8', { yaw: spin });
        raw(renderer, 'box', c[1], y + 2.24, c[3], 0.4, 0.1, 1.2, '#e8e8e8', { yaw: spin });
        if (fall > 0) {
          // the parachute and its lines
          raw(renderer, 'sph', c[1], y + 7.5, c[3], 7, 2.4, 7, '#e8502a', { yaw: spin });
          raw(renderer, 'box', c[1], y + 4.6, c[3], 0.08, 4.6, 0.08, '#f2f0ea');
        } else {
          raw(renderer, 'cyl', c[1], c[2] + 20, c[3], 1.2, 38, 1.2, '#ffe27a',
              { a: 0.16 + Math.sin(time * 3 + id) * 0.05, m: 2 });
        }
      });
      Object.keys(crates).forEach(function (id) { if (!live[id]) delete crates[id]; });
    }

    function drawEvac(renderer, time) {
      var list = marks.evac || [];
      var carrying = !!arena.me.carry;
      list.forEach(function (m, i) {
        var p = m.p;
        var pulse = 0.5 + Math.sin(time * 3) * 0.5;
        raw(renderer, 'cyl', p[0], p[1] + 30, p[2], 2.2, 60, 2.2, '#5aff8a',
            { a: (carrying ? 0.28 : 0.12) + pulse * 0.06, m: 2 });
        if (renderer.queueTag && (carrying || (ax.st || []).some(function (s) { return s[4] === 'carried'; }))) {
          renderer.queueTag('cc_evac' + i, 'EVAC', '#5aff8a', carrying ? 'bring them here' : '',
                            [p[0], p[1] + 12 + pulse * 0.4, p[2]], 1.6);
        }
      });
    }

    function drawLevels(renderer, time) {
      var lv = ax.lv || [];
      var levels = parts('level');
      lv.forEach(function (l, i) {
        var y = l[0], medium = l[1], r = rectOf(l[2]);
        var part = levels[i] || {};
        var from = part.from === undefined ? y - 10 : part.from;
        if (y < from + 0.12) return;           // still at the sea's own surface
        var cx = (r[0] + r[1]) / 2, cz = (r[2] + r[3]) / 2, w = r[1] - r[0], d = r[3] - r[2];
        var base = Math.min(from, y - 0.4);
        if (medium === 'lava') {
          raw(renderer, 'box', cx, (base + y) / 2, cz, w, Math.max(0.2, y - base), d, '#ff5a14', { m: 2, a: 0.97 });
          // a crust drifting on it
          for (var k = 0; k < 14; k++) {
            var hx = r[0] + hash(k) * w, hz = r[2] + ((hash(k + 40) * d + time * 1.5 * (0.5 + hash(k + 9))) % d);
            raw(renderer, 'box', hx, y + 0.06, hz, 4 + hash(k + 3) * 6, 0.12, 3 + hash(k + 5) * 5, '#4a1a0a',
                { yaw: hash(k + 7) * 3, a: 0.85 });
          }
        } else {
          raw(renderer, 'box', cx, y - 0.15, cz, w, 0.3, d, '#2f78b8', { a: 0.66 });
          if (y - base > 0.8) raw(renderer, 'box', cx, (base + y - 0.3) / 2, cz, w - 0.2, y - 0.3 - base, d - 0.2,
                                  '#1a4a7a', { a: 0.32 });
          // foam drifting along the flow
          var flow = part.flow || [0, 0];
          for (var f = 0; f < 22; f++) {
            var fx = r[0] + ((hash(f) * w + flow[0] * time * 6) % w + w) % w;
            var fz = r[2] + ((hash(f + 30) * d + flow[1] * time * 6) % d + d) % d;
            raw(renderer, 'box', fx, y + 0.05, fz, 3 + hash(f + 2) * 5, 0.1, 2 + hash(f + 4) * 3, '#e8f4ff',
                { yaw: hash(f + 6) * 3, a: 0.55 + Math.sin(time * 2 + f) * 0.15 });
          }
        }
      });
    }

    function drawWarnings(renderer, time) {
      var t = now();
      Object.keys(warns).forEach(function (id) {
        var w = warns[id];
        var left = w.at - t;
        if (left < -0.3) { delete warns[id]; return; }
        var k = Math.max(0, Math.min(1, 1 - left / w.total));
        var p = w.p;
        var blink = 0.35 + 0.25 * Math.abs(Math.sin(time * (6 + k * 14)));
        raw(renderer, 'cyl', p[0], p[1] + 0.09, p[2], w.r * 2, 0.06, w.r * 2, '#ff3a2a', { a: blink, m: 2 });
        raw(renderer, 'cyl', p[0], p[1] + 0.12, p[2], w.r * 2 * k, 0.06, w.r * 2 * k, '#ffd23a', { a: 0.45, m: 2 });
        // what is coming down onto it
        if (w.what === 'lightning') {
          if (left < 0.5) raw(renderer, 'cyl', p[0], p[1] + 40, p[2], 0.3, 80, 0.3, '#e8f0ff', { a: 0.25, m: 2 });
          return;
        }
        var h = left * left * 22 + left * 28;
        var slant = w.what === 'meteor' ? 0.8 : (w.what === 'lava_bomb' ? 0.5 : 0.08);
        var x = p[0] + h * slant * w.dx, z = p[2] + h * slant * w.dz, y = p[1] + h + 1;
        var spin = time * 6 + w.seed;
        if (w.what === 'meteor') {
          raw(renderer, 'rbox', x, y, z, 3.2, 3.2, 3.2, '#5a3a2a', { yaw: spin, rx: spin * 0.7 });
          raw(renderer, 'sph', x, y, z, 4.6, 4.6, 4.6, '#ff8a2a', { a: 0.45, m: 2 });
          for (var s = 1; s < 6; s++) {
            raw(renderer, 'sph', x + w.dx * s * 2.4, y + s * 3, z + w.dz * s * 2.4, 3.4 - s * 0.45, 3.4 - s * 0.45,
                3.4 - s * 0.45, s < 3 ? '#ffb43a' : '#8a8a8a', { a: 0.6 - s * 0.09, m: s < 3 ? 2 : 0 });
          }
        } else if (w.what === 'lava_bomb') {
          raw(renderer, 'sph', x, y, z, 2.4, 2.4, 2.4, '#ff6a1a', { m: 2 });
          for (var b = 1; b < 4; b++) raw(renderer, 'sph', x + w.dx * b * 1.4, y + b * 2.2, z + w.dz * b * 1.4,
                                          1.6, 1.6, 1.6, '#5a5050', { a: 0.5 - b * 0.12 });
        } else if (w.what === 'hail') {
          raw(renderer, 'sph', x, y, z, 1.3, 1.3, 1.3, '#eaf6ff');
        } else if (w.what === 'coconut') {
          raw(renderer, 'sph', x, y, z, 1.3, 1.5, 1.3, '#6a4a2a', { yaw: spin });
        } else if (w.what === 'boulder') {
          raw(renderer, 'rbox', x, y, z, 4.2, 3.6, 4.0, '#7a7068', { yaw: spin, rx: spin * 0.8 });
        } else {
          // debris: a tumbling plank or a lump of masonry
          var plank = w.seed % 2 < 1;
          raw(renderer, 'box', x, y, z, plank ? 4.2 : 2.2, plank ? 0.5 : 1.8, plank ? 0.9 : 1.6,
              plank ? '#8a6a44' : '#a89a88', { yaw: spin, rx: spin * 1.3 });
        }
      });
    }

    function drawScorches(renderer, dt) {
      scorches = scorches.filter(function (s) {
        s.t += dt;
        if (s.t > s.life) return false;
        var a = 0.55 * (1 - s.t / s.life);
        raw(renderer, 'cyl', s.p[0], s.p[1] + 0.07, s.p[2], s.r, 0.04, s.r, s.c || '#2a2420', { a: a });
        if (s.glow && s.t < 2) raw(renderer, 'cyl', s.p[0], s.p[1] + 0.1, s.p[2], s.r * 0.5, 0.05, s.r * 0.5,
                                   '#ff7a2a', { a: 0.6 * (1 - s.t / 2), m: 2 });
        return true;
      });
      bolts = bolts.filter(function (b) {
        b.t += dt;
        if (b.t > 0.32) return false;
        var flick = Math.floor(b.t * 30) % 3 !== 1;
        if (!flick) return true;
        for (var i = 0; i < b.pts.length - 1; i++) {
          var a = b.pts[i], c = b.pts[i + 1];
          var mx = (a[0] + c[0]) / 2, my = (a[1] + c[1]) / 2, mz = (a[2] + c[2]) / 2;
          var len = Math.hypot(c[0] - a[0], c[1] - a[1], c[2] - a[2]);
          var yaw = Math.atan2(c[0] - a[0], c[2] - a[2]);
          var pitch = Math.atan2(Math.hypot(c[0] - a[0], c[2] - a[2]), c[1] - a[1]);
          raw(renderer, 'box', mx, my, mz, 0.45, len, 0.45, '#f4f8ff', { yaw: yaw, rx: pitch, m: 2 });
          raw(renderer, 'box', mx, my, mz, 1.4, len, 1.4, '#9ab8ff', { yaw: yaw, rx: pitch, m: 2, a: 0.3 });
        }
        return true;
      });
    }

    function drawChunks(renderer, dt) {
      chunks = chunks.filter(function (c) {
        c.t += dt;
        if (c.t > c.life) return false;
        c.v[1] -= 40 * dt;
        c.p[0] += c.v[0] * dt; c.p[1] += c.v[1] * dt; c.p[2] += c.v[2] * dt;
        if (c.p[1] < c.floor) { c.p[1] = c.floor; c.v[1] *= -0.3; c.v[0] *= 0.6; c.v[2] *= 0.6; }
        raw(renderer, c.k || 'box', c.p[0], c.p[1], c.p[2], c.s, c.s, c.s, c.c,
            { yaw: c.t * 5 + c.seed, rx: c.t * 7, a: c.t > c.life - 0.4 ? (c.life - c.t) / 0.4 : 1, m: c.m || 0 });
        return true;
      });
      puffs = puffs.filter(function (p) {
        p.t += dt;
        if (p.t > p.life) return false;
        p.p[0] += p.v[0] * dt; p.p[1] += p.v[1] * dt; p.p[2] += p.v[2] * dt;
        var k = p.t / p.life;
        var s = p.s * (1 + k * 1.6);
        raw(renderer, 'sph', p.p[0], p.p[1], p.p[2], s, s * 0.8, s, p.c, { a: p.a * (1 - k) });
        return true;
      });
    }

    function burst(p, n, colour, speed, size, floor) {
      for (var i = 0; i < n; i++) {
        chunks.push({ p: [p[0], p[1] + 1, p[2]],
                      v: [(Math.random() - 0.5) * speed, Math.random() * speed * 0.9 + 4, (Math.random() - 0.5) * speed],
                      t: 0, life: 1.2 + Math.random() * 0.8, s: size * (0.5 + Math.random() * 0.7), c: colour,
                      seed: Math.random() * 6, floor: floor === undefined ? p[1] : floor });
      }
    }
    function dust(p, n, colour, size, rise) {
      for (var i = 0; i < n; i++) {
        puffs.push({ p: [p[0] + (Math.random() - 0.5) * size * 2, p[1] + Math.random() * 2, p[2] + (Math.random() - 0.5) * size * 2],
                     v: [(Math.random() - 0.5) * 3, (rise || 2) + Math.random() * 2, (Math.random() - 0.5) * 3],
                     t: 0, life: 1.6 + Math.random() * 1.2, s: size * (0.6 + Math.random() * 0.6), c: colour || '#c8b8a0',
                     a: 0.55 });
      }
    }

    function drawTornado(renderer, time) {
      var tw = ax.tw;
      if (!tw) return;
      var x = tw[0], y = tw[1], z = tw[2], r = tw[3], core = tw[4];
      var rings = 16, top = 80;
      for (var i = 0; i < rings; i++) {
        var f = i / (rings - 1);
        var rad = core * 0.55 + (r * 1.05 - core * 0.55) * Math.pow(f, 1.6);
        var sway = Math.sin(time * 1.3 + f * 3) * 3 * f;
        var cx = x + Math.cos(time * 2 + f * 5) * sway, cz = z + Math.sin(time * 2 + f * 5) * sway;
        raw(renderer, 'cyl', cx, y + f * top, cz, rad * 2, top / rings + 1.2, rad * 2,
            i % 2 ? '#6a6458' : '#7e786a', { a: 0.26 + f * 0.12, yaw: time * 4 + i });
      }
      // what it has picked up
      for (var k = 0; k < 26; k++) {
        var h = (hash(k) * top * 0.8 + time * 6 * (0.4 + hash(k + 1))) % (top * 0.8);
        var rr = core * 0.7 + (h / top) * r * 0.9 + hash(k + 2) * 3;
        var a = time * (2.4 + hash(k + 3) * 1.6) + k;
        var colours = ['#8a6a44', '#a89a88', '#5a4a3a', '#3a8a3a', '#d8402a'];
        raw(renderer, 'box', x + Math.cos(a) * rr, y + h + 1, z + Math.sin(a) * rr, 0.6 + hash(k + 4) * 1.4,
            0.3 + hash(k + 5) * 0.6, 0.6 + hash(k + 6) * 1.2, colours[k % colours.length],
            { yaw: a * 2, rx: a * 1.4 });
      }
      raw(renderer, 'cyl', x, y + 1.2, z, r * 1.6, 2.4, r * 1.6, '#a89a80', { a: 0.22 });
      var me = myPos(), d = Math.hypot(me[0] - x, me[2] - z);
      if (now() - roarAt > 1.6) {
        roarAt = now();
        client.audio.play('cc_roar', { volume: Math.max(0.05, Math.min(1, 1.2 - d / 140)) });
      }
    }

    function drawFronts(renderer, time) {
      var fr = ax.fr;
      var front = parts('front')[0];
      if (!fr || !front) return;
      var lanes = front.lanes || [];
      var depth = front.depth || 14;
      var snow = front.what !== 'rocks';
      var body = snow ? ['#ffffff', '#f2f6fc', '#e6eef8'] : ['#7a6a5a', '#8a7a68', '#5a4e44'];
      fr.forEach(function (s, i) {
        var lane = lanes[i];
        if (!lane || s <= 0) return;
        if (!lane._path) lane._path = new Path(lane.pts.map(function (p) { return [p[0] + centre[0], p[1] + centre[2]]; }));
        var path = lane._path;
        if (s - depth > path.length) return;
        var head = Math.min(s, path.length);
        var w = lane.w || 20;
        for (var back = 0; back <= depth; back += 4) {
          if (head - back < 0) break;
          var at = path.at(head - back);
          var ux = at[2], uz = at[3], px = -uz, pz = ux;
          // a churning wall at the head, lower behind it
          var tall = (back < 4 ? 13 : Math.max(5, 11 - back * 0.35)) * (snow ? 1 : 0.75);
          for (var o = -w / 2 + 2.5; o <= w / 2 - 2.5; o += 4.5) {
            var j = hash(i * 97 + Math.round(o) * 13 + Math.round(back));
            var gx = at[0] + px * o, gz = at[1] + pz * o;
            var gy = groundAt(gx, gz);
            var size = (snow ? 9 : 5) + j * 4;
            var tumble = time * (snow ? 2 : 4) + j * 6;
            raw(renderer, snow ? 'sph' : 'rbox', gx + ux * Math.sin(tumble) * 1.2, gy + tall * 0.42 + Math.abs(Math.sin(tumble)) * 1.5,
                gz + uz * Math.sin(tumble) * 1.2, size, tall, size, body[Math.floor(j * 3) % 3],
                { yaw: tumble, rx: snow ? 0 : tumble * 0.7, m: snow ? 2 : 0 });
            // the powder thrown up over the head of it
            if (snow && back < 8) {
              var lift = (time * 3 + j * 5) % 6;
              raw(renderer, 'sph', gx - ux * 2, gy + tall + 3 + lift, gz - uz * 2, 13 + j * 4, 9 + lift, 13 + j * 4,
                  '#ffffff', { a: 0.4 - lift * 0.05, m: 2 });
            }
          }
        }
        // spray off the head of it
        if (Math.random() < 0.35) {
          var tip = path.at(head);
          var off = (Math.random() - 0.5) * w;
          var tx = tip[0] - tip[3] * off, tz = tip[1] + tip[2] * off;
          dust([tx, groundAt(tx, tz) + 3, tz], 1, snow ? '#ffffff' : '#a89880', snow ? 4 : 3, 4);
        }
      });
      if (now() - rumbleAt > 1.1) {
        rumbleAt = now();
        client.audio.play(snow ? 'cc_avalanche' : 'cc_rumble', { volume: 0.55 });
      }
    }

    function drawFire(renderer, time, dt) {
      var cells = marks.fire || [];
      var burning = {};
      (ax.fi || []).forEach(function (i) { burning[i] = 1; });
      Object.keys(wasBurning).forEach(function (i) { if (!burning[i]) burnt[i] = 1; });
      wasBurning = burning;
      var me = myPos(), nearest = 1e9;
      Object.keys(burning).forEach(function (i) {
        var c = cells[i];
        if (!c) return;
        var p = c.p;
        nearest = Math.min(nearest, Math.hypot(me[0] - p[0], me[2] - p[2]));
        for (var k = 0; k < 11; k++) {
          var hx = p[0] + (hash(i * 31 + k) - 0.5) * 16, hz = p[2] + (hash(i * 17 + k + 5) - 0.5) * 14;
          var base = groundAt(hx, hz, p[1] + 40);
          var flick = 0.7 + 0.3 * Math.sin(time * (9 + k) + k * 2.1);
          var h = (4 + hash(k + i) * 5) * flick;
          raw(renderer, 'cone', hx, base + h / 2, hz, 2.6 + hash(k) * 1.6, h, 2.6 + hash(k) * 1.6,
              k % 3 ? '#ff7a1a' : '#ffd23a', { m: 2, a: 0.92, yaw: time + k });
          if (k % 3 === 0) raw(renderer, 'cone', hx, base + h * 0.3, hz, 1.4, h * 0.6, 1.4, '#fff2a8',
                               { m: 2, yaw: -time + k });
        }
        if (Math.random() < dt * 6) {
          puffs.push({ p: [p[0] + (Math.random() - 0.5) * 10, p[1] + 16, p[2] + (Math.random() - 0.5) * 10],
                       v: [gust.until > now() ? gust.dir[0] * 6 : 1, 5 + Math.random() * 3, gust.until > now() ? gust.dir[1] * 6 : 0.5],
                       t: 0, life: 4 + Math.random() * 2, s: 5 + Math.random() * 3, c: '#3a3430', a: 0.5 });
        }
      });
      Object.keys(burnt).forEach(function (i) {
        var c = cells[i];
        if (!c || Math.random() > dt * 1.5) return;
        puffs.push({ p: [c.p[0] + (Math.random() - 0.5) * 8, c.p[1] + 10, c.p[2] + (Math.random() - 0.5) * 8],
                     v: [0.5, 3, 0.4], t: 0, life: 4, s: 4, c: '#6a625a', a: 0.35 });
      });
      if (nearest < 80 && now() - fireAt > 0.9) {
        fireAt = now();
        client.audio.play('cc_fire', { volume: Math.max(0.1, 1 - nearest / 80) });
      }
    }

    function drawCracks(renderer, time) {
      var t = now();
      Object.keys(cracks).forEach(function (i) {
        var c = cracks[i];
        var k = Math.max(0, Math.min(1, 1 - (c.at - t) / c.total));
        if (t > c.at + 0.5) { delete cracks[i]; return; }
        var p = c.p;
        for (var j = 0; j < 9; j++) {
          var a = j * 0.7 + hash(j + i * 5) * 0.5;
          var len = c.r * (0.4 + k * 0.8) * (0.7 + hash(j) * 0.5);
          raw(renderer, 'box', p[0] + Math.cos(a) * len / 2, p[1] + 0.1, p[2] + Math.sin(a) * len / 2, len, 0.06, 0.35,
              '#1a120a', { yaw: -a, a: 0.85 });
        }
        raw(renderer, 'cyl', p[0], p[1] + 0.08, p[2], c.r * 2, 0.05, c.r * 2, '#ff3a2a',
            { a: 0.15 + 0.2 * Math.abs(Math.sin(time * (5 + k * 10))), m: 2 });
        if (Math.random() < 0.2) dust([p[0] + (Math.random() - 0.5) * c.r, p[1], p[2] + (Math.random() - 0.5) * c.r], 1,
                                      '#b8a080', 1.5, 1);
      });
    }

    /* rain, snow or hail round the camera, never under a roof */
    function weather() {
      if (!active()) return '';
      var rain = parts('rain')[0];
      if (rain) return rain.what === 'hail' ? 'hail' : (rain.what === 'acid' ? 'acid' : 'rain');
      if (parts('cold').length) return 'snow';
      if (parts('tornado').length) return 'drizzle';
      return '';
    }

    function roofAt(x, z) {
      var cell = Math.round((x - roofs.eye[0]) / 8) + ',' + Math.round((z - roofs.eye[2]) / 8);
      var y = roofs.cells[cell];
      return y === undefined ? -1e9 : y;
    }

    function updateRoofs(eye) {
      if (now() - roofs.at < 0.4 && Math.hypot(eye[0] - roofs.eye[0], eye[2] - roofs.eye[2]) < 4) return;
      roofs.at = now();
      roofs.eye = eye.slice();
      roofs.cells = {};
      var phys = client.physics;
      if (!phys) return;
      for (var gx = -5; gx <= 5; gx++) {
        for (var gz = -5; gz <= 5; gz++) {
          var x = eye[0] + gx * 8, z = eye[2] + gz * 8, top = eye[1] + 60;
          roofs.cells[gx + ',' + gz] = top - phys.rayDistance([x, top, z], [0, -1, 0], 160);
        }
      }
    }

    function drawWeather(renderer, dt, time) {
      var kind = weather();
      var target = kind ? (kind === 'drizzle' ? 70 : 190) : 0;
      while (drops.length < target) {
        drops.push({ o: [(Math.random() - 0.5) * 80, Math.random() * 50 - 15, (Math.random() - 0.5) * 80],
                     s: 0.8 + Math.random() * 0.4 });
      }
      if (drops.length > target) drops.length = target;
      if (!drops.length) return;
      var eye = eyePos();
      updateRoofs(eye);
      var windy = gust.until > now();
      var wx = windy ? gust.dir[0] * 22 : 0, wz = windy ? gust.dir[1] * 22 : 0;
      var fall = { rain: 70, drizzle: 60, acid: 55, hail: 80, snow: 9 }[kind] || 60;
      if (kind === 'snow') { wx *= 1.3; wz *= 1.3; }
      for (var i = 0; i < drops.length; i++) {
        var d = drops[i];
        d.o[1] -= fall * d.s * dt;
        d.o[0] += wx * dt + (kind === 'snow' ? Math.sin(time * 1.5 + i) * 1.5 * dt : 0);
        d.o[2] += wz * dt + (kind === 'snow' ? Math.cos(time * 1.3 + i) * 1.5 * dt : 0);
        if (d.o[1] < -15 || Math.abs(d.o[0]) > 40 || Math.abs(d.o[2]) > 40) {
          d.o = [(Math.random() - 0.5) * 80, 30 + Math.random() * 6, (Math.random() - 0.5) * 80];
        }
        var x = eye[0] + d.o[0], y = eye[1] + d.o[1], z = eye[2] + d.o[2];
        if (y < roofAt(x, z)) continue;
        if (kind === 'snow') {
          raw(renderer, 'sph', x, y, z, 0.35, 0.35, 0.35, '#ffffff', { a: 0.9, m: 2 });
        } else if (kind === 'hail') {
          raw(renderer, 'sph', x, y, z, 0.4, 0.4, 0.4, '#eaf6ff', { m: 2 });
        } else {
          var tilt = Math.atan2(Math.hypot(wx, wz), fall) * 0.9;
          raw(renderer, 'box', x, y, z, 0.07, 2.2, 0.07, kind === 'acid' ? '#8aff4a' : '#a8c8e8',
              { a: 0.38, rx: tilt, yaw: Math.atan2(wx, wz) });
        }
      }
      if (kind !== 'snow' && now() - rainAt > 2.0) {
        rainAt = now();
        client.audio.play(kind === 'hail' ? 'cc_hail' : 'cc_rain', { volume: 0.45 });
      }
    }

    function drawWind(renderer, dt) {
      var on = gust.until > now() && active();
      var target = on ? 34 : 0;
      while (streaks.length < target) streaks.push({ o: [(Math.random() - 0.5) * 70, Math.random() * 14 - 2, (Math.random() - 0.5) * 70], l: 4 + Math.random() * 6 });
      if (streaks.length > target) streaks.length = target;
      if (!streaks.length) return;
      var eye = eyePos();
      var dx = gust.dir[0], dz = gust.dir[1];
      var yaw = Math.atan2(dx, dz);
      streaks.forEach(function (s) {
        s.o[0] += dx * 60 * dt; s.o[2] += dz * 60 * dt;
        if (Math.abs(s.o[0]) > 36 || Math.abs(s.o[2]) > 36) {
          s.o = [-dx * 34 + (Math.random() - 0.5) * 70 * Math.abs(dz), Math.random() * 14 - 2,
                 -dz * 34 + (Math.random() - 0.5) * 70 * Math.abs(dx)];
        }
        raw(renderer, 'box', eye[0] + s.o[0], eye[1] + s.o[1], eye[2] + s.o[2], 0.08, 0.08, s.l, '#ffffff',
            { yaw: yaw, a: 0.22 });
      });
    }

    // --------------------------------------------------------- the hud
    function roleChip() {
      if (!client.myTeam || arena.phase === 'intermission') { arena.setRole(''); return; }
      if (arena.me.out) {
        arena.setRole('<b>DOWN</b> &bull; back at the next calm', 'out');
        return;
      }
      var bits = [];
      if (arena.me.carry) bits.push('<b style="color:#5aff8a">CARRYING</b> someone to the EVAC');
      (arena.me.pw || []).forEach(function (k) {
        var p = POWERS[k];
        if (p) bits.push('<b style="color:' + p[1] + '">' + p[0] + '</b>');
      });
      if ((arena.me.shoes || 0) > 0) bits.push('<b style="color:' + POWERS.shoes[1] + '">RUNNING SHOES</b>');
      var team = client.myTeam;
      arena.setRole('<b style="color:' + TEAM_LIGHT[team] + '">' + esc(arena.teamName(team).toUpperCase()) +
                    '</b>' + (bits.length ? ' &bull; ' + bits.join(' &bull; ') : ''), team);
    }

    function hud(state) {
      var left = stageLeft();
      var name = esc(cc.name || 'the disaster');
      var sub = '', timer, title;
      if (arena.phase === 'active' && cc.stage === 'calm') {
        title = 'DISASTER ' + cc.n + ' OF ' + cc.of + (cc.big ? ' -- THE BIG ONE' : '');
        timer = (siren > 0 ? 'SIREN! ' : 'NEXT IN ') + Arena.fmt(left);
        sub = '<b>Next: ' + name.toUpperCase() + '</b> &bull; ' + esc(cc.line || '');
        if (cc.stranded) sub += '<br>' + cc.stranded + ' stranded &bull; hold <b>E</b> by one, carry them to the EVAC';
      } else if (arena.phase === 'active' && cc.stage === 'active') {
        title = name.toUpperCase() + '!';
        timer = Arena.fmt(left) + ' TO SURVIVE';
        sub = esc(cc.line || '') + (cc.stranded ? ' &bull; ' + cc.stranded + ' stranded' : '');
      }
      var bars = [];
      var mine = client.myTeam;
      if (mine && cc.alive) {
        var total = (cc.alive.red || 0) + (cc.alive.blue || 0);
        if (total) {
          bars.push({ label: 'Standing', value: (cc.alive[mine] || 0) / Math.max(1, total), colour: TEAM[mine],
                      text: (cc.alive.red || 0) + ' v ' + (cc.alive.blue || 0) });
        }
      }
      if (active() && parts('cold').length && !arena.me.out) {
        var cold = arena.me.cold || 0;
        bars.push({ label: 'Cold', value: cold, colour: cold > 0.85 ? '#ff6a6a' : '#8ad8ff',
                    text: cold >= 1 ? 'FREEZING' : Math.round(cold * 100) + '%' });
      }
      if ((arena.me.shoes || 0) > 0) {
        bars.push({ label: 'Shoes', value: arena.me.shoes / 25, colour: POWERS.shoes[1], text: Math.ceil(arena.me.shoes) + 's' });
      }
      var out = {
        left: { value: cc.points ? cc.points.red || 0 : 0, label: arena.teamName('red'), colour: TEAM_LIGHT.red },
        right: { value: cc.points ? cc.points.blue || 0 : 0, label: arena.teamName('blue'), colour: TEAM_LIGHT.blue },
        sub: sub, bars: bars,
        urgent: (cc.stage === 'calm' && siren > 0) || (cc.stage === 'active' && left < 6)
      };
      if (title) out.title = title;
      if (timer) out.timer = timer;
      return out;
    }

    function nearStranded() {
      if (!inPlay() || arena.me.carry) return null;
      var me = myPos(), best = null, bestD = PICKUP_REACH - 0.3;
      (ax.st || []).forEach(function (s) {
        if (s[4] !== 'wait') return;
        var d = Math.hypot(me[0] - s[1], me[1] - s[2], me[2] - s[3]);
        if (d < bestD) { best = s; bestD = d; }
      });
      return best;
    }

    // -------------------------------------------------------- messages
    var messages = {
      ccs: function (msg) { applyState(msg.s && msg.s.cc); },
      ccx: function (msg) {
        var k = msg.k, me = client.myId;
        if (k === 'next') {
          siren = 0;
          seenCrate = {};
          arena.banner('DISASTER ' + msg.n + ' OF ' + msg.of + (msg.big ? ': THE BIG ONE' : ''),
                       '<b>' + esc(msg.name) + '</b> in ' + Math.round(msg['in']) + 's &bull; ' + esc(msg.line), 'area', 4200);
          client.audio.play('cc_bell', { volume: 0.6 });
        } else if (k === 'siren') {
          siren = msg['in'] || 7;
          arena.banner(esc(String(msg.name).toUpperCase()) + '!', esc(cc.line || 'Get somewhere safe!'), 'bad', 2600);
          client.audio.play('cc_siren', { volume: 0.75 });
        } else if (k === 'hit') {
          siren = 0;
          arena.flashScreen('rgba(255,255,255,0.3)', 260);
          var id = msg.id;
          client.audio.play(id === 'tsunami' || id === 'flood' ? 'cc_wave' :
                            (id === 'eruption' ? 'cc_boom' : 'cc_rumble'), { volume: 0.8 });
        } else if (k === 'passed') {
          var st = msg.standing || {};
          arena.banner(esc(String(msg.name || 'It').toUpperCase()) + ' PASSED',
                       esc(arena.teamName('red')) + ' ' + (st.red || 0) + ' standing &bull; ' +
                       esc(arena.teamName('blue')) + ' ' + (st.blue || 0) + ' standing', 'go', 3200);
          client.audio.play('cc_cheer', { volume: 0.7 });
          warns = {}; cracks = {};
          shake.until = 0; gust.until = 0;
        } else if (k === 'warn') {
          var a = Math.random() * Math.PI * 2;
          warns[msg.id] = { p: msg.p, r: msg.r, what: msg.what, at: now() + (msg['in'] || 1.5), total: msg['in'] || 1.5,
                            dx: Math.cos(a), dz: Math.sin(a), seed: Math.random() * 6 };
          if (msg.what !== 'lightning' && msg.what !== 'hail') play('cc_whistle', msg.p, 0.5);
        } else if (k === 'land') {
          delete warns[msg.id];
          var p = msg.p, r = msg.r || 5;
          if (msg.what === 'lightning') {
            var pts = [[p[0], p[1], p[2]]], y = p[1];
            while (y < p[1] + 110) {
              y += 6 + Math.random() * 8;
              var last = pts[pts.length - 1];
              pts.push([last[0] + (Math.random() - 0.5) * 7, y, last[2] + (Math.random() - 0.5) * 7]);
            }
            bolts.push({ pts: pts, t: 0 });
            scorches.push({ p: p, r: r * 1.2, t: 0, life: 8, glow: true });
            var d = Math.hypot(p[0] - myPos()[0], p[2] - myPos()[2]);
            arena.flashScreen('rgba(230,240,255,' + Math.max(0.15, 0.6 - d / 300) + ')', 160);
            client.audio.play('cc_thunder', { volume: Math.max(0.25, 1 - d / 260) });
          } else if (msg.what === 'hail') {
            burst(p, 5, '#eaf6ff', 8, 0.5);
            play('cc_tick', p, 0.6);
          } else if (msg.what === 'coconut') {
            burst(p, 4, '#6a4a2a', 8, 0.7);
            burst(p, 3, '#f2f0ea', 6, 0.5);
            play('cc_bonk', p, 0.9);
          } else {
            var colour = { meteor: '#5a3a2a', lava_bomb: '#ff6a1a', debris: '#a89a88', boulder: '#7a7068' }[msg.what] || '#8a7a6a';
            burst(p, 10, colour, 16, msg.what === 'boulder' ? 1.6 : 1.0);
            dust(p, 6, msg.what === 'lava_bomb' ? '#4a3a34' : '#b8a890', r * 0.6, 3);
            scorches.push({ p: p, r: r * 1.5, t: 0, life: 10, glow: msg.what === 'meteor' || msg.what === 'lava_bomb' });
            if (client.particles) client.particles.burst('explosion', [p[0], p[1] + 1, p[2]]);
            play('cc_boom', p, msg.what === 'debris' ? 0.6 : 1);
          }
          var me2 = myPos();
          var dd = Math.hypot(me2[0] - p[0], me2[2] - p[2]);
          if (dd < r * 3 && msg.what !== 'hail') shake = { until: Math.max(shake.until, now() + 0.35), power: Math.max(shake.power, 1.4 - dd / (r * 3)) };
        } else if (k === 'gust') {
          gust = { until: now() + (msg['for'] || 4), dir: msg.dir || [1, 0] };
          client.audio.play('cc_wind', { volume: 0.7 });
        } else if (k === 'shake') {
          shake = { until: now() + (msg['for'] || 10), power: msg.power || 1 };
          client.audio.play('cc_rumble', { volume: 0.9 });
        } else if (k === 'collapse') {
          if (msg.name) client.hud.toast('<b>' + esc(msg.name.charAt(0).toUpperCase() + msg.name.slice(1)) + '</b> gave way!', 'bad');
          client.audio.play('cc_crash', { volume: 0.9 });
        } else if (k === 'crack') {
          cracks[msg.i] = { p: msg.p, r: msg.r || 6, at: now() + (msg['in'] || 3), total: msg['in'] || 3 };
          play('cc_crack', msg.p, 1);
        } else if (k === 'sink') {
          var c = cracks[msg.i];
          if (c) {
            dust(c.p, 12, '#b8a080', c.r * 0.5, 2);
            burst(c.p, 10, '#6a5a3a', 10, 1.0, c.p[1] - 8);
            play('cc_crash', c.p, 1);
          }
          delete cracks[msg.i];
        } else if (k === 'lost') {
          client.hud.toast('A townsperson was ' + esc(msg.why || 'lost'), 'bad');
          play('cc_lost', msg.p, 0.8);
        } else if (k === 'dropped') {
          play('cc_lost', msg.p, 0.5);
        } else if (k === 'carry') {
          if (msg.by === me) {
            client.hud.toast('Got them! Get to the <b>EVAC</b> -- you are slower carrying', 'good');
            client.audio.play('cc_lift', { volume: 0.8 });
          }
        } else if (k === 'rescued') {
          var mine = msg.team === client.myTeam;
          client.hud.toast('<b>' + esc(msg.by) + '</b> rescued a townsperson! +15 ' + esc(arena.teamName(msg.team)),
                           mine ? 'good' : 'bad');
          client.audio.play('cc_rescue', { volume: mine ? 0.9 : 0.5 });
          (marks.evac || []).forEach(function (m) {
            if (client.particles) client.particles.burst('confetti', [m.p[0], m.p[1] + 3, m.p[2]]);
          });
        } else if (k === 'crate') {
          var cp = crates[msg.id];
          if (cp) {
            burst(cp, 8, '#a87a3a', 10, 0.6);
            if (client.particles) client.particles.burst('pickup', [cp[0], cp[1] + 1.5, cp[2]]);
            if (msg.by !== me) play('cc_crate', cp, 0.6);
          }
          delete crates[msg.id];
        } else if (k === 'power') {
          var pw = POWERS[msg.what] || ['A POWER-UP', '#ffffff', ''];
          arena.banner('<span style="color:' + pw[1] + '">' + pw[0] + '</span>', esc(pw[2]), 'go', 2400);
          client.audio.play('cc_crate', { volume: 0.9 });
        } else if (k === 'saved') {
          client.hud.toast('Your <b>hard hat</b> took the hit!', 'good');
          client.audio.play('cc_bonk', { volume: 1 });
        }
      }
    };

    // ----------------------------------------------------------- hooks
    return {
      init: function () { makeVeil(); },
      onMap: loadMap,
      onArea: function () { arena.setRole(''); reset(); },
      onState: function (state) { applyState(state.cc); },
      onSnapshot: function (msg) { ax = msg.ax || {}; },
      onMe: function () { roleChip(); },
      onPhase: function (msg) {
        if (msg.phase !== 'active') { reset(); }
        roleChip();
      },
      onDynamic: function (changes) {
        // whatever just gave way goes up in a cloud of dust
        Object.keys(changes).forEach(function (key) {
          if (changes[key] || arena.phase !== 'active') return;
          var d = arena.dynamic[key];
          ((d && d.boxes) || []).slice(0, 12).forEach(function (b) {
            var c = [(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2, (b[0][2] + b[1][2]) / 2];
            dust(c, 2, '#c8b8a0', 3, 2);
            burst(c, 2, '#8a6a44', 10, 0.9, groundAt(c[0], c[2], c[1]));
          });
        });
      },
      goLine: function () { return 'The calm will not last'; },
      messages: messages,
      hud: hud,
      prompt: function () {
        if (!inPlay() || arena.phase !== 'active') return '';
        if (arena.me.carry) return 'Carrying someone -- get them to the EVAC point';
        if (nearStranded()) return 'Hold E: pick them up';
        return '';
      },
      canFire: function () { return false; },
      jolt: function () {
        var t = now();
        if (t >= shake.until) return null;
        var left = shake.until - t;
        var a = Math.min(1, left / 1.5) * 0.22 * shake.power;
        return [Math.sin(t * 37) * a, Math.sin(t * 29 + 1) * a * 0.6, Math.cos(t * 41) * a, Math.sin(t * 23) * a * 0.02];
      },
      draw: function (renderer, dt, time) {
        if (siren > 0) siren = Math.max(0, siren - dt);
        moodSky(dt);
        updateVeil();
        if (arena.phase !== 'active') return;
        drawLevels(renderer, time);
        drawWarnings(renderer, time);
        drawScorches(renderer, dt);
        drawTornado(renderer, time);
        drawFronts(renderer, time);
        drawFire(renderer, time, dt);
        drawCracks(renderer, time);
        drawChunks(renderer, dt);
        drawStranded(renderer, time);
        drawCrates(renderer, time);
        drawEvac(renderer, time);
        drawWeather(renderer, dt, time);
        drawWind(renderer, dt);
        if (shake.until > now() && now() - rumbleAt > 1.4 && !parts('front').length) {
          rumbleAt = now();
          client.audio.play('cc_rumble', { volume: 0.5 * Math.min(1, shake.power) });
        }
      },
      scoreHead: function () {
        return '<th>Player</th><th>Team</th><th>Survived</th><th>Rescues</th><th>Score</th>';
      },
      scoreRow: function (row) {
        return '<td>' + esc(arena.teamName(row.team)) + (row.out ? ' (down)' : '') + '</td><td>' + (row.sv || 0) +
          '</td><td>' + (row.rs || 0) + '</td><td>' + row.score + '</td>';
      }
    };
  });

  // ============================================================ sounds
  var GA = global.GameAudio;
  if (GA && GA.register) {
    GA.register('cc_siren', function (vol) {
      for (var i = 0; i < 3; i++) {
        this.later(i * 900, function () {
          this.tone({ type: 'sawtooth', freq: 420, freqEnd: 880, dur: 0.45, gain: 0.07 * vol });
          this.later(450, function () { this.tone({ type: 'sawtooth', freq: 880, freqEnd: 420, dur: 0.45, gain: 0.07 * vol }); });
        });
      }
    });
    GA.register('cc_bell', function (vol) {
      [880, 660].forEach(function (f, i) {
        this.later(i * 380, function () {
          this.tone({ type: 'triangle', freq: f, dur: 0.9, gain: 0.12 * vol });
          this.tone({ type: 'sine', freq: f * 2.01, dur: 0.6, gain: 0.04 * vol });
        });
      }, this);
    });
    GA.register('cc_thunder', function (vol) {
      this.noise({ filter: 'lowpass', freq: 2400, freqEnd: 120, dur: 0.25, gain: 0.35 * vol });
      this.later(120, function () { this.noise({ filter: 'lowpass', freq: 400, freqEnd: 60, dur: 1.8, gain: 0.3 * vol }); });
    });
    GA.register('cc_boom', function (vol) {
      this.tone({ type: 'sine', freq: 120, freqEnd: 30, dur: 0.6, gain: 0.3 * vol });
      this.noise({ filter: 'lowpass', freq: 1200, freqEnd: 100, dur: 0.7, gain: 0.3 * vol });
    });
    GA.register('cc_whistle', function (vol) {
      this.tone({ type: 'sine', freq: 1800, freqEnd: 500, dur: 1.2, gain: 0.05 * vol });
    });
    GA.register('cc_wave', function (vol) {
      this.noise({ filter: 'lowpass', freq: 300, freqEnd: 1400, dur: 1.6, gain: 0.3 * vol });
      this.later(1200, function () { this.noise({ filter: 'lowpass', freq: 1400, freqEnd: 200, dur: 2.0, gain: 0.28 * vol }); });
    });
    GA.register('cc_wind', function (vol) {
      this.noise({ filter: 'bandpass', freq: 300, freqEnd: 900, dur: 1.4, gain: 0.18 * vol });
      this.later(900, function () { this.noise({ filter: 'bandpass', freq: 900, freqEnd: 250, dur: 1.6, gain: 0.15 * vol }); });
    });
    GA.register('cc_roar', function (vol) {
      this.noise({ filter: 'lowpass', freq: 500, freqEnd: 300, dur: 1.8, gain: 0.25 * vol });
      this.tone({ type: 'sawtooth', freq: 55, freqEnd: 48, dur: 1.8, gain: 0.05 * vol });
    });
    GA.register('cc_rumble', function (vol) {
      this.noise({ filter: 'lowpass', freq: 160, freqEnd: 80, dur: 1.4, gain: 0.4 * vol });
      this.tone({ type: 'sine', freq: 38, freqEnd: 30, dur: 1.4, gain: 0.18 * vol });
    });
    GA.register('cc_avalanche', function (vol) {
      this.noise({ filter: 'lowpass', freq: 700, freqEnd: 300, dur: 1.3, gain: 0.3 * vol });
      this.noise({ filter: 'highpass', freq: 3000, dur: 1.0, gain: 0.05 * vol });
    });
    GA.register('cc_crash', function (vol) {
      this.noise({ filter: 'lowpass', freq: 2000, freqEnd: 150, dur: 0.9, gain: 0.35 * vol });
      for (var i = 0; i < 5; i++) {
        this.later(80 + i * 90, function () { this.noise({ filter: 'bandpass', freq: 600 + Math.random() * 900, dur: 0.12, gain: 0.15 * vol }); });
      }
    });
    GA.register('cc_crack', function (vol) {
      for (var i = 0; i < 4; i++) {
        this.later(i * 110, function () { this.noise({ filter: 'highpass', freq: 1800, dur: 0.06, gain: 0.25 * vol }); });
      }
      this.tone({ type: 'sine', freq: 70, freqEnd: 40, dur: 0.8, gain: 0.12 * vol });
    });
    GA.register('cc_fire', function (vol) {
      for (var i = 0; i < 6; i++) {
        this.later(Math.random() * 800, function () { this.noise({ filter: 'bandpass', freq: 1200 + Math.random() * 2400, dur: 0.05, gain: 0.12 * vol }); });
      }
      this.noise({ filter: 'lowpass', freq: 400, dur: 0.9, gain: 0.08 * vol });
    });
    GA.register('cc_rain', function (vol) {
      this.noise({ filter: 'highpass', freq: 2200, freqEnd: 2000, dur: 2.2, gain: 0.06 * vol });
    });
    GA.register('cc_hail', function (vol) {
      for (var i = 0; i < 14; i++) {
        this.later(Math.random() * 1900, function () { this.noise({ filter: 'highpass', freq: 3000, dur: 0.03, gain: 0.12 * vol }); });
      }
    });
    GA.register('cc_tick', function (vol) {
      this.noise({ filter: 'highpass', freq: 3500, dur: 0.04, gain: 0.2 * vol });
    });
    GA.register('cc_bonk', function (vol) {
      this.tone({ type: 'square', freq: 520, freqEnd: 260, dur: 0.12, gain: 0.12 * vol });
      this.tone({ type: 'sine', freq: 1400, dur: 0.25, gain: 0.06 * vol });
    });
    GA.register('cc_cheer', function (vol) {
      [523, 659, 784].forEach(function (f, i) {
        this.later(i * 120, function () { this.tone({ type: 'triangle', freq: f, dur: 0.3, gain: 0.1 * vol }); });
      }, this);
      this.noise({ filter: 'bandpass', freq: 1500, dur: 1.2, gain: 0.06 * vol });
    });
    GA.register('cc_rescue', function (vol) {
      [659, 784, 988, 1318].forEach(function (f, i) {
        this.later(i * 90, function () { this.tone({ type: 'triangle', freq: f, dur: 0.22, gain: 0.12 * vol }); });
      }, this);
    });
    GA.register('cc_lift', function (vol) {
      this.tone({ type: 'sine', freq: 300, freqEnd: 600, dur: 0.2, gain: 0.1 * vol });
      this.noise({ filter: 'bandpass', freq: 800, dur: 0.15, gain: 0.08 * vol });
    });
    GA.register('cc_crate', function (vol) {
      this.noise({ filter: 'bandpass', freq: 900, freqEnd: 300, dur: 0.18, gain: 0.2 * vol });
      [784, 1046].forEach(function (f, i) {
        this.later(120 + i * 90, function () { this.tone({ type: 'square', freq: f, dur: 0.12, gain: 0.07 * vol }); });
      }, this);
    });
    GA.register('cc_lost', function (vol) {
      this.tone({ type: 'triangle', freq: 440, freqEnd: 220, dur: 0.5, gain: 0.1 * vol });
    });
  }

  // =================================================== arrival scenes
  var Intro = global.AreaIntro;
  if (!Intro) return;
  var K = Intro.kit;
  var VW = K.VW, VH = K.VH, TAU = K.TAU, HEAVY = K.HEAVY;
  var seg = K.seg, lerp = K.lerp, outCubic = K.outCubic, outBack = K.outBack;
  var dot = K.dot, additive = K.additive, fitSize = K.fitSize;
  var between = K.between, wobble = K.wobble, mix = K.mix;

  function nameText(ctx, name, x, y, max, colour, shade, font) {
    var size = fitSize(ctx, name, 'bold #px ' + (font || HEAVY), 110, max, 0.04);
    ctx.font = 'bold ' + size + 'px ' + (font || HEAVY);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = shade;
    ctx.fillText(name, x + 4, y + 5);
    ctx.fillStyle = colour;
    ctx.fillText(name, x, y);
    ctx.textAlign = 'left';
    return size;
  }

  function house(ctx, x, y, w, h, wall, roof, lit) {
    ctx.fillStyle = wall; ctx.fillRect(x, y - h, w, h);
    ctx.fillStyle = roof;
    ctx.beginPath(); ctx.moveTo(x - 8, y - h); ctx.lineTo(x + w / 2, y - h - w * 0.42); ctx.lineTo(x + w + 8, y - h); ctx.fill();
    ctx.fillStyle = lit ? '#ffd88a' : '#3a4a5a';
    ctx.fillRect(x + w * 0.2, y - h * 0.7, w * 0.2, h * 0.25);
    ctx.fillRect(x + w * 0.6, y - h * 0.7, w * 0.2, h * 0.25);
  }

  /* a blocky little person in the classic colours, arms up */
  function person(ctx, x, y, s, t, phase) {
    var wave = Math.sin(t * 10 + phase) * 0.5;
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    ctx.fillStyle = '#0d69ac'; ctx.fillRect(-10, -26, 9, 26); ctx.fillRect(1, -26, 9, 26);
    ctx.fillStyle = '#c4281c'; ctx.fillRect(-11, -52, 22, 27);
    ctx.fillStyle = '#f5cd30';
    ctx.save(); ctx.translate(-11, -50); ctx.rotate(-2.6 + wave); ctx.fillRect(-4, 0, 8, 24); ctx.restore();
    ctx.save(); ctx.translate(11, -50); ctx.rotate(2.6 - wave); ctx.fillRect(-4, 0, 8, 24); ctx.restore();
    ctx.fillRect(-8, -68, 16, 16);
    ctx.restore();
  }

  // ------------------------------------------------------- Port Sunny
  Intro.register('cc_portsunny', {
    name: 'Port Sunny',
    tagline: 'Ice creams on the harbour wall. Then the sea went out.',
    accent: '#2a8ad8',
    cues: [[0.2, 'cc_bell', 0.5], [1.6, 'cc_siren', 0.5], [2.6, 'cc_wave', 0.9], [3.1, 'slam', 0.3]],
    shakes: [[3.1, 6, 0.4]],
    tagY: 650, tagAt: 3.4,
    setup: function (r) {
      var d = { houses: [], gulls: [] };
      var cols = ['#f2e6c8', '#e8a8a0', '#a8d0e8', '#f2d088', '#c8e0b0', '#f0c8d8'];
      for (var row = 0; row < 4; row++) {
        for (var i = 0; i < 9; i++) {
          d.houses.push({ x: 120 + i * 150 + row * 30 + between(r, -10, 10), y: 560 - row * 70, w: between(r, 70, 100),
                          h: between(r, 60, 90), c: cols[(i + row * 2) % cols.length] });
        }
      }
      for (var g = 0; g < 6; g++) d.gulls.push({ x: between(r, 0, VW), y: between(r, 80, 260), s: between(r, 30, 60) });
      return d;
    },
    draw: function (ctx, t, d) {
      var storm = seg(t, 1.6, 3.0);
      var sky = ctx.createLinearGradient(0, 0, 0, VH);
      sky.addColorStop(0, mix('#4a8ad8', '#3a4a5a', storm));
      sky.addColorStop(0.6, mix('#d8ecf8', '#8a9aa8', storm));
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      additive(ctx, function () { dot(ctx, '#fff4c8', 1300, 170, 160 * (1 - storm * 0.7), 0.6, 130); });
      // the terraces and the town on them
      for (var row = 3; row >= 0; row--) {
        ctx.fillStyle = ['#c8b898', '#bca888', '#b09a78', '#a48c6a'][row];
        ctx.fillRect(0, 560 - row * 70, VW, 70);
      }
      d.houses.forEach(function (h, i) { house(ctx, h.x, h.y, h.w, h.h, h.c, i % 2 ? '#c8503a' : '#3a6a9a', storm > 0.5); });
      // the lighthouse, its beam turning
      ctx.fillStyle = '#f4f0e8'; ctx.fillRect(1440, 260, 60, 300);
      ctx.fillStyle = '#d8402a'; ctx.fillRect(1440, 330, 60, 30); ctx.fillRect(1440, 420, 60, 30);
      ctx.fillStyle = '#3a3a3a'; ctx.fillRect(1430, 240, 80, 22);
      additive(ctx, function () {
        var a = t * 1.8;
        ctx.fillStyle = 'rgba(255,240,180,0.25)';
        ctx.beginPath(); ctx.moveTo(1470, 250);
        ctx.lineTo(1470 + Math.cos(a) * 900, 250 + Math.sin(a) * 120 - 60);
        ctx.lineTo(1470 + Math.cos(a + 0.12) * 900, 250 + Math.sin(a + 0.12) * 120 + 60); ctx.fill();
      });
      // the sea, drawing back, then the wave
      var back = seg(t, 0.8, 2.2) * 60;
      var wave = outCubic(seg(t, 2.3, 3.4));
      var seaTop = 640 + back - wave * 330;
      var sea = ctx.createLinearGradient(0, seaTop, 0, VH);
      sea.addColorStop(0, '#3a8ac8'); sea.addColorStop(1, '#1a4a7a');
      ctx.fillStyle = sea;
      ctx.beginPath(); ctx.moveTo(0, VH);
      for (var x = 0; x <= VW; x += 20) ctx.lineTo(x, seaTop + Math.sin(x * 0.012 + t * 3) * (8 + wave * 30));
      ctx.lineTo(VW, VH); ctx.fill();
      // foam on the crest
      ctx.fillStyle = 'rgba(255,255,255,0.85)';
      for (var f = 0; f < VW; f += 34) {
        var fy = seaTop + Math.sin(f * 0.012 + t * 3) * (8 + wave * 30);
        ctx.beginPath(); ctx.arc(f, fy, 10 + wave * 12 + Math.sin(f + t * 5) * 4, 0, TAU); ctx.fill();
      }
      d.gulls.forEach(function (g, i) {
        var gx = (g.x + t * g.s * (1 + storm * 3)) % (VW + 100) - 50;
        ctx.strokeStyle = '#2a2a2a'; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(gx - 12, g.y); ctx.quadraticCurveTo(gx - 6, g.y - 8 + Math.sin(t * 8 + i) * 4, gx, g.y);
        ctx.quadraticCurveTo(gx + 6, g.y - 8 + Math.sin(t * 8 + i) * 4, gx + 12, g.y); ctx.stroke();
      });
      // two lifeguards waving everyone up the hill
      person(ctx, 300, 560 - seg(t, 1.8, 3.0) * 70, 1.4, t, 0);
      person(ctx, 380, 560 - seg(t, 2.0, 3.0) * 70, 1.4, t, 2);
    },
    title: function (ctx, t, d, run) {
      if (t < 3.3) return;
      var name = (run.info.name || 'Port Sunny').toUpperCase();
      // a lifebuoy rolls in and the name rides on a harbour sign beneath it
      var k = outBack(seg(t, 3.3, 3.9), 1.4);
      ctx.save();
      ctx.translate(800, 300 - (1 - k) * 260);
      ctx.rotate(wobble(t, 3.9, 0.04, 8, 3));
      ctx.fillStyle = '#f4f0e8';
      ctx.fillRect(-520, -80, 1040, 160);
      ctx.strokeStyle = '#2a8ad8'; ctx.lineWidth = 10; ctx.strokeRect(-510, -70, 1020, 140);
      for (var s = 0; s < 4; s++) {
        ctx.fillStyle = s % 2 ? '#f4f0e8' : '#e8502a';
        ctx.beginPath(); ctx.arc(-560, 0, 70, s * TAU / 4, (s + 1) * TAU / 4); ctx.arc(-560, 0, 38, (s + 1) * TAU / 4, s * TAU / 4, true); ctx.fill();
      }
      ctx.globalAlpha = run.alpha * seg(t, 3.5, 3.9);
      nameText(ctx, name, 0, 4, 920, '#1a4a7a', 'rgba(0,0,0,0.18)');
      ctx.globalAlpha = run.alpha;
      ctx.restore();
    }
  });

  // ---------------------------------------------------- Summit Village
  Intro.register('cc_summit', {
    name: 'Summit Village',
    tagline: 'Fresh powder, a roaring fire, and the whole mountain about to move.',
    accent: '#8ad8ff',
    cues: [[0.4, 'cc_wind', 0.5], [2.0, 'cc_crack', 0.8], [2.4, 'cc_avalanche', 1], [3.2, 'cc_avalanche', 0.9],
           [3.6, 'slam', 0.3]],
    shakes: [[2.4, 4, 1.4], [3.6, 6, 0.4]],
    tagY: 660, tagAt: 3.9,
    setup: function (r) {
      var d = { flakes: [], pines: [] };
      for (var i = 0; i < 140; i++) d.flakes.push({ x: between(r, 0, VW), y: between(r, 0, VH), s: between(r, 2, 5), v: between(r, 30, 70) });
      for (var p = 0; p < 22; p++) d.pines.push({ x: between(r, 0, VW), y: between(r, 600, 760), s: between(r, 0.7, 1.3) });
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, VH);
      sky.addColorStop(0, '#5a8ac8'); sky.addColorStop(1, '#e8f0f8');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      // the peak
      ctx.fillStyle = '#8a96a8';
      ctx.beginPath(); ctx.moveTo(200, 720); ctx.lineTo(800, 120); ctx.lineTo(1400, 720); ctx.fill();
      ctx.fillStyle = '#f4f8ff';
      ctx.beginPath(); ctx.moveTo(620, 300); ctx.lineTo(800, 120); ctx.lineTo(980, 300);
      ctx.lineTo(900, 280); ctx.lineTo(840, 320); ctx.lineTo(760, 290); ctx.lineTo(700, 320); ctx.fill();
      // the avalanche pours down the face: a widening mass of snow with a
      // churning front and a powder cloud thrown up over it
      var k = seg(t, 2.2, 4.2);
      if (k > 0) {
        var fy = 230 + outCubic(k) * 500;
        var half = (fy - 120) * 0.82;
        ctx.fillStyle = '#ffffff';
        ctx.beginPath(); ctx.moveTo(800, 150); ctx.lineTo(800 + half, fy); ctx.lineTo(800 - half, fy); ctx.fill();
        for (var b = -8; b <= 8; b++) {
          ctx.beginPath();
          ctx.arc(800 + b * half / 8.5, fy + Math.sin(b * 1.7 + t * 6) * 6, 22 + ((b + 9) % 3) * 6, 0, TAU);
          ctx.fill();
        }
        ctx.fillStyle = 'rgba(255,255,255,0.45)';
        for (var c = -6; c <= 6; c++) {
          ctx.beginPath();
          ctx.arc(800 + c * half / 6.5, fy - 50 - Math.abs(c) * 6 + Math.sin(t * 3 + c) * 10, 46 + ((c + 7) % 3) * 14, 0, TAU);
          ctx.fill();
        }
        ctx.fillStyle = 'rgba(255,255,255,' + (0.3 * k) + ')'; ctx.fillRect(0, 0, VW, VH);
      }
      // the village: a lodge with a lit chimney, chalets
      ctx.fillStyle = '#e8f0f8'; ctx.fillRect(0, 720, VW, VH - 720);
      house(ctx, 230, 760, 180, 110, '#8a5a3a', '#4a3a3a', true);
      house(ctx, 1150, 760, 150, 90, '#a87a4a', '#5a3a2a', true);
      house(ctx, 1340, 770, 120, 80, '#9a6a3a', '#4a3a3a', false);
      ctx.fillStyle = '#6a5a4a'; ctx.fillRect(360, 560, 30, 80);
      for (var s = 0; s < 5; s++) {
        ctx.fillStyle = 'rgba(200,200,210,' + (0.5 - s * 0.08) + ')';
        ctx.beginPath(); ctx.arc(375 + Math.sin(t + s) * 10 + s * 8, 540 - s * 30 - (t * 20) % 30, 14 + s * 4, 0, TAU); ctx.fill();
      }
      d.pines.forEach(function (p) {
        ctx.fillStyle = '#24502e';
        ctx.beginPath(); ctx.moveTo(p.x, p.y - 90 * p.s); ctx.lineTo(p.x - 30 * p.s, p.y); ctx.lineTo(p.x + 30 * p.s, p.y); ctx.fill();
        ctx.fillStyle = '#ffffff';
        ctx.beginPath(); ctx.moveTo(p.x, p.y - 90 * p.s); ctx.lineTo(p.x - 12 * p.s, p.y - 55 * p.s); ctx.lineTo(p.x + 12 * p.s, p.y - 55 * p.s); ctx.fill();
      });
      // the cable car on its wire
      ctx.strokeStyle = '#3a3a3a'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(1500, 720); ctx.lineTo(880, 220); ctx.stroke();
      var c = seg(t, 0, 5) * 0.6 + 0.2;
      var cx = lerp(1500, 880, c), cy = lerp(720, 220, c);
      ctx.fillStyle = '#d8402a'; ctx.fillRect(cx - 30, cy + 16, 60, 44);
      ctx.fillStyle = '#cfe8ff'; ctx.fillRect(cx - 22, cy + 24, 44, 16);
      ctx.strokeStyle = '#3a3a3a'; ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx, cy + 16); ctx.stroke();
      person(ctx, 520, 760, 1.3, t, 1);
      d.flakes.forEach(function (f) {
        var y = (f.y + t * f.v) % VH, x = (f.x + Math.sin(t + f.y) * 20 + t * 30) % VW;
        ctx.fillStyle = 'rgba(255,255,255,0.9)';
        ctx.beginPath(); ctx.arc(x, y, f.s, 0, TAU); ctx.fill();
      });
    },
    title: function (ctx, t, d, run) {
      if (t < 3.6) return;
      var name = (run.info.name || 'Summit Village').toUpperCase();
      // a carved lodge board swings down on two chains, with snow on top
      var k = outBack(seg(t, 3.6, 4.2), 1.3);
      ctx.save();
      ctx.translate(800, 280);
      ctx.rotate(wobble(t, 4.2, 0.06, 6, 2.2));
      ctx.strokeStyle = '#5a5a5a'; ctx.lineWidth = 6;
      ctx.beginPath(); ctx.moveTo(-380, -300); ctx.lineTo(-380, -80 * k - 220 * (1 - k)); ctx.moveTo(380, -300);
      ctx.lineTo(380, -80 * k - 220 * (1 - k)); ctx.stroke();
      ctx.translate(0, -220 * (1 - k));
      ctx.fillStyle = '#6a4024'; ctx.fillRect(-500, -80, 1000, 160);
      ctx.fillStyle = '#7e5030'; for (var p = 0; p < 4; p++) ctx.fillRect(-500, -80 + p * 40, 1000, 18);
      ctx.fillStyle = '#ffffff';
      ctx.beginPath(); ctx.moveTo(-510, -80);
      for (var x = -510; x <= 510; x += 40) ctx.quadraticCurveTo(x + 20, -104 - Math.sin(x) * 6, x + 40, -80);
      ctx.fill();
      ctx.globalAlpha = run.alpha * seg(t, 3.9, 4.3);
      nameText(ctx, name, 0, 6, 900, '#f4e8c8', 'rgba(0,0,0,0.45)', 'Georgia, serif');
      ctx.globalAlpha = run.alpha;
      ctx.restore();
    }
  });

  // ---------------------------------------------------------- Palm Key
  Intro.register('cc_palmkey', {
    name: 'Palm Key',
    tagline: 'Five-star resort. Four-star volcano. It is waking up.',
    accent: '#ff8a2a',
    cues: [[0.3, 'cc_wave', 0.3], [1.8, 'cc_rumble', 0.8], [2.5, 'cc_boom', 1], [2.8, 'cc_boom', 0.7],
           [3.3, 'slam', 0.3]],
    shakes: [[1.8, 3, 0.8], [2.5, 7, 0.6]],
    tagY: 650, tagAt: 3.5,
    setup: function (r) {
      var d = { bombs: [], palms: [] };
      for (var i = 0; i < 18; i++) d.bombs.push({ a: between(r, -1.2, 1.2), v: between(r, 380, 620), t0: 2.5 + between(r, 0, 1.2) });
      for (var p = 0; p < 7; p++) d.palms.push({ x: 80 + p * 230 + between(r, -30, 30), h: between(r, 180, 260), lean: between(r, -0.3, 0.3) });
      return d;
    },
    draw: function (ctx, t, d) {
      var erupt = seg(t, 2.4, 3.2);
      var sky = ctx.createLinearGradient(0, 0, 0, VH);
      sky.addColorStop(0, mix('#3a8ae0', '#5a2a1a', erupt));
      sky.addColorStop(0.7, mix('#f0e8c8', '#e0803a', erupt));
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      // the volcano, smoking, then lit
      ctx.fillStyle = '#5a4a3a';
      ctx.beginPath(); ctx.moveTo(700, 640); ctx.lineTo(1040, 230); ctx.lineTo(1160, 230); ctx.lineTo(1500, 640); ctx.fill();
      ctx.fillStyle = '#3a8a3a';
      ctx.beginPath(); ctx.moveTo(700, 640); ctx.lineTo(860, 450); ctx.lineTo(1340, 450); ctx.lineTo(1500, 640); ctx.fill();
      for (var s = 0; s < 8; s++) {
        var sy = 210 - s * 40 - (t * 30) % 40;
        ctx.fillStyle = 'rgba(' + (erupt > 0 ? '60,50,50' : '200,200,200') + ',' + (0.55 - s * 0.06) + ')';
        ctx.beginPath(); ctx.arc(1100 + Math.sin(t + s) * 20 + s * 12, sy, 30 + s * 12 + erupt * 30, 0, TAU); ctx.fill();
      }
      if (erupt > 0) {
        additive(ctx, function () { dot(ctx, '#ff6a1a', 1100, 240, 160 * erupt, 0.8, 120); });
        ctx.fillStyle = '#ff6a1a';
        ctx.beginPath(); ctx.moveTo(1060, 232); ctx.lineTo(1140, 232);
        ctx.lineTo(1150 + erupt * 140, 232 + erupt * 300); ctx.lineTo(1030 - erupt * 120, 232 + erupt * 300); ctx.fill();
        d.bombs.forEach(function (b) {
          var k = t - b.t0;
          if (k < 0 || k > 1.6) return;
          var x = 1100 + Math.sin(b.a) * b.v * k, y = 230 - Math.cos(b.a) * b.v * k + 420 * k * k;
          ctx.fillStyle = '#ffb43a'; ctx.beginPath(); ctx.arc(x, y, 9, 0, TAU); ctx.fill();
          ctx.fillStyle = 'rgba(90,80,80,0.5)'; ctx.beginPath(); ctx.arc(x - Math.sin(b.a) * 16, y + 14, 8, 0, TAU); ctx.fill();
        });
      }
      // the lagoon and the beach, the hotel and the bungalows
      ctx.fillStyle = '#3ac0d8'; ctx.fillRect(0, 640, VW, 120);
      ctx.fillStyle = '#f2e0a8'; ctx.fillRect(0, 740, VW, VH - 740);
      ctx.fillStyle = '#f2f0ea'; ctx.fillRect(220, 420, 260, 240);
      for (var w = 0; w < 5; w++) for (var c = 0; c < 4; c++) {
        ctx.fillStyle = erupt > 0.5 ? '#ffd88a' : '#8ac8e8'; ctx.fillRect(240 + c * 60, 440 + w * 42, 36, 26);
      }
      [560, 640, 1520].forEach(function (bx) {
        ctx.fillStyle = '#8a6a44'; ctx.fillRect(bx, 650, 8, 60); ctx.fillRect(bx + 52, 650, 8, 60);
        ctx.fillStyle = '#c8a070'; ctx.fillRect(bx - 6, 610, 72, 44);
        ctx.fillStyle = '#d8b060'; ctx.beginPath(); ctx.moveTo(bx - 14, 612); ctx.lineTo(bx + 30, 580); ctx.lineTo(bx + 74, 612); ctx.fill();
      });
      d.palms.forEach(function (p, i) {
        var sway = Math.sin(t * 1.6 + i) * 0.06 + p.lean;
        ctx.save(); ctx.translate(p.x, 800);
        ctx.rotate(sway);
        ctx.fillStyle = '#8a6a44'; ctx.fillRect(-7, -p.h, 14, p.h);
        ctx.fillStyle = '#2a8a3a';
        for (var l = 0; l < 6; l++) {
          ctx.save(); ctx.translate(0, -p.h); ctx.rotate(l * TAU / 6 + Math.sin(t * 2 + l) * 0.1);
          ctx.beginPath(); ctx.ellipse(46, 0, 50, 12, 0.3, 0, TAU); ctx.fill(); ctx.restore();
        }
        ctx.restore();
      });
      person(ctx, 900, 760, 1.3, t, 0);
    },
    title: function (ctx, t, d, run) {
      if (t < 3.3) return;
      var name = (run.info.name || 'Palm Key').toUpperCase();
      // a surfboard sign drops into the sand and wobbles
      var k = outBack(seg(t, 3.3, 3.8), 1.6);
      ctx.save();
      ctx.translate(800, 300 - (1 - k) * 400);
      ctx.rotate(-0.03 + wobble(t, 3.8, 0.05, 9, 3));
      ctx.fillStyle = '#ff8a2a';
      ctx.beginPath(); ctx.ellipse(0, 0, 540, 100, 0, 0, TAU); ctx.fill();
      ctx.fillStyle = '#f4f0e8';
      ctx.beginPath(); ctx.ellipse(0, 0, 520, 84, 0, 0, TAU); ctx.fill();
      ctx.fillStyle = '#3ac0d8'; ctx.fillRect(-520, -6, 1040, 12);
      ctx.globalAlpha = run.alpha * seg(t, 3.5, 3.9);
      nameText(ctx, name, 0, 4, 820, '#c8401a', 'rgba(0,0,0,0.2)');
      ctx.globalAlpha = run.alpha;
      ctx.restore();
    }
  });

  // ---------------------------------------------------------- Old Town
  Intro.register('cc_oldtown', {
    name: 'Old Town',
    tagline: 'Eight hundred years of timber, thatch and very good luck.',
    accent: '#ffb43a',
    cues: [[0.2, 'cc_bell', 0.6], [1.1, 'cc_bell', 0.5], [2.1, 'cc_rumble', 1], [2.6, 'cc_crash', 0.9],
           [3.3, 'cc_fire', 0.8], [3.6, 'slam', 0.3]],
    shakes: [[2.1, 7, 1.2], [3.6, 5, 0.3]],
    tagY: 660, tagAt: 3.8,
    setup: function (r) {
      var d = { houses: [], bricks: [], embers: [] };
      var walls = ['#e8dcc0', '#d8c8a8', '#f0e4c8', '#c8b898'];
      for (var i = 0; i < 10; i++) d.houses.push({ x: 40 + i * 155, w: between(r, 110, 140), h: between(r, 120, 180), c: walls[i % 4] });
      for (var b = 0; b < 16; b++) d.bricks.push({ x: between(r, 100, 1500), v: between(r, -60, 60), t0: 2.4 + between(r, 0, 0.8) });
      for (var e = 0; e < 40; e++) d.embers.push({ x: between(r, 0, VW), s: between(r, 40, 90), p: between(r, 0, 6) });
      return d;
    },
    draw: function (ctx, t, d) {
      var fire = seg(t, 3.0, 4.2);
      var sky = ctx.createLinearGradient(0, 0, 0, VH);
      sky.addColorStop(0, mix('#4a5a88', '#3a1a14', fire));
      sky.addColorStop(0.7, mix('#e8b888', '#ff8a3a', fire));
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      var sx = (t > 2.1 && t < 3.3) ? Math.sin(t * 60) * 6 : 0;
      ctx.save(); ctx.translate(sx, 0);
      // the castle on its hill, the cathedral
      ctx.fillStyle = '#5a6a4a';
      ctx.beginPath(); ctx.ellipse(260, 520, 320, 160, 0, Math.PI, TAU); ctx.fill();
      ctx.fillStyle = '#8a8478';
      ctx.fillRect(140, 300, 240, 120); ctx.fillRect(220, 220, 80, 100);
      for (var c = 0; c < 7; c++) ctx.fillRect(140 + c * 36, 286, 22, 16);
      ctx.fillStyle = '#d8ccb4'; ctx.fillRect(980, 260, 260, 260);
      ctx.fillStyle = '#4a4a5a';
      ctx.beginPath(); ctx.moveTo(960, 262); ctx.lineTo(1110, 170); ctx.lineTo(1260, 262); ctx.fill();
      ctx.fillStyle = '#c8bca4'; ctx.fillRect(1260, 140, 70, 380);
      ctx.fillStyle = '#4a4a5a';
      ctx.beginPath(); ctx.moveTo(1250, 142); ctx.lineTo(1295, 40); ctx.lineTo(1340, 142); ctx.fill();
      ctx.fillStyle = '#ffd88a'; ctx.beginPath(); ctx.arc(1110, 340, 40, 0, TAU); ctx.fill();
      // the row of timbered houses along the river
      d.houses.forEach(function (h, i) {
        var y = 700;
        ctx.fillStyle = h.c; ctx.fillRect(h.x, y - h.h, h.w, h.h);
        ctx.strokeStyle = '#5a3a24'; ctx.lineWidth = 6;
        ctx.strokeRect(h.x, y - h.h, h.w, h.h);
        ctx.beginPath(); ctx.moveTo(h.x, y - h.h); ctx.lineTo(h.x + h.w, y - h.h / 2); ctx.moveTo(h.x + h.w, y - h.h);
        ctx.lineTo(h.x, y - h.h / 2); ctx.stroke();
        ctx.fillStyle = '#7a3a2a';
        ctx.beginPath(); ctx.moveTo(h.x - 10, y - h.h); ctx.lineTo(h.x + h.w / 2, y - h.h - 70); ctx.lineTo(h.x + h.w + 10, y - h.h); ctx.fill();
        if (fire > 0 && (i === 3 || i === 4 || (i === 6 && fire > 0.5) || (i === 2 && fire > 0.7))) {
          additive(ctx, function () { dot(ctx, '#ff7a1a', h.x + h.w / 2, y - h.h - 40, 90 * fire, 0.8, 90); });
          for (var f = 0; f < 6; f++) {
            var fh = 50 + Math.sin(t * 12 + f + i) * 20;
            ctx.fillStyle = f % 2 ? '#ffd23a' : '#ff6a1a';
            ctx.beginPath(); ctx.moveTo(h.x + f * h.w / 6, y - h.h); ctx.lineTo(h.x + f * h.w / 6 + h.w / 12, y - h.h - fh * fire);
            ctx.lineTo(h.x + (f + 1) * h.w / 6, y - h.h); ctx.fill();
          }
        }
      });
      // the river
      ctx.fillStyle = '#3a6a8a'; ctx.fillRect(0, 700, VW, 90);
      ctx.fillStyle = '#a89a88'; ctx.fillRect(0, 790, VW, VH - 790);
      // the bridge
      ctx.fillStyle = '#a89a88';
      ctx.beginPath(); ctx.moveTo(620, 720); ctx.quadraticCurveTo(800, 640, 980, 720); ctx.lineTo(980, 740);
      ctx.quadraticCurveTo(800, 670, 620, 740); ctx.fill();
      // bricks shaken off the chimneys
      d.bricks.forEach(function (b) {
        var k = t - b.t0;
        if (k < 0 || k > 1.2) return;
        ctx.fillStyle = '#9a4f3a';
        ctx.save(); ctx.translate(b.x + b.v * k, 520 + 500 * k * k); ctx.rotate(k * 8); ctx.fillRect(-9, -5, 18, 10); ctx.restore();
      });
      ctx.restore();
      if (fire > 0) {
        d.embers.forEach(function (e) {
          var y = VH - ((t * e.s * 2 + e.p * 100) % VH);
          ctx.fillStyle = 'rgba(255,' + Math.round(140 + Math.sin(t * 9 + e.p) * 60) + ',40,' + (0.8 * fire) + ')';
          ctx.fillRect(e.x + Math.sin(t * 2 + e.p) * 20, y, 4, 4);
        });
      }
      person(ctx, 760, 690, 1.2, t, 0);
      person(ctx, 840, 690, 1.2, t, 3);
    },
    title: function (ctx, t, d, run) {
      if (t < 3.7) return;
      var name = (run.info.name || 'Old Town').toUpperCase();
      // a wrought-iron shop sign on a bracket, swinging in
      var k = outCubic(seg(t, 3.7, 4.3));
      ctx.save();
      ctx.translate(800, 220);
      ctx.fillStyle = '#2a2a2a'; ctx.fillRect(-560, -150, 1120 * k, 14);
      ctx.rotate(wobble(t, 4.3, 0.08, 5, 1.6) + (1 - k) * -1.2);
      ctx.strokeStyle = '#2a2a2a'; ctx.lineWidth = 5;
      ctx.beginPath(); ctx.moveTo(-420, -140); ctx.lineTo(-420, -70); ctx.moveTo(420, -140); ctx.lineTo(420, -70); ctx.stroke();
      ctx.fillStyle = '#2a2420'; ctx.fillRect(-520, -72, 1040, 170);
      ctx.fillStyle = '#5a3a24'; ctx.fillRect(-506, -58, 1012, 142);
      ctx.strokeStyle = '#d8b040'; ctx.lineWidth = 4; ctx.strokeRect(-490, -44, 980, 114);
      ctx.globalAlpha = run.alpha * seg(t, 4.0, 4.4);
      nameText(ctx, name, 0, 14, 880, '#f2d890', 'rgba(0,0,0,0.5)', 'Georgia, serif');
      ctx.globalAlpha = run.alpha;
      ctx.restore();
    }
  });
})(window);
