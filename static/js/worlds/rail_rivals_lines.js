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

  // ============================================================== sweep
  /* Thunder Junction: the through freight on the main line.  The server
     says when one sets off (and where its head is in every state); the
     client runs it from there: the engine and its string of cars rolling
     down the line out of one portal and into the other, its headlight and
     smoke, the crossing gates coming down and their lamps flashing, the
     danger along the line while it comes, the call boxes -- and the bells,
     the whistle at the crossing and the clatter of every car going by. */
  function seeded(n) {
    var x = (n * 2654435761) % 4294967296;
    return function () {
      x = (x * 1664525 + 1013904223) % 4294967296;
      return x / 4294967296;
    };
  }

  var CAR_COLOURS = ['#7a2e22', '#6a3a26', '#8a4a2a', '#5a2a22', '#4a3a30', '#2f3a4a'];
  var HERALDS = ['#efe2c4', '#e8b23a', '#f2f2ee', '#c8d8e8'];

  Twists.sweep = function (ctx) {
    var CALL_R = 4.6, GAP = 1.2;
    var spec = {}, main = null, gates = [], calls = [], cross = {}, show = [-1e9, 1e9];
    var st = { phase: 'idle' }, stAt = 0;
    var cars = [], carsN = -1;
    var bellAt = 0, whistled = false, rumbleAt = 0, joints = -1, puffs = [], puffAt = 0;

    function now() { return performance.now() / 1000; }
    function load(map) {
      var mk = (map && map.markers) || {};
      spec = (mk.extra || {}).sweep || {};
      main = spec.path ? new ctx.Lane(spec.path) : null;
      gates = (spec.gates || []).map(function (g) { return { g: g, up: 1 }; });
      calls = ((mk.points || {}).call || []).map(function (m) { return m.p; });
      cross = spec.cross || {};
      show = spec.show || show;
      st = { phase: 'idle', next: 60, call: 0 };
      stAt = now();
      puffs = [];
    }
    function apply(tw) {
      if (!tw.sweep) return;
      st = tw.sweep;
      stAt = now();
    }
    function speed() { return st.speed || spec.speed || 40; }
    function trainLen() { return st.len || spec.length || 230; }
    function head() { return st.phase === 'run' ? (st.head || 0) + (now() - stAt) * speed() : -1e9; }
    function travel(s) { return (st.dir || 1) > 0 ? s : main.length - s; }
    function closed(lane) {
      if (st.phase !== 'run' || !main || cross[lane] === undefined) return false;
      return head() - trainLen() < travel(cross[lane]) + 6;
    }
    function anyClosed() { return closed('a') || closed('b'); }
    function waitLeft() { return Math.max(0, (st.next || 0) - (now() - stAt)); }

    // ------------------------------------------------------- the train
    function consist(n) {
      var rnd = seeded(n * 7919 + 13);
      var out = [{ t: 'engine', len: 22 }, { t: 'tender', len: 11 }];
      var used = 33 + GAP * 2, L = trainLen();
      var kinds = ['box', 'box', 'reefer', 'tank', 'hopper', 'stock', 'flat', 'box', 'hopper'];
      while (used + 14 + GAP + 13 <= L) {
        out.push({ t: kinds[Math.floor(rnd() * kinds.length)], len: 14,
                   c: CAR_COLOURS[Math.floor(rnd() * CAR_COLOURS.length)],
                   h: HERALDS[Math.floor(rnd() * HERALDS.length)], r: rnd() });
        used += 14 + GAP;
      }
      out.push({ t: 'caboose', len: 13 });
      var u = 0;
      out.forEach(function (c) { c.back = u + c.len / 2; u += c.len + GAP; });
      return out;
    }

    function part(renderer, base, yaw, kind, lp, size, colour, o) {
      ctx.local(renderer, kind, base, yaw, lp, size, colour, o);
    }

    function trucks(r, b, yaw, len) {
      for (var e = -1; e <= 1; e += 2) {
        part(r, b, yaw, 'box', [0, 1.2, e * (len / 2 - 3.2)], [4.0, 1.3, 3.4], '#1e1c1a', { m: 1 });
        for (var side = -1; side <= 1; side += 2) {
          for (var w = -1; w <= 1; w += 2) {
            part(r, b, yaw, 'cyl', [side * 1.95, 1.0, e * (len / 2 - 3.2) + w * 1.1], [1.6, 0.3, 1.6], '#141210',
                 { r: [0, 0, Math.PI / 2], m: 1 });
          }
        }
      }
      part(r, b, yaw, 'box', [0, 2.1, 0], [4.6, 0.5, len - 0.6], '#2a2826', { m: 1 });
    }

    function drawEngine(r, b, yaw, rolled, time) {
      var black = '#1e2022', trim = '#c8a040';
      part(r, b, yaw, 'box', [0, 1.7, -1], [4.2, 1.8, 20], '#141414', { m: 1 });
      for (var side = -1; side <= 1; side += 2) {
        part(r, b, yaw, 'box', [side * 2.5, 3.0, 0], [1.1, 0.3, 16], '#2a2826', { m: 1 });
        for (var k = 0; k < 4; k++) {
          part(r, b, yaw, 'cyl', [side * 2.05, 2.0, -5.6 + k * 3.4], [3.4, 0.36, 3.4], '#141210',
               { r: [0, 0, Math.PI / 2], m: 1 });
          part(r, b, yaw, 'cyl', [side * 2.2, 2.0, -5.6 + k * 3.4], [1.1, 0.4, 1.1], '#b8322a',
               { r: [0, 0, Math.PI / 2] });
        }
        // the side rods going round with the drivers
        var ph = rolled / 1.7;
        part(r, b, yaw, 'box', [side * 2.42, 2.0 + Math.sin(ph) * 0.8, -0.5 + Math.cos(ph) * 0.8],
             [0.18, 0.3, 10.6], '#8a8680', { m: 1 });
        part(r, b, yaw, 'box', [side * 2.42, 2.6 + Math.sin(ph) * 0.4, 6.0], [0.3, 1.0, 2.4], '#3a3836', { m: 1 });
      }
      part(r, b, yaw, 'cyl', [0, 4.9, 1.6], [4.8, 13, 4.8], black, { r: [Math.PI / 2, 0, 0], m: 1 });
      for (var band = 0; band < 3; band++) {
        part(r, b, yaw, 'cyl', [0, 4.9, -3 + band * 4], [4.96, 0.3, 4.96], trim, { r: [Math.PI / 2, 0, 0], m: 1 });
      }
      part(r, b, yaw, 'cyl', [0, 4.9, 8.8], [5.0, 2.4, 5.0], '#141414', { r: [Math.PI / 2, 0, 0], m: 1 });
      part(r, b, yaw, 'cyl', [0, 4.9, 10.02], [2.0, 0.1, 2.0], '#3a3836', { r: [Math.PI / 2, 0, 0], m: 1 });
      part(r, b, yaw, 'cyl', [0, 8.4, 7.6], [1.5, 3.0, 1.5], '#141414', { m: 1 });
      part(r, b, yaw, 'cyl', [0, 9.95, 7.6], [1.9, 0.3, 1.9], trim, { m: 1 });
      part(r, b, yaw, 'sph', [0, 7.5, 3.4], [1.8, 1.4, 2.0], trim, { m: 1 });
      part(r, b, yaw, 'sph', [0, 7.4, -1.2], [1.6, 1.3, 1.8], black, { m: 1 });
      part(r, b, yaw, 'sph', [0, 7.6, 5.4], [0.8, 0.9, 0.8], '#e8c060', { m: 1 });
      // the headlamp, the number board, the pilot
      part(r, b, yaw, 'box', [0, 7.6, 9.6], [1.6, 1.5, 1.4], '#2a2826', { m: 1 });
      part(r, b, yaw, 'box', [0, 7.6, 10.32], [1.2, 1.1, 0.06], '#fff6c8', { m: 2, e: 1 });
      part(r, b, yaw, 'box', [0, 6.2, 9.9], [2.2, 0.7, 0.06], '#efe2c4');
      part(r, b, yaw, 'box', [0, 1.3, 10.6], [4.4, 1.6, 1.4], '#8a2a1c', { r: [0.5, 0, 0] });
      part(r, b, yaw, 'box', [0, 2.6, 10.0], [4.6, 0.6, 0.8], '#b8322a');
      // the cab, its windows lit
      part(r, b, yaw, 'box', [0, 5.8, -6.6], [5.4, 5.6, 5.0], black, { m: 1 });
      part(r, b, yaw, 'box', [0, 8.8, -6.6], [6.0, 0.4, 5.8], '#141414', { m: 1 });
      for (var s2 = -1; s2 <= 1; s2 += 2) {
        part(r, b, yaw, 'box', [s2 * 2.72, 6.6, -6.2], [0.06, 1.6, 2.4], '#ffd88a', { m: 2 });
        part(r, b, yaw, 'box', [s2 * 1.2, 7.0, -4.08], [1.4, 1.2, 0.06], '#ffd88a', { m: 2 });
      }
      // the beam ahead of it down the line
      part(r, b, yaw, 'cone', [0, 7.6, 10.4 + 30], [16, 60, 10], '#fff2c0',
           { r: [-Math.PI / 2, 0, 0], a: 0.1, m: 2 });
    }

    function drawCar(r, b, yaw, c, time) {
      var len = c.len, roof = '#2a2624';
      if (c.t === 'tender') {
        part(r, b, yaw, 'box', [0, 4.2, 0], [5.2, 4.4, len - 1], '#1e2022', { m: 1 });
        part(r, b, yaw, 'box', [0, 6.6, 0.8], [4.4, 0.8, len - 3.4], '#1f1d1c', { st: 1 });
        part(r, b, yaw, 'box', [0, 6.5, -len / 2 + 1.4], [5.2, 0.6, 1.6], '#2a2826', { m: 1 });
        trucks(r, b, yaw, len);
        return;
      }
      trucks(r, b, yaw, len);
      if (c.t === 'box' || c.t === 'reefer') {
        var body = c.t === 'reefer' ? '#d8b048' : c.c;
        part(r, b, yaw, 'box', [0, 5.4, 0], [5.4, 6.0, len - 0.6], body);
        part(r, b, yaw, 'box', [0, 8.5, 0], [5.6, 0.25, len - 0.4], c.t === 'reefer' ? '#6a3a26' : roof);
        part(r, b, yaw, 'box', [0, 8.72, 0], [0.9, 0.2, len - 0.6], '#6a4e34');
        for (var side = -1; side <= 1; side += 2) {
          if (c.t === 'box') {
            part(r, b, yaw, 'box', [side * 2.72, 5.0, 0.4], [0.06, 5.0, 4.4], '#3a2a22');
            part(r, b, yaw, 'box', [side * 2.73, 7.0, -3.8], [0.04, 0.7, 3.8], c.h);
          } else {
            part(r, b, yaw, 'box', [side * 2.72, 5.0, 0], [0.06, 4.6, 3.6], '#c8a040');
            part(r, b, yaw, 'box', [side * 2.73, 7.0, -3.6], [0.04, 0.8, 4.4], '#3a2a22');
          }
          part(r, b, yaw, 'box', [side * 2.74, 5.4, len / 2 - 0.9], [0.1, 5.4, 0.3], '#2a2826', { m: 1 });
        }
        if (c.t === 'reefer') {
          for (var hz = -1; hz <= 1; hz += 2) part(r, b, yaw, 'box', [0, 8.75, hz * (len / 2 - 1.5)], [2.4, 0.2, 1.6], '#8a8680', { m: 1 });
        }
      } else if (c.t === 'tank') {
        part(r, b, yaw, 'cyl', [0, 5.0, 0], [4.8, len - 1.2, 4.8], c.r < 0.5 ? '#1e2022' : '#a8aaa8',
             { r: [Math.PI / 2, 0, 0], m: 1 });
        part(r, b, yaw, 'cyl', [0, 7.6, 0], [2.0, 1.2, 2.0], '#2a2826', { m: 1 });
        for (var ring = -1; ring <= 1; ring += 2) {
          part(r, b, yaw, 'cyl', [0, 5.0, ring * 3.2], [4.96, 0.25, 4.96], '#3a3836', { r: [Math.PI / 2, 0, 0], m: 1 });
        }
        part(r, b, yaw, 'box', [0, 2.7, 0], [3.0, 0.6, len - 1], '#2a2826', { m: 1 });
      } else if (c.t === 'hopper') {
        part(r, b, yaw, 'box', [0, 5.2, 0], [5.4, 5.0, len - 0.8], c.r < 0.5 ? '#3a3a3c' : c.c);
        part(r, b, yaw, 'box', [0, 7.9, 0], [4.8, 0.7, len - 2], '#1f1d1c', { st: 1 });
        for (var bay = -1; bay <= 1; bay++) part(r, b, yaw, 'box', [0, 2.5, bay * 4], [4.6, 1.2, 2.4], '#2a2826', { m: 1 });
      } else if (c.t === 'stock') {
        part(r, b, yaw, 'box', [0, 8.4, 0], [5.6, 0.3, len - 0.4], roof);
        part(r, b, yaw, 'box', [0, 2.8, 0], [5.4, 0.8, len - 0.6], '#6a4a30');
        for (var slat = 0; slat < 5; slat++) {
          for (var sd = -1; sd <= 1; sd += 2) {
            part(r, b, yaw, 'box', [sd * 2.6, 3.8 + slat * 1.0, 0], [0.2, 0.5, len - 0.6], '#9a6a40');
          }
        }
        for (var post = -2; post <= 2; post++) part(r, b, yaw, 'box', [0, 5.6, post * 3.2], [5.5, 5.4, 0.4], '#7a5232');
        // somebody's looking out between the slats
        var nod = Math.sin(time * 2 + c.r * 9) * 0.2;
        part(r, b, yaw, 'box', [2.0, 5.3 + nod, -2.0], [1.4, 1.4, 1.8], '#7a4a2a');
        part(r, b, yaw, 'box', [2.6, 5.1 + nod, -2.0], [0.4, 0.8, 1.0], '#f2ece0');
        part(r, b, yaw, 'box', [2.0, 6.15 + nod, -2.6], [0.3, 0.4, 0.3], '#e8dcc8');
        part(r, b, yaw, 'box', [2.0, 6.15 + nod, -1.4], [0.3, 0.4, 0.3], '#e8dcc8');
      } else if (c.t === 'flat') {
        part(r, b, yaw, 'box', [0, 2.8, 0], [5.4, 0.6, len - 0.4], '#6a4a30');
        if (c.r < 0.5) {
          for (var lay = 0; lay < 3; lay++) part(r, b, yaw, 'box', [0, 3.6 + lay * 0.9, 0], [4.4, 0.85, len - 2 - lay], lay % 2 ? '#c89a62' : '#b8875a');
          part(r, b, yaw, 'box', [0, 5.2, 0], [4.6, 0.2, 0.4], '#3a3836', { m: 1 });
        } else {
          // a threshing machine bound for somebody's harvest
          part(r, b, yaw, 'box', [0, 5.0, 1], [3.6, 3.6, 8], '#c43a28');
          part(r, b, yaw, 'cyl', [0, 7.4, 4.6], [1.0, 3.0, 1.0], '#8a8680', { r: [0.7, 0, 0], m: 1 });
          for (var wh = -1; wh <= 1; wh += 2) {
            part(r, b, yaw, 'cyl', [wh * 2.0, 4.2, -3.5], [2.4, 0.4, 2.4], '#e8b23a', { r: [0, 0, Math.PI / 2] });
          }
        }
      } else if (c.t === 'caboose') {
        part(r, b, yaw, 'box', [0, 5.3, 0], [5.4, 5.6, len - 3.4], '#a8281e');
        part(r, b, yaw, 'box', [0, 8.25, 0], [5.8, 0.3, len - 2.6], roof);
        part(r, b, yaw, 'box', [0, 9.4, 0], [3.6, 2.0, 3.8], '#a8281e');
        part(r, b, yaw, 'box', [0, 10.5, 0], [4.2, 0.3, 4.4], roof);
        for (var cs = -1; cs <= 1; cs += 2) {
          for (var w2 = -1; w2 <= 1; w2 += 2) {
            part(r, b, yaw, 'box', [cs * 2.72, 6.0, w2 * 2.4], [0.06, 1.4, 1.6], '#ffd88a', { m: 2 });
          }
          part(r, b, yaw, 'box', [cs * 1.82, 9.5, 0], [0.06, 1.0, 2.4], '#ffd88a', { m: 2 });
          part(r, b, yaw, 'box', [0, 2.8, cs * (len / 2 - 0.9)], [5.0, 0.3, 1.8], '#2a2826', { m: 1 });
          part(r, b, yaw, 'box', [0, 4.2, cs * (len / 2 - 0.2)], [5.0, 0.12, 0.12], '#c8a040', { m: 1 });
        }
        // the markers on its tail, and the brakeman waving his lantern
        for (var mk2 = -1; mk2 <= 1; mk2 += 2) {
          part(r, b, yaw, 'box', [mk2 * 2.2, 7.4, -len / 2 + 1.0], [0.6, 0.8, 0.6], '#ff3a2a', { m: 2 });
        }
        var wave = Math.sin(time * 5) * 0.6;
        part(r, b, yaw, 'box', [1.0, 4.0, -len / 2 + 0.9], [0.9, 1.6, 0.6], '#3a4a6a');
        part(r, b, yaw, 'box', [1.0, 5.2, -len / 2 + 0.9], [0.7, 0.7, 0.7], '#f5cd30');
        part(r, b, yaw, 'box', [1.0, 5.65, -len / 2 + 0.9], [0.8, 0.25, 0.8], '#2a3a5a');
        part(r, b, yaw, 'box', [1.75, 4.7 + wave * 0.4, -len / 2 + 0.6 - wave * 0.3], [0.3, 1.1, 0.3], '#f5cd30');
        part(r, b, yaw, 'box', [1.9, 4.1 + wave * 0.8, -len / 2 + 0.4 - wave * 0.5], [0.4, 0.5, 0.4], '#ffcf6a', { m: 2 });
      }
    }

    function drawTrain(r, time, dt) {
      if (st.phase !== 'run' || !main) return;
      if (carsN !== (st.n || 0)) { cars = consist(st.n || 0); carsN = st.n || 0; }
      var h = head(), flip = (st.dir || 1) < 0 ? Math.PI : 0;
      for (var i = 0; i < cars.length; i++) {
        var c = cars[i];
        var s = travel(h - c.back);
        if (s < show[0] - c.len || s > show[1] + c.len) continue;
        var at = main.at(s);
        var base = [at[0], (at[3] || 0) + 0.44, at[1], 0];
        if (c.t === 'engine') {
          drawEngine(r, base, at[2] + flip, h, time);
          var stack = [at[0] + Math.sin(at[2] + flip) * 7.6, base[1] + 10.2, at[1] + Math.cos(at[2] + flip) * 7.6];
          puffAt -= dt;
          if (puffAt <= 0) {
            puffAt = 0.05;
            puffs.push({ x: stack[0], y: stack[1], z: stack[2], t: 0, s: 1.6 + Math.random() * 0.8 });
          }
        } else {
          drawCar(r, base, at[2] + flip, c, time);
        }
      }
    }

    function drawPuffs(r, dt) {
      puffs = puffs.filter(function (q) {
        q.t += dt;
        if (q.t > 2.6) return false;
        var k = q.t / 2.6;
        q.y += dt * (7 - k * 4);
        q.x += dt * 2.0;
        var size = q.s * (1 + k * 3.4);
        var shade = 0.22 + k * 0.45;
        r.pushRaw('sph', q.x, q.y, q.z, 0, 0, 0, size, size * 0.85, size, [shade, shade, shade * 1.02],
                  0.6 * (1 - k), 0, 0, 0, null);
        return true;
      });
      if (puffs.length > 140) puffs.splice(0, puffs.length - 140);
    }

    // ---------------------------------------------- the crossings
    function drawGates(r, time, dt) {
      gates.forEach(function (gate) {
        var g = gate.g, shut = closed(g.lane);
        gate.up = gate.up + ((shut ? 0 : 1) - gate.up) * Math.min(1, dt * (shut ? 1.6 : 1.1));
        var th = gate.up * Math.PI / 2 * 0.96, yaw = g.yaw, L = g.len || 7;
        var dir = [Math.sin(yaw) * Math.cos(th), Math.sin(th), Math.cos(yaw) * Math.cos(th)];
        var n = 6, seg = L / n;
        for (var i = 0; i < n; i++) {
          var u = (i + 0.5) * seg + 0.6;
          r.pushRaw('box', g.p[0] + dir[0] * u, g.p[1] + dir[1] * u, g.p[2] + dir[2] * u, -th, yaw, 0,
                    0.32, 0.32, seg + 0.02, i % 2 ? [0.95, 0.95, 0.92] : [0.82, 0.12, 0.1], 1, 0, 0, 0, null);
        }
        var on = shut && Math.sin(time * 7.5) > 0;
        var tip = [g.p[0] + dir[0] * (L + 0.5), g.p[1] + dir[1] * (L + 0.5), g.p[2] + dir[2] * (L + 0.5)];
        r.pushRaw('sph', tip[0], tip[1], tip[2], 0, 0, 0, 0.45, 0.45, 0.45, on ? [1, 0.25, 0.15] : [0.35, 0.08, 0.06],
                  1, 0, 2, on ? 1 : 0, null);
        (g.lamps || []).forEach(function (lp, k) {
          var lit = shut && ((Math.sin(time * 7.5) > 0) === (k === 0));
          r.pushRaw('sph', lp[0], lp[1], lp[2], 0, 0, 0, 0.9, 0.9, 0.9, lit ? [1, 0.2, 0.12] : [0.3, 0.06, 0.05],
                    1, 0, 2, lit ? 1 : 0, null);
          if (lit) r.pushRaw('sph', lp[0], lp[1], lp[2], 0, 0, 0, 3.4, 3.4, 3.4, [1, 0.3, 0.2], 0.16, 0, 2, 0.5, null);
        });
      });
    }

    function drawDanger(r, time) {
      if (st.phase !== 'run' || !main) return;
      var p = ctx.client.local.pos, sp = main.project(p[0], p[2]);
      var h = head(), tail = h - trainLen(), half = spec.half || 4;
      var pulse = 0.12 + 0.1 * Math.abs(Math.sin(time * 5));
      for (var s = sp - 110; s <= sp + 110; s += 8) {
        if (s < show[0] || s > show[1]) continue;
        var u = travel(s);
        if (u < tail - 2 || u > h + 220) continue;
        var at = main.at(s);
        r.pushRaw('box', at[0], (at[3] || 0) + 0.62, at[1], 0, at[2], 0, half * 2, 0.04, 7.6, [1, 0.25, 0.12],
                  pulse, 0, 2, 0.4, null);
      }
    }

    function drawCalls(r, time) {
      var p = ctx.client.local.pos, open = st.phase !== 'run' && st.call;
      calls.forEach(function (box, i) {
        if (flat(box, p) > 90) return;
        var pulse = open ? 0.18 + 0.12 * Math.sin(time * 4 + i) : 0.06;
        r.pushRaw('cyl', box[0], box[1] + 0.08, box[2], 0, 0, 0, CALL_R * 2, 0.05, CALL_R * 2,
                  open ? [1, 0.82, 0.3] : [0.6, 0.6, 0.6], pulse, 0, 2, 0.4, null);
        if (open) {
          var bob = Math.sin(time * 2.4 + i) * 0.3;
          r.pushRaw('box', box[0], box[1] + 4.2 + bob, box[2], 0, time * 1.2, 0, 1.0, 1.4, 0.2, [1, 0.85, 0.35], 0.9, 0, 2, 0.6, null);
        }
      });
    }

    // ------------------------------------------------------ the sounds
    function sounds(time) {
      if (!main) return;
      var audio = ctx.client.audio, p = ctx.client.local.pos;
      var mid = main.at(cross.a !== undefined ? cross.a : main.length / 2);
      var toX = Math.hypot(mid[0] - p[0], mid[1] - p[2]);
      if (anyClosed() && toX < 300 && time - bellAt > 0.55) {
        bellAt = time;
        audio.play('rr_xbell', { volume: Math.max(0.12, 0.7 * (1 - toX / 300)) });
      }
      if (st.phase !== 'run') { whistled = false; joints = -1; return; }
      var h = head();
      var ahead = travel(cross.a !== undefined ? cross.a : main.length / 2) - h;
      if (!whistled && ahead < 150 && ahead > 0) {
        whistled = true;
        audio.play('rr_horn', { volume: Math.max(0.3, 0.9 * (1 - toX / 500)) });
      }
      // the clatter of the cars going by the nearest point of the line
      var sp = main.project(p[0], p[2]), at = main.at(sp);
      var off = Math.hypot(at[0] - p[0], at[1] - p[2]);
      var u = travel(sp), count = 0;
      cars.forEach(function (c) { if (h - c.back - c.len / 2 > u) count += 1; });
      if (count > joints && joints >= 0 && off < 160 && u > h - trainLen() - 4) {
        audio.play('rr_clack', { volume: Math.max(0.1, 0.8 * (1 - off / 160)) });
      }
      joints = count;
      if (off < 140 && u > h - trainLen() - 20 && u < h + 160 && time - rumbleAt > 0.42) {
        rumbleAt = time;
        audio.play('rr_rumble', { volume: Math.max(0.1, 0.6 * (1 - off / 140)) });
      }
    }

    function draw(renderer, time, dt) {
      drawTrain(renderer, time, dt);
      drawPuffs(renderer, dt);
      drawGates(renderer, time, dt);
      drawDanger(renderer, time);
      drawCalls(renderer, time);
      sounds(time);
    }

    function here(p) {
      for (var i = 0; i < calls.length; i++) {
        if (flat(calls[i], p) > CALL_R) continue;
        if (st.phase === 'run') return { k: 'callx', text: 'The main line is occupied' };
        if (st.call) return { k: 'call', text: 'Hold <b>E</b> to call the through freight down now' };
        var left = waitLeft();
        if (left <= 14) return { k: 'callx', text: 'The freight is due in ' + Math.ceil(left) + 's anyway' };
        return { k: 'callx', text: 'The wire is busy &bull; try again in a moment' };
      }
      return null;
    }

    function hud() {
      if (st.phase === 'run') {
        if (!anyClosed()) return 'The freight is clearing the junction';
        var h = head();
        var past = Object.keys(cross).every(function (l) { return h > travel(cross[l]); });
        return past ? '<b>The freight is going by</b> &bull; both crossings shut'
          : '<b>FREIGHT COMING</b> &bull; crossings shut &bull; get off the main line';
      }
      var left = waitLeft(), m = Math.floor(left / 60), s = Math.floor(left % 60);
      return 'Through freight due in <b>' + m + ':' + ('0' + s).slice(-2) + '</b>' +
        (st.call ? ' &bull; the call boxes are open' : '');
    }

    function message(msg) {
      var me = ctx.client.myTeam;
      if (msg.k === 'sweep') {
        if (msg.on) {
          st = { phase: 'run', dir: msg.dir || 1, head: 0, speed: msg.speed || speed(), len: msg.len || trainLen(),
                 n: msg.n || 0 };
          stAt = now();
          whistled = false;
          if (msg.by) {
            var ours = msg.team === me;
            ctx.say('sweep', ours ? 'FREIGHT CALLED ON THEM' : 'THEY CALLED THE FREIGHT', ours ? 'go' : 'bad', 'rr_xbell',
                    ctx.esc(msg.by) + ' called the through freight down');
          } else {
            ctx.say('sweep', 'FREIGHT COMING', 'bad', 'rr_xbell', 'The crossings are shut &bull; get off the main line');
          }
        } else {
          st = { phase: 'idle', next: 60, call: 0 };
          stAt = now();
        }
        return true;
      }
      if (msg.k === 'beat') {
        var mine = msg.team === me;
        ctx.say('beat' + msg.team, mine ? 'BEAT THE FREIGHT!' : 'THEY BEAT THE FREIGHT', mine ? 'go' : 'bad', 'rr_whistle');
        return true;
      }
      return false;
    }

    return {
      load: load, apply: apply, draw: draw, here: here, hud: hud, message: message,
      held: function (reason) { return reason === 'freight' ? 'HELD FOR THE FREIGHT' : ''; },
      labels: { call: 'Calling the freight down' },
      carryName: function (kind) { return kind; }
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
    GA.register('rr_xbell', function (vol) {
      // a crossing bell: one hard ding with its ring
      this.tone({ type: 'triangle', freq: 1320, freqEnd: 1300, dur: 0.32, gain: 0.12 * vol });
      this.tone({ type: 'sine', freq: 2640, freqEnd: 2600, dur: 0.2, gain: 0.05 * vol });
      this.noise({ filter: 'bandpass', freq: 4200, freqEnd: 3000, dur: 0.03, gain: 0.08 * vol });
    });
    GA.register('rr_horn', function (vol) {
      // a steam chime at a crossing: long, long, short, long
      var notes = [[0, 900], [1050, 900], [2100, 380], [2620, 1300]];
      notes.forEach(function (n) {
        this.later(n[0], function () {
          var d = n[1] / 1000;
          this.tone({ type: 'sawtooth', freq: 277, freqEnd: 270, dur: d, gain: 0.05 * vol });
          this.tone({ type: 'sawtooth', freq: 349, freqEnd: 342, dur: d, gain: 0.04 * vol });
          this.tone({ type: 'triangle', freq: 415, freqEnd: 408, dur: d, gain: 0.05 * vol });
          this.noise({ filter: 'bandpass', freq: 1800, dur: d, gain: 0.02 * vol });
        });
      }, this);
    });
    GA.register('rr_clack', function (vol) {
      // a car's wheels over a rail joint: clickety-clack
      this.noise({ filter: 'bandpass', freq: 900, freqEnd: 500, dur: 0.06, gain: 0.22 * vol });
      this.later(90, function () { this.noise({ filter: 'bandpass', freq: 800, freqEnd: 420, dur: 0.06, gain: 0.2 * vol }); });
    });
    GA.register('rr_rumble', function (vol) {
      this.noise({ freq: 220, freqEnd: 120, dur: 0.6, gain: 0.16 * vol });
      this.tone({ type: 'sawtooth', freq: 38, freqEnd: 34, dur: 0.5, gain: 0.04 * vol });
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
  // --------------------------------------------------- Thunder Junction
  /* Storm light on the prairie.  At the crossing the bells start and the
     lamps swing, the gate comes down across the line, a headlamp grows out
     of the rain -- lightning hits the tall elevator's rod -- and the
     through freight thunders across the frame, engine, cars and caboose,
     the whistle going.  The name comes up on a crossbuck. */
  function freightCar(ctx, x, y, kind, colour, t) {
    var w = 300, h = 120;
    ctx.fillStyle = '#16161a';
    ctx.fillRect(x - w / 2 + 6, y - 22, w - 12, 12);
    [-1, 1].forEach(function (e) {
      [-1, 1].forEach(function (k) {
        ctx.fillStyle = '#0c0c0e';
        ctx.beginPath(); ctx.arc(x + e * (w / 2 - 48) + k * 22, y - 8, 15, 0, TAU); ctx.fill();
        ctx.fillStyle = '#5a5650';
        ctx.beginPath(); ctx.arc(x + e * (w / 2 - 48) + k * 22, y - 8, 5, 0, TAU); ctx.fill();
      });
    });
    if (kind === 'tank') {
      ctx.fillStyle = colour;
      roundRect(ctx, x - w / 2 + 10, y - 22 - h * 0.78, w - 20, h * 0.74, 44); ctx.fill();
      ctx.fillRect(x - 22, y - 22 - h * 0.95, 44, 22);
      ctx.fillStyle = 'rgba(255,255,255,0.12)';
      ctx.fillRect(x - w / 2 + 30, y - 22 - h * 0.66, w - 60, 8);
    } else if (kind === 'hopper') {
      ctx.fillStyle = colour;
      ctx.beginPath();
      ctx.moveTo(x - w / 2 + 6, y - 22 - h); ctx.lineTo(x + w / 2 - 6, y - 22 - h);
      ctx.lineTo(x + w / 2 - 30, y - 30); ctx.lineTo(x - w / 2 + 30, y - 30); ctx.fill();
      ctx.fillStyle = '#1a1816';
      ctx.fillRect(x - w / 2 + 14, y - 30 - h, w - 28, 14);
    } else if (kind === 'stock') {
      ctx.fillStyle = '#2a2420';
      ctx.fillRect(x - w / 2 + 6, y - 22 - h - 6, w - 12, 10);
      for (var sl = 0; sl < 6; sl++) {
        ctx.fillStyle = colour;
        ctx.fillRect(x - w / 2 + 6, y - 30 - sl * 19, w - 12, 11);
      }
      ctx.fillStyle = '#8a5a3a';
      ctx.fillRect(x - 40, y - 88, 34, 22);
      ctx.fillStyle = '#f2ece0';
      ctx.fillRect(x - 46, y - 82, 10, 12);
    } else if (kind === 'caboose') {
      ctx.fillStyle = '#a8281e';
      ctx.fillRect(x - w / 2 + 40, y - 22 - h, w - 80, h - 2);
      ctx.fillRect(x - 50, y - 22 - h - 40, 100, 42);
      ctx.fillStyle = '#2a2420';
      ctx.fillRect(x - w / 2 + 30, y - 24 - h, w - 60, 8);
      ctx.fillRect(x - 60, y - 22 - h - 46, 120, 8);
      ctx.fillStyle = '#ffd88a';
      [-1, 1].forEach(function (k) { ctx.fillRect(x + k * 70 - 18, y - 22 - h + 26, 36, 28); });
      ctx.fillRect(x - 30, y - 22 - h - 30, 60, 18);
      additive(ctx, function () { dot(ctx, '#ff3a2a', x + w / 2 - 44, y - 22 - h + 12, 30, 0.8); });
    } else {
      ctx.fillStyle = colour;
      ctx.fillRect(x - w / 2 + 6, y - 22 - h, w - 12, h);
      ctx.fillStyle = '#2a2420';
      ctx.fillRect(x - w / 2 + 2, y - 26 - h, w - 4, 8);
      ctx.fillStyle = 'rgba(0,0,0,0.35)';
      ctx.fillRect(x - 40, y - 18 - h + 14, 80, h - 18);
      ctx.fillStyle = 'rgba(255,240,210,0.7)';
      ctx.fillRect(x - w / 2 + 26, y - h + 4, 70, 8);
    }
  }

  Intro.register('rr_thunder', {
    name: 'Thunder Junction',
    tagline: 'When the bells ring, the crossing is shut. Call the freight down on them -- and keep off the main line.',
    accent: '#ffc24a',
    cues: [[0.3, 'rr_xbell', 0.6], [0.85, 'rr_xbell', 0.6], [1.25, 'rr_crack', 0.9], [1.4, 'rr_xbell', 0.6],
           [1.55, 'rr_rumble', 0.9], [1.75, 'rr_horn', 0.7], [1.95, 'rr_clack', 0.8], [2.2, 'rr_clack', 0.8],
           [2.45, 'rr_clack', 0.8], [2.7, 'rr_clack', 0.8], [2.95, 'rr_clack', 0.7]],
    shakes: [[1.25, 7, 0.3], [1.65, 4, 1.4]],
    tagY: 430, tagAt: 3.0,
    setup: function (r) {
      var d = { rain: [], breaks: [], cars: [], puffs: Art.makePuffs(r, 22, 0, 9, 0), grass: [] };
      for (var i = 0; i < 160; i++) d.rain.push({ x: r() * (VW + 300), y: r() * VH, s: between(r, 0.6, 1.4) });
      var x = -40;
      while (x < VW + 60) {
        var w = between(r, 90, 200);
        d.breaks.push({ x: x, w: w, h: between(r, 60, 150) });
        x += w * 0.8;
      }
      var kinds = ['box', 'tank', 'stock', 'box', 'hopper', 'box', 'tank', 'box'];
      var colours = ['#6a2e22', '#1e1e22', '#7a5232', '#5a3a26', '#3a3a3c', '#7a2e22', '#a8aaa8', '#4a3a30'];
      for (i = 0; i < kinds.length; i++) d.cars.push({ kind: kinds[i], c: colours[i] });
      d.cars.push({ kind: 'caboose', c: '#a8281e' });
      for (i = 0; i < 60; i++) d.grass.push({ x: r() * VW, y: between(r, 700, 860), h: between(r, 10, 26) });
      return d;
    },
    draw: function (ctx, t, d) {
      var HZ = 600;
      var strike = t >= 1.25 && t < 1.6 ? 1 - (t - 1.25) / 0.35 : 0;
      var sky = ctx.createLinearGradient(0, 0, 0, HZ);
      sky.addColorStop(0, '#161c24');
      sky.addColorStop(0.55, '#3a4248');
      sky.addColorStop(0.9, '#8a8a70');
      sky.addColorStop(1, '#e0b878');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, VW, HZ + 2);
      // the cloud deck rolling over
      for (var c = 0; c < 9; c++) {
        var cx = ((c * 230 + t * 30) % (VW + 400)) - 200;
        ctx.fillStyle = rgba('#20262e', 0.7);
        ctx.beginPath(); ctx.ellipse(cx, 90 + (c % 3) * 40, 220, 70, 0, 0, TAU); ctx.fill();
      }
      // the twister on the horizon, lit up by the strike
      var tw = 0.35 + strike * 0.6;
      ctx.fillStyle = rgba('#4a4a52', tw);
      ctx.beginPath();
      ctx.moveTo(1180, 170); ctx.quadraticCurveTo(1230 + Math.sin(t) * 10, 380, 1262 + Math.sin(t * 1.3) * 12, HZ);
      ctx.lineTo(1274 + Math.sin(t * 1.3) * 12, HZ);
      ctx.quadraticCurveTo(1260 + Math.sin(t) * 10, 380, 1300, 170); ctx.fill();
      // the breaks and the prairie
      d.breaks.forEach(function (m, i) {
        ctx.fillStyle = i % 2 ? '#3a2c24' : '#46342a';
        ctx.fillRect(m.x, HZ - m.h, m.w, m.h + 2);
        ctx.fillStyle = 'rgba(160,120,80,0.25)';
        ctx.fillRect(m.x, HZ - m.h * 0.6, m.w, 6);
      });
      ctx.fillStyle = '#3a4a2a';
      ctx.fillRect(0, HZ, VW, VH - HZ);
      // the grain elevators and the water tank, black against the light
      ctx.fillStyle = '#241c1a';
      [[150, 250, 70], [240, 290, 80], [340, 330, 90]].forEach(function (e) {
        ctx.fillRect(e[0], HZ - e[1], e[2], e[1]);
        ctx.fillRect(e[0] + e[2] * 0.25, HZ - e[1] - 40, e[2] * 0.5, 40);
        ctx.beginPath(); ctx.moveTo(e[0] + e[2] * 0.2, HZ - e[1] - 40); ctx.lineTo(e[0] + e[2] * 0.5, HZ - e[1] - 62);
        ctx.lineTo(e[0] + e[2] * 0.8, HZ - e[1] - 40); ctx.fill();
      });
      ctx.fillRect(383, HZ - 452, 4, 60);
      ctx.fillRect(900, HZ - 170, 8, 110);
      ctx.fillRect(960, HZ - 170, 8, 110);
      ctx.beginPath(); ctx.ellipse(934, HZ - 200, 54, 40, 0, 0, TAU); ctx.fill();
      ctx.fillRect(880, HZ - 214, 108, 16);
      // the main line across the frame
      var TY = 680;
      ctx.fillStyle = '#4a4238';
      ctx.fillRect(0, TY - 6, VW, 20);
      ctx.fillStyle = '#8a8680';
      ctx.fillRect(0, TY - 8, VW, 4); ctx.fillRect(0, TY + 8, VW, 4);
      // the headlamp coming out of the rain, far off to the right
      var come = seg(t, 0.55, 1.6);
      if (t < 1.75) {
        var hx = lerp(1700, 1500, come), hr = lerp(6, 60, come * come);
        additive(ctx, function () {
          dot(ctx, '#fff2c0', hx, TY - 90 * come, hr * 3, 0.5 + come * 0.4);
          dot(ctx, '#ffffff', hx, TY - 90 * come, hr, 0.9);
        });
      }
      // the freight: engine first, right to left, the cars after it
      var run = seg(t, 1.55, 3.6);
      var lx = lerp(VW + 260, -2900, run);
      Art.puffs(ctx, d.puffs.map(function (p) {
        var born = p.at * 0.25 + 1.55;
        return { at: born, x: lerp(VW + 260, -2900, seg(born, 1.55, 3.6)) - 30, y: TY - 236 - (p.off % 5) * 12,
                 vx: 90 - p.vx * 3, vy: p.vy * 2.0, r: p.r * (1.1 + (p.off % 3) * 0.35), life: p.life };
      }), t, '#62626a');
      if (run > 0) {
        locoLeft(ctx, lx, TY + 6, 1.7, '#141416', t * 3, '#fff2c0');
        additive(ctx, function () { dot(ctx, '#fff2c0', lx - 100, TY - 120, 120, 0.4); });
        d.cars.forEach(function (car, i) {
          var x = lx + 330 + i * 312;
          if (x < -200 || x > VW + 200) return;
          freightCar(ctx, x, TY + 6, car.kind, car.c, t);
        });
      }
      // the crossing in front: the lane coming at us, the crossbuck, the lamps, the gate
      ctx.fillStyle = '#5a5046';
      ctx.beginPath(); ctx.moveTo(700, TY + 14); ctx.lineTo(900, TY + 14); ctx.lineTo(1160, VH); ctx.lineTo(440, VH); ctx.fill();
      ctx.strokeStyle = '#8a8680'; ctx.lineWidth = 5;
      ctx.beginPath(); ctx.moveTo(750, TY + 14); ctx.lineTo(560, VH); ctx.moveTo(850, TY + 14); ctx.lineTo(1040, VH); ctx.stroke();
      d.grass.forEach(function (g) {
        ctx.strokeStyle = '#5a6a3a'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(g.x, g.y); ctx.lineTo(g.x + 6 + Math.sin(t * 3 + g.x) * 4, g.y - g.h); ctx.stroke();
      });
      var px = 1240;
      ctx.fillStyle = '#e8e2d4';
      ctx.fillRect(px - 8, 500, 16, VH - 500);
      var on = t > 0.3 && Math.sin(t * 9) > 0;
      [-1, 1].forEach(function (k, i) {
        ctx.fillStyle = '#141414';
        ctx.beginPath(); ctx.arc(px + k * 46, 630, 26, 0, TAU); ctx.fill();
        var lit = t > 0.3 && (on === (i === 0));
        additive(ctx, function () { dot(ctx, '#ff3a2a', px + k * 46, 630, lit ? 70 : 10, lit ? 0.95 : 0.2); });
      });
      ctx.fillStyle = '#141414';
      ctx.fillRect(px - 72, 620, 144, 8);
      var down = outCubic(seg(t, 0.5, 1.2));
      ctx.save();
      ctx.translate(px - 20, 668);
      ctx.rotate(-Math.PI / 2 * (1 - down) - 0.02);
      for (var sgm = 0; sgm < 8; sgm++) {
        ctx.fillStyle = sgm % 2 ? '#f2f2ee' : '#c82a1e';
        ctx.fillRect(-sgm * 90 - 90, -9, 90, 18);
      }
      additive(ctx, function () { dot(ctx, '#ff3a2a', -730, 0, 30, on ? 0.9 : 0.25); });
      ctx.restore();
      // rain
      ctx.strokeStyle = 'rgba(190,205,225,0.35)'; ctx.lineWidth = 2;
      ctx.beginPath();
      d.rain.forEach(function (q) {
        var y = (q.y + t * 900 * q.s) % VH;
        var x = (q.x - t * 220 * q.s) % (VW + 300);
        if (x < -100) x += VW + 300;
        ctx.moveTo(x, y); ctx.lineTo(x - 10 * q.s, y + 30 * q.s);
      });
      ctx.stroke();
      // the strike on the elevator's rod, and the whole sky going white
      if (strike > 0) {
        ctx.strokeStyle = rgba('#f4f6ff', strike); ctx.lineWidth = 6;
        ctx.beginPath(); ctx.moveTo(470, 90);
        [[440, 110], [452, 120], [410, 132], [385, HZ - 452]].forEach(function (pt) { ctx.lineTo(pt[0], pt[1]); });
        ctx.stroke();
        additive(ctx, function () { dot(ctx, '#e8eeff', 385, HZ - 452, 160, strike); });
        ctx.fillStyle = rgba('#eef2ff', strike * 0.55);
        ctx.fillRect(0, 0, VW, VH);
      }
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Thunder Junction').toUpperCase();
      var words = name.split(' ');
      var top = words.slice(0, Math.ceil(words.length / 2)).join(' ');
      var bottom = words.slice(Math.ceil(words.length / 2)).join(' ') || top;
      var k = outBack(seg(t, 1.9, 2.3), 1.3);
      if (k <= 0) return;
      ctx.save();
      ctx.translate(800, 262);
      ctx.scale(k, k);
      // a word to a board, split round the middle where the boards cross
      [[top, 0.38], [bottom, -0.38]].forEach(function (b) {
        ctx.save();
        ctx.rotate(b[1]);
        var w = 700, h = 84, gap = 150;
        ctx.fillStyle = '#0e0e10';
        ctx.fillRect(-w / 2 + 6, -h / 2 + 8, w, h);
        ctx.fillStyle = '#f2ede0';
        ctx.fillRect(-w / 2, -h / 2, w, h);
        ctx.strokeStyle = '#141414'; ctx.lineWidth = 6;
        ctx.strokeRect(-w / 2 + 8, -h / 2 + 8, w - 16, h - 16);
        var word = b[0], cut = Math.ceil(word.length / 2);
        var left = word.slice(0, cut), right = word.slice(cut);
        var size = Math.min(fitSize(ctx, left, 'bold #px ' + HEAVY, 70, (w - gap) / 2 - 30, 0.04),
                            fitSize(ctx, right, 'bold #px ' + HEAVY, 70, (w - gap) / 2 - 30, 0.04));
        ctx.font = 'bold ' + size + 'px ' + HEAVY;
        ctx.textBaseline = 'middle';
        ctx.fillStyle = '#141414';
        ctx.textAlign = 'right'; ctx.fillText(left, -gap / 2, 4);
        ctx.textAlign = 'left'; ctx.fillText(right, gap / 2, 4);
        ctx.textAlign = 'left';
        ctx.restore();
      });
      ctx.fillStyle = '#c8a040';
      ctx.beginPath(); ctx.arc(0, 0, 18, 0, TAU); ctx.fill();
      ctx.restore();
    }
  });

  // --------------------------------------------------- Sidewinder Dunes
  /* Noon on the dune sea.  A sidewinder loops across the sand in front of
     us, the twenty-mule team crawls along a far crest, the wind gets up and
     the crests start to smoke, the brown wall of a haboob climbs the
     horizon -- a drift pours over the rails, and the cart comes bursting
     through it in a spray of sand.  The name is blown clear of the sand. */
  Intro.register('rr_sidewinder', {
    name: 'Sidewinder Dunes',
    tagline: 'The wind buries the line. Dig your cart out -- faster than they dig theirs.',
    accent: '#ffb84a',
    cues: [[0.2, 'rr_wind', 0.4], [1.0, 'rr_wind', 0.8], [1.5, 'rr_whistle', 0.5], [1.9, 'rr_crunch', 0.8],
           [2.0, 'rr_chug', 0.7], [2.5, 'rr_wind', 0.5]],
    shakes: [[1.95, 5, 0.35]],
    tagY: 430, tagAt: 3.0,
    setup: function (r) {
      var d = { far: [], mid: [], near: [], grains: [], streams: [], spray: [] };
      var x = -80;
      while (x < VW + 100) { var w = between(r, 260, 420); d.far.push({ x: x, w: w, h: between(r, 40, 90) }); x += w * 0.75; }
      x = -120;
      while (x < VW + 100) { w = between(r, 320, 520); d.mid.push({ x: x, w: w, h: between(r, 70, 140) }); x += w * 0.8; }
      for (var i = 0; i < 90; i++) d.grains.push({ x: r() * VW, y: between(r, 660, 860), s: between(r, 0.6, 1.4) });
      for (i = 0; i < 40; i++) d.streams.push({ x: r() * VW, y: between(r, 420, 560), p: r() * 6 });
      for (i = 0; i < 46; i++) d.spray.push({ a: between(r, -2.6, -0.5), v: between(r, 180, 520), s: between(r, 4, 12) });
      return d;
    },
    draw: function (ctx, t, d) {
      var HZ = 470;
      var sky = ctx.createLinearGradient(0, 0, 0, HZ);
      sky.addColorStop(0, '#6a98c8');
      sky.addColorStop(0.7, '#c8d4d8');
      sky.addColorStop(1, '#f2dcb0');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, VW, HZ + 2);
      ctx.fillStyle = '#dcc290';
      ctx.fillRect(0, HZ, VW, VH - HZ);
      additive(ctx, function () { dot(ctx, '#fff6d8', 1260, 150, 260, 0.55); });
      ctx.fillStyle = '#fffbe8';
      ctx.beginPath(); ctx.arc(1260, 150, 44, 0, TAU); ctx.fill();
      // the haboob climbing the horizon on the left
      var hab = seg(t, 0.9, 2.6);
      if (hab > 0) {
        // a billowing wall: rounded heads of dust, tallest to the west
        for (var k = 0; k < 12; k++) {
          var hx = -20 + k * 72, top = (150 + 60 * Math.sin(k * 1.7 + t * 0.8)) * hab * (1 - k / 13);
          ctx.fillStyle = rgba(k % 2 ? '#a8845a' : '#b8946a', 0.8 * hab);
          ctx.beginPath(); ctx.ellipse(hx, HZ - top * 0.45, 70, top * 0.6 + 10, 0, 0, TAU); ctx.fill();
        }
      }
      // far dunes, then the mid ones, slip faces in shadow
      function dunes(list, base, col, shade) {
        list.forEach(function (m) {
          ctx.fillStyle = col;
          ctx.beginPath(); ctx.moveTo(m.x, base);
          ctx.quadraticCurveTo(m.x + m.w * 0.45, base - m.h * 1.3, m.x + m.w * 0.7, base - m.h);
          ctx.lineTo(m.x + m.w, base); ctx.fill();
          ctx.fillStyle = shade;
          ctx.beginPath(); ctx.moveTo(m.x + m.w * 0.7, base - m.h); ctx.lineTo(m.x + m.w, base);
          ctx.lineTo(m.x + m.w * 0.82, base); ctx.fill();
        });
      }
      dunes(d.far, HZ + 6, '#e2c896', '#c8a874');
      // the twenty-mule team crawling along a far crest
      var mx = lerp(1500, 1180, t / 3.6);
      ctx.fillStyle = '#5a4a3a';
      for (var mu = 0; mu < 10; mu++) {
        ctx.fillRect(mx + mu * 13, HZ - 48, 9, 5);
        ctx.fillRect(mx + mu * 13 + 1, HZ - 44, 2, 4); ctx.fillRect(mx + mu * 13 + 6, HZ - 44, 2, 4);
      }
      ctx.fillStyle = '#e8dcc0'; ctx.fillRect(mx + 134, HZ - 58, 30, 14); ctx.fillRect(mx + 168, HZ - 58, 30, 14);
      dunes(d.mid, HZ + 120, '#e8cc94', '#c89c62');
      // sand smoking off the crests once the wind gets up
      var wind = seg(t, 0.9, 1.6);
      d.streams.forEach(function (st) {
        if (wind <= 0) return;
        var u = ((t * 0.9 + st.p) % 1);
        ctx.fillStyle = rgba('#f2e2b8', 0.5 * wind * (1 - u));
        ctx.beginPath(); ctx.ellipse(st.x + u * 160, st.y - u * 20, 30 + u * 60, 6 + u * 6, -0.1, 0, TAU); ctx.fill();
      });
      // the foreground sand and the line across it
      ctx.fillStyle = '#ecd2a0';
      ctx.fillRect(0, HZ + 110, VW, VH - HZ - 110);
      var TY = 700;
      ctx.fillStyle = '#a89070';
      ctx.fillRect(0, TY - 6, VW, 18);
      ctx.fillStyle = '#8a8680';
      ctx.fillRect(0, TY - 8, VW, 4); ctx.fillRect(0, TY + 8, VW, 4);
      d.grains.forEach(function (g) {
        ctx.fillStyle = 'rgba(160,120,70,0.35)';
        ctx.fillRect((g.x + t * 60 * g.s) % VW, g.y, 3, 2);
      });
      // the drift pouring over the rails
      var drift = seg(t, 1.2, 1.85), burst = seg(t, 1.9, 2.3);
      var dx0 = 760;
      if (drift > 0 && burst < 1) {
        ctx.fillStyle = '#f0d8a4';
        ctx.beginPath(); ctx.moveTo(dx0 - 220 * drift, TY + 20);
        ctx.quadraticCurveTo(dx0, TY - 110 * drift * (1 - burst), dx0 + 240 * drift, TY + 20); ctx.fill();
      }
      // the cart, bursting through it
      var cx = lerp(VW + 200, 300, outCubic(seg(t, 1.75, 2.9)));
      if (t > 1.75) {
        Art.loco(ctx, cx, TY + 8, 1.0, '#7a2e22', t * 4, '#fff2c0');
        if (burst > 0 && burst < 1) {
          d.spray.forEach(function (sp, i) {
            var age = burst * 0.9;
            var px = dx0 + Math.cos(sp.a) * sp.v * age, py = TY - 30 + Math.sin(sp.a) * sp.v * age + 300 * age * age;
            ctx.fillStyle = rgba(i % 2 ? '#f2dcac' : '#d8b880', 1 - burst);
            ctx.beginPath(); ctx.arc(px, py, sp.s * (1 + burst), 0, TAU); ctx.fill();
          });
        }
      }
      // the sidewinder looping across the near sand, its tracks behind it
      var sx = lerp(-160, VW + 80, t / 3.6);
      for (var tr = 0; tr < 14; tr++) {
        var tx = sx - 60 - tr * 46;
        if (tx < -60) break;
        ctx.strokeStyle = 'rgba(150,110,60,0.45)'; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.moveTo(tx, 820); ctx.quadraticCurveTo(tx + 18, 790, tx + 6, 770); ctx.stroke();
      }
      ctx.strokeStyle = '#8a6a44'; ctx.lineWidth = 11; ctx.lineCap = 'round';
      ctx.beginPath();
      for (var s2 = 0; s2 <= 16; s2++) {
        var u2 = s2 / 16;
        var px2 = sx + Math.sin(u2 * 6 + t * 9) * 14 - u2 * 30, py2 = 770 + u2 * 52;
        if (s2 === 0) ctx.moveTo(px2, py2); else ctx.lineTo(px2, py2);
      }
      ctx.stroke(); ctx.lineCap = 'butt';
      ctx.fillStyle = '#6a4e30';
      ctx.beginPath(); ctx.ellipse(sx + Math.sin(t * 9) * 14 + 4, 766, 12, 8, 0.4, 0, TAU); ctx.fill();
      // heat over everything
      ctx.fillStyle = rgba('#fff4d8', 0.08 + 0.04 * Math.sin(t * 7));
      ctx.fillRect(0, HZ - 40, VW, 160);
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Sidewinder Dunes').toUpperCase();
      var k = seg(t, 1.85, 2.45);
      if (k <= 0) return;
      ctx.save();
      // the letters raised in the sand, the wind sweeping the sand off
      // them right to left
      var size = fitSize(ctx, name, 'bold #px ' + HEAVY, 128, 1260, 0.04);
      ctx.font = 'bold ' + size + 'px ' + HEAVY;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      var w = ctx.measureText(name).width;
      ctx.beginPath(); ctx.rect(800 + w / 2 - (w + 80) * k, 120, (w + 80) * k + 40, 240); ctx.clip();
      ctx.fillStyle = 'rgba(90,60,30,0.55)';
      ctx.fillText(name, 808, 236);
      ctx.fillStyle = '#f2dcac';
      ctx.fillText(name, 800, 228);
      ctx.strokeStyle = '#c8a06a'; ctx.lineWidth = 3;
      ctx.strokeText(name, 800, 228);
      ctx.restore();
      // the sand still streaming off the edge of the sweep
      if (k < 1) {
        var ex = 800 + w / 2 - (w + 80) * k;
        for (var i = 0; i < 18; i++) {
          ctx.fillStyle = rgba('#f2dcac', 0.7 * (1 - k));
          ctx.fillRect(ex - (i * 37 % 90), 150 + (i * 53 % 160), 6, 4);
        }
      }
    }
  });

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
