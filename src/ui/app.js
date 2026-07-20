/**
 * UI uygulama katmanı — yalnızca ApiClient kullanır.
 * HTML onclick uyumluluğu için fonksiyonlar window'a bağlanır.
 */
import { api } from "../api/bootstrap.js";

// ── Durum ────────────────────────────────────────────────────────────────────
/** @type {string} — ApiClient token ile senkron tutulur */
let TOKEN = api.getToken();
let kullanici = null;
let kategoriler = {};
let ilanTipleri = {};
let duzenleId = null;
let aktifPid = null;
let mevcutResimler = [];
let gecmisSayfa = 'anasayfa';
let aramaTO = null;

function syncTokenFromApi() {
  TOKEN = api.getToken();
}

function clearSessionLocal() {
  api.logout();
  TOKEN = '';
  kullanici = null;
}

// ── Bildirim ─────────────────────────────────────────────────────────────────
function bildirim(msg, tip = 'bilgi') {
  const el = document.createElement('div');
  el.className = `bildirim bil-${tip === 'hata' ? 'hata' : tip === 'basari' ? 'basari' : 'bilgi'}`;
  el.textContent = msg;
  document.getElementById('bil-kont').appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ── Sayfa Yönetimi ───────────────────────────────────────────────────────────
function sayfaGit(sayfa, data = null) {
  if (sayfa !== 'detay') gecmisSayfa = sayfa;
  document.querySelectorAll('.sayfa').forEach(s => s.classList.remove('aktif'));
  document.querySelectorAll('.nav-link, .mobil-tab-item').forEach(b => b.classList.remove('aktif'));
  document.getElementById('sayfa-' + sayfa).classList.add('aktif');
  const nb = document.querySelector(`.nav-link[data-sayfa="${sayfa}"]`);
  if (nb) nb.classList.add('aktif');
  const tb = document.getElementById('tab-' + (sayfa === 'anasayfa' ? 'ana' : sayfa === 'ilanlar' ? 'ilan' : sayfa === 'admin' ? 'admin' : ''));
  if (tb) tb.classList.add('aktif');
  const adminSayfada = document.getElementById('sayfa-admin')?.classList.contains('aktif');
  if (sayfa === 'anasayfa')     { anaSayfaYukle(); bannerlariYukle('anasayfa_ust'); bannerlariYukle('anasayfa_hero_alti'); bannerlariYukle('tum_sayfalar_ust'); bannerlariYukle('tum_sayfalar_alt'); }
  if (sayfa === 'ilanlar')      { ilanYukle(); bannerlariYukle('ilanlar_ust'); }
  if (sayfa === 'blog')         { blogListeYukle(); }
  if (sayfa === 'blog-detay' && data) blogDetayGoster(data);
  if (sayfa === 'sayfa' && data && data.slug) sayfaGoster(data.slug);
  if (sayfa === 'admin')        { adminKontrol(); adminSayfa('portfoyler'); }
  if (sayfa === 'detay' && data) detayGoster(data);
  window.scrollTo(0, 0);
  
  // SEO update hook (mevcut fonksiyonu bozmaz, sadece meta tags günceller)
  if (typeof window.seoUpdate === 'function') {
    window.seoUpdate(sayfa, data);
  }
}
function geriGit() { sayfaGit(gecmisSayfa); }

// ── Auth ─────────────────────────────────────────────────────────────────────
async function girisYap() {
  const email = document.getElementById('g-email').value;
  const sifre = document.getElementById('g-sifre').value;
  if (!email || !sifre) { bildirim('Email ve şifre gerekli', 'hata'); return; }
  const d = await api.login(email, sifre);
  if (!d) return;
  syncTokenFromApi();
  kullanici = { rol: d.rol, ad: d.ad };
  authGuncelle();
  bildirim('Hoş geldiniz, ' + d.ad + '!', 'basari');
  sayfaGit(d.rol === 'admin' ? 'admin' : 'anasayfa');
}

function cikisYap(sessiz = false) {
  clearSessionLocal();
  authGuncelle(); sayfaGit('anasayfa');
  if (!sessiz) bildirim('Çıkış yapıldı', 'bilgi');
}

async function authGuncelle() {
  if (TOKEN) {
    const d = await api.getMe(); // 401 sessiz handle edilir
    if (d && d.giris) {
      kullanici = d;
      // Onay durumunu normalize et
      if (kullanici.onay === undefined) kullanici.onay = 1;
      const el = document.getElementById('admin-ad');
      if (el) el.textContent = d.ad_soyad || 'Admin';
    }
  }
  const isAdmin = kullanici && kullanici.rol === 'admin';
  document.getElementById('giris-btn').style.display  = kullanici ? 'none' : '';
  document.getElementById('cikis-btn').style.display  = kullanici ? '' : 'none';
  const kayitBtn = document.getElementById('kayit-btn');
  if (kayitBtn) kayitBtn.style.display = kullanici ? 'none' : '';
  document.getElementById('admin-btn').style.display  = isAdmin   ? '' : 'none';
  const tabAdmin = document.getElementById('tab-admin');
  if (tabAdmin) tabAdmin.style.display = isAdmin ? 'flex' : 'none';
}

function adminKontrol() {
  if (!kullanici || kullanici.rol !== 'admin') sayfaGit('giris');
}

// ── Kategoriler ──────────────────────────────────────────────────────────────
async function katYukle() {
  const d = await api.getKategoriler();
  if (!d) return;
  kategoriler = d.kategoriler || {}; ilanTipleri = d.ilan_tipleri || {};

  // Ana kategori bantları
  const bantlar = ['ana-kat-bant', 'ilan-kat-bant'];
  bantlar.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    const isIlan = id === 'ilan-kat-bant';
    const tiklama = isIlan ? 'katFiltrelIlan' : 'katFiltrele';
    el.innerHTML = `<div class="kat-chip aktif" data-kat="" onclick="${tiklama}(this,'')">🏘 Tümü</div>`;
    const emojiler = { 'Konut':'🏠','İş Yeri':'🏢','Arsa':'🌿','Konut Projeleri':'🏗','Bina':'🏛','Devre Mülk':'🌅','Turistik Tesis':'🏨' };
    Object.keys(kategoriler).forEach(k => {
      const chip = document.createElement('div');
      chip.className = 'kat-chip';
      chip.dataset.kat = k;
      chip.innerHTML = `${emojiler[k]||'📌'} ${k}`;
      chip.onclick = () => window[tiklama](chip, k);
      el.appendChild(chip);
    });
  });

  // Form select
  const fAna = document.getElementById('f-ana');
  if (fAna) {
    Object.keys(kategoriler).forEach(k => {
      fAna.innerHTML += `<option value="${k}">${k}</option>`;
    });
  }

  // Footer kategoriler
  const fc = document.getElementById('footer-katlar');
  if (fc) Object.keys(kategoriler).slice(0,4).forEach(k => {
    fc.innerHTML += `<a onclick="sayfaGit('ilanlar')" style="cursor:pointer">${k}</a>`;
  });
}

function anaKatDegisti() {
  const ana = document.getElementById('f-ana').value;
  const altSel = document.getElementById('f-alt');
  altSel.innerHTML = '<option value="">Seçin…</option>';
  if (ana && kategoriler[ana]) {
    kategoriler[ana].forEach(a => altSel.innerHTML += `<option value="${a}">${a}</option>`);
  }
  document.getElementById('f-tip').innerHTML = '<option value="">Seçin…</option>';
  document.getElementById('dinamik-kont').innerHTML = '';
}

async function altKatDegisti() {
  const ana = document.getElementById('f-ana').value;
  const alt = document.getElementById('f-alt').value;
  const tipSel = document.getElementById('f-tip');
  tipSel.innerHTML = '<option value="">Seçin…</option>';
  if (ana && alt && ilanTipleri[ana] && ilanTipleri[ana][alt]) {
    ilanTipleri[ana][alt].forEach(t => tipSel.innerHTML += `<option value="${t}">${t}</option>`);
  }
  if (ana && alt) {
    const alanlar = await api.getAlanlar(ana, alt);
    if (alanlar) dinamikOlustur(alanlar);
  }
}

function dinamikOlustur(alanlar, degerler = {}) {
  const kont = document.getElementById('dinamik-kont');
  if (!alanlar || !alanlar.length) { kont.innerHTML = ''; return; }
  let html = '<div class="dinamik-kutu"><div class="dinamik-kutu-baslik">🔧 Teknik Özellikler</div><div class="form-ikili" style="flex-wrap:wrap">';
  alanlar.forEach(a => {
    const v = degerler[a.key] || '';
    const cls = !v ? ' eksik' : '';
    if (a.type === 'textarea') {
      html += `</div><div class="form-grup"><label class="form-etiket">${a.label}</label>
        <textarea class="form-girdi${cls}" id="da-${a.key}" rows="2">${v}</textarea></div>
        <div class="form-ikili" style="flex-wrap:wrap">`;
    } else if (a.type === 'select') {
      const opts = (a.options || []).map(o => `<option${o===v?' selected':''}>${o}</option>`).join('');
      html += `<div class="form-grup"><label class="form-etiket">${a.label}</label>
        <select class="form-girdi${cls}" id="da-${a.key}"><option value="">Seçin…</option>${opts}</select></div>`;
    } else {
      html += `<div class="form-grup"><label class="form-etiket">${a.label}</label>
        <input class="form-girdi${cls}" type="${a.type}" id="da-${a.key}" value="${v}"></div>`;
    }
  });
  html += '</div></div>';
  kont.innerHTML = html;
}

function dinamikOku() {
  const out = {};
  document.querySelectorAll('[id^="da-"]').forEach(el => {
    out[el.id.replace('da-','')] = el.value;
  });
  return out;
}

// ── İlan Kartı ───────────────────────────────────────────────────────────────
function kartOlustur(i) {
  const el = document.createElement('div');
  el.className = 'ilan-kart';
  const fotograf = (i.resimler && i.resimler.length)
    ? `<img src="${i.resimler[0]}" alt="${i.baslik}" loading="lazy">`
    : `<div class="ilan-kart-foto-bos">🏠<span>Fotoğraf yok</span></div>`;
  const isAdmin = kullanici && kullanici.rol === 'admin';
  const m2 = i.alanlar?.net_m2 || i.alanlar?.alan_m2 || '';
  const oda = i.alanlar?.oda_sayisi || '';
  const pip = [m2 ? m2+' m²' : '', oda, i.ilan_tipi].filter(Boolean).map(p => `<span class="ilan-detay-pip">${p}</span>`).join('');
  el.innerHTML = `
    <div class="ilan-kart-foto">
      <div class="ilan-serit"></div>
      ${fotograf}
      <div class="ilan-etiket">${i.alt_kategori}</div>
      ${isAdmin && i.durum !== 'Aktif' ? `<div class="ilan-durum-badge d-${i.durum}">${i.durum}</div>` : ''}
    </div>
    <div class="ilan-kart-bilgi">
      <div class="ilan-kart-kategori">${i.ana_kategori}</div>
      <div class="ilan-kart-baslik">${i.baslik}</div>
      <div class="ilan-kart-konum">📍 ${[i.mahalle, i.ilce].filter(Boolean).join(', ')}</div>
      <div class="ilan-kart-alt">
        <div class="ilan-kart-fiyat">${i.fiyat ? (i.fiyat.includes(i.para_birimi||'TL') ? i.fiyat : i.fiyat + ' ' + (i.para_birimi||'TL')) : 'Fiyat sorunuz'}</div>
        <div class="ilan-kart-detaylar">${pip}</div>
      </div>
    </div>`;
  el.onclick = () => sayfaGit('detay', i);

  // Favori butonu
  const favBtn = el.querySelector('.fav-btn');
  if (favBtn) favBtn.onclick = (e) => {
    e.stopPropagation();
    favToggleId(i.id, i.baslik, favBtn);
  };

  // Karşılaştırma butonu
  const karsBtn = el.querySelector('.kars-btn');
  if (karsBtn) karsBtn.onclick = (e) => {
    e.stopPropagation();
    karsEkle(i.id, i.baslik, i.fiyat, i.ana_kategori, karsBtn);
  };

  return el;
}

// ── Anasayfa ─────────────────────────────────────────────────────────────────
let aktifAnaKat = '';
async function anaSayfaYukle() {
  // İstatistikler — sadece admin girişiyse
  if (kullanici && kullanici.rol === 'admin') {
    const istat = await api.getIstatistik();
    if (istat) {
      document.getElementById('stat-toplam').textContent = istat.toplam;
      document.getElementById('stat-aktif').textContent  = istat.aktif;
    }
  } else {
    // Genel ilan sayısını göster
    const ilanlar = await api.getPortfoyler({ durum: 'Aktif' });
    if (ilanlar) {
      document.getElementById('stat-toplam').textContent = ilanlar.length;
      document.getElementById('stat-aktif').textContent  = ilanlar.length;
    }
  }
  // İlanlar
  await anaGridYukle(aktifAnaKat);
  // Hero vitrin (ilk 1 ilan)
  vitrinYukle();
}

async function anaGridYukle(kat = '') {
  const grid = document.getElementById('ana-grid');
  grid.innerHTML = '<div class="yukleniyor"><div class="spinner"></div>Yükleniyor…</div>';
  const params = { durum: 'Aktif' };
  if (kat) params.kategori = kat;
  const ilanlar = await api.getPortfoyler(params);
  if (!ilanlar) return;
  grid.innerHTML = '';
  if (!ilanlar.length) {
    grid.innerHTML = '<div class="bos-durum"><div class="bos-ikon">🏠</div><h3>İlan bulunamadı</h3><p>Farklı kategori deneyin</p></div>';
    return;
  }
  ilanlar.slice(0,9).forEach(i => grid.appendChild(kartOlustur(i)));
}

async function vitrinYukle() {
  const vit = document.getElementById('hero-vitrin');
  if (!vit) return; // Hero vitrin kaldırıldıysa çalışma
  const ilanlar = await api.getPortfoyler({ durum: 'Aktif' });
  if (!ilanlar || !ilanlar.length) { vit.innerHTML = ''; return; }
  const i = ilanlar[0];
  const foto = (i.resimler && i.resimler.length)
    ? `<img src="${i.resimler[0]}" alt="${i.baslik}" style="width:100%;height:100%;object-fit:cover">`
    : `<div style="font-size:3rem;color:var(--gri-metin);display:flex;align-items:center;justify-content:center;height:100%">🏠</div>`;
  vit.innerHTML = `
    <div class="vitrin-kart" style="position:relative; padding-bottom:2rem;">
      <div class="vitrin-kart-foto">
        ${foto}
        <div class="vitrin-kart-serit">${i.alt_kategori}</div>
      </div>
      <div class="vitrin-kart-bilgi">
        <div class="vitrin-kart-fiyat">${i.fiyat ? i.fiyat+(i.para_birimi && i.para_birimi!=='TL' ? ' '+i.para_birimi : ' TL') : '—'}</div>
        <div class="vitrin-kart-baslik">${i.baslik}</div>
      </div>
      ${ilanlar[1] ? `
      <div class="vitrin-kart-kucuk">
        <div class="vitrin-badge">🏡</div>
        <div>
          <div class="vitrin-kucuk-etiket">Bir diğer ilan</div>
          <div class="vitrin-kucuk-deger">${ilanlar[1].baslik.substring(0,28)}…</div>
        </div>
      </div>` : ''}
    </div>`;
}

function katFiltrele(el, kat) {
  aktifAnaKat = kat;
  document.querySelectorAll('#ana-kat-bant .kat-chip').forEach(c => c.classList.remove('aktif'));
  el.classList.add('aktif');
  anaGridYukle(kat);
}

function heroAra() {
  const q = document.getElementById('hero-q').value;
  sayfaGit('ilanlar');
  setTimeout(() => { document.getElementById('ilan-q').value = q; ilanYukle(); }, 80);
}

// ── İlanlar Sayfası ──────────────────────────────────────────────────────────
let aktifIlanKat = '';

function katFiltrelIlan(el, kat) {
  aktifIlanKat = kat;
  document.querySelectorAll('#ilan-kat-bant .kat-chip').forEach(c => c.classList.remove('aktif'));
  el.classList.add('aktif');
  // Alt kategori doldurulan
  const altSel = document.getElementById('filtre-alt');
  altSel.innerHTML = '<option value="">Alt kategori</option>';
  if (kat && kategoriler[kat]) {
    kategoriler[kat].forEach(a => altSel.innerHTML += `<option value="${a}">${a}</option>`);
  }
  ilanYukle();
}

async function ilanYukle() {
  const q        = document.getElementById('ilan-q')?.value || '';
  const alt      = document.getElementById('filtre-alt')?.value || '';
  const fiyatMin = parseFloat(document.getElementById('gf-fiyat-min')?.value || 0) || 0;
  const fiyatMax = parseFloat(document.getElementById('gf-fiyat-max')?.value || 0) || 0;
  const m2Min    = parseFloat(document.getElementById('gf-m2-min')?.value || 0) || 0;
  const m2Max    = parseFloat(document.getElementById('gf-m2-max')?.value || 0) || 0;
  const oda      = document.getElementById('gf-oda')?.value || '';
  const para     = document.getElementById('gf-para')?.value || '';

  const params = { durum: 'Aktif' };
  if (aktifIlanKat) params.kategori = aktifIlanKat;
  if (alt)          params.alt_kat = alt;
  if (q)            params.arama = q;

  const grid = document.getElementById('ilan-grid');
  grid.innerHTML = '<div class="yukleniyor"><div class="spinner"></div>Yükleniyor…</div>';
  let ilanlar = await api.getPortfoyler(params);
  if (!ilanlar) return;

  // İstemci tarafı gelişmiş filtreler
  const herhangiAktif = fiyatMin||fiyatMax||m2Min||m2Max||oda||para;
  if (herhangiAktif) {
    ilanlar = ilanlar.filter(i => {
      const fiyatSayi = parseFloat((i.fiyat||'').replace(/[^\d.]/g,'')) || 0;
      const m2 = parseFloat((i.alanlar?.net_m2 || i.alanlar?.alan_m2 || '0')) || 0;
      if (fiyatMin > 0 && fiyatSayi > 0 && fiyatSayi < fiyatMin) return false;
      if (fiyatMax > 0 && fiyatSayi > 0 && fiyatSayi > fiyatMax) return false;
      if (m2Min > 0 && m2 > 0 && m2 < m2Min) return false;
      if (m2Max > 0 && m2 > 0 && m2 > m2Max) return false;
      if (oda && i.alanlar?.oda_sayisi) {
        const ilanOda = i.alanlar.oda_sayisi;
        if (oda === '5+') { if (!['5+1','5+2','6+','6+1','6+2'].some(o => ilanOda.startsWith('5')||ilanOda.startsWith('6'))) return false; }
        else if (ilanOda !== oda) return false;
      }
      if (para && i.para_birimi && i.para_birimi !== para) return false;
      return true;
    });
  }

  // Sıfırla butonunu göster/gizle
  const sfBtn = document.getElementById('filtre-sifirla-btn');
  if (sfBtn) sfBtn.style.display = (q||alt||aktifIlanKat||herhangiAktif) ? '' : 'none';

  document.getElementById('ilan-sayi').textContent = ilanlar.length + ' ilan';
  grid.innerHTML = '';

  if (!ilanlar.length) {
    grid.innerHTML = '<div class="bos-durum"><div class="bos-ikon">🔍</div><h3>İlan bulunamadı</h3><p>Filtreleri genişletin veya sıfırlayın</p></div>';
    return;
  }
  ilanlar.forEach(i => grid.appendChild(kartOlustur(i)));

  // Harita görünümündeyse haritayı da güncelle
  if (aktifGorunum === 'harita') haritaYukle();
}

function aramaBekle() { clearTimeout(aramaTO); aramaTO = setTimeout(ilanYukle, 380); }

// ── İlan Detay ───────────────────────────────────────────────────────────────
async function detayGoster(ilan) {
  const kont = document.getElementById('detay-ic');
  kont.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  const d = await api.getPortfoy(ilan.id);
  if (!d) return;
  const isAdmin = kullanici && kullanici.rol === 'admin';
  const yetkiliKullanici = kullanici && (kullanici.rol === 'admin' || kullanici.onay === 1 || kullanici.onayli === 1 || kullanici.onay_durumu === 'onaylandi');
  const resimler = d.resimler || [];

  // Galeri
  const anaFoto = resimler.length
    ? `<img src="${resimler[0]}" id="galeri-ana-img" alt="${d.baslik}">`
    : `<div class="galeri-ana-bos">🏠</div>`;
  const thumbler = resimler.length > 1
    ? resimler.map((r,i) =>
        `<div class="galeri-thumb${i===0?' aktif':''}" onclick="gFotoDegis(this,'${r}')">
          <img src="${r}" loading="lazy">
        </div>`).join('') : '';

  // Teknik alanlar
  const alanlar = d.alanlar || {};
  const teknikHtml = Object.entries(alanlar)
    .filter(([k,v]) => v && k !== 'ozellikler')
    .map(([k,v]) => `<div class="teknik-satir">
      <div class="teknik-etiket">${k.replace(/_/g,' ')}</div>
      <div class="teknik-deger">${v}</div>
    </div>`).join('');

  const gpsLink = d.gps
    ? `<a href="https://maps.google.com/?q=${d.gps}" target="_blank">🗺 Haritada Gör</a>` : '';

  const adminBant = isAdmin ? `
    <div class="admin-arac-bant">
      <span>⚙ Admin</span>
      <button class="btn btn-kirm btn-sm" onclick="ilanDuzenle(${d.id})">✏ Düzenle</button>
      <select class="form-girdi" style="width:auto;padding:.3rem .6rem;font-size:.78rem" onchange="durumDegistir(${d.id},this.value)">
        <option value="">Durum…</option>
        ${['Aktif','Taslak','Pasif','Satıldı','Kiralandı'].map(s=>`<option value="${s}"${d.durum===s?' selected':''}>${s}</option>`).join('')}
      </select>
      <button class="btn btn-ntr btn-sm" onclick="pdfIndir(${d.id})">📄 PDF Broşür</button>
      <button class="btn btn-ntr btn-sm" onclick="fiyatAnaliziGoster(${d.id})">📊 Fiyat Analizi</button>
      <button class="btn btn-hat btn-sm" onclick="if(confirm('Silinsin mi?'))ilanSilDetay(${d.id})">🗑 Sil</button>
    </div>
    <div id="fiyat-analiz-kutu" style="display:none;margin-bottom:1.25rem"></div>` : '';

  // Site iletişim + admin profil resmi
  const [ayarlar, adminBilgi] = await Promise.all([
    api.getAyarlar().then(r => r || {}),
    TOKEN ? api.getKullaniciBen().catch(() => null) : Promise.resolve(null)
  ]);
  const adminProfilResmi = adminBilgi?.profil_resmi || window._profilResmi || '';
  // SEO meta etiketlerini güncelle
  seoGuncelle({
    baslik: d.baslik,
    aciklama: d.aciklama || (d.fiyat ? d.fiyat + ' ' + (d.para_birimi||'TL') + ' — ' + [d.mahalle,d.ilce].filter(Boolean).join(', ') : ''),
    resim: (d.resimler && d.resimler[0]) || '',
    url: window.location.origin + '/?ilan=' + d.id,
    tip: 'product',
    fiyat: d.fiyat || '',
    konum: [d.mahalle, d.ilce].filter(Boolean).join(', ')
  });

  kont.innerHTML = `
    ${adminBant}
    <div class="detay-layout">
      <div>
        <div class="galeri-ana">${anaFoto}</div>
        ${thumbler ? `<div class="galeri-thumbler">${thumbler}</div>` : ''}

        <div style="margin-top:1.5rem">
          <div class="detay-kategori-serit">
            <span class="detay-etiket de-ana">${d.ana_kategori}</span>
            <span class="detay-etiket de-alt">${d.alt_kategori}</span>
            ${d.ilan_tipi ? `<span class="detay-etiket de-tip">${d.ilan_tipi}</span>` : ''}
          </div>
          <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:.75rem;flex-wrap:wrap">
            <h1 class="detay-baslik" style="margin-bottom:0">${d.baslik}</h1>
            <button onclick="favToggle(${d.id},'${d.baslik.replace(/'/g,"\'")}',this)"
              style="flex-shrink:0;padding:.4rem .85rem;border-radius:6px;border:1.5px solid var(--kumtasi);background:var(--krem);cursor:pointer;font-size:.8rem;font-weight:600;transition:.15s;white-space:nowrap"
              id="detay-fav-btn">
              ${favKontrol(d.id) ? '❤ Favoride' : '♡ Favoriye Ekle'}
            </button>
          </div>
          <div class="detay-fiyat" style="margin-top:.5rem">${
            d.fiyat
              ? d.fiyat.toString().trim() + ' ' + (d.para_birimi || 'TL').trim()
              : 'Fiyat için arayın'
          }</div>
          <div class="detay-konum">
            📍 ${[d.mahalle, d.ilce, d.il].filter(Boolean).join(' / ')}
          </div>
          ${d.aciklama ? `
          <div class="detay-bolum">
            <div class="detay-bolum-baslik">Açıklama</div>
            <p class="aciklama-metin">${d.aciklama}</p>
          </div>` : ''}

          <!-- Paylaşım barı -->
          <div class="paylasim-bar">
            <button class="paylasim-btn pb-wa" onclick="ilanPaylas('wa',${d.id},'${d.baslik.replace(/'/g,"\'")}','${d.fiyat||''}')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.374 0 0 5.373 0 12c0 2.126.556 4.122 1.523 5.855L.057 24l6.305-1.538A11.955 11.955 0 0 0 12 24c6.626 0 12-5.373 12-12S18.626 0 12 0zm0 22c-1.885 0-3.65-.51-5.17-1.402l-.371-.22-3.843.937.977-3.75-.242-.385A9.946 9.946 0 0 1 2 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z"/></svg>
              WhatsApp
            </button>
            <button class="paylasim-btn pb-fb" onclick="ilanPaylas('fb',${d.id},'${d.baslik.replace(/'/g,"\'")}','${d.fiyat||''}')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
              Facebook
            </button>
            <button class="paylasim-btn pb-tw" onclick="ilanPaylas('tw',${d.id},'${d.baslik.replace(/'/g,"\'")}','${d.fiyat||''}')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.748l7.73-8.835L1.254 2.25H8.08l4.26 5.633zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
              X
            </button>
            <button class="paylasim-btn pb-kop" onclick="ilanPaylas('kop',${d.id},'${d.baslik.replace(/'/g,"\'")}','${d.fiyat||''}')">
              🔗 Linki Kopyala
            </button>
          </div>

          ${alanlar.ozellikler ? `
          <div class="detay-bolum">
            <div class="detay-bolum-baslik">Değer Katan Özellikler</div>
            <div class="ozellik-listesi">
              ${alanlar.ozellikler.split(/[·,\n]/).map(o=>o.trim()).filter(Boolean).map(o=>`<span class="ozellik-chip">${o}</span>`).join('')}
            </div>
          </div>` : ''}

          ${teknikHtml ? `
          <div class="detay-bolum">
            <div class="detay-bolum-baslik">Teknik Bilgiler</div>
            <div class="teknik-grid">${teknikHtml}</div>
          </div>` : ''}

          ${d.gps ? `
          <div class="detay-bolum">
            <div class="detay-bolum-baslik">🗺 Konum</div>
            <div style="border-radius:var(--r-sm);overflow:hidden;border:1px solid var(--kumtasi);height:240px">
              <iframe src="https://maps.google.com/maps?q=${d.gps}&z=15&output=embed"
                width="100%" height="240" style="border:none;display:block"
                loading="lazy" allowfullscreen title="Konum"></iframe>
            </div>
            <a href="https://maps.google.com/?q=${d.gps}" target="_blank" rel="noopener"
               style="display:inline-flex;align-items:center;gap:.3rem;font-size:.78rem;color:var(--kiremit);margin-top:.5rem;font-weight:600">
              🗺 Google Maps'te Büyük Gör →
            </a>
          </div>` : ''}

          ${isAdmin && d.saha_notu ? `
          <div class="detay-bolum" style="border-left:3px solid var(--kiremit)">
            <div class="detay-bolum-baslik">Saha Notu (Admin)</div>
            <p class="aciklama-metin" style="font-size:.88rem">${d.saha_notu}</p>
          </div>` : ''}
        </div>
      </div>

      <div class="detay-panel">
        <div class="panel-kart">
          <h3>Bilgi Talep Edin</h3>
          <p>Bu mülk hakkında sizi bilgilendirelim</p>
          <button class="btn btn-kirm btn-blok btn-lg" onclick="iletisimAc(${d.id})">
            📬 İletişime Geçin
          </button>
          <div class="panel-iletisim-satirlar" data-tip="site">
            ${ayarlar.telefon ? `<div class="panel-iletisim-satir">📞 <strong>${ayarlar.telefon}</strong></div>` : ''}
            ${ayarlar.email   ? `<div class="panel-iletisim-satir">✉️ ${ayarlar.email}</div>` : ''}
          </div>
        </div>

        ${(d.musteri_ad && (isAdmin || yetkiliKullanici || d.sahip_goster)) ? `
        <div class="panel-kart" style="margin-top:1rem;border-top:3px solid var(--kiremit)">
          <div style="font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--gri-metin);margin-bottom:.85rem;display:flex;align-items:center;justify-content:space-between">
            <span>${isAdmin ? '👤 Mal Sahibi' : '🏡 Portföy Sahibi'}</span>
            ${!isAdmin && d.sahip_goster ? '<span style="font-size:.65rem;background:var(--zeytun-a);color:var(--zeytun);padding:.1rem .4rem;border-radius:4px">✓ Onaylı Bilgi</span>' : ''}
            ${isAdmin && !d.sahip_goster ? '<span style="font-size:.65rem;background:#FEF3C7;color:#92400E;padding:.1rem .4rem;border-radius:4px">🔒 Gizli</span>' : ''}
          </div>
          <div style="display:flex;align-items:center;gap:.85rem;margin-bottom:.85rem">
            <div id="detay-sahip-avatar" style="width:56px;height:56px;border-radius:50%;overflow:hidden;background:var(--kumtasi);border:2.5px solid var(--kiremit-a);flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:1.4rem;filter:saturate(.9)">
              ${adminProfilResmi
                ? `<img src="${adminProfilResmi}" style="width:100%;height:100%;object-fit:cover;border-radius:50%">`
                : '🏠'}
            </div>
            <div>
              <div style="font-weight:700;font-size:.95rem;color:var(--toprak)">${d.musteri_ad}</div>
              ${d.musteri_iliski ? `<div style="font-size:.72rem;color:var(--gri-metin);margin-top:.1rem">${d.musteri_iliski}</div>` : ''}
              <div style="font-size:.72rem;color:var(--kiremit);font-weight:600;margin-top:.1rem">Portföy Gayrimenkul</div>
            </div>
          </div>
          <div class="panel-iletisim-satirlar">
            ${d.musteri_tel  ? `<div class="panel-iletisim-satir">📞 <strong>${d.musteri_tel}</strong></div>` : ''}
            ${d.musteri_mail ? `<div class="panel-iletisim-satir">✉️ ${d.musteri_mail}</div>` : ''}
            ${isAdmin && d.musteri_adres ? `<div class="panel-iletisim-satir">📍 ${d.musteri_adres}</div>` : ''}
          </div>
          ${isAdmin && d.musteri_not ? `
          <div style="margin-top:.75rem;padding:.6rem .75rem;background:var(--krem);border-radius:6px;border-left:3px solid var(--kiremit)">
            <div style="font-size:.68rem;font-weight:700;color:var(--gri-metin);margin-bottom:.25rem">İÇ NOT</div>
            <div style="font-size:.82rem;color:var(--toprak)">${d.musteri_not}</div>
          </div>` : ''}
        </div>` : ''}
      </div>
    </div>`;
}

// Detay sayfasında portföy sahibinin profil resmini yükle
async function detaySahipResmiYukle(pid) {
  if (!kullanici) return;
  try {
    const r = await api.getSahipProfil(pid);
    if (r && r.profil_resmi) {
      const avatar = document.getElementById('detay-sahip-avatar');
      if (avatar) avatar.innerHTML = `<img src="${r.profil_resmi}" style="width:100%;height:100%;object-fit:cover">`;
    }
  } catch(e) {}
}

function gFotoDegis(el, url) {
  document.querySelectorAll('.galeri-thumb').forEach(t => t.classList.remove('aktif'));
  el.classList.add('aktif');
  const img = document.getElementById('galeri-ana-img');
  if (img) img.src = url;
}

function iletisimAc(pid) {
  document.getElementById('istek-pid').value = pid;
  ['istek-ad','istek-tel','istek-mail','istek-mesaj'].forEach(id => {
    const el = document.getElementById(id); if (el) el.value = '';
  });
  document.getElementById('iletisim-modal').style.display = 'flex';
}

async function istekGonder() {
  const ad = document.getElementById('istek-ad').value;
  if (!ad) { bildirim('Ad soyad gerekli', 'hata'); return; }
  const d = await api.iletisim({
      ad_soyad:   ad,
      telefon:    document.getElementById('istek-tel').value,
      email:      document.getElementById('istek-mail').value,
      mesaj:      document.getElementById('istek-mesaj').value,
      portfoy_id: parseInt(document.getElementById('istek-pid').value)||null,
    });
  if (d) { bildirim('Mesajınız iletildi, teşekkürler!', 'basari'); document.getElementById('iletisim-modal').style.display = 'none'; }
}

// ── Admin Portföy Modal ───────────────────────────────────────────────────────
function modalAc(baslik = 'Yeni Portföy') {
  duzenleId = null; aktifPid = null; mevcutResimler = [];
  document.getElementById('modal-baslik').textContent = baslik;
  document.getElementById('modal-kaydet').textContent = '💾 Kaydet';
  const ids = ['f-baslik','f-fiyat','f-gps','f-aciklama','f-saha','f-m-ad','f-m-tel','f-m-mail'];
  ids.forEach(id => { const e = document.getElementById(id); if (e) e.value = ''; });
  document.getElementById('f-il').value = 'Muğla';
  document.getElementById('f-ilce').value = 'Fethiye';
  document.getElementById('f-mahalle').value = '';
  document.getElementById('f-ana').value = '';
  document.getElementById('f-alt').innerHTML = '<option value="">Önce ana</option>';
  document.getElementById('f-tip').innerHTML = '<option value="">Seçin…</option>';
  document.getElementById('f-durum').value = 'Taslak';
  document.getElementById('f-para').value = 'TL';
  document.getElementById('dinamik-kont').innerHTML = '';
  document.getElementById('resim-bolum').style.display = 'none';
  resimGridGuncelle();
  document.getElementById('portfoy-modal').style.display = 'flex';
}

function modalKapat() { document.getElementById('portfoy-modal').style.display = 'none'; }

async function ilanDuzenle(id) {
  const d = await api.getPortfoy(id);
  if (!d) return;
  duzenleId = id; aktifPid = id; mevcutResimler = d.resimler || [];
  document.getElementById('modal-baslik').textContent = 'Portföy Düzenle';
  document.getElementById('modal-kaydet').textContent = '💾 Güncelle';

  // Kategori
  document.getElementById('f-ana').value = d.ana_kategori || '';
  anaKatDegisti();
  await new Promise(r => setTimeout(r, 60));
  document.getElementById('f-alt').value = d.alt_kategori || '';
  await altKatDegisti();
  await new Promise(r => setTimeout(r, 120));
  document.getElementById('f-tip').value = d.ilan_tipi || '';

  // Temel
  document.getElementById('f-baslik').value  = d.baslik || '';
  document.getElementById('f-fiyat').value   = d.fiyat || '';
  document.getElementById('f-para').value    = d.para_birimi || 'TL';
  document.getElementById('f-il').value      = d.il || 'Muğla';
  document.getElementById('f-ilce').value    = d.ilce || 'Fethiye';
  document.getElementById('f-mahalle').value = d.mahalle || '';
  document.getElementById('f-gps').value     = d.gps || '';
  document.getElementById('f-aciklama').value= d.aciklama || '';
  document.getElementById('f-saha').value    = d.saha_notu || '';
  document.getElementById('f-m-ad').value     = d.musteri_ad || '';
  document.getElementById('f-m-tel').value    = d.musteri_tel || '';
  document.getElementById('f-m-mail').value   = d.musteri_mail || '';
  const tcEl = document.getElementById('f-m-tc');      if (tcEl) tcEl.value = d.musteri_tc || '';
  const adrEl = document.getElementById('f-m-adres');  if (adrEl) adrEl.value = d.musteri_adres || '';
  const notEl = document.getElementById('f-m-not');    if (notEl) notEl.value = d.musteri_not || '';
  const ilEl = document.getElementById('f-m-iliski');  if (ilEl) ilEl.value = d.musteri_iliski || '';
  const spEl = document.getElementById('f-sahip-goster'); if (spEl) spEl.checked = !!d.sahip_goster;
  document.getElementById('f-durum').value   = d.durum || 'Taslak';

  // Dinamik
  if (d.alanlar) {
    await new Promise(r => setTimeout(r, 80));
    Object.entries(d.alanlar).forEach(([k,v]) => {
      const el = document.getElementById('da-' + k);
      if (el) { el.value = v; el.classList.remove('eksik'); }
    });
  }

  // Resimler
  document.getElementById('resim-bolum').style.display = '';
  resimGridGuncelle();
  document.getElementById('portfoy-modal').style.display = 'flex';
}

async function portfoyKaydet() {
  const btn = document.getElementById('modal-kaydet');
  const ana = document.getElementById('f-ana').value;
  const alt = document.getElementById('f-alt').value;
  const baslik = document.getElementById('f-baslik').value;
  if (!ana || !alt || !baslik) { bildirim('Kategori ve başlık zorunlu', 'hata'); return; }
  btn.disabled = true; btn.textContent = '⏳…';

  const veri = {
    baslik, ana_kategori: ana, alt_kategori: alt,
    ilan_tipi:    document.getElementById('f-tip').value,
    il:           document.getElementById('f-il').value,
    ilce:         document.getElementById('f-ilce').value,
    mahalle:      document.getElementById('f-mahalle').value,
    fiyat:        document.getElementById('f-fiyat').value,
    para_birimi:  document.getElementById('f-para').value,
    aciklama:     document.getElementById('f-aciklama').value,
    saha_notu:    document.getElementById('f-saha').value,
    gps:          document.getElementById('f-gps').value,
    durum:        document.getElementById('f-durum').value,
    alanlar:      dinamikOku(),
    musteri_ad:     document.getElementById('f-m-ad')?.value      || '',
    musteri_tel:    document.getElementById('f-m-tel')?.value     || '',
    musteri_mail:   document.getElementById('f-m-mail')?.value    || '',
    musteri_adres:  document.getElementById('f-m-adres')?.value   || '',
    musteri_iliski: document.getElementById('f-m-iliski')?.value  || '',
    musteri_not:    document.getElementById('f-m-not')?.value     || '',
    musteri_tc:     document.getElementById('f-m-tc')?.value      || '',
    sahip_goster:   document.getElementById('f-sahip-goster')?.checked ? 1 : 0,
  };

  let sonuc;
  if (duzenleId) {
    sonuc = await api.update('portfoyler', duzenleId, veri);
  } else {
    sonuc = await api.save('portfoyler', veri);
    if (sonuc?.id) { aktifPid = sonuc.id; duzenleId = sonuc.id; }
  }

  btn.disabled = false; btn.textContent = '💾 Güncelle';
  if (sonuc) {
    if (duzenleId && !sonuc.id) {
      // Güncelleme — listeye dön
      bildirim('Portföy güncellendi!', 'basari');
      modalKapat();
      adminSayfa('portfoyler');
    } else {
      // Yeni kayıt — modal'da kal, resim bölümünü aç
      bildirim('Portföy oluşturuldu! Şimdi fotoğraf ekleyebilirsiniz.', 'basari');
      document.getElementById('modal-baslik').textContent = 'Fotoğraf Ekle';
      document.getElementById('resim-bolum').style.display = '';
      document.getElementById('modal-kaydet').textContent = '✓ Tamamla';
      document.getElementById('modal-kaydet').onclick = () => { modalKapat(); adminSayfa('portfoyler'); };
      resimGridGuncelle();
      // Sayfayı resim bölümüne kaydır
      setTimeout(() => document.getElementById('resim-bolum').scrollIntoView({ behavior: 'smooth', block: 'center' }), 100);
    }
  }
}

// ── Resim Yükleme ─────────────────────────────────────────────────────────────
async function resimYukle(evt) {
  const pid = duzenleId || aktifPid;
  if (!pid) { bildirim('Önce portföyü kaydedin', 'bilgi'); return; }
  for (const dosya of evt.target.files) {
    const fd = new FormData(); fd.append('dosya', dosya);
    const d = await api.upload('portfoyler', pid, fd, { kind: 'resim' });
    if (d) { mevcutResimler = d.resimler; resimGridGuncelle(); }
  }
}

function resimGridGuncelle() {
  const grid = document.getElementById('resim-grid');
  const pid = duzenleId || aktifPid;

  // Önceki event listener'ları temizle
  grid.innerHTML = '';

  mevcutResimler.forEach((url, idx) => {
    const div = document.createElement('div');
    div.className = 'resim-thumb';
    div.draggable = true;
    div.dataset.url = url;
    div.dataset.idx = idx;
    div.style.cssText = 'position:relative;cursor:grab;';

    const img = document.createElement('img');
    img.src = url;
    img.style.cssText = 'width:100%;height:100%;object-fit:cover;pointer-events:none;border-radius:var(--r-sm);';

    // Kapak rozeti (ilk resim)
    if (idx === 0) {
      const badge = document.createElement('div');
      badge.style.cssText = 'position:absolute;bottom:3px;left:3px;background:var(--kiremit);color:#fff;font-size:.6rem;font-weight:700;padding:.1rem .4rem;border-radius:3px;letter-spacing:.04em;';
      badge.textContent = 'KAPAK';
      div.appendChild(badge);
    }

    const silBtn = document.createElement('button');
    silBtn.className = 'resim-sil-btn';
    silBtn.textContent = '✕';
    silBtn.title = 'Sil';
    silBtn.onclick = (e) => { e.stopPropagation(); resimSil(url, pid); };

    const kapakBtn = document.createElement('button');
    kapakBtn.style.cssText = 'position:absolute;bottom:3px;right:3px;background:rgba(0,0,0,.55);color:#fff;border:none;border-radius:4px;font-size:.62rem;padding:.15rem .4rem;cursor:pointer;display:' + (idx===0?'none':'block');
    kapakBtn.textContent = '⭐ Kapak';
    kapakBtn.title = 'Kapak yap';
    kapakBtn.onclick = (e) => { e.stopPropagation(); kapakYap(url, pid); };

    div.appendChild(img);
    div.appendChild(silBtn);
    div.appendChild(kapakBtn);

    // Sürükle-bırak
    div.addEventListener('dragstart', e => {
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', idx);
      div.style.opacity = '.4';
    });
    div.addEventListener('dragend', () => { div.style.opacity = '1'; });
    div.addEventListener('dragover', e => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; div.style.outline = '2px solid var(--kiremit)'; });
    div.addEventListener('dragleave', () => { div.style.outline = ''; });
    div.addEventListener('drop', e => {
      e.preventDefault();
      div.style.outline = '';
      const fromIdx = parseInt(e.dataTransfer.getData('text/plain'));
      const toIdx = idx;
      if (fromIdx === toIdx) return;
      const item = mevcutResimler.splice(fromIdx, 1)[0];
      mevcutResimler.splice(toIdx, 0, item);
      resimGridGuncelle();
      resimSiralaKaydet(pid);
    });

    grid.appendChild(div);
  });

  // Ekle butonu
  const label = document.createElement('label');
  label.className = 'resim-ekle-btn';
  label.style.cursor = 'pointer';
  const span1 = document.createElement('span'); span1.textContent = '📷';
  const span2 = document.createElement('span'); span2.textContent = 'Ekle';
  const inp = document.createElement('input');
  inp.type = 'file'; inp.id = 'resim-input'; inp.accept = 'image/*'; inp.multiple = true;
  inp.style.display = 'none';
  inp.onchange = resimYukle;
  label.appendChild(span1); label.appendChild(span2); label.appendChild(inp);
  grid.appendChild(label);

  // Sıralama ipucu
  if (mevcutResimler.length > 1) {
    const hint = document.getElementById('resim-siralama-hint');
    if (hint) hint.style.display = '';
  }
}

async function resimSiralaKaydet(pid) {
  await api.update('portfoyler', pid, { resimler: mevcutResimler }, { action: 'resim-sirala' });
}

async function kapakYap(url, pid) {
  const d = await api.update('portfoyler', pid, {}, { action: 'resim-kapak', query: { url } });
  if (d) { mevcutResimler = d.resimler; resimGridGuncelle(); bildirim('Kapak fotoğrafı güncellendi', 'basari'); }
}

async function resimSil(url, pid) {
  if (!confirm('Fotoğraf silinsin mi?')) return;
  const d = await api.delete('portfoyler', pid, { action: 'resim', query: { url } });
  if (d) { mevcutResimler = d.resimler; resimGridGuncelle(); }
}

// ── Admin Sayfaları ───────────────────────────────────────────────────────────
let _aktifAdminSayfa = '';

function adminSayfa(sayfa) {
  _aktifAdminSayfa = sayfa;
  document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('aktif'));
  const harita = { portfoyler:0, yeni:1, belge:2, bannerlar:3, blog:4, istekler:5, kullanicilar:6, ayarlar:7, hesabim:8, menuler:9, sayfalar:10, widgetler:11, tema:12, sablonlar:13, wizard:14 };
  const items = document.querySelectorAll('.sidebar-item');
  if (items[harita[sayfa]]) items[harita[sayfa]].classList.add('aktif');
  const ic = document.getElementById('admin-ic');
  if (sayfa && sayfa.startsWith && sayfa.startsWith('sistem-')) {
    const alt = sayfa.slice('sistem-'.length);
    const fn = window.sistemSayfaAc;
    if (typeof fn === 'function' && fn(alt)) return;
    if (ic) ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div>Yükleniyor…</div>';
    return;
  }
  if (sayfa === 'portfoyler')  adminPortfoyler();
  else if (sayfa === 'yeni')   { modalAc(); }
  else if (sayfa === 'belge')  adminBelge();
  else if (sayfa === 'bannerlar') adminBannerlar();
  else if (sayfa === 'blog') adminBlog();
  else if (sayfa === 'istekler') adminIstekler();
  else if (sayfa === 'kullanicilar') adminKullanicilar();
  else if (sayfa === 'ayarlar') adminAyarlar();
  else if (sayfa === 'hesabim') adminHesabim();
  else if (sayfa === 'menuler') adminMenuler();
  else if (sayfa === 'sayfalar') adminSayfalar();
  else if (sayfa === 'widgetler') adminWidgetler();
  else if (sayfa === 'tema') adminTema();
  else if (sayfa === 'sablonlar') adminSablonlar();
  else if (sayfa === 'wizard') adminWizard();
  else if (sayfa === 'marketplace') adminMarketplace();
  else if (sayfa === 'saas') adminSaaS();
}

async function adminPortfoyler() {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  const [istat, ilanlar] = await Promise.all([api.getIstatistik(), api.getPortfoyler({ durum: '' })]);
  let html = `<div class="admin-baslik">Portföyler
    <button class="btn btn-kirm" onclick="adminSayfa('yeni')">+ Yeni Portföy</button>
  </div>`;
  if (istat) {
    html += `<div class="stat-grid">
      <div class="stat-kart"><div class="stat-sayi">${istat.toplam}</div><div class="stat-etiket">Toplam Portföy</div></div>
      <div class="stat-kart k"><div class="stat-sayi">${istat.aktif}</div><div class="stat-etiket">Aktif / Yayında</div></div>
      <div class="stat-kart"><div class="stat-sayi" style="color:var(--kiremit-k)">${istat.taslak}</div><div class="stat-etiket">Taslak</div></div>
      <div class="stat-kart z"><div class="stat-sayi">${istat.yeni_istekler}</div><div class="stat-etiket">Yeni İstek</div></div>
    </div>`;
  }
  if (!ilanlar || !ilanlar.length) {
    html += '<div class="bos-durum"><div class="bos-ikon">🏠</div><h3>Henüz portföy yok</h3><p>Yeni portföy ekleyin veya belge yükleyin</p></div>';
  } else {
    html += `<div class="tablo-kont"><table class="tablo">
      <thead><tr><th>Başlık</th><th>Kategori</th><th>Konum</th><th>Fiyat</th><th>Durum</th><th></th></tr></thead>
      <tbody>`;
    ilanlar.forEach(p => {
      html += `<tr>
        <td><strong style="font-size:.9rem">${p.baslik}</strong></td>
        <td><span style="font-size:.78rem; color:var(--gri-metin)">${p.ana_kategori} / ${p.alt_kategori}</span></td>
        <td style="font-size:.82rem; color:var(--gri-metin)">${[p.mahalle,p.ilce].filter(Boolean).join(', ')}</td>
        <td style="font-weight:600; font-size:.9rem; color:var(--toprak)">${p.fiyat||'–'}</td>
        <td><span class="durum-pill dp-${p.durum}">${p.durum}</span></td>
        <td><div class="tablo-eylemler">
          <button class="btn btn-ntr btn-sm" onclick="ilanDuzenle(${p.id})">✏</button>
          <button class="btn btn-sm" style="background:${p.durum==='Aktif'?'#FEF3C7;color:#92400E':'#D1FAE5;color:#065F46'}" onclick="durumDegistir(${p.id},'${p.durum==='Aktif'?'Taslak':'Aktif'}')">${p.durum==='Aktif'?'⏸':'▶'}</button>
          <button class="btn btn-hat btn-sm" onclick="if(confirm('Silinsin mi?'))ilanSilAdmin(${p.id})">🗑</button>
        </div></td>
      </tr>`;
    });
    html += '</tbody></table></div>';
  }
  ic.innerHTML = html;
}

async function durumDegistir(id, durum) {
  const d = await api.update('portfoyler', id, {}, { action: 'durum', query: { durum } });
  if (d) { bildirim('Durum: '+durum, 'basari'); adminPortfoyler(); }
}

async function ilanSilAdmin(id) {
  const d = await api.delete('portfoyler', id);
  if (d) { bildirim('Portföy silindi', 'basari'); adminPortfoyler(); }
}

async function ilanSilDetay(id) {
  const d = await api.delete('portfoyler', id);
  if (d) { bildirim('Portföy silindi', 'basari'); sayfaGit('ilanlar'); }
}

// ── Belge Yükleme ────────────────────────────────────────────────────────────
function adminBelge() {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = `
    <div class="admin-baslik">Belge Yükle</div>
    <p style="color:var(--gri-metin); font-size:.92rem; margin-bottom:1.5rem; max-width:560px">
      Masaüstü programdan oluşturduğunuz portföy belgesini yükleyin.<br>
      Sistem içeriği otomatik analiz ederek formu dolduracak.
    </p>
    <div class="drop-zone" id="drop-zone" onclick="document.getElementById('belge-input').click()">
      <div class="drop-zone-ikon">📄</div>
      <div class="drop-zone-metin">
        <strong>Dosyayı buraya tıklayın veya sürükleyin</strong><br>
        <span style="font-size:.82rem; color:var(--gri-metin)">.docx · .html · .htm</span>
      </div>
      <input type="file" id="belge-input" accept=".docx,.html,.htm" style="display:none" onchange="belgeIsle(event)">
    </div>
    <div id="belge-sonuc" style="margin-top:1.5rem"></div>`;

  const dz = document.getElementById('drop-zone');
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('uzerinde'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('uzerinde'));
  dz.addEventListener('drop', e => {
    e.preventDefault(); dz.classList.remove('uzerinde');
    if (e.dataTransfer.files[0]) belgeIsleDogrudan(e.dataTransfer.files[0]);
  });
}

async function belgeIsle(e) { if (e.target.files[0]) belgeIsleDogrudan(e.target.files[0]); }

async function belgeIsleDogrudan(dosya) {
  const sonuc = document.getElementById('belge-sonuc');
  sonuc.innerHTML = '<div style="display:flex;align-items:center;gap:.75rem;padding:1rem;background:var(--kiremit-a);border-radius:var(--r-sm);color:var(--kiremit)">⏳ Belge analiz ediliyor…</div>';
  const fd = new FormData(); fd.append('dosya', dosya);
  const d = await api.upload('belge', null, fd, { kind: 'parse' });
  if (!d) { sonuc.innerHTML = '<div style="color:var(--danger)">Belge işlenemedi.</div>'; return; }
  const p = d.portfoy;
  const eksikler = ['baslik','fiyat','mahalle','aciklama'].filter(k => !p[k]);
  sonuc.innerHTML = `
    <div style="background:var(--beyaz); border:1px solid var(--kumtasi); border-radius:var(--r); padding:1.25rem; box-shadow:var(--kart-gol)">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1rem; flex-wrap:wrap; gap:.5rem">
        <div>
          <div style="font-family:'Playfair Display',serif; font-size:1.05rem; font-weight:700">✅ Analiz tamamlandı</div>
          <div style="font-size:.8rem; color:var(--gri-metin); margin-top:.15rem">${dosya.name}</div>
        </div>
        ${eksikler.length ? `<span style="color:#D97706; font-size:.82rem; background:#FEF3C7; padding:.2rem .6rem; border-radius:4px">⚠ ${eksikler.length} alan eksik</span>` : '<span style="color:#065F46; font-size:.82rem; background:#D1FAE5; padding:.2rem .6rem; border-radius:4px">✅ Temel alanlar dolu</span>'}
      </div>
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:.5rem .75rem; font-size:.85rem; margin-bottom:1.1rem; padding:.75rem; background:var(--krem); border-radius:var(--r-sm)">
        <div><span style="color:var(--gri-metin)">Başlık: </span><strong>${p.baslik||'—'}</strong></div>
        <div><span style="color:var(--gri-metin)">Fiyat: </span><strong style="color:var(--kiremit)">${p.fiyat||'—'}</strong></div>
        <div><span style="color:var(--gri-metin)">Kategori: </span><strong>${p.ana_kategori} / ${p.alt_kategori}</strong></div>
        <div><span style="color:var(--gri-metin)">Konum: </span><strong>${[p.mahalle,p.ilce,p.il].filter(Boolean).join(' / ')||'—'}</strong></div>
        ${p.musteri_ad ? `<div><span style="color:var(--gri-metin)">Müşteri: </span><strong>${p.musteri_ad}</strong></div>` : ''}
        ${p.musteri_tel ? `<div><span style="color:var(--gri-metin)">Tel: </span><strong>${p.musteri_tel}</strong></div>` : ''}
        <div><span style="color:var(--gri-metin)">Teknik alan: </span><strong>${Object.keys(p.alanlar||{}).length} alan çıkarıldı</strong></div>
      </div>
      <div style="display:flex; gap:.75rem; flex-wrap:wrap">
        <button class="btn btn-ntr" onclick='belgeFormAc(${JSON.stringify(d).replace(/'/g,"&#39;")})'>✏ Formu Aç & Düzenle</button>
        <button class="btn btn-zey" onclick='belgeYayinla(${JSON.stringify(d).replace(/'/g,"&#39;")})'>🚀 Direkt Yayınla</button>
      </div>
    </div>`;
}

async function belgeYayinla(veri) {
  const p = { ...veri.portfoy, durum: 'Aktif', alanlar: veri.portfoy.alanlar || {} };
  const d = await api.save('portfoyler', p);
  if (d) { bildirim('Portföy yayınlandı! #' + d.id, 'basari'); adminSayfa('portfoyler'); }
}

async function belgeFormAc(veri) {
  const p = veri.portfoy;
  modalAc('Belgeden Düzenle');
  await new Promise(r => setTimeout(r, 80));
  document.getElementById('f-ana').value = p.ana_kategori || '';
  anaKatDegisti();
  await new Promise(r => setTimeout(r, 60));
  document.getElementById('f-alt').value = p.alt_kategori || '';
  await altKatDegisti();
  await new Promise(r => setTimeout(r, 160));
  document.getElementById('f-baslik').value   = p.baslik || '';
  document.getElementById('f-fiyat').value    = p.fiyat || '';
  document.getElementById('f-il').value       = p.il || 'Muğla';
  document.getElementById('f-ilce').value     = p.ilce || 'Fethiye';
  document.getElementById('f-mahalle').value  = p.mahalle || '';
  document.getElementById('f-gps').value      = p.gps || '';
  document.getElementById('f-aciklama').value = p.aciklama || '';
  document.getElementById('f-saha').value     = p.saha_notu || '';
  document.getElementById('f-m-ad').value     = p.musteri_ad || '';
  document.getElementById('f-m-tel').value    = p.musteri_tel || '';
  document.getElementById('f-m-mail').value   = p.musteri_mail || '';
  if (p.alanlar) {
    await new Promise(r => setTimeout(r, 80));
    Object.entries(p.alanlar).forEach(([k,v]) => {
      const el = document.getElementById('da-' + k);
      if (el) { el.value = v; el.classList.remove('eksik'); }
    });
  }
}

// ── Müşteri İstekleri ─────────────────────────────────────────────────────────
async function adminIstekler() {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  const istekler = await api.getIstekler();
  if (!istekler) return;
  let html = '<div class="admin-baslik">Müşteri İstekleri</div>';
  if (!istekler.length) {
    html += '<div class="bos-durum"><div class="bos-ikon">📬</div><h3>Henüz istek yok</h3></div>';
  } else {
    html += `<div class="tablo-kont"><table class="tablo">
      <thead><tr><th>Ad Soyad</th><th>İletişim</th><th>İlan</th><th>Mesaj</th><th>Tarih</th><th>Durum</th></tr></thead><tbody>`;
    istekler.forEach(i => {
      html += `<tr>
        <td><strong>${i.ad_soyad}</strong></td>
        <td style="font-size:.8rem">${i.telefon||''}<br>${i.email||''}</td>
        <td style="font-size:.8rem; max-width:140px">${i.portfoy_baslik||'–'}</td>
        <td style="font-size:.8rem; max-width:180px; color:var(--gri-metin)">${(i.mesaj||'').substring(0,60)}${(i.mesaj||'').length>60?'…':''}</td>
        <td style="font-size:.75rem; color:var(--gri-metin); white-space:nowrap">${(i.olusturma||'').substring(0,10)}</td>
        <td><select class="form-girdi" style="padding:.25rem .5rem;font-size:.78rem;width:auto" onchange="istekDurum(${i.id},this.value)">
          ${['Yeni','İşleniyor','Tamamlandı','Reddedildi'].map(s=>`<option value="${s}"${s===i.durum?' selected':''}>${s}</option>`).join('')}
        </select></td>
      </tr>`;
    });
    html += '</tbody></table></div>';
  }
  ic.innerHTML = html;
}

async function istekDurum(id, durum) {
  try {
    const r = await api.update('istekler', id, {}, { action: 'durum', query: { durum } });
    if (r) { bildirim('Durum güncellendi: ' + durum, 'basari'); adminIstekler(); }
    else bildirim('Durum güncellenemedi', 'hata');
  } catch (e) { bildirim('Hata: ' + e.message, 'hata'); }
}

// ── Kullanıcılar ──────────────────────────────────────────────────────────────
async function adminKullanicilar() {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  const kullanicilar = await api.getKullanicilar();
  if (!kullanicilar) return;
  // Bekleyen onay sayısı
  const bekleyenler = kullanicilar.filter(k => k.id > 1 && !k.onayli);
  let html = `<div class="admin-baslik">Kullanıcılar
    <button class="btn btn-kirm" onclick="kullaniciEkle()">+ Kullanıcı Ekle</button>
  </div>`;

  if (bekleyenler.length > 0) {
    html += `<div style="background:#FEF3C7;border:1px solid #FDE68A;border-radius:var(--r-sm);padding:.75rem 1rem;margin-bottom:1rem;font-size:.88rem;color:#92400E;display:flex;align-items:center;gap:.5rem">
      ⏳ <strong>${bekleyenler.length} kullanıcı</strong> admin onayı bekliyor — onaylanana kadar kısıtlı içeriklere erişemezler.
    </div>`;
  }

  html += `<div class="tablo-kont"><table class="tablo">
    <thead><tr><th>Ad Soyad</th><th>E-posta</th><th>Rol</th><th>Durum</th><th>Kayıt</th><th></th></tr></thead><tbody>`;
  kullanicilar.forEach(k => {
    const onay = k.onayli || k.onay;
    const onayRenk  = onay ? '#065F46' : '#92400E';
    const onayBg    = onay ? '#D1FAE5'  : '#FEF3C7';
    const onayMetin = onay ? '✓ Onaylı' : '⏳ Bekliyor';
    html += `<tr>
      <td>
        <div style="font-weight:600;font-size:.9rem">${k.ad_soyad}</div>
        ${k.profil_resmi ? `<img src="${k.profil_resmi}" style="width:28px;height:28px;border-radius:50%;object-fit:cover;margin-top:.2rem">` : ''}
      </td>
      <td style="font-size:.82rem;color:var(--gri-metin)">${k.email}</td>
      <td><span style="font-size:.75rem;font-weight:700;color:${k.rol==='admin'?'var(--kiremit)':'var(--gri-metin)'}">${k.rol}</span></td>
      <td>
        <span style="display:inline-flex;padding:.18rem .6rem;border-radius:20px;font-size:.72rem;font-weight:600;background:${onayBg};color:${onayRenk}">${onayMetin}</span>
        <div style="margin-top:.3rem;display:flex;gap:.3rem">
          ${k.id > 1 && !onay ? `<button class="btn btn-zey btn-sm" onclick="kullaniciOnayla(${k.id})">✓ Onayla</button>` : ''}
          ${k.id > 1 && onay  ? `<button class="btn btn-ntr btn-sm" onclick="kullaniciOnayKaldir(${k.id})">Onayı Kaldır</button>` : ''}
        </div>
      </td>
      <td style="font-size:.75rem;color:var(--gri-metin)">${(k.olusturma||'').substring(0,10)}</td>
      <td>
        ${k.id > 1 ? `<button class="btn btn-hat btn-sm" onclick="if(confirm('Kullanıcı kalıcı olarak silinsin mi?'))kullaniciSil(${k.id})">🗑</button>` : ''}
      </td>
    </tr>`;
  });
  html += '</tbody></table></div>';
  ic.innerHTML = html;
}

async function kullaniciOnayla(id) {
  const d = await api.update('kullanicilar', id, {}, { action: 'onayla' });
  if (d) { bildirim('Kullanıcı onaylandı ✓', 'basari'); adminKullanicilar(); }
}

async function kullaniciOnayKaldir(id) {
  const d = await api.update('kullanicilar', id, {}, { action: 'onay-kaldir' });
  if (d) { bildirim('Onay kaldırıldı', 'bilgi'); adminKullanicilar(); }
}

async function kullaniciOnayDegis(id, yeniOnay) {
  const r = await api.update('kullanicilar', id, {}, { action: 'onayla' });
  if (r) {
    bildirim(r.mesaj, 'basari');
    adminKullanicilar();
  }
}

function kullaniciEkle() {
  const ad = prompt('Ad Soyad:'); if (!ad) return;
  const email = prompt('E-posta:'); if (!email) return;
  const sifre = prompt('Şifre:'); if (!sifre) return;
  const rol = confirm('Admin yetkisi verilsin mi?') ? 'admin' : 'kullanici';
  api.save('kullanicilar', { ad_soyad:ad, email, sifre, rol })
    .then(d => { if (d) { bildirim('Kullanıcı oluşturuldu', 'basari'); adminKullanicilar(); } });
}

async function kullaniciSil(id) {
  const d = await api.delete('kullanicilar', id);
  if (d) { bildirim('Silindi', 'basari'); adminKullanicilar(); }
}

// kullaniciOnayla ve kullaniciOnayKaldir yukarıda tanımlı

// kullaniciOnayla — yukarıda tanımlı

async function kullaniciReddet(id) {
  if (!confirm('Bu kullanıcıyı reddetmek istediğinizden emin misiniz?')) return;
  const d = await api.update('kullanicilar', id, {}, { action: 'onay-kaldir' });
  if (d) { bildirim('Kullanıcı reddedildi', 'bilgi'); adminKullanicilar(); }
}

// ── Site Ayarları ─────────────────────────────────────────────────────────────
async function adminAyarlar() {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  const ayarlar = await api.getAyarlar() || {};
  seoGuncelle({ baslik: 'Site Ayarları' });
  ic.innerHTML = `
    <div class="admin-baslik">Site Ayarları</div>
    <div style="max-width:580px; display:flex; flex-direction:column; gap:1.25rem;">
      <!-- Logo Yükleme -->
      <div style="background:var(--beyaz); border:1px solid var(--kumtasi); border-radius:var(--r); padding:1.25rem;">
        <div style="font-size:.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--gri-metin); margin-bottom:1rem;">Logo</div>
        <div style="display:flex; align-items:center; gap:1.25rem; flex-wrap:wrap">
          <div id="logo-onizleme" style="width:80px; height:60px; background:var(--krem); border:1.5px dashed var(--kumtasi); border-radius:var(--r-sm); display:flex; align-items:center; justify-content:center; overflow:hidden; flex-shrink:0">
            <span style="font-size:1.5rem; color:var(--gri-metin)">🏠</span>
          </div>
          <div>
            <div style="font-size:.85rem; font-weight:500; margin-bottom:.4rem">Site Logosu</div>
            <div style="font-size:.75rem; color:var(--gri-metin); margin-bottom:.75rem">PNG, JPG veya SVG · Önerilen: beyaz/şeffaf arka plan · Maks. 2MB</div>
            <div style="display:flex; gap:.5rem; flex-wrap:wrap">
              <label class="btn btn-ntr btn-sm" style="cursor:pointer">
                📂 Logo Seç
                <input type="file" id="logo-input" accept="image/png,image/jpeg,image/webp,image/svg+xml" style="display:none" onchange="logoYukle(event)">
              </label>
              <button class="btn btn-sm" style="background:#FEE2E2;color:#991B1B" onclick="logoSil()" id="logo-sil-btn" style="display:none">🗑 Kaldır</button>
            </div>
          </div>
        </div>
      </div>

      <div style="background:var(--beyaz); border:1px solid var(--kumtasi); border-radius:var(--r); padding:1.25rem;">
        <div style="font-size:.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--gri-metin); margin-bottom:1rem;">Genel Bilgiler</div>
        <div class="form-grup"><label class="form-etiket">Site Adı</label>
          <input class="form-girdi" id="ay-site_adi" value="${ayarlar.site_adi||''}"></div>
        <div class="form-grup"><label class="form-etiket">Slogan</label>
          <input class="form-girdi" id="ay-site_slogan" value="${ayarlar.site_slogan||''}"></div>
        <div class="form-ikili">
          <div class="form-grup"><label class="form-etiket">Telefon</label>
            <input class="form-girdi" id="ay-telefon" value="${ayarlar.telefon||''}"></div>
          <div class="form-grup"><label class="form-etiket">E-posta</label>
            <input class="form-girdi" id="ay-email" value="${ayarlar.email||''}"></div>
        </div>
        <div class="form-grup"><label class="form-etiket">Adres</label>
          <input class="form-girdi" id="ay-adres" value="${ayarlar.adres||''}"></div>
      </div>

      <div style="background:var(--beyaz); border:1px solid var(--kumtasi); border-radius:var(--r); padding:1.25rem;">
        <div style="font-size:.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--gri-metin); margin-bottom:.75rem;">Renk Teması</div>
        <div style="display:flex; gap:.6rem; flex-wrap:wrap; align-items:center">
          ${[['','Kiremit (Varsayılan)','#C45C35'],['green','Zeytun Yeşil','#2D7D46'],['navy','Lacivert','#1A3C6B'],['purple','Mor','#6D28D9']].map(([v,n,c]) =>
            `<div style="display:flex;align-items:center;gap:.4rem;cursor:pointer" onclick="temaUygula('${v}',this)">
              <div style="width:28px;height:28px;border-radius:50%;background:${c};border:3px solid ${ayarlar.renk_tema===(v||'kiremit')||(!ayarlar.renk_tema&&!v)?'var(--toprak)':'transparent'};flex-shrink:0" class="tema-renk"></div>
              <span style="font-size:.82rem">${n}</span>
            </div>`).join('')}
        </div>
      </div>

      <div style="background:var(--beyaz); border:1px solid var(--kumtasi); border-radius:var(--r); padding:1.25rem;">
        <div style="font-size:.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--gri-metin); margin-bottom:1rem;">Sosyal Medya & İletişim</div>
        <div class="form-grup">
          <label class="form-etiket">WhatsApp Numarası</label>
          <input class="form-girdi" id="ay-sosyal_wa" value="${ayarlar.sosyal_wa||''}" placeholder="905421234567">
          <div style="font-size:.73rem;color:var(--gri-metin);margin-top:.3rem">
            ✅ Sağ altta yeşil WhatsApp butonu olarak görünür · Başında 90 ile ülke kodu yazın
          </div>
        </div>
        <div class="form-grup">
          <label class="form-etiket">Instagram</label>
          <input class="form-girdi" id="ay-sosyal_ig" value="${ayarlar.sosyal_ig||''}" placeholder="portfoygayrimenkul veya https://instagram.com/...">
        </div>
        <div class="form-grup">
          <label class="form-etiket">Facebook</label>
          <input class="form-girdi" id="ay-sosyal_fb" value="${ayarlar.sosyal_fb||''}" placeholder="https://facebook.com/portfoygayrimenkul">
        </div>
        <div class="form-grup" style="margin-bottom:0">
          <label class="form-etiket">Web Sitesi</label>
          <input class="form-girdi" id="ay-web_sitesi" value="${ayarlar.web_sitesi||'portfoygayrimenkul.com.tr'}">
        </div>
      </div>

      <!-- AI Fiyat Analizi Ayarları -->
      <div style="background:var(--beyaz); border:1px solid var(--kumtasi); border-radius:var(--r); padding:1.25rem;">
        <div style="font-size:.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--gri-metin); margin-bottom:1rem;">🤖 AI Fiyat Analizi</div>
        <p style="font-size:.78rem;color:var(--gri-metin);margin-bottom:1rem">
          İlan detay sayfasında piyasa karşılaştırması ve AI yorumu görmek için API anahtarı ekleyin. Masaüstü programınızdaki Bettafish AI ile aynı sağlayıcıları kullanır.
        </p>
        <div class="form-grup">
          <label class="form-etiket">AI Sağlayıcı</label>
          <select class="form-girdi" id="ay-ai_saglayici">
            <option value="deepseek"${ayarlar.ai_saglayici==='deepseek'?' selected':''}>DeepSeek</option>
            <option value="groq"${ayarlar.ai_saglayici==='groq'?' selected':''}>Groq (Llama 3.3)</option>
            <option value="openai"${ayarlar.ai_saglayici==='openai'?' selected':''}>OpenAI (GPT-4o mini)</option>
          </select>
        </div>
        <div class="form-grup" style="margin-bottom:.75rem">
          <label class="form-etiket">API Anahtarı</label>
          <input class="form-girdi" type="password" id="ay-ai_api_key" value="${ayarlar.ai_api_key||''}" placeholder="sk-...">
        </div>
        <button class="btn btn-ntr btn-sm" onclick="aiAyarlariKaydet()">💾 AI Ayarlarını Kaydet</button>
      </div>

      <!-- Hero Bölümü -->
      <div style="background:var(--beyaz); border:1px solid var(--kumtasi); border-radius:var(--r); padding:1.25rem;">
        <div style="font-size:.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--gri-metin); margin-bottom:1rem;">🏠 Hero Bölümü (Ana Sayfa Üst)</div>
        <p style="font-size:.78rem;color:var(--gri-metin);margin-bottom:1rem">
          Arama kutusu her zaman görünür. Hero pasif yapıldığında sadece başlık ve metinler gizlenir.
        </p>

        <div class="form-grup" style="margin-bottom:.5rem">
          <label style="display:flex;align-items:center;gap:.5rem;cursor:pointer;font-size:.875rem;margin-bottom:.75rem">
            <input type="checkbox" id="ay-hero_aktif" ${ayarlar.hero_aktif !== '0' ? 'checked' : ''}>
            Hero başlık/metin aktif (yayında)
          </label>
        </div>

        <!-- Üst Etiket -->
        <div style="background:var(--krem);border-radius:var(--r-sm);padding:.75rem;margin-bottom:.75rem">
          <div style="font-size:.72rem;font-weight:600;color:var(--gri-metin);margin-bottom:.35rem">Üst Etiket</div>
          <div style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:center">
            <input class="form-girdi" id="ay-hero_ust" value="${ayarlar.hero_ust||''}" placeholder="Fethiye · Muğla · Türkiye" style="flex:2;min-width:140px">
            <input type="number" id="ay-hero_ust_boyut" value="${ayarlar.hero_ust_boyut||''}" placeholder="px" style="width:60px;padding:.45rem;border:1.5px solid var(--kumtasi);border-radius:var(--r-sm);font-size:.82rem">
            <input type="color" id="ay-hero_ust_renk" value="${ayarlar.hero_ust_renk||'#000000'}" style="width:36px;height:34px;border-radius:var(--r-sm);border:1.5px solid var(--kumtasi);cursor:pointer;padding:2px">
          </div>
        </div>

        <!-- Başlık -->
        <div style="background:var(--krem);border-radius:var(--r-sm);padding:.75rem;margin-bottom:.75rem">
          <div style="font-size:.72rem;font-weight:600;color:var(--gri-metin);margin-bottom:.35rem">Başlık</div>
          <div style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:center">
            <input class="form-girdi" id="ay-hero_baslik" value="${ayarlar.hero_baslik||''}" placeholder="Ege'nin en güzel mülklerini keşfedin" style="flex:2;min-width:140px">
            <input type="number" id="ay-hero_baslik_boyut" value="${ayarlar.hero_baslik_boyut||''}" placeholder="px" style="width:60px;padding:.45rem;border:1.5px solid var(--kumtasi);border-radius:var(--r-sm);font-size:.82rem">
            <input type="color" id="ay-hero_baslik_renk" value="${ayarlar.hero_baslik_renk||'#000000'}" style="width:36px;height:34px;border-radius:var(--r-sm);border:1.5px solid var(--kumtasi);cursor:pointer;padding:2px">
          </div>
        </div>

        <!-- Alt Metin -->
        <div style="background:var(--krem);border-radius:var(--r-sm);padding:.75rem;margin-bottom:.75rem">
          <div style="font-size:.72rem;font-weight:600;color:var(--gri-metin);margin-bottom:.35rem">Alt Metin</div>
          <div style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:start">
            <textarea class="form-girdi" id="ay-hero_alt" rows="2" placeholder="Fethiye ve çevresinde..." style="flex:2;min-width:140px">${ayarlar.hero_alt||''}</textarea>
            <div style="display:flex;gap:.5rem;align-items:center;flex-shrink:0">
              <input type="number" id="ay-hero_alt_boyut" value="${ayarlar.hero_alt_boyut||''}" placeholder="px" style="width:60px;padding:.45rem;border:1.5px solid var(--kumtasi);border-radius:var(--r-sm);font-size:.82rem">
              <input type="color" id="ay-hero_alt_renk" value="${ayarlar.hero_alt_renk||'#000000'}" style="width:36px;height:34px;border-radius:var(--r-sm);border:1.5px solid var(--kumtasi);cursor:pointer;padding:2px">
            </div>
          </div>
        </div>

        <div class="form-grup" style="margin-bottom:0">
          <label class="form-etiket">Arka Plan Rengi <span style="font-size:.72rem;color:var(--gri-metin);font-weight:400">(opsiyonel)</span></label>
          <div style="display:flex;align-items:center;gap:.5rem">
            <input type="color" id="ay-hero_arkaplan" value="${ayarlar.hero_arkaplan||'#ffffff'}"
              style="width:44px;height:38px;border-radius:var(--r-sm);border:1.5px solid var(--kumtasi);cursor:pointer;padding:2px"
              oninput="document.getElementById('ay-hero_arkaplan-txt').value=this.value">
            <input class="form-girdi" id="ay-hero_arkaplan-txt" value="${ayarlar.hero_arkaplan||''}"
              oninput="document.getElementById('ay-hero_arkaplan').value=this.value"
              style="flex:1;font-family:monospace;font-size:.85rem" placeholder="#ffffff veya boş">
          </div>
        </div>

        <div class="form-grup" style="margin-bottom:0;margin-top:.75rem">
          <label class="form-etiket" style="margin-bottom:.5rem">Hero Fontu <span style="font-size:.72rem;color:var(--gri-metin);font-weight:400">(tüm hero metinleri)</span></label>
          <input type="hidden" id="ay-hero_font" value="${esc(ayarlar.hero_font||'Playfair Display')}">
          <div id="ay-hero-font-grd" style="display:flex;flex-wrap:wrap;gap:.35rem">
            ${(() => { const sf = ayarlar.hero_font || 'Playfair Display';
              return HERO_FONTS.map(f => `<div onclick="heroFontSec(this)" data-font="${esc(f)}" style="
                cursor:pointer;padding:.35rem .55rem;border-radius:var(--r-sm);
                border:2px solid ${f===sf?'var(--kiremit)':'var(--kumtasi)'};
                background:${f===sf?'rgba(196,92,53,.08)':'transparent'};
                text-align:center;font-family:'${esc(f)}',serif;font-size:.78rem;
                line-height:1.3;transition:.15s;flex:0 0 auto;
                max-width:calc(50% - .35rem)">${esc(f)}
                <div style="font-size:.58rem;opacity:.45;margin-top:1px">Aa Örnek Metin</div>
              </div>`).join('');
            })()}
          </div>
          <div style="display:flex;gap:.75rem;align-items:center;margin-top:.5rem;flex-wrap:wrap">
            <label style="display:inline-flex;align-items:center;gap:.4rem;cursor:pointer;font-size:.82rem">
              <input type="checkbox" id="ay-hero_font_italic" ${ayarlar.hero_font_italic === '1' ? 'checked' : ''}>
              <em>İtalik</em> (eğik yazı)
            </label>
            <label style="display:inline-flex;align-items:center;gap:.4rem;cursor:pointer;font-size:.82rem">
              <input type="checkbox" id="ay-hero_font_bold" ${ayarlar.hero_font_bold === '1' ? 'checked' : ''}>
              <strong>Kalın</strong> (bold)
            </label>
          </div>
        </div>
      </div>

      <!-- Genel Piyasa Özeti -->
      <div style="background:var(--beyaz); border:1px solid var(--kumtasi); border-radius:var(--r); padding:1.25rem;">
        <div style="font-size:.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--gri-metin); margin-bottom:1rem;">📊 Kategori Bazlı m² Fiyat Özeti</div>
        <div id="genel-fiyat-analiz">
          <div class="yukleniyor" style="padding:1rem"><div class="spinner"></div></div>
        </div>
      </div>

      <button class="btn btn-kirm btn-lg" onclick="ayarlariKaydet()">💾 Ayarları Kaydet</button>
    </div>`;
  // Logo önizlemeyi doldur
  if (ayarlar.logo_url) setTimeout(() => logoOnizlemeGuncelle(ayarlar.logo_url), 50);
  seciliTema = ayarlar.renk_tema || '';
  // Genel fiyat analizini yükle (404 sessiz)
  adminFiyatAnaliziGenel().then(html => {
    const kont = document.getElementById('genel-fiyat-analiz');
    if (kont) kont.innerHTML = html;
  }).catch(() => {});
  // Font önizlemesi için fontları önceden yükle
  HERO_FONTS.forEach(f => fontYukle(f));
}

let seciliTema = '';

async function logoYukle(evt) {
  const dosya = evt.target.files[0]; if (!dosya) return;
  if (dosya.size > 2 * 1024 * 1024) { bildirim('Logo max 2MB olabilir', 'hata'); return; }
  const fd = new FormData(); fd.append('dosya', dosya);
  const d = await api.upload('logo', null, fd);
  if (d) {
    bildirim('Logo yüklendi!', 'basari');
    logoOnizlemeGuncelle(d.url);
    // Navbar ve footer logo güncelle
    const navLogo = document.getElementById('nav-logo-img');
    const footerLogo = document.getElementById('footer-logo');
    if (navLogo) { navLogo.src = d.url; navLogo.style.display = 'block'; }
    if (footerLogo) { footerLogo.src = d.url; footerLogo.style.display = 'block'; }
  }
}

async function logoSil() {
  if (!confirm('Logo kaldırılsın mı?')) return;
  const d = await api.delete('logo', null);
  if (d) {
    bildirim('Logo kaldırıldı', 'bilgi');
    logoOnizlemeGuncelle('');
    const navLogo = document.getElementById('nav-logo-img');
    const footerLogo = document.getElementById('footer-logo');
    if (navLogo)   { navLogo.style.display = 'none'; }
    if (footerLogo){ footerLogo.style.display = 'none'; }
  }
}

function logoOnizlemeGuncelle(url) {
  const kont = document.getElementById('logo-onizleme');
  const silBtn = document.getElementById('logo-sil-btn');
  if (!kont) return;
  if (url) {
    kont.innerHTML = `<img src="${url}" style="width:100%;height:100%;object-fit:contain;padding:4px;">`;
    if (silBtn) silBtn.style.display = '';
  } else {
    kont.innerHTML = '<span style="font-size:1.5rem;color:var(--gri-metin)">🏠</span>';
    if (silBtn) silBtn.style.display = 'none';
  }
}
function temaUygula(tema, el) {
  seciliTema = tema;
  document.querySelectorAll('.tema-renk').forEach(r => r.style.borderColor = 'transparent');
  el.querySelector('.tema-renk').style.borderColor = 'var(--toprak)';
  document.body.setAttribute('data-tema', tema);
}

async function adminHesabim() {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';

  // Tek istekle kullanıcı bilgilerini çek
  const ben = await api.getKullaniciBen();
  if (!ben || !ben.giris && !ben.email) {
    ic.innerHTML = '<div class="bos-durum"><div class="bos-ikon">⚠</div><h3>Oturum süresi doldu</h3><p>Lütfen tekrar giriş yapın.</p></div>';
    return;
  }
  window._profilResmi = ben.profil_resmi || '';
  window._benData = ben;

  const profilSrc = ben.profil_resmi
    ? `<img src="${ben.profil_resmi}" style="width:100%;height:100%;object-fit:cover;border-radius:50%">`
    : '🏠';

  ic.innerHTML = `
    <div class="admin-baslik">Hesabım</div>
    <div style="max-width:540px;display:flex;flex-direction:column;gap:1.25rem;">

      <!-- Profil Bilgileri -->
      <div style="background:var(--beyaz);border:1px solid var(--kumtasi);border-radius:var(--r);padding:1.25rem;">
        <div style="font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--gri-metin);margin-bottom:1rem;">Profil Bilgileri</div>

        <!-- Profil Resmi -->
        <div style="display:flex;align-items:center;gap:1.1rem;margin-bottom:1.25rem;padding-bottom:1.25rem;border-bottom:1px solid var(--kumtasi)">
          <div id="profil-avatar-onizleme" style="width:72px;height:72px;border-radius:50%;overflow:hidden;background:var(--kumtasi);border:3px solid var(--kiremit-a);display:flex;align-items:center;justify-content:center;font-size:2rem;flex-shrink:0;">
            ${profilSrc}
          </div>
          <div>
            <div style="font-size:.85rem;font-weight:600;margin-bottom:.3rem;">Profil Fotoğrafı</div>
            <div style="font-size:.75rem;color:var(--gri-metin);margin-bottom:.5rem;">İlan detaylarında danışman olarak görünür. Otomatik kare kırpılır.</div>
            <label style="cursor:pointer">
              <span class="btn btn-ntr btn-sm">📷 Fotoğraf Seç</span>
              <input type="file" id="profil-resim-input" accept="image/jpeg,image/png,image/webp" style="display:none" onchange="profilResmiYukle(event)">
            </label>
            ${ben.profil_resmi ? `<button class="btn btn-sm" style="color:var(--gri-metin);margin-left:.4rem" onclick="profilResmiSil()">✕ Kaldır</button>` : ''}
          </div>
        </div>

        <div class="form-grup">
          <label class="form-etiket z">Ad Soyad</label>
          <input class="form-girdi" id="profil-ad" value="${ben.ad_soyad||''}">
        </div>
        <div class="form-grup">
          <label class="form-etiket z">E-posta</label>
          <input class="form-girdi" id="profil-email" type="email" value="${ben.email||''}">
        </div>
        <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.75rem;">
          <span style="font-size:.78rem;background:var(--zeytun-a);color:var(--zeytun);padding:.2rem .6rem;border-radius:4px;font-weight:600;">${ben.rol}</span>
        </div>
        <button class="btn btn-kirm" onclick="profilKaydet()">💾 Profili Güncelle</button>
      </div>

      <!-- Şifre Değiştir -->
      <div style="background:var(--beyaz);border:1px solid var(--kumtasi);border-radius:var(--r);padding:1.25rem;">
        <div style="font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--gri-metin);margin-bottom:1rem;">🔑 Şifre Değiştir</div>
        <div class="form-grup">
          <label class="form-etiket z">Mevcut Şifre</label>
          <input class="form-girdi" id="sifre-mevcut" type="password" placeholder="••••••••" autocomplete="current-password">
        </div>
        <div class="form-grup">
          <label class="form-etiket z">Yeni Şifre</label>
          <input class="form-girdi" id="sifre-yeni" type="password" placeholder="En az 8 karakter" autocomplete="new-password" oninput="sifreGucGoster(this.value)">
        </div>
        <div id="sifre-guc-bar" style="height:5px;border-radius:3px;background:var(--kumtasi);margin:-4px 0 .75rem;transition:.3s;width:0%"></div>
        <div class="form-grup">
          <label class="form-etiket z">Yeni Şifre (Tekrar)</label>
          <input class="form-girdi" id="sifre-tekrar" type="password" placeholder="••••••••" autocomplete="new-password">
        </div>
        <button class="btn btn-kirm" onclick="sifreDegistir()">🔑 Şifreyi Güncelle</button>
      </div>

      <!-- Güvenlik notu -->
      <div style="background:#FFF8F5;border:1px solid #F2C9BB;border-radius:var(--r);padding:1rem 1.25rem;">
        <div style="font-size:.82rem;color:var(--kiremit-k);font-weight:600;margin-bottom:.35rem;">⚠ Güvenlik Hatırlatıcısı</div>
        <div style="font-size:.8rem;color:var(--gri-metin);line-height:1.7;">
          • Varsayılan şifre kullanıyorsanız mutlaka değiştirin.<br>
          • Şifreniz en az 8 karakter, büyük/küçük harf ve rakam içermeli.<br>
          • Şifreyi kimseyle paylaşmayın.<br>
          • Şifrenizi unutursanız sunucuda <code style="background:var(--krem);padding:.1rem .3rem;border-radius:3px;font-size:.78rem">python sifre_sifirla.py</code> çalıştırın.
        </div>
      </div>
    </div>`;
}

function sifreGucGoster(v) {
  const bar = document.getElementById('sifre-guc-bar');
  if (!bar) return;
  const guc = [v.length >= 8, /[A-Z]/.test(v), /[0-9]/.test(v), /[^A-Za-z0-9]/.test(v)].filter(Boolean).length;
  const renkler = ['var(--kumtasi)','#DC2626','#D97706','#16A34A','#15803D'];
  const genislik = ['0%','25%','50%','75%','100%'];
  bar.style.background = renkler[guc];
  bar.style.width = genislik[guc];
}

async function profilKaydet() {
  const ad = document.getElementById('profil-ad').value.trim();
  const email = document.getElementById('profil-email').value.trim();
  if (!ad || !email) { bildirim('Ad soyad ve e-posta zorunlu', 'hata'); return; }
  const d = await api.update('kullanicilar', null, { ad_soyad: ad, email: email }, { action: 'profil' });
  if (d) {
    bildirim('Profil güncellendi!', 'basari');
    // Navbar'ı güncelle
    document.getElementById('admin-ad').textContent = ad;
    await authGuncelle();
  }
}

async function sifreDegistir() {
  const mevcut = document.getElementById('sifre-mevcut').value;
  const yeni   = document.getElementById('sifre-yeni').value;
  const tekrar = document.getElementById('sifre-tekrar').value;
  if (!mevcut || !yeni || !tekrar) { bildirim('Tüm alanları doldurun', 'hata'); return; }
  if (yeni.length < 8) { bildirim('Yeni şifre en az 8 karakter olmalı', 'hata'); return; }
  if (yeni !== tekrar) { bildirim('Yeni şifreler eşleşmiyor', 'hata'); return; }
  const d = await api.update('kullanicilar', null, { mevcut_sifre: mevcut, yeni_sifre: yeni }, { action: 'sifre' });
  if (d) {
    bildirim('Şifre güncellendi! Tekrar giriş yapmanız gerekiyor.', 'basari');
    ['sifre-mevcut','sifre-yeni','sifre-tekrar'].forEach(id => { document.getElementById(id).value = ''; });
    setTimeout(() => cikisYap(true), 2000);
  }
}

async function ayarlariKaydet() {
  const ayarlar = {};
  ['site_adi','site_slogan','telefon','email','adres','sosyal_wa','sosyal_ig','sosyal_fb','web_sitesi',
   'hero_baslik','hero_alt','hero_ust','hero_arkaplan','hero_font',
   'hero_baslik_boyut','hero_alt_boyut','hero_ust_boyut',
   'hero_baslik_renk','hero_alt_renk','hero_ust_renk'].forEach(k => {
    const el = document.getElementById('ay-' + k); if (el) ayarlar[k] = el.value;
  });
  ['hero_aktif', 'hero_font_italic', 'hero_font_bold'].forEach(k => {
    const el = document.getElementById('ay-' + k);
    if (el) ayarlar[k] = el.checked ? '1' : '0';
  });
  if (seciliTema !== undefined && seciliTema !== null) ayarlar['renk_tema'] = seciliTema;
  const d = await api.update('ayarlar', null, { ayarlar });
  if (d) { bildirim('Ayarlar kaydedildi!', 'basari'); siteAyarlariUygula(); }
}

// ── Site Ayarlarını Uygula ────────────────────────────────────────────────────
function lightenHex(hex, percent = 70) {
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  const m = c => Math.round(c + (255 - c) * percent / 100);
  return `#${m(r).toString(16).padStart(2,'0')}${m(g).toString(16).padStart(2,'0')}${m(b).toString(16).padStart(2,'0')}`;
}

window.heroFontSec = function(el) {
  const font = el.dataset.font;
  document.getElementById('ay-hero_font').value = font;
  document.querySelectorAll('#ay-hero-font-grd > div').forEach(d => {
    d.style.borderColor = 'var(--kumtasi)';
    d.style.background = 'transparent';
  });
  el.style.borderColor = 'var(--kiremit)';
  el.style.background = 'rgba(196,92,53,.08)';
};

async function siteAyarlariUygula() {
  const ay = await api.getAyarlar(); if (!ay) return;
  const setEl = (id, val) => { const e = document.getElementById(id); if (e && val) e.textContent = val; };

  // Temel bilgiler
  setEl('nav-adi',      ay.site_adi);
  setEl('nav-sub',      ay.site_slogan || ay.adres);
  setEl('footer-adi',   ay.site_adi);
  setEl('footer-slogan',ay.site_slogan);
  setEl('footer-adres', ay.adres);
  if (ay.site_adi) document.title = ay.site_adi + ' — Fethiye';
  if (ay.renk_tema) document.body.setAttribute('data-tema', ay.renk_tema);

  // Wizard'dan gelen özel renkleri CSS değişkenlerine uygula
  const root = document.documentElement;
  if (ay.renk_ana) root.style.setProperty('--kiremit', ay.renk_ana);
  if (ay.renk_ana_koy) root.style.setProperty('--kiremit-k', ay.renk_ana_koy);
  else if (ay.renk_ana_koyu) root.style.setProperty('--kiremit-k', ay.renk_ana_koyu);
  if (ay.renk_arka) root.style.setProperty('--krem', ay.renk_arka);
  if (ay.renk_metin) root.style.setProperty('--toprak', ay.renk_metin);
  if (ay.renk_ana) root.style.setProperty('--kiremit-a', lightenHex(ay.renk_ana, 72));

  // Tema ayarlarından font ve stil uygula
  const tm = await api.request('/api/tema').catch(()=>({}));
  // Tema renkleri — tema tablosu öncelikli, ayarlar fallback
  const tmRenk_ana = tm.renk_ana || ay.renk_ana;
  const tmRenk_ana_koy = tm.renk_ana_koy || ay.renk_ana_koy || ay.renk_ana_koyu;
  const tmRenk_arka = tm.renk_arka || ay.renk_arka;
  const tmRenk_metin = tm.renk_metin || ay.renk_metin;
  if (tmRenk_ana) root.style.setProperty('--kiremit', tmRenk_ana);
  if (tmRenk_ana_koy) root.style.setProperty('--kiremit-k', tmRenk_ana_koy);
  if (tmRenk_arka) root.style.setProperty('--krem', tmRenk_arka);
  if (tmRenk_metin) root.style.setProperty('--toprak', tmRenk_metin);
  if (tmRenk_ana) root.style.setProperty('--kiremit-a', lightenHex(tmRenk_ana, 72));
  if (tm.font_baslik) { root.style.setProperty('--font-baslik', tm.font_baslik); fontYukle(tm.font_baslik); }
  if (tm.font_govde) { root.style.setProperty('--font-govde', tm.font_govde); fontYukle(tm.font_govde); }
  if (tm.border_radius) {
    const br = parseInt(tm.border_radius) || 12;
    root.style.setProperty('--r', br + 'px');
    root.style.setProperty('--r-sm', Math.max(4, Math.round(br * 0.66)) + 'px');
  }
  if (tm.dark_mode === '1') document.body.classList.add('dark-mode');
  else document.body.classList.remove('dark-mode');
  if (tm.shadow_kart) root.style.setProperty('--dept-shadow', tm.shadow_kart);

  // Stil seçeneklerini uygula (body üzerine class olarak)
  const bodyStilSiniflari = ['header-sticky','header-fixed','header-default','header-minimal',
    'footer-default','footer-minimal','footer-centered','footer-classic',
    'kart-default','kart-shadow','kart-border','kart-glass',
    'button-default','button-rounded','button-square','button-pill',
    'animasyon-minimize','animasyon-none','animasyon-fade','animasyon-slide'];
  bodyStilSiniflari.forEach(s => document.body.classList.remove(s));
  if (tm.header_stil)  document.body.classList.add('header-' + tm.header_stil);
  if (tm.footer_stil) document.body.classList.add('footer-' + tm.footer_stil);
  if (tm.kart_stil)    document.body.classList.add('kart-' + tm.kart_stil);
  if (tm.button_stil)  document.body.classList.add('button-' + tm.button_stil);
  if (tm.animasyon)    document.body.classList.add('animasyon-' + tm.animasyon);

  // Logo & iletişim & tema data-attr aşağıda uygulanıyor (tekrardan kaçın)

  // İletişim
  const fTel = document.getElementById('footer-tel');
  if (fTel) fTel.innerHTML = ay.telefon ? `<a href="tel:${ay.telefon}" style="color:rgba(255,255,255,.7)">${ay.telefon}</a>` : '–';
  const fMail = document.getElementById('footer-mail');
  if (fMail) fMail.innerHTML = ay.email ? `<a href="mailto:${ay.email}" style="color:rgba(255,255,255,.7)">${ay.email}</a>` : '–';

  // Logo — navbar + footer
  const footerLogo = document.getElementById('footer-logo');
  const navLogoImg  = document.getElementById('nav-logo-img');
  const navLogoEmoji= document.getElementById('nav-logo-emoji');
  const logoUrl = ay.logo_url || tm.logo_url || '';
  if (logoUrl) {
    if (footerLogo) { footerLogo.src = logoUrl; footerLogo.style.display = 'block'; }
    if (navLogoImg) { navLogoImg.src = logoUrl; navLogoImg.style.display = 'block'; }
    if (navLogoEmoji) navLogoEmoji.style.display = 'none';
  } else {
    if (footerLogo) footerLogo.style.display = 'none';
    if (navLogoImg) navLogoImg.style.display = 'none';
    if (navLogoEmoji) navLogoEmoji.style.display = '';
  }

  // Theme palet data attribute
  document.body.setAttribute('data-tema', (ay.renk_tema || tm.template || ''));

  // WhatsApp sabit butonu
  const waBtn = document.getElementById('wa-btn');
  if (waBtn) {
    const wa = ay.sosyal_wa || '';
    if (wa) {
      const numara = wa.replace(/[^0-9]/g, '');
      const mesaj = encodeURIComponent(`Merhaba, ${ay.site_adi || 'Portföy Gayrimenkul'} sitesinden ulaşıyorum.`);
      waBtn.href = `https://wa.me/${numara}?text=${mesaj}`;
      waBtn.style.display = 'flex';
    } else {
      waBtn.style.display = 'none';
    }
  }

  // Sosyal medya - footer bar
  const bar = document.getElementById('footer-sosyal-bar');
  if (bar) {
    bar.innerHTML = '';
    const sosyaller = [
      { key: 'sosyal_wa',  ikon: waIkon(),       renk: '#25D366', prefix: 'https://wa.me/', label: 'WhatsApp' },
      { key: 'sosyal_ig',  ikon: igIkon(),        renk: '#E1306C', prefix: 'https://instagram.com/', label: 'Instagram' },
      { key: 'sosyal_fb',  ikon: fbIkon(),        renk: '#1877F2', prefix: '', label: 'Facebook' },
    ];
    sosyaller.forEach(({ key, ikon, renk, prefix, label }) => {
      let deger = ay[key] || '';
      if (!deger) return;
      if (key === 'sosyal_wa') {
        deger = 'https://wa.me/' + deger.replace(/[^0-9]/g,'') +
                '?text=' + encodeURIComponent('Merhaba, ' + (ay.site_adi||'') + ' sitesinden ulaşıyorum.');
      } else if (key === 'sosyal_ig' && !deger.startsWith('http')) {
        deger = prefix + deger.replace('@','');
      } else if (!deger.startsWith('http')) {
        deger = prefix + deger;
      }
      const a = document.createElement('a');
      a.href = deger; a.target = '_blank'; a.rel = 'noopener'; a.title = label;
      a.style.cssText = `width:32px;height:32px;border-radius:8px;background:${renk};
        color:#fff;display:flex;align-items:center;justify-content:center;
        transition:.15s;flex-shrink:0;`;
      a.onmouseover = () => a.style.opacity = '.8';
      a.onmouseout  = () => a.style.opacity = '1';
      a.innerHTML = ikon;
      bar.appendChild(a);
    });
  }

  // Detay paneli iletişim bilgileri
  document.querySelectorAll('.panel-iletisim-satirlar').forEach(el => {
    if (el.dataset.tip === 'site') {
      el.innerHTML = `
        ${ay.telefon ? `<div class="panel-iletisim-satir">📞 <strong>${ay.telefon}</strong></div>` : ''}
        ${ay.email   ? `<div class="panel-iletisim-satir">✉️ ${ay.email}</div>` : ''}
        ${ay.sosyal_wa ? `<a href="https://wa.me/${(ay.sosyal_wa||'').replace(/[^0-9]/g,'')}" target="_blank"
          style="display:inline-flex;align-items:center;gap:.4rem;margin-top:.4rem;padding:.4rem .9rem;
                 border-radius:6px;background:#25D366;color:#fff;font-size:.82rem;font-weight:600;text-decoration:none;">
          ${waIkon()} WhatsApp'tan Yaz
        </a>` : ''}`;
    }
  });

  // ── Hero Bölümü ──────────────────────────────────────────────────────────
  const heroUst = document.getElementById('hero-ust');
  const heroBaslik = document.getElementById('hero-baslik-metin');
  const heroAlt = document.getElementById('hero-alt-metin');
  if (ay.hero_aktif === '0') {
    if (heroUst) heroUst.style.display = 'none';
    if (heroBaslik) heroBaslik.style.display = 'none';
    if (heroAlt) heroAlt.style.display = 'none';
  } else {
    if (heroUst) { heroUst.style.display = ay.hero_ust ? '' : 'none'; heroUst.textContent = ay.hero_ust || ''; }
    if (heroBaslik) { heroBaslik.style.display = ay.hero_baslik ? '' : 'none'; heroBaslik.textContent = ay.hero_baslik || ''; }
    if (heroAlt) { heroAlt.style.display = ay.hero_alt ? '' : 'none'; heroAlt.textContent = ay.hero_alt || ''; }
  }
  // Arama her zaman görünür
  const heroArama = document.querySelector('.hero-arama');
  if (heroArama) heroArama.style.display = '';
  // Arka plan rengi
  const heroKont = document.querySelector('.hero')?.parentElement;
  if (heroKont) {
    if (ay.hero_arkaplan) heroKont.style.background = ay.hero_arkaplan;
    else heroKont.style.background = '';
  }
  // Hero font
  if (ay.hero_font) {
    fontYukle(ay.hero_font);
    const hf = `'${ay.hero_font}', serif`;
    if (heroUst) heroUst.style.fontFamily = hf;
    if (heroBaslik) heroBaslik.style.fontFamily = hf;
    if (heroAlt) heroAlt.style.fontFamily = hf;
  }
  // Hero italic
  const heroItalic = ay.hero_font_italic === '1' ? 'italic' : '';
  if (heroUst) heroUst.style.fontStyle = heroItalic;
  if (heroBaslik) heroBaslik.style.fontStyle = heroItalic;
  if (heroAlt) heroAlt.style.fontStyle = heroItalic;
  // Hero bold
  const heroBold = ay.hero_font_bold === '1' ? '700' : '';
  if (heroUst) heroUst.style.fontWeight = heroBold;
  if (heroBaslik) heroBaslik.style.fontWeight = heroBold;
  if (heroAlt) heroAlt.style.fontWeight = heroBold;
  // Font boyutları
  if (heroBaslik && ay.hero_baslik_boyut) heroBaslik.style.fontSize = ay.hero_baslik_boyut + 'px';
  if (heroAlt && ay.hero_alt_boyut) heroAlt.style.fontSize = ay.hero_alt_boyut + 'px';
  if (heroUst && ay.hero_ust_boyut) heroUst.style.fontSize = ay.hero_ust_boyut + 'px';
  // Metin renkleri
  if (heroBaslik && ay.hero_baslik_renk) heroBaslik.style.color = ay.hero_baslik_renk;
  if (heroAlt && ay.hero_alt_renk) heroAlt.style.color = ay.hero_alt_renk;
  if (heroUst && ay.hero_ust_renk) heroUst.style.color = ay.hero_ust_renk;
}

function waIkon() {
  return `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.890-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
  </svg>`;
}
function igIkon() {
  return `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
  </svg>`;
}
function fbIkon() {
  return `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
  </svg>`;
}

// ── Başlangıç ────────────────────────────────────────────────────────────────

// ══════════════════════════════════════════════════════════════════
// FAZ 2 — FAVORİ SİSTEMİ
// ══════════════════════════════════════════════════════════════════
function favGetir() {
  try { return JSON.parse(localStorage.getItem('portfoy_favs') || '[]'); } catch { return []; }
}
function favKaydet(liste) {
  localStorage.setItem('portfoy_favs', JSON.stringify(liste));
  favBantGuncelle();
  bannerlariYukle(); // Banner sistemini başlat
}
function favKontrol(id) { return favGetir().some(f => f.id == id); }

function favToggleId(id, baslik, btn) {
  let favlar = favGetir();
  const idx = favlar.findIndex(f => f.id == id);
  if (idx >= 0) {
    favlar.splice(idx, 1);
    if (btn) { btn.textContent = '♡'; btn.classList.remove('aktif'); btn.title = 'Favoriye ekle'; }
    bildirim('Favorilerden çıkarıldı', 'bilgi');
  } else {
    favlar.push({ id, baslik });
    if (btn) { btn.textContent = '❤'; btn.classList.add('aktif'); btn.title = 'Favoriden çıkar'; }
    bildirim('❤ Favorilere eklendi', 'basari');
  }
  favKaydet(favlar);
  // Detay sayfasındaki butonu da güncelle
  const detayBtn = document.getElementById('detay-fav-btn');
  if (detayBtn) {
    const isFav = favKontrol(id);
    detayBtn.textContent = isFav ? '❤ Favoride' : '♡ Favoriye Ekle';
    detayBtn.style.background = isFav ? 'var(--kiremit-a)' : 'var(--krem)';
    detayBtn.style.color = isFav ? 'var(--kiremit)' : '';
  }
}

function favToggle(id, baslik, btn) { favToggleId(id, baslik, btn); }

function favBantGuncelle() {
  const favlar = favGetir();
  const bant = document.getElementById('fav-bant');
  const sayi = document.getElementById('fav-sayi');
  if (!bant) return;
  if (favlar.length > 0) {
    bant.classList.add('gorunur');
    if (sayi) sayi.textContent = favlar.length;
  } else {
    bant.classList.remove('gorunur');
  }
}

function sadeceFavGoster() {
  const favlar = favGetir();
  if (!favlar.length) return;
  sayfaGit('ilanlar');
  setTimeout(async () => {
    const grid = document.getElementById('ilan-grid');
    grid.innerHTML = '<div class="yukleniyor"><div class="spinner"></div>Favoriler yükleniyor…</div>';
    const tumIlanlar = await api.getPortfoyler({ durum: 'Aktif' });
    if (!tumIlanlar) return;
    const favIds = favlar.map(f => f.id);
    const favIlanlar = tumIlanlar.filter(i => favIds.includes(i.id));
    grid.innerHTML = '';
    document.getElementById('ilan-sayi').textContent = favIlanlar.length + ' favori ilan';
    if (!favIlanlar.length) { grid.innerHTML = '<div class="bos-durum"><div class="bos-ikon">❤</div><h3>Favori ilan yok</h3></div>'; return; }
    favIlanlar.forEach(i => grid.appendChild(kartOlustur(i)));
  }, 100);
}

function favSifirla() {
  localStorage.removeItem('portfoy_favs');
  favBantGuncelle();
  bildirim('Favoriler temizlendi', 'bilgi');
}

// ══════════════════════════════════════════════════════════════════
// FAZ 2 — KARŞILAŞTIRMA SİSTEMİ
// ══════════════════════════════════════════════════════════════════
let karsListesi = [];

function karsEkle(id, baslik, fiyat, kategori, btn) {
  if (karsListesi.some(k => k.id == id)) {
    karsListesi = karsListesi.filter(k => k.id != id);
    if (btn) btn.classList.remove('aktif');
    bildirim('Karşılaştırmadan çıkarıldı', 'bilgi');
  } else {
    if (karsListesi.length >= 3) { bildirim('En fazla 3 ilan karşılaştırılabilir', 'hata'); return; }
    karsListesi.push({ id, baslik, fiyat, kategori });
    if (btn) btn.classList.add('aktif');
    bildirim('Karşılaştırmaya eklendi', 'basari');
  }
  karsBantGuncelle();
}

function karsBantGuncelle() {
  const bant = document.getElementById('kars-bant');
  const liste = document.getElementById('kars-listesi');
  if (!bant || !liste) return;
  liste.innerHTML = karsListesi.map(k =>
    `<div class="kars-mini">
      <span>${k.baslik.substring(0,22)}${k.baslik.length>22?'…':''}</span>
      <button class="kars-mini-kapat" onclick="karsKaldir(${k.id})">✕</button>
    </div>`
  ).join('');
  bant.classList.toggle('gorunur', karsListesi.length >= 2);
}

function karsKaldir(id) {
  karsListesi = karsListesi.filter(k => k.id != id);
  // Kartlardaki butonu güncelle
  const btn = document.querySelector(`.kars-btn[data-kars-id="${id}"]`);
  if (btn) btn.classList.remove('aktif');
  karsBantGuncelle();
}

function karsSifirla() {
  karsListesi = [];
  document.querySelectorAll('.kars-btn.aktif').forEach(b => b.classList.remove('aktif'));
  karsBantGuncelle();
}

async function karsGoster() {
  if (karsListesi.length < 2) return;

  // Detay sayfasını karşılaştırma için kullan — sayfaGit('detay') data olmadan çağrılınca
  // detayGoster() tetiklenmiyor, direkt el ile aktif edelim
  document.querySelectorAll('.sayfa').forEach(s => s.classList.remove('aktif'));
  document.querySelectorAll('.nav-link, .mobil-tab-item').forEach(b => b.classList.remove('aktif'));
  document.getElementById('sayfa-detay').classList.add('aktif');
  gecmisSayfa = 'ilanlar';
  window.scrollTo(0, 0);

  const kont = document.getElementById('detay-ic');
  kont.innerHTML = '<div class="yukleniyor"><div class="spinner"></div>İlanlar karşılaştırılıyor…</div>';

  const detaylar = await Promise.all(karsListesi.map(k => api.getPortfoy(k.id)));
  const gecerli = detaylar.filter(Boolean);

  const alanlar_tumu = new Set();
  gecerli.forEach(d => Object.keys(d.alanlar || {}).forEach(k => { if(k !== 'ozellikler') alanlar_tumu.add(k); }));

  const kolTh = gecerli.map(d => `<th style="padding:.75rem 1rem;text-align:left;font-size:.88rem;font-weight:700;color:var(--toprak)">${d.baslik}</th>`).join('');
  const fiyatTr = `<tr style="background:var(--kiremit-a)">
    <td style="padding:.6rem 1rem;font-size:.78rem;font-weight:700;color:var(--gri-metin);text-transform:uppercase;white-space:nowrap">💰 Fiyat</td>
    ${gecerli.map(d => `<td style="padding:.6rem 1rem;font-weight:700;color:var(--kiremit);font-size:1rem">${d.fiyat||'–'} ${d.para_birimi||''}</td>`).join('')}
  </tr>`;
  const kategoriTr = `<tr>
    <td style="padding:.6rem 1rem;font-size:.78rem;font-weight:700;color:var(--gri-metin);text-transform:uppercase">Kategori</td>
    ${gecerli.map(d => `<td style="padding:.6rem 1rem;font-size:.88rem">${d.ana_kategori} / ${d.alt_kategori}</td>`).join('')}
  </tr>`;
  const konumTr = `<tr style="background:var(--krem)">
    <td style="padding:.6rem 1rem;font-size:.78rem;font-weight:700;color:var(--gri-metin);text-transform:uppercase">📍 Konum</td>
    ${gecerli.map(d => `<td style="padding:.6rem 1rem;font-size:.88rem">${[d.mahalle,d.ilce].filter(Boolean).join(' / ')}</td>`).join('')}
  </tr>`;

  const alanSatirlari = [...alanlar_tumu].map((key, idx) => {
    const degerler = gecerli.map(d => (d.alanlar || {})[key] || '–');
    const satir = `<tr${idx%2===0 ? ' style="background:var(--krem)"' : ''}>
      <td style="padding:.55rem 1rem;font-size:.78rem;font-weight:600;color:var(--gri-metin);text-transform:capitalize;white-space:nowrap">${key.replace(/_/g,' ')}</td>
      ${degerler.map(v => `<td style="padding:.55rem 1rem;font-size:.88rem">${v}</td>`).join('')}
    </tr>`;
    return satir;
  }).join('');

  kont.innerHTML = `
    <div class="detay-geri" onclick="geriGit()" style="margin-bottom:1rem">← Geri dön</div>
    <div style="font-family:'Playfair Display',serif;font-size:1.4rem;font-weight:700;margin-bottom:1.25rem">
      ⚖ İlan Karşılaştırma
    </div>
    <div style="overflow-x:auto;border-radius:var(--r);border:1px solid var(--kumtasi);box-shadow:var(--kart-gol)">
      <table style="width:100%;border-collapse:collapse;min-width:500px">
        <thead>
          <tr style="background:var(--toprak)">
            <th style="padding:.75rem 1rem;text-align:left;font-size:.78rem;font-weight:700;color:rgba(255,255,255,.6);text-transform:uppercase;white-space:nowrap">Özellik</th>
            ${kolTh}
          </tr>
        </thead>
        <tbody>
          ${fiyatTr}${kategoriTr}${konumTr}${alanSatirlari}
        </tbody>
      </table>
    </div>
    <div style="display:flex;gap:.75rem;margin-top:1.25rem">
      ${gecerli.map(d => `<button class="btn btn-kirm btn-sm" onclick="haritaIlanAc(${d.id})">→ ${d.baslik.substring(0,20)}…</button>`).join('')}
      <button class="btn btn-ntr btn-sm" onclick="karsSifirla();sayfaGit('ilanlar')">← Listeye Dön</button>
    </div>`;
}

// ══════════════════════════════════════════════════════════════════
// FAZ 2 — GELİŞMİŞ FİLTRE
// ══════════════════════════════════════════════════════════════════
function gelismisFiltreToogle() {
  const panel = document.getElementById('gelismis-filtre');
  const btn   = document.getElementById('gf-toggle-btn');
  const acik  = panel.classList.toggle('acik');
  btn.textContent = acik ? '⚙ Gizle' : '⚙ Filtrele';
  btn.style.background = acik ? 'var(--kiremit-a)' : '';
  btn.style.color = acik ? 'var(--kiremit)' : '';
}

function filtreleriSifirla() {
  ['gf-fiyat-min','gf-fiyat-max','gf-m2-min','gf-m2-max','gf-oda','gf-para','ilan-q','filtre-alt'].forEach(id => {
    const el = document.getElementById(id); if (el) el.value = '';
  });
  aktifIlanKat = '';
  document.querySelectorAll('#ilan-kat-bant .kat-chip').forEach(c => c.classList.remove('aktif'));
  const ilk = document.querySelector('#ilan-kat-bant .kat-chip');
  if (ilk) ilk.classList.add('aktif');
  document.getElementById('filtre-sifirla-btn').style.display = 'none';
  ilanYukle();
}

// ══════════════════════════════════════════════════════════════════
// FAZ 2 — HARITA GÖRÜNÜMÜ (Leaflet.js)
// ══════════════════════════════════════════════════════════════════
let haritaOrnek = null;
let haritaIlanCache = [];

function haritaIlanAc(id) {
  const ilan = haritaIlanCache.find(i => i.id == id);
  if (ilan) sayfaGit('detay', ilan);
  else api.getPortfoy(id).then(d => { if (d) sayfaGit('detay', d); });
}
let haritaKatman = null;
let aktifGorunum = 'grid';

function gorunumDegis(tip) {
  aktifGorunum = tip;
  document.getElementById('gg-grid').classList.toggle('aktif', tip === 'grid');
  document.getElementById('gg-harita').classList.toggle('aktif', tip === 'harita');
  document.getElementById('ilan-grid').style.display = tip === 'grid' ? '' : 'none';
  const haritaKont = document.getElementById('harita-kont');
  haritaKont.classList.toggle('gorunur', tip === 'harita');
  if (tip === 'harita') haritaYukle();
}

async function haritaYukle() {
  const kont = document.getElementById('harita-kont');

  // Leaflet CSS + JS yükle (sadece bir kez)
  if (!document.getElementById('leaflet-css')) {
    const link = document.createElement('link');
    link.id = 'leaflet-css';
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(link);
  }

  if (!window.L) {
    await new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      s.onload = resolve; s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  // Haritayı bir kez oluştur
  if (!haritaOrnek) {
    haritaOrnek = L.map(kont).setView([36.62, 29.12], 11);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors', maxZoom: 18
    }).addTo(haritaOrnek);
    haritaKatman = L.layerGroup().addTo(haritaOrnek);
    // Boyut düzeltmesi (display:none'dan açılınca)
    setTimeout(() => haritaOrnek.invalidateSize(), 100);
  }

  // Mevcut ilanları göster
  haritaKatman.clearLayers();
  const ilanlar = await api.getPortfoyler({ durum: 'Aktif' });
  if (!ilanlar) return;
  haritaIlanCache = ilanlar;

  let ilkKonum = null;
  ilanlar.forEach(i => {
    if (!i.gps) return;
    const [lat, lng] = i.gps.split(',').map(Number);
    if (!lat || !lng || isNaN(lat) || isNaN(lng)) return;

    const ikon = L.divIcon({
      html: `<div style="background:var(--kiremit,#C45C35);color:#fff;padding:3px 7px;border-radius:4px;font-size:11px;font-weight:700;white-space:nowrap;box-shadow:0 2px 6px rgba(0,0,0,.25)">${i.fiyat ? i.fiyat.substring(0,9) : '📍'}</div>`,
      className: '', iconAnchor: [0, 0]
    });

    const marker = L.marker([lat, lng], { icon: ikon }).addTo(haritaKatman);
    const popupId = i.id;
    marker.bindPopup(`
      <div class="harita-popup">
        <div class="harita-popup-baslik">${i.baslik}</div>
        <div class="harita-popup-fiyat">${i.fiyat||'Fiyat sorunuz'} ${i.para_birimi||'TL'}</div>
        <div style="font-size:.78rem;color:#888;margin-bottom:.4rem">📍 ${[i.mahalle,i.ilce].filter(Boolean).join(' / ')}</div>
        <div class="harita-popup-detay" onclick="haritaIlanAc(${popupId})">Detaya git →</div>
      </div>
    `, { maxWidth: 220 });

    if (!ilkKonum) ilkKonum = [lat, lng];
  });

  if (ilkKonum) haritaOrnek.setView(ilkKonum, 12);
  else {
    // GPS'siz ilan uyarısı
    kont.insertAdjacentHTML('beforeend',
      '<div style="position:absolute;bottom:1rem;left:50%;transform:translateX(-50%);background:rgba(45,32,22,.8);color:#fff;padding:.5rem 1rem;border-radius:6px;font-size:.78rem;pointer-events:none">GPS koordinatı olan ilanlar haritada gösterilir</div>');
  }
}

// ══════════════════════════════════════════════════════════════════
// FAZ 2 — İLAN PAYLAŞMA
// ══════════════════════════════════════════════════════════════════
function ilanPaylas(platform, id, baslik, fiyat) {
  const url   = encodeURIComponent(window.location.origin + '/?ilan=' + id);
  const metin = encodeURIComponent(`${baslik}${fiyat ? ' — '+fiyat+' TL' : ''}`);
  const links = {
    wa:  `https://wa.me/?text=${metin}%20${url}`,
    fb:  `https://www.facebook.com/sharer/sharer.php?u=${url}`,
    tw:  `https://twitter.com/intent/tweet?text=${metin}&url=${url}`,
    kop: null
  };
  if (platform === 'kop') {
    const temizUrl = window.location.origin + '/?ilan=' + id;
    navigator.clipboard.writeText(temizUrl).then(() => bildirim('🔗 Link kopyalandı!', 'basari'));
    return;
  }
  if (links[platform]) window.open(links[platform], '_blank', 'width=600,height=400');
}



// ══════════════════════════════════════════════════════════════════
// FAZ 3 — SEO META ETİKETLERİ
// ══════════════════════════════════════════════════════════════════
function seoGuncelle({ baslik, aciklama, resim, url, tip = 'website', fiyat = '', konum = '' }) {
  const tamBaslik = baslik ? baslik + ' | Portföy Gayrimenkul' : 'Portföy Gayrimenkul — Fethiye';
  const tamAciklama = aciklama || (konum ? `${konum} — ${fiyat}` : 'Fethiye ve Muğla\'da satılık, kiralık gayrimenkul.');
  const tamResim = resim || 'https://portfoygayrimenkul.com.tr/static/img/og-default.jpg';
  const tamUrl = url || window.location.href;
  const setMeta = (id, val) => { const e = document.getElementById(id); if (e) e.setAttribute('content', val); };
  document.title = tamBaslik;
  document.querySelector('meta[name="description"]')?.setAttribute('content', tamAciklama);
  setMeta('og-title', tamBaslik);
  setMeta('og-description', tamAciklama);
  setMeta('og-image', tamResim);
  setMeta('og-url', tamUrl);
  setMeta('tw-title', tamBaslik);
  setMeta('tw-description', tamAciklama);
  setMeta('tw-image', tamResim);
  // og:type
  const ogType = document.querySelector('meta[property="og:type"]');
  if (ogType) ogType.setAttribute('content', tip);
  // Structured Data (JSON-LD)
  const ldId = 'structured-data-ld';
  let ld = document.getElementById(ldId);
  if (!ld) { ld = document.createElement('script'); ld.id = ldId; ld.type = 'application/ld+json'; document.head.appendChild(ld); }
  ld.textContent = JSON.stringify({
    '@context': 'https://schema.org',
    '@type': tip === 'article' ? 'Article' : 'RealEstateListing',
    'name': baslik,
    'description': tamAciklama,
    'url': tamUrl,
    'image': tamResim,
    'offers': fiyat ? { '@type': 'Offer', 'price': fiyat.replace(/[^\d]/g,''), 'priceCurrency': 'TRY' } : undefined
  });
}

// ══════════════════════════════════════════════════════════════════
// FAZ 3 — BLOG LİSTE
// ══════════════════════════════════════════════════════════════════
let aktifBlogEtiket = '';

async function blogListeYukle() {
  const grid = document.getElementById('blog-grid');
  if (!grid) return;
  grid.innerHTML = '<div class="yukleniyor"><div class="spinner"></div>Yükleniyor…</div>';

  // Güvenlik zaman aşımı — 8sn sonra spinner'ı kaldır
  let timeout;
  const safety = new Promise((_, rej) => {
    timeout = setTimeout(() => rej(new Error('Zaman aşımı')), 8000);
  });

  try {
    const yazılar = await Promise.race([api.getBlog(), safety]);
    clearTimeout(timeout);
    if (!yazılar || !yazılar.length) {
      grid.innerHTML = '<div class="bos-durum"><div class="bos-ikon">✍️</div><h3>Henüz yazı yok</h3><p>Admin panelinden yeni yazı ekleyebilirsiniz</p></div>';
      return;
    }

    seoGuncelle({
      baslik: 'Fethiye Gayrimenkul Haberleri',
      aciklama: 'Fethiye piyasa haberleri, gayrimenkul trendleri ve yatırım önerileri.'
    });

    // Etiket barı
    const etiketBar = document.getElementById('blog-etiket-bar');
    if (etiketBar) {
      const tumEtiketler = [...new Set(yazılar.flatMap(y => Array.isArray(y.etiketler) ? y.etiketler : []))];
      etiketBar.innerHTML = tumEtiketler.length
        ? '<span class="blog-etiket" style="cursor:pointer;padding:.3rem .75rem" onclick="blogEtiketFiltre(\'\')">Tümü</span>' +
          tumEtiketler.map(e => `<span class="blog-etiket" style="cursor:pointer;padding:.3rem .75rem" onclick="blogEtiketFiltre(\'${e}\')">${e}</span>`).join('')
        : '';
    }

    // Ana sayfa blog şeridi
    const anaGrid = document.getElementById('ana-blog-grid');
    const anaSerit = document.getElementById('ana-blog-serit');
    if (anaGrid && anaSerit && yazılar.length > 0) {
      anaSerit.style.display = '';
      anaGrid.innerHTML = '';
      yazılar.slice(0, 3).forEach(y => anaGrid.appendChild(blogKartOlustur(y)));
    }

    // Blog liste sayfası
    const filtreli = aktifBlogEtiket
      ? yazılar.filter(y => (Array.isArray(y.etiketler)?y.etiketler:[]).includes(aktifBlogEtiket))
      : yazılar;
    grid.innerHTML = '';
    if (!filtreli.length) {
      grid.innerHTML = '<div class="bos-durum"><div class="bos-ikon">✍️</div><h3>Henüz yazı yok</h3><p>Admin panelinden yeni yazı ekleyebilirsiniz</p></div>';
      return;
    }
    filtreli.forEach(y => grid.appendChild(blogKartOlustur(y)));
  } catch (e) {
    grid.innerHTML = '<div class="bos-durum"><div class="bos-ikon">⚠️</div><h3>Yazılar yüklenemedi</h3><p>Lütfen sayfayı yenileyin</p></div>';
  }
}

function blogEtiketFiltre(etiket) {
  aktifBlogEtiket = etiket;
  blogListeYukle();
}

function blogIcerikRender(metin) {
  // Önce [resim:URL:boyut:konum] etiketlerini geçici placeholder'a çevir (HTML escape'den önce)
  const resimEslesmeleri = [];
  let gecici = metin.replace(/\[resim:([^:\]]+):([^:\]]+):([^\]]+)\]/g, (m, url, boyut, konum) => {
    const idx = resimEslesmeleri.length;
    resimEslesmeleri.push({ url, boyut, konum });
    return `@@RESIM_${idx}@@`;
  });

  let html = gecici
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\_(.+?)\_/g, '<em>$1</em>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^(.+)$/, '<p>$1</p>');

  // Placeholder'ları gerçek resim HTML'iyle değiştir
  resimEslesmeleri.forEach((r, idx) => {
    const resimHtml = `<div class="blog-icerik-resim boyut-${r.boyut} konum-${r.konum}"><img src="${r.url}" loading="lazy" alt=""></div>`;
    html = html.replace(`@@RESIM_${idx}@@`, resimHtml);
  });

  return html;
}

async function sayfaGoster(slug) {
  const ic = document.getElementById('sayfa-icerik-ic');
  if (!ic) return;
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div>Yükleniyor…</div>';
  try {
    const r = await fetch(`/api/public/sayfa/${encodeURIComponent(slug)}`);
    const j = await r.json();
    if (!j || !j.success || !j.data) {
      ic.innerHTML = '<div class="bos-durum"><div class="bos-ikon">📄</div><h3>Sayfa bulunamadı</h3></div>';
      return;
    }
    const p = j.data;
    // Backend durum değerleri: 'Taslak', 'Yayınla', 'Arşiv'
    // Public görüntüleme sadece 'Yayınla' veya 'Aktif' için
    if (p.durum && p.durum !== 'Yayınla' && p.durum !== 'Yayında' && p.durum !== 'Aktif') {
      ic.innerHTML = '<div class="bos-durum"><div class="bos-ikon">🔒</div><h3>Bu sayfa yayında değil</h3></div>';
      return;
    }
    document.title = (p.seo_baslik || p.baslik || 'Sayfa') + ' — ' + (document.title.split(' — ')[1] || '');
    const etiketHtml = Array.isArray(p.etiketler) ? p.etiketler.map(e => `<span class="blog-etiket">${e}</span>`).join('') : '';
    ic.innerHTML = `
      ${p.kapak_resim ? `<img src="${p.kapak_resim}" alt="${p.baslik||''}" style="width:100%;max-height:340px;object-fit:cover;border-radius:var(--r);margin-bottom:1.5rem">` : ''}
      <h1 style="font-family:var(--font-baslik);font-size:2rem;margin-bottom:.5rem;color:var(--toprak)">${p.baslik || ''}</h1>
      ${p.ozet ? `<p style="color:var(--gri-metin);font-size:1.05rem;margin-bottom:1.5rem">${p.ozet}</p>` : ''}
      <div class="blog-icerik">${p.icerik || ''}</div>
      ${etiketHtml ? `<div style="margin-top:1.5rem">${etiketHtml}</div>` : ''}
    `;
    if (window.seoUpdate) window.seoUpdate('sayfa', { slug, baslik: p.baslik, aciklama: p.seo_aciklama || p.ozet, anahtar: p.seo_anahtar_kelimeler, resim: p.kapak_resim });
  } catch (e) {
    ic.innerHTML = '<div class="bos-durum"><div class="bos-ikon">⚠️</div><h3>Sayfa yüklenemedi</h3><p>Lütfen tekrar deneyin</p></div>';
  }
}
window.sayfaGoster = sayfaGoster;

function editorEkle(once, sonra) {
  const ta = document.getElementById('blog-icerik');
  if (!ta) return;
  const start = ta.selectionStart, end = ta.selectionEnd;
  const secili = ta.value.substring(start, end);
  const yeni = ta.value.substring(0, start) + once + secili + sonra + ta.value.substring(end);
  ta.value = yeni;
  ta.selectionStart = start + once.length;
  ta.selectionEnd = start + once.length + secili.length;
  ta.focus();
}

function blogKartOlustur(yazi) {
  const el = document.createElement('div');
  el.className = 'blog-kart';
  const tarih = yazi.olusturma ? new Date(yazi.olusturma).toLocaleDateString('tr-TR', { day:'numeric', month:'long', year:'numeric' }) : '';
  const etiketHtml = (Array.isArray(yazi.etiketler)?yazi.etiketler:[]).map(e => `<span class="blog-etiket">${e}</span>`).join('');
  el.innerHTML = `
    <div class="blog-kart-foto">
      ${yazi.kapak_resim ? `<img src="${yazi.kapak_resim}" alt="${yazi.baslik}" loading="lazy">` : '📰'}
    </div>
    <div class="blog-kart-bilgi">
      <div class="blog-kart-tarih">${tarih}${yazi.yazar ? ' · ' + yazi.yazar : ''}</div>
      <div class="blog-kart-baslik">${yazi.baslik}</div>
      <div class="blog-kart-ozet">${yazi.ozet || ''}</div>
      <div style="margin-top:.6rem">${etiketHtml}</div>
    </div>`;
  el.onclick = () => sayfaGit('blog-detay', yazi);
  return el;
}

async function blogDetayGoster(yazi) {
  const ic = document.getElementById('blog-detay-ic');
  if (!ic) return;
  const d = await api.getBlogBySlugOrId(yazi.slug) || yazi;
  const tarih = d.olusturma ? new Date(d.olusturma).toLocaleDateString('tr-TR', { day:'numeric', month:'long', year:'numeric' }) : '';
  const etiketHtml = (Array.isArray(d.etiketler)?d.etiketler:[]).map(e => `<span class="blog-etiket">${e}</span>`).join('');
  ic.innerHTML = `
    ${d.kapak_resim ? `<img src="${d.kapak_resim}" alt="${d.baslik}" style="width:100%;max-height:360px;object-fit:cover;border-radius:var(--r);margin-bottom:1.5rem">` : ''}
    <div style="margin-bottom:.75rem">${etiketHtml}</div>
    <h1 style="font-family:'Playfair Display',serif;font-size:clamp(1.5rem,4vw,2rem);font-weight:700;margin-bottom:.5rem;line-height:1.25">${d.baslik}</h1>
    <div style="font-size:.82rem;color:var(--gri-metin);margin-bottom:1.5rem;display:flex;gap:.75rem;flex-wrap:wrap">
      <span>📅 ${tarih}</span>
      ${d.yazar ? `<span>✍️ ${d.yazar}</span>` : ''}
    </div>
    <div class="blog-detay-icerik">${blogIcerikRender(d.icerik||'')}</div>
    <div style="margin-top:2rem;padding-top:1.25rem;border-top:1px solid var(--kumtasi);display:flex;gap:.5rem;flex-wrap:wrap">
      <span style="font-size:.82rem;color:var(--gri-metin)">Paylaş:</span>
      <button class="paylasim-btn pb-wa" style="font-size:.75rem;padding:.3rem .7rem" onclick="ilanPaylas('wa',0,'${d.baslik.replace(/'/g,"\\'")}','')">WhatsApp</button>
      <button class="paylasim-btn pb-fb" style="font-size:.75rem;padding:.3rem .7rem" onclick="ilanPaylas('fb',0,'${d.baslik.replace(/'/g,"\\'")}','')">Facebook</button>
    </div>`;

  seoGuncelle({
    baslik: d.baslik,
    aciklama: d.ozet || d.baslik,
    resim: d.kapak_resim || '',
    url: window.location.origin + '/?blog=' + d.slug,
    tip: 'article'
  });
}

// ══════════════════════════════════════════════════════════════════
// FAZ 3 — ADMIN BLOG PANELİ
// ══════════════════════════════════════════════════════════════════
let blogDuzenleId = null;

async function adminBlog() {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  try {
    const yazılar = await api.getBlog({ durum: '' });
    if (_aktifAdminSayfa !== 'blog') return;
    if (!yazılar || yazılar === null) {
      ic.innerHTML = '<div class="bos-durum"><div class="bos-ikon">⚠️</div><h3>Yazılar yüklenemedi</h3></div>';
      return;
    }

    let html = `<div class="admin-baslik">Blog / Haberler
      <button class="btn btn-kirm" onclick="blogModalAc()">+ Yeni Yazı</button>
    </div>`;

    if (!yazılar.length) {
      html += '<div class="bos-durum"><div class="bos-ikon">✍️</div><h3>Henüz yazı yok</h3><p>İlk blog yazınızı ekleyin</p></div>';
    } else {
      html += `<div class="tablo-kont"><table class="tablo">
        <thead><tr><th>Başlık</th><th>Durum</th><th>Tarih</th><th>Yazar</th><th></th></tr></thead><tbody>`;
      yazılar.forEach(y => {
        const tarih = y.olusturma ? new Date(y.olusturma).toLocaleDateString('tr-TR') : '';
        html += `<tr>
        <td><strong style="font-size:.9rem">${y.baslik}</strong>
          <div style="font-size:.75rem;color:var(--gri-metin);margin-top:.15rem">${(Array.isArray(y.etiketler)?y.etiketler:[]).join(', ')}</div>
        </td>
          <td><span class="durum-pill ${y.durum === 'Yayında' ? 'dp-Aktif' : 'dp-Taslak'}">${y.durum}</span></td>
          <td style="font-size:.78rem;color:var(--gri-metin)">${tarih}</td>
          <td style="font-size:.82rem">${y.yazar||'–'}</td>
          <td><div class="tablo-eylemler">
            <button class="btn btn-ntr btn-sm" onclick="blogDuzenle(${y.id})">✏</button>
            <button class="btn btn-sm" style="background:${y.durum==='Yayında'?'#FEF3C7;color:#92400E':'#D1FAE5;color:#065F46'}"
              onclick="blogDurumDegis(${y.id},'${y.durum==='Yayında'?'Taslak':'Yayında'}')">
              ${y.durum==='Yayında'?'⏸':'▶'}
            </button>
            <button class="btn btn-hat btn-sm" onclick="if(confirm('Yazı silinsin mi?'))blogSilAdmin(${y.id})">🗑</button>
          </div></td>
        </tr>`;
      });
      html += '</tbody></table></div>';
    }
    if (_aktifAdminSayfa !== 'blog') return;
    ic.innerHTML = html;
  } catch (e) {
    if (_aktifAdminSayfa !== 'blog') return;
    ic.innerHTML = '<div class="bos-durum"><div class="bos-ikon">⚠️</div><h3>Yazılar yüklenemedi</h3><p>Lütfen sayfayı yenileyin</p></div>';
  }
}

function blogModalAc(yazi = null) {
  blogDuzenleId = yazi ? yazi.id : null;
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = `
    <div class="admin-baslik" style="margin-bottom:1.25rem">
      ${yazi ? 'Yazıyı Düzenle' : 'Yeni Blog Yazısı'}
      <button class="btn btn-ntr btn-sm" onclick="adminBlog()">← Geri</button>
    </div>
    <div style="max-width:780px;display:flex;flex-direction:column;gap:1rem">
      <div class="form-grup"><label class="form-etiket z">Başlık</label>
        <input class="form-girdi" id="blog-baslik" value="${yazi?.baslik||''}" placeholder="Yazı başlığı…"></div>
      <div class="form-grup"><label class="form-etiket">Kısa Özet</label>
        <input class="form-girdi" id="blog-ozet" value="${yazi?.ozet||''}" placeholder="Listede görünecek kısa açıklama…"></div>
      <div class="form-grup"><label class="form-etiket">Etiketler <span style="font-size:.72rem;color:var(--gri-metin)">(virgülle ayırın)</span></label>
        <input class="form-girdi" id="blog-etiketler" value="${(Array.isArray(yazi?.etiketler)?yazi.etiketler:[]).join(', ')}" placeholder="Fethiye, Satılık, Yatırım…"></div>

      <div class="form-grup">
        <label class="form-etiket">İçerik</label>
        <div class="editor-araclari">
          <button onclick="editorEkle('**','**')"><b>B</b></button>
          <button onclick="editorEkle('_','_')"><i>I</i></button>
          <button onclick="editorEkle('\n## ','')">H2</button>
          <button onclick="editorEkle('\n### ','')">H3</button>
          <button onclick="editorEkle('\n\n','')">¶</button>
          <span style="width:1px;background:var(--kumtasi);align-self:stretch;margin:0 .15rem"></span>
          <button onclick="blogResimModalAc()" style="display:flex;align-items:center;gap:.3rem">🖼 Resim Ekle</button>
        </div>
        <div class="editor-toolbar-girdi">
          <textarea class="blog-editor" id="blog-icerik">${yazi?.icerik||''}</textarea>
        </div>
        <p style="font-size:.72rem;color:var(--gri-metin);margin-top:.4rem">
          İçerikte görsel görünecek yer: <code>[resim:URL:boyut:konum]</code> — Resim Ekle butonuyla otomatik eklenir.
        </p>
      </div>

      ${yazi ? `
      <div class="form-grup">
        <label class="form-etiket">Kapak Fotoğrafı</label>
        ${yazi.kapak_resim ? `<img src="${yazi.kapak_resim}" style="height:80px;border-radius:6px;margin-bottom:.5rem;display:block">` : ''}
        <label class="btn btn-ntr btn-sm" style="cursor:pointer">
          📷 Kapak Ekle
          <input type="file" accept="image/*" style="display:none" onchange="blogKapakYukle(event,${yazi.id})">
        </label>
      </div>` : ''}

      <div class="form-grup"><label class="form-etiket">Durum</label>
        <select class="form-girdi" id="blog-durum">
          <option ${(!yazi||yazi.durum==='Taslak')?'selected':''}>Taslak</option>
          <option ${yazi?.durum==='Yayında'?'selected':''}>Yayında</option>
        </select></div>

      <div style="display:flex;gap:.75rem">
        <button class="btn btn-kirm btn-lg" onclick="blogKaydet()">💾 ${yazi ? 'Güncelle' : 'Kaydet'}</button>
        <button class="btn btn-ntr" onclick="adminBlog()">Vazgeç</button>
      </div>
    </div>`;
}

async function blogKaydet() {
  const baslik = document.getElementById('blog-baslik')?.value?.trim();
  if (!baslik) { bildirim('Başlık zorunlu', 'hata'); return; }
  const etiketStr = document.getElementById('blog-etiketler')?.value || '';
  const etiketler = etiketStr.split(',').map(e => e.trim()).filter(Boolean);
  const data = {
    baslik,
    ozet:     document.getElementById('blog-ozet')?.value || '',
    icerik:   document.getElementById('blog-icerik')?.value || '',
    etiketler,
    durum:    document.getElementById('blog-durum')?.value || 'Taslak',
  };
  let r;
  if (blogDuzenleId) {
    // Mevcut yazıyı çek — kapak resmi kaybolmasın
    const mevcut = await api.getBlogBySlugOrId(blogDuzenleId);
    if (mevcut && mevcut.kapak_resim) data.kapak_resim = mevcut.kapak_resim;
    r = await api.update('blog', blogDuzenleId, data);
  } else {
    r = await api.save('blog', data);
    if (r?.id) blogDuzenleId = r.id;
  }
  if (r) { bildirim('Yazı kaydedildi!', 'basari'); adminBlog(); }
}

async function blogDurumDegis(id, durum) {
  const mevcut = await api.getBlogBySlugOrId(id);
  if (!mevcut) return;
  const r = await api.update('blog', id, { ...mevcut, durum });
  if (r) { bildirim('Durum: ' + durum, 'basari'); adminBlog(); }
}

async function blogDuzenle(id) {
  const yazı = await api.getBlogBySlugOrId(id);
  if (yazı) { blogDuzenleId = id; blogModalAc(yazı); }
}

async function blogSilAdmin(id) {
  const r = await api.delete('blog', id);
  if (r) { bildirim('Yazı silindi', 'basari'); adminBlog(); }
}

async function blogKapakYukle(evt, bid) {
  const dosya = evt.target.files[0]; if (!dosya) return;
  const fd = new FormData(); fd.append('dosya', dosya);
  const d = await api.upload('blog', bid, fd, { kind: 'kapak' });
  if (d) { bildirim('Kapak eklendi!', 'basari'); blogDuzenle(bid); }
}

// ── Profil Resmi ─────────────────────────────────────────────────────────────
async function profilResmiYukle(evt) {
  const dosya = evt.target.files[0];
  if (!dosya) return;
  if (dosya.size > 3 * 1024 * 1024) { bildirim('Maksimum 3MB olabilir', 'hata'); return; }

  // Önizleme
  const reader = new FileReader();
  reader.onload = e => {
    const onizleme = document.getElementById('profil-avatar-onizleme');
    if (onizleme) onizleme.innerHTML = `<img src="${e.target.result}" style="width:100%;height:100%;object-fit:cover">`;
  };
  reader.readAsDataURL(dosya);

  // Yükle
  const fd = new FormData(); fd.append('dosya', dosya);
  const d = await api.upload('kullanicilar', null, fd, { kind: 'profil-resmi' });
  if (d) {
    window._profilResmi = d.url;
    bildirim('Profil fotoğrafı güncellendi!', 'basari');
    const silBtn = document.getElementById('profil-resim-sil-btn');
    if (silBtn) silBtn.style.display = '';
  }
}

async function profilResmiSil() {
  // Sunucuda silme (basit - profil resmini boş yap)
  const r = await api.update('kullanicilar', null, {
      ad_soyad: document.getElementById('profil-ad')?.value || kullanici?.ad_soyad || '',
      email:    document.getElementById('profil-email')?.value || kullanici?.email || '',
      profil_resmi: ''
    }, { action: 'profil' });
  if (r) {
    window._profilResmi = '';
    const onizleme = document.getElementById('profil-avatar-onizleme');
    if (onizleme) onizleme.innerHTML = '🏠';
    bildirim('Profil fotoğrafı kaldırıldı', 'bilgi');
  }
}

// ══════════════════════════════════════════════════════════════════
// FAZ 4 — PDF BROŞÜR
// ══════════════════════════════════════════════════════════════════
async function pdfIndir(id) {
  bildirim('📄 PDF hazırlanıyor…', 'bilgi');
  try {
    const blob = await api.download('portfoyler', id, { kind: 'pdf' });
    if (!blob) { bildirim('PDF oluşturulamadı', 'hata'); return; }
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ilan_${id}_brosur.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    bildirim('✅ PDF indirildi', 'basari');
  } catch (e) {
    bildirim('PDF indirme hatası', 'hata');
  }
}

// ══════════════════════════════════════════════════════════════════
// FAZ 4 — AI FİYAT ANALİZİ
// ══════════════════════════════════════════════════════════════════
async function fiyatAnaliziGoster(id) {
  const kutu = document.getElementById('fiyat-analiz-kutu');
  if (!kutu) return;

  if (kutu.style.display !== 'none' && kutu.dataset.id == id) {
    kutu.style.display = 'none';
    return;
  }

  kutu.style.display = '';
  kutu.dataset.id = id;
  kutu.innerHTML = `<div class="yukleniyor" style="padding:1.5rem"><div class="spinner"></div>Piyasa verileri analiz ediliyor…</div>`;
  kutu.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

  const d = await api.getFiyatAnalizi(id);
  if (!d) { kutu.style.display = 'none'; return; }

  if (!d.yeterli_veri) {
    kutu.innerHTML = `
      <div class="detay-bolum" style="background:var(--krem);border-style:dashed">
        <div class="detay-bolum-baslik">📊 Piyasa Analizi</div>
        <p style="font-size:.88rem;color:var(--gri-metin)">${d.mesaj}</p>
      </div>`;
    return;
  }

  const renkler = {
    yuksek: { bg: '#FEE2E2', text: '#991B1B', etiket: '↑ Yüksek' },
    dusuk:  { bg: '#D1FAE5', text: '#065F46', etiket: '↓ Düşük' },
    uygun:  { bg: 'var(--kiremit-a)', text: 'var(--kiremit-k)', etiket: '≈ Uygun' },
  };
  const renk = renkler[d.durum] || renkler.uygun;

  const benzerSatirlari = d.en_yakin_3.map(b => `
    <div style="display:flex;justify-content:space-between;align-items:center;padding:.5rem 0;border-bottom:1px solid var(--kumtasi);font-size:.85rem">
      <span style="cursor:pointer;color:var(--kiremit)" onclick="haritaIlanAc(${b.id})">${b.baslik.substring(0,32)}${b.baslik.length>32?'…':''}</span>
      <span style="font-weight:600">${b.m2_fiyat.toLocaleString('tr-TR')} TL/m²</span>
    </div>`).join('');

  kutu.innerHTML = `
    <div class="detay-bolum">
      <div class="detay-bolum-baslik">📊 AI Piyasa Analizi</div>

      <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:1.25rem">
        <div style="flex:1;min-width:140px;background:var(--krem);border-radius:8px;padding:.85rem 1rem">
          <div style="font-size:.72rem;color:var(--gri-metin);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.2rem">Bu İlan</div>
          <div style="font-size:1.2rem;font-weight:700;color:var(--toprak)">${d.hedef_m2_fiyat.toLocaleString('tr-TR')} <span style="font-size:.75rem;font-weight:400">TL/m²</span></div>
        </div>
        <div style="flex:1;min-width:140px;background:var(--krem);border-radius:8px;padding:.85rem 1rem">
          <div style="font-size:.72rem;color:var(--gri-metin);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.2rem">Bölge Ortalaması</div>
          <div style="font-size:1.2rem;font-weight:700;color:var(--toprak)">${d.ortalama_m2_fiyat.toLocaleString('tr-TR')} <span style="font-size:.75rem;font-weight:400">TL/m²</span></div>
        </div>
        <div style="flex:1;min-width:140px;background:${renk.bg};border-radius:8px;padding:.85rem 1rem">
          <div style="font-size:.72rem;color:${renk.text};text-transform:uppercase;letter-spacing:.05em;margin-bottom:.2rem">Durum</div>
          <div style="font-size:1.1rem;font-weight:700;color:${renk.text}">${renk.etiket} %${Math.abs(d.fark_yuzde)}</div>
        </div>
      </div>

      ${d.ai_yorum ? `
      <div style="background:var(--kiremit-a);border-radius:8px;padding:1rem;margin-bottom:1.25rem;display:flex;gap:.75rem">
        <span style="font-size:1.3rem;flex-shrink:0">🤖</span>
        <p style="font-size:.88rem;color:var(--kiremit-k);line-height:1.6;margin:0">${d.ai_yorum}</p>
      </div>` : !d.ai_yorum_hata ? `
      <div style="font-size:.78rem;color:var(--gri-metin);margin-bottom:1rem;font-style:italic">
        AI yorumu için Site Ayarları → AI Ayarları'ndan API anahtarı ekleyin.
      </div>` : ''}

      <div style="font-size:.78rem;color:var(--gri-metin);margin-bottom:.5rem">
        ${d.benzer_sayisi} benzer ilanla karşılaştırıldı · En yakın 3 örnek:
      </div>
      ${benzerSatirlari}
    </div>`;
}

async function adminFiyatAnaliziGenel() {
  const veri = await api.getFiyatAnaliziGenel();
  if (!veri || !veri.length) return '<p style="font-size:.85rem;color:var(--gri-metin)">Henüz yeterli veri yok.</p>';
  return `
    <div class="tablo-kont"><table class="tablo">
      <thead><tr><th>Kategori</th><th>İlan Sayısı</th><th>Min m²</th><th>Ortalama m²</th><th>Max m²</th></tr></thead>
      <tbody>
        ${veri.map(v => `<tr>
          <td><strong>${v.kategori}</strong></td>
          <td>${v.ilan_sayisi}</td>
          <td>${v.min_m2_fiyat.toLocaleString('tr-TR')} TL</td>
          <td style="font-weight:600;color:var(--kiremit)">${v.ortalama_m2_fiyat.toLocaleString('tr-TR')} TL</td>
          <td>${v.max_m2_fiyat.toLocaleString('tr-TR')} TL</td>
        </tr>`).join('')}
      </tbody>
    </table></div>`;
}

async function aiAyarlariKaydet() {
  const apiKey = document.getElementById('ay-ai_api_key')?.value || '';
  const saglayici = document.getElementById('ay-ai_saglayici')?.value || 'deepseek';
  const r = await api.update('ayarlar/ai', null, { ai_api_key: apiKey, ai_saglayici: saglayici });
  if (r) bildirim('AI ayarları kaydedildi!', 'basari');
}

// ══════════════════════════════════════════════════════════════════
// FAZ 4 — BLOG İÇERİK RESMİ EKLEME
// ══════════════════════════════════════════════════════════════════
let blogResimSecilenDosya = null;

function blogResimModalAc() {
  blogResimSecilenDosya = null;
  document.getElementById('blog-resim-onizleme-kont').style.display = 'none';
  document.getElementById('blog-resim-ekle-btn').disabled = true;
  document.getElementById('blog-resim-input').value = '';
  document.querySelector('input[name="blog-boyut"][value="dikdortgen"]').checked = true;
  document.querySelector('input[name="blog-konum"][value="ortali"]').checked = true;
  document.getElementById('blog-resim-modal').style.display = 'flex';
}

function blogResimSecildi(evt) {
  const dosya = evt.target.files[0];
  if (!dosya) return;
  if (dosya.size > 12 * 1024 * 1024) { bildirim("Dosya 12MB'dan küçük olmalı", 'hata'); return; }

  blogResimSecilenDosya = dosya;
  const reader = new FileReader();
  reader.onload = e => {
    document.getElementById('blog-resim-onizleme').src = e.target.result;
    document.getElementById('blog-resim-onizleme-kont').style.display = '';
    document.getElementById('blog-resim-ekle-btn').disabled = false;
  };
  reader.readAsDataURL(dosya);
}

async function blogResimIcerigeEkle() {
  if (!blogResimSecilenDosya) return;
  const btn = document.getElementById('blog-resim-ekle-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Yükleniyor…';

  const boyut = document.querySelector('input[name="blog-boyut"]:checked')?.value || 'dikdortgen';
  const konum = document.querySelector('input[name="blog-konum"]:checked')?.value || 'ortali';

  const fd = new FormData();
  fd.append('dosya', blogResimSecilenDosya);
  const d = await api.upload('blog', null, fd, { kind: 'icerik-resim', query: { boyut, konum } });

  btn.disabled = false;
  btn.textContent = 'İçeriğe Ekle';

  if (d) {
    const ta = document.getElementById('blog-icerik');
    const etiket = `\n[resim:${d.url}:${boyut}:${konum}]\n`;
    if (ta) {
      const pos = ta.selectionStart || ta.value.length;
      ta.value = ta.value.substring(0, pos) + etiket + ta.value.substring(pos);
      ta.focus();
    }
    bildirim('✅ Resim içeriğe eklendi', 'basari');
    document.getElementById('blog-resim-modal').style.display = 'none';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const dz = document.getElementById('blog-resim-drop');
  if (dz) {
    dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('uzerinde'); });
    dz.addEventListener('dragleave', () => dz.classList.remove('uzerinde'));
    dz.addEventListener('drop', e => {
      e.preventDefault(); dz.classList.remove('uzerinde');
      if (e.dataTransfer.files[0]) {
        blogResimSecilenDosya = e.dataTransfer.files[0];
        blogResimSecildi({ target: { files: e.dataTransfer.files } });
      }
    });
  }
});


// ── Kayıt Sistemi ─────────────────────────────────────────────────────────────
function kayitModalAc() {
  ['k-ad','k-email','k-sifre','k-sifre2'].forEach(id => {
    const el = document.getElementById(id); if (el) el.value = '';
  });
  const hata = document.getElementById('kayit-hata');
  if (hata) { hata.style.display = 'none'; hata.textContent = ''; }
  document.getElementById('kayit-modal').style.display = 'flex';
}

async function kayitYap() {
  const ad     = document.getElementById('k-ad')?.value?.trim();
  const email  = document.getElementById('k-email')?.value?.trim();
  const sifre  = document.getElementById('k-sifre')?.value;
  const sifre2 = document.getElementById('k-sifre2')?.value;
  const hataEl = document.getElementById('kayit-hata');

  const hata = (msg) => { hataEl.textContent = msg; hataEl.style.display = ''; };

  if (!ad)    return hata('Ad soyad gerekli');
  if (!email) return hata('E-posta gerekli');
  if (!sifre || sifre.length < 8) return hata('Şifre en az 8 karakter olmalı');
  if (sifre !== sifre2) return hata('Şifreler eşleşmiyor');

  const d = await api.save('kullanicilar/kayit', { ad_soyad: ad, email, sifre });
  if (d) {
    document.getElementById('kayit-modal').style.display = 'none';
    bildirim('Kayıt başarılı! Admin onayı bekleniyor.', 'basari');
  }
}

// ── Kullanıcı Onay Sistemi ────────────────────────────────────────────────────
// kullaniciOnayla v3 — yukarıda tanımlı

// ══════════════════════════════════════════════════════════════════
// BANNER SİSTEMİ
// ══════════════════════════════════════════════════════════════════
let _sliderZamanlayici = {};

const BANNER_KONUMLAR = ['anasayfa_ust','anasayfa_hero_alti','ilanlar_ust','haberler_ust','tum_sayfalar_ust','tum_sayfalar_alt'];

async function bannerlariYukle(konum) {
  if (!konum) {
    await Promise.all(BANNER_KONUMLAR.map(k => bannerlariYukle(k)));
    return;
  }
  // Admin sayfasında bannerları gösterme
  if (document.getElementById('sayfa-admin')?.classList.contains('aktif')) {
    const el = document.getElementById(`banner-${konum}`) || document.getElementById(`banner-${konum.replace(/_/g, '-')}`);
    if (el) el.style.display = 'none';
    return;
  }
  const el = document.getElementById(`banner-${konum}`) || document.getElementById(`banner-${konum.replace(/_/g, '-')}`);
  if (!el) return;

  const bannerlar = await api.getBannerlar({ konum, sadece_aktif: 1 });
  if (!bannerlar || !bannerlar.length) { el.style.display = 'none'; el.innerHTML = ''; return; }
  el.style.display = '';

  const sliderler = bannerlar.filter(b => b.tip === 'slider');
  const duyurular = bannerlar.filter(b => b.tip === 'duyuru');

  let html = '';

  // Slider bannerlar
  if (sliderler.length) {
    const yukseklik = { tam: '420px', normal: '280px', kucuk: '160px' }[sliderler[0].boyut] || '280px';
    html += `<div class="banner-alan slider-kont" id="slider-${konum}" style="height:${yukseklik}">
      <div class="slider-sarici" id="slider-sarici-${konum}">
        ${sliderler.map((b, i) => `
        <div class="slider-slayt" style="height:${yukseklik}">
          ${b.resim_url ? `<img src="${b.resim_url}" alt="${b.baslik}" loading="lazy">` : `<div style="position:absolute;inset:0;background:${b.renk_arkaplan}"></div>`}
          ${(b.baslik || b.alt_metin || b.link_url) ? `
          <div class="slider-slayt-icerik">
            ${b.baslik ? `<div class="slider-baslik" style="color:${b.renk_metin}">${b.baslik}</div>` : ''}
            ${b.alt_metin  ? `<div class="slider-metin"  style="color:${b.renk_metin}">${b.alt_metin}</div>`  : ''}
            ${b.link_url ? `<a href="${b.link_url}" class="slider-btn" style="background:${b.renk_arkaplan};color:#fff">${b.link_metin || 'İncele'} →</a>` : ''}
          </div>` : ''}
        </div>`).join('')}
      </div>
      ${sliderler.length > 1 ? `
      <button class="slider-ok slider-ok-sol" onclick="sliderGit('${konum}',-1)">‹</button>
      <button class="slider-ok slider-ok-sag" onclick="sliderGit('${konum}',1)">›</button>
      <div class="slider-noktalar" id="slider-noktalar-${konum}">
        ${sliderler.map((_,i) => `<button class="slider-nokta${i===0?' aktif':''}" onclick="sliderGitDirekt('${konum}',${i})"></button>`).join('')}
      </div>` : ''}
    </div>`;

    // Otomatik geçiş
    if (sliderler.length > 1) {
      clearInterval(_sliderZamanlayici[konum]);
      window[`_sliderIdx_${konum}`] = 0;
      window[`_sliderMax_${konum}`] = sliderler.length;
      _sliderZamanlayici[konum] = setInterval(() => sliderGit(konum, 1), 5000);
    }
  }

  // Duyuru bannerlar
  duyurular.forEach(b => {
    html += `<div class="duyuru-banner" id="duyuru-${b.id}"
               style="background:${b.renk_arkaplan};color:${b.renk_metin}">
      ${b.resim_url ? `<div class="duyuru-ikon"><img src="${b.resim_url}" style="width:48px;height:48px;border-radius:50%;object-fit:cover"></div>` : '<div class="duyuru-ikon">📢</div>'}
      <div class="duyuru-icerik">
        ${b.baslik ? `<div class="duyuru-baslik">${b.baslik}</div>` : ''}
        ${b.alt_metin  ? `<div class="duyuru-metin">${b.alt_metin}</div>`   : ''}
      </div>
      ${b.link_url ? `<a href="${b.link_url}" class="slider-btn" style="background:rgba(0,0,0,.2);flex-shrink:0;color:inherit">${b.link_metin||'İncele'} →</a>` : ''}
      <button class="duyuru-kapat" onclick="duyuruKapat(${b.id})">✕</button>
    </div>`;
  });

  el.innerHTML = html;
}

function sliderGit(konum, yon) {
  const max = window[`_sliderMax_${konum}`] || 1;
  let idx = (window[`_sliderIdx_${konum}`] || 0) + yon;
  if (idx < 0) idx = max - 1;
  if (idx >= max) idx = 0;
  sliderGitDirekt(konum, idx);
  // Otomatik geçişi sıfırla
  clearInterval(_sliderZamanlayici[konum]);
  _sliderZamanlayici[konum] = setInterval(() => sliderGit(konum, 1), 5000);
}

function sliderGitDirekt(konum, idx) {
  window[`_sliderIdx_${konum}`] = idx;
  const sarici = document.getElementById(`slider-sarici-${konum}`);
  if (sarici) sarici.style.transform = `translateX(-${idx * 100}%)`;
  const noktalar = document.querySelectorAll(`#slider-noktalar-${konum} .slider-nokta`);
  noktalar.forEach((n, i) => n.classList.toggle('aktif', i === idx));
}

function duyuruKapat(id) {
  const el = document.getElementById(`duyuru-${id}`);
  if (el) { el.style.animation = 'bil-gir .2s reverse'; setTimeout(() => el.remove(), 180); }
}

// ── Admin Banner Yönetim ──────────────────────────────────────────────────────


// ── Admin Banner Yönetim Paneli ───────────────────────────────────────────────
async function adminBannerlar() {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';

  const [bannerlar, meta] = await Promise.all([
    api.getBannerlar(),
    api.getBannerKonumlar()
  ]);
  if (!bannerlar || !meta) return;

  const konumlar = meta.konumlar || {};
  const boyutlar = meta.boyutlar || {};

  let html = `<div class="admin-baslik">Bannerlar
    <button class="btn btn-kirm" onclick="bannerYeniModal(${JSON.stringify(konumlar).replace(/"/g,'&quot;')},${JSON.stringify(boyutlar).replace(/"/g,'&quot;')})">+ Yeni Banner</button>
  </div>
  <div style="font-size:.78rem;color:var(--gri-metin);margin-bottom:1rem;padding:.6rem .85rem;background:var(--krem);border-radius:var(--r-sm);border:1px solid var(--kumtasi)">
    💡 <strong>İpucu:</strong> Slayt gösterisi (dönen slider) için aynı konumda <strong>birden çok banner</strong> oluşturun. Her banner bir slayttır.
  </div>`;

  if (!bannerlar.length) {
    html += '<div class="bos-durum"><div class="bos-ikon">🖼</div><h3>Henüz banner yok</h3><p>Yeni banner ekleyerek sitenize görsel canlılık katın.</p></div>';
  } else {
    // Konuma göre grupla
    const gruplar = {};
    Object.entries(konumlar).forEach(([k,v]) => gruplar[k] = { label: v, liste: [] });
    bannerlar.forEach(b => {
      if (!gruplar[b.konum]) gruplar[b.konum] = { label: b.konum, liste: [] };
      gruplar[b.konum].liste.push(b);
    });

    Object.entries(gruplar).forEach(([konum, grup]) => {
      if (!grup.liste.length) return;
      html += `<div style="margin-bottom:2rem">
        <div style="font-size:.78rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--gri-metin);margin-bottom:.75rem;padding-bottom:.5rem;border-bottom:1px solid var(--kumtasi)">
          📍 ${grup.label}
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1rem">`;

      grup.liste.forEach(b => {
        const durumRenk = b.aktif ? 'var(--success,#16a34a)' : 'var(--gri-metin)';
        html += `
          <div style="background:var(--beyaz);border:1px solid var(--kumtasi);border-radius:var(--r);overflow:hidden;box-shadow:var(--kart-gol)">
            <!-- Önizleme -->
            <div style="height:120px;background:${b.resim_url ? 'var(--kumtasi)' : 'linear-gradient(135deg,var(--kiremit),var(--kiremit-k))'};position:relative;overflow:hidden">
              ${b.resim_url ? `<img src="${b.resim_url}" style="width:100%;height:100%;object-fit:cover" loading="lazy">` : ''}
              <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:.75rem;${b.resim_url?'background:rgba(0,0,0,.35)':''}">
                ${b.baslik ? `<div style="color:#fff;font-weight:700;font-size:.9rem;text-align:center;text-shadow:0 1px 4px rgba(0,0,0,.5)">${b.baslik}</div>` : ''}
                ${b.alt_metin ? `<div style="color:rgba(255,255,255,.85);font-size:.75rem;text-align:center;margin-top:.25rem">${b.alt_metin.substring(0,60)}${b.alt_metin.length>60?'…':''}</div>` : ''}
              </div>
              <div style="position:absolute;top:.4rem;left:.4rem">
                <span style="background:${b.tip==='slider'?'var(--primary,#1a56db)':'var(--zeytun)'};color:#fff;font-size:.65rem;font-weight:700;padding:.15rem .45rem;border-radius:3px;text-transform:uppercase">
                  ${b.tip === 'slider' ? '▶ Slider' : '📢 Duyuru'}
                </span>
              </div>
            </div>
            <!-- Bilgi -->
            <div style="padding:.75rem">
              <div style="font-size:.72rem;color:var(--gri-metin);margin-bottom:.35rem">
                📐 ${boyutlar[b.boyut]?.label||b.boyut}
                ${b.link_url ? ` · 🔗 Link var` : ''}
              </div>
              <div style="display:flex;gap:.35rem;flex-wrap:wrap">
                <button class="btn btn-ntr btn-sm" onclick="bannerResimModal(${b.id})">📷</button>
                <button class="btn btn-ntr btn-sm" onclick="bannerDuzenleModal(${b.id},${JSON.stringify(konumlar).replace(/"/g,'&quot;')},${JSON.stringify(boyutlar).replace(/"/g,'&quot;')})">✏</button>
                <button class="btn btn-sm" style="background:${b.aktif?'#FEF3C7':'#D1FAE5'};color:${b.aktif?'#92400E':'#065F46'}" onclick="bannerToggle(${b.id},${b.aktif?0:1})">
                  ${b.aktif ? '⏸ Pasif' : '▶ Aktif'}
                </button>
                <button class="btn btn-hat btn-sm" onclick="if(confirm('Silinsin mi?'))bannerSil(${b.id})">🗑</button>
              </div>
            </div>
          </div>`;
      });
      html += '</div></div>';
    });
  }

  ic.innerHTML = html;
}

// Banner Yeni/Düzenle Modal
function bannerYeniModal(konumlar, boyutlar) {
  bannerFormModal(null, konumlar, boyutlar);
}

async function bannerDuzenleModal(id, konumlar, boyutlar) {
  const d = await api.getBannerlar().then(list => list?.find(b => b.id === id));
  bannerFormModal(d, konumlar, boyutlar);
}

function bannerFormModal(mevcut, konumlar, boyutlar) {
  const modal = document.getElementById('banner-modal');
  const baslik = document.getElementById('banner-modal-baslik');
  const govde = document.getElementById('banner-modal-govde');

  baslik.textContent = mevcut ? 'Banner Düzenle' : 'Yeni Banner';
  modal.style.display = 'flex';

  const konumOpts = Object.entries(konumlar).map(([k,v]) =>
    `<option value="${k}"${mevcut?.konum===k?' selected':''}>${v}</option>`).join('');
  const boyutOpts = Object.entries(boyutlar).map(([k,v]) =>
    `<option value="${k}"${mevcut?.boyut===k?' selected':''}>${v.label} (${v.yukseklik}px)</option>`).join('');

  govde.innerHTML = `
    <div class="form-grup">
      <label class="form-etiket">Banner Türü</label>
      <div style="display:flex;gap:.5rem">
        <label style="flex:1;display:flex;align-items:center;gap:.5rem;padding:.6rem .85rem;border:1.5px solid ${!mevcut||mevcut.tip==='slider'?'var(--kiremit)':'var(--kumtasi)'};border-radius:var(--r-sm);cursor:pointer;font-size:.875rem" id="tip-slider-lbl">
          <input type="radio" name="b-tip" value="slider" ${!mevcut||mevcut.tip==='slider'?'checked':''} onchange="document.getElementById('tip-slider-lbl').style.borderColor='var(--kiremit)';document.getElementById('tip-duyuru-lbl').style.borderColor='var(--kumtasi)'">
          ▶ Slider / Resimli
        </label>
        <label style="flex:1;display:flex;align-items:center;gap:.5rem;padding:.6rem .85rem;border:1.5px solid ${mevcut?.tip==='duyuru'?'var(--kiremit)':'var(--kumtasi)'};border-radius:var(--r-sm);cursor:pointer;font-size:.875rem" id="tip-duyuru-lbl">
          <input type="radio" name="b-tip" value="duyuru" ${mevcut?.tip==='duyuru'?'checked':''} onchange="document.getElementById('tip-duyuru-lbl').style.borderColor='var(--kiremit)';document.getElementById('tip-slider-lbl').style.borderColor='var(--kumtasi)'">
          📢 Duyuru / Metin
        </label>
      </div>
    </div>
    <div class="form-grup">
      <label class="form-etiket">Başlık</label>
      <input class="form-girdi" id="b-baslik" value="${mevcut?.baslik||''}" placeholder="Banner başlığı (opsiyonel)">
    </div>
    <div class="form-grup">
      <label class="form-etiket">Alt Metin / Açıklama</label>
      <textarea class="form-girdi" id="b-altmetin" rows="2" placeholder="Kısa açıklama (opsiyonel)">${mevcut?.alt_metin||''}</textarea>
    </div>
    <div class="form-ikili">
      <div class="form-grup">
        <label class="form-etiket">Konum</label>
        <select class="form-girdi" id="b-konum">${konumOpts}</select>
      </div>
      <div class="form-grup">
        <label class="form-etiket">Boyut</label>
        <select class="form-girdi" id="b-boyut">${boyutOpts}</select>
      </div>
    </div>
    <div class="form-ikili">
      <div class="form-grup">
        <label class="form-etiket">Link URL</label>
        <input class="form-girdi" id="b-link" value="${mevcut?.link_url||''}" placeholder="https://... veya /ilanlar">
      </div>
      <div class="form-grup">
        <label class="form-etiket">Link Hedef</label>
        <select class="form-girdi" id="b-hedef">
          <option value="_self"${mevcut?.link_hedef!=='_blank'?' selected':''}>Aynı sekme</option>
          <option value="_blank"${mevcut?.link_hedef==='_blank'?' selected':''}>Yeni sekme</option>
        </select>
      </div>
    </div>
    <div class="form-grup">
      <label class="form-etiket">Sıra</label>
      <input class="form-girdi" id="b-sira" type="number" value="${mevcut?.sira||0}" min="0" style="width:100px">
    </div>
    <!-- Arka Plan Rengi + Metin Rengi -->
    <div class="form-ikili">
      <div class="form-grup">
        <label class="form-etiket">Arka Plan Rengi</label>
        <div style="display:flex;align-items:center;gap:.5rem">
          <input type="color" id="b-renk-arka" value="${mevcut?.renk_arkaplan||'#C45C35'}"
            style="width:44px;height:38px;border-radius:var(--r-sm);border:1.5px solid var(--kumtasi);cursor:pointer;padding:2px"
            oninput="document.getElementById('b-renk-arka-txt').value=this.value">
          <input class="form-girdi" id="b-renk-arka-txt" value="${mevcut?.renk_arkaplan||'#C45C35'}"
            oninput="document.getElementById('b-renk-arka').value=this.value"
            style="flex:1;font-family:monospace;font-size:.85rem">
        </div>
      </div>
      <div class="form-grup">
        <label class="form-etiket">Metin Rengi</label>
        <div style="display:flex;align-items:center;gap:.5rem">
          <input type="color" id="b-renk-metin" value="${mevcut?.renk_metin||'#ffffff'}"
            style="width:44px;height:38px;border-radius:var(--r-sm);border:1.5px solid var(--kumtasi);cursor:pointer;padding:2px"
            oninput="document.getElementById('b-renk-metin-txt').value=this.value">
          <input class="form-girdi" id="b-renk-metin-txt" value="${mevcut?.renk_metin||'#ffffff'}"
            oninput="document.getElementById('b-renk-metin').value=this.value"
            style="flex:1;font-family:monospace;font-size:.85rem">
        </div>
      </div>
    </div>

    <!-- Görsel Yükleme -->
    <div class="form-grup">
      <label class="form-etiket">Banner Görseli <span style="font-size:.72rem;color:var(--gri-metin);font-weight:400">(opsiyonel)</span></label>
      <label style="display:block;cursor:pointer">
        <div style="border:2px dashed var(--kumtasi);border-radius:var(--r-sm);padding:1.1rem;text-align:center;transition:.15s;background:var(--krem)"
          id="banner-resim-drop"
          ondragover="event.preventDefault();document.getElementById('banner-resim-drop').style.borderColor='var(--kiremit)'"
          ondragleave="document.getElementById('banner-resim-drop').style.borderColor='var(--kumtasi)'"
          ondrop="event.preventDefault();document.getElementById('banner-resim-drop').style.borderColor='var(--kumtasi)';bannerResimSec(event.dataTransfer.files[0])">
          <div style="font-size:1.4rem">🖼</div>
          <div style="font-size:.82rem;color:var(--gri-metin);margin-top:.2rem">
            <strong style="color:var(--kiremit)">Tıkla</strong> veya sürükle bırak<br>
            <span style="font-size:.72rem">JPG · PNG · WEBP — Maks 5MB</span>
          </div>
          <input type="file" id="b-resim-input" accept="image/jpeg,image/png,image/webp"
            style="display:none" onchange="bannerResimSec(this.files[0])">
        </div>
      </label>
      <div id="b-resim-onizleme" style="margin-top:.5rem;display:none">
        <img id="b-resim-onizleme-img" style="width:100%;max-height:100px;object-fit:cover;border-radius:var(--r-sm);border:1px solid var(--kumtasi)">
        <div style="font-size:.72rem;color:var(--zeytun);margin-top:.2rem">✅ Hazır — kaydettiğinizde yüklenecek</div>
      </div>
    </div>

    <div class="form-grup">
      <label style="display:flex;align-items:center;gap:.5rem;cursor:pointer;font-size:.875rem">
        <input type="checkbox" id="b-aktif" ${!mevcut||mevcut.aktif?'checked':''}>
        Aktif (yayında)
      </label>
    </div>`;

    const kaydetBtn = document.getElementById('banner-kaydet-btn');
  if (kaydetBtn) {
    kaydetBtn.textContent = mevcut ? '💾 Güncelle' : '💾 Kaydet';
    kaydetBtn.onclick = () => bannerKaydet(mevcut ? mevcut.id : null);
  }
}

async function bannerKaydet(id) {
  const veri = {
    baslik:          document.getElementById('b-baslik')?.value || '',
    alt_metin:       document.getElementById('b-altmetin')?.value || '',
    tip:             document.querySelector('input[name="b-tip"]:checked')?.value || 'slider',
    konum:           document.getElementById('b-konum')?.value || 'ana_hero_alti',
    boyut:           document.getElementById('b-boyut')?.value || 'genis',
    link_url:        document.getElementById('b-link')?.value || '',
    link_hedef:      document.getElementById('b-hedef')?.value || '_self',
    renk_arkaplan:   document.getElementById('b-renk-arka')?.value || '#C45C35',
    renk_metin:      document.getElementById('b-renk-metin')?.value || '#ffffff',
    sira:            parseInt(document.getElementById('b-sira')?.value) || 0,
    aktif:           document.getElementById('b-aktif')?.checked ? 1 : 0,
  };

  let r, newId = id;
  if (id) {
    r = await api.update('bannerlar', id, veri);
  } else {
    r = await api.save('bannerlar', veri);
  }
  if (r) {
    if (!id && r.id) newId = r.id;
    // Modal hemen kapat
    document.getElementById('banner-modal').style.display = 'none';
    bildirim(id ? 'Banner güncellendi!' : 'Banner oluşturuldu!', 'basari');
    adminBannerlar();
    // Formdan seçilen resim varsa arka planda yükle
    const resimInput = document.getElementById('b-resim-input');
    if (resimInput && resimInput.files && resimInput.files[0] && newId) {
      const fd = new FormData();
      fd.append('file', resimInput.files[0]);
      api.upload('bannerlar', newId, fd).then(rr => {
        if (rr) { bildirim('Görsel yüklendi!', 'basari'); adminBannerlar(); bannerlariYukle(); }
        else { bannerlariYukle(); }
      });
    } else {
      bannerlariYukle();
    }
  }
}

function bannerResimModal(id) {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/jpeg,image/png,image/webp,image/gif';
  input.onchange = async (e) => {
    const dosya = e.target.files[0];
    if (!dosya) return;
    const fd = new FormData();
    fd.append('file', dosya);
    const r = await api.upload('bannerlar', id, fd);
    if (r) {
      bildirim('Resim yüklendi!', 'basari');
      adminBannerlar();
      bannerlariYukle();
    }
  };
  input.click();
}

async function bannerToggle(id, aktif) {
  const r = await api.update('bannerlar', id, {}, { action: 'aktif', query: { aktif } });
  if (r) { adminBannerlar(); bannerlariYukle(); }
}

async function bannerSil(id) {
  const r = await api.delete('bannerlar', id);
  if (r) { bildirim('Banner silindi', 'basari'); adminBannerlar(); bannerlariYukle(); }
}


// ── Banner Yardımcı Fonksiyonlar ─────────────────────────────────────────────
function bannerResimSec(dosya) {
  if (!dosya) return;
  if (dosya.size > 5 * 1024 * 1024) { bildirim('Maksimum 5MB', 'hata'); return; }
  const reader = new FileReader();
  reader.onload = e => {
    const onizleme = document.getElementById('b-resim-onizleme');
    const img = document.getElementById('b-resim-onizleme-img');
    if (onizleme && img) {
      img.src = e.target.result;
      onizleme.style.display = '';
    }
    // Drop zone'u güncelle
    const drop = document.getElementById('banner-resim-drop');
    if (drop) drop.style.borderColor = 'var(--zeytun)';
  };
  reader.readAsDataURL(dosya);
  // Input'a dosyayı ata (her seçimde değiştir)
  const input = document.getElementById('b-resim-input');
  if (input) {
    const dt = new DataTransfer();
    dt.items.add(dosya);
    input.files = dt.files;
  }
}

async function bannerResimSil(bid) {
  if (!confirm('Banner görseli kaldırılsın mı?')) return;
  const r = await api.delete('bannerlar', bid, { action: 'resim-sil' });
  if (r) { bildirim('Görsel kaldırıldı', 'bilgi'); adminBannerlar(); }
}

async function baslat() {
  await katYukle();
  await authGuncelle();
  await siteAyarlariUygula();
  anaSayfaYukle();
  await blogListeYukle();
  BANNER_KONUMLAR.forEach(k => bannerlariYukle(k));
  favBantGuncelle();
  // URL'de ilan parametresi varsa direkt aç
  const urlParams = new URLSearchParams(window.location.search);
  const ilanId = urlParams.get('ilan');
  const blogSlug = urlParams.get('blog');
  if (ilanId) {
    const d = await api.getPortfoy(ilanId);
    if (d) sayfaGit('detay', d);
  } else if (blogSlug) {
    const d = await api.getBlogBySlugOrId(blogSlug);
    if (d) sayfaGit('blog-detay', d);
  }
}

/** Şifre sıfırlama modalını açar (UI; login akışı aynı kalır). */
function sifreSifirlaModalAc() {
  const m = document.getElementById('sifre-sifirlama-modal');
  if (!m) return;
  document.getElementById('ssm-adim1').style.display = '';
  document.getElementById('ssm-adim2').style.display = 'none';
  const email = document.getElementById('ssm-email');
  if (email) email.value = '';
  m.style.display = 'flex';
}

/**
 * Sıfırlama adım 1 — token talebi.
 * Mock: bilgilendirme; Server: ApiClient üzerinden.
 */
async function sifreSifirlaBaslat() {
  const email = document.getElementById('ssm-email')?.value?.trim();
  if (!email) { bildirim('E-posta gerekli', 'hata'); return; }
  const d = await api.save('auth/sifre-sifirlama-baslat', { email });
  if (d) {
    bildirim(d.mesaj || 'Talep alındı. Sunucu terminalini kontrol edin.', 'basari');
    document.getElementById('ssm-adim1').style.display = 'none';
    document.getElementById('ssm-adim2').style.display = '';
  }
}

/** Sıfırlama adım 2 — token + yeni şifre. */
async function sifreSifirlaTogele() {
  const token = document.getElementById('ssm-token')?.value?.trim();
  const yeni = document.getElementById('ssm-yeni')?.value || '';
  const tekrar = document.getElementById('ssm-yeni2')?.value || '';
  if (!token || !yeni) { bildirim('Token ve yeni şifre gerekli', 'hata'); return; }
  if (yeni.length < 8) { bildirim('Şifre en az 8 karakter olmalı', 'hata'); return; }
  if (yeni !== tekrar) { bildirim('Şifreler eşleşmiyor', 'hata'); return; }
  const d = await api.save('auth/sifre-sifirlama-tamamla', { token, yeni_sifre: yeni });
  if (d) {
    bildirim('Şifre güncellendi. Giriş yapabilirsiniz.', 'basari');
    document.getElementById('sifre-sifirlama-modal').style.display = 'none';
  }
}


// ── Global export (HTML onclick / inline handlers) ────────────────────────────
window.syncTokenFromApi = syncTokenFromApi;
window.clearSessionLocal = clearSessionLocal;
window.bildirim = bildirim;
window.sayfaGit = sayfaGit;
window.geriGit = geriGit;
window.girisYap = girisYap;
window.cikisYap = cikisYap;
window.authGuncelle = authGuncelle;
window.adminKontrol = adminKontrol;
window.katYukle = katYukle;
window.anaKatDegisti = anaKatDegisti;
window.altKatDegisti = altKatDegisti;
window.dinamikOlustur = dinamikOlustur;
window.dinamikOku = dinamikOku;
window.kartOlustur = kartOlustur;
window.anaSayfaYukle = anaSayfaYukle;
window.anaGridYukle = anaGridYukle;
window.vitrinYukle = vitrinYukle;
window.katFiltrele = katFiltrele;
window.heroAra = heroAra;
window.katFiltrelIlan = katFiltrelIlan;
window.ilanYukle = ilanYukle;
window.aramaBekle = aramaBekle;
window.detayGoster = detayGoster;
window.detaySahipResmiYukle = detaySahipResmiYukle;
window.gFotoDegis = gFotoDegis;
window.iletisimAc = iletisimAc;
window.istekGonder = istekGonder;
window.modalAc = modalAc;
window.modalKapat = modalKapat;
window.ilanDuzenle = ilanDuzenle;
window.portfoyKaydet = portfoyKaydet;
window.resimYukle = resimYukle;
window.resimGridGuncelle = resimGridGuncelle;
window.resimSiralaKaydet = resimSiralaKaydet;
window.kapakYap = kapakYap;
window.resimSil = resimSil;
window.adminSayfa = adminSayfa;
window.adminPortfoyler = adminPortfoyler;
window.durumDegistir = durumDegistir;
window.ilanSilAdmin = ilanSilAdmin;
window.ilanSilDetay = ilanSilDetay;
window.adminBelge = adminBelge;
window.belgeIsle = belgeIsle;
window.belgeIsleDogrudan = belgeIsleDogrudan;
window.belgeYayinla = belgeYayinla;
window.belgeFormAc = belgeFormAc;
window.adminIstekler = adminIstekler;
window.istekDurum = istekDurum;
window.adminKullanicilar = adminKullanicilar;
window.kullaniciOnayla = kullaniciOnayla;
window.kullaniciOnayKaldir = kullaniciOnayKaldir;
window.kullaniciOnayDegis = kullaniciOnayDegis;
window.kullaniciEkle = kullaniciEkle;
window.kullaniciSil = kullaniciSil;
window.kullaniciReddet = kullaniciReddet;
window.adminAyarlar = adminAyarlar;
window.logoYukle = logoYukle;
window.logoSil = logoSil;
window.logoOnizlemeGuncelle = logoOnizlemeGuncelle;
window.temaUygula = temaUygula;
window.adminHesabim = adminHesabim;
window.sifreGucGoster = sifreGucGoster;
window.profilKaydet = profilKaydet;
window.sifreDegistir = sifreDegistir;
window.ayarlariKaydet = ayarlariKaydet;
window.siteAyarlariUygula = siteAyarlariUygula;
window.waIkon = waIkon;
window.igIkon = igIkon;
window.fbIkon = fbIkon;
window.favGetir = favGetir;
window.favKaydet = favKaydet;
window.favKontrol = favKontrol;
window.favToggleId = favToggleId;
window.favToggle = favToggle;
window.favBantGuncelle = favBantGuncelle;
window.sadeceFavGoster = sadeceFavGoster;
window.favSifirla = favSifirla;
window.karsEkle = karsEkle;
window.karsBantGuncelle = karsBantGuncelle;
window.karsKaldir = karsKaldir;
window.karsSifirla = karsSifirla;
window.karsGoster = karsGoster;
window.gelismisFiltreToogle = gelismisFiltreToogle;
window.filtreleriSifirla = filtreleriSifirla;
window.haritaIlanAc = haritaIlanAc;
window.gorunumDegis = gorunumDegis;
window.haritaYukle = haritaYukle;
window.ilanPaylas = ilanPaylas;
window.seoGuncelle = seoGuncelle;
window.blogListeYukle = blogListeYukle;
window.blogEtiketFiltre = blogEtiketFiltre;
window.blogIcerikRender = blogIcerikRender;
window.editorEkle = editorEkle;
window.blogKartOlustur = blogKartOlustur;
window.blogDetayGoster = blogDetayGoster;
window.adminBlog = adminBlog;
window.blogModalAc = blogModalAc;
window.blogKaydet = blogKaydet;
window.blogDurumDegis = blogDurumDegis;
window.blogDuzenle = blogDuzenle;
window.blogSilAdmin = blogSilAdmin;
window.blogKapakYukle = blogKapakYukle;
window.profilResmiYukle = profilResmiYukle;
window.profilResmiSil = profilResmiSil;
window.pdfIndir = pdfIndir;
window.fiyatAnaliziGoster = fiyatAnaliziGoster;
window.adminFiyatAnaliziGenel = adminFiyatAnaliziGenel;
window.aiAyarlariKaydet = aiAyarlariKaydet;
window.blogResimModalAc = blogResimModalAc;
window.blogResimSecildi = blogResimSecildi;
window.blogResimIcerigeEkle = blogResimIcerigeEkle;
window.kayitModalAc = kayitModalAc;
// ── CMS Admin Sayfaları ──────────────────────────────────────────────────────
const esc = s => String(s||'').replace(/[&<>"']/g, c=>`&#${c.charCodeAt(0)};`);
const safeJsonParse = (s, d = {}) => { try { return JSON.parse(s); } catch { return d; } };

// ─── Menü Şablonları (görsel ön tanımlı yapılar) ────────────────────────────

const MENU_TEMPLATES = [
  { id:'header-klasik', ad:'Klasik Header', ikon:'🏠', lok:'header',
    aciklama:'Ana Sayfa, İlanlar, Blog, İletişim — standart üst menü',
    ogeler:[
      {baslik:'Ana Sayfa', url:'/'}, {baslik:'İlanlar', url:'/#ilanlar'},
      {baslik:'Blog', url:'/#blog'}, {baslik:'İletişim', url:'/#iletisim'},
    ]},
  { id:'header-minimal', ad:'Minimal Header', ikon:'↗️', lok:'header',
    aciklama:'Sadece Ana Sayfa + İletişim — sade tasarım',
    ogeler:[{baslik:'Ana Sayfa', url:'/'}, {baslik:'İletişim', url:'/#iletisim'}]},
  { id:'footer-klasik', ad:'Klasik Footer', ikon:'📌', lok:'footer',
    aciklama:'Kurumsal + Hızlı Linkler + Gizlilik — alt bilgi menüsü',
    ogeler:[
      {baslik:'Kurumsal', url:'/kurumsal'}, {baslik:'Hızlı Linkler', url:'/#ilanlar'},
      {baslik:'Gizlilik Politikası', url:'/gizlilik'}, {baslik:'Kullanım Şartları', url:'/kosullar'},
    ]},
  { id:'footer-minimal', ad:'Minimal Footer', ikon:'🔗', lok:'footer',
    aciklama:'İletişim + Sosyal Medya — sade alt menü',
    ogeler:[{baslik:'İletişim', url:'/#iletisim'}, {baslik:'Blog', url:'/#blog'}]},
  { id:'sidebar-dashboard', ad:'Panel Sidebar', ikon:'📊', lok:'sidebar',
    aciklama:'Admin paneli için: Dashboard, İstatistikler, Raporlar',
    ogeler:[
      {baslik:'Dashboard', url:'/admin'}, {baslik:'İstatistikler', url:'/admin/istatistik'},
      {baslik:'Raporlar', url:'/admin/raporlar'}, {baslik:'Ayarlar', url:'/admin/ayarlar'},
    ]},
  { id:'sosyal-medya', ad:'Sosyal Medya', ikon:'🌐', lok:'footer',
    aciklama:'Sosyal medya bağlantıları: Instagram, Facebook, WhatsApp',
    ogeler:[
      {baslik:'Instagram', url:'https://instagram.com', ikon:'📸'},
      {baslik:'Facebook', url:'https://facebook.com', ikon:'👍'},
      {baslik:'WhatsApp', url:'https://wa.me/', ikon:'💬'},
    ]},
];

function menuSablonGorsel(sablon, index) {
  return `<div class="menu-sablon-kart" onclick="menuSablonUygula(${index})">
    <div class="menu-sablon-ikon">${esc(sablon.ikon)}</div>
    <div class="menu-sablon-ad">${esc(sablon.ad)}</div>
    <div class="menu-sablon-aciklama">${esc(sablon.aciklama)}</div>
    <div class="menu-sablon-ogeler">${sablon.ogeler.map(o => `<span>${o.ikon||'•'} ${esc(o.baslik)}</span>`).join('')}</div>
    <button class="btn btn-sm btn-kirm menu-sablon-btn">Uygula</button>
  </div>`;
}

window.menuSablonUygula = async function(index) {
  const s = MENU_TEMPLATES[index];
  if (!s) return;
  if (!confirm(`"${s.ad}" menü şablonu uygulansın mı?\nMevcut menülere eklenir.`)) return;
  try {
    const slug = s.id;
    const mevcut = await api.request(`/api/admin/menuler`).catch(()=>[]);
    let menu = mevcut.find(m => m.slug === slug);
    if (!menu) {
      await api.request('/api/admin/menuler', {
        method:'POST',
        body:JSON.stringify({slug, ad:s.ad, lokasyon:s.lok}),
      });
      menu = { slug };
    }
    const yeni = await api.request(`/api/admin/menuler`).catch(()=>[]);
    const m = yeni.find(x => x.slug === slug);
    if (!m) return bildirim('Menü oluşturulamadı','hata');
    for (let i = 0; i < s.ogeler.length; i++) {
      const o = s.ogeler[i];
      const harici = o.url?.startsWith('http');
      await api.request(`/api/admin/menuler/${m.id}/ogeler`, {
        method:'POST',
        body:JSON.stringify({menu_id:m.id, baslik:o.baslik, hedef_tip:harici?'harici':'dahili', hedef_url:o.url||'/', ikon:o.ikon||'', sira:i, aktif:true}),
      });
    }
    bildirim(`"${s.ad}" şablonu uygulandı ✅`,'basari');
    adminMenuler();
  } catch(e) { bildirim('Hata: '+e.message,'hata'); }
};

// ─── Menü Ana Sayfası ──────────────────────────────────────────────────────

async function adminMenuler() {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  const menuler = await api.request('/api/admin/menuler').catch(()=>[]);

  let html = '<div class="admin-baslik">📋 Menü Yöneticisi</div>';
  html += '<div class="menu-editor">';

  // ── Görsel Şablonlar ────────────────────────────────────────────────────
  html += '<div class="tema-bolum"><div class="tema-bolum-baslik">Hazır Menü Şablonları</div>';
  html += '<div class="tema-bolum-aciklama">Beğendiğiniz bir menü yapısını seçip tek tıkla uygulayın</div>';
  html += '<div class="menu-sablon-grid">';
  MENU_TEMPLATES.forEach((s, i) => { html += menuSablonGorsel(s, i); });
  html += '</div></div>';

  // ── Mevcut Menüler ──────────────────────────────────────────────────────
  html += '<div class="tema-bolum"><div class="tema-bolum-baslik">Mevcut Menüleriniz</div>';
  html += '<div class="tema-bolum-aciklama">Aşağıdaki menüleri düzenleyebilir veya yenilerini ekleyebilirsiniz</div>';

  if (menuler && menuler.length) {
    html += '<div class="menu-liste">';
    for (const m of menuler) {
      const lokIkon = { header:'🏠', footer:'📌', sidebar:'📂' };
      html += `<div class="menu-kart">
        <div class="menu-kart-ust">
          <div class="menu-kart-baslik">
            <span class="menu-kart-ikon">${lokIkon[m.lokasyon]||'📋'}</span>
            <div><strong>${esc(m.ad)}</strong><div class="menu-kart-slug">${esc(m.slug)} · ${esc(m.lokasyon)}</div></div>
          </div>
          <label class="menu-toggle-label"><input type="checkbox"${m.aktif?' checked':''} onchange="menuAktifToggle(${m.id},this.checked)"><span class="menu-toggle-kut"></span></label>
        </div>
        <div class="menu-kart-alt">
          <button class="btn btn-sm btn-ntr" onclick="adminMenuOgelr(${m.id},'${esc(m.slug)}')">📋 Öğeleri Düzenle</button>
          <button class="btn btn-sm btn-cik" onclick="menuAdDuzenle(${m.id},'${esc(m.ad)}')">✏️ Ad</button>
          <button class="btn btn-sm btn-hat" onclick="menuSil(${m.id})">🗑️</button>
        </div>
      </div>`;
    }
    html += '</div>';
  } else {
    html += '<div class="bos-durum" style="margin:1rem 0"><div class="bos-ikon">📋</div><h3>Henüz menü yok</h3><p>Yukarıdaki şablonlardan birini seçin veya elle ekleyin</p></div>';
  }

  // ── Yeni Menü Ekle (gelişmiş) ──────────────────────────────────────────
  html += '<div class="menu-yeni-bar"><div class="menu-yeni-baslik">➕ Yeni Menü Ekle</div>';
  html += '<div class="menu-yeni-girdiler">';
  html += '<input id="ymn-ad" placeholder="Menü adı (örn: Ana Menü)" class="menu-yeni-input">';
  html += '<input id="ymn-slug" placeholder="slug (ana-menu)" class="menu-yeni-input">';
  html += '<select id="ymn-lok" class="menu-yeni-select"><option value="header">🏠 Header</option><option value="footer">📌 Footer</option><option value="sidebar">📂 Sidebar</option></select>';
  html += '<button class="btn btn-kirm" onclick="menuOlustur()">Oluştur</button>';
  html += '</div></div>';

  html += '</div></div>'; // .tema-bolum / .menu-editor
  ic.innerHTML = html;
}

// ─── Menü CRUD ─────────────────────────────────────────────────────────────

window.menuOlustur = async function() {
  const ad = document.getElementById('ymn-ad')?.value?.trim();
  const slug = document.getElementById('ymn-slug')?.value?.trim() || (ad ? ad.toLowerCase().replace(/[^a-z0-9]/g,'-').replace(/-+/g,'-') : '');
  if (!slug) return bildirim('Menü adı veya slug gerekli','hata');
  const lok = document.getElementById('ymn-lok')?.value || 'header';
  try {
    await api.request('/api/admin/menuler', { method:'POST', body:JSON.stringify({slug,ad:ad||slug,lokasyon:lok}) });
    bildirim(`"${ad||slug}" menüsü oluşturuldu ✅`,'basari');
    adminMenuler();
  } catch(e) { bildirim(e.message || 'Hata','hata'); }
};

window.menuSil = async function(id) {
  if (!confirm('Bu menü silinsin mi? (içindeki tüm öğeler de silinir)')) return;
  try {
    await api.request(`/api/admin/menuler/${id}`, { method:'DELETE' });
    bildirim('Menü silindi','basari');
    adminMenuler();
  } catch(e) { bildirim(e.message,'hata'); }
};

window.menuAktifToggle = async function(id, aktif) {
  try {
    await api.request(`/api/admin/menuler/${id}`, { method:'PUT', body:JSON.stringify({aktif}) });
  } catch(e) { bildirim(e.message,'hata'); }
};

window.menuAdDuzenle = async function(id, eski) {
  const yeni = prompt('Menü adını girin:', eski);
  if (!yeni || yeni === eski) return;
  try {
    await api.request(`/api/admin/menuler/${id}`, { method:'PUT', body:JSON.stringify({ad:yeni}) });
    bildirim('Menü adı güncellendi','basari');
    adminMenuler();
  } catch(e) { bildirim(e.message,'hata'); }
};

// ─── Menü Öğeleri ──────────────────────────────────────────────────────────

let _aktifMenu = 0;

async function adminMenuOgelr(menuId, menuSlug) {
  _aktifMenu = menuId;
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  const ogeler = await api.request(`/api/admin/menuler/${menuId}/ogeler`).catch(()=>[]);

  let html = '<div class="admin-baslik" style="display:flex;align-items:center;gap:.75rem;flex-wrap:wrap">';
  html += `<button class="btn btn-sm btn-ntr" onclick="adminMenuler()" style="font-size:.8rem">← Menüler</button>`;
  html += `<span>📋 ${esc(menuSlug)} — Öğeler</span></div>`;
  html += '<div class="menu-oge-editor">';

  // ── Hızlı Ekle ──────────────────────────────────────────────────────────
  html += '<div class="menu-oge-ekle-bar">';
  html += '<input id="ymo-baslik" placeholder="Başlık (örn: Ana Sayfa)" class="menu-yeni-input" style="flex:1;min-width:120px">';
  html += '<input id="ymo-url" placeholder="URL (/iletisim)" class="menu-yeni-input" style="flex:1;min-width:140px">';
  html += `<select id="ymo-parent" class="menu-yeni-select" style="max-width:120px"><option value="">— Üst Düzey —</option>`;
  if (ogeler) ogeler.forEach(o => {
    html += `<option value="${o.id}">${esc(o.baslik)}</option>`;
  });
  html += '</select>';
  html += `<button class="btn btn-kirm btn-sm" onclick="menuOgeEkle(${menuId})">+ Ekle</button></div>`;

  if (ogeler && ogeler.length) {
    html += '<div class="menu-oge-liste">';
    // Düz listeyi hiyerarşik göster
    const ust = ogeler.filter(o => !o.parent_id);
    const cocuk = id => ogeler.filter(o => o.parent_id === id);

    for (const o of ust) {
      html += menuOgeKart(o, menuId);
      for (const c of cocuk(o.id)) {
        html += menuOgeKart(c, menuId, true);
      }
    }
    html += '</div>';
  } else {
    html += '<div class="bos-durum" style="margin:1.5rem 0"><div class="bos-ikon">📄</div><h3>Henüz öğe yok</h3><p>Yukarıdaki kutulara başlık ve URL yazıp ekleyin</p></div>';
  }

  html += '</div>'; // .menu-oge-editor
  ic.innerHTML = html;
}

function menuOgeKart(o, menuId, alt = false) {
  const lokIkon = o.ikon || (o.hedef_url?.startsWith('http') ? '🔗' : '📄');
  return `<div class="menu-oge-kart${alt?' menu-oge-alt':''}">
    <div class="menu-oge-kart-sira">
      <button class="btn btn-sm btn-ntr" onclick="menuOgeTasi(${o.id},${menuId},-1)" title="Yukarı">↑</button>
      <button class="btn btn-sm btn-ntr" onclick="menuOgeTasi(${o.id},${menuId},1)" title="Aşağı">↓</button>
    </div>
    <div class="menu-oge-kart-ic">
      <div class="menu-oge-kart-ikon">${lokIkon}</div>
      <div class="menu-oge-kart-bilgi">
        <div class="menu-oge-kart-baslik">${esc(o.baslik)}</div>
        <div class="menu-oge-kart-url">${esc(o.hedef_url || o.hedef_tip || '—')}</div>
      </div>
    </div>
    <label class="menu-toggle-label"><input type="checkbox"${o.aktif?' checked':''} onchange="menuOgeAktifToggle(${o.id},${menuId},this.checked)"><span class="menu-toggle-kut"></span></label>
    <div class="menu-oge-kart-aks">
      <button class="btn btn-sm btn-cik" onclick="menuOgeDuzenle(${o.id},${menuId})">✏️</button>
      <button class="btn btn-sm btn-hat" onclick="menuOgeSil(${menuId},${o.id})">🗑️</button>
    </div>
  </div>`;
}

// ─── Menü Öğe CRUD ─────────────────────────────────────────────────────────

window.menuOgeEkle = async function(menuId) {
  const baslik = document.getElementById('ymo-baslik')?.value?.trim();
  if (!baslik) return bildirim('Başlık gerekli','hata');
  const url = document.getElementById('ymo-url')?.value?.trim() || '/';
  const parent = document.getElementById('ymo-parent')?.value;
  const harici = url.startsWith('http');
  try {
    await api.request(`/api/admin/menuler/${menuId}/ogeler`, {
      method:'POST',
      body:JSON.stringify({menu_id:menuId, baslik, hedef_tip:harici?'harici':'dahili', hedef_url:url, parent_id:parent||null, sira:0, aktif:true}),
    });
    bildirim('Öğe eklendi ✅','basari');
    adminMenuOgelr(menuId, '');
  } catch(e) { bildirim(e.message,'hata'); }
};

window.menuOgeSil = async function(menuId, itemId) {
  if (!confirm('Öğe silinsin mi?')) return;
  try {
    await api.request(`/api/admin/menu-ogeleri/${itemId}`, { method:'DELETE' });
    bildirim('Öğe silindi','basari');
    adminMenuOgelr(menuId, '');
  } catch(e) { bildirim(e.message,'hata'); }
};

window.menuOgeAktifToggle = async function(itemId, menuId, aktif) {
  try {
    await api.request(`/api/admin/menu-ogeleri/${itemId}`, { method:'PUT', body:JSON.stringify({aktif}) });
  } catch(e) { bildirim(e.message,'hata'); }
};

window.menuOgeTasi = async function(itemId, menuId, yon) {
  try {
    const ogeler = await api.request(`/api/admin/menuler/${menuId}/ogeler`).catch(()=>[]);
    const idx = ogeler.findIndex(o => o.id === itemId);
    if (idx < 0) return;
    const hedef = idx + yon;
    if (hedef < 0 || hedef >= ogeler.length) return;
    const items = ogeler.map((o, i) => ({ id: o.id, parent_id: o.parent_id, sira: i }));
    // swap sıraları
    const tmp = items[idx].sira;
    items[idx].sira = items[hedef].sira;
    items[hedef].sira = tmp;
    await api.request('/api/admin/menu-ogeleri/sirala', { method:'PUT', body:JSON.stringify({items}) });
    adminMenuOgelr(menuId, '');
  } catch(e) { bildirim(e.message,'hata'); }
};

window.menuOgeDuzenle = async function(itemId, menuId) {
  const yeniBaslik = prompt('Yeni başlık:');
  if (!yeniBaslik) return;
  try {
    await api.request(`/api/admin/menu-ogeleri/${itemId}`, { method:'PUT', body:JSON.stringify({baslik:yeniBaslik}) });
    bildirim('Öğe güncellendi ✅','basari');
    adminMenuOgelr(menuId, '');
  } catch(e) { bildirim(e.message,'hata'); }
};

// ── Sayfalar ─────────────────────────────────────────────────────────────────

async function adminSayfalar() {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  const sayfalar = await api.request('/api/admin/sayfalar').catch(()=>[]);
  const SABLONLAR = ['default','landing','corporate','minimal','estate-modern','sidebar'];
  let html = '<div class="admin-baslik">Sayfalar <button class="btn btn-kirm btn-sm" onclick="sayfaDuzenleModal()" style="margin-left:auto">+ Yeni Sayfa</button></div>';

  // Hızlı新建 bar
  html += '<div style="margin-bottom:1rem;display:flex;gap:6px;flex-wrap:wrap;align-items:center;background:var(--beyaz);padding:.85rem 1rem;border-radius:var(--r);border:1px solid var(--kumtasi)">';
  html += '<input id="ysf-baslik" placeholder="Sayfa başlığı" style="flex:1;min-width:180px" class="form-girdi">';
  html += '<input id="ysf-slug" placeholder="slug (boşsa otomatik)" style="width:160px" class="form-girdi">';
  html += '<select id="ysf-durum" class="form-girdi"><option value="Taslak">Taslak</option><option value="Yayınla">Yayınla</option></select>';
  html += '<button class="btn btn-kirm" onclick="sayfaOlustur()">+ Ekle</button></div>';

  if (sayfalar && sayfalar.length) {
    html += '<div class="tablo-kont"><table class="tablo"><thead><tr><th>Başlık</th><th>Slug</th><th>Durum</th><th>Şablon</th><th>Güncelleme</th><th></th></tr></thead><tbody>';
    sayfalar.forEach(s => {
      html += `<tr>
        <td><strong>${esc(s.baslik)}</strong>
          ${s.ozet ? `<div style="font-size:.74rem;color:var(--gri-metin);margin-top:.15rem">${esc((s.ozet||'').slice(0,60))}${s.ozet.length>60?'…':''}</div>` : ''}
        </td>
        <td><code style="font-size:.78rem">${esc(s.slug)}</code></td>
        <td><span class="durum-pill ${s.durum === 'Yayınla' ? 'dp-Aktif' : 'dp-Taslak'}">${s.durum === 'Yayınla' ? '✅ Yayında' : '📝 Taslak'}</span></td>
        <td style="font-size:.8rem">${esc(s.sablon || 'default')}</td>
        <td style="font-size:.78rem;color:var(--gri-metin)">${(s.guncelleme||'').slice(0,10)}</td>
        <td><div class="tablo-eylemler">
          <button class="btn btn-cik btn-sm" onclick="sayfaDuzenleModal(${s.id})" title="Düzenle">✏️</button>
          ${s.durum === 'Yayınla' ? `<button class="btn btn-sm" style="background:#FEF3C7;color:#92400E" onclick="sayfaDurumTog(${s.id},'Taslak')" title="Taslak">⏸</button>`
                                : `<button class="btn btn-sm" style="background:#D1FAE5;color:#065F46" onclick="sayfaDurumTog(${s.id},'Yayınla')" title="Yayınla">▶</button>`}
          <button class="btn btn-hat btn-sm" onclick="sayfaSil(${s.id})" title="Sil">🗑️</button>
        </div></td>
      </tr>`;
    });
    html += '</tbody></table></div>';
  } else {
    html += '<div class="bos-durum"><div class="bos-ikon">📄</div><h3>Henüz sayfa yok</h3><p>Yeni bir CMS sayfası ekleyin</p></div>';
  }
  ic.innerHTML = html;
}

window.sayfaOlustur = async function() {
  const baslik = document.getElementById('ysf-baslik')?.value?.trim();
  let slug = document.getElementById('ysf-slug')?.value?.trim();
  const durum = document.getElementById('ysf-durum')?.value || 'Taslak';
  if (!baslik) return bildirim('Başlık gerekli','hata');
  if (!slug) slug = baslik.toLowerCase()
    .replace(/ı/g,'i').replace(/ş/g,'s').replace(/ç/g,'c').replace(/ü/g,'u').replace(/ö/g,'o').replace(/ğ/g,'g')
    .replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
  try {
    const r = await api.request('/api/admin/sayfalar', { method:'POST', body:JSON.stringify({baslik,slug,durum}) });
    bildirim('Sayfa oluşturuldu','basari');
    if (r?.id) sayfaDuzenleModal(r.id); else adminSayfalar();
  } catch(e) { bildirim(e.message,'hata'); }
};

window.sayfaSil = async function(id) {
  if (!confirm('Sayfa silinsin mi? Bu sayfaya giden menü öğeleri de etkilenecek.')) return;
  try {
    await api.request(`/api/admin/sayfalar/${id}`, { method:'DELETE' });
    bildirim('Sayfa silindi','basari');
    adminSayfalar();
  } catch(e) { bildirim(e.message,'hata'); }
};

window.sayfaDurumTog = async function(id, durum) {
  try {
    await api.request(`/api/admin/sayfalar/${id}`, { method:'PUT', body:JSON.stringify({durum}) });
    bildirim('Durum: ' + durum, 'basari');
    adminSayfalar();
  } catch(e) { bildirim(e.message,'hata'); }
};

// Tam fonksiyonlu sayfa edit modalı — içerik, özet, SEO, kapak, durum, şablon
window.sayfaDuzenleModal = async function(id) {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';

  let sayfa = null;
  if (id) {
    try { sayfa = await api.request(`/api/admin/sayfalar/${id}`); } catch {}
  }
  const yeniMi = !sayfa;
  const s = sayfa || { baslik:'', slug:'', ozet:'', icerik:'', durum:'Taslak', sablon:'default',
                       seo_baslik:'', seo_aciklama:'', seo_anahtar_kelimeler:'', kapak_resim:'' };
  const SABLONLAR = ['default','landing','corporate','minimal','estate-modern','sidebar'];

  ic.innerHTML = `
    <div class="admin-baslik" style="display:flex;align-items:center;gap:.75rem;flex-wrap:wrap">
      <button class="btn btn-sm btn-ntr" onclick="adminSayfalar()">← Geri</button>
      <span>${yeniMi ? 'Yeni Sayfa' : 'Sayfayı Düzenle'}</span>
    </div>
    <div style="max-width:840px;display:flex;flex-direction:column;gap:1rem">
      <div class="form-grup"><label class="form-etiket z">Başlık</label>
        <input class="form-girdi" id="sdf-baslik" value="${esc(s.baslik)}" placeholder="Sayfa başlığı"></div>
      <div class="form-ikili">
        <div class="form-grup"><label class="form-etiket z">Slug</label>
          <input class="form-girdi" id="sdf-slug" value="${esc(s.slug)}" placeholder="ornek-sayfa"></div>
        <div class="form-grup"><label class="form-etiket">Durum</label>
          <select class="form-girdi" id="sdf-durum">
            <option ${s.durum==='Taslak'?'selected':''}>Taslak</option>
            <option ${s.durum==='Yayınla'?'selected':''}>Yayınla</option>
            <option ${s.durum==='Arşiv'?'selected':''}>Arşiv</option>
          </select></div>
      </div>
      <div class="form-grup"><label class="form-etiket">Kısa Özet</label>
        <input class="form-girdi" id="sdf-ozet" value="${esc(s.ozet||'')}" placeholder="Listede görünecek kısa açıklama"></div>
      <div class="form-grup"><label class="form-etiket">İçerik (HTML destekler)</label>
        <div class="editor-araclari">
          <button onclick="sayfaEditorEkle('**','**')"><b>B</b></button>
          <button onclick="sayfaEditorEkle('&#60;h2&#62;','&#60;/h2&#62;')">H2</button>
          <button onclick="sayfaEditorEkle('&#60;p&#62;','&#60;/p&#62;')">¶</button>
          <button onclick="sayfaEditorEkle('&#60;a href=\\'\\' target=\\'_blank\\'&#62;','&#60;/a&#62;')">🔗</button>
        </div>
        <textarea class="blog-editor" id="sdf-icerik" rows="12" placeholder="Sayfa içeriği (HTML)…">${esc(s.icerik||'')}</textarea>
      </div>
      <div class="form-ikili">
        <div class="form-grup"><label class="form-etiket">Şablon</label>
          <select class="form-girdi" id="sdf-sablon">
            ${SABLONLAR.map(sb => `<option ${s.sablon===sb?'selected':''} value="${sb}">${sb}</option>`).join('')}
          </select></div>
        <div class="form-grup"><label class="form-etiket">Kapak Resmi URL</label>
          <input class="form-girdi" id="sdf-kapak" value="${esc(s.kapak_resim||'')}" placeholder="/static/uploads/... veya https://…"></div>
      </div>
      <details style="border:1px solid var(--kumtasi);border-radius:var(--r);padding:.5rem 1rem">
        <summary style="cursor:pointer;font-weight:600;color:var(--gri-metin)">🔍 SEO Ayarları</summary>
        <div style="margin-top:.75rem;display:flex;flex-direction:column;gap:.75rem">
          <div class="form-grup"><label class="form-etiket">SEO Başlık</label>
            <input class="form-girdi" id="sdf-seo-baslik" value="${esc(s.seo_baslik||'')}" placeholder="Boşsa sayfa başlığı kullanılır"></div>
          <div class="form-grup"><label class="form-etiket">SEO Açıklama</label>
            <input class="form-girdi" id="sdf-seo-aciklama" value="${esc(s.seo_aciklama||'')}" placeholder="Meta description"></div>
          <div class="form-grup"><label class="form-etiket">SEO Anahtar Kelimeler</label>
            <input class="form-girdi" id="sdf-seo-anahtar" value="${esc(s.seo_anahtar_kelimeler||'')}" placeholder="virgülle ayırın"></div>
        </div>
      </details>
      <div style="display:flex;gap:.75rem;align-items:center;margin-top:.5rem">
        <button class="btn btn-kirm btn-lg" onclick="sayfaKaydet(${id||'null'})">💾 ${yeniMi?'Oluştur':'Kaydet'}</button>
        <button class="btn btn-ntr" onclick="adminSayfalar()">Vazgeç</button>
        ${!yeniMi && s.slug ? `<a href="#/sayfa/${esc(s.slug)}" target="_blank" class="btn btn-ntr btn-sm" style="text-decoration:none">👁 Önizle</a>` : ''}
      </div>
    </div>`;
};

window.sayfaEditorEkle = function(once, sonra) {
  const ta = document.getElementById('sdf-icerik');
  if (!ta) return;
  const start = ta.selectionStart, end = ta.selectionEnd;
  const secili = ta.value.substring(start, end);
  const yeni = ta.value.substring(0, start) + once + secili + sonra + ta.value.substring(end);
  ta.value = yeni;
  ta.selectionStart = start + once.length;
  ta.selectionEnd = start + once.length + secili.length;
  ta.focus();
};

window.sayfaKaydet = async function(id) {
  const baslik = document.getElementById('sdf-baslik')?.value?.trim();
  if (!baslik) return bildirim('Başlık gerekli','hata');
  let slug = document.getElementById('sdf-slug')?.value?.trim();
  if (!slug) slug = baslik.toLowerCase().replace(/ı/g,'i').replace(/ş/g,'s').replace(/ç/g,'c').replace(/ü/g,'u').replace(/ö/g,'o').replace(/ğ/g,'g').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
  const data = {
    baslik, slug,
    ozet:  document.getElementById('sdf-ozet')?.value || '',
    icerik: document.getElementById('sdf-icerik')?.value || '',
    durum: document.getElementById('sdf-durum')?.value || 'Taslak',
    sablon: document.getElementById('sdf-sablon')?.value || 'default',
    kapak_resim: document.getElementById('sdf-kapak')?.value || '',
    seo_baslik: document.getElementById('sdf-seo-baslik')?.value || '',
    seo_aciklama: document.getElementById('sdf-seo-aciklama')?.value || '',
    seo_anahtar_kelimeler: document.getElementById('sdf-seo-anahtar')?.value || '',
  };
  try {
    if (id) {
      await api.request(`/api/admin/sayfalar/${id}`, { method:'PUT', body:JSON.stringify(data) });
      bildirim('Sayfa güncellendi ✅','basari');
    } else {
      const r = await api.request('/api/admin/sayfalar', { method:'POST', body:JSON.stringify(data) });
      bildirim('Sayfa oluşturuldu ✅','basari');
      if (r?.id) { sayfaDuzenleModal(r.id); return; }
    }
    adminSayfalar();
  } catch(e) { bildirim(e.message,'hata'); }
};

// ── Widget'lar ───────────────────────────────────────────────────────────────

async function adminWidgetler() {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  const widgetlar = await api.request('/api/admin/widgets').catch(()=>[]);
  let html = '<div class="admin-baslik">Widget\'lar <button class="btn btn-kirm btn-sm" onclick="widgetDuzenleModal()" style="margin-left:auto">+ Yeni Widget</button></div>';

  // Widget tipleri ve konumları (widget-renderer.js ile uyumlu)
  const TIP_LISTESI = {
    'html': 'Serbest HTML',
    'contact-form': 'İletişim Formu',
    'cookie-banner': 'Çerez Bildirimi',
    'social-bar': 'Sosyal Medya Çubuğu',
    'whatsapp': 'WhatsApp Butonu',
    'google-maps': 'Google Maps',
    'telefon-butonu': 'Telefon Butonu',
    'instagram-feed': 'Instagram Beslemesi',
    'info-kart': 'Bilgi Kartı',
    'embed': 'Embed / Script',
    'script': 'Script',
    'link': 'Bağlantı',
  };
  const KONUM_LISTESI = {
    'home-top': 'Anasayfa Üstü',
    'home-bottom': 'Anasayfa Altı',
    'anasayfa-top': 'Anasayfa Üstü (alt)',
    'anasayfa-bottom': 'Anasayfa Alta',
    'footer-top': 'Footer Üstü',
    'all-pages': 'Tüm Sayfalarda',
    'sidebar': 'Sidebar',
    'header': 'Header',
    'footer': 'Footer',
    'floating': 'Sabit (Kayan)',
    '': 'Yer Belirtilmedi',
  };
  // Yardımcı: tip etiketi
  const tipEtiket = t => TIP_LISTESI[t] || t || '—';
  const konumEtiket = k => KONUM_LISTESI[k] || k || '—';

  if (widgetlar && widgetlar.length) {
    html += '<div class="tablo-kont"><table class="tablo"><thead><tr><th>Anahtar</th><th>Ad</th><th>Tip</th><th>Konum</th><th>Sıra</th><th>Aktif</th><th></th></tr></thead><tbody>';
    widgetlar.forEach(w => {
      html += `<tr>
        <td><code style="font-size:.78rem">${esc(w.anahtar)}</code></td>
        <td><strong>${esc(w.ad)}</strong>
          ${w.aciklama ? `<div style="font-size:.72rem;color:var(--gri-metin)">${esc(w.aciklama)}</div>` : ''}
        </td>
        <td><span style="font-size:.78rem;background:var(--krem);padding:.2rem .5rem;border-radius:4px">${esc(tipEtiket(w.tip))}</span></td>
        <td style="font-size:.8rem">${esc(konumEtiket(w.konum))}</td>
        <td style="font-size:.82rem;color:var(--gri-metin);text-align:center">${w.sira ?? 0}</td>
        <td>${w.aktif ? '✅' : '❌'}</td>
        <td><div class="tablo-eylemler">
          <button class="btn btn-cik btn-sm" title="Düzenle" onclick="widgetDuzenleModal(${w.id})">✏️</button>
          <button class="btn btn-sm ${w.aktif ? 'btn-cik' : 'btn-yes'}" title="${w.aktif?'Devre dışı':'Aktifleştir'}" onclick="widgetToggle(${w.id},${w.aktif ? 0 : 1})">${w.aktif ? '⏸' : '▶'}</button>
          <button class="btn btn-hat btn-sm" title="Sil" onclick="widgetSil(${w.id})">🗑️</button>
        </div></td>
      </tr>`;
    });
    html += '</tbody></table></div>';
    html += '<div style="margin-top:.75rem;font-size:.78rem;color:var(--gri-metin)">💡 Widget\'lar <code>konum</code> alanına göre <code>data-widget-container="..."</code> nitelikli elementlere yerleşir. Eğer DOM'da ilgili konteyner yoksa otomatik oluşturulur.</div>';
  } else {
    html += '<div class="bos-durum"><div class="bos-ikon">🧩</div><h3>Henüz widget yok</h3><p>+ Yeni Widget ile başlayın</p></div>';
  }
  ic.innerHTML = html;
}

window.widgetToggle = async function(id, aktif) {
  try {
    await api.request(`/api/admin/widgets/${id}`, { method:'PUT', body:JSON.stringify({aktif:!!aktif}) });
    bildirim(`Widget ${aktif ? 'aktifleştirildi' : 'devre dışı bırakıldı'}`,'basari');
    adminWidgetler();
  } catch(e) { bildirim(e.message,'hata'); }
};

window.widgetSil = async function(id) {
  if (!confirm('Widget silinsin mi?')) return;
  try {
    await api.request(`/api/admin/widgets/${id}`, { method:'DELETE' });
    bildirim('Widget silindi','basari');
    adminWidgetler();
  } catch(e) { bildirim(e.message,'hata'); }
};

// Tam fonksiyonelu widget edit/create modalı
window.widgetDuzenleModal = async function(id) {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';

  let w = null;
  if (id) {
    try { w = await api.request(`/api/admin/widgets/${id}`); } catch {}
  }
  const yeniMi = !w;
  const d = w || { anahtar:'', ad:'', aciklama:'', tip:'html', aktif:false, ayarlar:'{}', konum:'all-pages', sira:0, icerik:'' };

  // ayarlar JSON'ı olabilir; "icerik" genelde serbest HTML içerir
  let ayarlarObj = {};
  try { ayarlarObj = JSON.parse(d.ayarlar || '{}'); } catch {}
  const icerik = d.icerik || ayarlarObj.icerik || '';

  const TIP_OPTS = [
    ['html','Serbest HTML'], ['contact-form','İletişim Formu'],
    ['cookie-banner','Çerez Bildirimi'], ['social-bar','Sosyal Medya Çubuğu'],
    ['whatsapp','WhatsApp Butonu'], ['google-maps','Google Maps'],
    ['telefon-butonu','Telefon Butonu'], ['instagram-feed','Instagram Beslemesi'],
    ['info-kart','Bilgi Kartı'], ['embed','Embed / Script'],
    ['script','Script'], ['link','Bağlantı'],
  ];
  const KONUM_OPTS = [
    ['all-pages','Tüm Sayfalarda'], ['home-top','Anasayfa Üstü'],
    ['home-bottom','Anasayfa Altı'], ['anasayfa-top','Anasayfa Üstü (alt)'],
    ['anasayfa-bottom','Anasayfa Alta'], ['footer-top','Footer Üstü'],
    ['sidebar','Sidebar'], ['header','Header'],
    ['footer','Footer'], ['floating','Sabit (Kayan)'],
  ];

  ic.innerHTML = `
    <div class="admin-baslik" style="display:flex;align-items:center;gap:.75rem;flex-wrap:wrap">
      <button class="btn btn-sm btn-ntr" onclick="adminWidgetler()">← Geri</button>
      <span>${yeniMi ? 'Yeni Widget' : 'Widget Düzenle'}</span>
    </div>
    <div style="max-width:760px;display:flex;flex-direction:column;gap:1rem">
      <div class="form-ikili">
        <div class="form-grup"><label class="form-etiket z">Anahtar (benzersiz)</label>
          <input class="form-girdi" id="wg-anahtar" value="${esc(d.anahtar)}" placeholder="örn: whatsapp-banner" ${yeniMi?'':'readonly style="background:var(--krem)"'} ${yeniMi?'':'disabled'}></div>
        <div class="form-grup"><label class="form-etiket z">Ad</label>
          <input class="form-girdi" id="wg-ad" value="${esc(d.ad)}" placeholder="Widget adı"></div>
      </div>
      <div class="form-grup"><label class="form-etiket">Açıklama (opsiyonel)</label>
        <input class="form-girdi" id="wg-aciklama" value="${esc(d.aciklama||'')}" placeholder="Kısa açıklama"></div>
      <div class="form-ikili">
        <div class="form-grup"><label class="form-etiket z">Tip</label>
          <select class="form-girdi" id="wg-tip">
            ${TIP_OPTS.map(([v,l]) => `<option value="${v}" ${d.tip===v?'selected':''}>${l}</option>`).join('')}
          </select></div>
        <div class="form-grup"><label class="form-etiket z">Konum</label>
          <select class="form-girdi" id="wg-konum">
            ${KONUM_OPTS.map(([v,l]) => `<option value="${v}" ${d.konum===v?'selected':''}>${l}</option>`).join('')}
          </select></div>
      </div>
      <div class="form-ikili">
        <div class="form-grup"><label class="form-etiket">Sıra</label>
          <input class="form-girdi" id="wg-sira" type="number" value="${d.sira ?? 0}" style="width:120px"></div>
        <div class="form-grup"><label class="form-etiket">Aktif</label>
          <label style="display:flex;align-items:center;gap:.5rem;padding-top:.5rem">
            <input type="checkbox" id="wg-aktif" ${d.aktif?'checked':''} style="width:16px;height:16px;accent-color:var(--kiremit)">
            <span style="font-size:.85rem">Bu widget yayında</span>
          </label></div>
      </div>
      <div class="form-grup"><label class="form-etiket">İçerik / HTML / Embed</label>
        <div style="font-size:.72rem;color:var(--gri-metin);margin-bottom:.4rem">
          Tip <code>html</code>, <code>google-maps</code>, <code>instagram-feed</code>, <code>info-kart</code> için buradaki HTML kullanılır.
          Diğer tiplerde ayarlar JSON olarak da işlenebilir.
        </div>
        <textarea class="blog-editor" id="wg-icerik" rows="8" placeholder="<div>Widget içeriği…</div>">${esc(icerik)}</textarea>
      </div>
      <div style="display:flex;gap:.75rem;margin-top:.5rem">
        <button class="btn btn-kirm btn-lg" onclick="widgetKaydet(${id||'null'})">💾 ${yeniMi?'Oluştur':'Kaydet'}</button>
        <button class="btn btn-ntr" onclick="adminWidgetler()">Vazgeç</button>
      </div>
    </div>`;
};

window.widgetKaydet = async function(id) {
  const anahtar = (document.getElementById('wg-anahtar')?.value || '').trim().toLowerCase().replace(/[^a-z0-9_-]/g,'-').replace(/^-+|-+$/g,'');
  const ad = (document.getElementById('wg-ad')?.value || '').trim();
  if (!anahtar || !ad) return bildirim('Anahtar ve ad gerekli','hata');
  const tip = document.getElementById('wg-tip').value;
  const konum = document.getElementById('wg-konum').value;
  const sira = parseInt(document.getElementById('wg-sira').value) || 0;
  const aktif = document.getElementById('wg-aktif').checked;
  const aciklama = document.getElementById('wg-aciklama')?.value || '';
  const icerik = document.getElementById('wg-icerik')?.value || '';
  // ayarlar JSON'ında icerik sakla — widget-renderer.js uyumlu
  const ayarlar = JSON.stringify({ icerik });
  const payload = { anahtar, ad, aciklama, tip, aktif, ayarlar, konum, sira };
  try {
    if (id) {
      // anahtar'ı değiştiremeyiz (disabled)
      await api.request(`/api/admin/widgets/${id}`, { method:'PUT', body:JSON.stringify({ad, aciklama, tip, aktif, ayarlar, konum, sira}) });
      bildirim('Widget güncellendi ✅','basari');
    } else {
      await api.request('/api/admin/widgets', { method:'POST', body:JSON.stringify(payload) });
      bildirim('Widget oluşturuldu ✅','basari');
    }
    adminWidgetler();
  } catch(e) { bildirim(e.message,'hata'); }
};

// ── Tema — taslak (önizleme + toplu kaydet) ──────────────────────────────────

const TEMA_PALETLERI = [
  { id:'kiremit',    ad:'Kiremit',      renkler:['#C45C35','#A34A28','#FAF7F2','#2D2016'] },
  { id:'green',      ad:'Zeytun Yeşil', renkler:['#2D7D46','#1F5C33','#F0F7F2','#1A2E1A'] },
  { id:'navy',       ad:'Lacivert',    renkler:['#1A3C6B','#12295A','#EDF2F7','#0F1A2E'] },
  { id:'purple',     ad:'Mor',         renkler:['#6D28D9','#5B21B6','#F5F0FF','#1A0F2E'] },
  { id:'rose',       ad:'Gül Rox',     renkler:['#E11D48','#9F1239','#FFF1F2','#27171E'] },
  { id:'gold',       ad:'Altın',       renkler:['#D97706','#92400E','#FFFAF0','#2D2616'] },
  { id:'teal',       ad:'Okyanus',     renkler:['#0D9488','#115E59','#F0FDFA','#0F1A1A'] },
  { id:'charcoal',   ad:'Kömür',
   renkler:['#1F2937','#111827','#FAFAFA','#1F2937'] },
  { id:'okyanus',    ad:'Mavi Dalga',  renkler:['#0EA5E9','#0369A1','#F0F9FF','#0C1A2E'] },
  { id:'gül',        ad:'Pembe Trend', renkler:['#EC4899','#BE185D','#FDF2F8','#2D1A20'] },
  { id:'mor',        ad:'Lavanta',    renkler:['#9333EA','#6B21A8','#FAF5FF','#1A0F2E'] },
  { id:'altın',      ad:'Bronz',       renkler:['#B8860B','#92400E','#FFFDF5','#2D2616'] },
  { id:'kömür',      ad:'Grafit',      renkler:['#374151','#1F2937','#F9FAFB','#1F2937'] },
  { id:'kiremit-2',  ad:'Terracotta',  renkler:['#C2410C','#9A3412','#FFF7ED','#2D1407'] },
];

const FONT_LIST = [
  { baslik:'Playfair Display', govde:'Inter' },
  { baslik:'Poppins',          govde:'Open Sans' },
  { baslik:'Montserrat',       govde:'Merriweather' },
  { baslik:'Raleway',          govde:'Lora' },
  { baslik:'DM Serif Display', govde:'DM Sans' },
  { baslik:'Oswald',           govde:'Roboto' },
  { baslik:'Cinzel',           govde:'Lato' },
  { baslik:'Prata',            govde:'Nunito' },
];

const HERO_FONTS = [
  'Playfair Display','Poppins','Montserrat','Raleway','DM Serif Display',
  'Oswald','Cinzel','Prata','Inter','Open Sans','Merriweather','Lora',
  'DM Sans','Roboto','Lato','Nunito',
  'Great Vibes','Pacifico','Caveat','Dancing Script',
  'Tangerine','Alex Brush','Parisienne',
  'Cormorant Garamond','Libre Baskerville',
  'Josefin Sans','Barlow','Quicksand',
  'Allura','Italianno','Kaushan Script','Cookie','Lobster',
  'Pinyon Script','Rouge Script','Satisfy',
  'Abril Fatface','Anton','Bebas Neue','Bodoni Moda',
];

const STIL_SECENEKLERI = {
  header_stil: { ad:'Header', secim:{ sticky:'Yapışkan', fixed:'Sabit', default:'Varsayılan', minimal:'Minimal' }, aciklama:'Üst navigasyon çubuğu stili' },
  footer_stil: { ad:'Footer', secim:{ default:'Varsayılan', minimal:'Minimal', compact:'Kompakt' }, aciklama:'Alt bilgi alanı stili' },
  kart_stil:   { ad:'Kart',   secim:{ default:'Varsayılan', shadow:'Gölgeli', bordered:'Kenarlıklı', modern:'Modern', minimal:'Minimal' }, aciklama:'İlan/blog kartları görünümü' },
  button_stil: { ad:'Buton',  secim:{ default:'Varsayılan', rounded:'Yuvarlak', pill:'Hap', outline:'Outline', gradient:'Gradyan' }, aciklama:'Buton görünümü' },
  animasyon:   { ad:'Animasyon', secim:{ minimize:'Minimal', fade:'Soluk', slide:'Kaydır', zoom:'Büyüt', none:'Yok' }, aciklama:'Sayfa geçiş animasyonu' },
};

let temaDraft = {};       // önizleme taslağı
let temaSaved = {};       // son kaydedilen

function temaOnizleUygula() {
  if (!temaDraft || !Object.keys(temaDraft).length) return;
  const r = document.documentElement;
  if (temaDraft.renk_ana) r.style.setProperty('--kiremit', temaDraft.renk_ana);
  if (temaDraft.renk_ana_koy) r.style.setProperty('--kiremit-k', temaDraft.renk_ana_koy);
  if (temaDraft.renk_arka) r.style.setProperty('--krem', temaDraft.renk_arka);
  if (temaDraft.renk_metin) r.style.setProperty('--toprak', temaDraft.renk_metin);
  if (temaDraft.renk_ana) r.style.setProperty('--kiremit-a', lightenHex(temaDraft.renk_ana, 72));
  if (temaDraft.font_baslik) r.style.setProperty('--font-baslik', temaDraft.font_baslik);
  if (temaDraft.font_govde) r.style.setProperty('--font-govde', temaDraft.font_govde);
  if (temaDraft.border_radius) {
    const br = parseInt(temaDraft.border_radius) || 12;
    r.style.setProperty('--r', br + 'px');
    r.style.setProperty('--r-sm', Math.max(4, Math.round(br * 0.66)) + 'px');
  }
  if (temaDraft.dark_mode === '1') document.body.classList.add('dark-mode');
  else if (temaDraft.dark_mode === '0') document.body.classList.remove('dark-mode');
}

function fontYukle(fontAdi) {
  if (!fontAdi) return;
  const isim = fontAdi.replace(/ /g, '+');
  if (document.querySelector(`link[href*="${isim}"]`)) return;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = `https://fonts.googleapis.com/css2?family=${isim}:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600;1,700&display=swap`;
  document.head.appendChild(link);
}

// ── Önizleme (sadece CSS değişir, backend'e yazılmaz) ─────────────────────

window.temaPaletSec = function(id) {
  const palet = TEMA_PALETLERI.find(p => p.id === id);
  if (!palet) return;
  temaDraft.renk_ana = palet.renkler[0];
  temaDraft.renk_ana_koy = palet.renkler[1];
  temaDraft.renk_arka = palet.renkler[2];
  temaDraft.renk_metin = palet.renkler[3];
  document.body.setAttribute('data-tema', id);
  temaOnizleUygula();
  document.querySelectorAll('.tema-palet-kart').forEach(k => k.classList.toggle('aktif', k.dataset.palet === id));
};

window.temaRenkDegisti = function(el) {
  temaDraft[el.dataset.key] = el.value;
  const txt = el.parentElement.querySelector('.tema-renk-text');
  if (txt) txt.value = el.value;
  temaOnizleUygula();
};

window.temaRenkYaziDegisti = function(el) {
  const picker = el.parentElement.querySelector('.tema-renk-picker');
  if (picker && /^#[0-9a-f]{6}$/i.test(el.value)) picker.value = el.value;
  temaDraft[el.dataset.key] = el.value;
  temaOnizleUygula();
};

window.temaStilSec = function(anahtar, deger) {
  temaDraft[anahtar] = deger;
  document.querySelectorAll(`[data-stil-grup="${anahtar}"] .tema-stil-chip`).forEach(c => c.classList.toggle('aktif', c.dataset.stil === deger));
  temaOnizleUygula();
};

window.temaFontSec = function(el) {
  temaDraft[el.dataset.key] = el.value;
  fontYukle(el.value);
  temaOnizleUygula();
  // font preview güncelle
  const ornek = el.closest('.tema-font-kolon').querySelector('.tema-font-ornek');
  if (ornek) ornek.style.fontFamily = `'${el.value}', ${el.dataset.key === 'font_baslik' ? 'serif' : 'sans-serif'}`;
};

window.temaBorderRadius = function(el) {
  temaDraft.border_radius = el.value;
  document.getElementById('br-value').textContent = el.value + 'px';
  temaOnizleUygula();
};

window.temaDarkToggle = function(el) {
  temaDraft.dark_mode = el.checked ? '1' : '0';
  temaOnizleUygula();
};

// ── Kaydet / Sıfırla ───────────────────────────────────────────────────────

const TEMA_ANAHTARLAR = new Set([
  'renk_ana','renk_ana_koy','renk_arka','renk_metin',
  'font_baslik','font_govde','border_radius','dark_mode',
  'header_stil','footer_stil','kart_stil','button_stil','animasyon',
  'shadow_kart','logo_url','favicon_url','template'
]);

window.temaKaydet = async function() {
  const degisen = Object.keys(temaDraft).filter(k => TEMA_ANAHTARLAR.has(k));
  if (!degisen.length) { bildirim('Değişiklik yok', 'bilgi'); return; }
  try {
    for (const k of degisen) {
      await api.request(`/api/admin/tema/${k}`, { method:'PUT', body:JSON.stringify({anahtar:k,deger:temaDraft[k]}) });
    }
    // Backend'deki spam satırları temizle
    try {
      await api.request('/api/admin/tema/cleanup', { method:'POST' });
    } catch {}
    Object.assign(temaSaved, temaDraft);
    temaDraft = {};
    bildirim('Tema kaydedildi ✅', 'basari');
    siteAyarlariUygula();
  } catch(e) { bildirim('Kaydedilirken hata: ' + e.message, 'hata'); }
};

window.temaSifirla = async function() {
  temaDraft = {};
  await api.request('/api/tema').then(t => { temaSaved = t || {}; }).catch(()=>{});
  adminTema();
  bildirim('Değişiklikler geri alındı', 'bilgi');
};

// ── Admin Sayfası ──────────────────────────────────────────────────────────

async function adminTema() {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  temaSaved = await api.request('/api/admin/tema').catch(()=>({}));
  temaDraft = {};

  const t = temaSaved;
  const paletId = t.renk_ana ? (TEMA_PALETLERI.find(p =>
    p.renkler[0].toLowerCase() === (t.renk_ana||'').toLowerCase() &&
    p.renkler[2].toLowerCase() === (t.renk_arka||'').toLowerCase()
  ) || TEMA_PALETLERI[0]).id : '';

  let html = '<div class="admin-baslik">🎨 Tema Yöneticisi</div>';
  html += '<div class="tema-editor">';

  // ── 1) Renk Paletleri ──────────────────────────────────────────────────
  html += '<div class="tema-bolum"><div class="tema-bolum-baslik">Renk Paletleri</div><div class="tema-bolum-aciklama">Hazır şemalardan birini seçin, önizleyin, sonra kaydedin</div>';
  html += '<div class="tema-palet-grid">';
  for (const p of TEMA_PALETLERI) {
    const a = paletId === p.id;
    html += `<div class="tema-palet-kart${a?' aktif':''}" data-palet="${esc(p.id)}" onclick="temaPaletSec('${esc(p.id)}')">
      <div class="tema-palet-renkler">${p.renkler.map(r => `<span style="background:${r}"></span>`).join('')}</div>
      <div class="tema-palet-ad">${esc(p.ad)}</div>
      ${a ? '<div class="tema-palet-check">✓</div>' : ''}
    </div>`;
  }
  html += '</div></div>';

  // ── 2) Özel Renkler ────────────────────────────────────────────────────
  html += '<div class="tema-bolum"><div class="tema-bolum-baslik">Özel Renkler</div><div class="tema-bolum-aciklama">İnce ayar için renk seçici veya hex kodu</div>';
  const renkAlanlari = [
    ['renk_ana','Ana Renk','#C45C35'], ['renk_ana_koy','Ana Renk (Koyu)','#A34A28'],
    ['renk_arka','Arka Plan','#FAF7F2'], ['renk_metin','Metin Rengi','#2D2016']
  ];
  for (const [key, etiket, def] of renkAlanlari) {
    const v = t[key] || def;
    html += `<div class="tema-renk-satir">
      <label>${esc(etiket)}</label>
      <div class="tema-renk-girdi-grup">
        <input type="color" class="tema-renk-picker" value="${esc(v)}" data-key="${esc(key)}" onchange="temaRenkDegisti(this)">
        <input type="text" class="tema-renk-text" value="${esc(v)}" data-key="${esc(key)}" oninput="temaRenkYaziDegisti(this)">
      </div>
    </div>`;
  }
  html += '</div>';

  // ── 3) Fontlar ─────────────────────────────────────────────────────────
  const fb = t.font_baslik || 'Playfair Display';
  const fg = t.font_govde || 'Inter';
  html += '<div class="tema-bolum"><div class="tema-bolum-baslik">Fontlar</div><div class="tema-bolum-aciklama">Başlık ve gövde font çiftini seçin</div>';
  html += '<div class="tema-font-grid">';
  html += '<div class="tema-font-kolon"><label>Başlık</label><select class="tema-select" data-key="font_baslik" onchange="temaFontSec(this)">';
  for (const f of FONT_LIST) html += `<option value="${esc(f.baslik)}"${fb===f.baslik?' selected':''}>${esc(f.baslik)}</option>`;
  html += `</select><div class="tema-font-ornek" style="font-family:'${esc(fb)}',serif">Aa Başlık Örneği</div></div>`;
  html += '<div class="tema-font-kolon"><label>Gövde</label><select class="tema-select" data-key="font_govde" onchange="temaFontSec(this)">';
  for (const f of FONT_LIST) html += `<option value="${esc(f.govde)}"${fg===f.govde?' selected':''}>${esc(f.govde)}</option>`;
  html += `</select><div class="tema-font-ornek" style="font-family:'${esc(fg)}',sans-serif">Aa Gövde metni örneği — lorem ipsum dolor sit amet.</div></div>`;
  html += '</div></div>';

  // ── 4) Stiller ─────────────────────────────────────────────────────────
  html += '<div class="tema-bolum"><div class="tema-bolum-baslik">Stiller</div><div class="tema-bolum-aciklama">Bileşen görünümlerini seçin</div>';
  for (const [k, sec] of Object.entries(STIL_SECENEKLERI)) {
    const m = t[k] || Object.keys(sec.secim)[0];
    html += `<div class="tema-stil-grup" data-stil-grup="${esc(k)}">
      <div class="tema-stil-label">${esc(sec.ad)}</div>
      <div class="tema-stil-aciklama">${esc(sec.aciklama)}</div>
      <div class="tema-stil-secenekler">`;
    for (const [sk, sv] of Object.entries(sec.secim)) {
      html += `<div class="tema-stil-chip${m===sk?' aktif':''}" data-stil="${esc(sk)}" onclick="temaStilSec('${esc(k)}','${esc(sk)}')">${esc(sv)}</div>`;
    }
    html += '</div></div>';
  }
  html += '</div>';

  // ── 5) Köşe Yuvarlaklığı ──────────────────────────────────────────────
  const br = parseInt(t.border_radius || '12');
  html += '<div class="tema-bolum"><div class="tema-bolum-baslik">Köşe Yuvarlaklığı</div>';
  html += '<div class="tema-slider-satir"><input type="range" min="0" max="24" value="' + br + '" class="tema-slider" oninput="temaBorderRadius(this)"><span id="br-value">' + br + 'px</span></div></div>';

  // ── 6) Koyu Mod ───────────────────────────────────────────────────────
  html += '<div class="tema-bolum"><div class="tema-bolum-baslik">Koyu Mod</div>';
  html += '<label class="tema-toggle"><input type="checkbox"' + (t.dark_mode==='1'?' checked':'') + ' onchange="temaDarkToggle(this)"><span class="tema-toggle-slider"></span> Koyu Modu Etkinleştir</label></div>';

  // ── 7) Kaydet / Sıfırla butonları ─────────────────────────────────────
  html += '<div class="tema-aksiyon-bar">';
  html += '<button class="btn btn-kirm btn-lg tema-btn-kaydet" onclick="temaKaydet()">💾 Tema Kaydet</button>';
  html += '<button class="btn btn-ntr btn-lg" onclick="temaSifirla()">↺ Sıfırla</button>';
  html += '</div>';

  html += '</div>'; // .tema-editor
  ic.innerHTML = html;

  // taslak başlangıç değerlerini saved ile doldur
  Object.assign(temaDraft, t);
  temaDraft.dark_mode = t.dark_mode || '0';
}

// ── Şablonlar ─────────────────────────────────────────────────────────────────

async function adminSablonlar() {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  const [templates, bolumler] = await Promise.all([
    api.request('/api/admin/templates'),
    api.request('/api/template/homepage'),
  ]);
  let html = '<div class="admin-baslik">Şablonlar <span style="font-size:.8rem;font-weight:400;color:var(--gri-metin)">— Anasayfa Bölüm Yönetimi</span></div>';

  // Template kartları
  if (templates) {
    html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1rem;margin-bottom:1.5rem">';
    templates.forEach(t => {
      const moduller = safeJsonParse(t.modules || '{}');
      const isActive = t.varsayilan;
      html += `<div style="background:var(--beyaz);border-radius:var(--r);padding:1rem;border:2px solid ${isActive ? 'var(--kiremit)' : 'var(--kumtasi)'}">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem">
          <div><strong>${esc(t.ad)}</strong> <code style="font-size:.75em">${esc(t.klasor)}</code></div>
          ${isActive ? '<span style="background:var(--kiremit);color:#fff;padding:2px 10px;border-radius:20px;font-size:.7rem">AKTİF</span>' : `<button class="btn btn-cik btn-sm" onclick="sablonAktiflestir(${t.id})" style="font-size:.7rem">Aktifleştir</button>`}
        </div>
        <div style="font-size:.82rem;color:var(--gri-metin);margin-bottom:.5rem">${esc(t.aciklama)}</div>
        <div style="border-top:1px solid var(--kumtasi);padding-top:.5rem">
          <div style="font-size:.8rem;font-weight:600;margin-bottom:.4rem">Modüller</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:3px">
            ${['blog','gallery','forum','banner','portfolio','services','testimonials'].map(m => `
              <label style="display:flex;align-items:center;gap:5px;font-size:.78rem;cursor:pointer;padding:2px 0">
                <input type="checkbox" ${moduller[m] !== false ? 'checked' : ''} onchange="templateModuleToggle(${t.id},'${m}',this.checked)">
                ${m.charAt(0).toUpperCase() + m.slice(1)}
              </label>
            `).join('')}
          </div>
        </div>
      </div>`;
    });
    html += '</div>';
  }

  // Bölüm listesi
  if (bolumler && bolumler.length) {
    html += '<div class="admin-baslik" style="font-size:1rem;margin-bottom:.75rem">Anasayfa Bölümleri</div>';
    html += '<div class="tablo-kont"><table class="tablo"><thead><tr><th>#</th><th>Bölüm</th><th>Başlık</th><th>Durum</th><th>Animasyon</th><th>Padding</th><th></th></tr></thead><tbody>';
    bolumler.forEach((b, i) => {
      const a = b.ayarlar || {};
      html += `<tr${!b.aktif ? ' style="opacity:.5"' : ''}>
        <td>${b.sira}</td>
        <td><code>${esc(b.section_key)}</code></td>
        <td>${esc(b.baslik || '')}</td>
        <td><span class="toggle-slider" style="${b.aktif !== false ? 'background:var(--kiremit)' : ''}" onclick="sablonBolumAktifToggle(${b.id}, ${!(b.aktif !== false)})"></span></td>
        <td style="font-size:.8em">${esc(a.animasyon || '—')}</td>
        <td style="font-size:.8em">${esc(a.padding || '—')}</td>
        <td><button class="btn btn-cik btn-sm" onclick="sablonBolumDuzenle(${b.id})">⚙️</button></td>
      </tr>`;
    });
    html += '</tbody></table></div>';

    // Sıralama kontrolleri
    html += `<div style="margin-top:1rem;display:flex;gap:8px;flex-wrap:wrap">`;
    bolumler.forEach((b, i) => {
      html += `<div style="background:var(--kumtasi);padding:6px 12px;border-radius:8px;font-size:.85rem;display:flex;align-items:center;gap:6px">
        <span>${i + 1}</span>
        <code style="font-size:.75em">${esc(b.section_key)}</code>
        ${i > 0 ? `<button class="btn btn-gri" onclick="sablonBolumTasi(${b.id},${bolumler[i-1].id})" style="padding:2px 8px;font-size:.7rem">↑</button>` : ''}
        ${i < bolumler.length - 1 ? `<button class="btn btn-gri" onclick="sablonBolumTasi(${b.id},${bolumler[i+1].id})" style="padding:2px 8px;font-size:.7rem">↓</button>` : ''}
      </div>`;
    });
    html += '</div>';
  } else {
    html += '<div class="bos-durum"><div class="bos-ikon">📐</div><h3>Henüz bölüm yok</h3></div>';
  }
  ic.innerHTML = html;
}

window.sablonAktiflestir = async function(id) {
  if (!confirm('Bu şablonu aktifleştir?')) return;
  try {
    await api.request(`/api/admin/templates/${id}`, { method:'PUT', body:JSON.stringify({varsayilan:true}) });
    bildirim('Şablon değiştirildi','basari');
    adminSablonlar();
  } catch(e) { bildirim(e.message,'hata'); }
};

window.templateModuleToggle = async function(tid, modul, aktif) {
  try {
    const t = await api.request(`/api/admin/templates/${tid}`);
    const moduller = safeJsonParse(t.modules || '{}');
    moduller[modul] = aktif;
    await api.request(`/api/admin/templates/${tid}`, { method:'PUT', body:JSON.stringify({modules:JSON.stringify(moduller)}) });
    bildirim(`${modul} ${aktif ? 'aktif' : 'pasif'}`,'basari');
  } catch(e) { bildirim(e.message,'hata'); }
};

window.sablonBolumAktifToggle = async function(id, aktif) {
  try {
    await api.request(`/api/admin/bolumler/${id}`, { method:'PUT', body:JSON.stringify({aktif}) });
    adminSablonlar();
  } catch(e) { bildirim(e.message,'hata'); }
};

window.sablonBolumDuzenle = async function(id) {
  const bolum = await api.request(`/api/admin/bolumler/${id}`);
  if (!bolum) return;
  const a = safeJsonParse(bolum.ayarlar || '{}');
  const icerik = a.icerik || {};
  const isHero = bolum.section_key === 'hero';
  const isSlider = bolum.section_key === 'slider';
  const isServices = bolum.section_key === 'services';

  const html = `<div class="modal-zemin" id="bolum-modal" data-key="${esc(bolum.section_key)}" onclick="if(event.target===this)document.getElementById('bolum-modal').remove()">
    <div class="modal-kapsul" style="max-width:520px">
      <h3 style="margin-bottom:1rem">Bölüm Ayarları <code style="font-size:.75em">${esc(bolum.section_key)}</code></h3>
      <div style="display:grid;gap:.75rem">
        <label>Başlık <input id="bm-baslik" class="form-girdi" value="${esc(bolum.baslik || '')}"></label>
        ${isHero ? `
        <label>Alt Başlık <input id="bm-alt-baslik" class="form-girdi" value="${esc(a.alt_baslik || '')}"></label>
        <label>Buton Metni <input id="bm-buton" class="form-girdi" value="${esc(a.buton_metin || '')}"></label>
        <label>Buton Linki <input id="bm-link" class="form-girdi" value="${esc(a.buton_link || '')}"></label>
        <label>Arka Plan Görseli (URL) <input id="bm-gorsel" class="form-girdi" value="${esc(a.arka_gorsel || '')}"></label>` : ''}
        ${isSlider ? `
        <label>Slider İçeriği (JSON)
        <textarea id="bm-slider" class="form-girdi" rows="5" style="resize:vertical">${esc(JSON.stringify(icerik.slides || [{title:'',subtitle:''}], null, 2))}</textarea>
        <div style="font-size:.75rem;color:var(--gri-metin)">Her slide için: {"title":"...","subtitle":"...","image":"..."}</div></label>` : ''}
        ${isServices ? `
        <label>Hizmetler (JSON)
        <textarea id="bm-services" class="form-girdi" rows="5" style="resize:vertical">${esc(JSON.stringify(icerik.items || [{ikon:'',baslik:'',metin:''}], null, 2))}</textarea>
        <div style="font-size:.75rem;color:var(--gri-metin)">Her hizmet için: {"ikon":"🏠","baslik":"...","metin":"..."}</div></label>` : ''}
        <details style="margin-top:.5rem">
          <summary style="cursor:pointer;font-size:.85rem;font-weight:600;color:var(--gri-metin)">⚙️ Gelişmiş Ayarlar</summary>
          <div style="display:grid;gap:.75rem;margin-top:.75rem">
            <label style="display:flex;align-items:center;gap:8px">Aktif <input type="checkbox" class="toggle-label-cb" id="bm-aktif" ${bolum.aktif !== false ? 'checked' : ''}><span class="toggle-slider"></span></label>
            <label>Animasyon <select id="bm-animasyon" class="form-girdi">
              ${['fadeIn','fadeUp','slide','zoom','none'].map(o => `<option value="${o}" ${a.animasyon === o ? 'selected' : ''}>${o}</option>`).join('')}
            </select></label>
            <label>Padding <input id="bm-padding" class="form-girdi" value="${esc(a.padding || '60px 0')}"></label>
            <label>Arka Plan Rengi <input id="bm-renk" class="form-girdi" value="${esc(a.arka_renk || '')}" placeholder="#FFFFFF veya boş"></label>
            <label>Container <select id="bm-genislik" class="form-girdi">
              ${['boxed','full'].map(o => `<option value="${o}" ${a.container_genislik === o ? 'selected' : ''}>${o === 'boxed' ? 'Boxed (dar)' : 'Full (geniş)'}</option>`).join('')}
            </select></label>
            <label style="display:flex;align-items:center;gap:8px">Başlık Göster <input type="checkbox" class="toggle-label-cb" id="bm-baslik-goster" ${a.baslik_goster !== false ? 'checked' : ''}><span class="toggle-slider"></span></label>
          </div>
        </details>
      </div>
      <div style="display:flex;gap:8px;margin-top:1rem">
        <button class="btn btn-kirm" onclick="sablonBolumKaydet(${id})">💾 Kaydet</button>
        <button class="btn btn-ntr" onclick="document.getElementById('bolum-modal').remove()">İptal</button>
      </div>
    </div>
  </div>`;
  const existing = document.getElementById('bolum-modal');
  if (existing) existing.remove();
  document.body.insertAdjacentHTML('beforeend', html);
};

window.sablonBolumKaydet = async function(id) {
  try {
    const modal = document.getElementById('bolum-modal');
    const sectionKey = modal?.dataset?.key || '';
    const isHero = sectionKey === 'hero';
    const isSlider = sectionKey === 'slider';
    const isServices = sectionKey === 'services';

    const baslik = document.getElementById('bm-baslik')?.value?.trim() || '';
    const aktif = document.getElementById('bm-aktif')?.checked ?? true;
    const animasyon = document.getElementById('bm-animasyon')?.value || 'fadeIn';
    const padding = document.getElementById('bm-padding')?.value || '60px 0';
    const arka_renk = document.getElementById('bm-renk')?.value || '';
    const genislik = document.getElementById('bm-genislik')?.value || 'boxed';
    const baslik_goster = document.getElementById('bm-baslik-goster')?.checked ?? true;

    const ayarlar = {animasyon,padding,arka_renk,container_genislik:genislik,baslik_goster};

    if (isHero) {
      ayarlar.alt_baslik = document.getElementById('bm-alt-baslik')?.value || '';
      ayarlar.buton_metin = document.getElementById('bm-buton')?.value || '';
      ayarlar.buton_link = document.getElementById('bm-link')?.value || '';
      ayarlar.arka_gorsel = document.getElementById('bm-gorsel')?.value || '';
    }
    if (isSlider) {
      try {
        ayarlar.icerik = { slides: JSON.parse(document.getElementById('bm-slider')?.value || '[]') };
      } catch {}
    }
    if (isServices) {
      try {
        ayarlar.icerik = { items: JSON.parse(document.getElementById('bm-services')?.value || '[]') };
      } catch {}
    }

    await api.request(`/api/admin/bolumler/${id}`, {
      method:'PUT',
      body:JSON.stringify({baslik, aktif, ayarlar: JSON.stringify(ayarlar)}),
    });
    bildirim('Bölüm güncellendi','basari');
    if (modal) modal.remove();
    adminSablonlar();
  } catch(e) { bildirim(e.message,'hata'); }
};

window.sablonBolumTasi = async function(id1, id2) {
  try {
    const r = await api.request('/api/admin/bolumler/sirala', {
      method:'PUT',
      body:JSON.stringify({items:[{id:id1,sira:0},{id:id2,sira:1}]}),
    });
    bildirim('Sıra değiştirildi','basari');
    adminSablonlar();
  } catch(e) { bildirim(e.message,'hata'); }
};

// ── /CMS Admin ────────────────────────────────────────────────────────────────
// ── Site Sihirbazı (FAZ 3) ─────────────────────────────────────────────────
let wizardState = { wizard_id: null, adim: 1, veri: {} };

async function adminWizard() {
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = `<div class="admin-baslik">✨ Site Oluşturma Sihirbazı</div>
    <div class="wizard-step"><div class="wizard-secili">Adım 1/10</div>
    <div class="wizard-adimlar"><span class="wizard-adim aktif">1</span><span class="wizard-adim">2</span><span class="wizard-adim">3</span><span>…</span><span class="wizard-adim">10</span></div></div>
    <div style="background:var(--krem);border-radius:var(--r-sm);padding:1.5rem;max-width:500px">
    <label>Firma Adı <input id="wf-ad" class="inp" style="width:100%;margin-bottom:.8rem" placeholder="Firma Adı"></label>
    <label>E-Posta <input id="wf-email" class="inp" style="width:100%;margin-bottom:.8rem" placeholder="info@firma.com"></label>
    <label>Telefon <input id="wf-tel" class="inp" style="width:100%;margin-bottom:.8rem" placeholder="+90 555 000 00 00"></label>
    <button class="btn btn-kirm" onclick="wizardAdim1()">Devam →</button></div>`;
}

async function wizardAdim1() {
  const ad = document.getElementById('wf-ad')?.value?.trim();
  const email = document.getElementById('wf-email')?.value?.trim();
  const tel = document.getElementById('wf-tel')?.value?.trim();
  if (!ad) { bildirim('Firma adı gerekli', 'hata'); return; }

  try {
    const r = await api.request('/api/admin/wizard/baslat', { method: 'POST', body: '{}' }, { silent: true });
    if (!r || !r.wizard_id) throw new Error('Wizard başlatılamadı');
    wizardState.wizard_id = r.wizard_id;
    wizardState.adim = 1;
    wizardState.veri = { firma_adi: ad, firma_email: email, firma_tel: tel };
    await api.request(`/api/admin/wizard/${r.wizard_id}/adim/1`, {
      method: 'POST', body: JSON.stringify(wizardState.veri),
    });
    // Step 2: Sektör seç
    const sektorler = await api.request('/api/wizard/sektorler');
    const ic = document.getElementById('admin-ic');
    let html = `<div class="admin-baslik">✨ Adım 2/10 — Sektör Seçin</div>
      <div class="wizard-step"><div class="wizard-secili">${esc(ad)}</div>
      <div class="wizard-adimlar"><span class="wizard-adim">1</span><span class="wizard-adim aktif">2</span><span class="wizard-adim">3</span><span>…</span><span class="wizard-adim">10</span></div></div>
      <div class="wizard-grid">`;
    (sektorler || []).forEach(s => {
      html += `<div class="wizard-kart" onclick="wizardAdim2('${s.sector}')">
        <div class="wizard-ikon">${sektorIkon(s.sector)}</div>
        <div class="wizard-label">${esc(s.label)}</div>
        <div class="wizard-acik">${s.templates.length} template</div>
      </div>`;
    });
    html += '</div>';
    ic.innerHTML = html;
  } catch (e) { bildirim(e.message, 'hata'); }
}

function sektorIkon(sector) {
  const ikonlar = { estate:'🏠', travel:'✈️', hotel:'🏨', restaurant:'🍽️', corporate:'🏢', clinic:'🏥', landing:'🚀', construction:'🏗️' };
  return ikonlar[sector] || '📦';
}

async function wizardBaslat(sector) {
  try {
    const r = await api.request('/api/admin/wizard/baslat', { method: 'POST', body: '{}' }, { silent: true });
    if (!r || !r.wizard_id) throw new Error('Wizard başlatılamadı');
    wizardState.wizard_id = r.wizard_id;
    wizardState.adim = 1;
    wizardState.veri = {};
    await api.request(`/api/admin/wizard/${r.wizard_id}/adim/1`, {
      method: 'POST',
      body: JSON.stringify({ sector }),
    });
    await wizardAdim2(sector);
  } catch (e) { bildirim(e.message, 'hata'); }
}

async function wizardAdim2(sector) {
  if (!wizardState.wizard_id) return;
  wizardState.veri.sector = sector;
  await api.request(`/api/admin/wizard/${wizardState.wizard_id}/adim/2`, {
    method: 'POST', body: JSON.stringify({ sector }),
  });
  const ic = document.getElementById('admin-ic');
  const detay = await api.request(`/api/wizard/sektor/${sector}`);
  let tip = '';
  const isim = { estate:'Emlak', travel:'Seyahat', hotel:'Otel', restaurant:'Restaurant', corporate:'Kurumsal', clinic:'Klinik', landing:'Landing', construction:'İnşaat' };
  tip = isim[sector] || sector;

  const templates = detay?.templates || [];
  const tplLabels = { 'estate-modern':'Estate Modern', 'estate-luxury':'Estate Luxury', 'travel':'Travel', 'hotel':'Hotel', 'corporate':'Corporate', 'landing':'Landing', 'minimal':'Minimal' };
  let html = `<div class="admin-baslik">✨ Adım 3/10 — Template Seçin</div>
    <div class="wizard-step"><div class="wizard-secili">${tip}</div>
    <div class="wizard-adimlar"><span class="wizard-adim">1</span><span class="wizard-adim">2</span><span class="wizard-adim aktif">3</span><span>…</span><span class="wizard-adim">10</span></div></div>
    <div class="wizard-grid">`;
  templates.forEach(t => {
    const label = tplLabels[t] || t;
    html += `<div class="wizard-kart" onclick="wizardAdim3('${t}')">
      <div class="wizard-label">${esc(label)}</div>
    </div>`;
  });
  html += '</div>';
  ic.innerHTML = html;
}

async function wizardAdim3(template) {
  if (!wizardState.wizard_id) return;
  wizardState.veri.template = template;
  await api.request(`/api/admin/wizard/${wizardState.wizard_id}/adim/3`, {
    method: 'POST', body: JSON.stringify({ template }),
  });
  const ic = document.getElementById('admin-ic');
  const sector = wizardState.veri.sector || 'corporate';
  const palettes = await api.request(`/api/wizard/sektor/${sector}/palettes`);
  let html = `<div class="admin-baslik">✨ Adım 4/10 — Renk Paleti</div>
    <div class="wizard-step"><div class="wizard-secili">${esc(template)}</div>
    <div class="wizard-adimlar"><span class="wizard-adim">1</span><span class="wizard-adim">2</span><span class="wizard-adim">3</span><span class="wizard-adim aktif">4</span><span>…</span><span class="wizard-adim">10</span></div></div>
    <div class="wizard-palettes">`;
  (palettes || []).forEach(p => {
    const c = p.colors || {};
    const escJson = esc(JSON.stringify(p));
    html += `<div class="wizard-palet-kart" onclick="wizardAdim4('${escJson}')">
      <div class="wizard-palet-renkler">
        <span style="background:${c.ana || '#ccc'}"></span>
        <span style="background:${c.arka || '#fff'}"></span>
        <span style="background:${c.metin || '#333'}"></span>
      </div>
      <div class="wizard-palet-ad">${esc(p.name)}</div>
    </div>`;
  });
  html += '</div>';
  ic.innerHTML = html;
}

async function wizardAdim4(paletteArg) {
  if (!wizardState.wizard_id) return;
  let palette;
  try { palette = typeof paletteArg === 'string' ? JSON.parse(paletteArg) : paletteArg; }
  catch { palette = {}; }
  wizardState.veri.renk_paleti = palette;
  await api.request(`/api/admin/wizard/${wizardState.wizard_id}/renk`, {
    method: 'POST', body: JSON.stringify({ palette }),
  });
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = `<div class="admin-baslik">✨ Adım 5/10 — Menüler</div>
    <p>Menüler otomatik oluşturulsun mu?</p>
    <button class="btn btn-kirm" onclick="wizardAdim5(true)">Evet, Oluştur</button>
    <button class="btn btn-cik" onclick="wizardAdim5(false)">Sonra Ben Eklerim</button>`;
}

async function wizardAdim5(auto) {
  if (!wizardState.wizard_id) return;
  await api.request(`/api/admin/wizard/${wizardState.wizard_id}/menuler`, {
    method: 'POST', body: JSON.stringify({ auto }),
  });
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = `<div class="admin-baslik">✨ Adım 6/10 — Sayfalar</div>
    <p>Sayfalar otomatik oluşturulsun mu?</p>
    <button class="btn btn-kirm" onclick="wizardAdim6(true)">Evet, Oluştur</button>
    <button class="btn btn-cik" onclick="wizardAdim6(false)">Sonra Ben Eklerim</button>`;
}

async function wizardAdim6(auto) {
  if (!wizardState.wizard_id) return;
  await api.request(`/api/admin/wizard/${wizardState.wizard_id}/sayfalar`, {
    method: 'POST', body: JSON.stringify({ auto }),
  });
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = `<div class="admin-baslik">✨ Adım 7/10 — Widget'lar</div>
    <p>Hangi widget'lar aktif olsun?</p>
    <label><input type="checkbox" id="ww-wh" checked> WhatsApp</label><br>
    <label><input type="checkbox" id="ww-gm" checked> Google Maps</label><br>
    <label><input type="checkbox" id="ww-tel" checked> Telefon</label><br>
    <label><input type="checkbox" id="ww-ig"> Instagram</label><br>
    <label><input type="checkbox" id="ww-cb"> Çerez Bildirimi</label><br>
    <button class="btn btn-kirm" onclick="wizardAdim7()" style="margin-top:1rem">Devam</button>`;
}

async function wizardAdim7() {
  if (!wizardState.wizard_id) return;
  const list = [];
  ['ww-wh','ww-gm','ww-tel','ww-ig','ww-cb'].forEach(id => {
    const el = document.getElementById(id);
    if (el && el.checked) list.push(id.replace('ww-', ''));
  });
  const map = { wh:'whatsapp', gm:'google_maps', tel:'telefon', ig:'instagram', cb:'cookie_banner' };
  await api.request(`/api/admin/wizard/${wizardState.wizard_id}/widgetlar`, {
    method: 'POST',
    body: JSON.stringify({ widget_list: list.map(k => map[k] || k) }),
  });
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = `<div class="admin-baslik">✨ Adım 8/10 — Forum</div>
    <p>Forum kullanmak istiyor musunuz?</p>
    <button class="btn btn-kirm" onclick="wizardAdim8(true)">Evet</button>
    <button class="btn btn-cik" onclick="wizardAdim8(false)">Hayır</button>`;
}

async function wizardAdim8(aktif) {
  if (!wizardState.wizard_id) return;
  await api.request(`/api/admin/wizard/${wizardState.wizard_id}/forum`, {
    method: 'POST', body: JSON.stringify({ aktif }),
  });
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = `<div class="admin-baslik">✨ Adım 9/10 — SEO</div>
    <p>SEO ayarları otomatik oluşturulsun mu?</p>
    <button class="btn btn-kirm" onclick="wizardAdim9()">Evet, Oluştur</button>`;
}

async function wizardAdim9() {
  if (!wizardState.wizard_id) return;
  await api.request(`/api/admin/wizard/${wizardState.wizard_id}/seo`, {
    method: 'POST', body: JSON.stringify({ seo: {} }),
  });
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = `<div class="admin-baslik">✨ Adım 10/10 — Demo İçerik</div>
    <p>Hangi demo içerikler oluşturulsun?</p>
    <label><input type="checkbox" id="dm-banner" checked> Banner</label><br>
    <label><input type="checkbox" id="dm-blog" checked> Blog Yazıları</label><br>
    <label><input type="checkbox" id="dm-galeri" checked> Galeri</label><br>
    <label><input type="checkbox" id="dm-portfoy" checked> Portföy</label><br>
    <label><input type="checkbox" id="dm-forum"> Forum</label><br>
    <label><input type="checkbox" id="dm-referans" checked> Referanslar</label><br>
    <button class="btn btn-kirm" onclick="wizardAdim10()" style="margin-top:1rem">Devam</button>`;
}

async function wizardAdim10() {
  if (!wizardState.wizard_id) return;
  const demo = {};
  ['banner','blog','gallery','portfolio','forum','testimonials','services'].forEach(k => {
    const el = document.getElementById('dm-' + (k === 'testimonials' ? 'referans' : k === 'portfolio' ? 'portfoy' : k === 'gallery' ? 'galeri' : k));
    if (el) demo[k] = el.checked;
  });
  await api.request(`/api/admin/wizard/${wizardState.wizard_id}/demo`, {
    method: 'POST', body: JSON.stringify({ demo }),
  });
  const ic = document.getElementById('admin-ic');
  ic.innerHTML = `<div class="admin-baslik">✨ Tüm Adımlar Tamamlandı</div>
    <p style="margin:1rem 0">Siteyi oluşturmak için butona tıklayın.</p>
    <button class="btn btn-kirm" onclick="wizardSon()" style="font-size:1.2rem;padding:1rem 2rem">🚀 Siteyi Oluştur</button>`;
}

async function wizardSon() {
  if (!wizardState.wizard_id) return;
  try {
    const r = await api.request(`/api/admin/wizard/${wizardState.wizard_id}/olustur`, { method: 'POST', body: '{}' }, { silent: true });
    if (r?.success) {
      bildirim('✅ Site başarıyla oluşturuldu!', 'basari');
      api.clearCache();
      setTimeout(() => location.reload(), 1500);
      adminSayfa('sablonlar');
    } else {
      bildirim('Hata: ' + (r?.message || 'Bilinmeyen hata'), 'hata');
    }
  } catch (e) {
    bildirim(e.message, 'hata');
  }
}

window.adminWizard = adminWizard;
window.wizardBaslat = wizardBaslat;
window.wizardAdim1 = wizardAdim1;
window.wizardAdim2 = wizardAdim2;
window.wizardAdim3 = wizardAdim3;
window.wizardAdim4 = wizardAdim4;
window.wizardAdim5 = wizardAdim5;
window.wizardAdim6 = wizardAdim6;
window.wizardAdim7 = wizardAdim7;
window.wizardAdim8 = wizardAdim8;
window.wizardAdim9 = wizardAdim9;
window.wizardAdim10 = wizardAdim10;
window.wizardSon = wizardSon;
window.sektorIkon = sektorIkon;

// ── Marketplace (FAZ 4) ────────────────────────────────────────────────────
async function adminMarketplace() {
  const ic = document.getElementById('admin-ic');
  let html = '<div class="admin-baslik">🏪 Marketplace</div><div class="market-grid">';

  const pluginler = await api.request('/api/admin/plugins').catch(() => []);
  if (pluginler && pluginler.length) {
    pluginler.forEach(p => {
      html += `<div class="market-kart">
        <div class="market-baslik">${esc(p.ad)}</div>
        <div class="market-acik">${esc(p.aciklama || '')}</div>
        <div class="market-vers">v${esc(p.versiyon || '1.0.0')}</div>
        <button class="btn btn-${p.aktif ? 'kirm' : 'cik'}" onclick="adminPluginToggle(${p.id})" style="margin-top:.5rem;font-size:.8rem">${p.aktif ? 'Devre Dışı Bırak' : 'Aktif Et'}</button>
      </div>`;
    });
  }
  html += '</div>';
  ic.innerHTML = html;
}

async function adminPluginToggle(id) {
  await api.request(`/api/admin/plugins/${id}/toggle`);
  bildirim('Plugin durumu değiştirildi', 'basari');
  adminMarketplace();
}

window.adminMarketplace = adminMarketplace;
window.adminPluginToggle = adminPluginToggle;

// ── SaaS Yönetimi (FAZ 4) ───────────────────────────────────────────────
async function adminSaaS() {
  const ic = document.getElementById('admin-ic');
  let html = `<div class="admin-baslik">☁️ SaaS Yönetimi</div>
    <div style="display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:1.5rem">
      <button class="btn btn-kirm" onclick="saasTenant()">🏢 Multi-Tenant</button>
      <button class="btn btn-kirm" onclick="saasBackup()">💾 Yedekleme</button>
      <button class="btn btn-kirm" onclick="saasUpdate()">🔄 Güncelleme</button>
      <button class="btn btn-kirm" onclick="saasApi()">🔌 API Marketplace</button>
    </div>
    <div id="saas-ic" style="margin-top:1rem">
      <p style="color:var(--gri-metin)">Bir modül seçin.</p>
    </div>`;
  ic.innerHTML = html;
}

// ── 4.1 — Multi-Tenant ───────────────────────────────────────────────────
async function saasTenant() {
  const ic = document.getElementById('saas-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  try {
    const list = await api.request('/api/admin/saas/tenant');
    let html = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
      <h3 style="margin:0">🏢 Multi-Tenant Domainler</h3>
      <button class="btn btn-kirm" onclick="saasTenantEkle()">+ Yeni Domain</button>
    </div>`;
    if (!list || !list.length) {
      html += '<div class="bos-durum"><p>Henüz domain eklenmemiş.</p></div>';
    } else {
      html += '<table class="admin-table"><tr><th>Domain</th><th>Firma</th><th>Lisans</th><th></th></tr>';
      list.forEach(t => {
        html += `<tr>
          <td>${esc(t.domain)}</td>
          <td>${esc(t.firma_adi)}</td>
          <td>${esc(t.paket || '-')}</td>
          <td><button class="btn btn-hat btn-sm" onclick="saasTenantSil(${t.id})">🗑</button></td>
        </tr>`;
      });
      html += '</table>';
    }
    ic.innerHTML = html;
  } catch (e) { ic.innerHTML = `<p style="color:red">${e.message}</p>`; }
}

async function saasTenantEkle() {
  const domain = prompt('Domain (ör: firma.domain.com):');
  if (!domain) return;
  const firma = prompt('Firma adı:');
  if (!firma) return;
  try {
    await api.request('/api/admin/saas/tenant', { method: 'POST', body: JSON.stringify({ domain, firma_adi: firma }) });
    bildirim('Domain eklendi', 'basari');
    saasTenant();
  } catch (e) { bildirim(e.message, 'hata'); }
}

async function saasTenantSil(id) {
  if (!confirm('Emin misiniz?')) return;
  try {
    await api.request(`/api/admin/saas/tenant/${id}`, { method: 'DELETE' });
    bildirim('Silindi', 'basari');
    saasTenant();
  } catch (e) { bildirim(e.message, 'hata'); }
}

// ── 4.2 — Yedekleme ─────────────────────────────────────────────────────
async function saasBackup() {
  const ic = document.getElementById('saas-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  try {
    const list = await api.request('/api/admin/saas/backup');
    let html = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
      <h3 style="margin:0">💾 Yedeklemeler</h3>
      <button class="btn btn-kirm" onclick="saasBackupOlustur()">+ Yeni Yedek</button>
    </div>`;
    if (!list || !list.length) {
      html += '<div class="bos-durum"><p>Henüz yedek alınmamış.</p></div>';
    } else {
      html += '<table class="admin-table"><tr><th>Dosya</th><th>Boyut</th><th>Tür</th><th>Tarih</th><th></th></tr>';
      list.forEach(b => {
        const boyut = b.boyut > 1024 ? (b.boyut / 1024).toFixed(1) + ' KB' : b.boyut + ' B';
        html += `<tr>
          <td>${esc(b.dosya_adi)}</td>
          <td>${boyut}</td>
          <td>${esc(b.tur)}</td>
          <td>${(b.olusturma || '').slice(0, 19)}</td>
          <td>
            <button class="btn btn-ntr btn-sm" onclick="saasBackupRestore(${b.id})">🔄</button>
            <button class="btn btn-hat btn-sm" onclick="saasBackupSil(${b.id})">🗑</button>
          </td>
        </tr>`;
      });
      html += '</table>';
    }
    ic.innerHTML = html;
  } catch (e) { ic.innerHTML = `<p style="color:red">${e.message}</p>`; }
}

async function saasBackupOlustur() {
  try {
    const r = await api.request('/api/admin/saas/backup', { method: 'POST' });
    if (r?.success) bildirim('✅ Yedek alındı: ' + r.dosya_adi, 'basari');
    else bildirim('Hata: ' + (r?.error || '?'), 'hata');
    saasBackup();
  } catch (e) { bildirim(e.message, 'hata'); }
}

async function saasBackupRestore(id) {
  if (!confirm('Yedeği geri yüklemek mevcut veritabanını değiştirir. Emin misiniz?')) return;
  try {
    const r = await api.request(`/api/admin/saas/backup/${id}/restore`, { method: 'POST' });
    if (r?.success) bildirim('✅ Yedek geri yüklendi', 'basari');
    else bildirim('Hata: ' + (r?.error || '?'), 'hata');
  } catch (e) { bildirim(e.message, 'hata'); }
}

async function saasBackupSil(id) {
  if (!confirm('Yedek silinsin mi?')) return;
  try {
    await api.request(`/api/admin/saas/backup/${id}`, { method: 'DELETE' });
    bildirim('Silindi', 'basari');
    saasBackup();
  } catch (e) { bildirim(e.message, 'hata'); }
}

// ── 4.2 — Güncelleme ─────────────────────────────────────────────────────
async function saasUpdate() {
  const ic = document.getElementById('saas-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  try {
    const r = await api.request('/api/admin/saas/update/durum');
    const v = r?.versiyon || {};
    const d = r?.durum || {};
    let html = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
      <h3 style="margin:0">🔄 Güncelleme</h3>
      <button class="btn btn-kirm" onclick="saasUpdateYap()">Güncelle</button>
    </div>
    <div style="background:var(--krem);border-radius:var(--r-sm);padding:1rem;margin-bottom:1rem">
      <div><strong>Versiyon:</strong> ${esc(v.current_version || '-')}</div>
      <div><strong>Branch:</strong> ${esc(v.current_branch || '-')}</div>
      <div><strong>Commit:</strong> <code>${esc(v.current_hash || '-')}</code></div>
      <div><strong>Durum:</strong> ${d.clean ? '✅ Temiz' : '⚠️ Değişiklik var'}</div>
    </div>`;
    if (v.son_commits && v.son_commits.length) {
      html += '<div style="font-size:.85rem"><strong>Son 5 commit:</strong><ul>';
      v.son_commits.forEach(c => { html += `<li><code>${esc(c)}</code></li>`; });
      html += '</ul></div>';
    }
    if (d.degisken_dosyalar && d.degisken_dosyalar.length) {
      html += '<div style="color:var(--kiremit-k);font-size:.85rem;margin-top:.5rem">Değişen dosyalar:</div>';
      d.degisken_dosyalar.forEach(f => { html += `<div style="font-size:.8rem">${esc(f)}</div>`; });
    }
    ic.innerHTML = html;
  } catch (e) { ic.innerHTML = `<p style="color:red">${e.message}</p>`; }
}

async function saasUpdateYap() {
  if (!confirm('Güncelleme yapılsın mı? (git pull)')) return;
  try {
    const r = await api.request('/api/admin/saas/update', { method: 'POST' });
    if (r?.success) bildirim('✅ ' + r.message, 'basari');
    else bildirim('Hata: ' + (r?.message || '?'), 'hata');
    saasUpdate();
  } catch (e) { bildirim(e.message, 'hata'); }
}

// ── 4.3 — API Marketplace ───────────────────────────────────────────────
async function saasApi() {
  const ic = document.getElementById('saas-ic');
  ic.innerHTML = '<div class="yukleniyor"><div class="spinner"></div></div>';
  try {
    const [entegrasyonlar, saglayicilar] = await Promise.all([
      api.request('/api/admin/saas/api'),
      api.request('/api/admin/saas/api/saglayicilar').catch(() => []),
    ]);
    let html = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
      <h3 style="margin:0">🔌 API Marketplace</h3>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem">`;
    (saglayicilar || []).forEach(s => {
      const ent = (entegrasyonlar || []).find(e => e.saglayici === s.key);
      const aktif = ent?.aktif || false;
      const apiKey = ent?.api_key || '';
      html += `<div class="market-kart" style="position:relative">
        <div style="font-weight:600;font-size:.95rem">${esc(s.ad)}</div>
        <div style="font-size:.75rem;color:var(--gri-metin);margin:.25rem 0">${esc(s.key)}</div>
        <div style="font-size:.8rem;margin:.5rem 0">
          <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${aktif ? '#16a34a' : '#9ca3af'};margin-right:.4rem"></span>
          ${aktif ? 'Aktif' : 'Pasif'}
          ${apiKey ? '· 🔑 Var' : '· Anahtar Yok'}
        </div>
        <div style="display:flex;gap:.35rem;flex-wrap:wrap;margin-top:.5rem">
          <button class="btn btn-ntr btn-sm" onclick="saasApiDuzenle('${s.key}','${esc(s.ad)}')">✏</button>
          <button class="btn btn-sm" style="background:${aktif ? '#FEF3C7' : '#D1FAE5'}" onclick="saasApiToggle('${s.key}')">${aktif ? 'Pasif' : 'Aktif'}</button>
          <button class="btn btn-ntr btn-sm" onclick="saasApiTest('${s.key}')">🔍 Test</button>
        </div>
      </div>`;
    });
    html += '</div>';
    ic.innerHTML = html;
  } catch (e) { ic.innerHTML = `<p style="color:red">${e.message}</p>`; }
}

async function saasApiDuzenle(saglayici, ad) {
  try {
    const mevcut = await api.request(`/api/admin/saas/api/${saglayici}`);
    const apiKey = prompt(`${ad} API Key girin:`, mevcut?.api_key || '');
    if (apiKey === null) return;
    const apiUrl = prompt(`${ad} API URL:`, mevcut?.api_url || '');
    if (apiUrl === null) return;
    await api.request(`/api/admin/saas/api/${saglayici}`, {
      method: 'POST', body: JSON.stringify({ api_key: apiKey, api_url: apiUrl }),
    });
    bildirim(`${ad} güncellendi`, 'basari');
    saasApi();
  } catch (e) { bildirim(e.message, 'hata'); }
}

async function saasApiToggle(saglayici) {
  try {
    await api.request(`/api/admin/saas/api/${saglayici}/toggle`);
    bildirim('Durum değiştirildi', 'basari');
    saasApi();
  } catch (e) { bildirim(e.message, 'hata'); }
}

async function saasApiTest(saglayici) {
  try {
    const r = await api.request(`/api/admin/saas/api/${saglayici}/test`, { method: 'POST' });
    if (r?.success) bildirim('✅ ' + r.message, 'basari');
    else bildirim('❌ ' + (r?.message || 'Test başarısız'), 'hata');
  } catch (e) { bildirim(e.message, 'hata'); }
}

window.adminSaaS = adminSaaS;
window.saasTenant = saasTenant;
window.saasTenantEkle = saasTenantEkle;
window.saasTenantSil = saasTenantSil;
window.saasBackup = saasBackup;
window.saasBackupOlustur = saasBackupOlustur;
window.saasBackupRestore = saasBackupRestore;
window.saasBackupSil = saasBackupSil;
window.saasUpdate = saasUpdate;
window.saasUpdateYap = saasUpdateYap;
window.saasApi = saasApi;
window.saasApiDuzenle = saasApiDuzenle;
window.saasApiToggle = saasApiToggle;
window.saasApiTest = saasApiTest;

// ── Wizard CSS (head'e ekle) ──────────────────────────────────────────────
(function() {
  if (document.getElementById('wizard-css')) return;
  const s = document.createElement('style');
  s.id = 'wizard-css';
  s.textContent = `
.wizard-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:1rem; margin-top:1.5rem; }
.wizard-kart { background:var(--krem); border-radius:var(--r-sm); padding:1.5rem; cursor:pointer; transition:.2s; text-align:center; }
.wizard-kart:hover { transform:translateY(-3px); box-shadow:var(--golge); }
.wizard-ikon { font-size:2.5rem; margin-bottom:.5rem; }
.wizard-label { font-weight:600; font-size:.95rem; }
.wizard-acik { color:var(--gri-metin); font-size:.8rem; }
.wizard-step { display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem; }
.wizard-secili { background:var(--kiremit); color:#fff; padding:.3rem 1rem; border-radius:999px; font-size:.85rem; }
.wizard-adimlar { display:flex; gap:.5rem; align-items:center; font-size:.85rem; }
.wizard-adim { width:28px; height:28px; border-radius:50%; background:var(--gri-acik); display:flex; align-items:center; justify-content:center; font-size:.75rem; font-weight:600; }
.wizard-adim.aktif { background:var(--kiremit); color:#fff; }
.wizard-palettes { display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); gap:1rem; margin-top:1rem; }
.wizard-palet-kart { background:var(--krem); border-radius:var(--r-sm); padding:1rem; cursor:pointer; text-align:center; transition:.2s; }
.wizard-palet-kart:hover { transform:translateY(-2px); box-shadow:var(--golge); }
.wizard-palet-renkler { display:flex; gap:6px; justify-content:center; margin-bottom:.5rem; }
.wizard-palet-renkler span { width:32px; height:32px; border-radius:50%; border:2px solid #fff; box-shadow:0 1px 4px rgba(0,0,0,.15); }
.wizard-palet-ad { font-size:.85rem; font-weight:600; }
.market-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:1rem; margin-top:1rem; }
.market-kart { background:var(--krem); border-radius:var(--r-sm); padding:1.2rem; }
.market-baslik { font-weight:600; font-size:.95rem; }
.market-acik { color:var(--gri-metin); font-size:.8rem; margin:.3rem 0; }
.market-vers { font-size:.75rem; color:var(--gri-metin); }
`;
  document.head.appendChild(s);
})();

// ── /CMS Admin ────────────────────────────────────────────────────────────────
window.adminMenuler = adminMenuler;
window.adminMenuOgelr = adminMenuOgelr;
window.adminSayfalar = adminSayfalar;
window.adminWidgetler = adminWidgetler;
window.adminTema = adminTema;
window.adminSablonlar = adminSablonlar;

window.kayitYap = kayitYap;
window.bannerlariYukle = bannerlariYukle;
window.sliderGit = sliderGit;
window.sliderGitDirekt = sliderGitDirekt;
window.duyuruKapat = duyuruKapat;
window.adminBannerlar = adminBannerlar;
window.bannerYeniModal = bannerYeniModal;
window.bannerDuzenleModal = bannerDuzenleModal;
window.bannerFormModal = bannerFormModal;
window.bannerKaydet = bannerKaydet;
window.bannerResimModal = bannerResimModal;
window.bannerToggle = bannerToggle;
window.bannerSil = bannerSil;
window.bannerResimSec = bannerResimSec;
window.bannerResimSil = bannerResimSil;
window.baslat = baslat;

window.sifreSifirlaModalAc = sifreSifirlaModalAc;
window.sifreSifirlaBaslat = sifreSifirlaBaslat;
window.sifreSifirlaTogele = sifreSifirlaTogele;

window.bindApiUi({
  bildirim,
  onUnauthorized() {
    TOKEN = "";
    kullanici = null;
    if (typeof authGuncelle === "function") authGuncelle();
  }
});

syncTokenFromApi();
baslat();
