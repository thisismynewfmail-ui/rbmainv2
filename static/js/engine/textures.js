/* BLOCKHAVEN engine -- every texture in the project is drawn at runtime on a
   2D canvas, so the whole platform ships without a single image asset. */
(function (global) {
  'use strict';

  var CELL = 128;
  /* 16x16 cells -> a 2048x2048 atlas.  It was 10x10, which every decal
     painter (they are all prewarmed), every face, and a Last Light area's
     signage had to share -- and an overflowing atlas recycles cells, so the
     next thing painted lands on top of something still in use.  2048 is a
     power of two and inside every WebGL implementation's texture limit. */
  var GRID = 16;
  var SIZE = CELL * GRID;

  var Textures = {
    atlasCanvas: null,
    slots: {},                  // name -> {u, v, s}
    nextSlot: 1,                // slot 0 is a plain white square
    version: 0,
    changes: []                 // {v, x, y}: which cell each version painted
  };

  /* Re-sending the whole 2048x2048 atlas (16 MB, then its mipmaps) every time
     one cell is painted -- a face for somebody who just joined, the signage
     of the area a round moved to -- stalled a frame for every paint, and an
     area change paints dozens.  So every paint is logged by cell, and a
     renderer that is only a few versions behind sends just those cells
     (uploadAtlas).  The log is short; one that has fallen further behind
     than it reaches gets the whole atlas, as before. */
  var CHANGE_LOG = 256;
  var MAX_CELL_UPLOADS = 96;

  function painted(slot) {
    Textures.version++;
    Textures.changes.push({ v: Textures.version, x: slot.x, y: slot.y });
    if (Textures.changes.length > CHANGE_LOG) {
      Textures.changes.splice(0, Textures.changes.length - CHANGE_LOG);
    }
  }

  function ensureCanvas() {
    if (Textures.atlasCanvas) return Textures.atlasCanvas;
    var canvas = document.createElement('canvas');
    canvas.width = SIZE;
    canvas.height = SIZE;
    // painted a cell at a time and read back a cell at a time (uploadAtlas)
    var ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.clearRect(0, 0, SIZE, SIZE);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, CELL, CELL);
    Textures.atlasCanvas = canvas;
    Textures.ctx = ctx;
    return canvas;
  }

  function allocate(name) {
    if (Textures.slots[name]) return Textures.slots[name];
    // a cell given back (a sign from an area no longer being played) is
    // used again before the atlas grows into recycling live artwork
    var index = (Textures.freeCells && Textures.freeCells.length) ? Textures.freeCells.pop()
      : Textures.nextSlot++;
    // slot 0 is the plain white square every untextured part samples, so an
    // overflowing atlas recycles cells from 1 upwards rather than stamping
    // artwork over it.
    if (index >= GRID * GRID) index = 1 + ((index - 1) % (GRID * GRID - 1));
    var cx = (index % GRID), cy = Math.floor(index / GRID);
    var slot = { u: cx / GRID, v: cy / GRID, s: 1 / GRID, x: cx * CELL, y: cy * CELL,
                 index: index };
    Textures.slots[name] = slot;
    return slot;
  }

  function cellContext(slot, background) {
    ensureCanvas();
    var ctx = Textures.ctx;
    ctx.save();
    ctx.beginPath();
    ctx.rect(slot.x, slot.y, CELL, CELL);
    ctx.clip();
    ctx.clearRect(slot.x, slot.y, CELL, CELL);
    if (background) {
      ctx.fillStyle = background;
      ctx.fillRect(slot.x, slot.y, CELL, CELL);
    }
    ctx.translate(slot.x, slot.y);
    return ctx;
  }

  // --------------------------------------------------------------- faces
  Textures.drawFace = function (name, shapes) {
    var key = 'face:' + name;
    if (Textures.slots[key]) return Textures.slots[key];
    var slot = allocate(key);
    var ctx = cellContext(slot, null);
    var cx = CELL / 2, cy = CELL / 2, S = CELL;
    (shapes || []).forEach(function (shape) {
      ctx.save();
      ctx.fillStyle = shape.c || '#1a1a1a';
      ctx.strokeStyle = shape.c || '#1a1a1a';
      var x = cx + (shape.x || 0) * S;
      var y = cy + (shape.y || 0) * S;
      if (shape.k === 'ellipse') {
        ctx.beginPath();
        ctx.ellipse(x, y, (shape.w || 0.1) * S / 2, (shape.h || 0.1) * S / 2, 0, 0, Math.PI * 2);
        ctx.fill();
      } else if (shape.k === 'rect') {
        ctx.translate(x, y);
        if (shape.rot) ctx.rotate(shape.rot);
        ctx.fillRect(-(shape.w || 0.1) * S / 2, -(shape.h || 0.1) * S / 2,
                     (shape.w || 0.1) * S, (shape.h || 0.1) * S);
      } else if (shape.k === 'arc') {
        ctx.beginPath();
        ctx.lineWidth = (shape.w || 0.05) * S;
        ctx.lineCap = 'round';
        ctx.arc(x, y, (shape.r || 0.2) * S,
                (shape.a0 || 0) * Math.PI * 2, (shape.a1 || 1) * Math.PI * 2);
        ctx.stroke();
      } else if (shape.k === 'star') {
        // n points (5 by default); ``i`` is the inner radius as a fraction
        var n = shape.n || 5, inner = shape.i || (n === 4 ? 0.32 : 0.45);
        ctx.beginPath();
        for (var si = 0; si < n * 2; si++) {
          var sr = (si % 2 ? inner : 1) * (shape.r || 0.1) * S;
          var sa = (si / (n * 2)) * Math.PI * 2 - Math.PI / 2 + (shape.rot || 0);
          ctx[si ? 'lineTo' : 'moveTo'](x + Math.cos(sa) * sr, y + Math.sin(sa) * sr);
        }
        ctx.closePath(); ctx.fill();
      } else if (shape.k === 'poly') {
        ctx.beginPath();
        (shape.pts || []).forEach(function (q, qi) {
          ctx[qi ? 'lineTo' : 'moveTo'](cx + q[0] * S, cy + q[1] * S);
        });
        ctx.closePath(); ctx.fill();
      } else if (shape.k === 'line') {
        ctx.beginPath();
        ctx.lineWidth = (shape.w || 0.03) * S; ctx.lineCap = 'round';
        ctx.moveTo(cx + shape.x1 * S, cy + shape.y1 * S);
        ctx.lineTo(cx + shape.x2 * S, cy + shape.y2 * S);
        ctx.stroke();
      } else if (shape.k === 'ring') {
        ctx.beginPath();
        ctx.lineWidth = (shape.w || 0.02) * S;
        ctx.arc(x, y, (shape.r || 0.05) * S, 0, Math.PI * 2);
        ctx.stroke();
      } else if (shape.k === 'heart') {
        var hs = (shape.s || 0.1) * S;
        ctx.beginPath();
        ctx.moveTo(x, y + hs * 0.45);
        ctx.bezierCurveTo(x - hs * 0.9, y - hs * 0.15, x - hs * 0.45, y - hs * 0.75, x, y - hs * 0.3);
        ctx.bezierCurveTo(x + hs * 0.45, y - hs * 0.75, x + hs * 0.9, y - hs * 0.15, x, y + hs * 0.45);
        ctx.fill();
      }
      ctx.restore();
    });
    ctx.restore();
    painted(slot);
    return slot;
  };

  // -------------------------------------------------------------- decals
  var decalPainters = {};

  function painter(name, fn) { decalPainters[name] = fn; }

  painter('letter_R', function (ctx) {
    ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, CELL, CELL);
    ctx.fillStyle = '#c4281c';
    ctx.font = 'bold 104px Verdana, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('R', CELL / 2, CELL / 2 + 4);
  });

  painter('skull', function (ctx) {
    ctx.fillStyle = '#1b1b1b'; ctx.fillRect(0, 0, CELL, CELL);
    ctx.fillStyle = '#f2f3f3';
    ctx.beginPath(); ctx.ellipse(64, 54, 34, 30, 0, 0, Math.PI * 2); ctx.fill();
    ctx.fillRect(48, 76, 32, 18);
    ctx.fillStyle = '#1b1b1b';
    ctx.beginPath(); ctx.ellipse(52, 50, 9, 11, 0, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.ellipse(76, 50, 9, 11, 0, 0, Math.PI * 2); ctx.fill();
    ctx.fillRect(58, 66, 12, 10);
    ctx.fillStyle = '#f2f3f3';
    for (var i = 0; i < 3; i++) ctx.fillRect(50 + i * 12, 86, 8, 12);
  });

  function banner(colour, dark) {
    return function (ctx) {
      ctx.fillStyle = colour; ctx.fillRect(0, 0, CELL, CELL);
      ctx.fillStyle = dark;
      ctx.beginPath();
      ctx.moveTo(0, 0); ctx.lineTo(CELL, 0); ctx.lineTo(CELL, 96);
      ctx.lineTo(64, 120); ctx.lineTo(0, 96); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#f7e9c0';
      ctx.beginPath();
      ctx.moveTo(64, 24); ctx.lineTo(92, 46); ctx.lineTo(82, 84);
      ctx.lineTo(46, 84); ctx.lineTo(36, 46); ctx.closePath(); ctx.fill();
      ctx.fillStyle = colour;
      ctx.beginPath(); ctx.arc(64, 60, 15, 0, Math.PI * 2); ctx.fill();
    };
  }
  painter('banner_red', banner('#c4281c', '#8c1c15'));
  painter('banner_blue', banner('#0d69ac', '#0a3c69'));

  painter('burger', function (ctx) {
    ctx.clearRect(0, 0, CELL, CELL);
    ctx.fillStyle = '#e0a94e';
    ctx.beginPath(); ctx.ellipse(64, 44, 46, 26, 0, Math.PI, 0); ctx.fill();
    ctx.fillStyle = '#f2e2b0';
    for (var i = 0; i < 7; i++) {
      ctx.beginPath();
      ctx.ellipse(30 + i * 11, 32 + (i % 2) * 5, 3, 2, 0, 0, Math.PI * 2); ctx.fill();
    }
    ctx.fillStyle = '#5aa84f'; ctx.fillRect(16, 52, 96, 9);
    ctx.fillStyle = '#7c4a2a'; ctx.fillRect(18, 61, 92, 16);
    ctx.fillStyle = '#f5c518'; ctx.fillRect(20, 77, 88, 8);
    ctx.fillStyle = '#e0a94e';
    ctx.beginPath(); ctx.ellipse(64, 88, 46, 18, 0, 0, Math.PI); ctx.fill();
  });

  painter('logo_block', function (ctx) {
    ctx.clearRect(0, 0, CELL, CELL);
    ctx.fillStyle = '#f2f3f3'; ctx.fillRect(40, 40, 48, 48);
    ctx.fillStyle = '#b8b8b8'; ctx.fillRect(48, 48, 32, 32);
    ctx.fillStyle = '#8f9296'; ctx.fillRect(56, 56, 16, 16);
  });

  painter('tux', function (ctx) {
    ctx.clearRect(0, 0, CELL, CELL);
    ctx.fillStyle = '#f2f3f3';
    ctx.beginPath(); ctx.moveTo(46, 0); ctx.lineTo(82, 0); ctx.lineTo(64, 40);
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#1b2a35';
    ctx.beginPath(); ctx.moveTo(64, 34); ctx.lineTo(50, 46); ctx.lineTo(64, 54);
    ctx.lineTo(78, 46); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#c4281c';
    ctx.beginPath(); ctx.moveTo(52, 28); ctx.lineTo(76, 28); ctx.lineTo(64, 42);
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#dcdcdc';
    ctx.fillRect(60, 60, 8, 8); ctx.fillRect(60, 84, 8, 8);
  });

  painter('chevron', function (ctx) {
    ctx.clearRect(0, 0, CELL, CELL);
    ctx.strokeStyle = '#e0c060'; ctx.lineWidth = 10;
    for (var i = 0; i < 3; i++) {
      ctx.beginPath();
      ctx.moveTo(30, 40 + i * 22); ctx.lineTo(64, 62 + i * 22); ctx.lineTo(98, 40 + i * 22);
      ctx.stroke();
    }
  });

  painter('flowers', function (ctx) {
    ctx.clearRect(0, 0, CELL, CELL);
    var colours = ['#ffd166', '#ef476f', '#06d6a0', '#f7f7f7'];
    for (var i = 0; i < 12; i++) {
      var x = 14 + (i * 37) % 104, y = 16 + ((i * 53) % 96);
      ctx.fillStyle = colours[i % colours.length];
      for (var k = 0; k < 5; k++) {
        var a = (k / 5) * Math.PI * 2;
        ctx.beginPath();
        ctx.ellipse(x + Math.cos(a) * 6, y + Math.sin(a) * 6, 4, 4, 0, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.fillStyle = '#ffe066';
      ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2); ctx.fill();
    }
  });

  painter('sigil', function (ctx) {
    ctx.clearRect(0, 0, CELL, CELL);
    ctx.strokeStyle = '#c78bff'; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.arc(64, 64, 40, 0, Math.PI * 2); ctx.stroke();
    ctx.beginPath();
    for (var i = 0; i < 5; i++) {
      var a = -Math.PI / 2 + (i * 4 * Math.PI * 2) / 5;
      var x = 64 + Math.cos(a) * 36, y = 64 + Math.sin(a) * 36;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.closePath(); ctx.stroke();
  });

  painter('hazard', function (ctx) {
    ctx.fillStyle = '#f2b01e'; ctx.fillRect(0, 0, CELL, CELL);
    ctx.fillStyle = '#1b1b1b';
    for (var i = -CELL; i < CELL * 2; i += 32) {
      ctx.beginPath();
      ctx.moveTo(i, 0); ctx.lineTo(i + 16, 0); ctx.lineTo(i + 16 - CELL, CELL);
      ctx.lineTo(i - CELL, CELL); ctx.closePath(); ctx.fill();
    }
  });

  function teamSign(label, colour) {
    return function (ctx) {
      ctx.fillStyle = '#f2f3f3'; ctx.fillRect(0, 0, CELL, CELL);
      ctx.fillStyle = colour; ctx.fillRect(0, 34, CELL, 60);
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 34px Verdana, sans-serif';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(label, CELL / 2, 64);
      ctx.fillStyle = '#1b2a35';
      ctx.font = 'bold 14px Verdana, sans-serif';
      ctx.fillText('SPAWN', CELL / 2, 108);
    };
  }
  painter('sign_red', teamSign('RED', '#b8383b'));
  painter('sign_blue', teamSign('BLU', '#5885a2'));

  painter('sign_tycoon', function (ctx) {
    ctx.fillStyle = '#f2b01e'; ctx.fillRect(0, 0, CELL, CELL);
    ctx.fillStyle = '#8c1c15';
    ctx.font = 'bold 22px Verdana, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('PATTY', CELL / 2, 48);
    ctx.fillText('PLAINS', CELL / 2, 78);
  });

  /* ======================================================================
     WRAPPED PATTERNS
     These are printed over a whole surface rather than stuck on its front
     face (the part asks for it with ``wrap``), so a cone, a can or a cap
     carries the pattern all the way round.  Two rules follow from that.

     They are painted on transparency, not on a background: the shader mixes
     them over the part's own colour, so one "knit" pattern serves a blue
     beanie and a red one, and an item keeps being described by its colours.

     And they tile horizontally.  A mesh's U runs 0..1 once around, so
     anything crossing the edge has to be drawn again on the other side or
     there is a visible seam down the back of the hat -- which is what
     ``around`` does.
     ====================================================================== */

  /* Repeat a drawing at x and at x +/- CELL, so it survives the wrap. */
  function around(ctx, x, y, draw) {
    for (var k = -1; k <= 1; k++) {
      ctx.save();
      ctx.translate(x + k * CELL, y);
      draw(ctx);
      ctx.restore();
    }
  }

  function star(ctx, r, points) {
    ctx.beginPath();
    for (var i = 0; i < points * 2; i++) {
      var rad = i % 2 ? r * 0.45 : r;
      var a = (i / (points * 2)) * Math.PI * 2 - Math.PI / 2;
      ctx[i ? 'lineTo' : 'moveTo'](Math.cos(a) * rad, Math.sin(a) * rad);
    }
    ctx.closePath(); ctx.fill();
  }

  /* A deterministic scatter: the same hat comes out the same every time,
     which matters because these are baked once into the atlas. */
  function scatter(seed) {
    var s = seed;
    return function () { s = (s * 1103515245 + 12345) & 0x7fffffff; return s / 0x7fffffff; };
  }

  // the birthday cone: stars, spots and confetti printed over its colour
  painter('party', function (ctx) {
    var rnd = scatter(7);
    var colours = ['#f5c518', '#3c6fd6', '#2fa84f', '#f2f3f3', '#7a3fd6'];
    for (var i = 0; i < 26; i++) {
      var x = rnd() * CELL, y = rnd() * CELL, c = colours[i % colours.length];
      ctx.fillStyle = c;
      if (i % 3 === 0) {
        around(ctx, x, y, function (g) { g.fillStyle = c; star(g, 9 + rnd() * 4, 5); });
      } else if (i % 3 === 1) {
        around(ctx, x, y, function (g) {
          g.fillStyle = c; g.beginPath(); g.arc(0, 0, 6 + rnd() * 3, 0, Math.PI * 2); g.fill();
        });
      } else {
        around(ctx, x, y, function (g) {
          g.fillStyle = c; g.rotate(rnd() * Math.PI); g.fillRect(-5, -2, 10, 4);
        });
      }
    }
  });

  // knitwear: two rows of interlocking Vs, the stitch a beanie is made of
  painter('knit', function (ctx) {
    ctx.lineCap = 'round';
    for (var row = 0; row < 8; row++) {
      var y = row * 16 + 8;
      ctx.strokeStyle = row % 2 ? 'rgba(0,0,0,0.20)' : 'rgba(255,255,255,0.20)';
      ctx.lineWidth = 4;
      for (var col = -1; col < 9; col++) {
        var x = col * 16 + (row % 2 ? 8 : 0);
        ctx.beginPath();
        ctx.moveTo(x, y - 6); ctx.lineTo(x + 8, y + 5); ctx.lineTo(x + 16, y - 6);
        ctx.stroke();
      }
    }
  });

  // a woven canvas/cloth weave, for caps and bucket hats
  painter('canvas', function (ctx) {
    for (var i = 0; i < CELL; i += 6) {
      ctx.fillStyle = 'rgba(255,255,255,0.10)'; ctx.fillRect(i, 0, 3, CELL);
      ctx.fillStyle = 'rgba(0,0,0,0.10)'; ctx.fillRect(0, i, CELL, 3);
    }
  });

  // brushed felt, for a hat that should not look like plastic
  painter('felt', function (ctx) {
    var rnd = scatter(19);
    for (var i = 0; i < 900; i++) {
      ctx.fillStyle = rnd() > 0.5 ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.09)';
      ctx.fillRect(rnd() * CELL, rnd() * CELL, 3, 1);
    }
  });

  // fur: strands lying over each other, light on top and dark beneath
  painter('fur', function (ctx) {
    var rnd = scatter(31);
    ctx.lineCap = 'round';
    for (var i = 0; i < 260; i++) {
      var x = rnd() * CELL, y = rnd() * CELL, len = 6 + rnd() * 8;
      var lean = (rnd() - 0.5) * 6;
      ctx.strokeStyle = rnd() > 0.45 ? 'rgba(0,0,0,0.30)' : 'rgba(255,255,255,0.14)';
      ctx.lineWidth = 1 + rnd() * 1.6;
      around(ctx, x, y, function (g) {
        g.beginPath(); g.moveTo(0, 0); g.lineTo(lean, len); g.stroke();
      });
    }
  });

  // snow: flakes and specks over whatever the cap is dyed
  painter('snowflakes', function (ctx) {
    var rnd = scatter(5);
    ctx.strokeStyle = '#ffffff'; ctx.fillStyle = '#ffffff';
    for (var i = 0; i < 9; i++) {
      var x = rnd() * CELL, y = rnd() * CELL, r = 6 + rnd() * 6;
      around(ctx, x, y, function (g) {
        g.strokeStyle = '#ffffff'; g.lineWidth = 2; g.lineCap = 'round';
        for (var a = 0; a < 3; a++) {
          var ang = (a / 3) * Math.PI;
          g.beginPath();
          g.moveTo(-Math.cos(ang) * r, -Math.sin(ang) * r);
          g.lineTo(Math.cos(ang) * r, Math.sin(ang) * r);
          g.stroke();
        }
      });
    }
    for (i = 0; i < 40; i++) {
      ctx.globalAlpha = 0.8;
      ctx.beginPath(); ctx.arc(rnd() * CELL, rnd() * CELL, 1.5, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
  });

  // candy cane: diagonal bands, drawn past both edges so the wrap is clean
  painter('candy', function (ctx) {
    ctx.fillStyle = '#f2f3f3';
    ctx.save();
    ctx.translate(CELL / 2, CELL / 2); ctx.rotate(-0.5); ctx.translate(-CELL / 2, -CELL / 2);
    for (var i = -CELL; i < CELL * 2; i += 32) ctx.fillRect(i, -CELL, 16, CELL * 3);
    ctx.restore();
  });

  // four-colour disruptive camouflage
  painter('camo', function (ctx) {
    var rnd = scatter(11);
    var tones = ['rgba(28,40,22,0.85)', 'rgba(96,104,62,0.85)',
                 'rgba(60,74,42,0.9)', 'rgba(128,124,86,0.7)'];
    ctx.fillStyle = tones[2]; ctx.fillRect(0, 0, CELL, CELL);
    for (var i = 0; i < 40; i++) {
      var x = rnd() * CELL, y = rnd() * CELL, r = 8 + rnd() * 16;
      var c = tones[i % tones.length];
      around(ctx, x, y, function (g) {
        g.fillStyle = c;
        g.beginPath();
        for (var k = 0; k < 7; k++) {
          var a = (k / 7) * Math.PI * 2;
          var rr = r * (0.6 + ((k * 37) % 11) / 18);
          g[k ? 'lineTo' : 'moveTo'](Math.cos(a) * rr, Math.sin(a) * rr);
        }
        g.closePath(); g.fill();
      });
    }
  });

  // denim: a twill weave with a lighter wear down the middle
  painter('denim', function (ctx) {
    var rnd = scatter(23);
    for (var i = -CELL; i < CELL; i += 4) {
      ctx.strokeStyle = 'rgba(255,255,255,0.09)'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i + CELL, CELL); ctx.stroke();
      ctx.strokeStyle = 'rgba(0,0,0,0.10)';
      ctx.beginPath(); ctx.moveTo(i + 2, 0); ctx.lineTo(i + 2 + CELL, CELL); ctx.stroke();
    }
    for (var k = 0; k < 120; k++) {
      ctx.fillStyle = 'rgba(255,255,255,0.05)';
      ctx.fillRect(rnd() * CELL, rnd() * CELL, 2, 2);
    }
  });

  // hi-vis: two reflective bands round the garment
  painter('hivis', function (ctx) {
    ['rgba(240,244,248,0.92)', 'rgba(150,160,170,0.55)'].forEach(function (c, i) {
      ctx.fillStyle = c;
      ctx.fillRect(0, 34 + i * 6, CELL, i ? 4 : 14);
      ctx.fillRect(0, 78 + i * 6, CELL, i ? 4 : 14);
    });
  });

  // a carved lantern face, for the pumpkin hat
  painter('lantern', function (ctx) {
    ctx.fillStyle = '#2a1206';
    ctx.beginPath();
    ctx.moveTo(38, 44); ctx.lineTo(54, 44); ctx.lineTo(46, 62); ctx.closePath(); ctx.fill();
    ctx.beginPath();
    ctx.moveTo(90, 44); ctx.lineTo(74, 44); ctx.lineTo(82, 62); ctx.closePath(); ctx.fill();
    ctx.beginPath();
    ctx.moveTo(64, 62); ctx.lineTo(56, 74); ctx.lineTo(72, 74); ctx.closePath(); ctx.fill();
    ctx.beginPath();
    ctx.moveTo(30, 86); ctx.lineTo(98, 86); ctx.lineTo(90, 104); ctx.lineTo(38, 104);
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#f2b01e';
    for (var i = 0; i < 4; i++) ctx.fillRect(40 + i * 16, 86, 8, 10);
  });

  // leather grain, for a belt or a strap
  painter('leather', function (ctx) {
    var rnd = scatter(41);
    for (var i = 0; i < 400; i++) {
      var x = rnd() * CELL, y = rnd() * CELL;
      ctx.fillStyle = rnd() > 0.5 ? 'rgba(0,0,0,0.16)' : 'rgba(255,255,255,0.08)';
      ctx.beginPath(); ctx.arc(x, y, 1 + rnd() * 2, 0, Math.PI * 2); ctx.fill();
    }
    ctx.strokeStyle = 'rgba(0,0,0,0.25)';
    ctx.setLineDash([6, 5]); ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(0, 16); ctx.lineTo(CELL, 16); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, CELL - 16); ctx.lineTo(CELL, CELL - 16); ctx.stroke();
    ctx.setLineDash([]);
  });

  // plates and rivets, for armour and anything mechanical
  painter('rivets', function (ctx) {
    ctx.strokeStyle = 'rgba(0,0,0,0.35)'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(0, CELL / 2); ctx.lineTo(CELL, CELL / 2); ctx.stroke();
    for (var i = 0; i < 8; i++) {
      var x = i * 16 + 8;
      [30, 98].forEach(function (y) {
        ctx.fillStyle = 'rgba(255,255,255,0.35)';
        ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = 'rgba(0,0,0,0.30)';
        ctx.beginPath(); ctx.arc(x + 1, y + 1, 2.4, 0, Math.PI * 2); ctx.fill();
      });
    }
  });

  // a drink can's label: a band, a bubble and room for the colour underneath
  painter('cola', function (ctx) {
    ctx.fillStyle = 'rgba(0,0,0,0.45)';
    ctx.fillRect(0, 40, CELL, 48);
    ctx.fillStyle = '#f2f3f3';
    ctx.font = 'bold 26px Verdana, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('BLOXY', CELL / 2, 64);
    ctx.fillStyle = 'rgba(255,255,255,0.55)';
    for (var i = 0; i < 12; i++) {
      ctx.beginPath();
      ctx.arc(10 + (i * 37) % CELL, 14 + (i * 23) % 14, 2 + (i % 3), 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.fillStyle = 'rgba(255,255,255,0.22)';
    ctx.fillRect(0, 96, CELL, 6);
  });

  // stitched panels, for a sports cap
  painter('panels', function (ctx) {
    ctx.strokeStyle = 'rgba(0,0,0,0.28)'; ctx.lineWidth = 2;
    ctx.setLineDash([5, 4]);
    for (var i = 0; i < 6; i++) {
      var x = i * (CELL / 6);
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, CELL); ctx.stroke();
    }
    ctx.setLineDash([]);
    ctx.fillStyle = 'rgba(255,255,255,0.12)';
    ctx.fillRect(0, 0, CELL, 10);
  });

  // ------------------------------------------------ crate-era cosmetics
  // paisley teardrops on a bandana: white and dark on transparent, so one
  // print serves a red bandana and a blue one
  painter('paisley', function (ctx) {
    var rnd = scatter(13);
    for (var i = 0; i < 11; i++) {
      var x = rnd() * CELL, y = rnd() * CELL, r = 5 + rnd() * 4, a = rnd() * Math.PI * 2;
      around(ctx, x, y, function (g) {
        g.rotate(a);
        g.fillStyle = 'rgba(255,255,255,0.55)';
        g.beginPath();
        g.arc(0, 0, r, Math.PI * 0.5, Math.PI * 2.0);
        g.quadraticCurveTo(r * 0.2, r * 1.9, -r * 0.9, r * 2.2);
        g.quadraticCurveTo(0, r * 1.2, 0, r);
        g.fill();
        g.fillStyle = 'rgba(0,0,0,0.35)';
        g.beginPath(); g.arc(0, 0, r * 0.45, 0, Math.PI * 2); g.fill();
      });
    }
    ctx.fillStyle = 'rgba(255,255,255,0.7)';
    for (i = 0; i < 40; i++) {
      ctx.beginPath(); ctx.arc(rnd() * CELL, rnd() * CELL, 1.4, 0, Math.PI * 2); ctx.fill();
    }
  });

  // planks: a crate's boards, grain, gaps and nail heads
  painter('planks', function (ctx) {
    var rnd = scatter(29);
    for (var b = 0; b < 4; b++) {
      var y = b * 32;
      ctx.fillStyle = b % 2 ? 'rgba(0,0,0,0.10)' : 'rgba(255,255,255,0.06)';
      ctx.fillRect(0, y, CELL, 32);
      ctx.strokeStyle = 'rgba(0,0,0,0.16)'; ctx.lineWidth = 1;
      for (var g = 0; g < 5; g++) {
        var gy = y + 4 + rnd() * 24;
        ctx.beginPath(); ctx.moveTo(0, gy);
        ctx.bezierCurveTo(40, gy + rnd() * 6 - 3, 90, gy + rnd() * 6 - 3, CELL, gy);
        ctx.stroke();
      }
      ctx.fillStyle = 'rgba(0,0,0,0.42)';
      ctx.fillRect(0, y + 30, CELL, 2);
      ctx.fillStyle = 'rgba(30,24,18,0.7)';
      [10, CELL - 12].forEach(function (nx) {
        ctx.beginPath(); ctx.arc(nx, y + 16, 2.4, 0, Math.PI * 2); ctx.fill();
      });
    }
  });

  // a brass escutcheon with a keyhole, for a crate's lock plate
  painter('keyhole', function (ctx) {
    var g = ctx.createRadialGradient(54, 50, 6, 64, 64, 66);
    g.addColorStop(0, '#fff3b0'); g.addColorStop(0.5, '#e0b23a'); g.addColorStop(1, '#8a6410');
    ctx.fillStyle = g; ctx.fillRect(0, 0, CELL, CELL);
    ctx.strokeStyle = 'rgba(70,46,6,0.7)'; ctx.lineWidth = 5;
    ctx.strokeRect(6, 6, CELL - 12, CELL - 12);
    ctx.fillStyle = '#1b130a';
    ctx.beginPath(); ctx.arc(64, 50, 15, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.moveTo(56, 56); ctx.lineTo(72, 56); ctx.lineTo(77, 98); ctx.lineTo(51, 98);
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.55)';
    [[18, 18], [110, 18], [18, 110], [110, 110]].forEach(function (q) {
      ctx.beginPath(); ctx.arc(q[0], q[1], 5, 0, Math.PI * 2); ctx.fill();
    });
  });

  // the ace of hearts, tucked into a top hat's band
  painter('card_ace', function (ctx) {
    ctx.fillStyle = '#fbfaf5'; ctx.fillRect(0, 0, CELL, CELL);
    ctx.strokeStyle = '#c9c2b0'; ctx.lineWidth = 4; ctx.strokeRect(4, 4, CELL - 8, CELL - 8);
    ctx.fillStyle = '#c4281c';
    ctx.font = 'bold 30px Georgia, serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('A', 22, 24); ctx.fillText('A', CELL - 22, CELL - 24);
    ctx.beginPath();
    ctx.moveTo(64, 92);
    ctx.bezierCurveTo(30, 68, 36, 38, 64, 52);
    ctx.bezierCurveTo(92, 38, 98, 68, 64, 92);
    ctx.fill();
  });

  // linen bandages: overlapping strips of old cloth, stained at the edges
  painter('linen', function (ctx) {
    var rnd = scatter(37);
    for (var i = 0; i < 9; i++) {
      var y = i * 15 - 4;
      ctx.save();
      ctx.translate(0, y); ctx.rotate((rnd() - 0.5) * 0.12);
      ctx.fillStyle = i % 2 ? 'rgba(255,255,255,0.10)' : 'rgba(0,0,0,0.08)';
      ctx.fillRect(-10, 0, CELL + 20, 15);
      ctx.fillStyle = 'rgba(80,60,30,0.28)';
      ctx.fillRect(-10, 13, CELL + 20, 2);
      ctx.restore();
    }
    for (i = 0; i < 300; i++) {
      ctx.fillStyle = rnd() > 0.5 ? 'rgba(90,70,40,0.10)' : 'rgba(255,255,255,0.10)';
      ctx.fillRect(rnd() * CELL, rnd() * CELL, 2, 1);
    }
  });

  // rosebuds on china, for the teacup
  painter('rosebuds', function (ctx) {
    var rnd = scatter(43);
    for (var i = 0; i < 8; i++) {
      var x = (i % 4) * 32 + 16 + (i > 3 ? 16 : 0), y = i > 3 ? 92 : 38;
      around(ctx, x, y, function (g) {
        g.fillStyle = '#3f8a4a';
        g.beginPath(); g.ellipse(-9, 6, 7, 3, -0.6, 0, Math.PI * 2); g.fill();
        g.beginPath(); g.ellipse(9, 6, 7, 3, 0.6, 0, Math.PI * 2); g.fill();
        g.fillStyle = '#e46a8a';
        g.beginPath(); g.arc(0, 0, 7.5, 0, Math.PI * 2); g.fill();
        g.strokeStyle = '#b8385e'; g.lineWidth = 1.6;
        g.beginPath(); g.arc(0, 0, 4, 0.5, 5.2); g.stroke();
      });
    }
    ctx.fillStyle = 'rgba(214,170,60,0.9)';
    ctx.fillRect(0, 2, CELL, 5); ctx.fillRect(0, CELL - 7, CELL, 5);
  });

  // hair: strands running from the crown down, light and dark, on
  // transparency so it suits any colour of hair
  painter('strands', function (ctx) {
    var rnd = scatter(53);
    ctx.lineCap = 'round';
    for (var i = 0; i < 70; i++) {
      var x = rnd() * CELL, w = 1 + rnd() * 2.2;
      var bend = (rnd() - 0.5) * 10;
      ctx.strokeStyle = rnd() > 0.5 ? 'rgba(0,0,0,0.22)' : 'rgba(255,255,255,0.16)';
      ctx.lineWidth = w;
      [x, x - CELL, x + CELL].forEach(function (xx) {
        ctx.beginPath(); ctx.moveTo(xx, -4);
        ctx.quadraticCurveTo(xx + bend, CELL / 2, xx + bend * 0.4, CELL + 4);
        ctx.stroke();
      });
    }
  });

  // the stencil on a Blockhaven crate
  painter('crate_logo', function (ctx) {
    ctx.fillStyle = 'rgba(25,18,10,0.78)';
    ctx.font = 'bold 44px Verdana, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('BH', 64, 52);
    ctx.font = 'bold 15px Verdana, sans-serif';
    ctx.fillText('HAT CRATE', 64, 88);
    ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(25,18,10,0.7)';
    ctx.strokeRect(10, 18, 108, 92);
  });

  // ...and on a Hallowed Harvest crate
  painter('crate_hallowed', function (ctx) {
    ctx.fillStyle = 'rgba(255,140,30,0.92)';
    ctx.font = 'bold 22px Georgia, serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('HALLOWED', 64, 30);
    ctx.fillText('HARVEST', 64, 98);
    ctx.save(); ctx.translate(64, 64);
    ctx.fillStyle = 'rgba(255,140,30,0.92)';
    ctx.beginPath(); ctx.ellipse(0, 2, 22, 17, 0, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = 'rgba(20,10,4,0.9)';
    ctx.beginPath(); ctx.moveTo(-12, -2); ctx.lineTo(-4, -2); ctx.lineTo(-8, -10); ctx.fill();
    ctx.beginPath(); ctx.moveTo(12, -2); ctx.lineTo(4, -2); ctx.lineTo(8, -10); ctx.fill();
    ctx.fillRect(-12, 6, 24, 5);
    ctx.restore();
  });

  // stitched seams, for leather masks and patches
  painter('stitches', function (ctx) {
    ctx.strokeStyle = 'rgba(40,24,10,0.55)'; ctx.lineWidth = 3; ctx.lineCap = 'round';
    for (var row = 0; row < 3; row++) {
      var y = 24 + row * 40;
      for (var x = 6; x < CELL; x += 14) {
        ctx.beginPath(); ctx.moveTo(x, y - 4); ctx.lineTo(x + 6, y + 4); ctx.stroke();
      }
    }
  });

  // a full moon over a bat, for the event's banners and badges
  painter('moonbat', function (ctx) {
    var g = ctx.createRadialGradient(64, 64, 10, 64, 64, 60);
    g.addColorStop(0, '#fff6c8'); g.addColorStop(0.7, '#ffcf5a'); g.addColorStop(1, '#e08a1a');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(64, 64, 58, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#1a1024';
    ctx.beginPath();
    ctx.moveTo(64, 56);
    [[78, 46], [96, 50], [108, 66], [94, 62], [86, 72], [76, 64], [64, 80], [52, 64],
     [42, 72], [34, 62], [20, 66], [32, 50], [50, 46]].forEach(function (q) { ctx.lineTo(q[0], q[1]); });
    ctx.closePath(); ctx.fill();
  });

  /* ------------------------------------------------------- badge emblems
     The pictures struck on the face of a badge (app/models/badges.py names
     them).  They are stickers -- transparent round the picture -- drawn in a
     cream with a dark keyline so they read on any enamel and at the size of
     a badge worn on a chest.  ``Textures.paintEmblem`` draws one straight
     onto any 2D canvas, which is how the in-game toast shows it. */
  var INK = 'rgba(16,10,4,0.82)', CREAM = '#fff4d6';

  function inked(ctx, path, fill, width) {
    ctx.save();
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    ctx.beginPath(); path(ctx);
    ctx.lineWidth = width || 8; ctx.strokeStyle = INK; ctx.stroke();
    ctx.fillStyle = fill; ctx.fill();
    ctx.restore();
  }
  function stroked(ctx, path, colour, width) {
    ctx.save();
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    ctx.beginPath(); path(ctx);
    ctx.lineWidth = (width || 6) + 6; ctx.strokeStyle = INK; ctx.stroke();
    ctx.lineWidth = width || 6; ctx.strokeStyle = colour; ctx.stroke();
    ctx.restore();
  }
  function poly(points) {
    return function (g) {
      g.moveTo(points[0][0], points[0][1]);
      for (var i = 1; i < points.length; i++) g.lineTo(points[i][0], points[i][1]);
      g.closePath();
    };
  }
  function circlePath(x, y, r) { return function (g) { g.arc(x, y, r, 0, Math.PI * 2); }; }

  var emblems = {};
  function emblem(name, fn) { emblems[name] = fn; painter(name, fn); }

  emblem('em_flag', function (ctx) {
    stroked(ctx, function (g) { g.moveTo(38, 108); g.lineTo(38, 18); }, CREAM, 7);
    inked(ctx, function (g) {
      g.moveTo(42, 22); g.bezierCurveTo(62, 12, 78, 34, 104, 24);
      g.lineTo(100, 62); g.bezierCurveTo(76, 72, 60, 50, 42, 60); g.closePath();
    }, '#ff5a3c');
    inked(ctx, poly([[74, 28], [62, 46], [70, 46], [64, 60], [80, 40], [72, 40], [78, 28]]), '#ffd24a', 4);
    inked(ctx, function (g) { g.rect(26, 104, 26, 10); }, CREAM, 5);
  });

  emblem('em_return', function (ctx) {
    stroked(ctx, function (g) { g.arc(64, 66, 42, -0.25 * Math.PI, 1.25 * Math.PI); }, '#7fd1ff', 8);
    inked(ctx, poly([[96, 26], [108, 52], [80, 50]]), '#7fd1ff', 6);
    stroked(ctx, function (g) { g.moveTo(54, 92); g.lineTo(54, 40); }, CREAM, 5);
    inked(ctx, poly([[57, 42], [84, 48], [57, 62]]), '#ff5a3c', 6);
  });

  emblem('em_crosshair', function (ctx) {
    stroked(ctx, circlePath(64, 64, 40), '#ff5a3c', 7);
    stroked(ctx, circlePath(64, 64, 20), CREAM, 5);
    [[64, 8, 64, 34], [64, 94, 64, 120], [8, 64, 34, 64], [94, 64, 120, 64]].forEach(function (l) {
      stroked(ctx, function (g) { g.moveTo(l[0], l[1]); g.lineTo(l[2], l[3]); }, CREAM, 6);
    });
    inked(ctx, circlePath(64, 64, 6), '#ff5a3c', 4);
  });

  emblem('em_bolt', function (ctx) {
    inked(ctx, poly([[76, 8], [34, 70], [60, 70], [48, 120], [96, 50], [68, 50], [86, 8]]), '#ffd24a', 9);
    ctx.fillStyle = 'rgba(255,255,255,0.65)';
    ctx.beginPath(); ctx.moveTo(74, 16); ctx.lineTo(48, 62); ctx.lineTo(56, 62); ctx.lineTo(80, 16); ctx.fill();
  });

  emblem('em_trophy', function (ctx) {
    stroked(ctx, function (g) { g.arc(30, 44, 14, 0.5 * Math.PI, 1.6 * Math.PI); }, '#ffd24a', 6);
    stroked(ctx, function (g) { g.arc(98, 44, 14, 1.4 * Math.PI, 0.5 * Math.PI); }, '#ffd24a', 6);
    inked(ctx, function (g) {
      g.moveTo(32, 22); g.lineTo(96, 22); g.bezierCurveTo(96, 62, 84, 78, 64, 80);
      g.bezierCurveTo(44, 78, 32, 62, 32, 22); g.closePath();
    }, '#ffd24a');
    inked(ctx, function (g) { g.rect(56, 78, 16, 18); }, '#e2a10e', 6);
    inked(ctx, function (g) { g.rect(38, 96, 52, 14); }, CREAM, 7);
    inked(ctx, function (g) {
      for (var i = 0; i < 10; i++) {
        var rad = i % 2 ? 6 : 14, a = i * Math.PI / 5 - Math.PI / 2;
        g[i ? 'lineTo' : 'moveTo'](64 + Math.cos(a) * rad, 46 + Math.sin(a) * rad);
      }
      g.closePath();
    }, CREAM, 4);
  });

  emblem('em_tower', function (ctx) {
    inked(ctx, poly([[30, 112], [30, 34], [40, 34], [40, 22], [52, 22], [52, 34], [58, 34],
                     [58, 22], [70, 22], [70, 34], [76, 34], [76, 22], [88, 22], [88, 34],
                     [98, 34], [98, 112]]), CREAM);
    inked(ctx, function (g) { g.moveTo(52, 112); g.lineTo(52, 84); g.arc(64, 84, 12, Math.PI, 0); g.lineTo(76, 112); }, '#3b4a5c', 5);
    inked(ctx, function (g) { g.rect(58, 48, 12, 16); }, '#7fd1ff', 4);
  });

  emblem('em_clock', function (ctx) {
    inked(ctx, circlePath(64, 66, 44), CREAM);
    for (var i = 0; i < 12; i++) {
      var a = i * Math.PI / 6;
      ctx.fillStyle = INK;
      ctx.beginPath(); ctx.arc(64 + Math.sin(a) * 35, 66 - Math.cos(a) * 35, i % 3 ? 2.5 : 4.5, 0, Math.PI * 2); ctx.fill();
    }
    stroked(ctx, function (g) { g.moveTo(64, 66); g.lineTo(60, 36); }, '#1b2a35', 5);
    stroked(ctx, function (g) { g.moveTo(64, 66); g.lineTo(86, 72); }, '#ff5a3c', 4);
    inked(ctx, function (g) { g.rect(56, 10, 16, 10); }, '#ffd24a', 4);
  });

  emblem('em_hourglass', function (ctx) {
    inked(ctx, function (g) { g.rect(28, 12, 72, 12); }, '#8a5226', 6);
    inked(ctx, function (g) { g.rect(28, 104, 72, 12); }, '#8a5226', 6);
    inked(ctx, poly([[36, 24], [92, 24], [66, 64], [92, 104], [36, 104], [62, 64]]), 'rgba(220,240,255,0.95)', 7);
    inked(ctx, poly([[46, 38], [82, 38], [64, 60]]), '#ffb03a', 3);
    inked(ctx, poly([[42, 102], [86, 102], [64, 80]]), '#ffb03a', 3);
  });

  emblem('em_sunrise', function (ctx) {
    for (var i = 0; i < 9; i++) {
      var a = Math.PI + (i + 0.5) * Math.PI / 9;
      stroked(ctx, (function (a) { return function (g) {
        g.moveTo(64 + Math.cos(a) * 36, 80 + Math.sin(a) * 36);
        g.lineTo(64 + Math.cos(a) * 56, 80 + Math.sin(a) * 56); }; })(a), '#ffd24a', 5);
    }
    inked(ctx, function (g) { g.arc(64, 80, 30, Math.PI, 0); g.closePath(); }, '#ff8c1a');
    stroked(ctx, function (g) { g.moveTo(10, 84); g.lineTo(118, 84); }, CREAM, 6);
    stroked(ctx, function (g) { g.moveTo(30, 100); g.lineTo(98, 100); }, CREAM, 5);
  });

  emblem('em_cross', function (ctx) {
    inked(ctx, circlePath(64, 64, 50), CREAM);
    inked(ctx, poly([[50, 22], [78, 22], [78, 50], [106, 50], [106, 78], [78, 78], [78, 106],
                     [50, 106], [50, 78], [22, 78], [22, 50], [50, 50]]), '#e8312a', 6);
  });

  emblem('em_hand', function (ctx) {
    inked(ctx, function (g) {
      g.moveTo(40, 112); g.lineTo(44, 70); g.lineTo(34, 52); g.lineTo(40, 48); g.lineTo(50, 60);
      g.lineTo(48, 26); g.lineTo(56, 24); g.lineTo(60, 54); g.lineTo(62, 16); g.lineTo(70, 16);
      g.lineTo(70, 54); g.lineTo(76, 22); g.lineTo(84, 24); g.lineTo(80, 58); g.lineTo(90, 36);
      g.lineTo(97, 40); g.lineTo(86, 76); g.lineTo(84, 112); g.closePath();
    }, '#8fcf5a');
    ctx.strokeStyle = 'rgba(40,70,20,0.7)'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(52, 84); ctx.lineTo(72, 92); ctx.stroke();
    inked(ctx, function (g) { g.rect(14, 104, 100, 12); }, '#6b4a2a', 6);
  });

  emblem('em_skull', function (ctx) {
    inked(ctx, function (g) {
      g.moveTo(30, 64); g.bezierCurveTo(26, 18, 102, 18, 98, 64);
      g.lineTo(90, 78); g.lineTo(88, 104); g.lineTo(40, 104); g.lineTo(38, 78); g.closePath();
    }, CREAM);
    ctx.fillStyle = '#1b130a';
    ctx.beginPath(); ctx.ellipse(48, 62, 11, 13, 0.2, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.ellipse(80, 62, 11, 13, -0.2, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.moveTo(64, 74); ctx.lineTo(58, 86); ctx.lineTo(70, 86); ctx.fill();
    for (var x = 48; x <= 80; x += 8) ctx.fillRect(x - 1.5, 92, 3, 12);
    ctx.fillStyle = '#ff4d3a';
    ctx.beginPath(); ctx.arc(48, 62, 4, 0, Math.PI * 2); ctx.arc(80, 62, 4, 0, Math.PI * 2); ctx.fill();
  });

  emblem('em_fist', function (ctx) {
    inked(ctx, function (g) {
      g.moveTo(30, 54); g.quadraticCurveTo(30, 30, 50, 32); g.lineTo(92, 32);
      g.quadraticCurveTo(104, 34, 104, 50); g.lineTo(104, 76); g.quadraticCurveTo(100, 96, 80, 98);
      g.lineTo(80, 118); g.lineTo(42, 118); g.lineTo(42, 96); g.quadraticCurveTo(30, 88, 30, 72); g.closePath();
    }, '#ffb46b');
    ctx.strokeStyle = INK; ctx.lineWidth = 4;
    [52, 70, 88].forEach(function (x) { ctx.beginPath(); ctx.moveTo(x, 33); ctx.lineTo(x, 56); ctx.stroke(); });
    ctx.beginPath(); ctx.moveTo(32, 58); ctx.quadraticCurveTo(60, 54, 70, 72); ctx.stroke();
    ctx.strokeStyle = '#ff5a3c'; ctx.lineWidth = 5;
    [[18, 30, 8, 22], [16, 50, 4, 50], [22, 70, 10, 78]].forEach(function (l) {
      ctx.beginPath(); ctx.moveTo(l[0], l[1]); ctx.lineTo(l[2], l[3]); ctx.stroke();
    });
  });

  emblem('em_bomb', function (ctx) {
    inked(ctx, circlePath(58, 74, 38), '#2b2f36');
    ctx.fillStyle = 'rgba(255,255,255,0.35)';
    ctx.beginPath(); ctx.ellipse(46, 60, 10, 6, -0.7, 0, Math.PI * 2); ctx.fill();
    inked(ctx, function (g) { g.rect(74, 30, 16, 14); }, '#6d6e6c', 5);
    stroked(ctx, function (g) { g.moveTo(84, 30); g.quadraticCurveTo(92, 16, 98, 22); }, '#c9b48a', 4);
    stroked(ctx, function (g) { g.moveTo(104, 20); g.quadraticCurveTo(112, 14, 116, 20); }, '#c9b48a', 4);
    stroked(ctx, function (g) { g.moveTo(98, 30); g.lineTo(108, 8); }, CREAM, 3);
    stroked(ctx, function (g) { g.moveTo(92, 10); g.lineTo(114, 28); }, CREAM, 3);
  });

  emblem('em_scope', function (ctx) {
    inked(ctx, circlePath(64, 64, 46), 'rgba(160,220,255,0.35)');
    stroked(ctx, function (g) { g.moveTo(64, 22); g.lineTo(64, 106); g.moveTo(22, 64); g.lineTo(106, 64); }, CREAM, 3);
    [-24, -12, 12, 24].forEach(function (d) {
      ctx.fillStyle = CREAM;
      ctx.beginPath(); ctx.arc(64 + d, 64, 3, 0, Math.PI * 2); ctx.arc(64, 64 + d, 3, 0, Math.PI * 2); ctx.fill();
    });
    inked(ctx, circlePath(64, 64, 5), '#ff3a3a', 3);
    stroked(ctx, circlePath(64, 64, 46), '#1b2a35', 5);
  });

  emblem('em_waves', function (ctx) {
    [[40, '#bfe9ff'], [66, '#5fb8ff'], [92, '#2d7ff9']].forEach(function (w) {
      stroked(ctx, function (g) {
        g.moveTo(10, w[0]);
        for (var x = 10; x < 118; x += 27) g.bezierCurveTo(x + 7, w[0] - 16, x + 20, w[0] - 16, x + 27, w[0]);
      }, w[1], 8);
    });
  });

  emblem('em_shield', function (ctx) {
    inked(ctx, function (g) {
      g.moveTo(64, 12); g.lineTo(104, 26); g.bezierCurveTo(104, 74, 88, 100, 64, 116);
      g.bezierCurveTo(40, 100, 24, 74, 24, 26); g.closePath();
    }, '#7fd1ff');
    stroked(ctx, function (g) { g.moveTo(44, 62); g.lineTo(58, 78); g.lineTo(86, 44); }, CREAM, 8);
  });

  emblem('em_compass', function (ctx) {
    stroked(ctx, circlePath(64, 64, 44), CREAM, 5);
    inked(ctx, poly([[64, 8], [74, 54], [120, 64], [74, 74], [64, 120], [54, 74], [8, 64], [54, 54]]), CREAM, 6);
    inked(ctx, poly([[64, 8], [74, 54], [64, 64], [54, 54]]), '#ff5a3c', 4);
    inked(ctx, circlePath(64, 64, 6), '#ffd24a', 3);
  });

  emblem('em_crate', function (ctx) {
    inked(ctx, function (g) { g.rect(20, 26, 88, 82); }, '#b07a45');
    ctx.strokeStyle = 'rgba(60,34,12,0.7)'; ctx.lineWidth = 3;
    [46, 66, 86].forEach(function (y) { ctx.beginPath(); ctx.moveTo(22, y); ctx.lineTo(106, y); ctx.stroke(); });
    stroked(ctx, function (g) { g.moveTo(26, 32); g.lineTo(102, 102); }, '#8a5226', 6);
    inked(ctx, function (g) { g.rect(54, 18, 20, 22); }, '#ffd24a', 5);
    ctx.fillStyle = '#1b130a';
    ctx.beginPath(); ctx.arc(64, 27, 4, 0, Math.PI * 2); ctx.fill(); ctx.fillRect(62, 28, 4, 8);
  });

  emblem('em_sparkle', function (ctx) {
    function sparkle(x, y, r, c) {
      inked(ctx, function (g) {
        g.moveTo(x, y - r); g.quadraticCurveTo(x + r * 0.16, y - r * 0.16, x + r, y);
        g.quadraticCurveTo(x + r * 0.16, y + r * 0.16, x, y + r);
        g.quadraticCurveTo(x - r * 0.16, y + r * 0.16, x - r, y);
        g.quadraticCurveTo(x - r * 0.16, y - r * 0.16, x, y - r); g.closePath();
      }, c, 6);
    }
    sparkle(58, 66, 46, '#ffe36b');
    sparkle(98, 28, 18, '#e2b8ff');
    sparkle(100, 98, 12, '#ffffff');
  });

  emblem('em_pumpkin', function (ctx) {
    stroked(ctx, function (g) { g.moveTo(64, 34); g.quadraticCurveTo(62, 18, 74, 12); }, '#4f8a2e', 7);
    inked(ctx, function (g) { g.ellipse(64, 74, 50, 40, 0, 0, Math.PI * 2); }, '#ff8c1a');
    ctx.strokeStyle = 'rgba(120,50,0,0.6)'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.ellipse(64, 74, 20, 39, 0, 0, Math.PI * 2); ctx.stroke();
    ctx.fillStyle = '#ffe36b';
    ctx.beginPath(); ctx.moveTo(38, 66); ctx.lineTo(54, 66); ctx.lineTo(46, 52); ctx.fill();
    ctx.beginPath(); ctx.moveTo(74, 66); ctx.lineTo(90, 66); ctx.lineTo(82, 52); ctx.fill();
    ctx.beginPath(); ctx.moveTo(34, 82); ctx.quadraticCurveTo(64, 108, 94, 82);
    ctx.lineTo(84, 86); ctx.lineTo(78, 80); ctx.lineTo(70, 88); ctx.lineTo(62, 80); ctx.lineTo(54, 88);
    ctx.lineTo(46, 80); ctx.lineTo(40, 86); ctx.closePath(); ctx.fill();
  });

  /* -------------------------------------------------- the holiday icons
     One picture for each year of each holiday (app/models/holidays/), drawn
     in a 128 box.  The same drawing does three jobs: a badge emblem (in
     colour, with the cream-and-ink look of the others), the stencil on the
     side of a crate (one ink colour, details knocked out), and the site's
     own decorations.  ``P`` fills a shape, ``K`` cuts a detail into it (in
     colour mode it is painted in the dark ink instead), ``L`` strokes a
     line. */
  function iconPen(ctx, mono, ink) {
    return {
      P: function (path, colour) {
        if (mono) {
          ctx.save(); ctx.beginPath(); path(ctx); ctx.fillStyle = ink; ctx.fill(); ctx.restore();
        } else {
          inked(ctx, path, colour, 7);
        }
      },
      K: function (path, colour) {
        ctx.save();
        if (mono) ctx.globalCompositeOperation = 'destination-out';
        ctx.beginPath(); path(ctx);
        ctx.fillStyle = mono ? '#000' : (colour || INK); ctx.fill();
        ctx.restore();
      },
      L: function (path, colour, width) {
        ctx.save();
        ctx.lineCap = 'round'; ctx.lineJoin = 'round';
        ctx.beginPath(); path(ctx);
        if (!mono) { ctx.lineWidth = (width || 6) + 6; ctx.strokeStyle = INK; ctx.stroke(); }
        ctx.lineWidth = width || 6; ctx.strokeStyle = mono ? ink : colour; ctx.stroke();
        ctx.restore();
      }
    };
  }
  function circlePath(x, y, r) { return function (g) { g.arc(x, y, r, 0, Math.PI * 2); }; }
  function polyPath(pts) {
    return function (g) {
      pts.forEach(function (q, i) { g[i ? 'lineTo' : 'moveTo'](q[0], q[1]); }); g.closePath();
    };
  }
  function starPath(x, y, r, n, inner, rot) {
    return function (g) {
      for (var i = 0; i < n * 2; i++) {
        var rr = i % 2 ? r * (inner || 0.45) : r;
        var a = (i / (n * 2)) * Math.PI * 2 - Math.PI / 2 + (rot || 0);
        g[i ? 'lineTo' : 'moveTo'](x + Math.cos(a) * rr, y + Math.sin(a) * rr);
      }
      g.closePath();
    };
  }
  function heartPath(x, y, s) {
    return function (g) {
      g.moveTo(x, y + s * 0.5);
      g.bezierCurveTo(x - s, y - s * 0.1, x - s * 0.5, y - s * 0.8, x, y - s * 0.32);
      g.bezierCurveTo(x + s * 0.5, y - s * 0.8, x + s, y - s * 0.1, x, y + s * 0.5);
    };
  }
  function eggPath(x, y, w, h) {
    return function (g) {
      g.moveTo(x, y - h);
      g.bezierCurveTo(x + w * 0.9, y - h, x + w * 1.1, y + h * 0.75, x, y + h * 0.82);
      g.bezierCurveTo(x - w * 1.1, y + h * 0.75, x - w * 0.9, y - h, x, y - h);
    };
  }

  var ICONS = {
    // -- New Year
    clock: function (t) {
      t.P(circlePath(64, 66, 48), '#fff4d6');
      for (var k = 0; k < 12; k++) {
        var a = k * Math.PI / 6;
        t.K(circlePath(64 + Math.sin(a) * 38, 66 - Math.cos(a) * 38, k % 3 ? 2.5 : 4.5));
      }
      t.L(function (g) { g.moveTo(64, 66); g.lineTo(60, 34); }, '#2a1a08', 6);
      t.L(function (g) { g.moveTo(64, 66); g.lineTo(64, 26); }, '#2a1a08', 4);
      t.P(circlePath(64, 66, 6), '#f2c230');
      t.P(starPath(104, 22, 14, 5), '#f2c230');
    },
    champagne: function (t) {
      t.P(polyPath([[30, 24], [58, 24], [52, 66], [36, 66]]), '#fff4d6');
      t.P(polyPath([[70, 24], [98, 24], [92, 66], [76, 66]]), '#fff4d6');
      t.K(polyPath([[34, 34], [54, 34], [51, 60], [37, 60]]), '#f2c230');
      t.K(polyPath([[74, 34], [94, 34], [91, 60], [77, 60]]), '#f2c230');
      t.P(function (g) { g.rect(41, 66, 6, 34); }, '#fff4d6');
      t.P(function (g) { g.rect(81, 66, 6, 34); }, '#fff4d6');
      t.P(function (g) { g.ellipse(44, 104, 16, 5, 0, 0, Math.PI * 2); }, '#fff4d6');
      t.P(function (g) { g.ellipse(84, 104, 16, 5, 0, 0, Math.PI * 2); }, '#fff4d6');
      t.P(starPath(64, 16, 10, 4, 0.35), '#ffe36b');
    },
    firework: function (t) {
      for (var k = 0; k < 12; k++) {
        var a = k * Math.PI / 6;
        t.L(function (g) {
          g.moveTo(64 + Math.cos(a) * 14, 54 + Math.sin(a) * 14);
          g.lineTo(64 + Math.cos(a) * 42, 54 + Math.sin(a) * 42);
        }, k % 2 ? '#ff3b4e' : '#ffcf3a', 6);
      }
      t.P(circlePath(64, 54, 10), '#fff4d6');
      t.P(polyPath([[58, 96], [70, 96], [68, 124], [60, 124]]), '#3cc8ff');
    },
    cassette: function (t) {
      t.P(function (g) { g.rect(18, 34, 92, 60); }, '#2a2a33');
      t.K(function (g) { g.rect(28, 42, 72, 26); }, '#ff2bd6');
      t.P(circlePath(46, 55, 9), '#fff4d6');
      t.P(circlePath(82, 55, 9), '#fff4d6');
      t.K(polyPath([[38, 94], [90, 94], [84, 80], [44, 80]]), '#19f0ff');
    },
    crystal: function (t) {
      t.P(polyPath([[64, 14], [100, 50], [64, 116], [28, 50]]), '#dff2ff');
      t.K(polyPath([[64, 14], [80, 50], [64, 116], [48, 50]]), '#9fd8ff');
      t.L(function (g) { g.moveTo(28, 50); g.lineTo(100, 50); }, '#5aa9e6', 3);
      t.P(starPath(104, 20, 10, 4, 0.3), '#ffffff');
    },
    // -- St. Patrick's
    shamrock: function (t) {
      t.P(heartPath(64, 42, 30), '#4fc46e');
      t.P(function (g) { g.save(); g.translate(42, 70); g.rotate(-2.1); heartPath(0, 0, 30)(g); g.restore(); }, '#4fc46e');
      t.P(function (g) { g.save(); g.translate(86, 70); g.rotate(2.1); heartPath(0, 0, 30)(g); g.restore(); }, '#4fc46e');
      t.L(function (g) { g.moveTo(64, 72); g.quadraticCurveTo(66, 100, 82, 118); }, '#2f8a3a', 7);
    },
    potogold: function (t) {
      t.P(function (g) { g.ellipse(64, 84, 44, 32, 0, 0, Math.PI * 2); }, '#2a2a2e');
      t.P(function (g) { g.ellipse(64, 56, 40, 10, 0, 0, Math.PI * 2); }, '#ffcf3a');
      [[48, 48], [64, 42], [80, 48], [56, 36], [72, 36]].forEach(function (q) {
        t.P(circlePath(q[0], q[1], 9), '#ffcf3a');
      });
      t.L(function (g) { g.moveTo(16, 30); g.quadraticCurveTo(64, -6, 112, 30); }, '#ff5a5a', 5);
    },
    rainbow: function (t) {
      ['#ff5a5a', '#ffb347', '#ffe36b', '#7dff9a', '#5ab4ff', '#b26bff'].forEach(function (c, i) {
        t.L(function (g) { g.arc(64, 90, 50 - i * 7, Math.PI, 0); }, c, 7);
      });
      t.P(function (g) { g.ellipse(26, 92, 20, 12, 0, 0, Math.PI * 2); }, '#fff4d6');
      t.P(function (g) { g.ellipse(102, 92, 20, 12, 0, 0, Math.PI * 2); }, '#fff4d6');
    },
    horseshoe: function (t) {
      t.L(function (g) { g.arc(64, 60, 36, Math.PI * 0.8, Math.PI * 2.2); }, '#c9ced6', 18);
      for (var k = 0; k < 6; k++) {
        var a = Math.PI * 0.9 + k * Math.PI * 1.2 / 5;
        t.K(circlePath(64 + Math.cos(a) * 36, 60 + Math.sin(a) * 36, 3));
      }
      t.P(heartPath(64, 70, 14), '#4fc46e');
    },
    fiddle: function (t) {
      t.P(function (g) {
        g.ellipse(64, 86, 26, 28, 0, 0, Math.PI * 2);
      }, '#b8642a');
      t.P(function (g) { g.ellipse(64, 50, 20, 20, 0, 0, Math.PI * 2); }, '#b8642a');
      t.P(function (g) { g.rect(60, 8, 8, 44); }, '#3a1d0c');
      t.K(function (g) { g.rect(54, 70, 4, 18); g.rect(70, 70, 4, 18); }, '#2a1a08');
      t.L(function (g) { g.moveTo(20, 30); g.lineTo(112, 104); }, '#e8d9b8', 4);
    },
    jackbox: function (t) {
      t.P(function (g) { g.rect(30, 64, 68, 52); }, '#2f8a3a');
      t.P(polyPath([[30, 64], [98, 64], [108, 52], [40, 52]]), '#4fc46e');
      t.L(function (g) { g.moveTo(64, 58); g.quadraticCurveTo(50, 48, 64, 40); g.quadraticCurveTo(78, 32, 64, 26); }, '#c9ced6', 5);
      t.P(circlePath(64, 18, 13), '#ffcf3a');
      t.P(polyPath([[50, 12], [78, 12], [74, 0], [54, 0]]), '#2f8a3a');
    },
    // -- Easter
    egg: function (t) {
      t.P(eggPath(64, 66, 40, 50), '#ffb3d8');
      t.K(function (g) {
        g.moveTo(26, 62); for (var x = 26; x <= 102; x += 12) g.lineTo(x, (x / 12) % 2 ? 54 : 66);
        g.lineTo(102, 72); g.lineTo(26, 72);
      }, '#7de0ff');
      [[48, 92], [64, 100], [80, 92]].forEach(function (q) { t.K(circlePath(q[0], q[1], 5), '#ffe36b'); });
    },
    bunny: function (t) {
      t.P(function (g) { g.ellipse(46, 34, 11, 30, -0.2, 0, Math.PI * 2); }, '#fff4d6');
      t.P(function (g) { g.ellipse(82, 34, 11, 30, 0.2, 0, Math.PI * 2); }, '#fff4d6');
      t.K(function (g) { g.ellipse(46, 36, 5, 20, -0.2, 0, Math.PI * 2); }, '#ffb3d8');
      t.K(function (g) { g.ellipse(82, 36, 5, 20, 0.2, 0, Math.PI * 2); }, '#ffb3d8');
      t.P(circlePath(64, 84, 36), '#fff4d6');
      t.K(circlePath(52, 78, 4)); t.K(circlePath(76, 78, 4));
      t.K(heartPath(64, 92, 7), '#ff7ab8');
    },
    chick: function (t) {
      t.P(circlePath(64, 74, 40), '#ffe36b');
      t.K(circlePath(52, 64, 5)); t.K(circlePath(76, 64, 5));
      t.K(polyPath([[56, 78], [72, 78], [64, 90]]), '#ff8c1a');
      t.P(polyPath([[24, 112], [104, 112], [96, 94], [84, 104], [74, 92], [64, 104], [54, 92], [44, 104], [32, 94]]), '#fff4d6');
    },
    chocolate: function (t) {
      t.P(function (g) { g.rect(26, 22, 76, 92); }, '#5a3018');
      for (var r = 0; r < 3; r++) {
        for (var c = 0; c < 2; c++) {
          t.K(function (g) { g.rect(34 + c * 32, 30 + r * 26, 28, 22); }, '#7a4428');
        }
      }
      t.P(polyPath([[26, 80], [102, 64], [102, 114], [26, 114]]), '#c9ced6');
    },
    faberge: function (t) {
      t.P(eggPath(64, 70, 38, 48), '#b26bff');
      t.L(function (g) { g.moveTo(28, 60); g.quadraticCurveTo(64, 72, 100, 60); }, '#f2c230', 5);
      t.L(function (g) { g.moveTo(30, 84); g.quadraticCurveTo(64, 96, 98, 84); }, '#f2c230', 5);
      t.P(polyPath([[64, 30], [72, 40], [64, 50], [56, 40]]), '#7de0ff');
      t.P(starPath(64, 14, 10, 5), '#f2c230');
    },
    // -- the Fourth of July
    spangle: function (t) {
      t.P(starPath(64, 64, 52, 5, 0.42), '#f2f3f3');
      t.K(function (g) { g.rect(40, 58, 48, 8); }, '#c4281c');
      t.K(function (g) { g.rect(46, 74, 36, 8); }, '#c4281c');
      t.K(starPath(64, 44, 9, 5), '#2f5fa8');
    },
    grill: function (t) {
      t.P(function (g) { g.arc(64, 60, 44, 0, Math.PI); g.closePath(); }, '#2a2a2e');
      t.L(function (g) { g.moveTo(40, 100); g.lineTo(32, 122); g.moveTo(88, 100); g.lineTo(96, 122); }, '#2a2a2e', 6);
      t.P(function (g) { g.rect(22, 52, 84, 8); }, '#c9ced6');
      t.L(function (g) { g.moveTo(44, 46); g.quadraticCurveTo(40, 30, 48, 20); g.moveTo(64, 46); g.quadraticCurveTo(60, 28, 68, 14); g.moveTo(84, 46); g.quadraticCurveTo(80, 30, 88, 20); }, '#c9ced6', 4);
    },
    torch: function (t) {
      t.P(polyPath([[50, 62], [78, 62], [70, 120], [58, 120]]), '#c9a227');
      t.P(function (g) { g.rect(46, 56, 36, 10); }, '#e0b23a');
      t.P(function (g) {
        g.moveTo(64, 6); g.bezierCurveTo(90, 30, 84, 56, 64, 56); g.bezierCurveTo(44, 56, 38, 30, 64, 6);
      }, '#ff8c1a');
      t.K(function (g) { g.moveTo(64, 24); g.bezierCurveTo(76, 38, 72, 52, 64, 52); g.bezierCurveTo(56, 52, 52, 38, 64, 24); }, '#ffe36b');
    },
    eagle: function (t) {
      t.P(function (g) {
        g.moveTo(64, 50); g.bezierCurveTo(40, 20, 14, 30, 6, 46); g.bezierCurveTo(30, 44, 40, 60, 54, 70);
        g.lineTo(74, 70); g.bezierCurveTo(88, 60, 98, 44, 122, 46); g.bezierCurveTo(114, 30, 88, 20, 64, 50);
      }, '#6a4a2a');
      t.P(circlePath(64, 50, 12), '#fff4d6');
      t.K(polyPath([[64, 54], [76, 56], [66, 62]]), '#ffcf3a');
      t.P(polyPath([[52, 70], [76, 70], [72, 100], [56, 100]]), '#6a4a2a');
      t.P(polyPath([[54, 100], [74, 100], [80, 118], [48, 118]]), '#f2f3f3');
    },
    libertybell: function (t) {
      t.P(function (g) {
        g.moveTo(40, 30); g.quadraticCurveTo(64, 14, 88, 30); g.lineTo(96, 88);
        g.quadraticCurveTo(108, 100, 110, 104); g.lineTo(18, 104); g.quadraticCurveTo(20, 100, 32, 88);
        g.closePath();
      }, '#b8862e');
      t.L(function (g) { g.moveTo(56, 44); g.lineTo(62, 62); g.lineTo(58, 76); g.lineTo(64, 92); }, '#2a1a08', 3);
      t.P(circlePath(64, 112, 8), '#6a4a2a');
      t.P(function (g) { g.rect(56, 8, 16, 12); }, '#6a4a2a');
    },
    // -- Halloween
    coffin: function (t) {
      t.P(polyPath([[48, 8], [80, 8], [98, 34], [84, 120], [44, 120], [30, 34]]), '#5a3a28');
      t.K(function (g) { g.rect(60, 30, 8, 52); g.rect(46, 44, 36, 8); }, '#fff4d6');
    },
    cauldron: function (t) {
      t.P(function (g) { g.ellipse(64, 82, 46, 36, 0, 0, Math.PI * 2); }, '#2a2a2e');
      t.P(function (g) { g.ellipse(64, 52, 46, 10, 0, 0, Math.PI * 2); }, '#6bff9a');
      [[48, 36, 9], [70, 28, 12], [86, 40, 7]].forEach(function (q) {
        t.P(circlePath(q[0], q[1], q[2]), '#6bff9a');
      });
      t.L(function (g) { g.moveTo(34, 114); g.lineTo(28, 124); g.moveTo(94, 114); g.lineTo(100, 124); }, '#2a2a2e', 6);
    },
    manor: function (t) {
      t.P(polyPath([[20, 120], [20, 60], [44, 36], [64, 52], [84, 20], [108, 50], [108, 120]]), '#3a2a4a');
      [[34, 76], [70, 70], [90, 82], [52, 96], [86, 104]].forEach(function (q) {
        t.K(function (g) { g.rect(q[0], q[1], 10, 12); }, '#ffcf3a');
      });
      t.P(circlePath(104, 18, 12), '#fff4d6');
    },
    circustent: function (t) {
      t.P(polyPath([[64, 10], [118, 70], [10, 70]]), '#c4281c');
      t.K(polyPath([[64, 10], [76, 70], [52, 70]]), '#f2f3f3');
      t.K(polyPath([[64, 10], [104, 70], [94, 70]]), '#f2f3f3');
      t.K(polyPath([[64, 10], [34, 70], [24, 70]]), '#f2f3f3');
      t.P(function (g) { g.rect(16, 70, 96, 46); }, '#7a2a6a');
      t.K(polyPath([[52, 116], [64, 84], [76, 116]]), '#1a0d26');
      t.P(polyPath([[64, 10], [64, -2], [80, 4]]), '#ffcf3a');
    },
    pumpkin: function (t) {
      t.L(function (g) { g.moveTo(64, 34); g.quadraticCurveTo(62, 18, 74, 12); }, '#4f8a2e', 7);
      t.P(function (g) { g.ellipse(64, 74, 50, 40, 0, 0, Math.PI * 2); }, '#ff8c1a');
      t.K(polyPath([[38, 66], [54, 66], [46, 52]]), '#ffe36b');
      t.K(polyPath([[74, 66], [90, 66], [82, 52]]), '#ffe36b');
      t.K(function (g) {
        g.moveTo(34, 82); g.quadraticCurveTo(64, 108, 94, 82); g.lineTo(84, 86); g.lineTo(78, 80);
        g.lineTo(70, 88); g.lineTo(62, 80); g.lineTo(54, 88); g.lineTo(46, 80); g.lineTo(40, 86);
      }, '#ffe36b');
    },
    // -- Christmas
    gift: function (t) {
      t.P(function (g) { g.rect(22, 52, 84, 66); }, '#c4281c');
      t.P(function (g) { g.rect(16, 40, 96, 18); }, '#a8201a');
      t.K(function (g) { g.rect(58, 40, 12, 78); }, '#2fa84f');
      t.P(function (g) { g.ellipse(48, 32, 18, 10, 0.4, 0, Math.PI * 2); }, '#2fa84f');
      t.P(function (g) { g.ellipse(80, 32, 18, 10, -0.4, 0, Math.PI * 2); }, '#2fa84f');
      t.P(circlePath(64, 38, 8), '#3cc85a');
    },
    gingerbread: function (t) {
      t.P(function (g) {
        g.arc(64, 30, 20, 0, Math.PI * 2);
        g.moveTo(44, 48); g.lineTo(84, 48); g.lineTo(112, 62); g.lineTo(104, 76); g.lineTo(84, 70);
        g.lineTo(90, 112); g.lineTo(74, 118); g.lineTo(64, 92); g.lineTo(54, 118); g.lineTo(38, 112);
        g.lineTo(44, 70); g.lineTo(24, 76); g.lineTo(16, 62); g.closePath();
      }, '#b8642a');
      t.K(circlePath(57, 28, 3), '#fff4d6'); t.K(circlePath(71, 28, 3), '#fff4d6');
      t.L(function (g) { g.arc(64, 34, 8, 0.3, Math.PI - 0.3); }, '#fff4d6', 3);
      [[64, 60], [64, 74]].forEach(function (q) { t.K(circlePath(q[0], q[1], 4), '#ff5a5a'); });
    },
    train: function (t) {
      t.P(function (g) { g.rect(20, 50, 64, 46); }, '#c4281c');
      t.P(function (g) { g.rect(70, 30, 34, 66); }, '#2a2a2e');
      t.P(function (g) { g.rect(28, 30, 16, 22); }, '#2a2a2e');
      t.K(function (g) { g.rect(78, 38, 18, 18); }, '#ffcf3a');
      [[36, 104], [64, 104], [92, 104]].forEach(function (q) { t.P(circlePath(q[0], q[1], 12), '#f2c230'); });
      t.P(circlePath(30, 18, 8), '#e8eef5');
    },
    krampus: function (t) {
      t.P(function (g) { g.moveTo(40, 54); g.bezierCurveTo(14, 40, 18, 12, 30, 4); g.bezierCurveTo(30, 24, 40, 34, 54, 42); g.closePath(); }, '#e8dcc4');
      t.P(function (g) { g.moveTo(88, 54); g.bezierCurveTo(114, 40, 110, 12, 98, 4); g.bezierCurveTo(98, 24, 88, 34, 74, 42); g.closePath(); }, '#e8dcc4');
      t.P(function (g) { g.ellipse(64, 76, 34, 40, 0, 0, Math.PI * 2); }, '#3a2a2a');
      t.K(polyPath([[46, 66], [58, 70], [48, 76]]), '#ff3b3b');
      t.K(polyPath([[82, 66], [70, 70], [80, 76]]), '#ff3b3b');
      t.K(polyPath([[50, 96], [78, 96], [64, 112]]), '#c4281c');
    },
    snowflake: function (t) {
      for (var k = 0; k < 6; k++) {
        var a = k * Math.PI / 3;
        t.L(function (g) {
          g.moveTo(64, 64); g.lineTo(64 + Math.cos(a) * 50, 64 + Math.sin(a) * 50);
          var bx = 64 + Math.cos(a) * 30, by = 64 + Math.sin(a) * 30;
          g.moveTo(bx, by); g.lineTo(bx + Math.cos(a + 0.7) * 14, by + Math.sin(a + 0.7) * 14);
          g.moveTo(bx, by); g.lineTo(bx + Math.cos(a - 0.7) * 14, by + Math.sin(a - 0.7) * 14);
        }, '#e8f8ff', 6);
      }
      t.P(circlePath(64, 64, 9), '#9fd8ff');
    },
    aurora: function (t) {
      ['#7dff9a', '#5ae8d8', '#b26bff'].forEach(function (c, i) {
        t.L(function (g) {
          g.moveTo(10, 60 - i * 12); g.bezierCurveTo(40, 20 - i * 10, 80, 90 - i * 10, 118, 40 - i * 12);
        }, c, 9);
      });
      t.P(starPath(28, 100, 10, 5), '#e8f8ff');
      t.P(starPath(96, 104, 7, 5), '#e8f8ff');
    },
    tree: function (t) {
      t.P(polyPath([[64, 6], [98, 50], [82, 50], [108, 84], [88, 84], [116, 112], [12, 112],
                    [40, 84], [20, 84], [46, 50], [30, 50]]), '#2fa84f');
      t.P(function (g) { g.rect(56, 112, 16, 14); }, '#6a4a2a');
      [[54, 44], [76, 70], [48, 90], [84, 98]].forEach(function (q, i) {
        t.K(circlePath(q[0], q[1], 5), ['#ff5a5a', '#ffcf3a', '#5ab4ff', '#ff5a5a'][i]);
      });
      t.P(starPath(64, 8, 10, 5), '#ffcf3a');
    }
  };

  function drawIcon(ctx, name, x, y, size, mono, ink) {
    var fn = ICONS[name];
    if (!fn) return false;
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(size / CELL, size / CELL);
    fn(iconPen(ctx, !!mono, ink || '#000'));
    ctx.restore();
    return true;
  }
  Textures.drawIcon = drawIcon;
  Textures.icons = Object.keys(ICONS);
  Object.keys(ICONS).forEach(function (name) {
    emblem('em_' + name, function (ctx) { drawIcon(ctx, name, 0, 0, CELL, false); });
  });
  // a few emblems go by older names
  emblem('em_champagne', function (ctx) { drawIcon(ctx, 'champagne', 0, 0, CELL, false); });

  /* A crate's stencil: a line of lettering over the icon and a line under
     it, sprayed in one ink through a cardboard template -- or, for the
     fancier crates, gilded or lit.  ``frame`` is 'box', 'round' or none. */
  function stencil(opts) {
    return function (ctx) {
      var ink = opts.ink || 'rgba(25,18,10,0.82)';
      var font = opts.font || 'Verdana, sans-serif';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      if (opts.glow) { ctx.shadowColor = opts.glow; ctx.shadowBlur = 8; }
      ctx.fillStyle = ink;
      ctx.font = 'bold ' + (opts.size || 17) + 'px ' + font;
      if (opts.top) ctx.fillText(opts.top, 64, 16);
      ctx.font = 'bold ' + (opts.size2 || 15) + 'px ' + font;
      if (opts.bottom) ctx.fillText(opts.bottom, 64, 113);
      ctx.shadowBlur = 0;
      if (opts.frame === 'box') {
        ctx.strokeStyle = ink; ctx.lineWidth = 4; ctx.strokeRect(14, 28, 100, 72);
      } else if (opts.frame === 'round') {
        ctx.strokeStyle = ink; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.arc(64, 64, 38, 0, Math.PI * 2); ctx.stroke();
      }
      drawIcon(ctx, opts.icon, 34, 34, 60, !opts.colour, ink);
    };
  }

  /* ----------------------------------------------------------- New Year
     The decals the New Year crates (2022 to 2026) are printed with. */

  // a clock dial: numerals, minute ticks, a cream face (the hands are parts)
  painter('clockface', function (ctx) {
    var g = ctx.createRadialGradient(56, 52, 8, 64, 64, 64);
    g.addColorStop(0, '#fffdf4'); g.addColorStop(1, '#e8dcc0');
    ctx.fillStyle = g; ctx.fillRect(0, 0, CELL, CELL);
    ctx.strokeStyle = '#2a1a08';
    for (var k = 0; k < 60; k++) {
      var a = k * Math.PI / 30, big = k % 5 === 0;
      ctx.lineWidth = big ? 3 : 1;
      ctx.beginPath();
      ctx.moveTo(64 + Math.sin(a) * (big ? 50 : 54), 64 - Math.cos(a) * (big ? 50 : 54));
      ctx.lineTo(64 + Math.sin(a) * 59, 64 - Math.cos(a) * 59);
      ctx.stroke();
    }
    ctx.fillStyle = '#2a1a08'; ctx.font = 'bold 13px Georgia, serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    var numerals = ['XII', 'I', 'II', 'III', 'IIII', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI'];
    for (k = 0; k < 12; k++) {
      var b = k * Math.PI / 6;
      ctx.fillText(numerals[k], 64 + Math.sin(b) * 40, 64 - Math.cos(b) * 40);
    }
  });

  // the first sunrise of 2022, across a visor
  painter('sunrise', function (ctx) {
    var sky = ctx.createLinearGradient(0, 0, 0, CELL);
    sky.addColorStop(0, '#2b2f6a'); sky.addColorStop(0.55, '#ff7a5a'); sky.addColorStop(1, '#ffd36a');
    ctx.fillStyle = sky; ctx.fillRect(0, 20, CELL, 88);
    ctx.fillStyle = '#fff3b0';
    ctx.beginPath(); ctx.arc(64, 96, 30, Math.PI, 0); ctx.fill();
    ctx.strokeStyle = 'rgba(255,243,176,0.8)'; ctx.lineWidth = 3;
    for (var k = 0; k < 7; k++) {
      var a = Math.PI + (k + 0.5) * Math.PI / 7;
      ctx.beginPath(); ctx.moveTo(64 + Math.cos(a) * 36, 96 + Math.sin(a) * 36);
      ctx.lineTo(64 + Math.cos(a) * 52, 96 + Math.sin(a) * 52); ctx.stroke();
    }
    ctx.fillStyle = '#141d45'; ctx.font = 'bold 16px Verdana, sans-serif';
    ctx.textAlign = 'center'; ctx.fillText('2022', 64, 34);
  });

  // a sweater print: a gold clock on navy
  painter('tee_clock', function (ctx) {
    ctx.fillStyle = '#f2c230';
    ctx.beginPath(); ctx.arc(64, 60, 34, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#fff8e0';
    ctx.beginPath(); ctx.arc(64, 60, 28, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#141d45'; ctx.lineWidth = 4; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(64, 60); ctx.lineTo(60, 40); ctx.moveTo(64, 60); ctx.lineTo(64, 36);
    ctx.stroke();
    ctx.fillStyle = '#f2c230'; ctx.font = 'bold 15px Verdana, sans-serif';
    ctx.textAlign = 'center'; ctx.fillText('00:00', 64, 112);
  });

  // sequins: overlapping discs, each catching its own light
  painter('sequins', function (ctx) {
    var rnd = scatter(43);
    for (var row = 0; row < 11; row++) {
      for (var col = 0; col < 11; col++) {
        var x = col * 12 + (row % 2 ? 6 : 0), y = row * 12;
        var lit = rnd();
        around(ctx, x, y, function (g) {
          g.fillStyle = 'rgba(0,0,0,0.25)';
          g.beginPath(); g.arc(0.6, 0.8, 6.2, 0, Math.PI * 2); g.fill();
          g.fillStyle = lit > 0.7 ? 'rgba(255,255,255,0.75)' : (lit > 0.35 ? 'rgba(255,255,255,0.28)'
                                                                          : 'rgba(0,0,0,0.12)');
          g.beginPath(); g.arc(0, 0, 5.4, 0, Math.PI * 2); g.fill();
          g.fillStyle = 'rgba(0,0,0,0.35)';
          g.beginPath(); g.arc(0, 0, 1.2, 0, Math.PI * 2); g.fill();
        });
      }
    }
  });

  // a fascinator's veil
  painter('netting', function (ctx) {
    ctx.strokeStyle = 'rgba(20,16,24,0.9)'; ctx.lineWidth = 1.4;
    for (var k = -CELL; k < CELL * 2; k += 10) {
      ctx.beginPath(); ctx.moveTo(k, 0); ctx.lineTo(k + CELL, CELL); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(k, CELL); ctx.lineTo(k + CELL, 0); ctx.stroke();
    }
    ctx.fillStyle = 'rgba(20,16,24,0.9)';
    for (var d = 0; d < 9; d++) {
      ctx.beginPath(); ctx.arc(14 + (d * 37) % 100, 18 + (d * 23) % 92, 2.6, 0, Math.PI * 2); ctx.fill();
    }
  });

  // a record: grooves, a sheen and the label left to the part beneath
  painter('vinyl', function (ctx) {
    ctx.fillStyle = '#141018'; ctx.fillRect(0, 0, CELL, CELL);
    for (var r = 22; r < 64; r += 2) {
      ctx.strokeStyle = r % 4 ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.5)';
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(64, 64, r, 0, Math.PI * 2); ctx.stroke();
    }
    var sheen = ctx.createLinearGradient(0, 0, CELL, CELL);
    sheen.addColorStop(0.35, 'rgba(255,255,255,0)'); sheen.addColorStop(0.5, 'rgba(255,255,255,0.16)');
    sheen.addColorStop(0.65, 'rgba(255,255,255,0)');
    ctx.fillStyle = sheen; ctx.fillRect(0, 0, CELL, CELL);
    ctx.fillStyle = '#ff2bd6'; ctx.beginPath(); ctx.arc(64, 64, 20, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#141018'; ctx.beginPath(); ctx.arc(64, 64, 3, 0, Math.PI * 2); ctx.fill();
  });

  // gold filigree: scrolls and dots over a gilded ground
  painter('filigree', function (ctx) {
    ctx.strokeStyle = 'rgba(90,60,10,0.55)'; ctx.lineWidth = 2.2; ctx.lineCap = 'round';
    for (var row = 0; row < 4; row++) {
      for (var col = 0; col < 4; col++) {
        var x = col * 32 + 16, y = row * 32 + 16;
        around(ctx, x, y, function (g) {
          g.beginPath(); g.arc(-6, 0, 7, -Math.PI / 2, Math.PI); g.stroke();
          g.beginPath(); g.arc(6, 0, 7, 0, Math.PI * 1.5); g.stroke();
          g.fillStyle = 'rgba(255,248,210,0.6)';
          g.beginPath(); g.arc(0, -10, 2, 0, Math.PI * 2); g.fill();
        });
      }
    }
  });

  // the tailcoat: white shirt front, black tie, gold sequin lapels
  painter('tee_tailcoat', function (ctx) {
    ctx.fillStyle = '#f6f4ee';
    ctx.beginPath(); ctx.moveTo(48, 0); ctx.lineTo(80, 0); ctx.lineTo(72, 128); ctx.lineTo(56, 128);
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#e8c46a';
    ctx.beginPath(); ctx.moveTo(30, 0); ctx.lineTo(48, 0); ctx.lineTo(60, 70); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.moveTo(98, 0); ctx.lineTo(80, 0); ctx.lineTo(68, 70); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#f6f4ee';
    ctx.beginPath(); ctx.moveTo(52, 10); ctx.lineTo(64, 18); ctx.lineTo(52, 26); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.moveTo(76, 10); ctx.lineTo(64, 18); ctx.lineTo(76, 26); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#141019';
    [50, 74, 98].forEach(function (y) { ctx.beginPath(); ctx.arc(64, y, 3, 0, Math.PI * 2); ctx.fill(); });
  });

  // red firecracker paper: gold characters in rows
  painter('firecracker', function (ctx) {
    ctx.strokeStyle = 'rgba(255,214,90,0.75)'; ctx.lineWidth = 2;
    for (var row = 0; row < 5; row++) {
      for (var col = 0; col < 4; col++) {
        var x = col * 32 + (row % 2 ? 16 : 0), y = row * 26 + 13;
        around(ctx, x, y, function (g) {
          g.beginPath(); g.moveTo(-6, -6); g.lineTo(6, -6); g.moveTo(0, -8); g.lineTo(0, 7);
          g.moveTo(-5, 1); g.lineTo(5, 1); g.moveTo(-6, 7); g.lineTo(6, 7); g.stroke();
        });
      }
    }
  });

  // the pyro crew's back print
  painter('tee_rocket', function (ctx) {
    ctx.fillStyle = '#2b2b30';
    ctx.beginPath(); ctx.moveTo(64, 14); ctx.lineTo(78, 40); ctx.lineTo(78, 92); ctx.lineTo(50, 92);
    ctx.lineTo(50, 40); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#ffcf3a';
    ctx.beginPath(); ctx.moveTo(56, 92); ctx.lineTo(72, 92); ctx.lineTo(64, 118); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#2b2b30'; ctx.font = 'bold 12px Verdana, sans-serif';
    ctx.textAlign = 'center'; ctx.fillText('PYRO CREW', 64, 124);
  });

  // a synthwave grid in perspective-free neon: magenta lines on transparent
  painter('neongrid', function (ctx) {
    ctx.strokeStyle = 'rgba(255,43,214,0.85)'; ctx.lineWidth = 2;
    for (var k = 0; k <= CELL; k += 16) {
      ctx.beginPath(); ctx.moveTo(k, 0); ctx.lineTo(k, CELL); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, k); ctx.lineTo(CELL, k); ctx.stroke();
    }
    ctx.strokeStyle = 'rgba(25,240,255,0.55)'; ctx.lineWidth = 1;
    for (k = 8; k <= CELL; k += 16) {
      ctx.beginPath(); ctx.moveTo(0, k); ctx.lineTo(CELL, k); ctx.stroke();
    }
  });

  // mirror tiles for a disco ball: a grid of facets, each its own brightness
  painter('mirror', function (ctx) {
    var rnd = scatter(53);
    for (var row = 0; row < 12; row++) {
      for (var col = 0; col < 12; col++) {
        var v = rnd();
        ctx.fillStyle = v > 0.85 ? 'rgba(255,255,255,0.95)' : (v > 0.5 ? 'rgba(255,255,255,0.35)'
                                                                        : 'rgba(30,40,60,0.35)');
        ctx.fillRect(col * 10.67 + 1, row * 10.67 + 1, 8.7, 8.7);
        if (v > 0.93) {
          ctx.fillStyle = ['rgba(255,43,214,0.6)', 'rgba(25,240,255,0.6)'][col % 2];
          ctx.fillRect(col * 10.67 + 1, row * 10.67 + 1, 8.7, 8.7);
        }
      }
    }
  });

  // a cassette label
  painter('cassette', function (ctx) {
    ctx.fillStyle = '#f4f0e6'; ctx.fillRect(0, 0, CELL, CELL);
    ctx.fillStyle = '#ff2bd6'; ctx.fillRect(0, 0, CELL, 22);
    ctx.fillStyle = '#19f0ff'; ctx.fillRect(0, 22, CELL, 8);
    ctx.fillStyle = '#2a2a33'; ctx.font = 'bold 15px Verdana, sans-serif';
    ctx.textAlign = 'center'; ctx.fillText('MIDNIGHT MIX', 64, 50);
    ctx.font = 'bold 12px Verdana, sans-serif'; ctx.fillText('SIDE A  2025', 64, 70);
    ctx.fillStyle = '#2a2a33';
    ctx.fillRect(28, 84, 72, 26);
    ctx.fillStyle = '#f4f0e6';
    ctx.beginPath(); ctx.arc(44, 97, 8, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.arc(84, 97, 8, 0, Math.PI * 2); ctx.fill();
  });

  // a sunset over a grid, for a synthwave visor
  painter('sunset_grid', function (ctx) {
    var sky = ctx.createLinearGradient(0, 0, 0, 72);
    sky.addColorStop(0, '#2a0a4a'); sky.addColorStop(1, '#ff2bd6');
    ctx.fillStyle = sky; ctx.fillRect(0, 0, CELL, 72);
    var sun = ctx.createLinearGradient(0, 30, 0, 72);
    sun.addColorStop(0, '#ffe36b'); sun.addColorStop(1, '#ff4fa0');
    ctx.fillStyle = sun;
    ctx.beginPath(); ctx.arc(64, 72, 30, Math.PI, 0); ctx.fill();
    ctx.fillStyle = '#2a0a4a';
    for (var k = 0; k < 4; k++) ctx.fillRect(30, 52 + k * 5, 68, 2);
    ctx.fillStyle = '#0d0221'; ctx.fillRect(0, 72, CELL, 56);
    ctx.strokeStyle = '#19f0ff'; ctx.lineWidth = 1.5;
    for (k = -8; k <= 8; k++) {
      ctx.beginPath(); ctx.moveTo(64 + k * 4, 72); ctx.lineTo(64 + k * 22, 128); ctx.stroke();
    }
    for (k = 0; k < 6; k++) {
      var y = 72 + Math.pow(k / 5, 1.6) * 56;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(CELL, y); ctx.stroke();
    }
  });

  // piano keys, for the keytar
  painter('keys', function (ctx) {
    ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, CELL, CELL);
    ctx.strokeStyle = '#7a7d84'; ctx.lineWidth = 1;
    for (var k = 0; k <= 16; k++) {
      ctx.beginPath(); ctx.moveTo(k * 8, 0); ctx.lineTo(k * 8, CELL); ctx.stroke();
    }
    ctx.fillStyle = '#1a1a22';
    [1, 2, 4, 5, 6, 8, 9, 11, 12, 13, 15].forEach(function (k) { ctx.fillRect(k * 8 - 2.5, 0, 5, 76); });
  });

  // frosted glass: a bloom of frost from the corners and a fine grain
  painter('frost', function (ctx) {
    var rnd = scatter(61);
    ctx.strokeStyle = 'rgba(255,255,255,0.55)'; ctx.lineWidth = 1.2;
    for (var k = 0; k < 26; k++) {
      var x = rnd() * CELL, y = rnd() * CELL, len = 8 + rnd() * 16, a = rnd() * Math.PI * 2;
      around(ctx, x, y, function (g) {
        g.beginPath(); g.moveTo(0, 0); g.lineTo(Math.cos(a) * len, Math.sin(a) * len);
        g.moveTo(Math.cos(a) * len * 0.5, Math.sin(a) * len * 0.5);
        g.lineTo(Math.cos(a + 0.6) * len * 0.8, Math.sin(a + 0.6) * len * 0.8); g.stroke();
      });
    }
    for (k = 0; k < 400; k++) {
      ctx.fillStyle = 'rgba(255,255,255,' + (0.05 + rnd() * 0.2) + ')';
      ctx.fillRect(rnd() * CELL, rnd() * CELL, 1.5, 1.5);
    }
  });

  // an LED ticker
  painter('ticker', function (ctx) {
    ctx.fillStyle = '#05080e'; ctx.fillRect(0, 0, CELL, CELL);
    ctx.fillStyle = '#ff5a3a'; ctx.font = 'bold 30px Courier New, monospace';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.shadowColor = '#ff5a3a'; ctx.shadowBlur = 6;
    ctx.fillText('3..2..1', 64, 64);
    ctx.shadowBlur = 0;
    ctx.fillStyle = 'rgba(0,0,0,0.5)';
    for (var k = 0; k < CELL; k += 4) { ctx.fillRect(k, 0, 1, CELL); ctx.fillRect(0, k, CELL, 1); }
  });

  // a card crown's cut-out year and a scatter of confetti
  painter('year2026', function (ctx) {
    ctx.fillStyle = 'rgba(27,44,74,0.9)'; ctx.font = 'bold 26px Verdana, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('2026', 32, 92); ctx.fillText('2026', 96, 92);
    var rnd = scatter(71);
    for (var k = 0; k < 18; k++) {
      ctx.fillStyle = ['#ff6ad5', '#9fd8ff', '#ffd36a'][k % 3];
      ctx.fillRect(rnd() * CELL, 20 + rnd() * 40, 5, 3);
    }
  });

  painter('stencil_ny22', stencil({ top: 'FIRST LIGHT', bottom: '01.01.2022', icon: 'clock',
                                    ink: 'rgba(242,194,48,0.92)', frame: 'box' }));
  painter('stencil_ny23', stencil({ top: 'GLITTERFALL', bottom: 'GALA  2023', icon: 'champagne',
                                    ink: 'rgba(232,196,106,0.95)', font: 'Georgia, serif',
                                    frame: 'round' }));
  painter('stencil_ny24', stencil({ top: 'ROCKET RALLY', bottom: 'HANDLE WITH JOY', icon: 'firework',
                                    ink: 'rgba(20,20,24,0.85)', frame: 'box', size2: 12 }));
  painter('stencil_ny25', stencil({ top: 'NEON MIDNIGHT', bottom: '- 2025 -', icon: 'cassette',
                                    ink: 'rgba(255,43,214,0.95)', glow: '#ff2bd6', size: 15 }));
  painter('stencil_ny26', stencil({ top: 'CRYSTAL', bottom: 'COUNTDOWN 2026', icon: 'crystal',
                                    ink: 'rgba(223,242,255,0.95)', glow: '#9fd8ff', size2: 13 }));

  /* ----------------------------------------------------------- Halloween
     The decals of the Halloween crates, 2022 to 2025 (2026's are above). */

  // R.I.P. cut into weathered stone, with a crack and some lichen
  painter('tombstone', function (ctx) {
    var rnd = scatter(71);
    ctx.fillStyle = '#9a9ea3'; ctx.fillRect(0, 0, CELL, CELL);
    for (var k = 0; k < 140; k++) {
      ctx.fillStyle = 'rgba(' + (rnd() > 0.5 ? '255,255,255' : '40,44,48') + ',' + (0.05 + rnd() * 0.1) + ')';
      ctx.fillRect(rnd() * CELL, rnd() * CELL, 2 + rnd() * 5, 2 + rnd() * 5);
    }
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = 'bold 30px Georgia, serif';
    ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.fillText('R.I.P.', 65, 47);
    ctx.fillStyle = '#3f4347'; ctx.fillText('R.I.P.', 64, 46);
    ctx.font = 'bold 12px Georgia, serif';
    ctx.fillText('HERE LIES', 64, 76);
    ctx.fillText('???', 64, 92);
    ctx.strokeStyle = '#3f4347'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(98, 8); ctx.lineTo(90, 30); ctx.lineTo(96, 42); ctx.lineTo(88, 60); ctx.stroke();
    ctx.fillStyle = 'rgba(110,140,70,0.55)';
    for (k = 0; k < 9; k++) {
      ctx.beginPath(); ctx.arc(8 + rnd() * 30, 100 + rnd() * 26, 3 + rnd() * 5, 0, Math.PI * 2); ctx.fill();
    }
  });

  // a cobweb: spokes and a spiral, on nothing (drawn with a = -1)
  painter('cobweb', function (ctx) {
    ctx.strokeStyle = 'rgba(240,244,248,0.85)'; ctx.lineWidth = 1.5;
    var cx = 10, cy = 10, spokes = 7;
    for (var k = 0; k < spokes; k++) {
      var a = (k / (spokes - 1)) * Math.PI / 2;
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(a) * 130, cy + Math.sin(a) * 130); ctx.stroke();
    }
    for (var r = 18; r < 130; r += 14) {
      ctx.beginPath();
      for (k = 0; k < spokes; k++) {
        var b = (k / (spokes - 1)) * Math.PI / 2;
        var sag = k % 2 ? 0.92 : 1;
        var x = cx + Math.cos(b) * r * sag, y = cy + Math.sin(b) * r * sag;
        if (k === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
  });

  // a ribcage in glow ink, on a black tee
  painter('tee_ribs', function (ctx) {
    ctx.fillStyle = '#e8fff0'; ctx.strokeStyle = '#e8fff0';
    ctx.shadowColor = '#9fe870'; ctx.shadowBlur = 6;
    ctx.fillRect(60, 14, 8, 92);
    ctx.lineWidth = 6; ctx.lineCap = 'round';
    for (var k = 0; k < 5; k++) {
      var y = 26 + k * 15, w = 40 - Math.abs(k - 1.5) * 4;
      ctx.beginPath(); ctx.moveTo(60, y); ctx.quadraticCurveTo(60 - w, y - 4, 64 - w - 4, y + 12); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(68, y); ctx.quadraticCurveTo(68 + w, y - 4, 64 + w + 4, y + 12); ctx.stroke();
    }
    ctx.beginPath(); ctx.arc(64, 112, 12, Math.PI, 0); ctx.fill();
    ctx.shadowBlur = 0;
  });

  painter('stencil_hw22', stencil({ top: 'GRAVEYARD', bottom: 'SHIFT  2022', icon: 'coffin',
                                    ink: 'rgba(159,232,112,0.9)', glow: '#6bff9a', frame: 'box' }));

  // the night sky inside a cloak: deep purple, scattered stars, a few bright
  painter('starfield', function (ctx) {
    var rnd = scatter(83);
    var g = ctx.createLinearGradient(0, 0, 0, CELL);
    g.addColorStop(0, '#1a0d2a'); g.addColorStop(1, '#2a1640');
    ctx.fillStyle = g; ctx.fillRect(0, 0, CELL, CELL);
    for (var k = 0; k < 70; k++) {
      var big = rnd() > 0.88;
      ctx.fillStyle = big ? '#fff3b0' : 'rgba(233,220,255,' + (0.4 + rnd() * 0.5) + ')';
      var x = rnd() * CELL, y = rnd() * CELL, r = big ? 2.2 : 0.6 + rnd();
      ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
    }
    ctx.fillStyle = '#fff3b0';
    ctx.beginPath(); ctx.arc(92, 30, 12, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#1a0d2a';
    ctx.beginPath(); ctx.arc(98, 26, 11, 0, Math.PI * 2); ctx.fill();
  });

  // a crescent moon and stars on a robe
  painter('tee_moon', function (ctx) {
    ctx.fillStyle = '#fff3b0';
    ctx.beginPath(); ctx.arc(64, 58, 30, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#3a1f5a';
    ctx.beginPath(); ctx.arc(78, 50, 28, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#c9ccd8';
    [[30, 24, 5], [100, 92, 4], [40, 100, 3], [96, 18, 3], [22, 70, 3]].forEach(function (st) {
      ctx.beginPath();
      for (var k = 0; k < 10; k++) {
        var a = k * Math.PI / 5 - Math.PI / 2, r = k % 2 ? st[2] * 0.45 : st[2];
        ctx.lineTo(st[0] + Math.cos(a) * r * 2, st[1] + Math.sin(a) * r * 2);
      }
      ctx.closePath(); ctx.fill();
    });
  });

  // a witch's stockings: purple and black, round and round
  painter('witch_stripes', function (ctx) {
    for (var y = 0; y < CELL; y += 16) {
      ctx.fillStyle = '#4a2470'; ctx.fillRect(0, y, CELL, 8);
      ctx.fillStyle = '#16101e'; ctx.fillRect(0, y + 8, CELL, 8);
    }
  });

  painter('stencil_hw23', stencil({ top: 'WITCHING', bottom: 'HOUR  2023', icon: 'cauldron',
                                    ink: 'rgba(178,107,255,0.92)', glow: '#b26bff',
                                    font: 'Georgia, serif', frame: 'round' }));

  // slate roof shingles: fish-scale rows, each tile a slightly different slate
  painter('shingles', function (ctx) {
    var rnd = scatter(97);
    ctx.fillStyle = '#211c27'; ctx.fillRect(0, 0, CELL, CELL);
    for (var row = 0; row < 9; row++) {
      var y = row * 16 - 4, off = row % 2 ? 8 : 0;
      for (var x = -16 + off; x < CELL + 16; x += 16) {
        var v = 52 + Math.floor(rnd() * 22);
        ctx.fillStyle = 'rgb(' + v + ',' + (v - 6) + ',' + (v + 10) + ')';
        ctx.beginPath();
        ctx.moveTo(x, y); ctx.lineTo(x + 16, y); ctx.lineTo(x + 16, y + 12);
        ctx.arc(x + 8, y + 12, 8, 0, Math.PI);
        ctx.closePath(); ctx.fill();
        ctx.strokeStyle = 'rgba(10,8,14,0.7)'; ctx.lineWidth = 1.2; ctx.stroke();
        ctx.fillStyle = 'rgba(255,255,255,0.08)'; ctx.fillRect(x + 2, y + 2, 4, 9);
      }
    }
    // moss in the gaps
    ctx.fillStyle = 'rgba(96,120,70,0.35)';
    for (var k = 0; k < 12; k++) {
      ctx.beginPath(); ctx.arc(rnd() * CELL, rnd() * CELL, 1.5 + rnd() * 2.5, 0, Math.PI * 2); ctx.fill();
    }
  });

  // old soot-dark brick: staggered courses, crumbling mortar
  painter('bricks', function (ctx) {
    var rnd = scatter(101);
    ctx.fillStyle = '#6d6259'; ctx.fillRect(0, 0, CELL, CELL);
    for (var row = 0; row < 8; row++) {
      var off = row % 2 ? 16 : 0;
      for (var x = -32 + off; x < CELL; x += 32) {
        var r = 92 + Math.floor(rnd() * 40), g = 38 + Math.floor(rnd() * 18);
        ctx.fillStyle = 'rgb(' + r + ',' + g + ',' + (g - 6) + ')';
        ctx.fillRect(x + 2, row * 16 + 2, 28, 12);
        ctx.fillStyle = 'rgba(20,12,10,' + (0.15 + rnd() * 0.3) + ')';
        ctx.fillRect(x + 2, row * 16 + 2 + rnd() * 6, 28, 6);
      }
    }
    var soot = ctx.createLinearGradient(0, 0, 0, CELL);
    soot.addColorStop(0, 'rgba(10,8,8,0.55)'); soot.addColorStop(0.5, 'rgba(10,8,8,0)');
    ctx.fillStyle = soot; ctx.fillRect(0, 0, CELL, CELL);
  });

  // black mourning lace: a net of fine threads round little roses, on nothing
  painter('lace', function (ctx) {
    ctx.strokeStyle = 'rgba(132,116,142,0.85)'; ctx.lineWidth = 1;
    for (var d = -CELL; d < CELL * 2; d += 10) {
      ctx.beginPath(); ctx.moveTo(d, 0); ctx.lineTo(d + CELL, CELL); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(d, CELL); ctx.lineTo(d + CELL, 0); ctx.stroke();
    }
    ctx.lineWidth = 1.8; ctx.strokeStyle = 'rgba(176,160,186,0.95)';
    [[24, 24], [88, 24], [56, 64], [24, 104], [88, 104]].forEach(function (c) {
      for (var k = 0; k < 6; k++) {
        var a = k * Math.PI / 3;
        ctx.beginPath();
        ctx.ellipse(c[0] + Math.cos(a) * 7, c[1] + Math.sin(a) * 7, 6, 3.5, a, 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.beginPath(); ctx.arc(c[0], c[1], 3, 0, Math.PI * 2); ctx.stroke();
    });
    // a scalloped edge along the bottom
    ctx.beginPath();
    for (var x = 0; x < CELL; x += 12) ctx.arc(x + 6, CELL - 6, 6, Math.PI, 0);
    ctx.stroke();
  });

  // an ancestor in oils, whose eyes have been following you round the room
  painter('portrait', function (ctx) {
    var g = ctx.createRadialGradient(64, 54, 6, 64, 64, 80);
    g.addColorStop(0, '#4a3a2a'); g.addColorStop(1, '#120d0a');
    ctx.fillStyle = g; ctx.fillRect(0, 0, CELL, CELL);
    // coat and cravat
    ctx.fillStyle = '#17141c';
    ctx.beginPath(); ctx.moveTo(14, 128); ctx.quadraticCurveTo(22, 88, 64, 84);
    ctx.quadraticCurveTo(106, 88, 114, 128); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#e8e0cc';
    ctx.beginPath(); ctx.moveTo(56, 86); ctx.lineTo(72, 86); ctx.lineTo(64, 106); ctx.closePath(); ctx.fill();
    // a long pale face
    ctx.fillStyle = '#cdb79a';
    ctx.beginPath(); ctx.ellipse(64, 56, 20, 28, 0, 0, Math.PI * 2); ctx.fill();
    // hair and side whiskers
    ctx.fillStyle = '#3a2c22';
    ctx.beginPath(); ctx.ellipse(64, 32, 22, 10, 0, Math.PI, 0); ctx.fill();
    ctx.fillRect(43, 32, 6, 34); ctx.fillRect(79, 32, 6, 34);
    // the eyes: whites, and pupils turned to look straight out
    ctx.fillStyle = '#f2ead8';
    ctx.beginPath(); ctx.ellipse(56, 52, 5, 3, 0, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.ellipse(72, 52, 5, 3, 0, 0, Math.PI * 2); ctx.fill();
    ctx.shadowColor = '#ff3b3b'; ctx.shadowBlur = 5; ctx.fillStyle = '#7a0f0f';
    ctx.beginPath(); ctx.arc(56, 52, 2.2, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.arc(72, 52, 2.2, 0, Math.PI * 2); ctx.fill();
    ctx.shadowBlur = 0;
    // a thin unsmiling mouth
    ctx.strokeStyle = '#6a4434'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(57, 70); ctx.lineTo(71, 70); ctx.stroke();
    // craquelure over the varnish
    ctx.strokeStyle = 'rgba(0,0,0,0.25)'; ctx.lineWidth = 0.6;
    var rnd = scatter(103);
    for (var k = 0; k < 18; k++) {
      var x = rnd() * CELL, y = rnd() * CELL;
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + rnd() * 14 - 7, y + rnd() * 14 - 7); ctx.stroke();
    }
  });

  // a smoking jacket's front: a quilted shawl collar and gold frogging
  painter('tee_frogging', function (ctx) {
    ctx.fillStyle = '#2a0a14';
    ctx.beginPath(); ctx.moveTo(30, 0); ctx.quadraticCurveTo(40, 60, 62, 92); ctx.lineTo(62, 0); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.moveTo(98, 0); ctx.quadraticCurveTo(88, 60, 66, 92); ctx.lineTo(66, 0); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.10)'; ctx.lineWidth = 1;
    for (var q = 8; q < 90; q += 10) {
      ctx.beginPath(); ctx.moveTo(36, q); ctx.lineTo(60, q + 8); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(92, q); ctx.lineTo(68, q + 8); ctx.stroke();
    }
    ctx.strokeStyle = '#c9a227'; ctx.lineWidth = 3; ctx.lineCap = 'round';
    for (var k = 0; k < 4; k++) {
      var y = 52 + k * 17;
      ctx.beginPath(); ctx.moveTo(38, y); ctx.lineTo(90, y); ctx.stroke();
      ctx.beginPath(); ctx.arc(38, y, 4, Math.PI * 0.5, Math.PI * 1.5); ctx.stroke();
      ctx.beginPath(); ctx.arc(90, y, 4, -Math.PI * 0.5, Math.PI * 0.5); ctx.stroke();
      ctx.fillStyle = '#e8c24a';
      ctx.beginPath(); ctx.arc(64, y, 3.5, 0, Math.PI * 2); ctx.fill();
    }
  });

  // pinstripes: fine chalk lines, on nothing, all the way round
  painter('pinstripe', function (ctx) {
    ctx.fillStyle = 'rgba(220,214,200,0.55)';
    for (var x = 4; x < CELL; x += 16) ctx.fillRect(x, 0, 1.5, CELL);
  });

  painter('stencil_hw24', stencil({ top: 'WHISPER', bottom: 'MANOR  2024', icon: 'manor',
                                    ink: 'rgba(255,211,106,0.92)', glow: '#ffd36a',
                                    font: 'Georgia, serif', frame: 'box' }));

  /* ----------------------------------------------------------- St. Patrick's
     The decals of the St. Patrick's crates, 2022 to 2026. */

  // a shamrock: three heart leaves round a centre and a curling stem
  function spShamrock(ctx, x, y, s, fill, rot) {
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot || 0); ctx.fillStyle = fill;
    [0, 2.1, -2.1].forEach(function (a) {
      ctx.save(); ctx.rotate(a); ctx.translate(0, -s * 0.48);
      ctx.beginPath(); ctx.moveTo(0, s * 0.42);
      ctx.bezierCurveTo(-s * 0.62, -s * 0.02, -s * 0.30, -s * 0.52, 0, -s * 0.20);
      ctx.bezierCurveTo(s * 0.30, -s * 0.52, s * 0.62, -s * 0.02, 0, s * 0.42); ctx.fill();
      ctx.restore();
    });
    ctx.strokeStyle = fill; ctx.lineWidth = Math.max(1, s * 0.12); ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(s * 0.05, s * 0.55, s * 0.32, s * 0.85);
    ctx.stroke();
    ctx.restore();
  }

  // ---- 2022: Lucky Lep's Lockbox

  // a cobbler's brogue: oiled leather, a stitched seam and rows of punched
  // holes sweeping round in a wingtip
  painter('sp_brogue', function (ctx) {
    var rnd = scatter(223);
    for (var i = 0; i < 320; i++) {
      ctx.fillStyle = rnd() > 0.5 ? 'rgba(0,0,0,0.13)' : 'rgba(255,255,255,0.07)';
      ctx.beginPath(); ctx.arc(rnd() * CELL, rnd() * CELL, 1 + rnd() * 2.5, 0, Math.PI * 2); ctx.fill();
    }
    function holes(path, n, big) {
      for (var k = 0; k <= n; k++) {
        var q = path(k / n);
        ctx.fillStyle = 'rgba(255,255,255,0.16)';
        ctx.beginPath(); ctx.arc(q[0] + 0.6, q[1] + 0.6, big ? 3.2 : 2.2, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = 'rgba(8,14,8,0.70)';
        ctx.beginPath(); ctx.arc(q[0], q[1], big ? 2.4 : 1.5, 0, Math.PI * 2); ctx.fill();
      }
    }
    // the wingtip: a W of punched holes, twice over
    [0, 9].forEach(function (off) {
      holes(function (t) {
        var x = 6 + t * 116;
        return [x, 58 + off + Math.abs(Math.sin(t * Math.PI * 2)) * -34];
      }, 26, off === 0);
    });
    // stitched seams top and bottom
    ctx.strokeStyle = 'rgba(232,216,170,0.55)'; ctx.lineWidth = 1.6;
    ctx.setLineDash([5, 4]);
    [8, 118].forEach(function (y) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(CELL, y); ctx.stroke(); });
    ctx.setLineDash([]);
    // the medallion
    for (var r = 0; r < 3; r++) {
      for (var a = 0; a < 10 + r * 6; a++) {
        var ang = a / (10 + r * 6) * Math.PI * 2;
        ctx.fillStyle = 'rgba(8,14,8,0.65)';
        ctx.beginPath(); ctx.arc(64 + Math.cos(ang) * (5 + r * 7), 92 + Math.sin(ang) * (5 + r * 7), 1.5, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  });

  // a gold coin, struck with a shamrock and a beaded rim
  painter('sp_coin', function (ctx) {
    var g = ctx.createRadialGradient(50, 46, 6, 64, 64, 64);
    g.addColorStop(0, '#fff3b0'); g.addColorStop(0.55, '#f2c230'); g.addColorStop(1, '#b8860b');
    ctx.fillStyle = g; ctx.fillRect(0, 0, CELL, CELL);
    ctx.strokeStyle = 'rgba(120,80,10,0.8)'; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.arc(64, 64, 54, 0, Math.PI * 2); ctx.stroke();
    for (var k = 0; k < 36; k++) {
      var a = k / 36 * Math.PI * 2;
      ctx.fillStyle = 'rgba(255,243,176,0.9)';
      ctx.beginPath(); ctx.arc(64 + Math.cos(a) * 47, 64 + Math.sin(a) * 47, 2.2, 0, Math.PI * 2); ctx.fill();
    }
    spShamrock(ctx, 66, 66, 40, 'rgba(140,96,10,0.55)');
    spShamrock(ctx, 64, 63, 40, '#ffe58a');
  });

  // Lep's waistcoat: a white shirt-front, a green bow, a gold-buttoned
  // waistcoat buttoned to the throat and a shamrock in the buttonhole
  painter('sp_tee_waistcoat', function (ctx) {
    ctx.fillStyle = '#f4f1e6';
    ctx.beginPath(); ctx.moveTo(44, 0); ctx.lineTo(84, 0); ctx.lineTo(64, 44); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#c99a2a';
    ctx.beginPath(); ctx.moveTo(40, 0); ctx.lineTo(62, 46); ctx.lineTo(62, 128); ctx.lineTo(28, 128);
    ctx.lineTo(24, 20); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.moveTo(88, 0); ctx.lineTo(66, 46); ctx.lineTo(66, 128); ctx.lineTo(100, 128);
    ctx.lineTo(104, 20); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = 'rgba(90,60,10,0.5)'; ctx.lineWidth = 1;
    for (var y = 6; y < 128; y += 7) {
      ctx.beginPath(); ctx.moveTo(26, y); ctx.lineTo(62, y + 4); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(102, y); ctx.lineTo(66, y + 4); ctx.stroke();
    }
    ctx.fillStyle = '#1f6b34';
    ctx.beginPath(); ctx.moveTo(64, 12); ctx.lineTo(48, 4); ctx.lineTo(48, 20); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.moveTo(64, 12); ctx.lineTo(80, 4); ctx.lineTo(80, 20); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.arc(64, 12, 4, 0, Math.PI * 2); ctx.fill();
    for (var b = 0; b < 4; b++) {
      ctx.fillStyle = '#7a5a10';
      ctx.beginPath(); ctx.arc(65, 59 + b * 17, 5, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#ffd34a';
      ctx.beginPath(); ctx.arc(64, 58 + b * 17, 4.5, 0, Math.PI * 2); ctx.fill();
    }
    ctx.strokeStyle = '#3a2a10'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(30, 96); ctx.lineTo(50, 96); ctx.moveTo(78, 96); ctx.lineTo(98, 96); ctx.stroke();
    spShamrock(ctx, 92, 40, 18, '#4fc46e');
  });

  painter('stencil_sp22', stencil({ top: "LUCKY LEP'S", bottom: 'LOCKBOX  2022', icon: 'shamrock',
                                    ink: 'rgba(255,211,74,0.94)', font: 'Georgia, serif',
                                    frame: 'box', size: 16 }));
  // @@ stpatricks painters go above this line @@

  /* ----------------------------------------------------------- Easter
     The decals of the Easter crates, 2022 to 2026. */
  // @@ easter painters go above this line @@

  /* ----------------------------------------------------------- Fourth of July
     The decals of the Fourth of July crates, 2022 to 2026. */
  // @@ july4 painters go above this line @@

  /* ----------------------------------------------------------- Christmas
     The decals of the Christmas crates, 2022 to 2026. */
  // @@ christmas painters go above this line @@

  Textures.emblems = Object.keys(emblems);
  /* Draw an emblem onto any 2D context, ``size`` pixels square. */
  Textures.paintEmblem = function (ctx, name, x, y, size) {
    var fn = emblems[name];
    if (!fn) return false;
    ctx.save();
    ctx.translate(x || 0, y || 0);
    ctx.scale((size || CELL) / CELL, (size || CELL) / CELL);
    fn(ctx);
    ctx.restore();
    return true;
  };

  Textures.drawText = function (key, text, background, colour, fontSize) {
    if (Textures.slots['text:' + key]) return Textures.slots['text:' + key];
    var slot = allocate('text:' + key);
    var ctx = cellContext(slot, background || '#f2f3f3');
    ctx.fillStyle = colour || '#1b2a35';
    ctx.font = 'bold ' + (fontSize || 20) + 'px Verdana, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    var words = String(text).split(' ');
    var lines = [];
    var line = '';
    words.forEach(function (w) {
      var test = line ? line + ' ' + w : w;
      if (ctx.measureText(test).width > CELL - 10 && line) { lines.push(line); line = w; }
      else line = test;
    });
    if (line) lines.push(line);
    var startY = CELL / 2 - ((lines.length - 1) * (fontSize || 20)) / 2;
    lines.forEach(function (l, i) {
      ctx.fillText(l, CELL / 2, startY + i * (fontSize || 20) * 1.05);
    });
    ctx.restore();
    painted(slot);
    return slot;
  };

  /* A sign: text the map names itself, "t~TEXT~background~colour~aspect".

     The cell is square but the sign it is printed on is not, and a decal is
     stretched over the whole face.  So the lettering is laid out at the
     sign's real proportions on a canvas of its own and then squeezed into
     the cell -- the face stretches it back out, and the letters arrive the
     shape they were drawn.  Signs are painted the first time something asks
     for one rather than at start-up, so a map's signage only spends atlas
     cells on the area that is actually being played. */
  function drawSign(key, name) {
    var bits = name.split('~');
    var text = bits[1] || '', bg = bits[2] || '#f2f3f3', fg = bits[3] || '#1b2a35';
    var aspect = Math.max(0.2, Math.min(12, parseFloat(bits[4]) || 1));
    var w = aspect >= 1 ? Math.round(CELL * aspect) : CELL;
    var h = aspect >= 1 ? CELL : Math.round(CELL / aspect);
    var scratch = document.createElement('canvas');
    scratch.width = w; scratch.height = h;
    var c = scratch.getContext('2d');
    c.fillStyle = bg; c.fillRect(0, 0, w, h);
    c.strokeStyle = 'rgba(0,0,0,0.25)'; c.lineWidth = Math.max(2, h * 0.04);
    c.strokeRect(c.lineWidth / 2, c.lineWidth / 2, w - c.lineWidth, h - c.lineWidth);
    c.fillStyle = fg;
    c.textAlign = 'center'; c.textBaseline = 'middle';
    // the largest size whose wrapped lines fit both ways
    var words = text.split(' ');
    var size = Math.floor(h * 0.78), lines = [text];
    for (; size > 8; size -= 2) {
      c.font = 'bold ' + size + 'px Verdana, sans-serif';
      lines = [];
      var line = '';
      for (var i = 0; i < words.length; i++) {
        var test = line ? line + ' ' + words[i] : words[i];
        if (c.measureText(test).width > w * 0.9 && line) { lines.push(line); line = words[i]; }
        else line = test;
      }
      if (line) lines.push(line);
      var widest = 0;
      lines.forEach(function (l) { widest = Math.max(widest, c.measureText(l).width); });
      if (widest <= w * 0.92 && lines.length * size * 1.08 <= h * 0.9) break;
    }
    c.font = 'bold ' + size + 'px Verdana, sans-serif';
    var top = h / 2 - (lines.length - 1) * size * 1.08 / 2;
    lines.forEach(function (l, k) { c.fillText(l, w / 2, top + k * size * 1.08 + size * 0.04); });
    var slot = allocate(key);
    var ctx = cellContext(slot, null);
    ctx.drawImage(scratch, 0, 0, w, h, 0, 0, CELL, CELL);
    ctx.restore();
    painted(slot);
    return slot;
  }

  /* Give back every sign's cell.  A world that swaps its whole map (Last
     Light moves to a new area every round) calls this before building the
     new one, so four areas' worth of signage never has to fit in the atlas
     at once.  Whatever is still on screen asks for its sign again and gets
     it repainted. */
  Textures.freeCells = [];
  Textures.dropSigns = function () {
    Object.keys(Textures.slots).forEach(function (key) {
      if (key.indexOf('decal:t~') !== 0) return;
      Textures.freeCells.push(Textures.slots[key].index);
      delete Textures.slots[key];
    });
  };

  Textures.decal = function (name) {
    if (!name) return null;
    var key = 'decal:' + name;
    if (Textures.slots[key]) return Textures.slots[key];
    if (name.charAt(0) === 't' && name.charAt(1) === '~') return drawSign(key, name);
    var fn = decalPainters[name];
    if (!fn) {
      if (/^plot_\d+$/.test(name)) {
        return Textures.drawText(name, 'PLOT ' + (parseInt(name.slice(5), 10) + 1),
                                 '#ffffff', '#1b2a35', 26);
      }
      return null;
    }
    var slot = allocate(key);
    var ctx = cellContext(slot, null);
    fn(ctx);
    ctx.restore();
    painted(slot);
    return slot;
  };

  Textures.faceSlot = function (itemId, data) {
    if (!itemId) return null;
    if (Textures.slots['face:' + itemId]) return Textures.slots['face:' + itemId];
    if (!data || !data.shapes) return null;
    return Textures.drawFace(itemId, data.shapes);
  };

  /* The decals worth painting up front: the ones the maps and the starter
     kit use.  The hundreds that came with the event crates are painted the
     first time something on screen asks for one (Textures.decal is lazy), so
     the atlas only ever holds what is actually being drawn. */
  var PREWARM = ['letter_R', 'skull', 'banner_red', 'banner_blue', 'burger', 'logo_block',
                 'tux', 'chevron', 'flowers', 'sigil', 'hazard', 'sign_red', 'sign_blue',
                 'sign_tycoon', 'canvas', 'felt', 'knit', 'planks', 'keyhole', 'rivets',
                 'leather', 'strands', 'fur'];
  Textures.prewarm = function () {
    ensureCanvas();
    PREWARM.forEach(function (name) { if (decalPainters[name]) Textures.decal(name); });
  };
  Textures.painters = function () { return Object.keys(decalPainters); };

  /* Name tags are their own little textures (one per player) rather than
     atlas cells, so long names stay sharp. */
  Textures.nameTag = function (gl, text, colour, sub) {
    var pad = 10;
    var canvas = document.createElement('canvas');
    var ctx = canvas.getContext('2d');
    ctx.font = 'bold 34px Verdana, sans-serif';
    var width = Math.ceil(ctx.measureText(text).width) + pad * 2;
    canvas.width = Math.max(64, width);
    canvas.height = sub ? 74 : 52;
    ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = 'rgba(10,16,24,0.55)';
    var r = 8;
    ctx.beginPath();
    ctx.moveTo(r, 0); ctx.lineTo(canvas.width - r, 0);
    ctx.quadraticCurveTo(canvas.width, 0, canvas.width, r);
    ctx.lineTo(canvas.width, canvas.height - r);
    ctx.quadraticCurveTo(canvas.width, canvas.height, canvas.width - r, canvas.height);
    ctx.lineTo(r, canvas.height); ctx.quadraticCurveTo(0, canvas.height, 0, canvas.height - r);
    ctx.lineTo(0, r); ctx.quadraticCurveTo(0, 0, r, 0);
    ctx.fill();
    ctx.font = 'bold 34px Verdana, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.lineWidth = 5;
    ctx.strokeStyle = 'rgba(0,0,0,0.85)';
    ctx.strokeText(text, canvas.width / 2, 26);
    ctx.fillStyle = colour || '#ffffff';
    ctx.fillText(text, canvas.width / 2, 26);
    if (sub) {
      ctx.font = 'bold 18px Verdana, sans-serif';
      ctx.fillStyle = '#e8f4ff';
      ctx.strokeText(sub, canvas.width / 2, 58);
      ctx.fillText(sub, canvas.width / 2, 58);
    }
    var texture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, canvas);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    return { texture: texture, width: canvas.width, height: canvas.height,
             aspect: canvas.width / canvas.height };
  };

  /* The cells painted after version `since`, newest paint of each cell
     first, or null when the log no longer reaches back that far (or so much
     changed that one upload of everything is the cheaper way). */
  function changedSince(since) {
    var log = Textures.changes;
    if (!log.length || log[0].v > since + 1) return null;
    var seen = {}, cells = [];
    for (var i = log.length - 1; i >= 0 && log[i].v > since; i--) {
      var key = log[i].x + ',' + log[i].y;
      if (seen[key]) continue;
      seen[key] = true;
      cells.push(log[i]);
    }
    return cells.length <= MAX_CELL_UPLOADS ? cells : null;
  }

  /* Upload the atlas to `existing` (or a new texture).  A renderer passes the
     version it last uploaded as `since`, and gets only the cells painted
     after it. */
  Textures.uploadAtlas = function (gl, existing, since) {
    ensureCanvas();
    var cells = (existing && since !== undefined) ? changedSince(since) : null;
    var texture = existing || gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    if (cells) {
      for (var i = 0; i < cells.length; i++) {
        gl.texSubImage2D(gl.TEXTURE_2D, 0, cells[i].x, cells[i].y, gl.RGBA,
                         gl.UNSIGNED_BYTE,
                         Textures.ctx.getImageData(cells[i].x, cells[i].y, CELL, CELL));
      }
    } else {
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE,
                    Textures.atlasCanvas);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    }
    gl.generateMipmap(gl.TEXTURE_2D);
    return texture;
  };

  Textures.CELL = CELL;
  Textures.GRID = GRID;
  global.Textures = Textures;
})(window);
