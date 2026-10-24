/* Whodunit's world-page pictures: the card, and each of the four places
   the case moves to, built from the same blocks the game draws with
   (Thumbs.registerWorld; loaded by thumbs.js the first time one is asked
   for).  Every player wears the classic default -- yellow skin, red torso,
   blue legs; who is who is told by what they carry and wear: the
   detective's deerstalker and revolver, the murderer's knife held low, a
   guest's candle or lantern, the masquerade's masks. */
(function (global) {
  'use strict';
  var Thumbs = global.Thumbs;
  if (!Thumbs || !Thumbs.registerWorld) return;

  var BRASS = '#c8a040', WOOD = '#5a3a24', WOOD_DARK = '#3a2416', CHALK = '#f4f4f4';
  var LIT = '#ffcf8a', BOLT = '#dce6ff';

  // ------------------------------------------------- what they carry
  var REVOLVER = { data: { parts: [
    { t: 'box', p: [0, 0.12, 0.62], s: [0.2, 0.2, 1.3], c: '#5a5e66', m: 'metal' },
    { t: 'cyl', p: [0, 0.14, 0.05], s: [0.46, 0.5, 0.46], c: '#6a6e76', m: 'metal', r: [Math.PI / 2, 0, 0] },
    { t: 'box', p: [0, -0.32, -0.2], s: [0.3, 0.8, 0.42], c: '#5a3a24', r: [-0.35, 0, 0] }] } };
  var KNIFE = { data: { parts: [
    { t: 'box', p: [0, 0, -0.1], s: [0.22, 0.28, 0.7], c: '#2a1a12' },
    { t: 'box', p: [0, 0, 0.32], s: [0.5, 0.16, 0.14], c: BRASS, m: 'metal' },
    { t: 'wedge', p: [0, 0.04, 1.02], s: [0.08, 0.36, 1.3], c: '#d8dce4', m: 'metal' }] } };
  var CANDLE = { data: { parts: [
    { t: 'cyl', p: [0, -0.1, 0.3], s: [0.9, 0.12, 0.9], c: BRASS, m: 'metal' },
    { t: 'cyl', p: [0, 0.45, 0.3], s: [0.3, 1.0, 0.3], c: '#f2ead8' },
    { t: 'sph', p: [0, 1.1, 0.3], s: [0.24, 0.42, 0.24], c: '#ffb84a', m: 'neon' }] } };
  var LANTERN = { data: { parts: [
    { t: 'box', p: [0, 0.3, 0.3], s: [0.1, 0.9, 0.1], c: '#2a2a2e' },
    { t: 'box', p: [0, -0.55, 0.3], s: [0.8, 0.1, 0.8], c: '#2a2a2e', m: 'metal' },
    { t: 'box', p: [0, -0.95, 0.3], s: [0.66, 0.7, 0.66], c: '#ffc870', m: 'neon', a: 0.9 },
    { t: 'box', p: [0, -1.35, 0.3], s: [0.8, 0.12, 0.8], c: '#2a2a2e', m: 'metal' }] } };

  // ------------------------------------------------- what they wear
  // (the player's own space: +Z ahead, the top of the head at 5.9)
  function deerstalker() {
    return [{ t: 'sph', p: [0, 5.75, 0], s: [2.3, 1.1, 2.3], c: '#8a6a48' },
            { t: 'box', p: [0, 5.45, 1.25], s: [1.6, 0.14, 0.7], c: '#7a5a3a' },
            { t: 'box', p: [0, 5.45, -1.25], s: [1.6, 0.14, 0.7], c: '#7a5a3a' },
            { t: 'box', p: [0, 6.3, 0], s: [0.14, 0.2, 1.0], c: '#5a3a24' }];
  }
  function topHat(band) {
    return [{ t: 'cyl', p: [0, 5.95, 0], s: [2.5, 0.14, 2.5], c: '#1a1a1e' },
            { t: 'cyl', p: [0, 6.85, 0], s: [1.6, 1.8, 1.6], c: '#1a1a1e' },
            { t: 'cyl', p: [0, 6.2, 0], s: [1.64, 0.3, 1.64], c: band || '#7a1a2a' }];
  }
  function bowler() {
    return [{ t: 'cyl', p: [0, 5.92, 0], s: [2.4, 0.12, 2.4], c: '#3a2a1e' },
            { t: 'sph', p: [0, 6.2, 0], s: [1.8, 1.3, 1.8], c: '#3a2a1e' }];
  }
  function captainCap() {
    return [{ t: 'cyl', p: [0, 6.05, 0], s: [2.3, 0.6, 2.3], c: '#f2f0ea' },
            { t: 'box', p: [0, 5.82, 1.1], s: [1.4, 0.12, 0.7], c: '#1a1a24' },
            { t: 'cyl', p: [0, 5.82, 0], s: [2.32, 0.2, 2.32], c: '#1a1a24' }];
  }
  /* the masquerade: the same gold mask on every face, and a black cloak */
  function mask() {
    return [{ t: 'box', p: [0, 4.95, 0.74], s: [1.9, 0.62, 0.12], c: '#e8c860', m: 'metal' },
            { t: 'box', p: [-0.42, 4.97, 0.81], s: [0.4, 0.22, 0.04], c: '#1a1a1a' },
            { t: 'box', p: [0.42, 4.97, 0.81], s: [0.4, 0.22, 0.04], c: '#1a1a1a' },
            { t: 'cone', p: [-1.05, 5.3, 0.7], s: [0.3, 0.8, 0.12], c: '#c83a3a', r: [0, 0, 0.5] },
            { t: 'cone', p: [1.05, 5.3, 0.7], s: [0.3, 0.8, 0.12], c: '#c83a3a', r: [0, 0, -0.5] },
            { t: 'box', p: [0, 2.6, -0.62], s: [2.3, 3.4, 0.14], c: '#1a1a24' }];
  }

  // ------------------------------------------------- the scene of the crime
  /* a body where it fell, in its chalk outline (lying along +Z, head first) */
  function body(k, x, y, z, yaw) {
    k.attach(x, y, z, yaw, [
      { t: 'box', p: [0, 0.5, 0], s: [2.0, 1.0, 2.6], c: '#7a7a84' },
      { t: 'rbox', p: [0, 0.58, 2.1], s: [1.3, 1.1, 1.3], c: '#c8c0b8' },
      { t: 'box', p: [1.45, 0.4, 0.4], s: [0.9, 0.8, 2.4], c: '#7a7a84' },
      { t: 'box', p: [-1.45, 0.4, 0.2], s: [0.9, 0.8, 2.4], c: '#7a7a84' },
      { t: 'box', p: [0.55, 0.42, -2.55], s: [0.95, 0.85, 2.6], c: '#4a4a56' },
      { t: 'box', p: [-0.55, 0.42, -2.55], s: [0.95, 0.85, 2.6], c: '#4a4a56' },
      { t: 'box', p: [0, 0.04, 3.05], s: [3.4, 0.04, 0.18], c: CHALK },
      { t: 'box', p: [0, 0.04, -4.1], s: [2.8, 0.04, 0.18], c: CHALK },
      { t: 'box', p: [2.05, 0.04, -0.5], s: [0.18, 0.04, 7.2], c: CHALK },
      { t: 'box', p: [-2.05, 0.04, -0.5], s: [0.18, 0.04, 7.2], c: CHALK },
      { t: 'cyl', p: [0.8, 0.03, 1.2], s: [2.4, 0.04, 1.8], c: '#6a0a12' }]);
  }
  /* a clue on the floor, glowing, with its beam of light */
  function clue(k, x, y, z, which) {
    var parts = {
      watch: [{ t: 'cyl', p: [0, 0.5, 0], s: [1.0, 0.22, 1.0], c: BRASS, m: 'metal', r: [Math.PI / 2, 0, 0] },
              { t: 'cyl', p: [0, 0.5, 0.12], s: [0.82, 0.04, 0.82], c: '#f8f4e8', r: [Math.PI / 2, 0, 0] }],
      letter: [{ t: 'box', p: [0, 0.08, 0], s: [1.3, 0.08, 0.9], c: '#f2ead8' },
               { t: 'cyl', p: [0, 0.14, 0], s: [0.36, 0.06, 0.36], c: '#b81e2a' }],
      key: [{ t: 'box', p: [0, 0.12, 0.3], s: [0.2, 0.2, 1.2], c: BRASS, m: 'metal' },
            { t: 'cyl', p: [0, 0.12, -0.5], s: [0.7, 0.2, 0.7], c: BRASS, m: 'metal' }]
    }[which || 'watch'];
    k.attach(x, y, z, 0.4, parts);
    k.shape('cyl', [x, y + 6, z], [1.4, 12, 1.4], '#ffe8a0', { a: 0.18, m: 'glass' });
    k.shape('cyl', [x, y + 0.03, z], [2.6, 0.04, 2.6], '#ffe8a0', { a: 0.5, m: 'neon' });
  }
  /* a fork of lightning down the sky from (x, y, z): zig, zag, a branch */
  function lightning(k, x, y, z, scale) {
    var s = scale || 1, px = x, py = y;
    [[3, -9, 0.3], [-4, -8, -0.45], [3.5, -9, 0.35], [-2.5, -7, -0.3], [2, -8, 0.25]].forEach(function (seg) {
      var nx = px + seg[0] * s, ny = py + seg[1] * s;
      var len = Math.sqrt(seg[0] * seg[0] + seg[1] * seg[1]) * s;
      k.box([(px + nx) / 2, (py + ny) / 2, z], [0.7 * s, len + 0.6 * s, 0.7 * s], BOLT,
            { m: 'neon', r: [0, 0, Math.atan2(seg[0], -seg[1])] });
      px = nx; py = ny;
    });
    k.box([x + 2 * s, y - 20 * s, z], [0.4 * s, 9 * s, 0.4 * s], BOLT, { m: 'neon', r: [0, 0, -0.7] });
  }
  /* a bare winter tree, branches reaching */
  function deadTree(k, x, z, s) {
    k.shape('cyl', [x, 5 * s, z], [1.4 * s, 10 * s, 1.4 * s], '#3a2e26');
    [[0.7, 8, 0.9], [-0.8, 7, -0.8], [0.3, 9.5, -0.5], [-0.4, 10, 0.6]].forEach(function (b, i) {
      k.box([x + b[0] * 2.2 * s, b[1] * s + 1.4 * s, z + (i % 2 ? 0.8 : -0.8) * s], [0.5 * s, 5 * s, 0.5 * s],
            '#3a2e26', { r: [0, i * 0.8, b[2]] });
    });
  }
  function window_(k, x, y, z, w, h, lit, face) {
    // a window on a wall facing +z (face 'z') or +x (face 'x')
    var glass = lit ? LIT : '#1e2636';
    var o = lit ? { m: 'neon' } : { m: 'glass' };
    if (face === 'x') {
      k.box([x, y, z], [0.2, h, w], glass, o);
      k.box([x + 0.12, y, z], [0.12, h, 0.24], '#e8e0cc');
      k.box([x + 0.12, y, z], [0.12, 0.24, w], '#e8e0cc');
    } else {
      k.box([x, y, z], [w, h, 0.2], glass, o);
      k.box([x, y, z + 0.12], [0.24, h, 0.12], '#e8e0cc');
      k.box([x, y, z + 0.12], [w, 0.24, 0.12], '#e8e0cc');
    }
  }

  // ------------------------------------------------------------ card
  /* The drawing room at Blackwood, the storm at the window: a body on the
     rug, the detective's revolver on the guest with the knife, a guest
     with a candle who has just walked in on it. */
  Thumbs.registerWorld('whodunit', {
    sky: { top: '#121624', horizon: '#3a3a52', sun: [-0.3, 0.6, 0.5], clouds: 0.3, tint: '#ffe0c0' },
    camera: [[17, 11, 27], [-1, 4.4, -3], 44],
    build: function (parts, k) {
      k.box([0, -0.25, 0], [46, 0.5, 32], '#6a4a2e', { dec: 'planks' });
      k.box([0, 8, -16.3], [46, 16, 0.6], '#6a2228');
      k.box([-23.3, 8, 0], [0.6, 16, 32], '#5a1e24');
      // the panelling and the dado rail
      k.box([0, 2.4, -15.9], [46, 4.8, 0.2], WOOD);
      k.box([-22.9, 2.4, 0], [0.2, 4.8, 32], WOOD);
      k.box([0, 4.95, -15.85], [46, 0.3, 0.32], WOOD_DARK);
      k.box([-22.85, 4.95, 0], [0.32, 0.3, 32], WOOD_DARK);
      // the rug
      k.box([0, 0.03, -1], [20, 0.06, 13], '#7a1a2a');
      k.box([0, 0.07, -1], [17, 0.02, 10], '#9a2a32', { dec: 'filigree', dw: 1 });
      // the fireplace, and the portrait above it
      k.box([-4, 3.0, -15.5], [9, 6, 1.0], '#d8d0c0');
      k.box([-4, 2.1, -15.05], [4.6, 3.8, 0.2], '#1a1210');
      k.shape('cone', [-4, 1.3, -14.9], [2.4, 2.2, 0.8], '#ff8a2a', { m: 'neon' });
      k.shape('cone', [-3.2, 1.0, -14.85], [1.2, 1.5, 0.6], '#ffd04a', { m: 'neon' });
      k.box([-4, 6.2, -14.9], [10.4, 0.5, 2.0], '#c8c0b0');
      k.box([-4, 10.4, -15.85], [6.4, 7.6, 0.3], BRASS, { m: 'metal' });
      k.box([-4, 10.4, -15.65], [5.6, 6.8, 0.12], '#ffffff', { dec: 'portrait' });
      // the tall window, white with lightning
      k.box([10, 8.4, -15.95], [7.4, 11.4, 0.3], '#e8e0cc');
      k.box([10, 8.4, -15.75], [6.4, 10.4, 0.12], '#b8c8ff', { m: 'neon' });
      k.box([10, 8.4, -15.6], [0.3, 10.4, 0.2], '#e8e0cc');
      k.box([10, 8.4, -15.6], [6.4, 0.3, 0.2], '#e8e0cc');
      k.box([6.0, 8.6, -15.4], [1.4, 12, 0.6], '#3a1a3a');
      k.box([14.0, 8.6, -15.4], [1.4, 12, 0.6], '#3a1a3a');
      k.box([8.6, 9.8, -15.66], [0.3, 4.4, 0.04], '#ffffff', { m: 'neon', r: [0, 0, 0.4] });
      k.box([9.6, 6.4, -15.66], [0.3, 3.6, 0.04], '#ffffff', { m: 'neon', r: [0, 0, -0.35] });
      // the grandfather clock, the armchair, the side table
      k.box([-19.5, 0.3, -13.5], [2.4, 0.6, 1.6], WOOD_DARK);
      k.box([-19.5, 3.4, -13.5], [1.9, 5.6, 1.2], '#6a2a1a');
      k.box([-19.5, 7.3, -13.5], [2.3, 2.3, 1.5], '#6a2a1a');
      k.box([-19.5, 7.3, -12.7], [1.6, 1.6, 0.1], '#efe3c8', { dec: 'clockface' });
      k.box([-19.5, 8.65, -13.5], [2.5, 0.4, 1.7], WOOD_DARK);
      k.attach(-13, 0, -7, 0.7, [
        { t: 'box', p: [0, 0.8, 0.1], s: [2.6, 1.0, 2.6], c: '#3a5a3a' },
        { t: 'rbox', p: [0, 1.5, 0.3], s: [2.4, 0.5, 2.2], c: '#4a6a4a' },
        { t: 'box', p: [-1.5, 1.4, 0.05], s: [0.5, 2.0, 2.7], c: '#3a5a3a' },
        { t: 'box', p: [1.5, 1.4, 0.05], s: [0.5, 2.0, 2.7], c: '#3a5a3a' },
        { t: 'rbox', p: [0, 2.6, -1.15], s: [2.6, 3.0, 0.6], c: '#3a5a3a' }]);
      k.box([-9, 2.0, -11], [2.6, 0.2, 2.6], WOOD);
      k.box([-9, 1.0, -11], [0.4, 2.0, 0.4], WOOD_DARK);
      k.box([-9, 0.1, -11], [1.6, 0.2, 1.6], WOOD_DARK);
      k.shape('cyl', [-9, 2.5, -11], [0.6, 0.8, 0.6], '#d8dce4', { m: 'glass', a: 0.7 });
      // the chandelier, its candles lit
      k.shape('cyl', [0, 14.2, -3], [0.2, 3.6, 0.2], BRASS, { m: 'metal' });
      k.shape('cyl', [0, 12.3, -3], [4.4, 0.3, 4.4], BRASS, { m: 'metal' });
      for (var c = 0; c < 6; c++) {
        var a = c * Math.PI / 3;
        k.shape('cyl', [Math.sin(a) * 2.0, 12.85, -3 + Math.cos(a) * 2.0], [0.24, 0.8, 0.24], '#f2ead8');
        k.shape('sph', [Math.sin(a) * 2.0, 13.45, -3 + Math.cos(a) * 2.0], [0.24, 0.4, 0.24], '#ffd27a', { m: 'neon' });
      }
      // the victim, and a clue that fell with them
      body(k, -1, 0.08, -2.5, 2.1);
      clue(k, 3.6, 0.08, 1.6, 'watch');
      // the detective has the murderer covered; a guest walks in on it
      k.player(-9, 2, 1.68, { anim: 'idle', time: 0.2, holding: REVOLVER, pitch: -0.05, wear: deerstalker(),
                              face: 'face_angry' });
      k.player(9, 0, -0.64, { anim: 'walk', time: 0.7, holding: KNIFE, wear: topHat(), face: 'face_angry' });
      k.player(13, -9, -1.14, { anim: 'idle', time: 0.5, holding: CANDLE, wear: bowler() });
    }
  });

  // ------------------------------------------------- Blackwood Manor
  /* The house from the end of the drive in the storm: lightning over the
     roofs, two windows lit, a guest coming up the gravel with a lantern and
     another waiting under the portico. */
  Thumbs.registerWorld('wd_manor', {
    sky: { top: '#0e1220', horizon: '#3a3a52', sun: [-0.3, 0.55, 0.4], clouds: 0.75, tint: '#c8d0ff' },
    camera: [[30, 15, 66], [0, 10, -6], 44],
    build: function (parts, k) {
      k.box([0, -0.5, 0], [170, 1, 130], '#2e4a2a');
      // the drive and the turning circle
      k.box([0, 0.05, 18], [10, 0.1, 50], '#8a8478');
      k.shape('cyl', [0, 0.06, 12], [26, 0.12, 22], '#8a8478');
      // the fountain in the circle
      k.shape('cyl', [0, 0.8, 12], [10, 1.6, 10], '#8a8478');
      k.shape('cyl', [0, 1.5, 12], [8.6, 0.2, 8.6], '#2a3a4a', { m: 'glass', a: 0.85 });
      k.shape('cyl', [0, 3.2, 12], [1.2, 3.2, 1.2], '#a8a090');
      k.shape('cyl', [0, 4.9, 12], [4, 0.5, 4], '#a8a090');
      // the house: the main block and two wings
      var Z = -18;
      k.box([0, 11.5, Z], [56, 23, 22], '#c8bca4');
      k.box([-38, 9, Z + 3], [20, 18, 16], '#bcb098');
      k.box([38, 9, Z + 3], [20, 18, 16], '#bcb098');
      for (var i = 0; i < 4; i++) {
        k.box([0, 23.6 + i * 1.5, Z], [58 - i * 9, 1.5, 24 - i * 4.4], '#3a3a44');
      }
      [-38, 38].forEach(function (x) {
        for (var j = 0; j < 3; j++) k.box([x, 18.6 + j * 1.4, Z + 3], [22 - j * 6, 1.4, 18 - j * 5], '#3a3a44');
      });
      k.box([-20, 30, Z - 2], [4, 10, 4], '#7a4a3a', { dec: 'bricks' });
      k.box([20, 30, Z - 2], [4, 10, 4], '#7a4a3a', { dec: 'bricks' });
      k.box([-20, 35.3, Z - 2], [4.8, 0.6, 4.8], '#5a3a2e');
      k.box([20, 35.3, Z - 2], [4.8, 0.6, 4.8], '#5a3a2e');
      k.box([0, 12.0, Z + 11.1], [56.4, 0.6, 0.3], '#e8e0cc');
      // its windows: two lit, the rest dark
      var front = Z + 11.05;
      [[-20, 6, 0], [-10, 6, 0], [10, 6, 1], [20, 6, 0], [-20, 17, 1], [-10, 17, 0], [0, 17, 0], [10, 17, 0],
       [20, 17, 0]].forEach(function (w) {
        window_(k, w[0], w[1], front, 5, 6.4, w[2]);
      });
      [[-38, 6], [38, 6], [-38, 13], [38, 13]].forEach(function (w, n) {
        window_(k, w[0], w[1], Z + 11.05, 6, 5, n === 3);
      });
      // the portico: columns, pediment, steps, the door ajar
      k.box([0, 0.4, Z + 14], [16, 0.8, 6], '#a8a090');
      k.box([0, 1.0, Z + 12.5], [14, 0.4, 3], '#a8a090');
      [-6, -2, 2, 6].forEach(function (x) { k.shape('cyl', [x, 5.6, Z + 16], [1.4, 9.6, 1.4], '#e8e0cc'); });
      k.box([0, 11.0, Z + 14], [16, 1.2, 6.6], '#e8e0cc');
      k.shape('wedge', [0, 13.0, Z + 14], [16, 2.8, 6.6], '#d8d0bc');
      k.box([0, 4.6, Z + 11.1], [4.4, 8, 0.2], '#3a1e12');
      k.box([1.0, 4.6, Z + 11.25], [2.2, 7.8, 0.2], LIT, { m: 'neon' });
      k.shape('sph', [-3.4, 8.4, Z + 11.5], [0.8, 1.0, 0.8], '#ffd27a', { m: 'neon' });
      k.shape('sph', [3.4, 8.4, Z + 11.5], [0.8, 1.0, 0.8], '#ffd27a', { m: 'neon' });
      // hedges along the lawn and the drive, and the trees
      [[-30, 8, 30, 3], [30, 8, 30, 3], [-11, 28, 3, 22], [11, 28, 3, 22]].forEach(function (h) {
        k.box([h[0], 1.6, h[1]], [h[2], 3.2, h[3]], '#24502a');
        k.box([h[0], 3.3, h[1]], [h[2] - 0.6, 0.2, h[3] - 0.6], '#1e4424');
      });
      deadTree(k, -46, 18, 1.4);
      deadTree(k, 48, 24, 1.2);
      deadTree(k, -60, -10, 1.6);
      k.pine(62, -6, 1.6, '#1e3a24');
      k.pine(-70, 10, 1.3, '#1e3a24');
      // the storm
      lightning(k, 30, 70, -60, 1.6);
      // the guests
      k.player(4, 30, 3.0, { anim: 'walk', time: 0.4, holding: LANTERN, wear: topHat() });
      k.player(-3, Z + 17.5, 0.2, { anim: 'idle', time: 0.2, holding: null, wear: bowler() });
    }
  });

  // ------------------------------------------------- The Midnight Express
  /* The train on the viaduct over a snowy gorge, the tunnel mouth ahead, the
     streamliner's lamp burning -- and two passengers on the roof, one of
     them with a knife. */
  Thumbs.registerWorld('wd_express', {
    sky: { top: '#0a1020', horizon: '#2a3450', sun: [0.3, 0.6, -0.4], clouds: 0.3, tint: '#c8d0ff' },
    camera: [[36, 28, 84], [38, 14, -2], 50],
    build: function (parts, k) {
      k.box([0, -6, 0], [220, 1, 140], '#d8e0ec');
      // the gorge's river, and the viaduct across it
      k.box([0, -5.4, 18], [220, 0.4, 14], '#2a3a50', { m: 'glass', a: 0.9 });
      k.box([0, 6.6, 0], [200, 2.4, 12], '#8a8478');
      for (var p = -84; p <= 84; p += 21) {
        k.box([p, 0, 0], [5, 12, 10], '#7a746a');
        k.box([p, 4.8, 0], [7, 1.4, 11], '#8a8478');
      }
      k.box([0, 8.0, 0], [200, 0.4, 8], '#4a3a2e');
      k.box([0, 8.4, -1.6], [200, 0.4, 0.4], '#8a8e96', { m: 'metal' });
      k.box([0, 8.4, 1.6], [200, 0.4, 0.4], '#8a8e96', { m: 'metal' });
      // the mountains, snow on their tops, and the tunnel in the nearest
      [[-90, -60, 70, 60], [-30, -80, 90, 74], [50, -70, 80, 66], [110, -30, 70, 56]].forEach(function (m) {
        k.shape('cone', [m[0], m[3] / 2 - 6, m[1]], [m[2], m[3], m[2]], '#4a5468');
        k.shape('cone', [m[0], m[3] - 6 - m[3] * 0.16, m[1]], [m[2] * 0.34, m[3] * 0.32, m[2] * 0.34], '#eef2f8');
      });
      k.box([108, 14, 0], [24, 44, 50], '#4a5468');
      k.shape('cone', [122, 52, -4], [64, 32, 64], '#4a5468');
      k.shape('cone', [122, 62, -4], [30, 14, 30], '#eef2f8');
      k.box([108, 36.2, 0], [24.4, 0.6, 50.4], '#eef2f8');
      k.box([95.6, 12, 0], [0.8, 12, 9], '#141820');
      k.box([95.4, 18.8, 0], [1.2, 1.8, 12], '#8a8478');
      // the carriages: maroon and gold, their windows lit
      var cars = [[-70, 26], [-41, 26], [-12, 26], [17, 26]];
      cars.forEach(function (c, n) {
        k.box([c[0], 12.6, 0], [c[1], 8.4, 9], '#3a1a2a');
        k.box([c[0], 17.2, 0], [c[1] + 0.4, 0.8, 9.6], '#2a1a22');
        k.box([c[0], 11.0, 4.56], [c[1], 0.3, 0.12], BRASS);
        for (var w = 0; w < 6; w++) {
          k.box([c[0] - c[1] / 2 + 2.6 + w * 4.2, 14.0, 4.56], [2.6, 2.4, 0.12], n === 2 && w === 3 ? '#ffe8c0' : LIT,
                { m: 'neon' });
        }
        k.shape('cyl', [c[0] - 8, 9.0, 3.8], [2.2, 0.6, 2.2], '#1a1a1e', { r: [Math.PI / 2, 0, 0] });
        k.shape('cyl', [c[0] + 8, 9.0, 3.8], [2.2, 0.6, 2.2], '#1a1a1e', { r: [Math.PI / 2, 0, 0] });
      });
      // the tender and the streamliner
      k.box([46, 12.0, 0], [14, 7.2, 9], '#1e2a22', { m: 'metal' });
      k.box([46, 15.8, 0], [12, 0.6, 8], '#1a1a1a');
      k.box([60, 13.0, 0], [12, 9.2, 9.4], '#2a3a2a');
      k.box([60, 14.6, 4.76], [6, 2.2, 0.12], LIT, { m: 'neon' });
      k.box([74, 11.6, 0], [16, 6.4, 9.6], '#1e2a22', { m: 'metal' });
      k.box([84, 10.8, 0], [4, 4.8, 8.4], '#1e2a22', { m: 'metal' });
      k.box([87.5, 10.0, 0], [3, 3.2, 7.2], '#1e2a22', { m: 'metal' });
      k.box([74, 11.0, 4.86], [22, 0.3, 0.12], BRASS, { m: 'metal' });
      k.box([74, 12.2, 4.86], [22, 0.3, 0.12], BRASS, { m: 'metal' });
      k.shape('cyl', [78, 15.6, 0], [2.0, 1.8, 2.0], '#1e2a22');
      k.shape('sph', [89.2, 11.0, 0], [0.8, 1.8, 1.8], '#fff6c8', { m: 'neon' });
      k.shape('cone', [92.4, 11.0, 0], [6, 5, 6], '#fff6c8', { a: 0.12, m: 'glass', r: [0, 0, Math.PI / 2] });
      // the smoke trailing back
      for (var s = 0; s < 6; s++) {
        k.shape('sph', [76 - s * 9, 20 + s * 1.6, -1 - s * 0.8], [4 + s * 1.4, 3 + s, 4 + s * 1.4], '#c8ccd8',
                { a: 0.55 - s * 0.06 });
      }
      // snowy pines down the sides of the gorge
      [[-96, 26], [-70, 34], [-36, 30], [30, 34], [64, 28], [-110, -14], [70, -20], [-60, -24]].forEach(function (t, i) {
        k.pine(t[0], t[1], 1.3 + (i % 3) * 0.2, '#24402e', -6);
      });
      // on the roof: one running, one with the knife close behind
      k.player(-4, 0.4, 1.57, { y: 17.6, anim: 'run', time: 0.3, holding: null, wear: bowler() });
      k.player(-16, -0.4, 1.57, { y: 17.6, anim: 'run', time: 0.7, holding: KNIFE, wear: topHat('#3a3a8a'),
                                  face: 'face_angry' });
    }
  });

  // ------------------------------------------------- The Grand Meridian
  /* The hotel's front at night from across the street: the neon sign on the
     roof, the canopy lit, a masked guest on the fire escape, a detective in
     the street below. */
  Thumbs.registerWorld('wd_hotel', {
    sky: { top: '#0a0c1c', horizon: '#3a2a4a', sun: [0.25, 0.6, 0.45], clouds: 0.25, tint: '#e0c8ff' },
    camera: [[24, 8, 62], [-2, 16, -4], 48],
    build: function (parts, k) {
      k.box([0, -0.5, 0], [180, 1, 140], '#34343a');
      k.box([0, 0.15, 6], [120, 0.3, 12], '#8a8680');
      k.box([0, 0.15, 44], [120, 0.3, 10], '#8a8680');
      for (var d = -54; d <= 54; d += 12) k.box([d, 0.04, 25], [5, 0.04, 0.5], '#e8e0a0');
      // the building: limestone with bronze piers, setbacks at the top
      var F = -2;
      k.box([0, 16, F - 20], [76, 32, 40], '#d8c8a4');
      k.box([0, 34.5, F - 22], [56, 5, 32], '#d8c8a4');
      k.box([0, 39.5, F - 24], [36, 5, 24], '#cbbb96');
      for (var x = -36; x <= 36; x += 8) k.box([x, 16, F + 0.15], [1.2, 32, 0.3], '#8a7a60');
      for (var fl = 0; fl < 4; fl++) {
        for (var w = -32; w <= 32; w += 8) {
          if (fl === 0 && Math.abs(w) < 6) continue;
          var lit = (fl * 7 + w) % 3 !== 0;
          k.box([w, 6 + fl * 7.2, F + 0.1], [5.6, 4.6, 0.2], lit ? LIT : '#1e2636', { m: lit ? 'neon' : 'glass' });
          k.box([w, 3.6 + fl * 7.2, F + 0.35], [5.8, 0.3, 0.5], '#6a5434');
        }
      }
      k.box([0, 32.2, F + 0.2], [76, 0.8, 0.6], '#e8c860', { m: 'metal' });
      // the sign on the roof
      k.box([0, 46, F - 14], [30, 7, 0.6], '#1a1a24', { dec: 't~MERIDIAN~#1a1a24~#ff7ac8~4.40' });
      k.box([0, 42.3, F - 13.6], [31, 0.3, 0.2], '#ff7ac8', { m: 'neon' });
      k.box([0, 42.4, F - 14.2], [0.6, 2.2, 0.6], '#2a2a2e');
      k.box([-12, 42.4, F - 14.2], [0.6, 2.2, 0.6], '#2a2a2e');
      k.box([12, 42.4, F - 14.2], [0.6, 2.2, 0.6], '#2a2a2e');
      // the entrance: revolving door, canopy and its bulbs
      k.box([0, 4, F + 0.2], [8, 8, 0.4], '#3a2a1a');
      k.shape('cyl', [0, 3.6, F + 1.6], [5, 7.2, 3], '#cfe8ff', { m: 'glass', a: 0.5 });
      k.box([0, 8.6, F + 4.5], [14, 0.6, 9], '#1e5a4a');
      k.box([0, 8.2, F + 9], [14.4, 1.2, 0.3], '#e8c860', { dec: 't~GRAND MERIDIAN~#1e5a4a~#e8c860~12.00' });
      for (var b = -6; b <= 6; b += 2) k.shape('sph', [b, 7.6, F + 9.2], [0.4, 0.4, 0.4], '#ffe8a0', { m: 'neon' });
      k.shape('cyl', [-6.6, 4.2, F + 8.6], [0.3, 8.4, 0.3], BRASS, { m: 'metal' });
      k.shape('cyl', [6.6, 4.2, F + 8.6], [0.3, 8.4, 0.3], BRASS, { m: 'metal' });
      // the fire escape up the side
      var EX = -38.6;
      for (var lv = 1; lv < 4; lv++) {
        var y = lv * 7.2 + 1.2;
        k.box([EX - 2.4, y, F - 10], [5, 0.3, 12], '#2a2a2e', { m: 'metal' });
        k.box([EX - 4.8, y + 1.6, F - 10], [0.2, 0.2, 12], '#2a2a2e');
        k.box([EX - 2.4, y - 3.6, F - 10], [0.2, 7.4, 13], '#2a2a2e', { r: [0.56, 0, 0], a: 0.98 });
      }
      // across the street: lamps and a motor car
      [-30, 0, 30].forEach(function (lx) {
        k.shape('cyl', [lx, 5, 11], [0.5, 10, 0.5], '#2a2a2e');
        k.shape('sph', [lx, 10.4, 11], [1.4, 1.4, 1.4], '#ffe8a0', { m: 'neon' });
      });
      k.attach(-16, 0, 20, Math.PI / 2, [
        { t: 'box', p: [0, 1.6, 0], s: [4.4, 2.0, 11], c: '#1a1a24' },
        { t: 'box', p: [0, 3.4, -1.2], s: [4.0, 1.8, 5], c: '#1a1a24' },
        { t: 'box', p: [0, 3.4, 1.35], s: [3.8, 1.4, 0.1], c: '#8ab0c8', m: 'glass' },
        { t: 'box', p: [0, 2.2, 3.9], s: [3.6, 1.4, 3.0], c: '#2a2a34' },
        { t: 'box', p: [0, 1.4, 5.55], s: [4.0, 0.4, 0.2], c: '#d8dce4', m: 'metal' },
        { t: 'sph', p: [-1.6, 2.3, 5.5], s: [0.7, 0.7, 0.4], c: '#fff6c8', m: 'neon' },
        { t: 'sph', p: [1.6, 2.3, 5.5], s: [0.7, 0.7, 0.4], c: '#fff6c8', m: 'neon' },
        { t: 'cyl', p: [-2.2, 1.0, 3.4], s: [2.0, 0.6, 2.0], c: '#141414', r: [0, 0, Math.PI / 2] },
        { t: 'cyl', p: [2.2, 1.0, 3.4], s: [2.0, 0.6, 2.0], c: '#141414', r: [0, 0, Math.PI / 2] },
        { t: 'cyl', p: [-2.2, 1.0, -3.4], s: [2.0, 0.6, 2.0], c: '#141414', r: [0, 0, Math.PI / 2] },
        { t: 'cyl', p: [2.2, 1.0, -3.4], s: [2.0, 0.6, 2.0], c: '#141414', r: [0, 0, Math.PI / 2] }]);
      // the next buildings along, dark brick
      k.box([-64, 14, F - 20], [44, 28, 40], '#5a3a32', { dec: 'bricks' });
      k.box([64, 18, F - 20], [44, 36, 40], '#4a3a42');
      for (var n = 0; n < 5; n++) {
        k.box([52 + (n % 3) * 9, 8 + Math.floor(n / 3) * 12, F + 0.1], [4, 4, 0.2], n % 2 ? LIT : '#1e2636',
              { m: n % 2 ? 'neon' : 'glass' });
      }
      // the masked guest on the fire escape; the detective by the canopy
      k.player(EX - 2.4, F - 7, 0.3, { y: 2 * 7.2 + 1.35, anim: 'idle', time: 0.3, holding: KNIFE, wear: mask() });
      k.player(10, 12, -0.5, { anim: 'idle', time: 0.2, holding: REVOLVER, wear: deerstalker() });
      k.player(-4, 8, 0.4, { anim: 'walk', time: 0.6, holding: null, wear: mask() });
    }
  });

  // ------------------------------------------------- The SS Aurora
  /* The liner side-on from the sea at night, a fog bank rolling in astern
     and an iceberg off the bow; two passengers at the boat-deck rail and an
     officer on the bridge wing. */
  Thumbs.registerWorld('wd_liner', {
    sky: { top: '#060a18', horizon: '#1a2a40', sun: [-0.4, 0.5, -0.3], clouds: 0.3, tint: '#c0d0ff' },
    camera: [[-124, 56, 46], [40, 24, -4], 48],
    build: function (parts, k) {
      k.box([0, -1, 0], [400, 2, 300], '#0a1a2a', { m: 'glass', a: 0.95 });
      // the hull: black above a red boot-top, a white sheer line, portholes
      k.box([-6, 6, 0], [170, 16, 22], '#1a1a1e');
      k.box([-6, 0.4, 0], [171, 2.4, 22.4], '#8a1a1a');
      k.box([84, 7.2, 0], [12, 14.4, 18], '#1a1a1e');
      k.box([93, 8.4, 0], [8, 13, 12], '#1a1a1e');
      k.box([99, 9.6, 0], [5, 12, 6], '#1a1a1e');
      k.box([-96, 7.2, 0], [12, 14, 18], '#1a1a1e');
      k.box([-6, 13.6, 11.02], [170, 0.5, 0.1], '#f2f0ea');
      for (var p = -84; p <= 76; p += 4) {
        k.shape('cyl', [p, 9.2, 11.05], [0.8, 0.12, 0.8], (p / 4) % 3 ? LIT : '#1e2636',
                { m: (p / 4) % 3 ? 'neon' : 'glass', r: [Math.PI / 2, 0, 0] });
      }
      // the white decks, their promenade windows lit
      k.box([-10, 18, 0], [132, 8, 20], '#f2f0ea');
      k.box([-10, 18.6, 10.06], [128, 3.2, 0.12], LIT, { m: 'neon' });
      for (var m = -72; m <= 52; m += 6) k.box([m, 18.6, 10.14], [0.5, 3.4, 0.12], '#f2f0ea');
      k.box([-10, 22.2, 0], [134, 0.4, 21], '#a8784a');
      k.box([-20, 26, 0], [96, 7.6, 16], '#f2f0ea');
      k.box([-20, 26.4, 8.06], [92, 2.6, 0.12], LIT, { m: 'neon' });
      k.box([-20, 30, 0], [98, 0.4, 17], '#a8784a');
      // the bridge, forward, and its wings
      k.box([30, 33, 0], [14, 6, 16], '#f2f0ea');
      k.box([30, 34, 8.06], [12, 2.0, 0.12], '#cfe8ff', { m: 'neon' });
      k.box([30, 36.2, 0], [15, 0.4, 24], '#f2f0ea');
      k.shape('sph', [30, 36.8, 11.6], [0.6, 0.6, 0.6], '#3aff6a', { m: 'neon' });
      // three funnels, buff with black tops
      [-54, -30, -6].forEach(function (fx) {
        k.shape('cyl', [fx, 39, 0], [10, 18, 7], '#d8a040');
        k.shape('cyl', [fx, 50, 0], [10, 4, 7], '#1a1a1e');
      });
      // the lifeboats along the boat deck, under their davits
      [-66, -42, -18, 12].forEach(function (bx) {
        k.box([bx, 32.0, 6.8], [9, 1.8, 2.8], '#f2f0ea');
        k.box([bx, 33.0, 6.8], [9.2, 0.3, 3.0], '#a8784a');
        [-4.4, 4.4].forEach(function (dx) {
          k.box([bx + dx, 33.2, 6.2], [0.3, 6, 0.3], '#5a5e66', { m: 'metal', r: [0.4, 0, 0] });
        });
      });
      // the masts, the wireless aerial between them, their lights
      k.shape('cyl', [70, 34, 0], [0.8, 40, 0.8], '#3a3a3e');
      k.shape('cyl', [-88, 30, 0], [0.8, 32, 0.8], '#3a3a3e');
      k.box([-9, 53.6, 0], [158, 0.12, 0.12], '#5a5e66', { r: [0, 0, -0.04] });
      k.shape('sph', [70, 54.2, 0], [0.9, 0.9, 0.9], '#ffffff', { m: 'neon' });
      // the bow wave, and the wake
      k.box([96, 0.3, 6], [14, 0.4, 3], '#e8f0f8', { a: 0.7, r: [0, -0.4, 0] });
      k.box([-110, 0.3, 0], [30, 0.4, 16], '#c8d8e8', { a: 0.4 });
      // the iceberg dead ahead, fog banks closing in either side
      k.attach(176, 0, -6, 0.4, [
        { t: 'box', p: [0, 11, 0], s: [30, 22, 24], c: '#e8f2fa' },
        { t: 'box', p: [4, 24, 2], s: [16, 12, 14], c: '#dceaf6', r: [0, 0.4, 0.2] },
        { t: 'wedge', p: [-6, 33, 0], s: [9, 10, 11], c: '#f2f8ff' },
        { t: 'box', p: [-14, 5, 8], s: [12, 10, 10], c: '#d0e2f0', r: [0, 0.7, 0] }]);
      for (var f = 0; f < 8; f++) {
        var side = f % 2 ? 1 : -1;
        k.shape('sph', [-40 + f * 34, 12 + (f % 3) * 4, side * (110 + (f % 3) * 20)], [70, 30, 50], '#c8d8e8',
                { a: 0.3 });
      }
      // a passenger at the rail with a candle, somebody coming up behind with
      // a knife; the captain on the bridge wing, looking the other way
      k.player(-62, 3.6, 0.2, { y: 30.2, anim: 'idle', time: 0.4, holding: CANDLE, wear: topHat('#c8a040') });
      k.player(-66, -3, 1.1, { y: 30.2, anim: 'walk', time: 0.2, holding: KNIFE, wear: bowler(), face: 'face_angry' });
      k.player(30, 10.4, 1.57, { y: 36.4, anim: 'idle', time: 0.2, holding: null, wear: captainCap() });
    }
  });
})(window);
