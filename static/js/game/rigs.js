/* Animated scenery: "rigs".

   A map names the things on it that move as data -- markers.extra.rigs, a
   list of {kind, p: [x, y, z], yaw, ...more} (ArenaArea.rig() writes them)
   -- and this draws them every frame through the renderer's dynamic
   batches.  A rig never collides: it is something to look at, never
   something to stand on, so nothing about the map's collision changes when
   one is added and the server never hears of it.

   A world script registers the kinds it uses:

     Rigs.register('kind', function (spec, ctx) {
       return { radius: 60,                       // for culling
                update: function (dt, t, ctx) {}, // optional, every frame
                draw: function (pen, t, ctx) {},  // when in view
                event: function (kind, msg, ctx) {} };  // optional
     });

   and its plugin keeps a list from Rigs.build(map, ctx), hands net events
   to Rigs.notify(list, kind, msg) and calls Rigs.draw(list, renderer, dt,
   eye) from its draw hook.

   ``t`` is wall-clock seconds (Date.now), the same on every screen, so a
   mechanism -- an orrery's planets, a clock's hands -- stands the same way
   for everybody; behaviour that reacts to the game (who a cat is looking
   at) reads the same players and flags on every client, so it agrees too.

   The scene graph is as small as it can be: a *frame* is a position, a
   rotation (3x3, row-major) and a scale; ``child`` makes one inside
   another; ``pen.part(frame, kind, offset, size, colour, options)`` draws a
   primitive in a frame's space.  Rotations compose in the renderer's own
   order (yaw, then pitch, then roll: R = Ry Rx Rz, gl.js M.compose), and
   each part's world rotation is decomposed back into those three angles
   for the instance buffer, so a tail can bend segment on segment and a moon
   ride a planet that rides an arm. */
(function (global) {
  'use strict';

  var KINDS = {};
  var colours = {};

  function rgb(hex) {
    var c = colours[hex];
    if (c) return c;
    var M = global.GLX && global.GLX.mat;
    if (M && M.hexToRgb) {
      c = M.hexToRgb(hex);
    } else {
      var n = parseInt(String(hex || '#ffffff').replace('#', ''), 16);
      c = [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
    }
    colours[hex] = c;
    return c;
  }

  // ------------------------------------------------------------- maths
  /* R = Ry * Rx * Rz, row-major [r00 r01 r02 r10 r11 r12 r20 r21 r22]. */
  function rot(rx, ry, rz) {
    var cx = Math.cos(rx), sx = Math.sin(rx);
    var cy = Math.cos(ry), sy = Math.sin(ry);
    var cz = Math.cos(rz), sz = Math.sin(rz);
    return [cy * cz + sy * sx * sz, -cy * sz + sy * sx * cz, sy * cx,
            cx * sz, cx * cz, -sx,
            -sy * cz + cy * sx * sz, sy * sz + cy * sx * cz, cy * cx];
  }

  function mul(a, b) {
    return [
      a[0] * b[0] + a[1] * b[3] + a[2] * b[6], a[0] * b[1] + a[1] * b[4] + a[2] * b[7],
      a[0] * b[2] + a[1] * b[5] + a[2] * b[8],
      a[3] * b[0] + a[4] * b[3] + a[5] * b[6], a[3] * b[1] + a[4] * b[4] + a[5] * b[7],
      a[3] * b[2] + a[4] * b[5] + a[5] * b[8],
      a[6] * b[0] + a[7] * b[3] + a[8] * b[6], a[6] * b[1] + a[7] * b[4] + a[8] * b[7],
      a[6] * b[2] + a[7] * b[5] + a[8] * b[8]
    ];
  }

  function apply(r, x, y, z) {
    return [r[0] * x + r[1] * y + r[2] * z, r[3] * x + r[4] * y + r[5] * z,
            r[6] * x + r[7] * y + r[8] * z];
  }

  /* The angles M.compose takes back out of a rotation. */
  function euler(r) {
    var s = -r[5];
    if (s > 1) s = 1; else if (s < -1) s = -1;
    var rx = Math.asin(s);
    if (Math.abs(Math.cos(rx)) < 1e-6) return [rx, Math.atan2(-r[6], r[0]), 0];
    return [rx, Math.atan2(r[2], r[8]), Math.atan2(r[3], r[4])];
  }

  var IDENTITY = [1, 0, 0, 0, 1, 0, 0, 0, 1];

  function frame(p, yaw, scale) {
    return { p: [p[0], p[1], p[2]], r: yaw ? rot(0, yaw, 0) : IDENTITY.slice(), s: scale || 1 };
  }

  /* A frame inside ``f``: ``offset`` in f's space, turned by (rx, ry, rz)
     relative to it, scaled by ``scale`` on top of f's own. */
  function child(f, offset, rx, ry, rz, scale) {
    var o = apply(f.r, offset[0] * f.s, offset[1] * f.s, offset[2] * f.s);
    var r = (rx || ry || rz) ? mul(f.r, rot(rx || 0, ry || 0, rz || 0)) : f.r;
    return { p: [f.p[0] + o[0], f.p[1] + o[1], f.p[2] + o[2]], r: r, s: f.s * (scale || 1) };
  }

  /* A point given in f's space, in the world. */
  function point(f, offset) {
    var o = apply(f.r, offset[0] * f.s, offset[1] * f.s, offset[2] * f.s);
    return [f.p[0] + o[0], f.p[1] + o[1], f.p[2] + o[2]];
  }

  /* A world direction in f's space (f's rotation is orthonormal). */
  function local(f, v) {
    var r = f.r;
    return [r[0] * v[0] + r[3] * v[1] + r[6] * v[2], r[1] * v[0] + r[4] * v[1] + r[7] * v[2],
            r[2] * v[0] + r[5] * v[1] + r[8] * v[2]];
  }

  var MATERIAL = { plastic: 0, metal: 1, neon: 2, glass: 3, grass: 4, wood: 0 };

  // --------------------------------------------------------------- pen
  function Pen(renderer) {
    this.r = renderer;
    this.count = 0;
  }

  /* One primitive in ``f``'s space.  ``o``: rx/ry/rz (its own turn inside
     the frame), a (alpha), m (material name), st (studs), dec (a decal
     name, as a map part's ``dec``). */
  Pen.prototype.part = function (f, kind, offset, size, colour, o) {
    var r = f.r;
    if (o && (o.rx || o.ry || o.rz)) r = mul(r, rot(o.rx || 0, o.ry || 0, o.rz || 0));
    var e = euler(r);
    var p = point(f, offset);
    var decal = o && o.dec && global.Textures && global.Textures.decal ?
      global.Textures.decal(o.dec) : null;
    this.r.pushRaw(kind, p[0], p[1], p[2], e[0], e[1], e[2],
                   size[0] * f.s, size[1] * f.s, size[2] * f.s, rgb(colour),
                   o && o.a !== undefined ? o.a : 1, o && o.st ? 1 : 0,
                   o && o.m ? (MATERIAL[o.m] || 0) : 0, 0, decal, false);
    this.count++;
  };

  /* How far a world point is from the eye (a rig made of many far-flung
     pieces -- a gear train down a tunnel -- culls them one by one). */
  Pen.prototype.away = function (p) {
    var e = this.eye;
    return e ? Math.hypot(p[0] - e[0], p[1] - e[1], p[2] - e[2]) : 0;
  };

  /* A rod from a to b (world points), ``w`` thick: a cylinder, or a box
     with ``kind`` 'box'.  For ropes, spokes, beams of light. */
  Pen.prototype.rod = function (a, b, w, colour, o, kind) {
    var dx = b[0] - a[0], dy = b[1] - a[1], dz = b[2] - a[2];
    var len = Math.sqrt(dx * dx + dy * dy + dz * dz);
    if (len < 1e-4) return;
    // the cylinder's axis is local y: yaw to the line's heading, then pitch
    // y down onto it
    var yaw = Math.atan2(dx, dz);
    var pitch = Math.atan2(Math.sqrt(dx * dx + dz * dz), dy);
    var f = { p: [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2],
              r: rot(pitch, yaw, 0), s: 1 };
    this.part(f, kind || 'cyl', [0, 0, 0], [w, len, w], colour, o);
  };

  // -------------------------------------------------------- the registry
  function register(kind, factory) { KINDS[kind] = factory; }

  function has(kind) { return !!KINDS[kind]; }

  function build(map, ctx) {
    var specs = (((map || {}).markers || {}).extra || {}).rigs || [];
    var list = [];
    for (var i = 0; i < specs.length; i++) {
      var spec = specs[i];
      var factory = KINDS[spec.kind];
      if (!factory) continue;
      try {
        var rig = factory(spec, ctx || {});
        if (!rig) continue;
        rig.spec = spec;
        rig.at = rig.at || spec.p;
        rig.radius = rig.radius || spec.radius || 40;
        list.push(rig);
      } catch (err) {
        if (global.console) console.error('rig ' + spec.kind + ':', err);
      }
    }
    return list;
  }

  function clock() { return Date.now() / 1000; }

  /* Every rig's update, and the draw of the ones within ``far`` of the eye
     (plus their own radius).  A rig that throws is switched off rather
     than taking the frame down with it. */
  function draw(list, renderer, dt, eye, ctx, far) {
    if (!list || !list.length) return 0;
    var t = global.Rigs.clock();     // (a test can wind it)
    var pen = new Pen(renderer);
    var reach = far || 900;
    for (var i = 0; i < list.length; i++) {
      var rig = list[i];
      if (rig.dead) continue;
      try {
        if (rig.update) rig.update(dt, t, ctx);
        var at = rig.at;
        var d = eye ? Math.hypot(at[0] - eye[0], at[1] - eye[1], at[2] - eye[2]) : 0;
        if (d > reach + rig.radius) continue;
        pen.near = d < 160 + rig.radius;       // close enough for the fine details
        pen.eye = eye;
        rig.draw(pen, t, ctx);
      } catch (err) {
        rig.dead = true;
        if (global.console) console.error('rig ' + (rig.spec && rig.spec.kind) + ':', err);
      }
    }
    return pen.count;
  }

  function notify(list, kind, msg, ctx) {
    if (!list) return;
    for (var i = 0; i < list.length; i++) {
      var rig = list[i];
      if (rig.dead || !rig.event) continue;
      try { rig.event(kind, msg, ctx); } catch (err) { rig.dead = true; }
    }
  }

  // ----------------------------------------------------- small helpers
  /* Ease a value toward a target at ``rate`` per second (frame-rate free). */
  function approach(value, target, rate, dt) {
    return value + (target - value) * (1 - Math.exp(-rate * dt));
  }

  /* An angle eased the short way round. */
  function approachAngle(value, target, rate, dt) {
    var d = target - value;
    while (d > Math.PI) d -= Math.PI * 2;
    while (d < -Math.PI) d += Math.PI * 2;
    return value + d * (1 - Math.exp(-rate * dt));
  }

  /* Smooth noise from a few sines: the same everywhere for the same seed. */
  function wander(t, seed) {
    return (Math.sin(t * 0.71 + seed * 1.7) * 0.5 + Math.sin(t * 1.33 + seed * 3.1) * 0.3 +
            Math.sin(t * 2.07 + seed * 5.3) * 0.2);
  }

  function hash(n) {
    var x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
    return x - Math.floor(x);
  }

  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }

  global.Rigs = {
    register: register, has: has, build: build, draw: draw, notify: notify, clock: clock,
    frame: frame, child: child, point: point, local: local, rot: rot, mul: mul,
    euler: euler, Pen: Pen, rgb: rgb, approach: approach, approachAngle: approachAngle,
    wander: wander, hash: hash, clamp: clamp
  };
})(window);
