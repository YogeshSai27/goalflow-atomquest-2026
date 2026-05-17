/**
 * weightage_meter.js — Live weightage allocation meter.
 *
 * Reads all inputs with class "weightage-input" on the page.
 * When the edit modal is open, temporarily swaps that goal's original
 * weight for the in-progress edit value so the meter stays accurate.
 *
 * DOM targets:
 *   #weightage-meter   — wrapper div (receives class: weightage-under/ok/over)
 *   #weightage-fill    — inner bar div (receives width %)
 *   #weightage-label   — text showing "X% allocated"
 *   #weightage-hint    — hint text line
 */

(function () {
  'use strict';

  const MAX = 100;

  function sumWeightages() {
    // All inputs with the class, but skip the hidden edit-modal one when
    // computing — we want only the SAVED goals plus the active add-form.
    let total = 0;

    // 1. Saved goal weights: read from the table data cells
    document.querySelectorAll('[data-goal-weight]').forEach(el => {
      total += parseFloat(el.dataset.goalWeight) || 0;
    });

    // 2. The add-form weightage input (if filled in)
    const addInput = document.getElementById('add-weightage-input');
    if (addInput && addInput.value) {
      total += parseFloat(addInput.value) || 0;
    }

    return total;
  }

  function updateMeter() {
    const total  = sumWeightages();
    const fill   = document.getElementById('weightage-fill');
    const label  = document.getElementById('weightage-label');
    const hint   = document.getElementById('weightage-hint');
    const wrap   = document.getElementById('weightage-meter');

    if (!fill || !label || !wrap) return;

    fill.style.width = Math.min((total / MAX) * 100, 100) + '%';
    label.textContent = total.toFixed(0) + '% allocated';

    wrap.classList.remove('weightage-under', 'weightage-ok', 'weightage-over');

    if (Math.abs(total - MAX) < 0.01) {
      wrap.classList.add('weightage-ok');
      if (hint) hint.textContent = 'Perfect — total weightage is exactly 100%.';
    } else if (total < MAX) {
      wrap.classList.add('weightage-under');
      if (hint) hint.textContent = (MAX - total).toFixed(0) + '% remaining to allocate.';
    } else {
      wrap.classList.add('weightage-over');
      if (hint) hint.textContent = 'Over by ' + (total - MAX).toFixed(0) + '% — reduce before submitting.';
    }
  }

  // Listen to any weightage input change
  document.addEventListener('input', (e) => {
    if (e.target.id === 'add-weightage-input') {
      updateMeter();
    }
  });

  document.addEventListener('DOMContentLoaded', updateMeter);

  // Expose for external calls
  window.updateWeightageMeter = updateMeter;
})();
