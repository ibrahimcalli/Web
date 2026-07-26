// Hamburger Menü + Admin Sidebar Toggle + Tablo data-label
// (index.html içindeki inline <script> bloğundan CSP uyumu için taşındı — davranış değişmedi)

// Hamburger toggle (mobil menü aç/kapat)
(function() {
  var ham = document.getElementById('nav-hamburger');
  var panel = document.getElementById('nav-mobil-panel');
  if (!ham || !panel) return;
  function toggle() {
    ham.classList.toggle('aktif');
    panel.classList.toggle('aktif');
    var acik = panel.classList.contains('aktif');
    ham.setAttribute('aria-expanded', acik ? 'true' : 'false');
  }
  ham.addEventListener('click', toggle);
  // Menü dışına tıklayınca kapat
  document.addEventListener('click', function(e) {
    if (!ham.contains(e.target) && !panel.contains(e.target)) {
      ham.classList.remove('aktif');
      panel.classList.remove('aktif');
      ham.setAttribute('aria-expanded', 'false');
    }
  });
  // Sayfa geçişinde kapat (mevcut sayfaGit fonksiyonu sırasında otomatik kapanmazsa diye)
  window.navMobilKapat = function() {
    ham.classList.remove('aktif');
    panel.classList.remove('aktif');
    ham.setAttribute('aria-expanded', 'false');
  };
})();

// Admin sidebar mobil toggle (mevcut fonksiyonları bozmaz)
// DOMContentLoaded sonrası: admin sayfasındaki sidebar için toggle butonu enjekte edilir
document.addEventListener('DOMContentLoaded', function() {
  // Admin sidebar varsa, mobilde aç/kapat butonu ekle
  var sidebar = document.querySelector('.admin-sidebar');
  if (!sidebar) return;
  // Mobil toggle butonu ekle (sadece <=1023px görünür)
  var tog = document.createElement('div');
  tog.className = 'admin-mobil-tog';
  tog.innerHTML = '☰ Yönetim Menüsü';
  tog.setAttribute('role', 'button');
  tog.setAttribute('tabindex', '0');
  sidebar.parentNode.insertBefore(tog, sidebar);
  // Sidebar'a açılır sınıf ekle
  sidebar.classList.add('admin-mobil-panel');
  function adminToggle() {
    sidebar.classList.toggle('aktif');
  }
  tog.addEventListener('click', adminToggle);
  tog.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); adminToggle(); }
  });
});

// Akıllı tablo: her td'ye data-label ekle (mobilde kart için)
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('table.tablo').forEach(function(tablo) {
    var basliklar = [];
    tablo.querySelectorAll('thead th').forEach(function(th) {
      basliklar.push(th.textContent.trim());
    });
    tablo.querySelectorAll('tbody tr').forEach(function(tr) {
      tr.querySelectorAll('td').forEach(function(td, i) {
        if (!td.getAttribute('data-label') && basliklar[i]) {
          td.setAttribute('data-label', basliklar[i]);
        }
      });
    });
  });
});
