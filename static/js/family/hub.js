/* /parent_<name> -- the family page's live parts. */
(function () {
  'use strict';
  var FAM = window.FAM;
  var boot = FAM.boot || {};
  var $ = FAM.$;
  var $$ = FAM.$$;

  function totalToday(kids) {
    var s = 0;
    (kids || []).forEach(function (k) { s += ((k.status || k).today || {}).used || 0; });
    return FAM.duration(s);
  }
  var todayEl = $('[data-hub="today"]');
  if (todayEl) todayEl.textContent = totalToday(boot.kids);

  function paint(kid) {
    var card = document.querySelector('[data-kid="' + kid.id + '"]');
    if (!card) return;
    var t = kid.today || {};
    var status = card.querySelector('[data-live="status"]');
    if (status) {
      status.className = 'db-status ' + kid.state;
      var dot = status.querySelector('.f-dot');
      if (dot) dot.className = 'f-dot ' + (kid.state === 'playing' ? 'live' : (kid.state === 'online' ? 'on' : ''));
      var label = status.querySelector('[data-live="label"]');
      if (label) label.textContent = kid.paused ? 'Paused' : kid.label;
    }
    var used = card.querySelector('[data-live="used"]');
    if (used) used.textContent = t.used_label;
    var meter = card.querySelector('[data-live="meter"]');
    if (meter) {
      meter.style.width = (t.pct || 0) + '%';
      meter.parentNode.classList.toggle('low', (t.pct || 0) >= 85);
    }
    var note = card.querySelector('[data-live="note"]');
    if (note) note.textContent = t.quiet_now ? 'Quiet hours until ' + t.quiet_end
      : (t.left !== null && t.left !== undefined ? t.left_label + ' left' + (t.quiet ? ' · quiet from ' + t.quiet_start : '')
         : (t.quiet ? 'Quiet from ' + t.quiet_start : 'No limits set'));
  }
  function refresh() {
    if (document.hidden) return;
    FAM.get('/api/family/live').then(function (res) {
      if (!res.ok) return;
      res.kids.forEach(paint);
      var online = $('[data-hub="online"]');
      if (online) online.textContent = res.kids.filter(function (k) { return k.state !== 'offline'; }).length;
      if (todayEl) todayEl.textContent = totalToday(res.kids);
    });
  }
  if ((boot.kids || []).length) setInterval(refresh, 15000);

  /* ------------------------------------------------------- pause/resume */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-pause]');
    if (!btn) return;
    var uid = btn.getAttribute('data-pause');
    var name = btn.getAttribute('data-name');
    var paused = btn.getAttribute('data-paused') === '1';
    var go = paused ? Promise.resolve(true) : FAM.confirm({
      title: 'Pause ' + name + '’s account?',
      body: name + ' will be signed out everywhere, including any game, until you resume it.',
      confirm: 'Pause account'
    });
    go.then(function (yes) {
      if (!yes) return;
      btn.classList.add('is-busy');
      FAM.post('/api/family/child/' + uid + '/pause', { paused: !paused }).then(function (res) {
        btn.classList.remove('is-busy');
        if (!res.ok) { FAM.toast(res.error, 'bad'); return; }
        var now = !!res.paused;
        btn.setAttribute('data-paused', now ? '1' : '0');
        btn.className = 'f-btn f-btn-sm ' + (now ? 'f-btn-good' : 'f-btn-ghost');
        btn.innerHTML = '<svg class="f-ic sm"><use href="#i-' + (now ? 'play' : 'pause') + '"/></svg> ' + (now ? 'Resume' : 'Pause');
        var card = btn.closest('.hub-kid');
        if (card) {
          card.classList.toggle('is-paused', now);
          var label = card.querySelector('[data-live="label"]');
          if (label) label.textContent = now ? 'Paused' : 'Offline';
        }
        FAM.toast(now ? name + '’s account is paused.' : name + '’s account is active again.', 'good');
      });
    });
  });

  /* ---------------------------------------------------------- approvals */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-decide]');
    if (!btn) return;
    var row = btn.closest('[data-approval]');
    if (!row || row.classList.contains('done')) return;
    btn.classList.add('is-busy');
    var decision = btn.getAttribute('data-decide');
    FAM.post('/api/family/child/' + row.getAttribute('data-uid') + '/approval',
             { id: Number(row.getAttribute('data-approval')), decision: decision }).then(function (res) {
      btn.classList.remove('is-busy');
      if (!res.ok) { FAM.toast(res.error, 'bad'); return; }
      row.classList.add('done');
      $$('button', row).forEach(function (b) { b.disabled = true; });
      FAM.toast(decision === 'approve' ? 'Approved.' : 'Declined.', 'good');
      var count = $('[data-hub="attention"]');
      if (count) count.textContent = Math.max(0, Number(count.textContent) - 1);
    });
  });

  /* ------------------------------------------------------------ account */
  var acct = $('#acct-form');
  if (acct) acct.addEventListener('submit', function (e) {
    e.preventDefault();
    FAM.post('/api/family/account', {
      display_name: acct.display_name.value, email: acct.email.value, timezone: acct.timezone.value
    }).then(function (res) { FAM.toast(res.ok ? 'Saved.' : res.error, res.ok ? 'good' : 'bad'); });
  });
  var pass = $('#pass-form');
  if (pass) pass.addEventListener('submit', function (e) {
    e.preventDefault();
    FAM.post('/api/family/account/password', { current: pass.current.value, 'new': pass['new'].value }).then(function (res) {
      FAM.toast(res.ok ? 'Password changed. Your other devices were signed out.' : res.error, res.ok ? 'good' : 'bad');
      if (res.ok) { pass.current.value = ''; pass['new'].value = ''; }
    });
  });
  var out = $('#signout-all');
  if (out) out.addEventListener('click', function () {
    FAM.post('/api/family/account/signout-all', {}).then(function (res) {
      FAM.toast(res.ok ? 'Signed out on every other device.' : res.error, res.ok ? 'good' : 'bad');
    });
  });
  var del = $('#delete-family');
  if (del) del.addEventListener('click', function () {
    var username = del.getAttribute('data-username');
    FAM.confirm({ title: 'Delete your whole family account?', danger: true,
                  body: 'This deletes your account and every child account you made, for good. Type your username to confirm.',
                  match: username, placeholder: username, confirm: 'Delete everything' })
      .then(function (typed) {
        if (!typed) return;
        FAM.post('/api/family/account/delete', { confirm: typed }).then(function (res) {
          if (res.ok) location.href = res.redirect || '/parent_signup_l';
          else FAM.toast(res.error, 'bad');
        });
      });
  });
})();
