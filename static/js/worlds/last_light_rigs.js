/* Last Light's living scenery: the rig kinds the newer places use.

   Each place lists its rigs in markers.extra.rigs (the Last Light kit's
   Area.rig()); static/js/game/rigs.js builds them from the kinds registered
   here and the world's plugin (last_light.js) draws them every frame and
   tells them what happens -- 'wave' and 'cleared' (a wave starting and
   ending), 'lure' (the place's noise-maker going off), 'kill' (an infected
   dying, with where), 'blast' (a fuel barrel), 'roar' (a Tank), 'scream',
   'wipe', 'shot' and 'lightning'.  ctx.players() and ctx.zombies() say
   where everybody is; ctx.wave() is the wave, its phase and whether the
   lure is sounding.  Nothing here is solid. */
(function (global) {
  'use strict';
  var Rigs = global.Rigs;
  if (!Rigs) return;
  var GA = global.GameAudio;
  var TAU = Math.PI * 2;
  var frame = Rigs.frame, child = Rigs.child, point = Rigs.point;
  var approach = Rigs.approach, approachAngle = Rigs.approachAngle;
  var wander = Rigs.wander, hash = Rigs.hash, clamp = Rigs.clamp;

  /* The nearest of ``list`` (each with .pos) to ``p``, within ``reach``. */
  function nearest(list, p, reach) {
    var best = null, bd = reach || 1e9;
    for (var i = 0; i < list.length; i++) {
      var q = list[i].pos;
      if (!q) continue;
      var d = Math.hypot(q[0] - p[0], q[2] - p[2]);
      if (d < bd) { bd = d; best = list[i]; }
    }
    return best ? { who: best, d: bd } : null;
  }

  /* Heading (yaw) from a to b on the ground. */
  function heading(a, b) { return Math.atan2(b[0] - a[0], b[2] - a[2]); }

  // ------------------------------------------------------- the places
  // (each new place's kinds go here)

  // ============================================== Starlite Drive-In
  if (GA) {
    GA.register('ll_movie', function (vol) {
      // the B-movie at full blast: a theremin wail over a brass stab, and
      // the monster's roar under it
      this.tone({ type: 'sine', freq: 520, freqEnd: 980, dur: 1.6, gain: 0.09 * vol });
      this.later(700, function () { this.tone({ type: 'sine', freq: 980, freqEnd: 440, dur: 1.4, gain: 0.08 * vol }); });
      [196, 247, 294, 370].forEach(function (f) {
        this.tone({ type: 'sawtooth', freq: f, dur: 0.9, gain: 0.05 * vol });
      }, this);
      this.later(900, function () {
        this.tone({ type: 'sawtooth', freq: 90, freqEnd: 50, dur: 1.8, gain: 0.22 * vol });
        this.noise({ freq: 500, freqEnd: 90, dur: 1.8, gain: 0.22 * vol });
      });
    });
    GA.register('ll_honk', function (vol) {
      this.tone({ type: 'square', freq: 392, dur: 0.32, gain: 0.08 * vol });
      this.tone({ type: 'square', freq: 494, dur: 0.32, gain: 0.06 * vol });
      this.later(420, function () {
        this.tone({ type: 'square', freq: 392, dur: 0.5, gain: 0.08 * vol });
        this.tone({ type: 'square', freq: 494, dur: 0.5, gain: 0.06 * vol });
      });
    });
    GA.register('ll_creak', function (vol) {
      this.tone({ type: 'sawtooth', freq: 180, freqEnd: 260, dur: 0.5, gain: 0.03 * vol });
      this.noise({ filter: 'bandpass', freq: 900, freqEnd: 1400, dur: 0.5, gain: 0.03 * vol });
    });
    GA.register('ll_caw', function (vol) {
      for (var i = 0; i < 3; i++) {
        this.later(i * 260, function () {
          this.noise({ filter: 'bandpass', freq: 1300, freqEnd: 700, dur: 0.22, gain: 0.08 * vol });
          this.tone({ type: 'sawtooth', freq: 700, freqEnd: 520, dur: 0.2, gain: 0.03 * vol });
        });
      }
    });
  }

  function textDecal(text, bg, fg, aspect) {
    return 't~' + text + '~' + bg + '~' + fg + '~' + aspect.toFixed(2);
  }

  /* The picture on the screen.  The feature plays through a wave: the
     city at night, searchlights, a blocky giant stomping through it, the
     close-up, the crowd running, the title card -- round and round.  Between
     waves it is the intermission card with the dancing snacks and the time
     to the next feature; when the lure goes the monster comes right up to
     the glass and roars; a wipe is THE END. */
  Rigs.register('movie_screen', function (spec) {
    var W = spec.w || 150, H = spec.h || 50;
    var f = frame(spec.p, spec.yaw || 0);
    var st = { lure: -1, end: -1, roar: -10, flick: 1, next: 0 };
    function card(pen, x, y, w, h, colour, a, z) {
      pen.part(f, 'box', [x, y, z || 0.12], [w, h, 0.04], colour, { m: 'neon', a: a === undefined ? 1 : a });
    }
    function giant(pen, x, y, s, t, near) {
      // the Block Person: a blocky silhouette with two lit eyes
      var step = Math.sin(t * 2.2), arm = Math.sin(t * 2.2 + 1.2);
      var c = '#0c0e14';
      card(pen, x - 3 * s + step * 1.5 * s, y + 6 * s, 4 * s, 12 * s, c, 1, 0.2);
      card(pen, x + 3 * s - step * 1.5 * s, y + 6 * s, 4 * s, 12 * s, c, 1, 0.2);
      card(pen, x, y + 19 * s, 12 * s, 14 * s, c, 1, 0.22);
      card(pen, x - 8.5 * s, y + 18 * s + arm * 3 * s, 4 * s, 13 * s, c, 1, 0.24);
      card(pen, x + 8.5 * s, y + 18 * s - arm * 3 * s, 4 * s, 13 * s, c, 1, 0.24);
      card(pen, x, y + 30.5 * s, 8 * s, 8 * s, c, 1, 0.22);
      var glow = near ? '#ff3a2a' : '#ffd84a';
      card(pen, x - 2 * s, y + 31 * s, 1.6 * s, 1.2 * s, glow, 1, 0.26);
      card(pen, x + 2 * s, y + 31 * s, 1.6 * s, 1.2 * s, glow, 1, 0.26);
    }
    function city(pen, t, tone) {
      card(pen, 0, 0, W, H, tone, 0.96, 0.08);
      // searchlights sweeping the clouds
      for (var k = 0; k < 3; k++) {
        var a = Math.sin(t * 0.6 + k * 2.1) * 0.6;
        pen.part(f, 'box', [-W * 0.3 + k * W * 0.3, -H * 0.2, 0.1], [1.6, H * 0.9, 0.03], '#cfd8ff',
                 { m: 'neon', a: 0.25, rz: a });
      }
      // the skyline, its windows going out one by one
      for (var i = 0; i < 12; i++) {
        var bw = 8 + hash(i) * 6, bh = 8 + hash(i + 7) * 16;
        var bx = -W / 2 + 6 + i * (W - 12) / 11;
        card(pen, bx, -H / 2 + bh / 2, bw, bh, '#0a0c12', 1, 0.16);
        for (var j = 0; j < 3; j++) {
          if (hash(i * 13 + j + Math.floor(t * 0.3)) < 0.5) continue;
          card(pen, bx - bw * 0.2 + (j % 2) * bw * 0.4, -H / 2 + 3 + j * 4, 1.4, 1.2, '#ffd27a', 1, 0.18);
        }
      }
    }
    return {
      radius: W * 0.7,
      event: function (kind) {
        var t = Rigs.clock();
        if (kind === 'lure') st.lure = t + 16;
        else if (kind === 'wipe') st.end = t + 14;
        else if (kind === 'roar') st.roar = t;
      },
      draw: function (pen, t, ctx) {
        // the projector's flicker
        if (t > st.next) { st.flick = 0.86 + Math.random() * 0.14; st.next = t + 0.05 + Math.random() * 0.12; }
        var info = ctx.wave ? ctx.wave() : { phase: 'active' };
        var k = st.flick;
        if (t < st.end) {
          card(pen, 0, 0, W, H, '#0a0a0a', 0.97 * k, 0.08);
          pen.part(f, 'box', [0, 0, 0.2], [W * 0.5, H * 0.3, 0.04], '#0a0a0a',
                   { m: 'neon', dec: textDecal('THE END', '#0a0a0a', '#f2e8c8', W * 0.5 / (H * 0.3)) });
          return;
        }
        if (t < st.lure || t - st.roar < 4) {
          // the close-up: the giant's face fills the screen, roaring
          var jaw = 0.5 + 0.5 * Math.sin(t * 9);
          var flash = Math.sin(t * 13) > 0.6 ? '#5a0a0a' : '#1a0606';
          card(pen, 0, 0, W, H, flash, 0.97 * k, 0.08);
          card(pen, 0, 4, W * 0.62, H * 0.82, '#2a2d36', 1, 0.14);
          card(pen, -W * 0.15, H * 0.16, W * 0.12, H * 0.12, '#ff3a2a', 1, 0.18);
          card(pen, W * 0.15, H * 0.16, W * 0.12, H * 0.12, '#ff3a2a', 1, 0.18);
          card(pen, 0, -H * 0.14 - jaw * 3, W * 0.36, H * 0.12 + jaw * 6, '#0a0204', 1, 0.18);
          for (var tooth = 0; tooth < 6; tooth++) {
            card(pen, -W * 0.15 + tooth * W * 0.06, -H * 0.06, 2.2, 3, '#f2f2e6', 1, 0.2);
          }
          pen.part(f, 'box', [0, -H * 0.4, 0.22], [W * 0.7, H * 0.12, 0.04], '#1a0606',
                   { m: 'neon', dec: textDecal('THE BLOCK PEOPLE ARE COMING!', '#1a0606', '#ffe28a',
                                               W * 0.7 / (H * 0.12)) });
          return;
        }
        if (info.phase !== 'active') {
          // intermission: the snacks dance, the clock counts down
          card(pen, 0, 0, W, H, '#1a3a6a', 0.95 * k, 0.08);
          card(pen, 0, H * 0.32, W * 0.8, H * 0.2, '#f2b01e', 1, 0.12);
          pen.part(f, 'box', [0, H * 0.32, 0.16], [W * 0.76, H * 0.18, 0.04], '#f2b01e',
                   { m: 'neon', dec: textDecal('INTERMISSION', '#f2b01e', '#1a1a1a', W * 0.76 / (H * 0.18)) });
          var hop = Math.abs(Math.sin(t * 3.2)) * 5;
          // the hot dog
          card(pen, -W * 0.22, -H * 0.08 + hop, 22, 7, '#d8a050', 1, 0.14);
          card(pen, -W * 0.22, -H * 0.08 + hop + 1.6, 26, 4, '#b8482a', 1, 0.16);
          card(pen, -W * 0.22 - 4, -H * 0.08 + hop + 2.2, 1.4, 1.4, '#f2f2f2', 1, 0.18);
          card(pen, -W * 0.22 + 4, -H * 0.08 + hop + 2.2, 1.4, 1.4, '#f2f2f2', 1, 0.18);
          // the soda cup, on the other beat
          var hop2 = Math.abs(Math.sin(t * 3.2 + 1.6)) * 5;
          card(pen, W * 0.22, -H * 0.06 + hop2, 12, 16, '#e83a3a', 1, 0.14);
          card(pen, W * 0.22, -H * 0.06 + hop2 + 9, 14, 2, '#f2f2f2', 1, 0.16);
          card(pen, W * 0.22 + 2, -H * 0.06 + hop2 + 14, 1, 8, '#f2f2f2', 1, 0.16);
          card(pen, W * 0.22 - 3, -H * 0.06 + hop2 + 2, 1.4, 1.4, '#f2f2f2', 1, 0.18);
          card(pen, W * 0.22 + 3, -H * 0.06 + hop2 + 2, 1.4, 1.4, '#f2f2f2', 1, 0.18);
          var left = Math.max(0, Math.ceil(info.left || 0));
          var line = left > 0 ? 'NEXT FEATURE IN ' + left + 's  -  VISIT THE SNACK BAR' : 'VISIT THE SNACK BAR';
          pen.part(f, 'box', [0, -H * 0.36, 0.16], [W * 0.8, H * 0.12, 0.04], '#1a3a6a',
                   { m: 'neon', dec: textDecal(line, '#1a3a6a', '#f2f2f2', W * 0.8 / (H * 0.12)) });
          return;
        }
        // the feature, in reels: city and giant, the close-up, the crowd,
        // the title card
        var reel = t % 44;
        if (reel < 18) {
          city(pen, t, '#101a3a');
          var gx = -W / 2 - 20 + ((reel / 18) * (W + 40));
          giant(pen, gx, -H / 2, 1.0, t, false);
          // a plane buzzing it
          var px = W / 2 - ((t * 18) % (W + 20));
          card(pen, px, H * 0.32, 6, 1.4, '#0c0e14', 1, 0.2);
          card(pen, px, H * 0.32, 1.4, 4, '#0c0e14', 1, 0.2);
        } else if (reel < 26) {
          city(pen, t, '#1a1030');
          giant(pen, 0, -H / 2 - 30, 2.2, t, true);
        } else if (reel < 34) {
          card(pen, 0, 0, W, H, '#2a2a3a', 0.95 * k, 0.08);
          for (var n = 0; n < 18; n++) {
            var rx = ((n * 17 + (t * (30 + hash(n) * 20))) % (W + 20)) - W / 2 - 10;
            var ry = -H / 2 + 3 + hash(n + 3) * 10;
            card(pen, rx, ry + Math.abs(Math.sin(t * 9 + n)) * 1.2, 2, 5, '#0c0e14', 1, 0.16);
          }
          pen.part(f, 'box', [0, H * 0.22, 0.16], [W * 0.3, H * 0.24, 0.04], '#2a2a3a',
                   { m: 'neon', dec: textDecal('RUN!', '#2a2a3a', '#ff4a3a', W * 0.3 / (H * 0.24)) });
        } else {
          card(pen, 0, 0, W, H, '#100c08', 0.97 * k, 0.08);
          pen.part(f, 'box', [0, 6, 0.16], [W * 0.86, H * 0.3, 0.04], '#100c08',
                   { m: 'neon', dec: textDecal('ATTACK OF THE BLOCK PEOPLE', '#100c08', '#f2d84a',
                                               W * 0.86 / (H * 0.3)) });
          pen.part(f, 'box', [0, -H * 0.3, 0.16], [W * 0.5, H * 0.1, 0.04], '#100c08',
                   { m: 'neon', dec: textDecal('IN BLOCKORAMA', '#100c08', '#c8c8c8', W * 0.5 / (H * 0.1)) });
        }
        // scratches on the film
        if (hash(Math.floor(t * 8)) > 0.7) {
          card(pen, (hash(Math.floor(t * 8) + 1) - 0.5) * W, 0, 0.4, H, '#f2f2f2', 0.4, 0.3);
        }
      }
    };
  });

  /* The beam from the booth's port to the screen: a long, faint cone with
     dust drifting in it, flickering with the film. */
  Rigs.register('projector_beam', function (spec) {
    var a = spec.to_p, b = spec.p;
    var dx = b[0] - a[0], dy = b[1] - a[1], dz = b[2] - a[2];
    var len = Math.sqrt(dx * dx + dy * dy + dz * dz);
    var yaw = Math.atan2(dx, dz), pitch = Math.atan2(Math.sqrt(dx * dx + dz * dz), dy);
    var mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];
    var f = { p: mid, r: Rigs.rot(pitch, yaw, 0), s: 1 };
    var motes = [];
    for (var i = 0; i < 26; i++) motes.push({ u: hash(i), r1: hash(i + 40) - 0.5, r2: hash(i + 80) - 0.5, s: 0.4 + hash(i + 9) });
    return {
      radius: len,
      draw: function (pen, t, ctx) {
        var info = ctx.wave ? ctx.wave() : {};
        var k = 0.05 + 0.02 * Math.sin(t * 37) + (info.lure ? 0.04 : 0);
        pen.part(f, 'cone', [0, 0, 0], [(spec.w || 150) * 0.98, len, (spec.h || 50) * 0.98], '#d8e8ff',
                 { m: 'neon', a: k });
        pen.part(f, 'cone', [0, len * 0.3, 0], [(spec.w || 150) * 0.38, len * 0.4, (spec.h || 50) * 0.38],
                 '#ffffff', { m: 'neon', a: k * 0.8 });
        if (!pen.near) return;
        for (var m = 0; m < motes.length; m++) {
          var q = motes[m];
          var u = (q.u + t * 0.01 * q.s) % 1;
          var spread = u;
          var p = Rigs.point(f, [q.r1 * (spec.w || 150) * spread * 0.8 + Math.sin(t + m) * 0.6,
                                 len / 2 - u * len,
                                 q.r2 * (spec.h || 50) * spread * 0.8]);
          pen.part(frame(p, 0), 'box', [0, 0, 0], [0.22, 0.22, 0.22], '#fff6d8', { m: 'neon', a: 0.7 });
        }
      }
    };
  });

  /* The two reels on top of the projector, feeding and taking up; the
     lure runs them at a gallop. */
  Rigs.register('film_reels', function (spec) {
    var f = frame(spec.p, spec.yaw || 0);
    var spin = 0, last = 0;
    return {
      radius: 12,
      draw: function (pen, t, ctx) {
        var info = ctx.wave ? ctx.wave() : {};
        var dt = last ? Math.min(0.1, t - last) : 0;
        last = t;
        spin += dt * (info.lure ? 9 : 2.2);
        [[0, 0, -3.2, 1.0], [0, -0.6, 3.6, 0.8]].forEach(function (r, i) {
          var reel = child(f, [r[0], r[1] + 1.2, r[2]], i ? spin * 1.3 : spin, 0, 0);
          pen.part(reel, 'cyl', [0, 0, 0], [4.6 * r[3], 0.5, 4.6 * r[3]], '#8a8f94',
                   { m: 'metal', rz: Math.PI / 2 });
          for (var sp = 0; sp < 3; sp++) {
            pen.part(reel, 'box', [0.3, 0, 0], [0.2, 4.2 * r[3], 0.5], '#2a2d31', { rx: sp * Math.PI / 3 });
          }
        });
        // the arms that hold them
        pen.part(f, 'box', [0, 0.4, -3.2], [0.4, 1.4, 0.4], '#3a3f46');
        pen.part(f, 'box', [0, 0.1, 3.6], [0.4, 0.9, 0.4], '#3a3f46');
      }
    };
  });

  /* The flying saucer on its pole over the booth: turning, its rim lights
     chasing, bobbing on the pole's spring -- and when the lure goes, a
     tractor beam down onto the roof. */
  Rigs.register('flying_saucer', function (spec) {
    var f0 = frame(spec.p, 0);
    var beam = -1;
    return {
      radius: 20,
      event: function (kind) { if (kind === 'lure') beam = Rigs.clock() + 16; },
      draw: function (pen, t) {
        var bob = Math.sin(t * 1.3) * 0.5;
        var f = child(f0, [0, bob, 0], Math.sin(t * 0.7) * 0.06, t * 0.8, Math.cos(t * 0.6) * 0.06);
        pen.part(f, 'sph', [0, 0, 0], [12, 2.2, 12], '#b8c0c8', { m: 'metal' });
        pen.part(f, 'sph', [0, 1.2, 0], [5, 3.4, 5], '#9ad8e8', { m: 'glass', a: 0.75 });
        pen.part(f, 'sph', [0, 0.9, 0], [1.4, 1.6, 1.4], '#6fae55');
        for (var i = 0; i < 10; i++) {
          var a = i / 10 * TAU;
          var on = (i + Math.floor(t * 8)) % 3 === 0;
          pen.part(f, 'sph', [Math.cos(a) * 5.6, -0.2, Math.sin(a) * 5.6], [0.8, 0.8, 0.8],
                   on ? '#ff4a8a' : '#4ae8ff', { m: 'neon' });
        }
        if (t < beam) {
          pen.part(f0, 'cone', [0, -4.6, 0], [7, 9, 7], '#9affa0', { m: 'neon', a: 0.22 + 0.08 * Math.sin(t * 12) });
        }
      }
    };
  });

  /* The swings: they sway in the wind -- and the middle one swings high
     on its own, empty, until somebody comes near, and then it stops dead. */
  Rigs.register('swing_set', function (spec, ctx) {
    var f = frame(spec.p, spec.yaw || 0);
    var n = spec.n || 3, span = spec.span || 24;
    var amp = [], phase = [];
    for (var i = 0; i < n; i++) { amp.push(0.08); phase.push(i * 1.7); }
    var lastCreak = 0;
    return {
      radius: span,
      update: function (dt, t, ctx2) {
        var near = nearest(ctx2.players ? ctx2.players() : [], spec.p, 26);
        for (var i = 0; i < n; i++) {
          var target = (i === Math.floor(n / 2) && !near) ? 0.9 : 0.06 + 0.04 * Math.sin(t * 0.3 + i);
          amp[i] = approach(amp[i], target, near && i === Math.floor(n / 2) ? 6 : 0.4, dt);
        }
      },
      draw: function (pen, t, ctx2) {
        for (var i = 0; i < n; i++) {
          var x = -span / 2 + span * (i + 0.5) / n;
          var ang = Math.sin(t * 1.6 + phase[i]) * amp[i];
          var hang = child(f, [x, 0, 0], ang, 0, 0);
          pen.part(hang, 'box', [-1.4, -4.5, 0], [0.15, 9, 0.15], '#8a8f94', { m: 'metal' });
          pen.part(hang, 'box', [1.4, -4.5, 0], [0.15, 9, 0.15], '#8a8f94', { m: 'metal' });
          pen.part(hang, 'box', [0, -9.1, 0], [3.4, 0.3, 1.4], '#1b1d20');
          if (i === Math.floor(n / 2) && amp[i] > 0.5 && Math.abs(Math.cos(t * 1.6 + phase[i])) > 0.98 &&
              t - lastCreak > 0.8) {
            lastCreak = t;
            if (ctx2.sound) ctx2.sound('ll_creak', spec.p, 0.5);
          }
        }
      }
    };
  });

  /* The merry-go-round's rails, turning slowly with nobody on it. */
  Rigs.register('merry_go_round', function (spec) {
    var f0 = frame(spec.p, 0);
    var turn = 0, last = 0, speed = 0.25;
    return {
      radius: 12,
      event: function (kind) { if (kind === 'lure' || kind === 'roar') speed = 1.6; },
      draw: function (pen, t) {
        var dt = last ? Math.min(0.1, t - last) : 0;
        last = t;
        speed = approach(speed, 0.25, 0.2, dt);
        turn += speed * dt;
        var f = child(f0, [0, 0, 0], 0, turn, 0);
        var r = spec.r || 6;
        pen.part(f, 'cyl', [0, 3.0, 0], [0.5, 6.0, 0.5], '#8a8f94', { m: 'metal' });
        for (var i = 0; i < 6; i++) {
          var a = i / 6 * TAU;
          var arm = child(f, [0, 0, 0], 0, a, 0);
          pen.part(arm, 'box', [0, 2.6, r * 0.5], [0.3, 0.3, r], i % 2 ? '#e83a3a' : '#3a7ac8', { m: 'metal' });
          pen.part(arm, 'box', [0, 1.3, r - 0.3], [0.3, 2.6, 0.3], i % 2 ? '#e83a3a' : '#3a7ac8', { m: 'metal' });
        }
      }
    };
  });

  /* The marquee's bulbs chasing round the board, both faces, and the star
     on top turning and twinkling. */
  Rigs.register('marquee_lights', function (spec) {
    var f = frame(spec.p, spec.yaw || 0);
    var w = spec.w || 30, h = spec.h || 12, d = spec.d || 3;
    var bulbs = [];
    var per = 2 * (w + h), n = 40;
    for (var i = 0; i < n; i++) {
      var u = i / n * per, x, y;
      if (u < w) { x = -w / 2 + u; y = h / 2; }
      else if (u < w + h) { x = w / 2; y = h / 2 - (u - w); }
      else if (u < 2 * w + h) { x = w / 2 - (u - w - h); y = -h / 2; }
      else { x = -w / 2; y = -h / 2 + (u - 2 * w - h); }
      bulbs.push([x, y]);
    }
    var star = spec.star_p ? frame(spec.star_p, 0) : null;
    return {
      radius: w,
      draw: function (pen, t) {
        var chase = Math.floor(t * 10);
        for (var i = 0; i < bulbs.length; i++) {
          var on = (i + chase) % 4 !== 0 && i !== 13;
          var c = on ? '#fff2a8' : '#5a4a2a';
          pen.part(f, 'sph', [bulbs[i][0], bulbs[i][1], d / 2 + 0.3], [0.7, 0.7, 0.7], c, { m: on ? 'neon' : '' });
          pen.part(f, 'sph', [bulbs[i][0], bulbs[i][1], -d / 2 - 0.3], [0.7, 0.7, 0.7], c, { m: on ? 'neon' : '' });
        }
        if (star) {
          var s = child(star, [0, 0, 0], 0, t * 0.8, 0);
          var tw = 0.75 + 0.25 * Math.sin(t * 6);
          pen.part(s, 'box', [0, 0, 0], [7 * tw, 1.4, 0.8], '#ffd84a', { m: 'neon' });
          pen.part(s, 'box', [0, 0, 0], [1.4, 7 * tw, 0.8], '#ffd84a', { m: 'neon' });
          pen.part(s, 'box', [0, 0, 0], [4.6 * tw, 1.2, 0.7], '#fff6c0', { m: 'neon', rz: Math.PI / 4 });
          pen.part(s, 'box', [0, 0, 0], [4.6 * tw, 1.2, 0.7], '#fff6c0', { m: 'neon', rz: -Math.PI / 4 });
          pen.part(star, 'box', [0, -4.0, 0], [0.5, 4.0, 0.5], '#2a3a4a', { m: 'metal' });
        }
      }
    };
  });

  /* The putt-putt windmill's sails. */
  Rigs.register('golf_windmill', function (spec) {
    var f = frame(spec.p, spec.yaw || 0);
    var r = spec.r || 8;
    return {
      radius: r * 1.4,
      draw: function (pen, t) {
        var hub = child(f, [0, 0, -0.6], 0, 0, t * 0.9);
        pen.part(f, 'cyl', [0, 0, -0.4], [1.2, 0.8, 1.2], '#3a2a1a', { rx: Math.PI / 2 });
        for (var i = 0; i < 4; i++) {
          var arm = child(hub, [0, 0, 0], 0, 0, i * Math.PI / 2);
          pen.part(arm, 'box', [0, r / 2, 0], [0.4, r, 0.3], '#5a3a22');
          pen.part(arm, 'box', [0.9, r * 0.58, 0], [1.6, r * 0.8, 0.12], '#f2e6c8');
        }
      }
    };
  });

  /* The scrap crane's boom, slewing slowly round, and its magnet swinging
     on the cable. */
  Rigs.register('scrap_magnet', function (spec) {
    var f0 = frame(spec.p, 0);
    var arm = spec.arm || 14;
    return {
      radius: arm + 8,
      draw: function (pen, t) {
        var slew = Math.sin(t * 0.08) * 1.4;
        var f = child(f0, [0, 0, 0], 0, slew, 0);
        pen.part(f, 'box', [0, 0.6, arm / 2 - 2], [1.6, 1.4, arm + 4], '#e8b81a', { m: 'metal' });
        var tip = Rigs.point(f, [0, 0, arm]);
        var sway = Math.sin(t * 1.1) * 0.12, sway2 = Math.cos(t * 0.8) * 0.08;
        var drop = 12;
        var low = [tip[0] + Math.sin(sway) * drop, tip[1] - drop, tip[2] + Math.sin(sway2) * drop];
        pen.rod(tip, low, 0.16, '#2a2d31');
        pen.part(frame(low, slew), 'cyl', [0, -0.6, 0], [4.4, 1.2, 4.4], '#3a3f46', { m: 'metal' });
      }
    };
  });

  /* Crows on the scarecrow's arms: they scatter at a shot or when the
     infected come near, wheel about cawing, and settle back. */
  Rigs.register('crows', function (spec, ctx) {
    var n = spec.n || 5;
    var birds = [];
    for (var i = 0; i < n; i++) {
      var perch = [spec.p[0] + (i - (n - 1) / 2) * 1.7, spec.p[1] - 3.6 + (i % 2) * 0.2, spec.p[2]];
      birds.push({ perch: perch, pos: perch.slice(), yaw: hash(i) * TAU, up: 0, seed: i });
    }
    var scare = -10;
    return {
      radius: 60,
      event: function (kind, msg) {
        if (kind === 'shot' || kind === 'blast' || kind === 'lure' || kind === 'roar') {
          var from = msg && (msg.from || msg.p);
          if (!from || Math.hypot(from[0] - spec.p[0], from[2] - spec.p[2]) < 120) scare = Rigs.clock();
        }
      },
      update: function (dt, t, ctx2) {
        var near = nearest(ctx2.zombies ? ctx2.zombies() : [], spec.p, 16);
        if (near && t - scare > 6) scare = t;
        var flying = t - scare < 8;
        if (flying && t - scare < 0.05 && ctx2.sound) ctx2.sound('ll_caw', spec.p, 0.7);
        for (var i = 0; i < birds.length; i++) {
          var b = birds[i];
          var target;
          if (flying) {
            var a = t * 0.9 + b.seed * 1.3;
            target = [spec.p[0] + Math.cos(a) * (14 + b.seed * 2), spec.p[1] + 14 + Math.sin(t * 1.3 + b.seed) * 4,
                      spec.p[2] + Math.sin(a) * (14 + b.seed * 2)];
          } else {
            target = b.perch;
          }
          var k = 1 - Math.exp(-dt * (flying ? 2.4 : 1.6));
          var nx = b.pos[0] + (target[0] - b.pos[0]) * k, nz = b.pos[2] + (target[2] - b.pos[2]) * k;
          if (Math.hypot(nx - b.pos[0], nz - b.pos[2]) > 0.01) b.yaw = Math.atan2(nx - b.pos[0], nz - b.pos[2]);
          b.pos = [nx, b.pos[1] + (target[1] - b.pos[1]) * k, nz];
          b.up = flying || Math.hypot(target[0] - b.pos[0], target[2] - b.pos[2]) > 0.5 ? 1 : 0;
        }
      },
      draw: function (pen, t) {
        for (var i = 0; i < birds.length; i++) {
          var b = birds[i];
          var f = frame(b.pos, b.yaw);
          pen.part(f, 'box', [0, 0.5, 0], [0.7, 0.7, 1.4], '#141418');
          pen.part(f, 'box', [0, 0.9, 0.7], [0.5, 0.5, 0.5], '#141418');
          pen.part(f, 'box', [0, 0.85, 1.05], [0.15, 0.15, 0.35], '#3a3020');
          var flap = b.up ? Math.sin(t * 16 + i) * 0.9 : 0.15;
          pen.part(child(f, [0.35, 0.6, 0], 0, 0, -flap), 'box', [0.8, 0, 0], [1.6, 0.08, 0.8], '#141418');
          pen.part(child(f, [-0.35, 0.6, 0], 0, 0, flap), 'box', [-0.8, 0, 0], [1.6, 0.08, 0.8], '#141418');
        }
      }
    };
  });

  /* An old car in the front row with its battery not quite dead: the
     headlights stutter, and when one of the infected shambles past it the
     horn goes and the lights come up full. */
  Rigs.register('jalopy', function (spec) {
    var f = frame(spec.p, spec.yaw || 0);
    var alarm = -10, lastHonk = -10;
    return {
      radius: 60,
      update: function (dt, t, ctx) {
        var near = nearest(ctx.zombies ? ctx.zombies() : [], spec.p, 12);
        if (near && t - lastHonk > 6) {
          lastHonk = t;
          alarm = t + 3;
          if (ctx.sound) ctx.sound('ll_honk', spec.p, 0.9);
        }
      },
      draw: function (pen, t) {
        var lit = t < alarm ? (Math.sin(t * 14) > 0 ? 1 : 0.25) :
          (hash(Math.floor(t * 6)) > 0.25 ? 0.55 : 0.1);
        for (var side = -1; side <= 1; side += 2) {
          pen.part(f, 'box', [side * 1.6, 2.4, 5.06], [1.0, 0.7, 0.1], '#fff6c0', { m: 'neon', a: 0.4 + 0.6 * lit });
          pen.part(f, 'cone', [side * 1.6, 2.2, 5.1 + 13], [6 * lit + 1, 26, 3.5 * lit + 1], '#fff6c0',
                   { m: 'neon', a: 0.1 * lit, rx: -Math.PI / 2 });
        }
      }
    };
  });

  /* Moths round a lamp: pale flecks in a loose ball, darting. */
  Rigs.register('moth_swarm', function (spec) {
    var n = 14, seeds = [];
    for (var i = 0; i < n; i++) seeds.push([hash(i) * TAU, 0.6 + hash(i + 20), hash(i + 40) * 6]);
    return {
      radius: 8,
      draw: function (pen, t) {
        if (!pen.near) return;
        for (var i = 0; i < n; i++) {
          var s = seeds[i];
          var a = t * (2.4 + s[1]) + s[0];
          var p = [spec.p[0] + Math.cos(a) * (1.4 + s[1]) + wander(t * 2, i) * 0.6,
                   spec.p[1] - 1.2 + Math.sin(t * 3.1 + s[2]) * 1.2,
                   spec.p[2] + Math.sin(a * 1.3) * (1.4 + s[1])];
          var fl = frame(p, a);
          var flap = Math.sin(t * 30 + i) * 0.8;
          pen.part(child(fl, [0.18, 0, 0], 0, 0, -flap), 'box', [0.18, 0, 0], [0.36, 0.04, 0.3], '#e8e0c8');
          pen.part(child(fl, [-0.18, 0, 0], 0, 0, flap), 'box', [-0.18, 0, 0], [0.36, 0.04, 0.3], '#e8e0c8');
        }
      }
    };
  });

  // ============================================== Harrow County Zoo
  if (GA) {
    GA.register('ll_showtime', function (vol) {
      // the sea lion show's jingle over the tannoy: a bright calliope run,
      // a whistle, a cheer
      [523, 659, 784, 1047, 784, 659, 784, 1047, 1319].forEach(function (f, i) {
        this.later(i * 130, function () {
          this.tone({ type: 'square', freq: f, dur: 0.16, gain: 0.05 * vol });
          this.tone({ type: 'sine', freq: f * 2, dur: 0.12, gain: 0.03 * vol });
        });
      }, this);
      this.later(1250, function () { this.tone({ type: 'sine', freq: 2200, freqEnd: 2600, dur: 0.5, gain: 0.07 * vol }); });
      this.later(1500, function () { this.noise({ filter: 'bandpass', freq: 1200, dur: 1.4, gain: 0.08 * vol }); });
    });
    GA.register('ll_trumpet', function (vol) {
      this.tone({ type: 'sawtooth', freq: 330, freqEnd: 520, dur: 0.5, gain: 0.12 * vol });
      this.later(380, function () { this.tone({ type: 'sawtooth', freq: 520, freqEnd: 300, dur: 0.9, gain: 0.12 * vol }); });
      this.noise({ filter: 'bandpass', freq: 700, dur: 1.2, gain: 0.05 * vol });
    });
    GA.register('ll_lion', function (vol) {
      this.tone({ type: 'sawtooth', freq: 120, freqEnd: 70, dur: 1.4, gain: 0.2 * vol });
      this.noise({ freq: 400, freqEnd: 90, dur: 1.5, gain: 0.16 * vol });
    });
    GA.register('ll_bark', function (vol) {
      for (var i = 0; i < 3; i++) {
        this.later(i * 240, function () {
          this.tone({ type: 'square', freq: 300, freqEnd: 180, dur: 0.16, gain: 0.08 * vol });
          this.noise({ filter: 'bandpass', freq: 900, dur: 0.12, gain: 0.05 * vol });
        });
      }
    });
    GA.register('ll_chestbeat', function (vol) {
      for (var i = 0; i < 6; i++) {
        this.later(i * 110, function () { this.tone({ type: 'sine', freq: 90, freqEnd: 60, dur: 0.12, gain: 0.2 * vol }); });
      }
      this.later(700, function () { this.noise({ freq: 300, freqEnd: 120, dur: 0.6, gain: 0.08 * vol }); });
    });
    GA.register('ll_squawk', function (vol) {
      this.tone({ type: 'sawtooth', freq: 1400, freqEnd: 900, dur: 0.2, gain: 0.05 * vol });
      this.later(160, function () { this.tone({ type: 'sawtooth', freq: 1200, freqEnd: 1600, dur: 0.18, gain: 0.04 * vol }); });
    });
  }

  /* A walk that wanders round a rectangle and stops now and then: the
     position along a slow Lissajous whose speed falls to nothing once a
     cycle (s' = v (1 - cos wt)), the same on every screen. */
  function amble(area, t, seed, v) {
    var w = 0.21 + hash(seed) * 0.1;
    var s = t * v - (v / w) * Math.sin(w * t + seed);
    var cx = (area[0] + area[1]) / 2, cz = (area[2] + area[3]) / 2;
    var rx = (area[1] - area[0]) / 2 * 0.86, rz = (area[3] - area[2]) / 2 * 0.86;
    var a = s * 0.05 + seed * 2.1;
    return [cx + rx * Math.sin(a + seed), cz + rz * Math.sin(a * 1.37 + seed * 3.3),
            v * (1 - Math.cos(w * t + seed))];
  }

  /* An animal that ambles: its position, heading and how fast it is
     going, worked out per frame. */
  function walker(area, seed, v) {
    var st = { x: 0, z: 0, yaw: 0, speed: 0, ok: false };
    return {
      st: st,
      step: function (t) {
        var a = amble(area, t, seed, v), b = amble(area, t + 0.2, seed, v);
        st.x = a[0]; st.z = a[1]; st.speed = a[2];
        if (Math.hypot(b[0] - a[0], b[1] - a[1]) > 0.004) {
          var target = Math.atan2(b[0] - a[0], b[1] - a[1]);
          st.yaw = st.ok ? approachAngle(st.yaw, target, 3, 0.05) : target;
        }
        st.ok = true;
        return st;
      }
    };
  }

  /* Four legs swinging in pairs with a stride ``phase``; ``legs`` is
     [[x, z], ...] hips in the body frame, ``h`` the leg length. */
  function legsAt(pen, f, legs, h, w, colour, phase, amp) {
    for (var i = 0; i < legs.length; i++) {
      var swing = Math.sin(phase + (i === 0 || i === 3 ? 0 : Math.PI)) * amp;
      var hip = child(f, [legs[i][0], h, legs[i][1]], swing, 0, 0);
      pen.part(hip, 'box', [0, -h / 2, 0], [w, h, w], colour);
    }
  }

  Rigs.register('giraffe', function (spec) {
    var sc = spec.scale || 1;
    var walk = walker(spec.area, spec.seed || 1, 1.6);
    var neckYaw = 0, look = 0;
    return {
      radius: 30,
      update: function (dt, t, ctx) {
        var st = walk.step(t);
        this.at = [st.x, spec.p[1], st.z];
        var near = nearest(ctx.players ? ctx.players() : [], this.at, 60);
        var target = 0;
        if (near && st.speed < 0.6) target = Math.atan2(near.who.pos[0] - st.x, near.who.pos[2] - st.z) - st.yaw;
        while (target > Math.PI) target -= TAU;
        while (target < -Math.PI) target += TAU;
        neckYaw = approach(neckYaw, clamp(target, -1.1, 1.1), 1.5, dt);
        look = approach(look, near ? 1 : 0, 1, dt);
      },
      draw: function (pen, t) {
        var st = walk.st;
        var f = frame([st.x, spec.p[1], st.z], st.yaw, sc);
        var phase = t * 3.2 * Math.min(1, st.speed + 0.05);
        var amp = Math.min(0.45, st.speed * 0.4);
        var hide = '#e8b858', spot = '#8a5a2a';
        legsAt(pen, f, [[-1.0, 2.0], [1.0, 2.0], [-1.0, -2.0], [1.0, -2.0]], 7.2, 0.6, hide, phase, amp);
        var body = child(f, [0, 8.4, 0], Math.sin(phase * 2) * 0.02, 0, 0);
        pen.part(body, 'box', [0, 0, 0], [2.8, 2.8, 5.8], hide);
        [[0.8, 0.6, 1.4], [-0.7, 0.4, -0.6], [0.2, 1.0, -1.8], [-0.9, -0.3, 1.9], [1.0, -0.6, -1.2]]
          .forEach(function (p) {
            pen.part(body, 'box', [p[0] > 0 ? 1.42 : -1.42, p[1], p[2]], [0.06, 0.8, 1.0], spot);
          });
        pen.part(body, 'box', [0, 1.44, 0.6], [1.0, 0.06, 0.8], spot);
        // the tail and its tuft
        var tail = child(body, [0, 0.9, -2.9], 0.5 + Math.sin(t * 2.4) * 0.3, 0, Math.sin(t * 1.7) * 0.3);
        pen.part(tail, 'box', [0, -1.4, 0], [0.2, 2.8, 0.2], hide);
        pen.part(tail, 'box', [0, -2.9, 0], [0.4, 0.7, 0.4], '#2a1a0a');
        // the neck, turned to whoever it is watching, swaying
        var sway = Math.sin(t * 0.8 + (spec.seed || 0)) * 0.08;
        var neck = child(body, [0, 1.0, 2.4], -0.42 + look * 0.12 + sway, neckYaw * 0.6, 0);
        pen.part(neck, 'box', [0, 3.6, 0], [1.0, 7.4, 1.2], hide);
        pen.part(neck, 'box', [0, 3.6, -0.64], [0.4, 6.6, 0.1], '#8a5a2a');
        var head = child(neck, [0, 7.2, 0], 0.5 - look * 0.2 + Math.sin(t * 1.3) * 0.05, neckYaw * 0.4, 0);
        pen.part(head, 'box', [0, 0, 0.6], [1.1, 1.1, 2.4], hide);
        pen.part(head, 'box', [0, -0.15, 1.9], [0.9, 0.8, 0.5], '#c89848');
        for (var side = -1; side <= 1; side += 2) {
          pen.part(head, 'box', [side * 0.3, 0.9, 0.2], [0.2, 0.8, 0.2], '#8a5a2a');
          pen.part(head, 'box', [side * 0.3, 1.35, 0.2], [0.34, 0.3, 0.34], '#2a1a0a');
          pen.part(head, 'box', [side * 0.62, 0.4, -0.2], [0.5, 0.2, 0.6], hide, { rz: side * 0.4 });
          pen.part(head, 'box', [side * 0.56, 0.2, 0.9], [0.06, 0.24, 0.24], '#141414');
        }
      }
    };
  });

  Rigs.register('elephant', function (spec) {
    var sc = spec.scale || 1;
    var walk = walker(spec.area, spec.seed || 1, 1.1);
    var trumpet = -10, trunkUp = 0;
    return {
      radius: 30,
      event: function (kind) {
        if (kind === 'roar' || kind === 'lure' || (kind === 'wave' && Math.random() < 0.5)) trumpet = Rigs.clock();
      },
      update: function (dt, t, ctx) {
        var st = walk.step(t);
        this.at = [st.x, spec.p[1], st.z];
        var up = t - trumpet < 2.4;
        if (up && t - trumpet < dt * 1.5 && ctx.sound) ctx.sound('ll_trumpet', this.at, 1);
        trunkUp = approach(trunkUp, up ? 1 : 0, 4, dt);
      },
      draw: function (pen, t) {
        var st = walk.st;
        var f = frame([st.x, spec.p[1], st.z], st.yaw, sc);
        var grey = '#8a8f94';
        var phase = t * 2.4 * Math.min(1, st.speed + 0.05);
        legsAt(pen, f, [[-1.6, 2.4], [1.6, 2.4], [-1.6, -2.4], [1.6, -2.4]], 4.6, 1.8, grey, phase,
               Math.min(0.3, st.speed * 0.3));
        var body = child(f, [0, 7.0, 0], 0, 0, Math.sin(phase) * 0.02);
        pen.part(body, 'box', [0, 0, 0], [5.2, 5.0, 8.0], grey);
        pen.part(body, 'box', [0, 2.6, -0.4], [4.4, 0.4, 6.6], '#7a7f84');
        var tail = child(body, [0, 1.4, -4.0], 0.2, 0, Math.sin(t * 2) * 0.3);
        pen.part(tail, 'box', [0, -1.4, 0], [0.24, 2.8, 0.24], grey);
        var head = child(body, [0, 0.8, 4.4], 0.1 - trunkUp * 0.3, Math.sin(t * 0.5) * 0.15, 0);
        pen.part(head, 'box', [0, 0, 0], [3.4, 3.4, 2.4], grey);
        for (var side = -1; side <= 1; side += 2) {
          var ear = child(head, [side * 1.7, 0.4, -0.4], 0, side * (0.5 + Math.sin(t * 2.2) * 0.25), 0);
          pen.part(ear, 'box', [side * 1.2, 0, 0], [2.4, 3.0, 0.3], '#9a9fa4');
          pen.part(head, 'box', [side * 1.0, 0.5, 1.22], [0.3, 0.3, 0.1], '#141414');
          pen.part(head, 'box', [side * 0.9, -1.3, 1.6], [0.3, 0.3, 1.6], '#f2ece0', { rx: -0.4 });
        }
        // the trunk: four segments, curling, raised to trumpet
        var seg = child(head, [0, -0.8, 1.4], 0.3 - trunkUp * 2.2, 0, 0);
        for (var k = 0; k < 4; k++) {
          var w = 1.0 - k * 0.15;
          pen.part(seg, 'box', [0, -0.75, 0], [w, 1.5, w], grey);
          seg = child(seg, [0, -1.5, 0], 0.18 + Math.sin(t * 1.4 + k) * 0.12 - trunkUp * 0.35, 0, 0);
        }
      }
    };
  });

  Rigs.register('big_cat', function (spec) {
    var r = spec.r || 10, seed = spec.seed || 1;
    var roarAt = -10, ang = hash(seed) * TAU, dir = 1, pause = 0, last = 0;
    var st = { x: spec.p[0], z: spec.p[2], yaw: 0, moving: 0, look: 0 };
    return {
      radius: r + 20,
      event: function (kind) { if (kind === 'roar' || kind === 'wave') roarAt = Rigs.clock() + hash(seed + 5) * 0.8; },
      update: function (dt, t, ctx) {
        var u = Math.floor(t / 7 + seed);
        var walking = hash(u * 3 + seed) > 0.35;
        dir = hash(u * 7 + seed) > 0.5 ? 1 : -1;
        if (walking) ang += dir * dt * (2.2 / r);
        st.moving = approach(st.moving, walking ? 1 : 0, 3, dt);
        st.x = spec.p[0] + Math.cos(ang) * r;
        st.z = spec.p[2] + Math.sin(ang) * r;
        var tangent = Math.atan2(-Math.sin(ang) * dir, Math.cos(ang) * dir);
        st.yaw = approachAngle(st.yaw, tangent, 4, dt);
        this.at = [st.x, spec.p[1], st.z];
        var near = nearest(ctx.players ? ctx.players() : [], this.at, 70);
        st.target = near ? Math.atan2(near.who.pos[0] - st.x, near.who.pos[2] - st.z) : null;
        if (t - roarAt > 0 && t - roarAt < dt * 1.5 && ctx.sound) ctx.sound('ll_lion', this.at, 1);
      },
      draw: function (pen, t) {
        var f = frame([st.x, spec.p[1], st.z], st.yaw, 1);
        var coat = spec.mane ? '#c8963a' : '#d8a858';
        var phase = t * 6 * st.moving;
        legsAt(pen, f, [[-0.7, 1.5], [0.7, 1.5], [-0.7, -1.5], [0.7, -1.5]], 1.8, 0.6, coat, phase, 0.4 * st.moving);
        var body = child(f, [0, 2.4, 0], 0, 0, 0);
        pen.part(body, 'box', [0, 0, 0], [1.7, 1.5, 4.4], coat);
        var tail = child(body, [0, 0.3, -2.2], 0.9 + Math.sin(t * 2.6) * 0.3, 0, Math.sin(t * 1.9) * 0.5);
        pen.part(tail, 'box', [0, -1.2, 0], [0.18, 2.4, 0.18], coat);
        pen.part(tail, 'box', [0, -2.5, 0], [0.4, 0.5, 0.4], '#5a3a1a');
        var roaring = t - roarAt > 0 && t - roarAt < 2.0;
        var turn = 0;
        if (st.target !== null && st.target !== undefined && st.moving < 0.5) {
          turn = st.target - st.yaw;
          while (turn > Math.PI) turn -= TAU;
          while (turn < -Math.PI) turn += TAU;
          turn = clamp(turn, -1.0, 1.0);
        }
        var head = child(body, [0, 0.7, 2.3], roaring ? -0.4 : 0.05, turn, 0);
        if (spec.mane) pen.part(head, 'box', [0, 0.1, -0.3], [2.6, 2.6, 1.4], '#7a4a1a');
        pen.part(head, 'box', [0, 0, 0.5], [1.4, 1.3, 1.6], coat);
        pen.part(head, 'box', [0, -0.3, 1.35], [0.8, 0.6, 0.4], '#e8c888');
        pen.part(head, 'box', [0, -0.75 - (roaring ? 0.3 : 0), 1.1], [0.9, 0.3, 1.0], coat);
        for (var side = -1; side <= 1; side += 2) {
          pen.part(head, 'box', [side * 0.35, 0.25, 1.31], [0.24, 0.16, 0.1], '#2a1a0a');
          pen.part(head, 'box', [side * 0.6, 0.8, 0.0], [0.4, 0.4, 0.2], coat);
        }
      }
    };
  });

  Rigs.register('flamingos', function (spec) {
    var area = spec.area, n = spec.n || 8;
    var birds = [];
    for (var i = 0; i < n; i++) {
      birds.push({ x: area[0] + (area[1] - area[0]) * hash(i * 3 + 1), z: area[2] + (area[3] - area[2]) * hash(i * 5 + 2),
                   yaw: hash(i) * TAU, run: 0, tx: 0, tz: 0, seed: i });
    }
    return {
      radius: 40,
      update: function (dt, t, ctx) {
        var zs = ctx.zombies ? ctx.zombies() : [];
        for (var i = 0; i < birds.length; i++) {
          var b = birds[i];
          var near = nearest(zs, [b.x, 0, b.z], 18);
          var tx, tz;
          if (near) {
            // away from it, to the far end of the pond
            tx = near.who.pos[0] < (area[0] + area[1]) / 2 ? area[1] - 2 : area[0] + 2;
            tz = b.z;
          } else {
            var a = t * 0.05 + b.seed;
            tx = area[0] + (area[1] - area[0]) * (0.5 + 0.42 * Math.sin(a + b.seed));
            tz = area[2] + (area[3] - area[2]) * (0.5 + 0.4 * Math.sin(a * 1.3 + b.seed * 2));
          }
          var dx = tx - b.x, dz = tz - b.z, d = Math.hypot(dx, dz);
          var speed = near ? 14 : 0.8;
          b.run = approach(b.run, near ? 1 : 0, 3, dt);
          if (d > 0.3) {
            var step = Math.min(d, speed * dt);
            b.x += dx / d * step; b.z += dz / d * step;
            b.yaw = approachAngle(b.yaw, Math.atan2(dx, dz), 4, dt);
          }
        }
      },
      draw: function (pen, t) {
        var pink = '#f28aa0';
        for (var i = 0; i < birds.length; i++) {
          var b = birds[i];
          var f = frame([b.x, spec.p[1], b.z], b.yaw, 1);
          var oneLeg = b.run < 0.2 && hash(i + Math.floor(t / 9)) > 0.4;
          var phase = t * 10;
          pen.part(f, 'box', [0.2, 1.7, 0], [0.16, 3.4, 0.16], '#e86a80');
          if (!oneLeg) pen.part(child(f, [-0.2, 3.4, 0], Math.sin(phase) * 0.5 * b.run, 0, 0), 'box', [0, -1.7, 0], [0.16, 3.4, 0.16], '#e86a80');
          else pen.part(child(f, [-0.2, 3.4, 0], 1.2, 0, 0), 'box', [0, -0.9, 0], [0.16, 1.8, 0.16], '#e86a80');
          var body = child(f, [0, 4.0, 0], 0, 0, 0);
          pen.part(body, 'box', [0, 0, 0], [1.2, 1.2, 2.2], pink);
          var flap = b.run > 0.3 ? Math.sin(t * 18 + i) * 0.9 : 0.05;
          pen.part(child(body, [0.6, 0.3, 0], 0, 0, -flap), 'box', [0.8, 0, 0], [1.6, 0.1, 1.6], '#e86a80');
          pen.part(child(body, [-0.6, 0.3, 0], 0, 0, flap), 'box', [-0.8, 0, 0], [1.6, 0.1, 1.6], '#e86a80');
          var tucked = !b.run && hash(i * 7 + Math.floor(t / 11)) > 0.6;
          var neck = child(body, [0, 0.4, 0.9], tucked ? 1.6 : -0.2, 0, 0);
          pen.part(neck, 'box', [0, 1.2, 0], [0.3, 2.4, 0.3], pink);
          var head = child(neck, [0, 2.4, 0], tucked ? 1.2 : 1.4, 0, 0);
          pen.part(head, 'box', [0, 0, 0.3], [0.5, 0.5, 0.8], pink);
          pen.part(head, 'box', [0, -0.2, 0.9], [0.24, 0.3, 0.6], '#1a1a1a', { rx: 0.5 });
        }
      }
    };
  });

  Rigs.register('penguins', function (spec) {
    var pool = spec.pool, rocks = spec.rocks || [spec.p];
    var n = spec.n || 6;
    var cycle = 22;
    function pos(i, t) {
      // on rock A, waddling -- into the water -- a lap past the window --
      // out onto rock B, which is the next cycle's A
      var k = Math.floor((t + i * 5.3) / cycle), u = ((t + i * 5.3) % cycle) / cycle;
      var a = rocks[(k + i) % rocks.length], b = rocks[(k + i + 1) % rocks.length];
      var cx = (pool[0] + pool[1]) / 2, cz = (pool[2] + pool[3]) / 2;
      var rx = (pool[1] - pool[0]) / 2 - 3, rz = (pool[3] - pool[2]) / 2 - 3;
      if (u < 0.35) {
        return { p: [a[0] + Math.sin(t * 0.7 + i) * 0.8, a[1], a[2] + Math.cos(t * 0.6 + i) * 0.8], mode: 0,
                 yaw: Math.sin(t * 0.3 + i) * 2 };
      }
      if (u < 0.42) {
        var v = (u - 0.35) / 0.07;
        var entry = [cx + (a[0] - cx) * 0.6, -1.6, cz + (a[2] - cz) * 0.6];
        return { p: [a[0] + (entry[0] - a[0]) * v, a[1] + (entry[1] - a[1]) * v + Math.sin(v * Math.PI) * 3,
                     a[2] + (entry[2] - a[2]) * v], mode: 1, yaw: Math.atan2(entry[0] - a[0], entry[2] - a[2]) };
      }
      if (u < 0.9) {
        var w = (u - 0.42) / 0.48 * TAU * 1.2 + i;
        var depth = -3.8 + Math.sin(w * 2) * 1.2;
        return { p: [cx + Math.cos(w) * rx, depth, cz + Math.sin(w) * rz], mode: 2,
                 yaw: Math.atan2(-Math.sin(w), Math.cos(w)) };
      }
      var q = (u - 0.9) / 0.1;
      var from = [cx + (b[0] - cx) * 0.6, -1.4, cz + (b[2] - cz) * 0.6];
      return { p: [from[0] + (b[0] - from[0]) * q, from[1] + (b[1] - from[1]) * q + Math.sin(q * Math.PI) * 3,
                   from[2] + (b[2] - from[2]) * q], mode: 1, yaw: Math.atan2(b[0] - from[0], b[2] - from[2]) };
    }
    return {
      radius: 60,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var s = pos(i, t);
          var swim = s.mode === 2;
          var f = frame(s.p, s.yaw, 1);
          var body = child(f, [0, swim ? 0 : 1.2, 0], swim ? Math.PI / 2 : (s.mode === 1 ? 0.8 : Math.sin(t * 6 + i) * 0.08),
                           0, swim ? 0 : Math.sin(t * 6 + i) * 0.12);
          pen.part(body, 'box', [0, 0, 0], [1.1, 2.0, 0.9], '#1a1d24');
          pen.part(body, 'box', [0, -0.1, 0.46], [0.8, 1.5, 0.06], '#f2f2ec');
          pen.part(body, 'box', [0, 1.3, 0.05], [0.8, 0.7, 0.7], '#1a1d24');
          pen.part(body, 'box', [0, 1.25, 0.5], [0.24, 0.16, 0.4], '#e8a03a');
          pen.part(body, 'box', [0.26, 1.45, 0.41], [0.1, 0.1, 0.06], '#f2f2ec');
          pen.part(body, 'box', [-0.26, 1.45, 0.41], [0.1, 0.1, 0.06], '#f2f2ec');
          var flap = swim ? Math.sin(t * 10 + i) * 0.6 : 0.25 + Math.sin(t * 4 + i) * 0.1;
          pen.part(child(body, [0.6, 0.4, 0], 0, 0, -flap), 'box', [0.1, -0.6, 0], [0.16, 1.2, 0.5], '#1a1d24');
          pen.part(child(body, [-0.6, 0.4, 0], 0, 0, flap), 'box', [-0.1, -0.6, 0], [0.16, 1.2, 0.5], '#1a1d24');
          if (!swim) {
            pen.part(body, 'box', [0.3, -1.1, 0.2], [0.34, 0.2, 0.5], '#e8a03a');
            pen.part(body, 'box', [-0.3, -1.1, 0.2], [0.34, 0.2, 0.5], '#e8a03a');
          }
        }
      }
    };
  });

  Rigs.register('sea_lion', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    var show = -10, lastBark = -10;
    return {
      radius: 30,
      event: function (kind) { if (kind === 'lure') show = Rigs.clock() + 16; },
      update: function (dt, t, ctx) {
        if (t < show && t - lastBark > 3.0) {
          lastBark = t;
          if (ctx.sound) ctx.sound('ll_bark', spec.p, 1);
        }
      },
      draw: function (pen, t) {
        var on = t < show;
        var clap = on ? Math.abs(Math.sin(t * 8)) : 0;
        var bob = Math.sin(t * 1.2) * 0.1;
        var body = child(f0, [0, 1.4 + bob, 0], -0.5 - clap * 0.2, Math.sin(t * 0.4) * 0.3, 0);
        pen.part(body, 'box', [0, 0, 0], [2.0, 3.2, 1.8], '#4a3a2e');
        pen.part(body, 'box', [0, -1.6, -1.2], [1.6, 1.2, 2.4], '#4a3a2e');
        var head = child(body, [0, 2.0, 0.2], 0.6 + clap * 0.3, 0, 0);
        pen.part(head, 'box', [0, 0.2, 0.2], [1.2, 1.1, 1.4], '#5a4a3a');
        pen.part(head, 'box', [0, 0.0, 1.0], [0.6, 0.5, 0.5], '#3a2a1e');
        pen.part(head, 'box', [0.36, 0.5, 0.86], [0.14, 0.14, 0.06], '#0a0a0a');
        pen.part(head, 'box', [-0.36, 0.5, 0.86], [0.14, 0.14, 0.06], '#0a0a0a');
        for (var side = -1; side <= 1; side += 2) {
          var fl = child(body, [side * 1.0, 0.4, 0.4], -0.8 - clap * 0.9, 0, side * (0.6 + clap * 0.5));
          pen.part(fl, 'box', [side * 0.3, -0.7, 0], [0.4, 1.6, 0.9], '#3a2e24');
        }
        // the ball on its nose, bouncing higher for the show
        var hop = on ? Math.abs(Math.sin(t * 4)) * 4 : Math.abs(Math.sin(t * 2)) * 0.4;
        var ball = Rigs.point(head, [0, 1.3 + hop, 1.0]);
        var bf = frame(ball, t * 2);
        pen.part(bf, 'sph', [0, 0, 0], [1.4, 1.4, 1.4], '#e83a3a');
        pen.part(bf, 'box', [0, 0, 0], [1.42, 0.3, 1.42], '#f2f2f2');
        pen.part(bf, 'box', [0, 0, 0], [0.3, 1.42, 1.42], '#3a7ac8');
      }
    };
  });

  Rigs.register('aviary_birds', function (spec) {
    var n = spec.n || 12, r = spec.r || 30;
    var colours = ['#e83a3a', '#3a7ac8', '#f2c83a', '#3ab85a', '#e8783a'];
    var scare = -10;
    return {
      radius: r + 20,
      event: function (kind, msg) {
        var from = msg && (msg.from || msg.p);
        if ((kind === 'shot' || kind === 'blast' || kind === 'roar') &&
            (!from || Math.hypot(from[0] - spec.p[0], from[2] - spec.p[2]) < 90)) {
          if (Rigs.clock() - scare > 4) scare = Rigs.clock();
        }
      },
      update: function (dt, t, ctx) {
        if (t - scare < dt * 1.5 && ctx.sound) ctx.sound('ll_squawk', spec.p, 0.8);
      },
      draw: function (pen, t) {
        var panic = Math.max(0, 1 - (t - scare) / 6);
        for (var i = 0; i < n; i++) {
          var a = t * (0.35 + hash(i) * 0.25 + panic * 0.8) * (i % 2 ? 1 : -1) + i * 1.9;
          var rr = r * (0.35 + hash(i + 9) * 0.6);
          var y = spec.p[1] + Math.sin(t * 0.7 + i) * 4 + hash(i + 3) * 8 + panic * 6;
          var p = [spec.p[0] + Math.cos(a) * rr, y, spec.p[2] + Math.sin(a) * rr];
          var yaw = Math.atan2(-Math.sin(a), Math.cos(a)) * (i % 2 ? 1 : -1) + (i % 2 ? 0 : Math.PI);
          var f = frame(p, yaw, 1);
          var c = colours[i % colours.length];
          pen.part(f, 'box', [0, 0, 0], [0.5, 0.5, 1.2], c);
          pen.part(f, 'box', [0, 0.1, 0.7], [0.36, 0.36, 0.36], c);
          pen.part(f, 'box', [0, 0.0, 0.95], [0.14, 0.2, 0.2], '#2a2a2a');
          pen.part(f, 'box', [0, 0, -0.9], [0.3, 0.1, 0.8], colours[(i + 2) % colours.length]);
          var flap = Math.sin(t * (14 + panic * 10) + i) * 0.9;
          pen.part(child(f, [0.25, 0.1, 0], 0, 0, -flap), 'box', [0.7, 0, 0], [1.4, 0.08, 0.7], c);
          pen.part(child(f, [-0.25, 0.1, 0], 0, 0, flap), 'box', [-0.7, 0, 0], [1.4, 0.08, 0.7], c);
        }
      }
    };
  });

  /* Falling water: streaks running down a sheet, spray at the foot. */
  Rigs.register('waterfall', function (spec) {
    var f = frame(spec.p, spec.yaw || 0);
    var w = spec.w || 10, h = spec.h || 10;
    return {
      radius: Math.max(w, h),
      draw: function (pen, t) {
        pen.part(f, 'box', [0, -h / 2, 0.3], [w, h, 0.2], '#a8d8f0', { a: 0.45, m: 'glass' });
        for (var i = 0; i < 10; i++) {
          var x = -w / 2 + (i + 0.5) * w / 10;
          var u = (t * (1.2 + hash(i) * 0.6) + hash(i + 4)) % 1;
          pen.part(f, 'box', [x, -u * h, 0.45], [0.4, 2.2, 0.1], '#f2faff', { a: 0.7, m: 'neon' });
        }
        if (!pen.near) return;
        for (var k = 0; k < 8; k++) {
          var q = (t * 1.6 + hash(k)) % 1;
          pen.part(f, 'sph', [(hash(k + 7) - 0.5) * w, -h + q * 2.4, 1.0 + q * 2], [0.8 + q, 0.8 + q, 0.8 + q],
                   '#f2faff', { a: 0.5 * (1 - q) });
        }
      }
    };
  });

  /* The crocodile under the footbridge: drifting, eyes and snout above
     the water -- and when somebody is on the bridge over it, it comes up
     out of the water and snaps. */
  Rigs.register('crocodile', function (spec) {
    var area = spec.area;
    var st = { x: spec.p[0], z: spec.p[2], yaw: 0, lunge: 0, snapAt: -10 };
    return {
      radius: 40,
      update: function (dt, t, ctx) {
        var a = t * 0.04;
        var tx = (area[0] + area[1]) / 2 + Math.sin(a * 1.3) * ((area[1] - area[0]) / 2 - 5);
        var tz = (area[2] + area[3]) / 2 + Math.sin(a) * ((area[3] - area[2]) / 2 - 5);
        var near = nearest(ctx.players ? ctx.players() : [], [st.x, 0, st.z], 30);
        if (near && near.who.pos[1] > 0.6 && Math.abs(near.who.pos[0] - (area[0] + area[1]) / 2) < 6) {
          tx = near.who.pos[0] - 4; tz = near.who.pos[2];
          if (near.d < 9 && t - st.snapAt > 3) { st.snapAt = t; if (ctx.sound) ctx.sound('ll_clunk', [st.x, 0, st.z], 1); }
        }
        var dx = tx - st.x, dz = tz - st.z, d = Math.hypot(dx, dz);
        if (d > 0.5) {
          var step = Math.min(d, (near ? 6 : 1.2) * dt);
          st.x += dx / d * step; st.z += dz / d * step;
          st.yaw = approachAngle(st.yaw, Math.atan2(dx, dz), 2, dt);
        }
        st.lunge = approach(st.lunge, t - st.snapAt < 1.2 ? 1 : 0, 6, dt);
        this.at = [st.x, spec.p[1], st.z];
      },
      draw: function (pen, t) {
        var f = frame([st.x, spec.p[1] - 0.6 + st.lunge * 1.6, st.z], st.yaw, 1);
        var green = '#4a5a32';
        var body = child(f, [0, 0, 0], -st.lunge * 0.4, 0, 0);
        pen.part(body, 'box', [0, 0, 0], [2.4, 1.2, 5.0], green);
        for (var k = 0; k < 5; k++) pen.part(body, 'box', [0, 0.7, -2 + k], [0.6, 0.3, 0.5], '#3a4a28');
        var tail = child(body, [0, 0, -2.5], 0, Math.sin(t * 1.6) * 0.4, 0);
        pen.part(tail, 'box', [0, 0, -2.0], [1.4, 0.8, 4.0], green);
        var head = child(body, [0, 0.2, 2.5], 0, 0, 0);
        pen.part(head, 'box', [0, 0, 1.2], [1.6, 0.7, 2.6], green);
        var jaw = child(head, [0, -0.3, 0.2], 0.6 * st.lunge * Math.abs(Math.sin(t * 9)), 0, 0);
        pen.part(jaw, 'box', [0, -0.15, 1.2], [1.5, 0.3, 2.4], '#3a4a28');
        pen.part(head, 'box', [0.5, 0.5, 0.4], [0.4, 0.4, 0.4], '#d8c83a');
        pen.part(head, 'box', [-0.5, 0.5, 0.4], [0.4, 0.4, 0.4], '#d8c83a');
        for (var tooth = 0; tooth < 4; tooth++) {
          pen.part(head, 'box', [0.65, -0.4, 0.6 + tooth * 0.5], [0.1, 0.24, 0.1], '#f2f2e6');
          pen.part(head, 'box', [-0.65, -0.4, 0.6 + tooth * 0.5], [0.1, 0.24, 0.1], '#f2f2e6');
        }
      }
    };
  });

  Rigs.register('python', function (spec) {
    var f = frame(spec.p, 0);
    return {
      radius: 12,
      draw: function (pen, t, ctx) {
        var v = ctx.viewer ? ctx.viewer() : null;
        for (var k = 0; k < 26; k++) {
          var a = k * 0.55, rr = 3.6 - k * 0.09;
          pen.part(f, 'box', [Math.cos(a) * rr, 0.4 + k * 0.05, Math.sin(a) * rr * 0.7], [1.0, 0.9, 1.0],
                   k % 3 ? '#8a7a3a' : '#5a4a22');
        }
        var look = 0;
        if (v && v.eye) look = Math.atan2(v.eye[0] - spec.p[0], v.eye[2] - spec.p[2]);
        var neck = child(f, [0, 1.6, 0], 0, look, 0);
        var sway = Math.sin(t * 1.1) * 0.3;
        pen.part(neck, 'box', [sway, 0.8, 0.6], [0.8, 1.8, 0.8], '#8a7a3a', { rx: -0.4 });
        var head = child(neck, [sway, 1.9, 1.2], 0, 0, 0);
        pen.part(head, 'box', [0, 0, 0.3], [1.0, 0.6, 1.4], '#7a6a32');
        pen.part(head, 'box', [0.36, 0.2, 0.4], [0.1, 0.16, 0.16], '#e8d83a');
        pen.part(head, 'box', [-0.36, 0.2, 0.4], [0.1, 0.16, 0.16], '#e8d83a');
        if (Math.sin(t * 3) > 0.6) pen.part(head, 'box', [0, -0.1, 1.3], [0.12, 0.06, 0.8], '#c43a32');
      }
    };
  });

  Rigs.register('gorilla', function (spec) {
    var beat = -10;
    var f0 = frame(spec.p, spec.yaw || 0);
    var st = { x: spec.p[0], z: spec.p[2], yaw: 0 };
    return {
      radius: 30,
      event: function (kind) { if (kind === 'roar' || kind === 'lure' || kind === 'blast') beat = Rigs.clock(); },
      update: function (dt, t, ctx) {
        if (t - beat < dt * 1.5 && ctx.sound) ctx.sound('ll_chestbeat', spec.p, 1);
        var u = Math.floor(t / 12);
        var tx = spec.p[0] + (hash(u) - 0.5) * 22, tz = spec.p[2] + (hash(u + 3) - 0.5) * 18;
        var dx = tx - st.x, dz = tz - st.z, d = Math.hypot(dx, dz);
        st.moving = d > 0.6 && t - beat > 3;
        if (st.moving) {
          st.x += dx / d * Math.min(d, 2.2 * dt); st.z += dz / d * Math.min(d, 2.2 * dt);
          st.yaw = approachAngle(st.yaw, Math.atan2(dx, dz), 3, dt);
        } else {
          var near = nearest(ctx.players ? ctx.players() : [], [st.x, 0, st.z], 60);
          if (near) st.yaw = approachAngle(st.yaw, Math.atan2(near.who.pos[0] - st.x, near.who.pos[2] - st.z), 1.5, dt);
        }
        this.at = [st.x, spec.p[1], st.z];
      },
      draw: function (pen, t) {
        var f = frame([st.x, spec.p[1], st.z], st.yaw, 1);
        var fur = '#2a2a2e';
        var beating = t - beat < 3;
        var phase = t * 5;
        var lean = st.moving ? 0.5 : (beating ? -0.15 : 0.1);
        legsAt(pen, f, [[-0.9, -0.4], [0.9, -0.4]], 1.6, 1.0, fur, phase, st.moving ? 0.3 : 0);
        var body = child(f, [0, 1.6, -0.4], lean, 0, 0);
        pen.part(body, 'box', [0, 1.4, 0], [3.0, 3.0, 2.2], fur);
        pen.part(body, 'box', [0, 1.4, 1.12], [1.8, 1.8, 0.1], '#4a4a52');
        var head = child(body, [0, 3.2, 0.5], -lean * 0.8, 0, 0);
        pen.part(head, 'box', [0, 0.4, 0], [1.6, 1.6, 1.4], fur);
        pen.part(head, 'box', [0, 0.85, 0.65], [1.5, 0.4, 0.3], '#1a1a1e');
        pen.part(head, 'box', [0, 0.1, 0.72], [1.0, 0.7, 0.2], '#3a3a42');
        pen.part(head, 'box', [0.36, 0.55, 0.72], [0.18, 0.14, 0.06], '#c8a83a');
        pen.part(head, 'box', [-0.36, 0.55, 0.72], [0.18, 0.14, 0.06], '#c8a83a');
        for (var side = -1; side <= 1; side += 2) {
          var swing = beating ? (Math.sin(t * 14 + (side > 0 ? 0 : Math.PI)) > 0 ? -1.7 : -1.2)
            : (st.moving ? Math.sin(phase + (side > 0 ? 0 : Math.PI)) * 0.5 - 0.4 : 0.1);
          var arm = child(body, [side * 1.8, 2.6, 0], swing, 0, beating ? -side * 0.9 : side * 0.15);
          pen.part(arm, 'box', [0, -1.7, 0], [1.0, 3.4, 1.0], fur);
          pen.part(arm, 'box', [0, -3.5, 0.1], [1.1, 0.8, 1.2], '#3a3a42');
        }
      }
    };
  });

  /* Mei Mei, asleep on her platform, breathing, the Zs drifting up --
     a bang nearby and she sits up and looks about, then goes back down. */
  Rigs.register('panda', function (spec) {
    var f = frame(spec.p, spec.yaw || 0);
    var woke = -10;
    return {
      radius: 20,
      event: function (kind, msg) {
        var from = msg && (msg.p || msg.from);
        if ((kind === 'blast' || kind === 'roar') && (!from || Math.hypot(from[0] - spec.p[0], from[2] - spec.p[2]) < 100)) woke = Rigs.clock();
      },
      draw: function (pen, t) {
        var up = t - woke < 5;
        var breathe = 1 + Math.sin(t * 1.4) * 0.04;
        var body = child(f, [0, up ? 1.6 : 1.0, 0], up ? -1.2 : 0, 0, up ? 0 : Math.PI / 2 * 0.9);
        pen.part(body, 'box', [0, 0, 0], [2.6 * breathe, 2.4 * breathe, 3.2], '#f2f2ec');
        pen.part(body, 'box', [0, 0.6, 0], [2.7 * breathe, 0.9, 1.6], '#1a1a1e');
        for (var side = -1; side <= 1; side += 2) {
          pen.part(body, 'box', [side * 1.3, -0.4, 1.0], [0.9, 0.9, 1.4], '#1a1a1e');
          pen.part(body, 'box', [side * 1.3, -0.6, -1.2], [0.9, 0.9, 1.4], '#1a1a1e');
        }
        var head = child(body, [0, 0.4, 2.2], up ? 1.2 + Math.sin(t * 2) * 0.2 : 0, up ? Math.sin(t * 1.5) * 0.6 : 0, 0);
        pen.part(head, 'box', [0, 0, 0.4], [1.8, 1.6, 1.6], '#f2f2ec');
        for (var e = -1; e <= 1; e += 2) {
          pen.part(head, 'box', [e * 0.75, 0.85, 0.2], [0.5, 0.5, 0.3], '#1a1a1e');
          pen.part(head, 'box', [e * 0.42, 0.15, 1.21], [0.44, 0.5, 0.06], '#1a1a1e');
          if (up) pen.part(head, 'box', [e * 0.42, 0.18, 1.25], [0.12, 0.12, 0.04], '#f2f2ec');
        }
        pen.part(head, 'box', [0, -0.35, 1.22], [0.3, 0.2, 0.06], '#1a1a1e');
        if (!up && pen.near) {
          for (var z = 0; z < 3; z++) {
            var u = (t * 0.3 + z / 3) % 1;
            var p = Rigs.point(f, [0.8 + u * 1.6, 3.0 + u * 5, 1.5]);
            pen.part(frame(p, 0), 'box', [0, 0, 0], [0.9, 0.9, 0.1], '#f2f2f2',
                     { a: 1 - u, dec: textDecal('Z', '#f2f2f2', '#3a4a6a', 1) });
          }
        }
      }
    };
  });

  Rigs.register('goats', function (spec) {
    var steps = spec.steps || [spec.p], n = spec.n || 3;
    return {
      radius: 30,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var k = Math.floor(t / 5 + i * 1.7), u = (t / 5 + i * 1.7) % 1;
          var a = steps[(k + i) % steps.length], b = steps[(k + i + 1) % steps.length];
          var hop = u > 0.8 ? (u - 0.8) / 0.2 : 0;
          var p = [a[0] + (b[0] - a[0]) * hop + Math.sin(i * 2.3) * 1.2, a[1] + (b[1] - a[1]) * hop + Math.sin(hop * Math.PI) * 2.6,
                   a[2] + (b[2] - a[2]) * hop + Math.cos(i * 1.7) * 1.2];
          var yaw = hop > 0 ? Math.atan2(b[0] - a[0], b[2] - a[2]) : Math.sin(t * 0.4 + i) * 1.5;
          var f = frame(p, yaw, 1);
          var c = i % 2 ? '#f2ece0' : '#8a6a4a';
          var tuck = hop > 0 ? 0.7 : 0;
          legsAt(pen, f, [[-0.35, 0.6], [0.35, 0.6], [-0.35, -0.6], [0.35, -0.6]], 1.2, 0.3, c, 0, tuck);
          pen.part(f, 'box', [0, 1.6, 0], [1.0, 0.9, 2.0], c);
          var head = child(f, [0, 2.2, 1.0], hop > 0 ? -0.3 : 0.3 + Math.sin(t * 3 + i) * 0.2, 0, 0);
          pen.part(head, 'box', [0, 0, 0.4], [0.6, 0.6, 0.9], c);
          pen.part(head, 'box', [0.2, 0.45, 0.1], [0.14, 0.5, 0.14], '#5a4a3a', { rx: -0.5 });
          pen.part(head, 'box', [-0.2, 0.45, 0.1], [0.14, 0.5, 0.14], '#5a4a3a', { rx: -0.5 });
          pen.part(head, 'box', [0, -0.45, 0.6], [0.14, 0.4, 0.14], c);
        }
      }
    };
  });

  Rigs.register('ducks', function (spec) {
    var area = spec.area, n = spec.n || 4;
    return {
      radius: 20,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var a = t * 0.12 + i * 1.6;
          var x = (area[0] + area[1]) / 2 + Math.sin(a + i) * ((area[1] - area[0]) / 2 - 2);
          var z = (area[2] + area[3]) / 2 + Math.sin(a * 1.4 + i * 2) * ((area[3] - area[2]) / 2 - 2);
          var yaw = Math.atan2(Math.cos(a + i), Math.cos(a * 1.4 + i * 2) * 1.4);
          var f = frame([x, spec.p[1] + Math.sin(t * 2 + i) * 0.05, z], yaw, 1);
          pen.part(f, 'box', [0, 0.3, 0], [0.8, 0.6, 1.3], i % 2 ? '#8a6a4a' : '#f2f2ec');
          pen.part(f, 'box', [0, 0.85, 0.5], [0.5, 0.5, 0.5], i % 2 ? '#2a6a3a' : '#f2f2ec');
          pen.part(f, 'box', [0, 0.8, 0.85], [0.3, 0.14, 0.3], '#e8a03a');
        }
      }
    };
  });

  /* A rotating warning beacon. */
  Rigs.register('beacon', function (spec) {
    var f = frame(spec.p, 0);
    var c = spec.colour || '#ff8a2a';
    return {
      radius: 8,
      draw: function (pen, t) {
        pen.part(f, 'cyl', [0, 0.3, 0], [1.2, 0.6, 1.2], '#2a2d31');
        pen.part(f, 'sph', [0, 0.9, 0], [1.1, 1.1, 1.1], c, { m: 'neon', a: 0.7 });
        var beam = child(f, [0, 0.9, 0], 0, t * 4, 0);
        pen.part(beam, 'box', [0, 0, 3], [0.6, 0.6, 6], c, { m: 'neon', a: 0.25 });
      }
    };
  });

  // ========================================== Harrow Point Aquarium
  if (GA) {
    GA.register('ll_dolphin', function (vol) {
      // the dolphin show: clicks and whistles over the tannoy, a fanfare,
      // a splash
      for (var i = 0; i < 6; i++) {
        this.later(i * 90, function () { this.tone({ type: 'square', freq: 2400, dur: 0.03, gain: 0.05 * vol }); });
      }
      this.later(600, function () { this.tone({ type: 'sine', freq: 1800, freqEnd: 3200, dur: 0.45, gain: 0.07 * vol }); });
      this.later(1100, function () { this.tone({ type: 'sine', freq: 3000, freqEnd: 1600, dur: 0.5, gain: 0.07 * vol }); });
      [392, 494, 587, 784].forEach(function (f, k) {
        this.later(1700 + k * 140, function () { this.tone({ type: 'sawtooth', freq: f, dur: 0.3, gain: 0.05 * vol }); });
      }, this);
      this.later(2400, function () { this.noise({ filter: 'highpass', freq: 900, freqEnd: 300, dur: 1.0, gain: 0.12 * vol }); });
    });
    GA.register('ll_splash', function (vol) {
      this.noise({ filter: 'highpass', freq: 1200, freqEnd: 300, dur: 0.6, gain: 0.1 * vol });
    });
    GA.register('ll_gull', function (vol) {
      this.tone({ type: 'sawtooth', freq: 1300, freqEnd: 1900, dur: 0.25, gain: 0.04 * vol });
      this.later(260, function () { this.tone({ type: 'sawtooth', freq: 1700, freqEnd: 1100, dur: 0.35, gain: 0.04 * vol }); });
    });
  }

  /* The blue whale's skeleton hung on wires over the Great Hall, swaying
     a little in the draught -- more when a Tank's roar shakes the place. */
  Rigs.register('whale_skeleton', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    var shake = -10;
    return {
      radius: 60,
      event: function (kind) { if (kind === 'roar' || kind === 'blast' || kind === 'lightning') shake = Rigs.clock(); },
      draw: function (pen, t) {
        var k = Math.max(0, 1 - (t - shake) / 5);
        var sway = Math.sin(t * 0.5) * 0.03 + Math.sin(t * 7) * 0.05 * k;
        var f = child(f0, [0, 0, 0], 0, Math.sin(t * 0.2) * 0.04, sway);
        var bone = '#e8e0cc';
        // the wires up to the roof
        pen.rod(Rigs.point(f, [0, 1.6, 14]), Rigs.point(f, [0, 16, 14]), 0.12, '#3a3f46');
        pen.rod(Rigs.point(f, [0, 1.6, -12]), Rigs.point(f, [0, 16, -12]), 0.12, '#3a3f46');
        // the skull and jaw, the spine in vertebrae, the ribs, the flippers
        pen.part(f, 'box', [0, 0, 24], [6, 3.2, 10], bone);
        pen.part(f, 'box', [0, -2.4, 24.5], [5.4, 0.8, 10.5], bone, { rx: 0.08 });
        for (var v = 0; v < 26; v++) {
          var z = 18 - v * 1.9;
          var w = v < 14 ? 2.2 : 2.2 - (v - 14) * 0.15;
          var bend = Math.sin(t * 0.6 + v * 0.25) * 0.05 * (v / 26);
          pen.part(f, 'box', [Math.sin(bend) * v, 0.2 + (v > 18 ? (v - 18) * 0.25 : 0), z], [w, w, 1.4], bone);
          if (v > 1 && v < 13) {
            for (var side = -1; side <= 1; side += 2) {
              pen.part(f, 'box', [side * 2.4, -1.6, z], [0.4, 3.6, 0.6], bone, { rz: side * 0.35 });
            }
          }
        }
        for (var s2 = -1; s2 <= 1; s2 += 2) {
          pen.part(f, 'box', [s2 * 4.6, -1.0, 13], [5.0, 0.5, 2.0], bone, { ry: s2 * 0.5, rz: s2 * -0.2 });
        }
        pen.part(f, 'box', [0, 1.4, -32], [9, 0.6, 2.2], bone);
      }
    };
  });

  /* A school of small fish turning about a tank, darting off together
     from a shot. */
  Rigs.register('fish_school', function (spec) {
    var a = spec.area, n = spec.n || 12, seed = spec.seed || 1;
    var y0 = spec.y0 || spec.p[1] - 5, y1 = spec.y1 || spec.p[1] + 5;
    var colours = ['#f2c83a', '#e8783a', '#3ac8e8', '#f2f2f2', '#9a6ae8', '#e83a5a'];
    var dart = -10;
    return {
      radius: Math.max(a[1] - a[0], a[3] - a[2]),
      event: function (kind) { if (kind === 'shot' || kind === 'blast') dart = Rigs.clock(); },
      draw: function (pen, t) {
        var speed = 1 + 2.5 * Math.max(0, 1 - (t - dart) / 2);
        var cx = (a[0] + a[1]) / 2, cz = (a[2] + a[3]) / 2;
        var rx = (a[1] - a[0]) / 2 - 1, rz = (a[3] - a[2]) / 2 - 1;
        var lead = t * 0.25 * speed + seed;
        var hx = cx + Math.sin(lead) * rx * 0.7, hz = cz + Math.sin(lead * 1.3 + 1) * rz * 0.7;
        var hy = (y0 + y1) / 2 + Math.sin(lead * 0.7) * (y1 - y0) * 0.3;
        var yaw = Math.atan2(Math.cos(lead) * rx, Math.cos(lead * 1.3 + 1) * rz * 1.3);
        for (var i = 0; i < n; i++) {
          var ox = Math.sin(i * 2.3 + t * 0.9) * 2.4, oz = Math.cos(i * 1.7 + t * 0.7) * 2.4;
          var oy = Math.sin(i * 3.1 + t) * 1.6;
          var x = clamp(hx + ox, a[0] + 0.5, a[1] - 0.5), z = clamp(hz + oz, a[2] + 0.5, a[3] - 0.5);
          var f = frame([x, clamp(hy + oy, y0, y1), z], yaw + Math.sin(t * 6 + i) * 0.15, 1);
          var c = colours[(i + seed) % colours.length];
          pen.part(f, 'box', [0, 0, 0], [0.3, 0.6, 1.0], c);
          pen.part(f, 'box', [0, 0, -0.65], [0.1, 0.5, 0.4], c, { ry: Math.sin(t * 14 + i) * 0.5 });
        }
      }
    };
  });

  Rigs.register('sharks', function (spec) {
    var a = spec.area, n = spec.n || 3;
    var y0 = spec.y0, y1 = spec.y1;
    return {
      radius: Math.max(a[1] - a[0], a[3] - a[2]),
      draw: function (pen, t) {
        var cx = (a[0] + a[1]) / 2, cz = (a[2] + a[3]) / 2;
        var rx = (a[1] - a[0]) / 2 - 4, rz = (a[3] - a[2]) / 2 - 4;
        for (var i = 0; i < n; i++) {
          var u = t * (0.08 + i * 0.015) * (i % 2 ? -1 : 1) + i * 1.7;
          var x = cx + Math.cos(u) * rx * (0.6 + 0.4 * Math.sin(i + t * 0.05));
          var z = cz + Math.sin(u) * rz * (0.7 + 0.3 * Math.cos(i * 2 + t * 0.04));
          var y = (y0 + y1) / 2 + Math.sin(t * 0.3 + i * 2) * (y1 - y0) * 0.4;
          var yaw = Math.atan2(-Math.sin(u) * rx, Math.cos(u) * rz) * (i % 2 ? -1 : 1) + (i % 2 ? Math.PI : 0);
          var f = frame([x, y, z], yaw, 1.2 + (i % 2) * 0.4);
          var grey = '#6a7a8a';
          var tail = child(f, [0, 0, -3.0], 0, Math.sin(t * 3 + i) * 0.35, 0);
          pen.part(f, 'box', [0, 0, 0], [1.8, 1.8, 6.0], grey);
          pen.part(f, 'box', [0, -0.5, 0.4], [1.5, 0.8, 5.0], '#e8ecee');
          pen.part(f, 'box', [0, 0.1, 3.6], [1.3, 1.2, 1.6], grey);
          pen.part(f, 'box', [0, 1.6, 0.2], [0.3, 1.8, 1.4], grey, { rx: -0.4 });
          pen.part(tail, 'box', [0, 0, -1.4], [0.9, 1.0, 2.8], grey);
          pen.part(tail, 'box', [0, 0.4, -3.0], [0.2, 2.6, 1.0], grey, { rx: 0.3 });
          for (var s2 = -1; s2 <= 1; s2 += 2) {
            pen.part(f, 'box', [s2 * 1.6, -0.6, 1.0], [1.8, 0.2, 1.0], grey, { rz: s2 * 0.4 });
            pen.part(f, 'box', [s2 * 0.62, 0.3, 3.9], [0.06, 0.3, 0.3], '#0a0a0a');
          }
        }
      }
    };
  });

  /* The octopus in the deep sea room's tank: arms curling, and its eye on
     whoever is in the room. */
  Rigs.register('octopus', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    return {
      radius: 16,
      draw: function (pen, t, ctx) {
        var v = ctx.viewer ? ctx.viewer() : null;
        var bob = Math.sin(t * 0.9) * 0.4;
        var f = child(f0, [0, 1.6 + bob, -1.2], 0, 0, 0);
        var red = '#c8503a';
        pen.part(f, 'sph', [0, 1.4, -0.4], [3.0, 3.4, 3.0], red);
        for (var i = 0; i < 8; i++) {
          var ang = i / 8 * TAU;
          var arm = child(f, [Math.cos(ang) * 0.9, -0.2, Math.sin(ang) * 0.9], 0, -ang + Math.PI / 2, 0);
          for (var k = 0; k < 4; k++) {
            arm = child(arm, [0, 0, 0.8], 0.3 + Math.sin(t * 1.4 + i + k * 0.8) * 0.35, 0, 0);
            pen.part(arm, 'box', [0, 0, 0.4], [0.5 - k * 0.08, 0.5 - k * 0.08, 0.9], red);
          }
        }
        // the eyes: on the viewer, wherever they are in the room
        var look = 0;
        if (v && v.eye) {
          var w = Rigs.point(f, [0, 0, 0]);
          look = clamp(Math.atan2(v.eye[0] - w[0], v.eye[2] - w[2]) - (spec.yaw || 0), -1, 1);
        }
        for (var s2 = -1; s2 <= 1; s2 += 2) {
          var eye = child(f, [s2 * 0.9, 1.2, 1.1], 0, look * 0.6, 0);
          pen.part(eye, 'sph', [0, 0, 0], [0.8, 0.8, 0.5], '#f2e8b0');
          pen.part(eye, 'box', [0, 0, 0.24], [0.5, 0.16, 0.06], '#0a0a0a');
        }
      }
    };
  });

  Rigs.register('anglerfish', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    return {
      radius: 10,
      draw: function (pen, t) {
        var f = child(f0, [Math.sin(t * 0.4) * 2.5, Math.sin(t * 0.7) * 0.3, 0], 0, Math.sin(t * 0.4) > 0 ? Math.PI / 2 : -Math.PI / 2, 0);
        pen.part(f, 'box', [0, 0, 0], [1.4, 1.4, 2.0], '#2a2018');
        pen.part(f, 'box', [0, -0.4, 1.1], [1.3, 0.5, 0.4], '#1a1410');
        for (var k = 0; k < 4; k++) pen.part(f, 'box', [-0.45 + k * 0.3, -0.15, 1.25], [0.08, 0.3, 0.08], '#e8e0cc');
        var rod = child(f, [0, 0.7, 0.6], -0.8 + Math.sin(t * 2) * 0.1, 0, 0);
        pen.part(rod, 'box', [0, 0.6, 0], [0.08, 1.2, 0.08], '#2a2018');
        var glow = 0.6 + 0.4 * Math.sin(t * 3);
        pen.part(rod, 'sph', [0, 1.3, 0], [0.4, 0.4, 0.4], '#c8ff8a', { m: 'neon', a: glow });
      }
    };
  });

  /* Jellyfish rising and falling in a lit column, pulsing. */
  Rigs.register('jellyfish', function (spec) {
    var n = spec.n || 3, seed = spec.seed || 0, c = spec.colour || '#9ab8ff';
    return {
      radius: 8,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var ph = t * 0.4 + i * 2.1 + seed;
          var y = spec.p[1] + Math.sin(ph) * 3.6;
          var p = [spec.p[0] + Math.sin(ph * 0.7 + i) * 1.2, y, spec.p[2] + Math.cos(ph * 0.5 + i) * 1.2];
          var f = frame(p, t * 0.2 + i, 1);
          var pulse = 1 + Math.sin(t * 3 + i * 1.3) * 0.18;
          pen.part(f, 'sph', [0, 0, 0], [1.6 * pulse, 1.0 / pulse, 1.6 * pulse], c, { m: 'neon', a: 0.55 });
          for (var k = 0; k < 4; k++) {
            var ang = k / 4 * TAU;
            pen.part(f, 'box', [Math.cos(ang) * 0.5, -1.3 + Math.sin(t * 2 + k) * 0.2, Math.sin(ang) * 0.5],
                     [0.08, 2.2, 0.08], c, { m: 'neon', a: 0.4, rx: Math.sin(t * 2 + k + i) * 0.2 });
          }
        }
      }
    };
  });

  /* Dolphins circling under the show pool's surface, breaking it now and
     then -- and when the show starts, leaping clear in turn. */
  Rigs.register('dolphins', function (spec) {
    var a = spec.area, bed = spec.bed || spec.p[1] - 3;
    var show = -10, lastSplash = 0;
    return {
      radius: Math.max(a[1] - a[0], a[3] - a[2]),
      event: function (kind) { if (kind === 'lure') show = Rigs.clock() + 16; },
      update: function (dt, t, ctx) {
        if (t < show && t - lastSplash > 1.4) { lastSplash = t; if (ctx.sound) ctx.sound('ll_splash', spec.p, 0.8); }
      },
      draw: function (pen, t) {
        var cx = (a[0] + a[1]) / 2, cz = (a[2] + a[3]) / 2;
        var rx = (a[1] - a[0]) / 2 - 6, rz = (a[3] - a[2]) / 2 - 5;
        var on = t < show;
        for (var i = 0; i < 3; i++) {
          var u = t * (on ? 0.5 : 0.25) + i * TAU / 3;
          var x = cx + Math.cos(u) * rx, z = cz + Math.sin(u) * rz;
          var leap = on ? Math.max(0, Math.sin(t * 2.2 + i * 2.1)) : Math.max(0, Math.sin(t * 0.7 + i * 2.1) - 0.85) * 4;
          var y = spec.p[1] - 1.4 + leap * (on ? 8 : 1.2);
          var yaw = Math.atan2(-Math.sin(u) * rx, Math.cos(u) * rz);
          var pitch = on ? -Math.cos(t * 2.2 + i * 2.1) * 0.9 : 0;
          var f = child(frame([x, Math.max(bed + 0.8, y), z], yaw, 1), [0, 0, 0], pitch, 0, 0);
          pen.part(f, 'box', [0, 0, 0], [1.4, 1.4, 4.4], '#7a8a9a');
          pen.part(f, 'box', [0, -0.4, 0.2], [1.2, 0.7, 3.6], '#c8d0d8');
          pen.part(f, 'box', [0, -0.1, 2.7], [0.6, 0.5, 1.2], '#7a8a9a');
          pen.part(f, 'box', [0, 1.0, -0.2], [0.2, 1.0, 1.0], '#7a8a9a', { rx: -0.5 });
          var tail = child(f, [0, 0, -2.2], Math.sin(t * 5 + i) * 0.3, 0, 0);
          pen.part(tail, 'box', [0, 0, -0.8], [2.4, 0.2, 0.8], '#7a8a9a');
        }
      }
    };
  });

  Rigs.register('turtles', function (spec) {
    var tanks = spec.tanks || [[spec.p[0], spec.p[2]]];
    return {
      radius: 30,
      draw: function (pen, t) {
        for (var i = 0; i < tanks.length; i++) {
          var u = t * 0.3 + i * 2;
          var p = [tanks[i][0] + Math.sin(u) * 2.6, spec.p[1] - 0.6, tanks[i][1] + Math.cos(u * 1.3) * 1.8];
          var f = frame(p, Math.atan2(Math.cos(u) * 2.6, -Math.sin(u * 1.3) * 2.3), 1);
          pen.part(f, 'box', [0, 0, 0], [1.8, 0.6, 2.2], '#4a6a3a');
          pen.part(f, 'box', [0, 0.32, 0], [1.4, 0.2, 1.8], '#6a5a2a');
          pen.part(f, 'box', [0, 0.05, 1.4], [0.6, 0.5, 0.7], '#7a8a5a');
          for (var s2 = -1; s2 <= 1; s2 += 2) {
            pen.part(child(f, [s2 * 0.9, 0, 0.6], 0, 0, s2 * Math.sin(t * 2.4 + i) * 0.4), 'box', [s2 * 0.6, 0, 0],
                     [1.2, 0.12, 0.6], '#7a8a5a');
          }
        }
      }
    };
  });

  /* Gulls wheeling on the wind, blown off line by the gusts. */
  Rigs.register('gulls', function (spec) {
    var n = spec.n || 6, r = spec.r || 60;
    var cry = 0;
    return {
      radius: r + 40,
      update: function (dt, t, ctx) {
        if (t > cry) { cry = t + 7 + hash(Math.floor(t)) * 9; if (ctx.sound) ctx.sound('ll_gull', spec.p, 0.6); }
      },
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var u = t * (0.12 + hash(i) * 0.06) + i * 1.3;
          var gust = Math.sin(t * 0.9 + i) * 8;
          var p = [spec.p[0] + Math.cos(u) * r * (0.5 + hash(i + 3) * 0.5) + gust, spec.p[1] + Math.sin(t * 0.5 + i) * 6,
                   spec.p[2] + Math.sin(u) * r * 0.5];
          var f = frame(p, Math.atan2(-Math.sin(u), Math.cos(u) * 0.5), 1);
          pen.part(f, 'box', [0, 0, 0], [0.6, 0.6, 1.6], '#f2f2f2');
          pen.part(f, 'box', [0, 0.1, 0.9], [0.2, 0.2, 0.4], '#f2c83a');
          var flap = Math.sin(t * 6 + i) * 0.5 + 0.2;
          pen.part(child(f, [0.3, 0.1, 0], 0, 0, -flap), 'box', [1.3, 0, 0], [2.6, 0.08, 0.9], '#d8dce0');
          pen.part(child(f, [-0.3, 0.1, 0], 0, 0, flap), 'box', [-1.3, 0, 0], [2.6, 0.08, 0.9], '#d8dce0');
        }
      }
    };
  });

  /* Surf breaking along the shoreline: white crests rolling in and
     falling over, all along it. */
  Rigs.register('surf', function (spec) {
    var w = spec.w || 400;
    return {
      radius: w / 2 + 40,
      draw: function (pen, t) {
        var eye = pen.eye || spec.p;
        for (var k = 0; k < 3; k++) {
          var u = (t * 0.18 + k / 3) % 1;
          var z = spec.p[2] - 30 + u * 30;
          var lift = Math.sin(u * Math.PI) * 0.8;
          for (var j = -6; j <= 6; j++) {
            var x = Math.round(eye[0] / 20) * 20 + j * 20;
            if (Math.abs(x - spec.p[0]) > w / 2) continue;
            pen.part(frame([x, spec.p[1] + 0.2 + lift, z + Math.sin(x * 0.07 + t) * 2], 0, 1), 'box', [0, 0, 0],
                     [19.6, 0.4 + lift * 0.6, 1.4 + u * 2], '#e8f2f6', { a: 0.75 * (1 - u * 0.6) });
          }
        }
      }
    };
  });

  Rigs.register('buoy', function (spec) {
    return {
      radius: 10,
      draw: function (pen, t) {
        var f = child(frame(spec.p, 0), [0, Math.sin(t * 1.3) * 0.4, 0], Math.sin(t * 1.1) * 0.15, 0, Math.cos(t * 0.9) * 0.15);
        pen.part(f, 'cyl', [0, 0.4, 0], [3.0, 1.6, 3.0], '#e83a3a');
        pen.part(f, 'box', [0, 2.6, 0], [0.8, 3.0, 0.8], '#e83a3a');
        var on = Math.sin(t * 2.5) > 0.6;
        pen.part(f, 'sph', [0, 4.4, 0], [0.8, 0.8, 0.8], on ? '#ffe8a0' : '#5a4a2a', { m: on ? 'neon' : '' });
      }
    };
  });

  // ============================================ Silver Screen Studios
  if (GA) {
    GA.register('ll_boom', function (vol) {
      this.noise({ freq: 600, freqEnd: 60, dur: 1.2, gain: 0.3 * vol });
      this.tone({ type: 'sawtooth', freq: 70, freqEnd: 30, dur: 0.9, gain: 0.12 * vol });
    });
    GA.register('ll_pyro', function (vol) {
      // the first assistant through a loudhailer, then the charges
      this.tone({ type: 'square', freq: 300, freqEnd: 260, dur: 0.25, gain: 0.06 * vol });
      this.later(300, function () { this.tone({ type: 'square', freq: 420, freqEnd: 380, dur: 0.4, gain: 0.07 * vol }); });
      for (var i = 0; i < 5; i++) {
        this.later(900 + i * 320, function () {
          this.noise({ freq: 700, freqEnd: 70, dur: 0.9, gain: 0.26 * vol });
          this.tone({ type: 'sawtooth', freq: 80, freqEnd: 34, dur: 0.6, gain: 0.1 * vol });
        });
      }
    });
  }

  /* A premiere searchlight on its trailer: the beam swinging across the
     sky, the lamp housing turning with it. */
  Rigs.register('searchlight', function (spec) {
    var f0 = frame(spec.p, 0);
    var seed = spec.seed || 1;
    return {
      radius: 400,
      draw: function (pen, t) {
        var yaw = Math.sin(t * 0.21 + seed * 2) * 1.2 + seed;
        var pitch = 0.35 + Math.sin(t * 0.33 + seed) * 0.25;
        var head = child(f0, [0, 1.4, 0], -pitch, yaw, 0);
        pen.part(head, 'cyl', [0, 0, 0], [2.8, 3.6, 2.8], '#3a3f46', { m: 'metal', rx: Math.PI / 2 });
        pen.part(head, 'cyl', [0, 0, 1.85], [2.4, 0.1, 2.4], '#fff6d8', { m: 'neon', rx: Math.PI / 2 });
        var len = 340;
        pen.part(head, 'cone', [0, 0, len / 2 + 1.8], [26, len, 26], '#e8ecff', { m: 'neon', a: 0.06, rx: -Math.PI / 2 });
        pen.part(head, 'cone', [0, 0, len / 4 + 1.8], [8, len / 2, 8], '#ffffff', { m: 'neon', a: 0.07, rx: -Math.PI / 2 });
      }
    };
  });

  /* The camera crane on the war set: the arm swinging out over the
     trenches and back, the camera on the end of it panning to follow
     whatever is moving down there. */
  Rigs.register('camera_crane', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    var aim = 0;
    return {
      radius: 40,
      update: function (dt, t, ctx) {
        var near = nearest((ctx.zombies ? ctx.zombies() : []).concat(ctx.players ? ctx.players() : []), spec.p, 70);
        var target = near ? Math.atan2(near.who.pos[0] - spec.p[0], near.who.pos[2] - spec.p[2]) : Math.sin(t * 0.2) * 1.5;
        aim = approachAngle(aim, target, 0.8, dt);
      },
      draw: function (pen, t) {
        pen.part(f0, 'box', [0, 1.0, 0], [6, 2, 8], '#2a2a2e');
        pen.part(f0, 'cyl', [0, 4, 0], [1.4, 6, 1.4], '#3a3a3e', { m: 'metal' });
        var arm = child(f0, [0, 7, 0], -0.25 + Math.sin(t * 0.4) * 0.15, aim, 0);
        pen.part(arm, 'box', [0, 0, 7], [0.8, 0.8, 20], '#c8c8c8', { m: 'metal' });
        pen.part(arm, 'box', [0, 0, -5], [1.6, 1.6, 4], '#2a2a2e');
        var cam = child(arm, [0, -1.2, 17], 0.25 - Math.sin(t * 0.4) * 0.15, 0, 0);
        pen.part(cam, 'box', [0, 0, 0], [1.6, 1.6, 2.6], '#1a1a1a');
        pen.part(cam, 'cyl', [0, 0, 1.6], [1.0, 0.8, 1.0], '#3a3a3a', { rx: Math.PI / 2 });
        pen.part(cam, 'cyl', [0, 1.4, -0.4], [1.6, 0.4, 1.6], '#2a2a2a', { rz: Math.PI / 2 });
        pen.part(cam, 'box', [0.9, 0.5, 0.9], [0.1, 0.3, 0.3], '#ff3a2a', { m: 'neon' });
      }
    };
  });

  /* Lamps hung along a catwalk, tilting and panning in slow sweeps, their
     beams down onto the set. */
  Rigs.register('stage_lights', function (spec) {
    var n = spec.n || 5, span = spec.span || 100;
    var warm = spec.warm ? '#ffd8a0' : '#d8e8ff';
    return {
      radius: span / 2 + 30,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var x = spec.p[0] - span / 2 + span * (i + 0.5) / n;
          var f = frame([x, spec.p[1] - 0.4, spec.p[2]], 0);
          pen.part(f, 'box', [0, -0.6, 0], [0.4, 1.2, 0.4], '#2a2a2a');
          var lamp = child(f, [0, -1.6, 0], Math.PI - 0.5 + Math.sin(t * 0.5 + i * 1.3) * 0.35,
                           Math.sin(t * 0.37 + i) * 0.5, 0);
          pen.part(lamp, 'box', [0, 0, 0], [1.4, 1.4, 2.2], '#2a2a2e');
          pen.part(lamp, 'cyl', [0, 0, 1.12], [1.1, 0.06, 1.1], warm, { m: 'neon', rx: Math.PI / 2 });
          pen.part(lamp, 'cone', [0, 0, 13], [9, 24, 9], warm, { m: 'neon', a: 0.06, rx: -Math.PI / 2 });
        }
      }
    };
  });

  /* The dragon's head over the throne: eyes that light and follow you,
     smoke from the nostrils, and on a roar or a bang the jaw drops and
     the fire comes out. */
  Rigs.register('dragon_head', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    var fire = -10;
    return {
      radius: 30,
      event: function (kind) { if (kind === 'roar' || kind === 'lure' || kind === 'blast') fire = Rigs.clock(); },
      draw: function (pen, t, ctx) {
        var v = ctx.viewer ? ctx.viewer() : null;
        var look = 0;
        if (v && v.eye) look = clamp(Math.atan2(v.eye[0] - spec.p[0], v.eye[2] - spec.p[2]) - (spec.yaw || 0), -0.6, 0.6);
        var blazing = t - fire < 2.5;
        var head = child(f0, [0, 0, 1.2], 0.25, look * 0.5, 0);
        var green = '#2a5a2a';
        pen.part(head, 'box', [0, 0, 2], [6, 4, 7], green, { st: 1 });
        pen.part(head, 'box', [0, 0.6, 6.2], [4, 2.6, 3], green);
        var jaw = child(head, [0, -2, 1], blazing ? 0.5 : 0.08, 0, 0);
        pen.part(jaw, 'box', [0, -0.6, 3.6], [4.4, 1.2, 6.6], '#1f4a1f');
        for (var k = 0; k < 5; k++) {
          pen.part(head, 'box', [-1.6 + k * 0.8, -2.2, 7.2], [0.3, 0.8, 0.3], '#e8e0cc');
        }
        for (var s2 = -1; s2 <= 1; s2 += 2) {
          pen.part(head, 'box', [s2 * 2.0, 3.2, -0.6], [0.8, 3.0, 0.8], '#e8e0cc', { rx: -0.6 });
          pen.part(head, 'box', [s2 * 2.1, 1.0, 4.0], [1.0, 0.8, 0.4], blazing ? '#ff3a1a' : '#ffd83a', { m: 'neon' });
          var puff = (t * 0.6 + (s2 > 0 ? 0.5 : 0)) % 1;
          pen.part(head, 'sph', [s2 * 1.0, 1.4 + puff * 3, 7.8 + puff * 2], [0.8 + puff * 2, 0.8 + puff * 2, 0.8 + puff * 2],
                   '#8a8a8a', { a: 0.4 * (1 - puff) });
        }
        if (blazing) {
          for (var j = 0; j < 6; j++) {
            var u = ((t - fire) * 2 + j / 6) % 1;
            pen.part(head, 'sph', [Math.sin(j * 2.3 + t * 9) * u * 2, -2 - u * 6, 8 + u * 14], [1.5 + u * 4, 1.5 + u * 4, 1.5 + u * 4],
                     u < 0.5 ? '#ffd83a' : '#ff5a1a', { m: 'neon', a: 0.8 * (1 - u) });
          }
        }
      }
    };
  });

  /* The Earth hung in the moon set's black sky, turning. */
  Rigs.register('earth_globe', function (spec) {
    var f0 = frame(spec.p, 0);
    return {
      radius: 20,
      draw: function (pen, t) {
        var f = child(f0, [0, 0, 0], 0.4, t * 0.15, 0);
        pen.part(f, 'sph', [0, 0, 0], [14, 14, 14], '#2a5aa8');
        [[0.3, 0.2, 5], [-0.6, -0.3, 4], [1.2, 0.5, 3.5], [2.2, -0.2, 4.6], [3.4, 0.6, 3]].forEach(function (c) {
          var a = c[0];
          pen.part(f, 'sph', [Math.sin(a) * 5.4, c[1] * 6, Math.cos(a) * 5.4], [c[2], c[2] * 0.7, c[2]], '#3a8a3a');
        });
        pen.part(f, 'sph', [0, 6.4, 0], [6, 1.6, 6], '#f2f2f2');
        pen.part(f0, 'box', [0, 12, 0], [0.12, 10, 0.12], '#3a3a3a');
      }
    };
  });

  /* Tumbleweeds bowling down the western street on the wind, bouncing. */
  Rigs.register('tumbleweeds', function (spec) {
    var n = spec.n || 3;
    return {
      radius: (spec.x1 - spec.x0) / 2 + 20,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var u = (t * (0.045 + hash(i) * 0.03) + hash(i + 7)) % 1;
          var x = spec.x1 - u * (spec.x1 - spec.x0);
          var z = spec.z0 + (spec.z1 - spec.z0) * (0.5 + 0.45 * Math.sin(t * 0.3 + i * 2));
          var bounce = Math.abs(Math.sin(t * 3.2 + i)) * 1.4;
          var f = child(frame([x, spec.p[1] + 1.4 + bounce, z], 0), [0, 0, 0], 0, 0, t * 4 + i);
          for (var k = 0; k < 4; k++) {
            pen.part(f, 'box', [0, 0, 0], [2.8, 0.3, 0.3], '#a8865a', { rx: k * 0.8, ry: k * 0.6 });
            pen.part(f, 'box', [0, 0, 0], [0.3, 2.6, 0.3], '#8a6a4a', { rz: k * 0.7, rx: k * 0.4 });
          }
        }
      }
    };
  });

  /* The pirate flag at the masthead, flapping. */
  Rigs.register('ship_flag', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    return {
      radius: 12,
      draw: function (pen, t) {
        for (var k = 0; k < 6; k++) {
          var wave = Math.sin(t * 5 - k * 0.8) * 0.4 * (k / 6 + 0.2);
          pen.part(f0, 'box', [0.8 + k * 1.0, -1.6 + Math.sin(t * 5 - k) * 0.2, wave], [1.0, 3.2, 0.1], '#141414',
                   { ry: wave * 0.5 });
        }
        pen.part(f0, 'box', [3.2, -1.2, Math.sin(t * 5 - 2.4) * 0.2 + 0.07], [1.2, 1.2, 0.06], '#f2f2e6');
        pen.part(f0, 'box', [3.2, -2.4, Math.sin(t * 5 - 2.4) * 0.2 + 0.07], [2.0, 0.3, 0.06], '#f2f2e6', { rz: 0.6 });
        pen.part(f0, 'box', [3.2, -2.4, Math.sin(t * 5 - 2.4) * 0.2 + 0.07], [2.0, 0.3, 0.06], '#f2f2e6', { rz: -0.6 });
      }
    };
  });

  /* A wind machine: a big fan in a cage, blades a blur. */
  Rigs.register('wind_machine', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    return {
      radius: 12,
      draw: function (pen, t) {
        var hub = child(f0, [0, 0, -0.4], 0, 0, t * 18);
        for (var i = 0; i < 4; i++) {
          pen.part(child(hub, [0, 0, 0], 0, 0, i * Math.PI / 2), 'box', [0, 1.6, 0], [1.0, 3.2, 0.2], '#8a8f94', { m: 'metal' });
        }
        pen.part(f0, 'cyl', [0, 0, -0.6], [7.4, 0.3, 7.4], '#2a2a2e', { rx: Math.PI / 2, a: 0.6 });
      }
    };
  });

  /* The special effects: when they are fired, charges go off down the
     trenches one after another -- fireballs, dirt, smoke -- for as long as
     the lure lasts; between takes, a squib now and then. */
  Rigs.register('pyro', function (spec) {
    var shots = spec.shots || [[spec.p[0], spec.p[2]]];
    var floor = spec.floor !== undefined ? spec.floor : spec.p[1];
    var on = -10, lastBoom = 0;
    return {
      radius: 160,
      event: function (kind) { if (kind === 'lure') on = Rigs.clock(); },
      update: function (dt, t, ctx) {
        if (t - on < 16 && t - lastBoom > 1.1) {
          lastBoom = t;
          var k = Math.floor((t - on) / 1.1) % shots.length;
          if (ctx.sound) ctx.sound('ll_boom', [shots[k][0], floor, shots[k][1]], 1);
        }
      },
      draw: function (pen, t) {
        var live = t - on < 16;
        for (var k = 0; k < shots.length; k++) {
          var cycle = live ? ((t - on) - k * 1.1) : ((t + k * 7.3) % 31) - 29;
          var u = live ? (((cycle % (shots.length * 1.1)) + shots.length * 1.1) % (shots.length * 1.1)) / 1.6 : cycle / 1.6;
          if (u < 0 || u > 1) continue;
          var big = live ? 1 : 0.35;
          var p = [shots[k][0], floor + 1 + u * 10 * big, shots[k][1]];
          var f = frame(p, 0);
          pen.part(f, 'sph', [0, 0, 0], [(4 + u * 10) * big, (4 + u * 8) * big, (4 + u * 10) * big],
                   u < 0.35 ? '#ffe07a' : '#ff6a1a', { m: 'neon', a: 0.9 * (1 - u) });
          pen.part(f, 'sph', [0, 4 * u * big, 0], [(6 + u * 14) * big, (6 + u * 10) * big, (6 + u * 14) * big], '#4a4440',
                   { a: 0.5 * u * (1 - u) * 2 });
        }
      }
    };
  });

  // =============================================== Harrow County Fair
  if (GA) {
    GA.register('ll_derby', function (vol) {
      // the derby: engines revving, horns, the crowd, a crunch
      for (var i = 0; i < 3; i++) {
        this.later(i * 380, function () {
          this.tone({ type: 'sawtooth', freq: 60, freqEnd: 180, dur: 0.5, gain: 0.12 * vol });
          this.noise({ freq: 200, freqEnd: 600, dur: 0.5, gain: 0.08 * vol });
        });
      }
      this.later(1200, function () {
        this.tone({ type: 'square', freq: 392, dur: 0.4, gain: 0.07 * vol });
        this.tone({ type: 'square', freq: 494, dur: 0.4, gain: 0.05 * vol });
      });
      this.later(1700, function () { this.noise({ filter: 'bandpass', freq: 1000, dur: 1.4, gain: 0.08 * vol }); });
      this.later(2100, function () { this.noise({ freq: 900, freqEnd: 120, dur: 0.6, gain: 0.22 * vol }); });
    });
    GA.register('ll_ding', function (vol) {
      [1568, 2093, 2637].forEach(function (f, i) { this.tone({ type: 'sine', freq: f, dur: 1.2 - i * 0.2, gain: (0.07 - i * 0.015) * vol }); }, this);
    });
    GA.register('ll_moo', function (vol) {
      this.tone({ type: 'sawtooth', freq: 150, freqEnd: 110, dur: 1.4, gain: 0.08 * vol });
      this.tone({ type: 'sine', freq: 300, freqEnd: 220, dur: 1.4, gain: 0.04 * vol });
    });
    GA.register('ll_cluck', function (vol) {
      for (var i = 0; i < 4; i++) {
        this.later(i * 120, function () { this.tone({ type: 'square', freq: 700, freqEnd: 500, dur: 0.07, gain: 0.04 * vol }); });
      }
    });
    GA.register('ll_knock', function (vol) {
      for (var i = 0; i < 3; i++) {
        this.later(i * 150, function () {
          this.noise({ freq: 260, freqEnd: 120, dur: 0.12, gain: 0.16 * vol });
          this.tone({ type: 'sine', freq: 110, freqEnd: 70, dur: 0.12, gain: 0.1 * vol });
        });
      }
    });
    GA.register('ll_squeal', function (vol) {
      this.tone({ type: 'sawtooth', freq: 900, freqEnd: 1500, dur: 0.25, gain: 0.05 * vol });
      this.later(200, function () { this.tone({ type: 'sawtooth', freq: 1400, freqEnd: 800, dur: 0.3, gain: 0.05 * vol }); });
    });
    GA.register('ll_cackle', function (vol) {
      for (var i = 0; i < 5; i++) {
        this.later(i * 110, function () { this.tone({ type: 'sawtooth', freq: 260 - i * 10, freqEnd: 200, dur: 0.1, gain: 0.07 * vol }); });
      }
    });
  }

  /* The Ferris wheel: the rim, the spokes, the lights chasing round it and
     the gondolas hanging level as it turns. */
  Rigs.register('ferris_wheel', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    var r = spec.r || 30, n = spec.n || 12;
    var colours = ['#e83a3a', '#3a7ac8', '#f2c83a', '#5aa86a', '#e890b0', '#9a6ae8'];
    return {
      radius: r + 20,
      draw: function (pen, t) {
        var turn = t * 0.06;
        var wheel = child(f0, [0, 0, 0], 0, 0, turn);
        for (var side = -1; side <= 1; side += 2) {
          for (var k = 0; k < n; k++) {
            var a0 = k / n * TAU, a1 = (k + 1) / n * TAU;
            var p0 = Rigs.point(wheel, [Math.cos(a0) * r, Math.sin(a0) * r, side * 4.6]);
            var p1 = Rigs.point(wheel, [Math.cos(a1) * r, Math.sin(a1) * r, side * 4.6]);
            pen.rod(p0, p1, 0.6, '#e8e8e8', { m: 'metal' });
            pen.rod(Rigs.point(wheel, [0, 0, side * 4.6]), p0, 0.3, '#c8c8c8', { m: 'metal' });
            var lit = (k + Math.floor(t * 6)) % 3 !== 0;
            pen.part(frame(p0, 0), 'sph', [0, 0, 0], [0.9, 0.9, 0.9], lit ? colours[k % 6] : '#4a4a4a',
                     { m: lit ? 'neon' : '' });
          }
        }
        pen.part(wheel, 'cyl', [0, 0, 0], [4, 10, 4], '#c8c8c8', { m: 'metal', rx: Math.PI / 2 });
        for (var g = 0; g < n; g++) {
          var a = g / n * TAU + turn;
          var hang = [Math.cos(a) * r, Math.sin(a) * r, 0];
          var swing = Math.sin(t * 0.9 + g) * 0.08;
          var gf = child(f0, hang, swing, 0, 0);
          pen.part(gf, 'box', [0, -1.2, 0], [0.3, 2.4, 0.3], '#5a5f66');
          pen.part(gf, 'box', [0, -4.0, 0], [4.4, 3.2, 4.6], colours[g % 6]);
          pen.part(gf, 'box', [0, -2.2, 0], [4.8, 0.4, 5.0], '#f2ece0');
        }
      }
    };
  });

  /* The carousel: the canopy turning over the floor, horses rising and
     falling on their poles, the lights round the rim. */
  Rigs.register('fair_carousel', function (spec) {
    var f0 = frame(spec.p, 0);
    var r = spec.r || 12, n = spec.n || 10;
    var horses = ['#f2ece0', '#3a2a1a', '#c8a070', '#8a8a8a', '#e8e0cc'];
    return {
      radius: r + 10,
      draw: function (pen, t) {
        var turn = t * 0.35;
        var f = child(f0, [0, 0, 0], 0, turn, 0);
        pen.part(f, 'cone', [0, 17.0, 0], [r * 2.6, 5.0, r * 2.6], '#e83a3a');
        pen.part(f, 'cyl', [0, 14.4, 0], [r * 2.5, 0.8, r * 2.5], '#f2ece0');
        for (var k = 0; k < n; k++) {
          var a = k / n * TAU;
          var x = Math.cos(a) * (r - 2), z = Math.sin(a) * (r - 2);
          var up = Math.sin(t * 2 + k * 1.3) * 1.2;
          pen.part(f, 'cyl', [x, 7.4, z], [0.3, 13.4, 0.3], '#e8c83a', { m: 'metal' });
          var hf = child(f, [x, 3.6 + up, z], 0, -a, 0);
          var c = horses[k % horses.length];
          pen.part(hf, 'box', [0, 0, 0], [1.2, 1.4, 3.4], c);
          pen.part(hf, 'box', [0, 1.2, 1.6], [0.9, 2.0, 1.0], c, { rx: -0.4 });
          pen.part(hf, 'box', [0, 1.9, 2.3], [0.8, 0.8, 1.4], c);
          pen.part(hf, 'box', [0, 1.4, 1.1], [0.3, 1.6, 0.6], '#c43a32');
          pen.part(hf, 'box', [0, 0.85, 0], [1.3, 0.3, 1.4], '#3a7ac8');
          pen.part(hf, 'box', [0.4, -1.2, 1.2], [0.3, 1.4, 0.3], c, { rx: Math.sin(t * 2 + k) * 0.3 });
          pen.part(hf, 'box', [-0.4, -1.2, -1.2], [0.3, 1.4, 0.3], c, { rx: -Math.sin(t * 2 + k) * 0.3 });
          var lit = (k + Math.floor(t * 4)) % 2 === 0;
          pen.part(f, 'sph', [Math.cos(a + 0.3) * r * 1.25, 14.0, Math.sin(a + 0.3) * r * 1.25], [0.8, 0.8, 0.8],
                   lit ? '#fff2a8' : '#6a5a3a', { m: lit ? 'neon' : '' });
        }
      }
    };
  });

  /* The swing ride: the crown turning at the top of the mast, the chairs
     on their chains flying out with the speed. */
  Rigs.register('swing_ride', function (spec) {
    var f0 = frame(spec.p, 0);
    var n = spec.n || 10, r = spec.r || 9;
    return {
      radius: 40,
      draw: function (pen, t) {
        var speed = 0.6 + 0.4 * Math.sin(t * 0.15);
        var crown = child(f0, [0, 0, 0], 0, t * 1.1 * speed, 0);
        pen.part(crown, 'cyl', [0, 0, 0], [r * 2.2, 1.4, r * 2.2], '#3a7ac8');
        pen.part(crown, 'cone', [0, 2.6, 0], [r * 2.4, 3.6, r * 2.4], '#f2c83a');
        for (var k = 0; k < n; k++) {
          var a = k / n * TAU;
          var arm = child(crown, [Math.cos(a) * r, -0.7, Math.sin(a) * r], 0, -a, 0);
          var out = 0.25 + speed * 0.55;
          var chain = child(arm, [0, 0, 0], 0, 0, -out);
          var end = Rigs.point(chain, [0, -12, 0]);
          pen.rod(Rigs.point(arm, [0, 0, 0]), end, 0.12, '#8a8f94');
          var chair = frame(end, -a + Math.PI / 2);
          pen.part(chair, 'box', [0, -0.4, 0], [1.6, 0.4, 1.6], ['#e83a3a', '#f2c83a', '#5aa86a'][k % 3]);
          pen.part(chair, 'box', [0, 0.6, -0.7], [1.6, 1.6, 0.2], ['#e83a3a', '#f2c83a', '#5aa86a'][k % 3]);
        }
      }
    };
  });

  /* The duck shoot: tin ducks going along the back of the booth; a shot
     nearby knocks the nearest one flat, and it comes back up round the
     corner. */
  Rigs.register('duck_gallery', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    var w = spec.w || 14, n = 6;
    var down = [];
    for (var i = 0; i < n; i++) down.push(-10);
    return {
      radius: 30,
      event: function (kind, msg) {
        var from = msg && msg.from;
        if (kind !== 'shot' || !from || Math.hypot(from[0] - spec.p[0], from[2] - spec.p[2]) > 50) return;
        var t = Rigs.clock();
        var k = Math.floor(((t * 3) % n));
        down[k] = t;
      },
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var u = ((t * 0.25 + i / n) % 1);
          var x = -w / 2 + u * w;
          var flat = Math.min(1, Math.max(0, (t - down[i]) * 5)) * (t - down[i] < 3 ? 1 : 0);
          var d = child(f0, [x, 0, 0], -flat * 1.4, 0, 0);
          pen.part(d, 'box', [0, 0.9, 0], [1.6, 1.2, 0.2], '#f2c83a');
          pen.part(d, 'box', [0.7, 1.8, 0], [0.8, 0.8, 0.2], '#f2c83a');
          pen.part(d, 'box', [1.2, 1.7, 0], [0.4, 0.2, 0.2], '#e8783a');
        }
        pen.part(f0, 'box', [0, 0, 0], [w + 2, 0.4, 0.8], '#5a5f66');
      }
    };
  });

  /* The strength tester: a shot near it sends the puck up the pole, and
     a good one rings the bell at the top. */
  Rigs.register('strength_bell', function (spec) {
    var f0 = frame(spec.p, 0);
    var hit = -10, power = 0;
    return {
      radius: 30,
      event: function (kind, msg) {
        var from = msg && msg.from;
        if (kind === 'shot' && from && Math.hypot(from[0] - spec.p[0], from[2] - spec.p[2]) < 30) {
          hit = Rigs.clock();
          power = 0.5 + hash(Math.floor(hit * 10)) * 0.6;
        } else if (kind === 'roar') { hit = Rigs.clock(); power = 1.2; }
      },
      update: function (dt, t, ctx) {
        var u = t - hit;
        if (power >= 1 && u > 0.45 && u < 0.45 + dt * 1.5 && ctx.sound) ctx.sound('ll_ding', spec.p, 1);
      },
      draw: function (pen, t) {
        var u = t - hit;
        var h = u < 0 || u > 2 ? 0 : Math.max(0, Math.sin(Math.min(1, u / 0.9) * Math.PI)) * Math.min(1, power) * 19;
        pen.part(f0, 'box', [0, 2.6 + h, 0.7], [1.0, 1.0, 0.4], '#c8c8c8', { m: 'metal' });
        var ring = power >= 1 && u > 0.45 && u < 1.6;
        pen.part(f0, 'sph', [0, 23.2, 0], [2.6, 1.4, 2.6], ring ? '#fff2a8' : '#e8c83a', { m: ring ? 'neon' : 'metal' });
        for (var k = 0; k < 6; k++) {
          var lit = h > k * 3.2;
          pen.part(f0, 'box', [0, 4 + k * 3.2, 0.62], [0.8, 0.4, 0.1], lit ? '#ff5a3a' : '#5a2a2a', { m: lit ? 'neon' : '' });
        }
      }
    };
  });

  /* The prize bull in his pen: chewing, swishing, turning his head to
     whoever comes close, a snort and a stamp at the infected. */
  Rigs.register('prize_bull', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    var look = 0, last = 0;
    return {
      radius: 20,
      update: function (dt, t, ctx) {
        var near = nearest((ctx.players ? ctx.players() : []).concat(ctx.zombies ? ctx.zombies() : []), spec.p, 26);
        var target = near ? clamp(Math.atan2(near.who.pos[0] - spec.p[0], near.who.pos[2] - spec.p[2]) - (spec.yaw || 0), -1, 1) : Math.sin(t * 0.2) * 0.4;
        look = approachAngle(look, target, 2, dt);
        if (near && near.who.kind && t - last > 7) { last = t; if (ctx.sound) ctx.sound('ll_moo', spec.p, 1); }
      },
      draw: function (pen, t) {
        var c = '#3a2a1e';
        legsAt(pen, f0, [[-1.1, 2.2], [1.1, 2.2], [-1.1, -2.2], [1.1, -2.2]], 3.2, 1.0, c, 0, 0);
        var body = child(f0, [0, 4.6, 0], 0, 0, 0);
        pen.part(body, 'box', [0, 0, 0], [3.2, 3.0, 6.4], c);
        pen.part(body, 'box', [0, 1.4, 1.6], [3.0, 1.2, 2.6], '#4a3626');
        var tail = child(body, [0, 0.8, -3.2], 0.4, 0, Math.sin(t * 2.4) * 0.5);
        pen.part(tail, 'box', [0, -1.6, 0], [0.2, 3.2, 0.2], c);
        var head = child(body, [0, 0.6, 3.6], 0.1 + Math.sin(t * 3) * 0.04, look, 0);
        pen.part(head, 'box', [0, 0, 0.8], [2.0, 2.0, 2.2], c);
        pen.part(head, 'box', [0, -0.5, 2.0], [1.6, 1.0, 0.6], '#d8b8a0');
        pen.part(head, 'box', [0, -0.5, 2.36], [0.6, 0.2, 0.1], '#c8c8c8', { m: 'metal' });
        for (var s2 = -1; s2 <= 1; s2 += 2) {
          pen.part(head, 'box', [s2 * 1.4, 1.0, 0.6], [1.2, 0.4, 0.4], '#e8e0cc', { rz: s2 * 0.4 });
          pen.part(head, 'box', [s2 * 0.7, 0.4, 1.92], [0.2, 0.2, 0.1], '#0a0a0a');
        }
        // the blue ribbon on the pen
        pen.part(f0, 'box', [2.6, 3.4, 4.0], [0.1, 1.6, 0.8], '#3a5ae8');
      }
    };
  });

  Rigs.register('pigs', function (spec) {
    var a = spec.area, n = spec.n || 4;
    return {
      radius: 40,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var u = t * 0.08 + i * 1.7;
          var x = a[0] + (a[1] - a[0]) * (0.5 + 0.45 * Math.sin(u + i)), z = a[2] + (a[3] - a[2]) * (0.5 + 0.4 * Math.sin(u * 1.3 + i * 2));
          var yaw = Math.atan2(Math.cos(u + i) * (a[1] - a[0]), Math.cos(u * 1.3 + i * 2) * 1.3 * (a[3] - a[2]));
          var f = frame([x, spec.p[1], z], yaw);
          legsAt(pen, f, [[-0.5, 0.8], [0.5, 0.8], [-0.5, -0.8], [0.5, -0.8]], 0.8, 0.4, '#e8a0a0', t * 6, 0.3);
          pen.part(f, 'box', [0, 1.4, 0], [1.6, 1.3, 2.6], '#f2b0b0');
          pen.part(f, 'box', [0, 1.5, 1.5], [1.1, 1.0, 0.6], '#f2b0b0');
          pen.part(f, 'box', [0, 1.3, 1.85], [0.6, 0.4, 0.2], '#e88a8a');
          pen.part(f, 'box', [0, 1.9, -1.4], [0.2, 0.2, 0.4], '#e88a8a', { rx: Math.sin(t * 8 + i) });
        }
      }
    };
  });

  /* Chickens pecking about; a shot or the infected near them and they go
     everywhere, flapping. */
  Rigs.register('chickens', function (spec) {
    var a = spec.area, n = spec.n || 6;
    var birds = [];
    for (var i = 0; i < n; i++) birds.push({ x: a[0] + (a[1] - a[0]) * hash(i), z: a[2] + (a[3] - a[2]) * hash(i + 5), yaw: hash(i + 9) * TAU, panic: 0 });
    var scare = -10;
    return {
      radius: 50,
      event: function (kind) { if (kind === 'shot' || kind === 'blast') scare = Rigs.clock(); },
      update: function (dt, t, ctx) {
        var zs = ctx.zombies ? ctx.zombies() : [];
        for (var i = 0; i < birds.length; i++) {
          var c = birds[i];
          var near = nearest(zs, [c.x, 0, c.z], 10);
          var panic = t - scare < 3 || !!near;
          if (panic && c.panic < 0.5 && i === 0 && ctx.sound) ctx.sound('ll_cluck', [c.x, 0, c.z], 0.8);
          c.panic = approach(c.panic, panic ? 1 : 0, 4, dt);
          var speed = panic ? 9 : 0.6;
          var tx = a[0] + (a[1] - a[0]) * (0.5 + 0.48 * Math.sin(t * (panic ? 0.9 : 0.1) + i * 1.9));
          var tz = a[2] + (a[3] - a[2]) * (0.5 + 0.48 * Math.sin(t * (panic ? 1.1 : 0.13) + i * 2.7));
          var dx = tx - c.x, dz = tz - c.z, d = Math.hypot(dx, dz);
          if (d > 0.2) {
            c.x += dx / d * Math.min(d, speed * dt); c.z += dz / d * Math.min(d, speed * dt);
            c.yaw = approachAngle(c.yaw, Math.atan2(dx, dz), 6, dt);
          }
        }
      },
      draw: function (pen, t) {
        for (var i = 0; i < birds.length; i++) {
          var c = birds[i];
          var hop = c.panic * Math.abs(Math.sin(t * 9 + i)) * 0.8;
          var f = frame([c.x, spec.p[1] + hop, c.z], c.yaw);
          var peck = c.panic < 0.2 && Math.sin(t * 4 + i * 2) > 0.6 ? 0.9 : 0;
          pen.part(f, 'box', [0, 0.8, 0], [0.8, 0.8, 1.1], i % 3 ? '#f2ece0' : '#a8683a');
          pen.part(f, 'box', [0, 1.4 - peck * 0.5, 0.55 + peck * 0.2], [0.5, 0.6, 0.5], i % 3 ? '#f2ece0' : '#a8683a');
          pen.part(f, 'box', [0, 1.8 - peck * 0.5, 0.6 + peck * 0.2], [0.14, 0.3, 0.3], '#e83a3a');
          pen.part(f, 'box', [0, 1.35 - peck * 0.5, 0.86 + peck * 0.2], [0.16, 0.12, 0.2], '#e8a03a');
          var flap = c.panic * Math.sin(t * 22 + i) * 0.9;
          pen.part(child(f, [0.42, 0.9, 0], 0, 0, -flap), 'box', [0.2, 0, 0], [0.4, 0.5, 0.8], i % 3 ? '#e8e2d4' : '#8a5a2a');
          pen.part(child(f, [-0.42, 0.9, 0], 0, 0, flap), 'box', [-0.2, 0, 0], [0.4, 0.5, 0.8], i % 3 ? '#e8e2d4' : '#8a5a2a');
        }
      }
    };
  });

  /* The dark ride's scares: skeletons that spring up out of the dark as
     somebody passes, with a cackle, then sink back. */
  Rigs.register('haunt_popups', function (spec, ctx) {
    var spots = spec.spots_p || [spec.p];
    var up = [];
    for (var i = 0; i < spots.length; i++) up.push({ k: 0, at: -10 });
    return {
      radius: 80,
      update: function (dt, t, ctx2) {
        var ps = ctx2.players ? ctx2.players() : [];
        for (var i = 0; i < spots.length; i++) {
          var near = nearest(ps, spots[i], 9);
          if (near && t - up[i].at > 6) { up[i].at = t; if (ctx2.sound) ctx2.sound('ll_cackle', spots[i], 1); }
          up[i].k = approach(up[i].k, t - up[i].at < 2.5 ? 1 : 0, t - up[i].at < 2.5 ? 14 : 2, dt);
        }
      },
      draw: function (pen, t) {
        for (var i = 0; i < spots.length; i++) {
          if (up[i].k < 0.02) continue;
          var f = child(frame(spots[i], i * 1.3), [0, -6 + up[i].k * 6, 0], 0, 0, Math.sin(t * 6) * 0.1 * up[i].k);
          var bone = '#e8e0cc';
          pen.part(f, 'box', [0, 3.0, 0], [0.4, 3.0, 0.4], bone);
          for (var r = 0; r < 4; r++) pen.part(f, 'box', [0, 2.2 + r * 0.6, 0.1], [2.0 - r * 0.2, 0.2, 0.6], bone);
          pen.part(f, 'box', [0, 5.4, 0], [1.6, 1.6, 1.5], bone);
          pen.part(f, 'box', [0.36, 5.5, 0.76], [0.4, 0.4, 0.06], '#c8ff3a', { m: 'neon' });
          pen.part(f, 'box', [-0.36, 5.5, 0.76], [0.4, 0.4, 0.06], '#c8ff3a', { m: 'neon' });
          for (var s2 = -1; s2 <= 1; s2 += 2) {
            pen.part(child(f, [s2 * 1.2, 4.2, 0], -1.2 + Math.sin(t * 8 + s2) * 0.3, 0, s2 * 0.4), 'box', [0, -1.2, 0],
                     [0.3, 2.4, 0.3], bone);
          }
        }
      }
    };
  });

  /* A bunch of balloons tied to a booth, bobbing; a shot near them pops
     one, and another takes its place a while later. */
  Rigs.register('balloons', function (spec) {
    var n = spec.n || 6;
    var popped = [];
    for (var i = 0; i < n; i++) popped.push(-100);
    var colours = ['#e83a3a', '#3a7ac8', '#f2c83a', '#5aa86a', '#e890b0', '#9a6ae8'];
    return {
      radius: 20,
      event: function (kind, msg) {
        var from = msg && msg.from;
        if (kind === 'shot' && from && Math.hypot(from[0] - spec.p[0], from[2] - spec.p[2]) < 40) {
          var k = Math.floor(hash(Rigs.clock() * 3) * n);
          popped[k] = Rigs.clock();
        }
      },
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          if (t - popped[i] < 20) continue;
          var a = i / n * TAU;
          var top = [spec.p[0] + Math.cos(a) * 1.6 + Math.sin(t + i) * 0.5, spec.p[1] + 6 + (i % 3) * 1.2 + Math.sin(t * 1.3 + i) * 0.3,
                     spec.p[2] + Math.sin(a) * 1.6];
          pen.rod(spec.p, top, 0.05, '#e8e8e8');
          pen.part(frame(top, 0), 'sph', [0, 1.1, 0], [1.6, 2.0, 1.6], colours[i % 6]);
        }
      }
    };
  });

  /* The floodlights along the grandstand roof: on for the derby, flashing
     when the lure goes, a chase of bulbs along the edge. */
  Rigs.register('derby_lights', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    var w = spec.w || 160, show = -10;
    return {
      radius: w / 2 + 20,
      event: function (kind) { if (kind === 'lure') show = Rigs.clock() + 16; },
      draw: function (pen, t) {
        var on = t < show;
        for (var k = 0; k < 9; k++) {
          var x = -w / 2 + w * (k + 0.5) / 9;
          var flash = on ? (Math.sin(t * 10 + k) > 0 ? 1 : 0.2) : 0.7;
          pen.part(f0, 'box', [x, -0.6, 0], [4, 1.6, 1.6], '#2a2a2e');
          pen.part(f0, 'box', [x, -0.6, 0.82], [3.4, 1.2, 0.1], '#fff6d8', { m: 'neon', a: flash });
          if (on) pen.part(f0, 'cone', [x, -14, 18], [10, 34, 10], '#fff6d8', { m: 'neon', a: 0.05, rx: -2.3 });
        }
        for (var b2 = 0; b2 < 40; b2++) {
          var lit = (b2 + Math.floor(t * 8)) % 3 !== 0;
          pen.part(f0, 'sph', [-w / 2 + w * b2 / 39, -1.6, 0.4], [0.5, 0.5, 0.5], lit ? '#ff8a3a' : '#5a3a2a', { m: lit ? 'neon' : '' });
        }
      }
    };
  });

  /* The pig races: pigs in racing silks round the oval, each at its own
     pace and swapping the lead; a shot, the lure or a wave and they bolt,
     squealing. */
  Rigs.register('pig_race', function (spec) {
    var n = spec.n || 6, A = spec.a || 20, C = spec.c || 14;
    var silks = ['#e83a3a', '#3a7ac8', '#f2c83a', '#5aa86a', '#9a6ae8', '#f2ece0'];
    var pigs = [];
    for (var i = 0; i < n; i++) pigs.push({ u: -i * 0.22, v: 0.5 });
    var bolt = -10;
    function at(u) {
      var c = Math.cos(u), s = Math.sin(u);
      return [spec.p[0] + A * Math.sign(c) * Math.pow(Math.abs(c), 0.5), spec.p[2] + C * Math.sign(s) * Math.pow(Math.abs(s), 0.5)];
    }
    return {
      radius: 60,
      event: function (kind, msg) {
        var from = msg && msg.from;
        if (kind === 'lure' || kind === 'wave' || kind === 'blast' ||
            (kind === 'shot' && from && Math.hypot(from[0] - spec.p[0], from[2] - spec.p[2]) < 60)) bolt = Rigs.clock();
      },
      update: function (dt, t, ctx) {
        var fast = t - bolt < 5;
        if (fast && t - bolt < dt * 1.5 && ctx.sound) ctx.sound('ll_squeal', spec.p, 1);
        for (var i = 0; i < pigs.length; i++) {
          var pg = pigs[i];
          var want = (fast ? 1.5 : 0.42) * (1 + 0.25 * Math.sin(t * 0.37 + i * 2.1) + 0.1 * Math.sin(t * 1.3 + i));
          pg.v = approach(pg.v, want, 1.5, dt);
          pg.u += pg.v * dt * 0.33;
        }
      },
      draw: function (pen, t) {
        for (var i = 0; i < pigs.length; i++) {
          var pg = pigs[i];
          var p0 = at(pg.u), p1 = at(pg.u + 0.02);
          var yaw = Math.atan2(p1[0] - p0[0], p1[1] - p0[1]);
          var lane = (i % 3 - 1) * 2.2;
          var f = frame([p0[0] + Math.cos(yaw) * lane, spec.p[1], p0[1] - Math.sin(yaw) * lane], yaw);
          var gait = t * (6 + pg.v * 10) + i;
          var hop = Math.abs(Math.sin(gait)) * 0.25 * pg.v;
          var body = child(f, [0, hop, 0], 0, 0, 0);
          legsAt(pen, body, [[-0.5, 0.8], [0.5, 0.8], [-0.5, -0.8], [0.5, -0.8]], 0.8, 0.4, '#e8a0a0', gait, 0.5);
          pen.part(body, 'box', [0, 1.4, 0], [1.6, 1.3, 2.6], '#f2b0b0');
          pen.part(body, 'box', [0, 1.55, 1.5], [1.1, 1.0, 0.6], '#f2b0b0');
          pen.part(body, 'box', [0, 1.35, 1.86], [0.6, 0.4, 0.14], '#e88a8a');
          pen.part(body, 'box', [0.36, 2.1, 1.4], [0.3, 0.4, 0.2], '#e88a8a', { rx: -0.3 });
          pen.part(body, 'box', [-0.36, 2.1, 1.4], [0.3, 0.4, 0.2], '#e88a8a', { rx: -0.3 });
          pen.part(body, 'box', [0, 1.6, -0.1], [1.7, 1.0, 1.6], silks[i % silks.length]);
          pen.part(body, 'box', [0, 2.12, -0.1], [0.9, 0.06, 0.9], '#f2ece0',
                   { dec: textDecal(String(i + 1), '#f2ece0', '#1b1b1b', 1) });
          pen.part(body, 'box', [0, 1.8, -1.36], [0.16, 0.16, 0.3], '#e88a8a', { rx: Math.sin(t * 10 + i) * 0.6 });
        }
      }
    };
  });

  /* The occupied portable toilet: somebody is still in there.  Come close
     and they hammer on the door. */
  Rigs.register('porta_knock', function (spec) {
    var f0 = frame(spec.p, 0);
    var bang = -10, next = 0;
    return {
      radius: 30,
      update: function (dt, t, ctx) {
        var near = nearest(ctx.players ? ctx.players() : [], spec.p, 14);
        if (near && t > next) {
          bang = t; next = t + 3 + hash(Math.floor(t)) * 3;
          if (ctx.sound) ctx.sound('ll_knock', spec.p, 1);
        }
      },
      draw: function (pen, t) {
        var u = t - bang;
        var shake = u >= 0 && u < 0.5 ? Math.sin(u * 60) * (0.5 - u) * 0.12 : 0;
        var door = child(f0, [-1.5, 0.3, -0.22], 0, shake, 0);
        pen.part(door, 'box', [1.5, 3.3, 0], [3.0, 6.6, 0.2], '#2a5a98');
        pen.part(door, 'box', [1.5, 5.7, -0.15], [1.6, 0.5, 0.1], '#e83a3a',
                 { dec: textDecal('OCCUPIED', '#e83a3a', '#f2ece0', 3.2) });
        pen.part(door, 'box', [2.6, 3.2, -0.2], [0.3, 0.6, 0.2], '#c8c8c8', { m: 'metal' });
      }
    };
  });

  // ========================================== Redwater Cranberry Bogs
  if (GA) {
    GA.register('ll_floodgate', function (vol) {
      // the klaxon, the gate's screw groaning up, then the water
      for (var i = 0; i < 3; i++) {
        this.later(i * 420, function () {
          this.tone({ type: 'square', freq: 440, freqEnd: 330, dur: 0.36, gain: 0.07 * vol });
        });
      }
      this.later(1300, function () {
        this.tone({ type: 'sawtooth', freq: 70, freqEnd: 110, dur: 1.1, gain: 0.08 * vol });
        this.noise({ filter: 'bandpass', freq: 600, freqEnd: 900, dur: 1.1, gain: 0.05 * vol });
      });
      this.later(2300, function () { this.noise({ freq: 1400, freqEnd: 300, dur: 3.2, gain: 0.2 * vol }); });
      this.later(2400, function () { this.noise({ filter: 'lowpass', freq: 220, dur: 3.0, gain: 0.18 * vol }); });
    });
    GA.register('ll_heron', function (vol) {
      this.tone({ type: 'sawtooth', freq: 320, freqEnd: 190, dur: 0.42, gain: 0.07 * vol });
      this.noise({ filter: 'bandpass', freq: 900, freqEnd: 500, dur: 0.42, gain: 0.05 * vol });
    });
    GA.register('ll_plop', function (vol) {
      this.tone({ type: 'sine', freq: 700, freqEnd: 180, dur: 0.14, gain: 0.08 * vol });
      this.noise({ filter: 'bandpass', freq: 1200, dur: 0.1, gain: 0.03 * vol });
    });
    GA.register('ll_frog', function (vol) {
      for (var i = 0; i < 3; i++) {
        this.later(i * 140, function () { this.tone({ type: 'square', freq: 118, freqEnd: 96, dur: 0.11, gain: 0.05 * vol }); });
      }
    });
    GA.register('ll_chug', function (vol) {
      this.tone({ type: 'sine', freq: 62, freqEnd: 44, dur: 0.22, gain: 0.09 * vol });
      this.later(260, function () { this.noise({ freq: 500, freqEnd: 160, dur: 0.3, gain: 0.04 * vol }); });
    });
  }

  /* A water reel ("beater"): the reel at the front of its frame turning in
     the flooded bog, knocking the berries off the vines -- they fly up
     and patter back down -- with a foam wake behind. */
  Rigs.register('water_reel', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    var spray = [];
    for (var i = 0; i < 10; i++) spray.push({ ph: hash(i + 3), side: hash(i + 7) * 2 - 1 });
    return {
      radius: 30,
      draw: function (pen, t) {
        for (var sd = -1; sd <= 1; sd += 2) pen.part(f0, 'box', [1.1, 1.1, sd * 3.4], [2.6, 0.5, 0.5], '#c8a83a', { m: 'metal' });
        var axle = child(f0, [2.2, 1.1, 0], 0, 0, -t * 2.2);
        pen.part(axle, 'cyl', [0, 0, 0], [1.2, 6.8, 1.2], '#5a5f66', { m: 'metal', rx: Math.PI / 2 });
        for (var k = 0; k < 8; k++) {
          var arm = child(axle, [0, 0, 0], 0, 0, k / 8 * TAU);
          pen.part(arm, 'box', [1.2, 0, 3.0], [2.4, 0.25, 0.25], '#8a8f94', { m: 'metal' });
          pen.part(arm, 'box', [1.2, 0, -3.0], [2.4, 0.25, 0.25], '#8a8f94', { m: 'metal' });
          pen.part(arm, 'box', [2.4, 0, 0], [0.3, 0.9, 6.2], '#c8a83a', { m: 'metal' });
        }
        for (i = 0; i < spray.length; i++) {
          var sp = spray[i];
          var u = (t * 0.9 + sp.ph) % 1;
          pen.part(f0, 'sph', [3.0 + u * 4.0, 0.6 + u * 4.2 - u * u * 4.8, sp.side * 2.6], [0.5, 0.5, 0.5], '#c8243a');
        }
        for (var j = 0; j < 6; j++) {
          var w = (t * 0.5 + j / 6) % 1;
          pen.part(f0, 'cyl', [-2 - w * 10, 0.05, Math.sin(j * 2.3) * 2], [1.2 + w * 2.4, 0.06, 1.2 + w * 2.4], '#f2e8e8',
                   { a: 0.5 * (1 - w) });
        }
      }
    };
  });

  /* The corralled berries: clumps riding the surface inside the booms,
     drifting, and jostled when something disturbs the water. */
  Rigs.register('berry_raft', function (spec) {
    var a = spec.area, n = spec.n || 20, y = spec.p[1];
    var clumps = [];
    for (var i = 0; i < n; i++) {
      clumps.push({ x: a[0] + (a[1] - a[0]) * hash(i * 3 + 1), z: a[2] + (a[3] - a[2]) * hash(i * 5 + 2), p: hash(i + 11) * 6 });
    }
    var stir = -10;
    return {
      radius: Math.max(a[1] - a[0], a[3] - a[2]) / 2 + 20,
      event: function (kind, msg) {
        var from = msg && (msg.from || msg.pos);
        if (kind === 'lure' || ((kind === 'shot' || kind === 'blast' || kind === 'kill') && from &&
            from[0] > a[0] - 30 && from[0] < a[1] + 30 && from[2] > a[2] - 30 && from[2] < a[3] + 30)) stir = Rigs.clock();
      },
      draw: function (pen, t) {
        var k = Math.max(0, 1 - (t - stir) / 6);
        for (var i = 0; i < clumps.length; i++) {
          var c = clumps[i];
          var x = c.x + Math.sin(t * 0.07 + c.p) * 2.5 + Math.sin(t * 3 + c.p) * 0.4 * k;
          var z = c.z + Math.cos(t * 0.05 + c.p * 1.3) * 2.5;
          var bob = Math.sin(t * 1.4 + c.p) * 0.08 + k * Math.abs(Math.sin(t * 6 + c.p)) * 0.3;
          for (var j = 0; j < 4; j++) {
            pen.part(frame([x + (j % 2) * 0.7 - 0.35, y + 0.05 + bob, z + (j > 1 ? 0.6 : -0.3)], 0), 'sph', [0, 0, 0],
                     [0.6, 0.5, 0.6], j % 3 ? '#b81a2e' : '#d82a3a');
          }
        }
      }
    };
  });

  /* The floodgate: its handwheel spins when somebody opens it, the flume
     goes from a trickle to a torrent, and the water comes over the spout
     into the harvest bog in a white sheet, foam spreading out from it. */
  Rigs.register('floodgate', function (spec) {
    var wheel = frame(spec.p, 0);
    var x = spec.p[0], z0 = spec.z0, z1 = spec.z1, fy = spec.trough, pour = spec.pour;
    var len = Math.abs(z1 - z0), zm = (z0 + z1) / 2;
    var open = -100;
    return {
      radius: len + 50,
      event: function (kind) { if (kind === 'lure') open = Rigs.clock(); },
      draw: function (pen, t) {
        var u = t - open;
        var flow = u >= 0 && u < 18 ? Math.min(1, u / 1.5) * (u > 15 ? (18 - u) / 3 : 1) : 0;
        var wf = child(wheel, [0, 0, 0], 0, flow > 0 ? -u * 3 : 0, 0);
        for (var k = 0; k < 4; k++) {
          pen.part(child(wf, [0, 0, 0], 0, k * Math.PI / 4, 0), 'box', [0, 0.05, 0], [3.4, 0.2, 0.25], '#e8e8e8', { m: 'metal' });
        }
        pen.part(wf, 'box', [1.5, 0.5, 0], [0.3, 0.8, 0.3], '#1b1b1b');
        var depth = 0.25 + flow * 0.9;
        pen.part(frame([x, fy + depth / 2, zm], 0), 'box', [0, 0, 0], [4.6, depth, len - 0.2], '#8ab8d8', { a: 0.55 });
        for (var f = 0; f < 10; f++) {
          var v = (t * (0.25 + flow * 0.8) + f / 10) % 1;
          pen.part(frame([x + Math.sin(f * 2.1) * 1.4, fy + depth + 0.02, z1 - v * len], 0), 'box', [0, 0, 0], [1.2, 0.06, 0.8],
                   '#f2f6f8', { a: 0.7 });
        }
        var h = fy - pour, w = 1.2 + flow * 3.0;
        pen.part(frame([x, pour + h / 2, z0 - 0.3 - flow * 0.6], 0), 'box', [0, 0, 0], [w, h, 0.4 + flow * 0.8], '#cfe6f2',
                 { a: 0.4 + flow * 0.3 });
        for (var s2 = 0; s2 < 8; s2++) {
          var q = (t * 1.6 + s2 / 8) % 1, ang = s2 / 8 * TAU, rr = 0.5 + q * (2 + flow * 6);
          pen.part(frame([x + Math.cos(ang) * rr, pour + 0.1 + Math.sin(q * Math.PI) * (0.6 + flow * 1.6), z0 - 1 + Math.sin(ang) * rr], 0),
                   'sph', [0, 0, 0], [0.6, 0.6, 0.6], '#f2f6f8', { a: 0.7 * (1 - q) });
        }
        if (flow > 0) {
          for (var r2 = 0; r2 < 3; r2++) {
            var ring = (u * 0.4 + r2 / 3) % 1;
            pen.part(frame([x, pour + 0.03, z0 - 6], 0), 'cyl', [0, 0, 0], [6 + ring * 50, 0.05, 6 + ring * 50], '#f2e8e8',
                     { a: 0.25 * (1 - ring) * flow });
          }
        }
      }
    };
  });

  /* The frost sprinklers over the dry bog: off most of the time; a wave
     coming in (or every couple of minutes) and every head starts ticking
     round, throwing its jet in an arc. */
  Rigs.register('frost_sprinklers', function (spec) {
    var heads = spec.heads || [];
    var on = -100;
    return {
      radius: 150,
      event: function (kind) { if (kind === 'wave' || kind === 'lure') on = Rigs.clock(); },
      draw: function (pen, t) {
        var running = t - on < 25 || (t % 140) < 30;
        if (!running) return;
        for (var i = 0; i < heads.length; i++) {
          var hd = heads[i];
          var ang = Math.sin(t * 0.5 + i * 1.7) * 1.8 + i;
          var tick = Math.floor(t * 5) % 2 ? 0.08 : 0;
          var arm = frame(hd, ang + tick);
          pen.part(arm, 'box', [0, 0.25, 0.3], [0.2, 0.2, 0.9], '#c8a83a', { m: 'metal' });
          for (var k = 0; k < 7; k++) {
            var u = ((k + (t * 3) % 1) / 7);
            pen.part(arm, 'sph', [0, 0.3 + 5.2 * u * (1 - u), 0.5 + u * 9], [0.35, 0.35, 0.35], '#e8f4ff', { a: 0.55 * (1 - u * 0.5) });
          }
        }
      }
    };
  });

  /* The steam pump: the flywheel turning beside its bed, the crank and the
     rod going, the governor's balls flung out -- chuffing when somebody's
     near -- and smoke going up off the stack. */
  Rigs.register('pump_engine', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    var stack = spec.stack_p || spec.p;
    var last = 0;
    return {
      radius: 50,
      update: function (dt, t, ctx) {
        if (t - last > 1.6) {
          last = t;
          if (nearest(ctx.players ? ctx.players() : [], spec.p, 30) && ctx.sound) ctx.sound('ll_chug', spec.p, 0.7);
        }
      },
      draw: function (pen, t) {
        var a = t * 2.4;
        var fw = child(f0, [4.0, 1.6, 3.6], 0, 0, -a);
        for (var k = 0; k < 10; k++) {
          pen.part(child(fw, [0, 0, 0], 0, 0, k / 10 * TAU), 'box', [2.6, 0, 0], [0.5, 1.7, 0.8], '#3a3f46', { m: 'metal' });
        }
        for (var sp = 0; sp < 3; sp++) {
          pen.part(child(fw, [0, 0, 0], 0, 0, sp * Math.PI / 3), 'box', [0, 0, 0], [5.2, 0.3, 0.3], '#5a5f66', { m: 'metal' });
        }
        pen.part(fw, 'cyl', [0, 0, 0], [0.9, 1.2, 0.9], '#c8a83a', { m: 'metal', rx: Math.PI / 2 });
        var cx = Math.cos(a), cy = Math.sin(a);
        var piston = -2.4 + cx;
        pen.rod(Rigs.point(f0, [4.0 + cx, 1.6 + cy, 2.9]), Rigs.point(f0, [piston, 0.8, 2.9]), 0.3, '#c8c8c8', { m: 'metal' });
        pen.part(f0, 'box', [piston - 0.6, 0.8, 2.9], [1.2, 0.8, 0.8], '#8a8f94', { m: 'metal' });
        var gv = child(f0, [-1.0, 0.0, 0], 0, t * 4, 0);
        pen.part(gv, 'box', [0, 0.8, 0], [0.2, 1.6, 0.2], '#c8a83a', { m: 'metal' });
        for (var s2 = -1; s2 <= 1; s2 += 2) pen.part(gv, 'sph', [s2 * 0.9, 1.3, 0], [0.5, 0.5, 0.5], '#c8a83a', { m: 'metal' });
        for (var p2 = 0; p2 < 5; p2++) {
          var u = (t * 0.15 + p2 / 5) % 1, sz = 2 + u * 5;
          pen.part(frame([stack[0] + u * 6, stack[1] + 1 + u * 14, stack[2] + u * 2], 0), 'sph', [0, 0, 0], [sz, sz, sz], '#9a9a98',
                   { a: 0.35 * (1 - u) });
        }
      }
    };
  });

  /* The windmill's four sails, lattice and canvas, turning slowly on the
     west face. */
  Rigs.register('windmill_sails', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    var r = spec.r || 12;
    return {
      radius: r + 30,
      draw: function (pen, t) {
        pen.part(f0, 'cyl', [0, 0, 1.2], [1.6, 2.4, 1.6], '#3a2a1a', { rx: Math.PI / 2 });
        var hub = child(f0, [0, 0, 2.4], 0, 0, t * 0.45);
        pen.part(hub, 'box', [0, 0, 0], [1.6, 1.6, 0.8], '#4a3a2a');
        for (var k = 0; k < 4; k++) {
          var arm = child(hub, [0, 0, 0], 0, 0, k * Math.PI / 2);
          pen.part(arm, 'box', [r / 2, 0, 0], [r, 0.5, 0.5], '#4a3a2a');
          for (var b2 = 0; b2 < 5; b2++) pen.part(arm, 'box', [2.4 + b2 * (r - 3) / 4, 1.2, 0], [0.25, 2.4, 0.25], '#5a4a3a');
          pen.part(arm, 'box', [(r + 2.4) / 2, 2.4, 0], [r - 2.4, 0.25, 0.25], '#5a4a3a');
          pen.part(arm, 'box', [(r + 2.4) / 2, 1.2, -0.12], [r - 2.6, 2.2, 0.08], '#e8e0cc', { a: 0.85 });
        }
      }
    };
  });

  /* A great blue heron wading the west bog: stalking, stopping, now and
     then stabbing at the water; anybody close, or a shot, and it heaves
     itself up with a croak, flies over, and comes down somewhere else. */
  Rigs.register('heron', function (spec) {
    var a = spec.area, floor = spec.p[1];
    function pick(seed) { return [a[0] + (a[1] - a[0]) * hash(seed), a[2] + (a[3] - a[2]) * hash(seed + 7)]; }
    var st = { x: spec.p[0], z: spec.p[2], yaw: 0, tx: spec.p[0], tz: spec.p[2], next: 0, fly: -100,
               from: null, to: null, strike: -10, walking: false, alt: 0 };
    var scare = -100;
    return {
      radius: 140,
      event: function (kind, msg) {
        var from = msg && (msg.from || msg.pos);
        if ((kind === 'shot' || kind === 'blast' || kind === 'kill') && (!from || Math.hypot(from[0] - st.x, from[2] - st.z) < 70)) {
          scare = Rigs.clock();
        }
      },
      update: function (dt, t, ctx) {
        if (t - st.fly < 10) {
          var u = (t - st.fly) / 10, e = u * u * (3 - 2 * u);
          st.x = st.from[0] + (st.to[0] - st.from[0]) * e;
          st.z = st.from[1] + (st.to[1] - st.from[1]) * e;
          st.alt = Math.sin(u * Math.PI) * 30;
          st.yaw = approachAngle(st.yaw, Math.atan2(st.to[0] - st.from[0], st.to[1] - st.from[1]), 3, dt);
          return;
        }
        st.alt = 0;
        var ps = ctx.players ? ctx.players() : [], zs = ctx.zombies ? ctx.zombies() : [];
        if ((nearest(ps.concat(zs), [st.x, 0, st.z], 14) || t - scare < 0.5) && t - st.fly > 14) {
          st.fly = t; st.from = [st.x, st.z]; st.to = pick(Math.floor(t * 13));
          st.tx = st.to[0]; st.tz = st.to[1];
          if (ctx.sound) ctx.sound('ll_heron', [st.x, 0, st.z], 1);
          return;
        }
        if (t > st.next) { var p2 = pick(Math.floor(t * 3) + 1); st.tx = p2[0]; st.tz = p2[1]; st.next = t + 14 + hash(t) * 10; }
        var dx = st.tx - st.x, dz = st.tz - st.z, d = Math.hypot(dx, dz);
        st.walking = d > 0.5 && (t % 6) < 3.5;
        if (st.walking) {
          st.x += dx / d * 1.2 * dt; st.z += dz / d * 1.2 * dt;
          st.yaw = approachAngle(st.yaw, Math.atan2(dx, dz), 2, dt);
        } else if (Math.sin(t * 0.7) > 0.97 && t - st.strike > 4) st.strike = t;
      },
      draw: function (pen, t) {
        var grey = '#7a8aa0', dark = '#3a4250';
        var flying = st.alt > 0.2;
        var f = frame([st.x, floor + st.alt, st.z], st.yaw);
        if (flying) {
          var body = child(f, [0, 3.6, 0], 0, 0, 0);
          pen.part(body, 'box', [0, 0, 0], [1.0, 0.9, 2.4], grey);
          pen.part(body, 'box', [0, 0.2, 1.5], [0.5, 0.5, 0.9], grey);
          pen.part(body, 'box', [0, 0.3, 2.1], [0.4, 0.4, 0.5], '#e8e8ee');
          pen.part(body, 'box', [0, 0.25, 2.8], [0.14, 0.14, 1.0], '#e8c83a');
          pen.part(body, 'box', [0, -0.1, -2.6], [0.4, 0.2, 2.4], dark);
          var flap = Math.sin(t * 5) * 0.7;
          for (var sd = -1; sd <= 1; sd += 2) {
            var wing = child(body, [sd * 0.5, 0.3, 0.2], 0, 0, sd * flap);
            pen.part(wing, 'box', [sd * 2.4, 0, 0], [4.8, 0.12, 1.8], sd < 0 ? grey : '#6a7a90');
            pen.part(wing, 'box', [sd * 4.4, 0, -0.2], [1.2, 0.12, 1.4], dark);
          }
          return;
        }
        var stab = t - st.strike < 0.5 ? Math.sin((t - st.strike) / 0.5 * Math.PI) : 0;
        var step = st.walking ? Math.sin(t * 3) * 0.4 : 0;
        for (var lg = -1; lg <= 1; lg += 2) {
          var leg = child(f, [lg * 0.25, 3.3, 0], lg * step, 0, 0);
          pen.part(leg, 'box', [0, -1.65, 0], [0.16, 3.3, 0.16], '#6a5a3a');
        }
        var torso = child(f, [0, 3.8, 0], -0.25, 0, 0);
        pen.part(torso, 'box', [0, 0, 0], [1.0, 1.0, 2.2], grey);
        pen.part(torso, 'box', [0, -0.2, -1.4], [0.8, 0.6, 1.0], dark);
        var neck = child(torso, [0, 0.4, 0.9], -0.3 + stab * 1.3, 0, 0);
        pen.part(neck, 'box', [0, 0.9, 0], [0.32, 1.8, 0.32], '#c8ccd4');
        var head = child(neck, [0, 1.8, 0], 1.4 - stab * 0.3, 0, 0);
        pen.part(head, 'box', [0, 0.1, 0.2], [0.42, 0.42, 0.7], '#e8e8ee');
        pen.part(head, 'box', [0, 0.32, -0.3], [0.1, 0.1, 0.7], '#1a1a1a');
        pen.part(head, 'box', [0, 0.05, 1.05], [0.14, 0.14, 1.1], '#e8c83a');
        pen.part(head, 'box', [0.22, 0.2, 0.3], [0.04, 0.1, 0.1], '#e8c83a');
      }
    };
  });

  /* Out by the duck blind: come near, and a hand comes up out of the red
     water, grasping, and goes back under. */
  Rigs.register('bog_hand', function (spec) {
    var f0 = frame(spec.p, 0);
    var rise = -100, next = 0;
    var skin = '#6fae55';
    return {
      radius: 40,
      update: function (dt, t, ctx) {
        if (t > next && nearest(ctx.players ? ctx.players() : [], spec.p, 28)) {
          rise = t; next = t + 25 + hash(Math.floor(t)) * 20;
          if (ctx.sound) ctx.sound('ll_splash', spec.p, 0.8);
        }
      },
      draw: function (pen, t) {
        var u = t - rise;
        if (u < 0 || u > 6) return;
        var up = u < 1.5 ? 1 - Math.pow(1 - u / 1.5, 2) : (u < 4.2 ? 1 : Math.max(0, 1 - (u - 4.2) / 1.8));
        var arm = child(f0, [0, -3.0 + up * 4.2, 0], Math.sin(t * 3) * 0.15, 0, Math.sin(t * 2.2) * 0.12);
        pen.part(arm, 'box', [0, 0, 0], [0.9, 4.0, 0.9], skin);
        pen.part(arm, 'box', [0, -1.2, 0], [1.05, 1.4, 1.05], '#7a5230');
        pen.part(arm, 'box', [0, 2.3, 0], [1.3, 0.9, 0.5], skin);
        for (var g = 0; g < 4; g++) {
          var curl = u > 1.5 && u < 4.2 ? 0.4 + Math.sin(t * 6 + g) * 0.4 : 0.1;
          pen.part(child(arm, [-0.45 + g * 0.3, 2.75, 0], curl, 0, 0), 'box', [0, 0.45, 0], [0.2, 0.9, 0.24], skin);
        }
        pen.part(child(arm, [0.65, 2.2, 0], 0, 0, -0.8), 'box', [0, 0.35, 0], [0.22, 0.7, 0.24], skin);
        for (var r = 0; r < 2; r++) {
          var q = (u * 0.6 + r * 0.5) % 1;
          pen.part(f0, 'cyl', [0, 0.04, 0], [1.6 + q * 8, 0.04, 1.6 + q * 8], '#e8c8c8', { a: 0.35 * (1 - q) });
        }
      }
    };
  });

  /* Wooden duck decoys bobbing off the blind. */
  Rigs.register('decoys', function (spec) {
    var a = spec.area, n = spec.n || 5, y = spec.p[1];
    return {
      radius: 60,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var x = a[0] + (a[1] - a[0]) * hash(i * 3 + 2) + Math.sin(t * 0.1 + i) * 1.5;
          var z = a[2] + (a[3] - a[2]) * hash(i * 7 + 5) + Math.cos(t * 0.08 + i) * 1.5;
          var f = frame([x, y + Math.sin(t * 1.2 + i) * 0.05, z], i * 1.7 + Math.sin(t * 0.2 + i) * 0.6);
          pen.part(f, 'box', [0, 0.2, 0], [0.9, 0.6, 1.8], '#6a4a2a');
          pen.part(f, 'box', [0, 0.3, -0.85], [0.5, 0.3, 0.5], '#2a2a2a');
          pen.part(f, 'box', [0, 0.75, 0.7], [0.55, 0.55, 0.6], '#1a5a3a');
          pen.part(f, 'box', [0, 0.42, 0.7], [0.6, 0.12, 0.62], '#f2f2ee');
          pen.part(f, 'box', [0, 0.7, 1.15], [0.3, 0.16, 0.4], '#e8c83a');
        }
      }
    };
  });

  /* Frogs on the ditch banks: they croak while nobody's near, and when
     somebody comes along they hop into the ditch -- plop -- and come back
     a while later. */
  Rigs.register('frogs', function (spec) {
    var spots = spec.spots_p || [];
    var centre = spec.p;
    var st = spots.map(function (s0) {
      var dx = centre[0] - s0[0], dz = centre[2] - s0[2];
      var yaw = Math.abs(dx) < Math.abs(dz) ? (dx > 0 ? Math.PI / 2 : -Math.PI / 2) : (dz > 0 ? 0 : Math.PI);
      return { hop: -100, back: 0, yaw: yaw };
    });
    var croak = 0;
    return {
      radius: 130,
      update: function (dt, t, ctx) {
        var ps = ctx.players ? ctx.players() : [];
        for (var i = 0; i < spots.length; i++) {
          if (t < st[i].back) continue;
          if (nearest(ps, spots[i], 9)) {
            st[i].hop = t; st[i].back = t + 20;
            if (ctx.sound) ctx.sound('ll_plop', spots[i], 0.8);
          }
        }
        if (t > croak && spots.length) {
          croak = t + 3 + hash(Math.floor(t)) * 6;
          var k = Math.floor(hash(Math.floor(t * 7)) * spots.length);
          if (t > st[k].back && nearest(ps, spots[k], 70) && !nearest(ps, spots[k], 10) && ctx.sound) {
            ctx.sound('ll_frog', spots[k], 0.7);
            st[k].croakAt = t;
          }
        }
      },
      draw: function (pen, t) {
        for (var i = 0; i < spots.length; i++) {
          var s0 = spots[i], u = t - st[i].hop;
          if (u > 0.6 && t < st[i].back) continue;
          var h = 0, fwd = 0;
          if (u >= 0 && u <= 0.6) { var q = u / 0.6; h = Math.sin(q * Math.PI) * 1.4 - q * 1.6; fwd = q * 3.2; }
          var yaw = st[i].yaw;
          var f = frame([s0[0] + Math.sin(yaw) * fwd, s0[1] + h, s0[2] + Math.cos(yaw) * fwd], yaw);
          var puff = st[i].croakAt && t - st[i].croakAt < 0.5 ? Math.abs(Math.sin((t - st[i].croakAt) * 20)) : 0;
          pen.part(f, 'box', [0, 0.3, 0], [0.9, 0.5, 1.0], '#4a7a2a');
          pen.part(f, 'box', [0, 0.55, 0.35], [0.7, 0.35, 0.5], '#5a8a3a');
          pen.part(f, 'sph', [0.25, 0.8, 0.45], [0.25, 0.25, 0.25], '#e8c83a');
          pen.part(f, 'sph', [-0.25, 0.8, 0.45], [0.25, 0.25, 0.25], '#e8c83a');
          pen.part(f, 'sph', [0, 0.3, 0.6], [0.3 + puff * 0.4, 0.25 + puff * 0.35, 0.25 + puff * 0.2], '#e8e0a8');
          pen.part(f, 'box', [0.5, 0.15, -0.3], [0.3, 0.3, 0.7], '#4a7a2a');
          pen.part(f, 'box', [-0.5, 0.15, -0.3], [0.3, 0.3, 0.7], '#4a7a2a');
        }
      }
    };
  });

  /* A weathervane: the compass letters fixed, the arrow and its rooster
     swinging round with the wind. */
  Rigs.register('weathervane', function (spec) {
    var f0 = frame(spec.p, 0);
    var dir = 0;
    var letters = ['N', 'E', 'S', 'W'];
    return {
      radius: 30,
      update: function (dt, t) { dir = approachAngle(dir, Math.sin(t * 0.05) * 1.2 + Math.sin(t * 0.31) * 0.3, 0.6, dt); },
      draw: function (pen) {
        pen.part(f0, 'box', [0, 1.6, 0], [0.2, 3.2, 0.2], '#2a2a2a');
        for (var k = 0; k < 4; k++) {
          var arm = child(f0, [0, 1.4, 0], 0, k * Math.PI / 2, 0);
          pen.part(arm, 'box', [0, 0, 0.9], [0.1, 0.1, 1.8], '#2a2a2a');
          pen.part(arm, 'box', [0, 0, 1.9], [0.6, 0.6, 0.06], '#2a2a2a', { dec: textDecal(letters[k], '#2a2a2a', '#d8d8d8', 1) });
        }
        var v = child(f0, [0, 2.6, 0], 0, dir, 0);
        pen.part(v, 'box', [0, 0, 0], [0.12, 0.12, 3.2], '#2a2a2a');
        pen.part(v, 'box', [0, 0, 1.7], [0.1, 0.5, 0.5], '#2a2a2a', { rx: 0.785 });
        pen.part(v, 'box', [0, 0, -1.5], [0.08, 0.9, 0.7], '#2a2a2a');
        pen.part(v, 'box', [0, 0.7, -0.3], [0.1, 0.9, 1.3], '#2a2a2a');
        pen.part(v, 'box', [0, 1.3, 0.2], [0.1, 0.5, 0.4], '#2a2a2a');
        pen.part(v, 'box', [0, 1.65, 0.25], [0.1, 0.3, 0.2], '#a8282e');
        pen.part(v, 'box', [0, 1.0, -1.0], [0.1, 1.2, 0.5], '#2a2a2a', { rx: -0.4 });
      }
    };
  });

  /* Sheets on the farmhouse line, swinging in the wind. */
  Rigs.register('clothesline', function (spec) {
    var w = spec.w || 20, n = 5;
    var colours = ['#f2f2ee', '#8ab8d8', '#e8c8c8', '#f2f2ee', '#c8a83a'];
    return {
      radius: 40,
      draw: function (pen, t) {
        var cw = w / n - 0.6;
        for (var i = 0; i < n; i++) {
          var x = spec.p[0] - w / 2 + (i + 0.5) * w / n;
          var hang = child(frame([x, spec.p[1] - 0.2, spec.p[2]], 0), [0, 0, 0], Math.sin(t * 1.3 + i) * 0.25 + 0.1, 0, 0);
          pen.part(hang, 'box', [0, -1.8, 0], [cw, 3.6, 0.08], colours[i % colours.length]);
          pen.part(hang, 'box', [-cw / 2 + 0.3, 0.05, 0], [0.2, 0.4, 0.2], '#c8a070');
          pen.part(hang, 'box', [cw / 2 - 0.3, 0.05, 0], [0.2, 0.4, 0.2], '#c8a070');
        }
      }
    };
  });

  /* Festival bunting: strings of pennants between the poles, sagging,
     the pennants flapping. */
  Rigs.register('bunting', function (spec) {
    var poles = spec.poles || [], h = spec.h || 12;
    var colours = ['#c43a32', '#f2ece0', '#3a7ac8', '#e8c83a'];
    return {
      radius: 90,
      draw: function (pen, t) {
        for (var k = 0; k < poles.length; k++) {
          var a = poles[k], b2 = poles[(k + 1) % poles.length];
          var yaw = Math.atan2(b2[0] - a[0], b2[1] - a[1]);
          var last = null;
          for (var j = 0; j <= 8; j++) {
            var v = j / 8;
            var pt = [a[0] + (b2[0] - a[0]) * v, spec.p[1] + h - 0.3 - Math.sin(v * Math.PI) * 2.2, a[1] + (b2[1] - a[1]) * v];
            if (last) pen.rod(last, pt, 0.06, '#e8e8e8');
            last = pt;
          }
          for (var i = 0; i < 12; i++) {
            var u = (i + 0.5) / 12;
            var at = [a[0] + (b2[0] - a[0]) * u, spec.p[1] + h - 0.3 - Math.sin(u * Math.PI) * 2.2, a[1] + (b2[1] - a[1]) * u];
            var f = child(frame(at, yaw), [0, 0, 0], 0, 0, Math.sin(t * 3 + i + k) * 0.35);
            pen.part(f, 'box', [0, -0.7, 0], [0.1, 1.4, 1.0], colours[(i + k) % 4]);
          }
        }
      }
    };
  });

  // ================================================ Kettle Falls Mill
  if (GA) {
    GA.register('ll_whistle', function (vol) {
      // the mill whistle: a chord of steam, rising to pitch and holding
      [220, 277, 330].forEach(function (f, i) {
        this.tone({ type: 'sine', freq: f * 0.92, freqEnd: f, dur: 2.6, gain: (0.08 - i * 0.015) * vol });
      }, this);
      this.noise({ filter: 'bandpass', freq: 1600, dur: 2.6, gain: 0.05 * vol });
    });
    GA.register('ll_bell', function (vol) {
      [[440, 0.08, 2.6], [880, 0.04, 1.8], [1188, 0.03, 1.4], [220, 0.05, 3.0]].forEach(function (p) {
        this.tone({ type: 'sine', freq: p[0], dur: p[2], gain: p[1] * vol });
      }, this);
    });
    GA.register('ll_rush', function (vol) {
      this.noise({ filter: 'lowpass', freq: 700, dur: 2.7, gain: 0.07 * vol });
      this.noise({ filter: 'bandpass', freq: 2400, dur: 2.7, gain: 0.02 * vol });
    });
    GA.register('ll_loom', function (vol) {
      for (var i = 0; i < 8; i++) {
        this.later(i * 190, function () {
          this.noise({ filter: 'bandpass', freq: 1800, freqEnd: 900, dur: 0.06, gain: 0.08 * vol });
          this.tone({ type: 'square', freq: 140, freqEnd: 90, dur: 0.05, gain: 0.04 * vol });
        });
      }
    });
    GA.register('ll_meow', function (vol) {
      this.tone({ type: 'sawtooth', freq: 560, freqEnd: 860, dur: 0.22, gain: 0.04 * vol });
      this.later(200, function () { this.tone({ type: 'sawtooth', freq: 860, freqEnd: 480, dur: 0.32, gain: 0.04 * vol }); });
    });
    GA.register('ll_hiss', function (vol) {
      this.noise({ filter: 'highpass', freq: 3000, dur: 0.7, gain: 0.06 * vol });
    });
  }

  /* The overshot wheel: the flume's water coming off the spout onto its
     buckets, the wheel turning under the weight, water spilling off the
     descending side into the river. */
  Rigs.register('waterwheel', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    var r = spec.r || 6, spout = spec.spout_p || spec.p;
    return {
      radius: r + 40,
      draw: function (pen, t) {
        var w = child(f0, [0, 0, 0], 0, 0, -t * 0.55);
        for (var side = -1; side <= 1; side += 2) {
          for (var k = 0; k < 16; k++) {
            var a = k / 16 * TAU;
            pen.part(child(w, [0, 0, side * 2.3], 0, 0, a), 'box', [r, 0, 0], [0.5, r * 0.42, 0.4], '#5a4a3a');
          }
          for (var sp = 0; sp < 4; sp++) {
            pen.part(child(w, [0, 0, side * 2.3], 0, 0, sp * Math.PI / 4), 'box', [0, 0, 0], [2 * r - 0.6, 0.4, 0.3], '#4a3a2a');
          }
        }
        for (var bk = 0; bk < 16; bk++) {
          pen.part(child(w, [0, 0, 0], 0, 0, (bk + 0.5) / 16 * TAU), 'box', [r - 0.5, 0, 0], [1.0, 0.25, 4.4], '#6a5a42');
        }
        // the water: off the spout onto the wheel's top, off the far side
        var top = Rigs.point(f0, [-r * 0.45, r * 0.95, 0]);
        pen.rod(spout, top, 1.6, '#9ac8e0', { a: 0.55 });
        for (var d = 0; d < 6; d++) {
          var u = (t * 1.4 + d / 6) % 1;
          pen.part(frame([spec.p[0] - r * 0.9 - u * 0.6, spec.p[1] + r * 0.2 - u * (r * 1.3), spec.p[2] + Math.sin(d * 2.1) * 1.5], 0),
                   'sph', [0, 0, 0], [0.5, 1.0, 0.5], '#cfe6f2', { a: 0.6 });
        }
        for (var f = 0; f < 5; f++) {
          var q = (t * 1.1 + f / 5) % 1;
          pen.part(frame([spec.p[0] - r + q * 2, spec.p[1] - r + 0.4, spec.p[2] + Math.sin(f * 1.7) * 2], 0), 'cyl', [0, 0, 0],
                   [1 + q * 4, 0.08, 1 + q * 4], '#f2f6f8', { a: 0.5 * (1 - q) });
        }
      }
    };
  });

  /* The falls: the pond coming over the notch in a sheet, streaks running
     down it, white water and mist where it lands -- and its roar, for
     whoever's near. */
  Rigs.register('falls', function (spec) {
    var x = spec.p[0], y = spec.p[1], w = spec.w || 20, drop = spec.drop || 12;
    var cols = 8, last = -10;
    return {
      radius: 160,
      update: function (dt, t, ctx) {
        if (t - last > 2.5) {
          last = t;
          var near = nearest(ctx.players ? ctx.players() : [], spec.p, 140);
          if (near && ctx.sound) ctx.sound('ll_rush', spec.p, Math.max(0.2, 1 - near.d / 140));
        }
      },
      draw: function (pen, t) {
        for (var c = 0; c < cols; c++) {
          var z = spec.p[2] - w / 2 + (c + 0.5) * w / cols;
          var bow = 0.6 + Math.sin(c * 1.7) * 0.3;
          pen.part(frame([x + bow, y - drop / 2, z], 0), 'box', [0, 0, 0], [0.8, drop, w / cols + 0.05], '#b8d8e8', { a: 0.5 });
          for (var k = 0; k < 3; k++) {
            var u = (t * (1.2 + (c % 3) * 0.2) + k / 3 + c * 0.13) % 1;
            pen.part(frame([x + bow + 0.45, y - u * drop, z + Math.sin(c + k) * 0.8], 0), 'box', [0, 0, 0], [0.1, 1.8, 0.6],
                     '#f2f8fc', { a: 0.75 });
          }
        }
        pen.part(frame([x - 0.6, y + 0.15, spec.p[2]], 0), 'box', [0, 0, 0], [2.0, 0.3, w], '#cfe6f2', { a: 0.55 });
        for (var f = 0; f < 12; f++) {
          var q = (t * 0.8 + f / 12) % 1;
          var zz = spec.p[2] - w / 2 + ((f * 7) % 12 + 0.5) * w / 12;
          pen.part(frame([x + 2 + q * 8, y - drop + 0.3 + Math.sin(q * Math.PI) * 1.2, zz], 0), 'sph', [0, 0, 0],
                   [1.6 + q * 2, 1.2 + q, 1.6 + q * 2], '#f2f6f8', { a: 0.6 * (1 - q) });
        }
        for (var m = 0; m < 5; m++) {
          var v = (t * 0.12 + m / 5) % 1;
          pen.part(frame([x + 4 + v * 14, y - drop + 2 + v * 10, spec.p[2] + Math.sin(m * 2.3 + t * 0.2) * w * 0.4], 0),
                   'sph', [0, 0, 0], [6 + v * 8, 4 + v * 5, 6 + v * 8], '#eef4f8', { a: 0.14 * (1 - v) });
        }
      }
    };
  });

  /* The river below the falls: foam streaks and fallen leaves riding the
     current down the gorge. */
  Rigs.register('river_flow', function (spec) {
    var a = spec.area, n = spec.n || 30, y = spec.p[1];
    var leaf = ['#c8582a', '#d8a02a', '#a83a24', '#e8c84a'];
    return {
      radius: (a[1] - a[0]) / 2 + 40,
      draw: function (pen, t) {
        for (var i = 0; i < n; i++) {
          var speed = 6 + hash(i) * 5;
          var x = a[0] + ((hash(i + 3) * (a[1] - a[0]) + t * speed) % (a[1] - a[0]));
          var z = a[2] + (a[3] - a[2]) * hash(i + 9) + Math.sin(t * 0.7 + i) * 1.5;
          if (i % 3 === 0) {
            pen.part(frame([x, y + 0.04, z], Math.sin(t + i) * 2), 'box', [0, 0, 0], [0.9, 0.05, 0.6], leaf[i % 4]);
          } else {
            pen.part(frame([x, y + 0.03, z], 0), 'box', [0, 0, 0], [3.0 + hash(i + 5) * 3, 0.04, 0.5], '#e8f2f8', { a: 0.45 });
          }
        }
      }
    };
  });

  /* The belfry bell: it swings and rings when a wave comes on, and when
     one is beaten. */
  Rigs.register('mill_bell', function (spec) {
    var f0 = frame(spec.p, 0);
    var ring = -100, rings = 0;
    return {
      radius: 60,
      event: function (kind) { if (kind === 'wave' || kind === 'cleared') ring = Rigs.clock(); },
      update: function (dt, t, ctx) {
        var u = t - ring;
        var k = Math.floor(u / 1.6);
        if (u >= 0 && u < 4.8 && k >= rings) {
          rings = k + 1;
          if (ctx.sound) ctx.sound('ll_bell', spec.p, 1);
        }
        if (u > 5) rings = 0;
      },
      draw: function (pen, t) {
        var u = t - ring;
        var swing = u >= 0 && u < 6 ? Math.sin(u * TAU / 1.6) * 0.6 * Math.max(0, 1 - u / 6) : Math.sin(t * 0.4) * 0.02;
        pen.part(f0, 'box', [0, 1.4, 0], [5.0, 0.5, 0.5], '#4a3a2a');
        var bell = child(f0, [0, 1.2, 0], swing, 0, 0);
        pen.part(bell, 'cone', [0, -1.6, 0], [3.2, 3.0, 3.2], '#b8862a', { m: 'metal' });
        pen.part(bell, 'cyl', [0, -3.2, 0], [3.4, 0.4, 3.4], '#a8762a', { m: 'metal' });
        pen.part(child(bell, [0, -1.2, 0], -swing * 0.8, 0, 0), 'sph', [0, -2.0, 0], [0.6, 0.6, 0.6], '#3a3a3a');
      }
    };
  });

  /* The whistle on the boiler house roof: blown (the lure), it shrieks out a
     column of steam; the stack smokes all the while. */
  Rigs.register('whistle_steam', function (spec) {
    var stack = spec.stack_p || spec.p;
    var blow = -100;
    return {
      radius: 120,
      event: function (kind) { if (kind === 'lure') blow = Rigs.clock(); },
      draw: function (pen, t) {
        var u = t - blow;
        if (u >= 0 && u < 5) {
          for (var k = 0; k < 9; k++) {
            var q = (u * 1.4 + k / 9) % 1;
            var sz = 1.2 + q * 6;
            pen.part(frame([spec.p[0] + q * 3, spec.p[1] + 0.6 + q * 16, spec.p[2] + Math.sin(k) * q * 2], 0), 'sph', [0, 0, 0],
                     [sz, sz, sz], '#f2f2f2', { a: 0.5 * (1 - q) * Math.min(1, (5 - u) * 2) });
          }
        }
        for (var p2 = 0; p2 < 6; p2++) {
          var v = (t * 0.1 + p2 / 6) % 1, s2 = 3 + v * 8;
          pen.part(frame([stack[0] + v * 10, stack[1] + 1 + v * 22, stack[2] + v * 3], 0), 'sph', [0, 0, 0], [s2, s2, s2],
                   '#6a6866', { a: 0.4 * (1 - v) });
        }
      }
    };
  });

  /* One loom in the weave room still works: come near it and it starts up
     on its own -- the shuttle flying, the heddles going -- and stops. */
  Rigs.register('loom_ghost', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    var run = -100, next = 0;
    return {
      radius: 40,
      update: function (dt, t, ctx) {
        if (t > next && nearest(ctx.players ? ctx.players() : [], spec.p, 18)) {
          run = t; next = t + 14;
          if (ctx.sound) ctx.sound('ll_loom', spec.p, 1);
        }
      },
      draw: function (pen, t) {
        var on = t - run < 1.6;
        var ph = on ? (t - run) * 10 : 0;
        var shuttle = Math.sin(ph * 0.5) * 2.6;
        var heddle = on ? Math.sin(ph) * 0.4 : 0;
        pen.part(f0, 'box', [shuttle, 0.3, 0.4], [0.8, 0.3, 0.4], '#c8a83a');
        pen.part(f0, 'box', [0, 1.2 + heddle, -0.4], [5.4, 0.2, 0.2], '#8a8f94', { m: 'metal' });
        pen.part(f0, 'box', [0, 1.2 - heddle, 0.0], [5.4, 0.2, 0.2], '#8a8f94', { m: 'metal' });
        pen.part(f0, 'box', [0, 0.15, 0.9], [5.6, 0.1, 1.6], '#e8e0cc');
        var beat = on ? Math.max(0, Math.sin(ph * 2)) * 0.5 : 0;
        pen.part(f0, 'box', [0, 0.7, 1.2 - beat], [5.8, 0.9, 0.3], '#6a5a42');
      }
    };
  });

  /* The footbridge's cables: the main cables sagging between the towers,
     the hangers down to the rails, swaying a little in the wind. */
  Rigs.register('footbridge_cables', function (spec) {
    var x = spec.p[0], top = spec.p[1], half = (spec.w || 7) / 2, z0 = spec.z0, z1 = spec.z1, deck = spec.deck || 0;
    return {
      radius: Math.abs(z1 - z0) / 2 + 30,
      draw: function (pen, t) {
        var sway = Math.sin(t * 0.7) * 0.25;
        for (var side = -1; side <= 1; side += 2) {
          var last = null;
          for (var k = 0; k <= 12; k++) {
            var u = k / 12;
            var sag = Math.sin(u * Math.PI);
            var pt = [x + side * half + sway * sag, top - sag * (top - deck - 2.0), z0 + (z1 - z0) * u];
            if (last) pen.rod(last, pt, 0.18, '#3a3a3a');
            if (k > 0 && k < 12) pen.rod(pt, [x + side * (half - 0.9), deck + 1.6, pt[2]], 0.06, '#5a5a5a');
            last = pt;
          }
        }
      }
    };
  });

  /* The dyed cloth hung on the racks to dry: indigo, madder, weld, green,
     lifting and falling in the wind. */
  Rigs.register('cloth_racks', function (spec) {
    var w = spec.w || 40, rows = spec.rows || [spec.p[2]];
    var dyes = ['#2a3a8a', '#a8182a', '#d8a02a', '#3a7a2a', '#6a2a6a', '#2a6a8a'];
    return {
      radius: w / 2 + 30,
      draw: function (pen, t) {
        var n = Math.floor(w / 8);
        for (var r = 0; r < rows.length; r++) {
          for (var i = 0; i < n; i++) {
            var x = spec.p[0] - w / 2 + (i + 0.5) * w / n;
            var gust = Math.sin(t * 1.1 + i * 0.7 + r) * 0.3 + Math.sin(t * 2.7 + i) * 0.08;
            var c = child(frame([x, spec.p[1] - 0.2, rows[r]], 0), [0, 0, 0], gust, 0, 0);
            pen.part(c, 'box', [0, -3.4, 0], [w / n - 0.6, 6.8, 0.08], dyes[(i + r * 3) % dyes.length]);
          }
        }
      }
    };
  });

  /* The mill cat, on its crate by the counting house: watching whoever
     comes by, a meow for company, tail going -- and off like a shot when
     the infected come near, back later. */
  Rigs.register('mill_cat', function (spec) {
    var f0 = frame(spec.p, spec.yaw || 0);
    var look = 0, gone = -100, said = -100, hiss = -100;
    return {
      radius: 40,
      update: function (dt, t, ctx) {
        if (t - gone < 30) return;
        var zs = ctx.zombies ? ctx.zombies() : [], ps = ctx.players ? ctx.players() : [];
        var z = nearest(zs, spec.p, 16);
        if (z) {
          if (t - hiss > 3) { hiss = t; if (ctx.sound) ctx.sound('ll_hiss', spec.p, 1); }
          if (t - hiss > 0.8) gone = t;
          return;
        }
        var p = nearest(ps, spec.p, 24);
        var target = p ? clamp(Math.atan2(p.who.pos[0] - spec.p[0], p.who.pos[2] - spec.p[2]) - (spec.yaw || 0), -1.4, 1.4) : Math.sin(t * 0.3) * 0.5;
        look = approachAngle(look, target, 3, dt);
        if (p && p.d < 10 && t - said > 20) { said = t; if (ctx.sound) ctx.sound('ll_meow', spec.p, 0.8); }
      },
      draw: function (pen, t) {
        var u = t - gone;
        if (u >= 0 && u < 30) {
          if (u < 0.8) {
            var run = child(f0, [u * 12, Math.sin(u / 0.8 * Math.PI) * 2.0 - u * 3, 0], 0, Math.PI / 2, 0);
            pen.part(run, 'box', [0, 0.6, 0], [0.7, 0.6, 1.6], '#3a3a3a');
            pen.part(run, 'box', [0, 0.9, 0.9], [0.6, 0.6, 0.6], '#3a3a3a');
          }
          return;
        }
        var arch = t - hiss < 0.8 ? 0.4 : 0;
        var fur = '#3a3a3a', white = '#e8e8e8';
        pen.part(f0, 'box', [0, 0.55 + arch, -0.1], [0.9, 1.1, 1.3], fur);
        pen.part(f0, 'box', [0, 0.5, 0.5], [0.6, 0.7, 0.3], white);
        for (var s2 = -1; s2 <= 1; s2 += 2) pen.part(f0, 'box', [s2 * 0.25, 0.25, 0.55], [0.2, 0.5, 0.2], white);
        var head = child(f0, [0, 1.3 + arch, 0.35], 0, look, 0);
        pen.part(head, 'box', [0, 0.25, 0], [0.8, 0.6, 0.6], fur);
        pen.part(head, 'box', [0.25, 0.65, -0.05], [0.2, 0.3, 0.15], fur, { rz: -0.2 });
        pen.part(head, 'box', [-0.25, 0.65, -0.05], [0.2, 0.3, 0.15], fur, { rz: 0.2 });
        var blink = (t % 4.3) < 0.12 ? 0.02 : 0.12;
        pen.part(head, 'box', [0.18, 0.32, 0.31], [0.14, blink, 0.02], '#c8e83a', { m: 'neon' });
        pen.part(head, 'box', [-0.18, 0.32, 0.31], [0.14, blink, 0.02], '#c8e83a', { m: 'neon' });
        pen.part(head, 'box', [0, 0.18, 0.31], [0.12, 0.08, 0.02], '#e890a0');
        var tail = child(f0, [0, 0.3, -0.75], -0.4 - arch, Math.sin(t * 1.8) * 0.6, 0);
        pen.part(tail, 'box', [0, 0.2, -0.6], [0.2, 0.2, 1.3], fur);
        pen.part(child(tail, [0, 0.2, -1.2], -0.9, 0, 0), 'box', [0, 0, -0.35], [0.2, 0.2, 0.7], fur);
      }
    };
  });

  /* A rowboat loose on the millpond, drifting, its oars shipped, a lantern
     still lit in the stern. */
  Rigs.register('rowboat', function (spec) {
    var a = spec.area, y = spec.p[1];
    return {
      radius: 80,
      draw: function (pen, t) {
        var x = a[0] + (a[1] - a[0]) * (0.5 + 0.45 * Math.sin(t * 0.013));
        var z = a[2] + (a[3] - a[2]) * (0.5 + 0.4 * Math.sin(t * 0.017 + 1));
        var yaw = t * 0.02 + Math.sin(t * 0.1) * 0.3;
        var f = child(frame([x, y + Math.sin(t * 1.1) * 0.08, z], yaw), [0, 0, 0], Math.sin(t * 0.9) * 0.04, 0, Math.sin(t * 1.3) * 0.05);
        pen.part(f, 'box', [0, 0.1, 0], [3.2, 0.5, 8.0], '#6a4a2a');
        for (var s2 = -1; s2 <= 1; s2 += 2) pen.part(f, 'box', [s2 * 1.55, 0.7, 0], [0.2, 0.9, 7.6], '#7a5a3a');
        pen.part(f, 'box', [0, 0.7, 3.9], [3.0, 0.9, 0.2], '#7a5a3a');
        pen.part(f, 'box', [0, 0.7, -3.9], [2.4, 0.9, 0.2], '#7a5a3a');
        pen.part(f, 'box', [0, 0.6, 0.5], [3.0, 0.2, 0.8], '#8a6a4a');
        for (var o = -1; o <= 1; o += 2) pen.part(f, 'box', [o * 0.6, 0.9, 0.0], [0.2, 0.15, 6.0], '#a07a52', { ry: o * 0.06 });
        pen.part(f, 'box', [0, 0.9, -3.2], [0.5, 0.7, 0.5], '#2a2a2a');
        pen.part(f, 'box', [0, 0.95, -3.2], [0.36, 0.5, 0.36], '#ffcf7a', { m: 'neon' });
      }
    };
  });

  global.LastLightRigs = { nearest: nearest, heading: heading };
})(window);
