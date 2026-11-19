/* /parent_<name>/child/<kid> -- the child dashboard's live parts. */
(function () {
  'use strict';
  var FAM = window.FAM;
  var boot = FAM.boot || {};
  var $ = FAM.$;
  var $$ = FAM.$$;
  var child = boot.child || {};
  var report = boot.report || {};
  var api = '/api/family/child/' + child.id;
  var name = child.first_name || 'your child';

  /* ------------------------------------------------------------ charts */
  if (window.FamCharts) {
    FamCharts.days($('[data-chart="days"]'), (report.play || {}).chart);
    FamCharts.messages($('[data-chart="messages"]'), (report.messages || {}).daily);
    FamCharts.heat($('[data-chart="heat"]'), (report.play || {}).heat, (report.play || {}).heat_max);
  }

  /* -------------------------------------------------------------- tabs */
  var tabs = $$('#kid-tabs a');
  var sections = tabs.map(function (a) { return document.querySelector(a.getAttribute('href')); }).filter(Boolean);
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var id = '#' + entry.target.id;
        tabs.forEach(function (a) {
          var on = a.getAttribute('href') === id;
          a.classList.toggle('on', on);
          if (on && a.scrollIntoView) a.parentNode.scrollTo({ left: a.offsetLeft - 40, behavior: 'smooth' });
        });
      });
    }, { rootMargin: '-130px 0px -60% 0px' });
    sections.forEach(function (s) { io.observe(s); });
  }

  /* --------------------------------------------------------- live state */
  var statusEl = $('#kid-status');
  function paintLive(st) {
    if (!st) return;
    if (statusEl) {
      statusEl.className = 'db-status big ' + st.state + (st.paused ? ' paused' : '');
      var dot = statusEl.querySelector('.f-dot');
      if (dot) dot.className = 'f-dot ' + (st.state === 'playing' ? 'live' : (st.state === 'online' ? 'on' : ''));
      var label = statusEl.querySelector('[data-live="label"]');
      if (label) label.textContent = st.paused ? 'Paused' : st.label;
      var since = statusEl.querySelector('[data-live="since"]');
      if (since) since.textContent = st.since ? '· ' + st.since : '';
    }
    var t = st.today || {};
    var used = $('.kid-today [data-live="used"]');
    if (used) used.textContent = t.used_label;
    var meter = $('.kid-today [data-live="meter"]');
    if (meter && t.pct !== null && t.pct !== undefined) {
      meter.style.width = t.pct + '%';
      meter.parentNode.classList.toggle('low', t.pct >= 85);
    }
    var note = $('.kid-today [data-live="note"]');
    if (note) note.textContent = t.quiet_now ? 'Quiet hours until ' + t.quiet_end
      : (t.limit !== null && t.limit !== undefined ? t.left_label + ' left of ' + t.limit_label
         : 'No daily limit ' + (t.weekend ? 'on weekends' : 'on school days'));
    var badge = $('#tab-alerts');
    if (badge) {
      badge.textContent = st.alerts;
      badge.style.display = st.alerts ? '' : 'none';
    }
  }
  setInterval(function () {
    if (document.hidden) return;
    FAM.get(api + '/live').then(function (res) { if (res.ok) paintLive(res.status); });
  }, 10000);

  /* ------------------------------------------------------ pause/resume */
  var pauseBtn = $('#kid-pause');
  if (pauseBtn) pauseBtn.addEventListener('click', function () {
    var paused = pauseBtn.getAttribute('data-paused') === '1';
    var go = paused ? Promise.resolve(true) : FAM.confirm({
      title: 'Pause ' + name + '’s account?',
      body: name + ' will be signed out everywhere — including from any game they’re in — and can’t sign in until you resume it.',
      confirm: 'Pause account', cancel: 'Not now'
    });
    go.then(function (yes) {
      if (!yes) return;
      pauseBtn.classList.add('is-busy');
      FAM.post(api + '/pause', { paused: !paused }).then(function (res) {
        pauseBtn.classList.remove('is-busy');
        if (!res.ok) { FAM.toast(res.error, 'bad'); return; }
        var now = !!res.paused;
        pauseBtn.setAttribute('data-paused', now ? '1' : '0');
        pauseBtn.className = 'f-btn f-btn-sm ' + (now ? 'f-btn-good' : 'f-btn-glass');
        pauseBtn.innerHTML = '<svg class="f-ic sm"><use href="#i-' + (now ? 'play' : 'pause') + '"/></svg> <span>' +
          (now ? 'Resume account' : 'Pause account') + '</span>';
        if (statusEl) {
          statusEl.classList.toggle('paused', now);
          var label = statusEl.querySelector('[data-live="label"]');
          if (label) label.textContent = now ? 'Paused' : 'Offline';
        }
        FAM.toast(now ? name + '’s account is paused.' : name + '’s account is active again.', 'good');
      });
    });
  });

  var signoutBtn = $('#kid-signout');
  if (signoutBtn) signoutBtn.addEventListener('click', function () {
    FAM.confirm({ title: 'Sign ' + name + ' out everywhere?', body: 'They’ll be signed out of the site and any game, on every device. They can sign straight back in.', confirm: 'Sign out everywhere' })
      .then(function (yes) {
        if (!yes) return;
        FAM.post(api + '/signout', {}).then(function (res) {
          FAM.toast(res.ok ? 'Signed out everywhere.' : res.error, res.ok ? 'good' : 'bad');
        });
      });
  });

  /* --------------------------------------------------------- approvals */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-decide]');
    if (!btn) return;
    var row = btn.closest('[data-approval]');
    if (!row || row.classList.contains('done')) return;
    var decision = btn.getAttribute('data-decide');
    btn.classList.add('is-busy');
    FAM.post(api + '/approval', { id: Number(row.getAttribute('data-approval')), decision: decision }).then(function (res) {
      btn.classList.remove('is-busy');
      if (!res.ok) { FAM.toast(res.error, 'bad'); return; }
      row.classList.add('done');
      $$('button', row).forEach(function (b) { b.disabled = true; });
      var who = (row.querySelector('b') || {}).textContent || 'them';
      FAM.toast(decision === 'approve'
        ? (res.state === 'friends' ? name + ' and ' + who + ' are friends now.' : 'Approved — the request is on its way to ' + who + '.')
        : 'Declined. ' + who + ' won’t be told why.', 'good');
    });
  });

  /* ---------------------------------------------------------- unfriend */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-unfriend]');
    if (!btn) return;
    var who = btn.getAttribute('data-unfriend');
    FAM.confirm({ title: 'Remove ' + who + '?', body: who + ' will be removed from ' + name + '’s friends. They won’t be able to send private messages any more.', confirm: 'Remove friend', danger: true })
      .then(function (yes) {
        if (!yes) return;
        FAM.post(api + '/unfriend', { username: who }).then(function (res) {
          if (!res.ok) { FAM.toast(res.error, 'bad'); return; }
          var li = btn.closest('li');
          if (li) li.remove();
          FAM.toast(who + ' was removed.', 'good');
        });
      });
  });

  /* ----------------------------------------------------- conversations */
  var drawer = $('#convo-drawer');
  var drawerBody = $('#convo-body');
  function closeDrawer() { if (drawer) drawer.hidden = true; document.body.style.overflow = ''; }
  if (drawer) drawer.addEventListener('click', function (e) { if (e.target.closest('[data-close]')) closeDrawer(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && drawer && !drawer.hidden) closeDrawer(); });
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-convo]');
    if (!btn) return;
    var other = btn.getAttribute('data-convo');
    $('#convo-title').textContent = name + ' & ' + other;
    drawerBody.innerHTML = '<p class="f-muted">Loading…</p>';
    drawer.hidden = false;
    document.body.style.overflow = 'hidden';
    FAM.get(api + '/transcript?with=' + encodeURIComponent(other)).then(function (res) {
      drawerBody.innerHTML = '';
      if (!res.ok || !res.rows.length) {
        drawerBody.innerHTML = '<p class="f-muted">No messages.</p>';
        return;
      }
      res.rows.forEach(function (m) {
        var div = document.createElement('div');
        div.className = 'msg' + (m.mine ? ' mine' : '');
        if (m.subject) {
          var s = document.createElement('span');
          s.className = 'msg-subject';
          s.textContent = m.subject;
          div.appendChild(s);
        }
        div.appendChild(document.createTextNode(m.body));
        var when = document.createElement('small');
        when.textContent = (m.mine ? name : res.other) + ' · ' + m.when;
        div.appendChild(when);
        drawerBody.appendChild(div);
      });
      drawerBody.scrollTop = drawerBody.scrollHeight;
    });
  });

  /* ------------------------------------------------------------ alerts */
  var seenBtn = $('#alerts-seen');
  if (seenBtn) seenBtn.addEventListener('click', function () {
    FAM.post(api + '/alerts-seen', {}).then(function (res) {
      if (!res.ok) { FAM.toast(res.error, 'bad'); return; }
      $$('.alert.unseen').forEach(function (a) { a.classList.remove('unseen'); });
      var badge = $('#tab-alerts');
      if (badge) badge.style.display = 'none';
      seenBtn.remove();
      FAM.toast('All caught up.', 'good');
    });
  });

  /* ------------------------------------------------------------- rules */
  var editor = $('#rules-editor');
  var saveState = $('#save-state');
  var cv = report.controls || {};
  var values = JSON.parse(JSON.stringify(cv.values || {}));
  var labels = cv.labels || {};
  var help = cv.help || {};
  var saveTimer = 0;
  function setSave(cls, text) {
    if (!saveState) return;
    saveState.className = 'save-state ' + cls;
    saveState.textContent = text;
  }
  function save() {
    clearTimeout(saveTimer);
    setSave('saving', 'Saving…');
    saveTimer = setTimeout(function () {
      FAM.post(api + '/controls', { controls: values }).then(function (res) {
        if (!res.ok) { setSave('bad', res.error || 'Couldn’t save'); return; }
        values = res.controls;
        setSave('saved', '✓ Saved');
        if (res.today) paintLive({ state: (statusEl && statusEl.classList.contains('playing')) ? 'playing' : 'offline', label: (statusEl.querySelector('[data-live="label"]') || {}).textContent, today: res.today, alerts: 0, paused: child.paused });
        setTimeout(function () { if (saveState.classList.contains('saved')) saveState.className = 'save-state'; }, 2200);
      });
    }, 350);
  }
  function card(icon, title, sub, extra, span) {
    var d = document.createElement('div');
    d.className = 'wz-rule' + (span ? ' span' : '');
    d.innerHTML = '<div class="wz-rule-head"><span class="ic"><svg class="f-ic"><use href="#i-' + icon + '"/></svg></span><div><h3>' +
      FAM.esc(title) + '</h3>' + (sub ? '<p>' + FAM.esc(sub) + '</p>' : '') + '</div></div>';
    if (extra) d.querySelector('.wz-rule-head').appendChild(extra);
    return d;
  }
  function chip(label, on, act) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'wz-chip' + (on ? ' on' : '');
    b.textContent = label;
    b.setAttribute('aria-pressed', on ? 'true' : 'false');
    b.addEventListener('click', function () { act(); render(); save(); });
    return b;
  }
  function chips(list) {
    var wrap = document.createElement('div');
    wrap.className = 'wz-chips';
    list.forEach(function (c) { wrap.appendChild(c); });
    return wrap;
  }
  function sw(on, act, label) {
    var l = document.createElement('label');
    l.className = 'f-switch';
    l.innerHTML = '<input type="checkbox"' + (on ? ' checked' : '') + ' aria-label="' + FAM.esc(label) + '"><i></i>';
    l.querySelector('input').addEventListener('change', function (e) { act(e.target.checked); render(); save(); });
    return l;
  }
  function minuteChips(key) {
    var list = (cv.minute_choices || [15, 30, 45, 60, 90, 120, 180, 240]).map(function (m) {
      return chip(FAM.minutesLabel(m), values[key] === m, function () { values[key] = m; });
    });
    list.push(chip('No limit', values[key] === null, function () { values[key] = null; }));
    list.push(chip('No games', values[key] === 0, function () { values[key] = 0; }));
    return chips(list);
  }
  function choice(key) {
    return chips(Object.keys(labels[key] || {}).map(function (v) {
      return chip(labels[key][v], values[key] === v, function () { values[key] = v; });
    }));
  }
  function timeSelect(key, from, to) {
    var s = document.createElement('select');
    s.className = 'f-select';
    s.setAttribute('aria-label', key === 'quiet_start' ? 'Quiet hours start' : 'Quiet hours end');
    var found = false;
    for (var h = from; h <= to; h++) {
      [0, 30].forEach(function (m) {
        var v = (h < 10 ? '0' : '') + h + ':' + (m ? '30' : '00');
        var o = document.createElement('option');
        o.value = v;
        o.textContent = FAM.clock(v);
        if (v === values[key]) { o.selected = true; found = true; }
        s.appendChild(o);
      });
    }
    if (!found) {
      var o = document.createElement('option');
      o.value = values[key];
      o.textContent = FAM.clock(values[key]);
      o.selected = true;
      s.insertBefore(o, s.firstChild);
    }
    s.addEventListener('change', function () { values[key] = s.value; save(); });
    return s;
  }
  function render() {
    if (!editor) return;
    editor.innerHTML = '';
    var a = card('clock', 'Play time on school days', 'Monday to Friday');
    a.appendChild(minuteChips('weekday_minutes'));
    editor.appendChild(a);
    var b = card('sun', 'Play time on weekends', 'Saturday and Sunday');
    b.appendChild(minuteChips('weekend_minutes'));
    editor.appendChild(b);
    var q = card('moon', 'Quiet hours', 'No games at bedtime', sw(values.quiet, function (on) { values.quiet = on; }, 'Quiet hours'));
    if (values.quiet) {
      var t = document.createElement('div');
      t.className = 'wz-times';
      t.appendChild(document.createTextNode('From '));
      t.appendChild(timeSelect('quiet_start', 17, 23));
      t.appendChild(document.createTextNode(' until '));
      t.appendChild(timeSelect('quiet_end', 5, 10));
      q.appendChild(t);
    }
    editor.appendChild(q);
    var f = card('user-check', 'New friends', help.friends);
    f.appendChild(choice('friends'));
    editor.appendChild(f);
    var m = card('message', 'Private messages', help.messages);
    m.appendChild(choice('messages'));
    editor.appendChild(m);
    var c = card('chat-shield', 'In-game chat', help.chat);
    c.appendChild(choice('chat'));
    editor.appendChild(c);
    var w = card('message', 'Comments on their profile', help.wall);
    w.appendChild(choice('wall'));
    editor.appendChild(w);
    var p = card('eye', 'Who sees them online', help.presence);
    p.appendChild(choice('presence'));
    editor.appendChild(p);
    var worlds = card('globe', 'Worlds they can play', 'Each comes with a short parent’s guide', null, true);
    (cv.worlds || []).forEach(function (world) {
      var row = document.createElement('div');
      row.className = 'wz-world';
      var allowed = values.worlds_blocked.indexOf(world.id) < 0;
      row.innerHTML = '<span class="wz-world-dot" style="--c:' + FAM.esc(world.color) + '"></span><span class="wz-world-text"><b>' +
        FAM.esc(world.name) + ' <span class="f-chip ' + (world.intensity === 'gentle' ? 'good' : world.intensity === 'intense' ? 'grape' : 'blue') +
        '">' + FAM.esc(world.intensity_label) + '</span></b><small>' + FAM.esc(world.kind) + ' · ' + FAM.esc(world.note) + '</small></span>';
      row.appendChild(sw(allowed, function (on) {
        var i = values.worlds_blocked.indexOf(world.id);
        if (on && i >= 0) values.worlds_blocked.splice(i, 1);
        if (!on && i < 0) values.worlds_blocked.push(world.id);
      }, 'Allow ' + world.name));
      worlds.appendChild(row);
    });
    editor.appendChild(worlds);
    editor.appendChild(card('coin', 'Spend play money', help.spending, sw(values.spending, function (on) { values.spending = on; }, 'Spending')));
    editor.appendChild(card('box', 'Open crates', help.crates, sw(values.crates, function (on) { values.crates = on; }, 'Crates')));
  }
  render();

  /* ----------------------------------------------------------- account */
  var details = $('#kid-details');
  if (details) details.addEventListener('submit', function (e) {
    e.preventDefault();
    FAM.post(api + '/details', { first_name: details.first_name.value, birth_year: details.birth_year.value }).then(function (res) {
      FAM.toast(res.ok ? 'Saved.' : res.error, res.ok ? 'good' : 'bad');
      if (res.ok) setTimeout(function () { location.reload(); }, 700);
    });
  });
  var passForm = $('#kid-pass');
  if (passForm) passForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var pw = passForm.password.value;
    FAM.post(api + '/password', { password: pw }).then(function (res) {
      FAM.toast(res.ok ? 'Password changed. ' + name + ' will use the new one next time.' : res.error, res.ok ? 'good' : 'bad');
      if (res.ok) passForm.password.value = '';
    });
  });
  var hereBtn = $('#kid-signin-here');
  if (hereBtn) hereBtn.addEventListener('click', function () {
    FAM.confirm({ title: 'Sign ' + name + ' in on this computer?', body: 'They’ll be taken to ' + name + '’s account in this browser. You’ll stay signed in to your dashboard too.', confirm: 'Sign them in' })
      .then(function (yes) {
        if (!yes) return;
        FAM.post(api + '/signin-here', {}).then(function (res) {
          if (res.ok) location.href = res.redirect || '/';
          else FAM.toast(res.error, 'bad');
        });
      });
  });
  var delBtn = $('#kid-delete');
  if (delBtn) delBtn.addEventListener('click', function () {
    FAM.confirm({ title: 'Delete ' + name + '’s account?', body: 'This removes @' + child.username + ' for good. Type their username to confirm.',
                  match: child.username, placeholder: child.username, confirm: 'Delete forever', danger: true })
      .then(function (typed) {
        if (!typed) return;
        FAM.post(api + '/delete', { confirm: typed }).then(function (res) {
          if (res.ok) location.href = res.redirect || boot.home;
          else FAM.toast(res.error, 'bad');
        });
      });
  });
})();
