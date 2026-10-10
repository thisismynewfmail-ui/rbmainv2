#!/usr/bin/env node
/* Where the body is, in an item slot's own coordinates.

     node tools/bodyframe.js back      # hat | hair | back | usable

   Builds the male and the female character the way the game does, puts a
   one-hundredth-stud probe at [0,0,0] of the slot, and prints the bounding
   box of the head, neck, torso, hips, arms and legs relative to it -- the
   numbers to keep an item clear of.  (The parts are rounded boxes: the
   corners are about 0.28 in from these boxes.) */
'use strict';

var path = require('path');
var fs = require('fs');
var ROOT = path.resolve(__dirname, '..');

global.window = global;
global.document = undefined;
function load(rel) {
  new Function('window', 'globalThis', fs.readFileSync(path.join(ROOT, rel), 'utf8'))(global, global);
}
['static/js/engine/gl.js', 'static/js/engine/geometry.js', 'static/js/engine/shapes.js'].forEach(load);
global.Textures = { decal: function () { return null; }, emblems: [] };
load('static/js/engine/avatar.js');

var slot = process.argv[2] || 'hat';
['male', 'female'].forEach(function (build) {
  var pose = Avatar.pose('idle', 0, 0, { body_type: build });
  var opts = { position: [0, 0, 0], yaw: 0, pose: pose, holding: null, pitch: 0, time: 0 };
  var bare = Avatar.build({ body_type: build, colors: {}, items: {} }, opts);
  var probe = { item_id: 'probe', slot: slot,
                data: { parts: [{ t: 'box', p: [0, 0, 0], s: [0.01, 0.01, 0.01], c: '#fff' }] } };
  var desc = { body_type: build, colors: {}, items: {} };
  if (slot === 'usable') opts.holding = probe; else desc.items[slot] = probe;
  var built = Avatar.build(desc, opts);
  var origin = built.slice(bare.length)[0].p;
  console.log('== ' + build + ' (' + slot + ' space)');
  bare.filter(function (p) { return p.k && p.k !== 'badge' && p.k !== 'hair'; }).forEach(function (p) {
    var lo = [0, 1, 2].map(function (i) { return (p.p[i] - p.s[i] / 2 - origin[i]).toFixed(2); });
    var hi = [0, 1, 2].map(function (i) { return (p.p[i] + p.s[i] / 2 - origin[i]).toFixed(2); });
    console.log('  ' + (p.k + '        ').slice(0, 8) + ' x ' + lo[0] + '..' + hi[0] +
                '   y ' + lo[1] + '..' + hi[1] + '   z ' + lo[2] + '..' + hi[2]);
  });
});
