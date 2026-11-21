/* Blackout Relay's living scenery: the rigs its maps name in
   markers.extra.rigs (static/js/game/rigs.js draws them; the plugin in
   blackout_relay.js feeds them the game).

   Thimble Acre
     garden_cat   Marmalade, the giant ginger tabby on the north fence.  She
                  watches whoever is nearest (head first, eyes ahead of it),
                  stalks a carried or dropped flag -- crouched, pupils wide,
                  bottom wiggling -- and pounces when somebody captures,
                  then purrs.  Gunfire near her flattens her ears and puffs
                  her tail.  Stand below her and she bats at you; stand still
                  in front of her and she tilts her head; look her in the eye
                  long enough and she slow-blinks back.  Left alone she
                  grooms, yawns, watches the butterflies and nods off.
     butterfly, bee, snail, goldfish, ladybird, sunflower
                  the rest of the garden, going about its business. */
(function (global) {
  'use strict';
  var Rigs = global.Rigs;
  if (!Rigs) return;
  var child = Rigs.child, point = Rigs.point, approach = Rigs.approach;
  var clamp = Rigs.clamp, hash = Rigs.hash, wander = Rigs.wander;
  var TAU = Math.PI * 2;

  var GA = global.GameAudio;
  if (GA) {
    GA.register('br_meow', function (vol) {
      this.tone({ type: 'triangle', freq: 560, freqEnd: 930, dur: 0.2, gain: 0.09 * vol });
      this.tone({ type: 'sine', freq: 1120, freqEnd: 1860, dur: 0.2, gain: 0.025 * vol });
      this.later(170, function () {
        this.tone({ type: 'triangle', freq: 930, freqEnd: 470, dur: 0.42, gain: 0.08 * vol });
        this.tone({ type: 'sine', freq: 1860, freqEnd: 940, dur: 0.4, gain: 0.02 * vol });
      });
    });
    GA.register('br_mrrp', function (vol) {
      this.tone({ type: 'triangle', freq: 640, freqEnd: 1080, dur: 0.1, gain: 0.07 * vol });
      this.later(90, function () {
        this.tone({ type: 'triangle', freq: 1020, freqEnd: 760, dur: 0.16, gain: 0.06 * vol });
      });
    });
    GA.register('br_purr', function (vol) {
      for (var i = 0; i < 14; i++) {
        this.later(i * 62, function () {
          this.noise({ filter: 'lowpass', freq: 220, freqEnd: 140, dur: 0.07, gain: 0.07 * vol });
        });
      }
      this.tone({ type: 'sawtooth', freq: 26, dur: 0.9, gain: 0.025 * vol });
    });
    GA.register('br_chirp', function (vol) {
      // the chatter a cat makes at a bird it cannot reach
      for (var i = 0; i < 4; i++) {
        this.later(i * 85, function () {
          this.tone({ type: 'square', freq: 1500, freqEnd: 1250, dur: 0.05, gain: 0.025 * vol });
        });
      }
    });
    GA.register('br_hiss', function (vol) {
      this.noise({ filter: 'highpass', freq: 3200, freqEnd: 2400, dur: 0.55, gain: 0.08 * vol });
    });
    GA.register('br_bell', function (vol) {
      [2650, 3980, 3120].forEach(function (f, i) {
        this.later(i * 70, function () { this.tone({ type: 'sine', freq: f, dur: 0.35, gain: 0.025 * vol }); });
      }, this);
    });
    GA.register('br_buzz', function (vol) {
      this.tone({ type: 'sawtooth', freq: 180, freqEnd: 205, dur: 0.6, gain: 0.018 * vol });
      this.tone({ type: 'sawtooth', freq: 362, freqEnd: 350, dur: 0.6, gain: 0.008 * vol });
    });
    GA.register('br_splash', function (vol) {
      this.noise({ filter: 'bandpass', freq: 900, freqEnd: 300, dur: 0.4, gain: 0.08 * vol });
      this.later(60, function () { this.noise({ filter: 'highpass', freq: 2600, dur: 0.25, gain: 0.04 * vol }); });
    });
  }

  function dist(a, b) {
    return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  }

  /* A heart: two lobes and a point, for a happy cat. */
  function heart(pen, at, size, alpha) {
    var f = Rigs.frame(at, 0, size);
    var o = { a: alpha };
    pen.part(f, 'sph', [-0.55, 0.3, 0], [1.25, 1.25, 0.7], '#ff5f8f', o);
    pen.part(f, 'sph', [0.55, 0.3, 0], [1.25, 1.25, 0.7], '#ff5f8f', o);
    pen.part(f, 'cone', [0, -0.55, 0], [1.75, 1.3, 0.7], '#ff5f8f', { a: alpha, rx: Math.PI });
  }

  /* A Z, three bars, for a sleeping one. */
  function zed(pen, at, size, alpha) {
    var f = Rigs.frame(at, 0, size);
    var o = { a: alpha };
    pen.part(f, 'box', [0, 0.5, 0], [1.1, 0.22, 0.2], '#e8f0ff', o);
    pen.part(f, 'box', [0, -0.5, 0], [1.1, 0.22, 0.2], '#e8f0ff', o);
    pen.part(f, 'box', [0, 0, 0], [1.25, 0.22, 0.2], '#e8f0ff', { a: alpha, rz: 0.75 });
  }

  // ========================================================= Marmalade
  var GINGER = '#f2a446', GINGER_DARK = '#d27a2c', STRIPE = '#c2601e', CREAM = '#fcf3e3';
  var PINK = '#f59cb0', BEAN = '#f07c98', IRIS = '#a6d84a', PUPIL = '#15151d', BLUSH = '#ff9fb2';
  var COLLAR = '#e0344a', BELL = '#f2c84a';

  Rigs.register('garden_cat', function (spec, ctx) {
    var S = spec.s || 1;
    var root = Rigs.frame(spec.p, spec.yaw || 0, S);
    var headAt = point(root, [0, 58, 6]);
    var base = root.p;
    var seed = spec.seed || 3;
    var s = {
      headYaw: 0, headPitch: 0.3, headRoll: 0, bodyYaw: 0, eyeX: 0, eyeY: 0,
      pupil: 0.35, lid: 0, flat: 0, mouth: 0, tongue: 0, pawL: 0, pawR: 0, reachL: 0,
      reachR: 0, crouch: 0, rear: 0, hop: 0, puff: 1, tailAmp: 4, tailRate: 1.6, twitchTip: 0,
      happy: 0, sleep: 0, alone: 0, blinkAt: 0, act: null, plan: null, slot: -1,
      meowCool: 0, startleCool: 0, batCool: 0, tiltCool: 0, tiltSide: 1, chirpCool: 0,
      zone: 0, still: 0, gazedAt: 0, lastLook: null, earTwitch: [0, 0], hearts: [],
      watched: null, wasPrey: false
    };

    function say(name, vol) {
      if (ctx.sound) ctx.sound(name, headAt, vol || 1);
    }

    function start(kind, t, dur, extra) {
      s.act = { kind: kind, t0: t, dur: dur };
      if (extra) for (var k in extra) s.act[k] = extra[k];
    }

    function prey() {
      var spots = ctx.flagSpots ? ctx.flagSpots() : [];
      var best = null;
      for (var i = 0; i < spots.length; i++) {
        var f = spots[i];
        if (f.state === 'home' || !f.pos) continue;
        var d = dist(f.pos, headAt);
        if (d < 520 && (!best || d < best.d)) best = { pos: f.pos, d: d };
      }
      return best;
    }

    function nearest(people) {
      var best = null;
      for (var i = 0; i < people.length; i++) {
        var d = dist(people[i].pos, base);
        if (!best || d < best.d) best = { p: people[i], d: d };
      }
      return best;
    }

    function update(dt, t) {
      dt = Math.min(dt, 0.1);
      var people = ctx.players ? ctx.players() : [];
      var near = nearest(people);
      var hunt = prey();
      if (near && near.d < 260) s.alone = 0; else s.alone += dt;
      var act = s.act && t < s.act.t0 + s.act.dur ? s.act : null;
      if (s.act && !act) {
        var next = s.act.then;
        s.act = null;
        if (next === 'happy') { start('happy', t, 5.5); act = s.act; say('br_purr', 1); }
      }
      if (hunt && !s.wasPrey) { say('br_mrrp', 1); s.earTwitch = [t, t + 0.1]; }
      s.wasPrey = !!hunt;

      // the idle things she does, picked by the clock so every screen agrees
      if (!act && !hunt && s.alone > 6) {
        var slot = Math.floor(t / 17);
        if (slot !== s.slot) {
          s.slot = slot;
          var h = hash(slot * 7.31 + seed);
          var when = slot * 17 + 2 + h * 6;
          s.plan = h < 0.32 ? { kind: 'yawn', t0: when, dur: 2.6 } :
            (h < 0.72 ? { kind: 'groom', t0: when, dur: 7.0 } : null);
        }
        if (s.plan && t >= s.plan.t0 && t < s.plan.t0 + s.plan.dur && s.alone < 40) {
          s.act = act = s.plan;
          s.plan = null;
        }
      }
      var napping = !hunt && !act && s.alone > 40;

      // a person below her, by the fence: bat at them
      var local = null;
      if (near) {
        local = Rigs.local(root, [near.p.pos[0] - root.p[0], near.p.pos[1] - root.p[1],
                                  near.p.pos[2] - root.p[2]]);
        var inZone = local[2] > 4 * S && local[2] < 64 * S && Math.abs(local[0]) < 46 * S &&
          local[1] < 6 * S;
        s.zone = inZone ? s.zone + dt : 0;
        var moved = s.lastLook ? dist(s.lastLook, near.p.pos) / Math.max(dt, 1e-3) : 0;
        s.lastLook = near.p.pos.slice();
        s.still = (near.d < 120 * S && moved < 4) ? s.still + dt : 0;
        if (!act && !hunt && s.zone > 1.1 && t > s.batCool) {
          start('bat', t, 2.3, { side: local[0] >= 0 ? 1 : -1 });
          act = s.act;
          s.batCool = t + 6;
          say('br_mrrp', 0.8);
          say('br_bell', 0.8);
        }
        if (!act && near.d < 105 * S && t > s.meowCool && s.alone === 0 && !hunt) {
          start('meow', t, 0.9);
          act = s.act;
          s.meowCool = t + 11 + hash(t) * 6;
          say('br_meow', 1);
        }
      } else {
        s.zone = 0;
        s.still = 0;
      }

      // looked at, long and close: the slow blink
      var me = ctx.viewer ? ctx.viewer() : null;
      if (me && !act && !hunt) {
        var to = [headAt[0] - me.eye[0], headAt[1] - me.eye[1], headAt[2] - me.eye[2]];
        var d = Math.hypot(to[0], to[1], to[2]);
        var dot = d > 1 ? (to[0] * me.dir[0] + to[1] * me.dir[1] + to[2] * me.dir[2]) / d : 0;
        s.gazedAt = (d < 170 * S && dot > 0.965) ? s.gazedAt + dt : 0;
        if (s.gazedAt > 1.6) {
          start('slowblink', t, 2.2);
          act = s.act;
          s.gazedAt = -6;
          say('br_purr', 0.7);
          s.hearts.push({ t0: t + 0.9, x: 0 });
        }
      }

      // ---------------------------------------- where she is looking
      var look = null, kind = act ? act.kind : '';
      if (kind === 'groom') {
        look = null;
      } else if (hunt) {
        look = hunt.pos;
      } else if (near && near.d < 320 * S) {
        look = [near.p.pos[0], near.p.pos[1] + 3, near.p.pos[2]];
      } else if (ctx.critters) {
        var bestB = null, bd = 0;
        for (var i = 0; i < ctx.critters.length; i++) {
          var c = ctx.critters[i];
          if (c.kind !== 'butterfly') continue;
          var dc = dist(c.at, headAt);
          if (dc < 260 * S && (!bestB || dc < bd)) { bestB = c; bd = dc; }
        }
        if (bestB) look = bestB.at;
      }
      s.watched = look;
      var yawT = 0, pitchT = 0.32;
      if (look) {
        var dir = Rigs.local(root, [look[0] - headAt[0], look[1] - headAt[1], look[2] - headAt[2]]);
        yawT = clamp(Math.atan2(dir[0], Math.max(dir[2], 1)), -1.05, 1.05);
        pitchT = clamp(Math.atan2(-dir[1], Math.hypot(dir[0], dir[2])), -0.4, 0.78);
      } else if (kind !== 'groom') {
        yawT = 0.7 * Math.sin(t * 0.21 + seed);
        pitchT = 0.28 + 0.12 * Math.sin(t * 0.37);
      }
      var rollT = 0;

      // ------------------------------------------ the pose targets
      var crouchT = hunt ? 1 : 0, rearT = 0, hopT = 0, flatT = 0, pupilT = 0.32;
      var lidT = 0, mouthT = 0, tongueT = 0, pawLT = 0, pawRT = 0, reachLT = 0, reachRT = 0;
      var puffT = 1, ampT = 4, rateT = 1.6, tipT = 0, happyT = 0, sleepT = 0;
      if (hunt) { pupilT = 1; ampT = 1.5; rateT = 1.2; tipT = 1; }
      if (near && near.d < 130 * S) pupilT = Math.max(pupilT, 0.55);
      if (s.still > 2.2 && !hunt && !act && t > s.tiltCool) {
        start('tilt', t, 2.4, { side: s.tiltSide });
        act = s.act; kind = 'tilt';
        s.tiltSide = -s.tiltSide;
        s.tiltCool = t + 7;
        say('br_mrrp', 0.6);
      }
      var k = act ? (t - act.t0) / act.dur : 0;
      if (kind === 'pounce') {
        var up = k < 0.38 ? k / 0.38 : (k < 0.55 ? 1 - (k - 0.38) / 0.17 : 0);
        rearT = up;
        pawLT = pawRT = up > 0.05 ? 1.35 * up : 0;
        if (k >= 0.55 && !act.slammed) { act.slammed = true; say('br_bell', 1); }
        pupilT = 1; crouchT = 0; ampT = 7; rateT = 4;
      } else if (kind === 'happy') {
        happyT = 1; lidT = 1; ampT = 6; rateT = 1.1; pitchT -= 0.12;
        rollT = 0.14 * Math.sin((t - act.t0) * 1.6);
        if (!act.hearts || act.hearts < 5) {
          var due = Math.floor((t - act.t0) / 0.7);
          if ((act.hearts || 0) <= due) {
            act.hearts = (act.hearts || 0) + 1;
            s.hearts.push({ t0: t, x: (hash(t * 3.1) - 0.5) * 22 });
          }
        }
      } else if (kind === 'startle') {
        flatT = 1; pupilT = 1; puffT = 1.75; ampT = 0.6; rateT = 0.5;
        hopT = k < 0.25 ? Math.sin(k / 0.25 * Math.PI) : 0;
        mouthT = k < 0.5 ? 0.55 : 0;
      } else if (kind === 'bat') {
        var side = act.side;
        var swat = 1.15 + 0.5 * Math.sin((t - act.t0) * 12.5);
        var env = Math.min(1, k * 5, (1 - k) * 5);
        if (side > 0) { pawLT = swat * env; reachLT = env; } else { pawRT = swat * env; reachRT = env; }
        pupilT = 1; crouchT = 0.35; tipT = 1;
        if (local) yawT = clamp(Math.atan2(local[0], Math.max(local[2], 1)), -1.0, 1.0);
        pitchT = 0.7;
      } else if (kind === 'meow') {
        mouthT = Math.sin(Math.min(1, k * 1.15) * Math.PI) * 0.8;
        pitchT -= 0.12;
      } else if (kind === 'tilt') {
        rollT = act.side * 0.34 * Math.min(1, k * 4, (1 - k) * 4);
        pupilT = Math.max(pupilT, 0.7);
      } else if (kind === 'yawn') {
        var o = k < 0.3 ? k / 0.3 : (k < 0.75 ? 1 : 1 - (k - 0.75) / 0.25);
        mouthT = o; lidT = 0.85 * o; pitchT = 0.05 - 0.3 * o; flatT = 0.25 * o;
        tongueT = o > 0.6 ? 1 : 0;
      } else if (kind === 'groom') {
        var lick = k < 0.62;
        pawRT = lick ? 2.62 : 2.95;
        reachRT = lick ? 1 : 0.4;
        pitchT = lick ? 0.66 : 0.25;
        yawT = lick ? -0.2 : -0.35;
        rollT = lick ? 0 : -0.38;
        lidT = 0.6;
        if (lick) {
          mouthT = 0.3;
          tongueT = Math.sin((t - act.t0) * 9.5) > 0.2 ? 1 : 0;
        } else {
          flatT = 0.5;
        }
      } else if (kind === 'slowblink') {
        lidT = k > 0.15 && k < 0.75 ? 1 : 0;
        happyT = 0.6;
      }
      if (napping) {
        sleepT = 1; lidT = 1; pitchT = 0.62; yawT = 0.12; flatT = 0.3; ampT = 0.8; rateT = 0.5;
        pupilT = 0.2;
      }

      // ears flick now and then (and toward a shot)
      for (var e = 0; e < 2; e++) {
        if (t > s.earTwitch[e] + 0.25 && hash(Math.floor(t * 1.3) * 3.7 + e * 11 + seed) < 0.012) {
          s.earTwitch[e] = t;
        }
      }

      // blinking
      if (t > s.blinkAt + 0.16 && hash(Math.floor(t * 2) + seed * 9.7) < 0.06 && !napping) s.blinkAt = t;
      if (t - s.blinkAt < 0.14) lidT = Math.max(lidT, 1);

      // ease everything toward its target
      s.headYaw = Rigs.approachAngle(s.headYaw, yawT, hunt ? 6 : 3.2, dt);
      s.headPitch = approach(s.headPitch, pitchT, 3.2, dt);
      s.headRoll = approach(s.headRoll, rollT, 4, dt);
      s.bodyYaw = approach(s.bodyYaw, yawT * 0.22, 1.5, dt);
      var resid = clamp((yawT - s.headYaw) * 3.2, -1, 1);
      s.eyeX = approach(s.eyeX, resid * 1.1, 12, dt);
      s.eyeY = approach(s.eyeY, clamp(-(pitchT - s.headPitch) * 3, -1, 1) * 0.9, 12, dt);
      s.pupil = approach(s.pupil, pupilT, 5, dt);
      s.lid = approach(s.lid, lidT, lidT > s.lid ? 26 : 9, dt);
      s.flat = approach(s.flat, flatT, 9, dt);
      s.mouth = approach(s.mouth, mouthT, 14, dt);
      s.tongue = approach(s.tongue, tongueT, 20, dt);
      s.pawL = approach(s.pawL, pawLT, 14, dt);
      s.pawR = approach(s.pawR, pawRT, 14, dt);
      s.reachL = approach(s.reachL, reachLT, 10, dt);
      s.reachR = approach(s.reachR, reachRT, 10, dt);
      s.crouch = approach(s.crouch, crouchT, 4, dt);
      s.rear = approach(s.rear, rearT, 16, dt);
      s.hop = approach(s.hop, hopT, 22, dt);
      s.puff = approach(s.puff, puffT, puffT > s.puff ? 18 : 1.6, dt);
      s.tailAmp = approach(s.tailAmp, ampT, 2, dt);
      s.tailRate = approach(s.tailRate, rateT, 2, dt);
      s.twitchTip = approach(s.twitchTip, tipT, 4, dt);
      s.happy = approach(s.happy, happyT, 3, dt);
      s.sleep = approach(s.sleep, sleepT, 0.8, dt);
      s.hearts = s.hearts.filter(function (hh) { return t - hh.t0 < 2.6; });
    }

    // ------------------------------------------------------------ draw
    function draw(pen, t) {
      var near = pen.near;
      var breathe = 1 + Math.sin(t * (s.sleep > 0.5 ? 1.2 : 1.9)) * (0.012 + 0.02 * s.sleep);
      var wig = Math.sin(t * 10.5) * s.crouch;
      var body = child(root, [wig * 1.4, -3.5 * s.crouch + 9 * s.rear + 3.5 * s.hop, 0],
                       0.17 * s.crouch - 0.26 * s.rear, s.bodyYaw + wig * 0.05, wig * 0.06);
      // haunches, the chest, the bib
      pen.part(body, 'sph', [0, 12.5 * breathe, -2.5], [37, 27 * breathe, 31], GINGER);
      pen.part(body, 'sph', [0, 28.5, 3], [28, 34 * breathe, 24], GINGER);
      pen.part(body, 'sph', [0, 27.5, 11.6], [16, 25, 5.2], CREAM);
      pen.part(body, 'sph', [0, 36.5, 9.8], [14, 11, 6], CREAM);
      if (near) {
        // tabby bands over the back and the haunches
        for (var b = 0; b < 3; b++) {
          pen.part(body, 'box', [0, 18 + b * 7.5, -13.2 + b * 0.8], [17 - b * 2, 2.2, 1.0], STRIPE,
                   { rx: -0.25 });
        }
        for (var sx = -1; sx <= 1; sx += 2) {
          pen.part(body, 'box', [sx * 17.6, 12, -3], [1.0, 2.4, 11], STRIPE, { ry: sx * 0.2 });
          pen.part(body, 'box', [sx * 16.4, 17.5, -5], [1.0, 2.0, 8], STRIPE, { ry: sx * 0.25 });
        }
      }
      // the hind feet, peeping out each side
      for (var hs = -1; hs <= 1; hs += 2) {
        pen.part(root, 'rbox', [hs * 15, 2.1, 6.5], [8, 4.2, 11], CREAM);
      }
      // the front legs: from the shoulder down to the fence, or raised
      for (var side = -1; side <= 1; side += 2) {
        var raise = side > 0 ? s.pawL : s.pawR;
        var reach = side > 0 ? s.reachL : s.reachR;
        var sh = point(body, [side * 6.6, 22.2, 9.5]);
        var shLocal = Rigs.local(root, [sh[0] - root.p[0], sh[1] - root.p[1], sh[2] - root.p[2]]);
        var shoulder = child(root, [shLocal[0] / S, shLocal[1] / S, shLocal[2] / S],
                             -raise, side * (0.12 * reach) - (side < 0 ? 0.55 : -0.55) *
                             (s.act && s.act.kind === 'groom' ? reach : 0), 0);
        var len = raise > 0.05 ? 20 : clamp(shLocal[1] / S - 2.15, 10, 26);
        pen.part(shoulder, 'rlimb', [0, -len / 2, 0.6], [7.2, len, 7.2], GINGER);
        if (near) {
          pen.part(shoulder, 'box', [0, -len * 0.45, 4.05], [6.2, 1.3, 0.4], STRIPE);
          pen.part(shoulder, 'box', [0, -len * 0.7, 4.05], [6.0, 1.2, 0.4], STRIPE);
        }
        var paw = child(shoulder, [0, -len - 0.1, 2.6], 0, 0, 0);
        pen.part(paw, 'rbox', [0, 0, 0], [8.4, 4.2, 10.2], CREAM);
        if (near) {
          // toe beans, on the underside: you see them when she lifts it
          pen.part(paw, 'sph', [0, -2.12, -0.6], [4.0, 0.8, 3.4], BEAN);
          pen.part(paw, 'sph', [-2.5, -2.12, 3.1], [1.9, 0.7, 1.9], BEAN);
          pen.part(paw, 'sph', [0, -2.12, 3.9], [1.9, 0.7, 1.9], BEAN);
          pen.part(paw, 'sph', [2.5, -2.12, 3.1], [1.9, 0.7, 1.9], BEAN);
          pen.part(paw, 'box', [-1.4, 1.2, 5.12], [0.3, 1.6, 0.3], '#e8dcc8');
          pen.part(paw, 'box', [1.4, 1.2, 5.12], [0.3, 1.6, 0.3], '#e8dcc8');
        }
      }
      // the collar and its bell
      pen.part(body, 'torus', [0, 41.2, 4.5], [26, 15, 23], COLLAR);
      var bellSwing = Math.sin(t * 3.1) * 0.15 + s.rear * 0.5;
      var bell = child(body, [0, 40.0, 15.6], bellSwing, 0, 0);
      pen.part(bell, 'sph', [0, -1.8, 0], [4.4, 4.4, 4.4], BELL, { m: 'metal' });
      if (near) pen.part(bell, 'box', [0, -2.4, 2.1], [2.6, 0.5, 0.3], '#7a5a1a');

      // ------------------------------------------------------- the head
      var head = child(body, [0, 44, 5], s.headPitch, s.headYaw - s.bodyYaw, s.headRoll);
      pen.part(head, 'rhead', [0, 13, 1], [31, 25, 25], GINGER);
      for (var cs = -1; cs <= 1; cs += 2) {
        // round cheeks, fluffed out at the jaw
        pen.part(head, 'sph', [cs * 13.2, 6.2, 5.5], [12, 10.5, 12], GINGER);
        pen.part(head, 'sph', [cs * 16.2, 4.6, 5.0], [5.5, 4.4, 6], GINGER);
      }
      pen.part(head, 'sph', [0, 6, 12], [14, 9, 7], CREAM);
      pen.part(head, 'sph', [0, 2.4, 10.6], [8, 4.4, 6], CREAM);
      pen.part(head, 'rbox', [0, 9.3, 15.1], [3.8, 2.6, 1.8], '#f28aa0');
      // the mouth: a little w, or open
      if (s.mouth > 0.08) {
        var m = s.mouth;
        pen.part(head, 'rbox', [0, 4.9 - 1.6 * m, 14.6], [3 + 3 * m, 1 + 4 * m, 1.3], '#7a2a3a');
        if (s.tongue > 0.3 || m > 0.55) {
          pen.part(head, 'rbox', [0, 3.9 - 2.4 * m - s.tongue * 0.6, 15.0 + s.tongue * 1.2],
                   [3.2, 1.0, 2.4 + s.tongue * 1.4], '#f27a8e');
        }
      } else {
        // the little w under her nose
        pen.part(head, 'box', [0, 7.6, 15.42], [0.45, 1.5, 0.5], '#5a2a2a');
        pen.part(head, 'box', [-2.05, 6.55, 15.2], [1.9, 0.48, 0.5], '#5a2a2a', { rz: -0.55 });
        pen.part(head, 'box', [-0.75, 6.55, 15.42], [1.9, 0.48, 0.5], '#5a2a2a', { rz: 0.55 });
        pen.part(head, 'box', [0.75, 6.55, 15.42], [1.9, 0.48, 0.5], '#5a2a2a', { rz: -0.55 });
        pen.part(head, 'box', [2.05, 6.55, 15.2], [1.9, 0.48, 0.5], '#5a2a2a', { rz: 0.55 });
      }
      if (s.tongue > 0.3 && s.mouth < 0.4) {
        pen.part(head, 'rbox', [0, 5.0, 15.6 + s.tongue], [2.6, 0.9, 2.2], '#f27a8e');
      }
      // the eyes
      var pw = 1.5 + 4.6 * s.pupil;
      for (var es = -1; es <= 1; es += 2) {
        var ex = es * 7.2;
        pen.part(head, 'sph', [ex, 14, 13.65], [8.4, 9.6, 1.7], IRIS);
        pen.part(head, 'sph', [ex + s.eyeX, 14 + s.eyeY, 14.25], [pw, 7.9, 1.0], PUPIL);
        pen.part(head, 'sph', [ex - 1.6 + s.eyeX * 0.4, 16.3 + s.eyeY * 0.4, 14.62],
                 [2.5, 2.5, 0.5], '#ffffff');
        if (near) {
          pen.part(head, 'sph', [ex + 1.7 + s.eyeX * 0.4, 12.0 + s.eyeY * 0.4, 14.55],
                   [1.1, 1.1, 0.4], '#ffffff');
        }
        if (s.lid > 0.04) {
          var lh = 9.8 * Math.min(1, s.lid);
          pen.part(head, 'box', [ex, 19.0 - lh / 2, 14.35], [9.6, lh, 1.5], GINGER);
          if (s.lid > 0.9) {
            // closed: a happy ^ or a sleepy line
            var cup = s.happy > 0.3 ? 1 : -1;
            pen.part(head, 'box', [ex - 1.9, 14.3, 15.15], [4.4, 0.7, 0.3], '#5a2a1a',
                     { rz: 0.42 * cup });
            pen.part(head, 'box', [ex + 1.9, 14.3, 15.15], [4.4, 0.7, 0.3], '#5a2a1a',
                     { rz: -0.42 * cup });
          }
        }
        pen.part(head, 'sph', [es * 11, 9.6, 13.2], [5.4, 2.8, 0.8], BLUSH, { a: 0.55 + 0.3 * s.happy });
      }
      if (near) {
        // the tabby M on her forehead, stripes on her cheeks
        pen.part(head, 'box', [0, 21.6, 13.55], [1.7, 5.4, 0.3], STRIPE);
        pen.part(head, 'box', [-3.7, 21.0, 13.55], [1.4, 4.4, 0.3], STRIPE, { rz: 0.16 });
        pen.part(head, 'box', [3.7, 21.0, 13.55], [1.4, 4.4, 0.3], STRIPE, { rz: -0.16 });
        for (var st = -1; st <= 1; st += 2) {
          pen.part(head, 'box', [st * 15.56, 15.5, 2], [0.3, 1.3, 7], STRIPE);
          pen.part(head, 'box', [st * 15.56, 12.2, 3], [0.3, 1.2, 6], STRIPE);
          // whiskers, fanned and swept back, twitching
          for (var w = 0; w < 3; w++) {
            var tw = Math.sin(t * 2.3 + w + st) * 0.04 + (s.mouth > 0.3 ? 0.08 : 0);
            pen.part(head, 'box', [st * 13.4, 6.6 + (w - 1) * 1.35, 14.2], [13.5, 0.36, 0.36], '#ffffff',
                     { ry: -st * 0.22, rz: st * ((w - 1) * 0.15 + tw) });
          }
        }
      }
      // the ears
      for (var ea = -1; ea <= 1; ea += 2) {
        var twitch = t - s.earTwitch[ea > 0 ? 0 : 1] < 0.22 ? 0.4 : 0;
        var ear = child(head, [ea * 9.6, 24.2, 0.5], -0.65 * s.flat - twitch * 0.5,
                        ea * twitch * 0.4, -ea * (0.2 + 0.95 * s.flat));
        pen.part(ear, 'cone', [0, 6.0, 0], [12.5, 14.5, 7], GINGER);
        pen.part(ear, 'cone', [0, 4.8, 1.7], [7.4, 9.6, 1.4], PINK);
        if (near) pen.part(ear, 'cone', [0, 13.0, 0], [2.2, 2.6, 1.2], GINGER_DARK);
      }

      // ------------------------------------------------------- the tail
      // over the fence top and down its face, swishing; puffed when she
      // is frightened, its tip twitching when she is hunting
      var pts = [[-13, 5, -12], [-20, 4, -8], [-24, 3, -1], [-25.5, 2.5, 6], [-25.5, 1.5, 11.6],
                 [-25, -6, 13.6], [-24.5, -14, 13.6], [-23.5, -22, 13.6], [-22, -29, 13.6],
                 [-19.5, -34, 13.6], [-16, -36.5, 13.6], [-12.4, -36, 13.6]];
      var world = [];
      for (var i = 0; i < pts.length; i++) {
        var q = pts[i].slice();
        if (i >= 4) {
          var along = (i - 4) / 7;
          q[0] += s.tailAmp * Math.sin(t * s.tailRate - i * 0.55) * along * 1.6;
          q[1] += s.happy * along * along * 9;
          if (i >= 9) q[0] += s.twitchTip * Math.sin(t * 15 + i) * 1.6;
        }
        world.push(point(root, q));
      }
      for (var j = 0; j < world.length - 1; j++) {
        var r = (5.4 - j * 0.12) * s.puff * S;
        var col = j >= 10 ? STRIPE : (j % 2 ? GINGER_DARK : GINGER);
        pen.rod(world[j], world[j + 1], r * 2, col);
        pen.part({ p: world[j], r: root.r, s: 1 }, 'sph', [0, 0, 0], [r * 2, r * 2, r * 2], col);
      }
      var tipR = 4.0 * s.puff * S;
      pen.part({ p: world[world.length - 1], r: root.r, s: 1 }, 'sph', [0, 0, 0],
               [tipR * 2, tipR * 2, tipR * 2], STRIPE);

      // hearts and zeds
      for (var hh = 0; hh < s.hearts.length; hh++) {
        var age = t - s.hearts[hh].t0;
        if (age < 0) continue;
        var hp = point(root, [s.hearts[hh].x + Math.sin(age * 3) * 2, 86 + age * 11, 14]);
        heart(pen, hp, (2.6 + age * 0.8) * S, Math.max(0, 1 - age / 2.6));
      }
      if (s.sleep > 0.4) {
        for (var z = 0; z < 3; z++) {
          var ph = (t * 0.42 + z / 3) % 1;
          var zp = point(root, [12 + ph * 14, 80 + ph * 30, 10]);
          zed(pen, zp, (2.6 + ph * 3) * S, Math.sin(ph * Math.PI) * 0.9 * Math.min(1, (s.sleep - 0.4) * 3));
        }
      }
    }

    function event(kind, msg) {
      var t = Rigs.clock();
      if (kind === 'flag_capture') {
        start('pounce', t, 1.1, { then: 'happy' });
        say('br_meow', 1);
      } else if (kind === 'flag_return') {
        say('br_mrrp', 0.8);
        s.earTwitch = [t, t];
      } else if (kind === 'shot' && msg && msg.from) {
        var d = dist(msg.from, root.p);
        if (d < 120 * S && t > s.startleCool && !(s.act && s.act.kind === 'pounce')) {
          start('startle', t, 1.7);
          s.startleCool = t + 9;
          say(hash(t) < 0.5 ? 'br_hiss' : 'br_mrrp', 1);
        } else if (d < 260 * S) {
          s.earTwitch = [t, t + 0.05];
        }
      }
    }

    var me = { radius: 110 * S, at: headAt, update: update, draw: draw, event: event,
               kind: 'garden_cat' };
    return me;
  });

  // ======================================================= the garden
  /* A butterfly about a patch of the garden: a figure that never quite
     repeats, the wings beating and gliding. */
  Rigs.register('butterfly', function (spec, ctx) {
    var home = spec.p, R = spec.r || 30, seed = spec.seed || 1, S = spec.s || 1;
    var colour = spec.c || '#f6f2e6', tip = spec.tip || '#2a2a2a';
    var pos = home.slice(), heading = 0, lastT = 0;
    var me = { radius: R + 12, at: pos, kind: 'butterfly' };
    if (ctx.critters) ctx.critters.push(me);
    function place(t) {
      var tt = t * (spec.speed || 0.32);
      return [home[0] + R * wander(tt, seed), home[1] + 3 + 4 * wander(tt * 1.9, seed + 4),
              home[2] + R * wander(tt * 0.86, seed + 9)];
    }
    me.update = function (dt, t) {
      var next = place(t);
      var vx = next[0] - pos[0], vz = next[2] - pos[2];
      if (Math.abs(vx) + Math.abs(vz) > 1e-3) {
        heading = Rigs.approachAngle(heading, Math.atan2(vx, vz), 6, dt || 0.016);
      }
      pos[0] = next[0]; pos[1] = next[1]; pos[2] = next[2];
      lastT = t;
    };
    me.draw = function (pen, t) {
      var f = Rigs.frame(pos, heading, S);
      var glide = Math.sin(t * 0.9 + seed) > 0.6;
      var flap = glide ? 0.25 : Math.sin(t * 16 + seed) * 0.95 + 0.25;
      pen.part(f, 'cyl', [0, 0, 0], [0.6, 3.4, 0.6], '#2a2420', { rx: Math.PI / 2 });
      for (var side = -1; side <= 1; side += 2) {
        var wing = child(f, [side * 0.25, 0.1, 0], 0, 0, -side * flap);
        pen.part(wing, 'box', [side * 2.3, 0, 0.7], [4.4, 0.1, 3.4], colour);
        pen.part(wing, 'box', [side * 1.8, 0, -1.5], [3.4, 0.09, 2.4], colour);
        if (pen.near) {
          pen.part(wing, 'box', [side * 3.7, 0.06, 1.7], [1.3, 0.08, 1.3], tip);
          pen.part(wing, 'box', [side * 2.2, 0.06, 0.4], [0.9, 0.08, 0.9], tip);
        }
      }
    };
    return me;
  });

  /* A bumblebee doing the rounds of a few flowers: a figure of eight,
     hovering at each, buzzing as it passes you. */
  Rigs.register('bee', function (spec, ctx) {
    var a = spec.p, b = spec.q || [a[0] + 20, a[1], a[2]], seed = spec.seed || 2, S = spec.s || 1;
    var pos = a.slice(), heading = 0, buzzAt = 0;
    var me = { radius: dist(a, b) + 20, at: pos, kind: 'bee' };
    me.update = function (dt, t) {
      var u = (Math.sin(t * 0.45 + seed) + 1) / 2;
      var hover = Math.sin(t * 0.9 + seed * 2);
      var side = Math.sin(t * 0.9 + seed) * 7;
      var nx = a[0] + (b[0] - a[0]) * u + side * 0.5;
      var nz = a[2] + (b[2] - a[2]) * u + side;
      var ny = a[1] + 4 + hover * 1.6 + Math.sin(t * 7) * 0.3;
      var vx = nx - pos[0], vz = nz - pos[2];
      if (Math.abs(vx) + Math.abs(vz) > 1e-3) heading = Rigs.approachAngle(heading, Math.atan2(vx, vz), 5, dt);
      pos[0] = nx; pos[1] = ny; pos[2] = nz;
      if (ctx.viewer && t > buzzAt) {
        var v = ctx.viewer();
        if (v && dist(v.eye, pos) < 34) { buzzAt = t + 0.55; if (ctx.sound) ctx.sound('br_buzz', pos, 1.4); }
      }
    };
    me.draw = function (pen, t) {
      var f = Rigs.frame(pos, heading, S);
      pen.part(f, 'sph', [0, 0, 1.2], [2.6, 2.6, 2.4], '#f2c21e');
      pen.part(f, 'sph', [0, 0, -0.4], [2.9, 2.8, 2.2], '#1e1a14');
      pen.part(f, 'sph', [0, 0, -1.8], [2.7, 2.6, 2.4], '#f2c21e');
      pen.part(f, 'sph', [0, 0.1, 2.7], [1.8, 1.8, 1.6], '#1e1a14');
      pen.part(f, 'cone', [0, 0, -3.2], [0.8, 1.0, 0.8], '#1e1a14', { rx: -Math.PI / 2 });
      var flap = Math.sin(t * 70) * 0.5;
      for (var side = -1; side <= 1; side += 2) {
        var wing = child(f, [side * 0.6, 1.2, 0.2], 0, 0, -side * (0.5 + flap));
        pen.part(wing, 'box', [side * 1.6, 0, 0], [3.0, 0.08, 1.6], '#e8f4ff', { a: 0.55 });
      }
    };
    return me;
  });

  /* A snail going along the top of the hose and back, very slowly, its
     eyes on their stalks. */
  Rigs.register('snail', function (spec) {
    var a = spec.p, b = spec.q, S = spec.s || 1;
    var len = dist(a, b), speed = spec.speed || 0.7;
    var heading = Math.atan2(b[0] - a[0], b[2] - a[2]);
    var pos = a.slice();
    var me = { radius: len / 2 + 10, at: [(a[0] + b[0]) / 2, a[1], (a[2] + b[2]) / 2], kind: 'snail' };
    var dirn = 1;
    me.update = function (dt, t) {
      var period = (len / speed) * 2;
      var ph = (t % period) / period;
      var u = ph < 0.5 ? ph * 2 : 2 - ph * 2;
      dirn = ph < 0.5 ? 1 : -1;
      pos[0] = a[0] + (b[0] - a[0]) * u;
      pos[1] = a[1];
      pos[2] = a[2] + (b[2] - a[2]) * u;
    };
    me.draw = function (pen, t) {
      var f = Rigs.frame(pos, heading + (dirn < 0 ? Math.PI : 0), S);
      var creep = 1 + Math.sin(t * 2.2) * 0.05;
      pen.part(f, 'rbox', [0, 0.7, 0.6], [2.8, 1.4, 9.0 * creep], '#a8a890');
      pen.part(f, 'sph', [0, 1.4, 4.4 * creep], [2.4, 2.2, 2.4], '#b0b098');
      pen.part(f, 'sph', [0, 3.6, -0.6], [5.6, 5.4, 5.0], '#9a5a2a');
      pen.part(f, 'sph', [0, 4.1, 0.6], [3.6, 3.4, 3.6], '#b8743a');
      pen.part(f, 'sph', [0, 4.4, 1.3], [1.7, 1.6, 1.8], '#d89a5a');
      for (var side = -1; side <= 1; side += 2) {
        var bob = Math.sin(t * 1.7 + side) * 0.2;
        var stalk = child(f, [side * 0.6, 2.2, 5.0 * creep], -0.35 + bob, 0, -side * 0.25);
        pen.part(stalk, 'cyl', [0, 1.4, 0], [0.35, 2.8, 0.35], '#a8a890');
        pen.part(stalk, 'sph', [0, 2.9, 0], [0.8, 0.8, 0.8], '#3a3a30');
      }
    };
    return me;
  });

  /* A goldfish round and round the pond under the water -- and now and
     then, out of it, with a splash. */
  Rigs.register('goldfish', function (spec, ctx) {
    var c = spec.p, rx = spec.rx || 30, rz = spec.rz || 12, seed = spec.seed || 1, S = spec.s || 1;
    var water = spec.water !== undefined ? spec.water : c[1] + 1.4;
    var pos = c.slice(), heading = 0, splashT = -10, lastJump = -1;
    var me = { radius: Math.max(rx, rz) + 10, at: c, kind: 'goldfish' };
    var JUMP = 1.1, EVERY = 23;
    me.update = function (dt, t) {
      var a = t * (spec.speed || 0.35) + seed;
      var nx = c[0] + Math.cos(a) * rx, nz = c[2] + Math.sin(a * 1.0) * rz;
      var vx = -Math.sin(a) * rx, vz = Math.cos(a) * rz;
      heading = Math.atan2(vx, vz);
      var slot = Math.floor((t + seed * 7) / EVERY);
      var into = (t + seed * 7) - slot * EVERY;
      var y = c[1] + Math.sin(t * 0.8 + seed) * 0.4;
      me.jump = 0;
      if (hash(slot + seed * 3.3) < 0.55 && into < JUMP) {
        var k = into / JUMP;
        y = water - 0.6 + Math.sin(k * Math.PI) * 7;
        me.jump = k;
        if (slot !== lastJump && k > 0.85) {
          lastJump = slot;
          splashT = t;
          if (ctx.sound) ctx.sound('br_splash', [nx, water, nz], 1);
        }
      }
      pos[0] = nx; pos[1] = y; pos[2] = nz;
      me.splashT = splashT;
    };
    me.draw = function (pen, t) {
      var pitch = me.jump ? -Math.cos(me.jump * Math.PI) * 0.9 : 0;
      var f = Rigs.frame(pos, heading, S);
      f = child(f, [0, 0, 0], pitch, 0, 0);
      pen.part(f, 'sph', [0, 0, 0.4], [2.0, 2.4, 5.2], '#f2782a');
      pen.part(f, 'sph', [0, 0.2, 2.2], [1.6, 1.8, 1.8], '#f58a3a');
      var wag = Math.sin(t * 9 + seed) * 0.5;
      var tail = child(f, [0, 0, -2.0], 0, wag, 0);
      pen.part(tail, 'box', [0, 0, -1.2], [0.2, 2.6, 2.4], '#f2a05a');
      pen.part(f, 'box', [0, 1.4, 0.2], [0.18, 1.2, 2.2], '#f2a05a');
      if (pen.near) {
        for (var side = -1; side <= 1; side += 2) {
          pen.part(f, 'sph', [side * 0.85, 0.45, 2.6], [0.45, 0.5, 0.45], '#1a1a1a');
        }
      }
      var age = t - me.splashT;
      if (age >= 0 && age < 1.2) {
        var ring = Rigs.frame([pos[0], water + 0.05, pos[2]], 0, 1);
        var rr = 3 + age * 14;
        pen.part(ring, 'torus', [0, 0, 0], [rr, 1.2, rr], '#e8f4f8', { a: 0.7 * (1 - age / 1.2) });
      }
    };
    return me;
  });

  /* A ladybird walking round the top of a cabbage. */
  Rigs.register('ladybird', function (spec) {
    var c = spec.p, R = spec.r || 3.5, ry = spec.ry || 5, rr = spec.rr || 6, S = spec.s || 1;
    var pos = c.slice(), heading = 0;
    var me = { radius: 12, at: c, kind: 'ladybird' };
    me.update = function (dt, t) {
      var a = t * 0.25 + (spec.seed || 0);
      var x = Math.cos(a) * R, z = Math.sin(a) * R;
      var y = ry * Math.sqrt(Math.max(0, 1 - (R / rr) * (R / rr)));
      pos[0] = c[0] + x; pos[1] = c[1] + y; pos[2] = c[2] + z;
      heading = Math.atan2(-Math.sin(a), Math.cos(a));
    };
    me.draw = function (pen, t) {
      var f = Rigs.frame(pos, heading, S);
      pen.part(f, 'sph', [0, 0.6, 0], [2.6, 1.6, 3.0], '#d8221a');
      pen.part(f, 'sph', [0, 0.5, 1.5], [1.4, 1.0, 1.0], '#1b1b1b');
      if (pen.near) {
        pen.part(f, 'box', [0, 1.38, -0.1], [0.12, 0.1, 2.6], '#1b1b1b');
        [[-0.6, 0.4], [0.6, 0.4], [-0.55, -0.6], [0.55, -0.6]].forEach(function (d) {
          pen.part(f, 'sph', [d[0], 1.3, d[1]], [0.55, 0.2, 0.55], '#1b1b1b');
        });
        for (var leg = 0; leg < 3; leg++) {
          var step = Math.sin(t * 8 + leg * 2) * 0.25;
          for (var side = -1; side <= 1; side += 2) {
            pen.part(f, 'box', [side * 1.2, 0.15, -0.6 + leg * 0.6 + step * side], [0.8, 0.1, 0.12],
                     '#1b1b1b');
          }
        }
      }
    };
    return me;
  });

  /* A sunflower over the fence, nodding in the breeze. */
  Rigs.register('sunflower', function (spec) {
    var base = spec.p, H = spec.h || 30, W = spec.w || 30, seed = spec.seed || 0;
    var me = { radius: H + W, at: [base[0], base[1] + H, base[2]], kind: 'sunflower' };
    me.draw = function (pen, t) {
      var sway = Math.sin(t * 0.7 + seed) * 0.05 + Math.sin(t * 1.9 + seed * 2) * 0.015;
      var stem = Rigs.frame(base, spec.yaw || 0, 1);
      stem = child(stem, [0, 0, 0], 0, 0, sway);
      pen.part(stem, 'cyl', [0, H / 2, 0], [3, H, 3], '#4a8a2a');
      pen.part(stem, 'box', [2.6, H * 0.45, 0], [5.0, 0.6, 2.6], '#5a9a3a', { rz: -0.4 });
      var head = child(stem, [0, H + 2, -2], -0.3 + sway * 2, 0, 0);
      pen.part(head, 'cyl', [0, 0, 0], [W * 0.8, 2.4, W * 0.8], '#f2b81e', { rx: Math.PI / 2 });
      for (var k = 0; k < 12; k++) {
        var a = k * TAU / 12 + seed;
        pen.part(head, 'box', [Math.sin(a) * W * 0.42, Math.cos(a) * W * 0.42, 0.2],
                 [W * 0.14, W * 0.3, 0.5], k % 2 ? '#f2c21e' : '#f8d23a', { rz: -a });
      }
      pen.part(head, 'cyl', [0, 0, 1.4], [W * 0.47, 2, W * 0.47], '#5a3a1a', { rx: Math.PI / 2 });
    };
    return me;
  });

  // ========================================================= The Orrery
  var BRASS = '#c89a3a', BRASS_DARK = '#8a6a28', BRASS_LIGHT = '#e8c060', IRON = '#2a2a2e';
  var AXES = { x: [0, 0, -Math.PI / 2], y: [0, 0, 0], z: [Math.PI / 2, 0, 0] };

  if (GA) {
    GA.register('br_cuckoo', function (vol) {
      this.tone({ type: 'sine', freq: 740, freqEnd: 700, dur: 0.22, gain: 0.08 * vol });
      this.later(260, function () { this.tone({ type: 'sine', freq: 587, freqEnd: 560, dur: 0.32, gain: 0.08 * vol }); });
    });
    GA.register('br_whirr', function (vol) {
      this.tone({ type: 'sawtooth', freq: 90, freqEnd: 260, dur: 0.8, gain: 0.02 * vol });
      this.noise({ filter: 'bandpass', freq: 1800, dur: 0.6, gain: 0.02 * vol });
    });
    GA.register('br_toll', function (vol) {
      [196, 392, 588].forEach(function (f, i) {
        this.tone({ type: 'sine', freq: f, dur: 2.6 - i * 0.6, gain: (0.06 - i * 0.015) * vol });
      }, this);
    });
  }

  function axisFrame(at, axis) {
    var a = AXES[axis || 'y'];
    return child(Rigs.frame(at, 0, 1), [0, 0, 0], a[0], a[1], a[2]);
  }

  /* A gear: a disc on local y, teeth round the rim, a hub and spokes. */
  function drawGear(pen, f, r, n, th, colour, angle) {
    var g = child(f, [0, 0, 0], 0, angle, 0);
    pen.part(g, 'cyl', [0, 0, 0], [r * 2 - 0.2, th, r * 2 - 0.2], colour, { m: 'metal' });
    pen.part(g, 'cyl', [0, 0, 0], [r * 0.5, th + 0.5, r * 0.5], BRASS_DARK, { m: 'metal' });
    if (!pen.near) return;
    for (var sp = 0; sp < 4; sp++) {
      pen.part(g, 'box', [0, th * 0.5 + 0.03, 0], [r * 1.5, 0.08, r * 0.16], BRASS_DARK,
               { ry: sp * Math.PI / 4 });
    }
    var tw = Math.max(0.35, Math.PI * r / n);
    for (var k = 0; k < n; k++) {
      var a = k * TAU / n;
      pen.part(g, 'box', [Math.sin(a) * (r + 0.32), 0, Math.cos(a) * (r + 0.32)],
               [tw * 0.9, th * 0.92, 0.9], colour, { ry: a, m: 'metal' });
    }
  }

  /* A train of gears on a wall, meshed: each turns at the base rate times
     (r0 / r), alternate ones the other way.  spec.gears: [dx, dy, dz, r, n,
     dir] about the rig's point; spec.axis the way the discs face. */
  Rigs.register('gear_train', function (spec, ctx) {
    var gears = spec.gears || [];
    var base = spec.w || 0.6, r0 = gears.length ? gears[0][3] : 1;
    var reach = 0;
    gears.forEach(function (g) { reach = Math.max(reach, Math.hypot(g[0], g[1], g[2]) + g[3]); });
    var me = { radius: reach + 6, at: spec.p, kind: 'gear_train', spin: 0 };
    me.update = function (dt) {
      var rate = spec.flags && ctx.flagSpots && ctx.flagSpots().some(function (f) {
        return f.state !== 'home';
      }) ? 2.6 : 1;
      me.rate = approach(me.rate || 1, rate, 1.5, dt);
      me.spin += dt * base * me.rate;
    };
    me.draw = function (pen) {
      for (var i = 0; i < gears.length; i++) {
        var g = gears[i];
        var f = axisFrame([spec.p[0] + g[0], spec.p[1] + g[1], spec.p[2] + g[2]], spec.axis);
        drawGear(pen, f, g[3], g[4], spec.th || 0.8, g[6] || (i % 2 ? BRASS_LIGHT : BRASS),
                 (g[5] || 1) * me.spin * r0 / g[3] + (g[7] || 0));
      }
    };
    return me;
  });

  /* The gear room's seconds pendulum, and the escape wheel it lets round a
     tooth at a time: tick... tock. */
  Rigs.register('pendulum', function (spec, ctx) {
    var L = spec.len || 7, period = spec.period || 2, amp = spec.amp || 0.32;
    var wheel = spec.wheel_p, axis = spec.axis || 'z', half = period / 2;
    var me = { radius: L + 16, at: spec.p, kind: 'pendulum' };
    me.draw = function (pen, t) {
      var swing = Math.sin(t * TAU / period) * amp;
      var f = child(Rigs.frame(spec.p, spec.yaw || 0, 1), [0, 0, 0], 0, 0, swing);
      pen.part(f, 'box', [0, -L / 2, 0], [0.35, L, 0.35], BRASS_DARK, { m: 'metal' });
      pen.part(f, 'cyl', [0, -L - 0.2, 0], [2.8, 0.7, 2.8], BRASS, { m: 'metal', rx: Math.PI / 2 });
      pen.part(f, 'sph', [0, -L - 0.2, 0.2], [1.2, 1.2, 0.5], BRASS_LIGHT, { m: 'metal' });
      pen.part(Rigs.frame(spec.p, 0, 1), 'box', [0, 0.3, 0], [2.4, 0.6, 1.2], BRASS_DARK, { m: 'metal' });
      if (wheel) {
        var steps = Math.floor(t / half), f2 = (t / half) - steps;
        var a = (steps + Math.min(1, f2 * 7)) * TAU / 30;
        drawGear(pen, axisFrame(wheel, axis), spec.wheel_r || 6, 30, 1.0, BRASS, a);
        if (spec.pinion_p) {
          drawGear(pen, axisFrame(spec.pinion_p, axis), 2.4, 12, 1.0, BRASS_LIGHT,
                   -a * (spec.wheel_r || 6) / 2.4 + 0.13);
        }
      }
      var beat = Math.floor(t / half);
      if (beat !== me.tick) {
        me.tick = beat;
        var v = ctx.viewer ? ctx.viewer() : null;
        if (v && dist(v.eye, spec.p) < 46 && ctx.sound) ctx.sound('br_tick', spec.p, 1.2);
      }
    };
    return me;
  });

  /* The sun of the orrery: a glowing core that breathes, flares wheeling
     round it, and three armillary bands turning each its own way. */
  Rigs.register('orrery_sun', function (spec, ctx) {
    var R = spec.r || 11;
    var me = { radius: R * 3, at: spec.p, kind: 'orrery_sun' };
    me.draw = function (pen, t) {
      var c = spec.p;
      var f = Rigs.frame(c, t * 0.08, 1);
      var breathe = 1 + Math.sin(t * 1.3) * 0.03;
      pen.part(f, 'sph', [0, 0, 0], [R * 2, R * 2, R * 2], '#ffb84a', { m: 'neon' });
      pen.part(f, 'sph', [0, 0, 0], [R * 2.32 * breathe, R * 2.32 * breathe, R * 2.32 * breathe],
               '#ffd890', { m: 'neon', a: 0.2 });
      pen.part(f, 'sph', [0, 0, 0], [R * 2.8 * breathe, R * 2.8 * breathe, R * 2.8 * breathe],
               '#ffb070', { m: 'neon', a: 0.08 });
      for (var k = 0; k < 6; k++) {
        var a = t * (0.5 + k * 0.07) + k * 1.05;
        var tilt = 0.5 + k * 0.33;
        var fl = child(Rigs.frame(c, 0, 1), [0, 0, 0], tilt, a, 0);
        var pulse = 0.7 + 0.3 * Math.sin(t * 3 + k * 2);
        pen.part(fl, 'sph', [0, 0, R * 1.02], [2.6 * pulse, 2.6 * pulse, 3.6 * pulse], '#ffe0a0',
                 { m: 'neon', a: 0.85 });
      }
      var bands = [[t * 0.21, 0, 0.42, 1.0], [0.9, t * -0.17, 1.2, 1.06], [Math.PI / 2, 0, t * 0.13, 1.12]];
      for (var b2 = 0; b2 < bands.length; b2++) {
        var bf = child(Rigs.frame(c, 0, 1), [0, 0, 0], bands[b2][0], bands[b2][1], bands[b2][2]);
        var d = R * 2.6 * bands[b2][3];
        pen.part(bf, 'torus', [0, 0, 0], [d, 5, d], b2 === 1 ? BRASS_LIGHT : BRASS, { m: 'metal' });
        if (pen.near && b2 === 0) {
          for (var z = 0; z < 12; z++) {
            var za = z * TAU / 12;
            pen.part(bf, 'box', [Math.sin(za) * d * 0.4, 0, Math.cos(za) * d * 0.4], [1.6, 1.4, 1.6],
                     BRASS_LIGHT, { ry: za, m: 'metal' });
          }
        }
      }
    };
    return me;
  });

  /* The planets: each on a brass arm from the column (or the crown above
     the sun), round and round at its own rate, a counterweight opposite,
     moons on their own little arms.  The whole works winds faster while a
     flag is out. */
  Rigs.register('orrery', function (spec, ctx) {
    var planets = spec.planets || [];
    var c = spec.p;
    var phases = planets.map(function (pl, i) {
      return (Rigs.clock() * TAU / pl.period + i * 1.7) % TAU;
    });
    var maxR = 0;
    planets.forEach(function (pl) { maxR = Math.max(maxR, pl.R + pl.size); });
    var me = { radius: maxR + 20, at: [c[0], c[1] + 50, c[2]], kind: 'orrery', wind: 1, spin: 0 };
    me.update = function (dt) {
      var out = ctx.flagSpots && ctx.flagSpots().some(function (f) { return f.state !== 'home'; });
      me.wind = approach(me.wind, out ? 3.2 : 1, 0.6, dt);
      for (var i = 0; i < planets.length; i++) phases[i] += dt * TAU / planets[i].period * me.wind;
      me.spin += dt * me.wind;
    };
    function planet(pen, f, pl, t) {
      var d = pl.size;
      var spinF = child(f, [0, 0, 0], pl.tilt || 0, me.spin * (pl.day || 1), 0);
      pen.part(spinF, 'sph', [0, 0, 0], [d, d, d], pl.c);
      var bands = pl.bands || [];
      for (var b = 0; b < bands.length; b++) {
        var lat = bands[b][0] * d / 2, rho = Math.sqrt(Math.max(0, d * d / 4 - lat * lat));
        pen.part(spinF, 'cyl', [0, lat, 0], [rho * 2 + 0.25, bands[b][1] * d, rho * 2 + 0.25], bands[b][2]);
      }
      var spots = pl.spots || [];
      for (var s2 = 0; s2 < spots.length; s2++) {
        var sp = spots[s2];   // [lat, lon, size, colour]
        var la = sp[0], lo = sp[1];
        var off = [Math.cos(la) * Math.sin(lo) * d * 0.47, Math.sin(la) * d * 0.47, Math.cos(la) * Math.cos(lo) * d * 0.47];
        pen.part(spinF, 'sph', off, [sp[2], sp[2] * 0.7, sp[2]], sp[3]);
      }
      if (pl.ring) {
        var rf = child(f, [0, 0, 0], pl.ring.tilt || 0.45, me.spin * 0.05, 0);
        pen.part(rf, 'cyl', [0, 0, 0], [d * pl.ring.outer, 0.25, d * pl.ring.outer], pl.ring.c || '#e8dcb0',
                 { a: 0.9 });
        pen.part(rf, 'cyl', [0, 0, 0], [d * pl.ring.outer * 0.78, 0.32, d * pl.ring.outer * 0.78],
                 pl.ring.c2 || '#b8a878', { a: 0.95 });
      }
      var moons = pl.moons || [];
      for (var m = 0; m < moons.length; m++) {
        var mo = moons[m];   // [R, size, period, colour]
        var ma = t * TAU / mo[2] * me.wind + m * 2.1;
        var mf = child(f, [0, 0, 0], 0, ma, 0);
        if (pen.near) pen.part(mf, 'box', [0, 0, mo[0] / 2], [0.25, 0.25, mo[0]], BRASS_DARK, { m: 'metal' });
        pen.part(mf, 'sph', [0, 0, mo[0]], [mo[1], mo[1], mo[1]], mo[3]);
      }
    }
    me.draw = function (pen, t) {
      for (var i = 0; i < planets.length; i++) {
        var pl = planets[i];
        var arm = Rigs.frame([c[0], pl.y, c[2]], phases[i], 1);
        var collar = pl.collar || 5.6;
        pen.part(arm, 'cyl', [0, 0, 0], [collar * 2, 1.6, collar * 2], BRASS_DARK, { m: 'metal' });
        pen.part(arm, 'box', [0, 0, (pl.R + collar) / 2], [1.1, 1.1, pl.R - collar], BRASS, { m: 'metal' });
        // a counterweight opposite, on a short arm
        var cw = pl.R * 0.25 + 4;
        pen.part(arm, 'box', [0, 0, -(cw + collar) / 2], [0.9, 0.9, cw - collar + 2], BRASS, { m: 'metal' });
        pen.part(arm, 'sph', [0, 0, -cw], [2.4 + pl.size * 0.12, 2.4 + pl.size * 0.12, 2.4 + pl.size * 0.12],
                 BRASS_DARK, { m: 'metal' });
        // up a post to the ecliptic (or down a rod from the crown)
        var lift = pl.post ? pl.post - pl.y : 0, drop = pl.drop || 0;
        if (lift) {
          pen.part(arm, 'cyl', [0, (lift - pl.size / 2) / 2, pl.R], [0.9, lift - pl.size / 2, 0.9],
                   BRASS_DARK, { m: 'metal' });
          pen.part(arm, 'cyl', [0, lift - pl.size / 2 - 0.1, pl.R], [2.4, 0.7, 2.4], BRASS, { m: 'metal' });
        }
        if (drop) {
          pen.part(arm, 'box', [0, -(drop - pl.size / 2) / 2, pl.R], [0.7, drop - pl.size / 2, 0.7],
                   BRASS_DARK, { m: 'metal' });
        }
        var pf = child(arm, [0, lift - drop, pl.R], 0, 0, 0);
        planet(pen, pf, pl, t);
      }
      if (spec.spindle) {
        var sp = spec.spindle;   // [from y, to y]
        pen.part(Rigs.frame([c[0], (sp[0] + sp[1]) / 2, c[2]], 0, 1), 'cyl', [0, 0, 0],
                 [1.8, sp[1] - sp[0], 1.8], BRASS_DARK, { m: 'metal' });
        var star = Rigs.frame([c[0], sp[1] + 3, c[2]], me.spin * 0.4, 1);
        pen.part(star, 'sph', [0, 0, 0], [2.6, 2.6, 2.6], BRASS_LIGHT, { m: 'metal' });
        for (var k = 0; k < 4; k++) {
          pen.part(star, 'cone', [0, 0, 0], [1.6, 9, 1.6], BRASS_LIGHT, { rz: k * Math.PI / 2, m: 'metal' });
        }
      }
    };
    return me;
  });

  /* A clock face whose hands count the round down: one turn of the long
     hand is the whole round, the short one sweeps the seconds.  The last
     minute it glows; in sudden death the hands spin. */
  Rigs.register('round_clock', function (spec, ctx) {
    var R = spec.r || 4.5;
    var shown = { left: null, at: 0 };
    var me = { radius: R + 4, at: spec.p, kind: 'round_clock' };
    me.update = function (dt, t) {
      var st = ctx.round ? ctx.round() : null;
      if (st && typeof st.time_left === 'number' && st.time_left !== shown.raw) {
        shown.raw = st.time_left;
        shown.left = st.time_left;
        shown.at = t;
      }
      me.len = st && st.length ? st.length : 900;
      me.sudden = st && (st.sudden || st.overtime);
    };
    me.draw = function (pen, t) {
      var f = Rigs.frame(spec.p, spec.yaw || 0, 1);
      var left = shown.left === null ? me.len * (0.5 + 0.5 * Math.sin(t * 0.01)) :
        Math.max(0, shown.left - (t - shown.at));
      var urgent = left < 60 || me.sudden;
      var glow = urgent ? 0.5 + 0.5 * Math.sin(t * 6) : 0;
      pen.part(f, 'cyl', [0, 0, 0.1], [R * 2 + 1.2, 0.5, R * 2 + 1.2], BRASS_DARK, { rx: Math.PI / 2, m: 'metal' });
      pen.part(f, 'cyl', [0, 0, 0.3], [R * 2, 0.3, R * 2], glow > 0.05 ? '#ffd0a0' : '#f4ecd8',
               { rx: Math.PI / 2, m: glow > 0.5 ? 'neon' : '' });
      for (var k = 0; k < 12; k++) {
        var a = k * TAU / 12;
        var big = k % 3 === 0;
        pen.part(f, 'box', [Math.sin(a) * R * 0.82, Math.cos(a) * R * 0.82, 0.5],
                 [big ? 0.5 : 0.28, big ? 1.1 : 0.6, 0.12], '#2a2218', { rz: -a });
      }
      var frac = me.sudden ? (t * 0.7) % 1 : 1 - left / me.len;
      var long = frac * TAU, sec = me.sudden ? t * 9 : ((me.len - left) % 60) / 60 * TAU;
      var hand = function (angle, length, width, colour, z) {
        pen.part(child(f, [0, 0, z], 0, 0, -angle), 'box', [0, length / 2 - 0.4, 0],
                 [width, length, 0.14], colour);
      };
      hand(long / 12, R * 0.55, 0.55, '#2a2218', 0.62);
      hand(long, R * 0.82, 0.38, '#2a2218', 0.72);
      hand(sec, R * 0.9, 0.16, urgent ? '#d8321a' : '#8a1a12', 0.8);
      pen.part(f, 'cyl', [0, 0, 0.86], [0.7, 0.2, 0.7], BRASS_LIGHT, { rx: Math.PI / 2, m: 'metal' });
      // a chime when each minute of the round runs out
      var minute = Math.ceil(left / 60);
      if (me.minute !== undefined && minute < me.minute && spec.chime && ctx.sound) {
        ctx.sound('br_toll', spec.p, 1);
      }
      me.minute = minute;
    };
    return me;
  });

  /* A cuckoo in its little house, which comes out to call when its team
     scores -- and on every minute of the round. */
  Rigs.register('cuckoo', function (spec, ctx) {
    var me = { radius: 14, at: spec.p, kind: 'cuckoo', pop: -10 };
    var team = spec.team, colour = team === 'red' ? '#c4281c' : (team === 'blue' ? '#0d69ac' : '#6a8a3a');
    me.event = function (kind, msg) {
      if (kind === 'flag_capture' && (!team || (msg && msg.team === team))) {
        me.pop = Rigs.clock();
        if (ctx.sound) {
          setTimeout(function () { ctx.sound('br_cuckoo', spec.p, 1.4); }, 450);
          setTimeout(function () { ctx.sound('br_cuckoo', spec.p, 1.4); }, 1350);
        }
      }
    };
    me.update = function (dt, t) {
      var st = ctx.round ? ctx.round() : null;
      if (st && typeof st.time_left === 'number') {
        var minute = Math.ceil(st.time_left / 60);
        if (me.minute !== undefined && minute < me.minute && t - me.pop > 3) me.pop = t;
        me.minute = minute;
      }
    };
    me.draw = function (pen, t) {
      var f = Rigs.frame(spec.p, spec.yaw || 0, spec.s || 1);
      pen.part(f, 'box', [0, 0, -1.2], [6, 6.4, 2.4], '#6a3a1e');
      pen.part(f, 'box', [-1.7, 4.2, -1.2], [4.4, 0.7, 3.4], '#3a2a1a', { rz: 0.6 });
      pen.part(f, 'box', [1.7, 4.2, -1.2], [4.4, 0.7, 3.4], '#3a2a1a', { rz: -0.6 });
      pen.part(f, 'cyl', [0, 0.6, 0.02], [3.0, 0.1, 3.0], '#1a120c', { rx: Math.PI / 2 });
      if (pen.near) {
        for (var lv = 0; lv < 3; lv++) {
          pen.part(f, 'box', [0, -2.4, 0.05 + lv * 0.0], [5.2 - lv * 1.2, 0.3, 0.2], '#8a5a2e');
        }
        pen.part(f, 'cyl', [0, -5.6, 0.2], [1.2, 2.6, 1.2], BRASS, { m: 'metal' });
        pen.part(f, 'cone', [0, -7.5, 0.2], [1.6, 1.8, 1.6], BRASS, { m: 'metal', rx: Math.PI });
      }
      var age = t - me.pop;
      var out = age < 0 || age > 2.6 ? 0 : Math.min(1, age * 5, (2.6 - age) * 4);
      var bob = age > 0 && age < 2.6 ? Math.max(0, Math.sin(age * TAU / 0.9)) * 0.5 : 0;
      for (var side = -1; side <= 1; side += 2) {
        var leaf = child(f, [side * 1.5, 0.6, 0.12], 0, side * out * 1.9, 0);
        pen.part(leaf, 'box', [-side * 0.75, 0, 0], [1.5, 3.0, 0.2], '#8a5a2e');
      }
      if (out > 0.02) {
        var bird = child(f, [0, 0.6 + bob * 0.4, out * 3.4], -bob * 0.5, 0, 0);
        pen.part(bird, 'sph', [0, 0, 0], [1.6, 1.5, 2.6], colour);
        pen.part(bird, 'sph', [0, 0.9, 1.0], [1.2, 1.2, 1.2], colour);
        pen.part(bird, 'cone', [0, 0.85, 1.9], [0.45, 1.0, 0.45], '#f2b81e', { rx: Math.PI / 2 });
        pen.part(bird, 'box', [0, 0.1, -1.6], [0.9, 0.2, 1.6], '#3a2a1a', { rx: -0.3 });
        pen.part(child(f, [0, 0.6, out * 1.6], 0, 0, 0), 'box', [0, 0, 0], [0.25, 0.25, out * 3.2],
                 BRASS_DARK, { m: 'metal' });
      }
    };
    return me;
  });

  /* A beacon on a glasshouse ridge: a soft glow while the team's flag is
     home, a turning beam the moment it is not. */
  Rigs.register('beacon', function (spec, ctx) {
    var team = spec.team;
    var neon = team === 'red' ? '#ff6a54' : '#63c0ff';
    var me = { radius: 30, at: spec.p, kind: 'beacon', spin: 0, heat: 0 };
    me.update = function (dt) {
      var mine = ctx.flagSpots ? ctx.flagSpots().filter(function (f) { return f.team === team; })[0] : null;
      var out = mine && mine.state !== 'home';
      me.heat = approach(me.heat, out ? 1 : 0, 3, dt);
      me.spin += dt * (0.6 + me.heat * 5);
    };
    me.draw = function (pen, t) {
      var f = Rigs.frame(spec.p, 0, 1);
      pen.part(f, 'cyl', [0, 0.8, 0], [4.2, 1.6, 4.2], BRASS_DARK, { m: 'metal' });
      pen.part(f, 'cyl', [0, 3.2, 0], [3.4, 3.2, 3.4], neon, { a: 0.35 + 0.3 * me.heat, m: 'neon' });
      pen.part(f, 'cone', [0, 5.6, 0], [4.2, 1.8, 4.2], BRASS, { m: 'metal' });
      var glow = 0.35 + 0.25 * Math.sin(t * 2) * (1 - me.heat);
      pen.part(f, 'sph', [0, 3.2, 0], [2.4, 2.4, 2.4], neon, { m: 'neon', a: glow + me.heat * 0.4 });
      if (me.heat > 0.05) {
        var beam = child(f, [0, 3.2, 0], 0, me.spin, 0);
        pen.part(beam, 'box', [0, 0, 9], [1.6, 1.6, 16], neon, { m: 'neon', a: 0.35 * me.heat });
        pen.part(beam, 'box', [0, 0, -9], [1.6, 1.6, 16], neon, { m: 'neon', a: 0.35 * me.heat });
      }
    };
    return me;
  });

  /* Steam from a boiler chimney: lazy puffs, a rush while the team's flag
     is away (the boilers working overtime). */
  Rigs.register('steam', function (spec, ctx) {
    var n = spec.n || 7, team = spec.team;
    var me = { radius: 30, at: spec.p, kind: 'steam', heat: 0 };
    me.update = function (dt) {
      var mine = team && ctx.flagSpots ? ctx.flagSpots().filter(function (f) { return f.team === team; })[0] : null;
      me.heat = approach(me.heat, mine && mine.state !== 'home' ? 1 : 0, 1.2, dt);
    };
    me.draw = function (pen, t) {
      var rate = 0.22 + me.heat * 0.4;
      for (var i = 0; i < n; i++) {
        var ph = (t * rate + i / n) % 1;
        var size = 2.2 + ph * (6 + me.heat * 5);
        var drift = ph * 6;
        var at = [spec.p[0] + Math.sin(i * 2.3 + t * 0.3) * drift * 0.5 + drift * 0.6,
                  spec.p[1] + ph * (16 + me.heat * 10), spec.p[2] + Math.cos(i * 1.7) * drift * 0.4];
        pen.part(Rigs.frame(at, 0, 1), 'sph', [0, 0, 0], [size, size * 0.85, size], spec.c || '#eef0f2',
                 { a: (1 - ph) * (0.32 + me.heat * 0.2) });
      }
    };
    return me;
  });

  /* A fountain's jet: drops thrown up and out, falling back in rings. */
  Rigs.register('fountain', function (spec) {
    var H = spec.h || 5, W = spec.w || 3;
    var me = { radius: W + 10, at: spec.p, kind: 'fountain' };
    me.draw = function (pen, t) {
      for (var i = 0; i < 16; i++) {
        var ph = (t * 0.9 + i / 16) % 1;
        var a = i * 2.39996;
        var x = Math.sin(a) * W * ph, z = Math.cos(a) * W * ph;
        var y = H * 4 * ph * (1 - ph);
        pen.part(Rigs.frame([spec.p[0] + x, spec.p[1] + y, spec.p[2] + z], 0, 1), 'sph', [0, 0, 0],
                 [0.7, 0.9, 0.7], '#bfe8f8', { a: 0.7 });
      }
      var pulse = 1 + Math.sin(t * 5) * 0.08;
      pen.part(Rigs.frame([spec.p[0], spec.p[1] + H * 0.5, spec.p[2]], 0, 1), 'cyl', [0, 0, 0],
               [0.6, H * pulse, 0.6], '#d8f2ff', { a: 0.6 });
    };
    return me;
  });

  /* Clockwork birds: brass, wound by the key in their backs, beating their
     wings in jerks as they wheel round the orrery. */
  Rigs.register('clockwork_bird', function (spec) {
    var R = spec.r || 60, speed = spec.speed || 0.25, seed = spec.seed || 0;
    var pos = spec.p.slice(), heading = 0;
    var me = { radius: R + 12, at: spec.p, kind: 'clockwork_bird' };
    me.update = function (dt, t) {
      var a = t * speed + seed;
      pos[0] = spec.p[0] + Math.sin(a) * R;
      pos[2] = spec.p[2] + Math.cos(a) * R * (spec.squash || 1);
      pos[1] = spec.p[1] + Math.sin(t * 0.7 + seed) * 4;
      heading = a + (speed > 0 ? Math.PI / 2 : -Math.PI / 2);
      me.at = pos;
    };
    me.draw = function (pen, t) {
      var bank = speed > 0 ? -0.25 : 0.25;
      var f = child(Rigs.frame(pos, heading, spec.s || 1.6), [0, 0, 0], 0, 0, bank);
      pen.part(f, 'sph', [0, 0, 0], [2.2, 2.0, 4.2], BRASS, { m: 'metal' });
      pen.part(f, 'sph', [0, 0.7, 2.2], [1.6, 1.6, 1.6], BRASS_LIGHT, { m: 'metal' });
      pen.part(f, 'cone', [0, 0.6, 3.4], [0.5, 1.2, 0.5], BRASS_DARK, { rx: Math.PI / 2, m: 'metal' });
      pen.part(f, 'sph', [0.6, 0.95, 2.7], [0.35, 0.35, 0.35], '#7ae8ff', { m: 'neon' });
      pen.part(f, 'sph', [-0.6, 0.95, 2.7], [0.35, 0.35, 0.35], '#7ae8ff', { m: 'neon' });
      for (var k = -1; k <= 1; k++) {
        pen.part(f, 'box', [k * 0.5, 0.2, -2.8], [0.7, 0.15, 2.4], BRASS_DARK, { ry: k * 0.3, m: 'metal' });
      }
      var s0 = Math.sin(t * 7 + seed);
      var flap = (s0 > 0 ? 1 : -1) * Math.pow(Math.abs(s0), 0.4) * 0.7;
      for (var side = -1; side <= 1; side += 2) {
        var w = child(f, [side * 0.9, 0.4, 0.2], 0, 0, -side * flap);
        pen.part(w, 'box', [side * 2.6, 0, 0], [5.2, 0.16, 2.2], BRASS_LIGHT, { m: 'metal' });
        if (pen.near) pen.part(w, 'box', [side * 4.2, 0.05, -0.6], [2.0, 0.12, 1.2], BRASS, { m: 'metal' });
      }
      var key = child(f, [0, 1.3, -0.4], 0, t * 4, 0);
      pen.part(key, 'cyl', [0, 0, 0], [0.3, 1.0, 0.3], BRASS_DARK, { m: 'metal' });
      pen.part(key, 'box', [0, 0.6, 0], [1.6, 0.6, 0.2], BRASS_DARK, { m: 'metal' });
    };
    return me;
  });

  /* The observatory's telescope, sweeping the sky -- and swinging round to
     follow whoever is carrying a flag. */
  Rigs.register('telescope', function (spec, ctx) {
    var me = { radius: 40, at: spec.p, kind: 'telescope', az: 0, el: 0.6 };
    me.update = function (dt, t) {
      var spots = ctx.flagSpots ? ctx.flagSpots() : [];
      var target = null;
      spots.forEach(function (f) { if (f.state === 'carried' && f.pos) target = f.pos; });
      var az = 0.35 * Math.sin(t * 0.06), el = 0.62 + 0.18 * Math.sin(t * 0.045);
      if (target) {
        var base = Rigs.frame(spec.p, spec.yaw || 0, 1);
        var d = Rigs.local(base, [target[0] - spec.p[0], target[1] - spec.p[1], target[2] - spec.p[2]]);
        az = clamp(Math.atan2(d[0], d[2]), -1.2, 1.2);
        el = clamp(Math.atan2(d[1], Math.hypot(d[0], d[2])), -0.2, 1.2);
      }
      me.az = Rigs.approachAngle(me.az, az, target ? 1.6 : 0.4, dt);
      me.el = approach(me.el, el, target ? 1.6 : 0.4, dt);
    };
    me.draw = function (pen) {
      var f = child(Rigs.frame(spec.p, spec.yaw || 0, 1), [0, 0, 0], -me.el, me.az, 0);
      var L = spec.len || 30;
      pen.part(f, 'cyl', [0, 0, L * 0.35], [5, L, 5], '#e8e4dc', { rx: Math.PI / 2 });
      pen.part(f, 'cyl', [0, 0, L * 0.85], [6, 1.6, 6], BRASS, { rx: Math.PI / 2, m: 'metal' });
      pen.part(f, 'cyl', [0, 0, L * 0.86], [4.4, 0.4, 4.4], '#7ac8ff', { rx: Math.PI / 2, m: 'neon', a: 0.7 });
      pen.part(f, 'cyl', [3.4, 2.2, L * 0.4], [1.4, L * 0.4, 1.4], '#3a3a40', { rx: Math.PI / 2 });
      pen.part(f, 'sph', [0, 0, 0], [7, 7, 7], '#5a5a60', { m: 'metal' });
    };
    return me;
  });

  /* Fireflies about the topiary at dusk. */
  Rigs.register('fireflies', function (spec) {
    var n = spec.n || 10, R = spec.r || 20, seed = spec.seed || 1;
    var me = { radius: R + 8, at: spec.p, kind: 'fireflies' };
    me.draw = function (pen, t) {
      for (var i = 0; i < n; i++) {
        var glow = Math.pow(Math.max(0, Math.sin(t * (1.3 + i * 0.07) + i * 2.1)), 3);
        if (glow < 0.05) continue;
        var tt = t * 0.18;
        var at = [spec.p[0] + R * wander(tt, seed + i * 3.1), spec.p[1] + 2 + 3 * wander(tt * 1.4, seed + i),
                  spec.p[2] + R * wander(tt * 0.9, seed + i * 5.7)];
        pen.part(Rigs.frame(at, 0, 1), 'sph', [0, 0, 0], [0.5, 0.5, 0.5], '#e8ff7a', { m: 'neon', a: glow });
        pen.part(Rigs.frame(at, 0, 1), 'sph', [0, 0, 0], [1.6, 1.6, 1.6], '#d8ff6a', { m: 'neon', a: glow * 0.18 });
      }
    };
    return me;
  });

  /* The sky at twilight: stars coming out, twinkling, and now and then
     one falling. */
  Rigs.register('starfield', function (spec) {
    var n = spec.n || 80, R = spec.r || 700, seed = spec.seed || 7;
    var stars = [];
    for (var i = 0; i < n; i++) {
      var az = hash(i * 3.1 + seed) * TAU, el = 0.25 + hash(i * 7.7 + seed) * 1.15;
      stars.push([Math.cos(el) * Math.sin(az) * R, Math.sin(el) * R * 0.6 + R * 0.25,
                  Math.cos(el) * Math.cos(az) * R, 2 + hash(i * 1.3) * 3.5, hash(i * 9.1) * 6]);
    }
    var me = { radius: R * 2, at: spec.p, kind: 'starfield' };
    me.draw = function (pen, t) {
      for (var i = 0; i < stars.length; i++) {
        var st = stars[i];
        var tw = 0.55 + 0.45 * Math.sin(t * (0.8 + (i % 5) * 0.3) + st[4]);
        pen.part(Rigs.frame([spec.p[0] + st[0], spec.p[1] + st[1], spec.p[2] + st[2]], 0, 1), 'sph',
                 [0, 0, 0], [st[3], st[3], st[3]], '#fff6e0', { m: 'neon', a: 0.5 + 0.5 * tw });
      }
      var slot = Math.floor(t / 9), into = t - slot * 9;
      if (hash(slot + seed) < 0.45 && into < 1.1) {
        var k = into / 1.1;
        var a0 = hash(slot * 2.7) * TAU, h0 = R * (0.55 + hash(slot * 5.3) * 0.25);
        var x = Math.sin(a0) * R * 0.8 + k * 260, z = Math.cos(a0) * R * 0.8, y = h0 - k * 140;
        var head = [spec.p[0] + x, spec.p[1] + y, spec.p[2] + z];
        var tail = [head[0] - 70, head[1] + 38, head[2]];
        pen.rod(tail, head, 3, '#fff6e0', { m: 'neon', a: Math.sin(k * Math.PI) * 0.9 });
      }
    };
    return me;
  });

  /* A moon round a planet on one of the orrery's decks. */
  Rigs.register('moonlet', function (spec) {
    var me = { radius: (spec.r || 8) + 4, at: spec.p, kind: 'moonlet' };
    me.draw = function (pen, t) {
      var f = child(Rigs.frame(spec.p, t * TAU / (spec.period || 9), 1), [0, 0, 0], spec.tilt || 0.3, 0, 0);
      pen.part(f, 'sph', [0, 0, spec.r || 8], [spec.size || 1.8, spec.size || 1.8, spec.size || 1.8],
               spec.c || '#d8d4c8');
      if (pen.near) {
        pen.part(f, 'torus', [0, 0, 0], [(spec.r || 8) * 2, 0.4, (spec.r || 8) * 2], BRASS_DARK,
                 { m: 'metal', a: 0.5 });
      }
    };
    return me;
  });

  global.BlackoutRelayRigs = true;
})(window);
