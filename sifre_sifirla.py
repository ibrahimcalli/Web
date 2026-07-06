#!/usr/bin/env python3
"""
Portföy Gayrimenkul — Acil Şifre Sıfırlama
Kullanım: python sifre_sifirla.py
"""
import sqlite3, sys, os, getpass
from pathlib import Path

DB = Path(__file__).parent / "emlak_web.db"

try:
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
except ImportError:
    print("❌ passlib kurulu değil: pip install passlib[bcrypt]")
    sys.exit(1)

if not DB.exists():
    print(f"❌ Veritabanı bulunamadı: {DB}")
    sys.exit(1)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
kullanicilar = conn.execute(
    "SELECT id, ad_soyad, email, rol FROM kullanicilar WHERE aktif=1 ORDER BY id"
).fetchall()

if not kullanicilar:
    print("❌ Aktif kullanıcı bulunamadı.")
    conn.close()
    sys.exit(1)

print("\n=== Portföy Gayrimenkul — Şifre Sıfırlama ===\n")
print("Mevcut kullanıcılar:")
for k in kullanicilar:
    print(f"  [{k['id']}] {k['ad_soyad']} <{k['email']}> ({k['rol']})")

print()
secim = input("Sıfırlanacak kullanıcı ID (Enter = 1. admin): ").strip()
if not secim:
    hedef = kullanicilar[0]
else:
    hedef = next((k for k in kullanicilar if str(k["id"]) == secim), None)
    if not hedef:
        print("❌ Geçersiz ID")
        conn.close()
        sys.exit(1)

print(f"\nSeçilen: {hedef['ad_soyad']} <{hedef['email']}>")

while True:
    yeni = getpass.getpass("Yeni şifre (gizli): ")
    if len(yeni) < 6:
        print("⚠  En az 6 karakter olmalı, tekrar deneyin.")
        continue
    tekrar = getpass.getpass("Yeni şifre (tekrar): ")
    if yeni != tekrar:
        print("⚠  Şifreler eşleşmiyor, tekrar deneyin.")
        continue
    break

hash_sifre = pwd.hash(yeni)
conn.execute(
    "UPDATE kullanicilar SET sifre=? WHERE id=?",
    (hash_sifre, hedef["id"])
)
conn.commit()
conn.close()

print(f"\n✅ Şifre güncellendi: {hedef['email']}")
print("   Şimdi web arayüzünden giriş yapabilirsiniz.\n")
