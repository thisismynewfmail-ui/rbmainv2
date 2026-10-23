/* BLOCKHAVEN game -- pets in a world.

   Every player whose avatar carries a pet (app/models/pets.py) has her
   follow them about.  Nothing about a pet goes over the network: each client
   runs every pet it can see from the owner's position, velocity, animation,
   health and the events it already receives (shots, kills, chat, deaths), so
   a pet costs no bandwidth and no server time, and what she does is the
   same kind of thing on every screen even if not the same frame of it.

   A pet is a little creature with a mind, in four layers:

     perception   what her owner is doing (moving, jumping, landing, hurt,
                  healed, shooting, scoring, dead, chatting), who else is
                  about (players, their pets, enemies, the horde) and how long
                  things have been as they are
     mood         joy, energy, fear, anger, sadness, love, boredom and
                  sleepiness, pushed by events and drifting back to her own
                  baseline -- which her persona tags set
     intent       one of a dozen states (follow, catch up, settle, wander,
                  play, greet, guard, hide, mourn, sleep, ...) chosen by
                  weighing what is happening against her persona, and a
                  stream of one-shot actions from static/js/engine/pet.js
                  layered on top (a wave while walking, a cheer, a yawn)
     body         steering with ground probes, step-ups, ledge jumps, falls,
                  wall-sliding, separation and line-of-fire avoidance; a gait
                  matched to her speed and her species (Fern skips, Mochi
                  hops, Luna floats, Pixel fires her boot jets); a head that
                  looks at what she is interested in; blinks, glances, hair
                  that lags and swings; and little emotes over her head

   Persona tags (PERSONA below) are numbers, not scripts: Shy raises the
   weight on hiding and lowers the one on greeting, Curious widens how far
   she will wander and how often, Sleepy lowers how long she will wait before
   she sits down -- so three tags together make a character rather than
   three behaviours bolted together.

   Following is the thing her owner sees her do most, so it gets the most
   care (see "following" below).  She keeps a ring of personal space well
   outside their body and only comes inside it on purpose -- a hug, a pat on
   the head, hiding behind their legs -- and then drifts back out.  On the
   move she trails further back the faster they go, with three ideas of
   where "behind" is (their footsteps, straight back from their heading, the
   line from them to her) blended by her persona so she keeps to their path,
   swings wide of their turns or cuts inside them; she weaves, crosses
   behind them to the other side, keeps a pace of her own that drifts about
   theirs, lags and then scampers to catch up, and reads where they are
   going rather than chasing where they were.  Whims take her now and then
   (a sniff at something by the wayside, a dash ahead to wait for them, a
   dawdle and a gallop, a run alongside, a string of happy hops), and she
   answers how they move: a hop when they jump, a skid when they stop dead,
   a spin when they set off at a run, a sit and then a lie-down when they
   stay put. */
(function (global) {
  'use strict';

  var TAU = Math.PI * 2;
  var GRAVITY = 62;
  var MAX_SPEED = 28;
  var TELEPORT_AT = 58;
  var DRAW_RANGE = 170;
  // personal space, in studs: she never settles nearer her owner than
  // MIN_SPACE, and nothing but a purpose brings her inside BUBBLE
  var MIN_SPACE = 6.0;
  var BUBBLE = 4.3;
  // what she keeps clear of on her way anywhere (BUBBLE and a stride: she
  // goes round them, not across it), and how short of a spot she may come
  // to a stop
  var ROUND = BUBBLE + 0.8;
  var ARRIVE = 0.4;
  // her owner's path, as breadcrumbs CRUMB studs apart, the last TRAIL of them
  var TRAIL = 40;
  var CRUMB = 1.4;
  // how long after a shot her owner's gun counts as in use: she keeps out
  // of the line of fire while they are shooting, not whenever they happen
  // to look her way with something in their hands
  var LIVE_FIRE = 2.5;

  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function rand(a, b) { return a + Math.random() * (b - a); }
  function pick(list) { return list[(Math.random() * list.length) | 0]; }
  function wrap(a) {
    while (a > Math.PI) a -= TAU;
    while (a < -Math.PI) a += TAU;
    return a;
  }
  function hdist(a, b) { return Math.hypot(a[0] - b[0], a[2] - b[2]); }
  /* Where along the way from (ax, az) to (bx, bz) it comes nearest
     (cx, cz), as a share of the way (0 at a, 1 at b). */
  function nearestAlong(ax, az, bx, bz, cx, cz) {
    var dx = bx - ax, dz = bz - az, l2 = dx * dx + dz * dz;
    return l2 > 1e-9 ? clamp(((cx - ax) * dx + (cz - az) * dz) / l2, 0, 1) : 0;
  }

  // ------------------------------------------------------------- persona
  /* Who she is, as numbers.  Every pet starts from BASE; each persona tag
     adds its leanings.  The follower reads these when it weighs what to do. */
  var BASE = {
    follow: 7.6,     // how far from her owner she is comfortable, in studs
    lead: 0,         // dashes ahead of them, and runs alongside when they run
    wander: 0.15,    // how readily she goes off to look at something
    range: 4,        // how far beyond her comfortable distance she goes then
    fidget: 0.5,     // how often she does something while waiting
    patience: 9,     // seconds of stillness before she sits down
    bounce: 0.25,    // hops and skips
    brave: 0.25, shy: 0.15, chat: 0.15, clumsy: 0.02, showoff: 0.15,
    cling: 0.25, play: 0.2, dream: 0.15, copy: 0.25, greet: 0.4, curious: 0.25,
    energy: 0.5, feisty: 0,
    // how she follows: cut > 0 cuts inside her owner's turns, < 0 swings
    // wide of them, 0 keeps to their footsteps; weave is how much she
    // meanders; lateral how far round to the side of them she walks (an
    // angle off straight behind); anticipate how far ahead (in seconds) she
    // reads where they are going
    cut: 0.1, weave: 0.45, lateral: 0.5, anticipate: 0.28
  };
  var PERSONA = {
    cheerful:  { greet: 0.45, bounce: 0.3, energy: 0.15, fidget: 0.15, weave: 0.15,
                 follow: -0.2 },
    shy:       { shy: 0.8, greet: -0.35, follow: 1.6, showoff: -0.2, chat: -0.1, cut: -0.55,
                 lateral: 0.2, weave: -0.15 },
    curious:   { wander: 0.5, curious: 0.7, range: 4, follow: 0.7, weave: 0.45,
                 anticipate: 0.08 },
    loyal:     { copy: 0.65, follow: -0.9, cling: 0.3, wander: -0.1, patience: 4,
                 lateral: -0.3, weave: -0.25, cut: -0.15, anticipate: 0.15 },
    sleepy:    { patience: -6, energy: -0.3, fidget: -0.25, weave: 0.1 },
    energetic: { energy: 0.45, lead: 0.75, bounce: 0.5, fidget: 0.45, patience: 6, cut: 0.5,
                 anticipate: 0.12, follow: 0.3 },
    feisty:    { feisty: 0.8, brave: 0.35, energy: 0.2, cut: 0.3 },
    dreamy:    { dream: 0.75, energy: -0.1, fidget: 0.1, weave: 0.6, cut: -0.4, follow: 0.5,
                 anticipate: -0.15 },
    playful:   { play: 0.75, bounce: 0.3, fidget: 0.2, lead: 0.35, weave: 0.35, cut: 0.3 },
    brave:     { brave: 0.75, shy: -0.2, cut: 0.15, follow: -0.2 },
    clingy:    { cling: 0.85, follow: -1.3, wander: -0.15, range: -2, lateral: -0.15, cut: 0.25 },
    showoff:   { showoff: 0.8, greet: 0.3, lead: 0.25, follow: -0.3 },
    chatty:    { chat: 0.8, greet: 0.2, follow: -0.2 },
    clumsy:    { clumsy: 0.2, weave: 0.2 }
  };

  function traitsOf(tags) {
    var t = {};
    Object.keys(BASE).forEach(function (k) { t[k] = BASE[k]; });
    (tags || []).forEach(function (tag) {
      var add = PERSONA[tag];
      if (!add) return;
      Object.keys(add).forEach(function (k) { t[k] += add[k]; });
    });
    // clingy and loyal come nearer, shy and dreamy keep further off, but
    // every one of them stays well outside her owner's body
    t.follow = clamp(t.follow, MIN_SPACE + 0.4, 11.5);
    t.patience = clamp(t.patience, 2.5, 20);
    t.range = clamp(t.range, 2.5, 10);
    t.cut = clamp(t.cut, -1, 1);
    t.weave = clamp(t.weave, 0, 1.2);
    t.lateral = clamp(t.lateral, 0.1, 0.95);
    t.anticipate = clamp(t.anticipate, 0, 0.6);
    ['wander', 'fidget', 'bounce', 'brave', 'shy', 'chat', 'clumsy', 'showoff', 'cling',
     'play', 'dream', 'copy', 'greet', 'curious', 'energy', 'lead', 'feisty']
      .forEach(function (k) { t[k] = clamp(t[k], 0, 1); });
    t.tags = {};
    (tags || []).forEach(function (tag) { t.tags[tag] = true; });
    return t;
  }

  /* What she does with her time while her owner stands still, weighted by
     who she is -- the idle repertoire. */
  function idlePool(f) {
    var t = f.traits, sp = f.species.id, pool = [];
    function add(name, w) { if (w > 0) pool.push([name, w]); }
    add('look', 1 + t.curious * 2);
    add('stretch', 0.5);
    add('yawn', 0.3 + f.mood.sleepy * 2 + (t.tags.sleepy ? 1 : 0));
    add('hum', t.dream * 2.5 + 0.2);
    add('twirl', t.dream * 1.2 + t.showoff * 1.5);
    add('pose', t.showoff * 2.2);
    add('curtsy', t.showoff * 0.8 + (sp === 'fern' ? 0.6 : 0));
    add('dance', t.play * 1.2 + t.energy * 0.8);
    add('kick', t.play * 0.8 + t.energy * 0.5);
    add('giggle', t.chat * 1.2 + t.shy * 0.6);
    add('think', t.curious * 1.2);
    add('sparkle', t.tags.cheerful ? 1 : 0.2);
    add('heart', t.cling * 1.4 + (t.tags.loyal ? 0.6 : 0));
    add('salute', t.tags.loyal ? 0.8 : 0);
    add('shadowbox', t.feisty * 1.4);
    add('flex', t.brave * 0.6 + t.feisty * 0.6);
    add('nod', 0.4);
    add('sneeze', sp === 'ember' ? 0.5 : 0.08);
    add('ear_twitch', sp === 'mochi' ? 1.6 : 0);
    add('scan', sp === 'pixel' ? 1.4 : 0);
    add('float_spin', sp === 'luna' ? 1.0 : 0);
    add('fistpump', t.energy * 0.6);
    add('pout', t.cling * (f.mood.sad > 0.3 ? 1.5 : 0.2));
    return pool;
  }

  function weighted(pool) {
    var total = 0;
    pool.forEach(function (p) { total += p[1]; });
    var r = Math.random() * total;
    for (var i = 0; i < pool.length; i++) {
      r -= pool[i][1];
      if (r <= 0) return pool[i][0];
    }
    return pool.length ? pool[pool.length - 1][0] : 'idle';
  }

  // The actions that only need her arms and face, so she can do them on
  // the move -- a wave while walking, a heart while trotting along.
  var UPPER = { wave: 1, clap: 1, heart: 1, giggle: 1, think: 1, salute: 1, fistpump: 1,
                cover_ears: 1, nod: 1, shake: 1, sparkle: 1, hum: 1, scan: 1, ear_twitch: 1,
                flex: 1 };
  // the parts of a pose an upper-body action takes over, and the parts a
  // face-only one does (lying down)
  var UPPER_KEYS = ['armL', 'armR', 'armLZ', 'armRZ', 'headYaw', 'headPitch', 'headRoll', 'eyes',
                    'mouth', 'brows', 'blush', 'glow', 'flame', 'perk', 'earL', 'earR', 'sniff'];
  var FACE_KEYS = ['headRoll', 'eyes', 'mouth', 'brows', 'blush', 'glow', 'flame', 'perk',
                   'earL', 'earR', 'sniff'];
  // whole-body actions that do not root her to the spot: she leaps, slides
  // or spins on with the way she was going
  var MOBILE = { jump: 1, pounce: 1, skid: 1, zoom_spin: 1 };
  // what she does up close to her owner on purpose, inside her ring
  var CLOSE = { hide: 1, comfort: 1, visit: 1 };
  // what she does to pass the time, and drops when her owner sets off
  var IDLE = { follow: 1, play: 1, wander: 1, sit: 1, lie: 1, petpal: 1, greet: 1, visit: 1 };

  // the colour of Pixel's antenna for each feeling
  var LED = { joy: '#4ff2ff', love: '#ff6fd8', anger: '#ff4040', fear: '#ffd23a',
              sad: '#5b7cff', sleepy: '#8a7cff', calm: '#7dffb0' };

  // ============================================================ follower
  function Follower(world, key, pet) {
    this.world = world;
    this.key = key;
    this.pos = null;
    this.vel = [0, 0, 0];
    this.vy = 0;
    this.grounded = true;
    this.yaw = 0;
    this.turnRate = 0;
    this.pose = Pet.restPose();
    this.stride = Math.random() * 10;
    this.time = Math.random() * 100;
    this.mood = { joy: 0.6, energy: 0.5, fear: 0, anger: 0, sad: 0, love: 0.35,
                  bored: 0, sleepy: 0 };
    this.act = null;            // the one-shot action playing: {name, t, dur, upper}
    this.state = 'follow';      // what she is doing
    this.stateT = 0;
    this.side = Math.random() < 0.5 ? -1 : 1;
    this.still = 0;             // how long her owner has stood still
    this.idleIn = rand(2, 4);   // until her next idle action
    this.blinkAt = rand(1, 3);
    this.blinkT = -1;
    this.glance = [0, 0];
    this.glanceT = 0;
    this.head = [0, 0];         // eased head yaw and pitch
    this.look = null;           // world point she is looking at
    this.lookWhy = '';
    this.stuck = 0;
    this.cool = {};             // cooldowns by name
    this.memory = { owner: null, health: null, alive: true, air: false, airTop: 0,
                    deathAt: null, near: {}, pets: {} };
    this.sway = [0, 0, 0, 0];   // hair spring: x, z and their velocities
    this.emoteT = rand(4, 9);
    this.toy = null;            // a butterfly she is chasing
    this.queue = [];            // actions waiting to play, with delays
    this.lastAccel = 0;
    this.thinkT = 0;
    this.visible = true;
    // following: her owner's way (smoothed), how sharply they are turning,
    // and the path they took
    this.heading = [0, 1];
    this.turn = 0;
    this.oSpd = 0;
    this.crumbs = new Float32Array(TRAIL * 3);
    this.crumbN = 0;
    this.crumbSeq = -1;         // the newest crumb's number; crumb n lives at n % TRAIL
    this.via = -1;              // the crumb she is making for round a corner, or -1
    this.blocked = false;       // the way to where she wants to be is not clear
    this.losT = 0;
    // her own travel: a heading and a speed along it, each eased
    this.hdg = 0;
    this.spd = 0;
    this.shuffling = false;
    this.sideK = this.side;     // her side, eased, so she crosses behind them in an arc
    this.swapAt = -9;           // when she last swapped sides on purpose
    this.phase = [rand(0, TAU), rand(0, TAU), rand(0, TAU)];
    this.paceK = 1;             // her pace, as a share of theirs
    this.paceTo = 1;
    this.paceT = 0;
    this.scamper = false;       // flat out to catch up
    this.whim = null;           // a little plan of her own while following
    this.whimAt = this.time + rand(4, 9);
    this.besideK = 0;           // running alongside rather than behind
    this.settle = null;         // her spot while her owner stands still
    this.settleT = 0;
    this.settleFor = 20;
    this.skid = 0;
    this.lying = false;
    this.lieAfter = 10;
    this.ownerLook = 0;         // looking up at her owner until then
    this.glanceUp = rand(2, 5);
    this.tilt = 0;              // a tilt of the head, and where it is going
    this.tiltTo = 0;
    this.tiltT = 0;
    this.twistE = 0;            // her shoulders turned to look back
    this.ears = [0, 0];         // a spring on her starts and stops
    this.ledgeTop = null;       // the top of the ledge she is leaping up onto
    this.overshoot = 1.15;      // how much harder she plans to stop than she can
    this.roundSg = 0;           // which way round her owner she is going, or 0
    this.meetIn = 9;            // on a collision course with them: how soon,
    this.meetVs = 0;            // how fast, how much of that is them coming
    this.meetBy = 0;            // at her, and the quickest way off it
    this.asideX = 0;
    this.asideZ = 0;
    // scratch space reused every frame
    this.goalP = [0, 0, 0];
    this.aimP = [0, 0, 0];
    this.roundP = [0, 0, 0];
    this.landP = [0, 0, 0];
    this.trailP = [0, 0, 0];
    this.trailDir = [0, 1];
    this.sep = [0, 0];
    this.cool.visit = this.time + rand(12, 30);
    this.setPet(pet);
  }

  Follower.prototype.setPet = function (pet) {
    this.pet = pet;
    this.species = Pet.species(pet);
    this.traits = traitsOf(pet.tags);
    this.name = (pet.name || this.species.name).toLowerCase();
    this.mood.energy = clamp(0.35 + this.traits.energy * 0.5, 0, 1);
    // an eager, clumsy pet comes in long and has to settle back; a careful
    // one stops on the spot
    var t = this.traits;
    this.overshoot = 1.05 + t.energy * 0.25 + t.clumsy * 0.6 + t.play * 0.1 - t.shy * 0.08;
  };

  Follower.prototype.cooled = function (name, secs) {
    var now = this.time;
    if (this.cool[name] && now < this.cool[name]) return false;
    this.cool[name] = now + secs;
    return true;
  };

  /* Play a one-shot action now (or after ``delay`` seconds). */
  Follower.prototype.play = function (name, delay, force) {
    if (delay) { this.queue.push({ name: name, at: this.time + delay, force: force }); return; }
    if (this.act && !force && this.act.prio && this.act.t < this.act.dur * 0.6) return;
    var dur = Pet.DURATION[name] || 2;
    this.act = { name: name, t: 0, dur: dur, upper: !!UPPER[name], prio: !!force };
    this.onAction(name);
  };

  /* Emotes and effects that go with an action. */
  Follower.prototype.onAction = function (name) {
    var sp = this.species.id;
    if (name === 'cheer' || name === 'fistpump') this.emote('sparkle', 3);
    if (name === 'heart' || name === 'hug') this.emote('heart', 2);
    if (name === 'hum') this.emote('note', 1);
    if (name === 'twirl' || name === 'float_spin') {
      this.emote(sp === 'fern' ? 'petals' : (sp === 'luna' ? 'stars' : 'sparkle'), 4);
    }
    if (name === 'stomp' || name === 'shadowbox') this.emote('anger', 1);
    if (name === 'trip') this.emote('bang', 1);
    if (name === 'pant' || name === 'shy') this.emote('sweat', 1);
    if (name === 'scan') this.emote('bits', 5);
    if (name === 'think' || name === 'inspect') this.emote('quest', 1);
    if (name === 'sneeze' && sp === 'ember') this.queueEmote('sparks', 0.85, 10);
  };

  Follower.prototype.queueEmote = function (kind, delay, n) {
    var self = this;
    this.queue.push({ emote: kind, n: n, at: this.time + delay });
    return self;
  };

  // ------------------------------------------------------------ perception
  Follower.prototype.perceive = function (o, dt) {
    var m = this.memory;
    var ev = [];
    var air = !o.grounded;
    if (air && !m.air) { m.airTop = o.pos[1]; ev.push('jump'); }
    if (air) m.airTop = Math.max(m.airTop, o.pos[1]);
    if (!air && m.air) ev.push(m.airTop - o.pos[1] > 6 ? 'bigland' : 'land');
    m.air = air;
    if (m.health !== null && o.health < m.health - 0.5 && o.alive) ev.push('hurt');
    if (m.health !== null && o.health > m.health + 4 && o.alive && m.alive) ev.push('heal');
    m.health = o.health;
    if (m.alive && !o.alive) { ev.push('died'); m.deathAt = o.pos.slice(); }
    if (!m.alive && o.alive) ev.push('respawn');
    m.alive = o.alive;
    // how they are moving: which way (smoothed, so a wobble of the stick is
    // not a turn), how sharply they are turning, and the moments it changes
    var s = o.speed, h = this.heading;
    if (s > 0.8) {
      // (eased as an angle: easing the direction itself never comes round
      // at all when they turn straight back the way they came)
      var want = Math.atan2(o.vel[0], o.vel[2]), was = Math.atan2(h[0], h[1]);
      var now = was + wrap(want - was) * Math.min(1, dt * 6);
      h[0] = Math.sin(now); h[1] = Math.cos(now);
      this.turn = wrap(want - now);
    } else {
      this.turn = 0;
    }
    if (s > 9) { m.fastAt = this.time; m.halted = false; }
    if (s > 14) m.runFor = (m.runFor || 0) + dt;
    // their speed, eased down slowly: how far back she trails does not
    // snap in when they stop
    this.oSpd = s > this.oSpd ? s : lerp(this.oSpd, s, Math.min(1, dt * 1.5));
    if (s > 2.5 && !m.moving) {
      m.moving = true;
      m.setOff = this.time;
      m.waited = this.still;            // how long they stood there first
    } else if (m.moving && !m.halted && s < 4 && this.time - (m.fastAt || -9) < 0.25) {
      // stopping dead from a run is a different thing from slowing down,
      // and she knows it the moment they plant their feet
      m.halted = true;
      ev.push('halt');
    } else if (s < 1.2 && m.moving) {
      m.moving = false;
      if (!m.halted) ev.push('stop');
      m.halted = false;
    }
    if (m.moving && s > 12 && m.waited > 1.0 && this.time - m.setOff < 0.6) {
      ev.push('dash');                  // off at a run from a standstill
      m.waited = 0;
    }
    if (s > 6 && Math.abs(this.turn) > 2.2 && this.cooled('uturn', 1.5)) ev.push('uturn');
    if (o.speed > 1.2 || air) this.still = 0;
    else this.still += dt;
    // the path they took, for her to follow round corners; a jump of more
    // than a few strides in a frame is a respawn or a teleport, not a path
    var lp = m.lastPos;
    if (lp && hdist(lp, o.pos) > 14) this.crumbN = 0;
    if (!lp) lp = m.lastPos = [0, 0, 0];
    lp[0] = o.pos[0]; lp[1] = o.pos[1]; lp[2] = o.pos[2];
    this.lay(o.pos);
    return ev;
  };

  /* Drop a breadcrumb where her owner is, if they have come far enough from
     the last one.  The crumbs are a ring of TRAIL in one typed array. */
  Follower.prototype.lay = function (p) {
    var c = this.crumbs, i;
    if (this.crumbN) {
      i = (this.crumbSeq % TRAIL) * 3;
      if (Math.hypot(p[0] - c[i], p[2] - c[i + 2]) < CRUMB) return;
    } else {
      this.via = -1;
    }
    this.crumbSeq++;
    i = (this.crumbSeq % TRAIL) * 3;
    c[i] = p[0]; c[i + 1] = p[1]; c[i + 2] = p[2];
    if (this.crumbN < TRAIL) this.crumbN++;
  };

  /* Crumb number n, copied into ``into``. */
  Follower.prototype.crumb = function (n, into) {
    var i = (n % TRAIL) * 3, c = this.crumbs;
    into[0] = c[i]; into[1] = c[i + 1]; into[2] = c[i + 2];
    return into;
  };

  /* The point ``dist`` studs back along the way her owner came, into
     ``into``; this.trailDir is the way they were going there.  Past the end
     of the crumbs it carries on straight back. */
  Follower.prototype.trailPoint = function (o, dist, into) {
    var c = this.crumbs, dir = this.trailDir;
    var px = o.pos[0], py = o.pos[1], pz = o.pos[2], left = dist;
    dir[0] = this.heading[0]; dir[1] = this.heading[1];
    for (var j = 0; j < this.crumbN; j++) {
      var i = ((this.crumbSeq - j) % TRAIL) * 3;
      var qx = c[i], qz = c[i + 2];
      var len = Math.hypot(qx - px, qz - pz);
      if (len > 1e-3) {
        dir[0] = (px - qx) / len; dir[1] = (pz - qz) / len;
        if (len >= left) {
          var f = left / len;
          into[0] = px + (qx - px) * f; into[1] = py + (c[i + 1] - py) * f; into[2] = pz + (qz - pz) * f;
          return into;
        }
        left -= len;
      }
      px = qx; py = c[i + 1]; pz = qz;
    }
    into[0] = px - dir[0] * left; into[1] = py; into[2] = pz - dir[1] * left;
    return into;
  };

  /* The crumb nearest her: where she joins their path to go round a corner. */
  Follower.prototype.nearestCrumb = function () {
    var c = this.crumbs, best = -1, bestD = 1e9;
    for (var j = 0; j < this.crumbN; j++) {
      var n = this.crumbSeq - j, i = (n % TRAIL) * 3;
      var d = Math.hypot(c[i] - this.pos[0], c[i + 2] - this.pos[2]);
      if (d < bestD) { bestD = d; best = n; }
    }
    return best;
  };

  /* Everyone else about: players near her owner, other pets near her, and
     anything hostile. */
  Follower.prototype.surroundings = function (o) {
    var world = this.world, self = this;
    var near = [], pets = [], threat = null, threatD = 1e9;
    world.owners.forEach(function (other) {
      if (other.key === self.key || !other.alive) return;
      var d = hdist(other.pos, o.pos);
      if (d < 11) near.push({ key: other.key, pos: other.pos, d: d, name: other.name,
                              enemy: o.team && other.team && other.team !== o.team });
      if (o.team && other.team && other.team !== o.team && d < 26 && d < threatD) {
        threat = other.pos; threatD = d;
      }
    });
    Object.keys(world.followers).forEach(function (key) {
      var f = world.followers[key];
      if (f === self || !f.pos || !self.pos) return;
      var d = hdist(f.pos, self.pos);
      if (d < 6) pets.push({ f: f, d: d });
    });
    if (world.zombies) {
      world.zombies.forEach(function (z) {
        var d = hdist(z, o.pos);
        if (d < 18 && d < threatD) { threat = z; threatD = d; }
      });
    }
    return { near: near, pets: pets, threat: threat, threatD: threatD };
  };

  // ------------------------------------------------------------------ mood
  Follower.prototype.feel = function (dt, o, ev, around) {
    var m = this.mood, t = this.traits;
    var k = Math.min(1, dt * 0.12);
    // everything drifts back to who she is
    m.joy = lerp(m.joy, 0.55 + t.greet * 0.15 + (t.tags.cheerful ? 0.15 : 0), k);
    m.energy = lerp(m.energy, 0.35 + t.energy * 0.5, k);
    m.fear = lerp(m.fear, 0, k * 2);
    m.anger = lerp(m.anger, 0, k * 2.5);
    m.sad = lerp(m.sad, 0, k * 0.8);
    m.love = lerp(m.love, 0.3 + t.cling * 0.3, k * 0.5);
    // waiting about: bored, then drowsy
    if (this.still > 3) {
      m.bored = clamp(m.bored + dt * (0.03 + t.energy * 0.05), 0, 1);
      m.sleepy = clamp(m.sleepy + dt * (0.006 + (t.tags.sleepy ? 0.03 : 0) +
                                        (1 - t.energy) * 0.01), 0, 1);
    } else {
      m.bored = Math.max(0, m.bored - dt * 0.4);
      m.sleepy = Math.max(0, m.sleepy - dt * 0.15);
    }
    // running with them is the best thing
    if (o.speed > 10) m.energy = clamp(m.energy + dt * 0.04, 0, 1);
    // being near and still with them grows on her
    if (this.pos && hdist(this.pos, o.pos) < t.follow + 1.5 && this.still > 2) {
      m.love = clamp(m.love + dt * 0.01, 0, 1);
    }
    if (around.threat) m.fear = clamp(m.fear + dt * (0.25 - t.brave * 0.25), 0, 1);
    ev.forEach(function (e) {
      if (e === 'hurt') {
        m.fear = clamp(m.fear + 0.35 * (1 - t.brave * 0.6), 0, 1);
        m.anger = clamp(m.anger + 0.25 + t.feisty * 0.4, 0, 1);
        m.joy = clamp(m.joy - 0.15, 0, 1);
      } else if (e === 'heal') {
        m.joy = clamp(m.joy + 0.25, 0, 1); m.fear *= 0.5;
      } else if (e === 'died') {
        m.sad = 1; m.joy = 0.1; m.fear = 0.3;
      } else if (e === 'respawn') {
        m.joy = clamp(m.joy + 0.5, 0, 1); m.sad *= 0.3; m.love = clamp(m.love + 0.2, 0, 1);
      } else if (e === 'kill') {
        m.joy = clamp(m.joy + 0.35, 0, 1); m.energy = clamp(m.energy + 0.2, 0, 1);
        m.anger *= 0.4;
      } else if (e === 'shot') {
        m.fear = clamp(m.fear + 0.05 * (1 - t.brave), 0, 1);
      } else if (e === 'boom') {
        m.fear = clamp(m.fear + 0.3 * (1 - t.brave * 0.7), 0, 1);
      }
    });
  };

  /* Her dominant feeling, for her face and Pixel's antenna. */
  Follower.prototype.feeling = function () {
    var m = this.mood;
    if (this.state === 'sleep') return 'sleepy';
    if (m.sad > 0.45) return 'sad';
    if (m.fear > 0.5) return 'fear';
    if (m.anger > 0.5) return 'anger';
    if (m.sleepy > 0.6) return 'sleepy';
    if (m.love > 0.75) return 'love';
    if (m.joy > 0.72) return 'joy';
    return 'calm';
  };

  // ------------------------------------------------------------- reactions
  /* One-off events: a shot, a kill, a chat line, a bang nearby. */
  Follower.prototype.react = function (kind, data, o) {
    var t = this.traits, sp = this.species.id;
    if (this.state === 'sleep' && kind !== 'chat') {
      this.wake('bang');
      return;
    }
    if (kind === 'shot') {
      this.feel(0, o, ['shot'], { threat: null });
      if (!this.cooled('shot', 5)) return;
      if (t.shy > 0.5 || t.tags.sleepy) this.play('cover_ears');
      else if (t.feisty > 0.4 && Math.random() < 0.6) this.play('shadowbox');
      else if (t.showoff > 0.5 && Math.random() < 0.4) this.play('fistpump');
      else if (Math.random() < 0.3) this.emote('bang', 1);
    } else if (kind === 'kill') {
      this.feel(0, o, ['kill'], { threat: null });
      var streak = data && data.streak || 0;
      var pool = [['cheer', 1 + t.greet + t.energy], ['fistpump', t.brave + t.feisty + t.showoff],
                  ['clap', 0.5 + t.copy], ['heart', t.cling], ['dance', t.play],
                  ['twirl', t.showoff + t.dream]];
      this.play(streak >= 3 ? 'twirl' : weighted(pool), 0.25, true);
      if (streak >= 3) this.emote('sparkle', 6);
    } else if (kind === 'victim') {
      // her owner's victim's pet -- she does not take it well
      this.play('cry', 0.3, true);
    } else if (kind === 'boom') {
      this.feel(0, o, ['boom'], { threat: null });
      if (this.cooled('boom', 3)) {
        this.emote('bang', 1);
        this.play(t.shy > 0.4 ? 'hide' : 'cover_ears', 0, true);
      }
    } else if (kind === 'chat') {
      var text = String((data && data.m) || '').toLowerCase();
      if (text.indexOf(this.name) >= 0 || /\b(pet|good girl|cute)\b/.test(text)) {
        // they said her name
        this.play(Math.random() < 0.5 ? 'wave' : 'heart', 0.3, true);
        this.emote('heart', 2);
        this.mood.love = clamp(this.mood.love + 0.2, 0, 1);
        if (this.state === 'sleep') this.wake('quest');
      } else if (Math.random() < 0.25 + t.chat * 0.7) {
        this.emote(pick(['dots', 'dots', 'note', 'bang', 'quest']), 1);
        if (t.chat > 0.5 && Math.random() < 0.5) this.play('nod', 0.4);
      }
    } else if (kind === 'swing') {
      if (t.feisty > 0.4 && this.cooled('swing', 4)) this.play('shadowbox');
    }
    if (sp === 'pixel' && kind === 'kill') this.emote('bits', 6);
  };

  Follower.prototype.wake = function (why) {
    this.state = 'follow';
    this.stateT = 0;
    this.mood.sleepy = 0;
    this.emote(why || 'bang', 1);
    this.act = null;
    this.play('jump', 0, true);
    this.vy = 9;
    this.grounded = false;
  };

  // ---------------------------------------------------------------- intent
  /* Choose what she is doing.  Called a few times a second, and at once
     when something happens. */
  Follower.prototype.think = function (o, ev, around) {
    var t = this.traits, m = this.mood, self = this;
    var d = hdist(this.pos, o.pos);
    var sp = this.species.id;

    // the big ones first
    if (ev.indexOf('died') >= 0) { this.enter('mourn'); this.play('cry', 0.4, true); return; }
    if (!o.alive) { if (this.state !== 'mourn') this.enter('mourn'); return; }
    if (ev.indexOf('respawn') >= 0) {
      this.enter('follow');
      this.play(d > 14 ? 'cheer' : 'hug', 0.6, true);
      return;
    }
    if (ev.indexOf('hurt') >= 0) {
      if (t.brave > 0.55 || t.feisty > 0.5) { this.enter('guard'); this.play('stomp', 0, true); }
      else if (t.shy > 0.5) { this.enter('hide'); this.play('hide', 0, true); }
      else if (t.cling > 0.5) { this.enter('comfort'); }
      else if (this.cooled('hurtface', 4)) this.emote('bang', 1);
      if (o.health < 30 && this.cooled('worried', 10)) this.play('cry', 1.2);
    }
    if (ev.indexOf('heal') >= 0 && this.cooled('healcheer', 6)) this.play('heart', 0.2);
    if (ev.indexOf('jump') >= 0 && Math.random() < t.copy + t.bounce * 0.5 &&
        this.grounded && d < t.follow + 10) {
      // copying her owner: a hop of her own, a beat behind
      this.queue.push({ jump: Math.random() < 0.5 ? 8 : 11, at: this.time + rand(0.12, 0.3) });
    }
    if (ev.indexOf('bigland') >= 0 && this.cooled('land', 4)) {
      if (t.play > 0.5) this.play('pounce', 0.3);
      else if (t.greet > 0.5) this.play('clap', 0.3);
      else if (t.shy > 0.5) this.play('cover_ears', 0.1);
    }
    // how they move: a dead stop, a slow one, a dash from a standstill
    if (ev.indexOf('halt') >= 0) this.onHalt(o);
    if (ev.indexOf('halt') >= 0 || ev.indexOf('stop') >= 0) this.onStop(o);
    if (ev.indexOf('dash') >= 0) this.onDash(o);
    if (ev.indexOf('uturn') >= 0 && this.whim && this.whim.kind === 'dart') this.whim = null;

    // too far: run, or vanish and reappear at their side
    if (d > TELEPORT_AT || this.stuck > 3.2) { this.teleport(o); return; }

    // somebody new came near her owner -- kept track of whatever she is
    // doing, so that nobody who came by while she sat is news when she gets up
    var fresh = null, nowNear = {};
    around.near.forEach(function (n) {
      if (!self.memory.near[n.key]) fresh = n;
      nowNear[n.key] = true;
    });
    this.memory.near = nowNear;

    switch (this.state) {
      case 'sleep':
        if (o.speed > 1.5 || d > t.follow + 6) this.wake(sp === 'pixel' ? 'bits' : 'bang');
        return;
      case 'sit':
      case 'lie':
        if (o.speed > 1.5 || d > t.follow + 5) {
          this.enter('follow');
          this.play('stretch', 0, true);
          return;
        }
        // somebody new: a shy one is up and behind her owner's legs, the
        // rest say hello from where they are
        if (fresh && t.shy > 0.45 && this.meet(fresh)) return;
        if (fresh && !fresh.enemy && Math.random() < 0.3 + t.greet && this.cooled('greet', 8)) {
          this.play(t.shy > 0.3 ? 'peek' : 'wave', 0.2);
        }
        // up for a cuddle, and back to her spot after
        if (this.stateT > 3 && this.maybeVisit()) {
          this.play('stretch', 0, true);
          return;
        }
        // a while sat there, and some of them flop down on their tummy
        var flop = t.play * 0.6 + t.dream * 0.6 + (t.tags.sleepy ? 0.45 : 0) +
                   (1 - m.energy) * 0.25 + t.bounce * 0.2;
        if (this.state === 'sit' && this.stateT > this.lieAfter) {
          if (Math.random() < flop) { this.enter('lie'); return; }
          this.lieAfter = this.stateT + rand(8, 16);
        }
        if (m.sleepy > 0.55 || this.stateT > 18 + (1 - m.sleepy) * 20) {
          if (Math.random() < 0.5 + (t.tags.sleepy ? 0.4 : 0)) {
            // a lounger dozes off lying down; the rest nod off where they sit
            if (!this.lying && Math.random() < flop * 0.7) this.lying = true;
            this.enter('sleep');
            if (!this.lying) this.play('yawn', 0, true);
          }
        }
        return;
      case 'visit':
        if (o.speed > 2 || this.stateT > 8 ||
            (this.visited && !this.act && this.stateT > this.visitT + 0.8)) {
          this.enter('follow');      // and back out to her spot
        }
        return;
      case 'wander':
        if (o.speed > 2 || this.stateT > 14) { this.enter('follow'); return; }
        if (fresh) this.meet(fresh);
        return;
      case 'mourn':
        return;
      case 'hide':
      case 'guard':
      case 'comfort':
        if (this.stateT > 4 && !around.threat) this.enter('follow');
        return;
      case 'play':
        if (o.speed > 2 || this.stateT > 9) {
          this.enter('follow');
          if (o.speed < 2) this.play('pounce', 0, true);
          return;
        }
        if (fresh) this.meet(fresh);
        return;
      case 'greet':
        if (this.stateT > 3.5 || o.speed > 6) this.enter('follow');
        return;
      case 'petpal':
        if (this.stateT > 5 || o.speed > 3) { this.enter('follow'); return; }
        if (fresh) this.meet(fresh);
        return;
    }

    // following: weigh what else she might be doing
    if (around.threat && around.threatD < 16) {
      if (t.brave > 0.5 && this.cooled('guard', 6)) { this.enter('guard'); return; }
      if (t.shy > 0.5 && this.cooled('hide', 6)) { this.enter('hide'); this.play('peek'); return; }
    }
    if (fresh && this.meet(fresh)) return;
    // another pet: a little meeting
    if (around.pets.length && this.cooled('petpal', 25) && o.speed < 2) {
      var pal = around.pets[0].f;
      this.palF = pal;
      this.enter('petpal');
      var both = (t.play > 0.4 || t.greet > 0.5);
      this.play(both ? pick(['wave', 'dance', 'heart']) : (t.shy > 0.5 ? 'shy' : 'wave'), 0.2);
      return;
    }
    if (o.speed > 2) {
      this.considerWhim(o);
      return;
    }
    // the rest is for when she has got to her spot by them
    if (o.speed < 1.2 && this.spd < 0.5 && (!this.settle || hdist(this.pos, this.settle) < 0.8)) {
      if (this.still > t.patience + (1 - m.sleepy) * 6 && d < t.follow + 3) {
        this.enter('sit');
        return;
      }
      if (this.maybeVisit()) return;
      if (this.still > 3 && Math.random() < t.wander * 0.35 && this.cooled('wander', 9)) {
        var spot = this.findSpot(o, t.range);
        if (spot) { this.wanderTo = spot; this.enter('wander'); return; }
      }
      if (this.still > 2.5 && Math.random() < t.play * 0.3 && this.cooled('play', 14)) {
        this.enter('play');
        if (Math.random() < 0.6) this.spawnToy();
        return;
      }
    }
  };

  /* Somebody new near her owner: she stands guard against an enemy (if
     she has the nerve), hides behind her owner (if she is shy), or goes to
     say hello.  True if she has met them -- or has lately met somebody. */
  Follower.prototype.meet = function (fresh) {
    var t = this.traits;
    if (!this.cooled('greet', 8)) return false;
    this.greetee = fresh;
    if (fresh.enemy && (t.feisty > 0.4 || t.brave > 0.5)) {
      this.enter('guard');
    } else if (t.shy > 0.45 && Math.random() < 0.4 + t.shy * 0.6) {
      this.enter('hide');
      this.play('peek', 0.2);
    } else if (Math.random() < 0.3 + t.greet + t.showoff * 0.5) {
      this.enter('greet');
      this.play(t.showoff > 0.5 && Math.random() < 0.6 ? 'pose'
        : (t.curious > 0.5 && Math.random() < 0.4 ? 'inspect' : 'wave'), 0.15);
    }
    return true;
  };

  /* Up close for a cuddle or a pat on the head, now and then while her
     owner stands about -- the fonder she is, the oftener. */
  Follower.prototype.maybeVisit = function () {
    var t = this.traits, m = this.mood;
    if (this.still < 4 || this.act || m.love < 0.3) return false;
    if (Math.random() >= 0.05 * (t.cling + m.love + t.copy * 0.5)) return false;
    if (!this.cooled('visit', rand(35, 70) * (1.3 - t.cling * 0.5))) return false;
    this.enter('visit');
    return true;
  };

  Follower.prototype.enter = function (state) {
    if (this.state === state) return;
    this.state = state;
    this.stateT = 0;
    if (state === 'sit' || state === 'sleep' || state === 'lie') this.act = null;
    // asleep she stays however she was, sitting or lying
    if (state !== 'sleep') this.lying = state === 'lie';
    if (state === 'sit') this.lieAfter = rand(5, 12);
    if (state === 'visit') this.visited = false;
    if (state !== 'follow') { this.whim = null; this.scamper = false; }
  };

  /* Somewhere nearby worth a look: on the ground, reachable in a straight
     line, out past her usual distance but not too far from her owner. */
  Follower.prototype.findSpot = function (o, range) {
    var phys = this.world.physics();
    var near = this.traits.follow;
    for (var n = 0; n < 6; n++) {
      var a = Math.random() * TAU, r = rand(Math.max(MIN_SPACE + 0.3, near * 0.9), near + range);
      var p = [o.pos[0] + Math.sin(a) * r, 0, o.pos[2] + Math.cos(a) * r];
      var g = this.world.groundAt(p[0], this.pos[1] + 2, p[2], 6);
      if (g === null || Math.abs(g - this.pos[1]) > 1.6) continue;
      if (phys) {
        var dx = p[0] - this.pos[0], dz = p[2] - this.pos[2], len = Math.hypot(dx, dz);
        if (len < 1.5) continue;
        var clear = phys.rayDistance([this.pos[0], this.pos[1] + 0.8, this.pos[2]],
                                     [dx / len, 0, dz / len], len);
        if (clear < len - 0.2) continue;
      }
      p[1] = g;
      return p;
    }
    return null;
  };

  /* A butterfly for a playful pet to chase about. */
  Follower.prototype.spawnToy = function () {
    this.toy = { p: [this.pos[0] + rand(-2, 2), this.pos[1] + 2.4, this.pos[2] + rand(-2, 2)],
                 t: 0, seed: Math.random() * 10,
                 c: pick(['#ffd23a', '#ff8fb8', '#8fd8ff', '#c9b6ff', '#9cff8a']) };
  };

  // ------------------------------------------------------------ the target
  /* Where she wants to be, how she wants to face, how fast to get there.
     out.p is where she wants to be; out.aim, if set, is where she steers
     for on the way (a point ahead of a moving spot, or a crumb round a
     corner); out.speed, if set, is how fast she wants to go, and
     out.arrive whether to ease to a stop at out.p. */
  Follower.prototype.goal = function (o, around, dt) {
    var fwd = [Math.sin(o.yaw), 0, Math.cos(o.yaw)];
    var right = [Math.cos(o.yaw), 0, -Math.sin(o.yaw)];
    var side = this.side;
    var R = this.space();
    var out = { p: null, face: null, urgency: 1, look: null, aim: null, speed: null,
                arrive: true, overshoot: 1 };
    function at(f, s) {
      return [o.pos[0] + fwd[0] * f + right[0] * s * side, o.pos[1],
              o.pos[2] + fwd[2] * f + right[2] * s * side];
    }
    var head = [o.pos[0], o.pos[1] + 5, o.pos[2]];
    switch (this.state) {
      case 'mourn':
        out.p = this.memory.deathAt || o.pos;
        out.look = this.memory.deathAt;
        break;
      case 'wander':
        out.p = this.wanderTo;
        out.urgency = 0.35;
        out.look = this.wanderTo ? [this.wanderTo[0], this.wanderTo[1], this.wanderTo[2]] : null;
        if (this.wanderTo && hdist(this.pos, this.wanderTo) < 1.0 && !this.inspected) {
          this.inspected = true;
          this.play(this.species.id === 'pixel' ? 'scan' : 'inspect', 0, true);
        }
        break;
      case 'hide': {
        // tucked in behind her owner's legs, away from whoever she is hiding from
        var from = (this.greetee && this.greetee.pos) || around.threat;
        if (from) {
          var dx = o.pos[0] - from[0], dz = o.pos[2] - from[2], l = Math.hypot(dx, dz) || 1;
          out.p = [o.pos[0] + dx / l * 2.1, o.pos[1], o.pos[2] + dz / l * 2.1];
          out.look = [from[0], from[1] + 4, from[2]];
        } else {
          out.p = at(-2.0, 0.6);
        }
        out.urgency = 1.4;
        break;
      }
      case 'guard': {
        // between them and trouble, a few paces out
        var foe = around.threat || (this.greetee && this.greetee.pos);
        if (foe) {
          var gx = foe[0] - o.pos[0], gz = foe[2] - o.pos[2], gl = Math.hypot(gx, gz) || 1;
          out.p = [o.pos[0] + gx / gl * 3.6, o.pos[1], o.pos[2] + gz / gl * 3.6];
          out.face = Math.atan2(gx, gz);
          out.look = [foe[0], foe[1] + 3, foe[2]];
          if (this.cooled('guardact', 3)) {
            this.play(this.traits.feisty > 0.4 ? pick(['stomp', 'shadowbox']) : 'flex');
          }
        } else {
          out.p = at(2.4, 2.8);
        }
        out.urgency = 1.3;
        break;
      }
      case 'comfort':
        // right up to them for a hug, then (following again) back out
        out.p = at(1.0, 1.9);
        out.look = head;
        if (hdist(this.pos, out.p) < 1.0 && this.cooled('comforthug', 5)) this.play('hug', 0, true);
        out.urgency = 1.3;
        break;
      case 'visit': {
        // in close on purpose: straight in along her bearing to just
        // outside arm's length, for a cuddle or a pat on the head
        var vx0 = this.pos[0] - o.pos[0], vz0 = this.pos[2] - o.pos[2];
        var vd = Math.hypot(vx0, vz0) || 1;
        out.p = [o.pos[0] + vx0 / vd * 2.1, o.pos[1], o.pos[2] + vz0 / vd * 2.1];
        out.look = head;
        out.face = Math.atan2(-vx0, -vz0);
        out.speed = vd > 2.4 ? 3.5 + Math.min(vd, 10) * 0.45 : 0;
        if (vd < 2.5 && !this.visited) {
          var tt = this.traits;
          this.visited = true;
          this.visitT = this.stateT;
          this.play(weighted([['hug', 0.4 + tt.cling * 1.5], ['patted', 1.2],
                              ['heart', 0.5 + tt.copy * 0.5], ['shy', tt.shy * 1.6],
                              ['giggle', tt.chat * 0.8]]), 0, true);
          this.emote('heart', 2);
          this.mood.love = clamp(this.mood.love + 0.1, 0, 1);
        }
        break;
      }
      case 'greet': {
        var g = this.greetee;
        out.p = at(R * 0.35, R * 0.85);
        if (g) {
          out.look = [g.pos[0], g.pos[1] + 5, g.pos[2]];
          out.face = Math.atan2(g.pos[0] - this.pos[0], g.pos[2] - this.pos[2]);
        }
        break;
      }
      case 'petpal': {
        var pal = this.palF;
        if (pal && pal.pos) {
          var px = pal.pos[0] - this.pos[0], pz = pal.pos[2] - this.pos[2], pl = Math.hypot(px, pz) || 1;
          out.p = pl > 2.6 ? [pal.pos[0] - px / pl * 2.2, this.pos[1], pal.pos[2] - pz / pl * 2.2]
            : this.pos;
          out.face = Math.atan2(px, pz);
          out.look = [pal.pos[0], pal.pos[1] + 2, pal.pos[2]];
        } else {
          out.p = at(-0.5, R);
        }
        out.urgency = 0.6;
        break;
      }
      case 'play': {
        if (this.toy) {
          out.p = [this.toy.p[0], o.pos[1], this.toy.p[2]];
          out.look = this.toy.p;
          out.urgency = 1.1;
        } else {
          // round and round her owner, at a romp's distance: always for a
          // point a little further round from wherever she is, so she runs
          // the ring rather than cutting across it -- and now and then she
          // turns about with a bounce and runs it the other way
          if (this.cooled('romp', rand(2.5, 5))) {
            if (this.stateT > 0.5) this.skip(o, rand(6, 8));
            this.side = -this.side;
          }
          var ra = Math.atan2(this.pos[0] - o.pos[0], this.pos[2] - o.pos[2]) + this.side * 0.6;
          var rr = Math.max(MIN_SPACE + 0.7, R * 0.9) + Math.sin(this.stateT * 1.3) * 0.4;
          out.p = [o.pos[0] + Math.sin(ra) * rr, o.pos[1], o.pos[2] + Math.cos(ra) * rr];
          out.look = head;
          out.urgency = 0.8;
        }
        break;
      }
      case 'sit':
      case 'lie':
      case 'sleep':
        out.p = this.pos;
        out.look = this.state === 'sleep' ? null : head;
        break;
      default:
        this.followGoal(o, out, dt || 0, R);
    }
    // wherever she is going, it is not inside their personal space unless
    // that is the point of it
    if (out.p && o.alive && !CLOSE[this.state] && out.p !== this.pos) {
      var ex = out.p[0] - o.pos[0], ez = out.p[2] - o.pos[2], ed = Math.hypot(ex, ez);
      if (ed < ROUND) {
        if (ed < 1e-3) { ex = this.pos[0] - o.pos[0]; ez = this.pos[2] - o.pos[2]; ed = Math.hypot(ex, ez) || 1; }
        out.p = [o.pos[0] + ex / ed * ROUND, out.p[1], o.pos[2] + ez / ed * ROUND];
        out.aim = null;
      }
    }
    // never stand in front of a gun they are shooting: out to the side of
    // the line of fire, and no nearer them than she would have been
    if (o.holding && this.state !== 'mourn' && out.p && this.inFire(o, out.p, 1.4)) {
      var vx = out.p[0] - o.pos[0], vz = out.p[2] - o.pos[2];
      var along = Math.max(0, vx * fwd[0] + vz * fwd[2]);
      var across = vx * right[0] + vz * right[2];
      var sg = Math.abs(across) > 0.3 ? (across > 0 ? 1 : -1) : side;
      var push = sg * (along * 0.45 + 2.6);
      var safe = [o.pos[0] + fwd[0] * along * 0.45 + right[0] * push, out.p[1],
                  o.pos[2] + fwd[2] * along * 0.45 + right[2] * push];
      var sd = hdist(safe, o.pos);
      if (!CLOSE[this.state] && sd < MIN_SPACE) {
        safe[0] = o.pos[0] + (safe[0] - o.pos[0]) / sd * MIN_SPACE;
        safe[2] = o.pos[2] + (safe[2] - o.pos[2]) / sd * MIN_SPACE;
      }
      out.p = safe;
      out.aim = null;
    }
    // ...nor across the front of it on her way.  In it (they have turned
    // it on her)?  Out sideways, the quickest way.  About to cross it?
    // Round by their side and behind them instead.
    if (o.holding && this.state !== 'mourn' && out.p && out.p !== this.pos) {
      var qx = this.pos[0] - o.pos[0], qz = this.pos[2] - o.pos[2];
      var tx = out.p[0] - o.pos[0], tz = out.p[2] - o.pos[2];
      var qa = qx * fwd[0] + qz * fwd[2], qc = qx * right[0] + qz * right[2];
      var ta = tx * fwd[0] + tz * fwd[2], tc = tx * right[0] + tz * right[2];
      var keep = Math.abs(qc) > 0.3 ? (qc > 0 ? 1 : -1) : side;
      var wx = null, wa = 0, wc = 0;
      if (this.inFire(o, this.pos, 0.6)) {
        wa = qa; wc = keep * (Math.max(0, qa) * 0.45 + 3);
        out.escape = true;
      } else if (qc * tc < 0 && qa + (ta - qa) * (qc / (qc - tc)) > -1.5) {
        wa = -1; wc = keep * Math.max(MIN_SPACE, R * 0.8, Math.abs(qc) + 1);
      } else {
        wx = false;
      }
      if (wx === null) {
        out.aim = [o.pos[0] + fwd[0] * wa + right[0] * wc, out.p[1],
                   o.pos[2] + fwd[2] * wa + right[2] * wc];
        out.arrive = false;
        out.speed = Math.max(out.speed || 0, o.speed + 6);
      }
    }
    // and wherever she is going, she goes round them to get there, not
    // through them -- whatever she is doing, however slowly
    if (o.alive && !CLOSE[this.state] && !out.escape && out.p && out.p !== this.pos) {
      var via = this.roundOwner(o, out.aim || out.p);
      if (via && !(o.holding && this.inFire(o, via, 0.6))) out.aim = via;
    }
    return out;
  };

  /* If the straight way from her to ``p`` cuts through (or all but
     grazes) her owner's personal space, the point to make for instead: out
     on her ring, as far round them as the tangent from where she is (and
     always a step on), the short way round -- so she walks round them
     rather than through them.  Worked out afresh each frame, it walks her
     round the ring until the way is clear.  Null when it already is. */
  Follower.prototype.roundOwner = function (o, p) {
    var ox = o.pos[0], oz = o.pos[2], x = this.pos[0], z = this.pos[2];
    var f = nearestAlong(x, z, p[0], p[2], ox, oz);
    // (nearest them at either end of the way is not through them: where
    // she is, or where she is going, which goal() keeps outside it)
    if (f <= 0 || f >= 1 ||
        Math.hypot(x + (p[0] - x) * f - ox, z + (p[2] - z) * f - oz) >= ROUND + 0.3) {
      this.roundSg = 0;
      return null;
    }
    var px = x - ox, pz = z - oz, rd = Math.hypot(px, pz) || 1e-3;
    // which way round: the short way to where she is going -- or, if that
    // is straight across from her, whichever way she is going round them
    // already (and once she has chosen, she keeps to it)
    var b = Math.atan2(px, pz), delta = wrap(Math.atan2(p[0] - ox, p[2] - oz) - b), sg;
    if (Math.abs(delta) < 2.7) {
      sg = delta > 0 ? 1 : -1;
    } else {
      var swing = pz * this.vel[0] - px * this.vel[2];
      sg = Math.abs(swing) > rd * 1.5 ? (swing > 0 ? 1 : -1) : (this.roundSg || this.side);
    }
    this.roundSg = sg;
    var r = MIN_SPACE + 0.3;
    var a = b + sg * Math.max(0.55, rd > r ? Math.acos(r / rd) : 0);
    var w = this.roundP;
    w[0] = ox + Math.sin(a) * r; w[1] = p[1]; w[2] = oz + Math.cos(a) * r;
    return this.byOwner(o, w);
  };

  /* ``p`` is a point that keeps its place by her owner as they go (a way
     round them, a spot out at their side): on the move, the point she
     should steer at to get there -- their way plus her own way to it --
     rather than to where it was a moment ago.  Changes ``p`` in place. */
  Follower.prototype.byOwner = function (o, p) {
    if (o.speed <= 1.5) return p;
    var x = this.pos[0], z = this.pos[2];
    var wx = p[0] - x, wz = p[2] - z, wl = Math.hypot(wx, wz) || 1e-3;
    var c = clamp(wl * 3, 3, 10) / wl;
    p[0] = x + (o.vel[0] + wx * c) * 0.5;
    p[2] = z + (o.vel[2] + wz * c) * 0.5;
    return p;
  };

  /* How far she keeps from her owner: her own comfortable distance, a
     little nearer when she is frightened or sad, never inside MIN_SPACE. */
  Follower.prototype.space = function () {
    var m = this.mood;
    return Math.max(MIN_SPACE, this.traits.follow * (1 - m.fear * 0.15 - m.sad * 0.08));
  };

  /* Is ``p`` in the line of fire of what her owner is holding (with
     ``margin`` studs to spare either side)? */
  Follower.prototype.inFire = function (o, p, margin) {
    var fx = Math.sin(o.yaw), fz = Math.cos(o.yaw);
    var vx = p[0] - o.pos[0], vz = p[2] - o.pos[2];
    var along = vx * fx + vz * fz, across = vx * fz - vz * fx;
    return along > -0.5 && along < 34 && Math.abs(across) < Math.max(0, along) * 0.45 + margin;
  };

  /* Can she see from ``a`` to ``b`` at about her eye height?  (A wall
     stops it; a kerb she can step up does not.) */
  Follower.prototype.clear = function (a, b) {
    var phys = this.world.physics();
    if (!phys) return true;
    var dx = b[0] - a[0], dz = b[2] - a[2], len = Math.hypot(dx, dz);
    if (len < 0.5) return true;
    return phys.rayDistance([a[0], a[1] + 1.6, a[2]], [dx / len, 0, dz / len], len) >= len - 0.25;
  };

  // ------------------------------------------------------------- following
  /* Where she wants to be while following, into ``out``: somewhere behind
     and to one side of her owner while they are on the move, a spot on her
     ring where she can see them while they stand still.  A whim of her own
     can take the goal over for a while. */
  Follower.prototype.followGoal = function (o, out, dt, R) {
    if (this.whim && this.whimGoal(o, out, dt, R)) return;
    if (o.speed > 1.5) {
      this.settle = null;
      this.trailGoal(o, out, dt, R);
    } else {
      this.besideK = 0;
      this.settleGoal(o, out, dt, R);
    }
    this.route(o, out, dt);
  };

  /* On the move.  Three ideas of where "behind" is pull on her:

       footsteps   that far back along the path they actually took, so she
                   goes round corners after them
       formation   straight back from the way they are heading, off to her
                   side, which swings her wide of their turns
       pursuit     that far out on the line from them to her, which cuts
                   inside every turn

     blended by her persona (cut), and the more so the sharper they turn.
     On top of that she meanders across their path, crosses behind them when
     she changes sides, and gets out of their way if they come back at her.
     Her speed is her own: a pace that drifts about theirs, a slack before
     she bothers to catch up, and a scamper when she has fallen too far
     behind.  She steers for a point ahead of where she wants to be, along
     the way they are going this instant, so she reads their turns rather
     than chasing them. */
  Follower.prototype.trailGoal = function (o, out, dt, R) {
    var t = this.traits, m = this.mood, s = o.speed, w = this.whim;
    var hx = this.heading[0], hz = this.heading[1];
    var rx = hz, rz = -hx;                  // across their path (goal()'s "right")
    var px = this.pos[0] - o.pos[0], pz = this.pos[2] - o.pos[2];
    var pd = Math.hypot(px, pz) || 1;
    var ahead = px * hx + pz * hz, across = px * rx + pz * rz;
    // she has ended up on their other side -- they turned across her, or
    // came by her -- and that is her side now: she does not cut back over
    // in front of them for it (a swap of sides on purpose aside)
    if (Math.abs(across) > 2.5 && (across > 0 ? 1 : -1) !== this.side && this.time > this.swapAt + 4) {
      this.side = -this.side;
      this.sideK = this.side;
    }
    // running alongside them for a while, when she is having the best time
    this.besideK += ((w && w.kind === 'race' ? 1 : 0) - this.besideK) * Math.min(1, dt * 1.5);
    var bk = this.besideK;
    // further back the faster they go
    var k = clamp(this.oSpd / 22, 0, 1.25);
    var gap = lerp(R * (0.85 + 0.5 * k), Math.max(MIN_SPACE, R * 0.85), bk);
    this.sideK += (this.side - this.sideK) * Math.min(1, dt * 0.9);
    var ang = lerp(t.lateral * this.sideK, 1.45 * this.side, bk);
    var ca = Math.cos(ang), sa = Math.sin(ang);
    // footsteps, a little to her side of them
    var T = this.trailPoint(o, gap * ca, this.trailP), td = this.trailDir;
    var tl = gap * sa * 0.6;
    var Tx = T[0] + td[1] * tl, Tz = T[2] - td[0] * tl;
    // formation
    var Fx = o.pos[0] - hx * gap * ca + rx * gap * sa;
    var Fz = o.pos[2] - hz * gap * ca + rz * gap * sa;
    // pursuit
    var Px = o.pos[0] + px / pd * gap, Pz = o.pos[2] + pz / pd * gap;
    // how she takes their turns: the sharper the turn, the more a cutter
    // cuts and a wide one swings
    var sharp = clamp(Math.abs(this.turn) - 0.3, 0, 1.4);
    var cut = clamp(t.cut + sharp * (t.cut > -0.15 ? 0.45 : -0.35), -1, 1);
    var wp = Math.max(0, cut) * (1 - bk), wf = Math.max(0, -cut) * (1 - bk) + bk;
    var wt = 1 - wp - wf;
    var bx = Tx * wt + Fx * wf + Px * wp, bz = Tz * wt + Fz * wf + Pz * wp;
    // she meanders: two slow swings of her own across their path
    var wv = t.weave * (1 - bk * 0.6) * (1.1 + gap * 0.14) *
             (Math.sin(this.time * 0.53 + this.phase[0]) * 0.65 +
              Math.sin(this.time * 1.37 + this.phase[1]) * 0.35);
    bx += rx * wv; bz += rz * wv;
    // never nearer them than her ring
    var ox = bx - o.pos[0], oz = bz - o.pos[2], od = Math.hypot(ox, oz);
    var ring = Math.max(MIN_SPACE, gap * 0.8);
    if (od < ring) {
      if (od < 1e-3) { ox = -hx; oz = -hz; od = 1; }
      bx = o.pos[0] + ox / od * ring; bz = o.pos[2] + oz / od * ring;
    }
    // ahead of them -- they have turned back on her, or set off past her:
    // out of their way to the side she is on, and let them come by.  (Only
    // once they are nearly on her: from further off she simply comes back
    // to them, and steps aside as they close.)
    var yw = w && w.kind === 'dart' ? 0 : clamp((ahead + 2.5 - bk * 4) / 2, 0, 1) *
             clamp((R * 1.8 - pd) / (R * 0.8), 0, 1);
    if (yw > 0) {
      var sg = across >= 0 ? 1 : -1;
      var yl = Math.max(MIN_SPACE, R * 0.85);
      bx += (o.pos[0] - hx * 2.5 + rx * sg * yl - bx) * yw;
      bz += (o.pos[2] - hz * 2.5 + rz * sg * yl - bz) * yw;
    }
    var B = this.goalP;
    B[0] = bx; B[1] = o.pos[1]; B[2] = bz;
    out.p = B;
    out.arrive = false;
    // her pace: a share of theirs that drifts, more for a lively pet
    this.paceT -= dt;
    if (this.paceT <= 0) {
      var spread = 0.07 + t.energy * 0.1 + t.dream * 0.06 + t.play * 0.04;
      this.paceTo = 1 + rand(-spread, spread) - (1 - m.energy) * 0.05;
      this.paceT = rand(1.2, 3.6);
    }
    this.paceK += (this.paceTo - this.paceK) * Math.min(1, dt * 1.2);
    var pace = this.paceK;
    // how far she lets herself fall back before she scampers
    var slack = 2.6 + (1 - t.energy) * 3 + (t.tags.sleepy ? 1.5 : 0);
    if (w && w.kind === 'dawdle') { pace = w.slow; slack = 40; }
    var ex = bx - this.pos[0], ez = bz - this.pos[2];
    var behind = ex * hx + ez * hz;          // how far back of her spot she is
    var off = Math.abs(ex * rx + ez * rz);   // and how far to one side of it
    if (!this.scamper && behind > slack) this.startScamper(o, false);
    var want;
    if (this.scamper) {
      want = s * 1.12 + 6 + t.energy * 6;
      if (behind < 0.6) this.scamper = false;
    } else if (behind > 0) {
      want = s * pace + behind * 0.8 + off * 0.5;
    } else {
      want = s * pace * clamp(1 + behind * 0.2, 0.3, 1) + off * 0.5;
    }
    // (but caught out in front of them, right in their way, she keeps
    // ahead of them while she gets clear, rather than stop under their feet)
    if (ahead > 0.5 && Math.abs(across) < MIN_SPACE - 1) want = Math.max(want, s + 3);
    out.speed = Math.min(MAX_SPEED, want);
    // steer for a point ahead of her spot, along the way they are going
    // this instant...
    var lead = clamp(s * t.anticipate, 1.4, 7);
    var A = this.aimP;
    A[0] = bx + o.vel[0] / s * lead; A[1] = B[1]; A[2] = bz + o.vel[2] / s * lead;
    // ...but never one behind her: she slows and lets her spot come back
    // to her rather than turning round for it
    var fa = (A[0] - this.pos[0]) * hx + (A[2] - this.pos[2]) * hz;
    if (fa < 1.2) { A[0] += hx * (1.2 - fa); A[2] += hz * (1.2 - fa); }
    out.aim = A;
    // a happy pet skips along now and then (Mochi hops anyway)
    if (this.grounded && !this.act && m.joy > 0.62 && this.species.gait !== 'hop' &&
        Math.random() < dt * t.bounce * 0.2) {
      this.skip(o, rand(5, 7));
    }
  };

  /* Stood still: a spot on her ring where she can see them, chosen when
     they stop and kept -- her owner looking about does not send her round
     and round them -- until it stops being a good one (they shuffle off it,
     turn a gun on it) or, now and then, she fancies a change. */
  Follower.prototype.settleGoal = function (o, out, dt, R) {
    var S = this.settle;
    this.settleT += dt;
    if (!S) {
      this.pickSettle(o, R, false);
    } else {
      var d = hdist(S, o.pos);
      if (d < MIN_SPACE || d > R * 1.35 || Math.abs(S[1] - o.pos[1]) > 1.6 ||
          (o.holding && this.inFire(o, S, 1.0))) {
        this.pickSettle(o, R, false);
      } else if (this.settleT > this.settleFor && !this.act && hdist(this.pos, S) < 1) {
        this.pickSettle(o, R, true);
      }
    }
    S = this.settle;
    var gap = hdist(this.pos, S);
    out.p = S;
    out.arrive = true;
    out.overshoot = this.overshoot;
    out.speed = gap > 0.35 ? 3.4 + Math.min(gap, 16) * (0.6 + this.traits.energy * 0.4) : 0;
    out.look = [o.pos[0], o.pos[1] + 5, o.pos[2]];
    out.face = Math.atan2(o.pos[0] - this.pos[0], o.pos[2] - this.pos[2]);
  };

  /* Choose her spot: from where she is, partway round toward where she
     likes to be relative to the way they face -- a show-off well round in
     front, a shy one more at their side -- on her ring, on their level, in
     sight of them and out of any line of fire.  ``nudge`` is a smaller
     change of spot, for a fidget. */
  Follower.prototype.pickSettle = function (o, R, nudge) {
    var t = this.traits;
    var px = this.pos[0] - o.pos[0], pz = this.pos[2] - o.pos[2];
    var b0 = Math.atan2(px, pz);
    var across = px * Math.cos(o.yaw) - pz * Math.sin(o.yaw);
    var sg = Math.abs(across) > 0.5 ? (across > 0 ? 1 : -1) : this.side;
    var b, r;
    if (nudge) {
      b = b0 + rand(-0.45, 0.45);
      r = R * rand(0.96, 1.12);
    } else {
      var pref = o.yaw + sg * clamp(0.95 + t.shy * 0.7 - t.showoff * 0.45 - t.greet * 0.15,
                                    0.45, 1.75);
      b = b0 + clamp(wrap(pref - b0), -1.4, 1.4) * clamp(0.45 + t.greet * 0.3 + t.cling * 0.25, 0, 1);
      r = R * rand(0.98, 1.06);
    }
    // (she may stop a little short of it, coming from nearer in)
    r = Math.max(r, MIN_SPACE + ARRIVE);
    var p = [0, 0, 0];
    var tries = [0, 0.5, -0.5, 1.1, -1.1, 1.8];
    for (var i = 0; i < tries.length; i++) {
      var a = b + sg * tries[i];
      p[0] = o.pos[0] + Math.sin(a) * r; p[2] = o.pos[2] + Math.cos(a) * r;
      if (this.spotOK(o, p)) return this.keepSettle(p);
    }
    // nowhere on her ring will do (a ledge, a corridor): where she stands,
    // if that is a fair way off; further out; and only then nearer in,
    // never inside their bubble
    var here = hdist(this.pos, o.pos);
    if (here >= MIN_SPACE && here <= r * 1.4) {
      p[0] = this.pos[0]; p[2] = this.pos[2];
      if (this.spotOK(o, p)) return this.keepSettle(p);
    }
    for (var rf = r * 1.2; rf <= r * 1.55; rf += r * 0.17) {
      for (var j = 0; j < 3; j++) {
        var af = b + sg * [0, 0.5, -0.5][j];
        p[0] = o.pos[0] + Math.sin(af) * rf; p[2] = o.pos[2] + Math.cos(af) * rf;
        if (this.spotOK(o, p)) return this.keepSettle(p);
      }
    }
    for (var rr = r * 0.85; rr >= BUBBLE; rr -= 0.8) {
      p[0] = o.pos[0] + Math.sin(b) * rr; p[2] = o.pos[2] + Math.cos(b) * rr;
      if (this.spotOK(o, p)) return this.keepSettle(p);
    }
    p[0] = this.pos[0]; p[1] = this.pos[1]; p[2] = this.pos[2];
    return this.keepSettle(p);
  };

  Follower.prototype.keepSettle = function (p) {
    this.settle = p;
    this.settleT = 0;
    this.settleFor = rand(14, 32);
    return p;
  };

  /* A spot she could settle on: on her owner's level, in sight of them,
     and out of any line of fire. */
  Follower.prototype.spotOK = function (o, p) {
    if (o.holding && this.inFire(o, p, 1.2)) return false;
    var g = this.world.groundAt(p[0], o.pos[1] + 2.5, p[2], 6);
    if (g === null || Math.abs(g - o.pos[1]) > 1.6) return false;
    p[1] = g;
    return this.clear(o.pos, p);
  };

  /* Is the way to where she wants to be clear?  A few times a second she
     looks (one ray).  When it is not, she follows her owner's breadcrumbs
     from the one nearest her, skipping on whenever the next is in sight,
     so she goes round the corner after them rather than into the wall --
     and when it is, she cuts straight across. */
  Follower.prototype.route = function (o, out, dt) {
    var P = out.p;
    if (!P || !this.crumbN) { this.blocked = false; return; }
    this.losT -= dt;
    if (this.losT <= 0) {
      this.losT = rand(0.18, 0.3);
      this.blocked = hdist(this.pos, P) > 1.5 && !this.clear(this.pos, P);
      if (!this.blocked) {
        this.via = -1;
      } else if (this.via < 0 || this.via <= this.crumbSeq - this.crumbN) {
        this.via = this.nearestCrumb();
      } else if (this.via < this.crumbSeq && this.clear(this.pos, this.crumb(this.via + 1, this.aimP))) {
        this.via++;
      }
    }
    if (!this.blocked || this.via < 0) return;
    var c = this.crumb(this.via, this.aimP);
    if (hdist(this.pos, c) < 1.6 && this.via < this.crumbSeq) c = this.crumb(++this.via, this.aimP);
    out.aim = c;
    out.arrive = false;
    out.speed = Math.max(out.speed || 0,
                         Math.min(MAX_SPEED, o.speed + 4 + hdist(this.pos, o.pos) * 0.3));
  };

  // ----------------------------------------------------------------- whims
  /* While her owner is on the move she does not only follow: now and then
     something takes her fancy.  Her persona weighs which, and her mood and
     fidgetiness how often:

       sniff    off to something by the wayside, a good sniff, a look round
                for them -- oh! -- and a scamper to catch up with a leap
       dart     a dash past them to a spot ahead, to wait there on her toes
                (never while they hold a gun)
       race     running alongside them when they run
       dawdle   lagging on purpose, looking about, then a gallop to catch up
       hops     a string of happy hops
       swap     across behind them to their other side */
  Follower.prototype.considerWhim = function (o) {
    var t = this.traits, m = this.mood, s = o.speed;
    if (this.whim || this.scamper || this.time < this.whimAt || this.state !== 'follow') return;
    this.whimAt = this.time + rand(3.5, 9) * (1.35 - t.fidget * 0.45 - m.energy * 0.3);
    var kind = weighted([
      ['none', 1.1],
      ['sniff', s < 13 ? 0.25 + t.curious * 1.5 + t.wander * 1.2 + m.bored : 0],
      // (a shy pet keeps behind them, and nobody goes out in front of a gun)
      ['dart', !o.holding && t.shy < 0.5 && s > 3 && s < 15
        ? t.lead * 1.6 + t.play * 0.9 + t.showoff * 0.4 + t.brave * 0.3 + Math.max(0, m.joy - 0.55)
        : 0],
      ['race', s > 12 && t.shy < 0.5 ? t.lead * 1.3 + t.energy * 0.4 + t.play * 0.3 : 0],
      ['dawdle', 0.2 + t.dream * 1.3 + (1 - m.energy) * 0.6 + (t.tags.sleepy ? 0.6 : 0) +
                 t.curious * 0.3],
      ['hops', m.joy > 0.55 ? t.bounce * 1.3 + t.play * 0.4 : 0],
      ['swap', 0.3 + t.curious * 0.4 + t.play * 0.4 + t.weave * 0.3]
    ]);
    if (kind === 'none') return;
    if (kind === 'swap') { this.side = -this.side; this.swapAt = this.time; return; }
    this.startWhim(kind, o);
  };

  Follower.prototype.startWhim = function (kind, o) {
    var t = this.traits;
    var hx = this.heading[0], hz = this.heading[1], rx = hz, rz = -hx;
    var across = (this.pos[0] - o.pos[0]) * rx + (this.pos[2] - o.pos[2]) * rz;
    var sg = Math.abs(across) > 0.5 ? (across > 0 ? 1 : -1) : this.side;
    var w = { kind: kind, phase: 'go', t: 0, p: null };
    if (kind === 'sniff') {
      // something by the wayside: off to her side of their path, a little ahead of her
      var f = rand(1.5, 3.5), l = rand(1.2, 3);
      w.p = [this.pos[0] + hx * f + rx * sg * l, 0, this.pos[2] + hz * f + rz * sg * l];
      if (!this.reachable(w.p, null)) return;
      // a good long sniff while they amble, a quick one while they hurry
      w.dur = (rand(0.7, 1.2) + t.curious * 0.4) * (o.speed > 8 ? 0.65 : 1);
      w.wait = rand(0.35, 0.8);
    } else if (kind === 'dart') {
      // past them, on her side, far enough ahead to get there first
      var ahead = 10 + o.speed * 0.6, lat = Math.max(MIN_SPACE, this.space() * 0.7);
      w.p = [o.pos[0] + hx * ahead + rx * sg * lat, 0, o.pos[2] + hz * ahead + rz * sg * lat];
      if (!this.reachable(w.p, o.pos)) return;
      w.lat = lat;
      w.sg = sg;
      w.hx = hx;
      w.hz = hz;
      if (Math.random() < 0.5) this.skip(o, rand(6, 9));
    } else if (kind === 'race') {
      w.dur = rand(2.5, 5.5);
    } else if (kind === 'dawdle') {
      w.dur = rand(1.6, 3.2);
      w.slow = rand(0.4, 0.62);
    } else if (kind === 'hops') {
      w.n = 2 + ((Math.random() * 3) | 0);
    }
    this.whim = w;
  };

  /* A whim under way.  True when it decides where she goes (a sniff, a dash
     ahead), false when it only colours her following (a dawdle, a run
     alongside, hops, the scamper after a sniff) or is over. */
  Follower.prototype.whimGoal = function (o, out, dt, R) {
    var w = this.whim, s = o.speed, t = this.traits;
    var hx = this.heading[0], hz = this.heading[1];
    w.t += dt;
    if (w.kind === 'sniff') {
      var far = hdist(this.pos, o.pos);
      if (w.phase === 'go') {
        // they have turned her way, and it is in their path: never mind
        var sx = w.p[0] - o.pos[0], sz = w.p[2] - o.pos[2], sa = sx * hx + sz * hz;
        if (sa > 0 && sa < 12 && Math.abs(sx * hz - sz * hx) < MIN_SPACE) {
          this.whim = null;
          return false;
        }
        out.p = w.p;
        out.speed = clamp(s * 0.85, 3.5, 9);
        out.look = w.p;
        if (far > 20) this.sniffLook(w);             // left behind already
        else if (hdist(this.pos, w.p) < 0.7 || w.t > 3) {
          w.phase = 'sniff'; w.t = 0;
          this.play('sniff', 0, true);
        }
        return true;
      }
      if (w.phase === 'sniff') {
        out.p = this.pos;
        out.speed = 0;
        out.look = w.p;
        if (w.t > w.dur || far > 20) this.sniffLook(w);
        return true;
      }
      if (w.phase === 'look') {
        if (w.t < w.wait && far < 30) {
          out.p = this.pos;
          out.speed = 0;
          out.face = Math.atan2(o.pos[0] - this.pos[0], o.pos[2] - this.pos[2]);
          out.look = [o.pos[0], o.pos[1] + 5, o.pos[2]];
          return true;
        }
        this.whimCatch(w, o);
      }
      // catching up: following does the rest; the whim is over once she has
      if (!this.scamper || s < 1.5) this.whim = null;
      return false;
    }
    if (w.kind === 'dart') {
      if (w.phase === 'go') {
        // they have changed course, stopped, broken into a run she will
        // never get ahead of, or all but got there first: never mind
        var ahead = (w.p[0] - o.pos[0]) * hx + (w.p[2] - o.pos[2]) * hz;
        if (ahead < 1.5 || s < 1.5 || s > 16 || w.t > 4 || hx * w.hx + hz * w.hz < 0.9 ||
            hdist(w.p, o.pos) < R) {
          this.whim = null;
          return false;
        }
        out.p = w.p;
        out.speed = MAX_SPEED;
        out.overshoot = this.overshoot;
        // round them wide, not past their elbow: from behind them, out to
        // the side first, level with them, and then on past -- and not flat
        // out until she is by them
        var qx = this.pos[0] - o.pos[0], qz = this.pos[2] - o.pos[2];
        var qa = qx * hx + qz * hz, qc = Math.abs(qx * hz - qz * hx);
        if (qa < 2 && qc < w.lat - 0.5) {
          var A = this.aimP, fwd = qa < -1 ? qa + 2.5 : 3;
          A[0] = o.pos[0] + hx * fwd + hz * w.sg * (w.lat + 0.5);
          A[1] = o.pos[1];
          A[2] = o.pos[2] + hz * fwd - hx * w.sg * (w.lat + 0.5);
          out.aim = this.byOwner(o, A);
          out.arrive = false;
        }
        if (qa < 2 && qa > -4 && hdist(this.pos, o.pos) < w.lat + 2.5) out.speed = s + 8;
        if (hdist(this.pos, w.p) < 1.0) {
          w.phase = 'wait'; w.t = 0;
          this.play(weighted([['tiptoe', 1.2], ['wave', 0.6 + t.greet], ['clap', 0.3 + t.copy],
                              ['pose', t.showoff]]), 0.15);
        }
        return true;
      }
      // waiting for them, facing them, until they come near, or change
      // course -- above all toward her: then following, and getting out of
      // their way, again
      var mx = this.pos[0] - o.pos[0], mz = this.pos[2] - o.pos[2];
      var mine = mx * hx + mz * hz;
      if (mine < 1.0 || s < 1.5 || w.t > 3.5 || hx * w.hx + hz * w.hz < 0.9 ||
          Math.abs(mx * hz - mz * hx) < MIN_SPACE - 0.5 || hdist(this.pos, o.pos) < R) {
        this.whim = null;
        return false;
      }
      out.p = this.pos;
      out.speed = 0;
      out.face = Math.atan2(o.pos[0] - this.pos[0], o.pos[2] - this.pos[2]);
      out.look = [o.pos[0], o.pos[1] + 5, o.pos[2]];
      return true;
    }
    if (w.kind === 'dawdle') {
      if (w.t > w.dur || hdist(this.pos, o.pos) > R * 1.5 + 7) {
        // ...and a gallop to catch up
        this.whim = null;
        this.startScamper(o, true);
        return false;
      }
      if (w.t > (w.lookAt || 0)) {
        // looking about her as she ambles
        w.lookAt = w.t + rand(0.6, 1.2);
        var a = Math.atan2(hx, hz) + rand(-2.2, 2.2);
        this.lookOverride = { p: [this.pos[0] + Math.sin(a) * 6, this.pos[1] + rand(0.5, 3),
                                  this.pos[2] + Math.cos(a) * 6], until: this.time + 0.9 };
      }
      return false;
    }
    if (w.kind === 'race') {
      if (w.t > w.dur || s < 9) this.whim = null;
      return false;
    }
    if (w.kind === 'hops') {
      if (this.grounded && w.t > (w.next || 0)) {
        this.skip(o, rand(5.5, 8));
        w.n--;
        w.next = w.t + rand(0.35, 0.55);
        if (Math.random() < 0.25) this.emote(Math.random() < 0.5 ? 'note' : 'sparkle', 1);
      }
      if (w.n <= 0 || w.t > 4) this.whim = null;
      return false;
    }
    this.whim = null;
    return false;
  };

  /* Done sniffing -- oh!  Where have they got to?  A look round for them,
     head on one side. */
  Follower.prototype.sniffLook = function (w) {
    w.phase = 'look';
    w.t = 0;
    this.act = null;
    this.ownerLook = this.time + 1.0;
    this.tiltTo = (Math.random() < 0.5 ? -1 : 1) * rand(0.18, 0.32);
    this.tiltT = 0.9;
    if (Math.random() < 0.45) this.emote(Math.random() < 0.6 ? 'bang' : 'quest', 1);
  };

  Follower.prototype.whimCatch = function (w, o) {
    w.phase = 'catch';
    w.t = 0;
    this.act = null;
    if (o.speed > 1.5) this.startScamper(o, true);
  };

  /* Off after them flat out -- often, or always if ``leap``, with a
     little leap to start. */
  Follower.prototype.startScamper = function (o, leap) {
    this.scamper = true;
    if (leap || Math.random() < 0.2 + this.traits.bounce * 0.6) this.skip(o, rand(6, 9));
  };

  /* Somewhere she could get to: on the ground at about her height, and in
     sight of her (and of ``from``, if given). */
  Follower.prototype.reachable = function (p, from) {
    var g = this.world.groundAt(p[0], this.pos[1] + 2.5, p[2], 6);
    if (g === null || Math.abs(g - this.pos[1]) > 1.4) return false;
    p[1] = g;
    return this.clear(this.pos, p) && (!from || this.clear(from, p));
  };

  // ------------------------------------------------- how her owner moves
  /* They stopped dead: if she was going at a lick she skids to a stop (a
     clumsy one goes over), and sometimes looks up at them -- what now? */
  Follower.prototype.onHalt = function (o) {
    var t = this.traits;
    if (this.state !== 'follow' || this.spd < 7 || !this.cooled('halt', 2)) return;
    // in the middle of a hop: she skids as she lands
    if (!this.grounded) { this.skidOnLand = true; return; }
    if (t.clumsy > 0.1 && Math.random() < t.clumsy * 2.2) {
      this.play('trip', 0.05, true);
      return;
    }
    if (Math.random() < 0.9) this.startSkid(o);
    if (Math.random() < 0.35 + t.curious * 0.4) {
      this.ownerLook = this.time + 1.2;
      this.tiltTo = (Math.random() < 0.5 ? -1 : 1) * rand(0.18, 0.32);
      this.tiltT = 1.3;
    }
  };

  Follower.prototype.startSkid = function (o) {
    this.skid = rand(0.3, 0.45) * clamp(this.spd / 16, 0.7, 1.3);
    this.play('skid', 0, true);
    this.burst('puff', this.pos, 3);
    // and she swerves as she slides, to her side of them, not into them
    var hx = Math.sin(this.hdg), hz = Math.cos(this.hdg);
    var across = (this.pos[0] - o.pos[0]) * hz - (this.pos[2] - o.pos[2]) * hx;
    var sw = (across >= 0 ? 1 : -1) * 0.5, c = Math.cos(sw), s = Math.sin(sw);
    this.hdg = Math.atan2(hx * c + hz * s, hz * c - hx * s);
  };

  /* They have stopped: what she was up to on the move is over, and after a
     long run a pet without much puff pants. */
  Follower.prototype.onStop = function (o) {
    var mem = this.memory;
    if (this.whim && this.whim.kind !== 'sniff') this.whim = null;
    this.scamper = false;
    if ((mem.runFor || 0) > 12 && this.traits.energy < 0.6 && this.state === 'follow' &&
        this.cooled('pant', 20)) {
      this.play('pant', rand(0.6, 1.1));
    }
    mem.runFor = 0;
  };

  /* They set off at a run from a standstill: the eager ones celebrate --
     a spin, a hop, a fist in the air -- and off they all go after them. */
  Follower.prototype.onDash = function (o) {
    var t = this.traits;
    // (whatever she was doing to pass the time, she drops it)
    if (!IDLE[this.state] || !this.cooled('dash', 5)) return;
    var what = weighted([
      ['none', 0.6 + t.shy + (t.tags.sleepy ? 0.8 : 0)],
      ['zoom_spin', t.play * 1.4 + t.energy * 0.8 + (t.tags.cheerful ? 0.5 : 0) + t.showoff * 0.4],
      ['hop', t.bounce * 1.5],
      ['fistpump', t.feisty * 0.8 + t.showoff * 0.6]
    ]);
    var at = rand(0.05, 0.2);
    if (what === 'zoom_spin') {
      this.play('zoom_spin', at, true);
      this.queue.push({ jump: 7, at: this.time + at });
    } else if (what === 'hop') {
      this.queue.push({ jump: rand(8, 11), at: this.time + at });
    } else if (what === 'fistpump') {
      this.play('fistpump', at);
    }
    if (what !== 'none') this.mood.joy = clamp(this.mood.joy + 0.08, 0, 1);
    this.scamper = true;
  };

  // ------------------------------------------------------------------ body
  Follower.prototype.teleport = function (o) {
    var old = this.pos ? this.pos.slice() : null;
    // back at their side, a little behind them, at her own distance and in
    // sight of them; failing that close in; failing that at their feet
    var p = null, a = o.yaw + this.side * 2.2;
    var radii = [Math.max(MIN_SPACE, this.traits.follow * 0.9), 2.6];
    for (var i = 0; i < radii.length && !p; i++) {
      var q = [o.pos[0] + Math.sin(a) * radii[i], o.pos[1], o.pos[2] + Math.cos(a) * radii[i]];
      var g = this.world.groundAt(q[0], o.pos[1] + 4, q[2], 12);
      if (g !== null && Math.abs(g - o.pos[1]) <= 3 && (i || this.clear(o.pos, q))) {
        q[1] = g;
        p = q;
      }
    }
    if (!p) p = o.pos.slice();
    if (old) this.burst(this.species.id === 'pixel' ? 'bits' : 'puff', old, 10);
    this.pos = p;
    this.vel = [0, 0, 0];
    this.vy = 0;
    this.spd = 0;
    this.grounded = true;
    this.stuck = 0;
    this.skid = 0;
    this.scamper = false;
    this.whim = null;
    this.settle = null;
    this.via = -1;
    this.burst(this.species.id === 'pixel' ? 'bits' : 'puff', p, 12);
    this.emote('sparkle', 3);
    this.yaw = this.hdg = Math.atan2(o.pos[0] - p[0], o.pos[2] - p[2]);
    if (this.state !== 'mourn') this.enter('follow');
    this.play('land', 0, true);
  };

  /* Steer her toward the goal.  She travels on a heading and at a speed of
     her own, each with limits: the heading turns more slowly the faster she
     goes, so she runs in arcs rather than laser lines and a hard turn costs
     her speed; the speed rises and falls at rates her energy sets, and she
     plans to stop a little harder than she can, so an eager pet comes in
     long and settles back.  The last step or two of settling she shuffles,
     without turning round for it. */
  Follower.prototype.move = function (dt, goal, o) {
    var world = this.world, phys = world.physics();
    var t = this.traits, m = this.mood;
    var target = goal.p || o.pos;
    var aim = goal.aim || target;
    var dx = target[0] - this.pos[0], dz = target[2] - this.pos[2];
    var dist = Math.hypot(dx, dz);
    var ax = aim[0] - this.pos[0], az = aim[2] - this.pos[2];
    var aimDist = Math.hypot(ax, az);
    var agile = clamp(t.energy * 0.6 + m.energy * 0.4, 0, 1);
    var accel = this.grounded ? 22 + agile * 34 : 9;
    var brake = this.grounded ? 18 + agile * 20 : 5;
    var want = 0;
    if (goal.speed !== null && goal.speed !== undefined) {
      want = goal.speed;
    } else if (dist > 0.35) {
      // matched to her owner, and faster the further behind she has
      // fallen; a stroll to look at something, or over to another pet,
      // stays a stroll
      var cruise = this.state === 'wander' ? 3.2 : (o.speed > 1.5 ? o.speed : 4.2);
      var hurry = (this.state === 'wander' || this.state === 'petpal') ? 0 : 2.4;
      want = Math.min(MAX_SPEED, cruise * goal.urgency + Math.max(0, dist - 2) * hurry);
      if (this.state === 'wander') want = Math.min(want, 4.5);
    }
    if (goal.arrive !== false) {
      // ease in to the spot
      want = dist <= 0.35 ? 0
        : Math.min(want, Math.sqrt(2 * brake * (goal.overshoot || 1) * (dist - 0.3)) + 0.4);
    }
    if (this.state === 'sit' || this.state === 'sleep' || this.state === 'lie') want = 0;
    var free = want;
    var rooted = this.act && !this.act.upper && !MOBILE[this.act.name];
    if (rooted) want *= 0.15;             // a whole-body action roots her
    if (this.skid > 0) {
      // momentum carries her on: she brakes on her heels and cannot steer
      this.skid -= dt;
      want = 0;
      brake *= 0.8;
      if (this.spd > 4 && Math.random() < dt * 12) this.burst('puff', this.pos, 1);
      // and wherever she has slid to, she finds her spot from there rather
      // than trotting back round them to the one she had in mind
      if (this.skid <= 0) this.settle = null;
    }
    var going = want > 0.6 || this.spd > 1.2;
    this.shuffling = goal.arrive !== false && dist < 1.6 && this.spd < 3 && want < 3 &&
                     this.skid <= 0;
    var vx, vz;
    if (this.shuffling) {
      var sw = Math.min(want, 1.8);
      var ux = dist > 1e-3 ? dx / dist : 0, uz = dist > 1e-3 ? dz / dist : 0;
      vx = this.vel[0] + clamp(ux * sw - this.vel[0], -accel * dt, accel * dt);
      vz = this.vel[2] + clamp(uz * sw - this.vel[2], -accel * dt, accel * dt);
      this.spd = Math.hypot(vx, vz);
      this.hdg = this.yaw;
    } else {
      if (!going) this.hdg = this.yaw;
      var des = aimDist > 1e-3 ? Math.atan2(ax, az) : this.hdg;
      var omega = 2.4 + agile * 2.2 + 7.5 / (1 + this.spd * 0.25);
      if (aimDist < 2) omega *= 2;
      if (!this.grounded) omega *= 0.3;
      if (this.skid > 0) omega = 0;
      // never into her owner: she bends her way round them (unless she is
      // getting out of their line of fire, which comes first, and fast)
      var dodge = goal.escape ? null : this.dodge(o, brake);
      if (dodge !== null) {
        des = dodge;
        omega = Math.max(omega, this.skid > 0 ? 4 : 6);
        // they are bearing down on her (or she on them): whatever she was
        // in the middle of, she breaks off and gets out of the way -- and
        // if they are all but on top of her, with a startled leap aside
        var down = this.state === 'sit' || this.state === 'lie' || this.state === 'sleep';
        if (rooted && this.skid <= 0 && !down) {
          this.act = null;
          want = Math.max(free, 4);
        }
        // (it is them coming at her, so standing still is no answer)
        if (this.meetBy > 2 && !down && this.skid <= 0) want = Math.max(want, 3 + this.meetBy * 0.5);
        if (this.meetIn < 0.3 && this.meetVs > 8 && this.grounded && !down &&
            this.cooled('aside', 1.5)) {
          this.leapAside(o);
        }
      }
      if (goal.escape) omega = Math.max(omega * 1.6, 7);
      var diff = wrap(des - this.hdg);
      // turning right about beside her owner, she turns away from them,
      // not round into their legs
      if (Math.abs(diff) > 2 && this.spd > 2 && o.alive && !CLOSE[this.state]) {
        var rx = o.pos[0] - this.pos[0], rz = o.pos[2] - this.pos[2], rl = Math.hypot(rx, rz);
        var by = (Math.sin(this.hdg) * rz - Math.cos(this.hdg) * rx) / (rl || 1);
        if (rl < 8 && Math.abs(by) > 0.3 && (by > 0) !== (diff > 0)) diff -= (diff > 0 ? 1 : -1) * TAU;
      }
      this.hdg = wrap(this.hdg + clamp(diff, -omega * dt, omega * dt));
      // a hard turn costs her speed; from a standstill she turns, then goes
      var sharp = Math.abs(diff);
      if (sharp > 1.0) want *= Math.max(0.3, 1 - (sharp - 1.0) * 0.55);
      if (sharp > 1.6 && this.spd < 3 && dodge === null) want = 0;
      this.spd = Math.max(0, this.spd + clamp(want - this.spd, -brake * dt, accel * dt));
      vx = Math.sin(this.hdg) * this.spd;
      vz = Math.cos(this.hdg) * this.spd;
    }
    // keep out of people's way -- her owner's most of all, unless she means
    // to be close -- and other pets', and out of the line of fire
    var sep = this.sep, close = CLOSE[this.state];
    sep[0] = 0; sep[1] = 0;
    for (var i = 0; i < world.owners.length; i++) {
      var other = world.owners[i];
      if (!other.alive) continue;
      var mine = other.key === this.key;
      var room = mine ? (close ? 1.7 : BUBBLE) : 2.4;
      var ox = this.pos[0] - other.pos[0], oz = this.pos[2] - other.pos[2], od = Math.hypot(ox, oz);
      if (od < room && od > 1e-3) {
        // her owner's bubble is firm: she backs right out of it
        var push = (room - od) * (mine && !close ? 2 : 1);
        sep[0] += ox / od * push; sep[1] += oz / od * push;
      }
    }
    for (var key in world.followers) {
      var f = world.followers[key];
      if (f === this || !f.pos) continue;
      var fx = this.pos[0] - f.pos[0], fz = this.pos[2] - f.pos[2], fd = Math.hypot(fx, fz);
      if (fd < 1.6 && fd > 1e-3) { sep[0] += fx / fd * (1.6 - fd); sep[1] += fz / fd * (1.6 - fd); }
    }
    if (o.holding && this.state !== 'mourn' && this.inFire(o, this.pos, 0.6)) {
      var gx = Math.sin(o.yaw), gz = Math.cos(o.yaw);
      var gs = (this.pos[0] - o.pos[0]) * gz - (this.pos[2] - o.pos[2]) * gx >= 0 ? 1 : -1;
      sep[0] += gz * gs * 1.2; sep[1] -= gx * gs * 1.2;
    }
    vx += sep[0] * 6; vz += sep[1] * 6;
    // on the ground her feet do as she says; in the air she carries on
    var k = this.grounded ? 1 : Math.min(1, dt * 2.5);
    var nvx = this.vel[0] + (vx - this.vel[0]) * k, nvz = this.vel[2] + (vz - this.vel[2]) * k;
    this.lastAccel = clamp(((nvx - this.vel[0]) * Math.sin(this.yaw) +
                            (nvz - this.vel[2]) * Math.cos(this.yaw)) / Math.max(dt, 1e-3), -60, 60);
    this.vel[0] = nvx;
    this.vel[2] = nvz;
    var speed = Math.hypot(this.vel[0], this.vel[2]);

    // up onto a ledge: straight up the face of it first, then on over the
    // edge once she is above it (and no sliding along it on the way)
    var climbing = !this.grounded && this.ledgeTop !== null && this.ledgeTop !== undefined;
    if (climbing && this.vy < 0 && this.pos[1] < this.ledgeTop - 0.5) climbing = this.ledgeTop = null;
    var rising = climbing && this.pos[1] < this.ledgeTop + 0.2;

    // walls: look ahead at knee height; slide round or hop over
    if (phys && speed > 0.3 && !climbing) {
      var hx = this.vel[0] / speed, hz = this.vel[2] / speed;
      var reach = speed * dt + 0.45;
      var knee = [this.pos[0], this.pos[1] + 0.7, this.pos[2]];
      if (phys.rayDistance(knee, [hx, 0, hz], reach) < reach) {
        // a ledge she can get up?  If where she wants to be is up there,
        // she hops rather than sliding along it
        var top = world.groundAt(this.pos[0] + hx * 1.2, this.pos[1] + 10, this.pos[2] + hz * 1.2, 12);
        var hop = this.grounded && top !== null && top - this.pos[1] < 9.5 && top - this.pos[1] > 0.6;
        var slid = hop && target[1] - this.pos[1] > 0.6;
        // (she leaps toward where she is going, not along the wall)
        var lx = aimDist > 0.5 ? ax / aimDist : hx, lz = aimDist > 0.5 ? az / aimDist : hz;
        if (slid) this.leap(top - this.pos[1], lx, lz, speed);
        for (var n = 0; n < 4 && !slid; n++) {
          var turn = [0.6, -0.6, 1.2, -1.2][n] * (this.side || 1);
          var c = Math.cos(turn), s = Math.sin(turn);
          var nx = hx * c + hz * s, nz = -hx * s + hz * c;
          if (phys.rayDistance(knee, [nx, 0, nz], reach) >= reach) {
            this.vel[0] = nx * speed * 0.85; this.vel[2] = nz * speed * 0.85;
            slid = true;
          }
        }
        if (!slid) {
          // no way round: up it if she can, otherwise stop and think again
          if (hop) this.leap(top - this.pos[1], lx, lz, speed);
          else { this.vel[0] = 0; this.vel[2] = 0; }
        }
        // her own travel goes the way the wall sent her
        this.spd = Math.hypot(this.vel[0], this.vel[2]);
        if (this.spd > 0.05) this.hdg = Math.atan2(this.vel[0], this.vel[2]);
      }
    }
    // where she is going is up on something just ahead: jump up to it
    var rise = target[1] - this.pos[1];
    if (this.grounded && o.grounded && rise > 1.4 && rise < 9.5 && dist < 7 && this.spd > 2) {
      this.jump(Math.sqrt(2 * GRAVITY * (rise + 1)));
    }

    var nx2 = this.pos[0] + this.vel[0] * dt * (rising ? 0.1 : 1);
    var nz2 = this.pos[2] + this.vel[2] * dt * (rising ? 0.1 : 1);
    var ground = world.groundAt(nx2, this.pos[1] + 1.4, nz2, 40);
    if (this.grounded) {
      if ((ground === null || ground < this.pos[1] - 0.9) && rise > -0.9 && this.state !== 'mourn') {
        // a drop, and where she is going is not down there: she stops at the edge
        nx2 = this.pos[0]; nz2 = this.pos[2];
        this.vel[0] = 0; this.vel[2] = 0;
        this.spd = 0;
      } else if (ground === null || ground < this.pos[1] - 0.9) {
        this.grounded = false;            // off the edge, on purpose
        this.vy = 0;
      } else if (ground > this.pos[1] + 1.25) {
        nx2 = this.pos[0]; nz2 = this.pos[2];  // too high a step: blocked
        this.vel[0] *= 0.3; this.vel[2] *= 0.3;
        this.spd *= 0.3;
      } else {
        // step up and down smoothly
        this.pos[1] += (ground - this.pos[1]) * Math.min(1, dt * 18);
      }
    }
    this.pos[0] = nx2;
    this.pos[2] = nz2;
    if (!this.grounded) {
      this.vy -= GRAVITY * dt;
      this.pos[1] += this.vy * dt;
      var below = world.groundAt(this.pos[0], this.pos[1] + 1.4 + Math.max(0, -this.vy * dt), this.pos[2], 60);
      if (below !== null && this.pos[1] <= below && this.vy <= 0) {
        var fell = -this.vy;
        this.pos[1] = below;
        this.vy = 0;
        this.grounded = true;
        this.ledgeTop = null;
        // her ears and hair bounce as she lands
        this.ears[1] -= Math.min(5, fell * 0.2);
        // they stopped dead while she was in the air
        if (this.skidOnLand) {
          this.skidOnLand = false;
          if (o.speed < 2 && this.spd > 5 && this.state === 'follow') this.startSkid(o);
        }
        if (fell > 14) {
          this.play('land', 0, true);
          this.burst('puff', this.pos, 5);
          if (t.clumsy > 0.1 && Math.random() < t.clumsy * 2) this.play('trip', 0.05, true);
        }
      }
    }
    // the void: back to her owner
    var kill = world.killY();
    if (this.pos[1] < kill + 4) this.teleport(o);

    // stuck: wanting to go somewhere and not getting there
    if (want > 3 && speed < 0.6 && dist > 3) this.stuck += dt;
    else this.stuck = Math.max(0, this.stuck - dt * 2);

    // turn to face the way she is going, or what she is facing; a skid
    // keeps her as she was, and lying down she stays put
    var faceTo = null;
    if (this.skid > 0) faceTo = null;
    else if (going && !this.shuffling) faceTo = this.hdg;
    else if (goal.face !== null && goal.face !== undefined) faceTo = goal.face;
    else if (goal.look) faceTo = Math.atan2(goal.look[0] - this.pos[0], goal.look[2] - this.pos[2]);
    if (faceTo !== null && this.state !== 'sleep' && this.state !== 'lie') {
      var dy = wrap(faceTo - this.yaw);
      // standing still she only turns her body when her head cannot reach
      if (!going && Math.abs(dy) < 0.9) dy *= 0.02;
      var rate = going ? 10 : 4;
      var turnBy = clamp(dy, -rate * dt, rate * dt);
      this.yaw = wrap(this.yaw + turnBy);
      this.turnRate = lerp(this.turnRate, turnBy / Math.max(dt, 1e-3), 0.3);
    } else {
      this.turnRate = lerp(this.turnRate, 0, 0.2);
    }
    return Math.hypot(this.vel[0], this.vel[2]);
  };

  /* If the way she is going would take her through her owner's personal
     space before she could stop, the heading that takes her round them
     instead, on the side she is passing anyway; otherwise null.  (A
     repulsion alone cannot stop a pet at full tilt: she has to steer.)
     It is worked out relative to them -- trotting along beside them is not
     closing on them; them stopping dead in front of her is. */
  Follower.prototype.dodge = function (o, brake) {
    if (CLOSE[this.state] || !o.alive) return null;
    var vx = Math.sin(this.hdg) * this.spd - o.vel[0], vz = Math.cos(this.hdg) * this.spd - o.vel[2];
    var vs = Math.hypot(vx, vz);
    if (vs < 2.5) return null;
    var ux = vx / vs, uz = vz / vs;
    var rx = o.pos[0] - this.pos[0], rz = o.pos[2] - this.pos[2], rd = Math.hypot(rx, rz);
    var ahead = rx * ux + rz * uz, room = ROUND;
    if (ahead <= 0 || rd < 1e-3 || ahead > vs * vs / (2 * brake) + room + 1.5) return null;
    var off = rx * uz - rz * ux;            // how wide of them she would pass
    if (Math.abs(off) >= room) return null;
    // how soon they would meet, and the quickest way off that line (for a
    // leap aside, if it comes to that)
    var sg = off > 0.2 ? -1 : (off < -0.2 ? 1 : this.side);
    this.meetIn = Math.max(0, ahead - room) / vs;
    this.meetVs = vs;
    this.meetBy = -(o.vel[0] * rx + o.vel[2] * rz) / rd;   // how fast they come at her
    this.asideX = uz * sg; this.asideZ = -ux * sg;
    var base = Math.atan2(rx, rz), spread = Math.asin(Math.min(1, room / rd));
    var a = base - (off >= 0 ? 1 : -1) * spread;
    if (o.holding) {
      // with a gun out, round the back of them, whichever side that is
      var b = base + (off >= 0 ? 1 : -1) * spread;
      var reach = Math.sqrt(Math.max(0, rd * rd - room * room));
      var fx = Math.sin(o.yaw), fz = Math.cos(o.yaw);
      var px = this.pos[0] - o.pos[0], pz = this.pos[2] - o.pos[2];
      if ((px + Math.sin(b) * reach) * fx + (pz + Math.cos(b) * reach) * fz <
          (px + Math.sin(a) * reach) * fx + (pz + Math.cos(a) * reach) * fz) a = b;
    }
    // ...and back from their frame to a heading of her own
    return Math.atan2(o.vel[0] + Math.sin(a) * vs, o.vel[2] + Math.cos(a) * vs);
  };

  /* Eep!  A hop sideways off the line her owner is coming along -- going
     their way a little, and still some of her own -- so that they go by
     rather than over her.  With a gun out, never into the line of fire:
     the other way, or not at all. */
  Follower.prototype.leapAside = function (o) {
    var up = rand(7, 8.5), air = 2 * up / GRAVITY, land = this.landP;
    for (var sg = 1; sg >= -1; sg -= 2) {
      var vx = this.vel[0] * 0.6 + o.vel[0] * 0.35 + this.asideX * 9 * sg;
      var vz = this.vel[2] * 0.6 + o.vel[2] * 0.35 + this.asideZ * 9 * sg;
      var vl = Math.hypot(vx, vz);
      if (vl > MAX_SPEED) { vx *= MAX_SPEED / vl; vz *= MAX_SPEED / vl; }
      land[0] = this.pos[0] + vx * air; land[2] = this.pos[2] + vz * air;
      if (!o.holding || (!this.inFire(o, land, 1.2) && !this.inFire(o, this.pos, 0.6))) break;
    }
    if (sg < -1) return;
    this.vel[0] = vx; this.vel[2] = vz;
    this.spd = Math.hypot(vx, vz);
    this.hdg = Math.atan2(vx, vz);
    this.jump(up);
    this.act = null;
    this.whim = null;
    if (Math.random() < 0.6) this.emote('bang', 1);
    this.ears[1] += 3;
  };

  /* Up onto a ledge ``rise`` studs high, the way (hx, hz) she is going:
     high enough to clear it and on enough to land on it, not straight up
     and back down in front of it. */
  Follower.prototype.leap = function (rise, hx, hz, speed) {
    this.jump(Math.sqrt(2 * GRAVITY * (rise + 0.9)));
    this.ledgeTop = this.pos[1] + rise;
    var on = Math.max(speed, 4.5);
    this.vel[0] = hx * on; this.vel[2] = hz * on;
    this.spd = on;
    this.hdg = Math.atan2(hx, hz);
  };

  /* A hop of her own as she goes along -- for joy, for a butterfly, to
     copy them -- rather than one she needs to get up onto something: only
     if, should her owner stop dead this moment, it would not carry her into
     them before she could land and steer round them.  (In the air she
     cannot.)  True if she hopped. */
  Follower.prototype.skip = function (o, v) {
    if (!this.grounded) return false;
    var air = 2 * v / GRAVITY;
    var x = this.pos[0], z = this.pos[2];
    var lx = x + this.vel[0] * air, lz = z + this.vel[2] * air;
    var f = nearestAlong(x, z, lx, lz, o.pos[0], o.pos[2]);
    if (o.alive && Math.hypot(x + (lx - x) * f - o.pos[0], z + (lz - z) * f - o.pos[2]) < MIN_SPACE) {
      return false;
    }
    this.jump(v);
    return true;
  };

  Follower.prototype.jump = function (v) {
    if (!this.grounded) return;
    var sp = this.species.id;
    this.vy = Math.min(v, sp === 'pixel' ? 40 : 36);
    this.grounded = false;
    this.jets = sp === 'pixel' && v > 18 ? 0.8 : 0;
    if (sp === 'mochi') this.burst('puff', this.pos, 3);
  };

  // ------------------------------------------------------------------ pose
  Follower.prototype.compose = function (dt, speed, goal, o) {
    var sp = this.species, t = this.traits, m = this.mood;
    var feeling = this.feeling();
    var happy = m.joy > 0.62 && feeling !== 'sad';
    var target;
    // the legs: a gait matched to how fast she is going
    if (this.state === 'sleep') {
      target = Pet.act(this.lying ? 'snooze' : 'sleep', this.time);
    } else if (this.state === 'sit') {
      target = Pet.act('sit', this.stateT);
    } else if (this.state === 'lie') {
      target = Pet.act('lounge', this.stateT);
    } else if (this.state === 'mourn' && speed < 1) {
      target = Pet.act(this.stateT < 3 ? 'cry' : 'sit', this.stateT);
      if (this.stateT >= 3) { target.eyes = 'sad'; target.mouth = 'frown'; target.brows = 'sad'; target.headPitch += 0.3; }
    } else if (!this.grounded) {
      target = Pet.act(sp.gait === 'float' ? 'float' : 'jump', this.time);
      if (sp.gait === 'float') { target.float = 0; target.legL = target.legR = 0.3; }
    } else {
      var gait = Pet.gait(sp, speed, happy);
      if (this.state === 'hide' && speed < 1) gait = 'idle';
      if (feeling === 'sad' && gait === 'walk') gait = 'sad_walk';
      if (this.state === 'wander' && gait === 'walk' && t.shy > 0.5) gait = 'sneak';
      // cadence follows speed, so feet do not skate
      var base = { walk: 3.4, sad_walk: 2.2, sneak: 2.0, skip: 4.0, hop: 4.5, run: 9,
                   float: 4, idle: 1 }[gait] || 3.4;
      this.stride += dt * (gait === 'idle' ? 1 : clamp(speed / base, 0.55, 2.3));
      target = Pet.act(gait, this.stride);
      if (gait === 'hop' && sp.id === 'mochi') {
        // a puff of dust where her feet come down
        var ph = (this.stride * 2.2) % 1;
        if (this.lastHop !== undefined && this.lastHop < 0.7 && ph >= 0.7) this.burst('puff', this.pos, 2);
        this.lastHop = ph;
      }
    }
    // Luna is never quite on the ground
    if (sp.gait === 'float' && this.state !== 'sleep' && this.state !== 'sit') {
      target.float = Math.max(target.float, 0.16 + Math.sin(this.time * 2.1) * 0.05);
    }
    // a one-shot action on top
    if (this.act) {
      this.act.t += dt;
      var ap = Pet.act(this.act.name, this.act.t);
      var i;
      if (this.act.upper && (speed > 1.2 || this.state === 'sit')) {
        // arms and face from the action, legs from the gait
        for (i = 0; i < UPPER_KEYS.length; i++) target[UPPER_KEYS[i]] = ap[UPPER_KEYS[i]];
      } else if (this.state === 'lie') {
        // lying on her tummy, only her face takes part
        for (i = 0; i < FACE_KEYS.length; i++) target[FACE_KEYS[i]] = ap[FACE_KEYS[i]];
      } else {
        ap.float = Math.max(ap.float, target.float || 0);
        target = ap;
      }
      if (this.act.t >= this.act.dur) this.act = null;
    }
    // her face, when the action leaves it to her
    if (target.eyes === 'open' && target.mouth === 'smile' && !target.brows) {
      var face = {
        sleepy: ['sleepy', 'tiny', ''], sad: ['sad', 'frown', 'sad'], fear: ['wide', 'o', 'worry'],
        anger: ['open', 'frown', 'angry'], love: ['happy', 'cat', ''], joy: ['happy', 'grin', ''],
        calm: [sp.eyes || 'open', sp.mouth || 'smile', '']
      }[feeling];
      target.eyes = face[0]; target.mouth = face[1]; target.brows = face[2];
      if (feeling === 'joy' && sp.mouth === 'fang') target.mouth = 'fang';
    }
    target.blush = Math.max(target.blush || 0, m.love * 0.45 +
                            (this.state === 'hide' || this.state === 'greet' ? t.shy * 0.6 : 0));
    // signature features follow her mood
    target.perk = Math.min(target.perk, clamp(0.2 + m.joy * 0.8 - m.sad * 0.7, 0, 1.1));
    if (feeling === 'joy' || feeling === 'love') target.perk = Math.max(target.perk, 0.9);
    var ear = clamp(0.25 + m.joy * 0.7 - m.sad * 0.8 - m.sleepy * 0.5 + m.fear * 0.3, -0.4, 1.1);
    target.earL = Math.min(target.earL, ear) + (this.state === 'wander' ? 0.2 : 0);
    target.earR = Math.min(target.earR, ear - (this.state === 'wander' ? 0.5 : 0));
    // and on a spring: swept back as she sets off, up as she pulls up,
    // trailing in the air and bouncing as she lands
    var es = this.ears;
    var wantE = clamp(-this.lastAccel * 0.012, -0.5, 0.4) - (this.grounded ? 0 : 0.2);
    es[1] += ((wantE - es[0]) * 70 - es[1] * 6) * dt;
    es[0] += es[1] * dt;
    target.earL += es[0];
    target.earR += es[0] * 0.85;
    target.sniff = Math.max(target.sniff || 0, this.state === 'wander' ? 1 : 0);
    target.flame = Math.max(target.flame * 0.5, clamp(0.2 + m.energy * 0.5 + m.anger * 0.9 +
                                                      (speed > 10 ? 0.4 : 0) - m.sad * 0.5, 0, 1.5));
    target.glow = Math.max(target.glow, clamp(0.3 + m.joy * 0.4 + m.love * 0.3, 0, 1));
    target.led = LED[feeling];
    target.jet = this.jets ? this.jets : 0;
    // the head: towards whatever has her attention
    var look = goal.look;
    if (!look && this.state === 'follow' && speed < 1.2) look = [o.pos[0], o.pos[1] + 5, o.pos[2]];
    if (this.ownerLook > this.time) look = [o.pos[0], o.pos[1] + 5, o.pos[2]];
    if (this.lookOverride && this.lookOverride.until > this.time) look = this.lookOverride.p;
    var hy = 0, hp = 0, over = 0;
    if (look) {
      var lx = look[0] - this.pos[0], lz = look[2] - this.pos[2];
      var ly = look[1] - (this.pos[1] + 2.0);
      var raw = wrap(Math.atan2(lx, lz) - this.yaw);
      hy = clamp(raw, -1.05, 1.05);
      // on the move, what her head cannot reach her shoulders turn for:
      // a look back over her shoulder
      if (speed > 1.2) over = clamp((raw - hy) * 0.7, -0.5, 0.5);
      hp = clamp(-Math.atan2(ly, Math.hypot(lx, lz) + 0.01), -0.62, 0.45);
    }
    // lying on her tummy her head can only lift and tip, not turn
    if (this.state === 'lie' || (this.state === 'sleep' && this.lying)) hy *= 0.3;
    var ease = Math.min(1, dt * 6);
    this.head[0] = lerp(this.head[0], hy, ease);
    this.head[1] = lerp(this.head[1], hp, ease);
    this.twistE = lerp(this.twistE, over, ease);
    target.headYaw += this.head[0];
    target.headPitch += this.head[1];
    target.twist += this.twistE;
    // a tilt of the head: curious, or puzzled
    if (this.tiltT > 0) this.tiltT -= dt;
    else this.tiltTo = 0;
    this.tilt = lerp(this.tilt, this.tiltTo, Math.min(1, dt * 5));
    target.headRoll += this.tilt;
    target.lookX += clamp(this.head[0] * 0.6, -0.7, 0.7) + this.glance[0];
    target.lookY += clamp(-this.head[1] * 0.8, -0.6, 0.8) + this.glance[1];
    // blinks
    this.blinkAt -= dt;
    if (this.blinkAt <= 0) {
      this.blinkT = 0;
      this.blinkAt = Math.random() < 0.18 ? 0.25 : rand(1.8, 5) * (feeling === 'sleepy' ? 0.6 : 1);
    }
    if (this.blinkT >= 0) {
      this.blinkT += dt;
      target.blink = this.blinkT < (feeling === 'sleepy' ? 0.3 : 0.12) ? 1 : 0;
      if (this.blinkT > 0.3) this.blinkT = -1;
    }
    this.glanceT -= dt;
    if (this.glanceT <= 0) {
      this.glanceT = rand(0.8, 3);
      this.glance = Math.random() < 0.5 ? [0, 0] : [rand(-0.6, 0.6), rand(-0.3, 0.4)];
    }
    // hair: a spring that lags behind her turns and her starts and stops
    var sw = this.sway;
    var wantX = clamp(-this.lastAccel * 0.012 + speed * 0.012, -0.5, 0.6);
    var wantZ = clamp(-this.turnRate * 0.1, -0.45, 0.45);
    sw[2] += ((wantX - sw[0]) * 60 - sw[2] * 9) * dt;
    sw[3] += ((wantZ - sw[1]) * 60 - sw[3] * 9) * dt;
    sw[0] += sw[2] * dt; sw[1] += sw[3] * dt;
    target.swayX += sw[0];
    target.swayZ += sw[1];
    target.lean += clamp(this.lastAccel * 0.004, -0.12, 0.12);
    // she leans into her turns, the more the faster she is going, and her
    // skirt flares as she starts and stops
    target.roll -= clamp(this.turnRate * speed * 0.006, -0.22, 0.22);
    target.skirt += clamp(Math.abs(this.lastAccel) * 0.006, 0, 0.3);
    // ease from the last pose into this one
    var spin = target.spin;
    this.pose = Pet.blend(this.pose, target, 1 - Math.exp(-dt * 13));
    this.pose.spin = spin;
    this.pose.led = target.led;
    if (this.jets) this.jets = Math.max(0, this.jets - dt * 1.5);
  };

  // ---------------------------------------------------------------- emotes
  var EMOTES = {
    heart:   { shape: 'pet_heart', colors: ['#ff5c93', '#ff9ec0'], life: 1.5, size: 0.5, rise: 1.4 },
    zzz:     { shape: 'pet_zzz', colors: ['#cfe0ff', '#ffffff'], life: 2.0, size: 0.38, rise: 0.9, grow: 0.25, drift: 0.6 },
    bang:    { shape: 'pet_bang', colors: ['#ffd23a', '#ff8a2a'], life: 0.9, size: 0.62, rise: 0.8 },
    quest:   { shape: 'pet_quest', colors: ['#8fd8ff', '#ffffff'], life: 1.1, size: 0.55, rise: 0.6 },
    sweat:   { shape: 'pet_sweat', colors: ['#9fdcff'], life: 0.9, size: 0.3, rise: -0.6, side: 0.55 },
    anger:   { shape: 'pet_anger', colors: ['#ff3b3b', '#ff7a5a'], life: 0.9, size: 0.45, rise: 0.3, side: 0.5 },
    note:    { shape: 'note', colors: ['#ffffff', '#ffe58a'], life: 1.6, size: 0.42, rise: 1.0, drift: 0.8 },
    dots:    { shape: 'pet_dots', colors: ['#ffffff', '#f3f6ff'], life: 1.4, size: 0.62, rise: 0.4 },
    sparkle: { shape: 'star', colors: ['#fff6a8', '#ffd23a'], life: 0.9, size: 0.3, rise: 1.6, spread: 0.9 },
    petals:  { shape: 'flower', colors: ['#ffb8d8', '#ffffff'], life: 1.4, size: 0.28, rise: 0.4, spread: 1.0, gravity: 1.2 },
    stars:   { shape: 'star', colors: ['#e9e2ff', '#c9b6ff'], life: 1.2, size: 0.22, rise: 0.5, spread: 0.7 },
    bits:    { shape: 'pet_pixel', colors: ['#4ff2ff', '#b6fbff'], life: 0.8, size: 0.16, rise: 1.2, spread: 0.7 },
    sparks:  { shape: 'spark', colors: ['#fff3c4', '#ffc23a', '#ff7a1a'], life: 0.6, size: 0.22, rise: 1.4, spread: 1.2, add: true },
    puff:    { shape: 'puff', colors: ['#ffffff', '#d9dde3'], life: 0.6, size: 0.5, rise: 0.4, spread: 1.3, grow: 0.8 }
  };

  Follower.prototype.emote = function (kind, n) {
    var spec = EMOTES[kind];
    var parts = this.world.client.particles;
    if (!spec || !parts || !Settings.particles || !this.pos || !this.visible) return;
    var top = Pet.headTop(this.pos, this.pose);
    n = n || 1;
    for (var i = 0; i < n; i++) {
      var sx = spec.side ? (Math.random() < 0.5 ? -1 : 1) * spec.side : 0;
      var sp = spec.spread || (n > 1 ? 0.5 : 0.12);
      parts.spawn({
        p: [top[0] + sx + rand(-sp, sp) * 0.5, top[1] + 0.25 + rand(0, 0.2), top[2] + rand(-sp, sp) * 0.5],
        v: [rand(-0.2, 0.2) + (spec.drift ? rand(0, spec.drift) : 0), spec.rise * rand(0.8, 1.2),
            rand(-0.2, 0.2)],
        life: spec.life * rand(0.85, 1.15), size: spec.size, grow: spec.grow || 0,
        gravity: spec.gravity || 0, blend: spec.add ? 'add' : 'normal', shape: spec.shape,
        colors: spec.colors, upright: true, wobble: 0.3
      });
    }
  };

  Follower.prototype.burst = function (kind, at, n) {
    var spec = EMOTES[kind];
    var parts = this.world.client.particles;
    if (!spec || !parts || !Settings.particles || !at) return;
    for (var i = 0; i < n; i++) {
      var a = Math.random() * TAU;
      parts.spawn({
        p: [at[0] + Math.sin(a) * 0.4, at[1] + 0.3 + rand(0, 0.6), at[2] + Math.cos(a) * 0.4],
        v: [Math.sin(a) * rand(0.6, 2), rand(0.3, 1.6), Math.cos(a) * rand(0.6, 2)],
        life: spec.life * rand(0.8, 1.2), size: spec.size, grow: spec.grow || 0,
        gravity: spec.gravity || 0, blend: spec.add ? 'add' : 'normal', shape: spec.shape,
        colors: spec.colors, upright: true
      });
    }
  };

  /* The little things she does by herself: Zzz while asleep, notes while
     humming, sparks off Ember when she is fired up, stars under Luna. */
  Follower.prototype.ambient = function (dt, speed) {
    var sp = this.species.id, m = this.mood;
    this.emoteT -= dt;
    if (this.state === 'sleep') {
      if (this.emoteT <= 0) { this.emote('zzz', 1); this.emoteT = rand(1.2, 1.9); }
      return;
    }
    if (this.emoteT <= 0) {
      this.emoteT = rand(5, 12) * (1.2 - this.traits.chat * 0.8);
      var f = this.feeling();
      if (f === 'love') this.emote('heart', 1);
      else if (f === 'sad' && Math.random() < 0.5) this.emote('sweat', 1);
      else if (f === 'anger') this.emote('anger', 1);
      else if (this.traits.chat > 0.5 && Math.random() < 0.6) this.emote(pick(['dots', 'note', 'heart']), 1);
      else if (this.traits.dream > 0.5 && Math.random() < 0.5) this.emote('note', 1);
    }
    if (!Settings.particles || !this.visible) return;
    if (sp === 'ember' && (m.anger > 0.4 || m.energy > 0.75 || speed > 12) && Math.random() < dt * 6) {
      this.burst('sparks', [this.pos[0], this.pos[1] + 1.8, this.pos[2]], 1);
    }
    if (sp === 'luna' && Math.random() < dt * (speed > 1 ? 5 : 1.2)) {
      this.burst('stars', [this.pos[0], this.pos[1] + 0.1, this.pos[2]], 1);
    }
    if (sp === 'pixel' && this.jets > 0.05 && Math.random() < dt * 30) {
      this.burst('sparks', this.pos, 1);
    }
  };

  /* The butterfly: it flits about, she chases it, and when she catches up
     she jumps for it and it gets away. */
  Follower.prototype.stepToy = function (dt, o) {
    var toy = this.toy;
    if (!toy) return;
    toy.t += dt;
    var s = toy.seed;
    var aim = this.pos;
    var fx = Math.sin(toy.t * 0.9 + s) * 2.4, fz = Math.cos(toy.t * 0.7 + s * 2) * 2.4;
    toy.p[0] += ((aim[0] + fx + Math.sin(toy.t * 0.3) * 3) - toy.p[0]) * Math.min(1, dt * 0.8);
    toy.p[2] += ((aim[2] + fz) - toy.p[2]) * Math.min(1, dt * 0.8);
    toy.p[1] = aim[1] + 2.3 + Math.sin(toy.t * 3.1) * 0.5;
    // it flutters off from her owner, so the chase stays out of their way
    var ox = toy.p[0] - o.pos[0], oz = toy.p[2] - o.pos[2], od = Math.hypot(ox, oz);
    var room = BUBBLE + 2.5;
    if (od < room && od > 1e-3) {
      toy.p[0] += ox / od * (room - od) * Math.min(1, dt * 3);
      toy.p[2] += oz / od * (room - od) * Math.min(1, dt * 3);
    }
    if (hdist(this.pos, toy.p) < 1.1 && this.grounded && this.cooled('toyjump', 1.6) &&
        this.skip(o, 13)) {
      this.play('pounce');               // (not over a wave to her owner)
    }
    if (toy.t > 10 || this.state !== 'play') {
      this.toy = null;
      this.emote('heart', 1);
    }
  };

  Follower.prototype.drawToy = function (renderer, time) {
    var toy = this.toy;
    if (!toy) return;
    var flap = Math.sin(time * 26) * 0.9;
    var yaw = Math.atan2(Math.cos(toy.t * 0.9 + toy.seed), -Math.sin(toy.t * 0.7));
    var col = toy.c;
    [-1, 1].forEach(function (s) {
      var a = yaw + s * (0.3 + flap * 0.5);
      renderer.push({ t: 'leaf', p: [toy.p[0] + Math.cos(yaw) * s * 0.14, toy.p[1], toy.p[2] - Math.sin(yaw) * s * 0.14],
                      s: [0.26, 0.34, 0.03], c: col, r: [Math.PI / 2 - 0.3, a, s * 0.9] });
    });
    renderer.push({ t: 'cyl', p: toy.p.slice(), s: [0.04, 0.18, 0.04], c: '#2a2030',
                    r: [Math.PI / 2, yaw, 0] });
  };

  // ------------------------------------------------------------ one frame
  Follower.prototype.update = function (dt, o) {
    this.time += dt;
    this.stateT += dt;
    if (!this.pos) this.teleport(o);
    var ev = this.perceive(o, dt);
    (this.world.inbox[this.key] || []).forEach(function (e) { ev.push(e); });
    var around = this.surroundings(o);
    this.feel(dt, o, ev, around);
    // things queued for a moment from now
    var now = this.time, later = [], self = this;
    this.queue.forEach(function (q) {
      if (q.at > now) { later.push(q); return; }
      if (q.jump) self.skip(o, q.jump);
      else if (q.emote) self.emote(q.emote, q.n);
      else self.play(q.name, 0, q.force);
    });
    this.queue = later;
    this.thinkT -= dt;
    if (ev.length || this.thinkT <= 0) {
      this.think(o, ev, around);
      this.thinkT = rand(0.2, 0.4);
    }
    // waiting about, once she is at her spot: the idle repertoire
    if (o.speed < 1.2 && this.state === 'follow' && !this.act && !this.whim && this.spd < 1.2 &&
        (!this.settle || hdist(this.pos, this.settle) < 1)) {
      this.idleIn -= dt * (0.5 + this.traits.fidget + this.mood.bored * 0.8);
      if (this.idleIn <= 0) {
        this.idleIn = rand(3, 7);
        this.play(weighted(idlePool(this)));
      }
    }
    // sitting: the things she can do without getting up
    if (this.state === 'sit' && !this.act) {
      this.idleIn -= dt * (0.4 + this.traits.fidget * 0.6);
      if (this.idleIn <= 0) {
        this.idleIn = rand(4, 9);
        var seat = idlePool(this).filter(function (a) { return UPPER[a[0]]; });
        seat.push(['wave', 0.4 + this.traits.greet], ['nod', 0.5]);
        this.play(weighted(seat));
      }
    }
    // lying on her tummy: what she can do with just her face
    if (this.state === 'lie' && !this.act) {
      this.idleIn -= dt * (0.4 + this.traits.fidget * 0.6);
      if (this.idleIn <= 0) {
        var tl = this.traits;
        this.idleIn = rand(3, 7);
        this.play(weighted([['hum', 0.4 + tl.dream * 2], ['giggle', 0.3 + tl.chat + tl.shy * 0.5],
                            ['heart', 0.3 + tl.cling], ['sparkle', 0.3], ['think', tl.curious],
                            ['yawn', 0.2 + this.mood.sleepy * 2]]));
      }
    }
    // a glance at the camera, now and then, for her owner
    var cam = this.world.camera;
    if (this.key === 'me' && cam && this.state === 'follow' && !this.act && this.visible &&
        this.cooled('fourthwall', rand(35, 70))) {
      var cx = cam.eye[0] - this.pos[0], cz = cam.eye[2] - this.pos[2];
      if (Math.hypot(cx, cz) < 24) {
        this.lookOverride = { p: cam.eye.slice(), until: this.time + 2.2 };
        this.play(Math.random() < 0.6 ? 'wave' : 'heart', 0.4);
      }
    }
    // as she goes along she glances up at her owner, now and then with a
    // tilt of the head -- the fonder of them, the oftener
    if (this.state === 'follow' && !this.act) {
      this.glanceUp -= dt;
      if (this.glanceUp <= 0) {
        var tr = this.traits;
        this.glanceUp = rand(2.2, 6.5) * (1.4 - tr.cling * 0.4 - tr.copy * 0.3 - this.mood.love * 0.3);
        this.ownerLook = this.time + rand(0.5, 1.1);
        if (Math.random() < 0.3 + tr.curious * 0.35) {
          this.tiltTo = (Math.random() < 0.5 ? -1 : 1) * rand(0.14, 0.3);
          this.tiltT = rand(0.6, 1.2);
        }
      }
    }
    // clumsy on the run (a clumsy pet, that is: the rest keep their feet)
    if (o.speed > 12 && this.grounded && this.traits.clumsy > 0.1 &&
        Math.random() < dt * this.traits.clumsy * 0.25 && this.cooled('trip', 20)) {
      this.play('trip', 0, true);
    }
    var goal = this.goal(o, around, dt);
    var speed = this.move(dt, goal, o);
    if (this.state === 'wander' && !this.act && this.inspected && this.stateT > 6) {
      this.inspected = false;
      this.enter('follow');
    }
    if (this.state !== 'wander') this.inspected = false;
    this.stepToy(dt, o);
    this.compose(dt, speed, goal, o);
    this.ambient(dt, speed);
    this.speed = speed;
  };

  Follower.prototype.draw = function (renderer, time, camera) {
    if (!this.pos) return;
    var d = camera ? Math.hypot(camera.eye[0] - this.pos[0], camera.eye[2] - this.pos[2]) : 0;
    this.visible = d < DRAW_RANGE;
    if (!this.visible) return;
    var parts = Pet.build(this.pet, { position: this.pos, yaw: this.yaw, pose: this.pose,
                                      time: this.time });
    for (var i = 0; i < parts.length; i++) renderer.push(parts[i]);
    this.drawToy(renderer, time);
    // her shadow, small and soft, shrinking as she leaves the ground
    var phys = this.world.physics();
    if (phys) {
      var drop = phys.rayDistance([this.pos[0], this.pos[1] + 0.3, this.pos[2]], [0, -1, 0], 30);
      if (drop < 30) {
        var lift = drop + (this.pose.float || 0) + (this.pose.bob || 0);
        var k = Math.max(0.35, 1 - lift * 0.12);
        renderer.pushRaw('cyl', this.pos[0], this.pos[1] + 0.3 - drop + 0.05, this.pos[2], 0, 0, 0,
                         1.6 * k, 0.05, 1.35 * k, [0.1, 0.12, 0.14], 0.3 * k, 0, 0, 0.9, null);
      }
    }
  };

  // ================================================================ world
  function PetWorld(client) {
    this.client = client;
    this.clock = 0;
    this.shots = {};            // owner key -> clock at their last shot
    this.followers = {};
    this.owners = [];
    this.inbox = {};
    this.camera = null;
    this.zombies = null;
  }

  PetWorld.prototype.physics = function () { return this.client.physics || null; };

  PetWorld.prototype.killY = function () {
    return (this.client.map && this.client.map.kill_y) || -60;
  };

  /* The floor under (x, z), looking down from y; null when there is none
     within ``reach``. */
  PetWorld.prototype.groundAt = function (x, y, z, reach) {
    var phys = this.physics();
    if (!phys) return 0;
    var d = phys.rayDistance([x, y, z], [0, -1, 0], reach || 30);
    return d >= (reach || 30) ? null : y - d;
  };

  /* Has ``key`` fired in the last LIVE_FIRE seconds? */
  PetWorld.prototype.firing = function (key) {
    var at = this.shots[key];
    return at !== undefined && this.clock - at < LIVE_FIRE;
  };

  /* Everyone in the world, as an owner record pets can read.  ``holding``
     is a gun out and in use (shot lately), the only time the line of fire
     matters to a pet. */
  PetWorld.prototype.gather = function (dt) {
    var client = this.client, out = [];
    var me = client.local;
    var arena = client.arena;
    if (me && client.myId && !(arena && arena.noPet(client.myId))) {
      var weapon = client.currentWeapon ? client.currentWeapon() : null;
      out.push({
        key: 'me', id: client.myId, name: (global.BH && BH.user && BH.user.name) || '',
        pet: client.avatar && client.avatar.pet, pos: me.pos, yaw: me.yaw,
        speed: Math.hypot(me.vel[0], me.vel[2]), vel: me.vel, grounded: !!me.grounded,
        alive: !!me.alive, health: me.health === undefined ? 100 : me.health,
        team: client.myTeam || '', holding: !!(weapon && !client.stowed) && this.firing('me')
      });
    }
    var self = this;
    Object.keys(client.players).forEach(function (id) {
      var p = client.players[id];
      // a pet at a hider's heels would give the hider away
      if (arena && arena.noPet(p.id)) return;
      var track = self.tracks[id] || (self.tracks[id] = { last: p.pos.slice(), vel: [0, 0, 0] });
      if (dt > 0) {
        var k = Math.min(1, dt * 8);
        for (var a = 0; a < 3; a++) {
          track.vel[a] = lerp(track.vel[a], (p.pos[a] - track.last[a]) / dt, k);
        }
      }
      track.last = p.pos.slice();
      var hot = p.avatar && p.avatar.hotbar && p.avatar.hotbar[p.slot];
      out.push({
        key: String(id), id: p.id, name: p.name, pet: p.avatar && p.avatar.pet,
        pos: p.pos, yaw: p.yaw, speed: Math.hypot(track.vel[0], track.vel[2]), vel: track.vel,
        grounded: p.anim !== 'jump' && p.anim !== 'fall', alive: !!p.alive,
        health: p.health === undefined ? 100 : p.health, team: p.team || '',
        holding: !!hot && self.firing(String(id))
      });
    });
    return out;
  };

  PetWorld.prototype.frame = function (dt, time, camera) {
    var renderer = this.client.renderer;
    this.tracks = this.tracks || {};
    this.clock += dt;
    if (!global.Pet || !Settings.showPets) {
      this.followers = {};
      return;
    }
    this.camera = camera;
    this.owners = this.gather(dt);
    var survival = this.client.survival;
    if (survival && survival.zombies) {
      var zs = [];
      Object.keys(survival.zombies).forEach(function (id) {
        var z = survival.zombies[id];
        if (z && z.pos && z.hp > 0) zs.push(z.pos);
      });
      this.zombies = zs;
    } else {
      this.zombies = null;
    }
    var seen = {}, self = this;
    this.owners.forEach(function (o) {
      if (!o.pet || !o.pet.species) return;
      seen[o.key] = true;
      var f = self.followers[o.key];
      var sig = JSON.stringify([o.pet.species, o.pet.colors, o.pet.tags, o.pet.name,
                                Object.keys(o.pet.items || {})]);
      if (!f) {
        f = self.followers[o.key] = new Follower(self, o.key, o.pet);
        f.sig = sig;
      } else if (f.sig !== sig) {
        f.setPet(o.pet);
        f.sig = sig;
      }
    });
    Object.keys(this.followers).forEach(function (key) {
      if (!seen[key]) delete self.followers[key];
    });
    var step = Math.min(dt, 0.05);
    this.owners.forEach(function (o) {
      var f = self.followers[o.key];
      if (!f) return;
      f.update(step, o);
      f.draw(renderer, time, camera);
    });
    this.inbox = {};
  };

  /* Something happened: route it to the pets it concerns. */
  PetWorld.prototype.keyFor = function (id) {
    if (id === undefined || id === null) return null;
    return id === this.client.myId ? 'me' : String(id);
  };

  PetWorld.prototype.notify = function (kind, data) {
    if (!Settings.showPets) return;
    var self = this, client = this.client;
    data = data || {};
    function owner(key) {
      return self.owners.filter(function (o) { return o.key === key; })[0] || null;
    }
    function tell(key, what, payload) {
      var f = self.followers[key];
      if (!f) return;
      if (what === 'event') { (self.inbox[key] = self.inbox[key] || []).push(payload); return; }
      var o = owner(key);
      if (o) f.react(what, payload, o);
    }
    if (kind === 'kill') {
      tell(this.keyFor(data.kid), 'kill', data);
      if (data.kid !== data.vid) tell(this.keyFor(data.vid), 'victim', data);
    } else if (kind === 'shot') {
      this.shots[this.keyFor(data.id)] = this.clock;
      tell(this.keyFor(data.id), 'shot', data);
    } else if (kind === 'swing') {
      tell(this.keyFor(data.id), 'swing', data);
    } else if (kind === 'chat') {
      var key = null;
      if (global.BH && BH.user && data.from === BH.user.name) key = 'me';
      Object.keys(client.players).forEach(function (id) {
        if (client.players[id].name === data.from) key = String(id);
      });
      if (key) tell(key, 'chat', data);
    } else if (kind === 'boom' && data.p) {
      Object.keys(this.followers).forEach(function (k) {
        var f = self.followers[k];
        if (f.pos && Math.hypot(f.pos[0] - data.p[0], f.pos[1] - data.p[1], f.pos[2] - data.p[2]) < 22) {
          tell(k, 'boom', data);
        }
      });
    }
  };

  global.PetWorld = PetWorld;
  global.PetFollower = Follower;
  PetWorld.traitsOf = traitsOf;
})(window);
