#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Portföy Gayrimenkul — SSL Kurulum Scripti
# 01_kurulum.sh'dan sonra çalıştırın
# Kullanım: sudo bash deploy/02_ssl.sh
# ═══════════════════════════════════════════════════════════════════════════════
set -e

GRN='\033[0;32m'; YLW='\033[1;33m'; BLU='\033[0;34m'; NC='\033[0m'
ok()   { echo -e "${GRN}✅ $1${NC}"; }
info() { echo -e "${BLU}ℹ  $1${NC}"; }
warn() { echo -e "${YLW}⚠  $1${NC}"; }

DOMAIN="portfoygayrimenkul.com.tr"
WWW_DOMAIN="www.portfoygayrimenkul.com.tr"
EMAIL="bilgi@portfoygayrimenkul.com.tr"
APP_DIR="/opt/portfoy_gayrimenkul"

echo ""
echo -e "${BLU}╔══════════════════════════════════════╗${NC}"
echo -e "${BLU}║   SSL Sertifikası Kurulumu           ║${NC}"
echo -e "${BLU}╚══════════════════════════════════════╝${NC}"
echo ""

[[ $EUID -ne 0 ]] && { echo "sudo gerekli"; exit 1; }

# DNS kontrol
info "DNS doğrulanıyor..."
SERVER_IP=$(curl -s --max-time 5 ifconfig.me || hostname -I | awk '{print $1}')
DOMAIN_IP=$(dig +short "$DOMAIN" 2>/dev/null | head -1 || nslookup "$DOMAIN" 2>/dev/null | grep Address | tail -1 | awk '{print $2}')

echo "  Sunucu IP : $SERVER_IP"
echo "  Domain IP : ${DOMAIN_IP:-Çözümlenemedi}"

if [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
    warn "DNS henüz bu sunucuya işaret etmiyor!"
    warn "Cloudflare/DNS panelinizde A kaydı: $DOMAIN → $SERVER_IP"
    echo ""
    read -p "  Yine de devam et? (DNS yayılımı 1-48 saat sürebilir) [e/H] " -n 1 -r
    echo ""
    [[ ! $REPLY =~ ^[Ee]$ ]] && { info "SSL kurulumu iptal edildi."; exit 0; }
fi

# Certbot çalıştır
info "Let's Encrypt sertifikası alınıyor..."
certbot --nginx \
    -d "$DOMAIN" \
    -d "$WWW_DOMAIN" \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    --redirect \
    --keep-until-expiring

ok "SSL sertifikası alındı"

# Nginx yapılandırmasına ekstra güvenlik + statik dosya optimizasyonu ekle
info "Nginx optimize ediliyor..."

cat > /etc/nginx/sites-available/portfoy << NGINXEOF
# HTTP → HTTPS yönlendirme
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN $WWW_DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS ana blok
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN $WWW_DOMAIN;

    # SSL (certbot tarafından yönetilir)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Güvenlik başlıkları
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Yükleme boyutu (resimler için 20MB)
    client_max_body_size 20M;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json
               application/javascript application/xml+rss
               application/atom+xml image/svg+xml;

    # Statik dosyalar — Nginx direkt serve eder (hız için)
    location /static/uploads/ {
        alias $APP_DIR/static/uploads/;
        expires 7d;
        add_header Cache-Control "public";
        access_log off;
    }

    location /static/ {
        alias $APP_DIR/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # API + SPA → FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
        proxy_buffering off;
    }
}
NGINXEOF

nginx -t && systemctl reload nginx
ok "Nginx HTTPS konfigürasyonu aktif"

# Otomatik yenileme
systemctl enable certbot.timer 2>/dev/null || true
systemctl start  certbot.timer 2>/dev/null || true
ok "Certbot otomatik yenileme aktif (90 günde bir)"

echo ""
ok "═══════════════════════════════════"
ok " SSL KURULUMU TAMAMLANDI"
ok "═══════════════════════════════════"
echo ""
echo "  🔒 https://$DOMAIN"
echo "  🔒 https://$WWW_DOMAIN"
echo ""
echo "  Sertifika durumu: certbot certificates"
echo "  Yenileme testi:   certbot renew --dry-run"
echo ""
