/* BLOCKHAVEN engine -- every texture in the project is drawn at runtime on a
   2D canvas, so the whole platform ships without a single image asset. */
(function (global) {
  'use strict';

  var CELL = 128;
  var GRID = 10;                // 10x10 cells -> 1280x1280 atlas
  var SIZE = CELL * GRID;

  var Textures = {
    atlasCanvas: null,
    slots: {},                  // name -> {u, v, s}
    nextSlot: 1,                // slot 0 is a plain white square
    version: 0
  };

  function ensureCanvas() {
    if (Textures.atlasCanvas) return Textures.atlasCanvas;
    var canvas = document.createElement('canvas');
    canvas.width = SIZE;
    canvas.height = SIZE;
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, SIZE, SIZE);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, CELL, CELL);
    Textures.atlasCanvas = canvas;
    Textures.ctx = ctx;
    return canvas;
  }

  function allocate(name) {
    if (Textures.slots[name]) return Textures.slots[name];
    var index = Textures.nextSlot++;
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
      }
      ctx.restore();
    });
    ctx.restore();
    Textures.version++;
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
    Textures.version++;
    return slot;
  };

  Textures.decal = function (name) {
    if (!name) return null;
    var key = 'decal:' + name;
    if (Textures.slots[key]) return Textures.slots[key];
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
    Textures.version++;
    return slot;
  };

  Textures.faceSlot = function (itemId, data) {
    if (!itemId) return null;
    if (Textures.slots['face:' + itemId]) return Textures.slots['face:' + itemId];
    if (!data || !data.shapes) return null;
    return Textures.drawFace(itemId, data.shapes);
  };

  Textures.prewarm = function () {
    ensureCanvas();
    Object.keys(decalPainters).forEach(function (name) { Textures.decal(name); });
  };

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

  Textures.uploadAtlas = function (gl, existing) {
    ensureCanvas();
    var texture = existing || gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE,
                  Textures.atlasCanvas);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.generateMipmap(gl.TEXTURE_2D);
    return texture;
  };

  Textures.CELL = CELL;
  Textures.GRID = GRID;
  global.Textures = Textures;
})(window);
