/* Rail Rivals' moving scenery and its weather ("rigs": static/js/game/rigs.js).

   A railroad names what moves on it in markers.extra.rigs (ArenaArea.rig()),
   and the plugin (rail_rivals.js) builds them with Rigs.build and draws them
   every frame.  Nothing here collides or reaches the server.

     rr_weather      the sky round the camera: rain, a storm (rain and
                     lightning, a bolt now and then -- and the lightning rods
                     the map names take a strike every so often, at the same
                     moment on every screen), snow, dust, mist; never under a
                     roof
     rr_twister      a funnel cloud walking along the horizon
     rr_windpump     a farm windpump: the wheel, the tail, the pump rod
     rr_vane         a weathervane swinging with the wind
     rr_tumbleweed   one bowling across the prairie and back
     rr_clothesline  washing on a line
     rr_smoke        a chimney or a stack, smoking
     rr_flag         a flag at the top of a pole
     rr_order_board  a depot's train-order signal: its blades drop to clear
                     and its lamps go green while a train is on the main line
     rr_sounder      a telegraph sounder on the operator's desk, clicking
                     out the station's call -- and chattering when a train is
                     called down

   ctx (from the plugin): players(), viewer(), sound(name, at, volume),
   sound2d(name, volume), physics(), twist(). */
(function (global) {
  'use strict';
  var Rigs = global.Rigs;
  if (!Rigs) return;
  var frame = Rigs.frame, child = Rigs.child, hash = Rigs.hash;
  var approach = Rigs.approach, approachAngle = Rigs.approachAngle;
  var TAU = Math.PI * 2;

  function dist(a, b) { return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]); }
  function hexOf(r, g, b) {
    function two(v) { var n = Math.max(0, Math.min(255, Math.round(v * 255))); return (n < 16 ? '0' : '') + n.toString(16); }
    return '#' + two(r) + two(g) + two(b);
  }
  function flat(a, b) { return Math.hypot(a[0] - b[0], a[2] - b[2]); }

  // ============================================================= sounds
  var GA = global.GameAudio;
  if (GA && GA.register) {
    GA.register('rr_thunder', function (vol) {
      // the long roll of a strike far off
      this.noise({ freq: 320, freqEnd: 50, dur: 2.8, gain: 0.32 * vol });
      this.later(120, function () { this.noise({ freq: 800, freqEnd: 110, dur: 1.4, gain: 0.16 * vol }); });
      this.later(700, function () { this.noise({ freq: 260, freqEnd: 60, dur: 1.6, gain: 0.14 * vol }); });
      this.tone({ type: 'sawtooth', freq: 46, freqEnd: 28, dur: 2.0, gain: 0.05 * vol });
    });
    GA.register('rr_crack', function (vol) {
      // a strike close by: the crack, then the roll right behind it
      this.noise({ filter: 'highpass', freq: 2400, freqEnd: 600, dur: 0.18, gain: 0.5 * vol });
      this.noise({ freq: 1800, freqEnd: 200, dur: 0.5, gain: 0.4 * vol });
      this.later(160, function () { this.noise({ freq: 420, freqEnd: 50, dur: 2.6, gain: 0.36 * vol }); });
      this.tone({ type: 'square', freq: 90, freqEnd: 30, dur: 0.6, gain: 0.08 * vol });
    });
    GA.register('rr_rain', function (vol) {
      this.noise({ filter: 'highpass', freq: 2800, dur: 2.6, gain: 0.05 * vol });
      this.noise({ filter: 'bandpass', freq: 1100, dur: 2.4, gain: 0.03 * vol });
    });
    GA.register('rr_sounder', function (vol) {
      // the sounder's armature: click down, clack up
      this.noise({ filter: 'bandpass', freq: 3400, freqEnd: 2600, dur: 0.03, gain: 0.16 * vol });
      this.tone({ type: 'square', freq: 1500, freqEnd: 1300, dur: 0.025, gain: 0.03 * vol });
      this.later(70, function () {
        this.noise({ filter: 'bandpass', freq: 2200, freqEnd: 1800, dur: 0.03, gain: 0.12 * vol });
      });
    });
  }

  // ============================================================ weather
  var WEATHER = {
    rain:  { n: 220, fall: 80, size: [0.07, 2.6, 0.07], colour: '#b8cce0', a: 0.36, slant: 0.12, hiss: 1 },
    storm: { n: 260, fall: 92, size: [0.08, 3.0, 0.08], colour: '#c0d0e2', a: 0.4, slant: 0.24, hiss: 1,
             flash: [6, 15], bolts: 0.65 },
    snow:  { n: 170, fall: 8, size: [0.34, 0.34, 0.34], colour: '#ffffff', a: 0.9, drift: 1.6 },
    dust:  { n: 90, fall: 0.6, size: [0.16, 0.16, 0.16], colour: '#e8d0a0', a: 0.6, drift: 7.0 },
    mist:  { n: 40, fall: 0.2, size: [9.0, 2.6, 9.0], colour: '#eef2f4', a: 0.1, drift: 2.2, sph: 1 },
    embers: { n: 70, fall: -6, size: [0.22, 0.22, 0.22], colour: '#ffae4a', a: 0.95, glow: 1, drift: 2.4 }
  };

  /* A bolt: a jagged line of glowing rods from the cloud base to the
     ground, a fork or two off it, all of it fixed for its short life. */
  function makeBolt(top, ground, seed) {
    var pts = [top.slice()], n = 9, i;
    for (i = 1; i < n; i++) {
      var f = i / n;
      pts.push([top[0] + (ground[0] - top[0]) * f + (hash(seed + i) - 0.5) * 14,
                top[1] + (ground[1] - top[1]) * f,
                top[2] + (ground[2] - top[2]) * f + (hash(seed + i * 7) - 0.5) * 14]);
    }
    pts.push(ground.slice());
    var forks = [];
    for (i = 2; i < 6; i += 2) {
      if (hash(seed + i * 13) < 0.5) continue;
      var from = pts[i], len = 18 + hash(seed + i) * 20;
      var a = hash(seed + i * 3) * TAU;
      forks.push([from, [from[0] + Math.cos(a) * len * 0.6, from[1] - len, from[2] + Math.sin(a) * len * 0.6]]);
    }
    return { pts: pts, forks: forks };
  }

  function drawBolt(pen, bolt, lit) {
    var o = { m: 'neon', a: Math.min(1, lit) };
    for (var i = 0; i < bolt.pts.length - 1; i++) {
      pen.rod(bolt.pts[i], bolt.pts[i + 1], 0.9, '#eef2ff', o, 'box');
      pen.rod(bolt.pts[i], bolt.pts[i + 1], 3.2, '#9fb4ff', { m: 'neon', a: 0.18 * lit }, 'box');
    }
    bolt.forks.forEach(function (f) { pen.rod(f[0], f[1], 0.5, '#dce4ff', o, 'box'); });
  }

  Rigs.register('rr_weather', function (spec, ctx) {
    var kind = WEATHER[spec.weather] || null;
    if (!kind) return null;
    var drops = [];
    var roofs = { at: -10, eye: [1e9, 0, 1e9], cells: {} };
    var clock = 0, step = 1 / 60;
    var flash = { next: 4 + Math.random() * 5, at: -10, power: 0, bolt: null };
    var rods = spec.rods || [];
    var struck = -1;            // the last rod strike drawn (its slot)
    var ROD_EVERY = spec.rod_every || 47;

    function roofAt(x, z) {
      var y = roofs.cells[Math.round((x - roofs.eye[0]) / 8) + ',' + Math.round((z - roofs.eye[2]) / 8)];
      return y === undefined ? -1e9 : y;
    }
    function updateRoofs(at) {
      if (clock - roofs.at < 0.4 && Math.hypot(at[0] - roofs.eye[0], at[2] - roofs.eye[2]) < 4) return;
      roofs.at = clock;
      roofs.eye = at.slice();
      roofs.cells = {};
      var phys = ctx.physics ? ctx.physics() : null;
      if (!phys || !phys.rayDistance) return;
      for (var gx = -5; gx <= 5; gx++) {
        for (var gz = -5; gz <= 5; gz++) {
          var x = at[0] + gx * 8, z = at[2] + gz * 8, top = at[1] + 60;
          roofs.cells[gx + ',' + gz] = top - phys.rayDistance([x, top, z], [0, -1, 0], 160);
        }
      }
    }
    function thunder(at, from, power) {
      var d = from ? flat(at, from) : 500;
      var delay = Math.min(3000, d * 4.5);
      var close = d < 160;
      setTimeout(function () {
        if (ctx.sound2d) ctx.sound2d(close ? 'rr_crack' : 'rr_thunder', Math.max(0.25, Math.min(1, power * (close ? 1 : 0.6))));
      }, delay);
    }

    return {
      radius: 1e6,
      at: spec.p,
      update: function (dt) { clock += dt; step = Math.min(0.1, dt); },
      draw: function (pen, t) {
        var r = pen.r, eye = pen.eye || spec.p;
        // -- the rain (snow, dust) round the camera
        var target = kind.n;
        while (drops.length < target) {
          drops.push({ o: [(Math.random() - 0.5) * 80, Math.random() * 46 - 14, (Math.random() - 0.5) * 80],
                       s: 0.75 + Math.random() * 0.5, p: Math.random() * TAU });
        }
        updateRoofs(eye);
        var col = Rigs.rgb(kind.colour);
        var slant = kind.slant || 0, wind = spec.wind || [1, 0.3];
        var dt = step;
        for (var i = 0; i < drops.length; i++) {
          var d = drops[i];
          d.o[1] -= kind.fall * d.s * dt;
          d.o[0] += wind[0] * kind.fall * slant * dt;
          d.o[2] += wind[1] * kind.fall * slant * dt;
          if (kind.drift) {
            d.o[0] += (Math.sin(t * 0.9 + d.p) * kind.drift + wind[0] * kind.drift) * dt;
            d.o[2] += (Math.cos(t * 0.7 + d.p * 1.3) * kind.drift + wind[1] * kind.drift) * dt;
          }
          if (d.o[1] < -16 || d.o[1] > 34 || Math.abs(d.o[0]) > 40 || Math.abs(d.o[2]) > 40) {
            d.o = [(Math.random() - 0.5) * 80, kind.fall > 0 ? 28 + Math.random() * 6 : -14 + Math.random() * 4,
                   (Math.random() - 0.5) * 80];
          }
          var x = eye[0] + d.o[0], y = eye[1] + d.o[1], z = eye[2] + d.o[2];
          if (y < roofAt(x, z)) continue;
          r.pushRaw(kind.sph ? 'sph' : 'box', x, y, z, slant ? -wind[1] * slant : 0, 0, slant ? wind[0] * slant : 0,
                    kind.size[0] * (kind.sph ? d.s : 1), kind.size[1] * (kind.sph ? d.s : 1),
                    kind.size[2] * (kind.sph ? d.s : 1), col,
                    kind.a * (kind.glow ? 0.6 + 0.4 * Math.sin(t * 4 + d.p) : 1), 0, kind.glow ? 2 : 0, 0, null);
        }
        if (kind.hiss && Math.random() < dt * 0.45 && ctx.sound2d) ctx.sound2d('rr_rain', 0.5);
        if (!kind.flash) return;
        // -- a lightning rod's turn: the same slot on every screen
        var slot = Math.floor(t / ROD_EVERY), into = t - slot * ROD_EVERY;
        if (rods.length && hash(slot * 3 + 1) < 0.6 && into >= 17 && into < 17.6 && struck !== slot) {
          struck = slot;
          var rod = rods[Math.floor(hash(slot + 5) * rods.length) % rods.length];
          flash.at = clock;
          flash.power = 1;
          flash.bolt = makeBolt([rod[0] + 30, rod[1] + 150, rod[2] - 20], rod, slot * 31);
          flash.sparks = rod;
          thunder(eye, rod, 1);
        }
        // -- the sky lighting up now and then, the thunder after it
        flash.next -= dt;
        if (flash.next <= 0) {
          flash.next = kind.flash[0] + Math.random() * (kind.flash[1] - kind.flash[0]);
          flash.at = clock;
          flash.power = 0.6 + Math.random() * 0.4;
          flash.bolt = null;
          flash.sparks = null;
          var far = null;
          if (Math.random() < (kind.bolts || 0)) {
            var a = Math.random() * TAU, rr = 330 + Math.random() * 300;
            far = [eye[0] + Math.cos(a) * rr, 0, eye[2] + Math.sin(a) * rr];
            flash.bolt = makeBolt([far[0] + 20, 190, far[2] + 10], far, Math.floor(Math.random() * 1e5));
          }
          thunder(eye, far, flash.power);
        }
        var k = clock - flash.at;
        var lit = k < 0.08 ? 1 : (k < 0.16 ? 0.25 : (k < 0.28 ? 0.85 : Math.max(0, 0.85 - (k - 0.28) * 3)));
        if (lit <= 0.01) return;
        r.pushRaw('sph', eye[0], eye[1], eye[2], 0, 0, 0, 900, 900, 900, [0.9, 0.92, 1.0],
                  Math.min(0.32, 0.28 * lit * flash.power), 0, 2, 0, null);
        if (flash.bolt && k < 0.45) drawBolt(pen, flash.bolt, lit);
        if (flash.sparks && k < 1.2) {
          // the rod glowing white-hot, sparks falling off it
          var sp = flash.sparks;
          r.pushRaw('sph', sp[0], sp[1], sp[2], 0, 0, 0, 3, 3, 3, [1, 0.95, 0.8], Math.max(0, 1 - k), 0, 2, 0, null);
          for (var s = 0; s < 8; s++) {
            var ang = s * 0.785 + 0.3, out = k * 7;
            r.pushRaw('box', sp[0] + Math.cos(ang) * out, sp[1] - k * k * 14 + 1, sp[2] + Math.sin(ang) * out, 0, 0, 0,
                      0.3, 0.3, 0.3, [1, 0.85, 0.4], Math.max(0, 1 - k), 0, 2, 0, null);
          }
        }
      }
    };
  });

  // ======================================================= the horizon
  /* A twister: the funnel hanging out of the wall cloud, writhing, its
     foot kicking up a ring of dust, walking slowly between ``p`` and ``q``
     far out beyond the edge. */
  Rigs.register('rr_twister', function (spec) {
    var a = spec.p, b = spec.q || spec.p, h = spec.h || 150, s = spec.s || 1;
    return {
      radius: 700,
      at: [(a[0] + b[0]) / 2, a[1], (a[2] + b[2]) / 2],
      draw: function (pen, t) {
        var u = 0.5 + 0.5 * Math.sin(t * 0.011 + (spec.seed || 0));
        var x = a[0] + (b[0] - a[0]) * u, z = a[2] + (b[2] - a[2]) * u, y = a[1];
        var n = 26;
        for (var i = 0; i < n; i++) {
          var f = i / n, f1 = (i + 1.35) / n;
          var sway = Math.sin(t * 0.6 + i * 0.22) * 10 * s * (1 - f) + Math.sin(t * 0.23) * 14 * s * f;
          var sway1 = Math.sin(t * 0.6 + (i + 1.35) * 0.22) * 10 * s * (1 - f1) + Math.sin(t * 0.23) * 14 * s * f1;
          var w0 = (3 + Math.pow(f, 2.0) * 50) * s, w1 = (3 + Math.pow(f1, 2.0) * 50) * s;
          var shade = Math.round((0.33 + 0.05 * Math.sin(i * 1.7)) * 40) / 40;
          pen.rod([x + sway, y + f * h, z], [x + sway1, y + Math.min(1, f1) * h, z], (w0 + w1) / 2,
                  hexOf(shade, shade, shade * 1.06), { a: 0.5 - f * 0.1 });
        }
        // the wall cloud it hangs from
        for (var c = 0; c < 6; c++) {
          var ca = c * 1.05 + t * 0.02;
          pen.part(frame([x + Math.sin(t * 0.23) * 14 * s + Math.cos(ca) * 40 * s, y + h + 6, z + Math.sin(ca) * 34 * s], 0),
                   'sph', [0, 0, 0], [90 * s, 26 * s, 80 * s], '#3e4048', { a: 0.85 });
        }
        // dust and wreckage whirling round its foot
        for (var d = 0; d < 14; d++) {
          var da = d * 0.45 + t * 2.4, dr = (9 + (d % 4) * 4) * s;
          pen.part(frame([x + Math.cos(da) * dr, y + 3 + (d % 5) * 3 * s, z + Math.sin(da) * dr], 0), 'sph', [0, 0, 0],
                   [8 * s, 5 * s, 8 * s], '#7a6a54', { a: 0.35 });
          if (d % 3 === 0) {
            pen.part(frame([x + Math.cos(-da) * dr * 1.4, y + 8 + d * 1.6 * s, z + Math.sin(-da) * dr * 1.4], da),
                     'box', [0, 0, 0], [2.4 * s, 0.4 * s, 1.0 * s], '#4a3a2a', { rx: da });
          }
        }
      }
    };
  });

  // ======================================================== the farm
  /* A windpump on its tower (the tower is the map's): the wheel round and
     round, the tail keeping it into the wind, the rod going up and down. */
  Rigs.register('rr_windpump', function (spec) {
    var R = spec.r || 5;
    var spin = 0;
    return {
      radius: R + 30,
      update: function (dt, t) { spin += dt * (2.2 + 1.2 * Math.sin(t * 0.13) + 0.6 * Math.sin(t * 0.41)); },
      draw: function (pen, t) {
        var yaw = (spec.yaw || 0) + Math.sin(t * 0.07) * 0.35;
        var f = frame(spec.p, yaw, 1);
        pen.part(f, 'box', [0, 0, -2.5], [1.0, 1.0, 6], '#6a6a64', { m: 'metal' });
        pen.part(f, 'box', [0, 0.8, -6.4], [0.2, 4.0, 3.6], '#c8c0a8', { m: 'metal' });
        var wheel = child(f, [0, 0, 1.0], 0, 0, spin);
        pen.part(wheel, 'cyl', [0, 0, 0], [1.4, 1.0, 1.4], '#4a4a44', { rx: Math.PI / 2, m: 'metal' });
        pen.part(wheel, 'torus', [0, 0, 0], [R * 2, 1.2, R * 2], '#6a6a64', { rx: Math.PI / 2, m: 'metal' });
        for (var k = 0; k < 16; k++) {
          pen.part(child(wheel, [0, 0, 0], 0, 0, k * TAU / 16), 'box', [0, R * 0.58, 0], [1.0, R * 0.8, 0.1],
                   '#d8d4c8', { ry: 0.35 });
        }
        var stroke = Math.sin(spin) * 0.8;
        pen.part(frame(spec.p, 0, 1), 'box', [0, -5 + stroke, 0], [0.26, 9, 0.26], '#4a4a44', { m: 'metal' });
      }
    };
  });

  /* A weathervane: a rooster on its arrow over the four arms, swinging
     with the wind. */
  Rigs.register('rr_vane', function (spec) {
    var f0 = frame(spec.p, 0, spec.s || 1);
    var dir = 0;
    return {
      radius: 30,
      update: function (dt, t) {
        dir = approachAngle(dir, (spec.yaw || 0) + Math.sin(t * 0.06) * 0.8 + Math.sin(t * 0.37) * 0.35, 0.9, dt);
      },
      draw: function (pen) {
        pen.part(f0, 'box', [0, 1.6, 0], [0.2, 3.2, 0.2], '#2a2a2a', { m: 'metal' });
        for (var k = 0; k < 4; k++) {
          var arm = child(f0, [0, 1.4, 0], 0, k * Math.PI / 2, 0);
          pen.part(arm, 'box', [0, 0, 0.9], [0.1, 0.1, 1.8], '#2a2a2a', { m: 'metal' });
          pen.part(arm, 'box', [0, 0, 1.9], [0.12, 0.5, 0.36], '#2a2a2a', { m: 'metal' });
        }
        var v = child(f0, [0, 2.6, 0], 0, dir, 0);
        pen.part(v, 'box', [0, 0, 0], [0.12, 0.12, 3.2], '#2a2a2a', { m: 'metal' });
        pen.part(v, 'box', [0, 0, 1.7], [0.1, 0.5, 0.5], '#2a2a2a', { rx: 0.785, m: 'metal' });
        pen.part(v, 'box', [0, 0, -1.5], [0.08, 0.9, 0.7], '#2a2a2a', { m: 'metal' });
        pen.part(v, 'box', [0, 0.7, -0.3], [0.1, 0.9, 1.3], '#2a2a2a', { m: 'metal' });
        pen.part(v, 'box', [0, 1.3, 0.2], [0.1, 0.5, 0.4], '#2a2a2a', { m: 'metal' });
        pen.part(v, 'box', [0, 1.65, 0.25], [0.1, 0.3, 0.2], '#a8282e');
        pen.part(v, 'box', [0, 1.0, -1.0], [0.1, 1.2, 0.5], '#2a2a2a', { rx: -0.4, m: 'metal' });
      }
    };
  });

  /* A tumbleweed bowling along from ``p`` to ``q``, out of sight a while,
     then again. */
  Rigs.register('rr_tumbleweed', function (spec) {
    var a = spec.p, b = spec.q || spec.p, R = spec.r || 1.6, speed = spec.speed || 9, seed = spec.seed || 0;
    var len = Math.max(1, flat(a, b));
    var dir = [(b[0] - a[0]) / len, (b[2] - a[2]) / len];
    var heading = Math.atan2(dir[0], dir[1]);
    return {
      radius: len / 2 + 10,
      at: [(a[0] + b[0]) / 2, a[1], (a[2] + b[2]) / 2],
      draw: function (pen, t) {
        var period = len / speed + 7;
        var d = ((t + seed * 13) % period) * speed;
        if (d > len) return;
        var fade = Math.min(1, d / 10, (len - d) / 10);
        var wob = Math.sin(t * 0.7 + seed) * 5;
        var x = a[0] + dir[0] * d + dir[1] * wob, z = a[2] + dir[1] * d - dir[0] * wob;
        var y = a[1] + (b[1] - a[1]) * d / len + R + Math.abs(Math.sin(d * 0.21)) * R * 1.3;
        var f = child(frame([x, y, z], heading, R * fade), [0, 0, 0], d / R, 0, 0);
        pen.part(f, 'torus', [0, 0, 0], [2, 4, 2], '#a8844c');
        pen.part(f, 'torus', [0, 0, 0], [2, 4, 2], '#9a7a44', { rx: Math.PI / 2 });
        pen.part(f, 'torus', [0, 0, 0], [1.9, 4, 1.9], '#b8945a', { rz: Math.PI / 2 });
        pen.part(f, 'torus', [0, 0, 0], [1.6, 4, 1.6], '#8a6a3c', { rx: 0.8, rz: 0.6 });
      }
    };
  });

  /* Washing on a line between two posts (the posts are the map's), ``w``
     long along x, flapping. */
  Rigs.register('rr_clothesline', function (spec) {
    var w = spec.w || 16, n = 5;
    var colours = spec.colours || ['#f2f2ee', '#8ab8d8', '#e8c8c8', '#f2f2ee', '#c8a83a'];
    return {
      radius: 30,
      draw: function (pen, t) {
        var cw = w / n - 0.6;
        pen.rod([spec.p[0] - w / 2, spec.p[1], spec.p[2]], [spec.p[0] + w / 2, spec.p[1], spec.p[2]], 0.06, '#d8d8d0');
        for (var i = 0; i < n; i++) {
          var x = spec.p[0] - w / 2 + (i + 0.5) * w / n;
          var hang = child(frame([x, spec.p[1] - 0.1, spec.p[2]], 0), [0, 0, 0],
                           Math.sin(t * 2.1 + i) * 0.35 + 0.25, 0, 0);
          pen.part(hang, 'box', [0, -1.6, 0], [cw, 3.2, 0.08], colours[i % colours.length]);
          pen.part(hang, 'box', [-cw / 2 + 0.3, 0.05, 0], [0.2, 0.4, 0.2], '#c8a070');
          pen.part(hang, 'box', [cw / 2 - 0.3, 0.05, 0], [0.2, 0.4, 0.2], '#c8a070');
        }
      }
    };
  });

  /* Smoke from a chimney or a stack: puffs rising and leaning off with
     the wind, growing and thinning. */
  Rigs.register('rr_smoke', function (spec) {
    var wind = spec.wind || [1, 0.2], rate = spec.rate || 0.25, h = spec.h || 22, n = spec.n || 9;
    var colour = spec.colour || '#8a8680', size = spec.size || 2.2;
    return {
      radius: h + 30,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var u = (t * rate + i / n) % 1;
          var lean = u * u * h * 0.9;
          var s = size * (1 + u * 2.6);
          pen.part(frame([spec.p[0] + wind[0] * lean + Math.sin(t + i) * 0.6, spec.p[1] + u * h,
                          spec.p[2] + wind[1] * lean], 0), 'sph', [0, 0, 0], [s, s * 0.85, s], colour,
                   { a: 0.55 * (1 - u) });
        }
      }
    };
  });

  /* A flag at the top of a pole (the pole is the map's): the cloth in
     segments rippling out downwind. */
  Rigs.register('rr_flag', function (spec) {
    var w = spec.w || 5, h = spec.h || 3, colours = spec.colours || ['#c4281c', '#f2ece0'];
    return {
      radius: 20,
      draw: function (pen, t) {
        var yaw = (spec.yaw || 0) + Math.sin(t * 0.3) * 0.2;
        var f = frame(spec.p, yaw, 1);
        var n = 6, last = 0;
        for (var i = 0; i < n; i++) {
          var u = (i + 0.5) / n;
          var wave = Math.sin(t * 6 - i * 0.9) * 0.45 * u;
          var seg = child(f, [0, -h / 2, -(i + 0.5) * w / n - last * 0.2], 0, wave, 0);
          last = wave;
          var stripes = colours.length;
          for (var s = 0; s < stripes; s++) {
            pen.part(seg, 'box', [0, h / 2 - (s + 0.5) * h / stripes, 0], [0.06, h / stripes, w / n + 0.05],
                     colours[s]);
          }
        }
      }
    };
  });

  // ===================================================== the railroad
  function trainOn(ctx) {
    var tw = ctx.twist ? ctx.twist() : null;
    return !!(tw && tw.sweep && tw.sweep.phase === 'run');
  }

  /* A depot's train-order signal: two blades on a mast (the mast is the
     map's), one for each way along the main line.  At stop they stand
     out level, their lamps red; while a train is on the main line they
     drop to clear and the lamps go green. */
  Rigs.register('rr_order_board', function (spec, ctx) {
    var drop = 0, on = false;
    return {
      radius: 30,
      event: function (kind, msg) { if (kind === 'sweep') on = !!(msg && msg.on); },
      update: function (dt) {
        var running = on || trainOn(ctx);
        drop = approach(drop, running ? 1 : 0, 3, dt);
      },
      draw: function (pen, t) {
        var f = frame(spec.p, spec.yaw || 0, 1);
        for (var side = -1; side <= 1; side += 2) {
          var pivot = child(f, [side * 0.5, 0, 0], 0, 0, side * drop * 1.05);
          pen.part(pivot, 'box', [side * 2.4, 0, 0], [4.4, 0.7, 0.14], '#c8281e');
          pen.part(pivot, 'box', [side * 3.6, 0, 0.09], [0.6, 0.72, 0.04], '#f2ece0');
          pen.part(pivot, 'box', [side * 0.2, -0.6, 0], [0.5, 0.6, 0.3], '#2a2a2a', { m: 'metal' });
        }
        var green = drop > 0.5;
        var lamp = green ? '#5aff7a' : '#ff3a2a';
        for (var s2 = -1; s2 <= 1; s2 += 2) {
          pen.part(f, 'sph', [s2 * 0.7, -1.4, 0.3], [0.6, 0.6, 0.6], lamp, { m: 'neon', a: 0.9 + 0.1 * Math.sin(t * 3) });
        }
      }
    };
  });

  /* The telegraph sounder on the operator's desk: its brass armature
     clicking out the station's call letters now and then -- and
     chattering when a train is called down. */
  var MORSE = { T: '-', J: '.---', D: '-..', X: '-..-' };
  Rigs.register('rr_sounder', function (spec, ctx) {
    var call = (spec.call || 'TJ').split('');
    var seq = [];
    call.forEach(function (ch) {
      (MORSE[ch] || '.').split('').forEach(function (c) { seq.push(c === '-' ? 3 : 1); });
      seq.push(-3);
    });
    var down = 0, busy = 0, clicked = false;
    function near(at) {
      var v = ctx.viewer ? ctx.viewer() : null;
      return v && v.eye && dist(v.eye, at) < 40;
    }
    return {
      radius: 12,
      event: function (kind, msg) { if (kind === 'sweep' && msg && msg.on) busy = 3.0; },
      update: function (dt, t) {
        var on;
        if (busy > 0) {
          busy -= dt;
          on = Math.sin(t * 38) > 0.2;
        } else {
          // the call every twelve seconds: dots one unit, dashes three, a
          // unit apart (a unit is 0.09 s)
          var into = (t % 12) / 0.09, u = 0;
          on = false;
          for (var i = 0; i < seq.length; i++) {
            var len = Math.abs(seq[i]);
            if (into < u + len) { on = seq[i] > 0; break; }
            u += len + 1;
          }
        }
        if (on && !clicked && ctx.sound && near(spec.p)) ctx.sound('rr_sounder', spec.p, 0.35);
        clicked = on;
        down = approach(down, on ? 1 : 0, 40, dt);
      },
      draw: function (pen) {
        var f = frame(spec.p, spec.yaw || 0, 1);
        pen.part(f, 'box', [0, 0.06, 0], [1.4, 0.12, 0.8], '#5a3a22');
        pen.part(f, 'box', [-0.35, 0.3, 0], [0.24, 0.4, 0.24], '#c8a040', { m: 'metal' });
        pen.part(f, 'box', [0.35, 0.3, 0], [0.24, 0.4, 0.24], '#c8a040', { m: 'metal' });
        var arm = child(f, [0.5, 0.62, 0], 0, 0, 0.12 - down * 0.12);
        pen.part(arm, 'box', [-0.55, 0, 0], [1.2, 0.08, 0.14], '#d8b050', { m: 'metal' });
      }
    };
  });
})(window);
