/* Whodunit -- the Game View half of the murder mystery
   (app/game/worlds/whodunit.py).

   The server deals the roles and decides every stab, shot and pickup; this
   shows them.  The role is revealed in a card at the start of the case and
   kept in a chip at the top of the screen.  Clues float where they turned
   up, with a beam of light to find them by; a body lies where it fell, in
   chalk; a disgraced detective's revolver glints on the floor for a hero.
   Thrown knives fly, and stick.  The case file fills along the top, and its
   hints arrive one after another: where the murderer was seen, their
   footprints glowing on the floor, three suspects, a glimpse.

   Each place's twist: the manor's storm puts the lights out and splits the
   sky with lightning; the express runs through a tunnel (with the
   mountainside streaming past the windows the rest of the time); the
   hotel's masquerade puts every guest in the same mask and cloak, no names;
   the liner sails into fog.

   Four arrival scenes are registered at the bottom. */
(function (global) {
  'use strict';
  var Arena = global.Arena || { register: function () {} };

  var ROLES = {
    murderer: { name: 'MURDERER', colour: '#ff4a4a',
                line: 'Leave nobody standing. 1 draws the knife (out of sight!), R throws it.' },
    detective: { name: 'DETECTIVE', colour: '#5aa8ff',
                 line: 'Shoot the murderer. Shoot anybody else and you are finished.' },
    hero: { name: 'HERO', colour: '#ffd27a',
            line: "The detective's revolver is yours now. Finish the case." },
    innocent: { name: 'INNOCENT', colour: '#7aea8a',
                line: 'Pick up clues for the case file. Stay alive. Trust nobody.' }
  };
  var CLUE_NAMES = ['a sealed letter', 'a bloody glove', 'a pocket watch', 'a torn photograph',
                    'a brass key'];
  var HINTS = {
    seen: ['SEEN', 'The murderer was seen'],
    trail: ['TRAIL', "The murderer's footprints are glowing"],
    suspects: ['SUSPECTS', 'Three suspects'],
    glimpse: ['GLIMPSE', 'The murderer stands out']
  };
  var TWISTS = {
    storm: { warn: 'THE STORM IS GETTING WORSE', warnSub: 'The lights are flickering...',
             on: 'THE LIGHTS ARE OUT', onSub: 'Nobody can see who is who in the dark',
             off: 'The lights come back on', colour: '#9ab0ff', chip: 'LIGHTS OUT' },
    tunnel: { warn: 'TUNNEL AHEAD', warnSub: 'Get off the roof!', on: 'IN THE TUNNEL',
              onSub: 'Pitch dark -- and nobody left on the roof', off: 'Out of the tunnel',
              colour: '#ffb35a', chip: 'TUNNEL' },
    masks: { warn: 'THE BAND STRIKES UP', warnSub: 'Masks on...', on: 'THE MASQUERADE',
             onSub: 'Every guest in the same mask -- no names', off: 'Masks off',
             colour: '#e8c860', chip: 'MASQUERADE' },
    fog: { warn: 'FOG AHEAD', warnSub: 'The foghorn sounds', on: 'IN THE FOG',
           onSub: 'You cannot see past arm\'s length', off: 'The fog lifts',
           colour: '#c8d8e8', chip: 'FOG' }
  };
  var CLUE_REACH = 3.2;
  var GUN_REACH = 3.6;

  function rgb(hex) {
    var n = parseInt(String(hex).slice(1), 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
  }
  function esc(text) {
    return String(text == null ? '' : text).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function now() { return performance.now() / 1000; }
  function hash(n) { var x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }
  function darker(hex, k) {
    var c = rgb(hex);
    function h(v) { return ('0' + Math.round(Math.max(0, Math.min(1, v)) * 255).toString(16)).slice(-2); }
    return '#' + h(c[0] * k) + h(c[1] * k) + h(c[2] * k);
  }

  /* Boxes and friends in a local frame (x across, z ahead) turned by yaw:
     [kind, x, y, z, sx, sy, sz, colour, material, rx, extraYaw]. */
  function drawParts(renderer, list, p, yaw, alpha) {
    var c = Math.cos(yaw), s = Math.sin(yaw);
    for (var i = 0; i < list.length; i++) {
      var q = list[i];
      var x = q[1], z = q[3];
      renderer.pushRaw(q[0], p[0] + x * c + z * s, p[1] + q[2], p[2] - x * s + z * c,
                       q[9] || 0, yaw + (q[10] || 0), 0, q[4], q[5], q[6], rgb(q[7]),
                       alpha === undefined ? 1 : alpha, 0, q[8] || 0, 0, null);
    }
  }

  // ------------------------------------------------------------ the props
  var CLUE_PARTS = [
    // a sealed letter
    [['box', 0, 0, 0, 1.3, 0.08, 0.9, '#f2ead8'], ['cyl', 0, 0.06, 0, 0.36, 0.06, 0.36, '#b81e2a']],
    // a bloody glove
    [['rbox', 0, 0, 0, 0.9, 0.36, 1.3, '#6a1a1a'], ['rbox', 0.32, 0, 0.62, 0.3, 0.3, 0.5, '#6a1a1a'],
     ['rbox', -0.1, 0, 0.72, 0.5, 0.3, 0.4, '#7a2020']],
    // a pocket watch
    [['cyl', 0, 0, 0, 1.0, 0.22, 1.0, '#d8b040', 1, 1.5708], ['cyl', 0, 0, 0.12, 0.82, 0.04, 0.82,
      '#f8f4e8', 0, 1.5708], ['cyl', 0, 0.62, 0, 0.26, 0.26, 0.12, '#d8b040', 1, 1.5708]],
    // a torn photograph
    [['box', 0, 0, 0, 1.1, 1.3, 0.06, '#f2ead8'], ['box', 0, 0.06, 0.04, 0.86, 0.9, 0.02, '#8a6a4a']],
    // a brass key
    [['box', 0, 0, 0.3, 0.2, 0.2, 1.2, '#c8a040', 1], ['cyl', 0, 0, -0.5, 0.7, 0.2, 0.7, '#c8a040', 1],
     ['box', 0.2, 0, 0.75, 0.24, 0.2, 0.18, '#c8a040', 1]]
  ];
  var BODY_PARTS = [
    ['box', 0, 0.55, 0, 2.0, 1.0, 2.6, '#7a7a84'],
    ['rbox', 0, 0.62, 2.1, 1.3, 1.1, 1.3, '#c8c0b8'],
    ['box', 1.45, 0.45, 0.4, 0.9, 0.8, 2.4, '#7a7a84'],
    ['box', -1.45, 0.45, 0.2, 0.9, 0.8, 2.4, '#7a7a84'],
    ['box', 0.55, 0.45, -2.55, 0.95, 0.85, 2.6, '#4a4a56'],
    ['box', -0.55, 0.45, -2.55, 0.95, 0.85, 2.6, '#4a4a56']
  ];
  var CHALK = [
    ['box', 0, 0.03, 3.05, 3.4, 0.03, 0.18, '#f4f4f4'], ['box', 0, 0.03, -4.1, 2.8, 0.03, 0.18, '#f4f4f4'],
    ['box', 2.05, 0.03, -0.5, 0.18, 0.03, 7.2, '#f4f4f4'], ['box', -2.05, 0.03, -0.5, 0.18, 0.03, 7.2, '#f4f4f4']
  ];
  var GUN_PARTS = [
    ['box', 0, 0.22, 0.55, 0.2, 0.2, 1.4, '#5a5e66', 1], ['box', 0, 0.3, -0.1, 0.5, 0.48, 0.55, '#6a6e76', 1],
    ['box', 0, 0.2, -0.75, 0.32, 0.3, 0.85, '#5a3a24'], ['box', 0, 0.38, 1.18, 0.06, 0.12, 0.06, '#c8a040']
  ];
  var KNIFE_PARTS = [
    ['box', 0, 0, 0.55, 0.08, 0.3, 1.3, '#d8dce4', 1], ['box', 0, 0, -0.4, 0.2, 0.32, 0.7, '#3a2418'],
    ['box', 0, 0, -0.02, 0.5, 0.14, 0.14, '#a8a8a8', 1]
  ];

  // ============================================================ plugin
  Arena.register('whodunit', function (arena) {
    var client = arena.client;
    var centre = [0, 0, 0], extra = {}, twistKind = '';
    var wd = { case: 0, goal: 0, prev: 0, hints: [], alive: 0, guests: 0, twist: '', on: false,
               left: 0, gun: false };
    var ax = {};
    var role = '', partners = [];
    var bodyNames = {};                      // body id -> name
    var flying = {};                         // knife id -> {p, v, at, by}
    var stuck = [];                          // {p, yaw, until}
    var steps = [];                          // {p, yaw, at, side}
    var glimpse = { ids: [], until: 0 };
    var seen = null;                         // {p, where, until}
    var suspects = [];
    var tw = { on: false, kind: '', until: 0, warnUntil: 0 };
    var dark = 0;                            // 0..1, eased
    var fogK = 0;                            // 0..1, eased
    var nextBolt = 0, thunderAt = 0, flashUntil = 0;
    var savedFar = 0, baseSky = null, baseAmbient = null;
    var clackAt = 0;
    var reveal = null, veil = null, maskVeil = null;
    var lastCase = 0;

    function local(p) { return [p[0] + centre[0], p[1], p[2] + centre[2]]; }
    function myPos() { return client.local.pos; }
    function inPlay() { return arena.phase === 'active' && !arena.me.out && client.local.alive; }
    function amMurderer() { return role === 'murderer'; }
    function armed() { return role === 'detective' || role === 'hero'; }
    function masked() { return tw.on && tw.kind === 'masks'; }
    function audible(p) {
      if (!p) return 1;
      var me = myPos();
      var d = Math.hypot(p[0] - me[0], p[1] - me[1], p[2] - me[2]);
      return Math.max(0.1, Math.min(1, 1.15 - d / 120));
    }
    function play(name, p, vol) { client.audio.play(name, { volume: (vol || 1) * audible(p) }); }
    function playerPos(id) {
      if (id === client.myId) return myPos();
      var p = client.players[id];
      return p ? p.pos : null;
    }
    function nameOf(id) {
      if (id === client.myId) return BH.user.name;
      var p = client.players[id];
      return p ? p.name : '';
    }

    // --------------------------------------------------------- overlays
    function overlay(id, css) {
      var node = document.getElementById(id);
      if (node) return node;
      node = document.createElement('div');
      node.id = id;
      node.style.cssText = 'position:fixed;left:0;top:0;right:0;bottom:0;pointer-events:none;' + (css || '');
      (document.querySelector('#game-root .hud') || document.body).appendChild(node);
      return node;
    }
    function ensureNodes() {
      if (!veil) veil = overlay('wd-veil', 'z-index:5;opacity:0;transition:opacity .4s;');
      if (!maskVeil) {
        maskVeil = overlay('wd-mask', 'z-index:6;opacity:0;transition:opacity .6s;' +
          'background:radial-gradient(ellipse 15% 11% at 39% 47%, transparent 92%, rgba(0,0,0,0) 100%),' +
          'radial-gradient(ellipse 15% 11% at 61% 47%, transparent 92%, rgba(0,0,0,0) 100%);');
        maskVeil.innerHTML = '<svg viewBox="0 0 160 90" preserveAspectRatio="none" style="width:100%;height:100%">' +
          '<path fill="rgba(14,8,22,0.86)" fill-rule="evenodd" d="M0 0H160V90H0Z ' +
          'M50 34 C58 26 72 28 76 40 C72 52 58 54 50 46 C46 42 46 38 50 34Z ' +
          'M110 34 C102 26 88 28 84 40 C88 52 102 54 110 46 C114 42 114 38 110 34Z"/>' +
          '<path fill="none" stroke="#e8c860" stroke-width="0.8" d="M50 34 C58 26 72 28 76 40 C72 52 58 54 50 46 C46 42 46 38 50 34Z ' +
          'M110 34 C102 26 88 28 84 40 C88 52 102 54 110 46 C114 42 114 38 110 34Z"/></svg>';
      }
      if (!reveal) {
        reveal = overlay('wd-reveal', 'z-index:30;display:flex;align-items:center;justify-content:center;' +
          'flex-direction:column;opacity:0;transition:opacity .5s;font-family:Georgia,serif;text-align:center;');
      }
    }
    function showReveal(r, partnersList) {
      ensureNodes();
      var spec = ROLES[r] || ROLES.innocent;
      var who = partnersList && partnersList.length
        ? '<div style="margin-top:14px;font:600 18px Verdana,sans-serif;color:#ffb0a0">Your partner' +
          (partnersList.length > 1 ? 's' : '') + ': ' + partnersList.map(esc).join(', ') + '</div>' : '';
      reveal.style.background = 'radial-gradient(ellipse at center, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.25) 70%, rgba(0,0,0,0) 100%)';
      reveal.innerHTML = '<div style="font:700 20px Verdana,sans-serif;letter-spacing:6px;color:#e8dcc0">YOU ARE THE</div>' +
        '<div style="font:900 92px Georgia,serif;letter-spacing:10px;color:' + spec.colour +
        ';text-shadow:0 0 30px ' + spec.colour + ',0 4px 0 #000">' + spec.name + '</div>' +
        '<div style="max-width:720px;font:600 20px Verdana,sans-serif;color:#f4e6c8;margin-top:6px">' +
        esc(spec.line) + '</div>' + who;
      reveal.style.opacity = '1';
      clearTimeout(reveal._t);
      reveal._t = setTimeout(function () { reveal.style.opacity = '0'; }, 4200);
    }

    function roleChip() {
      if (!client.myTeam || arena.phase === 'intermission' || !role) { arena.setRole(''); return; }
      if (arena.me.out) {
        arena.setRole('<b style="color:#c8c8d0">DEAD</b> &bull; you can only talk to the dead now', 'out');
        return;
      }
      var spec = ROLES[role] || ROLES.innocent;
      var bits = '<b style="color:' + spec.colour + '">' + spec.name + '</b>';
      if (amMurderer()) {
        var drawn = !!arena.me.drawn;
        bits += ' &bull; knife <b style="color:' + (drawn ? '#ff6a5a' : '#9aa4b0') + '">' +
          (drawn ? 'OUT -- everybody can see it' : 'hidden') + '</b>';
        var cool = arena.me['throw'] || 0;
        bits += ' &bull; R throw ' + (cool > 0 ? '<b>' + Math.ceil(cool) + 's</b>' : '<b style="color:#ffb35a">ready</b>');
        if (partners.length) bits += ' &bull; with ' + partners.map(esc).join(', ');
      } else if (armed()) {
        var reload = arena.me.reload || 0;
        bits += ' &bull; revolver ' + (reload > 0 ? 'reloading <b>' + reload.toFixed(1) + 's</b>'
          : '<b style="color:#9ecbff">loaded</b>') + ' &bull; only the murderer';
      } else {
        bits += ' &bull; clues: <b style="color:#e8c860">' + (arena.me.clues || 0) + '</b>';
      }
      arena.setRole(bits, role === 'murderer' ? 'red' : (armed() ? 'blue' : ''));
    }

    // ---------------------------------------------------------- the sky
    function captureSky() {
      var map = client.map || {};
      baseSky = map.sky || null;
      baseAmbient = map.ambient || '#a0a8b8';
    }
    function applyLight() {
      var r = client.renderer;
      if (!r || !baseSky) return;
      var k = dark;
      if (now() < flashUntil) k = 0;
      if (k > 0.02) {
        r.setSky({ top: darker(baseSky.top || '#203040', 1 - 0.85 * k),
                   horizon: darker(baseSky.horizon || '#405060', 1 - 0.85 * k),
                   sun: baseSky.sun, clouds: baseSky.clouds, tint: darker(baseSky.tint || '#ffffff', 1 - 0.7 * k) });
        r.setAmbient(darker(baseAmbient, 1 - 0.8 * k));
      } else {
        r.setSky(baseSky);
        r.setAmbient(baseAmbient);
      }
      if (fogK > 0.01) {
        if (!savedFar) savedFar = r.far || 900;
        r.far = savedFar + (70 - savedFar) * fogK;
        var g = 0.66;
        r.fogColor = [g * 0.95, g, g * 1.05];
      } else if (savedFar) {
        r.far = savedFar;
        savedFar = 0;
        r.setSky(baseSky);
      }
    }

    // ------------------------------------------------------------ map
    function loadMap(map) {
      var mk = (map && map.markers) || {};
      centre = mk.centre || [0, 0, 0];
      extra = mk.extra || {};
      twistKind = extra.twist || '';
      reset();
      captureSky();
      applyLight();
    }
    function reset() {
      flying = {}; stuck = []; steps = []; bodyNames = {};
      glimpse = { ids: [], until: 0 }; seen = null; suspects = [];
      tw = { on: false, kind: twistKind, until: 0, warnUntil: 0 };
      dark = 0; fogK = 0; lastCase = 0;
      ax = {};
      if (maskVeil) maskVeil.style.opacity = '0';
    }

    function applyState(s) {
      if (!s) return;
      var was = wd.on;
      wd = s;
      if (s.twist) {
        tw.kind = s.twist;
        if (s.on && !was) tw.until = now() + (s.left || 6);
        tw.on = !!s.on;
      }
    }

    // ------------------------------------------------------- messages
    function twistMessage(msg) {
      var spec = TWISTS[msg.twist] || TWISTS.storm;
      tw.kind = msg.twist;
      if (msg.k === 'twist_warn') {
        tw.warnUntil = now() + (msg['in'] || 3);
        arena.banner(spec.warn, spec.warnSub || '', 'area', 2600);
        if (msg.twist === 'storm') play('wd_thunder', null, 0.5);
        else if (msg.twist === 'tunnel') play('wd_whistle', null, 0.9);
        else if (msg.twist === 'masks') play('wd_waltz', null, 0.7);
        else if (msg.twist === 'fog') play('wd_foghorn', null, 0.9);
        return;
      }
      if (msg.on) {
        tw.on = true;
        tw.until = now() + (msg['for'] || 6);
        arena.banner(spec.on, spec.onSub || '', 'area', 2600);
        if (msg.twist === 'storm') { play('wd_thunder', null, 1); flashUntil = now() + 0.15; nextBolt = now() + 1.2; }
        if (msg.twist === 'tunnel') play('wd_rumble', null, 1);
        if (msg.twist === 'masks') play('wd_waltz', null, 0.9);
        if (msg.twist === 'fog') play('wd_foghorn', null, 0.6);
      } else {
        tw.on = false;
        client.hud.toast(spec.off);
      }
    }

    var messages = {
      wds: function (msg) { applyState((msg.s || {}).wd); },
      wdx: function (msg) {
        var k = msg.k;
        if (k === 'role') {
          role = msg.role || '';
          partners = msg.partners || [];
          showReveal(role, partners);
          play(role === 'murderer' ? 'wd_sting' : 'wd_chime', null, 0.8);
          roleChip();
        } else if (k === 'swing') {
          play('wd_swish', playerPos(msg.id), 0.8);
        } else if (k === 'throw') {
          flying[msg.id] = { p: msg.p.slice(), v: msg.v.slice(), at: now(), by: msg.by };
          play('wd_whirr', msg.p, 0.9);
        } else if (k === 'stick') {
          var f = flying[msg.id];
          delete flying[msg.id];
          var yaw = f ? Math.atan2(f.v[0], f.v[2]) : 0;
          stuck.push({ p: msg.p, yaw: yaw, until: now() + 8 });
          play(msg.hit ? 'wd_stab' : 'wd_thunk', msg.p, 0.9);
        } else if (k === 'cool') {
          // the cooldown itself comes in the per-player state
        } else if (k === 'shot') {
          client.tracers.push({ a: msg.a, b: msg.b, t: 0, c: rgb('#ffe2a0') });
          if (client.particles) client.particles.burst('impact', msg.b);
          if (msg.id !== client.myId) play('wd_bang', msg.a, 1);
        } else if (k === 'caught') {
          arena.banner('CASE CLOSED', esc(msg.by) + ' shot ' + esc(msg.who) + (msg.hero ? ' -- a hero!' : '') +
            ' -- the murderer', 'go', 4200);
          play('wd_solved', null, 1);
        } else if (k === 'misfire') {
          arena.banner('THE WRONG MAN', 'You shot ' + esc(msg.who) + ', who was innocent. You are disgraced.', 'red', 4200);
          play('wd_sting', null, 1);
        } else if (k === 'disgraced') {
          arena.banner('THE WRONG MAN', esc(msg.who) + ' shot ' + esc(msg.victim) + ' -- an innocent. The revolver is on the floor!', 'red', 4200);
          play('wd_sting', null, 0.7);
        } else if (k === 'body') {
          bodyNames[msg.id] = msg.name;
          if (msg.pid === client.myId) {
            arena.banner('YOU WERE MURDERED', 'You can only talk to the dead now', 'red', 3600);
          } else {
            client.hud.toast('A body: <b>' + esc(msg.name) + '</b>', 'bad');
          }
          play(msg.w === 'knife' ? 'wd_scream' : 'wd_bang', msg.p, 1);
        } else if (k === 'gun') {
          arena.banner('THE REVOLVER IS DOWN', armed() || amMurderer() ? '' : 'Pick it up and be the hero', 'area', 3000);
          play('wd_clink', msg.p, 1);
        } else if (k === 'gun_taken') {
          client.hud.toast('Somebody picked up the revolver');
        } else if (k === 'armed') {
          role = 'hero';
          arena.banner('YOU ARE THE HERO', 'Shoot the murderer -- and only the murderer', 'go', 3600);
          play('wd_chime', null, 1);
          roleChip();
        } else if (k === 'burned') {
          client.hud.toast('You burned a clue before anybody saw it', 'good');
          play('wd_burn', null, 0.8);
        } else if (k === 'clue') {
          if (msg.burn) return;
          if (msg.by === client.myId) {
            client.hud.toast('You found a clue! The case file has <b>' + (msg.case || 0) + '</b>', 'good');
            play('wd_clue', null, 1);
          } else {
            play('wd_clue', null, 0.25);
          }
        } else if (k === 'hint') {
          hintArrived(msg);
        } else if (k === 'hint_m') {
          var h = HINTS[msg.hint] || ['HINT', ''];
          arena.banner('THE CASE FILE HAS A HINT', h[1] + ' -- careful', 'red', 3200);
          play('wd_sting', null, 0.5);
        } else if (k === 'step') {
          var side = steps.length % 2 ? 1 : -1;
          steps.push({ p: msg.p, yaw: msg.yaw || 0, at: now(), side: side });
          if (steps.length > 90) steps.shift();
        } else if (k === 'twist_warn' || k === 'twist') {
          twistMessage(msg);
        } else if (k === 'reveal') {
          // the end card shows the roles
        }
      }
    };

    function hintArrived(msg) {
      var h = HINTS[msg.hint] || ['HINT', ''];
      var sub = h[1];
      if (msg.hint === 'seen') {
        sub = 'The murderer was seen in <strong style="color:#fff">' + esc(msg.where || 'the house') + '</strong>';
        if (msg.p) seen = { p: msg.p, where: msg.where, until: now() + 9 };
      } else if (msg.hint === 'trail') {
        sub = "The murderer's footprints are glowing -- follow them";
      } else if (msg.hint === 'suspects') {
        suspects = msg.names || [];
        sub = 'Suspects: <strong style="color:#ffb0a0">' + suspects.map(esc).join(', ') + '</strong>';
      } else if (msg.hint === 'glimpse') {
        glimpse = { ids: msg.ids || [], until: now() + (msg['for'] || 6) };
        sub = 'The murderer is glowing red for a few seconds -- look!';
      }
      arena.banner('CASE FILE: ' + h[0], sub, 'go', 4200);
      play('wd_hint', null, 1);
    }

    // ------------------------------------------------------------ draw
    function drawClues(renderer, time) {
      (ax.cl || []).forEach(function (c) {
        var bob = Math.sin(time * 2.2 + c[0]) * 0.25;
        var p = [c[1], c[2] + 1.5 + bob, c[3]];
        drawParts(renderer, CLUE_PARTS[c[4] % CLUE_PARTS.length], p, time * 1.4 + c[0]);
        renderer.pushRaw('cyl', c[1], c[2] + 4.0, c[3], 0, 0, 0, 1.3, 8.0, 1.3, rgb('#ffd27a'),
                         0.12 + 0.04 * Math.sin(time * 3 + c[0]), 0, 2, 0, null);
        renderer.pushRaw('cyl', c[1], c[2] + 0.04, c[3], 0, 0, 0, 2.4, 0.04, 2.4, rgb('#ffd27a'),
                         0.35, 0, 2, 0, null);
      });
    }
    function drawBodies(renderer) {
      (ax.bd || []).forEach(function (b) {
        var p = [b[1], b[2], b[3]];
        renderer.pushRaw('cyl', p[0], p[1] + 0.03, p[2], 0, 0, 0, 3.6, 0.04, 3.2, rgb('#5a0a10'), 0.88, 0, 0, 0, null);
        drawParts(renderer, CHALK, p, b[4] || 0, 0.9);
        drawParts(renderer, BODY_PARTS, p, b[4] || 0);
      });
    }
    function drawGun(renderer, time) {
      if (!ax.gn) return;
      var p = ax.gn;
      drawParts(renderer, GUN_PARTS, p, time * 0.8);
      renderer.pushRaw('cyl', p[0], p[1] + 5, p[2], 0, 0, 0, 1.8, 10, 1.8, rgb('#ffd27a'),
                       0.16 + 0.06 * Math.sin(time * 5), 0, 2, 0, null);
    }
    function drawKnives(renderer, dt, time) {
      var t = now();
      Object.keys(flying).forEach(function (id) {
        var f = flying[id];
        var k = t - f.at;
        if (k > 1.6) { delete flying[id]; return; }
        var p = [f.p[0] + f.v[0] * k, f.p[1] + f.v[1] * k - 7 * k * k, f.p[2] + f.v[2] * k];
        var yaw = Math.atan2(f.v[0], f.v[2]);
        var c = Math.cos(yaw), s = Math.sin(yaw);
        KNIFE_PARTS.forEach(function (q) {
          renderer.pushRaw(q[0], p[0] + q[3] * s, p[1], p[2] + q[3] * c, time * 22, yaw, 0, q[4], q[5], q[6],
                           rgb(q[7]), 1, 0, q[8] || 0, 0, null);
        });
      });
      stuck = stuck.filter(function (s) { return s.until > t; });
      stuck.forEach(function (sk) {
        var a = Math.min(1, (sk.until - t) / 1.5);
        drawParts(renderer, KNIFE_PARTS, sk.p, sk.yaw, a);
      });
    }
    function drawSteps(renderer) {
      var t = now();
      steps = steps.filter(function (s) { return t - s.at < 14; });
      steps.forEach(function (s) {
        var a = Math.max(0, 1 - (t - s.at) / 14);
        var c = Math.cos(s.yaw), sn = Math.sin(s.yaw);
        var x = s.side * 0.55;
        renderer.pushRaw('box', s.p[0] + x * c, s.p[1] + 0.05, s.p[2] - x * sn, 0, s.yaw, 0, 0.6, 0.06, 1.1,
                         rgb('#ff2a4a'), 0.35 + 0.55 * a, 0, 2, 0, null);
      });
    }
    function drawGlimpse(renderer, time) {
      var t = now();
      if (t < glimpse.until) {
        glimpse.ids.forEach(function (id) {
          var p = playerPos(id);
          if (!p) return;
          renderer.pushRaw('cyl', p[0], p[1] + 3.2, p[2], 0, 0, 0, 4.2, 7.0, 4.2, rgb('#ff2a3a'),
                           0.28 + 0.12 * Math.sin(time * 10), 0, 2, 0, null);
          renderer.pushRaw('cyl', p[0], p[1] + 30, p[2], 0, 0, 0, 1.2, 50, 1.2, rgb('#ff2a3a'), 0.35, 0, 2, 0, null);
        });
      }
      if (seen && t < seen.until) {
        var k = (seen.until - t) / 9;
        renderer.pushRaw('cyl', seen.p[0], seen.p[1] + 0.06, seen.p[2], 0, 0, 0, 14 + 6 * Math.sin(time * 4),
                         0.06, 14 + 6 * Math.sin(time * 4), rgb('#ff5a3a'), 0.45 * k, 0, 2, 0, null);
        renderer.pushRaw('cyl', seen.p[0], seen.p[1] + 20, seen.p[2], 0, 0, 0, 1.4, 40, 1.4, rgb('#ff5a3a'),
                         0.3 * k, 0, 2, 0, null);
      }
    }

    // the express: the mountainside streaming past, and the tunnel
    function drawJourney(renderer, time) {
      var motion = extra.motion, speed = extra.speed || 0, train = extra.train;
      if (!motion || !speed || !train) return;
      var x0 = train[0] - 220, x1 = train[1] + 220, len = x1 - x0;
      var shift = (time * speed) % len;
      if (tw.on && tw.kind === 'tunnel') {
        // the bore, close round the train, its ribs and lamps going by
        var mid = local([(train[0] + train[1]) / 2, 0, 0]);
        var length = train[1] - train[0] + 140;
        renderer.pushRaw('box', mid[0], 14, mid[2] + 14, 0, 0, 0, length, 28, 1.0, rgb('#2a2622'), 1, 0, 0, 0, null);
        renderer.pushRaw('box', mid[0], 14, mid[2] - 14, 0, 0, 0, length, 28, 1.0, rgb('#2a2622'), 1, 0, 0, 0, null);
        renderer.pushRaw('box', mid[0], 26.5, mid[2], 0, 0, 0, length, 1.0, 29, rgb('#221e1a'), 1, 0, 0, 0, null);
        for (var i = 0; i < 26; i++) {
          var x = x0 + ((i * len / 26 - shift) % len + len) % len;
          var p = local([x, 0, 0]);
          renderer.pushRaw('box', p[0], 14, p[2] + 13.4, 0, 0, 0, 1.2, 26, 0.4, rgb('#3a342e'), 1, 0, 0, 0, null);
          renderer.pushRaw('box', p[0], 14, p[2] - 13.4, 0, 0, 0, 1.2, 26, 0.4, rgb('#3a342e'), 1, 0, 0, 0, null);
          if (i % 3 === 0) {
            renderer.pushRaw('box', p[0], 18, p[2] + 13.2, 0, 0, 0, 0.8, 0.8, 0.2, rgb('#ffb35a'), 1, 0, 2, 0, null);
            renderer.pushRaw('box', p[0], 18, p[2] - 13.2, 0, 0, 0, 0.8, 0.8, 0.2, rgb('#ffb35a'), 1, 0, 2, 0, null);
          }
        }
        return;
      }
      // telegraph poles by the line, pines and drifts further out
      for (var j = 0; j < 22; j++) {
        var xj = x0 + ((j * len / 22 - shift) % len + len) % len;
        var q = local([xj, 0, 0]);
        renderer.pushRaw('box', q[0], 9, q[2] - 16, 0, 0, 0, 0.6, 18, 0.6, rgb('#3a2a1e'), 1, 0, 0, 0, null);
        renderer.pushRaw('box', q[0], 17, q[2] - 16, 0, 0, 0, 0.3, 0.3, 3.6, rgb('#3a2a1e'), 1, 0, 0, 0, null);
      }
      for (var n = 0; n < 34; n++) {
        var far = 1.0 + hash(n) * 0.6;
        var xn = x0 + ((n * len / 34 - shift * far) % len + len) % len;
        var side = n % 2 ? 1 : -1;
        var z = side * (26 + hash(n + 7) * 34);
        var pn = local([xn, 0, z]);
        var h = 10 + hash(n + 3) * 12;
        renderer.pushRaw('cone', pn[0], h / 2, pn[2], 0, 0, 0, h * 0.55, h, h * 0.55, rgb('#1e3a2a'), 1, 0, 0, 0, null);
        renderer.pushRaw('cone', pn[0], h * 0.86, pn[2], 0, 0, 0, h * 0.3, h * 0.36, h * 0.3, rgb('#e8eef4'), 1, 0, 0, 0, null);
      }
    }

    // the liner: foam along the hull and the wake astern
    function drawSea(renderer, time) {
      if (extra.sea === undefined) return;
      var y = extra.sea + 0.08;
      for (var i = 0; i < 40; i++) {
        var side = i % 2 ? 1 : -1;
        var x = -150 + ((i * 9 - time * 22) % 300 + 300) % 300;
        var p = local([x, y, side * (23 + hash(i) * 2.5)]);
        renderer.pushRaw('box', p[0], y, p[2], 0, 0, 0, 5 + hash(i + 2) * 4, 0.06, 1.2, rgb('#e8f2f8'),
                         0.55, 0, 0, 0, null);
      }
      for (var k = 0; k < 18; k++) {
        var d = ((k * 14 + time * 22) % 252);
        var spread = 4 + d * 0.18;
        var pk = local([-122 - d, y, (hash(k) - 0.5) * spread * 2]);
        renderer.pushRaw('box', pk[0], y, pk[2], 0, hash(k + 9), 0, 6, 0.06, 1.6, rgb('#dce8f0'),
                         Math.max(0, 0.5 - d / 500), 0, 0, 0, null);
      }
    }

    function stepTwist(dt, time) {
      var kind = tw.kind;
      var t = now();
      var wantDark = 0, wantFog = 0;
      if (tw.on && (kind === 'storm' || kind === 'tunnel')) wantDark = kind === 'tunnel' ? 0.95 : 0.85;
      if (!tw.on && kind === 'storm' && t < tw.warnUntil) wantDark = 0.3 * (Math.sin(time * 20) > 0.6 ? 1 : 0);
      if (tw.on && kind === 'fog') wantFog = 1;
      dark += (wantDark - dark) * Math.min(1, dt * 4);
      fogK += (wantFog - fogK) * Math.min(1, dt * 1.5);
      if (kind === 'storm' && tw.on && t > nextBolt) {
        nextBolt = t + 1.6 + Math.random() * 3.4;
        flashUntil = t + 0.12;
        arena.flashScreen('rgba(220,230,255,0.75)', 160);
        thunderAt = t + 0.3 + Math.random() * 0.9;
      }
      if (thunderAt && t > thunderAt) { thunderAt = 0; play('wd_thunder', null, 0.9); }
      applyLight();
      if (veil) {
        if (kind === 'tunnel' && tw.on) {
          veil.style.background = 'radial-gradient(ellipse at center, rgba(0,0,0,0) 30%, rgba(0,0,0,0.7) 100%)';
          veil.style.opacity = '1';
        } else if (kind === 'storm' && tw.on) {
          veil.style.background = 'radial-gradient(ellipse at center, rgba(0,0,10,0) 35%, rgba(0,0,20,0.6) 100%)';
          veil.style.opacity = t < flashUntil ? '0' : '1';
        } else if (kind === 'fog' && fogK > 0.05) {
          veil.style.background = 'radial-gradient(ellipse at center, rgba(200,210,220,0.05) 20%, rgba(200,210,220,0.55) 100%)';
          veil.style.opacity = String(fogK);
        } else {
          veil.style.opacity = '0';
        }
      }
      if (maskVeil) maskVeil.style.opacity = masked() && inPlay() ? '1' : '0';
      // the train's wheels on the rails, and the rumble in the tunnel
      if (extra.motion && arena.phase !== 'intermission' && t > clackAt) {
        clackAt = t + (tw.on && kind === 'tunnel' ? 0.42 : 0.62);
        client.audio.play('wd_clack', { volume: tw.on && kind === 'tunnel' ? 0.5 : 0.18 });
      }
    }

    // ------------------------------------------------------------ hud
    function hud(state) {
      var s = wd || {};
      var info = { title: state.area_name || '' };
      if (state.aphase === 'active') {
        info.left = { value: String(s.alive || 0), label: 'ALIVE', colour: '#f4e6c8' };
        info.right = { value: String(s['case'] || 0), label: 'CLUES', colour: '#e8c860' };
        var chips = ['seen', 'trail', 'suspects', 'glimpse'].map(function (h) {
          var got = (s.hints || []).indexOf(h) >= 0;
          return '<span style="padding:1px 6px;margin:0 2px;border-radius:4px;font-size:11px;' +
            (got ? 'background:#e8c860;color:#1a1a1a' : 'background:rgba(255,255,255,0.08);color:#8a8a8a') +
            '">' + HINTS[h][0] + '</span>';
        }).join('');
        var sub = chips;
        if (suspects.length) sub += ' &bull; suspects: <b style="color:#ff9a8a">' + suspects.map(esc).join(', ') + '</b>';
        if (s.on && TWISTS[s.twist]) {
          sub += ' &bull; <b style="color:' + TWISTS[s.twist].colour + '">' + TWISTS[s.twist].chip + '</b>';
        }
        if (s.gun) sub += ' &bull; <b style="color:#ffd27a">the revolver is on the floor</b>';
        info.sub = sub;
        var span = Math.max(1, (s.goal || 1) - (s.prev || 0));
        var into = Math.max(0, (s['case'] || 0) - (s.prev || 0));
        var done = (s.hints || []).length >= 4;
        info.bars = [{ label: 'CASE FILE', value: done ? 1 : into / span,
                       text: done ? 'all hints' : (s['case'] || 0) + ' / ' + (s.goal || 0),
                       colour: '#e8c860' }];
        info.urgent = (state.time_left || 99) < 20;
      }
      return info;
    }

    function prompt() {
      if (!inPlay()) return undefined;
      var me = myPos();
      if (ax.gn && !amMurderer() && !armed()) {
        var g = ax.gn;
        var d = Math.hypot(g[0] - me[0], g[2] - me[2]);
        if (d < 18) return d < GUN_REACH + 1 ? 'Picking up the revolver...' : 'The revolver -- walk over it to be the hero';
      }
      if (amMurderer() && arena.me.drawn) return 'Knife OUT -- anybody looking can see it. 1 to hide it, R to throw';
      var near = (ax.cl || []).some(function (c) { return Math.hypot(c[1] - me[0], c[3] - me[2]) < CLUE_REACH + 4; });
      if (near) return amMurderer() ? 'A clue -- walk over it to burn it' : 'A clue -- walk over it to pick it up';
      return '';
    }

    // ------------------------------------------------------- masks
    function maskedParts(player, parts) {
      var cloak = '#1e1626', trim = '#e8c860';
      var top = player.pos[1] + 5.5;
      var out = [];
      parts.forEach(function (part) {
        if (part.p && part.p[1] > top) return;          // hats and the like: hidden
        var copy = {};
        for (var key in part) copy[key] = part[key];
        if (copy.dec) delete copy.dec;
        if (copy.decSlot) delete copy.decSlot;
        var y = part.p ? part.p[1] - player.pos[1] : 0;
        copy.c = y > 4.0 ? '#d8c8b0' : cloak;           // the face pale, the rest in the cloak
        out.push(copy);
      });
      var yaw = player.yaw || 0;
      var fx = Math.sin(yaw), fz = Math.cos(yaw);
      var p = player.pos;
      out.push({ t: 'box', p: [p[0] + fx * 0.74, p[1] + 4.88, p[2] + fz * 0.74], s: [1.62, 0.6, 0.1],
                 c: '#0e0a14', r: [0, yaw, 0] });
      out.push({ t: 'box', p: [p[0] + fx * 0.8, p[1] + 5.2, p[2] + fz * 0.8], s: [1.66, 0.08, 0.06],
                 c: trim, r: [0, yaw, 0], m: 'metal' });
      out.push({ t: 'box', p: [p[0] + fx * 0.8 - fz * 0.95, p[1] + 5.5, p[2] + fz * 0.8 + fx * 0.95],
                 s: [0.12, 1.0, 0.06], c: '#8a2ac8', r: [0, yaw, 0.4] });
      return out;
    }

    // ------------------------------------------------------------ hooks
    return {
      init: function () { ensureNodes(); },
      messages: messages,
      onMap: loadMap,
      onArea: function () { arena.setRole(''); role = ''; partners = []; reset(); },
      onState: function (state) { applyState(state.wd); },
      onSnapshot: function (msg) { ax = msg.ax || {}; },
      onMe: function (me) {
        if (me.role && me.role !== role) role = me.role;
        if (me.partners) partners = me.partners;
        roleChip();
      },
      onPhase: function (msg) {
        if (msg.phase === 'setup') { role = ''; reset(); arena.setRole(''); }
      },
      onEnd: function (msg, card) {
        role = '';
        arena.setRole('');
        if (maskVeil) maskVeil.style.opacity = '0';
        tw.on = false; dark = 0; fogK = 0; applyLight();
        var roles = msg.roles || {};
        var names = { murderer: 'the murderer', detective: 'the detective', hero: 'the hero' };
        var killers = (msg.rows || []).filter(function (r) { return roles[String(r.id)] === 'murderer'; })
          .map(function (r) { return r.name; });
        if (card && killers.length) {
          var node = document.createElement('div');
          node.className = 'ar-end-s';
          node.style.cssText = 'margin-top:6px;color:#ff8a7a;font-weight:700';
          node.textContent = 'It was ' + killers.join(' and ') + '.';
          var h2 = card.querySelector('h2');
          if (h2 && h2.parentNode) h2.parentNode.insertBefore(node, h2.nextSibling);
        }
        var mine = roles[String(client.myId)];
        var won = msg.side === 'murderer' ? mine === 'murderer' : (mine && mine !== 'murderer');
        if (mine) client.hud.toast('You were ' + (names[mine] || 'innocent') + ' -- ' + (won ? 'and you won' : 'and you lost'),
                                   won ? 'good' : 'bad');
      },
      goLine: function () { return 'The roles are dealt. Trust nobody.'; },
      canFire: function () { return arena.phase === 'active'; },
      isCustom: function (stats) { return !!(stats && String(stats.kind || '').indexOf('wd_') === 0); },
      localFire: function (stats, origin, dir) {
        if (stats.kind === 'wd_knife') {
          client.audio.play('wd_swish', { volume: 0.8 });
          return true;
        }
        if (stats.kind === 'wd_revolver') {
          if ((arena.me.reload || 0) > 0.05) {
            client.hud.toast('Reloading -- ' + arena.me.reload.toFixed(1) + 's');
            return true;
          }
          var phys = client.physics;
          var dist = phys ? phys.rayDistance(origin, dir, stats.range || 170) : (stats.range || 170);
          var end = [origin[0] + dir[0] * dist, origin[1] + dir[1] * dist, origin[2] + dir[2] * dist];
          client.tracers.push({ a: origin.slice(), b: end, t: 0, c: rgb('#ffe2a0') });
          if (client.particles) client.particles.burst('muzzle', [origin[0] + dir[0] * 1.8, origin[1] + dir[1] * 1.8, origin[2] + dir[2] * 1.8]);
          client.audio.play('wd_bang', { volume: 1 });
          client.recoil = Math.min(1.6, (client.recoil || 0) + 0.6);
          arena.me.reload = 2.6;
          return true;
        }
        return false;
      },
      reloadDown: function () {
        if (!amMurderer() || !inPlay()) return false;
        if (!arena.me.drawn) { client.hud.toast('Draw the knife first (1)'); return true; }
        if ((arena.me['throw'] || 0) > 0.05) { client.hud.toast('Throw again in ' + Math.ceil(arena.me['throw']) + 's'); return true; }
        var yaw = client.local.yaw, pitch = client.local.pitch;
        var cp = Math.cos(pitch);
        arena.send('throw', { d: [Math.sin(yaw) * cp, Math.sin(pitch), Math.cos(yaw) * cp] });
        client.audio.play('wd_whirr', { volume: 0.8 });
        return true;
      },
      draw: function (renderer, dt, time) {
        stepTwist(dt, time);
        drawJourney(renderer, time);
        drawSea(renderer, time);
        drawBodies(renderer);
        drawClues(renderer, time);
        drawGun(renderer, time);
        drawKnives(renderer, dt, time);
        drawSteps(renderer);
        drawGlimpse(renderer, time);
      },
      avatarParts: function (player, parts, self) {
        if (!masked() || self) return parts;
        return maskedParts(player, parts);
      },
      nameTag: function (player) {
        if (masked()) return { hide: true };
        if (now() < glimpse.until && glimpse.ids.indexOf(player.id) >= 0) return { colour: '#ff4a4a', sub: 'THE MURDERER' };
        if (arena.phase === 'active') return { sub: '' };
        return null;
      },
      disguised: function () { return masked(); },
      noPet: function () { return masked(); },
      hud: hud,
      prompt: prompt,
      scoreHead: function () {
        return '<th>Player</th><th>Status</th><th>Clues</th><th>Score</th>';
      },
      scoreRow: function (row) {
        var status = row.out ? 'dead' : (arena.phase === 'active' ? 'alive' : '');
        return '<td>' + status + '</td><td>' + (row.clues || 0) + '</td><td>' +
          (arena.phase === 'active' ? '?' : row.score) + '</td>';
      },
      introInfo: function () { return { kicker: 'A MURDER AT' }; }
    };
  });

  // ============================================================ sounds
  var GA = global.GameAudio;
  if (GA && GA.register) {
    GA.register('wd_swish', function (vol) {
      this.noise({ filter: 'bandpass', freq: 2600, freqEnd: 900, dur: 0.16, gain: 0.2 * vol });
    });
    GA.register('wd_stab', function (vol) {
      this.noise({ filter: 'lowpass', freq: 900, freqEnd: 200, dur: 0.12, gain: 0.3 * vol });
      this.tone({ type: 'sine', freq: 160, freqEnd: 70, dur: 0.14, gain: 0.16 * vol });
    });
    GA.register('wd_thunk', function (vol) {
      this.tone({ type: 'square', freq: 220, freqEnd: 120, dur: 0.06, gain: 0.12 * vol });
      this.noise({ filter: 'bandpass', freq: 1800, dur: 0.05, gain: 0.15 * vol });
    });
    GA.register('wd_whirr', function (vol) {
      for (var i = 0; i < 4; i++) {
        this.later(i * 70, function () {
          this.noise({ filter: 'bandpass', freq: 1400, freqEnd: 2400, dur: 0.06, gain: 0.12 * vol });
        });
      }
    });
    GA.register('wd_bang', function (vol) {
      this.noise({ filter: 'lowpass', freq: 3400, freqEnd: 300, dur: 0.38, gain: 0.5 * vol });
      this.tone({ type: 'sine', freq: 120, freqEnd: 40, dur: 0.3, gain: 0.3 * vol });
    });
    GA.register('wd_scream', function (vol) {
      this.tone({ type: 'sawtooth', freq: 880, freqEnd: 1320, dur: 0.25, gain: 0.07 * vol });
      this.later(220, function () { this.tone({ type: 'sawtooth', freq: 1320, freqEnd: 520, dur: 0.6, gain: 0.07 * vol }); });
      this.noise({ filter: 'bandpass', freq: 1800, dur: 0.7, gain: 0.06 * vol });
    });
    GA.register('wd_sting', function (vol) {
      [233, 247, 220].forEach(function (f, i) {
        this.later(i * 10, function () { this.tone({ type: 'sawtooth', freq: f, dur: 1.2, gain: 0.06 * vol }); });
      }, this);
      this.tone({ type: 'sine', freq: 58, dur: 1.4, gain: 0.2 * vol });
    });
    GA.register('wd_chime', function (vol) {
      [523, 659, 784].forEach(function (f, i) {
        this.later(i * 120, function () { this.tone({ type: 'triangle', freq: f, dur: 0.5, gain: 0.1 * vol }); });
      }, this);
    });
    GA.register('wd_clue', function (vol) {
      this.tone({ type: 'triangle', freq: 1046, dur: 0.12, gain: 0.12 * vol });
      this.later(90, function () { this.tone({ type: 'triangle', freq: 1568, dur: 0.22, gain: 0.1 * vol }); });
    });
    GA.register('wd_hint', function (vol) {
      [392, 523, 659, 1046].forEach(function (f, i) {
        this.later(i * 90, function () { this.tone({ type: 'square', freq: f, dur: 0.16, gain: 0.07 * vol }); });
      }, this);
      this.later(420, function () { this.noise({ filter: 'bandpass', freq: 3000, dur: 0.12, gain: 0.08 * vol }); });
    });
    GA.register('wd_solved', function (vol) {
      [523, 659, 784, 1046, 1318].forEach(function (f, i) {
        this.later(i * 110, function () { this.tone({ type: 'triangle', freq: f, dur: 0.4, gain: 0.12 * vol }); });
      }, this);
    });
    GA.register('wd_clink', function (vol) {
      this.tone({ type: 'square', freq: 1800, freqEnd: 1500, dur: 0.05, gain: 0.08 * vol });
      this.later(80, function () { this.tone({ type: 'square', freq: 1400, freqEnd: 1200, dur: 0.06, gain: 0.06 * vol }); });
      this.later(200, function () { this.tone({ type: 'square', freq: 1600, dur: 0.04, gain: 0.04 * vol }); });
    });
    GA.register('wd_burn', function (vol) {
      this.noise({ filter: 'highpass', freq: 1200, freqEnd: 4000, dur: 0.5, gain: 0.14 * vol });
    });
    GA.register('wd_thunder', function (vol) {
      this.noise({ filter: 'lowpass', freq: 600, freqEnd: 60, dur: 2.2, gain: 0.5 * vol });
      this.later(120, function () { this.noise({ filter: 'lowpass', freq: 300, freqEnd: 40, dur: 1.8, gain: 0.35 * vol }); });
    });
    GA.register('wd_whistle', function (vol) {
      this.tone({ type: 'square', freq: 587, dur: 0.6, gain: 0.07 * vol });
      this.tone({ type: 'square', freq: 740, dur: 0.6, gain: 0.06 * vol });
      this.later(700, function () {
        this.tone({ type: 'square', freq: 587, dur: 1.1, gain: 0.07 * vol });
        this.tone({ type: 'square', freq: 740, dur: 1.1, gain: 0.06 * vol });
      });
    });
    GA.register('wd_rumble', function (vol) {
      this.noise({ filter: 'lowpass', freq: 220, freqEnd: 120, dur: 3.0, gain: 0.35 * vol });
    });
    GA.register('wd_clack', function (vol) {
      this.noise({ filter: 'bandpass', freq: 900, dur: 0.04, gain: 0.3 * vol });
      this.later(110, function () { this.noise({ filter: 'bandpass', freq: 800, dur: 0.04, gain: 0.25 * vol }); });
    });
    GA.register('wd_waltz', function (vol) {
      [[392, 0], [494, 300], [587, 450], [494, 600], [392, 900], [440, 1200], [523, 1350], [440, 1500]].forEach(function (n) {
        this.later(n[1], function () { this.tone({ type: 'triangle', freq: n[0], dur: 0.28, gain: 0.08 * vol }); });
      }, this);
      [196, 196, 196].forEach(function (f, i) {
        this.later(i * 300, function () { this.tone({ type: 'sine', freq: f, dur: 0.2, gain: 0.08 * vol }); });
      }, this);
    });
    GA.register('wd_foghorn', function (vol) {
      this.tone({ type: 'sawtooth', freq: 82, dur: 2.2, gain: 0.14 * vol });
      this.tone({ type: 'sine', freq: 164, dur: 2.2, gain: 0.08 * vol });
    });
  }

  // =================================================== arrival scenes
  var Intro = global.AreaIntro;
  if (!Intro) return;
  var K = Intro.kit;
  var VW = K.VW, VH = K.VH, TAU = K.TAU, HEAVY = K.HEAVY, FONT = K.FONT;
  var seg = K.seg, lerp = K.lerp, outCubic = K.outCubic, outBack = K.outBack, inOut = K.inOut;
  var dot = K.dot, additive = K.additive, roundRect = K.roundRect, fitSize = K.fitSize;
  var between = K.between, rgba = K.rgba, wobble = K.wobble, makeStars = K.makeStars, stars = K.stars;
  var SERIF = 'Georgia, "Times New Roman", serif';

  function nameText(ctx, name, x, y, max, colour, shade, font, size0) {
    var size = fitSize(ctx, name, 'bold #px ' + (font || HEAVY), size0 || 104, max, 0.04);
    ctx.font = 'bold ' + size + 'px ' + (font || HEAVY);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    if (shade) { ctx.fillStyle = shade; ctx.fillText(name, x + 4, y + 5); }
    ctx.fillStyle = colour;
    ctx.fillText(name, x, y);
    ctx.textAlign = 'left';
    return size;
  }

  /* A stamped case file: a manila folder, the place typed on its tab, a red
     CONFIDENTIAL stamp thumping down. */
  function caseFile(ctx, t, run, name, at, accent) {
    var k = outBack(seg(t, at, at + 0.5), 1.4);
    ctx.save();
    ctx.translate(800, 250 + (1 - k) * 340);
    ctx.rotate(-0.03 + wobble(t, at + 0.5, 0.02, 9, 3));
    ctx.fillStyle = '#c8a46a';
    roundRect(ctx, -520, -120, 1040, 240, 14); ctx.fill();
    ctx.fillStyle = '#b8945a';
    roundRect(ctx, -520, -150, 300, 50, 10); ctx.fill();
    ctx.fillStyle = '#4a3420';
    ctx.font = 'bold 22px "Courier New", monospace';
    ctx.textBaseline = 'middle';
    ctx.fillText('CASE No. ' + (100 + (name.length * 37) % 900), -490, -125);
    var shown = name.slice(0, Math.floor(name.length * seg(t, at + 0.4, at + 1.2)));
    ctx.globalAlpha = run.alpha;
    nameText(ctx, shown, 0, 8, 900, '#2a1a10', null, '"Courier New", monospace', 92);
    var s = seg(t, at + 1.3, at + 1.5);
    if (s > 0) {
      ctx.save();
      ctx.translate(330, 70);
      ctx.rotate(-0.18);
      ctx.scale(2 - s, 2 - s);
      ctx.globalAlpha = run.alpha * s * 0.9;
      ctx.strokeStyle = accent || '#c8202a';
      ctx.lineWidth = 6;
      ctx.strokeRect(-150, -32, 300, 64);
      ctx.fillStyle = accent || '#c8202a';
      ctx.font = 'bold 40px ' + HEAVY;
      ctx.textAlign = 'center';
      ctx.fillText('MURDER', 0, 3);
      ctx.restore();
    }
    ctx.restore();
  }

  // a figure in a hat, in silhouette, with a knife
  function figure(ctx, x, y, s, colour, knife) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(s, s);
    ctx.fillStyle = colour;
    ctx.fillRect(-14, -150, 28, 30);
    ctx.fillRect(-26, -128, 52, 8);
    ctx.fillRect(-20, -120, 40, 70);
    ctx.beginPath(); ctx.moveTo(-30, -112); ctx.lineTo(30, -112); ctx.lineTo(36, -20); ctx.lineTo(-36, -20); ctx.fill();
    ctx.fillRect(-22, -20, 18, 20); ctx.fillRect(4, -20, 18, 20);
    if (knife) {
      ctx.fillStyle = '#e8eef4';
      ctx.beginPath(); ctx.moveTo(34, -90); ctx.lineTo(70, -116); ctx.lineTo(74, -110); ctx.lineTo(40, -84); ctx.fill();
    }
    ctx.restore();
  }

  // ------------------------------------------------ Blackwood Manor
  Intro.register('wd_manor', {
    name: 'Blackwood Manor',
    tagline: 'A dark and stormy night. One of the guests will not see the morning.',
    accent: '#c8202a',
    cues: [[0.35, 'wd_thunder', 0.7], [1.6, 'wd_scream', 0.5], [2.15, 'wd_thunder', 0.9],
           [3.4, 'slam', 0.35], [4.4, 'wd_sting', 0.6]],
    shakes: [[2.15, 5, 0.4]],
    tagY: 520, tagAt: 3.6,
    setup: function (r) {
      var d = { rain: [], stars: makeStars(r, 50, 0, 300) };
      for (var i = 0; i < 160; i++) d.rain.push([between(r, 0, VW), between(r, 0, VH), between(r, 18, 34)]);
      return d;
    },
    draw: function (ctx, t, d) {
      var flash = Math.max(seg(t, 0.3, 0.36) * (1 - seg(t, 0.36, 0.6)), seg(t, 2.1, 2.16) * (1 - seg(t, 2.16, 2.6)));
      var sky = ctx.createLinearGradient(0, 0, 0, VH);
      sky.addColorStop(0, K.mix('#0c1020', '#c8d0ff', flash)); sky.addColorStop(0.6, K.mix('#262a44', '#e8ecff', flash));
      sky.addColorStop(1, '#0a0c12');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      if (flash > 0.05) {
        ctx.strokeStyle = 'rgba(240,244,255,' + flash + ')'; ctx.lineWidth = 4;
        ctx.beginPath(); var x = 1180, y = 0; ctx.moveTo(x, y);
        for (var j = 0; j < 9; j++) { x += (j % 2 ? 30 : -24); y += 46; ctx.lineTo(x, y); }
        ctx.stroke();
      }
      // the hill and the house on it
      ctx.fillStyle = '#0c0e14';
      ctx.beginPath(); ctx.moveTo(0, 760); ctx.quadraticCurveTo(800, 520, VW, 760); ctx.lineTo(VW, VH); ctx.lineTo(0, VH); ctx.fill();
      ctx.fillStyle = '#14161e';
      ctx.fillRect(470, 380, 660, 250);
      for (var g = 0; g < 4; g++) ctx.fillRect(450 + g * 20, 380 - (g + 1) * 30, 700 - g * 40, 32);
      ctx.fillRect(560, 230, 50, 120); ctx.fillRect(990, 230, 50, 120);
      ctx.beginPath(); ctx.moveTo(760, 250); ctx.lineTo(800, 150); ctx.lineTo(840, 250); ctx.fill();
      // windows: warm, one by one, then the one with the figure
      [[510, 420], [600, 420], [690, 420], [880, 420], [970, 420], [1060, 420],
       [510, 530], [600, 530], [970, 530], [1060, 530]].forEach(function (w, i) {
        var on = seg(t, 0.4 + i * 0.12, 0.5 + i * 0.12);
        ctx.fillStyle = 'rgba(255,200,110,' + (0.85 * on * (0.85 + 0.15 * Math.sin(t * 3 + i))) + ')';
        ctx.fillRect(w[0], w[1], 46, 70);
      });
      ctx.fillStyle = 'rgba(255,190,100,0.9)'; ctx.fillRect(760, 520, 80, 110);
      figure(ctx, 800, 630, 0.62 + 0.04 * seg(t, 1.5, 2.2), '#0a0a0e', t > 1.55);
      // rain
      ctx.strokeStyle = 'rgba(180,190,220,0.35)'; ctx.lineWidth = 1.5;
      d.rain.forEach(function (p) {
        var y = (p[1] + t * 900) % VH;
        ctx.beginPath(); ctx.moveTo(p[0] - y * 0.05, y); ctx.lineTo(p[0] - y * 0.05 - 4, y + p[2]); ctx.stroke();
      });
    },
    title: function (ctx, t, d, run) {
      caseFile(ctx, t, run, (run.info.name || 'Blackwood Manor').toUpperCase(), 2.4, '#c8202a');
    }
  });

  // ------------------------------------------------ The Midnight Express
  Intro.register('wd_express', {
    name: 'The Midnight Express',
    tagline: 'Twelve sleeping cars, one tunnel, and a passenger who will not reach the other end.',
    accent: '#ffb35a',
    cues: [[0.2, 'wd_whistle', 0.7], [1.0, 'wd_clack', 0.5], [1.6, 'wd_clack', 0.5], [2.2, 'wd_clack', 0.5],
           [2.8, 'wd_rumble', 0.7], [3.6, 'wd_sting', 0.5]],
    shakes: [[2.8, 3, 0.6]],
    tagY: 520, tagAt: 3.4,
    setup: function (r) {
      var d = { stars: makeStars(r, 120, 0, 420), peaks: [] };
      for (var i = 0; i < 9; i++) d.peaks.push([i * 220 - 80 + between(r, -40, 40), between(r, 260, 420)]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, VH);
      sky.addColorStop(0, '#060a18'); sky.addColorStop(0.6, '#1e2848'); sky.addColorStop(1, '#2a3450');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      stars(ctx, d.stars, t, 0.9);
      additive(ctx, function () { dot(ctx, '#f4f0d8', 1300, 160, 120, 0.5); });
      ctx.fillStyle = '#f4f0d8'; ctx.beginPath(); ctx.arc(1300, 160, 38, 0, TAU); ctx.fill();
      d.peaks.forEach(function (p, i) {
        ctx.fillStyle = i % 2 ? '#2a3448' : '#222a3c';
        ctx.beginPath(); ctx.moveTo(p[0] - 260, 700); ctx.lineTo(p[0], p[1]); ctx.lineTo(p[0] + 260, 700); ctx.fill();
        ctx.fillStyle = '#d8e0ec';
        ctx.beginPath(); ctx.moveTo(p[0] - 50, p[1] + 60); ctx.lineTo(p[0], p[1]); ctx.lineTo(p[0] + 50, p[1] + 60); ctx.fill();
      });
      // the viaduct and the mountain with the tunnel mouth on the right
      ctx.fillStyle = '#141820';
      ctx.fillRect(0, 640, VW, 26);
      for (var a = 0; a < 12; a++) {
        ctx.beginPath(); ctx.moveTo(a * 150, 666); ctx.lineTo(a * 150, VH); ctx.lineTo(a * 150 + 30, VH); ctx.lineTo(a * 150 + 30, 700);
        ctx.quadraticCurveTo(a * 150 + 75, 676, a * 150 + 120, 700); ctx.lineTo(a * 150 + 120, VH); ctx.lineTo(a * 150 + 150, VH); ctx.lineTo(a * 150 + 150, 666); ctx.fill();
      }
      ctx.fillStyle = '#10141c';
      ctx.beginPath(); ctx.moveTo(1240, 666); ctx.lineTo(1340, 380); ctx.lineTo(VW, 300); ctx.lineTo(VW, VH); ctx.lineTo(1240, VH); ctx.fill();
      ctx.fillStyle = '#05060a'; ctx.beginPath(); ctx.arc(1360, 640, 70, Math.PI, 0); ctx.fill(); ctx.fillRect(1290, 640, 140, 26);
      // the train: engine and cars sliding into the tunnel
      var x = lerp(-600, 1500, seg(t, 0.1, 5.4));
      ctx.save();
      ctx.beginPath(); ctx.rect(0, 0, 1330, VH); ctx.clip();
      for (var c = 0; c < 6; c++) {
        var cx = x - c * 190;
        ctx.fillStyle = c === 0 ? '#1a2a1e' : '#3a1a2a';
        ctx.fillRect(cx, 590, c === 0 ? 150 : 180, 50);
        if (c === 0) { ctx.fillRect(cx + 110, 560, 40, 32); ctx.fillStyle = '#ffe8a8'; ctx.fillRect(cx + 148, 600, 8, 8); }
        else {
          for (var w = 0; w < 6; w++) {
            ctx.fillStyle = 'rgba(255,214,140,' + (0.7 + 0.3 * Math.sin(t * 4 + c + w)) + ')';
            ctx.fillRect(cx + 12 + w * 27, 600, 16, 16);
          }
        }
      }
      for (var s = 0; s < 6; s++) {
        var age = (t * 2 + s * 0.4) % 2.4;
        ctx.fillStyle = 'rgba(200,200,210,' + (0.4 * (1 - age / 2.4)) + ')';
        ctx.beginPath(); ctx.arc(x + 128 - age * 120, 550 - age * 60, 14 + age * 22, 0, TAU); ctx.fill();
      }
      ctx.restore();
    },
    title: function (ctx, t, d, run) {
      // a railway ticket, punched
      var at = 2.2, k = outBack(seg(t, at, at + 0.5), 1.3);
      ctx.save();
      ctx.translate(800, 250);
      ctx.scale(k, k);
      ctx.rotate(0.02);
      ctx.fillStyle = '#e8dcb8';
      roundRect(ctx, -500, -110, 1000, 220, 18); ctx.fill();
      ctx.strokeStyle = '#8a3a2a'; ctx.lineWidth = 4; ctx.setLineDash([12, 8]);
      ctx.strokeRect(-470, -84, 940, 168); ctx.setLineDash([]);
      ctx.fillStyle = '#8a3a2a'; ctx.font = 'bold 22px ' + FONT; ctx.textBaseline = 'middle';
      ctx.fillText('ONE WAY  ·  FIRST CLASS  ·  SLEEPER', -440, -60);
      ctx.globalAlpha = run.alpha;
      nameText(ctx, (run.info.name || 'The Midnight Express').toUpperCase(), 0, 16, 880, '#2a1a10', null, SERIF, 84);
      if (t > at + 1.2) {
        ctx.fillStyle = '#05060a';
        ctx.beginPath(); ctx.arc(430, 70, 18, 0, TAU); ctx.fill();
      }
      ctx.restore();
    }
  });

  // ------------------------------------------------ The Grand Meridian
  Intro.register('wd_hotel', {
    name: 'The Grand Meridian',
    tagline: 'Black tie. Masks at midnight. Someone came to the ball with a knife.',
    accent: '#e8c860',
    cues: [[0.3, 'wd_waltz', 0.6], [1.6, 'wd_waltz', 0.5], [2.6, 'buzz', 0.4], [3.4, 'wd_sting', 0.6]],
    shakes: [],
    tagY: 520, tagAt: 3.5,
    setup: function (r) {
      var d = { stars: makeStars(r, 60, 0, 260), towers: [] };
      for (var i = 0; i < 14; i++) d.towers.push([i * 120 + between(r, -20, 20), between(r, 220, 520), between(r, 70, 110)]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, VH);
      sky.addColorStop(0, '#0a0c1c'); sky.addColorStop(0.7, '#3a2a4a'); sky.addColorStop(1, '#1a1420');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, VH);
      stars(ctx, d.stars, t, 0.6);
      d.towers.forEach(function (w, i) {
        ctx.fillStyle = i % 2 ? '#14141e' : '#1a1a26';
        ctx.fillRect(w[0], w[1], w[2], VH - w[1]);
        for (var y = w[1] + 20; y < VH - 40; y += 34) {
          for (var x = w[0] + 10; x < w[0] + w[2] - 14; x += 22) {
            if (Math.sin(x * 1.3 + y * 0.7 + i) > 0.35) { ctx.fillStyle = 'rgba(255,214,140,0.55)'; ctx.fillRect(x, y, 10, 14); }
          }
        }
      });
      // the hotel front, its canopy, the sign stuttering into life
      ctx.fillStyle = '#d8c8a4'; ctx.fillRect(420, 380, 760, 520);
      for (var r = 0; r < 4; r++) {
        for (var c = 0; c < 8; c++) {
          ctx.fillStyle = 'rgba(255,214,140,' + (0.55 + 0.35 * Math.sin(t * 2 + r + c)) + ')';
          ctx.fillRect(450 + c * 92, 420 + r * 110, 50, 70);
        }
      }
      ctx.fillStyle = '#1a1a24'; ctx.fillRect(700, 780, 200, 26);
      var on = K.sputter(t, 2.5, 3) * K.buzz(t, 5);
      ctx.fillStyle = '#1a1a24'; ctx.fillRect(560, 250, 480, 120);
      ctx.save();
      // the sign gives way to the name in gold, which lands where it hangs
      ctx.globalAlpha = 1 - seg(t, 1.8, 2.3);
      ctx.font = 'bold 76px ' + HEAVY; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.shadowColor = '#ff7ac8'; ctx.shadowBlur = 30 * on;
      ctx.fillStyle = on > 0.5 ? '#ff7ac8' : '#5a2a44';
      ctx.fillText('MERIDIAN', 800, 312);
      ctx.restore();
      // masks drift down out of the dark
      for (var m = 0; m < 7; m++) {
        var k = seg(t, 0.4 + m * 0.35, 3.0 + m * 0.35);
        if (k <= 0) continue;
        var mx = 160 + m * 210, my = lerp(-80, 180 + (m % 3) * 140, outCubic(k));
        ctx.save(); ctx.translate(mx, my); ctx.rotate(Math.sin(t * 2 + m) * 0.3);
        ctx.fillStyle = m % 2 ? '#1a0a24' : '#e8c860';
        ctx.beginPath(); ctx.ellipse(-28, 0, 32, 20, 0, 0, TAU); ctx.ellipse(28, 0, 32, 20, 0, 0, TAU); ctx.fill();
        ctx.fillStyle = '#05060a';
        ctx.beginPath(); ctx.ellipse(-26, 0, 13, 8, 0, 0, TAU); ctx.ellipse(26, 0, 13, 8, 0, 0, TAU); ctx.fill();
        ctx.restore();
      }
    },
    title: function (ctx, t, d, run) {
      var at = 2.0, k = outCubic(seg(t, at, at + 0.6));
      ctx.save();
      ctx.translate(800, 250);
      ctx.globalAlpha = run.alpha * k;
      ctx.fillStyle = 'rgba(10,8,16,0.96)';
      ctx.fillRect(-520 * k, -100, 1040 * k, 200);
      ctx.strokeStyle = '#e8c860'; ctx.lineWidth = 3;
      ctx.strokeRect(-500 * k, -84, 1000 * k, 168);
      for (var i = -1; i <= 1; i += 2) {
        ctx.beginPath(); ctx.moveTo(i * 470 * k, -60); ctx.lineTo(i * 440 * k, -30); ctx.lineTo(i * 470 * k, 0);
        ctx.lineTo(i * 440 * k, 30); ctx.lineTo(i * 470 * k, 60); ctx.stroke();
      }
      nameText(ctx, (run.info.name || 'The Grand Meridian').toUpperCase(), 0, 6, 840 * k + 1, '#e8c860', 'rgba(0,0,0,0.6)', SERIF, 92);
      ctx.restore();
    }
  });

  // ------------------------------------------------ The SS Aurora
  Intro.register('wd_liner', {
    name: 'The SS Aurora',
    tagline: 'Mid-Atlantic, among the ice. There is nowhere to run but overboard.',
    accent: '#8ad8ff',
    cues: [[0.3, 'wd_foghorn', 0.8], [2.4, 'wd_foghorn', 0.6], [3.6, 'wd_sting', 0.6]],
    shakes: [],
    tagY: 520, tagAt: 3.4,
    setup: function (r) {
      var d = { stars: makeStars(r, 140, 0, 420), waves: [] };
      for (var i = 0; i < 60; i++) d.waves.push([between(r, 0, VW), between(r, 640, VH), between(r, 20, 80)]);
      return d;
    },
    draw: function (ctx, t, d) {
      var sky = ctx.createLinearGradient(0, 0, 0, 640);
      sky.addColorStop(0, '#060a18'); sky.addColorStop(1, '#1a2a40');
      ctx.fillStyle = sky; ctx.fillRect(0, 0, VW, 640);
      stars(ctx, d.stars, t, 0.9);
      ctx.fillStyle = '#081420'; ctx.fillRect(0, 640, VW, VH - 640);
      ctx.strokeStyle = 'rgba(160,200,230,0.25)'; ctx.lineWidth = 2;
      d.waves.forEach(function (w) {
        var x = (w[0] - t * 30 + VW) % VW;
        ctx.beginPath(); ctx.moveTo(x, w[1]); ctx.lineTo(x + w[2], w[1]); ctx.stroke();
      });
      // the berg
      ctx.fillStyle = '#dce8f0';
      ctx.beginPath(); ctx.moveTo(1180, 640); ctx.lineTo(1260, 470); ctx.lineTo(1320, 520); ctx.lineTo(1380, 430); ctx.lineTo(1480, 640); ctx.fill();
      // the liner, lights blazing, sliding across
      var x = lerp(-900, 260, outCubic(seg(t, 0.1, 4.8)));
      ctx.save(); ctx.translate(x, 0);
      ctx.fillStyle = '#12141a';
      ctx.beginPath(); ctx.moveTo(0, 560); ctx.lineTo(900, 560); ctx.lineTo(960, 520); ctx.lineTo(980, 520); ctx.lineTo(940, 660); ctx.lineTo(30, 660); ctx.fill();
      ctx.fillStyle = '#f2f0ea'; ctx.fillRect(140, 500, 620, 60); ctx.fillRect(260, 460, 380, 40);
      for (var f = 0; f < 3; f++) {
        ctx.fillStyle = '#d8a040'; ctx.fillRect(300 + f * 120, 380, 54, 82);
        ctx.fillStyle = '#12141a'; ctx.fillRect(300 + f * 120, 380, 54, 16);
        var age = (t * 0.8 + f * 0.3) % 2;
        ctx.fillStyle = 'rgba(180,180,190,' + (0.35 * (1 - age / 2)) + ')';
        ctx.beginPath(); ctx.arc(327 + f * 120 - age * 50, 360 - age * 50, 16 + age * 20, 0, TAU); ctx.fill();
      }
      for (var w = 0; w < 26; w++) {
        ctx.fillStyle = 'rgba(255,214,140,' + (0.7 + 0.3 * Math.sin(t * 3 + w)) + ')';
        ctx.fillRect(60 + w * 32, 590, 12, 10);
        if (w % 2 === 0 && w > 4 && w < 22) ctx.fillRect(140 + w * 23, 516, 10, 14);
      }
      ctx.restore();
      // the fog bank rolling in
      var fog = seg(t, 2.2, 5.2);
      var g = ctx.createLinearGradient(0, 300, 0, VH);
      g.addColorStop(0, 'rgba(200,210,220,0)'); g.addColorStop(1, 'rgba(200,210,220,' + (0.65 * fog) + ')');
      ctx.fillStyle = g; ctx.fillRect(0, 300, VW, VH - 300);
    },
    title: function (ctx, t, d, run) {
      // a telegram
      var at = 2.1, k = outBack(seg(t, at, at + 0.5), 1.2);
      ctx.save();
      ctx.translate(800, 240);
      ctx.scale(k, k);
      ctx.rotate(-0.02);
      ctx.fillStyle = '#f2ead0';
      ctx.fillRect(-500, -110, 1000, 220);
      ctx.fillStyle = '#1a3a5a'; ctx.fillRect(-500, -110, 1000, 34);
      ctx.fillStyle = '#f2ead0'; ctx.font = 'bold 20px ' + FONT; ctx.textBaseline = 'middle';
      ctx.fillText('MARCONI WIRELESS TELEGRAM  ·  URGENT', -470, -93);
      ctx.globalAlpha = run.alpha;
      var name = (run.info.name || 'The SS Aurora').toUpperCase();
      var shown = name.slice(0, Math.floor(name.length * seg(t, at + 0.3, at + 1.1)));
      nameText(ctx, shown, 0, 10, 880, '#1a1a1a', null, '"Courier New", monospace', 86);
      ctx.fillStyle = '#5a1a1a'; ctx.font = 'bold 20px "Courier New", monospace';
      ctx.textAlign = 'center';
      ctx.fillText('STOP. A PASSENGER IS DEAD. STOP. THE KILLER IS ABOARD. STOP.', 0, 78 * seg(t, at + 1.0, at + 1.2) + 0.01);
      ctx.restore();
    }
  });
})(window);
