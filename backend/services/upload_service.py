"""Ortak dosya yükleme iş kuralları (tekrarları tek yerde)."""
from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Optional, Tuple

from backend.core.settings import settings
from backend.core.errors import AppError

try:
    from PIL import Image, ImageOps

    PIL_OK = True
except ImportError:
    PIL_OK = False


# Magic number doğrulama — dosya başlık baytları (kullanıcı adına güvenme)
# image: JPEG, PNG, WEBP
# document: PDF, DOCX (ZIP-based, pk signature)
IMAGE_MAGIC = (
    (b"\xff\xd8\xff", "jpg"),                  # JPEG
    (b"\x89PNG", "png"),                         # PNG
    (b"RIFF", b"WEBP"),                          # WEBP (2 bölüm)
)
DOC_MAGIC = (
    (b"%PDF", "pdf"),                            # PDF
)
# DOCX/XLSX/PPTX = ZIP zip-based, başlangıç "PK\x03\x04"
ZIP_MAGIC = (
    (b"PK\x03\x04", "docx_or_xlsx"),
)


def _magic_ok(icerik: bytes) -> bool:
    """Eski API — sadece resim kontrolü (jpeg/png/webp)."""
    jpeg_ok = len(icerik) >= 3 and icerik[0] == 0xFF and icerik[1] == 0xD8 and icerik[2] == 0xFF
    png_ok = len(icerik) >= 4 and icerik[:4] == bytes([0x89, 0x50, 0x4E, 0x47])
    webp_ok = len(icerik) >= 12 and icerik[:4] == b"RIFF" and icerik[8:12] == b"WEBP"
    return jpeg_ok or png_ok or webp_ok


def _doc_magic_ok(icerik: bytes) -> str | None:
    """
    Doküman magic-number kontrolü —> dosya uzantısı döndürür.
    
    Returns:
        "pdf", "docx" (zip-based) — None değilse.
    """
    if len(icerik) >= 4 and icerik[:4] == b"%PDF":
        return "pdf"
    if len(icerik) >= 4 and icerik[:4] == b"PK\x03\x04":
        # ZIP container — DOCX/XLSX/PPTX
        return "docx"
    return None


def validate_upload_filename(filename: str) -> str:
    """
    Yüklenen dosya adını güvenli hale getir.
    
    - Path traversal engelle (../, ..\\, /)
    - Sadece bilinen uzantıları kabul et
    - Boş/uzun adları reddet
    
    Returns:
        Temizlenmiş dosya adı (uzantı hariç).
    
    Raises:
        AppError: Geçersiz ad veya uzantı
    """
    if not filename or len(filename) > 200:
        raise AppError("Geçersiz dosya adı", 400)
    # Path traversal önlemek için sadece basename
    name = Path(filename).name
    if not name or name in (".", ".."):
        raise AppError("Geçersiz dosya adı", 400)
    # Uzantı kontrolü
    ext = Path(name).suffix.lower().lstrip(".")
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(settings.ALLOWED_UPLOAD_EXTENSIONS)
        raise AppError(f"İzin verilmeyen dosya türü. İzin verilenler: {allowed}", 400)
    # Dosya adındaki tehlikeli karakterleri temizle
    safe = name.replace("..", "").replace("/", "").replace("\\", "")
    return safe


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
        hedef = settings.UPLOAD_DIR / ad

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
    
    def kaydet_dokuman(
        self,
        icerik: bytes,
        *,
        filename: str,
        prefix: str,
        max_mb: Optional[float] = None,
    ) -> str:
        """
        Doküman (PDF/DOCX) yükleme — magic-number + filename validation.
        
        Args:
            icerik: Dosya içeriği (bytes)
            filename: İstemci tarafından verilen orijinal ad
            prefix: Kaydedilecek dosya adı prefix (örn "belge")
            max_mb: MB limiti (None ise settings.MAX_UPLOAD_MB kullanılır)
        
        Returns:
            URL path (örn "/static/uploads/belge_xxxx.pdf")
        
        Raises:
            AppError: Dosya adı geçersiz, boyut limiti, magic number uyuşmazlığı
        """
        # Filename validation
        validate_upload_filename(filename)
        
        # Boyut kontrolü
        limit_mb = max_mb if max_mb is not None else settings.MAX_UPLOAD_MB
        if len(icerik) > int(limit_mb * 1024 * 1024):
            raise AppError(f"Dosya {limit_mb}MB'dan küçük olmalı", 400)
        
        # Magic number kontrolü
        detected = _doc_magic_ok(icerik)
        if not detected:
            raise AppError("Geçersiz doküman dosyası (PDF veya DOCX olmalı)", 400)
        
        # Beklenen uzantı ile detected magic uyuşumu?
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext != detected and not (ext == "xlsx" and detected == "docx"):
            # Eğer kullanıcı .docx yüklemiş ama magic PDF döndüyse — mismatch
            raise AppError(f"Dosya uzantısı ({ext}) ile içerik türü ({detected}) uyuşmuyor", 400)
        
        # Kaydet
        ad = f"{prefix}_{uuid.uuid4().hex[:10]}.{ext}"
        hedef = settings.UPLOAD_DIR / ad
        hedef.parent.mkdir(parents=True, exist_ok=True)
        with open(hedef, "wb") as f:
            f.write(icerik)
        return f"/static/uploads/{ad}"
