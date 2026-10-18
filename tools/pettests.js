#!/usr/bin/env node
/* The pet rig and the follower AI, checked headless (no browser, no server):

     node tools/pettests.js

   static/js/engine/pet.js and static/js/game/pets.js are loaded into a
   stand-in window with a flat world (and a wall, for the tests that want
   one).  The follower is then put through what a player puts her through:
   standing about, running off, jumping, dying, coming back, strangers,
   enemies, a long way off -- and is checked for doing something sensible
   each time.  Her choices are random by design, so the checks that depend
   on a choice run her many times over and look for the behaviour at all. */
'use strict';
var fs = require('fs');
var path = require('path');
var vm = require('vm');

var ROOT = path.join(__dirname, '..');
var passed = 0, failed = 0;
function check(name, ok, detail) {
  if (ok) { passed++; console.log('  PASS  ' + name); }
  else { failed++; console.log('  FAIL  ' + name + (detail !== undefined ? '  ' + JSON.stringify(detail) : '')); }
}

function load() {
  var win = { console: console, Math: Math, JSON: JSON, Object: Object, Array: Array,
              Settings: { particles: true, showPets: true }, BH: { user: { name: 'owner' } } };
  win.window = win;
  var ctx = vm.createContext(win);
  ['static/js/engine/pet.js', 'static/js/game/pets.js'].forEach(function (file) {
    vm.runInContext(fs.readFileSync(path.join(ROOT, file), 'utf8'), ctx, { filename: file });
  });
  return win;
}

/* A flat world at y = 0, with an optional wall: an axis-aligned box.  It
   counts the rays it is asked to cast. */
function physics(walls) {
  walls = walls || [];
  return {
    rays: 0,
    rayDistance: function (o, d, max) {
      this.rays++;
      var best = max;
      if (d[1] < -0.5 && o[1] >= 0) best = Math.min(best, o[1]);
      walls.forEach(function (b) {
        var tmin = 0, tmax = max;
        for (var a = 0; a < 3; a++) {
          if (Math.abs(d[a]) < 1e-9) {
            if (o[a] < b.min[a] || o[a] > b.max[a]) { tmin = Infinity; break; }
          } else {
            var t1 = (b.min[a] - o[a]) / d[a], t2 = (b.max[a] - o[a]) / d[a];
            tmin = Math.max(tmin, Math.min(t1, t2));
            tmax = Math.min(tmax, Math.max(t1, t2));
          }
        }
        if (tmin <= tmax && tmin < best) best = tmin;
      });
      return best;
    }
  };
}

function world(win, pet, opts) {
  opts = opts || {};
  var spawned = 0;
  var client = {
    particles: { spawn: function () { spawned++; } },
    renderer: { push: function () {}, pushRaw: function () {} },
    physics: physics(opts.walls), map: { kill_y: -60 }, myId: 1, myTeam: opts.team || '',
    local: { pos: [0, 0, 0], vel: [0, 0, 0], yaw: 0, anim: 'idle', grounded: true, alive: true,
             health: 100 },
    players: {}, avatar: { pet: pet }, stowed: true,
    currentWeapon: function () { return null; }
  };
  var pw = new win.PetWorld(client);
  return { client: client, pw: pw, spawned: function () { return spawned; },
           me: function () { return pw.followers.me; } };
}

function run(w, secs, each) {
  var dt = 1 / 30;
  for (var t = 0; t < secs; t += dt) {
    if (each) each(t, dt);
    var me = w.client.local;
    me.pos[0] += me.vel[0] * dt; me.pos[2] += me.vel[2] * dt;
    w.pw.frame(dt, t, { eye: [me.pos[0], me.pos[1] + 9, me.pos[2] - 14] });
  }
}

function hd(a, b) { return Math.hypot(a[0] - b[0], a[2] - b[2]); }
function avg(list) { return list.reduce(function (a, b) { return a + b; }, 0) / (list.length || 1); }
// what she does up close to her owner on purpose
var CLOSE = { visit: 1, comfort: 1, hide: 1 };

/* Her owner holds a gun: is she in front of it? */
function inLine(w) {
  var f = w.me(), me = w.client.local;
  var along = (f.pos[0] - me.pos[0]) * Math.sin(me.yaw) + (f.pos[2] - me.pos[2]) * Math.cos(me.yaw);
  var across = (f.pos[0] - me.pos[0]) * Math.cos(me.yaw) - (f.pos[2] - me.pos[2]) * Math.sin(me.yaw);
  return along > 0 && along < 25 && Math.abs(across) < along * 0.4 + 0.5;
}

/* Her owner keeps shooting: a shot every half second or so. */
function shooting(w, t) {
  if (Math.floor(t / 0.5) !== Math.floor((t - 1 / 30) / 0.5) || t < 1 / 30) {
    w.pw.notify('shot', { id: w.client.myId });
  }
}

/* Her owner jumps: up, and down again a little later. */
function hop(me) {
  me.grounded = false;
  me.vel[1] = 34;
}
function fall(me, dt) {
  if (me.grounded) return;
  me.vel[1] -= 62 * dt;
  me.pos[1] += me.vel[1] * dt;
  if (me.pos[1] <= 0) { me.pos[1] = 0; me.vel[1] = 0; me.grounded = true; }
}

var win = load();
var Pet = win.Pet;

// ----------------------------------------------------------------- the rig
console.log('== the rig ==');
var species = Pet.ORDER;
check('five species', species.length === 5, species);
species.forEach(function (sp) {
  var parts = Pet.build({ species: sp, items: {} }, { position: [0, 0, 0], pose: Pet.act('idle', 0.5) });
  var bad = parts.filter(function (p) {
    return [p.p, p.s, p.r].some(function (v) { return v.some(function (x) { return !isFinite(x); }); });
  });
  var top = Math.max.apply(null, parts.map(function (p) { return p.p[1] + p.s[1] / 2; }));
  var low = Math.min.apply(null, parts.map(function (p) { return p.p[1] - p.s[1] / 2; }));
  check(sp + ': every part is finite', !bad.length, bad.length);
  // the avatar is 5.4 from soles to crown: she is about half that
  var crown = sp === 'mochi' || sp === 'pixel' ? 3.5 : 3.05;
  check(sp + ': about half a player tall', top > 2.45 && top < crown, top.toFixed(2));
  check(sp + ': stands on the ground', low > -0.12 && low < 0.12, low.toFixed(3));
  check(sp + ': a reasonable part count', parts.length > 40 && parts.length < 170, parts.length);
});
var acts = Pet.actions();
var nan = [];
acts.forEach(function (a) {
  [0, 0.4, 1.1, 2.7].forEach(function (t) {
    var pose = Pet.act(a, t);
    Object.keys(pose).forEach(function (k) {
      if (typeof pose[k] === 'number' && !isFinite(pose[k])) nan.push(a + '.' + k);
    });
    var parts = Pet.build({ species: 'mochi' }, { pose: pose, time: t });
    if (parts.some(function (p) { return !isFinite(p.p[1]); })) nan.push(a + '@' + t);
  });
});
check('every action (' + acts.length + ') poses cleanly', !nan.length, nan.slice(0, 5));
check('at least 40 actions', acts.length >= 40, acts.length);
var faces = {};
acts.forEach(function (a) { var p = Pet.act(a, 0.5); faces[p.eyes + '/' + p.mouth] = 1; });
check('the actions use at least a dozen faces', Object.keys(faces).length >= 12, Object.keys(faces).length);
var hat = { pet_hat: { item_id: 'x', data: { parts: [{ t: 'box', p: [0, 0.1, 0], s: [1, 0.2, 1], c: '#f00' }] } } };
var bare = Pet.build({ species: 'fern', items: {} }, { pose: Pet.act('idle', 0) });
var hatted = Pet.build({ species: 'fern', items: hat }, { pose: Pet.act('idle', 0) });
check('a hat hides Fern\'s sprout and sits on her', hatted.length === bare.length - 3 + 1,
      [bare.length, hatted.length]);
check('worn parts are tagged for framing', hatted.some(function (p) { return p.k === 'worn'; }));
var show = new Pet.Showcase({ species: 'luna', tags: ['sleepy', 'dreamy'] });
var seen = {};
for (var i = 0; i < 30 * 60; i++) { show.step(1 / 30); seen[show.action] = 1; }
check('a showcase pet does several things in a minute', Object.keys(seen).length >= 4, Object.keys(seen));

// ------------------------------------------------------------------ the face
/* The eyes are the first thing anyone looks at, so they are checked the way
   they go wrong: sinking into the head where it rounds off or standing off
   it like a visor (at every species, expression, glance, head turn and
   squash), the iris sliding out of the eye or over the lash (two blocks
   fighting over one patch of face shimmer), and hair or a hat hanging in
   front of them.  Everything is measured in the head's own frame, against
   the head's real surface: the 'pethead' rounded box, from its own size. */
console.log('\n== the face ==');
function euler(r) {
  var cx = Math.cos(r[0]), sx = Math.sin(r[0]), cy = Math.cos(r[1]), sy = Math.sin(r[1]);
  var cz = Math.cos(r[2]), sz = Math.sin(r[2]);
  return [cy * cz + sy * sx * sz, cx * sz, -sy * cz + cy * sx * sz,
          -cy * sz + sy * sx * cz, cx * cz, sy * sz + cy * sx * cz, sy * cx, -sx, cy * cx];
}
function rot(m, v) {
  return [m[0] * v[0] + m[3] * v[1] + m[6] * v[2], m[1] * v[0] + m[4] * v[1] + m[7] * v[2],
          m[2] * v[0] + m[5] * v[1] + m[8] * v[2]];
}
function unrot(m, v) {
  return [m[0] * v[0] + m[1] * v[1] + m[2] * v[2], m[3] * v[0] + m[4] * v[1] + m[5] * v[2],
          m[6] * v[0] + m[7] * v[1] + m[8] * v[2]];
}
/* The head's frame, in head units: its centre at the origin, facing +Z, and
   any squash or stretch taken back out, so a squashed face is measured
   against the same layout as a still one.  point() is a part's point at
   (i, j, k), each -1..1 across its box. */
function headFrame(parts) {
  var head = parts.filter(function (p) { return p.k === 'head'; })[0];
  var m = euler(head.r);
  var R = Pet.HEAD_ROUND, S = Pet.B.head;
  var k = [head.s[0] / S[0], head.s[1] / S[1], head.s[2] / S[2]];
  return {
    head: head, m: m,
    local: function (P) {
      var o = unrot(m, [P[0] - head.p[0], P[1] - head.p[1], P[2] - head.p[2]]);
      return [o[0] / k[0], o[1] / k[1], o[2] / k[2]];
    },
    point: function (part, i, j, n) {
      var o = rot(euler(part.r), [i * part.s[0] / 2, j * part.s[1] / 2, n * part.s[2] / 2]);
      return this.local([part.p[0] + o[0], part.p[1] + o[1], part.p[2] + o[2]]);
    },
    // how far forward of the head's centre its skin is, at (x, y)
    skin: function (x, y) {
      var dx = Math.max(0, Math.abs(x) - S[0] * (0.5 - R[0])) / (S[0] * R[0]);
      var dy = Math.max(0, Math.abs(y) - S[1] * (0.5 - R[1])) / (S[1] * R[1]);
      return S[2] * (0.5 - R[2]) + S[2] * R[2] * Math.sqrt(Math.max(0, 1 - dx * dx - dy * dy));
    },
    // a ray from a point in the head's frame straight out of the face (or
    // back into it, dir -1) against a part's box: how far along it enters,
    // or Infinity
    hit: function (P, part, max, dir) {
      dir = dir || 1;
      var pm = euler(part.r);
      var o = unrot(pm, rot(m, [P[0] * k[0], P[1] * k[1], P[2] * k[2]]));
      var d = unrot(pm, rot(m, [0, 0, dir * k[2]]));
      var c = unrot(pm, [part.p[0] - head.p[0], part.p[1] - head.p[1], part.p[2] - head.p[2]]);
      var t0 = 0, t1 = max;
      for (var a = 0; a < 3; a++) {
        var lo = c[a] - part.s[a] / 2, hi = c[a] + part.s[a] / 2;
        if (Math.abs(d[a]) < 1e-9) {
          if (o[a] < lo || o[a] > hi) return Infinity;
        } else {
          var u = (lo - o[a]) / d[a], v = (hi - o[a]) / d[a];
          t0 = Math.max(t0, Math.min(u, v)); t1 = Math.min(t1, Math.max(u, v));
        }
      }
      return t0 <= t1 ? t0 : Infinity;
    }
  };
}
var F = Pet.FACE;
/* Which pixel of an eye bitmap a point on the face falls in. */
function eyeCell(rows, x, y) {
  var mirror = x > 0;
  var u = (mirror ? (F.eyeX - x) : (x + F.eyeX)) / F.eyePx + rows[0].length / 2;
  var v = (F.eyeY - y) / F.eyePx + rows.length / 2;
  var r = Math.floor(v), c = Math.floor(u);
  return r >= 0 && r < rows.length ? (rows[r].charAt(c) || '.') : '.';
}
function bitmaps(pose) {
  var e = pose.eyes || 'open';
  if (pose.blink > 0.5 && e !== 'joy' && e !== 'closed' && e !== 'dizzy') e = 'closed';
  var pair = e === 'wink' ? ['open', 'joy'] : [e, e];
  if (pose.blink > 0.5 && e === 'wink') pair = ['closed', 'closed'];
  return [Pet.EYES[pair[0]], Pet.EYES[pair[1]]];
}
var faceFail = { sunk: [], proud: [], floats: [], overlap: [], outside: [], area: [] };
function note(list, what) { if (list.length < 4) list.push(what); }
function checkFace(sp, pose, label) {
  var parts = Pet.build({ species: sp, items: {} }, { position: [3, 0, -2], yaw: 0.7, pose: pose,
                                                      time: 1.3 });
  var H = headFrame(parts);
  var pieces = parts.filter(function (p) { return p.k === 'eye' || p.k === 'face'; });
  pieces.forEach(function (p) {
    var top = p.k === 'eye' ? 0.02 : 0.045;
    [-1, 0, 1].forEach(function (i) {
      [-1, 0, 1].forEach(function (j) {
        var f = H.point(p, i, j, 1), b = H.point(p, i, j, -1);
        var lift = f[2] - H.skin(f[0], f[1]);
        if (lift < 0.001) note(faceFail.sunk, [label, p.k, lift.toFixed(4)]);
        if (lift > top) note(faceFail.proud, [label, p.k, lift.toFixed(4)]);
        if (b[2] - H.skin(b[0], b[1]) > -0.001) note(faceFail.floats, [label, p.k]);
      });
    });
  });
  // the eyes tile their outline exactly: no two pieces overlap, none strays
  // outside it, and between them they cover all of it
  var rows = bitmaps(pose);
  var eyes = parts.filter(function (p) { return p.k === 'eye'; }).map(function (p) {
    var a = H.point(p, -1, -1, 1), b = H.point(p, 1, 1, 1);
    return [Math.min(a[0], b[0]), Math.max(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[1], b[1])];
  });
  var area = 0;
  eyes.forEach(function (q, n) {
    area += (q[1] - q[0]) * (q[3] - q[2]);
    var bm = q[0] + q[1] > 0 ? rows[1] : rows[0];
    for (var i = 0; i <= 4; i++) {
      for (var j = 0; j <= 4; j++) {
        var x = q[0] + 1e-4 + (q[1] - q[0] - 2e-4) * i / 4;
        var y = q[2] + 1e-4 + (q[3] - q[2] - 2e-4) * j / 4;
        if (eyeCell(bm, x, y) === '.') { note(faceFail.outside, [label, x.toFixed(3), y.toFixed(3)]); return; }
      }
    }
    for (var k = n + 1; k < eyes.length; k++) {
      var o = eyes[k];
      var w = Math.min(q[1], o[1]) - Math.max(q[0], o[0]), h = Math.min(q[3], o[3]) - Math.max(q[2], o[2]);
      if (w > 1e-5 && h > 1e-5) note(faceFail.overlap, [label, (w * h).toExponential(2)]);
    }
  });
  var want = 0;
  rows.forEach(function (bm) {
    bm.join('').split('').forEach(function (ch) { if (ch !== '.') want += F.eyePx * F.eyePx; });
  });
  if (Math.abs(area - want) > 1e-5) note(faceFail.area, [label, area.toFixed(5), want.toFixed(5)]);
}
var looks = [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1], [0.7, 0.6], [-0.8, -0.5], [0.33, -0.21]];
var heads = [[0, 0, 0], [0.9, 0.3, 0.2], [-1.05, -0.6, -0.3]];
var faceBuilds = 0;
species.forEach(function (sp) {
  Object.keys(Pet.EYES).concat(['wink']).forEach(function (e) {
    looks.forEach(function (lk) {
      heads.forEach(function (hd, n) {
        [1, 0.86, 1.06].forEach(function (sq) {
          var pose = Pet.act('idle', 0.7);
          pose.eyes = e; pose.lookX = lk[0]; pose.lookY = lk[1];
          pose.headYaw = hd[0]; pose.headPitch = hd[1]; pose.headRoll = hd[2];
          pose.squash = sq; pose.blink = (n === 2 && lk[0] === 1) ? 1 : 0;
          pose.brows = ['angry', 'sad', 'up', 'worry', ''][n + (sq === 1 ? 0 : 2)];
          pose.mouth = Object.keys(Pet.MOUTHS)[(faceBuilds++) % Object.keys(Pet.MOUTHS).length];
          pose.blush = 0.8; pose.tears = lk[1] < 0 ? 1 : 0; pose.sniff = 1;
          checkFace(sp, pose, [sp, e, lk.join(','), hd.join(','), sq].join(' '));
        });
      });
    });
  });
  acts.forEach(function (a) {
    [0.2, 0.9, 1.7].forEach(function (t) {
      var pose = Pet.act(a, t);
      pose.lookX = Math.sin(t * 3); pose.lookY = Math.cos(t * 5);
      checkFace(sp, pose, sp + ' ' + a + '@' + t);
      faceBuilds++;
    });
  });
});
check('eyes, mouth and cheeks never sink into the head (' + faceBuilds + ' faces)',
      !faceFail.sunk.length, faceFail.sunk);
check('...nor stand off it', !faceFail.proud.length, faceFail.proud);
check('...nor float in front of it with a gap behind', !faceFail.floats.length, faceFail.floats);
check('no two pixels of an eye cover the same patch of face', !faceFail.overlap.length,
      faceFail.overlap);
check('a glance never carries the iris out of the eye', !faceFail.outside.length, faceFail.outside);
check('...nor leaves a hole in it', !faceFail.area.length, faceFail.area);

/* ...and it does carry it the way she looks: the catchlight in each eye
   moves with the look, and the white shows beside the iris when she looks
   aside or up -- not at rest, and not when she looks down, when her lids
   follow her eyes down instead. */
var glances = [];
species.forEach(function (sp) {
  var s = Pet.SPECIES[sp], iris = s.colors.eyes;
  var white = s.led ? Pet.shade(iris, 0.6) : '#f7f7fa';
  function eyesAt(lx, ly) {
    var pose = Pet.act('idle', 0.7);
    pose.eyes = 'open'; pose.lookX = lx; pose.lookY = ly;
    var parts = Pet.build({ species: sp, items: {} }, { pose: pose });
    var H = headFrame(parts);
    var eyes = { l: [0, 0, 0, false], r: [0, 0, 0, false] };
    parts.forEach(function (p) {
      if (p.k !== 'eye') return;
      var c = H.point(p, 0, 0, 1), e = eyes[c[0] < 0 ? 'l' : 'r'];
      if (p.c === white) e[3] = true;
      if (p.c !== '#ffffff') return;
      var a = p.s[0] * p.s[1];
      e[0] += c[0] * a; e[1] += c[1] * a; e[2] += a;
    });
    return [eyes.l, eyes.r].map(function (e) { return [e[0] / e[2], e[1] / e[2], e[3]]; });
  }
  var rest = eyesAt(0, 0);
  if (rest[0][2] || rest[1][2]) glances.push([sp, 'white showing at rest']);
  [[1, 0, 0, 1, true], [-1, 0, 0, -1, true], [0, 1, 1, 1, true], [0, -1, 1, -1, false]]
    .forEach(function (g) {
      eyesAt(g[0], g[1]).forEach(function (e, n) {
        var moved = (e[g[2]] - rest[n][g[2]]) * g[3];
        if (!(moved > 0.006)) glances.push([sp, g[0], g[1], n ? 'right' : 'left', moved]);
        if (e[2] !== g[4]) glances.push([sp, g[0], g[1], e[2] ? 'white showing' : 'no white']);
      });
    });
});
check('a glance moves the iris the way she looks, showing the white', !glances.length, glances);

/* Nothing on her head hangs in front of her eyes, and the brows are always
   drawn over what is in front of them -- looking straight out of the face,
   so at any head turn -- while lying on it: no air behind a brow, and never
   standing further forward than the hair or skin it is drawn over. */
var covered = [], hidden = [], browsOff = [];
function onHer(p) { return p.k !== 'eye' && p.k !== 'face' && p.k !== 'brow' && p.k !== 'head'; }
function infront(H, from, parts, max) {
  var best = Infinity, what = null;
  parts.forEach(function (p) {
    if (!onHer(p)) return;
    var t = H.hit(from, p, max);
    if (t < best) { best = t; what = p; }
  });
  return { t: best, part: what };
}
/* How far forward the skin or the hair is, straight behind a point. */
function behind(H, P, parts) {
  var z = H.skin(P[0], P[1]);
  parts.forEach(function (q) {
    if (!onHer(q)) return;
    var t = H.hit(P, q, 0.3, -1);
    if (t < Infinity) z = Math.max(z, P[2] - t);
  });
  return z;
}
/* How far forward the frontmost thing is that a brow is drawn over: the
   skin across it, or any of her that overlaps it seen from the front (the
   separating-axis test on its box's corners, along the brow's own axes and
   the part's). */
function under(H, brow, parts) {
  var a = H.point(brow, -1, -1, 1), b = H.point(brow, 1, 1, 1);
  var x0 = Math.min(a[0], b[0]), x1 = Math.max(a[0], b[0]);
  var y0 = Math.min(a[1], b[1]), y1 = Math.max(a[1], b[1]);
  var z = Math.max(H.skin(x0, y0), H.skin(x1, y0), H.skin(x0, y1), H.skin(x1, y1));
  parts.forEach(function (q) {
    if (!onHer(q)) return;
    var pts = [];
    [-1, 1].forEach(function (i) {
      [-1, 1].forEach(function (j) {
        [-1, 1].forEach(function (k) { pts.push(H.point(q, i, j, k)); });
      });
    });
    var ax = pts[4][0] - pts[0][0], ay = pts[4][1] - pts[0][1];
    var axes = [[1, 0], [0, 1], [ax, ay], [-ay, ax]];
    var apart = axes.some(function (n) {
      var len = Math.hypot(n[0], n[1]);
      if (len < 1e-9) return false;
      var lo = Infinity, hi = -Infinity;
      pts.forEach(function (P) {
        var d = (P[0] * n[0] + P[1] * n[1]) / len;
        lo = Math.min(lo, d); hi = Math.max(hi, d);
      });
      var r = [[x0, y0], [x1, y0], [x0, y1], [x1, y1]].map(function (P) {
        return (P[0] * n[0] + P[1] * n[1]) / len;
      });
      return Math.min.apply(null, r) >= hi - 1e-4 || Math.max.apply(null, r) <= lo + 1e-4;
    });
    if (!apart) {
      pts.forEach(function (P) { z = Math.max(z, P[2]); });
    }
  });
  return z;
}
species.forEach(function (sp) {
  ['idle', 'walk', 'run', 'skip', 'hop', 'float', 'jump', 'land', 'twirl', 'dance', 'look',
   'scan', 'sit', 'curtsy', 'nod', 'stomp', 'sad_walk', 'sparkle'].forEach(function (a) {
    [0.15, 0.6, 1.2].forEach(function (t) {
      var pose = Pet.act(a, t);
      pose.brows = ['angry', 'sad', 'up', 'worry'][Math.round(t * 5) % 4];
      var parts = Pet.build({ species: sp, items: {} }, { pose: pose, time: t });
      var H = headFrame(parts);
      parts.forEach(function (p) {
        if (p.k !== 'eye' && p.k !== 'brow') return;
        for (var i = -0.95; i < 1; i += 0.38) {
          for (var j = -0.95; j < 1; j += 0.38) {
            var hit = infront(H, H.point(p, i, j, 1), parts, 0.6);
            if (hit.t < Infinity) note(p.k === 'eye' ? covered : hidden, [sp, a, t, hit.part.t]);
            var b = H.point(p, i, j, -1);
            if (p.k === 'brow' && b[2] - behind(H, b, parts) > 0.002) {
              note(browsOff, [sp, a, t, 'air behind']);
            }
          }
        }
        if (p.k !== 'brow') return;
        var off = H.point(p, 0, 0, 1)[2] - under(H, p, parts);
        if (off > 0.02) note(browsOff, [sp, a, t, 'stands off by', off.toFixed(3)]);
      });
    });
  });
});
check('no hair hangs in front of her eyes, whatever she is doing', !covered.length, covered);
check('the brows are drawn over the fringe', !hidden.length, hidden);
check('...lying on it rather than hovering in front of it', !browsOff.length, browsOff);

/* The wardrobe: no hat ever comes down over her eyes, and nothing stuck on
   her face (a plaster, a sticker: anything centred within a few hundredths
   of the skin) is stuck over one -- glasses, which stand well out in front
   of her eyes, are worn over them on purpose.  The models come from the
   catalogue (app/models/pets.py). */
var wardrobe = null;
try {
  wardrobe = JSON.parse(require('child_process').execFileSync('python3', ['-c',
    'import json, sys; sys.path.insert(0, sys.argv[1]); from app.models import pets; ' +
    'print(json.dumps([it for it in pets.ITEMS if it["slot"] in ("pet_hat", "pet_face")]))',
    ROOT], { encoding: 'utf8', timeout: 30000 }));
} catch (err) {
  console.log('  SKIP  the wardrobe (no python3 to read the catalogue)');
}
if (wardrobe) {
  var hatOver = [], stuckOver = [];
  wardrobe.forEach(function (it) {
    species.forEach(function (sp) {
      var items = {};
      items[it.slot] = { item_id: it.id, data: it.data };
      [[0, 0], [1, 1], [-1, -1]].forEach(function (lk) {
        var pose = Pet.act('idle', 0.4);
        pose.lookX = lk[0]; pose.lookY = lk[1];
        var parts = Pet.build({ species: sp, items: items }, { pose: pose, time: 0.4 });
        var H = headFrame(parts);
        var worn = parts.filter(function (p) {
          if (p.k !== 'worn') return false;
          if (it.slot === 'pet_hat') return true;
          var c = H.local(p.p);
          return c[2] - H.skin(c[0], c[1]) < 0.045;
        });
        parts.forEach(function (p) {
          if (p.k !== 'eye') return;
          [-0.9, 0, 0.9].forEach(function (i) {
            [-0.9, 0, 0.9].forEach(function (j) {
              var f = H.point(p, i, j, 1);
              worn.forEach(function (w) {
                if (H.hit(f, w, 0.6) === Infinity) return;
                note(it.slot === 'pet_hat' ? hatOver : stuckOver, [it.id, sp, w.t]);
              });
            });
          });
        });
      });
    });
  });
  check('no hat comes down over her eyes (' + wardrobe.length + ' hats and face things)',
        !hatOver.length, hatOver);
  check('nothing stuck on her face covers an eye', !stuckOver.length, stuckOver);
}

// ------------------------------------------------------------ following
console.log('\n== following ==');
var fern = { species: 'fern', name: 'Sprout', tags: ['cheerful', 'loyal', 'curious'], items: {} };
// settling first, with a pet who will not wander off in the middle of it
var w = world(win, { species: 'fern', name: 'Sprout', tags: ['cheerful', 'loyal', 'clingy'], items: {} });
run(w, 1);
var R = w.me().traits.follow;
check('her comfortable distance is well outside her owner (' + R.toFixed(1) + ' studs, clingy and loyal)',
      R >= 6 && R <= 7.5);
check('she appears near her owner, at about that distance',
      hd(w.me().pos, w.client.local.pos) > 4.5 && hd(w.me().pos, w.client.local.pos) < R + 2,
      hd(w.me().pos, w.client.local.pos).toFixed(1));
w.client.local.vel = [0, 0, 15];
w.client.local.anim = 'run';
var maxGap = 0, nearest = 1e9, speeds = [];
run(w, 6, function (t) {
  if (!w.me()) return;
  var d = hd(w.me().pos, w.client.local.pos);
  maxGap = Math.max(maxGap, d);
  if (!CLOSE[w.me().state]) nearest = Math.min(nearest, d);
  if (t > 1.5) speeds.push(w.me().speed);
});
check('she keeps up with a running owner', hd(w.me().pos, w.client.local.pos) < 16,
      hd(w.me().pos, w.client.local.pos).toFixed(1));
check('...never falling far behind', maxGap < 20, maxGap.toFixed(1));
check('...running, not walking', avg(speeds) > 12, avg(speeds).toFixed(1));
w.client.local.vel = [0, 0, 0];
w.client.local.anim = 'idle';
// where she is once she has stopped (a moment later she may well be off
// romping round them, which is not what this is about)
var rest = null, still = 0;
run(w, 3, function () {
  var f = w.me(), d = hd(f.pos, w.client.local.pos);
  if (!CLOSE[f.state]) nearest = Math.min(nearest, d);
  still = f.speed < 0.3 ? still + 1 : 0;
  if (still === 15 && !rest) {
    var dy = Math.atan2(w.client.local.pos[0] - f.pos[0], w.client.local.pos[2] - f.pos[2]);
    rest = { d: d, facing: Math.abs(((dy - (f.yaw + f.head[0])) + Math.PI * 3) % (Math.PI * 2) - Math.PI) };
  }
});
check('when they stop she settles a comfortable distance off',
      rest && rest.d >= 6 && rest.d < R * 1.25 + 1, rest && rest.d.toFixed(1));
check('...and comes to rest', !!rest, w.me().speed);
check('...and looks at them', rest && rest.facing < 0.6, rest && rest.facing.toFixed(2));
check('she is never inside her owner\'s personal space by accident', nearest > 4, nearest.toFixed(2));

console.log('\n== waiting ==');
var sat = false, slept = false, idled = {};
run(w, 120, function () {
  var f = w.me();
  if (f.state === 'sit') sat = true;
  if (f.state === 'sleep') slept = true;
  if (f.act) idled[f.act.name] = 1;
});
check('a long wait and she sits down', sat);
check('a longer one and she falls asleep', slept);
check('she keeps herself busy while she waits (' + Object.keys(idled).length + ' things)',
      Object.keys(idled).length >= 4, Object.keys(idled));
check('asleep, Zzz float up', w.spawned() > 0);
w.client.local.vel = [0, 0, 12];
run(w, 1.2);
check('her owner sets off and she wakes up', w.me().state !== 'sleep' && w.me().state !== 'sit',
      w.me().state);
w.client.local.vel = [0, 0, 0];

console.log('\n== far away ==');
w.client.local.pos = [300, 0, 300];
run(w, 0.5);
var back = hd(w.me().pos, w.client.local.pos);
check('a long way off and she reappears at their side, at her own distance', back > 3.5 && back < R + 2,
      back.toFixed(1));

console.log('\n== a ledge ==');
var w2 = world(win, fern, { walls: [{ min: [-20, 0, 6], max: [20, 5, 40] }] });
run(w2, 1);
w2.client.local.pos = [0, 5, 10];
// (up there she is as free to wander off and look at things as anywhere,
// so it is how near them she comes once she is up that counts)
var up = 0, upNear = 1e9;
run(w2, 5, function () {
  var f = w2.me();
  if (!f || f.pos[1] <= 4.5 || !f.grounded) return;
  up++;
  upNear = Math.min(upNear, hd(f.pos, w2.client.local.pos));
});
check('her owner jumps up on a block and she hops up after them',
      up > 30 && w2.me().pos[1] > 4.5 && upNear < w2.me().traits.follow + 3,
      { y: w2.me().pos[1].toFixed(2), near: upNear.toFixed(1), up: up });
check('...and does not wander off the edge of it', w2.me().pos[1] > 4.5, w2.me().pos[1].toFixed(2));

console.log('\n== a wall ==');
var w3 = world(win, fern, { walls: [{ min: [-3, 0, 4], max: [3, 30, 5] }] });
run(w3, 1);
w3.client.local.pos = [0, 0, 12];
var closest = 1e9;
run(w3, 5, function () { closest = Math.min(closest, hd(w3.me().pos, w3.client.local.pos)); });
check('a wall in the way and she finds her way round (or over) to their side of it',
      closest < w3.me().traits.follow + 1.5 && w3.me().pos[2] > 5,
      { closest: closest.toFixed(1), z: w3.me().pos[2].toFixed(1) });

console.log('\n== life and death ==');
var w4 = world(win, fern);
run(w4, 2);
w4.client.local.alive = false;
run(w4, 3);
check('her owner dies and she mourns', w4.me().state === 'mourn', w4.me().state);
check('...looking sad', w4.me().feeling() === 'sad', w4.me().feeling());
w4.client.local.alive = true;
w4.client.local.pos = [90, 0, 90];
run(w4, 1.5);
check('they respawn far off and she is back at their side',
      w4.me().state !== 'mourn' && hd(w4.me().pos, w4.client.local.pos) < w4.me().traits.follow + 3,
      { s: w4.me().state, d: hd(w4.me().pos, w4.client.local.pos).toFixed(1) });

console.log('\n== her persona decides ==');
function strangerTrial(tags, secs) {
  var ww = world(win, { species: 'mochi', tags: tags, items: {} });
  run(ww, 2);
  ww.client.players[7] = { id: 7, name: 'stranger', pos: [30, 0, 30], target: [30, 0, 30], yaw: 0,
                           anim: 'idle', alive: true, health: 100, team: '', avatar: {}, slot: 0 };
  var states = {};
  run(ww, secs || 4, function (t) {
    var p = ww.client.players[7];
    p.pos[0] = Math.max(3, p.pos[0] - 12 / 30); p.pos[2] = Math.max(3, p.pos[2] - 12 / 30);
    states[ww.me().state] = 1;
    if (ww.me().act) states['act:' + ww.me().act.name] = 1;
  });
  return states;
}
var shyHid = 0, cheerGreeted = 0;
for (var n = 0; n < 12; n++) {
  if (strangerTrial(['shy', 'sleepy', 'clingy']).hide) shyHid++;
  var c = strangerTrial(['cheerful', 'showoff', 'chatty']);
  if (c.greet || c['act:wave'] || c['act:pose']) cheerGreeted++;
}
check('a shy pet hides from a stranger', shyHid >= 6, shyHid + '/12');
check('a cheerful show-off greets them', cheerGreeted >= 8, cheerGreeted + '/12');

function hurtTrial(tags) {
  var ww = world(win, { species: 'ember', tags: tags, items: {} });
  run(ww, 2);
  ww.client.local.health = 60;
  var st = {};
  run(ww, 1.5, function () { st[ww.me().state] = 1; if (ww.me().act) st['act:' + ww.me().act.name] = 1; });
  return st;
}
var brave = hurtTrial(['brave', 'feisty']);
check('her owner is hurt and a brave pet stands guard', brave.guard || brave['act:stomp'], brave);
var shyHurt = hurtTrial(['shy']);
check('...and a shy one hides', shyHurt.hide || shyHurt['act:hide'], shyHurt);

var wandered = 0;
for (var k = 0; k < 6; k++) {
  var wc = world(win, { species: 'pixel', tags: ['curious', 'energetic', 'chatty'], items: {} });
  var went = false;
  run(wc, 40, function () { if (wc.me() && wc.me().state === 'wander') went = true; });
  if (went) wandered++;
}
check('a curious pet wanders off to look at things', wandered >= 3, wandered + '/6');

var wk = world(win, fern);
run(wk, 2);
var cheered = {};
wk.pw.notify('kill', { kid: 1, vid: 9, streak: 1 });
run(wk, 1.2, function () { if (wk.me().act) cheered[wk.me().act.name] = 1; });
check('her owner scores and she celebrates',
      ['cheer', 'fistpump', 'clap', 'heart', 'dance', 'twirl'].some(function (a) { return cheered[a]; }),
      Object.keys(cheered));
var mood = wk.me().mood.joy;
check('...and is happier for it', mood > 0.6, mood.toFixed(2));
wk.pw.notify('chat', { from: 'owner', m: 'good job sprout!' });
var named = {};
run(wk, 1.0, function () { if (wk.me().act) named[wk.me().act.name] = 1; });
check('her name in chat gets a wave or a heart', named.wave || named.heart, Object.keys(named));

var gun = world(win, fern);
gun.client.stowed = false;
gun.client.currentWeapon = function () { return { name: 'pistol' }; };
run(gun, 4, function (t) { shooting(gun, t); });
var f = gun.me(), me = gun.client.local;
var along = (f.pos[0] - me.pos[0]) * Math.sin(me.yaw) + (f.pos[2] - me.pos[2]) * Math.cos(me.yaw);
var across = (f.pos[0] - me.pos[0]) * Math.cos(me.yaw) - (f.pos[2] - me.pos[2]) * Math.sin(me.yaw);
check('her owner shooting, she stays out of the line of fire', !(along > 0 && Math.abs(across) < along * 0.4 + 0.5),
      { along: along.toFixed(2), across: across.toFixed(2) });

/* A gun in hand is not a gun going off: her owner, armed but not
   shooting, turns to look at her, and she stays where she is -- until
   they open fire, when she is out of the way at once. */
var look = world(win, { species: 'fern', name: 'Sprout', tags: ['cheerful', 'loyal', 'clingy'], items: {} });
look.client.stowed = false;
look.client.currentWeapon = function () { return { name: 'pistol' }; };
// (a pet with nothing else on her mind: no romps, rambles or cuddles to
// move her about while this is watched)
run(look, 0.1);
['play', 'wander', 'cling', 'fidget'].forEach(function (k) { look.me().traits[k] = 0; });
run(look, 6);
var lf = look.me(), lme = look.client.local;
lme.yaw = Math.atan2(lf.pos[0] - lme.pos[0], lf.pos[2] - lme.pos[2]);
var lfrom = lf.pos.slice(), lmoved = 0;
run(look, 3, function () { lmoved = Math.max(lmoved, hd(look.me().pos, lfrom)); });
check('armed but not shooting, her owner turns to look at her and she stays put',
      lmoved < 1.2 && inLine(look), lmoved.toFixed(2));
var lclear = false;
run(look, 1.5, function (t) { shooting(look, t); if (t > 1 && !inLine(look)) lclear = true; });
check('...and when they start shooting she gets out of the way', lclear);

/* A long way off and coming back to them as they walk her way, gun in
   hand: she heads for them, not off to one side, until they close. */
var cb = world(win, fern);
cb.client.stowed = false;
cb.client.currentWeapon = function () { return { name: 'pistol' }; };
run(cb, 1);
cb.me().pos = [0, 0, 30];
cb.client.local.vel = [0, 0, 6];
var bside = 0;
run(cb, 1.5, function () {
  var bf = cb.me(), bme = cb.client.local;
  if (bf.pos[2] - bme.pos[2] > cb.me().traits.follow * 2) bside = Math.max(bside, Math.abs(bf.pos[0]));
});
cb.client.local.vel = [0, 0, 0];
check('far ahead of them as they walk her way, she comes back to them, not off to one side',
      bside < 2.5, bside.toFixed(2));

// ------------------------------------------------------- personal space
console.log('\n== personal space ==');
/* Every species and a spread of personas, put through a walk, a turn, a
   run and a dead stop: where does she settle, and does she ever come
   inside her owner's personal space without meaning to? */
var MIXES = [[], ['shy', 'curious', 'dreamy'], ['clingy', 'loyal', 'cheerful'],
             ['energetic', 'playful', 'showoff'], ['sleepy', 'loyal', 'clingy'],
             ['feisty', 'brave', 'clumsy'], ['chatty', 'shy', 'curious']];
var settleMin = { d: 1e9 }, settleMax = { d: 0 }, bubble = { d: 1e9 }, follows = [];
Pet.ORDER.forEach(function (sp) {
  MIXES.forEach(function (tags) {
    var ww = world(win, { species: sp, tags: tags, items: {} });
    var me = ww.client.local, who = sp + ' ' + (tags.join('+') || 'no tags');
    var frame = 0, closeAt = -1e9;
    // (up close on purpose -- a cuddle -- and the moments after, on her
    // way back out, do not count)
    function watch() {
      var f = ww.me(), d = hd(f.pos, me.pos);
      frame++;
      if (CLOSE[f.state]) closeAt = frame;
      if (frame - closeAt > 90 && d < bubble.d) bubble = { d: d.toFixed(2), who: who, state: f.state };
    }
    run(ww, 1.5);
    follows.push(ww.me().traits.follow);
    me.vel = [0, 0, 10]; run(ww, 3, watch);
    me.vel = [8, 0, 6]; run(ww, 2, watch);
    me.vel = [22, 0, 0]; run(ww, 3, watch);
    me.vel = [0, 0, 0]; run(ww, 4, watch);
    run(ww, 4, function () {
      watch();
      var f = ww.me(), d = hd(f.pos, me.pos);
      // settled: following (or sat, or lying) and at rest at her spot
      if (['follow', 'sit', 'lie', 'sleep'].indexOf(f.state) < 0 || f.whim || f.spd > 0.5 ||
          frame - closeAt < 150) return;
      if (d < settleMin.d) settleMin = { d: d, who: who, state: f.state };
      if (d > settleMax.d) settleMax = { d: d, who: who, state: f.state };
    });
  });
});
check('every species and persona settles a comfortable way off (at least 6 studs)',
      settleMin.d >= 6, settleMin);
check('...and not miles away (at most 14)', settleMax.d <= 14, settleMax);
check('...and never comes inside her owner\'s personal space by accident', bubble.d >= 4, bubble);
var nearR = Math.min.apply(null, follows), farR = Math.max.apply(null, follows);
check('clingy and loyal keep nearer than shy and dreamy (' + nearR.toFixed(1) + ' to ' +
      farR.toFixed(1) + ' studs)', nearR >= 6 && farR - nearR > 3);

// ---------------------------------------------------------- on the move
console.log('\n== on the move ==');
/* Her owner walks (or runs) straight ahead: where is she, from 3 s in? */
function trail(tags, speed, secs, species) {
  var ww = world(win, { species: species || 'fern', tags: tags, items: {} });
  var me = ww.client.local;
  run(ww, 1.5);
  me.vel = [0, 0, speed];
  var out = { d: [], behind: 0, n: 0, x: [], spd: [], max: 0 };
  run(ww, secs, function (t) {
    if (t < 3) return;
    var f = ww.me(), d = hd(f.pos, me.pos);
    out.max = Math.max(out.max, d);
    out.x.push(f.pos[0] - me.pos[0]);
    out.spd.push(f.speed);
    // her trailing distance is what she keeps when simply following, not
    // off on a whim or scampering to catch up after one
    if (f.whim || f.scamper) return;
    out.n++;
    out.d.push(d);
    if (f.pos[2] < me.pos[2] - 1) out.behind++;
  });
  out.mean = avg(out.d);
  out.behind /= out.n;
  return out;
}
function spread(list) { return Math.max.apply(null, list) - Math.min.apply(null, list); }
function sd(list) {
  var m = avg(list);
  return Math.sqrt(avg(list.map(function (v) { return (v - m) * (v - m); })));
}
function field(list, key) { return list.map(function (r) { return r[key]; }); }
var PACES = [['loyal', 'clingy'], ['cheerful', 'curious'], [], ['shy', 'dreamy']];
var walks = {}, runs = {};
PACES.forEach(function (tags) {
  var key = tags.join('+');
  walks[key] = []; runs[key] = [];
  for (var i = 0; i < 3; i++) {
    walks[key].push(trail(tags, 10, 14));
    runs[key].push(trail(tags, 22, 14));
  }
});
var allWalks = [].concat.apply([], PACES.map(function (t) { return walks[t.join('+')]; }));
var allRuns = [].concat.apply([], PACES.map(function (t) { return runs[t.join('+')]; }));
var walkMean = avg(field(allWalks, 'mean')), runMean = avg(field(allRuns, 'mean'));
check('walking, she trails a natural distance back (6 to 10 studs on average)',
      walkMean >= 6 && walkMean <= 10, walkMean.toFixed(1));
check('...behind them, not alongside or in front', avg(field(allWalks, 'behind')) > 0.8,
      avg(field(allWalks, 'behind')).toFixed(2));
check('running, she trails further back', runMean > walkMean + 1,
      [walkMean.toFixed(1), runMean.toFixed(1)]);
check('...and keeps up (never more than 24 studs behind)', Math.max.apply(null, field(allRuns, 'max')) < 24,
      Math.max.apply(null, field(allRuns, 'max')).toFixed(1));
var clingyAt = avg(field(walks['loyal+clingy'], 'mean')), shyAt = avg(field(walks['shy+dreamy'], 'mean'));
check('a clingy pet trails nearer than a shy dreamer', shyAt - clingyAt > 1.5,
      [clingyAt.toFixed(1), shyAt.toFixed(1)]);
var weave = avg(allWalks.map(function (r) { return spread(r.x); }));
check('her path is no laser line: she meanders across theirs (' + weave.toFixed(1) + ' studs)', weave > 1.5);
var pace = avg(allWalks.map(function (r) { return sd(r.spd); }));
check('...and her pace is her own, not theirs to the stud (varies by ' + pace.toFixed(1) + ')', pace > 0.6);

/* Straight back the way they came -- forward on the stick, then back --
   and she comes round with them, to trail behind them their new way. */
function reverse(tags) {
  var wr = world(win, { species: 'ember', tags: tags, items: {} });
  var rme = wr.client.local, back = 0, n = 0, far = 0, whimAt = -9;
  run(wr, 1.5);
  rme.vel = [0, 0, 10]; run(wr, 4);
  rme.vel = [0, 0, -10];
  run(wr, 7, function (t) {
    // (off on a whim of her own -- a dash ahead, a sniff -- and just after, aside)
    if (wr.me().whim) whimAt = t;
    if (t < 3 || t < whimAt + 1.5) return;
    n++;
    if (wr.me().pos[2] > rme.pos[2] + 1) back++;
    far += hd(wr.me().pos, rme.pos);
  });
  return { n: n, back: back / (n || 1), far: far / (n || 1) };
}
var turned = 0, turns = [];
[['loyal'], [], ['curious', 'dreamy'], ['energetic', 'playful']].forEach(function (tags) {
  // (whims can fill a run: then it says nothing, and she goes again)
  var r = reverse(tags);
  for (var again = 0; again < 4 && r.n < 30; again++) r = reverse(tags);
  turns.push(r.back.toFixed(2) + ' ' + r.far.toFixed(1));
  if (r.n >= 30 && r.back > 0.8 && r.far < 14) turned++;
});
check('they turn straight back the way they came and she comes round with them', turned === 4, turns);

/* Standing about, she fancies a spot on the far side of them: she goes
   round them to get there, not through them. */
var roundNear = 1e9;
for (var r3 = 0; r3 < 6; r3++) {
  var wo = world(win, { species: Pet.ORDER[r3 % 5], tags: [], items: {} });
  var ome = wo.client.local;
  run(wo, 3);
  var fo = wo.me();
  fo.settle = [2 * ome.pos[0] - fo.pos[0], 0, 2 * ome.pos[2] - fo.pos[2]];
  fo.settleT = 0;
  fo.settleFor = 99;
  run(wo, 3, function () {
    if (!CLOSE[wo.me().state]) roundNear = Math.min(roundNear, hd(wo.me().pos, ome.pos));
  });
}
check('she wants to be on their other side and goes round them, not through them', roundNear > 4,
      roundNear.toFixed(2));

/* Her owner turns and sprints straight at her from a little way off: she
   gets out of their way -- with a startled leap aside, as it comes to that. */
var clear = 0, leapt = 0, nears = [];
for (var r2 = 0; r2 < 8; r2++) {
  var wa = world(win, { species: Pet.ORDER[r2 % 5], tags: ['cheerful'], items: {} });
  var ame = wa.client.local;
  run(wa, 3);
  var fa = wa.me(), ax = ame.pos[0] - fa.pos[0], az = ame.pos[2] - fa.pos[2], al = Math.hypot(ax, az);
  ame.pos = [fa.pos[0] + ax / al * 11, 0, fa.pos[2] + az / al * 11];
  ame.vel = [-ax / al * 22, 0, -az / al * 22];
  var near = 1e9, hopped = false;
  run(wa, 1.2, function () {
    var f = wa.me();
    near = Math.min(near, hd(f.pos, ame.pos));
    // (off the ground, and going sideways to their run)
    if (!f.grounded && Math.abs(f.vel[0] * az - f.vel[2] * ax) / al > 5) hopped = true;
  });
  nears.push(near.toFixed(1));
  if (near > 3) clear++;
  if (hopped) leapt++;
}
check('her owner sprints straight at her and she gets out of their way', clear >= 7, nears);
check('...with a startled leap aside', leapt >= 7, leapt + '/8');

/* A stroll with gentle turns: what takes her fancy on the way? */
function outing(tags, secs, species, holding) {
  var ww = world(win, { species: species || 'mochi', tags: tags, items: {} });
  if (holding) {
    ww.client.stowed = false;
    ww.client.currentWeapon = function () { return { name: 'pistol' }; };
  }
  var me = ww.client.local, seen = {}, hot = 0;
  run(ww, 1.5);
  run(ww, secs, function (t) {
    if (holding) shooting(ww, t);
    var a = Math.sin(t * 0.25) * 1.2;
    me.vel = [Math.sin(a) * 9, 0, Math.cos(a) * 9];
    me.yaw = a;
    var f = ww.me();
    if (f.whim) seen[f.whim.kind] = 1;
    if (f.act) seen['act:' + f.act.name] = 1;
    if (t > 1.5 && inLine(ww)) hot++;
  });
  return { seen: seen, hot: hot };
}
var sniffs = 0, darts = 0, shyDarts = 0, kinds = {};
for (var o1 = 0; o1 < 6; o1++) {
  var nose = outing(['curious', 'cheerful', 'chatty'], 40);
  if (nose.seen.sniff && nose.seen['act:sniff']) sniffs++;
  var bold = outing(['playful', 'energetic', 'showoff'], 40, 'ember');
  if (bold.seen.dart) darts++;
  var meek = outing(['shy', 'sleepy', 'loyal'], 40, 'luna');
  if (meek.seen.dart) shyDarts++;
  [nose, bold, meek].forEach(function (r) { Object.keys(r.seen).forEach(function (k) { kinds[k] = 1; }); });
}
check('a curious pet stops to sniff at things by the wayside', sniffs >= 4, sniffs + '/6');
check('a playful one darts on ahead to wait for them', darts >= 3, darts + '/6');
check('...and a shy, sleepy one never does', shyDarts === 0, shyDarts + '/6');
var whims = ['sniff', 'dart', 'dawdle', 'hops', 'race'].filter(function (k) { return kinds[k]; });
check('between them they get up to all sorts on the way (' + whims.join(', ') + ')', whims.length >= 4);

/* Shooting: walking, backing up, strafing, running, stopping and turning
   on the spot -- she keeps out of the line of fire throughout. */
var gw = world(win, { species: 'pixel', tags: ['playful', 'energetic', 'clingy'], items: {} });
gw.client.stowed = false;
gw.client.currentWeapon = function () { return { name: 'pistol' }; };
var gme = gw.client.local, hot = 0, frames = 0, darted = false;
run(gw, 2, function (t) { shooting(gw, t); });
[[0, 10, 0], [0, -8, 0], [8, 0, 0], [0, 0, 0], [0, 22, 0], [0, 0, 0], [0, 0, Math.PI / 2],
 [0, 0, Math.PI], [-9, 0, Math.PI]].forEach(function (leg) {
  gme.vel = [leg[0], 0, leg[1]];
  gme.yaw = leg[2];
  run(gw, 4, function (t) {
    shooting(gw, t);
    if (gw.me().whim && gw.me().whim.kind === 'dart') darted = true;
    if (t < 1.5) return;               // a moment to get out of the way
    frames++;
    if (inLine(gw)) hot++;
  });
});
check('shooting -- walking, backing up, strafing, running, turning -- she stays out of the line of fire',
      hot === 0, hot + '/' + frames);
check('...and never darts out in front of it', !darted);
var guarded = outing(['playful', 'energetic', 'showoff'], 30, 'ember', true);
check('...nor on a stroll with it', guarded.hot === 0 && !guarded.seen.dart, guarded);

// ------------------------------------------------- how her owner moves
console.log('\n== how her owner moves ==');
var copied = 0;
for (var j1 = 0; j1 < 10; j1++) {
  var wj = world(win, { species: 'ember', tags: ['loyal', 'cheerful'], items: {} });
  run(wj, 3);
  var leapt = -1;
  hop(wj.client.local);
  run(wj, 1.2, function (t, dt) {
    fall(wj.client.local, dt);
    if (!wj.me().grounded && leapt < 0) leapt = t;
  });
  if (leapt > 0.05 && leapt < 0.6) copied++;
}
check('her owner jumps and a loyal pet hops too, a beat behind', copied >= 6, copied + '/10');

var skids = 0;
for (var j2 = 0; j2 < 10; j2++) {
  var wsk = world(win, { species: 'luna', tags: ['cheerful', 'brave'], items: {} });
  wsk.client.local.vel = [0, 0, 18];
  run(wsk, 5);
  wsk.client.local.vel = [0, 0, 0];
  var slid = false;
  run(wsk, 0.8, function () {
    var a = wsk.me().act;
    if (a && (a.name === 'skid' || a.name === 'trip')) slid = true;
  });
  if (slid) skids++;
}
check('they stop dead from a run and she skids to a stop', skids >= 6, skids + '/10');

var parties = 0;
for (var j3 = 0; j3 < 10; j3++) {
  var wd = world(win, { species: 'mochi', tags: ['playful', 'energetic', 'cheerful'], items: {} });
  run(wd, 4);
  wd.client.local.vel = [0, 0, 22];
  var party = false;
  run(wd, 1.0, function () {
    var f = wd.me();
    if ((f.act && (f.act.name === 'zoom_spin' || f.act.name === 'fistpump')) || !f.grounded) party = true;
  });
  if (party) parties++;
}
check('they set off at a run and a playful pet celebrates (a spin, a hop)', parties >= 6, parties + '/10');

var lay = 0;
for (var j4 = 0; j4 < 4; j4++) {
  var wl = world(win, { species: 'fern', tags: ['playful', 'dreamy', 'sleepy'], items: {} });
  var lied = false;
  run(wl, 1);
  run(wl, 90, function () {
    if (wl.me().state === 'lie' || (wl.me().state === 'sleep' && wl.me().lying)) lied = true;
  });
  if (lied) lay++;
}
check('left standing about, a dreamy, playful pet sits, then lies down on her tummy', lay >= 3, lay + '/4');

var wv = world(win, { species: 'mochi', tags: ['clingy', 'loyal', 'cheerful'], items: {} });
var cuddled = false, inClose = 1e9, outAgain = null, over = -1;
run(wv, 1);
run(wv, 160, function (t) {
  var f = wv.me(), d = hd(f.pos, wv.client.local.pos);
  if (f.state === 'visit') {
    inClose = Math.min(inClose, d);
    if (d < 3) cuddled = true;
    over = -1;
  } else if (cuddled && outAgain === null) {
    if (over < 0) over = t;
    if (t > over + 4 && !CLOSE[f.state]) outAgain = d;   // a few seconds after
  }
});
check('a clingy pet comes in close on purpose, for a cuddle or a pat', cuddled, inClose.toFixed(1));
check('...not right on top of them', inClose > 1.5, inClose.toFixed(2));
check('...and drifts back out to her spot after', outAgain !== null && outAgain >= 6,
      outAgain === null ? null : outAgain.toFixed(1));

// ------------------------------------------------------------ many pets
console.log('\n== many pets ==');
/* Two dozen pets in one world, their owners strolling and stopping: what
   does each cost a frame?  (Rays are the expensive part in a real map.) */
var crowd = world(win, { species: 'fern', tags: ['playful'], items: {} });
var TAGSETS = [['shy', 'curious'], ['playful', 'energetic'], ['loyal', 'clingy'], ['dreamy'], ['feisty']];
for (var c = 0; c < 23; c++) {
  crowd.client.players[100 + c] = {
    id: 100 + c, name: 'p' + c, pos: [(c % 6) * 14, 0, Math.floor(c / 6) * 14], yaw: 0, anim: 'walk',
    alive: true, health: 100, team: '', slot: 0,
    avatar: { pet: { species: Pet.ORDER[c % 5], tags: TAGSETS[c % TAGSETS.length], items: {} } }
  };
}
run(crowd, 2);
var rays0 = crowd.client.physics.rays, began = Date.now(), steps = 0;
run(crowd, 10, function (t, dt) {
  steps++;
  Object.keys(crowd.client.players).forEach(function (id, i) {
    var p = crowd.client.players[id];
    if (Math.sin(t * 0.5 + i) > 0.4) return;      // standing about for a while
    var a = t * 0.3 + i;
    p.pos[0] += Math.sin(a) * 10 * dt; p.pos[2] += Math.cos(a) * 10 * dt;
    p.yaw = a;
  });
  crowd.client.local.vel = Math.sin(t * 0.7) > 0 ? [0, 0, 10] : [0, 0, 0];
});
var petFrames = steps * Object.keys(crowd.pw.followers).length;
var perRays = (crowd.client.physics.rays - rays0) / petFrames;
var perMs = (Date.now() - began) / petFrames;
check('24 pets in a world, all of them running', Object.keys(crowd.pw.followers).length === 24,
      Object.keys(crowd.pw.followers).length);
check('...each casting a handful of rays a frame, no path searches (' + perRays.toFixed(2) + ')',
      perRays < 6);
check('...and costing well under a millisecond a frame, rig and all (' + perMs.toFixed(3) + ' ms)',
      perMs < 0.5);

var off = world(win, fern);
win.Settings.showPets = false;
run(off, 1);
check('"Show pets" off: no pets at all', !off.me());
win.Settings.showPets = true;

console.log('\n== the Pet Zone ==');
/* The room (static/js/ui/pet_zone.js) runs her through pet.js's library
   by name: every name it asks for has to be there, every act it adds has
   to keep her in one piece, and every treat and toy the server knows has
   to have a model to draw. */
var zone = fs.readFileSync(path.join(ROOT, 'static/js/ui/pet_zone.js'), 'utf8');
var known = Pet.actions();
var asked = {};
(zone.match(/act: '[a-z_]+'/g) || []).forEach(function (m) { asked[m.slice(6, -1)] = 1; });
(zone.match(/act: pick\(\[[^\]]+\]\)/g) || []).forEach(function (m) {
  (m.match(/'[a-z_]+'/g) || []).forEach(function (q) { asked[q.slice(1, -1)] = 1; });
});
['snooze', 'nestle', 'stroked', 'sad_walk', 'float', 'idle'].forEach(function (a) { asked[a] = 1; });
var missing = Object.keys(asked).filter(function (a) { return known.indexOf(a) < 0; });
check('every act the Pet Zone asks for is in the library (' + Object.keys(asked).length + ')',
      Object.keys(asked).length > 30 && !missing.length, missing);
var ZONE_ACTS = ['munch', 'yum', 'nope', 'stroked', 'bliss', 'tickled', 'brushed', 'shake_off', 'catch',
                 'cuddle', 'ready', 'beg', 'tummy', 'nestle', 'wake_up', 'nod_off', 'scratch', 'hop_hello',
                 'sigh', 'mope', 'spicy'];
var broken = [];
ZONE_ACTS.forEach(function (name) {
  if (!(name in Pet.DURATION)) broken.push(name + ': no duration');
  for (var t = 0; t <= 3; t += 0.1) {
    var p = Pet.act(name, t, Math.sin(t * 3));
    Object.keys(p).forEach(function (k) {
      if (typeof p[k] === 'number' && !isFinite(p[k])) broken.push(name + '.' + k + ' at ' + t.toFixed(1));
    });
    if (p.bob > 0.8 || p.squash < 0.75 || p.squash > 1.2) broken.push(name + ' leaps or squashes too far at ' + t.toFixed(1));
    if (Math.abs(p.headYaw) > 1.2 || Math.abs(p.headPitch) > 1.0) broken.push(name + ' turns her head off at ' + t.toFixed(1));
  }
});
check('the Pet Zone acts keep her in one piece, every frame for three seconds', !broken.length, broken.slice(0, 5));
var parts = Pet.build({ species: 'mochi', tags: [] }, { pose: Pet.act('nestle', 1.2) });
check('...and curled up for a nap she is still all there',
      parts.length > 40 && parts.every(function (q) { return q.p.every(isFinite) && q.s.every(isFinite); }));
var care = fs.readFileSync(path.join(ROOT, 'app/models/pet_care.py'), 'utf8');
var ids = [];
['TREAT_ORDER', 'TOY_ORDER'].forEach(function (name) {
  var m = care.match(new RegExp(name + ' = \\[([^\\]]+)\\]'));
  if (m) (m[1].match(/"[a-z]+"/g) || []).forEach(function (q) { ids.push(q.slice(1, -1)); });
});
var unmodelled = ids.filter(function (id) { return !new RegExp('\\n    ' + id + ': ').test(zone); });
check('every treat and toy has a model in the room (' + ids.length + ')', ids.length === 11 && !unmodelled.length,
      unmodelled);

console.log('\n' + '='.repeat(20) + ' ' + passed + ' passed, ' + failed + ' failed ' + '='.repeat(20));
process.exit(failed ? 1 : 0);
