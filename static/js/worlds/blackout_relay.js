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
      sparks: { n: 50, fall: 1.0, size: [0.12, 0.12, 0.12], colour: '#9fe8ff', a: 0.9, glow: 1, drift: 1.4 }
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
      var name = (run.info.name || 'Thimble Acre').toUpperCase().replace(/ /g, '');
      var colours = ['#c4281c', '#0d69ac', '#f2c21e', '#3a9a3a'];
      var w = 96, gap = 10, total = name.length * (w + gap) - gap;
      var x0 = 800 - total / 2;
      for (var i = 0; i < name.length; i++) {
        var at = 2.0 + i * 0.15 * (5 / Math.max(5, name.length));
        var k = seg(t, at, at + 0.35);
        if (k <= 0) continue;
        var bounce = k < 1 ? lerp(-500, 0, outBack(k, 1.8)) : 0;
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

  global.BlackoutRelayScenes = { runner: runner, pennant: pennant, sky: sky, bolt: bolt,
                                 rainOver: rainOver, makeRain: makeRain, neonTitle: neonTitle,
                                 stencilPlate: stencilPlate };
})(window);
