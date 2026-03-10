const revenueCtx = document.getElementById('revenueChart');
if (revenueCtx) {
  new Chart(revenueCtx, {
    type: 'line',
    data: {
      labels: ['6أ', '9أ', '12م', '3م', '6م', '9م'],
      datasets: [{
        data: [0, 200, 400, 350, 500, 650],
        borderColor: '#e94560',
        backgroundColor: 'rgba(233, 69, 96, 0.15)',
        tension: 0.4,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { display: false },
        y: { display: false }
      }
    }
  });
}

const mainCtx = document.getElementById('mainSalesChart');
if (mainCtx) {
  new Chart(mainCtx, {
    type: 'line',
    data: {
      labels: ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'],
      datasets: [
        {
          label: 'المبيعات',
          data: [120, 190, 170, 220, 260, 310, 280],
          borderColor: '#e94560',
          backgroundColor: 'rgba(233, 69, 96, 0.12)',
          tension: 0.4,
          fill: true
        },
        {
          label: 'الطلبات',
          data: [12, 18, 15, 22, 25, 30, 27],
          borderColor: '#8b2f97',
          backgroundColor: 'rgba(139, 47, 151, 0.1)',
          tension: 0.4,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#fff' }
        }
      },
      scales: {
        x: { ticks: { color: '#a0a0a0' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: '#a0a0a0' }, grid: { color: 'rgba(255,255,255,0.05)' } }
      }
    }
  });
}

document.querySelectorAll('.btn-group .btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.btn-group .btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  });
});
