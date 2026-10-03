/* Profile editor: the pinned item slots.

   The arrangement is spatial -- three tiles across the top of your profile --
   so setting it up is a drag rather than a list of checkboxes: pull an item
   out of the inventory into a slot, pull it back out to unpin it, and drop
   one on top of another to swap the two.  It is driven by pointer events, so
   the identical gesture works with a mouse, a trackpad and a finger; a plain
   click still pins and unpins for anyone who would rather not drag. */
(function () {
  'use strict';

  var DRAG_SLOP = 6;          // pixels before a press becomes a drag

  document.addEventListener('DOMContentLoaded', function () {
    var pool = document.getElementById('pin-pool');
    var row = document.getElementById('pin-preview');
    if (!pool || !row) return;
    var slots = document.querySelectorAll('[id^="pin-field-"]').length;
    var status = document.getElementById('pin-status');

    // ------------------------------------------------------------- state
    function current() {
      var out = [];
      for (var i = 0; i < slots; i++) {
        var field = document.getElementById('pin-field-' + i);
        out.push(parseInt(field && field.value, 10) || 0);
      }
      return out;
    }

    function write(list) {
      for (var i = 0; i < slots; i++) {
        var field = document.getElementById('pin-field-' + i);
        if (field) field.value = list[i] || 0;
      }
      paint(list);
    }

    function pickFor(invId) {
      return pool.querySelector('[data-pin="' + invId + '"]');
    }

    function slotNode(index) {
      return row.querySelector('[data-pin-slot="' + index + '"]');
    }

    // ----------------------------------------------------------- drawing
    function paint(list) {
      pool.querySelectorAll('[data-pin]').forEach(function (pick) {
        pick.classList.toggle('on',
          list.indexOf(parseInt(pick.dataset.pin, 10)) >= 0);
      });
      for (var i = 0; i < slots; i++) {
        var box = slotNode(i);
        if (!box) continue;
        var invId = list[i];
        var pick = invId ? pickFor(invId) : null;
        if (!pick) {
          box.className = 'pinslot';
          box.innerHTML = '<span class="slot-n">' + (i + 1) + '</span>' +
            '<span class="slot-hint">drag an item here</span>';
          delete box.dataset.inv;
          continue;
        }
        box.className = 'pinslot filled item tier-' +
          (pick.dataset.tier || 'normal');
        box.dataset.inv = invId;
        box.innerHTML =
          '<span class="slot-n">' + (i + 1) + '</span>' +
          '<button type="button" class="slot-clear" data-pin-clear="' + i +
          '" title="Unpin this" aria-label="Unpin this">&times;</button>' +
          '<div class="thumb-wrap"><canvas class="thumb item-thumb" width="180" ' +
          'height="180" data-item="' + esc(pick.dataset.item) + '" data-effect="' +
          esc(pick.dataset.effect || '') + '"' +
          (pick.dataset.effect ? ' data-live-effect="1"' : '') + '></canvas></div>' +
          '<div class="meta"><span class="iname">' + esc(pick.dataset.name || '') +
          '</span></div>';
      }
      if (window.Thumbs) Thumbs.rescan();
      var used = list.filter(function (value) { return !!value; }).length;
      if (status) {
        status.textContent = used
          ? used + ' of ' + slots + ' slots used. Drag to rearrange, or drop one ' +
            'on another to swap.'
          : 'Drag an item into a slot to pin it.';
      }
    }

    function esc(text) {
      var div = document.createElement('div');
      div.textContent = text == null ? '' : String(text);
      return div.innerHTML;
    }

    // -------------------------------------------------------- placements
    function place(invId, index) {
      var list = current();
      var from = list.indexOf(invId);
      if (from === index) return;
      var displaced = list[index];
      list[index] = invId;
      // dragged between two slots: the one that was there takes the old seat,
      // which is what makes a drop onto an occupied slot read as a swap
      if (from >= 0) list[from] = displaced;
      write(list);
    }

    function unpin(invId) {
      var list = current();
      var at = list.indexOf(invId);
      if (at < 0) return;
      list[at] = 0;
      write(list);
    }

    function firstEmpty(list) {
      for (var i = 0; i < slots; i++) { if (!list[i]) return i; }
      return -1;
    }

    // -------------------------------------------------------------- drag
    var drag = null;

    function tileFrom(node) {
      var pick = node.closest('#pin-pool [data-pin]');
      if (pick) return { invId: parseInt(pick.dataset.pin, 10), source: pick };
      var slot = node.closest('.pinslot.filled[data-inv]');
      if (slot) return { invId: parseInt(slot.dataset.inv, 10), source: slot };
      return null;
    }

    function startDrag(event, tile) {
      var pick = pickFor(tile.invId);
      drag = {
        invId: tile.invId,
        pointerId: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
        moved: false,
        ghost: null,
        source: tile.source,
        label: (pick && pick.dataset.name) || ''
      };
    }

    function makeGhost() {
      var pick = pickFor(drag.invId);
      var ghost = document.createElement('div');
      ghost.className = 'pin-ghost';
      ghost.innerHTML = '<canvas class="item-thumb" width="120" height="120" ' +
        'data-item="' + esc(pick ? pick.dataset.item : '') + '" data-effect="' +
        esc(pick ? (pick.dataset.effect || '') : '') + '"></canvas>' +
        '<span>' + esc(drag.label) + '</span>';
      document.body.appendChild(ghost);
      drag.ghost = ghost;
      if (window.Thumbs) Thumbs.rescan();
      document.body.classList.add('pin-dragging');
      if (drag.source) drag.source.classList.add('dragging');
    }

    function moveGhost(event) {
      if (!drag.ghost) return;
      drag.ghost.style.transform =
        'translate(' + (event.clientX - 34) + 'px,' + (event.clientY - 40) + 'px)';
    }

    function hover(event) {
      var under = document.elementFromPoint(event.clientX, event.clientY);
      row.querySelectorAll('.pinslot').forEach(function (node) {
        node.classList.remove('over');
      });
      pool.classList.remove('over');
      if (!under) return null;
      var slot = under.closest('[data-pin-slot]');
      if (slot) { slot.classList.add('over'); return { kind: 'slot', node: slot }; }
      if (under.closest('#pin-pool')) {
        pool.classList.add('over');
        return { kind: 'pool' };
      }
      return null;
    }

    function endDrag(event, cancelled) {
      if (!drag) return;
      var target = drag.moved && !cancelled ? hover(event) : null;
      if (drag.ghost) drag.ghost.remove();
      if (drag.source) drag.source.classList.remove('dragging');
      document.body.classList.remove('pin-dragging');
      row.querySelectorAll('.pinslot').forEach(function (node) {
        node.classList.remove('over');
      });
      pool.classList.remove('over');

      if (!drag.moved && !cancelled) {
        // a plain click: pin into the first free slot, or unpin
        var list = current();
        if (list.indexOf(drag.invId) >= 0) {
          unpin(drag.invId);
        } else {
          var free = firstEmpty(list);
          if (free < 0) {
            if (window.Site) {
              Site.toast('All ' + slots + ' slots are full — drag one out first, ' +
                         'or drop this on top of one to swap.', 'bad');
            }
          } else {
            place(drag.invId, free);
          }
        }
      } else if (target && target.kind === 'slot') {
        place(drag.invId, parseInt(target.node.dataset.pinSlot, 10));
      } else if (target && target.kind === 'pool') {
        unpin(drag.invId);
      }
      drag = null;
    }

    function onPointerDown(event) {
      if (event.button !== undefined && event.button !== 0) return;
      if (event.target.closest('[data-pin-clear]')) return;   // the X handles it
      var tile = tileFrom(event.target);
      if (!tile || !tile.invId) return;
      startDrag(event, tile);
      // claim the gesture so a drag inside the scrolling pool does not turn
      // into a page scroll halfway through
      try { event.target.setPointerCapture(event.pointerId); } catch (e) {}
    }

    function onPointerMove(event) {
      if (!drag || event.pointerId !== drag.pointerId) return;
      if (!drag.moved) {
        if (Math.abs(event.clientX - drag.startX) < DRAG_SLOP &&
            Math.abs(event.clientY - drag.startY) < DRAG_SLOP) return;
        drag.moved = true;
        makeGhost();
      }
      event.preventDefault();
      moveGhost(event);
      hover(event);
    }

    function onPointerUp(event) {
      if (!drag || event.pointerId !== drag.pointerId) return;
      endDrag(event, false);
    }

    document.addEventListener('pointerdown', onPointerDown);
    document.addEventListener('pointermove', onPointerMove, { passive: false });
    document.addEventListener('pointerup', onPointerUp);
    document.addEventListener('pointercancel', function (event) {
      if (drag && event.pointerId === drag.pointerId) endDrag(event, true);
    });

    row.addEventListener('click', function (event) {
      var clear = event.target.closest('[data-pin-clear]');
      if (!clear) return;
      event.preventDefault();
      var list = current();
      list[parseInt(clear.dataset.pinClear, 10)] = 0;
      write(list);
    });

    paint(current());
  });
})();

/* Profile editor: the Badge Inventory.

   The same gesture as the pinned items above -- drag a badge into one of the
   four slots, drag it back out (or hit its x) to take it down, drop one on
   another to swap, or just click it -- over badges rather than items. Locked
   badges can be hovered (to see what they are for) but not picked up. */
(function () {
  'use strict';

  var DRAG_SLOP = 6;

  document.addEventListener('DOMContentLoaded', function () {
    var pool = document.getElementById('badge-pool');
    var row = document.getElementById('badge-slots');
    if (!pool || !row) return;
    var slots = row.querySelectorAll('[data-badge-slot]').length;
    var status = document.getElementById('badge-status');

    function esc(text) { return window.Site ? Site.escape(text) : String(text || ''); }
    function field(i) { return document.getElementById('badge-field-' + i); }
    function current() {
      var out = [];
      for (var i = 0; i < slots; i++) out.push((field(i) && field(i).value) || '');
      return out;
    }
    function cardOf(id) { return pool.querySelector('[data-badge-pick="' + id + '"]'); }

    function paint(list) {
      pool.querySelectorAll('[data-badge-pick]').forEach(function (card) {
        card.classList.toggle('on', !!card.dataset.badgePick && list.indexOf(card.dataset.badgePick) >= 0);
      });
      for (var i = 0; i < slots; i++) {
        var box = row.querySelector('[data-badge-slot="' + i + '"]');
        var id = list[i];
        var info = id && window.Badges ? Badges.cards[id] : null;
        if (!info) {
          box.className = 'bi-slot';
          box.removeAttribute('data-badge-pop');
          box.removeAttribute('data-badge');
          box.innerHTML = '<span class="slot-n">' + (i + 1) + '</span><span class="slot-hint">drag a badge here</span>';
          continue;
        }
        box.className = 'bi-slot filled tier-' + info.tier;
        box.dataset.badge = id;
        box.dataset.badgePop = id;
        box.style.setProperty('--tier', info.color);
        box.style.setProperty('--glow', info.glow);
        box.innerHTML = '<span class="slot-n">' + (i + 1) + '</span>' +
          '<button type="button" class="slot-clear" data-badge-clear="' + i + '" title="Take it down">&times;</button>' +
          '<div class="bt-stage"><canvas class="badge-3d" width="160" height="160" data-badge="' + esc(id) + '"></canvas></div>' +
          '<b>' + esc(info.name) + '</b>';
        if (window.Badges) Badges.render(box.querySelector('canvas'), info);
      }
      var used = list.filter(Boolean).length;
      if (status) {
        status.textContent = used
          ? used + ' of ' + slots + ' shown on your profile. Save to keep it.'
          : 'None picked: your profile shows your best four. Drag badges into the slots to choose.';
      }
    }

    function write(list) {
      for (var i = 0; i < slots; i++) if (field(i)) field(i).value = list[i] || '';
      paint(list);
    }

    function place(id, index) {
      var list = current();
      var from = list.indexOf(id);
      if (from === index) return;
      var displaced = list[index];
      list[index] = id;
      if (from >= 0) list[from] = displaced;
      write(list);
    }

    function takeDown(id) {
      var list = current();
      var at = list.indexOf(id);
      if (at >= 0) { list[at] = ''; write(list); }
    }

    // ---------------------------------------------------------- dragging
    var drag = null;
    function tileFrom(node) {
      var card = node.closest('#badge-pool [data-badge-pick]');
      if (card && card.dataset.badgePick) return { id: card.dataset.badgePick, source: card };
      var slot = node.closest('.bi-slot.filled[data-badge]');
      if (slot) return { id: slot.dataset.badge, source: slot };
      return null;
    }
    function hover(e) {
      var under = document.elementFromPoint(e.clientX, e.clientY);
      row.querySelectorAll('.bi-slot').forEach(function (n) { n.classList.remove('over'); });
      if (!under) return null;
      var slot = under.closest('[data-badge-slot]');
      if (slot) { slot.classList.add('over'); return { kind: 'slot', node: slot }; }
      if (under.closest('#badge-pool')) return { kind: 'pool' };
      return null;
    }
    function startGhost() {
      var info = window.Badges ? Badges.cards[drag.id] : null;
      var ghost = document.createElement('div');
      ghost.className = 'bi-ghost';
      ghost.innerHTML = '<canvas width="120" height="120"></canvas>';
      document.body.appendChild(ghost);
      if (info && window.Badges) Badges.render(ghost.querySelector('canvas'), info);
      drag.ghost = ghost;
      document.body.classList.add('bi-dragging');
      drag.source.classList.add('dragging');
      if (window.Badges) Badges.hide(true);
    }
    document.addEventListener('pointerdown', function (e) {
      if (e.button !== undefined && e.button !== 0) return;
      if (e.target.closest('[data-badge-clear]')) return;
      var tile = tileFrom(e.target);
      if (!tile) return;
      drag = { id: tile.id, source: tile.source, x: e.clientX, y: e.clientY,
               pointerId: e.pointerId, moved: false, ghost: null };
    });
    document.addEventListener('pointermove', function (e) {
      if (!drag || e.pointerId !== drag.pointerId) return;
      if (!drag.moved) {
        if (Math.abs(e.clientX - drag.x) < DRAG_SLOP && Math.abs(e.clientY - drag.y) < DRAG_SLOP) return;
        drag.moved = true;
        startGhost();
      }
      e.preventDefault();
      drag.ghost.style.transform = 'translate(' + (e.clientX - 42) + 'px,' + (e.clientY - 48) + 'px)';
      hover(e);
    }, { passive: false });
    function end(e, cancelled) {
      if (!drag || e.pointerId !== drag.pointerId) return;
      var target = drag.moved && !cancelled ? hover(e) : null;
      if (drag.ghost) drag.ghost.remove();
      drag.source.classList.remove('dragging');
      document.body.classList.remove('bi-dragging');
      row.querySelectorAll('.bi-slot').forEach(function (n) { n.classList.remove('over'); });
      if (!drag.moved && !cancelled) {
        var list = current();
        if (list.indexOf(drag.id) >= 0) takeDown(drag.id);
        else {
          var free = list.indexOf('');
          if (free < 0 && window.Site) Site.toast('All ' + slots + ' slots are full -- drag one out first, or drop this on one to swap.', 'bad');
          else if (free >= 0) place(drag.id, free);
        }
      } else if (target && target.kind === 'slot') {
        place(drag.id, parseInt(target.node.dataset.badgeSlot, 10));
      } else if (target && target.kind === 'pool') {
        takeDown(drag.id);
      }
      drag = null;
    }
    document.addEventListener('pointerup', function (e) { end(e, false); });
    document.addEventListener('pointercancel', function (e) { end(e, true); });
    row.addEventListener('click', function (e) {
      var clear = e.target.closest('[data-badge-clear]');
      if (!clear) return;
      e.preventDefault();
      var list = current();
      list[parseInt(clear.dataset.badgeClear, 10)] = '';
      write(list);
    });

    // ------------------------------------------------------------ filter
    var filter = document.getElementById('badge-filter');
    if (filter) {
      filter.addEventListener('click', function (e) {
        var b = e.target.closest('[data-game]');
        if (!b) return;
        filter.querySelectorAll('button').forEach(function (x) { x.classList.toggle('on', x === b); });
        pool.querySelectorAll('.bi-card').forEach(function (card) {
          card.style.display = !b.dataset.game || card.dataset.game === b.dataset.game ? '' : 'none';
        });
      });
    }

    // the badge cards arrive with the page; draw the slots once they are read
    setTimeout(function () { paint(current()); }, 0);
  });
})();
