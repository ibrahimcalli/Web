"""
Portföy Gayrimenkul Web Sistemi - Backend (Yeni Mimari)
=========================================================

Repository Pattern + Service Layer + DI
- Repository: SQL işlemleri (PostgreSQL geçişine hazır)
- Service: İş kuralları
- API: Standart response model {success, message, data}

Çalıştırma:
    python app.py

Dokümantasyon:
    http://localhost:8000/docs  (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app import create_app
from backend.core.config import BASE_DIR
from backend.db.schema import init_db

# Uygulama oluştur
app = create_app()

# ─── Statik dosyalar ──────────────────────────────────────────────────────────
app.mount(
    "/src",
    StaticFiles(directory=str(BASE_DIR / "src")),
    name="src_modules",
)
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)


# ─── SPA Fallback (Frontend için) ─────────────────────────────────────────────
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    """
    SPA fallback - frontend route'ları için index.html döndürür.
    API endpoint'leri önce işlenir, sonra buraya düşer.
    """
    index = BASE_DIR / "static" / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"mesaj": "API çalışıyor"}, status_code=200)


# ─── Başlat ────────────────────────────────────────────────────────────────────
init_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
