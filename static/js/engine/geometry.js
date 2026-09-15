/* BLOCKHAVEN engine -- procedural meshes.
   Every primitive is unit sized and centred on the origin so an instance's
   model matrix carries all of the position/rotation/scale information. */
(function (global) {
  'use strict';

  var Geometry = {};

  /* Make every triangle wind counter-clockwise when seen from outside.

     The scene is drawn with back-face culling on, so a triangle whose index
     order disagrees with its own vertex normals gets culled and the solid
     reads as a hollow, see-through shell.  Rather than hand-checking each
     primitive below (and every one added later) the winding is measured
     against the authored normals here and flipped when it disagrees. */
  function fixWinding(positions, normals, indices) {
    for (var t = 0; t < indices.length; t += 3) {
      var a = indices[t] * 3, b = indices[t + 1] * 3, c = indices[t + 2] * 3;
      var e1x = positions[b] - positions[a];
      var e1y = positions[b + 1] - positions[a + 1];
      var e1z = positions[b + 2] - positions[a + 2];
      var e2x = positions[c] - positions[a];
      var e2y = positions[c + 1] - positions[a + 1];
      var e2z = positions[c + 2] - positions[a + 2];
      var fx = e1y * e2z - e1z * e2y;
      var fy = e1z * e2x - e1x * e2z;
      var fz = e1x * e2y - e1y * e2x;
      var nx = normals[a] + normals[b] + normals[c];
      var ny = normals[a + 1] + normals[b + 1] + normals[c + 1];
      var nz = normals[a + 2] + normals[b + 2] + normals[c + 2];
      if (fx * nx + fy * ny + fz * nz < 0) {
        var swap = indices[t + 1];
        indices[t + 1] = indices[t + 2];
        indices[t + 2] = swap;
      }
    }
    return indices;
  }

  function mesh(positions, normals, uvs, indices) {
    fixWinding(positions, normals, indices);
    return {
      positions: new Float32Array(positions),
      normals: new Float32Array(normals),
      uvs: new Float32Array(uvs),
      indices: (positions.length / 3 > 65535)
        ? new Uint32Array(indices) : new Uint16Array(indices)
    };
  }

  Geometry.box = function () {
    var p = [], n = [], u = [], i = [];
    var faces = [
      { nrm: [0, 0, 1], v: [[-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5]] },
      { nrm: [0, 0, -1], v: [[0.5, -0.5, -0.5], [-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5], [0.5, 0.5, -0.5]] },
      { nrm: [1, 0, 0], v: [[0.5, -0.5, 0.5], [0.5, -0.5, -0.5], [0.5, 0.5, -0.5], [0.5, 0.5, 0.5]] },
      { nrm: [-1, 0, 0], v: [[-0.5, -0.5, -0.5], [-0.5, -0.5, 0.5], [-0.5, 0.5, 0.5], [-0.5, 0.5, -0.5]] },
      { nrm: [0, 1, 0], v: [[-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5]] },
      { nrm: [0, -1, 0], v: [[-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5]] }
    ];
    var uvq = [[0, 0], [1, 0], [1, 1], [0, 1]];
    for (var f = 0; f < faces.length; f++) {
      var base = p.length / 3;
      for (var k = 0; k < 4; k++) {
        p.push(faces[f].v[k][0], faces[f].v[k][1], faces[f].v[k][2]);
        n.push(faces[f].nrm[0], faces[f].nrm[1], faces[f].nrm[2]);
        u.push(uvq[k][0], uvq[k][1]);
      }
      i.push(base, base + 1, base + 2, base, base + 2, base + 3);
    }
    return mesh(p, n, u, i);
  };

  Geometry.cylinder = function (segments) {
    segments = segments || 18;
    var p = [], n = [], u = [], i = [];
    var s, ang, cx, sz;
    for (s = 0; s <= segments; s++) {
      ang = (s / segments) * Math.PI * 2;
      cx = Math.cos(ang) * 0.5; sz = Math.sin(ang) * 0.5;
      var nx = Math.cos(ang), nz = Math.sin(ang);
      p.push(cx, -0.5, sz); n.push(nx, 0, nz); u.push(s / segments, 0);
      p.push(cx, 0.5, sz); n.push(nx, 0, nz); u.push(s / segments, 1);
    }
    for (s = 0; s < segments; s++) {
      var a = s * 2;
      i.push(a, a + 2, a + 3, a, a + 3, a + 1);
    }
    // caps
    for (var side = 0; side < 2; side++) {
      var y = side ? 0.5 : -0.5;
      var ny = side ? 1 : -1;
      var centre = p.length / 3;
      p.push(0, y, 0); n.push(0, ny, 0); u.push(0.5, 0.5);
      for (s = 0; s <= segments; s++) {
        ang = (s / segments) * Math.PI * 2;
        p.push(Math.cos(ang) * 0.5, y, Math.sin(ang) * 0.5);
        n.push(0, ny, 0);
        u.push(0.5 + Math.cos(ang) * 0.5, 0.5 + Math.sin(ang) * 0.5);
      }
      for (s = 0; s < segments; s++) {
        if (side) i.push(centre, centre + 1 + s, centre + 2 + s);
        else i.push(centre, centre + 2 + s, centre + 1 + s);
      }
    }
    return mesh(p, n, u, i);
  };

  Geometry.sphere = function (rings, segments) {
    rings = rings || 12; segments = segments || 18;
    var p = [], n = [], u = [], i = [];
    for (var r = 0; r <= rings; r++) {
      var phi = (r / rings) * Math.PI;
      var y = Math.cos(phi) * 0.5, rad = Math.sin(phi) * 0.5;
      for (var s = 0; s <= segments; s++) {
        var theta = (s / segments) * Math.PI * 2;
        var x = Math.cos(theta) * rad, z = Math.sin(theta) * rad;
        p.push(x, y, z);
        var len = Math.sqrt(x * x + y * y + z * z) || 1;
        n.push(x / len, y / len, z / len);
        u.push(s / segments, 1 - r / rings);
      }
    }
    for (r = 0; r < rings; r++) {
      for (s = 0; s < segments; s++) {
        var a = r * (segments + 1) + s;
        var b = a + segments + 1;
        i.push(a, b, a + 1, a + 1, b, b + 1);
      }
    }
    return mesh(p, n, u, i);
  };

  Geometry.cone = function (segments) {
    segments = segments || 16;
    var p = [], n = [], u = [], i = [], s, ang;
    for (s = 0; s < segments; s++) {
      var a0 = (s / segments) * Math.PI * 2;
      var a1 = ((s + 1) / segments) * Math.PI * 2;
      var x0 = Math.cos(a0) * 0.5, z0 = Math.sin(a0) * 0.5;
      var x1 = Math.cos(a1) * 0.5, z1 = Math.sin(a1) * 0.5;
      var mx = (Math.cos(a0) + Math.cos(a1)) * 0.5;
      var mz = (Math.sin(a0) + Math.sin(a1)) * 0.5;
      var ny = 0.45;
      var len = Math.sqrt(mx * mx + mz * mz + ny * ny) || 1;
      var base = p.length / 3;
      p.push(x0, -0.5, z0, x1, -0.5, z1, 0, 0.5, 0);
      for (var k = 0; k < 3; k++) n.push(mx / len, ny / len, mz / len);
      u.push(s / segments, 0, (s + 1) / segments, 0, (s + 0.5) / segments, 1);
      i.push(base, base + 1, base + 2);
    }
    var centre = p.length / 3;
    p.push(0, -0.5, 0); n.push(0, -1, 0); u.push(0.5, 0.5);
    for (s = 0; s <= segments; s++) {
      ang = (s / segments) * Math.PI * 2;
      p.push(Math.cos(ang) * 0.5, -0.5, Math.sin(ang) * 0.5);
      n.push(0, -1, 0);
      u.push(0.5 + Math.cos(ang) * 0.5, 0.5 + Math.sin(ang) * 0.5);
    }
    for (s = 0; s < segments; s++) i.push(centre, centre + 2 + s, centre + 1 + s);
    return mesh(p, n, u, i);
  };

  /* A right-triangle prism: full height at -Z, zero height at +Z. */
  Geometry.wedge = function () {
    var p = [], n = [], u = [], i = [];
    function quad(v0, v1, v2, v3, nrm) {
      var base = p.length / 3;
      var vs = [v0, v1, v2, v3];
      var uvq = [[0, 0], [1, 0], [1, 1], [0, 1]];
      for (var k = 0; k < 4; k++) {
        p.push(vs[k][0], vs[k][1], vs[k][2]);
        n.push(nrm[0], nrm[1], nrm[2]);
        u.push(uvq[k][0], uvq[k][1]);
      }
      i.push(base, base + 1, base + 2, base, base + 2, base + 3);
    }
    function tri(v0, v1, v2, nrm) {
      var base = p.length / 3;
      var vs = [v0, v1, v2];
      var uvq = [[0, 0], [1, 0], [0.5, 1]];
      for (var k = 0; k < 3; k++) {
        p.push(vs[k][0], vs[k][1], vs[k][2]);
        n.push(nrm[0], nrm[1], nrm[2]);
        u.push(uvq[k][0], uvq[k][1]);
      }
      i.push(base, base + 1, base + 2);
    }
    quad([-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5], [0, -1, 0]);
    quad([0.5, -0.5, -0.5], [-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5], [0.5, 0.5, -0.5], [0, 0, -1]);
    var sy = 1 / Math.sqrt(2);
    quad([-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5], [0, sy, sy]);
    tri([0.5, -0.5, -0.5], [0.5, -0.5, 0.5], [0.5, 0.5, -0.5], [1, 0, 0]);
    tri([-0.5, -0.5, 0.5], [-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5], [-1, 0, 0]);
    return mesh(p, n, u, i);
  };

  Geometry.torus = function (major, minor) {
    major = major || 20; minor = minor || 9;
    var p = [], n = [], u = [], i = [];
    var R = 0.4, r = 0.1;   // relative to a unit bounding box
    for (var a = 0; a <= major; a++) {
      var theta = (a / major) * Math.PI * 2;
      var ct = Math.cos(theta), st = Math.sin(theta);
      for (var b = 0; b <= minor; b++) {
        var phi = (b / minor) * Math.PI * 2;
        var cp = Math.cos(phi), sp = Math.sin(phi);
        p.push((R + r * cp) * ct, r * sp, (R + r * cp) * st);
        n.push(cp * ct, sp, cp * st);
        u.push(a / major, b / minor);
      }
    }
    for (a = 0; a < major; a++) {
      for (b = 0; b < minor; b++) {
        var i0 = a * (minor + 1) + b;
        var i1 = i0 + minor + 1;
        i.push(i0, i1, i0 + 1, i0 + 1, i1, i1 + 1);
      }
    }
    return mesh(p, n, u, i);
  };

  /* A box with rounded edges and corners -- the shape the whole avatar is
     built from.

     ``radius`` may be a single number or a per-axis [rx, ry, rz].  The
     per-axis form matters because an instance's model matrix scales the mesh
     non-uniformly: baking one radius into a 1x1x1 mesh and then stretching it
     to a 1x2x1 arm doubles the rounding along the arm, which domes the ends
     into a pill.  Baking [0.17, 0.08, 0.17] instead lands a uniform bevel once
     the limb scale is applied.

     Each of the six faces is sampled on a grid and pushed onto the Minkowski
     sum of an inner box and an ellipsoid of those radii, so the middle of
     every face stays perfectly flat (and keeps an exact face normal, which is
     what the decal test needs) while the edges curve. */
  Geometry.roundedBox = function (radius, bevelSteps) {
    var r = (typeof radius === 'number' || radius === undefined)
      ? [radius === undefined ? 0.12 : radius,
         radius === undefined ? 0.12 : radius,
         radius === undefined ? 0.12 : radius]
      : [radius[0], radius[1], radius[2]];
    for (var axis = 0; axis < 3; axis++) {
      r[axis] = Math.max(0.0005, Math.min(0.4999, r[axis]));
    }
    bevelSteps = Math.max(1, bevelSteps || 2);
    var h = 0.5;
    var a = [h - r[0], h - r[1], h - r[2]];

    /* Sample positions along one axis.  A uniform grid would spend every
       vertex on the flat middle (which needs two) and leave the bevel as a
       single smooth-shaded chamfer, which is what makes a part read as a
       pillow rather than a bevelled brick.  These put the vertices where the
       curvature actually is. */
    function axisSamples(inner) {
      var out = [];
      var span = h - inner;
      for (var k = 0; k <= bevelSteps; k++) out.push(-h + span * (k / bevelSteps));
      out.push(inner);
      for (k = 1; k <= bevelSteps; k++) out.push(inner + span * (k / bevelSteps));
      return out;
    }
    var samples = [axisSamples(a[0]), axisSamples(a[1]), axisSamples(a[2])];

    var p = [], n = [], u = [], i = [];
    var faces = [
      { axis: 2, sign: 1, ua: 0, va: 1 },
      { axis: 2, sign: -1, ua: 0, va: 1 },
      { axis: 0, sign: 1, ua: 2, va: 1 },
      { axis: 0, sign: -1, ua: 2, va: 1 },
      { axis: 1, sign: 1, ua: 0, va: 2 },
      { axis: 1, sign: -1, ua: 0, va: 2 }
    ];
    function clamp(v, limit) { return v < -limit ? -limit : (v > limit ? limit : v); }

    for (var f = 0; f < faces.length; f++) {
      var face = faces[f];
      var us = samples[face.ua];
      var vs = samples[face.va];
      var base = p.length / 3;
      for (var vi = 0; vi < vs.length; vi++) {
        for (var ui = 0; ui < us.length; ui++) {
          var ideal = [0, 0, 0];
          ideal[face.axis] = h * face.sign;
          ideal[face.ua] = us[ui];
          ideal[face.va] = vs[vi];
          var centre = [clamp(ideal[0], a[0]), clamp(ideal[1], a[1]),
                        clamp(ideal[2], a[2])];
          // direction in radius-normalised space, so the corner is an
          // ellipsoid octant rather than a sphere octant
          var tx = (ideal[0] - centre[0]) / r[0];
          var ty = (ideal[1] - centre[1]) / r[1];
          var tz = (ideal[2] - centre[2]) / r[2];
          var len = Math.sqrt(tx * tx + ty * ty + tz * tz) || 1;
          tx /= len; ty /= len; tz /= len;
          p.push(centre[0] + tx * r[0], centre[1] + ty * r[1],
                 centre[2] + tz * r[2]);
          // the ellipsoid's surface normal is the radius-weighted gradient
          var nx = tx / r[0], ny = ty / r[1], nz = tz / r[2];
          var nlen = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
          n.push(nx / nlen, ny / nlen, nz / nlen);
          // UVs run 0..1 across the whole face, and stay linear in position,
          // so a decal still lands square on the flat middle
          var su = us[ui] + h, sv = vs[vi] + h;
          if (face.axis === 2) su = face.sign > 0 ? su : 1 - su;
          if (face.axis === 0) su = face.sign > 0 ? 1 - su : su;
          u.push(su, sv);
        }
      }
      var stride = us.length;
      for (vi = 0; vi < vs.length - 1; vi++) {
        for (ui = 0; ui < us.length - 1; ui++) {
          var i0 = base + vi * stride + ui;
          var i1 = i0 + 1;
          var i2 = i0 + stride;
          var i3 = i2 + 1;
          i.push(i0, i1, i3, i0, i3, i2);
        }
      }
    }
    return mesh(p, n, u, i);
  };


  /* ==========================================================================
     LOFTED SURFACES
     A body is not a pile of parts.  Rounded boxes are right for a blocky
     build, but a figure with real curves cannot be made by bolting spheres
     onto a box -- the joins show, the shading breaks at every seam, and the
     result reads as assembled rather than shaped.

     So there is a second way of making a mesh here: sweep one continuous skin
     through a stack of cross sections.  Each section is a superellipse ring
     with its own half width, its own front and back depth and its own corner
     sharpness, so a single surface can be wide at the shoulder, deep at the
     chest, narrow at the waist and wide again at the hip.  The curves ARE the
     surface; there is nothing stuck to it and nothing to come unstuck.
     ========================================================================== */

  /* Monotone cubic (Fritsch-Carlson) tangents.

     A Catmull-Rom spline through unevenly spaced rings overshoots, which on a
     body means a bulge where nothing was authored -- a pot belly under the
     ribs, a flare under the knee.  This interpolation cannot overshoot: it
     stays inside the values it is given and flattens to a smooth apex at a
     local maximum, which is exactly what a bust or a calf is. */
  function monotoneTangents(xs, ys) {
    var n = xs.length;
    var m = new Array(n), d = new Array(n - 1), i;
    for (i = 0; i < n - 1; i++) {
      d[i] = (ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i] || 1e-6);
    }
    m[0] = d[0];
    m[n - 1] = d[n - 2];
    for (i = 1; i < n - 1; i++) {
      m[i] = (d[i - 1] * d[i] <= 0) ? 0 : (d[i - 1] + d[i]) * 0.5;
    }
    for (i = 0; i < n - 1; i++) {
      if (d[i] === 0) { m[i] = 0; m[i + 1] = 0; continue; }
      var a = m[i] / d[i], b = m[i + 1] / d[i];
      var s = a * a + b * b;
      if (s > 9) {
        var t = 3 / Math.sqrt(s);
        m[i] = t * a * d[i];
        m[i + 1] = t * b * d[i];
      }
    }
    return m;
  }

  function hermite(xs, ys, ms, x) {
    var n = xs.length;
    if (x <= xs[0]) return ys[0];
    if (x >= xs[n - 1]) return ys[n - 1];
    var lo = 0, hi = n - 1;
    while (hi - lo > 1) {
      var mid = (lo + hi) >> 1;
      if (xs[mid] <= x) lo = mid; else hi = mid;
    }
    var h = xs[hi] - xs[lo];
    var t = (x - xs[lo]) / h;
    var t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * ys[lo] + (t3 - 2 * t2 + t) * h * ms[lo] +
           (-2 * t3 + 3 * t2) * ys[hi] + (t3 - t2) * h * ms[hi];
  }

  var SECTION_FIELDS = ['w', 'df', 'db', 'n', 'cx', 'cz', 'cleft', 'cleftW'];

  /* Turn an authored profile into something that can be sampled at any
     height.  ``df``/``db`` default to ``d`` so a limb can be written with one
     depth and a torso with two. */
  function profileCurve(profile) {
    var ys = profile.map(function (s) { return s.y; });
    var curves = {};
    SECTION_FIELDS.forEach(function (key) {
      var vals = profile.map(function (s) {
        if (key === 'df' || key === 'db') {
          return s[key] === undefined ? (s.d === undefined ? 0.5 : s.d) : s[key];
        }
        if (key === 'n') return s.n === undefined ? 2.6 : s.n;
        if (key === 'cleftW') return s.cleftW === undefined ? 0.32 : s.cleftW;
        return s[key] === undefined ? 0 : s[key];
      });
      curves[key] = { ys: vals, ms: monotoneTangents(ys, vals) };
    });
    return {
      lo: ys[0],
      hi: ys[ys.length - 1],
      at: function (y) {
        var out = { y: y };
        SECTION_FIELDS.forEach(function (key) {
          out[key] = hermite(ys, curves[key].ys, curves[key].ms, y);
        });
        return out;
      }
    };
  }

  /* One point on a section.  ``t`` runs 0..1 around the ring starting at the
     front (+Z) and turning towards +X.

     The section is a superellipse, so ``n`` alone carries it from an ellipse
     (2) to a squircle with flat faces and rounded corners (4+) -- which is
     how the same generator draws both a soft waist and a flat-enough face
     plate for a decal to print on.  ``cleft`` presses the front of the ring
     in towards the centre line with a gaussian, which is what moulds a chest
     into the body instead of parking two spheres on it. */
  function sectionPoint(sec, t) {
    var ang = t * Math.PI * 2;
    var sn = Math.sin(ang), cs = Math.cos(ang);
    var e = 2 / Math.max(2, sec.n);
    var x = sec.w * (sn < 0 ? -1 : 1) * Math.pow(Math.abs(sn), e);
    var depth = cs >= 0 ? sec.df : sec.db;
    if (cs >= 0 && sec.cleft > 0.0001) {
      var k = x / Math.max(1e-4, sec.w * sec.cleftW);
      depth *= 1 - sec.cleft * Math.exp(-k * k);
    }
    var z = depth * (cs < 0 ? -1 : 1) * Math.pow(Math.abs(cs), e);
    return [x + sec.cx, sec.y, z + sec.cz];
  }

  /* Sweep a profile into a mesh.

     opts:
       rows     rings to resample to (default 40)
       segs     points around a ring (default 28)
       from,to  emit only this slice of the profile.  The curve is still
                evaluated over the whole thing, so two slices of one profile
                meet with matching positions AND matching normals -- which is
                what lets a torso and a hip be two colours and still be one
                unbroken body.
       arc      [t0, t1] to emit a patch of the surface rather than a tube
       caps     close the ends (default true; never for a patch)
       inflate  push every vertex out along its own normal, for something
                that has to sit ON the surface (a printed graphic, a stripe)
       uv       {x0, x1, y0, y1} planar window mapped to 0..1 and clamped, so
                a decal lands where it was meant to

     Returns {mesh, size, centre, at}: the mesh normalised into the unit cube
     (because an instance's model matrix carries the real size), together with
     the box it came out of, so the caller can scale it straight back. */
  Geometry.loft = function (profile, opts) {
    opts = opts || {};
    var curve = profileCurve(profile);
    var from = opts.from === undefined ? curve.lo : opts.from;
    var to = opts.to === undefined ? curve.hi : opts.to;
    var rows = Math.max(2, opts.rows || 40);
    var segs = Math.max(6, opts.segs || 28);
    var arc = opts.arc || null;
    var caps = arc ? false : (opts.caps !== false);
    var inflate = opts.inflate || 0;

    var p = [], n = [], u = [], idx = [];
    var grid = [];              // rows of [x,y,z]
    var r, s;

    for (r = 0; r < rows; r++) {
      var y = from + (to - from) * (r / (rows - 1));
      var sec = curve.at(y);
      var ring = [];
      for (s = 0; s < segs; s++) {
        var t = arc ? (arc[0] + (arc[1] - arc[0]) * (s / (segs - 1)))
                    : (s / segs);
        ring.push(sectionPoint(sec, t));
      }
      grid.push(ring);
    }

    // Normals from the surface itself: the cross product of the two
    // tangents, measured on the real geometry, so every curve shades as the
    // one surface it is.
    function at(ri, si) {
      var row = grid[Math.max(0, Math.min(rows - 1, ri))];
      var k = arc ? Math.max(0, Math.min(segs - 1, si)) : ((si % segs) + segs) % segs;
      return row[k];
    }
    function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }

    var normals = [];
    for (r = 0; r < rows; r++) {
      var nrow = [];
      for (s = 0; s < segs; s++) {
        var du = sub(at(r, s + 1), at(r, s - 1));
        var dv = sub(at(r + 1, s), at(r - 1, s));
        var nx = du[1] * dv[2] - du[2] * dv[1];
        var ny = du[2] * dv[0] - du[0] * dv[2];
        var nz = du[0] * dv[1] - du[1] * dv[0];
        var len = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
        // the ring turns from the front towards +X and the rows climb, so
        // this cross product already points out of the surface
        nrow.push([nx / len, ny / len, nz / len]);
      }
      normals.push(nrow);
    }

    // a seam column is duplicated so the wrap gets u=0 and u=1 with the same
    // position and the same normal -- a UV seam, never a shading one
    var cols = arc ? segs : segs + 1;
    var win = opts.uv || null;

    function pushVertex(ri, si) {
      var pt = at(ri, si);
      var nv = normals[ri][arc ? si : (si % segs)];
      p.push(pt[0] + nv[0] * inflate, pt[1] + nv[1] * inflate,
             pt[2] + nv[2] * inflate);
      n.push(nv[0], nv[1], nv[2]);
      if (win) {
        var uu = (pt[0] - win.x0) / (win.x1 - win.x0);
        var vv = (pt[1] - win.y0) / (win.y1 - win.y0);
        u.push(Math.max(0, Math.min(1, uu)), Math.max(0, Math.min(1, vv)));
      } else {
        u.push(si / (cols - 1), ri / (rows - 1));
      }
    }

    for (r = 0; r < rows; r++) {
      for (s = 0; s < cols; s++) pushVertex(r, s);
    }
    for (r = 0; r < rows - 1; r++) {
      for (s = 0; s < cols - 1; s++) {
        var i0 = r * cols + s, i1 = i0 + 1;
        var i2 = i0 + cols, i3 = i2 + 1;
        idx.push(i0, i1, i3, i0, i3, i2);
      }
    }

    if (caps) {
      [0, rows - 1].forEach(function (ri) {
        var sign = ri === 0 ? -1 : 1;
        var cx = 0, cy = 0, cz = 0;
        for (s = 0; s < segs; s++) {
          var pt = grid[ri][s];
          cx += pt[0]; cy += pt[1]; cz += pt[2];
        }
        cx /= segs; cy /= segs; cz /= segs;
        var base = p.length / 3;
        p.push(cx, cy, cz); n.push(0, sign, 0); u.push(0.5, 0.5);
        for (s = 0; s <= segs; s++) {
          var q = grid[ri][s % segs];
          p.push(q[0], q[1], q[2]);
          n.push(0, sign, 0);
          u.push(0.5, 0.5);
        }
        for (s = 0; s < segs; s++) {
          if (sign > 0) idx.push(base, base + 1 + s, base + 2 + s);
          else idx.push(base, base + 2 + s, base + 1 + s);
        }
      });
    }

    // Normalise the positions into the unit cube -- an instance's model
    // matrix carries the real size -- but leave the normals alone: the same
    // matrix stretches the mesh straight back out again, so the normals that
    // belong to the finished shape are the ones measured on it.
    var lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
    for (var i = 0; i < p.length; i += 3) {
      for (var a = 0; a < 3; a++) {
        if (p[i + a] < lo[a]) lo[a] = p[i + a];
        if (p[i + a] > hi[a]) hi[a] = p[i + a];
      }
    }
    var size = [Math.max(1e-4, hi[0] - lo[0]), Math.max(1e-4, hi[1] - lo[1]),
                Math.max(1e-4, hi[2] - lo[2])];
    var centre = [(hi[0] + lo[0]) / 2, (hi[1] + lo[1]) / 2, (hi[2] + lo[2]) / 2];
    for (i = 0; i < p.length; i += 3) {
      p[i] = (p[i] - centre[0]) / size[0];
      p[i + 1] = (p[i + 1] - centre[1]) / size[1];
      p[i + 2] = (p[i + 2] - centre[2]) / size[2];
    }

    return { mesh: mesh(p, n, u, idx), size: size, centre: centre,
             at: curve.at, lo: curve.lo, hi: curve.hi };
  };

  /* Meshes registered by another module (the avatar rig bakes its lofted
     body here) so that every Renderer built afterwards picks them up. */
  Geometry.extra = {};
  Geometry.register = function (name, built) {
    Geometry.extra[name] = built.mesh || built;
    return built;
  };

  Geometry.quad = function () {
    return mesh(
      [-0.5, -0.5, 0, 0.5, -0.5, 0, 0.5, 0.5, 0, -0.5, 0.5, 0],
      [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1],
      [0, 0, 1, 0, 1, 1, 0, 1],
      [0, 1, 2, 0, 2, 3]);
  };

  Geometry.build = function () {
    var base = {
      box: Geometry.box(),
      // three bakes of the same shape, chosen so that once the avatar's part
      // sizes are applied the bevel comes out roughly uniform in world units
      rbox: Geometry.roundedBox(0.085, 2),                  // near-cubic parts
      rlimb: Geometry.roundedBox([0.133, 0.064, 0.133], 2),  // 1:2:1 arms, legs
      rhead: Geometry.roundedBox([0.196, 0.214, 0.202], 3),  // the head
      cyl: Geometry.cylinder(18),
      sph: Geometry.sphere(12, 18),
      cone: Geometry.cone(16),
      wedge: Geometry.wedge(),
      torus: Geometry.torus(20, 9),
      quad: Geometry.quad()
    };
    // ...plus whatever the avatar rig baked for itself
    Object.keys(Geometry.extra).forEach(function (name) {
      base[name] = Geometry.extra[name];
    });
    return base;
  };

  global.Geometry = Geometry;
})(window);
