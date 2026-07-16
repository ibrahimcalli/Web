#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  Portföy Gayrimenkul — Sunucu Kurulum Scripti
#  Ubuntu 22.04 / Debian 12 / Linux Mint 21+
#
#  Kullanım:
#      sudo bash install.sh              # interaktif
#      DOMAIN=emlakfethiye.com.tr \
#          APP_DIR=/opt/portfoy_web \
#          sudo -E bash install.sh       # non-interactive
#
#  İçerik:
#    1. Sistem paketleri (Python, Nginx, ufw, certbot)
#    2. Uygulama kullanıcısı ve dizin yapısı
#    3. Git clone (veya varolan repo'dan kopyala)
#    4. Python venv + requirements.txt
#    5. Systemd servis kaydı
#    6. Nginx reverse proxy
#    7. UFW güvenlik duvarı
#    8. SSL (Let's Encrypt, opsiyonel)
#    9. İlk deployment + health check + smoke test
#
#  Not: Mevcut setup.sh hâlâ çalışır; install.sh onun yerini alır
#       (geriye dönük uyumlu).
# ═══════════════════════════════════════════════════════════════
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

banner "Portföy Gayrimenkul — Sunucu Kurulumu"

require_root

# ─── Konfigürasyon (env override) ───────────────────────────────
: "${DOMAIN:=emlakfethiye.com.tr}"
: "${APP_USER:=portfoy}"
: "${APP_DIR:=/opt/portfoy_web}"
: "${APP_PORT:=8000}"
: "${GIT_REPO:=https://github.com/ibrahimcalli/Web.git}"
: "${GIT_BRANCH:=main}"
: "${INSTALL_SSL:=yes}"  # "yes" / "no" / "ask"

export DOMAIN APP_USER APP_DIR APP_PORT

log "Domain:      $DOMAIN"
log "App dizini:  $APP_DIR"
log "App user:    $APP_USER"
log "App port:    $APP_PORT"
log "Git branch:  $GIT_BRANCH"

# ─── 1. Sistem paketleri ────────────────────────────────────────
log "Sistem paketleri kuruluyor..."
apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv \
    nginx certbot python3-certbot-nginx \
    curl ufw git rsync
ok "Sistem paketleri tamam"

# ─── 2. Uygulama kullanıcısı ────────────────────────────────────
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --create-home --shell /bin/bash "$APP_USER"
    ok "Kullanıcı oluşturuldu: $APP_USER"
else
    ok "Kullanıcı mevcut: $APP_USER"
fi

# ─── 3. Dizin Yapısı ────────────────────────────────────────────
ensure_dirs

# ─── 4. Kodu kur (git clone veya local kopya) ──────────────────
# İlk kurulumda repo clone'la. Tekrar çalıştırılırsa update et.
if [ ! -d "$APP_DIR/.git" ]; then
    if [ -d "$REPO_DIR/.git" ] && [ -f "$REPO_DIR/app.py" ]; then
        # Local repo mevcut — rsync ile kopyala (.git hariç)
        log "Local repo'dan kopyalanıyor: $REPO_DIR → $APP_DIR"
        rsync -a \
            --exclude='.git' --exclude='__pycache__' \
            --exclude='.venv' --exclude='venv' \
            --exclude='logs/' --exclude='*.db' \
            --exclude='static/uploads/' \
            "$REPO_DIR/" "$APP_DIR/"
    else
        # Remote git clone
        log "Git clone: $GIT_REPO (branch: $GIT_BRANCH)"
        git clone --branch "$GIT_BRANCH" --depth 1 "$GIT_REPO" "$APP_DIR"
    fi
else
    log "Repo zaten mevcut — git pull yapılıyor"
    (cd "$APP_DIR" && git pull --ff-only origin "$GIT_BRANCH" || warn "Git pull başarısız — manuel kontrol gerekir")
fi

# logs/ ve static/uploads/ dizinleri her durumda mevcut olmalı
ensure_dirs

# ─── 5. Python venv + requirements ──────────────────────────────
if [ ! -d "$APP_DIR/venv" ]; then
    log "Python venv kuruluyor..."
    sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
fi

log "requirements.txt yükleniyor..."
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -q --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
ok "Python bağımlılıkları hazır"

# ─── 6. Systemd servisi ────────────────────────────────────────
log "Systemd servisi yazılıyor..."
cat > /etc/systemd/system/${APP_SERVICE}.service << EOF
[Unit]
Description=Portföy Gayrimenkul Web Servisi
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
Environment="PYTHONPATH=${APP_DIR}"
Environment="DOMAIN=${DOMAIN}"
# Üretimde mutlaka JWT_SECRET env'inden sağlanmalı (bkz /etc/portfoy.env)
EnvironmentFile=-/etc/portfoy.env
ExecStart=${APP_DIR}/venv/bin/uvicorn app:app \\
    --host 127.0.0.1 \\
    --port ${APP_PORT} \\
    --workers 2 \\
    --log-level warning \\
    --access-log
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=5
StartLimitInterval=60
StartLimitBurst=3
StandardOutput=append:${APP_DIR}/logs/app.log
StandardError=append:${APP_DIR}/logs/error.log
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${APP_DIR}

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$APP_SERVICE"
ok "Systemd servis dosyası yazıldı"

# ─── 7. JWT_SECRET (uyarı) ────────────────────────────────────
if [ ! -f /etc/portfoy.env ]; then
    warn "/etc/portfoy.env mevcut değil — JWT_SECRET üretimi uygulanıyor"
    SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    cat > /etc/portfoy.env << EOF
# Production secrets — bu dosyayı VERSİYON KONTROLÜNE EKLEMEYİN
# Sahiplik: root:portfoy, mod 600
JWT_SECRET=${SECRET}
DEBUG=false
DOMAIN=${DOMAIN}
EOF
    chmod 600 /etc/portfoy.env
    chown root:${APP_USER} /etc/portfoy.env
    ok "/etc/portfoy.env kuruldu (JWT_SECRET 64 byte random)"
else
    ok "/etc/portfoy.env mevcut"
fi

# ─── 8. Nginx ──────────────────────────────────────────────────
log "Nginx yapılandırılıyor..."
NGINX_CONF="/etc/nginx/sites-available/${APP_SERVICE}"
NGINX_LINK="/etc/nginx/sites-enabled/${APP_SERVICE}"

cat > "$NGINX_CONF" << 'EOF'
# Portföy Gayrimenkul — Nginx Yapılandırması
# Bu dosya install.sh tarafından otomatik üretilir.
# PWA dosyaları (sw.js, manifest.json, favicon.ico) backend'de
# WhitelistedStaticFiles ile servis edildiği için nginx'te ayrı
# location gerekmez — backend'e paslanır.

# HTTP → HTTPS yönlendirme (certbot ekler)
server {
    listen 80;
    server_name __DOMAIN__ www.__DOMAIN__;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }

    # Diğer her şeyi HTTPS'e yönlendir
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS — ana sunucu
server {
    listen 443 ssl http2;
    server_name __DOMAIN__ www.__DOMAIN__;

    # SSL sertifikası — certbot tarafından doldurulur
    # ssl_certificate     /etc/letsencrypt/live/__DOMAIN__/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/__DOMAIN__/privkey.pem;

    access_log /var/log/nginx/portfoy_access.log;
    error_log  /var/log/nginx/portfoy_error.log;

    # Upload limit (resimler için 20MB)
    client_max_body_size 20M;

    # Statik dosyalar — nginx'te servis (FastAPI'ye düşmeden hızlı)
    location /static/ {
        alias __APP_DIR__/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options "nosniff";
        add_header Referrer-Policy "strict-origin-when-cross-origin";
        # Güvenlik başlıkları
        gzip_static on;
    }

    # src/ — frontend JS/CSS
    location /src/ {
        alias __APP_DIR__/src/;
        expires 7d;
        add_header Cache-Control "public";
        add_header X-Content-Type-Options "nosniff";
    }

    # API + SPA — FastAPI'ye yönlendir
    location / {
        proxy_pass         http://127.0.0.1:__APP_PORT__;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade           $http_upgrade;
        proxy_set_header   Connection        "upgrade";
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;

        # Gzip sıkıştırma (HTML/CSS/JS/Application JSON)
        gzip on;
        gzip_types text/plain text/css application/json
                   application/javascript text/javascript
                   application/xml application/xml+rss
                   image/svg+xml;
        gzip_vary on;
        gzip_min_length 1000;
    }

    # Güvenlik başlıkları
    add_header X-Content-Type-Options        "nosniff"      always;
    add_header X-Frame-Options               "SAMEORIGIN"   always;
    add_header Referrer-Policy                "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy             "geolocation=(), microphone=(), camera=()" always;
    add_header Strict-Transport-Security      "max-age=63072000; includeSubDomains; preload" always;
}
EOF

# Placeholder'ları değiştir
sed -i "s|__DOMAIN__|${DOMAIN}|g"          "$NGINX_CONF"
sed -i "s|__APP_DIR__|${APP_DIR}|g"        "$NGINX_CONF"
sed -i "s|__APP_PORT__|${APP_PORT}|g"      "$NGINX_CONF"

rm -f /etc/nginx/sites-enabled/default
ln -sf "$NGINX_CONF" "$NGINX_LINK"

# Nginx config test
if nginx -t 2>&1; then
    systemctl reload nginx
    ok "Nginx yapılandırıldı ve reload edildi"
else
    die "Nginx konfig error — manuel kontrol: nginx -t"
fi

# ─── 9. UFW güvenlik duvarı ────────────────────────────────────
log "UFW güvenlik duvarı..."
ufw allow OpenSSH      >/dev/null 2>&1 || true
ufw allow 'Nginx Full' >/dev/null 2>&1 || true
ufw --force enable >/dev/null 2>&1 || warn "UFW etkinleştirilemedi"
ok "UFW: SSH + HTTP/HTTPS açık"

# ─── 10. Servis başlatma + health ────────────────────────────
log "Servis başlatılıyor..."
systemctl start "$APP_SERVICE" || systemctl restart "$APP_SERVICE"

if wait_for_health 45; then
    ok "Servis ayağa kalktı"
    smoke_test
else
    err "Servis ayağa kalkmadı — log:"
    journalctl -u "$APP_SERVICE" -n 30 --no-pager
    die "Kurulum tamamlanamadı"
fi

# ─── 11. SSL (Let's Encrypt) ───────────────────────────────────
INSTALL_SSL_ACTION="$INSTALL_SSL"
if [ "$INSTALL_SSL_ACTION" = "ask" ]; then
    echo ""
    read -p "$(${warn_inline:-echo} 'SSL kurulacak mı? (e/H): ')" ssl_cevap
    if [[ "$ssl_cevap" =~ ^[Ee]$ ]]; then
        INSTALL_SSL_ACTION=yes
    else
        INSTALL_SSL_ACTION=no
    fi
fi

if [ "$INSTALL_SSL_ACTION" = "yes" ]; then
    log "Let's Encrypt SSL kuruluyor..."
    mkdir -p /var/www/letsencrypt
    # Nginx HTTP-only modunda challenge için root doğru olsun
    certbot --nginx \
        -d "$DOMAIN" -d "www.$DOMAIN" \
        --non-interactive --agree-tos \
        --email "bilgi@$DOMAIN" \
        --redirect || warn "SSL kurulamadı — manuel: sudo certbot --nginx -d $DOMAIN"
    systemctl enable --now certbot.timer 2>/dev/null || true
    ok "SSL tamam"
else
    warn "SSL atlandı. Sonra: sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
fi

# ─── 12. Crontab (otomatik yedek + SSL yenileme) ───────────────
log "Crontab ekleniyor (yedek + SSL yenileme)..."
CRON_FILE="/etc/cron.d/portfoy-web"
cat > "$CRON_FILE" << EOF
# Portföy Gayrimenkul — cron jobs
# Günlük DB yedek (02:00)
0 2 * * * ${APP_USER} bash ${APP_DIR}/deploy/backup.sh >> ${APP_DIR}/logs/cron.log 2>&1

# SSL yenileme kontrol (haftalık, Pazar 03:00)
0 3 * * 0 root certbot renew --quiet --deploy-hook "systemctl reload nginx"
EOF
chmod 644 "$CRON_FILE"
ok "Crontab kuruldu: $CRON_FILE"

# ─── Özet ─────────────────────────────────────────────────────
echo ""
echo -e "${YESIL}╔══════════════════════════════════════╗${NC}"
echo -e "${YESIL}║   Kurulum Tamamlandı! 🎉              ║${NC}"
echo -e "${YESIL}╚══════════════════════════════════════╝${NC}"
echo ""
echo "  Servis:     systemctl status $APP_SERVICE"
echo "  Log:        journalctl -u $APP_SERVICE -f"
echo "              tail -f $APP_DIR/logs/app.log"
echo "  Nginx log:  /var/log/nginx/portfoy_*.log"
echo "  Health:     https://$DOMAIN/health"
echo ""
echo "  Sonraki adım:  sudo bash $APP_DIR/deploy/update.sh"
echo ""
