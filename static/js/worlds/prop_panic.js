/* Prop Panic -- the Game View half of prop hunt
   (app/game/worlds/prop_panic.py).

   A hider is drawn as whatever it is disguised as: the area's own drawing
   of that prop (extra.props, the same parts the map is furnished with),
   turned by its quarter, bobbing a little when it moves.  Your own disguise
   puts you in a third-person orbit camera, gives your body the prop's hull
   (Physics reads ``local.size``), and E picks the prop under the crosshair
   to become; R turns you a quarter if there is room.

   Seekers get a blindfold through the countdown, the popper's tracer, the
   sniffer's reading and the glitter bomb's burst.  Everybody sees decoys,
   taunts (notes and a sound from where they came), finds, and each area's
   twist: Mittens the cat walking the house, the toy shop's power cuts (and
   the seekers' torches), MegaMart's flash-sale price tags and the museum's
   searchlight and alarm.

   Four arrival scenes, one per place, are registered at the bottom. */
(function (global) {
  'use strict';
  var Arena = global.Arena || { register: function () {} };

  var TEAM = { red: '#d8402a', blue: '#2f6ad0' };
  var TEAM_LIGHT = { red: '#ff9a8a', blue: '#9ec8ff' };
  var PINK = '#e85a7a';
  var EYE = 5.05;
  var REACH = 18;
  var Q = Math.PI / 2;

  function rgb(hex) {
    var n = parseInt(String(hex).slice(1), 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
  }
  function esc(text) {
    return String(text == null ? '' : text).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function el(id) { return document.getElementById(id); }

  /* ray against a box: the distance to it, or null */
  function rayBox(o, d, lo, hi) {
    var tmin = 0, tmax = Infinity;
    for (var a = 0; a < 3; a++) {
      if (Math.abs(d[a]) < 1e-8) {
        if (o[a] < lo[a] || o[a] > hi[a]) return null;
        continue;
      }
      var inv = 1 / d[a], t1 = (lo[a] - o[a]) * inv, t2 = (hi[a] - o[a]) * inv;
      if (t1 > t2) { var tmp = t1; t1 = t2; t2 = tmp; }
      tmin = Math.max(tmin, t1);
      tmax = Math.min(tmax, t2);
      if (tmin > tmax) return null;
    }
    return tmin;
  }

  /* A kind's parts turned ``q`` quarter turns, still at the origin. */
  function turnParts(parts, q) {
    var yaw = q * Q, c = Math.round(Math.cos(yaw)), s = Math.round(Math.sin(yaw));
    return parts.map(function (p) {
      var lx = p.p[0], lz = p.p[2];
      var out = { t: p.t, p: [lx * c + lz * s, p.p[1], -lx * s + lz * c], s: p.s, c: p.c };
      var total = (q + (p.turn || 0)) % 4;
      if (total) out.r = [0, total * Q, 0];
      if (p.m) out.m = p.m;
      if (p.dec) out.dec = p.dec;
      if (p.dw) out.dw = 1;
      if (p.a !== undefined) out.a = p.a;
      return out;
    });
  }

  // ============================================================ plugin
  Arena.register('prop_panic', function (arena) {
    var client = arena.client;
    var kinds = {}, decor = [], starter = '', twistKind = '', accent = PINK;
    var turned = {};               // kind -> [parts at q 0..3]
    var dis = {};                  // pid -> [kind, q]
    var decoys = [];               // [id, kind, x, y, z, q]
    var reveals = {};              // pid -> {why, left}
    var hiders = 'red', alive = 0, started = 0, creak = 0;
    var twist = { kind: '' };
    var cat = null, catShown = null, spot = null;
    var notes = [], bursts = [], shots = [];
    var dark = 0, flicker = 0, sale = { kind: '', name: '', warn: 0, left: 0 };
    var pick = null, lastPick = 0, myQ = 0, myDis = '', sniffText = '', sniffUntil = 0;
    var veil = null, baseAmbient = null;

    function kindName(k) { return (kinds[k] && kinds[k].name) || 'prop'; }
    function size(k, q) {
      var s = (kinds[k] && kinds[k].size) || [2, 2, 2];
      return q % 2 ? { w: s[2], h: s[1], d: s[0] } : { w: s[0], h: s[1], d: s[2] };
    }
    function partsOf(k, q) {
      if (!kinds[k]) return [];
      if (!turned[k]) turned[k] = [0, 1, 2, 3].map(function (n) { return turnParts(kinds[k].parts, n); });
      return turned[k][q % 4];
    }
    function amHider() { return client.myTeam === hiders; }
    function amProp() { return amHider() && !arena.me.out && client.local.alive && arena.phase !== 'intermission'; }
    function isHider(player) { return player && player.team === hiders; }
    function hullOf(pos, k, q) {
      var sz = size(k, q);
      return [[pos[0] - sz.w / 2, pos[1], pos[2] - sz.d / 2], [pos[0] + sz.w / 2, pos[1] + sz.h, pos[2] + sz.d / 2]];
    }

    // -------------------------------------------------------- the veil
    function makeVeil() {
      if (veil) return veil;
      var host = document.querySelector('#game-root .hud') || document.body;
      veil = document.createElement('div');
      veil.id = 'pp-veil';
      veil.style.cssText = 'position:absolute;left:0;top:0;right:0;bottom:0;pointer-events:none;' +
        'opacity:0;transition:opacity .35s;z-index:1;display:flex;align-items:center;' +
        'justify-content:center;flex-direction:column;color:#f4e6c8;font:bold 28px sans-serif;' +
        'text-shadow:0 2px 8px #000;text-align:center';
      host.insertBefore(veil, host.firstChild);
      return veil;
    }

    function updateVeil() {
      var v = makeVeil();
      var blind = arena.phase === 'setup' && !amHider() && !arena.me.out && client.myTeam;
      if (blind) {
        var left = Math.max(0, Math.ceil(arena.phaseLeft - (performance.now() / 1000 - (arena.phaseAt || 0))));
        v.style.background = 'radial-gradient(ellipse at 50% 45%, rgba(20,10,20,0.96), rgba(0,0,0,0.99))';
        v.innerHTML = '<div style="font-size:15px;letter-spacing:6px;opacity:.7">EYES SHUT</div>' +
          '<div style="font-size:64px;margin:10px 0">' + left + '</div>' +
          '<div style="font-size:18px;opacity:.85">The hiders are hiding. The pen opens when the count runs out.</div>';
        v.style.opacity = '1';
        return;
      }
      v.innerHTML = '';
      if (dark > 0) {
        var torch = !amHider();
        v.style.background = torch
          ? 'radial-gradient(circle at 50% 50%, rgba(0,0,0,0) 0, rgba(0,0,0,0.05) 120px, rgba(0,0,0,0.93) 260px)'
          : 'rgba(0,0,8,0.82)';
        v.style.opacity = '1';
        return;
      }
      if (flicker > 0) {
        var on = Math.floor(flicker * 9) % 3 === 0;
        v.style.background = 'rgba(0,0,0,0.85)';
        v.style.transition = 'none';
        v.style.opacity = on ? '1' : '0';
        return;
      }
      v.style.transition = 'opacity .35s';
      v.style.opacity = '0';
    }

    function setDark(on) {
      var r = client.renderer;
      if (!r || !r.setAmbient) return;
      if (on) {
        if (baseAmbient === null) baseAmbient = (client.map && client.map.ambient) || '#a0a8b8';
        r.setAmbient('#2a2a3a');
      } else if (baseAmbient !== null) {
        r.setAmbient(baseAmbient);
        baseAmbient = null;
      }
    }

    // -------------------------------------------------------- the map
    function loadMap(map) {
      var mk = (map && map.markers) || {};
      var extra = mk.extra || {};
      kinds = extra.props || {};
      turned = {};
      starter = extra.starter || '';
      twistKind = extra.twist || '';
      accent = extra.accent || PINK;
      decor = (extra.decor || []).map(function (d, i) {
        var h = hullOf(d.p, d.k, d.q || 0);
        return { i: i, k: d.k, q: d.q || 0, p: d.p, lo: h[0], hi: h[1] };
      });
      dis = {}; decoys = []; reveals = {}; notes = []; bursts = []; shots = [];
      cat = null; catShown = null; spot = null; dark = 0; flicker = 0;
      sale = { kind: '', name: '', warn: 0, left: 0 };
      setDark(false);
      applySize();
    }

    function applyState(pp) {
      if (!pp) return;
      hiders = pp.hiders || hiders;
      alive = pp.alive || 0;
      started = pp.started || 0;
      creak = pp.creak || 0;
      if (pp.dis) {
        dis = {};
        Object.keys(pp.dis).forEach(function (id) { dis[id] = pp.dis[id]; });
      }
      if (pp.decoys) decoys = pp.decoys;
      if (pp.reveals) {
        reveals = {};
        Object.keys(pp.reveals).forEach(function (id) {
          reveals[id] = { why: pp.reveals[id][0], left: pp.reveals[id][1] };
        });
      }
      twist = pp.twist || twist;
      if (twist.kind === 'blackout') {
        var was = dark > 0;
        dark = twist.dark || 0;
        if (dark > 0 && !was) setDark(true);
        if (dark <= 0 && was) setDark(false);
      }
      if (twist.kind === 'sale') {
        sale = { kind: twist.sale || '', name: twist.name || '', warn: twist.warn || 0, left: twist.left || 0 };
      }
      applySize();
    }

    /* Your own body is the size of what you are disguised as. */
    function applySize() {
      var local = client.local;
      if (!local) return;
      var mine = dis[client.myId];
      if (amHider() && mine && !arena.me.out) {
        myDis = mine[0]; myQ = mine[1];
        local.size = size(myDis, myQ);
      } else {
        delete local.size;
      }
    }

    // -------------------------------------------------------- sounds
    function audible(p) {
      var me = client.local.pos;
      var d = p ? Math.hypot(p[0] - me[0], p[1] - me[1], p[2] - me[2]) : 0;
      return Math.max(0.12, Math.min(1, 1.15 - d / 110));
    }
    function play(name, p, vol) {
      client.audio.play(name, { volume: (vol || 1) * audible(p) });
    }

    function noteBurst(p, colour) {
      for (var i = 0; i < 5; i++) {
        notes.push({ p: [p[0] + (Math.random() - 0.5) * 2, p[1] + 2, p[2] + (Math.random() - 0.5) * 2],
                     v: [(Math.random() - 0.5) * 2, 4 + Math.random() * 3, (Math.random() - 0.5) * 2],
                     t: 0, life: 1.6 + Math.random() * 0.6, c: colour || '#ffd23a', spin: Math.random() * 6 });
      }
    }

    function popBurst(p, colour, n) {
      var parts = client.particles;
      if (parts && parts.burst) parts.burst('confetti', [p[0], p[1] + 1.5, p[2]]);
      for (var i = 0; i < (n || 12); i++) {
        bursts.push({ p: [p[0], p[1] + 1, p[2]],
                      v: [(Math.random() - 0.5) * 12, 3 + Math.random() * 8, (Math.random() - 0.5) * 12],
                      t: 0, life: 0.7 + Math.random() * 0.5, c: colour || '#f2f0ea', s: 0.4 + Math.random() * 0.5 });
      }
    }

    // -------------------------------------------------------- messages
    var TAUNTS = ['pp_honk', 'pp_kazoo', 'pp_quack', 'pp_boing', 'pp_whistle', 'pp_toot', 'pp_cuckoo',
                  'pp_raspberry'];
    var messages = {
      ppd: function (msg) {
        if (msg.k) dis[msg.id] = [msg.k, msg.q || 0];
        else delete dis[msg.id];
        if (msg.id === client.myId) {
          if (msg.k && msg.k !== myDis) play('pp_change', null, 0.7);
          applySize();
        } else if (msg.k) {
          var p = client.players[msg.id];
          if (p && amHider()) popBurst(p.pos, '#ffffff', 4);
        }
      },
      ppall: function (msg) {
        dis = msg.d || {};
        decoys = msg.decoys || [];
        applySize();
      },
      pps: function (msg) { applyState(msg.s); },
      ppx: function (msg) {
        var k = msg.k;
        var me = client.myId;
        if (k === 'shot') {
          var colour = msg.h === 'prop' ? '#ff5a8a' : '#ffd23a';
          client.tracers.push({ a: msg.a, b: msg.b, t: 0, c: rgb(colour) });
          if (client.particles) client.particles.burst('impact', msg.b);
          play('pp_pop', msg.a, 0.5);
        } else if (k === 'hit') {
          client.audio.play('hit', { volume: 0.7 });
        } else if (k === 'wrong') {
          client.hud.toast('Wrong guess -- that was just a ' + esc(String(msg.what || 'prop').toLowerCase()), 'bad');
          client.audio.play('pp_wrong', { volume: 0.8 });
        } else if (k === 'became') {
          client.hud.toast('You are a <b>' + esc(msg.what) + '</b> now', 'good');
        } else if (k === 'fooled') {
          client.hud.toast('<b>' + esc(msg.by) + '</b> fell for your decoy!', 'good');
          client.audio.play('pp_honk', { volume: 0.6 });
        } else if (k === 'decoy') {
          decoys.push(msg.d);
          play('pp_change', [msg.d[2], msg.d[3], msg.d[4]], 0.6);
        } else if (k === 'decoy_pop') {
          decoys = decoys.filter(function (d) { return d[0] !== msg.id; });
          popBurst(msg.p, '#c8a070', 14);
          play('pp_poof', msg.p, 1);
        } else if (k === 'sniff') {
          sniffText = msg.d < 0 ? 'Nothing to sniff out round here' :
            'Sniffed something <b>' + esc(msg.band) + '</b> (' + msg.d + ' studs)';
          sniffUntil = performance.now() / 1000 + 4;
          client.audio.play('pp_sniff', { volume: 0.8 });
        } else if (k === 'glitter') {
          popBurst(msg.p, '#ff7ad8', 30);
          for (var g = 0; g < 26; g++) {
            var a = Math.random() * Math.PI * 2, r = Math.random() * msg.r;
            bursts.push({ p: [msg.p[0] + Math.cos(a) * r, msg.p[1] + 0.5, msg.p[2] + Math.sin(a) * r],
                          v: [0, 2 + Math.random() * 4, 0], t: 0, life: 1.4, c: ['#ff7ad8', '#ffd23a', '#7ad8ff'][g % 3],
                          s: 0.35 });
          }
          play('pp_glitter', msg.p, 1);
        } else if (k === 'taunt') {
          var tp = msg.p;
          noteBurst(tp, msg.why === 'creak' ? '#c8b090' : (msg.why === 'sniff' ? '#7affd8' : '#ffd23a'));
          play(msg.why === 'taunt' ? TAUNTS[(msg.n || 0) % TAUNTS.length] : 'pp_squeak', tp, 1);
        } else if (k === 'scurry') {
          var sp = client.players[msg.id];
          if (sp) play('pp_whoosh', sp.pos, 0.6);
          if (msg.id === me) client.audio.play('pp_whoosh', { volume: 0.7 });
        } else if (k === 'found') {
          popBurst(msg.p, '#ffd23a', 20);
          play('pp_found', msg.p, 1);
          delete dis[msg.id];
          if (msg.id === me) {
            arena.banner('FOUND!', '', 'bad', 2600);
            applySize();
          }
        } else if (k === 'last') {
          arena.banner("YOU'RE THE LAST ONE", '', 'bad', 3000);
          client.audio.play('pp_creak', { volume: 0.9 });
        } else if (k === 'release') {
          arena.banner(amHider() ? 'HERE THEY COME' : 'READY OR NOT!', '', 'go', 2200);
          client.audio.play('pp_release', { volume: 0.9 });
        } else if (k === 'creak') {
          arena.banner('The house creaks...', '', 'area', 1600);
          client.audio.play('pp_creak', { volume: 0.8 });
        } else if (k === 'reveal') {
          reveals[msg.id] = { why: msg.why, left: msg['for'] || 5 };
          if (msg.id === me) {
            var text = { glitter: "You've been glittered!", cat: 'The cat is staring at you!',
                         sale: "You've got a price tag on you!", alarm: 'You set off the alarm!' }[msg.why];
            if (text) client.hud.toast(text, 'bad');
          }
        } else if (k === 'cat') {
          play('pp_meow', msg.p, 1);
        } else if (k === 'hiss') {
          play('pp_hiss', msg.p, 1);
        } else if (k === 'flicker') {
          flicker = msg['in'] || 3;
          client.audio.play('pp_buzz', { volume: 0.7 });
        } else if (k === 'lights') {
          if (msg.on) {
            dark = 0; flicker = 0; setDark(false);
            client.audio.play('power', { volume: 0.6 });
          } else {
            dark = msg['for'] || 12; flicker = 0; setDark(true);
            client.audio.play('pp_dark', { volume: 0.8 });
            arena.banner('LIGHTS OUT', '', 'bad', 2200);
          }
        } else if (k === 'sale_warn') {
          sale = { kind: msg.kind, name: msg.name, warn: msg['in'] || 6, left: 0 };
          client.audio.play('pp_chime', { volume: 0.9 });
          arena.banner(myDis === msg.kind && amHider() ? 'FLASH SALE ON YOU -- CHANGE NOW!'
                       : 'FLASH SALE: ' + esc(String(msg.name).toUpperCase()), '', 'area', 3000);
        } else if (k === 'sale_on') {
          sale = { kind: msg.kind, name: msg.name, warn: 0, left: 10 };
          client.audio.play('pp_chime', { volume: 0.6 });
        } else if (k === 'alarm') {
          play('pp_alarm', msg.p, 1);
          arena.flashScreen('rgba(255,30,30,0.25)', 400);
        }
      }
    };

    // -------------------------------------------------- what you look at
    function look() {
      var cam = client.cameraPosition ? client.cameraPosition() : null;
      var dir = client.lookDirection();
      var eye = cam ? cam.eye : [client.local.pos[0], client.local.pos[1] + EYE, client.local.pos[2]];
      return { eye: eye, dir: dir };
    }

    function findPick() {
      if (!amProp()) return null;
      var ray = look();
      var phys = client.physics;
      var max = 40;
      var world = phys ? phys.rayDistance(ray.eye, ray.dir, max) : max;
      var me = client.local.pos;
      var best = null, bestT = world + 0.8;
      for (var i = 0; i < decor.length; i++) {
        var d = decor[i];
        if (Math.abs(d.p[0] - me[0]) > REACH + 4 || Math.abs(d.p[2] - me[2]) > REACH + 4) continue;
        var t = rayBox(ray.eye, ray.dir, d.lo, d.hi);
        if (t === null || t >= bestT) continue;
        var cx = (d.lo[0] + d.hi[0]) / 2, cy = (d.lo[1] + d.hi[1]) / 2, cz = (d.lo[2] + d.hi[2]) / 2;
        if (Math.hypot(cx - me[0], cy - me[1] - EYE, cz - me[2]) > REACH) continue;
        best = d; bestT = t;
      }
      return best;
    }

    /* Room for a hull here, or just beside? */
    function roomFor(k, q) {
      var phys = client.physics, pos = client.local.pos;
      var sz = size(k, q);
      if (!phys || !phys.blocked) return pos.slice();
      if (!phys.blocked(pos[0], pos[1] + 0.05, pos[2], null, sz)) return pos.slice();
      var steps = [0.6, 1.2, 1.8];
      for (var s = 0; s < steps.length; s++) {
        for (var a = 0; a < 8; a++) {
          var ang = a * Math.PI / 4;
          var x = pos[0] + Math.cos(ang) * steps[s], z = pos[2] + Math.sin(ang) * steps[s];
          if (!phys.blocked(x, pos[1] + 0.05, z, null, sz)) return [x, pos[1], z];
        }
      }
      return null;
    }

    // -------------------------------------------------------- drawing
    function pushParts(renderer, parts, base, bob, alpha) {
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        var part = { t: p.t, p: [base[0] + p.p[0], base[1] + p.p[1] + (bob || 0), base[2] + p.p[2]],
                     s: p.s, c: p.c };
        if (p.r) part.r = p.r;
        if (p.m) part.m = p.m;
        if (p.dec) part.dec = p.dec;
        if (p.dw) part.dw = 1;
        if (alpha !== undefined) part.a = alpha;
        else if (p.a !== undefined) part.a = p.a;
        renderer.push(part);
      }
    }

    function rawBox(renderer, x, y, z, sx, sy, sz, colour, o) {
      o = o || {};
      renderer.pushRaw(o.kind || 'box', x, y, z, 0, o.yaw || 0, 0, sx, sy, sz, rgb(colour),
                       o.a === undefined ? 1 : o.a, 0, o.m || 0, o.e || 0, null);
    }

    function drawCat(renderer, time) {
      if (!catShown) return;
      var c = catShown;
      var yaw = c.yaw, cs = Math.cos(yaw), sn = Math.sin(yaw);
      function at(lx, ly, lz) { return [c.p[0] + lx * cs + lz * sn, c.p[1] + ly, c.p[2] - lx * sn + lz * cs]; }
      var walking = c.mode === 0 || c.mode === 2;
      var sit = c.mode === 3 || c.mode === 1;
      var step = walking ? Math.sin(time * (c.mode === 2 ? 22 : 13)) * 0.22 : 0;
      var fur = '#d8873a', dark = '#a85a22', light = '#f4e0c0';
      function box(lx, ly, lz, sx, sy, sz, colour, kind) {
        var p = at(lx, ly, lz);
        renderer.pushRaw(kind || 'box', p[0], p[1], p[2], 0, yaw, 0, sx, sy, sz, rgb(colour), 1, 0, 0, 0, null);
      }
      if (sit) {
        box(0, 0.75, -0.2, 0.9, 1.1, 1.1, fur, 'rbox');
        box(0, 0.45, 0.4, 0.8, 0.5, 0.5, light, 'rbox');
      } else {
        box(0, 0.85, 0, 0.8, 0.7, 1.7, fur, 'rbox');
        box(0, 0.85, 0.3, 0.6, 0.5, 0.7, light, 'rbox');
      }
      var hy = sit ? 1.65 : 1.35, hz = sit ? 0.35 : 0.95;
      box(0, hy, hz, 0.8, 0.7, 0.7, fur, 'rbox');
      box(-0.24, hy + 0.48, hz - 0.05, 0.22, 0.32, 0.12, dark, 'cone');
      box(0.24, hy + 0.48, hz - 0.05, 0.22, 0.32, 0.12, dark, 'cone');
      box(-0.18, hy + 0.08, hz + 0.36, 0.12, 0.14, 0.04, c.mode === 1 ? '#7aff8a' : '#2a2a2a', 'sph');
      box(0.18, hy + 0.08, hz + 0.36, 0.12, 0.14, 0.04, c.mode === 1 ? '#7aff8a' : '#2a2a2a', 'sph');
      box(0, hy - 0.08, hz + 0.37, 0.12, 0.08, 0.04, '#f07aa8', 'box');
      if (!sit) {
        [[-0.26, 0.6], [0.26, 0.6], [-0.26, -0.6], [0.26, -0.6]].forEach(function (l, i) {
          box(l[0], 0.25, l[1] + (i % 2 ? step : -step), 0.2, 0.5, 0.2, fur, 'box');
        });
      }
      var wag = Math.sin(time * 3) * 0.3;
      box(wag * 0.4, sit ? 0.3 : 1.1, sit ? -0.7 : -1.0, 0.16, 0.16, 1.2, dark, 'box');
      if (c.mode === 1) {
        var q = at(0, hy + 1.6 + Math.abs(Math.sin(time * 6)) * 0.2, hz);
        renderer.pushRaw('box', q[0], q[1], q[2], 0, 0, 0, 0.25, 0.8, 0.25, rgb('#ffd23a'), 1, 0, 2, 0, null);
        renderer.pushRaw('box', q[0], q[1] - 0.65, q[2], 0, 0, 0, 0.25, 0.25, 0.25, rgb('#ffd23a'), 1, 0, 2, 0, null);
      }
    }

    function drawReveal(renderer, id, pos, k, q, time) {
      var r = reveals[id];
      if (!r) return;
      var sz = size(k, q);
      var top = pos[1] + sz.h + 1.2 + Math.sin(time * 4) * 0.2;
      if (r.why === 'glitter') {
        for (var i = 0; i < 6; i++) {
          var a = time * 2 + i * 1.05;
          rawBox(renderer, pos[0] + Math.cos(a) * (sz.w * 0.7 + 0.4), pos[1] + (i % 3) * sz.h * 0.4 + 0.3,
                 pos[2] + Math.sin(a) * (sz.d * 0.7 + 0.4), 0.25, 0.25, 0.25,
                 ['#ff7ad8', '#ffd23a', '#7ad8ff'][i % 3], { m: 2, kind: 'sph' });
        }
      } else if (r.why === 'sale') {
        var p = [pos[0], top + 0.6, pos[2]];
        renderer.pushRaw('box', p[0], p[1], p[2], 0, time * 1.5, 0, 2.2, 1.3, 0.12, rgb('#f2c230'), 1, 0, 0, 0,
                         global.Textures && Textures.decal ? Textures.decal('t~SALE!~#f2c230~#c82a2a~1.70') : null);
        rawBox(renderer, p[0], p[1] + 0.9, p[2], 0.06, 0.6, 0.06, '#8a8a8a');
      } else if (r.why === 'alarm') {
        rawBox(renderer, pos[0], top, pos[2], 1.0, 1.0, 1.0, Math.floor(time * 6) % 2 ? '#ff2a2a' : '#7a0a0a',
               { m: 2, kind: 'sph' });
      } else if (r.why === 'cat') {
        rawBox(renderer, pos[0], top + 0.4, pos[2], 0.3, 1.0, 0.3, '#ffd23a', { m: 2 });
        rawBox(renderer, pos[0], top - 0.4, pos[2], 0.3, 0.3, 0.3, '#ffd23a', { m: 2 });
      }
    }

    function drawSpot(renderer, time) {
      if (!spot) return;
      var top = spot[1] + 24;
      renderer.pushRaw('cyl', spot[0], (spot[1] + top) / 2, spot[2], 0, 0, 0, spot[3] * 2, top - spot[1], spot[3] * 2,
                       rgb('#fff6c8'), 0.12, 0, 3, 0, null);
      renderer.pushRaw('cyl', spot[0], spot[1] + 0.08, spot[2], 0, 0, 0, spot[3] * 2, 0.06, spot[3] * 2,
                       rgb('#fff6c8'), 0.35, 0, 2, 0, null);
    }

    function drawFx(renderer, dt) {
      notes = notes.filter(function (n) {
        n.t += dt;
        if (n.t > n.life) return false;
        n.p[0] += n.v[0] * dt; n.p[1] += n.v[1] * dt; n.p[2] += n.v[2] * dt;
        var k = 1 - n.t / n.life;
        renderer.pushRaw('box', n.p[0], n.p[1], n.p[2], 0, n.spin + n.t * 3, 0, 0.18, 0.7, 0.18, rgb(n.c), k, 0, 2, 0, null);
        renderer.pushRaw('sph', n.p[0] - 0.22, n.p[1] - 0.35, n.p[2], 0, 0, 0, 0.5, 0.36, 0.36, rgb(n.c), k, 0, 2, 0, null);
        return true;
      });
      bursts = bursts.filter(function (b) {
        b.t += dt;
        if (b.t > b.life) return false;
        b.v[1] -= 22 * dt;
        b.p[0] += b.v[0] * dt; b.p[1] += b.v[1] * dt; b.p[2] += b.v[2] * dt;
        renderer.pushRaw('box', b.p[0], b.p[1], b.p[2], b.t * 5, b.t * 7, 0, b.s, b.s, b.s, rgb(b.c),
                         1 - b.t / b.life, 0, 2, 0, null);
        return true;
      });
    }

    // -------------------------------------------------------- the hud
    function roleChip() {
      if (!client.myTeam || arena.phase === 'intermission') { arena.setRole(''); return; }
      var team = client.myTeam;
      if (arena.me.out) {
        arena.setRole('<b>FOUND</b> &bull; watching the rest', 'out');
        return;
      }
      if (amHider()) {
        arena.setRole('<b style="color:' + TEAM_LIGHT[team] + '">HIDING</b> as a <b>' +
                      esc(kindName(myDis)) + '</b>' + (arena.me.rev ? ' &bull; <b style="color:#ff7a7a">SPOTTED</b>' : ''), team);
      } else {
        arena.setRole('<b style="color:' + TEAM_LIGHT[team] + '">SEEKING</b> &bull; find every hider', team);
      }
    }

    function hud(state) {
      var hid = arena.teamName(hiders), seek = arena.teamName(hiders === 'red' ? 'blue' : 'red');
      var sub = '';
      if (arena.phase === 'setup') {
        sub = '<b>' + esc(hid) + '</b> are hiding &bull; ' + esc(seek) + ' are counting';
      } else if (arena.phase === 'active') {
        sub = amHider() ? 'Stay still. Taunt for points. <b>E</b> become what you look at, <b>R</b> turn.'
          : 'Pop the props that are people. A wrong guess hurts.';
      }
      if (twist.kind === 'cat') sub += ' &bull; Mittens is about';
      else if (twist.kind === 'blackout') {
        sub += dark > 0 ? ' &bull; <b>LIGHTS OUT</b> (' + Math.ceil(dark) + 's)' : (flicker > 0 ? ' &bull; <b>the lights flicker...</b>' : '');
      } else if (twist.kind === 'sale' && sale.kind) {
        sub += sale.warn > 0 ? ' &bull; <b>Flash sale</b> on ' + esc(sale.name) + ' in ' + Math.ceil(sale.warn) + 's'
          : (sale.left > 0 ? ' &bull; <b>SALE ON ' + esc(String(sale.name).toUpperCase()) + '</b>' : '');
      } else if (twist.kind === 'alarm') sub += ' &bull; mind the searchlight';
      if (sniffText && performance.now() / 1000 < sniffUntil) sub += '<br>' + sniffText;
      if (creak > 0 && creak < 20 && arena.phase === 'active') sub += ' &bull; the house creaks in ' + Math.ceil(creak) + 's';
      return {
        left: { value: alive + '/' + (started || alive), label: hid + ' hidden', colour: TEAM_LIGHT[hiders] },
        right: { value: seek, label: 'seeking', colour: TEAM_LIGHT[hiders === 'red' ? 'blue' : 'red'] },
        sub: sub,
        bars: started ? [{ label: 'Still hidden', value: alive / Math.max(1, started), colour: TEAM[hiders],
                           text: alive + ' of ' + started }] : [],
        urgent: alive === 1 && started >= 3 && arena.phase === 'active'
      };
    }

    // -------------------------------------------------------- hooks
    return {
      init: function () { makeVeil(); },
      onMap: loadMap,
      onArea: function () { arena.setRole(''); },
      onState: function (state) { applyState(state.pp); },
      onSnapshot: function (msg) {
        var ax = msg.ax;
        if (!ax) { cat = null; spot = null; return; }
        if (ax.cat) {
          cat = { p: [ax.cat[0], ax.cat[1], ax.cat[2]], yaw: ax.cat[3], mode: ax.cat[4] };
          if (!catShown || Math.hypot(catShown.p[0] - cat.p[0], catShown.p[2] - cat.p[2]) > 12) {
            catShown = { p: cat.p.slice(), yaw: cat.yaw, mode: cat.mode };
          }
        } else { cat = null; catShown = null; }
        spot = ax.spot || null;
      },
      onMe: function (me) {
        if (me.hiders) hiders = me.hiders;
        if (me.dis !== undefined && me.dis) { myDis = me.dis; myQ = me.q || 0; dis[client.myId] = [myDis, myQ]; }
        applySize();
        roleChip();
      },
      onPhase: function () { roleChip(); },
      messages: messages,
      hud: hud,
      prompt: function () {
        if (amProp()) {
          var now = performance.now() / 1000;
          if (now - lastPick > 0.15) { pick = findPick(); lastPick = now; }
          if (pick && pick.k !== myDis) return 'E: become the ' + kindName(pick.k).toLowerCase() + ' · R: turn';
          return 'Look at something and press E to become it · R: turn';
        }
        if (arena.phase === 'setup' && !amHider()) return 'Eyes shut -- the pen opens soon';
        return '';
      },
      thirdPerson: function () { return amProp(); },
      camera: function () {
        if (!amProp()) return null;
        var pos = client.local.pos, sz = size(myDis, myQ);
        var dir = client.lookDirection();
        var pivot = [pos[0], pos[1] + Math.min(4.5, sz.h * 0.6 + 1.2), pos[2]];
        var back = 6 + Math.max(sz.w, sz.h, sz.d) * 1.4;
        var d = back;
        var phys = client.physics;
        if (phys) {
          var bdir = [-dir[0], -dir[1], -dir[2]];
          d = Math.max(2.5, Math.min(back, phys.rayDistance(pivot, bdir, back + 2) - 1.2));
        }
        return { eye: [pivot[0] - dir[0] * d, pivot[1] - dir[1] * d, pivot[2] - dir[2] * d],
                 yaw: client.local.yaw, pitch: client.local.pitch };
      },
      useDown: function (repeat) {
        if (repeat || !amProp()) return false;
        var target = findPick();
        if (!target) {
          client.hud.toast('Look at something to become it');
          return true;
        }
        if (target.k === myDis && target.q === myQ) return true;
        var spotFree = roomFor(target.k, target.q);
        if (!spotFree) {
          client.hud.toast('No room to be a ' + esc(kindName(target.k).toLowerCase()) + ' here', 'bad');
          return true;
        }
        client.local.pos[0] = spotFree[0]; client.local.pos[2] = spotFree[2];
        arena.send('disguise', { i: target.i });
        return true;
      },
      reloadDown: function () {
        if (!amProp()) return false;
        var q = (myQ + 1) % 4;
        if (!roomFor(myDis, q) || (client.physics && client.physics.blocked &&
            client.physics.blocked(client.local.pos[0], client.local.pos[1] + 0.05, client.local.pos[2], null, size(myDis, q)))) {
          client.hud.toast('No room to turn here', 'bad');
          return true;
        }
        myQ = q;
        dis[client.myId] = [myDis, q];
        applySize();
        arena.send('spin');
        return true;
      },
      moveScale: function () {
        if (!amProp()) return 1;
        var k = kinds[myDis];
        var s = k ? (k.speed || 1) : 1;
        if ((arena.me.fast || 0) > 0) s *= 1.6;
        return s;
      },
      canFire: function () { return arena.phase === 'active'; },
      isCustom: function (stats) { return !!(stats && String(stats.kind || '').indexOf('pp_') === 0); },
      localFire: function (stats, origin, dir) {
        var kind = stats.kind;
        if (kind === 'pp_popper') {
          var phys = client.physics;
          var dist = phys ? phys.rayDistance(origin, dir, stats.range || 140) : (stats.range || 140);
          var hitProp = false;
          Object.keys(dis).forEach(function (id) {
            var p = client.players[id];
            if (!p || !p.alive) return;
            var h = hullOf(p.pos, dis[id][0], dis[id][1]);
            var t = rayBox(origin, dir, h[0], h[1]);
            if (t !== null && t < dist + 0.3) { dist = Math.min(dist, t); hitProp = true; }
          });
          decoys.forEach(function (d) {
            var h = hullOf([d[2], d[3], d[4]], d[1], d[5]);
            var t = rayBox(origin, dir, h[0], h[1]);
            if (t !== null && t < dist) dist = t;
          });
          var end = [origin[0] + dir[0] * dist, origin[1] + dir[1] * dist, origin[2] + dir[2] * dist];
          client.tracers.push({ a: origin.slice(), b: end, t: 0, c: rgb(hitProp ? '#ff5a8a' : '#ffd23a') });
          if (client.particles) {
            client.particles.burst('muzzle', [origin[0] + dir[0] * 1.8, origin[1] + dir[1] * 1.8, origin[2] + dir[2] * 1.8]);
            client.particles.burst('impact', end);
          }
          client.audio.play('pp_pop', { volume: 0.7 });
          client.recoil = Math.min(1.4, (client.recoil || 0) + 0.12);
        } else if (kind === 'pp_sniff') {
          if ((arena.me.sniff || 0) > 0) client.hud.toast('The sniffer needs ' + Math.ceil(arena.me.sniff) + 's');
          else client.audio.play('pp_sniff', { volume: 0.6 });
        } else if (kind === 'pp_glitter') {
          if ((arena.me.glitter || 0) <= 0) client.hud.toast('No glitter bombs left', 'bad');
          else client.audio.play('swing', { volume: 0.6 });
        } else if (kind === 'pp_taunt') {
          if ((arena.me.taunt || 0) > 0) client.hud.toast('Taunt again in ' + Math.ceil(arena.me.taunt) + 's');
        } else if (kind === 'pp_decoy') {
          if ((arena.me.decoys || 0) <= 0) client.hud.toast('No decoys left', 'bad');
          else client.hud.toast('Decoy left behind -- now move!', 'good');
        } else if (kind === 'pp_scurry') {
          if ((arena.me.scurry || 0) > 0) client.hud.toast('Scurry again in ' + Math.ceil(arena.me.scurry) + 's');
        }
        return true;
      },
      draw: function (renderer, dt, time) {
        Object.keys(reveals).forEach(function (id) {
          reveals[id].left -= dt;
          if (reveals[id].left <= -0.5) delete reveals[id];
        });
        if (dark > 0) { dark = Math.max(0, dark - dt); if (!dark) setDark(false); }
        if (flicker > 0) flicker = Math.max(0, flicker - dt);
        if (sale.warn > 0) sale.warn = Math.max(0, sale.warn - dt);
        else if (sale.left > 0) sale.left = Math.max(0, sale.left - dt);
        updateVeil();
        // decoys: the real thing, standing where it was left
        decoys.forEach(function (d) { pushParts(renderer, partsOf(d[1], d[5]), [d[2], d[3], d[4]]); });
        // the reveals over the hiders
        Object.keys(dis).forEach(function (id) {
          var pid = parseInt(id, 10);
          var p = pid === client.myId ? { pos: client.local.pos } : client.players[id];
          if (!p) return;
          drawReveal(renderer, id, p.pos, dis[id][0], dis[id][1], time);
        });
        if (cat && catShown) {
          var k = Math.min(1, dt * 8);
          catShown.p[0] += (cat.p[0] - catShown.p[0]) * k;
          catShown.p[1] += (cat.p[1] - catShown.p[1]) * k;
          catShown.p[2] += (cat.p[2] - catShown.p[2]) * k;
          var dy = ((cat.yaw - catShown.yaw + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
          catShown.yaw += dy * k;
          catShown.mode = cat.mode;
          drawCat(renderer, time);
        }
        drawSpot(renderer, time);
        drawFx(renderer, dt);
        // the outline of what E would turn you into
        if (amProp() && pick && pick.k !== myDis) {
          var lo = pick.lo, hi = pick.hi;
          renderer.pushRaw('box', (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2, 0, 0, 0,
                           hi[0] - lo[0] + 0.3, hi[1] - lo[1] + 0.3, hi[2] - lo[2] + 0.3,
                           rgb(accent), 0.18 + Math.sin(time * 6) * 0.06, 0, 3, 0, null);
        }
      },
      avatarParts: function (player, parts, self) {
        var id = self ? client.myId : player.id;
        var mine = dis[id];
        if (!mine || (self ? !amProp() : !isHider(player))) return parts;
        var moving = self ? Math.hypot(client.local.vel[0], client.local.vel[2]) > 2
          : (player.anim === 'walk' || player.anim === 'run');
        var bob = moving ? Math.abs(Math.sin(performance.now() / 1000 * 11 + id)) * 0.35 : 0;
        var out = [];
        pushParts({ push: function (p) { out.push(p); } }, partsOf(mine[0], mine[1]), player.pos, bob);
        return out;
      },
      disguised: function (player) { return isHider(player) && !!dis[player.id]; },
      noPet: function (id) {
        if (id === client.myId) return amHider();
        var p = client.players[id];
        return !!p && isHider(p);
      },
      nameTag: function (player) {
        if (!isHider(player) || !dis[player.id]) return null;
        if (amHider()) return { sub: 'as a ' + kindName(dis[player.id][0]).toLowerCase() };
        if (reveals[player.id]) return { colour: '#ff7a9a', sub: '???' };
        return { hide: true };
      },
      scoreHead: function () {
        return '<th>Player</th><th>Team</th><th>Role</th><th>Found</th><th>Taunts</th><th>Score</th>';
      },
      scoreRow: function (row) {
        var role = row.hider ? (row.out ? 'Found' : 'Hiding') : 'Seeking';
        return '<td>' + esc(arena.teamName(row.team)) + '</td><td>' + role + '</td><td>' + (row.found || 0) +
          '</td><td>' + (row.taunts || 0) + '</td><td>' + row.score + '</td>';
      }
    };
  });

  // ============================================================ sounds
  var GA = global.GameAudio;
  if (GA && GA.register) {
    GA.register('pp_pop', function (vol) {
      this.tone({ type: 'square', freq: 900, freqEnd: 300, dur: 0.08, gain: 0.12 * vol });
      this.noise({ filter: 'highpass', freq: 2400, freqEnd: 900, dur: 0.06, gain: 0.12 * vol });
    });
    GA.register('pp_wrong', function (vol) {
      this.tone({ type: 'sawtooth', freq: 220, freqEnd: 110, dur: 0.35, gain: 0.12 * vol });
      this.later(120, function () { this.tone({ type: 'sawtooth', freq: 180, freqEnd: 90, dur: 0.4, gain: 0.1 * vol }); });
    });
    GA.register('pp_found', function (vol) {
      this.noise({ filter: 'bandpass', freq: 2400, freqEnd: 600, dur: 0.25, gain: 0.25 * vol });
      [523, 659, 784, 1046].forEach(function (f, i) {
        this.later(i * 70, function () { this.tone({ type: 'triangle', freq: f, dur: 0.18, gain: 0.12 * vol }); });
      }, this);
    });
    GA.register('pp_poof', function (vol) {
      this.noise({ filter: 'lowpass', freq: 1800, freqEnd: 200, dur: 0.4, gain: 0.25 * vol });
      this.tone({ type: 'sine', freq: 300, freqEnd: 80, dur: 0.3, gain: 0.1 * vol });
    });
    GA.register('pp_change', function (vol) {
      this.noise({ filter: 'bandpass', freq: 800, freqEnd: 3000, dur: 0.22, gain: 0.16 * vol });
      this.tone({ type: 'sine', freq: 400, freqEnd: 900, dur: 0.2, gain: 0.08 * vol });
    });
    GA.register('pp_sniff', function (vol) {
      for (var i = 0; i < 3; i++) {
        this.later(i * 130, function () {
          this.noise({ filter: 'bandpass', freq: 1600, freqEnd: 2600, dur: 0.1, gain: 0.18 * vol });
        });
      }
    });
    GA.register('pp_squeak', function (vol) {
      this.tone({ type: 'sine', freq: 1400, freqEnd: 2200, dur: 0.12, gain: 0.12 * vol });
      this.later(140, function () { this.tone({ type: 'sine', freq: 1600, freqEnd: 2600, dur: 0.1, gain: 0.1 * vol }); });
    });
    GA.register('pp_honk', function (vol) {
      this.tone({ type: 'square', freq: 330, freqEnd: 300, dur: 0.22, gain: 0.12 * vol });
      this.later(260, function () { this.tone({ type: 'square', freq: 330, freqEnd: 290, dur: 0.3, gain: 0.12 * vol }); });
    });
    GA.register('pp_kazoo', function (vol) {
      this.tone({ type: 'sawtooth', freq: 392, freqEnd: 523, dur: 0.3, gain: 0.08 * vol });
      this.later(320, function () { this.tone({ type: 'sawtooth', freq: 523, freqEnd: 392, dur: 0.4, gain: 0.08 * vol }); });
    });
    GA.register('pp_quack', function (vol) {
      this.tone({ type: 'sawtooth', freq: 600, freqEnd: 300, dur: 0.14, gain: 0.12 * vol });
      this.noise({ filter: 'bandpass', freq: 900, dur: 0.12, gain: 0.08 * vol });
    });
    GA.register('pp_boing', function (vol) {
      this.tone({ type: 'sine', freq: 140, freqEnd: 600, dur: 0.45, gain: 0.16 * vol });
    });
    GA.register('pp_whistle', function (vol) {
      this.tone({ type: 'sine', freq: 1200, freqEnd: 2400, dur: 0.25, gain: 0.1 * vol });
      this.later(300, function () { this.tone({ type: 'sine', freq: 2400, freqEnd: 900, dur: 0.4, gain: 0.1 * vol }); });
    });
    GA.register('pp_toot', function (vol) {
      [392, 523, 659].forEach(function (f, i) {
        this.later(i * 110, function () { this.tone({ type: 'square', freq: f, dur: 0.1, gain: 0.08 * vol }); });
      }, this);
    });
    GA.register('pp_cuckoo', function (vol) {
      this.tone({ type: 'sine', freq: 784, dur: 0.18, gain: 0.14 * vol });
      this.later(240, function () { this.tone({ type: 'sine', freq: 622, dur: 0.3, gain: 0.14 * vol }); });
    });
    GA.register('pp_raspberry', function (vol) {
      this.tone({ type: 'sawtooth', freq: 90, freqEnd: 70, dur: 0.6, gain: 0.12 * vol });
      this.noise({ filter: 'lowpass', freq: 600, dur: 0.6, gain: 0.12 * vol });
    });
    GA.register('pp_release', function (vol) {
      this.tone({ type: 'square', freq: 440, dur: 0.12, gain: 0.1 * vol });
      this.later(150, function () { this.tone({ type: 'square', freq: 660, dur: 0.12, gain: 0.1 * vol }); });
      this.later(300, function () { this.tone({ type: 'square', freq: 880, dur: 0.3, gain: 0.1 * vol }); });
      this.noise({ filter: 'lowpass', freq: 400, freqEnd: 120, dur: 0.9, gain: 0.12 * vol });
    });
    GA.register('pp_creak', function (vol) {
      this.tone({ type: 'sawtooth', freq: 70, freqEnd: 110, dur: 0.9, gain: 0.08 * vol });
      this.noise({ filter: 'bandpass', freq: 500, freqEnd: 300, dur: 0.9, gain: 0.08 * vol });
    });
    GA.register('pp_meow', function (vol) {
      this.tone({ type: 'triangle', freq: 600, freqEnd: 900, dur: 0.18, gain: 0.12 * vol });
      this.later(180, function () { this.tone({ type: 'triangle', freq: 900, freqEnd: 500, dur: 0.35, gain: 0.12 * vol }); });
    });
    GA.register('pp_hiss', function (vol) {
      this.noise({ filter: 'highpass', freq: 3000, freqEnd: 5000, dur: 0.7, gain: 0.18 * vol });
    });
    GA.register('pp_buzz', function (vol) {
      for (var i = 0; i < 5; i++) {
        this.later(i * 140 + (i % 2) * 40, function () {
          this.tone({ type: 'sawtooth', freq: 120, dur: 0.08, gain: 0.1 * vol });
        });
      }
    });
    GA.register('pp_dark', function (vol) {
      this.tone({ type: 'sine', freq: 220, freqEnd: 40, dur: 0.8, gain: 0.16 * vol });
      this.noise({ filter: 'lowpass', freq: 800, freqEnd: 100, dur: 0.6, gain: 0.12 * vol });
    });
    GA.register('pp_chime', function (vol) {
      [659, 523, 784].forEach(function (f, i) {
        this.later(i * 240, function () { this.tone({ type: 'triangle', freq: f, dur: 0.4, gain: 0.12 * vol }); });
      }, this);
    });
    GA.register('pp_alarm', function (vol) {
      for (var i = 0; i < 4; i++) {
        this.later(i * 220, function () {
          this.tone({ type: 'square', freq: 960, freqEnd: 760, dur: 0.2, gain: 0.08 * vol });
        });
      }
    });
    GA.register('pp_glitter', function (vol) {
      for (var i = 0; i < 6; i++) {
        this.later(i * 50, function () {
          this.tone({ type: 'sine', freq: 1800 + Math.random() * 1600, dur: 0.12, gain: 0.05 * vol });
        });
      }
      this.noise({ filter: 'highpass', freq: 4000, dur: 0.4, gain: 0.1 * vol });
    });
    GA.register('pp_whoosh', function (vol) {
      this.noise({ filter: 'bandpass', freq: 400, freqEnd: 2400, dur: 0.35, gain: 0.18 * vol });
    });
  }

  // =================================================== arrival scenes
  var Intro = global.AreaIntro;
  if (!Intro) return;
  var K = Intro.kit;
  var VW = K.VW, VH = K.VH, TAU = K.TAU, HEAVY = K.HEAVY, FONT = K.FONT;
  var seg = K.seg, lerp = K.lerp, outCubic = K.outCubic, outBack = K.outBack, inOut = K.inOut;
  var dot = K.dot, additive = K.additive, roundRect = K.roundRect, fitSize = K.fitSize;
  var between = K.between, rgba = K.rgba, wobble = K.wobble;

  function nameText(ctx, name, x, y, max, colour, shade, font) {
    var size = fitSize(ctx, name, 'bold #px ' + (font || HEAVY), 110, max, 0.04);
    ctx.font = 'bold ' + size + 'px ' + (font || HEAVY);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = shade;
    ctx.fillText(name, x + 4, y + 5);
    ctx.fillStyle = colour;
    ctx.fillText(name, x, y);
    ctx.textAlign = 'left';
    return size;
  }

  /* A teapot in silhouette that blinks: the hider giving itself away. */
  function teapot(ctx, x, y, s, colour, t, blinkAt) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = colour;
    ctx.beginPath(); ctx.ellipse(0, 0, 60, 46, 0, 0, TAU); ctx.fill();
    ctx.fillRect(-26, -58, 52, 14);
    ctx.beginPath(); ctx.arc(0, -64, 9, 0, TAU); ctx.fill();
    ctx.beginPath(); ctx.moveTo(52, -6); ctx.quadraticCurveTo(96, -16, 100, -44); ctx.lineTo(90, -46);
    ctx.quadraticCurveTo(84, -24, 50, 10); ctx.fill();
    ctx.lineWidth = 12; ctx.strokeStyle = colour;
    ctx.beginPath(); ctx.arc(-62, -4, 24, Math.PI * 0.5, Math.PI * 1.5); ctx.stroke();
    var open = t < blinkAt || t > blinkAt + 0.18;
    ctx.fillStyle = '#ffffff';
    if (open) {
      ctx.beginPath(); ctx.ellipse(-16, -6, 9, 12, 0, 0, TAU); ctx.ellipse(16, -6, 9, 12, 0, 0, TAU); ctx.fill();
      ctx.fillStyle = '#1a1a1a';
      var look = Math.sin(t * 2) * 3;
      ctx.beginPath(); ctx.arc(-16 + look, -4, 4.5, 0, TAU); ctx.arc(16 + look, -4, 4.5, 0, TAU); ctx.fill();
    } else {
      ctx.fillRect(-25, -6, 18, 3); ctx.fillRect(7, -6, 18, 3);
    }
    ctx.restore();
  }

  function catSil(ctx, x, y, s, colour, t, walk) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = colour;
    ctx.beginPath(); ctx.ellipse(0, -30, 46, 22, 0, 0, TAU); ctx.fill();
    ctx.beginPath(); ctx.arc(44, -50, 18, 0, TAU); ctx.fill();
    ctx.beginPath(); ctx.moveTo(32, -64); ctx.lineTo(36, -84); ctx.lineTo(44, -66); ctx.fill();
    ctx.beginPath(); ctx.moveTo(48, -66); ctx.lineTo(56, -84); ctx.lineTo(58, -62); ctx.fill();
    for (var i = 0; i < 4; i++) {
      var lx = -30 + i * 20, sw = walk ? Math.sin(t * 9 + i * 1.6) * 8 : 0;
      ctx.fillRect(lx + sw * 0.4, -14, 8, 14);
    }
    ctx.lineWidth = 8; ctx.strokeStyle = colour; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(-44, -36);
    ctx.quadraticCurveTo(-80, -40 + Math.sin(t * 3) * 10, -74, -86); ctx.stroke();
    ctx.fillStyle = '#c8ff6a';
    ctx.beginPath(); ctx.arc(50, -52, 3.5, 0, TAU); ctx.fill();
    ctx.restore();
  }

  // ------------------------------------------------ Grandma's Cottage
  Intro.register('pp_grandma', {
    name: "Grandma's Cottage",
    tagline: 'Tea is at four. Something on the sideboard just blinked.',
    accent: '#e85a7a',
    cues: [[0.3, 'pp_cuckoo', 0.6], [1.1, 'pp_cuckoo', 0.6], [2.2, 'pp_meow', 0.7], [2.9, 'pp_change', 0.7],
           [3.0, 'slam', 0.25]],
    shakes: [[3.0, 4, 0.3]],
    tagY: 640, tagAt: 3.3,
    setup: function (r) {
      var d = { flowers: [], stars: [] };
      for (var i = 0; i < 40; i++) d.flowers.push({ x: between(r, 0, VW), y: between(r, 760, 890), c: ['#e85a8a', '#f2c230', '#c86ad8', '#ffffff'][i % 4], s: between(r, 5, 11) });
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, VH);
      sky.addColorStop(0, '#f6b8a0'); sky.addColorStop(0.5, '#f8d8b0'); sky.addColorStop(1, '#a8d088');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      additive(ctx, function () { dot(ctx, '#fff0c8', 300, 220, 300, 0.5, 200); });
      // the cottage, its windows warm
      ctx.fillStyle = '#efe6d2'; ctx.fillRect(420, 300, 760, 420);
      ctx.fillStyle = '#9a4a3a';
      for (var i = 0; i < 5; i++) ctx.fillRect(400 + i * 40, 300 - (i + 1) * 34, 800 - i * 80, 36);
      ctx.fillStyle = '#5a3a24'; ctx.fillRect(420, 500, 760, 16);
      [[480, 360], [640, 360], [880, 360], [1040, 360], [480, 560], [1040, 560]].forEach(function (w, i) {
        ctx.fillStyle = '#4a7a5a'; ctx.fillRect(w[0] - 18, w[1], 14, 90); ctx.fillRect(w[0] + 84, w[1], 14, 90);
        ctx.fillStyle = 'rgba(255,214,140,' + (0.75 + 0.2 * Math.sin(t * 2 + i)) + ')'; ctx.fillRect(w[0], w[1], 80, 90);
        ctx.fillStyle = '#f4f0e8'; ctx.fillRect(w[0] + 38, w[1], 4, 90); ctx.fillRect(w[0], w[1] + 42, 80, 4);
      });
      ctx.fillStyle = '#7a3a2a'; ctx.fillRect(760, 560, 80, 160);
      ctx.fillStyle = '#9a4f3a'; ctx.fillRect(1120, 120, 50, 200);
      // the picket fence
      ctx.fillStyle = '#5c9c48'; ctx.fillRect(0, 720, VW, VH - 720);
      for (var p = 0; p < 60; p++) {
        ctx.fillStyle = '#f4f0e8';
        ctx.fillRect(p * 28, 690, 16, 70);
        ctx.beginPath(); ctx.moveTo(p * 28, 690); ctx.lineTo(p * 28 + 8, 680); ctx.lineTo(p * 28 + 16, 690); ctx.fill();
      }
      ctx.fillRect(0, 708, VW, 8); ctx.fillRect(0, 740, VW, 8);
      // Mittens walks the fence top
      var cx = lerp(-120, VW + 120, seg(t, 0.3, 4.6));
      catSil(ctx, cx, 680, 0.9, '#2a1a12', t, true);
      d.flowers.forEach(function (f) {
        ctx.fillStyle = f.c; ctx.beginPath(); ctx.arc(f.x, f.y, f.s, 0, TAU); ctx.fill();
      });
      // a teapot on the window sill blinks
      teapot(ctx, 1080, 438, 0.42, '#f4f4f4', t, 2.85);
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || "Grandma's Cottage").toUpperCase();
      // an embroidered sampler unrolls, stitched in rose thread
      var k = outCubic(seg(t, 1.4, 2.2));
      var w = 1040 * k, h = 190;
      ctx.save();
      ctx.translate(800, 250);
      ctx.rotate(wobble(t, 2.2, 0.02, 7, 2.5));
      ctx.fillStyle = '#f4ecd8';
      ctx.fillRect(-w / 2, -h / 2, w, h);
      ctx.strokeStyle = '#e85a7a'; ctx.lineWidth = 4; ctx.setLineDash([10, 8]);
      ctx.strokeRect(-w / 2 + 14, -h / 2 + 14, w - 28, h - 28);
      ctx.setLineDash([]);
      ctx.fillStyle = '#8a5a34'; ctx.fillRect(-w / 2 - 14, -h / 2 - 10, 14, h + 20); ctx.fillRect(w / 2, -h / 2 - 10, 14, h + 20);
      ctx.globalAlpha = run.alpha * seg(t, 2.0, 2.5);
      nameText(ctx, name, 0, 4, Math.max(10, w - 120), '#c83a5a', 'rgba(90,40,40,0.25)', 'Georgia, serif');
      ctx.globalAlpha = run.alpha;
      ctx.restore();
    }
  });

  // ------------------------------------------------ Tinker's Toy Emporium
  Intro.register('pp_toyshop', {
    name: "Tinker's Toy Emporium",
    tagline: 'Everything here is a toy. Nearly.',
    accent: '#f2c230',
    cues: [[0.4, 'pp_toot', 0.6], [1.2, 'pp_boing', 0.6], [2.4, 'pp_boing', 0.8], [2.5, 'slam', 0.3],
           [3.4, 'pp_buzz', 0.5]],
    shakes: [[2.5, 5, 0.35]],
    tagY: 640, tagAt: 3.0,
    setup: function (r) {
      var d = { blocks: [] };
      for (var i = 0; i < 12; i++) d.blocks.push({ x: 120 + i * 120 + between(r, -20, 20), h: Math.floor(between(r, 1, 4)), c: i % 4 });
      return d;
    },
    draw: function (ctx, t, d) {
      var lights = t > 3.4 && t < 3.9 ? 0.25 : 1;
      ctx.fillStyle = '#3a2a5a'; ctx.fillRect(0, 0, VW, VH);
      // the shop window, striped awning
      ctx.fillStyle = '#e8c8a0'; ctx.fillRect(160, 160, 1280, 560);
      for (var s = 0; s < 16; s++) {
        ctx.fillStyle = s % 2 ? '#d8402a' : '#f4f0e8';
        ctx.beginPath(); ctx.moveTo(140 + s * 82, 120); ctx.lineTo(222 + s * 82, 120); ctx.lineTo(222 + s * 82, 190);
        ctx.quadraticCurveTo(181 + s * 82, 220, 140 + s * 82, 190); ctx.fill();
      }
      ctx.fillStyle = 'rgba(255,240,200,' + (0.85 * lights) + ')'; ctx.fillRect(200, 230, 1200, 460);
      // shelves of toys
      var cols = ['#d8402a', '#2f6ad0', '#f2c230', '#3aa04a'];
      d.blocks.forEach(function (b, i) {
        for (var j = 0; j < b.h; j++) {
          ctx.fillStyle = cols[(b.c + j) % 4];
          ctx.fillRect(b.x, 620 - j * 62, 56, 56);
          ctx.fillStyle = 'rgba(255,255,255,0.8)'; ctx.font = 'bold 34px ' + HEAVY; ctx.textAlign = 'center';
          ctx.fillText('ABCD'.charAt((i + j) % 4), b.x + 28, 660 - j * 62);
        }
      });
      ctx.textAlign = 'left';
      // a teddy that turns its head
      ctx.fillStyle = '#a87a4a';
      ctx.beginPath(); ctx.arc(1240, 560, 70, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.arc(1240 + (t > 1.8 ? 14 : 0), 460, 50, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.arc(1200, 420, 18, 0, TAU); ctx.arc(1280, 420, 18, 0, TAU); ctx.fill();
      ctx.fillStyle = '#1a1a1a';
      ctx.beginPath(); ctx.arc(1226 + (t > 1.8 ? 18 : 0), 456, 6, 0, TAU); ctx.arc(1254 + (t > 1.8 ? 18 : 0), 456, 6, 0, TAU); ctx.fill();
      // the jack-in-the-box springs
      var pop = outBack(seg(t, 2.4, 2.8), 2.2);
      ctx.fillStyle = '#8a4ad0'; ctx.fillRect(330, 560, 120, 120);
      ctx.strokeStyle = '#c8c8c8'; ctx.lineWidth = 6;
      ctx.beginPath();
      for (var z = 0; z < 8; z++) ctx.lineTo(390 + (z % 2 ? 18 : -18), 560 - z * 14 * pop);
      ctx.stroke();
      if (pop > 0.05) {
        ctx.fillStyle = '#f2c8a0'; ctx.beginPath(); ctx.arc(390, 560 - 120 * pop, 34 * Math.min(1, pop), 0, TAU); ctx.fill();
        ctx.fillStyle = '#d8402a'; ctx.beginPath(); ctx.arc(390, 556 - 110 * pop, 8, 0, TAU); ctx.fill();
      }
      if (lights < 1) { ctx.fillStyle = 'rgba(0,0,10,0.75)'; ctx.fillRect(0, 0, VW, VH); }
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || "Tinker's Toy Emporium").toUpperCase();
      // letters drop in one at a time like building blocks
      ctx.save();
      var size = fitSize(ctx, name, 'bold #px ' + HEAVY, 96, 1300, 0.04);
      ctx.font = 'bold ' + size + 'px ' + HEAVY;
      var total = ctx.measureText(name).width;
      var x = 800 - total / 2;
      var cols = ['#d8402a', '#2f6ad0', '#f2c230', '#3aa04a', '#8a4ad0'];
      for (var i = 0; i < name.length; i++) {
        var ch = name.charAt(i), w = ctx.measureText(ch).width;
        var at = 1.3 + i * 0.05;
        var k = outBack(seg(t, at, at + 0.35), 1.8);
        var y = lerp(-120, 245, k);
        if (ch !== ' ') {
          ctx.fillStyle = cols[i % cols.length];
          roundRect(ctx, x - 4, y - size * 0.62, w + 8, size * 1.1, 10); ctx.fill();
          ctx.fillStyle = '#ffffff'; ctx.textBaseline = 'middle';
          ctx.fillText(ch, x, y - size * 0.05);
        }
        x += w;
      }
      ctx.restore();
    }
  });

  // ------------------------------------------------ MegaMart
  Intro.register('pp_megamart', {
    name: 'MegaMart',
    tagline: 'Attention shoppers: one of these cereal boxes is a person.',
    accent: '#2ab0a0',
    cues: [[0.3, 'pp_chime', 0.7], [1.6, 'thunk', 0.6], [1.9, 'thunk', 0.6], [2.2, 'thunk', 0.6], [2.25, 'slam', 0.25]],
    shakes: [[2.25, 4, 0.25]],
    tagY: 640, tagAt: 2.7,
    setup: function (r) {
      var d = { items: [] };
      for (var row = 0; row < 3; row++) {
        for (var i = 0; i < 22; i++) {
          d.items.push({ row: row, x: i * 72 + between(r, -4, 4), h: between(r, 40, 70), c: ['#f08a2a', '#d8402a', '#f2c230', '#3a8ad8', '#3aa04a'][(i + row) % 5] });
        }
      }
      return d;
    },
    draw: function (ctx, t, d) {
      ctx.fillStyle = '#e8eef0'; ctx.fillRect(0, 0, VW, VH);
      ctx.fillStyle = '#f4f8f8';
      for (var l = 0; l < 6; l++) ctx.fillRect(l * 300 + 40, 40, 200, 20);
      // the aisle, looking down it
      var pan = -lerp(0, 300, inOut(seg(t, 0, 4.5)));
      for (var row = 0; row < 3; row++) {
        var y = 300 + row * 150;
        ctx.fillStyle = '#c8d0d8'; ctx.fillRect(0, y, VW, 12);
        d.items.forEach(function (it) {
          if (it.row !== row) return;
          var x = it.x + pan;
          ctx.fillStyle = it.c; ctx.fillRect(x, y - it.h, 50, it.h);
          ctx.fillStyle = 'rgba(255,255,255,0.75)'; ctx.fillRect(x + 8, y - it.h + 10, 34, 12);
        });
      }
      ctx.fillStyle = '#b8c0c8'; ctx.fillRect(0, 760, VW, 140);
      // a trolley rolls past
      var tx = lerp(VW + 200, -300, seg(t, 0.6, 3.6));
      ctx.strokeStyle = '#8a9098'; ctx.lineWidth = 6;
      ctx.strokeRect(tx, 640, 180, 110);
      for (var g = 1; g < 6; g++) { ctx.beginPath(); ctx.moveTo(tx + g * 30, 640); ctx.lineTo(tx + g * 30, 750); ctx.stroke(); }
      ctx.fillStyle = '#2a2a2a';
      ctx.beginPath(); ctx.arc(tx + 20, 790, 14, 0, TAU); ctx.arc(tx + 160, 790, 14, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.moveTo(tx + 180, 640); ctx.lineTo(tx + 230, 600); ctx.stroke();
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'MegaMart').toUpperCase();
      // three price-gun stamps: a yellow price label slaps on
      ctx.save();
      ctx.translate(800, 250);
      var hits = [1.6, 1.9, 2.2];
      var k = outBack(seg(t, 2.2, 2.45), 2.0);
      ctx.rotate(-0.04);
      var w = 980, h = 180;
      if (t > hits[0]) {
        ctx.fillStyle = '#f2c230';
        ctx.scale(lerp(1.3, 1, k), lerp(1.3, 1, k));
        roundRect(ctx, -w / 2, -h / 2, w, h, 22); ctx.fill();
        ctx.strokeStyle = '#c82a2a'; ctx.lineWidth = 8; ctx.stroke();
        ctx.fillStyle = '#ffffff';
        ctx.beginPath(); ctx.arc(-w / 2 + 50, 0, 18, 0, TAU); ctx.fill();
        ctx.globalAlpha = run.alpha * seg(t, 1.9, 2.1);
        nameText(ctx, name, 30, 0, w - 180, '#c82a2a', 'rgba(0,0,0,0.2)');
        ctx.globalAlpha = run.alpha * seg(t, 2.2, 2.4);
        ctx.font = 'bold 30px ' + FONT; ctx.fillStyle = '#1b2a35'; ctx.textAlign = 'right';
        ctx.fillText('NOW 99p', w / 2 - 30, h / 2 - 22);
        ctx.textAlign = 'left';
      }
      ctx.restore();
    }
  });

  // ------------------------------------------------ The Museum After Dark
  Intro.register('pp_museum', {
    name: 'The Museum After Dark',
    tagline: 'Closing time. The exhibits are not all where they were.',
    accent: '#8ab0ff',
    cues: [[0.4, 'pp_creak', 0.6], [1.6, 'clang', 0.5], [2.6, 'pp_alarm', 0.5], [2.6, 'slam', 0.2]],
    shakes: [[2.6, 3, 0.3]],
    tagY: 640, tagAt: 3.0,
    setup: function () { return {}; },
    draw: function (ctx, t) {
      ctx.fillStyle = '#0c1020'; ctx.fillRect(0, 0, VW, VH);
      // columns down the hall
      for (var c = 0; c < 6; c++) {
        var x = 100 + c * 280;
        ctx.fillStyle = '#2a3048'; ctx.fillRect(x, 120, 80, 640);
        ctx.fillStyle = '#343c5a'; ctx.fillRect(x - 14, 110, 108, 24); ctx.fillRect(x - 14, 740, 108, 24);
      }
      ctx.fillStyle = '#1a1e30'; ctx.fillRect(0, 760, VW, 140);
      // the dinosaur skeleton
      ctx.strokeStyle = '#8a8070'; ctx.lineWidth = 10; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(500, 520); ctx.quadraticCurveTo(760, 380, 1000, 470); ctx.quadraticCurveTo(1150, 520, 1260, 470); ctx.stroke();
      for (var r = 0; r < 9; r++) {
        ctx.beginPath(); ctx.moveTo(700 + r * 34, 440 + Math.abs(r - 4) * 6); ctx.lineTo(700 + r * 34, 540 - Math.abs(r - 4) * 8); ctx.stroke();
      }
      ctx.beginPath(); ctx.moveTo(760, 540); ctx.lineTo(740, 760); ctx.moveTo(940, 520); ctx.lineTo(960, 760); ctx.stroke();
      ctx.beginPath(); ctx.ellipse(470, 520, 60, 34, -0.3, 0, TAU); ctx.stroke();
      // the suit of armour turns its head
      ctx.fillStyle = '#9aa0aa';
      ctx.fillRect(1350, 520, 70, 120); ctx.fillRect(1340, 640, 34, 120); ctx.fillRect(1396, 640, 34, 120);
      var turn = t > 1.6 ? 12 : 0;
      ctx.fillRect(1362 + turn * 0.4, 460, 46, 56);
      ctx.fillStyle = '#ff3a3a';
      if (t > 1.6) { ctx.fillRect(1372 + turn, 480, 10, 5); ctx.fillRect(1390 + turn, 480, 10, 5); }
      // the searchlight sweeps
      var a = lerp(-0.6, 0.7, (Math.sin(t * 1.1) + 1) / 2);
      additive(ctx, function () {
        ctx.save();
        ctx.translate(800, 40);
        ctx.rotate(a);
        var g = ctx.createLinearGradient(0, 0, 0, 900);
        g.addColorStop(0, 'rgba(255,246,200,0.55)'); g.addColorStop(1, 'rgba(255,246,200,0.05)');
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.moveTo(-20, 0); ctx.lineTo(20, 0); ctx.lineTo(240, 900); ctx.lineTo(-240, 900); ctx.fill();
        ctx.restore();
      });
      if (t > 2.6 && t < 3.8 && Math.floor(t * 6) % 2) { ctx.fillStyle = 'rgba(255,0,0,0.15)'; ctx.fillRect(0, 0, VW, VH); }
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'The Museum After Dark').toUpperCase();
      // a brass exhibit plaque, lit by the sweep
      var k = outCubic(seg(t, 1.2, 1.9));
      ctx.save();
      ctx.translate(800, 245);
      ctx.globalAlpha = run.alpha * k;
      var w = 1100, h = 170;
      var g = ctx.createLinearGradient(-w / 2, 0, w / 2, 0);
      g.addColorStop(0, '#6a4a1a'); g.addColorStop(0.5, '#d8b050'); g.addColorStop(1, '#6a4a1a');
      ctx.fillStyle = g; roundRect(ctx, -w / 2, -h / 2, w, h, 8); ctx.fill();
      ctx.strokeStyle = '#3a2a0a'; ctx.lineWidth = 5; roundRect(ctx, -w / 2 + 12, -h / 2 + 12, w - 24, h - 24, 4); ctx.stroke();
      [[-w / 2 + 26, -h / 2 + 26], [w / 2 - 26, -h / 2 + 26], [-w / 2 + 26, h / 2 - 26], [w / 2 - 26, h / 2 - 26]].forEach(function (p) {
        ctx.fillStyle = '#3a2a0a'; ctx.beginPath(); ctx.arc(p[0], p[1], 7, 0, TAU); ctx.fill();
      });
      nameText(ctx, name, 0, 2, w - 140, '#2a1a06', 'rgba(255,240,180,0.35)', 'Georgia, serif');
      var sweep = ((t * 0.9) % 2) - 0.5;
      additive(ctx, function () { dot(ctx, '#fff6c8', sweep * w, 0, 200, 0.35, 120); });
      ctx.restore();
    }
  });
})(window);
