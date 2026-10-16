#!/usr/bin/env node
/* Render pets to a contact sheet, for looking at them.

     node tools/petsheet.js --out pets.png
     node tools/petsheet.js --species fern,luna --actions idle,wave,sit --t 0.6
     node tools/petsheet.js --scale              (each pet beside an avatar)
     node tools/petsheet.js --wear pet_hat_beret,pet_neck_bell --species mochi
     node tools/petsheet.js --angles 0.5,2.6 --zoom head

   Needs the dev server (bash tools/devserver.sh start) for the engine
   scripts; the pets themselves are drawn from static/js/engine/pet.js and
   cosmetics come from the catalogue the market serves. */
'use strict';
var fs = require('fs');
var path = require('path');

function arg(name, fallback) {
  var i = process.argv.indexOf('--' + name);
  if (i < 0) return fallback;
  var v = process.argv[i + 1];
  return v && v.indexOf('--') !== 0 ? v : true;
}

var PORT = arg('port', process.env.BLOCKHAVEN_PORT || '8972');
var OUT = arg('out', path.join(process.cwd(), 'petsheet.png'));

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
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
           '--ignore-gpu-blocklist']
  });
  var page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  page.on('console', function (msg) {
    if (msg.type() === 'error') console.error('[page]', msg.text());
  });
  page.on('pageerror', function (err) { console.error('[page]', err.message); });
  await page.goto('http://127.0.0.1:' + PORT + '/market', { waitUntil: 'load' });
  await page.waitForFunction(function () { return !!(window.Pet && window.Renderer && window.Avatar); });
  var req = {
    species: String(arg('species', 'fern,ember,luna,mochi,pixel')).split(','),
    actions: String(arg('actions', 'idle')).split(','),
    angles: String(arg('angles', '0.45')).split(',').map(Number),
    t: parseFloat(arg('t', '0.5')),
    tile: parseInt(arg('tile', '300'), 10),
    scale: !!arg('scale', false),
    zoom: arg('zoom', ''),
    wear: String(arg('wear', '') === true ? '' : arg('wear', '')).split(',').filter(Boolean),
    colors: arg('colors', '') === true ? '' : arg('colors', ''),
    tags: String(arg('tags', '') === true ? '' : arg('tags', '')).split(',').filter(Boolean)
  };
  var info = await page.evaluate(function (req) {
    var catalogPromise = (window.Thumbs && Thumbs.loadCatalog) ? Thumbs.loadCatalog()
      : Promise.resolve({});
    return catalogPromise.then(function (catalog) {
      var W = req.tile;
      var offscreen = document.createElement('canvas');
      offscreen.width = W * 2; offscreen.height = W * 2;
      var renderer = new Renderer(offscreen, { antialias: true, preserveDrawingBuffer: true });
      var SKY = { top: '#9fc6e8', horizon: '#eef5fb', sun: [0.45, 0.8, 0.35], clouds: 0,
                  tint: '#ffffff' };
      function prep(parts) {
        return parts.map(function (p) {
          if (p.decSlot === undefined && p.decal) p.decSlot = Textures.decal(p.decal);
          return p;
        });
      }
      function shoot(parts, focus, size, angle, tilt) {
        renderer.setSky(SKY);
        renderer.buildStatic([]);
        renderer.beginFrame(0.016);
        parts.forEach(function (p) { renderer.push(p); });
        // a floor, so floating and sitting read as what they are
        renderer.pushRaw('box', 0, -0.05, 0, 0, 0, 0, 14, 0.1, 14, [0.72, 0.8, 0.86], 1, 0, 0,
                         0, null);
        var dist = size / (2 * Math.tan(20 * Math.PI / 180)) * 1.05;
        var eye = [focus[0] + Math.sin(angle) * Math.cos(tilt) * dist,
                   focus[1] + Math.sin(tilt) * dist,
                   focus[2] + Math.cos(angle) * Math.cos(tilt) * dist];
        renderer.setCameraMatrix(eye, focus, 40);
        renderer.render();
        var copy = document.createElement('canvas');
        copy.width = W; copy.height = W;
        copy.getContext('2d').drawImage(offscreen, 0, 0, W, W);
        return copy;
      }
      var root = document.createElement('div');
      root.id = 'sheet';
      root.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;background:#20262e;' +
        'padding:8px;display:grid;gap:6px;font:11px Verdana;color:#e8eef5';
      var cells = 0;
      var colours = null;
      if (req.colors) {
        colours = {};
        req.colors.split(';').forEach(function (kv) {
          var bits = kv.split('=');
          if (bits.length === 2) colours[bits[0]] = bits[1];
        });
      }
      var items = {};
      req.wear.forEach(function (id) {
        var it = catalog[id];
        if (!it) return;
        items[it.slot] = { item_id: id, slot: it.slot, data: it.data };
      });
      var cols = req.angles.length * req.actions.length;
      if (cols < 3) cols = Math.min(5, req.species.length * cols);
      root.style.gridTemplateColumns = 'repeat(' + cols + ', ' + W + 'px)';
      req.species.forEach(function (sp) {
        var pet = { species: sp, colors: colours || undefined, items: items, tags: req.tags };
        req.actions.forEach(function (action) {
          var pose = Pet.act(action, req.t);
          var s = Pet.species(pet);
          if (s.eyes && pose.eyes === 'open') pose.eyes = s.eyes;
          if (s.mouth && pose.mouth === 'smile') pose.mouth = s.mouth;
          req.angles.forEach(function (angle) {
            var parts = prep(Pet.build(pet, { position: req.scale ? [1.9, 0, 0.6] : [0, 0, 0],
                                              yaw: 0, pose: pose, time: req.t }));
            var focus = [0, 1.35, 0], size = 3.3;
            if (req.zoom === 'head') { focus = [0, 2.05, 0]; size = 1.7; }
            if (req.scale) {
              var av = Avatar.build({ body_type: 'female', colors: {}, items: {} },
                                    { position: [-1.0, 0, 0], yaw: 0,
                                      pose: Avatar.pose('idle', 0, 0, {}) });
              parts = parts.concat(av);
              focus = [0.4, 2.8, 0]; size = 6.6;
            }
            var cell = document.createElement('div');
            cell.style.cssText = 'position:relative;width:' + W + 'px;height:' + (W + 14) + 'px';
            cell.appendChild(shoot(parts, focus, size, angle, 0.12));
            var label = document.createElement('div');
            label.textContent = sp + ' / ' + action + ' / ' + angle;
            cell.appendChild(label);
            root.appendChild(cell);
            cells++;
          });
        });
      });
      document.body.appendChild(root);
      window.scrollTo(0, 0);
      return { count: cells, height: root.scrollHeight, width: root.scrollWidth };
    });
  }, req);
  await page.setViewportSize({ width: Math.max(400, info.width + 20),
                               height: Math.max(300, info.height + 20) });
  var sheet = await page.$('#sheet');
  await sheet.screenshot({ path: OUT });
  console.log('rendered ' + info.count + ' pet view(s) -> ' + OUT);
  await browser.close();
})().catch(function (err) { console.error(err); process.exit(1); });
