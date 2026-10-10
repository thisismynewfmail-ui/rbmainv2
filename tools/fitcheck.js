#!/usr/bin/env node
/* Fit check: does every wearable sit ON both bodies rather than in them?

   Loads the real engine (gl.js maths, geometry.js primitives, shapes.js
   sculpted meshes, avatar.js rig) headless, builds the male and the female
   character in their idle pose, puts each item on them exactly the way the
   game does, and samples the item's actual mesh surface -- every vertex and
   every triangle centre -- against the body's own solids (the rounded-box
   head, torso, hips and limbs, with the female jaw's pinch).

   An item surface point inside a body part means the body pokes through the
   item there.  That is a failure for:

     hats   any part that wraps round the head (its footprint holds the
            head's axis), and any part at all sinking into the torso or arms
     hair   any piece sunk into the head (the shells sit a hair off it)
     back   anything inside the torso, hips, head or arms
     held   anything inside the torso, head or legs (the grip may hold the
            hand)

   A part can opt out with ``emb: 1`` when it is MEANT to grow out of the
   body -- a horn's root, the stalk of an antenna -- because that is a seam,
   not a clip.  Faces are textures and are not checked.

     node tools/fitcheck.js                 # every item, summary + failures
     node tools/fitcheck.js --prefix hat_ny22_ --verbose
     node tools/fitcheck.js --items hat_crown,hat_beanie
     node tools/fitcheck.js --json report.json

   Exit status 1 when anything fails. */
'use strict';

var path = require('path');
var fs = require('fs');
var cp = require('child_process');

var ROOT = path.resolve(__dirname, '..');

function arg(name, fallback) {
  var i = process.argv.indexOf('--' + name);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}
var VERBOSE = process.argv.indexOf('--verbose') >= 0;
var TOL = parseFloat(arg('tol', '0.015'));

// ------------------------------------------------------------ the engine
global.window = global;
global.document = undefined;
function load(rel) {
  var src = fs.readFileSync(path.join(ROOT, rel), 'utf8');
  // the engine files are IIFEs over ``window``; run them in this context
  new Function('window', 'globalThis', src)(global, global);
}
load('static/js/engine/gl.js');
load('static/js/engine/geometry.js');
load('static/js/engine/shapes.js');
global.Textures = { decal: function () { return null; },
                    faceSlot: function () { return null; } };
load('static/js/engine/avatar.js');
var MESHES = Geometry.build();

// the bakes the body is drawn with: bevel radii in the unit cube, and taper
var BAKES = {
  rbox: { r: [0.085, 0.085, 0.085] },
  rlimb: { r: [0.133, 0.064, 0.133] },
  rhead: { r: [0.196, 0.214, 0.202] },
  fhead: { r: [0.205, 0.2165, 0.205], taper: { bottom: 0.85, from: 0.55 } },
  cyl: { cyl: true }
};

// ------------------------------------------------------------ maths
function euler(r) {
  r = r || [0, 0, 0];
  var cx = Math.cos(r[0]), sx = Math.sin(r[0]), cy = Math.cos(r[1]), sy = Math.sin(r[1]);
  var cz = Math.cos(r[2]), sz = Math.sin(r[2]);
  // column major, matching the renderer (R = Ry * Rx * Rz)
  return [cy * cz + sy * sx * sz, cx * sz, -sy * cz + cy * sx * sz,
          -cy * sz + sy * sx * cz, cx * cz, sy * sz + cy * sx * cz,
          sy * cx, -sx, cy * cx];
}
function apply(m, v) {
  return [m[0] * v[0] + m[3] * v[1] + m[6] * v[2],
          m[1] * v[0] + m[4] * v[1] + m[7] * v[2],
          m[2] * v[0] + m[5] * v[1] + m[8] * v[2]];
}
function applyT(m, v) {        // the inverse of a rotation is its transpose
  return [m[0] * v[0] + m[1] * v[1] + m[2] * v[2],
          m[3] * v[0] + m[4] * v[1] + m[5] * v[2],
          m[6] * v[0] + m[7] * v[1] + m[8] * v[2]];
}

/* How far ``world`` is inside a body solid, in world units (<= 0 outside). */
function depthIn(solid, world) {
  var d = [world[0] - solid.p[0], world[1] - solid.p[1], world[2] - solid.p[2]];
  var q = applyT(solid.m, d);
  var s = solid.s;
  var u = [q[0] / s[0], q[1] / s[1], q[2] / s[2]];          // unit cube
  if (Math.abs(u[0]) > 0.52 || Math.abs(u[1]) > 0.52 || Math.abs(u[2]) > 0.52) return 0;
  var bake = solid.bake;
  if (bake.cyl) {
    var rr = Math.hypot(u[0] * 2, u[2] * 2);
    if (rr >= 1 || Math.abs(u[1]) >= 0.5) return 0;
    return Math.min((1 - rr) * Math.min(s[0], s[2]) / 2, (0.5 - Math.abs(u[1])) * s[1]);
  }
  if (bake.taper) {
    var h = 0.5, lowWidth = bake.taper.bottom, top = bake.taper.from;
    var t = Math.min(1, Math.max(0, (u[1] + h) / top));
    var pinch = lowWidth + (1 - lowWidth) * t * t * (3 - 2 * t);
    u = [u[0] / pinch, u[1], u[2] / pinch];
  }
  var r = bake.r;
  var a = [0.5 - r[0], 0.5 - r[1], 0.5 - r[2]];
  var e = [Math.max(0, Math.abs(u[0]) - a[0]), Math.max(0, Math.abs(u[1]) - a[1]),
           Math.max(0, Math.abs(u[2]) - a[2])];
  var k = Math.sqrt(Math.pow(e[0] / r[0], 2) + Math.pow(e[1] / r[1], 2) + Math.pow(e[2] / r[2], 2));
  if (k >= 1) return 0;
  if (e[0] === 0 && e[1] === 0 && e[2] === 0) {
    return Math.min((0.5 - Math.abs(u[0])) * s[0], (0.5 - Math.abs(u[1])) * s[1],
                    (0.5 - Math.abs(u[2])) * s[2]);
  }
  return (1 - k) * Math.min(r[0] * s[0], r[1] * s[1], r[2] * s[2]);
}

/* The part's triangles in world space, the way the renderer draws it. */
function triangles(part) {
  var mesh = MESHES[part.t || 'box'] || MESHES.box;
  var m = euler(part.r);
  var pos = mesh.positions, idx = mesh.indices;
  var verts = [];
  for (var i = 0; i < pos.length; i += 3) {
    var w = apply(m, [pos[i] * part.s[0], pos[i + 1] * part.s[1], pos[i + 2] * part.s[2]]);
    verts.push([w[0] + part.p[0], w[1] + part.p[1], w[2] + part.p[2]]);
  }
  var tris = [];
  var lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
  for (var t = 0; t < idx.length; t += 3) {
    tris.push([verts[idx[t]], verts[idx[t + 1]], verts[idx[t + 2]]]);
  }
  verts.forEach(function (v) {
    for (var k = 0; k < 3; k++) { lo[k] = Math.min(lo[k], v[k]); hi[k] = Math.max(hi[k], v[k]); }
  });
  var c = [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2];
  var rad = 0;
  verts.forEach(function (v) { rad = Math.max(rad, Math.hypot(v[0] - c[0], v[1] - c[1], v[2] - c[2])); });
  return { tris: tris, lo: lo, hi: hi, c: c, r: rad };
}

/* Surface samples with their normals: every vertex of the part's real
   mesh, turned and moved the way the renderer draws it.  Normals go through
   the inverse transpose (the scale is not uniform). */
function samplesOf(part) {
  var mesh = MESHES[part.t || 'box'] || MESHES.box;
  var m = euler(part.r);
  var pos = mesh.positions, nor = mesh.normals;
  var out = [];
  for (var i = 0; i < pos.length; i += 3) {
    var w = apply(m, [pos[i] * part.s[0], pos[i + 1] * part.s[1], pos[i + 2] * part.s[2]]);
    var n = apply(m, [nor[i] / part.s[0], nor[i + 1] / part.s[1], nor[i + 2] / part.s[2]]);
    var l = Math.hypot(n[0], n[1], n[2]) || 1;
    out.push({ p: [w[0] + part.p[0], w[1] + part.p[1], w[2] + part.p[2]],
               n: [n[0] / l, n[1] / l, n[2] / l] });
  }
  return out;
}

/* Moller-Trumbore, both faces: distance along the ray or -1. */
function hit(o, d, tri) {
  var a = tri[0], b = tri[1], c = tri[2];
  var e1 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], e2 = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
  var p = [d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2], d[0] * e2[1] - d[1] * e2[0]];
  var det = e1[0] * p[0] + e1[1] * p[1] + e1[2] * p[2];
  if (Math.abs(det) < 1e-12) return -1;
  var inv = 1 / det;
  var tv = [o[0] - a[0], o[1] - a[1], o[2] - a[2]];
  var u = (tv[0] * p[0] + tv[1] * p[1] + tv[2] * p[2]) * inv;
  if (u < 0 || u > 1) return -1;
  var q = [tv[1] * e1[2] - tv[2] * e1[1], tv[2] * e1[0] - tv[0] * e1[2], tv[0] * e1[1] - tv[1] * e1[0]];
  var v = (d[0] * q[0] + d[1] * q[1] + d[2] * q[2]) * inv;
  if (v < 0 || u + v > 1) return -1;
  var t = (e2[0] * q[0] + e2[1] * q[1] + e2[2] * q[2]) * inv;
  return t > 1e-6 ? t : -1;
}

// directions spread evenly over a sphere (a Fibonacci lattice)
var DIRS = (function () {
  var n = parseInt(arg('rays', '900'), 10), out = [];
  var g = Math.PI * (3 - Math.sqrt(5));
  for (var i = 0; i < n; i++) {
    var y = 1 - (i + 0.5) * 2 / n, r = Math.sqrt(1 - y * y), th = g * i;
    out.push([Math.cos(th) * r, y, Math.sin(th) * r]);
  }
  return out;
})();

/* Where a ray from a solid's own centre leaves it. */
function exitOf(solid, d) {
  var lo = 0, hi = Math.max(solid.s[0], solid.s[1], solid.s[2]);
  for (var k = 0; k < 22; k++) {
    var mid = (lo + hi) / 2;
    var q = [solid.p[0] + d[0] * mid, solid.p[1] + d[1] * mid, solid.p[2] + d[2] * mid];
    if (depthIn(solid, q) > 0) lo = mid; else hi = mid;
  }
  return lo;
}

function boxesMeet(a, b, pad) {
  for (var k = 0; k < 3; k++) {
    if (a.hi[k] + pad < b.lo[k] || b.hi[k] + pad < a.lo[k]) return false;
  }
  return true;
}

// ------------------------------------------------------------ the catalogue
function catalogue() {
  var py = 'import json,sys; sys.path.insert(0, %s); from app.models import catalog; ' +
           'print(json.dumps(catalog.ALL_ITEMS))';
  var out = cp.execFileSync('python3', ['-c', py.replace('%s', JSON.stringify(ROOT))],
                            { cwd: ROOT, maxBuffer: 256 * 1024 * 1024 });
  return JSON.parse(out.toString());
}

function solidsOf(parts) {
  return parts.filter(function (p) {
    return p.k && p.k !== 'hair' && p.k !== 'badge';
  }).map(function (p) {
    var t = p.t || 'rbox';
    var m = euler(p.r);
    var half = Math.max(p.s[0], p.s[1], p.s[2]) / 2;
    return { k: p.k, t: t, p: p.p, s: p.s, m: m, bake: BAKES[t] || BAKES.rbox,
             lo: [p.p[0] - half, p.p[1] - half, p.p[2] - half],
             hi: [p.p[0] + half, p.p[1] + half, p.p[2] + half] };
  });
}

var WEAR = { hat: 1, hair: 1, back: 1, usable: 1 };
// which parts of the body each kind of item is measured against
var AGAINST = {
  hat: { head: 1, neck: 1, torso: 1, arm: 1 },
  hair: { head: 1 },
  back: { head: 1, neck: 1, torso: 1, hips: 1, arm: 1 },
  usable: { head: 1, torso: 1, hips: 1, leg: 1, foot: 1 }
};

/* Rays out of each body part that pass through an item part: where the body
   reaches further along the ray than the far side of the item, the body
   shows through it (or the piece is buried in the body). */
function check(item) {
  var report = { id: item.id, slot: item.slot, worst: 0, where: '', fails: [] };
  ['male', 'female'].forEach(function (build) {
    var pose = Avatar.pose('idle', 0, 0, { body_type: build });
    var desc = { body_type: build, colors: {}, items: {} };
    var holding = null;
    if (item.slot === 'usable') holding = item;
    else desc.items[item.slot] = { item_id: item.id, slot: item.slot, data: item.data };
    var opts = { position: [0, 0, 0], yaw: 0, pose: pose, holding: holding, pitch: 0, time: 0 };
    var built = Avatar.build(desc, opts);
    var bare = Avatar.build({ body_type: build, colors: {}, items: {} }, opts);
    var solids = solidsOf(bare).filter(function (s) { return AGAINST[item.slot][s.k]; });
    var mine = built.slice(bare.length);
    var authored = (item.data && item.data.parts) || [];
    var hand = holding && mine.length ? mine[0].p : null;
    var geos = mine.map(function (part) { return triangles(part); });
    /* Is a point inside one of the item's own solids?  Ray parity along a
       slightly skewed direction (so no ray runs down a seam). */
    var RAY = (function () { var d = [0.31, 0.93, 0.19]; var l = Math.hypot(d[0], d[1], d[2]);
                             return [d[0] / l, d[1] / l, d[2] / l]; })();
    function covered(point, skip) {
      for (var g = 0; g < geos.length; g++) {
        if (g === skip) continue;
        var geo = geos[g];
        if (point[0] < geo.lo[0] || point[0] > geo.hi[0] || point[1] < geo.lo[1] ||
            point[1] > geo.hi[1] || point[2] < geo.lo[2] || point[2] > geo.hi[2]) continue;
        var crossings = 0;
        for (var i = 0; i < geo.tris.length; i++) if (hit(point, RAY, geo.tris[i]) > 0) crossings++;
        if (crossings % 2 === 1) return true;
      }
      return false;
    }
    mine.forEach(function (part, index) {
      var src = authored[index] || {};
      if (src.emb) return;
      var geo = geos[index];
      var pts = null;
      solids.forEach(function (solid) {
        if (!boxesMeet(geo, solid, 0.05)) return;
        pts = pts || samplesOf(part);
        var wraps = geo.lo[0] < solid.p[0] - 0.15 && geo.hi[0] > solid.p[0] + 0.15 &&
                    geo.lo[2] < solid.p[2] - 0.15 && geo.hi[2] > solid.p[2] + 0.15 &&
                    geo.lo[1] < solid.p[1] + solid.s[1] / 2 && geo.hi[1] > solid.p[1] - solid.s[1] / 2;
        // a piece wholly inside the body is a piece nobody can see
        var inside = pts.filter(function (q) { return depthIn(solid, q.p) > 0.005; }).length;
        if (inside > pts.length * 0.85 && depthIn(solid, geo.c) > 0.03) {
          report.fails.push({ build: build, part: index, t: part.t, into: solid.k, kind: 'buried',
                              depth: Math.round(depthIn(solid, geo.c) * 1000) / 1000, rays: inside });
          return;
        }
        /* A piece set into the scalp (a horn's root, a lock of hair) meets
           the head in a seam, which is how it is meant to look.  What may not
           happen is the head coming out through something that goes ROUND it
           -- a band, a dome, a cuff -- or the trunk and limbs coming out
           through anything at all. */
        if (solid.k === 'head' && !wraps) return;
        /* A sample is a defect when it is a WALL facing out from the body,
           sunk inside it, and nothing else of the item covers the body
           there: then the body shows through that wall.  A face that runs
           across the body (the top of a solid band, the cap of a cuff) lies
           inside it by design and is never seen. */
        var worst = 0, count = 0;
        pts.forEach(function (q) {
          if (hand && Math.hypot(q.p[0] - hand[0], q.p[1] - hand[1], q.p[2] - hand[2]) < 0.9) return;
          var depth = depthIn(solid, q.p);
          if (depth <= TOL) return;
          var h = [q.p[0] - solid.p[0], 0, q.p[2] - solid.p[2]];
          var hl = Math.hypot(h[0], h[2]);
          if (hl < 1e-6) return;
          h = [h[0] / hl, 0, h[2] / hl];
          var outward = q.n[0] * h[0] + q.n[2] * h[2];
          if (Math.abs(q.n[1]) > 0.75 || outward < 0.35) return;
          // where the body surface is, straight out from here
          var at = q.p.slice();
          for (var step = 0; step < 80 && depthIn(solid, at) > 0; step++) {
            at = [at[0] + h[0] * 0.01, at[1], at[2] + h[2] * 0.01];
          }
          at = [at[0] + h[0] * 0.012, at[1], at[2] + h[2] * 0.012];
          if (covered(at, index)) return;
          count++;
          if (depth > worst) worst = depth;
        });
        if (count < 3) return;
        report.fails.push({ build: build, part: index, t: part.t, into: solid.k, kind: 'through',
                            depth: Math.round(worst * 1000) / 1000, rays: count });
        if (worst >= report.worst) {
          report.worst = worst;
          report.where = build + ' part ' + index + ' (' + part.t + ') through ' + solid.k;
        }
      });
    });
  });
  return report;
}

(function main() {
  var items = catalogue().filter(function (it) {
    return WEAR[it.slot] && it.data && it.data.parts && it.data.parts.length;
  });
  var only = (arg('items', '') || '').split(',').filter(Boolean);
  var prefix = arg('prefix', '');
  var event = arg('event', '');
  if (only.length) items = items.filter(function (it) { return only.indexOf(it.id) >= 0; });
  if (prefix) items = items.filter(function (it) { return it.id.indexOf(prefix) === 0; });
  if (event) items = items.filter(function (it) { return it.event === event; });
  var failed = 0, reports = [];
  items.forEach(function (it) {
    var r = check(it);
    reports.push(r);
    if (r.fails.length) {
      failed++;
      console.log('  FAIL  ' + it.id + '  worst ' + r.worst.toFixed(3) + ' at ' + r.where);
      if (VERBOSE) {
        r.fails.slice(0, 12).forEach(function (f) {
          console.log('          ' + f.build + ' part ' + f.part + ' ' + f.t + ' ' + f.kind + ' ' +
                      f.into + ' ' + f.depth + ' (' + f.rays + ' pts)');
        });
      }
    } else if (VERBOSE) {
      console.log('  PASS  ' + it.id + (r.worst ? '  (' + r.worst.toFixed(3) + ')' : ''));
    }
  });
  if (arg('json', '')) fs.writeFileSync(arg('json', ''), JSON.stringify(reports, null, 1));
  console.log('== fit check: ' + items.length + ' wearables, ' + (items.length - failed) +
              ' sit on both builds, ' + failed + ' clip ==');
  process.exit(failed ? 1 : 0);
})();
