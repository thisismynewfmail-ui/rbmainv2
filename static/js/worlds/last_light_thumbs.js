/* Last Light's newer places, as the world page shows them: each a corner
   of the place at its hour, a horde coming at a handful of survivors.
   (The first four are static/js/ui/thumbs.js's own.)  Each is registered as
   'll_<place id>' with Thumbs.registerWorld; k.zombie, k.horde and
   k.survivor draw the infected in the place's own clothes and the team. */
(function (global) {
  'use strict';
  var Thumbs = global.Thumbs;
  if (!Thumbs || !Thumbs.registerWorld) return;

  // (each new place's diorama goes here)

  /* Starlite Drive-In: the picture on, the giant on it; rows of cars
     under it, the horde coming between them out of the corn, and the team
     up on the snack bar's roof by the projection booth. */
  Thumbs.registerWorld('ll_drivein', {
    camera: [[16, 24, -46], [-2, 12, 34], 54],
    sky: { top: '#03061a', horizon: '#2a3060', sun: [0.3, 0.5, 0.6], clouds: 0.1, tint: '#9aa8e8' },
    build: function (parts, k) {
      k.box([0, -0.5, 20], [200, 1, 200], '#3f5a34', { st: 1 });
      k.box([0, 0.15, 24], [130, 0.3, 80], '#6e6a60', { st: 1 });
      var colours = ['#7ac8c8', '#e8a0b0', '#f0e0a0', '#c83a3a', '#3a5a8a', '#f2f2f2'];
      [4, 22, 40].forEach(function (z, row) {
        k.box([0, 0.75, z], [120, 1.2, 8], '#3a3d42', { st: 1 });
        for (var x = -56; x <= 56; x += 14) {
          k.box([x + 7, 3.5, z], [0.5, 4.6, 0.5], '#8a8f94', { m: 'metal' });
          k.box([x + 7, 6.0, z], [1.6, 1.0, 1.0], '#5a5f66');
          if ((x / 14 + row) % 3 === 0) continue;
          var c = colours[(x / 14 + row * 3 + 9) % colours.length];
          k.box([x, 2.6, z], [4.6, 2.4, 9.4], c, { m: 'metal' });
          k.box([x, 4.4, z - 0.8], [4.0, 1.4, 4.6], '#2b3a44', { m: 'metal' });
        }
      });
      // the screen, lit, the giant on it
      k.box([0, 28, 70], [96, 40, 2], '#14161c');
      k.box([0, 29, 68.9], [88, 32, 0.2], '#a8b8f0', { m: 'neon' });
      for (var b = 0; b < 10; b++) {
        k.box([-40 + b * 9, 15 + (b * 7) % 7, 68.7], [6, 4 + (b * 7) % 11, 0.2], '#0c0e14', { m: 'neon' });
      }
      k.box([10, 28, 68.6], [8, 10, 0.2], '#0c0e14', { m: 'neon' });
      k.box([10, 36.5, 68.6], [5.4, 5.4, 0.2], '#0c0e14', { m: 'neon' });
      k.box([4, 29, 68.6], [2.6, 9, 0.2], '#0c0e14', { m: 'neon', r: [0, 0, 0.5] });
      k.box([16, 29, 68.6], [2.6, 9, 0.2], '#0c0e14', { m: 'neon', r: [0, 0, -0.5] });
      k.box([8.4, 19.5, 68.6], [2.6, 8, 0.2], '#0c0e14', { m: 'neon' });
      k.box([11.6, 19.5, 68.6], [2.6, 8, 0.2], '#0c0e14', { m: 'neon' });
      k.box([8.8, 37.2, 68.5], [1.2, 0.9, 0.2], '#ff3a2a', { m: 'neon' });
      k.box([11.2, 37.2, 68.5], [1.2, 0.9, 0.2], '#ff3a2a', { m: 'neon' });
      for (var leg = -40; leg <= 40; leg += 20) k.box([leg, 4, 71], [1.2, 8, 1.2], '#2a2d33');
      // the snack bar on the left, the booth on its roof, the team up there
      k.box([-34, 6, -16], [30, 12, 18], '#f2efe6', { st: 1 });
      k.box([-34, 10.6, -6.9], [30, 1.2, 0.2], '#c43a32');
      k.box([-34, 12.5, -16], [31, 1, 19], '#3a3d42', { st: 1 });
      k.box([-38, 16.5, -18], [12, 7, 9], '#d8d4c8');
      k.box([-38, 17, -13.4], [5, 2.2, 0.2], '#ffe8a0', { m: 'neon' });
      k.box([-38, 20.5, -18], [13, 1, 10], '#3a3d42');
      k.box([0, 19, 26], [2.4, 2.4, 86], '#d8e8ff', { m: 'neon', a: 0.1, r: [-0.1, 0.42, 0] });
      k.survivor(-26, -9, -0.5, 0, 13);
      k.survivor(-22, -12, -0.4, 1, 13);
      k.survivor(-30, -8, -0.3, 2, 13);
      k.survivor(-20, -16, -0.7, 3, 13);
      // the horde between the cars, out of the corn
      k.horde(8, 40, 30, 8, 12, Math.PI + 0.8, 'drivein', 3);
      k.horde(6, 30, 14, 2, -2, Math.PI + 0.6, 'drivein', 8);
      k.zombie('bloater', 20, 10, Math.PI + 0.7, 0, 'drivein', 0);
      k.zombie('common', 6, 0, Math.PI + 0.9, 3, 'drivein', 2);
      for (var cx = 62; cx <= 82; cx += 5) {
        k.box([cx, 6, 30], [2.4, 12, 80], '#6f8a2a', { st: 1 });
      }
    }
  });

  global.LastLightThumbs = true;
})(window);
