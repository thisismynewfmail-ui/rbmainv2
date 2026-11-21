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

  global.LastLightRigs = { nearest: nearest, heading: heading };
})(window);
