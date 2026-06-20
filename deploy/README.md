# Sunucu Kurulum Adımları

## Ön Gereksinimler
- Ubuntu 22.04 veya 24.04 LTS
- Root / sudo erişimi
- Domain DNS → sunucu IP yönlendirisi

## Kurulum Sırası

### 1. Dosyaları sunucuya kopyala
```bash
scp -r emlak_web/ root@SUNUCU_IP:/opt/
# veya git clone / SFTP ile
```

### 2. Temel kurulum (Python, Nginx, UFW, systemd)
```bash
sudo bash /opt/emlak_web/deploy/01_kurulum.sh
```
→ Python venv oluşturur, paketleri kurar, systemd servisini başlatır, UFW'yi ayarlar

### 3. SSL sertifikası (DNS hazırsa)
```bash
sudo bash /opt/emlak_web/deploy/02_ssl.sh
```
→ Let's Encrypt ücretsiz SSL, otomatik yenileme aktif

### 4. Kod güncellemesi (sonraki sürümler için)
```bash
sudo bash /opt/emlak_web/deploy/03_guncelle.sh
```
→ Yedek alır, dosyaları kopyalar, servisi yeniden başlatır

### 5. Sistem durumu kontrolü
```bash
bash /opt/emlak_web/deploy/04_durum.sh
```

## Servis Yönetimi

| Komut | Açıklama |
|-------|----------|
| `systemctl status portfoy`  | Durum |
| `systemctl restart portfoy` | Yeniden başlat |
| `systemctl stop portfoy`    | Durdur |
| `journalctl -u portfoy -f`  | Canlı log |
| `nginx -t`                  | Nginx yapılandırma testi |
| `systemctl reload nginx`    | Nginx yeniden yükle |

## Önemli Dizinler

| Dizin | Açıklama |
|-------|----------|
| `/opt/portfoy_gayrimenkul/` | Uygulama kök dizini |
| `/opt/portfoy_gayrimenkul/app.py` | Backend |
| `/opt/portfoy_gayrimenkul/static/` | Frontend + resimler |
| `/opt/portfoy_gayrimenkul/emlak_web.db` | Veritabanı |
| `/opt/portfoy_backups/` | Otomatik yedekler |
| `/etc/nginx/sites-available/portfoy` | Nginx config |
| `/etc/systemd/system/portfoy.service` | systemd servis |

## Admin Girişi
- URL: `https://portfoygayrimenkul.com.tr`
- E-posta: `bilgi@portfoygayrimenkul.com.tr`
- Şifre: `admin123` ← **Kurulum sonrası değiştirin!**
