"""Ortak dosya yükleme iş kuralları (tekrarları tek yerde)."""
from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Optional, Tuple

from backend.core.config import UPLOAD_DIR
from backend.core.errors import AppError

try:
    from PIL import Image, ImageOps

    PIL_OK = True
except ImportError:
    PIL_OK = False


def _magic_ok(icerik: bytes) -> bool:
    jpeg_ok = len(icerik) >= 3 and icerik[0] == 0xFF and icerik[1] == 0xD8 and icerik[2] == 0xFF
    png_ok = len(icerik) >= 4 and icerik[:4] == bytes([0x89, 0x50, 0x4E, 0x47])
    webp_ok = len(icerik) >= 12 and icerik[:4] == b"RIFF" and icerik[8:12] == b"WEBP"
    return jpeg_ok or png_ok or webp_ok


class UploadService:
    """Resim doğrulama + kaydetme. Endpoint'ler yalnızca bu servisi çağırır."""

    def kaydet_ham(
        self,
        icerik: bytes,
        *,
        prefix: str,
        max_mb: float = 10,
        uzanti: str = ".webp",
        as_webp: bool = False,
        max_width: Optional[int] = None,
        square: Optional[int] = None,
    ) -> str:
        if len(icerik) > int(max_mb * 1024 * 1024):
            raise AppError(f"Dosya {max_mb}MB'dan küçük olmalı", 400)
        if not _magic_ok(icerik):
            raise AppError("Geçersiz resim dosyası", 400)

        ad = f"{prefix}_{uuid.uuid4().hex[:10]}{'.webp' if as_webp or square else uzanti}"
        hedef = UPLOAD_DIR / ad

        if PIL_OK and (as_webp or square or max_width):
            try:
                img = Image.open(io.BytesIO(icerik))
                img = ImageOps.exif_transpose(img)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                if square:
                    m = min(img.width, img.height)
                    sol = (img.width - m) // 2
                    ust = (img.height - m) // 2
                    img = img.crop((sol, ust, sol + m, ust + m)).resize(
                        (square, square), Image.LANCZOS
                    )
                elif max_width and img.width > max_width:
                    oran = max_width / img.width
                    img = img.resize((max_width, int(img.height * oran)), Image.LANCZOS)
                img.save(hedef, "WEBP", quality=85, method=4)
            except Exception as e:
                raise AppError(f"Resim işlenemedi: {str(e)[:120]}", 400)
        else:
            with open(hedef, "wb") as f:
                f.write(icerik)

        return f"/static/uploads/{ad}"
