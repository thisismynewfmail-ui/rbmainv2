/* BLOCKHAVEN -- Edit Pet (templates/pet_editor.html).

   Which pet follows you, and what she is like.  Everything saves as it is
   changed: a name after a pause in typing, a colour after the picker stops
   moving, a tag or a piece of her wardrobe at once.  The preview is a stage
   from pets_shop.js, and every change makes her react -- a new hat and she
   poses, a new persona tag and she shows it off -- so the editor answers
   "what will she be like?" as well as "what will she look like?". */
(function (global) {
  'use strict';

  var root = document.getElementById('pet-editor');
  if (!root) return;
  var boot;
  try { boot = JSON.parse(document.getElementById('pe-boot').textContent); } catch (e) { return; }

  var $ = function (sel) { return root.querySelector(sel); };
  var $$ = function (sel) { return Array.prototype.slice.call(root.querySelectorAll(sel)); };

  var pets = {};
  boot.pets.forEach(function (p) { pets[p.inv_id] = p; });
  var cosmetics = {};
  boot.cosmetics.forEach(function (c) { cosmetics[c.inv_id] = c; });
  var current = pets[boot.chosen] || boot.pets[0];
  var active = boot.active;
  var catalog = {};
  var stage = null;
  var status = $('#pe-status');

  // the actions a persona tag shows off (pet.js has the full repertoire)
  var TAG_ACT = {
    cheerful: 'cheer', shy: 'shy', curious: 'inspect', loyal: 'salute', sleepy: 'yawn',
    energetic: 'fistpump', feisty: 'shadowbox', dreamy: 'hum', playful: 'pounce', brave: 'flex',
    clingy: 'hug', showoff: 'pose', chatty: 'giggle', clumsy: 'trip'
  };
  var SLOT_ACT = { pet_hat: 'pose', pet_face: 'giggle', pet_neck: 'nod', pet_pin: 'heart',
                   pet_top: 'twirl', pet_back: 'twirl' };

  /* The pet as the renderer draws her, from what is being edited. */
  function describe(p) {
    var items = {};
    Object.keys(p.equipped || {}).forEach(function (slot) {
      var c = cosmetics[p.equipped[slot]];
      var item = c && catalog[c.item_id];
      if (item) items[slot] = { item_id: c.item_id, slot: slot, data: item.data, name: item.name };
    });
    return { inv_id: p.inv_id, species: p.species, name: p.name, colors: p.colors,
             tags: p.tags, items: items };
  }

  function say(text, bad) {
    if (!status) return;
    status.textContent = text;
    status.classList.toggle('bad', !!bad);
  }

  // ------------------------------------------------------------------ saving
  var pending = {}, timer = null, saving = false;
  function queue(fields, delay) {
    Object.keys(fields).forEach(function (k) { pending[k] = fields[k]; });
    pending.inv_id = current.inv_id;
    clearTimeout(timer);
    say('Saving…');
    timer = setTimeout(flush, delay === undefined ? 350 : delay);
  }
  function flush() {
    if (saving) { timer = setTimeout(flush, 200); return; }
    var body = pending;
    pending = {};
    saving = true;
    Site.post('/api/pets/save', body).then(function (res) {
      saving = false;
      if (!res.ok) { say(res.error || 'Could not save.', true); Site.toast(res.error, 'bad'); return; }
      say('Saved ✓');
    }).catch(function () { saving = false; say('Could not save -- check your connection.', true); });
  }

  function refresh(action) {
    if (stage) {
      stage.setPet(describe(current));
      if (action) stage.play(action);
      stage.idleSince = 0;
    }
    var box = root.querySelector('.pe-stage');
    if (box) {
      box.style.setProperty('--pc', current.colors.hair);
      box.style.setProperty('--po', current.colors.outfit);
      box.style.setProperty('--pa', current.colors.accent);
    }
    thumb(current);
  }

  // ------------------------------------------------------------- thumbnails
  /* My pets: a still of each, in her own colours and outfit. */
  function thumb(p) {
    var canvas = root.querySelector('[data-pet-thumb="' + p.inv_id + '"]');
    if (!canvas || !global.Thumbs || !global.Pet || !Thumbs.renderPartsTo) return;
    var pose = Pet.act('idle', 0.5);
    var sp = Pet.species(p);
    pose.eyes = sp.eyes || 'happy';
    pose.mouth = sp.mouth || 'smile';
    pose.blush = 0.3;
    Thumbs.renderPartsTo(canvas, Pet.build(describe(p), { position: [0, 0, 0], yaw: 0.3, pose: pose }),
                         { angle: -0.25, tilt: 0.1, padding: 1.08 },
                         'petthumb:' + p.inv_id + ':' + JSON.stringify(p.colors) + JSON.stringify(p.equipped));
  }

  // ------------------------------------------------------------ the panels
  function paintTags() {
    $$('.pe-tag').forEach(function (b) {
      var on = current.tags.indexOf(b.dataset.tag) >= 0;
      b.classList.toggle('on', on);
      b.setAttribute('aria-pressed', String(on));
      // full, not disabled: tapping one still says why it will not go on
      var full = !on && current.tags.length >= boot.maxTags;
      b.classList.toggle('full', full);
      b.setAttribute('aria-disabled', String(full));
    });
    var count = $('#pe-tag-count');
    if (count) count.textContent = current.tags.length + '/' + boot.maxTags;
  }

  function paintColours() {
    boot.colorKeys.forEach(function (key) {
      var value = current.colors[key];
      var pick = root.querySelector('[data-pick="' + key + '"]');
      if (pick) pick.value = value;
      var hex = root.querySelector('[data-hex="' + key + '"]');
      if (hex) hex.textContent = value;
      root.querySelectorAll('.swatches[data-part="' + key + '"] .swatch').forEach(function (sw) {
        sw.classList.toggle('on', sw.dataset.color.toLowerCase() === String(value).toLowerCase());
      });
    });
  }

  function paintWardrobe() {
    $$('.pick[data-wear]').forEach(function (pick) {
      var slot = pick.dataset.slot;
      var on = String(current.equipped[slot] || 0) === pick.dataset.wear;
      pick.classList.toggle('on', on);
    });
  }

  function paintMine() {
    $$('.pe-pet[data-pet-id]').forEach(function (b) {
      var on = String(current.inv_id) === b.dataset.petId;
      b.classList.toggle('on', on);
      b.setAttribute('aria-selected', String(on));
    });
    $$('[data-pet-active]').forEach(function (chip) {
      chip.classList.toggle('hidden', String(active) !== chip.dataset.petActive);
    });
    var none = $('#pe-unset');
    if (none) none.classList.toggle('on-none', !active);
    var badge = $('#pe-active-badge');
    if (badge) badge.classList.toggle('hidden', active !== current.inv_id);
    var btn = $('#pe-activate');
    if (btn) {
      btn.disabled = active === current.inv_id;
      btn.textContent = active === current.inv_id ? 'Following you' : 'Set as Active Pet';
    }
  }

  function paintAll() {
    var name = $('#pe-name');
    if (name) { name.value = current.name; name.placeholder = boot.species[current.species].name; }
    paintTags();
    paintColours();
    paintWardrobe();
    paintMine();
  }

  // ---------------------------------------------------------------- binding
  root.addEventListener('click', function (e) {
    var act = e.target.closest('[data-act]');
    if (act && stage) {
      var name = act.dataset.act;
      if (name === 'sit' || name === 'sleep') {
        stage.show.only = stage.show.only === name ? null : name;
        if (!stage.show.only) stage.show.play('stretch');
      } else {
        stage.show.only = null;
        stage.play(name);
      }
      return;
    }
    var tag = e.target.closest('.pe-tag');
    if (tag) {
      var id = tag.dataset.tag, at = current.tags.indexOf(id);
      if (at >= 0) current.tags.splice(at, 1);
      else if (current.tags.length < boot.maxTags) current.tags.push(id);
      else { Site.toast('She can have ' + boot.maxTags + ' persona tags -- take one off first.'); return; }
      paintTags();
      refresh(at >= 0 ? 'shake' : (TAG_ACT[id] || 'nod'));
      queue({ tags: current.tags.slice() }, 0);
      return;
    }
    var sw = e.target.closest('.swatch[data-color]');
    if (sw) {
      setColour(sw.closest('.swatches').dataset.part, sw.dataset.color, 'sparkle');
      return;
    }
    var pick = e.target.closest('.pick[data-wear]');
    if (pick) { wear(pick); return; }
    var petBtn = e.target.closest('.pe-pet[data-pet-id]');
    if (petBtn) { choose(parseInt(petBtn.dataset.petId, 10)); return; }
    if (e.target.closest('#pe-unset')) { setActive(0); return; }
    if (e.target.closest('#pe-activate')) { setActive(current.inv_id); return; }
    if (e.target.closest('#pe-reset')) {
      e.preventDefault();
      var own = boot.species[current.species].colors;
      boot.colorKeys.forEach(function (k) { current.colors[k] = own[k]; });
      paintColours();
      refresh('twirl');
      queue({ colors: current.colors }, 0);
      return;
    }
    var tab = e.target.closest('[data-slot-tab]');
    if (tab) {
      e.preventDefault();
      $$('[data-slot-tab]').forEach(function (t) { t.classList.toggle('on', t === tab); });
      $$('[data-slot-panel]').forEach(function (p) {
        p.classList.toggle('hidden', p.dataset.slotPanel !== tab.dataset.slotTab);
      });
      if (global.Thumbs) Thumbs.rescan();
    }
  });

  root.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    var target = e.target.closest('.swatch[data-color], .pick[data-wear]');
    if (target && target === e.target) { e.preventDefault(); target.click(); }
  });

  function setColour(key, value, action) {
    if (!/^#[0-9a-fA-F]{6}$/.test(value)) return;
    current.colors[key] = value.toLowerCase();
    paintColours();
    refresh(action);
    queue({ colors: current.colors });
  }

  $$('[data-pick]').forEach(function (input) {
    var key = input.dataset.pick;
    input.addEventListener('input', function () { setColour(key, input.value); });
    input.addEventListener('change', function () { setColour(key, input.value, 'sparkle'); });
  });

  var nameBox = $('#pe-name');
  if (nameBox) {
    nameBox.addEventListener('input', function () {
      var clean = nameBox.value.replace(/[^A-Za-z0-9 _.'\-]/g, '').slice(0, boot.nameMax);
      if (clean !== nameBox.value) nameBox.value = clean;
      current.name = clean.trim() || boot.species[current.species].name;
      var label = root.querySelector('[data-pet-name="' + current.inv_id + '"]');
      if (label) label.textContent = current.name;
      queue({ name: current.name }, 700);
    });
    nameBox.addEventListener('change', function () { if (stage) stage.play('curtsy'); });
  }

  function wear(pick) {
    var slot = pick.dataset.slot;
    var inv = parseInt(pick.dataset.wear, 10) || 0;
    if (inv) current.equipped[slot] = inv; else delete current.equipped[slot];
    paintWardrobe();
    refresh(inv ? (SLOT_ACT[slot] || 'wave') : 'shake');
    if (stage && slot === 'pet_back' && inv) stage.yaw = Math.PI * 0.85;
    var change = {};
    change[slot] = inv;
    queue({ equipped: change }, 0);
  }

  function choose(invId) {
    if (!pets[invId] || invId === current.inv_id) return;
    if (Object.keys(pending).length) flush();
    current = pets[invId];
    paintAll();
    refresh('wave');
    try { history.replaceState(null, '', '/pet?pet=' + invId); } catch (e) {}
  }

  function setActive(invId) {
    Site.post('/api/pets/active', { inv_id: invId }).then(function (res) {
      if (!res.ok) { Site.toast(res.error, 'bad'); return; }
      active = res.active;
      paintMine();
      if (invId) {
        Site.toast(current.name + ' is following you now!');
        if (stage) stage.play('cheer');
      } else {
        Site.toast('Nobody follows you around now.');
        if (stage) stage.play('pout');
      }
    });
  }

  // ------------------------------------------------------------------- boot
  function start() {
    var canvas = document.getElementById('pe-stage');
    stage = canvas && canvas.__petStage;
    if (!stage && global.PetStages) {
      PetStages.scan(root);
      stage = canvas && canvas.__petStage;
    }
    if (stage) {
      stage.restYaw = -0.25;
      stage.play('wave');
    }
    paintAll();
    boot.pets.forEach(thumb);
  }

  if (global.Thumbs && Thumbs.loadCatalog) {
    Thumbs.loadCatalog().then(function (c) { catalog = c || {}; start(); });
  } else {
    start();
  }
})(window);
