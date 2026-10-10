#!/usr/bin/env node
/* Screenshots from inside a world, for looking at what gear does in play.

     python3 tools/gearkit.py builderman_x use_ny24_roman_candle use_ny26_ball_drop
     node tools/gameshot.js --user builderman_x --world blackout_relay \
          --do "slot:0,fire,wait:0.3,shot,slot:1,fire,wait:1.2,shot" --out /tmp/shots

   Signs in (--user/--pass, "blockhaven" by default) in a headless Chromium,
   joins the world, switches to the third-person camera, and runs the steps:
     slot:N       draw hotbar slot N (0-4)
     fire         one shot / swing / use, aimed where the camera looks
     hold:S       hold the trigger for S seconds (beams, automatics)
     look:Y,P     set the view yaw/pitch (radians)
     wait:S       let S seconds of play pass
     shot         save a PNG (<out>/<n>.png)
     holdshot:S   hold the trigger S seconds and save a PNG while it is down
     dump         print the gear state the page holds
   Needs a running server: BLOCKHAVEN_PORT or --port (8972 by default). */
'use strict';

var path = require('path');
var fs = require('fs');

function arg(name, fallback) {
  var i = process.argv.indexOf('--' + name);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

var PORT = arg('port', process.env.BLOCKHAVEN_PORT || '8972');
var USER = arg('user', 'builderman_x');
var PASS = arg('pass', 'blockhaven');
var WORLD = arg('world', 'blackout_relay');
var STEPS = arg('do', 'shot').split(',');
var OUT = arg('out', process.cwd());
var BASE = 'http://127.0.0.1:' + PORT;

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
  var context = await browser.newContext({ viewport: { width: 1280, height: 760 } });
  var page = await context.newPage();
  page.on('pageerror', function (err) { console.error('[page]', err.message); });
  page.on('console', function (msg) { if (msg.type() === 'error') console.error('[page]', msg.text()); });
  await page.goto(BASE + '/login', { waitUntil: 'load' });
  await page.fill('form[action="/login"] input[name=username]', USER);
  await page.fill('form[action="/login"] input[name=password]', PASS);
  await Promise.all([page.waitForNavigation({ waitUntil: 'load' }),
                     page.click('form[action="/login"] [type=submit]')]);
  await page.goto(BASE + '/' + WORLD, { waitUntil: 'load' });
  await page.waitForFunction(function () {
    var c = window.gameClient;
    return !!(c && c.map && c.myId && c.local && c.local.alive);
  }, null, { timeout: 90000 });
  // third person, no menus, the page as if focused and locked
  await page.evaluate(function () {
    var c = window.gameClient;
    c.thirdPerson = true;
    c.paused = false;
    c.mouseGrabbed = true;
    var loading = document.getElementById('loading');
    if (loading) loading.classList.add('hide');
    document.querySelectorAll('.menu, #pause, #pause-menu').forEach(function (el) { el.style.display = 'none'; });
  });
  fs.mkdirSync(OUT, { recursive: true });
  var shots = 0;
  for (var i = 0; i < STEPS.length; i++) {
    var step = STEPS[i].trim();
    var name = step.split(':')[0];
    var value = step.indexOf(':') >= 0 ? step.slice(step.indexOf(':') + 1) : '';
    if (name === 'slot') {
      await page.evaluate(function (n) { window.gameClient.selectSlot(n); }, parseInt(value, 10));
      await page.waitForTimeout(400);
    } else if (name === 'fire') {
      await page.evaluate(function () {
        var c = window.gameClient;
        c.nextFire = 0;
        c.tryFire();
      });
    } else if (name === 'hold') {
      var until = Date.now() + parseFloat(value) * 1000;
      while (Date.now() < until) {
        await page.evaluate(function () { var c = window.gameClient; c.tryFire(); });
        await page.waitForTimeout(90);
      }
    } else if (name === 'look') {
      var yp = value.split(/[;/]/).map(Number);
      await page.evaluate(function (v) {
        var c = window.gameClient;
        c.local.yaw = v[0];
        c.local.pitch = v[1] || 0;
      }, yp);
    } else if (name === 'wait') {
      await page.waitForTimeout(parseFloat(value) * 1000);
    } else if (name === 'dump') {
      console.log(await page.evaluate(function () {
        var c = window.gameClient, g = c.gear;
        return JSON.stringify({ pos: c.local.pos, deps: g ? g.deps : null,
                                minions: g ? Object.keys(g.minions).length : 0,
                                status: g ? g.status : null, projectiles: c.projectiles });
      }));
    } else if (name === 'holdshot') {
      // a shot taken with the trigger still down (beams)
      var end = Date.now() + parseFloat(value || '0.8') * 1000;
      while (Date.now() < end) {
        await page.evaluate(function () { window.gameClient.tryFire(); });
        await page.waitForTimeout(80);
      }
      await page.evaluate(function () { window.gameClient.tryFire(); });
      shots += 1;
      var hfile = path.join(OUT, String(shots).padStart(2, '0') + '.png');
      await page.screenshot({ path: hfile });
      console.log('saved', hfile);
    } else if (name === 'shot') {
      shots += 1;
      var file = path.join(OUT, String(shots).padStart(2, '0') + '.png');
      await page.screenshot({ path: file });
      console.log('saved', file);
    }
  }
  await browser.close();
})().catch(function (e) { console.error(e); process.exit(1); });
