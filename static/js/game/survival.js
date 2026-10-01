/* Last Light -- the survival half of the Game View.

   Everything the zombie world needs on screen and nothing the other worlds
   do: the infected themselves (built from the same avatar rig as players,
   dressed per area and per kind), their deaths, their thrown acid, bolts and
   rocks, the fuel barrels and acid pools, the safe-room supplies, the area's
   noise-maker; the survival HUD (wave, infected left, the team's health,
   the Tank's bar, wave banners and the end card); being downed, pinned or
   covered in bile; and the spectator camera the dead watch the living
   through until the next wave brings them back.

   The client creates one of these when the world's mode is "survival" and
   forwards the messages, the snapshot rows and a handful of hooks to it --
   movement, the camera, interaction and drawing.  Nothing here decides
   anything: the server says what happened, this shows it. */
(function (global) {
  'use strict';

  var M = GLX.mat;

  // ----------------------------------------------------------------- kinds
  // the server's KIND_CODES, in order
  var KINDS = ['common', 'runner', 'bloater', 'bomber', 'leaper', 'brute',
               'spitter', 'screamer', 'riot', 'captain', 'hive', 'mite', 'ronin',
               'burrower', 'tank'];
  var NAMES = {
    common: 'Infected', runner: 'Runner', bloater: 'Bloater', bomber: 'Bomber',
    leaper: 'Leaper', brute: 'Brute', spitter: 'Spitter', screamer: 'Screamer',
    riot: 'Riot', captain: 'Plague Captain', hive: 'Hive', mite: 'Mite',
    ronin: 'Ronin', burrower: 'Burrower', tank: 'Tank'
  };
  // hit boxes (w, h, d), matching app/game/worlds/infected.py, for tracers
  var BOX = {
    common: [3.0, 5.4, 2.0], runner: [3.0, 5.4, 2.0], bloater: [4.6, 5.8, 3.8],
    bomber: [3.0, 5.4, 2.2], leaper: [3.0, 4.8, 2.2], brute: [4.8, 7.2, 3.6],
    spitter: [2.8, 6.0, 2.0], screamer: [2.8, 5.6, 2.0], riot: [3.6, 5.9, 2.6],
    captain: [3.2, 6.4, 2.2], hive: [4.4, 6.0, 3.6], mite: [1.6, 1.8, 1.6],
    ronin: [3.0, 5.8, 2.2], burrower: [3.0, 5.4, 2.2], tank: [6.4, 9.0, 4.6]
  };
  var SCALE = { brute: 1.32, tank: 1.68, bloater: 1.06, spitter: 1.1, captain: 1.08 };
  // animation codes and flag bits on the wire
  var A = { WALK: 0, RUN: 1, ATTACK: 2, LEAP: 3, SCREAM: 4, STUN: 5, CLIMB: 6,
            THROW: 7, RISE: 8, PIN: 9, CHARGE: 10, SPIT: 11, BURROW: 12,
            GUARD: 13, SLAM: 14 };
  var F = { ENRAGED: 1, HIDDEN: 2, GUARD: 4, FUSE: 8, CHARGING: 16, PINNING: 32,
            STUNNED: 64, LURED: 128 };

  // --------------------------------------------------------------- looks
  /* The face every one of them shares: two dots for eyes and a mouth hung
     open in an O, with a string of drool off the lip.  Specials get their
     own eyes; the mouth is the family resemblance. */
  function zombieFace(eyes, mouth, extra) {
    var shapes = [
      { k: 'ellipse', x: -0.22, y: -0.14, w: 0.13, h: 0.13, c: eyes || '#141414' },
      { k: 'ellipse', x: 0.22, y: -0.16, w: 0.12, h: 0.12, c: eyes || '#141414' },
      { k: 'ellipse', x: 0.0, y: 0.18, w: 0.26, h: 0.3, c: '#141414' },
      { k: 'ellipse', x: 0.0, y: 0.2, w: 0.15, h: 0.18, c: mouth || '#5a1414' },
      { k: 'rect', x: 0.07, y: 0.37, w: 0.05, h: 0.16, c: '#d8f0b8' },
      { k: 'ellipse', x: 0.07, y: 0.46, w: 0.08, h: 0.07, c: '#d8f0b8' }
    ];
    return shapes.concat(extra || []);
  }
  var FACE_COMMON = zombieFace();
  var FACE_RED = zombieFace('#c81e1e', '#3a0808');
  var FACE_GLOW = zombieFace('#b6ff4a', '#2a4a08');

  function shirt(torso, arms, extra) {
    var data = { torso: torso, arms: arms === undefined ? torso : arms };
    for (var k in (extra || {})) data[k] = extra[k];
    return { data: data };
  }
  function pants(legs, extra) {
    var data = { legs: legs };
    for (var k in (extra || {})) data[k] = extra[k];
    return { data: data };
  }
  function hat(parts) { return { data: { parts: parts } }; }
  function hair(parts) { return { data: { parts: parts } }; }

  var SKINS = ['#6fae55', '#7fb069', '#5f9a4c', '#86b86a', '#6c9f68', '#79a84e'];
  var CLASSIC = { shirt: shirt('#7a5230', '#7a5230', { sleeves: 0.55 }),
                  pants: pants('#3f63a8') };

  /* What the commons died in, area by area.  Variant 0 is everywhere the
     classic: brown shirt, blue trousers. */
  var WARDROBE = {
    town: [
      CLASSIC,
      { shirt: shirt('#b8382e', '#b8382e', { weave: 'flannel' }), pants: pants('#2f4f8a') },
      { shirt: shirt('#e8e8e2', '#e8e8e2', { decal: 'tux' }), pants: pants('#4a4f58') },
      { shirt: shirt('#8fb8dc', '#8fb8dc', { sleeves: 0.4 }), pants: pants('#24345a', { length: 0.55 }),
        hat: hat([{ t: 'cyl', p: [0, 0.2, 0], s: [1.6, 0.4, 1.6], c: '#24345a' },
                  { t: 'box', p: [0, 0.08, 0.86], s: [1.3, 0.12, 0.7], c: '#1b2440' }]) },
      { shirt: shirt('#f2f2ee', '#f2f2ee', { stripe: '#c83a2a' }), pants: pants('#3a3a3a') },
      { shirt: shirt('#1f2f4a', '#1f2f4a', { decal: 'chevron' }), pants: pants('#1f2f4a'),
        hat: hat([{ t: 'cyl', p: [0, 0.22, 0], s: [1.64, 0.44, 1.64], c: '#1b2440' },
                  { t: 'box', p: [0, 0.06, 0.9], s: [1.4, 0.1, 0.6], c: '#111111' },
                  { t: 'box', p: [0, 0.32, 0.8], s: [0.3, 0.3, 0.06], c: '#d8b84a' }]) },
      { shirt: shirt('#5a5f6a', '#5a5f6a', { hood: true }), pants: pants('#26282c') },
      { shirt: shirt('#c8a060', '#7a5230', { sleeves: 0.3 }), pants: pants('#3f63a8', { cuff: '#2a3f6a' }),
        hat: hat([{ t: 'cyl', p: [0, 0.1, 0], s: [2.3, 0.12, 2.0], c: '#c8a860' },
                  { t: 'cyl', p: [0, 0.48, 0], s: [1.32, 0.8, 1.32], c: '#d8b870' }]) }
    ],
    hospital: [
      CLASSIC,
      { shirt: shirt('#a8c8e0', '#a8c8e0', { sleeves: 0.2, weave: 'canvas' }), pants: pants('#a8c8e0', { length: 0.4 }) },
      { shirt: shirt('#e890b0', '#e890b0', { sleeves: 0.3 }), pants: pants('#e890b0'),
        hat: hat([{ t: 'box', p: [0, 0.16, 0.2], s: [1.2, 0.32, 0.8], c: '#f4f4f4' },
                  { t: 'box', p: [0, 0.18, 0.61], s: [0.3, 0.12, 0.02], c: '#d02020' }]) },
      { shirt: shirt('#f4f4f4', '#f4f4f4', { stripe: '#d8d8d8' }), pants: pants('#3aa0a0') },
      { shirt: shirt('#5aa070', '#5aa070', { sleeves: 0.3 }), pants: pants('#5aa070'),
        hat: hat([{ t: 'sph', p: [0, 0.2, 0], s: [1.6, 0.9, 1.6], c: '#5aa070' }]) },
      { shirt: shirt('#2a3a5a', '#2a3a5a', { decal: 'chevron' }), pants: pants('#20283a') },
      { shirt: shirt('#e8f21a', '#2a3a5a', { stripe: '#c8cbcd', weave: 'hivis' }), pants: pants('#2a3a5a') },
      { shirt: shirt('#8a8f94', '#8a8f94', { sleeves: 0.4 }), pants: pants('#4a4f58', { cuff: '#2a2f38' }) }
    ],
    docks: [
      CLASSIC,
      { shirt: shirt('#e9f21a', '#d7c59a', { sleeves: 0.0, stripe: '#c8cbcd', weave: 'hivis' }),
        pants: pants('#3a3f46'),
        hat: hat([{ t: 'sph', p: [0, 0.34, 0], s: [1.62, 1.18, 1.62], c: '#f2b01e' },
                  { t: 'box', p: [0, 0.12, 0.86], s: [1.35, 0.14, 0.7], c: '#f2b01e' }]) },
      { shirt: shirt('#f2f3f3', '#f2f3f3', { stripes: 5, stripe: '#1f3a6a' }), pants: pants('#1f3a6a'),
        hat: hat([{ t: 'cyl', p: [0, 0.18, 0], s: [1.56, 0.36, 1.56], c: '#f2f3f3' },
                  { t: 'cyl', p: [0, 0.04, 0], s: [1.62, 0.1, 1.62], c: '#1f3a6a' }]) },
      { shirt: shirt('#e8c81a', '#e8c81a', { hood: true }), pants: pants('#e8c81a') },
      { shirt: shirt('#3a5a7a', '#3a5a7a', { sleeves: 0.55 }), pants: pants('#3a5a7a', { cuff: '#24384c' }) },
      { shirt: shirt('#6a2a2a', '#6a2a2a', { weave: 'knit' }), pants: pants('#2a2f38'),
        hat: hat([{ t: 'sph', p: [0, 0.22, 0], s: [1.58, 1.0, 1.58], c: '#2a2f38', decal: 'knit' }]) },
      { shirt: shirt('#f4f4f0', '#f4f4f0', { sleeves: 0.3 }), pants: pants('#3a3f46', { length: 0.6 }) },
      { shirt: shirt('#4a5a34', '#4a5a34', { sleeves: 0.6 }), pants: pants('#5a4a34') }
    ],
    camp: [
      CLASSIC,
      { shirt: shirt('#e8782a', '#e8782a', { sleeves: 0.4, decal: 'logo_block' }), pants: pants('#b8a070', { length: 0.5 }) },
      { shirt: shirt('#3a7a3a', '#3a7a3a', { sleeves: 0.35 }), pants: pants('#5a4a34', { length: 0.5 }),
        hat: hat([{ t: 'sph', p: [0, 0.28, 0], s: [1.6, 1.0, 1.6], c: '#3a7a3a' },
                  { t: 'box', p: [0, 0.07, 0.9], s: [1.4, 0.14, 0.86], c: '#2a5a2a' }]) },
      { shirt: shirt('#c8b880', '#c8b880', { sleeves: 0.5, stripe: '#c83a2a' }), pants: pants('#8a7a50', { length: 0.55 }) },
      { shirt: shirt('#d82a2a', '#d82a2a', { sleeves: 0.0 }), pants: pants('#d82a2a', { length: 0.35 }) },
      { shirt: shirt('#4a6a3a', '#4a6a3a', { decal: 'chevron' }), pants: pants('#4a5a3a'),
        hat: hat([{ t: 'cyl', p: [0, 0.1, 0], s: [2.3, 0.12, 2.3], c: '#7a6a3a' },
                  { t: 'cyl', p: [0, 0.48, 0], s: [1.3, 0.8, 1.3], c: '#8a7a4a' }]) },
      { shirt: shirt('#2a6aa8', '#2a6aa8', { hood: true, weave: 'canvas' }), pants: pants('#3a3a3a') },
      { shirt: shirt('#f2f2f2', '#f2f2f2', { sleeves: 0.3, decal: 'flowers' }), pants: pants('#3f63a8', { length: 0.5 }) }
    ]
  };

  /* The specials: each one's silhouette says what it does. */
  var SPECIAL = {
    runner: { skin: '#7fb069', face: FACE_COMMON,
              shirt: shirt('#3a3a3a', '#3a3a3a', { sleeves: 0.0 }),
              pants: pants('#2a2a2a', { length: 0.5, stripe: '#e8e8e8' }) },
    bloater: { skin: '#a8b84a', face: zombieFace('#2a2a10', '#4a5a10'),
               shirt: shirt('#d8d0a0', '#a8b84a', { sleeves: 0.0 }), pants: pants('#4a4a3a') },
    bomber: { skin: '#6c9f68', face: FACE_RED,
              shirt: shirt('#5a4a34', '#5a4a34', { sleeves: 0.5 }), pants: pants('#3a3f46'),
              hat: hat([{ t: 'sph', p: [0, 0.3, 0], s: [1.62, 1.1, 1.62], c: '#3a3f46' },
                        { t: 'box', p: [0, 0.1, 0.9], s: [1.2, 0.1, 0.5], c: '#2a2f36' }]) },
    leaper: { skin: '#7a8a8a', face: FACE_RED,
              shirt: shirt('#3a3f4a', '#3a3f4a', { hood: true, weave: 'canvas' }),
              pants: pants('#2a2a30') },
    brute: { skin: '#4f7a3a', face: FACE_RED,
             shirt: shirt('#7a5230', '#4f7a3a', { sleeves: 0.0 }),
             pants: pants('#2f4f7a', { cuff: '#24384c' }) },
    spitter: { skin: '#9ad84a', face: FACE_GLOW,
               shirt: shirt('#4a6a2a', '#9ad84a', { sleeves: 0.2 }), pants: pants('#3a4a2a'),
               hair: hair([{ p: [0, 0.36, -0.1], s: [1.06, 0.4, 1.0], c: '#2a3a1a' }]) },
    screamer: { skin: '#c8d0c0', face: zombieFace('#141414', '#000000', [
                  { k: 'ellipse', x: 0.0, y: 0.2, w: 0.34, h: 0.42, c: '#000000' }]),
                shirt: shirt('#e8e8e2', '#e8e8e2', { sleeves: 0.6 }),
                pants: pants('#e8e8e2'),
                hair: hair([{ p: [0, 0.3, -0.06], s: [1.1, 0.5, 1.08], c: '#1a1a1a' },
                            { p: [0, -0.3, -0.42], s: [1.08, 1.3, 0.3], c: '#1a1a1a' }]) },
    riot: { skin: '#5f9a4c', face: FACE_COMMON,
            shirt: shirt('#1a1f2a', '#1a1f2a', { decal: 'chevron', stripe: '#3a4050' }),
            pants: pants('#1a1f2a', { cuff: '#0f1218' }),
            hat: hat([{ t: 'sph', p: [0, 0.32, 0], s: [1.7, 1.24, 1.72], c: '#1a1f2a', m: 'metal' },
                      { t: 'box', p: [0, -0.32, 0.84], s: [1.34, 0.9, 0.08], c: '#8ab0c8', a: 0.55 }]) },
    captain: { skin: '#7aa86a', face: zombieFace('#b6ff4a', '#1a3a08', [
                 { k: 'rect', x: -0.22, y: -0.14, w: 0.26, h: 0.2, c: '#111111' },
                 { k: 'rect', x: 0, y: -0.24, w: 0.9, h: 0.04, c: '#111111', rot: -0.3 }]),
               shirt: shirt('#7a1a1a', '#7a1a1a', { stripe: '#d8b84a', decal: 'tux' }),
               pants: pants('#2a2a2a', { cuff: '#4a3a1a' }),
               hat: hat([{ t: 'cyl', p: [0, 0.12, 0], s: [2.4, 0.14, 1.9], c: '#1a1a1a' },
                         { t: 'cyl', p: [0, 0.52, 0], s: [1.4, 0.8, 1.4], c: '#1a1a1a' },
                         { t: 'box', p: [0, 0.22, 0.92], s: [1.6, 0.36, 0.12], c: '#1a1a1a' },
                         { t: 'sph', p: [0, 0.56, 0.72], s: [0.4, 0.4, 0.1], c: '#e8e8e2' }]) },
    hive: { skin: '#9a8a4a', face: zombieFace('#1a0a04', '#3a1a04'),
            shirt: shirt('#5a4a2a', '#8a7a3a', { sleeves: 0.3 }), pants: pants('#4a3a2a') },
    ronin: { skin: '#6a9a5a', face: FACE_RED,
             shirt: shirt('#2a2a3a', '#2a2a3a', { stripe: '#8a1a1a' }),
             pants: pants('#1a1a24'),
             hat: hat([{ t: 'cone', p: [0, 0.42, 0], s: [2.8, 0.8, 2.8], c: '#c8a860' },
                       { t: 'cyl', p: [0, 0.06, 0], s: [1.5, 0.12, 1.5], c: '#8a7040' }]) },
    burrower: { skin: '#7a8a5a', face: FACE_COMMON,
                shirt: shirt('#3a5a7a', '#5a4a34', { sleeves: 0.6, weave: 'canvas' }),
                pants: pants('#3a5a7a'),
                hat: hat([{ t: 'sph', p: [0, 0.34, 0], s: [1.62, 1.18, 1.62], c: '#d8a01a' },
                          { t: 'box', p: [0, 0.12, 0.86], s: [1.35, 0.14, 0.7], c: '#d8a01a' },
                          { t: 'cyl', p: [0, 0.5, 0.82], s: [0.4, 0.4, 0.2], c: '#fff6c0',
                            m: 'neon', r: [1.5708, 0, 0] }]) },
    tank: { skin: '#5a7a4a', face: zombieFace('#c81e1e', '#2a0808'),
            shirt: shirt('#5a7a4a', '#5a7a4a', { sleeves: 0.0 }),
            pants: pants('#3a4a6a', { length: 0.7 }) }
  };

  var PICKAXE = { data: { parts: [
    { t: 'cyl', p: [0, 0, 0.9], s: [0.18, 2.2, 0.18], c: '#6a4a2a', r: [1.5708, 0, 0] },
    { t: 'box', p: [0, 0.4, 1.95], s: [0.2, 0.25, 1.6], c: '#8a8f94', r: [0, 0, 0] }] } };
  var KATANA = { data: { parts: [
    { t: 'box', p: [0, 0, 0.4], s: [0.16, 0.2, 0.8], c: '#1a1a1a' },
    { t: 'box', p: [0, 0, 2.1], s: [0.06, 0.18, 2.8], c: '#d8dde2', m: 'metal' }] } };
  var LANTERN = { data: { parts: [
    { t: 'cyl', p: [0, -0.4, 0.3], s: [0.6, 0.8, 0.6], c: '#9ad84a', m: 'neon' },
    { t: 'box', p: [0, 0.1, 0.3], s: [0.66, 0.12, 0.66], c: '#3a3a2a' }] } };

  var descriptorCache = {};

  /* The rig descriptor for one infected: kind, area and variant. */
  function descriptorFor(kind, area, variant) {
    var key = kind + ':' + area + ':' + variant;
    if (descriptorCache[key]) return descriptorCache[key];
    var look, skin, face;
    if (kind === 'common' || kind === 'mite') {
      var set = WARDROBE[area] || WARDROBE.town;
      look = set[variant % set.length];
      skin = SKINS[variant % SKINS.length];
      face = FACE_COMMON;
    } else {
      look = SPECIAL[kind] || CLASSIC;
      skin = look.skin || SKINS[0];
      face = look.face || FACE_COMMON;
    }
    var faceKey = 'zface_' + (face === FACE_COMMON ? 'common' : kind);
    var desc = {
      body_type: variant % 3 === 1 && kind === 'common' ? 'female' : 'male',
      colors: { head: skin, torso: skin, left_arm: skin, right_arm: skin,
                left_leg: skin, right_leg: skin, hips: skin },
      items: {
        face: { item_id: faceKey, data: { shapes: face } },
        shirt: look.shirt || null, pants: look.pants || null,
        hat: look.hat || null, hair: look.hair || null
      }
    };
    descriptorCache[key] = desc;
    return desc;
  }

  // ------------------------------------------------------------ geometry
  function rotY(x, z, yaw) {
    var c = Math.cos(yaw), s = Math.sin(yaw);
    return [x * c + z * s, -x * s + z * c];
  }

  /* Scale a built rig about its feet: the avatar is authored at one size,
     a Tank is not. */
  function scaleParts(parts, origin, k) {
    if (k === 1) return parts;
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i];
      p.p = [origin[0] + (p.p[0] - origin[0]) * k, origin[1] + (p.p[1] - origin[1]) * k,
             origin[2] + (p.p[2] - origin[2]) * k];
      p.s = [p.s[0] * k, p.s[1] * k, p.s[2] * k];
    }
    return parts;
  }

  /* Tip a whole rig over about a point at its feet: forward for a body
     falling on its face, backward for a survivor down on their back.  Parts
     are turned about the body's own sideways axis, which composes with the
     renderer's yaw-then-pitch order exactly for every part facing the
     body's way (all of them, near enough). */
  function tiltParts(parts, pivot, yaw, angle) {
    if (!angle) return parts;
    var c = Math.cos(angle), s = Math.sin(angle);
    for (var i = 0; i < parts.length; i++) {
      var part = parts[i];
      var dx = part.p[0] - pivot[0], dy = part.p[1] - pivot[1], dz = part.p[2] - pivot[2];
      var local = rotY(dx, dz, -yaw);         // into the body's own frame
      var ly = dy * c - local[1] * s;
      var lz = dy * s + local[1] * c;
      var back = rotY(local[0], lz, yaw);
      part.p = [pivot[0] + back[0], pivot[1] + ly, pivot[2] + back[1]];
      var r = part.r || [0, yaw, 0];
      part.r = [r[0] + angle, r[1], r[2]];
    }
    return parts;
  }

  function push(renderer, parts) {
    for (var i = 0; i < parts.length; i++) renderer.push(parts[i]);
  }

  /* A part in the body's own frame: x across, y up, z forward. */
  function local(pos, yaw, x, y, z) {
    var xz = rotY(x, z, yaw);
    return [pos[0] + xz[0], pos[1] + y, pos[2] + xz[1]];
  }

  function rgb(hex) { return M.hexToRgb(hex); }

  // ========================================================== Survival
  function Survival(client) {
    this.client = client;
    this.zombies = {};
    this.dying = [];
    this.shots = {};
    this.pools = [];
    this.barrels = [];
    this.me = { where: 'field', downed: false, downs: 0, pinned: 0, biled: 0,
                revive: null, struggle: 0 };
    this.markers = {};
    this.area = '';
    this.spectating = false;
    this.lobbyWatch = false;
    this.watchId = 0;
    this.useHeld = false;
    this.promptAt = 0;
    this.groanAt = 0;
    this.lastState = {};
    this.biledUntil = 0;
    this.fogUntil = 0;
    this.bannerTimer = 0;
    this.downedPlayers = {};
    this.time = 0;
    this.buildHud();
  }

  // ------------------------------------------------------------- the map
  Survival.prototype.onMap = function (map) {
    var markers = (map && map.markers) || {};
    this.markers = markers;
    this.area = markers.area || '';
    this.dummies = (markers.dummies || []).map(function (p, i) {
      return { id: 'd' + i, pos: p.slice(), yaw: Math.PI * 0.5, variant: i % 8,
               memory: {} };
    });
    this.zombies = {};
    this.dying = [];
    this.shots = {};
    this.pools = [];
  };

  /* A new area: the whole static world is replaced in place. */
  Survival.prototype.onArea = function (msg) {
    var client = this.client;
    var map = msg.map;
    client.map = map;
    client.physics = new Physics(map, client.constants);
    client.renderer.setSky(map.sky);
    client.renderer.setAmbient(map.ambient);
    if (Textures.dropSigns) Textures.dropSigns();
    client.staticParts = map.parts;
    client.rebuildStatic();
    this.onMap(map);
    this.banner(msg.name || 'A new area', 'Round ' + (msg.round || 1) + ' -- get ready',
                'area');
    client.audio.play('alarm', { volume: 0.4 });
    this.hideWipe();
  };

  // ------------------------------------------------------------ messages
  Survival.prototype.bind = function (net) {
    var self = this;
    net.on('zarea', function (msg) { self.onArea(msg); });
    net.on('zwave', function (msg) { self.onWave(msg); });
    net.on('zwipe', function (msg) { self.onWipe(msg); });
    net.on('zd', function (msg) { self.onZombieDeath(msg); });
    net.on('zfx', function (msg) { self.onZfx(msg); });
    net.on('zdown', function (msg) { self.onDown(msg); });
    net.on('zbar', function (msg) { self.onBarrel(msg); });
    net.on('zpool', function (msg) {
      self.pools.push({ p: msg.p.slice(), r: msg.r, until: self.time + (msg.s || 7),
                        born: self.time });
      self.client.audio.play('splat', { volume: self.client.volumeAt(msg.p) });
    });
    net.on('llme', function (msg) { self.onMe(msg); });
  };

  Survival.prototype.onSnapshot = function (msg) {
    if (msg.zs) {
      var seen = {};
      for (var i = 0; i < msg.zs.length; i++) {
        var row = msg.zs[i];
        var id = row[0];
        seen[id] = true;
        var z = this.zombies[id];
        var target = [row[3], row[4], row[5]];
        if (!z) {
          z = this.zombies[id] = {
            id: id, kind: KINDS[row[1]] || 'common', variant: row[2],
            pos: target.slice(), target: target, yaw: row[6], tyaw: row[6],
            anim: row[7], hp: row[8], flags: row[9], memory: {}, born: this.time,
            seed: (id * 7919) % 1000 / 1000
          };
        }
        z.target = target;
        z.tyaw = row[6];
        z.anim = row[7];
        z.hp = row[8];
        z.flags = row[9];
      }
      for (var key in this.zombies) {
        if (!seen[key]) delete this.zombies[key];
      }
    }
    var live = {};
    (msg.zp || []).forEach(function (row) {
      live[row[0]] = true;
      var shot = this.shots[row[0]];
      if (!shot) {
        shot = this.shots[row[0]] = { kind: row[1], pos: [row[2], row[3], row[4]] };
      }
      shot.target = [row[2], row[3], row[4]];
    }, this);
    for (var sid in this.shots) {
      if (!live[sid]) delete this.shots[sid];
    }
  };

  Survival.prototype.onState = function (state) {
    this.lastState = state || {};
    this.barrels = (state && state.barrels) || this.barrels;
    var downed = {};
    ((state && state.downed) || []).forEach(function (id) { downed[id] = true; });
    this.downedPlayers = downed;
    this.renderTeam();
    this.renderBoss();
  };

  Survival.prototype.onMe = function (msg) {
    var was = this.me;
    this.me = msg;
    var client = this.client;
    if (msg.biled > 0) this.biledUntil = this.time + msg.biled;
    if (msg.downed && !was.downed) {
      client.audio.play('down');
      client.hud.toast('You are down! A teammate has to hold <b>E</b> on you.', 'bad', true);
    }
    if (!msg.downed && was.downed && client.local.alive) {
      client.audio.play('revive');
    }
    if (msg.pinned && !was.pinned) {
      client.hud.toast('Pinned! Mash <b>E</b> to fight it off!', 'bad', true);
    }
    if (msg.where === 'lobby' && was.where !== 'lobby') {
      this.lobbyWatch = false;
    }
    this.renderOverlay();
  };

  Survival.prototype.onWave = function (msg) {
    var client = this.client;
    if (msg.on) {
      var title = 'WAVE ' + msg.wave;
      var sub = msg.tank ? 'A TANK IS COMING' : (msg.total + ' infected incoming');
      if (msg.mod_name) sub += ' -- ' + msg.mod_name + ': ' + msg.mod_blurb;
      this.banner(title, sub, msg.tank ? 'tank' : 'wave');
      client.audio.play('wave');
      if (msg.mod === 'fog') this.fogUntil = this.time + 600;
      else this.fogUntil = 0;
      // the dead and the waiting come in with the wave
      this.lobbyWatch = false;
    } else {
      this.banner('WAVE ' + msg.wave + ' CLEARED',
                  msg.kills + ' infected down in ' + fmt(msg.time || 0) +
                  ' -- wave ' + msg.next + ' in ' + Math.round(msg.in || 20) + 's',
                  'clear');
      client.audio.play('wavewin');
      this.fogUntil = 0;
    }
  };

  Survival.prototype.onWipe = function (msg) {
    var client = this.client;
    client.audio.play('die');
    var rows = (msg.rows || []).map(function (r, i) {
      return '<tr' + (r.id === client.myId ? ' class="me"' : '') + '><td>' + (i + 1) +
        '</td><td class="n">' + client.hud.escape(r.name) + '</td><td>' + r.kills +
        '</td><td>' + r.specials + '</td><td>' + r.revives + '</td><td>' +
        (r.damage || 0).toLocaleString() + '</td></tr>';
    }).join('');
    var card = el('ll-wipe');
    if (!card) return;
    card.innerHTML =
      '<div class="ll-wipe-in"><div class="ll-wipe-k">THE LAST LIGHT WENT OUT</div>' +
      '<h2>' + client.hud.escape(msg.area) + '</h2>' +
      '<div class="ll-wipe-s"><b>' + msg.survived + '</b> wave' +
      (msg.survived === 1 ? '' : 's') + ' survived &bull; <b>' + (msg.kills || 0) +
      '</b> infected killed &bull; ' + fmt(msg.time || 0) + '</div>' +
      '<table><thead><tr><th></th><th class="n">Survivor</th><th>Kills</th>' +
      '<th>Specials</th><th>Revives</th><th>Damage</th></tr></thead><tbody>' + rows +
      '</tbody></table><div class="ll-wipe-next">Next stand: <b>' +
      client.hud.escape(msg.next) + '</b> in <span id="ll-wipe-count">' +
      Math.round(msg['in'] || 12) + '</span>s</div></div>';
    card.classList.add('on');
    var left = Math.round(msg['in'] || 12);
    clearInterval(this.wipeTimer);
    this.wipeTimer = setInterval(function () {
      left -= 1;
      var node = el('ll-wipe-count');
      if (node) node.textContent = Math.max(0, left);
      if (left <= 0) clearInterval(this.wipeTimer);
    }.bind(this), 1000);
  };

  Survival.prototype.hideWipe = function () {
    clearInterval(this.wipeTimer);
    var card = el('ll-wipe');
    if (card) card.classList.remove('on');
  };

  Survival.prototype.onZombieDeath = function (msg) {
    var z = this.zombies[msg.id];
    if (!z) return;
    delete this.zombies[msg.id];
    var client = this.client;
    z.deathAt = this.time;
    z.gone = !!msg.gone;
    z.fall = (Math.random() < 0.5 ? 1 : -1) * (1.35 + Math.random() * 0.25);
    this.dying.push(z);
    if (this.dying.length > 40) this.dying.shift();
    if (msg.gone) return;
    var box = BOX[z.kind] || BOX.common;
    var head = [z.pos[0], z.pos[1] + box[1] * 0.9, z.pos[2]];
    var gore = z.kind === 'bloater' || z.kind === 'spitter' ? '#9ad84a'
      : (z.kind === 'hive' || z.kind === 'mite' ? '#e8a01a' : '#7a1a12');
    client.particles.burst('blood', msg.hs ? head : [z.pos[0], z.pos[1] + box[1] * 0.55, z.pos[2]],
                           { color: gore });
    if (msg.hs) client.particles.burst('blood', head, { color: gore });
    if (msg.by === client.myId) {
      client.audio.play(msg.hs ? 'headshot' : 'zkill', { volume: 0.55 });
      if (msg.hs) client.hud.hitmarker();
    }
    if (z.kind === 'tank') {
      this.banner('TANK DOWN', 'The big one is dead', 'clear');
    }
  };

  Survival.prototype.onZfx = function (msg) {
    var client = this.client;
    var p = msg.p || client.local.pos;
    var vol = client.volumeAt(p);
    var z = this.zombies[msg.id];
    switch (msg.k) {
      case 'lure':
        client.audio.play(msg.s || 'bell', { volume: Math.max(0.35, vol) });
        client.hud.toast('<b>' + client.hud.escape(msg.by || 'Somebody') +
                         '</b> set it off -- they are going for the noise!', 'good');
        this.lureAt = this.time;
        this.lurePos = p;
        break;
      case 'scream':
        client.audio.play('scream', { volume: Math.max(0.3, vol) });
        if (vol > 0.2) client.hud.toast('A <b>Screamer</b> is calling the horde!', 'bad');
        break;
      case 'roar':
        client.audio.play('roar', { volume: Math.max(0.45, vol) });
        break;
      case 'pounce': client.audio.play('pounce', { volume: vol }); break;
      case 'pin':
        client.audio.play('pounce', { volume: vol });
        if (msg.v !== client.myId) {
          var victim = client.players[msg.v];
          if (victim) client.hud.toast('<b>' + client.hud.escape(victim.name) +
                                       '</b> is pinned -- shoot it off!', 'bad');
        }
        break;
      case 'charge': client.audio.play('charge', { volume: Math.max(0.25, vol) }); break;
      case 'thud':
        client.audio.play('land', { volume: vol });
        client.particles.burst('dust', p);
        break;
      case 'spit': client.audio.play('spit', { volume: vol }); break;
      case 'fuse':
        client.audio.play('fuse', { volume: Math.max(0.3, vol) });
        break;
      case 'defuse':
        client.audio.play('defuse', { volume: vol });
        client.particles.burst('impact', p, { color: '#ffd95e' });
        break;
      case 'bile':
        client.audio.play('bile', { volume: vol });
        for (var i = 0; i < 26; i++) {
          client.particles.spawn({ p: [p[0], p[1] + 3, p[2]],
            v: [(Math.random() - 0.5) * 22, Math.random() * 12, (Math.random() - 0.5) * 22],
            life: 0.7 + Math.random() * 0.6, size: 1.0 + Math.random(), grow: 1.6,
            gravity: -14, blend: 'normal', shape: 'puff',
            colors: ['#b8d84a', '#6a8a1a'] });
        }
        break;
      case 'burst':
        client.audio.play('splat', { volume: vol });
        client.particles.burst('blood', [p[0], p[1] + 3, p[2]], { color: '#e8a01a' });
        break;
      case 'bolt': client.audio.play('bolt', { volume: vol }); break;
      case 'boltend':
        client.particles.burst('impact', p, { color: '#9ad84a' });
        break;
      case 'raise':
        client.audio.play('raise', { volume: Math.max(0.25, vol) });
        break;
      case 'dash': client.audio.play('charge', { volume: vol }); break;
      case 'slash': client.audio.play('sword', { volume: vol }); break;
      case 'block':
        client.particles.burst('impact', [p[0], p[1] + 3.5, p[2]], { color: '#ffe8a0' });
        client.audio.play('clang', { volume: vol });
        break;
      case 'burrow':
      case 'surface':
        client.audio.play('burrow', { volume: vol });
        client.particles.burst('dust', p);
        client.particles.burst('dust', [p[0] + 1, p[1], p[2] - 1]);
        break;
      case 'throw': client.audio.play('swing', { volume: vol }); break;
      case 'slam':
      case 'punch':
        client.audio.play('explode', { volume: vol * 0.7 });
        client.particles.burst('dust', p);
        break;
      case 'restock':
        client.audio.play('reload', { volume: 0.8 });
        break;
      default: break;
    }
    if (z && msg.k === 'scream') z.screamAt = this.time;
  };

  Survival.prototype.onDown = function (msg) {
    var client = this.client;
    if (msg.on) this.downedPlayers[msg.id] = true;
    else delete this.downedPlayers[msg.id];
    if (msg.id !== client.myId) {
      var player = client.players[msg.id];
      if (player && msg.on) {
        client.hud.toast('<b>' + client.hud.escape(player.name) +
                         '</b> is down! Hold <b>E</b> on them.', 'bad');
      } else if (player && !msg.on && msg.by) {
        client.hud.toast('<b>' + client.hud.escape(msg.by) + '</b> picked up <b>' +
                         client.hud.escape(player.name) + '</b>', 'good');
      }
    }
    this.renderTeam();
  };

  Survival.prototype.onBarrel = function (msg) {
    if (msg.all) {
      this.barrels = msg.all;
    } else if (msg.alive === false) {
      this.barrels = this.barrels.filter(function (b) { return b[0] !== msg.id; });
    }
  };

  // ------------------------------------------------------------- hooks
  /* How fast the local player may move: crawling when down, not at all
     while something is on top of them. */
  Survival.prototype.moveScale = function () {
    if (this.me.pinned) return 0;
    if (this.me.downed) return 0.27;
    return 1;
  };

  Survival.prototype.canJump = function () {
    return !this.me.pinned && !this.me.downed;
  };

  Survival.prototype.inLobby = function () {
    return this.me.where === 'lobby';
  };

  /* E pressed: struggle, use whatever is in reach, or start a revive. */
  Survival.prototype.useDown = function (repeat) {
    if (repeat && !this.me.pinned) return;
    if (repeat) return;           // mashing means pressing, not holding
    this.useHeld = true;
    this.client.net.send({ t: 'act', k: 'use' });
  };

  Survival.prototype.useUp = function () {
    if (!this.useHeld) return;
    this.useHeld = false;
    this.client.net.send({ t: 'act', k: 'unuse' });
  };

  /* Who the dead (and anybody in the bunker who pressed F) are watching. */
  Survival.prototype.watchable = function () {
    var client = this.client;
    var where = (this.lastState && this.lastState.where) || {};
    var out = [];
    var self = this;
    Object.keys(client.players).forEach(function (id) {
      var player = client.players[id];
      if (!player.alive) return;
      if (where[id] && where[id] !== 'field') return;
      out.push(player);
    });
    out.sort(function (a, b) { return a.id - b.id; });
    return out;
  };

  Survival.prototype.isWatching = function () {
    var local = this.client.local;
    return (!local.alive || (this.inLobby() && this.lobbyWatch)) &&
      this.watchable().length > 0;
  };

  Survival.prototype.cycle = function (step) {
    var list = this.watchable();
    if (!list.length) return;
    var index = 0;
    for (var i = 0; i < list.length; i++) if (list[i].id === this.watchId) index = i;
    index = (index + step + list.length) % list.length;
    this.watchId = list[index].id;
    this.client.audio.play('ui', { volume: 0.3 });
  };

  Survival.prototype.watched = function () {
    var list = this.watchable();
    if (!list.length) return null;
    for (var i = 0; i < list.length; i++) if (list[i].id === this.watchId) return list[i];
    this.watchId = list[0].id;
    return list[0];
  };

  /* The spectator camera: over the shoulder of whoever is being watched,
     orbited with the mouse, pulled in when a wall is in the way. */
  Survival.prototype.camera = function () {
    var client = this.client;
    var target = this.watched();
    if (!target) return null;
    var yaw = client.local.yaw, pitch = Math.max(-1.1, Math.min(0.9, client.local.pitch));
    var cp = Math.cos(pitch);
    var dir = [Math.sin(yaw) * cp, Math.sin(pitch), Math.cos(yaw) * cp];
    var pivot = [target.pos[0], target.pos[1] + 5.4, target.pos[2]];
    var back = [-dir[0], -dir[1], -dir[2]];
    var distance = 16;
    if (client.physics) {
      distance = Math.min(16, Math.max(3.5, client.physics.rayDistance(pivot, back, 18) - 1.4));
    }
    return { eye: [pivot[0] + back[0] * distance, pivot[1] + back[1] * distance,
                   pivot[2] + back[2] * distance], yaw: yaw, pitch: pitch };
  };

  /* The first-person eye drops to the floor while down. */
  Survival.prototype.eyeDrop = function () {
    return this.me.downed ? 3.2 : 0;
  };

  /* Where a tracer stops: the nearest infected in its way. */
  Survival.prototype.rayHit = function (origin, dir, maxDistance) {
    var best = maxDistance;
    for (var id in this.zombies) {
      var z = this.zombies[id];
      if (z.flags & F.HIDDEN) continue;
      var box = BOX[z.kind] || BOX.common;
      var hit = rayBox(origin, dir,
                       [z.pos[0] - box[0] / 2, z.pos[1], z.pos[2] - box[0] / 2],
                       [z.pos[0] + box[0] / 2, z.pos[1] + box[1], z.pos[2] + box[0] / 2]);
      if (hit !== null && hit < best) best = hit;
    }
    return best;
  };

  function rayBox(origin, dir, lo, hi) {
    var tmin = 0, tmax = Infinity;
    for (var axis = 0; axis < 3; axis++) {
      var o = origin[axis], d = dir[axis];
      if (Math.abs(d) < 1e-8) {
        if (o < lo[axis] || o > hi[axis]) return null;
        continue;
      }
      var t1 = (lo[axis] - o) / d, t2 = (hi[axis] - o) / d;
      if (t1 > t2) { var tmp = t1; t1 = t2; t2 = tmp; }
      tmin = Math.max(tmin, t1); tmax = Math.min(tmax, t2);
      if (tmin > tmax) return null;
    }
    return tmin >= 0 ? tmin : null;
  }

  /* What E would do from here, for the prompt under the crosshair. */
  Survival.prototype.updatePrompt = function () {
    var client = this.client;
    var hud = client.hud;
    var me = this.me;
    var local = client.local;
    if (!local.alive) { hud.setPrompt(null); return; }
    if (me.pinned) {
      hud.setPrompt('<b>MASH E</b> to fight it off (' + (me.struggle || 0) + '/9)');
      return;
    }
    if (me.downed) {
      hud.setPrompt(me.revive ? 'Being revived by <b>' + hud.escape(me.revive[2]) + '</b>...'
                    : 'You are down -- stay near your team. You can still shoot.');
      return;
    }
    if (me.revive) {
      hud.setPrompt('Reviving <b>' + hud.escape(me.revive[2]) + '</b>... keep holding E');
      return;
    }
    if (this.inLobby()) {
      hud.setPrompt(this.lobbyWatch ? 'Watching the survivors -- <b>F</b> to look away, click to switch'
                    : 'You deploy with the next wave. <b>F</b> watch the survivors &bull; <b>E</b> restock at the range');
      return;
    }
    var pos = local.pos;
    var best = null, bestD = 7;
    var self = this;
    Object.keys(this.downedPlayers).forEach(function (id) {
      var player = client.players[id];
      if (!player || !player.alive) return;
      var d = Math.hypot(player.pos[0] - pos[0], player.pos[2] - pos[2]);
      if (d < bestD) { bestD = d; best = player; }
    });
    if (best) { hud.setPrompt('Hold <b>E</b> to revive <b>' + hud.escape(best.name) + '</b>'); return; }
    var markers = this.markers;
    var lure = markers.lure;
    var state = this.lastState || {};
    if (lure && dist(lure.p, pos) < 9.5) {
      var info = state.lure || {};
      hud.setPrompt(info.ready > 0
        ? hud.escape(lure.name) + ' -- ready in <b>' + Math.ceil(info.ready) + 's</b>'
        : '<b>E</b> ' + hud.escape(lure.verb) + ' (draws the horde for 16s)');
      return;
    }
    var ammo = (markers.ammo || []).some(function (p) { return dist(p, pos) < 7.5; });
    if (ammo) { hud.setPrompt('<b>E</b> Restock ammunition'); return; }
    var med = -1;
    (markers.med || []).forEach(function (p, i) { if (dist(p, pos) < 7.5) med = i; });
    if (med >= 0) {
      var left = (state.med || [])[med];
      hud.setPrompt(left > 0 ? '<b>E</b> First aid (+50 health, resets downs) -- ' + left + ' left'
                    : 'First-aid cabinet: empty until the next wave');
      return;
    }
    hud.setPrompt(null);
  };

  function dist(a, b) {
    return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  }

  function fmt(seconds) {
    seconds = Math.max(0, Math.floor(seconds));
    return Math.floor(seconds / 60) + ':' + (seconds % 60 < 10 ? '0' : '') + seconds % 60;
  }

  // -------------------------------------------------------------- hud
  function el(id) { return document.getElementById(id); }

  Survival.prototype.buildHud = function () {
    if (el('ll-hud')) return;
    var root = document.createElement('div');
    root.id = 'll-hud';
    root.innerHTML =
      '<div id="ll-boss"><div class="ll-boss-name">TANK</div><div class="ll-boss-bar"><i></i></div></div>' +
      '<div id="ll-team"></div>' +
      '<div id="ll-banner"><div class="t"></div><div class="s"></div></div>' +
      '<div id="ll-down"><div class="t">YOU ARE DOWN</div><div class="s"></div>' +
      '<div class="ll-bar"><i></i></div></div>' +
      '<div id="ll-revive"><div class="s"></div><div class="ll-bar"><i></i></div></div>' +
      '<div id="ll-watch"><div class="t"></div><div class="s"></div></div>' +
      '<div id="ll-vignette"></div><div id="ll-bile"></div>' +
      '<div id="ll-wipe"></div>';
    var parent = document.querySelector('#game-root .hud') || document.body;
    parent.appendChild(root);
  };

  Survival.prototype.banner = function (title, sub, kind) {
    var node = el('ll-banner');
    if (!node) return;
    node.querySelector('.t').textContent = title;
    node.querySelector('.s').textContent = sub || '';
    node.className = 'on ' + (kind || '');
    clearTimeout(this.bannerTimer);
    this.bannerTimer = setTimeout(function () { node.className = ''; }, 4200);
  };

  Survival.prototype.updateObjective = function (state) {
    var red = el('score-red'), blue = el('score-blue');
    var mode = el('score-mode'), timer = el('obj-timer'), sub = el('obj-sub');
    var panel = el('objective');
    if (red) red.textContent = '';
    if (blue) blue.textContent = '';
    var wave = state.wave || 0;
    var phase = state.wphase || 'setup';
    if (mode) {
      mode.innerHTML = '<span class="ll-wave">' + (phase !== 'setup' ? 'WAVE ' + wave
        : (wave ? 'WAVE ' + wave + ' CLEARED' : 'GET READY')) + '</span>' +
        '<span class="ll-area">' + this.client.hud.escape(state.area_name || '') + '</span>';
    }
    if (timer) {
      if (phase === 'active') {
        timer.textContent = (state.zleft || 0) + ' infected left' +
          (state.tank && state.tank.length ? '  --  TANK' : '');
      } else if (phase === 'wiped') {
        timer.textContent = 'Everybody is down';
      } else {
        timer.textContent = 'Wave ' + (wave + 1) + ' in ' + fmt(state.phase_left || 0);
      }
    }
    if (sub) {
      var bits = [];
      bits.push((state.alive || 0) + '/' + (state.field || 0) + ' alive');
      if (state.downed && state.downed.length) bits.push(state.downed.length + ' down');
      if (state.lobby) bits.push(state.lobby + ' waiting');
      if (state.modifier_name) bits.push('<b style="color:#ffd95e">' + state.modifier_name + '</b>');
      if (state.best) bits.push('best: wave ' + state.best);
      sub.innerHTML = bits.join(' &bull; ');
    }
    if (panel) panel.classList.toggle('urgent', !!(state.tank && state.tank.length));
    this.onState(state);
  };

  Survival.prototype.renderTeam = function () {
    var node = el('ll-team');
    if (!node) return;
    var client = this.client;
    var state = this.lastState || {};
    var where = state.where || {};
    var rows = [];
    var self = this;
    var me = { id: client.myId, name: BH.user.name, health: client.local.health,
               alive: client.local.alive };
    var list = [me].concat(Object.keys(client.players).map(function (id) {
      return client.players[id];
    }));
    list.forEach(function (p) {
      var status = where[p.id] || 'field';
      var downed = !!self.downedPlayers[p.id] || (p.id === client.myId && self.me.downed);
      var cls = status === 'lobby' ? 'wait' : (!p.alive ? 'dead' : (downed ? 'down' : ''));
      var hp = Math.max(0, Math.min(100, Math.round(p.health || 0)));
      var label = status === 'lobby' ? 'bunker' : (!p.alive ? 'dead' : (downed ? 'DOWN' : hp));
      rows.push('<div class="ll-mate ' + cls + (p.id === client.myId ? ' me' : '') + '">' +
                '<span class="n">' + client.hud.escape(p.name || '?') + '</span>' +
                '<span class="h"><i style="width:' + (p.alive && status !== 'lobby' ? hp : 0) +
                '%"></i></span><span class="v">' + label + '</span></div>');
    });
    node.innerHTML = rows.slice(0, 12).join('');
  };

  Survival.prototype.renderBoss = function () {
    var node = el('ll-boss');
    if (!node) return;
    var tanks = (this.lastState && this.lastState.tank) || [];
    if (!tanks.length) { node.classList.remove('on'); return; }
    node.classList.add('on');
    var frac = tanks.reduce(function (a, b) { return a + b; }, 0) / tanks.length;
    node.querySelector('i').style.width = Math.max(0, frac * 100) + '%';
    node.querySelector('.ll-boss-name').textContent = tanks.length > 1
      ? 'TANKS x' + tanks.length : 'TANK';
  };

  Survival.prototype.renderOverlay = function () {
    var me = this.me;
    var down = el('ll-down');
    if (down) {
      down.classList.toggle('on', !!me.downed && this.client.local.alive);
      var sub = down.querySelector('.s');
      if (sub) {
        sub.textContent = me.revive ? 'Being revived by ' + me.revive[2] + '...'
          : (me.downs >= 2 ? 'Last chance -- the next fall is the last'
            : 'Hold on. A teammate can pick you up with E.');
      }
    }
    var vignette = el('ll-vignette');
    if (vignette) vignette.classList.toggle('on', !!me.downed || !!me.pinned);
  };

  /* Per frame: the bars that move smoothly, and the spectator caption. */
  Survival.prototype.updateHud = function (dt) {
    var client = this.client;
    var me = this.me;
    var down = el('ll-down');
    if (down && me.downed) {
      down.querySelector('i').style.width = Math.max(0, client.local.health) + '%';
    }
    var revive = el('ll-revive');
    if (revive) {
      var active = me.revive && !me.downed;
      revive.classList.toggle('on', !!active);
      if (active) {
        revive.querySelector('.s').textContent = 'Reviving ' + me.revive[2];
        revive.querySelector('i').style.width = Math.min(100, me.revive[1] * 100) + '%';
      }
    }
    var bile = el('ll-bile');
    if (bile) bile.classList.toggle('on', this.time < this.biledUntil);
    var watch = el('ll-watch');
    if (watch) {
      var watching = this.isWatching();
      watch.classList.toggle('on', watching || !client.local.alive);
      if (watching || !client.local.alive) {
        var target = this.watched();
        var state = this.lastState || {};
        var next = (state.wphase === 'active' ? 'You come back when wave ' + ((state.wave || 0) + 1) +
                    ' begins' : 'You come back when the next wave begins');
        if (this.inLobby() && client.local.alive) next = 'Waiting in the holdout -- you deploy with the next wave';
        watch.querySelector('.t').textContent = target ? 'Watching ' + target.name
          : 'Nobody left standing';
        watch.querySelector('.s').textContent = next + '  --  click to switch';
      }
    }
    if (this.time - this.promptAt > 0.2) {
      this.promptAt = this.time;
      this.updatePrompt();
      this.renderTeam();
    }
  };

  // ------------------------------------------------------------ drawing
  Survival.prototype.draw = function (renderer, dt) {
    var client = this.client;
    this.time += dt;
    var time = this.time;
    var camera = renderer.eye || client.local.pos;
    var far = Math.min(renderer.far || 900, 700);
    var lerp = Math.min(1, dt * 12);
    // fog bank: the view closes in for the wave
    if (this.time < this.fogUntil) {
      if (!this.savedFar) this.savedFar = renderer.far;
      renderer.far = Math.min(this.savedFar, 240);
    } else if (this.savedFar) {
      renderer.far = this.savedFar;
      this.savedFar = 0;
    }
    var near = 0;
    for (var id in this.zombies) {
      var z = this.zombies[id];
      z.pos[0] += (z.target[0] - z.pos[0]) * lerp;
      z.pos[1] += (z.target[1] - z.pos[1]) * lerp;
      z.pos[2] += (z.target[2] - z.pos[2]) * lerp;
      var dy = ((z.tyaw - z.yaw + Math.PI) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2) - Math.PI;
      z.yaw += dy * Math.min(1, dt * 10);
      var d = Math.hypot(z.pos[0] - camera[0], z.pos[2] - camera[2]);
      if (d > far) continue;
      if (d < 60) near++;
      this.drawZombie(renderer, z, time, dt, d, 0);
      if (d < 140 && z.kind !== 'common' && z.kind !== 'runner' && z.kind !== 'mite' &&
          !(z.flags & F.HIDDEN) && Settings.showNames) {
        var box = BOX[z.kind] || BOX.common;
        var colour = z.kind === 'tank' ? '#ff6a4a' : '#ffb84a';
        renderer.queueTag('z' + z.id, NAMES[z.kind], colour, z.hp + '%',
                          [z.pos[0], z.pos[1] + box[1] * (SCALE[z.kind] || 1) * 0.1 + box[1] + 1.4,
                           z.pos[2]], Math.max(0.8, Math.min(2.6, 0.8 + d * 0.012)));
      } else if (z.kind !== 'common') {
        renderer.dropTag('z' + z.id);
      }
    }
    // the dying: they fall, lie still a moment and sink away
    for (var i = 0; i < this.dying.length; i++) {
      var body = this.dying[i];
      var age = time - body.deathAt;
      renderer.dropTag('z' + body.id);
      if (age > (body.gone ? 0.6 : 3.4)) { this.dying.splice(i, 1); i--; continue; }
      this.drawZombie(renderer, body, time, dt,
                      Math.hypot(body.pos[0] - camera[0], body.pos[2] - camera[2]), age);
    }
    // practice dummies in the holdout
    (this.dummies || []).forEach(function (dummy) {
      this.drawZombie(renderer, { id: dummy.id, kind: 'common', variant: dummy.variant,
                                  pos: dummy.pos, yaw: dummy.yaw, anim: A.GUARD, hp: 100,
                                  flags: 0, memory: dummy.memory, seed: 0.3, area: 'town' },
                      time, dt, 10, 0, true);
    }, this);
    this.drawShots(renderer, dt);
    this.drawBarrels(renderer, time);
    this.drawPools(renderer, dt);
    this.drawSupplies(renderer, time, camera);
    this.drawDowned(renderer, time, camera);
    // a groan now and then from something close
    if (near && time > this.groanAt) {
      this.groanAt = time + 1.2 + Math.random() * 2.2 / Math.min(4, near);
      var keys = Object.keys(this.zombies);
      var pick = this.zombies[keys[(Math.random() * keys.length) | 0]];
      if (pick && !(pick.flags & F.HIDDEN)) {
        var vol = client.volumeAt(pick.pos) * 0.55;
        if (vol > 0.08) client.audio.play(pick.kind === 'tank' ? 'growl' : 'groan',
                                          { volume: vol });
      }
    }
    this.updateHud(dt);
  };

  /* One infected: the rig in its area's clothes, posed for what it is
     doing, plus whatever its kind carries. */
  Survival.prototype.drawZombie = function (renderer, z, time, dt, distance, deathAge, dummy) {
    var kind = z.kind;
    var flags = z.flags || 0;
    if (flags & F.HIDDEN) {
      // underground: only the trail of earth it pushes up
      var pos0 = z.pos;
      renderer.pushRaw('sph', pos0[0], pos0[1] + 0.2, pos0[2], 0, 0, 0, 3.4, 1.2, 3.4,
                       rgb('#5a4a34'), 1, 0, 0, 0, null);
      if (Settings.particles && Math.random() < 0.35) {
        this.client.particles.burst('dust', [pos0[0], pos0[1] + 0.3, pos0[2]]);
      }
      return;
    }
    if (kind === 'mite') { this.drawMite(renderer, z, time, deathAge); return; }
    var scale = SCALE[kind] || 1;
    var pos = z.pos;
    if (distance > 300 && !deathAge) {
      // far away: a coloured silhouette is all anyone can see
      var box = BOX[kind] || BOX.common;
      var look = descriptorFor(kind, z.area || this.area, z.variant);
      renderer.pushRaw('box', pos[0], pos[1] + box[1] * 0.3, pos[2], 0, z.yaw, 0,
                       box[0] * 0.6, box[1] * 0.6, box[2] * 0.7,
                       rgb((look.items.shirt && look.items.shirt.data.torso) || '#7a5230'),
                       1, 0, 0, 0, null);
      renderer.pushRaw('box', pos[0], pos[1] + box[1] * 0.85, pos[2], 0, z.yaw, 0,
                       box[0] * 0.45, box[1] * 0.25, box[2] * 0.6, rgb(look.colors.head),
                       1, 0, 0, 0, null);
      return;
    }
    var desc = descriptorFor(kind, z.area || this.area, z.variant);
    var anim = z.anim;
    var state = anim === A.RUN || anim === A.CHARGE ? 'run'
      : (anim === A.ATTACK || anim === A.WALK || anim === A.CLIMB ? 'walk' : 'idle');
    if (dummy) state = 'idle';
    var t = time * (kind === 'runner' ? 1.15 : 0.8) + (z.seed || 0) * 10;
    var pose = Avatar.smoothPose(z.memory, deathAge ? 'idle' : state, t, 0, desc, dt);
    pose = Object.assign({}, pose);
    var reach = -1.45 + Math.sin(t * 3.1) * 0.12;
    pose.armL = reach + Math.sin(t * 2.3) * 0.08;
    pose.armR = reach - Math.sin(t * 2.3) * 0.08;
    pose.lean = (pose.lean || 0) + 0.16;
    var yOffset = 0;
    var tilt = 0;
    switch (anim) {
      case A.RUN:
        pose.armL = -1.15 + Math.sin(t * 11) * 0.5;
        pose.armR = -1.15 - Math.sin(t * 11) * 0.5;
        pose.lean += 0.25;
        break;
      case A.ATTACK:
        pose.armR = -1.7 + Math.sin(time * 12 + z.seed * 5) * 0.9;
        pose.armL = -1.5 - Math.sin(time * 12 + z.seed * 5) * 0.7;
        pose.lean += 0.12;
        break;
      case A.LEAP:
      case A.PIN:
        pose.armL = pose.armR = -2.3;
        pose.legL = -0.9; pose.legR = 0.6;
        pose.lean += 0.7;
        if (anim === A.PIN) {
          pose.armR = -2.0 + Math.sin(time * 16) * 0.6;
          pose.armL = -2.0 - Math.sin(time * 16) * 0.6;
          yOffset = -1.2;
        }
        break;
      case A.SCREAM:
        pose.armL = -0.5; pose.armR = -0.5;
        pose.armLZ = 1.1; pose.armRZ = -1.1;
        pose.lean = -0.3;
        break;
      case A.STUN:
        pose.armL = -0.3; pose.armR = -0.4;
        pose.lean = Math.sin(time * 9) * 0.18 - 0.1;
        break;
      case A.CLIMB:
        pose.armL = -2.9 + Math.sin(time * 9) * 0.4;
        pose.armR = -2.9 - Math.sin(time * 9) * 0.4;
        pose.lean = -0.1;
        break;
      case A.THROW:
        pose.armL = pose.armR = -3.0;
        pose.lean = -0.2;
        break;
      case A.SLAM:
        pose.armL = pose.armR = -2.6 + Math.sin(time * 14) * 1.2;
        break;
      case A.RISE:
        yOffset = -Math.max(0, 1 - (time - (z.born || 0)) / 1.4) * 5.0;
        pose.armL = pose.armR = -2.6;
        break;
      case A.SPIT:
        pose.lean = -0.25;
        pose.armL = pose.armR = -0.6;
        break;
      case A.CHARGE:
        pose.lean += 0.45;
        if (kind === 'brute') { pose.armR = -0.9; pose.armL = -0.2; }
        break;
      case A.GUARD:
        if (kind === 'ronin') { pose.armR = -1.25; pose.armL = -1.0; }
        break;
      default: break;
    }
    if (kind === 'tank') {
      pose.lean += 0.12;
      if (anim !== A.ATTACK && anim !== A.THROW && anim !== A.SLAM) {
        pose.armL = -0.4 + Math.sin(t * 4) * 0.3;
        pose.armR = -0.4 - Math.sin(t * 4) * 0.3;
        pose.armLZ = 0.35; pose.armRZ = -0.35;
      }
    }
    if (kind === 'captain' && anim !== A.SCREAM) {
      pose.armR = -1.1;
    }
    if (deathAge) {
      // falling over: a quick topple, a bounce, then sinking into the ground
      var f = Math.min(1, deathAge / 0.55);
      tilt = (z.fall || 1.4) * (f * f);
      if (deathAge > 2.2) yOffset = -(deathAge - 2.2) * 3.0;
    }
    var holding = null;
    if (kind === 'burrower') holding = PICKAXE;
    else if (kind === 'ronin') holding = KATANA;
    else if (kind === 'captain') holding = LANTERN;
    var origin = [pos[0], pos[1] + yOffset, pos[2]];
    var parts = Avatar.build(desc, { position: origin, yaw: z.yaw, pitch: 0, time: time,
                                     pose: pose, holding: holding });
    this.dressExtras(parts, kind, origin, z, time, pose);
    scaleParts(parts, origin, scale);
    if (tilt) tiltParts(parts, origin, z.yaw, tilt);
    var fade = 1;
    if (deathAge && z.gone) fade = Math.max(0, 1 - deathAge / 0.6);
    if (fade < 1) parts.forEach(function (p) { p.a = fade; });
    if (flags & F.ENRAGED && !deathAge) {
      parts.forEach(function (p) { if (p.k === 'head') p.m = 'neon'; });
    }
    push(renderer, parts);
    if (!deathAge && distance < 200) this.client.drawShadow(pos);
    if ((flags & F.FUSE) && !deathAge && Math.sin(time * 26) > 0) {
      var light = local(origin, z.yaw, 0, 4.0 * scale, 1.0 * scale);
      renderer.pushRaw('sph', light[0], light[1], light[2], 0, 0, 0, 0.9, 0.9, 0.9,
                       [1, 0.15, 0.1], 1, 0, 2, 1, null);
    }
  };

  /* The things that make a special what it is, built on to the rig in the
     body's own frame before it is scaled. */
  Survival.prototype.dressExtras = function (parts, kind, origin, z, time, pose) {
    var yaw = z.yaw;
    var lean = pose.lean || 0;
    function add(t, x, y, zz, s, c, extra) {
      var at = local(origin, yaw, x, y, zz + Math.sin(lean) * (y - 2.5) * 0.6);
      var part = { t: t, p: at, s: s, c: c, r: [lean * 0.6, yaw, 0] };
      if (extra) for (var k in extra) part[k] = extra[k];
      parts.push(part);
    }
    if (kind === 'bloater') {
      add('sph', 0, 2.9, 0.55, [3.4, 3.2, 3.0], '#b8c45a');
      add('sph', 0.9, 3.6, 1.6, [0.7, 0.7, 0.5], '#d8e07a');
      add('sph', -0.7, 2.4, 1.75, [0.6, 0.6, 0.4], '#d8e07a');
      add('sph', 0.3, 1.9, 1.6, [0.5, 0.5, 0.4], '#c8a03a');
      add('sph', -1.3, 3.2, 0.9, [0.55, 0.55, 0.45], '#d8e07a');
    } else if (kind === 'bomber') {
      for (var i = 0; i < 6; i++) {
        var a = -0.9 + i * 0.36;
        add('cyl', Math.sin(a) * 1.0, 3.3, Math.cos(a) * 0.62 + 0.05, [0.32, 1.2, 0.32], '#c82a1a');
      }
      add('box', 0, 3.75, 0.62, [2.0, 0.18, 0.2], '#2a2a2a');
      add('box', 0.25, 3.0, 0.78, [0.5, 0.4, 0.16], '#2a2a2a');
    } else if (kind === 'brute') {
      // one arm grown into a club
      add('rbox', -1.65, 2.6, 0.3, [1.5, 2.6, 1.5], '#4f7a3a', { k: 'arm' });
      add('sph', -1.75, 1.4, 0.6, [1.6, 1.4, 1.6], '#3f6a2a');
    } else if (kind === 'spitter') {
      add('box', 0, 4.1, 0.8, [0.3, 0.6, 0.1], '#b6ff4a', { m: 'neon' });
    } else if (kind === 'riot') {
      // the shield, carried in front on the left arm
      add('box', 0.85, 2.7, 1.25, [1.9, 3.6, 0.22], '#20283a', { m: 'metal' });
      add('box', 0.85, 3.4, 1.37, [1.5, 0.6, 0.04], '#c8d0d8', { dec: 't~POLICE~#20283a~#f2f3f3~4.50' });
    } else if (kind === 'hive') {
      var lumps = [[0.7, 3.4, 0.7], [-0.6, 3.0, 0.8], [0.2, 2.4, 0.9], [-1.0, 3.7, 0.0],
                   [0.9, 2.8, -0.5], [0.1, 3.8, -0.8], [-0.4, 2.3, -0.8]];
      lumps.forEach(function (l, n) {
        add('sph', l[0], l[1], l[2], [1.1 + n % 3 * 0.25, 0.9 + n % 2 * 0.3, 1.0],
            n % 2 ? '#e8a01a' : '#c88a1a');
      });
      if (Settings.particles && Math.random() < 0.15) {
        this.client.particles.spawn({ p: local(origin, yaw, 0, 4.2, 0),
          v: [(Math.random() - 0.5) * 3, Math.random() * 2, (Math.random() - 0.5) * 3],
          life: 0.8, size: 0.18, grow: 0, gravity: 0, blend: 'normal', shape: 'spark',
          colors: ['#1a1a1a', '#e8a01a'] });
      }
    } else if (kind === 'tank') {
      // shoulders like boulders and a back hunched over them
      add('rbox', 0, 3.85, -0.2, [3.6, 1.6, 2.0], '#5a7a4a');
      add('sph', 1.55, 3.7, 0, [1.7, 1.7, 1.7], '#4f6f40');
      add('sph', -1.55, 3.7, 0, [1.7, 1.7, 1.7], '#4f6f40');
      add('rbox', 1.7, 2.2, 0.4, [1.4, 2.4, 1.4], '#5a7a4a');
      add('rbox', -1.7, 2.2, 0.4, [1.4, 2.4, 1.4], '#5a7a4a');
      if (z.anim === A.THROW) add('rbox', 0, 6.4, 0.3, [2.4, 2.0, 2.2], '#7a6a5a');
    } else if (kind === 'captain') {
      if (Settings.particles && Math.random() < 0.25) {
        this.client.particles.spawn({ p: local(origin, yaw, -0.9, 2.0, 1.2),
          v: [0, 1.5, 0], life: 0.9, size: 0.5, grow: 1.2, gravity: 0.5, blend: 'add',
          shape: 'puff', colors: ['#b6ff4a', '#2a6a10'] });
      }
    } else if (kind === 'screamer' && z.screamAt && time - z.screamAt < 1.8) {
      var ring = (time - z.screamAt) * 22;
      add('torus', 0, 4.6, 0, [ring, 0.3, ring], '#e8e8f8', { a: Math.max(0, 0.6 - (time - z.screamAt) * 0.33) });
    }
  };

  Survival.prototype.drawMite = function (renderer, z, time, deathAge) {
    var pos = z.pos, yaw = z.yaw;
    var y = pos[1] + 0.7 - (deathAge ? Math.min(0.6, deathAge) : 0);
    renderer.pushRaw('sph', pos[0], y, pos[2], 0, yaw, 0, 1.4, 0.9, 1.8,
                     rgb('#c88a1a'), 1, 0, 0, 0, null);
    var head = local([pos[0], y, pos[2]], yaw, 0, 0.2, 1.0);
    renderer.pushRaw('sph', head[0], head[1], head[2], 0, yaw, 0, 0.7, 0.6, 0.6,
                     rgb('#2a1a0a'), 1, 0, 0, 0, null);
    for (var i = 0; i < 6; i++) {
      var side = i < 3 ? 1 : -1;
      var along = (i % 3 - 1) * 0.5;
      var leg = local([pos[0], y - 0.3, pos[2]], yaw, side * 0.95, 0, along);
      var wiggle = deathAge ? 0 : Math.sin(time * 30 + i) * 0.4;
      renderer.pushRaw('box', leg[0], leg[1], leg[2], 0, yaw, side * (0.7 + wiggle),
                       0.9, 0.12, 0.12, rgb('#1a1a1a'), 1, 0, 0, 0, null);
    }
  };

  Survival.prototype.drawShots = function (renderer, dt) {
    var lerp = Math.min(1, dt * 18);
    var client = this.client;
    for (var id in this.shots) {
      var shot = this.shots[id];
      for (var k = 0; k < 3; k++) shot.pos[k] += (shot.target[k] - shot.pos[k]) * lerp;
      var p = shot.pos;
      if (shot.kind === 'rock') {
        renderer.pushRaw('rbox', p[0], p[1], p[2], this.time * 3, this.time * 2, 0,
                         2.6, 2.2, 2.4, rgb('#7a6a5a'), 1, 0, 0, 0, null);
      } else {
        var colour = shot.kind === 'acid' ? [0.6, 1, 0.25] : [0.7, 1, 0.3];
        renderer.pushRaw('sph', p[0], p[1], p[2], 0, 0, 0, 1.2, 1.2, 1.2,
                         colour, 0.9, 0, 2, 1, null);
        if (Settings.particles && Math.random() < 0.7) {
          client.particles.spawn({ p: p, v: [0, -0.5, 0], life: 0.4, size: 0.6, grow: 0.6,
            gravity: -4, blend: 'add', shape: 'puff',
            colors: shot.kind === 'acid' ? ['#b6ff4a', '#3a6a10'] : ['#d8ff8a', '#2a4a08'] });
        }
      }
    }
  };

  Survival.prototype.drawBarrels = function (renderer, time) {
    for (var i = 0; i < this.barrels.length; i++) {
      var b = this.barrels[i];
      var x = b[1], y = b[2], z = b[3];
      renderer.pushRaw('cyl', x, y + 1.8, z, 0, 0, 0, 2.4, 3.6, 2.4, rgb('#c8281a'),
                       1, 0, 1, 0, null);
      renderer.pushRaw('cyl', x, y + 1.1, z, 0, 0, 0, 2.5, 0.18, 2.5, rgb('#8a1a10'),
                       1, 0, 1, 0, null);
      renderer.pushRaw('cyl', x, y + 2.5, z, 0, 0, 0, 2.5, 0.18, 2.5, rgb('#8a1a10'),
                       1, 0, 1, 0, null);
      renderer.pushRaw('box', x, y + 1.8, z + 1.2, 0, 0, 0, 1.0, 1.0, 0.04,
                       rgb('#ffd23a'), 1, 0, 0, 0, null);
    }
  };

  Survival.prototype.drawPools = function (renderer, dt) {
    var keep = [];
    for (var i = 0; i < this.pools.length; i++) {
      var pool = this.pools[i];
      var left = pool.until - this.time;
      if (left <= 0) continue;
      keep.push(pool);
      var grow = Math.min(1, (this.time - pool.born) * 3);
      var r = pool.r * 2 * grow;
      var alpha = Math.min(0.7, left * 0.5);
      renderer.pushRaw('cyl', pool.p[0], pool.p[1] + 0.12, pool.p[2], 0, 0, 0, r, 0.08, r,
                       [0.45, 0.95, 0.15], alpha, 0, 2, 0.8, null);
      if (Settings.particles && Math.random() < 0.3) {
        var a = Math.random() * Math.PI * 2, d = Math.random() * pool.r * grow;
        this.client.particles.spawn({ p: [pool.p[0] + Math.cos(a) * d, pool.p[1] + 0.2,
                                          pool.p[2] + Math.sin(a) * d],
          v: [0, 1.8, 0], life: 0.6, size: 0.35, grow: 0.4, gravity: 0, blend: 'add',
          shape: 'puff', colors: ['#b6ff4a', '#3a6a10'] });
      }
    }
    // pools also come from the state, for anyone who joined while one sat
    var state = this.lastState || {};
    if (!keep.length && state.pools && state.pools.length && !this.poolsSeeded) {
      this.poolsSeeded = true;
      var self = this;
      state.pools.forEach(function (row) {
        keep.push({ p: [row[0], row[1], row[2]], r: row[3], until: self.time + row[4],
                    born: self.time - 1 });
      });
    }
    this.pools = keep;
  };

  /* A soft beacon over every ammo crate and cabinet, so a player who has
     never been here can find them, and the lure's glow while it sounds. */
  Survival.prototype.drawSupplies = function (renderer, time, camera) {
    var markers = this.markers;
    var state = this.lastState || {};
    var pulse = 0.5 + Math.sin(time * 3) * 0.2;
    (markers.ammo || []).forEach(function (p) {
      if (dist(p, camera) > 220) return;
      renderer.pushRaw('cyl', p[0], p[1] + 9, p[2], 0, 0, 0, 0.5, 14, 0.5,
                       [1, 0.82, 0.3], 0.18 * pulse, 0, 2, 1, null);
    });
    (markers.med || []).forEach(function (p, i) {
      if (dist(p, camera) > 220) return;
      var empty = (state.med || [])[i] === 0;
      renderer.pushRaw('cyl', p[0], p[1] + 9, p[2], 0, 0, 0, 0.5, 14, 0.5,
                       empty ? [0.5, 0.5, 0.5] : [0.4, 1, 0.5], 0.18 * pulse, 0, 2, 1, null);
    });
    var lure = markers.lure;
    if (lure && state.lure && state.lure.on) {
      var f = lure.focus;
      var ring = 6 + (time * 18) % 40;
      renderer.pushRaw('torus', f[0], f[1] + 1, f[2], 0, 0, 0, ring, 0.6, ring,
                       [1, 0.8, 0.3], Math.max(0, 0.5 - ring / 90), 0, 2, 1, null);
    }
  };

  /* A downed teammate: on their back, with a beacon and a tag over them so
     they can be found in a crowd. */
  Survival.prototype.drawDowned = function (renderer, time, camera) {
    var client = this.client;
    for (var id in this.downedPlayers) {
      var player = client.players[id];
      if (!player || !player.alive) continue;
      var d = dist(player.pos, camera);
      renderer.pushRaw('cyl', player.pos[0], player.pos[1] + 12, player.pos[2], 0, 0, 0,
                       0.7, 22, 0.7, [1, 0.25, 0.2], 0.22 + Math.sin(time * 6) * 0.08,
                       0, 2, 1, null);
      if (d < 400) {
        renderer.queueTag('down' + id, player.name + ' -- DOWN', '#ff8a7a', 'hold E to revive',
                          [player.pos[0], player.pos[1] + 5.2, player.pos[2]],
                          Math.max(0.9, Math.min(3, 0.9 + d * 0.01)));
      }
    }
  };

  /* Remote players who are down are drawn lying on their backs, the rig
     tipped over at the feet. */
  Survival.prototype.layDown = function (parts, player, self) {
    if (!self && !this.downedPlayers[player.id]) return parts;
    var pivot = [player.pos[0], player.pos[1] + 0.6, player.pos[2]];
    return tiltParts(parts, pivot, player.yaw, -1.45);
  };

  Survival.prototype.isDowned = function (id) {
    return !!this.downedPlayers[id];
  };

  global.Survival = Survival;
  global.Survival.KINDS = KINDS;
  global.Survival.descriptorFor = descriptorFor;
  global.Survival.dressFor = function (kind) { return SPECIAL[kind]; };
})(window);
