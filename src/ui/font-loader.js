// Google Fonts'u asenkron yüklemek için media="print" → "all" trick'i
// (CSP uyumu için index.html'deki onload="" attribute'u yerine).
// NOT: DOMContentLoaded beklenmiyor — bu script <link> etiketinden hemen
// sonra, senkron olarak çalışır (script tag'i document order'da hemen
// ardında); DOMContentLoaded'ı beklersek font zaten yüklenmiş olabilir ve
// 'load' event'ini kaçırırız.
(function() {
  const link = document.getElementById('google-fonts-link');
  if (link) link.addEventListener('load', function() { this.media = 'all'; });
})();
