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

  /* Harrow County Zoo: the sea lion arena with the horde lured down into
     its pool, the team firing from the top of the seats, the monorail on
     its stilts behind with the stalled train, and a giraffe looking over. */
  Thumbs.registerWorld('ll_zoo', {
    camera: [[30, 30, -60], [0, 8, 26], 54],
    sky: { top: '#3a4a8a', horizon: '#f2a868', sun: [0.6, 0.22, 0.7], clouds: 0.3, tint: '#ffd0a0' },
    build: function (parts, k) {
      k.box([0, -0.5, 10], [200, 1, 200], '#5a7a3a', { st: 1 });
      // the arena: steps of seats down to the pool
      k.box([0, -3, 10], [64, 6, 34], '#a8b4b8');
      k.box([0, -1.4, -10.5], [64, 2.8, 7], '#4a7aa8', { st: 1 });
      k.box([0, -0.5, -15.5], [64, 1.0, 5], '#e8e2d4', { st: 1 });
      k.box([-29, -1.4, 10], [6, 2.8, 34], '#4a7aa8', { st: 1 });
      k.box([29, -1.4, 10], [6, 2.8, 34], '#4a7aa8', { st: 1 });
      k.box([0, -4.0, 14], [40, 0.4, 18], '#2f7aa8', { m: 'glass', a: 0.8 });
      k.box([0, 3, 28], [70, 12, 3], '#3a6a9a');
      k.box([0, 9.4, 28], [72, 1, 4], '#f2f2f2');
      k.box([0, -2.4, 14], [6, 3, 4], '#9a8a72', { st: 1 });
      k.box([0, 0.4, 14], [1.6, 2.6, 2.2], '#4a3a2e');
      k.shape('sph', [0.2, 2.6, 15], [1.4, 1.4, 1.4], '#e83a3a');
      k.horde(8, -14, 8, 12, 18, Math.PI, 'zoo', 5);
      k.zombie('brute', -6, 20, Math.PI + 0.3, 0, 'zoo', 10, -4);
      k.survivor(-14, -16, 0.1, 0, 0);
      k.survivor(-6, -18, 0, 1, 0);
      k.survivor(6, -17, -0.1, 2, 0);
      k.survivor(15, -15, -0.2, 3, 0);
      // the monorail behind: stilts, the deck, the train
      for (var x = -60; x <= 60; x += 24) k.box([x, 8, 44], [2.4, 16, 2.4], '#b8bcc0');
      k.box([0, 16.6, 44], [140, 1.2, 7], '#d8dcd8', { st: 1 });
      k.box([-14, 20.5, 44], [26, 6.6, 6], '#f2f2f2');
      k.box([14, 20.5, 44], [26, 6.6, 6], '#f2f2f2');
      k.box([0, 21.0, 40.9], [52, 2, 0.2], '#8fb8c8', { m: 'glass', a: 0.7 });
      k.box([0, 24.0, 44], [54, 0.6, 6.4], '#3a7a4a');
      k.box([0, 18.6, 40.9], [52, 0.6, 0.2], '#3a7a4a');
      // the giraffe looking over it
      var gx = -40, gz = 30, G = 1.5;
      [[-1, 1.6], [1, 1.6], [-1, -1.6], [1, -1.6]].forEach(function (l) {
        k.box([gx + l[0] * G, 4 * G, gz + l[1] * G], [0.7 * G, 8 * G, 0.7 * G], '#e8b858');
      });
      k.box([gx, 9 * G, gz], [2.8 * G, 2.8 * G, 5.2 * G], '#e8b858');
      k.box([gx, 15.5 * G, gz - 2.4 * G], [1.1 * G, 11 * G, 1.2 * G], '#e8b858', { r: [-0.25, 0, 0] });
      k.box([gx, 21 * G, gz - 4.4 * G], [1.2 * G, 1.2 * G, 2.6 * G], '#e8b858');
      k.box([gx + 0.3 * G, 22 * G, gz - 4.0 * G], [0.2 * G, 0.8 * G, 0.2 * G], '#8a5a2a');
      k.box([gx - 0.3 * G, 22 * G, gz - 4.0 * G], [0.2 * G, 0.8 * G, 0.2 * G], '#8a5a2a');
      [[1.42, 0.4, 1.2], [-1.42, -0.3, -0.8], [1.42, -0.5, -1.6], [-1.42, 0.6, 1.6]].forEach(function (p) {
        k.box([gx + p[0] * G, (9 + p[1]) * G, gz + p[2] * G], [0.06 * G, 0.8 * G, 1.0 * G], '#8a5a2a');
      });
      // trees round it
      k.tree(-60, 40, 1.4); k.tree(64, 30, 1.2); k.tree(-46, 62, 1.6); k.tree(70, 70, 1.3);
    }
  });

  /* Harrow Point Aquarium: inside the shark tunnel -- the glass all
     round, the sharks going over, the team at this end and the infected
     coming down it from the other. */
  Thumbs.registerWorld('ll_aquarium', {
    camera: [[-2.6, 7.4, -40], [1, 6.4, 30], 60],
    sky: { top: '#0a2a4a', horizon: '#1a5a7a', sun: [0.2, 0.8, 0.2], clouds: 0, tint: '#7ad8f8' },
    build: function (parts, k) {
      k.box([0, -0.5, 10], [120, 1, 160], '#c8b48a', { st: 1 });
      // the tank's walls far off, its water, its floor
      k.box([0, 14, 70], [120, 30, 2], '#1a3a5a');
      k.box([-50, 14, 10], [2, 30, 120], '#1a3a5a');
      k.box([50, 14, 10], [2, 30, 120], '#1a3a5a');
      k.box([0, 28, 10], [100, 0.4, 120], '#3a8ac8', { m: 'glass', a: 0.5 });
      for (var r = 0; r < 6; r++) k.shape('sph', [-30 + r * 13, 0.8, 20 + (r * 17) % 40], [5, 3, 4], '#5a5a5a');
      // the tunnel: floor, glass walls and roof, ribs
      k.box([0, 0.4, 10], [8, 0.8, 120], '#5a6a7a', { st: 1 });
      k.box([-4.2, 4.4, 10], [0.4, 7.2, 120], '#3a8ac8', { m: 'glass', a: 0.32 });
      k.box([4.2, 4.4, 10], [0.4, 7.2, 120], '#3a8ac8', { m: 'glass', a: 0.32 });
      k.box([0, 8.2, 10], [8.8, 0.4, 120], '#3a8ac8', { m: 'glass', a: 0.32 });
      for (var z = -20; z <= 60; z += 12) {
        k.box([-4.6, 4.4, z], [0.4, 7.6, 1.2], '#3a4a5a', { m: 'metal' });
        k.box([4.6, 4.4, z], [0.4, 7.6, 1.2], '#3a4a5a', { m: 'metal' });
        k.box([0, 8.6, z], [9.6, 0.4, 1.2], '#3a4a5a', { m: 'metal' });
      }
      // the sharks over it
      [[-1, 11.4, 2, 0.4], [6, 14, 18, -0.6], [-9, 10.6, 26, 0.9]].forEach(function (sh) {
        var c = Math.cos(sh[3]), s = Math.sin(sh[3]);
        k.box([sh[0], sh[1], sh[2]], [2, 2, 7], '#6a7a8a', { r: [0, sh[3], 0] });
        k.box([sh[0], sh[1] - 0.6, sh[2]], [1.7, 0.9, 6], '#e8ecee', { r: [0, sh[3], 0] });
        k.box([sh[0] - s * 0.2, sh[1] + 1.8, sh[2] - c * 0.2], [0.3, 2, 1.6], '#6a7a8a', { r: [-0.4, sh[3], 0] });
        k.box([sh[0] - s * 4.4, sh[1] + 0.4, sh[2] - c * 4.4], [0.3, 3, 1.2], '#6a7a8a', { r: [0.3, sh[3], 0] });
      });
      // the team at this end, the infected coming down the tunnel
      k.survivor(-1.6, -8, 0.05, 0, 0.8);
      k.survivor(1.8, -10, -0.1, 1, 0.8);
      k.horde(6, 0, 24, 0, 44, Math.PI, 'aquarium', 4);
      k.zombie('spitter', 1.4, 20, Math.PI, 0, 'aquarium', 11, 0.8);
      k.box([0, 7.9, -6], [6, 0.3, 1.4], '#9fe8ff', { m: 'neon' });
    }
  });

  /* Silver Screen Studios: the western street, one front cut away to
     show the team in the gallery behind its windows, the cast coming
     down the dirt in costume, the water tower over the lot. */
  Thumbs.registerWorld('ll_backlot', {
    camera: [[4, 24, -42], [-2, 5, 30], 56],
    sky: { top: '#050814', horizon: '#2a2a4a', sun: [0.4, 0.5, 0.6], clouds: 0.15, tint: '#a8a8e0' },
    build: function (parts, k) {
      k.box([0, -0.5, 20], [180, 1, 180], '#4a6438', { st: 1 });
      k.box([0, 0.2, 20], [24, 0.4, 140], '#a8865a', { st: 1 });
      var cols = ['#a8784a', '#c89a6a', '#8a5a3a', '#b88a5a'];
      for (var i = 0; i < 4; i++) {
        var z = -8 + i * 26;
        // the left side: fronts, a board walk; the nearest cut away
        k.box([-15, 0.6, z], [6, 1.2, 22], '#7a5335', { st: 1 });
        if (i > 0) k.box([-18.5, 10, z], [1, 20, 22], cols[i]);
        k.box([-18.5, 21.2, z], [1, 2.4, 13], cols[i]);
        k.box([-24, 8.6, z], [10, 0.8, 22], '#a07a52', { st: 1 });
        k.box([-28.6, 4, z - 9], [0.8, 8.2, 0.8], '#543923');
        k.box([-28.6, 4, z + 9], [0.8, 8.2, 0.8], '#543923');
        // the right side
        k.box([15, 0.6, z], [6, 1.2, 22], '#7a5335', { st: 1 });
        k.box([18.5, 10, z], [1, 20, 22], cols[(i + 2) % 4]);
        k.box([18.5, 21.2, z], [1, 2.4, 13], cols[(i + 2) % 4]);
        k.box([18.0, 11.6, z - 5], [0.2, 3.8, 4.4], '#1a1208');
        k.box([18.0, 11.6, z + 5], [0.2, 3.8, 4.4], '#1a1208');
      }
      // the team in the gallery behind the cut-away front
      k.survivor(-22, -10, 1.3, 0, 9.0);
      k.survivor(-23, -3, 1.1, 1, 9.0);
      k.survivor(-14, -12, 0.8, 2, 1.2);
      // the cast coming down the street
      k.zombie('common', -3, 14, Math.PI, 1, 'backlot', 2, 0.4);
      k.zombie('common', 4, 20, Math.PI, 2, 'backlot', 0, 0.4);
      k.zombie('common', -1, 28, Math.PI, 4, 'backlot', 2, 0.4);
      k.zombie('common', 6, 34, Math.PI, 3, 'backlot', 0, 0.4);
      k.zombie('common', -5, 40, Math.PI, 5, 'backlot', 2, 0.4);
      k.zombie('common', 2, 46, Math.PI, 6, 'backlot', 0, 0.4);
      // the stagecoach, the water tower beyond
      k.box([8, 4.4, 4], [5.6, 5.6, 11], '#3a1a1a', { st: 1 });
      k.box([8, 7.6, 4], [6, 0.8, 11.4], '#2a1a12');
      for (var lg = -1; lg <= 1; lg += 2) k.box([-30 + lg * 5, 18, 84], [1.2, 36, 1.2], '#5a5f66');
      k.shape('cyl', [-30, 40, 84], [16, 10, 16], '#c8c8c0');
      k.shape('cone', [-30, 47, 84], [17, 4, 17], '#5a5f66');
      k.box([-30, 40, 75.9], [10, 2.4, 0.2], '#1a3a6a');
    }
  });

  global.LastLightThumbs = true;
})(window);
