/* NoogBlock for families -- what every family page shares.
   No dependencies.  window.FAM carries the parent session's CSRF token (put
   there by templates/family/partials/foot.html) and the helpers below. */
(function (global) {
  'use strict';
  var FAM = global.FAM = global.FAM || {};
  var doc = document;

  function $(sel, root) { return (root || doc).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || doc).querySelectorAll(sel)); }
  FAM.$ = $;
  FAM.$$ = $$;

  FAM.boot = (function () {
    var node = doc.getElementById('fam-boot');
    if (!node) return {};
    try { return JSON.parse(node.textContent || '{}') || {}; } catch (e) { return {}; }
  })();
  if (FAM.boot.csrf) FAM.csrf = FAM.boot.csrf;

  FAM.esc = function (text) {
    var div = doc.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
  };

  /* ---------------------------------------------------------------- API */
  FAM.request = function (method, url, data) {
    var opts = {
      method: method, credentials: 'same-origin',
      headers: { 'X-Requested-With': 'fetch', 'Accept': 'application/json' }
    };
    if (method !== 'GET') {
      opts.headers['Content-Type'] = 'application/json';
      opts.headers['X-CSRF-Token'] = FAM.csrf || '';
      opts.body = JSON.stringify(data || {});
    }
    return fetch(url, opts).then(function (res) {
      return res.json().catch(function () {
        return { ok: false, error: 'Something went wrong. Please try again.' };
      });
    }, function () {
      return { ok: false, error: 'You seem to be offline. Check your connection and try again.' };
    });
  };
  FAM.post = function (url, data) { return FAM.request('POST', url, data); };
  FAM.get = function (url) { return FAM.request('GET', url); };

  /* --------------------------------------------------------------- toast */
  FAM.toast = function (text, kind, ms) {
    var box = doc.getElementById('f-toasts');
    if (!box) {
      box = doc.createElement('div');
      box.className = 'f-toasts';
      box.id = 'f-toasts';
      doc.body.appendChild(box);
    }
    var node = doc.createElement('div');
    node.className = 'f-toast' + (kind ? ' ' + kind : '');
    node.setAttribute('role', kind === 'bad' ? 'alert' : 'status');
    node.textContent = text;
    box.appendChild(node);
    setTimeout(function () {
      node.classList.add('out');
      setTimeout(function () { node.remove(); }, 320);
    }, ms || 3200);
  };

  /* --------------------------------------------------------------- modal
     FAM.confirm({title, body, confirm, cancel, danger, match, placeholder})
     resolves true (or the typed text when ``match`` is set), or false. */
  FAM.confirm = function (opts) {
    opts = opts || {};
    return new Promise(function (resolve) {
      var wrap = doc.createElement('div');
      wrap.className = 'f-modal';
      wrap.setAttribute('role', 'dialog');
      wrap.setAttribute('aria-modal', 'true');
      var card = doc.createElement('div');
      card.className = 'f-modal-card';
      var h = doc.createElement('h3');
      h.textContent = opts.title || 'Are you sure?';
      card.appendChild(h);
      if (opts.body) {
        var p = doc.createElement('p');
        p.textContent = opts.body;
        card.appendChild(p);
      }
      var input = null;
      if (opts.match || opts.input) {
        var field = doc.createElement('div');
        field.className = 'f-field';
        field.style.marginTop = '16px';
        input = doc.createElement('input');
        input.className = 'f-input';
        input.type = opts.inputType || 'text';
        input.autocomplete = 'off';
        input.placeholder = opts.placeholder || '';
        field.appendChild(input);
        card.appendChild(field);
      }
      var actions = doc.createElement('div');
      actions.className = 'f-modal-actions';
      var no = doc.createElement('button');
      no.type = 'button';
      no.className = 'f-btn f-btn-ghost';
      no.textContent = opts.cancel || 'Cancel';
      var yes = doc.createElement('button');
      yes.type = 'button';
      yes.className = 'f-btn ' + (opts.danger ? 'f-btn-danger solid' : 'f-btn-primary');
      yes.textContent = opts.confirm || 'OK';
      actions.appendChild(no);
      actions.appendChild(yes);
      card.appendChild(actions);
      wrap.appendChild(card);
      doc.body.appendChild(wrap);
      var last = doc.activeElement;
      function done(value) {
        wrap.remove();
        doc.removeEventListener('keydown', onKey);
        if (last && last.focus) last.focus();
        resolve(value);
      }
      function check() {
        if (!opts.match) return true;
        return input && input.value.trim().toLowerCase() === String(opts.match).toLowerCase();
      }
      function onKey(e) {
        if (e.key === 'Escape') done(false);
        if (e.key === 'Enter' && input && check()) done(input.value);
      }
      if (opts.match) {
        yes.disabled = true;
        input.addEventListener('input', function () { yes.disabled = !check(); });
      }
      no.addEventListener('click', function () { done(false); });
      yes.addEventListener('click', function () { if (check()) done(input ? input.value : true); });
      wrap.addEventListener('click', function (e) { if (e.target === wrap) done(false); });
      doc.addEventListener('keydown', onKey);
      setTimeout(function () { (input || yes).focus(); }, 30);
    });
  };

  /* -------------------------------------------------------------- motion */
  FAM.reveal = function (root) {
    var nodes = $$('.f-reveal:not(.in)', root);
    if (!('IntersectionObserver' in global)) {
      nodes.forEach(function (n) { n.classList.add('in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    nodes.forEach(function (n) { io.observe(n); });
  };

  FAM.countUp = function (el, to, ms, format) {
    if (!el) return;
    var target = Number(to);
    if (isNaN(target)) target = Number(el.getAttribute('data-count')) || 0;
    var reduce = global.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var fmt = format || function (v) { return Math.round(v).toLocaleString(); };
    if (reduce || !target) { el.textContent = fmt(target); return; }
    var start = performance.now();
    var dur = ms || 1200;
    function step(now) {
      var t = Math.min(1, (now - start) / dur);
      var eased = 1 - Math.pow(1 - t, 3);
      el.textContent = fmt(target * eased);
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  };

  /* -------------------------------------------------------------- format */
  FAM.duration = function (seconds) {
    seconds = Math.max(0, Math.round(Number(seconds) || 0));
    if (seconds < 60) return seconds + 's';
    var minutes = Math.floor(seconds / 60);
    if (minutes < 60) return minutes + 'm';
    var hours = Math.floor(minutes / 60);
    var rest = minutes % 60;
    return rest ? hours + 'h ' + (rest < 10 ? '0' : '') + rest + 'm' : hours + 'h';
  };
  FAM.minutesLabel = function (minutes) {
    if (minutes === null || minutes === undefined) return 'No limit';
    if (minutes === 0) return 'No games';
    if (minutes < 60) return minutes + ' min';
    var h = Math.floor(minutes / 60);
    var m = minutes % 60;
    return m ? h + ' hr ' + m + ' min' : h + (h === 1 ? ' hour' : ' hours');
  };
  FAM.clock = function (hhmm) {
    var parts = String(hhmm || '').split(':');
    var h = parseInt(parts[0], 10);
    var m = parseInt(parts[1], 10) || 0;
    if (isNaN(h)) return hhmm;
    var suffix = h < 12 ? 'am' : 'pm';
    var shown = h % 12 || 12;
    return m ? shown + ':' + (m < 10 ? '0' : '') + m + ' ' + suffix : shown + ' ' + suffix;
  };

  /* --------------------------------------------------------- ad tracking
     Only does anything when the opt-in pixel is on the page. */
  FAM.track = function (event, params) {
    try { if (global.fbq) global.fbq('track', event, params || {}); } catch (e) {}
  };

  /* --------------------------------------------------------------- theme */
  function effectiveDark() {
    var t = doc.documentElement.getAttribute('data-theme');
    if (t === 'dark') return true;
    if (t === 'light') return false;
    return !!(global.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches);
  }
  FAM.setTheme = function (theme) {
    doc.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('blockhaven.theme', theme); } catch (e) {}
    doc.cookie = 'bh_theme=' + theme + '; path=/; max-age=31536000; samesite=lax' +
      (location.protocol === 'https:' ? '; secure' : '');
    $$('[data-theme-toggle]').forEach(function (b) { b.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false'); });
  };

  /* ---------------------------------------------------------------- boot */
  doc.addEventListener('click', function (e) {
    var toggle = e.target.closest('[data-theme-toggle]');
    if (toggle) {
      FAM.setTheme(effectiveDark() ? 'light' : 'dark');
      return;
    }
    var peek = e.target.closest('[data-peek]');
    if (peek) {
      var input = doc.getElementById(peek.getAttribute('data-peek'));
      if (!input) return;
      var show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      peek.setAttribute('aria-pressed', show ? 'true' : 'false');
      peek.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
      peek.innerHTML = '<svg class="f-ic sm"><use href="#i-' + (show ? 'eye-off' : 'eye') + '"/></svg>';
    }
  });

  function ready() {
    $$('[data-theme-toggle]').forEach(function (b) { b.setAttribute('aria-pressed', effectiveDark() ? 'true' : 'false'); });
    FAM.reveal();
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', ready);
  else ready();
})(window);
