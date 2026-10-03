/* Inventory page: wear and sell, both through the site's own dialogs, and the
   crate shelf -- pick up a key, carry it to a crate it opens, and the crate
   stage (crates.js) takes over from there. */
(function () {
  'use strict';

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function esc(t) { return Site.escape(t); }
  function reduced() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  // ------------------------------------------------------------- stacks
  /* A crate or key card stands for every copy of that item; data-ids holds
     their inventory rows, oldest first. */
  function idsOf(card) {
    return (card.dataset.ids || '').split(' ').filter(Boolean).map(Number);
  }
  function setIds(card, ids) {
    card.dataset.ids = ids.join(' ');
    var n = card.querySelector('.stack-count b');
    if (n) {
      n.textContent = ids.length;
      n.parentNode.classList.remove('pop'); void n.parentNode.offsetWidth; n.parentNode.classList.add('pop');
    }
    var sell = card.querySelector('[data-sell]');
    if (sell && ids.length) sell.dataset.sell = ids[0];
    if (!ids.length) {
      card.classList.add('leaving');
      setTimeout(function () { card.remove(); }, 450);
    }
  }
  function takeId(id) {
    $$('.stash-card').forEach(function (card) {
      var ids = idsOf(card);
      var at = ids.indexOf(id);
      if (at >= 0) { ids.splice(at, 1); setIds(card, ids); }
    });
  }
  function crateName(id) {
    var s = (window.CRATE_SERIES || {})[id];
    return s ? s.crate_name : 'matching crate';
  }
  function keysFor(series) {
    return $$('.stash-card.kind-key').filter(function (card) {
      return (' ' + card.dataset.opens + ' ').indexOf(' ' + series + ' ') >= 0 && idsOf(card).length;
    });
  }
  function cratesFor(keyCard) {
    var opens = (keyCard.dataset.opens || '').split(' ');
    return $$('.stash-card.kind-crate').filter(function (card) {
      return opens.indexOf(card.dataset.series) >= 0 && idsOf(card).length && !card.classList.contains('leaving');
    });
  }

  // ------------------------------------------------------- the open/need-key buttons
  function refreshButtons(left) {
    $$('.stash-card.kind-crate').forEach(function (card) {
      // the server's counts after an opening; otherwise the key cards on the shelf
      var hasKey = left ? ((left[card.dataset.series] || {}).keys || 0) > 0
                        : keysFor(card.dataset.series).length > 0;
      var open = card.querySelector('[data-open-crate]');
      var need = card.querySelector('[data-need-key]');
      if (open) open.classList.toggle('hidden', !hasKey);
      if (need) need.classList.toggle('hidden', hasKey);
      card.classList.toggle('openable', hasKey);
    });
  }

  // ------------------------------------------------------------ key mode
  /* Pick up a key: it follows the pointer, the crates it opens light up and
     everything else dims.  Click one of the lit crates to use it; Escape,
     the banner's Cancel or a click anywhere else puts the key back. */
  var armed = null;     // { card, ghost, banner, series }
  var pointer = { x: window.innerWidth / 2, y: window.innerHeight / 2 };

  function snapshot(card) {
    var canvas = card.querySelector('canvas');
    try { return canvas ? canvas.toDataURL() : ''; } catch (e) { return ''; }
  }

  function arm(keyCard) {
    if (armed && armed.card === keyCard) { disarm(); return; }
    disarm();
    if (!idsOf(keyCard).length) return;
    var targets = cratesFor(keyCard);
    var opens = (keyCard.dataset.opens || '').split(' ').filter(Boolean);
    var name = opens.map(crateName).join(' / ');
    document.body.classList.add('key-mode');
    keyCard.classList.add('armed');
    $$('.stash-card, #inv-grid .item').forEach(function (card) {
      if (card === keyCard) return;
      card.classList.toggle('pickable', targets.indexOf(card) >= 0);
      card.classList.toggle('dimmed', targets.indexOf(card) < 0);
    });

    var ghost = document.createElement('div');
    ghost.className = 'key-ghost';
    var img = snapshot(keyCard);
    ghost.innerHTML = img ? '<img alt="" src="' + img + '">' : '<span>&#128273;</span>';
    document.body.appendChild(ghost);
    moveGhost(ghost, pointer.x, pointer.y);

    var banner = document.createElement('div');
    banner.className = 'key-banner theme-' + (((window.CRATE_SERIES || {})[opens[0]] || {}).theme || 'classic');
    banner.innerHTML = targets.length
      ? '<span class="kb-icon">&#128273;</span><div><b>' + esc(keyCard.dataset.name) + ' in hand</b>' +
        '<span>Click a glowing <b>' + esc(name) + '</b> to unlock it.</span></div>' +
        '<button type="button" class="btn small">Cancel <kbd>Esc</kbd></button>'
      : '<span class="kb-icon">&#128273;</span><div><b>No crate for this key</b>' +
        '<span>This key opens the ' + esc(name) + ' &mdash; you have none right now.</span></div>' +
        '<a class="btn small primary" href="/market?slot=stash">Get a crate</a>' +
        '<button type="button" class="btn small">Put it back</button>';
    document.body.appendChild(banner);
    requestAnimationFrame(function () { banner.classList.add('in'); ghost.classList.add('in'); });
    banner.querySelector('button').addEventListener('click', function (e) { e.stopPropagation(); disarm(); });

    armed = { card: keyCard, ghost: ghost, banner: banner };
    if (targets.length) {
      // bring the first lit crate into view if the shelf scrolled away
      var r = targets[0].getBoundingClientRect();
      if (r.bottom < 0 || r.top > window.innerHeight) targets[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function disarm() {
    if (!armed) return;
    var a = armed;
    armed = null;
    document.body.classList.remove('key-mode');
    a.card.classList.remove('armed');
    $$('.pickable, .dimmed').forEach(function (c) { c.classList.remove('pickable', 'dimmed'); });
    a.banner.classList.remove('in');
    setTimeout(function () { a.banner.remove(); }, 300);
    if (a.ghost.isConnected && !a.ghost.classList.contains('flying')) {
      a.ghost.classList.remove('in');
      setTimeout(function () { a.ghost.remove(); }, 250);
    }
  }

  function moveGhost(ghost, x, y) {
    ghost.style.transform = 'translate(' + (x + 14) + 'px,' + (y + 10) + 'px) rotate(-28deg)';
  }

  document.addEventListener('pointermove', function (e) {
    pointer.x = e.clientX; pointer.y = e.clientY;
    if (armed && !armed.ghost.classList.contains('flying')) moveGhost(armed.ghost, e.clientX, e.clientY);
  }, { passive: true });

  /* The key flies into the crate's keyhole, the crate jolts, and then the
     full-screen stage takes over.  `from` is the key card the key leaves
     from when no key was in hand (the Open button). */
  function useKey(crateCard, keyCard, ghost) {
    var crateIds = idsOf(crateCard), keyIds = idsOf(keyCard);
    if (!crateIds.length || !keyIds.length || !window.Crates) return;
    var series = crateCard.dataset.series;
    var target = crateCard.querySelector('.thumb-wrap').getBoundingClientRect();
    if (!ghost) {
      ghost = document.createElement('div');
      ghost.className = 'key-ghost in';
      var img = snapshot(keyCard);
      ghost.innerHTML = img ? '<img alt="" src="' + img + '">' : '<span>&#128273;</span>';
      document.body.appendChild(ghost);
      var from = keyCard.querySelector('.thumb-wrap').getBoundingClientRect();
      moveGhost(ghost, from.left + from.width / 2 - 40, from.top + from.height / 2 - 40);
    }
    if (armed) { armed.ghost = document.createElement('div'); disarm(); }
    crateCard.classList.add('unlocking');
    var go = function () {
      ghost.classList.add('flying');
      ghost.style.transform = 'translate(' + (target.left + target.width / 2 - 34) + 'px,' +
        (target.top + target.height / 2 - 30) + 'px) rotate(0deg) scale(.55)';
    };
    if (reduced()) go(); else requestAnimationFrame(function () { requestAnimationFrame(go); });
    setTimeout(function () {
      ghost.classList.add('turn');
      crateCard.classList.add('jolt');
      if (window.Crates && Crates.sfx) Crates.sfx('turn');
    }, reduced() ? 0 : 520);
    setTimeout(function () {
      ghost.remove();
      crateCard.classList.remove('unlocking', 'jolt');
      Crates.open({
        series: series,
        crateInv: crateIds[0],
        keyInv: keyIds[0],
        crateItem: crateCard.dataset.stack,
        keyItem: keyCard.dataset.stack
      });
    }, reduced() ? 60 : 900);
  }

  // ------------------------------------------------------- after opening
  /* The crate and key are gone from the shelf, and the thing that came out
     lands at the front of the grid with a NEW ribbon on it. */
  var currentSlot = (new URLSearchParams(location.search)).get('slot') || 'all';

  function wonCard(it) {
    var card = document.createElement('div');
    card.className = 'item tier-' + it.tier + ' just-won';
    card.dataset.inv = it.inv_id;
    card.style.setProperty('--won', it.grade_color || '#f2a93b');
    var wearable = it.slot !== 'usable';
    card.innerHTML =
      '<div class="thumb-wrap">' +
      '<canvas class="thumb item-thumb" width="216" height="216" data-item="' + esc(it.item_id) +
      '" data-effect="' + esc(it.effect || '') + '"></canvas>' +
      '<span class="tier-flag ' + esc(it.tier) + '">' + esc(it.tier_label) + '</span>' +
      '<span class="new-flag">New!</span>' +
      (it.effect_name ? '<span class="effect-flag">' + esc(it.effect_name) + '</span>' : '') +
      '</div><div class="meta">' +
      '<span class="iname" title="' + esc(it.name) + '">' + esc(it.name) + '</span>' +
      '<span class="islot">' + esc(it.slot_label) + ' &bull; #' + it.serial + '</span>' +
      '<div class="spread" style="margin-top:5px">' +
      (wearable
        ? '<button class="btn small primary" data-equip-inv="' + it.inv_id + '" data-slot="' + esc(it.slot) + '">Wear</button>'
        : '<a class="btn small" href="/avatar#hotbar">Hotbar</a>') +
      '<button class="btn small" data-sell="' + it.inv_id + '" data-name="' + esc(it.name) +
      '" data-item="' + esc(it.item_id) + '" data-refund="' + Math.floor((it.price || 0) * 0.4) +
      '" title="Sell back for 40%">Sell</button>' +
      '</div></div>';
    return card;
  }

  document.addEventListener('crates:opened', function (e) {
    var res = e.detail || {};
    if (res.used) { takeId(res.used.crate); takeId(res.used.key); }
    refreshButtons(res.left);
    var it = res.item;
    if (!it) return;
    if (currentSlot !== 'all' && currentSlot !== it.slot) return;
    var grid = $('#inv-grid');
    if (!grid) return;
    var card = wonCard(it);
    grid.insertBefore(card, grid.firstChild);
    var empty = grid.parentNode.querySelector('p.muted');
    if (empty && !grid.children.length) empty.remove();
    if (window.Thumbs) Thumbs.rescan();
    var total = $('[data-inv-total]');
    if (total) total.textContent = (parseInt(total.textContent, 10) || 0) - 1;
  });

  // ------------------------------------------------------------ wear + sell
  function wear(button) {
    Site.post('/api/avatar/equip', {
      slot: button.dataset.slot,
      inv_id: parseInt(button.dataset.equipInv, 10)
    }).then(function (res) {
      if (!res.ok) { Site.toast(res.error, 'bad'); return; }
      Site.toast('Equipped. Check your profile!');
      // one slot holds one item, so clear the old "Worn" marker first
      $$('[data-slot="' + button.dataset.slot + '"][data-equip-inv]').forEach(function (other) {
        var card = other.closest('.item');
        var flag = card && card.querySelector('.owned-flag');
        if (flag && flag.textContent === 'Worn') flag.remove();
      });
      var card = button.closest('.item');
      if (card && !card.querySelector('.owned-flag')) {
        var flag = document.createElement('span');
        flag.className = 'owned-flag';
        flag.textContent = 'Worn';
        card.querySelector('.thumb-wrap').appendChild(flag);
      }
    });
  }

  function sell(button) {
    var refund = parseInt(button.dataset.refund, 10) || 0;
    Site.dialog({
      title: 'Sell this item?',
      tone: 'red',
      danger: true,
      confirm: 'Sell it',
      cancel: 'Keep it',
      bodyHtml: '<div class="spread" style="gap:12px;align-items:flex-start">' +
        '<canvas class="item-thumb" width="180" height="180" data-item="' +
        esc(button.dataset.item) + '" style="width:80px;height:80px;flex:0 0 80px;' +
        'background:var(--tile-normal);border:1px solid var(--line-soft);border-radius:4px"></canvas>' +
        '<div><b>' + esc(button.dataset.name) + '</b>' +
        '<p style="margin:6px 0 0">Selling returns 40% of the catalogue price: ' +
        '<span class="coin" style="vertical-align:-1px"></span> <b>' +
        refund.toLocaleString() + '</b>.</p>' +
        '<p class="tiny muted" style="margin:6px 0 0">This copy, serial and any ' +
        'Unusual effect on it are gone for good.</p></div></div>'
    }).then(function (yes) {
      if (!yes) return;
      var invId = parseInt(button.dataset.sell, 10);
      Site.post('/api/market/sell', { inv_id: invId }).then(function (res) {
        if (!res.ok) { Site.toast(res.error, 'bad'); return; }
        Site.toast('Sold for ' + res.refund.toLocaleString() + ' Noogets.');
        var card = button.closest('.item');
        if (card && card.classList.contains('stash-card')) {
          takeId(invId);
          // the server's stash counts are the truth for the Open buttons
          Site.get('/api/crates/stash').then(function (r) {
            if (r.ok && window.Crates) { Crates.setStash(r.counts); refreshButtons(r.counts); }
          });
        } else if (card) {
          card.remove();
        }
        if (window.Crates) Crates.setBalance(res.balance);
      });
    });
  }

  // ---------------------------------------------------------------- boot
  document.addEventListener('DOMContentLoaded', function () {
    refreshButtons();

    document.addEventListener('click', function (e) {
      var t = e.target;
      var equip = t.closest('[data-equip-inv]');
      if (equip) { wear(equip); return; }
      var sale = t.closest('[data-sell]');
      if (sale) { if (armed) disarm(); sell(sale); return; }
      if (t.closest('[data-contents], .key-banner')) return;

      // a key in hand and a lit crate under the pointer
      if (armed) {
        var crate = t.closest('.stash-card.pickable');
        if (crate) { e.preventDefault(); useKey(crate, armed.card, armed.ghost); return; }
        if (t.closest('.stash-card.armed') && !t.closest('[data-use-key]')) { disarm(); return; }
        if (!t.closest('[data-use-key]')) { disarm(); return; }
      }

      var keyButton = t.closest('[data-use-key]');
      if (keyButton) { e.preventDefault(); arm(keyButton.closest('.stash-card')); return; }

      // the Open button on a crate, or the crate itself when a key is held
      var openButton = t.closest('[data-open-crate]');
      var crateCard = openButton ? openButton.closest('.stash-card')
        : (t.closest('.stash-card.kind-crate.openable .thumb-wrap') || { closest: function () { return null; } }).closest('.stash-card');
      if (crateCard) {
        e.preventDefault();
        var keys = keysFor(crateCard.dataset.series);
        if (!keys.length) { Site.toast('You need a key for that crate.', 'bad'); return; }
        useKey(crateCard, keys[0], null);
        return;
      }

      // clicking a key card's picture picks the key up too
      var keyCard = t.closest('.stash-card.kind-key .thumb-wrap');
      if (keyCard) { e.preventDefault(); arm(keyCard.closest('.stash-card')); }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && armed) disarm();
    });
  });
})();
