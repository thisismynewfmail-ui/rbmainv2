/* BLOCKHAVEN engine -- particles.
   Drives the Unusual hat effects (which follow a player everywhere) plus all
   the combat feedback: muzzle flashes, impacts, explosions and pickups. */
(function (global) {
  'use strict';

  var M = GLX.mat;
  var MAX = 2600;

  var VERT = [
    'precision highp float;',
    'attribute vec2 aQuad;',
    'attribute vec3 aPos;',
    'attribute vec4 aColor;',
    'attribute vec3 aMeta;',   // size, rotation, shape index
    'uniform mat4 uViewProj;',
    'uniform vec3 uRight;',
    'uniform vec3 uUp;',
    'varying vec4 vColor;',
    'varying vec2 vUV;',
    'varying float vShape;',
    'void main() {',
    '  float c = cos(aMeta.y), s = sin(aMeta.y);',
    '  vec2 q = vec2(aQuad.x * c - aQuad.y * s, aQuad.x * s + aQuad.y * c);',
    '  vec3 world = aPos + uRight * (q.x * aMeta.x) + uUp * (q.y * aMeta.x);',
    '  vUV = aQuad * 0.5 + 0.5;',
    '  vColor = aColor;',
    '  vShape = aMeta.z;',
    '  gl_Position = uViewProj * vec4(world, 1.0);',
    '}'
  ].join('\n');

  var FRAG = [
    'precision highp float;',
    'varying vec4 vColor;',
    'varying vec2 vUV;',
    'varying float vShape;',
    'uniform sampler2D uTex;',
    'void main() {',
    '  float col = mod(vShape, ATLAS_COLS);',
    '  float row = floor(vShape / ATLAS_COLS);',
    '  vec2 uv = vec2((col + vUV.x) / ATLAS_COLS, (row + vUV.y) / ATLAS_ROWS);',
    '  vec4 tex = texture2D(uTex, uv);',
    '  gl_FragColor = vec4(vColor.rgb * tex.rgb, tex.a * vColor.a);',
    '}'
  ].join('\n');

  /* ------------------------------------------------------------- the atlas
     Every particle is a billboarded quad showing one cell of this sheet.  The
     cell is a greyscale mask: the shader multiplies its RGB into the
     particle's colour and its alpha into the particle's alpha, so a cell
     carries the SHAPE in alpha and the SHADING in brightness.  White reads as
     the pure tint, mid grey as a darker version of it, and a hole punched in
     the alpha reads as a hole.  That is enough to draw a skull with sunken
     sockets or a lantern with a face brighter than its rind, out of one
     colour ramp.

     Cells are authored in ordinary screen coordinates -- y = 0 is the top of
     the particle -- because ``cell()`` flips the context to cancel out the
     texture's own flip (UNPACK_FLIP_Y is off, so canvas row 0 samples at the
     BOTTOM of the quad).  Before that flip the flame teardrop and the star
     both came out pointing at the floor.

     Keep art a few pixels clear of the cell edge: the sheet is sampled with
     linear filtering, so anything touching the border bleeds into whatever
     is drawn next to it. */
  var ATLAS_COLS = 4;
  var CELL = 128;

  // ---------------------------------------------------------- draw helpers
  function bar(c, x0, y0, x1, y1, w) {
    c.lineCap = 'round';
    c.lineWidth = w;
    c.beginPath();
    c.moveTo(x0, y0);
    c.lineTo(x1, y1);
    c.stroke();
  }

  function dot(c, x, y, r) {
    c.beginPath();
    c.arc(x, y, r, 0, Math.PI * 2);
    c.fill();
  }

  function poly(c, points) {
    c.beginPath();
    for (var i = 0; i < points.length; i++) {
      if (i === 0) c.moveTo(points[i][0], points[i][1]);
      else c.lineTo(points[i][0], points[i][1]);
    }
    c.closePath();
    c.fill();
  }

  /* Cut a hole rather than paint a dark patch: a socket that is see-through
     stays a socket whatever colour the particle happens to be tinted. */
  function punch(c, fn) {
    c.save();
    c.globalCompositeOperation = 'destination-out';
    c.fillStyle = '#000';
    c.strokeStyle = '#000';
    fn();
    c.restore();
  }

  /* The shapes, in atlas order.  Adding one here is all it takes -- the sheet
     grows a row when it needs to and the shader is told how many. */
  var SHAPE_CELLS = [
    ['puff', function (c) {
      var g = c.createRadialGradient(64, 64, 2, 64, 64, 62);
      g.addColorStop(0, 'rgba(255,255,255,1)');
      g.addColorStop(0.45, 'rgba(255,255,255,0.55)');
      g.addColorStop(1, 'rgba(255,255,255,0)');
      c.fillStyle = g; c.fillRect(0, 0, CELL, CELL);
    }],
    ['flame', function (c) {
      var fg = c.createRadialGradient(64, 78, 4, 64, 70, 56);
      fg.addColorStop(0, 'rgba(255,255,255,1)');
      fg.addColorStop(0.5, 'rgba(255,255,255,0.7)');
      fg.addColorStop(1, 'rgba(255,255,255,0)');
      c.fillStyle = fg;
      c.beginPath();
      c.moveTo(64, 8);
      c.bezierCurveTo(104, 58, 100, 112, 64, 118);
      c.bezierCurveTo(28, 112, 24, 58, 64, 8);
      c.fill();
    }],
    ['star', function (c) {
      c.fillStyle = '#ffffff';
      c.beginPath();
      for (var i = 0; i < 10; i++) {
        var ang = -Math.PI / 2 + i * Math.PI / 5;
        var rad = (i % 2 === 0) ? 58 : 22;
        var x = 64 + Math.cos(ang) * rad, y = 64 + Math.sin(ang) * rad;
        if (i === 0) c.moveTo(x, y); else c.lineTo(x, y);
      }
      c.closePath(); c.fill();
    }],
    ['flake', function (c) {
      c.strokeStyle = '#ffffff'; c.lineWidth = 8; c.lineCap = 'round';
      for (var i = 0; i < 6; i++) {
        var a = (i / 6) * Math.PI * 2;
        c.beginPath();
        c.moveTo(64, 64);
        c.lineTo(64 + Math.cos(a) * 52, 64 + Math.sin(a) * 52);
        c.stroke();
        c.beginPath();
        c.moveTo(64 + Math.cos(a) * 30, 64 + Math.sin(a) * 30);
        c.lineTo(64 + Math.cos(a) * 42 + Math.cos(a + 1.2) * 16,
                 64 + Math.sin(a) * 42 + Math.sin(a + 1.2) * 16);
        c.stroke();
      }
    }],
    ['spark', function (c) {
      var sg = c.createLinearGradient(64, 10, 64, 118);
      sg.addColorStop(0, 'rgba(255,255,255,0)');
      sg.addColorStop(0.5, 'rgba(255,255,255,1)');
      sg.addColorStop(1, 'rgba(255,255,255,0)');
      c.fillStyle = sg; c.fillRect(52, 8, 24, 112);
    }],
    ['bubble', function (c) {
      c.strokeStyle = 'rgba(255,255,255,0.95)'; c.lineWidth = 7;
      c.beginPath(); c.arc(64, 64, 50, 0, Math.PI * 2); c.stroke();
      c.fillStyle = 'rgba(255,255,255,0.55)';
      dot(c, 46, 44, 12);
    }],
    ['ray', function (c) {
      var rg = c.createLinearGradient(0, 64, 128, 64);
      rg.addColorStop(0, 'rgba(255,255,255,0)');
      rg.addColorStop(0.5, 'rgba(255,255,255,1)');
      rg.addColorStop(1, 'rgba(255,255,255,0)');
      c.fillStyle = rg; c.fillRect(0, 50, 128, 28);
    }],
    ['ring', function (c) {
      c.strokeStyle = '#ffffff'; c.lineWidth = 14;
      c.beginPath(); c.arc(64, 64, 46, 0, Math.PI * 2); c.stroke();
    }],

    /* ---------------------------------------------------------- the crypt */
    ['bone', function (c) {
      // A femur: one shaft, four knuckles.  Drawn on the diagonal so a drift
      // of them does not read as a row of matchsticks.
      c.save();
      c.translate(64, 64); c.rotate(-0.55); c.translate(-64, -64);
      c.strokeStyle = '#efefef';
      bar(c, 64, 34, 64, 94, 21);
      c.fillStyle = '#ffffff';
      dot(c, 53, 30, 15); dot(c, 75, 30, 15);
      dot(c, 53, 98, 15); dot(c, 75, 98, 15);
      // a soft core line gives the shaft some roundness
      c.strokeStyle = 'rgba(190,190,190,0.85)';
      bar(c, 70, 40, 70, 88, 5);
      c.restore();
    }],
    ['skull', function (c) {
      c.fillStyle = '#f2f2f2';
      c.beginPath(); c.arc(64, 56, 40, Math.PI, 0); c.fill();
      c.fillRect(24, 56, 80, 22);
      // cheekbones taper into the jaw
      poly(c, [[26, 74], [102, 74], [92, 96], [36, 96]]);
      c.fillStyle = '#ffffff';
      poly(c, [[44, 92], [84, 92], [80, 110], [48, 110]]);
      punch(c, function () {
        c.beginPath(); c.ellipse(49, 58, 13, 15, 0, 0, Math.PI * 2); c.fill();
        c.beginPath(); c.ellipse(79, 58, 13, 15, 0, 0, Math.PI * 2); c.fill();
        poly(c, [[64, 66], [75, 86], [53, 86]]);          // nasal cavity
        for (var i = 0; i < 3; i++) bar(c, 54 + i * 10, 92, 54 + i * 10, 110, 4);
      });
    }],
    ['pumpkin', function (c) {
      // Stem first so the rind overlaps its foot rather than the other way.
      c.strokeStyle = '#8f8f8f';
      bar(c, 64, 40, 59, 18, 13);
      // The rind is mid grey on purpose: the face is painted pure white over
      // it, so whatever orange the particle is tinted, the face comes out as
      // the full tint and the rind as a darker version of the same -- which
      // is a lit lantern rather than an orange blob with a hole in it.
      c.fillStyle = '#9d9d9d';
      c.beginPath(); c.ellipse(64, 74, 45, 39, 0, 0, Math.PI * 2); c.fill();
      c.save();                       // ribs stay inside the rind
      c.beginPath(); c.ellipse(64, 74, 45, 39, 0, 0, Math.PI * 2); c.clip();
      c.strokeStyle = 'rgba(60,60,60,0.55)'; c.lineWidth = 4; c.lineCap = 'round';
      [-30, -12, 12, 30].forEach(function (dx) {
        c.beginPath();
        c.moveTo(64 + dx * 0.4, 32);
        c.quadraticCurveTo(64 + dx * 1.45, 74, 64 + dx * 0.4, 116);
        c.stroke();
      });
      c.restore();
      c.fillStyle = '#ffffff';
      poly(c, [[37, 70], [59, 70], [48, 50]]);             // triangle eyes
      poly(c, [[91, 70], [69, 70], [80, 50]]);
      poly(c, [[64, 80], [72, 72], [56, 72]]);             // nose
      poly(c, [[36, 88], [92, 88], [84, 104], [74, 94],    // jagged grin
               [64, 102], [54, 94], [44, 104]]);
    }],
    ['ribcage', function (c) {
      c.strokeStyle = '#f0f0f0'; c.lineCap = 'round';
      bar(c, 64, 22, 64, 106, 13);                         // spine
      c.lineWidth = 9;
      for (var i = 0; i < 4; i++) {
        var y = 34 + i * 20;
        var w = 40 - i * 4;
        c.beginPath();
        c.moveTo(60, y);
        c.quadraticCurveTo(60 - w, y + 4, 62 - w * 0.5, y + 20);
        c.stroke();
        c.beginPath();
        c.moveTo(68, y);
        c.quadraticCurveTo(68 + w, y + 4, 66 + w * 0.5, y + 20);
        c.stroke();
      }
    }],
    ['bat', function (c) {
      c.fillStyle = '#ffffff';
      c.beginPath(); c.ellipse(64, 66, 10, 17, 0, 0, Math.PI * 2); c.fill();
      poly(c, [[57, 52], [61, 38], [65, 52]]);             // ears
      poly(c, [[63, 52], [67, 38], [71, 52]]);
      c.fillStyle = '#ededed';
      [-1, 1].forEach(function (s) {                       // scalloped wings
        c.beginPath();
        c.moveTo(64 + s * 8, 56);
        c.quadraticCurveTo(64 + s * 44, 40, 64 + s * 60, 58);
        c.quadraticCurveTo(64 + s * 48, 58, 64 + s * 44, 74);
        c.quadraticCurveTo(64 + s * 34, 60, 64 + s * 26, 78);
        c.quadraticCurveTo(64 + s * 18, 64, 64 + s * 8, 80);
        c.closePath(); c.fill();
      });
    }],
    ['wisp', function (c) {
      // a bright head trailing off into nothing
      var g = c.createRadialGradient(64, 44, 3, 64, 48, 34);
      g.addColorStop(0, 'rgba(255,255,255,1)');
      g.addColorStop(0.55, 'rgba(255,255,255,0.65)');
      g.addColorStop(1, 'rgba(255,255,255,0)');
      c.fillStyle = g;
      c.beginPath(); c.arc(64, 46, 34, 0, Math.PI * 2); c.fill();
      var t = c.createLinearGradient(64, 60, 64, 120);
      t.addColorStop(0, 'rgba(255,255,255,0.7)');
      t.addColorStop(1, 'rgba(255,255,255,0)');
      c.fillStyle = t;
      c.beginPath();
      c.moveTo(48, 62);
      c.quadraticCurveTo(70, 92, 58, 120);
      c.quadraticCurveTo(76, 92, 80, 62);
      c.closePath(); c.fill();
    }],
    ['rune', function (c) {
      c.strokeStyle = '#ffffff'; c.lineWidth = 7; c.lineJoin = 'round';
      c.beginPath();                                       // hex border
      for (var i = 0; i < 6; i++) {
        var a = -Math.PI / 2 + i * Math.PI / 3;
        var x = 64 + Math.cos(a) * 50, y = 64 + Math.sin(a) * 50;
        if (i === 0) c.moveTo(x, y); else c.lineTo(x, y);
      }
      c.closePath(); c.stroke();
      c.lineWidth = 9; c.lineCap = 'round';                // the glyph
      c.strokeStyle = '#ffffff';
      bar(c, 50, 42, 50, 86, 9);
      bar(c, 50, 64, 78, 44, 9);
      bar(c, 50, 74, 78, 88, 9);
    }],
    ['spider', function (c) {
      c.strokeStyle = '#efefef'; c.lineCap = 'round'; c.lineWidth = 6;
      [-1, 1].forEach(function (s) {
        for (var i = 0; i < 4; i++) {
          var y = 54 + i * 9;
          var reach = 36 - Math.abs(i - 1.5) * 5;
          c.beginPath();
          c.moveTo(64 + s * 10, y);
          c.quadraticCurveTo(64 + s * (reach + 6), y - 14, 64 + s * reach, y + 18);
          c.stroke();
        }
      });
      c.fillStyle = '#ffffff';
      c.beginPath(); c.ellipse(64, 74, 20, 23, 0, 0, Math.PI * 2); c.fill();
      c.beginPath(); c.ellipse(64, 48, 13, 12, 0, 0, Math.PI * 2); c.fill();
      punch(c, function () { dot(c, 59, 46, 4); dot(c, 69, 46, 4); });
    }],
    ['feather', function (c) {
      c.fillStyle = '#e6e6e6';
      [-1, 1].forEach(function (s) {                       // the two vanes
        c.beginPath();
        c.moveTo(64, 14);
        c.quadraticCurveTo(64 + s * 30, 52, 64 + s * 12, 104);
        c.quadraticCurveTo(64 + s * 4, 76, 64, 14);
        c.closePath(); c.fill();
      });
      c.strokeStyle = '#ffffff';
      bar(c, 64, 16, 66, 116, 5);                          // the quill
      punch(c, function () {                               // split the barbs
        for (var i = 0; i < 5; i++) {
          var y = 34 + i * 15;
          bar(c, 64, y, 64 - 26 + i * 3, y + 9, 3);
          bar(c, 64, y + 7, 64 + 26 - i * 3, y + 16, 3);
        }
      });
    }],
    ['candle', function (c) {
      c.fillStyle = '#dcdcdc';
      c.fillRect(50, 54, 28, 60);
      c.beginPath(); c.ellipse(64, 54, 14, 6, 0, 0, Math.PI * 2); c.fill();
      c.fillStyle = '#c0c0c0';                             // a drip down one side
      c.beginPath();
      c.moveTo(50, 60); c.quadraticCurveTo(44, 78, 50, 92);
      c.closePath(); c.fill();
      c.strokeStyle = '#8a8a8a';
      bar(c, 64, 52, 64, 44, 4);                           // wick
      var fg = c.createRadialGradient(64, 32, 2, 64, 30, 22);
      fg.addColorStop(0, 'rgba(255,255,255,1)');
      fg.addColorStop(0.55, 'rgba(255,255,255,0.8)');
      fg.addColorStop(1, 'rgba(255,255,255,0)');
      c.fillStyle = fg;
      c.beginPath();
      c.moveTo(64, 8);
      c.bezierCurveTo(80, 26, 78, 44, 64, 46);
      c.bezierCurveTo(50, 44, 48, 26, 64, 8);
      c.fill();
    }]
  ];

  var ATLAS_ROWS = Math.ceil(SHAPE_CELLS.length / ATLAS_COLS);
  var SHAPES = {};
  for (var si = 0; si < SHAPE_CELLS.length; si++) SHAPES[SHAPE_CELLS[si][0]] = si;

  function buildAtlas() {
    var canvas = document.createElement('canvas');
    canvas.width = CELL * ATLAS_COLS;
    canvas.height = CELL * ATLAS_ROWS;
    var ctx = canvas.getContext('2d');
    for (var i = 0; i < SHAPE_CELLS.length; i++) {
      ctx.save();
      // Into the cell, then flipped: see the note above the shape table.
      ctx.translate((i % ATLAS_COLS) * CELL,
                    Math.floor(i / ATLAS_COLS) * CELL + CELL);
      ctx.scale(1, -1);
      ctx.beginPath();
      ctx.rect(0, 0, CELL, CELL);
      ctx.clip();                 // nothing may spill into the neighbouring cell
      ctx.fillStyle = '#ffffff';
      ctx.strokeStyle = '#ffffff';
      SHAPE_CELLS[i][1](ctx);
      ctx.restore();
    }
    return canvas;
  }

  /* The sheet's grid is only known once the shape table below has been
     read, which is after FRAG is written -- so the two sizes go in as names
     and are filled in here, at compile time.  GLSL wants float literals,
     hence toFixed(1). */
  function atlasFrag() {
    return FRAG.replace(/ATLAS_COLS/g, ATLAS_COLS.toFixed(1))
               .replace(/ATLAS_ROWS/g, ATLAS_ROWS.toFixed(1));
  }

  function Particles(gl) {
    this.gl = gl;
    this.program = GLX.compile(gl, VERT, atlasFrag(), 'particles');
    this.enabled = true;
    this.count = 0;
    this.pos = new Float32Array(MAX * 3);
    this.vel = new Float32Array(MAX * 3);
    this.col = new Float32Array(MAX * 4);
    this.meta = new Float32Array(MAX * 3);      // size, rotation, shape
    this.life = new Float32Array(MAX);
    this.maxLife = new Float32Array(MAX);
    this.grow = new Float32Array(MAX);
    this.grav = new Float32Array(MAX);
    this.spin = new Float32Array(MAX);
    this.blend = new Uint8Array(MAX);
    this.ramp = new Float32Array(MAX * 12);     // up to 4 colours per particle
    this.rampLen = new Uint8Array(MAX);
    this.orbit = new Float32Array(MAX * 3);     // speed, radius, phase
    this.origin = new Float32Array(MAX * 3);
    this.emitters = {};

    this.atlas = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, this.atlas);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, buildAtlas());
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

    this.quad = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, this.quad);
    gl.bufferData(gl.ARRAY_BUFFER,
                  new Float32Array([-1, -1, 1, -1, 1, 1, -1, -1, 1, 1, -1, 1]),
                  gl.STATIC_DRAW);
    this.instanceBuffer = gl.createBuffer();
    this.instanceData = new Float32Array(MAX * 10);
  }

  Particles.prototype.spawn = function (opts) {
    if (!this.enabled) return;
    if (this.count >= MAX) return;
    var i = this.count++;
    this.pos[i * 3] = opts.p[0];
    this.pos[i * 3 + 1] = opts.p[1];
    this.pos[i * 3 + 2] = opts.p[2];
    this.vel[i * 3] = opts.v[0];
    this.vel[i * 3 + 1] = opts.v[1];
    this.vel[i * 3 + 2] = opts.v[2];
    this.origin[i * 3] = opts.origin ? opts.origin[0] : opts.p[0];
    this.origin[i * 3 + 1] = opts.origin ? opts.origin[1] : opts.p[1];
    this.origin[i * 3 + 2] = opts.origin ? opts.origin[2] : opts.p[2];
    this.life[i] = opts.life;
    this.maxLife[i] = opts.life;
    this.meta[i * 3] = opts.size;
    /* Smoke does not care which way up it is, so it starts at any angle.  A
       skull does: half of them landing upside down is the difference between
       a swarm and a mess.  ``upright`` starts one the right way up with just
       enough jitter that a cluster does not look stamped. */
    this.meta[i * 3 + 1] = opts.upright
      ? (Math.random() - 0.5) * (opts.wobble === undefined ? 0.5 : opts.wobble)
      : Math.random() * Math.PI * 2;
    /* An effect may name several shapes and get a mix of them, which is the
       difference between a stream of identical skulls and a scattering of
       bits of skeleton.  One shape per particle either way -- the sheet is
       sampled once -- so the choice is made here, at birth. */
    var shape = opts.shape;
    if (opts.shapes && opts.shapes.length) {
      shape = opts.shapes[(Math.random() * opts.shapes.length) | 0];
    }
    this.meta[i * 3 + 2] = SHAPES[shape] === undefined ? 0 : SHAPES[shape];
    this.grow[i] = opts.grow || 0;
    this.grav[i] = opts.gravity || 0;
    this.spin[i] = opts.spin || 0;
    this.blend[i] = opts.blend === 'add' ? 1 : 0;
    var colours = opts.colors || ['#ffffff'];
    this.rampLen[i] = Math.min(4, colours.length);
    for (var k = 0; k < this.rampLen[i]; k++) {
      var rgb = M.hexToRgb(colours[k]);
      this.ramp[i * 12 + k * 3] = rgb[0];
      this.ramp[i * 12 + k * 3 + 1] = rgb[1];
      this.ramp[i * 12 + k * 3 + 2] = rgb[2];
    }
    this.orbit[i * 3] = opts.orbit || 0;
    this.orbit[i * 3 + 1] = opts.orbitRadius || 0;
    this.orbit[i * 3 + 2] = Math.random() * Math.PI * 2;
    this.col[i * 4 + 3] = 1;
  };

  Particles.prototype.remove = function (i) {
    var last = --this.count;
    if (i === last) return;
    var arrays3 = ['pos', 'vel', 'meta', 'orbit', 'origin'];
    for (var a = 0; a < arrays3.length; a++) {
      var arr = this[arrays3[a]];
      arr[i * 3] = arr[last * 3];
      arr[i * 3 + 1] = arr[last * 3 + 1];
      arr[i * 3 + 2] = arr[last * 3 + 2];
    }
    for (var k = 0; k < 12; k++) this.ramp[i * 12 + k] = this.ramp[last * 12 + k];
    for (k = 0; k < 4; k++) this.col[i * 4 + k] = this.col[last * 4 + k];
    this.life[i] = this.life[last];
    this.maxLife[i] = this.maxLife[last];
    this.grow[i] = this.grow[last];
    this.grav[i] = this.grav[last];
    this.spin[i] = this.spin[last];
    this.blend[i] = this.blend[last];
    this.rampLen[i] = this.rampLen[last];
  };

  /* Attach a persistent effect (an Unusual hat) to a key. */
  Particles.prototype.setEmitter = function (key, effect, position) {
    if (!effect) { delete this.emitters[key]; return; }
    var emitter = this.emitters[key];
    if (!emitter || emitter.effect !== effect) {
      emitter = { effect: effect, acc: 0, p: position.slice(), active: true };
      this.emitters[key] = emitter;
    }
    emitter.p[0] = position[0];
    emitter.p[1] = position[1];
    emitter.p[2] = position[2];
    emitter.active = true;
  };

  Particles.prototype.clearEmitter = function (key) { delete this.emitters[key]; };

  Particles.prototype.updateEmitters = function (dt) {
    var keys = Object.keys(this.emitters);
    for (var k = 0; k < keys.length; k++) {
      var emitter = this.emitters[keys[k]];
      if (!emitter.active) continue;
      var e = emitter.effect;
      emitter.acc += (e.rate || 12) * dt;
      var spawnCount = Math.floor(emitter.acc);
      emitter.acc -= spawnCount;
      spawnCount = Math.min(spawnCount, 6);
      for (var n = 0; n < spawnCount; n++) {
        var radius = e.radius === undefined ? 0.5 : e.radius;
        var ang = Math.random() * Math.PI * 2;
        var rr = Math.sqrt(Math.random()) * radius;
        var spread = e.spread || 0.4;
        var rise = e.rise || [0.5, 1.2];
        this.spawn({
          p: [emitter.p[0] + Math.cos(ang) * rr,
              emitter.p[1] + (Math.random() - 0.2) * 0.25,
              emitter.p[2] + Math.sin(ang) * rr],
          origin: emitter.p,
          v: [(Math.random() - 0.5) * spread * 2,
              rise[0] + Math.random() * (rise[1] - rise[0]),
              (Math.random() - 0.5) * spread * 2],
          life: (e.life ? e.life[0] + Math.random() * (e.life[1] - e.life[0]) : 1),
          size: (e.size ? e.size[0] + Math.random() * (e.size[1] - e.size[0]) : 0.4),
          grow: e.grow || 0,
          gravity: e.gravity || 0,
          spin: (Math.random() - 0.5) * (e.spin || 0),
          blend: e.blend || 'normal',
          colors: e.colors,
          shape: e.shape || 'puff',
          shapes: e.shapes,
          upright: e.upright,
          wobble: e.wobble,
          orbit: e.orbit || 0,
          orbitRadius: rr
        });
      }
      emitter.active = false;   // must be refreshed every frame to keep going
    }
  };

  Particles.prototype.update = function (dt) {
    if (!this.enabled) { this.count = 0; return; }
    this.updateEmitters(dt);
    for (var i = 0; i < this.count; i++) {
      this.life[i] -= dt;
      if (this.life[i] <= 0) { this.remove(i); i--; continue; }
      var orbitSpeed = this.orbit[i * 3];
      if (orbitSpeed) {
        this.orbit[i * 3 + 2] += orbitSpeed * dt;
        var radius = this.orbit[i * 3 + 1];
        var phase = this.orbit[i * 3 + 2];
        this.pos[i * 3] = this.origin[i * 3] + Math.cos(phase) * radius;
        this.pos[i * 3 + 2] = this.origin[i * 3 + 2] + Math.sin(phase) * radius;
        this.pos[i * 3 + 1] += this.vel[i * 3 + 1] * dt;
      } else {
        this.vel[i * 3 + 1] += this.grav[i] * dt;
        this.pos[i * 3] += this.vel[i * 3] * dt;
        this.pos[i * 3 + 1] += this.vel[i * 3 + 1] * dt;
        this.pos[i * 3 + 2] += this.vel[i * 3 + 2] * dt;
      }
      this.meta[i * 3] = Math.max(0.01, this.meta[i * 3] + this.grow[i] * dt);
      this.meta[i * 3 + 1] += this.spin[i] * dt;
      // colour ramp across the lifetime
      var t = 1 - (this.life[i] / this.maxLife[i]);
      var n = this.rampLen[i] || 1;
      var f = t * (n - 1);
      var idx = Math.min(n - 2, Math.floor(f));
      if (n === 1) idx = 0;
      var frac = n === 1 ? 0 : f - idx;
      var base = i * 12 + idx * 3;
      var next = n === 1 ? base : base + 3;
      this.col[i * 4] = this.ramp[base] + (this.ramp[next] - this.ramp[base]) * frac;
      this.col[i * 4 + 1] = this.ramp[base + 1] +
        (this.ramp[next + 1] - this.ramp[base + 1]) * frac;
      this.col[i * 4 + 2] = this.ramp[base + 2] +
        (this.ramp[next + 2] - this.ramp[base + 2]) * frac;
      var fade = Math.min(1, this.life[i] / (this.maxLife[i] * 0.45));
      var fadeIn = Math.min(1, t / 0.12);
      this.col[i * 4 + 3] = fade * fadeIn;
    }
  };

  Particles.prototype.draw = function (renderer) {
    if (!this.count || !this.program) return;
    var gl = this.gl, p = this.program;
    var fwd = renderer.forward || [0, 0, 1];
    var flen = Math.hypot(fwd[0], fwd[1], fwd[2]) || 1;
    var right = [-fwd[2] / flen, 0, fwd[0] / flen];
    var rlen = Math.hypot(right[0], right[1], right[2]) || 1;
    right = [right[0] / rlen, 0, right[2] / rlen];
    var up = [
      right[1] * fwd[2] / flen - right[2] * fwd[1] / flen,
      right[2] * fwd[0] / flen - right[0] * fwd[2] / flen,
      right[0] * fwd[1] / flen - right[1] * fwd[0] / flen
    ];

    gl.useProgram(p);
    gl.uniformMatrix4fv(p.uniforms.uViewProj, false, renderer.viewProj);
    gl.uniform3fv(p.uniforms.uRight, right);
    gl.uniform3fv(p.uniforms.uUp, up);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, this.atlas);
    gl.uniform1i(p.uniforms.uTex, 0);
    gl.enable(gl.BLEND);
    gl.depthMask(false);

    for (var pass = 0; pass < 2; pass++) {
      var written = 0;
      for (var i = 0; i < this.count; i++) {
        if (this.blend[i] !== pass) continue;
        var o = written * 10;
        this.instanceData[o] = this.pos[i * 3];
        this.instanceData[o + 1] = this.pos[i * 3 + 1];
        this.instanceData[o + 2] = this.pos[i * 3 + 2];
        this.instanceData[o + 3] = this.col[i * 4];
        this.instanceData[o + 4] = this.col[i * 4 + 1];
        this.instanceData[o + 5] = this.col[i * 4 + 2];
        this.instanceData[o + 6] = this.col[i * 4 + 3];
        this.instanceData[o + 7] = this.meta[i * 3];
        this.instanceData[o + 8] = this.meta[i * 3 + 1];
        this.instanceData[o + 9] = this.meta[i * 3 + 2];
        written++;
      }
      if (!written) continue;
      if (pass === 1) gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
      else gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

      gl.bindBuffer(gl.ARRAY_BUFFER, this.quad);
      gl.enableVertexAttribArray(p.attribs.aQuad);
      gl.vertexAttribPointer(p.attribs.aQuad, 2, gl.FLOAT, false, 0, 0);
      gl.vertexAttribDivisor(p.attribs.aQuad, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, this.instanceBuffer);
      gl.bufferData(gl.ARRAY_BUFFER, this.instanceData.subarray(0, written * 10),
                    gl.DYNAMIC_DRAW);
      var stride = 10 * 4;
      gl.enableVertexAttribArray(p.attribs.aPos);
      gl.vertexAttribPointer(p.attribs.aPos, 3, gl.FLOAT, false, stride, 0);
      gl.vertexAttribDivisor(p.attribs.aPos, 1);
      gl.enableVertexAttribArray(p.attribs.aColor);
      gl.vertexAttribPointer(p.attribs.aColor, 4, gl.FLOAT, false, stride, 12);
      gl.vertexAttribDivisor(p.attribs.aColor, 1);
      gl.enableVertexAttribArray(p.attribs.aMeta);
      gl.vertexAttribPointer(p.attribs.aMeta, 3, gl.FLOAT, false, stride, 28);
      gl.vertexAttribDivisor(p.attribs.aMeta, 1);
      gl.drawArraysInstanced ? gl.drawArraysInstanced(gl.TRIANGLES, 0, 6, written)
        : null;
      if (!gl.drawArraysInstanced) {
        // WebGL1 fallback through the ANGLE extension
        gl.drawArraysInstancedANGLE(gl.TRIANGLES, 0, 6, written);
      }
    }
    gl.depthMask(true);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  };

  // ------------------------------------------------------------- one-shots
  Particles.prototype.burst = function (kind, position, options) {
    options = options || {};
    var n, i, ang, speed;
    if (kind === 'muzzle') {
      for (i = 0; i < 5; i++) {
        this.spawn({ p: position, v: [(Math.random() - 0.5) * 3,
                                      (Math.random() - 0.3) * 2,
                                      (Math.random() - 0.5) * 3],
          life: 0.09 + Math.random() * 0.07, size: 0.5 + Math.random() * 0.4,
          grow: -1.4, gravity: 0, spin: 6, blend: 'add', shape: 'flame',
          colors: ['#fff3b0', '#ffb347', '#ff6b1a'] });
      }
    } else if (kind === 'impact') {
      var colour = options.color || '#c8cbcd';
      for (i = 0; i < 8; i++) {
        this.spawn({ p: position, v: [(Math.random() - 0.5) * 9,
                                      Math.random() * 7,
                                      (Math.random() - 0.5) * 9],
          life: 0.28 + Math.random() * 0.3, size: 0.14 + Math.random() * 0.18,
          grow: -0.2, gravity: -20, spin: 8, blend: 'normal', shape: 'spark',
          colors: [colour, '#8a8f94'] });
      }
      this.spawn({ p: position, v: [0, 0.6, 0], life: 0.5, size: 0.7, grow: 1.4,
        gravity: 0.4, blend: 'normal', shape: 'puff', colors: ['#e8e8e8', '#b9c3cc'] });
    } else if (kind === 'blood') {
      for (i = 0; i < 10; i++) {
        this.spawn({ p: position, v: [(Math.random() - 0.5) * 7,
                                      Math.random() * 5 + 1,
                                      (Math.random() - 0.5) * 7],
          life: 0.32 + Math.random() * 0.25, size: 0.22 + Math.random() * 0.2,
          grow: -0.25, gravity: -22, spin: 4, blend: 'normal', shape: 'puff',
          colors: [options.color || '#d8412f', '#7c1a12'] });
      }
    } else if (kind === 'explosion') {
      var radius = options.radius || 8;
      for (i = 0; i < 34; i++) {
        ang = Math.random() * Math.PI * 2;
        speed = radius * (0.5 + Math.random());
        this.spawn({ p: position,
          v: [Math.cos(ang) * speed, Math.random() * radius * 1.1,
              Math.sin(ang) * speed],
          life: 0.5 + Math.random() * 0.7, size: 1.1 + Math.random() * 1.6,
          grow: 1.6, gravity: -3, spin: 3, blend: 'add', shape: 'flame',
          colors: ['#ffffff', '#ffd24a', '#ff6b1a', '#5a1a04'] });
      }
      for (i = 0; i < 14; i++) {
        ang = Math.random() * Math.PI * 2;
        this.spawn({ p: position,
          v: [Math.cos(ang) * radius * 1.4, Math.random() * 4,
              Math.sin(ang) * radius * 1.4],
          life: 1.1 + Math.random(), size: 1.6, grow: 2.4, gravity: 0.6,
          blend: 'normal', shape: 'puff', colors: ['#4a4a4a', '#2a2a2a'] });
      }
      this.spawn({ p: position, v: [0, 0, 0], life: 0.35, size: radius * 0.8,
        grow: radius * 2.4, gravity: 0, blend: 'add', shape: 'ring',
        colors: ['#fff3b0', '#ff8c1a'] });
    } else if (kind === 'heal') {
      for (i = 0; i < 8; i++) {
        this.spawn({ p: [position[0] + (Math.random() - 0.5) * 2, position[1],
                         position[2] + (Math.random() - 0.5) * 2],
          v: [0, 2.2 + Math.random(), 0], life: 0.8, size: 0.4, grow: -0.2,
          gravity: 0.4, spin: 2, blend: 'add', shape: 'star',
          colors: ['#ffffff', '#8ef2a0', '#2f9d4a'] });
      }
    } else if (kind === 'pickup') {
      for (i = 0; i < 12; i++) {
        ang = (i / 12) * Math.PI * 2;
        this.spawn({ p: position, v: [Math.cos(ang) * 3, 3, Math.sin(ang) * 3],
          life: 0.7, size: 0.4, grow: -0.3, gravity: -3, spin: 5, blend: 'add',
          shape: 'star', colors: ['#ffffff', '#ffd95e', '#e0a615'] });
      }
    } else if (kind === 'dust') {
      for (i = 0; i < 4; i++) {
        this.spawn({ p: position, v: [(Math.random() - 0.5) * 2, Math.random(),
                                      (Math.random() - 0.5) * 2],
          life: 0.45, size: 0.4, grow: 0.8, gravity: 0.2, blend: 'normal',
          shape: 'puff', colors: [options.color || '#cfcfcf', '#ffffff'] });
      }
    } else if (kind === 'coin') {
      for (i = 0; i < 10; i++) {
        ang = Math.random() * Math.PI * 2;
        this.spawn({ p: position, v: [Math.cos(ang) * 2.4, 5 + Math.random() * 3,
                                      Math.sin(ang) * 2.4],
          life: 0.9, size: 0.45, grow: -0.15, gravity: -12, spin: 9,
          blend: 'add', shape: 'star', colors: ['#fff3b0', '#f5c518', '#a97a06'] });
      }
    }
    n = 0; return n;
  };

  Particles.SHAPES = SHAPES;
  /* Also exposed for tooling: the sheet can be dumped to an image, so the
     art can be looked at without hunting for a hat that rolled the effect. */
  Particles.buildAtlas = buildAtlas;

  global.Particles = Particles;
})(window);
