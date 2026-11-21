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

  global.RelayThumbs = { flagItem: flagItem, pedestal: pedestal, rain: rain,
                         RED: RED, BLUE: BLUE, RED_NEON: RED_NEON, BLUE_NEON: BLUE_NEON };
})(window);
