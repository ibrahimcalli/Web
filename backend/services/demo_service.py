"""Demo Content Service — Örnek içerik oluşturur."""
from __future__ import annotations

import json
from typing import Optional

from backend.db.database import Database
from backend.repositories.misc_repository import (
    AyarRepository, BannerRepository, BlogRepository,
)
from backend.repositories.menu_repository import MenuRepository, MenuItemRepository
from backend.repositories.page_repository import PageRepository
from backend.repositories.widget_repository import WidgetRepository
from backend.repositories.forum_repository import (
    ForumCategoryRepository, ForumTopicRepository,
    ForumPostRepository, ForumSettingRepository,
)
from backend.repositories.template_repository import TemplateRepository


class DemoService:
    def __init__(self, database: Database) -> None:
        self.db = database

    def _slug(self, text: str) -> str:
        import re
        s = text.lower().replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c")
        s = re.sub(r"[^a-z0-9\s-]", "", s).strip()
        s = re.sub(r"[\s]+", "-", s)
        return s[:80]

    def blog_olustur(self, count: int = 3) -> list[int]:
        blog_repo = BlogRepository(self.db)
        ids = []
        ornekler = [
            ("Sektördeki Son Gelişmeler", "Sektördeki son trendler ve yenilikler hakkında kapsamlı bir değerlendirme."),
            ("Uzman Görüşü: Başarılı Projeler", "Başarılı projelerin ardındaki sırlar ve uzman tavsiyeleri."),
            ("2026 Yılı Trendleri", "Bu yıl sektörü şekillendirecek önemli trendler."),
            ("Sık Yapılan Hatalar", "Yeni başlayanların sık yaptığı hatalar ve çözümleri."),
            ("Başarı Hikayeleri", "Müşterilerimizin başarı hikayeleri ve deneyimleri."),
        ]
        for i in range(min(count, len(ornekler))):
            baslik, ozet = ornekler[i]
            slug = self._slug(baslik)
            data = {
                "baslik": baslik,
                "slug": slug + f"-{i}" if i > 0 else slug,
                "icerik": f"<article><h2>{baslik}</h2><p>{ozet}</p><p>Detaylı içerik burada yer alacak. Bu örnek blog yazısı demo içerik olarak oluşturulmuştur.</p></article>",
                "ozet": ozet,
                "durum": "Yayınla",
                "etiketler": json.dumps(["demo", "blog", slug]),
            }
            try:
                bid = blog_repo.create(data, yazar_id=None)
                ids.append(bid)
            except Exception:
                pass
        return ids

    def banner_olustur(self, count: int = 3) -> list[int]:
        repo = BannerRepository(self.db)
        ids = []
        for i in range(count):
            data = {
                "baslik": f"Demo Banner {i+1}",
                "aciklama": "Profesyonel hizmetlerimizle yanınızdayız.",
                "link_metin": "Detaylı Bilgi",
                "link_url": "/iletisim",
                "konum": "ana_hero_alti",
                "boyut": "genis",
                "aktif": 1,
                "sira": i,
            }
            try:
                bid = repo.create(data)
                ids.append(bid)
            except Exception:
                pass
        return ids

    def forum_olustur(self, kategoriler: list[str]) -> dict:
        kat_repo = ForumCategoryRepository(self.db)
        konu_repo = ForumTopicRepository(self.db)
        post_repo = ForumPostRepository(self.db)
        results = {}
        for kat_adi in kategoriler:
            try:
                kat_id = kat_repo.create({
                    "slug": self._slug(kat_adi),
                    "ad": kat_adi,
                    "aciklama": f"{kat_adi} kategorisi",
                })
                konu_id = konu_repo.create({
                    "category_id": kat_id,
                    "baslik": f"{kat_adi} Hakkında",
                    "slug": self._slug(f"{kat_adi}-hakkinda"),
                    "icerik": f"{kat_adi} ile ilgili tartışma konusu.",
                    "kullanici_ad": "Admin",
                })
                results[kat_adi] = {"id": kat_id, "konular": [konu_id]}
            except Exception:
                pass
        return results

    def portfoy_ornek(self, count: int = 6) -> list[int]:
        ids = []
        for i in range(count):
            data = {
                "baslik": f"Örnek Portföy {i+1}",
                "ana_kategori": "Konut",
                "alt_kategori": "Daire",
                "fiyat": str(1500000 + i * 250000),
                "para_birimi": "TL",
                "aciklama": f"Örnek portföy {i+1} açıklaması.",
                "durum": "Aktif",
                "il": "Muğla",
                "ilce": "Fethiye",
            }
            try:
                conn = self.db.connect()
                c = conn.cursor()
                c.execute(
                    "INSERT INTO portfoyler (baslik,ana_kategori,alt_kategori,fiyat,para_birimi,aciklama,durum,il,ilce) VALUES (?,?,?,?,?,?,?,?,?)",
                    (data["baslik"], data["ana_kategori"], data["alt_kategori"], data["fiyat"], data["para_birimi"], data["aciklama"], data["durum"], data["il"], data["ilce"]),
                )
                conn.commit()
                ids.append(c.lastrowid)
                conn.close()
            except Exception:
                pass
        return ids

    def testimonial_ornek(self, count: int = 3) -> list[dict]:
        isimler = ["Ali Yılmaz", "Ayşe Demir", "Mehmet Kaya"]
        yorumlar = [
            "Çok profesyonel bir ekip. İşlerini titizlikle yapıyorlar.",
            "Memnuniyet odaklı hizmet anlayışlarıyla fark yaratıyorlar.",
            "Güvenilir ve kaliteli hizmet için doğru adres.",
        ]
        return [{"ad": isimler[i], "yorum": yorumlar[i]} for i in range(min(count, len(isimler)))]

    def hepsi(self, demo_secim: dict, sector_preset: dict) -> dict:
        sonuc = {}
        if demo_secim.get("blog"):
            sonuc["blog_ids"] = self.blog_olustur(3)
        if demo_secim.get("banner"):
            sonuc["banner_ids"] = self.banner_olustur(3)
        if demo_secim.get("portfolio"):
            sonuc["portfoy_ids"] = self.portfoy_ornek(6)
        if demo_secim.get("forum"):
            kategoriler = sector_preset.get("forum_categories", [])
            if kategoriler:
                sonuc["forum"] = self.forum_olustur(kategoriler)
        if demo_secim.get("testimonials"):
            sonuc["testimonials"] = self.testimonial_ornek(3)
        if demo_secim.get("services"):
            sonuc["services"] = True
        if demo_secim.get("gallery"):
            sonuc["gallery"] = True
        return sonuc
