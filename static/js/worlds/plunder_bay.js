/* Plunder Bay -- the Game View half of the treasure haul
   (app/game/worlds/plunder_bay.py).

   The server owns the treasure, the holds and every cut, shot and shell;
   this shows them.  Treasure lies glinting where it fell -- a pouch, a gold
   bar, a jewel, a chest, the cursed idol -- with a beam of light over a
   live X.  What somebody carries rides above their head (a chest or the
   idol is in their hands, as their kit), and the idol's bearer has a pillar
   of gold over them for everybody to chase.  Tossed treasure flies the arc
   the server worked out; a cannon's shell flies its arc to the ring it is
   going to land in, and so do the lava bombs; the kraken's tentacles
   rise, rear back and slam, and the redcoats march their routes, stop and
   raise their muskets.

   Your own body: treasure slows you (a chest a lot), and so does the sea
   -- wading, more up to your chest.  Stand at your ship's cannon and a
   ring shows where a shell would land; E fires it.

   Four arrival scenes are registered at the bottom. */
(function (global) {
  'use strict';
  var Arena = global.Arena || { register: function () {} };

  var TEAM = { red: '#c8302a', blue: '#2a6ab8' };
  var TEAM_LIGHT = { red: '#ff7a6a', blue: '#7ab8ff' };
  var SHIPS = { red: 'Scarlet Queen', blue: 'Blue Marlin' };
  var KINDS = ['pouch', 'bar', 'gem', 'chest', 'idol'];
  var LOOT = {
    pouch: { name: 'A POUCH OF DOUBLOONS', short: 'POUCH', value: 2, colour: '#e8c040', speed: 1.0 },
    bar: { name: 'A GOLD BAR', short: 'GOLD BAR', value: 4, colour: '#ffd040', speed: 0.95 },
    gem: { name: 'A JEWEL', short: 'JEWEL', value: 6, colour: '#40e0c0', speed: 0.95 },
    chest: { name: 'A CHEST', short: 'CHEST', value: 12, colour: '#d8a050', speed: 0.74 },
    idol: { name: 'THE CURSED IDOL', short: 'THE IDOL', value: 25, colour: '#ffcf30', speed: 0.8 }
  };
  var GEMS = ['#ff3a5a', '#3ae08a', '#3a8aff', '#c05aff'];
  var TWO_HANDS = { chest: 1, idol: 1 };
  var TWISTS = {
    tide: { warn: 'THE TIDE IS TURNING', warnSub: 'The sea is pulling back from the lagoon...',
            on: 'LOW TIDE!', onSub: 'Treasure on the lagoon floor -- grab it before the sea comes back',
            off: 'The tide is in', colour: '#5ad8e8', chip: 'LOW TIDE' },
    kraken: { warn: 'SOMETHING STIRS UNDER THE WRECK', warnSub: 'The water is boiling...',
              on: 'THE KRAKEN!', onSub: 'Stay clear of the rings -- or cut a tentacle down for a jewel',
              off: 'The kraken sinks back into the deep', colour: '#c05aff', chip: 'KRAKEN' },
    redcoats: { warn: 'THE FORT\'S BELL IS RINGING', warnSub: 'The garrison is turning out...',
                on: 'THE REDCOATS!', onSub: 'They shoot any pirate they see -- carriers first',
                off: 'The redcoats march back to the fort', colour: '#ff5a4a', chip: 'REDCOATS' },
    eruption: { warn: 'THE VOLCANO IS RUMBLING', warnSub: 'Get clear of the open ground...',
                on: 'ERUPTION!', onSub: 'Lava bombs -- and gold raining all over the island',
                off: 'The volcano settles', colour: '#ff8a2a', chip: 'ERUPTION' }
  };
  // keep these in step with app/game/worlds/plunder_bay.py
  var GRAVITY = 62, DIG_REACH = 3.6, CANNON_REACH = 5.4;
  var CANNON_MIN = 24, CANNON_MAX = 120, CANNON_ARC = 0.85, CANNON_COOL = 9;
  var BANK_PAD = 1.4, WADE = 0.4, DEEP = 2.8, WADE_SCALE = 0.78, DEEP_SCALE = 0.6;
  var PISTOL_RELOAD = 2.5, DIG_SECONDS = 2.6, RAID_SECONDS = 2.5, EYE = 4.6;

  function rgb(hex) {
    var n = parseInt(String(hex).slice(1), 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
  }
  function esc(text) {
    return String(text == null ? '' : text).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function now() { return performance.now() / 1000; }
  function hash(n) { var x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }
  function flat(a, b) { return Math.hypot(a[0] - b[0], a[2] - b[2]); }
  function wrap(a) { return ((a + Math.PI) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI) - Math.PI; }
  function arcAt(f, t) {
    t = Math.max(0, Math.min(f.T, t));
    return [f.a[0] + f.v[0] * t, f.a[1] + f.v[1] * t - 0.5 * GRAVITY * t * t, f.a[2] + f.v[2] * t];
  }
  function put(r, kind, x, y, z, rx, ry, rz, sx, sy, sz, colour, alpha, material, emissive) {
    r.pushRaw(kind, x, y, z, rx || 0, ry || 0, rz || 0, sx, sy, sz, typeof colour === 'string' ? rgb(colour) : colour,
              alpha === undefined ? 1 : alpha, 0, material || 0, emissive || 0, null);
  }

  /* One piece of treasure at (x, y, z) -- its foot -- turned by yaw, scaled
     by s; ``id`` picks a jewel's colour. */
  function drawLoot(r, kind, x, y, z, yaw, s, id, time) {
    var c = Math.cos(yaw), sn = Math.sin(yaw);
    function at(dx, dz) { return [x + dx * c + dz * sn, z - dx * sn + dz * c]; }
    var p;
    if (kind === 'pouch') {
      put(r, 'sph', x, y + 0.75 * s, z, 0, yaw, 0, 1.6 * s, 1.5 * s, 1.6 * s, '#8a5a30');
      put(r, 'cyl', x, y + 1.5 * s, z, 0, yaw, 0, 0.7 * s, 0.35 * s, 0.7 * s, '#6a4220');
      put(r, 'torus', x, y + 1.45 * s, z, 0, yaw, 0, 0.75 * s, 0.6 * s, 0.75 * s, '#d8b040', 1, 1);
      p = at(0.45 * s, 0.2 * s);
      put(r, 'doubloon', p[0], y + 1.85 * s, p[1], Math.PI / 2 - 0.3, yaw + 0.5, 0, 0.7 * s, 0.7 * s, 0.7 * s, '#ffd040', 1, 1);
      p = at(-0.5 * s, 0.4 * s);
      put(r, 'doubloon', p[0], y + 0.1 * s, p[1], 0, yaw, 0, 0.6 * s, 0.6 * s, 0.6 * s, '#ffd040', 1, 1);
    } else if (kind === 'bar') {
      put(r, 'box', x, y + 0.3 * s, z, 0, yaw, 0, 1.8 * s, 0.6 * s, 0.9 * s, '#ffc830', 1, 1);
      p = at(0.15 * s, 0.05 * s);
      put(r, 'box', p[0], y + 0.85 * s, p[1], 0, yaw + 0.35, 0, 1.6 * s, 0.5 * s, 0.8 * s, '#ffd850', 1, 1);
      put(r, 'box', p[0], y + 1.11 * s, p[1], 0, yaw + 0.35, 0, 1.2 * s, 0.03 * s, 0.5 * s, '#fff0a0', 1, 1, 0.4);
    } else if (kind === 'gem') {
      var hue = GEMS[Math.abs(id || 0) % GEMS.length];
      put(r, 'gem', x, y + 0.2 * s, z, 0, yaw, 0, 1.5 * s, 1.5 * s, 1.5 * s, hue, 0.92, 3, 0.35);
      put(r, 'sph', x, y + 0.8 * s, z, 0, 0, 0, 0.5 * s, 0.5 * s, 0.5 * s, '#ffffff', 0.5, 2, 1);
    } else if (kind === 'chest') {
      put(r, 'box', x, y + 0.55 * s, z, 0, yaw, 0, 2.2 * s, 1.1 * s, 1.5 * s, '#7a4a26');
      put(r, 'box', x, y + 1.32 * s, z, 0, yaw, 0, 2.26 * s, 0.44 * s, 1.56 * s, '#8a5a2e');
      p = at(-0.75 * s, 0);
      put(r, 'box', p[0], y + 0.85 * s, p[1], 0, yaw, 0, 0.18 * s, 1.7 * s, 1.6 * s, '#d8b040', 1, 1);
      p = at(0.75 * s, 0);
      put(r, 'box', p[0], y + 0.85 * s, p[1], 0, yaw, 0, 0.18 * s, 1.7 * s, 1.6 * s, '#d8b040', 1, 1);
      p = at(0, 0.8 * s);
      put(r, 'box', p[0], y + 1.0 * s, p[1], 0, yaw, 0, 0.36 * s, 0.42 * s, 0.08 * s, '#d8b040', 1, 1);
    } else if (kind === 'idol') {
      put(r, 'box', x, y + 0.2 * s, z, 0, yaw, 0, 1.3 * s, 0.4 * s, 1.0 * s, '#b88a20', 1, 1);
      put(r, 'box', x, y + 1.15 * s, z, 0, yaw, 0, 1.0 * s, 1.5 * s, 0.8 * s, '#e8b830', 1, 1);
      put(r, 'box', x, y + 2.35 * s, z, 0, yaw, 0, 1.2 * s, 0.95 * s, 0.95 * s, '#e8b830', 1, 1);
      put(r, 'box', x, y + 2.95 * s, z, 0, yaw, 0, 1.4 * s, 0.2 * s, 1.1 * s, '#c89a20', 1, 1);
      var glow = 0.6 + 0.4 * Math.sin((time || 0) * 5);
      p = at(-0.25 * s, 0.49 * s);
      put(r, 'box', p[0], y + 2.45 * s, p[1], 0, yaw, 0, 0.22 * s, 0.16 * s, 0.04 * s, '#ff2a2a', 1, 2, glow);
      p = at(0.25 * s, 0.49 * s);
      put(r, 'box', p[0], y + 2.45 * s, p[1], 0, yaw, 0, 0.22 * s, 0.16 * s, 0.04 * s, '#ff2a2a', 1, 2, glow);
    }
  }

  Arena.register('plunder_bay', function (arena) {
    var client = arena.client;
    var pb = {};                  // the haul's state: pts, target, twist, on, idol, water
    var ax = {};                  // the snapshot extra: water, carried, flying, actors, npcs
    var ex = {}, pts = {};
    var digs = [], holds = {}, cannons = [], idolMark = null, vent = null;
    var items = {};               // id -> {kind, p, src}
    var liveX = [];
    var flights = {};             // id -> {kind, a, v, T, t0, to}
    var shells = [];              // cannon shells and lava bombs in the air
    var rings = [];               // where something is about to come down
    var npcs = {};                // id -> {kind, p, tp, yaw, state, hp}
    var slams = {};               // tentacle id -> {at, t0, until}
    var aims = {};                // redcoat id -> {target, until}
    var twist = { kind: '', on: false, until: 0 };
    var pistolReady = 0, cannonReady = {}, shakeUntil = 0, shakeK = 0;
    var act = { k: '', start: 0 };
    var lastRole = '', lastSide = '', sideAt = 0, digDust = 0, splashAt = 0;

    function myPos() { return client.local.pos; }
    function inPlay() { return arena.phase === 'active' && !arena.me.out && client.local.alive; }
    function carrying() { return arena.me.carry || ''; }
    function myTeam() { return client.myTeam; }
    function enemyOf(team) { return team === 'red' ? 'blue' : 'red'; }
    function playerPos(id) {
      if (id === client.myId) return myPos();
      var p = client.players[id];
      return p && p.pos ? p.pos : null;
    }
    function nameOf(id) {
      if (id === client.myId) return 'You';
      var p = client.players[id];
      return p ? p.name : 'Somebody';
    }
    function teamOf(id) {
      if (id === client.myId) return client.myTeam;
      var p = client.players[id];
      return p ? p.team : '';
    }
    function playAt(name, pos, vol) {
      var me = myPos();
      var d = pos ? Math.hypot(pos[0] - me[0], pos[1] - me[1], pos[2] - me[2]) : 0;
      var k = Math.max(0, 1 - d / 120);
      if (k > 0.04) client.audio.play(name, { volume: (vol || 1) * k });
    }
    function waterLevel() {
      if (ax.w !== undefined) return ax.w;
      if (pb.water !== undefined) return pb.water;
      return ex.water !== undefined ? ex.water : -1;
    }
    function onHold(team, pos, pad) {
      var h = holds[team];
      return !!h && flat(h.p, pos) < (h.r || 4.2) + pad && Math.abs(pos[1] - h.p[1]) < 3;
    }
    function myCannon() {
      var me = myPos(), team = myTeam();
      for (var i = 0; i < cannons.length; i++) {
        var c = cannons[i];
        if (c.team === team && flat(c.p, me) < CANNON_REACH && Math.abs(me[1] - c.p[1]) < 2.5) return i;
      }
      return -1;
    }
    function digNear() {
      var me = myPos(), best = -1, bestD = DIG_REACH;
      liveX.forEach(function (i) {
        var d = digs[i];
        if (!d) return;
        var dist = flat(d.p, me);
        if (dist < bestD && Math.abs(d.p[1] - me[1]) < 3) { best = i; bestD = dist; }
      });
      return best;
    }

    // ---------------------------------------------------------- the map
    function loadMap(map) {
      var mk = (map && map.markers) || {};
      ex = mk.extra || {};
      pts = mk.points || {};
      digs = (pts.dig || []).slice().sort(function (a, b) { return a.i - b.i; });
      holds = {};
      (pts.hold || []).forEach(function (h) { holds[h.team] = h; });
      cannons = pts.cannon || [];
      idolMark = (pts.idol || [])[0] || null;
      var centre = mk.centre || [0, 0, 0];
      vent = ex.vent ? [ex.vent[0] + centre[0], ex.vent[1], ex.vent[2] + centre[2]] : null;
      reset();
    }

    function reset() {
      ax = {};
      items = {}; liveX = []; flights = {}; shells = []; rings = []; npcs = {}; slams = {}; aims = {};
      twist = { kind: ex.twist || '', on: false, until: 0 };
      pistolReady = 0; cannonReady = {}; shakeUntil = 0;
      act = { k: '', start: 0 };
      lastRole = ''; lastSide = '';
      arena.side('');
      arena.setHold(null);
    }

    function applyState(s) {
      if (!s) return;
      pb = s;
      twist.kind = s.twist || twist.kind;
      twist.on = !!s.on;
      if (s.on && s.left) twist.until = now() + s.left;
      roleChip();
    }

    function takeItems(msg) {
      var fresh = {};
      (msg.it || []).forEach(function (e) {
        fresh[e[0]] = { kind: KINDS[e[1]] || 'pouch', p: [e[2], e[3], e[4]], src: e[5] || 0,
                        born: (items[e[0]] && items[e[0]].born) || now() };
        delete flights[e[0]];
      });
      items = fresh;
      liveX = msg.x || [];
    }

    // ------------------------------------------------- your own body
    function moveScale() {
      var s = 1, kind = carrying();
      if (kind && LOOT[kind]) s *= LOOT[kind].speed;
      var depth = waterLevel() - myPos()[1];
      if (depth > DEEP) s *= DEEP_SCALE;
      else if (depth > WADE) s *= WADE_SCALE;
      return s;
    }

    function afterStep(local, result, dt) {
      // a splash at your feet as you wade
      var t = now(), depth = waterLevel() - local.pos[1];
      if (depth > WADE && depth < 6 && Math.hypot(local.vel[0], local.vel[2]) > 3 && t - splashAt > 0.35 && client.particles) {
        splashAt = t;
        client.particles.burst('dust', [local.pos[0], waterLevel() + 0.1, local.pos[2]], { radius: 1.2 });
      }
    }

    // ---------------------------------------------------------- drawing
    function drawItems(r, time) {
      var w = waterLevel();
      Object.keys(items).forEach(function (key) {
        var it = items[key], p = it.p, id = parseInt(key, 10);
        var bob = it.kind === 'idol' ? 0.6 + Math.sin(time * 1.6) * 0.3 : 0.25 + Math.sin(time * 2.2 + id) * 0.18;
        var spin = it.kind === 'chest' ? hash(id) * 6.28 : time * 0.9 + id;
        var scale = it.kind === 'idol' ? 1.25 : (it.kind === 'chest' ? 1.0 : 1.05);
        drawLoot(r, it.kind, p[0], p[1] + (it.kind === 'chest' ? 0 : bob), p[2], spin, scale, id, time);
        // a glint to find it by, and a pillar of light over the idol
        var glint = 0.5 + 0.5 * Math.sin(time * 3 + id * 1.7);
        put(r, 'cyl', p[0], p[1] + 0.05, p[2], 0, 0, 0, 3.0, 0.04, 3.0, LOOT[it.kind].colour, 0.22 + 0.15 * glint, 2, 0.8);
        if (it.kind === 'idol') {
          put(r, 'cyl', p[0], p[1] + 40, p[2], 0, 0, 0, 2.4, 80, 2.4, '#ffcf30', 0.18, 2, 1);
          if (r.queueTag) r.queueTag('pb_idol', 'THE CURSED IDOL', '#ffcf30', '25 doubloons', [p[0], p[1] + 9, p[2]], 1.2);
        } else if (it.kind === 'chest') {
          put(r, 'cyl', p[0], p[1] + 12, p[2], 0, 0, 0, 1.2, 24, 1.2, '#ffd890', 0.12, 2, 1);
        }
        if (p[1] < w - 0.4 && hash(id + Math.floor(time * 2)) > 0.7 && client.particles) {
          client.particles.spawn({ p: [p[0] + (Math.random() - 0.5), p[1] + 1, p[2] + (Math.random() - 0.5)],
            v: [0, 2.5, 0], life: 1.2, size: 0.3, grow: 0.2, gravity: 0, spin: 0, blend: 'normal', shape: 'spark',
            colors: ['#e0f8ff', '#a0e0ff'] });
        }
      });
    }

    function drawX(r, time) {
      liveX.forEach(function (i) {
        var d = digs[i];
        if (!d) return;
        var p = d.p, pulse = 0.75 + 0.25 * Math.sin(time * 3 + i);
        put(r, 'box', p[0], p[1] + 0.06, p[2], 0, Math.PI / 4, 0, 4.6, 0.06, 0.7, '#c81e1e', 1, 0, 0.3 * pulse);
        put(r, 'box', p[0], p[1] + 0.07, p[2], 0, -Math.PI / 4, 0, 4.6, 0.06, 0.7, '#c81e1e', 1, 0, 0.3 * pulse);
        put(r, 'cyl', p[0], p[1] + 14, p[2], 0, 0, 0, 1.0, 28, 1.0, '#ff5a3a', 0.13 * pulse, 2, 1);
        // a spade stuck in the sand beside it
        put(r, 'box', p[0] + 2.4, p[1] + 1.6, p[2] - 1.2, 0, 0.6, 0.18, 0.18, 3.0, 0.18, '#7a4a28');
        put(r, 'box', p[0] + 2.18, p[1] + 0.25, p[2] - 1.2, 0, 0.6, 0.18, 0.9, 1.0, 0.1, '#8a8e96', 1, 1);
      });
    }

    function drawCarried(r, time) {
      var cr = ax.cr || {};
      Object.keys(cr).forEach(function (key) {
        var id = parseInt(key, 10), kind = KINDS[cr[key]] || 'pouch';
        var pos = playerPos(id);
        if (!pos) return;
        var mine = id === client.myId;
        if (kind === 'idol') {
          // everybody can see who has it
          put(r, 'cyl', pos[0], pos[1] + 46, pos[2], 0, 0, 0, 2.2, 80, 2.2, '#ffcf30', 0.2, 2, 1);
          if (!mine && r.queueTag) r.queueTag('pb_idol_by', nameOf(id).toUpperCase(), '#ffcf30', 'has the idol', [pos[0], pos[1] + 10, pos[2]], 1.2);
          return;
        }
        if (TWO_HANDS[kind]) return;            // in their hands, as their kit
        if (mine && !client.thirdPerson) return;
        drawLoot(r, kind, pos[0], pos[1] + 6.4 + Math.sin(time * 3 + id) * 0.15, pos[2], time * 1.5, 0.6, id, time);
      });
    }

    function drawFlights(r, time) {
      var t = now();
      Object.keys(flights).forEach(function (key) {
        var f = flights[key], id = parseInt(key, 10);
        var age = t - f.t0;
        if (age > f.T + 0.6) { delete flights[key]; return; }
        var p = age >= f.T && f.to ? f.to : arcAt(f, age);
        drawLoot(r, f.kind, p[0], p[1], p[2], time * 6 + id, f.kind === 'chest' ? 0.9 : 0.85, id, time);
        if (client.particles && Math.random() < 0.5) {
          client.particles.spawn({ p: [p[0], p[1] + 0.6, p[2]], v: [0, 0, 0], life: 0.4, size: 0.4, grow: -0.6,
            gravity: 0, spin: 3, blend: 'add', shape: 'spark', colors: ['#fff3b0', '#ffd040'] });
        }
      });
      // anything in the air we never saw leave (joined since)
      (ax.fl || []).forEach(function (e) {
        if (flights[e[0]]) return;
        drawLoot(r, KINDS[e[1]] || 'pouch', e[2], e[3], e[4], time * 6, 0.85, e[0], time);
      });
    }

    function drawShells(r, time) {
      var t = now();
      shells = shells.filter(function (s) { return t - s.t0 < s.T; });
      shells.forEach(function (s, n) {
        var p = arcAt(s, t - s.t0);
        if (s.kind === 'bomb') {
          put(r, 'sph', p[0], p[1], p[2], time * 4, time * 3, 0, 2.2, 2.0, 2.2, '#3a1a10');
          put(r, 'sph', p[0], p[1], p[2], 0, 0, 0, 2.8, 2.8, 2.8, '#ff6a1a', 0.45, 2, 1);
        } else {
          put(r, 'sph', p[0], p[1], p[2], 0, 0, 0, 1.3, 1.3, 1.3, '#2a2a30', 1, 1);
        }
        if (client.particles) {
          client.particles.spawn({ p: p.slice(), v: [(Math.random() - 0.5) * 2, 1, (Math.random() - 0.5) * 2],
            life: s.kind === 'bomb' ? 0.7 : 0.9, size: s.kind === 'bomb' ? 1.4 : 1.0, grow: 1.2, gravity: -2, spin: 2,
            blend: s.kind === 'bomb' ? 'add' : 'normal', shape: s.kind === 'bomb' ? 'flame' : 'smoke',
            colors: s.kind === 'bomb' ? ['#fff0a0', '#ff8a2a', '#c8301a'] : ['#d8d8d8', '#a8a8a8', '#808080'] });
        }
      });
    }

    function drawRings(r, time) {
      var t = now();
      rings = rings.filter(function (g) { return t < g.until + 0.15; });
      rings.forEach(function (g) {
        var left = Math.max(0, g.until - t), span = Math.max(0.1, g.until - g.t0);
        var k = 1 - left / span;
        var colour = g.kind === 'slam' ? '#c05aff' : (g.kind === 'bomb' ? '#ff6a1a' : (TEAM_LIGHT[g.team] || '#ffffff'));
        var pulse = 0.55 + 0.45 * Math.sin(time * (8 + k * 14));
        var d = g.r * 2;
        put(r, 'torus', g.at[0], g.at[1] + 0.25, g.at[2], 0, time, 0, d, 1.4, d, colour, 0.75 * pulse, 2, 1);
        put(r, 'cyl', g.at[0], g.at[1] + 0.12, g.at[2], 0, 0, 0, d * k, 0.05, d * k, colour, 0.35, 2, 0.8);
      });
    }

    function drawNpcs(r, dt, time) {
      var t = now(), w = waterLevel();
      var seen = {};
      (ax.np || []).forEach(function (e) {
        var id = e[0];
        seen[id] = 1;
        var n = npcs[id];
        if (!n) n = npcs[id] = { kind: e[1] ? 'redcoat' : 'tentacle', p: [e[2], e[3], e[4]], yaw: e[5], born: t };
        n.tp = [e[2], e[3], e[4]];
        n.tyaw = e[5];
        n.state = e[6];
        n.hp = e[7];
      });
      Object.keys(npcs).forEach(function (key) {
        var n = npcs[key], id = parseInt(key, 10);
        if (!seen[id]) {
          n.gone = n.gone || t;
          if (t - n.gone > 1.6) { delete npcs[key]; return; }
        }
        var k = Math.min(1, dt * 10);
        if (n.tp) for (var i = 0; i < 3; i++) n.p[i] += (n.tp[i] - n.p[i]) * k;
        if (n.tyaw !== undefined) n.yaw += wrap(n.tyaw - n.yaw) * k;
        if (n.kind === 'tentacle') drawTentacle(r, n, id, time, t, w);
        else drawRedcoat(r, n, id, time, t);
      });
    }

    /* A tentacle: a tapering column of segments out of the water, swaying;
       rearing back before a slam and whipping down onto its ring. */
    function drawTentacle(r, n, id, time, t, w) {
      var base = [n.p[0], w, n.p[2]];
      var rise = Math.min(1, (t - n.born) / 1.5);
      if (n.state === 'sink' || n.gone) rise = Math.max(0, 1 - (t - (n.gone || t)) / 1.4);
      if (n.state === 'sink' && !n.gone) n.gone = t;
      var slam = slams[id];
      var bendX = Math.sin(time * 1.3 + id) * 0.5, bendZ = Math.cos(time * 1.1 + id * 2) * 0.5;
      var reach = 0;
      if (slam && t < slam.until + 0.5) {
        var ux = slam.at[0] - base[0], uz = slam.at[2] - base[2], ul = Math.hypot(ux, uz) || 1;
        ux /= ul; uz /= ul;
        if (t < slam.until) {
          var wind = (t - slam.t0) / Math.max(0.1, slam.until - slam.t0);
          bendX = -ux * 1.4 * wind; bendZ = -uz * 1.4 * wind;
        } else {
          var strike = Math.min(1, (t - slam.until) / 0.18);
          var back = 1 - Math.max(0, (t - slam.until - 0.25) / 0.25);
          reach = Math.min(ul, 20) * strike * Math.max(0, back);
          bendX = ux * 2.2 * strike * Math.max(0, back); bendZ = uz * 2.2 * strike * Math.max(0, back);
        }
      }
      var segs = 11, height = 15 * rise;
      var hurt = n.hp !== undefined && n.hp < 1 ? (1 - n.hp) : 0;
      for (var s = 0; s < segs; s++) {
        var f = s / segs, f2 = (s + 0.5) / segs;
        var curve = f2 * f2;
        var x = base[0] + bendX * curve * 9 + (reach ? (slam.at[0] - base[0]) / (Math.hypot(slam.at[0] - base[0], slam.at[2] - base[2]) || 1) * reach * curve : 0);
        var z = base[2] + bendZ * curve * 9 + (reach ? (slam.at[2] - base[2]) / (Math.hypot(slam.at[0] - base[0], slam.at[2] - base[2]) || 1) * reach * curve : 0);
        var y = base[1] - 1 + height * f2 * (1 - (reach ? 0.75 * curve : 0));
        var rad = (2.6 - 2.0 * f) * (0.6 + 0.4 * rise);
        var colour = s % 2 ? '#7a3a9a' : '#8a4aaa';
        if (hurt > 0.5 && s % 3 === 0) colour = '#a85ab8';
        put(r, 'sph', x, y, z, 0, 0, 0, rad, height / segs * 1.6 + 0.2, rad, colour);
        if (s % 2 === 0 && s < segs - 2) {
          // suckers along the inside of the curl
          put(r, 'sph', x - Math.sin(time + id) * rad * 0.45, y, z - Math.cos(time + id) * rad * 0.45,
              0, 0, 0, rad * 0.32, rad * 0.32, rad * 0.32, '#f0a8c8');
        }
      }
      // the water churning round it
      var ring = 6 + 2 * Math.sin(time * 4 + id);
      put(r, 'torus', base[0], w + 0.1, base[2], 0, time, 0, ring, 0.8, ring, '#e0f8ff', 0.45 * rise, 0, 0.3);
      if (n.hp !== undefined && n.hp < 1 && !n.gone) hpBar(r, [base[0], base[1] + height + 2.4, base[2]], n.hp, '#c05aff');
    }

    /* A redcoat: white breeches, red coat with white cross-belts, a black
       tricorn, his musket shouldered -- or levelled at somebody. */
    function drawRedcoat(r, n, id, time, t) {
      var p = n.p, yaw = n.yaw || 0;
      var fade = n.gone ? Math.max(0, 1 - (t - n.gone) / 1.2) : 1;
      if (fade <= 0) return;
      var down = n.state === 'down' || n.state === 'gone';
      var c = Math.cos(yaw), s = Math.sin(yaw);
      function at(dx, dy, dz) { return [p[0] + dx * c + dz * s, p[1] + dy, p[2] - dx * s + dz * c]; }
      function box(dx, dy, dz, sx, sy, sz, colour, rx, mat) {
        var q = at(dx, dy, dz);
        put(r, 'box', q[0], q[1], q[2], rx || 0, yaw, 0, sx, sy, sz, colour, fade, mat || 0);
      }
      if (down) {
        // fallen flat
        var q0 = at(0, 0.5, -1.4);
        put(r, 'box', q0[0], q0[1], q0[2], Math.PI / 2, yaw, 0, 2.6, 4.2, 1.1, '#c81e1e', fade);
        return;
      }
      var walking = n.state === 'walk';
      var swing = walking ? Math.sin(time * 9 + id) * 0.5 : 0;
      box(-0.55, 1.0, 0, 0.95, 2.0, 1.0, '#f0ece0', swing);
      box(0.55, 1.0, 0, 0.95, 2.0, 1.0, '#f0ece0', -swing);
      box(-0.55, 0.15, 0.1, 1.0, 0.3, 1.3, '#1a1a1a');
      box(0.55, 0.15, 0.1, 1.0, 0.3, 1.3, '#1a1a1a');
      box(0, 3.1, 0, 2.6, 2.3, 1.1, '#c81e1e');
      box(0, 2.0, 0, 2.7, 0.6, 1.15, '#c81e1e');
      box(0, 3.1, 0.58, 0.3, 2.3, 0.04, '#f4f0e0');
      var q = at(0, 3.2, 0.58);
      put(r, 'box', q[0], q[1], q[2], 0, yaw, 0.7, 0.24, 3.0, 0.05, '#f4f0e0', fade);
      put(r, 'box', q[0], q[1], q[2], 0, yaw, -0.7, 0.24, 3.0, 0.05, '#f4f0e0', fade);
      box(0, 4.75, 0, 1.3, 1.2, 1.2, '#f5cd30');
      box(0, 4.95, -0.62, 1.0, 0.5, 0.2, '#e8e8e0');
      q = at(0, 5.4, 0);
      put(r, 'tricorn', q[0], q[1], q[2], 0, yaw, 0, 2.6, 1.6, 2.6, '#1a1a22', fade);
      put(r, 'box', q[0], q[1] + 0.05, q[2], 0, yaw, 0, 1.3, 0.12, 1.25, '#d8b040', fade, 1);
      var aim = aims[id];
      var level = n.state === 'aim' || (aim && aim.until > t);
      if (level) {
        box(0.9, 3.7, 0.9, 0.7, 0.7, 1.8, '#c81e1e');
        box(-0.6, 3.7, 1.1, 0.7, 0.7, 1.6, '#c81e1e');
        var m = at(0.4, 3.95, 2.2);
        put(r, 'box', m[0], m[1], m[2], 0, yaw, 0, 0.3, 0.3, 3.6, '#5a3a22', fade);
        var tip = at(0.4, 4.05, 4.2);
        put(r, 'box', tip[0], tip[1], tip[2], 0, yaw, 0, 0.16, 0.16, 1.2, '#8a8e96', fade, 1);
        if (Math.sin(time * 18) > 0.3) put(r, 'sph', tip[0], tip[1] + 0.1, tip[2], 0, 0, 0, 0.5, 0.5, 0.5, '#fff8d0', 0.8, 2, 1);
      } else {
        box(-1.55, 3.4, 0, 0.7, 2.1, 0.8, '#c81e1e', -swing * 0.6);
        box(1.55, 3.4, 0, 0.7, 2.1, 0.8, '#c81e1e', swing * 0.6);
        var g = at(1.6, 4.6, -0.3);
        put(r, 'box', g[0], g[1], g[2], 0, yaw, 0.12, 0.28, 4.4, 0.28, '#5a3a22', fade);
        put(r, 'box', g[0] + 0.0, g[1] + 2.6, g[2], 0, yaw, 0.12, 0.16, 1.2, 0.16, '#8a8e96', fade, 1);
      }
      if (n.hp !== undefined && n.hp < 1) hpBar(r, [p[0], p[1] + 7.2, p[2]], n.hp, '#ff5a4a');
    }

    function hpBar(r, p, hp, colour) {
      put(r, 'box', p[0], p[1], p[2], 0, 0, 0, 3.0, 0.3, 0.3, '#1a1a1a', 0.7);
      put(r, 'box', p[0] - 1.5 + 1.5 * hp, p[1], p[2], 0, 0, 0, 3.0 * hp, 0.34, 0.34, colour, 0.95, 2, 0.6);
    }

    /* At your own cannon: where a shell would land, as the server will work
       it out -- the point you are looking at, within the gun's arc and
       range -- and the shell's path to it. */
    function drawCannonAim(r, time) {
      if (!inPlay() || carrying()) return;
      var i = myCannon();
      if (i < 0) return;
      var c = cannons[i];
      var local = client.local, cp = Math.cos(local.pitch);
      var dir = [Math.sin(local.yaw) * cp, Math.sin(local.pitch), Math.cos(local.yaw) * cp];
      var eye = [local.pos[0], local.pos[1] + EYE, local.pos[2]];
      var phys = client.physics;
      var hit = phys ? phys.rayDistance(eye, dir, 180) : 180;
      var aim;
      if (hit < 180) aim = [eye[0] + dir[0] * hit, 0, eye[2] + dir[2] * hit];
      else {
        var fl = Math.hypot(dir[0], dir[2]) || 1;
        aim = [c.p[0] + dir[0] / fl * CANNON_MAX, 0, c.p[2] + dir[2] / fl * CANNON_MAX];
      }
      var dx = aim[0] - c.p[0], dz = aim[2] - c.p[2];
      var d = Math.max(CANNON_MIN, Math.min(CANNON_MAX, Math.hypot(dx, dz)));
      var off = Math.max(-CANNON_ARC, Math.min(CANNON_ARC, wrap(Math.atan2(dx, dz) - (c.yaw || 0))));
      var a = (c.yaw || 0) + off;
      var tx = c.p[0] + Math.sin(a) * d, tz = c.p[2] + Math.cos(a) * d;
      var down = phys ? phys.rayDistance([tx, 80, tz], [0, -1, 0], 120) : 80;
      var ty = down < 120 ? 80 - down : waterLevel();
      var ready = (cannonReady[i] || 0) - now();
      var colour = ready > 0 ? '#9a9a9a' : (TEAM_LIGHT[myTeam()] || '#ffffff');
      put(r, 'torus', tx, ty + 0.3, tz, 0, time * 1.5, 0, 15, 1.2, 15, colour, 0.85, 2, 1);
      put(r, 'cyl', tx, ty + 0.15, tz, 0, 0, 0, 2.2, 0.06, 2.2, colour, 0.8, 2, 1);
      // the shell's path, dotted
      var muzzle = [c.p[0] + Math.sin(a) * 4.4, c.p[1] + 2.4, c.p[2] + Math.cos(a) * 4.4];
      var T = 1.1 + d / 95;
      var v = [(tx - muzzle[0]) / T, (ty - muzzle[1] + 0.5 * GRAVITY * T * T) / T, (tz - muzzle[2]) / T];
      var f = { a: muzzle, v: v, T: T };
      for (var k = 1; k < 16; k++) {
        var q = arcAt(f, T * k / 16);
        put(r, 'sph', q[0], q[1], q[2], 0, 0, 0, 0.5, 0.5, 0.5, colour, 0.55, 2, 0.8);
      }
    }

    function drawHolds(r, time) {
      var team = myTeam();
      if (!team || arena.phase !== 'active') return;
      var kind = carrying();
      Object.keys(holds).forEach(function (side) {
        var h = holds[side], mine = side === team;
        var colour = TEAM_LIGHT[side] || '#ffffff';
        var d = ((h.r || 4.2) + BANK_PAD) * 2;
        var pulse = 0.5 + 0.5 * Math.sin(time * 2.5);
        put(r, 'torus', h.p[0], h.p[1] + 0.6, h.p[2], 0, time * 0.4, 0, d, 0.8, d, colour,
            mine && kind ? 0.5 + 0.4 * pulse : 0.25, 2, 1);
        if (mine && kind) {
          put(r, 'cyl', h.p[0], h.p[1] + 30, h.p[2], 0, 0, 0, 3.0, 60, 3.0, colour, 0.14 + 0.08 * pulse, 2, 1);
          var me = myPos();
          var dist = Math.hypot(me[0] - h.p[0], me[2] - h.p[2]);
          if (r.queueTag && dist > 12) {
            r.queueTag('pb_hold', 'YOUR HOLD', colour, Math.round(dist) + ' studs', [h.p[0], h.p[1] + 12, h.p[2]],
                       dist > 80 ? 1.5 : 1.1);
          }
        }
      });
    }

    function drawActors(r, time) {
      var t = now();
      if (t - digDust < 0.12 || !client.particles) return;
      digDust = t;
      (ax.ac || []).forEach(function (e) {
        var pos = playerPos(e[0]);
        if (!pos) return;
        if (e[1] === 0) {
          client.particles.spawn({ p: [pos[0] + (Math.random() - 0.5) * 2, pos[1] + 0.4, pos[2] + (Math.random() - 0.5) * 2],
            v: [(Math.random() - 0.5) * 6, 6 + Math.random() * 4, (Math.random() - 0.5) * 6], life: 0.6, size: 0.45,
            grow: -0.2, gravity: -30, spin: 4, blend: 'normal', shape: 'spark', colors: ['#d8c088', '#b89a60', '#8a6a3a'] });
        } else {
          client.particles.spawn({ p: [pos[0], pos[1] + 2.5, pos[2]], v: [(Math.random() - 0.5) * 3, 4, (Math.random() - 0.5) * 3],
            life: 0.5, size: 0.35, grow: -0.3, gravity: -12, spin: 3, blend: 'add', shape: 'spark', colors: ['#fff3b0', '#ffd040'] });
        }
      });
    }

    function drawVent(r, time) {
      if (!vent || !(twist.on && twist.kind === 'eruption')) return;
      var glow = 0.6 + 0.4 * Math.sin(time * 6);
      put(r, 'sph', vent[0], vent[1] + 2, vent[2], 0, 0, 0, 16, 10, 16, '#ff6a1a', 0.35 * glow, 2, 1);
      if (client.particles && Math.random() < 0.6) {
        client.particles.spawn({ p: [vent[0] + (Math.random() - 0.5) * 8, vent[1] + 2, vent[2] + (Math.random() - 0.5) * 8],
          v: [(Math.random() - 0.5) * 6, 16 + Math.random() * 10, (Math.random() - 0.5) * 6], life: 2.5, size: 4,
          grow: 3, gravity: 2, spin: 1, blend: 'normal', shape: 'smoke', colors: ['#5a4a44', '#3a302c', '#2a2422'] });
        client.particles.spawn({ p: [vent[0], vent[1] + 3, vent[2]], v: [(Math.random() - 0.5) * 14, 20 + Math.random() * 14, (Math.random() - 0.5) * 14],
          life: 1.4, size: 1.2, grow: -0.5, gravity: -24, spin: 3, blend: 'add', shape: 'flame', colors: ['#fff0a0', '#ff8a2a', '#c8301a'] });
      }
    }

    function stepHold() {
      if (!act.k || !inPlay()) { if (act.shown) { arena.setHold(null); act.shown = false; } return; }
      var span = act.k === 'dig' ? DIG_SECONDS : RAID_SECONDS;
      var frac = Math.min(1, (now() - act.start) / span);
      arena.setHold(frac, act.k === 'dig' ? 'DIGGING' : 'ROBBING THEIR HOLD');
      act.shown = true;
    }

    // ------------------------------------------------------------ HUD
    function roleChip() {
      var team = client.myTeam;
      if (!team || !TEAM_LIGHT[team]) { if (lastRole) { arena.setRole(''); lastRole = ''; } return; }
      var bits = [];
      var kind = carrying();
      if (kind && LOOT[kind]) bits.push('<b style="color:' + LOOT[kind].colour + '">CARRYING ' + LOOT[kind].short + '</b>');
      var reload = pistolReady - now();
      if (reload > 0.05) bits.push('<span style="opacity:.8">flintlock loading ' + reload.toFixed(1) + 's</span>');
      if (twist.on && TWISTS[twist.kind]) bits.push('<b style="color:' + TWISTS[twist.kind].colour + '">' + TWISTS[twist.kind].chip + '</b>');
      var html = '<b style="color:' + TEAM_LIGHT[team] + '">' + esc(arena.teamName(team).toUpperCase()) + '</b>' +
        (bits.length ? ' &bull; ' + bits.join(' &bull; ') : '');
      if (html !== lastRole) { arena.setRole(html, team); lastRole = html; }
    }

    function sidePanel() {
      var t = now();
      if (t - sideAt < 0.5) return;
      sideAt = t;
      if (arena.phase !== 'active') { if (lastSide) { arena.side(''); lastSide = ''; } return; }
      var lines = ['<div class="ar-side-h">THE HAUL</div>'];
      var counts = {};
      Object.keys(items).forEach(function (k) { counts[items[k].kind] = (counts[items[k].kind] || 0) + 1; });
      lines.push('<div>X marks the spot: <b>' + liveX.length + '</b></div>');
      lines.push('<div>Loose: ' + ['pouch', 'bar', 'gem', 'chest'].filter(function (k) { return counts[k]; }).map(function (k) {
        return '<b style="color:' + LOOT[k].colour + '">' + counts[k] + '</b> ' + LOOT[k].short.toLowerCase() + (counts[k] > 1 ? 's' : '');
      }).join(', ') + '</div>');
      var idol = pb.idol || 'waiting';
      var line = { waiting: 'not yet risen', altar: 'on its altar!', ground: 'lying loose!', banked: 'banked',
                   carried: 'carried by <b>' + esc(nameOf(pb.idol_by)) + '</b>' }[idol] || '';
      lines.push('<div>The idol: <span style="color:#ffcf30">' + line + '</span></div>');
      var html = lines.join('');
      if (html !== lastSide) { arena.side(html); lastSide = html; }
    }

    function hud(state) {
      roleChip();
      sidePanel();
      var points = pb.pts || {};
      var target = pb.target || 300;
      var out = {
        left: { value: points.red || 0, label: arena.teamName('red'), colour: TEAM_LIGHT.red },
        right: { value: points.blue || 0, label: arena.teamName('blue'), colour: TEAM_LIGHT.blue },
        bars: []
      };
      if (arena.phase === 'setup') {
        out.title = 'MAKE READY';
        out.sub = 'Haul treasure into your ship\'s hold &bull; first crew to <b>' + target + '</b> doubloons';
        return out;
      }
      if (arena.phase !== 'active') return out;
      var kind = carrying();
      var team = myTeam();
      if (kind && LOOT[kind]) {
        out.title = 'CARRYING ' + LOOT[kind].short;
        out.sub = 'Get it into the <b>' + esc(SHIPS[team] || 'ship') + '</b>\'s hold &bull; R tosses it &bull; worth ' + LOOT[kind].value;
      } else if (pb.idol === 'altar' || pb.idol === 'ground') {
        out.title = 'THE IDOL HAS RISEN';
        out.sub = 'Worth <b>25</b> &bull; whoever carries it shines for everybody to see';
      } else if (pb.idol === 'carried') {
        var by = pb.idol_by;
        var ours = teamOf(by) === team;
        out.title = ours ? 'ESCORT THE IDOL' : 'STOP THE IDOL';
        out.sub = '<b>' + esc(nameOf(by)) + '</b> has the cursed idol';
      } else {
        out.title = 'HAUL THE TREASURE';
        out.sub = 'Dig at an X (hold E) &bull; cut down their carriers &bull; ' + liveX.length + ' X' + (liveX.length === 1 ? '' : '\'s') + ' on the map';
      }
      ['red', 'blue'].forEach(function (side) {
        out.bars.push({ label: arena.teamName(side), value: (points[side] || 0) / target, colour: TEAM[side],
                        text: (points[side] || 0) + ' / ' + target });
      });
      if (twist.on && TWISTS[twist.kind]) {
        var left = Math.max(0, twist.until - now());
        out.bars.push({ label: TWISTS[twist.kind].chip, value: Math.min(1, left / 30), colour: TWISTS[twist.kind].colour,
                        text: Math.ceil(left) + 's' });
      }
      return out;
    }

    function prompt() {
      if (!inPlay()) return undefined;
      var me = myPos(), kind = carrying(), team = myTeam();
      if (act.k === 'dig') return 'Digging -- keep holding E';
      if (act.k === 'raid') return 'Robbing their hold -- keep holding E';
      var c = myCannon();
      if (c >= 0 && !kind) {
        var left = (cannonReady[c] || 0) - now();
        return left > 0 ? 'The cannon is loading -- ' + Math.ceil(left) + 's' : 'E: FIRE THE CANNON -- the ring shows where it lands';
      }
      if (kind) {
        if (TWO_HANDS[kind]) return 'Both hands full -- carry it to your hold (R tosses it to a crewmate)';
        return 'Carry it to your ship\'s hold -- R tosses it';
      }
      if (digNear() >= 0) return 'Hold E to dig up the chest';
      if (team && onHold(enemyOf(team), me, 0.6)) return (pb.pts || {})[enemyOf(team)] >= 4 ? 'Hold E to rob their hold' : 'Their hold is empty';
      return '';
    }

    // -------------------------------------------------------- messages
    function blast(msg) {
      var p = msg.p, t = now();
      rings = rings.filter(function (g) { return Math.hypot(g.at[0] - p[0], g.at[2] - p[2]) > 0.5; });
      var me = myPos(), d = Math.hypot(me[0] - p[0], me[1] - p[1], me[2] - p[2]);
      if (d < 50) { shakeUntil = t + 0.5; shakeK = Math.max(0.2, 1 - d / 50); }
      if (msg.w === 'slam') {
        playAt('pb_slam', p, 1);
        if (client.particles) {
          for (var i = 0; i < 24; i++) {
            client.particles.spawn({ p: [p[0], p[1] + 0.5, p[2]], v: [(Math.random() - 0.5) * 18, 8 + Math.random() * 14, (Math.random() - 0.5) * 18],
              life: 0.9, size: 0.8, grow: -0.3, gravity: -40, spin: 2, blend: 'normal', shape: 'spark', colors: ['#e0f8ff', '#a0d8ff', '#ffffff'] });
          }
        }
      } else {
        playAt(msg.w === 'bomb' ? 'pb_bomb' : 'pb_blast', p, 1);
        if (client.particles) {
          client.particles.burst('explosion', [p[0], p[1] + 1, p[2]], { radius: msg.r || 6 });
          for (var j = 0; j < 14; j++) {
            client.particles.spawn({ p: [p[0], p[1] + 1, p[2]], v: [(Math.random() - 0.5) * 16, 10 + Math.random() * 10, (Math.random() - 0.5) * 16],
              life: 1.0, size: 0.6, grow: -0.3, gravity: -40, spin: 4, blend: 'normal', shape: 'spark',
              colors: msg.w === 'bomb' ? ['#ff8a2a', '#3a1a10', '#c8301a'] : ['#d8c088', '#8a6a3a', '#5a4a3a'] });
          }
        }
      }
    }

    var messages = {
      pbs: function (msg) { applyState(msg.s && msg.s.pb); },
      pbi: function (msg) { takeItems(msg); },
      pbx: function (msg) {
        var k = msg.k, me = client.myId, t = now(), info, pos;
        if (k === 'go') {
          client.audio.play('pb_go', { volume: 0.85 });
          arena.banner('HAUL AWAY!', 'First crew to ' + (pb.target || 300) + ' doubloons', 'good', 2600);
        } else if (k === 'pick') {
          pos = (items[msg.id] || {}).p || playerPos(msg.by);
          delete items[msg.id];
          delete flights[msg.id];
          if (msg.by === me) {
            info = LOOT[msg.kind] || {};
            if (msg.kind === 'idol') {
              arena.banner('YOU HAVE THE CURSED IDOL', 'Everybody can see you -- get it home!', 'good', 3200);
              client.audio.play('pb_idol', { volume: 0.8 });
            } else if (TWO_HANDS[msg.kind]) {
              arena.banner(info.name, 'Both hands -- get it home &bull; worth ' + info.value, 'good', 2400);
              client.audio.play('pb_chest', { volume: 0.85 });
            } else {
              client.hud.toast('Picked up ' + (info.name || 'treasure').toLowerCase() + ' (' + info.value + ')', 'good');
              client.audio.play('pb_pick', { volume: 0.8 });
            }
          } else {
            playAt('pb_pick', pos, 0.5);
            if (msg.kind === 'idol') {
              var ours = teamOf(msg.by) === myTeam();
              arena.banner(ours ? 'WE HAVE THE IDOL' : 'THEY HAVE THE IDOL', esc(nameOf(msg.by)) + ' picked it up', ours ? 'good' : 'bad', 2600);
            }
          }
          if (pos && client.particles) client.particles.burst('pickup', [pos[0], pos[1] + 1.5, pos[2]]);
        } else if (k === 'drop') {
          pos = playerPos(msg.by);
          if (msg.by === me) client.hud.toast(msg.why === 'shot' ? 'Shot -- you dropped it!' : 'You dropped it!', 'bad');
          if (pos && client.particles) client.particles.burst('pickup', [pos[0], pos[1] + 2, pos[2]]);
        } else if (k === 'fly') {
          flights[msg.id] = { kind: msg.kind, a: msg.a, v: msg.v, T: msg.T, t0: t, to: msg.to };
          delete items[msg.id];
          playAt('pb_toss', msg.a, 0.7);
        } else if (k === 'catch') {
          if (msg.by === me) {
            arena.banner('GOOD CATCH!', '', 'good', 1600);
            client.audio.play('pb_catch', { volume: 0.8 });
          }
        } else if (k === 'bank') {
          pb.pts = msg.pts || pb.pts;
          var mine = msg.team === myTeam();
          var hold = holds[msg.team];
          if (msg.by === me) {
            arena.banner('BANKED! +' + msg.v, (LOOT[msg.kind] || {}).name || '', 'good', 2200);
            arena.flashScreen('rgba(255,215,90,0.3)', 300);
          } else if (TWO_HANDS[msg.kind]) {
            client.hud.toast(esc(nameOf(msg.by)) + ' banked ' + ((LOOT[msg.kind] || {}).name || 'treasure').toLowerCase() +
                             ' for the ' + esc(arena.teamName(msg.team)), mine ? 'good' : 'bad');
          }
          if (hold) {
            playAt(TWO_HANDS[msg.kind] ? 'pb_bank_big' : 'pb_bank', hold.p, msg.by === me ? 1 : 0.6);
            if (client.particles) client.particles.burst('confetti', [hold.p[0], hold.p[1] + 2, hold.p[2]], { radius: TWO_HANDS[msg.kind] ? 6 : 3 });
          }
        } else if (k === 'lost') {
          playAt('pb_lost', msg.p, 0.8);
          if (client.particles && msg.p) client.particles.burst('explosion', msg.p, { radius: 2 });
        } else if (k === 'x') {
          var d = digs[msg.i];
          if (d) playAt('pb_x', d.p, 0.7);
          client.hud.toast('A new X on the map' + (d && d.name ? ' -- ' + esc(d.name) : ''));
        } else if (k === 'digging') {
          if (msg.id === me) { act.k = 'dig'; act.start = t; }
          playAt('pb_dig', playerPos(msg.id), 0.6);
        } else if (k === 'dug') {
          playAt('pb_dug', msg.p, 0.9);
          if (client.particles) client.particles.burst('confetti', [msg.p[0], msg.p[1] + 1, msg.p[2]], { radius: 3 });
          if (msg.by === me) act.k = '';
        } else if (k === 'raiding') {
          if (msg.id === me) { act.k = 'raid'; act.start = t; }
          if (msg.team === myTeam()) {
            arena.banner('RAIDERS IN OUR HOLD!', esc(nameOf(msg.id)) + ' is robbing the ' + esc(SHIPS[msg.team] || 'ship'), 'bad', 2600);
            client.audio.play('pb_raid', { volume: 0.8 });
          }
        } else if (k === 'raid') {
          pb.pts = msg.pts || pb.pts;
          if (msg.by === me) {
            act.k = '';
            arena.banner('ROBBED THEM!', 'A gold bar of theirs -- get it home', 'good', 2400);
            client.audio.play('pb_pick', { volume: 0.9 });
          } else if (msg.team === myTeam()) {
            arena.banner('WE WERE ROBBED', esc(nameOf(msg.by)) + ' took ' + msg.v + ' out of our hold', 'bad', 2600);
          }
        } else if (k === 'idol') {
          if (msg.s === 'rise') {
            arena.banner('THE CURSED IDOL HAS RISEN', 'Worth 25 &bull; on its altar now', 'area', 3600);
            client.audio.play('pb_idol', { volume: 0.9 });
            arena.flashScreen('rgba(255,200,60,0.25)', 400);
          } else if (msg.s === 'back') {
            client.hud.toast('The idol is back on its altar');
          }
        } else if (k === 'cut') {
          pos = playerPos(msg.id);
          if (msg.id !== me) playAt('pb_cutlass', pos, 0.7);
          if (msg.hit) {
            var hp = playerPos(msg.hit) || ((npcs[msg.hit] || {}).p);
            if (hp) {
              playAt('pb_clang', hp, 0.8);
              if (client.particles) client.particles.burst('impact', [hp[0], hp[1] + 3, hp[2]]);
            }
          }
        } else if (k === 'shot') {
          if (msg.id !== me) {
            client.tracers.push({ a: msg.a, b: msg.b, t: 0, c: rgb('#ffe2a0') });
            playAt('pb_pistol', msg.a, 1);
            if (client.particles) client.particles.burst('muzzle', msg.a);
          }
          if (client.particles) client.particles.burst('impact', msg.b);
        } else if (k === 'cool') {
          pistolReady = t + (msg.s || PISTOL_RELOAD);
        } else if (k === 'cannon') {
          shells.push({ kind: 'shell', a: msg.a, v: msg.v, T: msg.T, t0: t });
          rings.push({ at: msg.at, r: msg.r || 7.5, t0: t, until: t + msg.T, kind: 'shell', team: msg.team });
          playAt('pb_cannon', msg.a, 1);
          if (client.particles) {
            for (var s = 0; s < 10; s++) {
              client.particles.spawn({ p: msg.a.slice(), v: [msg.v[0] * 0.08 + (Math.random() - 0.5) * 4, 2 + Math.random() * 3, msg.v[2] * 0.08 + (Math.random() - 0.5) * 4],
                life: 1.6, size: 2.2, grow: 2.5, gravity: 1, spin: 1, blend: 'normal', shape: 'smoke', colors: ['#e8e8e8', '#b8b8b8', '#888888'] });
            }
          }
          if (msg.by === me) { shakeUntil = t + 0.35; shakeK = 0.8; }
          var mineShell = msg.team === myTeam();
          var me3 = myPos();
          if (!mineShell && Math.hypot(me3[0] - msg.at[0], me3[2] - msg.at[2]) < 30) playAt('pb_whistle', msg.at, 0.9);
        } else if (k === 'cannon_cool') {
          cannonReady[msg.i] = t + (msg.s || CANNON_COOL);
        } else if (k === 'blast') {
          blast(msg);
        } else if (k === 'warn') {
          info = TWISTS[msg.twist] || {};
          arena.banner(info.warn || 'SOMETHING IS COMING', info.warnSub || '', 'bad', 2800);
          client.audio.play('pb_warn', { volume: 0.8 });
        } else if (k === 'twist') {
          info = TWISTS[msg.twist] || {};
          twist.kind = msg.twist || twist.kind;
          twist.on = !!msg.on;
          if (msg.on && msg.left) twist.until = t + msg.left;
          if (msg.on) {
            arena.banner(info.on || 'THE TWIST!', info.onSub || '', 'bad', 3400);
            client.audio.play('pb_twist_' + msg.twist, { volume: 0.9 });
            arena.flashScreen((info.colour || '#ffffff') + '55', 400);
            if (msg.twist === 'eruption' || msg.twist === 'kraken') { shakeUntil = t + 1.2; shakeK = 0.6; }
          } else {
            client.hud.toast(info.off || 'The island settles down');
          }
          roleChip();
        } else if (k === 'tide') {
          playAt('pb_tide', null, 0.8);
        } else if (k === 'uncover') {
          arena.banner('TREASURE ON THE LAGOON FLOOR', 'Grab it before the tide comes back in!', 'good', 2800);
        } else if (k === 'wash') {
          (msg.ids || []).forEach(function (id) { delete items[id]; });
          client.hud.toast('The tide came in and washed the rest away');
        } else if (k === 'bomb') {
          var T = msg['in'] || 1.6;
          shells.push({ kind: 'bomb', a: msg.a, v: [(msg.at[0] - msg.a[0]) / T, (msg.at[1] - msg.a[1] + 0.5 * GRAVITY * T * T) / T,
                                                   (msg.at[2] - msg.a[2]) / T], T: T, t0: t });
          rings.push({ at: msg.at, r: msg.r || 6.5, t0: t, until: t + T, kind: 'bomb' });
          var me4 = myPos();
          if (Math.hypot(me4[0] - msg.at[0], me4[2] - msg.at[2]) < 24) playAt('pb_whistle', msg.at, 0.7);
        } else if (k === 'slam') {
          slams[msg.id] = { at: msg.at, t0: t, until: t + (msg['in'] || 1.4) };
          rings.push({ at: msg.at, r: msg.r || 6, t0: t, until: t + (msg['in'] || 1.4), kind: 'slam' });
          playAt('pb_kraken', msg.at, 0.6);
        } else if (k === 'aim') {
          aims[msg.id] = { target: msg.at, until: t + 1.3 };
          var np = npcs[msg.id];
          if (np) playAt('pb_cock', np.p, 0.8);
          if (msg.at === me) client.hud.toast('A redcoat is aiming at you!', 'bad');
        } else if (k === 'volley') {
          delete aims[msg.id];
          client.tracers.push({ a: msg.a, b: msg.b, t: 0, c: rgb('#fff0c0') });
          playAt('pb_musket', msg.a, 1);
          if (client.particles) {
            client.particles.burst('muzzle', msg.a);
            for (var m = 0; m < 6; m++) {
              client.particles.spawn({ p: msg.a.slice(), v: [(Math.random() - 0.5) * 3, 1 + Math.random() * 2, (Math.random() - 0.5) * 3],
                life: 1.4, size: 1.6, grow: 2, gravity: 0.5, spin: 1, blend: 'normal', shape: 'smoke', colors: ['#f0f0f0', '#c8c8c8'] });
            }
          }
        } else if (k === 'nhit') {
          if (npcs[msg.id]) npcs[msg.id].hp = msg.hp;
        } else if (k === 'ndown') {
          var nd = npcs[msg.id];
          if (nd) { nd.state = msg.kind === 'tentacle' ? 'sink' : 'down'; nd.gone = t; }
          if (msg.by === me) {
            arena.banner(msg.kind === 'tentacle' ? 'TENTACLE SEVERED!' : 'REDCOAT DOWN!',
                         msg.kind === 'tentacle' ? 'It left a jewel behind' : 'He dropped his purse', 'good', 2200);
          }
          if (nd) playAt(msg.kind === 'tentacle' ? 'pb_kraken' : 'pb_clang', nd.p, 0.8);
        } else if (k === 'burn') {
          playAt('pb_lost', msg.p, 1);
          if (msg.id === me) arena.flashScreen('rgba(255,110,30,0.6)', 600);
        }
      }
    };

    // ------------------------------------------------------------ hooks
    return {
      messages: messages,
      onMap: loadMap,
      onArea: function () { arena.setRole(''); reset(); },
      onState: function (state) { applyState(state.pb); },
      onSnapshot: function (msg) { ax = msg.ax || {}; },
      onMe: function (me) {
        var k2 = me.act || '';
        if (k2 !== act.k) {
          act.k = k2;
          var span = k2 === 'dig' ? DIG_SECONDS : RAID_SECONDS;
          act.start = now() - (me.frac || 0) * span;
        }
        roleChip();
      },
      onPhase: function (msg) {
        if (msg.phase === 'setup') { twist.on = false; act.k = ''; roleChip(); }
        if (msg.phase !== 'active') { arena.side(''); lastSide = ''; arena.setHold(null); }
      },
      onEnd: function (msg) {
        twist.on = false;
        act.k = '';
        arena.setHold(null);
        arena.side(''); lastSide = '';
        var team = myTeam();
        if (!team) return;
        if (msg.winner === team) client.hud.toast('Your crew wins the haul!', 'good');
        else if (msg.winner) client.hud.toast('The ' + esc(arena.teamName(msg.winner)) + ' take the haul');
      },
      goLine: function () { return 'Haul the treasure home -- and cut down anybody who tries to take it!'; },
      canFire: function (stats) { return arena.phase === 'active' && !(stats && stats.kind === 'pb_carry'); },
      isCustom: function (stats) { return !!(stats && String(stats.kind || '').indexOf('pb_') === 0); },
      localFire: function (stats, origin, dir) {
        if (stats.kind === 'pb_cutlass') {
          client.audio.play('pb_cutlass', { volume: 0.85 });
          client.recoil = Math.min(1.4, (client.recoil || 0) + 0.5);
          return true;
        }
        if (stats.kind === 'pb_pistol') {
          if (now() < pistolReady) {
            client.hud.toast('Loading the flintlock -- ' + (pistolReady - now()).toFixed(1) + 's');
            client.audio.play('pb_reload', { volume: 0.5 });
            return true;
          }
          var phys = client.physics;
          var dist = phys ? phys.rayDistance(origin, dir, stats.range || 120) : (stats.range || 120);
          var end = [origin[0] + dir[0] * dist, origin[1] + dir[1] * dist, origin[2] + dir[2] * dist];
          client.tracers.push({ a: origin.slice(), b: end, t: 0, c: rgb('#ffe2a0') });
          var muzzle = [origin[0] + dir[0] * 1.8, origin[1] + dir[1] * 1.8, origin[2] + dir[2] * 1.8];
          if (client.particles) {
            client.particles.burst('muzzle', muzzle);
            for (var i = 0; i < 4; i++) {
              client.particles.spawn({ p: muzzle.slice(), v: [dir[0] * 3 + (Math.random() - 0.5), 1 + Math.random(), dir[2] * 3 + (Math.random() - 0.5)],
                life: 1.0, size: 0.9, grow: 1.6, gravity: 0.5, spin: 1, blend: 'normal', shape: 'smoke', colors: ['#f0f0f0', '#c8c8c8'] });
            }
          }
          client.audio.play('pb_pistol', { volume: 1 });
          client.recoil = Math.min(1.6, (client.recoil || 0) + 0.7);
          pistolReady = now() + PISTOL_RELOAD;
          return true;
        }
        return true;
      },
      useDown: function () {
        if (!inPlay()) return false;
        var kind = carrying();
        var c = myCannon();
        if (c >= 0 && !kind) {
          var left = (cannonReady[c] || 0) - now();
          if (left > 0) { client.hud.toast('The cannon is loading -- ' + Math.ceil(left) + 's'); return true; }
          client.audio.play('pb_fuse', { volume: 0.6 });
          return false;
        }
        if (kind) {
          client.hud.toast('Your hands are full -- carry it home, or R to toss it');
          return true;
        }
        var team = myTeam();
        if (digNear() >= 0 || (team && onHold(enemyOf(team), myPos(), 0.6))) return false;
        client.hud.toast('E digs on an X, fires your ship\'s cannon, or robs their hold');
        return true;
      },
      reloadDown: function () {
        if (!inPlay()) return false;
        if (carrying()) {
          var local = client.local, cp = Math.cos(local.pitch);
          arena.send('toss', { d: [Math.sin(local.yaw) * cp, Math.sin(local.pitch), Math.cos(local.yaw) * cp] });
          client.audio.play('pb_toss', { volume: 0.8 });
          return true;
        }
        var reload = pistolReady - now();
        if (reload > 0.05) client.hud.toast('Loading the flintlock -- ' + reload.toFixed(1) + 's');
        return true;
      },
      moveScale: moveScale,
      afterStep: afterStep,
      jolt: function () {
        var left = shakeUntil - now();
        if (left <= 0) return null;
        var k = Math.min(1, left * 2) * shakeK;
        return [Math.sin(now() * 71) * 0.3 * k, Math.cos(now() * 63) * 0.2 * k, 0, Math.sin(now() * 57) * 0.012 * k];
      },
      draw: function (renderer, dt, time) {
        drawItems(renderer, time);
        drawX(renderer, time);
        drawCarried(renderer, time);
        drawFlights(renderer, time);
        drawShells(renderer, time);
        drawRings(renderer, time);
        drawNpcs(renderer, dt, time);
        drawCannonAim(renderer, time);
        drawHolds(renderer, time);
        drawActors(renderer, time);
        drawVent(renderer, time);
        stepHold();
        if (pistolReady > now() - 0.2) roleChip();
      },
      nameTag: function (player) {
        if (arena.phase !== 'active') return null;
        var code = (ax.cr || {})[String(player.id)];
        if (code === undefined) return null;
        var kind = KINDS[code] || 'pouch';
        return { sub: kind === 'idol' ? 'HAS THE IDOL' : 'carrying ' + LOOT[kind].short.toLowerCase(), colour: LOOT[kind].colour };
      },
      hud: hud,
      prompt: prompt,
      scoreHead: function () {
        return '<th>Player</th><th>Crew</th><th>Plunder</th><th>Kills</th><th>Deaths</th><th>Score</th>';
      },
      scoreRow: function (row) {
        return '<td>' + esc(arena.teamName(row.team)) + (row.carry ? ' <b style="color:#ffd040">&bull;</b>' : '') + '</td><td>' +
          (row.plunder || 0) + '</td><td>' + (row.kills || 0) + '</td><td>' + (row.deaths || 0) + '</td><td>' + (row.score || 0) + '</td>';
      },
      introInfo: function () { return { kicker: 'SETTING SAIL FOR' }; }
    };
  });

  // ============================================================ sounds
  var GA = global.GameAudio;
  if (GA && GA.register) {
    GA.register('pb_go', function (vol) {
      [0, 260, 520].forEach(function (ms) {
        this.later(ms, function () {
          this.tone({ type: 'sine', freq: 880, freqEnd: 860, dur: 0.9, gain: 0.12 * vol });
          this.tone({ type: 'sine', freq: 1320, freqEnd: 1300, dur: 0.6, gain: 0.05 * vol });
        });
      }, this);
      this.later(800, function () { this.tone({ type: 'sawtooth', freq: 147, freqEnd: 196, dur: 0.7, gain: 0.08 * vol }); });
    });
    GA.register('pb_cutlass', function (vol) {
      this.noise({ filter: 'bandpass', freq: 2600, freqEnd: 700, dur: 0.16, gain: 0.24 * vol });
      this.tone({ type: 'triangle', freq: 1800, freqEnd: 1500, dur: 0.12, gain: 0.03 * vol });
    });
    GA.register('pb_clang', function (vol) {
      this.tone({ type: 'square', freq: 1240, freqEnd: 1180, dur: 0.22, gain: 0.06 * vol });
      this.tone({ type: 'triangle', freq: 2480, dur: 0.3, gain: 0.04 * vol });
      this.noise({ filter: 'highpass', freq: 3000, dur: 0.05, gain: 0.2 * vol });
    });
    GA.register('pb_pistol', function (vol) {
      this.noise({ filter: 'highpass', freq: 3000, dur: 0.03, gain: 0.25 * vol });
      this.later(30, function () {
        this.noise({ filter: 'lowpass', freq: 1800, freqEnd: 200, dur: 0.5, gain: 0.55 * vol });
        this.tone({ type: 'sine', freq: 110, freqEnd: 40, dur: 0.35, gain: 0.35 * vol });
      });
    });
    GA.register('pb_reload', function (vol) {
      this.noise({ filter: 'bandpass', freq: 3200, dur: 0.03, gain: 0.2 * vol });
      this.later(120, function () { this.noise({ filter: 'bandpass', freq: 2400, dur: 0.04, gain: 0.18 * vol }); });
    });
    GA.register('pb_cock', function (vol) {
      this.noise({ filter: 'bandpass', freq: 2800, dur: 0.04, gain: 0.22 * vol });
      this.later(90, function () { this.noise({ filter: 'bandpass', freq: 1900, dur: 0.05, gain: 0.2 * vol }); });
    });
    GA.register('pb_musket', function (vol) {
      this.noise({ filter: 'lowpass', freq: 2400, freqEnd: 160, dur: 0.7, gain: 0.6 * vol });
      this.tone({ type: 'sine', freq: 95, freqEnd: 35, dur: 0.5, gain: 0.4 * vol });
    });
    GA.register('pb_pick', function (vol) {
      [1568, 2093, 2637].forEach(function (f, i) {
        this.later(i * 45, function () { this.tone({ type: 'triangle', freq: f, dur: 0.12, gain: 0.08 * vol }); });
      }, this);
    });
    GA.register('pb_chest', function (vol) {
      this.tone({ type: 'sine', freq: 90, freqEnd: 60, dur: 0.25, gain: 0.4 * vol });
      this.noise({ filter: 'lowpass', freq: 700, dur: 0.12, gain: 0.25 * vol });
      [1319, 1568, 1976, 2349].forEach(function (f, i) {
        this.later(120 + i * 50, function () { this.tone({ type: 'triangle', freq: f, dur: 0.14, gain: 0.07 * vol }); });
      }, this);
    });
    GA.register('pb_bank', function (vol) {
      for (var i = 0; i < 7; i++) {
        (function (k) {
          this.later(k * 40, function () { this.tone({ type: 'triangle', freq: 1800 + (k % 3) * 400, dur: 0.08, gain: 0.06 * vol }); });
        }).call(this, i);
      }
      this.later(300, function () { this.tone({ type: 'sine', freq: 1046, dur: 0.4, gain: 0.08 * vol }); });
    });
    GA.register('pb_bank_big', function (vol) {
      for (var i = 0; i < 16; i++) {
        (function (k) {
          this.later(k * 35, function () { this.tone({ type: 'triangle', freq: 1500 + ((k * 7) % 5) * 300, dur: 0.09, gain: 0.06 * vol }); });
        }).call(this, i);
      }
      [523, 659, 784, 1046].forEach(function (f, i) {
        this.later(560 + i * 90, function () { this.tone({ type: 'square', freq: f, dur: 0.2, gain: 0.06 * vol }); });
      }, this);
    });
    GA.register('pb_toss', function (vol) {
      this.noise({ filter: 'bandpass', freq: 600, freqEnd: 2000, dur: 0.3, gain: 0.2 * vol });
    });
    GA.register('pb_catch', function (vol) {
      this.tone({ type: 'triangle', freq: 784, dur: 0.1, gain: 0.1 * vol });
      this.later(90, function () { this.tone({ type: 'triangle', freq: 1175, dur: 0.22, gain: 0.1 * vol }); });
    });
    GA.register('pb_dig', function (vol) {
      [0, 420, 840, 1260, 1680, 2100].forEach(function (ms) {
        this.later(ms, function () {
          this.noise({ filter: 'bandpass', freq: 900, freqEnd: 500, dur: 0.18, gain: 0.25 * vol });
          this.noise({ filter: 'highpass', freq: 2600, dur: 0.05, gain: 0.08 * vol });
        });
      }, this);
    });
    GA.register('pb_dug', function (vol) {
      this.tone({ type: 'sine', freq: 70, freqEnd: 50, dur: 0.3, gain: 0.4 * vol });
      this.noise({ filter: 'lowpass', freq: 900, dur: 0.2, gain: 0.3 * vol });
      [784, 988, 1175, 1568].forEach(function (f, i) {
        this.later(200 + i * 70, function () { this.tone({ type: 'triangle', freq: f, dur: 0.18, gain: 0.08 * vol }); });
      }, this);
    });
    GA.register('pb_x', function (vol) {
      this.tone({ type: 'triangle', freq: 660, dur: 0.12, gain: 0.07 * vol });
      this.later(120, function () { this.tone({ type: 'triangle', freq: 990, dur: 0.18, gain: 0.07 * vol }); });
    });
    GA.register('pb_fuse', function (vol) {
      this.noise({ filter: 'highpass', freq: 4000, freqEnd: 6000, dur: 0.25, gain: 0.12 * vol });
    });
    GA.register('pb_cannon', function (vol) {
      this.noise({ filter: 'lowpass', freq: 1200, freqEnd: 90, dur: 1.2, gain: 0.7 * vol });
      this.tone({ type: 'sine', freq: 70, freqEnd: 28, dur: 0.9, gain: 0.55 * vol });
    });
    GA.register('pb_whistle', function (vol) {
      this.tone({ type: 'sine', freq: 1900, freqEnd: 700, dur: 1.1, gain: 0.06 * vol });
    });
    GA.register('pb_blast', function (vol) {
      this.noise({ filter: 'lowpass', freq: 1600, freqEnd: 100, dur: 0.9, gain: 0.7 * vol });
      this.tone({ type: 'sine', freq: 80, freqEnd: 30, dur: 0.6, gain: 0.5 * vol });
    });
    GA.register('pb_bomb', function (vol) {
      this.noise({ filter: 'lowpass', freq: 900, freqEnd: 80, dur: 1.0, gain: 0.6 * vol });
      this.noise({ filter: 'highpass', freq: 3000, freqEnd: 1500, dur: 0.6, gain: 0.12 * vol });
      this.tone({ type: 'sine', freq: 60, freqEnd: 25, dur: 0.7, gain: 0.5 * vol });
    });
    GA.register('pb_slam', function (vol) {
      this.tone({ type: 'sine', freq: 90, freqEnd: 32, dur: 0.6, gain: 0.55 * vol });
      this.noise({ filter: 'lowpass', freq: 2200, freqEnd: 300, dur: 0.8, gain: 0.45 * vol });
      this.later(150, function () { this.noise({ filter: 'bandpass', freq: 1400, freqEnd: 600, dur: 0.9, gain: 0.25 * vol }); });
    });
    GA.register('pb_kraken', function (vol) {
      this.tone({ type: 'sawtooth', freq: 62, freqEnd: 44, dur: 1.4, gain: 0.12 * vol });
      this.tone({ type: 'sine', freq: 48, freqEnd: 40, dur: 1.4, gain: 0.3 * vol });
      this.noise({ filter: 'bandpass', freq: 260, freqEnd: 140, dur: 1.4, gain: 0.25 * vol });
    });
    GA.register('pb_lost', function (vol) {
      this.noise({ filter: 'highpass', freq: 2000, freqEnd: 5000, dur: 0.9, gain: 0.2 * vol });
      this.tone({ type: 'sine', freq: 300, freqEnd: 120, dur: 0.5, gain: 0.1 * vol });
    });
    GA.register('pb_idol', function (vol) {
      [[220, 277, 330], [233, 294, 349]].forEach(function (chord, i) {
        this.later(i * 700, function () {
          chord.forEach(function (f) { this.tone({ type: 'sawtooth', freq: f, dur: 0.9, gain: 0.03 * vol }); }, this);
        });
      }, this);
      this.noise({ filter: 'bandpass', freq: 500, freqEnd: 300, dur: 1.6, gain: 0.08 * vol });
    });
    GA.register('pb_raid', function (vol) {
      for (var i = 0; i < 8; i++) {
        (function (k) {
          this.later(k * 140, function () { this.tone({ type: 'triangle', freq: 1320, freqEnd: 1290, dur: 0.12, gain: 0.1 * vol }); });
        }).call(this, i);
      }
    });
    GA.register('pb_warn', function (vol) {
      [0, 500, 1000].forEach(function (ms) {
        this.later(ms, function () {
          this.tone({ type: 'sine', freq: 660, freqEnd: 650, dur: 0.6, gain: 0.12 * vol });
          this.tone({ type: 'sine', freq: 990, freqEnd: 980, dur: 0.4, gain: 0.04 * vol });
        });
      }, this);
    });
    GA.register('pb_tide', function (vol) {
      this.noise({ filter: 'lowpass', freq: 600, freqEnd: 200, dur: 2.2, gain: 0.3 * vol });
      this.noise({ filter: 'highpass', freq: 2500, freqEnd: 1200, dur: 1.6, gain: 0.08 * vol });
    });
    GA.register('pb_twist_tide', function (vol) {
      this.noise({ filter: 'lowpass', freq: 900, freqEnd: 150, dur: 2.4, gain: 0.35 * vol });
      this.tone({ type: 'sine', freq: 330, freqEnd: 220, dur: 1.4, gain: 0.05 * vol });
    });
    GA.register('pb_twist_kraken', function (vol) {
      this.tone({ type: 'sawtooth', freq: 55, freqEnd: 36, dur: 2.0, gain: 0.16 * vol });
      this.tone({ type: 'sine', freq: 41, dur: 2.0, gain: 0.35 * vol });
      this.noise({ filter: 'lowpass', freq: 500, freqEnd: 120, dur: 2.0, gain: 0.35 * vol });
    });
    GA.register('pb_twist_redcoats', function (vol) {
      for (var i = 0; i < 12; i++) {
        (function (k) {
          this.later(k * 95, function () { this.noise({ filter: 'bandpass', freq: 220, dur: 0.06, gain: (k % 4 === 0 ? 0.45 : 0.25) * vol }); });
        }).call(this, i);
      }
      [523, 659, 784, 1046].forEach(function (f, i) {
        this.later(1150 + i * 120, function () { this.tone({ type: 'square', freq: f, dur: 0.16, gain: 0.05 * vol }); });
      }, this);
    });
    GA.register('pb_twist_eruption', function (vol) {
      this.noise({ filter: 'lowpass', freq: 400, freqEnd: 60, dur: 2.4, gain: 0.7 * vol });
      this.tone({ type: 'sine', freq: 40, freqEnd: 24, dur: 2.0, gain: 0.5 * vol });
      this.later(500, function () { this.noise({ filter: 'lowpass', freq: 1400, freqEnd: 200, dur: 1.4, gain: 0.4 * vol }); });
    });
    // for the arrival scenes
    GA.register('pb_waves', function (vol) {
      this.noise({ filter: 'lowpass', freq: 500, freqEnd: 900, dur: 1.4, gain: 0.2 * vol });
      this.later(1400, function () { this.noise({ filter: 'lowpass', freq: 900, freqEnd: 300, dur: 1.6, gain: 0.18 * vol }); });
    });
    GA.register('pb_gull', function (vol) {
      [0, 260, 480].forEach(function (ms, i) {
        this.later(ms, function () { this.tone({ type: 'sine', freq: 1500 - i * 80, freqEnd: 1100 - i * 80, dur: 0.22, gain: 0.05 * vol }); });
      }, this);
    });
    GA.register('pb_drum', function (vol) {
      for (var i = 0; i < 16; i++) {
        (function (k) {
          this.later(k * 110, function () { this.noise({ filter: 'bandpass', freq: 240, dur: 0.05, gain: (k % 4 === 0 ? 0.4 : 0.2) * vol }); });
        }).call(this, i);
      }
    });
    GA.register('pb_coins', function (vol) {
      for (var i = 0; i < 12; i++) {
        (function (k) {
          this.later(k * 55 + (k % 3) * 12, function () { this.tone({ type: 'triangle', freq: 2000 + ((k * 5) % 7) * 220, dur: 0.07, gain: 0.05 * vol }); });
        }).call(this, i);
      }
    });
    GA.register('pb_rumble', function (vol) {
      this.noise({ filter: 'lowpass', freq: 240, freqEnd: 90, dur: 1.6, gain: 0.5 * vol });
      this.tone({ type: 'sine', freq: 36, dur: 1.4, gain: 0.35 * vol });
    });
  }

  // =================================================== arrival scenes
  var Intro = global.AreaIntro;
  if (!Intro) return;
  var K = Intro.kit;
  var VW = K.VW, VH = K.VH, TAU = K.TAU, HEAVY = K.HEAVY;
  var seg = K.seg, lerp = K.lerp, outCubic = K.outCubic, outBack = K.outBack;
  var dot = K.dot, additive = K.additive, roundRect = K.roundRect, fitSize = K.fitSize;
  var between = K.between, wobble = K.wobble, makeStars = K.makeStars, stars = K.stars;
  var SKIN = '#f5cd30', TORSO = '#c4281c', LEGS = '#0d69ac';

  /* A pirate in the classic colours -- yellow head and arms, red torso,
     blue legs -- in a black tricorn with a red sash, a cutlass in hand;
     (x, y) is the feet.  ``pose`` 0 walks, 1 raises the cutlass, 2 digs. */
  function pirate(ctx, x, y, s, t, phase, pose, face) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s * (face || 1), s);
    var swing = pose === 0 ? Math.sin(t * 9 + phase) * 0.6 : 0;
    function limb(px, py, w, h, ang, colour) {
      ctx.save(); ctx.translate(px, py); ctx.rotate(ang);
      ctx.fillStyle = colour; ctx.fillRect(-w / 2, 0, w, h);
      ctx.restore();
    }
    limb(-7, -40, 13, 40, swing, LEGS);
    limb(7, -40, 13, 40, -swing, LEGS);
    ctx.fillStyle = '#1a1a1a'; ctx.fillRect(-14, -4, 13, 5); ctx.fillRect(1, -4, 13, 5);
    limb(-21, -79, 11, 37, pose === 2 ? -0.6 + Math.sin(t * 8) * 0.5 : -swing * 0.8, SKIN);
    ctx.fillStyle = TORSO; ctx.fillRect(-15, -81, 30, 43);
    ctx.fillStyle = '#1a1a1a'; ctx.fillRect(-15, -48, 30, 6);
    ctx.fillStyle = '#e8b830'; ctx.fillRect(-4, -48, 8, 6);
    var arm = pose === 1 ? -2.6 + Math.sin(t * 6) * 0.25 : (pose === 2 ? -0.4 + Math.sin(t * 8) * 0.5 : swing * 0.8);
    ctx.save(); ctx.translate(21, -79); ctx.rotate(arm);
    ctx.fillStyle = SKIN; ctx.fillRect(-5.5, 0, 11, 37);
    if (pose === 2) {
      // a spade
      ctx.fillStyle = '#7a4a28'; ctx.fillRect(-2, 30, 4, 46);
      ctx.fillStyle = '#9aa0a8'; ctx.beginPath(); ctx.moveTo(-9, 74); ctx.lineTo(9, 74); ctx.lineTo(6, 92); ctx.lineTo(-6, 92); ctx.fill();
    } else {
      // a cutlass, its guard gold
      ctx.fillStyle = '#e8b830'; ctx.fillRect(-7, 34, 14, 4);
      ctx.fillStyle = '#e8ecf0';
      ctx.beginPath(); ctx.moveTo(-3, 38); ctx.quadraticCurveTo(6, 60, 2, 82); ctx.lineTo(-3, 80); ctx.quadraticCurveTo(0, 60, -6, 38); ctx.fill();
    }
    ctx.restore();
    ctx.fillStyle = SKIN; roundRect(ctx, -12, -107, 24, 25, 6); ctx.fill();
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(-6, -99, 3, 5);
    ctx.fillRect(1, -101, 9, 7);
    ctx.fillRect(-12, -101, 24, 2);
    ctx.strokeStyle = '#1a1a1a'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(1, -91, 5, 0.25, Math.PI - 0.25); ctx.stroke();
    // the tricorn
    ctx.fillStyle = '#1a1a22';
    ctx.beginPath(); ctx.moveTo(-22, -106); ctx.quadraticCurveTo(0, -128, 22, -106); ctx.quadraticCurveTo(0, -114, -22, -106); ctx.fill();
    ctx.fillRect(-11, -118, 22, 10);
    ctx.fillStyle = '#e8b830'; ctx.fillRect(-11, -110, 22, 2);
    ctx.restore();
  }

  /* A galleon side on: hull in its crew's colours, three masts and sails,
     a Jolly Roger at the top.  (x, y) is the waterline's middle. */
  function galleon(ctx, x, y, s, sail, stripe, t, face) {
    ctx.save();
    ctx.translate(x, y + Math.sin(t * 1.4) * 4 * s);
    ctx.rotate(Math.sin(t * 1.1) * 0.02);
    ctx.scale(s * (face || 1), s);
    ctx.fillStyle = '#5a3a20';
    ctx.beginPath(); ctx.moveTo(-200, -60); ctx.lineTo(180, -60); ctx.lineTo(230, -90); ctx.lineTo(200, 0); ctx.lineTo(-170, 0); ctx.lineTo(-210, -80); ctx.closePath(); ctx.fill();
    ctx.fillStyle = stripe; ctx.fillRect(-195, -46, 385, 10);
    ctx.fillStyle = '#3a2412'; ctx.fillRect(-210, -110, 70, 50);
    ctx.fillStyle = '#ffd890';
    for (var w = 0; w < 6; w++) ctx.fillRect(-120 + w * 50, -32, 14, 10);
    [[-120, 210], [0, 260], [120, 200]].forEach(function (m, i) {
      ctx.fillStyle = '#3a2412'; ctx.fillRect(m[0] - 4, -60 - m[1], 8, m[1]);
      for (var k = 0; k < 2; k++) {
        var top = -60 - m[1] + 20 + k * (m[1] * 0.42), h = m[1] * 0.36, wd = 120 - k * 10 - i * 8;
        ctx.fillStyle = sail;
        ctx.beginPath(); ctx.moveTo(m[0] - wd / 2, top); ctx.lineTo(m[0] + wd / 2, top);
        ctx.quadraticCurveTo(m[0] + wd / 2 + 14 + Math.sin(t * 2 + i) * 4, top + h / 2, m[0] + wd / 2, top + h);
        ctx.lineTo(m[0] - wd / 2, top + h);
        ctx.quadraticCurveTo(m[0] - wd / 2 + 14 + Math.sin(t * 2 + i) * 4, top + h / 2, m[0] - wd / 2, top); ctx.fill();
      }
    });
    // the Jolly Roger
    ctx.fillStyle = '#111';
    var fl = Math.sin(t * 5) * 6;
    ctx.beginPath(); ctx.moveTo(4, -320); ctx.lineTo(70, -316 + fl); ctx.lineTo(70, -276 + fl); ctx.lineTo(4, -280); ctx.fill();
    ctx.fillStyle = '#f4f0e0';
    ctx.beginPath(); ctx.arc(37, -302 + fl / 2, 9, 0, TAU); ctx.fill();
    ctx.fillRect(25, -290 + fl / 2, 24, 3);
    ctx.restore();
  }

  function palm(ctx, x, y, h, lean, t, colour) {
    ctx.save();
    ctx.translate(x, y);
    ctx.strokeStyle = '#6a4a2a'; ctx.lineWidth = 14; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(lean * 0.4, -h * 0.6, lean, -h); ctx.stroke();
    ctx.fillStyle = colour || '#2a7a3a';
    for (var f = 0; f < 7; f++) {
      var a = -Math.PI / 2 + (f - 3) * 0.55 + Math.sin(t * 1.5 + f) * 0.05;
      ctx.save(); ctx.translate(lean, -h); ctx.rotate(a);
      ctx.beginPath(); ctx.moveTo(0, -6); ctx.quadraticCurveTo(60, -30, 120, 10); ctx.quadraticCurveTo(60, -6, 0, 6); ctx.fill();
      ctx.restore();
    }
    ctx.fillStyle = '#5a3a1a';
    ctx.beginPath(); ctx.arc(lean - 8, -h + 8, 7, 0, TAU); ctx.arc(lean + 8, -h + 10, 7, 0, TAU); ctx.fill();
    ctx.restore();
  }

  function waves(ctx, y, colour, t, amp, speed, alpha) {
    ctx.fillStyle = colour;
    ctx.globalAlpha = alpha === undefined ? 1 : alpha;
    ctx.beginPath(); ctx.moveTo(0, VH);
    for (var x = 0; x <= VW; x += 20) ctx.lineTo(x, y + Math.sin(x * 0.012 + t * speed) * amp + Math.sin(x * 0.031 - t * speed * 1.3) * amp * 0.4);
    ctx.lineTo(VW, VH); ctx.closePath(); ctx.fill();
    ctx.globalAlpha = 1;
  }

  function coin(ctx, x, y, r, spin) {
    var w = Math.abs(Math.cos(spin)) * r;
    ctx.fillStyle = '#b88a20';
    ctx.beginPath(); ctx.ellipse(x, y, Math.max(1, w), r, 0, 0, TAU); ctx.fill();
    ctx.fillStyle = '#ffd040';
    ctx.beginPath(); ctx.ellipse(x, y, Math.max(0.5, w * 0.78), r * 0.78, 0, 0, TAU); ctx.fill();
  }

  function titleText(ctx, text, x, y, max, size0, fill, stroke, lw, font) {
    var size = fitSize(ctx, text, 'bold #px ' + (font || HEAVY), size0 || 110, max, 0.04);
    ctx.font = 'bold ' + size + 'px ' + (font || HEAVY);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round';
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw || 10; ctx.strokeText(text, x, y); }
    ctx.fillStyle = fill;
    ctx.fillText(text, x, y);
    ctx.textAlign = 'left';
    return size;
  }

  /* A parchment sheet, its edges a little ragged. */
  function parchment(ctx, w, h, seed) {
    ctx.fillStyle = '#e8d8a8';
    ctx.beginPath();
    for (var i = 0; i <= 40; i++) {
      var f = i / 40;
      var jag = (hash(seed + i) - 0.5) * 8;
      if (i <= 10) ctx.lineTo(-w / 2 + f * 4 * w, -h / 2 + jag);
      else if (i <= 20) ctx.lineTo(w / 2 + jag, -h / 2 + (f - 0.25) * 4 * h);
      else if (i <= 30) ctx.lineTo(w / 2 - (f - 0.5) * 4 * w, h / 2 + jag);
      else ctx.lineTo(-w / 2 + jag, h / 2 - (f - 0.75) * 4 * h);
    }
    ctx.closePath(); ctx.fill();
    ctx.strokeStyle = 'rgba(120,80,40,0.5)'; ctx.lineWidth = 3; ctx.stroke();
    var g = ctx.createRadialGradient(0, 0, Math.min(w, h) * 0.2, 0, 0, Math.max(w, h) * 0.65);
    g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(110,70,20,0.35)');
    ctx.fillStyle = g; ctx.fillRect(-w / 2, -h / 2, w, h);
  }

  // ------------------------------------------------ Skull Cove
  Intro.register('pb_skullcove', {
    name: 'Skull Cove',
    tagline: 'Dig where X marks the spot. When the tide goes out, the lagoon is gold.',
    accent: '#e8b830',
    cues: [[0.2, 'pb_waves', 0.7], [0.8, 'pb_gull', 0.6], [1.6, 'pb_tide', 0.6], [2.4, 'pb_dig', 0.6],
           [3.5, 'pb_dug', 0.8], [4.4, 'pb_go', 0.6]],
    shakes: [],
    tagY: 600, tagAt: 3.3,
    setup: function (r) {
      var d = { gulls: [], glints: [], sand: [] };
      for (var i = 0; i < 6; i++) d.gulls.push([between(r, 0, VW), between(r, 120, 300), between(r, 30, 70), r() * 6]);
      for (var g = 0; g < 30; g++) d.glints.push([between(r, 0, VW), between(r, 530, 660), r() * 6]);
      for (var s = 0; s < 40; s++) d.sand.push([between(r, -1, 1), between(r, 0.4, 1), r() * 2]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, VH);
      sky.addColorStop(0, '#2a3a7a'); sky.addColorStop(0.45, '#e8806a'); sky.addColorStop(0.65, '#ffcf8a'); sky.addColorStop(1, '#ffe8b0');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      dot(ctx, '#ffe8a0', 800, 440, 260, 0.7);
      ctx.fillStyle = '#ffd890'; ctx.beginPath(); ctx.arc(800, 440, 70, 0, TAU); ctx.fill();
      // the cliffs, and the skull between them
      ctx.fillStyle = '#5a4a44';
      ctx.beginPath(); ctx.moveTo(0, 520); ctx.lineTo(0, 290); ctx.lineTo(160, 250); ctx.lineTo(420, 320); ctx.lineTo(560, 400); ctx.lineTo(560, 520); ctx.fill();
      ctx.beginPath(); ctx.moveTo(VW, 520); ctx.lineTo(VW, 280); ctx.lineTo(1440, 240); ctx.lineTo(1180, 320); ctx.lineTo(1040, 400); ctx.lineTo(1040, 520); ctx.fill();
      ctx.fillStyle = '#3a7a3a';
      ctx.beginPath(); ctx.moveTo(0, 290); ctx.lineTo(160, 250); ctx.lineTo(420, 320); ctx.lineTo(420, 340); ctx.lineTo(160, 275); ctx.lineTo(0, 310); ctx.fill();
      ctx.beginPath(); ctx.moveTo(VW, 280); ctx.lineTo(1440, 240); ctx.lineTo(1180, 320); ctx.lineTo(1180, 340); ctx.lineTo(1440, 265); ctx.lineTo(VW, 300); ctx.fill();
      ctx.strokeStyle = '#2f6a2f'; ctx.lineWidth = 4;
      [[90, 268, 70], [250, 262, 90], [360, 300, 60], [1220, 312, 80], [1360, 252, 100], [1510, 262, 70]].forEach(function (v) {
        ctx.beginPath(); ctx.moveTo(v[0], v[1]); ctx.quadraticCurveTo(v[0] + 6, v[1] + v[2] / 2, v[0] - 2, v[1] + v[2]); ctx.stroke();
      });
      ctx.fillStyle = '#d8cfb8';
      ctx.beginPath(); ctx.ellipse(800, 320, 230, 200, 0, Math.PI, 0); ctx.lineTo(1000, 500); ctx.lineTo(600, 500); ctx.fill();
      ctx.fillStyle = '#b8ae96'; ctx.fillRect(660, 420, 280, 90);
      ctx.fillStyle = '#2a2420';
      ctx.beginPath(); ctx.ellipse(725, 320, 52, 46, 0, 0, TAU); ctx.ellipse(875, 320, 52, 46, 0, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.moveTo(800, 370); ctx.lineTo(780, 410); ctx.lineTo(820, 410); ctx.fill();
      ctx.beginPath(); ctx.ellipse(800, 490, 90, 60, 0, Math.PI, 0); ctx.fill();
      ctx.fillStyle = '#f0e8d8';
      for (var tooth = 0; tooth < 5; tooth++) ctx.fillRect(728 + tooth * 30, 432, 22, 18);
      var eyes = seg(t, 1.0, 1.6);
      if (eyes > 0) {
        additive(ctx, function () {
          dot(ctx, '#ff2a1a', 725, 320, 46, eyes * (0.7 + 0.3 * Math.sin(t * 6)));
          dot(ctx, '#ff2a1a', 875, 320, 46, eyes * (0.7 + 0.3 * Math.sin(t * 6 + 1)));
        });
      }
      // the lagoon, the tide falling out of it
      var tide = seg(t, 1.6, 2.8);
      var waterY = 520 + tide * 64;
      ctx.fillStyle = '#d8c088'; ctx.fillRect(0, 520, VW, 380);
      if (tide > 0.5) {
        for (var c = 0; c < 6; c++) coin(ctx, 520 + c * 110, 566 + (c % 2) * 6, 9, t * 3 + c);
        ctx.fillStyle = '#7a4a26'; ctx.fillRect(760, 548, 70, 34);
        ctx.fillStyle = '#d8b040'; ctx.fillRect(760, 548, 70, 8); ctx.fillRect(788, 548, 14, 34);
      }
      waves(ctx, waterY, '#2a9aaa', t, 6, 1.4, 0.85);
      d.glints.forEach(function (g) {
        if (g[1] < waterY) return;
        additive(ctx, function () { dot(ctx, '#ffffff', g[0], g[1], 8, 0.4 + 0.4 * Math.sin(t * 4 + g[2])); });
      });
      // the ships, coming in from either side
      galleon(ctx, lerp(-260, 200, outCubic(seg(t, 0, 2.6))), 520, 0.5, '#b8282a', '#c8302a', t, 1);
      galleon(ctx, lerp(VW + 260, 1400, outCubic(seg(t, 0.3, 2.9))), 520, 0.5, '#2a5aa8', '#2a6ab8', t, -1);
      // the beach in front, palms, the X and our pirate digging
      ctx.fillStyle = '#e8d098';
      ctx.beginPath(); ctx.moveTo(0, VH); ctx.lineTo(0, 680); ctx.quadraticCurveTo(500, 640, 1000, 690); ctx.quadraticCurveTo(1300, 710, VW, 680); ctx.lineTo(VW, VH); ctx.fill();
      palm(ctx, 220, 760, 300, 60, t);
      palm(ctx, 1420, 750, 260, -50, t, '#2a8a3a');
      ctx.strokeStyle = '#c81e1e'; ctx.lineWidth = 10; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(960, 720); ctx.lineTo(1020, 748); ctx.moveTo(1020, 720); ctx.lineTo(960, 748); ctx.stroke();
      var walk = seg(t, 0.3, 2.2);
      var px = lerp(560, 930, walk);
      pirate(ctx, px, 742, 1.0, t, 0, t > 2.2 && t < 3.4 ? 2 : (t >= 3.4 ? 1 : 0));
      if (t > 2.3 && t < 3.5) {
        d.sand.forEach(function (sd) {
          var age = (t * 2 + sd[2]) % 1;
          ctx.fillStyle = 'rgba(200,170,110,' + (1 - age) + ')';
          ctx.fillRect(990 + sd[0] * 60 * age, 735 - sd[1] * 120 * age + 160 * age * age, 6, 6);
        });
      }
      if (t > 3.4) {
        var up = outBack(seg(t, 3.4, 3.9), 1.4);
        var cx = 990, cy = 730 - up * 50;
        ctx.fillStyle = '#7a4a26'; ctx.fillRect(cx - 40, cy - 30, 80, 46);
        ctx.fillStyle = '#8a5a2e'; ctx.fillRect(cx - 42, cy - 44, 84, 16);
        ctx.fillStyle = '#d8b040'; ctx.fillRect(cx - 30, cy - 44, 8, 60); ctx.fillRect(cx + 22, cy - 44, 8, 60); ctx.fillRect(cx - 6, cy - 34, 12, 14);
        additive(ctx, function () { dot(ctx, '#ffe080', cx, cy - 20, 110, 0.6 * (1 - seg(t, 3.9, 5))); });
      }
      // the gulls
      d.gulls.forEach(function (g) {
        var gx = (g[0] + t * g[2]) % (VW + 100) - 50, gy = g[1] + Math.sin(t * 2 + g[3]) * 10;
        var flap = Math.sin(t * 8 + g[3]) * 8;
        ctx.strokeStyle = '#2a2a2a'; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(gx - 16, gy - flap); ctx.quadraticCurveTo(gx - 6, gy - 8, gx, gy); ctx.quadraticCurveTo(gx + 6, gy - 8, gx + 16, gy - flap); ctx.stroke();
      });
    },
    title: function (ctx, t, d, run) {
      // a treasure map unrolls, the name inked on it, a red X
      var at = 1.4;
      if (t < at) return;
      var open = outCubic(seg(t, at, at + 0.6));
      ctx.save();
      ctx.translate(800, 230);
      ctx.rotate(-0.02);
      var w = 1000 * Math.max(0.05, open), h = 230;
      ctx.save();
      ctx.beginPath(); ctx.rect(-w / 2, -h / 2 - 10, w, h + 20); ctx.clip();
      parchment(ctx, 1000, h, 7);
      ctx.globalAlpha = run.alpha * seg(t, at + 0.4, at + 0.9);
      ctx.font = 'bold 26px ' + HEAVY; ctx.textAlign = 'center'; ctx.fillStyle = '#8a2a1a';
      ctx.fillText('PLUNDER BAY', 0, -70);
      titleText(ctx, (run.info.name || 'Skull Cove').toUpperCase(), 0, 10, 820, 104, '#4a2a12', null);
      ctx.strokeStyle = '#8a2a1a'; ctx.lineWidth = 4; ctx.setLineDash([12, 10]);
      ctx.beginPath(); ctx.moveTo(-380, 80); ctx.quadraticCurveTo(-100, 40, 300, 78); ctx.stroke();
      ctx.setLineDash([]);
      ctx.strokeStyle = '#c81e1e'; ctx.lineWidth = 8;
      ctx.beginPath(); ctx.moveTo(300, 64); ctx.lineTo(330, 94); ctx.moveTo(330, 64); ctx.lineTo(300, 94); ctx.stroke();
      ctx.restore();
      // the rolled ends
      ctx.globalAlpha = run.alpha;
      ctx.fillStyle = '#c8b080';
      ctx.fillRect(-w / 2 - 18, -h / 2 - 14, 22, h + 28);
      ctx.fillRect(w / 2 - 4, -h / 2 - 14, 22, h + 28);
      ctx.restore();
    }
  });

  // ------------------------------------------------ Coral Reef
  Intro.register('pb_reef', {
    name: 'Coral Reef',
    tagline: 'Boardwalks, a lighthouse, a wreck in the lagoon. Something lives under it.',
    accent: '#3ad8c8',
    cues: [[0.2, 'pb_waves', 0.6], [0.6, 'pb_gull', 0.5], [1.7, 'pb_kraken', 0.8], [2.9, 'pb_slam', 0.9],
           [3.5, 'pb_pistol', 0.8], [4.4, 'pb_kraken', 0.6]],
    shakes: [[2.9, 7, 0.45]],
    tagY: 600, tagAt: 3.3,
    setup: function (r) {
      var d = { fish: [], spray: [] };
      for (var i = 0; i < 10; i++) d.fish.push([between(r, 0, VW), between(r, 610, 780), between(r, 20, 50), r() * 6]);
      for (var s = 0; s < 50; s++) d.spray.push([between(r, -1, 1), between(r, 0.5, 1.2), between(r, 4, 9)]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, 470);
      sky.addColorStop(0, '#3a8ae8'); sky.addColorStop(1, '#c8f0ff');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, 470);
      var sea = ctx.createLinearGradient(0, 440, 0, VH);
      sea.addColorStop(0, '#2ab8c8'); sea.addColorStop(1, '#5ae8d8');
      ctx.fillStyle = sea; ctx.fillRect(0, 440, VW, VH - 440);
      // the lighthouse on its rock, its beam sweeping
      ctx.fillStyle = '#6a6a72'; ctx.beginPath(); ctx.ellipse(1300, 460, 130, 40, 0, Math.PI, 0); ctx.fill();
      for (var b = 0; b < 6; b++) {
        ctx.fillStyle = b % 2 ? '#f4f4f4' : '#c81e1e';
        ctx.fillRect(1268 + b * 2, 430 - (b + 1) * 40, 64 - b * 4, 40);
      }
      ctx.fillStyle = '#2a2a30'; ctx.fillRect(1272, 156, 56, 34);
      additive(ctx, function () {
        dot(ctx, '#fff8c0', 1300, 172, 40, 0.9);
        var a = Math.sin(t * 1.4) * 0.8;
        ctx.save(); ctx.translate(1300, 172); ctx.rotate(a);
        var g = ctx.createLinearGradient(0, 0, -700, 0);
        g.addColorStop(0, 'rgba(255,248,192,0.5)'); g.addColorStop(1, 'rgba(255,248,192,0)');
        ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-700, -70); ctx.lineTo(-700, 70); ctx.fill();
        ctx.restore();
      });
      // an islet with stilt huts and palms
      ctx.fillStyle = '#f0dca0'; ctx.beginPath(); ctx.ellipse(260, 470, 240, 46, 0, Math.PI, 0); ctx.fill();
      palm(ctx, 180, 462, 180, 30, t);
      palm(ctx, 330, 462, 150, -30, t, '#3a8a3a');
      ctx.fillStyle = '#c8a878'; ctx.fillRect(400, 380, 70, 50);
      ctx.fillStyle = '#d8c080'; ctx.beginPath(); ctx.moveTo(390, 384); ctx.lineTo(435, 340); ctx.lineTo(480, 384); ctx.fill();
      ctx.fillStyle = '#6a4a2a'; ctx.fillRect(408, 430, 6, 40); ctx.fillRect(456, 430, 6, 40);
      // the wreck, run aground, listing
      ctx.save(); ctx.translate(780, 520); ctx.rotate(-0.12);
      ctx.fillStyle = '#4a3020'; ctx.beginPath(); ctx.moveTo(-220, -50); ctx.lineTo(200, -50); ctx.lineTo(240, -90); ctx.lineTo(210, 10); ctx.lineTo(-190, 10); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#c8302a'; ctx.fillRect(-190, -34, 390, 8);
      ctx.fillStyle = '#3a2412'; ctx.fillRect(-40, -260, 10, 210); ctx.fillRect(90, -190, 10, 140);
      ctx.fillStyle = 'rgba(230,220,200,0.8)'; ctx.fillRect(-100, -240, 70, 60); ctx.fillRect(-20, -200, 60, 40);
      ctx.restore();
      // the kraken: tentacles rise round the wreck, one rears and slams
      var rise = outCubic(seg(t, 1.7, 2.5));
      var tents = [[560, 0.3], [700, -0.5], [930, 0.6], [1060, -0.2]];
      tents.forEach(function (tn, i) {
        var h = rise * (200 + i * 28);
        var sway = Math.sin(t * 2 + i) * 0.25;
        var slam = i === 2 ? seg(t, 2.6, 2.9) : 0;
        var back = i === 2 ? seg(t, 2.0, 2.6) * (1 - slam) : 0;
        ctx.save(); ctx.translate(tn[0], 560);
        for (var s2 = 0; s2 < 14; s2++) {
          var f = s2 / 14;
          var bend = (sway + tn[1] * 0.4 - back * 0.9 + slam * 2.2) * f * f;
          var x = Math.sin(bend) * h * f, y = -Math.cos(bend) * h * f;
          var rad = 30 * (1 - f) + 4;
          ctx.fillStyle = s2 % 2 ? '#7a3a9a' : '#8a4aaa';
          ctx.beginPath(); ctx.arc(x, y, rad, 0, TAU); ctx.fill();
          if (s2 % 2 === 0 && s2 < 12) { ctx.fillStyle = '#f0a8c8'; ctx.beginPath(); ctx.arc(x + rad * 0.5, y, rad * 0.3, 0, TAU); ctx.fill(); }
        }
        ctx.restore();
      });
      if (t > 2.9) {
        var age = t - 2.9;
        d.spray.forEach(function (sp) {
          var x = 1160 + sp[0] * 160 * age * sp[1], y = 560 - sp[2] * 70 * age + 260 * age * age;
          if (y > 600) return;
          ctx.fillStyle = 'rgba(230,250,255,' + Math.max(0, 1 - age / 1.2) + ')';
          ctx.beginPath(); ctx.arc(x, y, 6, 0, TAU); ctx.fill();
        });
      }
      waves(ctx, 570, 'rgba(60,200,210,0.7)', t, 5, 1.8);
      d.fish.forEach(function (fs) {
        var x = (fs[0] + t * fs[2]) % (VW + 60) - 30;
        ctx.fillStyle = ['#ff8a3a', '#ffd84a', '#3ad8ff'][Math.floor(fs[3]) % 3];
        ctx.beginPath(); ctx.ellipse(x, fs[1] + Math.sin(t * 3 + fs[3]) * 6, 14, 7, 0, 0, TAU); ctx.fill();
      });
      // the boardwalk in front, our pirate with a smoking flintlock
      ctx.fillStyle = '#6a4a2a';
      for (var p = 0; p < 16; p++) ctx.fillRect(p * 110 + 20, 722, 14, 90);
      ctx.fillStyle = '#8a6a44'; ctx.fillRect(0, 700, VW, 24);
      ctx.strokeStyle = '#c8a878'; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(0, 650); ctx.lineTo(VW, 650); ctx.stroke();
      for (var q = 0; q < 16; q++) { ctx.fillStyle = '#6a4a2a'; ctx.fillRect(q * 110 + 22, 650, 8, 50); }
      var px = lerp(180, 520, seg(t, 0.4, 2.4));
      pirate(ctx, px, 702, 1.0, t, 0, t > 2.4 ? 1 : 0);
      if (t > 3.5) {
        var puff = t - 3.5;
        ctx.fillStyle = 'rgba(240,240,240,' + Math.max(0, 0.8 - puff * 0.5) + ')';
        ctx.beginPath(); ctx.arc(px + 60 + puff * 40, 610 - puff * 30, 20 + puff * 30, 0, TAU); ctx.fill();
      }
    },
    title: function (ctx, t, d, run) {
      // a driftwood sign on two ropes, a tentacle curled round one end
      var at = 1.5;
      if (t < at) return;
      var k = outBack(seg(t, at, at + 0.4), 1.5);
      ctx.save();
      ctx.translate(800, 240 - (1 - k) * 380);
      ctx.rotate(-0.03 + wobble(t, at + 0.4, 0.04, 14, 4));
      ctx.strokeStyle = '#c8a878'; ctx.lineWidth = 6;
      ctx.beginPath(); ctx.moveTo(-400, -110); ctx.lineTo(-380, -400); ctx.moveTo(400, -110); ctx.lineTo(380, -400); ctx.stroke();
      ctx.fillStyle = '#8a6a44'; roundRect(ctx, -520, -115, 1040, 230, 26); ctx.fill();
      ctx.strokeStyle = '#5a4026'; ctx.lineWidth = 4;
      for (var g = -3; g <= 3; g++) { ctx.beginPath(); ctx.moveTo(-500, g * 28); ctx.quadraticCurveTo(0, g * 28 + 10, 500, g * 28 - 4); ctx.stroke(); }
      ctx.globalAlpha = run.alpha;
      ctx.font = 'bold 26px ' + HEAVY; ctx.textAlign = 'center'; ctx.fillStyle = '#ffe8b0';
      ctx.fillText('PLUNDER BAY', 0, -64);
      titleText(ctx, (run.info.name || 'Coral Reef').toUpperCase(), 0, 16, 900, 104, '#f4fff8', '#2a4a5a', 10);
      ctx.fillStyle = '#8a4aaa';
      for (var s = 0; s < 10; s++) {
        var f = s / 10, a = f * 3.6 + Math.sin(t * 2) * 0.2;
        ctx.beginPath(); ctx.arc(500 + Math.cos(a) * (60 - f * 30), Math.sin(a) * (60 - f * 30), 16 * (1 - f) + 4, 0, TAU); ctx.fill();
      }
      ctx.restore();
    }
  });

  // ------------------------------------------------ Port Royale
  Intro.register('pb_royale', {
    name: 'Port Royale',
    tagline: 'Rob the governor\'s town blind. When the fort\'s bell rings, run.',
    accent: '#ff5a4a',
    cues: [[0.3, 'pb_warn', 0.5], [0.9, 'pb_drum', 0.7], [2.8, 'pb_cock', 0.8], [3.1, 'pb_musket', 1],
           [3.8, 'pb_cannon', 0.7], [4.5, 'pb_coins', 0.6]],
    shakes: [[3.8, 5, 0.35]],
    tagY: 600, tagAt: 3.4,
    setup: function (r) {
      var d = { houses: [] };
      var hues = ['#e8c878', '#d88a6a', '#8ac0d8', '#e8e0c8', '#c8d88a', '#e8a0a0'];
      for (var i = 0; i < 9; i++) d.houses.push([i * 180 + between(r, -10, 10), between(r, 150, 230), hues[i % hues.length]]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, VH);
      sky.addColorStop(0, '#4a8ad8'); sky.addColorStop(0.6, '#c8e0f0'); sky.addColorStop(1, '#e8f0f4');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      // the fort on its hill, the governor's colours flying
      ctx.fillStyle = '#7a9a5a'; ctx.beginPath(); ctx.ellipse(800, 400, 620, 180, 0, Math.PI, 0); ctx.fill();
      ctx.fillStyle = '#b8b0a0'; ctx.fillRect(560, 240, 480, 110);
      for (var c = 0; c < 12; c++) ctx.fillRect(560 + c * 42, 224, 24, 18);
      ctx.fillStyle = '#a8a090'; ctx.fillRect(520, 210, 80, 140); ctx.fillRect(1000, 210, 80, 140);
      ctx.fillStyle = '#4a3a2a'; ctx.fillRect(770, 290, 60, 60);
      ctx.fillStyle = '#e8e8e8'; ctx.fillRect(796, 110, 6, 120);
      var wave = Math.sin(t * 4) * 6;
      ctx.fillStyle = '#1a2a5a'; ctx.beginPath(); ctx.moveTo(802, 112); ctx.lineTo(880, 116 + wave); ctx.lineTo(880, 166 + wave); ctx.lineTo(802, 162); ctx.fill();
      ctx.fillStyle = '#e8c840'; ctx.beginPath(); ctx.arc(842, 140 + wave / 2, 12, 0, TAU); ctx.fill();
      if (t > 3.8) {
        var age = t - 3.8;
        ctx.fillStyle = 'rgba(240,240,240,' + Math.max(0, 0.85 - age * 0.4) + ')';
        ctx.beginPath(); ctx.arc(600 - age * 30, 260 - age * 50, 30 + age * 40, 0, TAU); ctx.fill();
        additive(ctx, function () { dot(ctx, '#ffd890', 590, 270, 60, Math.max(0, 1 - age * 3)); });
      }
      // the town along the quay
      d.houses.forEach(function (h) {
        ctx.fillStyle = h[2]; ctx.fillRect(h[0], 520 - h[1], 160, h[1]);
        ctx.fillStyle = '#8a4a3a'; ctx.beginPath(); ctx.moveTo(h[0] - 10, 520 - h[1]); ctx.lineTo(h[0] + 80, 460 - h[1]); ctx.lineTo(h[0] + 170, 520 - h[1]); ctx.fill();
        ctx.fillStyle = '#4a6a8a';
        for (var w = 0; w < 3; w++) for (var r2 = 0; r2 < 2; r2++) ctx.fillRect(h[0] + 18 + w * 48, 520 - h[1] + 24 + r2 * 60, 26, 34);
      });
      ctx.fillStyle = '#e8e4d8'; ctx.fillRect(1380, 180, 70, 340);
      ctx.fillStyle = '#8a4a3a'; ctx.beginPath(); ctx.moveTo(1370, 180); ctx.lineTo(1415, 100); ctx.lineTo(1460, 180); ctx.fill();
      // the street
      ctx.fillStyle = '#9a9488'; ctx.fillRect(0, 520, VW, 380);
      ctx.strokeStyle = 'rgba(80,70,60,0.35)'; ctx.lineWidth = 2;
      for (var row = 0; row < 9; row++) { ctx.beginPath(); ctx.moveTo(0, 545 + row * 36); ctx.lineTo(VW, 545 + row * 36); ctx.stroke(); }
      // barrels, a pirate crouched behind them with a sack of gold
      ctx.fillStyle = '#7a4a28';
      [[300, 740], [370, 740], [335, 684]].forEach(function (b) { ctx.beginPath(); ctx.ellipse(b[0], b[1], 34, 40, 0, 0, TAU); ctx.fill(); });
      ctx.fillStyle = '#4a3020'; ctx.fillRect(266, 730, 138, 6); ctx.fillRect(301, 674, 68, 6);
      var duck = t > 2.9 && t < 3.6 ? 30 : 0;
      pirate(ctx, 200, 772 + duck, 1.0, t, 0, t > 3.6 ? 1 : 0);
      ctx.fillStyle = '#8a5a30'; ctx.beginPath(); ctx.ellipse(150, 748, 30, 36, 0, 0, TAU); ctx.fill();
      ctx.fillStyle = '#ffd040'; ctx.font = 'bold 22px ' + HEAVY; ctx.textAlign = 'center'; ctx.fillText('$', 150, 756); ctx.textAlign = 'left';
      // the redcoats march in from the right, stop, and fire
      var march = seg(t, 0.6, 2.6);
      for (var s = 0; s < 4; s++) {
        var x = lerp(VW + 120 + s * 110, 900 + s * 110, outCubic(march));
        var step = march < 1 ? Math.sin(t * 9 + s) * 0.4 : 0;
        ctx.save(); ctx.translate(x, 772); ctx.scale(-1.0, 1.0);
        ctx.fillStyle = '#f0ece0'; ctx.save(); ctx.translate(-7, -40); ctx.rotate(step); ctx.fillRect(-6, 0, 12, 40); ctx.restore();
        ctx.save(); ctx.translate(7, -40); ctx.rotate(-step); ctx.fillRect(-6, 0, 12, 40); ctx.restore();
        ctx.fillStyle = '#c81e1e'; ctx.fillRect(-16, -84, 32, 46);
        ctx.strokeStyle = '#f4f0e0'; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.moveTo(-14, -82); ctx.lineTo(14, -42); ctx.moveTo(14, -82); ctx.lineTo(-14, -42); ctx.stroke();
        ctx.fillStyle = SKIN; ctx.fillRect(-11, -108, 22, 24);
        ctx.fillStyle = '#1a1a22'; ctx.beginPath(); ctx.moveTo(-20, -106); ctx.quadraticCurveTo(0, -126, 20, -106); ctx.fill();
        var aim = seg(t, 2.6, 2.9);
        ctx.save(); ctx.translate(14, -76); ctx.rotate(lerp(-1.4, -0.05, aim));
        ctx.fillStyle = '#5a3a22'; ctx.fillRect(0, -3, 70, 6);
        ctx.fillStyle = '#8a8e96'; ctx.fillRect(60, -2, 22, 4);
        ctx.restore();
        ctx.restore();
        if (t > 3.1) {
          var age2 = t - 3.1;
          ctx.fillStyle = 'rgba(245,245,245,' + Math.max(0, 0.9 - age2 * 0.5) + ')';
          ctx.beginPath(); ctx.arc(x - 90 - age2 * 30, 700 - age2 * 20, 16 + age2 * 30, 0, TAU); ctx.fill();
          if (age2 < 0.12) additive(ctx, function () { dot(ctx, '#fff0a0', x - 84, 696, 30, 1); });
        }
      }
    },
    title: function (ctx, t, d, run) {
      // the governor's proclamation, pinned up, sealed in red wax
      var at = 1.4;
      if (t < at) return;
      var k = outBack(seg(t, at, at + 0.4), 1.3);
      ctx.save();
      ctx.translate(800, 230);
      ctx.scale(k, k);
      ctx.rotate(0.02);
      parchment(ctx, 980, 250, 13);
      ctx.globalAlpha = run.alpha;
      ctx.font = 'bold 24px ' + HEAVY; ctx.textAlign = 'center'; ctx.fillStyle = '#6a2a1a';
      ctx.fillText('BY ORDER OF THE GOVERNOR', 0, -82);
      ctx.fillStyle = '#4a2a12'; ctx.fillRect(-380, -64, 760, 3);
      titleText(ctx, (run.info.name || 'Port Royale').toUpperCase(), 0, 4, 840, 100, '#2a1a10', null);
      ctx.font = 'bold 20px ' + HEAVY; ctx.fillStyle = '#6a2a1a'; ctx.textAlign = 'center';
      ctx.fillText('PIRATES WILL BE SHOT ON SIGHT', 0, 82);
      var seal = outBack(seg(t, at + 0.5, at + 0.8), 2);
      ctx.save(); ctx.translate(410, 90); ctx.scale(seal, seal);
      ctx.fillStyle = '#a81a1a'; ctx.beginPath(); ctx.arc(0, 0, 44, 0, TAU); ctx.fill();
      ctx.fillStyle = '#c82a2a'; ctx.beginPath(); ctx.arc(0, 0, 32, 0, TAU); ctx.fill();
      ctx.fillStyle = '#e8c840'; ctx.font = 'bold 30px ' + HEAVY; ctx.fillText('G', 0, 11);
      ctx.restore();
      ctx.restore();
    }
  });

  // ------------------------------------------------ Doubloon Isle
  Intro.register('pb_doubloon', {
    name: 'Doubloon Isle',
    tagline: 'A river of lava, a temple with the idol on top, and a volcano full of gold.',
    accent: '#ff8a2a',
    cues: [[0.3, 'pb_rumble', 0.7], [1.0, 'pb_rumble', 0.8], [1.4, 'pb_twist_eruption', 0.7], [2.0, 'pb_coins', 0.7],
           [3.2, 'pb_bomb', 0.8], [3.9, 'pb_coins', 0.6]],
    shakes: [[1.4, 9, 0.7], [3.2, 5, 0.3]],
    tagY: 600, tagAt: 3.3,
    setup: function (r) {
      var d = { coins: [], embers: [], stars: makeStars(r, 60, 0, 300) };
      for (var i = 0; i < 40; i++) d.coins.push([between(r, -1, 1), between(r, 0.6, 1.2), between(r, 0, 1.6), r() * 6]);
      for (var e = 0; e < 60; e++) d.embers.push([between(r, 0, VW), between(r, 0, VH), between(r, 0, 6)]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, VH);
      sky.addColorStop(0, '#1a0e1e'); sky.addColorStop(0.5, '#5a1e1a'); sky.addColorStop(1, '#a04a1a');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      stars(ctx, d.stars, t, 0.6);
      var erupt = seg(t, 1.4, 1.8);
      // the volcano, its crater at y 360
      ctx.fillStyle = '#2a1e1e';
      ctx.beginPath(); ctx.moveTo(380, 640); ctx.lineTo(720, 360); ctx.lineTo(880, 360); ctx.lineTo(1220, 640); ctx.fill();
      ctx.fillStyle = '#3a2826';
      ctx.beginPath(); ctx.moveTo(720, 360); ctx.lineTo(760, 420); ctx.lineTo(820, 384); ctx.lineTo(870, 430); ctx.lineTo(880, 360); ctx.fill();
      additive(ctx, function () {
        dot(ctx, '#ff6a1a', 800, 360, 110 + erupt * 150, 0.5 + erupt * 0.5);
        if (erupt > 0) {
          ctx.fillStyle = 'rgba(255,140,40,' + (0.6 * erupt) + ')';
          ctx.beginPath(); ctx.moveTo(760, 360); ctx.quadraticCurveTo(800, 150 - erupt * 40, 840, 360); ctx.fill();
        }
      });
      // a river of lava down its side
      ctx.strokeStyle = '#ff7a1a'; ctx.lineWidth = 14; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(810, 376); ctx.quadraticCurveTo(850, 500, 780, 640); ctx.stroke();
      additive(ctx, function () { ctx.strokeStyle = 'rgba(255,220,120,0.6)'; ctx.lineWidth = 6; ctx.stroke(); });
      // gold flying out of the crater, raining down either side
      if (t > 1.6) {
        d.coins.forEach(function (c) {
          var age = t - 1.6 - c[2] * 0.6;
          if (age < 0) return;
          var x = 800 + c[0] * 560 * age, y = 360 - c[1] * 420 * age + 330 * age * age;
          if (y > 700) return;
          coin(ctx, x, y, 11, t * 8 + c[3]);
        });
      }
      // the temple in the jungle, the idol glinting on top
      ctx.fillStyle = '#1e2a1a';
      ctx.beginPath(); ctx.moveTo(0, 660); for (var j = 0; j <= 16; j++) ctx.lineTo(j * 100, 600 + Math.sin(j * 1.7) * 30); ctx.lineTo(VW, 660); ctx.fill();
      ctx.fillStyle = '#5a5444';
      for (var tier = 0; tier < 4; tier++) ctx.fillRect(1180 + tier * 30, 600 - tier * 40, 280 - tier * 60, 42);
      ctx.fillStyle = '#e8b830'; ctx.fillRect(1306, 412, 28, 30);
      additive(ctx, function () { dot(ctx, '#ffe080', 1320, 426, 50, 0.6 + 0.3 * Math.sin(t * 4)); });
      // the black sand in front, the lava trench, the stone bridge
      ctx.fillStyle = '#2a2624'; ctx.fillRect(0, 640, VW, 260);
      ctx.fillStyle = '#ff6a1a'; ctx.fillRect(0, 712, VW, 40);
      ctx.fillStyle = '#3a3430'; ctx.fillRect(0, 704, VW, 8); ctx.fillRect(0, 752, VW, 8);
      additive(ctx, function () {
        for (var l = 0; l < 20; l++) dot(ctx, '#ffb04a', l * 85 + Math.sin(t * 2 + l) * 20, 732, 40, 0.5);
      });
      ctx.fillStyle = '#8a8478'; ctx.fillRect(560, 690, 420, 22);
      ctx.fillStyle = '#6a6460'; ctx.fillRect(600, 712, 340, 26);
      ctx.fillStyle = '#7a746a'; ctx.fillRect(560, 676, 420, 14);
      // our pirate running the bridge with a gold bar, a lava bomb coming down
      var run2 = seg(t, 0.4, 4.2);
      var px = lerp(420, 1100, run2);
      pirate(ctx, px, 692, 0.95, t, 0, 0);
      ctx.fillStyle = '#ffc830'; ctx.fillRect(px - 40, 622, 34, 14);
      if (t > 2.7) {
        var fall = seg(t, 2.7, 3.2);
        var bx = lerp(700, 760, fall), by = lerp(380, 690, fall * fall);
        if (fall < 1) {
          ctx.fillStyle = '#3a1a10'; ctx.beginPath(); ctx.arc(bx, by, 18, 0, TAU); ctx.fill();
          additive(ctx, function () { dot(ctx, '#ff8a2a', bx, by, 40, 0.8); });
        } else {
          var age = t - 3.2;
          additive(ctx, function () { dot(ctx, '#ffb04a', 760, 690, 90 + age * 100, Math.max(0, 1 - age * 1.5)); });
        }
      }
      d.embers.forEach(function (e) {
        var y = (e[1] - t * 60) % VH;
        if (y < 0) y += VH;
        additive(ctx, function () { dot(ctx, '#ff8a2a', e[0] + Math.sin(t + e[2]) * 10, y, 4, 0.5 + 0.5 * Math.sin(t * 5 + e[2])); });
      });
    },
    title: function (ctx, t, d, run) {
      // a gold tablet carved with glyphs, the name raised in it, coming
      // down once the volcano has gone up
      var at = 2.3;
      if (t < at) return;
      var k = outBack(seg(t, at, at + 0.4), 1.6);
      ctx.save();
      ctx.translate(800, 220 - (1 - k) * 360);
      ctx.rotate(-0.02 + wobble(t, at + 0.4, 0.03, 16, 5));
      var g = ctx.createLinearGradient(0, -130, 0, 130);
      g.addColorStop(0, '#ffe080'); g.addColorStop(0.5, '#d8a030'); g.addColorStop(1, '#a87020');
      ctx.fillStyle = g; roundRect(ctx, -520, -125, 1040, 250, 14); ctx.fill();
      ctx.strokeStyle = '#7a5010'; ctx.lineWidth = 6; roundRect(ctx, -500, -105, 1000, 210, 8); ctx.stroke();
      ctx.fillStyle = '#8a6018';
      for (var gl = 0; gl < 12; gl++) {
        var gx = -440 + gl * 80;
        ctx.fillRect(gx, -98, 30, 8); ctx.fillRect(gx + 10, -90, 10, 10);
        ctx.fillRect(gx, 90, 30, 8); ctx.fillRect(gx + 10, 80, 10, 10);
      }
      ctx.globalAlpha = run.alpha;
      ctx.font = 'bold 24px ' + HEAVY; ctx.textAlign = 'center'; ctx.fillStyle = '#5a3a08';
      ctx.fillText('PLUNDER BAY', 0, -54);
      titleText(ctx, (run.info.name || 'Doubloon Isle').toUpperCase(), 0, 18, 900, 100, '#fff4c0', '#7a4a08', 10);
      var shine = seg(t, at + 0.4, at + 1.4);
      if (shine > 0 && shine < 1) {
        additive(ctx, function () {
          var sx = lerp(-520, 520, shine);
          var sg = ctx.createLinearGradient(sx - 80, 0, sx + 80, 0);
          sg.addColorStop(0, 'rgba(255,255,255,0)'); sg.addColorStop(0.5, 'rgba(255,255,220,0.5)'); sg.addColorStop(1, 'rgba(255,255,255,0)');
          ctx.fillStyle = sg; ctx.fillRect(sx - 80, -125, 160, 250);
        });
      }
      ctx.restore();
    }
  });
})(window);
