/* BLOCKHAVEN engine -- the avatar base system.
   One rig, driven entirely by a descriptor from the server, used by the
   profile preview, the avatar editor, item thumbnails and the game itself.

   The rig is built from rounded boxes rather than hard cubes, with a neck, a
   tapered torso and softened limbs, so a bare default character already has a
   silhouette instead of reading as a stack of blocks.

   Four builds ship, as two families of two: "male" and its slimmer cut
   "male_thin", "female" and its slimmer cut "female_thin".  Every one of them
   keeps RIG.headTop, the eye height and the hitbox exactly where they are,
   which is what guarantees every hat, face and outfit fits all four with no
   per-type variant.  Cosmetics that colour the body (shirts, trousers) are
   driven from the same metrics, so they follow whichever silhouette is in
   use.

   The female builds carry their own head -- narrower, shallower and a little
   softer than the male one, because the shared head read as wide and
   jutting on a slighter body -- and their own gait: the pelvis swings,
   twists and drops through the stride while the shoulders counter-rotate,
   rather than the limbs simply swinging from a fixed trunk. */
(function (global) {
  'use strict';

  var M = GLX.mat;

  var HEIGHT = 5.4;          // feet to the top of the head, all body types
  var HEAD_TOP = 5.4;

  /* The male head.  The width is pinned at 1.46 because the tightest brims in
     the catalogue are 1.56-1.62 across and the skull has to stay inside them;
     the friendlier proportion therefore comes out of the other two axes.  It
     is wider than it is tall (1.14:1 rather than the old 1.07:1) and a little
     deeper, which reads as a round face rather than a tall brick, and the top
     stays pinned to HEAD_TOP so every hat anchor, the eye height and the
     hitbox are all untouched.  The neck is shorter and thicker so the head
     sits down on the shoulders instead of being served up on a post -- a
     short neck is most of what makes a character read as cute. */
  var HEAD = {
    size: [1.46, 1.28, 1.40],
    centre: [0, 4.76, 0],
    mesh: 'rhead',
    neck: { size: [0.70, 0.30, 0.66], y: 4.03 }
  };

  /* The female head.  Same top (5.4), same face plate, same hat anchor --
     but 0.18 narrower and 0.18 shallower, so it stops overhanging the
     shoulders and stops jutting out in front of the chest.  It loses a
     little height with it, which keeps it from reading as a long face now
     that it is narrow, and it is baked with a slightly softer bevel
     (rheadf) so the smaller skull still rounds off rather than turning
     back into a brick.  The neck is proportionally slimmer to match. */
  var HEAD_F = {
    size: [1.28, 1.24, 1.22],
    centre: [0, 4.78, 0],
    mesh: 'rheadf',
    neck: { size: [0.54, 0.34, 0.52], y: 4.05 }
  };

  /* The builds differ by silhouette, not by parts: the same segments, the
     same anchors, different measurements.

     "male" reads as a near-uniform block (the waist is only a hair narrower
     than the chest).  "male_thin" is the same build drawn slighter -- narrow
     shoulders, a real waist, hips back out to shoulder width and slimmer,
     slightly longer limbs.

     The two female builds are an hourglass rather than a taper: shoulders in,
     a bust that carries the chest forward, a cinched waist, hips flared
     wider than the shoulders and a seat that rounds the profile out behind.
     Their legs are full at the thigh and slim at the calf, and stand closer
     together.  "female_thin" is the same figure with slimmer arms, a
     narrower ribcage and a longer, shapelier leg, so the curve reads harder
     against the narrower frame rather than softer.

     Consecutive torso segments overlap by more than their two bevels put
     together, because rounded boxes that merely touch leave a groove between
     them and the torso reads as a stack of trays rather than one body. */
  var BODIES = {
    male: {
      id: 'male',
      label: 'Male',
      family: 'male',
      gait: 'masc',
      head: HEAD,
      // Stacked torso segments, top first; "decal" marks the one a shirt
      // graphic is printed on (here 0.32 of overlap against 0.20 of bevel).
      torso: [
        { size: [2.00, 1.39, 1.06], y: 3.315, decal: true },
        { size: [1.94, 0.94, 1.02], y: 2.47 }
      ],
      chest: { size: [2.00, 1.30, 1.06], y: 3.36 },
      waistLine: 2.00,
      hips: { size: [1.96, 0.38, 1.06], y: 2.06 },
      // narrow across, deeper front to back: a rectangle in section, not a
      // post.  x moves in with the half-width so the inner face still
      // meets the torso at the same place and the shoulder joint is sound.
      arm: { size: [0.82, 2.02, 0.96], x: 1.36, pivotY: 3.98 },
      leg: { size: [1.00, 2.00, 1.02], x: 0.52, pivotY: 2.00 },
      foot: { size: [1.06, 0.28, 1.24], z: 0.10 },
      backAnchor: [0, 3.02, -0.54]
    },
    male_thin: {
      id: 'male_thin',
      label: 'Thin',
      family: 'male',
      gait: 'masc',
      head: HEAD,
      // Three segments of two widths.  The top two share a width so there is
      // no step across the front, but the upper one is deeper -- which reads
      // as a chest in profile and leaves the front flat for a shirt graphic.
      // Each pair overlaps by 0.20 against a combined bevel of 0.13, so the
      // three read as one tapering body instead of three slabs.
      torso: [
        { size: [1.56, 0.73, 1.00], y: 3.645 },
        { size: [1.56, 0.82, 0.90], y: 3.07, decal: true },
        { size: [1.38, 0.70, 0.84], y: 2.51 }
      ],
      chest: { size: [1.56, 1.26, 0.95], y: 3.38 },
      waistLine: 2.16,
      hips: { size: [1.70, 0.54, 0.98], y: 2.12 },
      arm: { size: [0.64, 2.12, 0.78], x: 1.07, pivotY: 3.99 },
      leg: { size: [0.76, 2.12, 0.86], x: 0.40, pivotY: 2.12 },
      foot: { size: [0.82, 0.24, 1.04], z: 0.10 },
      backAnchor: [0, 3.06, -0.46]
    },
    female: {
      id: 'female',
      label: 'Female',
      family: 'female',
      gait: 'fem',
      head: HEAD_F,
      /* Five thin segments rather than two thick ones.  Thin segments are
         what let the width move on every one of them -- 1.34 across the
         shoulders, out again over the chest, in hard at the waist, then out
         past the shoulders at the hip -- without any one step being big
         enough to read as a shelf.  The shirt graphic goes on the chest
         segment, at the height a print sits on a tee.

         The waist also sits higher than the male one, which is the other
         half of the silhouette: it leaves the legs 46% of the total height
         instead of 40%, and a long leg under a short waist is most of what
         separates this build from the one it replaced. */
      torso: [
        { size: [1.28, 0.44, 0.78], y: 3.86 },
        { size: [1.22, 0.58, 0.76], y: 3.48, decal: true },
        { size: [1.04, 0.44, 0.72], y: 3.12 },
        { size: [0.92, 0.38, 0.68], y: 2.86 },
        { size: [1.16, 0.32, 0.78], y: 2.66 }
      ],
      /* The chest curve is a pair of soft domes rather than a deeper box: a
         box deep enough to read as a bust in profile also reads as a barrel
         from the front, and a shirt graphic printed on it bows.  They are
         set close enough together to overlap across the centre line, so the
         two read as one curve with a cleft rather than as two bumps, and
         they take the shirt colour with the rest of the trunk -- which is
         how every shirt in the catalogue covers them without knowing they
         are there. */
      bust: { size: [0.92, 0.48, 0.58], x: 0.19, y: 3.36, z: 0.17 },
      chest: { size: [1.22, 0.58, 0.76], y: 3.48 },
      waistLine: 2.86,
      hips: { size: [1.50, 0.50, 0.88], y: 2.44 },
      // ...and the same trick behind, which is what puts the curve in the
      // silhouette seen from the side.  It takes the trousers colour,
      // because it is part of the lower body.
      seat: { size: [1.00, 0.58, 0.68], x: 0.22, y: 2.32, z: -0.24 },
      arm: { size: [0.52, 2.02, 0.62], x: 0.87, pivotY: 3.98 },
      // full at the thigh, slim at the calf: the leg proper is the calf and
      // "thigh" is the wider block dropped over the top of it, which is one
      // extra part per leg for the whole difference between a post and a
      // shape
      leg: { size: [0.50, 2.44, 0.62], x: 0.40, pivotY: 2.44 },
      thigh: { size: [0.62, 1.12, 0.78], drop: 0.0 },
      foot: { size: [0.64, 0.26, 0.86], z: 0.10 },
      backAnchor: [0, 3.20, -0.42]
    },
    female_thin: {
      id: 'female_thin',
      label: 'Thin',
      family: 'female',
      gait: 'fem',
      head: HEAD_F,
      // the same figure on a smaller frame: the shoulders and ribcage come
      // in, the hips barely move, and the legs get longer again -- so the
      // flare reads harder here than it does on the standard build rather
      // than softer
      torso: [
        { size: [1.16, 0.44, 0.72], y: 3.88 },
        { size: [1.10, 0.58, 0.70], y: 3.50, decal: true },
        { size: [0.92, 0.44, 0.66], y: 3.14 },
        { size: [0.80, 0.38, 0.62], y: 2.88 },
        { size: [1.08, 0.32, 0.72], y: 2.68 }
      ],
      bust: { size: [0.86, 0.46, 0.54], x: 0.18, y: 3.38, z: 0.16 },
      chest: { size: [1.10, 0.58, 0.70], y: 3.50 },
      waistLine: 2.88,
      hips: { size: [1.44, 0.48, 0.82], y: 2.48 },
      seat: { size: [0.96, 0.56, 0.64], x: 0.21, y: 2.36, z: -0.23 },
      arm: { size: [0.44, 2.06, 0.54], x: 0.80, pivotY: 3.99 },
      leg: { size: [0.44, 2.48, 0.56], x: 0.38, pivotY: 2.48 },
      thigh: { size: [0.56, 1.14, 0.70], drop: 0.0 },
      foot: { size: [0.60, 0.24, 0.82], z: 0.10 },
      backAnchor: [0, 3.22, -0.40]
    }
  };

  var RIG = {
    head: HEAD,
    height: HEIGHT,
    headTop: HEAD_TOP,
    hipY: 2.0,
    bodies: BODIES,
    // legacy shorthands a few callers still read
    torso: { size: BODIES.male.chest.size, centre: [0, 3.0, 0] },
    arm: { size: BODIES.male.arm.size, pivotY: BODIES.male.arm.pivotY,
           x: BODIES.male.arm.x },
    leg: { size: BODIES.male.leg.size, pivotY: BODIES.male.leg.pivotY,
           x: BODIES.male.leg.x }
  };

  var Avatar = {
    RIG: RIG,
    BODY_TYPES: ['male', 'male_thin', 'female', 'female_thin'],
    // short enough for a chip, and they say which family a Thin cut is from
    BODY_LABELS: {
      male: 'Male', male_thin: 'Male thin',
      female: 'Female', female_thin: 'Female thin'
    },
    // The first person camera sits a touch above the middle of the head so the
    // view reads as "behind the eyes" rather than "inside the chin".
    EYE_HEIGHT: 5.05,
    // Third person orbits the old, lower pivot so that camera is unchanged.
    CHASE_PIVOT: 4.85
  };

  Avatar.body = function (descriptor) {
    var key = descriptor && (descriptor.body_type || descriptor.body);
    if (typeof descriptor === 'string') key = descriptor;
    return BODIES[key] || BODIES.male;
  };

  function rotateY(x, z, yaw) {
    var c = Math.cos(yaw), s = Math.sin(yaw);
    return [x * c + z * s, -x * s + z * c];
  }

  /* Rotate a point around the X axis (used for limb swing). */
  function rotateX(y, z, angle) {
    var c = Math.cos(angle), s = Math.sin(angle);
    return [y * c - z * s, y * s + z * c];
  }

  /* A point ``down`` units down a limb from its joint, ``forward`` units in
     front of it and ``lateral`` units out to its side, carried through the
     limb's own roll and then its swing.  The renderer composes Ry * Rx * Rz,
     so rolling first and swinging second is exactly what the part's own
     rotation does -- which is what keeps the top of a rolled limb pinned in
     its joint instead of drifting out of the shoulder, and what keeps a
     trouser stripe on the outside of a leg that is rolled inwards.  Returns
     an offset from the joint. */
  function limbPoint(down, forward, swing, roll, lateral) {
    var c = Math.cos(roll || 0), s = Math.sin(roll || 0);
    lateral = lateral || 0;
    var yz = rotateX(lateral * s - down * c, forward || 0, swing);
    return [lateral * c + down * s, yz[0], yz[1]];
  }

  function colourOf(descriptor, key, fallback) {
    var colors = descriptor.colors || {};
    return colors[key] || fallback || '#f5cd30';
  }

  function itemData(descriptor, slot) {
    var items = descriptor.items || {};
    return items[slot] || null;
  }

  function blankPose() {
    return {
      // limbs
      armL: 0, armR: 0, legL: 0, legR: 0, armLZ: 0, armRZ: 0,
      // whole body
      lean: 0, bob: 0,
      // the pelvis, which is a moving part in its own right on the female
      // rigs: it slides across, drops on one side and turns with the stride
      hipShift: 0, hipRoll: 0, hipTwist: 0, legPinch: 0, legRoll: 0,
      // ...and the trunk, which answers it rather than riding it
      torsoShift: 0, torsoTwist: 0, chestRoll: 0
    };
  }

  /* The original gait: the limbs swing from a trunk that stays put. */
  function mascPose(pose, state, time) {
    if (state === 'walk' || state === 'run') {
      var rate = state === 'run' ? 9.5 : 7.0;
      var amp = state === 'run' ? 0.85 : 0.62;
      var phase = time * rate;
      pose.legL = Math.sin(phase) * amp;
      pose.legR = -Math.sin(phase) * amp;
      pose.armL = -Math.sin(phase) * amp * 0.85;
      pose.armR = Math.sin(phase) * amp * 0.85;
      pose.armLZ = 0.06;
      pose.armRZ = -0.06;
      pose.bob = Math.abs(Math.sin(phase)) * 0.10;
      pose.lean = state === 'run' ? 0.09 : 0.045;
    } else if (state === 'jump') {
      pose.armL = -2.1; pose.armR = -2.1;
      pose.legL = -0.25; pose.legR = 0.35;
    } else if (state === 'fall') {
      pose.armL = -1.5; pose.armR = -1.5;
      pose.legL = 0.3; pose.legR = -0.2;
    } else if (state === 'sit') {
      pose.legL = -1.5; pose.legR = -1.5;
      pose.armL = -0.4; pose.armR = -0.4;
    } else {
      pose.armL = Math.sin(time * 1.4) * 0.035;
      pose.armR = -Math.sin(time * 1.4) * 0.035;
      // a relaxed idle keeps the arms just off the torso
      pose.armLZ = 0.07;
      pose.armRZ = -0.07;
      pose.bob = Math.sin(time * 1.4) * 0.02;
    }
    return pose;
  }

  /* The female gait.  What separates it from the one above is that the
     pelvis is animated rather than welded to the spine: it slides across to
     sit over whichever leg is carrying the weight, lifts on the side the
     swinging leg hangs from, and turns with the stride while the shoulders
     turn against it.  The feet track closer to the centre line than the hips
     are wide (``legPinch``) and roll very slightly inwards, which is most of
     the difference between a walk and a march.  The arms swing less, hang
     further from the body, and the whole thing carries a smaller vertical
     bounce, because a long stride with a quiet head is what reads as poise.

     Every field here is an offset applied in ``Avatar.build``; nothing about
     the geometry, the anchors or the hitbox changes, so the same animation
     runs safely on a character wearing anything in the catalogue. */
  function femPose(pose, state, time) {
    var phase, swing;
    if (state === 'walk' || state === 'run') {
      var running = state === 'run';
      var rate = running ? 9.0 : 6.6;
      var amp = running ? 0.84 : 0.58;
      phase = time * rate;
      swing = Math.sin(phase);
      pose.legL = swing * amp;
      pose.legR = -swing * amp;
      pose.armL = -swing * amp * 0.5;
      pose.armR = swing * amp * 0.5;
      pose.armLZ = running ? 0.13 : 0.17;
      pose.armRZ = -pose.armLZ;
      pose.bob = Math.abs(Math.sin(phase)) * (running ? 0.115 : 0.07);
      pose.lean = running ? 0.10 : 0.05;
      // the pelvis: across to the standing leg, up on the swinging side
      pose.hipShift = -swing * (running ? 0.10 : 0.13);
      pose.hipRoll = swing * (running ? 0.10 : 0.13);
      pose.hipTwist = swing * (running ? 0.22 : 0.17);
      pose.legPinch = running ? 0.38 : 0.30;
      pose.legRoll = running ? 0.08 : 0.06;
      // the shoulders turn against the hips and stay over the centre line
      pose.torsoTwist = -pose.hipTwist * 0.66;
      pose.torsoShift = -pose.hipShift * 0.30;
      pose.chestRoll = -pose.hipRoll * 0.40;
    } else if (state === 'jump') {
      pose.armL = -2.25; pose.armR = -2.25;
      pose.armLZ = 0.24; pose.armRZ = -0.24;
      pose.legL = -0.34; pose.legR = 0.40;
      pose.legPinch = 0.5; pose.legRoll = 0.12;
      pose.hipRoll = 0.05; pose.lean = 0.06;
    } else if (state === 'fall') {
      pose.armL = -1.62; pose.armR = -1.62;
      pose.armLZ = 0.3; pose.armRZ = -0.3;
      pose.legL = 0.34; pose.legR = -0.18;
      pose.legPinch = 0.3; pose.legRoll = 0.08;
    } else if (state === 'sit') {
      pose.legL = -1.5; pose.legR = -1.5;
      pose.armL = -0.35; pose.armR = -0.35;
      pose.armLZ = 0.1; pose.armRZ = -0.1;
      pose.legPinch = 0.6; pose.legRoll = 0.1;
      pose.hipTwist = 0.1; pose.torsoTwist = -0.08;
    } else {
      /* Contrapposto: the weight is on one leg and stays there, so the idle
         is a held pose that breathes rather than a body swaying between two
         feet.  The slow sine is the breath; the constants are the stance. */
      var breath = Math.sin(time * 1.25);
      pose.armL = breath * 0.03;
      pose.armR = -breath * 0.03;
      pose.armLZ = 0.16;
      pose.armRZ = -0.18;
      pose.bob = breath * 0.018;
      pose.hipShift = -0.075 + breath * 0.012;
      pose.hipRoll = 0.075 + breath * 0.012;
      pose.hipTwist = -0.05;
      pose.legPinch = 0.12;
      pose.legRoll = 0.04;
      pose.torsoShift = 0.03;
      pose.torsoTwist = 0.05;
      pose.chestRoll = -0.035;
    }
    return pose;
  }

  /* Compute the animation pose for a given state.

     ``who`` is optional and may be a descriptor or a body-type name; it
     picks the gait.  Callers that do not pass it get the original one, so
     every existing three-argument call still means exactly what it did. */
  Avatar.pose = function (state, time, speed, who) {
    var pose = blankPose();
    speed = speed === undefined ? 0 : speed;
    var body = who ? Avatar.body(who) : null;
    if (body && body.gait === 'fem') return femPose(pose, state, time);
    return mascPose(pose, state, time);
  };

  /* Build every renderable part for one character.
     opts: {position, yaw, pitch, pose, holding, dead, scale} */
  Avatar.build = function (descriptor, opts) {
    descriptor = descriptor || {};
    opts = opts || {};
    var body = Avatar.body(descriptor);
    var head = body.head || HEAD;
    var parts = [];
    var pos = opts.position || [0, 0, 0];
    var yaw = opts.yaw || 0;
    var pose = opts.pose || Avatar.pose('idle', 0, 0, descriptor);
    var shirt = itemData(descriptor, 'shirt');
    var pants = itemData(descriptor, 'pants');
    var hat = itemData(descriptor, 'hat');
    var face = itemData(descriptor, 'face');
    var back = itemData(descriptor, 'back');
    var shirtData = (shirt && shirt.data) || {};
    var pantsData = (pants && pants.data) || {};
    var bob = pose.bob || 0;
    var lean = pose.lean || 0;
    // the pelvis and the trunk each carry their own small transform, which
    // is zero on the builds whose gait does not use them
    var hipShift = pose.hipShift || 0;
    var hipRoll = pose.hipRoll || 0;
    var hipTwist = pose.hipTwist || 0;
    var legPinch = pose.legPinch || 0;
    var legRoll = pose.legRoll || 0;
    var torsoShift = pose.torsoShift || 0;
    var torsoTwist = pose.torsoTwist || 0;
    var chestRoll = pose.chestRoll || 0;

    function place(local, size, colour, extra) {
      var xz = rotateY(local[0], local[2], yaw);
      var part = {
        t: (extra && extra.t) || 'rbox',
        p: [pos[0] + xz[0], pos[1] + local[1] + bob, pos[2] + xz[1]],
        s: size,
        c: colour,
        r: [(extra && extra.rx) || 0, yaw + ((extra && extra.ry) || 0),
            (extra && extra.rz) || 0]
      };
      if (extra) {
        if (extra.decSlot) part.decSlot = extra.decSlot;
        if (extra.dec) part.dec = extra.dec;
        if (extra.m) part.m = extra.m;
        if (extra.a !== undefined) part.a = extra.a;
        if (extra.st) part.st = extra.st;
        if (extra.k) part.k = extra.k;
      }
      parts.push(part);
      return part;
    }

    /* Place something that belongs to the trunk: it slides and turns with
       the shoulders.  ``x``/``z`` are measured on the un-twisted body. */
    function placeTrunk(x, y, z, size, colour, extra) {
      var o = rotateY(x + torsoShift, z || 0, torsoTwist);
      extra = extra || {};
      extra.ry = torsoTwist;
      if (extra.rz === undefined) extra.rz = chestRoll;
      if (extra.rx === undefined) extra.rx = lean;
      return place([o[0], y, o[1]], size, colour, extra);
    }

    /* ...and something that belongs to the pelvis, which has its own slide,
       turn and side-to-side drop. */
    function placePelvis(x, y, z, size, colour, extra) {
      var o = rotateY(x + hipShift, z || 0, hipTwist);
      extra = extra || {};
      extra.ry = hipTwist;
      if (extra.rz === undefined) extra.rz = hipRoll;
      return place([o[0], y + x * hipRoll, o[1]], size, colour, extra);
    }

    // --------------------------------------------------------------- torso
    var torsoColour = shirtData.torso || colourOf(descriptor, 'torso', '#0d69ac');
    var torsoDecal = null;
    if (shirtData.decal) torsoDecal = Textures.decal(shirtData.decal);
    body.torso.forEach(function (segment) {
      placeTrunk(0, segment.y, 0, segment.size.slice(), torsoColour, {
        decSlot: segment.decal ? torsoDecal : null, k: 'torso'
      });
    });
    /* The chest curve is two soft domes sitting just proud of the chest
       segment rather than a deeper box, so the front stays flat enough for a
       shirt graphic to print square on it.  They take the shirt's own colour
       with the rest of the trunk, so every shirt in the catalogue covers
       them without knowing they exist. */
    if (body.bust) {
      [-1, 1].forEach(function (side) {
        placeTrunk(body.bust.x * side, body.bust.y, body.bust.z,
                   body.bust.size.slice(), torsoColour, { t: 'sph', k: 'torso' });
      });
    }
    // hips read as part of the lower body, so they take the trousers colour
    var hipColour = pantsData.legs || colourOf(descriptor, 'left_leg', '#a4bd47');
    placePelvis(0, body.hips.y, 0, body.hips.size.slice(), hipColour, { k: 'hips' });
    if (body.seat) {
      [-1, 1].forEach(function (side) {
        placePelvis(body.seat.x * side, body.seat.y, body.seat.z,
                    body.seat.size.slice(), hipColour, { t: 'sph', k: 'hips' });
      });
    }

    var lowest = body.torso[body.torso.length - 1];
    if (shirtData.stripe) {
      placeTrunk(0, lowest.y - lowest.size[1] / 2 + 0.18, 0,
                 [lowest.size[0] + 0.04, 0.34, lowest.size[2] + 0.04],
                 shirtData.stripe, { k: 'torso' });
    }
    if (shirtData.stripes) {
      var span = body.chest.size[1] - 0.3;
      for (var si = 0; si < shirtData.stripes; si++) {
        var t = shirtData.stripes > 1 ? si / (shirtData.stripes - 1) : 0.5;
        placeTrunk(0, body.chest.y - span / 2 + span * t, 0,
                   [body.chest.size[0] + 0.03, 0.15, body.chest.size[2] + 0.03],
                   shirtData.stripe || '#1b2a35', { k: 'torso' });
      }
    }
    if (shirtData.hood) {
      placeTrunk(0, body.chest.y + body.chest.size[1] / 2 - 0.06, -0.34,
                 [body.chest.size[0] * 0.86, 0.62, 0.72],
                 shirtData.torso || torsoColour, { rx: 0, rz: chestRoll, k: 'torso' });
    }

    // ---------------------------------------------------------------- neck
    var headColour = colourOf(descriptor, 'head', '#f5cd30');
    place([0, head.neck.y, 0], head.neck.size.slice(), headColour,
          { t: 'cyl', k: 'neck' });

    // ---------------------------------------------------------------- head
    var faceSlot = null;
    if (face && face.data) faceSlot = Textures.faceSlot(face.item_id, face.data);
    place([0, head.centre[1], 0], head.size.slice(), headColour, {
      t: head.mesh || 'rhead', decSlot: faceSlot, k: 'head'
    });

    // ---------------------------------------------------------------- arms
    var armLen = body.arm.size[1];
    function arm(side, swing, roll) {
      var shoulder = body.arm.x * side;
      var pivotY = body.arm.pivotY;
      var half = armLen / 2;
      roll = roll || 0;
      // the shoulder turns with the trunk, and the limb hangs from it
      function at(down) {
        var o = limbPoint(down, 0, swing, roll);
        var xz = rotateY(shoulder + torsoShift + o[0], o[2], torsoTwist);
        return [xz[0], pivotY + o[1], xz[1]];
      }
      var centre = at(half);
      var skin = colourOf(descriptor, side < 0 ? 'right_arm' : 'left_arm', '#f5cd30');
      var sleeve = shirtData.arms;
      var coverage = shirtData.sleeves === undefined ? 1.0 : shirtData.sleeves;
      var extra = { t: 'rlimb', rx: swing, ry: torsoTwist, rz: roll, k: 'arm' };
      if (sleeve && coverage >= 0.99) {
        place(centre, body.arm.size.slice(), sleeve, extra);
      } else if (sleeve && coverage > 0.01) {
        var upperLen = armLen * coverage;
        place(at(upperLen / 2),
              [body.arm.size[0] * 1.02, upperLen, body.arm.size[2] * 1.02],
              sleeve, extra);
        var lowerLen = armLen - upperLen;
        place(at(upperLen + lowerLen / 2),
              [body.arm.size[0], lowerLen, body.arm.size[2]], skin, extra);
      } else {
        place(centre, body.arm.size.slice(), skin, extra);
      }
      var hand = at(armLen);
      return { x: hand[0], y: hand[1], z: hand[2], swing: swing };
    }

    var holding = opts.holding;
    var rightSwing = pose.armR;
    if (holding) rightSwing = -1.32 + (opts.pitch || 0) * 0.55;
    var leftSwing = pose.armL;
    if (holding && holding.twoHanded !== false) leftSwing = -1.15 + (opts.pitch || 0) * 0.4;
    var rightHand = arm(-1, rightSwing, holding ? 0 : pose.armRZ);
    arm(1, leftSwing, holding ? 0 : pose.armLZ);

    // ---------------------------------------------------------------- legs
    var legLen = body.leg.size[1];
    function leg(side, swing) {
      // the stride narrows the stance rather than widening the hips, so the
      // feet track under the body instead of out beside it
      var root = body.leg.x * side * (1 - legPinch);
      var roll = -side * legRoll;
      // the pelvis carries the whole leg: across, around and up or down
      var pivotY = body.leg.pivotY + root * hipRoll;
      function at(down, forward, lateral) {
        var o = limbPoint(down, forward || 0, swing, roll, lateral || 0);
        var xz = rotateY(root + hipShift + o[0], o[2], hipTwist);
        return [xz[0], pivotY + o[1], xz[1]];
      }
      var skin = colourOf(descriptor, side < 0 ? 'right_leg' : 'left_leg', '#a4bd47');
      var trouser = pantsData.legs;
      var length = pantsData.length === undefined ? 1.0 : pantsData.length;
      var extra = { t: 'rlimb', rx: swing, ry: hipTwist, rz: roll, k: 'leg' };
      var shoeColour = skin;
      var bareColour = pantsData.skin || skin;
      if (trouser && length >= 0.99) {
        place(at(legLen / 2), body.leg.size.slice(), trouser, extra);
        shoeColour = pantsData.cuff || trouser;
      } else if (trouser && length > 0.01) {
        var upperLen = legLen * length;
        place(at(upperLen / 2),
              [body.leg.size[0] * 1.02, upperLen, body.leg.size[2] * 1.02],
              trouser, extra);
        var lowerLen = legLen - upperLen;
        place(at(upperLen + lowerLen / 2),
              [body.leg.size[0], lowerLen, body.leg.size[2]], bareColour, extra);
      } else {
        place(at(legLen / 2), body.leg.size.slice(), skin, extra);
      }
      /* A fuller block over the top of the leg.  The leg proper is the calf,
         so one extra part per leg is the whole difference between a post and
         a shape -- and because it is coloured by whatever covers the leg at
         that height, trousers and bare skin both come out right. */
      if (body.thigh) {
        var thighMid = body.thigh.drop + body.thigh.size[1] / 2;
        var covered = trouser && length * legLen >= thighMid;
        place(at(thighMid), body.thigh.size.slice(),
              covered ? trouser : (trouser ? bareColour : skin), extra);
      }
      if (pantsData.cuff) {
        place(at(legLen - 0.2), [body.leg.size[0] + 0.05, 0.3,
                                 body.leg.size[2] + 0.05],
              pantsData.cuff, { rx: swing, ry: hipTwist, rz: roll, k: 'leg' });
      }
      if (pantsData.stripe) {
        place(at(legLen / 2, 0, side * (body.leg.size[0] / 2 + 0.01)),
              [0.07, legLen * 0.92, body.leg.size[2] * 0.5],
              pantsData.stripe,
              { t: 'rlimb', rx: swing, ry: hipTwist, rz: roll,
                m: pantsData.glow ? 'neon' : '', k: 'leg' });
      }
      // a shallow foot block: cheap, and it stops the legs reading as bare posts
      if (body.foot) {
        place(at(legLen - body.foot.size[1] / 2, body.foot.z),
              body.foot.size.slice(), shoeColour,
              { rx: swing, ry: hipTwist, rz: roll, k: 'foot' });
      }
    }
    leg(-1, pose.legR);
    leg(1, pose.legL);

    // ------------------------------------------------------- accessories
    function attach(itemParts, origin, extraYaw) {
      (itemParts || []).forEach(function (piece) {
        var local = [origin[0] + piece.p[0], origin[1] + piece.p[1],
                     origin[2] + piece.p[2]];
        var spin = piece.spin ? (opts.time || 0) * piece.spin : 0;
        var xz = rotateY(local[0], local[2], yaw);
        parts.push({
          t: piece.t || 'box',
          p: [pos[0] + xz[0], pos[1] + local[1] + bob, pos[2] + xz[1]],
          s: piece.s.slice(),
          c: piece.c,
          r: [(piece.r ? piece.r[0] : 0), yaw + (piece.r ? piece.r[1] : 0) + spin +
              (extraYaw || 0), (piece.r ? piece.r[2] : 0)],
          m: piece.m,
          a: piece.a,
          decSlot: piece.decal ? Textures.decal(piece.decal) : null
        });
      });
    }

    if (hat && hat.data && hat.data.parts) {
      attach(hat.data.parts, [0, RIG.headTop, 0]);
    }
    if (back && back.data && back.data.parts) {
      // a back item rides the shoulders, so it turns with them
      var anchor = rotateY(body.backAnchor[0] + torsoShift, body.backAnchor[2],
                           torsoTwist);
      attach(back.data.parts, [anchor[0], body.backAnchor[1], anchor[1]],
             torsoTwist);
    }

    // ---------------------------------------------------------- held item
    if (holding && holding.data && holding.data.parts) {
      var gripSwing = rightSwing;
      (holding.data.parts).forEach(function (piece) {
        var ly = rotateX(piece.p[1] - 0.0, piece.p[2] + 0.0, gripSwing + Math.PI / 2);
        var grip = rotateY(piece.p[0], ly[1], torsoTwist);
        var local = [rightHand.x + grip[0], rightHand.y + ly[0],
                     rightHand.z + grip[1]];
        var xz = rotateY(local[0], local[2], yaw);
        parts.push({
          t: piece.t || 'box',
          p: [pos[0] + xz[0], pos[1] + local[1] + bob, pos[2] + xz[1]],
          s: piece.s.slice(),
          c: piece.c,
          r: [(piece.r ? piece.r[0] : 0) + gripSwing + Math.PI / 2,
              yaw + torsoTwist + (piece.r ? piece.r[1] : 0),
              (piece.r ? piece.r[2] : 0)],
          m: piece.m
        });
      });
    }
    return parts;
  };
  /* World position of the hat emitter (for Unusual particle effects). */
  Avatar.hatAnchor = function (position, yaw, hat) {
    var y = RIG.headTop + 0.55;
    if (hat && hat.data && hat.data.parts && hat.data.parts.length) {
      var top = 0;
      hat.data.parts.forEach(function (piece) {
        top = Math.max(top, piece.p[1] + piece.s[1] * 0.5);
      });
      y = RIG.headTop + top + 0.18;
    }
    return [position[0], position[1] + y, position[2]];
  };

  /* A compact first-person view model: the right arm plus the held item,
     positioned relative to the camera basis. */
  Avatar.viewModel = function (descriptor, holding, camera, sway, opts) {
    opts = opts || {};
    var parts = [];
    var body = Avatar.body(descriptor);
    var eye = camera.eye;
    var fwd = camera.forward;
    var right = camera.right;
    var up = camera.up;
    var flen = Math.hypot(fwd[0], fwd[1], fwd[2]) || 1;
    var f = [fwd[0] / flen, fwd[1] / flen, fwd[2] / flen];
    var rlen = Math.hypot(right[0], right[1], right[2]) || 1;
    var r = [right[0] / rlen, right[1] / rlen, right[2] / rlen];
    var ulen = Math.hypot(up[0], up[1], up[2]) || 1;
    var u = [up[0] / ulen, up[1] / ulen, up[2] / ulen];
    var yaw = Math.atan2(f[0], f[2]);
    var pitch = Math.asin(M.clamp(f[1], -1, 1));

    function toWorld(local) {
      return [
        eye[0] + r[0] * local[0] + u[0] * local[1] + f[0] * local[2],
        eye[1] + r[1] * local[0] + u[1] * local[1] + f[1] * local[2],
        eye[2] + r[2] * local[0] + u[2] * local[1] + f[2] * local[2]
      ];
    }

    var bobX = (sway && sway.x) || 0;
    var bobY = (sway && sway.y) || 0;
    var recoil = (sway && sway.recoil) || 0;
    var base = [1.05 + bobX, -0.98 + bobY - recoil * 0.30, 2.35 - recoil * 0.55];
    var armColour = (descriptor.items && descriptor.items.shirt &&
                     descriptor.items.shirt.data && descriptor.items.shirt.data.arms) ||
                    colourOf(descriptor, 'right_arm', '#f5cd30');
    // the real arm is rectangular now, so the view model takes the mean of
    // its two cross-section axes rather than the narrow one alone
    var armThickness = (body.arm.size[0] + body.arm.size[2]) * 0.5 * 0.46;

    // forearm
    var armLocal = [base[0] - 0.10, base[1] - 0.34, base[2] - 0.78];
    parts.push({
      // long in Z rather than Y, so the general bake is the right one here
      t: 'rbox',
      p: toWorld(armLocal),
      s: [armThickness, armThickness, 1.5],
      c: armColour,
      r: [pitch + 0.14, yaw, 0]
    });

    if (holding && holding.data && holding.data.parts) {
      holding.data.parts.forEach(function (piece) {
        var local = [base[0] + piece.p[0] * 0.45,
                     base[1] + piece.p[1] * 0.45,
                     base[2] + piece.p[2] * 0.45];
        parts.push({
          t: piece.t || 'box',
          p: toWorld(local),
          s: [piece.s[0] * 0.45, piece.s[1] * 0.45, piece.s[2] * 0.45],
          c: piece.c,
          r: [pitch + (piece.r ? piece.r[0] : 0),
              yaw + (piece.r ? piece.r[1] : 0),
              (piece.r ? piece.r[2] : 0)],
          m: piece.m
        });
      });
    }
    if (opts.muzzle) {
      var mz = [base[0], base[1] + 0.08, base[2] + 1.1];
      parts.push({
        t: 'sph', p: toWorld(mz), s: [0.5, 0.5, 0.5], c: '#ffd95e',
        r: [0, 0, 0], m: 'neon'
      });
    }
    return parts;
  };

  global.Avatar = Avatar;
})(window);
