/* Rail Rivals -- the Game View half of the payload race
   (app/game/worlds/rail_rivals.py).

   Draws what the race adds to the area: both companies' ore carts on their
   tracks (each a little steam dinky with an ore bucket, its push ring, its
   brakes and its smoke), the brake levers' handles, a sack over every coal
   heap, the depots down each line, the sack on a carrier's back, and each
   line's twist -- the junction signal, the snowdrifts, the lift bridges'
   warning lamps, the firedamp clouds and their blasts.  The objective panel
   shows both carts' progress with their depots; the prompt and the hold bar
   say what E does where you stand.

   Four arrival scenes, one per railroad, are registered at the bottom. */
(function (global) {
  'use strict';
  // the arrival scenes and sounds stand on their own (the world page's
  // previews load this file without the game around it)
  var Arena = global.Arena || { register: function () {} };

  var TEAM = { red: '#c4281c', blue: '#2f6aa8' };
  var TEAM_LIGHT = { red: '#ff8a7a', blue: '#8ac4ff' };
  var GOLD = '#e8b23a';
  var PUSH_R = 10, LEVER_R = 4.6, COAL_R = 6, STOKE_R = 9, DRIFT_R = 7, WINCH_R = 5;

  function rgb(hex) {
    var n = parseInt(String(hex).slice(1), 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
  }
  function esc(text) {
    return String(text == null ? '' : text).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function fmt(s) { s = Math.max(0, Math.round(s || 0)); return Math.floor(s / 60) + ':' + ('0' + s % 60).slice(-2); }

  // ----------------------------------------------------------- a track
  function Lane(points) {
    this.pts = (points || []).map(function (p) { return [p[0], p[2]]; });
    this.cum = [0];
    for (var i = 0; i < this.pts.length - 1; i++) {
      this.cum.push(this.cum[i] + Math.hypot(this.pts[i + 1][0] - this.pts[i][0],
                                             this.pts[i + 1][1] - this.pts[i][1]));
    }
    this.length = this.cum[this.cum.length - 1] || 1;
  }
  Lane.prototype.at = function (d) {
    d = Math.max(0, Math.min(this.length, d));
    var lo = 0, hi = this.cum.length - 1;
    while (hi - lo > 1) {
      var mid = (lo + hi) >> 1;
      if (this.cum[mid] <= d) lo = mid; else hi = mid;
    }
    var a = this.pts[lo], b = this.pts[hi] || a;
    var seg = this.cum[hi] - this.cum[lo];
    var f = seg > 0 ? (d - this.cum[lo]) / seg : 0;
    return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, Math.atan2(b[0] - a[0], b[1] - a[1])];
  };
  Lane.prototype.project = function (x, z) {
    var best = 0, off = 1e9;
    for (var i = 0; i < this.pts.length - 1; i++) {
      var a = this.pts[i], b = this.pts[i + 1];
      var dx = b[0] - a[0], dz = b[1] - a[1], len2 = dx * dx + dz * dz;
      var f = len2 > 0 ? Math.max(0, Math.min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / len2)) : 0;
      var o = Math.hypot(a[0] + dx * f - x, a[1] + dz * f - z);
      if (o < off) { off = o; best = this.cum[i] + f * Math.sqrt(len2); }
    }
    return best;
  };

  /* Put a part given in the cart's own frame (+Z down the track) into the
     world, turned by ``yaw``, through the renderer's raw path. */
  function local(renderer, kind, base, yaw, lp, size, colour, o) {
    o = o || {};
    var c = Math.cos(yaw), s = Math.sin(yaw);
    var r = o.r || [0, 0, 0];
    renderer.pushRaw(kind, base[0] + lp[0] * c + lp[2] * s, base[1] + lp[1],
                     base[2] - lp[0] * s + lp[2] * c, r[0], r[1] + yaw, r[2],
                     size[0], size[1], size[2], typeof colour === 'string' ? rgb(colour) : colour,
                     o.a === undefined ? 1 : o.a, o.st || 0, o.m || 0, o.e || 0, null);
  }

  // ============================================================ plugin
  Arena.register('rail_rivals', function (arena) {
    var client = arena.client;
    var lanes = {}, levers = {}, heaps = [], depots = { a: [], b: [] }, finishes = {};
    var laneOf = { red: 'a', blue: 'b' };
    var carts = {}, shown = {}, coal = {}, twist = { kind: '' };
    var signal = null, cross = {}, bridgeSpans = {}, winches = {};
    var gasWarn = null, blasts = [], smoke = [], dust = [];
    var names = {}, accent = '#ffd27a';
    var lastSaid = {}, myLane = 'a';

    function loadMap(map) {
      var mk = (map && map.markers) || {};
      var extra = mk.extra || {};
      var pts = mk.points || {};
      lanes = {};
      Object.keys(extra.lanes || {}).forEach(function (k) { lanes[k] = new Lane(extra.lanes[k]); });
      names = extra.names || {};
      accent = extra.accent || accent;
      levers = { a: [], b: [] };
      (pts.lever || []).forEach(function (m) {
        if (!levers[m.lane]) levers[m.lane] = [];
        levers[m.lane].push({ i: m.index, p: m.p, yaw: m.yaw || 0, pulled: '', cool: 0, swing: 0 });
      });
      heaps = (pts.coal || []).map(function (m) { return m.p; });
      depots = { a: [], b: [] };
      (pts.depot || []).forEach(function (m) {
        if (!lanes[m.lane]) return;
        depots[m.lane].push({ d: lanes[m.lane].project(m.p[0], m.p[2]), p: m.p, name: m.name });
      });
      Object.keys(depots).forEach(function (k) { depots[k].sort(function (x, y) { return x.d - y.d; }); });
      finishes = {};
      (pts.finish || []).forEach(function (m) { finishes[m.lane] = m.p; });
      signal = (pts.signal || [])[0] || null;
      winches = {};
      (pts.winch || []).forEach(function (m) { winches[m.lane] = m.p; });
      bridgeSpans = extra.bridges || {};
      cross = {};
      if (lanes.a && lanes.b) {
        var best = 1e9;
        for (var i = 0; i < lanes.a.pts.length; i += 1) {
          var p = lanes.a.pts[i];
          var d = lanes.b.project(p[0], p[1]);
          var q = lanes.b.at(d);
          var gap = Math.hypot(q[0] - p[0], q[1] - p[1]);
          if (gap < best) { best = gap; cross = { x: q[0], z: q[1] }; }
        }
      }
      carts = {}; shown = {}; coal = {}; drifts = {}; gasWarn = null; blasts = []; smoke = [];
    }

    var drifts = {};

    function applyState(rr) {
      if (!rr) return;
      if (rr.lanes) laneOf = rr.lanes;
      Object.keys(rr.carts || {}).forEach(function (team) {
        var c = rr.carts[team];
        var cart = carts[team] || (carts[team] = { d: c.d, team: team });
        cart.lane = c.lane; cart.len = c.len; cart.f = c.f; cart.push = c.push;
        cart.contest = c.contest; cart.brake = c.brake; cart.stoke = c.stoke;
        cart.held = c.held; cart.passed = c.passed; cart.depots = c.depots;
        cart.target = c.d;
        if (shown[team] === undefined || Math.abs(shown[team] - c.d) > 25) shown[team] = c.d;
      });
      Object.keys(rr.levers || {}).forEach(function (lane) {
        (rr.levers[lane] || []).forEach(function (s) {
          var lv = findLever(lane, s.i);
          if (lv) { lv.pulled = s.pulled; lv.cool = s.cool; }
        });
      });
      twist = rr.twist || twist;
      if (twist.kind === 'drifts') {
        var next = {};
        Object.keys(twist.drifts || {}).forEach(function (lane) {
          next[lane] = { d: twist.drifts[lane].d, left: twist.drifts[lane].left };
        });
        drifts = next;
      }
      if (twist.kind === 'firedamp') {
        gasWarn = twist.gas && twist.gas.p ? { p: twist.gas.p, left: twist.gas.left,
                                                at: performance.now() / 1000 } : null;
      }
      var mine = laneOf[client.myTeam];
      if (mine) myLane = mine;
    }

    function findLever(lane, i) {
      var list = levers[lane] || [];
      for (var k = 0; k < list.length; k++) if (list[k].i === i) return list[k];
      return null;
    }

    function teamOfLane(lane) {
      return laneOf.red === lane ? 'red' : 'blue';
    }

    function rival(team) { return team === 'red' ? 'blue' : 'red'; }

    function cartPos(team) {
      var cart = carts[team];
      if (!cart || !lanes[cart.lane]) return null;
      return lanes[cart.lane].at(shown[team] === undefined ? cart.d : shown[team]);
    }

    function say(key, title, sub, kind, sound) {
      var now = performance.now();
      if (lastSaid[key] && now - lastSaid[key] < 1500) return;
      lastSaid[key] = now;
      arena.banner(title, sub || '', kind || '', 2600);
      if (sound) client.audio.play(sound, { volume: 0.6 });
    }

    // --------------------------------------------------- messages
    var messages = {
      rrs: function (msg) { applyState(msg.s); },
      rrx: function (msg) {
        var me = client.myTeam;
        var k = msg.k;
        if (k === 'coal') {
          client.audio.play('rr_coal', { volume: 0.6 });
        } else if (k === 'stoke') {
          var mineS = msg.team === me;
          if (mineS) say('stoke', 'STOKED!', esc(msg.by) + ' shovelled coal in &bull; full steam', 'go', 'rr_whistle');
          var pos = cartPos(msg.team);
          if (pos) puff(pos, 8);
        } else if (k === 'brake') {
          var lv = findLever(msg.lane, msg.i);
          if (lv) { lv.pulled = msg.on ? (msg.team === 'red' ? 'blue' : 'red') : ''; }
          var mineB = msg.team === me;
          if (msg.on) {
            client.audio.play('rr_brake', { volume: mineB ? 0.8 : 0.5 });
            if (mineB) say('brake', 'BRAKES ON!', esc(msg.by) + ' pulled a lever on your cart &bull; go release it', 'bad');
            else say('brake', 'BRAKES PULLED', esc(msg.by) + ' locked their cart', 'go');
          } else if (msg.by) {
            client.audio.play('rr_release', { volume: 0.5 });
            if (mineB) say('brake', 'BRAKES OFF', esc(msg.by) + ' freed your cart', 'go');
          }
        } else if (k === 'depot') {
          var mineD = msg.team === me;
          say('depot' + msg.team, mineD ? 'DEPOT!' : 'THEY PASSED A DEPOT',
              esc(msg.name) + (mineD ? ' &bull; you respawn here now' : ''), mineD ? 'go' : 'bad',
              'rr_bell');
        } else if (k === 'signal') {
          if (msg.team) {
            var ours = msg.team === me;
            say('signal', ours ? 'SIGNAL IS OURS' : 'SIGNAL AGAINST YOU',
                ours ? 'Their cart is held at the diamond' : 'Your cart stops at the diamond &bull; take the cabin back',
                ours ? 'go' : 'bad', 'rr_signal');
          }
        } else if (k === 'drift') {
          if (msg.d >= 0) {
            drifts[msg.lane] = { d: msg.d, left: 1 };
            if (msg.lane === laneOf[me]) say('drift', 'SNOWDRIFT AHEAD', 'Hold E by it to dig your cart through', 'bad', 'rr_wind');
          } else {
            delete drifts[msg.lane];
            if (msg.lane === laneOf[me]) say('drift', 'DUG OUT!', esc(msg.by || '') + ' cleared the drift', 'go');
            var lane = lanes[msg.lane];
            if (lane) dustAt(lane, msg.lane);
          }
        } else if (k === 'bridge') {
          var mineBr = msg.lane === laneOf[me];
          if (msg.state === 'warn') {
            client.audio.play('rr_bell', { volume: 0.7 });
            client.audio.later(500, function () { this.play('rr_bell', { volume: 0.7 }); });
            say('bridge', mineBr ? 'YOUR BRIDGE IS LIFTING' : 'BRIDGE LIFTING', 'Get off the deck!', 'bad');
          } else if (msg.state === 'up') {
            client.audio.play('rr_lift', { volume: 0.7 });
            if (mineBr) say('bridge2', 'BRIDGE UP', 'Your cart waits at the bank until it comes down', 'bad');
          } else if (msg.state === 'down') {
            client.audio.play('rr_lift', { volume: 0.4 });
          }
        } else if (k === 'gas') {
          if (msg.state === 'warn') {
            gasWarn = { p: msg.p, left: msg.in, at: performance.now() / 1000 };
            var mp = client.local.pos;
            var near = Math.hypot(mp[0] - msg.p[0], mp[2] - msg.p[2]) < 40;
            client.audio.play('rr_hiss', { volume: near ? 0.8 : 0.25 });
            if (near) say('gas', 'FIREDAMP!', 'Get clear before it goes up', 'bad');
          } else {
            gasWarn = null;
            blasts.push({ p: msg.p, t: 0 });
            var q = client.local.pos;
            var dist = Math.hypot(q[0] - msg.p[0], q[2] - msg.p[2]);
            client.audio.play('explode', { volume: Math.max(0.15, 1 - dist / 160) });
            if (dist < 40) arena.flashScreen('rgba(255,170,60,0.55)', 420);
          }
        } else if (k === 'nope') {
          arena.banner(esc(msg.m || ''), '', 'bad', 1600);
        }
      }
    };

    // ------------------------------------------------------- effects
    function puff(pos, n) {
      for (var i = 0; i < n; i++) {
        smoke.push({ x: pos[0] + (Math.random() - 0.5) * 2, y: 7 + Math.random(), z: pos[1] +
                     (Math.random() - 0.5) * 2, t: 0, life: 1.6 + Math.random(), s: 1 + Math.random() });
      }
    }
    function dustAt(lane, key) {
      var drift = drifts[key];
      if (!drift) return;
      var p = lane.at(drift.d);
      for (var i = 0; i < 10; i++) {
        dust.push({ x: p[0] + (Math.random() - 0.5) * 5, y: 1 + Math.random() * 2,
                    z: p[1] + (Math.random() - 0.5) * 5, t: 0, life: 1 + Math.random() });
      }
    }

    // ---------------------------------------------------- drawing
    function drawCart(renderer, team, time) {
      var cart = carts[team];
      var lane = cart && lanes[cart.lane];
      if (!lane) return;
      var at = lane.at(shown[team]);
      var base = [at[0], 0.44, at[1]], yaw = at[2];
      var colour = TEAM[team];
      var moving = cart.speed > 0.05;
      var stoked = cart.stoke > 0;
      var braked = cart.brake > 0;
      // wheels, turning with the distance rolled
      var spin = (shown[team] || 0) / 0.9;
      for (var sx = -1; sx <= 1; sx += 2) {
        for (var sz = -1; sz <= 1; sz += 2) {
          local(renderer, 'cyl', base, yaw, [sx * 2.0, 0.85, sz * 2.4], [1.7, 0.5, 1.7], '#2a2826',
                { r: [spin, 0, Math.PI / 2], m: 1 });
          if (braked) {
            local(renderer, 'box', base, yaw, [sx * 2.0, 0.85, sz * 2.4 - 1.0], [0.6, 0.6, 0.3],
                  '#ff3a2a', { m: 2, e: 0.8 });
          }
        }
      }
      // frame, bucket and ore
      local(renderer, 'box', base, yaw, [0, 1.5, 0], [4.2, 0.6, 7.8], '#3a3632', { m: 1 });
      local(renderer, 'box', base, yaw, [0, 3.2, 1.7], [4.6, 2.8, 4.0], colour, { st: 1 });
      local(renderer, 'box', base, yaw, [0, 4.7, 1.7], [4.9, 0.3, 4.3], '#2a2826', { m: 1 });
      local(renderer, 'box', base, yaw, [0, 4.75, 1.7], [4.0, 0.5, 3.4], GOLD, { m: 1 });
      local(renderer, 'sph', base, yaw, [-0.8, 5.1, 1.2], [1.4, 1.0, 1.3], '#ffd24a', { m: 1 });
      local(renderer, 'sph', base, yaw, [0.9, 5.2, 2.2], [1.2, 1.1, 1.2], '#f2c03a', { m: 1 });
      local(renderer, 'box', base, yaw, [0, 3.2, 3.72], [3.0, 1.2, 0.06], '#fff4d6');
      // the little boiler at the back, its stack and its firebox
      local(renderer, 'cyl', base, yaw, [0, 3.0, -2.0], [2.6, 3.4, 2.6], '#2e2c2a', { r: [Math.PI / 2, 0, 0], m: 1 });
      local(renderer, 'cyl', base, yaw, [0, 5.3, -2.6], [0.9, 2.2, 0.9], '#1e1c1a', { m: 1 });
      local(renderer, 'cyl', base, yaw, [0, 6.5, -2.6], [1.4, 0.4, 1.4], GOLD, { m: 1 });
      var fire = stoked ? 0.9 : 0.35 + 0.15 * Math.sin(time * 6);
      local(renderer, 'box', base, yaw, [0, 2.2, -3.75], [1.6, 0.8, 0.08], [1, 0.45 + fire * 0.3, 0.1],
            { m: 2, e: fire });
      // the lamp, the pennant
      local(renderer, 'box', base, yaw, [0, 2.4, 3.95], [0.9, 0.9, 0.2], '#fff3c4', { m: 2, e: 0.8 });
      local(renderer, 'box', base, yaw, [2.0, 5.4, -0.6], [0.14, 3.2, 0.14], '#5a3a22');
      var flap = Math.sin(time * 5 + (team === 'red' ? 0 : 2)) * 0.25;
      local(renderer, 'box', base, yaw, [2.0, 6.5, -1.4], [0.06, 1.0, 1.6], colour, { r: [0, flap, 0] });
      // the push ring: grey idle, team colour pushing, red contested
      var ring = cart.contest ? [1, 0.3, 0.25] : (cart.push > 0 ? rgb(TEAM_LIGHT[team]) : [0.75, 0.75, 0.78]);
      var pulse = 1 + 0.03 * Math.sin(time * (cart.push ? 6 : 2));
      renderer.pushRaw('cyl', at[0], 0.32, at[1], 0, 0, 0, PUSH_R * 2 * pulse, 0.1, PUSH_R * 2 * pulse,
                       ring, cart.contest ? 0.32 : 0.2, 0, 2, 0.6, null);
      // smoke from the stack, thicker when stoked
      if (Math.random() < (stoked ? 0.5 : (moving ? 0.12 : 0.03))) {
        var c = Math.cos(yaw), s = Math.sin(yaw);
        smoke.push({ x: at[0] + (-2.6) * s, y: base[1] + 7.0, z: at[1] + (-2.6) * c, t: 0,
                     life: 1.4 + Math.random(), s: stoked ? 1.4 : 0.9, dark: stoked });
      }
      if (client.settings.showNames) {
        var status = cart.contest ? 'CONTESTED' : braked ? 'BRAKES ON ' + Math.ceil(cart.brake) + 's'
          : cart.held === 'signal' ? 'HELD AT THE SIGNAL' : cart.held === 'drift' ? 'SNOWED IN'
          : cart.held === 'bridge' ? 'BRIDGE UP' : stoked ? 'FULL STEAM' :
          (cart.push ? cart.push + ' pushing' : 'idle');
        renderer.queueTag('rrcart' + team, arena.teamName(team) + '  ' + Math.round((cart.f || 0) * 100) + '%',
                          TEAM_LIGHT[team], status, [at[0], 10.4, at[1]], 1.7);
      }
    }

    function drawLevers(renderer, time) {
      var me = client.myTeam, p = client.local.pos;
      Object.keys(levers).forEach(function (lane) {
        var owner = teamOfLane(lane);
        (levers[lane] || []).forEach(function (lv) {
          var target = lv.pulled ? -0.75 : 0.55;
          lv.swing += (target - lv.swing) * 0.2;
          var yaw = lv.yaw;
          var off = [Math.sin(lv.swing) * Math.sin(yaw), Math.cos(lv.swing), Math.sin(lv.swing) * Math.cos(yaw)];
          var pivot = [lv.p[0], 2.1, lv.p[2]];
          renderer.pushRaw('box', pivot[0] + off[0] * 1.5, pivot[1] + off[1] * 1.5, pivot[2] + off[2] * 1.5,
                           lv.swing, yaw, 0, 0.32, 3.0, 0.32, rgb('#c8ccd2'), 1, 0, 1, 0, null);
          renderer.pushRaw('sph', pivot[0] + off[0] * 3.1, pivot[1] + off[1] * 3.1, pivot[2] + off[2] * 3.1,
                           0, 0, 0, 0.8, 0.8, 0.8, lv.pulled ? [1, 0.25, 0.2] : rgb('#fff4d6'), 1, 0, 0,
                           lv.pulled ? 0.6 : 0, null);
          // the lamp on the stand: whose track it is
          renderer.pushRaw('box', lv.p[0], 2.1, lv.p[2], 0, yaw, 0, 0.5, 0.5, 1.26,
                           rgb(TEAM[owner]), 1, 0, 2, 0.5, null);
          var can = me && ((owner !== me && !lv.pulled && lv.cool <= 0) || (owner === me && lv.pulled));
          if (can && Math.hypot(p[0] - lv.p[0], p[2] - lv.p[2]) < 60) {
            var k = 0.5 + 0.5 * Math.sin(time * 4);
            renderer.pushRaw('cyl', lv.p[0], 0.08, lv.p[2], 0, 0, 0, LEVER_R * 2, 0.06, LEVER_R * 2,
                             owner === me ? [0.4, 1, 0.5] : [1, 0.75, 0.25], 0.18 + 0.12 * k, 0, 2, 0.5, null);
          }
        });
      });
    }

    function drawCoal(renderer, time) {
      var carrying = arena.me && arena.me.coal;
      if (carrying) return;
      heaps.forEach(function (h, i) {
        var bob = Math.sin(time * 2 + i) * 0.4;
        renderer.pushRaw('box', h[0], h[1] + 4.2 + bob, h[2], 0, time * 0.8 + i, 0, 1.6, 1.9, 1.2,
                         rgb('#6a5a48'), 1, 0, 0, 0, null);
        renderer.pushRaw('box', h[0], h[1] + 5.3 + bob, h[2], 0, time * 0.8 + i, 0, 1.0, 0.3, 0.8,
                         rgb('#3a3028'), 1, 0, 0, 0, null);
        renderer.pushRaw('sph', h[0], h[1] + 4.6 + bob, h[2], 0, 0, 0, 2.6, 2.6, 2.6,
                         [1, 0.7, 0.3], 0.14, 0, 2, 0.4, null);
      });
    }

    function drawDepots(renderer, time) {
      ['a', 'b'].forEach(function (lane) {
        var owner = teamOfLane(lane);
        var cart = carts[owner];
        var passed = cart ? cart.passed || 0 : 0;
        (depots[lane] || []).forEach(function (dp, i) {
          var done = i < passed;
          var col = done ? [0.4, 0.95, 0.5] : rgb(TEAM_LIGHT[owner]);
          renderer.pushRaw('box', dp.p[0], dp.p[1] + 17, dp.p[2], 0, time * 0.6, 0, 1.4, 1.4, 1.4,
                           col, 1, 0, 2, 0.6, null);
          renderer.pushRaw('cyl', dp.p[0], dp.p[1] + 26, dp.p[2], 0, 0, 0, 0.8, 16, 0.8,
                           col, 0.22, 0, 2, 0.5, null);
        });
        var fin = finishes[lane];
        if (fin) {
          renderer.pushRaw('cyl', fin[0], 20, fin[2], 0, 0, 0, 1.6, 40, 1.6, rgb(GOLD), 0.3, 0, 2, 0.7, null);
        }
      });
    }

    function drawTwist(renderer, time, dt) {
      if (twist.kind === 'signal' && signal) {
        var held = twist.team;
        var col = held ? rgb(TEAM_LIGHT[held]) : [1, 1, 0.85];
        var blink = held ? 0.6 + 0.4 * Math.sin(time * 5) : 0.5;
        renderer.pushRaw('sph', signal.p[0], 25.5, signal.p[2], 0, 0, 0, 2.2, 2.2, 2.2, col, 1, 0, 2, blink, null);
        if (cross.x !== undefined) {
          renderer.pushRaw('cyl', cross.x, 0.2, cross.z, 0, 0, 0, 36, 0.08, 36,
                           held ? rgb(TEAM[held]) : [1, 0.85, 0.4], held ? 0.22 : 0.08, 0, 2, 0.4, null);
          renderer.pushRaw('box', cross.x, 13, cross.z, 0, time, 0, 1.2, 1.2, 1.2, col, 1, 0, 2, blink, null);
        }
        if (twist.taking) {
          renderer.pushRaw('cyl', signal.p[0], signal.p[1] + 0.2, signal.p[2], 0, 0, 0, 11, 0.1, 11,
                           rgb(TEAM_LIGHT[twist.taking]), 0.25 + 0.2 * (twist.progress || 0), 0, 2, 0.6, null);
        }
      } else if (twist.kind === 'drifts') {
        Object.keys(drifts).forEach(function (lane) {
          var drift = drifts[lane];
          var path = lanes[lane];
          if (!path) return;
          var at = path.at(drift.d), k = Math.max(0.25, drift.left === undefined ? 1 : drift.left);
          for (var i = 0; i < 5; i++) {
            var a = i * 1.26;
            renderer.pushRaw('sph', at[0] + Math.cos(a) * 2.2 * k, 0.6 + (i % 2) * 0.7 * k,
                             at[1] + Math.sin(a) * 2.2 * k, 0, 0, 0, 4.5 * k, 2.8 * k, 4.2 * k,
                             rgb('#f4f8fc'), 1, 0, 0, 0, null);
          }
          renderer.pushRaw('sph', at[0], 1.6 * k, at[1], 0, 0, 0, 7 * k, 3.6 * k, 6 * k,
                           rgb('#ffffff'), 1, 0, 0, 0, null);
          if (lane === myLane) {
            renderer.pushRaw('cyl', at[0], 0.12, at[1], 0, 0, 0, DRIFT_R * 2, 0.06, DRIFT_R * 2,
                             [0.6, 0.85, 1], 0.2 + 0.1 * Math.sin(time * 4), 0, 2, 0.5, null);
          }
        });
        // snow on the wind, round the player
        var me = client.local.pos;
        for (var f = 0; f < 18; f++) {
          var fx = me[0] + ((f * 37.3 + time * 6) % 60) - 30, fz = me[2] + ((f * 53.1 + time * 2) % 60) - 30;
          var fy = me[1] + 22 - ((time * 4 + f * 3.1) % 24);
          renderer.pushRaw('box', fx, fy, fz, time + f, f, 0, 0.18, 0.18, 0.18, [1, 1, 1], 0.85, 0, 2, 0.3, null);
        }
      } else if (twist.kind === 'bridges') {
        Object.keys(bridgeSpans).forEach(function (lane) {
          var span = bridgeSpans[lane], path = lanes[lane];
          if (!path || !span) return;
          var b = (twist.bridges || {})[lane] || {};
          if (!b.warn && !b.up) return;
          var on = Math.sin(time * 10) > 0;
          [span[0] - 3, span[1] + 3].forEach(function (d) {
            var at = path.at(d);
            renderer.pushRaw('sph', at[0], 39.4, at[1], 0, 0, 0, 1.6, 1.6, 1.6,
                             on ? [1, 0.2, 0.1] : [0.3, 0.05, 0.05], 1, 0, 2, on ? 1 : 0, null);
          });
        });
      } else if (twist.kind === 'firedamp' && gasWarn) {
        var since = performance.now() / 1000 - gasWarn.at;
        var grow = Math.min(1, since / Math.max(0.5, gasWarn.left || 6));
        for (var g = 0; g < 7; g++) {
          var ang = g * 0.9 + time * 0.6;
          renderer.pushRaw('sph', gasWarn.p[0] + Math.cos(ang) * 6 * grow, 1.5 + (g % 3) * 1.4,
                           gasWarn.p[2] + Math.sin(ang) * 6 * grow, 0, 0, 0,
                           9 * grow + 2, 4 * grow + 1, 9 * grow + 2, [0.55, 0.85, 0.35], 0.22, 0, 2, 0.3, null);
        }
        renderer.pushRaw('cyl', gasWarn.p[0], 0.1, gasWarn.p[2], 0, 0, 0, 24, 0.06, 24,
                         [1, 0.9, 0.2], 0.18 + 0.15 * Math.sin(time * 9), 0, 2, 0.6, null);
      }
      blasts = blasts.filter(function (b) {
        b.t += dt;
        var k = b.t / 0.8;
        if (k >= 1) return false;
        renderer.pushRaw('sph', b.p[0], 4, b.p[2], 0, 0, 0, 10 + k * 34, 6 + k * 18, 10 + k * 34,
                         [1, 0.65 - k * 0.4, 0.2], 0.6 * (1 - k), 0, 2, 1, null);
        return true;
      });
    }

    function drawSmoke(renderer, dt) {
      smoke = smoke.filter(function (s) {
        s.t += dt;
        if (s.t > s.life) return false;
        var k = s.t / s.life;
        s.y += dt * 3.2;
        s.x += dt * 0.8;
        var size = s.s * (1 + k * 2.2);
        var shade = s.dark ? 0.25 + k * 0.4 : 0.6 + k * 0.3;
        renderer.pushRaw('sph', s.x, s.y, s.z, 0, 0, 0, size, size, size, [shade, shade, shade],
                         0.5 * (1 - k), 0, 0, 0, null);
        return true;
      });
      if (smoke.length > 160) smoke.splice(0, smoke.length - 160);
      dust = dust.filter(function (s) {
        s.t += dt;
        if (s.t > s.life) return false;
        var k = s.t / s.life;
        s.y += dt * 2;
        renderer.pushRaw('sph', s.x, s.y, s.z, 0, 0, 0, 1.5 + k * 2, 1.5 + k * 2, 1.5 + k * 2,
                         [1, 1, 1], 0.7 * (1 - k), 0, 0, 0, null);
        return true;
      });
    }

    // -------------------------------------------- what E does here
    function here() {
      var me = client.myTeam, p = client.local.pos;
      if (!me || !client.local.alive || arena.phase !== 'active') return null;
      var own = carts[me];
      if (arena.me && arena.me.coal && own) {
        var at = cartPos(me);
        if (at && Math.hypot(at[0] - p[0], at[1] - p[2]) <= STOKE_R) return { k: 'stoke', text: 'Press <b>E</b> to stoke your cart with coal' };
        return { k: 'carry', text: 'Carrying coal &bull; take it to your cart' };
      }
      var lane, i, lv;
      for (lane in levers) {
        for (i = 0; i < levers[lane].length; i++) {
          lv = levers[lane][i];
          if (Math.hypot(lv.p[0] - p[0], lv.p[2] - p[2]) > LEVER_R) continue;
          var owner = teamOfLane(lane);
          if (lv.pulled && owner === me) return { k: 'release', text: 'Hold <b>E</b> to release the brakes' };
          if (!lv.pulled && owner !== me) {
            return lv.cool > 0 ? { k: 'cool', text: 'Lever cooling down (' + Math.ceil(lv.cool) + 's)' }
              : { k: 'brake', text: 'Hold <b>E</b> to pull the brakes on their cart' };
          }
        }
      }
      if (own && drifts[own.lane] && lanes[own.lane]) {
        var d = lanes[own.lane].at(drifts[own.lane].d);
        if (Math.hypot(d[0] - p[0], d[1] - p[2]) <= DRIFT_R) return { k: 'dig', text: 'Hold <b>E</b> to dig the drift' };
      }
      for (lane in winches) {
        var w = winches[lane];
        if (Math.hypot(w[0] - p[0], w[2] - p[2]) > WINCH_R) continue;
        var b = ((twist.bridges || {})[lane]) || {};
        var ownerW = teamOfLane(lane);
        if (b.up && ownerW === me) return { k: 'lower', text: 'Hold <b>E</b> to lower your bridge' };
        if (!b.up && !b.warn && ownerW !== me) return { k: 'raise', text: 'Hold <b>E</b> to winch their bridge up' };
      }
      for (i = 0; i < heaps.length; i++) {
        if (Math.hypot(heaps[i][0] - p[0], heaps[i][2] - p[2]) <= COAL_R) {
          return { k: 'coal', text: 'Hold <b>E</b> to take a sack of coal' };
        }
      }
      if (signal && twist.kind === 'signal' && Math.abs(p[0] - signal.p[0]) <= 5.6 &&
          Math.abs(p[2] - signal.p[2]) <= 5.6 && p[1] > signal.p[1] - 1) {
        if (twist.team === me) return { k: 'sig', text: 'The signal is yours for ' + Math.ceil(twist.left || 0) + 's' };
        if (twist.rest > 0) return { k: 'sig', text: 'The signal resets in ' + Math.ceil(twist.rest) + 's' };
        return { k: 'sig', text: 'Hold the cabin to set the signal against them' };
      }
      return null;
    }

    var ACT_LABEL = { coal: 'Taking coal', brake: 'Pulling the brakes', release: 'Releasing the brakes',
                      stoke: 'Stoking', dig: 'Digging', raise: 'Winching the bridge up',
                      lower: 'Lowering the bridge' };

    // -------------------------------------------------------- hooks
    return {
      init: function () {},
      onMap: loadMap,
      onArea: function () {
        arena.setRole('');
      },
      onState: function (state) { applyState(state.rr); },
      onSnapshot: function (msg) {
        var ax = msg.ax;
        if (!ax) return;
        Object.keys(ax.c || {}).forEach(function (team) {
          var row = ax.c[team];
          var cart = carts[team] || (carts[team] = { team: team, lane: laneOf[team] });
          cart.target = row[0];
          cart.d = row[0];
          cart.speed = row[1];
          cart.contest = !!row[2];
          if (!row[3]) cart.brake = 0; else if (!cart.brake) cart.brake = 9;
          if (!row[4]) cart.stoke = 0; else if (!cart.stoke) cart.stoke = 10;
          cart.push = row[5];
          if (shown[team] === undefined || Math.abs(shown[team] - row[0]) > 25) shown[team] = row[0];
        });
        coal = {};
        (ax.coal || []).forEach(function (id) { coal[id] = true; });
      },
      onMe: function (me) {
        if (me.lane) myLane = me.lane;
        if (me.act) arena.setHold(me.act.p, ACT_LABEL[me.act.k] || '');
        else arena.setHold(null);
        var team = me.team;
        if (team && arena.phase !== 'intermission') {
          arena.setRole('<b style="color:' + TEAM_LIGHT[team] + '">' + esc(arena.teamName(team)) +
                        '</b> &bull; ' + esc(names[me.lane] || 'your line') +
                        (me.coal ? ' &bull; <b>carrying coal</b>' : ''), team);
        }
      },
      goLine: function () {
        var team = client.myTeam;
        return team ? 'Push the ' + arena.teamName(team) + "'s cart down " + (names[laneOf[team]] || 'the line') + '!' : '';
      },
      messages: messages,
      hud: function (state) {
        var me = client.myTeam;
        var bars = [];
        var red = carts.red || {}, blue = carts.blue || {};
        ['red', 'blue'].forEach(function (team) {
          var c = carts[team] || {};
          var status = c.contest ? 'CONTESTED' : c.brake > 0 ? 'BRAKES' : c.held === 'signal' ? 'SIGNAL'
            : c.held === 'drift' ? 'SNOWED IN' : c.held === 'bridge' ? 'BRIDGE UP'
            : c.stoke > 0 ? 'STEAM' : (c.push ? c.push + ' pushing' : 'idle');
          bars.push({ label: arena.teamName(team), value: c.f || 0, marks: c.depots || [],
                      colour: TEAM[team], text: Math.round((c.f || 0) * 100) + '% · ' + status,
                      cls: team === me ? 'mine' : '' });
        });
        var sub = '';
        if (twist.kind === 'signal') {
          sub = twist.team ? 'Junction signal set by <b>' + esc(arena.teamName(twist.team)) + '</b> (' +
            Math.ceil(twist.left || 0) + 's)' : twist.taking ? esc(arena.teamName(twist.taking)) +
            ' taking the signal cabin ' + Math.round((twist.progress || 0) * 100) + '%'
            : (twist.rest > 0 ? 'Signal resetting (' + Math.ceil(twist.rest) + 's)' : 'Junction signal: clear');
        } else if (twist.kind === 'drifts') {
          var snowed = Object.keys(drifts).map(function (l) { return names[l] || l; });
          sub = snowed.length ? 'Drift on ' + esc(snowed.join(' and ')) : 'Silverpine Pass: the track is clear';
        } else if (twist.kind === 'bridges') {
          var up = Object.keys(twist.bridges || {}).filter(function (l) { return twist.bridges[l].up; });
          sub = up.length ? 'Lift bridge UP on ' + esc(up.map(function (l) { return names[l] || l; }).join(' and '))
            : 'Both lift bridges down';
        } else if (twist.kind === 'firedamp') {
          sub = gasWarn ? '<b>Firedamp venting!</b> Keep clear of the hissing board' : 'Lantern Deep: mind the firedamp';
        }
        var own = carts[me] || {};
        return {
          left: { value: Math.round((red.f || 0) * 100) + '%', label: arena.teamName('red'), colour: TEAM_LIGHT.red },
          right: { value: Math.round((blue.f || 0) * 100) + '%', label: arena.teamName('blue'), colour: TEAM_LIGHT.blue },
          sub: sub, bars: bars,
          urgent: !!(own.contest || own.brake > 0 || own.held)
        };
      },
      prompt: function () {
        var h = here();
        return h ? h.text : '';
      },
      draw: function (renderer, dt, time) {
        ['red', 'blue'].forEach(function (team) {
          var cart = carts[team];
          if (!cart) return;
          if (shown[team] === undefined) shown[team] = cart.d || 0;
          var target = cart.target === undefined ? cart.d : cart.target;
          shown[team] += (target + (cart.speed || 0) * 0.05 - shown[team]) * Math.min(1, dt * 8);
          if (cart.brake > 0) cart.brake = Math.max(0, cart.brake - dt);
          if (cart.stoke > 0) cart.stoke = Math.max(0, cart.stoke - dt);
          drawCart(renderer, team, time);
        });
        drawLevers(renderer, time);
        drawCoal(renderer, time);
        drawDepots(renderer, time);
        drawTwist(renderer, time, dt);
        drawSmoke(renderer, dt);
      },
      avatarParts: function (player, parts, self) {
        var carrying = self ? (arena.me && arena.me.coal) : coal[player.id];
        if (!carrying) return parts;
        var yaw = player.yaw || 0, p = player.pos;
        var bx = -Math.sin(yaw) * 1.25, bz = -Math.cos(yaw) * 1.25;
        parts.push({ t: 'box', p: [p[0] + bx, p[1] + 3.9, p[2] + bz], s: [2.0, 2.4, 1.2],
                     c: '#6a5a48', r: [0, yaw, 0] });
        parts.push({ t: 'box', p: [p[0] + bx, p[1] + 5.2, p[2] + bz], s: [1.4, 0.3, 0.9],
                     c: '#2a2420', r: [0, yaw, 0] });
        return parts;
      },
      nameTag: function (player) {
        if (coal[player.id]) return { sub: 'coal' };
        return null;
      },
      scoreHead: function () {
        return '<th>Player</th><th>Company</th><th>Pushed</th><th>Kills</th><th>Deaths</th><th>Score</th>';
      },
      scoreRow: function (row) {
        return '<td>' + esc(arena.teamName(row.team)) + (row.coal ? ' &#9899;' : '') + '</td><td>' +
          (row.pushed || 0) + '</td><td>' + row.kills + '</td><td>' + row.deaths + '</td><td>' + row.score + '</td>';
      }
    };
  });

  // ============================================================ sounds
  var GA = global.GameAudio;
  if (GA && GA.register) {
    GA.register('rr_whistle', function (vol) {
      this.tone({ type: 'square', freq: 740, freqEnd: 760, dur: 0.5, gain: 0.07 * vol });
      this.tone({ type: 'square', freq: 932, freqEnd: 950, dur: 0.5, gain: 0.06 * vol });
      this.later(520, function () {
        this.tone({ type: 'square', freq: 740, freqEnd: 700, dur: 0.9, gain: 0.07 * vol });
        this.tone({ type: 'square', freq: 932, freqEnd: 880, dur: 0.9, gain: 0.06 * vol });
      });
    });
    GA.register('rr_chug', function (vol) {
      for (var i = 0; i < 4; i++) {
        this.later(i * 180, function () {
          this.noise({ freq: 900, freqEnd: 200, dur: 0.14, gain: 0.18 * vol });
        });
      }
    });
    GA.register('rr_bell', function (vol) {
      this.tone({ type: 'triangle', freq: 1320, freqEnd: 1300, dur: 0.9, gain: 0.12 * vol });
      this.tone({ type: 'sine', freq: 2640, freqEnd: 2600, dur: 0.6, gain: 0.04 * vol });
    });
    GA.register('rr_brake', function (vol) {
      this.noise({ filter: 'bandpass', freq: 3800, freqEnd: 2200, dur: 0.7, gain: 0.18 * vol });
      this.tone({ type: 'sawtooth', freq: 1900, freqEnd: 1500, dur: 0.6, gain: 0.05 * vol });
      this.tone({ type: 'square', freq: 120, freqEnd: 60, dur: 0.2, gain: 0.14 * vol });
    });
    GA.register('rr_release', function (vol) {
      this.noise({ filter: 'highpass', freq: 2400, freqEnd: 800, dur: 0.5, gain: 0.14 * vol });
      this.tone({ type: 'square', freq: 220, freqEnd: 330, dur: 0.12, gain: 0.1 * vol });
    });
    GA.register('rr_coal', function (vol) {
      for (var i = 0; i < 3; i++) {
        this.later(i * 70, function () {
          this.noise({ filter: 'bandpass', freq: 1400, freqEnd: 600, dur: 0.1, gain: 0.16 * vol });
        });
      }
    });
    GA.register('rr_signal', function (vol) {
      this.tone({ type: 'square', freq: 520, dur: 0.12, gain: 0.1 * vol });
      this.later(160, function () { this.tone({ type: 'square', freq: 780, dur: 0.2, gain: 0.1 * vol }); });
    });
    GA.register('rr_wind', function (vol) {
      this.noise({ filter: 'bandpass', freq: 500, freqEnd: 1400, dur: 1.4, gain: 0.14 * vol });
    });
    GA.register('rr_lift', function (vol) {
      this.tone({ type: 'sawtooth', freq: 60, freqEnd: 90, dur: 1.6, gain: 0.12 * vol });
      this.noise({ freq: 500, freqEnd: 300, dur: 1.4, gain: 0.08 * vol });
    });
    GA.register('rr_hiss', function (vol) {
      this.noise({ filter: 'highpass', freq: 3000, freqEnd: 5000, dur: 2.2, gain: 0.12 * vol });
    });
    GA.register('rr_hammer', function (vol) {
      this.tone({ type: 'square', freq: 180, freqEnd: 90, dur: 0.08, gain: 0.2 * vol });
      this.noise({ freq: 2200, freqEnd: 400, dur: 0.1, gain: 0.2 * vol });
    });
    GA.register('rr_crunch', function (vol) {
      this.noise({ freq: 1800, freqEnd: 120, dur: 0.45, gain: 0.25 * vol });
    });
  }

  // =================================================== arrival scenes
  var Intro = global.AreaIntro;
  if (!Intro) return;
  var K = Intro.kit;
  var VW = K.VW, VH = K.VH, TAU = K.TAU, FONT = K.FONT, HEAVY = K.HEAVY;
  var seg = K.seg, lerp = K.lerp, outCubic = K.outCubic, outBack = K.outBack, inOut = K.inOut;
  var dot = K.dot, additive = K.additive, roundRect = K.roundRect, fitSize = K.fitSize;
  var spaced = K.spaced, between = K.between, mix = K.mix, rgba = K.rgba, wobble = K.wobble;

  /* A locomotive in silhouette, facing +x, its wheels turning. */
  function loco(ctx, x, y, s, colour, t, light) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = colour;
    ctx.fillRect(-120, -70, 150, 52);              // boiler
    ctx.fillRect(-150, -104, 56, 86);              // cab
    ctx.fillRect(-160, -112, 76, 10);              // cab roof
    ctx.fillRect(-2, -118, 22, 50);                // stack
    ctx.fillRect(-10, -126, 38, 10);
    ctx.fillRect(-70, -88, 22, 20);                // dome
    ctx.beginPath(); ctx.moveTo(30, -18); ctx.lineTo(62, -6); ctx.lineTo(30, -6); ctx.fill(); // cowcatcher
    ctx.fillRect(-170, -24, 210, 12);
    for (var i = 0; i < 4; i++) {
      var wx = -130 + i * 46;
      ctx.beginPath(); ctx.arc(wx, -6, i < 3 ? 18 : 12, 0, TAU); ctx.fill();
      ctx.save();
      ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(wx, -6);
      ctx.lineTo(wx + Math.cos(t * 9 + i) * 14, -6 + Math.sin(t * 9 + i) * 14); ctx.stroke();
      ctx.restore();
    }
    ctx.strokeStyle = colour; ctx.lineWidth = 6;
    ctx.beginPath(); ctx.moveTo(-130 + Math.cos(t * 9) * 10, -6 + Math.sin(t * 9) * 10);
    ctx.lineTo(-38 + Math.cos(t * 9) * 10, -6 + Math.sin(t * 9) * 10); ctx.stroke();
    if (light) {
      ctx.fillStyle = light;
      ctx.fillRect(22, -62, 12, 14);
    }
    ctx.restore();
    if (light) additive(ctx, function () { dot(ctx, light, x + 30 * s, y - 55 * s, 140 * s, 0.55, 60 * s); });
  }

  function puffs(ctx, list, t, colour) {
    list.forEach(function (p) {
      var age = t - p.at;
      if (age < 0 || age > p.life) return;
      var k = age / p.life;
      ctx.fillStyle = rgba(colour, (1 - k) * 0.75);
      ctx.beginPath();
      ctx.arc(p.x + p.vx * age, p.y + p.vy * age, p.r * (1 + k * 2.4), 0, TAU);
      ctx.fill();
    });
  }

  function makePuffs(r, n, x0, rate, y) {
    var out = [];
    for (var i = 0; i < n; i++) {
      out.push({ at: i / rate, x: 0, y: y, vx: between(r, -40, -10), vy: between(r, -90, -50),
                 r: between(r, 14, 26), life: between(r, 1.4, 2.4), off: i });
    }
    return out;
  }

  /* The name, centred, with a thin underline and a spaced kicker over it. */
  function nameText(ctx, name, x, y, max, colour, shade, k) {
    var size = fitSize(ctx, name, 'bold #px ' + HEAVY, 104, max, 0.04);
    ctx.font = 'bold ' + size + 'px ' + HEAVY;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = shade;
    ctx.fillText(name, x + 4, y + 5);
    ctx.fillStyle = colour;
    ctx.fillText(name, x, y);
    ctx.textAlign = 'left';
    return size;
  }

  // ------------------------------------------------- Dustbowl Gulch
  Intro.register('rr_dustbowl', {
    name: 'Dustbowl Gulch',
    tagline: 'Gold in the canyon. Two railroads. One junction.',
    accent: '#f2a03a',
    cues: [[0.2, 'rr_whistle', 0.5], [0.6, 'rr_chug', 0.4], [1.4, 'rr_chug', 0.4],
           [2.2, 'rr_hammer', 0.6], [2.42, 'rr_hammer', 0.6], [2.64, 'rr_hammer', 0.6],
           [2.66, 'slam', 0.3]],
    shakes: [[2.66, 6, 0.3]],
    tagY: 420, tagAt: 2.9,
    setup: function (r) {
      var d = { mesas: [], fronts: [], weeds: [], puffs: makePuffs(r, 26, 0, 6, 0) };
      var x = -40;
      while (x < VW + 80) {
        var w = between(r, 120, 260);
        d.mesas.push({ x: x, w: w, h: between(r, 90, 230), cap: between(r, 6, 18) });
        x += w + between(r, -30, 40);
      }
      x = -20;
      while (x < VW) {
        var fw = between(r, 90, 150);
        d.fronts.push({ x: x, w: fw, h: between(r, 110, 190), sign: r() < 0.6 });
        x += fw + between(r, 4, 20);
      }
      for (var i = 0; i < 3; i++) d.weeds.push({ at: between(r, 0.2, 2.5), y: between(r, 770, 830), s: between(r, 0.7, 1.2) });
      return d;
    },
    draw: function (ctx, t, d) {
      var HZ = 560;
      var sky = ctx.createLinearGradient(0, 0, 0, HZ);
      sky.addColorStop(0, '#3a5f9a');
      sky.addColorStop(0.55, '#d88a5a');
      sky.addColorStop(1, '#f6c27a');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, VW, HZ + 2);
      additive(ctx, function () { dot(ctx, '#ffd28a', 1180, 470 + t * 4, 360, 0.55, 220); });
      ctx.fillStyle = '#ffe6a8';
      ctx.beginPath(); ctx.arc(1180, 470 + t * 4, 48, 0, TAU); ctx.fill();
      // the mesas
      d.mesas.forEach(function (m, i) {
        ctx.fillStyle = i % 2 ? '#a8603e' : '#985434';
        ctx.fillRect(m.x, HZ - m.h, m.w, m.h + 2);
        ctx.fillStyle = '#7a442c';
        ctx.fillRect(m.x - 6, HZ - m.h - m.cap, m.w + 12, m.cap);
      });
      ctx.fillStyle = '#c8a06e';
      ctx.fillRect(0, HZ, VW, VH - HZ);
      // the track and its sleepers
      ctx.fillStyle = '#6a5a4a';
      ctx.fillRect(0, 640, VW, 18);
      for (var k = 0; k < 60; k++) {
        ctx.fillStyle = '#5a4030';
        ctx.fillRect(k * 28 - (t * 0) % 28, 636, 16, 26);
      }
      ctx.fillStyle = '#9a9690';
      ctx.fillRect(0, 634, VW, 4);
      ctx.fillRect(0, 656, VW, 4);
      // the train comes through, smoke streaming back
      var lx = lerp(-300, VW + 400, seg(t, 0.2, 3.6));
      // each puff leaves the stack where the engine was when it was blown
      puffs(ctx, d.puffs.map(function (p) {
        return { at: p.at, x: lerp(-300, VW + 400, seg(p.at, 0.2, 3.6)) + 12, y: 500,
                 vx: p.vx, vy: p.vy, r: p.r, life: p.life };
      }), t, '#efe2c8');
      loco(ctx, lx, 636, 1.15, '#2a1a12', t, '#fff1b0');
      for (var c = 1; c < 4; c++) {
        ctx.fillStyle = c % 2 ? '#8a3a2a' : '#6a4a32';
        ctx.fillRect(lx - 200 - c * 190, 560, 170, 70);
        ctx.fillStyle = '#2a1a12';
        ctx.beginPath(); ctx.arc(lx - 170 - c * 190, 632, 14, 0, TAU); ctx.arc(lx - 60 - c * 190, 632, 14, 0, TAU); ctx.fill();
      }
      // false fronts along Main Street in front
      d.fronts.forEach(function (f, i) {
        var y = VH - f.h;
        ctx.fillStyle = i % 3 === 0 ? '#5a3a24' : (i % 3 === 1 ? '#6a4630' : '#4e3220');
        ctx.fillRect(f.x, y, f.w, f.h);
        ctx.fillStyle = '#3a2416';
        ctx.fillRect(f.x - 4, y - 10, f.w + 8, 12);
        ctx.fillStyle = 'rgba(255,200,120,' + (0.4 + 0.3 * Math.sin(t * 3 + i)) + ')';
        ctx.fillRect(f.x + 16, y + 50, 22, 30);
        ctx.fillRect(f.x + f.w - 38, y + 50, 22, 30);
      });
      // tumbleweeds
      d.weeds.forEach(function (w) {
        var age = t - w.at;
        if (age < 0) return;
        var wx = -60 + age * 420, wy = w.y - Math.abs(Math.sin(age * 4)) * 40;
        ctx.save();
        ctx.translate(wx, wy); ctx.rotate(age * 5); ctx.scale(w.s, w.s);
        ctx.strokeStyle = '#8a6a3a'; ctx.lineWidth = 3;
        for (var j = 0; j < 6; j++) {
          ctx.beginPath(); ctx.arc(0, 0, 22 - j * 2, j, j + 4.2); ctx.stroke();
        }
        ctx.restore();
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Dustbowl Gulch').toUpperCase();
      // a plank board, hammered up: it slams down and three nails go in
      var drop = outBack(seg(t, 1.8, 2.2), 1.6);
      var y = lerp(-200, 250, drop);
      var tilt = wobble(t, 2.2, 0.04, 9, 2.6);
      ctx.save();
      ctx.translate(800, y);
      ctx.rotate(tilt);
      var w = 980, h = 170;
      for (var i = 0; i < 4; i++) {
        ctx.fillStyle = i % 2 ? '#8a5a34' : '#9a6a3e';
        ctx.fillRect(-w / 2, -h / 2 + i * h / 4, w, h / 4 - 3);
        ctx.fillStyle = 'rgba(40,20,10,0.35)';
        ctx.fillRect(-w / 2 + 40 + i * 70, -h / 2 + i * h / 4 + 10, 120, 3);
      }
      ctx.strokeStyle = '#3a2414'; ctx.lineWidth = 6;
      ctx.strokeRect(-w / 2, -h / 2, w, h);
      [[-w / 2 + 26, -h / 2 + 24, 2.2], [w / 2 - 26, -h / 2 + 24, 2.42], [0, h / 2 - 22, 2.64]].forEach(function (n) {
        if (t < n[2]) return;
        ctx.fillStyle = '#2a2a2a';
        ctx.beginPath(); ctx.arc(n[0], n[1], 7, 0, TAU); ctx.fill();
        ctx.fillStyle = '#9a9a9a';
        ctx.beginPath(); ctx.arc(n[0] - 2, n[1] - 2, 3, 0, TAU); ctx.fill();
      });
      ctx.globalAlpha = run.alpha * seg(t, 2.05, 2.3);
      nameText(ctx, name, 0, 6, w - 120, '#ffe6a0', '#3a1c0c');
      ctx.globalAlpha = run.alpha;
      ctx.restore();
      // dust kicked up when it lands
      var dust = seg(t, 2.2, 3.4);
      if (dust > 0 && dust < 1) {
        for (var k = 0; k < 14; k++) {
          ctx.fillStyle = rgba('#e8c890', (1 - dust) * 0.6);
          ctx.beginPath();
          ctx.arc(800 + (k - 7) * 70 * (0.6 + dust), 340 + dust * 30 - (k % 3) * 10, 20 + dust * 40, 0, TAU);
          ctx.fill();
        }
      }
    }
  });

  // ------------------------------------------------ Silverpine Pass
  Intro.register('rr_silverpine', {
    name: 'Silverpine Pass',
    tagline: 'Snow on the summit. Dig if you have to.',
    accent: '#8fd0ff',
    cues: [[0.3, 'rr_wind', 0.5], [1.3, 'rr_whistle', 0.45], [1.9, 'rr_crunch', 0.7],
           [2.5, 'rr_bell', 0.4]],
    shakes: [[1.95, 8, 0.4]],
    tagY: 410, tagAt: 2.8,
    setup: function (r) {
      var d = { peaks: [], pines: [], flakes: [], spray: [] };
      for (var i = 0; i < 9; i++) d.peaks.push({ x: i * 200 + between(r, -40, 40), h: between(r, 220, 420), w: between(r, 260, 380) });
      for (i = 0; i < 26; i++) d.pines.push({ x: between(r, -20, VW + 20), h: between(r, 90, 210), back: r() < 0.5 });
      for (i = 0; i < 160; i++) d.flakes.push({ x: r() * VW, y: r() * VH, s: between(r, 1, 3.6), v: between(r, 40, 120), w: r() * 6 });
      for (i = 0; i < 60; i++) d.spray.push({ a: between(r, -2.6, -0.4), v: between(r, 160, 480), s: between(r, 6, 18) });
      return d;
    },
    draw: function (ctx, t, d) {
      var HZ = 600;
      var sky = ctx.createLinearGradient(0, 0, 0, HZ);
      sky.addColorStop(0, '#2a4a80');
      sky.addColorStop(0.6, '#7a9cc8');
      sky.addColorStop(1, '#dfe8f2');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, VW, HZ + 2);
      d.peaks.forEach(function (p, i) {
        ctx.fillStyle = i % 2 ? '#5a6a80' : '#4a5a70';
        ctx.beginPath(); ctx.moveTo(p.x - p.w / 2, HZ); ctx.lineTo(p.x, HZ - p.h); ctx.lineTo(p.x + p.w / 2, HZ); ctx.fill();
        ctx.fillStyle = '#f4f8fc';
        ctx.beginPath(); ctx.moveTo(p.x - p.w * 0.14, HZ - p.h * 0.72); ctx.lineTo(p.x, HZ - p.h);
        ctx.lineTo(p.x + p.w * 0.14, HZ - p.h * 0.72); ctx.lineTo(p.x + p.w * 0.05, HZ - p.h * 0.66);
        ctx.lineTo(p.x - p.w * 0.04, HZ - p.h * 0.74); ctx.fill();
      });
      d.pines.filter(function (p) { return p.back; }).forEach(function (p) { K.pine(ctx, p.x, HZ + 30, p.h * 0.7, '#2a4a3a', Math.sin(t + p.x) * 2); });
      ctx.fillStyle = '#eef2f6';
      ctx.fillRect(0, HZ, VW, VH - HZ);
      // the snow shed, and the drift across the line in front of it
      ctx.fillStyle = '#4a3420';
      ctx.fillRect(160, 470, 760, 26);
      for (var k = 0; k < 9; k++) ctx.fillRect(170 + k * 92, 490, 14, 150);
      ctx.fillStyle = '#f4f8fc';
      ctx.fillRect(150, 452, 780, 20);
      ctx.fillStyle = '#7a7470';
      ctx.fillRect(0, 640, VW, 14);
      // the plow train bursts through the drift at 1.9
      var px = lerp(-420, 1900, inOut(seg(t, 0.6, 4.2)));
      var burst = seg(t, 1.9, 3.0);
      if (burst < 1) {
        ctx.fillStyle = '#ffffff';
        ctx.beginPath(); ctx.ellipse(1040, 640, 220 * (1 - burst * 0.9), 110 * (1 - burst), 0, Math.PI, TAU); ctx.fill();
      }
      if (t > 1.9) {
        var age = t - 1.9;
        d.spray.forEach(function (s) {
          if (age > 1.4) return;
          var x = 1040 + Math.cos(s.a) * s.v * age, y = 600 + Math.sin(s.a) * s.v * age + 240 * age * age;
          ctx.fillStyle = rgba('#ffffff', 1 - age / 1.4);
          ctx.beginPath(); ctx.arc(x, y, s.s, 0, TAU); ctx.fill();
        });
      }
      loco(ctx, px, 640, 1.1, '#1a2230', t, '#fff6d0');
      ctx.fillStyle = '#b8322a';
      ctx.beginPath(); ctx.moveTo(px + 60, 640); ctx.lineTo(px + 110, 640); ctx.lineTo(px + 60, 560); ctx.fill();
      d.pines.filter(function (p) { return !p.back; }).forEach(function (p) {
        K.pine(ctx, p.x, VH + 40, p.h, '#1e3a2a', Math.sin(t * 1.4 + p.x) * 3);
      });
      d.flakes.forEach(function (f) {
        var y = (f.y + f.v * t) % VH, x = (f.x + Math.sin(t * 1.3 + f.w) * 30 + t * 50) % VW;
        ctx.fillStyle = 'rgba(255,255,255,0.85)';
        ctx.beginPath(); ctx.arc(x, y, f.s, 0, TAU); ctx.fill();
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Silverpine Pass').toUpperCase();
      var k = outCubic(seg(t, 2.0, 2.6));
      ctx.save();
      ctx.translate(800, 250);
      ctx.globalAlpha = run.alpha * k;
      // a frosted board, icicles growing off its bottom edge
      var w = 940, h = 150;
      var g = ctx.createLinearGradient(0, -h / 2, 0, h / 2);
      g.addColorStop(0, '#dff2ff'); g.addColorStop(1, '#a8d0ec');
      ctx.fillStyle = g;
      roundRect(ctx, -w / 2, -h / 2, w, h, 18); ctx.fill();
      ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 4;
      roundRect(ctx, -w / 2 + 6, -h / 2 + 6, w - 12, h - 12, 14); ctx.stroke();
      var grow = seg(t, 2.4, 3.6);
      ctx.fillStyle = '#e8f6ff';
      for (var i = 0; i < 22; i++) {
        var ix = -w / 2 + 30 + i * (w - 60) / 21, len = (18 + (i * 37 % 40)) * grow;
        ctx.beginPath(); ctx.moveTo(ix - 7, h / 2 - 2); ctx.lineTo(ix + 7, h / 2 - 2); ctx.lineTo(ix, h / 2 + len); ctx.fill();
      }
      nameText(ctx, name, 0, 4, w - 120, '#2a4a7a', 'rgba(255,255,255,0.9)');
      ctx.restore();
      ctx.globalAlpha = run.alpha;
      additive(ctx, function () { dot(ctx, '#bfe8ff', 800, 250, 600, 0.25 * k, 160); });
    }
  });

  // --------------------------------------------------- Redrock Mesa
  Intro.register('rr_redrock', {
    name: 'Redrock Mesa',
    tagline: 'Mind the gorge. They can lift the bridge.',
    accent: '#ff7a3a',
    cues: [[0.3, 'rr_bell', 0.5], [0.8, 'rr_bell', 0.5], [1.2, 'rr_lift', 0.7],
           [2.6, 'rr_lift', 0.5], [3.0, 'slam', 0.4]],
    shakes: [[3.0, 6, 0.3]],
    tagY: 430, tagAt: 3.2,
    setup: function (r) {
      var d = { mesas: [], birds: [] };
      var x = -60;
      while (x < VW + 60) {
        var w = between(r, 160, 320);
        d.mesas.push({ x: x, w: w, h: between(r, 120, 300) });
        x += w + between(r, 10, 80);
      }
      for (var i = 0; i < 5; i++) d.birds.push({ x: between(r, 200, 1400), y: between(r, 120, 260), s: between(r, 0.8, 1.3), f: r() * 6 });
      return d;
    },
    draw: function (ctx, t, d) {
      var HZ = 520;
      var sky = ctx.createLinearGradient(0, 0, 0, HZ);
      sky.addColorStop(0, '#35305e');
      sky.addColorStop(0.55, '#b0506a');
      sky.addColorStop(1, '#ff9a5a');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, VW, HZ + 2);
      additive(ctx, function () { dot(ctx, '#ff9a4a', 380, 500, 420, 0.6, 200); });
      d.mesas.forEach(function (m, i) {
        var y = HZ - m.h;
        ctx.fillStyle = i % 2 ? '#8a3a22' : '#a04a2a';
        ctx.fillRect(m.x, y, m.w, m.h + 2);
        [0.3, 0.55, 0.8].forEach(function (b, j) {
          ctx.fillStyle = j % 2 ? 'rgba(232,184,144,0.45)' : 'rgba(255,140,90,0.3)';
          ctx.fillRect(m.x, y + m.h * b, m.w, 8);
        });
      });
      d.birds.forEach(function (b) { K.crow(ctx, b.x + t * 30, b.y, b.s, t * 6 + b.f); });
      // the two rims and the gorge between them
      ctx.fillStyle = '#b8643a';
      ctx.fillRect(0, 560, 520, VH - 560);
      ctx.fillRect(1080, 560, 520, VH - 560);
      var deep = ctx.createLinearGradient(0, 560, 0, VH);
      deep.addColorStop(0, '#6a2a1a'); deep.addColorStop(1, '#1a0a08');
      ctx.fillStyle = deep;
      ctx.fillRect(520, 560, 560, VH - 560);
      ctx.fillStyle = '#3a7a9a';
      ctx.fillRect(520, 860, 560, 40);
      // the towers, and the span going up and coming down again
      ctx.fillStyle = '#8a3a2a';
      [470, 1100].forEach(function (x) {
        ctx.fillRect(x, 200, 30, 380);
        ctx.fillRect(x - 12, 190, 54, 22);
      });
      var lift = seg(t, 1.2, 2.5) - seg(t, 2.6, 3.0);
      var sy = lerp(556, 236, inOut(Math.max(0, lift)));
      ctx.fillStyle = '#5a2a1e';
      ctx.fillRect(500, sy, 600, 26);
      ctx.fillStyle = '#9a9690';
      ctx.fillRect(500, sy - 4, 600, 4);
      for (var k = 0; k < 13; k++) {
        ctx.strokeStyle = '#7a3424'; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.moveTo(500 + k * 50, sy + 26); ctx.lineTo(525 + k * 50, sy + 46); ctx.lineTo(550 + k * 50, sy + 26); ctx.stroke();
      }
      var on = Math.sin(t * 12) > 0 && t < 3.0;
      [485, 1115].forEach(function (x) {
        ctx.fillStyle = on ? '#ff3a2a' : '#4a1410';
        ctx.beginPath(); ctx.arc(x, 182, 10, 0, TAU); ctx.fill();
        if (on) additive(ctx, function () { dot(ctx, '#ff4a2a', x, 182, 60, 0.8); });
      });
      // the cart waiting on the near rim
      ctx.fillStyle = '#c4281c';
      ctx.fillRect(330, 510, 110, 52);
      ctx.fillStyle = '#e8b23a';
      ctx.beginPath(); ctx.moveTo(334, 510); ctx.lineTo(380, 486); ctx.lineTo(436, 510); ctx.fill();
      ctx.fillStyle = '#1a1210';
      ctx.beginPath(); ctx.arc(356, 566, 12, 0, TAU); ctx.arc(414, 566, 12, 0, TAU); ctx.fill();
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Redrock Mesa').toUpperCase();
      // the name rides up with the bridge's span, painted on its girder
      var lift = seg(t, 1.2, 2.5);
      var y = lerp(640, 300, inOut(lift));
      ctx.globalAlpha = run.alpha * seg(t, 1.0, 1.4);
      ctx.save();
      ctx.translate(800, y);
      ctx.fillStyle = '#3a1a10';
      ctx.fillRect(-460, -70, 920, 140);
      ctx.strokeStyle = '#e8b890'; ctx.lineWidth = 4;
      ctx.strokeRect(-450, -60, 900, 120);
      for (var k = 0; k < 10; k++) {
        ctx.fillStyle = '#e8b890';
        ctx.beginPath(); ctx.arc(-430 + k * 95.5, -50, 4, 0, TAU); ctx.arc(-430 + k * 95.5, 50, 4, 0, TAU); ctx.fill();
      }
      nameText(ctx, name, 0, 4, 820, '#ffb070', '#000000');
      ctx.restore();
      ctx.globalAlpha = run.alpha;
    }
  });

  // --------------------------------------------------- Lantern Deep
  Intro.register('rr_lantern', {
    name: 'Lantern Deep',
    tagline: 'The lowest level. Mind the gas, mind the lava.',
    accent: '#ffb347',
    cues: [[0.3, 'rr_chug', 0.3], [0.5, 'tick', 0.4], [0.8, 'tick', 0.4], [1.1, 'tick', 0.4],
           [1.4, 'tick', 0.4], [2.2, 'rr_hiss', 0.5], [2.9, 'explode', 0.4]],
    shakes: [[2.95, 9, 0.4]],
    tagY: 430, tagAt: 3.1,
    setup: function (r) {
      var d = { lamps: [], crystals: [], drips: [] };
      for (var i = 0; i < 8; i++) d.lamps.push({ x: 120 + i * 190, y: between(r, 250, 330), at: 0.4 + i * 0.16 });
      for (i = 0; i < 18; i++) d.crystals.push({ x: between(r, 0, VW), h: between(r, 30, 110), c: ['#5ae0ff', '#b06aff', '#7affc8'][i % 3], a: between(r, -0.4, 0.4) });
      for (i = 0; i < 20; i++) d.drips.push({ x: between(r, 0, VW), at: between(r, 0, 4), v: between(r, 300, 500) });
      return d;
    },
    draw: function (ctx, t, d) {
      ctx.fillStyle = '#0c0907';
      ctx.fillRect(0, 0, VW, VH);
      // the tunnel's timber sets receding to a point
      var cx = 800, cy = 470;
      for (var k = 8; k >= 0; k--) {
        var s = Math.pow(0.72, k), w = 1500 * s, h = 760 * s;
        var lit = d.lamps.some(function (l) { return t > l.at; }) ? 0.25 + 0.6 * (1 - k / 9) : 0.08;
        ctx.strokeStyle = rgba('#7a5232', lit);
        ctx.lineWidth = 26 * s;
        ctx.beginPath();
        ctx.moveTo(cx - w / 2, cy + h / 2); ctx.lineTo(cx - w / 2, cy - h / 2);
        ctx.lineTo(cx + w / 2, cy - h / 2); ctx.lineTo(cx + w / 2, cy + h / 2);
        ctx.stroke();
      }
      // the lava glow from the chasm at the bottom
      additive(ctx, function () { dot(ctx, '#ff5a1a', 800, 900, 700, 0.35 + 0.1 * Math.sin(t * 3), 160); });
      // lanterns lighting one by one down the gallery
      d.lamps.forEach(function (l) {
        var on = t > l.at;
        var sw = Math.sin(t * 2.4 + l.x) * 0.1;
        ctx.strokeStyle = '#3a3030'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(l.x, 140); ctx.lineTo(l.x + sw * 80, l.y); ctx.stroke();
        ctx.fillStyle = on ? '#ffcf6a' : '#3a2a1a';
        ctx.fillRect(l.x + sw * 80 - 10, l.y, 20, 26);
        if (on) additive(ctx, function () { dot(ctx, '#ffb347', l.x + sw * 80, l.y + 12, 120, 0.6); });
      });
      d.crystals.forEach(function (c) {
        ctx.save(); ctx.translate(c.x, VH); ctx.rotate(c.a);
        ctx.fillStyle = c.c;
        ctx.beginPath(); ctx.moveTo(-10, 0); ctx.lineTo(0, -c.h); ctx.lineTo(10, 0); ctx.fill();
        ctx.restore();
        additive(ctx, function () { dot(ctx, c.c, c.x, VH - c.h / 2, 60, 0.35); });
      });
      // the ore cart rolls past
      var mx = lerp(-200, 1800, seg(t, 0.6, 3.8));
      ctx.fillStyle = '#4a4642';
      ctx.fillRect(mx - 80, 720, 160, 70);
      ctx.fillStyle = '#e8b23a';
      ctx.beginPath(); ctx.moveTo(mx - 76, 720); ctx.lineTo(mx - 10, 690); ctx.lineTo(mx + 76, 720); ctx.fill();
      ctx.fillStyle = '#1a1614';
      ctx.beginPath(); ctx.arc(mx - 46, 796, 16, 0, TAU); ctx.arc(mx + 46, 796, 16, 0, TAU); ctx.fill();
      // the firedamp: a green haze, then the flash
      var haze = seg(t, 2.0, 2.9);
      if (haze > 0 && t < 3.0) additive(ctx, function () { dot(ctx, '#8aff6a', 1180, 560, 260 * haze, 0.35 * haze); });
      var boom = seg(t, 2.9, 3.5);
      if (boom > 0 && boom < 1) {
        additive(ctx, function () { dot(ctx, '#ffd28a', 1180, 560, 700 * boom, 0.9 * (1 - boom)); });
      }
      d.drips.forEach(function (dr) {
        var age = (t - dr.at) % 2.2;
        if (age < 0) return;
        ctx.fillStyle = 'rgba(160,200,220,0.6)';
        ctx.fillRect(dr.x, 100 + age * dr.v, 2, 8);
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Lantern Deep').toUpperCase();
      // a brass plate, struck: sparks fly off it as it comes into the light
      var k = outBack(seg(t, 1.5, 2.0), 1.4);
      ctx.save();
      ctx.translate(800, 250);
      ctx.scale(k, k);
      var g = ctx.createLinearGradient(0, -80, 0, 80);
      g.addColorStop(0, '#f2c86a'); g.addColorStop(0.5, '#b8862a'); g.addColorStop(1, '#7a5418');
      ctx.fillStyle = g;
      roundRect(ctx, -470, -80, 940, 160, 12); ctx.fill();
      ctx.strokeStyle = '#4a3010'; ctx.lineWidth = 5;
      roundRect(ctx, -458, -68, 916, 136, 9); ctx.stroke();
      [[-440, -50], [440, -50], [-440, 50], [440, 50]].forEach(function (p) {
        ctx.fillStyle = '#5a3c14';
        ctx.beginPath(); ctx.arc(p[0], p[1], 8, 0, TAU); ctx.fill();
      });
      nameText(ctx, name, 0, 4, 840, '#2a1a08', 'rgba(255,240,200,0.6)');
      ctx.restore();
      var sparks = seg(t, 1.9, 2.8);
      if (sparks > 0 && sparks < 1) {
        for (var i = 0; i < 26; i++) {
          var a = i * 0.9, r = sparks * (160 + (i * 37) % 200);
          ctx.fillStyle = rgba('#ffd27a', 1 - sparks);
          ctx.fillRect(800 + Math.cos(a) * r * 2.2, 250 + Math.sin(a) * r * 0.7 + sparks * sparks * 120, 4, 4);
        }
      }
      additive(ctx, function () { dot(ctx, '#ffb347', 800, 250, 700, 0.2 * seg(t, 1.6, 2.2), 180); });
    }
  });
})(window);
