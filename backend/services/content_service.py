"""İstek, ayar, banner, blog, meta servisleri."""
from __future__ import annotations

from typing import Optional

from backend.core.errors import NotFoundError
from backend.domain.banners import BANNER_BOYUTLAR, BANNER_KONUMLAR
from backend.domain.catalog import ILAN_TIPLERI, KATEGORILER, alan_sablonu_sec
from backend.domain.slug import slug_olustur
from backend.repositories.kullanici_repository import KullaniciRepository
from backend.repositories.misc_repository import (
    AyarRepository,
    BannerRepository,
    BlogRepository,
    IstekRepository,
)


class IstekService:
    def __init__(self, repo: Optional[IstekRepository] = None):
        self.repo = repo or IstekRepository()

    def gonder(self, data) -> dict:
        self.repo.create(data.ad_soyad, data.telefon, data.email, data.mesaj, data.portfoy_id)
        return {"mesaj": "İsteğiniz alındı, en kısa sürede dönüş yapılacak."}

    def listele(self) -> list:
        return self.repo.list_with_portfoy()

    def durum(self, iid: int, durum: str) -> dict:
        self.repo.set_durum(iid, durum)
        return {"mesaj": "Güncellendi"}


class AyarService:
    def __init__(self, repo: Optional[AyarRepository] = None):
        self.repo = repo or AyarRepository()

    def getir(self) -> dict:
        return self.repo.get_all()

    def kaydet(self, ayarlar: dict) -> dict:
        self.repo.set_many(ayarlar)
        return {"mesaj": "Ayarlar kaydedildi"}

    def ai_kaydet(self, ai_api_key: str, ai_saglayici: str) -> dict:
        self.repo.set("ai_api_key", ai_api_key)
        self.repo.set("ai_saglayici", ai_saglayici)
        return {"mesaj": "AI ayarları kaydedildi"}

    def set_logo(self, url: str) -> dict:
        self.repo.set("logo_url", url)
        return {"mesaj": "Logo yüklendi", "url": url}

    def sil_logo(self) -> dict:
        self.repo.set("logo_url", "")
        return {"mesaj": "Logo silindi"}


class BannerService:
    def __init__(self, repo: Optional[BannerRepository] = None):
        self.repo = repo or BannerRepository()

    def listele(self, konum="", sadece_aktif=False) -> list:
        return self.repo.list(konum=konum, sadece_aktif=sadece_aktif)

    def konumlar(self) -> dict:
        return {"konumlar": BANNER_KONUMLAR, "boyutlar": BANNER_BOYUTLAR}

    def ekle(self, data: dict) -> dict:
        bid = self.repo.create(data if isinstance(data, dict) else data.model_dump())
        return {"id": bid, "mesaj": "Banner oluşturuldu"}

    def guncelle(self, bid: int, data: dict) -> dict:
        if not self.repo.get(bid):
            raise NotFoundError("Banner bulunamadı")
        self.repo.update(bid, data if isinstance(data, dict) else data.model_dump())
        return {"mesaj": "Güncellendi"}

    def aktif(self, bid: int, aktif: int) -> dict:
        self.repo.set_aktif(bid, aktif)
        return {"mesaj": "Durum güncellendi"}

    def sira(self, siralar: list) -> dict:
        self.repo.reorder(siralar)
        return {"mesaj": "Sıra güncellendi"}

    def sil(self, bid: int) -> dict:
        b = self.repo.get(bid)
        self.repo.delete(bid)
        return {"mesaj": "Silindi", "eski_resim": (b or {}).get("resim_url", "")}

    def set_resim(self, bid: int, url: str) -> dict:
        if not self.repo.get(bid):
            raise NotFoundError("Banner bulunamadı")
        self.repo.set_resim(bid, url)
        return {"mesaj": "Yüklendi", "url": url}


class BlogService:
    def __init__(
        self,
        repo: Optional[BlogRepository] = None,
        kullanicilar: Optional[KullaniciRepository] = None,
    ):
        self.repo = repo or BlogRepository()
        self.kullanicilar = kullanicilar or KullaniciRepository()

    def listele(self, payload, durum="") -> list:
        is_admin = bool(payload and payload.get("rol") == "admin")
        return self.repo.list(is_admin=is_admin, durum=durum)

    def detay(self, slug: str) -> dict:
        y = self.repo.get_by_slug_or_id(slug)
        if not y:
            raise NotFoundError("Yazı bulunamadı")
        return y

    def ekle(self, data, payload) -> dict:
        yazar = self.kullanicilar.get_by_email(payload["sub"]) if payload else None
        payload_data = data.model_dump() if hasattr(data, "model_dump") else dict(data)
        payload_data["slug"] = slug_olustur(payload_data["baslik"])
        bid = self.repo.create(payload_data, (yazar or {}).get("id"))
        return {"id": bid, "mesaj": "Oluşturuldu"}

    def guncelle(self, bid: int, data) -> dict:
        if not self.repo.get_by_slug_or_id(str(bid)):
            raise NotFoundError("Yazı bulunamadı")
        payload_data = data.model_dump() if hasattr(data, "model_dump") else dict(data)
        self.repo.update(bid, payload_data)
        return {"mesaj": "Güncellendi", "id": bid}

    def sil(self, bid: int) -> dict:
        self.repo.delete(bid)
        return {"mesaj": "Silindi"}

    def set_kapak(self, bid: int, url: str) -> dict:
        self.repo.set_kapak(bid, url)
        return {"mesaj": "Kapak yüklendi", "url": url}


class MetaService:
    def kategoriler(self) -> dict:
        return {"kategoriler": KATEGORILER, "ilan_tipleri": ILAN_TIPLERI}

    def alanlar(self, ana_kat: str, alt_kat: str, ilan_tipi: str = "") -> list:
        return alan_sablonu_sec(ana_kat, alt_kat, ilan_tipi)
