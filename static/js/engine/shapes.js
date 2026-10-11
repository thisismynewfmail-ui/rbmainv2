/* BLOCKHAVEN engine -- sculpted shapes.

   The core primitives (box, cylinder, sphere, cone, wedge, torus and the
   rounded boxes the avatar is built from) draw a world.  They do not draw a
   top hat with a curled brim, a baseball cap with a bent bill, a pumpkin with
   ribs or a medal with a bevelled rim -- an item made only of those reads as
   "shapes with a texture on".  This module bakes the meshes that let an item
   be modelled instead:

     lathe    a profile spun round the Y axis (domes, crowns, bells, pots,
              pumpkins, gems, teardrops), optionally ribbed or faceted
     extrude  a 2D outline pushed out along Z with a bevelled edge (medals,
              stars, shields, wings, blades, bones, leaves, flames) -- the
              front face carries planar UVs over the outline's bounds, so a
              decal lands on it like a print on a coin
     sheet    a thin surface with real thickness (a cap's bent bill, a cowboy
              brim curled at the sides, a cape hanging in folds)
     tube     a tapering tube along a curve (horns, a witch hat's crook)

   Every mesh is registered with Geometry.register, so any Renderer built
   after this file has loaded draws it by name -- an item part simply says
   ``"t": "hemi"`` the way it says ``"t": "box"``.  Load this after
   geometry.js and before anything constructs a Renderer.

   Like every primitive, each mesh is normalised into the unit cube centred
   on the origin, and an instance's scale carries its real size.  Normals are
   measured on the shape BEFORE that normalisation, so a part drawn at its
   native proportions (Shapes.native[name]) shades exactly as modelled. */
(function (global) {
  'use strict';

  var Shapes = { native: {}, centre: {} };
  var TAU = Math.PI * 2;

  // ------------------------------------------------------------- plumbing
  function v3sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function v3cross(a, b) {
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]];
  }
  function v3norm(a) {
    var l = Math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]);
    return l > 1e-9 ? [a[0] / l, a[1] / l, a[2] / l] : [0, 1, 0];
  }
  function v3dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }

  /* A growing mesh: positions, normals, uvs and triangle indices. */
  function Builder() { this.p = []; this.n = []; this.u = []; this.i = []; }
  Builder.prototype.vert = function (pos, nrm, uv) {
    this.p.push(pos[0], pos[1], pos[2]);
    this.n.push(nrm[0], nrm[1], nrm[2]);
    this.u.push(uv[0], uv[1]);
    return this.p.length / 3 - 1;
  };
  Builder.prototype.tri = function (a, b, c) { this.i.push(a, b, c); };
  Builder.prototype.quad = function (a, b, c, d) { this.i.push(a, b, c, a, c, d); };

  /* Every triangle wound counter-clockwise from outside (judged against its
     own vertex normals), positions normalised into the unit cube, typed
     arrays out.  Returns {mesh, size} where size is the shape's real extent,
     which is what Shapes.native records. */
  function finish(b) {
    var p = b.p, n = b.n, idx = b.i, t;
    for (t = 0; t < idx.length; t += 3) {
      var a = idx[t] * 3, c1 = idx[t + 1] * 3, c2 = idx[t + 2] * 3;
      var e1 = [p[c1] - p[a], p[c1 + 1] - p[a + 1], p[c1 + 2] - p[a + 2]];
      var e2 = [p[c2] - p[a], p[c2 + 1] - p[a + 1], p[c2 + 2] - p[a + 2]];
      var f = v3cross(e1, e2);
      var nn = [n[a] + n[c1] + n[c2], n[a + 1] + n[c1 + 1] + n[c2 + 1],
                n[a + 2] + n[c1 + 2] + n[c2 + 2]];
      if (v3dot(f, nn) < 0) {
        var swap = idx[t + 1]; idx[t + 1] = idx[t + 2]; idx[t + 2] = swap;
      }
    }
    var lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
    for (t = 0; t < p.length; t += 3) {
      for (var k = 0; k < 3; k++) {
        if (p[t + k] < lo[k]) lo[k] = p[t + k];
        if (p[t + k] > hi[k]) hi[k] = p[t + k];
      }
    }
    var size = [Math.max(1e-4, hi[0] - lo[0]), Math.max(1e-4, hi[1] - lo[1]),
                Math.max(1e-4, hi[2] - lo[2])];
    var mid = [(hi[0] + lo[0]) / 2, (hi[1] + lo[1]) / 2, (hi[2] + lo[2]) / 2];
    var out = new Float32Array(p.length);
    for (t = 0; t < p.length; t += 3) {
      out[t] = (p[t] - mid[0]) / size[0];
      out[t + 1] = (p[t + 1] - mid[1]) / size[1];
      out[t + 2] = (p[t + 2] - mid[2]) / size[2];
    }
    return {
      centre: mid,
      mesh: {
        positions: out,
        normals: new Float32Array(n),
        uvs: new Float32Array(b.u),
        indices: (p.length / 3 > 65535) ? new Uint32Array(idx) : new Uint16Array(idx)
      },
      size: size
    };
  }

  /* Re-emit an indexed mesh with one vertex per corner and face normals, for
     shapes that should read as cut rather than moulded (a gem). */
  function facet(b) {
    var out = new Builder();
    for (var t = 0; t < b.i.length; t += 3) {
      var ids = [b.i[t], b.i[t + 1], b.i[t + 2]];
      var pts = ids.map(function (id) {
        return [b.p[id * 3], b.p[id * 3 + 1], b.p[id * 3 + 2]];
      });
      var fn = v3norm(v3cross(v3sub(pts[1], pts[0]), v3sub(pts[2], pts[0])));
      // keep the facet facing the way the smooth normals said it did
      var avg = [0, 0, 0];
      ids.forEach(function (id) {
        avg[0] += b.n[id * 3]; avg[1] += b.n[id * 3 + 1]; avg[2] += b.n[id * 3 + 2];
      });
      if (v3dot(fn, avg) < 0) fn = [-fn[0], -fn[1], -fn[2]];
      var base = out.p.length / 3;
      for (var k = 0; k < 3; k++) {
        out.vert(pts[k], fn, [b.u[ids[k] * 2], b.u[ids[k] * 2 + 1]]);
      }
      out.tri(base, base + 1, base + 2);
    }
    return out;
  }

  // --------------------------------------------------------------- lathe
  /* Spin a profile round the Y axis.

     ``profile`` is a list of [r, y] (or [r, y, 1] to crease there) walked
     so that the outside of the surface is on the RIGHT of the direction of
     travel, r to the right and y up: up the outside of a dome, or round a
     closed cross-section anticlockwise.  An open profile is capped wherever
     it ends off the axis.

     opts.segs      points round a ring (default 28)
     opts.ribs      number of ribs pressed into the surface (a pumpkin's 8)
     opts.ribDepth  how deep, as a fraction of the radius
     opts.facets    flat-shade every triangle (a cut gem)
     opts.capTop / opts.capBottom   force a cap on or off */
  function lathe(profile, opts) {
    opts = opts || {};
    var segs = opts.segs || 28;
    var ribs = opts.ribs || 0;
    var ribDepth = opts.ribDepth || 0;
    var b = new Builder();

    // Expand the profile into rows, each with an outward 2D normal; a crease
    // becomes two rows at one point with the normal of each side.
    var pts = profile.map(function (q) { return { r: q[0], y: q[1], crease: !!q[2] }; });
    function segNormal(a, c) {
      var dr = c.r - a.r, dy = c.y - a.y;
      var l = Math.hypot(dr, dy) || 1;
      return [dy / l, -dr / l];
    }
    var closed = pts.length > 2 && Math.abs(pts[0].r - pts[pts.length - 1].r) < 1e-6 &&
      Math.abs(pts[0].y - pts[pts.length - 1].y) < 1e-6;
    var rows = [];
    for (var k = 0; k < pts.length; k++) {
      var prev = k > 0 ? pts[k - 1] : (closed ? pts[pts.length - 2] : null);
      var next = k < pts.length - 1 ? pts[k + 1] : (closed ? pts[1] : null);
      var nIn = prev ? segNormal(prev, pts[k]) : null;
      var nOut = next ? segNormal(pts[k], next) : null;
      if (pts[k].crease && nIn && nOut) {
        rows.push({ r: pts[k].r, y: pts[k].y, n: nIn });
        rows.push({ r: pts[k].r, y: pts[k].y, n: nOut });
      } else {
        var nr = (nIn ? nIn[0] : 0) + (nOut ? nOut[0] : 0);
        var ny = (nIn ? nIn[1] : 0) + (nOut ? nOut[1] : 0);
        var l = Math.hypot(nr, ny) || 1;
        rows.push({ r: pts[k].r, y: pts[k].y, n: [nr / l, ny / l] });
      }
    }
    var ylo = Infinity, yhi = -Infinity;
    rows.forEach(function (row) { ylo = Math.min(ylo, row.y); yhi = Math.max(yhi, row.y); });
    var yspan = Math.max(1e-6, yhi - ylo);

    function ribAt(theta) {
      if (!ribs) return 1;
      // valleys between rounded lobes: 1 at a lobe's crest, 1-depth in a seam
      var c = Math.abs(Math.cos(theta * ribs * 0.5));
      return 1 - ribDepth * (1 - Math.pow(c, 0.6));
    }
    function ribSlope(theta) {
      var h = 1e-3;
      return (ribAt(theta + h) - ribAt(theta - h)) / (2 * h);
    }

    var cols = segs + 1;
    var start = 0;
    rows.forEach(function (row, ri) {
      for (var s = 0; s <= segs; s++) {
        var th = (s / segs) * TAU;
        var f = ribAt(th);
        var rr = row.r * f;
        var cs = Math.cos(th), sn = Math.sin(th);
        var pos = [rr * cs, row.y, rr * sn];
        // the profile normal turned to this angle, then leaned along the
        // ring by however steeply the rib slopes here
        var nr = row.n[0], ny = row.n[1];
        var normal = [nr * cs, ny, nr * sn];
        if (ribs && row.r > 1e-5) {
          var slope = ribSlope(th) / Math.max(1e-3, f);
          var tangent = [-sn, 0, cs];
          normal = v3norm([normal[0] - tangent[0] * slope * nr,
                           normal[1],
                           normal[2] - tangent[2] * slope * nr]);
        }
        b.vert(pos, normal, [s / segs, (row.y - ylo) / yspan]);
      }
      if (ri > 0) {
        var a0 = start + (ri - 1) * cols, a1 = start + ri * cols;
        for (var q = 0; q < segs; q++) {
          b.quad(a0 + q, a0 + q + 1, a1 + q + 1, a1 + q);
        }
      }
    });

    function cap(row, up) {
      if (row.r < 1e-5) return;
      var centre = b.vert([0, row.y, 0], [0, up ? 1 : -1, 0], [0.5, 0.5]);
      var first = b.p.length / 3;
      for (var s = 0; s <= segs; s++) {
        var th = (s / segs) * TAU;
        var rr = row.r * ribAt(th);
        b.vert([rr * Math.cos(th), row.y, rr * Math.sin(th)], [0, up ? 1 : -1, 0],
               [0.5 + Math.cos(th) * 0.5, 0.5 + Math.sin(th) * 0.5]);
      }
      for (s = 0; s < segs; s++) b.tri(centre, first + s, first + s + 1);
    }
    if (!closed) {
      if (opts.capBottom !== false) cap(rows[0], false);
      if (opts.capTop !== false) cap(rows[rows.length - 1], true);
    }
    return opts.facets ? facet(b) : b;
  }

  // ------------------------------------------------------------- extrude
  function signedArea(poly) {
    var a = 0;
    for (var i = 0; i < poly.length; i++) {
      var p = poly[i], q = poly[(i + 1) % poly.length];
      a += p[0] * q[1] - q[0] * p[1];
    }
    return a / 2;
  }

  /* Ear clipping, for a simple polygon (concave is fine) wound
     anticlockwise.  Returns triangles as index triples. */
  function triangulate(poly) {
    var n = poly.length;
    var idx = [];
    for (var i = 0; i < n; i++) idx.push(i);
    var out = [];
    function cross(o, a, b) {
      return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    }
    function inside(p, a, b, c) {
      var c1 = cross(a, b, p), c2 = cross(b, c, p), c3 = cross(c, a, p);
      return c1 >= -1e-12 && c2 >= -1e-12 && c3 >= -1e-12;
    }
    var guard = 0;
    while (idx.length > 3 && guard++ < 10000) {
      var clipped = false;
      for (var k = 0; k < idx.length; k++) {
        var ia = idx[(k + idx.length - 1) % idx.length];
        var ib = idx[k];
        var ic = idx[(k + 1) % idx.length];
        var a = poly[ia], bb = poly[ib], c = poly[ic];
        if (cross(a, bb, c) <= 1e-12) continue;          // reflex: not an ear
        var ok = true;
        for (var m = 0; m < idx.length && ok; m++) {
          var im = idx[m];
          if (im === ia || im === ib || im === ic) continue;
          if (inside(poly[im], a, bb, c)) ok = false;
        }
        if (!ok) continue;
        out.push([ia, ib, ic]);
        idx.splice(k, 1);
        clipped = true;
        break;
      }
      if (!clipped) {
        // degenerate leftovers: fan what remains rather than looping forever
        for (var f = 1; f < idx.length - 1; f++) out.push([idx[0], idx[f], idx[f + 1]]);
        return out;
      }
    }
    if (idx.length === 3) out.push([idx[0], idx[1], idx[2]]);
    return out;
  }

  /* Push an outline out along Z.

     ``outline`` is a list of [x, y]; either winding is accepted.
     opts.depth   thickness along Z (same units as the outline)
     opts.bevel   how far the bevel cuts in, on the face and down the side
     opts.smooth  edges meeting at less than this angle (radians) shade as one
                  curve rather than as a corner (default 0.6) */
  function extrude(outline, opts) {
    opts = opts || {};
    var poly = outline.map(function (q) { return [q[0], q[1]]; });
    if (signedArea(poly) < 0) poly.reverse();
    var n = poly.length;
    var depth = opts.depth === undefined ? 0.2 : opts.depth;
    var bevel = Math.min(opts.bevel === undefined ? depth * 0.3 : opts.bevel, depth * 0.49);
    var smooth = Math.cos(opts.smooth === undefined ? 0.6 : opts.smooth);
    var half = depth / 2;
    var inner = half - bevel;

    var minx = Infinity, maxx = -Infinity, miny = Infinity, maxy = -Infinity;
    poly.forEach(function (q) {
      minx = Math.min(minx, q[0]); maxx = Math.max(maxx, q[0]);
      miny = Math.min(miny, q[1]); maxy = Math.max(maxy, q[1]);
    });
    var w = Math.max(1e-6, maxx - minx), h = Math.max(1e-6, maxy - miny);
    function uv(x, y) { return [(x - minx) / w, (y - miny) / h]; }

    // outward normal of each edge (i -> i+1), anticlockwise polygon
    var edgeN = [];
    for (var i = 0; i < n; i++) {
      var a = poly[i], c = poly[(i + 1) % n];
      var dx = c[0] - a[0], dy = c[1] - a[1];
      var l = Math.hypot(dx, dy) || 1;
      edgeN.push([dy / l, -dx / l]);
    }
    // the inset outline the faces are cut to, along each corner's mitre
    var insetPoly = [];
    var vertSmooth = [];
    for (i = 0; i < n; i++) {
      var n1 = edgeN[(i + n - 1) % n], n2 = edgeN[i];
      var mx = n1[0] + n2[0], my = n1[1] + n2[1];
      var ml = Math.hypot(mx, my);
      var m = ml > 1e-6 ? [mx / ml, my / ml] : n2;
      var cosHalf = Math.max(0.3, m[0] * n2[0] + m[1] * n2[1]);
      var len = Math.min(bevel / cosHalf, bevel * 3);
      insetPoly.push([poly[i][0] - m[0] * len, poly[i][1] - m[1] * len]);
      vertSmooth.push(n1[0] * n2[0] + n1[1] * n2[1] > smooth ? m : null);
    }

    var b = new Builder();
    // front and back faces
    var tris = triangulate(insetPoly);
    [1, -1].forEach(function (side) {
      var base = b.p.length / 3;
      insetPoly.forEach(function (q) {
        b.vert([q[0], q[1], half * side], [0, 0, side], uv(q[0], q[1]));
      });
      tris.forEach(function (t3) { b.tri(base + t3[0], base + t3[1], base + t3[2]); });
    });

    // side walls and the two bevels, one quad per edge so a corner can stay
    // sharp while a curve stays smooth
    function sideNormal(vi, ei) {
      var s = vertSmooth[vi];
      return s ? s : edgeN[ei];
    }
    for (i = 0; i < n; i++) {
      var j = (i + 1) % n;
      var na = sideNormal(i, i), nb = sideNormal(j, i);
      var pa = poly[i], pb = poly[j];
      var qa = insetPoly[i], qb = insetPoly[j];
      // wall
      var w0 = b.vert([pa[0], pa[1], -inner], [na[0], na[1], 0], uv(pa[0], pa[1]));
      var w1 = b.vert([pb[0], pb[1], -inner], [nb[0], nb[1], 0], uv(pb[0], pb[1]));
      var w2 = b.vert([pb[0], pb[1], inner], [nb[0], nb[1], 0], uv(pb[0], pb[1]));
      var w3 = b.vert([pa[0], pa[1], inner], [na[0], na[1], 0], uv(pa[0], pa[1]));
      b.quad(w0, w1, w2, w3);
      // bevels: lean the normal half way between the wall and the face
      [1, -1].forEach(function (side) {
        var ba = v3norm([na[0], na[1], side]);
        var bb = v3norm([nb[0], nb[1], side]);
        var v0 = b.vert([pa[0], pa[1], inner * side], ba, uv(pa[0], pa[1]));
        var v1 = b.vert([pb[0], pb[1], inner * side], bb, uv(pb[0], pb[1]));
        var v2 = b.vert([qb[0], qb[1], half * side], bb, uv(qb[0], qb[1]));
        var v3 = b.vert([qa[0], qa[1], half * side], ba, uv(qa[0], qa[1]));
        b.quad(v0, v1, v2, v3);
      });
    }
    return b;
  }

  // --------------------------------------------------------------- sheet
  /* A thin solid: ``fn(u, v)`` gives the top surface for u, v in 0..1, and
     the underside is the same surface pushed ``thickness`` along its own
     normal.  Edges are closed with flat strips.  ``flip`` turns the surface
     over when the parameterisation runs the other way. */
  function sheet(fn, nu, nv, thickness, flip) {
    var b = new Builder();
    var grid = [], norms = [];
    var r, c;
    for (r = 0; r <= nv; r++) {
      var row = [];
      for (c = 0; c <= nu; c++) row.push(fn(c / nu, r / nv));
      grid.push(row);
    }
    function at(rr, cc) {
      rr = Math.max(0, Math.min(nv, rr)); cc = Math.max(0, Math.min(nu, cc));
      return grid[rr][cc];
    }
    for (r = 0; r <= nv; r++) {
      var nrow = [];
      for (c = 0; c <= nu; c++) {
        var du = v3sub(at(r, c + 1), at(r, c - 1));
        var dv = v3sub(at(r + 1, c), at(r - 1, c));
        var nn = v3norm(v3cross(du, dv));
        if (flip) nn = [-nn[0], -nn[1], -nn[2]];
        nrow.push(nn);
      }
      norms.push(nrow);
    }
    var top = [], bot = [];
    for (r = 0; r <= nv; r++) {
      for (c = 0; c <= nu; c++) {
        var p = grid[r][c], nm = norms[r][c];
        top.push(b.vert(p, nm, [c / nu, r / nv]));
      }
    }
    for (r = 0; r <= nv; r++) {
      for (c = 0; c <= nu; c++) {
        var p2 = grid[r][c], nm2 = norms[r][c];
        bot.push(b.vert([p2[0] - nm2[0] * thickness, p2[1] - nm2[1] * thickness,
                         p2[2] - nm2[2] * thickness],
                        [-nm2[0], -nm2[1], -nm2[2]], [c / nu, r / nv]));
      }
    }
    var cols = nu + 1;
    for (r = 0; r < nv; r++) {
      for (c = 0; c < nu; c++) {
        var a = r * cols + c;
        b.quad(top[a], top[a + 1], top[a + cols + 1], top[a + cols]);
        b.quad(bot[a], bot[a + cols], bot[a + cols + 1], bot[a + 1]);
      }
    }
    // The rim: walk the four edges and stitch top to bottom with flat
    // strips.  Each strip faces outwards across the parameter domain (off
    // the end of the bill, out of the hole in a brim), flattened onto the
    // surface, which is right for a ring as well as for a plate.
    function edge(list, outward) {
      for (var k = 0; k < list.length - 1; k++) {
        var i0 = list[k], i1 = list[k + 1];
        var t0 = grid[i0[0]][i0[1]], t1 = grid[i1[0]][i1[1]];
        var n0 = norms[i0[0]][i0[1]], n1 = norms[i1[0]][i1[1]];
        var b0 = [t0[0] - n0[0] * thickness, t0[1] - n0[1] * thickness, t0[2] - n0[2] * thickness];
        var b1 = [t1[0] - n1[0] * thickness, t1[1] - n1[1] * thickness, t1[2] - n1[2] * thickness];
        var o = outward(i0[0], i0[1]);
        var side = v3norm(v3sub(o, [n0[0] * v3dot(o, n0), n0[1] * v3dot(o, n0),
                                    n0[2] * v3dot(o, n0)]));
        var q0 = b.vert(t0, side, [0, 0]), q1 = b.vert(t1, side, [1, 0]);
        var q2 = b.vert(b1, side, [1, 1]), q3 = b.vert(b0, side, [0, 1]);
        b.quad(q0, q1, q2, q3);
      }
    }
    var e1 = [], e2 = [], e3 = [], e4 = [];
    for (c = 0; c <= nu; c++) { e1.push([0, c]); e2.push([nv, c]); }
    for (r = 0; r <= nv; r++) { e3.push([r, 0]); e4.push([r, nu]); }
    edge(e1, function (rr, cc) { return v3sub(at(rr, cc), at(rr + 1, cc)); });
    edge(e2, function (rr, cc) { return v3sub(at(rr, cc), at(rr - 1, cc)); });
    edge(e3, function (rr, cc) { return v3sub(at(rr, cc), at(rr, cc + 1)); });
    edge(e4, function (rr, cc) { return v3sub(at(rr, cc), at(rr, cc - 1)); });
    return b;
  }

  // ---------------------------------------------------------------- tube
  /* A tube along ``curve(t)`` (t 0..1) with radius ``radius(t)``, framed by
     parallel transport so it never twists.  It is closed at the base and
     runs to a point wherever the radius reaches zero. */
  function tube(curve, radius, rings, segs) {
    var b = new Builder();
    var pts = [], i, s;
    for (i = 0; i <= rings; i++) pts.push(curve(i / rings));
    var tangents = pts.map(function (p, k) {
      return v3norm(v3sub(pts[Math.min(rings, k + 1)], pts[Math.max(0, k - 1)]));
    });
    var normal = Math.abs(tangents[0][1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
    normal = v3norm(v3cross(v3cross(tangents[0], normal), tangents[0]));
    var frames = [];
    for (i = 0; i <= rings; i++) {
      if (i > 0) {
        var t = tangents[i];
        normal = v3norm(v3sub(normal, [t[0] * v3dot(normal, t), t[1] * v3dot(normal, t),
                                       t[2] * v3dot(normal, t)]));
      }
      frames.push({ n: normal, b: v3norm(v3cross(tangents[i], normal)) });
    }
    var cols = segs + 1;
    for (i = 0; i <= rings; i++) {
      var rr = radius(i / rings);
      for (s = 0; s <= segs; s++) {
        var th = (s / segs) * TAU;
        var cs = Math.cos(th), sn = Math.sin(th);
        var nn = [frames[i].n[0] * cs + frames[i].b[0] * sn,
                  frames[i].n[1] * cs + frames[i].b[1] * sn,
                  frames[i].n[2] * cs + frames[i].b[2] * sn];
        b.vert([pts[i][0] + nn[0] * rr, pts[i][1] + nn[1] * rr, pts[i][2] + nn[2] * rr],
               nn, [s / segs, i / rings]);
      }
      if (i > 0) {
        for (s = 0; s < segs; s++) {
          var a0 = (i - 1) * cols + s, a1 = i * cols + s;
          b.quad(a0, a0 + 1, a1 + 1, a1);
        }
      }
    }
    // base cap
    var base = b.vert(pts[0], [-tangents[0][0], -tangents[0][1], -tangents[0][2]], [0.5, 0.5]);
    var first = b.p.length / 3;
    var r0 = radius(0);
    for (s = 0; s <= segs; s++) {
      var a = (s / segs) * TAU;
      var dir = [frames[0].n[0] * Math.cos(a) + frames[0].b[0] * Math.sin(a),
                 frames[0].n[1] * Math.cos(a) + frames[0].b[1] * Math.sin(a),
                 frames[0].n[2] * Math.cos(a) + frames[0].b[2] * Math.sin(a)];
      b.vert([pts[0][0] + dir[0] * r0, pts[0][1] + dir[1] * r0, pts[0][2] + dir[2] * r0],
             [-tangents[0][0], -tangents[0][1], -tangents[0][2]], [0.5, 0.5]);
    }
    for (s = 0; s < segs; s++) b.tri(base, first + s + 1, first + s);
    var rEnd = radius(1);
    if (rEnd > 0.01) {
      var tEnd = tangents[rings];
      var tip = b.vert(pts[rings], tEnd, [0.5, 0.5]);
      var ring0 = b.p.length / 3;
      for (s = 0; s <= segs; s++) {
        var ae = (s / segs) * TAU;
        var de = [frames[rings].n[0] * Math.cos(ae) + frames[rings].b[0] * Math.sin(ae),
                  frames[rings].n[1] * Math.cos(ae) + frames[rings].b[1] * Math.sin(ae),
                  frames[rings].n[2] * Math.cos(ae) + frames[rings].b[2] * Math.sin(ae)];
        b.vert([pts[rings][0] + de[0] * rEnd, pts[rings][1] + de[1] * rEnd,
                pts[rings][2] + de[2] * rEnd], tEnd, [0.5, 0.5]);
      }
      for (s = 0; s < segs; s++) b.tri(tip, ring0 + s, ring0 + s + 1);
    }
    return b;
  }

  // ------------------------------------------------------------- outlines
  function circle(r, n, cx, cy) {
    var out = [];
    for (var i = 0; i < n; i++) {
      var a = (i / n) * TAU;
      out.push([(cx || 0) + Math.cos(a) * r, (cy || 0) + Math.sin(a) * r]);
    }
    return out;
  }

  function starOutline(points, outer, inner, rot) {
    var out = [];
    for (var i = 0; i < points * 2; i++) {
      var a = (rot === undefined ? Math.PI / 2 : rot) + (i / (points * 2)) * TAU;
      var r = i % 2 ? inner : outer;
      out.push([Math.cos(a) * r, Math.sin(a) * r]);
    }
    return out;
  }

  /* A smooth closed outline through control points (Catmull-Rom), so the
     organic shapes below can be described by a dozen numbers each. */
  function spline(points, per) {
    per = per || 6;
    var out = [], n = points.length;
    for (var i = 0; i < n; i++) {
      var p0 = points[(i + n - 1) % n], p1 = points[i];
      var p2 = points[(i + 1) % n], p3 = points[(i + 2) % n];
      for (var k = 0; k < per; k++) {
        var t = k / per, t2 = t * t, t3 = t2 * t;
        out.push([
          0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                 (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                 (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
          0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                 (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                 (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
        ]);
      }
    }
    return out;
  }

  // ------------------------------------------------------------ the set
  var BUILT = {};
  function add(name, builder) {
    var done = finish(builder);
    BUILT[name] = done.mesh;
    Shapes.native[name] = done.size;
    // where the unit cube's centre sits in the shape's own modelling space,
    // so a part can be placed by a point on the shape (a horn's root, the
    // inner edge of a bill) rather than by its bounding box
    Shapes.centre[name] = done.centre;
    if (global.Geometry && Geometry.register) Geometry.register(name, done.mesh);
  }

  // A dome with a flat base: caps, crowns, helmets, the top of a bell.
  (function () {
    var prof = [];
    for (var k = 0; k <= 12; k++) {
      var a = (k / 12) * Math.PI / 2;
      prof.push([Math.cos(a) * 0.5, Math.sin(a) * 0.5]);
    }
    add('hemi', lathe(prof, { segs: 32 }));
  })();

  // A baseball cap's crown: a dome that comes down into a short straight
  // band, so the cap sits ON the head instead of perching on it.
  (function () {
    var prof = [[0.5, 0], [0.5, 0.10]];
    for (var k = 1; k <= 12; k++) {
      var a = (k / 12) * Math.PI / 2;
      prof.push([Math.cos(a) * 0.5, 0.10 + Math.sin(a) * 0.42]);
    }
    add('capcrown', lathe(prof, { segs: 32 }));
  })();

  // A flat ring with a rolled outer lip (a top hat's or a bowler's brim).
  add('brim', lathe([[0.30, 0, 1], [0.47, 0.0, 1], [0.5, 0.06], [0.49, 0.13],
                     [0.44, 0.10], [0.30, 0.05, 1], [0.30, 0, 1]], { segs: 40 }));

  // A flat washer: hat bands, bezels, collars.
  add('ring', lathe([[0.36, 0, 1], [0.5, 0, 1], [0.5, 0.2, 1], [0.36, 0.2, 1],
                     [0.36, 0, 1]], { segs: 36 }));

  // A crown that widens towards the top, with a slight waist: top hats.
  add('flare', lathe([[0.44, 0], [0.43, 0.35], [0.45, 0.75], [0.5, 1.0, 1],
                      [0.0, 1.0]], { segs: 32 }));

  // A bell: witch hats' brim cone, lamps, a cowbell, a dinner bell.
  add('bell', lathe([[0.5, 0, 1], [0.44, 0.08], [0.30, 0.25], [0.24, 0.55],
                     [0.20, 0.85], [0.10, 1.0], [0.0, 1.02]], { segs: 32 }));

  // An open bowl with a thick rim: a cauldron, a pot, a mortarboard's cup.
  add('bowl', lathe([[0.0, 0.0], [0.30, 0.02], [0.46, 0.18], [0.5, 0.42],
                     [0.48, 0.58, 1], [0.44, 0.60, 1], [0.43, 0.42], [0.30, 0.16],
                     [0.0, 0.12]], { segs: 32, capTop: false, capBottom: false }));

  // A pumpkin: a squashed ribbed sphere with a dimple for the stem.
  (function () {
    // a dimple underneath, the swell of the body, and a dimple on top that
    // the stem stands in
    var prof = [[0.0, 0.07]];
    for (var k = 1; k <= 15; k++) {
      var a = -Math.PI / 2 + (k / 16) * Math.PI;
      prof.push([Math.cos(a) * 0.5, 0.40 + Math.sin(a) * 0.36]);
    }
    prof.push([0.05, 0.735]);
    prof.push([0.0, 0.70]);
    add('pumpkin', lathe(prof, { segs: 48, ribs: 8, ribDepth: 0.14 }));
  })();

  // A cut gem: flat-shaded crown, girdle and pavilion.
  add('gem', lathe([[0.0, 0.0], [0.5, 0.42, 1], [0.5, 0.48, 1], [0.32, 0.72, 1],
                    [0.0, 0.72]], { segs: 8, facets: true }));

  // A teardrop: flames, drips, candy, candle flames, a wizard's bauble.
  add('teardrop', lathe([[0.0, 0.0], [0.30, 0.06], [0.48, 0.22], [0.50, 0.34],
                         [0.40, 0.55], [0.18, 0.82], [0.0, 1.0]], { segs: 24 }));

  // A pill: handles, rungs, plush limbs.
  (function () {
    var prof = [];
    for (var k = 0; k <= 8; k++) {
      var a = -Math.PI / 2 + (k / 8) * Math.PI / 2;
      prof.push([Math.cos(a) * 0.5, 0.5 + Math.sin(a) * 0.5]);
    }
    for (k = 0; k <= 8; k++) {
      var b = (k / 8) * Math.PI / 2;
      prof.push([Math.cos(b) * 0.5, 2.5 + Math.sin(b) * 0.5]);
    }
    add('capsule', lathe(prof, { segs: 20 }));
  })();

  // A barrel stave shape: a cask, a potion bottle's belly, a lantern glass.
  add('cask', lathe([[0.0, 0.0], [0.42, 0.0, 1], [0.5, 0.5], [0.42, 1.0, 1],
                     [0.0, 1.0]], { segs: 28 }));

  // A coin: badges, medals, buttons, a key's bow.  Its front face (+Z) takes
  // a decal across its whole diameter.
  add('disc', extrude(circle(0.5, 48), { depth: 0.16, bevel: 0.035, smooth: 0.5 }));

  // A five-pointed star with a bevel.
  add('star', extrude(starOutline(5, 0.5, 0.215), { depth: 0.14, bevel: 0.035 }));

  // A heater shield.
  add('shield', extrude(spline([[0, 0.5], [0.44, 0.47], [0.46, 0.08], [0.32, -0.26],
                                [0, -0.5], [-0.32, -0.26], [-0.46, 0.08], [-0.44, 0.47]], 5)
                          .concat([]), { depth: 0.14, bevel: 0.04, smooth: 0.9 }));

  // A wing of three layered feathers, root at the left.
  add('wing', extrude([[-0.5, 0.12], [-0.30, 0.34], [0.05, 0.44], [0.50, 0.50],
                       [0.36, 0.22], [0.42, 0.20], [0.20, -0.04], [0.26, -0.08],
                       [0.02, -0.26], [0.06, -0.30], [-0.24, -0.40], [-0.5, -0.18]],
                      { depth: 0.08, bevel: 0.025, smooth: 0.35 }));

  // A scythe's crescent blade, edge along the bottom, tang at the left.
  add('blade', extrude(spline([[-0.5, 0.08], [-0.40, 0.20], [-0.10, 0.30], [0.22, 0.24],
                               [0.44, 0.05], [0.5, -0.20], [0.36, -0.06], [0.12, 0.08],
                               [-0.16, 0.10], [-0.42, -0.02]], 6),
                       { depth: 0.05, bevel: 0.018, smooth: 0.8 }));

  // A crescent moon.
  add('crescent', extrude(spline([[0.10, 0.5], [-0.24, 0.38], [-0.44, 0.0], [-0.24, -0.38],
                                  [0.10, -0.5], [-0.08, -0.26], [-0.16, 0.0],
                                  [-0.08, 0.26]], 6),
                          { depth: 0.12, bevel: 0.03, smooth: 0.9 }));

  // A bat with its wings spread.
  add('bat', extrude([[0, 0.12], [0.06, 0.24], [0.09, 0.14], [0.22, 0.20],
                      [0.40, 0.26], [0.5, 0.10], [0.42, 0.04], [0.36, -0.08],
                      [0.27, -0.02], [0.20, -0.12], [0.10, -0.04], [0.0, -0.20],
                      [-0.10, -0.04], [-0.20, -0.12], [-0.27, -0.02], [-0.36, -0.08],
                      [-0.42, 0.04], [-0.5, 0.10], [-0.40, 0.26], [-0.22, 0.20],
                      [-0.09, 0.14], [-0.06, 0.24]], { depth: 0.06, bevel: 0.015 }));

  // A leaf: laurel wreaths, a crown of leaves, a feather's vane.
  add('leaf', extrude(spline([[0, 0.5], [0.16, 0.2], [0.14, -0.2], [0, -0.5],
                              [-0.14, -0.2], [-0.16, 0.2]], 6),
                      { depth: 0.05, bevel: 0.015, smooth: 0.9 }));

  // A plume feather, the quill at the bottom.
  add('feather', extrude(spline([[0.0, 0.5], [0.12, 0.30], [0.16, 0.0], [0.10, -0.30],
                                 [0.02, -0.5], [-0.02, -0.5], [-0.09, -0.22],
                                 [-0.15, 0.06], [-0.08, 0.34]], 6),
                         { depth: 0.04, bevel: 0.012, smooth: 0.9 }));

  // A flame licking upwards.
  add('flame', extrude(spline([[0.0, 0.5], [0.10, 0.20], [0.24, 0.12], [0.30, -0.18],
                               [0.16, -0.46], [-0.16, -0.46], [-0.30, -0.18],
                               [-0.20, 0.02], [-0.08, -0.02], [-0.10, 0.22]], 6),
                       { depth: 0.12, bevel: 0.03, smooth: 0.9 }));

  // A cartoon bone: a shaft with two round knobs at each end.  The outline
  // walks anticlockwise: along the underside, round the right-hand knobs,
  // back along the top and round the left-hand ones.
  (function () {
    var R = 0.12, CX = 0.38, CY = 0.10, SHAFT = 0.07;
    var join = Math.asin(SHAFT - CY < 0 ? (CY - SHAFT) / R : 0);      // 0.2527
    var pinch = Math.atan2(CY, Math.sqrt(R * R - CY * CY));          // 0.9851
    var right = [];
    function arc(cy, from, to) {
      for (var k = 0; k <= 8; k++) {
        var a = from + (to - from) * (k / 8);
        right.push([CX + Math.cos(a) * R, cy + Math.sin(a) * R]);
      }
    }
    arc(-CY, Math.PI - join, TAU + pinch);     // lower knob: under and round
    arc(CY, -pinch, Math.PI + join);           // upper knob: round and over
    var left = right.map(function (q) { return [-q[0], q[1]]; }).reverse();
    add('bone', extrude(right.concat(left), { depth: 0.12, bevel: 0.03, smooth: 0.9 }));
  })();

  // Candy corn: a rounded triangle.
  add('candycorn', extrude(spline([[0, 0.5], [0.22, 0.05], [0.30, -0.38], [0.0, -0.5],
                                   [-0.30, -0.38], [-0.22, 0.05]], 6),
                           { depth: 0.24, bevel: 0.08, smooth: 1.1 }));

  // A ribbon tail with the V cut out of its end (badges, rosettes).
  add('ribbon', extrude([[-0.5, 0.5], [0.5, 0.5], [0.5, -0.5], [0.0, -0.22],
                         [-0.5, -0.5]], { depth: 0.05, bevel: 0.012 }));

  // A rank chevron.
  add('chevron', extrude([[-0.5, 0.0], [0.0, 0.5], [0.5, 0.0], [0.5, -0.32],
                          [0.0, 0.18], [-0.5, -0.32]], { depth: 0.12, bevel: 0.03 }));

  // A cog with twelve teeth.
  (function () {
    var pts = [];
    var teeth = 12;
    for (var k = 0; k < teeth; k++) {
      var a0 = (k / teeth) * TAU;
      var step = TAU / teeth;
      pts.push([Math.cos(a0) * 0.40, Math.sin(a0) * 0.40]);
      pts.push([Math.cos(a0 + step * 0.18) * 0.5, Math.sin(a0 + step * 0.18) * 0.5]);
      pts.push([Math.cos(a0 + step * 0.48) * 0.5, Math.sin(a0 + step * 0.48) * 0.5]);
      pts.push([Math.cos(a0 + step * 0.66) * 0.40, Math.sin(a0 + step * 0.66) * 0.40]);
    }
    add('cog', extrude(pts, { depth: 0.14, bevel: 0.03 }));
  })();

  // A heart (valentine boxes, health pickups, a lifeline badge).
  add('heart', extrude(spline([[0, 0.24], [0.16, 0.46], [0.42, 0.40], [0.48, 0.14],
                               [0.30, -0.18], [0.0, -0.5], [-0.30, -0.18], [-0.48, 0.14],
                               [-0.42, 0.40], [-0.16, 0.46]], 6),
                       { depth: 0.16, bevel: 0.04, smooth: 1.0 }));

  // A cap's bill: an arc of the crown's edge carried forward and bent down
  // at the sides.  Attach it with its inner edge on a crown of radius 0.5.
  add('visor', sheet(function (u, v) {
    var th = (u - 0.5) * 2 * 1.22;                       // +-70 degrees
    var reach = 0.5 + 0.48 * Math.pow(Math.max(0, Math.cos(th * 1.28)), 0.7);
    var d = 0.5 + (reach - 0.5) * v;
    var droop = -0.10 * Math.pow(v, 1.4) - 0.16 * Math.pow(Math.sin(th), 2) * v;
    return [Math.sin(th) * d, droop, Math.cos(th) * d];
  }, 24, 8, 0.045, true));

  // A short peak (a hard hat's, a fisherman's cap's): the same attachment as
  // the visor, a third of the reach and barely any droop.
  add('peak', sheet(function (u, v) {
    var th = (u - 0.5) * 2 * 1.10;
    var reach = 0.5 + 0.22 * Math.pow(Math.max(0, Math.cos(th * 1.4)), 0.6);
    var d = 0.5 + (reach - 0.5) * v;
    var droop = -0.05 * Math.pow(v, 1.3) - 0.05 * Math.pow(Math.sin(th), 2) * v;
    return [Math.sin(th) * d, droop, Math.cos(th) * d];
  }, 22, 6, 0.04, true));

  // A twin-bladed propeller, centred on its hub, blades swept like an S.
  add('prop', extrude([[0.0, 0.07], [0.20, 0.10], [0.42, 0.13], [0.5, 0.06],
                       [0.46, -0.02], [0.22, -0.04], [0.0, -0.07], [-0.20, -0.10],
                       [-0.42, -0.13], [-0.5, -0.06], [-0.46, 0.02], [-0.22, 0.04]],
                      { depth: 0.03, bevel: 0.01, smooth: 0.5 }));

  // A carved triangle: a jack-o'-lantern's eye or nose.
  add('tri', extrude([[0.0, 0.5], [0.5, -0.4], [-0.5, -0.4]], { depth: 0.12, bevel: 0.03 }));

  // A jack-o'-lantern's jagged grin, teeth and all.
  add('grin', extrude([[-0.5, 0.18], [-0.30, 0.06], [-0.18, 0.16], [-0.06, 0.02],
                       [0.06, 0.16], [0.18, 0.02], [0.30, 0.14], [0.5, 0.18],
                       [0.40, -0.06], [0.22, -0.20], [0.12, -0.08], [0.0, -0.24],
                       [-0.12, -0.08], [-0.22, -0.20], [-0.40, -0.06]],
                      { depth: 0.12, bevel: 0.025 }));

  // A vampire's stand-up collar: an open ring round the back of the neck
  // that flares outwards as it rises, its two front tips standing tallest.
  add('collar', sheet(function (u, v) {
    var th = Math.PI + (u - 0.5) * 2 * 2.05;          // the back, +-117 degrees
    var front = Math.pow(Math.abs(u - 0.5) * 2, 3);    // 0 at the back, 1 at a tip
    var h = v * (0.55 + 0.35 * front);
    var r = 0.5 + 0.30 * v * v;
    return [Math.sin(th) * r, h, Math.cos(th) * r];
  }, 36, 8, 0.035, false));

  /* Hair shells: one surface hugging the skull, cut along a hairline that is
     high at the brow, lower over the ears and lowest at the nape.  The skull
     is a superellipsoid a hair bigger than the head (whose own corners are
     rounded the same way), so the shell sits ON the head all the way round
     instead of the head's corners poking through, and a style is volume
     added on top of a shell rather than slabs stuck to the sides.  Four cut
     lengths; all are authored in head units (the head is 1 x 1 x 1), centred
     on the middle of the head. */
  function hairShell(front, side, back) {
    var a = 0.535, bb = 0.535, c = 0.545, e = 0.42;
    function f(w, k) { return (w < 0 ? -1 : 1) * Math.pow(Math.abs(w), k); }
    function hairline(phi) {
      var cf = Math.cos(phi);
      var wf = Math.pow(Math.max(0, cf), 1.6), wb = Math.pow(Math.max(0, -cf), 1.6);
      return side + (front - side) * wf + (back - side) * wb;
    }
    return sheet(function (u, v) {
      var phi = u * TAU;                       // 0 at the face, turning to +X
      var hl = Math.max(-0.999, Math.min(0.999, hairline(phi) / bb));
      var latMin = Math.asin(Math.max(-1, Math.min(1, f(hl, 1 / e))));
      var lat = Math.PI / 2 - (Math.PI / 2 - latMin) * v;
      var cl = Math.cos(lat), sl = Math.sin(lat);
      return [a * f(cl, e) * f(Math.sin(phi), e), bb * f(sl, e),
              c * f(cl, e) * f(Math.cos(phi), e)];
    }, 56, 14, 0.035, true);
  }
  add('hairshort', hairShell(0.30, 0.08, -0.18));
  add('hairmid', hairShell(0.30, -0.06, -0.34));
  add('hairbob', hairShell(0.32, -0.40, -0.44));
  add('hairlong', hairShell(0.30, -0.30, -0.52));

  // A cowboy brim: an annulus whose sides curl up and whose front and back
  // dip a little.  The crown sits in the hole (inner radius 0.27).
  add('cowbrim', sheet(function (u, v) {
    var th = u * TAU;
    var r = 0.27 + 0.23 * v;
    var side = Math.pow(Math.abs(Math.sin(th)), 2.2);
    var lift = v * v * (0.22 * side - 0.05 * (1 - side));
    return [Math.cos(th) * r, lift, Math.sin(th) * r * 0.92];
  }, 48, 6, 0.035, false));

  // A tricorn's brim: three corners turned up hard.
  add('tricorn', sheet(function (u, v) {
    var th = u * TAU;
    var r = 0.26 + 0.24 * v;
    var lobes = Math.pow(Math.max(0, Math.cos(1.5 * (th - Math.PI / 2))), 1.6);
    var lift = v * v * (0.10 + 0.30 * (1 - lobes));
    return [Math.cos(th) * r, lift, Math.sin(th) * r];
  }, 54, 6, 0.04, false));

  // A cape hanging in folds from a straight top edge.
  add('cape', sheet(function (u, v) {
    var x = (u - 0.5) * (1 + v * 0.3);
    var fold = Math.sin(u * TAU * 2.5) * 0.04 * (0.3 + v);
    var sweep = -0.12 * v * v;                          // hangs away behind
    return [x, -v * 1.4, fold + sweep];
  }, 30, 12, 0.03, true));

  // A horn: a cone bent through a quarter turn towards +X.
  add('horn', tube(function (t) {
    var a = t * Math.PI * 0.42;
    return [0.5 - Math.cos(a) * 0.5, Math.sin(a) * 0.6, 0];
  }, function (t) { return 0.13 * Math.pow(1 - t, 0.85) + 0.004; }, 18, 14));

  // A crook: the floppy tip of a witch's hat, curling right round.
  add('hook', tube(function (t) {
    var a = t * Math.PI * 1.15;
    var r = 0.5 - t * 0.22;
    return [Math.sin(a) * r * 0.9, (1 - Math.cos(a)) * r * 0.5 + t * 0.35, 0];
  }, function (t) { return 0.18 * Math.pow(1 - t, 0.9) + 0.008; }, 22, 14));

  // Half a ring standing up: handles, headbands, a lantern's bail.
  add('arch', tube(function (t) {
    var a = t * Math.PI;
    return [-Math.cos(a) * 0.5, Math.sin(a) * 0.5, 0];
  }, function () { return 0.06; }, 20, 10));

  /* ================================================== the holiday shapes
     The event crates (app/models/holidays/) brought a whole year of
     occasions with them -- New Year, St. Patrick's Day, Easter, the Fourth
     of July, Halloween and Christmas -- and each one has silhouettes of its
     own that boxes and domes cannot fake: an egg, a shamrock, a holly leaf,
     a snowflake, a firework rocket, a flag in the wind, a leprechaun's
     beard.  Same rules as everything above: every mesh normalised into the
     unit cube, its native size and centre recorded so app/models/modeling.py
     can place a point on it (``python3 tools/shapes_table.py`` rewrites the
     Python copy of those numbers). */

  /* An egg: fuller at the bottom than the top, the way a real one sits. */
  function eggProfile(n) {
    var prof = [[0, 0]];
    for (var k = 1; k < n; k++) {
      var a = -Math.PI / 2 + (k / n) * Math.PI;
      var y = 0.5 + Math.sin(a) * 0.5;
      // the top narrows: a hair of taper on an ellipse is what reads as egg
      var r = Math.cos(a) * 0.5 * (1.0 - 0.16 * y);
      prof.push([r, y * 1.30]);
    }
    prof.push([0, 1.30]);
    return prof;
  }
  add('egg', lathe(eggProfile(18), { segs: 32 }));

  /* The bottom of a hatched egg: a shell cup whose rim is a jagged crack.
     A sheet rather than a lathe, so the rim can zig-zag round the cup. */
  add('crackedshell', sheet(function (u, v) {
    var th = u * TAU;
    var zig = Math.abs(((u * 9) % 1) - 0.5) * 2;            // 0..1 saw tooth
    var rim = 0.52 + 0.16 * zig;                            // crack height, 0..1 of the egg
    var t = v * rim;                                        // up the egg from the bottom
    var a = -Math.PI / 2 + t * Math.PI;
    var y = 0.5 + Math.sin(a) * 0.5;
    var r = Math.max(0.001, Math.cos(a) * 0.5 * (1.0 - 0.16 * y));
    return [Math.cos(th) * r, y * 1.30, Math.sin(th) * r];
  }, 54, 10, 0.03, true));

  /* The lobes of a clover: ``leaves`` hearts round the middle, each with the
     notch at its tip, and a stem out of the bottom. */
  function clover(leaves, notch, stem) {
    var out = [];
    var steps = 26 * leaves;
    var half = Math.PI / leaves;
    var start = -Math.PI / 2;                     // the stem points down
    for (var i = 0; i < steps; i++) {
      var th = start + (i / steps) * TAU;
      // angle measured from the nearest leaf's middle (leaves sit between
      // the stem and its opposite)
      var rel = (((th - start) % (2 * half)) + 2 * half) % (2 * half) - half;
      var lobe = Math.pow(Math.max(0, Math.cos(rel * leaves / 2)), 0.55);
      var dip = 1 - notch * Math.exp(-Math.pow(rel / 0.10, 2));
      var r = 0.5 * lobe * dip;
      if (i === 0 && stem) {
        out.push([-0.035, -0.04], [-0.05, -0.5], [0.02, -0.5], [0.035, -0.04]);
        continue;
      }
      out.push([Math.cos(th) * Math.max(r, 0.035), Math.sin(th) * Math.max(r, 0.035)]);
    }
    return out;
  }
  add('shamrock', extrude(clover(3, 0.22, true), { depth: 0.10, bevel: 0.03, smooth: 0.9 }));
  add('clover4', extrude(clover(4, 0.20, true), { depth: 0.10, bevel: 0.03, smooth: 0.9 }));

  /* A holly leaf: long, waxy, five spines a side. */
  (function () {
    var top = [], bottom = [];
    var spines = 5;
    for (var k = 0; k <= spines * 2; k++) {
      var x = -0.5 + k / (spines * 2);
      var env = 0.20 * Math.sqrt(Math.max(0, 1 - Math.pow(x * 2, 2)));
      var w = (k % 2) ? env * 0.62 : env + 0.05;
      if (k === 0 || k === spines * 2) w = 0;
      top.push([x, w]);
      bottom.push([x, -w]);
    }
    add('holly', extrude(top.concat(bottom.reverse().slice(1, -1)),
                         { depth: 0.05, bevel: 0.015, smooth: 0.4 }));
  })();

  /* A six-armed snowflake, each arm with a pair of branches. */
  (function () {
    var pts = [];
    var arm = [[0.10, 0.045], [0.27, 0.045], [0.37, 0.15], [0.39, 0.12], [0.32, 0.045],
               [0.50, 0.03], [0.50, -0.03], [0.32, -0.045], [0.39, -0.12], [0.37, -0.15],
               [0.27, -0.045], [0.10, -0.045]].reverse();
    for (var k = 0; k < 6; k++) {
      var a = Math.PI / 2 + k * TAU / 6;
      var c = Math.cos(a), s = Math.sin(a);
      arm.forEach(function (q) { pts.push([q[0] * c - q[1] * s, q[0] * s + q[1] * c]); });
    }
    add('snowflake', extrude(pts, { depth: 0.06, bevel: 0.015, smooth: 0.3 }));
  })();

  // A rabbit's ear: long, rounded, a little wider below the tip.
  add('bunnyear', extrude(spline([[0, 0.5], [0.15, 0.40], [0.20, 0.08], [0.16, -0.30],
                                  [0.10, -0.5], [-0.10, -0.5], [-0.16, -0.30],
                                  [-0.20, 0.08], [-0.15, 0.40]], 6),
                          { depth: 0.08, bevel: 0.025, smooth: 0.9 }));

  // A gingerbread man, arms out.
  add('gingerman', extrude(spline([[0, 0.5], [0.12, 0.46], [0.14, 0.33], [0.09, 0.25],
                                   [0.30, 0.23], [0.40, 0.14], [0.33, 0.05], [0.13, 0.07],
                                   [0.15, -0.14], [0.29, -0.43], [0.20, -0.5], [0.09, -0.44],
                                   [0, -0.26], [-0.09, -0.44], [-0.20, -0.5], [-0.29, -0.43],
                                   [-0.15, -0.14], [-0.13, 0.07], [-0.33, 0.05],
                                   [-0.40, 0.14], [-0.30, 0.23], [-0.09, 0.25], [-0.14, 0.33],
                                   [-0.12, 0.46]], 4),
                           { depth: 0.12, bevel: 0.035, smooth: 1.0 }));

  /* A flag in a breeze, its pole edge at the left (x -0.5).  The face takes
     a decal across its whole width through its own UVs. */
  add('flag', sheet(function (u, v) {
    var x = u - 0.5;
    var wave = Math.sin(u * TAU * 1.15 - 0.4) * 0.07 * Math.pow(u, 0.8);
    return [x, (v - 0.5) * 0.64 - u * 0.04, wave];
  }, 24, 8, 0.02, false));

  // A horseshoe, open at the bottom, nail holes left to a decal.
  add('horseshoe', tube(function (t) {
    var a = (-0.30 + t * 1.60) * Math.PI;
    var r = 0.40 + 0.05 * Math.pow(Math.abs(t - 0.5) * 2, 3);
    return [Math.cos(a) * r, Math.sin(a) * r, 0];
  }, function () { return 0.09; }, 30, 12));

  // A coil: a slinky, a streamer, a curly tail, a corkscrew curl of hair.
  add('spiral', tube(function (t) {
    var a = t * TAU * 4.5;
    return [Math.cos(a) * 0.42, t * 1.0, Math.sin(a) * 0.42];
  }, function () { return 0.06; }, 140, 10));

  // A champagne flute: foot, stem and a tall bowl.
  add('flute', lathe([[0, 0], [0.30, 0, 1], [0.30, 0.03, 1], [0.05, 0.06], [0.035, 0.12],
                      [0.035, 0.42], [0.08, 0.48], [0.15, 0.58], [0.19, 0.78], [0.21, 1.0, 1],
                      [0, 1.0]], { segs: 28 }));

  // A carrot: a tapering root, ridged, round at the shoulder.
  add('carrot', lathe([[0, 0], [0.05, 0.08], [0.12, 0.35], [0.17, 0.70], [0.18, 0.86],
                       [0.14, 0.96], [0.06, 1.0], [0, 1.0]],
                      { segs: 24, ribs: 7, ribDepth: 0.06 }));

  // A mitten, thumb out to the left.
  add('mitten', extrude(spline([[-0.20, 0.50], [0.10, 0.50], [0.24, 0.36], [0.26, -0.08],
                                [0.22, -0.30], [0.22, -0.50], [-0.20, -0.50], [-0.22, -0.26],
                                [-0.24, -0.08], [-0.40, 0.02], [-0.44, 0.14], [-0.36, 0.20],
                                [-0.26, 0.14], [-0.26, 0.36]], 5),
                        { depth: 0.20, bevel: 0.07, smooth: 1.0 }));

  // A fir tree in three tiers, the way a child draws one.
  add('tree', lathe([[0, 0], [0.50, 0.02, 1], [0.14, 0.38, 1], [0.40, 0.33, 1],
                     [0.10, 0.66, 1], [0.28, 0.61, 1], [0, 1.0]], { segs: 24 }));

  // A firework rocket: nozzle, tube and a sharp nose.
  add('rocket', lathe([[0, 0], [0.10, 0, 1], [0.14, 0.10, 1], [0.14, 0.72, 1],
                       [0.10, 0.84], [0.04, 0.95], [0, 1.0]], { segs: 20 }));

  // A lightning bolt.
  add('bolt', extrude([[-0.10, 0.50], [0.22, 0.50], [0.06, 0.10], [0.24, 0.10],
                       [-0.18, -0.50], [-0.04, -0.06], [-0.22, -0.06]],
                      { depth: 0.10, bevel: 0.025 }));

  /* One loop of a gift bow: a flat ribbon band bent into a loop, its root
     at the origin and its far end out at x = 1.  Width runs along Z. */
  add('bowloop', sheet(function (u, v) {
    var a = u * TAU;
    var x = 0.5 - Math.cos(a) * 0.5;
    var y = Math.sin(a) * 0.28 * (0.6 + 0.4 * x);
    return [x, y, (v - 0.5) * 0.34];
  }, 32, 3, 0.03, true));

  // A Christmas stocking, toe to the right.
  add('stocking', extrude(spline([[-0.22, 0.50], [0.10, 0.50], [0.10, 0.02], [0.30, -0.12],
                                  [0.36, -0.30], [0.26, -0.46], [0.02, -0.50], [-0.18, -0.40],
                                  [-0.24, -0.20], [-0.22, 0.10]], 5),
                          { depth: 0.16, bevel: 0.05, smooth: 1.0 }));

  // A handlebar moustache, twirled at both ends.
  add('mustache', extrude(spline([[0, 0.10], [0.14, 0.18], [0.30, 0.10], [0.42, 0.14],
                                  [0.50, 0.30], [0.48, 0.06], [0.34, -0.06], [0.16, -0.06],
                                  [0, -0.02], [-0.16, -0.06], [-0.34, -0.06], [-0.48, 0.06],
                                  [-0.50, 0.30], [-0.42, 0.14], [-0.30, 0.10], [-0.14, 0.18]], 5),
                          { depth: 0.10, bevel: 0.035, smooth: 1.0 }));

  /* A full beard, flat behind where it lies on the jaw, rounded in front,
     with a parting for the mouth near the top. */
  add('beard', extrude(spline([[-0.50, 0.50], [-0.30, 0.40], [-0.10, 0.36], [0, 0.40],
                               [0.10, 0.36], [0.30, 0.40], [0.50, 0.50], [0.46, 0.10],
                               [0.30, -0.26], [0.10, -0.50], [0, -0.40], [-0.10, -0.50],
                               [-0.30, -0.26], [-0.46, 0.10]], 5),
                       { depth: 0.30, bevel: 0.12, smooth: 1.2 }));

  // A bow tie.
  add('bowtie', extrude(spline([[0, 0.10], [0.20, 0.30], [0.46, 0.38], [0.50, 0.0],
                                [0.46, -0.38], [0.20, -0.30], [0, -0.10], [-0.20, -0.30],
                                [-0.46, -0.38], [-0.50, 0.0], [-0.46, 0.38], [-0.20, 0.30]], 4),
                        { depth: 0.12, bevel: 0.04, smooth: 1.0 }));

  // A candy cane: a straight shaft and its crook, the crook to the right.
  add('cane', tube(function (t) {
    if (t < 0.68) return [0, (t / 0.68) * 0.80, 0];
    var a = ((t - 0.68) / 0.32) * Math.PI * 1.05;
    return [0.16 - Math.cos(a) * 0.16, 0.80 + Math.sin(a) * 0.16, 0];
  }, function () { return 0.06; }, 40, 12));

  // A hand bell: a flared mouth, a waist and a knob to hold it by.
  add('handbell', lathe([[0, 0], [0.50, 0, 1], [0.48, 0.07], [0.34, 0.20], [0.27, 0.45],
                         [0.24, 0.66], [0.14, 0.74], [0.07, 0.78], [0.06, 0.86], [0.10, 0.92],
                         [0.08, 0.99], [0, 1.0]], { segs: 28 }));

  // A masquerade mask: swept wings either side, the bridge of the nose cut out.
  add('mask', extrude(spline([[0, 0.20], [0.20, 0.30], [0.40, 0.34], [0.50, 0.48],
                              [0.48, 0.12], [0.36, -0.16], [0.18, -0.22], [0.06, -0.10],
                              [0, -0.02], [-0.06, -0.10], [-0.18, -0.22], [-0.36, -0.16],
                              [-0.48, 0.12], [-0.50, 0.48], [-0.40, 0.34], [-0.20, 0.30]], 5),
                      { depth: 0.08, bevel: 0.025, smooth: 1.0 }));

  // A party horn (and a trumpet's bell): a thin tube flaring at the top.
  add('trumpet', lathe([[0, 0], [0.07, 0.0, 1], [0.06, 0.50], [0.09, 0.74], [0.20, 0.90],
                        [0.50, 0.99, 1], [0.47, 1.0, 1], [0, 0.98]], { segs: 26 }));

  // A pinwheel: four curled blades round a pin.
  add('pinwheel', extrude((function () {
    var pts = [];
    for (var k = 0; k < 4; k++) {
      var a = k * TAU / 4;
      [[0.05, 0.0], [0.50, 0.04], [0.42, 0.22], [0.05, 0.05]].forEach(function (q) {
        var c = Math.cos(a), s = Math.sin(a);
        pts.push([q[0] * c - q[1] * s, q[0] * s + q[1] * c]);
      });
    }
    return pts;
  })(), { depth: 0.05, bevel: 0.015 }));

  // A four-pointed twinkle.
  add('sparkle', extrude(starOutline(4, 0.5, 0.11), { depth: 0.10, bevel: 0.03 }));

  /* A rainbow: a half ring of band standing in the XY plane, the bands run
     across its width (v), so a stripe decal printed through its UVs lies in
     arcs. */
  add('rainbowarc', sheet(function (u, v) {
    var a = u * Math.PI;
    var r = 0.30 + 0.20 * v;
    return [Math.cos(a) * r, Math.sin(a) * r, 0];
  }, 36, 6, 0.10, true));

  // A balloon, knot at the bottom.
  add('balloon', lathe([[0, 0], [0.06, 0.0, 1], [0.05, 0.05], [0.10, 0.10], [0.30, 0.24],
                       [0.46, 0.46], [0.50, 0.64], [0.44, 0.84], [0.26, 0.97], [0, 1.0]],
                      { segs: 28 }));

  // A ruff: a pleated ring collar.
  add('ruffle', sheet(function (u, v) {
    var a = u * TAU;
    var r = 0.30 + 0.20 * v;
    var pleat = Math.sin(u * TAU * 14) * 0.06 * v;
    return [Math.cos(a) * r, pleat, Math.sin(a) * r];
  }, 112, 4, 0.02, false));

  // A tentacle, curling at its tip.
  add('tentacle', tube(function (t) {
    var curl = Math.pow(t, 2.2);
    return [Math.sin(curl * Math.PI * 1.6) * 0.30 * t, t * 0.9 - curl * 0.12,
            Math.cos(curl * Math.PI * 1.6) * 0.06 - 0.06];
  }, function (t) { return 0.13 * Math.pow(1 - t, 0.8) + 0.008; }, 30, 12));

  // A sharp drop of ice, point down.
  add('icicle', lathe([[0, 0], [0.12, 0.40], [0.34, 0.80], [0.50, 0.96], [0.40, 1.0], [0, 1.0]],
                      { segs: 10, facets: true }));

  // A folding fan, pleated, its pin at the origin end (bottom).
  add('fan', sheet(function (u, v) {
    var a = (u - 0.5) * 2.2;
    var r = 0.10 + 0.40 * v;
    var pleat = (Math.abs(((u * 18) % 1) - 0.5) - 0.25) * 0.07 * v;
    return [Math.sin(a) * r, Math.cos(a) * r, pleat];
  }, 72, 6, 0.015, false));

  // A pointer: a clock hand, a sign, a compass needle.
  add('arrow', extrude([[0, 0.5], [0.22, 0.18], [0.07, 0.20], [0.07, -0.5], [-0.07, -0.5],
                        [-0.07, 0.20], [-0.22, 0.18]], { depth: 0.08, bevel: 0.02 }));

  // A five-petalled blossom.
  add('flower', extrude((function () {
    var pts = [];
    for (var i = 0; i < 80; i++) {
      var th = (i / 80) * TAU;
      var r = 0.5 * (0.42 + 0.58 * Math.pow(Math.abs(Math.cos(th * 2.5)), 0.7));
      pts.push([Math.cos(th + Math.PI / 2) * r, Math.sin(th + Math.PI / 2) * r]);
    }
    return pts;
  })(), { depth: 0.08, bevel: 0.025, smooth: 0.8 }));

  /* A cup of petals (a tulip, a crown of leaves): a bowl whose rim rises in
     five rounded points. */
  add('petalcup', sheet(function (u, v) {
    var th = u * TAU;
    var lobe = Math.pow(Math.abs(Math.cos(th * 2.5)), 0.6);
    var h = 0.62 + 0.38 * lobe;
    var y = v * h;
    var r = 0.22 + 0.28 * Math.sin(Math.min(1, y / 0.75) * Math.PI * 0.5);
    return [Math.cos(th) * r, y, Math.sin(th) * r];
  }, 60, 10, 0.03, true));

  // A skull, front on, for stickers and stencils that need a solid one.
  add('skullface', extrude(spline([[0, 0.5], [0.30, 0.44], [0.44, 0.20], [0.42, -0.06],
                                   [0.26, -0.18], [0.24, -0.44], [0.08, -0.5], [-0.08, -0.5],
                                   [-0.24, -0.44], [-0.26, -0.18], [-0.42, -0.06],
                                   [-0.44, 0.20], [-0.30, 0.44]], 5),
                           { depth: 0.14, bevel: 0.05, smooth: 1.0 }));

  /* A cloud: a row of puffs over a flat underside.  The top edge is the
     upper envelope of four circles, walked right to left, so the outline
     stays one simple loop however much the puffs overlap. */
  add('cloud', extrude((function () {
    var bumps = [[0.34, -0.04, 0.17], [0.13, 0.06, 0.23], [-0.12, 0.05, 0.21],
                 [-0.33, -0.04, 0.17]];
    var out = [[0.5, -0.18]];
    for (var i = 0; i <= 60; i++) {
      var x = 0.5 - i / 60;
      var y = -0.16;
      bumps.forEach(function (b) {
        var d = x - b[0];
        if (Math.abs(d) < b[2]) y = Math.max(y, b[1] + Math.sqrt(b[2] * b[2] - d * d));
      });
      out.push([x, y]);
    }
    out.push([-0.5, -0.18]);
    return out;
  })(), { depth: 0.30, bevel: 0.11, smooth: 1.2 }));

  // A cracker (the Christmas kind) and a firecracker: a tube with frilled ends.
  add('cracker', lathe([[0, 0], [0.30, 0.0, 1], [0.24, 0.06], [0.14, 0.20], [0.20, 0.24, 1],
                        [0.20, 0.76, 1], [0.14, 0.80], [0.24, 0.94], [0.30, 1.0, 1], [0, 1.0]],
                       { segs: 22, ribs: 10, ribDepth: 0.08 }));

  // A crown of points: a band whose top edge rises in seven spikes.
  add('spikecrown', sheet(function (u, v) {
    var th = u * TAU;
    var spike = Math.abs(((u * 7) % 1) - 0.5) * 2;           // 0 at a point
    var h = 0.40 + 0.60 * (1 - spike);
    return [Math.cos(th) * 0.5, v * h, Math.sin(th) * 0.5];
  }, 84, 8, 0.03, true));

  /* ---- St. Patrick's meshes (any the St. Patrick's events needed that were not here) */
  // A leprechaun's crown: a hat that narrows as it rises, flat on top --
  // the old capotain shape, not a top hat's waist and flare.
  add('sp_taper', lathe([[0.5, 0.0, 1], [0.475, 0.30], [0.44, 0.70], [0.42, 1.0, 1],
                         [0.0, 1.0]], { segs: 36 }));

  // @@ stpatricks shapes go above this line @@

  /* ---- Easter meshes (any the Easter events needed that were not here) */
  // @@ easter shapes go above this line @@

  /* ---- Fourth of July meshes (any the Fourth of July events needed that were not here) */
  // @@ july4 shapes go above this line @@

  /* ---- Christmas meshes (any the Christmas events needed that were not here) */
  // @@ christmas shapes go above this line @@

  Shapes.lathe = lathe;
  Shapes.extrude = extrude;
  Shapes.sheet = sheet;
  Shapes.tube = tube;
  Shapes.finish = finish;
  Shapes.spline = spline;
  Shapes.built = BUILT;
  Shapes.names = Object.keys(BUILT);

  global.Shapes = Shapes;
})(typeof window !== 'undefined' ? window : globalThis);
