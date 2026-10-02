/* Last Light -- arriving somewhere new.

   Three wipes at one place and the server shuffles everybody to another, and
   the round there opens on this: a few seconds of the place itself, painted
   on a canvas over the game in the blocky silhouettes and the very sky the
   area is built with, each with its own motion and its own way of putting
   the name up --

     Harrow Main Street  dusk.  The church bell swings and the crows lift off
                         the steeple, the streetlights stutter on one after
                         another down Main Street, the infected come up it,
                         and the Bijou's marquee drops in on its chains with
                         its bulbs chasing.
     St. Agnes Medical   night.  Ward windows buzz and die, the ambulance
                         washes everything red and blue, a searchlight sweeps
                         from the roof, hazard tape snaps across, the name
                         flickers on like a tube light and a QUARANTINE
                         stamp comes down over a heartbeat that goes flat.
     Blackwater Docks    fog on black water.  The lighthouse turns, and
                         wherever its beam falls the ship and the container
                         yard show their colours -- and whatever is coming up
                         out of the water -- until it reads the name off a
                         container and a floodlight clanks on over it.
     Cedar Pines Camp    the last of the sun on the lake.  Pines sway, bats
                         flit, fireflies come out, eyes shine in the old mine,
                         and the camp sign swings in on its chains -- with
                         something's claw marks across it.

   Every one opens like a light sputtering on and closes on a ring of light
   opening onto the game.  Nothing here takes input from the game: Space,
   Enter or Escape only cut it short.

   The wipe card's shuffle (a reel of the areas that spins and lands on the
   next one) and the three lamps that count the tries at a place live here
   too, so everything about moving on looks of a piece. */
(function (global) {
  'use strict';

  var VW = 1600, VH = 900;        // the stage every scene is painted on
  var CLOSE = 5.9;                // the ring of light starts to open
  var TOTAL = 7.1;
  var TAU = Math.PI * 2;
  var FONT = 'Verdana, Geneva, Tahoma, Arial, sans-serif';
  var HEAVY = "'Arial Black', 'Arial Bold', Impact, Verdana, sans-serif";

  // ------------------------------------------------------------ helpers
  function clamp(x, a, b) { return x < a ? a : (x > b ? b : x); }
  function seg(t, a, b) { return clamp((t - a) / (b - a), 0, 1); }
  function lerp(a, b, k) { return a + (b - a) * k; }
  function outCubic(x) { return 1 - Math.pow(1 - x, 3); }
  function inCubic(x) { return x * x * x; }
  function inOut(x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }
  function outBack(x, c) {
    c = c === undefined ? 1.70158 : c;
    return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2);
  }
  // a damped wobble after a knock at t0
  function wobble(t, t0, amp, freq, damp) {
    if (t < t0) return 0;
    var k = t - t0;
    return amp * Math.exp(-damp * k) * Math.sin(freq * k);
  }
  function rgbOf(h) {
    var n = parseInt(h.charAt(0) === '#' ? h.slice(1) : h, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function rgba(h, a) {
    var c = rgbOf(h);
    return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + clamp(a, 0, 1).toFixed(3) + ')';
  }
  function mix(a, b, k) {
    var x = rgbOf(a), y = rgbOf(b);
    return 'rgb(' + Math.round(lerp(x[0], y[0], k)) + ',' + Math.round(lerp(x[1], y[1], k)) +
      ',' + Math.round(lerp(x[2], y[2], k)) + ')';
  }
  function rng(seed) {
    var s = (seed >>> 0) || 0x9e3779b9;
    return function () {
      s ^= s << 13; s ^= s >>> 17; s ^= s << 5;
      return (s >>> 0) / 4294967296;
    };
  }
  function between(r, a, b) { return a + r() * (b - a); }

  // a light coming on: dark, a stutter or two, then steady
  function sputter(t, at, seed) {
    var k = t - at;
    if (k <= 0) return 0;
    if (k >= 0.45) return 1;
    var s = Math.sin(k * 71 + (seed || 0) * 13.1) + Math.sin(k * 23 + (seed || 0) * 5.3);
    return s > 0.3 - k * 2 ? 1 : 0.08;
  }
  // a bad tube or a dying neon: on, with the odd drop-out
  function buzz(t, seed) {
    return Math.sin(t * 37 + seed) + Math.sin(t * 11.3 + seed * 2.1) > -1.35 ? 1 : 0.15;
  }

  // soft round glows, one cached sprite per colour
  var sprites = {};
  function glow(color) {
    if (!sprites[color]) {
      var c = document.createElement('canvas');
      c.width = c.height = 64;
      var g = c.getContext('2d');
      var grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
      grad.addColorStop(0, rgba(color, 1));
      grad.addColorStop(0.22, rgba(color, 0.6));
      grad.addColorStop(1, rgba(color, 0));
      g.fillStyle = grad;
      g.fillRect(0, 0, 64, 64);
      sprites[color] = c;
    }
    return sprites[color];
  }
  function dot(ctx, color, x, y, rx, a, ry) {
    if (a <= 0.002) return;
    var old = ctx.globalAlpha;
    ctx.globalAlpha = old * Math.min(1, a);
    ry = ry || rx;
    ctx.drawImage(glow(color), x - rx, y - ry, rx * 2, ry * 2);
    ctx.globalAlpha = old;
  }
  function additive(ctx, fn) {
    var old = ctx.globalCompositeOperation;
    ctx.globalCompositeOperation = 'lighter';
    fn();
    ctx.globalCompositeOperation = old;
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }

  // ------------------------------------------------------------- text
  function layout(ctx, text, spacing) {
    var chars = [], x = 0;
    for (var i = 0; i < text.length; i++) {
      var w = ctx.measureText(text.charAt(i)).width;
      chars.push({ ch: text.charAt(i), x: x, w: w });
      x += w + spacing;
    }
    return { chars: chars, width: Math.max(0, x - spacing) };
  }
  // text centred on cx, letter by letter so it can be spaced out
  function spaced(ctx, text, cx, y, spacing) {
    var l = layout(ctx, text, spacing);
    var left = cx - l.width / 2;
    for (var i = 0; i < l.chars.length; i++) ctx.fillText(l.chars[i].ch, left + l.chars[i].x, y);
    return { left: left, width: l.width, chars: l.chars };
  }
  // the biggest size up to ``max`` at which ``text`` fits ``width``
  function fitSize(ctx, text, font, max, width, spacingEm) {
    ctx.font = font.replace('#', max);
    var w = layout(ctx, text, max * spacingEm).width;
    return w <= width ? max : Math.max(10, Math.floor(max * width / w));
  }
  // a long name over two lines at its middle space
  function split(name) {
    var words = name.split(' ');
    if (words.length < 2) return [name];
    var best = 1, gap = 1e9;
    for (var i = 1; i < words.length; i++) {
      var a = words.slice(0, i).join(' ').length, b = words.slice(i).join(' ').length;
      if (Math.abs(a - b) < gap) { gap = Math.abs(a - b); best = i; }
    }
    return [words.slice(0, best).join(' '), words.slice(best).join(' ')];
  }

  // ---------------------------------------------------- shared figures
  function stars(ctx, list, t, alpha) {
    var base = ctx.globalAlpha;
    ctx.fillStyle = '#fff';
    for (var i = 0; i < list.length; i++) {
      var s = list[i];
      ctx.globalAlpha = base * alpha * (0.3 + 0.7 * Math.abs(Math.sin(t * 1.3 + s[3])));
      ctx.fillRect(s[0], s[1], s[2], s[2]);
    }
    ctx.globalAlpha = base;
  }

  function makeStars(r, n, top, bottom) {
    var out = [];
    for (var i = 0; i < n; i++) {
      out.push([between(r, 0, VW), between(r, top, bottom), between(r, 1, 2.4), r() * 6]);
    }
    return out;
  }

  function bands(ctx, list, t, color) {
    ctx.fillStyle = color;
    for (var i = 0; i < list.length; i++) {
      var c = list[i];
      var x = ((c[0] + t * c[4]) % (VW + 800)) - 400;
      roundRect(ctx, x, c[1], c[2], c[3], c[3] / 2);
      ctx.fill();
    }
  }

  // an infected, blocky like everything else, shambling towards you
  function shambler(ctx, x, y, h, phase, color, eyes) {
    var u = h / 32, step = Math.sin(phase), sway = Math.sin(phase * 0.5) * 0.08;
    ctx.save();
    ctx.translate(x, y);
    ctx.fillStyle = color;
    var lift = Math.max(0, step) * u, other = Math.max(0, -step) * u;
    ctx.fillRect(-4.2 * u, -13 * u, 3.4 * u, 13 * u - lift);
    ctx.fillRect(0.8 * u, -13 * u, 3.4 * u, 13 * u - other);
    ctx.translate(0, -13 * u);
    ctx.rotate(sway);
    ctx.fillRect(-5.2 * u, -12.5 * u, 10.4 * u, 13 * u);
    ctx.save(); ctx.translate(-5 * u, -11.5 * u); ctx.rotate(0.32 + step * 0.12);
    ctx.fillRect(-3.2 * u, 0, 3.2 * u, 11.5 * u); ctx.restore();
    ctx.save(); ctx.translate(5 * u, -11.5 * u); ctx.rotate(-1.15 - step * 0.15);
    ctx.fillRect(0, 0, 3.2 * u, 11 * u); ctx.restore();
    ctx.translate(0, -12.5 * u);
    ctx.rotate(-0.2 + sway);
    ctx.fillRect(-3.5 * u, -7.2 * u, 7 * u, 7.4 * u);
    if (eyes > 0) {
      additive(ctx, function () {
        dot(ctx, '#ff6a2a', -1.5 * u, -4.4 * u, 2.6 * u, eyes);
        dot(ctx, '#ff6a2a', 1.5 * u, -4.4 * u, 2.6 * u, eyes);
      });
    }
    ctx.restore();
  }

  // a head and shoulders coming up out of the water
  function wader(ctx, x, y, h, rise, phase, color) {
    var u = h / 16;
    var up = rise * 11 * u;
    ctx.save();
    ctx.beginPath();
    ctx.rect(x - 20 * u, y - 30 * u, 40 * u, 30 * u);
    ctx.clip();
    ctx.translate(x, y + 11 * u - up);
    ctx.rotate(Math.sin(phase) * 0.06);
    ctx.fillStyle = color;
    ctx.fillRect(-5.5 * u, -1 * u, 11 * u, 8 * u);
    ctx.fillRect(-3.4 * u, -8 * u, 6.8 * u, 7 * u);
    if (rise > 0.45) {
      ctx.save(); ctx.translate(5 * u, 0); ctx.rotate(-2.3 + Math.sin(phase * 1.3) * 0.15);
      ctx.fillRect(0, 0, 2.6 * u, 9 * u); ctx.restore();
    }
    ctx.restore();
  }

  function crow(ctx, x, y, s, flap, perched) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = ctx.strokeStyle = '#0a070d';
    ctx.lineWidth = 2.2;
    ctx.lineCap = 'round';
    ctx.beginPath(); ctx.ellipse(0, 0, 7, 3.2, 0, 0, TAU); ctx.fill();
    if (perched) {
      ctx.beginPath(); ctx.arc(5, -3, 2.8, 0, TAU); ctx.fill();
    } else {
      var w = Math.sin(flap) * 8;
      ctx.beginPath(); ctx.moveTo(-2, 0); ctx.lineTo(-8, -w - 2); ctx.lineTo(-15, -w * 0.6 + 2);
      ctx.stroke();
      ctx.beginPath(); ctx.moveTo(2, 0); ctx.lineTo(7, -w - 2); ctx.lineTo(13, -w * 0.6 + 2);
      ctx.stroke();
    }
    ctx.restore();
  }

  function bat(ctx, x, y, s, flap) {
    var w = Math.sin(flap);
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = '#100a18';
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(-7, -5 * w - 2); ctx.lineTo(-13, -3 * w); ctx.lineTo(-9, 1); ctx.lineTo(-4, 0);
    ctx.lineTo(0, 3);
    ctx.lineTo(4, 0); ctx.lineTo(9, 1); ctx.lineTo(13, -3 * w); ctx.lineTo(7, -5 * w - 2);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  // a chain hanging between two points, link by link
  function chain(ctx, x1, y1, x2, y2) {
    var dx = x2 - x1, dy = y2 - y1;
    var len = Math.sqrt(dx * dx + dy * dy), n = Math.max(1, Math.floor(len / 12));
    var ang = Math.atan2(dy, dx);
    ctx.save();
    ctx.lineWidth = 3;
    for (var i = 0; i < n; i++) {
      var k = (i + 0.5) / n;
      ctx.save();
      ctx.translate(x1 + dx * k, y1 + dy * k);
      ctx.rotate(ang);
      ctx.strokeStyle = i % 2 ? '#2c2a2e' : '#4a4650';
      ctx.beginPath();
      if (i % 2) ctx.ellipse(0, 0, 7.5, 3.6, 0, 0, TAU);
      else { ctx.moveTo(-7, 0); ctx.lineTo(7, 0); }
      ctx.stroke();
      ctx.restore();
    }
    ctx.restore();
  }

  // a blocky pine: tiers of steps, as the camp's trees are built
  function pine(ctx, x, base, h, color, sway) {
    var tiers = 9, trunk = h * 0.1, width = h * 0.36;
    ctx.save();
    ctx.translate(x, base);
    ctx.transform(1, 0, sway || 0, 1, 0, 0);
    ctx.fillStyle = color;
    ctx.fillRect(-h * 0.022, -trunk - 4, h * 0.044, trunk + 6);
    var top = h - trunk, tierH = top / (tiers + 0.6);
    for (var k = 0; k < tiers; k++) {
      // each tier a skirt of three steps, narrowing up the tree
      var w = width * (1 - k / tiers * 0.86);
      var y = -trunk - k * tierH;
      ctx.fillRect(-w / 2, y - tierH * 0.42, w, tierH * 0.42);
      ctx.fillRect(-w * 0.34, y - tierH * 0.86, w * 0.68, tierH * 0.46);
      ctx.fillRect(-w * 0.18, y - tierH * 1.3, w * 0.36, tierH * 0.46);
    }
    ctx.fillRect(-width * 0.035, -h - tierH * 0.2, width * 0.07, tierH * 0.8);
    ctx.restore();
  }

  function pineIcon(ctx, x, y, s, color) {
    ctx.fillStyle = color;
    ctx.fillRect(x - s * 0.06, y + s * 0.32, s * 0.12, s * 0.2);
    for (var k = 0; k < 3; k++) {
      var w = s * (0.7 - k * 0.2), yy = y + s * (0.3 - k * 0.25);
      ctx.fillRect(x - w / 2, yy - s * 0.14, w, s * 0.16);
      ctx.fillRect(x - w * 0.32, yy - s * 0.24, w * 0.64, s * 0.12);
    }
  }

  // ============================================================= TOWN
  var TOWN = {
    name: 'Harrow Main Street',
    tagline: 'The night the town fell. The church bell still works.',
    cues: [[0.25, 'bell', 0.42], [0.5, 'crow', 0.4], [0.95, 'whoosh', 0.35],
           [1.5, 'slam', 0.32], [1.52, 'power', 0.45], [2.8, 'crow', 0.22],
           [3.4, 'groan', 0.3]],
    shakes: [[1.55, 5, 0.3]],
    tagY: 396, tagAt: 2.0,
    setup: function (r) {
      var d = { stars: makeStars(r, 46, 10, 300), far: [], crows: [], walkers: [],
                windows: [], clouds: [], bulbs: perimeter(916, 152, 24) };
      var x = 470;
      while (x < 1140) {
        var w = between(r, 24, 58);
        d.far.push({ x: x, w: w, h: between(r, 14, 64), lit: r() < 0.55 ? r() * 2.2 : -1 });
        x += w + between(r, -4, 6);
      }
      for (var i = 0; i < 5; i++) {
        d.clouds.push([between(r, 0, VW + 600), between(r, 150, 470), between(r, 260, 640),
                       between(r, 7, 15), between(r, 5, 13)]);
      }
      for (i = 0; i < 11; i++) {
        d.crows.push({ x: between(r, 120, 280), y: between(r, 140, 300), vx: between(r, 140, 300),
                       vy: between(r, -170, -70), at: 0.35 + r() * 0.4, flap: r() * 6,
                       s: between(r, 0.9, 1.4) });
      }
      for (i = 0; i < 10; i++) {
        d.walkers.push({ lane: between(r, -0.85, 0.85), s0: between(r, 0.09, 0.3),
                         v: between(r, 0.01, 0.024), ph: r() * 6, rate: between(r, 3.2, 4.8) });
      }
      for (var b = 0; b < 2; b++) {
        for (var row = 0; row < 3; row++) {
          for (var col = 0; col < 3; col++) {
            d.windows.push({ b: b, row: row, col: col, on: between(r, 0.1, 2.8),
                             off: r() < 0.3 ? between(r, 2.6, 6) : 99, warm: r() < 0.8 });
          }
        }
      }
      return d;
    },
    draw: function (ctx, t, d) {
      var HZ = 612;
      var sky = ctx.createLinearGradient(0, 0, 0, HZ);
      sky.addColorStop(0, '#15132a');
      sky.addColorStop(0.42, '#2c2748');
      sky.addColorStop(0.78, '#8a4c5e');
      sky.addColorStop(1, '#e48c5c');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, VW, HZ + 2);
      stars(ctx, d.stars, t, 0.55);
      // the sun going down at the end of Main Street
      var sunY = 574 + t * 6;
      additive(ctx, function () { dot(ctx, '#ff8a4a', 820, sunY, 420, 0.5, 260); });
      ctx.fillStyle = '#ffc47a';
      ctx.beginPath(); ctx.arc(820, sunY, 56, 0, TAU); ctx.fill();
      bands(ctx, d.clouds, t, 'rgba(58,34,62,0.75)');
      // the far end of town, hazy
      d.far.forEach(function (f) {
        ctx.fillStyle = '#4a3352';
        ctx.fillRect(f.x, HZ - f.h, f.w, f.h + 2);
        if (f.lit >= 0 && t > f.lit) {
          ctx.fillStyle = 'rgba(255,200,120,0.75)';
          ctx.fillRect(f.x + f.w * 0.3, HZ - f.h * 0.6, 3, 3);
        }
      });
      ctx.fillStyle = '#41304c';            // the water tower and the silos
      ctx.fillRect(1052, 520, 4, 92); ctx.fillRect(1088, 520, 4, 92);
      ctx.fillRect(1040, 488, 64, 36);
      ctx.beginPath(); ctx.moveTo(1036, 490); ctx.lineTo(1072, 466); ctx.lineTo(1108, 490); ctx.fill();
      roundRect(ctx, 560, 520, 30, 92, 12); ctx.fill();
      roundRect(ctx, 594, 536, 30, 76, 12); ctx.fill();
      // the ground and Main Street running away to the sun
      ctx.fillStyle = '#1a131f';
      ctx.fillRect(0, HZ, VW, VH - HZ);
      var road = ctx.createLinearGradient(0, HZ, 0, VH);
      road.addColorStop(0, '#4a3442');
      road.addColorStop(1, '#151018');
      ctx.fillStyle = road;
      ctx.beginPath();
      ctx.moveTo(250, VH); ctx.lineTo(792, HZ); ctx.lineTo(808, HZ); ctx.lineTo(1350, VH);
      ctx.closePath(); ctx.fill();
      // the centre line, creeping past as we walk in
      var creep = (t * 0.32) % 1;
      ctx.fillStyle = 'rgba(216,176,96,0.55)';
      for (var k = 0; k < 14; k++) {
        var near = 1 / (1 + (k - creep) * 0.75), far2 = 1 / (1 + (k - creep + 0.4) * 0.75);
        if (near <= 0 || near > 1.4) continue;
        var y1 = HZ + 288 * near, y2 = HZ + 288 * far2, w1 = 5 * near, w2 = 5 * far2;
        ctx.beginPath();
        ctx.moveTo(800 - w1, y1); ctx.lineTo(800 + w1, y1); ctx.lineTo(800 + w2, y2);
        ctx.lineTo(800 - w2, y2); ctx.closePath(); ctx.fill();
      }
      // a car run off the road, hazards still going
      var cs = 0.5, cx = 800 - 0.62 * 550 * cs, cy = HZ + 288 * cs;
      ctx.save();
      ctx.translate(cx, cy); ctx.rotate(-0.1);
      ctx.fillStyle = '#0f0b13';
      roundRect(ctx, -110 * cs, -52 * cs, 220 * cs, 38 * cs, 9 * cs); ctx.fill();
      roundRect(ctx, -62 * cs, -84 * cs, 112 * cs, 36 * cs, 10 * cs); ctx.fill();
      ctx.fillRect(56 * cs, -84 * cs, 10 * cs, 60 * cs);
      ctx.beginPath(); ctx.arc(-66 * cs, -12 * cs, 18 * cs, 0, TAU); ctx.arc(66 * cs, -12 * cs, 18 * cs, 0, TAU);
      ctx.fill();
      ctx.fillStyle = 'rgba(160,140,170,0.25)';
      ctx.fillRect(-52 * cs, -78 * cs, 40 * cs, 22 * cs);
      if ((t * 1.6) % 1 < 0.5) {
        additive(ctx, function () {
          dot(ctx, '#ffa030', -104 * cs, -36 * cs, 34 * cs, 0.95);
          dot(ctx, '#ffa030', 104 * cs, -36 * cs, 34 * cs, 0.95);
        });
      }
      ctx.restore();
      // streetlights: the light pools first, so the infected walk through them
      var lamps = [];
      for (var i = 0; i < 6; i++) {
        var s = 1 / (1 + i * 0.85);
        lamps.push({ s: s, x: 800 - 640 * s, side: 1, on: 0.85 + i * 0.15 });
        lamps.push({ s: s, x: 800 + 640 * s, side: -1, on: 0.92 + i * 0.15 });
      }
      lamps.forEach(function (l, n) {
        l.y = HZ + 288 * l.s;
        l.hx = l.x + l.side * 50 * l.s;
        l.hy = l.y - 300 * l.s;
        l.k = sputter(t, l.on, n);
      });
      additive(ctx, function () {
        lamps.forEach(function (l) {
          if (l.k <= 0.1) return;
          var cone = ctx.createLinearGradient(0, l.hy, 0, l.y);
          cone.addColorStop(0, 'rgba(255,214,150,' + (0.2 * l.k) + ')');
          cone.addColorStop(1, 'rgba(255,214,150,0)');
          ctx.fillStyle = cone;
          ctx.beginPath();
          ctx.moveTo(l.hx - 6 * l.s, l.hy); ctx.lineTo(l.hx + 6 * l.s, l.hy);
          ctx.lineTo(l.hx + 90 * l.s, l.y + 6 * l.s); ctx.lineTo(l.hx - 90 * l.s, l.y + 6 * l.s);
          ctx.closePath(); ctx.fill();
          dot(ctx, '#ffcf80', l.hx, l.y + 4 * l.s, 130 * l.s, 0.5 * l.k, 26 * l.s);
        });
      });
      // they come up Main Street
      d.walkers.slice().sort(function (a, b) { return a.s0 + a.v * t - b.s0 - b.v * t; })
        .forEach(function (w) {
          var ws = w.s0 + w.v * t;
          shambler(ctx, 800 + w.lane * 550 * ws, HZ + 288 * ws, 290 * ws,
                   w.ph + t * w.rate, '#0c0910', 0.6 + 0.4 * Math.sin(t * 3 + w.ph));
        });
      // the posts and the heads
      lamps.forEach(function (l) {
        ctx.fillStyle = '#0d0a10';
        ctx.fillRect(l.x - 4 * l.s, l.hy, 8 * l.s, l.y - l.hy);
        ctx.fillRect(Math.min(l.x, l.hx) - 2 * l.s, l.hy - 3 * l.s, Math.abs(l.hx - l.x) + 4 * l.s,
                     6 * l.s);
        ctx.fillRect(l.hx - 12 * l.s, l.hy - 2 * l.s, 24 * l.s, 9 * l.s);
        if (l.k > 0.1) {
          ctx.fillStyle = 'rgba(255,240,200,' + l.k + ')';
          ctx.fillRect(l.hx - 9 * l.s, l.hy + 6 * l.s, 18 * l.s, 3 * l.s);
          additive(ctx, function () { dot(ctx, '#ffd28a', l.hx, l.hy + 8 * l.s, 70 * l.s, l.k); });
        }
      });
      TOWN.church(ctx, t, d);
      TOWN.shops(ctx, t, d);
      // the crows, off the steeple at the first ring
      d.crows.forEach(function (c) {
        if (t < c.at) { crow(ctx, c.x, c.y + 6, c.s, 0, true); return; }
        var k = t - c.at;
        crow(ctx, c.x + c.vx * k, c.y + c.vy * k + 22 * k * k, c.s * (1 - k * 0.05),
             k * 17 + c.flap, false);
      });
    },
    church: function (ctx, t, d) {
      var C = '#110c17';
      ctx.fillStyle = C;
      ctx.beginPath();                       // the nave, off to the left
      ctx.moveTo(-40, VH); ctx.lineTo(-40, 520); ctx.lineTo(56, 432); ctx.lineTo(150, 520);
      ctx.lineTo(150, VH); ctx.closePath(); ctx.fill();
      ctx.fillRect(110, 390, 170, VH - 390);  // the tower
      ctx.fillRect(110, 300, 22, 92);
      ctx.fillRect(258, 300, 22, 92);
      ctx.fillRect(100, 286, 190, 18);
      ctx.beginPath(); ctx.moveTo(104, 290); ctx.lineTo(195, 112); ctx.lineTo(286, 290); ctx.fill();
      ctx.fillRect(192, 70, 6, 44); ctx.fillRect(181, 84, 28, 6);
      var opening = ctx.createLinearGradient(0, 304, 0, 390);
      opening.addColorStop(0, '#3a2a4a');
      opening.addColorStop(1, '#7a4a5a');
      ctx.fillStyle = opening;
      ctx.fillRect(132, 304, 126, 86);
      ctx.fillStyle = C;
      ctx.fillRect(120, 386, 150, 6);
      // the bell, swung hard and slowly let go
      var amp = t < 2.4 ? 0.5 : 0.5 * Math.exp(-0.9 * (t - 2.4));
      var swing = amp * Math.cos(Math.PI * (t - 0.25) / 0.9);
      ctx.save();
      ctx.translate(195, 308);
      ctx.rotate(swing);
      ctx.fillStyle = '#0b0810';
      ctx.fillRect(-5, -2, 10, 12);
      ctx.beginPath();
      ctx.moveTo(-17, 10); ctx.quadraticCurveTo(-19, 42, -31, 56); ctx.lineTo(31, 56);
      ctx.quadraticCurveTo(19, 42, 17, 10); ctx.closePath(); ctx.fill();
      ctx.fillStyle = 'rgba(255,190,120,0.35)';
      ctx.fillRect(-13, 18, 3, 30);
      ctx.fillStyle = '#0b0810';
      ctx.beginPath(); ctx.arc(-swing * 14, 60, 6, 0, TAU); ctx.fill();
      ctx.restore();
      // each ring rolls out over the town
      [0.25, 1.15, 2.05].forEach(function (at) {
        var k = (t - at) / 1.5;
        if (k <= 0 || k >= 1) return;
        ctx.strokeStyle = 'rgba(255,214,160,' + (0.4 * (1 - k)) + ')';
        ctx.lineWidth = 1 + 3 * (1 - k);
        ctx.beginPath(); ctx.arc(195, 345, 50 + 460 * k, -1.2, 1.2); ctx.stroke();
      });
      // the rose window, candle-lit
      var candle = 0.55 + 0.25 * Math.sin(t * 9) * Math.sin(t * 4.3);
      ctx.fillStyle = 'rgba(255,170,80,' + candle + ')';
      ctx.beginPath(); ctx.arc(195, 470, 22, 0, TAU); ctx.fill();
      ctx.strokeStyle = C; ctx.lineWidth = 3;
      for (var k2 = 0; k2 < 4; k2++) {
        ctx.beginPath(); ctx.moveTo(195, 470);
        ctx.lineTo(195 + Math.cos(k2 * Math.PI / 4) * 22, 470 + Math.sin(k2 * Math.PI / 4) * 22);
        ctx.moveTo(195, 470);
        ctx.lineTo(195 - Math.cos(k2 * Math.PI / 4) * 22, 470 - Math.sin(k2 * Math.PI / 4) * 22);
        ctx.stroke();
      }
      additive(ctx, function () { dot(ctx, '#ff9a40', 195, 470, 60, candle * 0.5); });
    },
    shops: function (ctx, t, d) {
      var blocks = [[1250, 430, 190], [1440, 360, 220]];
      blocks.forEach(function (b, n) {
        ctx.fillStyle = n ? '#120d18' : '#150f1c';
        ctx.fillRect(b[0], b[1], b[2], VH - b[1]);
        ctx.fillStyle = '#1e1626';
        ctx.fillRect(b[0] - 6, b[1] - 10, b[2] + 12, 12);
      });
      d.windows.forEach(function (w) {
        var b = blocks[w.b];
        var x = b[0] + 24 + w.col * (b[2] - 48) / 3, y = b[1] + 34 + w.row * 64;
        var lit = t > w.on && t < w.off ? sputter(t, w.on, w.row * 3 + w.col) : 0;
        ctx.fillStyle = lit > 0.5 ? (w.warm ? '#f2b860' : '#a8c8e8') : '#241a2a';
        ctx.fillRect(x, y, 30, 40);
        ctx.fillStyle = '#120d18';
        ctx.fillRect(x + 13, y, 4, 40);
        if (lit > 0.5) {
          additive(ctx, function () {
            dot(ctx, w.warm ? '#ffa850' : '#88b0e0', x + 15, y + 20, 46, 0.35);
          });
        }
      });
      // the diner's neon, hung out over the street
      var on = sputter(t, 0.7, 7) * buzz(t, 3);
      ctx.fillStyle = '#0d0a10';
      ctx.fillRect(1196, 600, 58, 6);
      roundRect(ctx, 1130, 610, 112, 46, 8);
      ctx.fill();
      ctx.font = 'bold 26px ' + FONT;
      ctx.textBaseline = 'middle';
      ctx.textAlign = 'center';
      ctx.fillStyle = on > 0.5 ? '#ff6a9a' : '#3a1a2a';
      ctx.fillText('DINER', 1186, 634);
      if (on > 0.5) additive(ctx, function () { dot(ctx, '#ff3a7a', 1186, 634, 110, 0.5, 46); });
      ctx.textAlign = 'left';
      // shopfronts
      ctx.fillStyle = 'rgba(242,184,96,' + (0.25 + 0.5 * sputter(t, 1.1, 9)) + ')';
      ctx.fillRect(1270, 760, 150, 100);
      ctx.fillStyle = '#120d18';
      ctx.fillRect(1340, 760, 6, 100);
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || TOWN.name).toUpperCase();
      var drop = outBack(seg(t, 1.0, 1.55), 1.25);
      var cy = lerp(-240, 232, drop);
      var swing = wobble(t, 1.55, 0.05, 8.5, 2.3) - 0.05 * (1 - seg(t, 1.0, 1.55));
      var hw = 470, hh = 88;
      var cos = Math.cos(swing), sin = Math.sin(swing);
      [[-330, -hh], [330, -hh]].forEach(function (p) {
        chain(ctx, 800 + p[0] * 1.05, -30, 800 + cos * p[0] - sin * p[1], cy + sin * p[0] + cos * p[1]);
      });
      ctx.save();
      ctx.translate(800, cy);
      ctx.rotate(swing);
      var panel = sputter(t, 1.42, 3);
      if (panel > 0.5) additive(ctx, function () { dot(ctx, '#ffd890', 0, 0, 700, 0.28, 220); });
      // the plate on top
      ctx.fillStyle = '#6a1410';
      roundRect(ctx, -200, -hh - 36, 400, 42, 8); ctx.fill();
      ctx.strokeStyle = '#d9a54a'; ctx.lineWidth = 2;
      roundRect(ctx, -194, -hh - 31, 388, 32, 6); ctx.stroke();
      ctx.font = 'bold 15px ' + FONT;
      ctx.textBaseline = 'middle';
      ctx.textAlign = 'left';
      ctx.fillStyle = '#ffd27a';
      spaced(ctx, 'THE BIJOU  ·  NOW SHOWING', 0, -hh - 15, 3);
      // the frame
      var frame = ctx.createLinearGradient(0, -hh, 0, hh);
      frame.addColorStop(0, '#7a1a14');
      frame.addColorStop(1, '#3a0a08');
      ctx.fillStyle = frame;
      roundRect(ctx, -hw, -hh, hw * 2, hh * 2, 14); ctx.fill();
      ctx.strokeStyle = '#d9a54a'; ctx.lineWidth = 3;
      roundRect(ctx, -hw + 5, -hh + 5, hw * 2 - 10, hh * 2 - 10, 11); ctx.stroke();
      // the backlit letter board
      var board = ctx.createLinearGradient(0, -hh + 30, 0, hh - 30);
      board.addColorStop(0, mix('#2a2420', '#fff6dc', panel));
      board.addColorStop(1, mix('#221c18', '#ecd7a6', panel));
      ctx.fillStyle = board;
      ctx.fillRect(-hw + 30, -hh + 30, hw * 2 - 60, hh * 2 - 60);
      ctx.fillStyle = 'rgba(150,120,80,0.6)';
      ctx.fillRect(-hw + 30, -22, hw * 2 - 60, 2);
      ctx.fillRect(-hw + 30, 34, hw * 2 - 60, 2);
      // the letters, hung one at a time
      var size = fitSize(ctx, name, 'bold #px ' + FONT, 64, 820, 0.06);
      ctx.font = 'bold ' + size + 'px ' + FONT;
      var l = layout(ctx, name, size * 0.06), left = -l.width / 2;
      for (var i = 0; i < l.chars.length; i++) {
        var at = 1.62 + i * 0.035;
        if (t < at) break;
        var k = seg(t, at, at + 0.2);
        ctx.globalAlpha = run.alpha * k;
        ctx.fillStyle = '#1a120e';
        ctx.fillText(l.chars[i].ch, left + l.chars[i].x, 6 - (1 - outBack(k, 2.2)) * 16);
      }
      ctx.globalAlpha = run.alpha;
      // the bulbs: they come on round the frame, then chase
      var count = d.bulbs.length, lit = [];
      for (var b = 0; b < count; b++) {
        var on;
        if (t < 1.2) on = false;
        else if (t < 1.75) on = b / count < seg(t, 1.2, 1.75);
        else on = ((b + Math.floor(t * 11)) % 3) !== 0;
        ctx.fillStyle = on ? '#fff3c4' : '#4a3018';
        ctx.beginPath(); ctx.arc(d.bulbs[b][0], d.bulbs[b][1], 4.3, 0, TAU); ctx.fill();
        if (on) lit.push(d.bulbs[b]);
      }
      additive(ctx, function () {
        lit.forEach(function (p) { dot(ctx, '#ffb84a', p[0], p[1], 15, 0.75); });
      });
      ctx.restore();
    }
  };

  function perimeter(w, h, step) {
    var pts = [], x0 = -w / 2, y0 = -h / 2;
    var nx = Math.max(1, Math.round(w / step)), ny = Math.max(1, Math.round(h / step));
    var i;
    for (i = 0; i < nx; i++) pts.push([x0 + w * i / nx, y0]);
    for (i = 0; i < ny; i++) pts.push([x0 + w, y0 + h * i / ny]);
    for (i = 0; i < nx; i++) pts.push([x0 + w - w * i / nx, y0 + h]);
    for (i = 0; i < ny; i++) pts.push([x0, y0 + h - h * i / ny]);
    return pts;
  }

  // ========================================================= HOSPITAL
  var HOSPITAL = {
    name: 'St. Agnes Medical',
    tagline: 'The army tried to quarantine it. Hold the roof.',
    cues: [[0.15, 'siren', 0.3], [0.75, 'whoosh', 0.3], [1.0, 'whoosh', 0.25],
           [1.36, 'buzz', 0.6], [1.56, 'beep', 0.6], [2.07, 'beep', 0.6],
           [2.52, 'flatline', 0.55], [2.85, 'slam', 0.5]],
    shakes: [[2.9, 10, 0.4]],
    tagY: 440, tagAt: 3.1,
    setup: function (r) {
      var d = { stars: makeStars(r, 70, 10, 330), windows: [], clouds: [] };
      for (var row = 0; row < 7; row++) {
        for (var col = 0; col < 15; col++) {
          var roll = r();
          d.windows.push({
            x: 500 + col * 50, y: 270 + row * 52,
            kind: roll < 0.34 ? 'lit' : (roll < 0.42 ? 'flicker' : (roll < 0.46 ? 'red' : 'dark')),
            seed: r() * 20, dies: r() < 0.2 ? between(r, 1.5, 5.5) : 99,
            figure: r() < 0.06
          });
        }
      }
      for (var i = 0; i < 4; i++) {
        d.clouds.push([between(r, 0, VW + 600), between(r, 60, 300), between(r, 300, 700),
                       between(r, 10, 22), between(r, 6, 14)]);
      }
      d.stamp = stampArt('QUARANTINE');
      return d;
    },
    draw: function (ctx, t, d) {
      var HZ = 650;
      var sky = ctx.createLinearGradient(0, 0, 0, HZ);
      sky.addColorStop(0, '#070d1a');
      sky.addColorStop(0.45, '#0f1a2c');
      sky.addColorStop(1, '#4a6478');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, VW, HZ);
      stars(ctx, d.stars, t, 0.7);
      additive(ctx, function () { dot(ctx, '#bcd0e8', 250, 150, 170, 0.35); });
      ctx.fillStyle = '#dfe8f0';
      ctx.beginPath(); ctx.arc(250, 150, 32, 0, TAU); ctx.fill();
      bands(ctx, d.clouds, t, 'rgba(14,22,36,0.85)');
      // a helicopter crossing high up, nav light blinking
      var hx = 1720 - t * 260, hy = 104 + Math.sin(t * 1.4) * 6;
      ctx.fillStyle = '#05080e';
      roundRect(ctx, hx - 22, hy - 7, 40, 15, 6); ctx.fill();
      ctx.fillRect(hx + 16, hy - 3, 34, 4);
      ctx.fillRect(hx - 34 + (t * 60 % 8), hy - 12, 70, 2);
      if ((t * 1.8) % 1 < 0.18) additive(ctx, function () { dot(ctx, '#ff3a2a', hx - 20, hy + 6, 16, 1); });
      // the searchlight on the roof, sweeping
      var ang = -1.95 + 0.48 * Math.sin(t * 0.9), half = 0.05;
      additive(ctx, function () {
        var ox = 1150, oy = 236, L = 1300;
        var beam = ctx.createLinearGradient(ox, oy, ox + Math.cos(ang) * L, oy + Math.sin(ang) * L);
        beam.addColorStop(0, 'rgba(220,235,255,0.32)');
        beam.addColorStop(1, 'rgba(220,235,255,0)');
        ctx.fillStyle = beam;
        ctx.beginPath(); ctx.moveTo(ox, oy);
        ctx.lineTo(ox + Math.cos(ang - half) * L, oy + Math.sin(ang - half) * L);
        ctx.lineTo(ox + Math.cos(ang + half) * L, oy + Math.sin(ang + half) * L);
        ctx.closePath(); ctx.fill();
      });
      // the garage, the skybridge, the hospital, the ER wing
      ctx.fillStyle = '#141c28';
      ctx.fillRect(30, 430, 350, HZ - 430);
      for (var deck = 0; deck < 4; deck++) {
        ctx.fillStyle = '#0a0f17';
        ctx.fillRect(40, 446 + deck * 52, 330, 30);
        ctx.fillStyle = 'rgba(200,220,255,0.12)';
        ctx.fillRect(60 + deck * 70, 456 + deck * 52, 22, 6);
      }
      ctx.fillStyle = 'rgba(140,200,230,0.22)';
      ctx.fillRect(380, 440, 90, 30);
      ctx.strokeStyle = '#141c28'; ctx.lineWidth = 3;
      for (var bridge = 0; bridge < 4; bridge++) {
        ctx.beginPath(); ctx.moveTo(390 + bridge * 24, 440); ctx.lineTo(390 + bridge * 24, 470); ctx.stroke();
      }
      ctx.fillStyle = '#1b2536';
      ctx.fillRect(470, 240, 780, HZ - 240);
      ctx.fillStyle = '#26324a';
      ctx.fillRect(462, 232, 796, 12);
      ctx.fillStyle = '#18202e';
      ctx.fillRect(1250, 470, 290, HZ - 470);
      d.windows.forEach(function (w) {
        var light = 0;
        if (w.kind === 'lit') light = 1;
        else if (w.kind === 'flicker') light = buzz(t * 2.2, w.seed) > 0.5 && Math.sin(t * 5 + w.seed) > -0.2 ? 1 : 0;
        else if (w.kind === 'red') light = 0.8;
        if (t > w.dies) light = sputter(t, w.dies, w.seed) > 0.5 ? 0 : light;
        ctx.fillStyle = light ? (w.kind === 'red' ? '#c84a40' : '#c4daf0') : '#0d131e';
        ctx.fillRect(w.x, w.y, 32, 30);
        if (light && w.figure) {
          ctx.fillStyle = '#0a0e16';
          ctx.fillRect(w.x + 11, w.y + 8, 10, 9);
          ctx.fillRect(w.x + 7, w.y + 17, 18, 13);
        }
      });
      // the entrance, the lobby still lit
      ctx.fillStyle = 'rgba(210,228,255,0.75)';
      ctx.fillRect(760, 600, 120, 50);
      ctx.fillStyle = '#26324a';
      ctx.fillRect(740, 590, 160, 10);
      ctx.fillStyle = '#1b2536';
      ctx.fillRect(817, 600, 6, 50);
      // the red cross on the roof, its tube buzzing
      ctx.fillStyle = '#0d131e';
      ctx.fillRect(828, 196, 6, 40); ctx.fillRect(886, 196, 6, 40);
      var cross = sputter(t, 0.45, 2) * buzz(t, 7);
      ctx.fillStyle = cross > 0.5 ? '#f4f4f0' : '#3a3e48';
      ctx.fillRect(820, 150, 80, 60);
      ctx.fillStyle = cross > 0.5 ? '#e0302a' : '#4a2020';
      ctx.fillRect(852, 156, 16, 48); ctx.fillRect(836, 172, 48, 16);
      if (cross > 0.5) additive(ctx, function () { dot(ctx, '#ff4a3a', 860, 180, 120, 0.35); });
      // the ER canopy and the ambulance, lights going
      ctx.fillStyle = '#26324a';
      ctx.fillRect(1290, 556, 230, 14);
      ctx.font = 'bold 18px ' + FONT;
      ctx.textBaseline = 'middle'; ctx.textAlign = 'center';
      ctx.fillStyle = sputter(t, 0.9, 5) > 0.5 ? '#ff5a4a' : '#4a2020';
      ctx.fillText('EMERGENCY', 1405, 540);
      ctx.textAlign = 'left';
      ctx.fillStyle = '#e8ecf0';
      roundRect(ctx, 1330, 590, 140, 54, 6); ctx.fill();
      ctx.fillStyle = '#c83a30';
      ctx.fillRect(1330, 618, 140, 8);
      var phase = Math.sin(t * 8.8);
      ctx.fillStyle = phase > 0 ? '#ff3a2a' : '#3a6aff';
      ctx.fillRect(1356, 582, 30, 8); ctx.fillRect(1414, 582, 30, 8);
      // the lot
      ctx.fillStyle = '#10151e';
      ctx.fillRect(0, HZ, VW, VH - HZ);
      ctx.fillStyle = 'rgba(220,220,200,0.18)';
      for (var line = 0; line < 9; line++) {
        ctx.beginPath();
        ctx.moveTo(140 + line * 160, 680); ctx.lineTo(150 + line * 160, 680);
        ctx.lineTo(100 + line * 175, 760); ctx.lineTo(88 + line * 175, 760);
        ctx.closePath(); ctx.fill();
      }
      // red and blue over everything
      additive(ctx, function () {
        var red = Math.max(0, phase), blue = Math.max(0, -phase);
        dot(ctx, '#ff2a1a', 1400, 600, 760, 0.3 * red, 420);
        dot(ctx, '#2a5aff', 1400, 600, 760, 0.32 * blue, 420);
        dot(ctx, '#ff2a1a', 1400, 586, 90, red);
        dot(ctx, '#2a5aff', 1400, 586, 90, blue);
      });
      // the checkpoint: tents, sandbags, a fence with wire on it
      ctx.fillStyle = '#1a2418';
      [[60, 300], [1300, 1520]].forEach(function (tent) {
        ctx.beginPath();
        ctx.moveTo(tent[0], 800); ctx.lineTo((tent[0] + tent[1]) / 2, 700); ctx.lineTo(tent[1], 800);
        ctx.closePath(); ctx.fill();
      });
      ctx.fillStyle = '#0c1018';
      for (var post = 0; post < 13; post++) ctx.fillRect(20 + post * 130, 660, 7, 140);
      ctx.strokeStyle = 'rgba(150,170,190,0.16)';
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      for (var m = -200; m < VW + 200; m += 16) {
        ctx.moveTo(m, 676); ctx.lineTo(m + 124, 800);
        ctx.moveTo(m + 124, 676); ctx.lineTo(m, 800);
      }
      ctx.stroke();
      ctx.strokeStyle = 'rgba(160,170,180,0.4)';
      ctx.lineWidth = 1.5;
      for (var coil = 0; coil < 70; coil++) {
        ctx.beginPath(); ctx.arc(coil * 24, 662, 11, 0, TAU); ctx.stroke();
      }
      ctx.fillStyle = '#2a2a22';
      for (var bag = 0; bag < 22; bag++) {
        roundRect(ctx, -20 + bag * 76, 800 + (bag % 2) * 6, 80, 26, 12); ctx.fill();
      }
      // hazard tape, snapped across
      HOSPITAL.tape(ctx, t, 0.75, 770, -0.07, 0);
      HOSPITAL.tape(ctx, t, 1.0, 640, 0.09, 260);
    },
    tape: function (ctx, t, at, y, ang, offset) {
      var k = outCubic(seg(t, at, at + 0.32));
      if (k <= 0) return;
      ctx.save();
      ctx.translate(800 + (1 - k) * -2000, y + wobble(t, at + 0.32, 6, 22, 7));
      ctx.rotate(ang);
      ctx.fillStyle = '#f2c230';
      ctx.fillRect(-1100, -20, 2200, 40);
      ctx.save();
      ctx.beginPath(); ctx.rect(-1100, -20, 2200, 40); ctx.clip();
      ctx.fillStyle = '#121212';
      var slide = (t * 40 + offset) % 520;
      ctx.font = '900 20px ' + HEAVY;
      ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
      for (var x = -1100 - slide; x < 1100; x += 520) {
        for (var s = 0; s < 4; s++) {
          ctx.beginPath();
          ctx.moveTo(x + s * 30, -20); ctx.lineTo(x + s * 30 + 16, -20);
          ctx.lineTo(x + s * 30 - 4, 20); ctx.lineTo(x + s * 30 - 20, 20);
          ctx.closePath(); ctx.fill();
        }
        ctx.fillText('QUARANTINE — DO NOT CROSS', x + 128, 1);
      }
      ctx.restore();
      ctx.restore();
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || HOSPITAL.name).toUpperCase();
      var band = ctx.createLinearGradient(0, 0, VW, 0);
      var show = seg(t, 1.2, 1.6);
      band.addColorStop(0, 'rgba(3,7,14,' + (0.25 * show) + ')');
      band.addColorStop(0.5, 'rgba(3,7,14,' + (0.86 * show) + ')');
      band.addColorStop(1, 'rgba(3,7,14,' + (0.25 * show) + ')');
      ctx.fillStyle = band;
      ctx.fillRect(0, 226, VW, 252);
      ctx.fillStyle = 'rgba(120,170,220,' + (0.35 * show) + ')';
      ctx.fillRect(0, 226, VW, 1.5);
      ctx.fillRect(0, 476, VW, 1.5);
      var on = sputter(t, 1.36, 4);
      if (on > 0.05) {
        var size = fitSize(ctx, name, 'bold #px ' + FONT, 72, 1040, 0.1);
        ctx.font = 'bold ' + size + 'px ' + FONT;
        ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
        ctx.save();
        ctx.globalAlpha = run.alpha * on;
        ctx.shadowColor = 'rgba(140,200,255,0.9)';
        ctx.shadowBlur = 26;
        ctx.fillStyle = '#eaf4ff';
        spaced(ctx, name, 800, 300, size * 0.1);
        ctx.restore();
      }
      HOSPITAL.ekg(ctx, t);
      // the stamp comes down
      var k = seg(t, 2.85, 3.02);
      if (k > 0) {
        var scale = lerp(2.6, 1, inCubic(k));
        ctx.save();
        ctx.globalAlpha = run.alpha * Math.min(1, k * 1.6) * 0.95;
        ctx.translate(1110, 236);
        ctx.rotate(-0.17);
        ctx.scale(scale * 0.62, scale * 0.62);
        ctx.drawImage(d.stamp, -d.stamp.width / 2, -d.stamp.height / 2);
        ctx.restore();
      }
    },
    ekg: function (ctx, t) {
      var x0 = 520, x1 = 1080, y0 = 374;
      var head = lerp(x0, x1, seg(t, 1.3, 3.1));
      if (head <= x0) return;
      var beats = [600, 760, 900];
      function wave(x) {
        for (var i = 0; i < beats.length; i++) {
          var dx = x - beats[i], amp = i === 2 ? 0.35 : 1;
          if (dx > -40 && dx < -24) return -7 * amp * Math.sin((dx + 40) / 16 * Math.PI);
          if (dx >= -10 && dx < -5) return 6 * amp;
          if (dx >= -5 && dx < 0) return -54 * amp * (dx + 5) / 5;
          if (dx >= 0 && dx < 7) return lerp(-54, 20, dx / 7) * amp;
          if (dx >= 7 && dx < 12) return lerp(20, 0, (dx - 7) / 5) * amp;
          if (dx > 22 && dx < 50) return -11 * amp * Math.sin((dx - 22) / 28 * Math.PI);
        }
        return 0;
      }
      ctx.save();
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';
      ctx.lineWidth = 3;
      var flat = t > 2.5;
      var grad = ctx.createLinearGradient(head - 520, 0, head, 0);
      grad.addColorStop(0, flat ? 'rgba(255,90,74,0)' : 'rgba(109,255,176,0)');
      grad.addColorStop(1, flat ? 'rgba(255,90,74,1)' : 'rgba(109,255,176,1)');
      ctx.strokeStyle = grad;
      ctx.shadowColor = flat ? 'rgba(255,90,74,0.9)' : 'rgba(109,255,176,0.9)';
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.moveTo(x0, y0 + wave(x0));
      for (var x = x0 + 2; x <= head; x += 2) ctx.lineTo(x, y0 + wave(x));
      ctx.stroke();
      ctx.restore();
      if (head < x1) {
        additive(ctx, function () { dot(ctx, flat ? '#ff6a5a' : '#8affc0', head, y0 + wave(head), 16, 1); });
      }
    }
  };

  function stampArt(text) {
    var c = document.createElement('canvas');
    c.width = 560; c.height = 150;
    var g = c.getContext('2d');
    g.strokeStyle = g.fillStyle = '#e0352c';
    g.lineWidth = 8;
    roundRect(g, 10, 12, 540, 126, 12); g.stroke();
    g.lineWidth = 3;
    roundRect(g, 24, 26, 512, 98, 8); g.stroke();
    var size = fitSize(g, text, '900 #px ' + HEAVY, 64, 470, 0.08);
    g.font = '900 ' + size + 'px ' + HEAVY;
    g.textBaseline = 'middle'; g.textAlign = 'left';
    spaced(g, text, 280, 78, size * 0.08);
    // worn ink
    g.globalCompositeOperation = 'destination-out';
    for (var i = 0; i < 1100; i++) {
      g.globalAlpha = Math.random() * 0.85;
      var s = Math.random() * 3.2 + 0.6;
      g.fillRect(Math.random() * 560, Math.random() * 150, s, s);
    }
    return c;
  }

  // ============================================================ DOCKS
  var DOCKS = {
    name: 'Blackwater Docks',
    tagline: 'Fog off the water. They come up out of it.',
    cues: [[0.15, 'horn', 0.5], [1.4, 'splash', 0.3], [2.4, 'clang', 0.6],
           [2.45, 'power', 0.4], [3.6, 'groan', 0.3]],
    shakes: [],
    tagY: 516, tagAt: 2.6,
    lamp: [1460, 249],
    setup: function (r) {
      var colours = ['#8a3a2a', '#2f5f8a', '#3a6a3a', '#c8862a', '#6a3a6a', '#5a6a72',
                     '#a8322a', '#2a4a6a'];
      var d = { stars: makeStars(r, 30, 10, 260), streaks: [], fog: [], stacks: [], deck: [],
                waders: [] };
      for (var i = 0; i < 46; i++) {
        d.streaks.push([between(r, 0, VW), between(r, 478, 636), between(r, 30, 140),
                        between(r, 6, 22), r() * 6]);
      }
      for (i = 0; i < 12; i++) {
        d.fog.push([between(r, -200, VW + 200), between(r, 400, 660), between(r, 300, 620),
                    between(r, 40, 100), between(r, 10, 26), between(r, 0.1, 0.2)]);
      }
      var heights = [3, 2, 3, 1, 2];
      for (i = 0; i < 5; i++) {
        for (var h = 0; h < heights[i]; h++) {
          d.stacks.push({ x: 1010 + i * 118, y: 640 - (h + 1) * 54,
                          c: colours[Math.floor(r() * colours.length)] });
        }
      }
      for (i = 0; i < 9; i++) {
        d.deck.push({ x: 130 + i * 58, h: 1 + Math.floor(r() * 2), c: colours[Math.floor(r() * colours.length)] });
      }
      for (i = 0; i < 3; i++) {
        d.waders.push({ x: 760 + i * 84 + between(r, -14, 14), at: 0.7 + i * 0.5 + r() * 0.3,
                        ph: r() * 6, s: between(r, 34, 44) });
      }
      d.lit = null;
      return d;
    },
    beam: function (t) { return 3.49 - 0.75 * Math.max(0, t - 0.3); },
    yard: function (ctx, t, d, lit) {
      // the water
      var water = ctx.createLinearGradient(0, 470, 0, 650);
      water.addColorStop(0, lit ? '#3a5a6e' : '#0e1a26');
      water.addColorStop(1, lit ? '#1e3a4a' : '#08111a');
      ctx.fillStyle = water;
      ctx.fillRect(0, 470, VW, 180);
      ctx.fillStyle = lit ? 'rgba(200,230,240,0.45)' : 'rgba(74,100,120,0.35)';
      d.streaks.forEach(function (s) {
        var x = ((s[0] - t * s[3]) % (VW + 200) + VW + 200) % (VW + 200) - 100;
        ctx.globalAlpha = (0.3 + 0.7 * Math.abs(Math.sin(t * 1.7 + s[4])));
        ctx.fillRect(x, s[1], s[2], 2);
      });
      ctx.globalAlpha = 1;
      // the far breakwater
      ctx.fillStyle = lit ? '#3a4048' : '#0a1018';
      ctx.fillRect(1150, 462, 450, 10);
      // the ship
      ctx.fillStyle = lit ? '#2a3440' : '#0c1219';
      ctx.beginPath();
      ctx.moveTo(30, 556); ctx.lineTo(96, 640); ctx.lineTo(706, 640); ctx.lineTo(724, 556);
      ctx.closePath(); ctx.fill();
      ctx.fillStyle = lit ? '#8a2a22' : '#0c1219';
      ctx.beginPath();
      ctx.moveTo(84, 626); ctx.lineTo(96, 640); ctx.lineTo(706, 640); ctx.lineTo(710, 626);
      ctx.closePath(); ctx.fill();
      if (lit) {
        ctx.font = 'bold 13px ' + FONT;
        ctx.fillStyle = '#e8e4d8';
        ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
        ctx.fillText('BLACKWATER STAR', 120, 584);
      }
      d.deck.forEach(function (c) {
        for (var k = 0; k < c.h; k++) {
          ctx.fillStyle = lit ? c.c : '#0b1117';
          ctx.fillRect(c.x, 520 - k * 34, 54, 34);
        }
      });
      ctx.fillStyle = lit ? '#d8d6cc' : '#111820';
      ctx.fillRect(560, 430, 130, 128);
      ctx.fillRect(548, 424, 154, 10);
      ctx.fillRect(612, 370, 6, 56);
      // the yard
      d.stacks.forEach(function (s) {
        ctx.fillStyle = lit ? s.c : '#0b1117';
        ctx.fillRect(s.x, s.y, 114, 52);
        ctx.fillStyle = lit ? 'rgba(0,0,0,0.25)' : 'rgba(255,255,255,0.03)';
        for (var rib = 6; rib < 114; rib += 9) ctx.fillRect(s.x + rib, s.y + 4, 2, 44);
      });
      // the gantry crane
      ctx.fillStyle = lit ? '#c8a030' : '#0f151c';
      ctx.fillRect(1000, 300, 16, 340); ctx.fillRect(1330, 300, 16, 340);
      ctx.fillRect(700, 300, 690, 22);
      ctx.fillRect(1120, 260, 18, 42);
      ctx.strokeStyle = lit ? '#c8a030' : '#0f151c';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(1129, 262); ctx.lineTo(720, 302); ctx.moveTo(1129, 262); ctx.lineTo(1380, 302);
      ctx.moveTo(840, 322); ctx.lineTo(840, 430); ctx.moveTo(870, 322); ctx.lineTo(870, 430);
      ctx.stroke();
      ctx.fillStyle = lit ? '#8a8a8a' : '#0f151c';
      ctx.fillRect(820, 430, 70, 10);
      // the quay
      ctx.fillStyle = lit ? '#4a4e52' : '#12161b';
      ctx.fillRect(0, 640, VW, VH - 640);
      ctx.fillStyle = lit ? '#6a6e70' : '#1a1f24';
      ctx.fillRect(0, 640, VW, 8);
      [230, 760, 1250].forEach(function (x) {
        ctx.fillStyle = lit ? '#2a2e32' : '#080b0e';
        roundRect(ctx, x - 9, 628, 18, 20, 5); ctx.fill();
      });
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, 470);
      sky.addColorStop(0, '#05090f');
      sky.addColorStop(0.35, '#0a111d');
      sky.addColorStop(1, '#2c3c4a');
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, VW, 472);
      stars(ctx, d.stars, t, 0.45);
      var L = DOCKS.lamp, ang = DOCKS.beam(t), half = 0.085;
      DOCKS.yard(ctx, t, d, false);
      DOCKS.lighthouse(ctx, t);
      // the water reflection of the lamp
      ctx.fillStyle = 'rgba(255,220,140,0.5)';
      for (var y = 482; y < 636; y += 9) {
        var w = 10 + Math.sin(t * 3 + y) * 6 + (y - 482) * 0.12;
        ctx.globalAlpha = 0.25 + 0.25 * Math.sin(t * 4 + y * 0.3);
        ctx.fillRect(L[0] - w / 2, y, w, 2);
      }
      ctx.globalAlpha = 1;
      // whatever is coming up out of the harbour
      d.waders.forEach(function (w) {
        var rise = seg(t, w.at, w.at + 3.5);
        if (rise <= 0) return;
        wader(ctx, w.x, 560, w.s, outCubic(rise), t * 2 + w.ph, '#05080c');
        ctx.strokeStyle = 'rgba(150,180,200,' + (0.35 * (1 - ((t - w.at) * 0.6) % 1)) + ')';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.ellipse(w.x, 562, 14 + ((t - w.at) * 18) % 30, 3 + ((t - w.at) * 4) % 6, 0, 0, TAU);
        ctx.stroke();
      });
      // where the beam falls, the colours come up
      var on = ang > 1.1 && ang < 3.7;
      if (on) {
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(L[0], L[1]);
        ctx.lineTo(L[0] + Math.cos(ang - half) * 2600, L[1] + Math.sin(ang - half) * 2600);
        ctx.lineTo(L[0] + Math.cos(ang + half) * 2600, L[1] + Math.sin(ang + half) * 2600);
        ctx.closePath();
        ctx.clip();
        DOCKS.yard(ctx, t, d, true);
        d.waders.forEach(function (w) {
          var rise = seg(t, w.at, w.at + 3.5);
          if (rise > 0) wader(ctx, w.x, 560, w.s, outCubic(rise), t * 2 + w.ph, '#2a2a26');
        });
        ctx.restore();
      }
      // fog
      d.fog.forEach(function (f, n) {
        if (n > 8) return;
        var x = ((f[0] - t * f[4]) % (VW + 600) + VW + 600) % (VW + 600) - 300;
        dot(ctx, '#9ab0c0', x, f[1], f[2], f[5], f[3]);
      });
      // the container with the name on it, and the floodlight that finds it
      var flood = sputter(t, 2.4, 6);
      DOCKS.container(ctx, t, d, false, 1);
      if (on) {
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(L[0], L[1]);
        ctx.lineTo(L[0] + Math.cos(ang - half) * 2600, L[1] + Math.sin(ang - half) * 2600);
        ctx.lineTo(L[0] + Math.cos(ang + half) * 2600, L[1] + Math.sin(ang + half) * 2600);
        ctx.closePath();
        ctx.clip();
        DOCKS.container(ctx, t, d, true, 1);
        ctx.restore();
      }
      if (flood > 0.5) DOCKS.container(ctx, t, d, true, 0.94);
      DOCKS.floodlight(ctx, t, flood);
      // the beam in the fog
      if (on) {
        additive(ctx, function () {
          var g = ctx.createLinearGradient(L[0], L[1], L[0] + Math.cos(ang) * 1500,
                                           L[1] + Math.sin(ang) * 1500);
          g.addColorStop(0, 'rgba(255,240,200,0.4)');
          g.addColorStop(1, 'rgba(255,240,200,0)');
          ctx.fillStyle = g;
          ctx.beginPath();
          ctx.moveTo(L[0], L[1]);
          ctx.lineTo(L[0] + Math.cos(ang - half) * 2000, L[1] + Math.sin(ang - half) * 2000);
          ctx.lineTo(L[0] + Math.cos(ang + half) * 2000, L[1] + Math.sin(ang + half) * 2000);
          ctx.closePath(); ctx.fill();
        });
      }
      d.fog.forEach(function (f, n) {
        if (n <= 8) return;
        var x = ((f[0] - t * f[4] * 1.6) % (VW + 600) + VW + 600) % (VW + 600) - 300;
        dot(ctx, '#9ab0c0', x, f[1] + 160, f[2], f[5] * 0.7, f[3]);
      });
      // red lights on the crane and the mast
      if ((t * 0.9) % 1 < 0.5) {
        additive(ctx, function () {
          dot(ctx, '#ff3a2a', 1129, 256, 18, 1);
          dot(ctx, '#ff3a2a', 615, 366, 14, 1);
        });
      }
    },
    lighthouse: function (ctx, t) {
      var L = DOCKS.lamp;
      ctx.fillStyle = '#c8c4bc';
      ctx.beginPath();
      ctx.moveTo(L[0] - 17, 470); ctx.lineTo(L[0] - 11, 270); ctx.lineTo(L[0] + 11, 270);
      ctx.lineTo(L[0] + 17, 470); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#a8322a';
      for (var b = 0; b < 3; b++) {
        var y = 300 + b * 56;
        ctx.fillRect(L[0] - 13 - b * 1.2, y, 26 + b * 2.4, 22);
      }
      ctx.fillStyle = '#1a1e24';
      ctx.fillRect(L[0] - 18, 262, 36, 8);
      ctx.fillStyle = '#ffe8a8';
      ctx.fillRect(L[0] - 10, 238, 20, 24);
      ctx.fillStyle = '#1a1e24';
      ctx.beginPath(); ctx.moveTo(L[0] - 13, 238); ctx.lineTo(L[0], 222); ctx.lineTo(L[0] + 13, 238);
      ctx.closePath(); ctx.fill();
      additive(ctx, function () { dot(ctx, '#ffe0a0', L[0], L[1], 90, 0.8); });
    },
    container: function (ctx, t, d, lit, alpha) {
      var x = 360, y = 560, w = 880, h = 300;
      ctx.save();
      ctx.globalAlpha *= alpha;
      ctx.fillStyle = lit ? '#7a2e22' : '#120d0c';
      ctx.fillRect(x, y, w, h);
      ctx.fillStyle = lit ? 'rgba(0,0,0,0.22)' : 'rgba(255,255,255,0.025)';
      for (var rib = 14; rib < w; rib += 22) ctx.fillRect(x + rib, y + 14, 6, h - 28);
      ctx.fillStyle = lit ? '#5a2018' : '#0a0807';
      ctx.fillRect(x, y, w, 14); ctx.fillRect(x, y + h - 14, w, 14);
      ctx.fillRect(x, y, 16, h); ctx.fillRect(x + w - 16, y, 16, h);
      if (!d.lit) {
        var name = DOCKS.current || DOCKS.name;
        d.lit = stencil(split(name.toUpperCase()), 760, '#efe6d0');
        d.dark = stencil(split(name.toUpperCase()), 760, '#2e2622');
      }
      var art = lit ? d.lit : d.dark;
      ctx.drawImage(art, x + w / 2 - art.width / 2, y + 30 + (h - 60 - art.height) / 2);
      ctx.font = 'bold 18px ' + FONT;
      ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
      ctx.fillStyle = lit ? 'rgba(239,230,208,0.8)' : 'rgba(60,50,46,0.8)';
      ctx.fillText('BWDU 447120  2', x + 30, y + 34);
      ctx.font = 'bold 12px ' + FONT;
      ctx.fillText('MAX GROSS 30,480 KG', x + 30, y + h - 30);
      ctx.restore();
    },
    floodlight: function (ctx, t, on) {
      ctx.fillStyle = '#0a0d10';
      ctx.fillRect(296, 470, 8, VH - 470);
      ctx.save();
      ctx.translate(300, 470);
      ctx.rotate(0.6);
      ctx.fillRect(-20, -12, 40, 24);
      ctx.fillStyle = on > 0.5 ? '#fff4d0' : '#2a2a28';
      ctx.fillRect(14, -9, 6, 18);
      ctx.restore();
      if (on > 0.5) {
        additive(ctx, function () {
          dot(ctx, '#ffd28a', 700, 690, 620, 0.22, 300);
          dot(ctx, '#ffe8b0', 318, 486, 54, 1);
        });
      }
    },
    title: function () {}
  };

  // the name on a container, cut like a stencil and worn by the weather
  function stencil(lines, width, paint) {
    var c = document.createElement('canvas');
    var g = c.getContext('2d');
    var family = '900 #px ' + HEAVY;
    var size = 140;
    lines.forEach(function (line) { size = Math.min(size, fitSize(g, line, family, 140, width, 0.05)); });
    size = Math.min(size, Math.floor(220 / lines.length));
    var lh = size * 1.05;
    c.width = width;
    c.height = Math.ceil(lh * lines.length + 8);
    g.font = family.replace('#', size);
    g.textBaseline = 'middle'; g.textAlign = 'left';
    g.fillStyle = paint;
    lines.forEach(function (line, n) {
      var y = lh * (n + 0.5) + 4;
      var l = spaced(g, line, width / 2, y, size * 0.05);
      g.globalCompositeOperation = 'destination-out';
      l.chars.forEach(function (ch) {
        if ('ABDOPQR04689'.indexOf(ch.ch) < 0) return;
        g.fillRect(l.left + ch.x + ch.w * 0.44, y - size * 0.6, size * 0.07, size * 1.2);
      });
      g.globalCompositeOperation = 'source-over';
    });
    g.globalCompositeOperation = 'destination-out';
    for (var i = 0; i < 700; i++) {
      g.globalAlpha = Math.random() * 0.7;
      var s = Math.random() * 4 + 1;
      g.fillRect(Math.random() * c.width, Math.random() * c.height, s, s * 0.6);
    }
    return c;
  }

  // ============================================================= CAMP
  var CAMP = {
    name: 'Cedar Pines Camp',
    tagline: 'The last hour of the sun. They come out of the old mine.',
    cues: [[0.3, 'dinner', 0.4], [1.0, 'loon', 0.55], [1.62, 'thunk', 0.5],
           [2.6, 'scratch', 0.55], [3.5, 'growl', 0.25]],
    shakes: [[1.68, 6, 0.3], [2.62, 4, 0.25]],
    tagY: 452, tagAt: 2.1,
    setup: function (r) {
      var d = { stars: makeStars(r, 26, 10, 200), clouds: [], hills: [], shore: [], bats: [],
                flies: [], trees: [] };
      for (var i = 0; i < 6; i++) {
        d.clouds.push([between(r, 0, VW + 600), between(r, 380, 520), between(r, 220, 560),
                       between(r, 5, 12), between(r, 4, 10)]);
      }
      for (var x = -40; x <= VW + 40; x += 40) d.hills.push([x, CAMP.shore(x) - between(r, 0, 10)]);
      for (i = 0; i < 70; i++) d.shore.push([between(r, 330, VW), between(r, 16, 38)]);
      for (i = 0; i < 6; i++) {
        d.bats.push({ x: between(r, -100, 700), y: between(r, 120, 360), vx: between(r, 80, 160),
                      ph: r() * 6, s: between(r, 0.9, 1.4) });
      }
      for (i = 0; i < 52; i++) {
        d.flies.push({ x: between(r, 0, VW), y: between(r, 600, 880), ph: r() * 6,
                       w: between(r, 1.2, 2.6), at: between(r, 0.6, 3.2) });
      }
      d.trees = [[-40, 700, 2.2], [70, 820, 0.3], [190, 900, 1.1],
                 [1330, 600, 2.8], [1440, 860, 0.7], [1560, 760, 1.9], [1650, 640, 0.2]];
      return d;
    },
    // the far shore: a hill each side and a low gap the sun goes down in
    shore: function (x) {
      return 588 - 72 * Math.exp(-Math.pow((x - 300) / 260, 2)) -
        92 * Math.exp(-Math.pow((x - 1300) / 240, 2));
    },
    draw: function (ctx, t, d) {
      var HZ = 548;
      var dusk = seg(t, 0, TOTAL) * 0.35;
      var sky = ctx.createLinearGradient(0, 0, 0, HZ);
      sky.addColorStop(0, mix('#241f4a', '#16142e', dusk));
      sky.addColorStop(0.38, mix('#35366a', '#262650', dusk));
      sky.addColorStop(0.76, mix('#b0607a', '#8a4a68', dusk));
      sky.addColorStop(1, mix('#f0a060', '#d8804e', dusk));
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, VW, HZ + 2);
      stars(ctx, d.stars, t, 0.25 + dusk);
      var sunY = 548 + t * 7;
      additive(ctx, function () { dot(ctx, '#ff9050', 820, sunY, 460, 0.55, 300); });
      var sun = ctx.createLinearGradient(0, sunY - 120, 0, sunY + 40);
      sun.addColorStop(0, '#ffe2a0');
      sun.addColorStop(1, '#ff8a4a');
      ctx.fillStyle = sun;
      ctx.beginPath(); ctx.arc(820, sunY, 118, 0, TAU); ctx.fill();
      bands(ctx, d.clouds, t, 'rgba(90,58,106,0.7)');
      // bats
      d.bats.forEach(function (b) {
        var x = b.x + b.vx * t + Math.sin(t * 3 + b.ph) * 30;
        var y = b.y + Math.sin(t * 5 + b.ph) * 14 + Math.cos(t * 2.3 + b.ph) * 10;
        bat(ctx, x, y, b.s, t * 22 + b.ph);
      });
      // the far shore, the lookout on its hill, the ridge and the mine
      ctx.fillStyle = '#3a2848';
      ctx.beginPath(); ctx.moveTo(0, 600);
      d.hills.forEach(function (p) { ctx.lineTo(p[0], p[1]); });
      ctx.lineTo(VW, 600); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#2a1c38';
      d.shore.forEach(function (p) {
        pineIcon(ctx, p[0], CAMP.shore(p[0]) - p[1] * 0.5 + 4, p[1], '#2a1c38');
      });
      ctx.fillStyle = '#2a1c38';
      ctx.fillRect(1232, 400, 5, 110); ctx.fillRect(1271, 400, 5, 110);
      ctx.strokeStyle = '#2a1c38'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(1234, 420); ctx.lineTo(1273, 500); ctx.moveTo(1273, 420);
      ctx.lineTo(1234, 500); ctx.stroke();
      ctx.fillRect(1222, 372, 64, 30);
      ctx.beginPath(); ctx.moveTo(1216, 374); ctx.lineTo(1254, 350); ctx.lineTo(1292, 374);
      ctx.closePath(); ctx.fill();
      ctx.fillStyle = 'rgba(255,190,110,' + (0.5 * buzz(t * 0.6, 4)) + ')';
      ctx.fillRect(1240, 380, 10, 8);
      ctx.fillStyle = '#2e2140';
      ctx.beginPath(); ctx.moveTo(0, 600); ctx.lineTo(0, 380); ctx.lineTo(90, 380);
      ctx.lineTo(90, 420); ctx.lineTo(170, 420); ctx.lineTo(170, 462); ctx.lineTo(250, 462);
      ctx.lineTo(250, 500); ctx.lineTo(340, 500); ctx.lineTo(340, 600); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#07040c';
      ctx.beginPath(); ctx.moveTo(262, 600); ctx.lineTo(262, 552); ctx.arc(292, 552, 30, Math.PI, 0);
      ctx.lineTo(322, 600); ctx.closePath(); ctx.fill();
      var blink = Math.sin(t * 1.7) > -0.85 ? 1 : 0;
      additive(ctx, function () {
        dot(ctx, '#ff4a2a', 284, 566, 4, 0.9 * blink * seg(t, 1.2, 2));
        dot(ctx, '#ff4a2a', 293, 566, 4, 0.9 * blink * seg(t, 1.2, 2));
        dot(ctx, '#ff4a2a', 306, 574, 3.5, 0.8 * seg(t, 2.4, 3.2));
        dot(ctx, '#ff4a2a', 313, 574, 3.5, 0.8 * seg(t, 2.4, 3.2));
      });
      // the lake, and the sun on it
      var lake = ctx.createLinearGradient(0, 590, 0, VH);
      lake.addColorStop(0, '#d88a60');
      lake.addColorStop(0.4, '#6a4a70');
      lake.addColorStop(1, '#1a1636');
      ctx.fillStyle = lake;
      ctx.fillRect(0, 596, VW, VH - 596);
      ctx.fillStyle = '#2e2140';
      ctx.fillRect(0, 590, VW, 8);
      for (var y = 604; y < 880; y += 9) {
        var k = (y - 604) / 276;
        var w = (190 - k * 120) * (0.6 + 0.4 * Math.sin(t * 2.2 + y * 0.13));
        ctx.fillStyle = 'rgba(255,208,138,' + (0.6 - k * 0.5) + ')';
        ctx.fillRect(820 + Math.sin(t * 1.3 + y * 0.07) * 8 - w / 2, y, w, 2.5);
      }
      // the island, the raft, a canoe nobody is in
      ctx.fillStyle = '#1e1530';
      roundRect(ctx, 1010, 612, 180, 16, 8); ctx.fill();
      pineIcon(ctx, 1050, 590, 30, '#1e1530'); pineIcon(ctx, 1090, 584, 40, '#1e1530');
      pineIcon(ctx, 1140, 594, 26, '#1e1530');
      ctx.fillRect(560, 660, 70, 8);
      var cx = 1040 + t * 7;
      ctx.beginPath(); ctx.moveTo(cx - 60, 700); ctx.quadraticCurveTo(cx, 716, cx + 60, 700);
      ctx.lineTo(cx + 50, 708); ctx.quadraticCurveTo(cx, 718, cx - 50, 708); ctx.closePath(); ctx.fill();
      ctx.fillStyle = 'rgba(30,21,48,0.35)';
      ctx.fillRect(cx - 54, 716, 108, 4);
      // the dock and the boathouse
      ctx.fillStyle = '#140e20';
      ctx.fillRect(0, 740, 440, 16);
      for (var p = 0; p < 6; p++) ctx.fillRect(20 + p * 80, 756, 9, 40);
      ctx.fillRect(40, 610, 220, 132);
      ctx.beginPath(); ctx.moveTo(26, 614); ctx.lineTo(150, 556); ctx.lineTo(274, 614); ctx.closePath(); ctx.fill();
      var lantern = 0.6 + 0.4 * Math.sin(t * 8) * Math.sin(t * 3.1);
      ctx.fillStyle = 'rgba(255,190,100,' + lantern + ')';
      ctx.fillRect(140, 660, 12, 14);
      additive(ctx, function () { dot(ctx, '#ffb060', 146, 667, 70, lantern * 0.6); });
      // the pines up close, swaying
      d.trees.forEach(function (tree) {
        pine(ctx, tree[0], VH + 20, tree[1], '#0e0a16', Math.sin(t * 1.1 + tree[2]) * 0.018);
      });
      // fireflies
      additive(ctx, function () {
        d.flies.forEach(function (f) {
          var a = seg(t, f.at, f.at + 0.8) * Math.pow(Math.max(0, Math.sin(t * f.w + f.ph)), 3);
          if (a <= 0.02) return;
          var x = f.x + Math.sin(t * 0.7 + f.ph) * 14, y = f.y + Math.cos(t * 0.9 + f.ph) * 9;
          dot(ctx, '#ffe98a', x, y, 12, a);
          dot(ctx, '#fffbe0', x, y, 2.5, a);
        });
      });
    },
    title: function (ctx, t, d, run) {
      var name = (run.info.name || CAMP.name).toUpperCase();
      var drop = outBack(seg(t, 1.0, 1.66), 1.45);
      var cy = lerp(-300, 258, drop);
      var swing = wobble(t, 1.66, 0.08, 6, 1.5) + wobble(t, 2.6, 0.03, 15, 4) -
        0.06 * (1 - seg(t, 1.0, 1.66));
      var hw = 460, hh = 84;
      var px = 800, py = cy - 160;            // it swings from above
      function at(x, y) {
        var dx = x - px, dy = y - py;
        return [px + dx * Math.cos(swing) - dy * Math.sin(swing),
                py + dx * Math.sin(swing) + dy * Math.cos(swing)];
      }
      var a = at(800 - 380, cy - hh), b = at(800 + 380, cy - hh);
      chain(ctx, 800 - 400, -30, a[0], a[1]);
      chain(ctx, 800 + 400, -30, b[0], b[1]);
      ctx.save();
      ctx.translate(px, py);
      ctx.rotate(swing);
      ctx.translate(800 - px, cy - py);
      // the planks
      var colours = ['#7a4a26', '#6c4022', '#845030'];
      for (var p = 0; p < 3; p++) {
        var y = -hh + p * 57;
        ctx.fillStyle = colours[p];
        ctx.fillRect(-hw, y, hw * 2, 54);
        ctx.strokeStyle = 'rgba(40,20,8,0.35)';
        ctx.lineWidth = 1.5;
        for (var g2 = 0; g2 < 3; g2++) {
          ctx.beginPath();
          for (var x = -hw; x <= hw; x += 20) {
            var gy = y + 12 + g2 * 14 + Math.sin(x * 0.02 + p * 3 + g2) * 3;
            if (x === -hw) ctx.moveTo(x, gy); else ctx.lineTo(x, gy);
          }
          ctx.stroke();
        }
        ctx.fillStyle = '#2a1a10';
        [-hw + 14, hw - 14].forEach(function (nx) {
          ctx.beginPath(); ctx.arc(nx, y + 27, 4, 0, TAU); ctx.fill();
        });
      }
      ctx.strokeStyle = '#3a2210';
      ctx.lineWidth = 6;
      ctx.strokeRect(-hw, -hh, hw * 2, 168);
      // the name, painted
      var size = fitSize(ctx, name, 'bold #px ' + FONT, 64, 760, 0.08);
      ctx.font = 'bold ' + size + 'px ' + FONT;
      ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
      ctx.fillStyle = '#2a1408';
      var l = spaced(ctx, name, 0, 4, size * 0.08);
      ctx.fillStyle = '#f4e6c8';
      spaced(ctx, name, -1, 0, size * 0.08);
      pineIcon(ctx, l.left - 44, -10, 44, '#2f4a2e');
      pineIcon(ctx, l.left + l.width + 44, -10, 44, '#2f4a2e');
      // something went at it
      var claw = seg(t, 2.6, 2.78);
      if (claw > 0) {
        for (var c = 0; c < 4; c++) {
          var x0 = 250 + c * 24, y0 = -76, x1 = 120 + c * 24, y1 = 70;
          var ex = lerp(x0, x1, claw), ey = lerp(y0, y1, claw);
          var mx = (x0 + ex) / 2 + 7, my = (y0 + ey) / 2;
          ctx.lineCap = 'round';
          ctx.lineJoin = 'round';
          ctx.strokeStyle = '#24110a'; ctx.lineWidth = 13;
          ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(mx, my); ctx.lineTo(ex, ey); ctx.stroke();
          ctx.strokeStyle = '#d29a66'; ctx.lineWidth = 5;
          ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(mx, my); ctx.lineTo(ex, ey); ctx.stroke();
        }
      }
      // and a plank hung under it
      var tilt = 0.14 + wobble(t, 1.66, 0.12, 8, 1.8);
      ctx.save();
      ctx.translate(-150, hh);
      ctx.strokeStyle = '#4a4650'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 22); ctx.stroke();
      ctx.translate(0, 22);
      ctx.rotate(tilt);
      ctx.fillStyle = '#d8c8a0';
      ctx.fillRect(-110, 0, 220, 50);
      ctx.strokeStyle = '#6a5a40'; ctx.lineWidth = 3;
      ctx.strokeRect(-110, 0, 220, 50);
      ctx.font = '900 30px ' + HEAVY;
      ctx.fillStyle = '#b8281a';
      spaced(ctx, 'CLOSED', 0, 26, 4);
      ctx.restore();
      ctx.restore();
    }
  };

  var SCENES = { town: TOWN, hospital: HOSPITAL, docks: DOCKS, camp: CAMP };

  // ======================================================== the frame
  var grainCanvas = null;
  function grain(ctx, W, H, t) {
    if (!grainCanvas) {
      grainCanvas = document.createElement('canvas');
      grainCanvas.width = grainCanvas.height = 128;
      var g = grainCanvas.getContext('2d');
      var img = g.createImageData(128, 128);
      for (var i = 0; i < img.data.length; i += 4) {
        var v = Math.random() * 255;
        img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
        img.data[i + 3] = 18;
      }
      g.putImageData(img, 0, 0);
    }
    ctx.save();
    ctx.translate(-((t * 997) % 128), -((t * 613) % 128));
    ctx.fillStyle = ctx.createPattern(grainCanvas, 'repeat');
    ctx.fillRect(0, 0, W + 128, H + 128);
    ctx.restore();
  }

  function lampIcon(ctx, x, y, s, lit) {
    ctx.strokeStyle = lit ? '#c9a46a' : '#6a5a48';
    ctx.lineWidth = 1.6 * s;
    roundRect(ctx, x - 6 * s, y - 8 * s, 12 * s, 17 * s, 3 * s);
    ctx.stroke();
    ctx.beginPath(); ctx.arc(x, y - 9 * s, 4 * s, Math.PI, 0); ctx.stroke();
    if (lit) additive(ctx, function () { dot(ctx, '#ffc04a', x, y + 1 * s, 10 * s, 1); });
  }

  // the black bars, and what they say
  function chrome(ctx, t, W, H, run) {
    var k = outCubic(seg(t, 0.05, 0.6)) * (1 - inOut(seg(t, CLOSE, CLOSE + 0.9)));
    var bar = Math.round(H * 0.105 * k);
    if (bar <= 0) return;
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, W, bar);
    ctx.fillRect(0, H - bar, W, bar);
    var a = seg(t, 0.6, 1.1) * (1 - seg(t, CLOSE - 0.3, CLOSE + 0.2));
    if (a <= 0) return;
    var s = Math.min(W / VW, H / VH);
    var info = run.info;
    ctx.save();
    ctx.globalAlpha = a;
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';
    ctx.font = 'bold ' + Math.round(15 * s) + 'px ' + FONT;
    ctx.fillStyle = '#ff8a6a';
    spaced(ctx, info.kicker || 'NEW LOCATION', W / 2, bar / 2, 8 * s);
    var by = H - bar / 2;
    ctx.font = 'bold ' + Math.round(14 * s) + 'px ' + FONT;
    ctx.fillStyle = '#ffd27a';
    var round = 'ROUND ' + (info.round || 1);
    var lr = layout(ctx, round, 4 * s);
    spaced(ctx, round, 40 * s + lr.width / 2, by, 4 * s);
    var tries = info.tries || 3;
    var left = Math.max(0, tries - ((info.attempt || 1) - 1));
    var line = (left === tries ? tries + ' TRIES TO HOLD IT' : left + ' OF ' + tries +
                ' TRIES LEFT') + '  ·  GET READY';
    var ll = layout(ctx, line, 3 * s);
    var x0 = W / 2 - (tries * 22 * s + 12 * s + ll.width) / 2;
    for (var i = 0; i < tries; i++) lampIcon(ctx, x0 + 6 * s + i * 22 * s, by, s, i >= tries - left);
    ctx.fillStyle = '#f4e6c8';
    spaced(ctx, line, x0 + tries * 22 * s + 12 * s + ll.width / 2, by, 3 * s);
    ctx.fillStyle = '#ffd27a';
    var logo = 'LAST LIGHT';
    var lg = layout(ctx, logo, 6 * s);
    spaced(ctx, logo, W - 40 * s - lg.width / 2, by, 6 * s);
    additive(ctx, function () {
      dot(ctx, '#ffb040', W - 52 * s - lg.width, by, 11 * s, 0.6 + 0.4 * Math.sin(t * 13));
    });
    ctx.restore();
  }

  function tagline(ctx, t, run) {
    var text = run.info.tagline || run.scene.tagline;
    if (!text) return;
    var at = run.scene.tagAt || 2;
    var n = Math.floor(text.length * seg(t, at, at + text.length * 0.028));
    if (n <= 0) return;
    ctx.save();
    ctx.font = 'italic bold 21px ' + FONT;
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';
    var full = ctx.measureText(text).width;
    var x = VW / 2 - full / 2, y = run.scene.tagY || 560;
    ctx.shadowColor = 'rgba(0,0,0,0.95)';
    ctx.shadowBlur = 10;
    ctx.fillStyle = '#f4e6c8';
    var shown = text.slice(0, n);
    ctx.fillText(shown, x, y);
    if (n < text.length && Math.floor(t * 8) % 2 === 0) {
      ctx.fillStyle = '#ffd27a';
      ctx.fillRect(x + ctx.measureText(shown).width + 3, y - 11, 3, 22);
    }
    ctx.restore();
  }

  function shakeAt(t, shakes) {
    var x = 0, y = 0;
    (shakes || []).forEach(function (s) {
      var k = (t - s[0]) / s[2];
      if (k < 0 || k > 1) return;
      var amp = s[1] * (1 - k) * (1 - k);
      x += Math.sin(t * 91) * amp;
      y += Math.cos(t * 77) * amp;
    });
    return [x, y];
  }

  // one frame, at time t, onto a canvas W x H
  function paint(run, t) {
    var ctx = run.ctx, W = run.canvas.width, H = run.canvas.height;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = 1;
    ctx.shadowBlur = 0;
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, W, H);
    var shake = shakeAt(t, run.scene.shakes);
    var cover = Math.max(W / VW, H / VH) * (1 + 0.06 * inOut(seg(t, 0, TOTAL)));
    ctx.save();
    ctx.translate(W / 2 + shake[0], H / 2 + shake[1]);
    ctx.scale(cover, cover);
    ctx.translate(-VW / 2, -VH / 2);
    DOCKS.current = run.info.name;
    run.scene.draw(ctx, t, run.data, run);
    ctx.restore();
    var light = sputter(t, 0.02, 1);
    if (light < 1) {
      ctx.fillStyle = 'rgba(0,0,0,' + (1 - light) + ')';
      ctx.fillRect(0, 0, W, H);
    }
    // the title, fitted rather than cropped
    var fit = Math.min(W / VW, H / VH);
    run.alpha = 1 - seg(t, CLOSE, CLOSE + 0.55);
    ctx.save();
    ctx.translate(W / 2 + shake[0], H / 2 + shake[1]);
    ctx.scale(fit, fit);
    ctx.translate(-VW / 2, -VH / 2);
    ctx.globalAlpha = run.alpha;
    run.scene.title(ctx, t, run.data, run);
    ctx.globalAlpha = run.alpha;
    tagline(ctx, t, run);
    ctx.restore();
    // vignette and grain
    if (!run.vignette || run.vignette.w !== W || run.vignette.h !== H) {
      var v = ctx.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.35, W / 2, H / 2,
                                       Math.sqrt(W * W + H * H) / 2);
      v.addColorStop(0, 'rgba(0,0,0,0)');
      v.addColorStop(1, 'rgba(0,0,0,0.62)');
      run.vignette = { w: W, h: H, g: v };
    }
    ctx.fillStyle = run.vignette.g;
    ctx.fillRect(0, 0, W, H);
    grain(ctx, W, H, t);
    chrome(ctx, t, W, H, run);
    // the ring of light opening onto the game
    if (t > CLOSE) {
      var k = inOut(seg(t, CLOSE, TOTAL));
      var R = Math.sqrt(W * W + H * H) / 2 * 1.12 * k;
      var soft = Math.max(20, Math.min(W, H) * 0.08);
      ctx.save();
      ctx.globalCompositeOperation = 'destination-out';
      var hole = ctx.createRadialGradient(W / 2, H / 2, Math.max(0, R - soft), W / 2, H / 2, R + 1);
      hole.addColorStop(0, 'rgba(0,0,0,1)');
      hole.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = hole;
      ctx.fillRect(0, 0, W, H);
      ctx.globalCompositeOperation = 'lighter';
      var ring = ctx.createRadialGradient(W / 2, H / 2, Math.max(0, R - soft * 1.2), W / 2, H / 2,
                                          R + soft * 0.6);
      ring.addColorStop(0, 'rgba(255,214,140,0)');
      ring.addColorStop(0.6, 'rgba(255,214,140,' + (0.55 * (1 - k)) + ')');
      ring.addColorStop(1, 'rgba(255,214,140,0)');
      ctx.fillStyle = ring;
      ctx.fillRect(0, 0, W, H);
      ctx.restore();
    }
  }

  // ========================================================= playback
  var current = null;

  function stop() {
    var run = current;
    current = null;
    if (!run) return;
    cancelAnimationFrame(run.raf);
    window.removeEventListener('keydown', run.onKey, true);
    if (run.root && run.root.parentNode) run.root.parentNode.removeChild(run.root);
  }

  function makeRun(areaId, info, canvas, seed) {
    var scene = SCENES[areaId];
    if (!scene) return null;
    var run = { scene: scene, info: info || {}, canvas: canvas, ctx: canvas.getContext('2d'),
                cues: (scene.cues || []).slice(), skip: 0, alpha: 1 };
    run.data = scene.setup(rng(seed));
    return run;
  }

  /* Play the arrival at ``areaId``.  ``info``: name, round, attempt, tries
     (and optionally kicker, tagline).  Returns false if there is no scene. */
  function play(areaId, info, audio) {
    stop();
    if (!SCENES[areaId]) return false;
    var host = document.querySelector('#game-root .hud') || document.body;
    var root = document.createElement('div');
    root.id = 'll-intro';
    var canvas = document.createElement('canvas');
    root.appendChild(canvas);
    host.appendChild(root);
    var run = makeRun(areaId, info, canvas, (Date.now() ^ Math.floor(Math.random() * 1e9)) >>> 0);
    run.root = root;
    run.audio = audio;
    run.start = performance.now();
    run.onKey = function (event) {
      var t = (performance.now() - run.start) / 1000 + run.skip;
      if (t > 0.8 && t < CLOSE &&
          (event.code === 'Space' || event.code === 'Enter' || event.code === 'Escape')) {
        run.skip += CLOSE - t;
        run.cues = run.cues.filter(function (c) { return c[0] >= CLOSE; });
      }
    };
    window.addEventListener('keydown', run.onKey, true);
    current = run;
    function frame(now) {
      if (current !== run) return;
      var t = (now - run.start) / 1000 + run.skip;
      if (t >= TOTAL) { stop(); return; }
      var dpr = Math.min(1.5, window.devicePixelRatio || 1);
      var w = Math.max(1, Math.round(root.clientWidth * dpr));
      var h = Math.max(1, Math.round(root.clientHeight * dpr));
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
      while (run.cues.length && run.cues[0][0] <= t) {
        var cue = run.cues.shift();
        if (run.audio) run.audio.play(cue[1], { volume: cue[2] });
      }
      paint(run, t);
      run.raf = requestAnimationFrame(frame);
    }
    run.raf = requestAnimationFrame(frame);
    return true;
  }

  /* Paint a single frame (for previews and tests): the scene for ``areaId``
     at ``t`` seconds onto ``canvas``, always the same for the same seed. */
  function still(canvas, areaId, t, info, seed) {
    var run = makeRun(areaId, info, canvas, seed || 7);
    if (!run) return false;
    paint(run, t);
    return true;
  }

  // ================================================ the shuffle, the tries
  var ACCENT = { town: '#e48c5c', hospital: '#7ab4e8', docks: '#5ab4a8', camp: '#f0a060' };

  function esc(text) {
    return String(text).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  /* The three lamps: one goes out for every wipe at this place.  ``fresh``
     blows the newest one out in front of you. */
  function lamps(out, tries, fresh) {
    var html = '<span class="ll-lamps">';
    for (var i = 0; i < tries; i++) {
      var cls = i < out ? (fresh && i === out - 1 ? 'going' : 'out') : 'lit';
      html += '<span class="ll-lamp ' + cls + '"><i></i></span>';
    }
    return html + '</span>';
  }

  /* The reel: every area's name round a slot window, spun after ``delay`` ms
     and slowing to a stop on ``nextId``.  ``done`` runs when it lands. */
  function reel(node, items, nextId, audio, delay, done) {
    if (!node || !items || !items.length) return null;
    var ROW = 54, LOOPS = 7;
    var index = 0;
    items.forEach(function (it, i) { if (it.id === nextId) index = i; });
    var strip = [];
    for (var l = 0; l < LOOPS; l++) strip = strip.concat(items);
    var target = (LOOPS - 1) * items.length + index;
    node.className = 'll-reel';
    node.innerHTML = '<div class="ll-reel-k">SHUFFLING THE SERVER</div>' +
      '<div class="ll-reel-win"><div class="ll-reel-strip">' + strip.map(function (it, i) {
        return '<div class="ll-reel-item' + (i === target ? ' target' : '') +
          '" style="--a:' + (ACCENT[it.id] || '#ffd27a') + '"><i></i>' + esc(it.name) + '</div>';
      }).join('') + '</div></div>';
    var stripNode = node.querySelector('.ll-reel-strip');
    var win = node.querySelector('.ll-reel-win');
    var start = Math.floor(Math.random() * items.length);
    var spin = 3.3;
    var state = { raf: 0, timer: 0, stopped: false };
    function place(pos) { stripNode.style.transform = 'translateY(' + (-pos * ROW).toFixed(1) + 'px)'; }
    place(start);
    var began = 0, lastRow = start, lastSound = 0;
    function frame(now) {
      if (state.stopped) return;
      if (!began) began = now;
      var k = Math.min(1, (now - began) / 1000 / spin);
      var pos = start + (target - start) * (1 - Math.pow(1 - k, 4));
      place(pos);
      var speed = (target - start) * 4 * Math.pow(1 - k, 3) / spin;
      stripNode.style.filter = speed > 10 ? 'blur(' + Math.min(2.4, speed / 12).toFixed(1) + 'px)' : 'none';
      var row = Math.floor(pos + 0.5);
      if (row !== lastRow) {
        lastRow = row;
        if (audio && now - lastSound > 45) { lastSound = now; audio.play('tick', { volume: 0.55 }); }
      }
      if (k >= 1) {
        win.classList.add('landed');
        node.classList.add('landed');
        node.querySelector('.ll-reel-k').textContent = 'NOW ENTERING';
        if (audio) audio.play('land', { volume: 0.6 });
        if (done) done();
        return;
      }
      state.raf = requestAnimationFrame(frame);
    }
    state.timer = setTimeout(function () {
      if (state.stopped) return;
      if (audio) audio.play('whoosh', { volume: 0.4 });
      state.raf = requestAnimationFrame(frame);
    }, delay || 0);
    return {
      stop: function () {
        state.stopped = true;
        clearTimeout(state.timer);
        cancelAnimationFrame(state.raf);
      }
    };
  }

  global.AreaIntro = {
    play: play, stop: stop, still: still, lamps: lamps, reel: reel,
    has: function (areaId) { return !!SCENES[areaId]; },
    playing: function () { return !!current; },
    DURATION: TOTAL
  };
})(window);
