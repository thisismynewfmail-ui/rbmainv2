/* /parent-signup -- live help on the form.  The form posts normally without
   any of this; with it, problems show up next to the field that has them,
   the username is checked as it is typed, and a successful sign-up goes
   straight on to setting up the first child. */
(function () {
  'use strict';
  var FAM = window.FAM;
  var form = document.getElementById('signup-form');
  if (!form) return;
  var $ = function (id) { return document.getElementById(id); };

  // the family's own clock, so "today" and "bedtime" mean their today
  try { $('tz').value = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) {}
  $('tz-offset').value = String(-new Date().getTimezoneOffset());

  function field(name) { return form.querySelector('[data-field="' + name + '"]'); }
  function setMsg(name, text, state) {
    var box = field(name);
    if (!box) return;
    box.classList.remove('is-bad', 'is-good');
    if (state) box.classList.add(state === 'bad' ? 'is-bad' : 'is-good');
    var msg = box.querySelector('.f-fieldmsg');
    if (msg) msg.textContent = text || '';
  }

  /* -------------------------------------------------- username, live */
  var nameInput = $('username');
  var nameTimer = 0;
  var nameSeq = 0;
  nameInput.addEventListener('input', function () {
    clearTimeout(nameTimer);
    var value = nameInput.value.trim();
    if (!value) { setMsg('username', ''); return; }
    if (!/^[A-Za-z0-9_]{3,20}$/.test(value)) {
      setMsg('username', '3–20 letters, numbers or underscores.', 'bad');
      return;
    }
    setMsg('username', 'Checking…');
    var seq = ++nameSeq;
    nameTimer = setTimeout(function () {
      FAM.post('/api/family/username', { kind: 'parent', username: value }).then(function (res) {
        if (seq !== nameSeq) return;
        if (!res.ok) { setMsg('username', ''); return; }
        if (res.available) setMsg('username', '✓ ' + value + ' is yours if you want it.', 'good');
        else setMsg('username', res.problem || 'That username is taken.', 'bad');
      });
    }, 380);
  });

  /* ----------------------------------------------- password strength */
  var pass = $('password');
  var meter = $('strength');
  function score(p) {
    if (!p) return 0;
    var s = 0;
    if (p.length >= 8) s++;
    if (p.length >= 12) s++;
    if (/[a-z]/.test(p) && /[A-Z]/.test(p)) s++;
    if (/\d/.test(p) && /[^A-Za-z0-9]/.test(p)) s++;
    else if (/\d/.test(p) || /[^A-Za-z0-9]/.test(p)) s += 0.5;
    return Math.max(1, Math.min(4, Math.round(s)));
  }
  pass.addEventListener('input', function () {
    var p = pass.value;
    meter.setAttribute('data-score', String(p ? score(p) : 0));
    var shield = $('pw-shield');
    if (shield) shield.setAttribute('data-score', String(p && p.length >= 8 ? score(p) : (p ? 1 : 0)));
    if (!p) setMsg('password', '');
    else if (p.length < 8) setMsg('password', (8 - p.length) + ' more character' + (8 - p.length === 1 ? '' : 's') + ' to go.');
    else setMsg('password', ['', 'Okay', 'Good', 'Strong', 'Very strong'][score(p)] + ' password.', 'good');
  });

  ['display_name', 'email'].forEach(function (name) {
    var input = $(name);
    input.addEventListener('input', function () { setMsg(name, ''); });
  });
  form.querySelector('[name="guardian"]').addEventListener('change', function () { setMsg('guardian', ''); });

  /* ------------------------------------------------------------ submit */
  function check() {
    var ok = true;
    if (!$('display_name').value.trim()) { setMsg('display_name', 'Tell us what to call you.', 'bad'); ok = false; }
    var email = $('email').value.trim();
    if (!/^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/.test(email)) { setMsg('email', 'That email doesn’t look right.', 'bad'); ok = false; }
    if (!/^[A-Za-z0-9_]{3,20}$/.test(nameInput.value.trim())) { setMsg('username', '3–20 letters, numbers or underscores.', 'bad'); ok = false; }
    if (pass.value.length < 8) { setMsg('password', 'Use at least 8 characters.', 'bad'); ok = false; }
    if (!form.querySelector('[name="guardian"]').checked) { setMsg('guardian', 'Please confirm this to continue.', 'bad'); ok = false; }
    return ok;
  }

  var btn = $('signup-btn');
  var banner = $('ob-error');
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    banner.classList.add('f-hidden');
    if (!check()) {
      var bad = form.querySelector('.is-bad input');
      if (bad) bad.focus();
      return;
    }
    btn.classList.add('is-busy');
    var body = new URLSearchParams(new FormData(form));
    fetch('/parent-signup', {
      method: 'POST', credentials: 'same-origin', body: body,
      headers: { 'Accept': 'application/json', 'X-Requested-With': 'fetch' }
    }).then(function (r) { return r.json(); }).then(function (res) {
      if (res.ok) {
        FAM.track('CompleteRegistration', { content_name: 'family_account' });
        setTimeout(function () { location.href = res.redirect; }, 180);
        return;
      }
      btn.classList.remove('is-busy');
      if (res.field && field(res.field)) {
        setMsg(res.field, res.error, 'bad');
        var input = field(res.field).querySelector('input');
        if (input) input.focus();
      } else {
        banner.querySelector('span').textContent = res.error || 'Something went wrong. Please try again.';
        banner.classList.remove('f-hidden');
      }
    }).catch(function () {
      // the network hiccuped: fall back to an ordinary post
      btn.classList.remove('is-busy');
      form.submit();
    });
  });
})();
