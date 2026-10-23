/* The arena worlds' arrival sequences -- the kit they are painted with.

   Last Light's four arrivals (game/area_intro.js) are each a few hundred
   lines of hand-placed canvas.  Sixty places across fifteen worlds are made
   the same way but from parts: a sky, a stack of animated layers (hills that
   parallax in, a skyline whose windows come on, water that rises, rain,
   snow, embers, confetti, searchlights...) and one of a handful of title
   treatments (a sign swung in on chains, a stamp slammed down, a neon tube
   flickering on, a marquee of chasing bulbs, letters dropped in and
   bouncing, a paint splat, a slide-in banner, a holo glitch).  A place adds
   whatever is its own as plain painter functions over the same kit.

   ArenaIntro.scene(id, spec) registers one with AreaIntro, which plays it in
   the same frame as Last Light's -- the bars, the grain, the ring of light
   opening onto the game -- so arriving anywhere looks of a piece.

   spec: name, tagline, accent (the reel and the bars), ring (the light that
   opens onto the game), sky ([top, middle, horizon]), horizon (y of the
   horizon, default 600), layers (painters, back to front), title (a style
   name or a painter), titleStyle (its colours), cues (sounds), shakes,
   tagY, tagAt, setup (extra data, given the seeded random). */
(function (global) {
  'use strict';

  var Intro = global.AreaIntro;
  if (!Intro || !Intro.kit) return;
  var K = Intro.kit;
  var VW = K.VW, VH = K.VH, TAU = K.TAU, FONT = K.FONT, HEAVY = K.HEAVY;
  var seg = K.seg, lerp = K.lerp, clamp = K.clamp, outBack = K.outBack, outCubic = K.outCubic;
  var inOut = K.inOut, rgba = K.rgba, mix = K.mix, dot = K.dot, additive = K.additive;
  var roundRect = K.roundRect, layout = K.layout, spaced = K.spaced, fitSize = K.fitSize;
  var between = K.between, sputter = K.sputter, buzz = K.buzz, wobble = K.wobble;

  // ================================================================ layers
  var L = {};

  /* The sky: a gradient, top to horizon. */
  function skyFill(ctx, stops, horizon) {
    var g = ctx.createLinearGradient(0, 0, 0, horizon);
    stops.forEach(function (c, i) { g.addColorStop(i / Math.max(1, stops.length - 1), c); });
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, VW, horizon + 2);
  }

  /* A sun or moon, rising or setting with a halo. */
  L.sun = function (o) {
    return function (ctx, t) {
      var y = o.y + (o.drift || 0) * t;
      additive(ctx, function () { dot(ctx, o.halo || o.colour, o.x, y, o.glow || 360, o.glowA || 0.45, (o.glow || 360) * 0.62); });
      ctx.fillStyle = o.colour;
      ctx.beginPath(); ctx.arc(o.x, y, o.r || 54, 0, TAU); ctx.fill();
      if (o.moon) {
        ctx.fillStyle = rgba('#000000', 0.18);
        ctx.beginPath(); ctx.arc(o.x - (o.r || 54) * 0.3, y - (o.r || 54) * 0.2, (o.r || 54) * 0.22, 0, TAU); ctx.fill();
        ctx.beginPath(); ctx.arc(o.x + (o.r || 54) * 0.25, y + (o.r || 54) * 0.3, (o.r || 54) * 0.14, 0, TAU); ctx.fill();
      }
    };
  };

  L.stars = function (n, top, bottom, alpha) {
    return function (ctx, t, d, run) {
      var key = 'stars' + n + '_' + top;
      if (!d[key]) d[key] = K.makeStars(run.rand, n, top, bottom);
      K.stars(ctx, d[key], t, alpha || 0.6);
    };
  };

  /* Drifting cloud bands. */
  L.clouds = function (colour, n, y0, y1, speed) {
    return function (ctx, t, d, run) {
      var key = 'clouds' + colour + y0;
      if (!d[key]) {
        d[key] = [];
        for (var i = 0; i < (n || 5); i++) {
          d[key].push([between(run.rand, 0, VW + 600), between(run.rand, y0, y1),
                       between(run.rand, 220, 620), between(run.rand, 10, 26),
                       between(run.rand, 6, 16) * (speed || 1)]);
        }
      }
      K.bands(ctx, d[key], t, colour);
    };
  };

  /* A puffy cloud bank (cumulus), drifting. */
  L.puffs = function (colour, list, speed) {
    return function (ctx, t) {
      ctx.fillStyle = colour;
      list.forEach(function (c) {
        var x = ((c[0] + t * (speed || 8)) % (VW + 500)) - 250;
        for (var k = 0; k < 5; k++) {
          ctx.beginPath();
          ctx.arc(x + (k - 2) * c[2] * 0.42, c[1] - Math.sin(k / 4 * Math.PI) * c[2] * 0.36, c[2] * (0.42 + 0.2 * Math.sin(k * 1.7)), 0, TAU);
          ctx.fill();
        }
        ctx.fillRect(x - c[2] * 1.05, c[1] - 2, c[2] * 2.1, c[2] * 0.32);
      });
    };
  };

  /* A ridge of hills or mountains, sliding in from below with parallax. */
  L.ridge = function (o) {
    return function (ctx, t, d, run) {
      var key = 'ridge' + o.colour + o.base;
      if (!d[key]) {
        var pts = [], x = -60;
        while (x < VW + 80) {
          pts.push([x, o.base - between(run.rand, o.min, o.max)]);
          x += between(run.rand, o.step * 0.6, o.step * 1.4);
        }
        d[key] = pts;
      }
      var rise = (1 - outCubic(seg(t, o.at || 0, (o.at || 0) + 1.1))) * (o.rise || 120);
      var slide = (o.pan || 0) * t;
      ctx.fillStyle = o.colour;
      ctx.beginPath();
      ctx.moveTo(-80, VH);
      d[key].forEach(function (p, i) {
        var y = p[1] + rise;
        if (o.sharp) ctx.lineTo(p[0] + slide, y);
        else if (i === 0) ctx.lineTo(p[0] + slide, y);
        else {
          var prev = d[key][i - 1];
          ctx.quadraticCurveTo(prev[0] + slide, prev[1] + rise, (prev[0] + p[0]) / 2 + slide, (prev[1] + p[1]) / 2 + rise);
        }
      });
      ctx.lineTo(VW + 80, VH);
      ctx.closePath();
      ctx.fill();
      if (o.snow) {
        ctx.fillStyle = o.snow;
        d[key].forEach(function (p) {
          if (o.base - p[1] < o.max * 0.7) return;
          ctx.beginPath();
          ctx.moveTo(p[0] + slide - 26, p[1] + rise + 30);
          ctx.lineTo(p[0] + slide, p[1] + rise);
          ctx.lineTo(p[0] + slide + 26, p[1] + rise + 30);
          ctx.closePath(); ctx.fill();
        });
      }
    };
  };

  /* Flat ground from the horizon down, with a gradient. */
  L.ground = function (top, bottom, y) {
    return function (ctx) {
      var g = ctx.createLinearGradient(0, y, 0, VH);
      g.addColorStop(0, top); g.addColorStop(1, bottom);
      ctx.fillStyle = g;
      ctx.fillRect(0, y, VW, VH - y);
    };
  };

  /* A city skyline whose windows come on one by one. */
  L.skyline = function (o) {
    return function (ctx, t, d, run) {
      var key = 'sky' + o.base + o.colour;
      if (!d[key]) {
        var list = [], x = -20;
        while (x < VW + 20) {
          var w = between(run.rand, o.minW || 50, o.maxW || 130);
          var h = between(run.rand, o.min, o.max);
          var win = [];
          for (var yy = 18; yy < h - 14; yy += 22) {
            for (var xx = 10; xx < w - 12; xx += 18) {
              if (run.rand() < (o.density || 0.55)) win.push([xx, yy, between(run.rand, 0.2, 3.2), run.rand()]);
            }
          }
          list.push({ x: x, w: w, h: h, win: win, spire: run.rand() < (o.spires || 0.15) });
          x += w + between(run.rand, 2, 14);
        }
        d[key] = list;
      }
      var rise = (1 - outCubic(seg(t, o.at || 0.1, (o.at || 0.1) + 1.2))) * (o.rise || 80);
      d[key].forEach(function (b) {
        var top = o.base - b.h + rise;
        ctx.fillStyle = o.colour;
        ctx.fillRect(b.x, top, b.w, o.base - top + 400);
        if (b.spire) ctx.fillRect(b.x + b.w / 2 - 3, top - 40, 6, 40);
        b.win.forEach(function (w) {
          var on = t > w[2] ? K.sputter(t, w[2], w[3] * 9) : 0;
          if (on < 0.5) return;
          ctx.fillStyle = w[3] < 0.5 ? (o.win || '#ffd890') : (o.win2 || o.win || '#9fd8ff');
          ctx.fillRect(b.x + w[0], top + w[1], 9, 12);
        });
      });
    };
  };

  /* Water: a body that can rise, with rolling wave lines and glints. */
  L.water = function (o) {
    return function (ctx, t) {
      var level = o.y - (o.rise ? o.rise * inOut(seg(t, o.riseAt || 1, (o.riseAt || 1) + (o.riseFor || 3))) : 0);
      var g = ctx.createLinearGradient(0, level, 0, VH);
      g.addColorStop(0, o.top); g.addColorStop(1, o.bottom);
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.moveTo(0, VH);
      for (var x = 0; x <= VW; x += 20) {
        ctx.lineTo(x, level + Math.sin(x * 0.012 + t * (o.speed || 1.6)) * (o.amp || 6) +
                   Math.sin(x * 0.031 - t * 2.3) * (o.amp || 6) * 0.4);
      }
      ctx.lineTo(VW, VH);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = rgba(o.foam || '#ffffff', 0.35);
      ctx.lineWidth = 2;
      for (var k = 1; k < 6; k++) {
        var yy = level + k * k * 9;
        ctx.beginPath();
        for (var x2 = -40; x2 <= VW; x2 += 40) {
          var ox = (x2 + t * 30 * (k % 2 ? 1 : -1) + k * 70) % (VW + 80) - 40;
          ctx.moveTo(ox, yy); ctx.lineTo(ox + 18 + k * 3, yy);
        }
        ctx.stroke();
      }
      if (o.glint) {
        additive(ctx, function () {
          for (var g2 = 0; g2 < 14; g2++) {
            var gx = o.glint + Math.sin(g2 * 7.3 + t * 2) * 140, gy = level + 10 + g2 * 9;
            dot(ctx, '#fff4d0', gx, gy, 26 - g2, 0.35 * Math.abs(Math.sin(t * 3 + g2)));
          }
        });
      }
      return level;
    };
  };

  /* Particles: rain, snow, embers, ash, bubbles, fireflies, petals, confetti, leaves. */
  L.particles = function (kind, n, o) {
    o = o || {};
    return function (ctx, t, d, run) {
      var key = 'p_' + kind + n;
      if (!d[key]) {
        d[key] = [];
        for (var i = 0; i < n; i++) {
          d[key].push([run.rand() * VW, run.rand() * VH, between(run.rand, 0.6, 1.4), run.rand() * TAU,
                       run.rand()]);
        }
      }
      var from = o.from || 0;
      var a = seg(t, from, from + 0.6) * (o.alpha || 1);
      if (a <= 0) return;
      var list = d[key];
      ctx.save();
      ctx.globalAlpha *= a;
      for (var i2 = 0; i2 < list.length; i2++) {
        var p = list[i2], s = p[2];
        var x, y;
        if (kind === 'rain') {
          x = (p[0] + t * 260 * s * (o.wind || 0.25)) % VW;
          y = (p[1] + t * 1100 * s) % VH;
          ctx.strokeStyle = o.colour || 'rgba(190,210,240,0.55)';
          ctx.lineWidth = 1.6 * s;
          ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - 7 * (o.wind || 0.25) * 4, y - 26 * s); ctx.stroke();
        } else if (kind === 'snow') {
          x = (p[0] + Math.sin(t * 0.8 + p[3]) * 30 + t * 40 * (o.wind || 0.4)) % VW;
          y = (p[1] + t * 70 * s) % VH;
          ctx.fillStyle = o.colour || '#ffffff';
          ctx.beginPath(); ctx.arc(x, y, 2.4 * s, 0, TAU); ctx.fill();
        } else if (kind === 'embers' || kind === 'sparks') {
          x = (p[0] + Math.sin(t * 1.3 + p[3]) * 40) % VW;
          y = VH - ((p[1] + t * 120 * s) % VH);
          additive(ctx, function () {
            dot(ctx, o.colour || '#ff8a2a', x, y, 7 * s, 0.6 + 0.4 * Math.sin(t * 9 + p[3]));
          });
        } else if (kind === 'ash') {
          x = (p[0] + t * 30 * s + Math.sin(t + p[3]) * 20) % VW;
          y = (p[1] + t * 40 * s) % VH;
          ctx.fillStyle = o.colour || 'rgba(70,64,64,0.7)';
          ctx.fillRect(x, y, 3 * s, 3 * s);
        } else if (kind === 'bubbles') {
          x = p[0] + Math.sin(t * 2 + p[3]) * 12;
          y = VH - ((p[1] + t * 90 * s) % VH);
          ctx.strokeStyle = o.colour || 'rgba(200,240,255,0.6)';
          ctx.lineWidth = 1.5;
          ctx.beginPath(); ctx.arc(x, y, 5 * s, 0, TAU); ctx.stroke();
        } else if (kind === 'fireflies') {
          x = p[0] + Math.sin(t * 0.7 + p[3]) * 40;
          y = (o.top || 500) + (p[1] % ((o.bottom || 800) - (o.top || 500))) + Math.cos(t * 0.9 + p[3]) * 20;
          additive(ctx, function () {
            dot(ctx, o.colour || '#e8ff7a', x, y, 9, Math.max(0, Math.sin(t * 2.2 + p[3] * 3)));
          });
        } else if (kind === 'confetti' || kind === 'petals' || kind === 'leaves') {
          x = (p[0] + Math.sin(t * 1.4 + p[3]) * 50 + t * 30 * (o.wind || 0.5)) % VW;
          y = (p[1] + t * 110 * s) % VH;
          var colours = o.colours || ['#ff4fa8', '#ffd24a', '#4ad8ff', '#7aff6a', '#ff7a3a'];
          ctx.fillStyle = colours[i2 % colours.length];
          ctx.save();
          ctx.translate(x, y);
          ctx.rotate(t * 3 * s + p[3]);
          if (kind === 'confetti') ctx.fillRect(-5, -2.5, 10, 5);
          else { ctx.beginPath(); ctx.ellipse(0, 0, 7, 3.5, 0, 0, TAU); ctx.fill(); }
          ctx.restore();
        } else if (kind === 'dust') {
          x = (p[0] + t * 160 * s) % VW;
          y = p[1] * 0.5 + 360 + Math.sin(t * 2 + p[3]) * 30;
          ctx.fillStyle = o.colour || 'rgba(200,150,90,0.35)';
          ctx.beginPath(); ctx.arc(x, y, 18 * s, 0, TAU); ctx.fill();
        }
      }
      ctx.restore();
    };
  };

  /* Searchlights sweeping the sky. */
  L.searchlights = function (list, colour) {
    return function (ctx, t) {
      additive(ctx, function () {
        list.forEach(function (sl, i) {
          var a = -Math.PI / 2 + Math.sin(t * (sl[2] || 0.7) + i * 2) * (sl[3] || 0.5);
          var len = 1100;
          var g = ctx.createLinearGradient(sl[0], sl[1], sl[0] + Math.cos(a) * len, sl[1] + Math.sin(a) * len);
          g.addColorStop(0, rgba(colour || '#fff4c8', 0.32));
          g.addColorStop(1, rgba(colour || '#fff4c8', 0));
          ctx.fillStyle = g;
          ctx.beginPath();
          ctx.moveTo(sl[0], sl[1]);
          ctx.lineTo(sl[0] + Math.cos(a - 0.05) * len, sl[1] + Math.sin(a - 0.05) * len);
          ctx.lineTo(sl[0] + Math.cos(a + 0.05) * len, sl[1] + Math.sin(a + 0.05) * len);
          ctx.closePath(); ctx.fill();
        });
      });
    };
  };

  /* A lightning flash: the whole frame whitens and a bolt forks down. */
  L.lightning = function (times, colour) {
    return function (ctx, t, d, run) {
      times.forEach(function (at, n) {
        var k = t - at;
        if (k < 0 || k > 0.35) return;
        var f = k < 0.06 ? 1 : (k < 0.12 ? 0.3 : (k < 0.18 ? 0.8 : 1 - k / 0.35));
        ctx.fillStyle = rgba('#e8f0ff', 0.28 * f);
        ctx.fillRect(0, 0, VW, VH);
        var x = 300 + ((n * 977) % 1000), y = 0;
        ctx.strokeStyle = rgba(colour || '#f4f8ff', f);
        ctx.lineWidth = 5;
        ctx.beginPath(); ctx.moveTo(x, y);
        var seedRand = K.rng(n * 31 + 7);
        while (y < 560) {
          x += between(seedRand, -60, 60); y += between(seedRand, 40, 90);
          ctx.lineTo(x, y);
        }
        ctx.stroke();
        additive(ctx, function () { dot(ctx, '#b8ccff', x, y, 240, 0.4 * f); });
      });
    };
  };

  /* Bunting strung across the top: triangles swinging. */
  L.bunting = function (y, colours, sag) {
    return function (ctx, t) {
      var n = 22;
      ctx.strokeStyle = '#2a2a2a'; ctx.lineWidth = 2;
      ctx.beginPath();
      for (var i = 0; i <= n; i++) {
        var x = i / n * VW, yy = y + Math.sin(i / n * Math.PI) * (sag || 60);
        if (i === 0) ctx.moveTo(x, yy); else ctx.lineTo(x, yy);
      }
      ctx.stroke();
      for (var j = 0; j < n; j++) {
        var x0 = (j + 0.5) / n * VW, y0 = y + Math.sin((j + 0.5) / n * Math.PI) * (sag || 60);
        var sw = Math.sin(t * 3 + j) * 0.18;
        ctx.save(); ctx.translate(x0, y0); ctx.rotate(sw);
        ctx.fillStyle = colours[j % colours.length];
        ctx.beginPath(); ctx.moveTo(-18, 0); ctx.lineTo(18, 0); ctx.lineTo(0, 36); ctx.closePath(); ctx.fill();
        ctx.restore();
      }
    };
  };

  /* A row of blocky figures in the classic default colours (yellow skin,
     red torso, blue legs), running, jumping, cheering. */
  function figure(ctx, x, y, h, phase, pose, colours) {
    var u = h / 30, c = colours || {};
    var skin = c.skin || '#f5cd30', torso = c.torso || '#c4281c', legs = c.legs || '#0d69ac';
    var step = Math.sin(phase);
    ctx.save();
    ctx.translate(x, y);
    if (pose === 'jump') ctx.translate(0, -Math.abs(Math.sin(phase * 0.5)) * 10 * u);
    // legs
    ctx.fillStyle = legs;
    var lean = pose === 'run' ? step * 0.45 : (pose === 'walk' ? step * 0.25 : 0);
    ctx.save(); ctx.translate(-2.1 * u, -12 * u); ctx.rotate(lean); ctx.fillRect(-2 * u, 0, 4 * u, 12 * u); ctx.restore();
    ctx.save(); ctx.translate(2.1 * u, -12 * u); ctx.rotate(-lean); ctx.fillRect(-2 * u, 0, 4 * u, 12 * u); ctx.restore();
    // torso
    ctx.fillStyle = torso;
    ctx.fillRect(-4.3 * u, -24 * u, 8.6 * u, 12.4 * u);
    // arms
    ctx.fillStyle = skin;
    var arm = pose === 'cheer' ? -2.6 + Math.sin(phase * 2) * 0.2 : (pose === 'run' ? -step * 0.6 : 0.1);
    ctx.save(); ctx.translate(-4.3 * u, -23 * u); ctx.rotate(-arm); ctx.fillRect(-3.6 * u, 0, 3.6 * u, 11 * u); ctx.restore();
    ctx.save(); ctx.translate(4.3 * u, -23 * u); ctx.rotate(arm); ctx.fillRect(0, 0, 3.6 * u, 11 * u); ctx.restore();
    // head
    ctx.fillStyle = skin;
    roundRect(ctx, -3.4 * u, -31.4 * u, 6.8 * u, 7 * u, 1.6 * u); ctx.fill();
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(-1.8 * u, -29 * u, 1 * u, 1.4 * u);
    ctx.fillRect(0.9 * u, -29 * u, 1 * u, 1.4 * u);
    ctx.restore();
  }
  L.figure = figure;

  /* Runners crossing the frame, left to right or right to left. */
  L.runners = function (list) {
    return function (ctx, t) {
      list.forEach(function (r) {
        var at = r.at || 0;
        if (t < at) return;
        var k = t - at;
        var x = r.x + (r.v || 0) * k;
        figure(ctx, x, r.y, r.h || 90, k * (r.rate || 9) + (r.ph || 0), r.pose || 'run', r.colours);
      });
    };
  };

  /* Something rotating in place (a windmill, a ferris wheel, a fan). */
  L.spinner = function (o) {
    return function (ctx, t) {
      var a = t * (o.speed || 1);
      ctx.save();
      ctx.translate(o.x, o.y);
      ctx.fillStyle = o.colour;
      ctx.strokeStyle = o.colour;
      ctx.lineWidth = o.width || 8;
      for (var i = 0; i < (o.arms || 4); i++) {
        ctx.save();
        ctx.rotate(a + i * TAU / (o.arms || 4));
        if (o.blade) ctx.fillRect(-o.blade / 2, 0, o.blade, o.r);
        else { ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, o.r); ctx.stroke(); }
        if (o.cars) {
          ctx.fillStyle = o.cars[i % o.cars.length];
          ctx.save(); ctx.translate(0, o.r); ctx.rotate(-(a + i * TAU / (o.arms || 4)));
          roundRect(ctx, -14, -4, 28, 24, 5); ctx.fill(); ctx.restore();
          ctx.fillStyle = o.colour;
        }
        ctx.restore();
      }
      if (o.rim) {
        ctx.beginPath(); ctx.arc(0, 0, o.r, 0, TAU); ctx.stroke();
      }
      ctx.beginPath(); ctx.arc(0, 0, o.hub || 12, 0, TAU); ctx.fill();
      ctx.restore();
    };
  };

  /* A glowing horizon band (lava, a city glow, a sunset). */
  L.glowBand = function (y, colour, h, alpha) {
    return function (ctx, t) {
      additive(ctx, function () {
        dot(ctx, colour, VW / 2, y, VW * 0.75, (alpha || 0.4) * (0.85 + 0.15 * Math.sin(t * 2)), h || 140);
      });
    };
  };

  /* A spotlight pool on the stage (a circus ring, an arena floor). */
  L.spot = function (x, y, rx, ry, colour, at) {
    return function (ctx, t) {
      var k = sputter(t, at || 0.4, x);
      if (k <= 0.1) return;
      additive(ctx, function () { dot(ctx, colour || '#fff4d0', x, y, rx, 0.55 * k, ry); });
    };
  };

  /* A grid floor in perspective (neon, a court). */
  L.grid = function (o) {
    return function (ctx, t) {
      var hz = o.y, cx = VW / 2;
      ctx.strokeStyle = o.colour;
      ctx.lineWidth = o.width || 2;
      ctx.globalAlpha *= o.alpha || 0.8;
      for (var i = -14; i <= 14; i++) {
        ctx.beginPath(); ctx.moveTo(cx + i * 30, hz); ctx.lineTo(cx + i * 220, VH); ctx.stroke();
      }
      var off = (t * (o.speed || 0.6)) % 1;
      for (var k = 0; k < 12; k++) {
        var f = (k + off) / 12;
        var y = hz + (VH - hz) * f * f;
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(VW, y); ctx.stroke();
      }
      ctx.globalAlpha /= o.alpha || 0.8;
    };
  };

  /* A blocky tree line (pines, palms, round trees) along a base line. */
  L.trees = function (o) {
    return function (ctx, t, d, run) {
      var key = 'trees' + o.base + o.colour;
      if (!d[key]) {
        d[key] = [];
        var x = -40;
        while (x < VW + 40) {
          d[key].push([x, between(run.rand, o.min || 120, o.max || 220), run.rand() * TAU]);
          x += between(run.rand, o.gap * 0.6, o.gap * 1.4);
        }
      }
      var rise = (1 - outCubic(seg(t, o.at || 0.2, (o.at || 0.2) + 1))) * 80;
      d[key].forEach(function (tr) {
        var sway = Math.sin(t * 1.2 + tr[2]) * (o.sway || 0.03);
        if (o.kind === 'palm') palm(ctx, tr[0], o.base + rise, tr[1], o.colour, o.trunk || o.colour, sway + Math.sin(t * 2 + tr[2]) * 0.05);
        else if (o.kind === 'round') {
          ctx.fillStyle = o.trunk || o.colour;
          ctx.fillRect(tr[0] - 6, o.base + rise - tr[1] * 0.45, 12, tr[1] * 0.45);
          ctx.fillStyle = o.colour;
          ctx.beginPath(); ctx.arc(tr[0] + sway * 200, o.base + rise - tr[1] * 0.62, tr[1] * 0.3, 0, TAU); ctx.fill();
        } else K.pine(ctx, tr[0], o.base + rise, tr[1], o.colour, sway);
      });
    };
  };

  function palm(ctx, x, base, h, leaf, trunk, sway) {
    ctx.save();
    ctx.translate(x, base);
    ctx.strokeStyle = trunk; ctx.lineWidth = h * 0.06;
    ctx.beginPath(); ctx.moveTo(0, 0);
    ctx.quadraticCurveTo(h * 0.1, -h * 0.5, h * 0.18 + sway * 200, -h);
    ctx.stroke();
    ctx.translate(h * 0.18 + sway * 200, -h);
    ctx.fillStyle = leaf;
    for (var i = 0; i < 6; i++) {
      ctx.save();
      ctx.rotate(-Math.PI / 2 + (i - 2.5) * 0.55 + sway * 3);
      ctx.beginPath();
      ctx.ellipse(h * 0.2, 0, h * 0.22, h * 0.05, 0.25, 0, TAU);
      ctx.fill();
      ctx.restore();
    }
    ctx.restore();
  }
  L.palm = palm;

  /* A painter that only runs from ``at`` (an event in the scene). */
  L.after = function (at, fn) {
    return function (ctx, t, d, run) { if (t >= at) fn(ctx, t, d, run, t - at); };
  };

  // ================================================================ titles
  /* Every title style draws the area name centred at (800, y), with the
     scene's alpha already set.  ``c`` is spec.titleStyle: plate, edge,
     ink, glow, font. */
  var T = {};

  function nameOf(run) { return (run.info.name || run.scene.name || '').toUpperCase(); }

  /* A sign swung in on two chains. */
  T.sign = function (ctx, t, d, run, c) {
    var name = nameOf(run);
    var drop = outBack(seg(t, 0.9, 1.45), 1.25);
    var cy = lerp(-260, c.y || 250, drop);
    var swing = wobble(t, 1.45, 0.06, 8, 2.2);
    var size = fitSize(ctx, name, 'bold #px ' + (c.font || HEAVY), c.size || 72, 1000, 0.05);
    ctx.font = 'bold ' + size + 'px ' + (c.font || HEAVY);
    var w = Math.max(560, layout(ctx, name, size * 0.05).width + 120), h = size + 70;
    [[-w * 0.36, -h / 2], [w * 0.36, -h / 2]].forEach(function (p) {
      var cos = Math.cos(swing), sin = Math.sin(swing);
      K.chain(ctx, 800 + p[0] * 1.05, -30, 800 + cos * p[0] - sin * p[1], cy + sin * p[0] + cos * p[1]);
    });
    ctx.save();
    ctx.translate(800, cy);
    ctx.rotate(swing);
    ctx.fillStyle = c.edge || '#3a2410';
    roundRect(ctx, -w / 2 - 8, -h / 2 - 8, w + 16, h + 16, 16); ctx.fill();
    var g = ctx.createLinearGradient(0, -h / 2, 0, h / 2);
    g.addColorStop(0, c.plate || '#c8904a'); g.addColorStop(1, c.plate2 || mix(c.plate || '#c8904a', '#000000', 0.35));
    ctx.fillStyle = g;
    roundRect(ctx, -w / 2, -h / 2, w, h, 12); ctx.fill();
    if (c.planks) {
      ctx.fillStyle = 'rgba(0,0,0,0.18)';
      for (var py = -h / 2 + h / 3; py < h / 2; py += h / 3) ctx.fillRect(-w / 2, py, w, 3);
    }
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillStyle = c.ink || '#2a1608';
    spaced(ctx, name, 0, 6, size * 0.05);
    if (c.sub) {
      ctx.font = 'bold 16px ' + FONT;
      ctx.fillStyle = c.subInk || c.ink || '#2a1608';
      spaced(ctx, c.sub, 0, h / 2 - 16, 4);
    }
    ctx.restore();
  };

  /* A stamp slammed down at an angle (with a shake, set in the cues). */
  T.stamp = function (ctx, t, d, run, c) {
    var name = nameOf(run);
    var at = c.at || 1.3;
    if (t < at) return;
    var k = seg(t, at, at + 0.16);
    var scale = lerp(2.6, 1, outCubic(k));
    var size = fitSize(ctx, name, 'bold #px ' + (c.font || HEAVY), c.size || 84, 1060, 0.04);
    ctx.save();
    ctx.translate(800, c.y || 270);
    ctx.rotate(c.angle === undefined ? -0.06 : c.angle);
    ctx.scale(scale, scale);
    ctx.globalAlpha *= k;
    ctx.font = 'bold ' + size + 'px ' + (c.font || HEAVY);
    var w = layout(ctx, name, size * 0.04).width + 80, h = size + 44;
    ctx.strokeStyle = c.ink || '#e8382a';
    ctx.lineWidth = 8;
    roundRect(ctx, -w / 2, -h / 2, w, h, 10); ctx.stroke();
    ctx.lineWidth = 3;
    roundRect(ctx, -w / 2 + 10, -h / 2 + 10, w - 20, h - 20, 6); ctx.stroke();
    ctx.fillStyle = c.ink || '#e8382a';
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    spaced(ctx, name, 0, 4, size * 0.04);
    ctx.restore();
  };

  /* A neon tube, flickering on letter by letter. */
  T.neon = function (ctx, t, d, run, c) {
    var name = nameOf(run);
    var size = fitSize(ctx, name, 'bold #px ' + (c.font || FONT), c.size || 76, 1040, 0.08);
    ctx.font = 'bold ' + size + 'px ' + (c.font || FONT);
    var l = layout(ctx, name, size * 0.08), left = 800 - l.width / 2, y = c.y || 260;
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    if (c.frame) {
      ctx.strokeStyle = rgba(c.frame, 0.9 * sputter(t, 0.9, 2));
      ctx.lineWidth = 4;
      roundRect(ctx, left - 40, y - size * 0.85, l.width + 80, size * 1.7, 22); ctx.stroke();
    }
    for (var i = 0; i < l.chars.length; i++) {
      var on = sputter(t, (c.at || 1.0) + i * 0.05, i) * buzz(t, i * 3.1);
      var col = i % 2 && c.glow2 ? c.glow2 : (c.glow || '#ff4fd8');
      ctx.fillStyle = on > 0.5 ? '#ffffff' : rgba(col, 0.25);
      if (on > 0.5) {
        ctx.shadowColor = col;
        ctx.shadowBlur = 26;
      }
      ctx.fillText(l.chars[i].ch, left + l.chars[i].x, y);
      ctx.shadowBlur = 0;
    }
    if (c.sub) {
      ctx.font = 'bold 18px ' + FONT;
      ctx.fillStyle = rgba(c.glow2 || c.glow || '#ff4fd8', sputter(t, 1.8, 5));
      spaced(ctx, c.sub, 800, y + size * 0.85, 6);
    }
  };

  /* A marquee: a lit board in a frame of chasing bulbs. */
  T.marquee = function (ctx, t, d, run, c) {
    var name = nameOf(run);
    var drop = outBack(seg(t, 0.9, 1.4), 1.2);
    var cy = lerp(-200, c.y || 250, drop);
    var size = fitSize(ctx, name, 'bold #px ' + (c.font || HEAVY), c.size || 66, 940, 0.05);
    ctx.font = 'bold ' + size + 'px ' + (c.font || HEAVY);
    var w = Math.max(600, layout(ctx, name, size * 0.05).width + 120), h = size + 80;
    ctx.save();
    ctx.translate(800, cy);
    ctx.fillStyle = c.edge || '#6a1410';
    roundRect(ctx, -w / 2, -h / 2, w, h, 14); ctx.fill();
    ctx.fillStyle = c.plate || '#fff6dc';
    ctx.fillRect(-w / 2 + 26, -h / 2 + 26, w - 52, h - 52);
    ctx.fillStyle = c.ink || '#1a120e';
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    spaced(ctx, name, 0, 4, size * 0.05);
    var bulbs = K.perimeter(w - 14, h - 14, 26), lit = [];
    for (var b = 0; b < bulbs.length; b++) {
      var on = t > 1.4 && ((b + Math.floor(t * 10)) % 3) !== 0;
      ctx.fillStyle = on ? (c.bulb || '#fff3c4') : '#4a3018';
      ctx.beginPath(); ctx.arc(bulbs[b][0], bulbs[b][1], 4.6, 0, TAU); ctx.fill();
      if (on) lit.push(bulbs[b]);
    }
    additive(ctx, function () {
      lit.forEach(function (p) { dot(ctx, c.glow || '#ffb84a', p[0], p[1], 15, 0.7); });
    });
    ctx.restore();
  };

  /* Letters dropped in one at a time, bouncing as they land. */
  T.drop = function (ctx, t, d, run, c) {
    var name = nameOf(run);
    var size = fitSize(ctx, name, 'bold #px ' + (c.font || HEAVY), c.size || 86, 1080, 0.04);
    ctx.font = 'bold ' + size + 'px ' + (c.font || HEAVY);
    var l = layout(ctx, name, size * 0.04), left = 800 - l.width / 2, y = c.y || 270;
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    var colours = c.colours || ['#ffd24a', '#ff6a3a', '#4ad8ff', '#7aff6a', '#ff4fa8'];
    for (var i = 0; i < l.chars.length; i++) {
      var at = (c.at || 0.9) + i * 0.05;
      if (t < at) break;
      var k = seg(t, at, at + 0.42);
      var yy = y - (1 - outBack(k, 2.4)) * 300;
      var sq = 1 + wobble(t, at + 0.3, 0.18, 22, 7);
      ctx.save();
      ctx.translate(left + l.chars[i].x + l.chars[i].w / 2, yy);
      ctx.scale(1 / sq, sq);
      ctx.lineWidth = size * 0.12;
      ctx.strokeStyle = c.edge || '#1a1a2a';
      ctx.strokeText(l.chars[i].ch, -l.chars[i].w / 2, 0);
      ctx.fillStyle = colours[i % colours.length];
      ctx.fillText(l.chars[i].ch, -l.chars[i].w / 2, 0);
      ctx.restore();
    }
  };

  /* A paint splat that bursts behind the name. */
  T.splat = function (ctx, t, d, run, c) {
    var name = nameOf(run);
    var at = c.at || 1.0;
    if (t < at) return;
    var k = outBack(seg(t, at, at + 0.3), 2);
    var y = c.y || 265;
    ctx.save();
    ctx.translate(800, y);
    ctx.scale(k, k);
    var blobs = d.splatBlobs || (d.splatBlobs = (function () {
      var r = K.rng(99), out = [];
      for (var i = 0; i < 26; i++) out.push([between(r, -560, 560), between(r, -110, 110), between(r, 30, 120)]);
      return out;
    })());
    ctx.fillStyle = c.paint || '#ff4fa8';
    blobs.forEach(function (b) { ctx.beginPath(); ctx.arc(b[0], b[1], b[2], 0, TAU); ctx.fill(); });
    ctx.beginPath(); ctx.ellipse(0, 0, 600, 130, 0, 0, TAU); ctx.fill();
    // drips
    for (var i = 0; i < 9; i++) {
      var dx = -480 + i * 120, len = 40 + ((i * 53) % 90) + seg(t, at + 0.3, at + 2.2) * 80;
      ctx.fillRect(dx - 9, 60, 18, len);
      ctx.beginPath(); ctx.arc(dx, 60 + len, 10, 0, TAU); ctx.fill();
    }
    ctx.restore();
    var size = fitSize(ctx, name, 'bold #px ' + (c.font || HEAVY), c.size || 82, 1040, 0.03);
    ctx.font = 'bold ' + size + 'px ' + (c.font || HEAVY);
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.globalAlpha *= seg(t, at + 0.15, at + 0.4);
    ctx.lineWidth = 10; ctx.strokeStyle = c.edge || '#1a1030';
    var l = layout(ctx, name, size * 0.03), left = 800 - l.width / 2;
    l.chars.forEach(function (ch) { ctx.strokeText(ch.ch, left + ch.x, y + 4); });
    ctx.fillStyle = c.ink || '#ffffff';
    l.chars.forEach(function (ch) { ctx.fillText(ch.ch, left + ch.x, y + 4); });
  };

  /* A banner sliding in from the side with a ribbon tail. */
  T.banner = function (ctx, t, d, run, c) {
    var name = nameOf(run);
    var k = outCubic(seg(t, c.at || 0.9, (c.at || 0.9) + 0.5));
    var x = lerp(c.from === 'right' ? 2400 : -800, 800, k);
    var y = c.y || 260;
    var size = fitSize(ctx, name, 'bold #px ' + (c.font || HEAVY), c.size || 70, 1000, 0.05);
    ctx.font = 'bold ' + size + 'px ' + (c.font || HEAVY);
    var w = layout(ctx, name, size * 0.05).width + 140, h = size + 50;
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(c.angle || -0.03);
    ctx.fillStyle = c.edge || '#14202e';
    ctx.beginPath();
    ctx.moveTo(-w / 2 - 60, -h / 2 + 18); ctx.lineTo(-w / 2, -h / 2 + 18); ctx.lineTo(-w / 2, h / 2 + 18);
    ctx.lineTo(-w / 2 - 60, h / 2 + 18); ctx.lineTo(-w / 2 - 34, 18); ctx.closePath(); ctx.fill();
    ctx.beginPath();
    ctx.moveTo(w / 2 + 60, -h / 2 + 18); ctx.lineTo(w / 2, -h / 2 + 18); ctx.lineTo(w / 2, h / 2 + 18);
    ctx.lineTo(w / 2 + 60, h / 2 + 18); ctx.lineTo(w / 2 + 34, 18); ctx.closePath(); ctx.fill();
    ctx.fillStyle = c.plate || '#2f86cf';
    ctx.fillRect(-w / 2, -h / 2, w, h);
    ctx.fillStyle = 'rgba(255,255,255,0.18)';
    ctx.fillRect(-w / 2, -h / 2, w, 6);
    ctx.fillStyle = c.ink || '#ffffff';
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    spaced(ctx, name, 0, 4, size * 0.05);
    ctx.restore();
  };

  /* A hologram: scanlines, a glitch jitter, then it locks in. */
  T.holo = function (ctx, t, d, run, c) {
    var name = nameOf(run);
    var at = c.at || 1.0;
    if (t < at) return;
    var size = fitSize(ctx, name, 'bold #px ' + (c.font || FONT), c.size || 78, 1040, 0.1);
    ctx.font = 'bold ' + size + 'px ' + (c.font || FONT);
    var y = c.y || 260;
    var lock = seg(t, at, at + 0.9);
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    var jitter = (1 - lock) * 26;
    [[c.glow2 || '#ff3a6a', -1], [c.glow || '#3affd8', 1]].forEach(function (pass) {
      ctx.fillStyle = rgba(pass[0], 0.7);
      spaced(ctx, name, 800 + pass[1] * (jitter + Math.sin(t * 40) * jitter * 0.5), y, size * 0.1);
    });
    ctx.fillStyle = '#ffffff';
    ctx.shadowColor = c.glow || '#3affd8'; ctx.shadowBlur = 24 * lock;
    spaced(ctx, name, 800, y, size * 0.1);
    ctx.shadowBlur = 0;
    ctx.fillStyle = 'rgba(0,0,0,0.25)';
    for (var sy = y - size; sy < y + size; sy += 5) ctx.fillRect(400, sy, 800, 2);
  };

  /* Carved in stone (temples, castles): it rises out of the ground. */
  T.carved = function (ctx, t, d, run, c) {
    var name = nameOf(run);
    var k = outCubic(seg(t, c.at || 0.9, (c.at || 0.9) + 0.8));
    var y = lerp((c.y || 250) + 140, c.y || 250, k);
    var size = fitSize(ctx, name, 'bold #px ' + (c.font || "Georgia, 'Times New Roman', serif"), c.size || 76, 1000, 0.08);
    ctx.font = 'bold ' + size + 'px ' + (c.font || "Georgia, 'Times New Roman', serif");
    var w = layout(ctx, name, size * 0.08).width + 120, h = size + 60;
    ctx.save();
    ctx.globalAlpha *= k;
    ctx.fillStyle = c.plate || '#8a8070';
    ctx.fillRect(800 - w / 2, y - h / 2, w, h);
    ctx.fillStyle = 'rgba(0,0,0,0.25)';
    ctx.fillRect(800 - w / 2, y + h / 2 - 10, w, 10);
    ctx.fillStyle = 'rgba(255,255,255,0.15)';
    ctx.fillRect(800 - w / 2, y - h / 2, w, 6);
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillStyle = 'rgba(255,255,255,0.25)';
    spaced(ctx, name, 802, y + 6, size * 0.08);
    ctx.fillStyle = c.ink || '#2a2218';
    spaced(ctx, name, 800, y + 4, size * 0.08);
    if (c.glow) additive(ctx, function () { dot(ctx, c.glow, 800, y, w * 0.6, 0.25 * k, h); });
    ctx.restore();
  };

  // ================================================================ scenes
  function scene(id, spec) {
    var horizon = spec.horizon || 600;
    var style = spec.titleStyle || {};
    var title = typeof spec.title === 'function' ? spec.title : (T[spec.title] || T.sign);
    Intro.register(id, {
      name: spec.name, tagline: spec.tagline, accent: spec.accent, ring: spec.ring,
      kickerColour: spec.kicker || spec.accent, chromeColour: spec.chrome,
      cues: spec.cues || [[0.3, 'whoosh', 0.35], [1.2, 'slam', 0.3]],
      shakes: spec.shakes || [], tagY: spec.tagY || 420, tagAt: spec.tagAt || 2.0,
      setup: function (r) {
        var d = spec.setup ? (spec.setup(r) || {}) : {};
        d._rand = r;
        return d;
      },
      draw: function (ctx, t, d, run) {
        run.rand = d._rand;
        if (spec.sky) skyFill(ctx, spec.sky, horizon);
        (spec.layers || []).forEach(function (layer) { layer(ctx, t, d, run); });
      },
      title: function (ctx, t, d, run) { title(ctx, t, d, run, style); }
    });
  }

  global.ArenaIntro = { scene: scene, L: L, T: T, K: K, figure: figure, palm: palm };
})(window);
