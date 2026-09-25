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
    stats: '▣', creation: '✚', personas: '☺', presence: '◔',
    worlds: '◉', ingame: '⌖', friends: '❤', chatter: '✎',
    messages: '✉', llm: '⚙', prompts: '¶'
  };
  var SCOPE_LABEL = { universal: 'Universal', 'per-bot': 'Per-bot range', base: 'Base × persona' };
  var SCOPE_HELP = {
    universal: 'One value for the whole platform.',
    'per-bot': 'Each bot draws its own value from inside this range once, nudged by its persona.',
    base: 'A platform-wide base that every bot scales by its own persona.'
  };
  var STATE_LABEL = { offline: 'Offline', waking: 'Settling in', online: 'Online', playing: 'In a world' };

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
      liveInst += worlds[id].live_instances || 0;
      humans += worlds[id].live_humans || 0;
    });
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
      kpi('Live rounds', num(liveInst), num(liveBots) + ' bots with ' + num(humans) + ' people', 'var(--link)') +
      kpi('Asleep', num(asleep), 'instances at no cost', 'var(--bz-waking)') +
      kpi('Language model', '<span class="' + (llmState === 'ready' ? 'bz-ok' : 'bz-bad') + '">' +
          esc(llmState) + '</span>', (llm.per_minute || 0) + '/min, ' + queue + ' queued', 'var(--bz-target)');
    drawChart(el('bz-spark'), s.history || [], null);
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
  }

  /* A plain canvas chart: online, in worlds and the target, over the last
     hours, sampled once a minute by the director. */
  function drawChart(canvas, history, curve) {
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
    var colors = {
      online: style.getPropertyValue('--bz-online').trim() || '#37c26a',
      playing: style.getPropertyValue('--bz-playing').trim() || '#f0b429',
      target: style.getPropertyValue('--bz-target').trim() || '#5a7fa8',
      ink: style.getPropertyValue('--ink-soft').trim() || '#888'
    };
    var pad = { l: 8, r: 8, t: 22, b: 14 };
    if (curve) {
      var max = 1;
      var pts = curve.map(function (p, i) {
        return [pad.l + (w - pad.l - pad.r) * i / Math.max(1, curve.length - 1),
                h - pad.b - (h - pad.t - pad.b) * p.share / max];
      });
      ctx.beginPath();
      pts.forEach(function (p, i) { if (i) ctx.lineTo(p[0], p[1]); else ctx.moveTo(p[0], p[1]); });
      ctx.lineTo(pts[pts.length - 1][0], h - pad.b);
      ctx.lineTo(pts[0][0], h - pad.b);
      ctx.closePath();
      ctx.fillStyle = 'rgba(154,95,224,.14)';
      ctx.fill();
      ctx.beginPath();
      pts.forEach(function (p, i) { if (i) ctx.lineTo(p[0], p[1]); else ctx.moveTo(p[0], p[1]); });
      ctx.strokeStyle = '#9a5fe0';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = colors.ink;
      ctx.font = '9px Verdana, sans-serif';
      curve.forEach(function (p, i) {
        if (i % 6) return;
        var d = new Date(p.at * 1000);
        ctx.fillText(('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2),
                     pts[i][0] - 10, h - 2);
      });
      // "now" marker
      ctx.strokeStyle = colors.ink;
      ctx.setLineDash([2, 3]);
      var nowX = pad.l + (w - pad.l - pad.r) * ((Date.now() / 1000 - curve[0].at) /
        Math.max(1, curve[curve.length - 1].at - curve[0].at));
      ctx.beginPath(); ctx.moveTo(nowX, pad.t); ctx.lineTo(nowX, h - pad.b); ctx.stroke();
      ctx.setLineDash([]);
      return;
    }
    if (!history.length) {
      ctx.fillStyle = colors.ink;
      ctx.font = '11px Verdana, sans-serif';
      ctx.fillText('Collecting history — one sample a minute.', 12, h / 2 + 4);
      return;
    }
    var top = 1;
    history.forEach(function (p) { top = Math.max(top, p.online, p.target, p.playing); });
    function line(key, color, dash) {
      ctx.beginPath();
      history.forEach(function (p, i) {
        var x = pad.l + (w - pad.l - pad.r) * (history.length === 1 ? 1 : i / (history.length - 1));
        var y = h - pad.b - (h - pad.t - pad.b) * (p[key] || 0) / top;
        if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y);
      });
      ctx.strokeStyle = color;
      ctx.lineWidth = dash ? 1.2 : 2;
      ctx.setLineDash(dash ? [4, 3] : []);
      ctx.stroke();
    }
    line('target', colors.target, true);
    line('playing', colors.playing);
    line('online', colors.online);
    ctx.setLineDash([]);
    ctx.fillStyle = colors.ink;
    ctx.font = '9px Verdana, sans-serif';
    ctx.fillText(num(top), 10, 12);
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
      stats: statsPane, creation: creationPane, personas: null, presence: presencePane,
      worlds: worldsPane, ingame: null, friends: feedsPane, chatter: feedsPane,
      messages: feedsPane, llm: llmPane, prompts: promptsPane
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
    syncBands();
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
    var wide = f.kind === 'textarea' || f.kind === 'weights' || (f.kind === 'list' && f.rows > 4);
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
    } else if (f.kind === 'weights') {
      ctl = weightsHtml(f, v || {});
    }
    if (f.kind !== 'range' && f.kind !== 'hours' && f.kind !== 'daterange' && f.kind !== 'weights') {
      ctl = '<div class="bz-ctl">' + ctl + '</div>';
    }
    return '<div class="bz-field' + (wide ? ' wide' : '') + (Object.prototype.hasOwnProperty.call(BZ.dirty, f.key) ? ' dirty' : '') +
      '" data-bz-field="' + f.key + '"><div class="bz-field-head"><label>' + esc(f.label) + '</label>' +
      '<span class="bz-scope ' + f.scope + '" title="' + esc(SCOPE_HELP[f.scope] || '') + '">' +
      esc(SCOPE_LABEL[f.scope] || f.scope) + '</span></div>' + ctl +
      (f.help ? '<div class="help">' + esc(f.help) + '</div>' : '') + '</div>';
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
      '<select id="bz-sort"><option value="recent">Newest</option><option value="name">Name</option>' +
      '<option value="joined">Join date</option><option value="seen">Last seen</option></select>' +
      '</div>' +
      '<div class="tablewrap"><table class="bz-table" id="bz-table"><tr><th>Bot</th><th>State</th><th>Where</th>' +
      '<th class="hide-sm">Friends</th><th>Comments</th><th class="hide-sm">K / D</th><th class="hide-sm">Joined</th>' +
      '<th class="hide-sm">Next</th></tr><tr><td colspan="8" class="muted">Loading…</td></tr></table></div>' +
      '<div class="bz-pager" id="bz-pager"></div>';
  }

  function drawWorldCards() {
    var box = el('bz-world-cards');
    if (!box || !BZ.overview) return;
    var stats = BZ.overview.stats || {}, worlds = stats.worlds || {};
    box.innerHTML = (BZ.overview.worlds || []).map(function (w) {
      var s = worlds[w.id] || {};
      var total = (s.live_humans || 0) + (s.live_bots || 0) + (s.sleeping_bots || 0);
      var pct = function (n) { return total ? (n / total * 100) : 0; };
      return '<div class="bz-world"><b>' + esc(w.name) + '</b>' +
        '<div class="bz-split" title="people / bots in live rounds / bots asleep">' +
        '<i class="p" style="width:' + pct(s.live_humans || 0) + '%"></i>' +
        '<i class="l" style="width:' + pct(s.live_bots || 0) + '%"></i>' +
        '<i class="s" style="width:' + pct(s.sleeping_bots || 0) + '%"></i></div>' +
        '<div class="tiny"><span>' + num(s.live_humans) + ' people</span><span>' + num(s.live_bots) + ' live bots</span></div>' +
        '<div class="tiny"><span>' + num(s.sleeping_bots) + ' asleep</span><span>' + num(s.sleeping_instances) +
        ' + ' + num(s.live_instances) + ' inst.</span></div></div>';
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
        '<span class="bz-sub">' + (r.state === 'offline' ? 'since ' + ago(r.since) : 'for ' + ago(r.since).replace(' ago', '')) + '</span></td>' +
        '<td>' + where + '</td>' +
        '<td class="hide-sm bz-num">' + r.friends + ' / ' + r.friend_target +
        '<div class="bz-meter"><i style="width:' + Math.min(100, r.friend_target ? r.friends / r.friend_target * 100 : 0) + '%"></i></div></td>' +
        '<td><span class="bz-num">' + num(r.comments) + '</span>' + (r.last_comment ? '<div class="bz-quote">“' +
          esc(r.last_comment) + '” <span class="muted">' + ago(r.last_comment_at) + '</span></div>' : '') + '</td>' +
        '<td class="hide-sm bz-num">' + num(r.kills) + ' / ' + num(r.deaths) + '<span class="bz-sub">K/D ' + kd + '</span></td>' +
        '<td class="hide-sm bz-num">' + new Date(r.joined * 1000).toLocaleDateString() + '</td>' +
        '<td class="hide-sm bz-num">' + (r.next_at ? inFuture(r.next_at) : '—') + '</td></tr>';
    }).join('');
    if (!rows) rows = '<tr><td colspan="8" class="muted">No bots match. Create some in Bot Creation.</td></tr>';
    table.innerHTML = head + rows;
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
    if (canvas && BZ.overview) drawChart(canvas, [], BZ.overview.curve || []);
  }

  // ========================================================== worlds pane
  function worldsPane() {
    return '<p class="bz-intro">Bots only run on a game host in rounds a real player is in. Everywhere else a round ' +
      'sleeps: its score, clock and objective carry on in closed form, it shows in every player count and list, and it ' +
      'costs nothing until somebody presses Join — then it wakes mid-round.</p><div class="tablewrap">' +
      '<table class="grid" id="bz-world-table"></table></div>';
  }

  function drawWorldTable() {
    var table = el('bz-world-table');
    if (!table || !BZ.overview) return;
    var worlds = (BZ.overview.stats || {}).worlds || {};
    table.innerHTML = '<tr><th>World</th><th>People</th><th>Bots with people</th><th>Bots asleep</th>' +
      '<th>Live instances</th><th>Sleeping instances</th></tr>' + (BZ.overview.worlds || []).map(function (w) {
        var s = worlds[w.id] || {};
        return '<tr><td><b>' + esc(w.name) + '</b></td><td>' + num(s.live_humans) + '</td><td>' + num(s.live_bots) +
          '</td><td>' + num(s.sleeping_bots) + '</td><td>' + num(s.live_instances) + '</td><td>' +
          num(s.sleeping_instances) + '</td></tr>';
      }).join('');
  }

  // ============================================================ feed panes
  function feedsPane() {
    return '<div class="bz-grid2"><div><b>What they are saying</b><div class="bz-feed" id="bz-feed-social"></div></div>' +
      '<div><b>Numbers</b><div class="bz-status" id="bz-feed-stats"></div>' +
      '<b style="display:block;margin-top:8px">In-game chat</b><div class="bz-feed" id="bz-feed-chat"></div></div></div>';
  }

  function drawFeeds() {
    if (!BZ.overview) return;
    var chatter = BZ.overview.chatter || {}, game = BZ.overview.gamechat || {};
    var social = el('bz-feed-social');
    if (social) {
      var rows = (chatter.recent || []).slice().reverse();
      social.innerHTML = rows.length ? rows.map(function (r) {
        return '<div class="row"><span class="t">' + ago(r.at) + '</span><span class="k">' + esc(r.kind) + '</span><b>' +
          esc(r.who) + '</b>' + (r.where ? ' → ' + esc(r.where) : '') + ': ' + esc(r.text) + '</div>';
      }).join('') : '<span class="muted tiny">Nothing written yet.</span>';
    }
    var chat = el('bz-feed-chat');
    if (chat) {
      var lines = (game.recent || []).slice().reverse();
      chat.innerHTML = lines.length ? lines.map(function (r) {
        return '<div class="row"><span class="t">' + ago(r.at) + '</span><span class="k">' + esc(r.world) + '</span><b>' +
          esc(r.who) + '</b> to ' + esc(r.to) + ': ' + esc(r.text) + '</div>';
      }).join('') : '<span class="muted tiny">No bot has answered anybody in a round yet.</span>';
    }
    var stats = el('bz-feed-stats');
    if (stats) {
      var s = chatter.stats || {}, g = game.stats || {};
      var cells = [['Requests sent', s.requests_sent], ['Accepted', s.accepted], ['Declined', s.declined],
        ['Follows', s.follows], ['Comments', s.comments], ['Replies', s.replies], ['Posts', s.posts],
        ['Likes', s.likes], ['DMs answered', s.dms], ['Deferred (budget)', s.deferred],
        ['Waiting DMs', chatter.pending_dms], ['Waiting wall replies', chatter.pending_walls],
        ['Chat heard', g.heard], ['Chat answered', g.answered], ['Live chat rooms', game.rooms]];
      stats.innerHTML = cells.map(function (c) {
        return '<dl class="cell"><dt>' + esc(c[0]) + '</dt><dd>' + num(c[1]) + '</dd></dl>';
      }).join('');
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
      t = event.target.closest('[data-bz-open]');
      if (t) { openBot(t.dataset.bzOpen); return; }
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
