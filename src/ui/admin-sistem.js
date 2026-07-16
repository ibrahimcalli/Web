/**
 * Admin Sistem Paneli — Durum, Test, Komutlar, Bakım, AI Tanılama, Kılavuz
 */
async function sistemDurumYukle() {
    const kont = document.getElementById('admin-ic');
    if (!kont) return;
    kont.innerHTML = '<div class="yukleniyor"><div class="spinner"></div>Yükleniyor…</div>';
    try {
        const r = await fetch('/api/sistem/durum', { headers: { Authorization: 'Bearer ' + (localStorage.getItem('token') || '') } });
        const data = await r.json();
        if (!data.success) { kont.innerHTML = '<div class="hata">' + (data.message || 'Hata') + '</div>'; return; }
        const d = data.data;
        let html = '<div class="sistem-durum"><h2 style="margin-bottom:1rem">📊 Sistem Durumu</h2><div class="durum-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem">';
        html += '<div class="durum-kart"><div class="durum-kart-baslik">Servisler</div><table class="tablo"><tbody>';
        for (const [k, v] of Object.entries(d.servis || {})) {
            html += `<tr><td data-label="Servis">${k}</td><td data-label="Durum"><span class="durum-${v === 'active' || v === 'açık' ? 'yesil' : 'kirmizi'}">${v}</span></td></tr>`;
        }
        html += '</tbody></table></div>';
        html += '<div class="durum-kart"><div class="durum-kart-baslik">Sistem</div><table class="tablo"><tbody>';
        for (const [k, v] of Object.entries(d.sistem || {})) {
            html += `<tr><td data-label="Özellik">${k}</td><td data-label="Değer">${v || '-'}</td></tr>`;
        }
        html += '</tbody></table></div>';
        html += '</div><div style="margin-top:0.5rem;font-size:0.78rem;color:var(--gri-metin)">Son güncelleme: ' + (d.zaman || '-') + '</div></div>';
        kont.innerHTML = html;
    } catch (e) { kont.innerHTML = '<div class="hata">Bağlantı hatası: ' + e.message + '</div>'; }
}

async function sistemLogYukle(tip = 'app') {
    const kont = document.getElementById('admin-ic');
    if (!kont) return;
    kont.innerHTML = '<div class="yukleniyor"><div class="spinner"></div>Yükleniyor…</div>';
    try {
        const r = await fetch(`/api/sistem/log/${tip}?satir=200`, { headers: { Authorization: 'Bearer ' + (localStorage.getItem('token') || '') } });
        const data = await r.json();
        if (!data.success) { kont.innerHTML = '<div class="hata">' + (data.message || 'Hata') + '</div>'; return; }
        const icerik = data.data.icerik || '(boş)';
        const secim = ['app', 'error', 'access', 'deploy'].map(t => `<button class="btn btn-sm ${tip === t ? 'btn-kirm' : 'btn-ntr'}" onclick="sistemLogYukle('${t}')">${t}.log</button>`).join(' ');
        kont.innerHTML = `<div style="margin-bottom:1rem"><h2 style="margin-bottom:0.5rem">📋 Log Görüntüle</h2><div style="display:flex;gap:0.4rem;flex-wrap:wrap">${secim}</div></div><pre style="background:#1a1a2e;color:#e0e0e0;padding:1rem;border-radius:6px;font-size:0.78rem;overflow:auto;max-height:70vh;white-space:pre-wrap;word-break:break-all">${escHtml(icerik)}</pre>`;
    } catch (e) { kont.innerHTML = '<div class="hata">Bağlantı hatası: ' + e.message + '</div>'; }
}

async function sistemKomutlar() {
    const kont = document.getElementById('admin-ic');
    if (!kont) return;
    kont.innerHTML = '<div class="yukleniyor"><div class="spinner"></div>Yükleniyor…</div>';
    try {
        const r = await fetch('/api/sistem/komutlar', { headers: { Authorization: 'Bearer ' + (localStorage.getItem('token') || '') } });
        const data = await r.json();
        if (!data.success) { kont.innerHTML = '<div class="hata">' + (data.message || 'Hata') + '</div>'; return; }
        let html = '<h2 style="margin-bottom:1rem">📝 Komutlar</h2><div style="font-size:0.85rem;color:var(--gri-metin);margin-bottom:1rem">Sık kullanılan komutlar — yanındaki 📋 butonu ile panoya kopyalayın.</div>';
        for (const grup of (data.data.gruplar || [])) {
            html += `<div class="komut-grup" style="margin-bottom:1.5rem"><h3 style="font-size:0.95rem;margin-bottom:0.5rem;color:var(--kiremit)">${grup.grup}</h3><div style="display:flex;flex-direction:column;gap:0.4rem">`;
            for (const cmd of (grup.komutlar || [])) {
                html += `<div class="komut-satir" style="display:flex;align-items:center;gap:0.5rem;background:var(--krem);padding:0.5rem 0.75rem;border-radius:6px;border:1px solid var(--kumtasi)">
                    <span style="flex:1;font-size:0.82rem">${cmd.aciklama}</span>
                    <code style="font-size:0.75rem;background:rgba(0,0,0,0.06);padding:0.2rem 0.5rem;border-radius:4px;flex:2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escHtml(cmd.komut)}</code>
                    <button class="btn btn-sm btn-ntr" onclick="navigator.clipboard.writeText('${escHtml(cmd.komut).replace(/'/g, "\\'")}');this.textContent='✓';setTimeout(()=>this.textContent='📋',1500)">📋</button>
                </div>`;
            }
            html += '</div></div>';
        }
        kont.innerHTML = html;
    } catch (e) { kont.innerHTML = '<div class="hata">Bağlantı hatası: ' + e.message + '</div>'; }
}

async function sistemTest() {
    const kont = document.getElementById('admin-ic');
    if (!kont) return;
    kont.innerHTML = '<div class="yukleniyor"><div class="spinner"></div>Testler çalıştırılıyor…</div><div style="text-align:center;margin-top:1rem;font-size:0.85rem;color:var(--gri-metin)">Bu işlem 30-60 saniye sürebilir.</div>';
    try {
        const r = await fetch('/api/sistem/test', { method: 'POST', headers: { Authorization: 'Bearer ' + (localStorage.getItem('token') || '') } });
        const data = await r.json();
        if (!data.success) { kont.innerHTML = '<div class="hata">' + (data.message || 'Hata') + '</div>'; return; }
        const d = data.data;
        let html = '<h2 style="margin-bottom:0.5rem">🧪 Test Sonuçları</h2>';
        html += `<div style="margin-bottom:1rem;padding:0.5rem 1rem;border-radius:6px;font-weight:600;display:inline-block;background:${d.success ? 'var(--zeytun-a)' : 'var(--kiremit-a)'};color:${d.success ? 'var(--zeytun)' : 'var(--kiremit-k)'}">${d.summary}</div>`;
        html += `<div style="font-size:0.78rem;color:var(--gri-metin);margin-bottom:1rem">${d.timestamp}</div>`;
        for (const res of (d.results || [])) {
            const ikon = res.durum === 'geçti' ? '✅' : '❌';
            html += `<div class="test-dosya" style="margin-bottom:1rem;background:var(--krem);border-radius:6px;border:1px solid var(--kumtasi);overflow:hidden">
                <div style="padding:0.5rem 0.75rem;font-weight:600;font-size:0.85rem">${ikon} ${res.dosya} — ${res.durum}</div>
                <pre style="font-size:0.72rem;padding:0.5rem 0.75rem;background:#1a1a2e;color:#e0e0e0;overflow:auto;max-height:400px;white-space:pre-wrap;word-break:break-all;margin:0">${escHtml(res.cikti || '(çıktı yok)')}</pre>
            </div>`;
        }
        html += `<div style="margin-top:1rem"><button class="btn btn-ntr btn-sm" onclick="sistemTest()">🔄 Tekrar Çalıştır</button></div>`;
        kont.innerHTML = html;
    } catch (e) { kont.innerHTML = '<div class="hata">Bağlantı hatası: ' + e.message + '</div>'; }
}

async function sistemBakim() {
    const kont = document.getElementById('admin-ic');
    if (!kont) return;
    const token = localStorage.getItem('token') || '';
    try {
        const r = await fetch('/api/sistem/bakim', { headers: { Authorization: 'Bearer ' + token } });
        const data = await r.json();
        if (!data.success) { kont.innerHTML = '<div class="hata">' + (data.message || 'Hata') + '</div>'; return; }
        let html = '<h2 style="margin-bottom:1rem">🔧 Bakım İşlemleri</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem">';
        for (const isl of (data.data.islemler || [])) {
            html += `<div class="bakim-kart" style="background:var(--krem);border-radius:8px;border:1px solid var(--kumtasi);padding:1rem;display:flex;flex-direction:column;gap:0.5rem">
                <div style="font-weight:600;font-size:1rem">${isl.baslik}</div>
                <div style="font-size:0.82rem;color:var(--gri-metin);flex:1">${isl.aciklama}</div>
                <div style="display:flex;align-items:center;gap:0.5rem;margin-top:0.5rem">
                    <span style="font-size:0.7rem;padding:0.15rem 0.5rem;border-radius:12px;background:${isl.risk === 'düşük' ? 'var(--zeytun-a)' : 'var(--kiremit-a)'};color:${isl.risk === 'düşük' ? 'var(--zeytun)' : 'var(--kiremit-k)'}">${isl.risk}</span>
                    <button class="btn btn-kirm btn-sm" onclick="sistemBakimCalistir('${isl.id}')">▶ Çalıştır</button>
                </div>
            </div>`;
        }
        html += '</div><div id="bakim-sonuc" style="margin-top:1rem"></div>';
        kont.innerHTML = html;
    } catch (e) { kont.innerHTML = '<div class="hata">Bağlantı hatası: ' + e.message + '</div>'; }
}

async function sistemBakimCalistir(islem) {
    const sonucDiv = document.getElementById('bakim-sonuc');
    if (!sonucDiv) return;
    sonucDiv.innerHTML = '<div class="yukleniyor"><div class="spinner"></div>Çalıştırılıyor…</div>';
    try {
        const r = await fetch(`/api/sistem/bakim/${islem}`, { method: 'POST', headers: { Authorization: 'Bearer ' + (localStorage.getItem('token') || '') } });
        const data = await r.json();
        if (data.success) {
            sonucDiv.innerHTML = `<div style="padding:0.75rem;border-radius:6px;background:var(--zeytun-a);color:var(--zeytun);font-weight:600">✅ ${data.data.mesaj}</div>`;
        } else {
            sonucDiv.innerHTML = `<div class="hata">${data.message || 'Hata'}</div>`;
        }
    } catch (e) { sonucDiv.innerHTML = '<div class="hata">Bağlantı hatası: ' + e.message + '</div>'; }
}

async function sistemAiTanilama() {
    const kont = document.getElementById('admin-ic');
    if (!kont) return;
    kont.innerHTML = '<div class="yukleniyor"><div class="spinner"></div>Tanı bilgileri toplanıyor…</div>';
    try {
        const r = await fetch('/api/sistem/ai-tanilama', { headers: { Authorization: 'Bearer ' + (localStorage.getItem('token') || '') } });
        const data = await r.json();
        if (!data.success) { kont.innerHTML = '<div class="hata">' + (data.message || 'Hata') + '</div>'; return; }
        const jsonStr = JSON.stringify(data.data, null, 2);
        kont.innerHTML = `<h2 style="margin-bottom:0.5rem">🤖 AI Tanılama</h2>
            <div style="font-size:0.82rem;color:var(--gri-metin);margin-bottom:1rem">Tüm sistem bilgisi tek JSON'da. Kopyalayıp AI'ya yapıştırabilirsiniz.</div>
            <div style="display:flex;gap:0.5rem;margin-bottom:1rem;flex-wrap:wrap">
                <button class="btn btn-kirm btn-sm" onclick="navigator.clipboard.writeText(document.getElementById('ai-json').textContent);this.textContent='✅ Kopyalandı';setTimeout(()=>this.textContent='📋 Panoya Kopyala',2000)">📋 Panoya Kopyala</button>
                <button class="btn btn-ntr btn-sm" onclick="sistemAiTanilamaIndir()">⬇ İndir (JSON)</button>
            </div>
            <pre id="ai-json" style="background:#1a1a2e;color:#e0e0e0;padding:1rem;border-radius:6px;font-size:0.72rem;overflow:auto;max-height:70vh;white-space:pre-wrap;word-break:break-all">${escHtml(jsonStr)}</pre>`;
    } catch (e) { kont.innerHTML = '<div class="hata">Bağlantı hatası: ' + e.message + '</div>'; }
}

function sistemAiTanilamaIndir() {
    const pre = document.getElementById('ai-json');
    if (!pre) return;
    const blob = new Blob([pre.textContent], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'diagnostic_' + new Date().toISOString().slice(0, 19).replace(/[:-]/g, '-') + '.json';
    a.click();
    URL.revokeObjectURL(a.href);
}

async function sistemKilavuz() {
    const kont = document.getElementById('admin-ic');
    if (!kont) return;
    kont.innerHTML = `<h2 style="margin-bottom:1rem">📖 Sistem Kılavuzu</h2>
    <div style="max-width:800px">
        <div class="kilavuz-bolum" style="margin-bottom:2rem">
            <h3 style="color:var(--kiremit);margin-bottom:0.5rem">🚀 Hızlı Deploy</h3>
            <p style="font-size:0.85rem;color:var(--gri-metin);margin-bottom:0.5rem">En son kodu production'a yayınlamak için:</p>
            <div class="komut-satir" style="display:flex;align-items:center;gap:0.5rem;background:var(--krem);padding:0.5rem 0.75rem;border-radius:6px;border:1px solid var(--kumtasi);max-width:500px">
                <code style="font-size:0.78rem;flex:1">git pull && python3 build_release.py && sudo systemctl restart emlak-api</code>
                <button class="btn btn-sm btn-ntr" onclick="navigator.clipboard.writeText('git pull && python3 build_release.py && sudo systemctl restart emlak-api');this.textContent='✓';setTimeout(()=>this.textContent='📋',1500)">📋</button>
            </div>
        </div>

        <div class="kilavuz-bolum" style="margin-bottom:2rem">
            <h3 style="color:var(--kiremit);margin-bottom:0.5rem">📂 Proje Yapısı</h3>
            <ul style="font-size:0.82rem;color:var(--gri-metin);line-height:1.8">
                <li><code>app.py</code> — Ana ASGI uygulaması (SPA fallback + StaticFiles mount)</li>
                <li><code>backend/</code> — FastAPI backend (app, routes, services, repositories)</li>
                <li><code>src/</code> — Frontend (app.js, ui/, styles/)</li>
                <li><code>static/</code> — Statik dosyalar (HTML, PWA assets, uploads)</li>
                <li><code>tests/</code> — Test dosyaları (test_api.py, test_backend.py)</li>
                <li><code>deploy/</code> — Deploy scriptleri (install, update, rollback, backup)</li>
                <li><code>logs/</code> — Log dosyaları (app.log, error.log, access.log, deploy.log)</li>
            </ul>
        </div>

        <div class="kilavuz-bolum" style="margin-bottom:2rem">
            <h3 style="color:var(--kiremit);margin-bottom:0.5rem">🔧 Önemli Komutlar</h3>
            <table class="tablo">
                <thead><tr><th>Amaç</th><th>Komut</th></tr></thead>
                <tbody>
                    <tr><td>Servis durumu</td><td><code>sudo systemctl status emlak-api</code></td></tr>
                    <tr><td>Servis logu (canlı)</td><td><code>journalctl -u emlak-api -f</code></td></tr>
                    <tr><td>Servis restart</td><td><code>sudo systemctl restart emlak-api</code></td></tr>
                    <tr><td>Cloudflare tunnel</td><td><code>sudo systemctl status cloudflared</code></td></tr>
                    <tr><td>Test çalıştır</td><td><code>python3 tests/test_api.py && python3 tests/test_backend.py</code></td></tr>
                    <tr><td>Sağlık kontrolü</td><td><code>curl https://emlakfethiye.com.tr/health</code></td></tr>
                    <tr><td>Minify build</td><td><code>python3 build_release.py</code></td></tr>
                </tbody>
            </table>
        </div>

        <div class="kilavuz-bolum" style="margin-bottom:2rem">
            <h3 style="color:var(--kiremit);margin-bottom:0.5rem">🗄️ Veritabanı</h3>
            <p style="font-size:0.85rem;color:var(--gri-metin)">SQLite kullanılıyor → <code>emlak_web.db</code>. Yedekler <code>backups/</code> klasöründe tutulur. PostgreSQL geçişine hazır altyapı.</p>
        </div>

        <div class="kilavuz-bolum" style="margin-bottom:2rem">
            <h3 style="color:var(--kiremit);margin-bottom:0.5rem">🌐 Mimari</h3>
            <p style="font-size:0.85rem;color:var(--gri-metin);line-height:1.6">
            <strong>GitHub</strong> → Local PC (Linux Mint) → <strong>systemd</strong> (emlak-api) → <strong>Cloudflare Tunnel</strong> → <strong>https://emlakfethiye.com.tr</strong>
            </p>
        </div>

        <div class="kilavuz-bolum" style="margin-bottom:2rem">
            <h3 style="color:var(--kiremit);margin-bottom:0.5rem">🔄 Rollback</h3>
            <p style="font-size:0.85rem;color:var(--gri-metin)">Deploy öncesi otomatik git tag alınır. Geri dönmek için: <code>sudo bash deploy/rollback.sh --latest</code></p>
        </div>
    </div>`;
}

function escHtml(s) {
    if (!s) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// AdminSayfa dispatcher — adminSayfa('sistem-durum') vs.
// app.js adminSayfa() fonksiyonu window.sistemSayfaAc'a delegre eder.
const _sistemSayfalar = {
    'durum': sistemDurumYukle,
    'log': () => sistemLogYukle('app'),
    'test': sistemTest,
    'komutlar': sistemKomutlar,
    'bakim': sistemBakim,
    'ai': sistemAiTanilama,
    'kilavuz': sistemKilavuz,
};

function sistemSayfaAc(alt) {
    const fn = _sistemSayfalar[alt];
    if (fn) { fn(); return true; }
    return false;
}

// app.js (ES module) adminSayfa() bunu window üzerinden çağırır.
// Modül yükleme sırası ne olursa olsun, app.js kendi yüklemesini tamamladığında
// window.sistemSayfaAc tanımlı olsun diye — klasik script olduğu için senkron yüklenir,
// ardından gelen module (app.js) bunu hazır bulur.
window.sistemSayfaAc = sistemSayfaAc;

// Bakım çalıştır + AI tanılama indir + log yeniden yükle — onclick handler'ılar için window'a aç
window.sistemBakimCalistir = sistemBakimCalistir;
window.sistemAiTanilamaIndir = sistemAiTanilamaIndir;
window.sistemLogYukle = sistemLogYukle;
window.sistemTest = sistemTest;
window.sistemBakim = sistemBakim;

console.log('Admin Sistem modülü yüklendi ✅');