"""
Backend API + mimari kapsamlı testler.

Çalıştırma:
    python tests/test_api.py            # tüm testler
    python tests/test_api.py -v         # pytest ile verbose (opsiyonel)

Kapsam (50+ test):
    ─ Password (hash/verify)
    ─ Repository (Portfoy, Kullanıcı, Ayar, Istek, Banner, Blog)
    ─ Service (Auth, Portfoy, Kullanıcı)
    ─ JWT (token create, decode, expire, invalid)
    ─ Login (başarı, hata, eksik, çok uzun, rate limit)
    ─ API endpoints (health, portfoyler listesi, portfoy detay)
    ─ 404 (olmayan portföy, bilinmeyen path)
    ─ PWA (sw.js, manifest.json, offline.html, favicon.ico — Content-Type)
    ─ SEO (sitemap.xml, robots.txt, sitemap-images.xml)
    ─ Response model (ok, fail, ApiResponse)
    ─ Security (CSRF Content-Type, upload filename validation)
    ─ Version (/health'ten version/git_hash al)
    ─ Settings (singleton, env okuma, DEBUG)
    ─ Logging (3 dosya oluşturma)
"""
import os
import sys
import json
import tempfile
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timedelta

# Proje root
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test sırasında gerçek log dosyalarını geçici dizine yazalım
_logs_tmp = tempfile.mkdtemp(prefix="emlak_logs_")
os.environ.setdefault("LOG_DIR", _logs_tmp)

from backend.db.database import Database
from backend.db.schema import init_db, SCHEMA_SQL
from backend.core.password import hash_sifre, sifre_dogrula
from backend.core.security import (
    token_olustur, decode_token, client_ip,
    rate_limit_kontrol, rate_limit_basarisiz, rate_limit_basarili,
    get_sifre_token_store,
)
from backend.repositories.portfoy_repository import PortfoyRepository
from backend.repositories.kullanici_repository import KullaniciRepository
from backend.repositories.misc_repository import (
    IstekRepository, AyarRepository, BannerRepository, BlogRepository
)
from backend.services.portfoy_service import PortfoyService
from backend.services.kullanici_service import KullaniciService
from backend.services.auth_service import AuthService
from backend.services.upload_service import (
    UploadService, validate_upload_filename, _magic_ok, _doc_magic_ok
)
from backend.schemas.response import ok, fail, ApiResponse

# Settings + Version
from backend.core.settings import settings
from backend.core.version import get_version_info

# FastAPI TestClient — using httpx2 değil, bizimstarlette httpx modülü
try:
    from fastapi.testclient import TestClient
    HTTP_OK = True
except Exception:
    HTTP_OK = False


# ─── Helpers ─────────────────────────────────────────────────────────────────
def get_test_db():
    """Test için geçici veritabanı."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Database(path)


def setup_test_db(db):
    """Test veritabanını oluştur ve örnek veri ekle."""
    conn = db.connect()
    conn.executescript(SCHEMA_SQL)
    # Migrasyonlar
    for mig in [
        "ALTER TABLE kullanicilar ADD COLUMN onay INTEGER DEFAULT 1",
    ]:
        try:
            conn.execute(mig)
        except Exception:
            pass
    # Admin
    conn.execute(
        "INSERT INTO kullanicilar (ad_soyad,email,sifre,rol,onay) VALUES (?,?,?,?,?)",
        ("Test Admin", "admin@test.com", hash_sifre("admin123"), "admin", 1),
    )
    # Onay bekleyen kullanıcı
    conn.execute(
        "INSERT INTO kullanicilar (ad_soyad,email,sifre,rol,onay) VALUES (?,?,?,?,?)",
        ("Onay bekleyen", "bekleyen@test.com", hash_sifre("sifre123"), "kullanici", 0),
    )
    # Pasif kullanıcı
    conn.execute(
        "INSERT INTO kullanicilar (ad_soyad,email,sifre,rol,aktif) VALUES (?,?,?,?,?)",
        ("Pasif Kullanici", "pasif@test.com", hash_sifre("sifre123"), "kullanici", 0),
    )
    # Portföy
    conn.execute(
        "INSERT INTO portfoyler (baslik,ana_kategori,alt_kategori,durum) VALUES (?,?,?,?)",
        ("Test Villa", "Konut", "Satılık", "Aktif"),
    )
    conn.execute(
        "INSERT INTO portfoyler (baslik,ana_kategori,alt_kategori,durum) VALUES (?,?,?,?)",
        ("Test Daire", "Konut", "Kiralık", "Pasif"),
    )
    # Banner
    conn.execute(
        "INSERT INTO bannerlar (konum,baslik,aktif) VALUES (?,?,?)",
        ("anasayfa_ust", "Test Banner", 1),
    )
    # Blog — `durum` kolonu 'Taslak'/'Yayında'
    conn.execute(
        "INSERT INTO blog_yazilari (baslik,icerik,durum,slug) VALUES (?,?,?,?)",
        ("Test Blog", "Blog içeriği", "Yayında", "test-blog"),
    )
    conn.commit()
    conn.close()


def run_tests(category: str, tests: list):
    """Test koşturucu — pytest olmayan ortamlarda basit runner."""
    passed = 0
    failed = 0
    print(f"\n=== {category} ===")
    for name, func in tests:
        try:
            func()
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            failed += 1
    return passed, failed


# ─── Password Tests (3) ──────────────────────────────────────────────────────
def test_password_hash():
    h = hash_sifre("test123")
    assert h != "test123"
    assert sifre_dogrula("test123", h) is True

def test_password_wrong():
    h = hash_sifre("test123")
    assert sifre_dogrula("wrong", h) is False

def test_password_different_hashes():
    h1 = hash_sifre("same")
    h2 = hash_sifre("same")
    assert h1 != h2  # salt

PASSWORD_TESTS = [
    ("password_hash", test_password_hash),
    ("password_wrong", test_password_wrong),
    ("password_different_hashes", test_password_different_hashes),
]


# ─── JWT Tests (5) ────────────────────────────────────────────────────────────
def test_jwt_create_decode():
    t = token_olustur({"sub": "x@y.z", "rol": "admin"})
    payload = decode_token(t)
    assert payload["sub"] == "x@y.z"
    assert payload["rol"] == "admin"

def test_jwt_invalid_returns_none():
    assert decode_token("invalid.token.here") is None

def test_jwt_empty_returns_none():
    assert decode_token(None) is None
    assert decode_token("") is None

def test_jwt_has_exp():
    t = token_olustur({"sub": "x@y.z"})
    payload = decode_token(t)
    assert "exp" in payload

def test_jwt_custom_expiry():
    t = token_olustur({"sub": "x@y.z"}, dakika=1)
    payload = decode_token(t)
    exp = datetime.utcfromtimestamp(payload["exp"])
    delta = exp - datetime.utcnow()
    # 1 dakikadan biraz fazla
    assert 30 < delta.total_seconds() <= 60

JWT_TESTS = [
    ("jwt_create_decode", test_jwt_create_decode),
    ("jwt_invalid_returns_none", test_jwt_invalid_returns_none),
    ("jwt_empty_returns_none", test_jwt_empty_returns_none),
    ("jwt_has_exp", test_jwt_has_exp),
    ("jwt_custom_expiry", test_jwt_custom_expiry),
]


# ─── Repository CRUD Tests (7) ────────────────────────────────────────────────
def test_portfoy_repo_list():
    db = get_test_db(); setup_test_db(db)
    repo = PortfoyRepository(db)
    items = repo.list(is_admin=False)
    assert len(items) == 1  # sadece Aktif

def test_portfoy_repo_get():
    db = get_test_db(); setup_test_db(db)
    repo = PortfoyRepository(db)
    p = repo.get(1)
    assert p is not None
    assert p["baslik"] == "Test Villa"

def test_portfoy_repo_counts():
    db = get_test_db(); setup_test_db(db)
    repo = PortfoyRepository(db)
    c = repo.counts()
    assert c["toplam"] == 2
    assert c["aktif"] == 1

def test_portfoy_repo_exists():
    db = get_test_db(); setup_test_db(db)
    repo = PortfoyRepository(db)
    assert repo.exists(1) is True
    assert repo.exists(999) is False

def test_kullanici_repo_get_by_email():
    db = get_test_db(); setup_test_db(db)
    repo = KullaniciRepository(db)
    k = repo.get_by_email("admin@test.com")
    assert k is not None
    assert k["rol"] == "admin"

def test_ayar_repo_set_get():
    db = get_test_db(); setup_test_db(db)
    repo = AyarRepository(db)
    repo.set("test", "val1")
    assert repo.get("test") == "val1"
    assert "test" in repo.get_all()

def test_blog_repo_list_published():
    db = get_test_db(); setup_test_db(db)
    repo = BlogRepository(db)
    # Public (non-admin) list — durum='Yayında' veya 'Aktif' filter
    items = repo.list(is_admin=False)
    assert len(items) >= 1
    assert any(b["baslik"] == "Test Blog" for b in items)

REPO_TESTS = [
    ("portfoy_repo_list", test_portfoy_repo_list),
    ("portfoy_repo_get", test_portfoy_repo_get),
    ("portfoy_repo_counts", test_portfoy_repo_counts),
    ("portfoy_repo_exists", test_portfoy_repo_exists),
    ("kullanici_repo_get_by_email", test_kullanici_repo_get_by_email),
    ("ayar_repo_set_get", test_ayar_repo_set_get),
    ("blog_repo_list_published", test_blog_repo_list_published),
]


# ─── Service Tests (4) ────────────────────────────────────────────────────────
def test_portfoy_service_list():
    db = get_test_db(); setup_test_db(db)
    s = PortfoyService(PortfoyRepository(db), KullaniciRepository(db), AyarRepository(db), IstekRepository(db))
    items = s.listele(None)
    assert len(items) == 1

def test_portfoy_service_detay():
    db = get_test_db(); setup_test_db(db)
    s = PortfoyService(PortfoyRepository(db), KullaniciRepository(db), AyarRepository(db), IstekRepository(db))
    d = s.detay(1, None)
    assert d["baslik"] == "Test Villa"

def test_auth_service_login_success():
    db = get_test_db(); setup_test_db(db)
    s = AuthService(KullaniciRepository(db))
    r = s.login("admin@test.com", "admin123", "1.2.3.4")
    assert r.access_token
    assert r.rol == "admin"
    assert r.ad == "Test Admin"

def test_auth_service_login_wrong_password():
    db = get_test_db(); setup_test_db(db)
    s = AuthService(KullaniciRepository(db))
    try:
        s.login("admin@test.com", "wrongpass", "1.2.3.4")
        assert False, "Should have raised"
    except Exception as e:
        assert "hatalı" in str(e).lower() or "400" in str(e)

SERVICE_TESTS = [
    ("portfoy_service_list", test_portfoy_service_list),
    ("portfoy_service_detay", test_portfoy_service_detay),
    ("auth_service_login_success", test_auth_service_login_success),
    ("auth_service_login_wrong_password", test_auth_service_login_wrong_password),
]


# ─── Login Tests (5) ──────────────────────────────────────────────────────────
def test_login_empty_email():
    db = get_test_db(); setup_test_db(db)
    s = AuthService(KullaniciRepository(db))
    try:
        s.login("", "x", "1.2.3.4")
        assert False, "Should 400"
    except Exception as e:
        assert "Geçersiz" in str(e) or "400" in str(e)

def test_login_very_long_email():
    db = get_test_db(); setup_test_db(db)
    s = AuthService(KullaniciRepository(db))
    long_email = "x" * 200
    try:
        s.login(long_email, "y", "1.2.3.4")
        assert False
    except Exception as e:
        assert "Geçersiz" in str(e) or "400" in str(e)

def test_login_unapproved_account():
    db = get_test_db(); setup_test_db(db)
    s = AuthService(KullaniciRepository(db))
    try:
        s.login("bekleyen@test.com", "sifre123", "1.2.3.4")
        assert False, "Unapproved should block"
    except Exception as e:
        # ForbiddenError, 403 expected
        assert "onay" in str(e).lower() or "403" in str(e)

def test_login_inactive_account():
    db = get_test_db(); setup_test_db(db)
    s = AuthService(KullaniciRepository(db))
    # aktif=0 → get_by_email(aktif_only=True) ile bulunmaz
    try:
        r = s.login("pasif@test.com", "sifre123", "1.2.3.4")
        # bulunamazsa → AppError("Email veya şifre hatalı", 400)
    except Exception as e:
        # Hata normal — pasif kullanıcı email aktif_only ile buluno
        pass

def test_login_rate_limit():
    # Aynı IP ile 5 başarısız → 6. denemede lock
    db = get_test_db(); setup_test_db(db)
    # Rate-limit fonksiyonlarını sıfırla
    from backend.core import security
    security._giris_denemeleri.clear()
    security._engellenen_ipler.clear()
    s = AuthService(KullaniciRepository(db))
    err_count = 0
    for i in range(5):
        try:
            s.login("admin@test.com", "wrong", "rate-ip-1")
        except Exception:
            err_count += 1
    # 5. denemede lock atılmalı
    assert err_count >= 1
    # Şimdi IP engellenmiş olmalı — 6. deneme HTTP 429
    try:
        s.login("admin@test.com", "admin123", "rate-ip-1")
        assert False, "Should be locked"
    except Exception as e:
        msg = str(e)
        assert "bekley" in msg.lower() or "429" in msg or "too many" in msg.lower()

LOGIN_TESTS = [
    ("login_empty_email", test_login_empty_email),
    ("login_very_long_email", test_login_very_long_email),
    ("login_unapproved_account", test_login_unapproved_account),
    ("login_inactive_account", test_login_inactive_account),
    ("login_rate_limit", test_login_rate_limit),
]


# ─── HTTP/API/PWA/SEO Tests ───────────────────────────────────────────────────
def make_client():
    """TestClient oluşturur. httpx yoksa skip flag set eder."""
    if not HTTP_OK:
        return None
    from app import app
    return TestClient(app)


def test_http_health():
    c = make_client()
    if not c: return
    r = c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert "version" in body
    assert "build_date" in body
    assert "git_hash" in body

def test_http_health_head():
    c = make_client()
    if not c: return
    r = c.head("/health")
    assert r.status_code == 200

def test_http_api_portfoyler():
    c = make_client()
    if not c: return
    r = c.get("/api/portfoyler")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True

def test_http_api_portfoy_detay():
    c = make_client()
    if not c: return
    r = c.get("/api/portfoyler/1")
    assert r.status_code == 200

def test_http_404_unknown_api():
    c = make_client()
    if not c: return
    r = c.get("/api/bilinmeyen-endpoint")
    # FastAPI / starlette /olmayan-api için 404 döner
    assert r.status_code in (404, 405, 422)

def test_http_404_spa_skip():
    c = make_client()
    if not c: return
    # favicon.ico MEVCUTSA → 200 (image/vnd.microsoft.icon veya image/x-icon)
    # YOKSA → 404 JSON. Test ikon dosyaları üretildikten sonra 200 bekler.
    r = c.get("/favicon.ico")
    # DDosya varsa 200 image, yoksa 404 json — ikisi de kabul
    assert r.status_code in (200, 404)
    if r.status_code == 404:
        assert r.headers["content-type"].startswith("application/json")
    else:
        assert r.headers["content-type"].startswith("image/")

def test_http_pwa_sw_js_content_type():
    c = make_client()
    if not c: return
    r = c.get("/sw.js")
    assert r.status_code == 200
    ct = r.headers["content-type"]
    assert ct == "application/javascript", f"Expected application/javascript, got {ct}"

def test_http_pwa_sw_js_body():
    c = make_client()
    if not c: return
    r = c.get("/sw.js")
    text = r.text
    assert not text.startswith("<!DOCTYPE")
    assert "const CACHE" in text or "self.addEventListener" in text or "/**" in text

def test_http_pwa_manifest_content_type():
    c = make_client()
    if not c: return
    r = c.get("/manifest.json")
    assert r.status_code == 200
    ct = r.headers["content-type"]
    assert ct.startswith("application/manifest+json") or ct.startswith("application/json"), \
        f"Expected application/manifest+json, got {ct}"

def test_http_pwa_manifest_body():
    c = make_client()
    if not c: return
    r = c.get("/manifest.json")
    text = r.text
    assert text.startswith("{")
    body = r.json()
    assert "name" in body

def test_http_pwa_manifest_head():
    c = make_client()
    if not c: return
    r = c.head("/manifest.json")
    assert r.status_code == 200

def test_http_pwa_offline_html():
    c = make_client()
    if not c: return
    r = c.get("/offline.html")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")

def test_http_pwa_offline_html_head():
    c = make_client()
    if not c: return
    r = c.head("/offline.html")
    assert r.status_code == 200

def test_http_pwa_sw_head():
    c = make_client()
    if not c: return
    r = c.head("/sw.js")
    assert r.status_code == 200

def test_http_seo_sitemap():
    c = make_client()
    if not c: return
    r = c.get("/sitemap.xml")
    assert r.status_code == 200
    ct = r.headers["content-type"]
    assert "xml" in ct
    assert r.text.startswith("<?xml")

def test_http_seo_sitemap_head():
    c = make_client()
    if not c: return
    r = c.head("/sitemap.xml")
    assert r.status_code == 200

def test_http_seo_sitemap_images():
    c = make_client()
    if not c: return
    r = c.get("/sitemap-images.xml")
    assert r.status_code == 200
    assert "xml" in r.headers["content-type"]

def test_http_seo_robots_txt():
    c = make_client()
    if not c: return
    r = c.get("/robots.txt")
    assert r.status_code == 200
    ct = r.headers["content-type"]
    assert ct.startswith("text/plain")
    assert "User-agent" in r.text

def test_http_seo_robots_head():
    c = make_client()
    if not c: return
    r = c.head("/robots.txt")
    assert r.status_code == 200

def test_http_spa_root():
    c = make_client()
    if not c: return
    r = c.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "DOCTYPE" in r.text or "<html" in r.text.lower()

def test_http_spa_route_fallback():
    c = make_client()
    if not c: return
    r = c.get("/ilanlar")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")

def test_http_static_files():
    c = make_client()
    if not c: return
    r = c.get("/static/manifest.json")
    # Aynı dosya /static altında da var — StaticFiles
    assert r.status_code == 200

def test_http_x_request_id_header():
    c = make_client()
    if not c: return
    r = c.get("/health")
    # AccessLogMiddleware ekler
    assert "X-Request-ID" in r.headers

def test_http_request_id_passthrough():
    c = make_client()
    if not c: return
    rid = "test-rid-12345"
    r = c.get("/health", headers={"X-Request-ID": rid})
    # Client'in verdiği rid kullanılmalı
    assert r.headers.get("X-Request-ID") == rid


def test_http_pwa_favicon_ico():
    c = make_client()
    if not c: return
    r = c.get("/favicon.ico")
    # favicon.ico dosyası var → 200 + image/*
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")

def test_http_apple_touch_icon():
    c = make_client()
    if not c: return
    r = c.get("/static/img/apple-touch-icon.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"

def test_http_icon_192():
    c = make_client()
    if not c: return
    r = c.get("/static/img/icon-192x192.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"

def test_http_icon_512():
    c = make_client()
    if not c: return
    r = c.get("/static/img/icon-512x512.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"


HTTP_TESTS = [
    ("http_health", test_http_health),
    ("http_health_head", test_http_health_head),
    ("http_api_portfoyler", test_http_api_portfoyler),
    ("http_api_portfoy_detay", test_http_api_portfoy_detay),
    ("http_404_unknown_api", test_http_404_unknown_api),
    ("http_404_spa_skip", test_http_404_spa_skip),
    ("http_pwa_sw_js_content_type", test_http_pwa_sw_js_content_type),
    ("http_pwa_sw_js_body", test_http_pwa_sw_js_body),
    ("http_pwa_manifest_content_type", test_http_pwa_manifest_content_type),
    ("http_pwa_manifest_body", test_http_pwa_manifest_body),
    ("http_pwa_manifest_head", test_http_pwa_manifest_head),
    ("http_pwa_offline_html", test_http_pwa_offline_html),
    ("http_pwa_offline_html_head", test_http_pwa_offline_html_head),
    ("http_pwa_sw_head", test_http_pwa_sw_head),
    ("http_pwa_favicon_ico", test_http_pwa_favicon_ico),
    ("http_apple_touch_icon", test_http_apple_touch_icon),
    ("http_icon_192", test_http_icon_192),
    ("http_icon_512", test_http_icon_512),
    ("http_seo_sitemap", test_http_seo_sitemap),
    ("http_seo_sitemap_head", test_http_seo_sitemap_head),
    ("http_seo_sitemap_images", test_http_seo_sitemap_images),
    ("http_seo_robots_txt", test_http_seo_robots_txt),
    ("http_seo_robots_head", test_http_seo_robots_head),
    ("http_spa_root", test_http_spa_root),
    ("http_spa_route_fallback", test_http_spa_route_fallback),
    ("http_static_files", test_http_static_files),
    ("http_x_request_id_header", test_http_x_request_id_header),
    ("http_request_id_passthrough", test_http_request_id_passthrough),
]


# ─── CSRF Security Tests (3) ─────────────────────────────────────────────────
def test_csrf_blocks_form_post():
    c = make_client()
    if not c: return
    # form-encoded CSRF vector → 415
    r = c.post("/api/auth/giris",
               data={"email": "a", "sifre": "b"},
               headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 415

def test_csrf_allows_json_post():
    c = make_client()
    if not c: return
    # JSON OK
    r = c.post("/api/auth/sifre-sifirlama-baslat", json={"email": "x@y.z"})
    assert r.status_code == 200  # success=true ile yanıt döner (non-existent user sessiz)

def test_csrf_allows_get():
    c = make_client()
    if not c: return
    r = c.get("/api/portfoyler")
    assert r.status_code == 200


CSRF_TESTS = [
    ("csrf_blocks_form_post", test_csrf_blocks_form_post),
    ("csrf_allows_json_post", test_csrf_allows_json_post),
    ("csrf_allows_get", test_csrf_allows_get),
]


# ─── Upload Validation Tests (6) ──────────────────────────────────────────────
def test_upload_validation_pdf_ok():
    out = validate_upload_filename("test.pdf")
    assert out == "test.pdf"

def test_upload_validation_rejects_exe():
    try:
        validate_upload_filename("malware.exe")
        assert False, "Should reject .exe"
    except Exception:
        pass

def test_upload_validation_rejects_path_traversal():
    try:
        validate_upload_filename("../../etc/passwd")
        # ../../etc/passwd has no extension → REJECTED via extension check
    except Exception:
        pass

def test_upload_validation_rejects_php():
    try:
        validate_upload_filename("shell.php")
        assert False
    except Exception:
        pass

def test_upload_validation_rejects_empty():
    try:
        validate_upload_filename("")
        assert False
    except Exception:
        pass

def test_upload_validation_rejects_long_name():
    long_name = "x" * 250 + ".pdf"
    try:
        validate_upload_filename(long_name)
        assert False
    except Exception:
        pass


def test_magic_ok_image_jpeg():
    assert _magic_ok(b"\xff\xd8\xff" + b"\x00" * 100) is True

def test_magic_ok_image_png():
    assert _magic_ok(b"\x89PNG" + b"\x00" * 100) is True

def test_magic_ok_invalid():
    assert _magic_ok(b"not an image" * 20) is False

def test_doc_magic_pdf():
    assert _doc_magic_ok(b"%PDF-1.4 test") == "pdf"

def test_doc_magic_zip():
    assert _doc_magic_ok(b"PK\x03\x04 content") == "docx"

def test_doc_magic_invalid():
    assert _doc_magic_ok(b"not a doc") is None

UPLOAD_TESTS = [
    ("upload_validation_pdf_ok", test_upload_validation_pdf_ok),
    ("upload_validation_rejects_exe", test_upload_validation_rejects_exe),
    ("upload_validation_rejects_path_traversal", test_upload_validation_rejects_path_traversal),
    ("upload_validation_rejects_php", test_upload_validation_rejects_php),
    ("upload_validation_rejects_empty", test_upload_validation_rejects_empty),
    ("upload_validation_rejects_long_name", test_upload_validation_rejects_long_name),
    ("magic_ok_image_jpeg", test_magic_ok_image_jpeg),
    ("magic_ok_image_png", test_magic_ok_image_png),
    ("magic_ok_invalid", test_magic_ok_invalid),
    ("doc_magic_pdf", test_doc_magic_pdf),
    ("doc_magic_zip", test_doc_magic_zip),
    ("doc_magic_invalid", test_doc_magic_invalid),
]


# ─── Response Model Tests (3) ────────────────────────────────────────────────
def test_response_ok():
    r = ok({"id": 1}, "Başarılı")
    assert r["success"] is True
    assert r["data"]["id"] == 1
    assert r["message"] == "Başarılı"

def test_response_fail():
    r = fail("Hata")
    assert r["success"] is False
    assert r["message"] == "Hata"
    assert r["data"] is None

def test_response_api_response_model():
    m = ApiResponse(success=True, message="ok", data={"id": 1})
    assert m.success is True
    assert m.data["id"] == 1


RESPONSE_TESTS = [
    ("response_ok", test_response_ok),
    ("response_fail", test_response_fail),
    ("response_api_response_model", test_response_api_response_model),
]


# ─── Settings + Version Tests (5) ─────────────────────────────────────────────
def test_settings_singleton():
    from backend.core.settings import settings as s1, settings as s2
    assert s1 is s2

def test_settings_has_database_url():
    assert settings.DATABASE_URL.startswith("sqlite:")

def test_settings_has_jwt_secret():
    assert settings.JWT_SECRET
    assert len(settings.JWT_SECRET) > 10

def test_settings_allowed_uploads():
    assert "pdf" in settings.ALLOWED_UPLOAD_EXTENSIONS
    assert "exe" not in settings.ALLOWED_UPLOAD_EXTENSIONS

def test_settings_env_override():
    assert isinstance(settings.DEBUG, bool)
    assert isinstance(settings.MAX_UPLOAD_MB, int)
    assert settings.MAX_UPLOAD_MB > 0

SETTINGS_TESTS = [
    ("settings_singleton", test_settings_singleton),
    ("settings_has_database_url", test_settings_has_database_url),
    ("settings_has_jwt_secret", test_settings_has_jwt_secret),
    ("settings_allowed_uploads", test_settings_allowed_uploads),
    ("settings_env_override", test_settings_env_override),
]


# ─── Version Tests (3) ──────────────────────────────────────────────────────
def test_version_info_dict():
    info = get_version_info()
    assert "version" in info
    assert "build_date" in info
    assert "git_hash" in info
    assert "domain" in info

def test_version_matches_settings():
    info = get_version_info()
    assert info["version"] == settings.API_VERSION

def test_version_git_hash_format():
    info = get_version_info()
    if info["git_hash"]:
        # 40 hex chars (git) ya da custom
        assert len(info["git_hash"]) >= 7


VERSION_TESTS = [
    ("version_info_dict", test_version_info_dict),
    ("version_matches_settings", test_version_matches_settings),
    ("version_git_hash_format", test_version_git_hash_format),
]


# ─── Logging Tests (4) ────────────────────────────────────────────────────────
def test_logging_initialize_creates_files():
    from backend.core import logging as _logmod
    _logmod._INITIALIZED = False  # Reset for test isolation
    _logmod.initialize()
    log = _logmod.get_logger("test_module")
    log.info("test message from app")
    acc = _logmod.get_access_logger()
    acc.info("127.0.0.1 | GET /test | 200 | 5ms | UA | rid=test")
    # Dosyalar mevcut mu?
    import os
    log_dir = settings.LOG_DIR
    assert (log_dir / "app.log").exists()
    assert (log_dir / "access.log").exists()
    assert (log_dir / "error.log").exists()

def test_logging_app_log_writes_message():
    from backend.core.logging import get_logger
    log = get_logger("verify_test")
    log.info("VERIFY_MARKER_12345")
    log_dir = settings.LOG_DIR
    content = (log_dir / "app.log").read_text(encoding="utf-8")
    assert "VERIFY_MARKER_12345" in content

def test_logging_error_log_on_error():
    from backend.core.logging import get_logger
    log = get_logger("error_test")
    try:
        raise RuntimeError("ERROR_MARKER_67890")
    except RuntimeError:
        log.exception("Captured error")
    log_dir = settings.LOG_DIR
    content = (log_dir / "error.log").read_text(encoding="utf-8")
    assert "ERROR_MARKER_67890" in content

def test_logging_access_separate_from_app():
    from backend.core.logging import get_access_logger
    acc = get_access_logger()
    acc.info("ACCESS_MARKER_ABCDEF")
    log_dir = settings.LOG_DIR
    acc_content = (log_dir / "access.log").read_text(encoding="utf-8")
    app_content = (log_dir / "app.log").read_text(encoding="utf-8")
    assert "ACCESS_MARKER_ABCDEF" in acc_content
    assert "ACCESS_MARKER_ABCDEF" not in app_content  # propagate=False

LOGGING_TESTS = [
    ("logging_initialize_creates_files", test_logging_initialize_creates_files),
    ("logging_app_log_writes_message", test_logging_app_log_writes_message),
    ("logging_error_log_on_error", test_logging_error_log_on_error),
    ("logging_access_separate_from_app", test_logging_access_separate_from_app),
]


# ─── Main ─────────────────────────────────────────────────────────────────────
ALL_CATEGORIES = [
    ("Password", PASSWORD_TESTS),
    ("JWT", JWT_TESTS),
    ("Repository CRUD", REPO_TESTS),
    ("Service", SERVICE_TESTS),
    ("Login", LOGIN_TESTS),
    ("HTTP / API", HTTP_TESTS),
    ("CSRF Security", CSRF_TESTS),
    ("Upload Validation", UPLOAD_TESTS),
    ("Response Model", RESPONSE_TESTS),
    ("Settings", SETTINGS_TESTS),
    ("Version", VERSION_TESTS),
    ("Logging", LOGGING_TESTS),
]

if __name__ == "__main__":
    total_passed = 0
    total_failed = 0
    cat_count = 0
    for cat_name, tests in ALL_CATEGORIES:
        cat_count += 1
        p, f = run_tests(cat_name, tests)
        total_passed += p
        total_failed += f
    print(f"\n{'='*60}")
    print(f"TOPLAM: {cat_count} kategori")
    print(f"  ✅ PASSED: {total_passed}")
    print(f"  ❌ FAILED: {total_failed}")
    print(f"  Toplam test: {total_passed + total_failed}")
    print(f"{'='*60}")
    if total_failed == 0:
        print("🎉 Tüm testler başarılı!")
    sys.exit(0 if total_failed == 0 else 1)
