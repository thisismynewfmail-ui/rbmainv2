/* Plunder Bay's moving scenery ("rigs": static/js/game/rigs.js).

   An island names what moves on it in markers.extra.rigs (ArenaArea.rig());
   the plugin (plunder_bay.js) builds and draws them every frame.  Nothing
   here collides or reaches the server.  The gulls, flags, smoke, surf,
   sails, lamps and weather come from Rail Rivals' set (rail_rivals_rigs.js,
   loaded alongside); these are the islands' own:

     pb_whale       a whale far out, surfacing to blow, showing its flukes
     pb_dolphins    a pod leaping in arcs round a loop
     pb_crabs       crabs scuttling sideways along a beach, scattering
     pb_parrots     parrots flying figure-eights over the jungle, squawking
     pb_wisps       will-o'-the-wisps drifting green over a wreck
     pb_ghostship   a ghost galleon sailing in and out of the fog
     pb_glow        bioluminescent sparkles on the water
     pb_jellyfish   glowing jellies pulsing in a lagoon
     pb_aurora      the northern lights, curtains waving in the sky
     pb_penguins    penguins waddling about -- and now and then a slide
     pb_lanterns    paper lanterns floating on the water
     pb_sampan      a little boat bobbing at its mooring
     pb_ferris      a Ferris wheel turning, its cars hanging level
     pb_firework    fireworks going up over the fair
     pb_sparks      St Elmo's fire crackling round a lightning rod's tip
     pb_skylanterns paper sky lanterns rising from a festival, drifting off
     pb_wake        the water lighting up round anybody wading in it
     pb_falls       a waterfall pouring off a cliff: curtain, foam, mist, roar
     pb_bunting     pennants on a sagging cord between points, fluttering
     pb_koi         koi circling a pond, tails swishing
     pb_ripples     rain rings spreading on still water (or in puddles)
     pb_rainbow     a rainbow arching over the sky, brightening and fading
     pb_petals      blossom petals drifting down from a tree
     pb_fishnet     a cantilevered fishing net dipping into the sea and rising

   A rig that floats (pb_glow, pb_lanterns, pb_sampan; rr_surf too) and is
   given ``tide: true`` rides the sea's height (ctx.water()) instead of its
   own y, so it goes out with the tide; ``floor`` is as low as it goes (a
   boat settles on the mud). */
(function (global) {
  'use strict';
  var Rigs = global.Rigs;
  if (!Rigs) return;
  var frame = Rigs.frame, child = Rigs.child, hash = Rigs.hash, point = Rigs.point;
  var TAU = Math.PI * 2;

  function dist(a, b) { return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]); }
  /* the height a floating rig rides at: the sea's, if it follows the tide */
  function afloat(spec, ctx, dy) {
    if (!spec.tide || !ctx || !ctx.water) return spec.p[1];
    var y = ctx.water() + (dy || 0);
    return spec.floor === undefined ? y : Math.max(spec.floor, y);
  }
  function near(ctx, p, r) {
    var v = ctx.viewer ? ctx.viewer() : null;
    return v && v.eye && dist(v.eye, p) < r;
  }

  // ========================================================== the sea
  /* A whale far out: it swims a slow loop, comes up to blow -- the spout,
     the long dark back -- then dives, its flukes lifting out of the sea. */
  Rigs.register('pb_whale', function (spec) {
    var R = spec.r || 60, seed = spec.seed || 0, S = spec.s || 1;
    return {
      radius: R + 80,
      draw: function (pen, t) {
        var cycle = (t + seed * 7) % 20;
        if (cycle > 9) return;
        var a = t * 0.025 + seed, x = spec.p[0] + Math.cos(a) * R, z = spec.p[2] + Math.sin(a) * R;
        var yaw = a + Math.PI;
        var dive = cycle > 6 ? (cycle - 6) / 3 : 0;
        var rise = Math.min(1, cycle / 1.2);
        var y = spec.p[1] - 2.6 + rise * 1.6 - dive * 4;
        var f = child(frame([x, y, z], yaw, S), [0, 0, 0], -dive * 0.6, 0, 0);
        pen.part(f, 'sph', [0, 0, 0], [7, 4.6, 20], '#3a4a5a');
        pen.part(f, 'sph', [0, -0.8, 1], [6, 3, 16], '#c8ccd0');
        pen.part(f, 'box', [0, 2.0, -3], [0.6, 1.6, 3], '#33424f', { rx: -0.4 });
        pen.part(f, 'sph', [0, 0.6, 8], [5.6, 3.6, 7], '#3a4a5a');
        if (dive > 0) {
          var tail = child(f, [0, 0.4, -11], 0.8 * dive, 0, 0);
          pen.part(tail, 'box', [0, 0, -2], [1.4, 1.2, 5], '#33424f');
          pen.part(tail, 'box', [0, 0, -4.6], [9, 0.5, 2.6], '#33424f');
        }
        if (cycle > 1 && cycle < 3) {
          var k = (cycle - 1) / 2;
          for (var i = 0; i < 6; i++) {
            pen.part(frame([x, spec.p[1] + 2 + i * 1.8 * (0.4 + k), z], 0, 1), 'sph', [0, 0, 0],
                     [1.6 + i * 0.5, 1.4, 1.6 + i * 0.5], '#f2f8ff', { a: (1 - k) * 0.8 });
          }
        }
      }
    };
  });

  /* A pod of dolphins leaping in arcs one after another round a loop. */
  Rigs.register('pb_dolphins', function (spec) {
    var n = spec.n || 4, R = spec.r || 30, seed = spec.seed || 0;
    return {
      radius: R + 40,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var ph = (t * 0.55 + i * 0.37 + seed) % 2.4;
          if (ph > 1) continue;
          var a = t * 0.09 + i * 0.22 + seed;
          var x = spec.p[0] + Math.cos(a) * (R + i * 2), z = spec.p[2] + Math.sin(a) * (R + i * 2);
          var y = spec.p[1] - 1.5 + Math.sin(ph * Math.PI) * 6;
          var f = child(frame([x, y, z], a + Math.PI, 1), [0, 0, 0], Math.cos(ph * Math.PI) * 0.9, 0, 0);
          pen.part(f, 'sph', [0, 0, 0], [1.8, 1.8, 6], '#7a8a9a');
          pen.part(f, 'sph', [0, -0.4, 0.4], [1.4, 1.1, 4.6], '#d8dce0');
          pen.part(f, 'box', [0, 0, 3.4], [0.5, 0.4, 1.4], '#6a7a8a');
          pen.part(f, 'box', [0, 1.0, -0.4], [0.3, 1.2, 1.2], '#6a7a8a', { rx: -0.5 });
          pen.part(f, 'box', [0, 0, -3.4], [2.6, 0.25, 0.9], '#6a7a8a');
        }
      }
    };
  });

  // ========================================================== the shore
  /* Crabs scuttling sideways up and down a stretch of beach, claws up
     when anybody comes near -- and off at a run. */
  Rigs.register('pb_crabs', function (spec, ctx) {
    var n = spec.n || 4, a = spec.p, b = spec.q || spec.p, seed = spec.seed || 0;
    var len = Math.hypot(b[0] - a[0], b[2] - a[2]) || 1;
    var ux = (b[0] - a[0]) / len, uz = (b[2] - a[2]) / len;
    var pos = [], scared = [];
    for (var i = 0; i < n; i++) { pos.push(hash(seed + i * 3.3) * len); scared.push(0); }
    return {
      radius: len / 2 + 30,
      at: [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2],
      update: function (dt, t) {
        var ps = ctx.players ? ctx.players() : [];
        for (var i = 0; i < n; i++) {
          var x = a[0] + ux * pos[i], z = a[2] + uz * pos[i];
          var threat = ps.some(function (p) { return Math.hypot(p.pos[0] - x, p.pos[2] - z) < 6; });
          scared[i] = threat ? 1 : Math.max(0, scared[i] - dt);
          var dir = Math.sin(t * 0.4 + i * 1.7 + seed) > 0 ? 1 : -1;
          pos[i] = Math.max(0, Math.min(len, pos[i] + dir * dt * (scared[i] ? 9 : (Math.sin(t * 2 + i) > 0.2 ? 2.2 : 0))));
        }
      },
      draw: function (pen, t) {
        if (!pen.near) return;
        for (var i = 0; i < n; i++) {
          var x = a[0] + ux * pos[i], z = a[2] + uz * pos[i], y = a[1] + (b[1] - a[1]) * pos[i] / len;
          var f = frame([x, y, z], Math.atan2(ux, uz) + Math.PI / 2, 0.9);
          var claws = scared[i] ? 0.9 : 0.2 + Math.sin(t * 3 + i) * 0.1;
          pen.part(f, 'sph', [0, 0.45, 0], [1.6, 0.8, 1.2], spec.colour || '#d8502a');
          for (var e = -1; e <= 1; e += 2) {
            pen.part(child(f, [e * 0.9, 0.6, 0.5], -claws, 0, e * 0.3), 'box', [0, 0.3, 0.3], [0.5, 0.4, 0.8], '#e8603a');
            for (var l = 0; l < 3; l++) {
              pen.part(f, 'box', [e * 0.95, 0.25, -0.4 + l * 0.4], [0.7, 0.1, 0.12], '#c8401a',
                       { rz: e * (0.5 + Math.sin(t * 18 + l + i) * 0.2) });
            }
          }
          pen.part(f, 'box', [-0.25, 0.95, 0.5], [0.12, 0.4, 0.12], '#1a1a1a');
          pen.part(f, 'box', [0.25, 0.95, 0.5], [0.12, 0.4, 0.12], '#1a1a1a');
        }
      }
    };
  });

  /* Parrots flying figure-eights over the jungle, red, blue, yellow and
     green, squawking now and then. */
  Rigs.register('pb_parrots', function (spec, ctx) {
    var n = spec.n || 4, R = spec.r || 18, seed = spec.seed || 0;
    var cols = [['#d8281e', '#2a6ab8', '#ffd04a'], ['#2a8ad8', '#ffd04a', '#2a6ab8'],
                ['#3ab84a', '#d8281e', '#ffd04a'], ['#ffd04a', '#2a8ad8', '#3ab84a']];
    var said = -1;
    return {
      radius: R + 40,
      update: function (dt, t) {
        var slot = Math.floor(t / 6);
        if (slot !== said && hash(slot + seed) < 0.45) {
          said = slot;
          if (near(ctx, spec.p, 90) && ctx.sound) ctx.sound('pb_squawk', spec.p, 0.5);
        }
      },
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var a = t * 0.5 + i * TAU / n + seed;
          var x = spec.p[0] + Math.sin(a) * R, z = spec.p[2] + Math.sin(a * 2) * R * 0.45;
          var y = spec.p[1] + Math.sin(a * 3 + i) * 2;
          var dx = Math.cos(a) * R, dz = Math.cos(a * 2) * R * 0.9;
          var f = frame([x, y, z], Math.atan2(dx, dz), 1);
          var c = cols[i % cols.length];
          var flap = Math.sin(t * 12 + i) * 0.7;
          pen.part(f, 'sph', [0, 0, 0], [0.9, 0.9, 1.8], c[0]);
          pen.part(f, 'sph', [0, 0.3, 1.0], [0.8, 0.8, 0.8], c[0]);
          pen.part(f, 'box', [0, 0.1, 1.5], [0.3, 0.4, 0.5], '#2a2a2a');
          pen.part(f, 'box', [0, -0.1, -1.6], [0.4, 0.15, 1.8], c[1]);
          pen.part(child(f, [0.4, 0.2, 0], 0, 0, -flap), 'box', [1.2, 0, 0], [2.4, 0.1, 1.0], c[1]);
          pen.part(child(f, [-0.4, 0.2, 0], 0, 0, flap), 'box', [-1.2, 0, 0], [2.4, 0.1, 1.0], c[2]);
        }
      }
    };
  });

  // ========================================================== the dead
  /* Will-o'-the-wisps: little green lights drifting and bobbing over the
     wrecks, pulsing, each with a soft halo. */
  Rigs.register('pb_wisps', function (spec) {
    var n = spec.n || 6, R = spec.r || 14, seed = spec.seed || 0, colour = spec.colour || '#7aff9a';
    return {
      radius: R + 40,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var a = t * (0.2 + hash(seed + i) * 0.3) + i * 2.1;
          var x = spec.p[0] + Math.cos(a) * R * (0.4 + hash(seed + i * 2) * 0.6);
          var z = spec.p[2] + Math.sin(a * 1.3) * R * (0.4 + hash(seed + i * 5) * 0.6);
          var y = spec.p[1] + Math.sin(t * 1.4 + i) * 1.4 + hash(seed + i * 7) * 3;
          var pulse = 0.6 + 0.4 * Math.sin(t * 3 + i * 1.3);
          var f = frame([x, y, z], 0, 1);
          pen.part(f, 'sph', [0, 0, 0], [0.7, 0.7, 0.7], '#e8ffe8', { m: 'neon' });
          pen.part(f, 'sph', [0, 0, 0], [2.6 * pulse, 2.6 * pulse, 2.6 * pulse], colour, { a: 0.25, m: 'neon' });
        }
      }
    };
  });

  /* A ghost galleon sailing slowly back and forth out in the fog, green
     and see-through, its rags of sails stirring, fading in and out. */
  Rigs.register('pb_ghostship', function (spec) {
    var a = spec.p, b = spec.q || spec.p, seed = spec.seed || 0;
    var len = Math.hypot(b[0] - a[0], b[2] - a[2]) || 1;
    return {
      radius: len / 2 + 120,
      at: [(a[0] + b[0]) / 2, a[1], (a[2] + b[2]) / 2],
      draw: function (pen, t) {
        var u = (Math.sin(t * 0.03 + seed) + 1) / 2;
        var x = a[0] + (b[0] - a[0]) * u, z = a[2] + (b[2] - a[2]) * u;
        var heading = Math.atan2(b[0] - a[0], b[2] - a[2]) + (Math.cos(t * 0.03 + seed) < 0 ? Math.PI : 0);
        var fade = 0.25 + 0.25 * Math.sin(t * 0.5 + seed);
        var f = child(frame([x, a[1] + Math.sin(t * 0.7) * 0.4, z], heading, spec.s || 1), [0, 0, 0], 0, 0,
                      Math.sin(t * 0.5) * 0.04);
        var hull = '#5aff9a';
        pen.part(f, 'box', [0, 1.5, 0], [10, 5, 36], hull, { a: fade, m: 'neon' });
        pen.part(f, 'box', [0, 5, -14], [10, 4, 8], hull, { a: fade, m: 'neon' });
        for (var m = 0; m < 3; m++) {
          var mz = -10 + m * 12;
          pen.part(f, 'box', [0, 16, mz], [0.6, 26, 0.6], '#3a8a5a', { a: fade * 1.4 });
          for (var y2 = 0; y2 < 2; y2++) {
            var billow = Math.sin(t * 1.3 + m + y2) * 0.6;
            pen.part(f, 'box', [0, 12 + y2 * 8, mz + 0.8 + billow], [12 - y2 * 3, 6, 0.3], '#c8ffd8',
                     { a: fade * 0.8, rx: billow * 0.2 });
          }
        }
        for (var l = 0; l < 3; l++) {
          pen.part(f, 'sph', [l - 1 ? 4.6 : -4.6, 7, -16 + l * 14], [0.8, 0.8, 0.8], '#ccffdd', { m: 'neon', a: 0.9 });
        }
      }
    };
  });

  // ========================================================== the glow
  /* Bioluminescence: sparkles of light on the dark water, twinkling and
     drifting, brighter where something moves. */
  Rigs.register('pb_glow', function (spec, ctx) {
    var n = spec.n || 40, W = spec.w || 40, D = spec.d || 40, seed = spec.seed || 0;
    var cols = spec.colours || ['#5af0ff', '#7affd8', '#4ab8ff', '#b8fff0'];
    return {
      radius: Math.max(W, D) / 2 + 40,
      draw: function (pen, t) {
        var y0 = afloat(spec, ctx, 0.05);
        for (var i = 0; i < n; i++) {
          var tw = Math.sin(t * (1.4 + hash(seed + i) * 2) + i * 1.9);
          if (tw < 0) continue;
          var x = spec.p[0] + (hash(seed + i * 3.1) - 0.5) * W + Math.sin(t * 0.2 + i) * 1.2;
          var z = spec.p[2] + (hash(seed + i * 5.3) - 0.5) * D + Math.cos(t * 0.17 + i) * 1.2;
          var s = 0.35 + tw * 0.5;
          pen.part(frame([x, y0 + (spec.lift ? hash(seed + i * 7) * spec.lift : 0), z], 0, 1), 'sph', [0, 0, 0],
                   [s, s, s], cols[i % cols.length], { m: 'neon', a: 0.5 + tw * 0.5 });
        }
      }
    };
  });

  /* Jellyfish in the lagoon: bells pulsing, tentacles trailing, glowing
     pink and blue, drifting slow circles. */
  Rigs.register('pb_jellyfish', function (spec) {
    var n = spec.n || 6, R = spec.r || 16, seed = spec.seed || 0;
    var cols = ['#ff8ad8', '#8ad8ff', '#c8a8ff', '#8affd8'];
    return {
      radius: R + 30,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var a = t * 0.06 * (i % 2 ? 1 : -1) + i * TAU / n + seed;
          var r = R * (0.3 + hash(seed + i) * 0.7);
          var x = spec.p[0] + Math.cos(a) * r, z = spec.p[2] + Math.sin(a) * r;
          var pulse = Math.sin(t * 2.2 + i * 1.3);
          var y = spec.p[1] + Math.sin(t * 0.6 + i) * 0.5 + pulse * 0.2;
          var f = frame([x, y, z], 0, 0.9 + hash(seed + i * 9) * 0.5);
          var c = cols[i % cols.length];
          pen.part(f, 'sph', [0, 0, 0], [2.4 - pulse * 0.4, 1.4 + pulse * 0.3, 2.4 - pulse * 0.4], c, { a: 0.55, m: 'neon' });
          for (var k = 0; k < 4; k++) {
            var ang = k * TAU / 4 + t * 0.5;
            pen.part(f, 'box', [Math.cos(ang) * 0.6, -1.4 - Math.sin(t * 3 + k) * 0.2, Math.sin(ang) * 0.6],
                     [0.12, 2.4, 0.12], c, { a: 0.45, m: 'neon' });
          }
        }
      }
    };
  });

  /* The northern lights: curtains of green and violet light hanging in
     the sky along an arc, their folds waving. */
  Rigs.register('pb_aurora', function (spec) {
    var R = spec.r || 600, H = spec.h || 120, n = spec.n || 26, span = spec.span || 2.2;
    return {
      radius: R + 400,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var f = i / (n - 1);
          var a = (spec.yaw || 0) - span / 2 + f * span;
          var wave = Math.sin(t * 0.4 + i * 0.45) * 30 + Math.sin(t * 0.17 + i * 0.2) * 20;
          var x = spec.p[0] + Math.sin(a) * (R + wave), z = spec.p[2] + Math.cos(a) * (R + wave);
          var bright = 0.18 + 0.14 * Math.sin(t * 0.8 + i * 0.7);
          var fr = frame([x, spec.p[1] + H, z], a, 1);
          pen.part(fr, 'box', [0, 0, 0], [R * span / n * 1.3, H * 0.9, 2], '#5affa8', { a: bright, m: 'neon' });
          pen.part(fr, 'box', [0, H * 0.55, 0], [R * span / n * 1.3, H * 0.35, 2], '#b85aff', { a: bright * 0.8, m: 'neon' });
        }
      }
    };
  });

  /* Penguins waddling about the ice -- and now and then one tobogganing on
     its belly. */
  Rigs.register('pb_penguins', function (spec) {
    var n = spec.n || 5, R = spec.r || 10, seed = spec.seed || 0;
    return {
      radius: R + 30,
      draw: function (pen, t) {
        if (!pen.near) return;
        for (var i = 0; i < n; i++) {
          var a = t * 0.08 * (i % 2 ? 1 : -1) + i * TAU / n + seed;
          var r = R * (0.4 + (i % 3) * 0.25);
          var x = spec.p[0] + Math.cos(a) * r, z = spec.p[2] + Math.sin(a) * r;
          var heading = a + (i % 2 ? Math.PI / 2 : -Math.PI / 2);
          var slide = Math.sin(t * 0.3 + i * 2.1) > 0.85;
          var waddle = slide ? 0 : Math.sin(t * 8 + i) * 0.18;
          var f = child(frame([x, spec.p[1], z], heading, 0.9), [0, 0, 0], slide ? 1.4 : 0, 0, waddle);
          pen.part(f, 'sph', [0, 1.4, 0], [1.6, 2.6, 1.5], '#1e2228');
          pen.part(f, 'sph', [0, 1.3, 0.35], [1.2, 2.2, 1.0], '#f4f4f0');
          pen.part(f, 'sph', [0, 2.9, 0.1], [1.1, 1.1, 1.1], '#1e2228');
          pen.part(f, 'box', [0, 2.85, 0.75], [0.3, 0.25, 0.6], '#ff9a2a');
          pen.part(f, 'box', [0.85, 1.6, 0], [0.2, 1.4, 0.6], '#1e2228', { rz: 0.3 + waddle });
          pen.part(f, 'box', [-0.85, 1.6, 0], [0.2, 1.4, 0.6], '#1e2228', { rz: -0.3 - waddle });
          pen.part(f, 'box', [0.4, 0.1, 0.4], [0.5, 0.2, 0.7], '#ff9a2a');
          pen.part(f, 'box', [-0.4, 0.1, 0.4], [0.5, 0.2, 0.7], '#ff9a2a');
        }
      }
    };
  });

  // ========================================================== the bazaar
  /* Paper lanterns floating on the water, bobbing, drifting slow loops,
     lit from inside. */
  Rigs.register('pb_lanterns', function (spec, ctx) {
    var n = spec.n || 10, W = spec.w || 30, D = spec.d || 30, seed = spec.seed || 0;
    var cols = ['#ff6a4a', '#ffb84a', '#ff8ad8', '#ffe07a'];
    return {
      radius: Math.max(W, D) / 2 + 40,
      draw: function (pen, t) {
        var y0 = afloat(spec, ctx, 0);
        for (var i = 0; i < n; i++) {
          var x = spec.p[0] + (hash(seed + i * 3.7) - 0.5) * W + Math.sin(t * 0.1 + i) * 3;
          var z = spec.p[2] + (hash(seed + i * 6.1) - 0.5) * D + Math.cos(t * 0.08 + i) * 3;
          var y = y0 + Math.sin(t * 1.1 + i * 1.7) * 0.15;
          var f = frame([x, y, z], t * 0.1 + i, 1);
          pen.part(f, 'box', [0, 0.1, 0], [1.6, 0.2, 1.6], '#6a4a2a');
          pen.part(f, 'box', [0, 0.9, 0], [1.3, 1.4, 1.3], cols[i % cols.length], { a: 0.85, m: 'neon' });
          pen.part(f, 'sph', [0, 0.9, 0], [2.6, 2.4, 2.6], cols[i % cols.length], { a: 0.15, m: 'neon' });
        }
      }
    };
  });

  /* A little boat at its mooring, bobbing and swinging on its line: the
     hull, a woven canopy, a lantern on a pole. */
  Rigs.register('pb_sampan', function (spec, ctx) {
    var seed = spec.seed || 0, colour = spec.colour || '#8a5a3a', roof = spec.roof || '#c8a060';
    return {
      radius: 40,
      draw: function (pen, t) {
        var y0 = afloat(spec, ctx, 0), aground = spec.floor !== undefined && y0 <= spec.floor + 1e-3;
        var bob = aground ? 0 : Math.sin(t * 1.2 + seed) * 0.18, roll = aground ? 0.06 : Math.sin(t * 0.9 + seed) * 0.05;
        var f = child(frame([spec.p[0], y0 + bob, spec.p[2]], (spec.yaw || 0) + (aground ? 0 : Math.sin(t * 0.2 + seed) * 0.08), 1),
                      [0, 0, 0], Math.sin(t * 1.1 + seed) * 0.03, 0, roll);
        pen.part(f, 'box', [0, 0.3, 0], [3.2, 1.0, 10], colour);
        pen.part(f, 'box', [0, 0.9, 5.4], [1.8, 0.8, 1.4], colour, { rx: -0.4 });
        pen.part(f, 'box', [0, 0.9, -5.4], [1.8, 0.8, 1.4], colour, { rx: 0.4 });
        pen.part(f, 'box', [0, 0.85, 0], [2.6, 0.1, 9.4], '#a8805a');
        for (var k = -1; k <= 1; k++) {
          pen.part(f, 'box', [0, 2.6, k * 1.4], [3.0, 0.3, 1.5], roof, { rz: 0 });
        }
        pen.part(f, 'box', [0, 3.0, 0], [2.0, 0.3, 4.4], roof);
        pen.part(f, 'box', [1.2, 1.8, 3.5], [0.15, 3.0, 0.15], '#4a3a2a');
        pen.part(f, 'sph', [1.2, 3.4, 3.5], [0.8, 0.9, 0.8], '#ff7a4a', { m: 'neon' });
      }
    };
  });

  // ========================================================== the fair
  /* A Ferris wheel turning slowly: the rim and its spokes, the bulbs
     round it chasing, the cars hanging level as it goes round. */
  Rigs.register('pb_ferris', function (spec) {
    var R = spec.r || 14, n = spec.n || 10, cars = ['#ff5a5a', '#5ab8ff', '#ffd84a', '#7aff7a', '#ff8ad8'];
    var spin = 0;
    return {
      radius: R + 60,
      update: function (dt) { spin += dt * 0.18; },
      draw: function (pen, t) {
        var f = frame(spec.p, spec.yaw || 0, 1);
        var w = child(f, [0, 0, 0], 0, 0, spin);
        for (var e = -1; e <= 1; e += 2) {
          for (var k = 0; k < 24; k++) {
            var a = k * TAU / 24;
            pen.part(w, 'box', [Math.cos(a) * R, Math.sin(a) * R, e * 1.4], [0.4, R * 0.27, 0.4], '#f4f0e8', { rz: a });
            var lit = (Math.floor(t * 6) + k) % 3 === 0;
            pen.part(w, 'sph', [Math.cos(a) * (R + 0.4), Math.sin(a) * (R + 0.4), e * 1.6], [0.6, 0.6, 0.6],
                     lit ? '#fff0a0' : '#ff8a4a', { m: 'neon' });
          }
          for (var s2 = 0; s2 < n; s2++) {
            pen.part(w, 'box', [0, 0, e * 1.4], [0.3, R * 2, 0.3], '#d8d0c0', { rz: s2 * Math.PI / n });
          }
        }
        pen.part(f, 'cyl', [0, 0, 0], [1.6, 3.6, 1.6], '#8a8a92', { rx: Math.PI / 2, m: 'metal' });
        for (var c = 0; c < n; c++) {
          var ang = spin + c * TAU / n;
          var cx = Math.cos(ang) * R, cy = Math.sin(ang) * R;
          pen.part(f, 'box', [cx, cy - 1.6, 0], [2.6, 2.2, 2.2], cars[c % cars.length]);
          pen.part(f, 'box', [cx, cy - 0.3, 0], [2.9, 0.3, 2.5], '#f4f0e8');
          pen.part(f, 'box', [cx, cy - 0.15, 0], [0.2, 0.6, 0.2], '#8a8a92', { m: 'metal' });
        }
      }
    };
  });

  /* Fireworks going up over the fair: a rocket climbing on its trail of
     sparks, then a burst of colour opening and falling away. */
  Rigs.register('pb_firework', function (spec, ctx) {
    var every = spec.every || 3.6, H = spec.h || 60, seed = spec.seed || 0;
    var cols = ['#ff5ad8', '#5ae8ff', '#ffe05a', '#7aff7a', '#ff7a3a', '#ffffff'];
    var banged = -1;
    return {
      radius: H + 200,
      update: function (dt, t) {
        var slot = Math.floor((t + seed) / every);
        var ph = ((t + seed) % every) / every;
        if (ph > 0.3 && slot !== banged) {
          banged = slot;
          if (near(ctx, spec.p, 260) && ctx.sound) ctx.sound('pb_pop', spec.p, 0.5);
        }
      },
      draw: function (pen, t) {
        var slot = Math.floor((t + seed) / every), ph = ((t + seed) % every) / every;
        var x = spec.p[0] + (hash(slot * 1.3 + seed) - 0.5) * 40, z = spec.p[2] + (hash(slot * 2.1 + seed) - 0.5) * 40;
        var top = spec.p[1] + H * (0.7 + hash(slot * 3.7) * 0.4);
        var c = cols[slot % cols.length], c2 = cols[(slot + 2) % cols.length];
        if (ph < 0.3) {
          var y = spec.p[1] + (top - spec.p[1]) * (ph / 0.3);
          pen.part(frame([x, y, z], 0, 1), 'sph', [0, 0, 0], [0.8, 1.4, 0.8], '#fff0c0', { m: 'neon' });
          for (var k = 1; k < 5; k++) {
            pen.part(frame([x, y - k * 1.4, z], 0, 1), 'sph', [0, 0, 0], [0.4, 0.4, 0.4], '#ffb84a', { m: 'neon', a: 1 - k / 5 });
          }
          return;
        }
        var b = (ph - 0.3) / 0.7, R = 4 + b * 26, fall = b * b * 10;
        for (var i = 0; i < 28; i++) {
          var u = hash(i * 1.7 + slot) * TAU, v = (hash(i * 2.9 + slot) - 0.5) * Math.PI;
          var px = x + Math.cos(u) * Math.cos(v) * R, py = top + Math.sin(v) * R - fall, pz = z + Math.sin(u) * Math.cos(v) * R;
          pen.part(frame([px, py, pz], 0, 1), 'sph', [0, 0, 0], [0.9, 0.9, 0.9], i % 3 ? c : c2, { m: 'neon', a: 1 - b });
        }
      }
    };
  });

  // ========================================================= the storm
  /* St Elmo's fire: blue-white sparks crackling round the tip of a
     lightning rod (or a storm crystal), jagged, never still. */
  Rigs.register('pb_sparks', function (spec) {
    var R = spec.r || 1.6, n = spec.n || 4, colour = spec.colour || '#9ad8ff', seed = spec.seed || 0;
    return {
      radius: R + 60,
      draw: function (pen, t) {
        var slot = Math.floor(t * 14);
        for (var i = 0; i < n; i++) {
          if (hash(slot * 7.3 + i + seed) < 0.35) continue;
          var a = hash(slot * 3.1 + i * 1.7 + seed) * TAU, e = (hash(slot * 5.9 + i + seed) - 0.3) * 1.2;
          var prev = spec.p;
          for (var k = 1; k <= 3; k++) {
            var rr = R * k / 3, wob = hash(slot + k * 3 + i + seed) - 0.5;
            var pt = [spec.p[0] + Math.cos(a + wob) * rr, spec.p[1] + e * rr + (hash(slot * 2 + k + seed) - 0.5) * 0.6,
                      spec.p[2] + Math.sin(a + wob) * rr];
            var dx = pt[0] - prev[0], dy = pt[1] - prev[1], dz = pt[2] - prev[2];
            var len = Math.hypot(dx, dy, dz) || 0.01;
            pen.part(frame([(prev[0] + pt[0]) / 2, (prev[1] + pt[1]) / 2, (prev[2] + pt[2]) / 2], Math.atan2(dx, dz), 1),
                     'box', [0, 0, 0], [0.12, 0.12, len], colour, { m: 'neon', rx: -Math.asin(Math.max(-1, Math.min(1, dy / len))) });
            prev = pt;
          }
        }
        pen.part(frame(spec.p, 0, 1), 'sph', [0, 0, 0], [0.9, 0.9, 0.9], '#e8f6ff', { m: 'neon', a: 0.6 + 0.4 * Math.sin(t * 30) });
      }
    };
  });

  // ======================================================= the festival
  /* Sky lanterns: paper lanterns let go from a spot one after another,
     rising slowly, swaying, drifting off downwind, fading as they climb. */
  Rigs.register('pb_skylanterns', function (spec) {
    var n = spec.n || 12, H = spec.h || 140, R = spec.r || 10, life = spec.life || 26, seed = spec.seed || 0;
    var wind = spec.wind || [0.6, 0.3];
    var cols = ['#ffb84a', '#ff8a4a', '#ffd86a', '#ff6a5a'];
    return {
      radius: H + 200,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var u = ((t + i * life / n + seed * 3) % life) / life;
          var slot = Math.floor((t + i * life / n + seed * 3) / life);
          var a = hash(i * 3.7 + slot * 1.3 + seed) * TAU, r = R * hash(i * 5.1 + slot);
          var up = u * H, drift = u * u * H * 0.7;
          var x = spec.p[0] + Math.cos(a) * r + wind[0] * drift + Math.sin(t * 0.7 + i) * 1.4;
          var z = spec.p[2] + Math.sin(a) * r + wind[1] * drift + Math.cos(t * 0.6 + i) * 1.4;
          var fade = u < 0.08 ? u / 0.08 : 1 - Math.max(0, (u - 0.7) / 0.3);
          var c = cols[(i + slot) % cols.length];
          var f = child(frame([x, spec.p[1] + up, z], t * 0.2 + i, 1), [0, 0, 0], Math.sin(t * 1.3 + i) * 0.08, 0, 0);
          pen.part(f, 'box', [0, 0, 0], [1.2, 1.6, 1.2], c, { m: 'neon', a: 0.9 * fade });
          pen.part(f, 'sph', [0, 0, 0], [3.4, 3.4, 3.4], c, { m: 'neon', a: 0.16 * fade });
        }
      }
    };
  });

  /* The water lighting up round anybody wading in it: rings of blue
     light spreading from their legs, brighter the deeper they are. */
  Rigs.register('pb_wake', function (spec, ctx) {
    var W = spec.w || 60, D = spec.d || 60, colour = spec.colour || '#5af0ff';
    return {
      radius: Math.max(W, D) / 2 + 40,
      draw: function (pen, t) {
        if (!ctx || !ctx.players || !ctx.water) return;
        var w = ctx.water();
        ctx.players().forEach(function (p, j) {
          var x = p.pos[0], z = p.pos[2];
          if (Math.abs(x - spec.p[0]) > W / 2 || Math.abs(z - spec.p[2]) > D / 2) return;
          var depth = w - p.pos[1];
          if (depth < 0.2) return;
          var k = Math.min(1, depth / 2.5);
          for (var r = 0; r < 3; r++) {
            var u = (t * 0.9 + r / 3 + j * 0.37) % 1;
            pen.part(frame([x, w + 0.04, z], 0, 1), 'torus', [0, 0, 0], [2 + u * 7, 0.3, 2 + u * 7], colour,
                     { m: 'neon', a: (0.25 + 0.5 * k) * (1 - u) });
          }
          pen.part(frame([x, w + 0.03, z], 0, 1), 'cyl', [0, 0, 0], [3.2, 0.04, 3.2], '#c8fcff', { m: 'neon', a: 0.35 * k });
        });
      }
    };
  });

  // ========================================================= the monsoon
  /* A waterfall pouring off a cliff's lip: the curtain arcing out and down
     in ribbons, white streaks racing down it, foam boiling where it lands,
     spray and mist rolling off the pool -- and its roar.  ``p`` is the
     middle of the lip, ``yaw`` the way it pours (local +z), ``w`` how wide,
     ``drop`` how far it falls. */
  Rigs.register('pb_falls', function (spec, ctx) {
    var W = spec.w || 8, H = spec.drop || 20, f0 = frame(spec.p, spec.yaw || 0);
    var cols = Math.max(4, Math.round(W / 1.1)), last = -10;
    function out(u) { return 0.5 + Math.sqrt(u) * 2.4; }
    return {
      radius: H + 80,
      update: function (dt, t) {
        if (!ctx || !ctx.sound || t - last < 2.6) return;
        last = t;
        if (near(ctx, spec.p, 110)) ctx.sound('pb_rush', point(f0, [0, -H, out(1)]), 1);
      },
      draw: function (pen, t) {
        var cw = W / cols + 0.14;
        for (var c = 0; c < cols; c++) {
          var x = -W / 2 + (c + 0.5) * W / cols, wob = Math.sin(c * 2.1 + t * 0.7) * 0.12;
          for (var s = 0; s < 4; s++) {
            var u0 = s / 4, u1 = (s + 1) / 4, dy = (u1 - u0) * H, dz = out(u1) - out(u0);
            pen.part(f0, 'box', [x, -(u0 + u1) / 2 * H, (out(u0) + out(u1)) / 2 + wob],
                     [cw, Math.hypot(dy, dz) + 0.1, 0.35], (c + s) % 2 ? '#bfe0ec' : '#cfe8f2',
                     { a: 0.58, rx: Math.atan2(-dz, dy) });
          }
          for (var k = 0; k < 3; k++) {
            var u = (t * (0.8 + hash(c * 3.1 + k) * 0.5) + k / 3 + hash(c)) % 1;
            pen.part(f0, 'box', [x + (hash(c + k * 7) - 0.5) * 0.5, -u * H, out(u) + wob + 0.25],
                     [0.35, 1.4 + u * 2.6, 0.12], '#ffffff', { a: 0.85 });
          }
        }
        // the lip, white where it breaks over; the foam where it lands
        pen.part(f0, 'box', [0, 0.05, 0.35], [W + 0.6, 0.35, 1.0], '#eef8fc', { a: 0.85 });
        pen.part(f0, 'cyl', [0, -H + 0.1, out(1) + 1.6], [W + 3, 0.18, 6], '#e8f4f8', { a: 0.65 });
        for (var j = 0; j < 12; j++) {
          var q = (t * 0.9 + j / 12) % 1, xx = (hash(j * 1.7) - 0.5) * (W + 1);
          pen.part(f0, 'sph', [xx, -H + 0.3 + Math.sin(q * Math.PI) * 1.6, out(1) + 0.4 + q * 5],
                   [1.4 + q * 2.4, 1.0 + q * 1.2, 1.4 + q * 2.4], '#f4fafc', { a: 0.7 * (1 - q) });
        }
        if (!pen.near) return;
        for (var m = 0; m < 6; m++) {
          var v = (t * 0.1 + m / 6) % 1;
          pen.part(f0, 'sph', [Math.sin(m * 2.3 + t * 0.2) * W * 0.6, -H + 2 + v * 10, out(1) + 2 + v * 11],
                   [5 + v * 8, 4 + v * 5, 5 + v * 8], '#eef6fa', { a: 0.16 * (1 - v) });
        }
      }
    };
  });

  /* Bunting: a cord sagging from ``p`` to ``q`` -- or through ``path``, a
     list of offsets from ``p`` (``loop`` closes it) -- pennants in a row
     along it, fluttering. */
  Rigs.register('pb_bunting', function (spec) {
    var pts = [spec.p];
    if (spec.path) {
      spec.path.forEach(function (o) { pts.push([spec.p[0] + o[0], spec.p[1] + o[1], spec.p[2] + o[2]]); });
      if (spec.path.length && !spec.from_p) pts.shift();
      if (spec.loop) pts.push(pts[0]);
    } else if (spec.q) {
      pts.push(spec.q);
    }
    var sag = spec.sag === undefined ? 1.0 : spec.sag, size = spec.size || 1.0;
    var cols = spec.colours || ['#f0a830', '#d83a8a', '#2aa8a0', '#3a4aa8', '#8ac83a', '#c8302a'];
    var span = 0;
    for (var i = 1; i < pts.length; i++) span = Math.max(span, Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][2] - pts[i - 1][2]));
    return {
      radius: span + 60,
      draw: function (pen, t) {
        var c = 0;
        for (var k = 1; k < pts.length; k++) {
          var a = pts[k - 1], b = pts[k];
          var len = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
          var yaw = Math.atan2(b[0] - a[0], b[2] - a[2]);
          var at = function (v) {
            return [a[0] + (b[0] - a[0]) * v, a[1] + (b[1] - a[1]) * v - Math.sin(v * Math.PI) * sag, a[2] + (b[2] - a[2]) * v];
          };
          var last = at(0);
          for (var j = 1; j <= 8; j++) { var pt = at(j / 8); pen.rod(last, pt, 0.06, '#efe6d6'); last = pt; }
          if (!pen.near) continue;
          var n = Math.max(2, Math.round(len / (1.5 * size)));
          for (var i2 = 0; i2 < n; i2++) {
            var f = child(frame(at((i2 + 0.5) / n), yaw), [0, 0, 0], 0, 0, Math.sin(t * 3 + i2 * 0.9 + k) * 0.35);
            pen.part(f, 'tri', [0, -0.55 * size, 0], [1.0 * size, 1.1 * size, 0.5], cols[c++ % cols.length],
                     { ry: Math.PI / 2, rz: Math.PI });
          }
        }
      }
    };
  });

  /* Koi circling a pond (``r`` its radius, ``p`` the middle of its
     surface): orange, white and gold, tails swishing, one now and then
     rising to kiss the surface. */
  Rigs.register('pb_koi', function (spec) {
    var n = spec.n || 5, R = spec.r || 3;
    var cols = ['#ff7a2a', '#f4f0e8', '#ffc84a', '#e84a2a', '#f8f8f8', '#ff9a4a'];
    var spots = ['#f4f0e8', '#e84a2a', '#ff7a2a', '#f8f8f8', '#2a2a2a', '#f4f0e8'];
    return {
      radius: 50,
      draw: function (pen, t) {
        if (!pen.near) return;
        for (var i = 0; i < n; i++) {
          var dir = i % 2 ? 1 : -1, sp = 0.22 + hash(i) * 0.2;
          var a = t * sp * dir + i * TAU / n;
          var r = R * (0.4 + 0.4 * hash(i * 3.3)) + Math.sin(t * 0.3 + i) * R * 0.1;
          var x = spec.p[0] + Math.cos(a) * r, z = spec.p[2] + Math.sin(a) * r;
          var rise = Math.max(0, Math.sin(t * 0.4 + i * 2.1) - 0.85) * 1.6;
          var f = frame([x, spec.p[1] - 0.22 + rise, z], Math.atan2(-Math.sin(a) * dir, Math.cos(a) * dir));
          var sw = Math.sin(t * 6 + i) * 0.45;
          pen.part(f, 'sph', [0, 0, 0], [0.5, 0.3, 1.3], cols[i % cols.length]);
          pen.part(f, 'sph', [0.05, 0.1, 0.15], [0.3, 0.14, 0.45], spots[i % spots.length]);
          pen.part(child(f, [0, 0, -0.55], 0, sw, 0), 'tri', [0, 0, -0.25], [0.6, 0.55, 0.4], cols[(i + 2) % cols.length],
                   { rx: Math.PI / 2 });
        }
      }
    };
  });

  /* Rain on still water: rings spreading where the drops land, over an
     area ``w`` by ``d`` at the rig's height -- or only in ``spots``
     ([dx, dz, r] offsets: the puddles on a street). */
  Rigs.register('pb_ripples', function (spec, ctx) {
    var W = spec.w || 20, D = spec.d || 20, n = spec.n || 16, seed = spec.seed || 0, spots = spec.spots;
    return {
      radius: Math.max(W, D) / 2 + 30,
      draw: function (pen, t) {
        if (!pen.near) return;
        var y = afloat(spec, ctx, 0) + 0.03;
        for (var i = 0; i < n; i++) {
          var period = 1.0 + hash(seed + i * 1.3) * 0.9;
          var cyc = t / period + hash(seed + i * 2.7), slot = Math.floor(cyc), u = cyc - slot;
          var x, z, rr = 1;
          if (spots && spots.length) {
            var sp = spots[i % spots.length], ang = hash(seed + i * 5.1 + slot * 0.37) * TAU;
            var rad = sp[2] * 0.7 * Math.sqrt(hash(seed + i * 7.3 + slot * 0.53));
            x = spec.p[0] + sp[0] + Math.cos(ang) * rad; z = spec.p[2] + sp[1] + Math.sin(ang) * rad;
            rr = Math.min(1, sp[2] / 3);
          } else {
            x = spec.p[0] + (hash(seed + i * 5.1 + slot * 0.37) - 0.5) * W;
            z = spec.p[2] + (hash(seed + i * 7.3 + slot * 0.53) - 0.5) * D;
          }
          var s = (0.3 + u * 2.4) * rr;
          pen.part(frame([x, y, z], 0), 'torus', [0, 0, 0], [s, 0.08, s], '#eef6fa', { a: 0.6 * (1 - u) });
        }
      }
    };
  });

  /* A rainbow arching over the sky, the sun breaking through: seven bands,
     faint, brightening and fading as the cloud moves.  ``r`` its radius;
     ``yaw`` turns it to face the island. */
  Rigs.register('pb_rainbow', function (spec) {
    var R = spec.r || 240, f0 = frame(spec.p, spec.yaw || 0), segs = 30;
    var bands = ['#ff4a4a', '#ff9a3a', '#ffe04a', '#5ad85a', '#4aa8ff', '#5a5ae0', '#a05ad8'];
    var bw = R * 0.016;
    return {
      radius: R + 2000,
      draw: function (pen, t) {
        var glow = (spec.a || 0.22) * (0.75 + 0.25 * Math.sin(t * 0.06));
        for (var k = 0; k < bands.length; k++) {
          var r = R - k * bw;
          for (var s = 0; s < segs; s++) {
            var a0 = Math.PI * s / segs, a1 = Math.PI * (s + 1) / segs, am = (a0 + a1) / 2;
            pen.part(f0, 'box', [Math.cos(am) * r, Math.sin(am) * r, 0], [bw, r * (a1 - a0) + 0.5, 0.4], bands[k],
                     { a: glow, m: 'neon', rz: am });
          }
        }
      }
    };
  });

  /* Blossom petals drifting down from a tree (``r`` round its crown at
     ``p``, falling ``h``), turning over as they go. */
  Rigs.register('pb_petals', function (spec) {
    var n = spec.n || 18, R = spec.r || 4, H = spec.h || 8, seed = spec.seed || 0;
    var cols = spec.colours || ['#ffc8dc', '#ffb0cc', '#fff0f4', '#ff9ac0'];
    return {
      radius: 40,
      draw: function (pen, t) {
        if (!pen.near) return;
        for (var i = 0; i < n; i++) {
          var life = 5 + hash(seed + i) * 3, cyc = t / life + hash(seed + i * 2.3), slot = Math.floor(cyc), u = cyc - slot;
          var a = hash(seed + i * 4.1 + slot) * TAU, r = R * Math.sqrt(hash(seed + i * 6.7 + slot));
          var x = spec.p[0] + Math.cos(a) * r + Math.sin(t * 1.3 + i) * 0.8 + u * 2.0;
          var z = spec.p[2] + Math.sin(a) * r + Math.cos(t * 1.1 + i) * 0.8 + u * 1.2;
          pen.part(frame([x, spec.p[1] - u * H, z], t * 2 + i), 'box', [0, 0, 0], [0.35, 0.05, 0.28], cols[i % cols.length],
                   { rx: Math.sin(t * 3 + i) * 0.9, a: u > 0.9 ? (1 - u) * 10 : 1 });
        }
      }
    };
  });

  /* A cantilevered fishing net at a pier's end: the boom pivoting on its
     frame, the net on four spars dipping into the sea, hanging there, then
     hauled up streaming water with fish flashing in it; stone weights on
     ropes swinging at the back end.  ``yaw`` points the boom out to sea,
     ``len`` how long it is. */
  Rigs.register('pb_fishnet', function (spec, ctx) {
    var L = spec.len || 16, f0 = frame(spec.p, spec.yaw || 0), period = spec.period || 18, seed = spec.seed || 0;
    return {
      radius: L + 60,
      draw: function (pen, t) {
        var ph = ((t + seed * 5) % period) / period;
        // up (0..0.35) -> lowering (..0.5) -> in the water (..0.75) -> hauling up (..1)
        var dip = ph < 0.35 ? 0 : ph < 0.5 ? (ph - 0.35) / 0.15 : ph < 0.75 ? 1 : 1 - (ph - 0.75) / 0.25;
        dip = dip * dip * (3 - 2 * dip);
        var tilt = -0.22 + dip * 0.48;                  // boom pitch: tip up, then down into the water
        // the A-frame the boom pivots on
        pen.rod(point(f0, [-1.6, 0, 0]), point(f0, [0, 3.6, 0]), 0.35, '#6a4a2a');
        pen.rod(point(f0, [1.6, 0, 0]), point(f0, [0, 3.6, 0]), 0.35, '#6a4a2a');
        var piv = child(f0, [0, 3.6, 0], tilt, 0, 0);
        pen.part(piv, 'box', [0, 0, L * 0.35], [0.4, 0.4, L * 1.3], '#7a5a3a');
        // the stone weights hanging off the back end
        for (var w = 0; w < 3; w++) {
          var back = point(piv, [0, 0, -L * 0.3 + w * 0.9]);
          var sw = Math.sin(t * 1.4 + w) * 0.25;
          var hang = [back[0] + sw, back[1] - 1.0 - w * 0.3, back[2]];
          pen.rod(back, hang, 0.08, '#c8b898');
          pen.part(frame(hang, w), 'box', [0, -0.35, 0], [0.8, 0.7, 0.7], '#8a8478');
        }
        // the spars and the net at the tip
        var tip = point(piv, [0, 0, L]);
        var corners = [[-4, -3.0, 3.2], [4, -3.0, 3.2], [4, -3.0, -3.2], [-4, -3.0, -3.2]];
        var cw = corners.map(function (c) { return [tip[0] + c[0] * Math.cos(spec.yaw || 0) + c[2] * Math.sin(spec.yaw || 0),
                                                   tip[1] + c[1], tip[2] - c[0] * Math.sin(spec.yaw || 0) + c[2] * Math.cos(spec.yaw || 0)]; });
        cw.forEach(function (c) { pen.rod(tip, c, 0.14, '#8a6a42'); });
        var mid = [tip[0], tip[1] - 4.0, tip[2]];
        for (var i = 0; i < 4; i++) {
          var a = cw[i], b = cw[(i + 1) % 4];
          pen.rod(a, b, 0.05, '#e8e0c8');
          pen.rod(a, mid, 0.05, '#e8e0c8');
          pen.rod([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2], mid, 0.04, '#e8e0c8');
        }
        pen.part(frame(mid, 0), 'sph', [0, 0.5, 0], [6.4, 1.4, 5.0], '#d8d0b8', { a: 0.35 });
        // hauled up: fish flashing in the net, water streaming off it
        if (dip < 0.6 && ph > 0.75 && pen.near) {
          for (var k = 0; k < 6; k++) {
            var fl = Math.sin(t * 9 + k * 2.3);
            pen.part(frame([mid[0] + (hash(k) - 0.5) * 3, mid[1] + 0.9 + Math.abs(fl) * 0.4, mid[2] + (hash(k + 3) - 0.5) * 2.4], t * 4 + k),
                     'box', [0, 0, 0], [0.2, 0.3, 0.9], k % 2 ? '#c8d8e8' : '#e8f0f8', { m: 'metal', rz: fl });
          }
          for (var d = 0; d < 6; d++) {
            var q = (t * 1.8 + d / 6) % 1;
            pen.part(frame([mid[0] + (hash(d * 2) - 0.5) * 5, mid[1] - q * 3, mid[2] + (hash(d * 5) - 0.5) * 4], 0),
                     'box', [0, 0, 0], [0.1, 0.8, 0.1], '#e8f6fc', { a: 0.6 * (1 - q) });
          }
        }
        if (ctx && ctx.water && dip > 0.8 && pen.near) {
          var wy = ctx.water();
          for (var r = 0; r < 2; r++) {
            var u = (t * 0.7 + r / 2) % 1;
            pen.part(frame([mid[0], wy + 0.05, mid[2]], 0), 'torus', [0, 0, 0], [6 + u * 6, 0.12, 6 + u * 6], '#eef6fa',
                     { a: 0.5 * (1 - u) });
          }
        }
      }
    };
  });

  // ============================================================ sounds
  var GA = global.GameAudio;
  if (GA && GA.register) {
    GA.register('pb_squawk', function (vol) {
      this.tone({ type: 'sawtooth', freq: 1400, freqEnd: 900, dur: 0.12, gain: 0.05 * vol });
      this.later(140, function () { this.tone({ type: 'sawtooth', freq: 1600, freqEnd: 1100, dur: 0.16, gain: 0.05 * vol }); });
    });
    GA.register('pb_rush', function (vol) {
      // a waterfall: a low roar and the hiss of the spray over it
      this.noise({ filter: 'lowpass', freq: 600, dur: 2.8, gain: 0.08 * vol });
      this.noise({ filter: 'bandpass', freq: 2200, dur: 2.8, gain: 0.025 * vol });
    });
    GA.register('pb_pop', function (vol) {
      this.noise({ freq: 1200, freqEnd: 200, dur: 0.3, gain: 0.25 * vol });
      this.later(90, function () {
        for (var i = 0; i < 8; i++) {
          this.later(i * 40, function () { this.noise({ filter: 'highpass', freq: 4000, freqEnd: 2500, dur: 0.03, gain: 0.05 * vol }); });
        }
      });
    });
  }
})(window);
