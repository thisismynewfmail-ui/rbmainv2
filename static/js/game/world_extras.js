/* Per-world dynamic objects: CTF flags, the payload cart, and every piece of
   Burger Tycoon's plot furniture (claim pads, buy buttons, collectors). */
(function (global) {
  'use strict';

  function WorldExtras(client) {
    this.client = client;
    this.mode = client.world.mode;
    this.flags = {};
    this.cart = null;
    this.plots = [];
    this.upgrades = [];
    this.builtGeometry = {};
    this.animations = [];
    this.interactTarget = null;
  }

  var TEAM_COLOR = { red: '#c4281c', blue: '#0d69ac' };

  // --------------------------------------------------------------------- CTF
  WorldExtras.prototype.setFlags = function (flags) {
    flags = flags || {};
    // Remember the moment each flag hit the ground.  The server tells us the
    // state, not when it changed, and the fall has to start from somewhere.
    this.droppedAt = this.droppedAt || {};
    var now = (typeof performance !== 'undefined' ? performance.now() : Date.now()) / 1000;
    var self = this;
    Object.keys(flags).forEach(function (team) {
      var was = self.flags[team];
      var is = flags[team];
      if (!is) return;
      if (is.state === 'dropped' && (!was || was.state !== 'dropped')) {
        self.droppedAt[team] = now;
      } else if (is.state !== 'dropped') {
        delete self.droppedAt[team];
      }
    });
    this.flags = flags;
  };

  /* A flag on the ground.

     It falls over when it lands -- the pole swings down over about three
     quarters of a second and rebounds before settling, the way a dropped
     pole actually behaves -- and then lies there rippling.  Round it, a disc
     drains from full to nothing over the return timer, so how long you have
     to get to it is something you can read from across the courtyard rather
     than something you have to have been counting. */
  WorldExtras.prototype.drawDroppedFlag = function (renderer, flag, colour, time) {
    var p = flag.p;
    var rgb = GLX.mat.hexToRgb(colour);
    var yaw = flag.yaw || 0;
    var since = 0;
    if (this.droppedAt && this.droppedAt[flag.team] !== undefined) {
      var now = (typeof performance !== 'undefined' ? performance.now() : Date.now()) / 1000;
      since = now - this.droppedAt[flag.team];
    } else {
      since = 10;                       // joined mid-drop: already settled
    }
    // The fall of a pole hinged at its foot: barely moving for the first
    // moment, then over it goes.  Easing the other way -- fast first, slow
    // into the ground -- is what most drop animations do and it reads as a
    // pole being lowered rather than one falling.  It lands, rebounds a
    // little, and rocks itself still.
    var FALL = 0.85;                    // seconds from upright to flat
    var FLAT = 1.32;                    // radians: lying on the ground
    var fall = Math.min(1, since / FALL);
    var eased = fall * fall;
    var settle = fall >= 1
      ? -Math.exp(-(since - FALL) * 6.0) * Math.sin((since - FALL) * 20) * 0.14
      : 0;
    var tilt = Math.min(FLAT, eased * FLAT + settle);

    var hold = flag.hold || 45;
    var left = flag.left === undefined ? hold : flag.left;
    var fraction = Math.max(0, Math.min(1, left / Math.max(1, hold)));
    var urgent = left <= 10;
    var beat = urgent ? 6.5 : 2.2;
    var pulse = 0.5 + Math.sin(time * beat) * 0.5;

    // the pole, hinged at its foot
    var poleLen = 8.0;
    var cx = Math.sin(yaw), cz = Math.cos(yaw);
    var lean = Math.sin(tilt) * poleLen * 0.5;
    var rise = Math.cos(tilt) * poleLen * 0.5;
    renderer.pushRaw('cyl', p[0] + cx * lean, p[1] + 0.5 + rise, p[2] + cz * lean,
                     Math.cos(yaw) * tilt, yaw, -Math.sin(yaw) * tilt,
                     0.5, poleLen, 0.5,
                     GLX.mat.hexToRgb('#d8dde2'), 1, 0, 1, 0, null);
    // the cloth, bunched at the head of the pole and rippling where it lies
    var hx = p[0] + cx * Math.sin(tilt) * poleLen * 0.86;
    var hz = p[2] + cz * Math.sin(tilt) * poleLen * 0.86;
    var hy = p[1] + 0.5 + Math.cos(tilt) * poleLen * 0.86;
    for (var i = 0; i < 3; i++) {
      var ripple = Math.sin(time * 2.4 - i * 0.9) * 0.16 * eased;
      renderer.pushRaw('box',
                       hx - cx * i * 1.15, hy + 0.5 + ripple * 0.6 + (1 - eased) * 1.4,
                       hz - cz * i * 1.15,
                       ripple, yaw, 0,
                       3.2 - i * 0.5, 1.5, 0.22, rgb, 1, 0, 0, 0.3, null);
    }

    // The return clock: a disc draining inside a fixed outline, drawn at the
    // radius you have to be inside to touch the flag.  So it is two things
    // at once -- how long is left, and where to stand -- and it is kept
    // faint, because a solid pool of team colour on the ground is the
    // loudest thing on the field and the flag itself is the point.
    var reach = 18.0;                   // across: about the reach to touch it
    renderer.pushRaw('cyl', p[0], p[1] + 0.22, p[2], 0, 0, 0,
                     reach + 1.4, 0.2, reach + 1.4, rgb, 0.2, 0, 2, 0.5, null);
    renderer.pushRaw('cyl', p[0], p[1] + 0.34, p[2], 0, 0, 0,
                     reach * fraction, 0.24, reach * fraction, rgb,
                     urgent ? 0.34 + pulse * 0.4 : 0.42, 0, 2, 0.6, null);
    // and a column so it can be found from the other side of the field.  It
    // starts above head height: the countdown tag hangs under it, and a
    // column drawn through the middle of that tag is a column you read the
    // timer through.
    for (var k = 0; k < 4; k++) {
      renderer.pushRaw('box', p[0], p[1] + 9.5 + k * 6, p[2], 0, time * 0.5, 0,
                       1.7 - k * 0.3, 5.4, 1.7 - k * 0.3, rgb,
                       (0.2 - k * 0.04) * (urgent ? 0.6 + pulse * 0.8 : 1),
                       0, 2, 0.9, null);
    }
    if (this.client.settings.showNames) {
      renderer.queueTag('flagdrop' + flag.team,
                        flag.team.toUpperCase() + ' FLAG',
                        urgent ? '#ffd95e' : colour,
                        'returns in ' + Math.ceil(left) + 's',
                        [p[0], p[1] + 4.8, p[2]], 1.3);
    }
  };

  /* A carrier is the most important thing on the map for both teams, and on a
     world this size you will not spot one by looking.  The beam is drawn in
     the carrier's own colours, is visible to everybody, and fades with height
     so it reads as a signal rather than a wall. */
  WorldExtras.prototype.drawCarrier = function (renderer, flag, time) {
    var carrier = this.client.players[flag.carrier];
    var mine = this.client.myId === flag.carrier;
    var pos = mine ? this.client.local.pos : (carrier && carrier.pos);
    if (!pos) return;
    var them = mine ? this.client.myTeam
                    : (carrier && carrier.team) || this.enemyOf(flag.team);
    var colour = GLX.mat.hexToRgb(TEAM_COLOR[them] || '#f5c518');
    for (var i = 0; i < 5; i++) {
      renderer.pushRaw('box', pos[0], pos[1] + 9 + i * 7, pos[2],
                       0, time * 0.7, 0, 2.6 - i * 0.35, 6.4, 2.6 - i * 0.35,
                       colour, 0.34 - i * 0.05, 0, 2, 0.85, null);
    }
    renderer.pushRaw('cyl', pos[0], pos[1] + 0.3, pos[2], 0, 0, 0,
                     11, 0.3, 11, colour, 0.34, 0, 2, 0.8, null);
  };

  WorldExtras.prototype.enemyOf = function (team) {
    return team === 'red' ? 'blue' : 'red';
  };

  /* While your own flag is out, your team falls back to the outposts.  These
     mark where that is, on your side only -- the enemy already knows. */
  WorldExtras.prototype.drawOutposts = function (renderer, state, time) {
    var lockdown = state && state.lockdown;
    var team = this.client.myTeam;
    if (!lockdown || !lockdown[team]) return;
    var markers = (this.client.map && this.client.map.markers) || {};
    var pads = markers['outpost_' + team];
    if (!pads || !pads.length) return;
    var colour = GLX.mat.hexToRgb(TEAM_COLOR[team] || '#f5c518');
    var pulse = 0.5 + Math.sin(time * 2.4) * 0.18;
    for (var i = 0; i < pads.length; i++) {
      var p = pads[i].p;
      renderer.pushRaw('cyl', p[0], p[1] - 0.6, p[2], 0, 0, 0,
                       9 * pulse, 0.3, 9 * pulse, colour, 0.5, 0, 2, 0.8, null);
      renderer.pushRaw('box', p[0], p[1] + 16, p[2], 0, time * 0.5, 0,
                       1.6, 30, 1.6, colour, 0.16, 0, 2, 0.9, null);
    }
  };

  WorldExtras.prototype.drawFlags = function (renderer, time) {
    var self = this;
    Object.keys(this.flags).forEach(function (team) {
      var flag = self.flags[team];
      if (!flag) return;
      var colour = TEAM_COLOR[team] || '#f5c518';
      var p = flag.p;
      var carried = flag.state === 'carried';
      var wave = Math.sin(time * 3 + p[0] * 0.2) * 0.12;
      if (flag.state === 'dropped') {
        self.drawDroppedFlag(renderer, flag, colour, time);
        if (flag.home) {
          var beat = 0.85 + Math.sin(time * 2.2) * 0.12;
          renderer.pushRaw('cyl', flag.home[0], flag.home[1] - 1.1, flag.home[2],
                           0, 0, 0, 13 * beat, 0.3, 13 * beat,
                           GLX.mat.hexToRgb(colour), 0.45, 0, 2, 0.7, null);
        }
        return;
      }
      if (!carried) {
        renderer.pushRaw('cyl', p[0], p[1] + 2.4, p[2], 0, 0, 0, 0.4, 7.0, 0.4,
                         GLX.mat.hexToRgb('#d8dde2'), 1, 0, 1, 0, null);
      }
      renderer.pushRaw('box', p[0] + Math.sin(time * 2) * 0.1, p[1] + 5.0,
                       p[2] + Math.cos(time * 2) * 0.1, wave, 0, 0,
                       3.4, 2.2, 0.16, GLX.mat.hexToRgb(colour), 1, 0, 0, 0.25, null);
      renderer.pushRaw('box', p[0], p[1] + 5.0, p[2], wave, 0, 0,
                       1.2, 1.2, 0.22, GLX.mat.hexToRgb('#ffffff'), 1, 0, 0, 0.4, null);
      // home base marker
      if (flag.home) {
        var pulse = 0.85 + Math.sin(time * 2.2) * 0.12;
        renderer.pushRaw('cyl', flag.home[0], flag.home[1] - 1.1, flag.home[2],
                         0, 0, 0, 13 * pulse, 0.3, 13 * pulse,
                         GLX.mat.hexToRgb(colour), 0.45, 0, 2, 0.7, null);
      }
      if (carried) self.drawCarrier(renderer, flag, time);
    });
  };

  // ----------------------------------------------------------------- payload
  WorldExtras.prototype.drawCart = function (renderer, state, time) {
    if (!state || !state.cart) return;
    var cart = state.cart;
    var p = cart.p;
    var yaw = cart.yaw || 0;
    var team = state.attackers === 'red' ? '#b8383b' : '#5885a2';
    // chassis
    renderer.pushRaw('box', p[0], p[1] + 1.6, p[2], 0, yaw, 0, 6.5, 2.2, 9.5,
                     GLX.mat.hexToRgb('#4a4a4a'), 1, 1, 1, 0, null);
    renderer.pushRaw('box', p[0], p[1] + 3.4, p[2], 0, yaw, 0, 5.4, 1.8, 7.6,
                     GLX.mat.hexToRgb('#6b4a2a'), 1, 1, 0, 0, null);
    // the bomb
    renderer.pushRaw('cyl', p[0], p[1] + 5.4, p[2], 0, yaw, 0, 3.4, 3.2, 3.4,
                     GLX.mat.hexToRgb(team), 1, 0, 1, 0, null);
    renderer.pushRaw('sph', p[0], p[1] + 7.0, p[2], 0, yaw, 0, 3.4, 2.4, 3.4,
                     GLX.mat.hexToRgb('#2f3640'), 1, 0, 1, 0, null);
    var blink = (Math.sin(time * (cart.pushers ? 9 : 3)) * 0.5 + 0.5);
    renderer.pushRaw('sph', p[0], p[1] + 8.4, p[2], 0, 0, 0, 1.0, 1.0, 1.0,
                     [1, blink * 0.4, 0.1], 1, 0, 2, 0.8, null);
    // wheels
    for (var side = -1; side <= 1; side += 2) {
      for (var end = -1; end <= 1; end += 2) {
        var ox = Math.cos(yaw) * side * 3.1 + Math.sin(yaw) * end * 3.4;
        var oz = -Math.sin(yaw) * side * 3.1 + Math.cos(yaw) * end * 3.4;
        renderer.pushRaw('cyl', p[0] + ox, p[1] + 1.1, p[2] + oz,
                         0, yaw, Math.PI / 2, 2.0, 0.7, 2.0,
                         GLX.mat.hexToRgb('#22262b'), 1, 0, 1, 0, null);
      }
    }
    // capture ring
    var radius = 11;
    var glow = cart.blocked ? [1, 0.35, 0.3] : (cart.pushers ? [0.4, 1, 0.5] : [0.8, 0.8, 0.85]);
    renderer.pushRaw('cyl', p[0], p[1] + 0.25, p[2], 0, 0, 0,
                     radius * 2, 0.2, radius * 2, glow, 0.24, 0, 2, 0.8, null);
    if (this.client.settings.showNames) {
      renderer.queueTag('cart', Math.round((cart.progress || 0) * 100) + '%',
                        cart.blocked ? '#ff9a90' : '#ffe08a',
                        cart.blocked ? 'BLOCKED' : (cart.pushers ? cart.pushers + ' pushing' : ''),
                        [p[0], p[1] + 10.5, p[2]], 1.5);
    }
    // checkpoints along the track
    var track = state.track;
    if (track && state.checkpoints && !this._cpDrawn) {
      this.checkpointPoints = state.checkpoints.map(function (fraction) {
        return pointAt(track, fraction * state.track_length);
      });
      this._cpDrawn = true;
    }
    if (this.checkpointPoints) {
      var reached = state.checkpoints_reached || 0;
      this.checkpointPoints.forEach(function (point, index) {
        var done = index < reached;
        renderer.pushRaw('cyl', point[0], point[1] + 0.4, point[2], 0, 0, 0,
                         9, 0.4, 9, done ? [0.35, 0.85, 0.4] : [1, 0.85, 0.3],
                         0.5, 0, 2, 0.6, null);
        renderer.pushRaw('box', point[0], point[1] + 6, point[2],
                         0, 0, 0, 0.5, 11, 0.5,
                         done ? [0.35, 0.85, 0.4] : [1, 0.85, 0.3], 0.75, 0, 2, 0.5, null);
      });
    }
  };

  function pointAt(track, distance) {
    distance = Math.max(0, distance);
    for (var i = 0; i < track.length - 1; i++) {
      var a = track[i], b = track[i + 1];
      var seg = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
      if (distance <= seg || i === track.length - 2) {
        var t = seg ? Math.min(1, distance / seg) : 0;
        return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
                a[2] + (b[2] - a[2]) * t];
      }
      distance -= seg;
    }
    return track[track.length - 1].slice();
  }

  // ------------------------------------------------------------------ tycoon
  WorldExtras.prototype.setPlots = function (plots) {
    this.plots = plots || [];
  };

  WorldExtras.prototype.addBuilt = function (plotIndex, upgradeId, geometry) {
    var key = plotIndex + ':' + upgradeId;
    if (this.builtGeometry[key]) return;
    this.builtGeometry[key] = geometry.parts || [];
    var client = this.client;
    // animate the pieces rising into place, then bake them into the static batch
    this.animations.push({
      parts: (geometry.parts || []).map(function (part) {
        return { part: part, from: part.p[1] - Math.max(4, part.s[1] * 1.5) };
      }),
      t: 0, duration: 0.85, plot: plotIndex, id: upgradeId
    });
    if (client.audio) client.audio.play('build', { volume: 0.7 });
  };

  WorldExtras.prototype.resetPlot = function (plotIndex) {
    var self = this;
    Object.keys(this.builtGeometry).forEach(function (key) {
      if (key.indexOf(plotIndex + ':') === 0) delete self.builtGeometry[key];
    });
    this.client.rebuildStatic();
  };

  WorldExtras.prototype.staticExtras = function () {
    var out = [];
    var self = this;
    Object.keys(this.builtGeometry).forEach(function (key) {
      var animating = self.animations.some(function (anim) {
        return (anim.plot + ':' + anim.id) === key;
      });
      if (animating) return;
      out = out.concat(self.builtGeometry[key]);
    });
    return out;
  };

  WorldExtras.prototype.updateAnimations = function (dt) {
    var finished = false;
    for (var i = 0; i < this.animations.length; i++) {
      this.animations[i].t += dt;
      if (this.animations[i].t >= this.animations[i].duration) {
        this.animations.splice(i, 1);
        i--;
        finished = true;
      }
    }
    if (finished) this.client.rebuildStatic();
  };

  WorldExtras.prototype.drawAnimations = function (renderer) {
    this.animations.forEach(function (anim) {
      var t = Math.min(1, anim.t / anim.duration);
      var ease = 1 - Math.pow(1 - t, 3);
      anim.parts.forEach(function (entry) {
        var part = entry.part;
        renderer.push({
          t: part.t, s: part.s, c: part.c, r: part.r, m: part.m, a: part.a,
          st: part.st, dec: part.dec,
          p: [part.p[0], entry.from + (part.p[1] - entry.from) * ease, part.p[2]]
        });
      });
    });
  };

  WorldExtras.prototype.drawTycoon = function (renderer, time) {
    var client = this.client;
    var myPlot = client.myPlot;
    var nearest = null;
    var nearestDist = 12;
    var eye = client.local.pos;

    this.plots.forEach(function (plot) {
      var mine = plot.index === myPlot;
      var colour = GLX.mat.hexToRgb(plot.color);
      // claim pad
      var claim = plot.claim;
      var free = !plot.owner;
      if (claim) {
        var pulse = 0.6 + Math.sin(time * 2 + plot.index) * 0.12;
        renderer.pushRaw('cyl', claim[0], claim[1] + 0.35, claim[2], 0, 0, 0,
                         9, 0.7, 9, free ? [0.3, 0.85, 0.4] : colour,
                         free ? 0.85 : 0.5, 0, 2, free ? 0.4 : 0.7, null);
        renderer.pushRaw('box', claim[0], claim[1] + 0.9 + Math.sin(time * 2) * 0.15,
                         claim[2], 0, time * 0.8, 0, 1.4, 1.4, 1.4,
                         free ? [0.4, 1, 0.5] : colour, 0.9, 0, 2, 0.5, null);
        if (client.settings.showNames) {
          renderer.queueTag('claim' + plot.index,
                            plot.name,
                            free ? '#9ade8f' : '#ffffff',
                            free ? 'unclaimed -- press E' : (plot.owner + "'s crew (" +
                              plot.members + '/' + plot.capacity + ')'),
                            [claim[0], claim[1] + 6.5, claim[2]], 1.35);
        }
        var d = dist(eye, claim);
        if (d < nearestDist && !mine) {
          nearest = { kind: 'claim', plot: plot.index,
                      label: free ? 'Claim <b>' + plot.name + '</b>'
                                  : 'Join the <b>' + plot.name + '</b> crew',
                      dist: d };
          nearestDist = d;
        }
      }
      if (!mine) return;

      // collector pad
      var collector = plot.collector;
      if (collector) {
        var bank = plot.bank || 0;
        var height = Math.min(3.2, 0.4 + bank / 900);
        renderer.pushRaw('box', collector[0], collector[1] + 0.3, collector[2],
                         0, 0, 0, 11, 0.6, 11, [0.15, 0.65, 0.25], 1, 1, 0, 0, null);
        renderer.pushRaw('box', collector[0], collector[1] + 0.7 + height / 2,
                         collector[2], 0, time * 0.6, 0, 5, height, 5,
                         [1, 0.83, 0.2], 0.92, 0, 1, 0.2, null);
        if (client.settings.showNames) {
          renderer.queueTag('collect' + plot.index, Math.floor(bank) + ' Noogets',
                            '#ffe08a', 'walk over to collect',
                            [collector[0], collector[1] + 6, collector[2]], 1.2);
        }
      }

      // buy buttons
      (plot.buttons || []).forEach(function (button) {
        var p = button.p;
        var affordable = client.coins >= button.cost;
        var glow = affordable ? [0.35, 0.9, 0.45] : [0.85, 0.35, 0.3];
        renderer.pushRaw('cyl', p[0], p[1] + 0.5, p[2], 0, 0, 0, 6, 1.0, 6,
                         glow, 1, 0, 0, 0, null);
        renderer.pushRaw('cyl', p[0], p[1] + 1.05 + Math.sin(time * 3 + p[0]) * 0.08,
                         p[2], 0, 0, 0, 4.6, 0.5, 4.6,
                         affordable ? [0.55, 1, 0.6] : [1, 0.5, 0.45], 1, 0, 2, 0.35, null);
        if (client.settings.showNames) {
          renderer.queueTag('btn' + plot.index + button.id, button.name,
                            affordable ? '#9ade8f' : '#ff9a90',
                            button.cost.toLocaleString() + ' Noogets' +
                            (button.income ? '  (+' + button.income + '/s)' : ''),
                            [p[0], p[1] + 6.2, p[2]], 1.25);
        }
        var bd = dist(eye, p);
        if (bd < nearestDist) {
          nearest = { kind: 'buy', id: button.id, dist: bd,
                      label: (affordable ? 'Buy <b>' + button.name + '</b> for ' +
                        button.cost.toLocaleString() + ' Noogets'
                        : 'Need ' + (button.cost - Math.floor(client.coins)).toLocaleString() +
                          ' more Noogets for <b>' + button.name + '</b>'),
                      enabled: affordable };
          nearestDist = bd;
        }
      });

      // active machines
      (plot.actives || []).forEach(function (machine) {
        var p = machine.p;
        var ready = machine.ready_in <= 0;
        renderer.pushRaw('cyl', p[0], p[1] + 0.4, p[2], 0, 0, 0, 7, 0.8, 7,
                         ready ? [0.95, 0.75, 0.2] : [0.4, 0.4, 0.45], 0.9, 0, 2,
                         ready ? 0.3 : 0.8, null);
        if (client.settings.showNames) {
          renderer.queueTag('act' + plot.index + machine.id, machine.label,
                            ready ? '#ffe08a' : '#b9c3cc',
                            ready ? 'press E  (+' + machine.payout + ')'
                                  : 'ready in ' + machine.ready_in.toFixed(1) + 's',
                            [p[0], p[1] + 6, p[2]], 1.2);
        }
        var md = dist(eye, p);
        if (md < nearestDist && ready) {
          nearest = { kind: 'use', id: machine.id, dist: md, enabled: true,
                      label: '<b>' + machine.label + '</b> (+' + machine.payout + ' Noogets)' };
          nearestDist = md;
        }
      });
    });

    this.interactTarget = nearest;
    if (nearest) {
      client.hud.setPrompt('[<b>E</b>] ' + nearest.label);
    } else {
      client.hud.setPrompt('');
    }
  };

  function dist(a, b) {
    return Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
  }

  WorldExtras.prototype.interact = function () {
    var target = this.interactTarget;
    if (!target) return;
    if (target.kind === 'claim') {
      this.client.net.send({ t: 'act', k: 'claim', plot: target.plot });
    } else if (target.kind === 'buy') {
      this.client.net.send({ t: 'act', k: 'buy', id: target.id });
    } else if (target.kind === 'use') {
      this.client.net.send({ t: 'act', k: 'use', id: target.id });
    }
  };

  WorldExtras.prototype.draw = function (renderer, state, time, dt) {
    this.updateAnimations(dt);
    this.drawAnimations(renderer);
    if (this.mode === 'captures') {
      this.drawFlags(renderer, time);
      this.drawOutposts(renderer, state, time);
    }
    else if (this.mode === 'payload') this.drawCart(renderer, state, time);
    else this.drawTycoon(renderer, time);
  };

  global.WorldExtras = WorldExtras;
})(window);
