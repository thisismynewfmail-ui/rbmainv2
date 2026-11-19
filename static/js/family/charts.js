/* The dashboard's charts, drawn as SVG from the report the page was rendered
   with.  No libraries.

   The rules they follow: one axis; thin columns (never more than 24px) with
   a rounded data end and a square foot on the baseline; hairline grid; a
   2px gap between neighbouring columns; colour by job (one hue for one
   series, two validated hues and a legend for two, a one-hue light-to-dark
   ramp for the heat map); text in the ink colours, never the series colour;
   a tooltip on every mark for the pointer AND the keyboard; and a table
   view for every chart (the "Table" buttons). */
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
  /* a column: rounded at the top (the data end), square on the baseline */
  function column(x, y, w, h, r) {
    if (h <= 0) return '';
    r = Math.min(r, w / 2, h);
    return 'M' + x + ' ' + (y + h) + 'V' + (y + r) + 'Q' + x + ' ' + y + ' ' + (x + r) + ' ' + y +
           'H' + (x + w - r) + 'Q' + (x + w) + ' ' + y + ' ' + (x + w) + ' ' + (y + r) + 'V' + (y + h) + 'Z';
  }

  /* ------------------------------------------------------------ tooltip */
  function ensureTip() {
    if (tip) return tip;
    tip = document.createElement('div');
    tip.className = 'chart-tip';
    tip.setAttribute('role', 'status');
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
    var x = Math.min(window.innerWidth - 90, Math.max(90, r.left + r.width / 2));
    t.style.left = x + 'px';
    t.style.top = Math.max(60, r.top) + 'px';
    t.classList.add('show');
  }
  function hideTip() { if (tip) tip.classList.remove('show'); }
  function hover(node, lead, rest, mark) {
    node.setAttribute('tabindex', '0');
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

  /* ----------------------------------------------- minutes per day, 14d */
  function days(host, chart) {
    if (!host || !chart || !chart.length) return;
    var W = 640, H = 230, padL = 38, padR = 8, padT = 22, padB = 30;
    var plotW = W - padL - padR, plotH = H - padT - padB;
    var maxMin = 0;
    chart.forEach(function (d) {
      maxMin = Math.max(maxMin, d.minutes, d.limit ? d.limit : 0);
    });
    var top = niceMax(maxMin * 1.08, maxMin > 150 ? 60 : 30);
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, 'aria-hidden': 'true' });
    var steps = top / (top > 150 ? 60 : 30);
    while (steps > 5) steps = Math.ceil(steps / 2);
    for (var i = 0; i <= steps; i++) {
      var v = top * i / steps;
      var y = padT + plotH - plotH * v / top;
      el('line', { x1: padL, x2: W - padR, y1: y, y2: y, 'class': i === 0 ? 'axis' : 'gridline' }, svg);
      text(svg, padL - 8, y + 4, v >= 60 && v % 60 === 0 ? (v / 60) + 'h' : Math.round(v) + 'm', 'tick', 'end');
    }
    var band = plotW / chart.length;
    var bw = Math.min(24, band - 6);
    chart.forEach(function (d, idx) {
      var x = padL + band * idx + (band - bw) / 2;
      var h = plotH * d.minutes / top;
      var y = padT + plotH - h;
      var g = el('g', {}, svg);
      var bar = el('path', { d: column(x, y, bw, Math.max(h, d.minutes > 0 ? 2 : 0), 4),
                             'class': 'bar' + (d.today ? '' : ' dim') }, g);
      if (d.limit) {
        var ly = padT + plotH - plotH * d.limit / top;
        el('line', { x1: x - 4, x2: x + bw + 4, y1: ly, y2: ly, 'class': 'limit' }, g);
      }
      text(svg, x + bw / 2, H - 10, d.short, 'tick' + (d.today ? ' label' : ''));
      if (d.today && d.minutes > 0) text(svg, x + bw / 2, Math.max(12, y - 6), Math.round(d.minutes) + 'm', 'label');
      var hit = el('rect', { x: padL + band * idx, y: padT, width: band, height: plotH, 'class': 'hit' }, g);
      g.insertBefore(hit, bar);
      var limitText = d.limit === null || d.limit === undefined ? 'no limit' : (d.limit === 0 ? 'no games' : 'limit ' + d.limit + ' min');
      hover(hit, Math.round(d.minutes) + ' min', ' — ' + d.label + (d.today ? ' (today)' : '') + ' · ' + limitText, bar);
    });
    host.innerHTML = '';
    host.appendChild(svg);
  }

  /* ------------------------------------ messages sent and received, 14d */
  function messages(host, daysData) {
    if (!host || !daysData || !daysData.length) return;
    var W = 640, H = 210, padL = 30, padR = 8, padT = 16, padB = 30;
    var plotW = W - padL - padR, plotH = H - padT - padB;
    var maxV = 0;
    daysData.forEach(function (d) { maxV = Math.max(maxV, d.sent, d.received); });
    var top = Math.max(4, niceMax(maxV, maxV > 20 ? 10 : 2));
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, 'aria-hidden': 'true' });
    var steps = 4;
    for (var i = 0; i <= steps; i++) {
      var v = top * i / steps;
      var y = padT + plotH - plotH * v / top;
      el('line', { x1: padL, x2: W - padR, y1: y, y2: y, 'class': i === 0 ? 'axis' : 'gridline' }, svg);
      if (v === Math.round(v)) text(svg, padL - 8, y + 4, String(v), 'tick', 'end');
    }
    var band = plotW / daysData.length;
    var bw = Math.min(11, (band - 8) / 2);
    daysData.forEach(function (d, idx) {
      var x0 = padL + band * idx + (band - (bw * 2 + 2)) / 2;
      var g = el('g', {}, svg);
      [['sent', 'bar', 0], ['received', 'bar b2', 1]].forEach(function (s) {
        var val = d[s[0]];
        var h = plotH * val / top;
        el('path', { d: column(x0 + s[2] * (bw + 2), padT + plotH - h, bw, h, 3), 'class': s[1] }, g);
      });
      text(svg, padL + band * idx + band / 2, H - 10, d.short, 'tick');
      var hit = el('rect', { x: padL + band * idx, y: padT, width: band, height: plotH, 'class': 'hit' }, svg);
      hover(hit, d.sent + ' sent · ' + d.received + ' received', ' — ' + d.label);
    });
    host.innerHTML = '';
    host.appendChild(svg);
  }

  /* ------------------------------------------ when they play: day x hour */
  var DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  function hourLabel(h) { return h === 0 ? '12a' : (h < 12 ? h + 'a' : (h === 12 ? '12p' : (h - 12) + 'p')); }
  function heat(host, matrix, max) {
    if (!host || !matrix) return;
    var W = 660, padL = 40, padT = 6, padB = 22;
    var cell = (W - padL - 4) / 24;
    var H = padT + cell * 7 + padB;
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H.toFixed(0), 'aria-hidden': 'true' });
    var bins = [0, 1, 2, 3, 4, 5];
    for (var d = 0; d < 7; d++) {
      text(svg, padL - 8, padT + cell * d + cell / 2 + 4, DAYS[d], 'tick', 'end');
      for (var h = 0; h < 24; h++) {
        var v = matrix[d][h] || 0;
        var bin = v <= 0 ? 0 : Math.min(5, 1 + Math.floor(4.999 * v / Math.max(1, max)));
        var rect = el('rect', { x: (padL + cell * h).toFixed(1), y: (padT + cell * d).toFixed(1),
                                width: cell.toFixed(1), height: cell.toFixed(1), rx: 3,
                                'class': 'cell', fill: 'var(--heat-' + bins[bin] + ')' }, svg);
        hover(rect, Math.round(v / 60) + ' min', ' — ' + DAYS[d] + 's around ' + hourLabel(h) + ' (last 4 weeks)');
      }
    }
    for (var hh = 0; hh < 24; hh += 3) text(svg, padL + cell * hh + cell / 2, H - 6, hourLabel(hh), 'tick');
    host.innerHTML = '';
    host.appendChild(svg);
  }

  /* ---------------------------------------------------------- tables */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-table-toggle]');
    if (!btn) return;
    var card = document.getElementById(btn.getAttribute('data-table-toggle'));
    if (!card) return;
    var table = card.querySelector('.chart-table');
    var chart = card.querySelector('.chart');
    var showTable = table.hasAttribute('hidden');
    if (showTable) { table.removeAttribute('hidden'); chart.setAttribute('hidden', ''); }
    else { table.setAttribute('hidden', ''); chart.removeAttribute('hidden'); }
    btn.setAttribute('aria-pressed', showTable ? 'true' : 'false');
    btn.textContent = showTable ? 'Chart' : 'Table';
  });

  global.FamCharts = { days: days, messages: messages, heat: heat };
})(window);
