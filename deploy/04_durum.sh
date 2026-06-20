#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Portföy Gayrimenkul — Durum Kontrol Scripti
# Kullanım: bash deploy/04_durum.sh
# ═══════════════════════════════════════════════════════════════════════════════

GRN='\033[0;32m'; YLW='\033[1;33m'; RED='\033[0;31m'; BLU='\033[0;34m'; NC='\033[0m'
ok()   { echo -e "  ${GRN}✅ $1${NC}"; }
warn() { echo -e "  ${YLW}⚠  $1${NC}"; }
err()  { echo -e "  ${RED}❌ $1${NC}"; }

APP_DIR="/opt/portfoy_gayrimenkul"
APP_PORT="8000"

echo ""
echo -e "${BLU}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLU}║   Portföy Gayrimenkul — Sistem Durumu       ║${NC}"
echo -e "${BLU}╚══════════════════════════════════════════════╝${NC}"
echo ""

# Servisler
echo -e "${BLU}─── Servisler ────────────────────────────────${NC}"
for SVC in portfoy nginx; do
    if systemctl is-active --quiet "$SVC" 2>/dev/null; then
        ok "$SVC çalışıyor"
    else
        err "$SVC ÇALIŞMIYOR"
    fi
done

# UFW
echo ""
echo -e "${BLU}─── Güvenlik Duvarı ──────────────────────────${NC}"
if ufw status 2>/dev/null | grep -q "Status: active"; then
    ok "UFW aktif"
    ufw status 2>/dev/null | grep -E "ALLOW|DENY" | head -6 | while read line; do
        echo "     $line"
    done
else
    warn "UFW aktif değil"
fi

# SSL
echo ""
echo -e "${BLU}─── SSL Sertifikası ──────────────────────────${NC}"
CERT="/etc/letsencrypt/live/portfoygayrimenkul.com.tr/fullchain.pem"
if [ -f "$CERT" ]; then
    EXPIRE=$(openssl x509 -enddate -noout -in "$CERT" 2>/dev/null | cut -d= -f2)
    DAYS=$(( ($(date -d "$EXPIRE" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$EXPIRE" +%s 2>/dev/null) - $(date +%s)) / 86400 ))
    if [ "$DAYS" -gt 14 ]; then
        ok "SSL geçerli — $DAYS gün kaldı ($EXPIRE)"
    else
        warn "SSL yakında sona eriyor: $DAYS gün ($EXPIRE)"
    fi
else
    warn "SSL sertifikası yok (02_ssl.sh çalıştırın)"
fi

# API testi
echo ""
echo -e "${BLU}─── API Sağlık Testi ─────────────────────────${NC}"
API_RESP=$(curl -s --max-time 3 "http://127.0.0.1:$APP_PORT/api/kategoriler" 2>/dev/null)
if echo "$API_RESP" | grep -q "kategoriler"; then
    ok "API yanıt veriyor (port $APP_PORT)"
else
    err "API yanıt vermiyor"
fi

# Disk
echo ""
echo -e "${BLU}─── Disk & Bellek ────────────────────────────${NC}"
DISK_KULL=$(df -h "$APP_DIR" 2>/dev/null | awk 'NR==2{print $5}' | tr -d '%')
if [ -n "$DISK_KULL" ]; then
    [ "$DISK_KULL" -lt 80 ] && ok "Disk kullanımı: %$DISK_KULL" || warn "Disk kullanımı yüksek: %$DISK_KULL"
fi
MEM=$(free -m 2>/dev/null | awk 'NR==2{printf "Kullanılan: %sMB / Toplam: %sMB", $3, $2}')
[ -n "$MEM" ] && ok "Bellek: $MEM"

# DB boyutu
DB="$APP_DIR/emlak_web.db"
[ -f "$DB" ] && ok "Veritabanı: $(du -sh "$DB" | cut -f1)"

# Yükleme alanı
UPLOADS="$APP_DIR/static/uploads"
if [ -d "$UPLOADS" ]; then
    RESIM_SAYI=$(find "$UPLOADS" -type f 2>/dev/null | wc -l)
    ok "Yüklenen resim: $RESIM_SAYI dosya ($(du -sh "$UPLOADS" 2>/dev/null | cut -f1))"
fi

# Son loglar
echo ""
echo -e "${BLU}─── Son Log Satırları ────────────────────────${NC}"
journalctl -u portfoy -n 5 --no-pager 2>/dev/null | while read line; do
    echo "  $line"
done

echo ""
echo -e "${BLU}  Canlı log: journalctl -u portfoy -f${NC}"
echo ""
