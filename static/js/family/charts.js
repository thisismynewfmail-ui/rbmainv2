/* The dashboard's charts, drawn as SVG from the report the page was rendered
   with.  No libraries.

   The rules they follow: one axis; thin columns (never more than 24px) with
   a rounded data end and a square foot on the baseline; hairline grid; a
   2px gap between neighbouring columns; colour by job (one hue for one
   series, two validated hues and a legend for two, a one-hue light-to-dark
   ramp for the heat map); text in the ink colours, never the series colour;
   a tooltip on every mark for the pointer AND the keyboard; and a table
   view for every chart (the "Table" buttons).

   Each chart is drawn at the pixel size of its box -- not scaled -- so its
   text is the same 11px on a phone and on a wide screen, and it is drawn
   again when the box changes size. */
(function (global) {
  'use strict';
  var NS = 'http://www.w3.org/2000/svg';
  var tip = null;

  function el(name, attrs, parent) {
    var node = document.createElementNS(NS, name);
    for (var k in attrs) if (attrs[k] !== undefined && attrs[k] !== null) node.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(node);
    return node;
  }
  function text(parent, x, y, value, cls, anchor) {
    var t = el('text', { x: x, y: y, 'class': cls || 'tick', 'text-anchor': anchor || 'middle' }, parent);
    t.textContent = value;
    return t;
  }
  function niceMax(v, step) {
    step = step || 30;
    if (v <= 0) return step;
    return Math.ceil(v / step) * step;
  }
  function minutesTick(v) {
    v = Math.round(v);
    if (v < 60) return v + 'm';
    var h = Math.floor(v / 60), m = v % 60;
    return m ? h + 'h' + (m < 10 ? '0' : '') + m : h + 'h';
  }
  /* a column: rounded at the top (the data end), square on the baseline */
  function column(x, y, w, h, r) {
    if (h <= 0) return '';
    r = Math.min(r, w / 2, h);
    return 'M' + x + ' ' + (y + h) + 'V' + (y + r) + 'Q' + x + ' ' + y + ' ' + (x + r) + ' ' + y +
           'H' + (x + w - r) + 'Q' + (x + w) + ' ' + y + ' ' + (x + w) + ' ' + (y + r) + 'V' + (y + h) + 'Z';
  }
  function widthOf(host) {
    return Math.max(260, Math.floor(host.getBoundingClientRect().width || host.clientWidth || 600));
  }

  /* ------------------------------------------------------------ tooltip */
  function ensureTip() {
    if (tip) return tip;
    tip = document.createElement('div');
    tip.className = 'chart-tip';
    tip.setAttribute('aria-hidden', 'true');
    document.body.appendChild(tip);
    return tip;
  }
  function showTip(target, lead, rest) {
    var t = ensureTip();
    t.textContent = '';
    var b = document.createElement('b');
    b.textContent = lead;
    t.appendChild(b);
    if (rest) t.appendChild(document.createTextNode(rest));
    var r = target.getBoundingClientRect();
    var half = Math.min(150, (t.offsetWidth || 180) / 2 + 8);
    var x = Math.min(window.innerWidth - half, Math.max(half, r.left + r.width / 2));
    t.style.left = x + 'px';
    t.style.top = Math.max(64, r.top) + 'px';
    t.classList.add('show');
  }
  function hideTip() { if (tip) tip.classList.remove('show'); }
  function hover(node, lead, rest, mark, focusable) {
    if (focusable !== false) node.setAttribute('tabindex', '0');
    node.setAttribute('role', 'img');
    node.setAttribute('aria-label', lead + (rest ? ', ' + rest : ''));
    var on = function () { showTip(node, lead, rest); if (mark) mark.classList.add('hover'); };
    var off = function () { hideTip(); if (mark) mark.classList.remove('hover'); };
    node.addEventListener('pointerenter', on);
    node.addEventListener('pointerleave', off);
    node.addEventListener('focus', on);
    node.addEventListener('blur', off);
  }
  window.addEventListener('scroll', hideTip, { passive: true });

  /* draw now, and again whenever the box changes width */
  var drawn = [];
  function keep(host, draw) {
    host.setAttribute('role', 'group');
    var entry = { host: host, draw: draw, w: 0 };
    drawn.push(entry);
    entry.w = widthOf(host);
    draw(entry.w);
  }
  var resizeTimer = 0;
  function redraw() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      drawn.forEach(function (d) {
        if (d.host.offsetParent === null) return;      /* hidden (table view) */
        var w = widthOf(d.host);
        if (Math.abs(w - d.w) < 2) return;
        d.w = w;
        d.draw(w);
      });
    }, 120);
  }
  if ('ResizeObserver' in window) {
    var ro = new ResizeObserver(redraw);
    setTimeout(function () { drawn.forEach(function (d) { ro.observe(d.host); }); }, 0);
  } else {
    window.addEventListener('resize', redraw);
  }

  /* ----------------------------------------------- minutes per day, 14d */
  function days(host, chart) {
    if (!host || !chart || !chart.length) return;
    keep(host, function (W) {
      var narrow = W < 460;
      var H = narrow ? 200 : 230, padL = 40, padR = 6, padT = 22, padB = 28;
      var plotW = W - padL - padR, plotH = H - padT - padB;
      var maxMin = 0;
      chart.forEach(function (d) { maxMin = Math.max(maxMin, d.minutes, d.limit ? d.limit : 0); });
      var step = maxMin > 150 ? 60 : 30;
      var top = niceMax(maxMin * 1.08, step);
      var svg = el('svg', { width: W, height: H, viewBox: '0 0 ' + W + ' ' + H, focusable: 'false' });
      var steps = top / step;
      while (steps > (narrow ? 4 : 5)) steps = Math.ceil(steps / 2);
      for (var i = 0; i <= steps; i++) {
        var v = top * i / steps;
        var y = Math.round(padT + plotH - plotH * v / top) + 0.5;
        el('line', { x1: padL, x2: W - padR, y1: y, y2: y, 'class': i === 0 ? 'axis' : 'gridline' }, svg);
        text(svg, padL - 8, y + 4, minutesTick(v), 'tick', 'end');
      }
      var band = plotW / chart.length;
      var bw = Math.max(4, Math.min(24, band - Math.max(2, band * 0.32)));
      chart.forEach(function (d, idx) {
        var x = padL + band * idx + (band - bw) / 2;
        var h = plotH * d.minutes / top;
        var y = padT + plotH - h;
        var g = el('g', {}, svg);
        var hit = el('rect', { x: padL + band * idx, y: padT, width: band, height: plotH, 'class': 'hit' }, g);
        var bar = el('path', { d: column(x, y, bw, Math.max(h, d.minutes > 0 ? 2 : 0), 4),
                               'class': 'bar' + (d.today ? '' : ' dim') }, g);
        if (d.limit) {
          var ly = Math.round(padT + plotH - plotH * d.limit / top);
          el('line', { x1: x - 3, x2: x + bw + 3, y1: ly, y2: ly, 'class': 'limit' }, g);
        }
        if (!narrow || idx % 2 === (chart.length - 1) % 2) {
          text(svg, x + bw / 2, H - 9, d.short, 'tick' + (d.today ? ' label' : ''));
        }
        if (d.today && d.minutes > 0) text(svg, x + bw / 2, Math.max(12, y - 7), Math.round(d.minutes) + 'm', 'label');
        var limitText = d.limit === null || d.limit === undefined ? 'no limit' : (d.limit === 0 ? 'no games' : 'limit ' + minutesTick(d.limit));
        hover(hit, Math.round(d.minutes) + ' min', ' — ' + d.label + (d.today ? ' (today)' : '') + ' · ' + limitText, bar);
      });
      host.innerHTML = '';
      host.appendChild(svg);
    });
  }

  /* ------------------------------------ messages sent and received, 14d */
  function messages(host, daysData) {
    if (!host || !daysData || !daysData.length) return;
    keep(host, function (W) {
      var narrow = W < 460;
      var H = narrow ? 180 : 210, padL = 30, padR = 6, padT = 16, padB = 28;
      var plotW = W - padL - padR, plotH = H - padT - padB;
      var maxV = 0;
      daysData.forEach(function (d) { maxV = Math.max(maxV, d.sent, d.received); });
      var top = Math.max(4, niceMax(maxV, maxV > 20 ? 10 : 2));
      var svg = el('svg', { width: W, height: H, viewBox: '0 0 ' + W + ' ' + H, focusable: 'false' });
      var steps = 4;
      for (var i = 0; i <= steps; i++) {
        var v = top * i / steps;
        var y = Math.round(padT + plotH - plotH * v / top) + 0.5;
        el('line', { x1: padL, x2: W - padR, y1: y, y2: y, 'class': i === 0 ? 'axis' : 'gridline' }, svg);
        if (v === Math.round(v)) text(svg, padL - 8, y + 4, String(v), 'tick', 'end');
      }
      var band = plotW / daysData.length;
      var bw = Math.max(3, Math.min(12, (band - Math.max(6, band * 0.3) - 2) / 2));
      daysData.forEach(function (d, idx) {
        var x0 = padL + band * idx + (band - (bw * 2 + 2)) / 2;
        var g = el('g', {}, svg);
        var hit = el('rect', { x: padL + band * idx, y: padT, width: band, height: plotH, 'class': 'hit' }, g);
        [['sent', 'bar', 0], ['received', 'bar b2', 1]].forEach(function (s) {
          var val = d[s[0]];
          var h = plotH * val / top;
          el('path', { d: column(x0 + s[2] * (bw + 2), padT + plotH - h, bw, h, 3), 'class': s[1] }, g);
        });
        if (!narrow || idx % 2 === (daysData.length - 1) % 2) {
          text(svg, padL + band * idx + band / 2, H - 9, d.short, 'tick');
        }
        hover(hit, d.sent + ' sent · ' + d.received + ' received', ' — ' + d.label);
      });
      host.innerHTML = '';
      host.appendChild(svg);
    });
  }

  /* ------------------------------------------ when they play: day x hour */
  var DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  var DAY_NAMES = ['Mondays', 'Tuesdays', 'Wednesdays', 'Thursdays', 'Fridays', 'Saturdays', 'Sundays'];
  function hourLabel(h) { return h === 0 ? '12a' : (h < 12 ? h + 'a' : (h === 12 ? '12p' : (h - 12) + 'p')); }
  function heatBin(v, max) { return v <= 0 ? 0 : Math.min(5, 1 + Math.floor(4.999 * v / Math.max(1, max))); }
  function heat(host, matrix, max) {
    if (!host || !matrix) return;
    var focus = { d: 0, h: 0 };
    /* start the keyboard on the busiest cell */
    var best = -1;
    for (var bd = 0; bd < 7; bd++) for (var bh = 0; bh < 24; bh++) {
      if ((matrix[bd][bh] || 0) > best) { best = matrix[bd][bh] || 0; focus = { d: bd, h: bh }; }
    }
    keep(host, function (W) {
      var padL = 38, padR = 2, padT = 4, padB = 22;
      var cellW = (W - padL - padR) / 24;
      var cellH = Math.max(14, Math.min(30, cellW * 0.78));
      var H = Math.round(padT + cellH * 7 + padB);
      var gap = cellW > 16 ? 2 : 1;
      var svg = el('svg', { width: W, height: H, viewBox: '0 0 ' + W + ' ' + H, focusable: 'false' });
      var cells = [];
      for (var d = 0; d < 7; d++) {
        text(svg, padL - 8, padT + cellH * d + cellH / 2 + 4, DAYS[d], 'tick', 'end');
        cells.push([]);
        for (var h = 0; h < 24; h++) {
          var v = matrix[d][h] || 0;
          var rect = el('rect', { x: (padL + cellW * h + gap / 2).toFixed(1), y: (padT + cellH * d + gap / 2).toFixed(1),
                                  width: Math.max(1, cellW - gap).toFixed(1), height: Math.max(1, cellH - gap).toFixed(1),
                                  rx: Math.min(4, cellW / 4).toFixed(1), 'class': 'cell',
                                  fill: 'var(--heat-' + heatBin(v, max) + ')' }, svg);
          rect.setAttribute('data-d', d);
          rect.setAttribute('data-h', h);
          hover(rect, Math.round(v / 60) + ' min', ' — ' + DAY_NAMES[d] + ' around ' + hourLabel(h) + ' (last 4 weeks)', null, false);
          rect.setAttribute('tabindex', d === focus.d && h === focus.h ? '0' : '-1');
          cells[d].push(rect);
        }
      }
      /* one tab stop for the whole grid; the arrow keys move inside it */
      svg.addEventListener('keydown', function (e) {
        var moves = { ArrowLeft: [0, -1], ArrowRight: [0, 1], ArrowUp: [-1, 0], ArrowDown: [1, 0],
                      Home: [0, -24], End: [0, 24] };
        var m = moves[e.key];
        if (!m) return;
        e.preventDefault();
        cells[focus.d][focus.h].setAttribute('tabindex', '-1');
        focus = { d: Math.max(0, Math.min(6, focus.d + m[0])), h: Math.max(0, Math.min(23, focus.h + m[1])) };
        var next = cells[focus.d][focus.h];
        next.setAttribute('tabindex', '0');
        next.focus();
      });
      var every = cellW < 14 ? 6 : 3;
      for (var hh = 0; hh < 24; hh += every) text(svg, padL + cellW * hh + cellW / 2, H - 6, hourLabel(hh), 'tick');
      host.innerHTML = '';
      host.appendChild(svg);
    });
    /* the table view: minutes per day and hour, empty where none */
    var card = host.closest('.db-card');
    var table = card && card.querySelector('.chart-table');
    if (table && !table.firstChild) {
      var wrap = document.createElement('div');
      wrap.className = 'db-table-wrap';
      var t = document.createElement('table');
      t.className = 'db-table heat-table';
      var head = '<thead><tr><th scope="col">Day</th>';
      for (var hx = 0; hx < 24; hx++) head += '<th scope="col">' + hourLabel(hx) + '</th>';
      head += '<th scope="col">Total</th></tr></thead><tbody>';
      for (var dx = 0; dx < 7; dx++) {
        var row = '<tr><th scope="row">' + DAYS[dx] + '</th>', sum = 0;
        for (var hy = 0; hy < 24; hy++) {
          var mins = Math.round((matrix[dx][hy] || 0) / 60);
          sum += matrix[dx][hy] || 0;
          row += '<td>' + (mins ? mins : '') + '</td>';
        }
        head += row + '<td><b>' + Math.round(sum / 60) + '</b></td></tr>';
      }
      t.innerHTML = head + '</tbody>';
      var cap = document.createElement('caption');
      cap.textContent = 'Minutes played by day and hour, last 4 weeks';
      t.insertBefore(cap, t.firstChild);
      wrap.appendChild(t);
      table.appendChild(wrap);
    }
  }

  /* ---------------------------------------------------------- tables */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-table-toggle]');
    if (!btn) return;
    var card = document.getElementById(btn.getAttribute('data-table-toggle'));
    if (!card) return;
    var table = card.querySelector('.chart-table');
    var chart = card.querySelector('.chart');
    var key = card.querySelector('.heat-key');
    var showTable = table.hasAttribute('hidden');
    if (showTable) { table.removeAttribute('hidden'); chart.setAttribute('hidden', ''); }
    else { table.setAttribute('hidden', ''); chart.removeAttribute('hidden'); redraw(); }
    if (key) key.hidden = showTable;
    btn.setAttribute('aria-pressed', showTable ? 'true' : 'false');
    btn.textContent = showTable ? 'Chart' : 'Table';
  });

  global.FamCharts = { days: days, messages: messages, heat: heat, redraw: redraw };
})(window);
