"""Update Service — Versiyon kontrol ve güncelleme."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from typing import Optional

from backend.core.settings import settings, BASE_DIR


class UpdateService:
    def __init__(self):
        self.repo_dir = str(BASE_DIR)

    def versiyon_kontrol(self) -> dict:
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True, text=True, cwd=self.repo_dir, timeout=10,
            )
            commits = [c.strip() for c in result.stdout.strip().split("\n") if c.strip()]
            return {
                "current_version": settings.API_VERSION,
                "current_hash": subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"],
                    capture_output=True, text=True, cwd=self.repo_dir, timeout=5,
                ).stdout.strip(),
                "current_branch": subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True, text=True, cwd=self.repo_dir, timeout=5,
                ).stdout.strip(),
                "son_commits": commits,
                "check_time": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "current_version": settings.API_VERSION}

    def guncelle(self) -> dict:
        try:
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                capture_output=True, text=True, cwd=self.repo_dir, timeout=60,
            )
            if result.returncode != 0:
                return {"success": False, "message": result.stderr.strip()}
            new_hash = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, cwd=self.repo_dir, timeout=5,
            ).stdout.strip()
            return {"success": True, "message": result.stdout.strip(), "new_hash": new_hash}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def durum(self) -> dict:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=self.repo_dir, timeout=10,
            )
            degisen = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
            return {
                "clean": len(degisen) == 0,
                "degisen_dosyalar": degisen[:20],
            }
        except Exception as e:
            return {"error": str(e)}
