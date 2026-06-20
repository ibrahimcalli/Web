# IC Gayrimenkul Web Sistemi

## Kurulum

```bash
cd emlak_web
pip install -r requirements.txt
python app.py
```

Tarayıcı: http://localhost:8000

## Varsayılan Admin Girişi
- Email: admin@icgayrimenkul.com
- Şifre: admin123

## Klasör Yapısı
```
emlak_web/
├── app.py              ← FastAPI backend (tek dosya)
├── emlak_web.db        ← SQLite veritabanı (otomatik oluşur)
├── requirements.txt
├── static/
│   ├── index.html      ← Frontend (tek dosya, tüm özellikler)
│   └── uploads/        ← Yüklenen resimler
```

## Özellikler
- ✅ 7 ana kategori × alt kategoriler × ilan tipleri
- ✅ Dinamik form alanları (kategoriye göre değişir)
- ✅ docx / html belge parser → form otomatik dolduruluyor
- ✅ Resim yükleme (jpg/png/webp)
- ✅ JWT ile admin/kullanıcı girişi
- ✅ Admin: portföy CRUD, durum yönetimi, yayınla
- ✅ Müşteri istek formu
- ✅ Kullanıcı yönetimi
- ✅ Site ayarları (ad, slogan, iletişim, renk teması)
- ✅ GPS konum desteği
