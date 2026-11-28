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

  // ------------------------------------------------ Whalebone Atoll
  function whaleRib(k, z, reach, peak, side, colour) {
    var p0 = [3.6, 4.6], p1 = [reach * 0.42, peak * 1.6], p2 = [reach, 3.2];
    var prev = p0;
    for (var i = 1; i <= 10; i++) {
      var u = i / 10;
      var x = (1 - u) * (1 - u) * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0];
      var y = (1 - u) * (1 - u) * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1];
      var ang = Math.atan2(y - prev[1], x - prev[0]);
      k.box([side * (prev[0] + x) / 2, (prev[1] + y) / 2, z], [Math.hypot(x - prev[0], y - prev[1]) + 0.4, 1.6 - 0.5 * u, 1.9],
            i % 3 ? colour : '#d8cfb4', { r: [0, 0, side > 0 ? ang : Math.PI - ang] });
      prev = [x, y];
    }
    k.box([side * reach, -0.4, z], [1.6, 7.2, 1.9], '#d8cfb4');
  }
  Thumbs.registerWorld('pb_whalebone', {
    sky: { top: '#1468c8', horizon: '#d8f4ff', sun: [0.45, 0.6, 0.35], clouds: 0.45, tint: '#fff8ec' },
    camera: [[30, 21, 46], [0, 6, -8], 54],
    build: function (parts, k) {
      var BONE = '#f0e8d4';
      // the white strand, the turquoise lagoon sunk in it
      k.box([0, -0.5, -52], [260, 1, 36], '#f0e2b4');
      k.box([-72, -0.5, 6], [64, 1, 80], '#f0e2b4');
      k.box([72, -0.5, 6], [64, 1, 80], '#f0e2b4');
      k.box([0, -0.5, 58], [260, 1, 24], '#f0e2b4');
      k.box([0, -4.5, 6], [80, 1, 80], '#e8dcae');
      k.box([0, -2.4, 6], [80, 3.0, 80], '#3ad0d8', { m: 'glass', a: 0.72 });
      [[-30, 12], [26, -18], [14, 30], [-18, -24]].forEach(function (c, i) {
        k.shape('sph', [c[0], -3.2, c[1]], [4, 3, 4], ['#ff7a8a', '#c86aff', '#ffd04a', '#ff9a5a'][i]);
      });
      // the maelstrom turning round the middle of the spine
      [[16, 0.8, '#e8ffff', 0.85], [11, 0.7, '#b8f4f8', 0.8], [7, 0.6, '#ffffff', 0.9], [3.6, 0.5, '#8ae8f0', 0.9]].forEach(function (ring, i) {
        k.shape('torus', [i * 0.6, -0.8, 2 + i * 0.4], [ring[0], ring[1], ring[0] * 0.9], ring[2], { a: ring[3] });
      });
      k.shape('cyl', [1.4, -0.85, 3.2], [3.4, 0.1, 3.0], '#0e4a5a', { a: 0.9 });
      // the spine across it: vertebrae, the discs between, their processes
      for (var v = 0; v < 12; v++) {
        var z = 32 - v * 6;
        k.box([0, 1.0, z], [4.4, 9.6, 4.8], v % 2 ? BONE : '#e4dcc4');
        k.box([0, 6.1, z], [1.0, 0.6, 1.8], '#d8cfb4');
        k.box([0, 0.6, z - 2.9], [3.8, 8.8, 1.0], '#b8ad92');
        k.box([3.8, 5.0, z], [3.2, 0.6, 1.6], '#d8cfb4');
        k.box([-3.8, 5.0, z], [3.2, 0.6, 1.6], '#d8cfb4');
      }
      // the ribs arching over it
      [26, 14, 2, -10, -22].forEach(function (z, i) {
        var sw = Math.sin((i + 0.5) / 5 * Math.PI);
        whaleRib(k, z, 24 + 6 * sw, 14 + 5 * sw, 1, BONE);
        whaleRib(k, z, 24 + 6 * sw, 14 + 5 * sw, -1, BONE);
      });
      // the skull at the far end, its jaw standing up behind it
      k.box([0, 6, -44], [26, 12, 14], BONE);
      k.box([0, 13, -45], [21, 2.4, 11], '#e4dcc4');
      k.box([0, 15, -45.6], [14, 2.0, 7], BONE);
      k.box([-7.5, 8.4, -36.9], [4.4, 2.8, 0.3], '#3a3430');
      k.box([7.5, 8.4, -36.9], [4.4, 2.8, 0.3], '#3a3430');
      k.box([-7.5, 8.4, -36.7], [1.8, 1.2, 0.1], '#ffb84a', { m: 'neon' });
      k.box([7.5, 8.4, -36.7], [1.8, 1.2, 0.1], '#ffb84a', { m: 'neon' });
      k.box([0, 3.2, -36.9], [7, 6.4, 0.3], '#2a2420');
      for (var tooth = 0; tooth < 4; tooth++) {
        k.shape('cone', [-2.4 + tooth * 1.6, 5.6, -36.4], [1.0, 1.6, 1.0], '#fffaf0', { r: [Math.PI, 0, 0] });
      }
      [-1, 1].forEach(function (s) {
        for (var j = 0; j < 9; j++) {
          var u = j / 8;
          k.box([s * (5 - 3.5 * u), 4 + u * 30, -52 - u * 5], [2.4 - u, 4.4, 2.2 - u], j % 2 ? BONE : '#e4dcc4',
                { r: [-0.25 - u * 0.3, 0, s * (0.15 - u * 0.3)] });
          if (j > 1 && j < 8) k.shape('cone', [s * (4 - 3.5 * u), 4 + u * 30, -50.4 - u * 5], [0.8, 1.6, 0.8], '#fffaf0', { r: [Math.PI / 2, 0, 0] });
        }
      });
      // palms on the strand
      [[-48, -40], [44, -42], [-52, 30], [56, 22], [40, 50]].forEach(function (p, i) {
        palm(k, p[0], 0, p[1], 12 + (i % 3) * 2, i % 2 ? 2 : -2, '#2a8a3a');
      });
      // a Corsair running the spine with a jewel, a Buccaneer behind him,
      // treasure thrown out of the whirlpool onto the beach
      pirate(k, 0, 18, 0.15, 'red', { y: 6.4, anim: 'run', time: 0.4,
                                      holding: { data: { parts: [{ t: 'gem', p: [0, 1.2, 0.8], s: [1.6, 1.6, 1.6], c: '#ff3a6a', m: 'glass' }] } } });
      pirate(k, 0, 4, 0.0, 'blue', { y: 6.4, anim: 'run', time: 0.9, face: 'face_angry' });
      [[10, 6, 10, 0], [18, 9, 12, 1], [26, 7, 14, 2], [33, 1.6, 15, 3]].forEach(function (c) {
        k.shape('doubloon', [c[0], c[1], c[2]], [2.0, 2.0, 2.0], '#ffd040', { m: 'metal', r: [c[3] * 0.8, c[3], 0] });
      });
      coins(k, 40, 0, 18, 6, 2.6);
    }
  });

  // ------------------------------------------------ Thunderhead Rock
  Thumbs.registerWorld('pb_thunderhead', {
    sky: { top: '#28243e', horizon: '#8e88a8', sun: [0.25, 0.45, -0.5], clouds: 0.95, tint: '#ccc6ea' },
    camera: [[36, 20, 46], [0, 12, -12], 54],
    build: function (parts, k) {
      var BASALT = ['#3c3c48', '#50505e', '#2c2c36', '#444452'];
      // the turf, the dark sea round it
      k.box([0, -4, 10], [400, 6, 400], '#2a5a6e', { m: 'glass', a: 0.85 });
      k.box([0, -1, 14], [150, 2, 120], '#4a7a44');
      k.box([-40, 0.06, 30], [16, 0.12, 12], '#9a62a8');
      k.box([44, 0.06, 26], [14, 0.12, 10], '#e8b832');
      // the mesa, ribbed in columns, its turfed summit
      k.box([0, 9, -46], [64, 18, 40], '#3c3c48');
      for (var r = 0; r < 14; r++) k.box([-30 + r * 4.6, 8.8, -25.85], [1.0, 17.6, 0.3], r % 2 ? '#50505e' : '#45454f');
      k.box([0, 18.2, -46], [64, 0.4, 40], '#5a8a4e');
      for (var c = 0; c < 9; c++) {
        k.shape('hexprism', [-28 + c * 7, 22 + (c % 3) * 2, -64], [4.4, 8 + (c % 3) * 4, 3.8], BASALT[c % 4]);
      }
      // the lighthouse: white and red, the lamp lit, its beam out over the sea
      k.shape('cyl', [0, 32.4, -50], [8, 28, 8], '#f4f0e8');
      [24, 31, 38].forEach(function (y) { k.shape('cyl', [0, y, -50], [8.3, 3, 8.3], '#c8302a'); });
      k.shape('cyl', [0, 46.6, -50], [11, 0.5, 11], '#3a3a40', { m: 'metal' });
      k.shape('cyl', [0, 49, -50], [5.6, 4.2, 5.6], '#fff4c0', { m: 'neon' });
      k.shape('cone', [0, 52.8, -50], [6.6, 3.4, 6.6], '#c8302a');
      k.shape('cyl', [0, 57.4, -50], [0.3, 6, 0.3], '#3a3a40', { m: 'metal' });
      k.box([30, 49, -36], [80, 5, 1], '#fff2b0', { m: 'neon', a: 0.16, r: [0, -0.5, 0] });
      // the giant's causeway stepping down towards us
      for (var i = -7; i <= 7; i++) {
        for (var j = 0; j < 9; j++) {
          var z = -24.4 + 3.0 * (j + 0.5 * (Math.abs(i) % 2)), x = i * 2.6;
          var h = Math.max(0.6, 16.6 - j * 1.75 - Math.abs(i) * 0.35 + ((i * 7 + j * 3) % 5) * 0.12);
          k.shape('hexprism', [x, h / 2, z], [3.4, h, 2.94], BASALT[(i * 7 + j * 3 + 40) % 4]);
          if ((i + j) % 4 === 0) k.shape('hexprism', [x, h + 0.05, z], [2.8, 0.1, 2.4], '#6a9a4a');
        }
      }
      // a Corsair running down it with a gold bar; the bolt coming down
      // just behind him, its ring on the stones; a Buccaneer giving chase
      var bar = { data: { parts: [{ t: 'box', p: [-0.75, 0.0, 0.9], s: [1.6, 0.7, 0.9], c: '#ffc830', m: 'metal' }] } };
      pirate(k, 3, 5.2, 0.3, 'red', { y: 9.4, anim: 'run', time: 0.5, holding: bar });
      pirate(k, -6, -6, 0.2, 'blue', { y: 13.2, anim: 'run', time: 1.0, face: 'face_angry' });
      var pts = [[10, 70, -10], [6, 58, -6], [11, 46, -7], [5, 34, -3], [8, 24, -1], [4, 14.2, -1]];
      for (var b = 1; b < pts.length; b++) {
        var p0 = pts[b - 1], p1 = pts[b];
        var dx = p1[0] - p0[0], dy = p1[1] - p0[1], dz = p1[2] - p0[2];
        var len = Math.hypot(dx, dy, dz);
        // a box's long (y) axis turned onto the segment: rx leans it towards
        // +z, rz towards -x (the engine's Ry*Rx*Rz)
        var tilt = [Math.atan2(dz, dy), 0, -Math.asin(dx / len)];
        k.box([(p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2], [0.5, len + 0.4, 0.5], '#e8f2ff',
              { m: 'neon', r: tilt });
        k.box([(p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2], [1.6, len + 0.4, 1.6], '#7ab8ff',
              { m: 'neon', a: 0.3, r: tilt });
      }
      k.shape('torus', [4, 14.3, -1], [8, 0.5, 8], '#7ab8ff', { m: 'neon', a: 0.9 });
      k.shape('sph', [4, 14.6, -1], [4, 1.6, 4], '#e8f2ff', { m: 'neon', a: 0.5 });
      // a cottage with its turf roof, its lamps lit
      k.box([-44, 3.5, 6], [16, 7, 12], '#9a948a');
      k.box([-44, 7.6, 6], [17, 1.2, 13], '#5a8a4e');
      k.box([-44, 8.8, 6], [12, 1.2, 9], '#5a8a4e');
      k.box([-36.2, 3.4, 6], [0.4, 5.8, 3.6], '#3a2a20');
      k.box([-36.0, 5.6, 9], [0.4, 0.8, 0.6], '#ffb84a', { m: 'neon' });
      // the rain
      for (var rn = 0; rn < 60; rn++) {
        var rx = ((rn * 37) % 120) - 60, rz = ((rn * 53) % 100) - 50, ry = 6 + ((rn * 29) % 50);
        k.box([rx, ry, rz], [0.08, 3.2, 0.08], '#c0d0e2', { a: 0.4, r: [0, 0, 0.25] });
      }
    }
  });

  // ------------------------------------------------ Sulphur Springs
  Thumbs.registerWorld('pb_sulphur', {
    sky: { top: '#3a8ad0', horizon: '#f4e8c8', sun: [0.5, 0.62, 0.3], clouds: 0.45, tint: '#fff4e0' },
    camera: [[30, 22, 50], [0, 8, -10], 54],
    build: function (parts, k) {
      k.box([0, -4, 10], [400, 6, 400], '#2a9ab8', { m: 'glass', a: 0.8 });
      k.box([0, -1, 14], [160, 2, 130], '#7aa040');
      // the terraces stepping up behind, each with its brimming pools
      [[70, -20, 3], [56, -34, 6], [42, -46, 9], [28, -58, 12]].forEach(function (tr, i) {
        var hw = tr[0] / 2;
        k.box([0, tr[2] / 2, (tr[1] - 80) / 2], [tr[0], tr[2], tr[1] + 80], i % 2 ? '#e4d8bc' : '#f2ead8');
        for (var f = 0; f < tr[0] / 3; f++) {
          k.box([-hw + 1.5 + f * 3, tr[2] - 0.9, tr[1] + 0.15], [1.4, 1.8 - (f % 3) * 0.4, 0.3], f % 2 ? '#cdbd9c' : '#e8c8a0');
        }
        if (i < 3) {
          [-1, 1].forEach(function (s) {
            k.box([s * hw * 0.55, tr[2] + 0.3, tr[1] - 6], [10, 0.6, 7], '#e4d8bc');
            k.box([s * hw * 0.55, tr[2] + 0.45, tr[1] - 6], [8.6, 0.4, 5.6], '#4ad8e8', { m: 'glass', a: 0.85 });
          });
        }
      });
      // the bathhouse on top: columns, the gilt governor
      for (var c = 0; c < 6; c++) {
        var h = c % 3 === 1 ? 3 : 8;
        k.shape('cyl', [-10 + c * 4, 12 + h / 2, -70], [1.4, h, 1.4], '#f4f0e4');
        k.box([-10 + c * 4, 12 + h + 0.3, -70], [2.0, 0.6, 2.0], '#e0d4b8');
      }
      k.box([0, 14.5, -74], [1.6, 5, 1.4], '#e8b830', { m: 'metal' });
      k.box([0, 17.6, -74], [1.2, 1.2, 1.2], '#e8b830', { m: 'metal' });
      // the volcano far off
      k.shape('cone', [-70, 20, -150], [120, 60, 90], '#6a5a4a');
      [[0, 54, 12], [4, 62, 16], [-2, 70, 20]].forEach(function (pl) {
        k.shape('sph', [-70 + pl[0], pl[1], -150], [pl[2], pl[2] * 0.7, pl[2]], '#d8d0c8', { a: 0.85 });
      });
      // the grand spring in its rings, Old Faithless blowing out of it
      k.box([0, 0.15, 22], [44, 0.3, 44], '#f2ead8');
      ['#c8402a', '#e8702a', '#f0a030', '#e8d040', '#7ac85a', '#3ab8b0', '#1a6ab8'].forEach(function (col, i) {
        k.shape('cyl', [0, 0.32 + i * 0.03, 22], [40 - i * 5.4, 0.03, 40 - i * 5.4], col);
      });
      for (var s = 0; s < 8; s++) {
        var f = (s + 0.5) / 8;
        k.shape('cyl', [Math.sin(s * 1.7) * 0.4, 0.5 + 26 * f, 22], [3.6 - f * 1.2, 26 / 8 + 0.4, 3.6 - f * 1.2],
                s % 2 ? '#e8fcff' : '#9ae8f8', { a: 0.8 });
      }
      k.shape('sph', [0, 28, 22], [8, 4, 8], '#f4feff', { a: 0.75 });
      k.shape('torus', [0, 0.5, 22], [10, 0.5, 10], '#ffffff', { a: 0.8 });
      // a Buccaneer flung high on it, treasure flying out
      pirate(k, 2, 22, 2.4, 'blue', { y: 20, anim: 'jump', time: 0.3, face: 'face_angry' });
      [[8, 24, 20, 0], [-7, 22, 25, 1], [12, 16, 26, 2], [-12, 14, 18, 3], [16, 6, 30, 4]].forEach(function (c) {
        k.shape('doubloon', [c[0], c[1], c[2]], [1.8, 1.8, 1.8], '#ffd040', { m: 'metal', r: [c[3], c[3] * 0.7, 0] });
      });
      // the boardwalk, a Corsair running it with a chest
      k.box([0, 1.05, 34], [90, 0.3, 4], '#a8805a');
      for (var bp = 0; bp < 12; bp++) k.shape('cyl', [-40 + bp * 7.5, 0.45, 34], [0.5, 0.9, 0.5], '#6a4a2e');
      pirate(k, -14, 34, 1.4, 'red', { y: 1.2, anim: 'run', time: 0.5, holding: CHEST });
      // sulphur heaps, steaming cones
      k.box([-44, 1, 10], [12, 2, 10], '#f2d230');
      k.box([-44, 2.4, 10], [7, 1.2, 6], '#d0a820');
      k.shape('cyl', [30, 0.4, 6], [6, 0.8, 6], '#e4d8bc');
      k.shape('cyl', [30, 1.0, 6], [4, 0.6, 4], '#f2ead8');
    }
  });

  // ------------------------------------------------ Ghost Fleet Cove
  /* a skeleton of the ghost crews: bones, a rag of a coat, a tricorn, eyes
     lit green, a pistol levelled; ``sunk`` how deep in the water */
  function skeleton(k, x, y, z, yaw) {
    var B = '#e8e4d4';
    k.attach(x, y, z, yaw, [
      { t: 'box', p: [-0.5, 1.0, 0], s: [0.36, 2.0, 0.36], c: B },
      { t: 'box', p: [0.5, 1.0, 0], s: [0.36, 2.0, 0.36], c: B },
      { t: 'box', p: [0, 2.2, 0], s: [1.6, 0.4, 0.6], c: B },
      { t: 'box', p: [0, 3.2, 0], s: [0.36, 2.2, 0.36], c: B },
      { t: 'box', p: [0, 3.0, 0], s: [1.8, 0.24, 0.9], c: B },
      { t: 'box', p: [0, 3.5, 0], s: [1.9, 0.24, 1.0], c: B },
      { t: 'box', p: [0, 4.0, 0], s: [1.8, 0.24, 0.9], c: B },
      { t: 'box', p: [0, 3.5, -0.1], s: [2.2, 2.0, 0.9], c: '#4a3a2a', a: 0.55 },
      { t: 'box', p: [0.95, 3.6, 1.0], s: [0.3, 0.3, 2.0], c: B },
      { t: 'box', p: [0.95, 3.7, 2.3], s: [0.24, 0.3, 1.0], c: '#4a4e56', m: 'metal' },
      { t: 'box', p: [-1.1, 3.2, 0], s: [0.3, 1.8, 0.3], c: B, r: [0, 0, -0.2] },
      { t: 'sph', p: [0, 5.0, 0], s: [1.3, 1.3, 1.3], c: B },
      { t: 'box', p: [-0.3, 5.05, 0.6], s: [0.3, 0.26, 0.1], c: '#7aff9a', m: 'neon' },
      { t: 'box', p: [0.3, 5.05, 0.6], s: [0.3, 0.26, 0.1], c: '#7aff9a', m: 'neon' },
      { t: 'tricorn', p: [0, 5.75, 0], s: [2.4, 1.4, 2.4], c: '#1a1a22' }
    ]);
  }
  Thumbs.registerWorld('pb_ghostfleet', {
    sky: { top: '#081028', horizon: '#34486e', sun: [-0.35, 0.55, -0.55], clouds: 0.4, tint: '#a8c0f0' },
    camera: [[28, 16, 40], [0, 6, -12], 54],
    build: function (parts, k) {
      var ROT = '#3a3428';
      k.box([0, -4, 0], [400, 6, 400], '#16303e', { m: 'glass', a: 0.88 });
      // the graveyard hill and the crypt behind, its ghost-light up the sky
      k.box([0, 2, -70], [140, 4, 50], '#3e5a48');
      k.box([0, 5, -80], [90, 2, 30], '#33503e');
      k.box([0, 10, -86], [18, 8, 12], '#7a7a86');
      k.shape('wedge', [0, 15.5, -83], [19, 3, 6], '#5a5a68');
      k.shape('wedge', [0, 15.5, -89], [19, 3, 6], '#5a5a68', { r: [0, Math.PI, 0] });
      k.shape('cyl', [0, 40, -86], [5, 48, 5], '#7aff9a', { m: 'neon', a: 0.16 });
      for (var g = 0; g < 9; g++) k.box([-32 + g * 8, 5.2, -50 - (g % 2) * 4], [1.4, 2.4, 0.5], '#8a8a94');
      // the flagship, sunk to her gunwales, her stern windows lit
      k.box([0, 1.6, -18], [14, 6, 34], ROT);
      k.box([0, 6.0, -2], [14, 3, 8], '#54463a');
      k.box([0, 5.4, -32], [12, 2, 7], '#54463a');
      for (var w = 0; w < 4; w++) k.box([-4.5 + w * 3, 4.6, 2.05], [1.8, 1.6, 0.1], '#7aff9a', { m: 'neon' });
      [[-30, 16], [-17, 22], [-4, 15]].forEach(function (m, i) {
        k.shape('cyl', [0, 4 + m[1] / 2, m[0]], [1.0, m[1], 1.0], ROT);
        k.box([0, 3 + m[1] - 2, m[0]], [12, 0.4, 0.4], ROT);
        k.box([-3, 3 + m[1] - 5.2, m[0] + 0.3], [4, 5.6, 0.1], '#a8c8a8', { a: 0.4 });
        k.box([3.5, 3 + m[1] - 4.4, m[0] + 0.3], [3, 4, 0.1], '#a8c8a8', { a: 0.4 });
      });
      idol(k, 0, 7.5, -2);
      // masts of the drowned fleet
      [[-24, -30, 12], [22, -20, 10], [30, 6, 14]].forEach(function (m) {
        k.shape('cyl', [m[0], m[2] / 2 - 2, m[1]], [0.9, m[2] + 4, 0.9], ROT);
        k.box([m[0], m[2] - 2, m[1]], [7, 0.4, 0.4], ROT);
      });
      // the pier, a Corsair on it with the idol; the dead climbing out of
      // the water to stop her
      k.box([4, 1.2, 14], [40, 0.4, 5], '#7a5a3a');
      for (var p2 = 0; p2 < 6; p2++) k.shape('cyl', [-14 + p2 * 7, -0.4, 16], [0.7, 3.2, 0.7], '#5a3a22');
      pirate(k, 8, 14, -1.9, 'red', { y: 1.4, anim: 'run', time: 0.5, holding: { data: { parts: [
        { t: 'box', p: [-0.75, 0.2, 0.9], s: [1.0, 1.6, 0.8], c: '#e8b830', m: 'metal' },
        { t: 'box', p: [-0.75, 1.3, 0.9], s: [1.1, 0.8, 0.9], c: '#e8b830', m: 'metal' }] } } });
      skeleton(k, 18, -2.6, 8, -2.2);
      skeleton(k, 22, -1.6, 18, -1.6);
      skeleton(k, -4, -3.4, 22, 2.6);
      [[14, 4.6, 7.4], [17, 5.6, 17]].forEach(function (f) {
        k.shape('sph', [f[0], f[1], f[2]], [1.4, 1.4, 1.4], '#aaffcc', { m: 'neon', a: 0.8 });
      });
      // wisps, the moon
      [[-10, 8, 4], [12, 10, -8], [-20, 6, -12], [26, 7, 0], [4, 12, 8]].forEach(function (w2) {
        k.shape('sph', w2, [0.7, 0.7, 0.7], '#e8ffe8', { m: 'neon' });
        k.shape('sph', w2, [2.4, 2.4, 2.4], '#7aff9a', { m: 'neon', a: 0.25 });
      });
      k.shape('sph', [-60, 70, -220], [40, 40, 40], '#eef2e4', { m: 'neon' });
    }
  });

  // ------------------------------------------------ Glowtide Lagoon
  Thumbs.registerWorld('pb_glowtide', {
    sky: { top: '#121848', horizon: '#e08a8a', sun: [0.2, 0.42, 0.72], clouds: 0.5, tint: '#c8c0f0' },
    camera: [[30, 18, 44], [0, 3, -8], 54],
    build: function (parts, k) {
      // the lagoon at low tide: its floor showing through a skin of deep
      // blue water, coral and clams on it; sandy shores, mangroves behind
      k.box([0, -6.5, 0], [400, 1, 400], '#5a5878');
      k.box([0, -5.4, 0], [400, 1.2, 400], '#0a2a6a', { m: 'glass', a: 0.72 });
      [[-60, 8], [60, 8]].forEach(function (b) { k.box([b[0], -3, b[1]], [30, 6, 120], '#d8c8a8'); });
      k.box([0, -3, -64], [150, 6, 30], '#3e6a4a');
      [[-30, -58], [-14, -62], [8, -60], [26, -58], [-44, -50], [44, -52]].forEach(function (m, i) {
        k.shape('cyl', [m[0], 3, m[1]], [1.2, 6, 1.2], '#5a4a3a');
        k.shape('sph', [m[0], 7, m[1]], [9, 3, 8], i % 2 ? '#2e5a3e' : '#386a48');
      });
      [[-24, 14, '#ff6a9a'], [20, 20, '#c86aff'], [-30, -16, '#ffd04a'], [28, -12, '#5af0c8'], [-10, 36, '#ff9a5a']].forEach(function (c) {
        k.shape('sph', [c[0], -5.2, c[1]], [3, 2.2, 3], c[2]);
        k.shape('cyl', [c[0], -3.9, c[1]], [0.5, 0.6, 0.5], '#ff8ad8', { m: 'neon' });
      });
      // the moon temple, stepped, the idol on its crown, crescents lit
      [[40, -4], [32, -2], [25, 1], [18, 4], [12, 7]].forEach(function (tr, i) {
        var prev = i ? [-4, -2, 1, 4][i - 1] : -6;
        k.box([0, (prev + tr[1]) / 2, -12], [tr[0], tr[1] - prev, tr[0]], i % 2 ? '#6a7894' : '#8a9ab4');
      });
      for (var st = 0; st < 3; st++) k.box([0, -1.5 + st * 1.0, 4.6 - st * 1.2], [5, 1.0, 1.2], '#6a7894');
      [[-7, 0.6], [7, 0.6]].forEach(function (c) {
        k.shape('crescent', [c[0], -0.5, c[1]], [2.2, 2.4, 0.2], '#7ad8ff', { m: 'neon' });
      });
      [[-10.9, -22.9], [10.9, -22.9], [-10.9, -1.1], [10.9, -1.1]].forEach(function (o) {
        k.box([o[0], 4, o[1]], [1.4, 6, 1.4], '#8a9ab4');
        k.shape('sph', [o[0], 7.6, o[1]], [1.2, 1.2, 1.2], '#f4f8ff', { m: 'neon' });
      });
      idol(k, 0, 7, -12);
      // the causeway out to it, its moon-lamps
      k.box([0, -4.3, 26], [6, 3.4, 30], '#8a9ab4');
      for (var p = 0; p < 3; p++) {
        [-2.6, 2.6].forEach(function (dx) {
          k.box([dx, -1.6, 16 + p * 9], [0.8, 2, 0.8], '#6a7894');
          k.box([dx, -0.3, 16 + p * 9], [0.7, 0.6, 0.7], '#7ad8ff', { m: 'neon' });
        });
      }
      // the giant clams open on the floor, pearls lit
      [[-14, 18], [16, 12], [-20, -2], [22, 30]].forEach(function (c) {
        k.shape('sph', [c[0], -5.6, c[1]], [3.4, 1.2, 2.6], '#b8a8c8');
        k.shape('sph', [c[0], -4.6, c[1] - 1.0], [3.2, 0.8, 2.4], '#c8b8d8', { r: [0.7, 0, 0] });
        k.shape('sph', [c[0], -5.0, c[1]], [1.0, 1.0, 1.0], '#f4f8ff', { m: 'neon' });
      });
      // a Corsair on the causeway with a pearl the size of a fist, wading
      // light round a Buccaneer still in the water
      pirate(k, 1, 24, 0.4, 'red', { y: -2.6, anim: 'run', time: 0.5, holding: { data: { parts: [
        { t: 'sph', p: [-0.75, 0.4, 0.9], s: [1.4, 1.4, 1.4], c: '#f4f8ff', m: 'neon' }] } } });
      pirate(k, -12, 8, 0.6, 'blue', { y: -6, anim: 'run', time: 1.0, face: 'face_angry' });
      [3, 5.4, 7.8].forEach(function (r, i) {
        k.shape('torus', [-12, -4.75, 8], [r, 0.3, r], '#5af0ff', { m: 'neon', a: 0.8 - i * 0.22 });
      });
      // a stilt hut, its lanterns; lanterns floating; sky lanterns going up
      k.box([40, 4.6, -6], [10, 5.4, 8], '#a8845a');
      k.shape('wedge', [40, 8.6, -4], [11, 2.6, 4.6], '#c8a85a');
      k.shape('wedge', [40, 8.6, -8], [11, 2.6, 4.6], '#c8a85a', { r: [0, Math.PI, 0] });
      k.box([35, 6, -1.7], [0.6, 0.8, 0.6], '#ffb05a', { m: 'neon' });
      [[36, -10], [44, -10], [36, -2], [44, -2]].forEach(function (s2) { k.shape('cyl', [s2[0], -2.2, s2[1]], [0.6, 7.6, 0.6], '#6a4a2e'); });
      [[-10, 30], [12, 22], [-18, 10], [20, 4], [8, 34], [-26, 24], [-4, 14], [26, 16], [-30, 4]].forEach(function (l, i) {
        var c = ['#ff6a4a', '#ffb84a', '#ff8ad8', '#ffe07a'][i % 4];
        k.box([l[0], -4.5, l[1]], [1.4, 1.4, 1.4], c, { m: 'neon', a: 0.9 });
        k.shape('sph', [l[0], -4.5, l[1]], [3.2, 2.0, 3.2], c, { m: 'neon', a: 0.18 });
      });
      [[30, 30, -40], [38, 42, -50], [22, 52, -60], [46, 36, -30], [16, 40, -44]].forEach(function (l, i) {
        k.box(l, [1.6, 2.0, 1.6], ['#ffb84a', '#ff8a4a', '#ffd86a'][i % 3], { m: 'neon' });
      });
      for (var g = 0; g < 22; g++) {
        k.shape('sph', [((g * 37) % 90) - 45, -4.7, ((g * 53) % 80) - 30], [0.5, 0.2, 0.5], g % 2 ? '#5af0ff' : '#b8fff0', { m: 'neon' });
      }
    }
  });

  // ------------------------------------------------ Frostfang Floe
  /* a frosted tentacle, pale and crusted with ice */
  function frostTentacle(k, x, y, z, h, lean, turn) {
    var n = 9;
    for (var s = 0; s < n; s++) {
      var f = (s + 0.5) / n, bend = lean * f * f;
      var px = x + Math.sin(turn) * bend * h * 0.6, pz = z + Math.cos(turn) * bend * h * 0.6;
      var rad = 2.4 * (1 - f) + 0.5;
      k.shape('sph', [px, y + h * f * (1 - 0.3 * f * Math.abs(lean)), pz], [rad, h / n * 1.5, rad], s % 2 ? '#6a9ab8' : '#8ab8d0');
      if (s % 2 === 0 && s < n - 2) {
        k.shape('sph', [px + Math.cos(turn) * rad * 0.42, y + h * f * (1 - 0.3 * f * Math.abs(lean)), pz - Math.sin(turn) * rad * 0.42],
                [rad * 0.34, rad * 0.34, rad * 0.34], '#f0faff');
      }
    }
  }
  Thumbs.registerWorld('pb_frostfang', {
    sky: { top: '#3a8ae0', horizon: '#e8f4ff', sun: [0.5, 0.42, -0.35], clouds: 0.3, tint: '#f4faff' },
    camera: [[32, 18, 44], [0, 6, -8], 54],
    build: function (parts, k) {
      k.box([0, -4, 10], [400, 6, 400], '#2a7aa8', { m: 'glass', a: 0.8 });
      k.box([0, -0.5, 0], [150, 1, 130], '#f2f6fa');
      k.box([0, 0.06, 2], [70, 0.12, 60], '#bfe4f4', { m: 'glass' });
      // the glacier behind, in steps
      [[100, -40, 7], [76, -52, 13], [52, -64, 19]].forEach(function (g, i) {
        k.box([0, g[2] / 2, g[1] - 10], [g[0], g[2], 24], i % 2 ? '#d4eef8' : '#bfe4f4');
        k.box([0, g[2] + 0.15, g[1] - 10], [g[0], 0.3, 24], '#f2f6fa');
        for (var ic = 0; ic < g[0] / 4; ic++) {
          k.shape('cone', [-g[0] / 2 + 2 + ic * 4, g[2] - 1, g[1] + 2.3], [0.8, 2, 0.8], '#e8f8ff', { r: [Math.PI, 0, 0] });
        }
      });
      // the frozen galleon held fast in the ice, sails stiff with frost
      k.box([0, 2.5, -6], [12, 5, 34], '#6a4a2e');
      k.box([0, 6.5, -20], [12, 3, 8], '#7a5a3a');
      k.box([0, 6.5, 8], [12, 3, 6], '#7a5a3a');
      k.box([0, 5.15, -6], [11, 0.3, 20], '#f4f8fc');
      [[-18, 22], [-6, 28], [6, 20]].forEach(function (m) {
        k.shape('cyl', [0, 5 + m[1] / 2, m[0]], [1.0, m[1], 1.0], '#4a3020');
        k.box([0, 5 + m[1] - 4, m[0]], [11, 0.5, 0.5], '#4a3020');
        k.box([0, 5 + m[1] - 7, m[0] + 0.3], [10, 5.4, 0.2], '#f4f8fc');
        for (var c = 0; c < 5; c++) k.shape('cone', [-4 + c * 2, 5 + m[1] - 10.3, m[0] + 0.3], [0.5, 1.4, 0.5], '#e8f8ff', { r: [Math.PI, 0, 0] });
      });
      idol(k, 0, 8, -20);
      // the breathing holes, the frost kraken coming up through them
      [[-18, 10], [18, 10], [0, 24], [-20, -16]].forEach(function (h, i) {
        k.box([h[0], 0.08, h[1]], [7, 0.16, 7], '#123a5a');
        for (var e = 0; e < 6; e++) {
          var a = e * Math.PI / 3;
          k.box([h[0] + Math.cos(a) * 4, 0.3, h[1] + Math.sin(a) * 4], [1.6, 0.6, 1.2], '#e8f8ff', { r: [0, -a, 0] });
        }
        frostTentacle(k, h[0], -1, h[1], 14 + (i % 2) * 4, i === 2 ? 1.2 : 0.4 * (i % 2 ? 1 : -1), i * 1.7);
      });
      k.shape('torus', [8, 0.3, 28], [12, 0.6, 12], '#9ae8ff', { m: 'neon', a: 0.85 });
      // a Corsair running over the ice with a jewel, a Buccaneer behind
      pirate(k, 10, 30, 0.9, 'red', { y: 0.12, anim: 'run', time: 0.5,
        holding: { data: { parts: [{ t: 'gem', p: [-0.75, 0.6, 0.9], s: [1.6, 1.6, 1.6], c: '#3ad0ff', m: 'glass' }] } } });
      pirate(k, 0, 37, 1.2, 'blue', { y: 0.12, anim: 'run', time: 1.0, face: 'face_angry' });
      // a whalers' hut, spruces, penguins
      k.box([-40, 3.5, 10], [12, 7, 10], '#c8302a');
      k.box([-40, 7.6, 10], [13, 1.2, 11], '#f2f6fa');
      k.box([-40, 8.8, 10], [9, 1.2, 7], '#f2f6fa');
      [[-46, -10], [40, -14], [44, 18]].forEach(function (p) {
        for (var tier = 0; tier < 3; tier++) {
          k.shape('cone', [p[0], 3 + tier * 2.6, p[1]], [6 - tier * 1.6, 4, 6 - tier * 1.6], '#2e5a3e');
          k.shape('cone', [p[0], 4.4 + tier * 2.6, p[1]], [3.4 - tier, 1.2, 3.4 - tier], '#f2f6fa');
        }
      });
      [[30, 40], [33, 42], [28, 44]].forEach(function (p, i) {
        k.shape('sph', [p[0], 1.4, p[1]], [1.6, 2.6, 1.5], '#1e2228');
        k.shape('sph', [p[0] + 0.2, 1.3, p[1] + 0.35], [1.2, 2.2, 1.0], '#f4f4f0');
        k.box([p[0], 2.9, p[1] + 0.8], [0.3, 0.25, 0.6], '#ff9a2a');
      });
    }
  });
})(window);
