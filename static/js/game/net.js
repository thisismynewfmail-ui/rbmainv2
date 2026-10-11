/* Websocket transport for the game view.
   The join ticket is minted by the website (signed, short lived); the socket
   itself is proxied through the same port into the world's host process. */
(function (global) {
  'use strict';

  function Net(worldId, instance) {
    this.worldId = worldId;
    this.instance = instance || '';
    this.handlers = {};
    this.socket = null;
    this.connected = false;
    this.queue = [];
    this.pingSent = 0;
    this.ping = 0;
    this.closedByUs = false;
    this.retries = 0;
    // When anything last arrived.  The host sends a snapshot twenty times a
    // second and answers our pings, so a socket that has carried nothing
    // for STALL_MS is not quiet, it is stuck: it is closed, and the client
    // rejoins (client.js) instead of showing a world frozen round a player
    // who can still walk.
    this.lastHeard = 0;
    this.stalled = false;
  }

  Net.STALL_MS = 8000;

  Net.prototype.on = function (kind, fn) {
    (this.handlers[kind] || (this.handlers[kind] = [])).push(fn);
    return this;
  };

  Net.prototype.emit = function (kind, payload) {
    var list = this.handlers[kind];
    if (list) for (var i = 0; i < list.length; i++) list[i](payload);
    var any = this.handlers['*'];
    if (any) for (i = 0; i < any.length; i++) any[i](kind, payload);
  };

  Net.prototype.connect = function () {
    var self = this;
    return fetch('/api/game/join', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': (window.BH && BH.csrf) || '',
        'X-Requested-With': 'fetch'
      },
      body: JSON.stringify({ world_id: this.worldId, instance: this.instance })
    }).then(function (r) { return r.json(); }).then(function (res) {
      if (!res.ok) throw new Error(res.error || 'Could not join.');
      var proto = location.protocol === 'https:' ? 'wss://' : 'ws://';
      var url = proto + location.host + res.ws;
      self.open(url);
      return res;
    });
  };

  Net.prototype.open = function (url) {
    var self = this;
    var socket = new WebSocket(url);
    this.socket = socket;
    socket.onopen = function () {
      self.connected = true;
      self.retries = 0;
      self.lastHeard = performance.now();
      self.emit('open');
      while (self.queue.length) socket.send(self.queue.shift());
      self.pingTimer = setInterval(function () { self.sendPing(); }, 2500);
      self.watchTimer = setInterval(function () { self.watch(); }, 1000);
    };
    socket.onmessage = function (event) {
      self.lastHeard = performance.now();
      var message;
      try { message = JSON.parse(event.data); } catch (e) { return; }
      if (message.t === 'pong') {
        self.ping = Math.max(0, Math.round(performance.now() - self.pingSent));
        self.emit('ping', self.ping);
        return;
      }
      self.emit(message.t, message);
    };
    socket.onclose = function () {
      self.connected = false;
      clearInterval(self.pingTimer);
      clearInterval(self.watchTimer);
      self.emit('close', { byUs: self.closedByUs, stalled: self.stalled });
    };
    socket.onerror = function () { self.emit('error'); };
  };

  /* The watchdog.  Only judged while the page is on screen: a background
     tab's timers are throttled and some browsers park its socket, and that
     is not a stall until somebody comes back to look at it -- at which
     point a dead connection is caught within a couple of seconds. */
  Net.prototype.watch = function () {
    if (!this.connected || !this.socket) return;
    if (document.visibilityState !== 'visible') return;
    if (performance.now() - this.lastHeard < Net.STALL_MS) return;
    this.stalled = true;
    try { this.socket.close(); } catch (e) { /* onclose follows */ }
    // some browsers take a long time to fire onclose on a dead link
    var self = this;
    setTimeout(function () {
      if (self.connected) {
        self.connected = false;
        clearInterval(self.pingTimer);
        clearInterval(self.watchTimer);
        self.emit('close', { byUs: false, stalled: true });
      }
    }, 1500);
  };

  Net.prototype.send = function (payload) {
    var text = JSON.stringify(payload);
    if (this.socket && this.socket.readyState === 1) this.socket.send(text);
    else if (this.queue.length < 40) this.queue.push(text);
  };

  Net.prototype.sendPing = function () {
    this.pingSent = performance.now();
    this.send({ t: 'ping', c: this.pingSent | 0 });
  };

  Net.prototype.close = function () {
    this.closedByUs = true;
    clearInterval(this.pingTimer);
    clearInterval(this.watchTimer);
    if (this.socket) { try { this.socket.close(); } catch (e) {} }
  };

  global.Net = Net;
})(window);
