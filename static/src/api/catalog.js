/**
 * Kategori ağacı — mock/server bağımsız sabit referans (backend ile aynı sözleşme).
 * Tekrarlayan hardcoded domain listelerini UI'dan uzak tutmak için burada tutulur;
 * server modunda getKategoriler() backend'den gelir.
 */
export const KATEGORILER = {
  "Konut": ["Satılık", "Kiralık", "Devren Satılık", "Devren Kiralık"],
  "İş Yeri": ["Satılık", "Kiralık", "Devren Satılık", "Devren Kiralık"],
  "Arsa": ["Satılık", "Kiralık"],
  "Konut Projeleri": ["Satılık"],
  "Bina": ["Satılık", "Kiralık"],
  "Devre Mülk": ["Satılık", "Kiralık"],
  "Turistik Tesis": ["Satılık", "Kiralık"],
};

export const ILAN_TIPLERI = {
  "Konut": {
    "Satılık": ["Daire", "Rezidans", "Villa", "Yazlık", "Müstakil Ev", "Kooperatif", "Bungalov"],
    "Kiralık": ["Daire", "Rezidans", "Villa", "Yazlık", "Müstakil Ev"],
    "Devren Satılık": ["Daire", "Rezidans", "Villa", "Müstakil Ev"],
    "Devren Kiralık": ["Daire", "Rezidans", "Villa", "Müstakil Ev"],
  },
  "İş Yeri": {
    "Satılık": ["Ofis", "Dükkan/Mağaza", "Depo/Antrepo", "Atölye", "Fabrika", "Akaryakıt İstasyonu"],
    "Kiralık": ["Ofis", "Dükkan/Mağaza", "Depo/Antrepo", "Atölye", "Fabrika"],
    "Devren Satılık": ["Ofis", "Dükkan/Mağaza", "Atölye"],
    "Devren Kiralık": ["Ofis", "Dükkan/Mağaza", "Atölye"],
  },
  "Arsa": {
    "Satılık": ["Konut Arsası", "Ticari Arsa", "Tarla", "Bahçe", "Bağ", "Çiftlik"],
    "Kiralık": ["Tarla", "Bahçe", "Bağ"],
  },
  "Konut Projeleri": {
    "Satılık": ["Daire", "Villa", "Rezidans", "Müstakil"],
  },
  "Bina": {
    "Satılık": ["Apartman", "İş Merkezi", "Fabrika", "Otel"],
    "Kiralık": ["Apartman", "İş Merkezi"],
  },
  "Devre Mülk": {
    "Satılık": ["Devre Mülk"],
    "Kiralık": ["Devre Mülk"],
  },
  "Turistik Tesis": {
    "Satılık": ["Otel", "Pansiyon", "Tatil Köyü", "Kamp Alanı"],
    "Kiralık": ["Otel", "Pansiyon", "Tatil Köyü", "Kamp Alanı"],
  },
};

export const BANNER_KONUMLAR = {
  anasayfa_ust: "Ana Sayfa — En Üst",
  anasayfa_hero_alti: "Ana Sayfa — Hero Altı",
  ilanlar_ust: "İlanlar Sayfası — Üst",
  haberler_ust: "Haberler Sayfası — Üst",
  tum_sayfalar_ust: "Tüm Sayfalarda — Navbar Altı",
  tum_sayfalar_alt: "Tüm Sayfalarda — Footer Üstü",
};

export const BANNER_BOYUTLAR = {
  tam: { label: "Tam Genişlik", yukseklik: 400 },
  genis: { label: "Geniş", yukseklik: 300 },
  orta: { label: "Orta", yukseklik: 220 },
  ince: { label: "İnce Şerit", yukseklik: 120 },
};

const ALAN_SABLONLARI = {
  konut_satilik: [
    { key: "net_m2", label: "Net m²", type: "number" },
    { key: "brut_m2", label: "Brüt m²", type: "number" },
    { key: "oda_sayisi", label: "Oda Sayısı", type: "select", options: ["1+0", "1+1", "2+0", "2+1", "3+1", "3+2", "4+1", "4+2", "5+1", "5+2", "6+"] },
    { key: "bina_kati", label: "Bina Katı", type: "number" },
    { key: "bulundugu_kat", label: "Bulunduğu Kat", type: "number" },
    { key: "bina_yasi", label: "Bina Yaşı", type: "number" },
    { key: "isitma", label: "Isıtma", type: "select", options: ["Doğalgaz (Kombi)", "Doğalgaz (Merkezi)", "Klima", "Elektrikli", "Soba", "Yerden Isıtma", "Yok"] },
    { key: "banyo_sayisi", label: "Banyo Sayısı", type: "number" },
    { key: "tapu_durumu", label: "Tapu Durumu", type: "select", options: ["Kat Mülkiyeti", "Kat İrtifakı", "Arsa Tapusu", "Hisseli Tapu"] },
    { key: "krediye_uygun", label: "Krediye Uygun", type: "select", options: ["Var", "Yok"] },
    { key: "cephe", label: "Cephe", type: "text" },
    { key: "esyali", label: "Eşyalı", type: "select", options: ["Yok", "Var", "Yarı Eşyalı"] },
    { key: "balkon", label: "Balkon", type: "select", options: ["Var", "Yok"] },
    { key: "asansor", label: "Asansör", type: "select", options: ["Var", "Yok"] },
    { key: "otopark", label: "Otopark", type: "select", options: ["Var", "Yok", "Açık", "Kapalı"] },
    { key: "site_icinde", label: "Site İçinde", type: "select", options: ["Evet", "Hayır"] },
    { key: "kullanim", label: "Kullanım Durumu", type: "select", options: ["Boş", "Kiracılı", "Mal Sahibi"] },
    { key: "takas", label: "Takas", type: "select", options: ["Var", "Yok"] },
    { key: "ada", label: "Ada", type: "text" },
    { key: "parsel", label: "Parsel", type: "text" },
    { key: "ozellikler", label: "Değer Katan Özellikler", type: "textarea" },
  ],
  konut_kiralik: [
    { key: "net_m2", label: "Net m²", type: "number" },
    { key: "brut_m2", label: "Brüt m²", type: "number" },
    { key: "oda_sayisi", label: "Oda Sayısı", type: "select", options: ["1+0", "1+1", "2+0", "2+1", "3+1", "3+2", "4+1", "4+2", "5+1", "5+2", "6+"] },
    { key: "bina_kati", label: "Bina Katı", type: "number" },
    { key: "bulundugu_kat", label: "Bulunduğu Kat", type: "number" },
    { key: "bina_yasi", label: "Bina Yaşı", type: "number" },
    { key: "isitma", label: "Isıtma", type: "select", options: ["Doğalgaz (Kombi)", "Doğalgaz (Merkezi)", "Klima", "Elektrikli", "Soba", "Yerden Isıtma", "Yok"] },
    { key: "banyo_sayisi", label: "Banyo Sayısı", type: "number" },
    { key: "esyali", label: "Eşyalı", type: "select", options: ["Yok", "Var", "Yarı Eşyalı"] },
    { key: "balkon", label: "Balkon", type: "select", options: ["Var", "Yok"] },
    { key: "asansor", label: "Asansör", type: "select", options: ["Var", "Yok"] },
    { key: "otopark", label: "Otopark", type: "select", options: ["Var", "Yok"] },
    { key: "site_icinde", label: "Site İçinde", type: "select", options: ["Evet", "Hayır"] },
    { key: "depozito", label: "Depozito (ay)", type: "number" },
    { key: "aidat", label: "Aidat (TL)", type: "number" },
    { key: "ozellikler", label: "Değer Katan Özellikler", type: "textarea" },
  ],
  isyeri_satilik: [
    { key: "net_m2", label: "Net m²", type: "number" },
    { key: "brut_m2", label: "Brüt m²", type: "number" },
    { key: "kat", label: "Kat", type: "number" },
    { key: "bina_yasi", label: "Bina Yaşı", type: "number" },
    { key: "isitma", label: "Isıtma", type: "select", options: ["Klima", "Doğalgaz (Kombi)", "Doğalgaz (Merkezi)", "Elektrikli", "Soba", "Yok"] },
    { key: "tapu_durumu", label: "Tapu Durumu", type: "select", options: ["Kat Mülkiyeti", "Kat İrtifakı", "Arsa Tapusu", "Hisseli Tapu"] },
    { key: "krediye_uygun", label: "Krediye Uygun", type: "select", options: ["Var", "Yok"] },
    { key: "kullanim", label: "Kullanım Durumu", type: "select", options: ["Boş", "Kiracılı", "Mal Sahibi"] },
    { key: "takas", label: "Takas", type: "select", options: ["Var", "Yok"] },
    { key: "cephe", label: "Cephe", type: "text" },
    { key: "asansor", label: "Asansör", type: "select", options: ["Var", "Yok"] },
    { key: "otopark", label: "Otopark", type: "select", options: ["Var", "Yok", "Açık", "Kapalı"] },
    { key: "ozellikler", label: "Özellikler", type: "textarea" },
  ],
  arsa: [
    { key: "alan_m2", label: "Alan (m²)", type: "number" },
    { key: "ada", label: "Ada", type: "text" },
    { key: "parsel", label: "Parsel", type: "text" },
    { key: "kaks", label: "KAKS/EMSAL", type: "text" },
    { key: "taks", label: "TAKS", type: "text" },
    { key: "imar_durumu", label: "İmar Durumu", type: "select", options: ["Konut İmarlı", "Ticari İmarlı", "Tarım", "Orman", "İmarsız", "Plansız"] },
    { key: "tapu_durumu", label: "Tapu Durumu", type: "select", options: ["Arsa Tapusu", "Hisseli Tapu", "Tarla Tapusu"] },
    { key: "takas", label: "Takas", type: "select", options: ["Var", "Yok"] },
    { key: "ozellikler", label: "Özellikler", type: "textarea" },
  ],
  turistik: [
    { key: "net_m2", label: "Net m²", type: "number" },
    { key: "oda_sayisi", label: "Oda/Suit Sayısı", type: "number" },
    { key: "yatak_kapasitesi", label: "Yatak Kapasitesi", type: "number" },
    { key: "yildiz", label: "Yıldız", type: "select", options: ["1", "2", "3", "4", "5", "Butik", "Belspaş", "Pansiyon"] },
    { key: "havuz", label: "Havuz", type: "select", options: ["Var", "Yok", "Kapalı", "Açık"] },
    { key: "plaj", label: "Plaj/Deniz", type: "select", options: ["Denize Sıfır", "Yakın", "Uzak"] },
    { key: "tapu_durumu", label: "Tapu Durumu", type: "select", options: ["Kat Mülkiyeti", "Arsa Tapusu", "Hisseli Tapu"] },
    { key: "ozellikler", label: "Özellikler", type: "textarea" },
  ],
  genel: [
    { key: "net_m2", label: "Net m²", type: "number" },
    { key: "brut_m2", label: "Brüt m²", type: "number" },
    { key: "tapu_durumu", label: "Tapu Durumu", type: "select", options: ["Kat Mülkiyeti", "Arsa Tapusu", "Hisseli Tapu"] },
    { key: "ozellikler", label: "Özellikler", type: "textarea" },
  ],
};

/**
 * @param {string} anaKat
 * @param {string} altKat
 * @returns {object[]}
 */
export function alanSablonuSec(anaKat, altKat) {
  const kiralik = altKat === "Kiralık" || altKat === "Devren Kiralık";
  if ((anaKat || "").includes("Arsa")) return ALAN_SABLONLARI.arsa;
  if ((anaKat || "").includes("Turistik")) return ALAN_SABLONLARI.turistik;
  if ((anaKat || "").includes("İş") || (anaKat || "").includes("Ticari")) return ALAN_SABLONLARI.isyeri_satilik;
  if ((anaKat || "").includes("Konut")) return kiralik ? ALAN_SABLONLARI.konut_kiralik : ALAN_SABLONLARI.konut_satilik;
  return ALAN_SABLONLARI.genel;
}

/**
 * Derin kopya (JSON).
 * @template T
 * @param {T} v
 * @returns {T}
 */
export function clone(v) {
  return JSON.parse(JSON.stringify(v));
}

/**
 * Query string oluşturur (değerler encode edilir).
 * @param {Record<string, any>} params
 * @returns {string}
 */
export function toQuery(params = {}) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null) return;
    sp.set(k, String(v));
  });
  const s = sp.toString();
  return s ? `?${s}` : "";
}

/**
 * Basit slug üretimi.
 * @param {string} text
 * @returns {string}
 */
export function slugify(text) {
  return String(text || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 80) || `yazi-${Date.now()}`;
}
