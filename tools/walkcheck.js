#!/usr/bin/env node
/* Walk check: can a person walk away from every spawn point on a map?

   Loads the client's own character physics (static/js/game/physics.js)
   headless and, from each spawn it is given, holds "forward" for a few
   seconds the way static/js/game/client.js drives a body: the same
   acceleration, gravity and jump.  Walking into something it jumps; still
   blocked, it turns a quarter and carries on, so a pad that faces a wall
   still finds the door.  It reports, per spawn:

     embedded   the body overlapped a solid where it was put down
     grounded   it was standing on something within the first half second
     reach      the farthest it got from where it started (x/z)
     drop       how far below the start it ever went
     path       its position every 1/20 s -- what the client would have
                sent the server -- so the caller can replay it there

     node tools/walkcheck.js payload.json > result.json

   payload.json: {"parts": [...], "kill_y": -60, "seconds": 4,
                  "spawns": [{"p": [x, y, z], "yaw": 0, "label": "..."}]}

   tools/relaytests.py (group "walk") is the caller. */
'use strict';

var fs = require('fs');
var path = require('path');
var vm = require('vm');

var ROOT = path.resolve(__dirname, '..');
var source = fs.readFileSync(path.join(ROOT, 'static/js/game/physics.js'), 'utf8');
var sandbox = { window: {}, Math: Math, console: console };
vm.createContext(sandbox);
vm.runInContext(source, sandbox, { filename: 'physics.js' });
var Physics = sandbox.window.Physics;

var data = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
var physics = new Physics({ parts: data.parts, kill_y: data.kill_y });
var SPEED = 22, GRAVITY = 62, JUMP = 34, DT = 1 / 60, SEND = 3;

function walk(spawn) {
  var local = { pos: spawn.p.slice(), vel: [0, 0, 0], grounded: false, yaw: spawn.yaw || 0 };
  var start = spawn.p.slice();
  var embedded = physics.blocked(start[0], start[1], start[2]);
  var grounded = false, reach = 0, lowest = start[1], blockedFor = 0;
  var trail = [];
  var frames = Math.round((data.seconds || 4) / DT);
  for (var f = 0; f < frames; f++) {
    var sin = Math.sin(local.yaw), cos = Math.cos(local.yaw);
    var accel = local.grounded ? 90 : 26;
    local.vel[0] += (sin * SPEED - local.vel[0]) * Math.min(1, accel * DT / SPEED);
    local.vel[2] += (cos * SPEED - local.vel[2]) * Math.min(1, accel * DT / SPEED);
    if (blockedFor > 0.05 && local.grounded) {
      local.vel[1] = JUMP;
      local.grounded = false;
    }
    local.vel[1] -= GRAVITY * DT;
    if (local.vel[1] < -140) local.vel[1] = -140;
    var before = [local.pos[0], local.pos[2]];
    var result = physics.move(local, DT);
    local.grounded = result.grounded;
    if (local.grounded && f * DT < 0.5) grounded = true;
    var moved = Math.hypot(local.pos[0] - before[0], local.pos[2] - before[1]);
    blockedFor = moved < SPEED * DT * 0.25 ? blockedFor + DT : 0;
    if (blockedFor > 0.35) {
      local.yaw += Math.PI / 2;
      blockedFor = 0;
    }
    reach = Math.max(reach, Math.hypot(local.pos[0] - start[0], local.pos[2] - start[2]));
    lowest = Math.min(lowest, local.pos[1]);
    if (f % SEND === SEND - 1) {
      trail.push([+local.pos[0].toFixed(3), +local.pos[1].toFixed(3), +local.pos[2].toFixed(3),
                  local.grounded ? 1 : 0, +local.yaw.toFixed(3)]);
    }
    if (local.pos[1] < (data.kill_y === undefined ? -60 : data.kill_y)) break;
  }
  return { label: spawn.label || '', start: start, embedded: embedded, grounded: grounded,
           reach: +reach.toFixed(2), drop: +(start[1] - lowest).toFixed(2), path: trail };
}

process.stdout.write(JSON.stringify((data.spawns || []).map(walk)));
