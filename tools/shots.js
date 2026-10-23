#!/usr/bin/env node
/* Pictures of the event worlds without a server: an area from any camera,
   a world-page thumbnail, or a still from an area's arrival sequence.

     python3 tools/shots.py rail_rivals dustbowl                  # area views
     node tools/shots.js --job /path/job.json --out /tmp/shots    # (what it runs)

   A job is JSON: { "kind": "map" | "thumb" | "intro", "scripts": [...],
   "map": {area payload}, "views": [[eye, target, fov], ...],
   "thumbs": [kind...], "scenes": [[sceneId, t, info]...],
   "width": 1280, "height": 720 }.
   Renders with the engine's own renderer in headless Chromium (SwiftShader)
   and writes <out>/<name>.png for each view. */
'use strict';

var fs = require('fs');
var path = require('path');

function arg(name, fallback) {
  var i = process.argv.indexOf('--' + name);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

function loadPlaywright() {
  var tries = ['playwright', '/opt/node22/lib/node_modules/playwright'];
  for (var i = 0; i < tries.length; i++) {
    try { return require(tries[i]); } catch (e) { /* next */ }
  }
  throw new Error('playwright is not installed');
}

var ROOT = path.resolve(__dirname, '..');
var ENGINE = ['static/js/engine/gl.js', 'static/js/engine/geometry.js',
              'static/js/engine/shapes.js', 'static/js/engine/textures.js',
              'static/js/engine/world_emblems.js', 'static/js/engine/renderer.js',
              'static/js/engine/avatar.js', 'static/js/engine/pet.js',
              'static/js/engine/zombies.js', 'static/js/engine/particles.js'];

(async function main() {
  var job = JSON.parse(fs.readFileSync(arg('job'), 'utf8'));
  var out = arg('out', process.cwd());
  fs.mkdirSync(out, { recursive: true });
  var pw = loadPlaywright();
  var browser = await pw.chromium.launch({
    executablePath: fs.existsSync('/opt/pw-browsers/chromium') ? undefined : undefined,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader',
           '--ignore-gpu-blocklist']
  });
  var W = job.width || 1280, H = job.height || 720;
  var page = await (await browser.newContext({ viewport: { width: W, height: H } })).newPage();
  page.on('pageerror', function (err) { console.error('[page]', err.message); });
  page.on('console', function (msg) { if (msg.type() === 'error') console.error('[page]', msg.text()); });
  await page.setContent('<html><body style="margin:0;background:#000"><canvas id="c" width="' +
                        W + '" height="' + H + '" style="width:' + W + 'px;height:' + H +
                        'px;display:block"></canvas><div id="game-root"><div class="hud" ' +
                        'style="position:fixed;inset:0"></div></div></body></html>');
  // a world's thumbnail script registers with thumbs.js, so that comes first
  var scripts = ENGINE.concat(job.kind === 'thumb' ? ['static/js/ui/thumbs.js'] : [])
    .concat(job.scripts || []);
  for (var i = 0; i < scripts.length; i++) {
    await page.addScriptTag({ path: path.join(ROOT, scripts[i]) });
  }
  var shots = [];
  if (job.kind === 'map') {
    await page.evaluate(function (map) {
      var canvas = document.getElementById('c');
      var r = new Renderer(canvas, { antialias: true });
      r.far = 1400;
      r.setSky(map.sky);
      r.setAmbient(map.ambient);
      var parts = map.parts.slice();
      var dyn = (map.markers || {}).dynamic || {};
      Object.keys(dyn).forEach(function (k) { if (dyn[k].on) parts = parts.concat(dyn[k].parts); });
      r.buildStatic(parts);
      window.__r = r;
    }, job.map);
    for (var v = 0; v < job.views.length; v++) {
      var data = await page.evaluate(function (view) {
        var r = window.__r;
        r.resize();
        r.beginFrame(0.016);
        r.setCameraMatrix(view[0], view[1], view[2] || 60);
        r.render();
        return document.getElementById('c').toDataURL('image/png');
      }, job.views[v]);
      shots.push([job.names ? job.names[v] : 'view' + v, data]);
    }
  } else if (job.kind === 'thumb') {
    for (var t = 0; t < job.thumbs.length; t++) {
      var img = await page.evaluate(function (kind) {
        var c = document.createElement('canvas');
        c.width = 960; c.height = 540;
        document.body.appendChild(c);
        Thumbs.renderWorld(c, kind, null);
        return c.toDataURL('image/png');
      }, job.thumbs[t]);
      shots.push(['thumb_' + job.thumbs[t], img]);
    }
  } else if (job.kind === 'intro') {
    await page.addScriptTag({ path: path.join(ROOT, 'static/js/game/area_intro.js') });
    for (var k = 0; k < (job.post || []).length; k++) {
      await page.addScriptTag({ path: path.join(ROOT, job.post[k]) });
    }
    for (var s = 0; s < job.scenes.length; s++) {
      var frame = await page.evaluate(function (spec) {
        var c = document.createElement('canvas');
        c.width = 1280; c.height = 720;
        document.body.appendChild(c);
        if (!AreaIntro.still(c, spec[0], spec[1], spec[2] || {}, 7)) return '';
        return c.toDataURL('image/png');
      }, job.scenes[s]);
      shots.push(['intro_' + job.scenes[s][0] + '_' + job.scenes[s][1], frame]);
    }
  }
  shots.forEach(function (shot) {
    if (!shot[1]) { console.error('nothing drawn for ' + shot[0]); return; }
    var file = path.join(out, shot[0] + '.png');
    fs.writeFileSync(file, Buffer.from(shot[1].split(',')[1], 'base64'));
    console.log(file);
  });
  await browser.close();
})().catch(function (err) { console.error(err); process.exit(1); });
