/* The Bots Zone: the admin dashboard's control room for synthetic players.

   Everything here is drawn from /api/admin/bots/*.  The settings forms are
   generated from the schema the server sends (app/bots/config.py), so each
   subtab is: the feature's own on/off switch at the top, then every setting
   that belongs to that feature, each labelled with what kind of setting it
   is -- universal, a per-bot range, or a base each persona scales.

   Feature switches save the moment they are flipped.  Everything else is
   collected and saved together with the Save bar, which says how many
   settings are waiting. */
(function () {
  'use strict';

  var ICONS = {
    stats: '▣', creation: '✚', personas: '☺', presence: '☼',
    worlds: '◉', ingame: '⌖', friends: '❤', chatter: '✎',
    messages: '✉', llm: '⚙', prompts: '¶', modifiers: '⇅', speech: '✦'
  };
  var SCOPE_LABEL = { universal: 'Universal', 'per-bot': 'Per-bot range', base: 'Base × persona' };
  var SCOPE_HELP = {
    universal: 'One value for the whole platform.',
    'per-bot': 'Each bot draws its own value from inside this range once, nudged by its persona.',
    base: 'A platform-wide base that every bot scales by its own persona.'
  };
  var STATE_LABEL = { offline: 'Offline', waking: 'Settling in', online: 'Online', playing: 'In a world' };
  var NEXT_LABEL = { offline: 'comes online', waking: 'ready', online: 'next move', playing: 'leaves world' };

  var BZ = {
    ready: false, visible: false, sub: 'stats',
    schema: null, values: {}, dirty: {}, tags: [], tagCounts: {},
    overview: null, timer: 0,
    table: { q: '', state: '', world: '', tag: '', sort: 'recent', page: 0, size: 40, total: 0, rows: [] },
    drawer: null, logName: ''
  };

  function esc(v) { return Site.escape(v == null ? '' : String(v)); }
  function num(v) { return (Number(v) || 0).toLocaleString(); }
  function el(id) { return document.getElementById(id); }
  function ago(t) { return t ? Site.ago(t) : '--'; }
  function inFuture(t) {
    var d = Math.round(t - Date.now() / 1000);
    if (d <= 0) return 'now';
    if (d < 60) return 'in ' + d + 's';
    if (d < 3600) return 'in ' + Math.round(d / 60) + ' min';
    if (d < 86400) return 'in ' + (d / 3600).toFixed(1) + ' h';
    return 'in ' + Math.round(d / 86400) + ' d';
  }
  function hue(name) {
    var h = 0;
    for (var i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) % 360;
    return 'hsl(' + h + ',48%,46%)';
  }

  // ================================================================ boot
  function show() {
    BZ.visible = true;
    if (!BZ.ready) {
      BZ.ready = true;
      bindOnce();
      loadSchema().then(function () { refresh(); drawNav(); drawSub(); });
    } else {
      refresh();
    }
    clearInterval(BZ.timer);
    BZ.timer = setInterval(function () {
      var panel = document.querySelector('[data-admin-panel="bots"]');
      if (!panel || panel.classList.contains('hidden') || document.hidden) return;
      refresh();
    }, 3000);
  }

  function loadSchema() {
    return Site.get('/api/admin/bots/schema').then(function (res) {
      if (!res.ok) { Site.toast(res.error || 'Could not load the settings.', 'bad'); return; }
      BZ.schema = res.schema;
      BZ.values = res.values;
      BZ.tags = res.tags || [];
      BZ.tagCounts = res.tag_counts || {};
      BZ.schemaGroups = res.groups || [];
    });
  }

  function refresh() {
    return Site.get('/api/admin/bots/overview').then(function (res) {
      if (!res.ok) return;
      BZ.overview = res;
      drawHero();
      drawNav();
      updateLiveBits();
    }).catch(function () {
      var live = el('bz-live');
      if (live) live.textContent = 'offline';
    });
  }

  // ================================================================ hero
  function kpi(label, value, sub, color) {
    return '<dl class="bz-kpi" style="--kpi:' + color + '"><dt>' + esc(label) + '</dt><dd>' +
      value + '</dd>' + (sub ? '<small>' + sub + '</small>' : '') + '</dl>';
  }

  function drawHero() {
    var o = BZ.overview, s = o.stats || {};
    var master = el('bz-master');
    var on = !!BZ.values['system.enabled'];
    master.setAttribute('aria-checked', on ? 'true' : 'false');
    master.classList.add('bot');
    var dot = el('bz-tab-dot');
    if (dot) dot.classList.toggle('on', on && (s.online || 0) > 0);
    el('bz-master-note').textContent = !o.running ? 'The director is not running (started with --no-bots?).'
      : (on ? (s.loaded ? 'Running — ' + num(s.total) + ' bots, director tick ' +
                (s.tick_ms || 0) + ' ms' : 'Loading the population…')
            : 'Paused: nobody logs in, joins, comments or answers.');
    var worlds = s.worlds || {};
    var asleep = 0, liveBots = 0, liveInst = 0, humans = 0;
    Object.keys(worlds).forEach(function (id) {
      asleep += worlds[id].sleeping_instances || 0;
      liveBots += worlds[id].live_bots || 0;
      liveInst += worlds[id].active_instances || 0;
      humans += worlds[id].live_humans || 0;
    });
    var social = (o.chatter || {}).stats || {};
    var talk = (social.comments || 0) + (social.replies || 0) + (social.dms || 0) + (social.posts || 0);
    var llm = o.llm || {}, info = llm.info || {};
    var llmState = !llm.enabled ? 'off' : (llm.available && info.reachable ? 'ready'
      : (llm.down_for ? 'backing off ' + llm.down_for + 's' : 'unreachable'));
    var queue = 0;
    Object.keys(llm.queue || {}).forEach(function (k) { queue += llm.queue[k]; });
    el('bz-kpis').innerHTML =
      kpi('Bots', num(o.population), s.total !== o.population && s.loaded ? num(s.total) + ' loaded' : 'accounts', 'var(--bz-bot)') +
      kpi('Online', num(s.online), 'target ' + num(s.target_online), 'var(--bz-online)') +
      kpi('In worlds', num(s.playing), 'target ' + num(s.target_playing), 'var(--bz-playing)') +
      kpi('Offline', num(s.offline), Math.round((s.curve_now || 0) * 100) + '% wanted now', 'var(--bz-offline)') +
      kpi('Live rounds', num(liveInst), liveInst ? num(liveBots) + ' bots with ' + num(humans) +
          (humans === 1 ? ' person' : ' people') : 'nobody real is playing', 'var(--link)') +
      kpi('Asleep', num(asleep), 'rounds simulated for free', 'var(--bz-waking)') +
      kpi('Social', num(talk), num(social.requests_sent || 0) + ' friend requests, ' +
          num(social.likes || 0) + ' likes', 'var(--bz-bot)') +
      kpi('Language model', '<span class="' + (llmState === 'ready' ? 'bz-ok' : 'bz-bad') + '">' +
          esc(llmState) + '</span>', (llm.per_minute || 0) + '/min, ' + queue + ' queued', 'var(--bz-target)');
    drawActivity(el('bz-spark'), s.history || [], s.plan || []);
  }

  function hhmm(at) {
    var d = new Date(at * 1000);
    return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2);
  }

  function niceTop(v) {
    if (v <= 5) return 5;
    var mag = Math.pow(10, Math.floor(Math.log(v) / Math.LN10));
    var steps = [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10];
    for (var i = 0; i < steps.length; i++) if (steps[i] * mag >= v) return steps[i] * mag;
    return 10 * mag;
  }

  /* The hero chart: the target the peak curve asks for (dashed, six hours
     back and two ahead) with what the director actually did laid over it. */
  function drawActivity(canvas, history, plan) {
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var ratio = Math.min(2, window.devicePixelRatio || 1);
    var w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    canvas.width = Math.round(w * ratio);
    canvas.height = Math.round(h * ratio);
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, w, h);
    var style = getComputedStyle(document.documentElement);
    function color(name, fallback) { return style.getPropertyValue(name).trim() || fallback; }
    var c = { online: color('--bz-online', '#37c26a'), playing: color('--bz-playing', '#f0b429'),
              target: color('--bz-target', '#5a7fa8'), ink: color('--ink-soft', '#888'),
              line: color('--line-soft', '#ddd') };
    var now = Date.now() / 1000;
    if (!plan.length && !history.length) {
      ctx.fillStyle = color('--ink-soft', '#888');
      ctx.font = '11px Verdana, sans-serif';
      ctx.fillText(BZ.overview && BZ.overview.running ? 'Presence is switched off: nothing to plot.'
                   : 'The bot director is not running, so there is nothing to plot.', 12, h / 2 + 4);
      return;
    }
    var t0 = plan.length ? plan[0].at : now - 6 * 3600;
    var t1 = plan.length ? plan[plan.length - 1].at : now;
    history = history.filter(function (p) { return p.at >= t0; });
    var top = 1;
    plan.forEach(function (p) { top = Math.max(top, p.target); });
    history.forEach(function (p) { top = Math.max(top, p.online, p.playing); });
    top = niceTop(top * 1.08);
    var pad = { l: 38, r: 10, t: 10, b: 18 };
    var iw = w - pad.l - pad.r, ih = h - pad.t - pad.b;
    function X(at) { return pad.l + iw * (at - t0) / Math.max(1, t1 - t0); }
    function Y(v) { return pad.t + ih - ih * v / top; }
    ctx.font = '9px Verdana, sans-serif';
    ctx.lineWidth = 1;
    // grid and y labels
    [0, 0.5, 1].forEach(function (f) {
      var y = Math.round(Y(top * f)) + 0.5;
      ctx.strokeStyle = c.line;
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
      ctx.fillStyle = c.ink;
      ctx.textAlign = 'right';
      ctx.fillText(num(Math.round(top * f)), pad.l - 5, y + 3);
    });
    // the future is shaded
    var nx = Math.min(w - pad.r, Math.max(pad.l, X(now)));
    ctx.fillStyle = 'rgba(128,128,128,.07)';
    ctx.fillRect(nx, pad.t, w - pad.r - nx, ih);
    // hour ticks
    ctx.textAlign = 'center';
    ctx.fillStyle = c.ink;
    for (var at = Math.ceil(t0 / 3600) * 3600; at <= t1; at += 3600) {
      var x = X(at);
      ctx.fillRect(Math.round(x), pad.t + ih, 1, 3);
      ctx.fillText(hhmm(at), x, h - 4);
    }
    function path(points, key, stroke, dash, width) {
      if (!points.length) return;
      ctx.beginPath();
      points.forEach(function (p, i) {
        var x = X(p.at), y = Y(p[key] || 0);
        if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y);
      });
      if (points.length === 1) ctx.lineTo(X(points[0].at) + 2, Y(points[0][key] || 0));
      ctx.strokeStyle = stroke;
      ctx.lineWidth = width || 2;
      ctx.setLineDash(dash ? [4, 3] : []);
      ctx.stroke();
      ctx.setLineDash([]);
    }
    path(plan, 'target', c.target, true, 1.3);
    // soft fill under "online" so the shape reads at a glance
    if (history.length > 1) {
      ctx.beginPath();
      history.forEach(function (p, i) {
        if (i) ctx.lineTo(X(p.at), Y(p.online)); else ctx.moveTo(X(p.at), Y(p.online));
      });
      ctx.lineTo(X(history[history.length - 1].at), Y(0));
      ctx.lineTo(X(history[0].at), Y(0));
      ctx.closePath();
      ctx.fillStyle = 'rgba(55,194,106,.12)';
      ctx.fill();
    }
    path(history, 'playing', c.playing);
    path(history, 'online', c.online);
    history.slice(-1).forEach(function (p) {
      [['online', c.online], ['playing', c.playing]].forEach(function (k) {
        ctx.beginPath();
        ctx.arc(X(p.at), Y(p[k[0]]), 3, 0, Math.PI * 2);
        ctx.fillStyle = k[1];
        ctx.fill();
      });
    });
    // now marker
    ctx.strokeStyle = c.ink;
    ctx.setLineDash([2, 3]);
    ctx.beginPath(); ctx.moveTo(Math.round(nx) + 0.5, pad.t); ctx.lineTo(Math.round(nx) + 0.5, pad.t + ih); ctx.stroke();
    ctx.setLineDash([]);
    ctx.textAlign = nx > w - 40 ? 'right' : 'left';
    ctx.fillStyle = c.ink;
    ctx.fillText('now', nx > w - 40 ? nx - 4 : nx + 4, pad.t + 9);
    ctx.textAlign = 'left';
    if (history.length < 3) ctx.fillText('collecting — one sample a minute', pad.l + 6, pad.t + 9);
    ctx.textAlign = 'start';
  }

  function updateLiveBits() {
    var live = el('bz-live');
    if (live) live.textContent = 'live — ' + new Date().toLocaleTimeString();
    if (BZ.sub === 'stats') { drawWorldCards(); }
    if (BZ.sub === 'creation') { drawJob(); }
    if (BZ.sub === 'llm') { drawLLMStatus(); }
    if (BZ.sub === 'chatter' || BZ.sub === 'messages' || BZ.sub === 'friends') { drawFeeds(); }
    if (BZ.sub === 'presence') { drawCurve(); }
    if (BZ.sub === 'worlds') { drawWorldTable(); }
    if (BZ.sub === 'modifiers') { drawModifiers(); }
    if (BZ.sub === 'speech') { drawSpeech(); }
  }

  /* The presence curve: the share of bots the director keeps online over
     the next day, with the peak window shaded and a "now" marker. */
  function drawCurveChart(canvas, curve) {
    if (!canvas || !curve.length) return;
    var ctx = canvas.getContext('2d');
    var ratio = Math.min(2, window.devicePixelRatio || 1);
    var w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    canvas.width = Math.round(w * ratio);
    canvas.height = Math.round(h * ratio);
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, w, h);
    var style = getComputedStyle(document.documentElement);
    var ink = style.getPropertyValue('--ink-soft').trim() || '#888';
    var grid = style.getPropertyValue('--line-soft').trim() || '#ddd';
    var pad = { l: 38, r: 10, t: 12, b: 18 };
    var iw = w - pad.l - pad.r, ih = h - pad.t - pad.b;
    var t0 = curve[0].at, t1 = curve[curve.length - 1].at;
    function X(at) { return pad.l + iw * (at - t0) / Math.max(1, t1 - t0); }
    function Y(v) { return pad.t + ih - ih * v; }
    ctx.font = '9px Verdana, sans-serif';
    ctx.lineWidth = 1;
    [0, 0.25, 0.5, 0.75, 1].forEach(function (f) {
      var y = Math.round(Y(f)) + 0.5;
      ctx.strokeStyle = grid;
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
      ctx.fillStyle = ink;
      ctx.textAlign = 'right';
      ctx.fillText(Math.round(f * 100) + '%', pad.l - 5, y + 3);
    });
    ctx.textAlign = 'center';
    curve.forEach(function (p, i) {
      if (i % 6) return;
      ctx.fillText(hhmm(p.at), X(p.at), h - 4);
    });
    ctx.beginPath();
    curve.forEach(function (p, i) { if (i) ctx.lineTo(X(p.at), Y(p.share)); else ctx.moveTo(X(p.at), Y(p.share)); });
    ctx.lineTo(X(t1), Y(0));
    ctx.lineTo(X(t0), Y(0));
    ctx.closePath();
    ctx.fillStyle = 'rgba(154,95,224,.16)';
    ctx.fill();
    ctx.beginPath();
    curve.forEach(function (p, i) { if (i) ctx.lineTo(X(p.at), Y(p.share)); else ctx.moveTo(X(p.at), Y(p.share)); });
    ctx.strokeStyle = '#9a5fe0';
    ctx.lineWidth = 2;
    ctx.stroke();
    // the highest point, labelled
    var best = curve.reduce(function (a, p) { return p.share > a.share ? p : a; }, curve[0]);
    ctx.fillStyle = '#7b45c2';
    ctx.textAlign = 'left';
    ctx.fillText(Math.round(best.share * 100) + '% at ' + hhmm(best.at), Math.min(w - 90, X(best.at) + 4), Y(best.share) - 5);
    var nowAt = Date.now() / 1000;
    var nx = X(nowAt), share = curve[0].share;
    for (var i = 1; i < curve.length; i++) {
      if (curve[i].at >= nowAt) {
        var a = curve[i - 1], b = curve[i];
        share = a.share + (b.share - a.share) * (nowAt - a.at) / Math.max(1, b.at - a.at);
        break;
      }
    }
    ctx.strokeStyle = ink;
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 3]);
    ctx.beginPath(); ctx.moveTo(Math.round(nx) + 0.5, pad.t); ctx.lineTo(Math.round(nx) + 0.5, pad.t + ih); ctx.stroke();
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.arc(nx, Y(share), 3.5, 0, Math.PI * 2);
    ctx.fillStyle = '#9a5fe0';
    ctx.fill();
    ctx.fillStyle = ink;
    ctx.fillText('now ' + Math.round(share * 100) + '%', nx + 6, pad.t + 9);
    ctx.textAlign = 'start';
  }

  // ================================================================= nav
  function sectionOn(id) {
    if (!BZ.schema) return null;
    var toggles = BZ.schema.fields.filter(function (f) { return f.section === id && f.toggle; });
    if (!toggles.length) return null;
    return toggles.every(function (f) { return !!BZ.values[f.key]; });
  }

  function drawNav() {
    var nav = el('bz-nav');
    if (!nav || !BZ.schema) return;
    nav.innerHTML = BZ.schema.sections.map(function (sec) {
      var state = sectionOn(sec.id);
      return '<button type="button" data-bz-sub="' + sec.id + '" class="' +
        (BZ.sub === sec.id ? 'on' : '') + '" title="' + esc(sec.blurb) + '">' +
        '<span class="ico">' + (ICONS[sec.id] || '•') + '</span>' +
        '<span class="lbl">' + esc(sec.label) + '</span>' +
        '<span class="state ' + (state === null ? '' : (state ? 'on' : 'off')) + '"></span></button>';
    }).join('');
  }

  function sectionInfo(id) {
    return (BZ.schema.sections.filter(function (s) { return s.id === id; })[0]) || { label: id, blurb: '' };
  }

  function drawSub() {
    var main = el('bz-main');
    if (!main || !BZ.schema) return;
    var sec = sectionInfo(BZ.sub);
    var html = '';
    var extra = {
      stats: statsPane, creation: creationPane, personas: personasPane, presence: presencePane,
      worlds: worldsPane, ingame: null, friends: feedsPane, chatter: feedsPane,
      messages: feedsPane, llm: llmPane, prompts: promptsPane,
      modifiers: modifiersPane, speech: speechPane
    }[BZ.sub];
    html += '<div class="panel"><div class="panel-head purple"><span>' + (ICONS[BZ.sub] || '') + ' ' +
      esc(sec.label) + '</span><span class="head-links">' + esc(sec.blurb) + '</span></div>' +
      '<div class="panel-body">' + featureCards(BZ.sub) + (extra ? extra() : '') + '</div></div>';
    if (BZ.sub !== 'stats') html += settingsPanel(BZ.sub);
    main.innerHTML = html;
    afterDraw();
  }

  function afterDraw() {
    if (BZ.sub === 'stats') { drawWorldCards(); loadTable(); }
    if (BZ.sub === 'creation') { drawJob(); }
    if (BZ.sub === 'llm') { drawLLMStatus(); }
    if (BZ.sub === 'presence') { drawCurve(); }
    if (BZ.sub === 'worlds') { drawWorldTable(); }
    if (BZ.sub === 'friends' || BZ.sub === 'chatter' || BZ.sub === 'messages') { drawFeeds(); }
    if (BZ.sub === 'modifiers') { drawModifiers(); }
    if (BZ.sub === 'speech') { drawSpeech(); }
    syncBands();
  }

  // ============================================================ personas
  var GROUP_HELP = {
    schedule: 'When it tends to be online: shifts its own peak hours.',
    skill: 'Aim, reaction time and how well it finds its way around.',
    focus: 'What it does in a round: objectives, frags, exploring or messing about.',
    social: 'How many friends it wants and how often it comments and chats.',
    voice: 'How it types, in every message the model writes for it.',
    temper: 'How it takes losing, dying and trash talk.',
    weapon: 'The loadout it reaches for.',
    age: 'Slang and topics in its persona block.',
    world: 'Favourite worlds: weights where it queues.',
    interest: 'What it talks about on walls and in posts.',
    custom: 'Your own tags, from the Custom tags list below.'
  };

  function personasPane() {
    var groups = (BZ.schemaGroups || []);
    var bots = (BZ.overview && BZ.overview.population) || 0;
    var depth = BZ.values['friends.depth'] || 0;
    return '<p class="bz-lead">Every bot draws one tag from each <b>core</b> group, so the system always knows ' +
      'how to drive it, then a few extras. The tags are the bot: they set its traits (when it is online, ' +
      'how it plays, how it types), decide who it befriends — two bots need <b>' + depth +
      '</b> shared tag' + (depth === 1 ? '' : 's') + ' (Friends → depth) — and each tag\'s line below goes ' +
      'into the persona block the language model sees. Hover a tag for its line; weights below change how ' +
      'often new bots draw it.</p><div class="bz-groups">' + groups.map(function (g) {
        var tags = BZ.tags.filter(function (t) { return t.group === g.id; });
        if (!tags.length) return '';
        return '<div class="bz-group"><div class="bz-group-head"><b>' + esc(g.id) + '</b>' +
          (g.core ? '<span class="pill">every bot</span>' : '<span class="pill">up to ' + g.max + '</span>') +
          '</div><div class="tiny muted">' + esc(GROUP_HELP[g.id] || '') + '</div><div class="bz-tags">' +
          tags.map(function (t) {
            var count = BZ.tagCounts[t.id] || 0;
            return '<span class="bz-tag g-' + esc(g.id) + '" title="' + esc(t.prompt) + '">' + esc(t.label) +
              ' <small>' + (bots ? Math.round(count / bots * 100) + '%' : num(count)) + '</small></span>';
          }).join('') + '</div></div>';
      }).join('') + '</div>';
  }

  // ==================================================== feature switches
  function featureCards(section) {
    var toggles = BZ.schema.fields.filter(function (f) { return f.section === section && f.toggle; });
    if (section === 'stats') {
      toggles = toggles.filter(function (f) { return f.key !== 'system.enabled'; });
    }
    return toggles.map(function (f) {
      var on = !!BZ.values[f.key];
      return '<div class="bz-feature' + (on ? ' on' : '') + '">' +
        '<button class="switch big bot" type="button" role="switch" data-bz-toggle="' + f.key +
        '" aria-checked="' + (on ? 'true' : 'false') + '" aria-label="' + esc(f.label) + '"><i></i></button>' +
        '<div class="grow"><b>' + esc(f.label) + '</b><div class="tiny">' + esc(f.help) + '</div></div>' +
        '<span class="state-word">' + (on ? 'On' : 'Off') + '</span></div>';
    }).join('');
  }

  function flip(key, button) {
    var next = !BZ.values[key];
    var change = {};
    change[key] = next;
    button.disabled = true;
    Site.post('/api/admin/bots/config', { changes: change }).then(function (res) {
      button.disabled = false;
      if (!res.ok) { Site.toast(res.error, 'bad'); return; }
      BZ.values = res.values;
      Site.toast((next ? 'Switched on: ' : 'Switched off: ') + fieldOf(key).label);
      drawNav();
      if (key === 'system.enabled') { drawHero(); return; }
      var card = button.closest('.bz-feature');
      button.setAttribute('aria-checked', next ? 'true' : 'false');
      if (card) {
        card.classList.toggle('on', next);
        card.querySelector('.state-word').textContent = next ? 'On' : 'Off';
      }
    });
  }

  function fieldOf(key) {
    return BZ.schema.fields.filter(function (f) { return f.key === key; })[0] || { label: key };
  }

  // ============================================================ settings
  function settingsPanel(section) {
    var fields = BZ.schema.fields.filter(function (f) { return f.section === section && !f.toggle; });
    if (!fields.length) return '';
    return '<div class="panel"><div class="panel-head"><span>Settings</span>' +
      '<span class="head-links">' + legendHtml() + '</span></div><div class="panel-body">' +
      '<div class="bz-form" data-bz-form="' + section + '">' +
      fields.map(fieldHtml).join('') + '</div>' +
      '<div class="bz-savebar" id="bz-savebar"><span class="grow" id="bz-dirty-note">No unsaved changes.</span>' +
      '<button class="btn small" type="button" data-bz="reset" data-section="' + section + '">Reset to defaults</button>' +
      '<button class="btn small" type="button" data-bz="discard">Discard</button>' +
      '<button class="btn primary" type="button" data-bz="save">Save changes</button></div>' +
      '</div></div>';
  }

  function legendHtml() {
    return '<span class="bz-scope universal" title="' + esc(SCOPE_HELP.universal) + '">Universal</span> ' +
      '<span class="bz-scope per-bot" title="' + esc(SCOPE_HELP['per-bot']) + '">Per-bot range</span> ' +
      '<span class="bz-scope base" title="' + esc(SCOPE_HELP.base) + '">Base × persona</span>';
  }

  function current(key) {
    return Object.prototype.hasOwnProperty.call(BZ.dirty, key) ? BZ.dirty[key] : BZ.values[key];
  }

  function numberAttrs(f) {
    return (f.min != null ? ' min="' + f.min + '"' : '') + (f.max != null ? ' max="' + f.max + '"' : '') +
      (f.step != null ? ' step="' + f.step + '"' : '');
  }

  function fieldHtml(f) {
    var v = current(f.key);
    var wide = f.kind === 'textarea' || f.kind === 'weights' || f.kind === 'chances' ||
      (f.kind === 'list' && f.rows > 4);
    var ctl = '';
    var unit = f.unit ? '<span class="unit">' + esc(f.unit) + '</span>' : '';
    if (f.kind === 'bool') {
      ctl = '<button class="switch" type="button" role="switch" data-bz-bool="' + f.key +
        '" aria-checked="' + (v ? 'true' : 'false') + '"><i></i></button><span class="unit">' +
        (v ? 'On' : 'Off') + '</span>';
    } else if (f.kind === 'int' || f.kind === 'float' || f.kind === 'pct') {
      var span = (f.max != null && f.min != null) ? f.max - f.min : 0;
      var slider = span > 0 && span <= 100000 && !f.nullable;
      ctl = '<input type="number" data-bz-num="' + f.key + '"' + numberAttrs(f) + ' value="' +
        (v == null ? '' : v) + '"' + (f.nullable ? ' placeholder="from server"' : '') + '>' + unit +
        (slider ? '<input type="range" data-bz-slide="' + f.key + '"' + numberAttrs(f) + ' value="' +
          (v == null ? f.min : v) + '">' : '') +
        (f.nullable ? '<button class="btn small" type="button" data-bz-clear="' + f.key + '">Server</button>' : '');
    } else if (f.kind === 'range' || f.kind === 'hours') {
      var lo = v ? v[0] : '', hi = v ? v[1] : '';
      ctl = '<input type="number" data-bz-pair="' + f.key + '" data-i="0"' + numberAttrs(f) + ' value="' + lo + '">' +
        '<span class="sep">' + (f.kind === 'hours' ? 'to' : '–') + '</span>' +
        '<input type="number" data-bz-pair="' + f.key + '" data-i="1"' + numberAttrs(f) + ' value="' + hi + '">' + unit;
      ctl = '<div class="bz-ctl">' + ctl + '</div>' +
        (f.kind === 'hours' ? '<div class="bz-clock" data-bz-band="' + f.key + '"></div>'
                            : '<div class="bz-band" data-bz-band="' + f.key + '"></div>');
    } else if (f.kind === 'daterange') {
      ctl = '<div class="bz-ctl"><input type="date" data-bz-pair="' + f.key + '" data-i="0" value="' + esc(v[0] || '') +
        '"><span class="sep">to</span><input type="date" data-bz-pair="' + f.key + '" data-i="1" value="' +
        esc(v[1] || '') + '" placeholder="today"></div>';
    } else if (f.kind === 'text' || f.kind === 'secret') {
      ctl = '<input type="' + (f.kind === 'secret' ? 'password' : 'text') + '" data-bz-text="' + f.key +
        '" value="' + esc(v || '') + '" autocomplete="off" spellcheck="false">';
    } else if (f.kind === 'select') {
      ctl = '<select data-bz-text="' + f.key + '">' + (f.options || []).map(function (o) {
        return '<option value="' + esc(o[0]) + '"' + (o[0] === v ? ' selected' : '') + '>' + esc(o[1]) + '</option>';
      }).join('') + '</select>';
    } else if (f.kind === 'textarea') {
      ctl = '<textarea data-bz-text="' + f.key + '" rows="' + (f.rows || 6) + '">' + esc(v || '') + '</textarea>';
    } else if (f.kind === 'list') {
      ctl = '<textarea data-bz-list="' + f.key + '" rows="' + (f.rows || 4) + '">' + esc((v || []).join('\n')) +
        '</textarea><span class="unit" data-bz-count="' + f.key + '">' + (v || []).length + ' lines</span>';
    } else if (f.kind === 'chances') {
      ctl = chancesHtml(f, v || {});
    } else if (f.kind === 'weights') {
      ctl = weightsHtml(f, v || {});
    }
    if (f.kind !== 'range' && f.kind !== 'hours' && f.kind !== 'daterange' && f.kind !== 'weights' &&
        f.kind !== 'chances') {
      ctl = '<div class="bz-ctl">' + ctl + '</div>';
    }
    return '<div class="bz-field' + (wide ? ' wide' : '') + (Object.prototype.hasOwnProperty.call(BZ.dirty, f.key) ? ' dirty' : '') +
      '" data-bz-field="' + f.key + '"><div class="bz-field-head"><label>' + esc(f.label) + '</label>' +
      '<span class="bz-scope ' + f.scope + '" title="' + esc(SCOPE_HELP[f.scope] || '') + '">' +
      esc(SCOPE_LABEL[f.scope] || f.scope) + '</span></div>' + ctl +
      (f.help ? '<div class="help">' + esc(f.help) + '</div>' : '') + '</div>';
  }

  /* One row per speech event, grouped by the worlds it happens in. */
  function chancesHtml(f, v) {
    var out = '<div class="bz-chances">';
    var lastGroup = null;
    (f.options || []).forEach(function (o) {
      var id = o[0], label = o[1], group = o[2] || '', help = o[3] || '';
      if (group !== lastGroup) {
        out += '<h4>' + esc(group) + '</h4>';
        lastGroup = group;
      }
      var pct = v[id] != null ? v[id] : 0;
      out += '<div class="bz-chance' + (pct ? '' : ' off') + '"><span class="name">' + esc(label) +
        '<small>' + esc(help) + '</small></span>' +
        '<input type="range" min="0" max="100" step="1" value="' + pct + '" data-bz-chance="' + f.key +
        '" data-event="' + esc(id) + '"><output>' + (pct ? pct + '%' : 'off') + '</output></div>';
    });
    return out + '</div>';
  }

  function weightsHtml(f, v) {
    var options = f.options || [];
    var groups = {};
    var total = 0;
    options.forEach(function (o) { total += BZ.tagCounts[o[0]] || 0; });
    var bots = (BZ.overview && BZ.overview.population) || 0;
    var out = '<div class="bz-weights">';
    var lastGroup = null;
    options.forEach(function (o) {
      var id = o[0], label = o[1], group = o[2] || '';
      if (group !== lastGroup && group) {
        out += '<h4>' + esc(group) + '</h4>';
        lastGroup = group;
      }
      var w = v[id] != null ? v[id] : 1;
      var count = BZ.tagCounts[id];
      var share = bots && count != null ? Math.min(100, count / bots * 100) : 0;
      var tag = BZ.tags.filter(function (t) { return t.id === id; })[0] || {};
      out += '<div class="bz-weight" title="' + esc(tag.prompt || '') + '"><span class="name">' + esc(label) +
        '<small>' + (count != null ? num(count) + ' bots (' + share.toFixed(0) + '%)' : esc(id)) + '</small></span>' +
        '<input type="range" min="0" max="' + (f.max || 5) + '" step="' + (f.step || 0.1) + '" value="' + w +
        '" data-bz-weight="' + f.key + '" data-tag="' + esc(id) + '"><output>' + Number(w).toFixed(1) + '</output>' +
        (group !== 'world' ? '<span class="share"><i style="width:' + share + '%"></i></span>' : '') + '</div>';
      groups[group] = true;
    });
    return out + '</div>';
  }

  function markDirty(key, value) {
    if (JSON.stringify(value) === JSON.stringify(BZ.values[key])) {
      delete BZ.dirty[key];
    } else {
      BZ.dirty[key] = value;
    }
    var box = document.querySelector('[data-bz-field="' + key + '"]');
    if (box) box.classList.toggle('dirty', Object.prototype.hasOwnProperty.call(BZ.dirty, key));
    var count = Object.keys(BZ.dirty).length;
    var note = el('bz-dirty-note');
    if (note) note.textContent = count ? count + ' unsaved change' + (count === 1 ? '' : 's') + '.' : 'No unsaved changes.';
    var bar = el('bz-savebar');
    if (bar) bar.classList.toggle('dirty', !!count);
  }

  function syncBands() {
    document.querySelectorAll('[data-bz-band]').forEach(function (band) {
      var key = band.dataset.bzBand;
      var f = fieldOf(key);
      var v = current(key) || [0, 0];
      var lo = Number(v[0]), hi = Number(v[1]);
      if (f.kind === 'hours') {
        var start = (lo % 24) / 24 * 100, end = (hi % 24) / 24 * 100;
        band.innerHTML = end >= start
          ? '<i style="left:' + start + '%;width:' + (end - start) + '%"></i>'
          : '<i style="left:' + start + '%;right:0"></i><i style="left:0;width:' + end + '%"></i>';
        return;
      }
      var min = Number(f.min || 0), max = Number(f.max || 1);
      var a = (lo - min) / (max - min) * 100, b = (hi - min) / (max - min) * 100;
      band.innerHTML = '<i style="left:' + Math.max(0, a) + '%;width:' + Math.max(1, b - a) + '%"></i>';
    });
  }

  function save() {
    var changes = BZ.dirty;
    if (!Object.keys(changes).length) { Site.toast('Nothing to save.', 'info'); return; }
    Site.post('/api/admin/bots/config', { changes: changes }).then(function (res) {
      if (!res.ok) { Site.toast(res.error, 'bad'); return; }
      BZ.values = res.values;
      BZ.dirty = {};
      Site.toast('Saved ' + res.applied.length + ' setting' + (res.applied.length === 1 ? '' : 's') + '.');
      loadSchema().then(function () { drawNav(); drawSub(); });
    });
  }

  // ============================================================ stats pane
  function statsPane() {
    var worlds = (BZ.overview && BZ.overview.worlds) || [];
    var t = BZ.table;
    return '<div class="bz-worlds" id="bz-world-cards"></div>' +
      '<div class="bz-filters">' +
      '<input type="search" id="bz-q" placeholder="Search bots by name" value="' + esc(t.q) + '">' +
      '<div class="bz-seg" id="bz-state-seg">' + [['', 'All'], ['online', 'Online'], ['playing', 'In a world'],
        ['waking', 'Settling in'], ['offline', 'Offline']].map(function (o) {
        return '<button type="button" data-bz-state="' + o[0] + '" class="' + (t.state === o[0] ? 'on' : '') + '">' + o[1] + '</button>';
      }).join('') + '</div>' +
      '<select id="bz-world"><option value="">Any world</option>' + worlds.map(function (w) {
        return '<option value="' + esc(w.id) + '"' + (t.world === w.id ? ' selected' : '') + '>' + esc(w.name) + '</option>';
      }).join('') + '</select>' +
      '<select id="bz-tag"><option value="">Any tag</option>' + BZ.tags.map(function (tag) {
        return '<option value="' + esc(tag.id) + '"' + (t.tag === tag.id ? ' selected' : '') + '>' +
          esc(tag.label) + ' (' + esc(tag.group) + ')</option>';
      }).join('') + '</select>' +
      '</div>' +
      '<div class="bz-results"><span id="bz-result-count" class="muted">&nbsp;</span><label class="tiny">Sort by ' +
      '<select id="bz-sort">' + [['recent', 'Newest bots'], ['name', 'Name'], ['joined', 'Join date'],
        ['seen', 'Last seen']].map(function (o) {
        return '<option value="' + o[0] + '"' + (t.sort === o[0] ? ' selected' : '') + '>' + o[1] + '</option>';
      }).join('') + '</select></label></div>' +
      '<div class="tablewrap"><table class="bz-table" id="bz-table"><tr><th>Bot</th><th>State</th><th>Where</th>' +
      '<th class="hide-sm">Friends</th><th>Comments</th><th class="hide-sm">K / D</th><th class="hide-sm">Joined</th>' +
      '<th class="hide-sm" title="When the bot will next change what it is doing">Next</th></tr><tr><td colspan="8" class="muted">Loading…</td></tr></table></div>' +
      '<div class="bz-pager" id="bz-pager"></div>';
  }

  function drawWorldCards() {
    var box = el('bz-world-cards');
    if (!box || !BZ.overview) return;
    var stats = BZ.overview.stats || {}, worlds = stats.worlds || {};
    box.innerHTML = (BZ.overview.worlds || []).map(function (w) {
      var s = worlds[w.id] || {};
      var bots = (s.live_bots || 0) + (s.sleeping_bots || 0);
      var total = (s.live_humans || 0) + bots;
      var pct = function (n) { return total ? (n / total * 100) : 0; };
      var live = s.active_instances || 0, asleep = s.sleeping_instances || 0;
      var picked = BZ.table.world === w.id;
      return '<button type="button" class="bz-world' + (picked ? ' on' : '') + '" data-bz-world="' + esc(w.id) +
        '" title="Show the bots in ' + esc(w.name) + '"><span class="bz-world-head"><b>' + esc(w.name) + '</b>' +
        '<span class="bz-world-count">' + num(total) + '</span></span>' +
        '<span class="bz-split" title="people, bots in live rounds, bots in sleeping rounds">' +
        '<i class="p" style="width:' + pct(s.live_humans || 0) + '%"></i>' +
        '<i class="l" style="width:' + pct(s.live_bots || 0) + '%"></i>' +
        '<i class="s" style="width:' + pct(s.sleeping_bots || 0) + '%"></i></span>' +
        '<span class="tiny"><span><i class="k p"></i>' + num(s.live_humans) + ' people</span>' +
        '<span><i class="k l"></i>' + num(s.live_bots) + ' live</span>' +
        '<span><i class="k s"></i>' + num(s.sleeping_bots) + ' asleep</span></span>' +
        '<span class="tiny muted">' + (live ? num(live) + ' live round' + (live === 1 ? '' : 's') + ', ' : '') +
        num(asleep) + ' asleep round' + (asleep === 1 ? '' : 's') + '</span></button>';
    }).join('');
  }

  function loadTable() {
    var t = BZ.table;
    var qs = '?q=' + encodeURIComponent(t.q) + '&state=' + t.state + '&world=' + t.world +
      '&tag=' + encodeURIComponent(t.tag) + '&sort=' + t.sort + '&page=' + t.page + '&size=' + t.size;
    Site.get('/api/admin/bots/list' + qs).then(function (res) {
      if (!res.ok) return;
      t.total = res.total;
      t.rows = res.rows;
      drawTable();
    });
  }

  function drawTable() {
    var table = el('bz-table');
    if (!table) return;
    var t = BZ.table;
    var head = table.rows[0].outerHTML;
    var rows = t.rows.map(function (r) {
      var where = r.state === 'playing'
        ? esc(r.world) + '<span class="bz-sub">#' + r.instance + (r.live ? ' • live with people' : ' • asleep') + '</span>'
        : '<span class="muted">—</span>';
      var kd = r.deaths ? (r.kills / r.deaths).toFixed(2) : (r.kills ? r.kills.toFixed(0) : '0');
      return '<tr data-bz-open="' + r.id + '"><td><div class="bz-who"><span class="bz-avatar" style="background:' +
        hue(r.name) + '">' + esc(r.name.charAt(0).toUpperCase()) + '</span><div><b>' + esc(r.name) + '</b>' +
        (r.banned ? ' <span class="pill red">suspended</span>' : '') +
        '<div class="bz-tags">' + r.tags.slice(0, 6).map(function (tag) {
          return '<span class="bz-tag g-' + esc(tag.group) + '">' + esc(tag.label) + '</span>';
        }).join('') + (r.tags.length > 6 ? '<span class="bz-tag">+' + (r.tags.length - 6) + '</span>' : '') +
        '</div></div></div></td>' +
        '<td><span class="bz-state ' + r.state + '"><i></i>' + (STATE_LABEL[r.state] || r.state) + '</span>' +
        '<span class="bz-sub">for ' + ago(r.since).replace(' ago', '') + '</span></td>' +
        '<td>' + where + '</td>' +
        '<td class="hide-sm bz-num">' + r.friends + ' / ' + r.friend_target +
        '<div class="bz-meter"><i style="width:' + Math.min(100, r.friend_target ? r.friends / r.friend_target * 100 : 0) + '%"></i></div></td>' +
        '<td><span class="bz-num">' + num(r.comments) + '</span>' + (r.last_comment ? '<div class="bz-quote">“' +
          esc(r.last_comment) + '” <span class="muted">' + ago(r.last_comment_at) + '</span></div>' : '') + '</td>' +
        '<td class="hide-sm bz-num">' + num(r.kills) + ' / ' + num(r.deaths) + '<span class="bz-sub">K/D ' + kd + '</span></td>' +
        '<td class="hide-sm bz-num">' + new Date(r.joined * 1000).toLocaleDateString() + '</td>' +
        '<td class="hide-sm bz-num">' + (r.next_at ? '<span class="bz-sub">' + (NEXT_LABEL[r.state] || 'next') +
          '</span>' + inFuture(r.next_at) : '—') + '</td></tr>';
    }).join('');
    if (!rows) rows = '<tr><td colspan="8" class="muted">No bots match. Create some in Bot Creation.</td></tr>';
    table.innerHTML = head + rows;
    var count = el('bz-result-count');
    if (count) count.textContent = num(t.total) + ' bot' + (t.total === 1 ? '' : 's') +
      (t.q || t.state || t.world || t.tag ? ' match' + (t.total === 1 ? 'es' : '') : '');
    var pages = Math.max(1, Math.ceil(t.total / t.size));
    el('bz-pager').innerHTML = '<span>' + num(t.total) + ' bot' + (t.total === 1 ? '' : 's') + '</span>' +
      '<span><button class="btn small" type="button" data-bz="prev"' + (t.page <= 0 ? ' disabled' : '') + '>&laquo; Prev</button> ' +
      'page ' + (t.page + 1) + ' of ' + pages +
      ' <button class="btn small" type="button" data-bz="next"' + (t.page + 1 >= pages ? ' disabled' : '') + '>Next &raquo;</button></span>';
  }

  // ============================================================== drawer
  function openBot(id) {
    Site.get('/api/admin/bots/detail?id=' + id).then(function (res) {
      if (!res.ok) { Site.toast(res.error, 'bad'); return; }
      BZ.drawer = res;
      BZ.logName = '';
      drawDrawer();
      el('bz-drawer').classList.remove('hidden');
    });
  }

  function traitBars(traits) {
    var keys = ['skill', 'aggression', 'objective', 'support', 'explore', 'chaos', 'social', 'chatty',
                'selective', 'kindness', 'toxicity', 'activity', 'gamer', 'collector'];
    return '<div class="bz-traits">' + keys.map(function (k) {
      var v = Math.max(0, Math.min(1, Number(traits[k] || 0)));
      return '<div class="bz-trait"><span>' + k + '</span><span class="bar"><i style="width:' + (v * 100) +
        '%"></i></span><span class="bz-num">' + v.toFixed(2) + '</span></div>';
    }).join('') + '</div>';
  }

  function drawDrawer() {
    var d = BZ.drawer, b = d.bot, p = d.presence || {};
    el('bz-drawer-title').textContent = b.name;
    var worlds = (BZ.overview && BZ.overview.worlds) || [];
    var html = '<section><div class="bz-who"><span class="bz-avatar" style="width:44px;height:44px;font-size:18px;background:' +
      hue(b.name) + '">' + esc(b.name.charAt(0).toUpperCase()) + '</span><div><b style="font-size:14px">' + esc(b.name) +
      '</b> <span class="pill bot">bot</span><div class="tiny muted">' + esc(b.blurb || '(no about-me)') +
      (b.location ? ' • ' + esc(b.location) : '') + '</div>' +
      '<div class="tiny"><span class="bz-state ' + (p.state || 'offline') + '"><i></i>' + (STATE_LABEL[p.state] || 'Offline') +
      '</span>' + (p.world ? ' in ' + esc(p.world) + ' #' + p.instance + (p.live ? ' (live)' : ' (asleep)') : '') +
      '</div></div></div></section>';
    html += '<section><h4>Controls</h4><div class="bz-actions">' +
      '<button class="btn small go" type="button" data-bz-act="online">Bring online</button>' +
      '<button class="btn small" type="button" data-bz-act="offline">Send offline</button>' +
      '<button class="btn small" type="button" data-bz-act="leave">Leave world</button>' +
      '<select id="bz-act-world">' + worlds.map(function (w) {
        return '<option value="' + esc(w.id) + '">' + esc(w.name) + '</option>';
      }).join('') + '</select><button class="btn small primary" type="button" data-bz-act="join">Send to world</button>' +
      '<a class="btn small" href="/profile/' + encodeURIComponent(b.name) + '" target="_blank" rel="noopener">Profile</a>' +
      '<button class="btn small" type="button" data-admin-open="' + esc(b.name) + '">Manage account</button>' +
      '<button class="btn small danger" type="button" data-bz-delete-one="' + b.id + '">Delete bot</button></div></section>';
    html += '<section><h4>Persona</h4><div class="bz-tags" style="margin-bottom:6px">' + d.tags.map(function (t) {
      return '<span class="bz-tag g-' + esc(t.group) + '" title="' + esc(t.prompt) + '">' + esc(t.label) + '</span>';
    }).join('') + '</div><div class="bz-list">' + d.tags.map(function (t) {
      return '<div class="tiny">• ' + esc(t.prompt) + '</div>';
    }).join('') + (d.style.length ? '<div class="tiny"><b>Types:</b> ' + esc(d.style.join(' ')) + '</div>' : '') + '</div></section>';
    html += '<section><h4>Traits</h4>' + traitBars(d.traits) + '</section>';
    html += '<section><h4>Schedule</h4><dl class="bz-kv">' +
      '<dt>State since</dt><dd>' + ago(p.since) + '</dd>' +
      '<dt>Next change</dt><dd>' + (p.next_at ? inFuture(p.next_at) : '--') + '</dd>' +
      (p.session_end ? '<dt>Session ends</dt><dd>' + inFuture(p.session_end) + '</dd>' : '') +
      (p.state === 'waking' ? '<dt>Ready</dt><dd>' + inFuture(p.ready_at) + ' (online delay)</dd>' : '') +
      '<dt>Joined</dt><dd>' + new Date(b.joined * 1000).toLocaleDateString() + '</dd>' +
      '<dt>Noogets</dt><dd>' + num(b.credits) + '</dd><dt>Place visits</dt><dd>' + num(b.visits) + '</dd>' +
      '<dt>Waiting replies</dt><dd>' + ((d.pending || {}).dms || 0) + ' DMs, ' + ((d.pending || {}).walls || 0) + ' wall comments</dd>' +
      '<dt>Text from</dt><dd>' + esc(b.generator || '?') + '</dd>' +
      '<dt>Folder</dt><dd class="tiny">' + esc(b.folder) + '</dd></dl></section>';
    html += '<section><h4>Friends (' + (p.friends || 0) + ' of a wanted ' + (p.friend_target || 0) + ')</h4>' +
      '<div class="bz-tags">' + (d.friends.length ? d.friends.map(function (f) {
        return '<span class="bz-tag' + (f.is_bot ? '' : ' g-world') + '" title="' + (f.shared != null ? f.shared + ' shared tags' : 'a real player') +
          '">' + esc(f.username) + (f.shared != null ? ' ·' + f.shared : ' ★') + '</span>';
      }).join('') : '<span class="muted tiny">No friends yet.</span>') + '</div></section>';
    html += '<section><h4>Comments it wrote</h4><div class="bz-list">' + (d.written.length ? d.written.map(function (c) {
      return '<div class="row">“' + esc(c.body) + '”<div class="tiny">on ' + esc(c.wall) + '’s profile • ' + ago(c.created_at) + '</div></div>';
    }).join('') : '<span class="muted tiny">None yet.</span>') + '</div></section>';
    html += '<section><h4>Its comment section</h4><div class="bz-list">' + (d.wall.length ? d.wall.map(function (c) {
      return '<div class="row"><b>' + esc(c.author) + '</b>' + (c.is_bot ? '' : ' ★') + ': ' + esc(c.body) +
        '<div class="tiny">' + ago(c.created_at) + '</div></div>';
    }).join('') : '<span class="muted tiny">Empty.</span>') + '</div></section>';
    var stats = (d.stats || {}).total || {};
    html += '<section><h4>Game statistics</h4><dl class="bz-kv"><dt>Kills / deaths</dt><dd>' + num(stats.kills) + ' / ' +
      num(stats.deaths) + ' (K/D ' + (stats.kdr || 0) + ')</dd><dt>Rounds / wins</dt><dd>' + num(stats.rounds) + ' / ' +
      num(stats.wins) + '</dd><dt>Playtime</dt><dd>' + Math.round((stats.playtime || 0) / 3600) + ' h</dd></dl></section>';
    html += '<section><h4>Logs (its own folder)</h4><div class="bz-logs">' + (d.logs.length ? d.logs.map(function (l) {
      return '<button type="button" data-bz-log="' + esc(l.name) + '" class="' + (BZ.logName === l.name ? 'on' : '') + '">' +
        esc(l.name) + ' <span class="muted">' + Math.ceil(l.bytes / 1024) + 'k</span></button>';
    }).join('') : '<span class="muted tiny">No conversations logged yet.</span>') + '</div>' +
      '<div class="bz-logview hidden" id="bz-logview"></div></section>';
    el('bz-drawer-body').innerHTML = html;
  }

  function openLog(name) {
    var d = BZ.drawer;
    Site.get('/api/admin/bots/log?id=' + d.bot.id + '&name=' + encodeURIComponent(name)).then(function (res) {
      if (!res.ok) { Site.toast(res.error, 'bad'); return; }
      BZ.logName = name;
      document.querySelectorAll('[data-bz-log]').forEach(function (b) {
        b.classList.toggle('on', b.dataset.bzLog === name);
      });
      var view = el('bz-logview');
      view.classList.remove('hidden');
      view.innerHTML = res.entries.length ? res.entries.map(function (e) {
        return '<div class="line' + (e.who === d.bot.name ? ' me' : '') + '"><span class="t">' +
          (e.at ? new Date(e.at * 1000).toLocaleString() : '') + '</span><b>' + esc(e.who) + '</b>' +
          (e.tag ? ' <span class="muted tiny">(' + esc(e.tag) + ')</span>' : '') + ': ' + esc(e.text) + '</div>';
      }).join('') : '<span class="muted">Empty.</span>';
      view.scrollTop = view.scrollHeight;
    });
  }

  function botAction(action) {
    var d = BZ.drawer;
    var world = el('bz-act-world') ? el('bz-act-world').value : '';
    Site.post('/api/admin/bots/action', { id: d.bot.id, action: action, world: world }).then(function (res) {
      if (!res.ok) { Site.toast(res.error, 'bad'); return; }
      Site.toast(d.bot.name + ': ' + res.result);
      d.presence = res.presence;
      drawDrawer();
      if (BZ.sub === 'stats') loadTable();
    });
  }

  // ======================================================== creation pane
  function creationPane() {
    return '<div class="bz-grid2"><div><b>Generate bots now</b>' +
      '<p class="tiny muted">Each one gets a name (the model is shown your example usernames, told about any that are ' +
      'taken, and asked again), a persona, a profile, items, an outfit, a play history and friends — in that order, ' +
      'written in one transaction per batch.</p>' +
      '<div class="bz-generate"><input type="number" id="bz-count" min="1" max="100000" value="10">' +
      '<button class="btn go" type="button" data-bz="generate">Generate</button>' +
      '<button class="btn small" type="button" data-bz="cancel-job">Stop the job</button></div>' +
      '<div id="bz-job"></div></div>' +
      '<div><b>Preview the built-in name generator</b><p class="tiny muted">What the fallback produces when the model ' +
      'is unavailable (or chosen as the only source).</p>' +
      '<button class="btn small" type="button" data-bz="names">Show 24 names</button><div class="bz-names" id="bz-names"></div>' +
      '<div class="bz-danger" style="margin-top:12px"><b>Delete every bot</b><p class="tiny">Removes all bot accounts, their ' +
      'comments, posts, friendships and folders. Real players are never touched. Type <code>DELETE ALL BOTS</code> to confirm.</p>' +
      '<div class="inline-form"><input type="text" id="bz-confirm" placeholder="DELETE ALL BOTS">' +
      '<button class="btn small danger" type="button" data-bz="delete-all">Delete all bots</button></div></div></div></div>';
  }

  function drawJob() {
    var box = el('bz-job');
    if (!box || !BZ.overview) return;
    var status = BZ.overview.job || {}, job = status.job;
    var html = '';
    if (job) {
      var pct = job.total ? Math.min(100, job.done / job.total * 100) : 0;
      html += '<div class="bz-job"><b>' + (job.kind === 'delete' ? 'Deleting' : 'Creating') + ' ' + num(job.total) +
        ' bot' + (job.total === 1 ? '' : 's') + '</b> ' + (job.running ? '<span class="loading"></span>' : '<span class="pill green">done</span>') +
        '<div class="progress"><i style="width:' + pct + '%"></i></div><div class="tiny">' + num(job.done) + ' done' +
        (job.failed ? ', ' + num(job.failed) + ' failed' : '') +
        (job.kind === 'create' ? ' • names: ' + num(job.names_llm || 0) + ' from the model, ' + num(job.names_generated || 0) +
          ' generated, ' + num(job.duplicates || 0) + ' duplicates refused • profiles from the model: ' + num(job.profiles_llm || 0) : '') +
        '</div><div class="bz-joblog">' + (job.log || []).slice().reverse().map(function (l) {
          return new Date(l.at * 1000).toLocaleTimeString() + '  ' + esc(l.text);
        }).join('<br>') + '</div></div>';
    }
    var history = (status.history || []).slice().reverse();
    if (history.length) {
      html += '<div class="tiny muted" style="margin-top:6px">Recent jobs: ' + history.slice(0, 5).map(function (h) {
        return (h.kind === 'delete' ? 'deleted ' : 'created ') + num(h.done) + (h.origin === 'auto' ? ' (auto)' : '') +
          ' ' + ago(h.finished);
      }).join(' • ') + '</div>';
    }
    box.innerHTML = html;
  }

  // ======================================================== presence pane
  function presencePane() {
    return '<p class="bz-intro">The purple curve is the share of all bots the director keeps online through the next 24 hours, ' +
      'from the peak, off-peak and ramp settings below. Individual bots keep their own hours: night owls come on later, ' +
      'early birds earlier, and the controller wakes whoever suits the moment.</p>' +
      '<canvas class="bz-chart tall" id="bz-curve"></canvas>';
  }

  function drawCurve() {
    var canvas = el('bz-curve');
    if (canvas && BZ.overview) drawCurveChart(canvas, BZ.overview.curve || []);
  }

  // ========================================================== worlds pane
  function worldsPane() {
    return '<p class="bz-intro">Bots only run on a game host in rounds a real player is in. Everywhere else a round ' +
      'sleeps: its score, clock and objective carry on in closed form, it shows in every player count and list, and it ' +
      'costs nothing until somebody presses Join — then it wakes mid-round.</p><div class="tablewrap">' +
      '<table class="grid" id="bz-world-table"></table></div>' +
      '<h4 class="bz-h">Rounds right now</h4><div class="bz-rounds" id="bz-rounds"></div>';
  }

  function drawWorldTable() {
    var table = el('bz-world-table');
    if (!table || !BZ.overview) return;
    var worlds = (BZ.overview.stats || {}).worlds || {};
    table.innerHTML = '<tr><th>World</th><th>People</th><th>Bots with people</th><th>Bots asleep</th>' +
      '<th>Live rounds</th><th>Sleeping rounds</th></tr>' + (BZ.overview.worlds || []).map(function (w) {
        var s = worlds[w.id] || {};
        return '<tr><td><b>' + esc(w.name) + '</b></td><td>' + num(s.live_humans) + '</td><td>' + num(s.live_bots) +
          '</td><td>' + num(s.sleeping_bots) + '</td><td>' + num(s.active_instances) + '</td><td>' +
          num(s.sleeping_instances) + '</td></tr>';
      }).join('');
    Site.get('/api/admin/bots/rounds').then(function (res) {
      var box = el('bz-rounds');
      if (!box || !res.ok) return;
      box.innerHTML = (BZ.overview.worlds || []).map(function (w) {
        var info = res.rounds[w.id] || { rows: [], hidden: 0 };
        var rows = info.rows.map(function (r) {
          var fill = r.max ? Math.min(100, (r.bots + r.humans) / r.max * 100) : 0;
          return '<div class="bz-round ' + r.state + '"><span class="bz-round-id">#' + r.id + '</span>' +
            '<span class="bz-round-state">' + (r.state === 'live' ? 'live' : 'asleep') + '</span>' +
            '<span class="bz-round-who">' + (r.humans ? num(r.humans) + ' ' + (r.humans === 1 ? 'person' : 'people') + ' + ' : '') +
            num(r.bots) + ' bot' + (r.bots === 1 ? '' : 's') + ' <span class="muted">/ ' + r.max + '</span></span>' +
            '<span class="bz-meter"><i style="width:' + fill + '%"></i></span>' +
            '<span class="bz-round-score">' + esc(r.summary || ('round ' + r.round)) +
            (r.phase && r.phase !== 'active' ? ' <span class="muted">(' + esc(r.phase) + ')</span>' : '') + '</span></div>';
        }).join('') || '<div class="muted tiny">No rounds.</div>';
        return '<div class="bz-round-world"><b>' + esc(w.name) + '</b>' + rows +
          (info.hidden ? '<div class="muted tiny">…and ' + num(info.hidden) + ' more asleep</div>' : '') + '</div>';
      }).join('');
    });
  }

  // ============================================================ feed panes
  var FEEDS = {
    friends: { title: 'Latest friendships', empty: 'No bot has a friend yet.',
      cells: function (s) {
        return [['Requests sent', s.requests_sent], ['Accepted', s.accepted], ['Declined', s.declined],
                ['Follows', s.follows]];
      } },
    chatter: { title: 'Latest comments and posts', empty: 'Nothing written yet.',
      cells: function (s, c) {
        return [['Comments', s.comments], ['Wall replies', s.replies], ['Posts', s.posts], ['Likes', s.likes],
                ['Held back (budget)', s.deferred], ['Waiting wall replies', c.pending_walls]];
      } },
    messages: { title: 'Latest direct messages', empty: 'No messages to or from a bot yet.',
      cells: function (s, c, g, game) {
        return [['DMs answered', s.dms], ['Waiting DMs', c.pending_dms], ['Chat heard', g.heard],
                ['Chat answered', g.answered], ['Live chat rooms', game.rooms]];
      } }
  };

  function feedsPane() {
    var f = FEEDS[BZ.sub];
    BZ.feedAt = 0;
    return '<div class="bz-grid2 bz-feeds"><div><div class="bz-feed-head"><b>' + esc(f.title) +
      '</b><span class="muted tiny">newest first · click a bot to open it</span></div>' +
      '<div class="bz-feed tall" id="bz-feed-db"><span class="muted tiny">Loading…</span></div></div>' +
      '<div><div class="bz-feed-head"><b>Since the server started</b></div><div class="bz-status compact" id="bz-feed-stats"></div>' +
      (BZ.sub === 'messages' ? '<div class="bz-feed-head" style="margin-top:10px"><b>In-game chat answered</b></div>' +
        '<div class="bz-feed" id="bz-feed-chat"></div>' : '') + '</div></div>';
  }

  function person(name, id, bot) {
    if (!name) return '';
    return bot ? '<a href="#" class="bz-name bot" data-bz-open="' + id + '">' + esc(name) + '</a>'
               : '<a href="/profile/' + encodeURIComponent(name) + '" class="bz-name" target="_blank">' + esc(name) +
                 '</a> <span class="pill tiny-pill">real</span>';
  }

  var FEED_VERB = { request: 'sent a friend request to', friends: 'is friends with', comment: 'on',
                    post: 'posted', dm: 'to' };

  function loadFeed() {
    var kind = BZ.sub;
    Site.get('/api/admin/bots/feed?kind=' + kind).then(function (res) {
      var box = el('bz-feed-db');
      if (!box || !res.ok || BZ.sub !== kind) return;
      box.innerHTML = res.rows.length ? res.rows.map(function (r) {
        var line = person(r.who, r.who_id, r.who_bot);
        if (r.kind === 'post') line += ' posted';
        else line += ' <span class="muted">' + FEED_VERB[r.kind] + '</span> ' + person(r.to, r.to_id, r.to_bot);
        return '<div class="row"><span class="t">' + ago(r.at) + '</span><span class="k ' + r.kind + '">' +
          esc(r.kind) + '</span>' + line + (r.text ? '<div class="say">' + esc(r.text) + '</div>' : '') +
          (r.likes ? '<span class="muted tiny"> ♥ ' + num(r.likes) + '</span>' : '') + '</div>';
      }).join('') : '<span class="muted tiny">' + esc(FEEDS[kind].empty) + '</span>';
    });
  }

  function drawFeeds() {
    if (!BZ.overview || !FEEDS[BZ.sub]) return;
    var chatter = BZ.overview.chatter || {}, game = BZ.overview.gamechat || {};
    if (Date.now() - (BZ.feedAt || 0) > 10000) {
      BZ.feedAt = Date.now();
      loadFeed();
    }
    var chat = el('bz-feed-chat');
    if (chat) {
      var lines = (game.recent || []).slice().reverse();
      chat.innerHTML = lines.length ? lines.map(function (r) {
        return '<div class="row"><span class="t">' + ago(r.at) + '</span><span class="k">' + esc(r.world) + '</span><b>' +
          esc(r.who) + '</b> <span class="muted">to</span> ' + esc(r.to) + '<div class="say">' + esc(r.text) + '</div></div>';
      }).join('') : '<span class="muted tiny">No bot has answered anybody in a round yet.</span>';
    }
    var stats = el('bz-feed-stats');
    if (stats) {
      stats.innerHTML = FEEDS[BZ.sub].cells(chatter.stats || {}, chatter, game.stats || {}, game).map(function (c) {
        return '<dl class="cell"><dt>' + esc(c[0]) + '</dt><dd>' + num(c[1]) + '</dd></dl>';
      }).join('');
    }
  }

  // ======================================================= modifiers pane
  function modifiersPane() {
    return '<p class="bz-intro">Modifiers are short-lived: they start when a conversation does and fade ' +
      'away once it goes quiet. Below is what is active right now.</p>' +
      '<div class="bz-grid2"><div><div class="bz-feed-head"><b>DM conversations with momentum</b>' +
      '<span class="muted tiny">fades after the decay time</span></div><div id="bz-mod-dm"></div></div>' +
      '<div><div class="bz-feed-head"><b>Rounds with chat heat</b><span class="muted tiny">' +
      'players talking, buzz after events</span></div><div id="bz-mod-heat"></div>' +
      '<div class="bz-feed-head" style="margin-top:10px"><b>Since the server started</b></div>' +
      '<div class="bz-status compact" id="bz-mod-stats"></div></div></div>';
  }

  function meter(pct) {
    return '<span class="bz-meter wide"><i style="width:' + Math.max(0, Math.min(100, pct)) + '%"></i></span>';
  }

  function drawModifiers() {
    if (!BZ.overview) return;
    var chatter = BZ.overview.chatter || {}, game = BZ.overview.gamechat || {};
    var dm = el('bz-mod-dm');
    if (dm) {
      var rows = chatter.momentum || [];
      var decay = Number(BZ.values['modifiers.dm_decay_seconds']) || 60;
      dm.innerHTML = rows.length ? '<table class="grid bz-mod-table"><tr><th>Bot</th><th>Talking with</th>' +
        '<th>Turns</th><th>Replies sooner</th><th>Fades in</th></tr>' + rows.map(function (r) {
          return '<tr><td><a href="#" class="bz-name bot" data-bz-open="' + r.bot + '">' + esc(r.bot_name || ('#' + r.bot)) +
            '</a></td><td>' + esc(r.other_name || ('#' + r.other)) + '<span class="bz-sub">' +
            (r.waiting_on === 'human' ? 'bot is typing' : 'waiting on them') + '</span></td><td class="bz-num">' +
            r.turns + '</td><td class="bz-num">' + (r.speedup ? r.speedup + '%' : '<span class="muted">not yet</span>') +
            meter(r.speedup) + '</td><td class="bz-num">' + Math.round(r.fades_in) + 's' +
            meter(r.fades_in / decay * 100) + '</td></tr>';
        }).join('') + '</table>' : '<span class="muted tiny">Nobody is trading messages with a bot right now.</span>';
    }
    var heat = el('bz-mod-heat');
    if (heat) {
      var rooms = game.heat || [];
      heat.innerHTML = rooms.length ? '<table class="grid bz-mod-table"><tr><th>Round</th><th>Talking</th>' +
        '<th>Heat</th><th>Reply odds</th><th>Buzz</th></tr>' + rooms.map(function (r) {
          return '<tr><td><b>' + esc(r.world_name) + '</b> <span class="muted">#' + r.inst + '</span></td><td>' +
            esc((r.talking || []).join(', ')) + '</td><td class="bz-num">' + r.heat.toFixed(1) +
            meter(r.heat / 5 * 100) + '</td><td class="bz-num">×' + r.multiplier.toFixed(2) + '</td><td class="bz-num">' +
            (r.buzz > 1.001 ? '×' + r.buzz.toFixed(2) : '<span class="muted">—</span>') + '</td></tr>';
        }).join('') + '</table>' : '<span class="muted tiny">No real player is talking in a round right now.</span>';
    }
    var stats = el('bz-mod-stats');
    if (stats) {
      var c = chatter.stats || {}, g = game.stats || {};
      stats.innerHTML = [['DMs answered sooner', c.quickened], ['In-game answers', g.answered],
        ['Second voices', g.second_voices], ['Bot-to-bot replies', g.bot_replies],
        ['Skipped (odds)', g.skipped], ['Held back (budget)', g.budget]].map(function (x) {
        return '<dl class="cell"><dt>' + esc(x[0]) + '</dt><dd>' + num(x[1]) + '</dd></dl>';
      }).join('');
    }
  }

  // ========================================================= speech pane
  function speechPane() {
    return '<p class="bz-intro">Each event is reported by the game host only from rounds a real player is in. ' +
      'The bots in that round see it from their own side (their flag or the enemy\'s, attacking or ' +
      'defending), and the chance below decides whether anyone says something about it.</p>' +
      '<div class="bz-grid2"><div><div class="bz-feed-head"><b>Latest events</b>' +
      '<span class="muted tiny">newest first</span></div><div class="bz-feed tall" id="bz-speech-feed"></div></div>' +
      '<div><div class="bz-feed-head"><b>Since the server started</b></div>' +
      '<div class="bz-status compact" id="bz-speech-stats"></div>' +
      '<div class="bz-feed-head" style="margin-top:10px"><b>What bots said</b></div>' +
      '<div class="bz-feed" id="bz-speech-said"></div></div></div>';
  }

  function drawSpeech() {
    if (!BZ.overview) return;
    var game = BZ.overview.gamechat || {};
    var feed = el('bz-speech-feed');
    if (feed) {
      var events = (game.events || []).slice().reverse();
      var worlds = {};
      (BZ.overview.worlds || []).forEach(function (w) { worlds[w.id] = w.name; });
      feed.innerHTML = events.length ? events.map(function (e) {
        return '<div class="row"><span class="t">' + ago(e.at) + '</span><span class="k">' + esc(e.label) +
          '</span>' + esc(worlds[e.world] || e.world) + ' <span class="muted">#' + e.inst + '</span>' +
          '<div class="say">' + (e.voices && e.voices.length ? esc(e.voices.join(', ')) + ' reacted'
            : '<span class="muted">' + esc(e.outcome || '') + '</span>') + '</div></div>';
      }).join('') : '<span class="muted tiny">No events yet: they come from rounds with a real player in them.</span>';
    }
    var stats = el('bz-speech-stats');
    if (stats) {
      var g = game.stats || {};
      stats.innerHTML = [['Events heard', g.events], ['Reactions', g.reactions],
        ['Stock lines (model down)', g.canned], ['Repeats dropped', g.repeats]].map(function (x) {
        return '<dl class="cell"><dt>' + esc(x[0]) + '</dt><dd>' + num(x[1]) + '</dd></dl>';
      }).join('');
    }
    var said = el('bz-speech-said');
    if (said) {
      var lines = (game.recent || []).slice().reverse();
      said.innerHTML = lines.length ? lines.map(function (r) {
        return '<div class="row"><span class="t">' + ago(r.at) + '</span><span class="k">' + esc(r.world) + '</span><b>' +
          esc(r.who) + '</b>' + (r.to ? ' <span class="muted">(' + esc(String(r.to).replace(/_/g, ' ')) + ')</span>' : '') +
          '<div class="say">' + esc(r.text) + '</div></div>';
      }).join('') : '<span class="muted tiny">Nothing said in a round yet.</span>';
    }
  }

  // ============================================================ llm pane
  function llmPane() {
    return '<div id="bz-llm-status"></div>' +
      '<div class="bz-actions" style="margin:8px 0"><button class="btn small primary" type="button" data-bz="probe">Probe the endpoint now</button>' +
      '<button class="btn small" type="button" data-bz="template">View the chat template</button></div>' +
      '<div class="bz-grid2"><div><b>Try it</b><div class="field"><label>System message (optional)</label>' +
      '<textarea id="bz-test-system" rows="3" placeholder="You are a player on BLOCKHAVEN..."></textarea></div>' +
      '<div class="field"><label>Prompt</label><textarea id="bz-test-prompt" rows="2">Say hi to the lobby in under ten words.</textarea></div>' +
      '<button class="btn small go" type="button" data-bz="test">Send</button><div id="bz-test-out" style="margin-top:6px"></div></div>' +
      '<div><b>Queue by kind</b><div class="bz-status" id="bz-llm-queue"></div><b style="display:block;margin-top:8px">Recent requests</b>' +
      '<div class="bz-feed" id="bz-llm-recent"></div></div></div>';
  }

  function drawLLMStatus() {
    var box = el('bz-llm-status');
    if (!box || !BZ.overview) return;
    var llm = BZ.overview.llm || {}, info = llm.info || {};
    var sampling = llm.sampling || {}, pulled = info.sampling || {}, source = info.sampling_source || {};
    var cells = [
      ['Reachable', info.reachable ? '<span class="bz-ok">yes</span>' : '<span class="bz-bad">no</span>'],
      ['Server', esc(info.backend || '?')], ['Model', esc(info.model || '(server default)')],
      ['Context', num(info.context) + (info.context_source ? ' <span class="tiny muted">(' + esc(info.context_source) + ')</span>' : '')],
      ['Culling to', num(llm.context_limit) + ' tokens'],
      ['Tokenizer', esc(info.tokenizer || 'estimated') + ' • ' + (info.chars_per_token || '?') + ' chars/token'],
      ['Chat template', info.template_chars ? num(info.template_chars) + ' chars from ' + esc(info.template_source) : 'none reported'],
      ['Last probe', ago(info.probed_at)],
      ['Status', llm.available ? '<span class="bz-ok">accepting work</span>' :
        '<span class="bz-bad">' + (llm.enabled ? 'backing off (' + llm.down_for + 's)' : 'switched off') + '</span>'],
      ['Throughput', (llm.per_minute || 0) + ' requests in the last minute, ' + (llm.active || 0) + ' running']
    ];
    var html = '<div class="bz-status">' + cells.map(function (c) {
      return '<dl class="cell"><dt>' + c[0] + '</dt><dd>' + c[1] + '</dd></dl>';
    }).join('') + '</div>';
    var keys = Object.keys(sampling);
    html += '<div class="tiny" style="margin-top:8px"><b>Sampling sent with every request:</b> ' + (keys.length ? keys.map(function (k) {
      return '<span class="bz-tag">' + esc(k) + ' = ' + esc(sampling[k]) + (pulled[k] != null && pulled[k] === sampling[k]
        ? ' <span class="muted">(' + esc(source[k] || 'server') + ')</span>' : ' <span class="muted">(override)</span>') + '</span>';
    }).join(' ') : '<span class="muted">none pulled yet — the server’s own defaults apply</span>') + '</div>';
    if ((info.notes || []).length || (info.errors || []).length) {
      html += '<div class="tiny muted" style="margin-top:4px">' + (info.notes || []).map(esc).join(' • ') +
        ((info.errors || []).length ? ' <span class="bz-bad">' + (info.errors || []).map(esc).join(' • ') + '</span>' : '') + '</div>';
    }
    box.innerHTML = html;
    var queue = el('bz-llm-queue');
    if (queue) {
      var stats = llm.stats || {}, labels = llm.labels || {};
      var kinds = Object.keys(labels);
      queue.innerHTML = kinds.map(function (k) {
        var s = stats[k] || {};
        return '<dl class="cell"><dt>' + esc(labels[k]) + '</dt><dd>' + num((llm.queue || {})[k] || 0) + ' waiting</dd>' +
          '<dd class="tiny muted">' + num(s.ok) + ' ok • ' + num(s.failed) + ' failed • ' +
          num((s.dropped || 0) + (s.expired || 0)) + ' dropped' + (s.ms ? ' • ' + Math.round(s.ms) + ' ms' : '') + '</dd></dl>';
      }).join('');
    }
    var recent = el('bz-llm-recent');
    if (recent) {
      var rows = (llm.recent || []).slice().reverse();
      recent.innerHTML = rows.length ? rows.map(function (r) {
        return '<div class="row"><span class="t">' + r.ms + ' ms • ' + ago(r.at) + '</span><span class="k">' + esc(r.kind) +
          '</span>' + (r.error ? '<span class="bz-bad">' + esc(r.error) + '</span>' : esc(r.reply || '(empty)')) + '</div>';
      }).join('') : '<span class="muted tiny">No requests yet.</span>';
    }
  }

  // ========================================================= prompts pane
  function promptsPane() {
    return '<p class="bz-intro">Every request is built the same way: the system message for its kind of interaction, the ' +
      'bot’s persona block underneath it, then the conversation itself — the comment section, the round’s chat or ' +
      'the DM thread — read from that bot’s own log and culled oldest-first to fit the context.</p>';
  }

  // ============================================================= events
  function bindOnce() {
    var root = document.querySelector('[data-admin-panel="bots"]');
    el('bz-master').addEventListener('click', function () { flip('system.enabled', el('bz-master')); });
    root.addEventListener('click', function (event) {
      var t = event.target.closest('[data-bz-sub]');
      if (t) {
        if (Object.keys(BZ.dirty).length && !window.confirm('Leave with unsaved changes?')) return;
        BZ.dirty = {};
        BZ.sub = t.dataset.bzSub;
        drawNav();
        drawSub();
        return;
      }
      t = event.target.closest('[data-bz-toggle]');
      if (t) { flip(t.dataset.bzToggle, t); return; }
      t = event.target.closest('[data-bz-bool]');
      if (t) {
        var on = t.getAttribute('aria-checked') !== 'true';
        t.setAttribute('aria-checked', on ? 'true' : 'false');
        t.nextElementSibling.textContent = on ? 'On' : 'Off';
        markDirty(t.dataset.bzBool, on);
        return;
      }
      t = event.target.closest('[data-bz-clear]');
      if (t) {
        var input = document.querySelector('[data-bz-num="' + t.dataset.bzClear + '"]');
        if (input) input.value = '';
        markDirty(t.dataset.bzClear, null);
        return;
      }
      t = event.target.closest('[data-bz-state]');
      if (t) { BZ.table.state = t.dataset.bzState; BZ.table.page = 0; drawSub(); return; }
      t = event.target.closest('[data-bz-world]');
      if (t) {
        // a world card toggles the world filter
        var picked = BZ.table.world === t.dataset.bzWorld ? '' : t.dataset.bzWorld;
        BZ.table.world = picked;
        BZ.table.state = picked ? 'playing' : '';
        BZ.table.page = 0;
        drawSub();
        return;
      }
      t = event.target.closest('[data-bz-open]');
      if (t) { event.preventDefault(); openBot(t.dataset.bzOpen); return; }
      t = event.target.closest('[data-bz-log]');
      if (t) { openLog(t.dataset.bzLog); return; }
      t = event.target.closest('[data-bz-act]');
      if (t) { botAction(t.dataset.bzAct); return; }
      t = event.target.closest('[data-bz-delete-one]');
      if (t) {
        var id = parseInt(t.dataset.bzDeleteOne, 10);
        Site.confirm('Delete this bot?', 'Its account, comments, posts, friendships and folder go with it.',
                     { confirm: 'Delete', danger: true, tone: 'red' }).then(function (ok) {
          if (!ok) return;
          Site.post('/api/admin/bots/delete', { ids: [id] }).then(function (res) {
            if (!res.ok) { Site.toast(res.error, 'bad'); return; }
            Site.toast(res.message);
            el('bz-drawer').classList.add('hidden');
            setTimeout(loadTable, 1500);
          });
        });
        return;
      }
      t = event.target.closest('[data-bz]');
      if (!t) return;
      var action = t.dataset.bz;
      if (action === 'close-drawer') el('bz-drawer').classList.add('hidden');
      else if (action === 'save') save();
      else if (action === 'discard') { BZ.dirty = {}; drawSub(); }
      else if (action === 'reset') {
        Site.confirm('Reset this section to its defaults?', 'Only the settings on this tab are affected.',
                     { confirm: 'Reset' }).then(function (ok) {
          if (!ok) return;
          Site.post('/api/admin/bots/reset', { section: t.dataset.section }).then(function (res) {
            if (!res.ok) { Site.toast(res.error, 'bad'); return; }
            BZ.values = res.values; BZ.dirty = {};
            Site.toast('Section reset.');
            drawNav(); drawSub();
          });
        });
      } else if (action === 'prev') { BZ.table.page = Math.max(0, BZ.table.page - 1); loadTable(); }
      else if (action === 'next') { BZ.table.page += 1; loadTable(); }
      else if (action === 'generate') {
        var count = parseInt(el('bz-count').value, 10) || 0;
        Site.post('/api/admin/bots/create', { count: count }).then(function (res) {
          if (!res.ok) { Site.toast(res.error, 'bad'); return; }
          Site.toast(res.message);
          if (BZ.overview) BZ.overview.job = res.job;
          drawJob();
        });
      } else if (action === 'cancel-job') {
        Site.post('/api/admin/bots/cancel', {}).then(function (res) {
          Site.toast(res.cancelled ? 'Stopping after the current batch.' : 'No job is running.', 'info');
        });
      } else if (action === 'names') {
        Site.get('/api/admin/bots/names/preview').then(function (res) {
          if (res.ok) el('bz-names').innerHTML = res.names.map(function (n) { return '<span>' + esc(n) + '</span>'; }).join('');
        });
      } else if (action === 'delete-all') {
        var phrase = (el('bz-confirm').value || '').trim();
        Site.confirm('Delete every bot?', 'This cannot be undone.', { confirm: 'Delete all', danger: true, tone: 'red' })
          .then(function (ok) {
            if (!ok) return;
            Site.post('/api/admin/bots/delete', { all: true, confirm: phrase }).then(function (res) {
              if (!res.ok) { Site.toast(res.error, 'bad'); return; }
              Site.toast(res.message);
              if (BZ.overview) BZ.overview.job = res.job;
              drawJob();
            });
          });
      } else if (action === 'probe') {
        t.disabled = true;
        Site.post('/api/admin/bots/llm/probe', {}).then(function (res) {
          t.disabled = false;
          if (!res.ok) { Site.toast(res.error, 'bad'); return; }
          if (BZ.overview) BZ.overview.llm = res.llm;
          drawLLMStatus();
          Site.toast(res.reachable ? 'The endpoint answered.' : 'The endpoint did not answer.', res.reachable ? '' : 'bad');
        });
      } else if (action === 'template') {
        Site.get('/api/admin/bots/llm/template').then(function (res) {
          Site.dialog({ title: 'Chat template' + (res.source ? ' (from ' + res.source + ')' : ''), centered: true,
                        bodyHtml: '<div class="bz-code">' + (res.template ? esc(res.template)
                          : 'The server did not report a chat template. Chat mode lets it apply its own.') + '</div>',
                        confirm: 'Close', cancel: null, tone: 'purple' });
        });
      } else if (action === 'test') {
        var out = el('bz-test-out');
        out.innerHTML = '<span class="loading"></span>';
        Site.post('/api/admin/bots/llm/test', { prompt: el('bz-test-prompt').value,
                                                 system: el('bz-test-system').value }).then(function (res) {
          if (!res.ok) { out.innerHTML = '<div class="notice bad">' + esc(res.error) + '</div>'; return; }
          out.innerHTML = '<div class="notice info">' + esc(res.text || '(empty)') + '</div><div class="tiny muted">' +
            res.ms + ' ms • ' + esc(res.mode) + ' mode' + (res.prompt_tokens ? ' • ' + res.prompt_tokens +
            ' prompt tokens, ' + res.completion_tokens + ' generated' : '') + '</div>';
        });
      }
    });
    root.addEventListener('input', function (event) {
      var t = event.target;
      if (t.id === 'bz-q') {
        clearTimeout(BZ.qTimer);
        BZ.qTimer = setTimeout(function () { BZ.table.q = t.value.trim(); BZ.table.page = 0; loadTable(); }, 260);
        return;
      }
      if (t.dataset.bzNum) {
        var f = fieldOf(t.dataset.bzNum);
        var value = t.value === '' ? null : Number(t.value);
        var slide = document.querySelector('[data-bz-slide="' + t.dataset.bzNum + '"]');
        if (slide && value != null) slide.value = value;
        markDirty(t.dataset.bzNum, value == null && !f.nullable ? f.default : value);
      } else if (t.dataset.bzSlide) {
        var box = document.querySelector('[data-bz-num="' + t.dataset.bzSlide + '"]');
        if (box) box.value = t.value;
        markDirty(t.dataset.bzSlide, Number(t.value));
      } else if (t.dataset.bzPair) {
        var key = t.dataset.bzPair;
        var pair = (current(key) || ['', '']).slice();
        var fp = fieldOf(key);
        pair[parseInt(t.dataset.i, 10)] = fp.kind === 'daterange' ? t.value : Number(t.value);
        markDirty(key, pair);
        syncBands();
      } else if (t.dataset.bzText) {
        markDirty(t.dataset.bzText, t.value);
      } else if (t.dataset.bzList) {
        var lines = t.value.split('\n');
        var counter = document.querySelector('[data-bz-count="' + t.dataset.bzList + '"]');
        if (counter) counter.textContent = lines.filter(function (l) { return l.trim(); }).length + ' lines';
        markDirty(t.dataset.bzList, lines);
      } else if (t.dataset.bzChance) {
        var ckey = t.dataset.bzChance;
        var chances = JSON.parse(JSON.stringify(current(ckey) || {}));
        chances[t.dataset.event] = Number(t.value);
        t.nextElementSibling.textContent = Number(t.value) ? t.value + '%' : 'off';
        t.parentNode.classList.toggle('off', !Number(t.value));
        markDirty(ckey, chances);
      } else if (t.dataset.bzWeight) {
        var wkey = t.dataset.bzWeight;
        var weights = JSON.parse(JSON.stringify(current(wkey) || {}));
        weights[t.dataset.tag] = Number(t.value);
        t.nextElementSibling.textContent = Number(t.value).toFixed(1);
        markDirty(wkey, weights);
      }
    });
    root.addEventListener('change', function (event) {
      var t = event.target;
      if (t.id === 'bz-world') { BZ.table.world = t.value; BZ.table.page = 0; loadTable(); }
      else if (t.id === 'bz-tag') { BZ.table.tag = t.value; BZ.table.page = 0; loadTable(); }
      else if (t.id === 'bz-sort') { BZ.table.sort = t.value; BZ.table.page = 0; loadTable(); }
      else if (t.dataset.bzText && t.tagName === 'SELECT') { markDirty(t.dataset.bzText, t.value); }
    });
    // the drawer lives outside the panel's normal flow; its buttons too
    el('bz-drawer').addEventListener('click', function (event) {
      var t = event.target.closest('[data-bz="close-drawer"]');
      if (t) el('bz-drawer').classList.add('hidden');
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') el('bz-drawer').classList.add('hidden');
    });
    window.addEventListener('resize', function () {
      if (BZ.visible && BZ.overview) { drawHero(); if (BZ.sub === 'presence') drawCurve(); }
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var tab = document.querySelector('[data-admin-tab="bots"]');
    if (!tab) return;
    tab.addEventListener('click', function () { setTimeout(show, 0); });
    // the drawer's buttons sit inside the bots panel's event delegation
    var drawer = el('bz-drawer');
    var panel = document.querySelector('[data-admin-panel="bots"]');
    if (drawer && panel && drawer.parentNode !== panel) panel.appendChild(drawer);
    if (window.location.hash === '#bots') tab.click();
  });
})();
