/* Sky Sprint's world-page pictures: the card, and each of the four
   courses, built from the same blocks the game draws with
   (Thumbs.registerWorld; loaded by thumbs.js the first time one is asked
   for).  Every racer wears the classic default -- yellow skin, red torso,
   blue legs -- with a cap in their team's colour, the Red Rockets' or the
   Blue Comets', and the bonk glove on one hand. */
(function (global) {
  'use strict';
  var Thumbs = global.Thumbs;
  if (!Thumbs || !Thumbs.registerWorld) return;

  var RED = '#e8463a', BLUE = '#3a8ae8', GOLD = '#ffd23a';

  // the same glove the game hands out (app/game/worlds/sky_sprint.py GLOVE)
  var H = Math.PI / 2, GR = '#e5352c', GB = '#2a6fd6';
  var GLOVE = { data: { parts: [
    { t: 'cyl', p: [0, 0, -0.4], s: [1.22, 0.56, 1.22], c: '#f4f1ea', r: [H, 0, 0] },
    { t: 'cyl', p: [0, 0, -0.27], s: [1.26, 0.1, 1.26], c: GB, r: [H, 0, 0] },
    { t: 'torus', p: [0, 0, -0.67], s: [1.18, 0.2, 1.18], c: GB, r: [H, 0, 0] },
    { t: 'cyl', p: [0, 0.02, -0.12], s: [1.04, 0.36, 1.1], c: GR, r: [H, 0, 0], m: 'glass' },
    { t: 'sph', p: [0, 0.06, 0.42], s: [1.48, 1.34, 1.48], c: GR, m: 'glass' },
    { t: 'sph', p: [0, 0.18, 0.9], s: [1.22, 0.9, 0.66], c: GR, m: 'glass' },
    { t: 'sph', p: [0.64, -0.16, 0.5], s: [0.44, 0.52, 0.96], c: '#b9241e', r: [0.2, 0, 0.25], m: 'glass' },
    { t: 'star', p: [0, 0.69, 0.38], s: [0.5, 0.48, 0.1], c: '#ffd23f', r: [-H + 0.3, 0, 0] }] } };

  /* a team cap, bill forward (the player's own space: +Z ahead, the top of
     the head at 5.9) */
  function cap(colour) {
    return [{ t: 'cyl', p: [0, 6.0, 0], s: [2.1, 0.5, 2.1], c: colour },
            { t: 'sph', p: [0, 6.25, 0], s: [1.9, 0.6, 1.9], c: colour },
            { t: 'box', p: [0, 5.8, 1.2], s: [1.7, 0.12, 0.9], c: colour },
            { t: 'cyl', p: [0, 6.56, 0], s: [0.3, 0.12, 0.3], c: '#ffffff' }];
  }
  function racer(k, x, z, yaw, team, o) {
    o = o || {};
    k.player(x, z, yaw, { y: o.y || 0, anim: o.anim || 'run', time: o.time === undefined ? 0.3 : o.time,
                          holding: o.empty ? null : GLOVE, wear: cap(team === 'blue' ? BLUE : RED),
                          face: o.face });
  }

  // ------------------------------------------------- course pieces
  /* a deck: top at y, studded, with a trim band round its edge */
  function deck(k, x, y, z, w, d, colour, trim, extra) {
    var o = { st: 1 };
    if (extra) { for (var key in extra) o[key] = extra[key]; }
    k.box([x, y - 0.6, z], [w, 1.2, d], colour, o);
    if (trim) k.box([x, y - 1.5, z], [w + 0.3, 0.6, d + 0.3], trim);
  }
  /* a jump pad: a ring set in a deck at y */
  function pad(k, x, y, z) {
    k.shape('cyl', [x, y + 0.15, z], [5.2, 0.3, 5.2], '#5a5e66', { m: 'metal' });
    k.shape('cyl', [x, y + 0.34, z], [3.1, 0.06, 3.1], '#ffffff', { m: 'neon', a: 0.8 });
  }
  /* a checkpoint arch across the line at y, facing +z */
  function arch(k, x, y, z, span, colour, label, glow, bare) {
    [-1, 1].forEach(function (s) {
      k.shape('cyl', [x + s * span, y + 5, z], [1.2, 10, 1.2], colour);
      k.shape('sph', [x + s * span, y + 10.4, z], [1.6, 1.6, 1.6], glow || '#ffffff', { m: 'neon' });
    });
    k.box([x, y + 9.4, z], [span * 2, 1.2, 0.8], colour);
    k.box([x, y + 11.1, z], [span * 1.4, 2.2, 0.3], colour,
          { dec: 't~' + label + '~' + colour + '~#ffffff~' + (span * 1.4 / 2.2).toFixed(2) });
    if (!bare) k.shape('cyl', [x, y + 0.05, z], [span * 1.8, 0.08, span * 1.8], glow || '#ffffff', { m: 'neon', a: 0.4 });
  }
  /* a sweeper: hub on a round deck, its arms at hub height (angle a) */
  function sweeper(k, x, y, z, r, arms, a, look) {
    k.shape('cyl', [x, y + 2.4, z], [2.6, 4.8, 2.6], look === 'bamboo' ? '#8a3a2a' : '#5a5e66', { m: 'metal' });
    for (var n = 0; n < arms; n++) {
      var ang = a + n * Math.PI * 2 / arms, ux = Math.cos(ang), uz = Math.sin(ang);
      var yaw = Math.atan2(ux, uz);
      var segs = look === 'lolly' ? 8 : (look === 'bamboo' ? 5 : 7), len = r / segs;
      for (var s = 0; s < segs; s++) {
        var m = len * (s + 0.5);
        var colour = look === 'lolly' ? (s % 2 ? '#ffffff' : '#e8306a')
          : (look === 'bamboo' ? (s % 2 ? '#7ab84a' : '#8ac85a') : (s % 2 ? '#1e1e22' : '#e8b830'));
        if (look === 'neon') {
          k.box([x + ux * r / 2, y + 2.2, z + uz * r / 2], [0.9, 0.9, r], ['#3ad8ff', '#ff3ad8'][n % 2], { m: 'neon', r: [0, yaw, 0] });
          break;
        }
        if (look === 'lolly' || look === 'bamboo') {
          k.shape('cyl', [x + ux * m, y + 2.2, z + uz * m], [1.4, len - (look === 'bamboo' ? 0.2 : 0), 1.4], colour,
                  { r: [Math.PI / 2, yaw, 0] });
        } else {
          k.box([x + ux * m, y + 2.2, z + uz * m], [1.4, 1.4, len], colour, { r: [0, yaw, 0], m: s % 2 ? 'metal' : '' });
        }
      }
      if (look === 'lolly') {
        var tx = Math.atan2(-uz, ux);
        k.shape('cyl', [x + ux * (r - 0.9), y + 2.6, z + uz * (r - 0.9)], [3.4, 0.5, 3.4], '#ff5aa0', { r: [Math.PI / 2, tx, 0] });
        k.shape('cyl', [x + ux * (r - 0.9), y + 2.6, z + uz * (r - 0.9)], [2.2, 0.56, 2.2], '#fff0f6', { r: [Math.PI / 2, tx, 0] });
      } else if (look === 'bamboo') {
        k.shape('sph', [x + ux * (r - 0.6), y + 0.1, z + uz * (r - 0.6)], [1.5, 1.9, 1.5], '#ff5a3a', { m: 'neon', a: 0.92 });
        k.box([x + ux * (r - 0.6), y + 1.6, z + uz * (r - 0.6)], [0.08, 1.2, 0.08], '#2a1a10');
      }
    }
  }
  /* puffs of cloud, a sea of them at y */
  function cloudSea(k, y, colours, seed, span) {
    span = span || 160;
    for (var i = 0; i < 46; i++) {
      var a = Math.sin(i * 12.9898 + seed) * 43758.5453, f = a - Math.floor(a);
      var b = Math.sin(i * 78.233 + seed) * 12345.678, g = b - Math.floor(b);
      var x = (f - 0.5) * span * 1.6, z = (g - 0.5) * span - 20;
      var s = 14 + (i % 5) * 4;
      k.shape('sph', [x, y + (i % 3) * 0.8, z], [s, s * 0.32, s * 0.8], colours[i % colours.length]);
    }
  }
  function floatingCloud(k, x, y, z, s, colour) {
    k.shape('sph', [x, y, z], [s, s * 0.45, s * 0.6], colour);
    k.shape('sph', [x - s * 0.35, y - s * 0.06, z + 0.4], [s * 0.6, s * 0.36, s * 0.5], colour);
    k.shape('sph', [x + s * 0.38, y - s * 0.04, z - 0.3], [s * 0.55, s * 0.34, s * 0.46], colour);
  }

  // ------------------------------------------------------------ card
  /* High over the clouds: the start lanes, a jump pad flinging one racer
     up, a Rocket bonking a Comet off the edge, a sweeper's arm being
     hopped, and the stepping stones climbing away to a gold finish. */
  Thumbs.registerWorld('sky_sprint', {
    sky: { top: '#3a8ae0', horizon: '#e0f2ff', sun: [0.4, 0.7, 0.3], clouds: 0.55, tint: '#ffffff' },
    camera: [[44, 30, 52], [-6, 11, -16], 46],
    build: function (parts, k) {
      cloudSea(k, -16, ['#ffffff', '#f2f6ff', '#eaf2ff'], 3, 200);
      // the start deck, its two lanes, the arch the gates hang from
      deck(k, 16, 0, 14, 24, 14, '#e8e8f0', '#b8c0d0');
      k.box([10, 0.04, 14], [11, 0.08, 13], RED, { m: 'neon', a: 0.35 });
      k.box([22, 0.04, 14], [11, 0.08, 13], BLUE, { m: 'neon', a: 0.35 });
      arch(k, 16, 0, 7.6, 11, '#3a5ae8', 'SKY SPRINT', '#ffe83a', true);
      racer(k, 11, 12, -2.6, 'red', { anim: 'run', time: 0.7 });
      racer(k, 21, 15, -2.4, 'blue', { anim: 'run', time: 0.2 });
      // the pad deck: one racer flung up, a Rocket bonking a Comet off its edge
      deck(k, -6, 4, 2, 16, 12, '#7ad85a', '#4a9a3a');
      pad(k, -9, 4, 2);
      racer(k, -9, 2, 2.4, 'red', { y: 15, anim: 'jump', time: 0.4 });
      racer(k, -1, 5, 0.9, 'red', { y: 4, anim: 'idle', time: 0.15, face: 'face_angry' });
      racer(k, 3.6, 8.6, 0.6, 'blue', { y: 5.4, anim: 'jump', time: 0.8, empty: true });
      k.shape('sparkle', [1.5, 8.2, 7.4], [1.6, 1.6, 1.6], '#ffffff', { m: 'neon' });
      // the sweeper's round deck, an arm coming round, a Comet hopping it
      k.shape('cyl', [-2, 9.4, -22], [22, 1.2, 22], '#ffb84a', { st: 1 });
      k.shape('cyl', [-2, 8.5, -22], [22.4, 0.6, 22.4], '#c8802a');
      sweeper(k, -2, 10, -22, 10, 2, 0.4, '');
      racer(k, 3.6, -17.6, -2.4, 'blue', { y: 14.4, anim: 'jump', time: 0.5 });
      // the stepping stones climbing away to the finish
      [[-24, 13, -16, '#ff5a8a'], [-30, 17, -32, '#5ad8ff'], [-20, 21, -46, '#c88aff']].forEach(function (st) {
        deck(k, st[0], st[1], st[2], 8, 8, st[3], '#ffffff');
      });
      racer(k, -30, -32, 2.2, 'red', { y: 17, anim: 'run', time: 0.4 });
      deck(k, 0, 25, -54, 22, 14, '#ffffff', GOLD);
      for (var f = 0; f < 10; f++) k.box([-9 + f * 2, 25.06, -58], [2, 0.1, 2], f % 2 ? '#1a1a1a' : '#ffffff');
      arch(k, 0, 25, -50, 9, GOLD, 'FINISH', '#ffffff', true);
      racer(k, 2, -55, 0.4, 'blue', { y: 25, anim: 'jump', time: 0.25 });
      floatingCloud(k, 40, 14, -24, 16, '#ffffff');
      floatingCloud(k, -50, 22, -40, 20, '#f6f8ff');
      floatingCloud(k, 30, 30, -70, 18, '#ffffff');
    }
  });

  // ------------------------------------------------- The Foundry
  /* Over the pour: a girder run with a hammer coming down across it, a
     belt carrying a Comet, a Rocket leaping the gap, and behind them the
     furnace mouth and the ladle tipping out its steel. */
  Thumbs.registerWorld('ss_foundry', {
    sky: { top: '#1a0c08', horizon: '#c8602a', sun: [0.5, 0.3, -0.5], clouds: 0.6, tint: '#ffb070' },
    camera: [[40, 24, 46], [0, 6, -10], 48],
    build: function (parts, k) {
      // the lava lake, its crust, the odd bubble
      k.box([0, -8, -20], [240, 2, 200], '#ff6a1a', { m: 'neon' });
      [[-20, 14, 9], [16, 22, 7], [34, -16, 11], [-36, -24, 8], [6, -40, 10], [-8, 30, 6]].forEach(function (c) {
        k.shape('cyl', [c[0], -6.85, c[1]], [c[2], 0.3, c[2] * 0.8], '#b8501a');
        k.shape('cyl', [c[0] + 0.6, -6.6, c[1] - 0.4], [c[2] * 0.6, 0.3, c[2] * 0.45], '#8a3a14');
      });
      [[-6, 18], [24, -4], [-30, 0]].forEach(function (bb) {
        k.shape('sph', [bb[0], -7, bb[1]], [2.4, 1.6, 2.4], '#ffd060', { m: 'neon' });
      });
      // the girders, on their lattice towers
      deck(k, -12, 4, 8, 36, 5, '#5a5e66', '#c8a030', { m: 'metal' });
      k.box([-12, 1.6, 8], [36, 2.4, 1.0], '#4a4e56');
      deck(k, 20, 6, 8, 16, 5, '#5a5e66', '#c8a030', { m: 'metal' });
      k.box([20, 3.6, 8], [16, 2.4, 1.0], '#4a4e56');
      [[-26, 8, 1.8], [2, 8, 1.8], [24, 8, 3.8]].forEach(function (t) {
        k.box([t[0], (t[2] - 7) / 2 - 0.6, t[1]], [2.2, t[2] + 5.8, 2.2], '#3a3e44', { m: 'metal' });
      });
      // the gantry and its hammer, swinging down across the girder
      k.box([-14, 21, 8], [2, 2, 16], '#3a3e44', { m: 'metal' });
      k.box([-14, 9, 15], [1.6, 22, 1.6], '#3a3e44', { m: 'metal' });
      k.box([-14, 9, 1], [1.6, 22, 1.6], '#3a3e44', { m: 'metal' });
      var th = 0.55;
      k.box([-14 + Math.sin(th) * 6.4, 20 - Math.cos(th) * 6.4, 8], [0.7, 12.8, 0.7], '#5a5e66', { m: 'metal', r: [0, 0, th] });
      [-1, 0, 1].forEach(function (n) {
        var off = n * 1.34;
        k.box([-14 + Math.sin(th) * 12.8 - Math.sin(th) * off, 20 - Math.cos(th) * 12.8 + Math.cos(th) * off, 8],
              [4, 1.34, 4], n === 0 ? '#1e1e22' : '#e8b830', { r: [0, 0, th] });
      });
      // the belt, a Comet riding it
      deck(k, -4, 9, -12, 34, 10, '#2a2a2e', '#5a5e66');
      for (var s = 0; s < 11; s++) k.box([-19.5 + s * 3, 9.08, -12], [0.5, 0.06, 8.8], '#e8b830');
      k.shape('cyl', [-20, 7.0, -12], [1.6, 9.6, 1.6], '#8a8e96', { m: 'metal', r: [Math.PI / 2, 0, 0] });
      k.shape('cyl', [12, 7.0, -12], [1.6, 9.6, 1.6], '#8a8e96', { m: 'metal', r: [Math.PI / 2, 0, 0] });
      racer(k, -8, -12, Math.PI / 2, 'blue', { y: 9, anim: 'idle', time: 0.2 });
      // a Rocket leaping the gap between the girders, two more on the run
      racer(k, 10, 8, Math.PI / 2, 'red', { y: 8.8, anim: 'jump', time: 0.5 });
      racer(k, -26, 8, Math.PI / 2, 'red', { y: 4, anim: 'run', time: 0.7 });
      racer(k, 24, 8, -Math.PI / 2, 'blue', { y: 6, anim: 'run', time: 0.2 });
      // the works behind: the furnace mouth, the ladle pouring, the stacks
      k.box([0, 8, -50], [110, 32, 16], '#3a2018', { dec: 'bricks' });
      k.box([-20, 2, -41.9], [16, 12, 0.2], '#ffb040', { m: 'neon' });
      k.box([-20, 8.6, -41.7], [18, 1.2, 0.6], '#2a1a14');
      for (var w = 0; w < 6; w++) k.box([6 + w * 7, 14, -41.9], [3.6, 5, 0.2], '#ffa040', { m: 'neon' });
      [-44, -26, 30, 48].forEach(function (x, i) {
        k.shape('cyl', [x, 34, -54], [5, 20, 5], '#3a2a24');
        k.shape('cyl', [x, 40 - i, -54], [5.4, 1.2, 5.4], '#c8a030');
        k.shape('sph', [x + 2, 47 + i, -56], [8, 5, 8], '#5a4a46', { a: 0.85 });
      });
      // the tapping spout out of the furnace wall, the steel pouring from it
      k.box([16, 18.6, -38.6], [6, 2.4, 8], '#5a4a40', { m: 'metal' });
      k.box([16, 19.5, -37.8], [4.4, 0.6, 7.6], '#ffb040', { m: 'neon' });
      k.box([16, 6.6, -34.2], [2.2, 23.2, 1.6], '#ffd060', { m: 'neon' });
      k.shape('sph', [16, -6.6, -34.2], [8, 2.4, 8], '#ffe080', { m: 'neon' });
    }
  });

  // ------------------------------------------------- Candy Clouds
  /* The jelly a Rocket is bouncing off, a lollipop sweeper, gumdrops on a
     wafer deck, the cake with its candle at the top. */
  Thumbs.registerWorld('ss_candy', {
    sky: { top: '#ff9ad0', horizon: '#fff0d8', sun: [0.3, 0.7, 0.5], clouds: 0.5, tint: '#fff0f6' },
    camera: [[38, 20, 42], [-2, 9, -8], 48],
    build: function (parts, k) {
      cloudSea(k, -12, ['#ffd8f0', '#ffffff', '#d8ecff'], 9, 170);
      // wafer decks
      deck(k, 0, 0, 6, 34, 12, '#e8c08a', '#c8986a', { dec: 'planks' });
      deck(k, -26, 6, -12, 16, 16, '#ffd8e8', '#ff8ab8');
      // the jelly, a Rocket bouncing high off it
      k.box([-6, 1, 6], [8, 2, 8], '#e83a5a', { m: 'glass', a: 0.82 });
      racer(k, -6, 6, -1.0, 'red', { y: 5.2, anim: 'jump', time: 0.35 });
      k.shape('torus', [-6, 2.3, 6], [9.6, 2.0, 9.6], '#ffffff', { m: 'neon', a: 0.5 });
      // gumdrops and candy canes along the deck
      [[8, 2, '#7ad8ff'], [12, 9, '#b8ff7a'], [15, 3, '#ffd84a']].forEach(function (g) {
        k.shape('sph', [g[0], 0.9, g[1]], [2.6, 2.6, 2.6], g[2]);
      });
      [[-15, 1], [15, 11]].forEach(function (c) {
        for (var s = 0; s < 6; s++) k.shape('cyl', [c[0], 0.5 + s, c[1]], [0.8, 1.0, 0.8], s % 2 ? '#ffffff' : '#e8306a');
      });
      racer(k, 6, 9, -2.6, 'blue', { anim: 'run', time: 0.5 });
      // the lollipop sweeper on its round deck
      k.shape('cyl', [10, 9.4, -22], [24, 1.2, 24], '#ff8ac8', { st: 1 });
      k.shape('cyl', [10, 8.5, -22], [24.4, 0.6, 24.4], '#ffffff');
      sweeper(k, 10, 10, -22, 11, 2, 2.3, 'lolly');
      racer(k, 13, -14, -2.8, 'blue', { y: 14.4, anim: 'jump', time: 0.6 });
      racer(k, 4, -26, 2.2, 'red', { y: 10, anim: 'run', time: 0.2 });
      // the cake, tier on tier, the candle the finish
      k.shape('cyl', [-24, 14, -46], [26, 8, 26], '#ffe8f0');
      k.shape('cyl', [-24, 18.2, -46], [26.6, 0.8, 26.6], '#ff8ab8');
      k.shape('cyl', [-24, 22, -46], [16, 8, 16], '#fff6d8');
      k.shape('cyl', [-24, 26.2, -46], [16.6, 0.8, 16.6], '#8ad8ff');
      for (var b = 0; b < 8; b++) {
        var a = b * Math.PI / 4;
        k.shape('sph', [-24 + Math.cos(a) * 12.6, 18.9, -46 + Math.sin(a) * 12.6], [1.8, 1.8, 1.8], '#e8304a');
      }
      k.shape('cyl', [-24, 29.5, -46], [1.2, 6, 1.2], '#7ad8ff');
      k.shape('cone', [-24, 33.4, -46], [1.0, 1.8, 1.0], '#ffb83a', { m: 'neon' });
      floatingCloud(k, 32, 16, -32, 14, '#ffe0f4');
      floatingCloud(k, -46, 10, -20, 12, '#ffffff');
    }
  });

  // ------------------------------------------------- Neon Grid
  /* Grid tiles at night under the striped sun: one blinked out (its ghost
     still there), a laser across the corridor being jumped, a speed strip
     and the city glowing on the skyline. */
  Thumbs.registerWorld('ss_neon', {
    sky: { top: '#0a0420', horizon: '#ff3a8a', sun: [0.0, 0.25, -0.9], clouds: 0.15, tint: '#d8a8ff' },
    camera: [[28, 17, 32], [-3, 3, -12], 50],
    build: function (parts, k) {
      k.box([0, -40, -40], [400, 1, 360], '#0a0418', { dec: 'neongrid', dw: 1 });
      // the city on the skyline and the sun going down behind it
      k.shape('cyl', [-30, 10, -320], [180, 1, 180], '#ff6a3a', { m: 'neon', r: [Math.PI / 2, 0, 0], dec: 'sunset_grid', dw: 1 });
      [[-170, 40, 20], [-140, 58, 16], [-112, 34, 22], [-84, 70, 18], [-56, 46, 20], [-28, 30, 18], [20, 52, 18],
       [48, 76, 16], [76, 40, 22], [104, 62, 18], [132, 44, 20]].forEach(function (b, i) {
        k.box([b[0], b[1] / 2 - 40, -240], [b[2], b[1], b[2]], '#12061e');
        k.box([b[0], b[1] - 40 + 0.3, -240], [b[2] + 0.4, 0.6, b[2] + 0.4], ['#3ad8ff', '#ff3ad8', '#ffe83a'][i % 3], { m: 'neon' });
        k.box([b[0], b[1] * 0.6 - 40, -230.9], [b[2] * 0.6, 0.5, 0.2], ['#ff3ad8', '#3ad8ff', '#ffe83a'][i % 3], { m: 'neon' });
      });
      // the beat tiles: one gone, its ghost left behind
      [[-10, 12, 1], [0, 12, 1], [10, 12, 0], [-10, 2, 1], [0, 2, 1], [10, 2, 1]].forEach(function (t, i) {
        if (!t[2]) {
          [[0, 4, 8, 0.3], [0, -4, 8, 0.3], [4, 0, 0.3, 8], [-4, 0, 0.3, 8]].forEach(function (e) {
            k.box([t[0] + e[0], -0.3, t[1] + e[1]], [e[2], 0.3, e[3]], '#9ad8ff', { m: 'neon', a: 0.45 });
          });
          return;
        }
        var hue = i % 2 ? '#3ad8ff' : '#ff3ad8';
        k.box([t[0], -0.6, t[1]], [8, 1.2, 8], '#140a28');
        k.box([t[0], -1.45, t[1]], [6.8, 0.5, 6.8], hue, { m: 'neon' });
        k.box([t[0], 0.03, t[1]], [6.4, 0.06, 6.4], hue, { m: 'neon', a: 0.3 });
      });
      racer(k, 0, 12, -2.8, 'red', { anim: 'run', time: 0.3 });
      racer(k, 9, 4, -2.6, 'blue', { y: 5, anim: 'jump', time: 0.5 });
      // the laser corridor: its emitters and the beam, a Rocket jumping it
      deck(k, 0, 0, -18, 14, 20, '#1a1430', '#3ad8ff');
      k.box([-6.6, 1.1, -16], [0.8, 1.6, 1.2], '#2a2440', { m: 'metal' });
      k.box([6.6, 1.1, -16], [0.8, 1.6, 1.2], '#2a2440', { m: 'metal' });
      k.box([0, 1.1, -16], [12.4, 0.22, 0.22], '#ff2a4a', { m: 'neon' });
      k.box([0, 1.1, -16], [12.4, 0.7, 0.7], '#ff4a6a', { m: 'neon', a: 0.25 });
      k.box([-6.6, 1.1, -23], [0.8, 1.6, 1.2], '#2a2440', { m: 'metal' });
      k.box([6.6, 1.1, -23], [0.8, 1.6, 1.2], '#2a2440', { m: 'metal' });
      k.box([0, 1.1, -23], [12.4, 0.22, 0.22], '#ff2a4a', { m: 'neon' });
      k.box([0, 1.1, -23], [12.4, 0.7, 0.7], '#ff4a6a', { m: 'neon', a: 0.25 });
      racer(k, -1, -14.6, Math.PI, 'red', { y: 3.4, anim: 'jump', time: 0.55 });
      racer(k, 2.6, -25, Math.PI, 'blue', { anim: 'run', time: 0.8 });
      // the highway on, its speed strip, a billboard
      deck(k, -20, 4, -30, 22, 8, '#1a1430', '#ff3ad8');
      for (var c = 0; c < 3; c++) k.box([-14 - c * 3.2, 4.12, -30], [0.6, 0.06, 4], '#ffffff', { m: 'neon' });
      k.box([-26, 14, -34.6], [14, 7, 0.6], '#140a28');
      k.box([-26, 14, -34.2], [12.6, 5.6, 0.2], '#3ad8ff', { dec: 't~SKY SPRINT~#140a28~#3ad8ff~2.25', m: 'neon' });
      k.box([-26, 7, -34.6], [0.8, 8, 0.8], '#2a2440', { m: 'metal' });
    }
  });

  // ------------------------------------------------- Jade Temple
  /* The rope bridge across the clouds in the wind, the bamboo sweeper by
     the shrine, the pagoda and its bell at the top. */
  Thumbs.registerWorld('ss_jade', {
    sky: { top: '#e8b860', horizon: '#ffe8c8', sun: [0.6, 0.35, -0.5], clouds: 0.55, tint: '#ffe0b0' },
    camera: [[38, 20, 40], [-2, 10, -10], 48],
    build: function (parts, k) {
      cloudSea(k, -14, ['#ffffff', '#fff4e8', '#f0f6f2'], 21, 180);
      // the mountains standing out of the clouds
      [[-60, -60, 30, 50], [50, -80, 26, 44], [-20, -100, 34, 60], [70, -30, 22, 36]].forEach(function (m) {
        k.shape('cone', [m[0], m[3] / 2 - 14, m[1]], [m[2], m[3], m[2]], '#5a8a7a');
        k.shape('cone', [m[0], m[3] - 18, m[1]], [m[2] * 0.3, m[3] * 0.25, m[2] * 0.3], '#f4f4f0');
      });
      // the shrine island and its bamboo sweeper
      k.shape('cone', [-14, -6, 4], [26, 14, 26], '#4a6a5a', { r: [Math.PI, 0, 0] });
      k.shape('cyl', [-14, 0.6, 4], [24, 1.2, 24], '#c8b890', { st: 1 });
      sweeper(k, -14, 1.2, 4, 10.5, 3, 0.9, 'bamboo');
      racer(k, -18.5, 10, -2.2, 'blue', { y: 5.0, anim: 'jump', time: 0.5 });
      racer(k, -10, -2, 1.0, 'red', { y: 1.2, anim: 'run', time: 0.3 });
      // the rope bridge to the tea house, a Rocket crossing
      for (var p = 0; p < 16; p++) k.box([2 + p * 2, 0.9, 4], [1.6, 0.25, 6], '#8a6a3a');
      [[1, 1], [33, 1]].forEach(function (end) {
        [-3.4, 3.4].forEach(function (dz) { k.shape('cyl', [end[0], 2.4, 4 + dz], [0.6, 4, 0.6], '#5a3a22'); });
      });
      [-3.4, 3.4].forEach(function (dz) { k.box([17, 3.8, 4 + dz], [32, 0.2, 0.2], '#c8a060'); });
      racer(k, 18, 4, Math.PI / 2, 'red', { y: 1.0, anim: 'run', time: 0.5 });
      deck(k, 40, 1, 4, 12, 12, '#c8b890', '#8a3a2a');
      // the pagoda, tier on tier, the bell at the top
      var px = 6, pz = -34;
      k.shape('cone', [px, -4, pz], [28, 20, 28], '#4a6a5a', { r: [Math.PI, 0, 0] });
      for (var t = 0; t < 4; t++) {
        var w = 16 - t * 3, y = 8 + t * 6;
        k.box([px, y - 2.5, pz], [w - 3, 5, w - 3], '#b8202a');
        k.shape('wedge', [px, y + 0.9, pz + w / 4], [w + 3, 1.8, w / 2 + 1.5], '#1e3a34');
        k.shape('wedge', [px, y + 0.9, pz - w / 4], [w + 3, 1.8, w / 2 + 1.5], '#1e3a34', { r: [0, Math.PI, 0] });
        k.box([px, y - 0.2, pz], [w - 2.6, 0.4, w - 2.6], '#e8b830');
      }
      k.shape('bell', [px, 31.4, pz], [3, 3, 3], '#e8b830', { m: 'metal' });
      k.box([px, 34, pz], [0.6, 2.4, 0.6], '#e8b830', { m: 'metal' });
      // lanterns hanging off the bridge posts
      [[1, 0.6], [33, 0.6]].forEach(function (l) {
        k.shape('sph', [l[0], 5.15, l[1]], [1.2, 1.5, 1.2], '#ff5a3a', { m: 'neon', a: 0.92 });
      });
      floatingCloud(k, 30, 18, -50, 16, '#ffffff');
      floatingCloud(k, -44, 12, -24, 12, '#fff6ee');
    }
  });
})(window);
