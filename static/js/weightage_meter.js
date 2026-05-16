/**
 * weightage_meter.js — Live weightage allocation meter.
 * Attach to the goal creation form — reads all weightage inputs
 * and updates the visual meter + status text in real time.
 *
 * Usage: Include this script on goal_wizard.html.
 * The meter element must have id="weightage-meter".
 */

(function () {
  'use strict';

  const MAX_WEIGHT = 100;

  function getWeightageInputs() {
    return Array.from(document.querySelectorAll('input[name="weightage"], input.weightage-input'));
  }

  function sumWeightages() {
    return getWeightageInputs().reduce((sum, el) => {
      const val = parseFloat(el.value) || 0;
      return sum + val;
    }, 0);
  }

  function updateMeter() {
    const total = sumWeightages();
    const pct   = Math.min((total / MAX_WEIGHT) * 100, 120); // allow slight over for visual

    const fill  = document.getElementById('weightage-fill');
    const label = document.getElementById('weightage-label');
    const hint  = document.getElementById('weightage-hint');
    const wrap  = document.getElementById('weightage-meter');

    if (!fill || !label || !wrap) return;

    // Update fill width (cap display at 100%)
    fill.style.width = Math.min(pct, 100) + '%';

    // Update label
    label.textContent = total.toFixed(1) + '% allocated';

    // Update color class
    wrap.classList.remove('weightage-under', 'weightage-ok', 'weightage-over');
    if (total < 100) {
      wrap.classList.add('weightage-under');
      if (hint) hint.textContent = `${(100 - total).toFixed(1)}% remaining to allocate.`;
    } else if (total === 100) {
      wrap.classList.add('weightage-ok');
      if (hint) hint.textContent = 'Perfect — total weightage is exactly 100%.';
    } else {
      wrap.classList.add('weightage-over');
      if (hint) hint.textContent = `Over by ${(total - 100).toFixed(1)}% — reduce before submitting.`;
    }

    // Enable/disable submit button based on validity
    const submitBtn = document.getElementById('wizard-submit-btn');
    if (submitBtn) {
      submitBtn.disabled = total !== 100;
    }
  }

  // Attach listeners to all existing + future weightage inputs via delegation
  document.addEventListener('input', (e) => {
    if (e.target.matches('input[name="weightage"], input.weightage-input')) {
      updateMeter();
    }
  });

  // Run on load
  document.addEventListener('DOMContentLoaded', updateMeter);

  // Expose for external calls (e.g. when a goal row is added/removed)
  window.updateWeightageMeter = updateMeter;
})();
