#!/usr/bin/env node
/* Contact sheets of catalogue items, for looking at them rather than at
   their numbers.

   Renders items with the site's own engine (the same renderer, rig, shapes
   and textures the market and the game use) in a headless Chromium, against
   a running server, and saves one PNG:

     node tools/itemsheet.js --items hat_crown,hat_halo --out /tmp/sheet.png
     node tools/itemsheet.js --event christmas_2023 --out /tmp/xmas.png
     node tools/itemsheet.js --prefix hat_ny22_ --views worn

   Wearables are drawn on BOTH builds (male, female) from the front three
   quarters and from the side, which is where a brim that clips a jaw or a
   cape that sinks into a back shows up; weapons are drawn on their own and
   in the hand; crates and keys on their own.  --views picks which:
   "worn" (on the body), "alone" (the item on its own), or "both".

   Needs playwright (installed globally in the dev image) and a server:
   BLOCKHAVEN_PORT or --port says where (8972 by default). */
'use strict';

var path = require('path');
var fs = require('fs');

function arg(name, fallback) {
  var i = process.argv.indexOf('--' + name);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

var PORT = arg('port', process.env.BLOCKHAVEN_PORT || '8972');
var OUT = arg('out', path.join(process.cwd(), 'itemsheet.png'));
var VIEWS = arg('views', 'both');
var TILE = parseInt(arg('tile', '220'), 10);
var COLS = parseInt(arg('cols', '0'), 10);
var EFFECT = arg('effect', '');

function loadPlaywright() {
  var tries = ['playwright', '/opt/node22/lib/node_modules/playwright'];
  for (var i = 0; i < tries.length; i++) {
    try { return require(tries[i]); } catch (e) { /* next */ }
  }
  throw new Error('playwright is not installed');
}

(async function main() {
  var pw = loadPlaywright();
  var browser = await pw.chromium.launch({
    executablePath: fs.existsSync('/opt/pw-browsers/chromium') ? undefined : undefined,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
           '--ignore-gpu-blocklist']
  });
  var page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  page.on('console', function (msg) {
    if (msg.type() === 'error') console.error('[page]', msg.text());
  });
  await page.goto('http://127.0.0.1:' + PORT + '/market', { waitUntil: 'load' });
  await page.waitForFunction(function () { return !!(window.Thumbs && window.Renderer && window.Avatar); });
  var request = {
    items: (arg('items', '') || '').split(',').filter(Boolean),
    event: arg('event', ''), prefix: arg('prefix', ''), slot: arg('slot', ''),
    views: VIEWS, tile: TILE, cols: COLS, effect: EFFECT
  };
  var info = await page.evaluate(function (req) {
    return Thumbs.loadCatalog().then(function (catalog) {
      var ids = req.items.slice();
      Object.keys(catalog).forEach(function (id) {
        var it = catalog[id];
        if (req.event && it.event === req.event && ids.indexOf(id) < 0) ids.push(id);
        if (req.prefix && id.indexOf(req.prefix) === 0 && ids.indexOf(id) < 0) ids.push(id);
      });
      if (req.slot) ids = ids.filter(function (id) { return catalog[id] && catalog[id].slot === req.slot; });
      ids = ids.filter(function (id) { return catalog[id]; });

      var W = req.tile;
      var offscreen = document.createElement('canvas');
      offscreen.width = W * 2; offscreen.height = W * 2;
      var renderer = new Renderer(offscreen, { antialias: true, preserveDrawingBuffer: true });
      var particles = new Particles(renderer.gl);
      var SKY = { top: '#9fc6e8', horizon: '#eef5fb', sun: [0.45, 0.8, 0.35], clouds: 0, tint: '#ffffff' };

      function prep(raw) {
        return (raw || []).map(function (piece) {
          return { t: piece.t || 'box', p: piece.p.slice(), s: piece.s.slice(), c: piece.c, r: piece.r,
                   m: piece.m, a: piece.a, dw: piece.dw,
                   decSlot: piece.decSlot || (piece.decal ? Textures.decal(piece.decal) : null) };
        });
      }
      function bounds(parts) {
        var lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9];
        parts.forEach(function (p) {
          var r = Math.max(p.s[0], p.s[1], p.s[2]) * 0.5;
          for (var k = 0; k < 3; k++) {
            lo[k] = Math.min(lo[k], p.p[k] - r * 0.8);
            hi[k] = Math.max(hi[k], p.p[k] + r * 0.8);
          }
        });
        return { lo: lo, hi: hi };
      }
      function shoot(parts, frame, angle, tilt, pad, effect, anchor) {
        renderer.setSky(SKY);
        renderer.buildStatic([]);
        renderer.beginFrame(0.016);
        parts.forEach(function (p) { renderer.push(p); });
        var b = bounds(frame && frame.length ? frame : parts);
        var mid = [(b.lo[0] + b.hi[0]) / 2, (b.lo[1] + b.hi[1]) / 2, (b.lo[2] + b.hi[2]) / 2];
        var size = Math.max(b.hi[0] - b.lo[0], b.hi[1] - b.lo[1], b.hi[2] - b.lo[2]);
        var dist = size * (pad || 1.15) / (2 * Math.tan(20 * Math.PI / 180)) + size * 0.5;
        var eye = [mid[0] + Math.sin(angle) * Math.cos(tilt) * dist, mid[1] + Math.sin(tilt) * dist,
                   mid[2] + Math.cos(angle) * Math.cos(tilt) * dist];
        renderer.setCameraMatrix(eye, mid, 40);
        if (effect && Thumbs.effects && Thumbs.effects[effect]) {
          particles.count = 0; particles.emitters = {};
          for (var s = 0; s < 120; s++) {
            particles.setEmitter('fx', Thumbs.effects[effect], anchor || mid);
            particles.update(1 / 60);
          }
        }
        renderer.render();
        if (effect) particles.draw(renderer);
        var copy = document.createElement('canvas');
        copy.width = W; copy.height = W;
        copy.getContext('2d').drawImage(offscreen, 0, 0, W, W);
        return copy;
      }
      function mannequin(body) {
        return {
          colors: { head: '#f5cd30', torso: '#7e8a96', hips: '#5d6670', left_arm: '#f5cd30',
                    right_arm: '#f5cd30', left_leg: '#5d6670', right_leg: '#5d6670' },
          body_type: body, items: { face: { item_id: 'face_smile', slot: 'face',
                                            data: (catalog.face_smile || {}).data } }
        };
      }
      function wear(item, body) {
        var d = mannequin(body);
        if (item.slot === 'usable') return d;
        d.items[item.slot] = { item_id: item.id, slot: item.slot, data: item.data, tier: 'normal' };
        return d;
      }
      var root = document.createElement('div');
      root.id = 'sheet';
      root.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;background:#20262e;padding:8px;' +
        'display:grid;gap:6px;font:11px Verdana;color:#e8eef5';
      var tiles = [];
      ids.forEach(function (id) {
        var it = catalog[id];
        var shots = [];
        var wearable = { hat: 1, hair: 1, face: 1, shirt: 1, pants: 1, belt: 1, back: 1 }[it.slot];
        if ((req.views === 'both' || req.views === 'alone') && !wearable) {
          var alone = prep(it.data && it.data.parts);
          if (alone.length) {
            var ang = it.slot === 'usable' ? -1.15 : -0.6;
            shots.push(shoot(alone, null, ang, it.slot === 'usable' ? 0.42 : 0.32, 1.1, req.effect, null));
            shots.push(shoot(alone, null, ang + Math.PI * 0.75, 0.25, 1.1, '', null));
          }
        }
        if ((req.views === 'both' || req.views === 'worn') && (wearable || it.slot === 'usable')) {
          ['male', 'female'].forEach(function (body) {
            var d = wear(it, body);
            var holding = it.slot === 'usable' ? it : null;
            var pose = Avatar.pose(holding ? 'idle' : 'idle', 0, 0, d);
            var parts = Avatar.build(d, { position: [0, 0, 0], yaw: 0, pose: pose, holding: holding,
                                          time: 0 });
            var head = parts.filter(function (p) {
              return p.k === 'head' || p.k === 'hair' || p.p[1] > 4.0;
            });
            var frame = it.slot === 'hat' || it.slot === 'hair' || it.slot === 'face' ? head
              : (it.slot === 'belt' ? parts.filter(function (p) { return p.k === 'hips'; }) : null);
            var anchor = it.slot === 'hat' ? Avatar.hatAnchor([0, 0, 0], 0, it) : null;
            shots.push(shoot(parts, frame, 0.55, 0.12, it.slot === 'face' ? 1.25 : 1.12, req.effect, anchor));
            var side = it.slot === 'back' ? Math.PI * 0.8 : (it.slot === 'usable' ? -0.9 : 1.45);
            shots.push(shoot(parts, frame, side, 0.10, 1.12, '', anchor));
          });
        }
        tiles.push({ id: id, name: it.name, slot: it.slot, shots: shots });
      });
      var perRow = req.cols || (tiles.length && tiles[0].shots.length >= 4 ? 4 : 6);
      var cols = Math.max(1, perRow * Math.max(1, Math.max.apply(null, tiles.map(function (t) {
        return t.shots.length || 1; }))));
      cols = Math.min(cols, Math.floor(1580 / (W + 6)));
      root.style.gridTemplateColumns = 'repeat(' + cols + ', ' + W + 'px)';
      tiles.forEach(function (t) {
        t.shots.forEach(function (c, i) {
          var cell = document.createElement('div');
          cell.style.cssText = 'position:relative;width:' + W + 'px;height:' + (W + 14) + 'px';
          cell.appendChild(c);
          var label = document.createElement('div');
          label.textContent = (i === 0 ? t.id : '') ;
          label.style.cssText = 'white-space:nowrap;overflow:hidden;text-overflow:ellipsis';
          cell.appendChild(label);
          root.appendChild(cell);
        });
      });
      document.body.appendChild(root);
      window.scrollTo(0, 0);
      return { count: tiles.length, cols: cols, height: root.scrollHeight, width: root.scrollWidth };
    });
  }, request);
  if (!info.count) {
    console.error('no items matched');
    await browser.close();
    process.exit(1);
  }
  await page.setViewportSize({ width: Math.max(400, info.width + 20), height: Math.max(300, info.height + 20) });
  var sheet = await page.$('#sheet');
  await sheet.screenshot({ path: OUT });
  console.log('rendered ' + info.count + ' item(s) -> ' + OUT);
  await browser.close();
})().catch(function (err) { console.error(err); process.exit(1); });
