"""Forum Service — forum iş kuralları."""
from __future__ import annotations

from typing import Dict, List, Optional

from backend.core.errors import AppError, NotFoundError
from backend.repositories.forum_repository import (
    ForumCategoryRepository, ForumPostRepository,
    ForumSettingRepository, ForumTopicRepository,
)
from backend.repositories.kullanici_repository import KullaniciRepository


class ForumService:
    def __init__(
        self,
        kategoriler: Optional[ForumCategoryRepository] = None,
        konular: Optional[ForumTopicRepository] = None,
        yanitlar: Optional[ForumPostRepository] = None,
        ayarlar: Optional[ForumSettingRepository] = None,
        kullanicilar: Optional[KullaniciRepository] = None,
    ):
        self.kategoriler = kategoriler or ForumCategoryRepository()
        self.konular = konular or ForumTopicRepository()
        self.yanitlar = yanitlar or ForumPostRepository()
        self.ayarlar = ayarlar or ForumSettingRepository()
        self.kullanicilar = kullanicilar or KullaniciRepository()

    def _kullanici_bilgisi(self, user_payload: Optional[dict]) -> tuple[Optional[int], str]:
        """JWT payload'ında sadece e-posta (sub) var, id/ad_soyad yok — bu
        ikisini bulmak için veritabanından gerçek kullanıcı kaydı çekilir.
        (Token'daki 'id'/'ad_soyad' alanlarına GÜVENİLMEZ, çünkü login akışı
        bunları hiç koymuyor — auth_service.giris() sadece sub/rol/ad koyar.)"""
        if not user_payload:
            return None, "Misafir"
        email = user_payload.get("sub")
        if not email:
            return None, "Misafir"
        kayit = self.kullanicilar.get_public_by_email(email)
        if not kayit:
            return None, "Misafir"
        return kayit["id"], kayit.get("ad_soyad") or "Kullanıcı"

    # ─── Durum ──────────────────────────────────────────────────────────────
    def forum_aktif_mi(self) -> bool:
        """Forum admin panelden açık mı? (veritabanı üzerinden, restart gerekmez)"""
        ayar = self.ayarlar.get("forum_aktif")
        return bool(ayar and ayar.get("deger") == "1")

    def misafir_yazabilir_mi(self) -> bool:
        ayar = self.ayarlar.get("misafir_yazabilir")
        return bool(ayar and ayar.get("deger") == "1")

    def moderasyon_aktif_mi(self) -> bool:
        ayar = self.ayarlar.get("moderasyon")
        # Varsayılan: moderasyon açık (ayar hiç yoksa güvenli taraf seçilir)
        return not (ayar and ayar.get("deger") == "0")

    def _baslangic_durumu(self) -> str:
        """Moderasyon açıksa yeni içerik onay bekler, kapalıysa direkt yayınlanır."""
        return "beklemede" if self.moderasyon_aktif_mi() else "yayin"

    # ─── Kategoriler ────────────────────────────────────────────────────────
    def kategori_listele(self, aktif_only: bool = False) -> List[dict]:
        return self.kategoriler.get_all(aktif_only=aktif_only)

    def kategori_getir(self, cat_id: int) -> dict:
        c = self.kategoriler.get_by_id(cat_id)
        if not c:
            raise NotFoundError("Kategori bulunamadı")
        return c

    def kategori_olustur(self, data: dict) -> dict:
        slug = (data.get("slug") or "").strip().lower()
        if not slug:
            raise AppError("slug gerekli", 400)
        if self.kategoriler.slug_exists(slug):
            raise AppError("Bu slug zaten kullanımda", 409)
        if not (data.get("ad") or "").strip():
            raise AppError("ad gerekli", 400)
        cid = self.kategoriler.create({**data, "slug": slug})
        return self.kategoriler.get_by_id(cid)

    def kategori_guncelle(self, cat_id: int, data: dict) -> dict:
        if not self.kategoriler.exists(cat_id):
            raise NotFoundError("Kategori bulunamadı")
        self.kategoriler.update(cat_id, data)
        return self.kategoriler.get_by_id(cat_id)

    def kategori_sil(self, cat_id: int) -> dict:
        if not self.kategoriler.exists(cat_id):
            raise NotFoundError("Kategori bulunamadı")
        self.kategoriler.delete(cat_id)
        return {"id": cat_id, "silindi": True}

    # ─── Konular ────────────────────────────────────────────────────────────
    def konu_listele(self, category_id: Optional[int] = None) -> List[dict]:
        if category_id:
            return self.konular.get_by_category(category_id)
        return self.konular.get_all()

    def konu_getir(self, topic_id: int) -> dict:
        t = self.konular.get_by_id(topic_id)
        if not t:
            raise NotFoundError("Konu bulunamadı")
        self.konular.increment_goruntuleme(topic_id)
        return t

    def konu_olustur(self, data: dict) -> dict:
        if not data.get("category_id") or not self.kategoriler.exists(int(data["category_id"])):
            raise NotFoundError("Kategori bulunamadı")
        if not (data.get("baslik") or "").strip():
            raise AppError("baslik gerekli", 400)
        tid = self.konular.create(data)
        return self.konular.get_by_id(tid)

    def konu_olustur_kullanici(self, data: dict, user: Optional[dict]) -> dict:
        """Genel (public) konu oluşturma — kullanici_id/ad İSTEMCİDEN DEĞİL,
        doğrulanmış token'dan (e-posta üzerinden veritabanı sorgusuyla) alınır
        (spoofing engellenir). Misafir yazımı kapalıysa giriş zorunludur
        (router seviyesinde de kontrol edilir)."""
        if not self.forum_aktif_mi():
            raise AppError("Forum şu anda kapalı", 403)
        kullanici_id, kullanici_ad = self._kullanici_bilgisi(user)
        if kullanici_id is None and not self.misafir_yazabilir_mi():
            raise AppError("Konu açmak için giriş yapmalısınız", 401)
        kategori = self.kategoriler.get_by_id(int(data.get("category_id", 0)))
        if not kategori or not kategori.get("aktif"):
            raise NotFoundError("Kategori bulunamadı")
        guvenli = {
            "category_id": data.get("category_id"),
            "baslik": data.get("baslik"),
            "icerik": data.get("icerik", ""),
            "kullanici_id": kullanici_id,
            "kullanici_ad": kullanici_ad,
            "durum": self._baslangic_durumu(),
        }
        return self.konu_olustur(guvenli)

    def konu_guncelle(self, topic_id: int, data: dict) -> dict:
        if not self.konular.exists(topic_id):
            raise NotFoundError("Konu bulunamadı")
        self.konular.update(topic_id, data)
        return self.konular.get_by_id(topic_id)

    def konu_sil(self, topic_id: int) -> dict:
        if not self.konular.exists(topic_id):
            raise NotFoundError("Konu bulunamadı")
        self.konular.delete(topic_id)
        return {"id": topic_id, "silindi": True}

    # ─── Yanıtlar ───────────────────────────────────────────────────────────
    def yanit_listele(self, topic_id: int) -> List[dict]:
        if not self.konular.exists(topic_id):
            raise NotFoundError("Konu bulunamadı")
        return self.yanitlar.get_by_topic(topic_id)

    def yanit_olustur(self, data: dict) -> dict:
        if not data.get("topic_id") or not self.konular.exists(int(data["topic_id"])):
            raise NotFoundError("Konu bulunamadı")
        if not (data.get("icerik") or "").strip():
            raise AppError("icerik gerekli", 400)
        pid = self.yanitlar.create(data)
        return self.yanitlar.get_by_id(pid)

    def yanit_olustur_kullanici(self, data: dict, user: Optional[dict]) -> dict:
        """Genel (public) yanıt oluşturma — kullanici_id/ad token'dan (e-posta
        üzerinden veritabanı sorgusuyla) alınır."""
        if not self.forum_aktif_mi():
            raise AppError("Forum şu anda kapalı", 403)
        kullanici_id, kullanici_ad = self._kullanici_bilgisi(user)
        if kullanici_id is None and not self.misafir_yazabilir_mi():
            raise AppError("Yanıt yazmak için giriş yapmalısınız", 401)
        topic_id = data.get("topic_id")
        if not topic_id or not self.konular.exists(int(topic_id)):
            raise NotFoundError("Konu bulunamadı")
        konu = self.konular.get_by_id(int(topic_id))
        if konu and konu.get("kapali"):
            raise AppError("Bu konu kapatılmış, yanıt yazılamaz", 403)
        guvenli = {
            "topic_id": topic_id,
            "parent_id": data.get("parent_id"),
            "icerik": data.get("icerik", ""),
            "kullanici_id": kullanici_id,
            "kullanici_ad": kullanici_ad,
            "durum": self._baslangic_durumu(),
        }
        return self.yanit_olustur(guvenli)

    def yanit_guncelle(self, post_id: int, data: dict) -> dict:
        if not self.yanitlar.exists(post_id):
            raise NotFoundError("Yanıt bulunamadı")
        self.yanitlar.update(post_id, data)
        return self.yanitlar.get_by_id(post_id)

    def yanit_sil(self, post_id: int) -> dict:
        if not self.yanitlar.exists(post_id):
            raise NotFoundError("Yanıt bulunamadı")
        self.yanitlar.delete(post_id)
        return {"id": post_id, "silindi": True}

    # ─── Ayarlar ────────────────────────────────────────────────────────────
    def ayarlari_getir(self) -> Dict[str, str]:
        return self.ayarlar.get_all()

    def ayar_guncelle(self, anahtar: str, deger: str) -> dict:
        self.ayarlar.set(anahtar, deger)
        return {"anahtar": anahtar, "deger": deger}
