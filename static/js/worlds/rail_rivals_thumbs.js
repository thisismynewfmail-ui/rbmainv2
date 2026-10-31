/* Rail Rivals' world-page pictures: the card and a diorama of each of the
   four railroads, built from the same blocks the game draws with
   (Thumbs.registerWorld; loaded by thumbs.js the first time one is asked
   for).  Every player wears the classic default -- yellow skin, red torso,
   blue legs -- and the two companies are told apart by their caps. */
(function (global) {
  'use strict';
  var Thumbs = global.Thumbs;
  if (!Thumbs || !Thumbs.registerWorld) return;

  var RED = '#c4281c', BLUE = '#2f6aa8', GOLD = '#e8b23a';

  /* An engineer's cap in a company's colour, in the player's own space. */
  function cap(colour) {
    return [{ t: 'box', p: [0, 6.15, -0.1], s: [2.3, 0.7, 2.3], c: colour },
            { t: 'box', p: [0, 5.95, 1.1], s: [2.2, 0.18, 1.1], c: '#2a2a2a' },
            { t: 'box', p: [0, 6.55, -0.1], s: [1.6, 0.18, 1.6], c: '#ffffff' }];
  }

  function straight(k, x0, x1, z, ballast) {
    k.box([(x0 + x1) / 2, 0.15, z], [x1 - x0, 0.3, 5.6], ballast || '#7a6f62');
    for (var x = x0 + 1.6; x < x1; x += 3.2) k.box([x, 0.36, z], [0.9, 0.14, 4.8], '#5e4630');
    k.box([(x0 + x1) / 2, 0.52, z - 1.6], [x1 - x0, 0.18, 0.36], '#8c8a86', { m: 'metal' });
    k.box([(x0 + x1) / 2, 0.52, z + 1.6], [x1 - x0, 0.18, 0.36], '#8c8a86', { m: 'metal' });
  }

  /* A diagonal run of track from (x0, z0) to (x1, z1). */
  function slant(k, x0, z0, x1, z1) {
    var len = Math.hypot(x1 - x0, z1 - z0), yaw = Math.atan2(x1 - x0, z1 - z0);
    var mx = (x0 + x1) / 2, mz = (z0 + z1) / 2;
    k.box([mx, 0.16, mz], [5.6, 0.3, len], '#7a6f62', { r: [0, yaw, 0] });
    var n = Math.floor(len / 3.2);
    for (var i = 0; i < n; i++) {
      var f = (i + 0.5) / n;
      k.box([x0 + (x1 - x0) * f, 0.37, z0 + (z1 - z0) * f], [4.8, 0.14, 0.9], '#5e4630', { r: [0, yaw, 0] });
    }
    var rx = Math.cos(yaw) * 1.6, rz = -Math.sin(yaw) * 1.6;
    k.box([mx + rx, 0.53, mz + rz], [0.36, 0.18, len], '#8c8a86', { r: [0, yaw, 0], m: 'metal' });
    k.box([mx - rx, 0.53, mz - rz], [0.36, 0.18, len], '#8c8a86', { r: [0, yaw, 0], m: 'metal' });
  }

  /* The race's ore cart: a dinky engine leading the way (+z, the way it
     runs) with its ore bucket behind like a tender. */
  function cart(k, x, z, yaw, colour) {
    k.attach(x, 0.44, z, yaw, [
      { t: 'box', p: [0, 1.5, 0], s: [4.2, 0.6, 7.8], c: '#3a3632', m: 'metal' },
      { t: 'cyl', p: [0, 3.0, 2.0], s: [2.6, 3.4, 2.6], c: '#2e2c2a', r: [Math.PI / 2, 0, 0], m: 'metal' },
      { t: 'cyl', p: [0, 3.0, 3.73], s: [2.1, 0.06, 2.1], c: '#1a1816', r: [Math.PI / 2, 0, 0], m: 'metal' },
      { t: 'cyl', p: [0, 4.35, 1.0], s: [1.1, 0.7, 1.1], c: GOLD, m: 'metal' },
      { t: 'cyl', p: [0, 5.3, 2.6], s: [0.9, 2.2, 0.9], c: '#1e1c1a', m: 'metal' },
      { t: 'cyl', p: [0, 6.5, 2.6], s: [1.4, 0.4, 1.4], c: GOLD, m: 'metal' },
      { t: 'box', p: [0, 4.55, 3.45], s: [0.9, 0.8, 0.5], c: '#3a3632', m: 'metal' },
      { t: 'box', p: [0, 4.55, 3.72], s: [0.7, 0.6, 0.06], c: '#fff3c4', m: 'neon' },
      { t: 'box', p: [0, 1.6, 3.95], s: [4.4, 0.5, 0.3], c: colour },
      { t: 'box', p: [0, 0.95, 4.25], s: [3.6, 0.9, 0.5], c: '#5a5e66', r: [0.6, 0, 0], m: 'metal' },
      { t: 'box', p: [0, 2.3, 0.85], s: [2.4, 1.0, 1.1], c: '#2a2826', m: 'metal' },
      { t: 'box', p: [1.22, 2.3, 0.85], s: [0.06, 0.55, 0.75], c: '#ff9a2a', m: 'neon' },
      { t: 'box', p: [-1.22, 2.3, 0.85], s: [0.06, 0.55, 0.75], c: '#ff9a2a', m: 'neon' },
      { t: 'box', p: [0, 3.2, -1.7], s: [4.6, 2.8, 4.0], c: colour },
      { t: 'box', p: [0, 4.7, -1.7], s: [4.9, 0.3, 4.3], c: '#2a2826', m: 'metal' },
      { t: 'box', p: [0, 4.85, -1.7], s: [4.0, 0.6, 3.4], c: GOLD, m: 'metal' },
      { t: 'sph', p: [0.8, 5.3, -1.2], s: [1.4, 1.1, 1.3], c: '#ffd24a', m: 'metal' },
      { t: 'box', p: [2.0, 5.4, 0.7], s: [0.14, 3.2, 0.14], c: '#5a3a22' },
      { t: 'box', p: [2.0, 6.5, -0.1], s: [0.06, 1.0, 1.6], c: colour },
      { t: 'cyl', p: [-2.0, 0.85, 2.4], s: [1.7, 0.5, 1.7], c: '#2a2826', r: [0, 0, Math.PI / 2] },
      { t: 'cyl', p: [2.0, 0.85, 2.4], s: [1.7, 0.5, 1.7], c: '#2a2826', r: [0, 0, Math.PI / 2] },
      { t: 'cyl', p: [-2.0, 0.85, -2.4], s: [1.7, 0.5, 1.7], c: '#2a2826', r: [0, 0, Math.PI / 2] },
      { t: 'cyl', p: [2.0, 0.85, -2.4], s: [1.7, 0.5, 1.7], c: '#2a2826', r: [0, 0, Math.PI / 2] }
    ]);
    // the smoke streams back over the bucket
    for (var i = 0; i < 4; i++) {
      var back = 2.6 - i * 1.4;
      var sx = x + Math.sin(yaw) * back, sz = z + Math.cos(yaw) * back;
      k.shape('sph', [sx, 8.2 + i * 1.2, sz], [1.4 + i * 0.6, 1.2 + i * 0.5, 1.4 + i * 0.6],
              i < 2 ? '#d8d4cc' : '#b8b4ac', { a: 0.85 - i * 0.12 });
    }
  }

  function lever(k, x, z, pulled) {
    k.box([x, 0.6, z], [2.4, 1.2, 2.4], '#5a5550', { m: 'metal' });
    k.box([x, 1.6, z], [1.2, 0.8, 1.2], '#3a3a3a', { m: 'metal' });
    var tilt = pulled ? -0.7 : 0.5;
    k.box([x, 2.0 + Math.cos(tilt) * 1.5, z + Math.sin(tilt) * 1.5], [0.32, 3.0, 0.32], '#c8ccd2',
          { r: [tilt, 0, 0], m: 'metal' });
    k.shape('sph', [x, 2.0 + Math.cos(tilt) * 3.1, z + Math.sin(tilt) * 3.1], [0.8, 0.8, 0.8],
            pulled ? '#ff3a2a' : '#fff4d6', pulled ? { m: 'neon' } : null);
  }

  function rock(k, x, z, w, h, d, c) {
    k.box([x, h * 0.35, z], [w, h * 0.7, d], c);
    k.box([x + w * 0.06, h * 0.85, z - d * 0.05], [w * 0.7, h * 0.3, d * 0.72], c);
  }

  function fir(k, x, z, s, snow) {
    k.shape('cyl', [x, 4.5 * s, z], [1.4 * s, 9 * s, 1.4 * s], '#5a3a22');
    for (var i = 0; i < 4; i++) {
      var w = (10 - i * 2.2) * s, cy = (7.6 + i * 3.2) * s;
      k.shape('cone', [x, cy, z], [w, 5 * s, w], '#2a5a3c');
      if (snow) k.shape('cone', [x, cy + 1.7 * s, z], [w * 0.5, 1.8 * s, w * 0.5], '#eef2f6');
    }
  }

  function pushers(k, x, z, yaw, colour, n, time) {
    for (var i = 0; i < n; i++) {
      var side = i % 2 ? 1 : -1, back = -5 - Math.floor(i / 2) * 3;
      var px = x + Math.cos(yaw) * side * 3.4 + Math.sin(yaw) * back;
      var pz = z - Math.sin(yaw) * side * 3.4 + Math.cos(yaw) * back;
      k.player(px, pz, yaw, { anim: 'run', time: (time || 0.3) + i * 0.27, wear: cap(colour) });
    }
  }

  // ------------------------------------------------------------ card
  Thumbs.registerWorld('rail_rivals', {
    sky: { top: '#3a5f9a', horizon: '#f2b06a', sun: [0.62, 0.32, -0.45], clouds: 0.3, tint: '#ffd8a0' },
    camera: [[30, 26, 46], [-2, 4, -2], 44],
    build: function (parts, k) {
      k.box([0, -0.5, 0], [180, 1, 140], '#c8a06e');
      k.box([0, -0.4, -40], [180, 1.02, 60], '#b8724a');
      slant(k, -60, -30, 40, 34);
      slant(k, -60, 34, 40, -30);
      cart(k, -14, -1.6, Math.atan2(100, 64), RED);
      cart(k, -35, 18, Math.atan2(100, -64), BLUE);
      pushers(k, -14, -1.6, Math.atan2(100, 64), RED, 3, 0.2);
      pushers(k, -35, 18, Math.atan2(100, -64), BLUE, 2, 0.6);
      k.player(-2, 12, -2.2, { anim: 'run', time: 0.7, wear: cap(BLUE) });
      lever(k, 10, 2, true);
      rock(k, -40, -42, 26, 30, 18, '#9a5a3a');
      rock(k, 10, -52, 30, 44, 20, '#7a442c');
      rock(k, 36, -40, 18, 22, 14, '#a8603e');
      k.box([22, 9, -8], [1.2, 18, 1.2], '#5a3a22');
      k.box([22, 18.6, -8], [5, 1.6, 2.4], '#2a2826', { m: 'metal' });
      k.box([20.4, 18.6, -6.75], [1.2, 1.2, 0.2], '#ff3a2a', { m: 'neon' });
      k.box([23.6, 18.6, -6.75], [1.2, 1.2, 0.2], '#3aff6a', { m: 'neon' });
      k.shape('cyl', [-36, 1.6, 34], [3.2, 3.2, 3.2], '#4a7a3a');
      k.box([30, 4, 26], [12, 8, 10], '#8a5a3a', { st: 1 });
      k.box([30, 8.6, 26], [13, 1.2, 11], '#3a2a22');
    }
  });

  // -------------------------------------------------- Dustbowl Gulch
  Thumbs.registerWorld('rr_dustbowl', {
    sky: { top: '#3a5f9a', horizon: '#f2b06a', sun: [0.62, 0.32, -0.45], clouds: 0.3, tint: '#ffd8a0' },
    camera: [[44, 30, 50], [-4, 4, -4], 44],
    build: function (parts, k) {
      k.box([0, -0.5, 0], [200, 1, 160], '#c8a06e');
      straight(k, -90, 90, 4);
      // Main Street's false fronts behind the track
      [[-50, '#9a6a44', 'SALOON'], [-28, '#8a5a3a', ''], [-6, '#a87a50', ''], [16, '#7a5335', ''],
       [38, '#c89a6a', '']].forEach(function (b, i) {
        var h = 10 + (i % 3) * 3;
        k.box([b[0], h / 2, -18], [18, h, 14], b[1], { st: 1 });
        k.box([b[0], h + 2.5, -11.2], [18, 5, 0.6], b[1]);
        k.box([b[0], 3.4, -10.4], [18, 0.4, 4], '#5a3a22');
        k.box([b[0] - 6, 5, -10.6], [3, 3, 0.2], '#ffd27a', { m: 'neon' });
        k.box([b[0] + 6, 5, -10.6], [3, 3, 0.2], '#ffd27a', { m: 'neon' });
      });
      k.box([-2, 22, -26], [6, 24, 6], '#efe6d6');
      k.shape('cone', [-2, 37, -26], [7, 8, 7], '#5a4a42');
      rock(k, -70, -50, 40, 46, 20, '#9a5a3a');
      rock(k, 60, -56, 46, 56, 22, '#7a442c');
      cart(k, -6, 4, Math.PI / 2, RED);
      pushers(k, -6, 4, Math.PI / 2, RED, 3, 0.1);
      k.player(10, 14, -1.4, { anim: 'run', time: 0.5, wear: cap(BLUE) });
      // the water tower and a cactus
      [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(function (o) {
        k.box([30 + o[0] * 3, 7, 22 + o[1] * 3], [0.8, 14, 0.8], '#5a3a22');
      });
      k.shape('cyl', [30, 18, 22], [8, 8, 8], '#7a5335');
      k.shape('cone', [30, 23.4, 22], [9, 3, 9], '#4a3a2a');
      k.shape('cyl', [-30, 4, 20], [1.6, 8, 1.6], '#4a7a3a');
      k.shape('cyl', [-28.4, 4.6, 20], [1, 3, 1], '#4a7a3a');
    }
  });

  // ------------------------------------------------- Silverpine Pass
  Thumbs.registerWorld('rr_silverpine', {
    sky: { top: '#4f78b0', horizon: '#dfe8f2', sun: [0.35, 0.42, 0.55], clouds: 0.55, tint: '#eaf2ff' },
    camera: [[46, 28, 44], [-2, 2, -2], 44],
    build: function (parts, k) {
      k.box([0, -0.5, 0], [200, 1, 160], '#e8eef4');
      // the frozen lake, the trestle across it
      k.box([-6, -0.46, 0], [60, 1, 34], '#a8d0e8');
      k.box([-6, 0.1, 0], [64, 1.0, 12], '#6a5040');
      straight(k, -70, 60, 0, '#6a5040');
      for (var x = -32; x <= 20; x += 8) {
        k.box([x, -2, -5.6], [0.6, 4, 0.6], '#4a3220');
        k.box([x, -2, 5.6], [0.6, 4, 0.6], '#4a3220');
      }
      k.box([-6, 2.4, -5.6], [64, 0.4, 0.4], '#7a5232');
      k.box([-6, 2.4, 5.6], [64, 0.4, 0.4], '#7a5232');
      cart(k, 6, 0, -Math.PI / 2, BLUE);
      pushers(k, 6, 0, -Math.PI / 2, BLUE, 2, 0.3);
      // the drift ahead of it, and somebody digging
      k.shape('sph', [-16, 1.2, 0], [9, 4.4, 8], '#ffffff');
      k.shape('sph', [-19, 1.0, 2], [6, 3.4, 6], '#f4f8fc');
      k.player(-12, 6, 2.2, { anim: 'walk', time: 0.6, wear: cap(BLUE) });
      // the snow shed and the pines
      k.box([30, 6, -22], [44, 12, 1.2], '#6a4a30');
      for (var px = 10; px <= 50; px += 8) k.box([px, 6, -8], [1.2, 12, 1.2], '#6a4a30');
      k.box([30, 12.6, -15], [46, 1.2, 18], '#4a3a2e');
      k.box([30, 13.5, -15], [45, 0.6, 17], '#eef2f6');
      [[-50, -30, 1.5], [-36, -40, 1.8], [-58, 20, 1.3], [50, 30, 1.6], [-20, -46, 2.0],
       [64, -40, 1.7]].forEach(function (f) { fir(k, f[0], f[1], f[2], true); });
      k.box([-40, 12, -60], [60, 24, 10], '#7a8088');
      k.shape('cone', [-46, 40, -64], [70, 50, 30], '#6a7480');
      k.shape('cone', [-46, 58, -64], [26, 16, 12], '#f4f8fc');
    }
  });

  // --------------------------------------------------- Redrock Mesa
  Thumbs.registerWorld('rr_redrock', {
    sky: { top: '#35305e', horizon: '#ff8a50', sun: [0.82, 0.14, 0.3], clouds: 0.4, tint: '#ffb888' },
    camera: [[66, 44, 78], [6, 10, -6], 46],
    build: function (parts, k) {
      k.box([-50, -0.5, 0], [100, 1, 160], '#c8743e');
      k.box([70, -0.5, 0], [60, 1, 160], '#c8743e');
      // the gorge between, the river far down it
      k.box([20, -14, 0], [40, 2, 160], '#3a7a9a', { a: 0.9 });
      k.box([0, -7, 0], [0.5, 14, 160], '#86381e');
      k.box([40, -7, 0], [0.5, 14, 160], '#86381e');
      straight(k, -80, -4, 6);
      straight(k, 44, 90, 6);
      // the lift bridge, its span up at the top of the towers
      [-3, 43].forEach(function (x) {
        k.box([x, 18, -2], [2.4, 36, 2.4], '#8a3a2a', { m: 'metal' });
        k.box([x, 18, 14], [2.4, 36, 2.4], '#8a3a2a', { m: 'metal' });
        k.box([x, 37, 6], [3, 2, 19], '#8a3a2a', { m: 'metal' });
        k.box([x, 35.6, 6], [1.2, 1.2, 1.2], '#ff3a2a', { m: 'neon' });
      });
      k.box([20, 24, 6], [46, 1.0, 12], '#8a3a2a', { m: 'metal' });
      k.box([20, 22, 1.8], [40, 3, 0.8], '#8a3a2a', { m: 'metal' });
      k.box([20, 22, 10.2], [40, 3, 0.8], '#8a3a2a', { m: 'metal' });
      cart(k, -20, 6, Math.PI / 2, RED);
      pushers(k, -20, 6, Math.PI / 2, RED, 2, 0.2);
      k.player(60, 20, -2.4, { anim: 'idle', time: 0.2, wear: cap(BLUE) });
      // the mesa and a hoodoo
      k.box([-50, 14, -40], [60, 28, 34], '#a84a28');
      k.box([-50, 8, -22.9], [60.1, 1.4, 0.2], '#e2b890');
      k.box([-50, 20, -22.9], [60.1, 1.4, 0.2], '#e2b890');
      k.box([-50, 28.5, -40], [56, 1.2, 30], '#d88a50');
      k.box([70, 10, -30], [6, 20, 6], '#c06038');
      k.box([70.4, 21.4, -30], [10, 2.8, 9], '#86381e');
      k.shape('cyl', [-30, 3, 30], [1.6, 6, 1.6], '#4a7a3a');
    }
  });

  // ---------------------------------------------------- Lantern Deep
  Thumbs.registerWorld('rr_lantern', {
    sky: { top: '#100c0a', horizon: '#2a1c14', sun: [0.25, 0.9, 0.35], clouds: 0, tint: '#ffb070' },
    camera: [[44, 24, 46], [-6, 5, -6], 46],
    build: function (parts, k) {
      k.box([0, -0.5, 0], [160, 1, 140], '#4a3a30');
      k.box([0, 30, -60], [160, 60, 4], '#2e2622');
      k.box([-70, 30, 0], [4, 60, 140], '#2e2622');
      // the lava chasm, and the rock bridge the line crosses it on
      k.box([24, -0.49, -30], [12, 1, 44], '#2a1a14');
      k.box([24, -0.48, -30], [8, 1, 42], '#d8501a', { m: 'neon' });
      k.box([24, -0.49, 38], [12, 1, 40], '#2a1a14');
      k.box([24, -0.48, 38], [8, 1, 38], '#d8501a', { m: 'neon' });
      for (var lz = -36; lz <= 50; lz += 14) {
        if (lz > -10 && lz < 18) continue;
        k.box([24 + (lz % 3), 0.06, lz], [3, 0.1, 2.4], '#3a2420');
      }
      straight(k, -60, 70, 4, '#5a5048');
      // the timbered gallery
      for (var x = -50; x <= -6; x += 8) {
        k.box([x, 6, -3.5], [1.2, 12, 1.2], '#6a4a2e');
        k.box([x, 6, 11.5], [1.2, 12, 1.2], '#6a4a2e');
        k.box([x, 12.6, 4], [1.4, 1.2, 16.4], '#4a3220');
        k.box([x, 11.2, 4], [0.8, 1.2, 0.8], '#ffcf6a', { m: 'neon' });
      }
      cart(k, -24, 4, Math.PI / 2, BLUE);
      pushers(k, -24, 4, Math.PI / 2, BLUE, 3, 0.4);
      k.player(40, 18, -2.0, { anim: 'run', time: 0.6, wear: cap(RED) });
      // crystals and a giant mushroom
      [[-44, -30, '#5ae0ff'], [-36, -36, '#b06aff'], [-52, -24, '#7affc8']].forEach(function (c, i) {
        k.box([c[0], 4 + i, c[1]], [2, 8 + i * 2, 2], c[2], { m: 'neon' });
      });
      k.shape('cyl', [50, 6, -30], [3, 12, 3], '#e8dcc8');
      k.shape('sph', [50, 13.6, -30], [16, 5, 16], '#ff5a8a', { m: 'neon' });
      k.shape('cyl', [-56, 0.6, 30], [0.8, 1.2, 0.8], '#e8dcc8');
      k.shape('sph', [-56, 1.5, 30], [2.4, 1, 2.4], '#5affd2', { m: 'neon' });
      for (var i = 0; i < 10; i++) {
        k.shape('cone', [-60 + i * 13, 54, -40 + (i % 3) * 20], [3, 10, 3], '#3e3430', { r: [Math.PI, 0, 0] });
      }
    }
  });
})(window);
