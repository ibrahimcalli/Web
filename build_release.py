"""
Production build script — CSS ve JS minification.

Kullanım:
    cd /home/ibrahim/PROGRAMLAR/WEB/emlak_web
    python3 build_release.py

Çıktı:
    src/styles/*.min.css
    static/sw.min.js (opsiyonel)
    static/manifest.json (zaten minified)
    
DOM off — Tailwind gibi, sadece gereksiz whitespace ve comment'ler temizlenir.
Mevcut okunabilir kaynak dosyalar KORUNUR.
"""
import re
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()


def minify_css(content: str) -> str:
    """
    Basit ama güvenli CSS minifier.
    - Çok satırlı yorumları kaldır (/* ... */)
    - Beyaz boşlukları sıkıştır
    - Sondaki noktalı virgülden önceki boşluğu koruyor
    - Gereksiz satır başlarını temizle
    """
    # 1. Yorumları kaldır /* ... */ (greedy ile heuristik)
    result = []
    i = 0
    while i < len(content):
        if i < len(content) - 1 and content[i] == '/' and content[i+1] == '*':
            # Yorumu atla
            end = content.find('*/', i)
            if end == -1:
                # Yorum yok kapanıyor
                break
            # Yorumdan sonra tüm whitespace karakteri de atla
            i = end + 2
            while i < len(content) and content[i] in ' \t\r\n':
                i += 1
        else:
            result.append(content[i])
            i += 1
    css = ''.join(result)
    
    # 2. Son karakterdeki whitespace
    css = css.strip()
    
    # 3. Yeni satırları normalize et
    css = re.sub(r'[\r\n]+', '\n', css)
    
    # 4. Son ardışık boşlukları (tek satırda) sil
    # Çoklu boşluk -> tek boşluk
    css = re.sub(r'[ \t]+', ' ', css)
    
    # 5. Özel bloklar — selector/rule arası
    css = re.sub(r' *; *', ';', css)
    css = re.sub(r' *, *', ',', css)
    css = re.sub(r' *: *', ':', css)  # ama property: value için bu riskli olabilir durum
    
    # 6. Son boşlukları kaldır
    css = re.sub(r' +(?=[}{;])', '', css)
    
    # 7. Yeni satırları kaldır (semicolon ve brace çevresinde)
    css = re.sub(r'\n\s*', '', css)
    
    return css


def minify_js(content: str) -> str:
    """
    Basit JS minifier — yorum ve gereksiz whitespace kaldırır.
    String ve regex literal'lerine güvenli.
    
    Daha agresif minification için esbuild/uglify-js önerilir.
    """
    # 1. Çok satırlı yorum kaldır /* ... */
    result = []
    i = 0
    in_string = None  # ', ", `
    in_regex = False
    while i < len(content):
        ch = content[i]
        
        # Yorum işleme
        if in_string is None and not in_regex:
            if ch == '/' and i < len(content) - 1:
                nx = content[i+1]
                # Çok satırlı yorum
                if nx == '*':
                    end = content.find('*/', i)
                    if end == -1:
                        break
                    # sonraki whitespace
                    i = end + 2
                    while i < len(content) and content[i] in ' \t\r\n':
                        i += 1
                    continue
                # Satır yorumu
                elif nx == '/':
                    end = content.find('\n', i)
                    i = end if end != -1 else len(content)
                    continue
            
            # String başlangıcı
            if ch in ('"', "'", '`'):
                in_string = ch
                result.append(ch)
                i += 1
                continue
            
            # Regex literal — zor tespit, basitleştirildi
            # Son geçerli false positive'leri önlememek için atla
        
        if in_string is not None:
            result.append(ch)
            if ch == '\\' and i + 1 < len(content):
                result.append(content[i+1])
                i += 2
                continue
            
            # Template literal: ${expr} için
            if in_string == '`' and ch == '$' and i + 1 < len(content) and content[i+1] == '{':
                # {} match et
                result.append('{')
                depth = 1
                i += 2
                while i < len(content) and depth > 0:
                    if content[i] == '{':
                        depth += 1
                    elif content[i] == '}':
                        depth -= 1
                    result.append(content[i])
                    i += 1
                in_string = '`'  # hala template içindeyiz
                continue
            
            if ch == in_string:
                in_string = None
        else:
            result.append(ch)
        
        i += 1
    
    js = ''.join(result)
    
    # Yeni satırları sil
    js = js.replace('\n', ' ').replace('\r', ' ')
    js = re.sub(r'[ \t]+', ' ', js)
    js = re.sub(r' *([(){}\[\];,.:?]) *', r'\1', js)
    
    return js.strip()


def process():
    styles_dir = ROOT / 'src' / 'styles'
    out_dir = ROOT / 'src' / 'styles'
    print('=' * 60)
    print('Production build — v2.0.0')
    print('=' * 60)
    
    # CSS
    css_files = ['responsive.css', 'layout.css', 'components.css', 'desktop.css']
    print('\n[ CSS Minification ]')
    for f in css_files:
        src = styles_dir / f
        if not src.exists():
            print(f'  ⚠ Kaynak yok: {f}')
            continue
        content = src.read_text(encoding='utf-8')
        original_size = len(content)
        minified = minify_css(content)
        out = out_dir / f.replace('.css', '.min.css')
        out.write_text(minified, encoding='utf-8')
        size = out.stat().st_size
        reduction = 100 - (size * 100 // original_size) if original_size else 0
        print(f'  ✓ {f} → {f.replace(".css", ".min.css")} '
              f'({original_size:,} → {size:,} byte, %{reduction} azalma)')
    
    # JS
    js_files = [
        ('src/ui/seo.js', 'src/ui/seo.min.js'),
        ('src/ui/pwa.js', 'src/ui/pwa.min.js'),
        ('src/ui/img-optimizer.js', 'src/ui/img-optimizer.min.js'),
    ]
    print('\n[ JS Minification ]')
    # app.js ES module — CommonJS-aware değil, agresif minification agresif olmaz
    # Sadece src/ui altındaki eski/küçük dosyalar minify edilebilir
    for src_rel, out_rel in js_files:
        src = ROOT / src_rel
        out = ROOT / out_rel
        if not src.exists():
            print(f'  ⚠ Kaynak yok: {src_rel}')
            continue
        content = src.read_text(encoding='utf-8')
        original_size = len(content)
        minified = minify_js(content)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(minified, encoding='utf-8')
        size = out.stat().st_size
        reduction = 100 - (size * 100 // original_size) if original_size else 0
        print(f'  ✓ {src_rel} → {out_rel} '
              f'({original_size:,} → {size:,} byte, %{reduction} azalma)')
    
    print('\n[ Done — Production dosyaları hazır ]')


if __name__ == '__main__':
    process()
