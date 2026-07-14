/**
 * Mock veri katmanı — fetch Kullanılmaz.
 * JSON modüller ES import ile yüklenir; CRUD bellek üzerinde yapılır.
 */
import ayarlarData from "../mock/ayarlar.json" with { type: "json" };
import blogData from "../mock/blog.json" with { type: "json" };
import bannerlarData from "../mock/bannerlar.json" with { type: "json" };
import portfoylerData from "../mock/portfoyler.json" with { type: "json" };
import kullaniciData from "../mock/kullanici.json" with { type: "json" };
import isteklerData from "../mock/istekler.json" with { type: "json" };

import { ApiError } from "./errors.js";
import {
  KATEGORILER,
  ILAN_TIPLERI,
  BANNER_KONUMLAR,
  BANNER_BOYUTLAR,
  alanSablonuSec,
  clone,
  slugify,
} from "./catalog.js";

/**
 * @returns {object}
 */
function emptyState() {
  return {
    ayarlar: clone(ayarlarData),
    blog: clone(blogData),
    bannerlar: clone(bannerlarData),
    portfoyler: clone(portfoylerData),
    istekler: clone(isteklerData || []),
    hesaplar: clone(kullaniciData.demo_hesaplar || []),
    kullanicilar: clone(kullaniciData.liste || []),
    oturum: null,
    nextIds: {
      portfoy: 1000,
      blog: 1000,
      banner: 1000,
      istek: 1000,
      kullanici: 1000,
    },
  };
}

export class MockAdapter {
  constructor() {
    /** @private */
    this.state = emptyState();
    for (const p of this.state.portfoyler) {
      this.state.nextIds.portfoy = Math.max(this.state.nextIds.portfoy, (p.id || 0) + 1);
    }
    for (const b of this.state.blog) {
      this.state.nextIds.blog = Math.max(this.state.nextIds.blog, (b.id || 0) + 1);
    }
    for (const b of this.state.bannerlar) {
      this.state.nextIds.banner = Math.max(this.state.nextIds.banner, (b.id || 0) + 1);
    }
  }

  /** @private */
  _requireAuth(adminOnly = false) {
    if (!this.state.oturum) throw new ApiError(401, "Giriş yapmanız gerekiyor");
    if (adminOnly && this.state.oturum.rol !== "admin") {
      throw new ApiError(403, "Bu işlem için yetkiniz yok");
    }
    return this.state.oturum;
  }

  /**
   * @param {string} email
   * @param {string} sifre
   */
  async login(email, sifre) {
    const hesap = this.state.hesaplar.find(
      (h) => h.email.toLowerCase() === String(email || "").toLowerCase().trim()
    );
    if (!hesap || hesap.sifre !== sifre) {
      throw new ApiError(400, "Email veya şifre hatalı");
    }
    if (!hesap.onay && hesap.rol !== "admin") {
      throw new ApiError(403, "Hesabınız henüz admin onayı bekliyor.");
    }
    const token = `mock-jwt-${hesap.id}-${Date.now()}`;
    this.state.oturum = {
      id: hesap.id,
      email: hesap.email,
      ad_soyad: hesap.ad_soyad,
      rol: hesap.rol,
      onay: hesap.onay,
      profil_resmi: hesap.profil_resmi || "",
      access_token: token,
    };
    return {
      access_token: token,
      token_type: "bearer",
      rol: hesap.rol,
      ad: hesap.ad_soyad,
    };
  }

  async logout() {
    this.state.oturum = null;
    return { mesaj: "Çıkış yapıldı" };
  }

  async getMe() {
    if (!this.state.oturum) return { giris: false };
    const o = this.state.oturum;
    return {
      giris: true,
      id: o.id,
      ad_soyad: o.ad_soyad,
      email: o.email,
      rol: o.rol,
      onay: o.onay,
      profil_resmi: o.profil_resmi || "",
    };
  }

  async getAyarlar() {
    return clone(this.state.ayarlar);
  }

  async updateAyarlar(ayarlar) {
    this._requireAuth(true);
    Object.assign(this.state.ayarlar, ayarlar || {});
    return { mesaj: "Ayarlar kaydedildi" };
  }

  async updateAiAyarlar(data) {
    this._requireAuth(true);
    if (data.ai_api_key != null) this.state.ayarlar.ai_api_key = data.ai_api_key;
    if (data.ai_saglayici != null) this.state.ayarlar.ai_saglayici = data.ai_saglayici;
    return { mesaj: "AI ayarları kaydedildi" };
  }

  /**
   * @param {{konum?: string, sadece_aktif?: boolean|number|string}} [params]
   */
  async getBannerlar(params = {}) {
    let list = clone(this.state.bannerlar);
    if (params.konum) list = list.filter((b) => b.konum === params.konum);
    if (params.sadece_aktif == 1 || params.sadece_aktif === true || params.sadece_aktif === "1") {
      list = list.filter((b) => b.aktif);
    }
    return list.sort((a, b) => (a.sira || 0) - (b.sira || 0) || a.id - b.id);
  }

  async getBannerKonumlar() {
    return { konumlar: BANNER_KONUMLAR, boyutlar: BANNER_BOYUTLAR };
  }

  /**
   * @param {{durum?: string}} [params]
   */
  async getBlog(params = {}) {
    let list = clone(this.state.blog);
    const durum = params.durum;
    if (durum === undefined || durum === null) {
      list = list.filter((y) => y.durum === "Yayında" || y.durum === "Aktif");
    } else if (durum !== "") {
      list = list.filter((y) => y.durum === durum);
    }
    return list;
  }

  async getBlogBySlugOrId(key) {
    const y = this.state.blog.find(
      (b) => String(b.id) === String(key) || b.slug === key
    );
    if (!y) throw new ApiError(404, "Yazı bulunamadı");
    return clone(y);
  }

  /**
   * @param {{kategori?: string, alt_kat?: string, durum?: string, arama?: string}} [params]
   */
  async getPortfoyler(params = {}) {
    const oturum = this.state.oturum;
    const isAdmin = oturum && oturum.rol === "admin";
    let list = clone(this.state.portfoyler);

    if (!isAdmin) {
      list = list.filter((p) => p.durum === "Aktif");
    } else if (params.durum !== undefined && params.durum !== null && params.durum !== "") {
      list = list.filter((p) => p.durum === params.durum);
    }

    if (params.kategori) list = list.filter((p) => p.ana_kategori === params.kategori);
    if (params.alt_kat) list = list.filter((p) => p.alt_kategori === params.alt_kat);
    if (params.arama) {
      const q = String(params.arama).toLowerCase();
      list = list.filter(
        (p) =>
          (p.baslik || "").toLowerCase().includes(q) ||
          (p.mahalle || "").toLowerCase().includes(q) ||
          (p.ilce || "").toLowerCase().includes(q)
      );
    }
    return list;
  }

  async getPortfoy(id) {
    const p = this.state.portfoyler.find((x) => String(x.id) === String(id));
    if (!p) throw new ApiError(404, "Portföy bulunamadı");
    const isAdmin = this.state.oturum && this.state.oturum.rol === "admin";
    if (!isAdmin && p.durum !== "Aktif") throw new ApiError(404, "Portföy bulunamadı");
    return clone(p);
  }

  /**
   * @param {string} q
   */
  async arama(q) {
    return this.getPortfoyler({ arama: q, durum: "Aktif" });
  }

  /**
   * Müşteri istek formu.
   * @param {object} data
   */
  async iletisim(data) {
    const id = this.state.nextIds.istek++;
    this.state.istekler.unshift({
      id,
      ad_soyad: data.ad_soyad || "",
      telefon: data.telefon || "",
      email: data.email || "",
      mesaj: data.mesaj || "",
      portfoy_id: data.portfoy_id || null,
      durum: "Yeni",
      olusturma: new Date().toISOString().slice(0, 19).replace("T", " "),
      portfoy_baslik: "",
    });
    return { mesaj: "İsteğiniz alındı, en kısa sürede dönüş yapılacak." };
  }

  async getIstekler() {
    this._requireAuth(true);
    return clone(this.state.istekler);
  }

  async updateIstekDurum(id, durum) {
    this._requireAuth(true);
    const it = this.state.istekler.find((x) => String(x.id) === String(id));
    if (!it) throw new ApiError(404, "İstek bulunamadı");
    it.durum = durum;
    return { mesaj: "Güncellendi" };
  }

  async getKategoriler() {
    return { kategoriler: KATEGORILER, ilan_tipleri: ILAN_TIPLERI };
  }

  async getAlanlar(anaKat, altKat, ilanTipi = "") {
    return alanSablonuSec(anaKat, altKat, ilanTipi);
  }

  async getIstatistik() {
    const list = this.state.portfoyler;
    const aktif = list.filter((p) => p.durum === "Aktif").length;
    const dag = {};
    list.filter((p) => p.durum === "Aktif").forEach((p) => {
      dag[p.ana_kategori] = (dag[p.ana_kategori] || 0) + 1;
    });
    const sonuc = {
      toplam: aktif,
      aktif,
      taslak: 0,
      yeni_istekler: 0,
      kategori_dagilimi: Object.entries(dag).map(([ana_kategori, sayi]) => ({ ana_kategori, sayi })),
    };
    if (this.state.oturum && this.state.oturum.rol === "admin") {
      sonuc.toplam = list.length;
      sonuc.taslak = list.filter((p) => p.durum === "Taslak").length;
      sonuc.yeni_istekler = this.state.istekler.filter((i) => i.durum === "Yeni").length;
    }
    return sonuc;
  }

  /**
   * Genel kayıt oluşturma.
   * @param {string} resource
   * @param {object} data
   */
  async save(resource, data) {
    switch (resource) {
      case "portfoyler":
        return this._savePortfoy(data);
      case "blog":
        return this._saveBlog(data);
      case "bannerlar":
        return this._saveBanner(data);
      case "kullanicilar":
        return this._saveKullanici(data, false);
      case "kullanicilar/kayit":
        return this._saveKullanici(data, true);
      case "auth/sifre-sifirlama-baslat":
        return {
          mesaj:
            "Mock mod: token sunucuya yazılmaz. Demo için sonraki adımda herhangi bir token kullanabilirsiniz.",
        };
      case "auth/sifre-sifirlama-tamamla":
        return { mesaj: "Mock mod: şifre güncellenmiş varsayıldı." };
      default:
        throw new ApiError(404, `Bilinmeyen kaynak: ${resource}`);
    }
  }

  /**
   * @param {string} resource
   * @param {string|number} id
   * @param {object} data
   * @param {{action?: string, query?: object}} [opts]
   */
  async update(resource, id, data = {}, opts = {}) {
    const action = opts.action || "";
    if (resource === "portfoyler" && action === "durum") {
      this._requireAuth(true);
      const p = this.state.portfoyler.find((x) => String(x.id) === String(id));
      if (!p) throw new ApiError(404, "Portföy bulunamadı");
      p.durum = (opts.query && opts.query.durum) || data.durum;
      p.guncelleme = new Date().toISOString().slice(0, 19).replace("T", " ");
      return { mesaj: "Durum güncellendi" };
    }
    if (resource === "portfoyler" && action === "resim-sirala") {
      this._requireAuth(true);
      const p = this.state.portfoyler.find((x) => String(x.id) === String(id));
      if (!p) throw new ApiError(404);
      p.resimler = data.resimler || data || [];
      return { mesaj: "Sıra kaydedildi" };
    }
    if (resource === "portfoyler" && action === "resim-kapak") {
      this._requireAuth(true);
      const p = this.state.portfoyler.find((x) => String(x.id) === String(id));
      if (!p) throw new ApiError(404);
      const url = (opts.query && opts.query.url) || data.url;
      const imgs = p.resimler || [];
      const i = imgs.indexOf(url);
      if (i > 0) {
        imgs.splice(i, 1);
        imgs.unshift(url);
        p.resimler = imgs;
      }
      return { mesaj: "Kapak güncellendi", resimler: clone(p.resimler) };
    }
    if (resource === "istekler" && action === "durum") {
      return this.updateIstekDurum(id, (opts.query && opts.query.durum) || data.durum);
    }
    if (resource === "bannerlar" && action === "aktif") {
      this._requireAuth(true);
      const b = this.state.bannerlar.find((x) => String(x.id) === String(id));
      if (!b) throw new ApiError(404);
      b.aktif = Number((opts.query && opts.query.aktif) ?? data.aktif);
      return { mesaj: "Durum güncellendi" };
    }
    if (resource === "kullanicilar" && action === "onayla") {
      this._requireAuth(true);
      const k = this.state.kullanicilar.find((x) => String(x.id) === String(id));
      if (!k) throw new ApiError(404);
      k.onay = 1;
      return { mesaj: "Onaylandı" };
    }
    if (resource === "kullanicilar" && action === "onay-kaldir") {
      this._requireAuth(true);
      const k = this.state.kullanicilar.find((x) => String(x.id) === String(id));
      if (!k) throw new ApiError(404);
      k.onay = 0;
      return { mesaj: "Onay kaldırıldı" };
    }
    if (resource === "kullanicilar" && action === "profil") {
      this._requireAuth();
      Object.assign(this.state.oturum, data);
      const k = this.state.kullanicilar.find((x) => x.id === this.state.oturum.id);
      if (k) Object.assign(k, data);
      return { mesaj: "Profil güncellendi" };
    }
    if (resource === "kullanicilar" && action === "sifre") {
      this._requireAuth();
      return { mesaj: "Şifre güncellendi" };
    }
    if (resource === "ayarlar") {
      return this.updateAyarlar(data.ayarlar || data);
    }
    if (resource === "ayarlar/ai") {
      return this.updateAiAyarlar(data);
    }
    if (resource === "portfoyler") {
      this._requireAuth(true);
      const p = this.state.portfoyler.find((x) => String(x.id) === String(id));
      if (!p) throw new ApiError(404, "Portföy bulunamadı");
      Object.assign(p, data, { id: p.id, guncelleme: new Date().toISOString().slice(0, 19).replace("T", " ") });
      return { mesaj: "Güncellendi", id: p.id };
    }
    if (resource === "blog") {
      this._requireAuth(true);
      const y = this.state.blog.find((x) => String(x.id) === String(id));
      if (!y) throw new ApiError(404);
      Object.assign(y, data, { id: y.id, guncelleme: new Date().toISOString().slice(0, 19).replace("T", " ") });
      return { mesaj: "Güncellendi", id: y.id };
    }
    if (resource === "bannerlar") {
      this._requireAuth(true);
      const b = this.state.bannerlar.find((x) => String(x.id) === String(id));
      if (!b) throw new ApiError(404);
      Object.assign(b, data, { id: b.id });
      return { mesaj: "Güncellendi" };
    }
    throw new ApiError(404, `Güncellenemedi: ${resource}`);
  }

  /**
   * @param {string} resource
   * @param {string|number} id
   * @param {{action?: string, query?: object}} [opts]
   */
  async delete(resource, id, opts = {}) {
    this._requireAuth(true);
    if (resource === "portfoyler" && opts.action === "resim") {
      const p = this.state.portfoyler.find((x) => String(x.id) === String(id));
      if (!p) throw new ApiError(404);
      const url = opts.query && opts.query.url;
      p.resimler = (p.resimler || []).filter((u) => u !== url);
      return { mesaj: "Resim silindi", resimler: clone(p.resimler) };
    }
    if (resource === "logo") {
      this.state.ayarlar.logo_url = "";
      return { mesaj: "Logo silindi" };
    }
    if (resource === "bannerlar" && opts.action === "resim-sil") {
      const b = this.state.bannerlar.find((x) => String(x.id) === String(id));
      if (b) b.resim_url = "";
      return { mesaj: "Resim silindi" };
    }
    const collections = {
      portfoyler: this.state.portfoyler,
      blog: this.state.blog,
      bannerlar: this.state.bannerlar,
      kullanicilar: this.state.kullanicilar,
    };
    const arr = collections[resource];
    if (!arr) throw new ApiError(404, `Bilinmeyen kaynak: ${resource}`);
    const idx = arr.findIndex((x) => String(x.id) === String(id));
    if (idx < 0) throw new ApiError(404, "Kayıt bulunamadı");
    arr.splice(idx, 1);
    return { mesaj: "Silindi" };
  }

  /**
   * Mock yükleme — dosya içeriği işlenmez, sahte URL döner.
   * @param {string} resource
   * @param {string|number|null} id
   * @param {FormData} _formData
   * @param {{kind?: string, query?: object}} [opts]
   */
  async upload(resource, id, _formData, opts = {}) {
    this._requireAuth(resource !== "belge");
    const kind = opts.kind || "resim";
    const fake = `/static/uploads/mock_${Date.now()}.webp`;

    if (resource === "portfoyler" && kind === "resim") {
      const p = this.state.portfoyler.find((x) => String(x.id) === String(id));
      if (!p) throw new ApiError(404);
      p.resimler = p.resimler || [];
      p.resimler.push(fake);
      return { mesaj: "Yüklendi", url: fake, resimler: clone(p.resimler) };
    }
    if (resource === "logo") {
      this.state.ayarlar.logo_url = fake;
      return { mesaj: "Logo yüklendi", url: fake };
    }
    if (resource === "bannerlar") {
      const b = this.state.bannerlar.find((x) => String(x.id) === String(id));
      if (!b) throw new ApiError(404);
      b.resim_url = fake;
      return { mesaj: "Yüklendi", url: fake };
    }
    if (resource === "blog" && kind === "kapak") {
      const y = this.state.blog.find((x) => String(x.id) === String(id));
      if (!y) throw new ApiError(404);
      y.kapak_resim = fake;
      return { mesaj: "Kapak yüklendi", url: fake };
    }
    if (resource === "blog" && kind === "icerik-resim") {
      return { url: fake, boyut: (opts.query && opts.query.boyut) || "orta", konum: (opts.query && opts.query.konum) || "sol" };
    }
    if (resource === "kullanicilar" && kind === "profil-resmi") {
      if (this.state.oturum) this.state.oturum.profil_resmi = fake;
      return { mesaj: "Yüklendi", url: fake };
    }
    if (resource === "belge" && kind === "parse") {
      return {
        portfoy: {
          baslik: "Mock Belge İlanı",
          ana_kategori: "Konut",
          alt_kategori: "Satılık",
          ilan_tipi: "Daire",
          il: "Muğla",
          ilce: "Fethiye",
          mahalle: "",
          fiyat: "1.000.000",
          para_birimi: "TL",
          aciklama: "Mock belge içeriği (Cloudflare demo).",
          alanlar: { net_m2: "120", oda_sayisi: "3+1" },
        },
        alan_sablonu: alanSablonuSec("Konut", "Satılık"),
      };
    }
    return { url: fake, mesaj: "Yüklendi" };
  }

  /**
   * @param {string} resource
   * @param {string|number} id
   * @param {{kind?: string}} [opts]
   * @returns {Promise<Blob|{url:string}>}
   */
  async download(resource, id, opts = {}) {
    if (resource === "portfoyler" && (opts.kind === "pdf" || !opts.kind)) {
      const p = await this.getPortfoy(id);
      const text = `Portföy #${p.id}\n${p.baslik}\n${p.fiyat || ""}\n(Mock PDF)`;
      return new Blob([text], { type: "application/pdf" });
    }
    throw new ApiError(404, "İndirilecek kaynak bulunamadı");
  }

  async getKullanicilar() {
    this._requireAuth(true);
    return clone(this.state.kullanicilar);
  }

  async getKullaniciBen() {
    this._requireAuth();
    return clone({
      id: this.state.oturum.id,
      ad_soyad: this.state.oturum.ad_soyad,
      email: this.state.oturum.email,
      rol: this.state.oturum.rol,
      onay: this.state.oturum.onay,
      profil_resmi: this.state.oturum.profil_resmi || "",
    });
  }

  async getSahipProfil(pid) {
    const p = await this.getPortfoy(pid);
    return {
      ad_soyad: p.musteri_ad || this.state.ayarlar.site_adi || "Danışman",
      profil_resmi: "",
      telefon: p.musteri_tel || this.state.ayarlar.telefon || "",
    };
  }

  async getFiyatAnalizi(id) {
    const p = await this.getPortfoy(id);
    return {
      baslik: p.baslik,
      tahmin: p.fiyat || "—",
      aciklama: "Mock fiyat analizi (demo modu).",
      benzerler: [],
    };
  }

  async getFiyatAnaliziGenel() {
    this._requireAuth(true);
    return { mesaj: "Mock genel analiz", ozet: "Demo verisi" };
  }

  /** @private */
  _savePortfoy(data) {
    this._requireAuth(true);
    const id = this.state.nextIds.portfoy++;
    const now = new Date().toISOString().slice(0, 19).replace("T", " ");
    const kayit = {
      id,
      durum: "Taslak",
      resimler: [],
      alanlar: {},
      para_birimi: "TL",
      il: "Muğla",
      ilce: "Fethiye",
      kaynak: "web",
      olusturma: now,
      guncelleme: now,
      ...data,
      id,
    };
    this.state.portfoyler.unshift(kayit);
    return { mesaj: "Oluşturuldu", id };
  }

  /** @private */
  _saveBlog(data) {
    this._requireAuth(true);
    const id = this.state.nextIds.blog++;
    const now = new Date().toISOString().slice(0, 19).replace("T", " ");
    const kayit = {
      id,
      slug: data.slug || slugify(data.baslik),
      icerik: "",
      ozet: "",
      etiketler: [],
      kapak_resim: "",
      durum: "Taslak",
      yazar_id: this.state.oturum.id,
      olusturma: now,
      guncelleme: now,
      ...data,
      id,
    };
    this.state.blog.unshift(kayit);
    return { mesaj: "Oluşturuldu", id };
  }

  /** @private */
  _saveBanner(data) {
    this._requireAuth(true);
    const id = this.state.nextIds.banner++;
    const kayit = {
      id,
      tip: "slider",
      baslik: "",
      alt_metin: "",
      aciklama: "",
      resim_url: "",
      link_url: "",
      link_metin: "",
      link_hedef: "_self",
      renk_arka: "",
      renk_metin: "#ffffff",
      konum: "anasayfa_hero_alti",
      boyut: "genis",
      sira: 0,
      aktif: 1,
      olusturma: new Date().toISOString().slice(0, 19).replace("T", " "),
      ...data,
      id,
    };
    this.state.bannerlar.push(kayit);
    return { id, mesaj: "Banner oluşturuldu" };
  }

  /** @private */
  _saveKullanici(data, selfRegister) {
    if (!selfRegister) this._requireAuth(true);
    const id = this.state.nextIds.kullanici++;
    const kayit = {
      id,
      ad_soyad: data.ad_soyad,
      email: data.email,
      rol: data.rol || "kullanici",
      aktif: 1,
      onay: selfRegister ? 0 : 1,
      profil_resmi: "",
      olusturma: new Date().toISOString().slice(0, 19).replace("T", " "),
    };
    this.state.kullanicilar.push(kayit);
    this.state.hesaplar.push({ ...kayit, sifre: data.sifre || "degistir" });
    return { mesaj: selfRegister ? "Kayıt alındı, onay bekleniyor" : "Kullanıcı eklendi", id };
  }
}
