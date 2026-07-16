#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  deploy/lib.sh — Ortak fonksiyonlar
#
#  Diğer deploy script'leri tarafından source'lanır:
#      source "$(dirname "$0")/lib.sh"
#
#  İçeriği:
#    - Renkli log çıktısı (log/ok/warn/err)
#    - Health check bekleyici (wait_for_health)
#    - Systemd servis kontrolü (service_status)
#    - Git hash okuyucu (git_hash, git_branch)
#    - Backup/restore yardımcıları
# ═══════════════════════════════════════════════════════════════

# ─── Renkler (sadece TTY ise) ───────────────────────────────────
if [ -t 1 ]; then
    KIRMIZI='\033[0;31m'; YESIL='\033[0;32m'; SARI='\033[1;33m'
    MAVI='\033[0;34m';   BOLD='\033[1m';     NC='\033[0m'
else
    KIRMIZI=''; YESIL=''; SARI=''; MAVI=''; BOLD=''; NC=''
fi

# ─── Sabitler ───────────────────────────────────────────────────
# Mimari: GitHub → Local PC → systemd (emlak-api) → Cloudflare Tunnel
# Yani "production" zaten geliştirme makinesinin kendisi — ayrı sunucu yok.
# APP_DIR aynı zamanda git repository'sidir.

APP_USER="${APP_USER:-ibrahim}"
APP_DIR="${APP_DIR:-/home/ibrahim/PROGRAMLAR/WEB/emlak_web}"
APP_PORT="${APP_PORT:-8000}"
APP_SERVICE="${APP_SERVICE:-emlak-api}"
TUNNEL_SERVICE="${TUNNEL_SERVICE:-cloudflared}"
DOMAIN="${DOMAIN:-emlakfethiye.com.tr}"
PUBLIC_HEALTH_URL="https://${DOMAIN}/health"
LOCAL_HEALTH_URL="http://127.0.0.1:${APP_PORT}/health"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-30}"  # saniye

# Test runner (venv-based bazı ortamlarda farklı)
PYTHON_BIN="${PYTHON_BIN:-python3}"
TEST_RUNNER="${TEST_RUNNER:-python3 -W ignore tests/test_api.py}"
TEST_RUNNER_LEGACY="${TEST_RUNNER_LEGACY:-python3 -W ignore tests/test_backend.py}"

# Log dosyaları
APP_LOG="${APP_DIR}/logs/app.log"
ERROR_LOG="${APP_DIR}/logs/error.log"
ACCESS_LOG="${APP_DIR}/logs/access.log"
DEPLOY_LOG="${APP_DIR}/logs/deploy.log"

# Mevcut script dizini
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Repo kökü (lib.sh'nin 2 üstü)
REPO_DIR="$(dirname "$LIB_DIR")"
# Bu mimaride REPO_DIR == APP_DIR
[ "$REPO_DIR" != "$APP_DIR" ] && warn "REPO_DIR ($REPO_DIR) != APP_DIR ($APP_DIR) — biri yanlış olabilir"

# ─── Log fonksiyonları ───────────────────────────────────────────
log()  { echo -e "${MAVI}[•]${NC} $1"; }
ok()   { echo -e "${YESIL}[✓]${NC} $1"; }
warn() { echo -e "${SARI}[!]${NC} $1"; }
err()  { echo -e "${KIRMIZI}[✗]${NC} $1" >&2; }
die()  { err "$1"; exit "${2:-1}"; }

# Büyük başlık
banner() {
    echo ""
    echo -e "${MAVI}╔══════════════════════════════════════════╗${NC}"
    echo -e "${MAVI}║  $1${NC}"
    echo -e "${MAVI}╚══════════════════════════════════════════╝${NC}"
    echo ""
}

# ─── Root kontrolü ───────────────────────────────────────────────
require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        die "Bu script sudo/root olarak çalıştırılmalı: sudo $0"
    fi
}

# ─── Git bilgisi ─────────────────────────────────────────────────
git_hash() {
    (cd "$REPO_DIR" 2>/dev/null && git rev-parse --short HEAD 2>/dev/null) || echo "unknown"
}

git_branch() {
    (cd "$REPO_DIR" 2>/dev/null && git rev-parse --abbrev-ref HEAD 2>/dev/null) || echo "unknown"
}

git_full_hash() {
    (cd "$REPO_DIR" 2>/dev/null && git rev-parse HEAD 2>/dev/null) || echo "unknown"
}

# ─── Health check ────────────────────────────────────────────────
# wait_for_health [timeout_secs]
# Servis ayağa kalkıp /health 200 döndürüne kadar bekler.
# Önce local 127.0.0.1, sonra public neckline dener.
wait_for_health() {
    local timeout="${1:-$HEALTH_TIMEOUT}"
    local start=$(date +%s)
    log "Health check bekleniyor (max ${timeout}s)..."
    while true; do
        local elapsed=$(( $(date +%s) - start ))
        if [ "$elapsed" -ge "$timeout" ]; then
            err "Servis ${timeout}s içinde ayağa kalkmadı"
            return 1
        fi
        # Önce local health (tunnel olmadan da çalışır)
        local resp
        resp=$(curl -s -m 2 "$LOCAL_HEALTH_URL" 2>/dev/null) || true
        if echo "$resp" | grep -q '"status" *: *"healthy"' 2>/dev/null; then
            ok "Servis sağlıklı (${elapsed}s — local)"
            return 0
        fi
        sleep 1
    done
}

# Smoke test — PWA, SEO, API, SPA hepsi çalışıyor mu?
smoke_test() {
    log "Smoke test çalıştırılıyor..."
    local errors=0
    
    # PWA sw.js
    if ! curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${APP_PORT}/sw.js" | grep -q "^200$"; then
        err "  /sw.js 200 dönmedi"
        errors=$((errors + 1))
    fi
    # PWA manifest.json
    if ! curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${APP_PORT}/manifest.json" | grep -q "^200$"; then
        err "  /manifest.json 200 dönmedi"
        errors=$((errors + 1))
    fi
    # SEO sitemap.xml
    if ! curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${APP_PORT}/sitemap.xml" | grep -q "^200$"; then
        err "  /sitemap.xml 200 dönmedi"
        errors=$((errors + 1))
    fi
    # robots.txt
    if ! curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${APP_PORT}/robots.txt" | grep -q "^200$"; then
        err "  /robots.txt 200 dönmedi"
        errors=$((errors + 1))
    fi
    # favicon.ico
    if ! curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${APP_PORT}/favicon.ico" | grep -q "^200$"; then
        err "  /favicon.ico 200 dönmedi"
        errors=$((errors + 1))
    fi
    # SPA root
    if ! curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${APP_PORT}/" | grep -q "^200$"; then
        err "  / 200 dönmedi"
        errors=$((errors + 1))
    fi
    # API
    if ! curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${APP_PORT}/api/portfoyler" | grep -q "^200$"; then
        err "  /api/portfoyler 200 dönmedi"
        errors=$((errors + 1))
    fi
    # Bilinmeyen API 404 dönmeli (HTML düşmemeli)
    if ! curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${APP_PORT}/api/bilinmeyen-test" | grep -q "^404$"; then
        err "  /api/bilinmeyen-test 404 dönmedi"
        errors=$((errors + 1))
    fi
    
    if [ "$errors" -eq 0 ]; then
        ok "Smoke test PASSED — 8/8 endpoint sağlıklı"
        return 0
    else
        err "Smoke test FAILED — ${errors} endpoint hatalı"
        return 1
    fi
}

# ─── Servis yönetimi ────────────────────────────────────────────
service_status() {
    systemctl status "$APP_SERVICE" --no-pager 2>&1 | head -15
}

service_running() {
    systemctl is-active --quiet "$APP_SERVICE"
}

service_restart() {
    log "Servis yeniden başlatılıyor ($APP_SERVICE)..."
    systemctl restart "$APP_SERVICE" || die "Servis yeniden başlatılamadı"
    wait_for_health || return 1
    ok "Servis çalışıyor"
}

# ─── Diğer dizinler ────────────────────────────────────────────
BACKUP_DIR="${BACKUP_DIR:-${APP_DIR}/backups}"
# Bu mimaride release'ler git tag'leriyle tutulur (release klasörü yok).
# Snapshot_release sadece DB + uploads backup yapar — kodu git halleder.
GIT_TAG_PREFIX="${GIT_TAG_PREFIX:-deployed-}"

# ─── Dizin hazırlığı ────────────────────────────────────────────
ensure_dirs() {
    mkdir -p "$APP_DIR" "$APP_DIR/static/uploads" \
             "$APP_DIR/static/img" "$APP_DIR/logs"
    mkdir -p "$BACKUP_DIR"
    chown -R "$APP_USER:$APP_USER" "$APP_DIR" 2>/dev/null || true
    chown -R "$APP_USER:$APP_USER" "$BACKUP_DIR" 2>/dev/null || \
        chown -R "$APP_USER" "$BACKUP_DIR" 2>/dev/null || true
}

# ─── Release snapshot (git tabanlı) ─────────────────────────────
# Bu mimaride repo directory = APP_DIR. Snapshot = git tag + DB/upload backup.
# Rollback = git checkout tag + restore backup.
#
# Kullanım: snapshot_release "$label"
snapshot_release() {
    local label="${1:-$(date +%Y%m%d_%H%M%S)}"
    local tag="${GIT_TAG_PREFIX}${label}"
    
    log "Snapshot alınıyor: git tag '$tag'"
    
    # 1. Git tag oluştur (sadece commit varsa)
    if (cd "$REPO_DIR" 2>/dev/null && git rev-parse HEAD >/dev/null 2>&1); then
        (cd "$REPO_DIR" && git tag -f "$tag" >/dev/null 2>&1)
        local gh=$(cd "$REPO_DIR" && git rev-parse --short HEAD)
        ok "Git tag: $tag (commit: $gh)"
        # Release bilgisi
        {
            echo "release_label=$label"
            echo "tag=$tag"
            echo "snapshot_date=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
            echo "git_hash=$(cd "$REPO_DIR" && git rev-parse HEAD)"
            echo "git_branch=$(cd "$REPO_DIR" && git rev-parse --abbrev-ref HEAD)"
            echo "commit_subject=$(cd "$REPO_DIR" && git log -1 --format='%s')"
        } > "$APP_DIR/logs/release_${label}.info"
    else
        warn "Git repo bulunamadı — tag atlandı"
    fi
    
    # 2. DB + uploads backup
    backup_db
    backup_uploads
    
    # 3. Eski tag'ları temizle (son 20 tag tut)
    local count
    count=$(cd "$REPO_DIR" && git tag -l "${GIT_TAG_PREFIX}*" 2>/dev/null | wc -l) || count=0
    if [ "$count" -gt 20 ]; then
        log "Eski deploy tag'ları temizleniyor (son 20 tutulur)..."
        cd "$REPO_DIR" && git tag -l "${GIT_TAG_PREFIX}*" --sort=v:refname | head -n -20 | \
            while read t; do git tag -d "$t" >/dev/null 2>&1; done
        ok "Eski tag'lar temizlendi"
    fi
}

# ─── Yedek (backup) ─────────────────────────────────────────────
backup_db() {
    local ts=$(date +%Y%m%d_%H%M%S)
    local db_path="$APP_DIR/emlak_web.db"
    if [ -f "$db_path" ]; then
        local backup_path="$BACKUP_DIR/db_${ts}.db"
        cp "$db_path" "$backup_path"
        ok "DB yedek: $backup_path"
        # 30 günden eski DB yedeklerini sil
        find "$BACKUP_DIR" -name "db_*.db" -mtime +30 -delete 2>/dev/null
    fi
}

backup_uploads() {
    local ts=$(date +%Y%m%d_%H%M%S)
    if [ -d "$APP_DIR/static/uploads" ]; then
        local backup_path="$BACKUP_DIR/uploads_${ts}.tar.gz"
        tar -czf "$backup_path" -C "$APP_DIR/static" uploads/ 2>/dev/null
        ok "Uploads yedek: $backup_path"
        find "$BACKUP_DIR" -name "uploads_*.tar.gz" -mtime +30 -delete 2>/dev/null
    fi
}

# ─── Rollback için listeleme (git tabanlı) ───────────────────────
list_releases() {
    local tags
    tags=$(cd "$REPO_DIR" && git tag -l "${GIT_TAG_PREFIX}*" --sort=-v:refname 2>/dev/null)
    if [ -z "$tags" ]; then
        echo "Deploy tag'i yok (${GIT_TAG_PREFIX}*). İlk deploy'dan önce listelenemez."
        return
    fi
    echo "Mevcut deploy tag'leri (en yeni üstte):"
    echo ""
    printf "  %-40s %-22s %s\n" "LABEL" "DATE" "HASH"
    echo "  ────────────────────────────────────────────────────────────────"
    cd "$REPO_DIR" || return
    while IFS= read -r tag; do
        local label="${tag#${GIT_TAG_PREFIX}}"
        local date=$(git log -1 --format="%ai" "$tag" 2>/dev/null | cut -d' ' -f1,2)
        local hash=$(git rev-parse --short "$tag" 2>/dev/null)
        printf "  %-40s %-22s %s\n" "$label" "$date" "$hash"
    done <<< "$tags"
}

# Strip ANSI codes — log dosyalarına yazmak için
strip_ansi() {
    sed 's/\x1b\[[0-9;]*m//g'
}

# ─── CLI helper (lib.sh doğrudan çağrılınca) ─────────────────────
# Kullanım:
#   source lib.sh        # sadece fonksiyonları tanımlar
#   bash lib.sh smoke_test
#   bash lib.sh snapshot
#   bash lib.sh list_releases
if [ "${BASH_SOURCE[0]}" = "$0" ] && [ $# -gt 0 ]; then
    case "$1" in
        smoke_test)      smoke_test ;;
        list)            list_releases ;;
        list_releases)   list_releases ;;
        snapshot)        snapshot_release ;;
        *) echo "Bilinmeyen komut: $1"; echo "Kullanım: bash lib.sh [smoke_test|list|snapshot]"; exit 1 ;;
    esac
fi
