/* Rail Rivals -- the lines built since the first four: each one's twist as
   the Game View draws it (registered in RailTwists for rail_rivals.js's
   plugin, which hands it the race: lanes, carts, who is on which track),
   their sounds, and their arrival scenes.

   A twist here is factory(ctx) -> {load(map), apply(twistState),
   message(rrx) -> handled, draw(renderer, time, dt), here(pos) -> prompt,
   hud() -> line, held(reason) -> cart status, labels{act: hold label},
   carryName(kind), avatar(player, parts, kind) -> parts}. */
(function (global) {
  'use strict';
  var Twists = global.RailTwists || (global.RailTwists = {});

  function rgbOf(hex) {
    var n = parseInt(String(hex).slice(1), 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
  }
  function flat(a, b) { return Math.hypot(a[0] - b[0], a[2] - b[2]); }

  /* A piece of track laid by the players: two rails and two sleepers along
     ``d0``..``d1`` of ``path``, pitched with the grade. */
  function trackPiece(renderer, path, d0, d1, alpha) {
    var a = path.at(d0), b = path.at(d1);
    var dx = b[0] - a[0], dz = b[1] - a[1], dy = b[3] - a[3];
    var run = Math.hypot(dx, dz) || 0.001, len = Math.hypot(run, dy);
    var yaw = Math.atan2(dx, dz), pitch = Math.atan2(dy, run);
    var mx = (a[0] + b[0]) / 2, mz = (a[1] + b[1]) / 2, my = (a[3] + b[3]) / 2;
    var rx = Math.cos(yaw), rz = -Math.sin(yaw);
    var o = alpha === undefined ? 1 : alpha;
    for (var side = -1; side <= 1; side += 2) {
      renderer.pushRaw('box', mx + rx * 1.6 * side, my + 0.37, mz + rz * 1.6 * side, -pitch, yaw, 0,
                       0.36, 0.14, len + 0.06, [0.55, 0.54, 0.53], o, 0, 1, 0, null);
    }
    if (o < 1) return;
    for (var k = 0; k < 2; k++) {
      var f = (k + 0.5) / 2;
      renderer.pushRaw('box', a[0] + dx * f, a[3] + dy * f + 0.24, a[1] + dz * f, -pitch, yaw, 0,
                       4.8, 0.12, 0.9, [0.37, 0.27, 0.19], 1, 0, 0, 0, null);
    }
  }

  // =========================================================== railhead
  /* Golden Spike Summit: the unfinished lines.  The gaps' rails as they are
     laid, the railhead's flag where the laid track ends, a ghost of the
     rails to come, a rail floating over every stack, and a rail on the
     shoulder of everyone carrying one. */
  Twists.railhead = function (ctx) {
    var RAIL_LEN = 6, LAY_R = 6.5, STACK_R = 6;
    var gaps = {}, stacks = [], drops = [];

    function load(map) {
      var mk = (map && map.markers) || {};
      stacks = ((mk.points || {}).rails || []).map(function (m) { return m.p; });
      var g = (mk.extra || {}).gaps || {};
      gaps = {};
      Object.keys(g).forEach(function (lane) {
        gaps[lane] = g[lane].map(function (s) {
          return { d0: s[0], d1: s[1], need: Math.max(1, Math.ceil((s[1] - s[0]) / RAIL_LEN - 1e-6)), laid: 0 };
        });
      });
    }
    function apply(tw) {
      Object.keys(tw.gaps || {}).forEach(function (lane) {
        gaps[lane] = tw.gaps[lane].map(function (g) { return { d0: g.d0, d1: g.d1, need: g.need, laid: g.laid }; });
      });
    }
    function openGap(lane) {
      var list = gaps[lane] || [];
      for (var i = 0; i < list.length; i++) if (list[i].laid < list[i].need) return list[i];
      return null;
    }
    function headD(g) { return Math.min(g.d1, g.d0 + g.laid * RAIL_LEN); }
    function laneName(lane) { return (ctx.names()[lane]) || ('lane ' + lane); }

    function draw(renderer, time, dt) {
      var lanes = ctx.lanes(), mine = ctx.myLane(), p = ctx.client.local.pos;
      Object.keys(gaps).forEach(function (lane) {
        var path = lanes[lane];
        if (!path) return;
        var team = ctx.teamOfLane(lane);
        var colour = rgbOf(ctx.TEAM_LIGHT[team] || '#ffffff');
        gaps[lane].forEach(function (g) {
          for (var k = 0; k < g.laid; k++) {
            trackPiece(renderer, path, g.d0 + k * RAIL_LEN, Math.min(g.d1, g.d0 + (k + 1) * RAIL_LEN));
          }
          if (g.laid >= g.need) return;
          var hd = headD(g);
          // the rails to come, a faint ghost in the line's colour
          var pulse = 0.12 + 0.08 * Math.sin(time * 3);
          for (var d = hd; d < g.d1 - 0.5; d += RAIL_LEN) {
            var a = path.at(d), b = path.at(Math.min(g.d1, d + RAIL_LEN));
            var run = Math.hypot(b[0] - a[0], b[1] - a[1]);
            var yaw = Math.atan2(b[0] - a[0], b[1] - a[1]);
            renderer.pushRaw('box', (a[0] + b[0]) / 2, (a[3] + b[3]) / 2 + 0.4, (a[1] + b[1]) / 2, 0, yaw, 0,
                             4.2, 0.08, Math.max(0.5, run - 0.6), colour, pulse, 0, 2, 0.3, null);
          }
          // the railhead: a striped surveyor's pole and its flag
          var h = path.at(hd + 0.6);
          for (var s = 0; s < 4; s++) {
            renderer.pushRaw('box', h[0], h[3] + 0.5 + s * 0.9, h[1], 0, h[2], 0, 0.36, 0.9, 0.36,
                             s % 2 ? [0.95, 0.95, 0.92] : [0.85, 0.18, 0.12], 1, 0, 0, 0, null);
          }
          var flap = Math.sin(time * 6 + (lane === 'a' ? 0 : 2)) * 0.3;
          renderer.pushRaw('box', h[0] + Math.cos(h[2]) * 0.9, h[3] + 3.6, h[1] - Math.sin(h[2]) * 0.9,
                           0, h[2] + Math.PI / 2 + flap, 0, 1.6, 1.0, 0.06, colour, 1, 0, 0, 0, null);
          if (lane === mine && flat(p, [h[0], h[3], h[1]]) < 80) {
            renderer.pushRaw('cyl', h[0], h[3] + 0.12, h[1], 0, 0, 0, LAY_R * 2, 0.06, LAY_R * 2,
                             [0.4, 1, 0.5], 0.14 + 0.1 * Math.sin(time * 4), 0, 2, 0.5, null);
          }
        });
      });
      // a rail turning over every stack, for anyone not carrying one
      if (ctx.me().carry !== 'rail') {
        stacks.forEach(function (st, i) {
          var bob = Math.sin(time * 2 + i) * 0.35;
          renderer.pushRaw('box', st[0], st[1] + 3.6 + bob, st[2], 0.25, time * 0.9 + i, 0, 0.5, 0.4, 4.2,
                           [0.75, 0.75, 0.78], 1, 0, 1, 0.2, null);
          renderer.pushRaw('sph', st[0], st[1] + 3.6 + bob, st[2], 0, 0, 0, 3, 3, 3, [1, 0.85, 0.45],
                           0.12, 0, 2, 0.4, null);
        });
      }
      // the dust of a rail going down
      drops = drops.filter(function (q) {
        q.t += dt;
        if (q.t > 0.8) return false;
        var k = q.t / 0.8;
        renderer.pushRaw('sph', q.p[0], q.p[3] + 0.6 + k, q.p[1], 0, 0, 0, 2 + k * 3, 1 + k, 2 + k * 3,
                         [0.85, 0.8, 0.7], 0.5 * (1 - k), 0, 0, 0, null);
        return true;
      });
    }

    function here(p) {
      var me = ctx.me(), lane = ctx.myLane(), lanes = ctx.lanes();
      if (me.carry === 'rail') {
        var g = openGap(lane);
        if (g && lanes[lane]) {
          var h = lanes[lane].at(headD(g) + 1.5);
          if (Math.hypot(h[0] - p[0], h[1] - p[2]) <= LAY_R) return { k: 'lay', text: 'Hold <b>E</b> to lay the rail' };
        }
        return { k: 'carry', text: g ? 'Carrying a rail &bull; take it to your railhead'
                                     : 'Carrying a rail &bull; your line is finished' };
      }
      if (me.coal) return null;
      for (var other in gaps) {
        if (other === lane || !lanes[other]) continue;
        var g2 = openGap(other);
        if (!g2 || g2.laid <= 0) continue;
        var cartD = ctx.shown(ctx.teamOfLane(other));
        if (cartD !== undefined && cartD >= headD(g2) - RAIL_LEN - 8) continue;
        var last = lanes[other].at(headD(g2) - RAIL_LEN / 2);
        if (Math.hypot(last[0] - p[0], last[1] - p[2]) <= LAY_R) {
          return { k: 'pull', text: 'Hold <b>E</b> to pull up their last rail' };
        }
      }
      for (var i = 0; i < stacks.length; i++) {
        if (flat(stacks[i], p) <= STACK_R) return { k: 'rail', text: 'Hold <b>E</b> to take a rail' };
      }
      return null;
    }

    function hud() {
      var parts = [];
      ['a', 'b'].forEach(function (lane) {
        var g = openGap(lane);
        var who = ctx.esc(ctx.arena.teamName(ctx.teamOfLane(lane)));
        parts.push(g ? who + ' railhead ' + g.laid + '/' + g.need : who + ' line through');
      });
      return 'The unfinished lines: ' + parts.join(' &bull; ');
    }

    function message(msg) {
      var me = ctx.client.myTeam, myLane = ctx.myLane(), lanes = ctx.lanes();
      if (msg.k === 'rail') {
        ctx.client.audio.play('rr_railup', { volume: 0.6 });
        return true;
      }
      if (msg.k === 'lay') {
        // (the state with the new count comes just after this message, so
        // the gap being worked is still the open one)
        var g = openGap(msg.lane);
        if (lanes[msg.lane] && g) {
          var at = lanes[msg.lane].at(g.d0 + (msg.laid - 0.5) * RAIL_LEN);
          drops.push({ p: at, t: 0 });
          var q = ctx.client.local.pos;
          ctx.client.audio.play('rr_clank', { volume: Math.max(0.15, 1 - Math.hypot(at[0] - q[0], at[1] - q[2]) / 120) });
        }
        if (msg.done) {
          ctx.say('lay' + msg.lane, msg.lane === myLane ? 'LINE THROUGH!' : 'THEIR LINE IS THROUGH',
                  msg.lane === myLane ? 'go' : 'bad', 'rr_bell');
        }
        return true;
      }
      if (msg.k === 'pull') {
        ctx.client.audio.play('rr_pry', { volume: 0.7 });
        if (msg.lane === myLane) ctx.say('pull', 'RAIL STOLEN', 'bad');
        return true;
      }
      return false;
    }

    function avatar(player, parts, kind) {
      if (kind !== 'rail') return parts;
      var yaw = player.yaw || 0, p = player.pos;
      var sx = Math.cos(yaw) * -1.1, sz = -Math.sin(yaw) * -1.1;
      parts.push({ t: 'box', p: [p[0] + sx, p[1] + 5.3, p[2] + sz], s: [0.36, 0.3, 6.2],
                   c: '#8c8a86', r: [0.12, yaw, 0], m: 'metal' });
      return parts;
    }

    return {
      load: load, apply: apply, draw: draw, here: here, hud: hud, message: message, avatar: avatar,
      held: function (reason) { return reason === 'railhead' ? 'AT THE RAILHEAD' : ''; },
      labels: { rail: 'Taking a rail', lay: 'Laying the rail', pull: 'Pulling up their rail' },
      carryName: function (kind) { return kind === 'rail' ? 'a rail' : kind; }
    };
  };

  // ============================================================= sounds
  var GA = global.GameAudio;
  if (GA && GA.register) {
    GA.register('rr_clank', function (vol) {
      // a rail dropped onto its sleepers, then two blows on the spikes
      this.noise({ filter: 'bandpass', freq: 2600, freqEnd: 900, dur: 0.25, gain: 0.2 * vol });
      this.tone({ type: 'square', freq: 320, freqEnd: 180, dur: 0.18, gain: 0.08 * vol });
      for (var i = 0; i < 2; i++) {
        this.later(260 + i * 220, function () {
          this.tone({ type: 'triangle', freq: 1800, freqEnd: 1500, dur: 0.12, gain: 0.1 * vol });
          this.noise({ freq: 3000, freqEnd: 800, dur: 0.06, gain: 0.12 * vol });
        });
      }
    });
    GA.register('rr_railup', function (vol) {
      this.noise({ filter: 'bandpass', freq: 1400, freqEnd: 2200, dur: 0.3, gain: 0.1 * vol });
      this.tone({ type: 'triangle', freq: 660, freqEnd: 700, dur: 0.25, gain: 0.05 * vol });
    });
    GA.register('rr_flap', function (vol) {
      // a split-flap board rattling: a burst of little clacks
      for (var i = 0; i < 14; i++) {
        this.later(i * 28, function () {
          this.noise({ filter: 'bandpass', freq: 3200, freqEnd: 2400, dur: 0.025, gain: 0.08 * vol });
        });
      }
    });
    GA.register('rr_pry', function (vol) {
      this.tone({ type: 'sawtooth', freq: 220, freqEnd: 520, dur: 0.5, gain: 0.06 * vol });
      this.noise({ filter: 'bandpass', freq: 1800, freqEnd: 600, dur: 0.45, gain: 0.12 * vol });
      this.later(480, function () { this.noise({ freq: 2400, freqEnd: 300, dur: 0.2, gain: 0.16 * vol }); });
    });
  }

  // ===================================================== arrival scenes
  var Intro = global.AreaIntro;
  var Art = global.RailRivalsArt;
  if (!Intro || !Art) return;
  var K = Intro.kit;
  var VW = K.VW, VH = K.VH, TAU = K.TAU, HEAVY = K.HEAVY;
  var seg = K.seg, lerp = K.lerp, outBack = K.outBack, outCubic = K.outCubic;
  var dot = K.dot, additive = K.additive, roundRect = K.roundRect, fitSize = K.fitSize;
  var spaced = K.spaced, between = K.between, rgba = K.rgba, wobble = K.wobble;
  var loco = Art.loco, nameText = Art.nameText;

  /* An engine facing -x: the same silhouette, mirrored. */
  function locoLeft(ctx, x, y, s, colour, t, light) {
    ctx.save();
    ctx.translate(x, 0);
    ctx.scale(-1, 1);
    loco(ctx, 0, y, s, colour, t, light);
    ctx.restore();
  }

  // ------------------------------------------------ Golden Spike Summit
  /* High noon on the pass.  The line has a gap in the middle; the track
     gangs run the rails in -- clank, clank, clank -- while the two engines
     ease up from either side, the crowd waiting under the bunting.  The
     last rail goes down, the engines touch noses, and the golden spike is
     driven home.  The name comes down on the laurel tie. */
  Intro.register('rr_goldspike', {
    name: 'Golden Spike Summit',
    tagline: 'Neither line is finished. Lay your rails -- and pull up theirs.',
    accent: '#e8b23a',
    cues: [[0.15, 'rr_whistle', 0.4], [0.55, 'rr_clank', 0.7], [0.85, 'rr_clank', 0.7],
           [1.15, 'rr_clank', 0.7], [1.45, 'rr_clank', 0.8], [2.05, 'rr_hammer', 0.8],
           [2.2, 'rr_bell', 0.8], [2.35, 'rr_whistle', 0.6]],
    shakes: [[2.05, 4, 0.25]],
    tagY: 420, tagAt: 2.9,
    setup: function (r) {
      var d = { far: [], near: [], crowd: [], sage: [], hats: [] };
      var x = -60;
      while (x < VW + 80) {
        var w = between(r, 80, 180);
        d.far.push({ x: x, w: w, h: between(r, 80, 190) });
        x += w * 0.7;
      }
      for (var i = 0; i < 9; i++) d.near.push({ x: i * 200 + between(r, -40, 40), w: between(r, 220, 320), h: between(r, 30, 70) });
      for (i = 0; i < 46; i++) {
        d.crowd.push({ x: 20 + i * 34 + between(r, -8, 8), h: between(r, 60, 84), hat: r() < 0.55 ? 'top' : (r() < 0.5 ? 'bonnet' : 'cap'),
                       c: ['#3a2a22', '#4a3a5a', '#2a3a4a', '#5a2a2a', '#3a4a2a'][i % 5], p: r() * 6 });
      }
      for (i = 0; i < 26; i++) d.sage.push({ x: r() * VW, y: between(r, 600, 760), s: between(r, 0.6, 1.3) });
      for (i = 0; i < 8; i++) d.hats.push({ x: 120 + r() * 1360, vx: between(r, -60, 60), vy: between(r, -520, -380), sp: between(r, -6, 6) });
      return d;
    },
    draw: function (ctx, t, d) {
      var HZ = 540;
      var sky = ctx.createLinearGradient(0, 0, 0, HZ);
      sky.addColorStop(0, '#2f62b4');
      sky.addColorStop(0.6, '#8ab8e6');
      sky.addColorStop(1, '#f2e6c8');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, VW, HZ + 2);
      additive(ctx, function () { dot(ctx, '#fff2c8', 1240, 120, 220, 0.5); });
      ctx.fillStyle = '#fff8e0';
      ctx.beginPath(); ctx.arc(1240, 120, 40, 0, TAU); ctx.fill();
      // the far peaks, then the sage hills
      d.far.forEach(function (m, i) {
        ctx.fillStyle = i % 2 ? '#8a7a98' : '#7a6a88';
        ctx.beginPath(); ctx.moveTo(m.x, HZ); ctx.lineTo(m.x + m.w * 0.5, HZ - m.h); ctx.lineTo(m.x + m.w, HZ); ctx.fill();
        ctx.fillStyle = '#f2f2f8';
        ctx.beginPath(); ctx.moveTo(m.x + m.w * 0.42, HZ - m.h * 0.84); ctx.lineTo(m.x + m.w * 0.5, HZ - m.h);
        ctx.lineTo(m.x + m.w * 0.58, HZ - m.h * 0.84); ctx.fill();
      });
      d.near.forEach(function (n, i) {
        ctx.fillStyle = i % 2 ? '#a89a68' : '#9a8c5e';
        ctx.beginPath(); ctx.ellipse(n.x, HZ + 10, n.w, n.h, 0, Math.PI, TAU); ctx.fill();
      });
      ctx.fillStyle = '#c8b47a';
      ctx.fillRect(0, HZ, VW, VH - HZ);
      d.sage.forEach(function (s) {
        ctx.fillStyle = '#8a9a78';
        ctx.beginPath(); ctx.ellipse(s.x, s.y, 22 * s.s, 10 * s.s, 0, 0, TAU); ctx.fill();
      });
      // the line, the gap in the middle, the rails going in
      var Y = 640, gap0 = 640, gap1 = 960;
      ctx.fillStyle = '#7a6f62';
      ctx.fillRect(0, Y, VW, 20);
      for (var k = 0; k < 60; k++) {
        ctx.fillStyle = '#5e4630';
        ctx.fillRect(k * 28, Y - 4, 16, 26);
      }
      ctx.fillStyle = '#9a9690';
      ctx.fillRect(0, Y - 6, gap0, 4); ctx.fillRect(0, Y + 16, gap0, 4);
      ctx.fillRect(gap1, Y - 6, VW - gap1, 4); ctx.fillRect(gap1, Y + 16, VW - gap1, 4);
      var laid = [0.55, 0.85, 1.15, 1.45].filter(function (at) { return t >= at; }).length;
      for (var p2 = 0; p2 < laid; p2++) {
        var lx = gap0 + p2 * 80;
        ctx.fillStyle = '#c8c8cc';
        ctx.fillRect(lx, Y - 6, 80, 4); ctx.fillRect(lx, Y + 16, 80, 4);
        if (t - [0.55, 0.85, 1.15, 1.45][p2] < 0.25) {
          additive(ctx, function () { dot(ctx, '#fff2c8', lx + 40, Y + 6, 70, 0.6); });
        }
      }
      // the gang: two men carrying the next rail in
      if (laid < 4) {
        var gx = lerp(gap0 - 160, gap0 + laid * 80, seg(t % 0.3, 0, 0.3)) ;
        ctx.fillStyle = '#2a2420';
        for (var m = 0; m < 2; m++) {
          ctx.fillRect(gx + m * 70, Y - 58, 14, 40);
          ctx.beginPath(); ctx.arc(gx + 7 + m * 70, Y - 66, 9, 0, TAU); ctx.fill();
        }
        ctx.fillStyle = '#c8c8cc';
        ctx.fillRect(gx - 10, Y - 54, 100, 5);
      }
      // the engines ease in, then close the last yards when the rail is down
      var meet = seg(t, 1.5, 2.0);
      var lxL = lerp(lerp(-420, gap0 - 210, outCubic(seg(t, 0.1, 1.2))), 800 - 78, meet);
      var lxR = lerp(lerp(VW + 420, gap1 + 210, outCubic(seg(t, 0.1, 1.2))), 800 + 78, meet);
      loco(ctx, lxL, Y - 4, 1.05, '#7a1a1a', t * (1 - meet * 0.8), '#fff1b0');
      locoLeft(ctx, lxR, Y - 4, 1.05, '#1a3a6a', t * (1 - meet * 0.8), '#fff1b0');
      // the spike: down into the last tie as the noses touch
      var drive = seg(t, 1.9, 2.05);
      if (t > 1.7) {
        var sy = lerp(Y - 200, Y - 30, drive);
        ctx.fillStyle = '#e8b23a';
        ctx.beginPath(); ctx.moveTo(792, sy - 60); ctx.lineTo(808, sy - 60); ctx.lineTo(806, sy + 10);
        ctx.lineTo(800, sy + 26); ctx.lineTo(794, sy + 10); ctx.fill();
        ctx.fillRect(784, sy - 70, 32, 12);
        if (t > 2.05) additive(ctx, function () { dot(ctx, '#ffd84a', 800, Y - 20, 260 * (1 - seg(t, 2.05, 2.8)) + 40, 0.7); });
      }
      // bunting across the top of the stand, and the crowd in front
      ctx.strokeStyle = '#3a2a1e'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(0, 470); ctx.quadraticCurveTo(800, 540, VW, 470); ctx.stroke();
      for (var b = 0; b < 32; b++) {
        var bx = b * 52 + 20, by = 470 + Math.sin(Math.PI * bx / VW) * 34;
        ctx.fillStyle = ['#c4281c', '#efe2c4', '#2f6aa8'][b % 3];
        ctx.beginPath(); ctx.moveTo(bx - 12, by); ctx.lineTo(bx + 12, by); ctx.lineTo(bx, by + 26); ctx.fill();
      }
      var cheer = seg(t, 2.1, 2.4);
      d.crowd.forEach(function (c, i) {
        var jump = cheer > 0 ? Math.abs(Math.sin(t * 9 + c.p)) * 14 * cheer : 0;
        var cy = VH - 20 - jump;
        ctx.fillStyle = c.c;
        ctx.fillRect(c.x - 12, cy - c.h, 24, c.h);
        ctx.beginPath(); ctx.arc(c.x, cy - c.h - 10, 11, 0, TAU); ctx.fill();
        if (c.hat === 'top' && !(cheer > 0 && i % 6 === 0)) {
          ctx.fillStyle = '#1a1414'; ctx.fillRect(c.x - 9, cy - c.h - 38, 18, 20); ctx.fillRect(c.x - 14, cy - c.h - 20, 28, 4);
        } else if (c.hat === 'bonnet') {
          ctx.fillStyle = '#e8d8b8'; ctx.beginPath(); ctx.arc(c.x, cy - c.h - 12, 13, Math.PI, TAU); ctx.fill();
        }
        if (cheer > 0 && i % 3 === 0) {
          ctx.fillStyle = c.c;
          ctx.fillRect(c.x + 10, cy - c.h - 10 - 20 * cheer, 6, 26);
        }
      });
      // hats in the air
      d.hats.forEach(function (h) {
        var age = t - 2.15;
        if (age < 0) return;
        var hx = h.x + h.vx * age, hy = VH - 140 + h.vy * age + 600 * age * age;
        ctx.save(); ctx.translate(hx, hy); ctx.rotate(h.sp * age);
        ctx.fillStyle = '#1a1414'; ctx.fillRect(-9, -20, 18, 20); ctx.fillRect(-14, -2, 28, 4);
        ctx.restore();
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Golden Spike Summit').toUpperCase();
      // the laurel tie with its silver plate, lowered on two ropes
      var drop = outBack(seg(t, 2.25, 2.7), 1.4);
      var y = lerp(-220, 240, drop);
      var tilt = wobble(t, 2.7, 0.03, 7, 2.4);
      ctx.save();
      ctx.translate(800, y);
      ctx.rotate(tilt);
      var w = 1000, h = 180;
      ctx.strokeStyle = '#6a5a4a'; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(-w / 2 + 80, -h / 2); ctx.lineTo(-w / 2 + 80, -h / 2 - 300);
      ctx.moveTo(w / 2 - 80, -h / 2); ctx.lineTo(w / 2 - 80, -h / 2 - 300); ctx.stroke();
      var wood = ctx.createLinearGradient(0, -h / 2, 0, h / 2);
      wood.addColorStop(0, '#9a6a3a'); wood.addColorStop(0.5, '#7a4e28'); wood.addColorStop(1, '#5a3a1e');
      ctx.fillStyle = wood;
      roundRect(ctx, -w / 2, -h / 2, w, h, 10); ctx.fill();
      ctx.strokeStyle = 'rgba(40,20,8,0.35)'; ctx.lineWidth = 2;
      for (var g = 0; g < 6; g++) {
        ctx.beginPath(); ctx.moveTo(-w / 2 + 20, -h / 2 + 22 + g * 26);
        ctx.bezierCurveTo(-120, -h / 2 + 10 + g * 28, 140, -h / 2 + 34 + g * 24, w / 2 - 20, -h / 2 + 20 + g * 26);
        ctx.stroke();
      }
      // the silver plate and its engraving
      ctx.fillStyle = '#d8dce2';
      roundRect(ctx, -w / 2 + 70, -h / 2 + 26, w - 140, h - 52, 8); ctx.fill();
      ctx.strokeStyle = '#8a8f96'; ctx.lineWidth = 4;
      roundRect(ctx, -w / 2 + 78, -h / 2 + 34, w - 156, h - 68, 6); ctx.stroke();
      ctx.globalAlpha = run.alpha * seg(t, 2.45, 2.7);
      nameText(ctx, name, 0, 10, w - 220, '#2a2a30', 'rgba(255,255,255,0.7)');
      ctx.font = 'bold 18px ' + HEAVY;
      ctx.fillStyle = '#5a5e66';
      spaced(ctx, 'THE LAST TIE  ·  THE RAILS MEET TODAY', 0, -h / 2 + 50, 4);
      ctx.globalAlpha = run.alpha;
      // the spike in the tie's end
      ctx.fillStyle = '#e8b23a';
      ctx.beginPath(); ctx.moveTo(w / 2 - 40, -h / 2 - 30); ctx.lineTo(w / 2 - 28, -h / 2 - 30);
      ctx.lineTo(w / 2 - 30, 20); ctx.lineTo(w / 2 - 34, 34); ctx.lineTo(w / 2 - 38, 20); ctx.fill();
      ctx.fillRect(w / 2 - 46, -h / 2 - 38, 24, 10);
      ctx.restore();
    }
  });

  // ---------------------------------------------------- Union Terminal
  /* Dusk over the city.  The signals drop to clear, the gas lamps come on
     along the street, and an engine steams in under the great iron arch of
     the train shed; the station clock strikes.  The name clatters into
     place on the departures board, flap by flap. */
  Intro.register('rr_union', {
    name: 'Union Terminal',
    tagline: 'The race ends under the glass. Take the tower -- hold their cart at the diamond.',
    accent: '#ffb35a',
    cues: [[0.2, 'rr_whistle', 0.4], [0.6, 'rr_signal', 0.6], [1.0, 'rr_chug', 0.5],
           [1.6, 'rr_bell', 0.5], [2.0, 'rr_flap', 0.8], [2.4, 'rr_flap', 0.6], [2.75, 'rr_bell', 0.4]],
    shakes: [],
    tagY: 430, tagAt: 3.0,
    setup: function (r) {
      var d = { towers: [], lamps: [], puffs: Art.makePuffs(r, 24, 0, 6, 0), stars: [] };
      var x = -40;
      while (x < VW + 60) {
        var w = between(r, 50, 110);
        d.towers.push({ x: x, w: w, h: between(r, 90, 300), lit: [] });
        var t = d.towers[d.towers.length - 1];
        for (var i = 0; i < 14; i++) t.lit.push({ u: r(), v: r(), on: between(r, 0.3, 2.2) });
        x += w + between(r, -6, 10);
      }
      for (var k = 0; k < 9; k++) d.lamps.push({ x: 90 + k * 180, at: 0.7 + k * 0.12 });
      for (k = 0; k < 40; k++) d.stars.push({ x: r() * VW, y: r() * 220, p: r() * 6 });
      return d;
    },
    draw: function (ctx, t, d) {
      var HZ = 600;
      var sky = ctx.createLinearGradient(0, 0, 0, HZ);
      sky.addColorStop(0, '#141c3a');
      sky.addColorStop(0.55, '#5a3a5a');
      sky.addColorStop(1, '#e8865a');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, VW, HZ + 2);
      d.stars.forEach(function (s) {
        ctx.fillStyle = rgba('#fff4d8', 0.3 + 0.3 * Math.sin(t * 2 + s.p));
        ctx.fillRect(s.x, s.y, 2, 2);
      });
      // the skyline, its windows coming on
      d.towers.forEach(function (tw) {
        ctx.fillStyle = '#1e1a2a';
        ctx.fillRect(tw.x, HZ - tw.h, tw.w, tw.h + 2);
        tw.lit.forEach(function (l) {
          if (t < l.on) return;
          ctx.fillStyle = l.u > 0.5 ? '#ffd27a' : '#ffb35a';
          ctx.fillRect(tw.x + 6 + l.u * (tw.w - 16), HZ - tw.h + 10 + l.v * (tw.h - 30), 6, 8);
        });
      });
      // the shed: a great arch of iron ribs and glass, the clock tower by it
      var ax = 980, ay = HZ, rad = 380;
      ctx.fillStyle = 'rgba(160,200,220,0.16)';
      ctx.beginPath(); ctx.arc(ax, ay, rad, Math.PI, TAU); ctx.fill();
      ctx.strokeStyle = '#2a2e38'; ctx.lineWidth = 10;
      ctx.beginPath(); ctx.arc(ax, ay, rad, Math.PI, TAU); ctx.stroke();
      ctx.lineWidth = 4;
      ctx.beginPath(); ctx.arc(ax, ay, rad - 40, Math.PI, TAU); ctx.stroke();
      for (var k2 = 1; k2 < 12; k2++) {
        var a = Math.PI + k2 * Math.PI / 12;
        ctx.beginPath(); ctx.moveTo(ax + Math.cos(a) * (rad - 40), ay + Math.sin(a) * (rad - 40));
        ctx.lineTo(ax + Math.cos(a) * rad, ay + Math.sin(a) * rad); ctx.stroke();
      }
      ctx.fillStyle = '#3a2a2a';
      ctx.fillRect(ax - rad - 40, HZ - 140, 40, 140);
      ctx.fillRect(ax + rad, HZ - 140, 40, 140);
      ctx.fillStyle = '#4a3434';
      ctx.fillRect(500, HZ - 330, 90, 330);
      ctx.beginPath(); ctx.moveTo(490, HZ - 330); ctx.lineTo(545, HZ - 400); ctx.lineTo(600, HZ - 330); ctx.fill();
      ctx.fillStyle = '#f2ead8';
      ctx.beginPath(); ctx.arc(545, HZ - 290, 30, 0, TAU); ctx.fill();
      ctx.strokeStyle = '#2a2a2a'; ctx.lineWidth = 4;
      var hand = t * 0.5;
      ctx.beginPath(); ctx.moveTo(545, HZ - 290); ctx.lineTo(545 + Math.sin(hand) * 22, HZ - 290 - Math.cos(hand) * 22);
      ctx.moveTo(545, HZ - 290); ctx.lineTo(545 + Math.sin(hand / 12 + 2) * 14, HZ - 290 - Math.cos(hand / 12 + 2) * 14);
      ctx.stroke();
      additive(ctx, function () { dot(ctx, '#fff2d8', 545, HZ - 290, 60, 0.35); });
      // the street, its lamps lighting one by one
      ctx.fillStyle = '#2a2830';
      ctx.fillRect(0, HZ, VW, VH - HZ);
      d.lamps.forEach(function (l) {
        ctx.fillStyle = '#16161c';
        ctx.fillRect(l.x - 3, HZ + 40, 6, 120);
        if (t < l.at) return;
        var flick = t - l.at < 0.3 ? (Math.sin(t * 70) > 0 ? 1 : 0.3) : 1;
        ctx.fillStyle = rgba('#ffcf7a', flick);
        ctx.fillRect(l.x - 9, HZ + 30, 18, 14);
        additive(ctx, function () { dot(ctx, '#ffb35a', l.x, HZ + 40, 90, 0.4 * flick); });
      });
      // the semaphores, dropping to clear
      var clear = seg(t, 0.55, 0.8);
      [180, 300].forEach(function (sx) {
        ctx.fillStyle = '#1a1a20';
        ctx.fillRect(sx - 4, HZ - 170, 8, 170);
        ctx.save(); ctx.translate(sx, HZ - 160); ctx.rotate(-0.7 * clear);
        ctx.fillStyle = '#c82a2a'; ctx.fillRect(0, -6, 60, 12);
        ctx.restore();
        additive(ctx, function () { dot(ctx, clear > 0.5 ? '#3aff6a' : '#ff3a2a', sx - 14, HZ - 160, 26, 0.9); });
      });
      // the track, and the train coming in under the arch
      ctx.fillStyle = '#4a4440';
      ctx.fillRect(0, HZ + 160, VW, 16);
      ctx.fillStyle = '#8a8680';
      ctx.fillRect(0, HZ + 156, VW, 4); ctx.fillRect(0, HZ + 174, VW, 4);
      var lx = lerp(-260, 860, outCubic(seg(t, 0.8, 2.6)));
      Art.puffs(ctx, d.puffs.map(function (p) {
        return { at: p.at + 0.8, x: lerp(-260, 860, outCubic(seg(p.at + 0.8, 0.8, 2.6))) + 12, y: HZ + 30,
                 vx: p.vx * 0.5, vy: p.vy, r: p.r, life: p.life };
      }), t, '#d8d0c8');
      loco(ctx, lx, HZ + 158, 1.0, '#141418', t * (1 - seg(t, 2.0, 2.6)), '#fff1b0');
      for (var c = 1; c < 4; c++) {
        ctx.fillStyle = c % 2 ? '#2f4a3a' : '#5a2a2a';
        ctx.fillRect(lx - 190 - c * 170, HZ + 90, 155, 62);
        ctx.fillStyle = '#ffe0a0';
        for (var w2 = 0; w2 < 5; w2++) ctx.fillRect(lx - 180 - c * 170 + w2 * 28, HZ + 104, 18, 16);
      }
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Union Terminal').toUpperCase();
      var k = outBack(seg(t, 1.85, 2.2), 1.2);
      if (k <= 0) return;
      ctx.save();
      ctx.translate(800, 230);
      ctx.scale(k, k);
      var w = 1040, h = 220;
      ctx.fillStyle = '#16161c';
      roundRect(ctx, -w / 2, -h / 2, w, h, 14); ctx.fill();
      ctx.strokeStyle = '#c8a03a'; ctx.lineWidth = 6;
      roundRect(ctx, -w / 2 + 8, -h / 2 + 8, w - 16, h - 16, 10); ctx.stroke();
      ctx.font = 'bold 22px ' + HEAVY; ctx.textBaseline = 'middle';
      ctx.fillStyle = '#c8a03a';
      spaced(ctx, 'DEPARTURES  ·  ARRIVALS', 0, -h / 2 + 34, 6);
      // the flaps: each letter rattles through the alphabet and lands
      var letters = name.split('');
      var cell = Math.min(62, (w - 80) / Math.max(1, letters.length));
      var x0 = -cell * letters.length / 2;
      var ABC = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
      letters.forEach(function (ch, i) {
        var land = 2.05 + i * 0.045;
        var shown = ch;
        if (t < land && ch !== ' ') shown = ABC.charAt(Math.floor((t * 40 + i * 7) % 26));
        var cx = x0 + i * cell + cell / 2;
        ctx.fillStyle = '#26262e';
        roundRect(ctx, cx - cell / 2 + 3, -40, cell - 6, 92, 6); ctx.fill();
        ctx.strokeStyle = '#0c0c10'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(cx - cell / 2 + 3, 6); ctx.lineTo(cx + cell / 2 - 3, 6); ctx.stroke();
        if (ch === ' ') return;
        ctx.font = 'bold ' + Math.floor(cell * 1.05) + 'px ' + HEAVY;
        ctx.textAlign = 'center';
        ctx.fillStyle = t < land ? '#c8b070' : '#ffd84a';
        ctx.fillText(shown, cx, 8);
        ctx.textAlign = 'left';
      });
      ctx.font = 'bold 20px ' + HEAVY;
      var blink = t > 2.7 && Math.sin(t * 6) > -0.3;
      ctx.fillStyle = blink ? '#3aff6a' : '#2a4a2a';
      spaced(ctx, 'PLATFORMS 1 & 7  ·  ON TIME', 0, h / 2 - 30, 4);
      ctx.restore();
    }
  });
})(window);
