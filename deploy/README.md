# Portföy Gayrimenkul — Deployment Scriptleri

Production kurulum, güncelleme ve rollback için otomasyon scriptleri.

## Hızlı Başlangıç

### İlk kurulum (fresh sunucu)
```bash
sudo bash deploy/install.sh
```
Tüm sunucu kurulumunu yapar: paketler, kullanıcı, Python venv, systemd, Nginx, UFW, SSL, cron.

### Güncelleme (mevcut deployment)
```bash
sudo bash deploy/update.sh
```
Git pull + dosya kopyalama + `pip install` + servis restart + health check + smoke test. Riskli durumda otomatik rollback.

### Geri al
```bash
sudo bash deploy/rollback.sh           # interaktif
sudo bash deploy/rollback.sh --latest  # en son snapshot
sudo bash deploy/rollback.sh --list    # sadece listele
```

---

## Komut Referansı

### `install.sh` — ilk kurulum
```bash
sudo bash deploy/install.sh
```

**Opsiyonel env değişkenleri:**
- `DOMAIN` — domain adı (default: `emlakfethiye.com.tr`)
- `APP_DIR` — kurulum dizini (default: `/opt/portfoy_web`)
- `APP_USER` — sistem kullanıcısı (default: `portfoy`)
- `APP_PORT` — uvicorn portu (default: `8000`)
- `INSTALL_SSL` — `yes`/`no`/`ask` (default: `yes`)

Örnek:
```bash
DOMAIN=emlakfethiye.com.tr APP_DIR=/opt/portfoy_web \
    sudo -E bash deploy/install.sh
```

**İçerik:**
1. apt paketleri (Python, Nginx, ufw, certbot, git, rsync)
2. `portfoy` kullanıcısı oluşturma
3. Dizin yapılandırması (releases + backup logs)
4. Git clone (veya local repo'dan kopyala)
5. Python venv + requirements.txt
6. Systemd birim dosyası (`/etc/systemd/system/portfoy-web.service`)
7. `/etc/portfoy.env` — JWT_SECRET üretimi (`chmod 600`)
8. Nginx konfig (`/etc/nginx/sites-available/portfoy-web`)
9. UFW kurallar (SSH + HTTP/HTTPS)
10. Servis başlatma + health cevap + smoke test
11. Let's Encrypt SSL (certbot)
12. Crontab (günlük yedek + SSL yenileme)

### `update.sh` — güncelleme
```bash
sudo bash deploy/update.sh
sudo bash deploy/update.sh --no-pull    # git pull atla
```

**İşlem sırası:**
1. **Snapshot** — mevcut deployment `/opt/portfoy_releases/release_<ts>_<git>`'e paketlenir (rollback için)
2. **DB backup** — `/opt/portfoy_yedek/db_<ts>.db`'ye kopyala
3. **Git pull** — `origin <branch>` (atlanabilir)
4. **Dosya kopyalama** — `app.py`, `backend/`, `src/`, `static/` (uploads KORUNUR), `deploy/`, `scripts/`
5. requirements diff kontrol — sadece değiştiyse `pip install`
6. **Restart** — `systemctl restart portfoy-web`
7. **Health check** — `/health` 200 + `"healthy"` (45s timeout)
8. **Smoke test** — 8 endpoint (PWA, SEO, API, SPA)
9. **Otomatik rollback** — smoke/health başarısızsa otomatik eski release'e geri alır, hata loglar

**Exit kodları:**
- `0` — başarı
- `1` — health/smoke başarısız, rollback tamamlandı
- `2` — kritik hata, manuel müdahale gerekir

### `rollback.sh` — geri al
```bash
sudo bash deploy/rollback.sh           # interaktif
sudo bash rollback.sh --latest         # en son release otomatik
sudo bash rollback.sh --label=LABEL    # özel etiket
sudo bash rollback.sh --list            # sadece listele
sudo bash rollback.sh --quiet           # onay isteme (update.sh içinden)
```

**İşlem sırası:**
1. Mevcut release'leri listele
2. Hedef release seç (interaktif / `--latest` / `--label`)
3. **Önce snapshot** — rollback işleminin kendisi için de "geri al" snapshot al
4. Backup DB
5. Servis durdur
6. Release dosyalarını `/opt/portfoy_web/`'e kopyala (uploads KORUNUR)
7. DB restore
8. Servis başlat
9. Health + smoke test
10. `deploy.log`'a yaz

### `backup.sh` — yedekleme
```bash
sudo -u portfoy bash deploy/backup.sh
```
Periyodik yedek — DB + uploads tar.gz. Cron'dan otomatik çağrılır (install.sh ile).

### `lib.sh` — ortak fonksiyon
Diğer scriptler tarafından `source`'lanır. Renkli log, health check, smoke test, snapshot, rollback listeleme.

---

## Önemli Dizinler

| Dizin | İçerik |
|-------|--------|
| `/opt/portfoy_web/` | Aktif kurulum (appdir) |
| `/opt/portfoy_web/app.py` | Kök ASGI app |
| `/opt/portfoy_web/backend/` | FastAPI router/repo/service |
| `/opt/portfoy_web/static/` | Frontend HTML, JS, CSS, PWA assets |
| `/opt/portfoy_web/static/uploads/` | Kullanıcı yüklediği resimler (rollback sırasında KORUNUR) |
| `/opt/portfoy_web/static/img/` | PWA ikonları, logo, og-default.jpg |
| `/opt/portfoy_web/emlak_web.db` | SQLite veritabanı |
| `/opt/portfoy_web/logs/` | * `access.log`, `error.log`, `app.log`, `deploy.log` |
| `/opt/portfoy_releases/` | Tüm snapshot'lar (son 10 tutulur) |
| `/opt/portfoy_yedek/` | DB + uploads yedekleri (30 gün) |
| `/etc/nginx/sites-available/portfoy-web` | Nginx config |
| `/etc/systemd/system/portfoy-web.service` | systemd birim |
| `/etc/portfoy.env` | Production secrets (JWT_SECRET), chmod 600 |

---

## Servis Yönetimi (manuel)

| Komut | Açıklama |
|-------|----------|
| `systemctl status portfoy-web` | Servis durumu |
| `systemctl restart portfoy-web` | Yeniden başlat |
| `systemctl stop portfoy-web` | Durdur |
| `journalctl -u portfoy-web -f` | Canlı systemd logu |
| `journalctl -u portfoy-web -n 50` | Son 50 satır |
| `tail -f /opt/portfoy_web/logs/app.log` | Uygulama logu |
| `tail -f /opt/portfoy_web/logs/error.log` | Hata logu |
| `tail -f /opt/portfoy_web/logs/access.log` | Access logu |
| `nginx -t` | Nginx config testi |
| `systemctl reload nginx` | Nginx reload |
| `curl http://127.0.0.1:8000/health` | Health check |
| `curl https://emlakfethiye.com.tr/health` | Public health |

---

## Deployment Senaryoları

### Senaryo 1: İlk kurulum (yeni sunucu)
```bash
# SSH ile sunucuya gir
ssh root@sunucu-ip
git clone https://github.com/ibrahimcalli/Web.git /tmp/portfoy_web
cd /tmp/portfoy_web
sudo bash deploy/install.sh
# Çıktıyı takip et — health OK + SSL kuruldu → tamam
```

### Senaryo 2: Güncelleme (açık ikonları ekledik)
```bash
ssh root@sunucu-ip
cd /opt/portfoy_web
git pull origin main
sudo bash deploy/update.sh
# → Snapshot alındı
# → pip install gereksiz (Pillow eklenmedi)
# → Restart + health 200 + smoke test 8/8 OK
# → "Güncelleme Tamamlandı!"
```

### Senaryo 3: Kötü deploy — rollback
```bash
# update.sh smoke test FAILED → otomatik rollback
# Manuel rollback gerekiyorsa:
sudo bash deploy/rollback.sh        # İnteraktif, en son snapshot
# veya:
sudo bash deploy/rollback.sh --latest
```

### Senaryo 4: Belirli release'e geri al
```bash
sudo bash deploy/rollback.sh --list
# Çıktı:
#   pre_update_20260716_193000_416a967 | 2026-07-16 19:30:00 | git:416a967...
#   rollback_20260716_184000_0f25928  | 2026-07-16 18:40:00 | git:0f25928...

sudo bash deploy/rollback.sh --label=pre_update_20260716_193000_416a967
```

### Senaryo 5: Arg-eksik — manuel restart
```bash
servis çalışmıyor mu?
sudo systemctl restart portfoy-web
sudo systemctl status portfoy-web
# hâlâ hata:
sudo journalctl -u portfoy-web -n 50 --no-pager
sudo tail -f /opt/portfoy_web/logs/error.log
```

---

## Production Secrets

`/etc/portfoy.env` (install.sh tarafından otomatik oluşturulur):
```ini
# Bu dosyayı ASLA git'e commit ETMEYİN
JWT_SECRET=<random64_random_url_safe>
DEBUG=false
DOMAIN=emlakfethiye.com.tr
```

Üretkenlik için isolasyon:
- Dosya sahibi: `root:portfoy`
- İzinler: `600` (sadece root okur, portfoy okur)
- systemd `EnvironmentFile=-/etc/portfoy.env` ile yüklenir (`-` = yoksa görmezden gel)

Yeni secret oluşturmak:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
sudo nano /etc/portfoy.env
sudo systemctl restart portfoy-web
```

---

## Cron Job'lar

`install.sh` `/etc/cron.d/portfoy-web` kurar:
- `0 2 * * *` (günlük 02:00) — `backup.sh` DB + uploads yedek
- `0 3 * * 0` (Pazar 03:00) — `certbot renew` + nginx reload

Crontab kontrol:
```bash
cat /etc/cron.d/portfoy-web
```

---

## Health Endpoint (production)

`https://emlakfethiye.com.tr/health` döner:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "build_date": "2026-07-16T08:23:06Z",
  "git_hash": "416a96d8dfda75e02c165b79cdbb3eabd038c34f",
  "git_branch": "main",
  "domain": "emlakfethiye.com.tr",
  "debug": false
}
```

**Monitoring için:**
- `status` `"healthy"` DEĞİLse → alert
- `git_hash` deployment'ı takip eder
- `debug` `true` ise (olmamalı!) → hemen düzelt

---

## Hata Giderme

### Servis ayağa kalkmıyor
1. `journalctl -u portfoy-web -n 50 --no-pager`
2. `tail -30 /opt/portfoy_web/logs/error.log`
3. `/etc/portfoy.env` dosyası mevcut mu? `JWT_SECRET` set mi?
4. `8000` portu kullanımda mı? `ss -ltnp | grep 8000`
5. Python venv bozuk mu? `sudo -u portfoy /opt/portfoy_web/venv/bin/python -c "import fastapi"`

### Nginx 502 Bad Gateway
1. `systemctl status portfoy-web` — servis çalışıyor mu?
2. `nginx -t` — config geçerli mi?
3. `/var/log/nginx/portfoy_error.log`'a bak

### Smoke test başarısız oldu
```bash
# Manuel çalıştır:
sudo bash deploy/lib.sh smoke_test
# veya
sudo bash deploy/rollback.sh --latest
```

### Database boş / veriler kayıp
1. `/opt/portfoy_yedek/`'e bak — `db_*.db` yedekleri 30 gün tutulur
2. Restore:
```bash
systemctl stop portfoy-web
cp /opt/portfoy_yedek/db_YYYYMMDD_HHMMSS.db /opt/portfoy_web/emlak_web.db
chown portfoy:portfoy /opt/portfoy_web/emlak_web.db
systemctl start portfoy-web
```

---

## Eski Scriptler (legacy)

Aşağıdaki scriptler hâlâ çalışır ama yeni scriptler önerilir:
- `setup.sh` — basitten kurulum (yerine `install.sh` kullanın)
- `update.sh` — basit güncelleme (yeni `update.sh` ile değiştirildi)
- `backup.sh` — aynı
- `01_kurulum.sh`, `02_ssl.sh`, `03_guncelle.sh`, `04_durum.sh` — eski numaralı scriptler

Yeni scriptler eski scriptlerin yerini alır — eski script'leri silebilir veya backup olarak tutabilirsiniz.

---

## Emeği Geçenler

- Version: `2.0.0`
- Production domain: https://emlakfethiye.com.tr
- Repo: https://github.com/ibrahimcalli/Web
