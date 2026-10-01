/* BLOCKHAVEN engine -- the infected of Last Light, as the rig draws them.

   Shared by the Game View (game/survival.js, which places them where the
   server says and animates what they do) and the website (the world page's
   bestiary portraits and the area dioramas in ui/thumbs.js), so a Leaper on
   the world page is the same Leaper that comes over the fence.

   Every one is the ordinary avatar rig dressed by a descriptor: the commons
   in whatever their area's people died in, the specials in their own gear,
   all of them the same green skin, two dot eyes and open O of a mouth --
   with the parts that make a special what it is (the Bloater's belly, the
   Bomber's vest, the Riot's shield, the Tank's shoulders) built on to the
   body before it is scaled to size. */
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

  /* A part in the body's own frame: x across, y up, z forward. */
  function local(pos, yaw, x, y, z) {
    var xz = rotY(x, z, yaw);
    return [pos[0] + xz[0], pos[1] + y, pos[2] + xz[1]];
  }

  function rgb(hex) { return M.hexToRgb(hex); }

  /* The things that make a special what it is, built on to the rig in the
     body's own frame before it is scaled. */
  function dressExtras(parts, kind, origin, z, time, pose, fx) {
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
      if (fx && Math.random() < 0.15) {
        fx({ p: local(origin, yaw, 0, 4.2, 0),
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
      if (fx && Math.random() < 0.25) {
        fx({ p: local(origin, yaw, -0.9, 2.0, 1.2),
          v: [0, 1.5, 0], life: 0.9, size: 0.5, grow: 1.2, gravity: 0.5, blend: 'add',
          shape: 'puff', colors: ['#b6ff4a', '#2a6a10'] });
      }
    } else if (kind === 'screamer' && z.screamAt && time - z.screamAt < 1.8) {
      var ring = (time - z.screamAt) * 22;
      add('torus', 0, 4.6, 0, [ring, 0.3, ring], '#e8e8f8', { a: Math.max(0, 0.6 - (time - z.screamAt) * 0.33) });
    }
  }

  function mite(z, time, deathAge) {
    var out = [];
    var pos = z.pos, yaw = z.yaw;
    var y = pos[1] + 0.7 - (deathAge ? Math.min(0.6, deathAge) : 0);
    out.push({ t: 'sph', p: [pos[0], y, pos[2]], s: [1.4, 0.9, 1.8], c: '#c88a1a',
               r: [0, yaw, 0] });
    var head = local([pos[0], y, pos[2]], yaw, 0, 0.2, 1.0);
    out.push({ t: 'sph', p: head, s: [0.7, 0.6, 0.6], c: '#2a1a0a', r: [0, yaw, 0] });
    for (var i = 0; i < 6; i++) {
      var side = i < 3 ? 1 : -1;
      var along = (i % 3 - 1) * 0.5;
      var leg = local([pos[0], y - 0.3, pos[2]], yaw, side * 0.95, 0, along);
      var wiggle = deathAge ? 0 : Math.sin(time * 30 + i) * 0.4;
      out.push({ t: 'box', p: leg, s: [0.9, 0.12, 0.12], c: '#1a1a1a',
                 r: [0, yaw, side * (0.7 + wiggle)] });
    }
    return out;
  }

  /* Every part of one infected, ready to push.

     ``z`` is anything with kind, variant, pos, yaw, anim, flags, seed, born
     and a ``memory`` object of its own (the pose cross-fade lives there);
     ``deathAge`` is seconds since it died (0 while it lives).  ``fx`` is
     handed particle specs for the few kinds that trail something, and may
     be null. */
  function build(z, area, time, dt, deathAge, dummy, fx) {
    var kind = z.kind;
    var flags = z.flags || 0;
    var scale = SCALE[kind] || 1;
    var pos = z.pos;
    if (kind === 'mite') return mite(z, time, deathAge);
    var desc = descriptorFor(kind, area, z.variant);
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
    dressExtras(parts, kind, origin, z, time, pose, fx);
    scaleParts(parts, origin, scale);
    if (tilt) tiltParts(parts, origin, z.yaw, tilt);
    var fade = 1;
    if (deathAge && z.gone) fade = Math.max(0, 1 - deathAge / 0.6);
    if (fade < 1) parts.forEach(function (p) { p.a = fade; });
    if (flags & F.ENRAGED && !deathAge) {
      parts.forEach(function (p) { if (p.k === 'head') p.m = 'neon'; });
    }
    return parts;
  }

  /* The fused vest's blinking light, for the Game View. */
  function fuseLight(z) {
    var scale = SCALE[z.kind] || 1;
    return local(z.pos, z.yaw, 0, 4.0 * scale, 1.0 * scale);
  }

  global.Zombies = {
    KINDS: KINDS, NAMES: NAMES, BOX: BOX, SCALE: SCALE, ANIM: A, FLAGS: F,
    descriptorFor: descriptorFor, build: build, fuseLight: fuseLight,
    tiltParts: tiltParts, scaleParts: scaleParts, local: local
  };
})(window);
