/* The event worlds' badge emblems (and any decal their maps paint).

   Loaded straight after textures.js on every page that draws badges -- the
   site's pages and the Game View -- because a badge can turn up anywhere
   (a profile, a toast, somebody's chest in another world).  Every emblem
   is a 128 x 128 sticker drawn with the same inked/stroked helpers as the
   originals in textures.js: keep the picture inside a circle of about 50
   round (64, 64), cream (CREAM) plus one or two strong colours.

   One section per world, in the order the worlds were added. */
(function (global) {
  'use strict';
  var T = global.Textures;
  if (!T || !T.registerEmblem) return;
  var I = T.ink;
  var inked = I.inked, stroked = I.stroked, poly = I.poly, circlePath = I.circlePath;
  var CREAM = I.CREAM, INK = I.INK;
  var emblem = T.registerEmblem, painter = T.registerPainter;

  // ------------------------------------------------------------ Rail Rivals
  var RR_GOLD = '#ffc83a', RR_RED = '#e0402e', RR_BLUE = '#4a9ae8', RR_IRON = '#8a8f96';

  emblem('em_rr_nugget', function (ctx) {
    // a gold nugget on a heap of ore
    inked(ctx, poly([[20, 104], [40, 82], [64, 90], [90, 78], [110, 104]]), '#7a5a3a', 6);
    inked(ctx, poly([[34, 70], [48, 40], [76, 30], [98, 48], [94, 78], [64, 92], [42, 86]]), RR_GOLD);
    inked(ctx, poly([[52, 50], [70, 42], [64, 60]]), '#fff1a8', 3);
    inked(ctx, poly([[78, 60], [88, 56], [86, 70]]), '#fff1a8', 3);
  });

  emblem('em_rr_cart', function (ctx) {
    // an ore cart on its rails, heaped with gold
    stroked(ctx, function (g) { g.moveTo(10, 104); g.lineTo(118, 104); }, RR_IRON, 5);
    inked(ctx, poly([[26, 52], [102, 52], [94, 88], [34, 88]]), RR_RED);
    inked(ctx, poly([[34, 52], [48, 32], [62, 42], [76, 26], [94, 52]]), RR_GOLD, 6);
    inked(ctx, circlePath(44, 94, 10), '#3a3a3a', 6);
    inked(ctx, circlePath(84, 94, 10), '#3a3a3a', 6);
    stroked(ctx, function (g) { g.moveTo(30, 66); g.lineTo(98, 66); }, '#ffd8c8', 3);
  });

  emblem('em_rr_lever', function (ctx) {
    // a brake lever thrown back, its handle red
    inked(ctx, function (g) { g.rect(36, 88, 56, 20); }, RR_IRON);
    stroked(ctx, function (g) { g.moveTo(64, 92); g.lineTo(34, 30); }, '#cfd4da', 9);
    inked(ctx, circlePath(32, 26, 12), RR_RED, 6);
    stroked(ctx, function (g) { g.arc(64, 92, 34, -2.6, -1.4); }, RR_GOLD, 4);
    inked(ctx, poly([[92, 58], [104, 60], [96, 70]]), RR_GOLD, 4);
  });

  emblem('em_rr_brake', function (ctx) {
    // a spanner across a brake shoe, freed
    inked(ctx, function (g) { g.arc(64, 64, 38, 0.2 * Math.PI, 1.8 * Math.PI); g.lineTo(64, 64);
      g.closePath(); }, RR_IRON);
    inked(ctx, circlePath(64, 64, 14), '#3a3a3a', 6);
    stroked(ctx, function (g) { g.moveTo(26, 104); g.lineTo(98, 32); }, CREAM, 10);
    inked(ctx, function (g) { g.arc(102, 28, 13, 0.75 * Math.PI, 2.6 * Math.PI); g.closePath(); }, CREAM, 6);
    inked(ctx, poly([[88, 86], [110, 86], [99, 106]]), '#5ad06a', 5);
  });

  emblem('em_rr_shovel', function (ctx) {
    // a coal shovel over a fire
    inked(ctx, poly([[26, 112], [44, 76], [64, 96], [84, 70], [102, 112]]), '#ff8a2a', 6);
    inked(ctx, poly([[40, 112], [54, 92], [66, 106], [80, 90], [90, 112]]), RR_GOLD, 4);
    stroked(ctx, function (g) { g.moveTo(92, 18); g.lineTo(52, 74); }, '#c89a6a', 8);
    inked(ctx, poly([[38, 64], [62, 70], [52, 96], [28, 90]]), RR_IRON, 6);
    inked(ctx, function (g) { g.rect(84, 12, 20, 8); }, '#c89a6a', 5);
  });

  emblem('em_rr_star', function (ctx) {
    // a lawman's star
    var pts = [];
    for (var i = 0; i < 12; i++) {
      var a = -Math.PI / 2 + i * Math.PI / 6;
      var r = i % 2 ? 22 : 46;
      pts.push([64 + Math.cos(a) * r, 64 + Math.sin(a) * r]);
    }
    inked(ctx, poly(pts), RR_GOLD);
    for (var k = 0; k < 6; k++) {
      var b = -Math.PI / 2 + k * Math.PI / 3;
      inked(ctx, circlePath(64 + Math.cos(b) * 46, 64 + Math.sin(b) * 46, 6), RR_GOLD, 4);
    }
    inked(ctx, circlePath(64, 64, 13), CREAM, 5);
  });

  emblem('em_rr_camera', function (ctx) {
    // an old box camera, flash going off
    inked(ctx, function (g) { g.rect(24, 50, 80, 54); }, '#5a4030');
    inked(ctx, circlePath(64, 78, 18), RR_IRON, 6);
    inked(ctx, circlePath(64, 78, 8), '#2a2a3a', 4);
    inked(ctx, function (g) { g.rect(32, 40, 22, 12); }, '#5a4030', 5);
    inked(ctx, poly([[84, 12], [92, 32], [112, 30], [96, 42], [104, 60], [86, 48], [72, 58],
                     [76, 38], [62, 28], [80, 30]]), '#fff6c0', 4);
  });

  emblem('em_rr_signal', function (ctx) {
    // a semaphore signal, arm raised to danger
    inked(ctx, function (g) { g.rect(58, 26, 12, 86); }, RR_IRON);
    inked(ctx, function (g) { g.rect(44, 104, 40, 10); }, RR_IRON, 5);
    inked(ctx, poly([[66, 36], [112, 26], [114, 40], [68, 50]]), RR_RED);
    stroked(ctx, function (g) { g.moveTo(90, 30); g.lineTo(92, 44); }, CREAM, 4);
    inked(ctx, circlePath(46, 44, 12), '#ff4a3a', 5);
    inked(ctx, circlePath(46, 72, 12), '#5ae06a', 5);
  });

  emblem('em_rr_drift', function (ctx) {
    // a snowdrift with a shovel stuck in it
    inked(ctx, function (g) { g.moveTo(10, 108); g.bezierCurveTo(30, 56, 70, 52, 82, 74);
      g.bezierCurveTo(94, 62, 118, 80, 118, 108); g.closePath(); }, '#eef6ff');
    stroked(ctx, function (g) { g.moveTo(60, 72); g.lineTo(86, 16); }, '#c89a6a', 7);
    inked(ctx, poly([[46, 70], [70, 80], [62, 100], [40, 92]]), RR_IRON, 6);
    [[28, 30], [100, 36], [46, 18]].forEach(function (f) {
      stroked(ctx, function (g) {
        for (var k = 0; k < 3; k++) {
          var a = k * Math.PI / 3;
          g.moveTo(f[0] - Math.cos(a) * 9, f[1] - Math.sin(a) * 9);
          g.lineTo(f[0] + Math.cos(a) * 9, f[1] + Math.sin(a) * 9);
        }
      }, '#bfe4ff', 3);
    });
  });

  emblem('em_rr_bridge', function (ctx) {
    // a lift bridge: two towers, the span raised between them
    inked(ctx, function (g) { g.rect(18, 22, 16, 90); }, '#b8503a');
    inked(ctx, function (g) { g.rect(94, 22, 16, 90); }, '#b8503a');
    inked(ctx, function (g) { g.rect(12, 14, 104, 12); }, '#b8503a', 6);
    inked(ctx, function (g) { g.rect(34, 40, 60, 14); }, RR_IRON);
    stroked(ctx, function (g) { g.moveTo(44, 26); g.lineTo(44, 40); g.moveTo(84, 26);
      g.lineTo(84, 40); }, CREAM, 3);
    inked(ctx, function (g) { g.moveTo(34, 112); g.bezierCurveTo(54, 96, 74, 120, 94, 104);
      g.lineTo(94, 116); g.lineTo(34, 116); g.closePath(); }, '#4a9ae8', 5);
  });

  emblem('em_rr_canary', function (ctx) {
    // the miner's canary on its perch, a lamp beside it
    stroked(ctx, function (g) { g.moveTo(22, 96); g.lineTo(84, 96); }, '#c89a6a', 6);
    inked(ctx, function (g) { g.ellipse(52, 70, 22, 17, -0.2, 0, Math.PI * 2); }, '#ffe14a');
    inked(ctx, circlePath(66, 50, 12), '#ffe14a');
    inked(ctx, poly([[76, 48], [88, 52], [76, 56]]), '#ff9a2a', 3);
    inked(ctx, poly([[30, 72], [16, 82], [32, 84]]), '#ffe14a', 5);
    inked(ctx, circlePath(68, 47, 2.5), '#2a2a2a', 2);
    inked(ctx, function (g) { g.rect(92, 52, 22, 32); }, '#ffb347', 6);
    inked(ctx, function (g) { g.rect(90, 44, 26, 8); }, RR_IRON, 5);
  });

  emblem('em_rr_map', function (ctx) {
    // a folded railroad map, four lines crossing it
    inked(ctx, poly([[14, 30], [44, 20], [84, 30], [114, 20], [114, 98], [84, 108], [44, 98],
                     [14, 108]]), '#f2e2b8');
    stroked(ctx, function (g) { g.moveTo(44, 20); g.lineTo(44, 98); g.moveTo(84, 30);
      g.lineTo(84, 108); }, '#c8b088', 3);
    stroked(ctx, function (g) { g.moveTo(22, 88); g.bezierCurveTo(50, 80, 60, 40, 104, 36); }, RR_RED, 5);
    stroked(ctx, function (g) { g.moveTo(22, 40); g.bezierCurveTo(50, 50, 70, 90, 104, 90); }, RR_BLUE, 5);
    inked(ctx, circlePath(63, 64, 7), RR_GOLD, 4);
  });

  // ------------------------------------------------------------- Prop Panic
  var PP_PINK = '#f06a8a', PP_GOLD = '#ffc83a', PP_BLUE = '#5aa0f0', PP_GREEN = '#6ac860';

  function ppEyes(ctx, x, y, gap, r) {
    // a pair of googly eyes: the thing is not what it seems
    [x - gap, x + gap].forEach(function (cx) {
      inked(ctx, circlePath(cx, y, r), '#ffffff', 4);
      inked(ctx, circlePath(cx + r * 0.25, y + r * 0.2, r * 0.45), INK, 2);
    });
  }

  emblem('em_pp_house', function (ctx) {
    // a cottage with a lit window
    inked(ctx, poly([[24, 60], [64, 24], [104, 60]]), '#c0563a');
    inked(ctx, poly([[32, 58], [96, 58], [96, 106], [32, 106]]), CREAM);
    inked(ctx, poly([[56, 78], [72, 78], [72, 106], [56, 106]]), '#7a4a2a', 5);
    inked(ctx, poly([[38, 66], [50, 66], [50, 78], [38, 78]]), PP_GOLD, 4);
    inked(ctx, poly([[78, 66], [90, 66], [90, 78], [78, 78]]), PP_GOLD, 4);
  });

  emblem('em_pp_still', function (ctx) {
    // a teapot keeping very still, eyes open
    inked(ctx, function (g) { g.ellipse(60, 74, 34, 26, 0, 0, Math.PI * 2); }, CREAM);
    inked(ctx, poly([[92, 70], [112, 52], [116, 58], [98, 80]]), CREAM, 6);
    stroked(ctx, function (g) { g.arc(28, 74, 12, Math.PI * 0.5, Math.PI * 1.5); }, CREAM, 6);
    inked(ctx, poly([[46, 46], [74, 46], [74, 52], [46, 52]]), PP_PINK, 5);
    inked(ctx, circlePath(60, 40, 6), PP_PINK, 4);
    ppEyes(ctx, 60, 72, 11, 8);
  });

  emblem('em_pp_eye', function (ctx) {
    // a watching eye under a magnifier's rim
    inked(ctx, function (g) {
      g.moveTo(16, 64); g.quadraticCurveTo(64, 20, 112, 64); g.quadraticCurveTo(64, 108, 16, 64);
    }, CREAM);
    inked(ctx, circlePath(64, 64, 20), PP_BLUE, 5);
    inked(ctx, circlePath(64, 64, 9), INK, 2);
    inked(ctx, circlePath(58, 58, 4), '#ffffff', 1);
  });

  emblem('em_pp_horn', function (ctx) {
    // a party horn blowing notes
    inked(ctx, poly([[20, 84], [72, 52], [80, 64], [24, 96]]), PP_GOLD);
    inked(ctx, poly([[72, 44], [92, 34], [96, 82], [80, 72]]), PP_PINK);
    stroked(ctx, function (g) { g.moveTo(100, 36); g.lineTo(108, 28); }, CREAM, 4);
    inked(ctx, circlePath(104, 54, 6), CREAM, 4);
    inked(ctx, circlePath(108, 76, 5), CREAM, 4);
  });

  emblem('em_pp_dare', function (ctx) {
    // a lamp sticking its tongue out at a looming shadow
    inked(ctx, poly([[40, 34], [88, 34], [98, 62], [30, 62]]), PP_GOLD);
    stroked(ctx, function (g) { g.moveTo(64, 62); g.lineTo(64, 104); }, '#a8a8a8', 6);
    inked(ctx, poly([[46, 104], [82, 104], [80, 112], [48, 112]]), '#7a7a7a', 4);
    ppEyes(ctx, 64, 46, 10, 6);
    inked(ctx, function (g) { g.ellipse(64, 58, 6, 8, 0, 0, Math.PI); }, PP_PINK, 3);
  });

  emblem('em_pp_duck', function (ctx) {
    // a rubber duck and its double
    [[44, 0.85, '#d8b020'], [70, 1, PP_GOLD]].forEach(function (d) {
      var x = d[0], k = d[1];
      inked(ctx, function (g) { g.ellipse(x, 84, 26 * k, 18 * k, 0, 0, Math.PI * 2); }, d[2]);
      inked(ctx, circlePath(x + 12 * k, 60, 14 * k), d[2]);
      inked(ctx, poly([[x + 24 * k, 60], [x + 38 * k, 64], [x + 24 * k, 68]]), '#f08a2a', 4);
      inked(ctx, circlePath(x + 15 * k, 56, 3), INK, 1);
    });
  });

  emblem('em_pp_last', function (ctx) {
    // the last one standing, under a spotlight
    inked(ctx, poly([[50, 14], [78, 14], [104, 110], [24, 110]]), 'rgba(255,240,180,0.55)', 3);
    inked(ctx, function (g) { g.ellipse(64, 104, 34, 8, 0, 0, Math.PI * 2); }, '#fff0b0', 4);
    inked(ctx, poly([[52, 64], [76, 64], [80, 102], [48, 102]]), PP_PINK);
    inked(ctx, circlePath(64, 54, 12), PP_PINK);
    ppEyes(ctx, 64, 78, 7, 5);
  });

  emblem('em_pp_broom', function (ctx) {
    // a broom sweeping up dust bunnies
    stroked(ctx, function (g) { g.moveTo(96, 16); g.lineTo(58, 76); }, '#a07a52', 7);
    inked(ctx, poly([[50, 70], [70, 82], [62, 112], [24, 98]]), PP_GOLD);
    stroked(ctx, function (g) { g.moveTo(40, 94); g.lineTo(56, 104); g.moveTo(48, 84); g.lineTo(62, 92); },
            '#c89a20', 3);
    inked(ctx, circlePath(96, 100, 9), '#c8c0b8', 4);
    inked(ctx, circlePath(108, 90, 6), '#c8c0b8', 4);
  });

  emblem('em_pp_mask', function (ctx) {
    // a masquerade mask
    inked(ctx, function (g) {
      g.moveTo(16, 56); g.quadraticCurveTo(40, 34, 64, 50); g.quadraticCurveTo(88, 34, 112, 56);
      g.quadraticCurveTo(108, 86, 82, 84); g.quadraticCurveTo(64, 78, 46, 84);
      g.quadraticCurveTo(20, 86, 16, 56);
    }, PP_PINK);
    inked(ctx, function (g) { g.ellipse(42, 62, 10, 7, 0, 0, Math.PI * 2); }, INK, 2);
    inked(ctx, function (g) { g.ellipse(86, 62, 10, 7, 0, 0, Math.PI * 2); }, INK, 2);
    inked(ctx, poly([[100, 44], [118, 20], [110, 48]]), PP_GOLD, 4);
  });

  emblem('em_pp_cat', function (ctx) {
    // Mittens, staring
    inked(ctx, poly([[30, 40], [40, 14], [56, 34]]), '#e88a3a');
    inked(ctx, poly([[72, 34], [88, 14], [98, 40]]), '#e88a3a');
    inked(ctx, circlePath(64, 66, 38), '#e88a3a');
    [[48, 62], [80, 62]].forEach(function (e) {
      inked(ctx, function (g) { g.ellipse(e[0], e[1], 9, 11, 0, 0, Math.PI * 2); }, '#c8ff6a', 4);
      inked(ctx, function (g) { g.ellipse(e[0], e[1], 2, 8, 0, 0, Math.PI * 2); }, INK, 1);
    });
    inked(ctx, poly([[58, 80], [70, 80], [64, 86]]), PP_PINK, 3);
  });

  emblem('em_pp_owl', function (ctx) {
    // an owl with a torch beam
    inked(ctx, poly([[64, 64], [118, 40], [118, 88]]), 'rgba(255,240,170,0.7)', 3);
    inked(ctx, function (g) { g.ellipse(48, 72, 30, 36, 0, 0, Math.PI * 2); }, '#8a6a4a');
    inked(ctx, poly([[24, 44], [32, 26], [42, 40]]), '#8a6a4a', 5);
    inked(ctx, poly([[54, 40], [64, 26], [72, 44]]), '#8a6a4a', 5);
    inked(ctx, circlePath(38, 62, 9), PP_GOLD, 4);
    inked(ctx, circlePath(60, 62, 9), PP_GOLD, 4);
    inked(ctx, poly([[46, 72], [52, 72], [49, 80]]), '#f08a2a', 3);
  });

  emblem('em_pp_tag', function (ctx) {
    // a price tag on its string
    inked(ctx, poly([[30, 50], [54, 26], [104, 26], [104, 102], [54, 102], [30, 78]]), PP_GOLD);
    inked(ctx, circlePath(48, 64, 6), CREAM, 4);
    stroked(ctx, function (g) { g.moveTo(66, 50); g.lineTo(92, 50); g.moveTo(66, 66); g.lineTo(88, 66); },
            '#c83a2a', 5);
    stroked(ctx, function (g) { g.moveTo(42, 64); g.quadraticCurveTo(24, 40, 14, 22); }, CREAM, 3);
  });

  emblem('em_pp_alarm', function (ctx) {
    // a ringing alarm bell
    inked(ctx, function (g) {
      g.moveTo(36, 88); g.quadraticCurveTo(36, 30, 64, 30); g.quadraticCurveTo(92, 30, 92, 88);
      g.lineTo(100, 96); g.lineTo(28, 96); g.closePath();
    }, '#e8402e');
    inked(ctx, circlePath(64, 102, 8), PP_GOLD, 4);
    stroked(ctx, function (g) { g.moveTo(18, 52); g.lineTo(10, 46); g.moveTo(110, 52); g.lineTo(118, 46); },
            PP_GOLD, 4);
    stroked(ctx, function (g) { g.moveTo(16, 70); g.lineTo(6, 70); g.moveTo(112, 70); g.lineTo(122, 70); },
            PP_GOLD, 4);
  });

  emblem('em_pp_map', function (ctx) {
    // four rooms on a floor plan, each with a tick
    inked(ctx, poly([[18, 22], [110, 22], [110, 106], [18, 106]]), CREAM);
    stroked(ctx, function (g) { g.moveTo(64, 22); g.lineTo(64, 106); g.moveTo(18, 64); g.lineTo(110, 64); },
            '#8a7a6a', 4);
    [[40, 44, PP_PINK], [88, 44, PP_GOLD], [40, 86, PP_BLUE], [88, 86, PP_GREEN]].forEach(function (c) {
      stroked(ctx, function (g) { g.moveTo(c[0] - 10, c[1]); g.lineTo(c[0] - 2, c[1] + 8); g.lineTo(c[0] + 12, c[1] - 8); },
              c[2], 5);
    });
  });

  // @@ event world emblems go above this line @@

  void inked; void stroked; void poly; void circlePath; void CREAM; void INK;
  void emblem; void painter;
})(typeof window !== 'undefined' ? window : globalThis);
