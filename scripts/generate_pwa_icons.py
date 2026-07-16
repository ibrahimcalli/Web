"""
PWA ikonları ve ekran görüntüleri üretici.

static/img/logo.png (1024x1024) kaynağından:
    - 72, 96, 128, 144, 152, 192, 384, 512 px kare ikonlar
    - Şeffaf arka planlı "any" ve "maskable" amaçlı ikonlar
    - Apple touch icon (180x180)
    - Favicon çeşitleri (16, 32, 96)
    - OG image (1200x630)

Çalıştırma:
    venv/bin/python scripts/generate_pwa_icons.py

Not: Mevcut static/img/logo.png üzerine yazmaz.
"""
from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

# Renkler — brand ile uyumlu
THEME_COLOR = (196, 92, 53)        # #C45C35 — kiremit
BG_COLOR = (250, 247, 242)        # #FAF7F2 — krem
MASKABLE_BG = (196, 92, 53)       # maskable için theme_color dolgu

BASE = Path(__file__).resolve().parent.parent
IMG_DIR = BASE / "static" / "img"
LOGO_SRC = IMG_DIR / "logo.png"

# Üretilecek kare icon boyutları (manifest'te referans verilenler)
SQUARE_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

# Apple touch iconları
APPLE_SIZES = [60, 76, 120, 152, 167, 180]

# Favicon
FAVICON_SIZES = [16, 32, 96]


def resize_logo(src: Image.Image, px: int) -> Image.Image:
    """Logo'yu px x px boyutunaşgetir (aspect preserve, ortalanmış)."""
    src = src.convert("RGBA")
    # Logo px^2'de %85 kaplayacak (padding bırak)
    inner = int(px * 0.78)
    resized = src.resize((inner, inner), Image.LANCZOS)
    return resized


def make_any_icon(logo_src: Image.Image, px: int) -> Image.Image:
    """Şeffaf arka planlı ikon (purpose=any)."""
    canvas = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    logo = resize_logo(logo_src, px)
    offset = ((px - logo.width) // 2, (px - logo.height) // 2)
    canvas.paste(logo, offset, logo)
    return canvas


def make_maskable_icon(logo_src: Image.Image, px: int) -> Image.Image:
    """
    Maskable ikon — dolgulu arka plan (safe zone için).
    Android adaptive icon'da köşeler kırpılır, bu yüzden %80 safe zone.
    """
    canvas = Image.new("RGBA", (px, px), MASKABLE_BG + (255,))
    # Dalga yumuşatma — gradient yerine basit dolgu
    logo = resize_logo(logo_src, int(px * 0.62))  # maskable daha küçük logo
    offset = ((px - logo.width) // 2, (px - logo.height) // 2)
    canvas.paste(logo, offset, logo)
    return canvas


def make_apple_touch_icon(logo_src: Image.Image, px: int) -> Image.Image:
    """Apple touch icon — RGB (şeffaflık yok), krem arkaplan."""
    canvas = Image.new("RGB", (px, px), BG_COLOR)
    logo_rgba = resize_logo(logo_src, px)
    # RGBA→RGB composite (BG üzerine)
    bg = Image.new("RGB", (px, px), BG_COLOR)
    bg.paste(logo_rgba, ((px - logo_rgba.width) // 2, (px - logo_rgba.height) // 2), logo_rgba)
    return bg


def make_favicon(logo_src: Image.Image, px: int) -> Image.Image:
    """Favicon — şeffaf arka planRGBA küçük ikon."""
    return make_any_icon(logo_src, px)


def make_og_image(logo_src: Image.Image) -> Image.Image:
    """
    Open Graph image — 1200x630 (WhatsApp/Facebook/Twitter paylaşımı için).
    Sol tarafta logo + sağda brand alanı.
    """
    canvas = Image.new("RGB", (1200, 630), BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    # Sol panel — THEME_COLOR dolgu (yatay %40)
    draw.rectangle([(0, 0), (480, 630)], fill=THEME_COLOR)
    # Logo merkez (sol panelde)
    logo = resize_logo(logo_src, 380)
    canvas.paste(logo, ((480 - logo.width) // 2, (630 - logo.height) // 2), logo)
    # Yatay gradient Mock (sadece solid dolgunun yanında subtle çizgi bırakalım)
    draw.line([(480, 0), (480, 630)], fill=(255, 255, 255), width=2)
    return canvas


def main():
    if not LOGO_SRC.exists():
        print(f"ERROR: {LOGO_SRC} bulunamadı", file=sys.stderr)
        sys.exit(1)

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    logo_src = Image.open(LOGO_SRC).convert("RGBA")
    print(f"Kaynak logo: {logo_src.size} {logo_src.mode}")

    # ─── Kare ikonlar (manifest'ten referans) ────────────────────────
    for px in SQUARE_SIZES:
        # any purpose
        any_icon = make_any_icon(logo_src, px)
        out = IMG_DIR / f"icon-{px}x{px}.png"
        any_icon.save(out, "PNG", optimize=True)
        print(f"  ✅ {out.name} ({any_icon.size})")
        # 512 ve 192 için ayrıca maskable üret
        if px in (192, 512):
            maskable = make_maskable_icon(logo_src, px)
            # manifest'te "any maskable" 512px tek girişte birleşik
            # ama ayrı dosya da tutalım — 512 için ana dosyayı maskable'la değiştir
            if px == 512:
                maskable.save(out, "PNG", optimize=True)
                print(f"     ↳ {out.name} (maskable overwrite)")
            else:
                mout = IMG_DIR / f"icon-{px}x{px}-maskable.png"
                maskable.save(mout, "PNG", optimize=True)
                print(f"  ✅ {mout.name} (maskable)")

    # ─── Apple touch iconlar ────────────────────────────────────────
    for px in APPLE_SIZES:
        icon = make_apple_touch_icon(logo_src, px)
        out = IMG_DIR / f"apple-touch-icon-{px}x{px}.png"
        icon.save(out, "PNG", optimize=True)
        print(f"  ✅ {out.name}")
    # Apple_touch_icon.png (varsayılan 180x180)
    apple_default = make_apple_touch_icon(logo_src, 180)
    apple_default.save(IMG_DIR / "apple-touch-icon.png", "PNG", optimize=True)
    print(f"  ✅ apple-touch-icon.png (180x180)")

    # ─── Apple-touch-icon-precomposed.png ────────────────────────────
    precomposed = make_apple_touch_icon(logo_src, 180)
    precomposed.save(IMG_DIR / "apple-touch-icon-precomposed.png", "PNG", optimize=True)
    print(f"  ✅ apple-touch-icon-precomposed.png")

    # ─── Faviconlar ────────────────────────────────────────────────
    for px in FAVICON_SIZES:
        fav = make_favicon(logo_src, px)
        out = IMG_DIR / f"favicon-{px}x{px}.png"
        fav.save(out, "PNG", optimize=True)
        print(f"  ✅ {out.name}")

    # ─── Multi-resolution favicon.ico (16, 32, 48) ───────────────────
    favicon_ico = Image.open(IMG_DIR / "favicon-32x32.png")
    favicon_ico.save(IMG_DIR.parent / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    print(f"  ✅ favicon.ico (16+32+48 multi-res)")

    # ─── android-chrome (192, 512) ──────────────────────────────────
    for px in (192, 512):
        icon = make_any_icon(logo_src, px)
        out = IMG_DIR / f"android-chrome-{px}x{px}.png"
        icon.save(out, "PNG", optimize=True)
        print(f"  ✅ {out.name}")

    # ─── OG default image ──────────────────────────────────────────
    try:
        og = make_og_image(logo_src)
        og.save(IMG_DIR / "og-default.jpg", "JPEG", quality=92, optimize=True)
        print(f"  ✅ og-default.jpg ({og.size})")
    except Exception as e:
        print(f"  ⚠️  og-default.jpg üretemedik: {e}")

    # ─── mstile-150x150.png (Microsoft tile) ─────────────────────────
    mstile = make_apple_touch_icon(logo_src, 150)
    mstile.save(IMG_DIR / "mstile-150x150.png", "PNG", optimize=True)
    print(f"  ✅ mstile-150x150.png")

    print(f"\n🎉 Tüm ikonlar üretildi: {IMG_DIR}")


if __name__ == "__main__":
    main()
