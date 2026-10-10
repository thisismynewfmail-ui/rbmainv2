/* BLOCKHAVEN Game View -- what the event weapons and held items look like and
   do on this side of the wire (the rules live in app/game/gear.py).

   It keeps:
     - your own statuses (``st``): slowed, rooted, stunned, blinded, a toad...
       which change how you move and whether you may fire, and show as icons
       and screen effects;
     - your cooldowns (``cd``) and meters (``meter``), drawn on the hotbar and
       over the ammo counter;
     - everybody else's statuses (bits in the snapshot), drawn on them: fire,
       ice, stars, a mark over the head, a shield bubble, a toad in place of
       the avatar, near-invisibility;
     - the round's summoned things (``mn`` rows), placed things (``dep``,
       the 1 Hz state), strikes on their way down, beams, cones, and the
       projectile models the event weapons fire (their ``data.proj``).

   Client.js calls in at a few points: bind (the socket), onSnapshot,
   onState, step (moveScale/canMove/canJump/gravityScale), tryFire
   (canFire/localFire), and render (avatarParts/draw/drawProjectile). */
(function (global) {
  'use strict';

  var BITS = {
    burn: 1, slow: 2, root: 4, stun: 8, freeze: 16, mark: 32, blind: 64, poison: 128,
    bleed: 256, polymorph: 512, cloak: 1024, shield: 2048, haste: 4096, reveal: 8192,
    might: 16384, regen: 32768, jumpless: 65536, silence: 131072, lowgrav: 262144,
    dazzle: 524288, block: 1048576, crit: 2097152
  };
  var GEAR_KINDS = { beam: 1, cone: 1, strike: 1, deploy: 1, summon: 1, ability: 1, consume: 1 };
  var CHARGED = { strike: 1, deploy: 1, summon: 1, ability: 1, consume: 1 };
  var ICON = {
    burn: '&#128293;', poison: '&#129514;', bleed: '&#129656;', slow: '&#10052;', freeze: '&#129482;',
    root: '&#129704;', stun: '&#128171;', jumpless: '&#11015;', silence: '&#128263;', blind: '&#127775;',
    mark: '&#127919;', dazzle: '&#10024;', reveal: '&#128065;', polymorph: '&#128056;', haste: '&#9889;',
    might: '&#128170;', regen: '&#10133;', shield: '&#128737;', lowgrav: '&#129718;', cloak: '&#128123;',
    cheat: '&#127808;', block: '&#9876;', crit: '&#127919;'
  };
  var GOOD = { haste: 1, might: 1, regen: 1, shield: 1, lowgrav: 1, cloak: 1, cheat: 1, block: 1, crit: 1 };
  var LABEL = {
    burn: 'Burning', poison: 'Poisoned', bleed: 'Bleeding', slow: 'Slowed', freeze: 'Chilled',
    root: 'Rooted', stun: 'Stunned', jumpless: 'Grounded', silence: 'Silenced', blind: 'Blinded',
    mark: 'Marked', dazzle: 'Dazzled', reveal: 'Revealed', polymorph: 'A toad', haste: 'Hasted',
    might: 'Empowered', regen: 'Mending', shield: 'Shielded', lowgrav: 'Floating', cloak: 'Cloaked',
    cheat: 'Lucky', block: 'Parrying', crit: 'Crits'
  };
  // the sounds an item's ``sound`` names, mapped onto the synth's own
  var SOUND = {
    horn: 'horn', chime: 'bell', bell: 'bell', drink: 'heal', eat: 'heal', crack: 'power',
    throw: 'whoosh', rocket: 'rocket', laser: 'buzz', pop: 'pistol', staff: 'raise',
    summon: 'raise', magic: 'power', tick: 'tick', beep: 'beep', crow: 'crow', splat: 'splat',
    whistle: 'loon', drum: 'thunk', banjo: 'scratch', fiddle: 'scratch', bagpipe: 'siren',
    fuse: 'fuse', swing: 'swing', sword: 'sword', shotgun: 'shotgun', pistol: 'pistol',
    rifle: 'rifle', sniper: 'sniper', smg: 'smg', heal: 'heal', coin: 'coin', splash: 'splash'
  };

  // ------------------------------------------------------------- matrices
  // the renderer's euler convention (yaw, then pitch, then roll), as the
  // crate stage uses it (ui/crates.js)
  function eulerMat(r) {
    var cx = Math.cos(r[0]), sx = Math.sin(r[0]), cy = Math.cos(r[1]), sy = Math.sin(r[1]);
    var cz = Math.cos(r[2]), sz = Math.sin(r[2]);
    return [cy * cz + sy * sx * sz, cx * sz, -sy * cz + cy * sx * sz,
            -cy * sz + sy * sx * cz, cx * cz, sy * sz + cy * sx * cz,
            sy * cx, -sx, cy * cx];
  }
  function mul(a, b) {
    var o = new Array(9);
    for (var c = 0; c < 3; c++) {
      for (var r = 0; r < 3; r++) {
        o[c * 3 + r] = a[r] * b[c * 3] + a[3 + r] * b[c * 3 + 1] + a[6 + r] * b[c * 3 + 2];
      }
    }
    return o;
  }
  function apply(m, v) {
    return [m[0] * v[0] + m[3] * v[1] + m[6] * v[2],
            m[1] * v[0] + m[4] * v[1] + m[7] * v[2],
            m[2] * v[0] + m[5] * v[1] + m[8] * v[2]];
  }
  function toEuler(m) {
    var rx = Math.asin(Math.max(-1, Math.min(1, -m[7])));
    return [rx, Math.atan2(m[6], m[8]), Math.atan2(m[1], m[4])];
  }

  /* An item's parts (a projectile, a turret, a summoned thing) placed at
     ``at``, turned by ``rot`` (a whole-model euler), scaled by ``k``. */
  function placeParts(parts, at, rot, k, alpha, time) {
    var R = eulerMat(rot || [0, 0, 0]);
    var out = [];
    k = k || 1;
    for (var i = 0; i < (parts || []).length; i++) {
      var q = parts[i];
      if (!q || !q.p || !q.s) continue;
      var off = apply(R, [q.p[0] * k, q.p[1] * k, q.p[2] * k]);
      var own = q.r || [0, 0, 0];
      if (q.spin && time) own = [own[0], own[1] + time * q.spin, own[2]];
      var part = {
        t: q.t || 'box', p: [at[0] + off[0], at[1] + off[1], at[2] + off[2]],
        s: [q.s[0] * k, q.s[1] * k, q.s[2] * k], c: q.c, r: toEuler(mul(R, eulerMat(own))),
        m: q.m, a: q.a, dw: q.dw,
        decSlot: q.decal ? Textures.decal(q.decal) : null
      };
      if (alpha !== undefined && alpha < 1) part.a = Math.min(part.a === undefined ? 1 : part.a, alpha);
      out.push(part);
    }
    return out;
  }

  function rgb(hex) { return GLX.mat.hexToRgb(hex || '#ffffff'); }
  function nowSec() { return performance.now() / 1000; }
  function dist(a, b) { return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]); }

  // ============================================================== Gear
  function Gear(client) {
    this.c = client;
    this.status = {};        // mine: name -> { until, value, stacks }
    this.cooldowns = {};     // item id -> until (seconds, performance clock)
    this.meters = {};        // item id -> { v, l, on, at }
    this.minions = {};       // id -> row-ish object with memory
    this.deps = {};          // id -> deployable
    this.strikes = [];
    this.beams = {};         // player id -> { o, e, c, until }
    this.flashes = [];       // short-lived shapes: cones, pulses, rings, lines
    this.blindUntil = 0;
    this.entityBits = {};    // non-player entities (the infected) -> bits
    this.dataCache = {};
    this.buildHud();
  }

  // --------------------------------------------------------------- lookups
  /* An item's ``data`` (its stats, parts, proj, deploy, minion), from
     whoever might be holding it: its owner, else anyone in the round. */
  Gear.prototype.itemData = function (itemId, ownerId) {
    if (!itemId) return null;
    if (this.dataCache[itemId]) return this.dataCache[itemId];
    var c = this.c;
    var pools = [];
    if (ownerId && c.players[ownerId]) pools.push(c.players[ownerId].avatar);
    pools.push(c.avatar);
    Object.keys(c.players).forEach(function (id) { pools.push(c.players[id].avatar); });
    for (var i = 0; i < pools.length; i++) {
      var hotbar = (pools[i] && pools[i].hotbar) || [];
      for (var j = 0; j < hotbar.length; j++) {
        if (hotbar[j] && hotbar[j].item_id === itemId && hotbar[j].data) {
          this.dataCache[itemId] = hotbar[j].data;
          return hotbar[j].data;
        }
      }
    }
    return null;
  };

  Gear.prototype.minionSpec = function (itemId, ownerId) {
    var data = this.itemData(itemId, ownerId) || {};
    var stats = data.stats || {};
    return stats.minion || data.minion || (stats.on_kill && stats.on_kill.summon) || {};
  };

  // ------------------------------------------------------------- the wire
  Gear.prototype.bind = function (net) {
    var self = this;
    net.on('st', function (msg) { self.onStatus(msg.s || {}); });
    net.on('cd', function (msg) {
      self.cooldowns[msg.w] = nowSec() + (msg.s || 0);
    });
    net.on('meter', function (msg) {
      self.meters[msg.w] = { v: msg.v, l: msg.l, on: !!msg.on, at: nowSec() };
    });
    net.on('gfx', function (msg) { self.onGfx(msg); });
    net.on('dep', function (msg) { self.upsertDep(msg.d, true); });
    net.on('undep', function (msg) {
      var d = self.deps[msg.id];
      if (d && msg.fx) self.c.particles.burst('dust', d.p);
      delete self.deps[msg.id];
    });
    net.on('tp', function (msg) {
      var c = self.c;
      c.local.pos = msg.p.slice();
      c.local.vel = [0, 0, 0];
    });
    net.on('notice', function (msg) {
      if (msg.m) self.c.hud.toast(self.c.hud.escape(msg.m), 'bad');
    });
  };

  Gear.prototype.onStatus = function (table) {
    var t = nowSec();
    var fresh = {};
    var self = this;
    Object.keys(table).forEach(function (name) {
      var row = table[name];
      fresh[name] = { until: t + row[0], value: row[1], stacks: row[2] || 1 };
      if (!self.status[name] && name === 'polymorph') self.c.hud.toast('<b>You have been turned into a toad!</b>', 'bad', true);
      if (!self.status[name] && name === 'stun') self.c.audio.play('hit', { volume: 0.6 });
    });
    this.status = fresh;
    this.drawStatusHud();
  };

  Gear.prototype.onSnapshot = function (msg) {
    var c = this.c;
    var rows = msg.ps || [];
    for (var i = 0; i < rows.length; i++) {
      var p = c.players[rows[i][0]];
      if (p) p.bits = rows[i][10] || 0;
    }
    var live = {};
    var self = this;
    (msg.mn || []).forEach(function (r) {
      live[r[0]] = true;
      var m = self.minions[r[0]];
      if (!m) {
        m = self.minions[r[0]] = { id: r[0], pos: [r[1], r[2], r[3]], target: [r[1], r[2], r[3]],
                                   memory: {}, seed: Math.random() };
      }
      m.target = [r[1], r[2], r[3]];
      m.yaw = r[4]; m.anim = r[5]; m.hp = r[6]; m.owner = r[7]; m.item = r[8]; m.bits = r[9] || 0;
    });
    Object.keys(this.minions).forEach(function (id) { if (!live[id]) delete self.minions[id]; });
    (msg.dm || []).forEach(function (r) {
      var d = self.deps[r[0]];
      if (d) { d.target = [r[1], r[2], r[3]]; d.yaw = r[4]; }
    });
    this.entityBits = {};
    (msg.es || []).forEach(function (r) { self.entityBits[r[0]] = r[1]; });
  };

  Gear.prototype.onState = function (state) {
    if (!state || !state.gear) return;
    var seen = {};
    var self = this;
    state.gear.forEach(function (row) { seen[row[0]] = true; self.upsertDep(row, false); });
    Object.keys(this.deps).forEach(function (id) { if (!seen[id]) delete self.deps[id]; });
  };

  Gear.prototype.upsertDep = function (row, fresh) {
    var d = this.deps[row[0]] || { born: nowSec() };
    d.id = row[0]; d.kind = row[1]; d.p = [row[2], row[3], row[4]]; d.target = d.target || d.p.slice();
    d.yaw = row[5]; d.item = row[6]; d.owner = row[7]; d.radius = row[8];
    d.until = nowSec() + row[9];
    var data = this.itemData(d.item, d.owner) || {};
    var stats = data.stats || {};
    d.spec = stats.deploy || stats.ground_zone || stats.ground_fire || stats.pickups ||
      (stats.strike && stats.strike.zone) || {};
    d.parts = (d.kind === 'pickup' ? null : data.deploy) || null;
    this.deps[d.id] = d;
    if (fresh && this.c.particles) this.c.particles.burst('dust', d.p);
  };

  // --------------------------------------------------------------- effects
  Gear.prototype.onGfx = function (msg) {
    var c = this.c;
    var P = c.particles;
    var self = this;
    var at = msg.p;
    switch (msg.k) {
      case 'beam':
        this.beams[msg.id] = { o: msg.o, e: msg.e, c: msg.c, until: nowSec() + 0.16, m: msg.m || 1 };
        break;
      case 'cone':
        this.flashes.push({ k: 'cone', o: msg.o, d: msg.d, a: msg.a, r: msg.r, c: msg.c, t: 0, life: 0.35 });
        this.spray(msg.o, msg.d, msg.a, msg.r, msg.c);
        c.audio.play('horn', { volume: c.volumeAt(msg.o) });
        break;
      case 'strike':
        this.strikes.push({ p: msg.p, r: msg.r, delay: msg.d, start: nowSec(), item: msg.w,
                            owner: msg.o, model: msg.m });
        c.audio.play('alarm', { volume: c.volumeAt(msg.p) * 0.5 });
        break;
      case 'pulse':
        this.flashes.push({ k: 'ring', p: at, r: msg.r, c: msg.c, t: 0, life: 0.6 });
        break;
      case 'rise':
        P.burst('dust', at);
        if (msg.m === 'zombie' || msg.m === 'skeleton') {
          P.spawn({ p: [at[0], at[1] + 0.5, at[2]], v: [0, 2, 0], life: 1.0, size: 1.6, grow: 1,
                    gravity: 0, blend: 'add', shape: 'wisp', colors: ['#b8ffd2', '#6bff9a'] });
        }
        c.audio.play('raise', { volume: c.volumeAt(at) * 0.7 });
        break;
      case 'unrise':
      case 'poof':
        for (var i = 0; i < 6; i++) {
          P.spawn({ p: [at[0], at[1] + 1.5, at[2]], v: [(Math.random() - 0.5) * 6, Math.random() * 4, (Math.random() - 0.5) * 6],
                    life: 0.7, size: 1.4, grow: 1.2, gravity: 0, blend: 'normal', shape: 'puff',
                    colors: ['#d9d9de', '#a8a8b0'] });
        }
        break;
      case 'blink':
        [msg.a, msg.b].forEach(function (p) {
          for (var j = 0; j < 10; j++) {
            P.spawn({ p: [p[0], p[1] + 2.5, p[2]], v: [(Math.random() - 0.5) * 8, Math.random() * 6, (Math.random() - 0.5) * 8],
                      life: 0.6, size: 0.6, grow: -0.5, gravity: 0, blend: 'add', shape: 'spark',
                      colors: ['#7dff9a', '#ffd96b', '#ffffff'] });
          }
        });
        c.audio.play('whoosh', { volume: c.volumeAt(msg.a) });
        break;
      case 'launch':
        for (var k = 0; k < 8; k++) {
          P.spawn({ p: [at[0], at[1] + 0.4, at[2]], v: [(Math.random() - 0.5) * 4, -2, (Math.random() - 0.5) * 4],
                    life: 0.8, size: 1.2, grow: 1.6, gravity: 0, blend: 'normal', shape: 'puff',
                    colors: ['#cfd3da', '#9a9da5'] });
        }
        c.audio.play('rocket', { volume: c.volumeAt(at) });
        break;
      case 'crit':
        c.hud.toast('<b style="color:#ff6a3d">CRITICAL!</b>');
        break;
      case 'gild':
        for (var g = 0; g < 14; g++) {
          P.spawn({ p: at, v: [(Math.random() - 0.5) * 10, Math.random() * 9, (Math.random() - 0.5) * 10],
                    life: 1.0, size: 0.45, grow: -0.2, gravity: 9, blend: 'normal', shape: 'coin',
                    colors: ['#ffd96b', '#f2c230', '#fff3b0'], spin: 6 });
        }
        c.audio.play('coin', { volume: c.volumeAt(at) });
        break;
      case 'cheat':
        var who = msg.id === c.myId ? c.local : c.players[msg.id];
        if (who && who.pos) P.burst('heal', [who.pos[0], who.pos[1] + 3, who.pos[2]]);
        break;
      case 'freeze':
        var fz = msg.id === c.myId ? c.local : c.players[msg.id];
        if (fz && fz.pos) {
          for (var f = 0; f < 10; f++) {
            P.spawn({ p: [fz.pos[0], fz.pos[1] + 2.5, fz.pos[2]], v: [(Math.random() - 0.5) * 7, Math.random() * 6, (Math.random() - 0.5) * 7],
                      life: 0.8, size: 0.5, grow: -0.3, gravity: 6, blend: 'normal', shape: 'flake',
                      colors: ['#e9f8ff', '#bfe9ff', '#9fd8ff'] });
          }
        }
        break;
      case 'lit':
        c.audio.play('fuse', { volume: 0.6 });
        break;
      case 'stick':
        c.audio.play('beep', { volume: c.volumeAt(msg.p) });
        break;
      case 'ricochet':
      case 'mshot':
      case 'tshot':
        this.flashes.push({ k: 'line', a: msg.a, b: msg.b, c: msg.c || '#ffd96b', t: 0, life: 0.09 });
        if (msg.k !== 'ricochet') c.audio.play(msg.k === 'tshot' ? 'smg' : 'pistol', { volume: c.volumeAt(msg.a) * 0.5 });
        break;
      case 'bite':
        var m = this.minions[msg.id];
        if (m) c.audio.play('growl', { volume: c.volumeAt(m.pos) * 0.5 });
        break;
      case 'parry':
        P.burst('impact', at);
        c.audio.play('clang', { volume: c.volumeAt(at) });
        break;
      case 'pickup':
        P.burst('coin', at);
        c.audio.play('coin', { volume: c.volumeAt(at) });
        break;
      case 'snap':
        P.burst('dust', at);
        c.audio.play('slam', { volume: c.volumeAt(at) });
        break;
      case 'pop':
      case 'bounce':
        P.burst('impact', at);
        break;
      case 'blind':
        this.blind(msg.s || 1.5, msg.v || 'flash');
        break;
      case 'eat':
      case 'use':
        var user = c.players[msg.id];
        if (user) {
          var data = this.itemData(msg.w, msg.id) || {};
          var snd = SOUND[(data.stats || {}).sound] || 'ui';
          c.audio.play(snd, { volume: c.volumeAt(user.pos) * 0.8 });
        }
        break;
    }
  };

  /* Confetti (or whatever the horn is full of) thrown out along a cone. */
  Gear.prototype.spray = function (o, d, a, r, colour) {
    var P = this.c.particles;
    for (var i = 0; i < 26; i++) {
      var yaw = Math.atan2(d[0], d[2]) + (Math.random() - 0.5) * a * 2;
      var pitch = Math.asin(Math.max(-1, Math.min(1, d[1]))) + (Math.random() - 0.5) * a;
      var sp = r * (1.4 + Math.random() * 1.4);
      var v = [Math.sin(yaw) * Math.cos(pitch) * sp, Math.sin(pitch) * sp, Math.cos(yaw) * Math.cos(pitch) * sp];
      P.spawn({ p: [o[0] + d[0] * 1.5, o[1] + d[1] * 1.5, o[2] + d[2] * 1.5], v: v, life: 0.55,
                size: 0.35, grow: 0, gravity: 8, spin: 8, blend: 'normal',
                shape: i % 2 ? 'confetti' : 'streamer',
                colors: [colour || '#ff4fa0', '#3cc8ff', '#f2c230', '#7dff9a'] });
    }
  };

  Gear.prototype.blind = function (secs, style) {
    this.blindUntil = nowSec() + secs;
    var el = this.blindEl;
    if (!el) return;
    el.className = 'gear-blind on style-' + String(style).replace(/[^a-z]/g, '');
    el.style.animationDuration = secs + 's';
  };

  // ----------------------------------------------------------- local rules
  Gear.prototype.has = function (name) {
    var s = this.status[name];
    return !!s && s.until > nowSec();
  };
  Gear.prototype.val = function (name) {
    var s = this.status[name];
    return s && s.until > nowSec() ? s.value * (name === 'freeze' ? s.stacks : 1) : 0;
  };

  Gear.prototype.heldStats = function () {
    var item = this.c.currentWeapon();
    return (item && item.data && item.data.stats) || {};
  };

  Gear.prototype.moveScale = function () {
    if (!this.canMove()) return 0;
    var slow = Math.max(this.val('slow'), Math.min(0.85, this.val('freeze')));
    if (this.has('polymorph')) slow = Math.max(slow, 0.4);
    var scale = 1 - Math.max(0, Math.min(0.9, slow));
    scale *= 1 + Math.max(0, Math.min(1.5, this.val('haste')));
    var held = this.heldStats().held || {};
    scale *= 1 + Math.max(-0.6, Math.min(0.6, held.speed || 0));
    return scale;
  };
  Gear.prototype.canMove = function () {
    var fz = this.status.freeze;
    return !(this.has('root') || this.has('stun') || (fz && fz.until > nowSec() && fz.stacks >= 3));
  };
  Gear.prototype.canJump = function () {
    return this.canMove() && !this.has('jumpless') && !this.has('polymorph');
  };
  Gear.prototype.gravityScale = function () {
    return this.has('lowgrav') ? Math.max(0.2, this.val('lowgrav') || 0.5) : 1;
  };

  /* May the held item be used now?  (stunned, a toad, silenced for gear,
     cooling down, overheated) */
  Gear.prototype.canFire = function (stats) {
    if (this.has('stun') || this.has('polymorph')) return false;
    var fz = this.status.freeze;
    if (fz && fz.until > nowSec() && fz.stacks >= 3) return false;
    var item = this.c.currentWeapon();
    if (!item) return true;
    if (CHARGED[stats.kind]) {
      if (this.has('silence')) return false;
      if ((this.cooldowns[item.item_id] || 0) > nowSec()) return false;
    }
    var meter = this.meters[item.item_id];
    if (stats.kind === 'beam' && meter && meter.on && nowSec() - meter.at < ((stats.heat || {}).lock || 2)) {
      return false;
    }
    return true;
  };

  Gear.prototype.isGear = function (stats) { return !!GEAR_KINDS[stats.kind]; };

  /* What the shooter sees at once, before the server answers. */
  Gear.prototype.localFire = function (stats, origin, dir) {
    var c = this.c;
    var item = c.currentWeapon() || {};
    var sound = SOUND[stats.sound] || 'ui';
    if (stats.kind === 'beam') {
      var reach = stats.range || 80;
      var d = c.physics ? c.physics.rayDistance(origin, dir, reach) : reach;
      this.beams[c.myId] = { o: [origin[0] + dir[0] * 1.2, origin[1] - 0.35 + dir[1] * 1.2, origin[2] + dir[2] * 1.2],
                             e: [origin[0] + dir[0] * d, origin[1] + dir[1] * d, origin[2] + dir[2] * d],
                             c: stats.beam || '#ff2bd6', until: nowSec() + 0.18, m: 1 };
      if (Math.random() < 0.3) c.audio.play('buzz', { volume: 0.35 });
      c.recoil = Math.min(1.4, c.recoil + 0.03);
      return;
    }
    if (stats.kind === 'cone') {
      if (stats.mag) {
        c.ammo[c.slot] = Math.max(0, c.ammo[c.slot] - 1);
        c.updateAmmoHud();
      }
      c.recoil = Math.min(1.4, c.recoil + (stats.recoil || 2) * 0.16);
      this.spray(origin, dir, (stats.cone || {}).angle || 0.5, stats.range || 12, (stats.cone || {}).color);
      c.audio.play(sound === 'ui' ? 'horn' : sound, { volume: 0.9 });
      return;
    }
    if (CHARGED[stats.kind]) {
      this.cooldowns[item.item_id] = nowSec() + (stats.cooldown || 10);
      c.audio.play(sound, { volume: 0.85 });
      this.drawHotbar();
    }
  };

  // ================================================================== HUD
  Gear.prototype.buildHud = function () {
    var hud = document.getElementById('hud') || document.body;
    var root = document.createElement('div');
    root.id = 'gear-hud';
    root.innerHTML = '<div class="gear-status" id="gear-status"></div>' +
      '<div class="gear-meter" id="gear-meter"><span class="l"></span><i><b></b></i></div>' +
      '<div class="gear-toad" id="gear-toad">&#128056; You are a toad</div>';
    (document.getElementById('health-wrap') || hud).parentNode.appendChild(root);
    var host = (document.getElementById('view') || hud).parentNode;
    var vignette = document.createElement('div');
    vignette.className = 'gear-vignette';
    host.appendChild(vignette);
    var blind = document.createElement('div');
    blind.className = 'gear-blind';
    host.appendChild(blind);
    this.blindEl = blind;
    this.vignetteEl = vignette;
    this.statusEl = root.querySelector('#gear-status');
    this.meterEl = root.querySelector('#gear-meter');
    this.toadEl = root.querySelector('#gear-toad');
  };

  Gear.prototype.drawStatusHud = function () {
    var el = this.statusEl;
    if (!el) return;
    var t = nowSec();
    var self = this;
    var names = Object.keys(this.status).filter(function (n) { return self.status[n].until > t; });
    el.innerHTML = names.map(function (n) {
      var s = self.status[n];
      var left = Math.max(0, s.until - t);
      return '<span class="gs ' + (GOOD[n] ? 'good' : 'bad') + '" title="' + (LABEL[n] || n) + '">' +
        (ICON[n] || '&#9679;') + '<em>' + (left >= 10 ? Math.round(left) : left.toFixed(1)) + '</em>' +
        (s.stacks > 1 ? '<sup>' + s.stacks + '</sup>' : '') + '</span>';
    }).join('');
    if (this.toadEl) this.toadEl.style.display = this.has('polymorph') ? 'block' : 'none';
    var v = this.vignetteEl;
    if (v) {
      v.classList.toggle('frost', this.has('freeze') || this.has('slow') || this.has('root'));
      v.classList.toggle('burn', this.has('burn'));
      v.classList.toggle('poison', this.has('poison') || this.has('bleed'));
      v.classList.toggle('stun', this.has('stun'));
    }
  };

  Gear.prototype.drawHotbar = function () {
    var wrap = document.getElementById('hotbar-hud');
    if (!wrap) return;
    var hotbar = this.c.avatar.hotbar || [];
    var t = nowSec();
    for (var i = 0; i < wrap.children.length; i++) {
      var slot = wrap.children[i];
      var item = hotbar[i];
      var cd = slot.querySelector('.gcd');
      var until = item ? (this.cooldowns[item.item_id] || 0) : 0;
      var stats = (item && item.data && item.data.stats) || {};
      if (until > t) {
        if (!cd) {
          cd = document.createElement('div');
          cd.className = 'gcd';
          cd.innerHTML = '<i></i><b></b>';
          slot.appendChild(cd);
        }
        var total = stats.cooldown || 10;
        var left = until - t;
        cd.firstChild.style.height = Math.min(100, left / total * 100) + '%';
        cd.lastChild.textContent = left >= 10 ? Math.ceil(left) : left.toFixed(1);
        cd.style.display = '';
      } else if (cd) {
        cd.style.display = 'none';
      }
    }
  };

  Gear.prototype.drawMeter = function () {
    var el = this.meterEl;
    if (!el) return;
    var item = this.c.currentWeapon();
    var meter = item ? this.meters[item.item_id] : null;
    if (!meter) { el.style.display = 'none'; return; }
    el.style.display = '';
    el.classList.toggle('on', !!meter.on);
    el.querySelector('.l').textContent = meter.l || '';
    el.querySelector('b').style.width = Math.round(Math.max(0, Math.min(1, meter.v)) * 100) + '%';
  };

  // ============================================================== render
  /* A remote player's parts, as statuses change them: a toad instead of the
     avatar, near-invisible when cloaked. */
  Gear.prototype.avatarParts = function (player, parts, time) {
    var bits = player.bits || 0;
    if (bits & BITS.polymorph) return this.toad(player.pos, player.yaw, time);
    if (bits & BITS.cloak) {
      var ally = player.team && player.team === this.c.myTeam;
      var alpha = ally ? 0.35 : 0.07;
      parts.forEach(function (p) { p.a = Math.min(p.a === undefined ? 1 : p.a, alpha); });
    }
    return parts;
  };

  Gear.prototype.toad = function (pos, yaw, time) {
    var hop = Math.abs(Math.sin(time * 5)) * 0.4;
    var model = [
      { t: 'sph', p: [0, 0.8, 0], s: [2.2, 1.4, 2.6], c: '#4fa83c' },
      { t: 'sph', p: [0, 0.9, 0.9], s: [1.6, 1.0, 1.2], c: '#5cbf45' },
      { t: 'sph', p: [0.5, 1.5, 1.1], s: [0.55, 0.55, 0.55], c: '#f6f1a8' },
      { t: 'sph', p: [-0.5, 1.5, 1.1], s: [0.55, 0.55, 0.55], c: '#f6f1a8' },
      { t: 'sph', p: [0.55, 1.55, 1.32], s: [0.22, 0.28, 0.12], c: '#16171b' },
      { t: 'sph', p: [-0.55, 1.55, 1.32], s: [0.22, 0.28, 0.12], c: '#16171b' },
      { t: 'box', p: [0, 0.75, 1.5], s: [1.0, 0.06, 0.1], c: '#2d6b22' },
      { t: 'sph', p: [1.0, 0.3, -0.3], s: [0.9, 0.5, 1.4], c: '#3f8c30' },
      { t: 'sph', p: [-1.0, 0.3, -0.3], s: [0.9, 0.5, 1.4], c: '#3f8c30' }
    ];
    return placeParts(model, [pos[0], pos[1] + hop, pos[2]], [0, yaw, 0], 1);
  };

  /* Statuses drawn on whoever has them (a player, a minion, an infected). */
  Gear.prototype.statusFx = function (key, pos, bits, renderer, dt, height) {
    if (!bits) return;
    var P = this.c.particles;
    var h = height || 5.4;
    var x = pos[0], y = pos[1], z = pos[2];
    var particles = global.Settings ? global.Settings.particles : true;
    if (particles && (bits & BITS.burn) && Math.random() < dt * 22) {
      P.spawn({ p: [x + (Math.random() - 0.5) * 2, y + Math.random() * h * 0.8, z + (Math.random() - 0.5) * 1.6],
                v: [0, 3 + Math.random() * 2, 0], life: 0.5, size: 0.9, grow: -1.2, gravity: -2,
                blend: 'add', shape: 'flame', colors: ['#ffd36a', '#ff8c1a', '#ff3b1a'] });
    }
    if (particles && (bits & BITS.poison) && Math.random() < dt * 10) {
      P.spawn({ p: [x + (Math.random() - 0.5) * 2, y + Math.random() * h, z + (Math.random() - 0.5) * 1.6],
                v: [0, 1.5, 0], life: 0.8, size: 0.4, grow: 0.2, gravity: -1,
                blend: 'add', shape: 'bubble', colors: ['#9dff6b', '#5fd13a'] });
    }
    if (particles && (bits & BITS.bleed) && Math.random() < dt * 8) {
      P.spawn({ p: [x + (Math.random() - 0.5) * 1.4, y + h * 0.6, z + (Math.random() - 0.5) * 1.0],
                v: [0, -1, 0], life: 0.6, size: 0.25, grow: 0, gravity: 18,
                blend: 'normal', shape: 'puff', colors: ['#c4281c', '#8a1410'] });
    }
    if (particles && (bits & BITS.haste) && Math.random() < dt * 14) {
      P.spawn({ p: [x + (Math.random() - 0.5) * 2, y + 0.3, z + (Math.random() - 0.5) * 2],
                v: [0, 0.5, 0], life: 0.4, size: 0.35, grow: -0.6, gravity: 0,
                blend: 'add', shape: 'spark', colors: ['#fff3b0', '#ffd96b'] });
    }
    if (particles && (bits & BITS.stun) && Math.random() < dt * 9) {
      var a = Math.random() * Math.PI * 2;
      P.spawn({ p: [x + Math.cos(a) * 1.2, y + h + 0.4, z + Math.sin(a) * 1.2], v: [Math.cos(a + 1.6) * 3, 0, Math.sin(a + 1.6) * 3],
                life: 0.5, size: 0.4, grow: 0, gravity: 0, blend: 'add', shape: 'star', colors: ['#fff3b0', '#ffd96b'] });
    }
    if (bits & (BITS.freeze | BITS.root)) {
      renderer.pushRaw('box', x, y + h * 0.5, z, 0, 0, 0, 3.6, h + 0.4, 2.6,
                       rgb('#bfe9ff'), (bits & BITS.root) ? 0.42 : 0.22, 0, 3, 0.2, null);
    } else if (bits & BITS.slow) {
      renderer.pushRaw('cyl', x, y + 0.08, z, 0, 0, 0, 4.2, 0.08, 4.2, rgb('#9fd8ff'), 0.35, 0, 2, 0.5, null);
    }
    if (bits & BITS.shield) {
      renderer.pushRaw('sph', x, y + h * 0.5, z, 0, 0, 0, 5.2, h + 1.2, 4.2, rgb('#9fd8ff'), 0.16, 0, 3, 0.4, null);
    }
    if (bits & (BITS.mark | BITS.dazzle)) {
      var bob = Math.sin(nowSec() * 5) * 0.25;
      renderer.pushRaw('cone', x, y + h + 1.6 + bob, z, Math.PI, nowSec() * 2, 0, 0.9, 1.1, 0.9,
                       rgb((bits & BITS.mark) ? '#ff3b4e' : '#fff3b0'), 0.95, 0, 2, 0.6, null);
    }
    if (bits & BITS.might) {
      renderer.pushRaw('cyl', x, y + 0.1, z, 0, nowSec(), 0, 3.6, 0.06, 3.6, rgb('#ff6a3d'), 0.45, 0, 2, 0.6, null);
    }
    if ((bits & BITS.reveal) && key) {
      renderer.queueTag('rv' + key, '◆', '#ff6a3d', '', [x, y + h + 2.6, z], 1.2);
    }
  };

  Gear.prototype.draw = function (renderer, dt, time) {
    var c = this.c;
    var t = nowSec();
    var self = this;
    // ---- statuses on remote players
    Object.keys(c.players).forEach(function (id) {
      var p = c.players[id];
      if (!p.alive || !p.bits) return;
      self.statusFx(id, p.pos, p.bits, renderer, dt);
    });
    // ---- on the infected (Last Light)
    if (c.survival && c.survival.zombies) {
      Object.keys(this.entityBits).forEach(function (id) {
        var z = c.survival.zombies[id];
        if (z && z.pos) self.statusFx('z' + id, z.pos, self.entityBits[id], renderer, dt);
      });
    }
    // ---- minions
    Object.keys(this.minions).forEach(function (id) { self.drawMinion(self.minions[id], renderer, dt, time); });
    // ---- placed things
    Object.keys(this.deps).forEach(function (id) { self.drawDep(self.deps[id], renderer, dt, time); });
    // ---- strikes on their way down
    this.strikes = this.strikes.filter(function (s) { return t - s.start < s.delay + 0.3; });
    this.strikes.forEach(function (s) { self.drawStrike(s, renderer, t); });
    // ---- beams
    Object.keys(this.beams).forEach(function (id) {
      var b = self.beams[id];
      if (b.until < t) { delete self.beams[id]; return; }
      var o = b.o;
      if (parseInt(id, 10) !== c.myId && c.players[id]) {
        var pl = c.players[id];
        o = [pl.pos[0], pl.pos[1] + 4.4, pl.pos[2]];
      }
      // a soft glow round a hot core, thicker as it ramps up
      var w = 0.22 + 0.08 * (b.m || 1);
      self.drawLine(renderer, o, b.e, b.c, w * 3.2, 0.22);
      self.drawLine(renderer, o, b.e, b.c, w, 0.95);
      self.drawLine(renderer, o, b.e, '#ffffff', w * 0.35, 0.95);
      if (Math.random() < dt * 30) c.particles.burst('impact', b.e);
    });
    // ---- flashes: cones, rings, tracer lines
    this.flashes = this.flashes.filter(function (f) { f.t += dt; return f.t < f.life; });
    this.flashes.forEach(function (f) {
      var k = 1 - f.t / f.life;
      if (f.k === 'ring') {
        var r = f.r * (0.2 + 0.8 * (f.t / f.life));
        renderer.pushRaw('cyl', f.p[0], f.p[1] - 1.8, f.p[2], 0, 0, 0, r * 2, 0.12, r * 2, rgb(f.c), 0.45 * k, 0, 2, 0.6, null);
      } else if (f.k === 'line') {
        self.drawLine(renderer, f.a, f.b, f.c, 0.1, 0.8 * k);
      } else if (f.k === 'cone') {
        var len = f.r * (0.4 + 0.6 * (f.t / f.life));
        var mid = [f.o[0] + f.d[0] * len * 0.5, f.o[1] + f.d[1] * len * 0.5, f.o[2] + f.d[2] * len * 0.5];
        var yaw = Math.atan2(f.d[0], f.d[2]);
        var pitch = -Math.asin(Math.max(-1, Math.min(1, f.d[1])));
        var w = Math.tan(f.a) * len * 2;
        renderer.pushRaw('cone', mid[0], mid[1], mid[2], pitch - Math.PI / 2, yaw, 0, w, len, w,
                         rgb(f.c), 0.18 * k, 0, 2, 0.5, null);
      }
    });
    // ---- the HUD bits that change by the frame
    this.hudTimer = (this.hudTimer || 0) - dt;
    if (this.hudTimer <= 0) {
      this.hudTimer = 0.1;
      this.drawHotbar();
      this.drawMeter();
      this.drawStatusHud();
    }
  };

  Gear.prototype.drawLine = function (renderer, a, b, colour, width, alpha) {
    var dx = b[0] - a[0], dy = b[1] - a[1], dz = b[2] - a[2];
    var length = Math.hypot(dx, dy, dz);
    if (length < 0.2) return;
    var yaw = Math.atan2(dx, dz);
    var pitch = -Math.asin(dy / length);
    renderer.pushRaw('box', a[0] + dx * 0.5, a[1] + dy * 0.5, a[2] + dz * 0.5, pitch, yaw, 0,
                     width, width, length, rgb(colour), alpha, 0, 2, 0.9, null);
  };

  Gear.prototype.drawMinion = function (m, renderer, dt, time) {
    var lerp = Math.min(1, dt * 12);
    for (var i = 0; i < 3; i++) m.pos[i] += (m.target[i] - m.pos[i]) * lerp;
    var spec = this.minionSpec(m.item, m.owner);
    var parts;
    var model = spec.model || 'avatar';
    var scale = spec.scale || 1;
    if (model === 'decoy') {
      var owner = this.c.players[m.owner];
      var desc = owner ? owner.avatar : this.c.avatar;
      parts = Avatar.build(desc, { position: m.pos, yaw: m.yaw, time: time,
                                   pose: Avatar.smoothPose(m.memory, 'idle', time + m.seed * 10, 0, desc, dt) });
    } else if (model === 'zombie' && global.Zombies) {
      var anim = m.anim === 'attack' ? Zombies.ANIM.ATTACK : (m.anim === 'run' ? Zombies.ANIM.RUN
        : (m.anim === 'walk' ? Zombies.ANIM.WALK : Zombies.ANIM.WALK));
      var z = { kind: 'common', variant: (m.id % 6), pos: m.pos, yaw: m.yaw, anim: anim, flags: 0,
                memory: m.memory, seed: m.seed };
      parts = Zombies.build(z, spec.area || 'town', time, dt, 0, m.anim === 'idle', null);
      // an ally's dead: a ghostly green glow in the eyes and round the feet
      renderer.pushRaw('cyl', m.pos[0], m.pos[1] + 0.06, m.pos[2], 0, 0, 0, 3.4, 0.05, 3.4,
                       rgb(spec.glow || '#6bff9a'), 0.4, 0, 2, 0.7, null);
    } else if (spec.parts && spec.parts.length) {
      var hop = m.anim === 'walk' || m.anim === 'run' ? Math.abs(Math.sin(time * 9 + m.seed * 6)) * 0.35 * scale : 0;
      parts = placeParts(spec.parts, [m.pos[0], m.pos[1] + hop, m.pos[2]], [0, m.yaw, 0], scale, undefined, time);
    } else {
      var colors = spec.colors || {};
      var d = { colors: { head: colors.head || '#e8d9b8', torso: colors.torso || '#6a5a48',
                          left_arm: colors.arms || colors.head || '#e8d9b8',
                          right_arm: colors.arms || colors.head || '#e8d9b8',
                          left_leg: colors.legs || '#3a3d42', right_leg: colors.legs || '#3a3d42',
                          hips: colors.legs || '#3a3d42' }, items: spec.items || {} };
      var state = m.anim === 'run' ? 'run' : (m.anim === 'walk' || m.anim === 'attack' ? 'walk' : 'idle');
      parts = Avatar.build(d, { position: m.pos, yaw: m.yaw, time: time,
                                pose: Avatar.smoothPose(m.memory, state, time + m.seed * 10, 0, d, dt) });
    }
    if (m.bits & BITS.cloak) parts.forEach(function (p) { p.a = 0.2; });
    parts.forEach(function (p) { renderer.push(p); });
    this.statusFx('m' + m.id, m.pos, m.bits, renderer, dt, 5.0 * scale);
    if (m.hp < 100) {
      // a little health bar over it
      var w = 2.4 * (m.hp / 100);
      renderer.pushRaw('box', m.pos[0], m.pos[1] + 6.4 * scale, m.pos[2], 0, Math.atan2(
        this.c.local.pos[0] - m.pos[0], this.c.local.pos[2] - m.pos[2]), 0, w, 0.18, 0.05,
        rgb(m.hp > 50 ? '#6bff9a' : m.hp > 25 ? '#ffd36a' : '#ff4d3d'), 0.9, 0, 2, 0.8, null);
    }
  };

  Gear.prototype.drawDep = function (d, renderer, dt, time) {
    var t = nowSec();
    if (d.target) {
      var lerp = Math.min(1, dt * 14);
      for (var i = 0; i < 3; i++) d.p[i] += (d.target[i] - d.p[i]) * lerp;
    }
    var spec = d.spec || {};
    var colour = spec.color || (d.kind === 'trap' ? '#c4281c' : '#7dff9a');
    var left = Math.max(0, d.until - t);
    var fade = left < 1 ? left : 1;
    if (d.kind === 'zone' || d.kind === 'banner' || d.kind === 'grill' || d.kind === 'dome') {
      var r = d.radius || 6;
      var pulse = 1 + Math.sin(time * 4) * 0.03;
      renderer.pushRaw('cyl', d.p[0], d.p[1] + 0.07, d.p[2], 0, time * 0.3, 0, r * 2 * pulse, 0.08, r * 2 * pulse,
                       rgb(colour), 0.28 * fade, 0, 2, 0.6, null);
      renderer.pushRaw('torus', d.p[0], d.p[1] + 0.15, d.p[2], 0, 0, 0, r * 2, 0.25, r * 2,
                       rgb(colour), 0.6 * fade, 0, 2, 0.8, null);
      if (d.kind === 'dome') {
        renderer.pushRaw('hemi', d.p[0], d.p[1], d.p[2], 0, 0, 0, r * 2, r, r * 2,
                         rgb(colour), 0.14 * fade, 0, 3, 0.3, null);
      }
      if (global.Settings && Settings.particles && Math.random() < dt * 6) {
        var a = Math.random() * Math.PI * 2, rr = Math.random() * r;
        this.c.particles.spawn({ p: [d.p[0] + Math.cos(a) * rr, d.p[1] + 0.3, d.p[2] + Math.sin(a) * rr],
                                 v: [0, 2, 0], life: 0.9, size: 0.5, grow: -0.3, gravity: -1,
                                 blend: 'add', shape: spec.particle || 'spark', colors: [colour, '#ffffff'] });
      }
    } else if (d.kind === 'pickup') {
      var bob = Math.sin(time * 3 + d.id) * 0.3;
      renderer.pushRaw('disc', d.p[0], d.p[1] + 1.2 + bob, d.p[2], Math.PI / 2, time * 3, 0, 1.4, 1.4, 0.25,
                       rgb(spec.color || '#f2c230'), 1, 0, 1, 0.3, null);
      return;
    } else if (d.kind === 'trap' || d.kind === 'mine') {
      renderer.pushRaw('torus', d.p[0], d.p[1] + 0.2, d.p[2], 0, 0, 0, (d.radius || 3) * 2, 0.15, (d.radius || 3) * 2,
                       rgb(colour), 0.25 * fade, 0, 2, 0.5, null);
    }
    var parts = d.parts;
    if (parts && parts.length) {
      var k = spec.scale || 1;
      placeParts(parts, d.p, [0, d.yaw || 0, 0], k, fade < 1 ? fade : undefined, time).forEach(function (p) {
        renderer.push(p);
      });
    } else if (d.kind === 'turret') {
      renderer.pushRaw('sph', d.p[0], d.p[1] + 2, d.p[2], 0, time * 2, 0, 1.6, 1.6, 1.6, rgb(colour), 1, 0, 1, 0.3, null);
    } else if (d.kind === 'orbit') {
      renderer.pushRaw('rbox', d.p[0], d.p[1] + 0.8, d.p[2], 0, d.yaw || 0, 0, 1.6, 1.4, 3.0, rgb(colour), 1, 0, 1, 0.2, null);
    }
  };

  Gear.prototype.drawStrike = function (s, renderer, t) {
    var age = t - s.start;
    var q = Math.min(1, age / Math.max(0.1, s.delay));
    var r = s.r || 8;
    // the warning: a ring that closes in
    renderer.pushRaw('torus', s.p[0], s.p[1] + 0.2, s.p[2], 0, t * 1.5, 0, r * 2 * (1.2 - 0.2 * q), 0.35,
                     r * 2 * (1.2 - 0.2 * q), rgb('#ff3b4e'), 0.75, 0, 2, 0.9, null);
    renderer.pushRaw('cyl', s.p[0], s.p[1] + 0.08, s.p[2], 0, 0, 0, r * 2 * q, 0.06, r * 2 * q,
                     rgb('#ff3b4e'), 0.22, 0, 2, 0.6, null);
    // what is coming down
    var data = this.itemData(s.item, s.owner) || {};
    var model = data.proj || null;
    var y = s.p[1] + 60 * (1 - q) * (1 - q) + 1.2;
    if (model && model.length) {
      placeParts(model, [s.p[0], y, s.p[2]], [0, t * 2, 0], 1.6, undefined, t).forEach(function (p) {
        renderer.push(p);
      });
    } else {
      renderer.pushRaw('sph', s.p[0], y, s.p[2], 0, 0, 0, 2.4, 2.4, 2.4, rgb('#dff2ff'), 1, 0, 3, 0.5, null);
    }
  };

  /* A projectile fired by an event weapon, drawn as its weapon's own
     ``data.proj`` model pointing along its flight.  False when it has no
     model (the client's own rocket is drawn). */
  Gear.prototype.drawProjectile = function (proj, renderer, dt) {
    if (!proj.w) return false;
    var data = this.itemData(proj.w, proj.o) || {};
    var model = data.proj;
    var stats = data.stats || {};
    if (proj.k && stats.cluster && proj.k === stats.cluster.projectile) {
      renderer.pushRaw('sph', proj.p[0], proj.p[1], proj.p[2], 0, 0, 0, 0.7, 0.7, 0.7,
                       rgb(stats.cluster.color || '#ffcf3a'), 1, 0, 2, 0.8, null);
      return true;
    }
    if (!model || !model.length) return false;
    var v = proj.vel || proj.v || [0, 0, 1];
    if (proj.last) {
      var dv = [proj.p[0] - proj.last[0], proj.p[1] - proj.last[1], proj.p[2] - proj.last[2]];
      if (Math.hypot(dv[0], dv[1], dv[2]) > 0.05) v = dv;
    }
    proj.last = proj.p.slice();
    proj.vel = v;
    var len = Math.hypot(v[0], v[1], v[2]) || 1;
    var yaw = Math.atan2(v[0], v[2]);
    var pitch = -Math.asin(Math.max(-1, Math.min(1, v[1] / len)));
    var age = (performance.now() - (proj.born || 0)) / 1000;
    var roll = stats.boomerang ? 0 : 0;
    var rot = stats.boomerang ? [0, age * 18, 0] : [pitch, yaw, roll];
    placeParts(model, proj.p, rot, stats.proj_scale || 1, undefined, age).forEach(function (p) { renderer.push(p); });
    if (global.Settings && Settings.particles && Math.random() < 0.7 && stats.trail !== false) {
      this.c.particles.spawn({ p: proj.p, v: [0, 0.3, 0], life: 0.35, size: 0.45, grow: -0.4, gravity: 0,
                               blend: 'add', shape: stats.trail_shape || 'spark',
                               colors: stats.trail_colors || [stats.tracer || '#ffd96b', '#ffffff'] });
    }
    return true;
  };

  global.Gear = Gear;
  global.Gear.BITS = BITS;
})(window);
