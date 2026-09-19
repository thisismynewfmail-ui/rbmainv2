/* BLOCKHAVEN site -- shared page behaviour.
   Theme, mobile navigation, in-theme dialogs, the floating messenger, posts,
   comments, friends and follows. */
(function (global) {
  'use strict';

  var Site = {};

  Site.post = function (url, body) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': (window.BH && BH.csrf) || '',
        'X-Requested-With': 'fetch'
      },
      body: JSON.stringify(body || {})
    }).then(function (r) { return r.json(); });
  };

  Site.get = function (url) {
    return fetch(url, { headers: { 'X-Requested-With': 'fetch' } })
      .then(function (r) { return r.json(); });
  };

  Site.toast = function (message, kind) {
    var wrap = document.getElementById('site-toasts');
    if (!wrap) {
      wrap = document.createElement('div');
      wrap.id = 'site-toasts';
      document.body.appendChild(wrap);
    }
    var el = document.createElement('div');
    el.className = 'notice ' + (kind === 'bad' ? 'bad' : (kind === 'info' ? 'info' : ''));
    el.style.cssText = 'margin:0;box-shadow:0 4px 14px rgba(0,0,0,.3);max-width:320px';
    el.textContent = message;
    wrap.appendChild(el);
    setTimeout(function () {
      el.style.transition = 'opacity .4s, transform .4s';
      el.style.opacity = '0';
      el.style.transform = 'translateY(8px)';
      setTimeout(function () { el.remove(); }, 420);
    }, 3200);
  };

  Site.escape = function (text) {
    var div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
  };

  Site.ago = function (timestamp) {
    var delta = Math.max(0, Math.floor(Date.now() / 1000) - timestamp);
    if (delta < 60) return delta + ' seconds ago';
    if (delta < 3600) return Math.floor(delta / 60) + ' minutes ago';
    if (delta < 86400) return Math.floor(delta / 3600) + ' hours ago';
    return Math.floor(delta / 86400) + ' days ago';
  };

  Site.number = function (value) {
    return (parseInt(value, 10) || 0).toLocaleString();
  };

  // ------------------------------------------------------------ dialogs
  /* Every confirmation in the site goes through here rather than
     window.confirm, so a purchase prompt is part of the page chrome instead
     of a browser alert bolted on top of it. */
  Site.dialog = function (options) {
    options = options || {};
    return new Promise(function (resolve) {
      var scrim = document.createElement('div');
      // "centred" is the phone difference: a sheet glued to the bottom edge is
      // right for a yes/no, wrong for something you are meant to look at.
      scrim.className = 'modal-scrim' + (options.centered ? ' centered' : '');
      var confirmLabel = options.confirm || 'Confirm';
      var cancelLabel = options.cancel === null ? null : (options.cancel || 'Cancel');
      scrim.innerHTML =
        '<div class="panel" role="dialog" aria-modal="true">' +
        '<div class="panel-head ' + (options.tone || '') + '">' +
        '<span>' + Site.escape(options.title || 'Are you sure?') + '</span></div>' +
        '<div class="panel-body">' + (options.bodyHtml || '<p>' +
          Site.escape(options.body || '') + '</p>') +
        '<div class="modal-actions">' +
        (cancelLabel ? '<button class="btn" data-modal="cancel">' +
          Site.escape(cancelLabel) + '</button>' : '') +
        '<button class="btn ' + (options.danger ? 'danger' : 'primary') +
        '" data-modal="ok">' + Site.escape(confirmLabel) + '</button>' +
        '</div></div></div>';
      function close(result) {
        scrim.remove();
        document.removeEventListener('keydown', onKey);
        if (options.onClose) { try { options.onClose(); } catch (e) {} }
        resolve(result);
      }
      function onKey(event) {
        if (event.key === 'Escape') close(false);
        if (event.key === 'Enter') close(true);
      }
      scrim.addEventListener('click', function (event) {
        if (event.target === scrim) return close(false);
        var button = event.target.closest('[data-modal]');
        if (button) close(button.dataset.modal === 'ok');
      });
      document.addEventListener('keydown', onKey);
      document.body.appendChild(scrim);
      var ok = scrim.querySelector('[data-modal="ok"]');
      if (ok) ok.focus();
      if (window.Thumbs) Thumbs.rescan();
    });
  };

  /* A quick look at one item without leaving the page -- used by the item
     strip on a profile, where clicking a tile should show the piece rather
     than only ever jumping to the inventory. */
  Site.showItem = function (data) {
    var unusual = data.tier === 'unusual';
    var lines = [];
    if (data.slot) lines.push(['Slot', data.slot]);
    if (data.serial) lines.push(['Serial', '#' + data.serial]);
    lines.push(['Tier', unusual ? 'Unusual' : 'Normal']);
    if (data.effect_name) lines.push(['Effect', data.effect_name]);
    if (data.rarity) lines.push(['Rarity', data.rarity]);
    var body =
      '<div class="center"><canvas id="item-peek" width="320" height="320" ' +
      'style="width:210px;height:210px;max-width:100%;border-radius:6px;' +
      'border:1px solid var(--line-soft);background:' +
      (unusual ? 'var(--tile-unusual)' : 'var(--tile-normal)') + '"></canvas></div>' +
      '<dl class="kv" style="margin-top:12px">' +
      lines.map(function (row) {
        return '<dt>' + Site.escape(row[0]) + '</dt><dd>' +
          Site.escape(row[1]) + '</dd>';
      }).join('') + '</dl>' +
      (data.description ? '<p class="muted tiny" style="margin-top:8px">' +
        Site.escape(data.description) + '</p>' : '') +
      (data.href ? '<p style="margin-top:10px"><a class="btn small block" href="' +
        Site.escape(data.href) + '">Open the full inventory</a></p>' : '');
    var peek = null;
    var dialog = Site.dialog({
      title: data.name || 'Item',
      tone: unusual ? 'purple' : 'green',
      bodyHtml: body,
      confirm: 'Close',
      cancel: null,
      centered: true,
      // the effect has to stop with the dialog, or it keeps drawing into a
      // canvas nobody can see for as long as the page is open
      onClose: function () {
        if (peek && window.Thumbs && Thumbs.stopLive) Thumbs.stopLive(peek);
      }
    });
    setTimeout(function () {
      peek = document.getElementById('item-peek');
      if (!peek || !window.Thumbs) return;
      if (data.effect && Thumbs.animateItem) {
        Thumbs.animateItem(peek, data.item_id, data.effect);
      } else {
        Thumbs.renderItem(peek, data.item_id, data.effect || '');
      }
    }, 30);
    return dialog;
  };

  Site.confirm = function (title, body, options) {
    options = options || {};
    options.title = title;
    options.body = body;
    return Site.dialog(options);
  };

  // -------------------------------------------------------------- theme
  var THEME_KEY = 'blockhaven.theme';
  var THEME_COOKIE = 'bh_theme';

  /* The choice is written to a cookie as well as to localStorage.  Two
     reasons: the server can read a cookie, so the very first byte of the
     next page already carries the right data-theme instead of the browser
     repainting once the script runs; and it still works when localStorage
     throws, which it does in a private window and wherever site data is
     locked down.  Between the cookie, localStorage and (when signed in) the
     account row, no single one of them going missing loses the setting --
     including across a restart of the server. */
  function writeThemeCookie(theme) {
    try {
      if (theme === 'light' || theme === 'dark') {
        document.cookie = THEME_COOKIE + '=' + theme +
          '; Path=/; Max-Age=31536000; SameSite=Lax';
      } else {
        // 'auto' means stop overriding, so the cookie has to go rather than
        // sit there pinning the browser to a stale choice.
        document.cookie = THEME_COOKIE + '=; Path=/; Max-Age=0; SameSite=Lax';
      }
    } catch (e) {}
  }

  Site.theme = function () {
    return document.documentElement.getAttribute('data-theme') || 'auto';
  };

  Site.prefersDark = function () {
    return !!(window.matchMedia &&
              window.matchMedia('(prefers-color-scheme: dark)').matches);
  };

  Site.isDark = function () {
    var theme = Site.theme();
    return theme === 'dark' || (theme === 'auto' && Site.prefersDark());
  };

  Site.setTheme = function (theme, persist) {
    if (theme !== 'light' && theme !== 'dark') theme = 'auto';
    var root = document.documentElement;
    root.classList.add('theme-swap');
    root.setAttribute('data-theme', theme);
    if (window.BH) BH.theme = theme;
    syncThemeButtons();
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', Site.isDark() ? '#0a2b48' : '#14548e');
    setTimeout(function () { root.classList.remove('theme-swap'); }, 350);
    // the 3D previews paint their own sky, so they need telling too
    if (window.Thumbs && Thumbs.retheme) Thumbs.retheme();
    try { localStorage.setItem(THEME_KEY, theme); } catch (e) {}
    writeThemeCookie(theme);
    // Storing it on the account is what keeps a phone and a desktop agreeing.
    // If this never lands -- offline, expired session -- the cookie written
    // above still carries the choice, so the toggle is never a lie.
    if (persist !== false && window.BH && BH.user) {
      Site.post('/api/settings/theme', { theme: theme }).catch(function () {});
    }
  };

  /* ------------------------------------------------------- the moon knob
     The dark-mode knob is a moon, so it may as well be *the* moon: the phase
     it shows is the one actually in the sky tonight.  The construction is the
     textbook one -- half the disc lit, half in shadow, and an ellipse across
     the middle whose width is how far the terminator has swung -- which gives
     a true crescent, quarter, gibbous or full rather than a fixed bite taken
     out of a circle.  It is all CSS variables, so it costs one layout and no
     canvas.

     Reference new moon: 2000-01-06 18:14 UTC, the standard epoch, with the
     mean synodic month.  That is accurate to a few hours across a century --
     far better than a toggle button needs. */
  var SYNODIC = 29.530588853;
  var NEW_MOON_EPOCH = Date.UTC(2000, 0, 6, 18, 14, 0);
  var PHASE_NAMES = [
    'New moon', 'Waxing crescent', 'First quarter', 'Waxing gibbous',
    'Full moon', 'Waning gibbous', 'Last quarter', 'Waning crescent'
  ];

  Site.moonPhase = function (when) {
    var days = ((when || new Date()).getTime() - NEW_MOON_EPOCH) / 86400000;
    var age = days % SYNODIC;
    if (age < 0) age += SYNODIC;
    var phase = age / SYNODIC;                       // 0 new .. 0.5 full .. 1
    var lit = (1 - Math.cos(phase * Math.PI * 2)) / 2;
    // eight named phases, each centred on its own eighth of the cycle
    var index = Math.floor(phase * 8 + 0.5) % 8;
    return {
      phase: phase,
      age: age,
      lit: lit,
      waxing: phase < 0.5,
      name: PHASE_NAMES[index],
      percent: Math.round(lit * 100)
    };
  };

  function paintMoon(button, moon) {
    var knob = button.querySelector('.knob');
    if (!knob) return;
    // the lit half sits on the side the sun is on: right while waxing
    knob.style.setProperty('--limb-side', moon.waxing ? '0%' : '50%');
    knob.style.setProperty('--term-w', (Math.abs(1 - 2 * moon.lit) * 100) + '%');
    knob.style.setProperty('--term-fill',
      moon.lit < 0.5 ? 'var(--moon-dark)' : 'var(--moon-lit)');
  }

  function syncThemeButtons() {
    var dark = Site.isDark();
    var moon = Site.moonPhase();
    document.querySelectorAll('.themetoggle').forEach(function (button) {
      button.setAttribute('aria-pressed', dark ? 'true' : 'false');
      paintMoon(button, moon);
      button.title = dark
        ? 'Switch to light mode \u2014 tonight: ' + moon.name +
          ' (' + moon.percent + '% lit)'
        : 'Switch to dark mode';
      var label = button.getAttribute('aria-label') || 'Toggle dark mode';
      if (label.indexOf('Toggle') === 0) {
        button.setAttribute('aria-label',
          dark ? 'Toggle dark mode \u2014 ' + moon.name : 'Toggle dark mode');
      }
    });
  }


  function bindTheme() {
    syncThemeButtons();
    document.addEventListener('click', function (event) {
      var button = event.target.closest('.themetoggle');
      if (!button) return;
      event.preventDefault();
      Site.setTheme(Site.isDark() ? 'light' : 'dark');
    });
    if (window.matchMedia) {
      var query = window.matchMedia('(prefers-color-scheme: dark)');
      var onChange = function () { if (Site.theme() === 'auto') syncThemeButtons(); };
      if (query.addEventListener) query.addEventListener('change', onChange);
      else if (query.addListener) query.addListener(onChange);
    }
    // a tab left open overnight should not keep showing yesterday's moon
    setInterval(syncThemeButtons, 30 * 60 * 1000);
  }

  // ------------------------------------------------------- mobile drawer
  function bindNav() {
    var toggle = document.getElementById('nav-toggle');
    var nav = document.getElementById('main-nav');
    if (!toggle || !nav) return;
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.classList.toggle('on', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('click', function (event) {
      if (!nav.classList.contains('open')) return;
      if (nav.contains(event.target) || toggle.contains(event.target)) return;
      nav.classList.remove('open');
      toggle.classList.remove('on');
      toggle.setAttribute('aria-expanded', 'false');
    });
  }

  // ------------------------------------------------------- autocomplete
  /* A shared type-ahead for "who do you mean" boxes.  It is attached by
     markup (data-user-autocomplete) so the compose page and the floating
     messenger get exactly the same behaviour, keyboard handling included, and
     it drops the list into the field's own wrapper so a phone keyboard
     pushing the page around cannot leave it stranded. */
  var AC_MIN = 1;

  Site.autocomplete = function (input, options) {
    if (!input || input.__ac) return input && input.__ac;
    options = options || {};
    var wrap = input.closest('.ac-wrap') || input.parentNode;
    if (wrap === input.parentNode && !wrap.classList.contains('ac-wrap')) {
      wrap.classList.add('ac-wrap');
    }
    var list = document.createElement('div');
    list.className = 'ac-list';
    list.setAttribute('role', 'listbox');
    list.hidden = true;
    wrap.appendChild(list);

    var rows = [];
    var active = -1;
    var timer = 0;
    var lastQuery = null;

    function hide() {
      list.hidden = true;
      active = -1;
      input.setAttribute('aria-expanded', 'false');
    }

    function draw() {
      if (!rows.length) { hide(); return; }
      list.innerHTML = rows.map(function (row, index) {
        return '<button type="button" class="ac-row' +
          (index === active ? ' on' : '') + '" role="option" data-ac="' +
          Site.escape(row.username) + '" aria-selected="' +
          (index === active ? 'true' : 'false') + '">' +
          '<canvas class="ac-face avatar-thumb" width="96" height="96" data-user="' +
          Site.escape(row.username) + '"></canvas>' +
          '<span class="ac-name">' + Site.escape(row.username) + '</span>' +
          '<span class="ac-when">' + (row.online ? 'online' : '') + '</span>' +
          '</button>';
      }).join('');
      list.hidden = false;
      input.setAttribute('aria-expanded', 'true');
      if (window.Thumbs) Thumbs.rescan();
    }

    function choose(name) {
      input.value = name;
      hide();
      if (options.onPick) options.onPick(name);
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function search() {
      var term = (input.value || '').trim();
      if (term.length < AC_MIN) { rows = []; hide(); return; }
      if (term === lastQuery) return;
      lastQuery = term;
      Site.get('/api/users/suggest?q=' + encodeURIComponent(term))
        .then(function (res) {
          if (!res.ok) { rows = []; hide(); return; }
          if ((input.value || '').trim() !== term) return;   // raced ahead
          var now = Math.floor(Date.now() / 1000);
          rows = (res.users || []).map(function (row) {
            return { username: row.username,
                     online: (now - (row.last_seen || 0)) < 180 };
          });
          active = -1;
          draw();
        }).catch(function () { rows = []; hide(); });
    }

    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-expanded', 'false');
    input.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(search, 140);
    });
    input.addEventListener('focus', function () {
      if (rows.length && (input.value || '').trim()) draw();
    });
    input.addEventListener('keydown', function (event) {
      if (list.hidden || !rows.length) {
        if (event.key === 'ArrowDown') { clearTimeout(timer); lastQuery = null; search(); }
        return;
      }
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault();
        active += event.key === 'ArrowDown' ? 1 : -1;
        if (active < 0) active = rows.length - 1;
        if (active >= rows.length) active = 0;
        draw();
        var on = list.querySelector('.ac-row.on');
        if (on && on.scrollIntoView) on.scrollIntoView({ block: 'nearest' });
      } else if (event.key === 'Enter' && active >= 0) {
        event.preventDefault();
        choose(rows[active].username);
      } else if (event.key === 'Escape') {
        hide();
      } else if (event.key === 'Tab' && active >= 0) {
        choose(rows[active].username);
      }
    });
    // pointerdown, not click: the field must not lose focus before we read it
    list.addEventListener('pointerdown', function (event) {
      var row = event.target.closest('[data-ac]');
      if (!row) return;
      event.preventDefault();
      choose(row.dataset.ac);
    });
    input.addEventListener('blur', function () {
      setTimeout(hide, 120);
    });
    input.__ac = { hide: hide, search: search };
    return input.__ac;
  };

  function bindAutocomplete(root) {
    (root || document).querySelectorAll('[data-user-autocomplete]')
      .forEach(function (input) { Site.autocomplete(input); });
  }

  // --------------------------------------------------- floating messenger
  /* Two screens behind one bubble: the conversation list, and a direct
     message view that slides in over it.  Writing a note from here never
     costs the page you were reading, and Back walks you straight out of the
     conversation rather than back through the inbox. */
  var DOCK_KEY = 'blockhaven.dock';
  var dockLoaded = false;
  var dockScreen = 'list';
  var dockWith = '';

  function dockState() {
    try { return localStorage.getItem(DOCK_KEY); } catch (e) { return null; }
  }

  function el(id) { return document.getElementById(id); }

  function showDockScreen(screen, options) {
    options = options || {};
    var screens = el('dock-screens');
    var heading = el('dock-heading');
    var back = el('dock-back');
    var toRow = el('dock-to-row');
    if (!screens) return;
    dockScreen = screen;
    screens.classList.toggle('at-dm', screen === 'dm');
    // the phone layout raises the whole window for a conversation and puts
    // it back for the list -- see .dock.dm-open in the stylesheet
    var dock = el('msg-dock');
    if (dock) dock.classList.toggle('dm-open', screen === 'dm');
    if (back) back.classList.toggle('on', screen === 'dm');
    if (heading) {
      heading.textContent = screen === 'dm'
        ? (dockWith || 'New message') : 'Messages';
    }
    if (toRow) toRow.classList.toggle('hidden', screen === 'dm' && !!dockWith);
    if (screen === 'dm') {
      var focus = dockWith ? el('dock-body-text') : el('dock-to');
      if (focus && !options.quiet) setTimeout(function () { focus.focus(); }, 320);
    }
  }

  function openDockDM(username) {
    dockWith = username || '';
    var thread = el('dock-thread');
    var to = el('dock-to');
    if (to) to.value = dockWith;
    if (thread) {
      thread.innerHTML = dockWith
        ? '<div class="muted tiny" style="padding:12px">Loading the conversation...</div>'
        : '<div class="dock-blank"><b>New message</b>' +
          '<span>Type a name above, write below, press Send.</span></div>';
    }
    showDockScreen('dm');
    if (dockWith) loadDockThread(dockWith);
  }

  function loadDockThread(username) {
    var thread = el('dock-thread');
    if (!thread) return;
    Site.get('/api/messages/thread?with=' + encodeURIComponent(username))
      .then(function (res) {
        if (!res.ok) {
          thread.innerHTML = '<div class="muted tiny" style="padding:12px">' +
            Site.escape(res.error || 'Could not load that conversation.') + '</div>';
          return;
        }
        if (!res.rows.length) {
          thread.innerHTML = '<div class="dock-blank"><b>' +
            Site.escape(username) + '</b><span>No messages yet. Say hello.</span></div>';
        } else {
          thread.innerHTML = res.rows.map(function (row) {
            return '<div class="bubble ' + (row.mine ? 'me' : 'them') + '">' +
              Site.escape(row.body) + '<span class="stamp">' +
              Site.ago(row.created_at) + '</span></div>';
          }).join('');
        }
        thread.scrollTop = thread.scrollHeight;
        dockLoaded = false;
        Site.refreshCounts();
      }).catch(function () {
        thread.innerHTML = '<div class="muted tiny" style="padding:12px">Offline.</div>';
      });
  }

  function sendFromDock() {
    var toInput = el('dock-to');
    var bodyInput = el('dock-body-text');
    var button = el('dock-send');
    if (!bodyInput) return;
    var to = dockWith || ((toInput && toInput.value) || '').trim();
    var text = (bodyInput.value || '').trim();
    if (!to) {
      Site.toast('Who is it going to?', 'bad');
      if (toInput) toInput.focus();
      return;
    }
    if (!text) { bodyInput.focus(); return; }
    if (button) button.disabled = true;
    Site.post('/api/messages/send', { to: to, subject: '', body: text })
      .then(function (res) {
        if (button) button.disabled = false;
        if (!res.ok) { Site.toast(res.error, 'bad'); return; }
        bodyInput.value = '';
        dockWith = to;
        showDockScreen('dm', { quiet: true });
        loadDockThread(to);
        dockLoaded = false;
        Site.toast('Sent to ' + to + '.');
      }).catch(function () {
        if (button) button.disabled = false;
        Site.toast('Could not send that.', 'bad');
      });
  }

  function bindDock() {
    var dock = el('msg-dock');
    if (!dock) return;
    document.body.classList.add('has-dock');
    var toggle = el('dock-toggle');

    function setOpen(open) {
      dock.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      try { localStorage.setItem(DOCK_KEY, open ? 'open' : 'closed'); } catch (e) {}
      if (open) loadDock();
    }
    toggle.addEventListener('click', function () {
      setOpen(!dock.classList.contains('open'));
    });

    var back = el('dock-back');
    if (back) {
      back.addEventListener('click', function () {
        dockWith = '';
        showDockScreen('list');
        loadDock(true);
      });
    }
    var fresh = el('dock-new');
    if (fresh) fresh.addEventListener('click', function () { openDockDM(''); });

    var send = el('dock-send');
    if (send) send.addEventListener('click', sendFromDock);

    var text = el('dock-body-text');
    if (text) {
      text.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault();
          sendFromDock();
        }
      });
    }
    var to = el('dock-to');
    if (to) {
      Site.autocomplete(to, {
        onPick: function (name) {
          dockWith = name;
          var heading = el('dock-heading');
          if (heading) heading.textContent = name;
          loadDockThread(name);
          var body = el('dock-body-text');
          if (body) body.focus();
        }
      });
    }

    // a row in the list opens the conversation in place instead of navigating
    var body = el('dock-body');
    if (body) {
      body.addEventListener('click', function (event) {
        var row = event.target.closest('[data-dock-who]');
        if (!row) return;
        event.preventDefault();
        openDockDM(row.dataset.dockWho);
      });
    }

    trackViewport(dock);

    // restore whatever the player left it on -- including across a round of
    // the game, which navigates away from the site entirely
    if (dockState() === 'open') setOpen(true);
  }

  /* Keep the messenger sized and seated against the part of the window that
     is actually visible.

     A phone keyboard does not resize the window: it covers the bottom of it,
     and a position:fixed element stays happily underneath.  visualViewport is
     the only thing that knows -- its height is what is left above the
     keyboard and its offsetTop is how far the page has been scrolled up to
     keep the focused field in view.  Both go into CSS custom properties, so
     the stylesheet decides what to do with them and a desktop browser (where
     the two viewports agree) gets exactly what it had before. */
  function trackViewport(dock) {
    var vv = window.visualViewport;
    var lastLift = -1;
    function apply() {
      var height = vv ? vv.height : window.innerHeight;
      document.documentElement.style.setProperty('--vvh', Math.round(height) + 'px');
      var lift = vv
        ? Math.max(0, Math.round(window.innerHeight - vv.height - vv.offsetTop))
        : 0;
      dock.style.setProperty('--dock-lift', lift + 'px');
      dock.classList.toggle('keyboard-up', lift > 90);
      // the box changed height, so whatever was at the bottom of the
      // conversation is no longer there -- put it back
      if (lift !== lastLift && dockScreen === 'dm') {
        var thread = el('dock-thread');
        if (thread) {
          requestAnimationFrame(function () {
            thread.scrollTop = thread.scrollHeight;
          });
        }
      }
      lastLift = lift;
    }
    apply();
    if (vv) {
      vv.addEventListener('resize', apply);
      vv.addEventListener('scroll', apply);
    }
    window.addEventListener('resize', apply);
    window.addEventListener('orientationchange', function () {
      setTimeout(apply, 250);
    });
  }

  function loadDock(force) {
    if (dockLoaded && !force) return;
    dockLoaded = true;
    var body = el('dock-body');
    if (!body) return;
    Site.get('/api/messages/recent').then(function (res) {
      if (!res.ok) { body.innerHTML = '<div class="muted tiny" style="padding:12px">Could not load messages.</div>'; return; }
      if (!res.rows.length) {
        body.innerHTML = '<div class="dock-blank"><b>No messages yet</b>' +
          '<span>Say hello to somebody.</span></div>';
        return;
      }
      body.innerHTML = '<div class="msglist">' + res.rows.map(function (row) {
        return '<a class="msgrow' + (row.unread ? ' unread' : '') +
          '" href="/messages/' + row.id + '" data-dock-who="' +
          Site.escape(row.who) + '">' +
          '<canvas class="who-thumb avatar-thumb" width="120" height="120" data-user="' +
          Site.escape(row.who) + '"></canvas>' +
          '<span class="msgmain"><span class="msgtop">' +
          '<span class="msgwho">' + Site.escape(row.who) +
          (row.total > 1 ? ' <span class="pill tiny">' + row.total + '</span>' : '') +
          (row.unread ? ' <span class="badge alert">' + row.unread + '</span>' : '') +
          '</span>' +
          '<span class="msgwhen">' + Site.ago(row.created_at) + '</span></span>' +
          '<span class="msgsubject">' + Site.escape(row.subject) + '</span>' +
          '<span class="msgpreview">' + Site.escape(row.preview) + '</span>' +
          '</span></a>';
      }).join('') + '</div>';
      if (window.Thumbs) Thumbs.rescan();
    }).catch(function () {
      body.innerHTML = '<div class="muted tiny" style="padding:12px">Offline.</div>';
    });
  }

  // --------------------------------------------------- messenger setting
  function bindMessengerSwitch() {
    var button = document.getElementById('messenger-toggle');
    if (!button) return;
    button.addEventListener('click', function () {
      var on = button.getAttribute('aria-checked') !== 'true';
      button.setAttribute('aria-checked', on ? 'true' : 'false');
      Site.post('/api/settings/prefs', { messenger: on }).then(function (res) {
        if (!res.ok) {
          button.setAttribute('aria-checked', on ? 'false' : 'true');
          Site.toast(res.error || 'Could not save that.', 'bad');
          return;
        }
        var dock = document.getElementById('msg-dock');
        if (dock && !on) {
          dock.remove();
          document.body.classList.remove('has-dock');
        }
        Site.toast(on ? 'The message bubble is on. Reload to see it.'
                      : 'The message bubble is off.');
      });
    });
  }

  // ------------------------------------------------------------------ posts
  function bindPosts() {
    var form = document.getElementById('post-form');
    var body = document.getElementById('post-body');
    var count = document.getElementById('post-count');
    if (body && count) {
      body.addEventListener('input', function () {
        count.textContent = String(400 - body.value.length);
      });
    }
    var submit = document.getElementById('post-submit');
    if (submit) {
      submit.addEventListener('click', function () {
        var text = (body.value || '').trim();
        if (!text) { Site.toast('Write something first.', 'bad'); return; }
        submit.disabled = true;
        Site.post('/api/social/post', { body: text }).then(function (res) {
          submit.disabled = false;
          if (!res.ok) { Site.toast(res.error, 'bad'); return; }
          body.value = '';
          if (count) count.textContent = '400';
          Site.toast('Posted!');
          setTimeout(function () { location.reload(); }, 350);
        });
      });
    }
    if (form) form.addEventListener('submit', function (e) { e.preventDefault(); });
  }

  document.addEventListener('click', function (event) {
    var peek = event.target.closest('[data-item-peek]');
    if (peek) {
      event.preventDefault();
      Site.showItem({
        item_id: peek.dataset.itemPeek,
        name: peek.dataset.name,
        slot: peek.dataset.slotLabel,
        serial: peek.dataset.serial,
        tier: peek.dataset.tier,
        effect: peek.dataset.effect,
        effect_name: peek.dataset.effectName,
        rarity: peek.dataset.rarity,
        href: peek.dataset.href
      });
      return;
    }
    var target = event.target.closest('[data-post-like]');
    if (target) {
      var id = parseInt(target.dataset.postLike, 10);
      Site.post('/api/social/post/like', { id: id }).then(function (res) {
        if (!res.ok) { Site.toast(res.error, 'bad'); return; }
        var counter = target.querySelector('.likecount');
        if (counter) counter.textContent = res.likes;
        target.classList.toggle('liked', res.liked);
        target.style.color = res.liked ? 'var(--link-hover)' : '';
      });
      return;
    }
    target = event.target.closest('[data-post-delete]');
    if (target) {
      var node = target;
      Site.confirm('Delete this post?', 'It will be removed for everybody.',
                   { confirm: 'Delete', danger: true, tone: 'red' })
        .then(function (yes) {
          if (!yes) return;
          Site.post('/api/social/post/delete', { id: parseInt(node.dataset.postDelete, 10) })
            .then(function (res) {
              if (!res.ok) { Site.toast(res.error, 'bad'); return; }
              var post = node.closest('.post');
              if (post) post.remove();
            });
        });
      return;
    }
    target = event.target.closest('[data-post-comments]');
    if (target) {
      var postId = parseInt(target.dataset.postComments, 10);
      var box = document.querySelector('[data-comments-for="' + postId + '"]');
      if (!box) return;
      if (!box.classList.contains('hidden')) { box.classList.add('hidden'); return; }
      box.classList.remove('hidden');
      box.innerHTML = '<div class="muted tiny">loading...</div>';
      Site.get('/api/social/post/comments?id=' + postId).then(function (res) {
        renderComments(box, postId, res.comments || []);
      });
      return;
    }
    target = event.target.closest('[data-wall-delete]');
    if (target) {
      var wallNode = target;
      Site.confirm('Remove this comment?', '', { confirm: 'Remove', danger: true, tone: 'red' })
        .then(function (yes) {
          if (!yes) return;
          Site.post('/api/profile/comment/delete', { id: parseInt(wallNode.dataset.wallDelete, 10) })
            .then(function (res) {
              if (!res.ok) { Site.toast(res.error, 'bad'); return; }
              var row = wallNode.closest('.post');
              if (row) row.remove();
            });
        });
      return;
    }
    target = event.target.closest('[data-friend]');
    if (target) {
      var action = target.dataset.friend;
      var username = target.dataset.username;
      var button = target;
      function runFriend() {
        button.disabled = true;
        Site.post('/api/social/friend', { action: action, username: username })
          .then(function (res) {
            button.disabled = false;
            if (!res.ok) { Site.toast(res.error, 'bad'); return; }
            Site.toast(labelFor(res.state, username));
            if (button.id === 'friend-btn') updateFriendButton(button, res.state);
            else if (button.dataset.friendInline) updateInlineFriend(button, res.state);
            else setTimeout(function () { location.reload(); }, 400);
          });
      }
      /* Unfriending is the one social action with no undo, and the button
         sits right under Send message, so it asks first.  Cancelling a
         request you sent uses the same "remove" action and is harmless, so
         that one still goes straight through. */
      if (action === 'remove' && button.dataset.state === 'friends') {
        Site.confirm('Remove ' + username + ' as a friend?',
                     'You will both drop off each other\u2019s friends lists. ' +
                     'You can send a new request later.',
                     { confirm: 'Remove friend', cancel: 'Keep them',
                       danger: true, tone: 'red' })
          .then(function (yes) { if (yes) runFriend(); });
        return;
      }
      runFriend();
      return;
    }
    target = event.target.closest('[data-follow-toggle], #follow-btn');
    if (target) {
      var name = target.dataset.followToggle || target.dataset.username;
      target.disabled = true;
      Site.post('/api/social/follow', { username: name }).then(function (res) {
        target.disabled = false;
        if (!res.ok) { Site.toast(res.error, 'bad'); return; }
        target.textContent = res.following ? 'Unfollow' : 'Follow';
        target.dataset.state = res.following ? '1' : '0';
        Site.toast(res.following ? 'Following ' + name : 'Unfollowed ' + name);
      });
    }
  });

  function labelFor(state, username) {
    if (state === 'friends') return 'You are now friends with ' + username + '!';
    if (state === 'pending_out') return 'Friend request sent to ' + username + '.';
    if (state === 'none') return 'Updated.';
    return 'Updated.';
  }

  /* The profile button carries three states.  "Request sent" is deliberately
     red and stays clickable so it doubles as "cancel the request". */
  function updateFriendButton(button, state) {
    button.dataset.state = state;   // the confirm prompt reads this
    button.classList.remove('go', 'danger', 'primary');
    if (state === 'friends') {
      button.textContent = 'Remove friend';
      button.dataset.friend = 'remove';
      button.classList.add('danger');
    } else if (state === 'pending_out') {
      button.textContent = 'Request sent';
      button.dataset.friend = 'remove';
      button.title = 'Click to cancel the request';
      button.classList.add('danger');
    } else if (state === 'pending_in') {
      button.textContent = 'Accept request';
      button.dataset.friend = 'accept';
      button.classList.add('go');
    } else {
      button.textContent = 'Add friend';
      button.dataset.friend = 'request';
      button.title = '';
      button.classList.add('go');
    }
  }

  function updateInlineFriend(button, state) {
    button.classList.remove('go', 'danger');
    if (state === 'friends') { button.textContent = 'Friends'; button.disabled = true; }
    else if (state === 'pending_out') {
      button.textContent = 'Request sent';
      button.classList.add('danger');
      button.dataset.friend = 'remove';
    } else { button.textContent = 'Add'; button.classList.add('go'); button.dataset.friend = 'request'; }
  }

  Site.updateFriendButton = updateFriendButton;

  function renderComments(box, postId, comments) {
    var html = comments.map(function (c) {
      return '<div class="comment"><a href="/profile/' + encodeURIComponent(c.username) +
        '"><b>' + Site.escape(c.username) + '</b></a> <span class="when">' +
        Site.ago(c.created_at) + '</span><div>' + Site.escape(c.body) + '</div></div>';
    }).join('');
    if (window.BH && BH.user) {
      html += '<form class="commentbox" data-comment-form="' + postId + '">' +
        '<input type="text" maxlength="300" placeholder="Write a reply">' +
        '<button class="btn small primary">Reply</button></form>';
    }
    box.innerHTML = html || '<div class="muted tiny">No comments yet.</div>';
  }

  /* Any form carrying data-confirm gets the in-theme dialog instead of the
     browser's, then submits itself once the answer comes back. */
  document.addEventListener('submit', function (event) {
    var guarded = event.target.closest('[data-confirm]');
    if (guarded && !guarded.dataset.confirmed) {
      event.preventDefault();
      Site.confirm(guarded.dataset.confirm, guarded.dataset.confirmBody || '',
                   { confirm: guarded.dataset.confirmLabel || 'Yes',
                     danger: true, tone: 'red' })
        .then(function (yes) {
          if (!yes) return;
          guarded.dataset.confirmed = '1';
          guarded.submit();
        });
      return;
    }
  }, true);

  document.addEventListener('submit', function (event) {
    var form = event.target.closest('[data-comment-form]');
    if (form) {
      event.preventDefault();
      var postId = parseInt(form.dataset.commentForm, 10);
      var input = form.querySelector('input');
      var text = (input.value || '').trim();
      if (!text) return;
      Site.post('/api/social/post/comment', { id: postId, body: text })
        .then(function (res) {
          if (!res.ok) { Site.toast(res.error, 'bad'); return; }
          var box = document.querySelector('[data-comments-for="' + postId + '"]');
          renderComments(box, postId, res.comments || []);
        });
      return;
    }
    var wall = event.target.closest('#wall-form');
    if (wall) {
      event.preventDefault();
      var body = document.getElementById('wall-body');
      var value = (body.value || '').trim();
      if (!value) return;
      Site.post('/api/profile/comment', {
        username: wall.dataset.username, body: value
      }).then(function (res) {
        if (!res.ok) { Site.toast(res.error, 'bad'); return; }
        body.value = '';
        renderWall(res.wall || []);
        Site.toast('Comment posted.');
      });
    }
  });

  function renderWall(rows) {
    var list = document.getElementById('wall-list');
    if (!list) return;
    list.innerHTML = rows.map(function (c) {
      return '<div class="post" data-wall="' + c.id + '"><div class="spread"><div>' +
        '<a class="who" href="/profile/' + encodeURIComponent(c.username) + '">' +
        Site.escape(c.username) + '</a> <span class="when">' + Site.ago(c.created_at) +
        '</span></div><a class="tiny muted" data-wall-delete="' + c.id + '">delete</a>' +
        '</div><div class="body">' + Site.escape(c.body) + '</div></div>';
    }).join('');
  }

  // ------------------------------------------------------- live nav counters
  /* Polled rather than pushed, because the same account may well be signed in
     on a phone and a desktop at once: whichever tab reads first, both end up
     showing the server's numbers, the server's Nooget balance and the
     server's theme choice. */
  var lastCounts = { unread: -1, requests: -1 };

  function pollCounts() {
    if (!window.BH || !BH.user) return;
    Site.get('/api/social/counts').then(function (res) {
      if (!res.ok) return;
      updateBadge('/messages', res.unread, 'alert', lastCounts.unread);
      updateBadge('/friends', res.requests, '', lastCounts.requests);
      if (res.requests > lastCounts.requests && lastCounts.requests >= 0) {
        Site.toast(res.requests === 1
          ? 'You have a new friend request.'
          : 'You have ' + res.requests + ' friend requests.', 'info');
      }
      if (res.unread > lastCounts.unread && lastCounts.unread >= 0) {
        dockLoaded = false;
        if (document.getElementById('msg-dock') &&
            document.getElementById('msg-dock').classList.contains('open')) loadDock(true);
      }
      lastCounts.unread = res.unread;
      lastCounts.requests = res.requests;
      var badge = document.getElementById('dock-badge');
      if (badge) {
        badge.textContent = res.unread;
        badge.classList.toggle('hidden', !res.unread);
      }
      var wallet = document.getElementById('wallet-amount');
      if (wallet && res.credits !== undefined) wallet.textContent = Site.number(res.credits);
      var big = document.getElementById('wallet-big');
      if (big && res.credits !== undefined) big.textContent = Site.number(res.credits);
      if (res.theme && res.theme !== Site.theme()) Site.setTheme(res.theme, false);
    }).catch(function () {});
  }

  function updateBadge(href, value, cls, previous) {
    var links = document.querySelectorAll('.tabbar a[href="' + href + '"]');
    links.forEach(function (link) {
      var badge = link.querySelector('.badge');
      if (!value) { if (badge) badge.remove(); return; }
      if (!badge) {
        badge = document.createElement('span');
        badge.className = 'badge ' + cls;
        link.appendChild(document.createTextNode(' '));
        link.appendChild(badge);
      }
      badge.textContent = value;
      if (previous >= 0 && value > previous) {
        badge.classList.remove('pop');
        void badge.offsetWidth;
        badge.classList.add('pop');
      }
    });
  }

  Site.refreshCounts = pollCounts;

  // ---------------------------------------------------------- folded lists
  /* A list that shows its first few entries and keeps the rest behind one
     button -- the friends grid on a profile is the first of them.  The
     markup carries the whole list and CSS hides the tail, so the button is
     instant and costs no request, and nothing is lost to a reader without
     JavaScript (the fold only closes once this has run).

     Newly revealed thumbnails have to be handed back to the painter: the
     canvases were display:none when the page loaded, so the observer that
     paints them on scroll never saw them. */
  function bindFolds() {
    document.querySelectorAll('[data-fold-toggle]').forEach(function (button) {
      var list = document.querySelector('[data-fold="' + button.dataset.foldToggle + '"]');
      if (!list) return;
      list.classList.add('folded');
      button.classList.remove('hidden');
      button.setAttribute('aria-expanded', 'false');
      var more = button.dataset.moreLabel || 'Show all';
      var less = button.dataset.lessLabel || 'Show fewer';
      var label = button.querySelector('.fold-label') || button;
      label.textContent = more;
      button.addEventListener('click', function () {
        var open = !list.classList.contains('folded');
        list.classList.toggle('folded', open);
        button.classList.toggle('open', !open);
        button.setAttribute('aria-expanded', open ? 'false' : 'true');
        label.textContent = open ? more : less;
        if (!open && window.Thumbs) Thumbs.rescan();
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    bindTheme();
    bindNav();
    bindDock();
    bindPosts();
    bindFolds();
    bindAutocomplete();
    bindMessengerSwitch();
    if (window.BH && BH.user) {
      pollCounts();
      setInterval(pollCounts, 20000);
      document.addEventListener('visibilitychange', function () {
        if (!document.hidden) pollCounts();
      });
    }
  });

  global.Site = Site;
})(window);
