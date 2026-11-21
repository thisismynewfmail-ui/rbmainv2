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

  global.RelayThumbs = { flagItem: flagItem, pedestal: pedestal, rain: rain,
                         RED: RED, BLUE: BLUE, RED_NEON: RED_NEON, BLUE_NEON: BLUE_NEON };
})(window);
