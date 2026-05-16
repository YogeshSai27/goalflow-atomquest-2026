/**
 * charts.js — Chart.js configuration helpers for GoalFlow dashboards.
 * Requires chart.js loaded before this file.
 */

// ─── Brand colours ──────────────────────────────────────────────────────────
const GF_COLORS = {
  blue:   '#2563eb',
  green:  '#16a34a',
  yellow: '#ca8a04',
  red:    '#dc2626',
  gray:   '#94a3b8',
  blueAlpha:   'rgba(37,99,235,0.15)',
  greenAlpha:  'rgba(22,163,74,0.15)',
  yellowAlpha: 'rgba(202,138,4,0.15)',
  redAlpha:    'rgba(220,38,38,0.15)',
};

Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
Chart.defaults.font.size   = 12;
Chart.defaults.color       = '#64748b';
Chart.defaults.plugins.legend.labels.boxWidth = 12;

// ─── Trend line chart (quarterly progress) ───────────────────────────────────
function renderTrendChart(canvasId, labels, datasets) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  return new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: { mode: 'index', intersect: false },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: val => val + '%',
          },
          grid: { color: '#f1f5f9' },
        },
        x: { grid: { display: false } },
      },
      elements: {
        line: { tension: 0.3 },
        point: { radius: 4, hoverRadius: 6 },
      },
    },
  });
}

// ─── Donut / doughnut chart ──────────────────────────────────────────────────
function renderDonutChart(canvasId, labels, data, colors) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors || [GF_COLORS.green, GF_COLORS.yellow, GF_COLORS.red, GF_COLORS.gray],
        borderWidth: 2,
        borderColor: '#ffffff',
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right' },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.parsed}`,
          },
        },
      },
      cutout: '65%',
    },
  });
}

// ─── Horizontal bar chart (completion by department/manager) ─────────────────
function renderBarChart(canvasId, labels, data, label, color) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: label || 'Progress',
        data,
        backgroundColor: color || GF_COLORS.blueAlpha,
        borderColor:     color ? color : GF_COLORS.blue,
        borderWidth: 2,
        borderRadius: 4,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.parsed.x.toFixed(1)}%`,
          },
        },
      },
      scales: {
        x: {
          beginAtZero: true,
          max: 100,
          ticks: { callback: val => val + '%' },
          grid: { color: '#f1f5f9' },
        },
        y: { grid: { display: false } },
      },
    },
  });
}
