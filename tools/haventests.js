#!/usr/bin/env node
/* The dome's town, checked headless (no browser, no server):

     node tools/haventests.js            # 6 towns of each size, 2 minutes each
     node tools/haventests.js 20 400     # 20 towns of each size, 400 s each

   static/js/family/haven.js is loaded into a stand-in window with a seeded
   Math.random, so every run is the same run.  Each town is built for the
   landing page's hero and for the sign-up page's panel (mirrored or not,
   every season) and checked as laid out: the sidewalks join up and keep
   clear of everything, every spot has a clear way in and out on its own side
   of the streets, every curb a kid waits at is on the sidewalk, and both
   cars' loops stay on the road.  Then it is run, and checked frame by frame:
   nobody walks into the fountain, a wall, a pond or a tree, no car touches
   a kid, the dog or the other car, nobody stays stuck, nobody waits at a curb
   for ever, nobody leaves the island, and two kids never stand in each other
   for long.  The two small domes (the wizard's and the comparison card's)
   are run too. */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');

var ROOT = path.join(__dirname, '..');
var TOWNS = parseInt(process.argv[2] || '6', 10), SECS = parseFloat(process.argv[3] || '120');
var passed = 0, failed = 0;
function check(name, ok, detail) {
  if (ok) { passed++; console.log('  PASS  ' + name); }
  else { failed++; console.log('  FAIL  ' + name + (detail !== undefined ? '  ' + (typeof detail === 'string' ? detail : JSON.stringify(detail)) : '')); }
}

/* haven.js in a stand-in window, with a Math.random that can be reseeded */
function load() {
  var M = Object.create(Math);
  M.seed = 1;
  M.random = function () {
    var t = (M.seed = (M.seed + 0x6D2B79F5) >>> 0);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  var win = {
    console: console, Math: M, Date: Date, JSON: JSON,
    location: { search: '' }, performance: { now: function () { return Date.now(); } },
    setTimeout: function () { return 0; }, clearTimeout: function () {},          // fireworks: not needed here
    sessionStorage: { getItem: function () { return null; }, setItem: function () {} },
    document: { readyState: 'complete', hidden: false, querySelectorAll: function () { return []; },
                getElementById: function () { return null; }, addEventListener: function () {} },
    CustomEvent: function (t, o) { this.type = t; this.detail = o && o.detail; },
    requestAnimationFrame: function () { return 0; }, cancelAnimationFrame: function () {}
  };
  win.window = win;
  vm.createContext(win);
  vm.runInContext(fs.readFileSync(path.join(ROOT, 'static/js/family/haven.js'), 'utf8'), win, { filename: 'haven.js' });
  return win;
}
function makeWorld(win, mode, seed, season) {
  var host = { getAttribute: function (k) { return k === 'data-seed' ? String(seed) : (k === 'data-season' ? season : null); },
               dispatchEvent: function () {}, classList: { add: function () {}, remove: function () {} }, clientWidth: 500, clientHeight: 500 };
  var w = new win.Haven.World(host, mode);
  w.renderer = { buildStatic: function () {}, setSky: function () {}, setAmbient: function () {}, sunColor: [1, 1, 1] };
  w.particles = null;
  w.generate();
  return w;
}

/* ------------------------------------------------------------- geometry */
function rectHas(o, x, z, pad) {
  var dx = x - o.x, dz = z - o.z, lx = dx * o.cs - dz * o.sn, lz = dx * o.sn + dz * o.cs;
  return Math.abs(lx) < o.hx + pad && Math.abs(lz) < o.hz + pad;
}
function inside(o, x, z, pad) {
  if (o.hole && rectHas(o.hole, x, z, 0)) return false;
  if (o.k === 'c') return Math.hypot(x - o.x, z - o.z) < o.r + pad;
  return rectHas(o, x, z, pad);
}
function depth(o, x, z, pad) {
  if (o.hole && rectHas(o.hole, x, z, 0)) return 0;
  if (o.k === 'c') return Math.max(0, o.r + pad - Math.hypot(x - o.x, z - o.z));
  var dx = x - o.x, dz = z - o.z, lx = dx * o.cs - dz * o.sn, lz = dx * o.sn + dz * o.cs;
  var px = o.hx + pad - Math.abs(lx), pz = o.hz + pad - Math.abs(lz);
  return px > 0 && pz > 0 ? Math.min(px, pz) : 0;
}
function where(w, x, z) { return '(' + (x * w.mir).toFixed(1) + ', ' + z.toFixed(1) + ')'; }
/* the first thing a walk along pts runs into, if any */
function hitAlong(w, pts, pad, own) {
  for (var i = 1; i < pts.length; i++) {
    var a = pts[i - 1], b = pts[i], n = Math.max(1, Math.ceil(Math.hypot(b.x - a.x, b.z - a.z) / 0.3));
    for (var j = 0; j <= n; j++) {
      var x = a.x + (b.x - a.x) * j / n, z = a.z + (b.z - a.z) * j / n;
      for (var k = 0; k < w.obst.length; k++) {
        var o = w.obst[k];
        if (own && own.indexOf(o) >= 0) continue;
        if (inside(o, x, z, pad)) return o.tag + ' at ' + where(w, x, z);
      }
    }
  }
  return '';
}
/* on the road, loosely: the car body may reach the road's very edge */
function onRoadLoose(w, x, z) {
  var T = w.town, ux = Math.abs(x), az = Math.abs(z), half = 3.5 + 0.05;
  if (Math.abs(ux - T.D) <= half && az <= T.zEnd) return true;
  return Math.abs(az - T.D) <= half && ux <= T.D + half;
}
function carCorners(c) {
  var cs = Math.cos(c.yaw), sn = Math.sin(c.yaw), out = [];
  [[-1, -1], [1, -1], [1, 1], [-1, 1]].forEach(function (q) { var lx = q[0] * 1.35, lz = q[1] * 2.6; out.push([c.x + lx * cs + lz * sn, c.z - lx * sn + lz * cs]); });
  return out;
}
/* the gap between two convex quads, 0 when they overlap */
function quadGap(A, B) {
  function within(P, Q) {
    var s = 0;
    for (var i = 0; i < 4; i++) { var a = Q[i], b = Q[(i + 1) % 4], c = (b[0] - a[0]) * (P[1] - a[1]) - (b[1] - a[1]) * (P[0] - a[0]); if (c > 0) s |= 1; else if (c < 0) s |= 2; }
    return s !== 3;
  }
  function seg(p, a, b) {
    var dx = b[0] - a[0], dz = b[1] - a[1], t = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / (dx * dx + dz * dz)));
    return Math.hypot(p[0] - a[0] - dx * t, p[1] - a[1] - dz * t);
  }
  for (var i = 0; i < 4; i++) if (within(A[i], B) || within(B[i], A)) return 0;
  var best = 1e9;
  for (i = 0; i < 4; i++) for (var j = 0; j < 4; j++) best = Math.min(best, seg(A[i], B[j], B[(j + 1) % 4]), seg(B[i], A[j], A[(j + 1) % 4]));
  return best;
}

/* ------------------------------------------------------- the layout */
function layoutProblems(w) {
  var out = [], i, j, hit;
  // the sidewalks join up
  var seen = { 0: 1 }, stack = [0];
  while (stack.length) { var u = stack.pop(); w.nodes[u].n.forEach(function (v) { if (!seen[v]) { seen[v] = 1; stack.push(v); } }); }
  if (Object.keys(seen).length !== w.nodes.length) out.push('the sidewalks are in ' + (w.nodes.length - Object.keys(seen).length + 1) + '+ pieces');
  // both lanes of every sidewalk keep clear of things
  for (i = 0; i < w.nodes.length; i++) {
    var a = w.nodes[i];
    for (j = 0; j < a.n.length; j++) {
      if (a.n[j] < i || w.edgeCross[i + '-' + a.n[j]]) continue;
      var b = w.nodes[a.n[j]], l = Math.hypot(b.x - a.x, b.z - a.z), rx = -(b.z - a.z) / l, rz = (b.x - a.x) / l;
      for (var side = -1; side <= 1; side += 2) {
        var off = 0.8 * side;
        hit = hitAlong(w, [{ x: a.x + rx * off, z: a.z + rz * off }, { x: b.x + rx * off, z: b.z + rz * off }], 0.85, null);
        if (hit) out.push('the sidewalk ' + where(w, a.x, a.z) + ' to ' + where(w, b.x, b.z) + ' runs into ' + hit);
      }
    }
  }
  // every zebra: from curb to curb, both ways, the way the kids and the dog walk it
  for (i = 0; i < w.cross.length; i++) {
    var cr = w.cross[i];
    [[cr.a, cr.b], [cr.b, cr.a]].forEach(function (ab) {
      var pts = w.lanePath(ab, 0.8);
      pts.forEach(function (p) {
        if (w.onRoad(p.x, p.z, 0.55)) out.push('a curb ' + where(w, p.x, p.z) + ' is out in the road');
        if (Math.hypot(p.x, p.z) > w.R - 1.5) out.push('a curb ' + where(w, p.x, p.z) + ' is at the edge');
      });
      var hitZ = hitAlong(w, pts, 0.85, null);
      if (hitZ) out.push('the zebra ' + where(w, pts[0].x, pts[0].z) + ' runs into ' + hitZ);
    });
  }
  // every spot (and party slot) has a clear way in and out, on its own side of the streets
  var list = w.spots.concat(w.partySlots || []);
  for (i = 0; i < list.length; i++) {
    var s = list[i], n = w.nodes[s.node], name = (s.party ? 'the party slot' : 'the ' + s.kind) + ' at ' + where(w, s.x, s.z);
    if (!n) { out.push(name + ' has no way to the sidewalk'); continue; }
    if (w.blockOf(s.x, s.z) !== n.block) out.push(name + ' is reached from across a street');
    hit = hitAlong(w, [n].concat(s.via || [], [s]), 0.85, s.own || null);
    if (hit) out.push('the way to ' + name + ' runs into ' + hit);
    if (s.exit) { hit = hitAlong(w, [s.off].concat(s.exit, [w.nodes[s.exitNode]]), 0.85, s.own || null); if (hit) out.push('the way out of ' + name + ' runs into ' + hit); }
    if (Math.hypot(s.x, s.z) > w.R - 1.5) out.push(name + ' is too near the edge');
  }
  for (i = 0; i < w.spots.length; i++) for (j = i + 1; j < w.spots.length; j++) {
    var p = w.spots[i], q = w.spots[j];
    if (Math.hypot(p.x - q.x, p.z - q.z) < 2.1) out.push('the ' + p.kind + ' and the ' + q.kind + ' at ' + where(w, p.x, p.z) + ' stand on each other');
  }
  // both cars' loops: on the road all the way round, clear of everything
  for (var li = 0; li < w.loops.length; li++) {
    var loop = w.loops[li], bad = '';
    for (var sv = 0; sv < loop.len && !bad; sv += 0.5) {
      var car = { loop: li, s: sv };
      w.placeCar(car);
      var c = Math.cos(car.yaw), sn = Math.sin(car.yaw), body = [[1.35, 2.6], [-1.35, 2.6], [1.35, -2.6], [-1.35, -2.6], [1.35, 0], [-1.35, 0]];
      for (j = 0; j < body.length && !bad; j++) {
        var x = car.x + sn * body[j][1] - c * body[j][0], z = car.z + c * body[j][1] + sn * body[j][0];
        if (!onRoadLoose(w, x, z)) bad = 'leaves the road at ' + where(w, x, z);
        for (var k = 0; k < w.obst.length && !bad; k++) if (w.obst[k].tag !== 'car' && w.obst[k].tag !== 'barrier' && inside(w.obst[k], x, z, 0.1)) bad = 'drives into the ' + w.obst[k].tag;
      }
    }
    if (bad) out.push('car loop ' + li + ' ' + bad);
  }
  return out;
}

/* --------------------------------------------------------- a run of it */
function run(w, secs) {
  var dt = 1 / 30, steps = Math.round(secs / dt), ks = w.kids, i, j;
  var r = { inside: 0, insideAt: '', carKid: 0, carKidAt: '', carDog: 0, carCar: 0, stuck: 0, stuckAt: '', wait: 0, waitAt: '',
            outside: 0, nan: 0, bump: 0, bumpAt: '', parties: 0, walked: 0, seeFrames: 0, seeMin: 9, seeMax: -9, seeOff: 0 };
  var pair = {}, waitFor = ks.map(function () { return 0; }), still = ks.map(function (k) { return { x: k.x, z: k.z, t: 0 }; }), wasParty = false;
  for (var st = 0; st < steps; st++) {
    w.step(dt, false);
    if (w.party > 0 && !wasParty) r.parties++;
    wasParty = w.party > 0;
    for (i = 0; i < ks.length; i++) {
      var a = ks[i];
      if (!isFinite(a.x) || !isFinite(a.z)) { r.nan++; continue; }
      var moving = w.mobility(a) > 0;
      if (a.path && !a.waiting) r.walked += dt;
      // into something it shouldn't be?
      if (moving) {
        var own = (a.target && a.target.own) || (a.spot && a.spot.own) || [], old = (a.leaving && a.leaving.own) || [];
        for (j = 0; j < w.obst.length; j++) {
          var o = w.obst[j];
          if (own.indexOf(o) >= 0 || old.indexOf(o) >= 0) continue;
          var dp = depth(o, a.x, a.z, 0.6);
          if (dp > 0.05) { r.inside++; r.insideAt = 'the ' + o.tag + ' at ' + where(w, a.x, a.z); }
        }
      }
      if (Math.hypot(a.x, a.z) > w.R - 0.9) r.outside++;
      // two kids standing in each other
      for (j = i + 1; j < ks.length; j++) {
        var b = ks[j], key = i + '-' + j;
        if ((moving || w.mobility(b) > 0) && Math.hypot(a.x - b.x, a.z - b.z) < 1.55) {
          pair[key] = (pair[key] || 0) + dt;
          if (pair[key] > r.bump) { r.bump = pair[key]; r.bumpAt = where(w, a.x, a.z); }
        } else pair[key] = 0;
      }
      // waiting at a curb
      if (a.waiting) { waitFor[i] += dt; if (waitFor[i] > r.wait) { r.wait = waitFor[i]; r.waitAt = where(w, a.x, a.z); } } else waitFor[i] = 0;
      // walking, not waiting, not getting anywhere
      var s = still[i];
      if (Math.hypot(a.x - s.x, a.z - s.z) > 0.6 || !a.path || a.waiting) { s.x = a.x; s.z = a.z; s.t = w.t; }
      else if (w.t - s.t > 6) { r.stuck++; r.stuckAt = where(w, a.x, a.z); s.t = w.t; }
    }
    // the seesaw: moving whenever someone rides it, the riders on their seats
    if (w.seesaws && w.seesaws.length === 2) {
      w.seesaws.forEach(function (s) {
        var k = s.user;
        if (!k || k.path || k.act !== 'seesaw') return;
        r.seeFrames++;
        r.seeMin = Math.min(r.seeMin, w.seeTh); r.seeMax = Math.max(r.seeMax, w.seeTh);
        if (k.actT < 0.5) return;          // still climbing on
        var u = s.end * 4, seat = 1.65 + u * Math.sin(w.seeTh) + 0.175 * Math.cos(w.seeTh) + 0.06 - 0.5;
        r.seeOff = Math.max(r.seeOff, Math.abs(k.y - seat), Math.abs(k.x - (s.cx + u * Math.cos(w.seeTh)) * w.mir));
      });
    }
    // the cars: against a kid, the dog, each other
    if (w.cars) {
      var bodies = w.cars.map(carCorners);
      for (var c = 0; c < w.cars.length; c++) {
        var car = w.cars[c], cs = Math.cos(car.yaw), sn = Math.sin(car.yaw);
        var touch = function (x, z, pad) {
          var dx = x - car.x, dz = z - car.z, lon = dx * sn + dz * cs, lat = -dx * cs + dz * sn;
          return Math.abs(lon) < 2.6 + pad && Math.abs(lat) < 1.35 + pad;
        };
        for (i = 0; i < ks.length; i++) if (ks[i].visible && touch(ks[i].x, ks[i].z, 0.55)) { r.carKid++; r.carKidAt = where(w, ks[i].x, ks[i].z); }
        if (w.dog && touch(w.dog.x, w.dog.z, 0.4)) r.carDog++;
        for (var c2 = c + 1; c2 < w.cars.length; c2++) if (quadGap(bodies[c], bodies[c2]) < 0.15) r.carCar++;
      }
    }
  }
  return r;
}

/* ------------------------------------------------------------- the runs */
var win = load(), seasons = ['spring', 'summer', 'autumn', 'winter'];
['hero', 'panel'].forEach(function (mode, m) {
  console.log('\n' + mode + ': ' + TOWNS + ' towns, ' + SECS + ' s each');
  var worst = { inside: 0, carKid: 0, carDog: 0, carCar: 0, stuck: 0, wait: 0, outside: 0, nan: 0, bump: 0, parties: 0, walked: 0,
                seeFrames: 0, seeMin: 9, seeMax: -9, seeOff: 0 }, notes = {};
  var layout = [], mirrored = 0, backs = {};
  for (var t = 1; t <= TOWNS; t++) {
    var seed = t * 7919 + m * 104729, season = seasons[t % 4];
    win.Math.seed = seed;
    var w = makeWorld(win, mode, seed, season), label = 'seed ' + seed + ' (' + season + ', ' + w.look.back + (w.mir < 0 ? ', mirrored' : '') + ')';
    if (w.mir < 0) mirrored++;
    backs[w.look.back] = 1;
    layoutProblems(w).forEach(function (p) { layout.push(label + ': ' + p); });
    if (SECS <= 0) continue;
    var r = run(w, SECS);
    ['inside', 'carKid', 'carDog', 'carCar', 'stuck', 'outside', 'nan'].forEach(function (k) {
      if (r[k]) { worst[k] += r[k]; notes[k] = notes[k] || (label + (r[k + 'At'] ? ', ' + r[k + 'At'] : '')); }
    });
    if (r.wait > worst.wait) { worst.wait = r.wait; notes.wait = label + ', ' + r.waitAt; }
    if (r.bump > worst.bump) { worst.bump = r.bump; notes.bump = label + ', ' + r.bumpAt; }
    worst.parties += r.parties; worst.walked += r.walked;
    worst.seeFrames += r.seeFrames; worst.seeMin = Math.min(worst.seeMin, r.seeMin); worst.seeMax = Math.max(worst.seeMax, r.seeMax);
    worst.seeOff = Math.max(worst.seeOff, r.seeOff);
  }
  check(mode + ': towns of both hands and several buildings', mirrored > 0 && mirrored < TOWNS || TOWNS < 3, { mirrored: mirrored, of: TOWNS });
  check(mode + ': the layout is sound (sidewalks, zebras, curbs, spots, car loops)', !layout.length, layout.slice(0, 8).join(' | '));
  if (SECS <= 0) return;
  check(mode + ': nobody walks into the fountain, a wall, a pond, a tree or a lamp', !worst.inside, notes.inside);
  check(mode + ': no car touches a kid', !worst.carKid, notes.carKid);
  check(mode + ': no car touches the dog', !worst.carDog, notes.carDog);
  check(mode + ': the two cars never touch', !worst.carCar, notes.carCar);
  check(mode + ': nobody gets stuck on the way somewhere', !worst.stuck, notes.stuck);
  check(mode + ': nobody waits at a curb for more than 20 s', worst.wait <= 20, (notes.wait || '') + ' ' + worst.wait.toFixed(1) + ' s');
  check(mode + ': nobody leaves the island', !worst.outside, notes.outside);
  check(mode + ': every position is a number', !worst.nan, notes.nan);
  check(mode + ': two kids never stand in each other for more than 1.5 s', worst.bump <= 1.5, (notes.bump || '') + ' ' + worst.bump.toFixed(2) + ' s');
  check(mode + ': the seesaw moves whenever someone rides it, and they stay on their seat',
        worst.seeFrames > 0 && worst.seeMax - worst.seeMin > 0.35 && worst.seeOff < 0.05,
        { riddenFrames: worst.seeFrames, tilt: [+worst.seeMin.toFixed(2), +worst.seeMax.toFixed(2)], offSeat: +worst.seeOff.toFixed(3) });
  check(mode + ': the kids get about (and the parties happen)', worst.walked > TOWNS * SECS * 0.5 && (SECS < 200 || worst.parties > 0), { walked: Math.round(worst.walked), parties: worst.parties });
});

/* the small domes: a single home, no streets -- they still run */
['build', 'mini'].forEach(function (mode) {
  win.Math.seed = 4242;
  var w = makeWorld(win, mode, 4242, 'summer');
  if (mode === 'build') { w.setName('PixelMia42'); w.setStage(6); }
  var ok = true;
  for (var i = 0; i < 30 * 30; i++) {
    w.step(1 / 30, false);
    w.kids.forEach(function (k) { if (!isFinite(k.x) || !isFinite(k.z)) ok = false; });
  }
  check(mode + ': the small dome has no town and runs', !w.town && ok, { town: !!w.town, kids: w.kids.length });
});

console.log('\n' + passed + ' passed, ' + failed + ' failed');
process.exit(failed ? 1 : 0);
