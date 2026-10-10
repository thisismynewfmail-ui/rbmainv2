#!/usr/bin/env node
/* Stills from a crate opening, for looking at the show frame by frame: the
   key going home in the lock, the turn, the rattle, the lid and the light.

     node tools/cratestage.js --series newyear_2022 --out /tmp/stage
     node tools/cratestage.js --series halloween --at 1.5,2.2,2.6,3.3,4.3

   Runs the market page's own Crates.open in a headless Chromium against a
   running server (BLOCKHAVEN_PORT or --port, 8972 by default), with the
   server's answer stubbed so nothing is bought or opened for real.  Saves
   one PNG per moment (seconds into the show) as <out>/<series>_<t>.png. */
'use strict';

var path = require('path');
var fs = require('fs');

function arg(name, fallback) {
  var i = process.argv.indexOf('--' + name);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

var PORT = arg('port', process.env.BLOCKHAVEN_PORT || '8972');
var SERIES = arg('series', 'classic');
var OUT = arg('out', process.cwd());
var AT = arg('at', '1.4,2.2,2.5,2.9,3.6,4.4').split(',').map(Number);

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
           '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required']
  });
  var page = await browser.newPage({ viewport: { width: 1100, height: 720 } });
  page.on('console', function (msg) { if (msg.type() === 'error') console.error('[page]', msg.text()); });
  page.on('pageerror', function (err) { console.error('[page]', err.message); });
  // the answer comes back late on purpose, so the intro plays out in full
  await page.route('**/api/crates/open', async function (route) {
    await new Promise(function (r) { setTimeout(r, 400); });
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      ok: true, series: { id: SERIES, name: 'Test' }, win_index: 30,
      reel: Array.from({ length: 40 }, function () { return { item_id: 'hat_red_cap', grade: 'rare' }; }),
      item: { item_id: 'hat_red_cap', name: 'Red Cap', tier: 'normal', grade: 'rare' }
    }) });
  });
  await page.goto('http://127.0.0.1:' + PORT + '/market', { waitUntil: 'load' });
  await page.waitForFunction(function () { return !!(window.Crates && window.Renderer); });
  await page.evaluate(function (series) { window.Crates.open({ series: series }); }, SERIES);
  await page.waitForFunction(function () { return !!(window.Crates.stage && window.Crates.stage.scene); });
  fs.mkdirSync(OUT, { recursive: true });
  for (var i = 0; i < AT.length; i++) {
    var when = AT[i];
    // the show's own clock (it slows down with the frame rate, not the wall)
    await page.waitForFunction(function (t) { return window.Crates.stage.t >= t; }, when, { timeout: 120000 });
    await page.evaluate(function () { window.Crates.stage.paused = true; });
    var file = path.join(OUT, SERIES + '_' + when.toFixed(1) + '.png');
    await page.screenshot({ path: file });
    await page.evaluate(function () { window.Crates.stage.paused = false; });
    console.log('saved', file);
  }
  await browser.close();
})().catch(function (e) { console.error(e); process.exit(1); });
