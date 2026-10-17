/* BLOCKHAVEN engine -- pets.
   A pet is a little companion who follows her owner about: a chibi girl
   about half a player's height, built in the same rounded-block language as
   the avatar rig and driven, like it, entirely by a descriptor from the
   server (app/models/pets.py).

   Every species is the same construction -- a big head, a short body in a
   flared dress, stub arms and stockinged legs -- drawn to its own hair, its
   own outfit and one signature feature that moves with her mood: Fern's
   sprout perks up and wilts, Ember's twin tails burn brighter, Luna floats
   and her crescent glows, Mochi's ears perk, droop and twitch, and Pixel's
   antenna light shows what she is feeling.  Sharing the construction is what
   lets one hat, one pin or one cardigan fit all five.

   The face is not a painted texture.  Each expression is a little pixel
   bitmap (EYES, MOUTHS, BROWS below) laid on the face as tiny blocks, so it
   reads as the same voxel style as the rest of her, an eye colour is just a
   colour, a blink is a change of bitmap and a glance is the iris sliding
   across -- and no atlas cell is spent on any of it, however many pets are
   in a world at once.

   Coordinates are world units, +Y up, facing +Z, feet at the origin -- the
   avatar's own conventions.  Pet.build() returns renderer parts exactly as
   Avatar.build() does.  How she moves is a pose (Pet.restPose); a library of
   named actions (Pet.act) turns a clock into poses, Pet.Showcase strings
   them together for a preview, and static/js/game/pets.js decides what she
   does in a world. */
(function (global) {
  'use strict';

  var PI = Math.PI;

  // ------------------------------------------------------------- maths
  /* The renderer reads a part's turn as an euler triple composed
     R = Ry * Rx * Rz (column major) -- the same helpers the avatar rig uses,
     so a pet's bones can nest: hips in the root, torso in the hips, head in
     the torso, a lock of hair in the head. */
  function eulerMatrix(r) {
    var cx = Math.cos(r[0]), sx = Math.sin(r[0]);
    var cy = Math.cos(r[1]), sy = Math.sin(r[1]);
    var cz = Math.cos(r[2]), sz = Math.sin(r[2]);
    return [cy * cz + sy * sx * sz, cx * sz, -sy * cz + cy * sx * sz,
            -cy * sz + sy * sx * cz, cx * cz, sy * sz + cy * sx * cz,
            sy * cx, -sx, cy * cx];
  }

  function mul(a, b) {
    var out = new Array(9);
    for (var col = 0; col < 3; col++) {
      for (var row = 0; row < 3; row++) {
        out[col * 3 + row] = a[row] * b[col * 3] + a[3 + row] * b[col * 3 + 1] +
                             a[6 + row] * b[col * 3 + 2];
      }
    }
    return out;
  }

  function matrixEuler(m) {
    var sx = -m[7];
    if (sx > 0.999999 || sx < -0.999999) {
      return [sx > 0 ? PI / 2 : -PI / 2, Math.atan2(-m[2], m[0]), 0];
    }
    return [Math.asin(sx), Math.atan2(m[6], m[8]), Math.atan2(m[1], m[4])];
  }

  function apply(m, v) {
    return [m[0] * v[0] + m[3] * v[1] + m[6] * v[2],
            m[1] * v[0] + m[4] * v[1] + m[7] * v[2],
            m[2] * v[0] + m[5] * v[1] + m[8] * v[2]];
  }

  var IDENTITY = [1, 0, 0, 0, 1, 0, 0, 0, 1];

  /* A bone: where it is and which way it is turned, in the world. */
  function frame(t, m) {
    return { t: t, m: m, e: null };
  }

  function child(parent, offset, r) {
    var o = apply(parent.m, offset);
    var m = (r && (r[0] || r[1] || r[2])) ? mul(parent.m, eulerMatrix(r)) : parent.m;
    return frame([parent.t[0] + o[0], parent.t[1] + o[1], parent.t[2] + o[2]], m);
  }

  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
  function smooth01(t) { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); }

  // ----------------------------------------------------------- colours
  function rgb(hex) {
    hex = String(hex || '#888888').replace('#', '');
    if (hex.length === 3) hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    var n = parseInt(hex, 16);
    if (isNaN(n)) n = 0x888888;
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  function hex(c) {
    function h(v) {
      v = clamp(Math.round(v), 0, 255).toString(16);
      return v.length < 2 ? '0' + v : v;
    }
    return '#' + h(c[0]) + h(c[1]) + h(c[2]);
  }

  function mix(a, b, t) {
    var x = rgb(a), y = rgb(b);
    return hex([x[0] + (y[0] - x[0]) * t, x[1] + (y[1] - x[1]) * t,
                x[2] + (y[2] - x[2]) * t]);
  }

  /* Darker (amount < 0) or lighter (amount > 0) without washing the hue out. */
  function shade(c, amount) {
    return amount < 0 ? mix(c, '#000000', -amount) : mix(c, '#ffffff', amount);
  }

  function luma(c) {
    var x = rgb(c);
    return (0.299 * x[0] + 0.587 * x[1] + 0.114 * x[2]) / 255;
  }

  // ----------------------------------------------------------- the meshes
  /* The head: softer than a generic rounded box, like the avatar's.  The
     face is laid on it to these same radii (skin() below), so they live in
     one place. */
  var HEAD_ROUND = [0.16, 0.17, 0.17];

  /* The skirt: a rounded box pinched toward one end.  It is baked narrow at
     the bottom (the same taper the female head's jaw uses) and drawn turned
     over, so it is narrow at the waist and flares out to the hem, with the
     smoothstep's flat ends keeping the waistline and the hem straight. */
  if (global.Geometry && Geometry.roundedBox) {
    Geometry.register('petskirt', Geometry.roundedBox([0.14, 0.11, 0.14], 2,
                                                      { bottom: 0.62, from: 1.0 }));
    Geometry.register('pethead', Geometry.roundedBox(HEAD_ROUND, 3));
  }

  // --------------------------------------------------------- measurements
  /* Half a player: the avatar is 5.4 from the soles to the top of the head,
     a pet 2.62 to the crown of her hair.  About two fifths of that is head,
     which is what makes her read as a chibi rather than as a small person. */
  var B = {
    height: 2.62,
    hipY: 0.84,                       // where the legs hang from
    legX: 0.14,
    leg: [0.25, 0.70, 0.27],
    shoe: [0.29, 0.16, 0.40],
    pelvisY: 0.90,
    skirt: { top: 1.04, bottom: 0.58, w: 0.82, d: 0.64 },
    waistY: 1.00,
    torso: [0.54, 0.46, 0.38],
    torsoY: 1.23,
    shoulderY: 1.40,
    armX: 0.36,
    arm: [0.19, 0.50, 0.21],
    armRest: 0.13,                    // arms held a little out, clear of the dress
    neckY: 1.46,
    head: [1.08, 0.98, 0.96],
    headUp: 0.50,                     // head centre above the neck
    hairTop: 0.57,                    // head units: where a hat sits
    faceZ: 0.48
  };

  // ------------------------------------------------------------ the face
  /* Eyes, as seen from the front, for the eye on the viewer's LEFT (the
     pet's right, -X); the other eye is the mirror image.  Column 0 is the
     outer corner, where the lash flicks out.

       K lash          D iris, dark      I iris        L iris, light
       W highlight     S white           H heart       .  nothing        */
  var EYES = {
    open:   ['KKKKK', '.DDWD', '.DIID', '.ILLI', '..LL.'],
    happy:  ['KKKKK', '.DDWD', '.DIID', '..LL.', '.....'],
    joy:    ['.....', '..KK.', '.K..K', '.....', '.....'],
    closed: ['.....', '.....', '.....', 'KKKKK', '.....'],
    sleepy: ['.....', '.....', 'KKKKK', '.DIWD', '..LL.'],
    half:   ['.....', 'KKKKK', '.DDWD', '.ILLI', '..LL.'],
    wide:   ['.KKKK', '.SSSS', '.SDDS', '.SDDS', '..SS.'],
    sad:    ['...KK', '.KKDW', '.DIID', '.ILLI', '..LL.'],
    love:   ['.H.H.', 'HWHHH', 'HHHHH', '.HHH.', '..H..'],
    dizzy:  ['.K..K', '..KK.', '..KK.', '.K..K', '.....'],
    squint: ['.....', 'KK...', '..KKK', 'KK...', '.....'],
    spark:  ['KKKKK', '.DWDW', '.WIWD', '.ILLI', '..LL.']
  };
  // composite expressions: [viewer-left eye, viewer-right eye]
  var EYE_PAIRS = { wink: ['open', 'joy'] };

  /* Brows sit above the eyes and are drawn in front of the fringe, the
     anime way -- the one place hair is allowed to be see-through. */
  var BROWS = {
    angry: ['BB...', '..BBB'],
    sad:   ['...BB', 'BBB..'],
    up:    ['.BBB.', '.....'],
    worry: ['....B', '.BBB.']
  };

  var MOUTHS = {
    smile:  ['K...K', '.KKK.'],
    grin:   ['KKKKK', 'KRRRK', '.KKK.'],
    open:   ['.KKK.', 'KRRRK', '.KKK.'],
    o:      ['.KK.', 'KRRK', '.KK.'],
    flat:   ['KKK'],
    frown:  ['.KKK.', 'K...K'],
    cat:    ['K.K.K', '.K.K.'],
    fang:   ['K...K', '.KKK.', '...W.'],
    yawn:   ['.KKK.', 'KRRRK', 'KRRRK', '.KKK.'],
    tongue: ['KKKKK', '..PP.'],
    pout:   ['.KK.'],
    wavy:   ['.K.K.', 'K.K.K'],
    tiny:   ['.K.', 'K.K']
  };

  var EYE_PX = 0.058, MOUTH_PX = 0.04;
  var EYE_X = 0.235, EYE_Y = -0.12, MOUTH_Y = -0.33;
  /* How far a full glance carries the iris, in pixels, across and up. */
  var GLANCE = [0.9, 0.7];
  /* Everything drawn on the face is a thin block laid on the skin: its front
     FACE_LIFT proud of it -- enough to keep its own depth at any range a pet
     is drawn at, little enough to read as printed on rather than stuck on
     when she turns her head -- and its back FACE_BURY under it, so there is
     never a gap behind it either. */
  var FACE_LIFT = 0.01, FACE_BURY = 0.012;

  /* The front of the head: how far forward of its centre the skin is at
     (x, y) on the face.  The head is the 'pethead' rounded box -- a flat
     face plate that rolls back over an ellipsoidal bevel into the cheeks,
     the brow and the chin -- and this is that surface exactly (the mesh is a
     polygon just inside it, never outside). */
  var HEAD_IN = [0, 1, 2].map(function (a) { return B.head[a] * (0.5 - HEAD_ROUND[a]); });
  var HEAD_R = [0, 1, 2].map(function (a) { return B.head[a] * HEAD_ROUND[a]; });

  function skin(x, y) {
    var dx = Math.max(0, Math.abs(x) - HEAD_IN[0]) / HEAD_R[0];
    var dy = Math.max(0, Math.abs(y) - HEAD_IN[1]) / HEAD_R[1];
    return HEAD_IN[2] + HEAD_R[2] * Math.sqrt(Math.max(0, 1 - dx * dx - dy * dy));
  }

  /* Where one rectangle of the face goes -- [x0, x1] x [y0, y1] as seen from
     the front, in head units -- laid on the skin (or flat at ``level``, on
     the hair) as a thin block: tilted to the surface's slope across it, its
     front ``lift`` proud of the surface everywhere (the bulge of a patch that
     runs onto the curve of a cheek or the chin included) and its back
     ``bury`` under it.  Nothing on the face sinks into it where the head
     rounds off, or stands off it like a visor.  [position, size, turn]. */
  function facePatch(x0, x1, y0, y1, lift, bury, level) {
    var w = x1 - x0, h = y1 - y0;
    var xc = (x0 + x1) / 2, yc = (y0 + y1) / 2;
    if (level !== undefined || (Math.max(-x0, x1) <= HEAD_IN[0] && Math.max(-y0, y1) <= HEAD_IN[1])) {
      // on the flat of the face plate (or of a lock of hair): nothing to fit
      var z = level === undefined ? HEAD_IN[2] + HEAD_R[2] : level;
      return [[xc, yc, z + (lift - bury) / 2], [w, h, lift + bury], null];
    }
    var zc = skin(xc, yc);
    var gx = (skin(x1, yc) - skin(x0, yc)) / w;
    var gy = (skin(xc, y1) - skin(xc, y0)) / h;
    // how far the surface strays from that plane across the patch
    var hi = 0, lo = 0;
    for (var i = 0; i <= 4; i++) {
      for (var j = 0; j <= 2; j++) {
        var x = x0 + w * i / 4, y = y0 + h * j / 2;
        var d = skin(x, y) - (zc + gx * (x - xc) + gy * (y - yc));
        if (d > hi) hi = d;
        if (d < lo) lo = d;
      }
    }
    var yaw = Math.atan(-gx), pitch = Math.atan(gy * Math.cos(yaw));
    var front = hi + lift, back = lo - bury, mid = (front + back) / 2;
    // the block's centre, out along the surface's normal from the patch
    var n = [Math.sin(yaw) * Math.cos(pitch), -Math.sin(pitch), Math.cos(yaw) * Math.cos(pitch)];
    return [[xc + n[0] * mid, yc + n[1] * mid, zc + n[2] * mid],
            [w / Math.cos(yaw), h / Math.cos(pitch), front - back], [pitch, yaw, 0]];
  }

  function onFace(emit, head, x0, x1, y0, y1, colour, opts) {
    var at = facePatch(x0, x1, y0, y1, opts.lift === undefined ? FACE_LIFT : opts.lift,
                       FACE_BURY, undefined);
    return emit(head, at[0], at[1], colour, { t: 'box', r: at[2], m: opts.m, k: opts.k });
  }

  /* A bitmap as rectangles in pixel units -- u across from its left edge, v
     down from its top -- [u0, u1, v0, v1, pixel].  Runs of the same pixel
     along a row become one rectangle, and runs that line up down the rows
     one taller one, so an eye is a handful of parts rather than twenty-five. */
  function rowRuns(row, v0, v1, du, keep, out) {
    var c = 0, w = row.length;
    while (c < w) {
      var ch = row.charAt(c);
      if (!keep(ch)) { c++; continue; }
      var start = c;
      while (c < w && row.charAt(c) === ch) c++;
      out.push([start + du, c + du, v0, v1, ch]);
    }
    return out;
  }

  function stack(rects) {
    var EPS = 1e-6;
    rects.sort(function (a, b) {
      return a[4] < b[4] ? -1 : (a[4] > b[4] ? 1 : (a[0] - b[0] || a[1] - b[1] || a[2] - b[2]));
    });
    var out = [];
    rects.forEach(function (q) {
      var last = out[out.length - 1];
      if (last && last[4] === q[4] && last[5] === q[5] && Math.abs(last[0] - q[0]) < EPS &&
          Math.abs(last[1] - q[1]) < EPS && Math.abs(last[3] - q[2]) < EPS) {
        last[3] = q[3];
      } else {
        out.push(q.slice());
      }
    });
    return out;
  }

  function solid(ch) { return ch !== '.'; }

  function bitmapRects(rows) {
    var out = [];
    rows.forEach(function (row, r) { rowRuns(row, r, r + 1, 0, solid, out); });
    return stack(out);
  }

  /* An eye, with a glance: (du, dv) in pixels, across and down the bitmap.
     The lash (K) stays where it is; everything inside it is the eye, and a
     glance slides the iris across it -- but only within the eye.  What
     slides past the rim goes under the lid, the white (S) shows where it
     slid from, and looking down the iris stays tucked under the upper lid
     the way a real lid follows the eye.  An eye with no lid to slide under
     (the hearts) does not glance.

     The pieces are cut to fit exactly against each other, so no two of them
     ever cover the same patch of face: two blocks at one depth fighting over
     which is in front is a shimmer at any distance, and was the iris
     flickering through the lash whenever she looked up at her owner. */
  function eyeRects(rows, du, dv) {
    var h = rows.length, w = rows[0].length;
    function cell(r, c) { return r >= 0 && r < h ? (rows[r].charAt(c) || '.') : '.'; }
    function lid(ch) { return ch === 'K'; }
    function inside(ch) { return ch !== '.' && ch !== 'K'; }
    function iris(ch) { return inside(ch) && ch !== 'S'; }
    if (rows.join('').indexOf('K') < 0 || (Math.abs(du) < 1e-4 && Math.abs(dv) < 1e-4)) {
      return bitmapRects(rows);
    }
    var out = [];
    for (var r = 0; r < h; r++) {
      rowRuns(rows[r], r, r + 1, 0, lid, out);
      // this row's stretches of eye, whatever is drawn in them
      var spans = [];
      for (var c = 0; c < w; c++) {
        if (!inside(cell(r, c))) continue;
        var last = spans[spans.length - 1];
        if (last && last[1] === c) last[1] = c + 1; else spans.push([c, c + 1]);
      }
      if (!spans.length) continue;
      // a vertical glance brings part of the row above or below into this one
      var bands = dv > 0 ? [[r, r + dv, r - 1], [r + dv, r + 1, r]]
        : (dv < 0 ? [[r, r + 1 + dv, r], [r + 1 + dv, r + 1, r + 1]] : [[r, r + 1, r]]);
      bands.forEach(function (band) {
        if (band[1] - band[0] < 1e-6) return;
        var src = '';
        for (var c = 0; c < w; c++) {
          var ch = cell(band[2], c);
          // under the upper lid the iris stays tucked in as she looks down
          if (band[2] < r && lid(ch)) ch = cell(r, c);
          src += iris(ch) ? ch : '.';
        }
        var pieces = rowRuns(src, band[0], band[1], du, iris, []);
        spans.forEach(function (span) {
          var at = span[0];
          pieces.forEach(function (p) {
            var a = Math.max(p[0], at), b = Math.min(p[1], span[1]);
            if (b - a < 1e-6) return;
            if (a - at > 1e-6) out.push([at, a, band[0], band[1], 'S']);
            out.push([a, b, band[0], band[1], p[4]]);
            at = b;
          });
          if (span[1] - at > 1e-6) out.push([at, span[1], band[0], band[1], 'S']);
        });
      });
    }
    return stack(out);
  }

  /* Where a bitmap's rectangle lands on the face, in head units, for a
     bitmap of ``size`` [w, h] pixels centred on (cx, cy). */
  function onHead(q, size, cx, cy, px, mirror) {
    var a = (q[0] - size[0] / 2) * px, b = (q[1] - size[0] / 2) * px;
    return [mirror ? cx - b : cx + a, mirror ? cx - a : cx + b,
            cy + (size[1] / 2 - q[3]) * px, cy + (size[1] / 2 - q[2]) * px];
  }

  /* Where a bitmap's rectangles go on the face: [pixel, position, size,
     turn] for each.  One that carries a level (a brow pixel over the fringe)
     lies on the hair at that level instead of on the skin. */
  function layout(rows, rects, cx, cy, px, mirror) {
    var size = [rows[0].length, rows.length];
    return rects.map(function (q) {
      var at = onHead(q, size, cx, cy, px, mirror);
      var bury = FACE_BURY;
      if (q[5] !== undefined) {
        // reaching back to the skin, so a pixel only partly over a lock has
        // no air behind the rest of it
        bury += q[5] - Math.min(skin(at[0], at[2]), skin(at[0], at[3]), skin(at[1], at[2]),
                                skin(at[1], at[3]));
      }
      var patch = facePatch(at[0], at[1], at[2], at[3], FACE_LIFT, bury, q[5]);
      return [q[4], patch[0], patch[1], patch[2]];
    });
  }

  /* Laying out an expression is the same sums every frame she wears it, so
     the layouts are kept -- a glance to a sixteenth of a pixel, finer than
     can be seen -- and all thrown away together if they ever pile up. */
  var LAID = {}, LAID_COUNT = 0;
  function laid(key, make) {
    var hit = LAID[key];
    if (hit) return hit;
    if (++LAID_COUNT > 800) { LAID = {}; LAID_COUNT = 1; }
    return (LAID[key] = make());
  }

  function stamp(emit, head, pieces, colours, m, k) {
    for (var i = 0; i < pieces.length; i++) {
      var q = pieces[i], colour = colours[q[0]];
      if (colour) emit(head, q[1], q[2], colour, { t: 'box', r: q[3], m: m, k: k });
    }
  }

  /* What hangs in front of the face is the hair's blocks on the head itself
     whose fronts stand forward of it -- the fringe, the cheek locks, a
     hood's rim -- each a footprint seen from the front (a rectangle turned
     about the face's normal) and how far forward it stands.  This is the
     frontmost of them that overlaps a rectangle of the face, or -Infinity:
     the separating-axis test, exact for any turn, with a block that only
     touches the rectangle's edge not counted. */
  function fringeOver(fringe, x0, x1, y0, y1) {
    var EPS = 1e-3;
    var cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, hx = (x1 - x0) / 2, hy = (y1 - y0) / 2;
    var z = -Infinity;
    fringe.forEach(function (f) {
      var c = Math.cos(f.a), s = Math.sin(f.a), ac = Math.abs(c), as = Math.abs(s);
      var dx = f.x - cx, dy = f.y - cy;
      if (Math.abs(dx) > hx + f.w * ac + f.h * as - EPS) return;
      if (Math.abs(dy) > hy + f.w * as + f.h * ac - EPS) return;
      if (Math.abs(c * dx + s * dy) > f.w + hx * ac + hy * as - EPS) return;
      if (Math.abs(c * dy - s * dx) > f.h + hx * as + hy * ac - EPS) return;
      if (f.z > z) z = f.z;
    });
    return z;
  }

  /* The brows, drawn over the fringe (see BROWS) without standing off her
     head to do it: each pixel lies on whatever is frontmost where it falls,
     the hair or the skin, so from the front a brow reads on top of the hair
     and from the side it is on her, rather than hovering in front of her. */
  function browRects(rows, cx, cy, mirror, fringe) {
    var size = [rows[0].length, rows.length];
    var out = [];
    rows.forEach(function (row, r) {
      var prev = null;
      for (var c = 0; c < row.length; c++) {
        var ch = row.charAt(c);
        if (ch === '.') { prev = null; continue; }
        var at = onHead([c, c + 1, r, r + 1], size, cx, cy, EYE_PX, mirror);
        var z = fringeOver(fringe, at[0], at[1], at[2], at[3]);
        var level = z > -Infinity ? z : undefined;
        if (prev && prev[4] === ch && prev[5] === level) {
          prev[1] = c + 1;
        } else {
          prev = [c, c + 1, r, r + 1, ch, level];
          out.push(prev);
        }
      }
    });
    return stack(out);
  }

  function buildFace(emit, head, col, pose, species, fringe) {
    var eyes = pose.eyes || 'open';
    if (pose.blink > 0.5 && eyes !== 'joy' && eyes !== 'closed' && eyes !== 'dizzy') {
      eyes = 'closed';
    }
    var pair = EYE_PAIRS[eyes] || [eyes, eyes];
    if (pose.blink > 0.5 && EYE_PAIRS[pose.eyes]) pair = ['closed', 'closed'];
    var led = species.led;
    var neon = led ? 'neon' : undefined;
    var iris = col.eyes;
    var colours = led ? {
      K: shade(iris, -0.15), D: iris, I: shade(iris, 0.25), L: shade(iris, 0.45),
      W: '#ffffff', S: shade(iris, 0.6), H: '#ff6fa6'
    } : {
      K: mix(iris, '#120b16', 0.8), D: shade(iris, -0.38), I: iris, L: shade(iris, 0.38),
      W: '#ffffff', S: '#f7f7fa', H: '#ff4f86'
    };
    var du = Math.round(clamp(pose.lookX || 0, -1, 1) * GLANCE[0] * 16) / 16;
    var dv = -Math.round(clamp(pose.lookY || 0, -1, 1) * GLANCE[1] * 16) / 16;
    var ey = EYE_Y + (species.eyeLift || 0);
    // viewer's left eye is the pet's right, at -X; both glance the same way
    var names = [EYES[pair[0]] ? pair[0] : 'open', EYES[pair[1]] ? pair[1] : 'open'];
    [[names[0], -EYE_X, false, du], [names[1], EYE_X, true, -du]].forEach(function (E) {
      var rows = EYES[E[0]];
      stamp(emit, head, laid(['eye', E[0], E[2], E[3], dv, ey].join(), function () {
        return layout(rows, eyeRects(rows, E[3], dv), E[1], ey, EYE_PX, E[2]);
      }), colours, neon, 'eye');
    });
    var brows = BROWS[pose.brows];
    if (brows) {
      var browColour = { B: led ? shade(iris, -0.1) : shade(col.hair, -0.42) };
      var by = ey + 2.5 * EYE_PX + 1.5 * EYE_PX;
      // the fringe is the hair style's, the same whatever she is doing
      var hair = fringe.map(function (f) { return [f.x, f.y, f.w, f.h, f.a, f.z].join(' '); });
      [[-EYE_X, false], [EYE_X, true]].forEach(function (E) {
        stamp(emit, head, laid(['brow', pose.brows, E[1], by, hair.join()].join(), function () {
          return layout(brows, browRects(brows, E[0], by, E[1], fringe), E[0], by, EYE_PX, E[1]);
        }), browColour, neon, 'brow');
      });
    }
    if (pose.tears > 0.05) {
      // a bead of water running down each cheek
      var drop = ((pose.time || 0) * 1.6) % 1;
      [-1, 1].forEach(function (side) {
        var tx = side * (EYE_X - 0.02), ty = ey - 0.17 - drop * 0.12;
        onFace(emit, head, tx - 0.025, tx + 0.025, ty - 0.04, ty + 0.04, '#9fdcff',
               { m: 'neon', k: 'face', lift: 0.03 });
      });
    }
    var mouth = MOUTHS[pose.mouth] ? pose.mouth : 'smile';
    stamp(emit, head, laid('mouth,' + mouth, function () {
      return layout(MOUTHS[mouth], bitmapRects(MOUTHS[mouth]), 0, MOUTH_Y, MOUTH_PX, false);
    }), {
      K: led ? shade(iris, -0.1) : '#4a2230', R: '#c33a57', P: '#ff7d9b', W: '#ffffff'
    }, neon, 'face');
    var blush = clamp(pose.blush || 0, 0, 1);
    if (blush > 0.12 && !led) {
      var cheek = mix(col.skin, '#ff5d86', 0.25 + 0.4 * blush);
      var bx = species.blushX || 0.36;
      [-1, 1].forEach(function (side) {
        // painted on: half as proud as the eyes
        onFace(emit, head, side * bx - 0.065, side * bx + 0.065, ey - 0.225, ey - 0.175, cheek,
               { k: 'face', lift: FACE_LIFT / 2 });
      });
    }
    if (species.nose) {
      // a little button of a nose, standing well out from her face
      var twitch = Math.sin((pose.time || 0) * 22) * 0.008 * (pose.sniff || 0);
      onFace(emit, head, -0.025, 0.025, -0.2725 + twitch, -0.2375 + twitch,
             species.nose === true ? '#ff8fb0' : species.nose, { k: 'face', lift: 0.035 });
    }
  }

  // --------------------------------------------------------- the species
  /* Defaults only: the server sends the colours a pet was given, and these
     fill anything it did not.  The palettes match app/models/pets.py. */
  var SPECIES = {
    fern: {
      id: 'fern', name: 'Fern',
      colors: { hair: '#3f9a3a', outfit: '#2c7a33', accent: '#8fd16a',
                eyes: '#43c25a', legs: '#1b1f1d', skin: '#ecc3a6' },
      gait: 'skip', back: -0.19,
      dress: { sleeve: 0.82, collar: 'accent', bow: true, hem: 'accent' },
      hair: 'bob', sig: 'sprout'
    },
    ember: {
      id: 'ember', name: 'Ember',
      colors: { hair: '#ff5a24', outfit: '#3a2a2e', accent: '#ffc23a',
                eyes: '#ffae2a', legs: '#24191c', skin: '#f2c7a2' },
      gait: 'run', back: -0.30,
      dress: { sleeve: 0.62, collar: 'accent', hoodie: true, pocket: true, hem: null,
               sneaker: true },
      hair: 'twintails', sig: 'flame', mouth: 'fang'
    },
    luna: {
      id: 'luna', name: 'Luna',
      colors: { hair: '#3b3f8f', outfit: '#252a5c', accent: '#c9b6ff',
                eyes: '#9d8cff', legs: '#e9e4ff', skin: '#f3d6c8' },
      gait: 'float', back: -0.60,
      dress: { sleeve: 1.0, bell: true, capelet: true, hem: 'accent', stripes: true,
               stars: true },
      hair: 'long', sig: 'moon', eyes: 'sleepy', blushX: 0.31
    },
    mochi: {
      id: 'mochi', name: 'Mochi',
      colors: { hair: '#ff9ec0', outfit: '#ffd3e2', accent: '#fff6ee',
                eyes: '#e2507e', legs: '#ffffff', skin: '#f6d2bd' },
      gait: 'hop', back: -0.24,
      dress: { sleeve: 1.0, collar: 'hair', puff: true, short: true, hem: 'hair',
               mary: true, tail: true },
      hair: 'hood', sig: 'ears', nose: true, mouth: 'cat'
    },
    pixel: {
      id: 'pixel', name: 'Pixel',
      colors: { hair: '#2bb3b1', outfit: '#2a3140', accent: '#4ff2ff',
                eyes: '#4ff2ff', legs: '#39414f', skin: '#efd0b8' },
      gait: 'walk', back: -0.19,
      dress: { sleeve: 0.34, seams: true, warmers: true, boots: true, hem: 'neon' },
      hair: 'techbob', sig: 'antenna', led: true
    }
  };
  var ORDER = ['fern', 'ember', 'luna', 'mochi', 'pixel'];

  /* Persona tags.  Each is a set of leanings the follower AI reads
     (static/js/game/pets.js), and a line for the tooltip.  The keys match
     app/models/pets.py. */
  var TAGS = {
    cheerful: { name: 'Cheerful', blurb: 'Bounces when you win and greets everyone she meets.' },
    shy:      { name: 'Shy', blurb: 'Hides behind you when strangers come close, and blushes a lot.' },
    curious:  { name: 'Curious', blurb: 'Wanders off to inspect things and peers at other players.' },
    loyal:    { name: 'Loyal', blurb: 'Sticks to your heel, copies your moves and waits for you.' },
    sleepy:   { name: 'Sleepy', blurb: 'Yawns, sits down and dozes off whenever you stand still.' },
    energetic:{ name: 'Energetic', blurb: 'Races ahead, hops about and never quite stops fidgeting.' },
    feisty:   { name: 'Feisty', blurb: 'Stomps when you get hurt and shadowboxes in a fight.' },
    dreamy:   { name: 'Dreamy', blurb: 'Gazes at the sky, hums little tunes and twirls.' },
    playful:  { name: 'Playful', blurb: 'Circles you, chases butterflies and pounces on your landings.' },
    brave:    { name: 'Brave', blurb: 'Steps in front of you when it gets dangerous, cheers your wins.' },
    clingy:   { name: 'Clingy', blurb: 'Never more than a step away. Pouts when she is left behind.' },
    showoff:  { name: 'Show-off', blurb: 'Strikes poses, waves at everyone and twirls for attention.' },
    chatty:   { name: 'Chatty', blurb: 'Always has something to say: little bubbles over her head.' },
    clumsy:   { name: 'Clumsy', blurb: 'Trips over her own feet now and then, and dusts herself off.' }
  };

  // ------------------------------------------------------------- poses
  var NUMERIC = ['bob', 'float', 'sit', 'lean', 'roll', 'twist', 'hipTwist', 'spin',
                 'squash', 'headYaw', 'headPitch', 'headRoll', 'armL', 'armR', 'armLZ',
                 'armRZ', 'legL', 'legR', 'legLZ', 'legRZ', 'skirt', 'swayX', 'swayZ',
                 'earL', 'earR', 'glow', 'jet', 'flame', 'perk', 'blink', 'lookX', 'lookY',
                 'blush', 'tears', 'sniff', 'lie'];

  function restPose() {
    return {
      bob: 0, float: 0, sit: 0, lie: 0, lean: 0, roll: 0, twist: 0, hipTwist: 0, spin: 0,
      squash: 1, headYaw: 0, headPitch: 0, headRoll: 0,
      armL: 0, armR: 0, armLZ: 0, armRZ: 0, legL: 0, legR: 0, legLZ: 0, legRZ: 0,
      skirt: 0, swayX: 0, swayZ: 0, earL: 0.6, earR: 0.6, glow: 0.5, jet: 0,
      flame: 0.5, perk: 0.6, blink: 0, lookX: 0, lookY: 0, blush: 0, tears: 0,
      sniff: 0, eyes: 'open', mouth: 'smile', brows: '', time: 0
    };
  }

  // --------------------------------------------------------- the builder
  function resolveColours(pet, species) {
    var given = (pet && pet.colors) || {};
    var out = {};
    Object.keys(species.colors).forEach(function (key) {
      var v = given[key];
      out[key] = (typeof v === 'string' && /^#[0-9a-fA-F]{6}$/.test(v)) ? v : species.colors[key];
    });
    return out;
  }

  Pet.species = function (pet) {
    var key = pet && (pet.species || String(pet.item_id || '').replace(/^pet_/, ''));
    return SPECIES[key] || SPECIES.fern;
  };

  function itemOf(pet, slot) {
    var items = (pet && pet.items) || {};
    var it = items[slot] || items['pet_' + slot];
    return it && it.data ? it : null;
  }

  /* Build every renderable part of one pet.
     opts: {position, yaw, pose, time, alpha} */
  function Pet() {}

  Pet.build = function (pet, opts) {
    opts = opts || {};
    var species = Pet.species(pet);
    var col = resolveColours(pet, species);
    var pose = opts.pose || restPose();
    var time = opts.time || 0;
    pose.time = time;
    var parts = [];
    var pos = opts.position || [0, 0, 0];
    var yaw = (opts.yaw || 0) + (pose.spin || 0);
    var squash = pose.squash || 1;
    var bulge = 1 + (1 - squash) * 0.5;    // she spreads as she squashes
    var alpha = opts.alpha;

    function emit(f, p, s, c, x) {
      x = x || {};
      // squash and stretch about the feet: close enough on a body this
      // small, and it never has to undo a turn.  A part's offset from its
      // bone squashes with the part itself, so whatever is laid on a surface
      // -- an eye on the face, a fringe on the forehead -- stays on it rather
      // than sinking into a head that bulges round it or floating off one
      // that narrows.
      var o = apply(f.m, squash === 1 ? p : [p[0] * bulge, p[1] * squash, p[2] * bulge]);
      var world = [f.t[0] + o[0], f.t[1] + o[1], f.t[2] + o[2]];
      if (squash !== 1) world[1] = pos[1] + (f.t[1] - pos[1]) * squash + o[1];
      var r;
      if (x.r && (x.r[0] || x.r[1] || x.r[2])) {
        r = matrixEuler(mul(f.m, eulerMatrix(x.r)));
      } else {
        r = f.e || (f.e = matrixEuler(f.m));
      }
      var size = [s[0], s[1], s[2]];
      if (squash !== 1) {
        size[1] *= squash;
        size[0] *= bulge; size[2] *= bulge;
      }
      var part = { t: x.t || 'rbox', p: world, s: size, c: c, r: [r[0], r[1], r[2]] };
      if (x.m) part.m = x.m;
      if (x.k) part.k = x.k;           // which bit of her it is, for framing
      if (x.dec) part.decSlot = global.Textures ? Textures.decal(x.dec) : null;
      if (x.dw) part.dw = x.dw;
      var a = x.a;
      if (alpha !== undefined && alpha < 0.999) a = (a === undefined ? 1 : a) * alpha;
      if (a !== undefined) part.a = a;
      parts.push(part);
      return part;
    }

    // ------------------------------------------------------------ bones
    var root = frame([pos[0], pos[1], pos[2]], eulerMatrix([0, yaw, 0]));
    var sit = clamp(pose.sit || 0, 0, 1);
    var lie = clamp(pose.lie || 0, 0, 1);
    // sitting drops the pelvis to the floor; floating lifts all of her
    var drop = sit * (B.pelvisY - 0.30);
    var lift = (pose.bob || 0) + (pose.float || 0) - drop;
    // lying down tips the whole body forward about the feet
    var hips = child(root, [0, B.pelvisY + lift - lie * 0.46, lie * 0.5],
                     [(pose.lean || 0) * 0.35 + lie * PI * 0.5, pose.hipTwist || 0,
                      (pose.roll || 0) * 0.4]);
    var torso = child(hips, [0, B.waistY - B.pelvisY, 0],
                      [(pose.lean || 0) * 0.65, pose.twist || 0, (pose.roll || 0) * 0.6]);
    var neck = child(torso, [0, B.neckY - B.waistY, 0],
                     [pose.headPitch || 0, pose.headYaw || 0, pose.headRoll || 0]);
    var head = child(neck, [0, B.headUp, 0], null);

    var dress = species.dress;
    var top = itemOf(pet, 'top');
    var topData = (top && top.data) || {};
    var outfit = topData.torso || col.outfit;
    var sleeveColour = topData.arms || outfit;
    var skirtColour = topData.skirt || col.outfit;
    var trim = topData.trim || (dress.hem === 'hair' ? col.hair : col.accent);
    var sleeve = topData.sleeve === undefined ? dress.sleeve : topData.sleeve;
    var weave = topData.weave || null;

    // ------------------------------------------------------------- legs
    var legColour = col.legs;
    var shoeColour = dress.mary ? shade(col.hair, -0.25)
      : (dress.sneaker ? '#f4f1ea' : (dress.boots ? shade(col.legs, -0.25)
                                                    : shade(col.legs, -0.35)));
    if (luma(shoeColour) > 0.85 && !dress.sneaker) shoeColour = shade(col.outfit, -0.3);
    [[-1, pose.legR || 0, pose.legRZ || 0], [1, pose.legL || 0, pose.legLZ || 0]]
      .forEach(function (L) {
        var side = L[0];
        // sitting swings the legs out in front, flat on the floor
        var swing = L[1] * (1 - sit) - sit * (PI / 2 - 0.08);
        var leg = child(hips, [side * B.legX, B.hipY - B.pelvisY, 0],
                        [swing, 0, side * (0.03 + L[2]) * (1 - sit * 0.5)]);
        var len = B.leg[1];
        if (dress.stripes) {
          // striped stockings: alternate bands of legwear and accent
          for (var k = 0; k < 5; k++) {
            var bandLen = len / 5;
            emit(leg, [0, -bandLen * (k + 0.5), 0],
                 [B.leg[0] + (k % 2 ? 0.004 : 0), bandLen + 0.01, B.leg[2] + (k % 2 ? 0.004 : 0)],
                 k % 2 ? col.accent : legColour, { t: 'box' });
          }
        } else if (dress.mary || dress.warmers === 'socks') {
          // bare knee, then a sock from the shin down
          emit(leg, [0, -len * 0.22, 0], [B.leg[0] - 0.01, len * 0.44, B.leg[2] - 0.01],
               col.skin, { t: 'rlimb' });
          emit(leg, [0, -len * 0.70, 0], [B.leg[0], len * 0.60, B.leg[2]], legColour,
               { t: 'rlimb' });
          emit(leg, [0, -len * 0.42, 0], [B.leg[0] + 0.04, 0.07, B.leg[2] + 0.04],
               shade(legColour, -0.06), { t: 'rbox' });
        } else {
          emit(leg, [0, -len / 2, 0], B.leg, legColour, { t: 'rlimb' });
        }
        if (dress.boots) {
          // thigh-high boots: the leg is the boot, with a cuff and a chunky sole
          emit(leg, [0, -0.06, 0], [B.leg[0] + 0.05, 0.10, B.leg[2] + 0.05],
               shade(legColour, 0.12), { t: 'rbox' });
          emit(leg, [0, -len - 0.05, 0.05], [B.shoe[0] + 0.03, B.shoe[1] + 0.06, B.shoe[2] + 0.04],
               shoeColour, { t: 'rbox' });
          emit(leg, [0, -len - 0.13, 0.05], [B.shoe[0] + 0.05, 0.04, B.shoe[2] + 0.06],
               col.accent, { t: 'box', m: 'neon' });
          if (pose.jet > 0.05) {
            var jl = 0.18 + 0.22 * pose.jet + Math.sin(time * 40 + side) * 0.04;
            emit(leg, [0, -len - 0.17 - jl / 2, 0.05], [0.16, jl, 0.16], col.accent,
                 { t: 'cone', r: [PI, 0, 0], m: 'neon', a: 0.85 });
          }
        } else {
          emit(leg, [0, -len - 0.06, 0.05], B.shoe, shoeColour, { t: 'rbox' });
          if (dress.sneaker) {
            emit(leg, [0, -len - 0.11, 0.05], [B.shoe[0] + 0.02, 0.05, B.shoe[2] + 0.02],
                 col.accent, { t: 'box' });
          }
          if (dress.mary) {
            emit(leg, [0, -len + 0.03, 0.11], [B.leg[0] + 0.03, 0.035, 0.2],
                 shoeColour, { t: 'box' });
          }
        }
      });

    // ------------------------------------------------------------ skirt
    var flare = clamp(pose.skirt || 0, 0, 1.4);
    var sk = B.skirt;
    var skLen = (sk.top - sk.bottom) * (dress.short ? 0.82 : 1);
    var skW = sk.w * (1 + 0.16 * flare) * (dress.puff ? 1.06 : 1) * (1 + sit * 0.12);
    var skD = sk.d * (1 + 0.16 * flare) * (dress.puff ? 1.08 : 1) * (1 + sit * 0.2);
    var skH = skLen * (1 - 0.12 * flare) * (1 - sit * 0.28);
    var skY = sk.top - B.pelvisY - skH / 2;
    emit(hips, [0, skY, 0], [skW, skH, skD], skirtColour,
         { t: 'petskirt', r: [PI, 0, 0], dec: weave, dw: weave ? 1 : 0 });
    if (dress.hem) {
      emit(hips, [0, skY - skH / 2 + 0.035, 0], [skW + 0.03, 0.07, skD + 0.03],
           dress.hem === 'neon' ? col.accent : trim,
           { t: 'rbox', m: dress.hem === 'neon' ? 'neon' : undefined });
    }
    if (dress.seams) {
      // pleats: glowing seams down the front of the skirt
      [-0.2, 0, 0.2].forEach(function (x) {
        emit(hips, [x * skW, skY - 0.02, skD * 0.47], [0.03, skH * 0.8, 0.03], col.accent,
             { t: 'box', m: 'neon' });
      });
    }
    if (dress.pocket) {
      emit(hips, [0, skY + 0.04, skD * 0.42], [skW * 0.5, skH * 0.38, 0.06],
           shade(skirtColour, -0.12), { t: 'rbox' });
    }
    if (dress.tail) {
      // a pompom tail on the back of the skirt
      var wag = Math.sin(time * 9) * 0.03 * (0.4 + (pose.perk || 0));
      emit(hips, [wag, skY + 0.02, -skD * 0.52], [0.26, 0.26, 0.24], col.accent,
           { t: 'sph' });
    }

    // ------------------------------------------------------------ torso
    emit(torso, [0, B.torsoY - B.waistY, 0], B.torso, outfit,
         { t: 'rbox', dec: weave, dw: weave ? 1 : 0, k: 'torso' });
    if (dress.puff) {
      emit(torso, [0, 0.05, 0], [B.torso[0] + 0.06, 0.12, B.torso[2] + 0.06],
           shade(outfit, -0.06), { t: 'rbox' });
    }
    var collarY = B.neckY - B.waistY - 0.02;
    if (dress.collar && !topData.nocollar) {
      var collarColour = topData.collar || (dress.collar === 'hair' ? col.hair : col.accent);
      emit(torso, [0, collarY, 0.0], [B.torso[0] * 0.78, 0.07, B.torso[2] + 0.04],
           collarColour, { t: 'rbox' });
    }
    if (dress.bow && !topData.nobow) {
      // where the reference had a logo: a little bow at the collar
      [-1, 1].forEach(function (side) {
        emit(torso, [side * 0.075, collarY - 0.05, B.torso[2] / 2 + 0.03],
             [0.13, 0.09, 0.05], topData.collar || col.accent,
             { t: 'rbox', r: [0, 0, side * 0.25] });
      });
      emit(torso, [0, collarY - 0.05, B.torso[2] / 2 + 0.045], [0.06, 0.07, 0.05],
           shade(topData.collar || col.accent, -0.2), { t: 'rbox' });
    }
    if (dress.hoodie) {
      // the hood, down, on her back -- and its drawstrings
      emit(torso, [0, collarY - 0.06, -B.torso[2] / 2 - 0.05], [0.44, 0.24, 0.16],
           shade(outfit, 0.06), { t: 'rbox' });
      [-1, 1].forEach(function (side) {
        emit(torso, [side * 0.07, collarY - 0.13, B.torso[2] / 2 + 0.02], [0.025, 0.16, 0.025],
             col.accent, { t: 'cyl' });
      });
      emit(torso, [0, 0.20, B.torso[2] / 2 + 0.005], [0.03, 0.34, 0.03], col.accent,
           { t: 'box' });
    }
    if (dress.seams) {
      [-1, 1].forEach(function (side) {
        emit(torso, [side * 0.16, B.torsoY - B.waistY, B.torso[2] / 2 + 0.005],
             [0.025, B.torso[1] * 0.86, 0.025], col.accent, { t: 'box', m: 'neon' });
      });
      emit(torso, [0, 0.03, 0], [B.torso[0] + 0.04, 0.07, B.torso[2] + 0.04],
           shade(outfit, -0.3), { t: 'rbox' });
      emit(torso, [0, 0.03, B.torso[2] / 2 + 0.03], [0.1, 0.06, 0.03], col.accent,
           { t: 'box', m: 'neon' });
    }
    if (dress.capelet) {
      emit(torso, [0, collarY - 0.12, -0.01], [B.torso[0] + 0.30, 0.24, B.torso[2] + 0.18],
           shade(outfit, -0.12), { t: 'rbox' });
      emit(torso, [0, collarY - 0.24, -0.01], [B.torso[0] + 0.32, 0.04, B.torso[2] + 0.20],
           col.accent, { t: 'rbox' });
    }
    if (dress.stars) {
      [[0, 0.30], [0, 0.17]].forEach(function (s) {
        emit(torso, [s[0], s[1], B.torso[2] / 2 + 0.02], [0.08, 0.08, 0.04], col.accent,
             { t: 'star', m: 'neon' });
      });
    }
    if (topData.buttons) {
      [0.32, 0.21, 0.10].forEach(function (y) {
        emit(torso, [0, y, B.torso[2] / 2 + 0.02], [0.05, 0.05, 0.03], topData.buttons,
             { t: 'cyl', r: [PI / 2, 0, 0] });
      });
    }
    if (topData.overall) {
      // a bib and its straps
      emit(torso, [0, 0.16, B.torso[2] / 2 + 0.01], [0.32, 0.26, 0.04], topData.overall,
           { t: 'rbox' });
      [-1, 1].forEach(function (side) {
        emit(torso, [side * 0.13, 0.33, 0], [0.06, 0.2, B.torso[2] + 0.03], topData.overall,
             { t: 'box' });
      });
    }

    // ------------------------------------------------------------- arms
    var hands = {};
    [[-1, pose.armR || 0, pose.armRZ || 0], [1, pose.armL || 0, pose.armLZ || 0]]
      .forEach(function (A) {
        var side = A[0];
        var arm = child(torso, [side * B.armX, B.shoulderY - B.waistY, 0],
                        [A[1], 0, side * (B.armRest + A[2])]);
        var len = B.arm[1];
        var cover = clamp(sleeve, 0, 1);
        if (cover > 0.02) {
          emit(arm, [0, -len * cover / 2 + 0.01, 0],
               [B.arm[0] + 0.01, len * cover, B.arm[2] + 0.01], sleeveColour,
               { t: 'rlimb', dec: weave, dw: weave ? 1 : 0 });
        }
        if (cover < 0.98) {
          emit(arm, [0, -len * (cover + (1 - cover) / 2), 0],
               [B.arm[0] - 0.015, len * (1 - cover), B.arm[2] - 0.015], col.skin,
               { t: 'rlimb' });
        }
        if (dress.bell) {
          emit(arm, [0, -len * 0.78, 0], [B.arm[0] + 0.1, 0.12, B.arm[2] + 0.1],
               col.accent, { t: 'rbox' });
        }
        if (dress.warmers) {
          emit(arm, [0, -len * 0.62, 0], [B.arm[0] + 0.03, len * 0.32, B.arm[2] + 0.03],
               col.legs, { t: 'rlimb' });
          emit(arm, [0, -len * 0.46, 0], [B.arm[0] + 0.05, 0.03, B.arm[2] + 0.05],
               col.accent, { t: 'box', m: 'neon' });
        }
        if (cover >= 0.98) {
          // a little hand out of the end of the sleeve
          emit(arm, [0, -len - 0.04, 0], [B.arm[0] - 0.03, 0.1, B.arm[2] - 0.03], col.skin,
               { t: 'rbox' });
        }
        hands[side] = child(arm, [0, -len - 0.04, 0], null);
      });

    // ------------------------------------------------------------- head
    emit(neck, [0, 0.03, 0], [0.24, 0.12, 0.22], col.skin, { t: 'cyl' });
    emit(head, [0, 0, 0], B.head, col.skin, { t: 'pethead', k: 'head' });

    // the hair goes on before the face, noting as it does what hangs in
    // front of the face, so the brows can be drawn over the fringe
    var fringe = [];
    function hairEmit(f, p, s, c, x) {
      var r = (x && x.r) || [0, 0, 0];
      var t = (x && x.t) || 'rbox';
      if (f === head && !r[0] && !r[1] && (t === 'rbox' || t === 'box') &&
          p[2] + s[2] / 2 > B.faceZ) {
        fringe.push({ x: p[0], y: p[1], w: s[0] / 2, h: s[1] / 2, a: r[2] || 0,
                      z: p[2] + s[2] / 2 });
      }
      return emit(f, p, s, c, x);
    }
    var hat = itemOf(pet, 'hat');
    var hatted = !!(hat && hat.data && hat.data.parts && hat.data.parts.length);
    var ctx = { emit: hairEmit, root: root, hips: hips, torso: torso, neck: neck, head: head,
                hands: hands, col: col, pose: pose, time: time, hat: hatted,
                species: species };
    HAIR[species.hair](ctx);
    if (SIG[species.sig]) SIG[species.sig](ctx);
    buildFace(emit, head, col, pose, species, fringe);

    // ------------------------------------------------------- cosmetics
    function wear(item, f, origin) {
      if (!item || !item.data || !item.data.parts) return;
      item.data.parts.forEach(function (piece) {
        var spin = piece.spin ? time * piece.spin : 0;
        var r = piece.r || [0, 0, 0];
        emit(f, [origin[0] + piece.p[0], origin[1] + piece.p[1], origin[2] + piece.p[2]],
             piece.s, piece.c,
             { t: piece.t || 'box', r: [r[0], r[1] + spin, r[2]], m: piece.m, a: piece.a,
               dec: piece.decal, dw: piece.dw, k: 'worn' });
      });
    }
    wear(itemOf(pet, 'hat'), head, [0, B.hairTop, 0]);
    wear(itemOf(pet, 'face'), head, [0, EYE_Y, B.faceZ]);
    wear(itemOf(pet, 'neck'), torso, [0, B.neckY - B.waistY - 0.02, 0]);
    wear(itemOf(pet, 'pin'), torso, [-0.14, 0.30, B.torso[2] / 2]);
    wear(itemOf(pet, 'back'), torso, [0, 0.22, species.back]);
    return parts;
  };

  // ------------------------------------------------------------- hair
  /* Every style is authored round the head's own centre (B.head is
     1.08 x 0.98 x 0.96), keeps its crown at B.hairTop so a hat sits the same
     on all of them, and hangs its moving locks from bones of their own so
     they lag and swing as she turns. */
  function sway(ctx, k) {
    var p = ctx.pose;
    return [(p.swayX || 0) * k, (p.swayZ || 0) * k];
  }

  /* The mass of the hair is one soft shell a size up from the head and set
     back from the face, so from the front it frames the face, from the side
     it is a rounded mass rather than a stack of slabs, and its crown is where
     a hat sits.  Each style then adds what makes it that style. */
  function shell(ctx, c, opts) {
    opts = opts || {};
    var low = opts.low === undefined ? -0.5 : opts.low;
    var h = 0.6 - low;
    // its front stands 0.04 behind the face: far enough apart to hold their
    // own depth at any range, close enough that the face reads as set in it
    var deep = 1.1 + (opts.deep || 0);
    ctx.emit(ctx.head, [0, 0.6 - h / 2, B.faceZ - 0.04 - deep / 2],
             [1.2 + (opts.wide || 0), h, deep], c,
             { t: 'pethead', dec: opts.dec, dw: opts.dec ? 1 : 0 });
    // the band across the top of the forehead that the fringe hangs from
    ctx.emit(ctx.head, [0, 0.47, 0.42], [1.12, 0.18, 0.16], c);
  }

  var HAIR = {
    /* Fern: the reference -- a heavy bob, a blunt fringe in four locks of
       different lengths, and two long locks framing the face that fall past
       the chin onto the shoulders. */
    bob: function (ctx) {
      var e = ctx.emit, h = ctx.head, c = ctx.col.hair;
      var dark = shade(c, -0.12);
      shell(ctx, c, { low: -0.56 });
      e(h, [0, -0.5, -0.5], [1.06, 0.16, 0.22], dark);
      [[-0.4, 0.28], [-0.14, 0.33], [0.14, 0.3], [0.4, 0.27]].forEach(function (b, i) {
        var len = [0.36, 0.25, 0.3, 0.38][i];
        e(h, [b[0], 0.48 - len / 2, 0.5], [0.27, len, 0.1], i % 2 ? c : dark);
      });
      var sw = sway(ctx, 1);
      [-1, 1].forEach(function (s) {
        var lock = child(h, [s * 0.58, 0.3, 0.3], [sw[0] * 0.8, 0, s * 0.03 + sw[1]]);
        e(lock, [0, -0.46, 0], [0.17, 0.94, 0.2], c);
        e(lock, [0, -0.89, 0], [0.13, 0.12, 0.17], dark);
      });
    },

    /* Ember: a short crown with a jagged fringe and two high twin tails, each
       in three bones so they whip as she runs.  Their tips are hers. */
    twintails: function (ctx) {
      var e = ctx.emit, h = ctx.head, c = ctx.col.hair, p = ctx.pose;
      var dark = shade(c, -0.15);
      shell(ctx, c, { low: -0.38 });
      // the middle lock is the longest, but stops short of her eyes
      [[-0.37, 0.27, -0.35, 0.38], [-0.02, 0.27, 0.1, 0.40], [0.35, 0.28, 0.38, 0.36]]
        .forEach(function (b, i) {
          e(h, [b[0], b[1], 0.5], [0.3, b[3], 0.1], i === 1 ? dark : c,
            { r: [0, 0, b[2]] });
        });
      [-1, 1].forEach(function (s) {
        e(h, [s * 0.5, 0.0, 0.42], [0.14, 0.5, 0.12], c, { r: [0, 0, -s * 0.1] });
      });
      var sw = sway(ctx, 1);
      var heat = clamp(p.flame === undefined ? 0.5 : p.flame, 0, 1.5);
      var flameColour = ctx.col.accent;
      [-1, 1].forEach(function (s) {
        e(h, [s * 0.6, 0.32, -0.14], [0.16, 0.16, 0.24], ctx.col.accent);
        var t1 = child(h, [s * 0.66, 0.32, -0.14],
                       [0.2 + sw[0], 0, s * (0.42 + sw[1] * 0.6)]);
        e(t1, [0, -0.2, 0], [0.27, 0.44, 0.27], c);
        var t2 = child(t1, [0, -0.38, 0], [sw[0] * 0.6, 0, s * (-0.2 + sw[1] * 0.4)]);
        e(t2, [0, -0.17, 0], [0.24, 0.38, 0.24], c);
        var t3 = child(t2, [0, -0.34, 0], [sw[0] * 0.5, 0, s * (-0.1 + sw[1] * 0.3)]);
        e(t3, [0, -0.1, 0], [0.2, 0.22, 0.2], mix(c, flameColour, 0.4));
        // the tip burns: it flickers, and burns brighter the more excited she is
        var flick = 1 + Math.sin(ctx.time * 23 + s * 2) * 0.1 + Math.sin(ctx.time * 37) * 0.06;
        var len = (0.3 + 0.2 * heat) * flick;
        e(t3, [0, -0.19 - len / 2, 0], [0.21, len, 0.21], mix(flameColour, c, 0.35),
          { t: 'teardrop', r: [PI, 0, 0], m: heat > 0.3 ? 'neon' : undefined });
        e(t3, [0, -0.2 - len * 0.38, 0], [0.12, len * 0.62, 0.12], shade(flameColour, 0.5),
          { t: 'teardrop', r: [PI, 0, 0], m: 'neon' });
      });
    },

    /* Luna: a hime cut -- a straight fringe and straight cheek locks -- and
       hair down to her knees that fades into her accent at the ends. */
    long: function (ctx) {
      var e = ctx.emit, h = ctx.head, c = ctx.col.hair;
      var tip = mix(c, ctx.col.accent, 0.6);
      shell(ctx, c, { low: -0.62, deep: 0.06 });
      e(h, [0, 0.31, 0.5], [1.1, 0.32, 0.1], c);
      e(h, [0, 0.165, 0.51], [1.0, 0.035, 0.1], shade(c, -0.18));
      [-1, 1].forEach(function (s) {
        e(h, [s * 0.5, -0.1, 0.44], [0.16, 0.82, 0.14], c);
      });
      var sw = sway(ctx, 1);
      // the fall of hair down her back, from the nape to the knee
      // it follows the line of her back rather than hanging off it like a cape
      var hang = child(h, [0, -0.3, -0.58], [sw[0] * 0.5 - 0.14, 0, sw[1] * 0.3]);
      e(hang, [0, -0.42, 0], [1.1, 0.92, 0.18], c);
      var end = child(hang, [0, -0.86, 0], [sw[0] * 0.4 + 0.1, 0, sw[1] * 0.2]);
      e(end, [0, -0.22, 0], [1.04, 0.48, 0.17], mix(c, tip, 0.45));
      e(end, [0, -0.5, 0], [0.9, 0.14, 0.15], tip);
    },

    /* Mochi: her hair is mostly a hood -- a soft shell round the head with a
       rim about the face -- and a pink fringe peeking out from under it. */
    hood: function (ctx) {
      var e = ctx.emit, h = ctx.head, hood = ctx.col.accent, c = ctx.col.hair;
      var rim = mix(hood, c, 0.3);
      e(h, [0, 0.04, -0.1], [1.26, 1.15, 1.08], hood, { t: 'pethead' });
      e(h, [0, 0.61, -0.12], [0.08, 0.05, 0.9], rim, { t: 'rbox' });
      [-1, 1].forEach(function (s) {
        e(h, [s * 0.6, -0.02, 0.47], [0.14, 0.96, 0.12], rim);
      });
      e(h, [0, 0.52, 0.47], [1.28, 0.15, 0.12], rim);
      [[-0.3, 0.27], [0.0, 0.21], [0.3, 0.27]].forEach(function (b, i) {
        e(h, [b[0], 0.44 - b[1] / 2, 0.5], [0.32, b[1], 0.09], i === 1 ? c : shade(c, -0.08));
      });
      // two pompom ties at the hood's chin
      [-1, 1].forEach(function (s) {
        e(h, [s * 0.38, -0.54, 0.4], [0.035, 0.18, 0.035], rim, { t: 'cyl' });
        e(h, [s * 0.38, -0.67, 0.4], [0.15, 0.15, 0.15], c, { t: 'sph' });
      });
    },

    /* Pixel: a sleek bob swept to one side, under a pair of headphones. */
    techbob: function (ctx) {
      var e = ctx.emit, h = ctx.head, c = ctx.col.hair;
      var dark = shade(c, -0.18);
      shell(ctx, c, { low: -0.46 });
      e(h, [-0.14, 0.3, 0.5], [0.76, 0.34, 0.1], c, { r: [0, 0, 0.16] });
      e(h, [0.34, 0.36, 0.5], [0.36, 0.22, 0.1], dark);
      var sw = sway(ctx, 1);
      [-1, 1].forEach(function (s) {
        var lock = child(h, [s * 0.56, -0.08, 0.28], [sw[0] * 0.5, 0, s * 0.12 + sw[1] * 0.5]);
        e(lock, [0, -0.26, 0], [0.15, 0.52, 0.24], c, { r: [0, 0, -s * 0.1] });
        e(lock, [s * 0.02, -0.56, 0.0], [0.13, 0.16, 0.2], dark, { t: 'cone', r: [PI, 0, 0] });
      });
      var phones = ctx.col.accent;
      if (!ctx.hat) {
        e(h, [0, 0.3, -0.02], [1.46, 0.66, 0.14], shade(ctx.col.outfit, 0.15), { t: 'arch' });
      }
      [-1, 1].forEach(function (s) {
        e(h, [s * 0.69, 0.0, -0.02], [0.36, 0.14, 0.36], shade(ctx.col.outfit, 0.1),
          { t: 'cyl', r: [0, 0, PI / 2] });
        e(h, [s * 0.765, 0.0, -0.02], [0.25, 0.03, 0.25], phones,
          { t: 'cyl', r: [0, 0, PI / 2], m: 'neon' });
      });
    }
  };

  // ---------------------------------------------------- signature features
  var SIG = {
    // a two-leafed sprout from the crown that perks up and wilts with her mood
    sprout: function (ctx) {
      if (ctx.hat) return;
      var e = ctx.emit, p = ctx.pose;
      var perk = clamp(p.perk === undefined ? 0.6 : p.perk, 0, 1.2);
      var wiggle = Math.sin(ctx.time * 3.1) * 0.06 + (p.swayZ || 0) * 0.4;
      var stem = child(ctx.head, [0.1, B.hairTop - 0.02, 0.05],
                       [(1 - perk) * 0.9 + (p.swayX || 0) * 0.5, 0, wiggle]);
      var green = mix(ctx.col.accent, '#3c8a2c', 0.25);
      e(stem, [0, 0.09, 0], [0.04, 0.18, 0.04], shade(green, -0.15), { t: 'cyl' });
      [-1, 1].forEach(function (s) {
        var droop = (1 - perk) * 0.9;
        e(stem, [s * 0.09, 0.2 - droop * 0.05, 0], [0.13, 0.22, 0.045], green,
          { t: 'leaf', r: [0, 0, -s * (1.0 + droop)] });
      });
    },

    // the flames are in the twin tails; this is the glow under her chin
    flame: function () {},

    // a glowing crescent pinned in her hair
    moon: function (ctx) {
      var e = ctx.emit;
      var glow = clamp(ctx.pose.glow === undefined ? 0.5 : ctx.pose.glow, 0, 1);
      var c = mix(shade(ctx.col.accent, -0.3), '#fff6c8', glow * 0.7);
      e(ctx.head, [0.6, 0.27, 0.16], [0.28, 0.36, 0.08], c,
        { t: 'crescent', r: [0, PI / 2, 0.35], m: glow > 0.25 ? 'neon' : 'metal' });
      e(ctx.head, [0.62, 0.05, 0.3], [0.1, 0.1, 0.05], c,
        { t: 'star', r: [0, PI / 2, 0], m: 'neon' });
    },

    // two long ears on the hood: perked, drooping, twitching, or splayed by a hat
    ears: function (ctx) {
      var e = ctx.emit, p = ctx.pose;
      var outer = ctx.col.accent, inner = mix(ctx.col.accent, '#ff8fb1', 0.55);
      [[-1, p.earR], [1, p.earL]].forEach(function (E) {
        var s = E[0];
        var perk = clamp(E[1] === undefined ? 0.6 : E[1], -0.5, 1.2);
        // 1 stands straight up, 0 lies back, below 0 flops over to the side
        var back = (1 - clamp(perk, 0, 1)) * 1.25;
        var flop = perk < 0 ? -perk * 1.6 : 0;
        var splay = ctx.hat ? 1.15 : 0.16;
        var twitch = Math.sin(ctx.time * 31 + s) * 0.05 * (p.sniff || 0);
        var ear = child(ctx.head, [s * 0.3, B.hairTop - 0.04, -0.06],
                        [-back + (p.swayX || 0) * 0.4, 0,
                         s * (splay + flop) + twitch + (p.swayZ || 0) * 0.5]);
        e(ear, [0, 0.44, 0], [0.38, 0.9, 0.13], outer, { t: 'bunnyear' });
        e(ear, [0, 0.41, 0.05], [0.22, 0.66, 0.06], inner, { t: 'bunnyear' });
      });
    },

    // an antenna on the headphones, its light the colour of her mood
    antenna: function (ctx) {
      var e = ctx.emit, p = ctx.pose;
      var wob = Math.sin(ctx.time * 6) * 0.08 + (p.swayZ || 0) * 0.6;
      var ant = child(ctx.head, [0.74, 0.12, 0], [(p.swayX || 0) * 0.4, 0, -0.35 + wob]);
      e(ant, [0, 0.2, 0], [0.035, 0.4, 0.035], '#c9d2dc', { t: 'cyl', m: 'metal' });
      var glow = clamp(p.glow === undefined ? 0.5 : p.glow, 0, 1);
      var blinkOn = (Math.sin(ctx.time * 5) > -0.6) || glow > 0.8;
      var light = p.led || ctx.col.accent;
      e(ant, [0, 0.43, 0], [0.11, 0.11, 0.11], blinkOn ? light : shade(light, -0.5),
        { t: 'sph', m: blinkOn ? 'neon' : undefined });
    }
  };

  // -------------------------------------------------------------- actions
  /* The animation library: each action poses a pet at ``t`` seconds into
     doing it.  ``k`` is a speed or an intensity where one applies.  The
     follower AI and the previews both build on these; a pose is plain
     numbers, so two actions blend by blending fields (Pet.blend). */
  var ACT = {};

  function breathe(p, t, rate) {
    rate = rate || 1;
    p.bob += Math.sin(t * 2.3 * rate) * 0.012;
    p.armLZ += Math.sin(t * 2.3 * rate) * 0.035;
    p.armRZ += Math.sin(t * 2.3 * rate) * 0.035;
  }

  ACT.idle = function (p, t) {
    breathe(p, t);
    p.headRoll += Math.sin(t * 0.7) * 0.05;
    p.hipTwist += Math.sin(t * 0.45) * 0.06;
    p.roll += Math.sin(t * 0.45) * 0.03;
    p.swayZ += Math.sin(t * 0.9) * 0.04;
  };

  ACT.walk = function (p, t, k) {
    k = k || 1;
    var ph = t * 7.5;
    p.legL = Math.sin(ph) * 0.55; p.legR = -p.legL;
    p.armL = -Math.sin(ph) * 0.45; p.armR = -p.armL;
    p.bob += Math.abs(Math.cos(ph)) * 0.04;
    p.lean += 0.08;
    p.skirt += 0.18 + Math.abs(Math.sin(ph)) * 0.08;
    p.swayX += 0.12 + Math.sin(ph * 2) * 0.05;
    p.swayZ += Math.sin(ph) * 0.08;
    p.hipTwist += Math.sin(ph) * 0.08;
  };

  ACT.run = function (p, t) {
    var ph = t * 11;
    p.legL = Math.sin(ph) * 0.95; p.legR = -p.legL;
    p.armL = -Math.sin(ph) * 0.9; p.armR = -p.armL;
    p.armLZ += 0.1; p.armRZ += 0.1;
    p.bob += Math.abs(Math.sin(ph)) * 0.09;
    p.lean += 0.26;
    p.skirt += 0.45;
    p.swayX += 0.42 + Math.sin(ph * 2) * 0.06;
    p.swayZ += Math.sin(ph) * 0.1;
    p.headPitch -= 0.06;
  };

  // Fern's happy gait: a skip on every step
  ACT.skip = function (p, t) {
    var ph = t * 7;
    var step = Math.sin(ph);
    p.legL = step * 0.7; p.legR = -step * 0.4;
    if (step < 0) { p.legR = -step * 0.7; p.legL = step * 0.4; }
    p.armL = -step * 0.7; p.armR = step * 0.7;
    p.armLZ += 0.25; p.armRZ += 0.25;
    p.bob += Math.abs(Math.sin(ph)) * 0.16;
    p.lean += 0.1;
    p.skirt += 0.35 + Math.abs(step) * 0.2;
    p.swayX += 0.18; p.swayZ += step * 0.14;
    p.headRoll += step * 0.08;
  };

  // Mochi's gait: both feet together, ears flopping on every landing
  ACT.hop = function (p, t) {
    var ph = (t * 2.2) % 1;
    var air = ph < 0.7 ? Math.sin(ph / 0.7 * PI) : 0;
    var crouch = ph >= 0.7 ? Math.sin((ph - 0.7) / 0.3 * PI) : 0;
    p.bob += air * 0.34;
    p.squash = 1 + air * 0.06 - crouch * 0.12;
    p.legL = p.legR = -air * 0.35 + crouch * 0.2;
    p.armL = p.armR = -0.3 - air * 0.6;
    p.armLZ += air * 0.5; p.armRZ += air * 0.5;
    p.lean += 0.12 - air * 0.1;
    p.skirt += air * 0.5;
    p.earL += -air * 0.5 + crouch * 0.3; p.earR = p.earL;
    p.swayX += 0.1 + crouch * 0.3;
  };

  // Luna's gait: she floats along, feet together and pointed
  ACT.float = function (p, t) {
    p.float += 0.2 + Math.sin(t * 2.2) * 0.05;
    p.legL = p.legR = 0.22;
    p.legLZ -= 0.02; p.legRZ -= 0.02;
    p.armL = p.armR = 0.3;
    p.armLZ += 0.25; p.armRZ += 0.25;
    p.lean += 0.14;
    p.skirt += 0.25 + Math.sin(t * 2.2) * 0.08;
    p.swayX += 0.32 + Math.sin(t * 1.7) * 0.06;
    p.swayZ += Math.sin(t * 1.3) * 0.08;
  };

  ACT.jump = function (p, t) {
    p.legL = -0.7; p.legR = -0.2;
    p.armLZ += 1.9; p.armRZ += 1.9;
    p.armL = p.armR = -0.4;
    p.skirt += 0.7;
    p.swayX -= 0.3;
    p.squash = 1.05;
    p.eyes = 'happy'; p.mouth = 'open';
  };

  ACT.land = function (p, t) {
    var k = 1 - smooth01(t / 0.3);
    p.squash = 1 - 0.14 * k;
    p.armLZ += 0.7 * k; p.armRZ += 0.7 * k;
    p.skirt += 0.6 * k;
    p.swayX += 0.4 * k;
  };

  ACT.wave = function (p, t) {
    breathe(p, t);
    p.armRZ = 2.35 + Math.sin(t * 12) * 0.32;
    p.armR = -0.25;
    p.headRoll += 0.16;
    p.hipTwist += 0.1;
    p.eyes = 'happy'; p.mouth = 'grin';
  };

  ACT.cheer = function (p, t) {
    var b = Math.abs(Math.sin(t * 6.5));
    p.bob += b * 0.26;
    p.armLZ = 2.7 + b * 0.2; p.armRZ = 2.7 + b * 0.2;
    p.legL = p.legR = -b * 0.25;
    p.skirt += b * 0.6;
    p.swayX -= b * 0.25;
    p.eyes = 'joy'; p.mouth = 'grin';
    p.blush += 0.3;
  };

  ACT.clap = function (p, t) {
    breathe(p, t);
    var c = Math.abs(Math.sin(t * 13));
    p.armL = p.armR = -1.15;
    p.armLZ = p.armRZ = -0.32 + c * 0.3;
    p.bob += c * 0.02;
    p.eyes = 'joy'; p.mouth = 'grin';
  };

  ACT.twirl = function (p, t, k) {
    var d = k || 1.3;
    var u = smooth01(t / d);
    p.spin = u * PI * 2;
    p.armLZ += 1.15; p.armRZ += 1.15;
    p.skirt += 1.1 * Math.sin(u * PI) + 0.2;
    p.bob += Math.sin(u * PI) * 0.08;
    p.swayZ += Math.sin(u * PI) * 0.5;
    p.eyes = 'joy'; p.mouth = 'open';
  };

  ACT.pose = function (p, t) {
    breathe(p, t);
    var u = smooth01(t / 0.35);
    p.hipTwist += 0.24 * u; p.roll += 0.1 * u;
    p.armLZ += 0.6 * u; p.armL = -0.15 * u;
    p.armR = -2.45 * u; p.armRZ += 0.35 * u;
    p.headRoll += 0.26 * u;
    p.legRZ += 0.08 * u;
    p.eyes = 'wink'; p.mouth = 'tongue';
    p.blush += 0.4;
  };

  ACT.curtsy = function (p, t) {
    var u = Math.sin(clamp(t / 1.4, 0, 1) * PI);
    p.lean += 0.35 * u;
    p.legR = 0.35 * u; p.legL = -0.05 * u;
    p.squash = 1 - 0.06 * u;
    p.armLZ += 0.5; p.armRZ += 0.5;
    p.armL = p.armR = -0.2;
    p.skirt += 0.5 * u;
    p.headPitch += 0.2 * u;
    p.eyes = 'joy'; p.mouth = 'smile';
  };

  ACT.sit = function (p, t) {
    p.sit = 1;
    breathe(p, t, 0.8);
    p.armL = p.armR = -0.55; p.armLZ += 0.12; p.armRZ += 0.12;
    p.lean -= 0.06;
    p.headYaw += Math.sin(t * 0.5) * 0.35;
    p.headRoll += Math.sin(t * 0.8) * 0.08;
    p.legL += Math.sin(t * 1.6) * 0.05; p.legR -= Math.sin(t * 1.6) * 0.05;
  };

  ACT.sleep = function (p, t) {
    p.sit = 1;
    breathe(p, t, 0.55);
    p.armL = p.armR = -0.4;
    p.headPitch += 0.32 + Math.sin(t * 0.9) * 0.05;
    p.headRoll += 0.26;
    p.eyes = 'closed'; p.mouth = 'tiny';
    p.perk = 0.1; p.earL = p.earR = 0.05; p.glow = 0.9; p.flame = 0.15;
    p.blush += 0.25;
  };

  ACT.yawn = function (p, t) {
    var u = Math.sin(clamp(t / 2.2, 0, 1) * PI);
    p.armLZ += 2.6 * u; p.armRZ += 2.6 * u;
    p.armL = p.armR = -0.3 * u;
    p.lean -= 0.12 * u;
    p.squash = 1 + 0.05 * u;
    p.headPitch -= 0.25 * u;
    p.eyes = 'closed'; p.mouth = u > 0.25 ? 'yawn' : 'o';
  };

  ACT.stretch = function (p, t) {
    var u = smooth01(t / 0.6);
    p.armLZ += 2.8 * u; p.armRZ += 2.8 * u;
    p.roll += Math.sin(t * 1.6) * 0.22 * u;
    p.squash = 1 + 0.04 * u;
    p.eyes = 'joy'; p.mouth = 'cat';
  };

  ACT.look = function (p, t) {
    breathe(p, t);
    var y = Math.sin(t * 1.3) * 0.85;
    p.headYaw += y;
    p.lookX = clamp(-y * 1.2, -1, 1);
    p.headPitch -= 0.05;
  };

  ACT.peek = function (p, t) {
    var u = smooth01(t / 0.4);
    p.roll += 0.32 * u; p.lean += 0.1 * u;
    p.headRoll += 0.32 * u;
    p.legLZ += 0.2 * u;
    p.armRZ += 0.3 * u;
    p.eyes = t % 2.4 < 1.2 ? 'open' : 'wide';
  };

  ACT.hide = function (p, t) {
    p.sit = 0.3;
    p.squash = 0.86 + Math.sin(t * 24) * 0.008;
    p.armL = p.armR = -2.3; p.armLZ = p.armRZ = -0.45;
    p.headPitch += 0.3;
    p.eyes = 'closed'; p.mouth = 'wavy';
    p.blush += 0.6; p.earL = p.earR = 0.1; p.perk = 0.2;
  };

  ACT.cover_ears = function (p, t) {
    p.armLZ = p.armRZ = 2.55; p.armL = p.armR = -0.35;
    p.squash = 0.94;
    p.headPitch += 0.15;
    p.eyes = 'squint'; p.mouth = 'wavy';
    p.earL = p.earR = 0.05;
  };

  ACT.cry = function (p, t) {
    p.armL = p.armR = -2.35; p.armLZ = p.armRZ = -0.32;
    p.bob += Math.sin(t * 20) * 0.012;
    p.headPitch += 0.22;
    p.eyes = 'closed'; p.mouth = 'frown'; p.brows = 'sad';
    p.tears = 1; p.perk = 0; p.earL = p.earR = -0.2; p.flame = 0.1; p.glow = 0.15;
  };

  ACT.stomp = function (p, t) {
    var ph = t * 7;
    var lift = Math.max(0, Math.sin(ph));
    var other = Math.max(0, -Math.sin(ph));
    p.legL = -lift * 0.55; p.legR = -other * 0.55;
    p.bob += (lift + other) * 0.05;
    p.armLZ += 0.32; p.armRZ += 0.32;
    p.armL = p.armR = 0.22;
    p.headPitch += 0.12;
    p.eyes = 'open'; p.brows = 'angry'; p.mouth = 'frown';
    p.flame = 1.4; p.glow = 0.9;
  };

  ACT.shadowbox = function (p, t) {
    var ph = t * 9;
    var a = Math.max(0, Math.sin(ph)), b = Math.max(0, -Math.sin(ph));
    p.armR = -1.5 * a - 0.5; p.armL = -1.5 * b - 0.5;
    p.armRZ = -0.25; p.armLZ = -0.25;
    p.twist += (a - b) * 0.25;
    p.lean += 0.14;
    p.legLZ += 0.14; p.legRZ += 0.14;
    p.bob += Math.abs(Math.sin(ph * 2)) * 0.03;
    p.eyes = 'open'; p.brows = 'angry'; p.mouth = 'fang';
    p.flame = 1.2;
  };

  ACT.pant = function (p, t) {
    p.lean += 0.5;
    p.armL = p.armR = -0.75; p.armLZ = p.armRZ = 0.1;
    p.bob += Math.sin(t * 11) * 0.02;
    p.headPitch -= 0.25;
    p.eyes = 'half'; p.mouth = 'open';
    p.blush += 0.5;
  };

  ACT.trip = function (p, t) {
    if (t < 0.35) {
      var u = t / 0.35;
      p.lean += 1.0 * u;
      p.armLZ += 2.2 * u; p.armRZ += 2.0 * u;
      p.legR = 0.6 * u;
      p.eyes = 'wide'; p.mouth = 'o';
    } else if (t < 1.1) {
      p.lie = 1;
      p.headPitch -= 0.5;
      p.armL = p.armR = -2.9; p.armLZ = p.armRZ = 0.4;
      p.legL = 0.3; p.legR = 0.1;
      p.eyes = 'dizzy'; p.mouth = 'wavy';
    } else if (t < 1.8) {
      var v = (t - 1.1) / 0.7;
      p.lie = 1 - smooth01(v);
      p.sit = 0.4 * Math.sin(v * PI);
      p.eyes = 'closed'; p.mouth = 'frown';
    } else {
      ACT.dust_off(p, t - 1.8);
    }
  };

  ACT.dust_off = function (p, t) {
    var pat = Math.sin(t * 16);
    p.armL = -0.35 + pat * 0.2; p.armR = -0.35 - pat * 0.2;
    p.armLZ = p.armRZ = -0.1;
    p.headPitch += 0.3; p.lean += 0.12;
    p.eyes = 'half'; p.mouth = 'pout';
  };

  ACT.hum = function (p, t) {
    breathe(p, t);
    p.roll += Math.sin(t * 2.5) * 0.12;
    p.headRoll += Math.sin(t * 2.5) * 0.22;
    p.hipTwist += Math.sin(t * 1.25) * 0.12;
    p.armLZ += 0.2; p.armRZ += 0.2;
    p.eyes = 'joy'; p.mouth = 'o';
    p.glow = 0.9;
  };

  ACT.dance = function (p, t) {
    var ph = t * 6;
    p.hipTwist += Math.sin(ph) * 0.32;
    p.roll += Math.sin(ph) * 0.15;
    p.bob += Math.abs(Math.sin(ph)) * 0.07;
    p.armL = -1.0 + Math.sin(ph) * 0.55; p.armR = -1.0 - Math.sin(ph) * 0.55;
    p.armLZ += 0.35; p.armRZ += 0.35;
    p.legL = Math.max(0, Math.sin(ph)) * -0.4; p.legR = Math.max(0, -Math.sin(ph)) * -0.4;
    p.skirt += 0.4 + Math.abs(Math.sin(ph)) * 0.3;
    p.headRoll += Math.sin(ph) * 0.18;
    p.eyes = 'joy'; p.mouth = 'grin';
  };

  ACT.inspect = function (p, t) {
    var u = smooth01(t / 0.5);
    p.lean += 0.45 * u;
    p.armL = p.armR = 0.62 * u; p.armLZ = p.armRZ = -0.25 * u;
    p.headPitch += 0.38 * u;
    p.headRoll += Math.sin(t * 1.5) * 0.3 * u;
    p.lookX = Math.sin(t * 2.1) * 0.8;
    p.eyes = (t % 3) < 2 ? 'open' : 'wide';
    p.mouth = (t % 3) < 2 ? 'o' : 'smile';
    p.sniff = 1;
  };

  ACT.pounce = function (p, t) {
    if (t < 0.45) {
      var u = t / 0.45;
      p.squash = 1 - 0.18 * u;
      p.lean += 0.35 * u;
      p.armL = p.armR = -0.6 * u;
      p.eyes = 'open'; p.brows = 'angry';
    } else if (t < 0.95) {
      var v = (t - 0.45) / 0.5;
      p.bob += Math.sin(v * PI) * 0.6;
      p.armL = p.armR = -2.3;
      p.legL = p.legR = 0.4;
      p.lean += 0.35;
      p.skirt += 0.8;
      p.eyes = 'joy'; p.mouth = 'grin';
    } else {
      ACT.land(p, t - 0.95);
      p.eyes = 'joy'; p.mouth = 'cat';
    }
  };

  ACT.hug = function (p, t) {
    var u = smooth01(t / 0.5);
    p.armL = p.armR = -1.35 * u;
    p.armLZ = p.armRZ = 0.4 - 0.65 * u;
    p.lean += 0.15 * u;
    p.headRoll += 0.18 * u;
    p.eyes = 'joy'; p.mouth = 'cat';
    p.blush += 0.8;
  };

  ACT.shy = function (p, t) {
    p.armL = p.armR = -0.38; p.armLZ = p.armRZ = -0.32;
    p.hipTwist += Math.sin(t * 2) * 0.2;
    p.twist += Math.sin(t * 2) * 0.1;
    p.headPitch += 0.2;
    p.headYaw += 0.4 * Math.sin(t * 0.7);
    p.lookX = -Math.sin(t * 0.7);
    p.legLZ -= 0.04; p.legRZ -= 0.04;
    p.legL = Math.sin(t * 2) * 0.1;
    p.eyes = 'happy'; p.mouth = 'wavy';
    p.blush = 1;
  };

  ACT.sneeze = function (p, t) {
    if (t < 0.8) {
      var u = t / 0.8;
      p.headPitch -= 0.38 * u; p.lean -= 0.1 * u;
      p.eyes = 'half'; p.mouth = 'o';
      p.sniff = 1;
    } else if (t < 1.05) {
      p.headPitch += 0.45; p.lean += 0.28;
      p.squash = 0.92;
      p.eyes = 'closed'; p.mouth = 'open';
      p.flame = 1.5; p.earL = p.earR = 1.1;
    } else {
      p.eyes = 'half'; p.mouth = 'pout';
      p.headRoll += 0.1;
    }
  };

  ACT.think = function (p, t) {
    breathe(p, t);
    p.armR = -2.05; p.armRZ = -0.42;
    p.armL = -0.5; p.armLZ = -0.38;
    p.headRoll += 0.2; p.headPitch -= 0.12;
    p.lookY = 0.9; p.lookX = 0.5;
    p.eyes = 'open'; p.mouth = 'flat';
  };

  ACT.heart = function (p, t) {
    var u = smooth01(t / 0.4);
    p.armL = p.armR = -1.25 * u; p.armLZ = p.armRZ = -0.48 * u;
    p.bob += Math.abs(Math.sin(t * 4)) * 0.05;
    p.headRoll += 0.15;
    p.eyes = 'love'; p.mouth = 'cat';
    p.blush += 0.7;
  };

  ACT.salute = function (p, t) {
    var u = smooth01(t / 0.3);
    p.armR = -2.55 * u; p.armRZ = -0.55 * u;
    p.headPitch -= 0.05;
    p.eyes = 'open'; p.brows = 'up'; p.mouth = 'smile';
    p.glow = 1;
  };

  ACT.scan = function (p, t) {
    breathe(p, t);
    p.headYaw += Math.sin(t * 1.1) * 0.85;
    p.headPitch += 0.1 + Math.sin(t * 2.2) * 0.08;
    p.eyes = 'half'; p.mouth = 'flat';
    p.glow = 1;
  };

  ACT.nod = function (p, t) {
    breathe(p, t);
    p.headPitch += Math.max(0, Math.sin(t * 9)) * 0.28;
    p.eyes = 'happy'; p.mouth = 'smile';
  };

  ACT.shake = function (p, t) {
    breathe(p, t);
    p.headYaw += Math.sin(t * 11) * 0.38;
    p.eyes = 'half'; p.mouth = 'pout'; p.brows = 'worry';
  };

  ACT.giggle = function (p, t) {
    p.armR = -2.25; p.armRZ = -0.5;
    p.armL = -0.4; p.armLZ = -0.2;
    p.bob += Math.abs(Math.sin(t * 16)) * 0.03;
    p.headRoll += 0.18;
    p.eyes = 'joy'; p.mouth = 'cat';
    p.blush += 0.5;
  };

  ACT.kick = function (p, t) {
    var u = clamp((t - 0.25) / 0.2, 0, 1);
    var back = clamp(t / 0.25, 0, 1);
    p.legR = u > 0 ? -0.9 * Math.sin(u * PI) : 0.4 * back;
    p.armL = -0.4; p.armLZ += 0.4; p.armRZ += 0.3;
    p.headPitch += 0.35;
    p.eyes = 'open'; p.mouth = 'o';
  };

  ACT.sneak = function (p, t) {
    var ph = t * 4;
    p.legL = Math.sin(ph) * 0.3; p.legR = -p.legL;
    p.lean += 0.12;
    p.armL = p.armR = -0.6; p.armLZ = p.armRZ = 0.55;
    p.bob += 0.04 + Math.abs(Math.cos(ph)) * 0.02;
    p.eyes = 'half'; p.mouth = 'cat';
  };

  ACT.sad_walk = function (p, t) {
    ACT.walk(p, t * 0.6);
    p.headPitch += 0.35;
    p.armL *= 0.3; p.armR *= 0.3;
    p.eyes = 'sad'; p.mouth = 'frown'; p.brows = 'sad';
    p.perk = 0.1; p.earL = p.earR = -0.3; p.flame = 0.15; p.glow = 0.15;
  };

  ACT.fistpump = function (p, t) {
    var b = Math.max(0, Math.sin(t * 8));
    p.armR = -2.9 + b * 0.25; p.armRZ = 0.1;
    p.armL = -0.6; p.armLZ = -0.2;
    p.bob += b * 0.12;
    p.eyes = 'joy'; p.mouth = 'fang';
    p.flame = 1.4;
  };

  ACT.float_spin = function (p, t) {
    ACT.float(p, t);
    p.spin = (t * 1.6) % (PI * 2);
    p.armLZ += 0.9; p.armRZ += 0.9;
    p.skirt += 0.5;
    p.eyes = 'joy'; p.mouth = 'o';
    p.glow = 1;
  };

  ACT.ear_twitch = function (p, t) {
    breathe(p, t);
    p.earL += Math.sin(t * 18) * 0.25;
    p.earR -= Math.max(0, Math.sin(t * 9)) * 0.6;
    p.sniff = 1;
    p.headRoll += 0.1;
    p.eyes = 'open'; p.mouth = 'cat';
  };

  ACT.flex = function (p, t) {
    var u = smooth01(t / 0.3);
    p.armR = -1.4 * u; p.armRZ = 0.9 * u;
    p.armL = -0.3; p.armLZ = 0.2;
    p.headRoll -= 0.15;
    p.eyes = 'happy'; p.brows = 'angry'; p.mouth = 'fang';
    p.flame = 1.3;
  };

  ACT.sparkle = function (p, t) {
    breathe(p, t);
    p.armL = p.armR = -1.0; p.armLZ = p.armRZ = -0.2;
    p.eyes = 'spark'; p.mouth = 'open';
    p.bob += Math.abs(Math.sin(t * 5)) * 0.06;
    p.glow = 1; p.perk = 1.1; p.earL = p.earR = 1.1;
  };

  ACT.pout = function (p, t) {
    breathe(p, t);
    p.armL = p.armR = -0.2; p.armLZ = p.armRZ = -0.45;
    p.headYaw += 0.5; p.headPitch -= 0.08;
    p.eyes = 'half'; p.mouth = 'pout'; p.brows = 'angry';
    p.blush += 0.5;
  };

  /* Pose a pet doing ``name`` for ``t`` seconds. */
  Pet.act = function (name, t, k, into) {
    var p = into || restPose();
    var fn = ACT[name] || ACT.idle;
    fn(p, t || 0, k);
    return p;
  };
  Pet.actions = function () { return Object.keys(ACT); };

  /* How long the one-shot actions take; the rest loop until replaced. */
  Pet.DURATION = {
    wave: 1.6, cheer: 1.8, clap: 1.6, twirl: 1.3, pose: 2.0, curtsy: 1.4, yawn: 2.2,
    stretch: 2.0, look: 2.6, peek: 2.4, trip: 2.6, dust_off: 1.0, kick: 0.9,
    pounce: 1.3, hug: 1.6, sneeze: 1.6, think: 2.4, heart: 1.8, salute: 1.4, scan: 2.8,
    nod: 1.0, shake: 1.0, giggle: 1.4, fistpump: 1.6, float_spin: 2.4, ear_twitch: 1.4,
    flex: 1.6, sparkle: 1.8, pout: 2.4, land: 0.3, cover_ears: 2.0, dance: 3.2, hum: 3.0,
    inspect: 3.2, shy: 2.6, stomp: 1.6, shadowbox: 1.8, cry: 2.6, pant: 2.0, sit: 0,
    sleep: 0, hide: 0
  };

  /* Ease one pose toward another, field by field; the discrete fields (which
     eyes, which mouth) switch as soon as the target changes. */
  Pet.blend = function (from, to, k) {
    var out = from || restPose();
    for (var i = 0; i < NUMERIC.length; i++) {
      var key = NUMERIC[i];
      var a = out[key], b = to[key];
      if (a === undefined) a = 0;
      if (b === undefined) b = 0;
      out[key] = a + (b - a) * k;
    }
    // a turn the long way round would spin her backwards through the blend
    out.eyes = to.eyes; out.mouth = to.mouth; out.brows = to.brows; out.led = to.led;
    return out;
  };

  /* The gait a species walks in, at ``speed`` (world units a second). */
  Pet.gait = function (species, speed, happy) {
    if (speed < 0.4) return 'idle';
    var g = species.gait;
    if (g === 'float') return 'float';
    if (g === 'hop') return speed > 9 ? 'run' : 'hop';
    if (speed > 8.5) return 'run';
    if (g === 'skip' && happy) return 'skip';
    if (g === 'run' && speed > 5) return 'run';
    return 'walk';
  };

  // ------------------------------------------------------------ showcase
  /* A pet that entertains herself, for the market, the editor and the
     profile: idles, glances about, blinks, and every few seconds does
     something from her repertoire -- chosen by her persona tags, so a Sleepy
     pet in a preview yawns and a Show-off strikes a pose. */
  var TAG_ACTS = {
    cheerful: ['wave', 'cheer', 'clap', 'nod'],
    shy: ['shy', 'peek', 'giggle'],
    curious: ['look', 'inspect', 'think'],
    loyal: ['salute', 'nod', 'heart'],
    sleepy: ['yawn', 'stretch'],
    energetic: ['cheer', 'fistpump', 'dance'],
    feisty: ['shadowbox', 'flex', 'stomp'],
    dreamy: ['hum', 'twirl', 'float_spin'],
    playful: ['pounce', 'dance', 'giggle'],
    brave: ['flex', 'salute', 'fistpump'],
    clingy: ['hug', 'heart', 'pout'],
    showoff: ['pose', 'twirl', 'curtsy'],
    chatty: ['giggle', 'nod', 'wave'],
    clumsy: ['trip', 'dust_off', 'sneeze']
  };
  var SPECIES_ACTS = {
    fern: ['curtsy', 'hum', 'sparkle'],
    ember: ['fistpump', 'flex', 'sneeze'],
    luna: ['float_spin', 'yawn', 'hum'],
    mochi: ['ear_twitch', 'pounce', 'heart'],
    pixel: ['scan', 'salute', 'dance']
  };

  function Showcase(pet, opts) {
    opts = opts || {};
    this.pet = pet;
    this.pose = restPose();
    this.t = 0;
    this.action = 'idle';
    this.actT = 0;
    this.next = 1.2 + Math.random() * 1.5;
    this.blinkAt = 1 + Math.random() * 2;
    this.blinkT = -1;
    this.lookT = 0;
    this.look = [0, 0];
    this.only = opts.only || null;
    this.calm = !!opts.calm;
  }

  Showcase.prototype.repertoire = function () {
    var species = Pet.species(this.pet);
    var pool = SPECIES_ACTS[species.id].slice();
    ((this.pet && this.pet.tags) || []).forEach(function (tag) {
      (TAG_ACTS[tag] || []).forEach(function (a) { pool.push(a, a); });
    });
    if (!pool.length) pool = ['wave', 'twirl', 'nod'];
    return pool;
  };

  Showcase.prototype.play = function (action) {
    this.action = action;
    this.actT = 0;
    this.next = (Pet.DURATION[action] || 2) + 2.2 + Math.random() * 2.5;
  };

  Showcase.prototype.step = function (dt) {
    this.t += dt;
    this.actT += dt;
    var species = Pet.species(this.pet);
    if (this.only) {
      if (this.action !== this.only) this.play(this.only);
    } else if (this.actT >= this.next && !this.calm) {
      if (this.action === 'idle') {
        var pool = this.repertoire();
        this.play(pool[(Math.random() * pool.length) | 0]);
      } else {
        this.action = 'idle';
        this.actT = 0;
        this.next = 2.5 + Math.random() * 3;
      }
    } else if (this.action !== 'idle' && this.actT > (Pet.DURATION[this.action] || 99) &&
               !this.only) {
      this.action = 'idle';
      this.actT = 0;
      this.next = 2.2 + Math.random() * 3;
    }
    var target = restPose();
    if (species.gait === 'float') ACT.float(target, this.t * 0.5);
    target.lean = 0; target.legL = target.legR = target.legL * 0.5;
    var name = this.action;
    var dur = Pet.DURATION[name];
    var t = (dur && !this.only) ? Math.min(this.actT, dur) : this.actT;
    if (this.only && dur) t = this.actT % (dur + 0.8);
    Pet.act(name, t, null, target);
    if (species.eyes && target.eyes === 'open') target.eyes = species.eyes;
    if (species.mouth && target.mouth === 'smile') target.mouth = species.mouth;
    // glances
    this.lookT -= dt;
    if (this.lookT <= 0) {
      this.lookT = 1.2 + Math.random() * 2.4;
      this.look = Math.random() < 0.4 ? [0, 0]
        : [(Math.random() - 0.5) * 1.6, (Math.random() - 0.4) * 0.8];
    }
    target.lookX += this.look[0];
    target.lookY += this.look[1];
    if (name === 'idle') target.headYaw += this.look[0] * 0.25;
    // blinks, now and then a double
    this.blinkAt -= dt;
    if (this.blinkAt <= 0) {
      this.blinkT = 0;
      this.blinkAt = Math.random() < 0.2 ? 0.28 : 2 + Math.random() * 3.5;
    }
    if (this.blinkT >= 0) {
      this.blinkT += dt;
      target.blink = this.blinkT < 0.13 ? 1 : 0;
      if (this.blinkT > 0.13) this.blinkT = -1;
    }
    this.pose = Pet.blend(this.pose, target, Math.min(1, dt * 12));
    this.pose.spin = target.spin;
    return this.pose;
  };

  Pet.Showcase = Showcase;
  Pet.restPose = restPose;
  Pet.SPECIES = SPECIES;
  Pet.ORDER = ORDER;
  Pet.TAGS = TAGS;
  Pet.B = B;
  Pet.EYES = EYES;
  Pet.MOUTHS = MOUTHS;
  Pet.BROWS = BROWS;
  /* The face's layout, for the checks in tools/pettests.js. */
  Pet.HEAD_ROUND = HEAD_ROUND;
  Pet.FACE = { eyeX: EYE_X, eyeY: EYE_Y, eyePx: EYE_PX, lift: FACE_LIFT, glance: GLANCE };
  Pet.mix = mix;
  Pet.shade = shade;
  /* Where a pet's crown is in the world, for emotes over her head. */
  Pet.headTop = function (position, pose) {
    pose = pose || {};
    var lift = (pose.bob || 0) + (pose.float || 0) - (pose.sit || 0) * (B.pelvisY - 0.30);
    return [position[0], position[1] + B.height + lift + 0.1, position[2]];
  };
  Pet.HEIGHT = B.height;

  global.Pet = Pet;
})(window);
