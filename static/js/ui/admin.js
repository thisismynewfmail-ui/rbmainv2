/* Admin dashboard: live stats, credit adjustments and item grants. */
(function () {
  'use strict';

  function refresh() {
    Site.get('/api/admin/live').then(function (res) {
      if (!res.ok) return;
      setText('s-users', res.site.users.toLocaleString());
      setText('s-online', res.online_users);
      setText('s-ingame', res.in_game);
      setText('s-visits', res.site.visits.toLocaleString());
      setText('s-credits', res.money.circulating.toLocaleString());
      setText('s-unusuals', res.item_stats.unusuals.toLocaleString());
      res.worlds.forEach(function (world) {
        var row = document.querySelector('[data-world-row="' + world.id + '"]');
        if (!row) return;
        row.querySelector('.p').textContent = world.players;
        row.querySelector('.i').textContent = world.instances;
        row.querySelector('.v').textContent = world.visits.toLocaleString();
        row.querySelector('.t').textContent = world.tick_ms + ' ms';
        row.querySelector('.s').innerHTML = world.online
          ? '<span class="pill green">running</span>'
          : '<span class="pill red">offline</span>';
      });
      var hosts = document.getElementById('admin-hosts');
      if (hosts && res.hosts.length) {
        var head = hosts.rows[0];
        var html = res.hosts.map(function (h) {
          return '<tr><td>' + esc(h.world) + '</td><td>' + esc(h.pid) + '</td><td>' + esc(h.port) +
            '</td><td>' + Math.floor(h.uptime) + 's</td><td>' + h.restarts +
            '</td><td>' + (h.alive ? '<span class="pill green">yes</span>'
                                   : '<span class="pill red">no</span>') + '</td></tr>';
        }).join('');
        hosts.innerHTML = '';
        hosts.appendChild(head);
        hosts.insertAdjacentHTML('beforeend', html);
      }
    }).catch(function () {});
  }

  function esc(value) {
    var div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
  }

  /* ------------------------------------------------------- connection map
     A live force-directed picture of who knows whom.  It is a plain 2D canvas
     rather than a library: nodes repel each other, edges pull like springs,
     and a weak pull to the middle stops a disconnected cluster drifting off.
     The whole thing re-fits itself to the panel every frame unless you have
     panned or zoomed, so it works the same on a phone held upright as it does
     on a wide monitor, and it merges each refresh into the layout already on
     screen instead of restarting the simulation. */
  var Net = {
    nodes: [], index: {}, edges: [],
    view: { x: 0, y: 0, k: 1, auto: true },
    selected: null,
    hover: null,
    drag: null,
    labels: true,
    loners: true,
    energy: 1,
    raf: 0,
    ready: false,
    tab: 'overview',      // which admin tab is showing
    inline: false,        // phone: the map folded in under the overview
    fitFor: 0             // seconds of catch-up fitting after Recentre
  };

  var NODE_COLORS = {
    admin: '#e0514b',
    playing: '#f0b429',
    online: '#37c26a',
    linked: '#6aa9e0',
    alone: '#8c93a1'
  };

  function nodeColor(node) {
    if (node.admin) return NODE_COLORS.admin;
    if (node.playing) return NODE_COLORS.playing;
    if (node.online) return NODE_COLORS.online;
    return node.degree ? NODE_COLORS.linked : NODE_COLORS.alone;
  }

  function nodeRadius(node) {
    // area, not radius, tracks the friend count: doubling the connections
    // should look like twice as much node, not four times
    return 4.2 + Math.sqrt(node.degree) * 3.1;
  }

  function netCanvas() { return document.getElementById('net-canvas'); }

  function fetchNetwork(first) {
    return Site.get('/api/admin/network').then(function (res) {
      if (!res.ok) return;
      mergeNetwork(res, first);
    }).catch(function () {});
  }

  function mergeNetwork(res, first) {
    var keep = {};
    var incoming = res.nodes || [];
    var spread = Math.max(140, Math.sqrt(incoming.length) * 46);
    incoming.forEach(function (row, i) {
      var node = Net.index[row.id];
      if (!node) {
        // seed on a spiral rather than at random, so the first settle pulls
        // inwards from an even ring instead of untangling a knot
        var angle = i * 2.399963;
        var radius = spread * Math.sqrt((i + 1) / (incoming.length + 1));
        node = { id: row.id, x: Math.cos(angle) * radius,
                 y: Math.sin(angle) * radius, vx: 0, vy: 0, fresh: true };
        Net.index[row.id] = node;
      }
      node.name = row.name;
      node.degree = row.degree;
      node.admin = row.admin;
      node.banned = row.banned;
      node.online = row.online;
      node.playing = row.playing;
      node.joined = row.joined;
      node.last_seen = row.last_seen;
      node.r = nodeRadius(node);
      keep[row.id] = true;
    });
    Object.keys(Net.index).forEach(function (id) {
      if (!keep[id]) delete Net.index[id];
    });
    Net.nodes = Object.keys(Net.index).map(function (id) { return Net.index[id]; });
    Net.edges = (res.edges || []).map(function (edge) {
      return { a: Net.index[edge.a], b: Net.index[edge.b], kind: edge.kind };
    }).filter(function (edge) { return edge.a && edge.b; });
    Net.summary = res.summary || {};
    Net.truncated = res.truncated || 0;
    Net.neighbours = {};
    Net.edges.forEach(function (edge) {
      (Net.neighbours[edge.a.id] || (Net.neighbours[edge.a.id] = [])).push(edge.b.id);
      (Net.neighbours[edge.b.id] || (Net.neighbours[edge.b.id] = [])).push(edge.a.id);
    });
    if (Net.selected && !Net.index[Net.selected]) Net.selected = null;
    // new arrivals get the layout moving again without jolting what settled
    Net.energy = Math.max(Net.energy, first ? 1 : 0.55);
    paintNetStats();
    if (Net.selected) paintNetCard(Net.index[Net.selected]);
  }

  function visibleNodes() {
    if (Net.loners) return Net.nodes;
    return Net.nodes.filter(function (node) { return node.degree > 0; });
  }

  /* Two populations, laid out on different principles.

     The connected accounts are a proper force graph: they repel, their links
     pull, and a weak gravity keeps the whole thing over the origin.

     The unconnected ones are not.  Left in the same simulation they have
     nothing pulling them anywhere, so repulsion alone flings them into a wide
     halo -- and because the auto-fit has to hold that halo, the part of the
     graph anybody actually reads ends up squeezed into a corner.  Seating
     them on a ring just outside the cluster instead keeps them visible and
     countable while the frame stays tight around the middle. */
  function stepNetwork(dt) {
    var nodes = visibleNodes();
    var count = nodes.length;
    if (!count) return;
    var pack = [], ring = [];
    var i, j, a, b, dx, dy, dist, force;
    for (i = 0; i < count; i++) {
      a = nodes[i];
      a.fx = 0; a.fy = 0;
      (a.degree ? pack : ring).push(a);
    }
    var repel = 1500 + pack.length * 9;
    for (i = 0; i < pack.length; i++) {
      a = pack[i];
      for (j = i + 1; j < pack.length; j++) {
        b = pack[j];
        dx = a.x - b.x;
        dy = a.y - b.y;
        dist = dx * dx + dy * dy;
        if (dist < 0.01) { dx = (Math.random() - 0.5); dy = (Math.random() - 0.5); dist = 0.01; }
        if (dist > 360000) continue;           // far enough to ignore
        force = repel / dist;
        var inv = 1 / Math.sqrt(dist);
        a.fx += dx * inv * force;
        a.fy += dy * inv * force;
        b.fx -= dx * inv * force;
        b.fy -= dy * inv * force;
      }
    }
    if (ring.length) {
      // Concentric with the cluster rather than with the origin: gravity
      // holds the connected nodes near the middle but does not pin their
      // centre of mass there, and a halo drawn round the origin instead
      // leaves the cluster sitting visibly off to one side of its own ring.
      var cx = 0, cy = 0, reach = 0;
      for (i = 0; i < pack.length; i++) { cx += pack[i].x; cy += pack[i].y; }
      if (pack.length) { cx /= pack.length; cy /= pack.length; }
      for (i = 0; i < pack.length; i++) {
        reach = Math.max(reach,
                         Math.hypot(pack[i].x - cx, pack[i].y - cy) + pack[i].r);
      }
      // just clear of the widest connected node, and never so tight that the
      // ring itself becomes a crowd
      var radius = Math.max(reach + 38, 92, ring.length * 6.2);
      // a slow drift, so the halo reads as alive rather than as decoration
      var spin = (Net.clock || 0) * 0.09;
      for (i = 0; i < ring.length; i++) {
        a = ring[i];
        var theta = spin + (Math.PI * 2 * i) / ring.length;
        a.fx += (cx + Math.cos(theta) * radius - a.x) * 6;
        a.fy += (cy + Math.sin(theta) * radius - a.y) * 6;
      }
    }
    Net.edges.forEach(function (edge) {
      if (!Net.loners && (!edge.a.degree || !edge.b.degree)) return;
      var rest = edge.kind === 'friend' ? 64 : 96;
      var pull = edge.kind === 'friend' ? 0.030 : 0.012;
      dx = edge.b.x - edge.a.x;
      dy = edge.b.y - edge.a.y;
      dist = Math.sqrt(dx * dx + dy * dy) || 0.001;
      force = (dist - rest) * pull;
      var ux = dx / dist, uy = dy / dist;
      edge.a.fx += ux * force * 60;
      edge.a.fy += uy * force * 60;
      edge.b.fx -= ux * force * 60;
      edge.b.fy -= uy * force * 60;
    });
    for (i = 0; i < count; i++) {
      a = nodes[i];
      if (a.degree) {
        a.fx -= a.x * 0.9;                    // gravity towards the centre
        a.fy -= a.y * 0.9;
      }
      if (Net.drag === a) { a.vx = 0; a.vy = 0; continue; }
      a.vx = (a.vx + a.fx * dt) * 0.86;
      a.vy = (a.vy + a.fy * dt) * 0.86;
      var speed = Math.hypot(a.vx, a.vy);
      if (speed > 420) { a.vx *= 420 / speed; a.vy *= 420 / speed; }
      // The cluster is allowed to cool to a stop; the halo is not, or a node
      // that has just lost its last friend crawls out to its seat over half a
      // minute instead of sliding there.
      var pace = a.degree ? Net.energy : Math.max(Net.energy, 0.7);
      a.x += a.vx * dt * pace;
      a.y += a.vy * dt * pace;
      a.fresh = false;
    }
    // the simulation cools off so a settled graph stops jittering, and any
    // refresh or interaction warms it straight back up
    Net.energy = Math.max(0.12, Net.energy * 0.995);
  }

  /* The toolbar, the key, the running totals and an open node card all float
     over the canvas, so fitting to the raw canvas parks nodes underneath
     them.  Work out what is actually clear instead: charge each overlay to
     the edge it hugs -- a tall one sideways, a wide one up or down -- and fit
     into what is left. */
  function netInsets(canvas) {
    var box = canvas.getBoundingClientRect();
    var inset = { top: 22, right: 22, bottom: 22, left: 22 };
    ['.net-toolbar', '#net-key', '.net-stats', '#net-card'].forEach(function (sel) {
      var el = document.querySelector(sel);
      if (!el || el.classList.contains('hidden')) return;
      var r = el.getBoundingClientRect();
      if (!r.width || !r.height) return;
      var edge;
      if (r.height >= r.width) {
        edge = (r.left - box.left <= box.right - r.right) ? 'left' : 'right';
      } else {
        edge = (r.top - box.top <= box.bottom - r.bottom) ? 'top' : 'bottom';
      }
      var reach = { top: r.bottom - box.top, bottom: box.bottom - r.top,
                    left: r.right - box.left, right: box.right - r.left }[edge];
      inset[edge] = Math.max(inset[edge], reach + 12);
    });
    // never let the chrome eat the whole box on a small screen
    var maxH = canvas.clientHeight * 0.62, maxW = canvas.clientWidth * 0.62;
    if (inset.top + inset.bottom > maxH) {
      var sh = maxH / (inset.top + inset.bottom);
      inset.top *= sh; inset.bottom *= sh;
    }
    if (inset.left + inset.right > maxW) {
      var sw = maxW / (inset.left + inset.right);
      inset.left *= sw; inset.right *= sw;
    }
    return inset;
  }

  /* Ease the view onto the graph's bounds.  Framerate independent, so a
     phone at 30fps refits at the same pace a desktop does, and deadzoned, so
     a settled graph stops adjusting instead of breathing forever.  This is
     what keeps every node in frame as accounts arrive and links form. */
  function fitNetwork(canvas, dt) {
    var nodes = visibleNodes();
    if (!nodes.length) return;
    var minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9;
    nodes.forEach(function (node) {
      minX = Math.min(minX, node.x - node.r);
      minY = Math.min(minY, node.y - node.r);
      maxX = Math.max(maxX, node.x + node.r);
      maxY = Math.max(maxY, node.y + node.r);
    });
    var inset = netInsets(canvas);
    var availW = Math.max(60, canvas.clientWidth - inset.left - inset.right);
    var availH = Math.max(60, canvas.clientHeight - inset.top - inset.bottom);
    var w = Math.max(1, maxX - minX), h = Math.max(1, maxY - minY);
    var k = Math.max(0.12, Math.min(1.9, Math.min(availW / w, availH / h)));
    // the graph centres on the clear area, not on the middle of the canvas
    var cx = (inset.left - inset.right) / 2;
    var cy = (inset.top - inset.bottom) / 2;
    var tx = cx / k - (minX + maxX) / 2;
    var ty = cy / k - (minY + maxY) / 2;
    if (Math.abs(k - Net.view.k) < 0.0015 &&
        Math.abs(tx - Net.view.x) < 0.4 && Math.abs(ty - Net.view.y) < 0.4) {
      Net.view.k = k; Net.view.x = tx; Net.view.y = ty;
      return;
    }
    var ease = Math.min(1, (dt === undefined ? 0.016 : dt) * 3.2);
    Net.view.k += (k - Net.view.k) * ease;
    Net.view.x += (tx - Net.view.x) * ease;
    Net.view.y += (ty - Net.view.y) * ease;
  }

  /* One switch for the auto-fit, so the button and the state can never
     disagree -- a pan or a zoom turns it off and the button goes with it. */
  function setAutoFit(on) {
    Net.view.auto = !!on;
    var button = document.getElementById('net-auto-btn');
    if (button) button.setAttribute('aria-pressed', on ? 'true' : 'false');
  }

  function toScreen(canvas, node) {
    return {
      x: canvas.clientWidth / 2 + (node.x + Net.view.x) * Net.view.k,
      y: canvas.clientHeight / 2 + (node.y + Net.view.y) * Net.view.k
    };
  }

  function fromScreen(canvas, px, py) {
    return {
      x: (px - canvas.clientWidth / 2) / Net.view.k - Net.view.x,
      y: (py - canvas.clientHeight / 2) / Net.view.k - Net.view.y
    };
  }

  function drawNetwork() {
    var canvas = netCanvas();
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var ratio = Math.min(2, window.devicePixelRatio || 1);
    var w = canvas.clientWidth, h = canvas.clientHeight;
    if (canvas.width !== Math.round(w * ratio) ||
        canvas.height !== Math.round(h * ratio)) {
      canvas.width = Math.round(w * ratio);
      canvas.height = Math.round(h * ratio);
    }
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, w, h);

    var dark = window.Site && Site.isDark();
    var edgeInk = dark ? 'rgba(150,190,230,' : 'rgba(40,80,130,';
    var nodes = visibleNodes();
    var focus = Net.selected || Net.hover;
    var near = focus ? (Net.neighbours[focus] || []) : null;

    Net.edges.forEach(function (edge) {
      if (!Net.loners && (!edge.a.degree || !edge.b.degree)) return;
      var a = toScreen(canvas, edge.a), b = toScreen(canvas, edge.b);
      var lit = !focus || edge.a.id === focus || edge.b.id === focus;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      if (edge.kind === 'friend') {
        ctx.strokeStyle = edgeInk + (lit ? 0.62 : 0.09) + ')';
        ctx.lineWidth = lit ? 1.6 : 1;
        ctx.setLineDash([]);
      } else if (edge.kind === 'pending') {
        ctx.strokeStyle = 'rgba(240,180,41,' + (lit ? 0.8 : 0.12) + ')';
        ctx.lineWidth = 1.2;
        ctx.setLineDash([4, 3]);
      } else {
        ctx.strokeStyle = edgeInk + (lit ? 0.3 : 0.05) + ')';
        ctx.lineWidth = 1;
        ctx.setLineDash([1, 4]);
      }
      ctx.stroke();
    });
    ctx.setLineDash([]);

    nodes.forEach(function (node) {
      var p = toScreen(canvas, node);
      var lit = !focus || node.id === focus ||
        (near && near.indexOf(node.id) >= 0);
      var r = Math.max(2.5, node.r * Math.min(1.4, Net.view.k));
      ctx.globalAlpha = lit ? 1 : 0.22;
      if (node.playing || node.online) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, r + 4, 0, Math.PI * 2);
        ctx.fillStyle = (node.playing ? 'rgba(240,180,41,' : 'rgba(55,194,106,') +
          (0.14 + 0.1 * Math.sin(Net.clock * 2 + node.id)) + ')';
        ctx.fill();
      }
      ctx.beginPath();
      ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
      ctx.fillStyle = nodeColor(node);
      ctx.fill();
      ctx.lineWidth = node.id === Net.selected ? 2.4 : 1;
      ctx.strokeStyle = node.banned ? '#000'
        : (node.id === Net.selected ? (dark ? '#fff' : '#12324f')
                                    : 'rgba(255,255,255,.65)');
      ctx.stroke();
      if (Net.labels && lit && (r > 6 || node.id === focus)) {
        ctx.font = '10px Verdana, Geneva, sans-serif';
        ctx.textAlign = 'center';
        ctx.lineWidth = 3;
        ctx.strokeStyle = dark ? 'rgba(10,22,34,.85)' : 'rgba(255,255,255,.85)';
        ctx.strokeText(node.name, p.x, p.y - r - 4);
        ctx.fillStyle = dark ? '#dce9f6' : '#1d3d5c';
        ctx.fillText(node.name, p.x, p.y - r - 4);
      }
      ctx.globalAlpha = 1;
    });
  }

  function paintNetStats() {
    var box = document.getElementById('net-stats');
    var summary = Net.summary || {};
    if (box) {
      box.innerHTML =
        '<span><b>' + (summary.people || 0) + '</b> people</span>' +
        '<span><b>' + (summary.friendships || 0) + '</b> friendships</span>' +
        '<span><b>' + (summary.pending || 0) + '</b> pending</span>' +
        '<span><b>' + (summary.follows || 0) + '</b> follows</span>' +
        '<span><b>' + (summary.isolated || 0) + '</b> unconnected</span>';
    }
    var foot = document.getElementById('net-foot');
    if (foot) {
      foot.textContent = Net.truncated
        ? 'Showing the ' + (summary.people || 0) + ' most connected accounts; ' +
          Net.truncated + ' quieter ones are off the map.'
        : 'Every account on the platform is on the map.';
    }
    var empty = document.getElementById('net-empty');
    if (empty) empty.classList.toggle('hidden', !!Net.nodes.length);
  }

  function paintNetCard(node) {
    var card = document.getElementById('net-card');
    if (!card) return;
    if (!node) { card.classList.add('hidden'); return; }
    var near = (Net.neighbours[node.id] || []).map(function (id) {
      return Net.index[id];
    }).filter(Boolean);
    near.sort(function (a, b) { return b.degree - a.degree; });
    card.classList.remove('hidden');
    card.innerHTML =
      '<button type="button" class="net-card-close" data-net="close" ' +
      'aria-label="Close">&times;</button>' +
      '<b>' + esc(node.name) + '</b>' +
      (node.admin ? ' <span class="pill red">admin</span>' : '') +
      (node.banned ? ' <span class="pill red">suspended</span>' : '') +
      '<div class="tiny muted">' +
      (node.playing ? 'in ' + esc(node.playing)
                    : (node.online ? 'online now' : 'offline')) +
      ' &bull; ' + node.degree + ' friend' + (node.degree === 1 ? '' : 's') +
      '</div>' +
      (near.length
        ? '<div class="net-near">' + near.slice(0, 10).map(function (other) {
            return '<button type="button" class="chip" data-net-focus="' +
              other.id + '">' + esc(other.name) + '</button>';
          }).join('') + (near.length > 10 ? '<span class="chip more">+' +
            (near.length - 10) + '</span>' : '') + '</div>'
        : '<div class="tiny muted net-near">No connections yet.</div>') +
      '<div class="net-card-links">' +
      '<a class="btn small" href="/profile/' + encodeURIComponent(node.name) +
      '" target="_blank" rel="noopener">Profile</a>' +
      '<button class="btn small" data-admin-open="' + esc(node.name) +
      '">Manage</button></div>';
  }

  function nodeAt(canvas, px, py) {
    var nodes = visibleNodes();
    for (var i = nodes.length - 1; i >= 0; i--) {
      var p = toScreen(canvas, nodes[i]);
      var r = Math.max(6, nodes[i].r * Math.min(1.4, Net.view.k)) + 4;
      if ((px - p.x) * (px - p.x) + (py - p.y) * (py - p.y) <= r * r) {
        return nodes[i];
      }
    }
    return null;
  }

  function bindNetwork() {
    var canvas = netCanvas();
    if (!canvas || Net.ready) return;
    Net.ready = true;
    var pan = null;

    canvas.addEventListener('pointerdown', function (event) {
      canvas.setPointerCapture(event.pointerId);
      var rect = canvas.getBoundingClientRect();
      var px = event.clientX - rect.left, py = event.clientY - rect.top;
      var hit = nodeAt(canvas, px, py);
      if (hit) {
        Net.drag = hit;
        Net.dragMoved = false;
      } else {
        pan = { x: event.clientX, y: event.clientY,
                vx: Net.view.x, vy: Net.view.y };
        setAutoFit(false);
        Net.fitFor = 0;
      }
    });
    canvas.addEventListener('pointermove', function (event) {
      var rect = canvas.getBoundingClientRect();
      var px = event.clientX - rect.left, py = event.clientY - rect.top;
      if (Net.drag) {
        var world = fromScreen(canvas, px, py);
        Net.drag.x = world.x;
        Net.drag.y = world.y;
        Net.dragMoved = true;
        Net.energy = Math.max(Net.energy, 0.7);
        return;
      }
      if (pan) {
        Net.view.x = pan.vx + (event.clientX - pan.x) / Net.view.k;
        Net.view.y = pan.vy + (event.clientY - pan.y) / Net.view.k;
        return;
      }
      var over = nodeAt(canvas, px, py);
      Net.hover = over ? over.id : null;
      canvas.style.cursor = over ? 'pointer' : 'grab';
    });
    function release(event) {
      if (Net.drag && !Net.dragMoved) {
        Net.selected = Net.selected === Net.drag.id ? null : Net.drag.id;
        paintNetCard(Net.selected ? Net.index[Net.selected] : null);
      }
      Net.drag = null;
      pan = null;
      if (event && canvas.hasPointerCapture &&
          canvas.hasPointerCapture(event.pointerId)) {
        canvas.releasePointerCapture(event.pointerId);
      }
    }
    canvas.addEventListener('pointerup', release);
    canvas.addEventListener('pointercancel', release);
    canvas.addEventListener('pointerleave', function () { Net.hover = null; });
    canvas.addEventListener('wheel', function (event) {
      event.preventDefault();
      setAutoFit(false);
      Net.fitFor = 0;
      var factor = Math.exp(-event.deltaY * 0.0015);
      Net.view.k = Math.max(0.1, Math.min(4, Net.view.k * factor));
    }, { passive: false });

  }

  /* The map's own buttons are bound once at load, not inside bindNetwork:
     the phone fold-out sits on the overview tab, where the canvas has never
     been touched, and a button that does nothing until you have already
     opened the thing it opens is no button at all. */
  function bindNetActions() {
    if (Net.actionsBound) return;
    Net.actionsBound = true;
    document.addEventListener('click', function (event) {
      var button = event.target.closest('[data-net]');
      if (button) {
        var action = button.dataset.net;
        if (action === 'key') {
          var key = document.getElementById('net-key');
          var on = key.classList.toggle('hidden');
          button.setAttribute('aria-pressed', on ? 'false' : 'true');
        } else if (action === 'labels') {
          Net.labels = !Net.labels;
          button.setAttribute('aria-pressed', Net.labels ? 'true' : 'false');
        } else if (action === 'loners') {
          Net.loners = !Net.loners;
          button.setAttribute('aria-pressed', Net.loners ? 'true' : 'false');
          Net.energy = 1;
        } else if (action === 'replay') {
          Net.nodes.forEach(function (node) {
            node.x = (Math.random() - 0.5) * 300;
            node.y = (Math.random() - 0.5) * 300;
            node.vx = 0; node.vy = 0;
          });
          Net.energy = 1;
          setAutoFit(true);
        } else if (action === 'autofit') {
          setAutoFit(!Net.view.auto);
          if (Net.view.auto) Net.fitFor = 0;
        } else if (action === 'fit') {
          // a one-off glide back onto the graph that leaves the auto-fit
          // switch exactly as the operator set it
          Net.fitFor = 1.1;
        } else if (action === 'inline') {
          Net.inline = !Net.inline;
          button.setAttribute('aria-pressed', Net.inline ? 'true' : 'false');
          button.textContent = Net.inline ? 'Hide connection map'
                                          : 'Show connection map';
          showPanels();
        } else if (action === 'close') {
          Net.selected = null;
          paintNetCard(null);
        }
        return;
      }
      var focus = event.target.closest('[data-net-focus]');
      if (focus) {
        Net.selected = parseInt(focus.dataset.netFocus, 10);
        paintNetCard(Net.index[Net.selected]);
      }
    });
  }

  function netLoop(now) {
    Net.raf = requestAnimationFrame(netLoop);
    var panel = document.querySelector('[data-admin-panel="network"]');
    if (!panel || panel.classList.contains('hidden') || document.hidden) {
      Net.last = 0;
      return;
    }
    var dt = Math.min(0.05, (now - (Net.last || now)) / 1000);
    Net.last = now;
    Net.clock = (Net.clock || 0) + dt;
    stepNetwork(dt);
    var canvas = netCanvas();
    if (Net.fitFor > 0) Net.fitFor = Math.max(0, Net.fitFor - dt);
    if (canvas && (Net.view.auto || Net.fitFor > 0)) fitNetwork(canvas, dt);
    drawNetwork();
  }

  /* There is no corner to spare on a phone, so the key starts out of the way
     and the Key button brings it in. */
  function collapseKeyOnPhones() {
    if (Net.keyDecided || window.innerWidth > 860) return;
    Net.keyDecided = true;
    var key = document.getElementById('net-key');
    var button = document.getElementById('net-key-btn');
    if (key) key.classList.add('hidden');
    if (button) button.setAttribute('aria-pressed', 'false');
  }

  /* One place decides what is on screen, from the tab, the phone toggle and
     the window width together.  The connection map already sits after the
     overview in the document, so showing both on a phone drops the map in at
     the bottom of the dashboard without moving a single node of markup. */
  function showPanels() {
    var phone = window.innerWidth <= 860;
    var inline = phone && Net.inline && Net.tab === 'overview';
    document.querySelectorAll('[data-admin-panel]').forEach(function (panel) {
      var name = panel.dataset.adminPanel;
      var on = name === Net.tab || (inline && name === 'network');
      panel.classList.toggle('hidden', !on);
      panel.classList.toggle('admin-inline', inline && name === 'network');
    });
    var button = document.getElementById('net-inline-btn');
    if (button) {
      button.setAttribute('aria-pressed', Net.inline ? 'true' : 'false');
      button.textContent = Net.inline ? 'Hide connection map'
                                      : 'Show connection map';
    }
    if (Net.tab === 'network' || inline) startNetwork();
  }

  function startNetwork() {
    bindNetwork();
    collapseKeyOnPhones();
    Net.energy = Math.max(Net.energy, 0.8);
    Net.fitFor = Math.max(Net.fitFor, 1.1);   // glide onto the graph on arrival
    if (!Net.nodes.length) fetchNetwork(true);
    if (!Net.raf) Net.raf = requestAnimationFrame(netLoop);
  }

  function bindAdminTabs() {
    var tabs = document.getElementById('admin-tabs');
    if (!tabs) return;
    tabs.addEventListener('click', function (event) {
      var tab = event.target.closest('[data-admin-tab]');
      if (!tab) return;
      Net.tab = tab.dataset.adminTab;
      tabs.querySelectorAll('[data-admin-tab]').forEach(function (other) {
        other.classList.toggle('on', other === tab);
      });
      showPanels();
    });
    // a rotation or a resize can take the inline map out of scope entirely
    window.addEventListener('resize', function () {
      clearTimeout(Net.resizeTimer);
      Net.resizeTimer = setTimeout(function () {
        showPanels();
        Net.fitFor = Math.max(Net.fitFor, 0.8);
      }, 180);
    });
  }


  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function openUser(username) {
    Site.get('/api/admin/user?username=' + encodeURIComponent(username))
      .then(function (res) {
        if (!res.ok) { Site.toast(res.error, 'bad'); return; }
        document.getElementById('am-title').textContent = username;
        var inv = res.inventory.map(function (item) {
          return '<tr><td>' + esc(item.name) + '</td><td>' + esc(item.slot_label) +
            '</td><td>' + (item.tier === 'unusual'
              ? '<span class="pill purple">Unusual: ' + esc(item.effect_name) + '</span>'
              : '<span class="pill">Normal</span>') +
            '</td><td class="right"><button class="btn small danger" data-revoke="' +
            item.inv_id + '" data-user="' + username + '">Remove</button></td></tr>';
        }).join('');
        var ledger = res.ledger.map(function (row) {
          return '<tr><td>' + esc(row.reason) + '</td><td class="right">' +
            (row.delta > 0 ? '+' : '') + row.delta.toLocaleString() +
            '</td><td class="right">' + row.balance_after.toLocaleString() + '</td></tr>';
        }).join('');
        document.getElementById('am-body').innerHTML =
          '<dl class="stats"><div><dt>Credits</dt><dd>' + res.credits.toLocaleString() +
          '</dd></div><div><dt>Kills</dt><dd>' + res.stats.total.kills +
          '</dd></div><div><dt>Deaths</dt><dd>' + res.stats.total.deaths +
          '</dd></div></dl>' +
          '<div class="inline-form" style="margin:10px 0">' +
          '<button class="btn small danger" data-ban="' + esc(username) +
          '">Toggle suspension</button>' +
          '<a class="btn small" href="/profile/' + encodeURIComponent(username) +
          '" target="_blank">Open profile</a>' +
          '</div>' +
          '<h3>Inventory (' + res.inventory.length + ')</h3>' +
          '<table class="grid">' + inv + '</table>' +
          '<h3 style="margin-top:10px">Credit ledger</h3>' +
          '<table class="grid">' + ledger + '</table>';
        document.getElementById('admin-modal').classList.remove('hidden');
      });
  }

  document.addEventListener('click', function (event) {
    var target = event.target.closest('[data-admin-open]');
    if (target) { openUser(target.dataset.adminOpen); return; }
    target = event.target.closest('#am-close');
    if (target) { document.getElementById('admin-modal').classList.add('hidden'); return; }
    target = event.target.closest('[data-revoke]');
    if (target) {
      Site.post('/api/admin/revoke', {
        username: target.dataset.user, inv_id: parseInt(target.dataset.revoke, 10)
      }).then(function (res) {
        if (!res.ok) { Site.toast(res.error, 'bad'); return; }
        Site.toast('Item removed.');
        openUser(target.dataset.user);
      });
      return;
    }
    target = event.target.closest('[data-ban]');
    if (target) {
      Site.post('/api/admin/ban', { username: target.dataset.ban }).then(function (res) {
        if (!res.ok) { Site.toast(res.error, 'bad'); return; }
        Site.toast(res.banned ? 'Account suspended.' : 'Account restored.');
      });
    }
  });

  document.addEventListener('DOMContentLoaded', function () {
    bindNetActions();
    bindAdminTabs();
    // the map rides the dashboard's own heartbeat, so the graph, the counters
    // and the world table are always describing the same moment
    setInterval(function () {
      refresh();
      var panel = document.querySelector('[data-admin-panel="network"]');
      if (panel && !panel.classList.contains('hidden')) fetchNetwork(false);
    }, 3000);

    document.getElementById('cr-go').addEventListener('click', function () {
      var payload = {
        username: document.getElementById('cr-user').value.trim(),
        amount: parseInt(document.getElementById('cr-amount').value, 10) || 0,
        mode: document.getElementById('cr-mode').value,
        reason: document.getElementById('cr-reason').value
      };
      Site.post('/api/admin/credits', payload).then(function (res) {
        var out = document.getElementById('cr-result');
        if (!res.ok) {
          out.innerHTML = '<div class="notice bad">' + esc(res.error) + '</div>';
          return;
        }
        out.innerHTML = '<div class="notice">' + esc(res.username) + ' now has ' +
          res.balance.toLocaleString() + ' credits.</div>';
        var row = document.querySelector('[data-user-row="' + res.username + '"] .credits');
        if (row) row.textContent = res.balance.toLocaleString();
      });
    });

    document.getElementById('gr-go').addEventListener('click', function () {
      var payload = {
        username: document.getElementById('gr-user').value.trim(),
        item_id: document.getElementById('gr-item').value,
        tier: document.getElementById('gr-tier').value,
        effect: document.getElementById('gr-effect').value
      };
      Site.post('/api/admin/grant', payload).then(function (res) {
        var out = document.getElementById('gr-result');
        if (!res.ok) {
          out.innerHTML = '<div class="notice bad">' + esc(res.error) + '</div>';
          return;
        }
        out.innerHTML = '<div class="notice">Granted ' + esc(res.item.item_id) +
          (res.item.tier === 'unusual' ? ' (UNUSUAL: ' + esc(res.item.effect) + ')' : '') +
          '.</div>';
      });
    });
  });
})();
