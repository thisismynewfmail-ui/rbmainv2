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

  global.LastLightRigs = { nearest: nearest, heading: heading };
})(window);
