/* The event worlds -- the half of the Game View they all share.

   An event world (app/game/worlds/arena.py) is played in one of several
   areas at a time.  Everything that comes from that is drawn here, for all
   of them alike:

     * a new area: the whole static world is swapped in place and the
       area's own arrival sequence plays (game/area_intro.js);
     * the round's three phases: the countdown, the round, the results
       card -- and, when the area has had its rounds, the reel that spins
       and lands on the next one;
     * spectating: the fallen (and anybody who joins a round already under
       way) watch over the shoulder of the living; click to switch;
     * the world's own kit for a round (a dodgeball, a revolver) in place of
       what the avatar carries, for you and for everybody else's hands;
     * solids that come and go: start gates, doors, falling floors;
     * the objective panel, the scoreboard, the hold-E bar and the prompt.

   What is particular to one world -- its carts, props, paint or crowns --
   is that world's plugin (static/js/worlds/<id>.js), registered with
   Arena.register(worldId, function (arena) { return { ...hooks } }).  Every
   hook is optional:

     init()  onMap(map)  onArea(msg)  onState(state)  onSnapshot(msg)
     onMe(me)  onEnd(msg)  messages: {type: fn(msg)}  hud(state) -> panel
     prompt() -> text  draw(renderer, dt, time)  avatarParts(player, parts,
     self) -> parts  hidden(player) -> bool  nameTag(player) -> {colour, sub}
     moveScale()  canJump()  gravityScale()  canFire(stats)  isCustom(stats)
     localFire(stats, origin, dir) -> handled  useDown(repeat) -> handled
     useUp()  rayHit(origin, dir, dist) -> dist  camera() -> {eye,yaw,pitch}
     scoreHead() -> html  scoreRow(row) -> html  introInfo(msg) -> info
     thirdPerson() -> bool (your own body drawn, not the view model)
     reloadDown() -> handled  noPet(id) -> bool  disguised(player) -> bool
     (no hat effects: whatever they are wearing is not a person)

   Nothing here decides anything: the server says what happened, this
   shows it. */
(function (global) {
  'use strict';

  var MODES = {};

  function el(id) { return document.getElementById(id); }
  function esc(text) {
    return String(text == null ? '' : text).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function fmt(seconds) {
    seconds = Math.max(0, Math.round(seconds || 0));
    var m = Math.floor(seconds / 60), s = seconds % 60;
    return m + ':' + (s < 10 ? '0' : '') + s;
  }
  function clone(list) { return list ? list.map(function (x) { return x; }) : list; }

  // ============================================================= Arena
  function Arena(client) {
    this.client = client;
    this.world = client.world;
    this.me = { team: '', out: false, role: '' };
    this.state = {};
    this.markers = {};
    this.map = null;
    this.dynamic = {};
    this.dynOn = {};
    this.watchId = 0;
    this.watchSent = -1;
    this.watchSentAt = 0;
    this.useHeld = false;
    this.ownHotbar = clone(client.avatar.hotbar || []);
    this.pendingLoads = {};
    this.time = 0;
    this.phase = 'setup';
    this.phaseLeft = 0;
    this.lastCount = -1;
    this.hold = null;
    this.buildHud();
    var factory = MODES[this.world.id];
    this.mode = factory ? (factory(this) || {}) : {};
    if (this.mode.init) this.mode.init();
  }

  Arena.register = function (worldId, factory) { MODES[worldId] = factory; };
  Arena.fmt = fmt;
  Arena.esc = esc;

  Arena.prototype.call = function (name) {
    var fn = this.mode[name];
    if (typeof fn !== 'function') return undefined;
    return fn.apply(this.mode, Array.prototype.slice.call(arguments, 1));
  };

  // ------------------------------------------------------------- hud
  Arena.prototype.buildHud = function () {
    var host = document.querySelector('#game-root .hud') || document.body;
    var make = function (id, cls) {
      var node = document.createElement('div');
      node.id = id;
      if (cls) node.className = cls;
      host.appendChild(node);
      return node;
    };
    this.bannerNode = make('ar-banner');
    this.roleNode = make('ar-role');
    this.specNode = make('ar-spec');
    this.holdNode = make('ar-hold');
    this.holdNode.innerHTML = '<div class="lbl"></div><div class="bar"><i></i></div>';
    this.endNode = make('ar-end', 'overlay-like');
    this.sideNode = make('ar-side');
    this.flash = make('ar-flash');
    var objective = el('objective');
    if (objective) {
      objective.classList.add('arena');
      objective.innerHTML =
        '<div class="ar-top"><span class="ar-l"></span><span class="ar-mid">' +
        '<span class="ar-title"></span><span class="ar-timer"></span></span>' +
        '<span class="ar-r"></span></div><div class="ar-sub"></div><div class="ar-bars"></div>';
    }
    var accent = (this.world.colors || [])[0];
    if (accent) document.documentElement.style.setProperty('--ar-accent', accent);
  };

  Arena.prototype.banner = function (title, sub, kind, ms) {
    var node = this.bannerNode;
    if (!node) return;
    node.className = 'on ' + (kind || '');
    node.innerHTML = '<b>' + title + '</b>' + (sub ? '<span>' + sub + '</span>' : '');
    clearTimeout(this._bannerTimer);
    this._bannerTimer = setTimeout(function () { node.className = ''; }, ms || 3200);
  };

  Arena.prototype.setRole = function (html, kind) {
    if (!this.roleNode) return;
    this.roleNode.className = html ? 'on ' + (kind || '') : '';
    this.roleNode.innerHTML = html || '';
  };

  Arena.prototype.setHold = function (fraction, label) {
    var node = this.holdNode;
    if (!node) return;
    if (fraction === null || fraction === undefined) { node.classList.remove('on'); return; }
    node.classList.add('on');
    node.querySelector('.lbl').innerHTML = label || '';
    node.querySelector('i').style.width = Math.round(Math.max(0, Math.min(1, fraction)) * 100) + '%';
  };

  Arena.prototype.side = function (html) {
    if (!this.sideNode) return;
    this.sideNode.innerHTML = html || '';
    this.sideNode.classList.toggle('on', !!html);
  };

  Arena.prototype.flashScreen = function (colour, ms) {
    var node = this.flash;
    if (!node) return;
    node.style.background = colour || 'rgba(255,255,255,0.5)';
    node.classList.remove('on');
    void node.offsetWidth;
    node.classList.add('on');
    setTimeout(function () { node.classList.remove('on'); }, ms || 400);
  };

  // ------------------------------------------------------------- net
  Arena.prototype.bind = function (net) {
    var self = this;
    net.on('aarea', function (msg) { self.onArea(msg); });
    net.on('aphase', function (msg) { self.onPhase(msg); });
    net.on('aend', function (msg) { self.onEnd(msg); });
    net.on('ame', function (msg) { self.onMe(msg); });
    net.on('aload', function (msg) { self.onLoad(msg); });
    net.on('adyn', function (msg) { self.onDynamic(msg.on || {}); });
    net.on('join', function (msg) {
      var id = msg.player && msg.player.id;
      if (id && self.pendingLoads[id]) {
        var pending = self.pendingLoads[id];
        delete self.pendingLoads[id];
        self.onLoad(pending);
      }
    });
    net.on('died', function (msg) {
      if (msg.spectate) self.client.hud.setRespawn(null);
    });
    var messages = this.mode.messages || {};
    Object.keys(messages).forEach(function (type) {
      net.on(type, function (msg) { messages[type].call(self.mode, msg); });
    });
  };

  // ------------------------------------------------------------- the map
  Arena.prototype.onMap = function (map) {
    var markers = (map && map.markers) || {};
    this.map = map;
    this.markers = markers;
    this.dynamic = markers.dynamic || {};
    this.dynOn = {};
    var self = this;
    Object.keys(this.dynamic).forEach(function (key) { self.dynOn[key] = !!self.dynamic[key].on; });
    var dyn = (this.state && this.state.dyn) || {};
    Object.keys(dyn).forEach(function (key) {
      if (key in self.dynOn) self.dynOn[key] = !!dyn[key];
    });
    this.syncDynamic();
    this.call('onMap', map);
  };

  Arena.prototype.swapMap = function (map) {
    var client = this.client;
    client.map = map;
    client.physics = new Physics(map, client.constants);
    client.renderer.setSky(map.sky);
    client.renderer.setAmbient(map.ambient);
    if (Textures.dropSigns) Textures.dropSigns();
    client.staticParts = map.parts;
    client.rebuildStatic();
    this.onMap(map);
  };

  Arena.prototype.gravityScale = function () {
    var g = (this.map && this.map.gravity) || 1;
    var extra = this.call('gravityScale');
    return g * (extra === undefined ? 1 : extra);
  };

  Arena.prototype.onArea = function (msg) {
    var client = this.client;
    this.hideEnd();
    if (msg.map) this.swapMap(msg.map);
    this.phase = msg.phase || 'setup';
    this.phaseLeft = msg.left || 0;
    this.phaseAt = performance.now() / 1000;
    this.lastCount = -1;
    var info = this.call('introInfo', msg) || {};
    var scene = info.scene || ((this.world.prefix || '') + '_' + msg.area);
    var Intro = global.AreaIntro;
    var line = msg.rounds > 1 ? 'Round ' + msg.area_round + ' of ' + msg.rounds + ' here'
      : 'One round, then the server moves on';
    var played = false;
    var intro = msg.intro || (msg.join && msg.phase === 'setup' && (msg.left || 0) > 6.5);
    if (intro && Intro && Intro.has(scene)) {
      played = Intro.play(scene, {
        name: msg.name, round: msg.round || 1, kicker: info.kicker || 'NOW ENTERING',
        logo: msg.logo || this.world.name, accent: msg.accent, line: info.line || line,
        tagline: info.tagline, kickerColour: info.kickerColour
      }, client.audio);
    }
    if (!played) {
      this.banner(esc(msg.name), msg.join ? esc(this.world.name) + ' &bull; round ' + (msg.round || 1)
        : 'Round ' + (msg.round || 1) + ' &bull; ' + esc(line), 'area', 3800);
      client.audio.play('alarm', { volume: 0.3 });
    }
    this.call('onArea', msg);
  };

  Arena.prototype.onPhase = function (msg) {
    this.phase = msg.phase;
    this.phaseLeft = msg.left || 0;
    this.phaseAt = performance.now() / 1000;
    if (msg.phase === 'active') {
      this.banner('GO!', esc(this.call('goLine') || ''), 'go', 1600);
      this.client.audio.play('alarm', { volume: 0.55 });
      this.flashScreen('rgba(255,255,255,0.35)', 300);
    }
    this.call('onPhase', msg);
  };

  // ------------------------------------------------------------ state
  Arena.prototype.onState = function (state) {
    this.state = state || {};
    if (state.aphase && state.aphase !== this.phase) {
      this.phase = state.aphase;
    }
    if (state.phase_left !== undefined) {
      this.phaseLeft = state.phase_left;
      this.phaseAt = performance.now() / 1000;
    }
    if (state.dyn) this.onDynamic(state.dyn);
    this.call('onState', state);
  };

  Arena.prototype.onSnapshot = function (msg) {
    this.call('onSnapshot', msg);
  };

  Arena.prototype.onMe = function (msg) {
    var was = this.me;
    this.me = msg;
    if (msg.out && !was.out) {
      this.client.hud.setRespawn(null);
      this.lockOnSomeone();
    }
    this.call('onMe', msg, was);
  };

  Arena.prototype.onLoad = function (msg) {
    var client = this.client;
    if (msg.you || msg.id === client.myId) {
      var hotbar = msg.hotbar ? clone(msg.hotbar) : clone(this.ownHotbar);
      client.avatar.hotbar = hotbar;
      var slot = msg.slot || 0;
      client.slot = slot;
      client.stowed = !hotbar[slot];
      for (var i = 0; i < 5; i++) {
        var stats = hotbar[i] && hotbar[i].data && hotbar[i].data.stats;
        client.ammo[i] = stats && stats.mag ? stats.mag : 0;
        client.reserve[i] = stats && stats.reserve ? stats.reserve : 0;
      }
      client.hud.buildHotbar(hotbar, slot);
      client.hud.setSlot(client.stowed ? -1 : slot);
      client.updateAmmoHud();
      if (client.scoped) { client.scoped = false; client.hud.setScope(false); }
      this.call('onLoadout', hotbar);
      return;
    }
    var player = client.players[msg.id];
    if (!player) { this.pendingLoads[msg.id] = msg; return; }
    if (!player._ownHotbar) player._ownHotbar = clone((player.avatar || {}).hotbar || []);
    var avatar = {};
    for (var k in player.avatar) avatar[k] = player.avatar[k];
    avatar.hotbar = msg.hotbar ? clone(msg.hotbar) : player._ownHotbar;
    player.avatar = avatar;
  };

  // --------------------------------------------------------- dynamics
  Arena.prototype.onDynamic = function (changes) {
    var changed = false;
    for (var key in changes) {
      if (!(key in this.dynamic)) continue;
      if (this.dynOn[key] !== !!changes[key]) { this.dynOn[key] = !!changes[key]; changed = true; }
    }
    if (changed) {
      this.syncDynamic();
      this.call('onDynamic', changes);
    }
  };

  Arena.prototype.syncDynamic = function () {
    var boxes = [];
    for (var key in this.dynamic) {
      if (!this.dynOn[key]) continue;
      var list = this.dynamic[key].boxes || [];
      for (var i = 0; i < list.length; i++) boxes.push(list[i]);
    }
    if (this.client.physics && this.client.physics.setDynamic) {
      this.client.physics.setDynamic(boxes);
    }
  };

  Arena.prototype.drawDynamic = function (renderer) {
    for (var key in this.dynamic) {
      if (!this.dynOn[key]) continue;
      var parts = this.dynamic[key].parts || [];
      for (var i = 0; i < parts.length; i++) renderer.push(parts[i]);
    }
  };

  // -------------------------------------------------------------- end
  Arena.prototype.onEnd = function (msg) {
    var client = this.client;
    var card = this.endNode;
    if (!card) return;
    this.phase = 'intermission';
    var cols = msg.columns || [['score', 'Score']];
    var myId = client.myId;
    var rows = (msg.rows || []).map(function (r, i) {
      var team = r.team === 'red' || r.team === 'blue' ? r.team : '';
      return '<tr class="' + (r.id === myId ? 'me ' : '') + team + '"><td>' + (i + 1) +
        '</td><td class="n">' + esc(r.name) + (r.tag ? ' <span class="tag">' + esc(r.tag) +
        '</span>' : '') + '</td>' + cols.map(function (c) {
          var v = r[c[0]];
          return '<td>' + (typeof v === 'number' ? v.toLocaleString() : esc(v == null ? '' : v)) +
            '</td>';
        }).join('') + '</tr>';
    }).join('');
    var won = msg.winner && (msg.winner === client.myTeam || msg.winner === BH.user.name);
    var Intro = global.AreaIntro;
    var next = msg.shuffle
      ? '<div id="ar-reel"></div><div class="ar-next ar-after" id="ar-after">Next stop: <b>' +
        esc(msg.next) + '</b> in <span id="ar-count">' + Math.round(msg['in'] || 15) + '</span>s</div>'
      : '<div class="ar-next">Round ' + ((msg.area_round || 1) + 1) + ' of ' + (msg.rounds || 1) +
        ' at <b>' + esc(msg.area) + '</b> in <span id="ar-count">' +
        Math.round(msg['in'] || 15) + '</span>s</div>';
    card.innerHTML =
      '<div class="ar-end-in' + (won ? ' won' : '') + '">' +
      '<div class="ar-end-k">' + esc(msg.logo || this.world.name) + ' &bull; ' + esc(msg.area) + '</div>' +
      '<h2>' + esc((msg.headline || 'Round over')).toUpperCase() + '</h2>' +
      (msg.reason_text ? '<div class="ar-end-s">' + esc(msg.reason_text) + '</div>' : '') +
      ((msg.awards || []).length ? '<div class="ar-awards">' + msg.awards.map(function (a) {
        return '<span>' + esc(a) + '</span>';
      }).join('') + '</div>' : '') +
      '<div class="ar-table"><table><thead><tr><th></th><th class="n">Player</th>' +
      cols.map(function (c) { return '<th>' + esc(c[1]) + '</th>'; }).join('') +
      '</tr></thead><tbody>' + rows + '</tbody></table></div>' + next + '</div>';
    card.classList.add('on');
    this.call('onEnd', msg, card);
    client.audio.play(won ? 'wavewin' : 'capture');
    if (this.reel) this.reel.stop();
    this.reel = null;
    if (msg.shuffle && Intro) {
      this.reel = Intro.reel(el('ar-reel'), msg.reel, msg.next_id, client.audio, 2600, function () {
        var after = el('ar-after');
        if (after) after.classList.add('on');
      });
    } else {
      var after = el('ar-after');
      if (after) after.classList.add('on');
    }
    var left = Math.round(msg['in'] || 15);
    clearInterval(this.endTimer);
    var self = this;
    this.endTimer = setInterval(function () {
      left -= 1;
      var node = el('ar-count');
      if (node) node.textContent = Math.max(0, left);
      if (left <= 0) clearInterval(self.endTimer);
    }, 1000);
  };

  Arena.prototype.hideEnd = function () {
    clearInterval(this.endTimer);
    if (this.reel) this.reel.stop();
    this.reel = null;
    if (this.endNode) this.endNode.classList.remove('on');
  };

  // -------------------------------------------------------- spectating
  Arena.prototype.isWatching = function () {
    return !!this.me.out;
  };

  Arena.prototype.watchable = function () {
    var players = this.client.players;
    var out = (this.state && this.state.out) || [];
    return Object.keys(players).map(function (id) { return players[id]; }).filter(function (p) {
      return p.alive && out.indexOf(p.id) < 0;
    }).sort(function (a, b) { return a.id - b.id; });
  };

  Arena.prototype.lockOnSomeone = function () {
    var list = this.watchable();
    if (!list.length) { this.watchId = 0; return; }
    if (!list.some(function (p) { return p.id === this.watchId; }, this)) {
      this.watchId = list[0].id;
    }
  };

  Arena.prototype.cycle = function (step) {
    var list = this.watchable();
    if (!list.length) { this.watchId = 0; return; }
    var index = 0;
    for (var i = 0; i < list.length; i++) if (list[i].id === this.watchId) index = i;
    index = (index + step + list.length) % list.length;
    this.watchId = list[index].id;
    this.client.audio.play('ui', { volume: 0.3 });
  };

  Arena.prototype.watched = function () {
    var p = this.client.players[this.watchId];
    if (!p || !p.alive) {
      this.lockOnSomeone();
      p = this.client.players[this.watchId];
    }
    return p && p.alive ? p : null;
  };

  Arena.prototype.camera = function () {
    var own = this.call('camera');
    if (own) return own;
    if (!this.isWatching()) return null;
    var target = this.watched();
    if (target) {
      var yaw = target.yaw || 0;
      var back = 15, up = 7.5;
      var eye = [target.pos[0] - Math.sin(yaw) * back, target.pos[1] + up,
                 target.pos[2] - Math.cos(yaw) * back];
      var physics = this.client.physics;
      if (physics) {
        var pivot = [target.pos[0], target.pos[1] + 5, target.pos[2]];
        var dir = [eye[0] - pivot[0], eye[1] - pivot[1], eye[2] - pivot[2]];
        var len = Math.hypot(dir[0], dir[1], dir[2]) || 1;
        dir = [dir[0] / len, dir[1] / len, dir[2] / len];
        var clear = physics.rayDistance(pivot, dir, len + 1) - 1.2;
        var d = Math.max(3, Math.min(len, clear));
        eye = [pivot[0] + dir[0] * d, pivot[1] + dir[1] * d, pivot[2] + dir[2] * d];
      }
      var dx = target.pos[0] - eye[0], dz = target.pos[2] - eye[2];
      var dy = target.pos[1] + 3.5 - eye[1];
      return { eye: eye, yaw: Math.atan2(dx, dz), pitch: Math.atan2(dy, Math.hypot(dx, dz)) };
    }
    var cams = this.markers.cameras || [];
    if (cams.length) {
      var cam = cams[Math.floor(this.time / 8) % cams.length];
      var tx = cam.t[0] - cam.p[0], ty = cam.t[1] - cam.p[1], tz = cam.t[2] - cam.p[2];
      return { eye: cam.p.slice(), yaw: Math.atan2(tx, tz), pitch: Math.atan2(ty, Math.hypot(tx, tz)) };
    }
    return null;
  };

  Arena.prototype.reportWatch = function () {
    var now = performance.now() / 1000;
    var id = this.isWatching() ? this.watchId : 0;
    if (id === this.watchSent && now - this.watchSentAt < 4) return;
    this.watchSent = id;
    this.watchSentAt = now;
    this.client.net.send({ t: 'act', k: 'watch', id: id });
  };

  // ---------------------------------------------------- input hooks
  Arena.prototype.useDown = function (repeat) {
    if (repeat) return;
    if (this.call('useDown', repeat)) return;
    this.useHeld = true;
    this.client.net.send({ t: 'act', k: 'use' });
  };

  Arena.prototype.useUp = function () {
    if (this.call('useUp')) return;
    if (!this.useHeld) return;
    this.useHeld = false;
    this.client.net.send({ t: 'act', k: 'unuse' });
  };

  Arena.prototype.send = function (kind, extra) {
    var msg = { t: 'act', k: kind };
    for (var key in (extra || {})) msg[key] = extra[key];
    this.client.net.send(msg);
  };

  Arena.prototype.canFire = function (stats) {
    if (this.me.out) return false;
    var own = this.call('canFire', stats);
    return own === undefined ? true : !!own;
  };

  Arena.prototype.isCustom = function (stats) {
    return !!this.call('isCustom', stats);
  };

  Arena.prototype.localFire = function (stats, origin, dir) {
    return !!this.call('localFire', stats, origin, dir);
  };

  Arena.prototype.moveScale = function () {
    var v = this.call('moveScale');
    return v === undefined ? 1 : v;
  };

  Arena.prototype.canJump = function () {
    var v = this.call('canJump');
    return v === undefined ? true : !!v;
  };

  Arena.prototype.rayHit = function (origin, dir, distance) {
    var v = this.call('rayHit', origin, dir, distance);
    return v === undefined ? distance : v;
  };

  Arena.prototype.avatarParts = function (player, parts, self) {
    var v = this.call('avatarParts', player, parts, !!self);
    return v || parts;
  };

  Arena.prototype.hidden = function (player) {
    return !!this.call('hidden', player);
  };

  Arena.prototype.nameTag = function (player) {
    return this.call('nameTag', player) || null;
  };

  Arena.prototype.forcesThird = function () {
    return !!this.call('thirdPerson');
  };

  Arena.prototype.reloadDown = function () {
    return !!this.call('reloadDown');
  };

  Arena.prototype.noPet = function (id) {
    return !!this.call('noPet', id);
  };

  Arena.prototype.disguised = function (player) {
    return !!this.call('disguised', player);
  };

  /* A shake of the view this frame -- [dx, dy, dz, dyaw] -- or null: an
     earthquake, a blast close by.  Only what is drawn moves; aim does not. */
  Arena.prototype.jolt = function () {
    return this.call('jolt') || null;
  };

  // ------------------------------------------------------- objective
  Arena.prototype.updateObjective = function (state) {
    var panel = el('objective');
    if (!panel) return;
    var info = this.call('hud', state) || {};
    var left = panel.querySelector('.ar-l'), right = panel.querySelector('.ar-r');
    var title = panel.querySelector('.ar-title'), timer = panel.querySelector('.ar-timer');
    var sub = panel.querySelector('.ar-sub'), bars = panel.querySelector('.ar-bars');
    function side(node, spec) {
      if (!node) return;
      if (!spec) { node.innerHTML = ''; node.style.display = 'none'; return; }
      node.style.display = '';
      node.innerHTML = '<b style="color:' + (spec.colour || '#fff') + '">' + esc(spec.value) +
        '</b>' + (spec.label ? '<i>' + esc(spec.label) + '</i>' : '');
    }
    side(left, info.left);
    side(right, info.right);
    if (title) title.textContent = info.title || state.area_name || '';
    if (timer) {
      var text = info.timer;
      if (text === undefined) {
        if (state.aphase === 'setup') text = 'STARTS IN ' + fmt(state.phase_left);
        else if (state.aphase === 'active') text = state.time_left ? fmt(state.time_left) : '';
        else text = 'ROUND OVER';
      }
      timer.textContent = text;
    }
    if (sub) sub.innerHTML = info.sub || '';
    if (bars) {
      bars.innerHTML = (info.bars || []).map(function (b) {
        var marks = (b.marks || []).map(function (m) {
          return '<em style="left:' + (m * 100).toFixed(1) + '%"></em>';
        }).join('');
        return '<div class="ar-bar' + (b.cls ? ' ' + b.cls : '') + '"><span>' + esc(b.label || '') +
          '</span><div class="track">' + marks + '<i style="width:' +
          (Math.max(0, Math.min(1, b.value || 0)) * 100).toFixed(1) + '%;background:' +
          (b.colour || '#ffd27a') + '"></i></div><span class="v">' + esc(b.text || '') + '</span></div>';
      }).join('');
    }
    panel.classList.toggle('urgent', !!info.urgent);
  };

  Arena.prototype.renderScoreboard = function (rows) {
    var board = el('sb-body');
    if (!board) return true;
    var head = document.querySelector('#scoreboard thead tr');
    var custom = this.call('scoreHead');
    if (head) {
      head.innerHTML = custom || '<th>Player</th><th>Team</th><th>Kills</th><th>Deaths</th><th>Score</th>';
    }
    var myId = this.client.myId;
    var self = this;
    board.innerHTML = (rows || []).map(function (row) {
      var team = row.team === 'red' || row.team === 'blue' ? row.team : '';
      var inner = self.call('scoreRow', row);
      if (inner === undefined) {
        inner = '<td>' + esc(self.teamName(row.team)) + (row.out ? ' (out)' : '') + '</td><td>' +
          row.kills + '</td><td>' + row.deaths + '</td><td>' + row.score + '</td>';
      }
      return '<tr class="' + team + (row.id === myId ? ' me' : '') + '">' +
        '<td class="who" data-username="' + esc(row.name) + '">' + esc(row.name) + '</td>' + inner + '</tr>';
    }).join('');
    var title = el('sb-title');
    if (title) {
      title.textContent = this.world.name + ' -- ' + (this.state.area_name || '') + ' -- instance #' +
        (this.state.instance || '?') + ' (' + (rows || []).length + ' players)';
    }
    return true;
  };

  Arena.prototype.teamName = function (team) {
    var names = this.world.team_names || {};
    return names[team] || (team === 'ffa' ? 'Free for all' : (team || '-'));
  };

  // ------------------------------------------------------------ frame
  Arena.prototype.update = function (dt) {
    this.time += dt;
    var client = this.client;
    // the countdown, out loud in its last seconds
    if (this.phase === 'setup') {
      var left = this.phaseLeft - (performance.now() / 1000 - (this.phaseAt || 0));
      var count = Math.ceil(left);
      if (count !== this.lastCount && count <= 3 && count >= 1 &&
          !(global.AreaIntro && global.AreaIntro.playing())) {
        this.banner(String(count), '', 'count', 900);
        client.audio.play('tick', { volume: 0.7 });
      }
      this.lastCount = count;
    }
    var prompt = this.call('prompt');
    if (prompt !== undefined) client.hud.setPrompt(prompt || '');
    if (this.isWatching()) {
      var target = this.watched();
      if (this.specNode) {
        this.specNode.className = 'on';
        this.specNode.innerHTML = target
          ? 'Watching <b>' + esc(target.name) + '</b> &bull; click to switch'
          : 'Out of this round &bull; the next one brings you back';
      }
    } else if (this.specNode && this.specNode.className) {
      this.specNode.className = '';
    }
    this.reportWatch();
  };

  Arena.prototype.draw = function (renderer, dt, time) {
    this.update(dt);
    this.drawDynamic(renderer);
    this.call('draw', renderer, dt, time);
  };

  global.Arena = Arena;
})(window);
