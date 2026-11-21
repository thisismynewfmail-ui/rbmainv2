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
  function drawGear(pen, f, r, n, th, colour, angle, coarse) {
    var g = child(f, [0, 0, 0], 0, angle, 0);
    pen.part(g, 'cyl', [0, 0, 0], [r * 2 - 0.2, th, r * 2 - 0.2], colour, { m: 'metal' });
    pen.part(g, 'cyl', [0, 0, 0], [r * 0.5, th + 0.5, r * 0.5], BRASS_DARK, { m: 'metal' });
    if (!pen.near || coarse) return;
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
    var far = spec.far || 150;
    me.draw = function (pen) {
      for (var i = 0; i < gears.length; i++) {
        var g = gears[i];
        var at = [spec.p[0] + g[0], spec.p[1] + g[1], spec.p[2] + g[2]];
        var d = pen.away(at);
        if (d > far) continue;            // (down a tunnel: out of sight anyway)
        drawGear(pen, axisFrame(at, spec.axis), g[3], g[4], spec.th || 0.8,
                 g[6] || (i % 2 ? BRASS_LIGHT : BRASS),
                 (g[5] || 1) * me.spin * r0 / g[3] + (g[7] || 0), d > 55);
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
        if (!pen.near && k % 3) continue;
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
        az = clamp(Math.atan2(d[0], d[2]), -0.55, 0.55);
        el = clamp(Math.atan2(d[1], Math.hypot(d[0], d[2])), 0.12, 1.1);
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

  /* A gas lamp's flame: a warm halo that breathes and gutters. */
  Rigs.register('gaslight', function (spec) {
    var seed = spec.seed || 0;
    var me = { radius: 8, at: spec.p, kind: 'gaslight' };
    me.draw = function (pen, t) {
      var f = 0.75 + 0.15 * Math.sin(t * 7.3 + seed) + 0.1 * Math.sin(t * 17.1 + seed * 3);
      if (hash(Math.floor(t * 6) + seed * 11) < 0.03) f *= 0.55;
      pen.part(Rigs.frame(spec.p, 0, 1), 'sph', [0, 0, 0], [5 * f, 4 * f, 5 * f], '#ffd27a',
               { m: 'neon', a: 0.16 * f });
      pen.part(Rigs.frame(spec.p, 0, 1), 'sph', [0, 0, 0], [1.4, 1.6, 1.4], '#fff0c0',
               { m: 'neon', a: 0.6 + 0.3 * f });
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

  // ==================================================== Snowglobe Hollow
  if (GA) {
    GA.register('br_musicbox', function (vol) {
      [1047, 1319, 1568, 2093, 1976, 1568, 1319, 1568].forEach(function (f, i) {
        this.later(i * 190, function () {
          this.tone({ type: 'sine', freq: f, dur: 0.5, gain: 0.035 * vol });
          this.tone({ type: 'sine', freq: f * 2, dur: 0.25, gain: 0.008 * vol });
        });
      }, this);
    });
    GA.register('br_whistle', function (vol) {
      this.tone({ type: 'sine', freq: 880, freqEnd: 860, dur: 0.7, gain: 0.05 * vol });
      this.tone({ type: 'sine', freq: 1108, freqEnd: 1090, dur: 0.7, gain: 0.04 * vol });
      this.noise({ filter: 'bandpass', freq: 2400, dur: 0.6, gain: 0.02 * vol });
    });
    GA.register('br_rumble', function (vol) {
      this.noise({ filter: 'lowpass', freq: 200, freqEnd: 60, dur: 2.6, gain: 0.22 * vol });
      this.tone({ type: 'sawtooth', freq: 38, freqEnd: 26, dur: 2.2, gain: 0.05 * vol });
      this.later(300, function () { this.noise({ filter: 'bandpass', freq: 900, freqEnd: 300, dur: 1.6, gain: 0.05 * vol }); });
    });
  }

  /* The globe's glass, curving up and over: one great ellipsoid drawn
     inside out (a mirrored scale turns its inner face towards you), with
     the room's light sliding over it. */
  Rigs.register('glass_dome', function (spec) {
    var hx = spec.hx || 300, hz = spec.hz || 200, H = spec.h || 160;
    var me = { radius: 4000, at: spec.p, kind: 'glass_dome' };
    me.draw = function (pen, t) {
      var c = spec.p;
      pen.part(Rigs.frame(c, 0, 1), 'sph', [0, 0, 0], [-hx * 2, H * 2, hz * 2], '#d8ecf8',
               { m: 'glass', a: 0.07 });
      // glints: short arcs of light high on the glass, drifting round
      for (var g = 0; g < 2; g++) {
        var el = 0.55 + g * 0.22, az0 = t * 0.012 + g * 2.4;
        var prev = null;
        for (var k = 0; k <= 6; k++) {
          var az = az0 + k * 0.05;
          var pt = [c[0] + hx * Math.cos(el) * Math.sin(az) * 0.995, c[1] + H * Math.sin(el) * 0.995,
                    c[2] + hz * Math.cos(el) * Math.cos(az) * 0.995];
          if (prev) pen.rod(prev, pt, 5 - g * 1.5, '#ffffff', { m: 'neon', a: 0.12 });
          prev = pt;
        }
      }
    };
    return me;
  });

  /* A fire: flames that lick and flicker over the logs, embers going up,
     a glow round it. */
  Rigs.register('hearth_fire', function (spec) {
    var W = spec.w || 5, H = spec.h || 4, n = Math.max(3, Math.min(14, Math.round(W / 1.4)));
    var me = { radius: W + H + 10, at: spec.p, kind: 'hearth_fire' };
    me.draw = function (pen, t) {
      var c = spec.p, f = Rigs.frame(c, spec.yaw || 0, 1);
      if (!spec.big) {
        pen.part(f, 'cyl', [0, H * 0.08, 0], [H * 0.18, W * 0.9, H * 0.18], '#4a2a1a', { rz: Math.PI / 2 });
        pen.part(f, 'cyl', [0, H * 0.14, 0], [H * 0.16, W * 0.8, H * 0.16], '#5a3420', { rz: Math.PI / 2, ry: 0.5 });
      }
      for (var i = 0; i < n; i++) {
        var x = -W / 2 + (i + 0.5) * W / n;
        var lick = 0.55 + 0.25 * Math.sin(t * 7.1 + i * 2.3) + 0.2 * Math.sin(t * 13.7 + i * 5.1);
        var fh = H * lick * (1 - Math.abs(x) / W * 0.8);
        var fw = W / n * 1.5;
        var sway = Math.sin(t * 3.3 + i) * 0.12;
        pen.part(f, 'cone', [x, fh / 2 + H * 0.1, 0], [fw, fh, fw * 0.7], '#ff7a2a',
                 { m: 'neon', a: 0.85, rz: sway });
        pen.part(f, 'cone', [x, fh * 0.32 + H * 0.1, 0.1], [fw * 0.55, fh * 0.6, fw * 0.4], '#ffd65a',
                 { m: 'neon', a: 0.9, rz: sway });
      }
      for (var e = 0; e < (spec.big ? 14 : 5); e++) {
        var ph = (t * 0.6 + e / (spec.big ? 14 : 5)) % 1;
        var ex = (hash(e * 3.7) - 0.5) * W + Math.sin(t * 2 + e) * W * 0.05;
        pen.part(f, 'sph', [ex, H * 0.2 + ph * H * 1.6, Math.sin(e) * W * 0.05],
                 [W * 0.012 + 0.2, W * 0.012 + 0.2, W * 0.012 + 0.2], '#ffb040', { m: 'neon', a: 1 - ph });
      }
      var glow = 1 + 0.06 * Math.sin(t * 9.3);
      pen.part(f, 'sph', [0, H * 0.4, 0], [W * 1.6 * glow, H * 1.6 * glow, W * 0.8 * glow], '#ff9a40',
               { m: 'neon', a: 0.08 });
    };
    return me;
  });

  /* A bell in its belfry: still, until a minute of the round runs out or
     somebody captures -- then it swings and tolls. */
  Rigs.register('church_bell', function (spec, ctx) {
    var S = spec.s || 1;
    var me = { radius: 16 * S, at: spec.p, kind: 'church_bell', rung: -100, tolls: 0 };
    me.event = function (kind) {
      if (kind === 'flag_capture') me.rung = Rigs.clock();
    };
    me.update = function (dt, t) {
      var st = ctx.round ? ctx.round() : null;
      if (st && typeof st.time_left === 'number') {
        var minute = Math.ceil(st.time_left / 60);
        if (me.minute !== undefined && minute < me.minute) me.rung = t;
        me.minute = minute;
      }
      var age = t - me.rung;
      var beat = Math.floor(age / 0.8);
      if (age >= 0 && age < 4 && beat !== me.beat) {
        me.beat = beat;
        if (ctx.sound) ctx.sound('br_toll', spec.p, 1.2);
      }
    };
    me.draw = function (pen, t) {
      var age = t - me.rung;
      var swing = age >= 0 && age < 5.5 ? Math.sin(age * TAU / 1.6) * 0.7 * Math.max(0, 1 - age / 5.5) : 0;
      var base = Rigs.frame(spec.p, spec.yaw || 0, S);
      pen.part(base, 'box', [0, 0.4, 0], [8, 0.8, 0.9], '#4e3220');
      var bell = child(base, [0, 0, 0], swing, 0, 0);
      pen.part(bell, 'cyl', [0, -0.8, 0], [2.0, 1.2, 2.0], '#b8902e', { m: 'metal' });
      pen.part(bell, 'cone', [0, -2.4, 0], [4.6, 3.6, 4.6], '#c8a040', { m: 'metal' });
      pen.part(bell, 'cyl', [0, -4.2, 0], [5.0, 0.6, 5.0], '#a8822a', { m: 'metal' });
      var clap = child(bell, [0, -1.4, 0], -swing * 0.6, 0, 0);
      pen.part(clap, 'box', [0, -1.4, 0], [0.3, 2.6, 0.3], '#3a3a3a');
      pen.part(clap, 'sph', [0, -3.0, 0], [0.9, 0.9, 0.9], '#3a3a3a', { m: 'metal' });
    };
    return me;
  });

  /* The carousel: painted horses rising and falling on their gilded poles
     under a striped canopy, round and round, its rim twinkling -- and a
     music box, if you are near enough to hear it. */
  Rigs.register('carousel', function (spec, ctx) {
    var R = spec.r || 11, H = spec.h || 11;
    var SADDLES = ['#c42b20', '#2a6aa8', '#f2c21e', '#2a8a4a', '#8a3ab8', '#ffffff'];
    var me = { radius: R + H + 8, at: spec.p, kind: 'carousel', spin: 0, tuneAt: -10 };
    me.update = function (dt, t) {
      me.spin += dt * 0.38;
      var v = ctx.viewer ? ctx.viewer() : null;
      if (v && dist(v.eye, spec.p) < 70 && t - me.tuneAt > 1.65) {
        me.tuneAt = t;
        if (ctx.sound) ctx.sound('br_musicbox', spec.p, 1.6);
      }
    };
    function horse(pen, f, colour, saddle, t, k) {
      var gallop = Math.sin(t * 5 + k);
      pen.part(f, 'rbox', [0, 0, 0], [1.7, 1.9, 4.6], colour);
      pen.part(f, 'rbox', [0, 1.4, 2.0], [1.0, 2.2, 1.3], colour, { rx: -0.5 });
      pen.part(f, 'rbox', [0, 2.6, 2.9], [1.1, 1.3, 2.0], colour, { rx: 0.25 });
      pen.part(f, 'box', [0, 2.3, 1.7], [0.4, 2.2, 1.6], '#e8c050', { rx: -0.5 });
      pen.part(f, 'box', [0, 1.05, -0.2], [1.9, 0.4, 1.8], saddle);
      pen.part(f, 'cone', [0, 0.1, -2.9], [0.8, 2.2, 0.8], '#e8c050', { rx: -2.3 });
      for (var side = -1; side <= 1; side += 2) {
        pen.part(f, 'box', [side * 0.55, -1.6, 1.5], [0.4, 2.2, 0.4], colour, { rx: -0.6 - gallop * 0.3 });
        pen.part(f, 'box', [side * 0.55, -1.6, -1.6], [0.4, 2.2, 0.4], colour, { rx: 0.4 + gallop * 0.3 });
        if (pen.near) pen.part(f, 'sph', [side * 0.5, 3.1, 3.4], [0.3, 0.3, 0.3], '#1b1b1b');
      }
    }
    me.draw = function (pen, t) {
      var c = spec.p;
      var top = Rigs.frame([c[0], c[1] + H, c[2]], me.spin, 1);
      pen.part(top, 'cone', [0, 3.2, 0], [R * 2.3, 6.4, R * 2.3], '#f8f2e8');
      // red stripes down the canopy, lying on the cone (its slope, half way
      // up, a hair proud of it)
      var rc = R * 1.15, hc = 6.4, slope = Math.atan2(hc, rc), run = Math.hypot(rc, hc);
      for (var s2 = 0; s2 < 8; s2++) {
        var a = s2 * TAU / 8;
        pen.part(child(top, [0, 0, 0], 0, a, 0), 'box',
                 [0, hc / 2 + 0.2 * Math.cos(slope), rc / 2 + 0.2 * Math.sin(slope)],
                 [1.8, 0.3, run], '#d8322a', { rx: slope });
      }
      pen.part(top, 'cyl', [0, -0.2, 0], [R * 2.32, 1.4, R * 2.32], '#d8322a');
      pen.part(top, 'sph', [0, 7.0, 0], [2.2, 2.2, 2.2], '#e8c050', { m: 'metal' });
      for (var l = 0; l < 20; l++) {
        var la = l * TAU / 20;
        var on = Math.sin(t * 4 + l * 1.3) > -0.2;
        pen.part(top, 'sph', [Math.sin(la) * R * 1.16, -0.2, Math.cos(la) * R * 1.16], [0.7, 0.7, 0.7],
                 on ? '#fff2b0' : '#c8a060', { m: on ? 'neon' : '' });
      }
      for (var k = 0; k < 6; k++) {
        var ha = me.spin + k * TAU / 6;
        var x = c[0] + Math.sin(ha) * R * 0.72, z = c[2] + Math.cos(ha) * R * 0.72;
        var bob = Math.sin(t * 2.2 + k * 1.7) * 1.2;
        pen.part(Rigs.frame([x, c[1] + H / 2, z], 0, 1), 'cyl', [0, 0, 0], [0.35, H, 0.35], '#e8c050',
                 { m: 'metal' });
        horse(pen, Rigs.frame([x, c[1] + 4.6 + bob, z], ha + Math.PI / 2, 1),
              k % 2 ? '#f8f4ec' : '#c8a070', SADDLES[k], t, k);
      }
    };
    return me;
  });

  /* The toy train, round and round the square on its loop: an engine
     puffing smoke, a wagon of presents or three, a caboose.  It whistles
     as it passes you, and goes faster while a flag is out. */
  Rigs.register('toy_train', function (spec, ctx) {
    var hx = spec.hx || 70, hz = spec.hz || 60, R = spec.cr || 10, cars = spec.cars || 4;
    var lx = 2 * (hx - R), lz = 2 * (hz - R), arc = Math.PI * R / 2;
    var L = 2 * lx + 2 * lz + 4 * arc;
    var me = { radius: Math.max(hx, hz) + 20, at: spec.p, kind: 'toy_train', s: 0, rate: 1, whistleAt: -20 };
    // the loop as nine pieces, anticlockwise seen from above, from the
    // middle of the south run: straight, corner, straight, corner...
    var SEGS = [
      { l: 1, x: 0, z: -hz, dx: 1, dz: 0, len: hx - R },
      { a: 1, cx: hx - R, cz: -hz + R, a0: -Math.PI / 2 },
      { l: 1, x: hx, z: -hz + R, dx: 0, dz: 1, len: lz },
      { a: 1, cx: hx - R, cz: hz - R, a0: 0 },
      { l: 1, x: hx - R, z: hz, dx: -1, dz: 0, len: lx },
      { a: 1, cx: -hx + R, cz: hz - R, a0: Math.PI / 2 },
      { l: 1, x: -hx, z: hz - R, dx: 0, dz: -1, len: lz },
      { a: 1, cx: -hx + R, cz: -hz + R, a0: Math.PI },
      { l: 1, x: -hx + R, z: -hz, dx: 1, dz: 0, len: hx - R }
    ];
    /* [x, z, heading] at distance d round the loop. */
    function at(d) {
      d = ((d % L) + L) % L;
      for (var i = 0; i < SEGS.length; i++) {
        var sg = SEGS[i], len = sg.l ? sg.len : arc;
        if (d <= len || i === SEGS.length - 1) {
          if (sg.l) return [sg.x + sg.dx * d, sg.z + sg.dz * d, Math.atan2(sg.dx, sg.dz)];
          var th = sg.a0 + d / R;
          return [sg.cx + Math.cos(th) * R, sg.cz + Math.sin(th) * R,
                  Math.atan2(-Math.sin(th), Math.cos(th))];
        }
        d -= len;
      }
      return [0, -hz, Math.PI / 2];
    }
    me.event = function (kind) {
      if (kind === 'flag_take' && ctx.sound) ctx.sound('br_whistle', [spec.p[0], spec.p[1], spec.p[2] - hz], 1.5);
    };
    me.update = function (dt, t) {
      var out = ctx.flagSpots && ctx.flagSpots().some(function (f) { return f.state !== 'home'; });
      me.rate = approach(me.rate, out ? 1.8 : 1, 1, dt);
      if (!me.started) { me.s = (t * (spec.speed || 9)) % L; me.started = true; }
      me.s += dt * (spec.speed || 9) * me.rate;
      var head = at(me.s);
      me.head = [spec.p[0] + head[0], spec.p[1], spec.p[2] + head[1]];
      var v = ctx.viewer ? ctx.viewer() : null;
      if (v && dist(v.eye, me.head) < 34 && t - me.whistleAt > 14) {
        me.whistleAt = t;
        if (ctx.sound) ctx.sound('br_whistle', me.head, 1.2);
      }
    };
    function wheels(pen, f, n, t) {
      for (var w = 0; w < n; w++) {
        var z = -2.6 + w * 5.2 / Math.max(1, n - 1);
        for (var side = -1; side <= 1; side += 2) {
          var wf = child(f, [side * 1.9, 0.9, z], t * 6, 0, Math.PI / 2);
          pen.part(wf, 'cyl', [0, 0, 0], [1.8, 0.5, 1.8], '#c42b20');
          if (pen.near) pen.part(wf, 'box', [0, 0.28, 0], [1.6, 0.1, 0.3], '#e8c050');
        }
      }
    }
    me.draw = function (pen, t) {
      var c = spec.p;
      for (var k = 0; k <= cars; k++) {
        var p = at(me.s - k * 9.5);
        var f = Rigs.frame([c[0] + p[0], c[1], c[2] + p[1]], p[2], 1);
        if (k === 0) {
          pen.part(f, 'box', [0, 2.2, -0.4], [3.6, 1.4, 7.6], '#1e1e24');
          pen.part(f, 'cyl', [0, 3.8, 1.2], [3.0, 5.0, 3.0], '#2a6a3a', { rx: Math.PI / 2 });
          pen.part(f, 'cyl', [0, 3.8, 3.75], [2.4, 0.3, 2.4], '#e8c050', { rx: Math.PI / 2, m: 'metal' });
          pen.part(f, 'box', [0, 4.4, -2.6], [3.6, 3.8, 2.8], '#c42b20');
          pen.part(f, 'box', [0, 6.5, -2.6], [4.2, 0.4, 3.4], '#1e1e24');
          pen.part(f, 'cyl', [0, 6.2, 2.6], [1.0, 2.0, 1.0], '#1e1e24');
          pen.part(f, 'cyl', [0, 7.3, 2.6], [1.6, 0.4, 1.6], '#e8c050', { m: 'metal' });
          pen.part(f, 'sph', [0, 4.9, 1.2], [1.0, 0.8, 1.0], '#e8c050', { m: 'metal' });
          pen.part(f, 'box', [0, 1.4, 3.9], [3.2, 1.2, 0.8], '#c42b20', { rx: 0.5 });
          pen.part(f, 'sph', [0, 3.8, 3.95], [0.9, 0.9, 0.4], '#fff2b0', { m: 'neon' });
          for (var puff = 0; puff < 4; puff++) {
            var ph = (t * 1.3 + puff / 4) % 1;
            var back = ph * 6 * me.rate;
            pen.part(f, 'sph', [Math.sin(puff * 2) * ph, 8.0 + ph * 5, 2.6 - back],
                     [1.4 + ph * 2.6, 1.2 + ph * 2.2, 1.4 + ph * 2.6], '#f4f6f8', { a: 0.55 * (1 - ph) });
          }
          wheels(pen, f, 3, t * me.rate);
        } else if (k === cars) {
          pen.part(f, 'box', [0, 2.2, 0], [3.6, 1.2, 7.0], '#1e1e24');
          pen.part(f, 'box', [0, 4.2, 0], [3.4, 2.8, 6.2], '#c42b20');
          pen.part(f, 'box', [0, 5.8, 0], [4.0, 0.4, 7.0], '#8a1a12');
          pen.part(f, 'box', [0, 6.6, 0], [2.0, 1.2, 2.6], '#c42b20');
          pen.part(f, 'box', [0, 4.6, 3.12], [1.6, 1.2, 0.1], '#fff2b0', { m: 'neon' });
          wheels(pen, f, 2, t * me.rate);
        } else {
          pen.part(f, 'box', [0, 2.2, 0], [3.6, 1.2, 7.0], '#1e1e24');
          pen.part(f, 'box', [0, 3.6, 0], [3.6, 1.6, 7.0], k % 2 ? '#2a6aa8' : '#2a6a3a');
          var gifts = [['#c42b20', '#f2c21e'], ['#f2c21e', '#c42b20'], ['#ffffff', '#2a8a4a']];
          for (var g = 0; g < 2; g++) {
            var gc = gifts[(k + g) % 3];
            var gz = -1.6 + g * 3.2, gs = 2.0 + ((k + g) % 2) * 0.5;
            pen.part(f, 'box', [0, 4.4 + gs / 2, gz], [gs, gs, gs], gc[0]);
            if (pen.near) {
              pen.part(f, 'box', [0, 4.4 + gs / 2, gz], [gs + 0.08, gs + 0.08, 0.4], gc[1]);
              pen.part(f, 'box', [0, 4.4 + gs + 0.25, gz], [0.9, 0.5, 0.9], gc[1]);
            }
          }
          wheels(pen, f, 2, t * me.rate);
        }
      }
    };
    return me;
  });

  /* A skater: a little blocky person in a bobble hat and a scarf, gliding
     figures of eight across the pond, arms out, leaning into the turns --
     and now and then a spin where the eight crosses itself. */
  Rigs.register('skater', function (spec) {
    var rx = spec.rx || 30, rz = spec.rz || 12, seed = spec.seed || 0, speed = spec.speed || 0.35;
    var colour = spec.c || '#c42b20';
    var me = { radius: Math.max(rx, rz) + 10, at: spec.p, kind: 'skater' };
    function place(a) {
      return [spec.p[0] + rx * Math.sin(a), spec.p[2] + rz * Math.sin(a) * Math.cos(a) * 2];
    }
    me.draw = function (pen, t) {
      var a = t * speed + seed;
      var p0 = place(a), p1 = place(a + 0.02), p2 = place(a + 0.04);
      var heading = Math.atan2(p1[0] - p0[0], p1[1] - p0[1]);
      var heading2 = Math.atan2(p2[0] - p1[0], p2[1] - p1[1]);
      var turn = heading2 - heading;
      while (turn > Math.PI) turn -= TAU;
      while (turn < -Math.PI) turn += TAU;
      var lean = clamp(-turn * 18, -0.35, 0.35);
      // a spin at the crossing, every other lap
      var lap = a / TAU, frac = lap - Math.floor(lap);
      var spin = (Math.floor(lap) % 2 === 0 && Math.abs(frac - 0.5) < 0.04) ? (frac - 0.46) / 0.08 * TAU * 2 : 0;
      var f = child(Rigs.frame([p0[0], spec.p[1], p0[1]], heading + spin, spec.s || 1), [0, 0, 0], 0.12, 0, lean);
      var stride = Math.sin(t * 4.2 + seed);
      for (var side = -1; side <= 1; side += 2) {
        var leg = child(f, [side * 0.55, 2.4, 0], 0, 0, side * (0.08 + Math.max(0, stride * side) * 0.35));
        pen.part(leg, 'rlimb', [0, -1.1, 0], [0.9, 2.2, 0.9], '#2a2a3a');
        pen.part(leg, 'box', [0, -2.35, 0.2], [0.3, 0.25, 2.2], '#d8dce4', { m: 'metal' });
      }
      pen.part(f, 'rbox', [0, 3.6, 0], [2.0, 2.4, 1.1], colour);
      for (var arm = -1; arm <= 1; arm += 2) {
        var sh = child(f, [arm * 1.15, 4.4, 0], 0.2, 0, arm * 1.2);
        pen.part(sh, 'rlimb', [0, -1.0, 0], [0.8, 2.0, 0.8], colour);
        pen.part(sh, 'sph', [0, -2.1, 0], [0.7, 0.7, 0.7], '#f5cd30');
      }
      pen.part(f, 'rhead', [0, 5.6, 0], [1.6, 1.6, 1.6], '#f5cd30');
      pen.part(f, 'box', [0, 4.85, 0], [1.9, 0.5, 1.3], '#f2f2f2');
      pen.part(f, 'box', [0.5, 4.3, -0.7], [0.5, 1.2, 0.2], '#f2f2f2', { rz: 0.2 });
      pen.part(f, 'cone', [0, 6.7, 0], [1.6, 1.2, 1.6], colour);
      pen.part(f, 'sph', [0, 7.35, 0], [0.6, 0.6, 0.6], '#ffffff');
      if (pen.near) {
        pen.part(f, 'box', [-0.3, 5.75, 0.81], [0.18, 0.22, 0.05], '#1b1b1b');
        pen.part(f, 'box', [0.3, 5.75, 0.81], [0.18, 0.22, 0.05], '#1b1b1b');
      }
    };
    return me;
  });

  /* The eye at the glass: now and then whoever owns the globe leans in to
     look -- at the flag carrier, if there is one, or whoever is nearest --
     blinks, and goes away again. */
  Rigs.register('giant_eye', function (spec, ctx) {
    var S = spec.s || 1, EVERY = spec.every || 47, STAY = 15;
    var me = { radius: 400, at: spec.p, kind: 'giant_eye', lx: 0, ly: 0, open: 1 };
    me.update = function (dt, t) {
      var slot = Math.floor(t / EVERY), into = t - slot * EVERY;
      var visit = hash(slot * 1.9 + 4) < 0.7;
      var k = !visit ? 0 : (into < 2 ? into / 2 : (into < STAY ? 1 : (into < STAY + 2.5 ? 1 - (into - STAY) / 2.5 : 0)));
      me.k = k * k * (3 - 2 * k);
      var target = null;
      var spots = ctx.flagSpots ? ctx.flagSpots() : [];
      spots.forEach(function (f) { if (f.state === 'carried' && f.pos) target = f.pos; });
      if (!target && ctx.players) {
        var best = null, bd = 1e9;
        ctx.players().forEach(function (p) {
          var d = dist(p.pos, spec.p);
          if (d < bd) { bd = d; best = p.pos; }
        });
        target = best;
      }
      var lx = Math.sin(t * 0.4) * 0.6, ly = Math.sin(t * 0.27) * 0.3;
      if (target) {
        var base = Rigs.frame(spec.p, spec.yaw || 0, 1);
        var d2 = Rigs.local(base, [target[0] - spec.p[0], target[1] - spec.p[1], target[2] - spec.p[2]]);
        lx = clamp(Math.atan2(d2[0], Math.max(1, d2[2])) * 1.6, -1, 1);
        ly = clamp(Math.atan2(d2[1], Math.hypot(d2[0], d2[2])) * 1.6, -1, 1);
      }
      me.lx = approach(me.lx, lx, 3, dt);
      me.ly = approach(me.ly, ly, 3, dt);
      var blink = hash(Math.floor(t * 1.7) + 5) < 0.08 || (into > 2 && into < 2.25);
      me.open = approach(me.open, blink ? 0 : 1, blink ? 30 : 10, dt);
    };
    me.draw = function (pen) {
      if (!me.k || me.k < 0.01) return;
      var slide = (1 - me.k) * 260 * S;
      var f = Rigs.frame([spec.p[0], spec.p[1] - slide * 0.3, spec.p[2] - slide], spec.yaw || 0, S);
      pen.part(f, 'sph', [0, 0, -30], [210, 150, 80], '#e8b898');
      pen.part(f, 'sph', [0, 0, 0], [110, 72, 30], '#f6f2ee');
      var ix = me.lx * 22, iy = me.ly * 14;
      pen.part(f, 'sph', [ix, iy, 11], [48, 48, 10], '#4a8ac8');
      pen.part(f, 'sph', [ix * 1.05, iy * 1.05, 14.5], [22, 22, 4], '#0a0a12');
      pen.part(f, 'sph', [ix - 9, iy + 9, 16.5], [9, 9, 2], '#ffffff');
      var lid = 1 - me.open;
      pen.part(f, 'sph', [0, 40 - 38 * lid, 6], [118, 48, 34], '#e0b090');
      pen.part(f, 'sph', [0, -40 + 14 * lid, 6], [118, 34, 30], '#e0b090');
      pen.part(f, 'box', [0, 62, 4], [120, 10, 12], '#6a4a2a', { rz: 0.08 });
    };
    return me;
  });

  /* Every couple of minutes somebody picks the globe up and shakes it: a
     rumble, and for a few seconds the snow goes everywhere. */
  Rigs.register('snow_shake', function (spec, ctx) {
    var EVERY = spec.every || 150, LAST = 8;
    var flakes = [];
    for (var i = 0; i < 160; i++) {
      flakes.push([hash(i * 1.7) * TAU, 4 + hash(i * 3.3) * 42, hash(i * 5.1) * 30 - 8, 0.4 + hash(i * 7.9) * 0.6]);
    }
    var me = { radius: 1e6, at: spec.p, kind: 'snow_shake' };
    me.update = function (dt, t) {
      var slot = Math.floor(t / EVERY), into = t - slot * EVERY;
      me.k = into < LAST ? Math.min(1, into * 2, (LAST - into) / 2) : 0;
      if (into < LAST && slot !== me.slot) {
        me.slot = slot;
        if (ctx.sound) {
          var v = ctx.viewer ? ctx.viewer() : null;
          ctx.sound('br_rumble', v ? v.eye : spec.p, 2.5);
        }
      }
    };
    me.draw = function (pen, t) {
      if (!me.k) return;
      var v = ctx.viewer ? ctx.viewer() : null;
      var e = v ? v.eye : spec.p;
      for (var i = 0; i < flakes.length; i++) {
        var fl = flakes[i];
        var a = fl[0] + t * (1.6 + fl[3]);
        var r = fl[1];
        var y = ((fl[2] + t * (6 + fl[3] * 8)) % 34) - 10;
        pen.part(Rigs.frame([e[0] + Math.sin(a) * r, e[1] + y, e[2] + Math.cos(a) * r], 0, 1), 'sph',
                 [0, 0, 0], [0.5 * fl[3] + 0.2, 0.5 * fl[3] + 0.2, 0.5 * fl[3] + 0.2], '#ffffff',
                 { a: 0.9 * me.k });
      }
    };
    return me;
  });

  // ====================================================== Big Ear Array
  if (GA) {
    GA.register('br_howl', function (vol) {
      this.tone({ type: 'sine', freq: 420, freqEnd: 760, dur: 0.7, gain: 0.06 * vol });
      this.later(650, function () { this.tone({ type: 'sine', freq: 760, freqEnd: 520, dur: 1.4, gain: 0.05 * vol }); });
      this.later(900, function () { this.tone({ type: 'sine', freq: 1520, freqEnd: 1040, dur: 1.0, gain: 0.012 * vol }); });
    });
    GA.register('br_moo', function (vol) {
      this.tone({ type: 'sawtooth', freq: 150, freqEnd: 118, dur: 1.1, gain: 0.04 * vol });
      this.tone({ type: 'sine', freq: 300, freqEnd: 240, dur: 1.0, gain: 0.03 * vol });
    });
    GA.register('br_ufo', function (vol) {
      for (var i = 0; i < 8; i++) {
        this.later(i * 140, function () {
          this.tone({ type: 'sine', freq: 620, freqEnd: 980, dur: 0.14, gain: 0.04 * vol });
        });
      }
      this.tone({ type: 'triangle', freq: 110, dur: 1.2, gain: 0.03 * vol });
    });
  }

  /* Where the array is listening: a carried flag if there is one, the
     light over the corral if not, and a slow sweep of the sky otherwise. */
  function listening(ctx, t) {
    var spots = ctx.flagSpots ? ctx.flagSpots() : [];
    for (var i = 0; i < spots.length; i++) {
      if (spots[i].state === 'carried' && spots[i].pos) return { p: spots[i].pos, flag: true };
    }
    if (ctx.skyTarget) return { p: ctx.skyTarget, flag: false };
    return null;
  }

  /* A radio dish on its yoke: the turntable, the arms, the dish with its
     lip and panel seams, the feed out at the focus on its struts.  It
     slews -- slowly, as heavy things do -- to point at what the array is
     listening to. */
  Rigs.register('radio_dish', function (spec, ctx) {
    var D = spec.d || 24, M = spec.mast || 12, big = !!spec.big;
    var me = { radius: D + M, at: [spec.p[0], spec.p[1] + M, spec.p[2]], kind: 'radio_dish',
               az: (spec.seed || 0) * 0.7, el: 0.9 };
    me.update = function (dt, t) {
      var tg = listening(ctx, t);
      var az = 0.6 * Math.sin(t * 0.02 + 1), el = 1.1 + 0.2 * Math.sin(t * 0.017);
      var pivot = me.at;
      if (tg) {
        var dx = tg.p[0] - pivot[0], dy = tg.p[1] + 3 - pivot[1], dz = tg.p[2] - pivot[2];
        az = Math.atan2(dx, dz);
        el = Math.atan2(dy, Math.hypot(dx, dz));
        if (!tg.flag) el = Math.max(el, 0.5);
      }
      el = clamp(el, 0.35, 1.45);
      var rate = big ? 0.45 : 0.75;
      me.az = Rigs.approachAngle(me.az, az, rate, dt);
      me.el = approach(me.el, el, rate, dt);
      if (tg && tg.flag && !me.wasFlag && big && ctx.sound) ctx.sound('br_whirr', pivot, 2);
      me.wasFlag = tg && tg.flag;
    };
    me.draw = function (pen, t) {
      var base = Rigs.frame(spec.p, me.az, 1);
      pen.part(base, 'cyl', [0, 0.6, 0], [D * 0.32, 1.2, D * 0.32], '#8a8e94', { m: 'metal' });
      var arm = D * 0.24;
      for (var side = -1; side <= 1; side += 2) {
        pen.part(base, 'box', [side * arm, M / 2 + 0.6, 0], [D * 0.05 + 0.6, M, D * 0.1 + 0.8], '#d8dce0',
                 { m: 'metal' });
      }
      pen.part(base, 'box', [0, 1.6, 0], [arm * 2 + 1, 1.4, D * 0.12 + 1], '#c8ccd0', { m: 'metal' });
      var head = child(base, [0, M + 0.6, 0], -me.el, 0, 0);
      pen.part(head, 'cyl', [0, 0, 0], [1.2 + D * 0.03, arm * 2 + 1.2, 1.2 + D * 0.03], '#8a8e94',
               { m: 'metal', rz: Math.PI / 2 });
      pen.part(head, 'box', [0, 0, -D * 0.06], [D * 0.3, D * 0.3, D * 0.1], '#c8ccd0', { m: 'metal' });
      pen.part(head, 'box', [0, -D * 0.12, -D * 0.16], [D * 0.18, D * 0.12, D * 0.12], '#6a6e74', { m: 'metal' });
      // the bowl: a shallow cone opening forward, its lip, its seams
      pen.part(head, 'cone', [0, 0, D * 0.05], [D, D * 0.2, D], '#f2f4f6', { rx: -Math.PI / 2 });
      pen.part(head, 'cyl', [0, 0, D * 0.135], [D * 1.05, 0.5, D * 1.05], '#9aa0a8', { rx: Math.PI / 2, m: 'metal' });
      pen.part(head, 'cone', [0, 0, D * 0.152], [D * 0.62, D * 0.04, D * 0.62], '#dfe3e8', { rx: -Math.PI / 2 });
      if (pen.near) {
        for (var k = 0; k < 8; k++) {
          var a = k * TAU / 8;
          pen.part(child(head, [0, 0, D * 0.152], 0, 0, a), 'box', [0, D * 0.25, 0], [0.18, D * 0.5, 0.06],
                   '#c8ccd0');
        }
      }
      // the feed at the focus on its struts
      var focus = Rigs.point(head, [0, 0, D * 0.48]);
      for (var st = 0; st < (big ? 4 : 3); st++) {
        var sa = st * TAU / (big ? 4 : 3) + 0.4;
        var rim = Rigs.point(head, [Math.sin(sa) * D * 0.46, Math.cos(sa) * D * 0.46, D * 0.14]);
        pen.rod(rim, focus, big ? 0.9 : 0.35, '#b8bcc2', { m: 'metal' });
      }
      var feed = child(head, [0, 0, D * 0.48], 0, 0, 0);
      pen.part(feed, 'cyl', [0, 0, 0], [D * 0.08 + 0.4, D * 0.06 + 0.6, D * 0.08 + 0.4], '#6a6e74',
               { rx: Math.PI / 2, m: 'metal' });
      if (big) {
        pen.part(feed, 'cyl', [0, 0, -1.6], [D * 0.16, 0.6, D * 0.16], '#d8dce0', { rx: Math.PI / 2, m: 'metal' });
        var on = Math.sin(t * 3) > 0;
        pen.part(feed, 'sph', [0, D * 0.06, 0], [1.2, 1.2, 1.2], on ? '#ff3020' : '#5a1a14', { m: on ? 'neon' : '' });
      }
    };
    return me;
  });

  /* A rack of receivers: rows of little lights winking. */
  Rigs.register('rack_lights', function (spec, ctx) {
    var seed = spec.seed || 0;
    var me = { radius: 8, at: spec.p, kind: 'rack_lights' };
    me.draw = function (pen, t) {
      if (!pen.near) return;
      var f = Rigs.frame(spec.p, spec.yaw || 0, 1);
      var busy = listening(ctx, t);
      var speed = busy && busy.flag ? 9 : 3;
      for (var row = 0; row < 6; row++) {
        for (var col = 0; col < 4; col++) {
          var h = hash(row * 7.1 + col * 3.3 + seed + Math.floor(t * speed + col) * 0.37);
          var c = h < 0.5 ? '#3aff6a' : (h < 0.8 ? '#ffb84a' : (h < 0.9 ? '#ff4030' : '#1a2a1e'));
          pen.part(f, 'box', [-2.2 + col * 1.4, -3.0 + row * 1.1, 0.05], [0.5, 0.35, 0.1], c,
                   { m: c === '#1a2a1e' ? '' : 'neon' });
        }
      }
    };
    return me;
  });

  /* A monitor: green phosphor, a trace sweeping across it -- which jumps
     the moment the array picks up a carried flag. */
  Rigs.register('crt', function (spec, ctx) {
    var W = spec.w || 3, seed = spec.seed || 0, big = !!spec.big;
    var me = { radius: W + 6, at: spec.p, kind: 'crt' };
    me.draw = function (pen, t) {
      var f = Rigs.frame(spec.p, spec.yaw || 0, 1);
      var H = W * (big ? 0.34 : 0.75);
      if (!big) pen.part(f, 'box', [0, 0, -W * 0.35], [W + 0.6, H + 0.6, W * 0.7], '#2a2e34');
      pen.part(f, 'box', [0, 0, 0.02], [W, H, 0.08], '#06140c', { m: 'neon' });
      if (!pen.near) return;
      var hit = listening(ctx, t);
      var amp = hit && hit.flag ? 0.42 : 0.12;
      var n = big ? 40 : 12;
      for (var i = 0; i < n; i++) {
        var u = i / (n - 1);
        var x = -W / 2 + 0.2 + u * (W - 0.4);
        var noise = Math.sin(u * 23 + t * 6 + seed) * 0.4 + Math.sin(u * 61 - t * 11) * 0.3;
        var spike = hit && hit.flag ? Math.exp(-Math.pow((u - ((t * 0.4) % 1)) * 9, 2)) * 1.6 : 0;
        var y = clamp((noise * amp + spike * 0.35) * H, -H * 0.45, H * 0.45);
        pen.part(f, 'box', [x, y, 0.1], [W / n * 1.1, Math.max(0.08, W * 0.02), 0.06],
                 hit && hit.flag && spike > 0.3 ? '#ffb84a' : '#7aff9a', { m: 'neon' });
      }
      if (big && hit && hit.flag && Math.sin(t * 8) > 0) {
        pen.part(f, 'box', [W * 0.38, H * 0.36, 0.1], [W * 0.14, H * 0.12, 0.06], '#ff4030', { m: 'neon' });
      }
    };
    return me;
  });

  /* An aviation light on a mast, blinking red into the dark. */
  Rigs.register('blinker', function (spec) {
    var period = spec.period || 1.5, seed = spec.seed || 0, colour = spec.c || '#ff3020';
    var me = { radius: 6, at: spec.p, kind: 'blinker' };
    me.draw = function (pen, t) {
      var ph = ((t + seed) % period) / period;
      var on = ph < 0.3;
      var f = Rigs.frame(spec.p, 0, 1);
      pen.part(f, 'cyl', [0, -0.5, 0], [1.2, 0.6, 1.2], '#3a3a3a');
      pen.part(f, 'sph', [0, 0.1, 0], [1.0, 1.0, 1.0], on ? colour : '#3a1410', { m: on ? 'neon' : '' });
      if (on) pen.part(f, 'sph', [0, 0.1, 0], [4.5, 4.5, 4.5], colour, { m: 'neon', a: 0.18 });
    };
    return me;
  });

  /* A tumbleweed bowling across the field on the wind, bouncing. */
  Rigs.register('tumbleweed', function (spec) {
    var a = spec.p, b = spec.q, R = spec.r || 2, speed = spec.speed || 6, seed = spec.seed || 0;
    var len = dist(a, b);
    var me = { radius: len / 2 + 10, at: [(a[0] + b[0]) / 2, a[1], (a[2] + b[2]) / 2], kind: 'tumbleweed' };
    var dir = [(b[0] - a[0]) / len, (b[2] - a[2]) / len];
    var heading = Math.atan2(dir[0], dir[1]);
    me.draw = function (pen, t) {
      var period = len / speed + 6;
      var ph = ((t + seed * 13) % period) / period * (len / speed + 6);
      var d = ph * speed;
      if (d > len) return;
      var fade = Math.min(1, d / 12, (len - d) / 12);
      var wob = Math.sin(t * 0.7 + seed) * 6;
      var x = a[0] + dir[0] * d + dir[1] * wob, z = a[2] + dir[1] * d - dir[0] * wob;
      var y = a[1] + R + Math.abs(Math.sin(d * 0.21)) * R * 1.2;
      var f = child(Rigs.frame([x, y, z], heading, R * fade), [0, 0, 0], d / R, 0, 0);
      pen.part(f, 'torus', [0, 0, 0], [2, 4, 2], '#a8844c');
      pen.part(f, 'torus', [0, 0, 0], [2, 4, 2], '#9a7a44', { rx: Math.PI / 2 });
      pen.part(f, 'torus', [0, 0, 0], [1.9, 4, 1.9], '#b8945a', { rz: Math.PI / 2 });
      pen.part(f, 'torus', [0, 0, 0], [1.6, 4, 1.6], '#8a6a3c', { rx: 0.8, rz: 0.6 });
    };
    return me;
  });

  /* A coyote on the mesa's rim: watching whoever comes near, and now and
     then lifting its head to howl at the moon. */
  Rigs.register('coyote', function (spec, ctx) {
    var me = { radius: 12, at: spec.p, kind: 'coyote', look: 0, howl: 0 };
    me.update = function (dt, t) {
      var slot = Math.floor(t / 23), into = t - slot * 23;
      var howling = hash(slot + 77) < 0.6 && into < 3.2;
      me.howl = approach(me.howl, howling ? 1 : 0, 4, dt);
      if (howling && slot !== me.slot) {
        me.slot = slot;
        var v = ctx.viewer ? ctx.viewer() : null;
        if (v && dist(v.eye, spec.p) < 300 && ctx.sound) ctx.sound('br_howl', spec.p, 2.2);
      }
      var near = null, nd = 1e9;
      (ctx.players ? ctx.players() : []).forEach(function (p) {
        var d = dist(p.pos, spec.p);
        if (d < nd) { nd = d; near = p; }
      });
      var look = 0;
      if (near && nd < 90) {
        var base = Rigs.frame(spec.p, spec.yaw || 0, 1);
        var l = Rigs.local(base, [near.pos[0] - spec.p[0], 0, near.pos[2] - spec.p[2]]);
        look = clamp(Math.atan2(l[0], l[2]), -1.2, 1.2);
      }
      me.look = Rigs.approachAngle(me.look, look, 3, dt);
    };
    me.draw = function (pen, t) {
      var f = Rigs.frame(spec.p, spec.yaw || 0, spec.s || 1.3);
      var fur = '#8a6a48', light = '#c8b090';
      pen.part(f, 'sph', [0, 1.6, -0.6], [2.4, 2.6, 3.6], fur);
      pen.part(f, 'sph', [0, 2.6, 0.6], [2.0, 2.8, 2.0], fur, { rx: -0.4 });
      pen.part(f, 'sph', [0, 2.6, 1.3], [1.2, 2.0, 0.8], light, { rx: -0.4 });
      for (var side = -1; side <= 1; side += 2) {
        pen.part(f, 'box', [side * 0.5, 0.9, 1.2], [0.4, 1.8, 0.4], fur);
        pen.part(f, 'sph', [side * 1.0, 0.7, -1.4], [1.0, 1.4, 1.8], fur);
      }
      pen.part(f, 'box', [0, 0.5, -2.8], [0.6, 0.6, 2.8], fur, { rx: 0.5 });
      var head = child(f, [0, 4.0, 1.0], -1.0 * me.howl + 0.1, me.look * (1 - me.howl), 0);
      pen.part(head, 'sph', [0, 0.4, 0], [1.6, 1.5, 1.8], fur);
      pen.part(head, 'box', [0, 0.1, 1.4], [0.8, 0.7, 1.6], light);
      pen.part(head, 'sph', [0, 0.3, 2.2], [0.35, 0.3, 0.3], '#1a1a1a');
      for (var e = -1; e <= 1; e += 2) {
        pen.part(head, 'cone', [e * 0.5, 1.6, -0.1], [0.6, 1.2, 0.4], fur, { rz: -e * 0.2 });
      }
    };
    return me;
  });

  /* An old windpump on its tower: the wheel round and round, the tail
     keeping it into the wind, the rod going up and down. */
  Rigs.register('windpump', function (spec) {
    var R = spec.r || 6;
    var me = { radius: R + 30, at: spec.p, kind: 'windpump', spin: 0 };
    me.update = function (dt, t) {
      me.spin += dt * (1.2 + 0.8 * Math.sin(t * 0.13) + 0.4 * Math.sin(t * 0.41));
    };
    me.draw = function (pen, t) {
      var yaw = (spec.yaw || 0) + Math.sin(t * 0.05) * 0.3;
      var f = Rigs.frame(spec.p, yaw, 1);
      pen.part(f, 'box', [0, 0, -2.5], [1.2, 1.2, 6], '#7a7a74', { m: 'metal' });
      pen.part(f, 'box', [0, 0.8, -6.5], [0.2, 4.4, 4.0], '#c8c0a8');
      var wheel = child(f, [0, 0, 1.0], 0, 0, me.spin);
      pen.part(wheel, 'cyl', [0, 0, 0], [1.6, 1.0, 1.6], '#5a5a54', { rx: Math.PI / 2, m: 'metal' });
      pen.part(wheel, 'torus', [0, 0, 0], [R * 2, 1.5, R * 2], '#7a7a74', { rx: Math.PI / 2, m: 'metal' });
      for (var k = 0; k < 16; k++) {
        var a = k * TAU / 16;
        pen.part(child(wheel, [0, 0, 0], 0, 0, a), 'box', [0, R * 0.58, 0], [1.1, R * 0.82, 0.12], '#d8d4c8',
                 { ry: 0.35 });
      }
      var stroke = Math.sin(me.spin) * 0.9;
      pen.part(Rigs.frame(spec.p, 0, 1), 'box', [0, -6 + stroke, 0], [0.3, 10, 0.3], '#5a5a54', { m: 'metal' });
    };
    return me;
  });

  /* A cow: grazing, swishing her tail, mooing now and then -- and, when
     the light over the corral comes for her, floating gently up into it
     and (it always lets her go) back down. */
  Rigs.register('cow', function (spec, ctx) {
    var me = { radius: 30, at: spec.p, kind: 'cow' };
    me.update = function (dt, t) {
      var slot = Math.floor(t / 19);
      if (slot !== me.slot) {
        me.slot = slot;
        if (hash(slot + 9) < 0.35 && ctx.viewer) {
          var v = ctx.viewer();
          if (v && dist(v.eye, spec.p) < 160 && ctx.sound) ctx.sound('br_moo', spec.p, 2);
        }
      }
    };
    me.draw = function (pen, t) {
      var lift = ctx.abduction || 0;
      var y = spec.p[1] + lift * 28 + Math.sin(t * 2) * lift * 0.8;
      var f = child(Rigs.frame([spec.p[0], y, spec.p[2]], (spec.yaw || 0) + lift * t * 0.8, 1), [0, 0, 0],
                    lift * 0.3, 0, lift * 0.2);
      pen.part(f, 'rbox', [0, 4.2, 0], [3.4, 3.0, 6.4], '#f6f6f2');
      if (pen.near) {
        pen.part(f, 'box', [1.72, 4.6, -1.0], [0.1, 1.8, 2.4], '#1b1b1b');
        pen.part(f, 'box', [-1.72, 3.8, 1.2], [0.1, 1.6, 2.0], '#1b1b1b');
        pen.part(f, 'box', [0.4, 5.72, 0.6], [1.6, 0.1, 2.2], '#1b1b1b');
      }
      var graze = lift > 0.05 ? 0 : Math.max(0, Math.sin(t * 0.5)) * 0.9;
      var head = child(f, [0, 5.0, 3.0], 0.2 + graze, Math.sin(t * 0.3) * 0.2, 0);
      pen.part(head, 'rbox', [0, -0.2, 1.4], [2.0, 2.0, 2.6], '#f6f6f2');
      pen.part(head, 'rbox', [0, -0.8, 2.8], [1.8, 1.2, 0.8], '#f0a0a8');
      for (var e = -1; e <= 1; e += 2) {
        pen.part(head, 'box', [e * 1.4, 0.4, 0.8], [1.0, 0.4, 0.6], '#f6f6f2');
        pen.part(head, 'cone', [e * 0.7, 1.2, 0.8], [0.4, 0.8, 0.4], '#e8e0c8');
        if (pen.near) pen.part(head, 'sph', [e * 0.6, 0.2, 2.62], [0.35, 0.35, 0.2], '#1b1b1b');
      }
      for (var lx = -1; lx <= 1; lx += 2) {
        for (var lz = -1; lz <= 1; lz += 2) {
          var dangle = lift * Math.sin(t * 3 + lx + lz) * 0.4;
          pen.part(child(f, [lx * 1.1, 2.8, lz * 2.3], dangle, 0, 0), 'box', [0, -1.4, 0], [0.8, 2.8, 0.8],
                   '#f6f6f2');
        }
      }
      pen.part(f, 'sph', [0, 2.6, -0.6], [1.6, 0.9, 1.6], '#f0a0a8');
      var swish = Math.sin(t * 2.4) * 0.5;
      pen.part(child(f, [0, 5.0, -3.2], 0.3, 0, swish), 'box', [0, -1.6, 0], [0.25, 3.2, 0.25], '#e8e0c8');
    };
    return me;
  });

  /* The moon: big, pale, its seas. */
  Rigs.register('moon', function (spec) {
    var R = spec.r || 40;
    var me = { radius: 1e6, at: spec.p, kind: 'moon' };
    me.draw = function (pen) {
      var f = Rigs.frame(spec.p, Math.atan2(-spec.p[0], -spec.p[2]), 1);
      pen.part(f, 'sph', [0, 0, 0], [R * 2, R * 2, R * 2], '#f2eedc', { m: 'neon' });
      pen.part(f, 'sph', [0, 0, 0], [R * 2.6, R * 2.6, R * 2.6], '#dde4ff', { m: 'neon', a: 0.08 });
      [[0.3, 0.25, 0.32], [-0.2, -0.3, 0.26], [-0.35, 0.3, 0.2], [0.15, -0.1, 0.16]].forEach(function (c) {
        pen.part(f, 'sph', [c[0] * R, c[1] * R, R * 0.92], [c[2] * R * 2, c[2] * R * 2, R * 0.2], '#d0ccbc',
                 { m: 'neon' });
      });
    };
    return me;
  });

  /* The light in the sky: a saucer wandering over the corral, its rim
     lights chasing, a little someone in its dome -- every so often it
     lowers its beam over the cow (and gives her back), and when a flag is
     captured it is off across the sky in a blink.  The array follows it
     when there is no flag to follow. */
  Rigs.register('ufo', function (spec, ctx) {
    var home = spec.p, R = spec.r || 40, cow = spec.cow_p;
    var pos = home.slice();
    var me = { radius: 1e6, at: pos, kind: 'ufo', zip: -100 };
    me.event = function (kind) { if (kind === 'flag_capture') me.zip = Rigs.clock(); };
    me.update = function (dt, t) {
      var x = home[0] + R * Math.sin(t * 0.11), z = home[2] + R * 0.6 * Math.sin(t * 0.17 + 1);
      var y = home[1] + 6 * Math.sin(t * 0.3);
      var slot = Math.floor(t / 71), into = t - slot * 71;
      var abduct = cow && hash(slot + 21) < 0.75 ? (into < 3 ? into / 3 : (into < 14 ? 1 : (into < 17 ? (17 - into) / 3 : 0))) : 0;
      var lift = cow && into > 3 && into < 17 ? Math.sin(Math.min(1, (into - 3) / 11) * Math.PI) : 0;
      if (abduct > 0) {
        var k = abduct * abduct * (3 - 2 * abduct);
        x = x + (cow[0] - x) * k; z = z + (cow[2] - z) * k; y = y + (cow[1] + 48 - y) * k;
        if (into < 0.1 && ctx.sound) ctx.sound('br_ufo', cow, 2.5);
      }
      var zage = t - me.zip;
      if (zage >= 0 && zage < 2.4) {
        var zk = Math.sin(zage / 2.4 * Math.PI);
        x += zk * 260; y += zk * 60;
      }
      pos[0] = x; pos[1] = y; pos[2] = z;
      me.beam = abduct > 0.9 ? 1 : 0;
      ctx.abduction = lift;
      ctx.skyTarget = pos;
    };
    me.draw = function (pen, t) {
      var f = child(Rigs.frame(pos, t * 0.6, 1), [0, 0, 0], Math.sin(t * 0.9) * 0.08, 0, Math.cos(t * 0.7) * 0.08);
      pen.part(f, 'sph', [0, 0, 0], [26, 5, 26], '#c8ccd4', { m: 'metal' });
      pen.part(f, 'sph', [0, -1.2, 0], [14, 3, 14], '#8a8e98', { m: 'metal' });
      pen.part(f, 'sph', [0, 2.6, 0], [10, 7, 10], '#a8f0d8', { m: 'glass', a: 0.45 });
      pen.part(f, 'sph', [0, 2.4, 0], [2.4, 3.0, 2.4], '#7ad85a');
      pen.part(f, 'sph', [-0.6, 3.4, 1.0], [0.8, 1.0, 0.4], '#0a0a0a');
      pen.part(f, 'sph', [0.6, 3.4, 1.0], [0.8, 1.0, 0.4], '#0a0a0a');
      for (var k = 0; k < 12; k++) {
        var a = k * TAU / 12;
        var lit = ((k + Math.floor(t * 8)) % 4) === 0;
        pen.part(f, 'sph', [Math.sin(a) * 11.6, 0.2, Math.cos(a) * 11.6], [1.4, 1.0, 1.4],
                 lit ? '#ffe26a' : '#6a8aff', { m: 'neon' });
      }
      pen.part(f, 'sph', [0, -2.2, 0], [10, 1.4, 10], '#9fe8ff', { m: 'neon', a: 0.5 });
      if (me.beam && cow) {
        var top = [pos[0], pos[1] - 2, pos[2]];
        var h = top[1] - cow[1];
        pen.part(Rigs.frame([top[0], top[1] - h / 2, top[2]], t, 1), 'cone', [0, 0, 0], [26, h, 26], '#b8fff0',
                 { m: 'neon', a: 0.16, rx: Math.PI });
      }
    };
    return me;
  });

  /* Satellites: dots crossing the night, now and then one flaring. */
  Rigs.register('satellites', function (spec) {
    var n = spec.n || 3, R = spec.r || 600;
    var me = { radius: 1e6, at: spec.p, kind: 'satellites' };
    me.draw = function (pen, t) {
      for (var i = 0; i < n; i++) {
        var period = 70 + i * 23;
        var ph = ((t + i * 31) % period) / period;
        var a0 = hash(i * 4.4) * TAU;
        var a = a0 + (ph - 0.5) * 2.6;
        var el = 0.5 + 0.4 * Math.sin(ph * Math.PI);
        var at = [spec.p[0] + Math.sin(a) * Math.cos(el) * R, spec.p[1] + Math.sin(el) * R * 0.7,
                  spec.p[2] + Math.cos(a) * Math.cos(el) * R];
        var flare = Math.abs(ph - 0.5 - i * 0.07) < 0.012 ? 3 : 1;
        pen.part(Rigs.frame(at, 0, 1), 'sph', [0, 0, 0], [2.2 * flare, 2.2 * flare, 2.2 * flare], '#ffffff',
                 { m: 'neon', a: 0.9 });
      }
    };
    return me;
  });

  // ======================================================== Polderhaven
  if (GA) {
    GA.register('br_baa', function (vol) {
      this.tone({ type: 'sawtooth', freq: 330, freqEnd: 300, dur: 0.5, gain: 0.03 * vol });
      for (var i = 0; i < 5; i++) {
        this.later(i * 90, function () { this.tone({ type: 'sine', freq: 640, freqEnd: 600, dur: 0.08, gain: 0.02 * vol }); });
      }
    });
    GA.register('br_quack', function (vol) {
      this.tone({ type: 'square', freq: 520, freqEnd: 380, dur: 0.12, gain: 0.025 * vol });
      this.later(160, function () { this.tone({ type: 'square', freq: 500, freqEnd: 360, dur: 0.12, gain: 0.025 * vol }); });
    });
  }

  /* A windmill's sails: four stocks, the lattice and the cloth on them,
     round and round in the plane in front of the cap; the axle back to
     it.  The great mills fly the team's colours. */
  Rigs.register('windmill_sails', function (spec) {
    var R = spec.r || 20, cloth = spec.c || '#f4f2ea', stripe = spec.stripe || '', rate = spec.rate || 0.6;
    var me = { radius: R + 6, at: spec.p, kind: 'windmill_sails', spin: (spec.seed || 0) * 1.3 };
    me.update = function (dt, t) {
      me.spin += dt * rate * (1 + 0.25 * Math.sin(t * 0.11 + (spec.seed || 0)));
    };
    me.draw = function (pen) {
      var hub = Rigs.frame(spec.p, spec.yaw || 0, 1);
      var axle = spec.axle || R * 0.12;
      pen.part(hub, 'cyl', [0, 0, -axle / 2], [R * 0.06 + 0.4, axle, R * 0.06 + 0.4], '#4a3a2a',
               { rx: Math.PI / 2 });
      pen.part(hub, 'sph', [0, 0, 0.4], [R * 0.1 + 0.6, R * 0.1 + 0.6, R * 0.1 + 0.6], '#3a2a1a');
      for (var k = 0; k < 4; k++) {
        var arm = child(hub, [0, 0, 0.8], 0, 0, me.spin + k * Math.PI / 2);
        pen.part(arm, 'box', [0, R / 2, 0], [R * 0.035 + 0.3, R, R * 0.035 + 0.3], '#4a3a2a');
        pen.part(arm, 'box', [R * 0.11, R * 0.6, 0.15], [R * 0.2, R * 0.74, 0.2], cloth);
        if (stripe) pen.part(arm, 'box', [R * 0.11, R * 0.6, 0.3], [R * 0.06, R * 0.74, 0.1], stripe);
        if (pen.near) {
          for (var b2 = 0; b2 < 7; b2++) {
            pen.part(arm, 'box', [R * 0.11, R * 0.26 + b2 * R * 0.11, 0.32], [R * 0.21, 0.18, 0.1], '#4a3a2a');
          }
        }
      }
    };
    return me;
  });

  /* A drawbridge's counterweight beams on their portal, the chains down
     to the deck swaying. */
  Rigs.register('bascule', function (spec) {
    var W = spec.w || 20;
    var me = { radius: W + 10, at: spec.p, kind: 'bascule' };
    me.draw = function (pen, t) {
      var f = Rigs.frame(spec.p, spec.yaw || 0, 1);
      for (var side = -1; side <= 1; side += 2) {
        var beam = child(f, [side * 6.2, 0.8, 0], 0.18, 0, 0);
        pen.part(beam, 'box', [0, 0, 2], [0.9, 0.9, W * 1.3], '#f4f2ea');
        pen.part(beam, 'box', [0, -0.4, -W * 0.55], [1.6, 2.4, 3.0], '#3a3a40');
        var end = Rigs.point(beam, [0, 0, W * 0.6]);
        var sway = Math.sin(t * 0.9 + side) * 0.3;
        pen.rod(end, [end[0] + sway, spec.p[1] - 12.4, end[2]], 0.25, '#3a3a40', { m: 'metal' });
      }
    };
    return me;
  });

  /* The pumping station's beam engine: the beam rocking on its column,
     the piston rod in and out of the cylinder, the connecting rod driving
     the flywheel round -- faster while a flag is out. */
  Rigs.register('beam_engine', function (spec, ctx) {
    var pv = spec.pivot_p, cy = spec.cyl_p, wh = spec.wheel_p;
    var L = Math.abs(pv[0] - cy[0]);
    var me = { radius: L + 12, at: pv, kind: 'beam_engine', phase: 0, rate: 1 };
    me.update = function (dt) {
      var out = spec.flags && ctx.flagSpots && ctx.flagSpots().some(function (f) { return f.state !== 'home'; });
      me.rate = approach(me.rate, out ? 2.3 : 1, 0.8, dt);
      me.phase += dt * 1.3 * me.rate;
    };
    me.draw = function (pen, t) {
      var ang = Math.sin(me.phase) * 0.22;
      var beam = child(Rigs.frame(pv, 0, 1), [0, 0, 0], 0, 0, ang);
      pen.part(beam, 'box', [0, 0, 0], [2 * L + 4, 1.4, 1.2], '#2a6a4a');
      pen.part(beam, 'box', [0, 0.9, 0], [2 * L, 0.4, 0.6], '#3a8a5a');
      pen.part(Rigs.frame(pv, 0, 1), 'cyl', [0, 0, 0], [1.2, 1.8, 1.2], '#c89a3a', { rx: Math.PI / 2, m: 'metal' });
      var left = Rigs.point(beam, [-(L), 0, 0]);
      var right = Rigs.point(beam, [L, 0, 0]);
      pen.rod(left, [left[0], cy[1], cy[2]], 0.5, '#c8ccd0', { m: 'metal' });
      var rc = 2.2;
      var crank = [wh[0] + Math.cos(me.phase) * rc, wh[1] + Math.sin(me.phase) * rc, wh[2] + 1.4];
      pen.rod(right, crank, 0.6, '#c8ccd0', { m: 'metal' });
      var wf = child(Rigs.frame([wh[0], wh[1], wh[2] + 1.0], 0, 1), [0, 0, 0], Math.PI / 2, 0, 0);
      var spin = child(wf, [0, 0, 0], 0, -me.phase, 0);
      pen.part(spin, 'cyl', [0, 0, 0], [9, 0.6, 9], '#2a2a30', { m: 'metal' });
      for (var k = 0; k < 6; k++) {
        pen.part(spin, 'box', [0, 0.35, 0], [8.4, 0.2, 0.6], '#c89a3a', { ry: k * Math.PI / 6, m: 'metal' });
      }
      pen.part(spin, 'cyl', [0, 0, 0], [1.6, 1.4, 1.6], '#c89a3a', { m: 'metal' });
      if (Math.sin(me.phase) > 0.9) {
        pen.part(Rigs.frame([cy[0] - 1.6, cy[1] + 1.5, cy[2]], 0, 1), 'sph', [0, 0, 0], [1.6, 1.4, 1.6], '#f2f4f6',
                 { a: 0.5 });
      }
    };
    return me;
  });

  /* A stork on its nest: standing, clattering its beak at the sky -- and
     every so often off on a long slow circle round the field. */
  Rigs.register('stork', function (spec, ctx) {
    var seed = spec.seed || 0;
    var me = { radius: 90, at: spec.p, kind: 'stork' };
    function bird(pen, f, flying, t) {
      pen.part(f, 'sph', [0, 0, 0], [1.8, 1.8, 3.4], '#f8f8f4');
      pen.part(f, 'sph', [0, 0.2, -1.6], [1.4, 0.6, 1.6], '#1b1b1b');
      var neck = child(f, [0, 0.6, 1.4], flying ? -1.2 : -0.4, 0, 0);
      pen.part(neck, 'cyl', [0, 1.0, 0], [0.5, 2.2, 0.5], '#f8f8f4');
      var head = child(neck, [0, 2.2, 0], flying ? 1.2 : 0.2 + (Math.sin(t * 9) > 0.7 ? -0.9 : 0), 0, 0);
      pen.part(head, 'sph', [0, 0, 0], [0.8, 0.8, 0.9], '#f8f8f4');
      pen.part(head, 'cone', [0, 0, 1.4], [0.35, 2.0, 0.35], '#e8502a', { rx: Math.PI / 2 });
      if (!flying) {
        for (var leg = -1; leg <= 1; leg += 2) pen.part(f, 'box', [leg * 0.4, -1.8, 0], [0.2, 2.6, 0.2], '#e8502a');
      } else {
        pen.part(f, 'box', [0, -0.2, -3.0], [0.4, 0.2, 2.6], '#e8502a');
      }
      var flap = flying ? Math.sin(t * 3.4) * 0.5 : -1.1;
      for (var side = -1; side <= 1; side += 2) {
        var wing = child(f, [side * 0.8, 0.4, 0], 0, 0, -side * flap);
        pen.part(wing, 'box', [side * (flying ? 3.4 : 0.4), 0, flying ? 0 : -0.2], flying ? [6.4, 0.14, 2.2] : [0.3, 1.6, 2.6], '#f8f8f4');
        if (flying) pen.part(wing, 'box', [side * 5.8, 0.02, -0.4], [2.2, 0.12, 1.8], '#1b1b1b');
      }
    }
    me.draw = function (pen, t) {
      var period = 46, into = (t + seed * 7) % period;
      if (into < 32) {
        var f = Rigs.frame([spec.p[0], spec.p[1] + 2.4, spec.p[2]], Math.sin(t * 0.2 + seed) * 1.2, 1.4);
        bird(pen, f, false, t);
        return;
      }
      var k = (into - 32) / (period - 32);
      var a = k * TAU;
      var rr = 70 * Math.sin(k * Math.PI);
      var pos = [spec.p[0] + Math.sin(a) * rr, spec.p[1] + 2.4 + Math.sin(k * Math.PI) * 30, spec.p[2] + (1 - Math.cos(a)) * rr * 0.6];
      var fwd = [Math.cos(a) * rr * TAU + 1e-3, 0, Math.sin(a) * rr * 0.6 * TAU];
      bird(pen, Rigs.frame(pos, Math.atan2(fwd[0], fwd[2]), 1.4), true, t);
    };
    return me;
  });

  /* A sheep: a cloud of fleece on black legs, grazing, its ears flicking;
     now and then a baa. */
  Rigs.register('sheep', function (spec, ctx) {
    var seed = spec.seed || 0;
    var me = { radius: 10, at: spec.p, kind: 'sheep' };
    me.update = function (dt, t) {
      var slot = Math.floor((t + seed * 5) / 17);
      if (slot !== me.slot) {
        me.slot = slot;
        var v = ctx.viewer ? ctx.viewer() : null;
        if (v && hash(slot + seed) < 0.4 && dist(v.eye, spec.p) < 90 && ctx.sound) ctx.sound('br_baa', spec.p, 2);
      }
    };
    me.draw = function (pen, t) {
      var drift = Math.sin(t * 0.05 + seed) * 4;
      var f = Rigs.frame([spec.p[0] + drift, spec.p[1], spec.p[2] + Math.cos(t * 0.04 + seed) * 3], (spec.yaw || 0) + Math.sin(t * 0.1 + seed) * 0.6, 1);
      [[0, 3.0, 0, 3.6, 2.8, 4.6], [0.8, 3.6, 1.0, 2.6, 2.2, 2.6], [-0.8, 3.6, -1.0, 2.6, 2.2, 2.6],
       [0, 3.9, 0, 2.8, 2.0, 3.0]].forEach(function (b2) {
        pen.part(f, 'sph', [b2[0], b2[1], b2[2]], [b2[3], b2[4], b2[5]], '#f4f2ea');
      });
      for (var lx = -1; lx <= 1; lx += 2) {
        for (var lz = -1; lz <= 1; lz += 2) pen.part(f, 'box', [lx * 0.8, 1.0, lz * 1.4], [0.4, 2.0, 0.4], '#1b1b1b');
      }
      var graze = Math.max(0, Math.sin(t * 0.6 + seed)) * 0.9;
      var head = child(f, [0, 3.6, 2.4], 0.2 + graze, 0, 0);
      pen.part(head, 'rbox', [0, 0, 0.8], [1.2, 1.4, 1.8], '#1b1b1b');
      pen.part(head, 'sph', [0, 0.6, 0.2], [1.4, 0.8, 1.2], '#f4f2ea');
      for (var e = -1; e <= 1; e += 2) {
        var flick = Math.sin(t * 7 + e + seed) > 0.95 ? 0.6 : 0;
        pen.part(child(head, [e * 0.7, 0.3, 0.6], 0, 0, e * (0.5 + flick)), 'box', [e * 0.5, 0, 0], [1.0, 0.25, 0.5], '#1b1b1b');
      }
    };
    return me;
  });

  /* A barge down the canal: low and long, a cabin with a window box, the
     skipper at the tiller, a wake. In at one end, out at the other. */
  Rigs.register('canal_boat', function (spec) {
    var a = spec.p, b = spec.q, speed = spec.speed || 4, seed = spec.seed || 0;
    var len = dist(a, b);
    var heading = Math.atan2(b[0] - a[0], b[2] - a[2]);
    var accent = spec.c || '#c42b20';
    var me = { radius: len / 2 + 20, at: [(a[0] + b[0]) / 2, a[1], (a[2] + b[2]) / 2], kind: 'canal_boat' };
    me.draw = function (pen, t) {
      var d = ((t + seed * 11) * speed) % (len + 40) - 20;
      if (d < -10 || d > len + 10) return;
      var pos = [a[0] + (b[0] - a[0]) * d / len, a[1], a[2] + (b[2] - a[2]) * d / len];
      var f = child(Rigs.frame(pos, heading, 1), [0, 0, 0], Math.sin(t * 1.3) * 0.02, 0, Math.sin(t * 0.9) * 0.03);
      pen.part(f, 'rbox', [0, -0.4, 0], [5.4, 1.6, 22], '#1e1e24');
      pen.part(f, 'box', [0, 0.32, 0], [5.5, 0.3, 22.2], accent);
      pen.part(f, 'cone', [0, -0.4, 11.6], [5.2, 2.2, 1.6], '#1e1e24', { rx: Math.PI / 2 });
      pen.part(f, 'box', [0, 0.9, -4], [4.2, 1.0, 8], '#f4f2ea');
      pen.part(f, 'box', [0, 1.45, -4], [4.6, 0.12, 8.6], '#2a5a3a');
      if (pen.near) {
        for (var w = 0; w < 3; w++) pen.part(f, 'box', [2.12, 0.95, -6.6 + w * 2.6], [0.05, 0.6, 1.4], '#8ac8e8');
        pen.part(f, 'box', [1.6, 1.6, 2.4], [1.0, 0.4, 2.4], '#8a5a3a');
        for (var fl = 0; fl < 3; fl++) pen.part(f, 'sph', [1.6, 2.0, 1.6 + fl * 0.8], [0.6, 0.6, 0.6], ['#e8302a', '#f2c21e', '#f07aa8'][fl]);
      }
      pen.part(f, 'box', [0, 0.9, -10.6], [0.3, 1.2, 0.3], '#4a3a2a');
      pen.part(f, 'rbox', [0, 1.9, -9.6], [1.1, 1.3, 0.8], '#3a6ab8');
      pen.part(f, 'rhead', [0, 3.0, -9.6], [0.9, 0.9, 0.9], '#f5cd30');
      pen.part(f, 'box', [0, 3.6, -9.6], [1.1, 0.3, 1.1], '#1e1e24');
      for (var k = 0; k < 4; k++) {
        var ph = (t * 1.2 + k / 4) % 1;
        for (var side = -1; side <= 1; side += 2) {
          pen.part(f, 'box', [side * (2.8 + ph * 4), -0.62, -11 - ph * 8], [1.4, 0.06, 0.8], '#e8f4f8',
                   { a: 0.7 * (1 - ph), ry: side * 0.4 });
        }
      }
    };
    return me;
  });

  /* A cyclist along the dike road: a sit-up-and-beg bike, tulips in the
     basket, legs going round, a ring of the bell as they pass you. */
  Rigs.register('cyclist', function (spec, ctx) {
    var a = spec.p, b = spec.q, speed = spec.speed || 8, seed = spec.seed || 0;
    var len = dist(a, b);
    var heading = Math.atan2(b[0] - a[0], b[2] - a[2]);
    var me = { radius: len / 2 + 10, at: [(a[0] + b[0]) / 2, a[1], (a[2] + b[2]) / 2], kind: 'cyclist', bell: -20 };
    me.draw = function (pen, t) {
      var cycle = len / speed + 4;
      var d = (((t + seed * 9) % cycle) - 2) * speed;
      if (d < 0 || d > len) return;
      var fade = Math.min(1, d / 8, (len - d) / 8);
      var pos = [a[0] + (b[0] - a[0]) * d / len, a[1], a[2] + (b[2] - a[2]) * d / len];
      me.at = pos;
      if (ctx.viewer && t - me.bell > 8) {
        var v = ctx.viewer();
        if (v && dist(v.eye, pos) < 26) { me.bell = t; if (ctx.sound) ctx.sound('br_bell', pos, 1.5); }
      }
      var f = Rigs.frame(pos, heading, fade);
      var spin = d / 1.4;
      for (var wz = -1; wz <= 1; wz += 2) {
        var wf = child(f, [0, 1.4, wz * 1.9], spin, 0, 0);
        pen.part(wf, 'torus', [0, 0, 0], [2.8, 2.0, 2.8], '#1e1e24', { rz: Math.PI / 2 });
        if (pen.near) pen.part(wf, 'box', [0, 0, 0], [0.1, 2.4, 0.1], '#9aa0a8');
      }
      pen.rod(Rigs.point(f, [0, 1.4, -1.9]), Rigs.point(f, [0, 3.0, 0.4]), 0.25, '#1e1e24', null, 'box');
      pen.rod(Rigs.point(f, [0, 3.0, 0.4]), Rigs.point(f, [0, 1.4, 1.9]), 0.25, '#1e1e24', null, 'box');
      pen.rod(Rigs.point(f, [0, 1.6, -0.2]), Rigs.point(f, [0, 3.2, -0.6]), 0.25, '#1e1e24', null, 'box');
      pen.part(f, 'box', [0, 3.9, 1.2], [1.8, 0.2, 0.2], '#9aa0a8', { m: 'metal' });
      pen.part(f, 'box', [0, 3.4, 2.2], [1.2, 0.9, 1.0], '#c8a060');
      for (var tl = 0; tl < 3; tl++) pen.part(f, 'sph', [-0.3 + tl * 0.3, 4.0, 2.2], [0.5, 0.7, 0.5], ['#e8302a', '#f2c21e', '#f07aa8'][tl]);
      var rider = child(f, [0, 3.4, -0.6], 0.2, 0, 0);
      pen.part(rider, 'rbox', [0, 1.3, 0.2], [1.6, 2.2, 1.0], spec.c || '#2a6aa8');
      pen.part(rider, 'rhead', [0, 3.0, 0.4], [1.2, 1.2, 1.2], '#f5cd30');
      for (var arm = -1; arm <= 1; arm += 2) pen.part(rider, 'box', [arm * 0.9, 1.4, 1.2], [0.5, 0.5, 1.8], spec.c || '#2a6aa8', { rx: -0.6 });
      for (var leg = -1; leg <= 1; leg += 2) {
        var crank = spin * 0.5 + (leg > 0 ? 0 : Math.PI);
        var foot = Rigs.point(f, [leg * 0.5, 1.4 + Math.sin(crank) * 0.8, 0.2 + Math.cos(crank) * 0.8]);
        pen.rod(Rigs.point(rider, [leg * 0.4, 0.2, 0]), foot, 0.6, '#2a2a3a', null, 'box');
      }
    };
    return me;
  });

  /* A duck and her ducklings, paddling round in a ring on the canal. */
  Rigs.register('duck', function (spec, ctx) {
    var R = spec.r || 6, seed = spec.seed || 0;
    var me = { radius: R + 6, at: spec.p, kind: 'duck' };
    me.update = function (dt, t) {
      var slot = Math.floor((t + seed * 3) / 13);
      if (slot !== me.slot) {
        me.slot = slot;
        var v = ctx.viewer ? ctx.viewer() : null;
        if (v && hash(slot + seed) < 0.5 && dist(v.eye, spec.p) < 60 && ctx.sound) ctx.sound('br_quack', spec.p, 2);
      }
    };
    me.draw = function (pen, t) {
      for (var k = 0; k < 4; k++) {
        var a = t * 0.3 + seed - k * 0.32;
        var s = k ? 0.5 : 1;
        var pos = [spec.p[0] + Math.sin(a) * R, spec.p[1] + 0.05, spec.p[2] + Math.cos(a) * R * 2.2];
        var f = Rigs.frame(pos, a + Math.PI / 2, s);
        pen.part(f, 'sph', [0, 0.5, 0], [1.4, 1.0, 2.2], k ? '#c8a050' : '#8a6a48');
        var bob = Math.sin(t * 3 + k) * 0.15;
        pen.part(f, 'sph', [0, 1.4 + bob, 0.9], [0.9, 0.9, 0.9], k ? '#d8b860' : '#2a6a3a');
        pen.part(f, 'box', [0, 1.3 + bob, 1.55], [0.5, 0.25, 0.6], '#f2a020');
      }
    };
    return me;
  });

  /* A kid on the church terp with a kite up in the spring wind. */
  Rigs.register('kite', function (spec) {
    var seed = spec.seed || 0;
    var me = { radius: 80, at: spec.p, kind: 'kite' };
    me.draw = function (pen, t) {
      var kid = Rigs.frame(spec.p, -0.4, 1);
      pen.part(kid, 'rbox', [0, 1.1, 0], [1.4, 2.2, 0.9], '#3a6ab8');
      pen.part(kid, 'rbox', [0, 3.0, 0], [1.6, 1.8, 1.0], '#f2c21e');
      pen.part(kid, 'rhead', [0, 4.5, 0], [1.2, 1.2, 1.2], '#f5cd30');
      pen.part(kid, 'box', [0.6, 4.0, 0.6], [0.4, 0.4, 1.6], '#f2c21e', { rx: -0.9 });
      var hand = Rigs.point(kid, [0.6, 4.6, 1.3]);
      var kx = spec.p[0] + 26 + wander(t * 0.25, seed) * 10, ky = spec.p[1] + 40 + wander(t * 0.3, seed + 3) * 8;
      var kz = spec.p[2] + 24 + wander(t * 0.2, seed + 7) * 10;
      var kf = child(Rigs.frame([kx, ky, kz], 0.9, 1), [0, 0, 0], 0.4, 0, Math.sin(t * 1.7) * 0.4);
      pen.part(kf, 'box', [0, 0, 0], [4.2, 4.2, 0.2], '#e8302a', { rz: Math.PI / 4 });
      pen.part(kf, 'box', [0, 0, 0.12], [0.2, 5.8, 0.1], '#4a3a2a');
      pen.part(kf, 'box', [0, 0, 0.12], [4.2, 0.2, 0.1], '#4a3a2a');
      pen.rod(hand, [kx, ky, kz], 0.08, '#f4f2ea');
      var prev = Rigs.point(kf, [0, -2.9, 0]);
      for (var k = 1; k <= 5; k++) {
        var next = [prev[0] + Math.sin(t * 3 + k) * 0.8, prev[1] - 2.2, prev[2] + Math.cos(t * 2 + k) * 0.6];
        pen.rod(prev, next, 0.08, '#f4f2ea');
        pen.part(Rigs.frame(next, 0, 1), 'box', [0, 0, 0], [0.9, 0.5, 0.2], ['#f2c21e', '#2a6aa8'][k % 2]);
        prev = next;
      }
    };
    return me;
  });

  /* Fair-weather clouds drifting over: heaps of white. */
  Rigs.register('clouds', function (spec) {
    var n = spec.n || 8, R = spec.r || 500;
    var me = { radius: 1e6, at: spec.p, kind: 'clouds' };
    me.draw = function (pen, t) {
      for (var i = 0; i < n; i++) {
        var size = 40 + hash(i * 2.3) * 70;
        var x = ((hash(i * 5.1) * 2 * R + t * (3 + hash(i) * 3)) % (2 * R)) - R;
        var z = (hash(i * 7.7) - 0.5) * 2 * R;
        var y = spec.p[1] + hash(i * 3.3) * 60;
        var f = Rigs.frame([spec.p[0] + x, y, spec.p[2] + z], 0, size / 50);
        var tint = spec.tint || '#ffffff';
        pen.part(f, 'sph', [0, 0, 0], [60, 22, 40], tint, { a: 0.92 });
        pen.part(f, 'sph', [18, 8, 6], [40, 24, 30], tint, { a: 0.92 });
        pen.part(f, 'sph', [-20, 6, -4], [36, 20, 28], spec.tint ? tint : '#f4f6fa', { a: 0.92 });
        pen.part(f, 'sph', [4, -6, 0], [64, 10, 42], spec.tint ? '#c8a0a8' : '#e4e8f0', { a: 0.9 });
      }
    };
    return me;
  });

  // ==================================================== Leviathan Quarry
  if (GA) {
    GA.register('br_song', function (vol) {
      // the leviathan's song: long falling and rising moans
      this.tone({ type: 'sine', freq: 180, freqEnd: 120, dur: 2.2, gain: 0.07 * vol });
      this.later(1600, function () { this.tone({ type: 'sine', freq: 140, freqEnd: 260, dur: 2.6, gain: 0.06 * vol }); });
      this.later(3600, function () { this.tone({ type: 'sine', freq: 300, freqEnd: 90, dur: 2.4, gain: 0.05 * vol }); });
    });
    GA.register('br_gull', function (vol) {
      this.tone({ type: 'triangle', freq: 1400, freqEnd: 900, dur: 0.25, gain: 0.03 * vol });
      this.later(280, function () { this.tone({ type: 'triangle', freq: 1300, freqEnd: 800, dur: 0.3, gain: 0.025 * vol }); });
    });
    GA.register('br_thud', function (vol) {
      this.noise({ filter: 'lowpass', freq: 300, freqEnd: 80, dur: 0.2, gain: 0.12 * vol });
    });
  }

  /* An eye socket of the leviathan: dark, with a slow ember in it -- that
     flares and sings when somebody captures, and again on the minute. */
  Rigs.register('leviathan_eye', function (spec, ctx) {
    var me = { radius: 14, at: spec.p, kind: 'leviathan_eye', sung: -100 };
    me.event = function (kind) {
      if (kind === 'flag_capture') {
        var t = Rigs.clock();
        if (t - me.sung > 6 && spec.p[0] < 0 && ctx.sound) ctx.sound('br_song', spec.p, 3);
        me.sung = t;
      }
    };
    me.draw = function (pen, t) {
      var age = t - me.sung;
      var flare = age >= 0 && age < 7 ? Math.sin(Math.min(1, age / 7) * Math.PI) : 0;
      var glow = 0.25 + 0.15 * Math.sin(t * 0.8 + spec.p[0]) + flare * 0.75;
      var f = Rigs.frame(spec.p, 0, spec.s || 1);
      pen.part(f, 'sph', [0, 0, 0], [5 + flare * 3, 4 + flare * 2.4, 2], '#ff7a2a', { m: 'neon', a: glow });
      pen.part(f, 'sph', [0, 0, 0], [12, 9, 3], '#ff9a4a', { m: 'neon', a: glow * 0.3 });
    };
    return me;
  });

  /* The winding engine's drum turning, the rope paying off it. */
  Rigs.register('winding_drum', function (spec) {
    var R = spec.r || 4, W = spec.w || 8;
    var me = { radius: R + W, at: spec.p, kind: 'winding_drum' };
    me.draw = function (pen, t) {
      var f = Rigs.frame(spec.p, spec.yaw || 0, 1);
      var spin = Math.sin(t * 0.25) * 6;
      var drum = child(f, [0, 0, 3.6], 0, 0, spin);
      pen.part(drum, 'cyl', [0, 0, 0], [R * 2, W, R * 2], '#5a5a60', { rz: Math.PI / 2, m: 'metal' });
      for (var k = 0; k < 6; k++) {
        pen.part(drum, 'box', [0, Math.cos(k * TAU / 6) * R, Math.sin(k * TAU / 6) * R], [W + 0.4, 0.3, 0.6],
                 '#c89a3a', { rx: k * TAU / 6, m: 'metal' });
      }
    };
    return me;
  });

  /* The headframe's sheave wheel, turning one way then the other as the
     cage goes down the old shaft and up again; the rope to the house. */
  Rigs.register('sheave', function (spec) {
    var R = spec.r || 4;
    var me = { radius: R + 40, at: spec.p, kind: 'sheave' };
    me.draw = function (pen, t) {
      var spin = Math.sin(t * 0.25) * 6;
      var f = child(Rigs.frame(spec.p, spec.yaw || 0, 1), [0, 0, 0], spin, 0, 0);
      pen.part(f, 'torus', [0, 0, 0], [R * 2, 2.5, R * 2], '#3a3a40', { rz: Math.PI / 2, m: 'metal' });
      for (var k = 0; k < 4; k++) {
        pen.part(f, 'box', [0, 0, 0], [0.3, R * 1.8, 0.4], '#a85a32', { rx: k * Math.PI / 4, m: 'metal' });
      }
      pen.part(Rigs.frame(spec.p, spec.yaw || 0, 1), 'cyl', [0, 0, 0], [1.2, 3, 1.2], '#2a2a30', { rz: Math.PI / 2 });
      if (spec.rope_p) {
        var top = Rigs.point(Rigs.frame(spec.p, spec.yaw || 0, 1), [0, R, 0]);
        pen.rod(top, spec.rope_p, 0.25, '#2a2a2a');
        pen.rod([spec.p[0], spec.p[1] - R, spec.p[2] + 0.0], [spec.p[0], spec.p[1] - 30, spec.p[2]], 0.25, '#2a2a2a');
      }
    };
    return me;
  });

  /* A crane on the pit floor: its jib slewing back and forth, a skip on the
     hook going up and coming down again. */
  Rigs.register('crane', function (spec) {
    var J = spec.jib || 24, seed = spec.seed || 0;
    var me = { radius: J + 10, at: spec.p, kind: 'crane' };
    me.draw = function (pen, t) {
      var slew = Math.sin(t * 0.12 + seed) * 1.4;
      var f = Rigs.frame(spec.p, slew, 1);
      pen.part(f, 'box', [0, 1.5, 0], [4, 3, 4], '#e8a020');
      pen.part(f, 'box', [0, 3.6, J / 2 - 3], [1.6, 1.6, J + 6], '#e8a020', { m: 'metal' });
      pen.part(f, 'box', [0, 3.0, -7], [3.6, 3.0, 3.0], '#5a5a60');
      pen.part(f, 'box', [0, 5.0, 0], [1.2, 4.0, 1.2], '#e8a020');
      pen.rod(Rigs.point(f, [0, 7.0, 0]), Rigs.point(f, [0, 4.4, J]), 0.2, '#3a3a3a');
      var drop = 10 + Math.sin(t * 0.3 + seed) * 8;
      var hook = Rigs.point(f, [0, 2.8 - drop, J - 1]);
      pen.rod(Rigs.point(f, [0, 2.8, J - 1]), hook, 0.15, '#2a2a2a');
      var skip = Rigs.frame([hook[0], hook[1] - 1.6, hook[2]], slew, 1);
      pen.part(skip, 'box', [0, 0, 0], [3.4, 2.4, 3.4], '#7a6a5a');
      pen.part(skip, 'box', [0, 1.3, 0], [3.0, 0.4, 3.0], '#c8a070');
    };
    return me;
  });

  /* A drill rig at the bench foot: the mast, the hammer going up and down,
     dust puffing at each blow. */
  Rigs.register('drill_rig', function (spec, ctx) {
    var H = spec.h || 14, seed = spec.seed || 0;
    var me = { radius: H + 8, at: spec.p, kind: 'drill_rig' };
    me.draw = function (pen, t) {
      var f = Rigs.frame(spec.p, seed, 1);
      pen.part(f, 'box', [0, H / 2, 0], [1.4, H, 1.4], '#c84a2a', { m: 'metal' });
      var cyc = (t * 1.6 + seed) % 1;
      var hy = cyc < 0.2 ? H - 3 - cyc / 0.2 * (H - 6) : 3 + (cyc - 0.2) / 0.8 * (H - 6);
      pen.part(f, 'box', [1.4, hy, 0], [2.2, 2.6, 2.2], '#3a3a40', { m: 'metal' });
      pen.part(f, 'cyl', [1.4, 1.5, 0], [0.6, 3, 0.6], '#9aa0a8', { m: 'metal' });
      if (cyc < 0.35) {
        var k = cyc / 0.35;
        pen.part(f, 'sph', [1.4, 0.6 + k * 2, 0], [2 + k * 4, 1.4 + k * 2, 2 + k * 4], '#d8c0a0', { a: 0.6 * (1 - k) });
      }
      if (cyc < 0.02 && ctx.viewer) {
        var v = ctx.viewer();
        if (v && dist(v.eye, spec.p) < 70 && ctx.sound) ctx.sound('br_thud', spec.p, 1.2);
      }
    };
    return me;
  });

  /* A palaeontologist on their knees at the trench, brushing at a bone. */
  Rigs.register('digger', function (spec) {
    var seed = spec.seed || 0;
    var me = { radius: 8, at: spec.p, kind: 'digger' };
    me.draw = function (pen, t) {
      var f = child(Rigs.frame(spec.p, spec.yaw || 0, 1), [0, 0, 0], 0.4, 0, 0);
      pen.part(f, 'rlimb', [-0.5, 0.6, -0.6], [0.9, 1.2, 2.2], '#6a5a3a', { rx: 1.2 });
      pen.part(f, 'rlimb', [0.5, 0.6, -0.6], [0.9, 1.2, 2.2], '#6a5a3a', { rx: 1.2 });
      pen.part(f, 'rbox', [0, 2.4, 0], [2.0, 2.2, 1.1], '#c8a868');
      pen.part(f, 'rhead', [0, 4.0, 0.3], [1.4, 1.4, 1.4], '#f5cd30');
      pen.part(f, 'cyl', [0, 4.8, 0.3], [2.6, 0.2, 2.6], '#c8b080');
      pen.part(f, 'cyl', [0, 5.1, 0.3], [1.5, 0.6, 1.5], '#c8b080');
      var brush = Math.sin(t * 6 + seed) * 0.5;
      var arm = child(f, [0.9, 3.0, 0.3], -1.0, 0, brush);
      pen.part(arm, 'rlimb', [0, -0.9, 0], [0.6, 1.8, 0.6], '#c8a868');
      pen.part(arm, 'box', [0, -2.0, 0], [0.5, 0.6, 0.3], '#8a5a2a');
    };
    return me;
  });

  /* A conveyor from the pit up to the crusher on the rim: the belt on its
     trestles, lumps of rock riding up it. */
  Rigs.register('conveyor', function (spec) {
    var a = spec.p, b = spec.q, W = spec.w || 3;
    var len = dist(a, b);
    var me = { radius: len / 2 + 6, at: [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2], kind: 'conveyor' };
    me.draw = function (pen, t) {
      pen.rod(a, b, W, '#2a2a2e', null, 'box');
      var n = Math.floor(len / 14);
      for (var k = 1; k < n; k++) {
        var u = k / n;
        var p = [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u];
        pen.rod(p, [p[0], Math.max(0, p[1] - 30), p[2]], 0.6, '#7a6a5a', null, 'box');
      }
      for (var r = 0; r < 12; r++) {
        var ph = ((t * 0.05) + r / 12) % 1;
        var q = [a[0] + (b[0] - a[0]) * ph, a[1] + (b[1] - a[1]) * ph + W * 0.4, a[2] + (b[2] - a[2]) * ph];
        pen.part(Rigs.frame(q, r, 1), 'rbox', [0, 0, 0], [1.4, 1.0, 1.2], ['#b8805a', '#c8a070', '#a86a4a'][r % 3]);
      }
    };
    return me;
  });

  /* Gulls wheeling over the quarry, calling. */
  Rigs.register('gulls', function (spec, ctx) {
    var n = spec.n || 6, R = spec.r || 120;
    var me = { radius: 1e6, at: spec.p, kind: 'gulls' };
    me.update = function (dt, t) {
      var slot = Math.floor(t / 9);
      if (slot !== me.slot) {
        me.slot = slot;
        if (hash(slot + 3) < 0.5 && ctx.sound) ctx.sound('br_gull', spec.p, 0.8);
      }
    };
    me.draw = function (pen, t) {
      for (var i = 0; i < n; i++) {
        var a = t * (0.12 + i * 0.015) + i * 1.3;
        var r = R * (0.5 + hash(i * 3.1) * 0.6);
        var pos = [spec.p[0] + Math.sin(a) * r, spec.p[1] + hash(i) * 30 + Math.sin(t * 0.5 + i) * 4,
                   spec.p[2] + Math.cos(a) * r * 0.8];
        var f = child(Rigs.frame(pos, a + Math.PI / 2, 1.2), [0, 0, 0], 0, 0, -0.3);
        pen.part(f, 'sph', [0, 0, 0], [1.2, 1.0, 2.6], '#f4f4f0');
        var flap = Math.sin(t * 5 + i) * 0.3;
        for (var side = -1; side <= 1; side += 2) {
          var w = child(f, [side * 0.5, 0.2, 0], 0, 0, -side * (0.2 + flap));
          pen.part(w, 'box', [side * 2.2, 0, 0], [4.4, 0.12, 1.2], '#e8e8e4');
          pen.part(w, 'box', [side * 4.0, 0.02, -0.2], [1.0, 0.1, 1.0], '#2a2a2a');
        }
        pen.part(f, 'cone', [0, 0, 1.6], [0.3, 0.8, 0.3], '#f2b81e', { rx: Math.PI / 2 });
      }
    };
    return me;
  });

  /* A dust devil skittering about the pit floor. */
  Rigs.register('dust_devil', function (spec) {
    var R = spec.r || 30, seed = spec.seed || 0;
    var me = { radius: R + 20, at: spec.p, kind: 'dust_devil' };
    me.draw = function (pen, t) {
      var life = (t + seed * 7) % 24;
      if (life > 9) return;
      var k = Math.sin(life / 9 * Math.PI);
      var cx = spec.p[0] + wander(t * 0.2, seed) * R, cz = spec.p[2] + wander(t * 0.18, seed + 5) * R;
      for (var i = 0; i < 14; i++) {
        var y = i * 1.4;
        var a = t * 6 + i * 0.7;
        var rr = (0.8 + y * 0.22) * k;
        pen.part(Rigs.frame([cx + Math.sin(a) * rr, spec.p[1] + y, cz + Math.cos(a) * rr], 0, 1), 'sph',
                 [0, 0, 0], [1.6 + y * 0.12, 1.2, 1.6 + y * 0.12], '#d8b888', { a: 0.35 * k * (1 - i / 16) });
      }
    };
    return me;
  });

  /* A haul truck along the rim road and back, laden one way. */
  Rigs.register('haul_truck', function (spec) {
    var a = spec.p, b = spec.q, speed = spec.speed || 9;
    var len = dist(a, b);
    var me = { radius: len / 2 + 14, at: [(a[0] + b[0]) / 2, a[1], (a[2] + b[2]) / 2], kind: 'haul_truck' };
    me.draw = function (pen, t) {
      var period = 2 * len / speed + 8;
      var ph = t % period;
      var go = ph < len / speed;
      var back = ph > len / speed + 4 && ph < 2 * len / speed + 4;
      var u = go ? ph * speed / len : (back ? 1 - (ph - len / speed - 4) * speed / len : (ph < len / speed + 4 ? 1 : 0));
      var pos = [a[0] + (b[0] - a[0]) * u, a[1], a[2] + (b[2] - a[2]) * u];
      var heading = Math.atan2(b[0] - a[0], b[2] - a[2]) + (back ? Math.PI : 0);
      var f = Rigs.frame(pos, heading, 1);
      pen.part(f, 'box', [0, 3.6, -1.5], [7.6, 3.6, 11], '#e8b820');
      pen.part(f, 'box', [0, 4.0, 6.0], [7.0, 4.4, 4.0], '#e8b820');
      pen.part(f, 'box', [0, 5.0, 8.05], [5.0, 1.6, 0.1], '#3a4a5a');
      if (go) pen.part(f, 'box', [0, 5.8, -1.5], [6.4, 1.2, 9.6], '#b8805a');
      for (var wx = -1; wx <= 1; wx += 2) {
        for (var wz = -1; wz <= 1; wz += 2) {
          pen.part(child(f, [wx * 3.6, 1.6, wz * 4.4], u * 30, 0, Math.PI / 2), 'cyl', [0, 0, 0], [3.2, 1.6, 3.2], '#1e1e24');
        }
      }
    };
    return me;
  });

  global.BlackoutRelayRigs = true;
})(window);
