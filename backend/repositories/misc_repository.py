"""İstek, Ayar, Banner, Blog Repository'leri - PostgreSQL uyumlu."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from backend.repositories.base import BaseRepository
from backend.db.database import row_to_dict, rows_to_dicts


def _parse_etiketler(val: Any) -> list:
    """etiketler alanını güvenli şekilde listeye çevirir.

    Veritabanında etiketler geçerli JSON listesi, çift kaçışlı JSON string
    veya None olabilir. Her durumda list döner.
    """
    if val is None or val == "":
        return []
    if isinstance(val, list):
        return val
    try:
        parsed = json.loads(val)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, str):
            # çift kaçışlı durum: json.loads string verdi, tekrar dene
            try:
                inner = json.loads(parsed)
                if isinstance(inner, list):
                    return inner
            except Exception:
                pass
            return [parsed]
        return [str(parsed)]
    except Exception:
        return []


# ─── İstek Repository ─────────────────────────────────────────────────────────
class IstekRepository(BaseRepository):
    """Kullanıcı istekleri CRUD operasyonları."""
    
    def create(self, ad_soyad: str, telefon: str, email: str, mesaj: str, portfoy_id: Optional[int]) -> int:
        """
        Kullanıcı isteği oluştur.
        
        Args:
            ad_soyad: Ad soyad
            telefon: Telefon
            email: E-posta
            mesaj: Mesaj
            portfoy_id: Portföy ID (opsiyonel)
            
        Returns:
            Oluşturulan istek ID
        """
        return self._execute(
            """INSERT INTO kullanici_istekleri (ad_soyad,telefon,email,mesaj,portfoy_id)
               VALUES (?,?,?,?,?)""",
            (ad_soyad, telefon, email, mesaj, portfoy_id),
        )
    
    def list_with_portfoy(self) -> List[dict]:
        """
        İstekleri portföy bilgisiyle getir.
        
        Returns:
            İstek listesi
        """
        rows = self._fetchall(
            """
            SELECT i.*, p.baslik as portfoy_baslik
            FROM kullanici_istekleri i
            LEFT JOIN portfoyler p ON i.portfoy_id=p.id
            ORDER BY i.olusturma DESC
            """
        )
        return rows_to_dicts(rows)
    
    def set_durum(self, iid: int, durum: str) -> None:
        """
        İstek durum güncelle.
        
        Args:
            iid: İstek ID
            durum: Yeni durum
        """
        self._execute("UPDATE kullanici_istekleri SET durum=? WHERE id=?", (durum, iid))
    
    def count_yeni(self) -> int:
        """
        Yeni istek sayısı.
        
        Returns:
            Yeni istek sayısı
        """
        row = self._fetchone(
            "SELECT COUNT(*) AS c FROM kullanici_istekleri WHERE durum='Yeni'"
        )
        return int(row["c"]) if row else 0
    
    def get(self, iid: int) -> Optional[dict]:
        """İstek getir."""
        row = self._fetchone("SELECT * FROM kullanici_istekleri WHERE id=?", (iid,))
        return row_to_dict(row) if row else None
    
    def delete(self, iid: int) -> None:
        """İstek sil."""
        self._execute("DELETE FROM kullanici_istekleri WHERE id=?", (iid,))


# ─── Ayar Repository ──────────────────────────────────────────────────────────
class AyarRepository(BaseRepository):
    """Site ayarları CRUD operasyonları."""
    
    def get_all(self) -> Dict[str, str]:
        """
        Tüm ayarları getir.
        
        Returns:
            Anahtar-değer sözlüğü
        """
        rows = self._fetchall("SELECT * FROM site_ayarlari")
        return {r["anahtar"]: r["deger"] for r in rows}
    
    def get(self, anahtar: str, default: str = "") -> str:
        """
        Tek ayar getir.
        
        Args:
            anahtar: Ayar anahtarı
            default: Varsayılan değer
            
        Returns:
            Ayar değeri
        """
        row = self._fetchone("SELECT deger FROM site_ayarlari WHERE anahtar=?", (anahtar,))
        return row["deger"] if row else default
    
    def set_many(self, ayarlar: Dict[str, Any]) -> None:
        """
        Birden fazla ayar güncelle.
        
        Args:
            ayarlar: Anahtar-değer sözlüğü
        """
        conn = self._connect()
        try:
            for k, v in ayarlar.items():
                conn.execute(
                    "INSERT OR REPLACE INTO site_ayarlari VALUES (?,?)",
                    (k, str(v)),
                )
            conn.commit()
        finally:
            conn.close()
    
    def set(self, anahtar: str, deger: str) -> None:
        """
        Tek ayar güncelle.
        
        Args:
            anahtar: Ayar anahtarı
            deger: Ayar değeri
        """
        self._execute(
            "INSERT OR REPLACE INTO site_ayarlari VALUES (?,?)",
            (anahtar, deger),
        )


# ─── Banner Repository ────────────────────────────────────────────────────────
class BannerRepository(BaseRepository):
    """Banner CRUD operasyonları."""
    
    def list(self, konum: str = "", sadece_aktif: bool = False) -> List[dict]:
        """
        Banner listesi getir.
        
        Args:
            konum: Konum filtresi
            sadece_aktif: Sadece aktif bannerlar
            
        Returns:
            Banner listesi
        """
        q = "SELECT * FROM bannerlar WHERE 1=1"
        args: list = []
        
        if konum:
            q += " AND konum=?"
            args.append(konum)
            
        if sadece_aktif:
            q += " AND aktif=1"
            
        q += " ORDER BY sira, id"
        
        return rows_to_dicts(self._fetchall(q, args))
    
    def get(self, bid: int) -> Optional[dict]:
        """
        Banner getir.
        
        Args:
            bid: Banner ID
            
        Returns:
            Banner dict veya None
        """
        row = self._fetchone("SELECT * FROM bannerlar WHERE id=?", (bid,))
        return row_to_dict(row) if row else None
    
    def create(self, data: dict) -> int:
        """
        Banner oluştur.
        
        Args:
            data: Banner verisi
            
        Returns:
            Oluşturulan banner ID
        """
        return self._execute(
            """INSERT INTO bannerlar
               (baslik, alt_metin, link_url, link_hedef, tip, konum, boyut, sira, aktif)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                data.get("baslik", ""),
                data.get("alt_metin", data.get("aciklama", "")),
                data.get("link_url", ""),
                data.get("link_hedef", "_self"),
                data.get("tip", "slider"),
                data.get("konum", "anasayfa_hero_alti"),
                data.get("boyut", "genis"),
                data.get("sira", 0),
                data.get("aktif", 1),
            ),
        )
    
    def update(self, bid: int, data: dict) -> None:
        """
        Banner güncelle.
        
        Args:
            bid: Banner ID
            data: Yeni veriler
        """
        self._execute(
            """UPDATE bannerlar SET
               baslik=?, alt_metin=?, link_url=?, link_hedef=?,
               tip=?, konum=?, boyut=?, sira=?, aktif=?
               WHERE id=?""",
            (
                data.get("baslik", ""),
                data.get("alt_metin", data.get("aciklama", "")),
                data.get("link_url", ""),
                data.get("link_hedef", "_self"),
                data.get("tip", "slider"),
                data.get("konum", "anasayfa_hero_alti"),
                data.get("boyut", "genis"),
                data.get("sira", 0),
                data.get("aktif", 1),
                bid,
            ),
        )
    
    def set_aktif(self, bid: int, aktif: int) -> None:
        """
        Banner aktif/pasif yap.
        
        Args:
            bid: Banner ID
            aktif: Aktif durumu (0/1)
        """
        self._execute("UPDATE bannerlar SET aktif=? WHERE id=?", (aktif, bid))
    
    def reorder(self, siralar: List[int]) -> None:
        """
        Banner sıralama güncelle.
        
        Args:
            siralar: Banner ID sıralaması
        """
        conn = self._connect()
        try:
            for i, bid in enumerate(siralar):
                conn.execute("UPDATE bannerlar SET sira=? WHERE id=?", (i, bid))
            conn.commit()
        finally:
            conn.close()
    
    def delete(self, bid: int) -> None:
        """
        Banner sil.
        
        Args:
            bid: Banner ID
        """
        self._execute("DELETE FROM bannerlar WHERE id=?", (bid,))
    
    def set_resim(self, bid: int, url: str) -> None:
        """
        Banner resim URL güncelle.
        
        Args:
            bid: Banner ID
            url: Resim URL
        """
        self._execute("UPDATE bannerlar SET resim_url=? WHERE id=?", (url, bid))
    
    def exists(self, bid: int) -> bool:
        """Banner var mı kontrol et."""
        row = self._fetchone("SELECT 1 FROM bannerlar WHERE id=?", (bid,))
        return row is not None


# ─── Blog Repository ──────────────────────────────────────────────────────────
class BlogRepository(BaseRepository):
    """Blog yazıları CRUD operasyonları."""
    
    def list(self, *, is_admin: bool, durum: str = "") -> List[dict]:
        """
        Blog yazıları listesi.
        
        Args:
            is_admin: Admin mi?
            durum: Durum filtresi
            
        Returns:
            Blog yazıları listesi
        """
        q = """
            SELECT b.*, k.ad_soyad as yazar_adi
            FROM blog_yazilari b
            LEFT JOIN kullanicilar k ON b.yazar_id=k.id
            WHERE 1=1
        """
        args: list = []
        
        if not is_admin:
            q += " AND b.durum IN ('Yayında','Aktif')"
        elif durum != "":
            q += " AND b.durum=?"
            args.append(durum)
            
        q += " ORDER BY b.guncelleme DESC"
        
        rows = self._fetchall(q, args)
        result = []
        for r in rows:
            d = dict(r)
            d["etiketler"] = _parse_etiketler(d.get("etiketler"))
            result.append(d)
        return result
    
    def get_by_slug_or_id(self, key: str) -> Optional[dict]:
        """
        Blog yazısı slug veya ID ile getir.
        
        Args:
            key: Slug veya ID
            
        Returns:
            Blog yazısı dict veya None
        """
        if str(key).isdigit():
            row = self._fetchone("SELECT * FROM blog_yazilari WHERE id=?", (int(key),))
        else:
            row = self._fetchone("SELECT * FROM blog_yazilari WHERE slug=?", (key,))
            
        if not row:
            return None
            
        d = dict(row)
        d["etiketler"] = _parse_etiketler(d.get("etiketler"))
        return d
    
    def create(self, data: dict, yazar_id: Optional[int]) -> int:
        """
        Blog yazısı oluştur.
        
        Args:
            data: Blog verisi
            yazar_id: Yazar ID
            
        Returns:
            Oluşturulan blog ID
        """
        return self._execute(
            """INSERT INTO blog_yazilari
               (baslik,slug,icerik,ozet,etiketler,kapak_resim,durum,yazar_id)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                data["baslik"],
                data["slug"],
                data.get("icerik", ""),
                data.get("ozet", ""),
                json.dumps(data.get("etiketler") or [], ensure_ascii=False),
                data.get("kapak_resim", ""),
                data.get("durum", "Taslak"),
                yazar_id,
            ),
        )
    
    def update(self, bid: int, data: dict) -> None:
        """
        Blog yazısı güncelle.
        
        Args:
            bid: Blog ID
            data: Yeni veriler
        """
        self._execute(
            """UPDATE blog_yazilari SET
               baslik=?, icerik=?, ozet=?, etiketler=?, kapak_resim=?, durum=?,
               guncelleme=datetime('now') WHERE id=?""",
            (
                data["baslik"],
                data.get("icerik", ""),
                data.get("ozet", ""),
                json.dumps(data.get("etiketler") or [], ensure_ascii=False),
                data.get("kapak_resim", ""),
                data.get("durum", "Taslak"),
                bid,
            ),
        )
    
    def delete(self, bid: int) -> None:
        """
        Blog yazısı sil.
        
        Args:
            bid: Blog ID
        """
        self._execute("DELETE FROM blog_yazilari WHERE id=?", (bid,))
    
    def set_kapak(self, bid: int, url: str) -> None:
        """
        Blog kapak resmi güncelle.
        
        Args:
            bid: Blog ID
            url: Kapak resmi URL
        """
        self._execute(
            "UPDATE blog_yazilari SET kapak_resim=?, guncelleme=datetime('now') WHERE id=?",
            (url, bid),
        )
    
    def list_published_sitemap(self) -> List[dict]:
        """
        Yayında olan blog yazıları (sitemap için).
        
        Returns:
            Slug ve güncelleme tarihi
        """
        rows = self._fetchall(
            "SELECT slug, guncelleme FROM blog_yazilari WHERE durum IN ('Yayında','Aktif')"
        )
        return rows_to_dicts(rows)
    
    def exists(self, bid: int) -> bool:
        """Blog yazısı var mı kontrol et."""
        row = self._fetchone("SELECT 1 FROM blog_yazilari WHERE id=?", (bid,))
        return row is not None