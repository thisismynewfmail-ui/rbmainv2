/* Blackout Relay -- the Game View half of the map rotation.

   Blackout Relay is capture the flag on a rotation of maps (the server side
   is app/game/worlds/blackout_relay.py, the maps app/game/maps/relay/).
   This plugin (client.js loads it as WorldPlugins.blackout_relay) does what
   moving between them needs on the client:

     * brnext  -- the round is over and the server has rolled the next map:
                  a reel of the rotation spins on the end card and lands on it;
     * brarea  -- the next round starts there: the whole static world is
                  swapped in place, the flags are cleared for the new ones,
                  and the map's own arrival sequence plays (game/area_intro.js);
     * weather -- what each map's sky is doing round the camera: rain, a dry
                  lightning storm, snow, embers, steam, drifting motes, petals,
                  never under a roof.

   Every map has an arrival scene, 'br_<map id>', registered at the bottom. */
(function (global) {
  'use strict';

  var GA = global.GameAudio;
  if (GA) {
    GA.register('br_thunder', function (vol) {
      this.noise({ freq: 380, freqEnd: 60, dur: 2.4, gain: 0.34 * vol });
      this.later(90, function () { this.noise({ freq: 900, freqEnd: 120, dur: 1.1, gain: 0.2 * vol }); });
      this.tone({ type: 'sawtooth', freq: 48, freqEnd: 30, dur: 1.8, gain: 0.05 * vol });
    });
    GA.register('br_rain', function (vol) {
      this.noise({ filter: 'highpass', freq: 2600, dur: 2.4, gain: 0.05 * vol });
      this.noise({ filter: 'bandpass', freq: 1200, dur: 2.2, gain: 0.03 * vol });
    });
    GA.register('br_arc', function (vol) {
      for (var i = 0; i < 5; i++) {
        this.later(i * 38, function () {
          this.noise({ filter: 'bandpass', freq: 5200, freqEnd: 2400, dur: 0.06, gain: 0.18 * vol });
        });
      }
      this.tone({ type: 'square', freq: 120, freqEnd: 60, dur: 0.3, gain: 0.04 * vol });
    });
    GA.register('br_hum', function (vol) {
      this.tone({ type: 'sawtooth', freq: 60, dur: 1.6, gain: 0.05 * vol });
      this.tone({ type: 'sine', freq: 120, dur: 1.6, gain: 0.04 * vol });
    });
    GA.register('br_clank', function (vol) {
      this.tone({ type: 'square', freq: 210, freqEnd: 90, dur: 0.16, gain: 0.12 * vol });
      this.noise({ filter: 'bandpass', freq: 2400, freqEnd: 800, dur: 0.12, gain: 0.14 * vol });
    });
    GA.register('br_wind', function (vol) {
      this.noise({ filter: 'bandpass', freq: 500, freqEnd: 900, dur: 2.6, gain: 0.08 * vol });
    });
    GA.register('br_chime', function (vol) {
      [880, 1320, 1760].forEach(function (f, i) {
        this.later(i * 120, function () { this.tone({ type: 'sine', freq: f, dur: 1.4, gain: 0.05 * vol }); });
      }, this);
    });
    GA.register('br_gong', function (vol) {
      this.tone({ type: 'sine', freq: 110, freqEnd: 104, dur: 3.2, gain: 0.16 * vol });
      this.tone({ type: 'sine', freq: 263, freqEnd: 258, dur: 2.4, gain: 0.06 * vol });
      this.noise({ filter: 'bandpass', freq: 900, dur: 0.2, gain: 0.08 * vol });
    });
    GA.register('br_tick', function (vol) {
      this.tone({ type: 'square', freq: 2400, dur: 0.03, gain: 0.05 * vol });
    });
    GA.register('br_steam', function (vol) {
      this.noise({ filter: 'highpass', freq: 3000, freqEnd: 1400, dur: 1.4, gain: 0.12 * vol });
    });
    GA.register('br_beep', function (vol) {
      this.tone({ type: 'sine', freq: 1046, dur: 0.12, gain: 0.07 * vol });
      this.later(160, function () { this.tone({ type: 'sine', freq: 1568, dur: 0.2, gain: 0.07 * vol }); });
    });
  }

  function rgb(hex) {
    var n = parseInt(hex.slice(1), 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
  }

  // ======================================================= the plugin
  global.WorldPlugins = global.WorldPlugins || {};
  global.WorldPlugins.blackout_relay = function (client) {
    var current = { area: '', weather: '', accent: '#ffd27a' };
    var drops = [];
    var roofs = { at: -10, eye: [0, -1e9, 0], cells: {} };
    var flash = { at: -10, next: 4 + Math.random() * 6, power: 0 };
    var reel = null;
    var bannerNode = null;
    var clock = 0;

    // ------------------------------------------------- living scenery
    // the map's rigs (static/js/game/rigs.js; the kinds are registered in
    // blackout_relay_rigs.js), and what they are told about the game
    var rigs = [];
    var rigCtx = {
      critters: [],
      players: function () {
        var out = [];
        if (client.myId && client.local && client.local.alive !== false) {
          out.push({ id: client.myId, pos: client.local.pos, team: client.myTeam, me: true });
        }
        Object.keys(client.players || {}).forEach(function (id) {
          var p = client.players[id];
          if (p && p.alive && p.pos) out.push({ id: p.id, pos: p.pos, team: p.team });
        });
        return out;
      },
      flagSpots: function () {
        var flags = (client.extras && client.extras.flags) || {};
        return Object.keys(flags).map(function (team) {
          var f = flags[team] || {};
          var pos = f.p;
          if (f.state === 'carried') {
            var who = f.carrier === client.myId ? client.local : (client.players || {})[f.carrier];
            pos = who && who.pos ? who.pos : pos;
          }
          return { team: team, state: f.state || 'home', pos: pos };
        });
      },
      viewer: function () {
        var cam = client.cameraPosition ? client.cameraPosition() : null;
        var at = cam && cam.eye ? cam.eye : client.local.pos;
        var yaw = client.local.yaw || 0, pitch = client.local.pitch || 0, cp = Math.cos(pitch);
        return { eye: at, dir: [Math.sin(yaw) * cp, Math.sin(pitch), Math.cos(yaw) * cp] };
      },
      round: function () {
        var st = client.state || {};
        var mk = (client.map && client.map.markers) || {};
        return { time_left: st.time_left, length: mk.round_seconds || 900,
                 sudden: !!st.sudden_death, overtime: !!st.overtime };
      },
      sound: function (name, at, volume) {
        if (!client.audio || !at) return;
        client.audio.play(name, { volume: (volume || 1) * client.volumeAt(at) });
      }
    };

    function buildRigs(map) {
      rigCtx.critters = [];
      rigs = global.Rigs ? global.Rigs.build(map, rigCtx) : [];
    }

    function el(id) { return document.getElementById(id); }
    function esc(text) {
      return String(text == null ? '' : text).replace(/[&<>"]/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
      });
    }

    function banner(title, sub, ms) {
      if (!bannerNode) {
        var host = document.querySelector('#game-root .hud') || document.body;
        bannerNode = document.createElement('div');
        bannerNode.id = 'ar-banner';
        host.appendChild(bannerNode);
      }
      var node = bannerNode;
      node.className = 'on area';
      node.innerHTML = '<b>' + title + '</b>' + (sub ? '<span>' + sub + '</span>' : '');
      clearTimeout(node._t);
      node._t = setTimeout(function () { node.className = ''; }, ms || 3600);
    }

    function setMap(map) {
      var markers = (map && map.markers) || {};
      var extra = markers.extra || {};
      current.area = markers.area || '';
      current.weather = extra.weather || '';
      current.accent = extra.accent || '#ffd27a';
      drops.length = 0;
      document.documentElement.style.setProperty('--ar-accent', current.accent);
      buildRigs(map);
    }

    function swap(map) {
      client.map = map;
      client.physics = new Physics(map, client.constants);
      client.renderer.setSky(map.sky);
      client.renderer.setAmbient(map.ambient);
      if (global.Textures && Textures.dropSigns) Textures.dropSigns();
      client.staticParts = map.parts;
      if (client.extras) client.extras.setFlags({});
      client.rebuildStatic();
      setMap(map);
    }

    function onArea(msg) {
      if (reel) { reel.stop(); reel = null; }
      if (msg.map) swap(msg.map);
      var line = 'FIRST TO ' + (msg.target || 3) + ' CAPTURES  ·  ' + (msg.minutes || 15) + ' MINUTES';
      var Intro = global.AreaIntro;
      var scene = 'br_' + msg.area;
      if (msg.intro && Intro && Intro.has(scene) &&
          Intro.play(scene, { name: msg.name, round: msg.round || 1, kicker: 'NOW DEPLOYING TO',
                              logo: 'BLACKOUT RELAY', accent: msg.accent || current.accent,
                              line: line }, client.audio)) {
        return;
      }
      banner(esc(msg.name), esc(line.toLowerCase()), 4200);
      client.audio.play('alarm', { volume: 0.3 });
    }

    function onNext(msg) {
      var body = el('end-body');
      var Intro = global.AreaIntro;
      if (!body || !Intro) return;
      var holder = document.createElement('div');
      holder.className = 'br-next';
      body.appendChild(holder);
      var after = document.createElement('div');
      after.className = 'ar-next';
      after.style.opacity = '0';
      after.innerHTML = 'Next map: <b>' + esc(msg.name) + '</b> &mdash; first to ' +
        (msg.target || 3) + ', ' + (msg.minutes || 15) + ' minutes';
      body.appendChild(after);
      if (reel) reel.stop();
      reel = Intro.reel(holder, msg.reel || [], msg.next, client.audio, 1400, function () {
        after.style.opacity = '1';
      });
    }

    // ---------------------------------------------------------- weather
    function eye() {
      var cam = client.cameraPosition ? client.cameraPosition() : null;
      return cam ? cam.eye : client.local.pos;
    }

    function roofAt(x, z) {
      var cell = Math.round((x - roofs.eye[0]) / 8) + ',' + Math.round((z - roofs.eye[2]) / 8);
      var y = roofs.cells[cell];
      return y === undefined ? -1e9 : y;
    }

    function updateRoofs(at) {
      if (clock - roofs.at < 0.4 && Math.hypot(at[0] - roofs.eye[0], at[2] - roofs.eye[2]) < 4) return;
      roofs.at = clock;
      roofs.eye = at.slice();
      roofs.cells = {};
      var phys = client.physics;
      if (!phys) return;
      for (var gx = -5; gx <= 5; gx++) {
        for (var gz = -5; gz <= 5; gz++) {
          var x = at[0] + gx * 8, z = at[2] + gz * 8, top = at[1] + 60;
          roofs.cells[gx + ',' + gz] = top - phys.rayDistance([x, top, z], [0, -1, 0], 160);
        }
      }
    }

    var KINDS = {
      rain:   { n: 200, fall: 72, size: [0.07, 2.4, 0.07], colour: '#a8c8e8', a: 0.38 },
      storm:  { n: 60, fall: 9, size: [0.16, 0.16, 0.16], colour: '#e8e0d0', a: 0.6, drift: 6 },
      snow:   { n: 170, fall: 8, size: [0.34, 0.34, 0.34], colour: '#ffffff', a: 0.9, drift: 1.6 },
      embers: { n: 70, fall: -6, size: [0.22, 0.22, 0.22], colour: '#ffae4a', a: 0.95, glow: 1, drift: 2.4 },
      steam:  { n: 34, fall: -4, size: [2.6, 2.0, 2.6], colour: '#e8eef2', a: 0.16, drift: 1.2, sph: 1 },
      motes:  { n: 80, fall: 0.6, size: [0.18, 0.18, 0.18], colour: '#fff2b0', a: 0.85, glow: 1, drift: 2.0 },
      petals: { n: 90, fall: 5, size: [0.5, 0.06, 0.4], colour: '#ffb8d0', a: 0.95, drift: 3.4, spin: 1 },
      leaves: { n: 70, fall: 6, size: [0.6, 0.06, 0.5], colour: '#d88a3a', a: 0.95, drift: 4.0, spin: 1 },
      dust:   { n: 60, fall: 0.3, size: [0.14, 0.14, 0.14], colour: '#e8d8b0', a: 0.55, drift: 3.0 },
      sparks: { n: 50, fall: 1.0, size: [0.12, 0.12, 0.12], colour: '#9fe8ff', a: 0.9, glow: 1, drift: 1.4 },
      mist:   { n: 40, fall: 0.2, size: [9.0, 2.6, 9.0], colour: '#eef2f4', a: 0.1, drift: 2.2, sph: 1 }
    };

    function drawWeather(renderer, dt, time) {
      var kind = KINDS[current.weather];
      var target = kind ? kind.n : 0;
      while (drops.length < target) {
        drops.push({ o: [(Math.random() - 0.5) * 80, Math.random() * 46 - 14, (Math.random() - 0.5) * 80],
                     s: 0.75 + Math.random() * 0.5, p: Math.random() * 6.28 });
      }
      if (drops.length > target) drops.length = target;
      if (!drops.length) return;
      var at = eye();
      updateRoofs(at);
      var col = rgb(kind.colour);
      for (var i = 0; i < drops.length; i++) {
        var d = drops[i];
        d.o[1] -= kind.fall * d.s * dt;
        if (kind.drift) {
          d.o[0] += Math.sin(time * 0.9 + d.p) * kind.drift * dt;
          d.o[2] += Math.cos(time * 0.7 + d.p * 1.3) * kind.drift * dt;
        }
        if (d.o[1] < -16 || d.o[1] > 34 || Math.abs(d.o[0]) > 40 || Math.abs(d.o[2]) > 40) {
          d.o = [(Math.random() - 0.5) * 80, kind.fall > 0 ? 28 + Math.random() * 6 : -14 + Math.random() * 4,
                 (Math.random() - 0.5) * 80];
        }
        var x = at[0] + d.o[0], y = at[1] + d.o[1], z = at[2] + d.o[2];
        if (y < roofAt(x, z)) continue;
        var spin = kind.spin ? time * 3 + d.p : 0;
        renderer.pushRaw(kind.sph ? 'sph' : 'box', x, y, z, spin * 0.7, spin, 0,
                         kind.size[0] * (kind.sph ? d.s : 1), kind.size[1] * (kind.sph ? d.s : 1),
                         kind.size[2] * (kind.sph ? d.s : 1), col,
                         kind.a * (kind.glow ? 0.6 + 0.4 * Math.sin(time * 4 + d.p) : 1), 0,
                         kind.glow ? 2 : 0, 0, null);
      }
      if (current.weather === 'rain' && Math.random() < dt * 0.5) client.audio.play('br_rain', { volume: 0.5 });
    }

    function drawFlash(renderer, dt) {
      // a dry storm: the sky lights up white now and then, and the thunder
      // follows a moment later
      if (current.weather !== 'storm' && current.weather !== 'rain') return;
      flash.next -= dt;
      if (flash.next <= 0) {
        flash.next = (current.weather === 'storm' ? 5 : 14) + Math.random() * 9;
        flash.at = clock;
        flash.power = 0.6 + Math.random() * 0.4;
        var delay = 400 + Math.random() * 1200;
        setTimeout(function () { client.audio.play('br_thunder', { volume: 0.5 * flash.power }); }, delay);
      }
      var k = clock - flash.at;
      var lit = k < 0.08 ? 1 : (k < 0.16 ? 0.2 : (k < 0.26 ? 0.8 : Math.max(0, 0.8 - (k - 0.26) * 3)));
      if (lit <= 0.01) return;
      var at = eye();
      renderer.pushRaw('sph', at[0], at[1], at[2], 0, 0, 0, 900, 900, 900, [0.9, 0.92, 1.0],
                       Math.min(0.35, 0.3 * lit * flash.power), 0, 2, 0, null);
    }

    return {
      bind: function (net) {
        net.on('brarea', onArea);
        net.on('brnext', onNext);
        net.on('round_start', function () { if (reel) { reel.stop(); reel = null; } });
        net.on('evt', function (msg) {
          if (global.Rigs && msg && msg.k) global.Rigs.notify(rigs, msg.k, msg, rigCtx);
        });
      },
      notify: function (kind, msg) {
        if (global.Rigs) global.Rigs.notify(rigs, kind, msg, rigCtx);
      },
      onMap: function (map, first) {
        setMap(map);
        if (first && map && map.name) {
          setTimeout(function () {
            banner(esc(map.name), 'Blackout Relay &bull; first to ' +
                   (((map.markers || {}).captures_to_win) || 3) + ' captures', 4200);
          }, 900);
        }
      },
      draw: function (renderer, dt, time) {
        clock += dt;
        if (rigs.length && global.Rigs) {
          global.Rigs.draw(rigs, renderer, dt, eye(), rigCtx, (client.map && client.map.fog) || 900);
        }
        drawWeather(renderer, dt, time);
        drawFlash(renderer, dt);
      }
    };
  };

  // =================================================== arrival scenes
  var Intro = global.AreaIntro;
  if (!Intro) return;
  var K = Intro.kit;
  var VW = K.VW, VH = K.VH, TAU = K.TAU, HEAVY = K.HEAVY, FONT = K.FONT;
  var seg = K.seg, lerp = K.lerp, outCubic = K.outCubic, outBack = K.outBack, inOut = K.inOut;
  var dot = K.dot, additive = K.additive, roundRect = K.roundRect, fitSize = K.fitSize;
  var between = K.between, rgba = K.rgba, mix = K.mix, wobble = K.wobble, sputter = K.sputter;
  var buzz = K.buzz, spaced = K.spaced, clamp = K.clamp;

  /* Shared figures, every scene painted from the same blocky set. */
  function sky(ctx, stops, h) {
    var g = ctx.createLinearGradient(0, 0, 0, h || VH);
    stops.forEach(function (s) { g.addColorStop(s[0], s[1]); });
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, VW, h || VH);
  }

  /* A blocky player mid-stride, side on: the classic yellow, red and blue,
     carrying ``flag`` (a colour) over the shoulder if given. */
  function runner(ctx, x, y, s, t, flag, dir) {
    dir = dir || 1;
    var step = Math.sin(t * 11);
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s * dir, s);
    ctx.fillStyle = '#0d69ac';
    ctx.save(); ctx.translate(-4, -26); ctx.rotate(step * 0.6); ctx.fillRect(-4, 0, 8, 26); ctx.restore();
    ctx.save(); ctx.translate(4, -26); ctx.rotate(-step * 0.6); ctx.fillRect(-4, 0, 8, 26); ctx.restore();
    ctx.fillStyle = '#c4281c';
    ctx.fillRect(-11, -52, 22, 26);
    ctx.fillStyle = '#f5cd30';
    ctx.save(); ctx.translate(-12, -50); ctx.rotate(0.9 - step * 0.5); ctx.fillRect(-4, 0, 8, 22); ctx.restore();
    ctx.fillRect(-8, -68, 16, 16);
    ctx.fillStyle = '#1b1b1b';
    ctx.fillRect(2, -63, 3, 3);
    if (flag) {
      ctx.fillStyle = '#d8d8d8';
      ctx.save(); ctx.translate(10, -48); ctx.rotate(-0.5);
      ctx.fillRect(-1.5, -50, 3, 56);
      ctx.fillStyle = flag;
      var wave = Math.sin(t * 14) * 4;
      ctx.beginPath(); ctx.moveTo(1.5, -50); ctx.lineTo(-34, -46 + wave); ctx.lineTo(-30, -32 + wave);
      ctx.lineTo(1.5, -28); ctx.fill();
      ctx.restore();
    } else {
      ctx.fillStyle = '#f5cd30';
      ctx.save(); ctx.translate(12, -50); ctx.rotate(-0.9 + step * 0.5); ctx.fillRect(-4, 0, 8, 22); ctx.restore();
    }
    ctx.restore();
  }

  /* A team flag on a pole, rippling. */
  function pennant(ctx, x, y, h, colour, t, dir) {
    dir = dir || 1;
    ctx.fillStyle = '#d8dce0';
    ctx.fillRect(x - 2, y - h, 4, h);
    ctx.fillStyle = colour;
    ctx.beginPath();
    ctx.moveTo(x, y - h);
    for (var i = 0; i <= 8; i++) {
      var u = i / 8;
      ctx.lineTo(x + dir * u * h * 0.42, y - h + Math.sin(t * 6 + u * 5) * 5 * u);
    }
    for (i = 8; i >= 0; i--) {
      var v = i / 8;
      ctx.lineTo(x + dir * v * h * 0.42, y - h + h * 0.26 + Math.sin(t * 6 + v * 5 + 0.4) * 5 * v);
    }
    ctx.fill();
  }

  /* A lightning bolt from (x, y0) down to y1, jagged by ``r``'s numbers. */
  function bolt(ctx, x, y0, y1, jag, colour, width) {
    ctx.save();
    ctx.strokeStyle = colour;
    ctx.lineWidth = width;
    ctx.lineJoin = 'miter';
    ctx.beginPath();
    ctx.moveTo(x, y0);
    var n = jag.length;
    for (var i = 0; i < n; i++) ctx.lineTo(x + jag[i], y0 + (y1 - y0) * (i + 1) / n);
    ctx.stroke();
    ctx.restore();
  }

  /* Rain streaks over everything, blown a little. */
  function rainOver(ctx, list, t, colour, slant) {
    ctx.strokeStyle = colour;
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    for (var i = 0; i < list.length; i++) {
      var d = list[i];
      var y = (d.y + t * d.v) % (VH + 80) - 40;
      var x = (d.x + t * d.v * slant) % (VW + 80) - 40;
      ctx.moveTo(x, y);
      ctx.lineTo(x + d.l * slant, y + d.l);
    }
    ctx.stroke();
  }

  function makeRain(r, n) {
    var out = [];
    for (var i = 0; i < n; i++) out.push({ x: r() * VW, y: r() * VH, v: between(r, 900, 1500), l: between(r, 14, 30) });
    return out;
  }

  /* The map's name in neon tubes: each letter stutters on in turn, then
     hums, with the odd drop-out. */
  function neonTitle(ctx, t, name, x, y, max, colour, at, gap) {
    var size = fitSize(ctx, name, 'bold #px ' + HEAVY, 112, max, 0.08);
    ctx.font = 'bold ' + size + 'px ' + HEAVY;
    ctx.textBaseline = 'middle';
    var lay = K.layout(ctx, name, size * 0.08);
    var left = x - lay.width / 2;
    for (var i = 0; i < lay.chars.length; i++) {
      var c = lay.chars[i];
      var on = sputter(t, at + i * (gap || 0.07), i + 1) * (i % 4 === 2 ? buzz(t, i) : 1);
      ctx.fillStyle = rgba('#1a1a1a', 0.85);
      ctx.fillText(c.ch, left + c.x + 3, y + 4);
      ctx.fillStyle = on > 0.5 ? colour : mix(colour, '#202020', 0.75);
      ctx.fillText(c.ch, left + c.x, y);
      if (on > 0.5) {
        additive(ctx, function () { dot(ctx, colour, left + c.x + c.w / 2, y, size * 0.9, 0.22); });
      }
    }
    return size;
  }

  /* A plate with a stencilled name, bolted on: what an industrial map
     says its name with. */
  function stencilPlate(ctx, t, name, x, y, w, h, plate, ink, at) {
    var k = outBack(seg(t, at, at + 0.45), 1.4);
    if (k <= 0) return;
    ctx.save();
    ctx.translate(x, lerp(y - 260, y, k));
    ctx.rotate(wobble(t, at + 0.45, 0.03, 10, 3));
    ctx.fillStyle = plate;
    roundRect(ctx, -w / 2, -h / 2, w, h, 10);
    ctx.fill();
    ctx.fillStyle = 'rgba(0,0,0,0.25)';
    for (var i = 0; i < 6; i++) ctx.fillRect(-w / 2 + 18 + i * (w - 36) / 5 - 3, -h / 2 + 10, 6, 6);
    for (i = 0; i < 6; i++) ctx.fillRect(-w / 2 + 18 + i * (w - 36) / 5 - 3, h / 2 - 16, 6, 6);
    var size = fitSize(ctx, name, 'bold #px ' + HEAVY, 96, w - 80, 0.06);
    ctx.font = 'bold ' + size + 'px ' + HEAVY;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = ink;
    spaced(ctx, name, 0, 4, size * 0.06);
    ctx.restore();
  }

  // ------------------------------------------------- Ironvale Relay
  Intro.register('br_ironvale', {
    tagline: 'One relay. Two keeps. A long run home.',
    accent: '#ff9a5a',
    cues: [[0.3, 'br_wind', 0.5], [1.5, 'br_clank', 0.6], [1.8, 'br_clank', 0.6], [2.1, 'br_clank', 0.6],
           [2.6, 'slam', 0.4], [3.2, 'pistol', 0.25], [3.35, 'pistol', 0.25]],
    shakes: [[2.62, 6, 0.3]],
    tagY: 600, tagAt: 3.0,
    setup: function (r) {
      var d = { hills: [], trees: [], tracers: [] };
      for (var i = 0; i < 14; i++) d.hills.push({ x: i * 130 - 60, h: between(r, 60, 150), w: between(r, 160, 260) });
      for (i = 0; i < 40; i++) d.trees.push({ x: between(r, 0, VW), s: between(r, 0.6, 1.2), y: between(r, 600, 640) });
      for (i = 0; i < 7; i++) d.tracers.push({ at: between(r, 3.0, 5.4), y: between(r, 560, 640), dir: r() < 0.5 ? -1 : 1 });
      return d;
    },
    draw: function (ctx, t, d) {
      sky(ctx, [[0, '#1d3463'], [0.55, '#9b86a0'], [0.72, '#e0875a'], [1, '#e8a070']], 640);
      additive(ctx, function () { dot(ctx, '#ffb070', 360, 560, 420, 0.5, 180); });
      d.hills.forEach(function (h, i) {
        ctx.fillStyle = i % 2 ? '#2a3a44' : '#26343e';
        ctx.beginPath(); ctx.ellipse(h.x + h.w / 2, 600, h.w * 0.7, h.h, 0, Math.PI, TAU); ctx.fill();
      });
      ctx.fillStyle = '#2a4a32';
      ctx.fillRect(0, 600, VW, VH - 600);
      // the relay in the middle: a concrete block with its mast and beacon
      ctx.fillStyle = '#4a5058';
      ctx.fillRect(640, 440, 320, 170);
      ctx.fillStyle = '#3a4048';
      ctx.fillRect(560, 520, 80, 90);
      ctx.fillRect(960, 520, 80, 90);
      ctx.fillRect(792, 250, 16, 190);
      var beacon = Math.sin(t * 5) > 0.2 ? 1 : 0.2;
      ctx.fillStyle = beacon > 0.5 ? '#ff4a3a' : '#5a1a14';
      ctx.fillRect(788, 238, 24, 14);
      if (beacon > 0.5) additive(ctx, function () { dot(ctx, '#ff4a3a', 800, 245, 60, 0.7); });
      // the floodlights clank on, one after another
      [[600, 1.5], [800, 1.8], [1000, 2.1]].forEach(function (f, i) {
        var on = sputter(t, f[1], i + 3);
        ctx.fillStyle = '#2a2e34';
        ctx.fillRect(f[0] - 4, 380, 8, 60);
        ctx.fillStyle = on > 0.5 ? '#ffe2a8' : '#4a4a40';
        ctx.fillRect(f[0] - 18, 370, 36, 12);
        if (on > 0.5) {
          additive(ctx, function () {
            ctx.fillStyle = 'rgba(255,226,168,0.09)';
            ctx.beginPath(); ctx.moveTo(f[0] - 16, 382); ctx.lineTo(f[0] - 140, 640); ctx.lineTo(f[0] + 140, 640);
            ctx.lineTo(f[0] + 16, 382); ctx.fill();
            dot(ctx, '#ffe2a8', f[0], 376, 50, 0.8);
          });
        }
      });
      // the keeps at either end, their banners up
      ctx.fillStyle = '#3e444c';
      ctx.fillRect(40, 470, 220, 140);
      ctx.fillRect(1340, 470, 220, 140);
      pennant(ctx, 150, 470, 120, '#c4281c', t, 1);
      pennant(ctx, 1450, 470, 120, '#0d69ac', t, -1);
      d.trees.forEach(function (tr) {
        ctx.fillStyle = '#1c3424';
        ctx.beginPath(); ctx.moveTo(tr.x, tr.y - 50 * tr.s); ctx.lineTo(tr.x - 16 * tr.s, tr.y);
        ctx.lineTo(tr.x + 16 * tr.s, tr.y); ctx.fill();
      });
      // a carrier runs the blue flag home across the foreground, shots after
      var rx = lerp(-80, VW + 80, seg(t, 2.8, 6.2));
      runner(ctx, rx, 760, 2.2, t, '#0d69ac', 1);
      additive(ctx, function () {
        d.tracers.forEach(function (tr) {
          var k = (t - tr.at) / 0.12;
          if (k < 0 || k > 1) return;
          ctx.strokeStyle = 'rgba(255,236,160,' + (1 - k) + ')';
          ctx.lineWidth = 2;
          ctx.beginPath();
          var sx = tr.dir > 0 ? 0 : VW;
          ctx.moveTo(sx + tr.dir * k * 600, tr.y);
          ctx.lineTo(sx + tr.dir * (k * 600 + 160), tr.y - 10);
          ctx.stroke();
        });
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Ironvale Relay').toUpperCase();
      stencilPlate(ctx, t, name, 800, 250, 1040, 170, '#c9ccd2', '#2a2e34', 2.2);
      var k = seg(t, 2.6, 2.9);
      if (k > 0) {
        ctx.save();
        ctx.globalAlpha *= k;
        for (var i = 0; i < 16; i++) {
          ctx.fillStyle = i % 2 ? '#f2b01e' : '#1b1b1b';
          ctx.fillRect(280 + i * 65, 345, 65, 14);
        }
        ctx.restore();
      }
    }
  });

  // ------------------------------------------------- Substation Nine
  Intro.register('br_substation', {
    tagline: 'The whole city is dark. Except this.',
    accent: '#ffb050',
    cues: [[0.1, 'br_rain', 0.6], [0.9, 'br_arc', 0.6], [1.7, 'br_thunder', 0.7], [2.3, 'br_hum', 0.5],
           [2.4, 'buzz', 0.35], [3.4, 'br_arc', 0.5], [4.6, 'siren', 0.25]],
    shakes: [[1.72, 7, 0.35]],
    tagY: 640, tagAt: 3.4,
    setup: function (r) {
      var d = { towers: [], rain: makeRain(r, 260), jag: [], sparks: [] };
      var x = -30;
      while (x < VW + 40) {
        var w = between(r, 70, 150);
        var tw = { x: x, w: w, h: between(r, 220, 560), wins: [] };
        for (var k = 0; k < 40; k++) {
          tw.wins.push({ x: between(r, 8, w - 16), y: between(r, 20, tw.h - 20), lit: r() < 0.05 });
        }
        d.towers.push(tw);
        x += w + between(r, 6, 24);
      }
      for (var i = 0; i < 12; i++) d.jag.push(between(r, -40, 40));
      for (i = 0; i < 40; i++) d.sparks.push({ a: between(r, -3.0, -0.2), v: between(r, 120, 380), at: between(r, 0.8, 5.6) });
      return d;
    },
    draw: function (ctx, t, d) {
      var storm = seg(t, 1.6, 1.68) * (1 - seg(t, 1.9, 2.3));
      sky(ctx, [[0, mix('#070a14', '#c8d4f0', storm)], [1, mix('#2a3446', '#e8eeff', storm)]], 700);
      if (storm > 0) bolt(ctx, 1180, 0, 420, d.jag, rgba('#ffffff', storm), 5);
      // the skyline: every window dark, the odd candle
      d.towers.forEach(function (tw) {
        ctx.fillStyle = '#10141c';
        ctx.fillRect(tw.x, 700 - tw.h, tw.w, tw.h);
        tw.wins.forEach(function (wn, i) {
          if (!wn.lit) return;
          ctx.fillStyle = rgba('#ffcf7a', 0.5 + 0.3 * Math.sin(t * 2 + i));
          ctx.fillRect(tw.x + wn.x, 700 - tw.h + wn.y, 7, 9);
        });
      });
      ctx.fillStyle = '#1a1e26';
      ctx.fillRect(0, 700, VW, 200);
      // the substation: transformers, insulators, a gantry -- and the arcs
      ctx.fillStyle = '#2a332e';
      for (var i = 0; i < 4; i++) {
        var tx = 420 + i * 230;
        ctx.fillRect(tx, 600, 120, 100);
        ctx.fillStyle = '#222a26';
        for (var f = 0; f < 6; f++) ctx.fillRect(tx - 10, 610 + f * 14, 140, 6);
        ctx.fillStyle = '#c8d4dc';
        for (f = 0; f < 3; f++) ctx.fillRect(tx + 22 + f * 34, 570, 10, 30);
        ctx.fillStyle = '#2a332e';
      }
      ctx.fillStyle = '#3a424a';
      ctx.fillRect(380, 520, 900, 10);
      ctx.fillRect(390, 520, 10, 180);
      ctx.fillRect(1260, 520, 10, 180);
      // arcing between the insulators, blue-white
      [[0.9, 520], [3.4, 980]].forEach(function (a) {
        var k = t - a[0];
        if (k < 0 || k > 0.5) return;
        additive(ctx, function () {
          for (var j = 0; j < 3; j++) {
            ctx.strokeStyle = rgba('#9fe8ff', 0.9 - k);
            ctx.lineWidth = 3;
            ctx.beginPath(); ctx.moveTo(a[1], 570);
            for (var s = 1; s <= 6; s++) ctx.lineTo(a[1] + s * 12, 570 - Math.sin(t * 90 + s * 3 + j) * 18);
            ctx.stroke();
          }
          dot(ctx, '#9fe8ff', a[1] + 36, 560, 140, 0.7 - k);
        });
        d.sparks.forEach(function (sp) {
          var age = t - a[0] - (sp.at % 0.3);
          if (age < 0 || age > 0.8) return;
          ctx.fillStyle = rgba('#fff2b0', 1 - age / 0.8);
          ctx.fillRect(a[1] + 36 + Math.cos(sp.a) * sp.v * age, 560 + Math.sin(sp.a) * sp.v * age + 300 * age * age, 3, 3);
        });
      });
      // the police car's lights wash the wet street
      var red = Math.sin(t * 10) > 0;
      additive(ctx, function () {
        dot(ctx, red ? '#ff3a2a' : '#3a7aff', 220, 740, 260, 0.35, 90);
      });
      ctx.fillStyle = '#d8dce4';
      ctx.fillRect(150, 720, 140, 34);
      ctx.fillStyle = red ? '#ff3a2a' : '#3a7aff';
      ctx.fillRect(196, 712, 48, 8);
      rainOver(ctx, d.rain, t, 'rgba(168,200,232,0.45)', 0.18);
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Substation Nine').toUpperCase();
      // the warning sign slides up first
      var k = outCubic(seg(t, 1.9, 2.3));
      if (k > 0) {
        ctx.save();
        ctx.translate(800, lerp(-120, 150, k));
        ctx.fillStyle = '#f2c21e';
        ctx.beginPath(); ctx.moveTo(0, -70); ctx.lineTo(80, 60); ctx.lineTo(-80, 60); ctx.closePath(); ctx.fill();
        ctx.strokeStyle = '#1b1b1b'; ctx.lineWidth = 8; ctx.stroke();
        ctx.fillStyle = '#1b1b1b';
        ctx.beginPath(); ctx.moveTo(8, -30); ctx.lineTo(-18, 14); ctx.lineTo(0, 14); ctx.lineTo(-8, 46);
        ctx.lineTo(20, 2); ctx.lineTo(2, 2); ctx.closePath(); ctx.fill();
        ctx.restore();
      }
      ctx.textAlign = 'left';
      neonTitle(ctx, t, name, 800, 330, 1200, '#ffb050', 2.4, 0.06);
      ctx.font = 'bold 18px ' + FONT;
      ctx.textAlign = 'center';
      ctx.fillStyle = rgba('#ff4a3a', seg(t, 3.0, 3.3) * (0.6 + 0.4 * Math.sin(t * 6)));
      ctx.fillText('DANGER  ·  HIGH VOLTAGE  ·  KEEP OUT', 800, 410);
    }
  });


  // ------------------------------------------------- Thimble Acre
  /* A toy brick: studs on top, a colour, a letter on its face. */
  function brick(ctx, x, y, w, h, colour, letter, size) {
    ctx.fillStyle = mix(colour, '#000000', 0.25);
    ctx.fillRect(x + 4, y + 6, w, h);
    ctx.fillStyle = colour;
    ctx.fillRect(x, y, w, h);
    for (var i = 0; i < 2; i++) {
      ctx.fillStyle = mix(colour, '#ffffff', 0.18);
      ctx.fillRect(x + w * (0.18 + i * 0.44), y - h * 0.14, w * 0.22, h * 0.16);
    }
    if (letter) {
      ctx.font = 'bold ' + size + 'px ' + HEAVY;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = 'rgba(0,0,0,0.25)';
      ctx.fillText(letter, x + w / 2 + 3, y + h / 2 + 4);
      ctx.fillStyle = '#ffffff';
      ctx.fillText(letter, x + w / 2, y + h / 2);
    }
  }

  Intro.register('br_thimble', {
    tagline: 'The lawn is a battlefield. You are a toy.',
    accent: '#ffb84a',
    cues: [[0.3, 'br_chime', 0.35], [1.2, 'crow', 0.25], [2.0, 'land', 0.4], [2.15, 'land', 0.4],
           [2.3, 'land', 0.4], [2.45, 'land', 0.4], [2.6, 'land', 0.4], [3.4, 'br_chime', 0.3]],
    tagY: 640, tagAt: 3.5,
    setup: function (r) {
      var d = { blades: [], motes: [], seeds: [] };
      for (var i = 0; i < 46; i++) {
        d.blades.push({ x: between(r, -40, VW + 40), h: between(r, 180, 460), w: between(r, 18, 40),
                        lean: between(r, -0.12, 0.12), ph: r() * 6, shade: r() });
      }
      for (i = 0; i < 70; i++) d.motes.push({ x: r() * VW, y: r() * VH, s: between(r, 1.5, 4), ph: r() * 6 });
      return d;
    },
    draw: function (ctx, t, d) {
      sky(ctx, [[0, '#5a8ad8'], [0.55, '#ffc890'], [1, '#ffe0a8']], 620);
      additive(ctx, function () { dot(ctx, '#fff0b0', 1240, 520, 460, 0.6, 260); });
      // the fence, and the cat rising over it to watch
      ctx.fillStyle = '#7a5a34';
      ctx.fillRect(0, 300, VW, 330);
      for (var k = 0; k < 22; k++) {
        ctx.fillStyle = k % 2 ? '#8a6a3e' : '#7a5a34';
        ctx.fillRect(k * 74, 280 + (k % 3) * 6, 70, 350);
      }
      var cat = outCubic(seg(t, 0.8, 1.8));
      var cy = lerp(420, 250, cat);
      ctx.save();
      ctx.beginPath(); ctx.rect(0, 0, VW, 290); ctx.clip();
      ctx.fillStyle = '#e8a04a';
      ctx.beginPath(); ctx.ellipse(420, cy, 120, 96, 0, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.moveTo(330, cy - 50); ctx.lineTo(352, cy - 150); ctx.lineTo(400, cy - 80); ctx.fill();
      ctx.beginPath(); ctx.moveTo(510, cy - 50); ctx.lineTo(488, cy - 150); ctx.lineTo(440, cy - 80); ctx.fill();
      var blink = (t > 2.6 && t < 2.75) ? 0.1 : 1;
      ctx.fillStyle = '#f2f2d8';
      ctx.beginPath(); ctx.ellipse(380, cy - 10, 20, 24 * blink, 0, 0, TAU); ctx.ellipse(460, cy - 10, 20, 24 * blink, 0, 0, TAU); ctx.fill();
      ctx.fillStyle = '#1b1b1b';
      ctx.beginPath(); ctx.ellipse(380 + Math.sin(t) * 5, cy - 10, 6, 18 * blink, 0, 0, TAU);
      ctx.ellipse(460 + Math.sin(t) * 5, cy - 10, 6, 18 * blink, 0, 0, TAU); ctx.fill();
      ctx.restore();
      ctx.fillStyle = '#e8a04a';
      ctx.beginPath(); ctx.ellipse(330, 296, 50, 22, 0, 0, TAU); ctx.ellipse(510, 296, 50, 22, 0, 0, TAU); ctx.fill();
      // the lawn and the upturned pot on it
      ctx.fillStyle = '#5aa03a';
      ctx.fillRect(0, 620, VW, VH - 620);
      ctx.fillStyle = '#c8643c';
      ctx.beginPath(); ctx.moveTo(1000, 640); ctx.lineTo(1040, 470); ctx.lineTo(1240, 470); ctx.lineTo(1280, 640); ctx.fill();
      ctx.fillStyle = '#a84e2c';
      ctx.fillRect(990, 610, 300, 34);
      ctx.fillRect(1120, 470, 40, 10);
      // grass blades in front, swaying
      d.blades.forEach(function (bl) {
        var sway = Math.sin(t * 1.6 + bl.ph) * 0.05 + bl.lean;
        ctx.save();
        ctx.translate(bl.x, VH + 10);
        ctx.rotate(sway);
        ctx.fillStyle = mix('#3a7a24', '#7ac84a', bl.shade);
        ctx.beginPath(); ctx.moveTo(-bl.w / 2, 0); ctx.lineTo(0, -bl.h); ctx.lineTo(bl.w / 2, 0); ctx.fill();
        ctx.restore();
      });
      // pollen in the low sun
      additive(ctx, function () {
        d.motes.forEach(function (m) {
          dot(ctx, '#fff2b0', (m.x + Math.sin(t + m.ph) * 20) % VW, (m.y - t * 14 + VH) % VH, m.s * 3, 0.5);
        });
      });
      // a ladybird crosses the shot
      var lx = lerp(-60, VW + 60, seg(t, 3.0, 6.4)), ly = 380 + Math.sin(t * 3) * 40;
      ctx.fillStyle = '#d8221a';
      ctx.beginPath(); ctx.arc(lx, ly, 16, 0, TAU); ctx.fill();
      ctx.fillStyle = '#1b1b1b';
      ctx.beginPath(); ctx.arc(lx + 14, ly, 7, 0, TAU); ctx.fill();
      ctx.fillRect(lx - 1, ly - 16, 2, 32);
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Thimble Acre').toUpperCase();
      var colours = ['#c4281c', '#0d69ac', '#f2c21e', '#3a9a3a'];
      var w = Math.min(96, 1320 / name.length - 10), gap = 10, total = name.length * (w + gap) - gap;
      var x0 = 800 - total / 2;
      for (var i = 0; i < name.length; i++) {
        var at = 2.0 + i * 0.15 * (5 / Math.max(5, name.length));
        var k = seg(t, at, at + 0.35);
        if (k <= 0) continue;
        var bounce = k < 1 ? lerp(-500, 0, outBack(k, 1.8)) : 0;
        if (name.charAt(i) === ' ') continue;
        brick(ctx, x0 + i * (w + gap), 230 + bounce, w, 100, colours[i % 4], name.charAt(i), 64);
      }
    }
  });

  // ------------------------------------------------- The Orrery
  function gear(ctx, x, y, r, teeth, angle, colour) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(angle);
    ctx.fillStyle = colour;
    ctx.beginPath();
    for (var i = 0; i < teeth * 2; i++) {
      var a = i * Math.PI / teeth;
      var rr = i % 2 ? r : r * 1.16;
      ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr);
    }
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.beginPath(); ctx.arc(0, 0, r * 0.3, 0, TAU); ctx.fill();
    ctx.restore();
  }

  Intro.register('br_orrery', {
    tagline: 'The planets keep time. So should you.',
    accent: '#e8b860',
    cues: [[0.2, 'br_tick', 0.6], [0.7, 'br_tick', 0.6], [1.2, 'br_tick', 0.6], [1.7, 'br_tick', 0.6],
           [2.2, 'br_clank', 0.5], [2.5, 'br_chime', 0.6], [3.6, 'br_tick', 0.5], [4.1, 'br_tick', 0.5]],
    tagY: 650, tagAt: 3.2,
    setup: function (r) { return { stars: K.makeStars(r, 220, 0, 700) }; },
    draw: function (ctx, t, d) {
      sky(ctx, [[0, '#1a1640'], [0.6, '#5a3a6a'], [1, '#e08a7a']]);
      K.stars(ctx, d.stars, t, 0.8);
      // gears turning in the corners
      gear(ctx, 120, 120, 90, 14, t * 0.6, '#6a4a1a');
      gear(ctx, 250, 60, 50, 9, -t * 1.1, '#8a6a28');
      gear(ctx, 1480, 800, 110, 16, -t * 0.5, '#6a4a1a');
      gear(ctx, 1330, 860, 60, 10, t * 0.9, '#8a6a28');
      // the orrery: tilted orbits round a burning sun
      var cx = 800, cy = 430;
      additive(ctx, function () { dot(ctx, '#ffb84a', cx, cy, 260, 0.7); });
      ctx.fillStyle = '#ffc860';
      ctx.beginPath(); ctx.arc(cx, cy, 58, 0, TAU); ctx.fill();
      [[150, 0.9, '#4a7ad8', 18], [240, 0.55, '#d86a3a', 24], [330, 0.32, '#c8b878', 30]].forEach(function (o, i) {
        ctx.strokeStyle = 'rgba(232,184,96,0.6)';
        ctx.lineWidth = 3;
        ctx.beginPath(); ctx.ellipse(cx, cy, o[0], o[0] * 0.32, -0.2, 0, TAU); ctx.stroke();
        var a = t * o[1] + i * 2.1;
        var px = cx + Math.cos(a) * o[0] * Math.cos(-0.2) - Math.sin(a) * o[0] * 0.32 * Math.sin(-0.2);
        var py = cy + Math.cos(a) * o[0] * Math.sin(-0.2) + Math.sin(a) * o[0] * 0.32 * Math.cos(-0.2);
        ctx.strokeStyle = '#8a6a28'; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(px, py); ctx.stroke();
        ctx.fillStyle = o[2];
        ctx.beginPath(); ctx.arc(px, py, o[3], 0, TAU); ctx.fill();
        if (i === 2) {
          ctx.strokeStyle = '#e8d8a8'; ctx.lineWidth = 3;
          ctx.beginPath(); ctx.ellipse(px, py, o[3] * 1.8, o[3] * 0.5, 0.3, 0, TAU); ctx.stroke();
        }
      });
      // the garden's silhouette along the bottom: hedges, a glasshouse, lamps
      ctx.fillStyle = '#16241c';
      ctx.fillRect(0, 760, VW, 140);
      for (var k = 0; k < 9; k++) {
        ctx.beginPath(); ctx.arc(80 + k * 190, 760, 46, Math.PI, TAU); ctx.fill();
      }
      ctx.strokeStyle = '#2a4a3a'; ctx.lineWidth = 3;
      ctx.strokeRect(1060, 650, 300, 110);
      for (k = 0; k < 6; k++) { ctx.beginPath(); ctx.moveTo(1060 + k * 60, 650); ctx.lineTo(1060 + k * 60, 760); ctx.stroke(); }
      [300, 520, 700].forEach(function (lx, i) {
        ctx.fillStyle = '#16241c';
        ctx.fillRect(lx - 3, 680, 6, 80);
        var on = sputter(t, 0.6 + i * 0.3, i);
        if (on > 0.5) additive(ctx, function () { dot(ctx, '#ffd890', lx, 676, 40, 0.8); });
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'The Orrery').toUpperCase();
      var k = outBack(seg(t, 2.0, 2.5), 1.3);
      if (k <= 0) return;
      var swing = wobble(t, 2.5, 0.08, 5, 1.6);
      ctx.save();
      ctx.translate(800, lerp(-160, 150, k));
      ctx.rotate(swing);
      ctx.strokeStyle = '#8a6a28'; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(-300, -70); ctx.lineTo(-200, -170); ctx.moveTo(300, -70); ctx.lineTo(200, -170); ctx.stroke();
      var g = ctx.createLinearGradient(0, -70, 0, 70);
      g.addColorStop(0, '#f2d890'); g.addColorStop(0.5, '#c89a3a'); g.addColorStop(1, '#8a6a28');
      ctx.fillStyle = g;
      roundRect(ctx, -460, -70, 920, 140, 70);
      ctx.fill();
      ctx.strokeStyle = '#5a4018'; ctx.lineWidth = 5; ctx.stroke();
      var size = fitSize(ctx, name, 'bold #px Georgia, serif', 86, 800, 0.08);
      ctx.font = 'bold ' + size + 'px Georgia, serif';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillStyle = '#3a2a10';
      spaced(ctx, name, 0, 4, size * 0.08);
      ctx.restore();
    }
  });

  // ------------------------------------------------- Saltglass Flats
  Intro.register('br_saltglass', {
    tagline: 'Nothing grows here. Lightning does.',
    accent: '#9fe8ff',
    cues: [[0.4, 'br_wind', 0.5], [1.5, 'br_arc', 0.6], [1.9, 'br_thunder', 0.9], [2.8, 'br_hum', 0.5],
           [3.9, 'br_arc', 0.5], [4.4, 'br_thunder', 0.5]],
    shakes: [[1.92, 9, 0.4]],
    tagY: 660, tagAt: 3.4,
    setup: function (r) {
      var d = { jag: [], jag2: [], rods: [], plates: [], spires: [] };
      for (var i = 0; i < 12; i++) { d.jag.push(between(r, -50, 50)); d.jag2.push(between(r, -30, 30)); }
      for (i = 0; i < 7; i++) d.rods.push({ x: 120 + i * 230 + between(r, -30, 30), h: between(r, 120, 220) });
      for (i = 0; i < 26; i++) d.plates.push({ x: r() * VW, y: between(r, 610, 900), w: between(r, 60, 220) });
      for (i = 0; i < 10; i++) d.spires.push({ x: r() * VW, h: between(r, 30, 90), y: between(r, 640, 860) });
      return d;
    },
    draw: function (ctx, t, d) {
      var strike = seg(t, 1.88, 1.92) * (1 - seg(t, 2.0, 2.5));
      var strike2 = seg(t, 4.35, 4.4) * (1 - seg(t, 4.45, 4.8));
      var flash = Math.max(strike, strike2 * 0.6);
      sky(ctx, [[0, mix('#120e24', '#d8d0ff', flash)], [1, mix('#4a3a5a', '#ffffff', flash)]], 620);
      // the buttes on the horizon
      ctx.fillStyle = mix('#2a2234', '#8a8098', flash);
      for (var k = 0; k < 8; k++) ctx.fillRect(k * 220 - 30, 520 - (k % 3) * 30, 180, 100 + (k % 3) * 30);
      // the salt, lit from above
      ctx.fillStyle = mix('#cfc8bc', '#ffffff', flash);
      ctx.fillRect(0, 600, VW, VH - 600);
      d.plates.forEach(function (p) {
        ctx.strokeStyle = mix('#a8a294', '#e8e4dc', flash); ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p.x + p.w, p.y + 10); ctx.lineTo(p.x + p.w * 0.7, p.y + 30); ctx.stroke();
      });
      // the lightning rods, and the one that gets hit
      d.rods.forEach(function (rd, i) {
        ctx.fillStyle = '#2a2e36';
        ctx.fillRect(rd.x - 4, 620 - rd.h, 8, rd.h);
        var glow = i === 3 ? Math.max(strike, seg(t, 1.9, 2.0) * (1 - seg(t, 2.6, 4))) : 0;
        additive(ctx, function () { dot(ctx, '#9fe8ff', rd.x, 620 - rd.h, 18 + glow * 90, 0.5 + glow * 0.5); });
      });
      if (strike > 0) {
        bolt(ctx, d.rods[3].x, 0, 620 - d.rods[3].h, d.jag, rgba('#ffffff', strike), 7);
        additive(ctx, function () { bolt(ctx, d.rods[3].x, 0, 620 - d.rods[3].h, d.jag, rgba('#9fe8ff', strike), 22); });
      }
      if (strike2 > 0) bolt(ctx, 1450, 0, 560, d.jag2, rgba('#ffffff', strike2), 4);
      // fulgurite spires glowing where the salt melted
      d.spires.forEach(function (s, i) {
        ctx.fillStyle = rgba('#7ad8e8', 0.85);
        ctx.fillRect(s.x, s.y - s.h, 14, s.h);
        ctx.fillRect(s.x + 16, s.y - s.h * 0.6, 10, s.h * 0.6);
        additive(ctx, function () { dot(ctx, '#9fe8ff', s.x + 8, s.y - s.h, 30, 0.3 + 0.2 * Math.sin(t * 3 + i)); });
      });
      // the two coils on the hall, arcing to each other
      ctx.fillStyle = '#3a3e46';
      ctx.fillRect(560, 520, 480, 100);
      [680, 920].forEach(function (cx) {
        ctx.fillStyle = '#c87a3a'; ctx.fillRect(cx - 14, 400, 28, 120);
        ctx.fillStyle = '#c8ccd2'; ctx.beginPath(); ctx.ellipse(cx, 396, 44, 14, 0, 0, TAU); ctx.fill();
      });
      if (Math.sin(t * 7) > 0.2 || (t > 3.8 && t < 4.2)) {
        additive(ctx, function () {
          ctx.strokeStyle = 'rgba(191,232,255,0.9)'; ctx.lineWidth = 3;
          ctx.beginPath(); ctx.moveTo(724, 392);
          for (var s = 1; s < 10; s++) ctx.lineTo(724 + s * 17.6, 392 + Math.sin(t * 60 + s * 2) * 14);
          ctx.lineTo(876, 392); ctx.stroke();
        });
      }
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Saltglass Flats').toUpperCase();
      // the name melts into the salt like glass: white hot, cooling to cyan
      var k = seg(t, 1.95, 2.4);
      if (k <= 0) return;
      var cool = seg(t, 2.2, 4.2);
      var size = fitSize(ctx, name, 'bold #px ' + HEAVY, 110, 1200, 0.06);
      ctx.font = 'bold ' + size + 'px ' + HEAVY;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.save();
      ctx.globalAlpha *= k;
      ctx.fillStyle = 'rgba(20,30,40,0.6)';
      spaced(ctx, name, 806, 236, size * 0.06);
      ctx.fillStyle = mix('#ffffff', '#7ad8e8', cool);
      spaced(ctx, name, 800, 230, size * 0.06);
      additive(ctx, function () { dot(ctx, '#bfe8ff', 800, 230, 520, 0.35 * (1 - cool * 0.6), 80); });
      ctx.restore();
    }
  });

  // ------------------------------------------------- Drawdown
  Intro.register('br_drawdown', {
    tagline: 'Forty years under water. Lower Ashby is back.',
    accent: '#d8c89a',
    cues: [[0.2, 'splash', 0.3], [0.9, 'splash', 0.2], [1.8, 'bell', 0.35], [2.6, 'br_clank', 0.4],
           [3.3, 'splash', 0.2], [4.4, 'bell', 0.25]],
    tagY: 660, tagAt: 3.3,
    setup: function (r) {
      var d = { houses: [], drips: [] };
      for (var i = 0; i < 9; i++) {
        d.houses.push({ x: 140 + i * 150 + between(r, -20, 20), w: between(r, 80, 120), h: between(r, 70, 120),
                        roof: r() < 0.5 });
      }
      for (i = 0; i < 40; i++) d.drips.push({ x: between(r, 100, 1500), at: between(r, 0.5, 5.5) });
      return d;
    },
    draw: function (ctx, t, d) {
      sky(ctx, [[0, '#7e868e'], [1, '#cfc8b8']], 700);
      // the hills and the dam
      ctx.fillStyle = '#5a6a4a';
      for (var k = 0; k < 7; k++) { ctx.beginPath(); ctx.ellipse(k * 260, 470, 220, 90, 0, Math.PI, TAU); ctx.fill(); }
      ctx.fillStyle = '#b8b4a8';
      ctx.fillRect(0, 420, VW, 60);
      // the lakebed, its bathtub rings, the village coming out of the water
      var level = lerp(400, 760, inOut(seg(t, 0.2, 3.4)));
      ctx.fillStyle = '#8a7a5a';
      ctx.fillRect(0, 480, VW, VH - 480);
      ['#6a7a6a', '#7a7a6a', '#8a7a6a'].forEach(function (c, i) {
        ctx.fillStyle = c; ctx.fillRect(0, 490 + i * 26, VW, 8);
      });
      // the valve tower in the middle
      ctx.fillStyle = '#c8c4b8';
      ctx.fillRect(760, 300, 80, 460);
      ctx.fillStyle = '#5a6a6a';
      [360, 420, 480].forEach(function (y) { ctx.fillRect(756, y, 88, 8); });
      ctx.fillStyle = '#8a5a3a';
      ctx.fillRect(796, 230, 6, 70); ctx.fillRect(796, 230, 50, 6);
      d.houses.forEach(function (hs, i) {
        if (Math.abs(hs.x - 800) < 120) return;
        var base = 760;
        ctx.fillStyle = i % 2 ? '#8a867a' : '#9a968a';
        ctx.fillRect(hs.x, base - hs.h, hs.w, hs.h);
        ctx.fillStyle = '#3a3e46';
        ctx.fillRect(hs.x + hs.w * 0.3, base - hs.h * 0.6, hs.w * 0.2, hs.h * 0.3);
        if (hs.roof) {
          ctx.fillStyle = '#4a4e56';
          ctx.beginPath(); ctx.moveTo(hs.x - 10, base - hs.h); ctx.lineTo(hs.x + hs.w / 2, base - hs.h - 50);
          ctx.lineTo(hs.x + hs.w + 10, base - hs.h); ctx.fill();
        }
      });
      // the steeple on its hill
      ctx.fillStyle = '#7e7a70';
      ctx.fillRect(1380, 520, 60, 240);
      ctx.fillStyle = '#4a4e56';
      ctx.beginPath(); ctx.moveTo(1370, 520); ctx.lineTo(1410, 420); ctx.lineTo(1450, 520); ctx.fill();
      // the water, falling away, its edge foaming
      ctx.fillStyle = 'rgba(60,90,100,0.86)';
      ctx.fillRect(0, level, VW, VH - level);
      ctx.fillStyle = 'rgba(220,230,232,0.7)';
      ctx.fillRect(0, level - 3, VW, 5);
      // drips off the roofs as they come clear
      d.drips.forEach(function (dr) {
        var age = t - dr.at;
        if (age < 0 || age > 0.8) return;
        ctx.fillStyle = 'rgba(160,200,210,0.8)';
        ctx.fillRect(dr.x, 560 + age * 300, 3, 9);
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Drawdown').toUpperCase();
      // a depth gauge: the name painted on it, the water line falling past
      var k = outCubic(seg(t, 1.6, 2.2));
      if (k <= 0) return;
      ctx.save();
      ctx.translate(800, 200);
      ctx.globalAlpha *= k;
      ctx.fillStyle = '#e8e4d8';
      ctx.fillRect(-420, -80, 840, 160);
      ctx.strokeStyle = '#3a3e46'; ctx.lineWidth = 4; ctx.strokeRect(-420, -80, 840, 160);
      ctx.fillStyle = '#3a3e46';
      for (var i = 0; i < 21; i++) {
        ctx.fillRect(-400 + i * 40, -80, 3, i % 5 === 0 ? 30 : 16);
      }
      ctx.font = 'bold 16px ' + FONT;
      ctx.textAlign = 'center';
      for (i = 0; i <= 4; i++) ctx.fillText(String(40 - i * 10) + 'm', -400 + i * 200, -36);
      var size = fitSize(ctx, name, 'bold #px ' + HEAVY, 84, 760, 0.1);
      ctx.font = 'bold ' + size + 'px ' + HEAVY;
      ctx.textBaseline = 'middle';
      ctx.fillStyle = '#c42b20';
      spaced(ctx, name, 0, 22, size * 0.1);
      var water = lerp(-80, 82, inOut(seg(t, 2.0, 3.6)));
      ctx.fillStyle = 'rgba(60,90,100,0.75)';
      ctx.fillRect(-420, water, 840, 82 - water);
      ctx.restore();
    }
  });


  // ------------------------------------------------- Lantern Terraces
  Intro.register('br_lantern', {
    tagline: 'A thousand lanterns. Two tea houses. One night.',
    accent: '#ff8a3a',
    cues: [[0.3, 'br_gong', 0.6], [1.6, 'br_chime', 0.4], [2.2, 'explode', 0.2], [2.5, 'explode', 0.15],
           [2.4, 'br_gong', 0.4], [3.4, 'explode', 0.2], [4.2, 'br_chime', 0.3]],
    tagY: 660, tagAt: 3.4,
    setup: function (r) {
      var d = { lanterns: [], bursts: [], terraces: [] };
      for (var i = 0; i < 90; i++) {
        d.lanterns.push({ x: between(r, 0, VW), y0: between(r, 600, 1100), v: between(r, 40, 110),
                          s: between(r, 6, 16), ph: r() * 6 });
      }
      for (i = 0; i < 5; i++) {
        d.bursts.push({ x: between(r, 200, 1400), y: between(r, 120, 320), at: 2.0 + i * 0.6,
                        c: ['#ff6a2a', '#ffd84a', '#ff4a8a', '#8affd8', '#ffffff'][i] });
      }
      for (i = 0; i < 8; i++) d.terraces.push(between(r, -14, 14));
      return d;
    },
    draw: function (ctx, t, d) {
      sky(ctx, [[0, '#08112a'], [0.7, '#2a1e44'], [1, '#4a2a3a']], 700);
      // the moon with its rabbit
      ctx.fillStyle = '#fff0c8';
      ctx.beginPath(); ctx.arc(1250, 170, 70, 0, TAU); ctx.fill();
      ctx.fillStyle = 'rgba(200,180,140,0.5)';
      ctx.beginPath(); ctx.ellipse(1236, 182, 20, 14, 0.3, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.ellipse(1258, 162, 6, 14, -0.3, 0, TAU); ctx.fill();
      // the hills of tea, terraced, both sides of the valley
      [[0, 1], [VW, -1]].forEach(function (side) {
        for (var k = 0; k < 8; k++) {
          var y = 560 + k * 42;
          var w = 520 - k * 40 + d.terraces[k];
          ctx.fillStyle = k % 2 ? '#1e3a1e' : '#244424';
          ctx.fillRect(side[1] > 0 ? 0 : VW - w, y, w, 44);
          ctx.fillStyle = '#2e6a2a';
          for (var j = 0; j < 8; j++) {
            ctx.fillRect(side[1] > 0 ? j * 62 + 10 : VW - w + j * 62 + 10, y - 6, 44, 10);
          }
        }
      });
      // the pagoda in the middle
      ctx.fillStyle = '#1a0a08';
      for (var tier = 0; tier < 5; tier++) {
        var w = 220 - tier * 34, y = 700 - tier * 70;
        ctx.fillRect(800 - w / 2, y - 60, w, 60);
        ctx.beginPath(); ctx.moveTo(800 - w / 2 - 40, y - 60); ctx.lineTo(800 + w / 2 + 40, y - 60);
        ctx.lineTo(800 + w / 2, y - 76); ctx.lineTo(800 - w / 2, y - 76); ctx.fill();
        additive(ctx, function () { dot(ctx, '#ff8a3a', 800, y - 30, w * 0.4, 0.25); });
      }
      ctx.fillRect(796, 330, 8, 50);
      // sky lanterns rising
      additive(ctx, function () {
        d.lanterns.forEach(function (l) {
          var y = l.y0 - t * l.v;
          var x = l.x + Math.sin(t + l.ph) * 14;
          dot(ctx, '#ffb04a', x, y, l.s * 2.4, 0.5);
        });
      });
      d.lanterns.forEach(function (l) {
        var y = l.y0 - t * l.v;
        var x = l.x + Math.sin(t + l.ph) * 14;
        ctx.fillStyle = '#ffcf7a';
        ctx.fillRect(x - l.s * 0.4, y - l.s * 0.5, l.s * 0.8, l.s);
      });
      // fireworks
      d.bursts.forEach(function (bu) {
        var age = t - bu.at;
        if (age < 0 || age > 1.4) return;
        additive(ctx, function () {
          for (var k = 0; k < 24; k++) {
            var a = k * TAU / 24;
            var rr = age * 160;
            dot(ctx, bu.c, bu.x + Math.cos(a) * rr, bu.y + Math.sin(a) * rr + age * age * 40, 10,
                1 - age / 1.4);
          }
        });
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Lantern Terraces').toUpperCase();
      // a red scroll unrolls from the middle, gold letters on it
      var k = outCubic(seg(t, 1.5, 2.3));
      if (k <= 0) return;
      var w = 1100 * k, h = 150;
      ctx.save();
      ctx.translate(800, 220);
      ctx.fillStyle = '#a8281c';
      ctx.fillRect(-w / 2, -h / 2, w, h);
      ctx.strokeStyle = '#e8b84a'; ctx.lineWidth = 4;
      ctx.strokeRect(-w / 2 + 10, -h / 2 + 10, w - 20, h - 20);
      ctx.fillStyle = '#5a3a1a';
      ctx.fillRect(-w / 2 - 16, -h / 2 - 10, 16, h + 20);
      ctx.fillRect(w / 2, -h / 2 - 10, 16, h + 20);
      ctx.beginPath(); ctx.rect(-w / 2, -h / 2, w, h); ctx.clip();
      var size = fitSize(ctx, name, 'bold #px ' + HEAVY, 84, 1000, 0.06);
      ctx.font = 'bold ' + size + 'px ' + HEAVY;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillStyle = '#e8b84a';
      spaced(ctx, name, 0, 4, size * 0.06);
      ctx.restore();
    }
  });

  // ------------------------------------------------- Meteora
  Intro.register('br_meteora', {
    tagline: 'They built on the rock so nobody could reach them.',
    accent: '#f2d8a8',
    cues: [[0.4, 'br_wind', 0.5], [1.4, 'bell', 0.5], [2.6, 'bell', 0.4], [1.9, 'crow', 0.3],
           [3.6, 'crow', 0.25], [4.4, 'bell', 0.3]],
    tagY: 660, tagAt: 3.3,
    setup: function (r) {
      var d = { pillars: [], birds: [], mist: [] };
      for (var layer = 0; layer < 3; layer++) {
        for (var i = 0; i < 7; i++) {
          d.pillars.push({ layer: layer, x: i * 260 + between(r, -60, 60) - 40,
                           w: between(r, 90, 160) * (1 - layer * 0.2), h: between(r, 280, 520) * (1 - layer * 0.25) });
        }
      }
      for (i = 0; i < 9; i++) d.birds.push({ x: between(r, 300, 1300), y: between(r, 150, 300), ph: r() * 6, r: between(r, 60, 160) });
      for (i = 0; i < 12; i++) d.mist.push({ y: between(r, 380, 760), x: r() * VW, w: between(r, 400, 900), v: between(r, 10, 40) });
      return d;
    },
    draw: function (ctx, t, d) {
      sky(ctx, [[0, '#7aa8d8'], [0.6, '#e8d8c8'], [1, '#f2e2c8']]);
      additive(ctx, function () { dot(ctx, '#fff0c8', 1300, 300, 300, 0.5); });
      // pillars in three layers, the back ones paler in the mist
      for (var layer = 2; layer >= 0; layer--) {
        var shade = ['#8a7a64', '#a89a84', '#c8beb0'][layer];
        d.pillars.forEach(function (p) {
          if (p.layer !== layer) return;
          var base = 900 - layer * 60;
          ctx.fillStyle = shade;
          ctx.beginPath();
          ctx.moveTo(p.x, base); ctx.lineTo(p.x + p.w * 0.08, base - p.h);
          ctx.quadraticCurveTo(p.x + p.w * 0.5, base - p.h - 30, p.x + p.w * 0.92, base - p.h);
          ctx.lineTo(p.x + p.w, base); ctx.fill();
        });
        // a band of mist between the layers
        ctx.fillStyle = 'rgba(242,238,230,' + (0.35 + layer * 0.1) + ')';
        d.mist.forEach(function (m, i) {
          if (i % 3 !== layer) return;
          ctx.beginPath();
          ctx.ellipse((m.x + t * m.v) % (VW + 600) - 300, m.y, m.w / 2, 40, 0, 0, TAU);
          ctx.fill();
        });
      }
      // the monastery on the nearest tall pillar, its dome, the basket
      var mx = 1080, my = 380;
      ctx.fillStyle = '#7a6a54';
      ctx.fillRect(mx - 120, my, 240, 520);
      ctx.fillStyle = '#ece6da';
      ctx.fillRect(mx - 110, my - 70, 220, 70);
      ctx.fillStyle = '#b8582e';
      ctx.fillRect(mx - 118, my - 80, 236, 12);
      ctx.beginPath(); ctx.arc(mx, my - 80, 42, Math.PI, TAU); ctx.fill();
      var drop = 120 + Math.sin(t * 0.8) * 20 + t * 26;
      ctx.strokeStyle = '#5a4a3a'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(mx - 130, my - 40); ctx.lineTo(mx - 130, my - 40 + drop); ctx.stroke();
      ctx.fillStyle = '#a07a4a';
      ctx.fillRect(mx - 142, my - 40 + drop, 24, 20);
      // birds circling
      d.birds.forEach(function (bd) {
        var a = t * 0.6 + bd.ph;
        K.crow(ctx, bd.x + Math.cos(a) * bd.r, bd.y + Math.sin(a) * bd.r * 0.3, 0.9, t * 9 + bd.ph, false);
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Meteora').toUpperCase();
      // carved into a slab of the rock as the mist burns off
      var k = seg(t, 1.4, 2.6);
      if (k <= 0) return;
      ctx.save();
      ctx.translate(560, 230);
      ctx.fillStyle = '#a89880';
      roundRect(ctx, -420, -90, 840, 180, 16);
      ctx.fill();
      ctx.strokeStyle = '#7a6a54'; ctx.lineWidth = 6; ctx.stroke();
      var size = fitSize(ctx, name, 'bold #px Georgia, serif', 104, 740, 0.14);
      ctx.font = 'bold ' + size + 'px Georgia, serif';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillStyle = 'rgba(255,255,255,0.35)';
      spaced(ctx, name, 3, 7, size * 0.14);
      ctx.fillStyle = '#4a3a2a';
      spaced(ctx, name, 0, 4, size * 0.14);
      ctx.fillStyle = 'rgba(242,238,230,' + (1 - k) + ')';
      ctx.fillRect(-430, -100, 860, 200);
      ctx.restore();
    }
  });

  // ------------------------------------------------- Circuit City
  Intro.register('br_circuit', {
    tagline: 'Power on. Run the traces. Take the port.',
    accent: '#ffb05a',
    cues: [[0.2, 'br_beep', 0.5], [0.9, 'br_tick', 0.6], [1.1, 'br_tick', 0.6], [1.3, 'br_tick', 0.6],
           [1.9, 'br_hum', 0.6], [2.4, 'br_beep', 0.6], [3.2, 'br_arc', 0.3]],
    tagY: 660, tagAt: 3.2,
    setup: function (r) {
      var d = { traces: [], chips: [], caps: [] };
      for (var i = 0; i < 26; i++) {
        var x = 800, y = 470, pts = [[x, y]];
        var dir = i % 4;
        for (var k = 0; k < 4; k++) {
          var len = between(r, 80, 260);
          if (dir === 0) x += len; else if (dir === 1) x -= len; else if (dir === 2) y += len * 0.5; else y -= len * 0.5;
          pts.push([x, y]);
          dir = (dir + (r() < 0.5 ? 1 : 3)) % 4;
          if (dir > 1 && k === 0) dir = r() < 0.5 ? 0 : 1;
        }
        d.traces.push({ pts: pts, at: between(r, 0.6, 2.2) });
      }
      for (i = 0; i < 14; i++) d.chips.push({ x: between(r, 60, 1500), y: between(r, 120, 820), w: between(r, 40, 110), h: between(r, 30, 70) });
      for (i = 0; i < 10; i++) d.caps.push({ x: between(r, 60, 1540), y: between(r, 140, 840), r: between(r, 14, 30), c: r() < 0.5 ? '#2a4aa8' : '#22242a' });
      return d;
    },
    draw: function (ctx, t, d) {
      ctx.fillStyle = '#0e2a1c';
      ctx.fillRect(0, 0, VW, VH);
      ctx.strokeStyle = 'rgba(80,160,110,0.18)'; ctx.lineWidth = 1;
      for (var g = 0; g < VW; g += 40) { ctx.beginPath(); ctx.moveTo(g, 0); ctx.lineTo(g, VH); ctx.stroke(); }
      d.chips.forEach(function (c) {
        ctx.fillStyle = '#1b1d22';
        ctx.fillRect(c.x, c.y, c.w, c.h);
        ctx.fillStyle = '#c8ccd2';
        for (var p = 4; p < c.w - 4; p += 9) { ctx.fillRect(c.x + p, c.y - 5, 4, 5); ctx.fillRect(c.x + p, c.y + c.h, 4, 5); }
      });
      d.caps.forEach(function (c) {
        ctx.fillStyle = c.c; ctx.beginPath(); ctx.arc(c.x, c.y, c.r, 0, TAU); ctx.fill();
        ctx.strokeStyle = '#c8ccd2'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(c.x - c.r * 0.6, c.y); ctx.lineTo(c.x + c.r * 0.6, c.y);
        ctx.moveTo(c.x, c.y - c.r * 0.6); ctx.lineTo(c.x, c.y + c.r * 0.6); ctx.stroke();
      });
      // current races out along the traces from the CPU
      d.traces.forEach(function (tr) {
        var k = seg(t, tr.at, tr.at + 1.2);
        ctx.strokeStyle = '#5a4a22'; ctx.lineWidth = 6;
        ctx.beginPath(); ctx.moveTo(tr.pts[0][0], tr.pts[0][1]);
        tr.pts.forEach(function (p) { ctx.lineTo(p[0], p[1]); }); ctx.stroke();
        if (k <= 0) return;
        var total = 0, segs = [];
        for (var i = 1; i < tr.pts.length; i++) {
          var l = Math.hypot(tr.pts[i][0] - tr.pts[i - 1][0], tr.pts[i][1] - tr.pts[i - 1][1]);
          segs.push(l); total += l;
        }
        var reach = total * k, run = 0;
        ctx.strokeStyle = '#ffb05a'; ctx.lineWidth = 5;
        ctx.beginPath(); ctx.moveTo(tr.pts[0][0], tr.pts[0][1]);
        var hx = tr.pts[0][0], hy = tr.pts[0][1];
        for (i = 1; i < tr.pts.length; i++) {
          var f = Math.min(1, Math.max(0, (reach - run) / segs[i - 1]));
          hx = tr.pts[i - 1][0] + (tr.pts[i][0] - tr.pts[i - 1][0]) * f;
          hy = tr.pts[i - 1][1] + (tr.pts[i][1] - tr.pts[i - 1][1]) * f;
          ctx.lineTo(hx, hy);
          run += segs[i - 1];
          if (f < 1) break;
        }
        ctx.stroke();
        additive(ctx, function () { dot(ctx, '#ffd08a', hx, hy, 24, k < 1 ? 1 : 0.4); });
      });
      // the CPU in the middle, its heatsink fins, the fan ring
      ctx.fillStyle = '#3a3e46';
      ctx.fillRect(700, 370, 200, 200);
      ctx.fillStyle = '#b8c0c8';
      for (var f = 0; f < 9; f++) ctx.fillRect(712 + f * 21, 380, 8, 180);
      additive(ctx, function () {
        ctx.strokeStyle = 'rgba(255,74,170,' + (0.5 + 0.4 * Math.sin(t * 4)) + ')'; ctx.lineWidth = 8;
        ctx.beginPath(); ctx.arc(800, 470, 80, 0, TAU); ctx.stroke();
      });
      // the boot text
      var lines = ['BIOS v2.6 ... OK', 'MEMORY 4 x 16GB ... OK', 'RELAY LINK ... ESTABLISHED',
                   'FLAGS ... RED / BLUE', 'BOOT >'];
      ctx.font = 'bold 18px Consolas, Menlo, monospace';
      ctx.textAlign = 'left'; ctx.textBaseline = 'top';
      ctx.fillStyle = '#4aff7a';
      lines.forEach(function (ln, i) {
        var at = 0.3 + i * 0.35;
        var n = Math.floor(ln.length * seg(t, at, at + 0.3));
        if (n > 0) ctx.fillText(ln.slice(0, n), 60, 120 + i * 26);
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Circuit City').toUpperCase();
      // an LED dot-matrix display lights up letter by letter
      var k = seg(t, 2.0, 2.2);
      if (k <= 0) return;
      ctx.save();
      ctx.translate(800, 260);
      ctx.fillStyle = '#0a0c10';
      roundRect(ctx, -520, -80, 1040, 160, 12);
      ctx.fill();
      ctx.strokeStyle = '#3a3e46'; ctx.lineWidth = 4; ctx.stroke();
      var size = fitSize(ctx, name, 'bold #px Consolas, Menlo, monospace', 96, 940, 0.1);
      ctx.font = 'bold ' + size + 'px Consolas, Menlo, monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      var shown = name.slice(0, Math.floor(name.length * seg(t, 2.1, 2.9)) + 1);
      var pad = name.slice(shown.length).replace(/./g, ' ');
      additive(ctx, function () {
        ctx.fillStyle = 'rgba(255,176,90,0.9)';
        spaced(ctx, shown + pad, 0, 4, size * 0.1);
      });
      ctx.restore();
    }
  });

  /* Snowglobe Hollow: a souvenir snow globe on the mantelpiece, the fire
     glowing.  Somebody shakes it -- the snow goes everywhere -- and as it
     settles the village's windows come on one by one, the toy train goes
     round the square, and the name comes up on the brass plaque. */
  Intro.register('br_snowglobe', {
    tagline: 'Shake it up. Take the chalet. Bring it home.',
    accent: '#bfe8ff',
    cues: [[0.15, 'br_musicbox', 0.7], [0.7, 'br_rumble', 0.7], [1.95, 'br_musicbox', 0.5],
           [2.5, 'br_whistle', 0.45], [3.3, 'br_toll', 0.5]],
    tagY: 856, tagAt: 3.1,
    setup: function (r) {
      var d = { flakes: [], houses: [], pines: [], stripes: [] };
      for (var i = 0; i < 190; i++) {
        d.flakes.push({ a: r() * TAU, rr: Math.sqrt(r()), y: between(r, -1, 1), s: between(r, 1.6, 4.2),
                        sp: between(r, 0.6, 1.4), ph: r() * TAU });
      }
      for (i = 0; i < 9; i++) {
        d.houses.push({ x: -190 + i * 47 + between(r, -8, 8), w: between(r, 30, 44), h: between(r, 26, 44),
                        c: ['#f2e0c8', '#f2ead8', '#e8d8e8', '#f2e8c0', '#e0e8f0'][i % 5], on: between(r, 1.7, 3.0) });
      }
      for (i = 0; i < 14; i++) d.pines.push({ x: between(r, -250, 250), y: between(r, 120, 200), s: between(r, 0.6, 1.2) });
      for (i = 0; i < 26; i++) d.stripes.push(i);
      return d;
    },
    draw: function (ctx, t, d) {
      // the room: a dark papered wall, the fire's glow coming up from below
      ctx.fillStyle = '#2a1a1e';
      ctx.fillRect(0, 0, VW, VH);
      ctx.fillStyle = 'rgba(255,255,255,0.025)';
      d.stripes.forEach(function (i) { ctx.fillRect(i * 64, 0, 22, VH); });
      var flick = 0.8 + 0.2 * Math.sin(t * 9) * Math.sin(t * 5.3);
      additive(ctx, function () {
        dot(ctx, '#ff8a3a', 160, 900, 520, 0.4 * flick);
        dot(ctx, '#ff8a3a', 1440, 900, 520, 0.4 * flick);
      });
      // the mantelpiece
      ctx.fillStyle = '#5a2a1a'; ctx.fillRect(0, 770, VW, 44);
      ctx.fillStyle = '#7a3e26'; ctx.fillRect(0, 770, VW, 8);
      ctx.fillStyle = '#3a1a10'; ctx.fillRect(0, 814, VW, 86);
      // the shake: the globe rocks for a second, then settles
      var shake = seg(t, 0.55, 1.75), hump = Math.sin(shake * Math.PI);
      var rock = Math.sin(t * 26) * 0.07 * hump, lift = -38 * hump;
      ctx.save();
      ctx.translate(800, 770 + lift);
      ctx.rotate(rock);
      // the base: dark wood, a gold band, (the plaque is the title)
      ctx.fillStyle = '#4a1e14';
      ctx.beginPath(); ctx.moveTo(-330, 0); ctx.lineTo(330, 0); ctx.lineTo(270, -136); ctx.lineTo(-270, -136); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#6a2e22'; ctx.fillRect(-276, -150, 552, 18);
      ctx.fillStyle = '#e8c050'; ctx.fillRect(-280, -156, 560, 8);
      // the globe
      var R = 268, cy = -156 - R * 0.86;
      ctx.save();
      ctx.beginPath(); ctx.arc(0, cy, R, 0, TAU); ctx.clip();
      var sky = ctx.createLinearGradient(0, cy - R, 0, cy + R);
      sky.addColorStop(0, '#3a3058'); sky.addColorStop(0.55, '#c89a8a'); sky.addColorStop(1, '#f2e0d0');
      ctx.fillStyle = sky; ctx.fillRect(-R, cy - R, R * 2, R * 2);
      // far peaks
      ctx.fillStyle = '#e8eef4';
      [[-220, 90], [-120, 130], [10, 100], [140, 140], [240, 96]].forEach(function (p) {
        ctx.beginPath(); ctx.moveTo(p[0] - 110, cy + 60); ctx.lineTo(p[0], cy + 60 - p[1]); ctx.lineTo(p[0] + 110, cy + 60); ctx.fill();
      });
      // the snowy ground, the two chalet hills
      ctx.fillStyle = '#f6f8fa';
      ctx.beginPath(); ctx.ellipse(0, cy + 190, R * 1.1, 150, 0, 0, TAU); ctx.fill();
      [[-1, '#c42b20'], [1, '#0d69ac']].forEach(function (side) {
        var hx = side[0] * 215;
        ctx.fillStyle = '#eef2f6';
        ctx.beginPath(); ctx.ellipse(hx, cy + 108, 110, 64, 0, Math.PI, TAU); ctx.fill();
        ctx.fillStyle = '#6a4a2e'; ctx.fillRect(hx - 34, cy + 22, 68, 40);
        ctx.fillStyle = '#4a5060';
        ctx.beginPath(); ctx.moveTo(hx - 44, cy + 24); ctx.lineTo(hx, cy - 8); ctx.lineTo(hx + 44, cy + 24); ctx.fill();
        ctx.fillStyle = '#f6f8fa';
        ctx.beginPath(); ctx.moveTo(hx - 38, cy + 18); ctx.lineTo(hx, cy - 6); ctx.lineTo(hx + 38, cy + 18); ctx.lineTo(hx, cy + 6); ctx.fill();
        if (t > 2.0) { ctx.fillStyle = '#ffd890'; ctx.fillRect(hx - 22, cy + 34, 10, 10); ctx.fillRect(hx + 12, cy + 34, 10, 10); }
        pennant(ctx, hx + side[0] * 40, cy + 14, 44, side[1], t, side[0] < 0 ? 1 : -1);
      });
      // the town: houses, lit window by window, the church and the clock tower
      d.houses.forEach(function (h) {
        var y0 = cy + 150;
        ctx.fillStyle = h.c; ctx.fillRect(h.x - h.w / 2, y0 - h.h, h.w, h.h);
        ctx.fillStyle = '#f6f8fa';
        ctx.beginPath(); ctx.moveTo(h.x - h.w / 2 - 4, y0 - h.h); ctx.lineTo(h.x, y0 - h.h - 18); ctx.lineTo(h.x + h.w / 2 + 4, y0 - h.h); ctx.fill();
        ctx.fillStyle = t > h.on ? '#ffd27a' : '#6a6a78';
        ctx.fillRect(h.x - 8, y0 - h.h + 10, 7, 8); ctx.fillRect(h.x + 2, y0 - h.h + 10, 7, 8);
        if (t > h.on) additive(ctx, function () { dot(ctx, '#ffcf7a', h.x, y0 - h.h + 14, 18, 0.5); });
      });
      ctx.fillStyle = '#e8d8c0'; ctx.fillRect(-16, cy - 30, 32, 150);
      ctx.fillStyle = '#4a5060';
      ctx.beginPath(); ctx.moveTo(-22, cy - 30); ctx.lineTo(0, cy - 78); ctx.lineTo(22, cy - 30); ctx.fill();
      ctx.fillStyle = '#f2ead8'; ctx.beginPath(); ctx.arc(0, cy + 2, 12, 0, TAU); ctx.fill();
      ctx.strokeStyle = '#2a2218'; ctx.lineWidth = 2.5;
      var ang = t * 1.4;
      ctx.beginPath(); ctx.moveTo(0, cy + 2); ctx.lineTo(Math.sin(ang) * 9, cy + 2 - Math.cos(ang) * 9);
      ctx.moveTo(0, cy + 2); ctx.lineTo(Math.sin(ang / 12) * 6, cy + 2 - Math.cos(ang / 12) * 6); ctx.stroke();
      ctx.fillStyle = '#3a6a4a'; ctx.beginPath(); ctx.arc(-96, cy + 46, 16, Math.PI, TAU); ctx.fill();
      ctx.fillStyle = '#f2ead8'; ctx.fillRect(-108, cy + 46, 24, 40);
      // the carousel, the toy train going round
      ctx.fillStyle = '#d8322a';
      ctx.beginPath(); ctx.moveTo(80, cy + 120); ctx.lineTo(104, cy + 98); ctx.lineTo(128, cy + 120); ctx.fill();
      ctx.fillStyle = '#c8a060'; ctx.fillRect(84, cy + 120, 40, 18);
      for (var c = 0; c < 5; c++) {
        var ta = t * 0.9 - c * 0.16;
        var tx = Math.cos(ta) * 160, ty = cy + 196 + Math.sin(ta) * 22;
        ctx.fillStyle = c === 0 ? '#2a6a3a' : (c === 4 ? '#c42b20' : ['#2a6aa8', '#f2c21e', '#c42b20'][c % 3]);
        ctx.fillRect(tx - 10, ty - 8, 20, 12);
      }
      // pines
      d.pines.forEach(function (p) {
        var y = cy + p.y;
        ctx.fillStyle = '#2a5a3a';
        ctx.beginPath(); ctx.moveTo(p.x - 14 * p.s, y); ctx.lineTo(p.x, y - 40 * p.s); ctx.lineTo(p.x + 14 * p.s, y); ctx.fill();
        ctx.fillStyle = '#f6f8fa';
        ctx.beginPath(); ctx.moveTo(p.x - 6 * p.s, y - 26 * p.s); ctx.lineTo(p.x, y - 40 * p.s); ctx.lineTo(p.x + 6 * p.s, y - 26 * p.s); ctx.fill();
      });
      // the snow: whirled up by the shake, then settling
      d.flakes.forEach(function (f) {
        var whirl = hump * 3.2 + shake * 2;
        var a = f.a + whirl * f.sp + t * 0.2;
        var settle = seg(t, 1.6, 4.6);
        var x = Math.cos(a) * f.rr * R * 0.95;
        var yv = f.y * R * 0.85 * (1 - hump * 0.3) + settle * 140 * f.sp + Math.sin(t * 2 + f.ph) * 6;
        var y = cy + ((yv + R) % (R * 2)) - R;
        ctx.fillStyle = 'rgba(255,255,255,0.9)';
        ctx.beginPath(); ctx.arc(x, y, f.s * (0.7 + hump * 0.4), 0, TAU); ctx.fill();
      });
      ctx.restore();
      // the glass: a rim, the window's reflection, the fire's
      ctx.strokeStyle = 'rgba(220,240,255,0.5)'; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.arc(0, cy, R, 0, TAU); ctx.stroke();
      additive(ctx, function () {
        ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 16;
        ctx.beginPath(); ctx.arc(0, cy, R - 30, Math.PI * 1.12, Math.PI * 1.42); ctx.stroke();
        ctx.strokeStyle = 'rgba(255,170,90,' + (0.18 * flick) + ')'; ctx.lineWidth = 22;
        ctx.beginPath(); ctx.arc(0, cy, R - 24, Math.PI * 0.2, Math.PI * 0.55); ctx.stroke();
      });
      ctx.restore();
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Snowglobe Hollow').toUpperCase();
      var k = seg(t, 2.05, 2.5);
      if (k <= 0) return;
      var shake = seg(t, 0.55, 1.75), hump = Math.sin(shake * Math.PI);
      ctx.save();
      ctx.translate(800, 770 - 38 * hump);
      ctx.rotate(Math.sin(t * 26) * 0.07 * hump);
      ctx.translate(0, -70);
      ctx.globalAlpha = k;
      var w = 420, h = 64;
      var plate = ctx.createLinearGradient(0, -h / 2, 0, h / 2);
      plate.addColorStop(0, '#f2d27a'); plate.addColorStop(0.5, '#c89a3a'); plate.addColorStop(1, '#e8c060');
      ctx.fillStyle = plate;
      roundRect(ctx, -w / 2, -h / 2, w, h, 10); ctx.fill();
      ctx.strokeStyle = '#7a5a1a'; ctx.lineWidth = 3; ctx.stroke();
      var size = fitSize(ctx, name, 'bold #px Georgia, serif', 40, w - 50, 0.08);
      ctx.font = 'bold ' + size + 'px Georgia, serif';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillStyle = 'rgba(255,240,200,0.6)';
      spaced(ctx, name, 0, 2, size * 0.08);
      ctx.fillStyle = '#4a3010';
      spaced(ctx, name, 0, 0, size * 0.08);
      // a shine running along the brass
      var sweep = seg(t, 2.5, 3.2);
      if (sweep > 0 && sweep < 1) {
        additive(ctx, function () {
          var x = -w / 2 + sweep * w;
          var g = ctx.createLinearGradient(x - 40, 0, x + 40, 0);
          g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(0.5, 'rgba(255,250,220,0.55)');
          g.addColorStop(1, 'rgba(255,255,255,0)');
          ctx.fillStyle = g; ctx.fillRect(x - 40, -h / 2, 80, h);
        });
      }
      ctx.restore();
    }
  });

  /* Big Ear Array: the dishes on the skyline under the Milky Way, all
     turning together; a scope trace jumps; then the printout comes up out
     of the printer with the name on it, and somebody circles it in red pen
     and writes WOW! beside it. */
  Intro.register('br_bigear', {
    tagline: 'They are listening. Carry the flag and the whole sky knows.',
    accent: '#9ab8ff',
    cues: [[0.3, 'br_howl', 0.45], [1.0, 'br_beep', 0.5], [1.4, 'br_beep', 0.6], [1.8, 'br_whirr', 0.5],
           [2.1, 'br_tick', 0.6], [2.25, 'br_tick', 0.6], [2.4, 'br_tick', 0.6], [2.55, 'br_tick', 0.6],
           [3.1, 'br_ufo', 0.4]],
    tagY: 846, tagAt: 3.3,
    setup: function (r) {
      var d = { stars: [], milky: [], dishes: [], rocks: [] };
      for (var i = 0; i < 260; i++) d.stars.push({ x: r() * VW, y: r() * 520, s: between(r, 0.6, 2.2), p: r() * TAU });
      for (i = 0; i < 420; i++) {
        var u = r();
        d.milky.push({ x: u * VW, y: 420 - u * 330 + (r() - 0.5) * 120 * (0.4 + r()), s: between(r, 0.4, 1.4) });
      }
      for (i = 0; i < 7; i++) d.dishes.push({ x: 140 + i * 220 + between(r, -20, 20), s: between(r, 0.7, 1.15) });
      return d;
    },
    draw: function (ctx, t, d) {
      var g = ctx.createLinearGradient(0, 0, 0, VH);
      g.addColorStop(0, '#03040c'); g.addColorStop(0.55, '#141a3a'); g.addColorStop(0.75, '#3a2a48'); g.addColorStop(1, '#1a1018');
      ctx.fillStyle = g; ctx.fillRect(0, 0, VW, VH);
      additive(ctx, function () {
        d.milky.forEach(function (m) { ctx.fillStyle = 'rgba(200,210,255,0.22)'; ctx.fillRect(m.x, m.y, m.s, m.s); });
        d.stars.forEach(function (st) {
          var tw = 0.5 + 0.5 * Math.sin(t * 3 + st.p);
          ctx.fillStyle = 'rgba(255,255,255,' + (0.4 + 0.6 * tw) + ')';
          ctx.fillRect(st.x, st.y, st.s, st.s);
        });
      });
      // the skyline: mesas, and the dishes all turning together
      ctx.fillStyle = '#0c0a14';
      ctx.beginPath(); ctx.moveTo(0, 640);
      [[120, 600], [260, 600], [300, 560], [520, 560], [560, 610], [900, 620], [960, 580], [1180, 580],
       [1220, 630], [1600, 620]].forEach(function (p) { ctx.lineTo(p[0], p[1]); });
      ctx.lineTo(1600, 900); ctx.lineTo(0, 900); ctx.fill();
      var turn = -0.6 + 1.1 * inOut(seg(t, 0.6, 2.2));
      d.dishes.forEach(function (dd, i) {
        var x = dd.x, y = 640, s = dd.s;
        ctx.fillStyle = '#05050a';
        ctx.fillRect(x - 6 * s, y - 70 * s, 12 * s, 70 * s);
        ctx.fillRect(x - 26 * s, y - 14 * s, 52 * s, 14 * s);
        ctx.save();
        ctx.translate(x, y - 76 * s);
        ctx.rotate(turn);
        ctx.beginPath(); ctx.ellipse(0, 0, 70 * s, 26 * s, 0, Math.PI, TAU); ctx.fill();
        ctx.strokeStyle = '#05050a'; ctx.lineWidth = 3 * s;
        ctx.beginPath(); ctx.moveTo(-50 * s, -6 * s); ctx.lineTo(0, -70 * s); ctx.lineTo(50 * s, -6 * s); ctx.stroke();
        if (Math.sin(t * 4 + i) > 0.3) additive(ctx, function () { dot(ctx, '#ff3020', 0, -72 * s, 10, 0.9); });
        ctx.restore();
      });
      // the scope: a trace along the bottom, jumping at 1.4
      var k = seg(t, 0.8, 1.2);
      if (k > 0) {
        ctx.globalAlpha = Math.min(1, k) * (1 - seg(t, 2.6, 3.0) * 0.6);
        ctx.fillStyle = 'rgba(4,20,10,0.85)';
        roundRect(ctx, 60, 690, 520, 150, 10); ctx.fill();
        ctx.strokeStyle = 'rgba(122,255,154,0.25)'; ctx.lineWidth = 1;
        for (var gx = 60; gx <= 580; gx += 52) { ctx.beginPath(); ctx.moveTo(gx, 690); ctx.lineTo(gx, 840); ctx.stroke(); }
        additive(ctx, function () {
          ctx.strokeStyle = '#7aff9a'; ctx.lineWidth = 2.5;
          ctx.beginPath();
          for (var x = 0; x <= 500; x += 4) {
            var u = x / 500;
            var spike = Math.exp(-Math.pow((u - 0.62) * 14, 2)) * seg(t, 1.35, 1.6) * 52;
            var y = 765 + Math.sin(u * 40 + t * 9) * 6 + Math.sin(u * 97 - t * 13) * 4 - spike;
            if (x === 0) ctx.moveTo(70 + x, y); else ctx.lineTo(70 + x, y);
          }
          ctx.stroke();
        });
        ctx.globalAlpha = 1;
      }
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Big Ear Array').toUpperCase();
      var k = seg(t, 1.9, 2.7);
      if (k <= 0) return;
      // the printout scrolls up out of the printer
      var W = 760, top = 900 - k * 560;
      ctx.save();
      ctx.translate(800 - W / 2, top);
      ctx.fillStyle = '#f4f1e6'; ctx.fillRect(0, 0, W, 620);
      ctx.fillStyle = 'rgba(80,150,110,0.12)';
      for (var band = 0; band < 620; band += 64) ctx.fillRect(0, band, W, 32);
      ctx.fillStyle = '#d8d4c8';
      for (var hole = 18; hole < 620; hole += 26) {
        ctx.beginPath(); ctx.arc(14, hole, 5, 0, TAU); ctx.arc(W - 14, hole, 5, 0, TAU); ctx.fill();
      }
      ctx.font = 'bold 20px Consolas, Menlo, monospace';
      ctx.fillStyle = '#3a3a48'; ctx.textAlign = 'left'; ctx.textBaseline = 'top';
      var rows = ['1 1  1   1  1 1   1 1  1   1', '1  1 1  1 1   1 1  1 1 1  1', '  1 1  6EQUJ5  1   1  1 1 1',
                  '1   1 1  1  1 1  1   1  1  1'];
      rows.forEach(function (row, i) { ctx.fillText(row, 60, 40 + i * 30); });
      var size = fitSize(ctx, name, 'bold #px Consolas, Menlo, monospace', 58, W - 160, 0.12);
      ctx.font = 'bold ' + size + 'px Consolas, Menlo, monospace';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillStyle = '#1a1a2a';
      spaced(ctx, name, W / 2 - 40, 214, size * 0.12);
      // the red pen: round the name, then WOW!
      var pen = seg(t, 2.55, 3.15);
      if (pen > 0) {
        ctx.strokeStyle = '#d8221a'; ctx.lineWidth = 6; ctx.lineCap = 'round';
        ctx.beginPath();
        var steps = 60, rx = W * 0.42, ry = 52;
        for (var i = 0; i <= steps * pen; i++) {
          var a = -Math.PI * 0.9 + (i / steps) * TAU * 1.08;
          var x = W / 2 - 40 + Math.cos(a) * rx * (1 + 0.03 * Math.sin(i * 0.7));
          var y = 214 + Math.sin(a) * ry * (1 + 0.05 * Math.sin(i * 1.3));
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.stroke();
        var wow = seg(t, 3.0, 3.3);
        if (wow > 0) {
          ctx.save();
          ctx.translate(W - 70, 150); ctx.rotate(-0.15);
          ctx.font = 'italic bold 52px Georgia, serif';
          ctx.fillStyle = '#d8221a'; ctx.textAlign = 'center';
          ctx.globalAlpha = wow;
          ctx.fillText('Wow!', 0, 0);
          ctx.restore();
        }
      }
      ctx.restore();
    }
  });

  global.BlackoutRelayScenes = { runner: runner, pennant: pennant, sky: sky, bolt: bolt,
                                 rainOver: rainOver, makeRain: makeRain, neonTitle: neonTitle,
                                 stencilPlate: stencilPlate };
})(window);
