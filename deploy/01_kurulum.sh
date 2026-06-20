#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Portföy Gayrimenkul — Sunucu Kurulum Scripti
# Ubuntu 22.04 / 24.04 LTS
# Kullanım: sudo bash 01_kurulum.sh
# ═══════════════════════════════════════════════════════════════════════════════
set -e

# ── Renkler ──────────────────────────────────────────────────────────────────
GRN='\033[0;32m'; YLW='\033[1;33m'; RED='\033[0;31m'; BLU='\033[0;34m'; NC='\033[0m'
ok()   { echo -e "${GRN}✅ $1${NC}"; }
info() { echo -e "${BLU}ℹ  $1${NC}"; }
warn() { echo -e "${YLW}⚠  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; exit 1; }

# ── Yapılandırma ──────────────────────────────────────────────────────────────
DOMAIN="portfoygayrimenkul.com.tr"
WWW_DOMAIN="www.portfoygayrimenkul.com.tr"
APP_USER="portfoy"
APP_DIR="/opt/portfoy_gayrimenkul"
APP_PORT="8000"
PYTHON_VER="python3"

echo ""
echo -e "${BLU}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLU}║   Portföy Gayrimenkul — Sunucu Kurulumu     ║${NC}"
echo -e "${BLU}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ── Root kontrolü ─────────────────────────────────────────────────────────────
[[ $EUID -ne 0 ]] && err "Bu script root olarak çalıştırılmalı: sudo bash $0"

# ── Sistem güncellemesi ───────────────────────────────────────────────────────
info "Sistem paketleri güncelleniyor..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv \
    nginx certbot python3-certbot-nginx \
    ufw curl git unzip \
    2>/dev/null
ok "Sistem paketleri kuruldu"

# ── Kullanıcı oluştur ─────────────────────────────────────────────────────────
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home-dir "$APP_DIR" --create-home "$APP_USER"
    ok "Kullanıcı oluşturuldu: $APP_USER"
else
    info "Kullanıcı zaten var: $APP_USER"
fi

# ── Uygulama dizini ───────────────────────────────────────────────────────────
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/static/uploads"
mkdir -p "$APP_DIR/static/img"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
ok "Uygulama dizini: $APP_DIR"

# ── Python venv ───────────────────────────────────────────────────────────────
info "Python sanal ortamı oluşturuluyor..."
sudo -u "$APP_USER" $PYTHON_VER -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip -q
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install \
    fastapi uvicorn[standard] python-multipart \
    python-jose[cryptography] passlib[bcrypt] \
    bcrypt==4.0.1 python-docx aiofiles -q
ok "Python paketleri kuruldu"

# ── Uygulama dosyalarını kopyala ──────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_SRC="$(dirname "$SCRIPT_DIR")"

if [ -f "$APP_SRC/app.py" ]; then
    cp "$APP_SRC/app.py" "$APP_DIR/"
    cp -r "$APP_SRC/static/"* "$APP_DIR/static/" 2>/dev/null || true
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    ok "Uygulama dosyaları kopyalandı"
else
    warn "app.py bulunamadı. Manuel kopyalama gerekebilir: $APP_DIR/"
fi

# ── systemd Servis ────────────────────────────────────────────────────────────
info "systemd servisi oluşturuluyor..."
cat > /etc/systemd/system/portfoy.service << EOF
[Unit]
Description=Portföy Gayrimenkul Web Uygulaması
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/uvicorn app:app --host 127.0.0.1 --port $APP_PORT --workers 2
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=portfoy
# Güvenlik
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$APP_DIR
ProtectHome=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable portfoy
systemctl start portfoy
sleep 2

if systemctl is-active --quiet portfoy; then
    ok "systemd servisi aktif: portfoy.service"
else
    warn "Servis başlamadı. Log: journalctl -u portfoy -n 20"
fi

# ── UFW Güvenlik Duvarı ───────────────────────────────────────────────────────
info "UFW güvenlik duvarı yapılandırılıyor..."
ufw --force reset > /dev/null 2>&1
ufw default deny incoming  > /dev/null
ufw default allow outgoing > /dev/null
ufw allow ssh              > /dev/null
ufw allow 'Nginx Full'     > /dev/null
ufw --force enable         > /dev/null
ok "UFW aktif: SSH + Nginx Full (80/443)"

# ── Nginx ─────────────────────────────────────────────────────────────────────
info "Nginx yapılandırılıyor..."

# Varsayılan siteyi kaldır
rm -f /etc/nginx/sites-enabled/default

cat > /etc/nginx/sites-available/portfoy << EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN $WWW_DOMAIN;

    # Certbot doğrulaması için
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # HTTP → HTTPS yönlendirme (SSL sonrası aktif olur)
    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF

ln -sf /etc/nginx/sites-available/portfoy /etc/nginx/sites-enabled/portfoy

nginx -t && systemctl reload nginx
ok "Nginx yapılandırması hazır (HTTP)"

# ── SSL Sertifikası ───────────────────────────────────────────────────────────
echo ""
warn "SSL SERTİFİKASI"
echo "  Domain DNS kayıtlarınızın bu sunucuya işaret ettiğinden emin olun:"
echo "  A   $DOMAIN      → $(curl -s ifconfig.me 2>/dev/null || echo 'SUNUCU_IP')"
echo "  A   $WWW_DOMAIN  → $(curl -s ifconfig.me 2>/dev/null || echo 'SUNUCU_IP')"
echo ""
read -p "  DNS hazır mı? SSL sertifikası alınsın mı? [e/H] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Ee]$ ]]; then
    certbot --nginx -d "$DOMAIN" -d "$WWW_DOMAIN" \
        --non-interactive --agree-tos \
        --email "bilgi@portfoygayrimenkul.com.tr" \
        --redirect
    ok "SSL sertifikası alındı ve Nginx HTTPS ile güncellendi"

    # Otomatik yenileme
    systemctl enable certbot.timer
    systemctl start certbot.timer
    ok "Certbot otomatik yenileme aktif"
else
    info "SSL kurulumu atlandı. Sonradan çalıştırın:"
    echo "  sudo bash deploy/02_ssl.sh"
fi

# ── Nginx HTTPS Blok (SSL sonrası) ────────────────────────────────────────────
# Bu blok certbot tarafından otomatik eklenir.
# Ama manuel kurulum için de bırakıyoruz:
cat > /etc/nginx/sites-available/portfoy_https_template << 'EOF'
# Bu dosyayı certbot çalıştıktan sonra sites-available/portfoy ile birleştirin
# veya 02_ssl.sh scriptini kullanın.

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name portfoygayrimenkul.com.tr www.portfoygayrimenkul.com.tr;

    # SSL (certbot tarafından doldurulur)
    ssl_certificate /etc/letsencrypt/live/portfoygayrimenkul.com.tr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/portfoygayrimenkul.com.tr/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Güvenlik başlıkları
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Maksimum yükleme boyutu (resimler için)
    client_max_body_size 20M;

    # Statik dosyalar — doğrudan Nginx serve eder (FastAPI'yi bypass)
    location /static/ {
        alias /opt/portfoy_gayrimenkul/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # API + SPA — FastAPI'ye yönlendir
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
    }

    # Gzip sıkıştırma
    gzip on;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml image/svg+xml;
    gzip_min_length 1000;
}
EOF

echo ""
ok "════════════════════════════════════"
ok " KURULUM TAMAMLANDI"
ok "════════════════════════════════════"
echo ""
echo "  🌐 Site: http://$DOMAIN (SSL sonrası https://)"
echo "  📁 Dizin: $APP_DIR"
echo "  🔧 Servis: systemctl status portfoy"
echo "  📋 Log: journalctl -u portfoy -f"
echo "  🔄 Yeniden başlat: systemctl restart portfoy"
echo ""
echo "  Sonraki adım:"
echo "  sudo bash deploy/02_ssl.sh   (DNS hazırsa SSL al)"
echo "  sudo bash deploy/03_guncelle.sh  (kod güncellemesi)"
echo ""
