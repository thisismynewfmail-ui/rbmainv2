/* BLOCKHAVEN engine -- all sound is synthesised with the Web Audio API, so
   there are no audio files to ship and nothing to download. */
(function (global) {
  'use strict';

  function Audio() {
    this.ctx = null;
    this.volume = 0.6;
    this.enabled = true;
  }

  Audio.prototype.resume = function () {
    if (!this.ctx) {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) { this.enabled = false; return; }
      this.ctx = new Ctx();
      this.master = this.ctx.createGain();
      this.master.gain.value = this.volume;
      this.master.connect(this.ctx.destination);
      this.noiseBuffer = this.makeNoise();
    }
    if (this.ctx.state === 'suspended') this.ctx.resume();
  };

  Audio.prototype.setVolume = function (v) {
    this.volume = v;
    if (this.master) this.master.gain.value = v;
  };

  Audio.prototype.makeNoise = function () {
    var length = this.ctx.sampleRate * 1.2;
    var buffer = this.ctx.createBuffer(1, length, this.ctx.sampleRate);
    var data = buffer.getChannelData(0);
    for (var i = 0; i < length; i++) data[i] = Math.random() * 2 - 1;
    return buffer;
  };

  Audio.prototype.tone = function (opts) {
    if (!this.enabled || !this.ctx) return;
    var now = this.ctx.currentTime;
    var osc = this.ctx.createOscillator();
    var gain = this.ctx.createGain();
    osc.type = opts.type || 'sine';
    osc.frequency.setValueAtTime(opts.freq || 440, now);
    if (opts.freqEnd) {
      osc.frequency.exponentialRampToValueAtTime(Math.max(20, opts.freqEnd),
                                                 now + (opts.dur || 0.2));
    }
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(Math.max(0.0002, opts.gain || 0.2),
                                           now + 0.006);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + (opts.dur || 0.2));
    osc.connect(gain);
    gain.connect(this.master);
    osc.start(now);
    osc.stop(now + (opts.dur || 0.2) + 0.05);
  };

  Audio.prototype.noise = function (opts) {
    if (!this.enabled || !this.ctx) return;
    var now = this.ctx.currentTime;
    var src = this.ctx.createBufferSource();
    src.buffer = this.noiseBuffer;
    var filter = this.ctx.createBiquadFilter();
    filter.type = opts.filter || 'lowpass';
    filter.frequency.setValueAtTime(opts.freq || 1200, now);
    if (opts.freqEnd) {
      filter.frequency.exponentialRampToValueAtTime(Math.max(60, opts.freqEnd),
                                                    now + (opts.dur || 0.2));
    }
    var gain = this.ctx.createGain();
    gain.gain.setValueAtTime(opts.gain || 0.25, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + (opts.dur || 0.2));
    src.connect(filter); filter.connect(gain); gain.connect(this.master);
    src.start(now);
    src.stop(now + (opts.dur || 0.2) + 0.02);
  };

  Audio.prototype.play = function (name, options) {
    if (!this.enabled) return;
    this.resume();
    if (!this.ctx) return;
    options = options || {};
    var vol = options.volume === undefined ? 1 : options.volume;
    switch (name) {
      case 'pistol':
        this.noise({ freq: 2600, freqEnd: 320, dur: 0.14, gain: 0.3 * vol });
        this.tone({ type: 'square', freq: 260, freqEnd: 70, dur: 0.1, gain: 0.16 * vol });
        break;
      case 'shotgun':
        this.noise({ freq: 1800, freqEnd: 150, dur: 0.34, gain: 0.42 * vol });
        this.tone({ type: 'sawtooth', freq: 150, freqEnd: 44, dur: 0.26, gain: 0.22 * vol });
        break;
      case 'smg':
        this.noise({ freq: 3000, freqEnd: 500, dur: 0.08, gain: 0.22 * vol });
        this.tone({ type: 'square', freq: 320, freqEnd: 110, dur: 0.06, gain: 0.1 * vol });
        break;
      case 'rifle':
        this.noise({ freq: 3400, freqEnd: 400, dur: 0.2, gain: 0.32 * vol });
        this.tone({ type: 'square', freq: 220, freqEnd: 60, dur: 0.16, gain: 0.16 * vol });
        break;
      case 'sniper':
        this.noise({ freq: 4200, freqEnd: 220, dur: 0.5, gain: 0.4 * vol });
        this.tone({ type: 'sawtooth', freq: 190, freqEnd: 40, dur: 0.42, gain: 0.2 * vol });
        break;
      case 'rocket':
        this.noise({ freq: 900, freqEnd: 90, dur: 0.5, gain: 0.4 * vol });
        this.tone({ type: 'sawtooth', freq: 120, freqEnd: 38, dur: 0.5, gain: 0.24 * vol });
        break;
      case 'explode':
        this.noise({ freq: 700, freqEnd: 45, dur: 0.85, gain: 0.5 * vol });
        this.tone({ type: 'sine', freq: 90, freqEnd: 28, dur: 0.7, gain: 0.3 * vol });
        break;
      case 'swing':
        this.noise({ filter: 'bandpass', freq: 900, freqEnd: 2200, dur: 0.16,
                     gain: 0.2 * vol });
        break;
      case 'sword':
        this.tone({ type: 'triangle', freq: 1200, freqEnd: 400, dur: 0.2, gain: 0.16 * vol });
        this.noise({ filter: 'bandpass', freq: 2400, dur: 0.18, gain: 0.14 * vol });
        break;
      case 'hit':
        this.tone({ type: 'square', freq: 1500, freqEnd: 900, dur: 0.06, gain: 0.16 * vol });
        break;
      case 'hurt':
        this.tone({ type: 'sawtooth', freq: 300, freqEnd: 120, dur: 0.2, gain: 0.2 * vol });
        break;
      case 'die':
        this.tone({ type: 'sawtooth', freq: 260, freqEnd: 60, dur: 0.6, gain: 0.24 * vol });
        break;
      case 'kill':
        this.tone({ type: 'square', freq: 660, dur: 0.09, gain: 0.16 * vol });
        setTimeout(function (self) {
          return function () { self.tone({ type: 'square', freq: 990, dur: 0.12, gain: 0.16 * vol }); };
        }(this), 80);
        break;
      case 'jump':
        this.tone({ type: 'sine', freq: 420, freqEnd: 700, dur: 0.1, gain: 0.1 * vol });
        break;
      case 'land':
        this.noise({ freq: 500, freqEnd: 120, dur: 0.12, gain: 0.14 * vol });
        break;
      case 'reload':
        this.noise({ filter: 'bandpass', freq: 1400, dur: 0.1, gain: 0.18 * vol });
        break;
      case 'heal':
        this.tone({ type: 'sine', freq: 520, freqEnd: 900, dur: 0.24, gain: 0.14 * vol });
        break;
      case 'coin':
        this.tone({ type: 'square', freq: 990, dur: 0.07, gain: 0.12 * vol });
        setTimeout(function (self) {
          return function () { self.tone({ type: 'square', freq: 1320, dur: 0.12, gain: 0.12 * vol }); };
        }(this), 70);
        break;
      case 'build':
        this.tone({ type: 'square', freq: 300, freqEnd: 800, dur: 0.25, gain: 0.16 * vol });
        this.noise({ freq: 1400, freqEnd: 300, dur: 0.3, gain: 0.14 * vol });
        break;
      case 'chat':
        this.tone({ type: 'sine', freq: 880, dur: 0.06, gain: 0.07 * vol });
        break;
      case 'ui':
        this.tone({ type: 'square', freq: 620, dur: 0.05, gain: 0.07 * vol });
        break;
      case 'capture':
        this.tone({ type: 'square', freq: 520, dur: 0.12, gain: 0.18 * vol });
        setTimeout(function (self) {
          return function () { self.tone({ type: 'square', freq: 780, dur: 0.18, gain: 0.18 * vol }); };
        }(this), 110);
        break;
      case 'alarm':
        this.tone({ type: 'sawtooth', freq: 440, freqEnd: 880, dur: 0.4, gain: 0.14 * vol });
        break;
      // ------------------------------------------------ Last Light
      case 'groan':
        // a wet, falling moan: a low saw through a narrow filter, pitch varied
        var base = 95 + Math.random() * 60;
        this.tone({ type: 'sawtooth', freq: base * 1.3, freqEnd: base * 0.7,
                    dur: 0.7 + Math.random() * 0.5, gain: 0.07 * vol });
        this.noise({ filter: 'bandpass', freq: 500, freqEnd: 260, dur: 0.6, gain: 0.05 * vol });
        break;
      case 'growl':
        this.tone({ type: 'sawtooth', freq: 70, freqEnd: 42, dur: 1.1, gain: 0.16 * vol });
        this.noise({ freq: 300, freqEnd: 90, dur: 1.0, gain: 0.12 * vol });
        break;
      case 'scream':
        this.tone({ type: 'sawtooth', freq: 900, freqEnd: 1600, dur: 1.2, gain: 0.12 * vol });
        this.tone({ type: 'square', freq: 1210, freqEnd: 760, dur: 1.4, gain: 0.06 * vol });
        this.noise({ filter: 'highpass', freq: 2400, dur: 1.2, gain: 0.1 * vol });
        break;
      case 'roar':
        this.tone({ type: 'sawtooth', freq: 110, freqEnd: 48, dur: 1.6, gain: 0.26 * vol });
        this.tone({ type: 'square', freq: 82, freqEnd: 36, dur: 1.5, gain: 0.12 * vol });
        this.noise({ freq: 600, freqEnd: 80, dur: 1.6, gain: 0.28 * vol });
        break;
      case 'bell':
        // the church bell: a struck partial series, three rings
        for (var b = 0; b < 3; b++) {
          setTimeout(function (self) { return function () {
            [220, 440, 528, 660, 880].forEach(function (f, k) {
              self.tone({ type: 'sine', freq: f, dur: 2.2 - k * 0.3, gain: (0.16 - k * 0.025) * vol });
            });
          }; }(this), b * 900);
        }
        break;
      case 'dinner':
        // the triangle on the mess hall porch, rattled
        for (var d = 0; d < 8; d++) {
          setTimeout(function (self) { return function () {
            self.tone({ type: 'triangle', freq: 1760, dur: 0.5, gain: 0.08 * vol });
            self.tone({ type: 'sine', freq: 2640, dur: 0.35, gain: 0.04 * vol });
          }; }(this), d * 120);
        }
        break;
      case 'siren':
        for (var w = 0; w < 4; w++) {
          setTimeout(function (self) { return function () {
            self.tone({ type: 'sawtooth', freq: 620, freqEnd: 980, dur: 0.6, gain: 0.12 * vol });
            setTimeout(function () {
              self.tone({ type: 'sawtooth', freq: 980, freqEnd: 620, dur: 0.6, gain: 0.12 * vol });
            }, 600);
          }; }(this), w * 1200);
        }
        break;
      case 'horn':
        this.tone({ type: 'sawtooth', freq: 98, dur: 2.6, gain: 0.2 * vol });
        this.tone({ type: 'square', freq: 147, dur: 2.6, gain: 0.08 * vol });
        break;
      case 'pounce':
        this.noise({ filter: 'bandpass', freq: 1800, freqEnd: 700, dur: 0.3, gain: 0.18 * vol });
        this.tone({ type: 'sawtooth', freq: 600, freqEnd: 1100, dur: 0.3, gain: 0.08 * vol });
        break;
      case 'charge':
        this.tone({ type: 'sawtooth', freq: 140, freqEnd: 260, dur: 0.8, gain: 0.16 * vol });
        this.noise({ freq: 400, dur: 0.8, gain: 0.1 * vol });
        break;
      case 'spit':
        this.noise({ filter: 'bandpass', freq: 2600, freqEnd: 900, dur: 0.25, gain: 0.16 * vol });
        break;
      case 'splat':
        this.noise({ freq: 900, freqEnd: 120, dur: 0.35, gain: 0.2 * vol });
        break;
      case 'fuse':
        for (var f = 0; f < 6; f++) {
          setTimeout(function (self) { return function () {
            self.tone({ type: 'square', freq: 1600, dur: 0.06, gain: 0.1 * vol });
          }; }(this), f * 200);
        }
        this.noise({ filter: 'highpass', freq: 3000, dur: 1.2, gain: 0.08 * vol });
        break;
      case 'defuse':
        this.tone({ type: 'sine', freq: 1200, freqEnd: 300, dur: 0.4, gain: 0.12 * vol });
        break;
      case 'bile':
        this.noise({ freq: 700, freqEnd: 90, dur: 0.7, gain: 0.32 * vol });
        this.tone({ type: 'sine', freq: 140, freqEnd: 50, dur: 0.6, gain: 0.2 * vol });
        break;
      case 'bolt':
        this.tone({ type: 'sine', freq: 300, freqEnd: 900, dur: 0.35, gain: 0.1 * vol });
        this.noise({ filter: 'bandpass', freq: 1200, dur: 0.3, gain: 0.08 * vol });
        break;
      case 'raise':
        this.tone({ type: 'sine', freq: 180, freqEnd: 90, dur: 1.4, gain: 0.14 * vol });
        this.tone({ type: 'triangle', freq: 270, freqEnd: 135, dur: 1.4, gain: 0.08 * vol });
        break;
      case 'clang':
        this.tone({ type: 'triangle', freq: 1900, freqEnd: 1500, dur: 0.25, gain: 0.12 * vol });
        this.tone({ type: 'sine', freq: 2850, dur: 0.18, gain: 0.06 * vol });
        break;
      case 'burrow':
        this.noise({ freq: 260, freqEnd: 70, dur: 0.9, gain: 0.3 * vol });
        break;
      case 'wave':
        this.tone({ type: 'sawtooth', freq: 110, dur: 0.5, gain: 0.18 * vol });
        setTimeout(function (self) {
          return function () { self.tone({ type: 'sawtooth', freq: 104, dur: 0.9, gain: 0.2 * vol }); };
        }(this), 420);
        this.noise({ freq: 400, freqEnd: 60, dur: 1.2, gain: 0.18 * vol });
        break;
      case 'wavewin':
        [523, 659, 784, 1046].forEach(function (f, k) {
          setTimeout(function (self) { return function () {
            self.tone({ type: 'square', freq: f, dur: 0.18, gain: 0.12 * vol });
          }; }(this), k * 110);
        }, this);
        break;
      case 'down':
        this.tone({ type: 'sine', freq: 300, freqEnd: 90, dur: 0.9, gain: 0.22 * vol });
        this.noise({ freq: 300, freqEnd: 60, dur: 0.6, gain: 0.14 * vol });
        break;
      case 'revive':
        this.tone({ type: 'sine', freq: 400, freqEnd: 800, dur: 0.4, gain: 0.16 * vol });
        setTimeout(function (self) {
          return function () { self.tone({ type: 'sine', freq: 800, freqEnd: 1200, dur: 0.3, gain: 0.14 * vol }); };
        }(this), 200);
        break;
      case 'headshot':
        this.tone({ type: 'square', freq: 1800, freqEnd: 1300, dur: 0.07, gain: 0.14 * vol });
        this.noise({ filter: 'bandpass', freq: 1500, dur: 0.12, gain: 0.12 * vol });
        break;
      case 'zkill':
        this.noise({ freq: 700, freqEnd: 150, dur: 0.18, gain: 0.12 * vol });
        break;
      default:
        break;
    }
  };

  global.GameAudio = Audio;
})(window);
