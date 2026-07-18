"""Şema oluşturma ve seed — Database katmanı."""
from __future__ import annotations

from backend.db.database import Database, db
from backend.core.password import hash_sifre


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS kullanicilar (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_soyad      TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    sifre         TEXT NOT NULL,
    rol           TEXT DEFAULT 'kullanici',
    aktif         INTEGER DEFAULT 1,
    onay_durumu   TEXT DEFAULT 'bekliyor',
    profil_resmi  TEXT DEFAULT '',
    olusturma     TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS _migrasyon_yapildi (ad TEXT PRIMARY KEY);

CREATE TABLE IF NOT EXISTS bannerlar (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tip         TEXT DEFAULT 'slider',
    baslik      TEXT DEFAULT '',
    aciklama    TEXT DEFAULT '',
    resim_url   TEXT DEFAULT '',
    link_url    TEXT DEFAULT '',
    link_metin  TEXT DEFAULT '',
    renk_arka   TEXT DEFAULT '',
    renk_metin  TEXT DEFAULT '#ffffff',
    konum       TEXT DEFAULT 'ana_hero_alti',
    boyut       TEXT DEFAULT 'genis',
    sira        INTEGER DEFAULT 0,
    aktif       INTEGER DEFAULT 1,
    olusturma   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS portfoyler (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    baslik          TEXT NOT NULL,
    ana_kategori    TEXT NOT NULL,
    alt_kategori    TEXT NOT NULL,
    ilan_tipi       TEXT,
    il              TEXT DEFAULT 'Mugla',
    ilce            TEXT DEFAULT 'Fethiye',
    mahalle         TEXT,
    fiyat           TEXT,
    para_birimi     TEXT DEFAULT 'TL',
    aciklama        TEXT,
    saha_notu       TEXT,
    gps             TEXT,
    durum           TEXT DEFAULT 'Taslak',
    alanlar         TEXT DEFAULT '{}',
    resimler        TEXT DEFAULT '[]',
    musteri_ad      TEXT,
    musteri_tel     TEXT,
    musteri_mail    TEXT,
    musteri_adres   TEXT DEFAULT '',
    musteri_tc      TEXT DEFAULT '',
    musteri_not     TEXT DEFAULT '',
    sahip_goster    INTEGER DEFAULT 0,
    kaynak          TEXT DEFAULT 'web',
    olusturma       TEXT DEFAULT (datetime('now')),
    guncelleme      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS kullanici_istekleri (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_soyad     TEXT,
    telefon      TEXT,
    email        TEXT,
    mesaj        TEXT,
    portfoy_id   INTEGER,
    durum        TEXT DEFAULT 'Yeni',
    olusturma    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(portfoy_id) REFERENCES portfoyler(id)
);

CREATE TABLE IF NOT EXISTS site_ayarlari (
    anahtar TEXT PRIMARY KEY,
    deger   TEXT
);

CREATE TABLE IF NOT EXISTS blog_yazilari (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    baslik      TEXT NOT NULL,
    slug        TEXT UNIQUE,
    icerik      TEXT DEFAULT '',
    ozet        TEXT DEFAULT '',
    etiketler   TEXT DEFAULT '[]',
    kapak_resim TEXT DEFAULT '',
    durum       TEXT DEFAULT 'Taslak',
    yazar_id    INTEGER,
    olusturma   TEXT DEFAULT (datetime('now')),
    guncelleme  TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════════════════
-- CMS v2.1 — Yeni modüler tablolar
-- Tüm tablolar idempotent (CREATE TABLE IF NOT EXISTS).
-- Frontend hardcode içermez — tüm veriler DB'den gelir.
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── Menü Yönetimi ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS menus (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    slug         TEXT UNIQUE NOT NULL,          -- 'ana-menu', 'footer-menu' vb.
    ad           TEXT NOT NULL,
    lokasyon     TEXT DEFAULT 'header',         -- header / footer / sidebar
    aktif        INTEGER DEFAULT 1,
    olusturma    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS menu_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_id       INTEGER NOT NULL,
    parent_id    INTEGER DEFAULT NULL,           -- alt menü (NULL üst düzey)
    baslik        TEXT NOT NULL,
    ikon          TEXT DEFAULT '',                -- emoji veya SVG key
    hedef_tip     TEXT DEFAULT 'dahili',          -- dahili / harici
    hedef_url     TEXT DEFAULT '',                -- harici URL veya slug
    hedef_page_id INTEGER DEFAULT NULL,           -- dahili ise pages.id
    gosterim      TEXT DEFAULT '_self',           -- _self / _blank
    izin_rol      TEXT DEFAULT '',                -- '', 'admin', 'kullanici'
    sira          INTEGER DEFAULT 0,
    aktif         INTEGER DEFAULT 1,
    dil          TEXT DEFAULT '',                 -- çoklu dil hazırlığı
    olusturma     TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(menu_id)    REFERENCES menus(id) ON DELETE CASCADE,
    FOREIGN KEY(parent_id)  REFERENCES menu_items(id) ON DELETE CASCADE,
    FOREIGN KEY(hedef_page_id) REFERENCES pages(id) ON DELETE SET NULL
);

-- ─── Sayfa Yönetimi ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pages (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    baslik        TEXT NOT NULL,
    slug          TEXT UNIQUE NOT NULL,
    icerik        TEXT DEFAULT '',                -- HTML (editör içeriği)
    ozet          TEXT DEFAULT '',
    seo_baslik       TEXT DEFAULT '',
    seo_aciklama     TEXT DEFAULT '',
    seo_anahtar_kelimeler TEXT DEFAULT '',
    kapak_resim   TEXT DEFAULT '',
    durum         TEXT DEFAULT 'Taslak',          -- Taslak / Yayınla / Arşiv
    sablon        TEXT DEFAULT 'default',         -- template key
    yazar_id      INTEGER DEFAULT NULL,
    olusturma     TEXT DEFAULT (datetime('now')),
    guncelleme    TEXT DEFAULT (datetime('now'))
);

-- ─── Widget Sistemi (aç/kapat) ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS widgets (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    anahtar       TEXT UNIQUE NOT NULL,            -- 'whatsapp', 'google_maps', ...
    ad            TEXT NOT NULL,
    aciklama      TEXT DEFAULT '',
    tip           TEXT DEFAULT 'embed',           -- embed / script / html / link
    aktif         INTEGER DEFAULT 0,
    ayarlar       TEXT DEFAULT '{}',              -- JSON: widget'a özel config
    konum         TEXT DEFAULT '',                -- footer / header / sidebar / floating
    sira          INTEGER DEFAULT 0,
    olusturma     TEXT DEFAULT (datetime('now')),
    guncelleme    TEXT DEFAULT (datetime('now'))
);

-- ─── Tema Ayarları (key-value) ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS theme_settings (
    anahtar   TEXT PRIMARY KEY,
    deger     TEXT
);

-- ─── Forum (opsiyonel) ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS forum_categories (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    slug          TEXT UNIQUE NOT NULL,
    ad            TEXT NOT NULL,
    aciklama      TEXT DEFAULT '',
    sira          INTEGER DEFAULT 0,
    aktif         INTEGER DEFAULT 1,
    olusturma     TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS forum_topics (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id   INTEGER NOT NULL,
    baslik        TEXT NOT NULL,
    slug          TEXT UNIQUE,
    icerik        TEXT DEFAULT '',
    kullanici_id  INTEGER,
    kullanici_ad  TEXT DEFAULT '',                -- misafir yazıyorsa
    goruntuleme   INTEGER DEFAULT 0,
    sabit         INTEGER DEFAULT 0,               -- pin
    kapali        INTEGER DEFAULT 0,
    durum         TEXT DEFAULT 'yayin',            -- yayin / taslak / moderasyon
    olusturma     TEXT DEFAULT (datetime('now')),
    guncelleme    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(category_id) REFERENCES forum_categories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS forum_posts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id      INTEGER NOT NULL,
    parent_id    INTEGER DEFAULT NULL,             -- alıntı / yanıt
    icerik        TEXT NOT NULL,
    kullanici_id  INTEGER,
    kullanici_ad  TEXT DEFAULT '',
    ip            TEXT DEFAULT '',
    durum         TEXT DEFAULT 'yayin',            -- yayin / moderasyon / silindi
    olusturma     TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(topic_id)   REFERENCES forum_topics(id) ON DELETE CASCADE,
    FOREIGN KEY(parent_id)  REFERENCES forum_posts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS forum_settings (
    anahtar   TEXT PRIMARY KEY,
    deger     TEXT
);
"""


def init_db(database: Database | None = None) -> None:
    database = database or db
    conn = database.connect()
    c = conn.cursor()
    c.executescript(SCHEMA_SQL)

    row = c.execute(
        "SELECT id FROM kullanicilar WHERE email=?",
        ("bilgi@portfoygayrimenkul.com.tr",),
    ).fetchone()
    if not row:
        c.execute(
            "INSERT INTO kullanicilar (ad_soyad,email,sifre,rol) VALUES (?,?,?,?)",
            (
                "Portföy Gayrimenkul",
                "bilgi@portfoygayrimenkul.com.tr",
                hash_sifre("admin123"),
                "admin",
            ),
        )

    defaults = {
        "site_adi": "Portföy Gayrimenkul",
        "site_slogan": "Fethiye'nin Güvenilir Gayrimenkul Danışmanı",
        "telefon": "0542 966 36 36",
        "email": "bilgi@portfoygayrimenkul.com.tr",
        "adres": "Fethiye / Muğla",
        "web_sitesi": "portfoygayrimenkul.com.tr",
        "renk_tema": "",
        "logo_url": "",
        "sosyal_ig": "",
        "sosyal_fb": "",
        "sosyal_wa": "",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO site_ayarlari VALUES (?,?)", (k, v))

    for mig in [
        "ALTER TABLE kullanicilar ADD COLUMN profil_resmi TEXT DEFAULT ''",
        "ALTER TABLE kullanicilar ADD COLUMN onay INTEGER DEFAULT 1",
        "ALTER TABLE portfoyler ADD COLUMN sahip_goster INTEGER DEFAULT 0",
        "ALTER TABLE portfoyler ADD COLUMN musteri_tc TEXT DEFAULT ''",
        "ALTER TABLE portfoyler ADD COLUMN musteri_adres TEXT DEFAULT ''",
        "ALTER TABLE portfoyler ADD COLUMN musteri_not TEXT DEFAULT ''",
        "ALTER TABLE bannerlar ADD COLUMN alt_metin TEXT DEFAULT ''",
        "ALTER TABLE bannerlar ADD COLUMN link_hedef TEXT DEFAULT '_self'",
    ]:
        try:
            c.execute(mig)
        except Exception:
            pass

    # ─── CMS v2.1 — Varsayılan seed'ler ────────────────────────────────────
    _seed_widgets(c)
    _seed_theme_settings(c)
    _seed_forum_settings(c)

    conn.commit()
    conn.close()


def _seed_widgets(c) -> None:
    """Varsayılan widget listesi — tümü KAPALI (aktif=0) olarak eklenir."""
    defaults = [
        ("whatsapp",       "WhatsApp Butonu",       "floating", "link"),
        ("google_maps",    "Google Maps",            "footer",   "embed"),
        ("canli_destek",   "Canlı Destek",           "floating", "script"),
        ("instagram",      "Instagram Beslemesi",   "footer",   "embed"),
        ("facebook",       "Facebook Beğen",         "footer",   "embed"),
        ("youtube",        "YouTube Kanal",          "footer",   "embed"),
        ("cookie_banner",  "Çerez Bildirimi",         "header",   "html"),
        ("newsletter",     "Bülten Aboneliği",       "footer",   "embed"),
        ("forum",          "Forum",                   "header",   "link"),
        ("arama",          "Hızlı Arama",            "header",   "embed"),
        ("dil_secici",     "Dil Seçici",              "header",   "embed"),
        ("telefon",        "Telefon Butonu",         "header",   "link"),
        ("eposta",         "E-Posta Butonu",          "footer",   "link"),
    ]
    for anahtar, ad, konum, tip in defaults:
        c.execute(
            "INSERT OR IGNORE INTO widgets (anahtar,ad,konum,tip,aktif,sira) "
            "VALUES (?,?,?,?,0,0)",
            (anahtar, ad, konum, tip),
        )


def _seed_theme_settings(c) -> None:
    """Varsayılan tema ayarları (key-value). Frontend hardcode'siz okur."""
    defaults = {
        "template":           "estate_modern",
        "renk_ana":           "#C45C35",
        "renk_ana_koy":       "#A34A28",
        "renk_arka":           "#FAF7F2",
        "renk_metin":          "#2D2016",
        "dark_mode":           "0",
        "font_baslik":         "Playfair Display",
        "font_govde":          "Inter",
        "border_radius":       "12",
        "shadow_kart":         "0 2px 12px rgba(45,32,22,0.09)",
        "header_stil":         "sticky",
        "footer_stil":         "default",
        "kart_stil":           "default",
        "animasyon":           "minimize",
        "button_stil":         "default",
        "logo_url":            "",
        "favicon_url":         "",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO theme_settings VALUES (?,?)", (k, v))


def _seed_forum_settings(c) -> None:
    """Varsayılan forum ayarları (forum kapalıyken de mevcut)."""
    defaults = {
        "forum_aktif":         "0",
        "uye_kaydi":           "1",
        "misafir_yazabilir":   "0",
        "moderasyon":          "1",
        "spam_korumasi":       "1",
        "captcha":             "1",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO forum_settings VALUES (?,?)", (k, v))
