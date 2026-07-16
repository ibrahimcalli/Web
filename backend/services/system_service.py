"""
Sistem bilgisi toplama servisi.

Admin panel "Sistem" bölümü için:
    - Durum: servis, disk, RAM, CPU, Python, nginx, cloudflared
    - Log: access/error/app.log son 200 satır
    - Commands: sık kullanılan komutlar
    - Bakım: cache temizle, log temizle, backup oluştur
    - AI Tanılama: tüm metrikleri tek json'da topla
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.core.settings import settings


BASH = "/bin/bash"
SERVIS_ADI = "emlak-api"
TUNNEL_ADI = "cloudflared"


def _cmd(cmd: str, timeout: int = 5) -> str:
    """Güvenli shell komut çalıştır — hata sessiz."""
    try:
        out = subprocess.run(
            [BASH, "-c", cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (out.stdout or "").strip() or (out.stderr or "").strip()[:200]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return "hata"


def _cmd_lines(cmd: str, timeout: int = 5) -> list[str]:
    """Komut çıktısını satır satır döndür."""
    out = _cmd(cmd, timeout)
    return [l for l in out.split("\n") if l.strip()]


def _file_tail(path: Path, lines: int = 200) -> str:
    """Dosyanın son N satırını oku."""
    try:
        if not path.exists() or path.stat().st_size == 0:
            return "(boş)"
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        return "".join(all_lines[-lines:])
    except (OSError, IOError):
        return "(okunamadı)"


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


# ─── Servis Durumu ──────────────────────────────────────────────
def servis_durumu() -> dict:
    """Servis, systemd, port durumu."""
    aktif = _cmd(f"systemctl is-active {SERVIS_ADI}")
    cloudflared = _cmd(f"systemctl is-active {TUNNEL_ADI}")
    port_check = _cmd("ss -ltnp | grep '8000'")
    memory = _cmd("free -h | grep Mem")
    disk = _cmd("df -h / | tail -1")
    uptime = _cmd("uptime -p")

    return {
        "servis": {
            "emlak_api": aktif or "inactive",
            "cloudflared": cloudflared or "inactive",
            "port_8000": "açık" if "8000" in port_check else "kapalı",
        },
        "sistem": {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "uptime": uptime,
            "memory": memory,
            "disk": disk,
        },
        "zaman": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


# ─── Log Görüntüleme ───────────────────────────────────────────
def log_goruntule(tip: str = "app", satir: int = 200) -> str:
    """Belirtilen log dosyasının son satırlarını döndür."""
    log_map = {
        "app": settings.LOG_DIR / "app.log",
        "error": settings.LOG_DIR / "error.log",
        "access": settings.LOG_DIR / "access.log",
        "deploy": settings.LOG_DIR / "deploy.log",
    }
    path = log_map.get(tip, log_map["app"])
    return _file_tail(path, satir)


# ─── Komutlar ────────────────────────────────────────────────────
KOMUTLAR = [
    {
        "grup": "Deploy",
        "komutlar": [
            {"aciklama": "Son kodu çek ve yayınla", "komut": "git pull && python3 build_release.py && sudo systemctl restart emlak-api"},
            {"aciklama": "Sadece build (CSS/JS minify)", "komut": "python3 build_release.py"},
            {"aciklama": "Servis restart", "komut": "sudo systemctl restart emlak-api"},
        ]
    },
    {
        "grup": "Servis",
        "komutlar": [
            {"aciklama": "Servis durumu", "komut": "sudo systemctl status emlak-api"},
            {"aciklama": "Servis logu (canlı)", "komut": "journalctl -u emlak-api -f"},
            {"aciklama": "Servis logu (son 50 satır)", "komut": "journalctl -u emlak-api -n 50 --no-pager"},
            {"aciklama": "Uygulama logu", "komut": "tail -100 logs/app.log"},
            {"aciklama": "Hata logu", "komut": "tail -100 logs/error.log"},
        ]
    },
    {
        "grup": "Health",
        "komutlar": [
            {"aciklama": "Health endpoint", "komut": "curl https://emlakfethiye.com.tr/health"},
            {"aciklama": "Service Worker", "komut": "curl -I https://emlakfethiye.com.tr/sw.js"},
            {"aciklama": "Manifest JSON", "komut": "curl https://emlakfethiye.com.tr/manifest.json"},
            {"aciklama": "Sitemap XML", "komut": "curl -I https://emlakfethiye.com.tr/sitemap.xml"},
        ]
    },
    {
        "grup": "Sistem",
        "komutlar": [
            {"aciklama": "Disk kullanımı", "komut": "df -h"},
            {"aciklama": "RAM kullanımı", "komut": "free -h"},
            {"aciklama": "Cloudflare Tunnel durumu", "komut": "sudo systemctl status cloudflared"},
            {"aciklama": "Python versiyon", "komut": "python3 --version"},
            {"aciklama": "Git durumu", "komut": "git status"},
            {"aciklama": "Git log (son 5)", "komut": "git log --oneline -5"},
        ]
    },
    {
        "grup": "Bakım",
        "komutlar": [
            {"aciklama": "Cache temizle (Python __pycache__)", "komut": "find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null"},
            {"aciklama": "Log dosyalarını temizle", "komut": "truncate -s 0 logs/*.log 2>/dev/null"},
            {"aciklama": "Yedek oluştur (DB + uploads)", "komut": "bash deploy/backup.sh"},
            {"aciklama": "Tüm testleri çalıştır", "komut": "python3 tests/test_api.py && python3 tests/test_backend.py"},
        ]
    },
]


# ─── Test Çalıştırıcı ────────────────────────────────────────────
def test_calistir() -> dict:
    """
    Tüm backend testlerini çalıştır.
    
    Returns:
        {
            "success": bool,
            "summary": "<test_raporu>",
            "timestamp": "...",
            "tests_api": [{"name": str, "passed": bool}, ...],
            "tests_backend": [{"name": str, "passed": bool}, ...],
        }
    """
    test_dizini = settings.BASE_DIR / "tests"
    sonuclar = []
    tum_basarili = True
    
    for test_file in ["test_api.py", "test_backend.py"]:
        path = test_dizini / test_file
        if not path.exists():
            sonuclar.append({"dosya": test_file, "durum": "bulunamadı", "cikti": ""})
            tum_basarili = False
            continue
        
        try:
            out = subprocess.run(
                ["python3", str(path)],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(settings.BASE_DIR),
            )
            cikti = out.stdout or out.stderr or ""
            # Başarı kontrolü — test dosyalarının çıktısı farklı:
            #   test_api.py: "🎉 Tüm testler başarılı!" + "PASSED: 82" + "FAILED: 0"
            #   test_backend.py: "✅ ..." + "🎉 Tüm testler başarılı!"
            cikti_lower = cikti.lower()
            basarili = (
                "tüm testler başarılı" in cikti_lower
                or ("passed" in cikti_lower and "failed: 0" in cikti_lower)
                or ("geçti" in cikti_lower and "başarısız" not in cikti_lower and "failed" not in cikti_lower)
            )
            if not basarili:
                tum_basarili = False
            sonuclar.append({
                "dosya": test_file,
                "durum": "geçti" if basarili else "başarısız",
                "cikti": cikti[-1500:] if cikti else "(çıktı yok)",
            })
        except subprocess.TimeoutExpired:
            sonuclar.append({"dosya": test_file, "durum": "zaman aşımı", "cikti": ""})
            tum_basarili = False
        except Exception as e:
            sonuclar.append({"dosya": test_file, "durum": f"hata: {e}", "cikti": ""})
            tum_basarili = False
    
    # Özet satırı
    gecen = sum(1 for s in sonuclar if s["durum"] == "geçti")
    toplam = len(sonuclar)
    ozet = f"{gecen}/{toplam} test dosyası geçti" if gecen == toplam else f"{gecen}/{toplam} geçti — bazı testler başarısız"
    
    return {
        "success": tum_basarili,
        "summary": ozet,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "results": sonuclar,
    }


# ─── AI Tanılama ─────────────────────────────────────────────────
def ai_tanilama() -> dict:
    """
    Tüm sistemi tek dict'te topla — AI'ya yapıştırmak için.
    
    İçerik:
        - servis durumu
        - sistem bilgisi
        - git durumu
        - health endpoint
        - test sonuçları (özet)
        - son deploy logları
        - nginx durumu
        - cloudflare tunnel
    """
    # Servis durumu
    durum = servis_durumu()
    
    # Git durumu
    git_hash = _cmd("git rev-parse HEAD")
    git_branch = _cmd("git rev-parse --abbrev-ref HEAD")
    git_status = _cmd("git status --short")
    git_log = _cmd("git log --oneline -5")
    
    # Health
    health = _cmd("curl -s -m 3 http://127.0.0.1:8000/health")
    
    # Nginx
    nginx_test = _cmd("nginx -t 2>&1", timeout=3)
    
    # Cloudflare
    tunnel_durum = _cmd(f"systemctl is-active {TUNNEL_ADI}")
    
    # Disk/RAM
    disk = _cmd("df -h / | tail -1")
    ram = _cmd("free -h | grep Mem")
    cpu = _cmd("top -bn1 | grep 'Cpu(s)' | head -1")
    load = _cmd("cat /proc/loadavg | cut -d' ' -f1-3")
    
    # Deploy log son 10
    deploy_log_path = settings.LOG_DIR / "deploy.log"
    deploy_log_son = _file_tail(deploy_log_path, 10)
    
    return {
        "tanilama_zamani": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "servis": durum["servis"],
        "sistem": {
            **durum["sistem"],
            "disk_kullanim": disk,
            "ram": ram,
            "cpu": cpu,
            "load_avg": load,
        },
        "git": {
            "hash": git_hash,
            "branch": git_branch,
            "degisiklik_var": bool(git_status.strip()),
            "degisiklikler": git_status[:500],
            "son_5_commit": git_log,
        },
        "health": health,
        "nginx": nginx_test,
        "cloudflare_tunnel": tunnel_durum,
        "deploy_log_son": deploy_log_son,
        "python_version": platform.python_version(),
    }


# ─── Bakım İşlemleri ────────────────────────────────────────────
def cache_temizle() -> dict:
    """Python cache (__pycache__) temizle."""
    try:
        count = 0
        for root, dirs, _ in os.walk(str(settings.BASE_DIR)):
            if "__pycache__" in dirs:
                shutil.rmtree(os.path.join(root, "__pycache__"), ignore_errors=True)
                count += 1
        return {"success": True, "mesaj": f"{count} __pycache__ dizini temizlendi"}
    except Exception as e:
        return {"success": False, "mesaj": f"Hata: {e}"}


def log_temizle() -> dict:
    """Log dosyalarını sıfırla (truncate)."""
    try:
        for name in ["app.log", "error.log", "access.log", "deploy.log"]:
            p = settings.LOG_DIR / name
            if p.exists():
                p.write_text("")
        return {"success": True, "mesaj": "Log dosyaları temizlendi"}
    except Exception as e:
        return {"success": False, "mesaj": f"Hata: {e}"}


def backup_olustur() -> dict:
    """Manuel backup oluştur ve path döndür."""
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = settings.BASE_DIR / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        db_path = settings.DB_PATH
        if db_path.exists():
            shutil.copy2(str(db_path), str(backup_dir / f"db_{ts}.db"))
        
        uploads = settings.BASE_DIR / "static" / "uploads"
        if uploads.exists():
            tar_path = backup_dir / f"uploads_{ts}.tar.gz"
            subprocess.run(["tar", "-czf", str(tar_path), "-C", str(uploads.parent), "uploads/"],
                         capture_output=True, timeout=30)
        
        return {"success": True, "mesaj": f"Yedek oluşturuldu: backups/ ({ts})"}
    except Exception as e:
        return {"success": False, "mesaj": f"Hata: {e}"}