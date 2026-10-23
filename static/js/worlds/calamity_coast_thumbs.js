/* Calamity Coast's world-page pictures: the card and a diorama of each of
   the four towns on its very bad day, built from the same blocks the game
   draws with (Thumbs.registerWorld; loaded by thumbs.js the first time one
   is asked for).  Every player wears the classic default -- yellow skin,
   red torso, blue legs; the Lifeguards wear a red cap and the Rangers a
   blue hat, and the townsfolk they are rescuing are in their own clothes. */
(function (global) {
  'use strict';
  var Thumbs = global.Thumbs;
  if (!Thumbs || !Thumbs.registerWorld) return;

  var SEA = '#2f78b8', FOAM = '#e8f4ff', WOOD = '#8a6a44', LAVA = '#ff5a14';

  function cap(colour) {
    return [{ t: 'cyl', p: [0, 6.05, 0], s: [2.3, 0.5, 2.3], c: colour },
            { t: 'box', p: [0, 5.85, 1.3], s: [1.6, 0.14, 1.0], c: colour }];
  }
  function lifeguard(k, x, z, yaw, o) {
    o = o || {};
    k.player(x, z, yaw, { anim: o.anim || 'run', time: o.time || 0.3, holding: null, y: o.y || 0,
                          wear: cap('#d8402a').concat(o.carry ? carried(o.look || 0) : []) });
  }
  function ranger(k, x, z, yaw, o) {
    o = o || {};
    k.player(x, z, yaw, { anim: o.anim || 'run', time: o.time || 0.5, holding: null, y: o.y || 0,
                          wear: [{ t: 'cyl', p: [0, 6.0, 0], s: [3.2, 0.2, 3.2], c: '#2a5a9a' },
                                 { t: 'cyl', p: [0, 6.4, 0], s: [1.9, 0.8, 1.9], c: '#2a5a9a' }]
                            .concat(o.carry ? carried(o.look || 1) : []) });
  }

  var LOOKS = [['#f2c8a0', '#3aa04a', '#5a4a3a', '#4a2a1a'], ['#c88a5a', '#f2c230', '#2a3a5a', '#f2c230'],
               ['#8a5a3a', '#d84a8a', '#3a3a3a', '#1a1a1a'], ['#f2d0b0', '#f2f0ea', '#4a6a9a', '#c8c8c8']];

  /* a townsperson across the back of the carrier's shoulders, lying on
     their side, head to the carrier's right (the carrier's own frame) */
  function carried(look) {
    var L = LOOKS[look % LOOKS.length];
    return [{ t: 'rbox', p: [0.2, 4.6, -1.15], s: [2.0, 1.5, 1.0], c: L[1] },
            { t: 'rbox', p: [-1.9, 4.25, -1.15], s: [2.0, 0.7, 0.8], c: L[2] },
            { t: 'rbox', p: [-1.9, 4.95, -1.15], s: [2.0, 0.7, 0.8], c: L[2] },
            { t: 'rbox', p: [1.8, 4.65, -1.15], s: [1.15, 1.15, 1.15], c: L[0] },
            { t: 'rbox', p: [2.45, 4.7, -1.15], s: [0.3, 1.2, 1.2], c: L[3] },
            { t: 'rbox', p: [0.9, 3.4, -0.95], s: [0.55, 1.5, 0.55], c: L[0] },
            { t: 'rbox', p: [0.5, 3.45, -1.4], s: [0.55, 1.5, 0.55], c: L[0] }];
  }

  /* a townsperson stranded somewhere, both arms up */
  function stranded(k, x, y, z, yaw, look) {
    var L = LOOKS[look % LOOKS.length];
    k.attach(x, y, z, yaw, [
      { t: 'rbox', p: [-0.42, 1.0, 0], s: [0.78, 2.0, 0.85], c: L[2] },
      { t: 'rbox', p: [0.42, 1.0, 0], s: [0.78, 2.0, 0.85], c: L[2] },
      { t: 'rbox', p: [0, 3.0, 0], s: [1.75, 2.0, 0.95], c: L[1] },
      { t: 'rbox', p: [-1.15, 4.5, 0], s: [0.6, 1.9, 0.6], c: L[0], r: [0, 0, -0.4] },
      { t: 'rbox', p: [1.15, 4.5, 0], s: [0.6, 1.9, 0.6], c: L[0], r: [0, 0, 0.4] },
      { t: 'rbox', p: [0, 4.65, 0], s: [1.15, 1.15, 1.15], c: L[0] },
      { t: 'rbox', p: [0, 5.3, -0.1], s: [1.2, 0.35, 1.2], c: L[3] },
      { t: 'cyl', p: [0, 18, 0], s: [0.5, 24, 0.5], c: '#ff5a3a', a: 0.3, m: 'neon' }]);
  }

  function crate(k, x, y, z, chute) {
    k.box([x, y + 1.1, z], [2.2, 2.2, 2.2], '#a87a3a');
    k.box([x, y + 1.1, z], [2.3, 0.35, 2.3], '#5a3a1a');
    k.box([x, y + 1.1, z], [0.35, 2.3, 2.3], '#5a3a1a');
    if (chute) {
      k.shape('sph', [x, y + 7.2, z], [6.4, 3.2, 6.4], '#e8502a');
      k.box([x, y + 4.6, z], [0.08, 4.6, 0.08], '#f2f0ea');
    } else {
      k.shape('cyl', [x, y + 14, z], [1.2, 26, 1.2], '#ffe27a', { a: 0.2, m: 'neon' });
    }
  }

  function house(k, x, z, w, d, h, wall, roof, yaw, y) {
    k.attach(x, y || 0, z, yaw || 0, [
      { t: 'box', p: [0, h / 2, 0], s: [w, h, d], c: wall },
      { t: 'box', p: [0, h + 0.8, 0], s: [w + 1, 1.6, d + 1], c: roof },
      { t: 'box', p: [0, h + 2.2, 0], s: [w - 3, 1.4, d - 2], c: roof },
      { t: 'box', p: [0, h + 3.4, 0], s: [w - 7, 1.2, d - 5], c: roof },
      { t: 'box', p: [-w / 4, h * 0.6, d / 2 + 0.05], s: [2.2, 2.4, 0.1], c: '#cfe8ff', m: 'glass' },
      { t: 'box', p: [w / 4, h * 0.6, d / 2 + 0.05], s: [2.2, 2.4, 0.1], c: '#cfe8ff', m: 'glass' },
      { t: 'box', p: [0, 2.2, d / 2 + 0.05], s: [2.4, 4.4, 0.1], c: '#6a4a2a' }]);
  }

  function palm(k, x, z, h, lean) {
    for (var i = 0; i < 6; i++) {
      k.shape('cyl', [x + lean * i * 0.4, 0.9 + i * h / 6, z], [0.9 - i * 0.05, h / 6 + 0.1, 0.9 - i * 0.05], WOOD);
    }
    var tx = x + lean * 2.4, ty = h + 0.6;
    for (var l = 0; l < 6; l++) {
      var a = l * Math.PI / 3;
      k.box([tx + Math.cos(a) * 2.6, ty - 0.6, z + Math.sin(a) * 2.6], [5.6, 0.25, 1.4], '#2a8a3a',
            { r: [0, -a, -0.35] });
    }
    k.shape('sph', [tx, ty - 0.6, z], [1.1, 1.1, 1.1], '#6a4a2a');
  }

  function helipad(k, x, y, z) {
    k.shape('cyl', [x, y + 0.08, z], [12, 0.16, 12], '#2a2e36');
    k.shape('cyl', [x, y + 0.12, z], [10.5, 0.1, 10.5], '#f2c230');
    k.shape('cyl', [x, y + 0.16, z], [9.6, 0.1, 9.6], '#2a2e36');
    k.box([x - 1.6, y + 0.2, z], [0.8, 0.1, 4.8], '#f2f0ea');
    k.box([x + 1.6, y + 0.2, z], [0.8, 0.1, 4.8], '#f2f0ea');
    k.box([x, y + 0.2, z], [2.4, 0.1, 0.8], '#f2f0ea');
    k.shape('cyl', [x, y + 20, z], [2.2, 40, 2.2], '#5aff8a', { a: 0.16, m: 'neon' });
  }

  /* a breaking wave ``length`` long and ``h`` high, centred on (x, z) and
     breaking the way ``yaw`` faces: the body, the face leaning over, the
     lip curling down, and the foam on it and where it lands */
  function wave(k, x, z, length, h, yaw) {
    var local = [];
    for (var lx = -length / 2; lx <= length / 2; lx += 6) {
      var j = Math.sin(lx * 0.27) * 1.4 + Math.sin(lx * 0.11) * 1.0, top = h + j;
      local.push({ t: 'box', p: [lx, top * 0.45, -7], s: [6.4, top * 0.9, 10], c: SEA });
      local.push({ t: 'box', p: [lx, top * 0.5, -1.2], s: [6.4, top, 3], c: '#3a8ac8', r: [0.3, 0, 0] });
      local.push({ t: 'box', p: [lx, top + 0.2, 2.6], s: [6.4, 1.8, 7], c: '#5aa8e0', r: [0.35, 0, 0] });
      local.push({ t: 'box', p: [lx, top - 2.2, 5.6], s: [6.4, 3.6, 1.4], c: '#c8e4f8' });
      local.push({ t: 'sph', p: [lx, top + 1.1, 3.2], s: [5.6, 2.4, 4.6], c: FOAM });
      var fj = Math.sin(lx * 1.7) * 2.2, fk = Math.cos(lx * 0.9);
      local.push({ t: 'sph', p: [lx + 2.5 + fj, 1.2 + fk * 0.5, 7.5 + fk * 2.0], s: [4.6 + fk * 1.6, 2.2 + fk * 0.6, 4.2],
                   c: FOAM, a: 0.85 });
      local.push({ t: 'sph', p: [lx - 1.5, top + 3.0 + (j > 0 ? 1 : 0), 4.2], s: [1.4, 1.4, 1.4], c: FOAM, a: 0.8 });
    }
    k.attach(x, 0, z, yaw, local);
  }

  // ------------------------------------------------------------ card
  Thumbs.registerWorld('calamity_coast', {
    sky: { top: '#3a4a5a', horizon: '#a8b4bc', sun: [0.45, 0.6, 0.3], clouds: 0.9, tint: '#d8e0e8' },
    camera: [[62, 14, 20], [4, 10, 2], 54],
    build: function (parts, k) {
      k.box([0, -0.5, -10], [160, 1, 60], '#d8c8a0');
      k.box([0, 2, -32], [160, 4, 20], '#bca888');
      house(k, -12, -32, 14, 10, 8, '#f2e6c8', '#c8503a', 0, 4);
      house(k, 6, -33, 12, 10, 9, '#a8d0e8', '#3a6a9a', 0, 4);
      house(k, 24, -32, 13, 10, 8, '#f0c8d8', '#c8503a', 0, 4);
      // the lighthouse on the point
      k.shape('cyl', [44, 13, -26], [5, 26, 5], '#f4f0e8');
      k.shape('cyl', [44, 9, -26], [5.1, 3, 5.1], '#d8402a');
      k.shape('cyl', [44, 18, -26], [5.1, 3, 5.1], '#d8402a');
      k.shape('cyl', [44, 27, -26], [3.6, 3, 3.6], '#ffe8a0', { m: 'neon' });
      k.shape('cone', [44, 30, -26], [4.4, 3, 4.4], '#3a3a3a');
      // the harbour wall, the sea behind it and the wave breaking over
      k.box([0, 1.2, 21.5], [160, 2.4, 3], '#a89a88');
      k.box([0, 0.4, 40], [160, 0.8, 34], SEA);
      wave(k, -10, 34, 110, 17, Math.PI);
      // a lifeguard carries a townsperson away up the quay, a ranger waves them on
      lifeguard(k, 34, 2, 3.4, { carry: true, look: 1, time: 0.2 });
      ranger(k, 24, -6, 1.2, { anim: 'idle', time: 0.3 });
      stranded(k, 18, 0, 12, 1.4, 2);
      crate(k, 40, 0, -10, true);
    }
  });

  // ------------------------------------------------------- Port Sunny
  Thumbs.registerWorld('cc_portsunny', {
    sky: { top: '#4a5a6a', horizon: '#c8d4dc', sun: [0.45, 0.7, 0.35], clouds: 0.8, tint: '#e8eef4' },
    camera: [[70, 30, 46], [0, 8, 0], 48],
    build: function (parts, k) {
      var cols = ['#f2e6c8', '#e8a8a0', '#a8d0e8', '#f2d088', '#c8e0b0'];
      for (var row = 0; row < 3; row++) {
        k.box([0, row * 4 + 2, -8 - row * 14], [150, 4 + row * 8, 14], ['#c8b898', '#bca888', '#b09a78'][row]);
        for (var i = 0; i < 5; i++) {
          // each row of houses stands on its own terrace (tops at 4, 12, 20)
          house(k, -40 + i * 20 + row * 4, -10 - row * 14, 12, 9, 7, cols[(i + row) % 5],
                i % 2 ? '#c8503a' : '#3a6a9a', 0, 4 + row * 8);
        }
      }
      k.box([0, 0.2, 18], [150, 0.4, 22], '#d8c8a0');
      // the harbour wall, and the sea over it
      k.box([0, 1.5, 28], [150, 3, 3], '#a89a88');
      k.box([0, 0.4, 44], [150, 0.8, 26], SEA);
      wave(k, 0, 40, 130, 14, Math.PI);
      // a fishing boat tossed up on the quay
      k.attach(-30, 1.2, 20, 0.6, [{ t: 'box', p: [0, 1, 0], s: [4, 2, 9], c: '#d8402a' },
                                    { t: 'box', p: [0, 2.6, -1], s: [3, 2, 3], c: '#f2f0ea' },
                                    { t: 'box', p: [0, 6, 1], s: [0.3, 7, 0.3], c: WOOD }]);
      helipad(k, 26, 4, -8);
      lifeguard(k, 6, 12, 3.0, { time: 0.1 });
      lifeguard(k, -6, 8, 2.7, { time: 0.6, carry: true, look: 3 });
      ranger(k, 18, 4, -2.6, { anim: 'idle' });
      stranded(k, -20, 0.4, 16, 0.4, 0);
      crate(k, 12, 0.4, 18, false);
    }
  });

  // ---------------------------------------------------- Summit Village
  Thumbs.registerWorld('cc_summit', {
    sky: { top: '#7a8a9a', horizon: '#e0e8f0', sun: [0.3, 0.6, 0.5], clouds: 0.85, tint: '#eef4ff' },
    camera: [[34, 18, 40], [0, 8, -8], 46],
    build: function (parts, k) {
      k.box([0, -0.5, 0], [150, 1, 110], '#f0f4fa');
      // the mountainside stepping up behind
      for (var s = 0; s < 6; s++) {
        k.box([0, 2 + s * 4, -16 - s * 10], [150, 4 + s * 8, 10], s % 2 ? '#e8eef6' : '#f4f8ff');
      }
      // the avalanche pouring down the steps: a wall of snow, a churning
      // front and the powder cloud thrown up over it
      for (var a = 0; a < 5; a++) {
        var ay = 6 + a * 8, az = -21 - a * 10;
        k.box([-12, ay + 2.5, az], [56, 6, 10], '#eef3fa');
        for (var b = 0; b < 6; b++) {
          var bj = Math.sin(a * 3.1 + b * 1.7);
          k.shape('sph', [-34 + b * 9.5 + bj * 2, ay + 5 + bj, az + 4], [11 + bj * 2, 7.5, 9],
                  (a + b) % 2 ? '#ffffff' : '#e4ecf6');
        }
      }
      for (var c = 0; c < 8; c++) {
        k.shape('sph', [-36 + c * 7.5, 3.2 + (c % 3), -11 + (c % 2) * 2], [8, 6, 7], c % 2 ? '#ffffff' : '#dde6f2');
        k.shape('sph', [-34 + c * 7, 14 + (c % 3) * 3, -16 - (c % 2) * 6], [12, 9, 10], '#ffffff', { a: 0.45 });
      }
      // the lodge with its chimney going, chalets, pines
      house(k, -24, 6, 18, 12, 9, '#8a5a3a', '#4a3a3a');
      k.box([-17, 13, 6], [2, 8, 2], '#7a6a5a');
      k.shape('sph', [-17, 18, 6], [3, 2.6, 3], '#c8c8d0', { a: 0.7 });
      house(k, 8, 4, 12, 10, 7, '#a87a4a', '#5a3a2a');
      [[-44, 12], [30, 10], [40, -2], [-40, -4], [24, 18]].forEach(function (p, i) {
        k.pine(p[0], p[1], 0.9 + (i % 2) * 0.3, '#24502e');
      });
      // the campfire, a ranger warming up, a lifeguard carrying someone in
      k.shape('cone', [-4, 1.2, 16], [2.4, 2.4, 2.4], '#ff7a1a', { m: 'neon' });
      k.box([-4, 0.3, 16], [3, 0.6, 0.6], WOOD);
      ranger(k, -8, 18, 1.8, { anim: 'idle' });
      lifeguard(k, 14, 18, 2.8, { carry: true, look: 2, time: 0.4 });
      stranded(k, 24, 0, 6, -2.2, 1);
      crate(k, 0, 0, 26, true);
    }
  });

  // ---------------------------------------------------------- Palm Key
  Thumbs.registerWorld('cc_palmkey', {
    sky: { top: '#3a1a14', horizon: '#d0602a', sun: [0.4, 0.5, 0.3], clouds: 0.85, tint: '#ffa070' },
    camera: [[36, 18, 44], [0, 10, -10], 46],
    build: function (parts, k) {
      k.box([0, -0.5, 0], [150, 1, 120], '#4a9a3a');
      k.box([0, 0.1, 30], [150, 0.4, 24], '#f2e0a8');
      k.box([0, -0.2, 50], [150, 0.4, 20], '#3ac0d8');
      // the volcano, stepped, lava pouring down the front
      for (var t = 0; t < 8; t++) {
        k.shape('cyl', [-6, 1.6 + t * 3.2, -36], [60 - t * 6.5, 3.2, 60 - t * 6.5], t % 2 ? '#5a4a3a' : '#6a5a48');
      }
      k.shape('cyl', [-6, 27, -36], [9, 2, 9], LAVA, { m: 'neon' });
      k.box([-6, 13.6, -18.5], [6, 1.2, 36], LAVA, { m: 'neon', r: [0.785, 0, 0] });
      k.box([-6, 0.5, -2], [14, 1, 10], LAVA, { m: 'neon' });
      for (var p = 0; p < 6; p++) {
        k.shape('sph', [-20 + p * 9, 30 + (p % 3) * 6, -22 + p * 3], [2, 2, 2], '#ffb43a', { m: 'neon' });
        k.shape('sph', [-21 + p * 9, 33 + (p % 3) * 6, -24 + p * 3], [1.6, 1.6, 1.6], '#5a5050', { a: 0.6 });
      }
      // bungalows on stilts, palms, the hotel
      [[22, 40], [34, 40], [10, 42]].forEach(function (b) {
        k.box([b[0] - 2, 1.5, b[1]], [0.5, 3, 0.5], WOOD); k.box([b[0] + 2, 1.5, b[1]], [0.5, 3, 0.5], WOOD);
        k.box([b[0], 4.5, b[1]], [6, 3, 5], '#c8a070');
        k.box([b[0], 6.6, b[1]], [7.4, 1.2, 6.4], '#d8b060');
      });
      k.box([34, 9, -6], [16, 18, 12], '#f2f0ea');
      for (var w = 0; w < 4; w++) {
        k.box([34, 3 + w * 4, 0.05], [13, 1.8, 0.1], '#ffd88a', { m: 'glass' });
        k.box([34, 1.6 + w * 4, 0.9], [14, 0.4, 1.8], '#e8e0d0');
        k.box([34, 2.4 + w * 4, 1.7], [14, 1.2, 0.15], '#ffffff', { a: 0.7 });
      }
      k.box([34, 19.2, -6], [17, 0.6, 13], '#c87a4a');
      palm(k, -30, 20, 12, 0.6); palm(k, 18, 22, 11, -0.5); palm(k, -40, 30, 13, 0.4); palm(k, 40, 24, 10, -0.6);
      lifeguard(k, 4, 22, 2.9, { time: 0.2 });
      ranger(k, -12, 26, 2.6, { carry: true, look: 3, time: 0.7 });
      stranded(k, -18, 0, 6, 2.2, 0);
      crate(k, -24, 0, 34, false);
    }
  });

  // ---------------------------------------------------------- Old Town
  Thumbs.registerWorld('cc_oldtown', {
    sky: { top: '#4a2a1a', horizon: '#d8803a', sun: [0.4, 0.5, -0.5], clouds: 0.7, tint: '#ffb880' },
    camera: [[50, 26, 66], [-2, 6, 0], 46],
    build: function (parts, k) {
      k.box([0, -0.5, -16.5], [150, 1, 77], '#a89a88');
      k.box([0, -0.5, 47], [150, 1, 26], '#a89a88');
      k.box([0, -3, 28], [150, 3, 12], '#5a5448');
      k.box([0, -1.2, 28], [150, 0.4, 12], '#3a6a8a');
      // the stone bridge over it, on two arches
      k.box([8, 0.6, 28], [8, 1.2, 16], '#a89a88');
      k.box([4.4, 1.8, 28], [0.8, 1.2, 16], '#988a78'); k.box([11.6, 1.8, 28], [0.8, 1.2, 16], '#988a78');
      k.box([8, -1.2, 28], [7, 2.4, 2], '#988a78');
      // the timbered row, two of them alight
      var walls = ['#e8dcc0', '#d8c8a8', '#f0e4c8', '#c8b898'];
      for (var i = 0; i < 5; i++) {
        var hx = -36 + i * 16;
        house(k, hx, -6, 13, 10, 9, walls[i % 4], i % 2 ? '#7a3a2a' : '#5a3a2a');
        k.box([hx - 3, 4.5, -0.9], [0.5, 9, 0.2], '#5a3a24');
        k.box([hx + 3, 4.5, -0.9], [0.5, 9, 0.2], '#5a3a24');
        if (i === 1 || i === 2) {
          for (var f = 0; f < 6; f++) {
            k.shape('cone', [hx - 5 + f * 2, 12 + (f % 2) * 1.5, -6 + (f % 3) - 1], [2.6, 5 + (f % 3) * 1.6, 2.6],
                    f % 2 ? '#ffd23a' : '#ff7a1a', { m: 'neon' });
          }
          for (var m = 0; m < 5; m++) {
            k.shape('sph', [hx + m * 1.6, 18 + m * 5, -7 - m * 1.4], [6 + m * 1.6, 5 + m, 6 + m * 1.6],
                    m < 2 ? '#3a3430' : '#5a5450', { a: 0.75 - m * 0.1 });
          }
        }
      }
      // the cathedral tower behind
      k.box([30, 16, -24], [8, 32, 8], '#c8bca4');
      k.shape('cone', [30, 38, -24], [9, 12, 9], '#4a4a5a');
      k.box([18, 10, -26], [16, 20, 14], '#d8ccb4');
      for (var g = 0; g < 4; g++) k.box([18, 20.6 + g * 1.4, -26], [16.6 - g * 3.6, 1.4, 15], '#4a4a5a');
      k.shape('cyl', [18, 13, -18.9], [5, 5, 0.2], '#c8a8d8', { r: [Math.PI / 2, 0, 0], m: 'glass' });
      k.box([18, 3, -18.95], [3.4, 6, 0.2], '#5a3a24');
      k.shape('cyl', [30, 26, -19.9], [3.4, 3.4, 0.2], '#f2e8c8', { r: [Math.PI / 2, 0, 0] });
      lifeguard(k, -4, 12, 2.8, { carry: true, look: 0, time: 0.3 });
      ranger(k, 10, 14, 3.1, { time: 0.6 });
      stranded(k, -26, 0, 6, 2.6, 3);
      crate(k, 22, 0, 10, true);
    }
  });
})(window);
