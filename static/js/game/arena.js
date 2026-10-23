/* The arena worlds -- the shared half of their Game View.

   Fifteen worlds run on one round-and-place engine (app/game/arena/), and
   this is its client: the place being played (only that one is ever sent),
   the arrival sequence when the server moves on to another, the round's
   banners, the results card with its reel of places, the objective panel,
   the things the world puts in the round (carts, chests, bombs, props),
   hold-E channels with their progress bar, lent loadouts, and the camera
   the eliminated watch the round through.

   Each world adds a plugin (static/js/game/arena/<world>.js, registered with
   Arena.define) for what is its own: how its entities look, what the
   objective panel says, what E would do from here, disguises and secrets on
   other players, overlays (a storm wall, wet paint, a blindfold) and its own
   messages.  Nothing here decides anything -- the server says what
   happened, this shows it.

   Messages: ar_area (a round starts, maybe somewhere new, with the map),
   ar_round (setup over), ar_end (the results), ar_me (my side, my secret,
   my channel), ar_pub (what everybody may see about a player), ar_ents (the
   world's things: all, updated, gone), ar_loadout (a lent hotbar) and arx
   (anything a world wants to say to its own plugin). */
(function (global) {
  'use strict';

  var plugins = {};
  var TAU = Math.PI * 2;

  function el(id) { return document.getElementById(id); }
  function dist2(a, b) { return Math.hypot(a[0] - b[0], a[2] - b[2]); }
  function fmt(seconds) {
    seconds = Math.max(0, Math.floor(seconds || 0));
    return Math.floor(seconds / 60) + ':' + (seconds % 60 < 10 ? '0' : '') + seconds % 60;
  }
  function angleTo(from, to) {
    return ((to - from + Math.PI) % TAU + TAU) % TAU - Math.PI;
  }

  // ============================================================ Arena
  function Arena(client) {
    this.client = client;
    var world = client.world || {};
    this.worldId = world.id;
    this.prefix = world.area_prefix || ('ar_' + world.id + '_');
    this.teams = world.teams || {};
    this.ents = {};
    this.pub = {};
    this.me = { team: '', out: false, chan: null };
    this.markers = {};
    this.data = {};
    this.area = '';
    this.areaName = '';
    this.phase = 'setup';
    this.lastState = {};
    this.time = 0;
    this.watchId = 0;
    this.watchSent = 0;
    this.watchSentAt = 0;
    this.useHeld = false;
    this.promptAt = 0;
    this.bannerTimer = 0;
    this.endTimer = 0;
    this.reel = null;
    this.buildHud();
    var make = plugins[this.worldId];
    this.plugin = make ? (make(this) || {}) : {};
  }

  Arena.define = function (worldId, factory) { plugins[worldId] = factory; };
  Arena.plugins = plugins;

  Arena.prototype.call = function (name) {
    var fn = this.plugin[name];
    if (typeof fn !== 'function') return undefined;
    return fn.apply(this.plugin, Array.prototype.slice.call(arguments, 1));
  };

  Arena.prototype.teamInfo = function (team) {
    var info = this.teams[team];
    if (info) return info;
    if (team === 'red') return { name: 'Red', colour: '#c4281c' };
    if (team === 'blue') return { name: 'Blue', colour: '#0d69ac' };
    return { name: team ? team.charAt(0).toUpperCase() + team.slice(1) : '', colour: '#e0a040' };
  };

  // ------------------------------------------------------------- the map
  Arena.prototype.onMap = function (map) {
    var markers = (map && map.markers) || {};
    this.markers = markers;
    this.area = markers.area || '';
    this.areaName = markers.area_name || '';
    this.data = markers.data || {};
    this.call('onMap', map, markers);
  };

  Arena.prototype.points = function (kind) {
    return ((this.markers.points || {})[kind]) || [];
  };

  /* A round starts.  Somewhere new: the whole static world is replaced in
     place and the arrival plays.  The same place again: the world stays,
     its things are reset, and a banner says which round this is. */
  Arena.prototype.onArea = function (msg) {
    var client = this.client;
    this.hideEnd();
    this.phase = 'setup';
    if (msg.map) {
      var map = msg.map;
      client.map = map;
      client.physics = new Physics(map, client.constants);
      client.renderer.setSky(map.sky);
      client.renderer.setAmbient(map.ambient);
      if (Textures.dropSigns) Textures.dropSigns();
      client.staticParts = map.parts;
      client.rebuildStatic();
      this.onMap(map);
    }
    this.ents = {};
    this.call('onArea', msg);
    if (msg.join) return;
    var name = msg.name || this.areaName;
    var Intro = global.AreaIntro;
    var key = this.prefix + msg.area;
    var line = (msg.of > 1 ? 'ROUND ' + msg.in_area + ' OF ' + msg.of + ' HERE' : 'ONE ROUND HERE') +
      (msg.twist_name ? '  ·  ' + msg.twist_name.toUpperCase() : '') + '  ·  GET READY';
    if (msg.intro && Intro && Intro.has(key) &&
        Intro.play(key, { name: name, round: msg.round || 1, kicker: 'NOW ENTERING',
                          logo: (client.world.name || '').toUpperCase(), line: line,
                          accent: (client.world.colors || [])[0] }, client.audio)) {
      return;
    }
    this.banner(name, 'Round ' + (msg.round || 1) + ' -- ' +
                (msg.of > 1 ? 'round ' + msg.in_area + ' of ' + msg.of + ' here' : 'get ready'),
                msg.intro ? 'area' : 'again',
                msg.twist_name ? '<b>' + client.hud.escape(msg.twist_name) + '</b> -- ' +
                  client.hud.escape(msg.twist_blurb || '') : '');
    client.audio.play(msg.intro ? 'whoosh' : 'power', { volume: 0.4 });
  };

  // ------------------------------------------------------------ messages
  Arena.prototype.bind = function (net) {
    var self = this;
    net.on('ar_area', function (msg) { self.onArea(msg); });
    net.on('ar_round', function (msg) { self.onRound(msg); });
    net.on('ar_end', function (msg) { self.onEnd(msg); });
    net.on('ar_me', function (msg) { self.onMe(msg); });
    net.on('ar_pub', function (msg) {
      if (msg.f && Object.keys(msg.f).length) self.pub[msg.id] = msg.f;
      else delete self.pub[msg.id];
      self.call('onPub', msg.id, msg.f || {});
    });
    net.on('ar_ents', function (msg) { self.onEnts(msg); });
    net.on('ar_loadout', function (msg) { self.onLoadout(msg); });
    net.on('arx', function (msg) { self.call('onMsg', msg); });
  };

  Arena.prototype.onRound = function (msg) {
    this.phase = 'active';
    var title = msg.title || ('ROUND ' + msg.round);
    var sub = msg.sub || '';
    var extra = msg.twist_name ? '<b>' + this.client.hud.escape(msg.twist_name) + '</b> -- ' +
      this.client.hud.escape(msg.twist_blurb || '') : '';
    this.banner(title, sub, 'go', extra);
    this.client.audio.play('alarm', { volume: 0.45 });
    this.call('onRound', msg);
  };

  Arena.prototype.onMe = function (msg) {
    var was = this.me;
    this.me = msg;
    if (msg.out && !was.out) this.watchId = 0;
    this.call('onMe', msg, was);
    this.renderChannel();
  };

  Arena.prototype.onEnts = function (msg) {
    var self = this;
    if (msg.all) {
      this.ents = {};
      msg.all.forEach(function (row) { self.upsert(row, true); });
    }
    (msg.u || []).forEach(function (row) { self.upsert(row, false); });
    (msg.d || []).forEach(function (id) {
      var ent = self.ents[id];
      if (ent) self.call('onGone', ent);
      delete self.ents[id];
      self.client.renderer.dropTag('e' + id);
    });
  };

  Arena.prototype.upsert = function (row, fresh) {
    var id = row[0];
    var ent = this.ents[id];
    var pos = [row[2], row[3], row[4]];
    if (!ent) {
      ent = this.ents[id] = { id: id, kind: row[1], pos: pos.slice(), target: pos, yaw: row[5],
                              tyaw: row[5], s: row[6], born: this.time, seed: (id * 7919) % 997 };
      this.call('onEnt', ent, true);
      return ent;
    }
    var before = ent.s;
    ent.kind = row[1];
    ent.target = pos;
    ent.tyaw = row[5];
    ent.s = row[6];
    // something that jumped (a respawned chest, a cart sent home) snaps
    if (fresh || dist2(ent.pos, pos) > 40 || Math.abs(ent.pos[1] - pos[1]) > 30) {
      ent.pos = pos.slice();
      ent.yaw = row[5];
    }
    if (JSON.stringify(before) !== JSON.stringify(ent.s)) this.call('onEnt', ent, false, before);
    return ent;
  };

  Arena.prototype.onSnapshot = function (msg) {
    var self = this;
    (msg.es || []).forEach(function (row) {
      var ent = self.ents[row[0]];
      if (!ent) { self.upsert(row, true); return; }
      ent.target = [row[2], row[3], row[4]];
      ent.tyaw = row[5];
      if (JSON.stringify(ent.s) !== JSON.stringify(row[6])) {
        var before = ent.s;
        ent.s = row[6];
        self.call('onEnt', ent, false, before);
      }
    });
  };

  Arena.prototype.onState = function (state) {
    this.lastState = state || {};
    if (state && state.aphase) this.phase = state.aphase;
    if (state && state.pub) {
      var pub = {};
      Object.keys(state.pub).forEach(function (id) { pub[id] = state.pub[id]; });
      this.pub = pub;
    }
    this.call('onState', state || {});
  };

  /* A lent hotbar (a dodgeball, a paint roller, a revolver): the HUD and the
     ammo counts follow, for me; for anyone else, what they hold. */
  Arena.prototype.onLoadout = function (msg) {
    var client = this.client;
    if (msg.id === client.myId) {
      var avatar = {};
      Object.keys(client.avatar).forEach(function (k) { avatar[k] = client.avatar[k]; });
      avatar.hotbar = msg.hotbar || [];
      client.avatar = avatar;
      client.slot = msg.slot || 0;
      client.stowed = false;
      client.reloadUntil = 0;
      for (var i = 0; i < 5; i++) {
        var item = avatar.hotbar[i];
        var stats = item && item.data && item.data.stats;
        client.ammo[i] = stats && stats.mag ? stats.mag : 0;
        client.reserve[i] = stats && stats.reserve ? stats.reserve : 0;
      }
      client.hud.buildHotbar(avatar.hotbar, client.slot);
      client.hud.setSlot(client.slot);
      client.updateAmmoHud();
      if (client.scoped) { client.scoped = false; client.hud.setScope(false); }
    } else {
      var player = client.players[msg.id];
      if (player) {
        var copy = {};
        Object.keys(player.avatar || {}).forEach(function (k) { copy[k] = player.avatar[k]; });
        copy.hotbar = msg.hotbar || [];
        player.avatar = copy;
        player.slot = msg.slot || 0;
      }
    }
  };

  // ------------------------------------------------------------ results
  Arena.prototype.onEnd = function (msg) {
    var client = this.client;
    var hud = client.hud;
    var esc = hud.escape.bind(hud);
    this.phase = 'ended';
    this.lastEnd = msg;
    var won = false;
    if (msg.winner) {
      won = msg.winner === client.myTeam || String(msg.winner) === String(client.myId);
    }
    client.audio.play(won ? 'wavewin' : (msg.winner ? 'capture' : 'tick'));
    var cols = msg.cols || [['score', 'Score']];
    var rows = (msg.rows || []).map(function (r, i) {
      var info = this.teamInfo(r.team);
      var colour = Object.keys(this.teams).length > 1 ? info.colour : '';
      return '<tr' + (r.id === client.myId ? ' class="me"' : '') + '><td>' + (i + 1) + '</td>' +
        '<td class="n">' + (colour ? '<i class="ar-dot" style="background:' + colour + '"></i>' : '') +
        esc(r.name) + '</td>' + cols.map(function (c) {
          var v = r[c[0]];
          return '<td>' + (typeof v === 'number' ? Math.round(v * 10) / 10 : esc(v === undefined ? '' : v)) +
            '</td>';
        }).join('') + '</tr>';
    }, this).join('');
    var scores = '';
    var teamIds = Object.keys(this.teams);
    if (teamIds.length > 1 && msg.scores) {
      scores = '<div class="ar-end-scores">' + teamIds.map(function (t) {
        var info = this.teamInfo(t);
        return '<span style="--c:' + info.colour + '"><b>' + esc(info.name) + '</b>' +
          Math.round((msg.scores[t] || 0) * 10) / 10 + '</span>';
      }, this).join('') + '</div>';
    }
    var extra = this.call('endExtra', msg) || '';
    var next = msg.moving
      ? '<div id="ar-reel"></div><div class="ll-wipe-next ll-after" id="ar-end-after">' +
        'Next: <b>' + esc(msg.next) + '</b> in <span id="ar-end-count">' + Math.round(msg['in'] || 12) +
        '</span>s</div>'
      : '<div class="ll-wipe-next">Round ' + (msg.in_area + 1) + ' of ' + msg.of + ' at <b>' +
        esc(msg.area) + '</b> in <span id="ar-end-count">' + Math.round(msg['in'] || 9) + '</span>s</div>';
    var card = el('ar-end');
    if (!card) return;
    card.innerHTML = '<div class="ar-end-in">' +
      '<div class="ar-end-k">' + esc(client.world.name || '') + ' &bull; ' + esc(msg.area) +
      ' &bull; round ' + msg.in_area + ' of ' + msg.of + '</div>' +
      '<h2 style="color:' + (msg.colour || '#f4e6c8') + '">' + esc(msg.title || 'ROUND OVER') + '</h2>' +
      '<div class="ar-end-s">' + esc(msg.reason || '') +
      (msg.mvp ? ' &bull; MVP <b>' + esc(msg.mvp) + '</b>' : '') + '</div>' + scores + extra +
      '<table><thead><tr><th></th><th class="n">Player</th>' +
      cols.map(function (c) { return '<th>' + esc(c[1]) + '</th>'; }).join('') +
      '</tr></thead><tbody>' + rows + '</tbody></table>' + next + '</div>';
    card.classList.add('on');
    if (won) card.classList.add('won'); else card.classList.remove('won');
    if (this.reel) this.reel.stop();
    this.reel = null;
    var Intro = global.AreaIntro;
    var prefix = this.prefix;
    if (msg.moving && Intro && Intro.reel) {
      var items = (msg.reel || []).map(function (it) { return { id: prefix + it.id, name: it.name }; });
      this.reel = Intro.reel(el('ar-reel'), items, prefix + msg.next_id, client.audio, 2300,
                             function () {
                               var after = el('ar-end-after');
                               if (after) after.classList.add('on');
                             }, { title: 'MOVING ON', landed: 'NEXT STOP' });
    } else if (msg.moving) {
      var after = el('ar-end-after');
      if (after) after.classList.add('on');
    }
    var left = Math.round(msg['in'] || 9);
    clearInterval(this.endTimer);
    this.endTimer = setInterval(function () {
      left -= 1;
      var node = el('ar-end-count');
      if (node) node.textContent = Math.max(0, left);
      if (left <= 0) clearInterval(this.endTimer);
    }.bind(this), 1000);
    this.call('onEnd', msg);
  };

  Arena.prototype.hideEnd = function () {
    clearInterval(this.endTimer);
    if (this.reel) this.reel.stop();
    this.reel = null;
    var card = el('ar-end');
    if (card) card.classList.remove('on');
  };

  // ------------------------------------------------------------- hooks
  Arena.prototype.moveScale = function () {
    var v = this.call('moveScale');
    return v === undefined ? 1 : v;
  };
  Arena.prototype.canJump = function () {
    var v = this.call('canJump');
    return v === undefined ? true : !!v;
  };
  Arena.prototype.jumpScale = function () {
    var v = this.call('jumpScale');
    return v === undefined ? 1 : v;
  };
  Arena.prototype.gravityScale = function () {
    var v = this.call('gravityScale');
    return v === undefined ? 1 : v;
  };
  Arena.prototype.canFire = function (stats) {
    if (this.me.out) return false;
    var v = this.call('canFire', stats);
    return v === undefined ? true : !!v;
  };
  Arena.prototype.forceThird = function () { return !!this.call('forceThird'); };
  Arena.prototype.hideViewModel = function () { return !!this.call('hideViewModel'); };

  /* E: the server decides what it does (on_use); a plugin may add to it. */
  Arena.prototype.useDown = function (repeat) {
    if (repeat) return;
    if (this.call('useDown') === false) return;
    this.useHeld = true;
    this.client.net.send({ t: 'act', k: 'use' });
  };
  Arena.prototype.useUp = function () {
    if (!this.useHeld) return;
    this.useHeld = false;
    this.client.net.send({ t: 'act', k: 'unuse' });
  };
  Arena.prototype.act = function (kind, extra) {
    var msg = { t: 'act', k: kind };
    if (extra) Object.keys(extra).forEach(function (k) { msg[k] = extra[k]; });
    this.client.net.send(msg);
  };

  // ------------------------------------------------------------ watching
  Arena.prototype.watchable = function () {
    var client = this.client;
    var pub = this.pub;
    var out = [];
    Object.keys(client.players).forEach(function (id) {
      var player = client.players[id];
      if (!player.alive) return;
      if (pub[id] && pub[id].x) return;
      out.push(player);
    });
    out.sort(function (a, b) { return a.id - b.id; });
    return out;
  };

  Arena.prototype.isWatching = function () {
    return !this.client.local.alive && !!this.me.out && this.watchable().length > 0;
  };

  Arena.prototype.cycle = function (step) {
    var list = this.watchable();
    if (!list.length) return;
    var index = 0;
    for (var i = 0; i < list.length; i++) if (list[i].id === this.watchId) index = i;
    index = (index + step + list.length) % list.length;
    this.watchId = list[index].id;
    this.client.audio.play('ui', { volume: 0.3 });
  };

  Arena.prototype.watched = function () {
    var list = this.watchable();
    if (!list.length) return null;
    for (var i = 0; i < list.length; i++) if (list[i].id === this.watchId) return list[i];
    this.watchId = list[0].id;
    return list[0];
  };

  Arena.prototype.camera = function () {
    var client = this.client;
    var target = this.watched();
    if (!target) return null;
    var yaw = client.local.yaw, pitch = Math.max(-1.1, Math.min(0.9, client.local.pitch));
    var cp = Math.cos(pitch);
    var dir = [Math.sin(yaw) * cp, Math.sin(pitch), Math.cos(yaw) * cp];
    var pivot = [target.pos[0], target.pos[1] + 5.4, target.pos[2]];
    var back = [-dir[0], -dir[1], -dir[2]];
    var distance = 16;
    if (client.physics) {
      distance = Math.min(16, Math.max(3.5, client.physics.rayDistance(pivot, back, 18) - 1.4));
    }
    return { eye: [pivot[0] + back[0] * distance, pivot[1] + back[1] * distance,
                   pivot[2] + back[2] * distance], yaw: yaw, pitch: pitch };
  };

  Arena.prototype.reportWatch = function () {
    var target = (!this.client.local.alive && this.me.out) ? this.watched() : null;
    var id = target ? target.id : 0;
    if (id === this.watchSent && (!id || this.time - this.watchSentAt < 5)) return;
    this.watchSent = id;
    this.watchSentAt = this.time;
    this.client.net.send({ t: 'act', k: 'watch', id: id });
  };

  // ------------------------------------------------------- other players
  Arena.prototype.avatarParts = function (player, parts) {
    var out = this.call('avatar', player, parts, this.pub[player.id] || {});
    return out || parts;
  };
  Arena.prototype.selfParts = function (parts) {
    var out = this.call('selfAvatar', parts, this.me);
    return out || parts;
  };
  /* The name over somebody's head: their side's colour; a world can hide it
     (a prop, a murderer among guests) or add to it. */
  Arena.prototype.nameTag = function (player) {
    var pub = this.pub[player.id] || {};
    var custom = this.call('nameTag', player, pub);
    if (custom === false) return false;
    if (custom) return custom;
    var info = this.teamInfo(player.team);
    var light = info.light || info.colour || '#ffe08a';
    return { text: player.name, colour: light, sub: null };
  };

  Arena.prototype.rayHit = function (origin, dir, distance) {
    var v = this.call('rayHit', origin, dir, distance);
    return v === undefined ? distance : v;
  };

  Arena.prototype.drawProjectile = function (proj, renderer, dt) {
    var fn = this.plugin.projectile && this.plugin.projectile[proj.k];
    if (!fn) return false;
    fn.call(this.plugin, renderer, proj, this.time, dt);
    return true;
  };

  // -------------------------------------------------------------- hud
  Arena.prototype.buildHud = function () {
    if (el('ar-hud')) return;
    var root = document.createElement('div');
    root.id = 'ar-hud';
    root.innerHTML =
      '<div id="ar-banner"><div class="t"></div><div class="s"></div><div class="x"></div></div>' +
      '<div id="ar-side"></div>' +
      '<div id="ar-chan"><div class="s"></div><div class="ll-bar"><i></i></div></div>' +
      '<div id="ar-watch"><div class="t"></div><div class="s"></div></div>' +
      '<div id="ar-blind"><div class="t"></div><div class="s"></div></div>' +
      '<div id="ar-over"></div>' +
      '<div id="ar-end"></div>';
    var parent = document.querySelector('#game-root .hud') || document.body;
    parent.appendChild(root);
  };

  Arena.prototype.banner = function (title, sub, kind, extra) {
    var node = el('ar-banner');
    if (!node) return;
    node.querySelector('.t').textContent = title;
    node.querySelector('.s').textContent = sub || '';
    node.querySelector('.x').innerHTML = extra || '';
    node.className = 'on ' + (kind || '');
    clearTimeout(this.bannerTimer);
    this.bannerTimer = setTimeout(function () { node.className = ''; }, 4200);
  };

  /* The objective panel at the top of the screen.  The world's plugin
     writes its middle (head, timer, sub); the team scores either side are
     drawn here from the round's scores. */
  Arena.prototype.updateObjective = function (state) {
    var red = el('score-red'), blue = el('score-blue');
    var mode = el('score-mode'), timer = el('obj-timer'), sub = el('obj-sub');
    var panel = el('objective');
    var bar = el('cartbar');
    if (bar) bar.style.display = 'none';
    this.onState(state);
    var teamIds = Object.keys(this.teams);
    var scores = state.scores || {};
    if (red) red.textContent = '';
    if (blue) blue.textContent = '';
    var view = this.call('objective', state) || {};
    var phase = state.aphase || 'setup';
    var head = view.head;
    if (head === undefined) {
      head = phase === 'setup' ? 'GET READY' : (phase === 'ended' ? 'ROUND OVER' : 'ROUND ' + (state.round || 1));
    }
    if (mode) {
      var sides = '';
      if (teamIds.length > 1 && view.scores !== false) {
        sides = '<span class="ar-scores">' + teamIds.map(function (t) {
          var info = this.teamInfo(t);
          var value = view.scoreText ? view.scoreText(t, scores[t] || 0) : Math.round(scores[t] || 0);
          return '<span class="ar-score' + (t === this.client.myTeam ? ' mine' : '') +
            '" style="--c:' + info.colour + '"><i></i>' + value + '</span>';
        }, this).join('') + '</span>';
      }
      mode.innerHTML = '<span class="ll-wave">' + head + '</span>' + sides +
        '<span class="ll-area">' + this.client.hud.escape(state.area_name || '') +
        (state.of > 1 ? ' &middot; ' + state.in_area + '/' + state.of : '') + '</span>';
    }
    if (timer) {
      if (view.timer !== undefined) timer.innerHTML = view.timer;
      else if (phase === 'setup') timer.textContent = 'Starts in ' + fmt(state.phase_left);
      else if (phase === 'active') timer.textContent = fmt(state.time_left);
      else timer.textContent = 'Next round in ' + fmt(state.phase_left);
    }
    if (sub) {
      var bits = [];
      if (view.sub) bits.push(view.sub);
      if (state.twist_name) bits.push('<b style="color:#ffd95e">' + state.twist_name + '</b>');
      sub.innerHTML = bits.join(' &bull; ');
    }
    if (panel) panel.classList.toggle('urgent', !!view.urgent);
    var side = el('ar-side');
    if (side) {
      var html = this.call('side', state);
      side.innerHTML = html || '';
      side.classList.toggle('on', !!html);
    }
  };

  Arena.prototype.renderChannel = function () {
    var node = el('ar-chan');
    if (!node) return;
    var chan = this.me.chan;
    node.classList.toggle('on', !!chan);
    if (!chan) return;
    node.querySelector('.s').textContent = chan[0];
    node.querySelector('i').style.width = Math.min(100, chan[1] * 100) + '%';
  };

  Arena.prototype.updatePrompt = function () {
    var hud = this.client.hud;
    if (!this.client.local.alive || this.me.out) { hud.setPrompt(null); return; }
    if (this.me.chan) { hud.setPrompt('Keep holding <b>E</b>'); return; }
    var text = this.call('prompt');
    hud.setPrompt(text || null);
  };

  Arena.prototype.scoreboard = function (rows) {
    var board = el('sb-body');
    if (!board) return false;
    var client = this.client;
    var esc = client.hud.escape.bind(client.hud);
    var cols = (this.lastEnd && this.lastEnd.cols) || (client.world.cols || []).map(function (c) {
      return c;
    });
    var head = document.querySelector('#scoreboard thead tr');
    var key = 'arena:' + cols.map(function (c) { return c[0]; }).join(',');
    if (head && head.dataset.arena !== key) {
      head.dataset.arena = key;
      head.innerHTML = '<th>Player</th><th>Side</th>' + cols.map(function (c) {
        return '<th>' + esc(c[1]) + '</th>';
      }).join('') + '<th>Score</th>';
    }
    var self = this;
    board.innerHTML = (rows || []).map(function (row) {
      var info = self.teamInfo(row.team);
      var side = self.call('sideLabel', row) || (Object.keys(self.teams).length > 1 ? info.name : '');
      return '<tr class="' + (row.id === client.myId ? 'me' : '') + (row.out ? ' out' : '') + '">' +
        '<td class="who" data-username="' + esc(row.name) + '">' +
        (Object.keys(self.teams).length > 1 ? '<i class="ar-dot" style="background:' + info.colour + '"></i>' : '') +
        esc(row.name) + '</td><td>' + esc(side) + (row.out ? ' <span class="ar-outtag">out</span>' : '') +
        '</td>' + cols.map(function (c) {
          var v = row[c[0]];
          return '<td>' + (typeof v === 'number' ? Math.round(v * 10) / 10 : esc(v === undefined ? '' : v)) + '</td>';
        }).join('') + '<td>' + (row.score || 0) + '</td></tr>';
    }).join('');
    var title = el('sb-title');
    if (title) {
      title.textContent = client.world.name + ' -- ' + (this.lastState.area_name || '') +
        ' -- instance #' + (client.state.instance || '?') + ' (' + (rows || []).length + ' players)';
    }
    return true;
  };

  Arena.prototype.updateHud = function (dt) {
    var client = this.client;
    var watch = el('ar-watch');
    if (watch) {
      var dead = !client.local.alive && this.me.out;
      watch.classList.toggle('on', dead);
      if (dead) {
        var target = this.watched();
        watch.querySelector('.t').textContent = target ? 'Watching ' + target.name : 'Nobody left standing';
        watch.querySelector('.s').textContent = (this.call('outText') ||
          'You are out until the next round') + (target ? '  --  click to switch' : '');
      }
    }
    var blind = el('ar-blind');
    if (blind) {
      var text = this.call('blind');
      blind.classList.toggle('on', !!text);
      if (text) {
        blind.querySelector('.t').innerHTML = text[0] || '';
        blind.querySelector('.s').innerHTML = text[1] || '';
      }
    }
    var over = el('ar-over');
    if (over) {
      var tint = this.call('overlay');
      over.style.background = tint || 'none';
      over.classList.toggle('on', !!tint);
    }
    if (this.time - this.promptAt > 0.2) {
      this.promptAt = this.time;
      this.updatePrompt();
    }
    this.reportWatch();
  };

  // ------------------------------------------------------------ drawing
  /* Draw parts given in an entity's own frame (origin at its feet, facing
     +Z) at its place and heading.  Euler rotations compose with the yaw
     because the renderer applies Ry last. */
  Arena.prototype.pushModel = function (renderer, parts, pos, yaw, scale) {
    var c = Math.cos(yaw || 0), s = Math.sin(yaw || 0);
    var k = scale || 1;
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i];
      var x = p.p[0] * k, z = p.p[2] * k;
      var out = { t: p.t, c: p.c, s: [p.s[0] * k, p.s[1] * k, p.s[2] * k],
                  p: [pos[0] + x * c + z * s, pos[1] + p.p[1] * k, pos[2] - x * s + z * c],
                  r: [p.r ? p.r[0] : 0, (p.r ? p.r[1] : 0) + (yaw || 0), p.r ? p.r[2] : 0] };
      if (p.m) out.m = p.m;
      if (p.a !== undefined) out.a = p.a;
      if (p.dec) out.dec = p.dec;
      if (p.st) out.st = p.st;
      renderer.push(out);
    }
  };

  Arena.prototype.draw = function (renderer, dt) {
    this.time += dt;
    var time = this.time;
    var camera = renderer.eye || this.client.local.pos;
    var lerp = Math.min(1, dt * 12);
    var models = this.plugin.models || {};
    var drawers = this.plugin.drawers || {};
    var far = Math.min(renderer.far || 900, 800);
    for (var id in this.ents) {
      var ent = this.ents[id];
      ent.pos[0] += (ent.target[0] - ent.pos[0]) * lerp;
      ent.pos[1] += (ent.target[1] - ent.pos[1]) * lerp;
      ent.pos[2] += (ent.target[2] - ent.pos[2]) * lerp;
      ent.yaw += angleTo(ent.yaw, ent.tyaw) * Math.min(1, dt * 10);
      var d = Math.hypot(ent.pos[0] - camera[0], ent.pos[2] - camera[2]);
      if (d > far) continue;
      ent.d = d;
      if (drawers[ent.kind]) {
        drawers[ent.kind].call(this.plugin, renderer, ent, time, dt);
      } else if (models[ent.kind]) {
        var parts = models[ent.kind].call(this.plugin, ent, time);
        if (parts && parts.length) this.pushModel(renderer, parts, ent.pos, ent.yaw, 1);
      }
      var tag = this.plugin.tags && this.plugin.tags[ent.kind];
      if (tag && Settings.showNames) {
        var info = tag.call(this.plugin, ent, d);
        if (info) {
          renderer.queueTag('e' + ent.id, info.text, info.colour || '#ffe08a', info.sub || '',
                            [ent.pos[0], ent.pos[1] + (info.y || 8), ent.pos[2]],
                            Math.max(0.85, Math.min(3.0, 0.85 + d * 0.011)));
        } else {
          renderer.dropTag('e' + ent.id);
        }
      }
    }
    this.call('draw', renderer, dt, time);
    this.updateHud(dt);
  };

  /* A ring on the ground (capture zones, blast radii, the storm's edge). */
  Arena.prototype.ring = function (renderer, centre, radius, colour, alpha, segments, height) {
    var n = segments || Math.max(16, Math.min(96, Math.round(radius * 1.2)));
    var rgb = GLX.mat.hexToRgb(colour);
    var len = TAU * radius / n * 1.06;
    for (var i = 0; i < n; i++) {
      var a = (i + 0.5) / n * TAU;
      renderer.pushRaw('box', centre[0] + Math.sin(a) * radius, centre[1] + (height || 0.3) / 2,
                       centre[2] + Math.cos(a) * radius, 0, a, 0, len, height || 0.3, 0.35,
                       rgb, alpha === undefined ? 0.6 : alpha, 0, 2, 0.7, null);
    }
  };

  /* A soft beam of light straight up (an objective you can see across the map). */
  Arena.prototype.beam = function (renderer, pos, colour, height, width, alpha) {
    var rgb = GLX.mat.hexToRgb(colour);
    var h = height || 60;
    renderer.pushRaw('cyl', pos[0], pos[1] + h / 2, pos[2], 0, 0, 0, width || 2.2, h, width || 2.2,
                     rgb, alpha === undefined ? 0.18 : alpha, 0, 2, 0.9, null);
  };

  global.Arena = Arena;
})(window);
