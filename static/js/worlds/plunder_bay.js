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
                off: 'The volcano settles', colour: '#ff8a2a', chip: 'ERUPTION' },
    maelstrom: { warn: 'THE SEA IS TURNING', warnSub: 'The lagoon is starting to spin...',
                 on: 'THE MAELSTROM!', onSub: 'Get out of the water -- it is throwing up the deep\'s treasure',
                 off: 'The maelstrom closes', colour: '#3ad8e8', chip: 'MAELSTROM' },
    storm: { warn: 'THE SKY IS CRACKLING', warnSub: 'Lightning seeks out gold...',
             on: 'THE STORM!', onSub: 'Lightning strikes whoever carries gold first -- watch the rings',
             off: 'The storm rolls on', colour: '#bfe8ff', chip: 'STORM' },
    geysers: { warn: 'THE GROUND IS HISSING', warnSub: 'The springs are about to blow...',
               on: 'THE GEYSERS!', onSub: 'Stay off the rings -- or ride one into the air',
               off: 'The springs go quiet', colour: '#7af0ff', chip: 'GEYSERS' },
    ghosts: { warn: 'THE FOG IS RISING OFF THE WRECKS', warnSub: 'Something is climbing out of them...',
              on: 'THE GHOST CREWS!', onSub: 'Skeletons with pistols -- carriers first. Shatter one for its purse',
              off: 'The dead lie down again', colour: '#7aff9a', chip: 'GHOSTS' }
  };
  // keep these in step with app/game/worlds/plunder_bay.py
  var GRAVITY = 62, DIG_REACH = 3.6, CANNON_REACH = 5.4;
  var CANNON_MIN = 24, CANNON_MAX = 120, CANNON_ARC = 0.85, CANNON_COOL = 9;
  var BANK_PAD = 1.4, WADE = 0.4, DEEP = 2.8, WADE_SCALE = 0.78, DEEP_SCALE = 0.6;
  var DIG_SECONDS = 2.6, RAID_SECONDS = 2.5, EYE = 4.6;

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
    var cannonReady = {}, shakeUntil = 0, shakeK = 0;
    var act = { k: '', start: 0 };
    var lastRole = '', lastSide = '', sideAt = 0, digDust = 0, splashAt = 0;
    var bolts = [];               // lightning: {at, t0, seed}
    var columns = [];             // geysers blowing: {at, t0}
    var style = {}, vortex = null, vortexR = 26;
    // the island's moving scenery (plunder_bay_rigs.js and rail_rivals_rigs.js)
    var rigs = [];
    var rigCtx = {
      players: function () {
        var out = [];
        if (client.myId && client.local && client.local.alive !== false) {
          out.push({ id: client.myId, pos: client.local.pos, team: client.myTeam, me: true });
        }
        Object.keys(client.players || {}).forEach(function (id) {
          var pl = client.players[id];
          if (pl && pl.pos && pl.alive !== false && String(id) !== String(client.myId)) {
            out.push({ id: id, pos: pl.pos, team: pl.team });
          }
        });
        return out;
      },
      viewer: function () {
        var cam = client.cameraPosition ? client.cameraPosition() : null;
        var at = cam && cam.eye ? cam.eye : client.local.pos;
        var yaw = client.local.yaw || 0, pitch = client.local.pitch || 0, cp = Math.cos(pitch);
        return { eye: at, dir: [Math.sin(yaw) * cp, Math.sin(pitch), Math.cos(yaw) * cp] };
      },
      sound: function (name, at, volume) {
        if (!client.audio || !at) return;
        var v = client.volumeAt ? client.volumeAt(at) : 1;
        client.audio.play(name, { volume: (volume || 1) * v });
      },
      sound2d: function (name, volume) {
        if (client.audio) client.audio.play(name, { volume: volume === undefined ? 1 : volume });
      },
      physics: function () { return client.physics || null; },
      twist: function () { return twist; },
      // the sea's height right now (the tide moves it): rigs that float on
      // it (spec.tide) ride up and down with it
      water: function () { return waterLevel(); }
    };
    function eye() {
      var cam = client.cameraPosition ? client.cameraPosition() : null;
      return cam && cam.eye ? cam.eye : client.local.pos;
    }
    /* A twist's words, as this island tells it (extra.twist_text). */
    function twistInfo(kind) {
      var base = TWISTS[kind] || {}, own = (ex.twist === kind && ex.twist_text) || {}, out = {};
      Object.keys(base).forEach(function (k) { out[k] = base[k]; });
      Object.keys(own).forEach(function (k) { out[k] = own[k]; });
      return out;
    }

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
      vortex = ex.vortex ? [ex.vortex[0] + centre[0], ex.vortex[1], ex.vortex[2] + centre[2]] : null;
      vortexR = ex.vortex_r || 26;
      style = ex.style || {};
      reset();
      rigs = global.Rigs ? global.Rigs.build(map, rigCtx) : [];
    }

    function reset() {
      ax = {};
      items = {}; liveX = []; flights = {}; shells = []; rings = []; npcs = {}; slams = {}; aims = {};
      bolts = []; columns = [];
      twist = { kind: ex.twist || '', on: false, until: 0 };
      cannonReady = {}; shakeUntil = 0;
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
      if (vortex && twist.on && twist.kind === 'maelstrom' && local.alive !== false && local.pos[1] < waterLevel() + 0.5) {
        var vx = local.pos[0] - vortex[0], vz = local.pos[2] - vortex[2], vd = Math.hypot(vx, vz);
        if (vd < vortexR && vd > 0.5) {
          var vk = 1 - vd / vortexR, ux = -vx / vd, uz = -vz / vd;
          local.pos[0] += (ux * 7.5 * (0.4 + vk) - uz * 9 * (0.3 + vk)) * dt;
          local.pos[2] += (uz * 7.5 * (0.4 + vk) + ux * 9 * (0.3 + vk)) * dt;
        }
      }
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
        if (s.kind === 'bomb' && style.bomb === 'rocket') {
          var hue = ['#ff5ad8', '#5ae8ff', '#ffe05a', '#7aff7a', '#ff7a3a'][n % 5];
          put(r, 'box', p[0], p[1], p[2], 0, time * 6, 0, 0.8, 2.6, 0.8, '#c8302a');
          put(r, 'cone', p[0], p[1] + 1.8, p[2], 0, 0, 0, 1.0, 1.2, 1.0, '#e8e0d0');
          put(r, 'sph', p[0], p[1], p[2], 0, 0, 0, 2.6, 2.6, 2.6, hue, 0.5, 2, 1);
          if (client.particles) {
            client.particles.spawn({ p: p.slice(), v: [(Math.random() - 0.5) * 4, -2, (Math.random() - 0.5) * 4],
              life: 0.6, size: 0.7, grow: -0.4, gravity: -6, spin: 3, blend: 'add', shape: 'spark', colors: ['#ffffff', hue, '#ffd04a'] });
          }
          return;
        } else if (s.kind === 'bomb') {
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
        var colour = g.kind === 'slam' ? (style.kraken === 'frost' ? '#9ae8ff' : '#c05aff') :
          g.kind === 'bomb' ? (style.bomb === 'rocket' ? '#ff5ad8' : '#ff6a1a') : g.kind === 'bolt' ? '#bfe8ff' :
          g.kind === 'geyser' ? '#7af0ff' : (TEAM_LIGHT[g.team] || '#ffffff');
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
        if (!n) n = npcs[id] = { kind: ['tentacle', 'redcoat', 'skeleton'][e[1]] || 'redcoat', p: [e[2], e[3], e[4]], yaw: e[5], born: t };
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
        else if (n.kind === 'skeleton') drawSkeleton(r, n, id, time, t);
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
        var frost = style.kraken === 'frost';
        var colour = frost ? (s % 2 ? '#6a9ab8' : '#8ab8d0') : (s % 2 ? '#7a3a9a' : '#8a4aaa');
        if (hurt > 0.5 && s % 3 === 0) colour = frost ? '#c8e8f8' : '#a85ab8';
        put(r, 'sph', x, y, z, 0, 0, 0, rad, height / segs * 1.6 + 0.2, rad, colour);
        if (s % 2 === 0 && s < segs - 2) {
          // suckers along the inside of the curl
          put(r, 'sph', x - Math.sin(time + id) * rad * 0.45, y, z - Math.cos(time + id) * rad * 0.45,
              0, 0, 0, rad * 0.32, rad * 0.32, rad * 0.32, frost ? '#f0faff' : '#f0a8c8');
          if (frost && s % 4 === 0) {
            put(r, 'cone', x + rad * 0.5, y + 0.4, z, 0, 0, -0.6, rad * 0.4, rad * 0.9, rad * 0.4, '#e8f8ff', 0.85);
          }
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
      if (style.bomb === 'rocket') {
        // the fireworks barge going up: its mortars glowing, sparks off it
        var g2 = 0.5 + 0.5 * Math.sin(time * 9);
        put(r, 'sph', vent[0], vent[1] + 1, vent[2], 0, 0, 0, 14, 6, 14, ['#ff5ad8', '#5ae8ff', '#ffe05a'][Math.floor(time * 3) % 3], 0.3 * g2, 2, 1);
        if (client.particles && Math.random() < 0.7) {
          client.particles.spawn({ p: [vent[0] + (Math.random() - 0.5) * 6, vent[1] + 1, vent[2] + (Math.random() - 0.5) * 6],
            v: [(Math.random() - 0.5) * 8, 18 + Math.random() * 12, (Math.random() - 0.5) * 8], life: 1.2, size: 0.9, grow: -0.5,
            gravity: -20, spin: 3, blend: 'add', shape: 'spark', colors: ['#ffffff', '#ffd04a', '#ff5ad8', '#5ae8ff'] });
        }
        return;
      }
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

    /* A skeleton of the ghost crews: bare bones under a rag of a coat, a
       tricorn gone green, a pistol, and eyes burning green. */
    function drawSkeleton(r, n, id, time, t) {
      var p = n.p, yaw = n.yaw || 0;
      var fade = n.gone ? Math.max(0, 1 - (t - n.gone) / 1.2) : 1;
      if (fade <= 0) return;
      var rise = Math.min(1, (t - n.born) / 1.2);
      var c = Math.cos(yaw), s = Math.sin(yaw);
      var lift = (1 - rise) * -4;
      function at(dx, dy, dz) { return [p[0] + dx * c + dz * s, p[1] + dy + lift, p[2] - dx * s + dz * c]; }
      function box(dx, dy, dz, sx, sy, sz, colour, rx, mat, a, em) {
        var q = at(dx, dy, dz);
        put(r, 'box', q[0], q[1], q[2], rx || 0, yaw, 0, sx, sy, sz, colour, (a === undefined ? 1 : a) * fade, mat || 0, em || 0);
      }
      var bone = '#e8e2cc', rag = '#3a4a3a';
      if (n.state === 'down' || n.state === 'gone') {
        // a heap of bones and the hat on top
        for (var k = 0; k < 6; k++) {
          var q0 = at((k % 3 - 1) * 0.9, 0.3, (Math.floor(k / 3) - 0.5) * 1.2);
          put(r, 'box', q0[0], q0[1], q0[2], k, yaw + k, 0, 0.4, 0.4, 1.8, bone, fade);
        }
        var sk = at(0.2, 0.7, 0.4);
        put(r, 'sph', sk[0], sk[1], sk[2], 0, 0, 0, 1.2, 1.1, 1.2, bone, fade);
        return;
      }
      var walking = n.state === 'walk';
      var swing = walking ? Math.sin(time * 8 + id) * 0.55 : 0;
      var rattle = Math.sin(time * 23 + id) * 0.05;
      box(-0.5, 1.0, 0, 0.35, 2.0, 0.35, bone, swing);
      box(0.5, 1.0, 0, 0.35, 2.0, 0.35, bone, -swing);
      box(0, 2.2, 0, 1.6, 0.4, 0.6, bone);
      for (var rb = 0; rb < 4; rb++) box(0, 2.8 + rb * 0.42, 0.05, 1.7 - rb * 0.1, 0.18, 0.9, bone);
      box(0, 3.3, -0.3, 0.3, 2.2, 0.3, bone);
      box(0, 3.4, -0.2, 2.5, 2.4, 0.9, rag, 0, 0, 0.85);
      box(0, 3.2, 0.32, 1.0, 2.0, 0.1, '#2a3a2a', 0, 0, 0.9);
      var head = at(0, 4.9 + rattle, 0.05);
      put(r, 'sph', head[0], head[1], head[2], 0, yaw, 0, 1.3, 1.35, 1.35, bone, fade);
      box(0, 4.55 + rattle, 0.5, 0.9, 0.35, 0.3, bone);
      box(-0.3, 5.0 + rattle, 0.62, 0.28, 0.28, 0.1, '#7aff9a', 0, 0, 1, 1);
      box(0.3, 5.0 + rattle, 0.62, 0.28, 0.28, 0.1, '#7aff9a', 0, 0, 1, 1);
      var hat = at(0, 5.6 + rattle, 0);
      put(r, 'tricorn', hat[0], hat[1], hat[2], 0, yaw, 0, 2.4, 1.4, 2.4, '#2a3a30', fade);
      var aim = aims[id];
      var level = n.state === 'aim' || (aim && aim.until > t);
      if (level) {
        box(0.9, 3.8, 0.8, 0.3, 0.3, 1.8, bone);
        var tip = at(0.9, 3.85, 2.0);
        put(r, 'box', tip[0], tip[1], tip[2], 0, yaw, 0, 0.3, 0.45, 1.0, '#4a4a50', fade, 1);
        if (Math.sin(time * 18) > 0.3) put(r, 'sph', tip[0], tip[1] + 0.1, tip[2] + 0.4, 0, 0, 0, 0.6, 0.6, 0.6, '#7aff9a', 0.85, 2, 1);
      } else {
        box(-1.3, 3.4, 0, 0.3, 2.0, 0.3, bone, -swing * 0.6);
        box(1.3, 3.4, 0, 0.3, 2.0, 0.3, bone, swing * 0.6);
        box(1.35, 2.2, 0.4, 0.2, 0.2, 2.4, '#8a8e96', 0.3, 1);
      }
      // the green glow about it
      var g = at(0, 3, 0);
      put(r, 'sph', g[0], g[1], g[2], 0, 0, 0, 5, 7, 5, '#5aff8a', 0.08 * fade, 2, 0.6);
      if (n.hp !== undefined && n.hp < 1) hpBar(r, [p[0], p[1] + 7.2, p[2]], n.hp, '#7aff9a');
    }

    /* The storm's lightning: a jagged bolt from the cloud base to where it
       struck, gone in a moment, and the ground round it glowing. */
    function drawBolts(r, time) {
      var t = now();
      bolts = bolts.filter(function (b) { return t - b.t0 < 0.45; });
      bolts.forEach(function (b) {
        var life = 1 - (t - b.t0) / 0.45;
        var x = b.at[0], y = b.at[1], z = b.at[2];
        var top = y + 70, n = 14, px = x + (hash(b.seed) - 0.5) * 16, pz = z + (hash(b.seed + 1) - 0.5) * 16;
        var prev = [px, top, pz];
        for (var i = 1; i <= n; i++) {
          var f = i / n;
          var jx = i === n ? 0 : (hash(b.seed + i * 3) - 0.5) * 7 * (1 - f * 0.6);
          var jz = i === n ? 0 : (hash(b.seed + i * 5) - 0.5) * 7 * (1 - f * 0.6);
          var cur = [px + (x - px) * f + jx, top + (y - top) * f, pz + (z - pz) * f + jz];
          var steps = 5;
          for (var k = 0; k < steps; k++) {
            var g = (k + 0.5) / steps;
            put(r, 'box', prev[0] + (cur[0] - prev[0]) * g, prev[1] + (cur[1] - prev[1]) * g, prev[2] + (cur[2] - prev[2]) * g,
                0, 0, 0, 0.55, 1.2, 0.55, '#ffffff', life, 2, 1);
          }
          put(r, 'sph', cur[0], cur[1], cur[2], 0, 0, 0, 2.4, 2.4, 2.4, '#bfe8ff', 0.25 * life, 2, 1);
          prev = cur;
        }
        put(r, 'cyl', x, y + 0.1, z, 0, 0, 0, 9 * life + 2, 0.06, 9 * life + 2, '#bfe8ff', 0.5 * life, 2, 1);
      });
    }

    /* A geyser blowing: a column of boiling water shooting up out of its
       ring, spray at the top, steam all round, then falling back. */
    function drawColumns(r, time) {
      var t = now();
      columns = columns.filter(function (c) { return t - c.t0 < 2.6; });
      columns.forEach(function (c) {
        var a = t - c.t0;
        var h = a < 0.25 ? 30 * (a / 0.25) : (a < 1.6 ? 30 : 30 * Math.max(0, 1 - (a - 1.6) / 1.0));
        var x = c.at[0], y = c.at[1], z = c.at[2];
        for (var k = 0; k < 8; k++) {
          var f = (k + 0.5) / 8, wob = Math.sin(time * 14 + k * 1.7) * 0.4;
          put(r, 'cyl', x + wob, y + h * f, z - wob, 0, time * 2, 0, 3.6 - f * 1.4, h / 8 + 0.3, 3.6 - f * 1.4,
              k % 2 ? '#e8fcff' : '#9ae8f8', 0.65, 0, 0.3);
        }
        if (h > 2) {
          put(r, 'sph', x, y + h + 1, z, 0, time * 3, 0, 7, 3.6, 7, '#f4feff', 0.55, 0, 0.3);
          if (client.particles && Math.random() < 0.8) {
            client.particles.spawn({ p: [x, y + h, z], v: [(Math.random() - 0.5) * 14, 6 + Math.random() * 6, (Math.random() - 0.5) * 14],
              life: 1.2, size: 1.2, grow: 0.6, gravity: -26, spin: 2, blend: 'normal', shape: 'smoke', colors: ['#ffffff', '#d8f4ff'] });
          }
        }
      });
    }

    /* The maelstrom: rings of foam turning round the eye, faster the nearer
       they are, the water sloping down into a dark funnel, spray. */
    function drawMaelstrom(r, time) {
      if (!vortex || !(twist.on && twist.kind === 'maelstrom')) return;
      var w = waterLevel(), R = vortexR;
      for (var k = 0; k < 7; k++) {
        var f = (k + 1) / 7, rad = R * f;
        var spin = time * (2.4 / (0.35 + f)), y = w + 0.12 - (1 - f) * 2.2;
        put(r, 'torus', vortex[0], y, vortex[2], 0, spin, 0, rad * 2, 0.7, rad * 2, k % 2 ? '#e8fcff' : '#7ad8e8', 0.55, 0, 0.4);
        for (var a = 0; a < 6; a++) {
          var ang = spin + a * Math.PI / 3 + k;
          put(r, 'box', vortex[0] + Math.cos(ang) * rad, y + 0.15, vortex[2] + Math.sin(ang) * rad, 0, -ang, 0,
              0.6, 0.3, rad * 0.5, '#ffffff', 0.7);
        }
      }
      put(r, 'cone', vortex[0], w - 4.5, vortex[2], Math.PI, time * 3, 0, 9, 9, 9, '#0a3a4a', 0.85);
      if (client.particles && Math.random() < 0.7) {
        var ang2 = Math.random() * Math.PI * 2, rr = R * (0.3 + Math.random() * 0.7);
        client.particles.spawn({ p: [vortex[0] + Math.cos(ang2) * rr, w + 0.4, vortex[2] + Math.sin(ang2) * rr],
          v: [-Math.sin(ang2) * 8, 3 + Math.random() * 3, Math.cos(ang2) * 8], life: 0.9, size: 0.9, grow: 0.4, gravity: -12,
          spin: 2, blend: 'normal', shape: 'smoke', colors: ['#ffffff', '#c8f4ff'] });
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
      if (twist.on && TWISTS[twist.kind]) bits.push('<b style="color:' + twistInfo(twist.kind).colour + '">' + twistInfo(twist.kind).chip + '</b>');
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
        out.bars.push({ label: twistInfo(twist.kind).chip, value: Math.min(1, left / 30), colour: twistInfo(twist.kind).colour,
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
      if (msg.w === 'bolt') {
        bolts.push({ at: p, t0: t, seed: Math.floor(t * 1000) % 997 });
        rings = rings.filter(function (g) { return Math.hypot(g.at[0] - p[0], g.at[2] - p[2]) > 0.5; });
        var me6 = myPos(), d6 = Math.hypot(me6[0] - p[0], me6[2] - p[2]);
        playAt('pb_thunder', p, 1);
        if (d6 < 60) arena.flashScreen('rgba(220,240,255,' + (0.5 * (1 - d6 / 60)).toFixed(2) + ')', 160);
        if (client.particles) client.particles.burst('explosion', [p[0], p[1] + 0.5, p[2]], { radius: 3 });
        return;
      }
      if (msg.w === 'geyser') {
        columns.push({ at: p, t0: t });
        rings = rings.filter(function (g) { return Math.hypot(g.at[0] - p[0], g.at[2] - p[2]) > 0.5; });
        playAt('pb_geyser', p, 1);
        return;
      }
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
          info = twistInfo(msg.twist);
          arena.banner(info.warn || 'SOMETHING IS COMING', info.warnSub || '', 'bad', 2800);
          client.audio.play('pb_warn', { volume: 0.8 });
        } else if (k === 'twist') {
          info = twistInfo(msg.twist);
          twist.kind = msg.twist || twist.kind;
          twist.on = !!msg.on;
          if (msg.on && msg.left) twist.until = t + msg.left;
          if (msg.on) {
            arena.banner(info.on || 'THE TWIST!', info.onSub || '', 'bad', 3400);
            client.audio.play('pb_twist_' + msg.twist, { volume: 0.9 });
            arena.flashScreen((info.colour || '#ffffff') + '55', 400);
            if (msg.twist === 'eruption' || msg.twist === 'kraken' || msg.twist === 'geysers' || msg.twist === 'maelstrom') {
              shakeUntil = t + 1.2; shakeK = 0.6;
            }
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
        } else if (k === 'bolt') {
          rings.push({ at: msg.at, r: msg.r || 5, t0: t, until: t + (msg['in'] || 1.15), kind: 'bolt' });
          var me5 = myPos();
          if (Math.hypot(me5[0] - msg.at[0], me5[2] - msg.at[2]) < 40) playAt('pb_crackle', msg.at, 0.6);
        } else if (k === 'geyser') {
          rings.push({ at: msg.at, r: msg.r || 5.5, t0: t, until: t + (msg['in'] || 1.7), kind: 'geyser' });
          playAt('pb_hiss', msg.at, 0.7);
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
            arena.banner(msg.kind === 'tentacle' ? 'TENTACLE SEVERED!' : msg.kind === 'skeleton' ? 'SKELETON SHATTERED!' : 'REDCOAT DOWN!',
                         msg.kind === 'tentacle' ? 'It left a jewel behind' : msg.kind === 'skeleton' ? 'It dropped its purse' :
                           'He dropped his purse', 'good', 2200);
          }
          if (nd) playAt(msg.kind === 'tentacle' ? 'pb_kraken' : msg.kind === 'skeleton' ? 'pb_bones' : 'pb_clang', nd.p, 0.8);
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
      // everybody fights with their own hotbar: only a chest or the idol in
      // both hands is the world's own (and it does not fire)
      isCustom: function (stats) { return !!(stats && stats.kind === 'pb_carry'); },
      localFire: function () { return true; },
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
        return false;                     // R reloads your own gun as anywhere else
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
        drawBolts(renderer, time);
        drawColumns(renderer, time);
        drawMaelstrom(renderer, time);
        if (rigs.length && global.Rigs) {
          global.Rigs.draw(rigs, renderer, dt, eye(), rigCtx, (client.map && client.map.fog) || 900);
        }
        stepHold();
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
    GA.register('pb_twist_maelstrom', function (vol) {
      this.noise({ freq: 300, freqEnd: 900, dur: 2.2, gain: 0.3 * vol });
      this.tone({ type: 'sawtooth', freq: 60, freqEnd: 40, dur: 2.0, gain: 0.08 * vol });
    });
    GA.register('pb_twist_storm', function (vol) {
      this.noise({ freq: 160, freqEnd: 60, dur: 2.6, gain: 0.5 * vol });
      this.later(80, function () { this.noise({ filter: 'highpass', freq: 3000, freqEnd: 800, dur: 0.3, gain: 0.3 * vol }); });
    });
    GA.register('pb_twist_geysers', function (vol) {
      this.noise({ filter: 'highpass', freq: 1800, freqEnd: 600, dur: 1.6, gain: 0.3 * vol });
      this.tone({ type: 'sine', freq: 80, freqEnd: 50, dur: 1.4, gain: 0.12 * vol });
    });
    GA.register('pb_twist_ghosts', function (vol) {
      this.tone({ type: 'sine', freq: 220, freqEnd: 180, dur: 2.0, gain: 0.08 * vol });
      this.tone({ type: 'sine', freq: 233, freqEnd: 190, dur: 2.0, gain: 0.07 * vol });
      this.tone({ type: 'triangle', freq: 440, freqEnd: 330, dur: 1.6, gain: 0.04 * vol });
    });
    GA.register('pb_thunder', function (vol) {
      this.noise({ filter: 'highpass', freq: 2600, freqEnd: 700, dur: 0.18, gain: 0.4 * vol });
      this.noise({ freq: 220, freqEnd: 50, dur: 1.8, gain: 0.5 * vol });
      this.tone({ type: 'sawtooth', freq: 48, freqEnd: 30, dur: 1.2, gain: 0.1 * vol });
    });
    GA.register('pb_crackle', function (vol) {
      for (var i = 0; i < 6; i++) {
        this.later(i * 60 + (i * 37 % 40), function () {
          this.noise({ filter: 'highpass', freq: 4200, freqEnd: 2000, dur: 0.04, gain: 0.08 * vol });
        });
      }
    });
    GA.register('pb_hiss', function (vol) {
      this.noise({ filter: 'highpass', freq: 2400, freqEnd: 1200, dur: 1.4, gain: 0.14 * vol });
    });
    GA.register('pb_geyser', function (vol) {
      this.noise({ freq: 500, freqEnd: 1600, dur: 0.4, gain: 0.4 * vol });
      this.noise({ filter: 'highpass', freq: 1400, freqEnd: 500, dur: 2.0, gain: 0.25 * vol });
    });
    GA.register('pb_bones', function (vol) {
      for (var i = 0; i < 7; i++) {
        this.later(i * 45, function () {
          this.tone({ type: 'square', freq: 900 + i * 60, freqEnd: 600, dur: 0.05, gain: 0.04 * vol });
          this.noise({ filter: 'bandpass', freq: 2400, freqEnd: 1600, dur: 0.04, gain: 0.08 * vol });
        });
      }
    });
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

  // ------------------------------------------------ Whalebone Atoll
  /* Looking down the whale's spine from its tail: the ribs arching
     overhead rank on rank, the lagoon either side, the skull at the far
     end with its jaw standing up behind it -- and the lagoon starting to
     turn.  The world is drawn in perspective from a camera 16 up over the
     spine's south end (Z runs away from it, X across, Y up). */
  function wbAt(X, Y, Z) {
    var f = 700 / Math.max(1, Z);
    return [800 + X * f, 330 + (16 - Y) * f, f];
  }
  function wbPoly(ctx, pts, fill) {
    ctx.fillStyle = fill;
    ctx.beginPath();
    pts.forEach(function (p, i) { var q = wbAt(p[0], p[1], p[2]); if (i) ctx.lineTo(q[0], q[1]); else ctx.moveTo(q[0], q[1]); });
    ctx.closePath(); ctx.fill();
  }
  function wbRib(ctx, Z, reach, peak, side) {
    // the same curve the island's ribs follow, on down to the water
    var p0 = [6, 5], p1 = [reach * 0.42, peak * 1.6], p2 = [reach, 5.2];
    var pts = [];
    for (var i = 0; i <= 18; i++) {
      var u = i / 18;
      pts.push([side * ((1 - u) * (1 - u) * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0]),
                (1 - u) * (1 - u) * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]]);
    }
    pts.push([side * reach, -1]);
    var f = 700 / Z;
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    [['#a89c80', 3.0], ['#f4ecd8', 2.2], ['#fffaf0', 0.8]].forEach(function (pass, k) {
      ctx.strokeStyle = pass[0]; ctx.lineWidth = Math.max(1, pass[1] * f);
      ctx.beginPath();
      pts.forEach(function (p, j) {
        var q = wbAt(p[0] + (k === 2 ? -side * 0.5 : 0), p[1] + (k === 2 ? 0.5 : 0), Z);
        if (j) ctx.lineTo(q[0], q[1]); else ctx.moveTo(q[0], q[1]);
      });
      ctx.stroke();
    });
  }

  Intro.register('pb_whalebone', {
    name: 'Whalebone Atoll',
    tagline: 'A whale bigger than any ship, a lagoon in its ribs. Mind the water when it starts to turn.',
    accent: '#3ad0d8',
    cues: [[0.2, 'pb_waves', 0.7], [0.8, 'pb_gull', 0.6], [1.5, 'pb_twist_maelstrom', 0.8], [2.3, 'pb_coins', 0.6],
           [3.3, 'pb_coins', 0.5], [4.4, 'pb_go', 0.6]],
    shakes: [[1.5, 4, 0.6]],
    tagY: 610, tagAt: 3.3,
    setup: function (r) {
      var d = { gulls: [], glints: [], coins: [], foam: [], clouds: [] };
      for (var i = 0; i < 7; i++) d.gulls.push([between(r, 0, VW), between(r, 90, 250), between(r, 30, 70), r() * 6]);
      for (var g = 0; g < 50; g++) d.glints.push([between(r, -60, 60), between(r, 14, 118), r() * 6]);
      for (var c = 0; c < 16; c++) {
        var side = c % 2 ? 1 : -1;
        d.coins.push([side * between(r, 64, 78), between(r, 30, 90), c * 0.14 + r() * 0.1, r() * 6]);
      }
      for (var f = 0; f < 40; f++) d.foam.push([r() * TAU, between(r, 3, 26), r() * 6]);
      for (var k = 0; k < 6; k++) d.clouds.push([between(r, 0, VW), between(r, 60, 230), between(r, 90, 200), r()]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, 340);
      sky.addColorStop(0, '#1468c8'); sky.addColorStop(0.6, '#58b4ee'); sky.addColorStop(1, '#d8f4ff');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, 340);
      additive(ctx, function () { dot(ctx, '#fff4c0', 1290, 110, 200, 0.55); });
      ctx.fillStyle = '#fffbe8'; ctx.beginPath(); ctx.arc(1290, 110, 46, 0, TAU); ctx.fill();
      d.clouds.forEach(function (c) {
        var x = (c[0] + t * 14) % (VW + 300) - 150;
        ctx.fillStyle = 'rgba(255,255,255,0.85)';
        ctx.beginPath(); ctx.ellipse(x, c[1], c[2], c[2] * 0.3, 0, 0, TAU); ctx.ellipse(x + c[2] * 0.4, c[1] - c[2] * 0.15, c[2] * 0.5, c[2] * 0.3, 0, 0, TAU); ctx.fill();
      });
      // the open sea to the horizon, a whale blowing far out
      var seaG = ctx.createLinearGradient(0, 330, 0, 440);
      seaG.addColorStop(0, '#2a8ac8'); seaG.addColorStop(1, '#1a6aa8');
      ctx.fillStyle = seaG; ctx.fillRect(0, 330, VW, 120);
      var blow = seg(t, 0.7, 2.2);
      if (blow > 0 && blow < 1) {
        ctx.fillStyle = '#2a3a4a'; ctx.beginPath(); ctx.ellipse(1460, 338, 26, 6, 0, Math.PI, 0); ctx.fill();
        additive(ctx, function () {
          for (var s = 0; s < 5; s++) dot(ctx, '#ffffff', 1460 + (s - 2) * 4 * blow, 330 - blow * 50 - s * 6, 8 + s * 2, 0.6 * (1 - blow));
        });
      }
      // the two crews' galleons coming round the atoll, far off
      galleon(ctx, lerp(-120, 170, outCubic(seg(t, 0, 3))), 338, 0.16, '#b8282a', '#c8302a', t, 1);
      galleon(ctx, lerp(VW + 120, 1430, outCubic(seg(t, 0.3, 3.3))), 338, 0.16, '#2a5aa8', '#2a6ab8', t, -1);
      // hills behind the north shore, the black rocks either side of the skull
      ctx.fillStyle = '#2e7a52';
      ctx.beginPath(); ctx.moveTo(0, 400); ctx.quadraticCurveTo(300, 250, 640, 330); ctx.quadraticCurveTo(900, 220, 1200, 320); ctx.quadraticCurveTo(1420, 260, VW, 330); ctx.lineTo(VW, 420); ctx.lineTo(0, 420); ctx.fill();
      [-1, 1].forEach(function (s) {
        wbPoly(ctx, [[s * 20, 0, 140], [s * 20, 17, 140], [s * 60, 15, 140], [s * 112, 18, 140], [s * 112, 0, 140]], '#4a4a52');
        wbPoly(ctx, [[s * 20, 17, 140], [s * 60, 15, 140], [s * 112, 18, 140], [s * 112, 19.4, 140], [s * 60, 16.6, 140], [s * 20, 18.4, 140]], '#5a9a4a');
      });
      // the white strand all round, the lagoon in the middle of it
      wbPoly(ctx, [[-140, 0, 140], [140, 0, 140], [140, 0, 8], [-140, 0, 8]], '#f4e8c0');
      var lag = ctx.createLinearGradient(0, 430, 0, VH);
      lag.addColorStop(0, '#5ae0e0'); lag.addColorStop(1, '#2ab8c8');
      wbPoly(ctx, [[-66, -1, 118], [66, -1, 118], [66, -1, 8], [-66, -1, 8]], lag);
      d.glints.forEach(function (g) {
        var q = wbAt(g[0], -0.9, g[1]);
        additive(ctx, function () { dot(ctx, '#ffffff', q[0], q[1], 2 + q[2] * 0.15, 0.3 + 0.4 * Math.sin(t * 4 + g[2])); });
      });
      // palms along the strand
      [[-80, 92], [80, 96], [-84, 112], [86, 110], [-74, 120], [72, 122]].forEach(function (p, i) {
        var q = wbAt(p[0], 0, p[1]);
        palm(ctx, q[0], q[1], 15 * q[2], (i % 2 ? -1 : 1) * 4 * q[2], t);
      });
      // the maelstrom, under the middle of the spine
      var spin = seg(t, 1.5, 2.6);
      if (spin > 0) {
        var eye = 52;
        wbPoly(ctx, (function () { var ring = []; for (var a = 0; a < 24; a++) ring.push([Math.cos(a * TAU / 24) * 26 * spin, -0.95, eye + Math.sin(a * TAU / 24) * 26 * spin]); return ring; })(),
               'rgba(20,110,140,' + (0.45 * spin) + ')');
        ctx.lineCap = 'round';
        for (var arm = 0; arm < 5; arm++) {
          ctx.strokeStyle = 'rgba(240,255,255,' + (0.75 * spin) + ')';
          ctx.beginPath();
          for (var rr = 3; rr <= 26; rr += 1.5) {
            var th = arm * TAU / 5 - t * 2.6 + rr * 0.22;
            var q = wbAt(Math.cos(th) * rr * spin, -0.9, eye + Math.sin(th) * rr * spin);
            ctx.lineWidth = Math.max(1, q[2] * 0.5);
            if (rr === 3) ctx.moveTo(q[0], q[1]); else ctx.lineTo(q[0], q[1]);
          }
          ctx.stroke();
        }
        d.foam.forEach(function (f) {
          var th = f[0] - t * (3.2 - f[1] * 0.06), q = wbAt(Math.cos(th) * f[1] * spin, -0.8, eye + Math.sin(th) * f[1] * spin);
          ctx.fillStyle = 'rgba(255,255,255,' + (0.8 * spin) + ')';
          ctx.beginPath(); ctx.arc(q[0], q[1], Math.max(1.5, q[2] * 0.35), 0, TAU); ctx.fill();
        });
        var c0 = wbAt(0, -0.9, eye);
        ctx.fillStyle = 'rgba(10,40,60,' + (0.8 * spin) + ')';
        ctx.beginPath(); ctx.ellipse(c0[0], c0[1], 5 * c0[2], 1.6 * c0[2], 0, 0, TAU); ctx.fill();
      }
      // the lower jaw standing up behind the skull, toothed
      [-1, 1].forEach(function (s) {
        ctx.strokeStyle = '#e8dcc0'; ctx.lineCap = 'round';
        ctx.beginPath();
        for (var i = 0; i <= 14; i++) {
          var u = i / 14;
          var X = (1 - u) * (1 - u) * 6 * s + 2 * (1 - u) * u * 7 * s + u * u * s;
          var Y = 2 * (1 - u) * u * 30 + u * u * 50, Z = 146 + 2 * (1 - u) * u * 4 + u * u * 11;
          var q = wbAt(X, Y, Z);
          ctx.lineWidth = Math.max(2, (3.2 - 1.6 * u) * q[2]);
          if (i) ctx.lineTo(q[0], q[1]); else ctx.moveTo(q[0], q[1]);
        }
        ctx.stroke();
        ctx.fillStyle = '#fffaf0';
        for (var tooth = 3; tooth < 12; tooth++) {
          var v = tooth / 14;
          var q2 = wbAt(((1 - v) * (1 - v) * 6 + 2 * (1 - v) * v * 7 + v * v) * s - s * 2, 2 * (1 - v) * v * 30 + v * v * 50, 150);
          ctx.beginPath(); ctx.moveTo(q2[0], q2[1] - 4); ctx.lineTo(q2[0] - s * 12, q2[1]); ctx.lineTo(q2[0], q2[1] + 4); ctx.fill();
        }
      });
      // the skull: its front, its stepped dome, the sockets, the toothed door
      wbPoly(ctx, [[-18.6, 14, 118], [18.6, 14, 118], [15.4, 19.6, 121], [-15.4, 19.6, 121]], '#e0d6bc');
      wbPoly(ctx, [[-18, 0, 118], [18, 0, 118], [18, 14, 118], [-18, 14, 118]], '#efe8d6');
      wbPoly(ctx, [[-9, 14, 118.5], [9, 14, 118.5], [9, 12, 117], [-9, 12, 117]], '#d8cfb4');
      var glare = 0.6 + 0.4 * Math.sin(t * 3);
      [-1, 1].forEach(function (s) {
        wbPoly(ctx, [[s * 7.7, 7.8, 118], [s * 13.3, 7.8, 118], [s * 13.3, 11.4, 118], [s * 7.7, 11.4, 118]], '#3a3430');
        var e = wbAt(s * 10.5, 9.6, 118);
        additive(ctx, function () { dot(ctx, '#ffb84a', e[0], e[1], 4 * e[2], 0.5 * glare); });
      });
      wbPoly(ctx, [[-5, 0, 118], [5, 0, 118], [5, 9, 118], [-5, 9, 118]], '#2a2420');
      var idolAt = wbAt(0, 4, 120);
      additive(ctx, function () { dot(ctx, '#ffd040', idolAt[0], idolAt[1], 3 * idolAt[2], 0.7); });
      ctx.fillStyle = '#fffaf0';
      for (var ft = 0; ft < 5; ft++) {
        var a1 = wbAt(-4.6 + ft * 2.3, 9, 118), a2 = wbAt(-3.4 + ft * 2.3, 9, 118), a3 = wbAt(-4.0 + ft * 2.3, 7, 118);
        ctx.beginPath(); ctx.moveTo(a1[0], a1[1]); ctx.lineTo(a2[0], a2[1]); ctx.lineTo(a3[0], a3[1]); ctx.fill();
      }
      // the spine, far to near, each vertebra's top and its face; the ribs
      // in among them (and our pirate on the deck)
      var ribs = [[92, 0], [79, 1], [66, 2], [53, 3], [40, 4], [27, 5], [14, 6]];
      var run = seg(t, 0.3, 4.4), pz = lerp(100, 24, run);
      function runner() {
        var q = wbAt(0, 6.6, pz), s = q[2] / 21.7;
        pirate(ctx, q[0], q[1], s, t, 0, 0, 1);
        // the jewel held up over the head
        var gy = q[1] - 132 * s;
        ctx.fillStyle = '#ff3a6a';
        ctx.beginPath(); ctx.moveTo(q[0] + 24 * s, gy - 14 * s); ctx.lineTo(q[0] + 38 * s, gy); ctx.lineTo(q[0] + 24 * s, gy + 14 * s); ctx.lineTo(q[0] + 10 * s, gy); ctx.fill();
        additive(ctx, function () { dot(ctx, '#ff8ab0', q[0] + 24 * s, gy, 40 * s, 0.6); });
      }
      // painted far to near: a vertebra by its far end (whoever stands on
      // it is drawn after it), a rib by its own plane
      var paint = [[pz, runner]];
      for (var v = 16; v >= 0; v--) {
        (function (v) {
          var z0 = 6 + v * 6.1, z1 = z0 + 5.3;
          paint.push([z1, function () {
            wbPoly(ctx, [[-3, 6, z1], [3, 6, z1], [3, 6, z0], [-3, 6, z0]], v % 2 ? '#efe8d6' : '#e4dcc4');
            wbPoly(ctx, [[-3, 6, z0], [3, 6, z0], [3, -1, z0], [-3, -1, z0]], v % 2 ? '#d8cfb4' : '#cfc5a8');
            [-1, 1].forEach(function (s) {
              wbPoly(ctx, [[s * 3, 5.8, z0 + 1.6], [s * 7.4, 5.8, z0 + 1.6], [s * 7.4, 5.0, z0 + 1.6], [s * 3, 5.0, z0 + 1.6]],
                     '#c8bea2');
            });
          }]);
        })(v);
      }
      ribs.forEach(function (rb) {
        var sw = Math.sin(rb[1] / 6 * Math.PI);
        paint.push([rb[0], function () {
          wbRib(ctx, rb[0], 40 + 8 * sw, 24 + 8 * sw, -1);
          wbRib(ctx, rb[0], 40 + 8 * sw, 24 + 8 * sw, 1);
        }]);
      });
      paint.sort(function (a, b) { return b[0] - a[0]; });
      paint.forEach(function (p) { p[1](); });
      // coins thrown up out of the eye onto the beaches
      if (t > 2.2) {
        d.coins.forEach(function (c) {
          var u = (t - 2.2 - c[2]) / 1.1;
          if (u < 0) return;
          u = Math.min(1, u);
          var X = c[0] * u, Z = 52 + (c[1] - 52) * u, Y = -1 + 30 * u * (1 - u) * 2 + u * 1;
          var q = wbAt(X, Y, Z);
          coin(ctx, q[0], q[1], Math.max(4, 0.9 * q[2]), t * 9 + c[3]);
          if (u >= 1) additive(ctx, function () { dot(ctx, '#ffe080', q[0], q[1], 3 * q[2], 0.4 + 0.3 * Math.sin(t * 6 + c[3])); });
        });
      }
      d.gulls.forEach(function (g) {
        var gx = (g[0] + t * g[2]) % (VW + 100) - 50, gy = g[1] + Math.sin(t * 2 + g[3]) * 10;
        var flap = Math.sin(t * 8 + g[3]) * 8;
        ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(gx - 16, gy - flap); ctx.quadraticCurveTo(gx - 6, gy - 8, gx, gy); ctx.quadraticCurveTo(gx + 6, gy - 8, gx + 16, gy - flap); ctx.stroke();
      });
    },
    title: function (ctx, t, d, run) {
      // a plaque of polished whalebone, scrimshawed: a rope border, a
      // whale and a ship engraved at the ends, the name inked in the middle
      var at = 1.1;
      if (t < at) return;
      var k = outBack(seg(t, at, at + 0.55), 1.3);
      ctx.save();
      ctx.translate(800, 196 - (1 - k) * 380);
      ctx.rotate(0.015 + wobble(t, at + 0.55, 0.025, 10, 5));
      var g = ctx.createLinearGradient(0, -120, 0, 120);
      g.addColorStop(0, '#fffaf0'); g.addColorStop(0.55, '#f0e6cc'); g.addColorStop(1, '#d8c8a0');
      ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.beginPath(); ctx.ellipse(10, 14, 548, 132, 0, 0, TAU); ctx.fill();
      ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(0, 0, 548, 132, 0, 0, TAU); ctx.fill();
      ctx.strokeStyle = 'rgba(150,120,80,0.3)'; ctx.lineWidth = 2;
      for (var gr = 0; gr < 6; gr++) {
        ctx.beginPath(); ctx.ellipse(0, 6, 520 - gr * 30, 112 - gr * 8, 0, 0.3, Math.PI - 0.3); ctx.stroke();
      }
      ctx.strokeStyle = '#1a2a4a'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.ellipse(0, 0, 518, 112, 0, 0, TAU); ctx.stroke();
      ctx.beginPath(); ctx.ellipse(0, 0, 492, 94, 0, 0, TAU); ctx.stroke();
      ctx.lineWidth = 2;
      for (var r2 = 0; r2 < 64; r2++) {
        var a = r2 * TAU / 64;
        ctx.beginPath(); ctx.moveTo(Math.cos(a) * 494, Math.sin(a) * 95); ctx.lineTo(Math.cos(a + 0.06) * 516, Math.sin(a + 0.06) * 111); ctx.stroke();
      }
      // the engravings: a sperm whale on the left, a galleon on the right
      ctx.save(); ctx.translate(-370, 8);
      ctx.beginPath(); ctx.moveTo(-60, -6); ctx.quadraticCurveTo(-58, -30, -20, -30); ctx.lineTo(30, -26);
      ctx.quadraticCurveTo(52, -20, 60, -6); ctx.lineTo(74, -20); ctx.lineTo(70, 0); ctx.lineTo(82, 12); ctx.lineTo(58, 4);
      ctx.quadraticCurveTo(20, 16, -40, 12); ctx.quadraticCurveTo(-62, 10, -60, -6); ctx.stroke();
      ctx.beginPath(); ctx.arc(-44, -14, 2.5, 0, TAU); ctx.fill();
      for (var sp = 0; sp < 3; sp++) { ctx.beginPath(); ctx.moveTo(-46, -32); ctx.quadraticCurveTo(-50 + sp * 6, -52, -58 + sp * 12, -58); ctx.stroke(); }
      for (var h2 = 0; h2 < 5; h2++) { ctx.beginPath(); ctx.moveTo(-40 + h2 * 16, 6); ctx.lineTo(-34 + h2 * 16, 12); ctx.stroke(); }
      ctx.restore();
      ctx.save(); ctx.translate(370, 14);
      ctx.beginPath(); ctx.moveTo(-50, 0); ctx.lineTo(50, 0); ctx.lineTo(40, 16); ctx.lineTo(-40, 16); ctx.closePath(); ctx.stroke();
      [[-24, 50], [6, 62], [32, 44]].forEach(function (m) {
        ctx.beginPath(); ctx.moveTo(m[0], 0); ctx.lineTo(m[0], -m[1]); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(m[0] - 14, -m[1] + 8); ctx.quadraticCurveTo(m[0] + 4, -m[1] + 18, m[0] - 14, -m[1] + 30); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(m[0] + 14, -m[1] + 8); ctx.quadraticCurveTo(m[0] - 4, -m[1] + 18, m[0] + 14, -m[1] + 30); ctx.stroke();
      });
      ctx.beginPath(); ctx.moveTo(-70, 24); ctx.quadraticCurveTo(-35, 18, 0, 24); ctx.quadraticCurveTo(35, 30, 70, 24); ctx.stroke();
      ctx.restore();
      ctx.globalAlpha = run.alpha;
      ctx.font = 'bold 24px ' + HEAVY; ctx.textAlign = 'center'; ctx.fillStyle = '#8a2a1a';
      ctx.fillText('PLUNDER BAY', 0, -48);
      titleText(ctx, (run.info.name || 'Whalebone Atoll').toUpperCase(), 0, 18, 620, 90, '#1a2a4a', null);
      var ink = seg(t, at + 0.5, at + 1.5);
      if (ink > 0 && ink < 1) {
        additive(ctx, function () {
          var sx = lerp(-520, 520, ink);
          var sg = ctx.createLinearGradient(sx - 90, 0, sx + 90, 0);
          sg.addColorStop(0, 'rgba(255,255,255,0)'); sg.addColorStop(0.5, 'rgba(255,255,240,0.45)'); sg.addColorStop(1, 'rgba(255,255,255,0)');
          ctx.fillStyle = sg; ctx.fillRect(sx - 90, -130, 180, 260);
        });
      }
      ctx.restore();
    }
  });

  // ------------------------------------------------ Thunderhead Rock
  /* A jagged bolt from (x0, y0) down to (x1, y1), forked, fixed by its
     seed for the moment it lives. */
  function thBolt(ctx, x0, y0, x1, y1, seed, power) {
    var pts = [[x0, y0]];
    for (var i = 1; i < 12; i++) {
      var f = i / 12;
      pts.push([lerp(x0, x1, f) + (hash(seed + i) - 0.5) * 70 * (1 - f * 0.5), lerp(y0, y1, f)]);
    }
    pts.push([x1, y1]);
    additive(ctx, function () {
      [[18, 'rgba(140,170,255,' + (0.25 * power) + ')'], [7, 'rgba(200,220,255,' + (0.7 * power) + ')'],
       [3, 'rgba(255,255,255,' + power + ')']].forEach(function (pass) {
        ctx.strokeStyle = pass[1]; ctx.lineWidth = pass[0]; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
        ctx.beginPath();
        pts.forEach(function (p, j) { if (j) ctx.lineTo(p[0], p[1]); else ctx.moveTo(p[0], p[1]); });
        var k = 4 + Math.floor(hash(seed * 3) * 4);
        ctx.moveTo(pts[k][0], pts[k][1]);
        ctx.lineTo(pts[k][0] + 90 * (hash(seed * 5) - 0.3), pts[k][1] + 80);
        ctx.lineTo(pts[k][0] + 130 * (hash(seed * 5) - 0.3), pts[k][1] + 150);
        ctx.stroke();
      });
      dot(ctx, '#c8d8ff', x1, y1, 90, 0.7 * power);
    });
  }

  Intro.register('pb_thunderhead', {
    name: 'Thunderhead Rock',
    tagline: 'A lighthouse on a rock in a storm. The lightning goes for whoever is carrying gold.',
    accent: '#8ab8ff',
    cues: [[0.1, 'pb_waves', 0.8], [1.0, 'pb_twist_storm', 0.6], [1.3, 'pb_thunder', 0.9], [2.4, 'pb_crackle', 0.7],
           [3.0, 'pb_thunder', 1.0], [4.4, 'pb_go', 0.6]],
    shakes: [[1.3, 6, 0.4], [3.0, 10, 0.5]],
    tagY: 612, tagAt: 3.4,
    setup: function (r) {
      var d = { rain: [], clouds: [], spray: [] };
      for (var i = 0; i < 160; i++) d.rain.push([r() * VW, r() * VH, between(r, 0.6, 1.2)]);
      for (var c = 0; c < 9; c++) d.clouds.push([between(r, -200, VW), between(r, 40, 260), between(r, 160, 340), r()]);
      for (var s = 0; s < 30; s++) d.spray.push([between(r, -1, 1), between(r, 0.4, 1), r()]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, 560);
      sky.addColorStop(0, '#16122a'); sky.addColorStop(0.55, '#40345e'); sky.addColorStop(1, '#8a7aa2');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      d.clouds.forEach(function (c, i) {
        var x = (c[0] + t * (12 + i * 3)) % (VW + 400) - 200;
        ctx.fillStyle = i % 2 ? 'rgba(30,24,50,0.75)' : 'rgba(50,40,76,0.7)';
        ctx.beginPath(); ctx.ellipse(x, c[1], c[2], c[2] * 0.26, 0, 0, TAU);
        ctx.ellipse(x + c[2] * 0.5, c[1] + 18, c[2] * 0.6, c[2] * 0.2, 0, 0, TAU); ctx.fill();
      });
      // the lighthouse's beam sweeping round over the sea
      var beam = Math.sin(t * 1.3) * 1.1;
      additive(ctx, function () {
        var g = ctx.createLinearGradient(800, 288, 800 + Math.cos(beam) * 900, 288 + Math.sin(beam) * 120);
        g.addColorStop(0, 'rgba(255,240,180,0.45)'); g.addColorStop(1, 'rgba(255,240,180,0)');
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.moveTo(800, 288);
        ctx.lineTo(800 + Math.cos(beam - 0.08) * 1000, 288 + Math.sin(beam - 0.08) * 300);
        ctx.lineTo(800 + Math.cos(beam + 0.08) * 1000, 288 + Math.sin(beam + 0.08) * 300); ctx.fill();
        ctx.beginPath(); ctx.moveTo(800, 288);
        ctx.lineTo(800 - Math.cos(beam - 0.08) * 1000, 288 - Math.sin(beam - 0.08) * 300);
        ctx.lineTo(800 - Math.cos(beam + 0.08) * 1000, 288 - Math.sin(beam + 0.08) * 300); ctx.fill();
      });
      // the sea, heaving, and the mesa standing out of it, ribbed in columns
      waves(ctx, 520, '#2a3e58', t, 12, 1.6, 1);
      ctx.fillStyle = '#2c2a3a';
      ctx.fillRect(520, 372, 560, 220);
      for (var col = 0; col < 28; col++) {
        ctx.fillStyle = col % 2 ? '#34324a' : '#262434';
        ctx.fillRect(522 + col * 20, 380 + (col % 3) * 4, 12, 210);
      }
      ctx.fillStyle = '#4a6a44'; ctx.fillRect(516, 364, 568, 12);
      [[470, 400, 70], [1130, 410, 60], [430, 450, 50], [1180, 455, 54]].forEach(function (s) {
        ctx.fillStyle = '#2a2836'; ctx.fillRect(s[0] - s[2] / 2, s[1], s[2], 600 - s[1]);
        ctx.fillStyle = '#3a3850'; ctx.fillRect(s[0] - s[2] / 2, s[1], s[2], 8);
      });
      // the lighthouse: white and red, the lamp lit, the rod on its cap
      ctx.fillStyle = '#f4f0e8'; ctx.beginPath(); ctx.moveTo(778, 366); ctx.lineTo(788, 300); ctx.lineTo(812, 300); ctx.lineTo(822, 366); ctx.fill();
      ctx.fillStyle = '#c8302a';
      [[312, 322], [334, 344], [356, 366]].forEach(function (b2) {
        var w0 = lerp(12, 22, (b2[0] - 300) / 66), w1 = lerp(12, 22, (b2[1] - 300) / 66);
        ctx.beginPath(); ctx.moveTo(800 - w0, b2[0]); ctx.lineTo(800 + w0, b2[0]); ctx.lineTo(800 + w1, b2[1]); ctx.lineTo(800 - w1, b2[1]); ctx.fill();
      });
      ctx.fillStyle = '#3a3a40'; ctx.fillRect(782, 296, 36, 5);
      ctx.fillStyle = '#fff4c0'; ctx.fillRect(790, 280, 20, 16);
      additive(ctx, function () { dot(ctx, '#fff0a0', 800, 288, 50, 0.8); });
      ctx.fillStyle = '#c8302a'; ctx.beginPath(); ctx.moveTo(786, 281); ctx.lineTo(800, 266); ctx.lineTo(814, 281); ctx.fill();
      ctx.strokeStyle = '#3a3a40'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(800, 266); ctx.lineTo(800, 248); ctx.stroke();
      // spray bursting over the rocks either side
      d.spray.forEach(function (s, i) {
        var age = (t * 0.9 + s[2]) % 1, side = i % 2 ? 1 : -1;
        var x = 800 + side * (360 + s[0] * 60) + side * age * 60 * s[1], y = 520 - Math.sin(age * Math.PI) * 140 * s[1];
        ctx.fillStyle = 'rgba(230,240,255,' + (0.7 * (1 - age)) + ')';
        ctx.beginPath(); ctx.arc(x, y, 6 + age * 14, 0, TAU); ctx.fill();
      });
      // the causeway: columns stepping down towards us, row on row
      var run = seg(t, 0.4, 4.4);
      var px = lerp(820, 740, run), py = lerp(600, 812, outCubic(run)), ps = lerp(0.42, 1.05, run);
      var drawnRunner = false;
      for (var row = 0; row < 7; row++) {
        var y = 590 + row * 46 + row * row * 3.4, rx = 34 + row * 13, ry = rx * 0.4;
        var nextY = 590 + (row + 1) * 46 + (row + 1) * (row + 1) * 3.4;
        var n = Math.ceil(VW / (rx * 1.5)) + 2;
        for (var k = -1; k < n; k++) {
          var x = 800 + (k - n / 2) * rx * 1.5 + (row % 2) * rx * 0.75;
          var yy = y + (hash(row * 31 + k) - 0.5) * 10;
          ctx.fillStyle = (row + k) % 3 === 0 ? '#2a2834' : '#323040';
          ctx.fillRect(x - rx, yy, rx * 2, 260);
          ctx.fillStyle = (row * 7 + k) % 5 === 0 ? '#5a8a4a' : ((row + k) % 2 ? '#4a4a5c' : '#55556a');
          ctx.beginPath();
          for (var e = 0; e < 6; e++) {
            var a = e * Math.PI / 3;
            var hx = x + Math.cos(a) * rx, hy = yy + Math.sin(a) * ry;
            if (e) ctx.lineTo(hx, hy); else ctx.moveTo(hx, hy);
          }
          ctx.closePath(); ctx.fill();
          ctx.strokeStyle = 'rgba(20,18,30,0.8)'; ctx.lineWidth = 2; ctx.stroke();
        }
        // the warning ring, then the strike, on the column the pirate has just left
        if (row === 3 && t > 2.4 && t < 3.6) {
          var ringA = t < 3.0 ? 0.5 + 0.5 * Math.sin(t * 20) : Math.max(0, 1 - (t - 3.0) * 2);
          ctx.strokeStyle = 'rgba(140,190,255,' + ringA + ')'; ctx.lineWidth = 5;
          ctx.beginPath(); ctx.ellipse(800, y, 70, 26, 0, 0, TAU); ctx.stroke();
        }
        // he stands on this row's columns: drawn over them, under the nearer rows
        if (!drawnRunner && py < nextY) { pirate(ctx, px, py, ps, t, 0, 0, -1); drawnRunner = true; }
      }
      // a gold bar in his arms: the lightning's favourite
      // (drawn with the pirate, above his head)
      ctx.fillStyle = '#ffc830';
      ctx.fillRect(px - 26 * ps, py - 140 * ps, 52 * ps, 18 * ps);
      additive(ctx, function () { dot(ctx, '#ffe080', px, py - 131 * ps, 36 * ps, 0.5); });
      // the strikes: the lighthouse's rod, then the causeway behind him
      if (t > 1.3 && t < 1.75) thBolt(ctx, 690, -20, 800, 248, 11, 1 - (t - 1.3) / 0.45);
      if (t > 3.0 && t < 3.5) thBolt(ctx, 980, -20, 800, 724, 29, 1 - (t - 3.0) / 0.5);
      var flash = Math.max(t > 1.3 ? Math.max(0, 1 - (t - 1.3) * 3) : 0, t > 3.0 ? Math.max(0, 1 - (t - 3.0) * 2.5) : 0);
      if (flash > 0) { ctx.fillStyle = 'rgba(220,225,255,' + (0.55 * flash) + ')'; ctx.fillRect(0, 0, VW, VH); }
      // the rain over everything
      ctx.strokeStyle = 'rgba(200,210,240,0.35)'; ctx.lineWidth = 2;
      ctx.beginPath();
      d.rain.forEach(function (r2) {
        var x = (r2[0] + t * 260 * r2[2]) % VW, y = (r2[1] + t * 1300 * r2[2]) % VH;
        ctx.moveTo(x, y); ctx.lineTo(x - 10, y - 34);
      });
      ctx.stroke();
    },
    title: function (ctx, t, d, run) {
      // a slab of slate, brass-riveted, the name burning in it in storm-light
      // -- it flickers on with the first strike
      var at = 1.0;
      if (t < at) return;
      var k = outBack(seg(t, at, at + 0.45), 1.4);
      ctx.save();
      ctx.translate(800, 168 - (1 - k) * 320);
      ctx.rotate(-0.012 + wobble(t, at + 0.45, 0.02, 12, 6));
      var g = ctx.createLinearGradient(0, -95, 0, 95);
      g.addColorStop(0, '#4a4858'); g.addColorStop(1, '#2a2834');
      ctx.fillStyle = 'rgba(0,0,0,0.35)'; roundRect(ctx, -490, -84, 1000, 190, 14); ctx.fill();
      ctx.fillStyle = g; roundRect(ctx, -500, -95, 1000, 190, 14); ctx.fill();
      ctx.strokeStyle = '#6a6878'; ctx.lineWidth = 3; roundRect(ctx, -480, -78, 960, 156, 8); ctx.stroke();
      ctx.fillStyle = '#c88a3a';
      [[-474, -72], [474, -72], [-474, 72], [474, 72]].forEach(function (p) {
        ctx.beginPath(); ctx.arc(p[0], p[1], 8, 0, TAU); ctx.fill();
      });
      ctx.globalAlpha = run.alpha;
      ctx.font = 'bold 22px ' + HEAVY; ctx.textAlign = 'center'; ctx.fillStyle = '#c88a3a';
      ctx.fillText('PLUNDER BAY', 0, -44);
      var lit = t < 1.3 ? 0.15 : (t < 1.6 ? (Math.sin(t * 90) > 0 ? 1 : 0.25) : 0.85 + 0.15 * Math.sin(t * 7));
      var name = (run.info.name || 'Thunderhead Rock').toUpperCase();
      titleText(ctx, name, 0, 18, 820, 84, lit > 0.5 ? '#e8f2ff' : '#6a7a98', '#1a1830', 8);
      if (lit > 0.5) {
        additive(ctx, function () {
          ctx.globalAlpha = 0.55 * lit * run.alpha;
          titleText(ctx, name, 0, 18, 820, 84, '#7ab8ff', null);
          ctx.globalAlpha = run.alpha;
        });
      }
      // sparks running round the border
      if (t > 1.3) {
        var per = 2 * (960 + 156);
        for (var sp = 0; sp < 3; sp++) {
          var u = ((t - 1.3) * 900 + sp * per / 3) % per, sx, sy;
          if (u < 960) { sx = -480 + u; sy = -78; } else if (u < 1116) { sx = 480; sy = -78 + (u - 960); }
          else if (u < 2076) { sx = 480 - (u - 1116); sy = 78; } else { sx = -480; sy = 78 - (u - 2076); }
          additive(ctx, function () { dot(ctx, '#9ad8ff', sx, sy, 22, 0.9); dot(ctx, '#ffffff', sx, sy, 6, 1); });
        }
      }
      ctx.restore();
    }
  });

  // ------------------------------------------------ Sulphur Springs
  Intro.register('pb_sulphur', {
    name: 'Sulphur Springs',
    tagline: 'White terraces, steaming pools, a spring in every colour. Do not stand on the geysers.',
    accent: '#3ad0e0',
    cues: [[0.2, 'pb_hiss', 0.6], [0.9, 'pb_gull', 0.5], [1.5, 'pb_twist_geysers', 0.7], [1.7, 'pb_geyser', 0.9],
           [2.4, 'pb_coins', 0.6], [3.4, 'pb_hiss', 0.5], [4.4, 'pb_go', 0.6]],
    shakes: [[1.7, 6, 0.5]],
    tagY: 612, tagAt: 3.3,
    setup: function (r) {
      var d = { steam: [], coins: [], drops: [], clouds: [] };
      for (var i = 0; i < 26; i++) d.steam.push([between(r, 140, 1460), between(r, 300, 520), r() * 6, between(r, 0.6, 1.3)]);
      for (var c = 0; c < 14; c++) d.coins.push([between(r, -1, 1), between(r, 0.6, 1.2), c * 0.08 + r() * 0.08, r() * 6]);
      for (var k = 0; k < 40; k++) d.drops.push([between(r, -1, 1), between(r, 0.3, 1), r()]);
      for (var q = 0; q < 5; q++) d.clouds.push([between(r, 0, VW), between(r, 60, 180), between(r, 120, 220)]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, 420);
      sky.addColorStop(0, '#2a7ac8'); sky.addColorStop(1, '#f4e8c8');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      d.clouds.forEach(function (c) {
        var x = (c[0] + t * 10) % (VW + 300) - 150;
        ctx.fillStyle = 'rgba(255,255,255,0.8)';
        ctx.beginPath(); ctx.ellipse(x, c[1], c[2], c[2] * 0.28, 0, 0, TAU); ctx.fill();
      });
      // the volcano far off, smoking; green hills
      ctx.fillStyle = '#6a5a4a';
      ctx.beginPath(); ctx.moveTo(140, 400); ctx.lineTo(330, 170); ctx.lineTo(380, 170); ctx.lineTo(600, 400); ctx.fill();
      for (var p = 0; p < 7; p++) {
        ctx.fillStyle = 'rgba(220,214,206,' + (0.7 - p * 0.08) + ')';
        ctx.beginPath(); ctx.arc(355 + Math.sin(t + p) * 8 + p * 12, 150 - p * 26 - (t * 10 % 26), 20 + p * 7, 0, TAU); ctx.fill();
      }
      ctx.fillStyle = '#4a8a3a';
      ctx.beginPath(); ctx.moveTo(0, 420); ctx.quadraticCurveTo(400, 300, 800, 360); ctx.quadraticCurveTo(1200, 280, VW, 380); ctx.lineTo(VW, 460); ctx.lineTo(0, 460); ctx.fill();
      // the terraces, four white steps, pools brimming on each; the
      // bathhouse's columns on top, the gilt governor among them
      var tiers = [[1300, 240, 470], [1120, 210, 430], [920, 180, 392], [700, 150, 356]];
      tiers.forEach(function (tr, i) {
        var w = tr[0], top = tr[2], x0 = 800 - w / 2;
        ctx.fillStyle = i % 2 ? '#e4d8bc' : '#f2ead8';
        ctx.fillRect(x0, top, w, 500 - top);
        ctx.fillStyle = '#cdbd9c';
        for (var f = 0; f < w / 30; f++) ctx.fillRect(x0 + f * 30 + 6, top + 6, 14, 10 + (f * 7 % 5) * 5);
        for (var pl = 0; pl < 3 + i % 2; pl++) {
          var px = x0 + 60 + pl * (w - 120) / (2 + i % 2);
          ctx.fillStyle = '#e4d8bc'; ctx.fillRect(px - 44, top - 8, 88, 10);
          ctx.fillStyle = '#5ae0ec'; ctx.fillRect(px - 38, top - 6, 76, 6);
        }
      });
      for (var cl = 0; cl < 8; cl++) {
        var cx2 = 590 + cl * 60, h = cl % 3 === 1 ? 36 : 86;
        ctx.fillStyle = '#f4f0e4'; ctx.fillRect(cx2 - 8, 356 - h, 16, h);
        ctx.fillStyle = '#e0d4b8'; ctx.fillRect(cx2 - 12, 356 - h - 8, 24, 8);
      }
      ctx.fillStyle = '#e8b830'; ctx.fillRect(792, 290, 16, 46); ctx.fillRect(788, 278, 24, 14);
      // the steam off the pools, drifting
      d.steam.forEach(function (s) {
        var age = (t * 0.3 * s[3] + s[2] / 6) % 1;
        ctx.fillStyle = 'rgba(255,255,255,' + (0.5 * (1 - age)) + ')';
        ctx.beginPath(); ctx.arc(s[0] + age * 30, s[1] - age * 120, 14 + age * 30, 0, TAU); ctx.fill();
      });
      // the green below, and the grand spring: rings from red to deep blue
      ctx.fillStyle = '#7aa040'; ctx.fillRect(0, 500, VW, 400);
      ctx.fillStyle = '#f2ead8';
      ctx.beginPath(); ctx.ellipse(800, 720, 620, 170, 0, 0, TAU); ctx.fill();
      ['#c8402a', '#e8702a', '#f0a030', '#e8d040', '#7ac85a', '#3ab8b0', '#1a6ab8'].forEach(function (c, i) {
        var k = 1 - i * 0.13;
        ctx.fillStyle = c;
        ctx.beginPath(); ctx.ellipse(800, 720, 580 * k, 150 * k, 0, 0, TAU); ctx.fill();
      });
      additive(ctx, function () { dot(ctx, '#ffffff', 800, 720, 300, 0.12, 80); });
      // the boardwalk across it
      ctx.fillStyle = '#a8805a'; ctx.fillRect(0, 770, VW, 20);
      ctx.fillStyle = '#6a4a2e';
      for (var bp = 0; bp < 20; bp++) ctx.fillRect(bp * 84 + 10, 790, 8, 40);
      // Old Faithless blows: a column of boiling water, a Buccaneer thrown
      // up on it, treasure flying out of it
      var blow = seg(t, 1.6, 1.9), fall = seg(t, 3.4, 4.2);
      var colH = 520 * blow * (1 - fall);
      if (t > 1.2 && t < 1.6) {
        ctx.strokeStyle = 'rgba(255,255,255,' + (0.5 + 0.5 * Math.sin(t * 30)) + ')'; ctx.lineWidth = 6;
        ctx.beginPath(); ctx.ellipse(800, 720, 90, 26, 0, 0, TAU); ctx.stroke();
      }
      if (colH > 4) {
        var g = ctx.createLinearGradient(0, 720 - colH, 0, 720);
        g.addColorStop(0, 'rgba(255,255,255,0.95)'); g.addColorStop(1, 'rgba(160,230,245,0.85)');
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.moveTo(740, 720);
        for (var yy = 0; yy <= 10; yy++) {
          var ff = yy / 10;
          ctx.lineTo(760 - ff * 30 + Math.sin(t * 20 + yy) * 8, 720 - colH * ff);
        }
        ctx.quadraticCurveTo(800, 720 - colH - 70, 870, 720 - colH);
        for (yy = 10; yy >= 0; yy--) {
          var f2 = yy / 10;
          ctx.lineTo(840 + f2 * 30 + Math.sin(t * 18 + yy) * 8, 720 - colH * f2);
        }
        ctx.closePath(); ctx.fill();
        d.drops.forEach(function (dr) {
          var age = (t * 1.6 + dr[2]) % 1;
          var x = 800 + dr[0] * 260 * age, y = 720 - colH - 30 + 420 * age * age - 200 * dr[1] * age;
          ctx.fillStyle = 'rgba(230,250,255,' + (1 - age) + ')';
          ctx.beginPath(); ctx.arc(x, y, 6, 0, TAU); ctx.fill();
        });
      }
      // the Buccaneer tossed into the air, tumbling
      var up = seg(t, 1.7, 2.6), down = seg(t, 2.6, 3.6);
      var by = 700 - 420 * Math.sin(up * Math.PI / 2) + 420 * down * down;
      var bx = 820 + down * 300;
      if (t > 1.7 && by < 800) {
        ctx.save(); ctx.translate(bx, by); ctx.rotate(t * 5);
        pirate(ctx, 0, 60, 0.7, t, 0, 0, -1);
        ctx.restore();
      }
      if (t <= 1.7) pirate(ctx, 820, 768, 0.75, t, 0, 0, -1);
      // treasure out of the geyser
      if (t > 2.0) {
        d.coins.forEach(function (c) {
          var u = (t - 2.0 - c[2]) / 1.2;
          if (u < 0 || u > 1.4) return;
          var x = 800 + c[0] * 520 * Math.min(u, 1), y = 300 - c[1] * 120 * u + 330 * u * u;
          if (y > 760) y = 760;
          coin(ctx, x, y, 12, t * 9 + c[3]);
        });
      }
      // our Corsair running the boardwalk with a chest
      var run2 = seg(t, 0.3, 4.4);
      var cx3 = lerp(120, 560, run2);
      pirate(ctx, cx3, 768, 1.0, t, 0, 0);
      ctx.fillStyle = '#7a4a26'; ctx.fillRect(cx3 - 34, 640, 68, 40);
      ctx.fillStyle = '#d8b040'; ctx.fillRect(cx3 - 34, 640, 68, 8); ctx.fillRect(cx3 - 6, 640, 12, 40);
    },
    title: function (ctx, t, d, run) {
      // a marble plaque from the bathhouse wall: a mosaic border of blue
      // and gold, the name in deep blue picked out in gold
      var at = 1.0;
      if (t < at) return;
      var k = outBack(seg(t, at, at + 0.5), 1.3);
      ctx.save();
      ctx.translate(800, 176 - (1 - k) * 340);
      ctx.rotate(0.01 + wobble(t, at + 0.5, 0.02, 10, 5));
      ctx.fillStyle = 'rgba(0,0,0,0.25)'; roundRect(ctx, -490, -82, 1000, 184, 10); ctx.fill();
      var g = ctx.createLinearGradient(0, -92, 0, 92);
      g.addColorStop(0, '#fffaf0'); g.addColorStop(1, '#e8dcc4');
      ctx.fillStyle = g; roundRect(ctx, -500, -92, 1000, 184, 10); ctx.fill();
      for (var tx = 0; tx < 62; tx++) {
        var c2 = tx % 4 === 0 ? '#e8b830' : (tx % 2 ? '#2a6ab8' : '#1a4a8a');
        ctx.fillStyle = c2;
        ctx.fillRect(-488 + tx * 15.8, -84, 12, 12); ctx.fillRect(-488 + tx * 15.8, 72, 12, 12);
      }
      for (var ty = 0; ty < 9; ty++) {
        var c3 = ty % 4 === 0 ? '#e8b830' : (ty % 2 ? '#2a6ab8' : '#1a4a8a');
        ctx.fillStyle = c3;
        ctx.fillRect(-488, -66 + ty * 15.6, 12, 12); ctx.fillRect(476, -66 + ty * 15.6, 12, 12);
      }
      ctx.globalAlpha = run.alpha;
      ctx.font = 'bold 22px ' + HEAVY; ctx.textAlign = 'center'; ctx.fillStyle = '#c8302a';
      ctx.fillText('PLUNDER BAY', 0, -40);
      titleText(ctx, (run.info.name || 'Sulphur Springs').toUpperCase(), 0, 20, 820, 86, '#1a4a8a', '#e8b830', 6);
      // steam drifting across it
      for (var s2 = 0; s2 < 5; s2++) {
        var sx = -560 + ((t - at) * 140 + s2 * 260) % 1160;
        ctx.fillStyle = 'rgba(255,255,255,0.35)';
        ctx.beginPath(); ctx.ellipse(sx, 60 - s2 * 22, 90, 26, 0, 0, TAU); ctx.fill();
      }
      ctx.restore();
    }
  });

  // ------------------------------------------------ Ghost Fleet Cove
  /* A skeleton of the ghost crews, side on, climbing up out of the water:
     ``rise`` 0..1 how far out, ``aim`` raising the pistol. */
  function gfSkeleton(ctx, x, y, s, rise, aim, t, face) {
    ctx.save();
    ctx.translate(x, y + (1 - rise) * 120 * s);
    ctx.scale(s * (face || 1), s);
    ctx.strokeStyle = '#e8e4d4'; ctx.lineCap = 'round';
    ctx.lineWidth = 6;
    ctx.beginPath(); ctx.moveTo(0, -40); ctx.lineTo(0, -80); ctx.stroke();
    ctx.lineWidth = 4;
    for (var r = 0; r < 4; r++) { ctx.beginPath(); ctx.moveTo(-12, -74 + r * 8); ctx.quadraticCurveTo(0, -70 + r * 8, 12, -74 + r * 8); ctx.stroke(); }
    ctx.lineWidth = 5;
    ctx.beginPath(); ctx.moveTo(-6, -40); ctx.lineTo(-10 + Math.sin(t * 6) * 4, 0); ctx.moveTo(6, -40); ctx.lineTo(10 - Math.sin(t * 6) * 4, 0); ctx.stroke();
    var arm = -0.4 - aim * 1.1;
    ctx.save(); ctx.translate(10, -78); ctx.rotate(arm);
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 34); ctx.stroke();
    ctx.fillStyle = '#4a4e56'; ctx.fillRect(-4, 30, 8, 22);
    ctx.restore();
    ctx.beginPath(); ctx.moveTo(-10, -78); ctx.lineTo(-18, -50); ctx.stroke();
    ctx.fillStyle = '#4a3a2a';
    ctx.beginPath(); ctx.moveTo(-16, -84); ctx.lineTo(16, -84); ctx.lineTo(18, -52); ctx.lineTo(-18, -52); ctx.closePath();
    ctx.globalAlpha = 0.55; ctx.fill(); ctx.globalAlpha = 1;
    ctx.fillStyle = '#e8e4d4'; ctx.beginPath(); ctx.arc(0, -96, 13, 0, TAU); ctx.fill();
    ctx.fillRect(-7, -88, 14, 8);
    ctx.fillStyle = '#1a1a22';
    ctx.beginPath(); ctx.moveTo(-18, -104); ctx.quadraticCurveTo(0, -124, 18, -104); ctx.fill();
    additive(ctx, function () {
      dot(ctx, '#7aff9a', -5, -97, 6, 0.9); dot(ctx, '#7aff9a', 5, -97, 6, 0.9);
    });
    ctx.fillStyle = '#7aff9a'; ctx.fillRect(-6, -99, 3, 3); ctx.fillRect(3, -99, 3, 3);
    ctx.restore();
  }

  Intro.register('pb_ghostfleet', {
    name: 'Ghost Fleet Cove',
    tagline: 'A cove full of wrecks under the moon. When the fog comes up, so do their crews.',
    accent: '#7aff9a',
    cues: [[0.2, 'pb_waves', 0.6], [1.2, 'pb_twist_ghosts', 0.8], [1.8, 'pb_bones', 0.7], [2.3, 'pb_bones', 0.6],
           [3.0, 'pb_pistol', 0.7], [3.2, 'pb_pistol', 0.6], [4.4, 'pb_go', 0.6]],
    shakes: [],
    tagY: 612, tagAt: 3.4,
    setup: function (r) {
      var d = { stars: makeStars(r, 90, 0, 360), wisps: [], fog: [] };
      for (var i = 0; i < 14; i++) d.wisps.push([between(r, 0, VW), between(r, 300, 640), r() * 6, between(r, 0.4, 1)]);
      for (var f = 0; f < 18; f++) d.fog.push([between(r, -200, VW), between(r, 560, 760), between(r, 160, 320), r()]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, 560);
      sky.addColorStop(0, '#060a1e'); sky.addColorStop(0.7, '#1c2a4a'); sky.addColorStop(1, '#34486e');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      stars(ctx, d.stars, t, 0.8);
      // the full moon, ringed, low over the cove
      additive(ctx, function () { dot(ctx, '#d8e8ff', 980, 250, 260, 0.35); });
      ctx.fillStyle = '#eef2e4'; ctx.beginPath(); ctx.arc(980, 250, 110, 0, TAU); ctx.fill();
      ctx.fillStyle = 'rgba(180,190,170,0.5)';
      [[950, 220, 22], [1020, 280, 16], [990, 300, 10], [940, 290, 12]].forEach(function (c) { ctx.beginPath(); ctx.arc(c[0], c[1], c[2], 0, TAU); ctx.fill(); });
      // the graveyard hill on the left, the crypt and its ghost-light
      ctx.fillStyle = '#1a2620';
      ctx.beginPath(); ctx.moveTo(0, 560); ctx.lineTo(0, 380); ctx.lineTo(120, 360); ctx.lineTo(260, 330); ctx.lineTo(420, 360); ctx.lineTo(560, 470); ctx.lineTo(560, 560); ctx.fill();
      ctx.fillStyle = '#4a4a56'; ctx.fillRect(210, 290, 90, 50);
      ctx.beginPath(); ctx.moveTo(200, 292); ctx.lineTo(255, 262); ctx.lineTo(310, 292); ctx.fill();
      additive(ctx, function () {
        var g = ctx.createLinearGradient(0, 0, 0, 290);
        g.addColorStop(0, 'rgba(122,255,154,0)'); g.addColorStop(1, 'rgba(122,255,154,0.35)');
        ctx.fillStyle = g; ctx.fillRect(240, 0, 30, 290);
      });
      ctx.fillStyle = '#3a3a44';
      for (var gs = 0; gs < 12; gs++) {
        var gx = 40 + gs * 40, gy = 400 + Math.abs(gs - 6) * 9;
        ctx.fillRect(gx, gy - 18, 12, 18);
        if (gs % 3 === 0) ctx.fillRect(gx - 5, gy - 13, 22, 4);
      }
      // the water of the cove
      waves(ctx, 520, '#14283a', t, 6, 0.8, 1);
      // the flagship, sunk to her gunwales: black against the moon, rags of
      // sail, her stern windows lit green
      ctx.fillStyle = '#100e0c';
      ctx.beginPath(); ctx.moveTo(700, 520); ctx.lineTo(720, 470); ctx.lineTo(1260, 470); ctx.lineTo(1300, 410); ctx.lineTo(1320, 420); ctx.lineTo(1300, 520); ctx.fill();
      ctx.fillRect(1180, 400, 120, 72);
      [[820, 230], [1000, 170], [1200, 250]].forEach(function (m, i) {
        ctx.fillRect(m[0] - 5, m[1], 10, 470 - m[1]);
        ctx.fillRect(m[0] - 70, m[1] + 30, 140, 6);
        ctx.fillStyle = 'rgba(170,200,170,0.28)';
        for (var rag = 0; rag < 4; rag++) {
          if (rag === 2) continue;
          var rx = m[0] - 64 + rag * 34;
          ctx.beginPath(); ctx.moveTo(rx, m[1] + 36); ctx.lineTo(rx + 28, m[1] + 36);
          ctx.lineTo(rx + 24 + Math.sin(t * 2 + rag + i) * 4, m[1] + 120 - rag * 12); ctx.lineTo(rx + 6, m[1] + 100); ctx.fill();
        }
        ctx.fillStyle = '#100e0c';
      });
      additive(ctx, function () {
        for (var w = 0; w < 4; w++) {
          dot(ctx, '#7aff9a', 1200 + w * 26, 436, 18, 0.7 + 0.2 * Math.sin(t * 3 + w));
        }
      });
      ctx.fillStyle = '#7aff9a';
      for (var w2 = 0; w2 < 4; w2++) ctx.fillRect(1192 + w2 * 26, 428, 16, 14);
      // masts of the drowned fleet standing out of the water
      ctx.fillStyle = '#16120e';
      [[560, 330], [620, 400], [1420, 340], [1500, 300]].forEach(function (m) {
        ctx.fillRect(m[0] - 4, m[1], 8, 560 - m[1]); ctx.fillRect(m[0] - 40, m[1] + 30, 80, 5);
      });
      // the pier in front, our Corsair on it with a lantern
      ctx.fillStyle = '#3a2a1e'; ctx.fillRect(0, 700, VW, 26);
      ctx.fillStyle = '#2a1e14';
      for (var pp = 0; pp < 18; pp++) ctx.fillRect(pp * 92 + 20, 726, 12, 120);
      var walk = seg(t, 0.2, 2.6);
      var px = lerp(120, 520, walk);
      pirate(ctx, px, 700, 1.0, t, 0, t > 2.8 ? 1 : 0);
      additive(ctx, function () { dot(ctx, '#ffd890', px - 30, 640, 60, 0.5); });
      ctx.fillStyle = '#ffd890'; ctx.fillRect(px - 36, 630, 12, 16);
      // the fog rising, then the dead climbing up out of the water
      var fogUp = seg(t, 1.0, 2.2);
      d.fog.forEach(function (f) {
        var x = (f[0] + t * 30 * (0.5 + f[3])) % (VW + 400) - 200;
        ctx.fillStyle = 'rgba(200,220,220,' + (0.12 + 0.22 * fogUp) + ')';
        ctx.beginPath(); ctx.ellipse(x, f[1] - fogUp * 60, f[2], 30, 0, 0, TAU); ctx.fill();
      });
      [[760, 640, 0.9, 1.6], [940, 660, 1.0, 1.9], [1140, 650, 0.95, 2.2], [1340, 670, 1.05, 2.0]].forEach(function (sk, i) {
        var rise = outCubic(seg(t, sk[3], sk[3] + 0.8));
        if (rise <= 0) return;
        var aim = seg(t, 2.7, 3.0);
        gfSkeleton(ctx, sk[0], sk[1], sk[2], rise, aim, t, -1);
        if (t > 3.0 + i * 0.08 && t < 3.2 + i * 0.08) {
          additive(ctx, function () { dot(ctx, '#aaffcc', sk[0] - 60 * sk[2], sk[1] - 120 * sk[2], 40, 0.9); });
        }
      });
      d.wisps.forEach(function (w) {
        var x = w[0] + Math.sin(t * 0.6 + w[2]) * 40, y = w[1] + Math.cos(t * 0.8 + w[2]) * 20;
        additive(ctx, function () {
          dot(ctx, '#7aff9a', x, y, 22 * w[3], 0.5 + 0.3 * Math.sin(t * 3 + w[2]));
          dot(ctx, '#e8ffe8', x, y, 5, 0.9);
        });
      });
    },
    title: function (ctx, t, d, run) {
      // the flagship's nameboard, salvaged: black planks on two chains,
      // swinging, the letters in ghost-light -- flickering
      var at = 0.9;
      if (t < at) return;
      var k = outBack(seg(t, at, at + 0.5), 1.2);
      ctx.save();
      ctx.translate(800, 150 - (1 - k) * 300);
      var swing = Math.sin((t - at) * 2.2) * 0.04 * Math.max(0.3, 1 - (t - at) * 0.3);
      ctx.rotate(swing);
      ctx.strokeStyle = '#6a6a72'; ctx.lineWidth = 5;
      for (var c = -1; c <= 1; c += 2) {
        ctx.beginPath(); ctx.moveTo(c * 380, -300); ctx.lineTo(c * 400, -50); ctx.stroke();
        for (var l = 0; l < 10; l++) {
          ctx.beginPath(); ctx.ellipse(c * (380 + l * 2), -280 + l * 24, 5, 9, 0, 0, TAU); ctx.stroke();
        }
      }
      ctx.fillStyle = 'rgba(0,0,0,0.35)'; roundRect(ctx, -510, -54, 1036, 156, 8); ctx.fill();
      for (var pl = 0; pl < 3; pl++) {
        ctx.fillStyle = pl % 2 ? '#2a2018' : '#33281e';
        ctx.fillRect(-520, -60 + pl * 50, 1040, 50);
        ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.fillRect(-520, -60 + pl * 50 + 46, 1040, 4);
      }
      ctx.fillStyle = '#2a5a3a';
      for (var wd = 0; wd < 14; wd++) ctx.fillRect(-500 + wd * 76, 88, 10, 14 + (wd * 7 % 5) * 6);
      ctx.fillStyle = '#8a7030';
      [[-500, -44], [500, -44], [-500, 74], [500, 74]].forEach(function (p) { ctx.beginPath(); ctx.arc(p[0], p[1], 7, 0, TAU); ctx.fill(); });
      ctx.globalAlpha = run.alpha;
      ctx.font = 'bold 22px ' + HEAVY; ctx.textAlign = 'center'; ctx.fillStyle = '#8a7030';
      ctx.fillText('PLUNDER BAY', 0, -28);
      var flick = Math.sin(t * 23) > 0.92 ? 0.35 : 1;
      var name = (run.info.name || 'Ghost Fleet Cove').toUpperCase();
      titleText(ctx, name, 0, 34, 860, 84, 'rgba(200,255,214,' + flick + ')', '#0a1a10', 8);
      additive(ctx, function () {
        ctx.globalAlpha = 0.5 * flick * run.alpha;
        titleText(ctx, name, 0, 34, 860, 84, '#7aff9a', null);
        ctx.globalAlpha = run.alpha;
      });
      ctx.restore();
    }
  });

  // ------------------------------------------------ Glowtide Lagoon
  Intro.register('pb_glowtide', {
    name: 'Glowtide Lagoon',
    tagline: 'A lagoon that lights up when you wade it. When the tide goes out, the clams give up their pearls.',
    accent: '#5af0ff',
    cues: [[0.2, 'pb_waves', 0.6], [1.3, 'pb_twist_tide', 0.7], [1.6, 'pb_tide', 0.7], [2.9, 'pb_coins', 0.6],
           [3.6, 'pb_pick', 0.6], [4.4, 'pb_go', 0.6]],
    shakes: [],
    tagY: 612, tagAt: 3.3,
    setup: function (r) {
      var d = { stars: makeStars(r, 70, 0, 300), glints: [], sky: [], floats: [] };
      for (var i = 0; i < 70; i++) d.glints.push([between(r, 0, VW), between(r, 0, 1), r() * 6]);
      for (var s = 0; s < 12; s++) d.sky.push([between(r, 1060, 1500), r(), between(r, 0.6, 1.2), r() * 6]);
      for (var f = 0; f < 14; f++) d.floats.push([between(r, 60, 1540), between(r, 0, 1), r() * 6]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, 470);
      sky.addColorStop(0, '#0e1240'); sky.addColorStop(0.5, '#4a2e6e'); sky.addColorStop(0.85, '#c86a8a'); sky.addColorStop(1, '#f0a88a');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      stars(ctx, d.stars, t, 0.7);
      // a thin moon, the festival's sky lanterns going up on the right
      ctx.fillStyle = '#f4f0e4'; ctx.beginPath(); ctx.arc(330, 150, 46, 0, TAU); ctx.fill();
      ctx.fillStyle = '#2a2056'; ctx.beginPath(); ctx.arc(350, 140, 42, 0, TAU); ctx.fill();
      d.sky.forEach(function (s) {
        var u = (s[1] + t * 0.06 * s[2]) % 1;
        var x = s[0] + u * 120 + Math.sin(t + s[3]) * 8, y = 470 - u * 440;
        additive(ctx, function () { dot(ctx, '#ffb84a', x, y, 22 * (1 - u * 0.5), 0.55 * (1 - u)); });
        ctx.fillStyle = 'rgba(255,200,110,' + (1 - u) + ')'; ctx.fillRect(x - 5, y - 7, 10, 14);
      });
      // mangroves black against the sky, either side
      ctx.fillStyle = '#121a26';
      [[0, 300, 260], [120, 330, 200], [1340, 320, 240], [1480, 290, 260]].forEach(function (m) {
        ctx.beginPath(); ctx.ellipse(m[0] + 60, m[1], m[2] / 2, 70, 0, 0, TAU); ctx.fill();
        ctx.fillRect(m[0] + 50, m[1], 14, 180);
        for (var rt = 0; rt < 5; rt++) { ctx.fillRect(m[0] + 20 + rt * 18, m[1] + 120 + (rt % 2) * 20, 5, 70); }
      });
      // the moon temple out in the lagoon, its crescents glowing, the idol on top
      var tiers = [[460, 500], [380, 456], [300, 414], [220, 372], [140, 330]];
      tiers.forEach(function (tr, i) {
        ctx.fillStyle = i % 2 ? '#3a4660' : '#46526e';
        ctx.fillRect(800 - tr[0] / 2, tr[1], tr[0], 540 - tr[1]);
      });
      ctx.fillStyle = '#2a3348'; ctx.fillRect(780, 330, 40, 210);
      additive(ctx, function () {
        [[640, 440], [960, 440]].forEach(function (c) { dot(ctx, '#7ad8ff', c[0], c[1], 26, 0.8); });
        dot(ctx, '#ffd040', 800, 312, 46, 0.7 + 0.2 * Math.sin(t * 3));
      });
      ctx.strokeStyle = '#bfefff'; ctx.lineWidth = 5;
      [[640, 440], [960, 440]].forEach(function (c) { ctx.beginPath(); ctx.arc(c[0], c[1], 14, -1.2, 1.9); ctx.stroke(); });
      ctx.fillStyle = '#e8b830'; ctx.fillRect(790, 300, 20, 30);
      // the lagoon, falling with the tide: the causeway coming up out of it,
      // the clams on the floor opening, their pearls lit
      var ebb = seg(t, 1.5, 2.8);
      var water = 540 + ebb * 90;
      ctx.fillStyle = '#2a3a52'; ctx.fillRect(0, 540, VW, 360);
      ctx.fillStyle = '#5a6a84'; ctx.fillRect(740, 600, 120, 300);
      ctx.fillStyle = '#6a7a96'; ctx.fillRect(740, 596, 120, 8);
      [[360, 760], [560, 700], [1060, 710], [1260, 770], [460, 840], [1160, 850]].forEach(function (c, i) {
        var open = seg(t, 2.6 + i * 0.08, 3.0 + i * 0.08);
        ctx.fillStyle = '#9a8ab8';
        ctx.beginPath(); ctx.ellipse(c[0], c[1], 44, 16, 0, 0, Math.PI); ctx.fill();
        ctx.save(); ctx.translate(c[0] - 44, c[1]); ctx.rotate(-open * 0.7);
        ctx.beginPath(); ctx.ellipse(44, 0, 44, 16, 0, Math.PI, TAU); ctx.fill(); ctx.restore();
        if (open > 0) additive(ctx, function () { dot(ctx, '#f4f8ff', c[0], c[1] - 6, 22 * open, 0.9); });
        ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(c[0], c[1] - 6, 6 * open, 0, TAU); ctx.fill();
      });
      ctx.fillStyle = 'rgba(14,74,138,0.72)'; ctx.fillRect(0, water, VW, VH - water);
      d.glints.forEach(function (g) {
        var y = water + 8 + g[1] * (VH - water - 8);
        additive(ctx, function () { dot(ctx, '#5af0ff', g[0] + Math.sin(t + g[2]) * 10, y, 5, 0.4 + 0.4 * Math.sin(t * 4 + g[2])); });
      });
      d.floats.forEach(function (f) {
        var x = f[0] + Math.sin(t * 0.4 + f[2]) * 20, y = water - 6 + Math.sin(t * 1.4 + f[2]) * 2;
        ctx.fillStyle = ['#ff6a4a', '#ffb84a', '#ff8ad8', '#ffe07a'][Math.floor(f[2]) % 4];
        ctx.fillRect(x - 7, y - 12, 14, 14);
        additive(ctx, function () { dot(ctx, '#ffb84a', x, y - 5, 18, 0.4); });
      });
      // our Corsair wading out along the causeway, the water lit round her
      // legs -- then dry, and stooping for a pearl
      var walk = seg(t, 0.3, 3.4);
      var px = 800, py = lerp(900, 640, outCubic(walk)), ps = lerp(1.25, 0.7, walk);
      if (py > water - 4) {
        additive(ctx, function () {
          for (var rr = 0; rr < 3; rr++) {
            var u = (t * 0.9 + rr / 3) % 1;
            ctx.strokeStyle = 'rgba(90,240,255,' + (0.7 * (1 - u)) + ')'; ctx.lineWidth = 4;
            ctx.beginPath(); ctx.ellipse(px, Math.min(py, water + 6), 30 + u * 70, 8 + u * 16, 0, 0, TAU); ctx.stroke();
          }
        });
      }
      pirate(ctx, px, py, ps, t, 0, t > 3.5 ? 2 : 0);
    },
    title: function (ctx, t, d, run) {
      // the name written in moonlight over the water, its reflection
      // rippling under it
      var at = 1.0;
      if (t < at) return;
      var k = seg(t, at, at + 0.8);
      var name = (run.info.name || 'Glowtide Lagoon').toUpperCase();
      ctx.save();
      ctx.globalAlpha = run.alpha * k;
      ctx.font = 'bold 22px ' + HEAVY; ctx.textAlign = 'center'; ctx.fillStyle = '#ffd8a0';
      ctx.fillText('PLUNDER BAY', 800, 110);
      ctx.strokeStyle = '#ffd8a0'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(800, 76, 14, -2.2, 1.2); ctx.stroke();
      var y = 176 - (1 - outCubic(k)) * 30;
      additive(ctx, function () { titleText(ctx, name, 800, y, 1000, 104, 'rgba(90,240,255,0.55)', null); });
      titleText(ctx, name, 800, y, 1000, 104, '#e8fcff', '#1a2a5a', 6);
      // the reflection, in slices, each pushed by the ripple
      for (var sl = 0; sl < 14; sl++) {
        ctx.save();
        ctx.beginPath(); ctx.rect(0, y + 52 + sl * 7, VW, 7); ctx.clip();
        ctx.translate(Math.sin(t * 3 + sl * 0.9) * 6 * (1 + sl * 0.1), 2 * (y + 52) - 0);
        ctx.scale(1, -1);
        ctx.globalAlpha = run.alpha * k * 0.32 * (1 - sl / 14);
        titleText(ctx, name, 800, y, 1000, 104, '#7ad8ff', null);
        ctx.restore();
      }
      ctx.restore();
    }
  });

  // ------------------------------------------------ Frostfang Floe
  /* A frosted tentacle bursting up out of a hole in the ice: ``up`` how
     far out, ``curl`` how far it has bent over to slam. */
  function ffTentacle(ctx, x, y, s, up, curl, t, seed) {
    var n = 14, h = 300 * s * up;
    var pts = [];
    for (var i = 0; i <= n; i++) {
      var f = i / n;
      var bend = curl * f * f * 1.6 + Math.sin(t * 2 + seed + f * 3) * 0.12 * f;
      pts.push([x + Math.sin(bend) * h * f * 0.8, y - Math.cos(bend) * h * f, (1 - f) * 34 * s + 5 * s]);
    }
    for (var j = 0; j < n; j++) {
      var a = pts[j], c = pts[j + 1];
      ctx.strokeStyle = j % 2 ? '#7aa8c8' : '#8ab8d4'; ctx.lineCap = 'round'; ctx.lineWidth = a[2];
      ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(c[0], c[1]); ctx.stroke();
      if (j % 2 === 0 && j < n - 2) {
        ctx.fillStyle = '#f0faff';
        ctx.beginPath(); ctx.arc(a[0] + a[2] * 0.35, a[1], a[2] * 0.22, 0, TAU); ctx.fill();
      }
      if (j % 4 === 1) {
        ctx.fillStyle = 'rgba(240,250,255,0.9)';
        ctx.beginPath(); ctx.moveTo(a[0] - a[2] * 0.5, a[1]); ctx.lineTo(a[0] - a[2] * 0.3, a[1] + a[2] * 0.9); ctx.lineTo(a[0] - a[2] * 0.1, a[1]); ctx.fill();
      }
    }
  }

  Intro.register('pb_frostfang', {
    name: 'Frostfang Floe',
    tagline: 'A galleon frozen into the ice at the top of the world. Something big lives under it.',
    accent: '#9ae8ff',
    cues: [[0.2, 'pb_waves', 0.4], [1.2, 'pb_twist_kraken', 0.8], [1.5, 'pb_kraken', 0.9], [2.8, 'pb_slam', 0.9],
           [3.4, 'pb_kraken', 0.6], [4.4, 'pb_go', 0.6]],
    shakes: [[1.5, 6, 0.5], [2.8, 12, 0.5]],
    tagY: 612, tagAt: 3.4,
    setup: function (r) {
      var d = { snow: [], shards: [], sparkle: [] };
      for (var i = 0; i < 120; i++) d.snow.push([r() * VW, r() * VH, between(r, 0.4, 1.2), r() * 6]);
      for (var s = 0; s < 30; s++) d.shards.push([between(r, -1, 1), between(r, 0.5, 1.2), r(), r() * 6]);
      for (var g = 0; g < 40; g++) d.sparkle.push([r() * VW, between(r, 560, 900), r() * 6]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, 480);
      sky.addColorStop(0, '#2a7ad8'); sky.addColorStop(1, '#e8f4ff');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      additive(ctx, function () { dot(ctx, '#ffffff', 1260, 120, 220, 0.5); });
      ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(1260, 120, 44, 0, TAU); ctx.fill();
      // the glacier behind, in three blue-white steps
      [[0, 1600, 470, 380, '#bfe4f4'], [180, 1420, 380, 300, '#d4eef8'], [360, 1240, 300, 230, '#bfe4f4']].forEach(function (g) {
        ctx.fillStyle = g[4]; ctx.fillRect(g[0], g[3], g[1] - g[0], g[2] - g[3] + 120);
        ctx.fillStyle = '#f4f8fc'; ctx.fillRect(g[0], g[3] - 8, g[1] - g[0], 10);
        ctx.fillStyle = 'rgba(74,144,184,0.5)';
        for (var c = g[0] + 30; c < g[1] - 20; c += 64) ctx.fillRect(c, g[3] + 8, 10, 40 + (c * 7 % 5) * 12);
        ctx.fillStyle = '#e8f8ff';
        for (var ic = g[0] + 50; ic < g[1] - 20; ic += 48) {
          ctx.beginPath(); ctx.moveTo(ic, g[3] + 2); ctx.lineTo(ic + 8, g[3] + 2); ctx.lineTo(ic + 4, g[3] + 26 + (ic * 3 % 4) * 6); ctx.fill();
        }
      });
      // the pack ice, and the frozen galleon held in it
      ctx.fillStyle = '#d8eef8'; ctx.fillRect(0, 520, VW, 380);
      ctx.fillStyle = '#5a3a20';
      ctx.beginPath(); ctx.moveTo(560, 560); ctx.lineTo(600, 500); ctx.lineTo(1000, 500); ctx.lineTo(1060, 470); ctx.lineTo(1050, 560); ctx.fill();
      ctx.fillStyle = '#f4f8fc'; ctx.fillRect(600, 494, 400, 10);
      [[680, 260], [800, 200], [930, 280]].forEach(function (m, i) {
        ctx.fillStyle = '#4a3020'; ctx.fillRect(m[0] - 5, m[1], 10, 500 - m[1]);
        for (var yd = 0; yd < 2; yd++) {
          var yy = m[1] + 30 + yd * 90;
          ctx.fillStyle = '#4a3020'; ctx.fillRect(m[0] - 70 + yd * 10, yy, 140 - yd * 20, 6);
          ctx.fillStyle = '#f4f8fc'; ctx.fillRect(m[0] - 64 + yd * 10, yy + 6, 128 - yd * 20, 64);
          ctx.fillStyle = '#e8f8ff';
          for (var c2 = 0; c2 < 6; c2++) {
            var cx = m[0] - 60 + yd * 10 + c2 * 22;
            ctx.beginPath(); ctx.moveTo(cx, yy + 70); ctx.lineTo(cx + 6, yy + 70); ctx.lineTo(cx + 3, yy + 90); ctx.fill();
          }
        }
      });
      ctx.fillStyle = '#e8b830'; ctx.fillRect(982, 448, 18, 24);
      additive(ctx, function () { dot(ctx, '#ffe080', 991, 460, 30, 0.6); });
      // the breathing holes in the ice in front, black water in them
      var holes = [[300, 700], [1300, 700], [520, 820], [1080, 820]];
      holes.forEach(function (h) {
        ctx.fillStyle = '#123a5a'; ctx.beginPath(); ctx.ellipse(h[0], h[1], 90, 26, 0, 0, TAU); ctx.fill();
        ctx.fillStyle = '#f0faff';
        for (var e = 0; e < 8; e++) {
          var a = e * TAU / 8;
          ctx.fillRect(h[0] + Math.cos(a) * 92 - 8, h[1] + Math.sin(a) * 27 - 4, 16, 8);
        }
      });
      d.sparkle.forEach(function (g) {
        additive(ctx, function () { dot(ctx, '#ffffff', g[0], g[1], 4, 0.3 + 0.5 * Math.max(0, Math.sin(t * 3 + g[2]))); });
      });
      // the kraken comes up through them: shards of ice flung out
      var burst = seg(t, 1.4, 1.9), slam = seg(t, 2.4, 2.8), back = seg(t, 3.6, 4.4);
      holes.forEach(function (h, i) {
        var up = outBack(seg(t, 1.4 + i * 0.12, 1.9 + i * 0.12), 1.2) * (1 - back);
        if (up <= 0) return;
        var curl = i === 2 ? slam * 1.4 : Math.sin(t * 1.5 + i) * 0.2;
        ffTentacle(ctx, h[0], h[1], i < 2 ? 0.8 : 1.0, up, curl, t, i);
      });
      if (burst > 0 && burst < 1) {
        d.shards.forEach(function (sh, i) {
          var h = holes[i % 4];
          var x = h[0] + sh[0] * 200 * burst, y = h[1] - sh[1] * 260 * burst + 300 * burst * burst;
          ctx.fillStyle = 'rgba(240,250,255,' + (1 - burst) + ')';
          ctx.save(); ctx.translate(x, y); ctx.rotate(t * 8 + sh[3]); ctx.fillRect(-6, -10, 12, 20); ctx.restore();
        });
      }
      // our Corsair running across the ice with a jewel; the slam lands
      // just behind her
      var run = seg(t, 0.3, 4.4);
      var px = lerp(160, 900, run);
      pirate(ctx, px, 860, 1.0, t, 0, 0);
      ctx.fillStyle = '#3ad0ff';
      ctx.beginPath(); ctx.moveTo(px + 30, 730); ctx.lineTo(px + 44, 744); ctx.lineTo(px + 30, 758); ctx.lineTo(px + 16, 744); ctx.fill();
      if (t > 2.3 && t < 2.8) {
        ctx.strokeStyle = 'rgba(154,232,255,' + (0.5 + 0.5 * Math.sin(t * 30)) + ')'; ctx.lineWidth = 6;
        ctx.beginPath(); ctx.ellipse(700, 840, 110, 30, 0, 0, TAU); ctx.stroke();
      }
      if (t > 2.8 && t < 3.6) {
        var age = t - 2.8;
        additive(ctx, function () { dot(ctx, '#e8f8ff', 700, 840, 140 + age * 200, Math.max(0, 0.9 - age * 1.2)); });
      }
      // penguins watching from the edge
      [[1440, 600], [1480, 610], [1520, 596]].forEach(function (p, i) {
        var w = Math.sin(t * 6 + i) * 0.1;
        ctx.save(); ctx.translate(p[0], p[1]); ctx.rotate(w);
        ctx.fillStyle = '#1e2228'; ctx.beginPath(); ctx.ellipse(0, -22, 12, 22, 0, 0, TAU); ctx.fill();
        ctx.fillStyle = '#f4f4f0'; ctx.beginPath(); ctx.ellipse(2, -18, 8, 16, 0, 0, TAU); ctx.fill();
        ctx.fillStyle = '#ff9a2a'; ctx.fillRect(8, -38, 8, 4);
        ctx.restore();
      });
      // the snow, blowing
      ctx.fillStyle = 'rgba(255,255,255,0.85)';
      d.snow.forEach(function (sn) {
        var x = (sn[0] + t * 60 * sn[2] + Math.sin(t + sn[3]) * 20) % VW, y = (sn[1] + t * 90 * sn[2]) % VH;
        ctx.beginPath(); ctx.arc(x, y, 2 + sn[2] * 2, 0, TAU); ctx.fill();
      });
    },
    title: function (ctx, t, d, run) {
      // a slab of clear blue ice, the name cut into it in frost, icicles
      // hanging off its lower edge
      var at = 1.0;
      if (t < at) return;
      var k = outBack(seg(t, at, at + 0.45), 1.5);
      ctx.save();
      ctx.translate(800, 168 - (1 - k) * 320);
      ctx.rotate(-0.01 + wobble(t, at + 0.45, 0.02, 12, 5));
      var g = ctx.createLinearGradient(0, -90, 0, 90);
      g.addColorStop(0, 'rgba(220,244,255,0.95)'); g.addColorStop(1, 'rgba(140,200,232,0.95)');
      ctx.fillStyle = 'rgba(30,60,90,0.25)'; roundRect(ctx, -490, -78, 1000, 180, 18); ctx.fill();
      ctx.fillStyle = g; roundRect(ctx, -500, -90, 1000, 180, 18); ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.9)'; ctx.lineWidth = 4; roundRect(ctx, -486, -76, 972, 152, 12); ctx.stroke();
      ctx.fillStyle = 'rgba(255,255,255,0.35)';
      ctx.beginPath(); ctx.moveTo(-480, -70); ctx.lineTo(-300, -70); ctx.lineTo(-420, 60); ctx.lineTo(-480, 60); ctx.fill();
      ctx.fillStyle = '#e8f8ff';
      for (var ic = -460; ic < 480; ic += 46) {
        var len = 18 + ((ic + 500) * 7 % 5) * 9;
        ctx.beginPath(); ctx.moveTo(ic, 88); ctx.lineTo(ic + 14, 88); ctx.lineTo(ic + 7, 88 + len); ctx.fill();
      }
      ctx.globalAlpha = run.alpha;
      ctx.font = 'bold 22px ' + HEAVY; ctx.textAlign = 'center'; ctx.fillStyle = '#2a6aa0';
      ctx.fillText('PLUNDER BAY', 0, -42);
      titleText(ctx, (run.info.name || 'Frostfang Floe').toUpperCase(), 0, 20, 860, 92, '#ffffff', '#2a6aa0', 8);
      var shine = seg(t, at + 0.4, at + 1.3);
      if (shine > 0 && shine < 1) {
        additive(ctx, function () {
          var sx = lerp(-500, 500, shine);
          var sg = ctx.createLinearGradient(sx - 70, 0, sx + 70, 0);
          sg.addColorStop(0, 'rgba(255,255,255,0)'); sg.addColorStop(0.5, 'rgba(255,255,255,0.6)'); sg.addColorStop(1, 'rgba(255,255,255,0)');
          ctx.fillStyle = sg; ctx.fillRect(sx - 70, -90, 140, 180);
        });
      }
      ctx.restore();
    }
  });
})(window);
