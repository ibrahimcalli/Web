#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  Portföy Gayrimenkul — Güncelleme Scripti (Local PC Production)
#
#  Mimari: GitHub → Local PC (/home/ibrahim/.../emlak_web) → systemd → Cloudflare
#  Kullanım: sudo bash deploy/update.sh
#
#  İşlem sırası:
#    1. Git tag ile snapshot al (rollback için)
#    2. DB + uploads yedekle
#    3. Git pull (en son kod)
#    4. build_release.py çalıştır (CSS/JS minify)
#    5. Servis restart (emlak-api)
#    6. Health check + smoke test
#    7. Başarısızsa otomatik rollback (git checkout tag)
# ═══════════════════════════════════════════════════════════════
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib.sh"

banner "Portföy Gayrimenkul — Güncelleme"

# Argümanlar (require_root'tan ÖNCE)
NO_PULL=false
NO_BUILD=false
for arg in "$@"; do
    case "$arg" in
        --no-pull) NO_PULL=true ;;
        --no-build) NO_BUILD=true ;;
        --help|-h)
            echo "Kullanım: sudo bash $(basename "$0") [--no-pull] [--no-build]"
            echo "  --no-pull   Git pull yapma (yerel değişiklikleri deploy et)"
            echo "  --no-build  build_release.py çalıştırma (CSS/JS minify atla)"
            exit 0 ;;
    esac
done

# Root kontrolü — sistem yoksa şifre iste
log "Repo: $REPO_DIR"
log "Servis: $APP_SERVICE"
log "Port: $APP_PORT"
log "Domain: $DOMAIN"

# ─── 1. Snapshot al (git tag + DB backup) ──────────────────────
BEFORE_HASH=$(git_full_hash)
LABEL="pre_update_$(date +%Y%m%d_%H%M%S)_${BEFORE_HASH:0:7}"
log "Snapshot alınıyor: $LABEL"
snapshot_release "$LABEL" || warn "Snapshot alınamadı — devam ediliyor"

# ─── 2. Git pull ───────────────────────────────────────────────
if [ "$NO_PULL" = false ]; then
    log "Git pull ($REPO_DIR)..."
    (cd "$REPO_DIR" && git fetch --quiet origin)
    (cd "$REPO_DIR" && git pull --ff-only origin "$(git_branch)" 2>&1 || true)
    AFTER_HASH=$(git_full_hash)
    if [ "$AFTER_HASH" = "$BEFORE_HASH" ]; then
        warn "Git hash değişmedi — yine de deploy ediliyor"
    else
        ok "Yeni git hash: ${AFTER_HASH:0:7}"
    fi
else
    log "--no-pull: Git pull atlandı (yerel değişiklikler deploy ediliyor)"
fi

# ─── 3. build_release.py çalıştır (CSS/JS minify) ──────────────
if [ "$NO_BUILD" = false ]; then
    if [ -f "$REPO_DIR/build_release.py" ]; then
        log "build_release.py çalıştırılıyor..."
        (cd "$REPO_DIR" && python3 build_release.py) || \
            warn "build_release.py başarısız — devam ediliyor"
        ok "Build tamam"
    else
        warn "build_release.py bulunamadı — atlandı"
    fi
else
    log "--no-build: build_release.py atlandı"
fi

# ─── 4. Servis restart (root gerekli) ─────────────────────────
log "Servis restart ($APP_SERVICE)..."
require_root
systemctl restart "$APP_SERVICE" || die "Servis restart başarısız"

# ─── 5. Health check ───────────────────────────────────────────
log "Health check..."
if wait_for_health 45; then
    ok "Servis sağlıklı"
else
    err "Servis ayağa kalkmadı — ROLLBACK başlatılıyor"
    bash "$SCRIPT_DIR/rollback.sh" --latest --quiet || die "Rollback başarısız" 2
    die "Rollback tamamlandı — güncelleme başarısız" 1
fi

# ─── 6. Smoke test ─────────────────────────────────────────────
if ! smoke_test; then
    err "Smoke test başarısız — ROLLBACK başlatılıyor"
    bash "$SCRIPT_DIR/rollback.sh" --latest --quiet || die "Rollback başarısız" 2
    die "Rollback tamamlandı — smoke test hatalı" 1
fi

# ─── 7. Deploy log kaydı ───────────────────────────────────────
AFTER_HASH=$(git_full_hash)
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) deploy ${AFTER_HASH:0:7} smoke=ok" \
    >> "$APP_DIR/logs/deploy.log"

# ─── Özet ─────────────────────────────────────────────────────
echo ""
echo -e "${YESIL}╔══════════════════════════════════════╗${NC}"
echo -e "${YESIL}║   Güncelleme Tamamlandı! 🎉          ║${NC}"
echo -e "${YESIL}╚══════════════════════════════════════╝${NC}"
echo ""
echo "  Git hash:   ${AFTER_HASH:0:7} ($(git_branch))"
echo "  Servis:     $APP_SERVICE (restart)"
echo "  Health:     https://$DOMAIN/health"
echo "  Deploy log: $DEPLOY_LOG"
echo ""
echo "  Geri almak: sudo bash $SCRIPT_DIR/rollback.sh"
echo ""