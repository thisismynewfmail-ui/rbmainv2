/* Plunder Bay's world-page pictures: the card, and each of the four
   islands, built from the same blocks the game draws with
   (Thumbs.registerWorld; loaded by thumbs.js the first time one is asked
   for).  Every pirate wears the classic default -- yellow skin, red torso,
   blue legs -- with a bandana in their crew's colour, the Scarlet
   Corsairs' or the Azure Buccaneers', and a cutlass, a flintlock or a
   chest in hand. */
(function (global) {
  'use strict';
  var Thumbs = global.Thumbs;
  if (!Thumbs || !Thumbs.registerWorld) return;

  var RED = '#c8302a', BLUE = '#2a6ab8', GOLD = '#e8b830';
  var SAILS = { red: '#b8282a', blue: '#2a5aa8' };

  var CUTLASS = { data: { parts: [
    { t: 'box', p: [0, 0.04, 1.2], s: [0.12, 0.42, 2.0], c: '#dfe4ea', m: 'metal' },
    { t: 'box', p: [0, 0.2, 2.36], s: [0.1, 0.32, 0.6], c: '#dfe4ea', m: 'metal', r: [-0.4, 0, 0] },
    { t: 'sph', p: [0, -0.08, 0.12], s: [0.56, 0.5, 0.4], c: GOLD, m: 'metal' },
    { t: 'cyl', p: [0, 0, -0.3], s: [0.18, 0.6, 0.18], c: '#4a2a18', r: [Math.PI / 2, 0, 0] }] } };
  var PISTOL = { data: { parts: [
    { t: 'cyl', p: [0, 0.12, 0.78], s: [0.18, 1.5, 0.18], c: '#4a4e56', m: 'metal', r: [Math.PI / 2, 0, 0] },
    { t: 'box', p: [0, 0.04, 0.22], s: [0.2, 0.24, 0.9], c: '#6a3a1e' },
    { t: 'box', p: [0, -0.28, -0.3], s: [0.2, 0.62, 0.32], c: '#6a3a1e', r: [-0.5, 0, 0] },
    { t: 'sph', p: [0, -0.56, -0.46], s: [0.28, 0.28, 0.28], c: GOLD, m: 'metal' }] } };
  var CHEST = { data: { parts: [
    { t: 'box', p: [-0.75, -0.25, 0.75], s: [1.9, 1.1, 1.3], c: '#7a4a26' },
    { t: 'box', p: [-0.75, 0.48, 0.75], s: [1.96, 0.42, 1.36], c: '#8a5a2e' },
    { t: 'box', p: [-1.35, 0.1, 0.75], s: [0.16, 1.5, 1.4], c: GOLD, m: 'metal' },
    { t: 'box', p: [-0.15, 0.1, 0.75], s: [0.16, 1.5, 1.4], c: GOLD, m: 'metal' }] } };
  var SPADE = { data: { parts: [
    { t: 'box', p: [0, 0, 0.9], s: [0.16, 0.16, 2.6], c: '#7a4a28' },
    { t: 'box', p: [0, 0, 2.4], s: [0.7, 0.08, 0.8], c: '#9aa0a8', m: 'metal' }] } };

  /* a crew bandana, knotted at the back, or a captain's tricorn (the
     player's own space: +Z ahead, the top of the head at 5.9) */
  function bandana(colour) {
    return [{ t: 'sph', p: [0, 5.55, 0], s: [2.3, 1.1, 2.3], c: colour },
            { t: 'box', p: [0, 5.3, -1.2], s: [0.5, 0.5, 0.4], c: colour },
            { t: 'box', p: [0.2, 4.9, -1.35], s: [0.3, 0.8, 0.12], c: colour, r: [0.3, 0, 0.2] }];
  }
  function tricorn(colour) {
    return [{ t: 'tricorn', p: [0, 5.75, 0], s: [3.4, 2.2, 3.4], c: '#1a1a22' },
            { t: 'cyl', p: [0, 5.95, 0], s: [1.95, 0.2, 1.95], c: colour },
            { t: 'skullface', p: [0, 6.5, 1.15], s: [0.55, 0.55, 0.55], c: '#f4f0e0' }];
  }
  function pirate(k, x, z, yaw, team, o) {
    o = o || {};
    var colour = team === 'blue' ? BLUE : RED;
    k.player(x, z, yaw, { y: o.y || 0, anim: o.anim || 'idle', time: o.time === undefined ? 0.3 : o.time,
                          holding: o.holding === undefined ? CUTLASS : o.holding,
                          wear: o.captain ? tricorn(colour) : bandana(colour), face: o.face, pitch: o.pitch });
  }

  // ------------------------------------------------------------ pieces
  function sea(k, y, colour, size) {
    k.box([0, y - 4, -20], [size || 260, 8, size || 220], colour || '#2a8aa8', { m: 'glass', a: 0.82 });
  }
  function sand(k, x, y, z, w, d, colour) {
    k.box([x, y - 1, z], [w, 2, d], colour || '#e8d098');
  }
  function palm(k, x, y, z, h, lean, leaf) {
    var n = 5;
    for (var s = 0; s < n; s++) {
      var f = (s + 0.5) / n;
      k.shape('cyl', [x + lean * f * f, y + h * f, z], [1.1 - s * 0.08, h / n + 0.2, 1.1 - s * 0.08],
              s % 2 ? '#7a5a34' : '#6a4a2a');
    }
    var tx = x + lean, ty = y + h;
    for (var i = 0; i < 7; i++) {
      var a = i * Math.PI * 2 / 7;
      k.box([tx + Math.sin(a) * 2.6, ty - 0.6, z + Math.cos(a) * 2.6], [0.6, 0.18, 5.4], leaf || '#2a8a3a',
            { r: [0.45, a, 0] });
    }
    k.shape('sph', [tx + 0.6, ty - 0.8, z + 0.4], [0.9, 0.9, 0.9], '#5a3a1a');
    k.shape('sph', [tx - 0.5, ty - 0.9, z - 0.4], [0.9, 0.9, 0.9], '#5a3a1a');
  }
  function chest(k, x, y, z, yaw, open) {
    var c = Math.cos(yaw), s = Math.sin(yaw);
    function at(dx, dz) { return [x + dx * c + dz * s, z - dx * s + dz * c]; }
    k.box([x, y + 0.75, z], [3.0, 1.5, 2.0], '#7a4a26', { r: [0, yaw, 0] });
    [-1, 1].forEach(function (side) {
      var p = at(side * 1.0, 0);
      k.box([p[0], y + 0.9, p[1]], [0.22, 1.7, 2.1], GOLD, { r: [0, yaw, 0], m: 'metal' });
    });
    if (open) {
      var lid = at(0, -1.1);
      k.box([lid[0], y + 2.3, lid[1]], [3.05, 1.6, 0.4], '#8a5a2e', { r: [0, yaw, 0] });
      for (var i = 0; i < 9; i++) {
        var q = at(-1.1 + (i % 3) * 1.1, -0.6 + Math.floor(i / 3) * 0.6);
        k.shape('doubloon', [q[0], y + 1.55 + (i % 2) * 0.12, q[1]], [0.75, 0.75, 0.75], '#ffd040',
                { m: 'metal', r: [Math.PI / 2 - 0.2 * (i % 3), yaw + i, 0] });
      }
      k.shape('gem', [at(0.4, 0.2)[0], y + 1.6, at(0.4, 0.2)[1]], [1.0, 1.0, 1.0], '#ff3a5a', { m: 'glass', a: 0.9 });
    } else {
      k.box([x, y + 1.7, z], [3.05, 0.5, 2.05], '#8a5a2e', { r: [0, yaw, 0] });
    }
  }
  function coins(k, x, y, z, n, spread) {
    for (var i = 0; i < n; i++) {
      var a = i * 2.4, r = (spread || 2) * ((i * 0.37) % 1);
      k.shape('doubloon', [x + Math.sin(a) * r, y + 0.08, z + Math.cos(a) * r], [0.8, 0.8, 0.8], '#ffd040',
              { m: 'metal', r: [0, a, 0] });
    }
  }
  function xmark(k, x, y, z) {
    k.box([x, y + 0.06, z], [5, 0.1, 0.8], '#c81e1e', { r: [0, Math.PI / 4, 0] });
    k.box([x, y + 0.07, z], [5, 0.1, 0.8], '#c81e1e', { r: [0, -Math.PI / 4, 0] });
  }
  /* a galleon broadside on, its bow towards +x (or -x with face -1),
     waterline at y */
  function galleon(k, x, y, z, team, face, s) {
    s = s || 1;
    face = face || 1;
    var stripe = team === 'blue' ? BLUE : RED, sail = SAILS[team];
    k.box([x, y + 2.5 * s, z], [40 * s, 7 * s, 11 * s], '#5a3a20');
    k.box([x + face * 22 * s, y + 3.4 * s, z], [6 * s, 5.4 * s, 7 * s], '#5a3a20');
    k.box([x, y + 3.8 * s, z + 5.6 * s], [40 * s, 1.0 * s, 0.2 * s], stripe);
    k.box([x, y + 3.8 * s, z - 5.6 * s], [40 * s, 1.0 * s, 0.2 * s], stripe);
    k.box([x - face * 15 * s, y + 8 * s, z], [10 * s, 4 * s, 11 * s], '#4a2e18');
    for (var w = 0; w < 5; w++) k.box([x - 12 * s + w * 6 * s, y + 2.4 * s, z + 5.62 * s], [1.4 * s, 1.0 * s, 0.1 * s], '#ffd890', { m: 'neon' });
    [[-8, 26], [4, 32], [15, 24]].forEach(function (m, i) {
      var mx = x + face * m[0] * s;
      k.shape('cyl', [mx, y + 6 * s + m[1] * s / 2, z], [0.8 * s, m[1] * s, 0.8 * s], '#3a2412');
      k.box([mx, y + 6 * s + m[1] * s * 0.62, z], [0.4 * s, 9 * s, 12 * s - i * s], sail);
      k.box([mx, y + 6 * s + m[1] * s * 0.3, z], [0.4 * s, 7 * s, 13 * s - i * s], sail);
    });
    k.box([x + face * 4 * s, y + 6 * s + 32 * s + 1.4 * s, z + 2 * s], [0.12 * s, 2.6 * s, 3.8 * s], '#111111');
    k.shape('skullface', [x + face * 4 * s + 0.1 * face, y + 6 * s + 32 * s + 1.6 * s, z + 2 * s], [1.4 * s, 1.4 * s, 1.4 * s],
            '#f4f0e0', { r: [0, face * Math.PI / 2, 0] });
  }
  function idol(k, x, y, z) {
    k.box([x, y + 1.2, z], [4.2, 2.4, 4.2], '#6a6458');
    k.box([x, y + 2.6, z], [1.6, 0.4, 1.2], '#b88a20', { m: 'metal' });
    k.box([x, y + 3.6, z], [1.2, 1.8, 0.9], GOLD, { m: 'metal' });
    k.box([x, y + 5.0, z], [1.4, 1.1, 1.1], GOLD, { m: 'metal' });
    k.box([x - 0.3, y + 5.1, z + 0.57], [0.26, 0.2, 0.06], '#ff2a2a', { m: 'neon' });
    k.box([x + 0.3, y + 5.1, z + 0.57], [0.26, 0.2, 0.06], '#ff2a2a', { m: 'neon' });
    k.shape('cyl', [x, y + 14, z], [2.4, 20, 2.4], '#ffcf30', { m: 'neon', a: 0.22 });
  }
  function tentacle(k, x, y, z, h, lean, turn) {
    var n = 9;
    for (var s = 0; s < n; s++) {
      var f = (s + 0.5) / n, bend = lean * f * f;
      var px = x + Math.sin(turn) * bend * h * 0.6, pz = z + Math.cos(turn) * bend * h * 0.6;
      var rad = 2.4 * (1 - f) + 0.5;
      k.shape('sph', [px, y + h * f * (1 - 0.3 * f * Math.abs(lean)), pz], [rad, h / n * 1.5, rad], s % 2 ? '#7a3a9a' : '#8a4aaa');
      if (s % 2 === 0 && s < n - 2) {
        k.shape('sph', [px + Math.cos(turn) * rad * 0.42, y + h * f * (1 - 0.3 * f * Math.abs(lean)), pz - Math.sin(turn) * rad * 0.42],
                [rad * 0.34, rad * 0.34, rad * 0.34], '#f0a8c8');
      }
    }
  }
  /* a redcoat of the garrison: white breeches, red coat, white cross-belts,
     a tricorn, a musket shouldered or levelled */
  function redcoat(k, x, y, z, yaw, aiming) {
    var parts = [
      { t: 'box', p: [-0.55, 1.0, 0], s: [0.95, 2.0, 1.0], c: '#f0ece0' },
      { t: 'box', p: [0.55, 1.0, 0], s: [0.95, 2.0, 1.0], c: '#f0ece0' },
      { t: 'box', p: [-0.55, 0.15, 0.1], s: [1.0, 0.3, 1.3], c: '#1a1a1a' },
      { t: 'box', p: [0.55, 0.15, 0.1], s: [1.0, 0.3, 1.3], c: '#1a1a1a' },
      { t: 'box', p: [0, 3.1, 0], s: [2.6, 2.3, 1.1], c: '#c81e1e' },
      { t: 'box', p: [0, 2.0, 0], s: [2.7, 0.6, 1.15], c: '#c81e1e' },
      { t: 'box', p: [0, 3.2, 0.58], s: [0.24, 3.0, 0.05], c: '#f4f0e0', r: [0, 0, 0.7] },
      { t: 'box', p: [0, 3.2, 0.58], s: [0.24, 3.0, 0.05], c: '#f4f0e0', r: [0, 0, -0.7] },
      { t: 'box', p: [0, 4.75, 0], s: [1.3, 1.2, 1.2], c: '#f5cd30' },
      { t: 'box', p: [0, 4.95, -0.62], s: [1.0, 0.5, 0.2], c: '#e8e8e0' },
      { t: 'tricorn', p: [0, 5.4, 0], s: [2.6, 1.6, 2.6], c: '#1a1a22' },
      { t: 'box', p: [0, 5.45, 0], s: [1.3, 0.12, 1.25], c: GOLD }
    ];
    if (aiming) {
      parts.push({ t: 'box', p: [0.9, 3.7, 0.9], s: [0.7, 0.7, 1.8], c: '#c81e1e' });
      parts.push({ t: 'box', p: [-0.6, 3.7, 1.1], s: [0.7, 0.7, 1.6], c: '#c81e1e' });
      parts.push({ t: 'box', p: [0.4, 3.95, 2.2], s: [0.3, 0.3, 3.6], c: '#5a3a22' });
      parts.push({ t: 'box', p: [0.4, 4.05, 4.2], s: [0.16, 0.16, 1.2], c: '#8a8e96', m: 'metal' });
    } else {
      parts.push({ t: 'box', p: [-1.55, 3.4, 0], s: [0.7, 2.1, 0.8], c: '#c81e1e' });
      parts.push({ t: 'box', p: [1.55, 3.4, 0], s: [0.7, 2.1, 0.8], c: '#c81e1e' });
      parts.push({ t: 'box', p: [1.6, 4.6, -0.3], s: [0.28, 4.4, 0.28], c: '#5a3a22', r: [0, 0, 0.12] });
    }
    k.attach(x, y, z, yaw, parts);
  }
  function house(k, x, z, w, d, h, colour, roof) {
    k.box([x, h / 2, z], [w, h, d], colour);
    k.shape('wedge', [x, h + 1.6, z + d / 4], [w + 1, 3.2, d / 2 + 0.6], roof || '#8a4a3a');
    k.shape('wedge', [x, h + 1.6, z - d / 4], [w + 1, 3.2, d / 2 + 0.6], roof || '#8a4a3a', { r: [0, Math.PI, 0] });
    for (var i = 0; i < 2; i++) {
      for (var j = 0; j < Math.floor(w / 4); j++) {
        k.box([x - w / 2 + 2.2 + j * 4, 3 + i * 4.4, z + d / 2 + 0.05], [1.8, 2.4, 0.1], '#4a6a8a', { m: 'glass' });
      }
    }
  }

  /* a rock of stacked blocks, its top greened over */
  function crag(k, x, z, w, d, h, rock, top) {
    k.box([x, h * 0.3, z], [w, h * 0.6, d], rock || '#6a5a4a');
    k.box([x + w * 0.08, h * 0.75, z - d * 0.06], [w * 0.82, h * 0.3, d * 0.84], '#7a6a58');
    k.box([x + w * 0.04, h * 0.93, z - d * 0.04], [w * 0.86, h * 0.08, d * 0.88], top || '#3a7a3a');
    for (var v = 0; v < 4; v++) {
      k.box([x - w * 0.36 + v * w * 0.24, h * 0.72, z + d / 2 + 0.06], [0.5, h * 0.36, 0.12], '#2f6a2f');
    }
  }
  function barrel(k, x, y, z) {
    k.shape('cask', [x, y, z], [2.0, 2.6, 2.0], '#7a4a28');
    k.shape('cyl', [x, y + 0.7, z], [2.06, 0.14, 2.06], '#3a3a3a', { m: 'metal' });
    k.shape('cyl', [x, y + 1.9, z], [2.06, 0.14, 2.06], '#3a3a3a', { m: 'metal' });
  }
  function rowboat(k, x, y, z, yaw) {
    k.box([x, y + 0.6, z], [3.2, 1.2, 8], '#7a5030', { r: [0, yaw, 0] });
    k.box([x, y + 1.25, z], [2.4, 0.2, 7], '#5a3a20', { r: [0, yaw, 0] });
  }

  // ------------------------------------------------------------ card
  /* The beach between the two ships: a chest just dug up and spilling
     gold, a Corsair making off with another while a Buccaneer captain
     draws a bead on her and a Corsair charges him, cutlass up; a second
     Buccaneer digging at an X, and the cursed idol glowing on its altar
     under the palms. */
  Thumbs.registerWorld('plunder_bay', {
    sky: { top: '#3f86d4', horizon: '#f4dcb0', sun: [0.55, 0.42, 0.3], clouds: 0.5, tint: '#fff2dc' },
    camera: [[30, 13, 38], [0, 5, -6], 52],
    build: function (parts, k) {
      sea(k, -0.6, '#2a8aa8', 320);
      sand(k, 0, 0.4, -6, 84, 44, '#e8d098');
      sand(k, 0, 0.12, 20, 100, 8, '#c8a868');
      k.box([0, -0.25, 25], [110, 0.3, 4], '#b89a5a');
      galleon(k, -46, -0.4, -36, 'red', 1, 0.75);
      galleon(k, 46, -0.4, -40, 'blue', -1, 0.75);
      // the idol on its stepped altar, palms either side
      k.box([0, 1.0, -22], [12, 1.2, 10], '#7a7468');
      k.box([0, 2.2, -22], [8, 1.2, 7], '#8a8478');
      idol(k, 0, 2.2, -22);
      palm(k, -14, 0.4, -20, 13, 3);
      palm(k, -22, 0.4, -14, 11, -2, '#3a8a3a');
      palm(k, 16, 0.4, -22, 14, -3);
      palm(k, 30, 0.4, -10, 10, 2, '#3a8a3a');
      crag(k, -32, -24, 10, 8, 6);
      barrel(k, 24, 0.4, 6);
      barrel(k, 26.4, 0.4, 7.4);
      rowboat(k, -30, 0.1, 18, 0.5);
      // the dig: an open chest spilling gold, the spade beside it
      chest(k, 2, 0.4, 2, 0.5, true);
      coins(k, 4.4, 0.4, 5.2, 10, 3.2);
      k.box([-1.6, 2.0, 4.4], [0.18, 3.2, 0.18], '#7a4a28', { r: [0.25, 0, 0.3] });
      k.box([-2.1, 0.7, 4.6], [0.9, 1.0, 0.1], '#9aa0a8', { m: 'metal', r: [0.25, 0, 0.3] });
      k.shape('sparkle', [2, 4.6, 2], [1.8, 1.8, 1.8], '#fff3b0', { m: 'neon' });
      xmark(k, 16, 0.4, -4);
      // the crews at it
      pirate(k, -12, 4, -1.1, 'red', { y: 0.4, anim: 'run', time: 0.3, holding: CHEST });
      pirate(k, 12, 10, -1.9, 'blue', { y: 0.4, anim: 'idle', time: 0.2, holding: PISTOL, captain: true, face: 'face_angry' });
      pirate(k, 6, 12, 1.4, 'red', { y: 0.4, anim: 'run', time: 0.7, face: 'face_angry' });
      pirate(k, 18, -2, -2.4, 'blue', { y: 0.4, anim: 'walk', time: 0.6, holding: SPADE });
      pirate(k, -4, -10, 0.4, 'red', { y: 0.4, anim: 'run', time: 0.1, captain: true });
    }
  });

  // ------------------------------------------------- Skull Cove
  /* The skull in the rock, its eyes lit and its mouth a cave, between the
     cliffs over the lagoon -- the tide half out, the sunken sloop's deck
     showing, a Buccaneer wading for the chest on the bottom -- and a
     Corsair on the beach under the palms who has just dug one up. */
  Thumbs.registerWorld('pb_skullcove', {
    sky: { top: '#2a3a7a', horizon: '#ffb07a', sun: [0.6, 0.25, -0.4], clouds: 0.5, tint: '#ffd8b0' },
    camera: [[34, 15, 44], [0, 7, -14], 50],
    build: function (parts, k) {
      sea(k, -2.2, '#2a9aaa', 300);
      // the lagoon floor and its banks stepping down, the beaches round it
      k.box([0, -4.5, -8], [60, 1, 38], '#c8b07a');
      k.box([0, -3.2, 12], [64, 1, 4], '#d8c088');
      sand(k, -42, 0.4, -2, 30, 74);
      sand(k, 42, 0.4, -2, 30, 74);
      sand(k, 0, 0.4, 24, 120, 18);
      k.box([0, 0.1, 15], [64, 0.6, 2], '#c8a868');
      // the skull: a dome of bone, two eyes lit red, the cave mouth
      k.shape('sph', [0, 14, -40], [40, 34, 24], '#d8cfb8');
      k.box([0, 6, -34], [26, 12, 14], '#b8ae96');
      k.shape('sph', [-7, 17, -28.5], [7, 6.4, 2], '#2a2420');
      k.shape('sph', [7, 17, -28.5], [7, 6.4, 2], '#2a2420');
      k.shape('sph', [-7, 17, -28.0], [3, 3, 1], '#ff2a1a', { m: 'neon' });
      k.shape('sph', [7, 17, -28.0], [3, 3, 1], '#ff2a1a', { m: 'neon' });
      k.shape('cone', [0, 10, -28], [3, 4, 2], '#2a2420', { r: [Math.PI, 0, 0] });
      k.box([0, 2.5, -26.9], [12, 5, 0.5], '#2a2420');
      for (var t = 0; t < 5; t++) k.box([-5 + t * 2.5, 4.6, -26.6], [1.6, 1.4, 0.6], '#f0e8d8');
      // the cliffs either side, layered, green on top, vines down them
      crag(k, -32, -40, 26, 20, 22);
      crag(k, 32, -40, 26, 20, 24, '#5a4a40');
      crag(k, -50, -22, 14, 16, 14, '#5a4a40');
      crag(k, 52, -20, 14, 14, 12);
      // the sloop on the lagoon floor, its deck clear of the water
      k.box([-12, -3.2, -8], [5, 3, 14], '#4a3020', { r: [0, 0.35, 0.1] });
      k.box([-12, -1.5, -8], [4.4, 0.4, 13], '#6a4a2a', { r: [0, 0.35, 0.1] });
      k.box([-14.2, -0.8, -13.6], [4, 2, 3], '#4a3020', { r: [0, 0.35, 0.1] });
      k.shape('cyl', [-11.6, 3, -7], [0.6, 9, 0.6], '#3a2412', { r: [0.25, 0, 0.35] });
      chest(k, 8, -4, -6, -0.4, false);
      k.shape('sparkle', [8, -0.6, -6], [1.4, 1.4, 1.4], '#fff3b0', { m: 'neon' });
      pirate(k, 11, -3, -2.2, 'blue', { y: -4, anim: 'walk', time: 0.4 });
      // the beach: palms, an X dug up, a Corsair with a spade, the camp
      palm(k, -30, 0.4, 14, 14, 3);
      palm(k, -38, 0.4, 2, 12, 2, '#3a8a3a');
      palm(k, 32, 0.4, 8, 13, -3, '#3a8a3a');
      palm(k, 44, 0.4, -6, 12, -2);
      xmark(k, -16, 0.4, 22);
      chest(k, -20, 0.4, 21, 0.4, true);
      pirate(k, -13, 20, -1.6, 'red', { y: 0.4, anim: 'idle', time: 0.6, holding: SPADE, captain: true });
      k.shape('cone', [-44, 3.4, 26], [8, 6.8, 7], '#e8dcc0');
      barrel(k, 34, 0.4, 16);
      barrel(k, 36.2, 0.4, 17.6);
      galleon(k, -66, -2.2, 18, 'red', 1, 0.6);
    }
  });

  // ------------------------------------------------- Coral Reef
  /* The kraken coming up round the wreck in the lagoon, a Corsair firing
     at it from the boardwalk, a Buccaneer running the boardwalk with a
     jewel, the stilt huts and the lighthouse on its rock. */
  Thumbs.registerWorld('pb_reef', {
    sky: { top: '#3a8ae8', horizon: '#c8f0ff', sun: [0.4, 0.7, 0.3], clouds: 0.45, tint: '#ffffff' },
    camera: [[38, 20, 46], [0, 6, -10], 48],
    build: function (parts, k) {
      sea(k, -1, '#2ab8c8', 280);
      k.box([0, -5.5, -10], [200, 1, 160], '#e8d8a8');
      // coral heads under the water
      [[-14, 6, '#ff7a6a'], [12, 10, '#ffb84a'], [20, -2, '#c86aff'], [-24, -8, '#ff5a8a']].forEach(function (c) {
        k.shape('sph', [c[0], -4.6, c[1]], [4, 2.4, 3.4], c[2]);
      });
      // the wreck, run aground and listing
      k.box([2, -1, -22], [30, 8, 10], '#4a3020', { r: [0, 0.2, 0.15] });
      k.box([2, 3.6, -22], [26, 0.6, 9], '#6a4a2a', { r: [0, 0.2, 0.15] });
      k.box([3, 1.2, -16.9], [26, 1.0, 0.2], '#c8302a', { r: [0, 0.2, 0.15] });
      k.box([-14, 1, -22], [6, 10, 10], '#3a2412', { r: [0, 0.2, 0.15] });
      k.shape('cyl', [-4, 12, -22], [0.9, 18, 0.9], '#3a2412', { r: [0, 0, 0.2] });
      k.box([-6, 15, -22], [0.4, 7, 10], '#e8e0d0', { r: [0, 0.2, 0.2], a: 0.9 });
      // the kraken's arms rising round it
      tentacle(k, -14, -1, -12, 18, 0.8, 0.6);
      tentacle(k, 16, -1, -10, 20, -0.6, -0.4);
      tentacle(k, 22, -1, -28, 16, 0.4, 2.6);
      tentacle(k, -20, -1, -30, 14, -0.5, 2.2);
      k.shape('torus', [-14, -0.8, -12], [8, 0.8, 8], '#e0f8ff', { a: 0.6 });
      k.shape('torus', [16, -0.8, -10], [8, 0.8, 8], '#e0f8ff', { a: 0.6 });
      // the boardwalk, a stilt hut on its islet
      k.box([0, 1.1, 14], [80, 0.4, 5], '#9a7a4a');
      for (var p = 0; p < 10; p++) {
        k.shape('cyl', [-36 + p * 8, -2, 11.8], [0.6, 6, 0.6], '#6a4a2a');
        k.shape('cyl', [-36 + p * 8, -2, 16.2], [0.6, 6, 0.6], '#6a4a2a');
      }
      pirate(k, -6, 14, -2.6, 'red', { y: 1.3, anim: 'idle', time: 0.2, holding: PISTOL, captain: true });
      k.shape('sph', [-8.4, 4.8, 11.6], [1.8, 1.4, 1.8], '#f0f0f0', { a: 0.7 });
      pirate(k, 14, 14, -1.57, 'blue', { y: 1.3, anim: 'run', time: 0.5 });
      k.shape('gem', [14, 7.6, 14], [1.1, 1.1, 1.1], '#3ae08a', { m: 'glass', a: 0.9 });
      k.shape('cyl', [42, 0, 2], [16, 1.6, 12], '#f0dca0');
      for (var st = 0; st < 4; st++) k.shape('cyl', [39 + (st % 2) * 6, 1.5, -1 + Math.floor(st / 2) * 6], [0.6, 3, 0.6], '#6a4a2a');
      k.box([42, 6, 2], [8, 5, 7], '#c8a878');
      k.shape('cone', [42, 10.5, 2], [11, 4, 10], '#d8c080');
      palm(k, 36, 0.8, 6, 11, 2);
      // giant clams on the sand under the water, one open on a pearl
      [[-26, 2, 0.2], [8, 4, 0.6], [26, -12, 0.1]].forEach(function (c, i) {
        k.shape('sph', [c[0], -5, c[1]], [4, 1.6, 3.2], '#a8d0d8');
        k.shape('sph', [c[0], -4.2 + (i === 1 ? 0.8 : 0), c[1] - (i === 1 ? 0.6 : 0)], [4, 1.4, 3.2], '#b8e0e8',
                { r: [i === 1 ? -0.6 : 0, 0, 0] });
        if (i === 1) k.shape('sph', [c[0], -3.9, c[1]], [1.2, 1.2, 1.2], '#f8f4f0', { m: 'metal' });
      });
      // the lighthouse on its rock
      k.shape('sph', [-44, -1, -40], [16, 8, 14], '#6a6a72');
      for (var b = 0; b < 6; b++) {
        k.shape('cyl', [-44, 3 + b * 3.2, -40], [5 - b * 0.3, 3.2, 5 - b * 0.3], b % 2 ? '#f4f4f4' : '#c81e1e');
      }
      k.shape('cyl', [-44, 23.4, -40], [3.4, 2.4, 3.4], '#fff3b0', { m: 'neon' });
      k.shape('cone', [-44, 26, -40], [4.4, 2.8, 4.4], '#2a2a30');
    }
  });

  // ------------------------------------------------- Port Royale
  /* The market square under the fort: redcoats marching out, one of them
     levelling his musket at a Corsair running with a gold bar, a
     Buccaneer ducked behind the barrels, the colourful houses round the
     square and the governor's colours flying on the fort. */
  Thumbs.registerWorld('pb_royale', {
    sky: { top: '#4a8ad8', horizon: '#e8f0f4', sun: [0.4, 0.65, 0.4], clouds: 0.5, tint: '#ffffff' },
    camera: [[40, 22, 46], [0, 6, -8], 48],
    build: function (parts, k) {
      k.box([0, -0.5, 0], [160, 1, 120], '#9a9488', { dec: 'pb_cobbles', dw: 1 });
      // the fort on the hill behind
      k.box([0, 4, -46], [120, 8, 30], '#7a9a5a');
      k.box([0, 12, -40], [60, 8, 4], '#b8b0a0');
      for (var c = 0; c < 12; c++) k.box([-27.5 + c * 5, 16.8, -40], [2.6, 1.6, 4], '#b8b0a0');
      k.box([-32, 14, -40], [8, 14, 8], '#a8a090');
      k.box([32, 14, -40], [8, 14, 8], '#a8a090');
      k.box([0, 10, -37.9], [6, 6, 0.4], '#4a3a2a');
      k.shape('cyl', [0, 24, -44], [0.6, 16, 0.6], '#e8e8e8');
      k.box([2.4, 30, -44], [4.2, 2.8, 0.12], '#1a2a5a');
      k.shape('cyl', [2.4, 30, -43.9], [1.4, 0.1, 1.4], '#e8c840', { r: [Math.PI / 2, 0, 0] });
      // the houses round the square
      house(k, -36, -12, 14, 10, 12, '#e8c878');
      house(k, -36, 6, 14, 10, 10, '#8ac0d8', '#6a3a2a');
      house(k, 38, -12, 14, 10, 14, '#d88a6a');
      house(k, 38, 6, 14, 10, 11, '#c8d88a', '#6a3a2a');
      // the fountain in the middle
      k.shape('cyl', [0, 0.8, 0], [10, 1.6, 10], '#c8c0b0');
      k.shape('cyl', [0, 1.5, 0], [8.4, 0.2, 8.4], '#4ab8d8', { m: 'glass', a: 0.8 });
      k.shape('cyl', [0, 3.6, 0], [1.4, 4, 1.4], '#c8c0b0');
      k.shape('cyl', [0, 5.8, 0], [4, 0.6, 4], '#c8c0b0');
      // the redcoats coming down out of the fort
      redcoat(k, 10, 0, -22, Math.PI * 0.95, false);
      redcoat(k, 14, 0, -26, Math.PI * 0.95, false);
      redcoat(k, 6, 0, -14, -2.4, true);
      k.shape('sph', [1.8, 4.2, -10.4], [1.6, 1.4, 1.6], '#f4f4f4', { a: 0.75 });
      // a Corsair running with a gold bar, a Buccaneer behind the barrels
      pirate(k, -12, 8, -1.2, 'red', { anim: 'run', time: 0.35 });
      k.box([-12, 7.0, 8], [1.6, 0.6, 0.8], '#ffc830', { m: 'metal' });
      [[18, 12], [20.4, 12], [19.2, 14.2]].forEach(function (b) {
        k.shape('cask', [b[0], 0, b[1]], [2.2, 2.8, 2.2], '#7a4a28');
      });
      pirate(k, 23, 13, -2.0, 'blue', { anim: 'idle', time: 0.1, holding: PISTOL, captain: true });
      // the church tower over the roofs, a redcoat drummer at the gate
      k.box([-46, 11, -24], [7, 22, 7], '#e8e4d8');
      k.shape('cone', [-46, 25, -24], [7.4, 6, 7.4], '#8a4a3a');
      k.shape('cyl', [-46, 17, -20.4], [2.6, 0.2, 2.6], '#f4f0e0', { r: [Math.PI / 2, 0, 0] });
      redcoat(k, -4, 6, -34, 0.2, false);
      k.shape('cyl', [-4, 9.6, -33], [1.6, 1.2, 1.6], '#f4f0e0', { r: [Math.PI / 2, 0, 0] });
      // a market stall
      k.box([-20, 2, 18], [8, 0.4, 4], '#8a6a44');
      k.box([-20, 5.4, 18], [8.6, 0.3, 4.6], '#e85a4a');
      coins(k, -20, 2.2, 18, 6, 2.4);
    }
  });

  // ------------------------------------------------- Doubloon Isle
  /* The volcano erupting gold behind the stepped temple, the idol shining
     on its top; in front the lava running in its trench under the stone
     bridge, a Corsair hauling a chest across it while a lava bomb comes
     down beside the bridge and a Buccaneer gives chase. */
  Thumbs.registerWorld('pb_doubloon', {
    sky: { top: '#1a0e1e', horizon: '#c85a2a', sun: [0.5, 0.3, -0.5], clouds: 0.55, tint: '#ffb070' },
    camera: [[30, 14, 42], [0, 7, -10], 52],
    build: function (parts, k) {
      // the black sand either side of the trench, the lava down in it
      k.box([0, -0.5, -32], [220, 1, 76], '#2a2624');
      k.box([0, -0.5, 40], [220, 1, 40], '#2a2624');
      k.box([0, -4, 12], [220, 4, 16], '#1e1a18');
      k.box([0, -0.9, 6.1], [220, 0.8, 4.2], '#3a3430');
      k.box([0, -0.9, 17.9], [220, 0.8, 4.2], '#3a3430');
      k.box([0, -1.6, 12], [220, 0.4, 7.6], '#ff6a1a', { m: 'neon' });
      [[-30, 11], [-12, 13.5], [24, 10.8], [40, 12.6]].forEach(function (c) {
        k.shape('cyl', [c[0], -1.38, c[1]], [3.4, 0.2, 2.4], '#b8401a');
      });
      // the stone bridge over it, parapets down both sides
      k.box([0, 0.3, 12], [10, 0.6, 16], '#8a8478');
      k.box([-4.6, 1.5, 12], [0.8, 1.8, 16], '#7a746a');
      k.box([4.6, 1.5, 12], [0.8, 1.8, 16], '#7a746a');
      k.box([0, -1.6, 12], [7, 3, 6], '#6a6460');
      // the volcano: its cone, the crater lit, lava down its face, a plume
      // of smoke and gold flying out of it
      k.shape('cone', [-14, 16, -64], [74, 34, 64], '#2a1e1e');
      // lava brimming over the crater and running down the face
      k.shape('cone', [-14, 27, -64], [27.6, 12, 24], '#ff6a1a', { m: 'neon' });
      k.shape('cyl', [-14, 33.2, -64], [10, 0.6, 9], '#ffb04a', { m: 'neon' });
      k.box([-14, 16.34, -47.64], [3, 46.7, 0.4], '#ff7a1a', { m: 'neon', r: [-0.755, 0, 0] });
      k.box([-14, 4.4, -36.6], [7, 0.4, 5], '#ff8a2a', { m: 'neon' });
      [[0, 40, 12], [-4, 46, 15], [3, 52, 18], [-2, 58, 22]].forEach(function (pl, i) {
        k.shape('sph', [-14 + pl[0], pl[1], -64 + i], [pl[2], pl[2] * 0.7, pl[2]], i % 2 ? '#4a3a36' : '#3a2e2c', { a: 0.9 });
      });
      [[-20, 40, -58], [-6, 44, -54], [-26, 36, -50], [-2, 38, -60], [-12, 48, -56], [4, 34, -48], [-30, 30, -46],
       [8, 42, -58]].forEach(function (c, i) {
        k.shape('doubloon', c, [2.6, 2.6, 2.6], '#ffd040', { m: 'metal', r: [i * 0.7, i, 0] });
      });
      // the stepped temple, the idol on top
      for (var t = 0; t < 4; t++) {
        k.box([22, 1.6 + t * 3.2, -24], [26 - t * 6, 3.2, 22 - t * 5], t % 2 ? '#6a6454' : '#5a5444',
              { dec: 'pb_glyphs', dw: 1 });
      }
      k.box([22, 3.4, -12.6], [6, 6.8, 0.6], '#3a342a');
      idol(k, 22, 12.8, -24);
      // jungle round it
      [[-34, -14], [-42, 0], [42, -6], [46, -20], [38, -34], [-30, -28]].forEach(function (p, i) {
        palm(k, p[0], 0, p[1], 10 + (i % 3) * 2, (i % 2 ? 2 : -2), '#2a6a2a');
      });
      // a Corsair hauling a chest over the bridge, a lava bomb coming down
      // beside it, its ring on the sand, a Buccaneer on his heels
      pirate(k, 0, 13, 0.0, 'red', { y: 0.6, anim: 'run', time: 0.4, holding: CHEST });
      pirate(k, -6, 24, 0.5, 'blue', { y: 0, anim: 'run', time: 0.8, face: 'face_angry' });
      k.shape('sph', [16, 12, 27], [2.6, 2.4, 2.6], '#3a1a10');
      k.shape('sph', [15.6, 12.6, 27.6], [1.6, 1.4, 1.6], '#ff8a2a', { m: 'neon' });
      [[17.0, 13.6, 26.2, 1.1], [17.9, 15.0, 25.4, 0.8], [18.7, 16.3, 24.7, 0.55]].forEach(function (f) {
        k.shape('sph', [f[0], f[1], f[2]], [f[3], f[3], f[3]], '#ffb04a', { m: 'neon' });
      });
      k.shape('torus', [14, 0.1, 31], [12, 0.6, 12], '#ff6a1a', { m: 'neon', a: 0.8 });
      k.shape('cyl', [14, 0.06, 31], [6, 0.06, 6], '#ff6a1a', { m: 'neon', a: 0.45 });
      coins(k, 18, 0, 34, 7, 3);
    }
  });
})(window);
