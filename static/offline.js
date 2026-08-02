// offline.html için — CSP uyumu için index.html'deki inline scriptten taşındı

// Online olunca otomatik yönlendir
window.addEventListener('online', () => {
  window.location.href = '/';
});

// "Tekrar Dene" butonu
document.getElementById('tekrar-dene-btn').addEventListener('click', () => {
  window.location.reload();
});
