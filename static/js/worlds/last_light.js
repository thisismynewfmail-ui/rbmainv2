/* Last Light -- the Game View half of the places added to the rotation.

   The survival client itself is static/js/game/survival.js; it swaps the
   world when the server moves everybody to a new place ('zarea'), plays the
   place's arrival sequence (game/area_intro.js) and draws the infected.
   This plugin (client.js loads it as WorldPlugins.last_light) adds what the
   newer places need on top of that:

     * rigs    -- the moving scenery a place lists in markers.extra.rigs
                  (static/js/game/rigs.js draws them; the kinds are in
                  last_light_rigs.js).  They hear the game: a wave starting
                  or cleared, the lure going off, an infected dying, a shot,
                  a wipe -- and they can see the survivors and the infected;
     * weather -- what the place's sky is doing round the camera (rain,
                  drizzle, fog, embers, snow, spray...), never under a roof,
                  and the lightning that goes with a storm.

   Every new place has an arrival scene, registered at the bottom under the
   place's own id (the ids of the first four are area_intro.js's own). */
(function (global) {
  'use strict';

  var GA = global.GameAudio;
  if (GA) {
    GA.register('ll_thunder', function (vol) {
      this.noise({ freq: 380, freqEnd: 60, dur: 2.4, gain: 0.34 * vol });
      this.later(90, function () { this.noise({ freq: 900, freqEnd: 120, dur: 1.1, gain: 0.2 * vol }); });
      this.tone({ type: 'sawtooth', freq: 48, freqEnd: 30, dur: 1.8, gain: 0.05 * vol });
    });
    GA.register('ll_rain', function (vol) {
      this.noise({ filter: 'highpass', freq: 2600, dur: 2.4, gain: 0.05 * vol });
      this.noise({ filter: 'bandpass', freq: 1200, dur: 2.2, gain: 0.03 * vol });
    });
    GA.register('ll_wind', function (vol) {
      this.noise({ filter: 'bandpass', freq: 500, freqEnd: 900, dur: 2.6, gain: 0.08 * vol });
    });
    GA.register('ll_click', function (vol) {
      this.tone({ type: 'square', freq: 1800, dur: 0.025, gain: 0.06 * vol });
    });
    GA.register('ll_clunk', function (vol) {
      this.tone({ type: 'square', freq: 150, freqEnd: 70, dur: 0.18, gain: 0.14 * vol });
      this.noise({ filter: 'bandpass', freq: 1800, freqEnd: 500, dur: 0.14, gain: 0.12 * vol });
    });
    GA.register('ll_sting', function (vol) {
      // the horror chord under a title
      [110, 116.5, 164.8, 233].forEach(function (f, i) {
        this.tone({ type: i % 2 ? 'sawtooth' : 'triangle', freq: f, freqEnd: f * 0.97, dur: 2.6,
                    gain: 0.05 * vol });
      }, this);
      this.noise({ filter: 'bandpass', freq: 300, dur: 1.6, gain: 0.05 * vol });
    });
  }

  function rgb(hex) {
    var n = parseInt(hex.slice(1), 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
  }

  // ======================================================= the plugin
  global.WorldPlugins = global.WorldPlugins || {};
  global.WorldPlugins.last_light = function (client) {
    var current = { area: '', weather: '', accent: '#e0a040' };
    var drops = [];
    var roofs = { at: -10, eye: [0, -1e9, 0], cells: {} };
    var flash = { at: -10, next: 4 + Math.random() * 6, power: 0 };
    var clock = 0;
    var rigs = [];

    function survival() { return client.survival || null; }

    var rigCtx = {
      critters: [],
      players: function () {
        var out = [];
        if (client.myId && client.local && client.local.alive !== false) {
          out.push({ id: client.myId, pos: client.local.pos, me: true });
        }
        Object.keys(client.players || {}).forEach(function (id) {
          var p = client.players[id];
          if (p && p.alive && p.pos) out.push({ id: p.id, pos: p.pos });
        });
        return out;
      },
      zombies: function () {
        var out = [];
        var s = survival();
        if (!s || !s.zombies) return out;
        for (var id in s.zombies) {
          var z = s.zombies[id];
          if (z && z.pos) out.push({ id: z.id, pos: z.pos, kind: z.kind });
        }
        return out;
      },
      viewer: function () {
        var cam = client.cameraPosition ? client.cameraPosition() : null;
        var at = cam && cam.eye ? cam.eye : client.local.pos;
        var yaw = client.local.yaw || 0, pitch = client.local.pitch || 0, cp = Math.cos(pitch);
        return { eye: at, dir: [Math.sin(yaw) * cp, Math.sin(pitch), Math.cos(yaw) * cp] };
      },
      wave: function () {
        var st = client.state || {};
        var lure = st.lure || {};
        return { wave: st.wave || 0, phase: st.wphase || 'setup', left: st.phase_left || 0,
                 zleft: st.zleft || 0, alive: st.zalive || 0, lure: !!lure.on,
                 tank: !!(st.tank && st.tank.length) };
      },
      sound: function (name, at, volume) {
        if (!client.audio || !at) return;
        client.audio.play(name, { volume: (volume || 1) * client.volumeAt(at) });
      }
    };

    function setMap(map) {
      var markers = (map && map.markers) || {};
      var extra = markers.extra || {};
      current.area = markers.area || '';
      current.weather = extra.weather || '';
      current.accent = extra.accent || '#e0a040';
      drops.length = 0;
      rigCtx.critters = [];
      rigs = global.Rigs ? global.Rigs.build(map, rigCtx) : [];
    }

    function notify(kind, msg) {
      if (global.Rigs && rigs.length) global.Rigs.notify(rigs, kind, msg || {}, rigCtx);
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
      rain:    { n: 200, fall: 72, size: [0.07, 2.4, 0.07], colour: '#a8c8e8', a: 0.38 },
      storm:   { n: 240, fall: 84, size: [0.07, 2.8, 0.07], colour: '#9ab8d8', a: 0.42 },
      drizzle: { n: 120, fall: 40, size: [0.05, 1.2, 0.05], colour: '#c8d8e8', a: 0.3, drift: 1.4 },
      snow:    { n: 170, fall: 8, size: [0.34, 0.34, 0.34], colour: '#ffffff', a: 0.9, drift: 1.6 },
      embers:  { n: 70, fall: -6, size: [0.22, 0.22, 0.22], colour: '#ffae4a', a: 0.95, glow: 1, drift: 2.4 },
      ash:     { n: 90, fall: 3, size: [0.2, 0.05, 0.2], colour: '#9a9490', a: 0.8, drift: 2.0, spin: 1 },
      steam:   { n: 34, fall: -4, size: [2.6, 2.0, 2.6], colour: '#e8eef2', a: 0.16, drift: 1.2, sph: 1 },
      motes:   { n: 80, fall: 0.6, size: [0.18, 0.18, 0.18], colour: '#fff2b0', a: 0.85, glow: 1, drift: 2.0 },
      moths:   { n: 40, fall: 0.2, size: [0.3, 0.06, 0.24], colour: '#e8e0c8', a: 0.9, drift: 5.0, spin: 1 },
      leaves:  { n: 70, fall: 6, size: [0.6, 0.06, 0.5], colour: '#d88a3a', a: 0.95, drift: 4.0, spin: 1 },
      dust:    { n: 60, fall: 0.3, size: [0.14, 0.14, 0.14], colour: '#e8d8b0', a: 0.55, drift: 3.0 },
      drips:   { n: 50, fall: 30, size: [0.08, 0.6, 0.08], colour: '#b8d8e8', a: 0.5 },
      spores:  { n: 90, fall: -0.4, size: [0.16, 0.16, 0.16], colour: '#9affd8', a: 0.85, glow: 1, drift: 1.2 },
      mist:    { n: 40, fall: 0.2, size: [9.0, 2.6, 9.0], colour: '#eef2f4', a: 0.1, drift: 2.2, sph: 1 },
      spray:   { n: 60, fall: 10, size: [0.12, 0.12, 0.12], colour: '#e8f6ff', a: 0.6, drift: 3.4 },
      smoke:   { n: 30, fall: -1.2, size: [7.0, 3.0, 7.0], colour: '#8a8078', a: 0.12, drift: 2.0, sph: 1 }
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
      if ((current.weather === 'rain' || current.weather === 'storm') && Math.random() < dt * 0.5) {
        client.audio.play('ll_rain', { volume: 0.5 });
      }
    }

    function drawFlash(renderer, dt) {
      // a storm lights the sky up white now and then, and the thunder
      // follows a moment later
      if (current.weather !== 'storm' && current.weather !== 'rain') return;
      flash.next -= dt;
      if (flash.next <= 0) {
        flash.next = (current.weather === 'storm' ? 6 : 16) + Math.random() * 9;
        flash.at = clock;
        flash.power = 0.6 + Math.random() * 0.4;
        notify('lightning', { power: flash.power });
        var delay = 400 + Math.random() * 1200;
        setTimeout(function () { client.audio.play('ll_thunder', { volume: 0.5 * flash.power }); }, delay);
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
        net.on('zarea', function (msg) { if (msg && msg.map) setMap(msg.map); });
        net.on('zwave', function (msg) { notify(msg && msg.on ? 'wave' : 'cleared', msg); });
        net.on('zwipe', function (msg) { notify('wipe', msg); });
        net.on('zfx', function (msg) {
          if (!msg) return;
          if (msg.k === 'lure') notify('lure', msg);
          else if (msg.k === 'roar') notify('roar', msg);
          else if (msg.k === 'scream') notify('scream', msg);
        });
        net.on('zd', function (msg) {
          var s = survival();
          var z = s && msg ? s.zombies[msg.id] : null;
          notify('kill', { id: msg && msg.id, pos: z ? z.pos : null, kind: z ? z.kind : '' });
        });
        net.on('zbar', function (msg) { notify('blast', msg); });
      },
      notify: function (kind, msg) { notify(kind, msg); },
      onMap: function (map) { setMap(map); },
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
  var buzz = K.buzz, spaced = K.spaced, clamp = K.clamp, makeStars = K.makeStars;
  var starsK = K.stars, bands = K.bands, pineK = K.pine, batK = K.bat, crowK = K.crow;

  function sky(ctx, stops, h) {
    var g = ctx.createLinearGradient(0, 0, 0, h || VH);
    stops.forEach(function (s) { g.addColorStop(s[0], s[1]); });
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, VW, h || VH);
  }

  /* One of the infected, side on, shambling: a blocky silhouette with the
     arms out in front.  ``look`` = [shirt, trousers, skin]. */
  function shambler(ctx, x, y, s, t, look, dir, seed) {
    dir = dir || 1;
    seed = seed || 0;
    var step = Math.sin(t * 4 + seed);
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s * dir, s);
    ctx.rotate(0.08 + Math.sin(t * 2 + seed) * 0.04);
    ctx.fillStyle = look[1];
    ctx.save(); ctx.translate(-4, -26); ctx.rotate(step * 0.4); ctx.fillRect(-4, 0, 8, 26); ctx.restore();
    ctx.save(); ctx.translate(4, -26); ctx.rotate(-step * 0.4); ctx.fillRect(-4, 0, 8, 26); ctx.restore();
    ctx.fillStyle = look[0];
    ctx.fillRect(-11, -52, 22, 26);
    ctx.fillStyle = look[2] || '#6fae55';
    ctx.save(); ctx.translate(8, -49); ctx.rotate(-1.45 + step * 0.12); ctx.fillRect(-4, 0, 8, 22); ctx.restore();
    ctx.save(); ctx.translate(-2, -49); ctx.rotate(-1.35 - step * 0.12); ctx.fillRect(-4, 0, 8, 22); ctx.restore();
    ctx.fillRect(-8, -68, 16, 16);
    ctx.fillStyle = '#141414';
    ctx.fillRect(2, -63, 3, 3);
    ctx.fillRect(-3, -63, 3, 3);
    ctx.fillStyle = '#5a1414';
    ctx.fillRect(0, -57, 5, 4);
    ctx.restore();
  }

  /* A row of the infected walking in, staggered, from ``x0`` toward ``x1``. */
  function shamblers(ctx, list, t, y, s, colour) {
    list.forEach(function (z) {
      var x = z.x + z.v * t;
      shambler(ctx, x, y + z.dy, s * z.s, t, z.look || [colour, '#1a1a1a', '#2a3a20'], z.dir || 1, z.p);
    });
  }

  function makeShamblers(r, n, x0, x1, v, looks) {
    var out = [];
    for (var i = 0; i < n; i++) {
      out.push({ x: between(r, x0, x1), v: between(r, v * 0.6, v), dy: between(r, -6, 6),
                 s: between(r, 0.85, 1.15), p: r() * 6, look: looks ? looks[i % looks.length] : null,
                 dir: v < 0 ? -1 : 1 });
    }
    return out;
  }

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

  /* The name in light bulbs on a marquee board: the bulbs chase round the
     edge and the letters come on one by one. */
  function marquee(ctx, t, name, x, y, w, h, board, bulb, ink, at) {
    var k = outBack(seg(t, at, at + 0.5), 1.3);
    if (k <= 0) return;
    ctx.save();
    ctx.translate(x, lerp(y + 300, y, k));
    ctx.fillStyle = board;
    roundRect(ctx, -w / 2, -h / 2, w, h, 18);
    ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.4)';
    ctx.lineWidth = 6;
    ctx.stroke();
    var n = Math.round((w + h) / 26), chase = Math.floor(t * 12);
    for (var i = 0; i < n * 2; i++) {
      var u = i / (n * 2), px, py;
      var per = 2 * (w + h), d = u * per;
      if (d < w) { px = -w / 2 + d; py = -h / 2 + 10; }
      else if (d < w + h) { px = w / 2 - 10; py = -h / 2 + (d - w); }
      else if (d < 2 * w + h) { px = w / 2 - (d - w - h); py = h / 2 - 10; }
      else { px = -w / 2 + 10; py = h / 2 - (d - 2 * w - h); }
      var lit = (i + chase) % 3 !== 0;
      ctx.fillStyle = lit ? bulb : '#4a3a20';
      ctx.beginPath(); ctx.arc(px, py, 5, 0, TAU); ctx.fill();
      if (lit) additive(ctx, function () { dot(ctx, bulb, px, py, 14, 0.35); });
    }
    var size = fitSize(ctx, name, 'bold #px ' + HEAVY, 96, w - 90, 0.08);
    ctx.font = 'bold ' + size + 'px ' + HEAVY;
    ctx.textBaseline = 'middle';
    var lay = K.layout(ctx, name, size * 0.08);
    var left = -lay.width / 2;
    for (var c = 0; c < lay.chars.length; c++) {
      var ch = lay.chars[c];
      var on = sputter(t, at + 0.4 + c * 0.05, c + 3);
      ctx.fillStyle = 'rgba(0,0,0,0.5)';
      ctx.fillText(ch.ch, left + ch.x + 3, 6);
      ctx.fillStyle = on > 0.5 ? ink : mix(ink, board, 0.7);
      ctx.fillText(ch.ch, left + ch.x, 2);
    }
    ctx.restore();
  }

  /* The name painted on, then dripping: what a place says its name with
     when the paint was not dry. */
  function dripTitle(ctx, t, name, x, y, max, paint, shadow, at, seed) {
    var size = fitSize(ctx, name, '900 #px ' + HEAVY, 110, max, 0.06);
    ctx.font = '900 ' + size + 'px ' + HEAVY;
    ctx.textBaseline = 'middle';
    var lay = K.layout(ctx, name, size * 0.06);
    var left = x - lay.width / 2;
    for (var i = 0; i < lay.chars.length; i++) {
      var c = lay.chars[i];
      var k = seg(t, at + i * 0.035, at + i * 0.035 + 0.18);
      if (k <= 0) continue;
      ctx.globalAlpha = k;
      ctx.fillStyle = shadow;
      ctx.fillText(c.ch, left + c.x + 4, y + 5);
      ctx.fillStyle = paint;
      ctx.fillText(c.ch, left + c.x, y);
      ctx.globalAlpha = 1;
      if (c.ch === ' ') continue;
      // a drip or two off the bottom of each letter, growing
      var h1 = Math.sin((i + 1) * 12.9898 + (seed || 0)) * 43758.5453;
      h1 -= Math.floor(h1);
      var run = seg(t, at + 0.3 + h1 * 0.6, at + 2.4 + h1) * (16 + h1 * 46);
      if (run > 1) {
        var dx = left + c.x + c.w * (0.25 + h1 * 0.5);
        ctx.fillRect(dx - 2.5, y + size * 0.34, 5, run);
        ctx.beginPath(); ctx.arc(dx, y + size * 0.34 + run, 4.5, 0, TAU); ctx.fill();
      }
    }
    return size;
  }

  /* The name in neon tubes: each letter stutters on in turn, then hums. */
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

  /* A plate with a stencilled name, bolted on. */
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

  var LL = {
    K: K, sky: sky, shambler: shambler, shamblers: shamblers, makeShamblers: makeShamblers,
    rainOver: rainOver, makeRain: makeRain, marquee: marquee, dripTitle: dripTitle,
    neonTitle: neonTitle, stencilPlate: stencilPlate
  };

  // ------------------------------------------------------- the places
  // (each new place's scene goes here, in the order of places.py)

  /* Starlite Drive-In: the screen flickers on out of the dark, the
     countdown leader runs, the feature starts -- a blocky giant stomping a
     city -- and between the cars in the rows below, lit from behind by the
     picture, the audience is getting up out of their seats.  Then the
     giant turns to the camera. */
  Intro.register('drivein', {
    tagline: "Tonight's feature is the end of the world. Honk if you're still alive.",
    accent: '#7ae8e0',
    cues: [[0.1, 'll_click', 0.6], [0.5, 'll_click', 0.5], [0.9, 'll_click', 0.5],
           [1.3, 'll_wind', 0.4], [2.5, 'll_movie', 0.55], [3.3, 'll_honk', 0.5]],
    shakes: [[2.62, 6, 0.4]],
    tagY: 850, tagAt: 3.0,
    setup: function (r) {
      var d = { stars: makeStars(r, 180, 0, 420), cars: [], posts: [], corn: [], zeds: [],
                motes: [] };
      for (var i = 0; i < 3; i++) {
        for (var k = 0; k < 7; k++) {
          d.cars.push({ row: i, x: 60 + k * 230 + between(r, -40, 40) + (i % 2) * 110,
                        c: ['#7ac8c8', '#e8a0b0', '#f0e0a0', '#c83a3a', '#3a5a8a'][(i * 7 + k) % 5],
                        fin: r() < 0.6 });
        }
      }
      for (i = 0; i < 40; i++) d.corn.push({ x: 1380 + between(r, 0, 240), h: between(r, 120, 220), p: r() * 6 });
      var looks = [['#1b1b1b', '#2a3a5a', '#6fae55'], ['#e890b0', '#e890b0', '#7fb069'],
                   ['#c43a32', '#c8b890', '#5f9a4c'], ['#8a1a2a', '#1b1b1b', '#86b86a'],
                   ['#3a5a8a', '#2f4f7a', '#6c9f68']];
      for (i = 0; i < 9; i++) {
        d.zeds.push({ x: between(r, 120, 1480), row: i % 3, v: between(r, -14, 14), p: r() * 6,
                      look: looks[i % looks.length], at: between(r, 0.9, 2.4) });
      }
      for (i = 0; i < 40; i++) d.motes.push({ u: r(), s: between(r, -1, 1), v: between(r, 0.05, 0.14) });
      return d;
    },
    draw: function (ctx, t, d) {
      sky(ctx, [[0, '#02030c'], [0.5, '#0a0e2a'], [0.85, '#28305a'], [1, '#3a3060']], 560);
      starsK(ctx, d.stars, t, 1);
      // the moon over the screen's shoulder
      additive(ctx, function () { dot(ctx, '#c8d0ff', 1360, 130, 140, 0.25); });
      ctx.fillStyle = '#e8ecf8';
      ctx.beginPath(); ctx.arc(1360, 130, 46, 0, TAU); ctx.fill();
      ctx.fillStyle = 'rgba(160,170,210,0.5)';
      ctx.beginPath(); ctx.arc(1346, 122, 9, 0, TAU); ctx.arc(1374, 146, 6, 0, TAU); ctx.fill();
      // the woods along the horizon, the corn on the right
      ctx.fillStyle = '#0a1210';
      for (var x = -20; x < VW + 40; x += 38) pineK(ctx, x, 540, 60 + Math.sin(x) * 20, '#0a1210', 0);
      ctx.fillRect(0, 530, VW, 380);
      // the screen: a white field on its black scaffold
      var sx0 = 330, sx1 = 1110, sy0 = 120, sy1 = 430;
      ctx.fillStyle = '#14161c';
      ctx.fillRect(sx0 - 18, sy0 - 18, sx1 - sx0 + 36, sy1 - sy0 + 160);
      for (var c = 0; c < 9; c++) ctx.fillRect(sx0 + c * 97, sy1, 6, 150);
      var on = seg(t, 0.05, 0.25) * (t < 1.2 ? sputter(t, 0.05, 3) : 1);
      var flick = 0.88 + 0.12 * Math.sin(t * 47) * Math.sin(t * 13);
      var W = sx1 - sx0, H = sy1 - sy0;
      ctx.save();
      ctx.beginPath(); ctx.rect(sx0, sy0, W, H); ctx.clip();
      if (t < 1.25) {
        // the countdown leader
        ctx.fillStyle = mix('#202020', '#d8d4c8', on * flick);
        ctx.fillRect(sx0, sy0, W, H);
        var num = 3 - Math.floor(seg(t, 0.1, 1.25) * 3);
        var sweep = (seg(t, 0.1, 1.25) * 3) % 1;
        ctx.strokeStyle = 'rgba(30,30,30,0.8)'; ctx.lineWidth = 6;
        ctx.beginPath(); ctx.arc(sx0 + W / 2, sy0 + H / 2, 120, 0, TAU); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(sx0, sy0 + H / 2); ctx.lineTo(sx1, sy0 + H / 2);
        ctx.moveTo(sx0 + W / 2, sy0); ctx.lineTo(sx0 + W / 2, sy1); ctx.stroke();
        ctx.fillStyle = 'rgba(40,40,40,0.35)';
        ctx.beginPath(); ctx.moveTo(sx0 + W / 2, sy0 + H / 2);
        ctx.arc(sx0 + W / 2, sy0 + H / 2, 116, -Math.PI / 2, -Math.PI / 2 + sweep * TAU); ctx.fill();
        if (on > 0.3) {
          ctx.fillStyle = '#1a1a1a';
          ctx.font = '900 150px ' + HEAVY; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
          ctx.fillText(String(Math.max(1, num)), sx0 + W / 2, sy0 + H / 2 + 6);
          ctx.textAlign = 'left';
        }
      } else {
        var lunge = seg(t, 2.5, 2.75);
        var g = ctx.createLinearGradient(0, sy0, 0, sy1);
        g.addColorStop(0, lunge > 0 && Math.sin(t * 30) > 0 ? '#5a0a0a' : '#101a3a');
        g.addColorStop(1, '#2a2050');
        ctx.fillStyle = g; ctx.fillRect(sx0, sy0, W, H);
        // searchlights
        ctx.fillStyle = 'rgba(200,210,255,0.16)';
        for (var s2 = 0; s2 < 3; s2++) {
          var ang = Math.sin(t * 1.1 + s2 * 2) * 0.5;
          var bx = sx0 + 140 + s2 * 250;
          ctx.save(); ctx.translate(bx, sy1); ctx.rotate(ang);
          ctx.beginPath(); ctx.moveTo(-6, 0); ctx.lineTo(6, 0); ctx.lineTo(40, -400); ctx.lineTo(-40, -400); ctx.fill();
          ctx.restore();
        }
        // the giant, stomping; then turning on the audience
        var gs = lerp(1.6, 4.6, outCubic(lunge));
        var gx = lerp(sx0 + 80 + seg(t, 1.25, 2.5) * 420, sx0 + W / 2, lunge);
        var gy = sy1 + lunge * 260;
        var step = Math.sin(t * 6);
        ctx.fillStyle = '#0c0e14';
        ctx.fillRect(gx - 14 * gs + step * 4 * gs, gy - 40 * gs, 11 * gs, 40 * gs);
        ctx.fillRect(gx + 3 * gs - step * 4 * gs, gy - 40 * gs, 11 * gs, 40 * gs);
        ctx.fillRect(gx - 20 * gs, gy - 88 * gs, 40 * gs, 50 * gs);
        ctx.fillRect(gx - 33 * gs, gy - 86 * gs + step * 10 * gs, 12 * gs, 44 * gs);
        ctx.fillRect(gx + 21 * gs, gy - 86 * gs - step * 10 * gs, 12 * gs, 44 * gs);
        ctx.fillRect(gx - 13 * gs, gy - 116 * gs, 26 * gs, 28 * gs);
        ctx.fillStyle = lunge > 0 ? '#ff3a2a' : '#ffd84a';
        ctx.fillRect(gx - 8 * gs, gy - 108 * gs, 5 * gs, 4 * gs);
        ctx.fillRect(gx + 3 * gs, gy - 108 * gs, 5 * gs, 4 * gs);
        // the city it is treading on
        ctx.fillStyle = '#06080e';
        for (var b2 = 0; b2 < 14; b2++) {
          var bw = 40 + (b2 * 37) % 30, bh = 40 + (b2 * 53) % 90;
          ctx.fillRect(sx0 + b2 * 58, sy1 - bh, bw, bh);
        }
      }
      // scratches
      if (t > 0.3 && Math.sin(t * 23) > 0.85) {
        ctx.fillStyle = 'rgba(255,255,255,0.35)';
        ctx.fillRect(sx0 + (Math.sin(t * 7) * 0.5 + 0.5) * W, sy0, 2, H);
      }
      ctx.restore();
      // the beam from the booth, dust in it
      additive(ctx, function () {
        var g2 = ctx.createLinearGradient(780, 760, 780, sy1);
        g2.addColorStop(0, 'rgba(220,235,255,' + (0.16 * on) + ')');
        g2.addColorStop(1, 'rgba(220,235,255,' + (0.03 * on) + ')');
        ctx.fillStyle = g2;
        ctx.beginPath(); ctx.moveTo(774, 760); ctx.lineTo(788, 760); ctx.lineTo(sx1 - 20, sy1);
        ctx.lineTo(sx0 + 20, sy1); ctx.closePath(); ctx.fill();
        d.motes.forEach(function (m) {
          var u = (m.u + t * m.v) % 1;
          dot(ctx, '#fff6d8', lerp(781, sx0 + W / 2 + m.s * W * 0.45, u), lerp(760, sy0 + H / 2 + m.s * H * 0.3, u),
              2, 0.6 * on);
        });
      });
      // the field: humps, speaker posts, cars, the audience getting up
      for (var row = 2; row >= 0; row--) {
        var ry = 600 + row * 100, s3 = 0.7 + row * 0.25;
        ctx.fillStyle = mix('#14161a', '#1e2026', row / 2);
        ctx.fillRect(0, ry - 8 * s3, VW, 30 * s3);
        d.cars.filter(function (q) { return q.row === row; }).forEach(function (q) {
          var x = q.x, y = ry;
          ctx.fillStyle = mix(q.c, '#0a0a10', 0.72);
          roundRect(ctx, x - 70 * s3, y - 26 * s3, 140 * s3, 26 * s3, 8 * s3); ctx.fill();
          roundRect(ctx, x - 40 * s3, y - 46 * s3, 74 * s3, 24 * s3, 10 * s3); ctx.fill();
          if (q.fin) {
            ctx.beginPath(); ctx.moveTo(x + 50 * s3, y - 24 * s3); ctx.lineTo(x + 72 * s3, y - 40 * s3);
            ctx.lineTo(x + 70 * s3, y - 24 * s3); ctx.fill();
          }
          ctx.fillStyle = 'rgba(160,190,255,' + (0.25 * on) + ')';
          ctx.fillRect(x - 36 * s3, y - 44 * s3, 66 * s3, 3 * s3);
          ctx.fillStyle = '#c42b20';
          ctx.fillRect(x + 64 * s3, y - 20 * s3, 5 * s3, 6 * s3);
        });
        ctx.fillStyle = '#2a2d33';
        for (var px = 120 + row * 60; px < VW; px += 230) {
          ctx.fillRect(px, ry - 70 * s3, 5 * s3, 70 * s3);
          ctx.fillRect(px - 8 * s3, ry - 78 * s3, 21 * s3, 10 * s3);
        }
        d.zeds.filter(function (z) { return z.row === row; }).forEach(function (z) {
          var k = seg(t, z.at, z.at + 0.7);
          if (k <= 0) return;
          var zx = z.x + z.v * (t - z.at) * 6;
          ctx.globalAlpha = k;
          LL.shambler(ctx, zx, ry - 26 * s3 * (1 - k) + 4, 2.3 * s3, t, z.look, z.v < 0 ? -1 : 1, z.p);
          ctx.globalAlpha = 1;
          // rim light from the screen
          additive(ctx, function () { dot(ctx, '#8ab0ff', zx, ry - 70 * s3, 26 * s3, 0.14 * on * k); });
        });
      }
      // the corn on the right, eyes in it
      d.corn.forEach(function (c2) {
        var sway = Math.sin(t * 1.4 + c2.p) * 8;
        ctx.strokeStyle = '#1a2410'; ctx.lineWidth = 7;
        ctx.beginPath(); ctx.moveTo(c2.x, VH); ctx.quadraticCurveTo(c2.x + sway * 0.5, VH - c2.h * 0.6,
                                                                c2.x + sway, VH - c2.h); ctx.stroke();
        ctx.fillStyle = '#3a4a1a';
        ctx.fillRect(c2.x + sway - 3, VH - c2.h - 14, 6, 16);
      });
      additive(ctx, function () {
        var blink = Math.sin(t * 2.3) > -0.8 ? 1 : 0;
        dot(ctx, '#ff3a2a', 1470, 760, 4, 0.9 * blink * seg(t, 1.6, 2.2));
        dot(ctx, '#ff3a2a', 1482, 760, 4, 0.9 * blink * seg(t, 1.6, 2.2));
        dot(ctx, '#ff3a2a', 1530, 700, 3.5, 0.8 * seg(t, 2.4, 3.0));
        dot(ctx, '#ff3a2a', 1541, 700, 3.5, 0.8 * seg(t, 2.4, 3.0));
      });
      // the glow of the picture over everything
      additive(ctx, function () { dot(ctx, '#7a9aff', 720, 300, 700, 0.08 * on * flick); });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Starlite Drive-In').toUpperCase();
      LL.marquee(ctx, t, name, 800, 640, 1120, 150, '#1a2430', '#fff2a8', '#ffd84a', 1.55);
      var k = seg(t, 2.0, 2.4);
      if (k > 0) {
        ctx.save();
        ctx.globalAlpha = k;
        ctx.fillStyle = '#f2f2e6';
        roundRect(ctx, 440, 728, 720, 46, 6); ctx.fill();
        var line = 'TONIGHT:  ATTACK OF THE BLOCK PEOPLE';
        var size = fitSize(ctx, line, 'bold #px ' + HEAVY, 28, 660, 0.1);
        ctx.font = 'bold ' + size + 'px ' + HEAVY; ctx.textBaseline = 'middle';
        ctx.fillStyle = '#1b1b1b';
        spaced(ctx, line, 800, 752, size * 0.1);
        ctx.restore();
      }
    }
  });

  /* Harrow County Zoo: the sun going down behind the monorail's track,
     parrots going over; a giraffe leans into the picture to see who has
     come, the flamingos in the pond at the front -- and then the infected
     come through the turnstiles and the flamingos go up all at once. */
  Intro.register('zoo', {
    tagline: 'Please do not feed the infected.',
    accent: '#f2a868',
    cues: [[0.2, 'll_squawk', 0.6], [1.1, 'll_trumpet', 0.45], [1.7, 'll_clunk', 0.5],
           [2.3, 'll_squawk', 0.8], [2.9, 'll_lion', 0.5], [3.4, 'll_showtime', 0.35]],
    shakes: [[1.72, 5, 0.3]],
    tagY: 846, tagAt: 2.6,
    setup: function (r) {
      var d = { birds: [], flam: [], trees: [], zeds: [], clouds: [] };
      for (var i = 0; i < 9; i++) {
        d.birds.push({ x: between(r, -400, 200), y: between(r, 120, 320), v: between(r, 160, 260), p: r() * 6,
                       c: ['#e83a3a', '#3a7ac8', '#f2c83a', '#3ab85a'][i % 4] });
      }
      for (i = 0; i < 9; i++) d.flam.push({ x: between(r, 420, 1180), y: between(r, 760, 800), p: r() * 6, s: between(r, 0.8, 1.1) });
      for (i = 0; i < 12; i++) d.trees.push({ x: between(r, -40, VW + 40), h: between(r, 90, 170), p: r() * 6 });
      var looks = [['#b8a070', '#6a5a3a', '#6fae55'], ['#3ab0b0', '#e8e0c8', '#7fb069'],
                   ['#d8a050', '#d8a050', '#5f9a4c'], ['#3aa0a0', '#3aa0a0', '#86b86a']];
      for (i = 0; i < 7; i++) d.zeds.push({ x: 560 + i * 80 + between(r, -20, 20), p: r() * 6, look: looks[i % 4],
                                            at: 1.7 + i * 0.12 });
      for (i = 0; i < 5; i++) d.clouds.push([between(r, 0, VW + 600), between(r, 140, 360), between(r, 220, 520),
                                             between(r, 6, 14), between(r, 4, 9)]);
      return d;
    },
    draw: function (ctx, t, d) {
      sky(ctx, [[0, '#2a3a7a'], [0.45, '#8a5a8a'], [0.75, '#e88a5a'], [1, '#f2c07a']], 640);
      // the sun, low and huge, behind everything
      additive(ctx, function () { dot(ctx, '#ffb070', 980, 560, 520, 0.4, 340); });
      ctx.fillStyle = '#ffd890';
      ctx.beginPath(); ctx.arc(980, 560 + t * 6, 120, 0, TAU); ctx.fill();
      bands(ctx, d.clouds, t, 'rgba(140,70,110,0.55)');
      // the far trees, the monorail's stilts and track, the stalled train
      ctx.fillStyle = '#3a2a3a';
      d.trees.forEach(function (tr) {
        ctx.beginPath(); ctx.arc(tr.x, 640 - tr.h * 0.5, tr.h * 0.42, 0, TAU); ctx.fill();
        ctx.fillRect(tr.x - 6, 640 - tr.h * 0.5, 12, tr.h * 0.5);
      });
      ctx.fillRect(0, 600, VW, 60);
      ctx.fillStyle = '#2a1e2e';
      for (var sx = 40; sx < VW; sx += 170) ctx.fillRect(sx, 420, 16, 220);
      ctx.fillRect(0, 404, VW, 22);
      ctx.fillRect(0, 398, VW, 6);
      ctx.fillStyle = '#3a2a3e';
      roundRect(ctx, 260, 330, 330, 74, 18); ctx.fill();
      roundRect(ctx, 600, 330, 330, 74, 18); ctx.fill();
      ctx.fillStyle = 'rgba(255,210,140,0.5)';
      for (var w = 0; w < 10; w++) ctx.fillRect(282 + w * 64 + (w > 4 ? 20 : 0), 346, 40, 22);
      // the beacon on the train
      var blink = Math.sin(t * 9) > 0 ? 1 : 0.2;
      additive(ctx, function () { dot(ctx, '#ff8a2a', 760, 322, 30, 0.6 * blink); });
      // parrots across the sky
      d.birds.forEach(function (b) {
        var x = b.x + b.v * t, y = b.y + Math.sin(t * 3 + b.p) * 18;
        var flap = Math.sin(t * 16 + b.p);
        ctx.fillStyle = b.c;
        ctx.beginPath(); ctx.moveTo(x - 14, y - flap * 10); ctx.lineTo(x, y); ctx.lineTo(x + 14, y - flap * 10);
        ctx.lineTo(x, y + 5); ctx.closePath(); ctx.fill();
        ctx.fillRect(x - 3, y - 2, 12, 5);
      });
      // the ground, the pond, the flamingos
      var g = ctx.createLinearGradient(0, 640, 0, VH);
      g.addColorStop(0, '#5a4a3a'); g.addColorStop(1, '#2a2018');
      ctx.fillStyle = g; ctx.fillRect(0, 640, VW, VH - 640);
      ctx.fillStyle = '#6a8ab0';
      ctx.beginPath(); ctx.ellipse(800, 790, 470, 70, 0, 0, TAU); ctx.fill();
      ctx.fillStyle = 'rgba(255,200,140,0.35)';
      ctx.fillRect(560, 784, 480, 6);
      var scatter = seg(t, 2.2, 3.4);
      d.flam.forEach(function (f, i) {
        var up = scatter * (1 + (i % 3) * 0.3);
        var x = f.x + up * (i % 2 ? 260 : -260), y = f.y - up * 420;
        ctx.save(); ctx.translate(x, y); ctx.scale(f.s, f.s);
        ctx.fillStyle = '#f28aa0';
        if (up < 0.05) {
          ctx.fillRect(-2, -60, 4, 60);
          ctx.beginPath(); ctx.ellipse(0, -66, 22, 12, 0, 0, TAU); ctx.fill();
          ctx.strokeStyle = '#f28aa0'; ctx.lineWidth = 5;
          ctx.beginPath(); ctx.moveTo(14, -70); ctx.quadraticCurveTo(30, -110 + Math.sin(t * 2 + f.p) * 6, 18, -118); ctx.stroke();
          ctx.fillStyle = '#1a1a1a'; ctx.fillRect(18, -122, 10, 5);
        } else {
          var flap = Math.sin(t * 20 + f.p) * 26;
          ctx.beginPath(); ctx.ellipse(0, 0, 22, 10, 0, 0, TAU); ctx.fill();
          ctx.beginPath(); ctx.moveTo(-6, 0); ctx.lineTo(-30, -flap); ctx.lineTo(10, 0); ctx.fill();
          ctx.beginPath(); ctx.moveTo(-6, 0); ctx.lineTo(-30, flap * 0.6); ctx.lineTo(10, 0); ctx.fill();
          ctx.fillRect(20, -2, 26, 4);
        }
        ctx.restore();
      });
      // the infected through the turnstiles at the front
      d.zeds.forEach(function (z, i) {
        var k = seg(t, z.at, z.at + 0.5);
        if (k <= 0) return;
        ctx.globalAlpha = k;
        LL.shambler(ctx, z.x + (t - z.at) * 20 * (i % 2 ? 1 : -0.6), 900 - 40 * k + 60, 3.2, t, z.look, i % 2 ? 1 : -1, z.p);
        ctx.globalAlpha = 1;
      });
      ctx.fillStyle = '#1e1a1a';
      for (var ts = 0; ts < 6; ts++) ctx.fillRect(470 + ts * 130, 836, 16, 64);
      ctx.fillRect(440, 832, 760, 10);
      // the giraffe leaning in from the right to look
      var lean = outBack(seg(t, 0.9, 1.7), 1.3);
      if (lean > 0) {
        ctx.save();
        ctx.translate(1600 + 60 - lean * 300, 900);
        ctx.rotate(-0.35 + lean * 0.12 + Math.sin(t * 1.2) * 0.02);
        ctx.fillStyle = '#e8b858';
        ctx.fillRect(-26, -640, 52, 640);
        ctx.fillStyle = '#8a5a2a';
        for (var sp = 0; sp < 8; sp++) {
          roundRect(ctx, -22 + (sp % 2) * 16, -600 + sp * 72, 22, 30, 8); ctx.fill();
        }
        ctx.fillStyle = '#5a3a1a'; ctx.fillRect(-30, -620, 10, 560);
        ctx.save(); ctx.translate(0, -650); ctx.rotate(-1.1 + Math.sin(t * 1.6) * 0.05);
        ctx.fillStyle = '#e8b858'; roundRect(ctx, -40, -34, 150, 68, 26); ctx.fill();
        ctx.fillStyle = '#c89848'; roundRect(ctx, 80, -24, 44, 50, 18); ctx.fill();
        ctx.fillStyle = '#5a3a1a'; ctx.fillRect(-20, -62, 8, 30); ctx.fillRect(4, -62, 8, 30);
        ctx.fillStyle = '#2a1a0a'; ctx.beginPath(); ctx.arc(-16, -64, 7, 0, TAU); ctx.arc(8, -64, 7, 0, TAU); ctx.fill();
        var blinkEye = Math.sin(t * 2.7) > 0.95 ? 0.2 : 1;
        ctx.fillStyle = '#141414'; ctx.fillRect(34, -14, 12, 12 * blinkEye);
        ctx.restore();
        ctx.restore();
      }
      // the elephant's trunk up at the left edge, trumpeting
      var tr = seg(t, 1.0, 1.4);
      if (tr > 0) {
        ctx.fillStyle = '#5a5458';
        ctx.beginPath(); ctx.ellipse(-40, 820, 220, 200, 0, 0, TAU); ctx.fill();
        ctx.strokeStyle = '#5a5458'; ctx.lineWidth = 46; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(120, 760);
        ctx.quadraticCurveTo(220 + 20 * tr, 640, 180 + Math.sin(t * 4) * 10, 520 - 60 * tr); ctx.stroke();
        ctx.fillStyle = '#4a4448';
        ctx.beginPath(); ctx.ellipse(70, 700, 70, 110, -0.3, 0, TAU); ctx.fill();
      }
      // dust in the low sun
      additive(ctx, function () {
        for (var m = 0; m < 40; m++) {
          var mx = (m * 137 + t * 20) % VW, my = 420 + (m * 71) % 300 + Math.sin(t + m) * 10;
          dot(ctx, '#ffd890', mx, my, 2, 0.5);
        }
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Harrow County Zoo').toUpperCase();
      var k = outBack(seg(t, 1.6, 2.15), 1.4);
      if (k <= 0) return;
      ctx.save();
      ctx.translate(800, lerp(-200, 168, k));
      ctx.rotate(wobble(t, 2.15, 0.04, 9, 2.4));
      // the arch-topped board, green with cream letters, on two chains
      ctx.strokeStyle = '#3a3a3a'; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(-420, -60); ctx.lineTo(-440, -260); ctx.moveTo(420, -60); ctx.lineTo(440, -260); ctx.stroke();
      ctx.fillStyle = '#2e6a3e';
      ctx.beginPath(); ctx.moveTo(-480, 70); ctx.lineTo(-480, -40); ctx.quadraticCurveTo(0, -130, 480, -40);
      ctx.lineTo(480, 70); ctx.closePath(); ctx.fill();
      ctx.strokeStyle = '#f2e8d2'; ctx.lineWidth = 6; ctx.stroke();
      var size = fitSize(ctx, name, '900 #px ' + HEAVY, 84, 860, 0.07);
      ctx.font = '900 ' + size + 'px ' + HEAVY; ctx.textBaseline = 'middle';
      ctx.fillStyle = '#1a3a22';
      var lay = spaced(ctx, name, 4, 16, size * 0.07);
      ctx.fillStyle = '#f2e8d2';
      spaced(ctx, name, 0, 12, size * 0.07);
      // a monkey hanging off the last letter, a parrot on the first
      var mx = lay.left + lay.width - 10, swing = Math.sin(t * 3) * 0.3;
      ctx.save(); ctx.translate(mx, 40); ctx.rotate(swing);
      ctx.strokeStyle = '#5a3a22'; ctx.lineWidth = 7;
      ctx.beginPath(); ctx.moveTo(0, -10); ctx.lineTo(0, 30); ctx.stroke();
      ctx.fillStyle = '#5a3a22'; ctx.beginPath(); ctx.ellipse(0, 50, 16, 22, 0, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.arc(0, 22, 13, 0, TAU); ctx.fill();
      ctx.fillStyle = '#c8a070'; ctx.beginPath(); ctx.arc(0, 25, 8, 0, TAU); ctx.fill();
      ctx.restore();
      var px = lay.left + 20;
      ctx.fillStyle = '#e83a3a'; ctx.beginPath(); ctx.ellipse(px, -48, 12, 18, 0.3, 0, TAU); ctx.fill();
      ctx.fillStyle = '#3a7ac8'; ctx.fillRect(px - 12, -38, 8, 22);
      ctx.fillStyle = '#f2c83a'; ctx.fillRect(px + 6, -64, 8, 6);
      ctx.restore();
    }
  });

  /* Harrow Point Aquarium: the headland in the storm, the Great Hall
     lit blue with the whale's bones hung inside it, the sea throwing
     itself at the cliff -- and in the lightning, people walking up out of
     the surf who should not be. */
  Intro.register('aquarium', {
    tagline: 'The sharks are the least of it.',
    accent: '#4ac8e8',
    cues: [[0.2, 'll_rain', 0.6], [0.75, 'll_thunder', 0.7], [1.5, 'll_splash', 0.6],
           [2.55, 'll_thunder', 0.8], [3.2, 'll_gull', 0.5]],
    shakes: [[0.78, 6, 0.35], [2.58, 8, 0.4]],
    tagY: 850, tagAt: 2.7,
    setup: function (r) {
      var d = { rain: LL.makeRain(r, 170), waves: [], zeds: [], bubbles: [] };
      for (var i = 0; i < 6; i++) d.waves.push({ y: 640 + i * 34, p: r() * 6, a: between(r, 10, 22) });
      var looks = [['#1a1d24', '#1a1d24', '#6fae55'], ['#f2c83a', '#3a5a8a', '#7fb069'],
                   ['#e8c81a', '#e8c81a', '#5f9a4c'], ['#2a8a9a', '#e8e0c8', '#86b86a']];
      for (i = 0; i < 6; i++) d.zeds.push({ x: 120 + i * 90 + between(r, -20, 20), p: r() * 6, look: looks[i % 4],
                                            at: 1.2 + i * 0.18 });
      for (i = 0; i < 30; i++) d.bubbles.push({ x: between(r, 320, 1280), s: between(r, 3, 9), v: between(r, 40, 90), p: r() });
      return d;
    },
    draw: function (ctx, t, d) {
      var flash = Math.max(Math.exp(-Math.pow((t - 0.8) * 9, 2)), Math.exp(-Math.pow((t - 2.6) * 7, 2)));
      sky(ctx, [[0, mix('#03060c', '#8a9ab8', flash * 0.6)], [0.6, mix('#0c1a26', '#5a6a8a', flash * 0.5)],
                [1, '#16303a']], 600);
      if (flash > 0.3) {
        ctx.strokeStyle = 'rgba(230,240,255,' + flash + ')'; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.moveTo(300, 0);
        [[320, 90], [280, 180], [340, 260], [300, 360], [330, 470]].forEach(function (p) { ctx.lineTo(p[0], p[1]); });
        ctx.stroke();
      }
      // the sea, heaving
      ctx.fillStyle = '#0e2a34'; ctx.fillRect(0, 560, VW, 340);
      d.waves.forEach(function (w, i) {
        ctx.fillStyle = mix('#1a4a5a', '#0e2a34', i / 6);
        ctx.beginPath(); ctx.moveTo(0, VH);
        for (var x = 0; x <= 900; x += 30) ctx.lineTo(x, w.y + Math.sin(x * 0.012 + t * 2 + w.p) * w.a);
        ctx.lineTo(900, VH); ctx.closePath(); ctx.fill();
      });
      // the headland and the cliff
      ctx.fillStyle = '#1a1e22';
      ctx.beginPath(); ctx.moveTo(700, VH); ctx.lineTo(760, 600); ctx.lineTo(820, 560); ctx.lineTo(VW, 540);
      ctx.lineTo(VW, VH); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#262c32';
      ctx.fillRect(820, 548, 780, 16);
      // the surf at the cliff's foot
      for (var k = 0; k < 4; k++) {
        var u = (t * 0.7 + k * 0.25) % 1;
        ctx.fillStyle = 'rgba(230,245,250,' + (0.7 * (1 - u)) + ')';
        ctx.beginPath(); ctx.ellipse(740 + k * 14, 700 - u * 120, 50 + u * 60, 18 + u * 30, -0.3, 0, TAU); ctx.fill();
      }
      // the Great Hall: glass, lit blue, the whale's bones inside
      var gx = 960, gy = 300, gw = 460, gh = 248;
      ctx.fillStyle = '#0a1a26'; ctx.fillRect(gx - 10, gy - 10, gw + 20, gh + 18);
      var g = ctx.createLinearGradient(0, gy, 0, gy + gh);
      g.addColorStop(0, '#1a5a7a'); g.addColorStop(1, '#3ab8d8');
      ctx.fillStyle = g; ctx.fillRect(gx, gy, gw, gh);
      ctx.strokeStyle = '#0a1a26'; ctx.lineWidth = 4;
      for (var c = 1; c < 8; c++) { ctx.beginPath(); ctx.moveTo(gx + c * gw / 8, gy); ctx.lineTo(gx + c * gw / 8, gy + gh); ctx.stroke(); }
      for (c = 1; c < 4; c++) { ctx.beginPath(); ctx.moveTo(gx, gy + c * gh / 4); ctx.lineTo(gx + gw, gy + c * gh / 4); ctx.stroke(); }
      var sway = Math.sin(t * 0.8) * 4;
      ctx.fillStyle = '#e8e0cc';
      for (var v = 0; v < 22; v++) {
        var vx = gx + 60 + v * 16, vy = gy + 90 + Math.sin(v * 0.3 + t) * 3 + sway * (v / 22);
        ctx.fillRect(vx, vy, 12, 10);
        if (v > 2 && v < 13) { ctx.fillRect(vx + 3, vy + 10, 4, 34 - Math.abs(v - 7) * 2); }
      }
      ctx.fillRect(gx + 18, gy + 82, 44, 24);
      ctx.strokeStyle = 'rgba(30,40,50,0.6)'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(gx + 120, gy); ctx.lineTo(gx + 120, gy + 90); ctx.moveTo(gx + 330, gy); ctx.lineTo(gx + 330, gy + 92);
      ctx.stroke();
      additive(ctx, function () { dot(ctx, '#4ac8e8', gx + gw / 2, gy + gh / 2, 360, 0.18); });
      // the rain over everything, and the shark's jaws at the right edge
      LL.rainOver(ctx, d.rain, t, 'rgba(180,210,230,0.35)', 0.25);
      ctx.fillStyle = '#5a6a7a';
      ctx.beginPath(); ctx.moveTo(1460, VH); ctx.lineTo(1460, 650); ctx.quadraticCurveTo(1530, 560, 1600, 600);
      ctx.lineTo(1600, VH); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#e8e8dc';
      for (var tooth = 0; tooth < 6; tooth++) {
        ctx.beginPath(); ctx.moveTo(1466, 660 + tooth * 36); ctx.lineTo(1490, 672 + tooth * 36); ctx.lineTo(1466, 684 + tooth * 36);
        ctx.fill();
      }
      // the infected walking up out of the surf onto the rocks, in the flash
      d.zeds.forEach(function (z, i) {
        var k2 = seg(t, z.at, z.at + 0.8);
        if (k2 <= 0) return;
        var x = z.x + (t - z.at) * 26;
        var y = 760 - k2 * 70 + i * 14;
        ctx.save(); ctx.globalAlpha = 0.55 + flash * 0.45;
        LL.shambler(ctx, x, y, 2.4, t, flash > 0.3 ? z.look : ['#0a1a20', '#0a1a20', '#0a1a20'], 1, z.p);
        ctx.restore();
        ctx.fillStyle = 'rgba(230,245,250,0.5)';
        ctx.fillRect(x - 26, y - 6, 52, 6);
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Harrow Point Aquarium').toUpperCase();
      var k = seg(t, 1.5, 2.1);
      if (k <= 0) return;
      ctx.save();
      ctx.globalAlpha = k;
      var y = 214 + Math.sin(t * 1.4) * 4;
      LL.neonTitle(ctx, t, name, 760, y, 1100, '#6ae8ff', 1.5, 0.05);
      additive(ctx, function () {
        d.bubbles.forEach(function (bb) {
          var u = (t * 0.5 + bb.p) % 1;
          ctx.strokeStyle = 'rgba(160,240,255,' + (0.7 * (1 - u)) + ')'; ctx.lineWidth = 2;
          ctx.beginPath(); ctx.arc(bb.x - 160 + Math.sin(t * 2 + bb.p * 9) * 8, y + 60 - u * 140, bb.s, 0, TAU); ctx.stroke();
        });
      });
      ctx.restore();
    }
  });

  /* Silver Screen Studios: searchlights over the lot, the studio's name on
     the hill, the western street's fronts -- the clapperboard comes down
     and snaps, and the cast comes down the street in costume. */
  Intro.register('backlot', {
    tagline: 'Nobody ever yelled cut.',
    accent: '#ffd84a',
    cues: [[0.2, 'll_wind', 0.4], [1.25, 'll_clunk', 0.9], [1.4, 'll_pyro', 0.4], [2.7, 'll_boom', 0.5]],
    shakes: [[1.28, 5, 0.25], [2.72, 6, 0.3]],
    tagY: 850, tagAt: 2.6,
    setup: function (r) {
      var d = { stars: makeStars(r, 140, 0, 360), zeds: [], windows: [] };
      var looks = [['#a8784a', '#3a5a8a', '#6fae55', 'cowboy'], ['#9aa0a6', '#7a8086', '#7fb069', 'knight'],
                   ['#f2f2f2', '#f2f2f2', '#5f9a4c', 'astro'], ['#f2f2ee', '#2a2a3a', '#86b86a', 'pirate'],
                   ['#1a1a1e', '#1a1a1e', '#1a1a1e', 'ape']];
      for (var i = 0; i < 8; i++) {
        d.zeds.push({ x: 560 + (i % 4) * 150 + between(r, -40, 40), row: Math.floor(i / 4), p: r() * 6,
                      look: looks[i % looks.length], at: 1.5 + i * 0.12 });
      }
      for (i = 0; i < 40; i++) d.windows.push([between(r, 1060, 1580), between(r, 300, 560), r() < 0.5]);
      return d;
    },
    draw: function (ctx, t, d) {
      sky(ctx, [[0, '#050814'], [0.6, '#1a1a3a'], [1, '#3a2a4a']], 600);
      starsK(ctx, d.stars, t, 0.9);
      // the searchlights crossing over the lot
      additive(ctx, function () {
        [[420, 0.45], [1180, -0.4]].forEach(function (sl, i) {
          var ang = sl[1] + Math.sin(t * 0.8 + i * 2) * 0.35;
          ctx.save(); ctx.translate(sl[0], 600); ctx.rotate(ang);
          var g = ctx.createLinearGradient(0, 0, 0, -700);
          g.addColorStop(0, 'rgba(230,235,255,0.35)'); g.addColorStop(1, 'rgba(230,235,255,0)');
          ctx.fillStyle = g;
          ctx.beginPath(); ctx.moveTo(-8, 0); ctx.lineTo(8, 0); ctx.lineTo(70, -700); ctx.lineTo(-70, -700); ctx.fill();
          ctx.restore();
        });
      });
      // the hill and the letters on it
      ctx.fillStyle = '#141a14';
      ctx.beginPath(); ctx.moveTo(0, 490); ctx.quadraticCurveTo(400, 400, 800, 440); ctx.quadraticCurveTo(1200, 470, VW, 410);
      ctx.lineTo(VW, 600); ctx.lineTo(0, 600); ctx.fill();
      ctx.font = 'bold 34px ' + HEAVY; ctx.textBaseline = 'middle';
      ctx.fillStyle = '#e8e8e0';
      spaced(ctx, 'HARROW STUDIOS', 800, 432, 14);
      // the western fronts down the left, New York down the right
      for (var k = 0; k < 5; k++) {
        var x = 40 + k * 104, h = 190 + (k % 3) * 30;
        ctx.fillStyle = ['#3a2418', '#4a2e1e', '#2e1c12'][k % 3];
        ctx.fillRect(x, 600 - h, 96, h);
        ctx.fillRect(x + 18, 600 - h - 24, 60, 26);
        ctx.fillStyle = 'rgba(255,200,120,0.55)';
        ctx.fillRect(x + 12, 600 - h + 50, 22, 26); ctx.fillRect(x + 62, 600 - h + 50, 22, 26);
      }
      // the end front is open at the back: the scaffold shows
      ctx.strokeStyle = '#2a1a12'; ctx.lineWidth = 4;
      for (var sc = 0; sc < 4; sc++) {
        ctx.beginPath(); ctx.moveTo(560 + sc * 20, 600); ctx.lineTo(560 + sc * 20, 390); ctx.stroke();
      }
      ctx.beginPath(); ctx.moveTo(560, 600); ctx.lineTo(620, 420); ctx.moveTo(620, 600); ctx.lineTo(560, 440); ctx.stroke();
      ctx.fillStyle = '#1a1a22';
      ctx.fillRect(1040, 280, 560, 320);
      d.windows.forEach(function (w) {
        ctx.fillStyle = w[2] ? 'rgba(255,220,150,0.7)' : 'rgba(40,40,60,0.9)';
        ctx.fillRect(w[0], w[1], 16, 20);
      });
      // the street, dust over it
      var g2 = ctx.createLinearGradient(0, 600, 0, VH);
      g2.addColorStop(0, '#6a5038'); g2.addColorStop(1, '#2a1e14');
      ctx.fillStyle = g2; ctx.fillRect(0, 600, VW, 300);
      additive(ctx, function () { dot(ctx, '#ffd8a0', 800, 640, 500, 0.12, 60); });
      // the cast coming down the street, in costume
      d.zeds.forEach(function (z) {
        var k2 = seg(t, z.at, z.at + 0.6);
        if (k2 <= 0) return;
        var x = z.x + Math.sin(t + z.p) * 6, y = 680 + z.row * 110 + (t - z.at) * 30;
        var s = 2.2 + z.row * 0.9;
        ctx.save(); ctx.globalAlpha = k2;
        LL.shambler(ctx, x, y, s, t, z.look, z.x < 800 ? 1 : -1, z.p);
        var hx = x + (z.x < 800 ? 1 : -1) * 0 * s, hy = y - 68 * s;
        if (z.look[3] === 'cowboy') { ctx.fillStyle = '#5a3a22'; ctx.fillRect(hx - 14 * s, hy - 2 * s, 28 * s, 3 * s); ctx.fillRect(hx - 8 * s, hy - 10 * s, 16 * s, 9 * s); }
        if (z.look[3] === 'knight') { ctx.fillStyle = '#9aa0a6'; ctx.fillRect(hx - 9 * s, hy - 2 * s, 18 * s, 18 * s); ctx.fillStyle = '#141414'; ctx.fillRect(hx - 6 * s, hy + 6 * s, 12 * s, 2 * s); ctx.fillStyle = '#c43a32'; ctx.fillRect(hx - 1.5 * s, hy - 8 * s, 3 * s, 7 * s); }
        if (z.look[3] === 'astro') { ctx.strokeStyle = 'rgba(200,230,255,0.8)'; ctx.lineWidth = 2 * s; ctx.beginPath(); ctx.arc(hx, hy + 8 * s, 13 * s, 0, TAU); ctx.stroke(); }
        if (z.look[3] === 'pirate') { ctx.fillStyle = '#1a1a1a'; ctx.beginPath(); ctx.moveTo(hx - 13 * s, hy + 1 * s); ctx.lineTo(hx, hy - 9 * s); ctx.lineTo(hx + 13 * s, hy + 1 * s); ctx.fill(); }
        ctx.restore();
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Silver Screen Studios').toUpperCase();
      var k = outBack(seg(t, 0.55, 1.0), 1.3);
      if (k <= 0) return;
      ctx.save();
      ctx.translate(800, lerp(-200, 236, k));
      ctx.scale(0.86, 0.86);
      ctx.rotate(-0.03 + wobble(t, 1.0, 0.02, 9, 2));
      // the slate: the board, the chalk, the clapper stick over it
      ctx.fillStyle = '#1a1a1a';
      roundRect(ctx, -380, -40, 760, 170, 10); ctx.fill();
      ctx.strokeStyle = '#e8e8e0'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(-370, 70); ctx.lineTo(370, 70); ctx.moveTo(-120, 70); ctx.lineTo(-120, 125);
      ctx.moveTo(140, 70); ctx.lineTo(140, 125); ctx.stroke();
      var size = fitSize(ctx, name, 'bold #px ' + HEAVY, 64, 700, 0.06);
      ctx.font = 'bold ' + size + 'px ' + HEAVY; ctx.textBaseline = 'middle';
      ctx.fillStyle = '#f2f2ea';
      spaced(ctx, name, 0, 16, size * 0.06);
      ctx.font = 'bold 20px ' + HEAVY;
      spaced(ctx, 'SCENE  99', -245, 98, 3);
      spaced(ctx, 'TAKE  ' + (run.info.attempt || 1), 10, 98, 3);
      spaced(ctx, 'NIGHT EXT.', 255, 98, 3);
      var open = t < 1.25 ? 0.5 * (1 - seg(t, 1.05, 1.25)) : 0;
      ctx.save(); ctx.translate(-380, -44); ctx.rotate(-open);
      ctx.fillStyle = '#1a1a1a'; ctx.fillRect(0, -42, 760, 40);
      for (var st = 0; st < 9; st++) {
        ctx.fillStyle = '#f2f2ea';
        ctx.beginPath(); ctx.moveTo(st * 86 + 10, -42); ctx.lineTo(st * 86 + 50, -42); ctx.lineTo(st * 86 + 30, -2);
        ctx.lineTo(st * 86 - 10, -2); ctx.closePath(); ctx.fill();
      }
      ctx.restore();
      if (t > 1.25 && t < 1.6) {
        ctx.font = '900 54px ' + HEAVY; ctx.fillStyle = '#ffd84a';
        spaced(ctx, 'ACTION!', 0, -110, 6);
      }
      ctx.restore();
    }
  });

  /* Harrow County Fair: the sun going down behind the Ferris wheel, its
     lights coming on round the rim and along the strings over the midway;
     the high striker in front sends its puck up and rings the bell -- and
     out of the corn in the foreground the county comes shambling, straw
     hats and all.  The name comes in on a first-prize rosette. */
  Intro.register('fair', {
    tagline: 'Last night of the fair. Keep your arms inside the ride.',
    accent: '#ff8a5a',
    cues: [[0.1, 'll_wind', 0.4], [0.7, 'll_click', 0.5], [0.95, 'll_click', 0.4], [1.72, 'll_ding', 0.8],
           [2.6, 'll_moo', 0.5]],
    shakes: [[1.72, 3, 0.2]],
    tagY: 850, tagAt: 2.6,
    setup: function (r) {
      var d = { stars: makeStars(r, 90, 0, 300), corn: [], zeds: [], tents: [] };
      for (var i = 0; i < 90; i++) {
        d.corn.push({ x: between(r, -20, VW + 20), h: between(r, 110, 190), p: r() * 6, row: i % 2 });
      }
      var looks = [['#b8382e', '#3a5a8a', '#6fae55', 'straw'], ['#f2ece0', '#2a5a3a', '#7fb069', 'cap'],
                   ['#c43a32', '#1b1b1b', '#5f9a4c', ''], ['#e8e0cc', '#2a3a5a', '#86b86a', 'bun'],
                   ['#3a5a8a', '#2f4f7a', '#6c9f68', 'cowboy'], ['#f2b0b0', '#f2b0b0', '#f2b0b0', 'pig']];
      for (i = 0; i < 7; i++) {
        d.zeds.push({ x: 420 + i * 175 + between(r, -40, 40), p: r() * 6, look: looks[(i * 5) % looks.length],
                      at: 1.1 + i * 0.16 + r() * 0.2, s: between(r, 2.5, 3.0) });
      }
      for (i = 0; i < 6; i++) {
        d.tents.push({ x: 40 + i * 150 + between(r, -20, 20), w: between(r, 100, 140), h: between(r, 70, 110),
                       c: ['#c43a32', '#3a7ac8', '#e8b83a', '#5aa86a'][i % 4] });
      }
      return d;
    },
    draw: function (ctx, t, d) {
      var dusk = seg(t, 0, 3);
      sky(ctx, [[0, mix('#2a2a5a', '#14143a', dusk)], [0.55, mix('#c8586a', '#7a3a6a', dusk)],
                [0.85, '#f2985a'], [1, '#ffc870']], 600);
      starsK(ctx, d.stars, t, dusk * 0.8);
      // the sun going down behind the tree line
      additive(ctx, function () { dot(ctx, '#ffb060', 560, 570, 340, 0.35); });
      ctx.fillStyle = '#ffd890';
      ctx.beginPath(); ctx.arc(560, 572 + dusk * 26, 74, Math.PI, 0); ctx.fill();
      ctx.fillStyle = '#2a1e2e';
      for (var x = -20; x < VW + 40; x += 34) pineK(ctx, x, 580, 46 + Math.sin(x * 0.7) * 16, '#2a1e2e', 0);
      ctx.fillRect(0, 574, VW, 340);
      // the midway's tents along the horizon, striped
      d.tents.forEach(function (tn) {
        ctx.save();
        ctx.beginPath(); ctx.moveTo(tn.x - tn.w / 2, 600); ctx.lineTo(tn.x, 600 - tn.h); ctx.lineTo(tn.x + tn.w / 2, 600);
        ctx.closePath(); ctx.clip();
        for (var st = 0; st < 8; st++) {
          ctx.fillStyle = st % 2 ? '#f2ece0' : tn.c;
          ctx.fillRect(tn.x - tn.w / 2 + st * tn.w / 8, 600 - tn.h, tn.w / 8 + 1, tn.h);
        }
        ctx.fillStyle = 'rgba(40,20,50,' + (0.35 + dusk * 0.35) + ')';
        ctx.fillRect(tn.x - tn.w / 2, 600 - tn.h, tn.w, tn.h);
        ctx.restore();
        ctx.fillStyle = '#2a1e2e'; ctx.fillRect(tn.x - 1, 600 - tn.h - 14, 2, 14);
      });
      // the Ferris wheel: legs, rim, spokes, the gondolas hanging level
      var wx = 1180, wy = 300, R = 220, turn = t * 0.14;
      ctx.strokeStyle = '#1e1626'; ctx.lineWidth = 12;
      ctx.beginPath(); ctx.moveTo(wx - 140, 640); ctx.lineTo(wx, wy); ctx.lineTo(wx + 140, 640); ctx.stroke();
      ctx.lineWidth = 8;
      ctx.beginPath(); ctx.arc(wx, wy, R, 0, TAU); ctx.stroke();
      ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(wx, wy, R - 26, 0, TAU); ctx.stroke();
      for (var sp = 0; sp < 16; sp++) {
        var a = turn + sp / 16 * TAU;
        ctx.beginPath(); ctx.moveTo(wx, wy); ctx.lineTo(wx + Math.cos(a) * R, wy + Math.sin(a) * R); ctx.stroke();
      }
      var lightsOn = seg(t, 0.7, 1.2);
      var bulbs = ['#ff5a5a', '#ffd84a', '#5ac8ff', '#8aff7a', '#ff8ad8'];
      for (var b = 0; b < 32; b++) {
        var ab = turn + b / 32 * TAU;
        var bx = wx + Math.cos(ab) * R, by = wy + Math.sin(ab) * R;
        var lit = b / 32 < lightsOn && (b + Math.floor(t * 8)) % 4 !== 0;
        ctx.fillStyle = lit ? bulbs[b % 5] : '#3a2a3a';
        ctx.beginPath(); ctx.arc(bx, by, 5, 0, TAU); ctx.fill();
        if (lit) additive(ctx, function () { dot(ctx, bulbs[b % 5], bx, by, 16, 0.4); });
      }
      for (var g = 0; g < 12; g++) {
        var ag = turn + g / 12 * TAU;
        var gx = wx + Math.cos(ag) * R, gy = wy + Math.sin(ag) * R;
        var sw = Math.sin(t * 1.4 + g) * 0.08;
        ctx.save(); ctx.translate(gx, gy); ctx.rotate(sw);
        ctx.strokeStyle = '#1e1626'; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 16); ctx.stroke();
        ctx.fillStyle = ['#a83a3a', '#3a5aa8', '#c8a03a', '#4a8a5a'][g % 4];
        roundRect(ctx, -18, 16, 36, 26, 6); ctx.fill();
        ctx.fillStyle = lightsOn > 0.5 ? 'rgba(255,220,150,0.6)' : 'rgba(30,20,30,0.6)';
        ctx.fillRect(-12, 20, 24, 8);
        ctx.restore();
      }
      ctx.fillStyle = '#2a1e2e';
      ctx.beginPath(); ctx.arc(wx, wy, 18, 0, TAU); ctx.fill();
      // the strings of bulbs over the midway, lighting along
      for (var line = 0; line < 3; line++) {
        var x0 = -40 + line * 40, x1 = wx - 60, y0 = 150 + line * 70, sag = 90 + line * 20;
        ctx.strokeStyle = '#1e1626'; ctx.lineWidth = 2;
        ctx.beginPath();
        for (var u = 0; u <= 1.0001; u += 0.05) {
          var px = lerp(x0, x1, u), py = lerp(y0, wy + 40, u) + Math.sin(u * Math.PI) * sag;
          if (u === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
        }
        ctx.stroke();
        for (var k = 0; k < 26; k++) {
          var uu = (k + 0.5) / 26;
          var qx = lerp(x0, x1, uu), qy = lerp(y0, wy + 40, uu) + Math.sin(uu * Math.PI) * sag + 6;
          var on = seg(t, 0.9 + uu * 0.5 + line * 0.1, 1.0 + uu * 0.5 + line * 0.1);
          var c2 = ['#fff2a8', '#ffb86a', '#ff8a8a'][(k + line) % 3];
          ctx.fillStyle = on > 0.5 ? c2 : '#3a2a3a';
          ctx.beginPath(); ctx.arc(qx, qy, 4, 0, TAU); ctx.fill();
          if (on > 0.5) additive(ctx, function () { dot(ctx, c2, qx, qy, 12, 0.35); });
        }
      }
      // the field going down to the corn
      var gr = ctx.createLinearGradient(0, 600, 0, VH);
      gr.addColorStop(0, '#2a2a1e'); gr.addColorStop(1, '#141410');
      ctx.fillStyle = gr; ctx.fillRect(0, 610, VW, 300);
      // the high striker: the pole, its lights, the puck and the bell
      var hx = 190, hb = 800, ht = 290;
      ctx.fillStyle = '#a82a24'; ctx.fillRect(hx - 13, ht, 26, hb - ht);
      ctx.fillStyle = '#f2ece0';
      ctx.save(); ctx.translate(hx, (ht + hb) / 2); ctx.rotate(-Math.PI / 2);
      ctx.font = 'bold 18px ' + HEAVY; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      spaced(ctx, 'HIGH  STRIKER', 0, 0, 4);
      ctx.restore(); ctx.textAlign = 'left';
      var rise = t < 1.32 ? 0 : (t < 1.72 ? outCubic(seg(t, 1.32, 1.72)) : 1 - inOut(seg(t, 1.9, 2.6)));
      var puckY = lerp(hb - 30, ht + 30, rise);
      for (var lb = 0; lb < 12; lb++) {
        var ly = lerp(hb - 40, ht + 40, lb / 11);
        var lit2 = ly >= puckY - 4;
        ctx.fillStyle = lit2 ? '#ffd84a' : '#4a2a1a';
        ctx.fillRect(hx + 16, ly - 5, 10, 10);
        if (lit2) additive(ctx, function () { dot(ctx, '#ffb84a', hx + 21, ly, 14, 0.3); });
      }
      ctx.fillStyle = '#c8c8c8'; ctx.fillRect(hx - 20, puckY - 9, 40, 18);
      var ring = seg(t, 1.72, 1.74) * (1 - seg(t, 1.74, 2.6));
      ctx.fillStyle = ring > 0 ? mix('#e8c83a', '#fff8d8', ring) : '#c8a03a';
      ctx.beginPath(); ctx.arc(hx, ht - 4, 34, Math.PI, 0); ctx.lineTo(hx + 38, ht + 6); ctx.lineTo(hx - 38, ht + 6); ctx.fill();
      if (ring > 0) {
        additive(ctx, function () {
          dot(ctx, '#fff2a8', hx, ht - 10, 160, 0.5 * ring);
          ctx.strokeStyle = 'rgba(255,242,168,' + (0.8 * ring) + ')'; ctx.lineWidth = 4;
          for (var w2 = 0; w2 < 3; w2++) {
            var rr = 40 + ((t - 1.72) * 300 + w2 * 40) % 160;
            ctx.beginPath(); ctx.arc(hx, ht - 10, rr, -Math.PI * 0.9, -Math.PI * 0.1); ctx.stroke();
          }
        });
      }
      ctx.fillStyle = '#6a4a2a'; ctx.fillRect(hx - 60, hb - 14, 120, 24);
      // the corn: the back row, the infected getting up out of it, the front row
      function corn(row) {
        d.corn.forEach(function (c) {
          if (c.row !== row) return;
          var base = row ? 836 : 770, sway = Math.sin(t * 1.6 + c.p) * 6, ch = row ? c.h * 0.62 : c.h;
          ctx.strokeStyle = row ? '#2a3a14' : '#3a4a1a'; ctx.lineWidth = row ? 7 : 5;
          ctx.beginPath(); ctx.moveTo(c.x, base); ctx.quadraticCurveTo(c.x + sway * 0.3, base - ch * 0.5, c.x + sway, base - ch);
          ctx.stroke();
          ctx.fillStyle = row ? '#24300f' : '#34441a';
          for (var lf = 0; lf < 3; lf++) {
            var ly2 = base - ch * (0.3 + lf * 0.22), side = lf % 2 ? 1 : -1;
            ctx.beginPath(); ctx.moveTo(c.x + sway * 0.4, ly2);
            ctx.quadraticCurveTo(c.x + side * 40, ly2 - 26, c.x + side * 58 + sway, ly2 + 6);
            ctx.quadraticCurveTo(c.x + side * 30, ly2 - 8, c.x + sway * 0.4, ly2 + 4); ctx.fill();
          }
          ctx.fillStyle = '#c8a040';
          ctx.fillRect(c.x + sway - 3, base - ch - 16, 6, 18);
        });
      }
      corn(0);
      d.zeds.forEach(function (z) {
        var k2 = seg(t, z.at, z.at + 0.7);
        if (k2 <= 0) return;
        var y = lerp(940, 826, outCubic(k2)) + (t - z.at) * 6;
        var x = z.x + Math.sin(t + z.p) * 5, s = z.s, dir = z.x < 800 ? 1 : -1;
        LL.shambler(ctx, x, y, s, t, z.look, dir, z.p);
        var hx2 = x, hy = y - 68 * s;
        if (z.look[3] === 'straw') {
          ctx.fillStyle = '#e0c878'; ctx.fillRect(hx2 - 15 * s, hy - 1 * s, 30 * s, 3 * s); ctx.fillRect(hx2 - 8 * s, hy - 8 * s, 16 * s, 8 * s);
          ctx.fillStyle = '#3a5a2a'; ctx.fillRect(hx2 - 8 * s, hy - 3 * s, 16 * s, 2 * s);
        } else if (z.look[3] === 'cap') {
          ctx.fillStyle = '#2a7a3a'; ctx.fillRect(hx2 - 8 * s, hy - 4 * s, 16 * s, 5 * s); ctx.fillRect(hx2, hy - 1 * s, 13 * s * dir, 2 * s);
        } else if (z.look[3] === 'cowboy') {
          ctx.fillStyle = '#6a4a2a'; ctx.fillRect(hx2 - 14 * s, hy - 1 * s, 28 * s, 3 * s); ctx.fillRect(hx2 - 7 * s, hy - 9 * s, 14 * s, 9 * s);
        } else if (z.look[3] === 'bun') {
          ctx.fillStyle = '#c8a060'; ctx.fillRect(hx2 - 8 * s, hy - 2 * s, 16 * s, 4 * s);
          ctx.beginPath(); ctx.arc(hx2 - 6 * s * dir, hy - 4 * s, 5 * s, 0, TAU); ctx.fill();
        } else if (z.look[3] === 'pig') {
          ctx.fillStyle = '#f2b0b0'; ctx.fillRect(hx2 - 10 * s, hy - 2 * s, 20 * s, 20 * s);
          ctx.fillStyle = '#e88a8a'; ctx.fillRect(hx2 + 8 * s * dir - 3 * s, hy + 8 * s, 6 * s, 6 * s);
          ctx.fillRect(hx2 - 9 * s, hy - 7 * s, 6 * s, 6 * s); ctx.fillRect(hx2 + 3 * s, hy - 7 * s, 6 * s, 6 * s);
          ctx.fillStyle = '#141414'; ctx.fillRect(hx2 + 2 * s * dir, hy + 4 * s, 3 * s, 3 * s);
        }
      });
      corn(1);
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Harrow County Fair').toUpperCase();
      var k = outBack(seg(t, 0.45, 0.95), 1.4);
      if (k <= 0) return;
      ctx.save();
      ctx.translate(800, 250);
      ctx.scale(0.78 * k, 0.78 * k);
      ctx.rotate((1 - k) * -2.4 + wobble(t, 1.0, 0.03, 7, 3));
      // the tails, hanging and swinging
      [-1, 1].forEach(function (side) {
        ctx.save(); ctx.rotate(side * 0.22 + Math.sin(t * 2 + side) * 0.04);
        ctx.fillStyle = side < 0 ? '#2a4ac8' : '#2350b8';
        ctx.beginPath(); ctx.moveTo(-34, 60); ctx.lineTo(34, 60); ctx.lineTo(34, 330); ctx.lineTo(0, 296); ctx.lineTo(-34, 330);
        ctx.closePath(); ctx.fill();
        ctx.fillStyle = '#e8c83a'; ctx.fillRect(-34, 70, 68, 6);
        ctx.restore();
      });
      // the ruffle: blue, then gold, then the middle
      function frill(r0, r1, n, colour) {
        ctx.fillStyle = colour;
        ctx.beginPath();
        for (var i = 0; i <= n * 2; i++) {
          var a = i / (n * 2) * TAU + t * 0.2, rr = i % 2 ? r0 : r1;
          if (i === 0) ctx.moveTo(Math.cos(a) * rr, Math.sin(a) * rr); else ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr);
        }
        ctx.closePath(); ctx.fill();
      }
      frill(150, 178, 40, '#2a4ac8');
      frill(124, 140, 32, '#e8c83a');
      ctx.fillStyle = '#f2ece0';
      ctx.beginPath(); ctx.arc(0, 0, 118, 0, TAU); ctx.fill();
      ctx.strokeStyle = '#2a4ac8'; ctx.lineWidth = 6;
      ctx.beginPath(); ctx.arc(0, 0, 108, 0, TAU); ctx.stroke();
      ctx.fillStyle = '#2a4ac8';
      ctx.font = '900 44px ' + HEAVY; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.font = '900 38px ' + HEAVY;
      ctx.fillText('1ST', 0, -80);
      ctx.font = 'bold 18px ' + HEAVY;
      spaced(ctx, 'PRIZE', 0, 66, 6);
      ctx.textAlign = 'left';
      // the banner across it with the name
      var size = fitSize(ctx, name, '900 #px ' + HEAVY, 70, 820, 0.05);
      var bw = 900, bh = 104;
      ctx.fillStyle = '#a82a24';
      ctx.beginPath(); ctx.moveTo(-bw / 2 - 60, -bh / 2 + 20); ctx.lineTo(-bw / 2 + 10, -bh / 2 + 20); ctx.lineTo(-bw / 2 + 10, bh / 2 + 20);
      ctx.lineTo(-bw / 2 - 60, bh / 2 + 20); ctx.lineTo(-bw / 2 - 36, 20); ctx.closePath(); ctx.fill();
      ctx.beginPath(); ctx.moveTo(bw / 2 + 60, -bh / 2 + 20); ctx.lineTo(bw / 2 - 10, -bh / 2 + 20); ctx.lineTo(bw / 2 - 10, bh / 2 + 20);
      ctx.lineTo(bw / 2 + 60, bh / 2 + 20); ctx.lineTo(bw / 2 + 36, 20); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#c43a32';
      roundRect(ctx, -bw / 2, -bh / 2, bw, bh, 8); ctx.fill();
      ctx.strokeStyle = '#f2ece0'; ctx.lineWidth = 3;
      roundRect(ctx, -bw / 2 + 10, -bh / 2 + 10, bw - 20, bh - 20, 6); ctx.stroke();
      ctx.font = '900 ' + size + 'px ' + HEAVY; ctx.textBaseline = 'middle';
      ctx.fillStyle = 'rgba(0,0,0,0.35)';
      spaced(ctx, name, 3, 5, size * 0.05);
      ctx.fillStyle = '#f2ece0';
      spaced(ctx, name, 0, 2, size * 0.05);
      ctx.restore();
    }
  });

  /* Redwater Cranberry Bogs: a full moon over the flooded bog, the water
     red from bank to bank, mist lying on it; the windmill turning on its
     knoll, the screenhouse lit; a heron crosses the moon -- and out of the
     berries, one after another, they stand up and come wading.  The name
     goes on like a fruit-crate label. */
  Intro.register('bogs', {
    tagline: 'The water was red before any of this.',
    accent: '#e83a4a',
    cues: [[0.1, 'll_wind', 0.4], [0.5, 'll_clunk', 0.7], [1.0, 'll_heron', 0.6], [1.6, 'll_splash', 0.6],
           [2.3, 'll_splash', 0.5], [2.9, 'll_frog', 0.6]],
    shakes: [[0.62, 3, 0.15]],
    tagY: 850, tagAt: 2.6,
    setup: function (r) {
      var d = { stars: makeStars(r, 160, 0, 420), berries: [], zeds: [], mist: [], lamps: [] };
      for (var i = 0; i < 260; i++) {
        var y = 600 + Math.pow(r(), 0.7) * 300;
        d.berries.push({ x: r() * VW, y: y, s: 1 + (y - 600) / 300 * 4, c: r() < 0.6 ? '#c8243a' : '#8a1022' });
      }
      var looks = [['#b8382e', '#2a4a2a', '#6fae55'], ['#f2c81a', '#2a4a2a', '#7fb069'], ['#e8e8e0', '#e8e8e0', '#5f9a4c'],
                   ['#a8182a', '#a8182a', '#86b86a'], ['#2a3a5a', '#3a3a3a', '#6c9f68'], ['#7a5230', '#3f63a8', '#79a84e']];
      for (i = 0; i < 7; i++) {
        d.zeds.push({ x: 160 + i * 205 + between(r, -50, 50), row: i % 2, at: 1.3 + i * 0.17 + r() * 0.2, p: r() * 6,
                      look: looks[i % looks.length] });
      }
      for (i = 0; i < 8; i++) d.mist.push({ x: r() * VW, y: between(r, 560, 760), w: between(r, 300, 600), v: between(r, 8, 22) });
      for (i = 0; i < 6; i++) d.lamps.push([120 + i * 270 + between(r, -30, 30), i % 2 ? 604 : 640]);
      return d;
    },
    draw: function (ctx, t, d) {
      sky(ctx, [[0, '#050818'], [0.55, '#1a1838'], [0.9, '#4a2a48'], [1, '#6a3a4a']], 580);
      starsK(ctx, d.stars, t, 1);
      // the moon, and a heron going across it
      additive(ctx, function () { dot(ctx, '#e8e0ff', 1180, 190, 260, 0.22); });
      ctx.fillStyle = '#f2ecd8';
      ctx.beginPath(); ctx.arc(1180, 190, 92, 0, TAU); ctx.fill();
      ctx.fillStyle = 'rgba(180,170,150,0.45)';
      ctx.beginPath(); ctx.arc(1150, 170, 18, 0, TAU); ctx.arc(1210, 220, 12, 0, TAU); ctx.arc(1196, 160, 8, 0, TAU); ctx.fill();
      var hk = seg(t, 0.7, 2.4);
      if (hk > 0 && hk < 1) {
        var hx = lerp(1480, 820, hk), hy = 200 - Math.sin(hk * Math.PI) * 30, flap = Math.sin(t * 9) * 26;
        ctx.fillStyle = '#0c0a14';
        ctx.beginPath(); ctx.ellipse(hx, hy, 34, 9, -0.1, 0, TAU); ctx.fill();
        ctx.beginPath(); ctx.moveTo(hx - 10, hy); ctx.lineTo(hx + 14, hy - 4 - flap); ctx.lineTo(hx + 36, hy - 2 - flap * 0.6);
        ctx.lineTo(hx + 8, hy + 2); ctx.fill();
        ctx.beginPath(); ctx.moveTo(hx - 10, hy); ctx.lineTo(hx - 4, hy - 6 - flap); ctx.lineTo(hx + 20, hy - 4 - flap * 0.6);
        ctx.lineTo(hx + 6, hy + 2); ctx.fill();
        ctx.fillRect(hx - 56, hy - 3, 24, 4); ctx.fillRect(hx + 30, hy, 34, 3);
      }
      // the tree line, the windmill on its knoll, the screenhouse
      ctx.fillStyle = '#0c0e14';
      for (var x = -20; x < VW + 40; x += 30) pineK(ctx, x, 560, 40 + Math.sin(x * 0.37) * 14, '#0c0e14', 0);
      ctx.fillRect(0, 552, VW, 60);
      ctx.beginPath(); ctx.moveTo(180, 560); ctx.quadraticCurveTo(300, 520, 420, 560); ctx.fill();
      ctx.beginPath(); ctx.moveTo(270, 540); ctx.lineTo(282, 420); ctx.lineTo(318, 420); ctx.lineTo(330, 540); ctx.fill();
      ctx.beginPath(); ctx.moveTo(276, 424); ctx.lineTo(300, 398); ctx.lineTo(324, 424); ctx.fill();
      ctx.save(); ctx.translate(300, 430); ctx.rotate(t * 0.5);
      for (var sl = 0; sl < 4; sl++) {
        ctx.rotate(Math.PI / 2);
        ctx.fillRect(-3, 0, 6, 110);
        ctx.fillStyle = 'rgba(20,18,26,0.9)'; ctx.fillRect(4, 22, 22, 84); ctx.fillStyle = '#0c0e14';
      }
      ctx.restore();
      ctx.fillStyle = 'rgba(255,200,120,0.75)'; ctx.fillRect(296, 470, 8, 12);
      ctx.fillStyle = '#121218';
      ctx.fillRect(1240, 500, 300, 64);
      ctx.beginPath(); ctx.moveTo(1230, 502); ctx.lineTo(1390, 450); ctx.lineTo(1550, 502); ctx.fill();
      ctx.fillRect(1380, 432, 22, 22);
      for (var w = 0; w < 6; w++) {
        ctx.fillStyle = 'rgba(255,196,110,' + (0.55 + 0.2 * Math.sin(t * 3 + w)) + ')';
        ctx.fillRect(1262 + w * 46, 520, 20, 16);
      }
      // the bog: red to the horizon, the moon's road on it, the dikes
      var g = ctx.createLinearGradient(0, 560, 0, VH);
      g.addColorStop(0, '#3a0610'); g.addColorStop(0.4, '#6a0c1a'); g.addColorStop(1, '#a01a2a');
      ctx.fillStyle = g; ctx.fillRect(0, 562, VW, VH - 562);
      additive(ctx, function () {
        for (var m = 0; m < 22; m++) {
          var my = 570 + m * 14 + Math.sin(t * 2 + m) * 2, mw = 30 + m * 6 + Math.sin(t * 3 + m * 1.7) * 10;
          ctx.fillStyle = 'rgba(255,220,220,' + (0.18 - m * 0.006) + ')';
          ctx.fillRect(1180 - mw / 2 + Math.sin(t + m) * 8, my, mw, 3);
        }
      });
      ctx.fillStyle = '#1a120e';
      ctx.fillRect(0, 600, VW, 7); ctx.fillRect(0, 640, VW, 9);
      d.lamps.forEach(function (lp) {
        ctx.fillStyle = '#1a120e'; ctx.fillRect(lp[0] - 2, lp[1] - 46, 4, 46);
        additive(ctx, function () { dot(ctx, '#ffcf7a', lp[0], lp[1] - 48, 26, 0.5); });
      });
      // the boom, swinging round in an arc
      ctx.strokeStyle = '#e8a01a'; ctx.lineWidth = 6;
      ctx.beginPath(); ctx.moveTo(-20, 720); ctx.quadraticCurveTo(500, 680, 900, 712); ctx.stroke();
      // the berries on the water
      d.berries.forEach(function (b, i) {
        ctx.fillStyle = b.c;
        ctx.beginPath(); ctx.arc(b.x + Math.sin(t * 0.8 + i) * 1.5, b.y + Math.sin(t * 1.3 + i) * 0.8, b.s, 0, TAU); ctx.fill();
      });
      // the mist lying on it
      d.mist.forEach(function (m) {
        var mx = (m.x + t * m.v) % (VW + m.w) - m.w / 2;
        var mg = ctx.createRadialGradient(mx, m.y, 0, mx, m.y, m.w / 2);
        mg.addColorStop(0, 'rgba(220,220,235,0.16)'); mg.addColorStop(1, 'rgba(220,220,235,0)');
        ctx.fillStyle = mg; ctx.fillRect(mx - m.w / 2, m.y - m.w / 4, m.w, m.w / 2);
      });
      // and the infected standing up out of it, wading in
      d.zeds.forEach(function (z) {
        var k2 = seg(t, z.at, z.at + 0.8);
        if (k2 <= 0) return;
        var water = z.row ? 780 : 730, s = z.row ? 2.6 : 2.0;
        var rise = outCubic(k2);
        var y = water + 68 * s - rise * 46 * s + (t - z.at) * 6;
        var x = z.x + Math.sin(t + z.p) * 4;
        ctx.save();
        ctx.beginPath(); ctx.rect(0, 0, VW, water); ctx.clip();
        LL.shambler(ctx, x, y, s, t, z.look, z.x < 800 ? 1 : -1, z.p);
        ctx.restore();
        ctx.strokeStyle = 'rgba(255,190,190,0.5)'; ctx.lineWidth = 2;
        var rr = 14 * s + Math.sin(t * 4 + z.p) * 3;
        ctx.beginPath(); ctx.ellipse(x, water, rr, rr * 0.22, 0, 0, TAU); ctx.stroke();
      });
      // a hand, in the near water
      var hk2 = seg(t, 1.55, 2.0) * (1 - seg(t, 3.2, 3.8));
      if (hk2 > 0) {
        ctx.save();
        ctx.beginPath(); ctx.rect(0, 0, VW, 858); ctx.clip();
        var bx = 1430, by = 858 + 90 - hk2 * 120;
        ctx.fillStyle = '#6fae55';
        ctx.fillRect(bx - 12, by, 24, 120);
        ctx.fillRect(bx - 18, by - 22, 36, 26);
        for (var fg = 0; fg < 4; fg++) ctx.fillRect(bx - 17 + fg * 9.5, by - 44 + Math.sin(t * 8 + fg) * 4, 7, 24);
        ctx.fillRect(bx + 18, by - 14, 12, 7);
        ctx.restore();
        ctx.strokeStyle = 'rgba(255,190,190,0.5)'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.ellipse(bx, 858, 40 + Math.sin(t * 5) * 4, 8, 0, 0, TAU); ctx.stroke();
      }
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Redwater Cranberry Bogs').toUpperCase();
      var k = outBack(seg(t, 0.4, 0.62), 1.6);
      if (k <= 0) return;
      ctx.save();
      ctx.translate(800, 236);
      ctx.rotate(-0.02 + (1 - k) * -0.25);
      var sc = 0.78 * (1.6 - 0.6 * k);
      ctx.scale(sc, sc);
      ctx.globalAlpha = Math.min(1, k * 1.4);
      // the crate's end boards behind the label
      for (var pl = 0; pl < 3; pl++) {
        ctx.fillStyle = ['#8a6a42', '#7a5c38', '#94744a'][pl];
        ctx.fillRect(-560, -150 + pl * 100, 1120, 96);
        ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.fillRect(-560, -150 + pl * 100 + 92, 1120, 4);
        ctx.fillStyle = '#3a2a1a';
        for (var nl = 0; nl < 2; nl++) { ctx.beginPath(); ctx.arc(nl ? 530 : -530, -102 + pl * 100, 5, 0, TAU); ctx.fill(); }
      }
      // the label
      ctx.fillStyle = '#a8182a'; roundRect(ctx, -500, -120, 1000, 240, 16); ctx.fill();
      ctx.fillStyle = '#f2e6c8'; roundRect(ctx, -488, -108, 976, 216, 10); ctx.fill();
      ctx.strokeStyle = '#1a2a5a'; ctx.lineWidth = 3; roundRect(ctx, -476, -96, 952, 192, 8); ctx.stroke();
      // the medallion: berries on a navy ground, two leaves
      ctx.fillStyle = '#1a2a5a'; ctx.beginPath(); ctx.arc(-370, 0, 86, 0, TAU); ctx.fill();
      ctx.strokeStyle = '#d8b84a'; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(-370, 0, 78, 0, TAU); ctx.stroke();
      ctx.fillStyle = '#3a7a3a';
      ctx.beginPath(); ctx.ellipse(-400, -40, 34, 12, -0.6, 0, TAU); ctx.fill();
      ctx.beginPath(); ctx.ellipse(-338, -44, 30, 11, 0.7, 0, TAU); ctx.fill();
      [[-392, 6, 24], [-350, 0, 26], [-372, 34, 22], [-330, 38, 18], [-410, 40, 16]].forEach(function (b) {
        ctx.fillStyle = '#c81a2e'; ctx.beginPath(); ctx.arc(b[0], b[1], b[2], 0, TAU); ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.55)'; ctx.beginPath(); ctx.arc(b[0] - b[2] * 0.35, b[1] - b[2] * 0.35, b[2] * 0.25, 0, TAU); ctx.fill();
      });
      ctx.textBaseline = 'middle';
      ctx.font = 'bold 22px ' + HEAVY; ctx.fillStyle = '#a8182a';
      spaced(ctx, 'REDWATER  BRAND', 110, -66, 8);
      var size = fitSize(ctx, name, '900 #px ' + HEAVY, 64, 660, 0.04);
      ctx.font = '900 ' + size + 'px ' + HEAVY;
      ctx.fillStyle = 'rgba(26,42,90,0.25)'; spaced(ctx, name, 113, 5, size * 0.04);
      ctx.fillStyle = '#1a2a5a'; spaced(ctx, name, 110, 2, size * 0.04);
      ctx.font = 'bold 18px ' + HEAVY; ctx.fillStyle = '#a8182a';
      spaced(ctx, 'CHOICE  CRANBERRIES   ·   HARROW  CO.', 110, 66, 4);
      ctx.restore();
    }
  });

  /* Kettle Falls Mill: across the gorge at dusk, the falls coming over
     the dam, the mill on the far cliff with every window lit, the wheel
     turning under it, leaves coming down.  The whistle blows -- a jet of
     steam off the boiler house -- the doors open and the shift files out
     along the cliff, and below, in the river, more of them wade.  The
     name is a time card, punched out. */
  Intro.register('mill', {
    tagline: 'The whistle still blows at six. They still come.',
    accent: '#e8883a',
    cues: [[0.1, 'll_wind', 0.4], [0.3, 'll_rush', 0.5], [0.85, 'll_clunk', 0.9], [1.3, 'll_whistle', 0.7],
           [2.7, 'll_bell', 0.5]],
    shakes: [[0.86, 4, 0.15]],
    tagY: 850, tagAt: 2.6,
    setup: function (r) {
      var d = { leaves: [], trees: [], walkers: [], waders: [], windows: [] };
      for (var i = 0; i < 46; i++) {
        d.leaves.push({ x: r() * VW, y: r() * 900, v: between(r, 30, 70), s: between(r, 5, 10), p: r() * 6,
                        c: ['#c8582a', '#d8a02a', '#a83a24', '#e8c84a'][i % 4] });
      }
      for (i = 0; i < 26; i++) d.trees.push({ x: i * 64 + between(r, -20, 20), y: between(r, 300, 360), s: between(r, 26, 44),
                                              c: ['#a8482a', '#c87a2a', '#8a3a24', '#b8902a'][i % 4] });
      var looks = [['#e8e0cc', '#4a3a5a', '#6fae55'], ['#3a4a6a', '#3a4a6a', '#7fb069'], ['#5a4a3a', '#3a3a3a', '#5f9a4c'],
                   ['#8a6a4a', '#4a4a3a', '#86b86a'], ['#1a1a1e', '#2a2a2e', '#6c9f68']];
      for (i = 0; i < 9; i++) d.walkers.push({ at: 1.7 + i * 0.22, p: r() * 6, look: looks[i % looks.length] });
      for (i = 0; i < 5; i++) d.waders.push({ x: 300 + i * 260 + between(r, -40, 40), at: 1.2 + i * 0.25, p: r() * 6,
                                              look: looks[(i + 2) % looks.length] });
      for (var row = 0; row < 3; row++) {
        for (var c = 0; c < 16; c++) d.windows.push({ x: 560 + c * 46, y: 330 + row * 44, f: r() });
      }
      return d;
    },
    draw: function (ctx, t, d) {
      sky(ctx, [[0, '#24243e'], [0.45, '#6a3a52'], [0.8, '#d87a4a'], [1, '#f2a85a']], 470);
      additive(ctx, function () { dot(ctx, '#ffb060', 1180, 330, 380, 0.3); });
      // the far hills in their colours
      ctx.fillStyle = '#3a2430';
      ctx.beginPath(); ctx.moveTo(0, 380);
      for (var hx = 0; hx <= VW; hx += 80) ctx.lineTo(hx, 340 + Math.sin(hx * 0.006) * 30 + Math.sin(hx * 0.02) * 10);
      ctx.lineTo(VW, 480); ctx.lineTo(0, 480); ctx.fill();
      d.trees.forEach(function (tr) {
        ctx.fillStyle = tr.c;
        ctx.beginPath(); ctx.arc(tr.x, tr.y + 30, tr.s * 0.7, 0, TAU); ctx.fill();
        ctx.fillStyle = 'rgba(40,20,30,0.35)';
        ctx.beginPath(); ctx.arc(tr.x + tr.s * 0.25, tr.y + 36, tr.s * 0.5, 0, TAU); ctx.fill();
      });
      // the far cliff top, the mill on it, the stack
      ctx.fillStyle = '#2a2a22'; ctx.fillRect(0, 466, VW, 14);
      ctx.fillStyle = '#5a2a20'; ctx.fillRect(540, 300, 780, 168);
      ctx.fillStyle = '#3a2a2a';
      ctx.beginPath(); ctx.moveTo(530, 302); ctx.lineTo(930, 262); ctx.lineTo(1330, 302); ctx.fill();
      ctx.fillStyle = '#e8e0cc'; ctx.fillRect(914, 222, 32, 40);
      ctx.fillStyle = '#3a2a2a'; ctx.beginPath(); ctx.moveTo(908, 224); ctx.lineTo(930, 198); ctx.lineTo(952, 224); ctx.fill();
      d.windows.forEach(function (w) {
        ctx.fillStyle = 'rgba(255,' + (190 + Math.floor(w.f * 40)) + ',110,' + (0.6 + 0.3 * Math.sin(t * 2 + w.f * 9)) + ')';
        ctx.fillRect(w.x, w.y, 20, 26);
      });
      var door = seg(t, 1.6, 1.9);
      ctx.fillStyle = door > 0 ? 'rgba(255,210,140,' + (0.5 + door * 0.4) + ')' : '#2a1a14';
      ctx.fillRect(904, 424, 52, 44);
      ctx.fillStyle = '#4a2a20'; ctx.fillRect(1366, 120, 34, 350);
      ctx.fillRect(1330, 400, 110, 68);
      for (var sm = 0; sm < 7; sm++) {
        var u = (t * 0.25 + sm / 7) % 1, sr = 16 + u * 50;
        ctx.fillStyle = 'rgba(90,86,84,' + (0.5 * (1 - u)) + ')';
        ctx.beginPath(); ctx.arc(1383 + u * 120, 110 - u * 90, sr, 0, TAU); ctx.fill();
      }
      var jet = seg(t, 1.3, 1.45) * (1 - seg(t, 3.4, 4.0));
      if (jet > 0) {
        for (var js = 0; js < 10; js++) {
          var q = (t * 1.6 + js / 10) % 1, jr = 8 + q * 40;
          ctx.fillStyle = 'rgba(245,245,245,' + (0.6 * (1 - q) * jet) + ')';
          ctx.beginPath(); ctx.arc(1356 + q * 20, 392 - q * 170, jr, 0, TAU); ctx.fill();
        }
      }
      // the shift coming out along the cliff top
      d.walkers.forEach(function (w) {
        var k = seg(t, w.at, w.at + 2.0);
        if (k <= 0) return;
        LL.shambler(ctx, 930 + k * 330 - Math.min(1, (t - w.at) * 2) * 10, 466, 1.0, t, w.look, 1, w.p);
      });
      // the gorge: the far cliff face, the falls on the left, the wheel
      var cg = ctx.createLinearGradient(0, 480, 0, 650);
      cg.addColorStop(0, '#4a4440'); cg.addColorStop(1, '#2a2622');
      ctx.fillStyle = cg; ctx.fillRect(0, 480, VW, 170);
      ctx.strokeStyle = 'rgba(0,0,0,0.25)'; ctx.lineWidth = 2;
      for (var st = 0; st < 5; st++) { ctx.beginPath(); ctx.moveTo(0, 500 + st * 30); ctx.lineTo(VW, 496 + st * 30 + Math.sin(st) * 8); ctx.stroke(); }
      ctx.fillStyle = '#6a6460'; ctx.fillRect(0, 452, 230, 30);
      for (var fc = 0; fc < 9; fc++) {
        var fx = 30 + fc * 20;
        ctx.fillStyle = 'rgba(200,225,240,0.7)'; ctx.fillRect(fx, 470, 18, 180);
        for (var fs = 0; fs < 3; fs++) {
          var fu = (t * 1.3 + fs / 3 + fc * 0.17) % 1;
          ctx.fillStyle = 'rgba(255,255,255,0.8)'; ctx.fillRect(fx + 6, 470 + fu * 170, 5, 22);
        }
      }
      ctx.fillStyle = '#5a4a3a'; ctx.fillRect(230, 512, 470, 10);
      ctx.save(); ctx.translate(780, 560); ctx.rotate(-t * 0.8);
      ctx.strokeStyle = '#4a3a2a'; ctx.lineWidth = 8;
      ctx.beginPath(); ctx.arc(0, 0, 84, 0, TAU); ctx.stroke();
      for (var bk = 0; bk < 16; bk++) {
        ctx.rotate(TAU / 16);
        ctx.fillStyle = '#6a5a42'; ctx.fillRect(70, -5, 22, 10);
        if (bk % 4 === 0) { ctx.fillStyle = '#3a2a1a'; ctx.fillRect(0, -3, 84, 6); }
      }
      ctx.restore();
      ctx.fillStyle = 'rgba(170,210,230,0.6)'; ctx.fillRect(700, 514, 14, 40);
      // the river, foam on it
      var rg = ctx.createLinearGradient(0, 640, 0, VH);
      rg.addColorStop(0, '#1a3a44'); rg.addColorStop(1, '#0a1a22');
      ctx.fillStyle = rg; ctx.fillRect(0, 640, VW, VH - 640);
      for (var fm = 0; fm < 30; fm++) {
        var fy = 650 + (fm * 37) % 150, fxx = ((fm * 173) % VW + t * (60 + fm % 5 * 20)) % (VW + 100) - 50;
        ctx.fillStyle = 'rgba(230,242,248,0.35)'; ctx.fillRect(fxx, fy, 30 + (fm % 4) * 14, 3);
      }
      additive(ctx, function () { dot(ctx, '#e8f4f8', 130, 650, 160, 0.25); });
      // and in the river, wading toward us
      d.waders.forEach(function (w) {
        var k2 = seg(t, w.at, w.at + 0.8);
        if (k2 <= 0) return;
        var water = 760, sc = 2.3;
        var y = water + 68 * sc - outCubic(k2) * 46 * sc + (t - w.at) * 5;
        ctx.save(); ctx.beginPath(); ctx.rect(0, 0, VW, water); ctx.clip();
        LL.shambler(ctx, w.x + Math.sin(t + w.p) * 4, y, sc, t, w.look, w.x < 800 ? 1 : -1, w.p);
        ctx.restore();
        ctx.strokeStyle = 'rgba(220,240,248,0.5)'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.ellipse(w.x, water, 30, 6, 0, 0, TAU); ctx.stroke();
      });
      // the leaves coming down
      d.leaves.forEach(function (l) {
        var ly = (l.y + t * l.v) % 900, lx = l.x + Math.sin(t * 1.3 + l.p) * 30;
        ctx.save(); ctx.translate(lx, ly); ctx.rotate(t * 2 + l.p);
        ctx.fillStyle = l.c; ctx.fillRect(-l.s / 2, -l.s / 4, l.s, l.s / 2);
        ctx.restore();
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Kettle Falls Mill').toUpperCase();
      var k = outCubic(seg(t, 0.4, 0.82));
      if (k <= 0) return;
      ctx.save();
      ctx.translate(lerp(-700, 760, k), 226);
      ctx.rotate(-0.015);
      // the time clock's slot the card goes into
      ctx.fillStyle = '#2a2a2e'; roundRect(ctx, 330, -120, 150, 240, 12); ctx.fill();
      ctx.fillStyle = '#e8e0cc'; ctx.beginPath(); ctx.arc(405, -60, 44, 0, TAU); ctx.fill();
      ctx.strokeStyle = '#2a2a2e'; ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(405, -60); ctx.lineTo(405, -92); ctx.moveTo(405, -60); ctx.lineTo(430, -60); ctx.stroke();
      ctx.fillStyle = '#111'; ctx.fillRect(330, -6, 24, 12);
      // the card
      ctx.fillStyle = '#efe6cc'; ctx.fillRect(-460, -96, 800, 192);
      ctx.fillStyle = '#2a3a5a'; ctx.fillRect(-460, -96, 800, 40);
      ctx.font = 'bold 20px ' + HEAVY; ctx.textBaseline = 'middle'; ctx.fillStyle = '#efe6cc';
      spaced(ctx, 'KETTLE FALLS MANUFACTURING CO.   ·   TIME CARD', -60, -76, 4);
      ctx.strokeStyle = 'rgba(42,58,90,0.5)'; ctx.lineWidth = 1.5;
      for (var ln = 0; ln < 3; ln++) { ctx.beginPath(); ctx.moveTo(-440, 20 + ln * 24); ctx.lineTo(320, 20 + ln * 24); ctx.stroke(); }
      var size = fitSize(ctx, name, '900 #px ' + HEAVY, 58, 700, 0.04);
      ctx.font = '900 ' + size + 'px ' + HEAVY; ctx.fillStyle = '#1a1a1a';
      spaced(ctx, name, -60, -18, size * 0.04);
      ctx.font = 'bold 16px ' + HEAVY; ctx.fillStyle = '#2a3a5a';
      spaced(ctx, 'NO. 1846        IN  6:00 A.M.        OUT  6:00 P.M.', -60, 56, 3);
      // punched: the stamp
      var stamp = seg(t, 0.85, 0.95);
      if (stamp > 0) {
        ctx.save(); ctx.translate(200, 40); ctx.rotate(-0.14); ctx.scale(1.4 - 0.4 * stamp, 1.4 - 0.4 * stamp);
        ctx.globalAlpha = stamp * 0.85;
        ctx.strokeStyle = '#b81a1a'; ctx.lineWidth = 5; roundRect(ctx, -110, -28, 220, 56, 6); ctx.stroke();
        ctx.font = '900 34px ' + HEAVY; ctx.fillStyle = '#b81a1a';
        spaced(ctx, 'SHIFT OVER', 0, 2, 3);
        ctx.restore();
      }
      ctx.restore();
    }
  });

  /* Launch Complex 9: the moon rocket on the pad at night, searchlights
     crossing it, oxygen venting white; the count runs down in the corner,
     the engines light -- fire under it, smoke rolling out across the pad
     -- and up the crawlerway toward us, lit orange from behind, the crew
     come shambling.  The name is on a mission patch. */
  Intro.register('launchpad', {
    tagline: 'T-minus nothing. Light it anyway.',
    accent: '#e8682a',
    cues: [[0.1, 'll_wind', 0.3], [0.8, 'll_beep', 0.6], [1.2, 'll_beep', 0.6], [1.6, 'll_beep', 0.6],
           [2.0, 'll_beep', 0.7], [2.3, 'll_boom', 0.8], [2.4, 'll_rush', 0.8]],
    shakes: [[2.32, 8, 0.6]],
    tagY: 850, tagAt: 2.8,
    setup: function (r) {
      var d = { stars: makeStars(r, 220, 0, 480), zeds: [], smoke: [] };
      var looks = [['#f2f2f2', '#2a2a30', '#6fae55'], ['#c8ccd2', '#c8ccd2', '#7fb069'], ['#e8e8e4', '#e8e8e4', '#5f9a4c'],
                   ['#2a3a6a', '#1a2a4a', '#86b86a'], ['#e86a2a', '#3a3a3a', '#6c9f68']];
      for (var i = 0; i < 8; i++) {
        d.zeds.push({ x: 560 + (i % 4) * 140 + between(r, -30, 30), row: Math.floor(i / 4), at: 0.9 + i * 0.15, p: r() * 6,
                      look: looks[i % looks.length] });
      }
      for (i = 0; i < 26; i++) d.smoke.push({ dir: i % 2 ? 1 : -1, p: r(), y: between(r, -20, 30), s: between(r, 60, 140) });
      return d;
    },
    draw: function (ctx, t, d) {
      sky(ctx, [[0, '#02040e'], [0.6, '#0a1430'], [1, '#1a2a4a']], 620);
      starsK(ctx, d.stars, t, 1);
      // the moon, up where it's going
      ctx.fillStyle = '#f2f2e6'; ctx.beginPath(); ctx.arc(1320, 140, 46, 0, TAU); ctx.fill();
      additive(ctx, function () { dot(ctx, '#e8e8ff', 1320, 140, 150, 0.2); });
      var ign = seg(t, 2.25, 2.45);
      // the horizon, scrub, the sea far off right
      ctx.fillStyle = '#0a1018'; ctx.fillRect(0, 600, VW, 300);
      ctx.fillStyle = '#0e1a2a'; ctx.fillRect(1240, 596, 360, 12);
      // the searchlight beams
      additive(ctx, function () {
        [[300, 0.5], [1300, -0.5], [560, 0.25], [1040, -0.2]].forEach(function (sl, i) {
          var ang = sl[1] + Math.sin(t * 0.7 + i * 1.9) * 0.12;
          ctx.save(); ctx.translate(sl[0], 600); ctx.rotate(ang);
          var g = ctx.createLinearGradient(0, 0, 0, -620);
          g.addColorStop(0, 'rgba(220,230,255,0.28)'); g.addColorStop(1, 'rgba(220,230,255,0)');
          ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(-6, 0); ctx.lineTo(6, 0); ctx.lineTo(60, -620); ctx.lineTo(-60, -620); ctx.fill();
          ctx.restore();
        });
      });
      // the umbilical tower
      ctx.strokeStyle = '#c8562a'; ctx.lineWidth = 4;
      for (var tl = 0; tl < 2; tl++) { ctx.beginPath(); ctx.moveTo(880 + tl * 40, 600); ctx.lineTo(880 + tl * 40, 140); ctx.stroke(); }
      ctx.lineWidth = 2;
      for (var br = 0; br < 12; br++) {
        ctx.beginPath(); ctx.moveTo(880, 600 - br * 38); ctx.lineTo(920, 562 - br * 38); ctx.moveTo(920, 600 - br * 38); ctx.lineTo(880, 562 - br * 38); ctx.stroke();
      }
      ctx.fillStyle = '#c8562a'; ctx.fillRect(840, 132, 120, 8);
      var blink = Math.floor(t * 1.5) % 2;
      ctx.fillStyle = blink ? '#ff2a2a' : '#4a1010'; ctx.beginPath(); ctx.arc(900, 126, 5, 0, TAU); ctx.fill();
      if (blink) additive(ctx, function () { dot(ctx, '#ff3a3a', 900, 126, 26, 0.6); });
      // the rocket
      var rx = 800, base = 560;
      [[0, 120, '#eef0f2'], [120, 30, '#1a1c20'], [150, 70, '#eef0f2'], [220, 24, '#1a1c20']].forEach(function (s) {
        ctx.fillStyle = s[2]; ctx.fillRect(rx - 34, base - s[0] - s[1], 68, s[1]);
      });
      ctx.fillStyle = '#eef0f2'; ctx.fillRect(rx - 24, base - 300, 48, 56);
      ctx.fillStyle = '#1a1c20'; ctx.fillRect(rx - 24, base - 260, 48, 12);
      ctx.fillStyle = '#eef0f2'; ctx.beginPath(); ctx.moveTo(rx - 22, base - 300); ctx.lineTo(rx, base - 340); ctx.lineTo(rx + 22, base - 300); ctx.fill();
      ctx.fillStyle = '#e8682a'; ctx.fillRect(rx - 2, base - 384, 4, 46);
      ctx.fillStyle = '#1a1c20';
      [[-48, -34], [34, 48]].forEach(function (f) { ctx.beginPath(); ctx.moveTo(rx + f[0], base); ctx.lineTo(rx + (f[0] < 0 ? -34 : 34), base - 50); ctx.lineTo(rx + f[1], base); ctx.fill(); });
      // the mount and the pad
      ctx.fillStyle = '#4a5058'; ctx.fillRect(rx - 90, base, 180, 16);
      ctx.fillStyle = '#5a6068'; ctx.fillRect(0, base + 16, VW, 24);
      // vapour off it
      for (var v = 0; v < 8; v++) {
        var vu = (t * 0.4 + v / 8) % 1, vs = v % 2 ? 1 : -1;
        ctx.fillStyle = 'rgba(240,244,250,' + (0.4 * (1 - vu)) + ')';
        ctx.beginPath(); ctx.arc(rx + vs * (40 + vu * 60), base - 60 - (v % 4) * 50 + vu * 20, 10 + vu * 26, 0, TAU); ctx.fill();
      }
      // ignition: fire under it, smoke rolling out both ways
      if (ign > 0) {
        additive(ctx, function () { dot(ctx, '#ffb04a', rx, base + 30, 420 * ign, 0.6); });
        for (var fl = 0; fl < 5; fl++) {
          var fh = (80 + fl * 20) * ign * (0.85 + 0.15 * Math.sin(t * 30 + fl));
          var g2 = ctx.createLinearGradient(0, base, 0, base + fh);
          g2.addColorStop(0, 'rgba(255,250,210,0.95)'); g2.addColorStop(1, 'rgba(255,120,40,0)');
          ctx.fillStyle = g2;
          ctx.beginPath(); ctx.moveTo(rx - 30 + fl * 15, base); ctx.lineTo(rx - 40 + fl * 15 - 10, base + fh); ctx.lineTo(rx - 20 + fl * 15 + 10, base + fh); ctx.fill();
        }
        d.smoke.forEach(function (sm) {
          var q = Math.min(1, (t - 2.25) * 0.7 + sm.p * 0.3);
          var sx = rx + sm.dir * q * (300 + sm.p * 500);
          ctx.fillStyle = 'rgba(' + (q < 0.3 ? '255,180,110' : '200,196,192') + ',' + (0.7 * (1 - q * 0.6)) + ')';
          ctx.beginPath(); ctx.arc(sx, base + 30 + sm.y - q * 40, sm.s * (0.4 + q), 0, TAU); ctx.fill();
        });
      }
      // the crawlerway toward us, and them on it
      ctx.fillStyle = '#2a2e34';
      ctx.beginPath(); ctx.moveTo(700, 640); ctx.lineTo(900, 640); ctx.lineTo(1100, VH); ctx.lineTo(500, VH); ctx.fill();
      d.zeds.forEach(function (z) {
        var k2 = seg(t, z.at, z.at + 0.6);
        if (k2 <= 0) return;
        var y = 700 + z.row * 90 + (t - z.at) * 26, s = 1.8 + z.row * 0.8;
        ctx.save(); ctx.globalAlpha = k2;
        LL.shambler(ctx, z.x, y, s, t, z.look, z.x < 800 ? 1 : -1, z.p);
        ctx.restore();
      });
      // the count in the corner
      var count = Math.max(0, 10 - Math.floor(seg(t, 0.4, 2.25) * 10));
      ctx.font = '900 46px ' + HEAVY; ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
      ctx.fillStyle = count === 0 ? '#ffd84a' : '#ff5a2a';
      ctx.fillText(count === 0 ? 'IGNITION' : 'T-00:00:' + (count < 10 ? '0' : '') + count, 60, 140);
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Launch Complex 9').toUpperCase();
      var k = outBack(seg(t, 0.4, 0.85), 1.4);
      if (k <= 0) return;
      ctx.save();
      ctx.translate(800, 250);
      ctx.scale(0.75 * k, 0.75 * k);
      ctx.rotate((1 - k) * 0.6);
      // the patch: a stitched border, the night, the moon, the rocket going
      ctx.fillStyle = '#c8a83a'; ctx.beginPath(); ctx.arc(0, 0, 176, 0, TAU); ctx.fill();
      ctx.fillStyle = '#0e1a3a'; ctx.beginPath(); ctx.arc(0, 0, 164, 0, TAU); ctx.fill();
      ctx.strokeStyle = '#e8e0c8'; ctx.lineWidth = 3; ctx.setLineDash([8, 6]);
      ctx.beginPath(); ctx.arc(0, 0, 170, 0, TAU); ctx.stroke(); ctx.setLineDash([]);
      for (var st = 0; st < 14; st++) {
        var a = st / 14 * TAU, rr = 90 + (st % 3) * 22;
        ctx.fillStyle = '#e8e0c8'; ctx.fillRect(Math.cos(a) * rr - 2, Math.sin(a) * rr - 2, 4, 4);
      }
      ctx.fillStyle = '#e8e8dc'; ctx.beginPath(); ctx.arc(70, -70, 42, 0, TAU); ctx.fill();
      ctx.fillStyle = '#0e1a3a'; ctx.beginPath(); ctx.arc(52, -82, 38, 0, TAU); ctx.fill();
      ctx.save(); ctx.rotate(0.5);
      ctx.fillStyle = '#eef0f2'; ctx.fillRect(-10, -60, 20, 100);
      ctx.beginPath(); ctx.moveTo(-10, -60); ctx.lineTo(0, -88); ctx.lineTo(10, -60); ctx.fill();
      ctx.fillStyle = '#ff8a2a'; ctx.beginPath(); ctx.moveTo(-10, 40); ctx.lineTo(0, 90); ctx.lineTo(10, 40); ctx.fill();
      ctx.restore();
      // the ribbon across it with the name
      var size = fitSize(ctx, name, '900 #px ' + HEAVY, 60, 700, 0.05);
      ctx.fillStyle = '#a8282e';
      ctx.beginPath(); ctx.moveTo(-430, 60); ctx.lineTo(-360, 60); ctx.lineTo(-360, 150); ctx.lineTo(-430, 150); ctx.lineTo(-400, 105); ctx.fill();
      ctx.beginPath(); ctx.moveTo(430, 60); ctx.lineTo(360, 60); ctx.lineTo(360, 150); ctx.lineTo(430, 150); ctx.lineTo(400, 105); ctx.fill();
      ctx.fillStyle = '#c8382e'; roundRect(ctx, -380, 50, 760, 96, 8); ctx.fill();
      ctx.strokeStyle = '#e8e0c8'; ctx.setLineDash([6, 5]); ctx.lineWidth = 2;
      roundRect(ctx, -370, 58, 740, 80, 6); ctx.stroke(); ctx.setLineDash([]);
      ctx.font = '900 ' + size + 'px ' + HEAVY; ctx.textBaseline = 'middle'; ctx.fillStyle = '#f2ece0';
      spaced(ctx, name, 0, 98, size * 0.05);
      ctx.restore();
    }
  });

  /* The Underneath: down the great cistern -- rows of brick pillars going
     away into the dark, a lamp hung over the catwalk every so often, black
     water throwing the lamps back; rain coming down a shaft of light from a
     grate.  Between the pillars, eyes; then they stand up out of the water.
     The name is cast in a manhole cover, dropped into place. */
  Intro.register('cistern', {
    tagline: "Under the town, the water's rising. So are they.",
    accent: '#5ab8c8',
    cues: [[0.0, 'll_rain', 0.35], [0.55, 'll_clunk', 0.9], [1.5, 'll_splash', 0.5], [2.1, 'll_splash', 0.4],
           [2.6, 'll_squeak', 0.5]],
    shakes: [[0.58, 5, 0.2]],
    tagY: 850, tagAt: 2.6,
    setup: function (r) {
      var d = { rain: [], eyes: [], zeds: [] };
      for (var i = 0; i < 70; i++) d.rain.push({ x: between(r, 160, 420), y: r() * 900, v: between(r, 700, 1100) });
      for (i = 0; i < 9; i++) d.eyes.push({ x: between(r, 300, 1300), y: between(r, 430, 520), at: between(r, 0.6, 1.6), s: between(r, 0.5, 1.2) });
      var looks = [['#e8c81a', '#2a4a2a', '#6fae55'], ['#2a3040', '#2a3040', '#7fb069'], ['#8a7a5a', '#3a3a40', '#5f9a4c'],
                   ['#5a4a3a', '#3a3a2a', '#86b86a'], ['#2a2a2e', '#3a3a3a', '#6c9f68']];
      for (i = 0; i < 7; i++) d.zeds.push({ x: 260 + i * 180 + between(r, -40, 40), row: i % 2, at: 1.3 + i * 0.18, p: r() * 6,
                                            look: looks[i % looks.length] });
      return d;
    },
    draw: function (ctx, t, d) {
      ctx.fillStyle = '#06070a'; ctx.fillRect(0, 0, VW, VH);
      var vx = 800, vy = 430;
      // the vault and the rows of pillars going away
      for (var row = 6; row >= 0; row--) {
        var k = 1 / (1 + row * 0.55);
        var span = 900 * k, h = 640 * k;
        var shade = Math.floor(40 + 50 * k);
        ctx.strokeStyle = 'rgb(' + (shade + 30) + ',' + Math.floor(shade * 0.6) + ',' + Math.floor(shade * 0.5) + ')';
        ctx.lineWidth = 10 * k;
        ctx.beginPath(); ctx.arc(vx, vy - h * 0.28, span * 0.52, Math.PI, 0); ctx.stroke();
        for (var sd = -1; sd <= 1; sd += 2) {
          var px = vx + sd * span * 0.52;
          ctx.fillStyle = 'rgb(' + (shade + 22) + ',' + Math.floor(shade * 0.55) + ',' + Math.floor(shade * 0.45) + ')';
          ctx.fillRect(px - 26 * k, vy - h * 0.3, 52 * k, h * 0.62);
          ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.fillRect(px + sd * 6 * k - 26 * k * (sd < 0 ? 0 : 0), vy - h * 0.3, 10 * k, h * 0.62);
        }
        // a lamp over the catwalk
        var ly = vy - h * 0.18;
        var flick = row === 3 && Math.sin(t * 17) > 0.7 ? 0.3 : 1;
        ctx.strokeStyle = '#1a1a1a'; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(vx, vy - h * 0.55); ctx.lineTo(vx, ly); ctx.stroke();
        ctx.fillStyle = 'rgba(255,232,168,' + flick + ')'; ctx.beginPath(); ctx.arc(vx, ly, 6 * k + 2, 0, TAU); ctx.fill();
        additive(ctx, function () { dot(ctx, '#ffe0a0', vx, ly, 120 * k, 0.35 * flick); });
      }
      // the water, the lamps in it, the catwalk down the middle
      var wg = ctx.createLinearGradient(0, vy + 10, 0, VH);
      wg.addColorStop(0, '#0a1416'); wg.addColorStop(1, '#122426');
      ctx.fillStyle = wg; ctx.fillRect(0, vy + 10, VW, VH - vy - 10);
      for (var rf = 0; rf < 6; rf++) {
        var rk = 1 / (1 + rf * 0.55);
        additive(ctx, function () {
          ctx.fillStyle = 'rgba(255,220,150,' + (0.12 * rk) + ')';
          ctx.fillRect(vx - 30 * rk + Math.sin(t * 2 + rf) * 4, vy + 20 + (1 - rk) * 0 + 240 * rk, 60 * rk, 6);
        });
      }
      ctx.fillStyle = '#4a3a2a';
      ctx.beginPath(); ctx.moveTo(vx - 6, vy + 12); ctx.lineTo(vx + 6, vy + 12); ctx.lineTo(vx + 110, VH); ctx.lineTo(vx - 110, VH); ctx.fill();
      ctx.strokeStyle = 'rgba(0,0,0,0.4)'; ctx.lineWidth = 2;
      for (var pl = 0; pl < 12; pl++) {
        var py = vy + 12 + Math.pow(pl / 12, 1.8) * (VH - vy);
        var pw = 6 + (py - vy) * 0.22;
        ctx.beginPath(); ctx.moveTo(vx - pw, py); ctx.lineTo(vx + pw, py); ctx.stroke();
      }
      // the light shaft and the rain in it
      additive(ctx, function () {
        var sg = ctx.createLinearGradient(0, 0, 0, 700);
        sg.addColorStop(0, 'rgba(220,230,210,0.3)'); sg.addColorStop(1, 'rgba(220,230,210,0)');
        ctx.fillStyle = sg;
        ctx.beginPath(); ctx.moveTo(220, 0); ctx.lineTo(380, 0); ctx.lineTo(440, 700); ctx.lineTo(160, 700); ctx.fill();
      });
      ctx.strokeStyle = 'rgba(200,215,230,0.5)'; ctx.lineWidth = 1.4;
      ctx.beginPath();
      d.rain.forEach(function (rd) {
        var y = (rd.y + t * rd.v) % 760;
        ctx.moveTo(rd.x + y * 0.05, y); ctx.lineTo(rd.x + y * 0.05 + 1, y + 16);
      });
      ctx.stroke();
      // eyes in the dark, then them, getting up out of the water
      d.eyes.forEach(function (e) {
        var k2 = seg(t, e.at, e.at + 0.3) * (1 - seg(t, 1.8, 2.2));
        if (k2 <= 0) return;
        additive(ctx, function () {
          dot(ctx, '#b6ff4a', e.x - 6 * e.s, e.y, 8 * e.s, 0.8 * k2);
          dot(ctx, '#b6ff4a', e.x + 6 * e.s, e.y, 8 * e.s, 0.8 * k2);
        });
      });
      d.zeds.forEach(function (z) {
        var k3 = seg(t, z.at, z.at + 0.8);
        if (k3 <= 0) return;
        var water = z.row ? 760 : 640, sc = z.row ? 2.4 : 1.5;
        var y = water + 68 * sc - outCubic(k3) * 44 * sc + (t - z.at) * 4;
        ctx.save(); ctx.beginPath(); ctx.rect(0, 0, VW, water); ctx.clip();
        LL.shambler(ctx, z.x, y, sc, t, z.look, z.x < 800 ? 1 : -1, z.p);
        ctx.restore();
        ctx.strokeStyle = 'rgba(180,220,220,0.4)'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.ellipse(z.x, water, 18 * sc, 4 * sc, 0, 0, TAU); ctx.stroke();
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'The Underneath').toUpperCase();
      var k = seg(t, 0.25, 0.58);
      if (k <= 0) return;
      var drop = 1 - Math.pow(1 - k, 3);
      ctx.save();
      ctx.translate(800, lerp(-260, 236, drop));
      var spin = (1 - drop) * 1.4 + (t > 0.58 ? Math.sin((t - 0.58) * 30) * 0.02 * Math.max(0, 1 - (t - 0.58) * 3) : 0);
      ctx.rotate(spin);
      ctx.scale(0.8, 0.8);
      // the cover: an iron disc, its rim, the grid
      ctx.fillStyle = '#2a2a2c'; ctx.beginPath(); ctx.arc(0, 0, 210, 0, TAU); ctx.fill();
      ctx.strokeStyle = '#4a4a4e'; ctx.lineWidth = 14; ctx.beginPath(); ctx.arc(0, 0, 196, 0, TAU); ctx.stroke();
      ctx.save(); ctx.beginPath(); ctx.arc(0, 0, 186, 0, TAU); ctx.clip();
      ctx.strokeStyle = '#3e3e42'; ctx.lineWidth = 6;
      for (var g = -200; g <= 200; g += 34) {
        ctx.beginPath(); ctx.moveTo(g, -200); ctx.lineTo(g + 200, 200); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(g, 200); ctx.lineTo(g + 200, -200); ctx.stroke();
      }
      ctx.restore();
      ctx.fillStyle = '#2a2a2c'; roundRect(ctx, -330, -52, 660, 104, 10); ctx.fill();
      ctx.strokeStyle = '#5a5a5e'; ctx.lineWidth = 5; roundRect(ctx, -322, -44, 644, 88, 8); ctx.stroke();
      var size = fitSize(ctx, name, '900 #px ' + HEAVY, 70, 600, 0.06);
      ctx.font = '900 ' + size + 'px ' + HEAVY; ctx.textBaseline = 'middle';
      ctx.fillStyle = '#121214'; spaced(ctx, name, 2, 4, size * 0.06);
      ctx.fillStyle = '#8a8a90'; spaced(ctx, name, 0, 0, size * 0.06);
      ctx.font = 'bold 22px ' + HEAVY; ctx.fillStyle = '#7a7a80';
      spaced(ctx, 'HARROW  FLOODWORKS', 0, -120, 6);
      spaced(ctx, 'STORM  DRAIN  1902', 0, 124, 6);
      ctx.restore();
    }
  });

  /* Rooftops of Harrow Heights: over the roofs of the city in the snow --
     water towers, chimneys, the towers behind with a few windows lit; the
     billboard across the way flickers on, the cola pouring in neon -- and
     at the near parapet, hands come over the edge, and then the rest of
     them, climbing up out of the street.  The name, in neon. */
  Intro.register('rooftops', {
    tagline: "Don't look down. They're coming up.",
    accent: '#ff5a7a',
    cues: [[0.1, 'll_wind', 0.5], [0.45, 'll_neon', 0.6], [1.5, 'll_clunk', 0.4], [2.0, 'll_jingle', 0.4]],
    shakes: [],
    tagY: 850, tagAt: 2.6,
    setup: function (r) {
      var d = { stars: makeStars(r, 60, 0, 300), snow: [], towers: [], wins: [], climbers: [] };
      for (var i = 0; i < 160; i++) d.snow.push({ x: r() * VW, y: r() * 900, v: between(r, 30, 80), s: between(r, 1.5, 3.5), p: r() * 6 });
      for (i = 0; i < 14; i++) {
        var w = between(r, 80, 160), h = between(r, 200, 420);
        d.towers.push({ x: i * 120 - 40 + between(r, -20, 20), w: w, h: h });
        for (var k = 0; k < 10; k++) if (r() < 0.5) d.wins.push({ x: i * 120 - 40 + between(r, 0, w - 12), y: 560 - between(r, 20, h - 20) });
      }
      var looks = [['#3a3a42', '#2a2a30', '#6fae55'], ['#c81a2a', '#c81a2a', '#7fb069'], ['#2a8a3a', '#c81a2a', '#5f9a4c'],
                   ['#e8c81a', '#2a3a5a', '#86b86a'], ['#c8a83a', '#c8a83a', '#6c9f68']];
      for (i = 0; i < 6; i++) d.climbers.push({ x: 180 + i * 240 + between(r, -40, 40), at: 1.2 + i * 0.22, p: r() * 6, look: looks[i % looks.length] });
      return d;
    },
    draw: function (ctx, t, d) {
      sky(ctx, [[0, '#06081a'], [0.6, '#1a1c34'], [1, '#3a3450']], 600);
      starsK(ctx, d.stars, t, 0.6);
      // the towers behind
      d.towers.forEach(function (tw) { ctx.fillStyle = '#14161e'; ctx.fillRect(tw.x, 560 - tw.h, tw.w, tw.h); });
      d.wins.forEach(function (w, i) { ctx.fillStyle = i % 3 ? 'rgba(255,210,130,0.7)' : 'rgba(200,225,255,0.55)'; ctx.fillRect(w.x, w.y, 10, 12); });
      // the roofs across the way: a water tower, the billboard
      ctx.fillStyle = '#1e2028'; ctx.fillRect(0, 520, VW, 120);
      ctx.fillStyle = '#e8ecf2'; ctx.fillRect(0, 516, VW, 6);
      ctx.fillStyle = '#2a2422';
      ctx.fillRect(1260, 420, 6, 100); ctx.fillRect(1310, 420, 6, 100); ctx.fillRect(1250, 340, 76, 84);
      ctx.beginPath(); ctx.moveTo(1244, 342); ctx.lineTo(1288, 300); ctx.lineTo(1332, 342); ctx.fill();
      ctx.fillStyle = '#e8ecf2'; ctx.beginPath(); ctx.moveTo(1252, 340); ctx.lineTo(1288, 306); ctx.lineTo(1324, 340); ctx.lineTo(1316, 340); ctx.lineTo(1288, 314); ctx.lineTo(1260, 340); ctx.fill();
      var bx = 260, by = 300, bw = 560, bh = 190;
      ctx.fillStyle = '#1a1a22'; ctx.fillRect(bx + 60, by + bh, 8, 40); ctx.fillRect(bx + bw - 68, by + bh, 8, 40);
      ctx.fillStyle = '#1a2a4a'; ctx.fillRect(bx, by, bw, bh);
      var on = seg(t, 0.5, 0.6);
      if (on > 0) {
        var word = 'FROSTY COLA';
        ctx.font = '900 58px ' + HEAVY; ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
        var lay = K.layout(ctx, word, 4);
        var left = bx + bw * 0.42 - lay.width / 2;
        for (var c = 0; c < lay.chars.length; c++) {
          var lit = sputter(t, 0.55 + c * 0.06, c + 2) > 0.5;
          if (!lit) continue;
          additive(ctx, function () { dot(ctx, '#ff3a5a', left + lay.chars[c].x + 18, by + 60, 40, 0.3); });
          ctx.fillStyle = '#ff8aa0'; ctx.fillText(lay.chars[c].ch, left + lay.chars[c].x, by + 60);
        }
        var tip = Math.min(1, seg(t, 1.0, 1.6)) * 1.1;
        ctx.save(); ctx.translate(bx + 90, by + 120); ctx.rotate(-tip);
        ctx.strokeStyle = '#e8f4ff'; ctx.lineWidth = 4; ctx.strokeRect(-14, -50, 28, 60); ctx.strokeRect(-6, -74, 12, 24);
        ctx.restore();
        ctx.strokeStyle = '#e8f4ff'; ctx.strokeRect(bx + 150, by + 120, 40, 50);
        var fill = seg(t, 1.3, 3.0);
        ctx.fillStyle = '#c8682a'; ctx.fillRect(bx + 154, by + 166 - 42 * fill, 32, 42 * fill);
        additive(ctx, function () { dot(ctx, '#ff3a5a', bx + bw / 2, by + bh / 2, 360, 0.15); });
      } else {
        ctx.fillStyle = 'rgba(200,215,230,0.25)'; ctx.font = '900 54px ' + HEAVY; ctx.textBaseline = 'middle';
        ctx.fillText('FROSTY COLA', bx + 120, by + 60);
      }
      // the near roof: snow, the parapet, and them coming over it
      ctx.fillStyle = '#d8dee6'; ctx.fillRect(0, 700, VW, 210);
      ctx.fillStyle = '#5a3a2e'; ctx.fillRect(0, 680, VW, 30);
      ctx.fillStyle = '#eef2f6'; ctx.fillRect(0, 674, VW, 8);
      d.climbers.forEach(function (z) {
        var k2 = seg(t, z.at, z.at + 1.0);
        if (k2 <= 0) return;
        var hands = Math.min(1, k2 * 3);
        ctx.fillStyle = z.look[2];
        ctx.fillRect(z.x - 26, 672 - 6 * hands, 14, 10); ctx.fillRect(z.x + 12, 672 - 6 * hands, 14, 10);
        var rise = outCubic(Math.max(0, (k2 - 0.25) / 0.75));
        ctx.save(); ctx.beginPath(); ctx.rect(0, 0, VW, 676); ctx.clip();
        LL.shambler(ctx, z.x, 676 + 140 - rise * 140, 2.2, t, z.look, z.x < 800 ? 1 : -1, z.p);
        ctx.restore();
      });
      // and the snow
      ctx.fillStyle = 'rgba(255,255,255,0.85)';
      d.snow.forEach(function (f) {
        var y = (f.y + t * f.v) % 900, x = f.x + Math.sin(t + f.p) * 20;
        ctx.beginPath(); ctx.arc(x, y, f.s, 0, TAU); ctx.fill();
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Rooftops of Harrow Heights').toUpperCase();
      if (t < 0.3) return;
      ctx.save();
      ctx.fillStyle = 'rgba(10,10,20,0.6)'; roundRect(ctx, 260, 150, 1080, 150, 18); ctx.fill();
      ctx.strokeStyle = '#ff5a7a'; ctx.lineWidth = 3; roundRect(ctx, 270, 160, 1060, 130, 14); ctx.stroke();
      ctx.restore();
      LL.neonTitle(ctx, t, name, 800, 226, 980, '#ff7a9a', 0.35, 0.05);
    }
  });

  /* Glasshouse Gardens: the Palm House glowing from inside, its dome a
     lantern over the dark lawns; fireflies; the topiary animals standing in
     the foreground -- and one of them, the giraffe, turns its head.  Between
     the hedges, they come.  The name is on an old seed packet. */
  Intro.register('gardens', {
    tagline: 'Something in the glass is blooming. Something out here is hungry.',
    accent: '#b6ff8a',
    cues: [[0.1, 'll_wind', 0.3], [0.7, 'll_peacock', 0.5], [1.5, 'll_snap', 0.6], [2.2, 'll_stink', 0.35]],
    shakes: [],
    tagY: 850, tagAt: 2.6,
    setup: function (r) {
      var d = { stars: makeStars(r, 120, 0, 380), flies: [], zeds: [], panes: [] };
      for (var i = 0; i < 50; i++) d.flies.push({ x: r() * VW, y: between(r, 420, 780), p: r() * 6, s: between(r, 0.6, 1.2) });
      var looks = [['#3a6a3a', '#5a4a3a', '#6fae55'], ['#f6f2ea', '#f6f2ea', '#7fb069'], ['#1a1a1e', '#1a1a1e', '#5f9a4c'],
                   ['#e8c81a', '#3a4a6a', '#86b86a'], ['#c8b888', '#8a7a5a', '#6c9f68']];
      for (i = 0; i < 6; i++) d.zeds.push({ x: 420 + i * 150 + between(r, -30, 30), at: 1.3 + i * 0.2, p: r() * 6, look: looks[i % looks.length] });
      for (i = 0; i < 12; i++) d.panes.push(r());
      return d;
    },
    draw: function (ctx, t, d) {
      sky(ctx, [[0, '#040810'], [0.6, '#0e1a22'], [1, '#1e3030']], 560);
      starsK(ctx, d.stars, t, 0.8);
      // the Palm House: lit glass, the dome, the white ironwork
      var cx = 800, base = 560;
      additive(ctx, function () { dot(ctx, '#c8ffb0', cx, base - 120, 520, 0.22); });
      var glow = 'rgba(200,255,180,0.28)';
      ctx.fillStyle = glow; ctx.fillRect(cx - 420, base - 150, 840, 150);
      ctx.beginPath(); ctx.ellipse(cx, base - 150, 230, 200, 0, Math.PI, 0); ctx.fill();
      ctx.strokeStyle = 'rgba(240,250,240,0.8)'; ctx.lineWidth = 3;
      ctx.strokeRect(cx - 420, base - 150, 840, 150);
      for (var m = 0; m <= 20; m++) { ctx.beginPath(); ctx.moveTo(cx - 420 + m * 42, base - 150); ctx.lineTo(cx - 420 + m * 42, base); ctx.stroke(); }
      for (var rib = 0; rib <= 10; rib++) {
        var a = Math.PI + rib / 10 * Math.PI;
        ctx.beginPath(); ctx.moveTo(cx, base - 150); ctx.lineTo(cx + Math.cos(a) * 230, base - 150 + Math.sin(a) * 200); ctx.stroke();
      }
      ctx.beginPath(); ctx.ellipse(cx, base - 150, 230, 200, 0, Math.PI, 0); ctx.stroke();
      ctx.beginPath(); ctx.ellipse(cx, base - 150, 140, 120, 0, Math.PI, 0); ctx.stroke();
      // palm silhouettes inside
      ctx.fillStyle = 'rgba(20,50,30,0.7)';
      [-160, -40, 90, 200].forEach(function (px, i) {
        ctx.fillRect(cx + px - 4, base - 220 + i * 10, 8, 220 - i * 10);
        for (var f = 0; f < 6; f++) {
          ctx.save(); ctx.translate(cx + px, base - 220 + i * 10); ctx.rotate(-1.4 + f * 0.56 + Math.sin(t + i) * 0.05);
          ctx.beginPath(); ctx.ellipse(36, 0, 40, 7, 0, 0, TAU); ctx.fill(); ctx.restore();
        }
      });
      // the lawn, the hedge line
      ctx.fillStyle = '#0e1a12'; ctx.fillRect(0, base, VW, VH - base);
      ctx.fillStyle = '#14281a'; ctx.fillRect(0, base + 120, VW, 40);
      // the topiary in front: the elephant, the giraffe (whose head turns)
      ctx.fillStyle = '#1a3a1e';
      ctx.fillRect(180, 560, 150, 110); ctx.fillRect(310, 520, 70, 80); ctx.fillRect(350, 590, 20, 90);
      for (var lg = 0; lg < 4; lg++) ctx.fillRect(190 + lg * 38, 660, 24, 60);
      ctx.fillRect(1240, 560, 90, 80);
      for (var lg2 = 0; lg2 < 4; lg2++) ctx.fillRect(1244 + lg2 * 24, 630, 14, 90);
      ctx.fillRect(1300, 400, 28, 170);
      var turn = seg(t, 1.6, 2.1);
      ctx.save(); ctx.translate(1314, 404); ctx.rotate(-turn * 0.9);
      ctx.fillRect(-14, -40, 60 - turn * 20, 40);
      if (turn > 0.5) { additive(ctx, function () { dot(ctx, '#b6ff4a', 26 - turn * 10, -24, 10, 0.9); }); }
      ctx.restore();
      // between the hedges, them
      d.zeds.forEach(function (z) {
        var k2 = seg(t, z.at, z.at + 0.7);
        if (k2 <= 0) return;
        ctx.save(); ctx.globalAlpha = k2;
        LL.shambler(ctx, z.x + (t - z.at) * 8 * (z.x < 800 ? 1 : -1), 760, 2.0, t, z.look, z.x < 800 ? 1 : -1, z.p);
        ctx.restore();
      });
      // fireflies
      d.flies.forEach(function (f) {
        if (Math.sin(t * 2.4 * f.s + f.p * 3) < 0.4) return;
        var x = f.x + Math.sin(t * 0.6 + f.p) * 30, y = f.y + Math.cos(t * 0.5 + f.p) * 16;
        additive(ctx, function () { dot(ctx, '#d8ff6a', x, y, 10, 0.8); });
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || 'Glasshouse Gardens').toUpperCase();
      var k = outBack(seg(t, 0.4, 0.85), 1.3);
      if (k <= 0) return;
      ctx.save();
      ctx.translate(800, 230);
      ctx.rotate(0.03 + (1 - k) * 0.4);
      ctx.scale(0.8 * k, 0.8 * k);
      // the seed packet: cream, a green border, a little engraving of the
      // flower, the name across it
      ctx.fillStyle = '#efe6c8'; roundRect(ctx, -440, -130, 880, 260, 8); ctx.fill();
      ctx.strokeStyle = '#2a5a2a'; ctx.lineWidth = 8; roundRect(ctx, -424, -114, 848, 228, 6); ctx.stroke();
      ctx.lineWidth = 2; roundRect(ctx, -410, -100, 820, 200, 4); ctx.stroke();
      ctx.save(); ctx.translate(-320, 10);
      ctx.fillStyle = '#5a1a3a';
      ctx.beginPath(); ctx.moveTo(-50, 70); ctx.quadraticCurveTo(-60, -10, 0, -30); ctx.quadraticCurveTo(60, -10, 50, 70); ctx.fill();
      ctx.fillStyle = '#e8d8a0'; ctx.fillRect(-7, -90, 14, 110);
      ctx.fillStyle = '#3a6a2a'; ctx.fillRect(-36, 66, 72, 14);
      ctx.restore();
      ctx.textBaseline = 'middle';
      ctx.font = 'bold 22px ' + HEAVY; ctx.fillStyle = '#2a5a2a';
      spaced(ctx, 'HARROW  BOTANIC  GARDENS   ·   EST. 1852', 80, -70, 4);
      var size = fitSize(ctx, name, '900 #px ' + HEAVY, 64, 600, 0.04);
      ctx.font = '900 ' + size + 'px ' + HEAVY; ctx.fillStyle = '#1a3a1a';
      spaced(ctx, name, 80, 4, size * 0.04);
      ctx.font = 'bold 18px ' + HEAVY; ctx.fillStyle = '#8a2a4a';
      spaced(ctx, 'TITAN ARUM  ·  BLOOMS ONCE IN SEVEN YEARS', 80, 70, 3);
      ctx.restore();
    }
  });

  global.LastLightScenes = LL;
})(window);
