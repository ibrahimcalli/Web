"""PDF broşür üretimi — repository üzerinden veri alır."""
from __future__ import annotations

from io import BytesIO
from typing import Optional

from backend.core.errors import NotFoundError
from backend.repositories.misc_repository import AyarRepository
from backend.repositories.portfoy_repository import PortfoyRepository


class PdfService:
    def __init__(
        self,
        portfoyler: Optional[PortfoyRepository] = None,
        ayarlar: Optional[AyarRepository] = None,
    ):
        self.portfoyler = portfoyler or PortfoyRepository()
        self.ayarlar = ayarlar or AyarRepository()

    def brosur(self, pid: int) -> bytes:
        p = self.portfoyler.get(pid)
        if not p:
            raise NotFoundError("Portföy bulunamadı")
        ay = self.ayarlar.get_all()
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            buf = BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            w, h = A4
            y = h - 50
            c.setFont("Helvetica-Bold", 16)
            c.drawString(40, y, (ay.get("site_adi") or "Portföy Gayrimenkul")[:60])
            y -= 30
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, (p.get("baslik") or "")[:80])
            y -= 24
            c.setFont("Helvetica", 11)
            for line in [
                f"Kategori: {p.get('ana_kategori')} / {p.get('alt_kategori')}",
                f"Konum: {p.get('mahalle') or ''}, {p.get('ilce') or ''}",
                f"Fiyat: {p.get('fiyat') or ''} {p.get('para_birimi') or ''}",
                "",
                (p.get("aciklama") or "")[:500],
            ]:
                c.drawString(40, y, line[:95])
                y -= 16
            c.showPage()
            c.save()
            return buf.getvalue()
        except ImportError:
            text = (
                f"{ay.get('site_adi','Portföy')}\n{p.get('baslik')}\n"
                f"{p.get('fiyat')} {p.get('para_birimi')}\n{p.get('aciklama') or ''}\n"
            ).encode("utf-8")
            return text
