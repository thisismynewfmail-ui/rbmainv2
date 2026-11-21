/* Blackout Relay's world-page pictures: a diorama of each map in the
   rotation, built from the same blocks the game draws with
   (Thumbs.registerWorld; loaded by thumbs.js the first time one is asked
   for).  Ironvale keeps the world's card ('relay', in thumbs.js itself).
   Every player wears the classic default -- yellow skin, red torso, blue
   legs -- and carries a flag or a gun; teams show in what they carry. */
(function (global) {
  'use strict';
  var Thumbs = global.Thumbs;
  if (!Thumbs || !Thumbs.registerWorld) return;

  var RED = '#c4281c', BLUE = '#0d69ac', RED_NEON = '#ff6a54', BLUE_NEON = '#63c0ff';

  /* A capture-the-flag flag, held: the item a carrier's hand draws. */
  function flagItem(colour) {
    return { parts: [
      { t: 'cyl', p: [0, 2.4, 0], s: [0.25, 5.4, 0.25], c: '#d8dce0', m: 'metal' },
      { t: 'box', p: [0, 4.3, 1.3], s: [0.12, 1.6, 2.6], c: colour }
    ] };
  }

  /* A flag on its pedestal, the way every map shows one. */
  function pedestal(k, x, y, z, colour, neon) {
    k.box([x, y + 0.6, z], [6.4, 1.2, 6.4], '#787f86');
    k.box([x, y + 1.6, z], [4.2, 0.8, 4.2], colour);
    k.shape('cyl', [x, y + 2.05, z], [3.2, 0.12, 3.2], neon, { m: 'neon' });
    k.shape('cyl', [x, y + 4.6, z], [0.22, 5.0, 0.22], '#d8dce0', { m: 'metal' });
    k.box([x + 1.2, y + 6.3, z], [2.4, 1.5, 0.12], colour);
  }

  function rain(k, n, x0, x1, z0, z1, seed) {
    var s = seed || 1;
    function r() { s = (s * 9301 + 49297) % 233280; return s / 233280; }
    for (var i = 0; i < n; i++) {
      k.box([x0 + r() * (x1 - x0), 2 + r() * 22, z0 + r() * (z1 - z0)], [0.06, 1.6, 0.06],
            '#a8c8e8', { a: 0.5 });
    }
  }

  // ------------------------------------------------- Substation Nine
  Thumbs.registerWorld('br_substation', {
    camera: [[30, 18, 40], [0, 5, -2], 46],
    sky: { top: '#070a14', horizon: '#2a3446', sun: [0.3, 0.55, -0.6], clouds: 0.8, tint: '#8aa0c8' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [120, 1, 90], '#5c5f66', { st: 1 });
      k.box([0, 0.03, 8], [120, 0.06, 12], '#33363c');
      // the control house and its yard
      k.box([-10, 4, -10], [22, 8, 12], '#9a4f3a');
      k.box([-10, 8.4, -10], [23, 0.8, 13], '#787f86', { st: 1 });
      k.box([-10, 6.6, -3.95], [12, 1.4, 0.1], '#1b1f26');
      k.box([-10, 6.6, -3.9], [10, 0.6, 0.05], '#ffb050', { m: 'neon' });
      for (var i = 0; i < 3; i++) {
        k.box([4 + i * 7, 2.5, -14], [4.5, 5, 3.5], '#5d6b62', { m: 'metal' });
        for (var j = 0; j < 3; j++) {
          k.shape('cyl', [2.6 + i * 7 + j * 1.4, 5.8, -14], [0.5, 1.4, 0.5], '#d8e2e8');
          k.shape('sph', [2.6 + i * 7 + j * 1.4, 6.7, -14], [0.6, 0.6, 0.6], '#9fe8ff', { m: 'neon' });
        }
      }
      // the arc between two insulators
      k.box([7.5, 7.4, -14], [6, 0.12, 0.12], '#cfefff', { m: 'neon', r: [0, 0, 0.18] });
      // dark towers behind, one window lit
      [[-40, -40, 30], [-20, -44, 44], [6, -46, 38], [30, -42, 50], [50, -38, 34]].forEach(function (tw, n) {
        k.box([tw[0], tw[2] / 2, tw[1]], [16, tw[2], 12], '#151a22');
        if (n === 2) k.box([tw[0] + 3, tw[2] * 0.6, tw[1] + 6.05], [1.6, 1.4, 0.1], '#ffcf7a', { m: 'neon' });
      });
      // the police car on the corner, lights going
      k.box([16, 1.4, 12], [9, 2, 4.2], '#e8e8ec', { m: 'metal' });
      k.box([15.5, 3.0, 12], [4.5, 1.2, 3.6], '#2b3a44', { m: 'metal' });
      k.box([15.5, 3.75, 11.4], [1.6, 0.4, 0.8], '#ff3a2a', { m: 'neon' });
      k.box([15.5, 3.75, 12.6], [1.6, 0.4, 0.8], '#3a7aff', { m: 'neon' });
      // a blue runner with red's flag, a red defender after him
      k.player(2, 10, 0.9, { anim: 'run', time: 0.3, holding: flagItem(RED),
                             wear: [{ t: 'box', p: [0, 6.0, 0], s: [2.2, 0.5, 2.2], c: BLUE }] });
      k.player(-8, 4, 2.2, { anim: 'run', time: 0.8,
                             wear: [{ t: 'box', p: [0, 6.0, 0], s: [2.2, 0.5, 2.2], c: RED }] });
      k.tracer([-7, 4.6, 4.6], [1.6, 4.4, 9.6]);
      pedestal(k, -34, 0, 10, RED, RED_NEON);
      rain(k, 120, -30, 40, -20, 30, 7);
    }
  });


  function cap(colour) {
    return [{ t: 'box', p: [0, 6.0, 0], s: [2.2, 0.5, 2.2], c: colour }];
  }

  // ------------------------------------------------- Thimble Acre
  Thumbs.registerWorld('br_thimble', {
    camera: [[26, 14, 34], [0, 6, -4], 50],
    sky: { top: '#5a8ad8', horizon: '#ffd08a', sun: [0.55, 0.25, -0.5], clouds: 0.45, tint: '#ffe0a8' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [120, 1, 90], '#5aa03a', { st: 1 });
      // the fence and the cat over it
      k.box([0, 14, -30], [120, 28, 2], '#7a5a34');
      k.shape('sph', [-8, 30, -30], [14, 11, 10], '#e8a04a');
      k.shape('cone', [-12, 37, -30], [4, 6, 3], '#e8a04a');
      k.shape('cone', [-4, 37, -30], [4, 6, 3], '#e8a04a');
      k.shape('sph', [-10.5, 31, -25.2], [2, 2.4, 0.6], '#f2f2d8');
      k.shape('sph', [-5.5, 31, -25.2], [2, 2.4, 0.6], '#f2f2d8');
      // the upturned pot
      k.box([6, 5.5, -12], [16, 11, 16], '#c8643c');
      k.box([6, 1, -12], [17.4, 2, 17.4], '#b85a34');
      k.box([6, 11.4, -12], [14, 0.8, 14], '#a84e2c', { st: 1 });
      // a red brick castle wall
      k.box([-20, 3.5, 0], [12, 7, 3], RED, { st: 1 });
      k.box([-26, 5, 0], [4, 10, 4], '#8c1c15', { st: 1 });
      pedestal(k, -20, 0, 6, RED, RED_NEON);
      // the hose
      k.box([4, 1.5, 6], [40, 3, 3], '#3a9a3a', { st: 1 });
      // a cabbage, grass blades
      k.shape('sph', [18, 3, -2], [7, 6, 7], '#7ab84a');
      for (var i = 0; i < 6; i++) k.box([-6 + i * 3.4, 3, 14 - (i % 2) * 2], [0.6, 6 + (i % 3) * 2, 0.6], '#4a8a30');
      k.player(-2, 10, 0.8, { anim: 'run', time: 0.4, holding: flagItem(RED), wear: cap(BLUE) });
      k.player(-12, 4, 2.4, { anim: 'run', time: 0.9, wear: cap(RED) });
    }
  });

  // ------------------------------------------------- The Orrery
  Thumbs.registerWorld('br_orrery', {
    camera: [[28, 16, 36], [0, 8, -4], 50],
    sky: { top: '#2a2458', horizon: '#e08a7a', sun: [-0.4, 0.12, 0.6], clouds: 0.35, tint: '#ffc8a8' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [120, 1, 90], '#4a8a4a', { st: 1 });
      k.box([0, 0.5, -6], [44, 1, 30], '#a8a090', { st: 1 });
      // the clockhouse and the sun on its column
      k.box([0, 4, -8], [16, 8, 12], '#d8d0c0');
      k.box([0, 8.4, -8], [17, 0.8, 13], '#8a6a28', { st: 1 });
      k.shape('cyl', [0, 16, -8], [2, 16, 2], '#8a6a28', { m: 'metal' });
      k.shape('sph', [0, 25, -8], [8, 8, 8], '#ffb84a', { m: 'neon' });
      k.box([0, 25, -8], [11, 0.4, 0.4], '#c89a3a', { m: 'metal' });
      // planet decks on columns
      [[-9, 4, '#4a7ad8'], [9, 4, '#d86a3a'], [-9, -18, '#d86a3a'], [9, -18, '#4a7ad8']].forEach(function (p) {
        k.shape('cyl', [p[0], 4, p[1]], [1.2, 8, 1.2], '#c89a3a', { m: 'metal' });
        k.box([p[0], 8.4, p[1]], [5, 0.8, 5], '#8a6a28', { st: 1 });
        k.shape('sph', [p[0], 10.2, p[1]], [2.6, 2.6, 2.6], p[2]);
      });
      // a hedge, a lamp, a glasshouse corner
      k.box([-22, 2, 10], [10, 4, 3], '#2f6a36', { st: 1 });
      k.shape('cyl', [16, 3, 12], [0.4, 6, 0.4], '#2a2a2a');
      k.box([16, 6.3, 12], [1, 0.6, 1], '#ffd890', { m: 'neon' });
      k.box([-30, 5, -14], [12, 10, 12], '#bfe8e0', { m: 'glass', a: 0.5 });
      pedestal(k, -30, 0, -14, RED, RED_NEON);
      k.player(6, 8, 0.6, { anim: 'run', time: 0.3, holding: flagItem(RED), wear: cap(BLUE) });
      k.player(-6, 10, 2.6, { anim: 'idle', time: 0.2, wear: cap(RED) });
    }
  });

  // ------------------------------------------------- Saltglass Flats
  Thumbs.registerWorld('br_saltglass', {
    camera: [[30, 15, 38], [0, 8, -4], 50],
    sky: { top: '#120e24', horizon: '#4a3a5a', sun: [0.2, 0.4, 0.7], clouds: 0.9, tint: '#b8a8e8' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [120, 1, 90], '#e2ddd2', { st: 1 });
      // the hall and its two coils, arcing
      k.box([0, 4, -12], [26, 8, 12], '#5a5e68');
      k.box([0, 8.4, -12], [27, 0.8, 13], '#787f86', { st: 1 });
      [-6, 6].forEach(function (x) {
        k.shape('cyl', [x, 13, -12], [2.4, 9, 2.4], '#c87a3a', { m: 'metal' });
        k.shape('cyl', [x, 17.8, -12], [5, 1.2, 5], '#c8ccd2', { m: 'metal' });
      });
      k.box([0, 18.6, -12], [12, 0.3, 0.3], '#bfe8ff', { m: 'neon' });
      // lightning rods and fulgurites
      [[-20, 6], [18, 8], [-10, 14]].forEach(function (r) {
        k.shape('cyl', [r[0], 8, r[1]], [0.5, 16, 0.5], '#6f767d', { m: 'metal' });
        k.shape('sph', [r[0], 16.4, r[1]], [0.8, 0.8, 0.8], '#9fe8ff', { m: 'neon' });
      });
      [[10, 10, 5], [12, 11, 3], [-24, -4, 4]].forEach(function (f) {
        k.box([f[0], f[2] / 2, f[1]], [1.2, f[2], 1], '#7ad8e8', { m: 'glass', a: 0.75 });
      });
      // a salt cone and the works on its mesa
      k.box([-34, 1, 0], [20, 2, 30], '#c8b8a0', { st: 1 });
      k.shape('cone', [-30, 7, 8], [8, 9, 8], '#f0ece4');
      pedestal(k, -34, 2, -6, RED, RED_NEON);
      // the speed course and the rocket car
      k.box([0, 0.03, 20], [120, 0.06, 3], '#1b1b1f');
      k.box([22, 1.2, 22], [3, 2.4, 10], '#c8ccd2', { m: 'metal' });
      k.player(-4, 6, 0.4, { anim: 'run', time: 0.5, holding: flagItem(RED), wear: cap(BLUE) });
      k.player(8, 2, -2.6, { anim: 'run', time: 0.1, wear: cap(RED) });
    }
  });

  // ------------------------------------------------- Drawdown
  Thumbs.registerWorld('br_drawdown', {
    camera: [[28, 16, 38], [0, 8, -4], 50],
    sky: { top: '#7e868e', horizon: '#cfc8b8', sun: [0.3, 0.6, 0.5], clouds: 0.95, tint: '#e8e0d0' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [120, 1, 90], '#8a7a5a', { st: 1 });
      // the valve tower with its high-water bands and crane
      k.box([0, 13, -10], [8, 26, 8], '#b6bcc1');
      [12, 16, 20].forEach(function (y) { k.box([0, y, -10], [8.3, 0.5, 8.3], '#6a7a6a'); });
      k.box([0, 27, -10], [6, 3, 6], '#c8c0a8');
      k.box([0, 31, -10], [0.5, 5, 0.5], '#8a5a3a');
      k.box([2.5, 33.4, -10], [5, 0.5, 0.5], '#8a5a3a');
      // roofless cottages, one with its slates on
      k.box([-18, 3, 0], [10, 6, 0.8], '#9a968a');
      k.box([-22.6, 3, 4], [0.8, 6, 8], '#9a968a');
      k.box([-13.4, 3, 4], [0.8, 6, 8], '#9a968a');
      k.box([16, 3.5, 2], [10, 7, 8], '#a89a84');
      k.box([16, 7.6, 2], [11, 1, 9], '#4a4e56', { st: 1 });
      k.box([16, 8.8, 2], [11, 1, 6], '#4a4e56');
      // the phone box, a stranded boat, the chapel on its hill
      k.box([4, 2, 10], [1.6, 4, 1.6], '#c42b20');
      k.box([-6, 0.8, 14], [8, 1.6, 3], '#3a6a8a');
      k.box([-34, 1, -6], [18, 2, 20], '#5a6a3a', { st: 1 });
      k.box([-34, 5, -6], [10, 6, 8], '#9a968a');
      k.box([-40, 9, -6], [4, 14, 4], '#7e7a70');
      k.shape('cone', [-40, 18, -6], [4, 5, 4], '#4a4e56');
      pedestal(k, -32, 2, -6, RED, RED_NEON);
      k.player(-2, 6, 0.9, { anim: 'run', time: 0.3, holding: flagItem(RED), wear: cap(BLUE) });
      k.player(8, 0, -2.4, { anim: 'run', time: 0.8, wear: cap(RED) });
    }
  });


  // ------------------------------------------------- Lantern Terraces
  Thumbs.registerWorld('br_lantern', {
    camera: [[28, 16, 38], [0, 8, -4], 50],
    sky: { top: '#08112a', horizon: '#3a2a4a', sun: [0.2, 0.45, 0.8], clouds: 0.25, tint: '#ffd8a8' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [120, 1, 90], '#3a5a2e', { st: 1 });
      k.box([0, 0.5, -4], [40, 1, 30], '#9a968c', { st: 1 });
      // the pagoda
      var y = 1;
      [[16, 5, '#e8d8b8'], [13, 4, '#a8281c'], [10, 3.4, '#e8d8b8'], [7, 3, '#a8281c']].forEach(function (t) {
        k.box([0, y + t[1] / 2, -8], [t[0], t[1], t[0] * 0.8], t[2]);
        y += t[1];
        k.box([0, y + 0.3, -8], [t[0] + 4, 0.6, t[0] * 0.8 + 4], '#2a3a3a', { st: 1 });
        y += 0.6;
      });
      k.shape('cyl', [0, y + 2, -8], [0.4, 4, 0.4], '#e8b84a', { m: 'metal' });
      // lantern lines to poles
      [[-16, 6], [16, 6], [-16, -20], [16, -20]].forEach(function (p) {
        k.shape('cyl', [p[0], 5, p[1]], [0.4, 10, 0.4], '#7a1c14');
        for (var i = 1; i < 4; i++) {
          var f = i / 4;
          k.shape('sph', [p[0] * f, 9 - Math.sin(f * 3.14) * 1.5, -8 + (p[1] + 8) * f], [1, 1.3, 1],
                  i % 2 ? '#ff6a2a' : '#e8b84a', { m: 'neon' });
        }
      });
      // terraces of tea up the left
      for (var t2 = 0; t2 < 5; t2++) {
        k.box([-34 - t2 * 3, 0.5 + t2, 0], [8, 1 + t2 * 2, 60], '#5a4430', { st: 1 });
        k.box([-31 - t2 * 3, 1.4 + t2 * 2, 0], [1.2, 1, 58], '#2e6a2a', { st: 1 });
      }
      pedestal(k, -24, 0, 14, RED, RED_NEON);
      k.player(-4, 8, 0.8, { anim: 'run', time: 0.4, holding: flagItem(RED), wear: cap(BLUE) });
      k.player(8, 4, -2.6, { anim: 'run', time: 0.9, wear: cap(RED) });
    }
  });

  // ------------------------------------------------- Meteora
  Thumbs.registerWorld('br_meteora', {
    camera: [[30, 18, 40], [-4, 12, -4], 50],
    sky: { top: '#7aa8d8', horizon: '#f2e2c8', sun: [0.55, 0.18, -0.6], clouds: 0.5, tint: '#fff0d8' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [120, 1, 90], '#6a8a4a', { st: 1 });
      // the monastery pillar and the monastery on it
      k.box([-18, 6, -10], [22, 12, 24], '#8a7a64', { st: 1 });
      k.box([-18, 15, -10], [20, 6, 22], '#a89880', { st: 1 });
      k.box([-18, 20, -10], [12, 4, 10], '#ece6da');
      k.box([-18, 22.4, -10], [13, 0.8, 11], '#b8582e');
      k.shape('sph', [-18, 23.4, -10], [5, 3.6, 5], '#984624');
      // the switchback up its face
      for (var i = 0; i < 6; i++) k.box([-6.4, 1 + i * 2, -18 + i * 3], [2.8, 2 + i * 4, 3], '#bcae96');
      // the hermit's pillar, hut and rope bridge
      k.box([-4, 4, 8], [8, 8, 8], '#a89880', { st: 1 });
      k.box([-4, 9.5, 8], [4, 3, 4], '#ece6da');
      k.box([-4, 11.3, 8], [4.6, 0.6, 4.6], '#b8582e');
      k.box([-10, 8.2, 8], [8, 0.3, 2], '#6a4a2a');
      // St Ezra's in the valley, cypresses
      k.box([18, 3, 4], [12, 6, 10], '#ece6da');
      k.box([18, 6.4, 4], [12.6, 0.8, 10.6], '#b8582e');
      k.shape('sph', [18, 7.6, 4], [5, 3.6, 5], '#984624');
      [[10, 12], [26, -4]].forEach(function (c) { k.shape('cone', [c[0], 5, c[1]], [2, 10, 2], '#2a4a2a'); });
      pedestal(k, -18, 18, -14, RED, RED_NEON);
      k.player(4, 14, 0.6, { anim: 'run', time: 0.4, holding: flagItem(RED), wear: cap(BLUE) });
      k.player(-10, 4, 2.4, { anim: 'idle', time: 0.2, wear: cap(RED) });
    }
  });

  // ------------------------------------------------- Circuit City
  Thumbs.registerWorld('br_circuit', {
    camera: [[30, 18, 40], [0, 6, -4], 50],
    sky: { top: '#05060c', horizon: '#1a2a4a', sun: [0.3, 0.7, 0.4], clouds: 0.1, tint: '#9ab8e8' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [120, 1, 90], '#1f5a3a', { st: 1 });
      // the CPU and its heatsink and fan
      k.box([0, 3, -10], [18, 6, 18], '#3a3e46');
      for (var f = 0; f < 6; f++) k.box([-7.5 + f * 3, 9.5, -10], [0.6, 7, 16], '#b8c0c8', { m: 'metal' });
      k.box([0, 13.3, -10], [18, 0.6, 18], '#2a2e36');
      k.shape('cyl', [0, 13.8, -10], [14, 0.4, 14], '#ff4aaa', { m: 'neon' });
      // capacitors and traces
      [[-16, 6, '#2a4aa8'], [-12, 10, '#22242a'], [14, 8, '#2a4aa8'], [18, 4, '#22242a']].forEach(function (c) {
        k.shape('cyl', [c[0], 4, c[1]], [4, 8, 4], c[2]);
        k.shape('cyl', [c[0], 8.1, c[1]], [3.8, 0.2, 3.8], '#c8ccd2', { m: 'metal' });
      });
      k.box([0, 0.04, 6], [80, 0.08, 0.8], '#ffb05a', { m: 'neon' });
      k.box([-20, 0.05, 0], [0.8, 0.1, 30], '#ffb05a', { m: 'neon' });
      k.box([22, 0.05, -2], [0.8, 0.1, 24], '#ffb05a', { m: 'neon' });
      // RAM sticks and the I/O block
      for (var r = 0; r < 3; r++) k.box([30 + r * 3, 4, -16], [0.6, 7, 18], '#1a3a2a');
      k.box([-34, 6, -6], [14, 12, 20], '#b8c0c8', { m: 'metal' });
      pedestal(k, -26, 0, 12, RED, RED_NEON);
      k.player(4, 10, 0.8, { anim: 'run', time: 0.4, holding: flagItem(RED), wear: cap(BLUE) });
      k.player(-8, 4, 2.6, { anim: 'run', time: 0.1, wear: cap(RED) });
    }
  });

  Thumbs.registerWorld('br_snowglobe', {
    camera: [[0, 22, 44], [0, 9, -2], 50],
    sky: { top: '#3a3048', horizon: '#c89a7a', sun: [0.3, 0.6, 0.5], clouds: 0.2, tint: '#ffe8d0' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [110, 1, 80], '#f2f5f8', { st: 1 });
      // the globe's base curving round the back
      for (var i = -5; i <= 5; i++) {
        var a = i * 0.24;
        k.box([Math.sin(a) * 46, 5, -Math.cos(a) * 30 - 4], [10, 10, 3], '#6a2e22');
        k.box([Math.sin(a) * 46, 10.3, -Math.cos(a) * 30 - 4], [10, 0.6, 3], '#e8c050', { m: 'metal' });
      }
      // the town hall and its clock tower
      k.box([0, 3, -10], [16, 6, 10], '#f2ead8');
      k.box([0, 6.5, -10], [17, 1, 11], '#eef2f6', { st: 1 });
      k.box([0, 11, -10], [5, 9, 5], '#e8d8c0');
      k.shape('cyl', [0, 12, -7.4], [3.4, 0.2, 3.4], '#f4ecd8', { r: [Math.PI / 2, 0, 0] });
      k.shape('cone', [0, 17.5, -10], [6, 4, 6], '#4a5060');
      // a chalet on its hill, its flag before it
      k.box([-30, 1, -6], [26, 2, 24], '#dde4ec', { st: 1 });
      k.box([-30, 3, -6], [20, 2, 18], '#f2f5f8', { st: 1 });
      k.box([-31, 8, -8], [12, 6, 10], '#7a4e2e');
      k.box([-31, 11.6, -8], [14, 1.2, 12], '#eef2f6', { st: 1 });
      pedestal(k, -22, 4, -2, RED, RED_NEON);
      // the carousel
      k.shape('cyl', [14, 0.6, 4], [10, 1.2, 10], '#c8a060');
      k.shape('cone', [14, 8, 4], [11, 3, 11], '#f8f2e8');
      k.shape('cyl', [14, 6.4, 4], [11, 0.8, 11], '#d8322a');
      k.shape('cyl', [14, 3.6, 4], [0.5, 6, 0.5], '#e8c050', { m: 'metal' });
      // the toy train going round
      k.box([-6, 1.2, 10], [3, 2, 5], '#2a6a3a');
      k.box([-6, 3, 8.6], [3, 2, 2], '#c42b20');
      k.box([0, 1.2, 10], [3, 1.6, 4], '#2a6aa8');
      k.box([0, 2.6, 10], [1.6, 1.6, 1.6], '#f2c21e');
      // pines with snow, a snowman
      [[-44, -16], [24, -16], [36, -6], [-14, -20]].forEach(function (p) {
        k.shape('cone', [p[0], 5, p[1]], [6, 8, 6], '#2a5a3a');
        k.shape('cone', [p[0], 8.4, p[1]], [2.4, 2, 2.4], '#ffffff');
      });
      k.shape('sph', [24, 1.4, 10], [3, 2.8, 3], '#ffffff');
      k.shape('sph', [24, 3.6, 10], [2, 2, 2], '#ffffff');
      k.shape('cone', [23.2, 3.7, 10.9], [0.4, 1.4, 0.4], '#e87a2a', { r: [Math.PI / 2, 0, 0] });
      k.player(-8, 2.2, 2, { anim: 'run', time: 0.3, holding: flagItem(RED), wear: cap(BLUE) });
      k.player(8, 0.0, 14, { anim: 'run', time: 0.7, wear: cap(RED) });
    }
  });

  Thumbs.registerWorld('br_bigear', {
    camera: [[22, 20, 46], [0, 10, -4], 50],
    sky: { top: '#04050c', horizon: '#26244a', sun: [-0.35, 0.55, 0.3], clouds: 0.08, tint: '#a8b8ff' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [120, 1, 90], '#b8925e', { st: 1 });
      // the rails, two dishes on their stepped bases, all looking one way
      k.box([0, 0.3, 0], [110, 0.6, 6], '#8a8a84', { st: 1 });
      [[-24, 1], [18, 0.8]].forEach(function (d) {
        var x = d[0], s = d[1];
        k.box([x, 1, 0], [14 * s, 2, 14 * s], '#9a9a94', { st: 1 });
        k.box([x, 3, 0], [9 * s, 2, 9 * s], '#c8c8c0', { st: 1 });
        k.box([x - 3 * s, 8, 0], [1, 8 * s, 2], '#d8dce0', { m: 'metal' });
        k.box([x + 3 * s, 8, 0], [1, 8 * s, 2], '#d8dce0', { m: 'metal' });
        k.shape('cyl', [x, 13 * s + 2, 1.5], [18 * s, 1.0, 18 * s], '#f2f4f6', { r: [-1.0, 0, 0] });
        k.shape('cyl', [x, 13 * s + 2, 1.0], [19 * s, 0.5, 19 * s], '#9aa0a8', { r: [-1.0, 0, 0], m: 'metal' });
        k.shape('cyl', [x, 13 * s + 5.5, 5.2], [1.2, 2, 1.2], '#6a6e74', { r: [-1.0, 0, 0], m: 'metal' });
      });
      // the control building, the Big Ear behind it
      k.box([0, 3, -18], [24, 6, 12], '#c8c8c0');
      k.box([0, 6.5, -18], [25, 1, 13], '#7a7a78', { st: 1 });
      k.shape('cyl', [0, 24, -33], [34, 1.4, 34], '#f2f4f6', { r: [-0.9, 0, 0] });
      k.shape('cyl', [0, 24, -33.6], [36, 0.7, 36], '#9aa0a8', { r: [-0.9, 0, 0], m: 'metal' });
      k.box([0, 10, -34], [8, 20, 8], '#c8c8c0');
      // a saguaro, the light in the sky with its beam
      k.shape('cyl', [34, 6, 6], [2.4, 12, 2.4], '#3a7a3e');
      k.shape('cyl', [36.4, 8, 6], [1.6, 5, 1.6], '#3a7a3e');
      k.shape('sph', [-30, 34, -26], [16, 3.2, 16], '#c8ccd4', { m: 'metal' });
      k.shape('sph', [-30, 36, -26], [6, 4, 6], '#a8f0d8', { m: 'glass', a: 0.5 });
      k.shape('cone', [-30, 18, -26], [12, 30, 12], '#b8fff0', { m: 'neon', a: 0.25, r: [Math.PI, 0, 0] });
      pedestal(k, 30, 0, -6, BLUE, BLUE_NEON);
      k.player(-4, 0.6, 6, { anim: 'run', time: 0.5, holding: flagItem(BLUE), wear: cap(RED) });
      k.player(10, 0.6, 12, { anim: 'run', time: 0.1, wear: cap(BLUE) });
    }
  });

  Thumbs.registerWorld('br_polder', {
    camera: [[26, 20, 46], [0, 12, -6], 50],
    sky: { top: '#4a8ae8', horizon: '#e8f2fa', sun: [0.45, 0.75, 0.35], clouds: 0.75, tint: '#fff8e8' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [120, 1, 90], '#5aa040', { st: 1 });
      // the canal and its white drawbridge
      k.box([14, 0.06, 0], [10, 0.12, 90], '#3a7a9a');
      k.box([14, 0.4, 6], [12, 0.8, 8], '#8a7a6a', { st: 1 });
      [[9, 2.6], [19, 2.6], [9, 9.4], [19, 9.4]].forEach(function (p) { k.box([p[0], 5.5, p[1]], [0.8, 10, 0.8], '#f4f2ea'); });
      k.box([14, 10.6, 2.6], [11, 0.8, 0.8], '#f4f2ea'); k.box([14, 10.6, 9.4], [11, 0.8, 0.8], '#f4f2ea');
      // the dike, the tulips beyond it in their bands
      k.box([26, 1, 0], [8, 2, 90], '#4a8a34', { st: 1 });
      k.box([26, 3, 0], [5, 2, 90], '#5aa040', { st: 1 });
      ['#e8302a', '#f2c21e', '#f07aa8', '#ffffff', '#8a4ac8'].forEach(function (c, i) {
        k.box([40, 0.6, -20 + i * 6], [16, 1.2, 4], c, { st: 1 });
      });
      // the great mill with its sails in the team's colour
      k.box([-26, 3, -12], [14, 6, 14], '#a84a32', { st: 1 });
      k.box([-26, 9, -12], [11, 6, 11], '#3a4a3a');
      k.box([-26, 14, -12], [8, 4, 8], '#4a5a4a');
      k.box([-26, 16.6, -12], [9, 1.4, 9], '#2a3a2a');
      [[0.4], [2.0], [3.55], [5.1]].forEach(function (a) {
        var ang = a[0];
        k.box([-26 + Math.sin(ang) * 7, 17 + Math.cos(ang) * 7, -6.6], [2.4, 14, 0.3], '#e8705e',
              { r: [0, 0, -ang] });
      });
      pedestal(k, -26, 0, 2, RED, RED_NEON);
      k.player(2, 0, 10, { anim: 'run', time: 0.6, holding: flagItem(RED), wear: cap(BLUE) });
      k.player(-10, 0, 14, { anim: 'run', time: 0.2, wear: cap(RED) });
    }
  });

  Thumbs.registerWorld('br_leviathan', {
    camera: [[30, 26, -40], [0, 8, 6], 52],
    sky: { top: '#3a2a5a', horizon: '#ff9a5a', sun: [0.55, 0.16, -0.35], clouds: 0.55, tint: '#ffc8a0' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [140, 1, 110], '#c8a070', { st: 1 });
      // the benches behind, in their strata
      ['#e8d0a0', '#b8603a', '#f0e0b8', '#9a5a3a', '#e0c090'].forEach(function (c, i) {
        k.box([0, 1 + i * 2, 40 + i * 4], [140, 2, 30], c, { st: 1 });
      });
      // the skull: stepped cranium, sockets aglow, jaws open towards us
      for (var i = 0; i < 5; i++) k.box([0, 2 + i * 2, 4 + i * 0.6], [26 - i * 3.6, 2, 20 - i * 2.6], i % 2 ? '#c8b898' : '#e8dcc0', { st: 1 });
      k.box([0, 6, -6.2], [26, 8, 1], '#e8dcc0');
      [-5, 5].forEach(function (x) { k.shape('sph', [x, 7.4, -6.8], [3.4, 2.4, 0.6], '#ff7a2a', { m: 'neon' }); });
      k.box([0, 3.4, -16], [10, 2.4, 20], '#e8dcc0', { st: 1 });
      [-4.2, 4.2].forEach(function (x) {
        for (var t2 = 0; t2 < 5; t2++) k.shape('cone', [x, 1.6, -22 + t2 * 3.4], [1.2, 2.2, 1.2], '#f8f2e2', { r: [Math.PI, 0, 0] });
        k.box([x * 1.2, 0.8, -16], [1.6, 1.6, 20], '#c8b898');
      });
      // the spine and ribs running away from it
      for (var v = 0; v < 6; v++) {
        k.box([0, 5, 16 + v * 5], [3, 2, 3.6], '#e8dcc0', { st: 1 });
        [-1, 1].forEach(function (sx) { k.box([sx * 5, 2.4, 16 + v * 5], [7, 1.2, 1.2], '#e8dcc0', { r: [0, 0, sx * 0.6] }); });
      }
      // a headframe on the rim
      k.box([-40, 18, 44], [1, 16, 1], '#a85a32', { m: 'metal' });
      k.box([-36, 18, 44], [1, 16, 1], '#a85a32', { m: 'metal' });
      k.shape('torus', [-38, 27, 44], [5, 2, 5], '#3a3a40', { r: [0, 0, Math.PI / 2] });
      pedestal(k, 22, 0, -10, BLUE, BLUE_NEON);
      k.player(-12, 0, -22, { anim: 'run', time: 0.3, holding: flagItem(BLUE), wear: cap(RED) });
      k.player(14, 0, -24, { anim: 'run', time: 0.8, wear: cap(BLUE) });
    }
  });

  Thumbs.registerWorld('br_stacks', {
    camera: [[30, 22, 40], [0, 9, -4], 52],
    sky: { top: '#6a8ab8', horizon: '#e8e0d0', sun: [0.3, 0.85, 0.2], clouds: 0.5, tint: '#fff0d8' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [120, 1, 90], '#7a4a2e', { st: 1 });
      // rows of shelves, books on their faces, a catwalk over them
      var BOOK = ['#8a2a2a', '#2a4a8a', '#2a6a3a', '#c89a3a', '#5a2a6a'];
      [-26, -14, 14, 26].forEach(function (x, i) {
        k.box([x, 7, -14], [2.4, 14, 22], '#4a2a16');
        for (var row = 0; row < 4; row++) k.box([x + 1.25, 2 + row * 3.2, -14], [0.1, 2.4, 20], BOOK[(i + row) % 5]);
      });
      k.box([0, 14.3, -14], [60, 0.6, 3], '#6a3e22', { st: 1 });
      // the rotunda behind: its drum, its stepped dome, the globe through the door
      k.box([0, 7, -36], [26, 14, 14], '#e8e0d0');
      k.box([0, 15, -36], [22, 2, 12], '#c8bca8');
      k.box([0, 17, -36], [16, 2, 9], '#e8e0d0');
      k.shape('sph', [0, 6, -28], [8, 8, 8], '#3a6ab8');
      // flying books
      [[-8, 20, 4], [6, 23, -2], [14, 19, 6]].forEach(function (p, i) {
        k.box([p[0] - 1.2, p[1], p[2]], [2.4, 0.2, 3], BOOK[i], { r: [0, 0, 0.5] });
        k.box([p[0] + 1.2, p[1], p[2]], [2.4, 0.2, 3], BOOK[i], { r: [0, 0, -0.5] });
      });
      // the map table with its flag, the nave's runner
      k.box([0, 0.05, 10], [8, 0.1, 40], '#8a2a2a');
      k.box([-22, 1.5, 16], [14, 3, 9], '#4a2a16', { st: 1 });
      pedestal(k, -22, 3, 16, RED, RED_NEON);
      k.player(6, 0, 14, { anim: 'run', time: 0.4, holding: flagItem(RED), wear: cap(BLUE) });
      k.player(-6, 0, 22, { anim: 'run', time: 0.9, wear: cap(RED) });
    }
  });

  Thumbs.registerWorld('br_steamworks', {
    camera: [[28, 26, 44], [0, 6, -4], 52],
    sky: { top: '#2a2a4a', horizon: '#e87a5a', sun: [-0.5, 0.12, 0.4], clouds: 0.45, tint: '#ffb890' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [130, 1, 100], '#5a5560', { st: 1 });
      // the benches stepping up behind, a crack glowing in one
      ['#5a5560', '#4a4550', '#6a6470', '#524c58'].forEach(function (c, i) {
        k.box([0, 1 + i * 2, -26 - i * 5], [130, 2, 20], c, { st: 1 });
      });
      k.box([-10, 4.2, -30.9], [14, 0.4, 0.2], '#ff6a2a', { m: 'neon' });
      // the lake, the island hall, the pipe bridge going up to the rim
      k.box([0, 0.05, 2], [60, 0.1, 30], '#3ac8c8', { m: 'glass', a: 0.85 });
      k.box([0, 4, 2], [18, 8, 12], '#b8bcc0');
      k.box([0, 8.4, 2], [19, 0.8, 13], '#f2c21e');
      k.box([24, 8, 2], [30, 0.8, 4], '#5a6068');
      k.box([24, 9.2, 0.2], [30, 1.6, 0.4], '#f2c21e');
      k.shape('cyl', [24, 7, 3], [1.6, 30, 1.6], '#c8ccd0', { r: [0, 0, Math.PI / 2], m: 'metal' });
      [14, 26, 36].forEach(function (x) { k.box([x, 3.5, 2], [1, 7, 1], '#5a6068'); });
      // a cooling tower with its plume, a geyser going up
      for (var i = 0; i < 6; i++) k.shape('cyl', [-34, 10 + i * 3, -40], [16 - Math.sin(i / 5 * 2.6) * 6, 3, 16 - Math.sin(i / 5 * 2.6) * 6], '#c8c4bc');
      k.shape('sph', [-30, 32, -40], [18, 10, 14], '#f2f2f4', { a: 0.8 });
      k.shape('cyl', [-16, 6, 10], [2.4, 12, 2.4], '#e8fafa', { a: 0.8 });
      k.shape('sph', [-16, 13, 10], [7, 4, 7], '#ffffff', { a: 0.6 });
      pedestal(k, 34, 0, 18, BLUE, BLUE_NEON);
      k.player(-4, 0, 20, { anim: 'run', time: 0.2, holding: flagItem(BLUE), wear: cap(RED) });
      k.player(12, 0, 22, { anim: 'run', time: 0.7, wear: cap(BLUE) });
    }
  });

  Thumbs.registerWorld('br_saddleback', {
    camera: [[0, 22, 60], [0, 16, -10], 55],
    sky: { top: '#04060f', horizon: '#1a2a48', sun: [0.2, 0.6, -0.5], clouds: 0.1, tint: '#a8c8ff' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [140, 1, 100], '#eef2f8', { st: 1 });
      // the twin peaks, stepped, a cliff band in each
      [-1, 1].forEach(function (sx) {
        for (var i = 0; i < 7; i++) {
          var w = 44 - i * 5.5, c = i === 3 ? '#5a6070' : (i % 2 ? '#eef2f8' : '#d4dcea');
          k.box([sx * 38, 1.5 + i * 3, -14], [w, 3, w * 0.9], c, { st: 1 });
        }
        // the dome on top
        k.box([sx * 38, 22.5, -14], [10, 3, 10], '#f2f2ee');
        k.shape('sph', [sx * 38, 24, -14], [10, 8, 10], '#f6f8fa');
        k.box([sx * 38, 26, -9.2], [1.4, 4, 0.6], '#1a1e28');
      });
      // the station in the saddle, the cables up to both domes, a cabin
      k.box([0, 2.5, 0], [16, 5, 10], '#c8ccd0');
      k.box([0, 5.4, 0], [17, 0.8, 11], '#4a5060');
      [-1, 1].forEach(function (sx) {
        k.box([sx * 19, 14, -7], [38, 0.25, 0.25], '#2a2a30', { r: [0, 0, sx * 0.48] });
      });
      k.box([16, 15.6, -7], [3.4, 2.6, 2.6], '#c42b20');
      // the aurora: curtains of thin ribbons, rippling in height and depth
      for (var i = 0; i < 26; i++) {
        var u = i / 25, ax = -70 + u * 140;
        var ay = 44 + Math.sin(u * 7.0) * 5, ah = 9 + 7 * (0.5 + 0.5 * Math.sin(u * 11 + 1.3));
        var ac = ['#5aff9a', '#4ae8c8', '#b06aff'][i % 3 === 2 ? 2 : (u < 0.5 ? 0 : 1)];
        k.box([ax, ay, -70 - Math.cos(u * 5) * 8], [5.6, ah, 0.3], ac, { m: 'neon', a: 0.18 + 0.1 * Math.sin(u * 9) });
      }
      pedestal(k, -16, 0, 14, RED, RED_NEON);
      k.player(6, 0, 16, { anim: 'run', time: 0.5, holding: flagItem(RED), wear: cap(BLUE) });
      k.player(-4, 0, 24, { anim: 'run', time: 0.1, wear: cap(RED) });
    }
  });

  global.RelayThumbs = { flagItem: flagItem, pedestal: pedestal, rain: rain,
                         RED: RED, BLUE: BLUE, RED_NEON: RED_NEON, BLUE_NEON: BLUE_NEON };
})(window);
