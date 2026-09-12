/* Game settings and key bindings.

   Two homes, on purpose.  Key bindings and the aim settings describe the
   *player*, so they live on the account: rebind crouch on a laptop and the
   desktop upstairs is already rebound.  Render scale, view distance, volume
   and the like describe the *machine*, so those stay in this browser -- a
   phone and a gaming desktop have no business sharing a render scale.

   The account copy arrives on the page as BH.controls, so the first frame is
   already bound correctly; changes are written back through
   /api/game/controls.  localStorage still shadows everything, so a dropped
   connection or a signed-out session never loses a binding. */
(function (global) {
  'use strict';

  var KEY = 'blockhaven.settings.v1';

  var DEFAULT_BINDS = {
    forward: 'KeyW', back: 'KeyS', left: 'KeyA', right: 'KeyD',
    jump: 'Space', sprint: 'ShiftLeft', crouch: 'ControlLeft',
    reload: 'KeyR', interact: 'KeyE', camera: 'KeyG',
    chat: 'KeyY', teamchat: 'KeyU', scoreboard: 'Tab', map: 'KeyM',
    slot1: 'Digit1', slot2: 'Digit2', slot3: 'Digit3', slot4: 'Digit4',
    slot5: 'Digit5'
  };

  var BIND_LABELS = {
    forward: 'Move forward', back: 'Move back', left: 'Strafe left',
    right: 'Strafe right', jump: 'Jump', sprint: 'Walk slowly',
    crouch: 'Crouch', reload: 'Reload', interact: 'Interact',
    camera: 'Third person', chat: 'Chat', teamchat: 'Team chat',
    scoreboard: 'Scoreboard', map: 'Objective info',
    slot1: 'Hotbar 1', slot2: 'Hotbar 2', slot3: 'Hotbar 3',
    slot4: 'Hotbar 4', slot5: 'Hotbar 5'
  };

  /* Which settings follow the account.  Everything else is per-device. */
  var ACCOUNT_KEYS = ['sensitivity', 'fov', 'invertY', 'rawMouse'];

  var DEFAULTS = {
    // Read from raw movementX/Y with no browser acceleration applied (see
    // rawMouse below).  This is the speed the game has always shipped with,
    // and it is where the slider sits until somebody moves it.
    sensitivity: 0.24,
    fov: 82,
    invertY: false,
    rawMouse: true,
    renderScale: 1,
    viewDistance: 900,
    particles: true,
    showNames: true,
    volume: 0.55,
    binds: DEFAULT_BINDS
  };

  function stored() {
    try { return JSON.parse(localStorage.getItem(KEY) || '{}') || {}; }
    catch (e) { return {}; }
  }

  function load() {
    var data = stored();
    var account = (global.BH && global.BH.controls) || null;
    var out = {};
    Object.keys(DEFAULTS).forEach(function (k) {
      out[k] = (data[k] === undefined) ? DEFAULTS[k] : data[k];
    });
    out.binds = Object.assign({}, DEFAULT_BINDS, data.binds || {});
    /* The account wins wherever it has an opinion.  It only carries the keys
       the player actually changed, so an untouched account leaves whatever
       this browser was already using -- which is what quietly carries an
       existing local setup up onto the account the first time it is saved. */
    if (account) {
      ACCOUNT_KEYS.forEach(function (k) {
        if (account[k] !== undefined) out[k] = account[k];
      });
      if (account.binds) Object.assign(out.binds, account.binds);
    }
    return out;
  }

  var Settings = load();

  /* Only the differences go to the server: storing a full set would freeze
     today's defaults onto the account for ever, so a later change to a
     default would never reach anybody who had once opened this menu. */
  function accountPayload() {
    var payload = { binds: {} };
    Object.keys(DEFAULT_BINDS).forEach(function (action) {
      var code = Settings.binds[action];
      // "" is a deliberate unbind and has to travel: dropping it as falsy
      // would hand the default straight back on the next machine.
      if (code !== undefined && code !== DEFAULT_BINDS[action]) {
        payload.binds[action] = code;
      }
    });
    ACCOUNT_KEYS.forEach(function (k) {
      if (Settings[k] !== DEFAULTS[k]) payload[k] = Settings[k];
    });
    return payload;
  }

  Settings.accountPayload = accountPayload;

  var syncTimer = 0;
  var syncing = false;

  /* Batched, because a slider drag fires on every pixel.  The status the
     menu shows comes back through Settings.onSync. */
  function syncAccount() {
    if (!global.BH || !global.BH.user) return;
    clearTimeout(syncTimer);
    syncTimer = setTimeout(function () {
      syncing = true;
      if (Settings.onSync) Settings.onSync('saving');
      fetch('/api/game/controls', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': (global.BH && global.BH.csrf) || '',
          'X-Requested-With': 'fetch'
        },
        body: JSON.stringify({ controls: accountPayload() })
      }).then(function (r) { return r.json(); }).then(function (res) {
        syncing = false;
        if (Settings.onSync) Settings.onSync(res && res.ok ? 'saved' : 'failed');
      }).catch(function () {
        syncing = false;
        // the local copy still holds it, so this is a note rather than a loss
        if (Settings.onSync) Settings.onSync('offline');
      });
    }, 450);
  }

  Settings.save = function (options) {
    try {
      var copy = {};
      Object.keys(DEFAULTS).forEach(function (k) { copy[k] = Settings[k]; });
      localStorage.setItem(KEY, JSON.stringify(copy));
    } catch (e) { /* private browsing */ }
    if (!options || options.account !== false) syncAccount();
  };

  Settings.reset = function () {
    var fresh = JSON.parse(JSON.stringify(DEFAULTS));
    Object.keys(fresh).forEach(function (k) { Settings[k] = fresh[k]; });
    Settings.save();
  };

  /* Bindings only: the display and audio settings are not the player's to
     lose when they are only trying to put WASD back. */
  Settings.resetBinds = function () {
    Settings.binds = Object.assign({}, DEFAULT_BINDS);
    Settings.save();
  };

  /* A key can only do one job.  Whatever held it lets go, and the caller is
     told so it can repaint that row. */
  Settings.bind = function (action, code) {
    var freed = [];
    Object.keys(Settings.binds).forEach(function (other) {
      if (other !== action && Settings.binds[other] === code) {
        Settings.binds[other] = '';
        freed.push(other);
      }
    });
    Settings.binds[action] = code;
    Settings.save();
    return freed;
  };

  /* One-time migration for browsers carrying the previous defaults: the
     camera toggle moved from P to G and the base sensitivity went up. */
  (function migrate() {
    var stamp = 'blockhaven.settings.migrated.v2';
    var done = false;
    try { done = localStorage.getItem(stamp) === '1'; } catch (e) { done = true; }
    if (done) return;
    if (Settings.binds.camera === 'KeyP') Settings.binds.camera = 'KeyG';
    if (Math.abs(Settings.sensitivity - 0.16) < 0.001) {
      Settings.sensitivity = DEFAULTS.sensitivity;
    }
    Settings.save({ account: false });
    try { localStorage.setItem(stamp, '1'); } catch (e) {}
  })();

  Settings.DEFAULTS = DEFAULTS;
  Settings.BIND_LABELS = BIND_LABELS;
  Settings.DEFAULT_BINDS = DEFAULT_BINDS;
  Settings.ACCOUNT_KEYS = ACCOUNT_KEYS;

  Settings.actionFor = function (code) {
    if (!code) return null;
    var binds = Settings.binds;
    for (var action in binds) {
      if (binds[action] === code) return action;
    }
    return null;
  };

  Settings.keyLabel = function (code) {
    if (!code) return 'unbound';
    return String(code)
      .replace('Key', '').replace('Digit', '')
      .replace('Left', ' L').replace('Right', ' R')
      .replace('Arrow', '');
  };

  global.Settings = Settings;
})(window);
