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

    conn.commit()
    conn.close()
