/* BLOCKHAVEN engine -- the avatar base system.
   One rig, driven entirely by a descriptor from the server, used by the
   profile preview, the avatar editor, item thumbnails and the game itself.

   The rig is built from rounded boxes rather than hard cubes, with a neck, a
   tapered torso and softened limbs, so a bare default character already has a
   silhouette instead of reading as a stack of blocks.

   Two builds ship: "male", the broader one, and "female", the slighter one.
   Both are the same construction with different measurements -- including
   the head, where the female one is narrower, a little taller than it is
   wide, and pinched through the jaw.  Both keep RIG.headTop, the eye height
   and the hitbox exactly where they are, and both keep the same flat face
   plate, which is what guarantees every hat, face and outfit fits either
   with no per-type variant.  Cosmetics that colour the body (shirts,
   trousers) are driven from the same metrics, so they follow whichever
   silhouette is in use.

   What separates them past the silhouette is the walk: the female build
   carries its own gait, in which the pelvis is an animated part rather than
   being welded to the spine -- it slides, drops and turns through the stride
   while the shoulders answer it.  It is a quiet version of that, not a
   catwalk: every offset is small enough to read as weight shifting rather
   than as a sway. */
(function (global) {
  'use strict';

  var M = GLX.mat;

  var HEIGHT = 5.4;          // feet to the top of the head, all body types
  var HEAD_TOP = 5.4;

  /* How far anything lying ON the body stands off it: a hem, a chest band, a
     cuff, a trouser stripe.  A band that merely touches the surface it is
     printed on shares a depth value with it across its whole face, and the
     two flicker against each other as the camera moves.  The bands used to
     clear the trunk by 0.015, which is inside the depth buffer's resolution
     at the distance a character is drawn at, so a striped shirt crawled.
     0.05 holds its own depth at any range the game or a thumbnail uses, and
     still reads as cloth rather than as a shelf.

     It works because both pieces are baked from the same rounded box: the
     bevel is the same FRACTION of each one's size, so growing a band by a
     constant leaves it parallel to the body all the way round, corners
     included, rather than diving back into it at the edges. */
  var LIES_ON = 0.05;

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

  /* The female head.  The same head, in the same language -- one rounded box
     with the same bevel in world units, the same flat face plate, the same
     top ring at HEAD_TOP -- drawn to its own proportions:

       narrower      1.34 across rather than 1.46, and no wider than it is
                     deep, so it reads as a head rather than as a wide one
       less wide     than it is tall: 1.06:1 where the male head is 1.14:1,
                     which is most of what takes the blockiness out of it
       a jaw         the bake pinches to 85% of its width below 55% of its
                     height, so the face narrows to a small round chin
                     instead of ending in the same square it started as

     The jaw is part of the head rather than a piece under it: pinching the
     bake keeps one surface, one colour and one decal, so there is no seam to
     show across the chin and nothing that can come unstuck.  The pinch is
     confined to the lower half, which is what keeps the crown -- the part a
     hat actually sits on -- at full width.  Nothing in the catalogue is
     tighter than 1.50 across, so every hat still clears this head and sits
     on it the way it sits on the male one.

     The bevel radii are the head's size divided into a 0.275 world bevel, so
     the corners are as soft as the male head's rather than sharper on the
     smaller box.  They also leave the flat face plate spanning the middle
     59% of the front, which comfortably contains every face in the
     catalogue (the widest eyes reach 55%), so a face decal lands on flat,
     front-facing surface exactly as it does on the male head. */
  var FEMALE_HEAD = {
    size: [1.34, 1.27, 1.34],
    centre: [0, 4.765, 0],         // 4.765 + 1.27/2 = HEAD_TOP
    mesh: 'fhead',
    neck: { size: [0.60, 0.32, 0.58], y: 4.02 }
  };

  Geometry.register('fhead', Geometry.roundedBox([0.205, 0.2165, 0.205], 3,
                                                 { bottom: 0.85, from: 0.55 }));

  /* The builds differ by silhouette, not by parts: the same segments, the
     same anchors, different measurements.

     "male" reads as a near-uniform block (the waist is only a hair narrower
     than the chest).  "female" is the same construction drawn slighter --
     narrow shoulders, a real waist, hips back out to shoulder width and
     slimmer, slightly longer limbs.  That build shipped as "Male Thin"
     before the lofted female rig was retired; it is the female figure now,
     and it walks with the female gait below.

     Consecutive torso segments overlap by more than their two bevels put
     together, because rounded boxes that merely touch leave a groove between
     them and the torso reads as a stack of trays rather than one body. */
  var BODIES = {
    male: {
      id: 'male',
      label: 'Male',
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
      pelvisY: 2.06,
      // where a waistband sits: the top of the hips, inside the overlap with
      // the trunk above, so a belt reads as being worn rather than balanced
      beltLine: 2.17,
      // narrow across, deeper front to back: a rectangle in section, not a
      // post.  x moves in with the half-width so the inner face still
      // meets the torso at the same place and the shoulder joint is sound.
      arm: { size: [0.82, 2.02, 0.96], x: 1.36, pivotY: 3.98 },
      leg: { size: [1.00, 2.00, 1.02], x: 0.52, pivotY: 2.00 },
      foot: { size: [1.06, 0.28, 1.24], z: 0.10 },
      backAnchor: [0, 3.02, -0.54]
    },
    female: {
      id: 'female',
      label: 'Female',
      gait: 'fem',
      head: FEMALE_HEAD,
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
      pelvisY: 2.12,
      beltLine: 2.28,
      arm: { size: [0.64, 2.12, 0.78], x: 1.07, pivotY: 3.99 },
      leg: { size: [0.76, 2.12, 0.86], x: 0.40, pivotY: 2.12 },
      foot: { size: [0.82, 0.24, 1.04], z: 0.10 },
      backAnchor: [0, 3.06, -0.46]
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

  /* Builds that no longer ship, and what a descriptor naming one is drawn
     as.  The server rewrites stored rows on boot, so this only has to cover
     a descriptor cached by a page (or held by a game host) from before the
     change -- and it matches what the server does, so both ends agree. */
  var LEGACY_BODIES = { male_thin: 'male', female_thin: 'female' };

  var Avatar = {
    RIG: RIG,
    BODY_TYPES: ['male', 'female'],
    // short enough for a chip
    BODY_LABELS: { male: 'Male', female: 'Female' },
    // The first person camera sits a touch above the middle of the head so the
    // view reads as "behind the eyes" rather than "inside the chin".
    EYE_HEIGHT: 5.05,
    // Third person orbits the old, lower pivot so that camera is unchanged.
    CHASE_PIVOT: 4.85
  };

  /* The build named by a descriptor, a body-type string, or neither. */
  Avatar.body = function (descriptor) {
    var key = descriptor && (descriptor.body_type || descriptor.body);
    if (typeof descriptor === 'string') key = descriptor;
    return BODIES[key] || BODIES[LEGACY_BODIES[key]] || BODIES.male;
  };

  /* ...and its id, for anything that stores or labels one. */
  Avatar.bodyType = function (descriptor) {
    return Avatar.body(descriptor).id;
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
      // rig: it slides across, drops on one side and turns with the stride
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
     turn against it.  The feet track a little closer to the centre line than
     the hips are wide (``legPinch``) and roll very slightly inwards, which is
     most of the difference between a walk and a march.  The arms swing less,
     hang a touch further from the body, and the whole thing carries a smaller
     vertical bounce, because a long stride with a quiet head is what reads as
     poise.

     Every number here is deliberately small.  The first cut of this gait was
     authored for a figure with a much wider hip than the build now uses, and
     on this one the same swing read as a catwalk: the pelvis swung out past
     the waist, the shoulders wound up against it, and the walk drew attention
     to itself.  Halving the pelvis channels (and pulling the stance-narrowing
     right back, because these legs already stand close together) leaves the
     same motion reading as weight shifting from one foot to the other, which
     is what it was always meant to be.

     Every field is an offset applied in ``Avatar.build``; nothing about the
     geometry, the anchors or the hitbox changes, so the same animation runs
     safely on a character wearing anything in the catalogue. */
  function femPose(pose, state, time) {
    var phase, swing;
    if (state === 'walk' || state === 'run') {
      var running = state === 'run';
      var rate = running ? 9.0 : 6.6;
      var amp = running ? 0.80 : 0.56;
      phase = time * rate;
      swing = Math.sin(phase);
      pose.legL = swing * amp;
      pose.legR = -swing * amp;
      pose.armL = -swing * amp * 0.62;
      pose.armR = swing * amp * 0.62;
      pose.armLZ = running ? 0.07 : 0.075;
      pose.armRZ = -pose.armLZ;
      pose.bob = Math.abs(swing) * (running ? 0.09 : 0.055);
      pose.lean = running ? 0.09 : 0.045;
      // the pelvis: across to the standing leg, up on the swinging side
      pose.hipShift = -swing * (running ? 0.045 : 0.055);
      pose.hipRoll = swing * (running ? 0.04 : 0.05);
      pose.hipTwist = swing * (running ? 0.11 : 0.085);
      // these legs nearly touch as they stand, so the stance only closes by
      // a hair -- any more and the thighs cross through each other
      pose.legPinch = running ? 0.09 : 0.06;
      pose.legRoll = running ? 0.035 : 0.03;
      // the shoulders turn against the hips and stay over the centre line
      pose.torsoTwist = -pose.hipTwist * 0.50;
      pose.torsoShift = -pose.hipShift * 0.30;
      pose.chestRoll = -pose.hipRoll * 0.35;
    } else if (state === 'jump') {
      pose.armL = -2.15; pose.armR = -2.15;
      pose.armLZ = 0.11; pose.armRZ = -0.11;
      pose.legL = -0.30; pose.legR = 0.36;
      pose.legPinch = 0.10; pose.legRoll = 0.06;
      pose.hipRoll = 0.025; pose.lean = 0.055;
    } else if (state === 'fall') {
      pose.armL = -1.55; pose.armR = -1.55;
      pose.armLZ = 0.13; pose.armRZ = -0.13;
      pose.legL = 0.30; pose.legR = -0.18;
      pose.legPinch = 0.08; pose.legRoll = 0.05;
    } else if (state === 'sit') {
      pose.legL = -1.5; pose.legR = -1.5;
      pose.armL = -0.35; pose.armR = -0.35;
      pose.armLZ = 0.085; pose.armRZ = -0.085;
      pose.legPinch = 0.18; pose.legRoll = 0.05;
      pose.hipTwist = 0.05; pose.torsoTwist = -0.04;
    } else {
      /* Contrapposto: the weight is on one leg and stays there, so the idle
         is a held pose that breathes rather than a body swaying between two
         feet.  The slow sine is the breath; the constants are the stance,
         and they are small enough that starting to walk is a change of
         motion rather than a change of posture. */
      var breath = Math.sin(time * 1.25);
      pose.armL = breath * 0.03;
      pose.armR = -breath * 0.03;
      pose.armLZ = 0.07;
      pose.armRZ = -0.076;
      pose.bob = breath * 0.016;
      pose.hipShift = -0.035 + breath * 0.008;
      pose.hipRoll = 0.032 + breath * 0.008;
      pose.hipTwist = -0.022;
      pose.legPinch = 0.03;
      pose.legRoll = 0.02;
      pose.torsoShift = 0.014;
      pose.torsoTwist = 0.022;
      pose.chestRoll = -0.016;
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

  /* Cross from one animation state into the next instead of cutting to it.

     ``Avatar.pose`` is a pure function of the animation state, so a character
     going from idle to walk, or from walk to jump, changes pose on a single
     frame and the limbs visibly jump -- most of all on the female gait, where
     the pelvis and the shoulders move too.  Any caller that can keep one
     object per character (a player record, a preview) can run the pose
     through here instead and get the change arriving over about a sixth of a
     second.

     It is a cross-fade rather than a filter on the output: while the change
     is in flight BOTH states are evaluated at the live clock and mixed, so a
     steady walk or run comes through exactly as it was authored -- no lag,
     no damping, nothing to re-tune -- and only the crossing is smoothed.  A
     second change arriving mid-cross has nothing sound to run as its source,
     so what is on screen is frozen and crossed out of instead.

     ``memory`` is the caller's own object, handed back every frame; anything
     falsy means "no memory", and the pose comes back as ``Avatar.pose`` would
     give it.  A caller with no clock (``dt`` of 0) gets the same.  Everything
     this needs to remember lives in one field of its own on that object, so
     it cannot collide with whatever the caller keeps there -- a look, for
     one, already carries a ``pose`` of its own meaning something else. */
  var POSE_KEYS = Object.keys(blankPose());
  var BLEND_SECONDS = 0.16;
  var MEMORY = '_avatarPose';

  function copyPose(into, from) {
    into = into || blankPose();
    for (var i = 0; i < POSE_KEYS.length; i++) into[POSE_KEYS[i]] = from[POSE_KEYS[i]];
    return into;
  }

  /* Forget what a character was doing: the next pose is taken up directly.
     Used when the thing being animated is no longer the same character --
     a preview rolling a new look on the other build, say -- because crossing
     between two gaits on two bodies is not a transition, it is a cut. */
  Avatar.resetPose = function (memory) {
    if (memory) memory[MEMORY] = null;
  };

  Avatar.smoothPose = function (memory, state, time, speed, who, dt) {
    state = state || 'idle';
    var target = Avatar.pose(state, time, speed, who);
    if (!memory) return target;
    var held = memory[MEMORY];
    if (!held) {
      // first frame for this character: take up the pose asked for
      held = memory[MEMORY] = { state: state, blend: 1, pose: copyPose(null, target),
                                from: '', frozen: null };
      return held.pose;
    }
    if (held.state !== state) {
      if (held.blend < 1) {
        // a second change inside a cross: there is no single state running to
        // cross out of, so freeze what is on screen and cross out of that
        held.frozen = copyPose(held.frozen, held.pose);
        held.from = '';
      } else {
        held.from = held.state;          // the old state carries on running
      }
      held.blend = 0;
      held.state = state;
    }
    if (held.blend < 1) {
      held.blend = Math.min(1, held.blend + (dt > 0 ? dt : BLEND_SECONDS) / BLEND_SECONDS);
    }
    if (!(held.blend < 1)) {
      held.pose = copyPose(held.pose, target);
      return held.pose;
    }
    var from = held.from ? Avatar.pose(held.from, time, speed, who) : held.frozen;
    // smoothstep, so the cross leaves one state and arrives in the other
    // without a corner at either end
    var b = held.blend;
    var t = b * b * (3 - 2 * b);
    held.pose = held.pose || blankPose();
    for (var i = 0; i < POSE_KEYS.length; i++) {
      var key = POSE_KEYS[i];
      held.pose[key] = from[key] + (target[key] - from[key]) * t;
    }
    return held.pose;
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
    var belt = itemData(descriptor, 'belt');
    var hair = itemData(descriptor, 'hair');
    var hat = itemData(descriptor, 'hat');
    var face = itemData(descriptor, 'face');
    var back = itemData(descriptor, 'back');
    var shirtData = (shirt && shirt.data) || {};
    var pantsData = (pants && pants.data) || {};
    var beltData = (belt && belt.data) || {};
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
        if (extra.dw) part.dw = extra.dw;
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

    // ----------------------------------------------------------- colouring
    var torsoColour = shirtData.torso || colourOf(descriptor, 'torso', '#0d69ac');
    var torsoDecal = shirtData.decal ? Textures.decal(shirtData.decal) : null;
    /* A weave is the cloth itself -- denim, camo, knit -- printed over the
       whole garment rather than stuck on the front of it, so it goes round
       the arms and the legs too.  A part carries one decal, so the segment a
       graphic is printed on keeps the graphic and the rest of the garment
       carries the weave. */
    var shirtWeave = shirtData.weave ? Textures.decal(shirtData.weave) : null;
    var pantsWeave = pantsData.weave ? Textures.decal(pantsData.weave) : null;
    var beltWeave = beltData.weave ? Textures.decal(beltData.weave) : null;
    /* The hips are trousered when trousers are on, and their own colour when
       they are not.  Before the hips were colourable they borrowed the left
       leg's, so that is what a descriptor without one still gets -- which
       covers anything cached, rolled or built by hand rather than loaded from
       an account. */
    var hipColour = pantsData.legs ||
      colourOf(descriptor, 'hips', colourOf(descriptor, 'left_leg', '#a4bd47'));
    var headColour = colourOf(descriptor, 'head', '#f5cd30');
    var faceSlot = (face && face.data)
      ? Textures.faceSlot(face.item_id, face.data) : null;

    /* Carrying something raises the arms towards the camera.  Zero hangs
       straight down and -PI/2 is straight out in front, so these are how far
       up the arms come to present whatever is in the hands.

       They were -1.32 and -1.15 -- within 15 degrees of horizontal -- which
       held a weapon up at shoulder height across the chest, hiding the torso
       and reading as sighting down the barrel rather than carrying a tool.
       Dropped by about 20 degrees the hand sits below the shoulder, the item
       clears the legs, and the character reads as holding something.  The
       held item hangs off this same angle (see "held item" below), so it
       follows the hand without a second number to keep in step. */
    var HOLD_ARM_RIGHT = -0.95;
    var HOLD_ARM_LEFT = -0.82;
    // how much of the look-pitch the arms carry, so aiming up or down still
    // swings them rather than leaving the item pointing at the horizon
    var HOLD_PITCH_RIGHT = 0.55;
    var HOLD_PITCH_LEFT = 0.40;

    var holding = opts.holding;
    var rightSwing = pose.armR;
    if (holding) {
      rightSwing = HOLD_ARM_RIGHT + (opts.pitch || 0) * HOLD_PITCH_RIGHT;
    }
    var leftSwing = pose.armL;
    if (holding && holding.twoHanded !== false) {
      leftSwing = HOLD_ARM_LEFT + (opts.pitch || 0) * HOLD_PITCH_LEFT;
    }
    var rightHand = null;

    /* ------------------------------------------------------------ the body
       Both builds are the same construction -- a stack of rounded boxes with
       the limbs hung off it -- so there is one body routine, driven by
       whichever set of measurements the descriptor asked for. */
    buildBlocks();

    /* The trunk's width and depth at a given height.

       A band round the body has to be measured against the piece it actually
       lies on.  The male trunk is two segments of different sizes and the
       female one is three, so a band sized from a single "chest" number
       stands proud of one segment and sinks inside another -- on the female
       build the chest metric is shallower than the segment above it, so the
       upper stripes disappeared into the body altogether. */
    function trunkAt(y) {
      var w = 0, d = 0;
      body.torso.forEach(function (seg) {
        if (y < seg.y - seg.size[1] / 2 || y > seg.y + seg.size[1] / 2) return;
        if (seg.size[0] > w) w = seg.size[0];
        if (seg.size[2] > d) d = seg.size[2];
      });
      return w ? [w, d] : [body.chest.size[0], body.chest.size[2]];
    }

    /* The belt: a band round the waist and, if it has one, a buckle at the
       front.  It is sized from the build's own hips rather than from numbers
       of its own, so one belt fits both builds, and it stands proud of them,
       so it is worn OVER whatever the trousers are doing rather than being
       painted into them.  It rides the pelvis, so it turns and drops with the
       hips through the stride instead of hanging in the air where they were. */
    function belted() {
      if (!beltData.band) return;
      var hips = body.hips.size;
      var band = beltData.width === undefined ? 0.20 : beltData.width;
      var y = body.beltLine === undefined ? body.hips.y : body.beltLine;
      placePelvis(0, y, 0, [hips[0] * 1.045, band, hips[2] * 1.05],
                  beltData.band,
                  { k: 'hips', decSlot: beltWeave, dw: beltWeave ? 1 : 0 });
      if (beltData.buckle) {
        placePelvis(0, y, hips[2] * 0.53,
                    [band * 1.7, band * 1.25, hips[2] * 0.14], beltData.buckle,
                    { k: 'hips',
                      m: beltData.glow ? 'neon' : (beltData.metal ? 'metal' : '') });
      }
      if (beltData.pouch) {
        /* Two pouches on the front of the band, flanking the buckle.  They
           have to stand off the front face rather than sit beside the hips:
           a pouch at the side is inside the hip block on one build and
           through the arm on the other. */
        for (var side = -1; side <= 1; side += 2) {
          placePelvis(side * hips[0] * 0.26, y - band * 0.85, hips[2] * 0.50,
                      [band * 1.6, band * 1.9, hips[2] * 0.20],
                      beltData.band, { k: 'hips' });
        }
      }
    }

    /* Where a leg hangs from once the pelvis has moved.

       The pelvis is drawn as a part with its own roll, so it turns about its
       own centre.  A leg that is merely shifted up and down by that roll is
       not on the same pelvis any more, and at the top of the stride the hip
       slides off the outside of it -- a sliver of bare leg above the
       waistband.  Turning the leg's root about the same point the pelvis
       turns about keeps them one body. */
    function hipRoot(root) {
      var pivot = body.pelvisY;
      var dy = body.leg.pivotY - pivot;
      var c = Math.cos(hipRoll), sn = Math.sin(hipRoll);
      return { x: root * c - dy * sn, y: pivot + root * sn + dy * c };
    }

    function buildBlocks() {
      // --------------------------------------------------------------- torso
      body.torso.forEach(function (segment) {
        var print = segment.decal ? torsoDecal : null;
        placeTrunk(0, segment.y, 0, segment.size.slice(), torsoColour, {
          decSlot: print || shirtWeave, dw: print ? 0 : (shirtWeave ? 1 : 0),
          k: 'torso'
        });
      });
      // the hips read as part of the lower body, so they take the trousers
      placePelvis(0, body.hips.y, 0, body.hips.size.slice(), hipColour,
                  { k: 'hips',
                    decSlot: pantsData.legs ? pantsWeave : null,
                    dw: pantsData.legs && pantsWeave ? 1 : 0 });
      belted();

      var lowest = body.torso[body.torso.length - 1];
      if (shirtData.stripe) {
        var hemY = lowest.y - lowest.size[1] / 2 + 0.18;
        var hem = trunkAt(hemY);
        placeTrunk(0, hemY, 0,
                   [hem[0] + LIES_ON * 2, 0.34, hem[1] + LIES_ON * 2],
                   shirtData.stripe, { k: 'torso' });
      }
      if (shirtData.stripes) {
        var span = body.chest.size[1] - 0.3;
        for (var si = 0; si < shirtData.stripes; si++) {
          var t = shirtData.stripes > 1 ? si / (shirtData.stripes - 1) : 0.5;
          var bandY = body.chest.y - span / 2 + span * t;
          var band = trunkAt(bandY);
          placeTrunk(0, bandY, 0,
                     [band[0] + LIES_ON * 2, 0.15, band[1] + LIES_ON * 2],
                     shirtData.stripe || '#1b2a35', { k: 'torso' });
        }
      }
      if (shirtData.hood) {
        placeTrunk(0, body.chest.y + body.chest.size[1] / 2 - 0.06, -0.34,
                   [body.chest.size[0] * 0.86, 0.62, 0.72],
                   shirtData.torso || torsoColour, { rx: 0, rz: chestRoll, k: 'torso' });
      }

      // ---------------------------------------------------------------- neck
      place([0, head.neck.y, 0], head.neck.size.slice(), headColour,
            { t: 'cyl', k: 'neck' });

      // ---------------------------------------------------------------- head
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
        var clad = { t: 'rlimb', rx: swing, ry: torsoTwist, rz: roll, k: 'arm',
                     decSlot: shirtWeave, dw: shirtWeave ? 1 : 0 };
        if (sleeve && coverage >= 0.99) {
          place(centre, body.arm.size.slice(), sleeve, clad);
        } else if (sleeve && coverage > 0.01) {
          var upperLen = armLen * coverage;
          place(at(upperLen / 2),
                [body.arm.size[0] * 1.02, upperLen, body.arm.size[2] * 1.02],
                sleeve, clad);
          var lowerLen = armLen - upperLen;
          place(at(upperLen + lowerLen / 2),
                [body.arm.size[0], lowerLen, body.arm.size[2]], skin, extra);
        } else {
          place(centre, body.arm.size.slice(), skin, extra);
        }
        var hand = at(armLen);
        return { x: hand[0], y: hand[1], z: hand[2], swing: swing };
      }

      rightHand = arm(-1, rightSwing, holding ? 0 : pose.armRZ);
      arm(1, leftSwing, holding ? 0 : pose.armLZ);

      // ---------------------------------------------------------------- legs
      var legLen = body.leg.size[1];
      function leg(side, swing) {
        // the stride narrows the stance rather than widening the hips, so the
        // feet track under the body instead of out beside it
        var root = body.leg.x * side * (1 - legPinch);
        var roll = -side * legRoll;
        // the pelvis carries the whole leg: across, around and up or down
        var seat = hipRoot(root);
        var pivotY = seat.y;
        root = seat.x;
        function at(down, forward, lateral) {
          var o = limbPoint(down, forward || 0, swing, roll, lateral || 0);
          var xz = rotateY(root + hipShift + o[0], o[2], hipTwist);
          return [xz[0], pivotY + o[1], xz[1]];
        }
        var skin = colourOf(descriptor, side < 0 ? 'right_leg' : 'left_leg', '#a4bd47');
        var trouser = pantsData.legs;
        var length = pantsData.length === undefined ? 1.0 : pantsData.length;
        var extra = { t: 'rlimb', rx: swing, ry: hipTwist, rz: roll, k: 'leg' };
        var clad = { t: 'rlimb', rx: swing, ry: hipTwist, rz: roll, k: 'leg',
                     decSlot: pantsWeave, dw: pantsWeave ? 1 : 0 };
        var shoeColour = skin;
        var bareColour = pantsData.skin || skin;
        if (trouser && length >= 0.99) {
          place(at(legLen / 2), body.leg.size.slice(), trouser, clad);
          shoeColour = pantsData.cuff || trouser;
        } else if (trouser && length > 0.01) {
          var upperLen = legLen * length;
          place(at(upperLen / 2),
                [body.leg.size[0] * 1.02, upperLen, body.leg.size[2] * 1.02],
                trouser, clad);
          var lowerLen = legLen - upperLen;
          place(at(upperLen + lowerLen / 2),
                [body.leg.size[0], lowerLen, body.leg.size[2]], bareColour, extra);
        } else {
          place(at(legLen / 2), body.leg.size.slice(), skin, extra);
        }
        if (pantsData.cuff) {
          place(at(legLen - 0.2), [body.leg.size[0] + LIES_ON * 2, 0.3,
                                   body.leg.size[2] + LIES_ON * 2],
                pantsData.cuff, { rx: swing, ry: hipTwist, rz: roll, k: 'leg' });
        }
        if (pantsData.stripe) {
          /* A flat plate rather than a rounded one.  The leg's bevel is a
             fraction of ITS size and the stripe's of its own, and a stripe
             0.07 across has almost none -- so a rounded stripe curves back
             into the leg along both its edges and the two surfaces meet
             there.  A plain box has no curvature to dive back in with, and
             its whole face holds the standoff.  It is narrow enough to sit
             inside the flat part of the leg's side either way. */
          place(at(legLen / 2, 0,
                   side * (body.leg.size[0] / 2 + LIES_ON - 0.035)),
                [0.07, legLen * 0.92, body.leg.size[2] * 0.5],
                pantsData.stripe,
                { t: 'box', rx: swing, ry: hipTwist, rz: roll,
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
    }


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
          decSlot: piece.decal ? Textures.decal(piece.decal) : null,
          dw: piece.dw
        });
      });
    }

    /* Hair is the one cosmetic that has to fit the skull rather than sit on
       top of it, and the two builds have different heads.  So it is authored
       in head units -- 1.0 is the head's own width, height and depth, and the
       origin is the middle of the head -- and scaled to whichever head is
       wearing it.  One style, both builds, no gap and no clipping, and a
       style added later needs no per-build variant. */
    if (hair && hair.data && hair.data.parts) {
      var hs = head.size, hc = head.centre;
      hair.data.parts.forEach(function (piece) {
        var spin = piece.spin ? (opts.time || 0) * piece.spin : 0;
        place([hc[0] + piece.p[0] * hs[0],
               hc[1] + piece.p[1] * hs[1],
               hc[2] + piece.p[2] * hs[2]],
              [piece.s[0] * hs[0], piece.s[1] * hs[1], piece.s[2] * hs[2]],
              piece.c,
              { t: piece.t || 'rbox', k: 'hair', m: piece.m, a: piece.a,
                dw: piece.dw,
                decSlot: piece.decal ? Textures.decal(piece.decal) : null,
                rx: piece.r ? piece.r[0] : 0,
                ry: (piece.r ? piece.r[1] : 0) + spin,
                rz: piece.r ? piece.r[2] : 0 });
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
    // A held item is authored at world scale, on a character six studs tall;
    // in the hand a foot from the eye it wants to be a good deal smaller.
    var VIEW_MODEL_SCALE = 0.45;
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

    /* Placing a part takes two things that have to agree: where its centre
       goes, and which way its box is turned.  The centre is laid out along
       the camera basis below (toWorld); the turn is an euler triple the
       renderer composes as Ry * Rx * Rz.  Those two are NOT the same frame,
       and the difference is what used to tear the weapon apart:

         * The renderer's pitch runs the other way.  Its Z column carries
           -sin(rx) where the camera's forward carries +sin(pitch), so at
           pitch 0 they agree -- which is why this looked fine while you
           were level -- and at any other angle the boxes pitched against
           their own offsets and each piece appeared to spin where it was.

         * ``right`` is [-cos(yaw), 0, sin(yaw)], so (right, up, forward) is
           left-handed: right x up = -forward.  No rotation matrix can equal
           a reflection, so the mesh's X axis is always the camera's LEFT and
           the flip has to be taken out of the offsets instead.

       Hence PITCH_SIGN on the euler and MESH_X on every offset that belongs
       to the model rather than to where the model is held. */
    var PITCH_SIGN = -1;
    var MESH_X = -1;

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
      // 0.14 holds the forearm just below the line of sight; the sign in
      // front of pitch is what makes it follow the look rather than fight it
      r: [PITCH_SIGN * pitch + 0.14, yaw, 0]
    });

    if (holding && holding.data && holding.data.parts) {
      // ``base`` is where the hand is held in view, so it stays in the
      // camera's own frame.  Each piece's offset is part of the model, so it
      // is laid out in the frame the model's boxes are actually turned into
      // -- which is the same one but mirrored in X.
      holding.data.parts.forEach(function (piece) {
        var local = [base[0] + MESH_X * piece.p[0] * VIEW_MODEL_SCALE,
                     base[1] + piece.p[1] * VIEW_MODEL_SCALE,
                     base[2] + piece.p[2] * VIEW_MODEL_SCALE];
        parts.push({
          t: piece.t || 'box',
          p: toWorld(local),
          s: [piece.s[0] * VIEW_MODEL_SCALE, piece.s[1] * VIEW_MODEL_SCALE,
              piece.s[2] * VIEW_MODEL_SCALE],
          c: piece.c,
          r: [PITCH_SIGN * pitch + (piece.r ? piece.r[0] : 0),
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
