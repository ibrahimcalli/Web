# Portföy Gayrimenkul Web Sistemi

**portfoygayrimenkul.com.tr**

FastAPI + SQLite backend · Tek dosya HTML/JS frontend · Akdeniz teması

## Kurulum

```bash
cd emlak_web
pip install -r requirements.txt
python app.py
```

Tarayıcı: http://localhost:8000

## Admin Girişi

Admin e-posta ve şifresi **Site Ayarları** üzerinden değiştirilebilir.  
İlk kurulumda varsayılan giriş bilgileri `app.py` içinde `init_db()` fonksiyonunda tanımlıdır.

> ⚠️ Canlı sunucuya geçmeden önce varsayılan şifreyi mutlaka değiştirin.

## Klasör Yapısı

```
emlak_web/
├── app.py              ← FastAPI backend
├── requirements.txt
├── static/
│   ├── index.html      ← Frontend (tek dosya)
│   └── uploads/        ← Yüklenen resimler (git'e girmez)
├── deploy/             ← Sunucu kurulum scriptleri
│   ├── 01_kurulum.sh   ← Ubuntu kurulum
│   ├── 02_ssl.sh       ← Let's Encrypt SSL
│   ├── 03_guncelle.sh  ← Kod güncelleme
│   └── 04_durum.sh     ← Sistem durumu
└── emlak_web.db        ← SQLite veritabanı (git'e girmez)
```

## Özellikler

- 7 ana kategori × alt kategoriler × ilan tipleri
- Dinamik form alanları (kategoriye göre değişir)
- docx / html belge parser → form otomatik dolduruluyor
- Resim yükleme (jpg/png/webp)
- JWT ile admin/kullanıcı girişi
- WhatsApp / Instagram / Facebook entegrasyonu
- Logo yükleme
- Renk teması seçici
- Müşteri istek formu
- Nginx + systemd + SSL kurulum scriptleri

## Sunucu Kurulumu

```bash
sudo bash deploy/01_kurulum.sh   # Python, Nginx, UFW, systemd
sudo bash deploy/02_ssl.sh       # Let's Encrypt SSL
```

## Geliştirme

```bash
git add .
git commit -m "açıklama"
git push
```
