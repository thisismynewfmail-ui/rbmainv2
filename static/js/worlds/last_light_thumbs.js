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

  /* Harrow County Fair: up the midway at dusk to the Ferris wheel, the
     carousel turning, the team on top of the hay pyramid -- and the county
     coming out of the corn maze. */
  Thumbs.registerWorld('ll_fair', {
    camera: [[-4, 18, -40], [4, 17, 50], 56],
    sky: { top: '#2a2a5a', horizon: '#e8885a', sun: [-0.5, 0.15, 0.7], clouds: 0.2, tint: '#ffc8a0' },
    build: function (parts, k) {
      k.box([0, -0.5, 30], [220, 1, 220], '#5a7a38', { st: 1 });
      k.box([0, 0.2, 18], [14, 0.4, 100], '#b89a6a', { st: 1 });
      // the Ferris wheel at the end of the midway
      var wx = 6, wy = 36, wz = 74, R = 26;
      for (var lx = -1; lx <= 1; lx += 2) {
        for (var lz = -1; lz <= 1; lz += 2) k.box([wx + lx * 4.8, wy / 2, wz + lz * 3], [1.6, wy, 1.6], '#e8e8e8');
      }
      k.box([wx, wy, wz], [9, 2.4, 8], '#e8e8e8');
      for (var sp = 0; sp < 8; sp++) {
        k.box([wx, wy, wz - 2.6], [2 * R, 0.5, 0.5], '#d8d8d8', { r: [0, 0, sp * Math.PI / 8] });
      }
      var bulbs = ['#ff5a5a', '#ffd84a', '#5ac8ff', '#8aff7a', '#ff8ad8'];
      for (var b = 0; b < 36; b++) {
        var a = b / 36 * Math.PI * 2;
        k.shape('sph', [wx + Math.cos(a) * R, wy + Math.sin(a) * R, wz - 2.6], [1.3, 1.3, 1.3], bulbs[b % 5],
                { m: 'neon' });
        k.shape('sph', [wx + Math.cos(a) * R, wy + Math.sin(a) * R, wz + 2.6], [0.9, 0.9, 0.9], '#c8c8c8');
      }
      for (var g = 0; g < 12; g++) {
        var ag = g / 12 * Math.PI * 2 + 0.13;
        var gx = wx + Math.cos(ag) * R, gy = wy + Math.sin(ag) * R;
        k.box([gx, gy - 1.4, wz], [0.3, 2.8, 0.3], '#5a5f66');
        k.box([gx, gy - 4.2, wz], [3.6, 3.0, 3.8], ['#e83a3a', '#3a7ac8', '#f2c83a', '#5aa86a'][g % 4]);
        k.box([gx, gy - 2.6, wz], [4.0, 0.4, 4.2], '#f2ece0');
      }
      // the midway: booths both sides, striped awnings, the prizes
      var stripes = ['#c43a32', '#3a7ac8', '#e8b83a', '#5aa86a'];
      for (var i = 0; i < 3; i++) {
        var bz = -2 + i * 18;
        for (var side = -1; side <= 1; side += 2) {
          var bx = side * 13;
          k.box([bx + side * 4.5, 4, bz], [1, 8, 14], stripes[(i + side + 4) % 4]);
          k.box([bx - side * 2.5, 1.5, bz], [1.4, 3, 14], '#8a6a48', { st: 1 });
          for (var st = 0; st < 7; st++) {
            k.box([bx, 8.4, bz - 6 + st * 2], [10, 0.5, 2], st % 2 ? '#f2ece0' : stripes[(i + 1 + side + 4) % 4]);
          }
          for (var pz = 0; pz < 4; pz++) {
            k.box([bx + side * 3.4, 5.4, bz - 4.5 + pz * 3], [1.2, 1.4, 1.2], ['#e890b0', '#f2d83a', '#8ad8e8', '#c8a070'][pz]);
          }
        }
      }
      // the strings of lights over the midway
      for (var ln = 0; ln < 3; ln++) {
        var sz = 2 + ln * 18;
        for (var q = 0; q <= 12; q++) {
          var u = q / 12;
          k.shape('sph', [-9 + u * 18, 11.6 - Math.sin(u * Math.PI) * 1.8, sz], [0.6, 0.6, 0.6],
                  ['#fff2a8', '#ffb86a', '#ff8a8a'][(q + ln) % 3], { m: 'neon' });
        }
      }
      // the carousel on the left
      var cx = -32, cz = 34;
      k.shape('cyl', [cx, 0.6, cz], [24, 1.2, 24], '#c8a060');
      k.shape('cyl', [cx, 7, cz], [3, 12, 3], '#e8c83a', { m: 'metal' });
      k.shape('cyl', [cx, 12.6, cz], [27, 1, 27], '#f2ece0');
      k.shape('cone', [cx, 15.6, cz], [28, 5.4, 28], '#e83a3a');
      var horses = ['#f2ece0', '#3a2a1a', '#c8a070', '#8a8a8a'];
      for (var h = 0; h < 8; h++) {
        var ah = h / 8 * Math.PI * 2;
        var hx = cx + Math.cos(ah) * 9, hz = cz + Math.sin(ah) * 9, hy = 3.6 + (h % 2) * 1.2;
        k.shape('cyl', [hx, 6.6, hz], [0.4, 11, 0.4], '#e8c83a', { m: 'metal' });
        k.attach(hx, hy, hz, -ah, [
          { t: 'box', p: [0, 0, 0], s: [1.2, 1.4, 3.4], c: horses[h % 4] },
          { t: 'box', p: [0, 1.4, 1.7], s: [0.9, 2.0, 1.0], c: horses[h % 4] },
          { t: 'box', p: [0, 2.0, 2.3], s: [0.8, 0.8, 1.4], c: horses[h % 4] },
          { t: 'box', p: [0, -1.4, 1.1], s: [0.3, 1.6, 0.3], c: horses[h % 4] },
          { t: 'box', p: [0, -1.4, -1.1], s: [0.3, 1.6, 0.3], c: horses[h % 4] }]);
        k.shape('sph', [cx + Math.cos(ah + 0.4) * 13.2, 12.6, cz + Math.sin(ah + 0.4) * 13.2], [0.7, 0.7, 0.7],
                '#fff2a8', { m: 'neon' });
      }
      // the corn maze beyond it, the infected coming out
      for (var mx = 0; mx < 6; mx++) {
        for (var mz = 0; mz < 3; mz++) {
          if ((mx + mz) % 3 === 1) continue;
          k.box([-74 + mx * 9, 4, 58 + mz * 12], [2, 8, 10], '#7a8a2a', { st: 1 });
        }
      }
      k.horde(12, -60, 50, -40, 16, 0.6, 'fair', 7);
      // the hay pyramid in front on the right, the team on top
      for (var t = 0; t < 4; t++) {
        k.box([31, 1 + t * 2, 16], [16 - t * 3.6, 2, 16 - t * 3.6], t % 2 ? '#c8b060' : '#d8c070', { st: 1 });
      }
      k.survivor(30, 15, -0.5, 0, 8.0);
      k.survivor(33, 18, -0.9, 1, 8.0);
      k.survivor(26, 10, -0.2, 2, 4.0);
      // the county coming down the midway
      k.zombie('common', 1, 8, Math.PI + 0.2, 7, 'fair', 2, 0.4);
      k.zombie('common', -3, 14, Math.PI, 1, 'fair', 0, 0.4);
      k.zombie('common', -2, 22, Math.PI, 5, 'fair', 0, 0.4);
      k.zombie('common', 3, 30, Math.PI, 1, 'fair', 2, 0.4);
      k.zombie('common', -4, 36, Math.PI, 5, 'fair', 0, 0.4);
      k.zombie('common', 2, 42, Math.PI, 3, 'fair', 0, 0.4);
      k.zombie('common', -1, 50, Math.PI, 4, 'fair', 2, 0.4);
      k.zombie('common', 4, 56, Math.PI, 6, 'fair', 0, 0.4);
      k.zombie('common', -3, 60, Math.PI, 2, 'fair', 0, 0.4);
      // the grain elevator off to the right, the tree line
      for (var si = 0; si < 3; si++) k.shape('cyl', [60 + si * 10, 14, 110], [10, 28, 10], '#c8c4b8');
      k.box([70, 28.6, 110], [32, 1.2, 12], '#8a8f94');
      k.box([70, 20, 104.6], [16, 3, 0.4], '#a83a2a');
      for (var tr = 0; tr < 9; tr++) k.pine(-90 + tr * 22, 130, 2.2 + (tr % 3) * 0.3, '#2a3a24');
    }
  });

  /* Redwater Cranberry Bogs: across the flooded bog by moonlight, the
     water solid red with berries inside the booms, a water reel churning,
     the infected wading in; the screenhouse lit on the right, the windmill
     on its knoll on the left, the team on the near dike. */
  Thumbs.registerWorld('ll_bogs', {
    camera: [[2, 17, -40], [0, 3, 46], 56],
    sky: { top: '#070b1c', horizon: '#4a2c48', sun: [0.2, 0.35, 0.9], clouds: 0.2, tint: '#b8c0e8' },
    build: function (parts, k) {
      k.box([0, -1.5, 40], [240, 1, 240], '#3a2a22');
      // the bog: red to the far dike
      k.box([0, -0.2, 34], [130, 0.8, 76], '#a01a2a', { st: 1 });
      // the dikes round it, raised
      k.box([0, 0.6, -10], [240, 2.4, 16], '#4a5a34', { st: 1 });
      k.box([0, 0.6, 80], [240, 2.4, 16], '#4a5a34', { st: 1 });
      k.box([73, 0.6, 34], [16, 2.4, 76], '#4a5a34', { st: 1 });
      k.box([-73, 0.6, 34], [16, 2.4, 76], '#4a5a34', { st: 1 });
      k.box([0, 1.85, -10], [240, 0.1, 6], '#7a6a4e');
      k.box([0, 1.85, 80], [240, 0.1, 6], '#7a6a4e');
      // the booms: a corral on the right, the berries packed inside it
      k.box([-30, 0.45, 20], [1.2, 0.6, 30], '#f2a81a');
      k.box([-47.5, 0.45, 5.4], [34, 0.6, 1.2], '#f2a81a');
      k.box([-47.5, 0.45, 34.6], [34, 0.6, 1.2], '#f2a81a');
      for (var b = 0; b < 40; b++) {
        k.shape('sph', [-34 - (b % 8) * 3.6, 0.35, 8 + Math.floor(b / 8) * 5.6], [1.4, 0.9, 1.4], b % 3 ? '#c81a2e' : '#e83a4a');
      }
      // a water reel, its paddles
      k.box([10, 1.2, 40], [8, 2.6, 6], '#c8a83a');
      k.box([8, 3.4, 40], [3, 1.8, 3], '#4a5057');
      k.shape('cyl', [16, 1.2, 40], [1.2, 6.6, 1.2], '#5a5f66', { r: [Math.PI / 2, 0, 0] });
      for (var pd = 0; pd < 4; pd++) {
        k.box([16 + Math.cos(pd * Math.PI / 2 + 0.4) * 2.4, 1.2 + Math.sin(pd * Math.PI / 2 + 0.4) * 2.4, 40], [0.4, 0.4, 6.2], '#c8a83a');
      }
      for (var sp = 0; sp < 6; sp++) k.shape('sph', [19 + sp * 0.9, 1.6 + Math.sin(sp * 0.6) * 2.2, 37 + sp * 1.1], [0.6, 0.6, 0.6], '#e83a4a');
      // the heron standing in it
      k.box([36, 2.2, 54], [0.2, 3.6, 0.2], '#6a5a3a');
      k.box([36, 4.6, 54], [1.0, 1.0, 2.2], '#7a8aa0');
      k.box([36, 6.0, 55.2], [0.3, 2.0, 0.3], '#c8ccd4');
      k.box([36, 7.0, 55.8], [0.4, 0.4, 0.7], '#e8e8ee');
      k.box([36, 6.9, 56.6], [0.14, 0.14, 1.0], '#e8c83a');
      // the infected wading in, the berries round their knees
      k.zombie('common', 0, 14, Math.PI, 2, 'bogs', 0, -1.6);
      k.zombie('common', -10, 22, Math.PI + 0.2, 6, 'bogs', 2, -1.6);
      k.zombie('common', 14, 26, Math.PI - 0.2, 1, 'bogs', 0, -1.6);
      k.zombie('common', -4, 34, Math.PI, 4, 'bogs', 0, -1.6);
      k.zombie('common', 24, 46, Math.PI, 5, 'bogs', 2, -1.6);
      k.zombie('common', -16, 50, Math.PI, 3, 'bogs', 0, -1.6);
      k.zombie('common', 6, 60, Math.PI, 7, 'bogs', 0, -1.6);
      // the team on the near dike
      k.survivor(-8, -8, 0.2, 0, 1.8);
      k.survivor(4, -6, -0.1, 1, 1.8);
      k.survivor(14, -9, -0.4, 2, 1.8);
      // lamps along the far dike
      for (var lp = 0; lp < 4; lp++) {
        var lx = -60 + lp * 40;
        k.box([lx, 7, 74], [0.8, 12, 0.8], '#3a3a3a');
        k.box([lx, 13.2, 74], [2.2, 0.6, 2.2], '#ffcf7a', { m: 'neon' });
      }
      // the screenhouse on the right
      k.box([-62, 8.2, 100], [44, 14, 22], '#8a8a82');
      for (var t = 0; t < 4; t++) k.box([-62, 15.8 + t * 1.6, 100], [46, 1.6, 22 - t * 5.2], '#4a4a48');
      for (var w = 0; w < 5; w++) k.box([-80 + w * 8, 7, 88.9], [3.4, 3.4, 0.2], '#ffcf7a', { m: 'neon' });
      k.box([-62, 24.4, 100], [5, 4, 5], '#f2ece0');
      // the windmill on its knoll on the left
      k.box([64, 1.2, 112], [36, 2.4, 30], '#4a5a34', { st: 1 });
      k.box([64, 3.6, 112], [26, 2.4, 22], '#55663e', { st: 1 });
      k.box([64, 15.8, 112], [12, 22, 12], '#8a8a82');
      for (var g = 0; g < 3; g++) k.box([64, 27.6 + g * 1.4, 112], [13 - g * 3.6, 1.4, 13], '#4a4a48');
      for (var sl = 0; sl < 4; sl++) {
        k.box([64, 22, 105.4], [22, 1.0, 0.3], '#4a3a2a', { r: [0, 0, Math.PI / 4 + sl * Math.PI / 2] });
      }
      k.box([64, 22, 105.6], [3, 3, 0.6], '#3a2a1a');
      for (var tr = 0; tr < 10; tr++) k.pine(-110 + tr * 24, 132 + (tr % 2) * 6, 2.4 + (tr % 3) * 0.3, '#1e2a1e');
    }
  });

  /* Kettle Falls Mill: down the gorge at dusk -- the brick mill on the far
     cliff with its windows lit and the wheel turning under it, the falls
     on the left, the covered bridge, the infected wading the river and the
     team up on the near bank. */
  Thumbs.registerWorld('ll_mill', {
    camera: [[6, 30, -34], [0, -8, 44], 60],
    sky: { top: '#2e2e4e', horizon: '#d8885a', sun: [-0.7, 0.15, 0.6], clouds: 0.5, tint: '#ffc8a0' },
    build: function (parts, k) {
      // the river at the bottom of the gorge, the cliffs either side
      k.box([0, -18.5, 30], [240, 1, 240], '#3a3a34');
      k.box([0, -16.2, 30], [240, 0.6, 52], '#2a4a5a', { a: 0.85 });
      k.box([0, -9, 70], [240, 18, 36], '#5a5650', { st: 1 });
      k.box([0, -9, -10], [240, 18, 24], '#5a5650', { st: 1 });
      k.box([0, 0.3, 70], [240, 0.6, 36], '#5a6a34', { st: 1 });
      k.box([0, 0.3, -10], [240, 0.6, 24], '#5a6a34', { st: 1 });
      // the mill on the far cliff
      k.box([-6, 14.6, 68], [76, 28, 28], '#9a4f3a');
      k.box([-6, 29.2, 68], [78, 1.2, 30], '#4a4a48');
      for (var row = 0; row < 2; row++) {
        for (var c = 0; c < 9; c++) {
          k.box([-40 + c * 8.4, 6.5 + row * 14, 53.9], [3.6, 5, 0.2], '#ffcf7a', { m: 'neon' });
        }
      }
      for (var p = 0; p < 4; p++) k.box([-6 + (p % 2 ? 4 : -4), 35, 68 + (p > 1 ? 4 : -4)], [0.8, 10, 0.8], '#e8e0cc');
      k.box([-6, 40.4, 68], [11, 0.8, 11], '#4a4a48');
      k.box([-6, 41.6, 68], [7, 1.6, 7], '#4a4a48');
      k.box([40, 26, 76], [5, 52, 5], '#7c3d2d');
      for (var sm = 0; sm < 4; sm++) k.shape('sph', [40 + sm * 4, 54 + sm * 5, 76], [5 + sm * 2, 5 + sm * 2, 5 + sm * 2], '#6a6866', { a: 0.5 });
      // the wheel under it
      var wx = -18, wy = -9, wz = 51;
      k.shape('cyl', [wx, wy, wz], [2, 6, 2], '#3a3a3a', { r: [Math.PI / 2, 0, 0] });
      for (var b = 0; b < 12; b++) {
        var a = b / 12 * Math.PI * 2;
        k.box([wx + Math.cos(a) * 6.4, wy + Math.sin(a) * 6.4, wz], [1.4, 1.4, 4.6], '#6a5a42');
      }
      for (var s2 = 0; s2 < 6; s2++) k.box([wx, wy, wz], [12.8, 0.4, 0.4], '#4a3a2a', { r: [0, 0, s2 * Math.PI / 6] });
      k.box([wx - 20, -3.2, 53], [34, 0.6, 4], '#7a5335');
      // the falls on the left
      k.box([62, -8, 30], [10, 22, 52], '#8a8478', { st: 1 });
      for (var f = 0; f < 6; f++) k.box([56.6, -8.5, 10 + f * 7], [0.6, 15, 6.8], '#cfe6f2', { a: 0.7 });
      for (var m = 0; m < 6; m++) k.shape('sph', [50 - m, -15, 12 + m * 6], [5, 3, 5], '#f2f6f8', { a: 0.5 });
      // the covered bridge on the right
      k.box([-60, -0.5, 30], [16, 1.2, 60], '#7a5335');
      k.box([-67.4, 5, 30], [1.2, 10, 60], '#8a2a24');
      k.box([-52.6, 5, 30], [1.2, 10, 60], '#8a2a24');
      for (var g = 0; g < 3; g++) k.box([-60, 10.6 + g * 1.4, 30], [18 - g * 5, 1.4, 62], '#4a4a48');
      for (var pr = 0; pr < 2; pr++) k.box([-60, -9.4, 20 + pr * 20], [18, 17.6, 5], '#8a8478');
      // the infected in the river, the team on the near bank
      k.zombie('common', 4, 22, Math.PI, 1, 'mill', 0, -17.8);
      k.zombie('common', -8, 30, Math.PI + 0.2, 2, 'mill', 2, -17.8);
      k.zombie('common', 16, 34, Math.PI - 0.3, 5, 'mill', 0, -17.8);
      k.zombie('common', -20, 40, Math.PI, 3, 'mill', 0, -17.8);
      k.zombie('common', 26, 44, Math.PI, 7, 'mill', 2, -17.8);
      k.zombie('common', 8, 46, Math.PI, 6, 'mill', 0, -17.8);
      k.zombie('common', -60, 26, Math.PI, 4, 'mill', 0, 0.6);
      k.zombie('common', -60, 42, Math.PI, 2, 'mill', 0, 0.6);
      k.survivor(-6, -6, 0.1, 0, 0.6);
      k.survivor(6, -8, -0.2, 1, 0.6);
      k.survivor(16, -4, -0.5, 2, 0.6);
      // maples along the far bank
      var cols = ['#c8582a', '#d8a02a', '#a83a24', '#e8c84a'];
      for (var tr = 0; tr < 8; tr++) k.tree(-110 + tr * 30, 96 + (tr % 2) * 8, 1.8 + (tr % 3) * 0.3, cols[tr % 4]);
    }
  });

  /* Launch Complex 9: up the crawlerway at night to the moon rocket on its
     pad, the orange tower beside it and searchlights on it; the service
     structure rolled back, the infected coming up the crawlerway, the team
     on top of the structure. */
  Thumbs.registerWorld('ll_launchpad', {
    camera: [[-44, 34, -62], [0, 24, 60], 58],
    sky: { top: '#04081a', horizon: '#1a2a4a', sun: [0.3, 0.6, 0.6], clouds: 0.1, tint: '#a8b8e8' },
    build: function (parts, k) {
      k.box([0, -0.5, 30], [260, 1, 260], '#5a6a3a', { st: 1 });
      k.box([-9, 0.15, -10], [10, 0.3, 130], '#9a968a', { st: 1 });
      k.box([9, 0.15, -10], [10, 0.3, 130], '#9a968a', { st: 1 });
      for (var t = 0; t < 3; t++) k.box([0, 1 + t * 2, 70], [90 - t * 20, 2, 70 - t * 16], t % 2 ? '#b6bcc1' : '#9aa0a6', { st: 1 });
      // the rocket
      var y = 14;
      [[6, 6.6, '#eef0f2'], [6, 6.6, '#1a1c20'], [14, 6.6, '#eef0f2'], [2, 6.8, '#1a1c20'], [10, 6.3, '#eef0f2'],
       [6, 6.3, '#1a1c20'], [4, 6.3, '#eef0f2'], [8, 4.4, '#eef0f2'], [4, 4.4, '#1a1c20']].forEach(function (s) {
        k.shape('cyl', [0, y + s[0] / 2, 70], [s[1] * 2, s[0], s[1] * 2], s[2]);
        y += s[0];
      });
      k.shape('cone', [0, y + 3, 70], [8, 6, 8], '#eef0f2');
      k.box([0, y + 10, 70], [0.8, 8, 0.8], '#e8682a');
      k.box([0, 12, 70], [24, 4, 24], '#4a5058');
      // the tower
      for (var lx = 0; lx < 2; lx++) for (var lz = 0; lz < 2; lz++) k.box([23 + lx * 10, 45, 65 + lz * 10], [1.6, 78, 1.6], '#e8682a');
      k.box([28, 85, 70], [20, 1.2, 20], '#e8682a');
      for (var a = 0; a < 3; a++) k.box([14, 30 + a * 20, 70], [16, 1.2, 2.4], '#8a8f94');
      k.shape('sph', [28, 87, 70], [1.6, 1.6, 1.6], '#ff2a2a', { m: 'neon' });
      // searchlight beams
      for (var b = 0; b < 3; b++) k.box([-30 + b * 30, 40, 40], [2.6, 2.6, 90], '#e8f0ff', { m: 'neon', a: 0.08, r: [0.6, (b - 1) * 0.3, 0] });
      // the service structure, rolled back, the team on top
      k.box([0, 10, -10], [40, 0.6, 24], '#8a8f94', { st: 1 });
      k.box([0, 20, -16], [40, 0.6, 12], '#8a8f94', { st: 1 });
      k.box([-10, 30, -16], [20, 0.6, 12], '#8a8f94', { st: 1 });
      for (var p = 0; p < 4; p++) k.box([p % 2 ? 19.4 : -19.4, 5, p < 2 ? -21.4 : 1.4], [1.2, 10, 1.2], '#c8382a');
      for (var q = 0; q < 2; q++) k.box([q ? 19.4 : -19.4, 15, -21.4], [1.2, 10, 1.2], '#c8382a');
      k.box([-19.4, 25, -21.4], [1.2, 10, 1.2], '#c8382a');
      k.survivor(-12, -18, 0.3, 0, 30.3);
      k.survivor(-6, -14, 0.1, 1, 30.3);
      k.survivor(8, -16, -0.2, 2, 20.3);
      // the crew coming up the crawlerway
      k.zombie('common', -6, 18, 0, 1, 'launchpad', 0, 0.3);
      k.zombie('common', 8, 22, 0, 2, 'launchpad', 2, 0.3);
      k.zombie('common', -10, 28, 0, 3, 'launchpad', 0, 0.3);
      k.zombie('common', 4, 30, 0, 5, 'launchpad', 0, 2.3);
      k.zombie('common', 12, 16, -0.3, 4, 'launchpad', 2, 0.3);
      k.zombie('common', -2, 40, 0, 6, 'launchpad', 0, 2.3);
      // the blockhouse dome off to the side
      k.box([-70, 6, -40], [50, 12, 40], '#9aa0a6');
      for (var d2 = 0; d2 < 4; d2++) k.box([-70, 13.2 + d2 * 2, -40], [42 - d2 * 8, 2, 32 - d2 * 8], '#b6bcc1');
    }
  });

  /* The Underneath: down the great cistern under the vault, pillars in
     rows standing in black water, a catwalk down the middle with its
     lamps, the infected wading in, the team on the catwalk. */
  Thumbs.registerWorld('ll_cistern', {
    camera: [[0, 12, -50], [0, 6, 40], 62],
    sky: { top: '#05060a', horizon: '#14161c', sun: [0.2, 0.9, 0.3], clouds: 0, tint: '#8a9ab8' },
    build: function (parts, k) {
      k.box([0, -4.5, 30], [200, 1, 220], '#2a2a24');
      k.box([0, -1.9, 30], [200, 0.8, 220], '#1a2a2a', { a: 0.85 });
      k.box([0, 41, 30], [200, 2, 220], '#4a2a22');
      for (var row = 0; row < 6; row++) {
        for (var sd = -1; sd <= 1; sd += 2) {
          for (var c = 0; c < 2; c++) {
            var x = sd * (14 + c * 26), z = -20 + row * 26;
            k.box([x, 18, z], [6, 44, 6], '#6a3a2e');
            k.box([x, 38.5, z], [8, 3, 8], '#4a2a22');
          }
        }
      }
      k.box([0, 0.8, 30], [6, 0.4, 200], '#7a5335', { st: 1 });
      for (var p2 = 0; p2 < 10; p2++) {
        k.box([-2.6, -1.6, -40 + p2 * 18], [0.8, 4.8, 0.8], '#543923');
        k.box([2.6, -1.6, -40 + p2 * 18], [0.8, 4.8, 0.8], '#543923');
      }
      for (var l = 0; l < 6; l++) {
        k.box([0, 34, -10 + l * 24], [0.1, 12, 0.1], '#2a2a2a');
        k.shape('sph', [0, 27.6, -10 + l * 24], [1.2, 1.2, 1.2], '#ffe8a8', { m: 'neon' });
      }
      k.zombie('common', -9, 16, Math.PI, 1, 'cistern', 0, -3.6);
      k.zombie('common', 8, 26, Math.PI + 0.3, 2, 'cistern', 2, -3.6);
      k.zombie('common', -6, 38, Math.PI, 4, 'cistern', 0, -3.6);
      k.zombie('common', 10, 48, Math.PI, 5, 'cistern', 0, -3.6);
      k.zombie('common', -12, 58, Math.PI, 3, 'cistern', 2, -3.6);
      k.zombie('common', 0, 20, Math.PI, 7, 'cistern', 0, 1.0);
      k.survivor(-1, -14, 0.1, 0, 1.0);
      k.survivor(1.5, -20, -0.1, 1, 1.0);
      k.box([-34, 20, 70], [12, 40, 0.5], '#e8eccf', { m: 'neon', a: 0.08 });
    }
  });

  /* Rooftops of Harrow Heights: over the snowy roofs of the block -- the
     penthouse, the water tower, the billboard lit across the alley, the
     towers behind; the team on the brick roof, the infected coming over
     the planks. */
  Thumbs.registerWorld('ll_rooftops', {
    camera: [[24, 52, 26], [-40, 38, -46], 60],
    sky: { top: '#0a0e1e', horizon: '#3a3a52', sun: [0.2, 0.5, -0.6], clouds: 0.6, tint: '#c8d0f0' },
    build: function (parts, k) {
      k.box([0, -0.5, 0], [260, 1, 260], '#5a5e66');
      var blocks = [[-46, 39, 80, 66, 30, '#9a4f3a'], [46, 39, 80, 66, 26, '#8a6a52'], [-46, -39, 80, 66, 34, '#5a5e6a'],
                    [46, -39, 80, 66, 22, '#7a5a4a']];
      blocks.forEach(function (bl) {
        k.box([bl[0], bl[4] / 2 - 0.2, bl[1]], [bl[2], bl[4] - 0.4, bl[3]], bl[5]);
        k.box([bl[0], bl[4] - 0.2, bl[1]], [bl[2], 0.4, bl[3]], '#eef2f6', { st: 1 });
        for (var w = 0; w < 8; w++) {
          if ((w * 7 + bl[4]) % 3 === 0) continue;
          k.box([bl[0] - bl[2] / 2 + 6 + w * 9, 6 + (w % 3) * 7, bl[1] + bl[3] / 2 + 0.1], [3, 3, 0.2], '#ffd27a', { m: 'neon' });
        }
      });
      // the penthouse
      k.box([-51, 36, 41], [50, 12, 38], '#e8e8e0');
      k.box([-51, 36, 22.1], [44, 8, 0.4], '#8fb8c8', { a: 0.5 });
      k.box([-51, 42.6, 41], [52, 1.2, 40], '#3a3a42');
      // the billboard, lit
      for (var l = 0; l < 3; l++) k.box([-70 + l * 24, 46, -47], [1.2, 24, 1.2], '#4a5057');
      k.box([-46, 50, -51], [56, 16, 1.2], '#1a2a4a');
      k.box([-46, 54, -50.2], [40, 4, 0.2], '#ff5a7a', { m: 'neon' });
      k.box([-64, 47, -50.2], [3, 8, 0.2], '#e8f4ff', { m: 'neon', r: [0, 0, -0.9] });
      // the water tower
      for (var lg = 0; lg < 4; lg++) k.box([66 + (lg % 2) * 8, 31, 56 + (lg > 1 ? 8 : 0)], [1, 10, 1], '#543923');
      k.shape('cyl', [70, 42, 60], [12, 12, 12], '#8a6a4a');
      k.shape('cone', [70, 50, 60], [13, 4, 13], '#5a4a3a');
      // planks across the alleys
      k.box([0, 29.7, 63], [12, 0.6, 6], '#7a5335', { st: 1 });
      k.box([0, 27.7, -37], [12, 0.6, 6], '#7a5335', { st: 1 });
      // the towers behind
      for (var t2 = 0; t2 < 6; t2++) k.box([-120 + t2 * 48, 45, -130], [36, 90 + (t2 % 3) * 16, 30], '#262a34');
      // the team on the brick roof, them coming over
      k.survivor(20, -20, -2.4, 0, 22);
      k.survivor(28, -28, -2.6, 1, 22);
      k.survivor(14, -30, -2.2, 2, 22);
      k.zombie('common', -2, -37, Math.PI / 2, 2, 'rooftops', 0, 28.0);
      k.zombie('common', -24, -30, 0.6, 3, 'rooftops', 2, 34);
      k.zombie('common', -40, -24, 0.5, 1, 'rooftops', 0, 34);
      k.zombie('common', -56, -34, 0.3, 5, 'rooftops', 0, 34);
      k.zombie('common', -70, -20, 0.4, 6, 'rooftops', 2, 34);
      k.zombie('common', -30, -12, 0.8, 7, 'rooftops', 0, 34);
      for (var sn = 0; sn < 40; sn++) k.shape('sph', [-100 + (sn * 37) % 200, 10 + (sn * 13) % 60, -80 + (sn * 53) % 160], [0.5, 0.5, 0.5], '#ffffff');
    }
  });

  /* Glasshouse Gardens: across the topiary garden to the Palm House lit
     up under its dome; hedge animals, the fountain, the infected coming
     between them, the team by the fountain. */
  Thumbs.registerWorld('ll_gardens', {
    camera: [[-30, 22, -70], [10, 14, 70], 58],
    sky: { top: '#081018', horizon: '#2a3a3a', sun: [-0.3, 0.55, 0.6], clouds: 0.3, tint: '#a8c8c0' },
    build: function (parts, k) {
      k.box([0, -0.5, 30], [260, 1, 260], '#3a6a32', { st: 1 });
      k.box([0, 0.15, 0], [12, 0.3, 200], '#b8ac94', { st: 1 });
      // the Palm House
      k.box([0, 12, 110], [180, 24, 100], '#c8ffd0', { a: 0.3 });
      for (var m = 0; m < 10; m++) k.box([-90 + m * 20, 12, 60], [1, 24, 1], '#e8ece8');
      k.box([0, 24.3, 110], [182, 0.6, 102], '#c8ffd0', { a: 0.35 });
      for (var d = 0; d < 4; d++) k.box([0, 26 + d * 4, 110], [80 - d * 16, 4, 60 - d * 16], '#c8ffd0', { a: 0.35 });
      k.shape('sph', [0, 20, 110], [60, 30, 40], '#d8ffc8', { m: 'neon', a: 0.12 });
      for (var p = 0; p < 4; p++) {
        var px = -30 + p * 20;
        k.shape('cyl', [px, 8, 110], [1.6, 16, 1.6], '#7a6a4a');
        k.shape('sph', [px, 17, 110], [8, 3, 8], '#2a6a2a');
      }
      // the topiary and the fountain
      k.box([-30, 4, -10], [5, 5, 9], '#2a5a26');
      k.box([-30, 5.6, -4.4], [3.6, 3.6, 2.2], '#2a5a26');
      k.box([30, 3.5, -10], [5, 7, 4], '#2a5a26');
      k.box([30, 8.6, -10], [3.6, 3.2, 3.2], '#2a5a26');
      k.box([-30, 9.6, 14], [1.4, 6, 1.4], '#2a5a26');
      k.box([-30, 5, 12], [3.4, 3.4, 6], '#2a5a26');
      k.box([-30, 13.2, 14.8], [1.8, 1.4, 2.8], '#2a5a26');
      k.shape('cyl', [0, 0.6, 0], [16, 1.2, 16], '#9a9488');
      k.box([0, 1.9, 0], [12, 0.6, 12], '#3a7a8a', { a: 0.8 });
      k.shape('cyl', [0, 4, 0], [2, 6, 2], '#9a9488');
      for (var h = 0; h < 4; h++) k.box([-56 + h * 37.4, 1.4, 22], [26, 2.8, 2], '#2a5a26', { st: 1 });
      // the infected between the hedges, the team at the fountain
      k.zombie('common', -12, 30, Math.PI, 4, 'gardens', 0, 0);
      k.zombie('common', 14, 36, Math.PI + 0.3, 5, 'gardens', 2, 0);
      k.zombie('common', 40, 20, -2.4, 1, 'gardens', 0, 0);
      k.zombie('common', -44, 26, 2.6, 3, 'gardens', 0, 0);
      k.zombie('common', 4, 46, Math.PI, 7, 'gardens', 0, 0);
      k.survivor(-6, -14, 0.1, 0, 0);
      k.survivor(6, -18, -0.2, 1, 0);
      k.survivor(-14, -20, 0.4, 2, 0);
      for (var f = 0; f < 18; f++) k.shape('sph', [-60 + (f * 37) % 120, 4 + (f * 7) % 10, -20 + (f * 29) % 60], [0.5, 0.5, 0.5], '#d8ff6a', { m: 'neon' });
    }
  });

  Thumbs.registerWorld('ll_fireworks', {
    camera: [[46, 26, -40], [-6, 22, 60], 60],
    sky: { top: '#070a1c', horizon: '#3a2238', sun: [0.3, 0.42, 0.7], clouds: 0.25, tint: '#d0b8d8' },
    build: function (parts, k) {
      k.box([0, -0.5, 30], [280, 1, 280], '#4a5a30', { st: 1 });
      k.box([0, 0.15, 20], [80, 0.3, 84], '#b6bcc1', { st: 1 });
      // the giant rocket on its fins, the gantry beside it
      k.box([0, 0.5, 56], [22, 1, 22], '#b6bcc1', { st: 1 });
      k.shape('cyl', [0, 23, 56], [9, 32, 9], '#b8282a');
      [13, 25, 35].forEach(function (y) { k.shape('cyl', [0, y, 56], [9.4, 2, 9.4], '#e8b83a'); });
      k.shape('cone', [0, 44, 56], [9.6, 10, 9.6], '#e8b83a');
      k.box([7.5, 5, 56], [6, 8, 1.2], '#e8b83a'); k.box([-7.5, 5, 56], [6, 8, 1.2], '#e8b83a');
      k.box([0, 5, 48.5], [1.2, 8, 6], '#e8b83a'); k.box([0, 5, 63.5], [1.2, 8, 6], '#e8b83a');
      k.box([-19, 9.7, 56], [14, 0.6, 24], '#6f767d', { st: 1 });
      k.box([-19, 19.7, 52], [14, 0.6, 16], '#6f767d', { st: 1 });
      for (var l = 0; l < 4; l++) k.box([-25.6 + (l % 2) * 13.2, 9.8, 44.4 + Math.floor(l / 2) * 23.2], [0.8, 19.6, 0.8], '#4a5057');
      // mortar racks and the bursts over them
      for (var r = 0; r < 4; r++) {
        var x = -36 + r * 24;
        k.box([x, 0.5, 96], [12, 1, 5], '#543923');
        for (var tb = 0; tb < 5; tb++) k.shape('cyl', [x - 4.4 + tb * 2.2, 2.6, 96], [1.6, 3.2, 1.6], '#2a2c2a');
      }
      var bursts = [[-30, 62, 120, '#ff4a4a'], [24, 74, 130, '#4a9aff'], [6, 54, 104, '#ffd84a']];
      bursts.forEach(function (b) {
        for (var i = 0; i < 22; i++) {
          var yv = 1 - (i + 0.5) / 22 * 2, rr = Math.sqrt(1 - yv * yv), th = i * 2.4;
          k.shape('sph', [b[0] + Math.cos(th) * rr * 12, b[1] + yv * 12, b[2] + Math.sin(th) * rr * 12], [0.9, 0.9, 0.9], b[3], { m: 'neon' });
        }
      });
      // the dead coming through the racks, the team at the rocket's foot
      k.zombie('common', -14, 84, Math.PI, 1, 'fireworks', 0, 0);
      k.zombie('common', 10, 88, Math.PI + 0.3, 4, 'fireworks', 2, 0);
      k.zombie('common', 26, 78, -2.6, 7, 'fireworks', 0, 0);
      k.zombie('common', -30, 76, 2.7, 5, 'fireworks', 0, 0);
      k.survivor(6, 30, 0.1, 0, 0.3);
      k.survivor(16, 26, -0.3, 1, 0.3);
      k.survivor(-4, 24, 0.4, 2, 0.3);
    }
  });

  Thumbs.registerWorld('ll_mount', {
    camera: [[-70, 40, -120], [0, 28, 70], 58],
    sky: { top: '#0a1018', horizon: '#3a4a58', sun: [-0.4, 0.3, 0.8], clouds: 0.6, tint: '#b8c8d0' },
    build: function (parts, k) {
      k.box([0, -0.5, 30], [300, 1, 300], '#c8b48a', { st: 1 });
      k.box([0, 0.4, 30], [300, 0.1, 300], '#3a6a7a', { a: 0.45 });
      k.box([0, 1, -115], [16, 2, 142], '#8a8478', { st: 1 });
      // the rock in its terraces
      k.box([0, 2, 58], [220, 4, 212], '#6a6a66', { st: 1 });
      k.box([0, 7, 60], [184, 6, 180], '#9a9488', { st: 1 });
      k.box([0, 13.5, 73], [140, 7, 126], '#9a9488', { st: 1 });
      k.box([0, 20.5, 77], [92, 7, 94], '#a49c8c', { st: 1 });
      k.box([0, 8, -45], [220, 8, 6], '#8a8a84');
      for (var c = 0; c < 18; c++) k.box([-102 + c * 12, 13, -47.4], [3, 2, 1.2], '#8a8a84');
      // houses, the inn
      [[-50, -13, 68, 34], [-56, 24, 22, 12], [-25, 24, 26, 12], [23, 24, 22, 12], [73, -11, 30, 30]].forEach(function (h, i) {
        var y = i === 0 || i === 4 ? 10 : 17;
        k.box([h[0] + (i === 0 ? 40 : 0), y + 6, h[1]], [h[2], 12, h[3]], ['#e8e0cc', '#d8c0a0', '#c8d0c8', '#e8e0cc', '#d8c8a8'][i]);
        k.box([h[0] + (i === 0 ? 40 : 0), y + 13, h[1]], [h[2] + 1, 2, h[3] * 0.6], '#3a4048');
      });
      // the abbey church and its spire, the saint in gold
      k.box([0, 35, 85], [28, 22, 66], '#a49c8c');
      k.box([0, 48, 85], [24, 4, 66], '#3a4048');
      k.box([0, 52, 85], [12, 4, 66], '#3a4048');
      k.box([0, 60, 85], [5, 13, 6], '#a49c8c');
      k.shape('cone', [0, 75, 85], [3.4, 10, 3.4], '#3a4048');
      k.shape('sph', [0, 81, 85], [1.2, 1.2, 1.2], '#e8c35a', { m: 'neon' });
      for (var w = 0; w < 4; w++) k.box([-14.1, 36, 63 + w * 14], [0.1, 12, 6], ['#1a3a8a', '#8a1a2a', '#c8a03a', '#2a6a3a'][w], { m: 'neon', a: 0.8 });
      // them on the sands and the causeway, the team at the gate
      k.zombie('common', -24, -90, 0.2, 4, 'mount', 0, 0);
      k.zombie('common', 30, -110, -0.3, 1, 'mount', 2, 0);
      k.zombie('common', -60, -70, 0.6, 5, 'mount', 0, 0);
      k.zombie('common', 2, -130, 0, 2, 'mount', 0, 2);
      k.survivor(-4, -52, Math.PI, 0, 2);
      k.survivor(5, -54, Math.PI + 0.2, 1, 2);
    }
  });

  global.LastLightThumbs = true;
})(window);
