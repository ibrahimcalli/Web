#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  Portföy Gayrimenkul — Geri Al (Rollback) Scripti
#
#  Mimari: Git tag tabanlı rollback
#  Kullanım:
#      sudo bash rollback.sh              # interaktif
#      sudo bash rollback.sh --latest     # en son tag
#      sudo bash rollback.sh --label=TAG  # özel tag
#      sudo bash rollback.sh --list       # sadece listele
#
#  İşlem sırası:
#    1. Tag'leri listele
#    2. Hedef tag seç
#    3. Mevcut durumu yeni tag olarak snapshot al
#    4. git checkout <tag>
#    5. build_release.py çalıştır
#    6. Servis restart + health + smoke test
# ═══════════════════════════════════════════════════════════════
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

banner "Portföy Gayrimenkul — Rollback"

# Argümanlar (require_root'tan önce — --list root gerekmesin)
QUIET=false
TARGET_TAG=""
USE_LATEST=false
shift_next=false

for arg in "$@"; do
    case "$arg" in
        --latest)  USE_LATEST=true ;;
        --list)    LIST_ONLY=true ;;
        --quiet)   QUIET=true ;;
        --label)   shift_next=true ;;
        --label=*) TARGET_TAG="${arg#--label=}" ;;
        -h|--help)
            echo "Kullanım: sudo bash $(basename "$0") [--latest|--label=TAG|--list|--quiet]"
            echo
            echo "  --latest         En son tag'a geri al"
            echo "  --label=TAG      Belirli bir tag'a geri al"
            echo "  --list           Sadece listele, geri alma"
            echo "  --quiet          Onay isteme (update.sh içinden)"
            exit 0 ;;
        *)
            if [ "$shift_next" = true ]; then
                TARGET_TAG="$arg"
                shift_next=false
            fi
            ;;
    esac
done

# --list root gerekmez
if [ "${LIST_ONLY:-false}" = true ]; then
    list_releases
    exit 0
fi

require_root

# Tag'leri listele
TAGS=()
while IFS= read -r line; do
    [ -n "$line" ] && TAGS+=("$line")
done < <(cd "$REPO_DIR" && git tag -l "${GIT_TAG_PREFIX}*" --sort=-v:refname 2>/dev/null)

if [ "${#TAGS[@]}" -eq 0 ]; then
    die "Geri alınacak tag yok — hiç deploy yapılmamış"
fi

echo "Mevcut deploy tag'leri:"
list_releases
echo ""

# Hedef tag seç
if [ "$USE_LATEST" = true ]; then
    TARGET_TAG="${TAGS[0]}"
    log "Otomatik: en son tag seçildi"
elif [ -z "$TARGET_TAG" ]; then
    # İnteraktif
    if [ "$QUIET" = true ]; then
        TARGET_TAG="${TAGS[0]}"
    else
        read -p "Hangi tag'a geri dönülecek? (numara — 1 en yeni): " choice
        if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "${#TAGS[@]}" ]; then
            die "Geçersiz seçim"
        fi
        TARGET_TAG="${TAGS[$((choice - 1))]}"
    fi
fi

log "Hedef tag: $TARGET_TAG"

# Onay
if [ "$QUIET" = false ]; then
    CURRENT_HASH=$(cd "$REPO_DIR" && git rev-parse --short HEAD)
    TARGET_HASH=$(cd "$REPO_DIR" && git rev-parse --short "$TARGET_TAG")
    echo ""
    warn "Bu işlem şunu geri alacak:"
    echo "      Şu an:  $CURRENT_HASH"
    echo "      Hedef:  $TARGET_TAG ($TARGET_HASH)"
    echo ""
    read -p "Onaylıyor musunuz? (evet/HAYIR): " confirm
    if ! [[ "$confirm" =~ ^[Ee][Vv][Ee][Tt]$ ]]; then
        die "İptal edildi"
    fi
fi

# ─── 1. Mevcut durumu snapshot al (rollback sonrası geri dönebilmek için) ──
CURRENT_LABEL="rollback_$(date +%Y%m%d_%H%M%S)"
log "Snapshot alınıyor: $CURRENT_LABEL"
snapshot_release "$CURRENT_LABEL" >/dev/null

# ─── 2. Servis durdur ─────────────────────────────────────────
log "Servis durduruluyor ($APP_SERVICE)..."
systemctl stop "$APP_SERVICE" || true

# ─── 3. Git checkout tag ───────────────────────────────────────
log "Git checkout $TARGET_TAG..."
(cd "$REPO_DIR" && git checkout --force "$TARGET_TAG") || \
    die "Git checkout başarısız"

# ─── 4. build_release.py ───────────────────────────────────────
if [ -f "$REPO_DIR/build_release.py" ]; then
    log "build_release.py çalıştırılıyor..."
    (cd "$REPO_DIR" && python3 build_release.py) || \
        warn "build_release.py başarısız — devam ediliyor"
fi

# ─── 5. DB restore (opsiyonel — snapshot'tan) ──────────────────
# Not: DB'yi geri yüklemek riskli olabilir (sonradan eklenen veriler kaybolur).
# Şimdilik DB restore etmiyoruz — sadece kod geri yükleniyor.

# ─── 6. Servis başlat ─────────────────────────────────────────
log "Servis başlatılıyor ($APP_SERVICE)..."
systemctl start "$APP_SERVICE" || systemctl restart "$APP_SERVICE"

# ─── 7. Health + smoke test ──────────────────────────────────
if ! wait_for_health 45; then
    err "Rollback sonrası servis ayağa kalkmadı — manuel müdahale gerekir"
    err "Log: journalctl -u $APP_SERVICE -n 30 --no-pager"
    exit 2
fi

if ! smoke_test; then
    warn "Smoke test başarısız — rollback yine de tamamlandı"
else
    ok "Smoke test PASSED"
fi

# ─── 8. Rollback kaydı ────────────────────────────────────────
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) rollback to $TARGET_TAG" \
    >> "$APP_DIR/logs/deploy.log"

# ─── Özet ─────────────────────────────────────────────────────
echo ""
echo -e "${YESIL}╔══════════════════════════════════════╗${NC}"
echo -e "${YESIL}║      Rollback Tamamlandı! 🎉         ║${NC}"
echo -e "${YESIL}╚══════════════════════════════════════╝${NC}"
echo ""
echo "  Target:     $TARGET_TAG"
echo "  Git hash:   $(cd "$REPO_DIR" && git rev-parse --short HEAD)"
echo "  Restart:    $APP_SERVICE"
echo "  Health:     https://$DOMAIN/health"
echo "  Deploy log: $DEPLOY_LOG"
echo ""

# Versiyon doğrula
RESP=$(curl -s "$LOCAL_HEALTH_URL" 2>/dev/null || true)
if [ -n "$RESP" ]; then
    VER=$(echo "$RESP" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    HASH=$(echo "$RESP" | grep -o '"git_hash":"[^"]*"' | cut -d'"' -f4)
    echo "  Version:    ${VER:-?}"
    echo "  Git hash:   ${HASH:-?}"
fi
echo ""