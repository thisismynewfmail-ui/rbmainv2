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
      pelvisY: 2.06,
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
      pelvisY: 2.12,
      arm: { size: [0.64, 2.12, 0.78], x: 1.07, pivotY: 3.99 },
      leg: { size: [0.76, 2.12, 0.86], x: 0.40, pivotY: 2.12 },
      foot: { size: [0.82, 0.24, 1.04], z: 0.10 },
      backAnchor: [0, 3.06, -0.46]
    }
  };


  /* ==========================================================================
     THE FEMALE BUILDS
     These are not the male rig with curves bolted on.  A curve made by
     pushing a sphere into a box is a sphere in a box: the join shows, the
     shading breaks along it, and the piece reads as stuck on -- because it
     is.  So the female builds are made the other way round.  One profile is
     authored down the whole figure -- shoulder, chest, waist, hip, seat --
     and Geometry.loft sweeps a single unbroken skin through it.  The bust is
     the front depth of the surface rising and falling through the chest
     rings, with a gaussian cleft pressed into the centre line; the seat is
     the back depth rising through the hip rings.  There is nothing to come
     unstuck because there is nothing attached.

     The surface is cut in two only where the clothes cut it -- at the hip
     line, so the top and the trousers can be different colours.  Both pieces
     are sliced out of the same curve, which means they share their boundary
     ring exactly and their normals are measured across the join rather than
     at it: the seam is a colour change on one continuous body, not a joint.

     Everything the clothes need follows the same rule.  A printed graphic is
     a patch of the body's own surface lifted 8mm off it, so it curves with
     the chest.  A hem, a cuff and a stripe are bands of the same surface.  A
     short sleeve or a pair of shorts is a garment standing off the limb,
     because that is what a short sleeve is -- not the arm painted a
     different colour half way down. */

  // Where the top stops and the trousers start.  Both pieces are cut from
  // the same spline here, so the cut is invisible.
  var HIP_LINE = 2.57;

  /* The head.  Its own skull, not the male one scaled down: a high rounded
     cranium, temples that come in above the cheekbone, a soft cheek and a
     jaw that tapers to a small round chin.  Feminine comes from the taper
     below the cheekbone -- the male head has none -- and from the crown
     being the widest thing up top rather than the jaw being the widest thing
     down below.

     Two numbers are fixed and cannot move: the top ring is at 5.40, which is
     where every hat in the catalogue anchors, and the face plate between the
     cheekbones is flat enough (n above 3) that its surface normals still
     face front, which is what every face decal needs to land on. */
  var FEMALE_HEAD = [
    { y: 4.34, w: 0.180, df: 0.186, db: 0.180, n: 2.4 },   // into the neck
    { y: 4.41, w: 0.300, df: 0.308, db: 0.290, n: 2.9 },
    { y: 4.49, w: 0.420, df: 0.416, db: 0.392, n: 3.3 },   // chin
    { y: 4.59, w: 0.512, df: 0.478, db: 0.464, n: 3.7 },   // jaw
    { y: 4.70, w: 0.572, df: 0.514, db: 0.516, n: 4.0 },   // cheek
    { y: 4.82, w: 0.604, df: 0.528, db: 0.556, n: 4.2 },   // cheekbone
    { y: 4.94, w: 0.612, df: 0.528, db: 0.584, n: 4.3 },   // temple
    { y: 5.06, w: 0.602, df: 0.518, db: 0.594, n: 4.1 },   // brow
    { y: 5.18, w: 0.570, df: 0.492, db: 0.574, n: 3.7 },
    { y: 5.29, w: 0.512, df: 0.450, db: 0.524, n: 3.3 },   // crown
    { y: 5.365, w: 0.410, df: 0.362, db: 0.428, n: 3.0 },
    { y: 5.40, w: 0.274, df: 0.244, db: 0.288, n: 2.7 }    // the hat anchor
  ];  // A slimmer neck than the male post, flaring where it meets the shoulders
  // and covering the stub the torso closes into.
  var FEMALE_NECK = [
    { y: 3.82, w: 0.305, d: 0.294, n: 2.8 },
    { y: 3.96, w: 0.256, d: 0.246, n: 2.7 },
    { y: 4.16, w: 0.236, d: 0.230, n: 2.6 },
    { y: 4.34, w: 0.242, d: 0.236, n: 2.6 },
    { y: 4.43, w: 0.252, d: 0.246, n: 2.6 }
  ];  /* The figure, shoulder to crotch, in one curve.

     Read the ``w`` column down and you have the silhouette from the front:
     0.635 across the shoulder, in to 0.445 at the waist, out to 0.710 at the
     hip.  Read ``df`` and you have it from the side: the chest comes forward
     through the bust rings and settles back under them.  Read ``db`` and you
     have the seat.  ``cleft`` presses the centre line of the chest in so the
     two sides of it are one moulded front rather than two lumps. */
  var FEMALE_BODY = [
    { y: 1.99, w: 0.560, df: 0.330, db: 0.350, n: 2.8 },   // crotch
    { y: 2.10, w: 0.630, df: 0.355, db: 0.420, n: 2.7 },
    { y: 2.22, w: 0.688, df: 0.380, db: 0.495, n: 2.6 },
    { y: 2.33, w: 0.710, df: 0.392, db: 0.522, n: 2.5 },   // seat
    { y: 2.45, w: 0.706, df: 0.396, db: 0.492, n: 2.6 },
    { y: 2.57, w: 0.648, df: 0.386, db: 0.436, n: 2.7 },   // the hip line
    { y: 2.68, w: 0.566, df: 0.368, db: 0.390, n: 2.8 },
    { y: 2.79, w: 0.489, df: 0.346, db: 0.342, n: 2.9 },
    { y: 2.90, w: 0.449, df: 0.332, db: 0.316, n: 3.0 },   // waist
    { y: 3.01, w: 0.462, df: 0.343, db: 0.316, n: 3.0 },
    { y: 3.12, w: 0.492, df: 0.372, db: 0.324, n: 2.9 },
    { y: 3.23, w: 0.522, df: 0.424, db: 0.334, n: 2.8, cleft: 0.10, cleftW: 0.36 },
    { y: 3.33, w: 0.552, df: 0.532, db: 0.342, n: 2.7, cleft: 0.22, cleftW: 0.34 },
    { y: 3.43, w: 0.574, df: 0.572, db: 0.348, n: 2.6, cleft: 0.24, cleftW: 0.33 },
    { y: 3.53, w: 0.588, df: 0.528, db: 0.352, n: 2.7, cleft: 0.18, cleftW: 0.33 },
    { y: 3.62, w: 0.607, df: 0.438, db: 0.354, n: 2.9, cleft: 0.07, cleftW: 0.34 },
    { y: 3.72, w: 0.632, df: 0.382, db: 0.352, n: 3.0 },   // shoulder
    { y: 3.81, w: 0.588, df: 0.344, db: 0.334, n: 2.9 },
    { y: 3.89, w: 0.452, df: 0.302, db: 0.296, n: 2.8 },
    { y: 3.96, w: 0.302, df: 0.254, db: 0.250, n: 2.6 },
    { y: 4.03, w: 0.186, df: 0.172, db: 0.170, n: 2.4 }    // closes under the neck
  ];

  /* The same figure on a smaller frame.  The shoulders, the ribcage and the
     bust all come in; the hip and the seat barely move.  A narrower frame
     around the same hip is what makes the curve read harder here rather than
     softer, which is the whole point of the slimmer cut. */
  var FEMALE_BODY_THIN = [
    { y: 1.99, w: 0.516, df: 0.312, db: 0.334, n: 2.8 },
    { y: 2.10, w: 0.590, df: 0.334, db: 0.404, n: 2.7 },
    { y: 2.22, w: 0.650, df: 0.356, db: 0.480, n: 2.5 },
    { y: 2.33, w: 0.674, df: 0.366, db: 0.508, n: 2.45 },  // seat
    { y: 2.45, w: 0.664, df: 0.370, db: 0.476, n: 2.5 },
    { y: 2.57, w: 0.596, df: 0.360, db: 0.418, n: 2.7 },   // the hip line
    { y: 2.68, w: 0.506, df: 0.340, db: 0.368, n: 2.8 },
    { y: 2.79, w: 0.424, df: 0.316, db: 0.316, n: 2.9 },
    { y: 2.90, w: 0.386, df: 0.300, db: 0.292, n: 3.0 },   // waist
    { y: 3.01, w: 0.398, df: 0.312, db: 0.292, n: 3.0 },
    { y: 3.12, w: 0.426, df: 0.340, db: 0.300, n: 2.9 },
    { y: 3.23, w: 0.456, df: 0.394, db: 0.308, n: 2.8, cleft: 0.11, cleftW: 0.36 },
    { y: 3.33, w: 0.486, df: 0.502, db: 0.316, n: 2.7, cleft: 0.23, cleftW: 0.34 },
    { y: 3.43, w: 0.508, df: 0.542, db: 0.322, n: 2.6, cleft: 0.25, cleftW: 0.33 },
    { y: 3.53, w: 0.522, df: 0.498, db: 0.326, n: 2.7, cleft: 0.19, cleftW: 0.33 },
    { y: 3.62, w: 0.540, df: 0.408, db: 0.328, n: 2.9, cleft: 0.07, cleftW: 0.34 },
    { y: 3.72, w: 0.562, df: 0.356, db: 0.326, n: 3.0 },   // shoulder
    { y: 3.81, w: 0.526, df: 0.322, db: 0.310, n: 2.9 },
    { y: 3.89, w: 0.410, df: 0.286, db: 0.280, n: 2.8 },
    { y: 3.96, w: 0.286, df: 0.244, db: 0.240, n: 2.6 },
    { y: 4.03, w: 0.180, df: 0.168, db: 0.166, n: 2.4 }
  ];

  /* Limbs are authored hanging from their own joint: y 0 is the shoulder or
     the hip and the profile runs down from there, which is the frame the rig
     already swings them in.  They taper the way a limb tapers -- a shoulder
     cap, a slimmer elbow, a wrist -- rather than being a post with a second
     post dropped over the top of it. */
  var FEMALE_ARM = [
    { y: -2.00, w: 0.098, d: 0.108, n: 2.3 },   // fingers
    { y: -1.90, w: 0.122, d: 0.132, n: 2.3 },   // hand
    { y: -1.78, w: 0.112, d: 0.122, n: 2.2 },   // wrist
    { y: -1.52, w: 0.134, d: 0.148, n: 2.3 },
    { y: -1.24, w: 0.154, d: 0.168, n: 2.4 },   // forearm
    { y: -1.02, w: 0.148, d: 0.162, n: 2.4 },   // elbow
    { y: -0.76, w: 0.170, d: 0.184, n: 2.5 },   // upper arm
    { y: -0.44, w: 0.196, d: 0.210, n: 2.6 },
    { y: -0.14, w: 0.234, d: 0.244, n: 2.8 },
    { y:  0.00, w: 0.246, d: 0.254, n: 2.9 },   // the shoulder joint
    { y:  0.08, w: 0.196, d: 0.206, n: 2.7 }    // ...and the cap above it,
  ];                                            //    tucked into the torso

  var FEMALE_LEG = [
    { y: -2.30, w: 0.118, d: 0.128, n: 2.3 },   // ankle
    { y: -2.16, w: 0.130, d: 0.145, n: 2.3 },
    { y: -1.94, w: 0.158, d: 0.178, n: 2.4 },
    { y: -1.70, w: 0.198, d: 0.220, n: 2.5 },   // calf
    { y: -1.48, w: 0.208, d: 0.230, n: 2.5 },
    { y: -1.26, w: 0.190, d: 0.210, n: 2.4 },   // knee
    { y: -1.02, w: 0.232, d: 0.246, n: 2.5 },
    { y: -0.68, w: 0.282, d: 0.292, n: 2.6 },
    { y: -0.34, w: 0.318, d: 0.322, n: 2.7 },   // thigh
    { y: -0.12, w: 0.332, d: 0.332, n: 2.8 },
    { y:  0.00, w: 0.330, d: 0.330, n: 2.8 }
  ];

  // Longer, with a harder difference between the thigh and the calf, so the
  // slimmer build's legs read as shapely rather than as sticks.
  var FEMALE_LEG_THIN = [
    { y: -2.36, w: 0.104, d: 0.114, n: 2.3 },
    { y: -2.22, w: 0.118, d: 0.132, n: 2.3 },
    { y: -1.98, w: 0.146, d: 0.166, n: 2.4 },
    { y: -1.72, w: 0.190, d: 0.214, n: 2.5 },   // calf
    { y: -1.50, w: 0.198, d: 0.222, n: 2.5 },
    { y: -1.28, w: 0.176, d: 0.196, n: 2.4 },   // knee
    { y: -1.02, w: 0.220, d: 0.236, n: 2.5 },
    { y: -0.66, w: 0.276, d: 0.288, n: 2.6 },
    { y: -0.32, w: 0.314, d: 0.320, n: 2.7 },   // thigh
    { y: -0.12, w: 0.328, d: 0.330, n: 2.8 },
    { y:  0.00, w: 0.326, d: 0.328, n: 2.8 }
  ];

  // A shoe: the rings push forward as they rise, which rounds the toe over
  // rather than ending the foot in a wall.
  var FEMALE_FOOT = [
    { y: 0.00, w: 0.158, df: 0.360, db: 0.170, n: 3.2, cz: 0.05 },
    { y: 0.10, w: 0.170, df: 0.376, db: 0.184, n: 3.0, cz: 0.05 },
    { y: 0.21, w: 0.164, df: 0.336, db: 0.180, n: 2.8, cz: 0.03 },
    { y: 0.30, w: 0.140, df: 0.252, db: 0.168, n: 2.5, cz: 0.00 }
  ];
  /* A garment that stands off the limb: a short sleeve, a pair of shorts.
     Near enough straight, with a little flare at the hem, because that is
     what cloth hanging off an arm does -- and because a sleeve is a sleeve
     rather than the arm painted a different colour half way down. */
  var GARMENT_TUBE = [
    { y: 0.00, w: 0.452, d: 0.452, n: 2.9 },   // hem, flared off the limb
    { y: 0.10, w: 0.428, d: 0.428, n: 2.9 },
    { y: 0.62, w: 0.500, d: 0.500, n: 2.9 },   // standing clear of it
    { y: 1.00, w: 0.462, d: 0.462, n: 2.9 }    // flush at the shoulder or hip
  ];  // A plain ring, scaled to whatever section of the body it has to sit on.
  var GARMENT_BAND = [
    { y: 0.00, w: 0.5, d: 0.5, n: 2.9 },
    { y: 0.50, w: 0.5, d: 0.5, n: 2.9 },
    { y: 1.00, w: 0.5, d: 0.5, n: 2.9 }
  ];

  function bake(name, profile, opts) {
    var built = Geometry.loft(profile, opts);
    Geometry.register(name, built);
    built.mesh_name = name;
    return built;
  }

  function piece(built) {
    return { mesh: built.mesh_name, size: built.size.slice(),
             centre: built.centre.slice() };
  }

  /* Bake one female build out of its two profiles.  The standard cut and the
     slim cut are the same construction with different numbers, which is what
     keeps them recognisably the same character. */
  function bakeFemale(tag, bodyProfile, legProfile) {
    var CHEST = [3.05, 3.69];          // the band a shirt graphic prints on
    var ARC = [-0.118, 0.118];         // ...and how far round the chest it goes
    // measure the patch first so its graphic can be mapped across itself
    var box = Geometry.loft(bodyProfile, { from: CHEST[0], to: CHEST[1], rows: 4,
                                           segs: 12, arc: ARC });
    var half = box.size[0] / 2;
    return {
      torso: bake('ftorso' + tag, bodyProfile,
                  { from: HIP_LINE, to: 4.03, rows: 48, segs: 32 }),
      hips: bake('fhips' + tag, bodyProfile,
                 { from: 1.99, to: HIP_LINE, rows: 26, segs: 32 }),
      // a printed graphic is a patch of the chest itself, lifted clear of it,
      // so it curves with the body instead of floating in front of it
      print: bake('fprint' + tag, bodyProfile,
                  { from: CHEST[0], to: CHEST[1], rows: 18, segs: 20,
                    arc: ARC, inflate: 0.009,
                    uv: { x0: box.centre[0] - half, x1: box.centre[0] + half,
                          y0: CHEST[0], y1: CHEST[1] } }),
      // ...and the hem of the top is a band of the same surface
      hem: bake('fhem' + tag, bodyProfile,
                { from: HIP_LINE + 0.02, to: HIP_LINE + 0.24, rows: 8,
                  segs: 32, inflate: 0.022 }),
      leg: bake('fleg' + tag, legProfile, { rows: 36, segs: 26 }),
      // the trouser stripe runs down the outside of the leg, so it is a
      // lengthways patch of the leg rather than a plank stood beside it
      stripe: bake('fstripe' + tag, legProfile,
                   { rows: 32, segs: 8, arc: [0.206, 0.294], inflate: 0.016 })
    };
  }

  var HEAD_F = bake('fhead', FEMALE_HEAD, {
    rows: 46, segs: 32,
    uv: { x0: -0.586, x1: 0.586, y0: 4.46, y1: 5.17 }
  });
  var NECK_F = bake('fneck', FEMALE_NECK, { rows: 14, segs: 24 });
  var ARM_F = bake('farm', FEMALE_ARM, { rows: 32, segs: 24 });
  var FOOT_F = bake('ffoot', FEMALE_FOOT, { rows: 12, segs: 24 });
  // these two are scaled to whatever they are put on, so only the shape is
  // wanted here and nothing needs to remember the box it came out of
  bake('ftube', GARMENT_TUBE, { rows: 10, segs: 26, caps: false });
  bake('fband', GARMENT_BAND, { rows: 4, segs: 28, caps: false });
  var FEM = bakeFemale('', FEMALE_BODY, FEMALE_LEG);
  var FEM_THIN = bakeFemale('2', FEMALE_BODY_THIN, FEMALE_LEG_THIN);

  /* Assemble one of the two builds.  ``armScale`` narrows the shared arm for
     the slimmer cut; everything else comes straight out of the bake, so the
     numbers in the profiles above are the only place the figure is
     described. */
  function femaleBuild(id, label, parts, armScale, armX, legX) {
    var head = piece(HEAD_F);
    head.neck = piece(NECK_F);
    var arm = piece(ARM_F);
    arm.size = [ARM_F.size[0] * armScale, ARM_F.size[1], ARM_F.size[2] * armScale];
    arm.x = armX;
    arm.pivotY = 3.745;
    arm.reach = 2.00;
    arm.scale = armScale;
    arm.at = ARM_F.at;
    var leg = piece(parts.leg);
    leg.x = legX;
    leg.pivotY = 2.42;
    leg.reach = parts.leg.size[1];
    leg.at = parts.leg.at;
    leg.stripe = piece(parts.stripe);
    return {
      id: id, label: label, family: 'female', gait: 'fem', kind: 'loft',
      head: head,
      // the body surface, cut only where the clothes cut it
      skin: { torso: piece(parts.torso), hips: piece(parts.hips),
              print: piece(parts.print), hem: piece(parts.hem),
              at: parts.torso.at, hipLine: HIP_LINE },
      // shorthands the shared code still reads
      chest: { size: [parts.print.size[0] * 2.1, 0.62, parts.torso.size[2]],
               y: 3.43 },
      hips: { size: parts.hips.size.slice(), y: parts.hips.centre[1] },
      pelvisY: parts.hips.centre[1],
      waistLine: 2.90,
      arm: arm,
      leg: leg,
      foot: piece(FOOT_F),
      garment: { tube: 'ftube', band: 'fband' },
      backAnchor: [0, 3.26, -0.40]
    };
  }

  BODIES.female = femaleBuild('female', 'Female', FEM, 1.00, 0.742, 0.360);
  BODIES.female_thin = femaleBuild('female_thin', 'Thin', FEM_THIN, 0.88,
                                   0.672, 0.338);

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
      pose.armLZ = running ? 0.085 : 0.095;
      pose.armRZ = -pose.armLZ;
      pose.bob = Math.abs(Math.sin(phase)) * (running ? 0.115 : 0.07);
      pose.lean = running ? 0.10 : 0.05;
      // the pelvis: across to the standing leg, up on the swinging side
      pose.hipShift = -swing * (running ? 0.10 : 0.13);
      pose.hipRoll = swing * (running ? 0.10 : 0.13);
      pose.hipTwist = swing * (running ? 0.22 : 0.17);
      pose.legPinch = running ? 0.30 : 0.22;
      pose.legRoll = running ? 0.08 : 0.06;
      // the shoulders turn against the hips and stay over the centre line
      pose.torsoTwist = -pose.hipTwist * 0.66;
      pose.torsoShift = -pose.hipShift * 0.30;
      pose.chestRoll = -pose.hipRoll * 0.40;
    } else if (state === 'jump') {
      pose.armL = -2.25; pose.armR = -2.25;
      pose.armLZ = 0.14; pose.armRZ = -0.14;
      pose.legL = -0.34; pose.legR = 0.40;
      pose.legPinch = 0.5; pose.legRoll = 0.12;
      pose.hipRoll = 0.05; pose.lean = 0.06;
    } else if (state === 'fall') {
      pose.armL = -1.62; pose.armR = -1.62;
      pose.armLZ = 0.18; pose.armRZ = -0.18;
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
      pose.armLZ = 0.075;
      pose.armRZ = -0.085;
      pose.bob = breath * 0.018;
      pose.hipShift = -0.075 + breath * 0.012;
      pose.hipRoll = 0.075 + breath * 0.012;
      pose.hipTwist = -0.05;
      pose.legPinch = 0.05;
      pose.legRoll = 0.035;
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

    // ----------------------------------------------------------- colouring
    var torsoColour = shirtData.torso || colourOf(descriptor, 'torso', '#0d69ac');
    var torsoDecal = shirtData.decal ? Textures.decal(shirtData.decal) : null;
    // the hips read as part of the lower body, so they take the trousers
    var hipColour = pantsData.legs || colourOf(descriptor, 'left_leg', '#a4bd47');
    var headColour = colourOf(descriptor, 'head', '#f5cd30');
    var faceSlot = (face && face.data)
      ? Textures.faceSlot(face.item_id, face.data) : null;

    var holding = opts.holding;
    var rightSwing = pose.armR;
    if (holding) rightSwing = -1.32 + (opts.pitch || 0) * 0.55;
    var leftSwing = pose.armL;
    if (holding && holding.twoHanded !== false) leftSwing = -1.15 + (opts.pitch || 0) * 0.4;
    var rightHand = null;

    /* ------------------------------------------------------------ the body
       Two constructions share every helper above.  The male builds are a
       stack of rounded boxes, which is the right shape for them.  The female
       builds are one lofted skin, because a figure with real curves cannot
       be made by bolting pieces onto a box -- see BODIES.female. */
    if (body.kind === 'loft') buildSkin(); else buildBlocks();

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

    /* Place a part of a lofted body.  Everything baked by Geometry.loft
       comes back with the box it was measured in, so a piece only has to be
       put back where it came from: no per-part numbers, and the profile at
       the top of this file is the only description of the figure. */
    function skinPart(part, colour, extra) {
      extra = extra || {};
      extra.t = part.mesh;
      return placeTrunk(part.centre[0], part.centre[1], part.centre[2],
                        part.size.slice(), colour, extra);
    }

    function buildSkin() {
      var skin = body.skin;

      // ---- the top: one piece of the body, wearing the shirt's colour
      skinPart(skin.torso, torsoColour, { k: 'torso' });
      // a printed graphic is a patch of that same surface lifted clear of
      // it, so it curves with the chest instead of floating in front of it
      if (torsoDecal) {
        skinPart(skin.print, torsoColour, { decSlot: torsoDecal, k: 'torso' });
      }
      // ...and the hem of the top is a band of it
      if (shirtData.stripe) skinPart(skin.hem, shirtData.stripe, { k: 'torso' });
      if (shirtData.stripes) {
        // bands up the chest, each one scaled to the section of the body it
        // sits on, so they follow the shape rather than cutting through it
        var top = 3.70, bottom = 2.94;
        for (var si = 0; si < shirtData.stripes; si++) {
          var t = shirtData.stripes > 1 ? si / (shirtData.stripes - 1) : 0.5;
          var y = bottom + (top - bottom) * t;
          var sec = skin.at(y);
          placeTrunk(sec.cx, y, sec.cz + (sec.df - sec.db) / 2,
                     [sec.w * 2.10, 0.082, (sec.df + sec.db) * 1.06],
                     shirtData.stripe || '#1b2a35',
                     { t: body.garment.band, k: 'torso' });
        }
      }
      if (shirtData.hood) {
        placeTrunk(0, 3.82, -0.34, [0.82, 0.70, 0.68],
                   shirtData.torso || torsoColour, { t: 'sph', k: 'torso' });
      }

      // ---- the trousers: the same surface below the hip line
      skinPart(skin.hips, hipColour, { k: 'hips', ry: hipTwist, rz: hipRoll });

      // ---- neck and head
      place([0, head.neck.centre[1], head.neck.centre[2]],
            head.neck.size.slice(), headColour, { t: head.neck.mesh, k: 'neck' });
      place([head.centre[0], head.centre[1], head.centre[2]],
            head.size.slice(), headColour,
            { t: head.mesh, decSlot: faceSlot, k: 'head' });

      // ---- arms
      var armLen = body.arm.reach;
      var armScale = body.arm.scale || 1;
      function limbArm(side, swing, roll) {
        var shoulder = body.arm.x * side;
        var pivotY = body.arm.pivotY;
        roll = roll || 0;
        function at(down, forward, lateral) {
          var o = limbPoint(down, forward || 0, swing, roll, lateral || 0);
          var xz = rotateY(shoulder + torsoShift + o[0], o[2], torsoTwist);
          return [xz[0], pivotY + o[1], xz[1]];
        }
        var bare = colourOf(descriptor, side < 0 ? 'right_arm' : 'left_arm', '#f5cd30');
        var sleeve = shirtData.arms;
        var coverage = shirtData.sleeves === undefined ? 1.0 : shirtData.sleeves;
        var extra = { t: body.arm.mesh, rx: swing, ry: torsoTwist, rz: roll,
                      k: 'arm' };
        var full = sleeve && coverage >= 0.99;
        place(at(-body.arm.centre[1] * 1, body.arm.centre[2] * armScale,
                 body.arm.centre[0] * armScale),
              body.arm.size.slice(), full ? sleeve : bare, extra);
        /* A short sleeve is a sleeve: cloth standing off the arm, not the
           arm painted a different colour half way down.  It starts above the
           joint, because the shoulder cap is tucked up there and a sleeve
           that began at the joint would leave a bare shoulder above it. */
        if (sleeve && !full && coverage > 0.01) {
          var cap = Math.max(0, body.arm.size[1] - armLen);
          var span = armLen * coverage;
          place(at((span - cap) / 2), [body.arm.size[0] * 1.10, span + cap,
                                       body.arm.size[2] * 1.10], sleeve,
                { t: body.garment.tube, rx: swing, ry: torsoTwist, rz: roll,
                  k: 'arm' });
        }
        var hand = at(armLen);
        return { x: hand[0], y: hand[1], z: hand[2], swing: swing };
      }
      rightHand = limbArm(-1, rightSwing, holding ? 0 : pose.armRZ);
      limbArm(1, leftSwing, holding ? 0 : pose.armLZ);

      // ---- legs
      var legLen = body.leg.reach;
      function limbLeg(side, swing) {
        var root = body.leg.x * side * (1 - legPinch);
        var roll = -side * legRoll;
        var seat = hipRoot(root);
        var pivotY = seat.y;
        root = seat.x;
        function at(down, forward, lateral) {
          var o = limbPoint(down, forward || 0, swing, roll, lateral || 0);
          var xz = rotateY(root + hipShift + o[0], o[2], hipTwist);
          return [xz[0], pivotY + o[1], xz[1]];
        }
        var bare = colourOf(descriptor, side < 0 ? 'right_leg' : 'left_leg', '#a4bd47');
        var trouser = pantsData.legs;
        var length = pantsData.length === undefined ? 1.0 : pantsData.length;
        var full = trouser && length >= 0.99;
        var extra = { t: body.leg.mesh, rx: swing, ry: hipTwist, rz: roll,
                      k: 'leg' };
        var shoeColour = full ? (pantsData.cuff || trouser) : bare;
        place(at(-body.leg.centre[1], body.leg.centre[2], body.leg.centre[0]),
              body.leg.size.slice(),
              full ? trouser : (trouser ? (pantsData.skin || bare) : bare), extra);
        if (trouser && !full && length > 0.01) {
          var span = legLen * length;
          place(at(span / 2), [body.leg.size[0] * 1.06, span,
                               body.leg.size[2] * 1.06], trouser,
                { t: body.garment.tube, rx: swing, ry: hipTwist, rz: roll,
                  k: 'leg' });
        }
        if (pantsData.cuff && full) {
          var cuffDown = legLen - 0.19;
          var sec = body.leg.at(-cuffDown);
          place(at(cuffDown), [sec.w * 2.18, 0.20, (sec.df + sec.db) * 1.09],
                pantsData.cuff,
                { t: body.garment.band, rx: swing, ry: hipTwist, rz: roll,
                  k: 'leg' });
        }
        if (pantsData.stripe) {
          // a lengthways patch of the leg's own surface, so the stripe
          // follows the calf instead of standing off it
          var st = body.leg.stripe;
          place(at(-st.centre[1], st.centre[2], side * st.centre[0]),
                st.size.slice(), pantsData.stripe,
                { t: st.mesh, rx: swing, rz: roll,
                  ry: hipTwist + (side < 0 ? Math.PI : 0),
                  m: pantsData.glow ? 'neon' : '', k: 'leg' });
        }
        if (body.foot) {
          place(at(body.leg.pivotY - body.foot.centre[1], body.foot.centre[2]),
                body.foot.size.slice(), shoeColour,
                { t: body.foot.mesh, rx: swing, ry: hipTwist, rz: roll,
                  k: 'foot' });
        }
      }
      limbLeg(-1, pose.legR);
      limbLeg(1, pose.legL);
    }

    function buildBlocks() {
      // --------------------------------------------------------------- torso
      body.torso.forEach(function (segment) {
        placeTrunk(0, segment.y, 0, segment.size.slice(), torsoColour, {
          decSlot: segment.decal ? torsoDecal : null, k: 'torso'
        });
      });
      // the hips read as part of the lower body, so they take the trousers
      placePelvis(0, body.hips.y, 0, body.hips.size.slice(), hipColour, { k: 'hips' });

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
