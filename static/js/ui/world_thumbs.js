/* BLOCKHAVEN site -- the arena worlds' pictures.

   An arena world's card and each of its places are shot from the real map
   (app/game/arena/thumbs.py picks the parts in front of the camera each
   place stages) with its players posed in it.  Every player in a picture
   wears the classic look: yellow skin, a red torso and blue legs.  Anything
   else -- the world browser's other cards -- goes on to thumbs.js as
   before. */
(function (global) {
  'use strict';

  var Thumbs = global.Thumbs;
  if (!Thumbs || !Thumbs.renderWorld) return;

  var YELLOW = '#f5cd30', RED = '#c4281c', BLUE = '#0d69ac';
  var CLASSIC = { head: YELLOW, left_arm: YELLOW, right_arm: YELLOW, torso: RED,
                  hips: BLUE, left_leg: BLUE, right_leg: BLUE };
  var FACES = {
    grin: { shapes: [
      { k: 'ellipse', x: -0.22, y: -0.16, w: 0.11, h: 0.16, c: '#1a1a1a' },
      { k: 'ellipse', x: 0.22, y: -0.16, w: 0.11, h: 0.16, c: '#1a1a1a' },
      { k: 'arc', x: 0.02, y: 0.02, r: 0.34, a0: 0.05, a1: 0.45, w: 0.06, c: '#1a1a1a' },
      { k: 'rect', x: 0.03, y: 0.12, w: 0.3, h: 0.07, c: '#ffffff' }] },
    smile: { shapes: [
      { k: 'ellipse', x: -0.2, y: -0.14, w: 0.1, h: 0.14, c: '#1a1a1a' },
      { k: 'ellipse', x: 0.2, y: -0.14, w: 0.1, h: 0.14, c: '#1a1a1a' },
      { k: 'arc', x: 0, y: 0.04, r: 0.3, a0: 0.1, a1: 0.4, w: 0.05, c: '#1a1a1a' }] },
    shock: { shapes: [
      { k: 'ellipse', x: -0.2, y: -0.16, w: 0.12, h: 0.18, c: '#1a1a1a' },
      { k: 'ellipse', x: 0.2, y: -0.16, w: 0.12, h: 0.18, c: '#1a1a1a' },
      { k: 'ellipse', x: 0, y: 0.2, w: 0.16, h: 0.18, c: '#1a1a1a' }] }
  };

  var pending = {};

  function fetchShot(key) {
    if (!pending[key]) {
      pending[key] = fetch('/api/arena_thumb/' + encodeURIComponent(key),
                           { headers: { 'X-Requested-With': 'fetch' } })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) { return data && data.ok ? data.shot : null; })
        .catch(function () { return null; });
    }
    return pending[key];
  }

  /* One classic player, posed. ``extra`` can set a face, a hat colour, a
     tilt (leaning into a run, flung by a blast) or a lift off the ground. */
  function classic(fig, time) {
    var extra = fig.extra || {};
    var face = FACES[extra.face || 'grin'];
    var desc = { colors: CLASSIC,
                 items: { face: { item_id: 'face_' + (extra.face || 'grin'), slot: 'face', data: face } } };
    var state = fig.pose || 'idle';
    var parts = Avatar.build(desc, {
      position: fig.p, yaw: fig.yaw || 0, pitch: extra.pitch || 0, time: time,
      holding: fig.holding || null,
      pose: Avatar.pose(state, time + (extra.phase || 0), state === 'run' ? 1 : 0, desc)
    });
    if (extra.tilt) {
      // the whole figure tipped about its feet (a shove, a fall, a dive)
      var c = Math.cos(extra.tilt), s = Math.sin(extra.tilt);
      var yaw = fig.yaw || 0, cy = Math.cos(yaw), sy = Math.sin(yaw);
      parts = parts.map(function (part) {
        var dx = part.p[0] - fig.p[0], dy = part.p[1] - fig.p[1], dz = part.p[2] - fig.p[2];
        // into the figure's frame, tip about its own x axis, and back
        var lx = dx * cy - dz * sy, lz = dx * sy + dz * cy;
        var ny = dy * c - lz * s, nz = dy * s + lz * c;
        var out = {};
        Object.keys(part).forEach(function (k) { out[k] = part[k]; });
        out.p = [fig.p[0] + lx * cy + nz * sy, fig.p[1] + ny, fig.p[2] - lx * sy + nz * cy];
        var r = part.r || [0, 0, 0];
        out.r = [r[0] + extra.tilt, r[1], r[2]];
        return out;
      });
    }
    return parts;
  }

  function draw(canvas, kind, shot) {
    var renderer = Thumbs.renderer || null;
    if (!renderer) return false;
    var previous = { w: renderer.canvas.width, h: renderer.canvas.height };
    renderer.transparentBackground = false;
    renderer.canvas.width = 512;
    renderer.canvas.height = 288;
    renderer.width = 512; renderer.height = 288; renderer.aspect = 512 / 288;
    var far = renderer.far;
    renderer.far = 900;
    renderer.setSky(shot.sky);
    renderer.buildStatic([]);
    renderer.beginFrame(0.016);
    (shot.parts || []).forEach(function (part) { renderer.push(part); });
    (shot.figures || []).forEach(function (fig, i) {
      classic(fig, 0.35 + i * 0.37).forEach(function (part) { renderer.push(part); });
    });
    renderer.setCameraMatrix(shot.eye, shot.look, shot.fov || 44);
    renderer.render();
    var copy = document.createElement('canvas');
    copy.width = renderer.canvas.width;
    copy.height = renderer.canvas.height;
    copy.getContext('2d').drawImage(renderer.canvas, 0, 0);
    Thumbs.imageCache['world:' + kind + ':' + canvas.width] = copy;
    var ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.imageSmoothingEnabled = true;
      ctx.drawImage(copy, 0, 0, canvas.width, canvas.height);
    }
    renderer.transparentBackground = true;
    renderer.far = far;
    renderer.canvas.width = previous.w;
    renderer.canvas.height = previous.h;
    renderer.width = previous.w; renderer.height = previous.h;
    renderer.aspect = previous.w / previous.h;
    return true;
  }

  var original = Thumbs.renderWorld;
  Thumbs.renderWorld = function (canvas, kind, colors) {
    if (!kind || kind.indexOf('ar_') !== 0) return original.call(Thumbs, canvas, kind, colors);
    var key = 'world:' + kind + ':' + canvas.width;
    var cached = Thumbs.imageCache[key];
    if (cached) {
      var ctx = canvas.getContext('2d');
      if (ctx) { ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.drawImage(cached, 0, 0, canvas.width, canvas.height); }
      return;
    }
    // the shared renderer: thumbs.js makes it on its first world card
    if (!Thumbs.renderer) original.call(Thumbs, document.createElement('canvas'), 'ctf', null);
    fetchShot(kind).then(function (shot) {
      if (!shot) { original.call(Thumbs, canvas, 'ctf', colors); return; }
      draw(canvas, kind, shot);
    });
  };
  Thumbs.classicFigure = classic;
})(window);
