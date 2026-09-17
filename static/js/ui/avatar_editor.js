/* Avatar editor page.

   The cosmetic slots are a click: a hat either is or is not on your head, and
   there is one place it can go.  The hotbar is not -- it is five numbered
   seats and the order matters -- so it is a drag, the same gesture and the
   same ghost as the pinned items on the profile editor: pull an item out of
   the pool into a slot, pull one slot onto another to swap the two, and drag
   a slot back down into the pool to empty it.  It is driven by pointer
   events, so the identical gesture works with a mouse, a trackpad and a
   finger, and every click that worked before still works. */
(function () {
  'use strict';

  var DRAG_SLOP = 6;          // pixels before a press becomes a drag

  var preview = null;
  var selectedHotslot = 0;
  var hotbar = [];            // inventory ids, by slot, as the server has them

  function livePreview() {
    if (preview) return preview;
    var el = document.getElementById('avatar-preview');
    preview = el && el.__preview;
    return preview;
  }

  function applyDescriptor(descriptor) {
    var p = livePreview();
    if (p && p.setDescriptor) p.setDescriptor(descriptor);
    if (window.Thumbs) Thumbs.avatarCache[BH.user.name] = descriptor;
    refreshHotbar(descriptor);
  }

  function esc(text) {
    var div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
  }

  function slotNode(index) {
    return document.querySelector('[data-hotslot="' + index + '"]');
  }

  function refreshHotbar(descriptor) {
    hotbar = [];
    (descriptor.hotbar || []).forEach(function (entry, index) {
      hotbar[index] = entry ? (entry.inv_id || 0) : 0;
      var name = document.querySelector('[data-hot-name="' + index + '"]');
      var canvas = document.querySelector('[data-hot-canvas="' + index + '"]');
      var slot = slotNode(index);
      if (name) name.textContent = entry ? entry.name : 'empty';
      if (slot) {
        slot.classList.toggle('on', !!entry);
        slot.classList.toggle('filled', !!entry);
        if (entry) {
          slot.dataset.inv = entry.inv_id;
          slot.dataset.name = entry.name;
          slot.dataset.effect = entry.effect || '';
        } else {
          delete slot.dataset.inv;
          delete slot.dataset.name;
          delete slot.dataset.effect;
        }
      }
      if (canvas) {
        var ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        if (entry) { canvas.dataset.item = entry.item_id; Thumbs.renderItem(canvas, entry.item_id, ''); }
        else canvas.dataset.item = '';
      }
    });
    // an item already on the bar is marked in the pool, so the two halves of
    // the panel always agree about what is where
    document.querySelectorAll('[data-usable]').forEach(function (pick) {
      pick.classList.toggle('on',
        hotbar.indexOf(parseInt(pick.dataset.usable, 10)) >= 0);
    });
    paintSelection();
  }

  function paintSelection() {
    document.querySelectorAll('[data-hotslot]').forEach(function (el) {
      el.classList.toggle('picked',
        parseInt(el.dataset.hotslot, 10) === selectedHotslot);
    });
  }

  // ------------------------------------------------------------- the server
  function setSlot(index, invId) {
    return Site.post('/api/avatar/hotbar', { index: index, inv_id: invId });
  }

  /* Put ``invId`` in ``index``.  The server clears the item out of whatever
     slot it was in already, so a plain move needs one request; a drop onto an
     occupied slot needs a second one to seat whatever was displaced in the
     seat the dragged item has just left, which is what makes it read as a
     swap rather than as an overwrite. */
  function moveTo(invId, index) {
    var from = hotbar.indexOf(invId);
    if (from === index) return;
    var displaced = hotbar[index] || 0;
    setSlot(index, invId).then(function (res) {
      if (!res.ok) { Site.toast(res.error, 'bad'); return; }
      applyDescriptor(res.avatar);
      if (from >= 0 && displaced && displaced !== invId) {
        setSlot(from, displaced).then(function (second) {
          if (!second.ok) { Site.toast(second.error, 'bad'); return; }
          applyDescriptor(second.avatar);
          Site.toast('Swapped slots ' + (from + 1) + ' and ' + (index + 1) + '.');
        });
      } else {
        Site.toast('Placed in slot ' + (index + 1) + '.');
      }
    });
  }

  function clearSlot(index, quiet) {
    setSlot(index, 0).then(function (res) {
      if (!res.ok) { Site.toast(res.error, 'bad'); return; }
      applyDescriptor(res.avatar);
      if (!quiet) Site.toast('Slot ' + (index + 1) + ' cleared.');
    });
  }

  // ---------------------------------------------------------------- dragging
  var drag = null;
  var draggedAt = 0;          // a real drag swallows the click that follows it

  function tileFrom(node) {
    var pick = node.closest('#usable-pool [data-usable]');
    if (pick) {
      var canvas = pick.querySelector('canvas');
      return {
        invId: parseInt(pick.dataset.usable, 10),
        item: canvas ? canvas.dataset.item : '',
        effect: canvas ? (canvas.dataset.effect || '') : '',
        name: pick.getAttribute('title') || '',
        source: pick, from: -1
      };
    }
    var slot = node.closest('.hotslot.filled[data-inv]');
    if (slot) {
      var slotCanvas = slot.querySelector('canvas');
      return {
        invId: parseInt(slot.dataset.inv, 10),
        item: slotCanvas ? slotCanvas.dataset.item : '',
        effect: slot.dataset.effect || '',
        name: slot.dataset.name || '',
        source: slot, from: parseInt(slot.dataset.hotslot, 10)
      };
    }
    return null;
  }

  function makeGhost() {
    var ghost = document.createElement('div');
    ghost.className = 'drag-ghost';
    ghost.innerHTML = '<canvas class="item-thumb" width="120" height="120" ' +
      'data-item="' + esc(drag.item) + '" data-effect="' + esc(drag.effect) +
      '"></canvas><span>' + esc(drag.name) + '</span>';
    document.body.appendChild(ghost);
    drag.ghost = ghost;
    if (window.Thumbs) Thumbs.rescan();
    document.body.classList.add('item-dragging');
    if (drag.source) drag.source.classList.add('dragging');
  }

  function moveGhost(event) {
    if (!drag.ghost) return;
    drag.ghost.style.transform =
      'translate(' + (event.clientX - 34) + 'px,' + (event.clientY - 40) + 'px)';
  }

  function hover(event) {
    var under = document.elementFromPoint(event.clientX, event.clientY);
    var pool = document.getElementById('usable-pool');
    document.querySelectorAll('.hotslot').forEach(function (node) {
      node.classList.remove('over');
    });
    if (pool) pool.classList.remove('over');
    if (!under) return null;
    var slot = under.closest('[data-hotslot]');
    if (slot) { slot.classList.add('over'); return { kind: 'slot', node: slot }; }
    if (pool && under.closest('#usable-pool')) {
      pool.classList.add('over');
      return { kind: 'pool' };
    }
    return null;
  }

  function endDrag(event, cancelled) {
    if (!drag) return;
    var moved = drag.moved;
    var target = moved && !cancelled ? hover(event) : null;
    if (drag.ghost) drag.ghost.remove();
    if (drag.source) drag.source.classList.remove('dragging');
    document.body.classList.remove('item-dragging');
    document.querySelectorAll('.hotslot').forEach(function (node) {
      node.classList.remove('over');
    });
    var pool = document.getElementById('usable-pool');
    if (pool) pool.classList.remove('over');
    var invId = drag.invId;
    var from = drag.from;
    drag = null;
    // A press that never moved is a click, and the click handlers below
    // already know what to do with it.
    if (!moved) return;
    draggedAt = Date.now();
    if (target && target.kind === 'slot') {
      moveTo(invId, parseInt(target.node.dataset.hotslot, 10));
    } else if (target && target.kind === 'pool' && from >= 0) {
      clearSlot(from);
    }
  }

  function onPointerDown(event) {
    if (event.button !== undefined && event.button !== 0) return;
    var tile = tileFrom(event.target);
    if (!tile || !tile.invId) return;
    drag = {
      invId: tile.invId, from: tile.from, item: tile.item, effect: tile.effect,
      name: tile.name, source: tile.source, pointerId: event.pointerId,
      startX: event.clientX, startY: event.clientY, moved: false, ghost: null
    };
  }

  function onPointerMove(event) {
    if (!drag || event.pointerId !== drag.pointerId) return;
    if (!drag.moved) {
      if (Math.abs(event.clientX - drag.startX) < DRAG_SLOP &&
          Math.abs(event.clientY - drag.startY) < DRAG_SLOP) return;
      drag.moved = true;
      // claim the gesture only once it is clearly a drag, so a plain tap is
      // still delivered as a click
      try { drag.source.setPointerCapture(event.pointerId); } catch (e) {}
      makeGhost();
    }
    event.preventDefault();
    moveGhost(event);
    hover(event);
  }

  function clickSwallowed() {
    return Date.now() - draggedAt < 350;
  }

  document.addEventListener('DOMContentLoaded', function () {
    // -------------------------------------------------------------- tabs
    document.querySelectorAll('[data-slot-tab]').forEach(function (tab) {
      tab.addEventListener('click', function () {
        var slot = tab.dataset.slotTab;
        document.querySelectorAll('[data-slot-tab]').forEach(function (t) {
          t.classList.toggle('on', t === tab);
        });
        document.querySelectorAll('[data-slot-panel]').forEach(function (panel) {
          panel.classList.toggle('hidden', panel.dataset.slotPanel !== slot);
        });
        if (window.Thumbs) Thumbs.rescan();
      });
    });

    // ------------------------------------------------------------ colours
    document.querySelectorAll('.swatches').forEach(function (group) {
      group.addEventListener('click', function (event) {
        var swatch = event.target.closest('.swatch');
        if (!swatch) return;
        var part = group.dataset.part;
        var colour = swatch.dataset.color;
        setColour(part, colour, group);
      });
    });
    document.querySelectorAll('[data-custom]').forEach(function (input) {
      input.addEventListener('change', function () {
        setColour(input.dataset.custom, input.value, null);
      });
    });

    function setColour(part, colour, group) {
      var payload = { colors: {} };
      payload.colors[part] = colour;
      var status = document.getElementById('color-status');
      if (status) status.textContent = 'Saving...';
      Site.post('/api/avatar/colors', payload).then(function (res) {
        if (!res.ok) { Site.toast(res.error, 'bad'); return; }
        if (status) status.textContent = 'Saved.';
        var hex = document.getElementById('hex-' + part);
        if (hex) hex.textContent = colour;
        var picker = document.querySelector('[data-custom="' + part + '"]');
        if (picker) picker.value = colour;
        if (group) {
          group.querySelectorAll('.swatch').forEach(function (s) {
            s.classList.toggle('on', s.dataset.color === colour);
          });
        }
        applyDescriptor(res.avatar);
      });
    }

    // ------------------------------------------------------------ equipping
    document.querySelectorAll('[data-equip]').forEach(function (pick) {
      pick.addEventListener('click', function () {
        var invId = parseInt(pick.dataset.equip, 10) || 0;
        var slot = pick.dataset.slot;
        Site.post('/api/avatar/equip', { slot: slot, inv_id: invId })
          .then(function (res) {
            if (!res.ok) { Site.toast(res.error, 'bad'); return; }
            document.querySelectorAll('[data-slot="' + slot + '"][data-equip]')
              .forEach(function (other) { other.classList.toggle('on', other === pick); });
            applyDescriptor(res.avatar);
            Site.toast(invId ? 'Equipped.' : 'Removed.');
          });
      });
    });

    // -------------------------------------------------------------- hotbar
    document.querySelectorAll('[data-hotslot]').forEach(function (slot) {
      slot.addEventListener('click', function () {
        if (clickSwallowed()) return;
        selectedHotslot = parseInt(slot.dataset.hotslot, 10);
        paintSelection();
        var status = document.getElementById('hotbar-status');
        if (status) status.textContent = 'Slot ' + (selectedHotslot + 1) + ' selected.';
      });
    });
    document.querySelectorAll('[data-usable]').forEach(function (pick) {
      pick.addEventListener('click', function () {
        if (clickSwallowed()) return;
        moveTo(parseInt(pick.dataset.usable, 10), selectedHotslot);
      });
    });
    var clear = document.getElementById('clear-slot');
    if (clear) {
      clear.addEventListener('click', function () { clearSlot(selectedHotslot); });
    }

    document.addEventListener('pointerdown', onPointerDown);
    document.addEventListener('pointermove', onPointerMove, { passive: false });
    document.addEventListener('pointerup', function (event) {
      if (drag && event.pointerId === drag.pointerId) endDrag(event, false);
    });
    document.addEventListener('pointercancel', function (event) {
      if (drag && event.pointerId === drag.pointerId) endDrag(event, true);
    });

    // ----------------------------------------------------------- body type
    function markBody(chosen) {
      document.querySelectorAll('[data-body]').forEach(function (other) {
        var on = other === chosen;
        other.classList.toggle('on', on);
        other.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
    }

    document.querySelectorAll('[data-body]').forEach(function (button) {
      button.addEventListener('click', function () {
        if (button.classList.contains('on')) return;
        Site.post('/api/avatar/body', { body_type: button.dataset.body })
          .then(function (res) {
            if (!res.ok) { Site.toast(res.error, 'bad'); return; }
            // the server has the last word on which build was applied, so a
            // retired one posted by a stale page still lights the right button
            markBody(document.querySelector('[data-body="' + res.body_type + '"]')
                     || button);
            // mannequin previews in the slot pickers follow the chosen build
            if (window.Thumbs) {
              Thumbs.mannequinBody = res.body_type;
              Thumbs.rescan();
            }
            applyDescriptor(res.avatar);
            Site.toast('Body type updated.');
          });
      });
    });
    var currentBody = document.querySelector('[data-body].on');
    if (currentBody && window.Thumbs) Thumbs.mannequinBody = currentBody.dataset.body;

    var spin = document.getElementById('spin-toggle');
    if (spin) {
      spin.addEventListener('click', function () {
        var p = livePreview();
        if (!p) return;
        p.spin = !p.spin;
        spin.textContent = p.spin ? 'Pause spin' : 'Resume spin';
      });
    }

    /* Apply.  Every control on this page already saves the moment it is
       clicked, so this is the full stop rather than the save: it re-reads the
       avatar the server actually holds, then hands the player their profile,
       which is where the finished character is meant to be looked at.  On a
       first session the template swaps it for "Finish & view profile", which
       is the same full stop going to the same place. */
    var apply = document.getElementById('apply-avatar');
    if (apply) {
      apply.addEventListener('click', function () {
        apply.disabled = true;
        var home = '/profile/' + encodeURIComponent(BH.user.name);
        Site.get('/api/avatar').then(function (res) {
          if (!res.ok) {
            apply.disabled = false;
            Site.toast(res.error || 'Could not reach the server.', 'bad');
            return;
          }
          applyDescriptor(res.avatar);
          Site.toast('Avatar Updated');
          // let the toast land before the page goes
          setTimeout(function () { window.location.href = home; }, 450);
        }).catch(function () {
          apply.disabled = false;
          Site.toast('Could not reach the server.', 'bad');
        });
      });
    }

    Site.get('/api/avatar').then(function (res) {
      if (res.ok) refreshHotbar(res.avatar);
    });
  });
})();
