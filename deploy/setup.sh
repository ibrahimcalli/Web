#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  Portföy Gayrimenkul — Sunucu Kurulum Scripti
#  Ubuntu 22.04 / Debian 12 / Linux Mint 21+
#  Kullanım: sudo bash setup.sh
# ═══════════════════════════════════════════════════════════════

set -e

DOMAIN="portfoygayrimenkul.com.tr"
APP_DIR="/opt/portfoy_web"
APP_USER="portfoy"
APP_PORT="8000"

KIRMIZI='\033[0;31m'; YESIL='\033[0;32m'
SARI='\033[1;33m';    MAVI='\033[0;34m'; NC='\033[0m'

log()  { echo -e "${MAVI}[•]${NC} $1"; }
ok()   { echo -e "${YESIL}[✓]${NC} $1"; }
warn() { echo -e "${SARI}[!]${NC} $1"; }
err()  { echo -e "${KIRMIZI}[✗]${NC} $1"; exit 1; }

echo ""
echo -e "${MAVI}╔══════════════════════════════════════╗${NC}"
echo -e "${MAVI}║  Portföy Gayrimenkul — Kurulum       ║${NC}"
echo -e "${MAVI}╚══════════════════════════════════════╝${NC}"
echo ""

[ "$(id -u)" -ne 0 ] && err "sudo bash setup.sh olarak çalıştırın"

# ── 1. Sistem Paketleri ────────────────────────────────────────
log "Sistem güncelleniyor..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv nginx \
    certbot python3-certbot-nginx curl ufw
ok "Sistem paketleri kuruldu"

# ── 2. Uygulama Kullanıcısı ────────────────────────────────────
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --create-home --shell /bin/bash "$APP_USER"
    ok "Kullanıcı oluşturuldu: $APP_USER"
else
    ok "Kullanıcı zaten mevcut: $APP_USER"
fi

# ── 3. Dizin Yapısı ────────────────────────────────────────────
log "Dizinler hazırlanıyor: $APP_DIR"
mkdir -p "$APP_DIR"/{static/uploads,static/img,logs}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$SOURCE_DIR/app.py" ]; then
    log "Dosyalar kopyalanıyor..."
    cp "$SOURCE_DIR/app.py"           "$APP_DIR/"
    cp "$SOURCE_DIR/requirements.txt" "$APP_DIR/"
    cp -r "$SOURCE_DIR/static/"       "$APP_DIR/"
    ok "Uygulama dosyaları kopyalandı"
else
    warn "app.py bulunamadı — $APP_DIR klasörüne manuel kopyalayın"
fi

chown -R "$APP_USER:$APP_USER" "$APP_DIR"
ok "Dizin izinleri ayarlandı"

# ── 4. Python Sanal Ortamı ────────────────────────────────────
log "Python venv kuruluyor..."
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -q --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
ok "Python ortamı hazır"

# ── 5. Systemd Servisi ────────────────────────────────────────
log "Systemd servisi oluşturuluyor..."
cat > /etc/systemd/system/portfoy-web.service << EOF
[Unit]
Description=Portföy Gayrimenkul Web Servisi
Documentation=https://portfoygayrimenkul.com.tr
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/uvicorn app:app \\
    --host 127.0.0.1 \\
    --port $APP_PORT \\
    --workers 2 \\
    --log-level warning
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=append:$APP_DIR/logs/app.log
StandardError=append:$APP_DIR/logs/error.log
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$APP_DIR

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable portfoy-web
systemctl start portfoy-web
sleep 2

if systemctl is-active --quiet portfoy-web; then
    ok "Servis aktif ve çalışıyor"
else
    warn "Servis başlatılamadı — log: journalctl -u portfoy-web -n 30"
fi

# ── 6. Nginx ─────────────────────────────────────────────────
log "Nginx yapılandırılıyor..."
cat > /etc/nginx/sites-available/portfoy-web << EOF
# Portföy Gayrimenkul — Nginx Yapılandırması
# portfoygayrimenkul.com.tr

# HTTP → HTTPS yönlendirme (SSL kurulduktan sonra certbot ekler)
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    access_log /var/log/nginx/portfoy_access.log;
    error_log  /var/log/nginx/portfoy_error.log;

    # Yükleme boyutu (resimler için 20MB)
    client_max_body_size 20M;

    # Statik dosyalar — Nginx doğrudan servis eder (çok hızlı)
    location /static/ {
        alias $APP_DIR/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options "nosniff";
        gzip_static on;
    }

    # API + SPA — FastAPI'ye yönlendir
    location / {
        proxy_pass         http://127.0.0.1:$APP_PORT;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade           \$http_upgrade;
        proxy_set_header   Connection        "upgrade";
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;

        # Gzip sıkıştırma
        gzip on;
        gzip_types text/plain application/json text/html application/javascript text/css;
    }
}
EOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/portfoy-web /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
ok "Nginx yapılandırıldı"

# ── 7. Güvenlik Duvarı ────────────────────────────────────────
log "Güvenlik duvarı (UFW) yapılandırılıyor..."
ufw allow OpenSSH      > /dev/null
ufw allow 'Nginx Full' > /dev/null
ufw --force enable     > /dev/null
ok "UFW aktif — SSH ve HTTP/HTTPS açık"

# ── 8. SSL — Let's Encrypt ────────────────────────────────────
echo ""
echo -e "  ${SARI}SSL için domain DNS'i bu sunucuya yönlendirilmiş olmalı${NC}"
read -p "  SSL sertifikası kurulsun mu? (e/H): " ssl_cevap
if [[ "$ssl_cevap" =~ ^[Ee]$ ]]; then
    log "Let's Encrypt SSL kuruluyor..."
    certbot --nginx \
        -d "$DOMAIN" -d "www.$DOMAIN" \
        --non-interactive --agree-tos \
        --email "bilgi@$DOMAIN" \
        --redirect
    # Otomatik yenileme
    systemctl enable --now certbot.timer 2>/dev/null || \
        (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet") | crontab -
    ok "SSL kuruldu — otomatik yenileme aktif"
else
    warn "SSL atlandı. Sonra: sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
fi

# ── Özet ─────────────────────────────────────────────────────
echo ""
echo -e "${YESIL}╔══════════════════════════════════════╗${NC}"
echo -e "${YESIL}║   Kurulum Tamamlandı! 🎉             ║${NC}"
echo -e "${YESIL}╚══════════════════════════════════════╝${NC}"
echo ""
echo -e "  🌐  Site      : http://$DOMAIN"
echo -e "  📁  Dizin     : $APP_DIR"
echo -e "  🔑  Admin     : bilgi@portfoygayrimenkul.com.tr"
echo ""
echo -e "  ${MAVI}Faydalı komutlar:${NC}"
echo -e "  journalctl -u portfoy-web -f          # Canlı log"
echo -e "  systemctl restart portfoy-web          # Yeniden başlat"
echo -e "  systemctl status  portfoy-web          # Durum"
echo -e "  bash ${SCRIPT_DIR}/update.sh           # Güncelle"
echo -e "  bash ${SCRIPT_DIR}/backup.sh           # Yedekle"
echo ""
