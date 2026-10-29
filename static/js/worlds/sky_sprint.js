/* Sky Sprint -- the Game View half of the obstacle-course race
   (app/game/worlds/sky_sprint.py).

   The server keeps the score, the checkpoints and the power-ups; this
   moves your own body the way the course moves everybody's: the jump pads
   and the jelly throw you up, the belts carry you, the speed strips fling
   you, the wind leans on you on the bridges, and the hammers and the
   sweepers knock you flying (a laser sends you back to your checkpoint --
   that one is the server's to do, told by a message).  Bots are moved by
   the same rules on the server, from the same four clocks it sends here
   many times a second, so the hammer you see swing is the one that hits
   them.

   It draws whatever moves: the sweepers in each place's style (steel
   girders, candy canes with a lollipop on the end, neon bars, bamboo with a
   lantern), the hammers, the laser beams, the belts' stripes, the jelly's
   wobble, a warning flash on a tile about to blink out and its ghost while
   it is gone, the power-ups turning on their spots, the gusts across a
   bridge, and a beam on your next checkpoint.

   Each place's twist: the Foundry's belts run backwards (and its hammers
   swing faster), Candy Clouds' sugar rush, Neon Grid's drop (the beat
   doubles) and the Jade Temple's typhoon.

   Four arrival scenes are registered at the bottom. */
(function (global) {
  'use strict';
  var Arena = global.Arena || { register: function () {} };

  var TEAM = { red: '#e8463a', blue: '#3a8ae8' };
  var TEAM_LIGHT = { red: '#ff8a7a', blue: '#8ac4ff' };
  var POWERS = {
    spring: { name: 'SPRING SHOES', colour: '#7aea5a', line: 'You jump higher' },
    rocket: { name: 'A ROCKET', colour: '#ff8a3a', line: 'Press E to blast off' },
    feather: { name: 'A FEATHER', colour: '#f4f0ff', line: 'You fall slowly' },
    shield: { name: 'A BUBBLE', colour: '#8ad8ff', line: 'Nothing can knock you about' }
  };
  var TWISTS = {
    reverse: { warn: 'THE BELTS ARE GRINDING', warnSub: 'Everything is about to run backwards...',
               on: 'REVERSE!', onSub: 'The belts run backwards and the hammers swing faster',
               off: 'The belts run true again', colour: '#ffb35a', chip: 'REVERSED' },
    sugar_rush: { warn: 'SUGAR INCOMING', warnSub: 'The candy is kicking in...',
                  on: 'SUGAR RUSH!', onSub: 'Everybody runs faster and jumps higher',
                  off: 'The sugar wears off', colour: '#ff7ac8', chip: 'SUGAR RUSH' },
    drop: { warn: 'THE BEAT IS BUILDING', warnSub: 'Wait for the drop...',
            on: 'THE DROP!', onSub: 'The tiles blink twice as fast and the lasers sweep faster',
            off: 'The beat settles down', colour: '#3ad8ff', chip: 'THE DROP' },
    typhoon: { warn: 'THE WIND IS RISING', warnSub: 'Hold on to something...',
               on: 'TYPHOON!', onSub: 'A gale blows across every bridge without a break',
               off: 'The typhoon passes', colour: '#9ae8c8', chip: 'TYPHOON' }
  };
  // keep these in step with app/game/worlds/sky_sprint.py
  var SPRING_SCALE = 1.3, SUGAR_JUMP = 1.15, SUGAR_SPEED = 1.3, BOOST_SCALE = 2.2;
  var FEATHER_GRAVITY = 0.42;
  var SWEEP_KNOCK = 32, HAMMER_KNOCK = 40, KNOCK_UP = 16, KNOCK_FOR = 0.55, HIT_COOL = 0.7;
  var WIND_MAX = 16;          // the most a gust carries a person, who steers against it
  var CRUMBLE_AFTER = 0.6, CRUMBLE_BACK = 2.6;
  var HEIGHT = 5.4;

  function rgb(hex) {
    var n = parseInt(String(hex).slice(1), 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
  }
  function esc(text) {
    return String(text == null ? '' : text).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function now() { return performance.now() / 1000; }
  function hash(n) { var x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }
  function ordinal(n) {
    var s = ['th', 'st', 'nd', 'rd'], v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
  }
  function inRect(rect, p, pad) {
    pad = pad || 0;
    return rect[0] - pad <= p[0] && p[0] <= rect[1] + pad && rect[2] - pad <= p[2] && p[2] <= rect[3] + pad;
  }

  // ======================================================== the motion
  // The same formulas as app/game/worlds/sky_sprint.py: keep them in step.
  function hammerAngle(h, t) {
    var a = 2 * Math.PI / h.period * t + h.ph;
    return [h.amp * Math.sin(a), Math.cos(a) >= 0 ? 1 : -1];
  }
  function hammerHead(h, t) {
    var ang = hammerAngle(h, t);
    var s = Math.sin(ang[0]) * h.len, c = Math.cos(ang[0]) * h.len;
    var p = h.pivot;
    return { p: h.axis === 'x' ? [p[0] + s, p[1] - c, p[2]] : [p[0], p[1] - c, p[2] + s],
             theta: ang[0], going: ang[1] };
  }
  function hammerHit(h, t, pos) {
    var head = hammerHead(h, t), hp = head.p;
    var sx = h.head[0], sy = h.head[1], sz = h.head[2];
    if (Math.abs(pos[0] - hp[0]) > sx / 2 + 1.2 || Math.abs(pos[2] - hp[2]) > sz / 2 + 0.9) return null;
    if (pos[1] > hp[1] + sy / 2 || pos[1] + HEIGHT < hp[1] - sy / 2) return null;
    return h.axis === 'x' ? [head.going, 0] : [0, head.going];
  }
  function sweeperHit(sw, t, pos) {
    var c = sw.c, bar = c[1] + sw.h, half = sw.t / 2;
    if (pos[1] > bar + half || pos[1] + HEIGHT < bar - half) return null;
    var dx = pos[0] - c[0], dz = pos[2] - c[2];
    if (Math.hypot(dx, dz) > sw.r + 1.4) return null;
    var turn = sw.ph + sw.w * t, sign = sw.w >= 0 ? 1 : -1;
    for (var k = 0; k < sw.arms; k++) {
      var a = turn + k * 2 * Math.PI / sw.arms;
      var ux = Math.cos(a), uz = Math.sin(a);
      var along = dx * ux + dz * uz;
      if (along < -1.2 || along > sw.r + 1.2) continue;
      if (Math.abs(-dx * uz + dz * ux) < half + 1.3) return [-uz * sign, ux * sign];
    }
    return null;
  }
  function laserBeam(lz, t) {
    var k = Math.sin(2 * Math.PI * t / lz.period + lz.ph);
    return [[lz.a[0] + lz.move[0] * k, lz.a[1] + lz.move[1] * k, lz.a[2] + lz.move[2] * k],
            [lz.b[0] + lz.move[0] * k, lz.b[1] + lz.move[1] * k, lz.b[2] + lz.move[2] * k]];
  }
  function laserHit(lz, t, pos) {
    var ab = laserBeam(lz, t), a = ab[0], b = ab[1];
    if (!(pos[1] - 0.2 < a[1] && a[1] < pos[1] + HEIGHT)) return false;
    var vx = b[0] - a[0], vz = b[2] - a[2], l2 = vx * vx + vz * vz;
    var f = l2 < 1e-6 ? 0 : Math.max(0, Math.min(1, ((pos[0] - a[0]) * vx + (pos[2] - a[2]) * vz) / l2));
    return Math.hypot(pos[0] - (a[0] + vx * f), pos[2] - (a[2] + vz * f)) < 1.3;
  }
  function blinkPhase(spec, beat) {
    var x = (beat + spec.ph) % spec.period;
    if (x < 0) x += spec.period;
    return x / spec.period;
  }
  function windNow(spec, t) {
    var k = Math.sin(2 * Math.PI * t / spec.period + spec.ph);
    return Math.max(0, (k - 0.25) / 0.75);
  }

  Arena.register('sky_sprint', function (arena) {
    var client = arena.client;
    var ss = {};                  // the race's state (pts, cps, done, racers, hurry, twist...)
    var ax = {};                  // the snapshot extra: clocks, progress, power spots
    var ex = {}, pts = {};
    var cps = [], pads = [], boosts = [], spots = [];
    var clk = { have: false, at: 0, ht: 0, hc: 0, lc: 0, bt: 0, rate: [1, 1, 1, 1] };
    var loc = { ht: 0, hc: 0, lc: 0, bt: 0 };
    var twist = { kind: '', on: false };
    var beltOff = [];
    var boostUntil = 0, carry = null, hitAt = -9, zapAt = -9, padAt = -9, shakeUntil = 0;
    var pw = {};                  // kind -> when it runs out
    var hurryUntil = 0;
    var wobbles = {};             // jelly pad index -> when it was bounced
    var creaks = {};              // crumble key -> when it began to creak
    var fellAt = {};              // crumble key -> when it went
    var flames = {};              // player id -> rockets burning until
    var lastRole = '', lastSide = '', sideAt = 0;
    var veil = null;

    function myPos() { return client.local.pos; }
    function inPlay() { return arena.phase === 'active' && !arena.me.out && client.local.alive; }
    function done() { return !!(arena.me.place || 0); }
    function twistOn(kind) { return twist.on && twist.kind === kind; }
    function has(kind) { return (pw[kind] || 0) > now(); }
    function playerPos(id) {
      if (id === client.myId) return myPos();
      var p = client.players[id];
      return p && p.pos ? p.pos : null;
    }
    function playAt(name, pos, vol) {
      var me = myPos();
      var d = pos ? Math.hypot(pos[0] - me[0], pos[1] - me[1], pos[2] - me[2]) : 0;
      var k = Math.max(0, 1 - d / 90);
      if (k > 0.04) client.audio.play(name, { volume: (vol || 1) * k });
    }
    function nameOf(id) {
      if (id === client.myId) return 'You';
      var p = client.players[id];
      return p ? p.name : 'Somebody';
    }

    // ---------------------------------------------------------- the map
    function loadMap(map) {
      var mk = (map && map.markers) || {};
      ex = mk.extra || {};
      pts = mk.points || {};
      cps = (pts.cp || []).slice().sort(function (a, b) { return a.i - b.i; });
      pads = pts.pad || [];
      boosts = pts.boost || [];
      spots = pts.power || [];
      beltOff = (ex.belts || []).map(function () { return 0; });
      reset();
    }

    function reset() {
      ax = {};
      clk.have = false;
      boostUntil = 0; carry = null; hitAt = -9; zapAt = -9; padAt = -9; shakeUntil = 0;
      pw = {}; hurryUntil = 0; wobbles = {}; creaks = {}; fellAt = {}; flames = {};
      twist = { kind: ex.twist || '', on: false };
      lastRole = ''; lastSide = '';
      arena.side('');
      setVeil(0, '');
    }

    function applyState(s) {
      if (!s) return;
      ss = s;
      twist.kind = s.twist || twist.kind;
      twist.on = !!s.on;
      if (s.hurry) hurryUntil = now() + s.hurry;
      roleChip();
    }

    // ---------------------------------------------------------- clocks
    /* The server's four clocks, carried forward from the last snapshot (and
       half a ping on, to where they are now), then eased into so nothing
       on the course ever jumps. */
    function takeClocks() {
      if (ax.ht === undefined) return;
      clk.at = now();
      clk.ht = ax.ht; clk.hc = ax.hc === undefined ? ax.ht : ax.hc;
      clk.lc = ax.lc === undefined ? ax.ht : ax.lc; clk.bt = ax.bt || 0;
      clk.rate = ax.rate || [1, 1, 1, 1];
      if (!clk.have) {
        clk.have = true;
        loc.ht = clk.ht; loc.hc = clk.hc; loc.lc = clk.lc; loc.bt = clk.bt;
      }
    }
    function stepClocks(dt) {
      var r = clk.rate;
      var rates = { ht: 1, hc: r[0] || 1, lc: r[2] || 1, bt: r[1] || 1 };
      var lead = (now() - clk.at) + ((client.net && client.net.ping) || 0) / 2000;
      for (var key in rates) {
        loc[key] += dt * rates[key];
        if (!clk.have) continue;
        var target = clk[key] + Math.min(lead, 1.5) * rates[key];
        var err = target - loc[key];
        if (Math.abs(err) > 0.4) loc[key] = target;
        else loc[key] += err * Math.min(1, dt * 4);
      }
    }

    // ------------------------------------------------- your own body
    function moveScale() {
      var s = 1, t = now(), me = myPos();
      if (boostUntil > t) s *= BOOST_SCALE;
      if (twistOn('sugar_rush')) s *= SUGAR_SPEED;
      (ex.taffy || []).forEach(function (z) {
        if (inRect(z.rect, me) && Math.abs(me[1] - z.y) < 0.8) s *= z.scale || 0.55;
      });
      return s;
    }
    function jumpScale() {
      return (has('spring') ? SPRING_SCALE : 1) * (twistOn('sugar_rush') ? SUGAR_JUMP : 1);
    }
    function gravityScale() {
      return has('feather') && client.local.vel[1] < 0 ? FEATHER_GRAVITY : 1;
    }

    function knock(local, vx, vy, vz, t) {
      local.vel[1] = Math.max(local.vel[1], vy);
      carry = { v: [vx, vz], until: t + KNOCK_FOR };
      hitAt = t;
      shakeUntil = t + 0.35;
      arena.send('hit');
    }

    /* After the client's own step: the course's part in moving you. */
    function afterStep(local, result, dt) {
      if (!inPlay()) { carry = null; return; }
      var t = now(), pos = local.pos;
      var mx = 0, mz = 0;
      if (result.grounded) {
        for (var i = 0; i < pads.length; i++) {
          var pad = pads[i];
          if (Math.hypot(pos[0] - pad.p[0], pos[2] - pad.p[2]) < pad.r && Math.abs(pos[1] - pad.p[1]) < 0.7) {
            local.vel[1] = pad.v;
            if (pad.f) carry = { v: [Math.sin(pad.yaw) * pad.f, Math.cos(pad.yaw) * pad.f], until: t + 1.5 };
            result.grounded = false;
            if (t - padAt > 0.3) {
              padAt = t;
              arena.send('pad');
              bounced(i, pad);
            }
            break;
          }
        }
        for (var b = 0; b < boosts.length; b++) {
          var boost = boosts[b];
          var d = Math.hypot(pos[0] - boost.p[0], pos[1] - boost.p[1], pos[2] - boost.p[2]);
          if (d < boost.l / 2 + 0.5) {
            if (boostUntil < t) client.audio.play('ss_whoosh', { volume: 0.7 });
            boostUntil = t + 0.9;
          }
        }
        var sign = twistOn('reverse') ? -1 : 1;
        (ex.belts || []).forEach(function (belt) {
          if (inRect(belt.rect, pos) && Math.abs(pos[1] - belt.y) < 0.5) {
            mx += belt.v[0] * sign;
            mz += belt.v[1] * sign;
          }
        });
        (ex.jelly || []).forEach(function (zone) {
          if (inRect(zone.rect, pos) && Math.abs(pos[1] - zone.y) < 0.6) {
            local.vel[1] = zone.v || 46;
            result.grounded = false;
          }
        });
      }
      // the wind on the bridges
      var w = windAt(pos);
      if (w) {
        var m = Math.hypot(w[0], w[1]);
        var cap = m > WIND_MAX ? WIND_MAX / m : 1;
        mx += w[0] * cap;
        mz += w[1] * cap;
      }
      if (carry && carry.until > t) { mx += carry.v[0]; mz += carry.v[1]; }
      else carry = null;
      if ((mx || mz) && client.physics) {
        client.physics.move({ pos: local.pos, vel: [mx, 0, mz], size: local.size }, dt);
      }
      // what swings, sweeps and burns
      if (has('shield') || t < hitAt + HIT_COOL) return;
      var hammers = ex.hammers || [];
      for (var h = 0; h < hammers.length; h++) {
        var hit = hammerHit(hammers[h], loc.hc, pos);
        if (hit) {
          knock(local, hit[0] * HAMMER_KNOCK, KNOCK_UP, hit[1] * HAMMER_KNOCK, t);
          result.grounded = false;
          client.audio.play('ss_thwack', { volume: 0.9 });
          return;
        }
      }
      var sweepers = ex.sweepers || [];
      for (var s = 0; s < sweepers.length; s++) {
        var hit2 = sweeperHit(sweepers[s], loc.ht, pos);
        if (hit2) {
          knock(local, hit2[0] * SWEEP_KNOCK, KNOCK_UP, hit2[1] * SWEEP_KNOCK, t);
          result.grounded = false;
          client.audio.play('ss_thwack', { volume: 0.75 });
          return;
        }
      }
      var lasers = ex.lasers || [];
      for (var l = 0; l < lasers.length; l++) {
        if (laserHit(lasers[l], loc.lc, pos) && t - zapAt > 1.2) {
          zapAt = t;
          arena.send('zap');
          return;
        }
      }
    }

    function windAt(pos) {
      var zones = ex.wind || [];
      if (!zones.length) return null;
      var rate = (clk.rate && clk.rate[3]) || 1;
      var wx = 0, wz = 0;
      zones.forEach(function (z) {
        if (!inRect(z.rect, pos) || !(pos[1] - z.y > -1 && pos[1] - z.y < 14)) return;
        var k = twistOn('typhoon') ? 1 : windNow(z, loc.ht);
        wx += z.dir[0] * z.strength * k * rate;
        wz += z.dir[1] * z.strength * k * rate;
      });
      return (wx || wz) ? [wx, wz] : null;
    }

    function bounced(index, pad) {
      if (pad.jelly) {
        wobbles[index] = now();
        playAt('ss_jelly', pad.p, 0.9);
      } else {
        playAt('ss_boing', pad.p, 0.9);
      }
      if (client.particles) client.particles.burst('dust', [pad.p[0], pad.p[1] + 0.3, pad.p[2]]);
    }

    // ---------------------------------------------------------- drawing
    function put(r, kind, x, y, z, rx, ry, rz, sx, sy, sz, colour, alpha, material, emissive) {
      r.pushRaw(kind, x, y, z, rx || 0, ry || 0, rz || 0, sx, sy, sz, typeof colour === 'string' ? rgb(colour) : colour,
                alpha === undefined ? 1 : alpha, 0, material || 0, emissive || 0, null);
    }

    /* A bar from the hub out along direction a (in xz), in segments. */
    function arm(r, sw, a, time, index) {
      var c = sw.c, y = c[1] + sw.h, len = sw.r, th = sw.t;
      var ux = Math.cos(a), uz = Math.sin(a), yaw = Math.atan2(ux, uz);
      var look = sw.look || 'gear';
      var n, k, seg, mid;
      if (look === 'lolly') {
        n = 8; seg = len / n;
        for (k = 0; k < n; k++) {
          mid = seg * (k + 0.5);
          put(r, 'cyl', c[0] + ux * mid, y, c[2] + uz * mid, Math.PI / 2, yaw, 0, th, seg, th,
              k % 2 ? '#ffffff' : '#e8306a');
        }
        // the lollipop on the end, side on to whoever it is coming at
        var tx = -uz, tz = ux;
        var tip = len - 0.2;
        put(r, 'cyl', c[0] + ux * tip, y + 0.4, c[2] + uz * tip, Math.PI / 2, Math.atan2(tx, tz), 0, 3.4, 0.5, 3.4, '#ff5aa0');
        put(r, 'cyl', c[0] + ux * tip, y + 0.4, c[2] + uz * tip, Math.PI / 2, Math.atan2(tx, tz), 0, 2.2, 0.56, 2.2, '#fff0f6');
        put(r, 'cyl', c[0] + ux * tip, y + 0.4, c[2] + uz * tip, Math.PI / 2, Math.atan2(tx, tz), 0, 1.0, 0.62, 1.0, '#ffb8d8');
      } else if (look === 'neon') {
        var hue = ['#3ad8ff', '#ff3ad8', '#ffe83a', '#7aff5a'];
        var hueNow = hue[index % hue.length];
        put(r, 'box', c[0] + ux * len / 2, y, c[2] + uz * len / 2, 0, yaw, 0, th * 0.7, th * 0.7, len,
            hueNow, 1, 2, 1);
        put(r, 'box', c[0] + ux * len / 2, y, c[2] + uz * len / 2, 0, yaw, 0, th * 1.5, th * 1.5, len + 0.4,
            hueNow, 0.22, 2, 1);
        put(r, 'sph', c[0] + ux * len, y, c[2] + uz * len, 0, 0, 0, th * 1.6, th * 1.6, th * 1.6, '#ffffff', 1, 2, 1);
      } else if (look === 'bamboo') {
        n = 5; seg = len / n;
        for (k = 0; k < n; k++) {
          mid = seg * (k + 0.5);
          put(r, 'cyl', c[0] + ux * mid, y, c[2] + uz * mid, Math.PI / 2, yaw, 0, th, seg - 0.2, th,
              k % 2 ? '#7ab84a' : '#8ac85a');
          put(r, 'cyl', c[0] + ux * (seg * (k + 1) - 0.1), y, c[2] + uz * (seg * (k + 1) - 0.1),
              Math.PI / 2, yaw, 0, th * 1.15, 0.2, th * 1.15, '#4a7a2a');
        }
        // a paper lantern riding on the end, bobbing
        var bob = Math.sin(time * 4 + a) * 0.12;
        var lx = c[0] + ux * (len - 0.5), lz = c[2] + uz * (len - 0.5);
        put(r, 'cyl', lx, y + th / 2 + 0.1, lz, 0, 0, 0, 0.9, 0.2, 0.9, '#2a1a10');
        put(r, 'sph', lx, y + th / 2 + 0.85 + bob, lz, 0, 0, 0, 1.0, 1.3, 1.0, '#ff5a3a', 0.92, 2, 0.6);
        put(r, 'cyl', lx, y + th / 2 + 1.55 + bob, lz, 0, 0, 0, 0.6, 0.16, 0.6, '#2a1a10');
      } else {
        // the Foundry's: a steel girder in hazard stripes, weighted at the tip
        n = 7; seg = len / n;
        for (k = 0; k < n; k++) {
          mid = seg * (k + 0.5);
          put(r, 'box', c[0] + ux * mid, y, c[2] + uz * mid, 0, yaw, 0, th, th, seg,
              k % 2 ? '#1e1e22' : '#e8b830', 1, k % 2 ? 1 : 0);
        }
        put(r, 'box', c[0] + ux * (len - 0.6), y, c[2] + uz * (len - 0.6), 0, yaw, 0, th + 0.8, th + 0.8, 1.6,
            '#4a4e56', 1, 1);
      }
    }

    function drawSweepers(r, time) {
      (ex.sweepers || []).forEach(function (sw) {
        var turn = sw.ph + sw.w * loc.ht;
        for (var k = 0; k < sw.arms; k++) arm(r, sw, turn + k * 2 * Math.PI / sw.arms, time, k);
        // the collar the arms turn in
        put(r, 'cyl', sw.c[0], sw.c[1] + sw.h, sw.c[2], 0, -turn, 0, 3.4, sw.t + 0.5, 3.4,
            sw.look === 'neon' ? '#1a1430' : (sw.look === 'bamboo' ? '#8a3a2a' : (sw.look === 'lolly' ? '#ffffff' : '#5a5e66')),
            1, sw.look === 'neon' || !sw.look ? 1 : 0);
      });
    }

    function drawHammers(r) {
      (ex.hammers || []).forEach(function (h) {
        var head = hammerHead(h, loc.hc), th = head.theta;
        var p = h.pivot, L = h.len, s = h.head, hp = head.p;
        var alongX = h.axis === 'x';
        var rx = alongX ? 0 : -th, rz = alongX ? th : 0;
        // the hammer's own up (back along the arm to the pivot), in the world
        var ux = alongX ? -Math.sin(th) : 0, uy = Math.cos(th), uz = alongX ? 0 : -Math.sin(th);
        // the arm, from the pivot down into the head, and the axle it turns on
        put(r, 'box', p[0] - ux * L / 2, p[1] - uy * L / 2, p[2] - uz * L / 2, rx, 0, rz, 0.7, L, 0.7, '#5a5e66', 1, 1);
        put(r, 'cyl', p[0], p[1] - 0.6, p[2], alongX ? Math.PI / 2 : 0, 0, alongX ? 0 : Math.PI / 2,
            1.0, 3.2, 1.0, '#2a2a2e', 1, 1);
        // the head, in three bands: hazard yellow, black, yellow
        for (var k = 0; k < 3; k++) {
          var off = (k - 1) * s[1] / 3;
          put(r, 'box', hp[0] + ux * off, hp[1] + uy * off, hp[2] + uz * off, rx, 0, rz, s[0], s[1] / 3, s[2],
              k === 1 ? '#1e1e22' : '#e8b830', 1, k === 1 ? 1 : 0);
        }
      });
    }

    function drawLasers(r, time) {
      (ex.lasers || []).forEach(function (lz) {
        var ab = laserBeam(lz, loc.lc), a = ab[0], b = ab[1];
        var dx = b[0] - a[0], dz = b[2] - a[2], len = Math.hypot(dx, dz), yaw = Math.atan2(dx, dz);
        var mx = (a[0] + b[0]) / 2, mz = (a[2] + b[2]) / 2;
        var flick = 0.85 + 0.15 * Math.sin(time * 40 + lz.id);
        put(r, 'box', mx, a[1], mz, 0, yaw, 0, 0.22, 0.22, len, '#ff2a4a', 1, 2, 1);
        put(r, 'box', mx, a[1], mz, 0, yaw, 0, 0.7, 0.7, len, '#ff4a6a', 0.25 * flick, 2, 1);
        // the emitters riding their rails at each end
        [a, b].forEach(function (e) {
          put(r, 'box', e[0], e[1], e[2], 0, yaw, 0, 1.2, 1.4, 1.2, '#1a1430', 1, 1);
          put(r, 'sph', e[0], e[1], e[2], 0, 0, 0, 0.7, 0.7, 0.7, '#ff2a4a', 1, 2, 1);
        });
      });
    }

    function drawBelts(r, dt) {
      var sign = twistOn('reverse') ? -1 : 1;
      (ex.belts || []).forEach(function (belt, i) {
        var speed = Math.hypot(belt.v[0], belt.v[1]);
        if (!speed) return;
        beltOff[i] = ((beltOff[i] || 0) + dt * speed * sign) % 3;
        var alongX = Math.abs(belt.v[0]) >= Math.abs(belt.v[1]);
        var dir = alongX ? (belt.v[0] > 0 ? 1 : -1) : (belt.v[1] > 0 ? 1 : -1);
        var lo = alongX ? belt.rect[0] : belt.rect[2], hi = alongX ? belt.rect[1] : belt.rect[3];
        var across0 = alongX ? belt.rect[2] : belt.rect[0], across1 = alongX ? belt.rect[3] : belt.rect[1];
        var mid = (across0 + across1) / 2, width = across1 - across0 - 1.2;
        var off = ((beltOff[i] * dir) % 3 + 3) % 3;
        for (var x = lo + 0.6 + off; x < hi - 0.4; x += 3) {
          var px = alongX ? x : mid, pz = alongX ? mid : x;
          put(r, 'box', px, belt.y + 0.08, pz, 0, 0, 0, alongX ? 0.5 : width, 0.06, alongX ? width : 0.5,
              sign < 0 ? '#ff7a3a' : '#e8b830', 1, 0);
        }
      });
    }

    function drawBoosts(r, time) {
      boosts.forEach(function (bo, i) {
        var k = (time * 1.6 + i * 0.3) % 1;
        var off = (k - 0.5) * bo.l;
        var x = bo.p[0] + Math.sin(bo.yaw) * off, z = bo.p[2] + Math.cos(bo.yaw) * off;
        put(r, 'box', x, bo.p[1] + 0.26, z, 0, bo.yaw, 0, bo.w * 0.86, 0.08, 0.8, '#ffffff',
            0.75 * Math.sin(k * Math.PI), 2, 1);
      });
    }

    function drawJelly(r, time) {
      var t = now();
      pads.forEach(function (pad, i) {
        if (!pad.jelly) return;
        var age = t - (wobbles[i] || -9);
        var top = pad.p[1], size = pad.s || [pad.r * 2, pad.r * 2];
        var w = age < 1.0 ? Math.sin(age * 26) * Math.exp(-age * 4.5) : 0.04 * Math.sin(time * 3 + i);
        var grow = Math.max(0, w), squash = Math.max(0, -w);
        var sy = 2.1 + 0.8 * squash;
        put(r, 'box', pad.p[0], top - 2.05 + sy / 2, pad.p[2], 0, 0, 0,
            size[0] + 0.2 + 1.2 * grow, sy, size[1] + 0.2 + 1.2 * grow, pad.c || '#e83a5a', 0.32, 3, 0.2);
      });
    }

    function tileBox(key) {
      var d = arena.dynamic && arena.dynamic[key];
      var boxes = d && d.boxes;
      return boxes && boxes.length ? boxes[0] : null;
    }
    function overlay(r, box, grow, colour, alpha, material, jitter) {
      var lo = box[0], hi = box[1];
      var j = jitter || 0;
      put(r, 'box', (lo[0] + hi[0]) / 2 + (hash(now() * 60) - 0.5) * j, (lo[1] + hi[1]) / 2,
          (lo[2] + hi[2]) / 2 + (hash(now() * 60 + 3) - 0.5) * j, 0, 0, 0,
          hi[0] - lo[0] + grow, hi[1] - lo[1] + grow, hi[2] - lo[2] + grow, colour, alpha, material || 3, 0.5);
    }

    function drawTiles(r) {
      var dyn = arena.dynamic || {}, on = arena.dynOn || {};
      var rate = (clk.rate && clk.rate[1]) || 1;
      (ex.blink || []).forEach(function (spec) {
        var phase = blinkPhase(spec, loc.bt);
        var left = (spec.on - phase) * spec.period / rate;            // to going out
        var back = (1 - phase) * spec.period / rate;                  // to coming on
        Object.keys(dyn).forEach(function (key) {
          if (dyn[key].group !== spec.group) return;
          var box = tileBox(key);
          if (!box) return;
          if (on[key]) {
            if (left > 0 && left < 0.75) {
              var pulse = 0.5 + 0.5 * Math.sin(now() * 30);
              overlay(r, box, 0.12, '#ff4a3a', 0.25 + 0.35 * pulse, 2);
            }
          } else {
            var soon = back < 0.6 ? 1 - back / 0.6 : 0;
            overlay(r, box, 0.06, soon > 0 ? '#ffffff' : '#9ab8d8', 0.08 + 0.3 * soon, 3);
          }
        });
      });
      var t = now();
      (ex.crumble || []).forEach(function (tile) {
        var box = tileBox(tile.key);
        if (!box) return;
        if (on[tile.key]) {
          var age = t - (creaks[tile.key] || -9);
          if (age < CRUMBLE_AFTER + 0.2) overlay(r, box, 0.1, '#5a3a1a', 0.45, 0, 0.3);
        } else {
          var gone = t - (fellAt[tile.key] || t);
          overlay(r, box, 0.06, '#d8c8a8', 0.06 + 0.22 * Math.min(1, gone / CRUMBLE_BACK), 3);
        }
      });
    }

    var POWER_ART = {
      spring: function (r, x, y, z, spin) {
        for (var k = 0; k < 4; k++) put(r, 'torus', x, y - 0.75 + k * 0.42, z, 0, spin, 0, 1.3, 1.6, 1.3, '#7aea5a', 1, 1);
        put(r, 'cyl', x, y + 1.0, z, 0, spin, 0, 1.5, 0.3, 1.5, '#2a7a2a');
      },
      rocket: function (r, x, y, z, spin) {
        put(r, 'rocket', x, y, z, 0.5, spin, 0.3, 1.4, 2.4, 1.4, '#ff8a3a', 1, 1);
      },
      feather: function (r, x, y, z, spin, time) {
        put(r, 'feather', x, y, z, 0.2 * Math.sin(time * 2), spin, 0.4, 1.4, 2.6, 1.4, '#f4f0ff');
      },
      shield: function (r, x, y, z, spin, time) {
        put(r, 'sph', x, y, z, 0, 0, 0, 2.2, 2.2, 2.2, '#8ad8ff', 0.45, 3, 0.3);
        put(r, 'sparkle', x + 0.5, y + 0.6, z, 0, spin, 0, 0.8, 0.8, 0.8, '#ffffff', 0.9 + 0.1 * Math.sin(time * 6), 2, 1);
      }
    };

    function drawPowers(r, time) {
      (ax.pw || []).forEach(function (entry) {
        var spot = spots[entry[0]], art = POWER_ART[entry[1]];
        if (!spot || !art) return;
        var p = spot.p, bob = Math.sin(time * 2.4 + entry[0]) * 0.35;
        art(r, p[0], p[1] + 2.4 + bob, p[2], time * 1.8 + entry[0], time);
        put(r, 'cyl', p[0], p[1] + 0.25, p[2], 0, 0, 0, 2.6 + 0.3 * Math.sin(time * 4), 0.06, 2.6 + 0.3 * Math.sin(time * 4),
            POWERS[entry[1]].colour, 0.55, 2, 1);
      });
    }

    function drawWind(r, time) {
      var zones = ex.wind || [];
      zones.forEach(function (z, zi) {
        var k = twistOn('typhoon') ? 1 : windNow(z, loc.ht);
        if (k < 0.05) return;
        var w = z.rect[1] - z.rect[0], d = z.rect[3] - z.rect[2];
        var along = Math.abs(z.dir[0]) > 0.5;
        var span = along ? w + 16 : d + 16;
        var count = Math.round((along ? d : w) / 2.4);
        var speed = z.strength * 2.2 * ((clk.rate && clk.rate[3]) || 1);
        for (var i = 0; i < count; i++) {
          var seed = hash(i * 7.1 + zi * 31);
          var run = ((time * speed + seed * span) % span) - 8;
          var cross = (i + 0.5) / count;
          var y = z.y + 1.2 + hash(i * 3.3 + zi) * 9;
          var x, zz;
          if (along) { x = (z.dir[0] > 0 ? z.rect[0] + run : z.rect[1] - run); zz = z.rect[2] + cross * d; }
          else { zz = (z.dir[1] > 0 ? z.rect[2] + run : z.rect[3] - run); x = z.rect[0] + cross * w; }
          put(r, 'box', x, y, zz, 0, along ? Math.PI / 2 : 0, 0, 0.08, 0.08, 3 + seed * 3, '#ffffff', 0.35 * k, 3, 0.2);
        }
      });
    }

    function drawBeacon(r, time) {
      if (arena.phase !== 'active' && arena.phase !== 'setup') return;
      var reached = arena.me.cp || 0;
      var next = cps[reached];
      if (!next || done()) return;
      var p = next.p, gold = !!next.finish;
      var colour = gold ? '#ffd23a' : (TEAM_LIGHT[client.myTeam] || '#ffffff');
      put(r, 'cyl', p[0], p[1] + 34, p[2], 0, 0, 0, 2.2, 68, 2.2, colour, 0.16, 2, 1);
      // a ring hovering over the line, breathing
      var ring = next.r * 2 * (1 + 0.04 * Math.sin(time * 3));
      put(r, 'torus', p[0], p[1] + 0.8 + Math.sin(time * 2) * 0.2, p[2], 0, time * 0.6, 0,
          ring, 2.2, ring, colour, 0.75, 2, 1);
      var me = myPos();
      var dist = Math.hypot(me[0] - p[0], me[1] - p[1], me[2] - p[2]);
      if (r.queueTag && dist > 14) {
        r.queueTag('ss_cp', gold ? 'FINISH' : 'CHECKPOINT ' + next.i, colour, Math.round(dist) + ' studs',
                   [p[0], p[1] + 14, p[2]], dist > 70 ? 1.5 : 1.1);
      }
    }

    function drawRacers(r, time) {
      var pr = ax.pr || {}, t = now();
      Object.keys(pr).forEach(function (key) {
        var id = parseInt(key, 10), flags = pr[key][3] || 0;
        var mine = id === client.myId;
        if (mine && !client.thirdPerson) return;
        var pos = playerPos(id);
        if (!pos) return;
        if (flags & 4) put(r, 'sph', pos[0], pos[1] + 2.8, pos[2], 0, 0, 0, 6.2, 7.0, 6.2, '#8ad8ff', 0.18, 3, 0.25);
        if (flags & 2) {
          put(r, 'feather', pos[0] + 0.9, pos[1] + 7.0 + Math.sin(time * 3 + id) * 0.2, pos[2], 0, time + id, 0.5,
              0.8, 1.5, 0.8, '#f4f0ff');
        }
        if (flags & 1) {
          for (var k = 0; k < 3; k++) {
            put(r, 'torus', pos[0] + 0.55, pos[1] - 0.1 + k * 0.28, pos[2], 0, 0, 0, 0.8, 1.0, 0.8, '#7aea5a', 1, 1);
            put(r, 'torus', pos[0] - 0.55, pos[1] - 0.1 + k * 0.28, pos[2], 0, 0, 0, 0.8, 1.0, 0.8, '#7aea5a', 1, 1);
          }
        }
      });
      // rockets burning
      Object.keys(flames).forEach(function (key) {
        var id = parseInt(key, 10);
        if (flames[key] < t) { delete flames[key]; return; }
        var pos = playerPos(id);
        if (!pos || !client.particles) return;
        var p = id === client.myId ? client.local : client.players[id];
        var yaw = (p && p.yaw) || 0;
        for (var i = 0; i < 2; i++) {
          client.particles.spawn({ p: [pos[0] - Math.sin(yaw) * 1.2, pos[1] + 2.6, pos[2] - Math.cos(yaw) * 1.2],
            v: [-Math.sin(yaw) * 10 + (Math.random() - 0.5) * 3, (Math.random() - 0.5) * 3, -Math.cos(yaw) * 10],
            life: 0.3, size: 0.9, grow: -1.5, gravity: 0, spin: 4, blend: 'add', shape: 'flame',
            colors: ['#fff3b0', '#ffb347', '#ff5a1a'] });
        }
      });
    }

    // -------------------------------------------------------- the veil
    function makeVeil() {
      if (veil) return veil;
      var host = document.querySelector('#game-root .hud') || document.body;
      veil = document.createElement('div');
      veil.id = 'ss-veil';
      veil.style.cssText = 'position:absolute;left:0;top:0;right:0;bottom:0;pointer-events:none;' +
        'opacity:0;transition:opacity .3s;z-index:1';
      host.appendChild(veil);
      return veil;
    }
    var veilColour = '';
    function setVeil(alpha, colour) {
      var v = veil || (alpha > 0 ? makeVeil() : null);
      if (!v) return;
      if (colour && colour !== veilColour) {
        veilColour = colour;
        v.style.background = 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, ' + colour + ' 100%)';
      }
      if (v.style.opacity !== String(alpha)) v.style.opacity = String(alpha);
    }
    function stepVeil(time) {
      if (!twist.on || arena.phase !== 'active') {
        if (veil && veil.style.opacity !== '0') setVeil(0);
        return;
      }
      var info = TWISTS[twist.kind] || {};
      var alpha = 0.55;
      if (twist.kind === 'drop') alpha = 0.25 + 0.5 * Math.pow(1 - blinkPhase({ ph: 0, period: 0.5 }, loc.bt), 3);
      if (twist.kind === 'sugar_rush') alpha = 0.45 + 0.12 * Math.sin(time * 8);
      var ease = twist.kind === 'drop' ? 'none' : 'opacity .3s';
      if (veil && veil.style.transition !== ease) veil.style.transition = ease;
      setVeil(alpha.toFixed(2), (info.colour || '#ffffff') + '88');
    }

    // ------------------------------------------------------------ HUD
    function standings() {
      var pr = ax.pr || {};
      return Object.keys(pr).map(function (key) {
        var e = pr[key];
        return { id: parseInt(key, 10), prog: e[0] || 0, cp: e[1] || 0, place: e[2] || 0 };
      }).sort(function (a, b) {
        if (a.place || b.place) return (a.place || 999) - (b.place || 999);
        return (b.cp - a.cp) || (b.prog - a.prog);
      });
    }

    function roleChip() {
      var team = client.myTeam;
      if (!team || !TEAM_LIGHT[team]) { if (lastRole) { arena.setRole(''); lastRole = ''; } return; }
      var bits = [];
      var t = now();
      ['spring', 'feather', 'shield'].forEach(function (kind) {
        if ((pw[kind] || 0) > t) bits.push('<b style="color:' + POWERS[kind].colour + '">' + POWERS[kind].name + ' ' + Math.ceil(pw[kind] - t) + 's</b>');
      });
      var rockets = arena.me.rocket || 0;
      if (rockets) bits.push('<b style="color:' + POWERS.rocket.colour + '">ROCKET x' + rockets + ' (E)</b>');
      if (twist.on && TWISTS[twist.kind]) bits.push('<b style="color:' + TWISTS[twist.kind].colour + '">' + TWISTS[twist.kind].chip + '</b>');
      var html = '<b style="color:' + TEAM_LIGHT[team] + '">' + esc(arena.teamName(team).toUpperCase()) + '</b>' +
        (bits.length ? ' &bull; ' + bits.join(' &bull; ') : '');
      if (html !== lastRole) { arena.setRole(html, team); lastRole = html; }
    }

    function sidePanel() {
      var t = now();
      if (t - sideAt < 0.5) return;
      sideAt = t;
      if (arena.phase !== 'active') { if (lastSide) { arena.side(''); lastSide = ''; } return; }
      var list = standings().slice(0, 6);
      var html = '<div class="ar-side-h">THE RACE</div>' + list.map(function (e, n) {
        var p = e.id === client.myId ? { name: 'You', team: client.myTeam } : client.players[e.id];
        if (!p) return '';
        var colour = TEAM_LIGHT[p.team] || '#ffffff';
        var where = e.place ? ordinal(e.place) + ' home' : (e.cp ? 'CP ' + e.cp : 'start');
        return '<div' + (e.id === client.myId ? ' style="font-weight:700"' : '') + '>' + (n + 1) + '. <b style="color:' +
          colour + '">' + esc(p.name) + '</b> <span style="opacity:.75">' + where + '</span></div>';
      }).join('');
      if (html !== lastSide) { arena.side(html); lastSide = html; }
    }

    function hud(state) {
      roleChip();
      sidePanel();
      var points = ss.pts || {};
      var out = {
        left: { value: points.red || 0, label: arena.teamName('red'), colour: TEAM_LIGHT.red },
        right: { value: points.blue || 0, label: arena.teamName('blue'), colour: TEAM_LIGHT.blue },
        bars: []
      };
      if (arena.phase === 'setup') {
        out.title = 'ON YOUR MARKS';
        out.sub = 'The gates drop at GO &bull; checkpoints and your finishing place score for your team';
        return out;
      }
      if (arena.phase !== 'active') return out;
      var total = ss.cps || cps.length;
      var reached = arena.me.cp || 0;
      var place = arena.me.place || 0;
      var list = standings();
      var at = 0;
      for (var i = 0; i < list.length; i++) if (list[i].id === client.myId) { at = i + 1; break; }
      if (place) {
        out.title = 'FINISHED ' + ordinal(place).toUpperCase() + (arena.me.time ? ' &bull; ' + Arena.fmt(arena.me.time) : '');
        out.sub = (ss.done || 0) + ' of ' + (ss.racers || 0) + ' home &bull; cheer the rest on';
      } else {
        var next = cps[reached];
        out.title = next && next.finish ? 'THE FINISH IS NEXT' : 'CHECKPOINT ' + Math.min(total, reached + 1) + ' OF ' + total;
        out.sub = next ? 'Next: <b>' + esc(next.finish ? 'the finish' : next.name) + '</b>' : '';
        if (ss.done) out.sub += ' &bull; ' + ss.done + ' home';
      }
      var hurry = hurryUntil - now();
      if (hurry > 0) {
        out.timer = 'HURRY! ' + Arena.fmt(hurry);
        out.urgent = hurry < 10;
      }
      var mine = (ax.pr || {})[String(client.myId)];
      if (mine && client.myTeam) {
        out.bars.push({ label: 'Course', value: place ? 1 : (mine[0] || 0), colour: TEAM[client.myTeam] || '#ffffff',
                        text: at ? ordinal(at) + ' of ' + list.length : '' });
      }
      var t = now();
      ['spring', 'feather', 'shield'].forEach(function (kind) {
        var left = (pw[kind] || 0) - t;
        if (left > 0) out.bars.push({ label: POWERS[kind].name.replace('A ', ''), value: left / 14, colour: POWERS[kind].colour,
                                       text: Math.ceil(left) + 's' });
      });
      if (twist.on && TWISTS[twist.kind] && ss.left) {
        out.bars.push({ label: TWISTS[twist.kind].chip, value: 1, colour: TWISTS[twist.kind].colour, text: 'on' });
      }
      return out;
    }

    function prompt() {
      if (!inPlay()) return undefined;
      if ((arena.me.rocket || 0) > 0) return 'Rocket ready -- press E to blast off the way you are facing';
      if (done()) return 'Home! Watch the rest come in';
      return '';
    }

    // -------------------------------------------------------- messages
    var messages = {
      sss: function (msg) { applyState(msg.s && msg.s.ss); },
      ssx: function (msg) {
        var k = msg.k, me = client.myId, t = now();
        var info;
        if (k === 'go') {
          client.audio.play('ss_go', { volume: 0.8 });
        } else if (k === 'cp') {
          var mark = cps[(msg.i || 1) - 1];
          if (msg.id === me) {
            if (msg.finish) {
              arena.banner('FINISHED ' + ordinal(msg.place).toUpperCase() + '!', '+' + msg.gain + ' for your team', 'good', 3600);
              client.audio.play('ss_finish', { volume: 0.9 });
              arena.flashScreen('rgba(255,230,120,0.35)', 400);
            } else {
              arena.banner('CHECKPOINT ' + msg.i, (msg.first ? '<b>FIRST THERE!</b> ' : '') + esc(msg.name || '') +
                           ' &bull; +' + msg.gain, msg.first ? 'good' : 'area', 2200);
              client.audio.play(msg.first ? 'ss_first' : 'ss_cp', { volume: 0.8 });
            }
          } else if (msg.finish) {
            client.hud.toast(esc(nameOf(msg.id)) + ' finished ' + ordinal(msg.place), msg.place === 1 ? 'good' : '');
            if (mark) playAt('ss_cp', mark.p, 0.6);
          } else if (msg.first) {
            client.hud.toast(esc(nameOf(msg.id)) + ' reached ' + esc(msg.name || 'checkpoint ' + msg.i) + ' first');
          }
          if (mark && client.particles) {
            client.particles.burst(msg.finish ? 'confetti' : 'pickup', [mark.p[0], mark.p[1] + 4, mark.p[2]],
                                   { radius: msg.finish ? 10 : 4 });
          }
        } else if (k === 'hurry') {
          hurryUntil = t + (msg['in'] || 25);
          arena.banner('HURRY UP!', 'Half the field is home &bull; ' + Math.round(msg['in'] || 25) + 's left', 'bad', 3000);
          client.audio.play('ss_hurry', { volume: 0.8 });
        } else if (k === 'twist_warn') {
          info = TWISTS[msg.twist] || {};
          arena.banner(info.warn || 'SOMETHING IS COMING', info.warnSub || '', 'bad', 2600);
          client.audio.play('ss_warn', { volume: 0.7 });
        } else if (k === 'twist') {
          info = TWISTS[msg.twist] || {};
          twist.kind = msg.twist || twist.kind;
          twist.on = !!msg.on;
          if (msg.on) {
            arena.banner(info.on || 'THE TWIST!', info.onSub || '', 'bad', 3200);
            client.audio.play('ss_twist_' + msg.twist, { volume: 0.85 });
            arena.flashScreen((info.colour || '#ffffff') + '55', 350);
          } else {
            client.hud.toast(info.off || 'The course settles down');
          }
          roleChip();
        } else if (k === 'fell') {
          if (msg.id === me) {
            client.audio.play('ss_fall', { volume: 0.7 });
            arena.flashScreen('rgba(20,30,60,0.45)', 300);
            client.hud.toast('Back to your last checkpoint');
            carry = null;
          }
        } else if (k === 'ring_out') {
          if (msg.by === me) {
            arena.banner('RING OUT!', 'You bonked ' + esc(nameOf(msg.who)) + ' off the course &bull; +2', 'good', 2400);
            client.audio.play('ss_ringout', { volume: 0.85 });
          } else if (msg.who === me) {
            client.hud.toast(esc(nameOf(msg.by)) + ' bonked you off!', 'bad');
          }
        } else if (k === 'swing') {
          var from = playerPos(msg.id);
          if (msg.id !== me) playAt('ss_swing', from, 0.6);
          if (msg.hit) {
            var to = playerPos(msg.hit);
            playAt('ss_bonk', to, 0.9);
            if (to && client.particles) client.particles.burst('impact', [to[0], to[1] + 3, to[2]]);
            if (msg.hit === me) { shakeUntil = t + 0.3; carry = null; }
          }
        } else if (k === 'bubble') {
          var bp = playerPos(msg.id);
          playAt('ss_bubble', bp, 0.8);
          if (bp && client.particles) client.particles.burst('heal', [bp[0], bp[1] + 3, bp[2]]);
        } else if (k === 'power') {
          var power = POWERS[msg.kind] || {};
          if (msg.kind !== 'rocket') pw[msg.kind] = t + (msg['for'] || 10);
          arena.banner(power.name || 'A POWER-UP', power.line || '', 'good', 2200);
          client.audio.play('ss_power', { volume: 0.8 });
          roleChip();
        } else if (k === 'took') {
          var spot = spots[msg.spot];
          if (spot) {
            playAt('ss_power', spot.p, 0.4);
            if (client.particles) client.particles.burst('pickup', [spot.p[0], spot.p[1] + 2.4, spot.p[2]]);
          }
        } else if (k === 'rocket') {
          flames[msg.id] = t + 0.8;
          playAt('ss_rocket', playerPos(msg.id), 0.9);
          if (msg.id === me) shakeUntil = t + 0.4;
        } else if (k === 'pad') {
          var pp = playerPos(msg.id);
          if (pp) {
            for (var i = 0; i < pads.length; i++) {
              if (Math.hypot(pads[i].p[0] - pp[0], pads[i].p[2] - pp[2]) < pads[i].r + 2) { bounced(i, pads[i]); break; }
            }
          }
        } else if (k === 'thwack') {
          var hp = playerPos(msg.id);
          playAt('ss_thwack', hp, 0.8);
          if (hp && client.particles) client.particles.burst('impact', [hp[0], hp[1] + 3, hp[2]]);
        } else if (k === 'zap') {
          var zp = playerPos(msg.id);
          playAt('ss_zap', zp, 0.9);
          if (msg.id === me) {
            arena.flashScreen('rgba(255,40,70,0.45)', 350);
            client.hud.toast('Zapped! Back to your checkpoint', 'bad');
            carry = null;
          }
        } else if (k === 'creak') {
          creaks[msg.key] = t;
          var box = tileBox(msg.key);
          if (box) playAt('ss_creak', [(box[0][0] + box[1][0]) / 2, box[1][1], (box[0][2] + box[1][2]) / 2], 0.8);
        }
      }
    };

    function onDynamic(changes) {
      var t = now();
      for (var key in changes) {
        if (changes[key]) continue;
        var d = arena.dynamic[key];
        if (!d || d.group !== 'crumble') continue;
        fellAt[key] = t;
        var box = tileBox(key);
        if (!box) continue;
        var c = [(box[0][0] + box[1][0]) / 2, box[1][1], (box[0][2] + box[1][2]) / 2];
        playAt('ss_crumble', c, 0.9);
        if (client.particles) {
          for (var i = 0; i < 14; i++) {
            client.particles.spawn({ p: [c[0] + (Math.random() - 0.5) * (box[1][0] - box[0][0]), c[1] - 0.5,
                                         c[2] + (Math.random() - 0.5) * (box[1][2] - box[0][2])],
              v: [(Math.random() - 0.5) * 4, -2 - Math.random() * 4, (Math.random() - 0.5) * 4],
              life: 1.0 + Math.random() * 0.5, size: 0.5 + Math.random() * 0.5, grow: -0.2, gravity: -30,
              spin: 5, blend: 'normal', shape: 'spark', colors: ['#c8a068', '#8a6a3a', '#5a3a1a'] });
          }
        }
      }
    }

    // ------------------------------------------------------------ hooks
    return {
      messages: messages,
      onMap: loadMap,
      onArea: function () { arena.setRole(''); reset(); },
      onState: function (state) { applyState(state.ss); },
      onSnapshot: function (msg) { ax = msg.ax || {}; takeClocks(); },
      onMe: function (me) {
        var t = now();
        var held = me.pw || {};
        ['spring', 'feather', 'shield'].forEach(function (kind) {
          pw[kind] = held[kind] ? t + held[kind] : 0;
        });
        roleChip();
      },
      onPhase: function (msg) {
        if (msg.phase === 'setup') {
          pw = {}; hurryUntil = 0; carry = null; boostUntil = 0; twist.on = false;
          roleChip();
        }
        if (msg.phase !== 'active') { arena.side(''); lastSide = ''; setVeil(0); }
      },
      onDynamic: onDynamic,
      onEnd: function (msg) {
        twist.on = false;
        setVeil(0);
        arena.side(''); lastSide = '';
        var place = arena.me.place || 0;
        if (place) client.hud.toast('You finished ' + ordinal(place) + (arena.me.time ? ' in ' + Arena.fmt(arena.me.time) : ''), place <= 3 ? 'good' : '');
        else if (client.myTeam) client.hud.toast('You reached checkpoint ' + (arena.me.cp || 0) + ' -- the clock beat you');
      },
      goLine: function () { return 'Race to the finish -- bonk your rivals off the course!'; },
      canFire: function () { return arena.phase === 'active' && !done(); },
      isCustom: function (stats) { return !!(stats && String(stats.kind || '').indexOf('ss_') === 0); },
      localFire: function (stats) {
        if (stats.kind === 'ss_bonk') {
          client.audio.play('ss_swing', { volume: 0.8 });
          return true;
        }
        return false;
      },
      useDown: function () {
        if (!inPlay()) return false;
        if ((arena.me.rocket || 0) <= 0) {
          client.hud.toast('No rocket -- look for one on the course');
          return true;
        }
        return false;
      },
      moveScale: moveScale,
      jumpScale: jumpScale,
      gravityScale: gravityScale,
      afterStep: afterStep,
      jolt: function () {
        var left = shakeUntil - now();
        if (left <= 0) return null;
        var k = left * 1.6;
        return [Math.sin(now() * 71) * 0.18 * k, Math.cos(now() * 63) * 0.12 * k, 0, Math.sin(now() * 57) * 0.01 * k];
      },
      draw: function (renderer, dt, time) {
        stepClocks(dt);
        stepVeil(time);
        drawSweepers(renderer, time);
        drawHammers(renderer);
        drawLasers(renderer, time);
        drawBelts(renderer, dt);
        drawBoosts(renderer, time);
        drawJelly(renderer, time);
        drawTiles(renderer);
        drawPowers(renderer, time);
        drawWind(renderer, time);
        drawBeacon(renderer, time);
        drawRacers(renderer, time);
      },
      nameTag: function (player) {
        if (arena.phase !== 'active') return null;
        var e = (ax.pr || {})[String(player.id)];
        if (!e) return null;
        return { sub: e[2] ? ordinal(e[2]) + ' home' : 'CP ' + (e[1] || 0) };
      },
      hud: hud,
      prompt: prompt,
      scoreHead: function () {
        return '<th>Player</th><th>Place</th><th>Checkpoints</th><th>Score</th>';
      },
      scoreRow: function (row) {
        return '<td>' + (row.place ? ordinal(row.place) : '-') + '</td><td>' + (row.cp || 0) + '</td><td>' + (row.score || 0) + '</td>';
      },
      introInfo: function () { return { kicker: 'THE NEXT COURSE' }; }
    };
  });

  // ============================================================ sounds
  var GA = global.GameAudio;
  if (GA && GA.register) {
    GA.register('ss_go', function (vol) {
      [523, 659, 784, 1046].forEach(function (f, i) {
        this.later(i * 90, function () { this.tone({ type: 'square', freq: f, dur: 0.18, gain: 0.08 * vol }); });
      }, this);
      this.later(360, function () { this.noise({ filter: 'highpass', freq: 3000, dur: 0.4, gain: 0.1 * vol }); });
    });
    GA.register('ss_cp', function (vol) {
      this.tone({ type: 'triangle', freq: 880, dur: 0.14, gain: 0.12 * vol });
      this.later(100, function () { this.tone({ type: 'triangle', freq: 1318, dur: 0.3, gain: 0.11 * vol }); });
    });
    GA.register('ss_first', function (vol) {
      [659, 784, 988, 1318].forEach(function (f, i) {
        this.later(i * 70, function () { this.tone({ type: 'square', freq: f, dur: 0.16, gain: 0.07 * vol }); });
      }, this);
      this.later(300, function () { this.tone({ type: 'triangle', freq: 1568, dur: 0.4, gain: 0.1 * vol }); });
    });
    GA.register('ss_finish', function (vol) {
      [[523, 0, 0.12], [523, 130, 0.12], [523, 260, 0.12], [659, 390, 0.5], [587, 640, 0.14], [659, 790, 0.14],
       [784, 940, 0.7]].forEach(function (n) {
        this.later(n[1], function () {
          this.tone({ type: 'square', freq: n[0], dur: n[2], gain: 0.07 * vol });
          this.tone({ type: 'triangle', freq: n[0] / 2, dur: n[2], gain: 0.08 * vol });
        });
      }, this);
      this.later(940, function () { this.noise({ filter: 'highpass', freq: 4000, dur: 0.9, gain: 0.12 * vol }); });
    });
    GA.register('ss_boing', function (vol) {
      this.tone({ type: 'sine', freq: 160, freqEnd: 720, dur: 0.26, gain: 0.22 * vol });
      this.tone({ type: 'triangle', freq: 320, freqEnd: 1440, dur: 0.2, gain: 0.05 * vol });
    });
    GA.register('ss_jelly', function (vol) {
      this.tone({ type: 'sine', freq: 200, freqEnd: 520, dur: 0.16, gain: 0.2 * vol });
      [120, 220, 310].forEach(function (ms, i) {
        this.later(ms, function () { this.tone({ type: 'sine', freq: 420 - i * 60, freqEnd: 300 - i * 40, dur: 0.1, gain: (0.12 - i * 0.03) * vol }); });
      }, this);
    });
    GA.register('ss_whoosh', function (vol) {
      this.noise({ filter: 'bandpass', freq: 500, freqEnd: 3400, dur: 0.38, gain: 0.25 * vol });
    });
    GA.register('ss_swing', function (vol) {
      this.noise({ filter: 'bandpass', freq: 1900, freqEnd: 500, dur: 0.15, gain: 0.22 * vol });
    });
    GA.register('ss_bonk', function (vol) {
      this.tone({ type: 'square', freq: 540, freqEnd: 150, dur: 0.12, gain: 0.12 * vol });
      this.tone({ type: 'sine', freq: 95, freqEnd: 50, dur: 0.16, gain: 0.3 * vol });
      this.noise({ filter: 'lowpass', freq: 1400, dur: 0.06, gain: 0.25 * vol });
    });
    GA.register('ss_thwack', function (vol) {
      this.noise({ filter: 'lowpass', freq: 900, freqEnd: 120, dur: 0.32, gain: 0.5 * vol });
      this.tone({ type: 'sine', freq: 72, freqEnd: 34, dur: 0.32, gain: 0.35 * vol });
      this.tone({ type: 'square', freq: 210, freqEnd: 90, dur: 0.08, gain: 0.08 * vol });
    });
    GA.register('ss_zap', function (vol) {
      this.tone({ type: 'sawtooth', freq: 1900, freqEnd: 110, dur: 0.3, gain: 0.12 * vol });
      this.noise({ filter: 'highpass', freq: 4200, dur: 0.16, gain: 0.14 * vol });
    });
    GA.register('ss_fall', function (vol) {
      this.tone({ type: 'sine', freq: 980, freqEnd: 170, dur: 0.85, gain: 0.12 * vol });
    });
    GA.register('ss_power', function (vol) {
      [784, 1046, 1318, 1568].forEach(function (f, i) {
        this.later(i * 55, function () { this.tone({ type: 'triangle', freq: f, dur: 0.14, gain: 0.1 * vol }); });
      }, this);
      this.later(200, function () { this.noise({ filter: 'highpass', freq: 5000, dur: 0.3, gain: 0.08 * vol }); });
    });
    GA.register('ss_rocket', function (vol) {
      this.noise({ filter: 'lowpass', freq: 400, freqEnd: 2600, dur: 0.65, gain: 0.4 * vol });
      this.tone({ type: 'sawtooth', freq: 80, freqEnd: 240, dur: 0.6, gain: 0.07 * vol });
    });
    GA.register('ss_bubble', function (vol) {
      this.tone({ type: 'sine', freq: 300, freqEnd: 900, dur: 0.08, gain: 0.18 * vol });
      this.later(110, function () { this.tone({ type: 'sine', freq: 520, freqEnd: 1300, dur: 0.07, gain: 0.14 * vol }); });
    });
    GA.register('ss_creak', function (vol) {
      this.tone({ type: 'sawtooth', freq: 150, freqEnd: 105, dur: 0.55, gain: 0.05 * vol });
      this.noise({ filter: 'bandpass', freq: 520, freqEnd: 380, dur: 0.55, gain: 0.12 * vol });
    });
    GA.register('ss_crumble', function (vol) {
      this.noise({ filter: 'lowpass', freq: 1500, freqEnd: 180, dur: 0.6, gain: 0.42 * vol });
      [90, 200, 330].forEach(function (ms) {
        this.later(ms, function () { this.noise({ filter: 'bandpass', freq: 900, dur: 0.05, gain: 0.2 * vol }); });
      }, this);
    });
    GA.register('ss_hurry', function (vol) {
      for (var i = 0; i < 6; i++) {
        (function (k) {
          this.later(k * 150, function () { this.tone({ type: 'square', freq: k % 2 ? 1318 : 988, dur: 0.1, gain: 0.07 * vol }); });
        }).call(this, i);
      }
    });
    GA.register('ss_warn', function (vol) {
      [[440, 0], [330, 220], [440, 440], [330, 660]].forEach(function (n) {
        this.later(n[1], function () { this.tone({ type: 'square', freq: n[0], dur: 0.18, gain: 0.07 * vol }); });
      }, this);
    });
    GA.register('ss_ringout', function (vol) {
      this.tone({ type: 'sawtooth', freq: 392, freqEnd: 370, dur: 0.3, gain: 0.07 * vol });
      this.later(300, function () { this.tone({ type: 'sawtooth', freq: 370, freqEnd: 196, dur: 0.6, gain: 0.07 * vol }); });
      this.noise({ filter: 'bandpass', freq: 700, freqEnd: 500, dur: 0.9, gain: 0.08 * vol });
    });
    GA.register('ss_twist_reverse', function (vol) {
      this.tone({ type: 'sawtooth', freq: 70, freqEnd: 38, dur: 1.1, gain: 0.12 * vol });
      this.noise({ filter: 'bandpass', freq: 320, freqEnd: 160, dur: 1.1, gain: 0.25 * vol });
      [200, 480, 760].forEach(function (ms) {
        this.later(ms, function () { this.tone({ type: 'square', freq: 260, freqEnd: 180, dur: 0.07, gain: 0.08 * vol }); });
      }, this);
    });
    GA.register('ss_twist_sugar_rush', function (vol) {
      [523, 659, 784, 1046, 1318, 1568, 2093].forEach(function (f, i) {
        this.later(i * 45, function () { this.tone({ type: 'triangle', freq: f, dur: 0.12, gain: 0.09 * vol }); });
      }, this);
      this.later(330, function () { this.tone({ type: 'sine', freq: 600, freqEnd: 1800, dur: 0.4, gain: 0.08 * vol }); });
    });
    GA.register('ss_twist_drop', function (vol) {
      this.noise({ filter: 'highpass', freq: 400, freqEnd: 6000, dur: 0.7, gain: 0.16 * vol });
      this.later(700, function () {
        this.tone({ type: 'sine', freq: 150, freqEnd: 40, dur: 0.4, gain: 0.5 * vol });
        this.tone({ type: 'sawtooth', freq: 55, dur: 0.6, gain: 0.08 * vol });
      });
    });
    GA.register('ss_twist_typhoon', function (vol) {
      this.noise({ filter: 'bandpass', freq: 300, freqEnd: 1100, dur: 1.2, gain: 0.3 * vol });
      this.later(900, function () { this.noise({ filter: 'bandpass', freq: 1100, freqEnd: 260, dur: 1.3, gain: 0.25 * vol }); });
    });
    // for the arrival scenes
    GA.register('ss_clank', function (vol) {
      [310, 466, 622].forEach(function (f) { this.tone({ type: 'square', freq: f, freqEnd: f * 0.96, dur: 0.22, gain: 0.05 * vol }); }, this);
      this.noise({ filter: 'bandpass', freq: 2400, dur: 0.06, gain: 0.25 * vol });
    });
    GA.register('ss_hiss', function (vol) {
      this.noise({ filter: 'highpass', freq: 2600, freqEnd: 5200, dur: 1.2, gain: 0.16 * vol });
    });
    GA.register('ss_pop', function (vol) {
      this.tone({ type: 'sine', freq: 520, freqEnd: 1500, dur: 0.06, gain: 0.2 * vol });
    });
    GA.register('ss_kick', function (vol) {
      this.tone({ type: 'sine', freq: 140, freqEnd: 40, dur: 0.24, gain: 0.5 * vol });
      this.noise({ filter: 'lowpass', freq: 600, dur: 0.03, gain: 0.2 * vol });
    });
    GA.register('ss_synth', function (vol) {
      [220, 262, 330, 440, 330, 262, 220, 196].forEach(function (f, i) {
        this.later(i * 125, function () { this.tone({ type: 'sawtooth', freq: f * 2, dur: 0.11, gain: 0.045 * vol }); });
      }, this);
    });
    GA.register('ss_gong', function (vol) {
      [[110, 0.3], [167, 0.12], [233, 0.08], [331, 0.05]].forEach(function (p) {
        this.tone({ type: 'sine', freq: p[0], freqEnd: p[0] * 0.98, dur: 3.2, gain: p[1] * vol });
      }, this);
      this.noise({ filter: 'lowpass', freq: 800, freqEnd: 120, dur: 0.6, gain: 0.25 * vol });
    });
    GA.register('ss_chime', function (vol) {
      [1175, 1319, 1568, 1760, 2093].forEach(function (f, i) {
        this.later(i * 110, function () { this.tone({ type: 'triangle', freq: f, dur: 0.6, gain: 0.05 * vol }); });
      }, this);
    });
  }

  // =================================================== arrival scenes
  var Intro = global.AreaIntro;
  if (!Intro) return;
  var K = Intro.kit;
  var VW = K.VW, VH = K.VH, TAU = K.TAU, HEAVY = K.HEAVY;
  var seg = K.seg, lerp = K.lerp, outCubic = K.outCubic, outBack = K.outBack, inOut = K.inOut;
  var dot = K.dot, additive = K.additive, roundRect = K.roundRect, fitSize = K.fitSize;
  var between = K.between, wobble = K.wobble, makeStars = K.makeStars, stars = K.stars;
  var SKIN = '#f5cd30', TORSO = '#c4281c', LEGS = '#0d69ac';

  /* A racer in the classic colours -- yellow head and arms, red torso,
     blue legs -- running, or tucked for a jump; (x, y) is the feet. */
  function racer(ctx, x, y, s, t, phase, air, face) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s * (face || 1), s);
    var swing = air ? 0.7 : Math.sin(t * 14 + phase) * 0.75;
    function limb(px, py, w, h, ang, colour) {
      ctx.save(); ctx.translate(px, py); ctx.rotate(ang);
      ctx.fillStyle = colour; ctx.fillRect(-w / 2, 0, w, h);
      ctx.restore();
    }
    limb(-7, -40, 13, 40, air ? -0.9 : swing, LEGS);
    limb(7, -40, 13, 40, air ? 0.5 : -swing, LEGS);
    limb(-21, -79, 11, 37, air ? -2.1 : -swing * 0.9, SKIN);
    ctx.fillStyle = TORSO; ctx.fillRect(-15, -81, 30, 43);
    limb(21, -79, 11, 37, air ? 2.1 : swing * 0.9, SKIN);
    ctx.fillStyle = SKIN; roundRect(ctx, -12, -107, 24, 25, 6); ctx.fill();
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(-6, -99, 3, 5); ctx.fillRect(4, -99, 3, 5);
    ctx.strokeStyle = '#1a1a1a'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(1, -93, 5, 0.25, Math.PI - 0.25); ctx.stroke();
    ctx.restore();
  }

  function titleText(ctx, text, x, y, max, size0, fill, stroke, lw, font) {
    var size = fitSize(ctx, text, 'bold #px ' + (font || HEAVY), size0 || 110, max, 0.04);
    ctx.font = 'bold ' + size + 'px ' + (font || HEAVY);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round';
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw || 10; ctx.strokeText(text, x, y); }
    ctx.fillStyle = fill;
    ctx.fillText(text, x, y);
    ctx.textAlign = 'left';
    return size;
  }

  // ------------------------------------------------ The Foundry
  Intro.register('ss_foundry', {
    name: 'The Foundry',
    tagline: 'Over the pour, along the girders, under the hammers -- and do not touch the steel.',
    accent: '#ff8a2a',
    cues: [[0.3, 'ss_clank', 0.6], [0.9, 'ss_hiss', 0.5], [1.75, 'ss_thwack', 0.9], [2.5, 'ss_clank', 0.7],
           [3.35, 'ss_thwack', 0.8], [4.2, 'ss_go', 0.6]],
    shakes: [[1.75, 6, 0.4], [3.35, 4, 0.35]],
    tagY: 560, tagAt: 3.5,
    setup: function (r) {
      var d = { sparks: [], stacks: [], smoke: [] };
      for (var i = 0; i < 70; i++) d.sparks.push([between(r, -1, 1), between(r, 0.3, 1), between(r, 0, 2), between(r, 2, 5)]);
      for (var s = 0; s < 6; s++) d.stacks.push([120 + s * 260 + between(r, -40, 40), between(r, 160, 320), between(r, 40, 70)]);
      for (var m = 0; m < 30; m++) d.smoke.push([between(r, 0, 6), between(r, 0, 1), between(r, 30, 80)]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, VH);
      sky.addColorStop(0, '#120a0a'); sky.addColorStop(0.55, '#4a1e10'); sky.addColorStop(1, '#a0441a');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      // the stacks and their smoke
      d.stacks.forEach(function (st, i) {
        ctx.fillStyle = '#1a0e0c';
        ctx.fillRect(st[0] - st[2] / 2, st[1], st[2], VH - st[1]);
        ctx.fillStyle = '#c8a030'; ctx.fillRect(st[0] - st[2] / 2, st[1] + 30, st[2], 8);
        d.smoke.forEach(function (sm, k) {
          if (k % d.stacks.length !== i) return;
          var age = (t * 0.5 + sm[1] * 3) % 3;
          ctx.fillStyle = 'rgba(60,40,36,' + (0.5 * (1 - age / 3)) + ')';
          ctx.beginPath(); ctx.arc(st[0] + age * 40, st[1] - age * 90, sm[2] * (0.4 + age / 3), 0, TAU); ctx.fill();
        });
      });
      // the works: a long shed, its windows glowing
      ctx.fillStyle = '#140c0a'; ctx.fillRect(0, 560, VW, 340);
      for (var w = 0; w < 22; w++) {
        ctx.fillStyle = 'rgba(255,150,60,' + (0.55 + 0.25 * Math.sin(t * 3 + w)) + ')';
        ctx.fillRect(30 + w * 72, 600, 40, 26);
      }
      // the ladle tipping, the pour, the mould glowing
      var tip = inOut(seg(t, 0.4, 1.4)) * 0.75;
      ctx.save(); ctx.translate(1150, 330); ctx.rotate(tip);
      ctx.fillStyle = '#3a2e2a'; ctx.beginPath(); ctx.moveTo(-90, -60); ctx.lineTo(90, -60); ctx.lineTo(70, 70); ctx.lineTo(-70, 70); ctx.fill();
      ctx.fillStyle = '#ffb040'; ctx.fillRect(-84, -62, 168, 12);
      ctx.restore();
      ctx.fillStyle = '#2a2420'; ctx.fillRect(1146, 120, 8, 170);
      if (t > 1.1) {
        var pour = seg(t, 1.1, 1.5);
        additive(ctx, function () {
          var g = ctx.createLinearGradient(1230, 300, 1240, 640);
          g.addColorStop(0, '#fff2a0'); g.addColorStop(1, '#ff6a1a');
          ctx.fillStyle = g;
          ctx.fillRect(1226 + Math.sin(t * 20) * 2, 300, 20, 340 * pour);
          dot(ctx, '#ff8a2a', 1236, 650, 160, 0.7 * pour);
        });
      }
      ctx.fillStyle = '#ff7a20'; ctx.fillRect(1120, 640, 240, 20);
      // sparks spraying off the pour
      if (t > 1.2) {
        additive(ctx, function () {
          d.sparks.forEach(function (s) {
            var age = (t - 1.2 + s[2]) % 1.4;
            var x = 1236 + s[0] * 260 * age, y = 640 - s[1] * 320 * age + 380 * age * age;
            ctx.fillStyle = 'rgba(255,' + Math.round(180 + 70 * s[1]) + ',90,' + (1 - age / 1.4) + ')';
            ctx.fillRect(x, y, s[3], s[3]);
          });
        });
      }
      // girders across the foreground, a racer leaping between them
      ctx.fillStyle = '#2a2a30';
      ctx.fillRect(0, 760, 520, 40); ctx.fillRect(760, 720, 840, 40);
      ctx.fillStyle = '#e8b830';
      for (var g2 = 0; g2 < 13; g2++) ctx.fillRect(g2 * 40, 760, 20, 8);
      for (var g3 = 0; g3 < 21; g3++) ctx.fillRect(760 + g3 * 40, 720, 20, 8);
      var leap = seg(t, 1.9, 2.9);
      var rx = leap > 0 ? lerp(420, 860, leap) : lerp(120, 420, seg(t, 0.4, 1.9));
      var ry = leap > 0 ? lerp(760, 720, leap) - Math.sin(leap * Math.PI) * 180 : 760;
      if (t > 2.9) { rx = lerp(860, 1700, seg(t, 2.9, 5)); ry = 720; }
      racer(ctx, rx, ry, 1.05, t, 0, leap > 0 && leap < 1);
      // the hammer swinging through
      var a = Math.sin((t - 1.0) * 2.1) * 1.0;
      ctx.save(); ctx.translate(600, -40); ctx.rotate(-a);
      ctx.fillStyle = '#5a5e66'; ctx.fillRect(-10, 0, 20, 560);
      ctx.fillStyle = '#3a3e44'; ctx.fillRect(-90, 540, 180, 140);
      ctx.fillStyle = '#e8b830'; ctx.fillRect(-90, 540, 180, 40); ctx.fillRect(-90, 640, 180, 40);
      ctx.restore();
    },
    title: function (ctx, t, d, run) {
      // a steel plate slammed down, hazard-striped and riveted, the name stamped in it
      var at = 1.7, k = outBack(seg(t, at, at + 0.35), 1.6);
      ctx.save();
      ctx.translate(800, 250 - (1 - k) * 420);
      ctx.rotate(-0.025 + wobble(t, at + 0.35, 0.03, 18, 5));
      ctx.fillStyle = '#4a4e56'; roundRect(ctx, -540, -125, 1080, 250, 10); ctx.fill();
      ctx.save(); roundRect(ctx, -540, -125, 1080, 250, 10); ctx.clip();
      for (var s = -14; s < 16; s++) {
        ctx.fillStyle = s % 2 ? '#1e1e22' : '#e8b830';
        ctx.beginPath(); ctx.moveTo(s * 40, -125); ctx.lineTo(s * 40 + 40, -125); ctx.lineTo(s * 40, -95); ctx.lineTo(s * 40 - 40, -95); ctx.fill();
        ctx.beginPath(); ctx.moveTo(s * 40, 95); ctx.lineTo(s * 40 + 40, 95); ctx.lineTo(s * 40, 125); ctx.lineTo(s * 40 - 40, 125); ctx.fill();
      }
      ctx.restore();
      ctx.fillStyle = '#8a8e96';
      [[-510, -70], [510, -70], [-510, 70], [510, 70]].forEach(function (rv) {
        ctx.beginPath(); ctx.arc(rv[0], rv[1], 10, 0, TAU); ctx.fill();
      });
      ctx.globalAlpha = run.alpha;
      ctx.font = 'bold 26px ' + HEAVY; ctx.textAlign = 'center'; ctx.fillStyle = '#e8b830';
      ctx.fillText('SKY SPRINT', 0, -62);
      titleText(ctx, (run.info.name || 'The Foundry').toUpperCase(), 0, 18, 920, 104, '#ffd07a', '#1e1e22', 10);
      var glow = 1 - seg(t, at + 0.3, at + 1.6);
      if (glow > 0) {
        ctx.globalAlpha = run.alpha * glow;
        titleText(ctx, (run.info.name || 'The Foundry').toUpperCase(), 0, 18, 920, 104, '#ff6a1a');
      }
      ctx.restore();
    }
  });

  // ------------------------------------------------ Candy Clouds
  Intro.register('ss_candy', {
    name: 'Candy Clouds',
    tagline: 'Bounce the jelly, wade the taffy, and mind the lollipops on the way to the cake.',
    accent: '#ff7ac8',
    cues: [[0.3, 'ss_pop', 0.6], [0.55, 'ss_pop', 0.5], [0.8, 'ss_pop', 0.6], [1.5, 'ss_jelly', 0.8],
           [2.4, 'ss_boing', 0.8], [3.0, 'ss_twist_sugar_rush', 0.6], [4.1, 'ss_pop', 0.5]],
    shakes: [],
    tagY: 560, tagAt: 3.4,
    setup: function (r) {
      var d = { clouds: [], drops: [], hills: [] };
      for (var i = 0; i < 9; i++) d.clouds.push([between(r, -100, VW), between(r, 60, 420), between(r, 60, 130), between(r, 8, 22)]);
      for (var s = 0; s < 120; s++) d.drops.push([between(r, 0, VW), between(r, 0, VH), between(r, 0, TAU), Math.floor(between(r, 0, 5))]);
      for (var h = 0; h < 7; h++) d.hills.push([h * 260 + between(r, -40, 40), between(r, 120, 220)]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, VH);
      sky.addColorStop(0, '#ffb8e0'); sky.addColorStop(0.5, '#ffd8c0'); sky.addColorStop(1, '#c8f0e0');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      // cotton-candy clouds drifting
      d.clouds.forEach(function (c, i) {
        var x = (c[0] + t * c[3]) % (VW + 300) - 150;
        ctx.fillStyle = i % 2 ? 'rgba(255,214,240,0.92)' : 'rgba(214,236,255,0.92)';
        for (var p = 0; p < 5; p++) {
          ctx.beginPath(); ctx.arc(x + (p - 2) * c[2] * 0.42, c[1] - Math.sin(p * 1.3) * c[2] * 0.25, c[2] * (0.38 + 0.12 * Math.sin(p * 2.1)), 0, TAU); ctx.fill();
        }
      });
      // gumdrop hills and candy-cane posts
      var gum = ['#ff5a8a', '#7ad8ff', '#b8ff7a', '#ffd84a', '#c88aff'];
      d.hills.forEach(function (h, i) {
        ctx.fillStyle = gum[i % gum.length];
        ctx.beginPath(); ctx.ellipse(h[0], 900, 170, h[1] + 80, 0, Math.PI, 0); ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.35)';
        ctx.beginPath(); ctx.ellipse(h[0] - 50, 900 - h[1] * 0.75, 30, 16, -0.4, 0, TAU); ctx.fill();
      });
      // the chocolate river
      ctx.fillStyle = '#6a3a1e';
      ctx.beginPath(); ctx.moveTo(0, 820); ctx.quadraticCurveTo(800, 760 + Math.sin(t * 2) * 6, VW, 830); ctx.lineTo(VW, VH); ctx.lineTo(0, VH); ctx.fill();
      ctx.strokeStyle = 'rgba(160,100,60,0.6)'; ctx.lineWidth = 3;
      for (var wv = 0; wv < 8; wv++) {
        var wx = (wv * 230 + t * 60) % (VW + 100) - 50;
        ctx.beginPath(); ctx.moveTo(wx, 850); ctx.quadraticCurveTo(wx + 30, 842, wx + 60, 850); ctx.stroke();
      }
      // the great swirl lollipop
      ctx.fillStyle = '#ffffff'; ctx.fillRect(296, 380, 18, 460);
      ctx.save(); ctx.translate(305, 330); ctx.rotate(t * 1.4);
      for (var ring = 0; ring < 6; ring++) {
        ctx.fillStyle = ring % 2 ? '#ffffff' : '#ff3a7a';
        ctx.beginPath(); ctx.arc(0, 0, 120 - ring * 20, ring * 0.6, ring * 0.6 + TAU * 0.98); ctx.lineTo(0, 0); ctx.fill();
      }
      ctx.restore();
      // a jelly block, a racer bouncing off it
      var hop = (t * 0.9) % 1;
      var squash = hop < 0.12 ? Math.sin(hop / 0.12 * Math.PI) : 0;
      ctx.save(); ctx.translate(1180, 780);
      ctx.scale(1 + squash * 0.18, 1 - squash * 0.22);
      ctx.fillStyle = 'rgba(232,58,90,0.85)'; roundRect(ctx, -130, -120, 260, 120, 22); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,0.35)'; roundRect(ctx, -110, -110, 120, 26, 12); ctx.fill();
      ctx.restore();
      var y = 780 - 120 * (1 - squash * 0.22) - Math.sin(hop * Math.PI) * 300;
      racer(ctx, 1180, y, 1.1, t, 0, hop > 0.12, 1);
      // sprinkles raining
      var colours = ['#ff3a7a', '#3ab0ff', '#ffe03a', '#7aff5a', '#ffffff'];
      d.drops.forEach(function (s) {
        var yy = (s[1] + t * 220) % VH;
        ctx.save(); ctx.translate(s[0] + Math.sin(t + s[2]) * 10, yy); ctx.rotate(s[2] + t * 3);
        ctx.fillStyle = colours[s[3]]; roundRect(ctx, -7, -2.5, 14, 5, 2.5); ctx.fill();
        ctx.restore();
      });
    },
    title: function (ctx, t, d, run) {
      // the name in bubbly candy letters, each one bouncing in
      var name = (run.info.name || 'Candy Clouds').toUpperCase();
      ctx.save();
      ctx.translate(800, 240);
      ctx.globalAlpha = run.alpha * seg(t, 1.0, 1.3);
      ctx.font = 'bold 30px ' + HEAVY; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.lineWidth = 8; ctx.strokeStyle = '#ffffff'; ctx.strokeText('SKY SPRINT', 0, -96);
      ctx.fillStyle = '#ff3a7a'; ctx.fillText('SKY SPRINT', 0, -96);
      var size = fitSize(ctx, name, 'bold #px ' + HEAVY, 120, 1000, 0.06);
      ctx.font = 'bold ' + size + 'px ' + HEAVY;
      var widths = name.split('').map(function (ch) { return ctx.measureText(ch).width + size * 0.06; });
      var total = widths.reduce(function (a, b) { return a + b; }, 0);
      var x = -total / 2;
      var fills = ['#ff5aa0', '#7ac8ff', '#ffd84a', '#8ae85a', '#c88aff'];
      name.split('').forEach(function (ch, i) {
        var at = 1.2 + i * 0.07, k = outBack(seg(t, at, at + 0.45), 2.2);
        var cx = x + widths[i] / 2;
        x += widths[i];
        if (k <= 0 || ch === ' ') return;
        var bob = Math.sin(t * 4 + i * 0.7) * 5 * seg(t, at + 0.5, at + 1);
        ctx.save();
        ctx.translate(cx, 20 + bob + (1 - k) * -60);
        ctx.scale(k, k);
        ctx.globalAlpha = run.alpha;
        ctx.lineJoin = 'round';
        ctx.lineWidth = 16; ctx.strokeStyle = '#8a2a5a'; ctx.strokeText(ch, 0, 6);
        ctx.lineWidth = 10; ctx.strokeStyle = '#ffffff'; ctx.strokeText(ch, 0, 0);
        ctx.fillStyle = fills[i % fills.length]; ctx.fillText(ch, 0, 0);
        ctx.fillStyle = 'rgba(255,255,255,0.45)';
        ctx.fillRect(-widths[i] * 0.22, -size * 0.3, widths[i] * 0.16, size * 0.18);
        ctx.restore();
      });
      ctx.restore();
    }
  });

  // ------------------------------------------------ Neon Grid
  Intro.register('ss_neon', {
    name: 'Neon Grid',
    tagline: 'Ride the beat. The floor blinks, the lasers sweep, and the drop is coming.',
    accent: '#3ad8ff',
    cues: [[0.25, 'ss_kick', 0.8], [0.75, 'ss_kick', 0.8], [1.0, 'ss_synth', 0.6], [1.25, 'ss_kick', 0.8],
           [1.75, 'ss_kick', 0.8], [2.0, 'ss_zap', 0.5], [2.25, 'ss_kick', 0.9], [2.6, 'ss_twist_drop', 0.8],
           [3.3, 'ss_kick', 0.9], [3.8, 'ss_kick', 0.9], [4.3, 'ss_kick', 0.9]],
    shakes: [[3.3, 4, 0.3]],
    tagY: 560, tagAt: 3.5,
    setup: function (r) {
      var d = { stars: makeStars(r, 90, 0, 360), city: [] };
      for (var i = 0; i < 34; i++) d.city.push([i * 50 + between(r, -10, 10), between(r, 80, 260), between(r, 36, 60), Math.floor(between(r, 0, 3))]);
      return d;
    },
    draw: function (ctx, t, d) {
      var beat = (t - 0.25) % 0.5, hit = t > 0.25 ? Math.pow(1 - beat / 0.5, 4) : 0;
      if (t > 3.3) hit *= 1.6;
      var sky = ctx.createLinearGradient(0, 0, 0, 520);
      sky.addColorStop(0, '#0a0420'); sky.addColorStop(0.7, '#3a0a4a'); sky.addColorStop(1, '#ff3a8a');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, 520);
      stars(ctx, d.stars, t, 0.8);
      // the striped sun
      var sunY = 430 - 30 * outCubic(seg(t, 0, 2));
      ctx.save();
      ctx.beginPath(); ctx.arc(800, sunY, 210, 0, TAU); ctx.clip();
      var sg = ctx.createLinearGradient(0, sunY - 210, 0, sunY + 210);
      sg.addColorStop(0, '#ffe83a'); sg.addColorStop(0.6, '#ff6a3a'); sg.addColorStop(1, '#ff2a8a');
      ctx.fillStyle = sg; ctx.fillRect(590, sunY - 210, 420, 420);
      ctx.fillStyle = '#3a0a4a';
      for (var b = 0; b < 7; b++) ctx.fillRect(590, sunY + 10 + b * 28 - (t * 20) % 28, 420, 6 + b * 1.6);
      ctx.restore();
      // the city against it
      d.city.forEach(function (c) {
        ctx.fillStyle = '#12061e';
        ctx.fillRect(c[0], 520 - c[1], c[2], c[1]);
        var hue = ['#3ad8ff', '#ff3ad8', '#ffe83a'][c[3]];
        ctx.fillStyle = hue;
        ctx.globalAlpha = 0.5 + 0.5 * hit;
        ctx.fillRect(c[0], 520 - c[1], c[2], 3);
        ctx.globalAlpha = 1;
        for (var wy = 520 - c[1] + 14; wy < 510; wy += 18) {
          if (Math.sin(wy * 1.7 + c[0]) > 0.4) { ctx.fillStyle = 'rgba(255,220,255,0.35)'; ctx.fillRect(c[0] + 8, wy, 6, 6); }
        }
      });
      // the grid running at us
      ctx.fillStyle = '#0a0418'; ctx.fillRect(0, 520, VW, VH - 520);
      additive(ctx, function () {
        ctx.strokeStyle = 'rgba(58,216,255,' + (0.55 + 0.45 * hit) + ')';
        ctx.lineWidth = 2;
        for (var gx = -20; gx <= 20; gx++) {
          ctx.beginPath(); ctx.moveTo(800 + gx * 14, 520); ctx.lineTo(800 + gx * 160, VH); ctx.stroke();
        }
        var scroll = (t * 1.4) % 1;
        for (var gz = 0; gz < 14; gz++) {
          var k = Math.pow((gz + scroll) / 14, 2.2);
          var y = 520 + k * (VH - 520);
          ctx.globalAlpha = Math.min(1, k * 3);
          ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(VW, y); ctx.stroke();
        }
        ctx.globalAlpha = 1;
        // two lasers sweeping the floor
        [0, 1].forEach(function (n) {
          var lx = 800 + Math.sin(t * 2.2 + n * 2.4) * 520;
          ctx.strokeStyle = 'rgba(255,42,74,0.9)'; ctx.lineWidth = 4;
          ctx.beginPath(); ctx.moveTo(lx, 520); ctx.lineTo(lx + (lx - 800) * 0.8, VH); ctx.stroke();
          dot(ctx, '#ff2a4a', lx, 520, 40, 0.8);
        });
      });
      // a racer sprinting along the grid, speed lines behind them
      var rx = lerp(-120, 1720, seg(t, 0.6, 5.4));
      ctx.strokeStyle = 'rgba(58,216,255,0.6)'; ctx.lineWidth = 3;
      for (var sl = 0; sl < 5; sl++) {
        ctx.beginPath(); ctx.moveTo(rx - 40 - sl * 20, 760 - sl * 22); ctx.lineTo(rx - 160 - sl * 30, 760 - sl * 22); ctx.stroke();
      }
      racer(ctx, rx, 830, 1.15, t * 1.4, 0, false);
      // the beat, flashing the screen
      if (hit > 0.05) {
        ctx.fillStyle = 'rgba(255,58,216,' + (0.12 * hit) + ')';
        ctx.fillRect(0, 0, VW, VH);
      }
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Neon Grid').toUpperCase();
      ctx.save();
      ctx.translate(800, 230);
      // chrome kicker
      ctx.globalAlpha = run.alpha * seg(t, 0.9, 1.2);
      ctx.font = 'italic bold 34px ' + HEAVY; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      var cg = ctx.createLinearGradient(0, -120, 0, -80);
      cg.addColorStop(0, '#ffffff'); cg.addColorStop(0.5, '#8ac8ff'); cg.addColorStop(0.52, '#3a2a6a'); cg.addColorStop(1, '#ff8ad8');
      ctx.fillStyle = cg; ctx.fillText('SKY SPRINT', 0, -100);
      // the name as neon tube, sputtering on
      var on = K.sputter(t, 1.3, 4) * (t > 2.6 && t < 2.75 ? 0.2 : 1);
      ctx.globalAlpha = run.alpha * (0.15 + 0.85 * on);
      var size = fitSize(ctx, name, 'bold #px ' + HEAVY, 120, 980, 0.04);
      ctx.font = 'bold ' + size + 'px ' + HEAVY;
      ctx.lineJoin = 'round';
      ctx.shadowColor = '#ff3ad8'; ctx.shadowBlur = 40 * on;
      ctx.strokeStyle = '#ff3ad8'; ctx.lineWidth = 10; ctx.strokeText(name, 0, 10);
      ctx.shadowColor = '#3ad8ff'; ctx.shadowBlur = 20 * on;
      ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 3; ctx.strokeText(name, 0, 10);
      ctx.shadowBlur = 0;
      ctx.restore();
    }
  });

  // ------------------------------------------------ Jade Temple
  Intro.register('ss_jade', {
    name: 'Jade Temple',
    tagline: 'Up through the clouds to the temple bell -- and the wind wants you off the bridges.',
    accent: '#5ad8a0',
    cues: [[0.3, 'ss_chime', 0.6], [1.0, 'ss_twist_typhoon', 0.35], [2.1, 'ss_gong', 0.9], [3.4, 'ss_chime', 0.5]],
    shakes: [[2.1, 3, 0.5]],
    tagY: 560, tagAt: 3.4,
    setup: function (r) {
      var d = { petals: [], cranes: [], peaks: [] };
      for (var i = 0; i < 60; i++) d.petals.push([between(r, 0, VW), between(r, 0, VH), between(r, 0, TAU), between(r, 0.6, 1.4)]);
      for (var c = 0; c < 4; c++) d.cranes.push([between(r, 0, 1), between(r, 120, 300), between(r, 0.8, 1.2)]);
      for (var p = 0; p < 4; p++) {
        var row = [];
        for (var k = 0; k < 7; k++) row.push([k * 280 + between(r, -60, 60), between(r, 120, 260) + p * 60]);
        d.peaks.push(row);
      }
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, VH);
      sky.addColorStop(0, '#f8d890'); sky.addColorStop(0.45, '#f8b8a0'); sky.addColorStop(1, '#a8e0d0');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      additive(ctx, function () { dot(ctx, '#fff0c0', 1240, 230, 220, 0.6); });
      ctx.fillStyle = '#fff4d8'; ctx.beginPath(); ctx.arc(1240, 230, 70, 0, TAU); ctx.fill();
      // the ranges, far to near, in wash
      var tones = ['#b8c8c0', '#8aa8a0', '#5a8a80', '#2a5a50'];
      d.peaks.forEach(function (row, depth) {
        ctx.fillStyle = tones[depth];
        var drift = t * (4 + depth * 6);
        row.forEach(function (pk) {
          var x = (pk[0] - drift + VW + 300) % (VW + 300) - 150;
          var top = 360 + pk[1] * 0.6 + depth * 40;
          ctx.beginPath(); ctx.moveTo(x - 220, VH); ctx.quadraticCurveTo(x - 40, top + 40, x, top);
          ctx.quadraticCurveTo(x + 40, top + 40, x + 220, VH); ctx.fill();
        });
        // a band of cloud between each range
        ctx.fillStyle = 'rgba(255,255,255,' + (0.35 + depth * 0.1) + ')';
        for (var c = 0; c < 9; c++) {
          var cx = (c * 210 + t * (10 + depth * 8)) % (VW + 200) - 100;
          ctx.beginPath(); ctx.ellipse(cx, 640 + depth * 60, 160, 34, 0, 0, TAU); ctx.fill();
        }
      });
      // the temple on its peak, the bell in its tower
      ctx.fillStyle = '#1e3a34';
      ctx.beginPath(); ctx.moveTo(560, VH); ctx.lineTo(800, 470); ctx.lineTo(1040, VH); ctx.fill();
      for (var tier = 0; tier < 4; tier++) {
        var w = 220 - tier * 44, y = 470 - tier * 62;
        ctx.fillStyle = '#b8202a'; ctx.fillRect(800 - w / 2 + 16, y - 50, w - 32, 50);
        ctx.fillStyle = '#1a2a24';
        ctx.beginPath(); ctx.moveTo(800 - w / 2 - 30, y - 44); ctx.quadraticCurveTo(800, y - 70, 800 + w / 2 + 30, y - 44);
        ctx.lineTo(800 + w / 2 - 10, y - 62); ctx.lineTo(800 - w / 2 + 10, y - 62); ctx.fill();
        ctx.fillStyle = '#e8b830'; ctx.fillRect(800 - w / 2 + 16, y - 6, w - 32, 6);
      }
      ctx.fillStyle = '#e8b830'; ctx.fillRect(796, 166, 8, 40);
      var ring = seg(t, 2.1, 2.2) * (1 - seg(t, 2.2, 3.4));
      if (ring > 0) {
        ctx.strokeStyle = 'rgba(255,230,160,' + ring + ')'; ctx.lineWidth = 4;
        for (var rr = 0; rr < 3; rr++) {
          ctx.beginPath(); ctx.arc(800, 280, 60 + rr * 50 + (t - 2.1) * 220, 0, TAU); ctx.stroke();
        }
      }
      // the rope bridge between two near peaks, a racer crossing in the wind
      ctx.fillStyle = '#163028';
      ctx.beginPath(); ctx.moveTo(-40, VH); ctx.lineTo(160, 640); ctx.lineTo(330, VH); ctx.fill();
      ctx.beginPath(); ctx.moveTo(1270, VH); ctx.lineTo(1450, 620); ctx.lineTo(1640, VH); ctx.fill();
      var sway = Math.sin(t * 3) * 10 * (0.4 + seg(t, 1.0, 2.0));
      ctx.strokeStyle = '#6a4a2a'; ctx.lineWidth = 5;
      ctx.beginPath(); ctx.moveTo(170, 650); ctx.quadraticCurveTo(800, 760 + sway, 1440, 630); ctx.stroke();
      ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(170, 610); ctx.quadraticCurveTo(800, 716 + sway, 1440, 590); ctx.stroke();
      for (var pl = 0; pl < 30; pl++) {
        var u = (pl + 0.5) / 30, bx = lerp(170, 1440, u);
        var by = (1 - u) * (1 - u) * 650 + 2 * u * (1 - u) * (760 + sway) + u * u * 630;
        ctx.fillStyle = '#8a6a3a'; ctx.fillRect(bx - 18, by - 3, 36, 8);
      }
      var cu = seg(t, 0.3, 5.6);
      var cx2 = lerp(170, 1440, cu), cy2 = (1 - cu) * (1 - cu) * 650 + 2 * cu * (1 - cu) * (760 + sway) + cu * cu * 630;
      racer(ctx, cx2 + Math.sin(t * 2.4) * 6, cy2 - 3, 0.9, t, 0, false);
      // cranes flying
      d.cranes.forEach(function (c, i) {
        var x = ((c[0] * VW + t * 90 * c[2]) % (VW + 200)) - 100, y = c[1] + Math.sin(t * 1.4 + i) * 12;
        var flap = Math.sin(t * 6 + i) * 18;
        ctx.strokeStyle = '#f8f4ec'; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.moveTo(x - 36, y - flap); ctx.quadraticCurveTo(x - 10, y - 8, x, y); ctx.quadraticCurveTo(x + 10, y - 8, x + 36, y - flap); ctx.stroke();
        ctx.fillStyle = '#c8202a'; ctx.fillRect(x + 4, y - 3, 6, 4);
      });
      // petals on the wind
      d.petals.forEach(function (p) {
        var x = (p[0] + t * 120 * p[3]) % (VW + 40) - 20, y = (p[1] + t * 40 + Math.sin(t * 2 + p[2]) * 20) % VH;
        ctx.save(); ctx.translate(x, y); ctx.rotate(p[2] + t * 2);
        ctx.fillStyle = 'rgba(255,184,208,0.9)';
        ctx.beginPath(); ctx.ellipse(0, 0, 8, 4, 0, 0, TAU); ctx.fill();
        ctx.restore();
      });
    },
    title: function (ctx, t, d, run) {
      // a red lacquer board on cords, swinging from the strike of the gong
      var at = 1.4, k = outCubic(seg(t, at, at + 0.6));
      var swing = wobble(t, 2.1, 0.05, 6, 1.6) + Math.sin(t * 1.3) * 0.006;
      ctx.save();
      ctx.translate(800, 40);
      ctx.rotate(swing);
      ctx.globalAlpha = run.alpha * k;
      ctx.strokeStyle = '#3a2a1a'; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(-300, 0); ctx.lineTo(-420, 110 + (1 - k) * -80); ctx.moveTo(300, 0); ctx.lineTo(420, 110 + (1 - k) * -80); ctx.stroke();
      ctx.translate(0, 210 - (1 - k) * 80);
      ctx.fillStyle = '#9a1a22'; roundRect(ctx, -530, -100, 1060, 200, 14); ctx.fill();
      ctx.strokeStyle = '#e8b830'; ctx.lineWidth = 6; roundRect(ctx, -510, -82, 1020, 164, 8); ctx.stroke();
      ctx.lineWidth = 2; roundRect(ctx, -496, -68, 992, 136, 6); ctx.stroke();
      ctx.font = 'bold 24px ' + HEAVY; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillStyle = '#f8d890'; ctx.fillText('SKY SPRINT', 0, -48);
      titleText(ctx, (run.info.name || 'Jade Temple').toUpperCase(), 0, 16, 900, 96, '#f8d060', '#5a0a10', 8,
                'Georgia, "Times New Roman", serif');
      ctx.restore();
    }
  });
})(window);
