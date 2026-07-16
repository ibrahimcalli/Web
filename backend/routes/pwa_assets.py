"""
Production static assets — manifest.json, sw.js, offline.html.

SPA fallback'in (index.html) bu dosyaları ezmemesi için FastAPI route olarak expose edilmiştir.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

from backend.core.config import BASE_DIR

router = APIRouter()

STATIC_DIR = BASE_DIR / "static"


@router.get("/manifest.json", include_in_schema=False)
async def manifest_json():
    """PWA manifest."""
    path = STATIC_DIR / "manifest.json"
    if path.exists():
        return FileResponse(
            path,
            media_type="application/manifest+json",
            headers={
                "Cache-Control": "public, max-age=86400",
                "Service-Worker-Allowed": "/",
            }
        )
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Manifest not found")


@router.get("/sw.js", include_in_schema=False)
async def service_worker():
    """PWA service worker."""
    path = STATIC_DIR / "sw.js"
    if path.exists():
        return FileResponse(
            path,
            media_type="application/javascript",
            headers={
                "Cache-Control": "public, max-age=3600",
                "Service-Worker-Allowed": "/",
            }
        )
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="SW not found")


@router.get("/offline.html", include_in_schema=False)
async def offline_page():
    """PWA offline fallback page."""
    path = STATIC_DIR / "offline.html"
    if path.exists():
        return FileResponse(
            path,
            media_type="text/html; charset=utf-8",
            headers={"Cache-Control": "public, max-age=3600"}
        )
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Offline page not found")