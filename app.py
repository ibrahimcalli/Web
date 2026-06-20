"""
Portföy Gayrimenkul Web Sistemi - Backend
FastAPI + SQLite | JWT Auth | Belge Parser
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel
import sqlite3, json, os, shutil, uuid, re
from pathlib import Path

# ─── Konfig ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DB_PATH    = BASE_DIR / "emlak_web.db"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY  = "emlak-gizli-anahtar-2026-degistir"
ALGORITHM   = "HS256"
TOKEN_EXPIRE = 60 * 24  # dakika

# ─── Kategori Ağacı (masaüstünden alındı) ─────────────────────────────────────
KATEGORILER = {
    "Konut":           ["Satılık", "Kiralık", "Devren Satılık", "Devren Kiralık"],
    "İş Yeri":         ["Satılık", "Kiralık", "Devren Satılık", "Devren Kiralık"],
    "Arsa":            ["Satılık", "Kiralık"],
    "Konut Projeleri": ["Satılık"],
    "Bina":            ["Satılık", "Kiralık"],
    "Devre Mülk":      ["Satılık", "Kiralık"],
    "Turistik Tesis":  ["Satılık", "Kiralık"],
}

ILAN_TIPLERI = {
    "Konut": {
        "Satılık":        ["Daire", "Rezidans", "Villa", "Yazlık", "Müstakil Ev", "Kooperatif", "Bungalov"],
        "Kiralık":        ["Daire", "Rezidans", "Villa", "Yazlık", "Müstakil Ev"],
        "Devren Satılık": ["Daire", "Rezidans", "Villa", "Müstakil Ev"],
        "Devren Kiralık": ["Daire", "Rezidans", "Villa", "Müstakil Ev"],
    },
    "İş Yeri": {
        "Satılık":        ["Ofis", "Dükkan/Mağaza", "Depo/Antrepo", "Atölye", "Fabrika", "Akaryakıt İstasyonu"],
        "Kiralık":        ["Ofis", "Dükkan/Mağaza", "Depo/Antrepo", "Atölye", "Fabrika"],
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
}

# ─── Form Alan Şablonları ──────────────────────────────────────────────────────
ALAN_SABLONLARI = {
    "konut_satilik": [
        {"key": "net_m2",        "label": "Net m²",          "type": "number"},
        {"key": "brut_m2",       "label": "Brüt m²",         "type": "number"},
        {"key": "oda_sayisi",    "label": "Oda Sayısı",       "type": "select",
         "options": ["1+0","1+1","2+0","2+1","3+1","3+2","4+1","4+2","5+1","5+2","6+"]},
        {"key": "bina_kati",     "label": "Bina Katı",        "type": "number"},
        {"key": "bulundugu_kat", "label": "Bulunduğu Kat",    "type": "number"},
        {"key": "bina_yasi",     "label": "Bina Yaşı",        "type": "number"},
        {"key": "isitma",        "label": "Isıtma",           "type": "select",
         "options": ["Doğalgaz (Kombi)","Doğalgaz (Merkezi)","Klima","Elektrikli","Soba","Yerden Isıtma","Yok"]},
        {"key": "banyo_sayisi",  "label": "Banyo Sayısı",     "type": "number"},
        {"key": "tapu_durumu",   "label": "Tapu Durumu",      "type": "select",
         "options": ["Kat Mülkiyeti","Kat İrtifakı","Arsa Tapusu","Hisseli Tapu"]},
        {"key": "krediye_uygun", "label": "Krediye Uygun",    "type": "select",
         "options": ["Var","Yok"]},
        {"key": "cephe",         "label": "Cephe",            "type": "text"},
        {"key": "esyali",        "label": "Eşyalı",           "type": "select",
         "options": ["Yok","Var","Yarı Eşyalı"]},
        {"key": "balkon",        "label": "Balkon",           "type": "select",
         "options": ["Var","Yok"]},
        {"key": "asansor",       "label": "Asansör",          "type": "select",
         "options": ["Var","Yok"]},
        {"key": "otopark",       "label": "Otopark",          "type": "select",
         "options": ["Var","Yok","Açık","Kapalı"]},
        {"key": "site_icinde",   "label": "Site İçinde",      "type": "select",
         "options": ["Evet","Hayır"]},
        {"key": "kullanim",      "label": "Kullanım Durumu",  "type": "select",
         "options": ["Boş","Kiracılı","Mal Sahibi"]},
        {"key": "takas",         "label": "Takas",            "type": "select",
         "options": ["Var","Yok"]},
        {"key": "ada",           "label": "Ada",              "type": "text"},
        {"key": "parsel",        "label": "Parsel",           "type": "text"},
        {"key": "ozellikler",    "label": "Değer Katan Özellikler", "type": "textarea"},
    ],
    "konut_kiralik": [
        {"key": "net_m2",        "label": "Net m²",           "type": "number"},
        {"key": "brut_m2",       "label": "Brüt m²",          "type": "number"},
        {"key": "oda_sayisi",    "label": "Oda Sayısı",        "type": "select",
         "options": ["1+0","1+1","2+0","2+1","3+1","3+2","4+1","4+2","5+1","5+2","6+"]},
        {"key": "bina_kati",     "label": "Bina Katı",         "type": "number"},
        {"key": "bulundugu_kat", "label": "Bulunduğu Kat",     "type": "number"},
        {"key": "bina_yasi",     "label": "Bina Yaşı",         "type": "number"},
        {"key": "isitma",        "label": "Isıtma",            "type": "select",
         "options": ["Doğalgaz (Kombi)","Doğalgaz (Merkezi)","Klima","Elektrikli","Soba","Yerden Isıtma","Yok"]},
        {"key": "banyo_sayisi",  "label": "Banyo Sayısı",      "type": "number"},
        {"key": "esyali",        "label": "Eşyalı",            "type": "select",
         "options": ["Yok","Var","Yarı Eşyalı"]},
        {"key": "balkon",        "label": "Balkon",            "type": "select",
         "options": ["Var","Yok"]},
        {"key": "asansor",       "label": "Asansör",           "type": "select",
         "options": ["Var","Yok"]},
        {"key": "otopark",       "label": "Otopark",           "type": "select",
         "options": ["Var","Yok"]},
        {"key": "site_icinde",   "label": "Site İçinde",       "type": "select",
         "options": ["Evet","Hayır"]},
        {"key": "depozito",      "label": "Depozito (ay)",     "type": "number"},
        {"key": "aidat",         "label": "Aidat (TL)",        "type": "number"},
        {"key": "ozellikler",    "label": "Değer Katan Özellikler","type": "textarea"},
    ],
    "isyeri_satilik": [
        {"key": "net_m2",        "label": "Net m²",            "type": "number"},
        {"key": "brut_m2",       "label": "Brüt m²",           "type": "number"},
        {"key": "kat",           "label": "Kat",               "type": "number"},
        {"key": "bina_yasi",     "label": "Bina Yaşı",         "type": "number"},
        {"key": "isitma",        "label": "Isıtma",            "type": "select",
         "options": ["Klima","Doğalgaz (Kombi)","Doğalgaz (Merkezi)","Elektrikli","Soba","Yok"]},
        {"key": "tapu_durumu",   "label": "Tapu Durumu",       "type": "select",
         "options": ["Kat Mülkiyeti","Kat İrtifakı","Arsa Tapusu","Hisseli Tapu"]},
        {"key": "krediye_uygun", "label": "Krediye Uygun",     "type": "select",
         "options": ["Var","Yok"]},
        {"key": "kullanim",      "label": "Kullanım Durumu",   "type": "select",
         "options": ["Boş","Kiracılı","Mal Sahibi"]},
        {"key": "takas",         "label": "Takas",             "type": "select",
         "options": ["Var","Yok"]},
        {"key": "cephe",         "label": "Cephe",             "type": "text"},
        {"key": "asansor",       "label": "Asansör",           "type": "select",
         "options": ["Var","Yok"]},
        {"key": "otopark",       "label": "Otopark",           "type": "select",
         "options": ["Var","Yok","Açık","Kapalı"]},
        {"key": "ozellikler",    "label": "Özellikler",        "type": "textarea"},
    ],
    "arsa": [
        {"key": "alan_m2",       "label": "Alan (m²)",         "type": "number"},
        {"key": "ada",           "label": "Ada",               "type": "text"},
        {"key": "parsel",        "label": "Parsel",            "type": "text"},
        {"key": "kaks",          "label": "KAKS/EMSAL",        "type": "text"},
        {"key": "taks",          "label": "TAKS",              "type": "text"},
        {"key": "imar_durumu",   "label": "İmar Durumu",       "type": "select",
         "options": ["Konut İmarlı","Ticari İmarlı","Tarım","Orman","İmarsız","Plansız"]},
        {"key": "tapu_durumu",   "label": "Tapu Durumu",       "type": "select",
         "options": ["Arsa Tapusu","Hisseli Tapu","Tarla Tapusu"]},
        {"key": "takas",         "label": "Takas",             "type": "select",
         "options": ["Var","Yok"]},
        {"key": "ozellikler",    "label": "Özellikler",        "type": "textarea"},
    ],
    "turistik": [
        {"key": "net_m2",        "label": "Net m²",            "type": "number"},
        {"key": "oda_sayisi",    "label": "Oda/Suit Sayısı",   "type": "number"},
        {"key": "yatak_kapasitesi","label":"Yatak Kapasitesi", "type": "number"},
        {"key": "yildiz",        "label": "Yıldız",            "type": "select",
         "options": ["1","2","3","4","5","Butik","Belspaş","Pansiyon"]},
        {"key": "havuz",         "label": "Havuz",             "type": "select",
         "options": ["Var","Yok","Kapalı","Açık"]},
        {"key": "plaj",          "label": "Plaj/Deniz",        "type": "select",
         "options": ["Denize Sıfır","Yakın","Uzak"]},
        {"key": "tapu_durumu",   "label": "Tapu Durumu",       "type": "select",
         "options": ["Kat Mülkiyeti","Arsa Tapusu","Hisseli Tapu"]},
        {"key": "ozellikler",    "label": "Özellikler",        "type": "textarea"},
    ],
    "genel": [
        {"key": "net_m2",        "label": "Net m²",            "type": "number"},
        {"key": "brut_m2",       "label": "Brüt m²",           "type": "number"},
        {"key": "tapu_durumu",   "label": "Tapu Durumu",       "type": "select",
         "options": ["Kat Mülkiyeti","Arsa Tapusu","Hisseli Tapu"]},
        {"key": "ozellikler",    "label": "Özellikler",        "type": "textarea"},
    ],
}

def alan_sablonu_sec(ana_kat: str, alt_kat: str, ilan_tipi: str = "") -> list:
    """Kategori + alt kategoriye göre uygun alan şablonu seç."""
    kiralik = alt_kat in ("Kiralık", "Devren Kiralık")
    if "Arsa" in ana_kat:
        return ALAN_SABLONLARI["arsa"]
    elif "Turistik" in ana_kat:
        return ALAN_SABLONLARI["turistik"]
    elif "İş" in ana_kat or "Ticari" in ana_kat:
        return ALAN_SABLONLARI["isyeri_satilik"]
    elif "Konut" in ana_kat:
        return ALAN_SABLONLARI["konut_kiralik"] if kiralik else ALAN_SABLONLARI["konut_satilik"]
    return ALAN_SABLONLARI["genel"]

# ─── Auth ──────────────────────────────────────────────────────────────────────
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2  = OAuth2PasswordBearer(tokenUrl="/api/auth/giris", auto_error=False)

def hash_sifre(sifre): return pwd_ctx.hash(sifre)
def sifre_dogrula(plain, hashed): return pwd_ctx.verify(plain, hashed)

def token_olustur(data: dict, dakika: int = TOKEN_EXPIRE):
    exp = datetime.utcnow() + timedelta(minutes=dakika)
    return jwt.encode({**data, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

def token_coz(token: str = Depends(oauth2)):
    if not token:
        return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def admin_gerek(payload=Depends(token_coz)):
    if not payload or payload.get("rol") != "admin":
        raise HTTPException(status_code=401, detail="Yetkisiz erişim")
    return payload

def kullanici_gerek(payload=Depends(token_coz)):
    if not payload:
        raise HTTPException(status_code=401, detail="Giriş yapmanız gerekiyor")
    return payload

# ─── Veritabanı ────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS kullanicilar (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        ad_soyad  TEXT NOT NULL,
        email     TEXT UNIQUE NOT NULL,
        sifre     TEXT NOT NULL,
        rol       TEXT DEFAULT 'kullanici',
        aktif     INTEGER DEFAULT 1,
        olusturma TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS portfoyler (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        baslik       TEXT NOT NULL,
        ana_kategori TEXT NOT NULL,
        alt_kategori TEXT NOT NULL,
        ilan_tipi    TEXT,
        il           TEXT DEFAULT 'Muğla',
        ilce         TEXT DEFAULT 'Fethiye',
        mahalle      TEXT,
        fiyat        TEXT,
        para_birimi  TEXT DEFAULT 'TL',
        aciklama     TEXT,
        saha_notu    TEXT,
        gps          TEXT,
        durum        TEXT DEFAULT 'Taslak',
        alanlar      TEXT DEFAULT '{}',
        resimler     TEXT DEFAULT '[]',
        musteri_ad   TEXT,
        musteri_tel  TEXT,
        musteri_mail TEXT,
        kaynak       TEXT DEFAULT 'web',
        olusturma    TEXT DEFAULT (datetime('now')),
        guncelleme   TEXT DEFAULT (datetime('now'))
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
    """)

    # Varsayılan admin
    row = c.execute("SELECT id FROM kullanicilar WHERE email='bilgi@portfoygayrimenkul.com.tr'").fetchone()
    if not row:
        c.execute("""INSERT INTO kullanicilar (ad_soyad,email,sifre,rol)
                     VALUES (?,?,?,?)""",
                  ("Portföy Gayrimenkul", "bilgi@portfoygayrimenkul.com.tr",
                   hash_sifre("admin123"), "admin"))

    # Varsayılan site ayarları
    defaults = {
        "site_adi":    "Portföy Gayrimenkul",
        "site_slogan": "Fethiye'nin Güvenilir Gayrimenkul Danışmanı",
        "telefon":     "0542 966 36 36",
        "email":       "bilgi@portfoygayrimenkul.com.tr",
        "adres":       "Fethiye / Muğla",
        "web_sitesi":  "portfoygayrimenkul.com.tr",
        "renk_tema":   "",
        "logo_url":    "",
        "sosyal_ig":   "",
        "sosyal_fb":   "",
        "sosyal_wa":   "",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO site_ayarlari VALUES (?,?)", (k, v))

    conn.commit()
    conn.close()

# ─── Belge Parser ──────────────────────────────────────────────────────────────
def docx_parse(dosya_yolu: str) -> dict:
    """docx dosyasından portföy alanlarını çıkar."""
    try:
        from docx import Document
        doc = Document(dosya_yolu)
        tablo_verisi = {}
        metin_bloklari = []

        # Tabloları oku
        for tablo in doc.tables:
            for satir in tablo.rows:
                cells = [c.text.strip() for c in satir.cells]
                if len(cells) >= 2 and cells[0] and cells[1]:
                    tablo_verisi[cells[0].strip(":")] = cells[1]

        # Paragrafları oku
        for para in doc.paragraphs:
            metin = para.text.strip()
            if metin:
                metin_bloklari.append(metin)

        return _tablo_to_portfoy(tablo_verisi, metin_bloklari)
    except Exception as e:
        return {"hata": str(e)}

def html_parse(icerik: str) -> dict:
    """HTML içeriğinden portföy alanlarını çıkar."""
    from html.parser import HTMLParser
    import html as html_module

    tablo_verisi = {}
    metin_bloklari = []

    # Tablo hücrelerini yakala
    td_pattern = re.findall(r'<td[^>]*>(.*?)</td>', icerik, re.DOTALL | re.IGNORECASE)
    temiz = [re.sub(r'<[^>]+>', '', h).strip() for h in td_pattern]
    temiz = [html_module.unescape(t) for t in temiz if t]

    for i in range(0, len(temiz) - 1, 2):
        if temiz[i] and temiz[i+1]:
            tablo_verisi[temiz[i].strip(":")] = temiz[i+1]

    # h2 başlıklar (bölüm bilgisi)
    for m in re.finditer(r'<h[1-3][^>]*>(.*?)</h[1-3]>', icerik, re.DOTALL | re.IGNORECASE):
        t = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        if t:
            metin_bloklari.append(t)

    return _tablo_to_portfoy(tablo_verisi, metin_bloklari)

def _tablo_to_portfoy(tablo: dict, metinler: list) -> dict:
    """Tablo verisi + metin → portföy dict."""
    def bul(*anahtarlar):
        for a in anahtarlar:
            for k, v in tablo.items():
                if a.lower() in k.lower():
                    return v.strip()
        return ""

    # Başlık: ilk metin satırı genellikle işletme adı + ilan tipi
    baslik = ""
    for m in metinler:
        if len(m) > 5 and not m.startswith("IC "):
            baslik = m
            break

    # Kategori tespiti
    kat_str  = bul("Kategori", "Kategori")
    alt_str  = bul("Ilan Tipi", "İlan Tipi", "Alt Kategori")
    durum_str = bul("Durum", "Statü")

    # Kategori → ana_kat / alt_kat çıkar
    ana_kat, alt_kat, ilan_tipi = "Konut", "Satılık", ""
    for k in KATEGORILER:
        if k.lower() in kat_str.lower():
            ana_kat = k
            break
    for a in KATEGORILER.get(ana_kat, []):
        if a.lower() in kat_str.lower() or a.lower() in alt_str.lower():
            alt_kat = a
            break

    # Fiyat: ilk büyük sayıyı yakala
    fiyat = ""
    for m in metinler:
        match = re.search(r'[\d.,]+\s*(TL|EUR|USD|\$|€)?', m)
        if match and any(c.isdigit() for c in match.group()):
            sayi = re.sub(r'[.,\s]', '', match.group())
            if len(sayi) >= 4:
                fiyat = match.group().strip()
                break

    # GPS
    gps = bul("GPS", "Konum", "google")
    gps_match = re.search(r'q=([\d.]+),([\d.]+)', gps)
    if gps_match:
        gps = f"{gps_match.group(1)},{gps_match.group(2)}"

    # Açıklama + saha notu
    aciklama = ""
    saha_notu = ""
    yakalanmis = False
    for m in metinler:
        if "açıklama" in m.lower() or "ACIKLAMA" in m:
            yakalanmis = True
            continue
        if "saha" in m.lower() or "SAHA" in m:
            yakalanmis = False
            saha_notu = m
            continue
        if yakalanmis and not aciklama:
            aciklama = m

    # Dinamik alanlar
    alanlar = {}
    alan_map = {
        "net_m2":        ["Net M2", "Net m2", "Net M²"],
        "brut_m2":       ["Brut M2", "Brüt m2", "Brüt M²"],
        "oda_sayisi":    ["Oda Sayisi", "Oda Sayısı"],
        "bina_kati":     ["Bina Kati", "Bina Katı"],
        "bulundugu_kat": ["Kat", "Bulunduğu Kat"],
        "bina_yasi":     ["Bina Yasi", "Bina Yaşı"],
        "banyo_sayisi":  ["Banyo Sayisi", "Banyo Sayısı"],
        "isitma":        ["Isitma", "Isıtma"],
        "tapu_durumu":   ["Tapu Durumu"],
        "cephe":         ["Cephe"],
        "esyali":        ["Esyali", "Eşyalı"],
        "balkon":        ["Balkon"],
        "asansor":       ["Asansor", "Asansör"],
        "otopark":       ["Otopark"],
        "site_icinde":   ["Site Icinde", "Site İçinde"],
        "kullanim":      ["Kullanim", "Kullanım"],
        "takas":         ["Takas"],
        "ada":           ["Ada"],
        "parsel":        ["Parsel"],
        "krediye_uygun": ["Krediye Uygun"],
        "kimden":        ["Kimden"],
        "ozellikler":    ["Deger Katan", "Değer Katan", "Özellikler"],
    }
    for hedef, kaynaklar in alan_map.items():
        deger = bul(*kaynaklar)
        if deger:
            alanlar[hedef] = deger

    musteri_ad   = bul("Ad Soyad", "Sahip", "Müşteri")
    musteri_tel  = bul("Telefon", "Tel")
    musteri_mail = bul("E-posta", "Mail", "Email")
    il_ilce      = bul("Il / Ilce", "İl / İlçe", "İl/İlçe")
    il, ilce     = "Muğla", "Fethiye"
    if "/" in il_ilce:
        parcalar = [p.strip() for p in il_ilce.split("/")]
        il  = parcalar[0] if parcalar[0] else il
        ilce = parcalar[1] if len(parcalar) > 1 and parcalar[1] else ilce
    mahalle = bul("Mahalle", "Bölge", "Semt")

    return {
        "baslik":       baslik,
        "ana_kategori": ana_kat,
        "alt_kategori": alt_kat,
        "ilan_tipi":    ilan_tipi,
        "fiyat":        fiyat,
        "il":           il,
        "ilce":         ilce,
        "mahalle":      mahalle,
        "gps":          gps,
        "aciklama":     aciklama,
        "saha_notu":    saha_notu,
        "musteri_ad":   musteri_ad,
        "musteri_tel":  musteri_tel,
        "musteri_mail": musteri_mail,
        "alanlar":      alanlar,
        "kaynak":       "belge_import",
    }

# ─── Pydantic Modeller ─────────────────────────────────────────────────────────
class PortfoyGiren(BaseModel):
    baslik:       str
    ana_kategori: str
    alt_kategori: str
    ilan_tipi:    Optional[str] = ""
    il:           Optional[str] = "Muğla"
    ilce:         Optional[str] = "Fethiye"
    mahalle:      Optional[str] = ""
    fiyat:        Optional[str] = ""
    para_birimi:  Optional[str] = "TL"
    aciklama:     Optional[str] = ""
    saha_notu:    Optional[str] = ""
    gps:          Optional[str] = ""
    durum:        Optional[str] = "Taslak"
    alanlar:      Optional[dict] = {}
    musteri_ad:   Optional[str] = ""
    musteri_tel:  Optional[str] = ""
    musteri_mail: Optional[str] = ""

class IstekGiren(BaseModel):
    ad_soyad:   str
    telefon:    Optional[str] = ""
    email:      Optional[str] = ""
    mesaj:      Optional[str] = ""
    portfoy_id: Optional[int] = None

class KullaniciGiren(BaseModel):
    ad_soyad: str
    email:    str
    sifre:    str
    rol:      Optional[str] = "kullanici"

class AyarGiren(BaseModel):
    ayarlar: dict

# ─── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(title="Portföy Gayrimenkul API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ─── Auth Endpoint'leri ────────────────────────────────────────────────────────
@app.post("/api/auth/giris")
def giris(form: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    kullanici = conn.execute(
        "SELECT * FROM kullanicilar WHERE email=? AND aktif=1",
        (form.username,)
    ).fetchone()
    conn.close()
    if not kullanici or not sifre_dogrula(form.password, kullanici["sifre"]):
        raise HTTPException(status_code=400, detail="Email veya şifre hatalı")
    token = token_olustur({"sub": kullanici["email"],
                            "rol": kullanici["rol"],
                            "ad":  kullanici["ad_soyad"]})
    return {"access_token": token, "token_type": "bearer",
            "rol": kullanici["rol"], "ad": kullanici["ad_soyad"]}

@app.get("/api/auth/ben")
def ben(payload=Depends(token_coz)):
    if not payload:
        return {"giris": False}
    conn = get_db()
    k = conn.execute("SELECT id,ad_soyad,email,rol FROM kullanicilar WHERE email=?",
                     (payload["sub"],)).fetchone()
    conn.close()
    if not k:
        return {"giris": False}
    return {"giris": True, **dict(k)}

# ─── Portföy Endpoint'leri ─────────────────────────────────────────────────────
@app.get("/api/portfoyler")
def portfoy_listele(
    kategori: str = "",
    alt_kat:  str = "",
    durum:    str = "Aktif",
    arama:    str = "",
    payload   = Depends(token_coz)
):
    conn = get_db()
    q    = "SELECT * FROM portfoyler WHERE 1=1"
    args = []

    # Admin değilse sadece Aktif ilanlar
    is_admin = payload and payload.get("rol") == "admin"
    if not is_admin:
        q += " AND durum='Aktif'"
    elif durum:
        q += " AND durum=?"
        args.append(durum)

    if kategori:
        q += " AND ana_kategori=?"; args.append(kategori)
    if alt_kat:
        q += " AND alt_kategori=?"; args.append(alt_kat)
    if arama:
        q += " AND (baslik LIKE ? OR mahalle LIKE ? OR ilce LIKE ?)"
        args += [f"%{arama}%"] * 3

    q += " ORDER BY guncelleme DESC"
    rows = conn.execute(q, args).fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["alanlar"]  = json.loads(d.get("alanlar") or "{}")
        d["resimler"] = json.loads(d.get("resimler") or "[]")
        result.append(d)
    return result

@app.get("/api/portfoyler/{pid}")
def portfoy_detay(pid: int, payload=Depends(token_coz)):
    conn = get_db()
    row = conn.execute("SELECT * FROM portfoyler WHERE id=?", (pid,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Portföy bulunamadı")
    is_admin = payload and payload.get("rol") == "admin"
    if not is_admin and row["durum"] != "Aktif":
        raise HTTPException(403, "Bu portföy henüz yayında değil")
    d = dict(row)
    d["alanlar"]  = json.loads(d.get("alanlar") or "{}")
    d["resimler"] = json.loads(d.get("resimler") or "[]")
    return d

@app.post("/api/portfoyler")
def portfoy_ekle(p: PortfoyGiren, payload=Depends(admin_gerek)):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO portfoyler
        (baslik,ana_kategori,alt_kategori,ilan_tipi,il,ilce,mahalle,
         fiyat,para_birimi,aciklama,saha_notu,gps,durum,alanlar,
         musteri_ad,musteri_tel,musteri_mail,kaynak)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'web')
    """, (p.baslik, p.ana_kategori, p.alt_kategori, p.ilan_tipi,
          p.il, p.ilce, p.mahalle, p.fiyat, p.para_birimi,
          p.aciklama, p.saha_notu, p.gps, p.durum,
          json.dumps(p.alanlar, ensure_ascii=False),
          p.musteri_ad, p.musteri_tel, p.musteri_mail))
    pid = c.lastrowid
    conn.commit(); conn.close()
    return {"id": pid, "mesaj": "Portföy oluşturuldu"}

@app.put("/api/portfoyler/{pid}")
def portfoy_guncelle(pid: int, p: PortfoyGiren, payload=Depends(admin_gerek)):
    conn = get_db()
    conn.execute("""
        UPDATE portfoyler SET
        baslik=?,ana_kategori=?,alt_kategori=?,ilan_tipi=?,
        il=?,ilce=?,mahalle=?,fiyat=?,para_birimi=?,
        aciklama=?,saha_notu=?,gps=?,durum=?,alanlar=?,
        musteri_ad=?,musteri_tel=?,musteri_mail=?,
        guncelleme=datetime('now')
        WHERE id=?
    """, (p.baslik, p.ana_kategori, p.alt_kategori, p.ilan_tipi,
          p.il, p.ilce, p.mahalle, p.fiyat, p.para_birimi,
          p.aciklama, p.saha_notu, p.gps, p.durum,
          json.dumps(p.alanlar, ensure_ascii=False),
          p.musteri_ad, p.musteri_tel, p.musteri_mail, pid))
    conn.commit(); conn.close()
    return {"mesaj": "Portföy güncellendi"}

@app.patch("/api/portfoyler/{pid}/durum")
def portfoy_durum(pid: int, durum: str, payload=Depends(admin_gerek)):
    if durum not in ("Aktif", "Taslak", "Pasif", "Satıldı", "Kiralandı"):
        raise HTTPException(400, "Geçersiz durum")
    conn = get_db()
    conn.execute("UPDATE portfoyler SET durum=?,guncelleme=datetime('now') WHERE id=?",
                 (durum, pid))
    conn.commit(); conn.close()
    return {"mesaj": f"Durum → {durum}"}

@app.delete("/api/portfoyler/{pid}")
def portfoy_sil(pid: int, payload=Depends(admin_gerek)):
    conn = get_db()
    conn.execute("DELETE FROM portfoyler WHERE id=?", (pid,))
    conn.commit(); conn.close()
    return {"mesaj": "Portföy silindi"}

# ─── Resim Yükleme ─────────────────────────────────────────────────────────────
@app.post("/api/portfoyler/{pid}/resim")
async def resim_yukle(pid: int, dosya: UploadFile = File(...),
                      payload=Depends(admin_gerek)):
    uzanti = Path(dosya.filename).suffix.lower()
    if uzanti not in (".jpg", ".jpeg", ".png", ".webp"):
        raise HTTPException(400, "Sadece jpg/png/webp kabul edilir")

    ad = f"{pid}_{uuid.uuid4().hex[:8]}{uzanti}"
    hedef = UPLOAD_DIR / ad
    with open(hedef, "wb") as f:
        shutil.copyfileobj(dosya.file, f)

    # Portföy resimler listesine ekle
    conn = get_db()
    row = conn.execute("SELECT resimler FROM portfoyler WHERE id=?", (pid,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Portföy bulunamadı")
    resimler = json.loads(row["resimler"] or "[]")
    url = f"/static/uploads/{ad}"
    resimler.append(url)
    conn.execute("UPDATE portfoyler SET resimler=? WHERE id=?",
                 (json.dumps(resimler), pid))
    conn.commit(); conn.close()
    return {"url": url, "resimler": resimler}

@app.delete("/api/portfoyler/{pid}/resim")
def resim_sil(pid: int, url: str, payload=Depends(admin_gerek)):
    conn = get_db()
    row = conn.execute("SELECT resimler FROM portfoyler WHERE id=?", (pid,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404)
    resimler = json.loads(row["resimler"] or "[]")
    resimler = [r for r in resimler if r != url]
    conn.execute("UPDATE portfoyler SET resimler=? WHERE id=?",
                 (json.dumps(resimler), pid))
    conn.commit(); conn.close()
    # Dosyayı da sil
    dosya = BASE_DIR / url.lstrip("/")
    if dosya.exists():
        dosya.unlink()
    return {"resimler": resimler}

# ─── Belge Parser Endpoint'i ────────────────────────────────────────────────────
@app.post("/api/belge/parse")
async def belge_parse(dosya: UploadFile = File(...), payload=Depends(admin_gerek)):
    gecici = BASE_DIR / "static" / "uploads" / f"tmp_{uuid.uuid4().hex}"
    uzanti = Path(dosya.filename).suffix.lower()

    with open(str(gecici) + uzanti, "wb") as f:
        shutil.copyfileobj(dosya.file, f)

    try:
        if uzanti == ".docx":
            sonuc = docx_parse(str(gecici) + uzanti)
        elif uzanti in (".html", ".htm"):
            icerik = open(str(gecici) + uzanti, encoding="utf-8", errors="ignore").read()
            sonuc = html_parse(icerik)
        else:
            raise HTTPException(400, "Sadece .docx veya .html destekleniyor")
    finally:
        try:
            Path(str(gecici) + uzanti).unlink()
        except:
            pass

    # İlgili alan şablonunu da döndür
    alan_list = alan_sablonu_sec(
        sonuc.get("ana_kategori", "Konut"),
        sonuc.get("alt_kategori", "Satılık"),
        sonuc.get("ilan_tipi", "")
    )
    return {"portfoy": sonuc, "alan_sablonu": alan_list}

# ─── Kategori Endpoint'i ───────────────────────────────────────────────────────
@app.get("/api/kategoriler")
def kategoriler():
    return {
        "kategoriler": KATEGORILER,
        "ilan_tipleri": ILAN_TIPLERI
    }

@app.get("/api/alanlar")
def alan_sec(ana_kat: str, alt_kat: str, ilan_tipi: str = ""):
    return alan_sablonu_sec(ana_kat, alt_kat, ilan_tipi)

# ─── Ziyaretçi İstek Formu ────────────────────────────────────────────────────
@app.post("/api/istekler")
def istek_gonder(istek: IstekGiren):
    conn = get_db()
    conn.execute("""INSERT INTO kullanici_istekleri
                    (ad_soyad,telefon,email,mesaj,portfoy_id)
                    VALUES (?,?,?,?,?)""",
                 (istek.ad_soyad, istek.telefon, istek.email,
                  istek.mesaj, istek.portfoy_id))
    conn.commit(); conn.close()
    return {"mesaj": "İsteğiniz alındı, en kısa sürede dönüş yapılacak."}

@app.get("/api/istekler")
def istek_listele(payload=Depends(admin_gerek)):
    conn = get_db()
    rows = conn.execute("""
        SELECT i.*, p.baslik as portfoy_baslik
        FROM kullanici_istekleri i
        LEFT JOIN portfoyler p ON i.portfoy_id=p.id
        ORDER BY i.olusturma DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.patch("/api/istekler/{iid}/durum")
def istek_durum(iid: int, durum: str, payload=Depends(admin_gerek)):
    conn = get_db()
    conn.execute("UPDATE kullanici_istekleri SET durum=? WHERE id=?", (durum, iid))
    conn.commit(); conn.close()
    return {"mesaj": "Güncellendi"}

# ─── Kullanıcı Yönetimi ────────────────────────────────────────────────────────
@app.get("/api/kullanicilar")
def kullanici_listele(payload=Depends(admin_gerek)):
    conn = get_db()
    rows = conn.execute(
        "SELECT id,ad_soyad,email,rol,aktif,olusturma FROM kullanicilar ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/api/kullanicilar")
def kullanici_ekle(k: KullaniciGiren, payload=Depends(admin_gerek)):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO kullanicilar (ad_soyad,email,sifre,rol) VALUES (?,?,?,?)",
            (k.ad_soyad, k.email, hash_sifre(k.sifre), k.rol)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Bu email zaten kayıtlı")
    finally:
        conn.close()
    return {"mesaj": "Kullanıcı oluşturuldu"}

@app.delete("/api/kullanicilar/{kid}")
def kullanici_sil(kid: int, payload=Depends(admin_gerek)):
    if kid == 1:
        raise HTTPException(400, "Varsayılan admin silinemez")
    conn = get_db()
    conn.execute("DELETE FROM kullanicilar WHERE id=?", (kid,))
    conn.commit(); conn.close()
    return {"mesaj": "Kullanıcı silindi"}


# ─── Logo Yükleme ──────────────────────────────────────────────────────────────
@app.post("/api/logo/yukle")
async def logo_yukle(dosya: UploadFile = File(...), payload=Depends(admin_gerek)):
    uzanti = Path(dosya.filename).suffix.lower()
    if uzanti not in (".jpg", ".jpeg", ".png", ".webp", ".svg"):
        raise HTTPException(400, "Desteklenen formatlar: jpg, png, webp, svg")
    # Eski logoyu sil
    conn = get_db()
    eski = conn.execute("SELECT deger FROM site_ayarlari WHERE anahtar='logo_url'").fetchone()
    if eski and eski["deger"]:
        eski_dosya = BASE_DIR / eski["deger"].lstrip("/")
        if eski_dosya.exists():
            eski_dosya.unlink()
    conn.close()
    # Yeni logo kaydet
    ad = f"logo{uzanti}"
    hedef = BASE_DIR / "static" / "img" / ad
    hedef.parent.mkdir(parents=True, exist_ok=True)
    with open(hedef, "wb") as f:
        shutil.copyfileobj(dosya.file, f)
    url = f"/static/img/{ad}"
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO site_ayarlari VALUES ('logo_url',?)", (url,))
    conn.commit(); conn.close()
    return {"url": url, "mesaj": "Logo yüklendi"}

@app.delete("/api/logo")
def logo_sil(payload=Depends(admin_gerek)):
    conn = get_db()
    row = conn.execute("SELECT deger FROM site_ayarlari WHERE anahtar='logo_url'").fetchone()
    if row and row["deger"]:
        dosya = BASE_DIR / row["deger"].lstrip("/")
        if dosya.exists():
            dosya.unlink()
    conn.execute("INSERT OR REPLACE INTO site_ayarlari VALUES ('logo_url','')")
    conn.commit(); conn.close()
    return {"mesaj": "Logo silindi"}

# ─── Site Ayarları ─────────────────────────────────────────────────────────────
@app.get("/api/ayarlar")
def ayar_getir():
    conn = get_db()
    rows = conn.execute("SELECT * FROM site_ayarlari").fetchall()
    conn.close()
    return {r["anahtar"]: r["deger"] for r in rows}

@app.put("/api/ayarlar")
def ayar_kaydet(data: AyarGiren, payload=Depends(admin_gerek)):
    conn = get_db()
    for k, v in data.ayarlar.items():
        conn.execute("INSERT OR REPLACE INTO site_ayarlari VALUES (?,?)", (k, str(v)))
    conn.commit(); conn.close()
    return {"mesaj": "Ayarlar kaydedildi"}

# ─── İstatistik ────────────────────────────────────────────────────────────────
@app.get("/api/istatistik")
def istatistik(payload=Depends(token_coz)):
    conn = get_db()
    aktif = conn.execute("SELECT COUNT(*) FROM portfoyler WHERE durum='Aktif'").fetchone()[0]
    kat_dag = conn.execute("""
        SELECT ana_kategori, COUNT(*) as sayi
        FROM portfoyler WHERE durum='Aktif'
        GROUP BY ana_kategori
    """).fetchall()
    sonuc = {
        "toplam": aktif,
        "aktif":  aktif,
        "taslak": 0,
        "yeni_istekler": 0,
        "kategori_dagilimi": [dict(r) for r in kat_dag],
    }
    # Admin ise ek bilgiler
    if payload and payload.get("rol") == "admin":
        toplam   = conn.execute("SELECT COUNT(*) FROM portfoyler").fetchone()[0]
        taslak   = conn.execute("SELECT COUNT(*) FROM portfoyler WHERE durum='Taslak'").fetchone()[0]
        istekler = conn.execute("SELECT COUNT(*) FROM kullanici_istekleri WHERE durum='Yeni'").fetchone()[0]
        sonuc.update({"toplam": toplam, "taslak": taslak, "yeni_istekler": istekler})
    conn.close()
    return sonuc

# ─── Static Files + SPA fallback ──────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    index = BASE_DIR / "static" / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"mesaj": "API çalışıyor"}, status_code=200)

# ─── Başlat ────────────────────────────────────────────────────────────────────
init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
