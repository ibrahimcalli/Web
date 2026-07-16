"""
Sitemap ve robots.txt generator.

Otomatik olarak:
- /sitemap.xml
- /sitemap-images.xml
- /robots.txt

üretir.

Portföyler, blog yazıları eklendikçe güncellenir.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response

from backend.repositories.portfoy_repository import PortfoyRepository
from backend.repositories.misc_repository import BlogRepository

router = APIRouter()

SITE_URL = "https://portfoygayrimenkul.com.tr"


def get_lastmod() -> str:
    """Son güncelleme tarihi (ISO 8601)."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


@router.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml(request: Request):
    """
    Ana sitemap.xml — tüm sayfaların URL'leri.
    
    Format: sitemap index + individual sitemaps
    """
    portfoy_repo = PortfoyRepository()
    blog_repo = BlogRepository()
    
    root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    
    # Ana sayfa
    ET.SubElement(root, "url", loc=SITE_URL + "/")
    ET.SubElement(root, "lastmod").text = get_lastmod()
    ET.SubElement(root, "changefreq").text = "daily"
    ET.SubElement(root, "priority").text = "1.0"
    
    # İlanlar, Blog, Hakkımızda vb. statik sayfalar
    static_pages = [
        ("ilanlar", "daily", "0.8"),
        ("blog", "weekly", "0.7"),
    ]
    for page, freq, prio in static_pages:
        url = ET.SubElement(root, "url", loc=SITE_URL + "/#"+page)
        ET.SubElement(url, "changefreq").text = freq
        ET.SubElement(url, "priority").text = prio
    
    # Portföy detay sayfaları
    portfoyler_list = portfoy_repo.list_aktif_sitemap()
    for p in portfoyler_list:
        url = ET.SubElement(root, "url", loc=SITE_URL + "/#detay/"+str(p["id"]))
        ET.SubElement(url, "lastmod").text = p.get("guncelleme", get_lastmod())
        ET.SubElement(url, "changefreq").text = "weekly"
        ET.SubElement(url, "priority").text = "0.9"
    
    # Blog detay sayfaları
    blog_list = blog_repo.list_published_sitemap()
    for b in blog_list:
        slug = b.get("slug") or str(b.get("id", ""))
        url = ET.SubElement(root, "url", loc=SITE_URL + "/#blog-detay/"+slug)
        ET.SubElement(url, "lastmod").text = b.get("guncelleme", get_lastmod())
        ET.SubElement(url, "changefreq").text = "monthly"
        ET.SubElement(url, "priority").text = "0.8"
    
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
    
    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={"Cache-Control": "public, max-age=3600"}
    )


@router.get("/sitemap-images.xml", include_in_schema=False)
async def sitemap_images_xml(request: Request):
    """
    Resim sitemap — tüm portföy resimlerini listeler.
    
    Google Image Search için optimize.
    """
    portfoy_repo = PortfoyRepository()
    
    root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    ET.SubElement(root, "ns:image", xmlns="http://www.google.com/schemas/sitemap-image/1.1")
    
    portfoyler_list = portfoy_repo.list_aktif_sitemap()
    for p in portfoyler_list:
        url = ET.SubElement(root, "url", loc=SITE_URL + "/#detay/"+str(p["id"]))
        ET.SubElement(url, "lastmod").text = p.get("guncelleme", get_lastmod())
        ET.SubElement(url, "changefreq").text = "weekly"
        ET.SubElement(url, "priority").text = "0.9"
        
        # Resimler (ilk 10 resim)
        # Not: Resim URL'leri frontend'den alınmalı, burada placeholder
        for i in range(min(10, 0)):  # Resim yoksa boş (gerçek implementasyonda resim listesi çekilir)
            img = ET.SubElement(url, "image:image", xmlns="http://www.google.com/schemas/sitemap-image/1.1")
            ET.SubElement(img, "image:loc").text = SITE_URL + "/static/uploads/portfoyler/placeholder.jpg"
            ET.SubElement(img, "image:title").text = f"Portföy {p['id']} resmi {i+1}"
            ET.SubElement(img, "image:caption").text = f"Fethiye gayrimenkul {p['id']}"
    
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
    
    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={"Cache-Control": "public, max-age=86400"}
    )


@router.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    """
    robots.txt — arama motorları için yönlendirme.
    
    Production'da tüm botlara izin, admin sayfalarını engelle.
    """
    robots = f"""# Portföy Gayrimenkul robots.txt
# Üretim sunucusu — {SITE_URL}

User-agent: *
Allow: /
Disallow: /api/
Disallow: /#admin
Disallow: /#giris

# Sitemap
Sitemap: {SITE_URL}/sitemap.xml
Sitemap: {SITE_URL}/sitemap-images.xml

# Crawl-delay (opsiyonel, bazı botlar için)
Crawl-delay: 1

# Google Bot özel
User-agent: Googlebot
Allow: /
Disallow: /api/
Disallow: /#admin

# Bing Bot özel
User-agent: Bingbot
Allow: /
Disallow: /api/
Disallow: /#admin
"""
    return PlainTextResponse(
        content=robots,
        media_type="text/plain",
        headers={"Cache-Control": "public, max-age=86400"}
    )