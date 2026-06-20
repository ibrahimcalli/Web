#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# Portföy Gayrimenkul — Kod Güncelleme Scripti
# Kullanım: sudo bash deploy/03_guncelle.sh
# ═══════════════════════════════════════════════════════════════════════════════
set -e

GRN='\033[0;32m'; YLW='\033[1;33m'; BLU='\033[0;34m'; NC='\033[0m'
ok()   { echo -e "${GRN}✅ $1${NC}"; }
info() { echo -e "${BLU}ℹ  $1${NC}"; }
warn() { echo -e "${YLW}⚠  $1${NC}"; }

APP_DIR="/opt/portfoy_gayrimenkul"
APP_USER="portfoy"
BACKUP_DIR="/opt/portfoy_backups"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(dirname "$SCRIPT_DIR")"

[[ $EUID -ne 0 ]] && { echo "sudo gerekli"; exit 1; }

echo ""
echo -e "${BLU}╔══════════════════════════════════════╗${NC}"
echo -e "${BLU}║   Portföy Gayrimenkul — Güncelleme  ║${NC}"
echo -e "${BLU}╚══════════════════════════════════════╝${NC}"
echo ""

# Yedek al
TARIH=$(date +%Y%m%d_%H%M)
mkdir -p "$BACKUP_DIR"
info "Yedek alınıyor: $BACKUP_DIR/backup_$TARIH.tar.gz"
tar -czf "$BACKUP_DIR/backup_$TARIH.tar.gz" \
    "$APP_DIR/app.py" \
    "$APP_DIR/emlak_web.db" \
    2>/dev/null || true
ok "Yedek alındı"

# Eski yedekleri temizle (son 10 tane kalsın)
ls -t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true

# Dosyaları kopyala
info "Dosyalar güncelleniyor..."
[ -f "$SRC_DIR/app.py" ] && cp "$SRC_DIR/app.py" "$APP_DIR/"
[ -f "$SRC_DIR/static/index.html" ] && cp "$SRC_DIR/static/index.html" "$APP_DIR/static/"
chown -R "$APP_USER:$APP_USER" "$APP_DIR/app.py" "$APP_DIR/static/index.html" 2>/dev/null || true
ok "Dosyalar güncellendi"

# pip paketleri güncelle (requirements.txt varsa)
if [ -f "$SRC_DIR/requirements.txt" ]; then
    info "Python paketleri güncelleniyor..."
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$SRC_DIR/requirements.txt" -q
    ok "Python paketleri güncellendi"
fi

# Servisi yeniden başlat
info "Servis yeniden başlatılıyor..."
systemctl restart portfoy
sleep 2

if systemctl is-active --quiet portfoy; then
    ok "Servis çalışıyor ✓"
else
    warn "Servis başlamadı! Log:"
    journalctl -u portfoy -n 20 --no-pager
    exit 1
fi

echo ""
ok "════════════════════════════════════"
ok " GÜNCELLEME TAMAMLANDI — $TARIH"
ok "════════════════════════════════════"
echo ""
echo "  📋 Log: journalctl -u portfoy -f"
echo "  🔄 Manuel restart: systemctl restart portfoy"
echo "  📦 Yedekler: $BACKUP_DIR/"
echo ""
