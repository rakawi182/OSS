from flask import Flask, request, jsonify, render_template_string
import os, sys, json, math
from datetime import datetime

# Impor semua modul Anda
from JRC_Ephemeris import (
    JolotundoArchaeoastronomySystem,
    TimeSystem,
    IAU2023UltraPrecision
)
from wuku_system import WukuMechanicalEngine
from Old_Java_Astronomy import (
    display_comprehensive_info,
    parse_time_input,
    NormalizationEngine,
    ΩConstants as OldConstants
)
from SPICA_v18 import ΩSthapatiSystem
from Damais_DB import DAMAIS_INSCRIPTIONS

app = Flask(__name__)

# ============================================================
# INISIALISASI ENGINE (sekali saat startup)
# ============================================================
print("🚀 Starting Jolotundo Complete Web App...")
jrc = JolotundoArchaeoastronomySystem()
wuku = WukuMechanicalEngine()
sthapati = ΩSthapatiSystem(verbose_startup=False)
time_sys = TimeSystem()
old_norm = NormalizationEngine()
const = IAU2023UltraPrecision()

# ============================================================
# HTML TEMPLATE UTAMA (dengan CSS & JavaScript)
# ============================================================
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jolotundo Archaeoastronomy Web</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }
        .container { max-width: 1200px; margin: auto; }
        h1 { text-align: center; color: #f0c27f; }
        .card { background: #16213e; border-radius: 12px; padding: 20px; margin: 20px 0; border: 1px solid #2a3a5e; }
        .form-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: end; }
        .form-group { display: flex; flex-direction: column; margin: 5px 0; }
        .form-group label { font-size: 0.8em; color: #aaa; margin-bottom: 2px; }
        .form-group input, .form-group select { padding: 8px 12px; background: #0f3460; border: 1px solid #2a4a7a; color: #fff; border-radius: 6px; }
        .form-group input:focus { outline: none; border-color: #f0c27f; }
        .btn { background: #f0c27f; color: #1a1a2e; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .btn:hover { background: #f5d08a; }
        .result-area { background: #0a0a1a; padding: 20px; border-radius: 8px; overflow-x: auto; font-family: 'Courier New', monospace; font-size: 0.9em; white-space: pre-wrap; word-wrap: break-word; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th { background: #2a3a5e; text-align: left; padding: 8px; }
        td { padding: 6px 8px; border-bottom: 1px solid #2a3a5e; }
        .badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.7em; }
        .badge-success { background: #2ecc71; color: #000; }
        .badge-warning { background: #f39c12; color: #000; }
        .badge-danger { background: #e74c3c; color: #fff; }
        .tab { overflow: hidden; border-bottom: 1px solid #2a3a5e; margin-bottom: 15px; }
        .tab button { background: #1a1a2e; border: none; color: #aaa; padding: 12px 20px; cursor: pointer; float: left; }
        .tab button.active { color: #f0c27f; border-bottom: 2px solid #f0c27f; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        @media (max-width: 600px) { .form-row { flex-direction: column; } }
    </style>
</head>
<body>
<div class="container">
    <h1>🌞 Jolotundo Archaeoastronomy System</h1>
    <p style="text-align:center;">Akses publik – semua perhitungan di cloud, HP Anda bebas.</p>

    <!-- Tabs -->
    <div class="tab">
        <button class="tablinks active" onclick="openTab(event, 'Astronomi')">Astronomi</button>
        <button class="tablinks" onclick="openTab(event, 'Prasasti')">Prasasti</button>
        <button class="tablinks" onclick="openTab(event, 'Wuku')">Wuku & Wara</button>
        <button class="tablinks" onclick="openTab(event, 'Konversi')">Konversi Waktu</button>
    </div>

    <!-- TAB 1: Astronomi -->
    <div id="Astronomi" class="tab-content active">
        <div class="card">
            <h3>📅 Informasi Lengkap (Matahari, Bulan, Planet, Pancanga, Lagna, Muhurta, Tabeh, Dewata)</h3>
            <div class="form-row">
                <div class="form-group"><label>Tahun</label><input type="number" id="astro_year" value="2024"></div>
                <div class="form-group"><label>Bulan</label><input type="number" id="astro_month" value="12"></div>
                <div class="form-group"><label>Tanggal</label><input type="number" id="astro_day" value="25"></div>
                <div class="form-group"><label>Jam (WIB)</label><input type="text" id="astro_time" value="12:00:00" placeholder="HH:MM:SS atau desimal"></div>
                <div class="form-group"><button class="btn" onclick="getAstronomy()">Hitung</button></div>
            </div>
            <div id="astro_result" class="result-area">Klik "Hitung" untuk menampilkan data astronomi lengkap.</div>
        </div>
    </div>

    <!-- TAB 2: Prasasti -->
    <div id="Prasasti" class="tab-content">
        <div class="card">
            <h3>📜 Konversi Prasasti Saka → Masehi (Ω‑STHAPATI)</h3>
            <div class="form-row">
                <div class="form-group"><label>Tahun Saka</label><input type="number" id="pras_saka" value="851"></div>
                <div class="form-group"><label>Masa (Bulan)</label><input type="text" id="pras_masa" value="Asuji"></div>
                <div class="form-group"><label>Tithi (1-30)</label><input type="number" id="pras_tithi" value="12"></div>
                <div class="form-group"><label>Paksa</label><select id="pras_paksa"><option value="Sukla">Sukla</option><option value="Krsna">Krsna</option></select></div>
                <div class="form-group"><label>Wuku (opsional)</label><input type="text" id="pras_wuku" value="Wugu"></div>
                <div class="form-group"><label>Wara (opsional)</label><input type="text" id="pras_wara" value="Tungleh-Pahing-Sukra"></div>
                <div class="form-group"><label>Nakshatra (opsional)</label><input type="text" id="pras_naks"></div>
                <div class="form-group"><button class="btn" onclick="getPrasasti()">Konversi</button></div>
            </div>
            <div id="pras_result" class="result-area">Masukkan data prasasti dan klik "Konversi".</div>
        </div>
    </div>

    <!-- TAB 3: Wuku -->
    <div id="Wuku" class="tab-content">
        <div class="card">
            <h3>📆 Wuku & Wara 210-hari</h3>
            <div class="form-row">
                <div class="form-group"><label>Tahun</label><input type="number" id="wuku_year" value="2024"></div>
                <div class="form-group"><label>Bulan</label><input type="number" id="wuku_month" value="12"></div>
                <div class="form-group"><label>Tanggal</label><input type="number" id="wuku_day" value="25"></div>
                <div class="form-group"><button class="btn" onclick="getWuku()">Cari</button></div>
            </div>
            <div id="wuku_result" class="result-area">Klik "Cari" untuk info wuku.</div>
        </div>
    </div>

    <!-- TAB 4: Konversi Waktu -->
    <div id="Konversi" class="tab-content">
        <div class="card">
            <h3>🔄 Konversi JD ↔ KA ↔ Tanggal</h3>
            <div class="form-row">
                <div class="form-group"><label>JD UTC</label><input type="text" id="conv_jd" placeholder="2451545.0"></div>
                <div class="form-group"><button class="btn" onclick="convertJD()">JD → Tanggal & KA</button></div>
            </div>
            <div class="form-row">
                <div class="form-group"><label>KA</label><input type="text" id="conv_ka" placeholder="1132592"></div>
                <div class="form-group"><button class="btn" onclick="convertKA()">KA → Tanggal & JD</button></div>
            </div>
            <div class="form-row">
                <div class="form-group"><label>Tanggal (YYYY-MM-DD)</label><input type="text" id="conv_date" placeholder="2024-12-25"></div>
                <div class="form-group"><button class="btn" onclick="convertDate()">Tanggal → JD & KA</button></div>
            </div>
            <div id="conv_result" class="result-area">Hasil konversi akan muncul di sini.</div>
        </div>
    </div>
</div>

<script>
// Fungsi untuk switch tab
function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) tabcontent[i].classList.remove("active");
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) tablinks[i].classList.remove("active");
    document.getElementById(tabName).classList.add("active");
    evt.currentTarget.classList.add("active");
}

// ====================
// ASTRONOMI
// ====================
function getAstronomy() {
    const year = document.getElementById('astro_year').value;
    const month = document.getElementById('astro_month').value;
    const day = document.getElementById('astro_day').value;
    const timeStr = document.getElementById('astro_time').value || '12:00:00';
    const resultDiv = document.getElementById('astro_result');
    resultDiv.innerHTML = '⏳ Menghitung...';
    fetch('/api/astronomy', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ year, month, day, time: timeStr })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            resultDiv.innerHTML = '❌ ' + data.error;
        } else {
            // Tampilkan hasil dengan format monospace
            resultDiv.innerHTML = data.text;
        }
    })
    .catch(err => resultDiv.innerHTML = '❌ Error: ' + err);
}

// ====================
// PRASASTI
// ====================
function getPrasasti() {
    const data = {
        saka_year: document.getElementById('pras_saka').value,
        masa: document.getElementById('pras_masa').value,
        tithi: document.getElementById('pras_tithi').value,
        paksa: document.getElementById('pras_paksa').value,
        wuku: document.getElementById('pras_wuku').value,
        wara_string: document.getElementById('pras_wara').value,
        nakshatra: document.getElementById('pras_naks').value
    };
    const resultDiv = document.getElementById('pras_result');
    resultDiv.innerHTML = '⏳ Mencari...';
    fetch('/api/prasasti', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            resultDiv.innerHTML = '❌ ' + data.error;
        } else {
            let html = '<strong>Hasil Konversi:</strong>\n';
            html += 'Tanggal: ' + data.tanggal + '\n';
            html += 'KA: ' + data.ka + '\n';
            html += 'Wuku: ' + data.wuku + '\n';
            html += 'Skor: ' + data.score + '\n';
            html += 'Confidence: ' + data.confidence + '\n';
            if (data.details) html += 'Detail:\n' + data.details;
            resultDiv.innerHTML = html;
        }
    })
    .catch(err => resultDiv.innerHTML = '❌ Error: ' + err);
}

// ====================
// WUKU
// ====================
function getWuku() {
    const year = document.getElementById('wuku_year').value;
    const month = document.getElementById('wuku_month').value;
    const day = document.getElementById('wuku_day').value;
    const resultDiv = document.getElementById('wuku_result');
    resultDiv.innerHTML = '⏳ Menghitung...';
    fetch('/api/wuku', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ year, month, day })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            resultDiv.innerHTML = '❌ ' + data.error;
        } else {
            let html = '';
            for (let key in data) {
                if (key !== 'status') html += key + ': ' + data[key] + '\n';
            }
            resultDiv.innerHTML = html;
        }
    })
    .catch(err => resultDiv.innerHTML = '❌ Error: ' + err);
}

// ====================
// KONVERSI WAKTU
// ====================
function convertJD() {
    const jd = document.getElementById('conv_jd').value;
    const resultDiv = document.getElementById('conv_result');
    if (!jd) { resultDiv.innerHTML = 'Masukkan JD.'; return; }
    resultDiv.innerHTML = '⏳...';
    fetch('/api/convert', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ type: 'jd', value: jd })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) resultDiv.innerHTML = '❌ ' + data.error;
        else {
            let html = 'Tanggal: ' + data.date + '\nKA: ' + data.ka + '\nWuku: ' + data.wuku;
            resultDiv.innerHTML = html;
        }
    });
}
function convertKA() {
    const ka = document.getElementById('conv_ka').value;
    const resultDiv = document.getElementById('conv_result');
    if (!ka) { resultDiv.innerHTML = 'Masukkan KA.'; return; }
    resultDiv.innerHTML = '⏳...';
    fetch('/api/convert', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ type: 'ka', value: ka })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) resultDiv.innerHTML = '❌ ' + data.error;
        else {
            let html = 'Tanggal: ' + data.date + '\nJD: ' + data.jd + '\nWuku: ' + data.wuku;
            resultDiv.innerHTML = html;
        }
    });
}
function convertDate() {
    const dateStr = document.getElementById('conv_date').value;
    const resultDiv = document.getElementById('conv_result');
    if (!dateStr) { resultDiv.innerHTML = 'Masukkan tanggal (YYYY-MM-DD).'; return; }
    resultDiv.innerHTML = '⏳...';
    fetch('/api/convert', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ type: 'date', value: dateStr })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) resultDiv.innerHTML = '❌ ' + data.error;
        else {
            let html = 'JD: ' + data.jd + '\nKA: ' + data.ka + '\nWuku: ' + data.wuku;
            resultDiv.innerHTML = html;
        }
    });
}
</script>
</body>
</html>
"""

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def home():
    return render_template_string(MAIN_TEMPLATE)

# ============================================================
# API ENDPOINT: ASTRONOMI LENGKAP
# ============================================================
@app.route('/api/astronomy', methods=['POST'])
def api_astronomy():
    data = request.get_json()
    try:
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        time_str = data.get('time', '12:00:00')
        hour = parse_time_input(time_str)  # dari Old_Java_Astronomy

        # Panggil fungsi display_comprehensive_info yang mengembalikan dict
        # Tapi fungsi asli mencetak ke console. Kita modifikasi untuk mengembalikan string.
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            display_comprehensive_info(year, month, day, hour)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        return jsonify({'text': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# API ENDPOINT: PRASASTI
# ============================================================
@app.route('/api/prasasti', methods=['POST'])
def api_prasasti():
    data = request.get_json()
    try:
        # Normalisasi input
        pras_data = {
            'saka_year': int(data.get('saka_year')),
            'masa': data.get('masa'),
            'tithi': int(data.get('tithi', 1)),
            'paksa': data.get('paksa', 'Sukla'),
            'wuku': data.get('wuku'),
            'wara_string': data.get('wara_string'),
            'nakshatra': data.get('nakshatra')
        }
        # Panggil Ω-STHAPATI
        results = sthapati.convert_prasasti_with_smart_parsing(pras_data, verbose=False)
        if results:
            best = results[0]
            cand = best['candidate']
            y, m, d = cand['date']
            return jsonify({
                'status': 'found',
                'tanggal': f"{int(y)}-{int(m):02d}-{int(d):02d}",
                'ka': cand['ka'],
                'wuku': cand['wuku_info']['wuku_name'],
                'score': best['score'],
                'confidence': best['confidence'],
                'details': str(best.get('breakdown', {}))
            })
        else:
            return jsonify({'status': 'not_found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# API ENDPOINT: WUKU
# ============================================================
@app.route('/api/wuku', methods=['POST'])
def api_wuku():
    data = request.get_json()
    try:
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        ka = wuku.date_to_ka(year, month, day)
        info = wuku.get_wuku_by_ka(ka)
        epoch = wuku.get_detailed_wuku_epoch_info(ka)
        return jsonify({
            'status': 'ok',
            'ka': ka,
            'wuku_name': info['wuku_name'],
            'wuku_number': info['wuku_number'],
            'wara_triple': info['wara_triple_full'],
            'day_in_wuku': info['day_in_wuku'],
            'is_tu_pa_a': info['is_tu_pa_a'],
            'days_since_epoch': epoch['days_since_epoch'],
            'cycle_number': epoch['cycle_number'],
            'days_to_next_tu_pa_a': epoch['days_to_next_tu_pa_a']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# API ENDPOINT: KONVERSI WAKTU
# ============================================================
@app.route('/api/convert', methods=['POST'])
def api_convert():
    data = request.get_json()
    try:
        typ = data['type']
        val = data['value']
        if typ == 'jd':
            jd = float(val)
            date_dict = time_sys.jd_to_gregorian(jd)
            ka = wuku.julian_day_to_ka(jd)
            info = wuku.get_wuku_by_ka(ka)
            return jsonify({
                'date': f"{date_dict['year_astronomical']}-{date_dict['month']:02d}-{date_dict['day']:02d}",
                'ka': ka,
                'wuku': info['wuku_name']
            })
        elif typ == 'ka':
            ka = int(val)
            y, m, d = wuku.ka_to_date(ka)
            jd = wuku.ka_to_julian_day(ka)
            info = wuku.get_wuku_by_ka(ka)
            return jsonify({
                'date': f"{y}-{m:02d}-{d:02d}",
                'jd': jd,
                'wuku': info['wuku_name']
            })
        elif typ == 'date':
            parts = val.split('-')
            y, m, d = map(int, parts)
            jd = time_sys.date_to_jd_utc(y, m, d)
            ka = wuku.date_to_ka(y, m, d)
            info = wuku.get_wuku_by_ka(ka)
            return jsonify({
                'jd': jd,
                'ka': ka,
                'wuku': info['wuku_name']
            })
        else:
            return jsonify({'error': 'Unknown type'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# RUN SERVER
# ============================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)