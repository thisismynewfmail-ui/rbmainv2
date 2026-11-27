/* The admin dashboard's Instances tab.

   Every game world down the side; pick one and every round being played in
   it -- live on its game host, or asleep in the bot director -- with its
   round, phase, how full it is and its best player, sorted by round number,
   by high stat (a survival round's wave, else the top score) or by people.
   Join opens the round in a new tab, pinned: the admin is seated in exactly
   that round even when it is full (app/game/host.py), and a sleeping bot
   round is woken for them.  Admin only; nothing outside the dashboard links
   here.  Refreshes itself every few seconds while the tab is open. */
(function () {
  'use strict';

  var AI = { world: '', worlds: [], rows: [], sort: 'round', timer: null, open: false };

  function el(id) { return document.getElementById(id); }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function num(n) { return Number(n || 0).toLocaleString(); }

  function age(s) {
    s = Math.max(0, Math.floor(Number(s) || 0));
    if (s < 60) return s + 's';
    if (s < 3600) return Math.floor(s / 60) + 'm';
    return Math.floor(s / 3600) + 'h ' + Math.floor((s % 3600) / 60) + 'm';
  }

  /* What "high stat" means for a round: a survival round's wave, else its
     best player's score. */
  function stat(r) { return r.wave > 0 ? r.wave * 100000 + (r.top || 0) : (r.top || 0); }

  function sorted(rows) {
    var by = {
      round: function (a, b) { return (b.round - a.round) || (stat(b) - stat(a)) || (b.count - a.count) || (a.id - b.id); },
      stat: function (a, b) { return (stat(b) - stat(a)) || (b.round - a.round) || (a.id - b.id); },
      players: function (a, b) { return (b.humans - a.humans) || (b.count - a.count) || (b.round - a.round) || (a.id - b.id); }
    }[AI.sort] || undefined;
    return rows.slice().sort(by);
  }

  // -------------------------------------------------------------- worlds
  function loadWorlds() {
    return Site.get('/api/admin/instances/worlds').then(function (res) {
      if (!res.ok) { Site.toast(res.error || 'Could not load the worlds.', 'bad'); return; }
      AI.worlds = res.worlds || [];
      if (!AI.world && AI.worlds.length) AI.world = AI.worlds[0].id;
      drawWorlds();
    });
  }

  function drawWorlds() {
    var table = el('ai-worlds');
    if (!table) return;
    var rows = AI.worlds.map(function (w) {
      var on = w.id === AI.world;
      return '<tr class="ai-world' + (on ? ' on' : '') + '" data-ai-world="' + esc(w.id) + '" style="cursor:pointer' +
        (on ? ';background:rgba(120,160,255,.14)' : '') + '"><td><b>' + esc(w.name) + '</b>' +
        '<div class="tiny muted">' + num(w.players) + ' playing &bull; ' + num(w.live) + ' live, ' + num(w.asleep) +
        ' asleep</div></td><td style="text-align:right">' +
        (w.online ? '<span class="pill green">up</span>' : '<span class="pill red">down</span>') + '</td></tr>';
    }).join('');
    table.innerHTML = rows || '<tr><td class="muted">No worlds.</td></tr>';
  }

  // ----------------------------------------------------------- instances
  function loadInstances() {
    if (!AI.world) return Promise.resolve();
    var wanted = AI.world;
    return Site.get('/api/admin/instances?world=' + encodeURIComponent(wanted)).then(function (res) {
      if (wanted !== AI.world) return;
      if (!res.ok) { Site.toast(res.error || 'Could not load the instances.', 'bad'); return; }
      AI.rows = res.instances || [];
      AI.info = res.world || {};
      drawInstances();
    });
  }

  function drawInstances() {
    var table = el('ai-instances');
    if (!table) return;
    var info = AI.info || {};
    var live = AI.rows.filter(function (r) { return r.state === 'live'; }).length;
    el('ai-title').textContent = (info.name || 'Instances') + ' — ' + num(AI.rows.length) + ' round' +
      (AI.rows.length === 1 ? '' : 's') + ' (' + num(live) + ' live)';
    var head = '<tr><th>#</th><th>State</th><th>Round</th><th>Phase / score</th><th>People</th>' +
      '<th>High stat</th><th class="hide-sm">Up for</th><th></th></tr>';
    var rows = sorted(AI.rows).map(function (r) {
      var best = r.wave > 0 ? 'wave ' + num(r.wave) : (r.top ? num(r.top) : '—');
      if (r.top_name) best += '<div class="tiny muted">' + esc(r.top_name) + (r.wave > 0 && r.top ? ' • ' + num(r.top) : '') + '</div>';
      var who = r.players && r.players.length
        ? ' title="' + esc(r.players.slice(0, 16).map(function (p) {
            return p.name + (p.bot ? ' (bot)' : '') + ' ' + p.score;
          }).join('\n')) + '"' : '';
      return '<tr><td><b>' + num(r.id) + '</b></td>' +
        '<td>' + (r.state === 'live' ? '<span class="pill green">live</span>' : '<span class="pill">asleep</span>') + '</td>' +
        '<td>' + num(r.round) + '</td>' +
        '<td>' + esc(r.summary || r.phase || '') + (r.summary && r.phase ? '<div class="tiny muted">' + esc(r.phase) + '</div>' : '') + '</td>' +
        '<td' + who + '>' + num(r.humans) + ' people, ' + num(r.bots) + ' bots<div class="tiny muted">' + num(r.count) +
        ' / ' + num(r.max) + '</div></td>' +
        '<td>' + best + '</td>' +
        '<td class="hide-sm">' + age(r.age) + '</td>' +
        '<td style="text-align:right"><button class="btn small go" type="button" data-ai-join="' + r.id + '">Join</button></td></tr>';
    }).join('');
    table.innerHTML = head + (rows || '<tr><td colspan="8" class="muted">No rounds in this world right now. ' +
      'Join opens a fresh one.</td></tr>');
  }

  function join(id) {
    if (!AI.world) return;
    var url = '/' + encodeURIComponent(AI.world) + '?instance=' + encodeURIComponent(id) + '&pin=1';
    window.open(url, '_blank', 'noopener');
  }

  // --------------------------------------------------------------- wiring
  function refresh() { loadWorlds().then(loadInstances); }

  function start() {
    AI.open = true;
    refresh();
    if (!AI.timer) AI.timer = setInterval(function () { if (AI.open && !document.hidden) refresh(); }, 5000);
  }

  function stop() {
    AI.open = false;
    if (AI.timer) { clearInterval(AI.timer); AI.timer = null; }
  }

  function bind() {
    var tabs = document.getElementById('admin-tabs');
    var panel = document.querySelector('[data-admin-panel="instances"]');
    if (!tabs || !panel) return;
    tabs.addEventListener('click', function (event) {
      var tab = event.target.closest('[data-admin-tab]');
      if (!tab) return;
      if (tab.dataset.adminTab === 'instances') start(); else stop();
    });
    panel.addEventListener('click', function (event) {
      var t = event.target.closest('[data-ai-world]');
      if (t) { AI.world = t.dataset.aiWorld; AI.rows = []; drawWorlds(); drawInstances(); loadInstances(); return; }
      t = event.target.closest('[data-ai-join]');
      if (t) { join(t.dataset.aiJoin); return; }
      if (event.target.closest('#ai-refresh')) refresh();
    });
    var sort = el('ai-sort');
    if (sort) sort.addEventListener('change', function () { AI.sort = sort.value; drawInstances(); });
    if (window.location.hash === '#instances') {
      var tab = tabs.querySelector('[data-admin-tab="instances"]');
      if (tab) tab.click();
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind);
  else bind();
})();
