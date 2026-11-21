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

  global.LastLightScenes = LL;
})(window);
