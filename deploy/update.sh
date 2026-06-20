#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  Portföy Gayrimenkul — Güncelleme Scripti
#  Kullanım: sudo bash update.sh
# ═══════════════════════════════════════════════════════════════

APP_DIR="/opt/portfoy_web"
APP_USER="portfoy"
YESIL='\033[0;32m'; MAVI='\033[0;34m'; NC='\033[0m'
log() { echo -e "${MAVI}[•]${NC} $1"; }
ok()  { echo -e "${YESIL}[✓]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(dirname "$SCRIPT_DIR")"

log "Servis durduruluyor..."
systemctl stop portfoy-web

log "Yedek alınıyor..."
cp "$APP_DIR/emlak_web.db" "$APP_DIR/logs/emlak_web_$(date +%Y%m%d_%H%M).db" 2>/dev/null || true

log "Dosyalar güncelleniyor..."
[ -f "$SOURCE_DIR/app.py" ]         && cp "$SOURCE_DIR/app.py"         "$APP_DIR/"
[ -f "$SOURCE_DIR/requirements.txt" ] && cp "$SOURCE_DIR/requirements.txt" "$APP_DIR/"
[ -d "$SOURCE_DIR/static" ]         && rsync -a --exclude='uploads/' "$SOURCE_DIR/static/" "$APP_DIR/static/"

log "Bağımlılıklar güncelleniyor..."
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"

chown -R "$APP_USER:$APP_USER" "$APP_DIR"

log "Servis başlatılıyor..."
systemctl start portfoy-web
sleep 2
systemctl is-active --quiet portfoy-web && ok "Güncelleme tamamlandı ✓" || echo "Hata — log: journalctl -u portfoy-web -n 20"
