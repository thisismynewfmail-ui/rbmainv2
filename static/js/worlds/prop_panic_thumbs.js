/* Prop Panic's world-page pictures: the card and a diorama of each of the
   four places, built from the same blocks the game draws with
   (Thumbs.registerWorld; loaded by thumbs.js the first time one is asked
   for).  Every player wears the classic default -- yellow skin, red torso,
   blue legs; the seekers carry a prop popper and a headband, and the
   hiders are the furniture with a pair of googly eyes giving them away. */
(function (global) {
  'use strict';
  var Thumbs = global.Thumbs;
  if (!Thumbs || !Thumbs.registerWorld) return;

  var PINK = '#e85a7a', GOLD = '#f2c230', BLUE = '#3a8ad8', WOOD = '#7a5335', WOOD_DARK = '#543923';

  var POPPER = { data: { parts: [
    { t: 'box', p: [0, 0, 0.5], s: [0.4, 0.5, 1.4], c: BLUE },
    { t: 'cyl', p: [0, 0.05, 1.3], s: [0.34, 0.5, 0.34], c: GOLD, r: [Math.PI / 2, 0, 0] },
    { t: 'sph', p: [0, 0.38, 0.3], s: [0.4, 0.4, 0.4], c: '#f07aa8' }] } };

  function band(colour) {
    return [{ t: 'box', p: [0, 5.3, 0], s: [2.32, 0.5, 2.32], c: colour },
            { t: 'box', p: [0.9, 5.3, -1.3], s: [0.3, 0.9, 0.6], c: colour }];
  }

  function seeker(k, x, z, yaw, o) {
    o = o || {};
    k.player(x, z, yaw, { anim: o.anim || 'walk', time: o.time || 0.3, holding: POPPER,
                          pitch: o.pitch || 0, wear: band(o.band || '#3a8ad8'), y: o.y || 0 });
  }

  /* googly eyes on the front of something, ``h`` up, ``front`` out */
  function eyes(h, front, gap) {
    gap = gap || 0.4;
    return [{ t: 'sph', p: [-gap, h, front], s: [0.5, 0.5, 0.2], c: '#ffffff' },
            { t: 'sph', p: [gap, h, front], s: [0.5, 0.5, 0.2], c: '#ffffff' },
            { t: 'sph', p: [-gap + 0.08, h - 0.05, front + 0.1], s: [0.22, 0.22, 0.1], c: '#1a1a1a' },
            { t: 'sph', p: [gap + 0.08, h - 0.05, front + 0.1], s: [0.22, 0.22, 0.1], c: '#1a1a1a' }];
  }

  // --------------------------------------------------------- props
  var P = {
    armchair: function (c) {
      return [{ t: 'box', p: [0, 0.8, 0.1], s: [2.0, 0.9, 2.2], c: c || '#b0606e' },
              { t: 'rbox', p: [0, 1.45, 0.25], s: [1.9, 0.5, 1.9], c: '#efe3c8' },
              { t: 'box', p: [-1.2, 1.3, 0.05], s: [0.4, 1.9, 2.3], c: c || '#b0606e' },
              { t: 'box', p: [1.2, 1.3, 0.05], s: [0.4, 1.9, 2.3], c: c || '#b0606e' },
              { t: 'rbox', p: [0, 2.3, -0.95], s: [2.0, 2.2, 0.5], c: c || '#b0606e' }];
    },
    lamp: function () {
      return [{ t: 'cyl', p: [0, 0.1, 0], s: [1.2, 0.2, 1.2], c: '#c89a3a' },
              { t: 'cyl', p: [0, 2.0, 0], s: [0.2, 3.6, 0.2], c: '#c89a3a' },
              { t: 'cone', p: [0, 4.5, 0], s: [1.6, 1.4, 1.6], c: '#efe3c8' },
              { t: 'sph', p: [0, 3.9, 0], s: [0.5, 0.4, 0.5], c: '#ffe2a8', m: 'neon' }];
    },
    plant: function () {
      return [{ t: 'cyl', p: [0, 0.55, 0], s: [1.3, 1.1, 1.3], c: '#c0663a' },
              { t: 'sph', p: [0, 2.1, 0], s: [1.8, 1.75, 1.8], c: '#4a8a3a' }];
    },
    teapot: function () {
      return [{ t: 'sph', p: [0, 0.5, 0], s: [1.1, 1.0, 1.1], c: '#f2f0ea' },
              { t: 'cyl', p: [0, 1.05, 0], s: [0.42, 0.2, 0.42], c: PINK },
              { t: 'box', p: [0.62, 0.44, 0], s: [0.36, 0.18, 0.2], c: '#f2f0ea' }];
    },
    clock: function () {
      return [{ t: 'box', p: [0, 0.25, 0], s: [1.8, 0.5, 1.2], c: WOOD_DARK },
              { t: 'box', p: [0, 2.3, 0], s: [1.4, 3.6, 0.9], c: '#7a3a24' },
              { t: 'box', p: [0, 4.95, 0], s: [1.7, 1.7, 1.1], c: '#7a3a24' },
              { t: 'cyl', p: [0, 4.95, 0.56], s: [1.2, 1.2, 0.06], c: '#efe3c8', r: [Math.PI / 2, 0, 0] },
              { t: 'box', p: [0, 6.0, 0], s: [1.8, 0.3, 1.2], c: WOOD_DARK }];
    },
    table: function () {
      return [{ t: 'box', p: [0, 2.1, 0], s: [2.0, 0.2, 2.0], c: WOOD },
              { t: 'box', p: [-0.8, 1.0, -0.8], s: [0.22, 2.0, 0.22], c: WOOD_DARK },
              { t: 'box', p: [0.8, 1.0, -0.8], s: [0.22, 2.0, 0.22], c: WOOD_DARK },
              { t: 'box', p: [-0.8, 1.0, 0.8], s: [0.22, 2.0, 0.22], c: WOOD_DARK },
              { t: 'box', p: [0.8, 1.0, 0.8], s: [0.22, 2.0, 0.22], c: WOOD_DARK }];
    },
    gnome: function () {
      return [{ t: 'cyl', p: [0, 0.55, 0], s: [0.8, 0.7, 0.8], c: '#2f6ad0' },
              { t: 'sph', p: [0, 1.05, 0], s: [0.8, 0.5, 0.7], c: '#d8402a' },
              { t: 'sph', p: [0, 1.24, 0.18], s: [0.5, 0.48, 0.42], c: '#f2c8a0' },
              { t: 'sph', p: [0, 1.06, 0.22], s: [0.44, 0.42, 0.3], c: '#ffffff' },
              { t: 'cone', p: [0, 1.78, 0], s: [0.66, 0.8, 0.66], c: '#d8402a' }];
    },
    teddy: function () {
      return [{ t: 'sph', p: [0, 0.85, -0.15], s: [1.7, 1.7, 1.4], c: '#a87a4a' },
              { t: 'sph', p: [0, 2.1, 0], s: [1.2, 1.15, 1.1], c: '#a87a4a' },
              { t: 'sph', p: [0, 2.0, 0.48], s: [0.5, 0.4, 0.3], c: '#d8b088' },
              { t: 'sph', p: [-0.5, 2.7, 0], s: [0.42, 0.42, 0.3], c: '#a87a4a' },
              { t: 'sph', p: [0.5, 2.7, 0], s: [0.42, 0.42, 0.3], c: '#a87a4a' },
              { t: 'box', p: [0, 1.47, 0.32], s: [0.8, 0.18, 0.5], c: '#d8402a' }];
    },
    block: function (c, letter) {
      return [{ t: 'box', p: [0, 0.9, 0], s: [1.8, 1.8, 1.8], c: c,
                dec: 't~' + (letter || 'A') + '~' + c + '~#ffffff~1.00' }];
    },
    horse: function () {
      return [{ t: 'box', p: [-0.45, 0.12, 0], s: [0.2, 0.25, 3.5], c: WOOD_DARK },
              { t: 'box', p: [0.45, 0.12, 0], s: [0.2, 0.25, 3.5], c: WOOD_DARK },
              { t: 'rbox', p: [0, 1.8, 0], s: [0.9, 0.9, 2.3], c: '#ffffff' },
              { t: 'rbox', p: [0, 2.6, 1.05], s: [0.7, 1.2, 0.6], c: '#ffffff' },
              { t: 'rbox', p: [0, 2.95, 1.35], s: [0.6, 0.55, 0.9], c: '#ffffff' },
              { t: 'box', p: [0, 2.3, 0.05], s: [0.94, 0.12, 0.7], c: '#d8402a' },
              { t: 'box', p: [-0.4, 0.8, 0.9], s: [0.18, 1.1, 0.18], c: WOOD },
              { t: 'box', p: [0.4, 0.8, -0.9], s: [0.18, 1.1, 0.18], c: WOOD }];
    },
    duck: function () {
      return [{ t: 'sph', p: [0, 0.5, -0.15], s: [1.5, 1.0, 1.6], c: GOLD },
              { t: 'sph', p: [0, 1.17, 0.45], s: [0.9, 0.85, 0.85], c: GOLD },
              { t: 'box', p: [0, 1.09, 0.85], s: [0.5, 0.18, 0.3], c: '#f08a2a' }];
    },
    ball: function () {
      return [{ t: 'sph', p: [0, 0.9, 0], s: [1.8, 1.8, 1.8], c: '#ffffff', dec: 'sp_rainbow_gores', dw: 1 }];
    },
    cereal: function (c) {
      return [{ t: 'box', p: [0, 1.0, 0], s: [1.4, 2.0, 0.6], c: c || '#f08a2a',
                dec: "t~CRUNCH O's~" + (c || '#f08a2a') + '~#5a2a0a~0.70' }];
    },
    soda: function () {
      return [{ t: 'cyl', p: [0, 0.8, 0], s: [0.85, 1.6, 0.85], c: '#c82a2a', dec: 'cola', dw: 1 },
              { t: 'cone', p: [0, 1.9, 0], s: [0.84, 0.6, 0.84], c: '#c82a2a' },
              { t: 'cyl', p: [0, 2.4, 0], s: [0.34, 0.3, 0.34], c: '#ffffff' }];
    },
    trolley: function () {
      return [{ t: 'box', p: [0, 0.42, 0], s: [1.6, 0.12, 2.6], c: '#b8bcc2', m: 'metal' },
              { t: 'box', p: [0, 2.2, 0.15], s: [1.9, 1.3, 2.9], c: '#c8ccd0', m: 'metal', dec: 'netting' },
              { t: 'box', p: [0, 2.94, -1.35], s: [1.9, 0.12, 0.12], c: '#d8402a' },
              { t: 'box', p: [-0.7, 1.0, 1.2], s: [0.1, 1.1, 0.1], c: '#b8bcc2' },
              { t: 'box', p: [0.7, 1.0, 1.2], s: [0.1, 1.1, 0.1], c: '#b8bcc2' },
              { t: 'box', p: [-0.7, 1.0, -1.2], s: [0.1, 1.1, 0.1], c: '#b8bcc2' },
              { t: 'box', p: [0.7, 1.0, -1.2], s: [0.1, 1.1, 0.1], c: '#b8bcc2' }];
    },
    bust: function () {
      return [{ t: 'box', p: [0, 1.2, 0], s: [1.0, 1.8, 1.0], c: '#e8e4dc' },
              { t: 'box', p: [0, 2.2, 0], s: [1.3, 0.2, 1.3], c: '#a89a88' },
              { t: 'sph', p: [0, 2.6, 0], s: [1.2, 0.6, 0.8], c: '#e8e4dc' },
              { t: 'sph', p: [0, 3.1, 0], s: [0.7, 0.85, 0.75], c: '#e8e4dc' }];
    },
    armour: function () {
      var s = '#b8bcc2';
      return [{ t: 'box', p: [0, 0.15, 0], s: [1.8, 0.3, 1.4], c: '#a89a88' },
              { t: 'box', p: [-0.32, 1.35, 0], s: [0.5, 2.1, 0.6], c: s, m: 'metal' },
              { t: 'box', p: [0.32, 1.35, 0], s: [0.5, 2.1, 0.6], c: s, m: 'metal' },
              { t: 'box', p: [0, 3.25, 0], s: [1.3, 1.7, 0.85], c: s, m: 'metal' },
              { t: 'box', p: [-0.82, 2.95, 0], s: [0.32, 1.3, 0.36], c: s, m: 'metal' },
              { t: 'box', p: [0.82, 2.95, 0], s: [0.32, 1.3, 0.36], c: s, m: 'metal' },
              { t: 'box', p: [0, 4.55, 0], s: [0.8, 0.9, 0.8], c: s, m: 'metal' },
              { t: 'box', p: [0, 4.51, 0.41], s: [0.6, 0.12, 0.04], c: '#1a1a1a' },
              { t: 'cone', p: [0, 5.3, 0], s: [0.5, 0.6, 0.5], c: s, m: 'metal' },
              { t: 'box', p: [0, 5.8, 0], s: [0.1, 0.4, 0.5], c: '#d8402a' }];
    },
    urn: function () {
      return [{ t: 'cyl', p: [0, 0.15, 0], s: [0.8, 0.3, 0.8], c: '#a8743a', m: 'metal' },
              { t: 'sph', p: [0, 1.0, 0], s: [1.5, 1.6, 1.5], c: '#a8743a', m: 'metal' },
              { t: 'cyl', p: [0, 1.95, 0], s: [0.6, 0.5, 0.6], c: '#a8743a', m: 'metal' },
              { t: 'cyl', p: [0, 2.3, 0], s: [0.9, 0.2, 0.9], c: '#d8b040', m: 'metal' }];
    }
  };

  function put(k, name, x, z, yaw, arg, arg2, y) {
    k.attach(x, y || 0, z, yaw || 0, P[name](arg, arg2));
  }

  /* a hider: the prop with eyes on it */
  function hider(k, name, x, z, yaw, eyeH, front, arg, y) {
    k.attach(x, y || 0, z, yaw || 0, P[name](arg).concat(eyes(eyeH, front)));
  }

  function room(k, w, d, floor, wall, side) {
    k.box([0, -0.25, 0], [w, 0.5, d], floor);
    k.box([0, 7, -d / 2 - 0.3], [w, 14, 0.6], wall);
    k.box([-w / 2 - 0.3, 7, 0], [0.6, 14, d], side || wall);
  }

  // ------------------------------------------------------------ card
  Thumbs.registerWorld('prop_panic', {
    sky: { top: '#f0b8a8', horizon: '#ffe8c8', sun: [0.4, 0.7, 0.5], clouds: 0.2, tint: '#fff2dc' },
    camera: [[16, 11, 24], [-1, 3, -2], 44],
    build: function (parts, k) {
      room(k, 44, 30, '#8a5a3a', '#c8d8b8', '#d8c0d0');
      k.box([0, 0.03, -2], [16, 0.06, 11], '#8a3a3a', { dec: 'paisley', dw: 1 });
      // the fireplace on the back wall
      k.box([-4, 3.5, -14.6], [8, 7, 0.8], '#9a4f3a', { dec: 'bricks' });
      k.box([-4, 2.2, -14.1], [4.4, 3.8, 0.2], '#2a1e1a');
      k.box([-4, 7.2, -14.3], [9, 0.5, 1.6], WOOD_DARK);
      k.shape('cone', [-4, 1.4, -14.0], [1.6, 1.8, 0.8], '#ff8a2a', { m: 'neon' });
      k.box([8, 6, -14.7], [6.6, 4.6, 0.3], '#d8b040');
      k.box([8, 6, -14.5], [6, 4, 0.1], '#ffffff', { dec: 'portrait' });
      put(k, 'clock', -18, -12, 0);
      put(k, 'armchair', -10, -5, 0.6, '#b0606e');
      put(k, 'armchair', 3, -6, -0.5, '#6a8a5a');
      put(k, 'table', -3, -9, 0);
      put(k, 'teapot', -3, -9, 0.4, null, null, 2.2);
      put(k, 'plant', 14, -12, 0);
      put(k, 'plant', -19, 2, 0);
      // the hider: the lamp has eyes
      hider(k, 'lamp', -14, -8, 0.5, 4.4, 0.75);
      // a seeker pops the wrong armchair
      seeker(k, 9, 4, -2.3, { anim: 'idle', pitch: -0.1 });
      k.box([5.2, 4.0, -0.6], [0.3, 0.3, 7.6], '#ffd23a', { m: 'neon', a: 0.8, r: [0, -0.65, 0] });
      k.player(-8, 6, 2.6, { anim: 'idle', time: 0.2, holding: null, wear: band('#d8402a') });
    }
  });

  // ------------------------------------------------- Grandma's Cottage
  Thumbs.registerWorld('pp_grandma', {
    sky: { top: '#5f9fdc', horizon: '#dcefff', sun: [0.45, 0.78, 0.3], clouds: 0.55, tint: '#fff2dc' },
    camera: [[24, 20, 52], [0, 6, -6], 44],
    build: function (parts, k) {
      k.box([0, -0.5, 0], [140, 1, 110], '#5c9c48');
      k.box([0, 0.08, 14], [6, 0.16, 50], '#b8b0a0');
      // the cottage
      k.box([0, 9, -22], [56, 18, 16], '#efe6d2');
      for (var i = 0; i < 5; i++) {
        k.box([0, 18.8 + i * 1.6, -22], [58 - i * 10, 1.6, 18 - i * 3.2], '#9a4a3a');
      }
      k.box([0, 9.5, -13.9], [56.4, 0.8, 0.3], '#5a3a24');
      [[-20, 4.5], [-8, 4.5], [8, 4.5], [20, 4.5], [-20, 13], [-8, 13], [8, 13], [20, 13]].forEach(function (w) {
        k.box([w[0], w[1], -13.9], [5, 4.4, 0.3], '#cfe8ff', { m: 'glass' });
        k.box([w[0] - 3.4, w[1], -13.85], [1.2, 4.4, 0.3], '#4a7a5a');
        k.box([w[0] + 3.4, w[1], -13.85], [1.2, 4.4, 0.3], '#4a7a5a');
      });
      k.box([0, 3.6, -13.8], [4, 7.2, 0.4], '#7a3a2a');
      k.box([0, 8.2, -11], [10, 0.5, 6], '#9a4a3a');
      k.box([26, 14, -22], [3, 28, 5], '#9a4f3a');
      // the fence, the beds, the gnomes
      for (var p = -60; p <= 60; p += 1.6) {
        if (Math.abs(p) < 4) continue;
        k.box([p, 1.6, 30], [0.5, 3.2, 0.4], '#f4f0e8');
      }
      k.box([-32, 2.6, 30.3], [56, 0.3, 0.3], '#f4f0e8');
      k.box([32, 2.6, 30.3], [56, 0.3, 0.3], '#f4f0e8');
      [[-7, 4], [7, 4], [-7, 18], [7, 18]].forEach(function (b) {
        k.box([b[0], 0.8, b[1]], [3, 1.6, 10], WOOD);
        for (var f = 0; f < 4; f++) k.shape('sph', [b[0], 1.9, b[1] - 3.6 + f * 2.4], [1.4, 1.2, 1.4], ['#e85a8a', GOLD, '#c86ad8', '#ffffff'][f]);
      });
      put(k, 'gnome', -18, 10, 0.4);
      put(k, 'gnome', 16, 16, -0.6);
      hider(k, 'gnome', -24, 20, 0.2, 1.3, 0.45);
      k.shape('cyl', [22, 0.9, 6], [0.5, 1.8, 0.5], '#a89a88');
      k.shape('cyl', [22, 2.0, 6], [1.9, 0.5, 1.9], '#a89a88');
      k.tree(36, 10, 1.6, '#3a8a3a');
      k.tree(-38, 0, 1.4, '#4a9a3a');
      // Mittens on the path
      k.attach(3, 0, 8, 1.2, [{ t: 'rbox', p: [0, 0.85, 0], s: [0.8, 0.7, 1.7], c: '#d8873a' },
                               { t: 'rbox', p: [0, 1.35, 0.95], s: [0.8, 0.7, 0.7], c: '#d8873a' },
                               { t: 'cone', p: [-0.24, 1.85, 0.9], s: [0.22, 0.32, 0.12], c: '#a85a22' },
                               { t: 'cone', p: [0.24, 1.85, 0.9], s: [0.22, 0.32, 0.12], c: '#a85a22' },
                               { t: 'box', p: [0, 1.4, -1.2], s: [0.16, 0.16, 1.2], c: '#a85a22' }]);
      seeker(k, 10, 22, -2.6, { anim: 'walk', time: 0.4 });
    }
  });

  // ------------------------------------------------- the toy shop
  Thumbs.registerWorld('pp_toyshop', {
    sky: { top: '#3a2a5a', horizon: '#8a6aa8', sun: [0.3, 0.8, 0.4], clouds: 0.2, tint: '#ffe8d0' },
    camera: [[18, 13, 26], [-1, 3, -3], 44],
    build: function (parts, k) {
      room(k, 46, 32, '#e8e0d0', '#f2c230', '#8ac8e8');
      k.box([0, 0.02, 0], [46, 0.04, 32], '#ffffff', { dec: 'harlequin', dw: 1, a: 0.5 });
      // shelves of toys along the back
      for (var s = 0; s < 3; s++) {
        k.box([-8, 1 + s * 3.4, -14.2], [26, 0.3, 2.4], '#d8402a');
      }
      [['#d8402a', 'A'], ['#2f6ad0', 'B'], ['#3aa04a', 'C'], [GOLD, 'D'], ['#8a4ad0', 'E']].forEach(function (b, i) {
        put(k, 'block', -18 + i * 4.4, -14, 0, b[0], b[1], 1.15);
      });
      put(k, 'teddy', -16, -14, 0, null, null, 4.55);
      put(k, 'duck', -6, -14, 0.3, null, null, 4.55);
      put(k, 'ball', 2, -14, 0, null, null, 4.55);
      put(k, 'teddy', -2, -8, 0.4);
      put(k, 'horse', 8, -9, -0.8);
      put(k, 'block', -12, -4, 0.3, '#2f6ad0', 'Z');
      put(k, 'block', -10.2, -4, 0.3, GOLD, 'Y');
      put(k, 'block', -11.1, -4, 0.3, '#d8402a', 'X', 1.8);
      hider(k, 'duck', 3, -2, -0.4, 1.3, 1.0);
      put(k, 'ball', 12, -2, 0);
      // a train set round a little hill
      k.box([-14, 0.3, 6], [12, 0.6, 7], '#4a8a3a');
      k.box([-14, 1.2, 6], [3, 1.4, 2], '#d8402a');
      k.box([-12.2, 1.0, 6], [2.4, 1.0, 1.8], '#2f6ad0');
      k.shape('cyl', [-14.6, 2.3, 6], [0.6, 1.0, 0.6], '#2a2a2a');
      // the lights are out: a seeker's torch
      seeker(k, 12, 8, -2.4, { anim: 'walk', time: 0.6 });
      k.shape('cone', [6, 3.6, 2.6], [5, 12, 5], '#fff6c8', { a: 0.25, m: 'glass', r: [1.35, -2.4, 0] });
    }
  });

  // ------------------------------------------------- MegaMart
  Thumbs.registerWorld('pp_megamart', {
    sky: { top: '#8fc4ef', horizon: '#e8f4f8', sun: [0.3, 0.8, 0.4], clouds: 0.4, tint: '#ffffff' },
    camera: [[20, 14, 28], [-2, 3, -4], 44],
    build: function (parts, k) {
      room(k, 50, 36, '#d8dcd8', '#e8f0f0', '#2ab0a0');
      k.box([0, 12.6, -17.7], [20, 2.4, 0.2], '#2ab0a0', { dec: 't~MEGAMART~#2ab0a0~#ffffff~8.00' });
      // two runs of shelving with boxes and bottles
      [-12, 2].forEach(function (z, row) {
        k.box([-6, 4.6, z], [26, 9.2, 0.4], '#c8ccd0');
        for (var s = 0; s < 3; s++) k.box([-6, 0.6 + s * 3.4, z + 1.2], [26, 0.3, 2.4], '#d8dcdf');
        for (var i = 0; i < 9; i++) {
          var x = -17 + i * 2.8;
          var colour = ['#f08a2a', '#d8402a', GOLD][(i + row) % 3];
          if (row === 0 || i % 2) put(k, 'cereal', x, z + 1.0, 0, colour, null, 0.75);
          put(k, i % 2 ? 'soda' : 'cereal', x, z + 1.0, 0, colour, null, 4.15);
        }
      });
      // the hider among the cereal, priced
      hider(k, 'cereal', -8.6, 3.0, 0, 1.5, 0.35, '#f08a2a', 7.55);
      k.box([-8.6, 11.6, 3.0], [2.2, 1.3, 0.12], GOLD, { dec: 't~SALE!~#f2c230~#c82a2a~1.70' });
      put(k, 'trolley', 8, 8, -0.7);
      put(k, 'trolley', 12, 4, -0.9);
      k.box([16, 1.2, -12], [8, 2.4, 3], '#3a4a5a');
      k.box([16, 2.5, -12], [8, 0.2, 3], '#2a2a2a');
      seeker(k, 4, 12, -2.8, { anim: 'walk', time: 0.2 });
      k.player(-2, 14, 2.9, { anim: 'idle', time: 0.5, holding: null, wear: band('#d8402a') });
    }
  });

  // ------------------------------------------------- the museum
  Thumbs.registerWorld('pp_museum', {
    sky: { top: '#0c1020', horizon: '#3a4a6a', sun: [0.2, 0.8, 0.3], clouds: 0.1, tint: '#c8d8ff' },
    camera: [[22, 15, 30], [-2, 5, -4], 44],
    build: function (parts, k) {
      room(k, 54, 38, '#d8d0c0', '#5a4a6a', '#4a4a6a');
      for (var c = 0; c < 4; c++) k.shape('cyl', [-22 + c * 14, 7, -17], [2.4, 14, 2.4], '#e8e4dc');
      // the dinosaur skeleton on its dais
      k.box([-6, 0.6, -6], [24, 1.2, 12], '#a89a88');
      var bone = '#d8cdb0';
      k.box([-6, 8.5, -6], [16, 0.9, 1.0], bone, { r: [0, 0, 0.12] });
      k.box([3.5, 9.5, -6], [5, 1.6, 2.2], bone);
      for (var r = 0; r < 7; r++) k.box([-12 + r * 2, 6.6, -6], [0.5, 3.6, 2.6], bone);
      k.box([-14.5, 7.4, -6], [6, 0.6, 0.6], bone, { r: [0, 0, -0.4] });
      [[-10, -7.4], [-10, -4.6], [-2, -7.4], [-2, -4.6]].forEach(function (l) { k.box([l[0], 4.0, l[1]], [0.7, 5.6, 0.7], bone); });
      put(k, 'armour', 16, -12, -0.4);
      put(k, 'armour', 20, -6, -0.8);
      put(k, 'urn', 12, 4, 0);
      k.box([-18, 1, 4], [3, 2, 3], '#e8e4dc');
      put(k, 'bust', -18, 4, 0.5, null, null, 2);
      k.box([-10, 1, 8], [3, 2, 3], '#e8e4dc');
      hider(k, 'bust', -10, 8, 0.3, 3.15, 0.38, null, 2);
      // the searchlight's beam on the floor
      k.shape('cyl', [2, 12, 4], [10, 24, 10], '#fff6c8', { a: 0.12, m: 'glass' });
      k.shape('cyl', [2, 0.05, 4], [10, 0.1, 10], '#fff6c8', { a: 0.4, m: 'neon' });
      seeker(k, 8, 13, -2.6, { anim: 'walk', time: 0.3 });
    }
  });
})(window);
