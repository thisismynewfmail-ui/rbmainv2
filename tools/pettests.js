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

/* A flat world at y = 0, with an optional wall: an axis-aligned box. */
function physics(walls) {
  walls = walls || [];
  return {
    rayDistance: function (o, d, max) {
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

// ------------------------------------------------------------ following
console.log('\n== following ==');
var fern = { species: 'fern', name: 'Sprout', tags: ['cheerful', 'loyal', 'curious'], items: {} };
// settling first, with a pet who will not wander off in the middle of it
var w = world(win, { species: 'fern', name: 'Sprout', tags: ['cheerful', 'loyal', 'clingy'], items: {} });
run(w, 1);
check('she appears at her owner\'s side', w.me() && hd(w.me().pos, w.client.local.pos) < 4.5);
w.client.local.vel = [0, 0, 15];
w.client.local.anim = 'run';
var maxGap = 0;
run(w, 6, function () { if (w.me()) maxGap = Math.max(maxGap, hd(w.me().pos, w.client.local.pos)); });
check('she keeps up with a running owner', hd(w.me().pos, w.client.local.pos) < 9,
      hd(w.me().pos, w.client.local.pos).toFixed(1));
check('...never falling far behind', maxGap < 12, maxGap.toFixed(1));
check('...running, not walking', w.me().speed > 10, w.me().speed);
w.client.local.vel = [0, 0, 0];
w.client.local.anim = 'idle';
run(w, 2);
check('when they stop she settles close by', hd(w.me().pos, w.client.local.pos) < 5,
      hd(w.me().pos, w.client.local.pos).toFixed(1));
check('...and comes to rest', w.me().speed < 1.5, w.me().speed);
var dy = Math.atan2(w.client.local.pos[0] - w.me().pos[0], w.client.local.pos[2] - w.me().pos[2]);
var facing = Math.abs(((dy - (w.me().yaw + w.me().head[0])) + Math.PI * 3) % (Math.PI * 2) - Math.PI);
check('...and looks at them', facing < 0.6, facing.toFixed(2));
check('she is never inside her owner', hd(w.me().pos, w.client.local.pos) > 1.2);

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
check('a long way off and she reappears at their side', hd(w.me().pos, w.client.local.pos) < 5,
      hd(w.me().pos, w.client.local.pos).toFixed(1));

console.log('\n== a ledge ==');
var w2 = world(win, fern, { walls: [{ min: [-20, 0, 6], max: [20, 5, 40] }] });
run(w2, 1);
w2.client.local.pos = [0, 5, 10];
var maxY = 0;
run(w2, 4, function () { if (w2.me()) maxY = Math.max(maxY, w2.me().pos[1]); });
check('her owner jumps up on a block and she hops up after them',
      w2.me().pos[1] > 4.5 && hd(w2.me().pos, w2.client.local.pos) < 6,
      { y: w2.me().pos[1].toFixed(2), d: hd(w2.me().pos, w2.client.local.pos).toFixed(1) });

console.log('\n== a wall ==');
var w3 = world(win, fern, { walls: [{ min: [-3, 0, 4], max: [3, 30, 5] }] });
run(w3, 1);
w3.client.local.pos = [0, 0, 12];
run(w3, 5);
check('a wall in the way and she finds her way round (or over)',
      hd(w3.me().pos, w3.client.local.pos) < 7, hd(w3.me().pos, w3.client.local.pos).toFixed(1));

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
      w4.me().state !== 'mourn' && hd(w4.me().pos, w4.client.local.pos) < 6,
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
run(gun, 4);
var f = gun.me(), me = gun.client.local;
var along = (f.pos[0] - me.pos[0]) * Math.sin(me.yaw) + (f.pos[2] - me.pos[2]) * Math.cos(me.yaw);
var across = (f.pos[0] - me.pos[0]) * Math.cos(me.yaw) - (f.pos[2] - me.pos[2]) * Math.sin(me.yaw);
check('she stays out of the line of fire', !(along > 0 && Math.abs(across) < along * 0.4 + 0.5),
      { along: along.toFixed(2), across: across.toFixed(2) });

var off = world(win, fern);
win.Settings.showPets = false;
run(off, 1);
check('"Show pets" off: no pets at all', !off.me());
win.Settings.showPets = true;

console.log('\n' + '='.repeat(20) + ' ' + passed + ' passed, ' + failed + ' failed ' + '='.repeat(20));
process.exit(failed ? 1 : 0);
