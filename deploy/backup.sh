#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  Portföy Gayrimenkul — Yedekleme Scripti
#  Kullanım: bash backup.sh
#  Crontab (günlük gece 02:00): 0 2 * * * bash /opt/portfoy_web/deploy/backup.sh
# ═══════════════════════════════════════════════════════════════

APP_DIR="/opt/portfoy_web"
YEDEK_DIR="/opt/portfoy_yedek"
TARIH=$(date +%Y%m%d_%H%M)
YESIL='\033[0;32m'; MAVI='\033[0;34m'; NC='\033[0m'

mkdir -p "$YEDEK_DIR"

echo -e "${MAVI}[•]${NC} Yedekleme başlıyor — $TARIH"

# Veritabanı yedekle
cp "$APP_DIR/emlak_web.db" "$YEDEK_DIR/db_$TARIH.db"

# Resimler yedekle (değişenleri)
tar -czf "$YEDEK_DIR/uploads_$TARIH.tar.gz" \
    -C "$APP_DIR/static" uploads/ 2>/dev/null

# 30 günden eski yedekleri sil
find "$YEDEK_DIR" -name "*.db" -mtime +30 -delete
find "$YEDEK_DIR" -name "*.tar.gz" -mtime +30 -delete

BOYUT=$(du -sh "$YEDEK_DIR" | cut -f1)
echo -e "${YESIL}[✓]${NC} Yedekleme tamamlandı — Toplam: $BOYUT"
echo -e "     DB:     $YEDEK_DIR/db_$TARIH.db"
echo -e "     Resimler: $YEDEK_DIR/uploads_$TARIH.tar.gz"
