/**
 * utils.js — Shared frontend utilities for GoalFlow.
 * Loaded on every page via base.html.
 */

// ─── Flash message auto-dismiss ────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.4s ease';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });
});

// ─── Generic form submit guard ─────────────────────────────────────────────
// Prevents double-submit by disabling the button after first click
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', () => {
      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Saving…';
      }
    });
  });
});

// ─── Confirmation dialogs ──────────────────────────────────────────────────
function confirmAction(message) {
  return window.confirm(message || 'Are you sure?');
}

// ─── Format helpers ────────────────────────────────────────────────────────
function formatPercent(value) {
  if (value === null || value === undefined) return '—';
  return parseFloat(value).toFixed(1) + '%';
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

// ─── Health indicator helper ───────────────────────────────────────────────
function healthBadge(status) {
  const map = {
    healthy:     '<span class="badge badge-healthy">● Healthy</span>',
    watch:       '<span class="badge badge-watch">● Watch</span>',
    at_risk:     '<span class="badge badge-at_risk">● At Risk</span>',
    not_started: '<span class="badge badge-not_started">— Not Started</span>',
  };
  return map[status] || status;
}
