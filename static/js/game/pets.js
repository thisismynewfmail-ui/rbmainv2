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
   three behaviours bolted together. */
(function (global) {
  'use strict';

  var TAU = Math.PI * 2;
  var GRAVITY = 62;
  var MAX_SPEED = 28;
  var TELEPORT_AT = 46;
  var DRAW_RANGE = 170;

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

  // ------------------------------------------------------------- persona
  /* Who she is, as numbers.  Every pet starts from BASE; each persona tag
     adds its leanings.  The follower reads these when it weighs what to do. */
  var BASE = {
    follow: 3.0,     // how far from her owner she is comfortable
    lead: 0,         // runs ahead when they run
    wander: 0.15,    // how readily she goes off to look at something
    range: 5,        // how far she goes when she does
    fidget: 0.5,     // how often she does something while waiting
    patience: 9,     // seconds of stillness before she sits down
    bounce: 0.25,    // hops and skips
    brave: 0.25, shy: 0.15, chat: 0.15, clumsy: 0.02, showoff: 0.15,
    cling: 0.25, play: 0.2, dream: 0.15, copy: 0.25, greet: 0.4, curious: 0.25,
    energy: 0.5, feisty: 0
  };
  var PERSONA = {
    cheerful:  { greet: 0.45, bounce: 0.3, energy: 0.15, fidget: 0.15 },
    shy:       { shy: 0.8, greet: -0.35, follow: -0.7, showoff: -0.2, chat: -0.1 },
    curious:   { wander: 0.5, curious: 0.7, range: 4, follow: 0.6 },
    loyal:     { copy: 0.65, follow: -0.8, cling: 0.3, wander: -0.1, patience: 4 },
    sleepy:    { patience: -6, energy: -0.3, fidget: -0.25 },
    energetic: { energy: 0.45, lead: 0.75, bounce: 0.5, fidget: 0.45, patience: 6 },
    feisty:    { feisty: 0.8, brave: 0.35, energy: 0.2 },
    dreamy:    { dream: 0.75, energy: -0.1, fidget: 0.1 },
    playful:   { play: 0.75, bounce: 0.3, fidget: 0.2 },
    brave:     { brave: 0.75, shy: -0.2 },
    clingy:    { cling: 0.85, follow: -1.0, wander: -0.15, range: -2 },
    showoff:   { showoff: 0.8, greet: 0.3 },
    chatty:    { chat: 0.8, greet: 0.2 },
    clumsy:    { clumsy: 0.2 }
  };

  function traitsOf(tags) {
    var t = {};
    Object.keys(BASE).forEach(function (k) { t[k] = BASE[k]; });
    (tags || []).forEach(function (tag) {
      var add = PERSONA[tag];
      if (!add) return;
      Object.keys(add).forEach(function (k) { t[k] += add[k]; });
    });
    t.follow = clamp(t.follow, 1.6, 4.4);
    t.patience = clamp(t.patience, 2.5, 20);
    t.range = clamp(t.range, 2.5, 10);
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
    this.setPet(pet);
  }

  Follower.prototype.setPet = function (pet) {
    this.pet = pet;
    this.species = Pet.species(pet);
    this.traits = traitsOf(pet.tags);
    this.name = (pet.name || this.species.name).toLowerCase();
    this.mood.energy = clamp(0.35 + this.traits.energy * 0.5, 0, 1);
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
    if (o.speed > 1.2 || air) this.still = 0;
    else this.still += dt;
    return ev;
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
    // being close and still with them grows on her
    if (this.pos && hdist(this.pos, o.pos) < 4 && this.still > 2) {
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
        this.grounded && d < 10) {
      // copying her owner: a hop of her own, a beat behind
      this.queue.push({ jump: Math.random() < 0.5 ? 8 : 11, at: this.time + rand(0.12, 0.3) });
    }
    if (ev.indexOf('bigland') >= 0 && this.cooled('land', 4)) {
      if (t.play > 0.5) this.play('pounce', 0.3);
      else if (t.greet > 0.5) this.play('clap', 0.3);
      else if (t.shy > 0.5) this.play('cover_ears', 0.1);
    }

    // too far: run, or vanish and reappear at their side
    if (d > TELEPORT_AT || this.stuck > 3.2) { this.teleport(o); return; }

    switch (this.state) {
      case 'sleep':
        if (o.speed > 1.5 || d > t.follow + 6) this.wake(sp === 'pixel' ? 'bits' : 'bang');
        return;
      case 'sit':
        if (o.speed > 1.5 || d > t.follow + 5) {
          this.enter('follow');
          this.play('stretch', 0, true);
          return;
        }
        if (m.sleepy > 0.55 || this.stateT > 18 + (1 - m.sleepy) * 20) {
          if (Math.random() < 0.5 + (t.tags.sleepy ? 0.4 : 0)) {
            this.enter('sleep');
            this.play('yawn', 0, true);
          }
        }
        return;
      case 'wander':
        if (o.speed > 2 || this.stateT > 14) { this.enter('follow'); return; }
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
        }
        return;
      case 'greet':
        if (this.stateT > 3.5 || o.speed > 6) this.enter('follow');
        return;
      case 'petpal':
        if (this.stateT > 5 || o.speed > 3) this.enter('follow');
        return;
    }

    // following: weigh what else she might be doing
    if (around.threat && around.threatD < 16) {
      if (t.brave > 0.5 && this.cooled('guard', 6)) { this.enter('guard'); return; }
      if (t.shy > 0.5 && this.cooled('hide', 6)) { this.enter('hide'); this.play('peek'); return; }
    }
    // somebody new came near her owner
    var fresh = null;
    around.near.forEach(function (n) {
      if (!self.memory.near[n.key]) fresh = n;
    });
    var nowNear = {};
    around.near.forEach(function (n) { nowNear[n.key] = true; });
    this.memory.near = nowNear;
    if (fresh && this.cooled('greet', 8)) {
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
      return;
    }
    // another pet: a little meeting
    if (around.pets.length && this.cooled('petpal', 25) && o.speed < 2) {
      var pal = around.pets[0].f;
      this.palF = pal;
      this.enter('petpal');
      var both = (t.play > 0.4 || t.greet > 0.5);
      this.play(both ? pick(['wave', 'dance', 'heart']) : (t.shy > 0.5 ? 'shy' : 'wave'), 0.2);
      return;
    }
    if (o.speed < 1.2) {
      if (this.still > t.patience + (1 - m.sleepy) * 6 && d < t.follow + 3) {
        this.enter('sit');
        return;
      }
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

  Follower.prototype.enter = function (state) {
    if (this.state === state) return;
    this.state = state;
    this.stateT = 0;
    if (state === 'sit' || state === 'sleep') this.act = null;
  };

  /* Somewhere nearby worth a look: on the ground, reachable in a straight
     line, not too far from her owner. */
  Follower.prototype.findSpot = function (o, range) {
    var phys = this.world.physics();
    for (var n = 0; n < 6; n++) {
      var a = Math.random() * TAU, r = rand(range * 0.5, range);
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
  /* Where she wants to be, how she wants to face, how fast to get there. */
  Follower.prototype.goal = function (o, around) {
    var t = this.traits;
    var fwd = [Math.sin(o.yaw), 0, Math.cos(o.yaw)];
    var right = [Math.cos(o.yaw), 0, -Math.sin(o.yaw)];
    var side = this.side;
    var R = t.follow;
    var out = { p: null, face: null, urgency: 1, look: null };
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
        // behind her owner, away from whoever she is hiding from
        var from = (this.greetee && this.greetee.pos) || around.threat;
        if (from) {
          var dx = o.pos[0] - from[0], dz = o.pos[2] - from[2], l = Math.hypot(dx, dz) || 1;
          out.p = [o.pos[0] + dx / l * 1.7, o.pos[1], o.pos[2] + dz / l * 1.7];
          out.look = [from[0], from[1] + 4, from[2]];
        } else {
          out.p = at(-1.6, 0.5);
        }
        out.urgency = 1.4;
        break;
      }
      case 'guard': {
        var foe = around.threat || (this.greetee && this.greetee.pos);
        if (foe) {
          var gx = foe[0] - o.pos[0], gz = foe[2] - o.pos[2], gl = Math.hypot(gx, gz) || 1;
          out.p = [o.pos[0] + gx / gl * 2.4, o.pos[1], o.pos[2] + gz / gl * 2.4];
          out.face = Math.atan2(gx, gz);
          out.look = [foe[0], foe[1] + 3, foe[2]];
          if (this.cooled('guardact', 3)) {
            this.play(this.traits.feisty > 0.4 ? pick(['stomp', 'shadowbox']) : 'flex');
          }
        } else {
          out.p = at(1.6, 1.2);
        }
        out.urgency = 1.3;
        break;
      }
      case 'comfort':
        out.p = at(0.9, 1.0);
        out.look = head;
        if (hdist(this.pos, out.p) < 1.2 && this.cooled('comforthug', 5)) this.play('hug', 0, true);
        out.urgency = 1.3;
        break;
      case 'greet': {
        var g = this.greetee;
        out.p = at(0.8, R * 0.8);
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
          // round and round her owner
          var a = this.stateT * 1.1 * this.side + this.side;
          out.p = [o.pos[0] + Math.sin(o.yaw + a) * 2.8, o.pos[1], o.pos[2] + Math.cos(o.yaw + a) * 2.8];
          out.look = head;
          out.urgency = 0.8;
        }
        break;
      }
      case 'sit':
      case 'sleep':
        out.p = this.pos;
        out.look = this.state === 'sit' ? head : null;
        break;
      default: {
        if (o.speed > 12 && t.lead > 0.5) {
          // she is having the best time: out in front of them
          out.p = at(3.2, 1.4);
        } else if (o.speed > 1.5) {
          // trotting along at their side, a little behind; the faster they
          // go, the further back she falls
          var lag = clamp(o.speed / 22, 0, 1);
          out.p = at(-0.6 - lag * 2.2, R * 0.75);
        } else {
          // they have stopped: she comes round where she can see them
          out.p = at(R * 0.55, R * 0.8);
          out.look = head;
          out.face = Math.atan2(o.pos[0] - this.pos[0], o.pos[2] - this.pos[2]);
        }
      }
    }
    // never stand in front of a gun
    if (o.holding && this.state !== 'mourn' && out.p) {
      var vx = out.p[0] - o.pos[0], vz = out.p[2] - o.pos[2];
      var along = vx * fwd[0] + vz * fwd[2];
      var across = vx * right[0] + vz * right[2];
      if (along > 0 && along < 14 && Math.abs(across) < along * 0.45 + 0.8) {
        var push = (across >= 0 ? 1 : -1) * (along * 0.45 + 1.6);
        out.p = [o.pos[0] + fwd[0] * along * 0.4 + right[0] * push, out.p[1],
                 o.pos[2] + fwd[2] * along * 0.4 + right[2] * push];
      }
    }
    return out;
  };

  // ------------------------------------------------------------------ body
  Follower.prototype.teleport = function (o) {
    var old = this.pos ? this.pos.slice() : null;
    var a = o.yaw + this.side * 2.2;
    var p = [o.pos[0] + Math.sin(a) * 2.6, o.pos[1] + 0.5, o.pos[2] + Math.cos(a) * 2.6];
    var g = this.world.groundAt(p[0], o.pos[1] + 4, p[2], 12);
    if (g === null || Math.abs(g - o.pos[1]) > 3) { p = o.pos.slice(); g = o.pos[1]; }
    p[1] = g;
    if (old) this.burst(this.species.id === 'pixel' ? 'bits' : 'puff', old, 10);
    this.pos = p;
    this.vel = [0, 0, 0];
    this.vy = 0;
    this.grounded = true;
    this.stuck = 0;
    this.burst(this.species.id === 'pixel' ? 'bits' : 'puff', p, 12);
    this.emote('sparkle', 3);
    this.yaw = Math.atan2(o.pos[0] - p[0], o.pos[2] - p[2]);
    if (this.state !== 'mourn') this.enter('follow');
    this.play('land', 0, true);
  };

  Follower.prototype.move = function (dt, goal, o) {
    var world = this.world, phys = world.physics();
    var t = this.traits;
    var target = goal.p || o.pos;
    var dx = target[0] - this.pos[0], dz = target[2] - this.pos[2];
    var dist = Math.hypot(dx, dz);
    // how fast she wants to go: matched to her owner when following, and
    // faster the further behind she has fallen
    var want = 0;
    if (dist > 0.35) {
      var cruise = this.state === 'wander' ? 3.2 : (o.speed > 1.5 ? o.speed : 4.2);
      // catching up is for falling behind her owner; a stroll to look at
      // something, or over to another pet, stays a stroll
      var hurry = (this.state === 'wander' || this.state === 'petpal') ? 0 : 2.4;
      want = Math.min(MAX_SPEED, cruise * goal.urgency + Math.max(0, dist - 2) * hurry);
      if (this.state === 'wander') want = Math.min(want, 4.5);
      want = Math.min(want, dist * 4.5);     // ease in to the spot
      if (this.state === 'sit' || this.state === 'sleep') want = 0;
    }
    if (this.act && !this.act.upper && this.act.name !== 'jump' && this.act.name !== 'pounce') {
      want *= 0.15;                       // a whole-body action roots her
    }
    var dir = dist > 1e-3 ? [dx / dist, dz / dist] : [0, 0];
    // keep out of other people's way
    var sep = [0, 0];
    world.owners.forEach(function (other) {
      if (!other.alive) return;
      var ox = this.pos[0] - other.pos[0], oz = this.pos[2] - other.pos[2], od = Math.hypot(ox, oz);
      if (od < 1.7 && od > 1e-3) { sep[0] += ox / od * (1.7 - od); sep[1] += oz / od * (1.7 - od); }
    }, this);
    Object.keys(world.followers).forEach(function (key) {
      var f = world.followers[key];
      if (f === this || !f.pos) return;
      var ox = this.pos[0] - f.pos[0], oz = this.pos[2] - f.pos[2], od = Math.hypot(ox, oz);
      if (od < 1.3 && od > 1e-3) { sep[0] += ox / od * (1.3 - od); sep[1] += oz / od * (1.3 - od); }
    }, this);
    var vx = dir[0] * want + sep[0] * 6, vz = dir[1] * want + sep[1] * 6;
    // accelerate rather than snap, so starts and stops have weight
    var acc = this.grounded ? 46 : 14;
    var ax = clamp(vx - this.vel[0], -acc * dt, acc * dt);
    var az = clamp(vz - this.vel[2], -acc * dt, acc * dt);
    this.lastAccel = (ax * Math.sin(this.yaw) + az * Math.cos(this.yaw)) / Math.max(dt, 1e-3);
    this.vel[0] += ax;
    this.vel[2] += az;
    var speed = Math.hypot(this.vel[0], this.vel[2]);

    // walls: look ahead at knee height; slide round or hop over
    if (phys && speed > 0.3) {
      var hx = this.vel[0] / speed, hz = this.vel[2] / speed;
      var reach = speed * dt + 0.45;
      var knee = [this.pos[0], this.pos[1] + 0.7, this.pos[2]];
      if (phys.rayDistance(knee, [hx, 0, hz], reach) < reach) {
        var slid = false;
        for (var k = 0; k < 4 && !slid; k++) {
          var turn = [0.6, -0.6, 1.2, -1.2][k] * (this.side || 1);
          var c = Math.cos(turn), s = Math.sin(turn);
          var nx = hx * c + hz * s, nz = -hx * s + hz * c;
          if (phys.rayDistance(knee, [nx, 0, nz], reach) >= reach) {
            this.vel[0] = nx * speed * 0.85; this.vel[2] = nz * speed * 0.85;
            slid = true;
          }
        }
        if (!slid) {
          // a ledge she can get up?  Hop.  Otherwise stop and think again.
          var top = world.groundAt(this.pos[0] + hx * 1.2, this.pos[1] + 10, this.pos[2] + hz * 1.2, 12);
          if (this.grounded && top !== null && top - this.pos[1] < 9.5 && top - this.pos[1] > 0.6) {
            this.jump(Math.sqrt(2 * GRAVITY * (top - this.pos[1] + 0.9)));
          } else {
            this.vel[0] = 0; this.vel[2] = 0;
          }
        }
      }
    }
    // her owner is up on something: jump to them
    if (this.grounded && o.grounded && o.pos[1] - this.pos[1] > 1.4 && dist < 7 &&
        o.pos[1] - this.pos[1] < 9.5) {
      this.jump(Math.sqrt(2 * GRAVITY * (o.pos[1] - this.pos[1] + 1)));
    }

    var nx2 = this.pos[0] + this.vel[0] * dt, nz2 = this.pos[2] + this.vel[2] * dt;
    var ground = world.groundAt(nx2, this.pos[1] + 1.4, nz2, 40);
    if (this.grounded) {
      if (ground === null || ground < this.pos[1] - 0.9) {
        this.grounded = false;            // walked off an edge
        this.vy = 0;
      } else if (ground > this.pos[1] + 1.25) {
        nx2 = this.pos[0]; nz2 = this.pos[2];  // too high a step: blocked
        this.vel[0] *= 0.3; this.vel[2] *= 0.3;
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

    // turn to face where she is going, or what she is facing
    var faceTo = null;
    if (speed > 1.2) faceTo = Math.atan2(this.vel[0], this.vel[2]);
    else if (goal.face !== null && goal.face !== undefined) faceTo = goal.face;
    else if (goal.look) faceTo = Math.atan2(goal.look[0] - this.pos[0], goal.look[2] - this.pos[2]);
    if (faceTo !== null && this.state !== 'sleep') {
      var dy = wrap(faceTo - this.yaw);
      // standing still she only turns her body when her head cannot reach
      if (speed < 1.2 && Math.abs(dy) < 0.9) dy *= 0.02;
      var rate = speed > 1.2 ? 9 : 4;
      var turnBy = clamp(dy, -rate * dt, rate * dt);
      this.yaw = wrap(this.yaw + turnBy);
      this.turnRate = lerp(this.turnRate, turnBy / Math.max(dt, 1e-3), 0.3);
    } else {
      this.turnRate = lerp(this.turnRate, 0, 0.2);
    }
    return speed;
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
      target = Pet.act('sleep', this.time);
    } else if (this.state === 'sit') {
      target = Pet.act('sit', this.stateT);
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
      if (this.act.upper && (speed > 1.2 || this.state === 'sit')) {
        // arms and face from the action, legs from the gait
        ['armL', 'armR', 'armLZ', 'armRZ', 'headYaw', 'headPitch', 'headRoll', 'eyes',
         'mouth', 'brows', 'blush', 'glow', 'flame', 'perk', 'earL', 'earR', 'sniff']
          .forEach(function (k) { target[k] = ap[k]; });
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
    target.sniff = Math.max(target.sniff || 0, this.state === 'wander' ? 1 : 0);
    target.flame = Math.max(target.flame * 0.5, clamp(0.2 + m.energy * 0.5 + m.anger * 0.9 +
                                                      (speed > 10 ? 0.4 : 0) - m.sad * 0.5, 0, 1.5));
    target.glow = Math.max(target.glow, clamp(0.3 + m.joy * 0.4 + m.love * 0.3, 0, 1));
    target.led = LED[feeling];
    target.jet = this.jets ? this.jets : 0;
    // the head: towards whatever has her attention
    var look = goal.look;
    if (!look && this.state === 'follow' && speed < 1.2) look = [o.pos[0], o.pos[1] + 5, o.pos[2]];
    if (this.lookOverride && this.lookOverride.until > this.time) look = this.lookOverride.p;
    var hy = 0, hp = 0;
    if (look) {
      var lx = look[0] - this.pos[0], lz = look[2] - this.pos[2];
      var ly = look[1] - (this.pos[1] + 2.0);
      hy = clamp(wrap(Math.atan2(lx, lz) - this.yaw), -1.05, 1.05);
      hp = clamp(-Math.atan2(ly, Math.hypot(lx, lz) + 0.01), -0.62, 0.45);
    }
    var ease = Math.min(1, dt * 6);
    this.head[0] = lerp(this.head[0], hy, ease);
    this.head[1] = lerp(this.head[1], hp, ease);
    target.headYaw += this.head[0];
    target.headPitch += this.head[1];
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
  Follower.prototype.stepToy = function (dt) {
    var toy = this.toy;
    if (!toy) return;
    toy.t += dt;
    var s = toy.seed;
    var aim = this.pos;
    var fx = Math.sin(toy.t * 0.9 + s) * 2.4, fz = Math.cos(toy.t * 0.7 + s * 2) * 2.4;
    toy.p[0] += ((aim[0] + fx + Math.sin(toy.t * 0.3) * 3) - toy.p[0]) * Math.min(1, dt * 0.8);
    toy.p[2] += ((aim[2] + fz) - toy.p[2]) * Math.min(1, dt * 0.8);
    toy.p[1] = aim[1] + 2.3 + Math.sin(toy.t * 3.1) * 0.5;
    if (hdist(this.pos, toy.p) < 1.1 && this.grounded && this.cooled('toyjump', 1.6)) {
      this.jump(13);
      this.play('pounce', 0, true);
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
      if (q.jump) self.jump(q.jump);
      else if (q.emote) self.emote(q.emote, q.n);
      else self.play(q.name, 0, q.force);
    });
    this.queue = later;
    this.thinkT -= dt;
    if (ev.length || this.thinkT <= 0) {
      this.think(o, ev, around);
      this.thinkT = rand(0.2, 0.4);
    }
    // waiting about: the idle repertoire
    if (o.speed < 1.2 && this.state === 'follow' && !this.act) {
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
    // clumsy on the run
    if (o.speed > 12 && this.grounded && Math.random() < dt * this.traits.clumsy * 0.25 &&
        this.cooled('trip', 20)) {
      this.play('trip', 0, true);
    }
    var goal = this.goal(o, around);
    var speed = this.move(dt, goal, o);
    if (this.state === 'wander' && !this.act && this.inspected && this.stateT > 6) {
      this.inspected = false;
      this.enter('follow');
    }
    if (this.state !== 'wander') this.inspected = false;
    this.stepToy(dt);
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

  /* Everyone in the world, as an owner record pets can read. */
  PetWorld.prototype.gather = function (dt) {
    var client = this.client, out = [];
    var me = client.local;
    if (me && client.myId) {
      var weapon = client.currentWeapon ? client.currentWeapon() : null;
      out.push({
        key: 'me', id: client.myId, name: (global.BH && BH.user && BH.user.name) || '',
        pet: client.avatar && client.avatar.pet, pos: me.pos, yaw: me.yaw,
        speed: Math.hypot(me.vel[0], me.vel[2]), vel: me.vel, grounded: !!me.grounded,
        alive: !!me.alive, health: me.health === undefined ? 100 : me.health,
        team: client.myTeam || '', holding: !!(weapon && !client.stowed)
      });
    }
    var self = this;
    Object.keys(client.players).forEach(function (id) {
      var p = client.players[id];
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
        health: p.health === undefined ? 100 : p.health, team: p.team || '', holding: !!hot
      });
    });
    return out;
  };

  PetWorld.prototype.frame = function (dt, time, camera) {
    var renderer = this.client.renderer;
    this.tracks = this.tracks || {};
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
