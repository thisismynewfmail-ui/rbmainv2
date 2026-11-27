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

  // ------------------------------------------- Golden Spike Summit
  /* The gulch trestle with its gap: the Crimson cart waiting at the
     railhead, a hand carrying the next rail in, the Bluebird line's cart
     beyond; sage, junipers, the terraced hills. */
  Thumbs.registerWorld('rr_goldspike', {
    sky: { top: '#3a6ab8', horizon: '#f2e6c8', sun: [0.3, 0.9, -0.25], clouds: 0.35, tint: '#fff2d8' },
    camera: [[44, 24, 46], [-6, 0, -6], 44],
    build: function (parts, k) {
      k.box([-90, -0.5, 0], [132, 1, 260], '#c8b47a', { st: 1 });
      k.box([90, -0.5, 0], [132, 1, 260], '#c8b47a', { st: 1 });
      k.box([0, -12.5, 0], [48, 1, 260], '#a08a62', { st: 1 });
      k.box([-27, -6.5, 0], [6, 11, 260], '#7a5a40');
      k.box([27, -6.5, 0], [6, 11, 260], '#7a5a40');
      // the hills behind, terrace on terrace
      [[-70, -70, 90, 40], [40, -80, 110, 36]].forEach(function (h, i) {
        for (var t = 0; t < 4; t++) {
          k.box([h[0], 1 + t * 2, h[1] - t * 3], [h[2] - t * 16, 2, h[3] - t * 6],
                t % 2 ? '#b8a068' : (i ? '#a07a58' : '#c8b47a'), { st: 1 });
        }
      });
      // the trestle: bents, the deck, the gap where the rails will go
      for (var x = -22; x <= 22; x += 7.3) {
        [-6, -2.4, 2.4, 6].forEach(function (w) { k.box([x, -6.2, 4 + w], [0.9, 11.6, 0.9], '#7a5838'); });
        k.box([x, -0.9, 4], [1.0, 0.8, 14], '#5a4028');
      }
      k.box([0, -0.4, 4], [48, 0.8, 14], '#6a4a30', { st: 1 });
      for (var t2 = -23; t2 < 24; t2 += 2.4) k.box([t2, 0.12, 4], [0.8, 0.24, 6], '#5e4630');
      straight(k, -150, -24, 4);
      straight(k, 24, 150, 4);
      k.box([-12, 0.37, 2.4], [24, 0.14, 0.36], '#8c8a86', { m: 'metal' });
      k.box([-12, 0.37, 5.6], [24, 0.14, 0.36], '#8c8a86', { m: 'metal' });
      for (var sk = 3; sk < 22; sk += 6) {
        k.box([sk, 0.6, 0.6], [0.3, 1.2, 0.3], '#c8a878');
        k.box([sk, 1.25, 0.6], [0.5, 0.3, 0.06], '#d83a2a');
      }
      // the railhead's pole
      for (var s2 = 0; s2 < 4; s2++) k.box([0, 0.5 + s2 * 0.9, 4], [0.36, 0.9, 0.36], s2 % 2 ? '#f2f2ee' : '#d82a1a');
      k.box([0.9, 3.6, 4], [1.6, 1.0, 0.06], '#ff8a7a');
      cart(k, -10, 4, Math.PI / 2, RED);
      pushers(k, -10, 4, Math.PI / 2, RED, 2, 0.3);
      // the next rail coming, on a shoulder
      k.player(12, 16, -2.6, { anim: 'walk', time: 0.4, wear: cap(RED).concat([
        { t: 'box', p: [-1.1, 5.3, 0], s: [0.36, 0.3, 6.2], c: '#8c8a86', r: [0.12, 0, 0], m: 'metal' }]) });
      k.player(-36, 20, 2.4, { anim: 'run', time: 0.7, wear: cap(BLUE) });
      // the rail stack, junipers, sage
      for (var l = 0; l < 3; l++) k.box([-44, 1.0 + l * 0.5, 26], [14, 0.5, 3.4 - l * 0.6], '#8c8a86', { m: 'metal' });
      [[-58, -24], [52, -30], [-80, 20]].forEach(function (j) {
        k.shape('cyl', [j[0], 2.6, j[1]], [1.2, 5.2, 1.2], '#6a4a32');
        k.shape('sph', [j[0], 6.8, j[1]], [7, 4.6, 6.4], '#4a6a44');
      });
      [[-60, 34], [-48, -16], [44, -18], [62, 24], [30, 30], [-20, 30]].forEach(function (p) {
        k.shape('sph', [p[0], 0.7, p[1]], [2.6, 1.6, 2.4], '#8a9a78');
      });
      cart(k, 66, -36, Math.PI / 2, BLUE);
      straight(k, 36, 150, -36);
    }
  });

  // ------------------------------------------------ Union Terminal
  /* Dusk at the throat: Union Tower with its cabin lit over the diamond, a
     cart running under the signal gantry toward the train shed's great
     glass arch and its clock, coaches waiting inside; Upper Town's wall
     and the hotel above the line, the city's lit towers behind, a gas
     lamp. */
  Thumbs.registerWorld('rr_union', {
    sky: { top: '#1a2448', horizon: '#e8865a', sun: [0.18, 0.12, -0.96], clouds: 0.4, tint: '#ffb88a' },
    camera: [[-50, 30, 50], [26, 6, -10], 46],
    build: function (parts, k) {
      k.box([20, -0.5, -10], [260, 1, 220], '#5a5652', { st: 1 });
      slant(k, -70, -46, 40, 30);
      slant(k, -70, 30, 40, -46);
      straight(k, 40, 100, 30);
      straight(k, 40, 100, -46);
      straight(k, 40, 100, -8);
      // the city behind: towers with lit windows against the dusk
      var towers = [[128, -96, 14, 34], [140, -60, 12, 46], [126, -24, 16, 28], [150, 8, 14, 52],
                    [130, 44, 12, 30], [146, 76, 16, 40], [92, -112, 18, 38], [56, -118, 14, 26],
                    [20, -110, 16, 44], [-16, -116, 12, 30], [118, 104, 14, 24]];
      towers.forEach(function (t, n) {
        var tone = n % 3 === 0 ? '#3a3442' : (n % 3 === 1 ? '#4a3a3a' : '#34383f');
        k.box([t[0], t[3] / 2, t[1]], [t[2], t[3], t[2]], tone, { st: 1 });
        k.box([t[0], t[3] + 0.6, t[1]], [t[2] + 1, 1.2, t[2] + 1], '#2a2630');
        for (var f = 1; f * 6 < t[3] - 2; f++) {
          for (var w = 0; w < 3; w++) {
            if ((f * 7 + w * 3 + n) % 4 === 0) continue;
            k.box([t[0] - t[2] / 2 - 0.12, f * 6, t[1] - t[2] / 3 + w * t[2] / 3], [0.2, 2.2, 1.8],
                  '#ffd27a', { m: 'neon' });
          }
        }
      });
      // Upper Town's wall, its railing and the hotel
      k.box([-40, 3, -58], [100, 6, 24], '#6a6660', { st: 1 });
      k.box([-40, 3, -45.8], [100, 6, 0.6], '#8a3a2a');
      k.box([-40, 7.5, -46.4], [100, 0.3, 0.3], '#3a4048', { m: 'metal' });
      k.box([-56, 6 + 13, -62], [28, 26, 16], '#c8bca4');
      for (var w2 = 0; w2 < 3; w2++) {
        for (var f2 = 0; f2 < 3; f2++) k.box([-64 + w2 * 8, 10 + f2 * 7, -53.9], [3, 3.6, 0.2], '#ffd27a', { m: 'neon' });
      }
      k.box([-56, 6 + 26.6, -62], [29, 1.2, 17], '#4a3a3a');
      // Union Tower and its cabin over the diamond
      k.box([-26, 6, -8], [12, 12, 12], '#8a3a2a');
      k.box([-26, 13.2 + 4.5, -8], [8, 9, 8], '#c8b898');
      k.box([-26, 17.5, -3.95], [5, 3, 0.2], '#ffd27a', { m: 'neon' });
      k.box([-21.8, 21, -8], [0.4, 1, 1], '#3aff6a', { m: 'neon' });
      k.box([-26, 22.6, -8], [9, 0.6, 9], '#3a3a40');
      // the gantry over the throat
      k.box([22, 8.5, -40], [1.2, 17, 1.2], '#3a4048', { m: 'metal' });
      k.box([22, 8.5, 26], [1.2, 17, 1.2], '#3a4048', { m: 'metal' });
      k.box([22, 17.6, -7], [1.4, 1.2, 67], '#3a4048', { m: 'metal' });
      k.box([22.3, 20, 16], [0.1, 0.5, 2.6], '#d8282a', { r: [0.5, 0, 0] });
      k.box([22.3, 20, -30], [0.1, 0.5, 2.6], '#d8282a', { r: [-0.5, 0, 0] });
      // the shed: brick sides, five ribs with glass between, the clock
      k.box([72, 8, 48], [56, 16, 2], '#8a3a2a', { st: 1 });
      k.box([72, 8, -64], [56, 16, 2], '#8a3a2a', { st: 1 });
      for (var r = 0; r < 5; r++) {
        for (var i = 0; i < 10; i++) {
          var a0 = Math.PI * i / 10, a1 = Math.PI * (i + 1) / 10;
          var za = -8 - Math.cos(a0) * 56, zb = -8 - Math.cos(a1) * 56;
          var ya = 16 + Math.sin(a0) * 22, yb = 16 + Math.sin(a1) * 22;
          var tilt = { r: [-Math.atan2(yb - ya, zb - za), 0, 0], m: 'metal' };
          var len = Math.hypot(zb - za, yb - ya);
          k.box([46 + r * 13, (ya + yb) / 2, (za + zb) / 2], [1.2, 1.2, len], '#2a2e38', tilt);
          if (r < 4) {
            k.box([52.5 + r * 13, (ya + yb) / 2, (za + zb) / 2], [11.8, 0.3, len], '#9ec4d4',
                  { r: tilt.r, a: 0.45, m: 'glass' });
          }
        }
      }
      // the end screen: glazing strips under the arch, a fan of bars and
      // the great clock
      for (var zs = -60; zs < 44; zs += 8) {
        var e = (zs + 4 + 8) / 56, h = 22 * Math.sqrt(Math.max(0, 1 - e * e));
        k.box([45.9, 16 + h / 2, zs + 4], [0.2, h, 8], '#9ec4d4', { a: 0.3, m: 'glass' });
      }
      for (var b = 1; b < 6; b++) {
        var ang = Math.PI * b / 6;
        var dz = -Math.cos(ang) * 56, dy = Math.sin(ang) * 22;
        k.box([45.6, 16 + dy / 2, -8 + dz / 2], [0.5, 0.5, Math.hypot(dz, dy)], '#2a2e38',
              { r: [-Math.atan2(dy, dz), 0, 0], m: 'metal' });
      }
      k.shape('cyl', [45.4, 29, -8], [8, 0.4, 8], '#2a2e38', { r: [0, 0, Math.PI / 2], m: 'metal' });
      k.shape('cyl', [45.0, 29, -8], [7, 0.4, 7], '#f4ecd8', { r: [0, 0, Math.PI / 2], m: 'neon' });
      k.box([44.7, 30.4, -8], [0.2, 3, 0.45], '#1a1a1a');
      k.box([44.7, 29, -6.9], [0.2, 0.45, 2.4], '#1a1a1a');
      // coaches at the platforms, a lit concourse at the far end
      [[30, '#2f4a3a'], [-8, '#5a2a2a'], [-46, '#2a3a5a']].forEach(function (c2, n) {
        var cz = c2[0] - 22;
        if (n === 1) return;
        k.box([80, 4.6, cz], [28, 7.4, 6], c2[1]);
        for (var c = 0; c < 6; c++) k.box([69 + c * 4.4, 5.4, cz + 3.1], [1.6, 1.8, 0.1], '#ffe0a0', { m: 'neon' });
        k.box([80, 8.5, cz], [28.4, 0.5, 6.4], '#2a2826');
      });
      k.box([80, 0.6, 11], [44, 1.2, 8], '#8a6a4a', { st: 1 });
      k.box([80, 0.6, -27], [44, 1.2, 8], '#8a6a4a', { st: 1 });
      k.box([100, 6, -8], [4, 12, 110], '#c8bca4', { st: 1 });
      for (var g = 0; g < 7; g++) k.box([97.9, 5, -50 + g * 14], [0.2, 4, 5], '#ffd27a', { m: 'neon' });
      cart(k, 2, 0, Math.atan2(110, 76), RED);
      pushers(k, 2, 0, Math.atan2(110, 76), RED, 2, 0.4);
      k.player(-20, 22, 2.2, { anim: 'run', time: 0.6, wear: cap(BLUE) });
      k.shape('cyl', [-6, 6.5, 30], [0.8, 13, 0.8], '#3a4048', { m: 'metal' });
      k.box([-6, 13.4, 30], [1.6, 1.2, 1.6], '#ffcf7a', { m: 'neon' });
    }
  });
  // ------------------------------------------------ Thunder Junction
  /* Storm light at the Star Diamond: the through freight thundering down
     the main line over the crossing, the gates down and their lamps lit,
     a red cart held at its stop board with its pushers, the yellow depot
     with its order board, the grain elevators behind -- lightning on the
     tall one's rod -- and the breaks under the storm. */
  Thumbs.registerWorld('rr_thunder', {
    sky: { top: '#1e242e', horizon: '#c8b888', sun: [-0.7, 0.16, 0.4], clouds: 0.95, tint: '#c8ccc0' },
    camera: [[-34, 24, 66], [-18, 10, -26], 50],
    build: function (parts, k) {
      k.box([0, -0.5, -10], [240, 1, 200], '#6f8048', { st: 1 });
      // swells and the breaks behind
      k.shape('sph', [-70, -6, 30], [70, 16, 50], '#7a8a4e');
      k.shape('sph', [70, -6, 40], [80, 18, 60], '#7a8a4e');
      for (var b = 0; b < 12; b++) {
        var bh = 14 + (b * 7 % 5) * 4;
        k.box([-130 + b * 24, bh / 2, -104 - (b % 2) * 6], [26, bh, 18], b % 2 ? '#6e5038' : '#8a6a4a', { st: 1 });
        k.box([-130 + b * 24, bh * 0.55, -94.9 - (b % 2) * 6], [26.2, 1.6, 0.2], '#a8865c');
      }
      // the lines: the main line north to south, the race lines across it
      slant(k, 0, -92, 0, 70);
      slant(k, -90, 40, 70, -46);
      slant(k, -90, -46, 70, 40);
      // the grain elevators and the lightning on the tallest
      [[-76, 26], [-60, 31], [-44, 36]].forEach(function (e, i) {
        k.box([e[0], e[1] / 2, -70], [13, e[1], 13], '#8a3428');
        k.box([e[0], e[1] + 3, -70], [6.5, 6, 9], '#6a2a22');
        k.box([e[0], e[1] * 0.62, -63.4], [11, 2.6, 0.2], '#e8e2d4');
      });
      k.box([-44, 46, -70], [0.3, 8, 0.3], '#8a8680', { m: 'metal' });
      var bolt = [[-34, 80], [-31, 72], [-38, 65], [-34, 58], [-41, 54], [-44, 50]];
      for (var j = 0; j < bolt.length - 1; j++) {
        var a = bolt[j], c = bolt[j + 1];
        var len = Math.hypot(c[0] - a[0], c[1] - a[1]);
        k.box([(a[0] + c[0]) / 2, (a[1] + c[1]) / 2, -70], [0.8, len, 0.8], '#eef2ff',
              { r: [0, 0, Math.atan2(c[0] - a[0], c[1] - a[1])], m: 'neon' });
      }
      k.shape('sph', [-44, 50, -70], [8, 8, 8], '#dce4ff', { a: 0.5, m: 'neon' });
      // the depot, its bay and the order board
      k.box([-22, 5.4, -36], [10, 9, 22], '#d8b860');
      k.box([-22, 10.4, -36], [11, 1, 23], '#6a3e24');
      k.box([-22, 11.6, -36], [6, 1.4, 23], '#6a3e24');
      k.box([-16, 3.2, -36], [2.4, 5, 5], '#d8b860');
      k.box([-14.75, 3.6, -36], [0.1, 2.4, 3.6], '#ffd88a', { m: 'neon' });
      k.box([-12, 8, -36], [0.5, 16, 0.5], '#3a3a3e', { m: 'metal' });
      k.box([-12, 15.6, -38.4], [0.2, 0.6, 4.4], '#c8281e', { r: [0.5, 0, 0] });
      k.box([-12, 15.6, -33.6], [0.2, 0.6, 4.4], '#c8281e', { r: [-0.5, 0, 0] });
      k.shape('sph', [-11.6, 14.6, -36], [0.8, 0.8, 0.8], '#5aff7a', { m: 'neon' });
      // the freight: engine over the diamond, its cars strung out behind
      var y0 = 0.44;
      k.box([0, y0 + 1.6, 6], [4, 1.8, 20], '#141414', { m: 'metal' });
      k.shape('cyl', [0, y0 + 4.9, 8], [4.8, 13, 4.8], '#1e2022', { r: [Math.PI / 2, 0, 0], m: 'metal' });
      k.shape('cyl', [0, y0 + 4.9, 2], [4.96, 0.4, 4.96], '#c8a040', { r: [Math.PI / 2, 0, 0], m: 'metal' });
      k.shape('cyl', [0, y0 + 8.4, 13.4], [1.5, 3, 1.5], '#141414', { m: 'metal' });
      k.box([0, y0 + 5.8, -0.8], [5.4, 5.6, 5], '#1e2022', { m: 'metal' });
      k.box([0, y0 + 6.6, 1.72], [3, 1.4, 0.1], '#ffd88a', { m: 'neon' });
      k.box([0, y0 + 7.6, 16.3], [1.2, 1.1, 0.1], '#fff6c8', { m: 'neon' });
      k.shape('sph', [0, y0 + 7.6, 16.6], [3.4, 3.4, 1.0], '#fff6c8', { a: 0.5, m: 'neon' });
      for (var p2 = 0; p2 < 5; p2++) {
        k.shape('sph', [p2 * 0.8, y0 + 11 + p2 * 1.6, 12 - p2 * 4.5], [2.6 + p2, 2 + p2 * 0.8, 2.6 + p2], '#4a4a4e',
                { a: 0.8 - p2 * 0.12 });
      }
      k.box([0, y0 + 4.2, -9], [5.2, 4.4, 10], '#1e2022', { m: 'metal' });
      var cars = [['#6a2e22', 'box'], ['#1e1e22', 'tank'], ['#7a5232', 'box'], ['#3a3a3c', 'box'], ['#d8b048', 'box']];
      cars.forEach(function (c2, i) {
        var cz = -23 - i * 15.2;
        if (c2[1] === 'tank') {
          k.shape('cyl', [0, y0 + 5, cz], [4.8, 13, 4.8], c2[0], { r: [Math.PI / 2, 0, 0], m: 'metal' });
        } else {
          k.box([0, y0 + 5.4, cz], [5.4, 6, 13.4], c2[0]);
          k.box([0, y0 + 8.5, cz], [5.6, 0.25, 13.6], '#2a2624');
        }
        k.box([0, y0 + 1.6, cz], [4.4, 1.6, 12.8], '#1e1c1a', { m: 'metal' });
      });
      // the gates down, their lamps lit
      [[-6.3, -10.1, -0.62], [6.3, 10.1, 2.5]].forEach(function (g) {
        k.box([g[0], 4.3, g[1]], [0.7, 8.6, 0.7], '#e8e2d4');
        for (var sgm = 0; sgm < 5; sgm++) {
          var u = 1 + sgm * 1.7;
          k.box([g[0] + Math.sin(g[2]) * u, 4.2, g[1] + Math.cos(g[2]) * u], [0.36, 0.36, 1.72],
                sgm % 2 ? '#f2f2ee' : '#c82a1e', { r: [0, g[2], 0] });
        }
        k.shape('sph', [g[0] - 0.6, 4.6, g[1] + 0.6], [1.0, 1.0, 1.0], '#ff3a2a', { m: 'neon' });
        k.box([g[0], 7.8, g[1]], [5, 0.7, 0.12], '#e8e2d4', { r: [0, 0.6, 0.78] });
        k.box([g[0], 7.8, g[1]], [5, 0.7, 0.12], '#e8e2d4', { r: [0, 0.6, -0.78] });
      });
      // a red cart held at its stop board, pushing in vain; blue on the watch
      cart(k, -20, 14.3, Math.atan2(80, -43), RED);
      pushers(k, -20, 14.3, Math.atan2(80, -43), RED, 2, 0.5);
      k.player(-30, -12, 1.2, { anim: 'run', time: 0.4, wear: cap(BLUE) });
      k.box([-14, 2.2, 21], [0.4, 4.4, 0.4], '#5a3a22');
      k.box([-14, 4.8, 21], [2.4, 1.6, 0.2], '#e8e2d4');
      k.box([-14, 4.8, 21.12], [1.6, 0.8, 0.05], '#c8281e');
    }
  });
})(window);
