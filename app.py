# ============================================================================
# app.py - OSS ΩLDJAVA-astro Web Application
# Open Source System for Old Javanese Archaeoastronomy
# Streamlit Cloud Deployment Ready
#
# FINAL VERSION - LENGKAP
# - Istilah "Sistem Zodiak" untuk Sayana/Nirayana
# - Referensi Damais (1955) dicantumkan di Beranda, Database, Footer
# - Dukungan tahun negatif (tahun astronomi) di deskripsi dan input
# - Fitur Database Damais & Analisis Sistem Zodiak
# - Plotly fallback (jika tidak terinstall)
# ============================================================================

import sys
import os
import re
import json
import glob
from datetime import datetime, timezone, timedelta
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np

# ============================================================================
# PLOTLY FALLBACK
# ============================================================================
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAVE_PLOTLY = True
except ImportError:
    HAVE_PLOTLY = False
    px = None
    go = None

# ============================================================================
# FUNGSI PEMBERSIH ANSI
# ============================================================================
def clean_ansi(text):
    """Hapus semua escape sequence ANSI dari teks."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="OSS ΩLDJAVA-astro – Open Source Old Javanese Astronomy",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    h1, h2, h3, h4, h5, h6 { color: #f0e6d0 !important; font-family: 'Georgia', serif; }
    h1 { font-size: 2.2rem !important; }
    h2 { font-size: 1.6rem !important; }
    h3 { font-size: 1.2rem !important; }
    .css-1d391kg, .css-12oz5g7 { background-color: #1a1e2a; }
    .jae-card {
        background: linear-gradient(145deg, #1e2230, #151926);
        border-radius: 12px; padding: 18px 20px;
        border: 1px solid #2a3040;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        margin-bottom: 16px;
    }
    .jae-card h3 { color: #d4b896; border-bottom: 1px solid #2a3040; padding-bottom: 8px; margin-bottom: 12px; font-size: 1.1rem; }
    .jae-card p { font-size: 0.9rem; color: #c0c8d8; line-height: 1.6; }
    .metric-box {
        background: #1a1e2a; border-radius: 8px; padding: 10px 14px;
        border-left: 3px solid #d4b896; margin: 4px 0;
    }
    .metric-label { color: #8899bb; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { color: #f0e6d0; font-size: 0.95rem; font-weight: 600; font-family: 'Courier New', monospace; }
    .dataframe { background: #1a1e2a !important; border-radius: 8px !important; border: 1px solid #2a3040 !important; font-size: 0.85rem !important; }
    .dataframe th { background: #252b3d !important; color: #d4b896 !important; font-weight: 600 !important; font-size: 0.85rem !important; }
    .dataframe td { color: #c0c8d8 !important; font-size: 0.85rem !important; }
    .stButton button { background: #2a3040 !important; color: #f0e6d0 !important; border: 1px solid #3a4050 !important; border-radius: 8px !important; font-size: 0.9rem !important; transition: all 0.2s; }
    .stButton button:hover { background: #3a4050 !important; border-color: #d4b896 !important; }
    .streamlit-expanderHeader { background: #1a1e2a !important; color: #d4b896 !important; border-radius: 8px !important; font-size: 0.9rem !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; background: #1a1e2a; border-radius: 8px; padding: 4px; }
    .stTabs [data-baseweb="tab"] { background: transparent; color: #8899bb; border-radius: 6px; padding: 6px 14px; font-size: 0.85rem !important; }
    .stTabs [aria-selected="true"] { background: #2a3040 !important; color: #f0e6d0 !important; }
    .footer { text-align: center; color: #556688; font-size: 0.7rem; padding: 20px 0 10px 0; border-top: 1px solid #1a1e2a; margin-top: 30px; }
    .oss-badge { display: inline-block; background: #2a3040; color: #d4b896; padding: 3px 10px; border-radius: 20px; font-size: 0.65rem; letter-spacing: 1px; border: 1px solid #3a4050; }
    .global-footer { text-align: center; color: #556688; font-size: 0.7rem; padding: 20px 0 10px 0; border-top: 1px solid #1a1e2a; margin-top: 40px; width: 100%; }
    .global-footer a { color: #8899bb; text-decoration: none; }
    .global-footer a:hover { color: #d4b896; text-decoration: underline; }
    .description-box { background: #1a1e2a; border-radius: 12px; padding: 20px 24px; border: 1px solid #2a3040; margin: 16px 0; color: #c0c8d8; font-size: 0.9rem; line-height: 1.7; }
    .description-box b { color: #d4b896; }
    .description-box a { color: #7a9bcb; text-decoration: none; }
    .description-box a:hover { text-decoration: underline; }
    .description-box ul { margin: 8px 0 8px 20px; }
    .description-box li { margin: 4px 0; }
    .input-hint { color: #8899bb; font-size: 0.75rem; font-style: italic; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE
# ============================================================================
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    wib_tz = timezone(timedelta(hours=7))
    now_wib = datetime.now(wib_tz)
    st.session_state.current_year = now_wib.year
    st.session_state.current_month = now_wib.month
    st.session_state.current_day = now_wib.day
    st.session_state.current_hour = now_wib.hour + now_wib.minute / 60.0

# ============================================================================
# CACHE LOADER UNTUK MODUL
# ============================================================================
@st.cache_resource
def load_core_modules():
    from JRC_Ephemeris import (
        IAU2023UltraPrecision,
        TimeSystem as JRC_TimeSystem,
        JolotundoArchaeoastronomySystem as JRC_ArchaeoSystem,
        VSOP87SolarEngine,
        LunarELP82Engine,
        UnifiedCoordinateTransformer,
        JPLStyleTopocentricCorrections
    )
    from wuku_system import (
        WukuMechanicalEngine,
        CalendarConverter,
        offset_solar_days,
        offset_solar_months,
        offset_solar_years,
        offset_lunar_months,
        offset_lunar_years,
        offset_tithi
    )
    from Old_Java_Astronomy import (
        display_comprehensive_info,
        parse_time_input,
        NormalizationEngine as OldJavaNormalizer,
        AstronomicalEngine,
        VedicTimeEngine,
        GrahacaraAsthaEngine,
        DewataMandalaEngine,
        ΩConstants,
        get_saka_cal          
    )
    from SPICA_v18 import ΩSthapatiSystem
    from Damais_DB import DAMAIS_INSCRIPTIONS

    return {
        "jrc_const": IAU2023UltraPrecision(),
        "time_sys": JRC_TimeSystem(),
        "jrc_archaeo": JRC_ArchaeoSystem(),
        "mech_engine": WukuMechanicalEngine(),
        "sthapati": ΩSthapatiSystem(verbose_startup=False),
        "CalendarConverter": CalendarConverter,
        "offset_solar_days": offset_solar_days,
        "offset_solar_months": offset_solar_months,
        "offset_solar_years": offset_solar_years,
        "offset_lunar_months": offset_lunar_months,
        "offset_lunar_years": offset_lunar_years,
        "offset_tithi": offset_tithi,
        "display_comprehensive_info": display_comprehensive_info,
        "parse_time_input": parse_time_input,
        "OldJavaNormalizer": OldJavaNormalizer,
        "AstronomicalEngine": AstronomicalEngine,
        "VedicTimeEngine": VedicTimeEngine,
        "GrahacaraAsthaEngine": GrahacaraAsthaEngine,
        "DewataMandalaEngine": DewataMandalaEngine,
        "ΩConstants": ΩConstants,
        "VSOP87SolarEngine": VSOP87SolarEngine,
        "LunarELP82Engine": LunarELP82Engine,
        "UnifiedCoordinateTransformer": UnifiedCoordinateTransformer,
        "JPLStyleTopocentricCorrections": JPLStyleTopocentricCorrections,
        "DAMAIS_INSCRIPTIONS": DAMAIS_INSCRIPTIONS,
        "get_saka_cal": get_saka_cal   
    }

# ============================================================================
# LOAD MODULES
# ============================================================================
with st.spinner("⏳ Memuat OSS ΩLDJAVA-astro..."):
    mods = load_core_modules()

jrc_const = mods["jrc_const"]
time_sys = mods["time_sys"]
jrc_archaeo = mods["jrc_archaeo"]
mech_engine = mods["mech_engine"]
sthapati = mods["sthapati"]
CC = mods["CalendarConverter"]
display_info = mods["display_comprehensive_info"]
parse_time = mods["parse_time_input"]
OldJavaNormalizer = mods["OldJavaNormalizer"]
AstronomicalEngine = mods["AstronomicalEngine"]
VedicTimeEngine = mods["VedicTimeEngine"]
GrahacaraAsthaEngine = mods["GrahacaraAsthaEngine"]
DewataMandalaEngine = mods["DewataMandalaEngine"]
ΩConst = mods["ΩConstants"]
DAMAIS_INSCRIPTIONS = mods["DAMAIS_INSCRIPTIONS"]
get_saka_cal = mods["get_saka_cal"]

offset_funcs = {
    "solar_days": mods["offset_solar_days"],
    "solar_months": mods["offset_solar_months"],
    "solar_years": mods["offset_solar_years"],
    "lunar_months": mods["offset_lunar_months"],
    "lunar_years": mods["offset_lunar_years"],
    "tithi": mods["offset_tithi"]
}

st.markdown("""
<div style="
    background: linear-gradient(135deg, #1a1e2a, #2a3040);
    border-radius: 12px;
    padding: 16px 24px;
    border-left: 6px solid #d4b896;
    margin: 16px 0 24px 0;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
">
    <span style="font-size: 2rem; line-height: 1;">🔭</span>
    <div>
        <span style="color: #d4b896; font-weight: 600; font-size: 1.15rem; font-family: 'Georgia', serif;">
            Jolotundo Research
        </span>
        <span style="color: #8899bb; font-size: 0.95rem; margin-left: 8px; font-style: italic;">
            — not just observing, but remembering
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# LOAD VALIDATION RESULTS (BATCH FILES)
# ============================================================================
@st.cache_data
def load_validation_results():
    """Gabungkan semua file quick_test_results_batch_*.json menjadi satu DataFrame."""
    try:
        pattern = "quick_test_results_batch_*.json"
        files = sorted(glob.glob(pattern))
        if not files:
            return pd.DataFrame()
        all_data = []
        for f in files:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                if "results" in data:
                    for res in data["results"]:
                        res["batch"] = data.get("batch_number", 0)
                        all_data.append(res)
        df = pd.DataFrame(all_data)
        return df
    except Exception as e:
        st.warning(f"Tidak dapat memuat hasil validasi: {e}")
        return pd.DataFrame()

validation_df = load_validation_results()

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
st.sidebar.image("https://img.icons8.com/fluency/96/000000/sun.png", width=60)
st.sidebar.title("🌙 OSS ΩLDJAVA-astro")
st.sidebar.caption("Open Source Old Javanese Astronomy")
st.sidebar.markdown("---")

nav = st.sidebar.radio(
    "Navigasi",
    [
        "🏠 Beranda",
        "🌞 Real-time",
        "📅 Tanggal Spesifik",
        "📆 Wuku & Wara",
        "📜 Konversi Prasasti",
        "📊 Database Damais",
        "📈 Analisis Sistem Zodiak",
        "🔄 Konversi Waktu",
        "⏱️ Offset Waktu"
    ],
    index=0
)

st.sidebar.markdown("---")
wib_tz = timezone(timedelta(hours=7))
now_wib = datetime.now(wib_tz)
st.sidebar.caption(f"PAWITRA • {now_wib.strftime('%Y-%m-%d')}")
st.sidebar.caption("Open Source • Jolotundo Research Consortium")
st.sidebar.caption("🏫 Sekolah Alam Penanggungan")
st.sidebar.caption("📜 SAJAK (Sinau Aksara Jawa Kuno)")
st.sidebar.caption("🔭 Jolotundo Obsv")
st.sidebar.caption(f"📍 {ΩConst.LOC_LAT:.4f}°, {ΩConst.LOC_LON:.4f}°")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def format_ka(ka):
    return f"{ka:,}".replace(",", ".")

def get_wuku_display(ka):
    info = mech_engine.get_wuku_by_ka(ka)
    epoch = mech_engine.get_detailed_wuku_epoch_info(ka)
    return info, epoch

def show_metric(label, value):
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def display_wuku_detail(info, epoch, ka):
    cols = st.columns(2)
    with cols[0]:
        st.markdown("""
        <div class="jae-card">
            <h3>📆 Wuku</h3>
        """, unsafe_allow_html=True)
        st.metric("Nama Wuku", f"{info['wuku_name']} (#{info['wuku_number']})")
        st.metric("Hari ke-", f"{info['day_in_wuku']}/7")
        st.metric("TU-PA-Ā", "✅" if info['is_tu_pa_a'] else "❌")
        st.markdown("</div>", unsafe_allow_html=True)

    with cols[1]:
        st.markdown("""
        <div class="jae-card">
            <h3>🌀 Wara Triple</h3>
        """, unsafe_allow_html=True)
        st.metric("Sadwara", f"{info['sadwara_full']} ({info['sadwara']})")
        st.metric("Pancawara", f"{info['pancawara_full']} ({info['pancawara']})")
        st.metric("Saptawara", f"{info['saptawara_full']} ({info['saptawara']})")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="jae-card">
        <h3>📊 Posisi Relatif</h3>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Hari sejak epoch", f"{epoch['days_since_epoch']:,}")
        st.metric("Arah", epoch['direction'])
    with c2:
        st.metric("Siklus Wuku", f"{epoch['cycle_number']}")
        st.metric("Hari dalam siklus", f"{epoch['day_in_cycle']}/210")
    with c3:
        st.metric("Progres siklus", f"{epoch['progress_percent']:.1f}%")
        st.metric("TU-PA-Ā berikutnya", f"{epoch['days_to_next_tu_pa_a']} hari")
    st.markdown("</div>", unsafe_allow_html=True)

def display_astronomical_year_help():
    """Helper untuk menampilkan informasi tahun negatif."""
    st.caption("""
    ℹ️ **Tahun astronomi** – sistem penanggalan dengan dukungan tahun negatif:
    - `1` = 1 M | `0` = 1 SM | `-1` = 2 SM | `-3101` = 3102 SM
    """)

# ============================================================================
# PAGE: BERANDA
# ============================================================================
if nav == "🏠 Beranda":
    st.title("🏛️ OSS ΩLDJAVA-astro")
    st.markdown("""
    <div style="background: linear-gradient(145deg, #1a1e2a, #0e1117); border-radius: 16px; padding: 24px; border: 1px solid #2a3040; margin-bottom: 20px;">
        <p style="color: #c0c8d8; font-size: 1.05rem; line-height: 1.7;">
            <b style="color: #d4b896;">Open Source System for Old Javanese Archaeoastronomy</b> – 
            sistem terpadu untuk astronomi arkeologi Jawa Kuno.
        </p>
        <div style="margin-top: 12px;">
            <span class="oss-badge">🌍 OPEN SOURCE</span>
            <span class="oss-badge" style="margin-left: 8px;">🔓 PUBLIC</span>
            <span class="oss-badge" style="margin-left: 8px;">⚡ OSS.Ω</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ============================================================
    # TAMPILKAN TAHUN SAKA DAN BULAN SAKA UNTUK WAKTU SEKARANG
    # ============================================================
    try:
        wib_tz = timezone(timedelta(hours=7))
        now = datetime.now(wib_tz)
        year = now.year
        month = now.month
        day = now.day
        hour = now.hour
        minute = now.minute
        second = now.second

        jd_utc = time_sys.wib_to_jd_utc(year, month, day, hour, minute, second)
        saka_cal = get_saka_cal()
        saka_info = saka_cal.jd_to_saka(jd_utc)

        saka_year = saka_info.get('saka_year')
        saka_month = saka_info.get('month_name')
        is_adhika = saka_info.get('is_adhika', False)

        if saka_year is not None:
            st.markdown(f"""
            <div style="background: #1a1e2a; border-radius: 12px; padding: 16px 20px; border: 1px solid #d4b896; margin: 20px 0;">
                <h3 style="color: #d4b896; margin-top: 0;">📅 Kalender Saka Sekarang</h3>
                <p style="color: #f0e6d0; font-size: 1.1rem;">
                    <b>Tahun Saka:</b> {saka_year}
                    &nbsp;·&nbsp; <b>Bulan:</b> {saka_month if saka_month else 'N/A'}
                    { ' (Bulan Adhika)' if is_adhika else '' }
                </p>
                <p style="color: #8899bb; font-size: 0.9rem;">
                    Berdasarkan waktu sekarang: {now.strftime('%Y-%m-%d %H:%M:%S')} WIB
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Tidak dapat mengambil informasi Saka untuk waktu sekarang.")
    except Exception as e:
        st.warning(f"Gagal mengambil informasi Saka: {e}")

    # Deskripsi lengkap dengan dukungan tahun negatif
    st.markdown("""
    <div class="description-box">
        <b>🔭 EPHEMERIS PRESISI TINGGI – SUMBER RESMI &amp; VALIDASI</b>
        <br><br>
        <b>☀️ MATAHARI (VSOP87D) – IMCCE / Observatoire de Paris</b><br>
        Menggunakan <b>VSOP87D</b> (<i>Bretagnon &amp; Francou, 1988</i>) dari 
        <b>IMCCE - Observatoire de Paris</b>, yang merupakan turunan spherical 
        (bujur, lintang, radius) dari solusi analitik VSOP87 yang difit terhadap 
        integrasi numerik <b>DE200/LE200 (JPL)</b>. Implementasi ini adalah 
        translasi Python langsung dari subroutine Fortran resmi 
        (file data <code>VSOP87D.ear</code>).
        <br><br>
        Validasi internal terhadap tabel referensi FORTRAN menunjukkan selisih 
        posisi <b>&lt; 0.001″</b>. Perbandingan eksternal dengan 
        <b>JPL Horizons (DE441)</b> menunjukkan akurasi praktis <b>3–10″</b> 
        untuk koordinat ekuatorial dan <b>&lt; 0.1°</b> untuk koordinat horizontal.
        <br><br>
        <b>🌙 BULAN (ELP2000-82B) – SYRTE / Observatoire de Paris</b><br>
        Menggunakan <b>ELP2000-82B</b> (<i>Chapront-Touzé, Chapront &amp; Francou, 2001</i>) 
        dari <b>SYRTE - Observatoire de Paris</b>, solusi semi-analitik yang 
        dikalibrasi terhadap integrasi numerik <b>DE200/LE200 (JPL)</b>. 
        Implementasi ini menggunakan 36 file data resmi 
        (<code>ELP01</code> sampai <code>ELP36</code>) yang berisi deret Fourier 
        dan Poisson untuk bujur, lintang, dan jarak, sesuai dokumentasi internal 
        SYRTE (<i>Lunar solution ELP, version ELP 2000-82B</i>).
        <br><br>
        Validasi internal terhadap <b>Tabel H</b> (lima epoch acuan) menunjukkan 
        perbedaan posisi <b>&lt; 0.001 km</b> (sub-meter). Perbandingan eksternal 
        dengan <b>JPL Horizons (DE441)</b> menunjukkan akurasi praktis 
        <b>7–10″</b> untuk asensio rekta/deklinasi dan <b>&lt; 40 km</b> 
        untuk jarak geosentrik.
        <br><br>
        <b>📆 WUKU SYSTEM (210-HARI) – SUMBER EPIGRAFI</b><br>
        Berdasarkan penelitian <b>Louis-Charles Damais (1955)</b> tentang 
        kalender Jawa kuno, serta katalog prasasti dan wuku dalam 
        <b><i>Javaanese Oorkonden</i></b> (<i>Pigeaud, 1960–1963</i>). 
        Sistem ini menggunakan epoch absolut <b>8 Februari 1 SM</b> 
        (KA 1132630) dan siklus 210 hari yang konsisten dengan data prasasti.
        <br><br>
        <b>📅 DUKUNGAN TAHUN NEGATIF (SISTEM TAHUN ASTRONOMI)</b><br>
        Sistem ini mendukung <b>tahun astronomi</b> (tahun negatif) untuk rentang waktu 
        yang sangat luas, sesuai dengan konvensi astronomi internasional:
        <ul>
            <li><b>Tahun 1 M</b> → ditulis <code>1</code></li>
            <li><b>Tahun 1 SM</b> → ditulis <code>0</code></li>
            <li><b>Tahun 2 SM</b> → ditulis <code>-1</code></li>
            <li><b>Tahun 3102 SM</b> (awal Kali Yuga) → ditulis <code>-3101</code></li>
        </ul>
        Dengan sistem ini, perhitungan kalender dan astronomi dapat dilakukan secara konsisten 
        melintasi batas tahun Masehi tanpa perlu konversi manual yang rumit. Cukup masukkan 
        tahun negatif pada kolom input yang tersedia di menu <b>Tanggal Spesifik</b> atau 
        <b>Konversi Waktu</b>.
        <br><br>
        <b>📚 DATABASE DAMAIS (112 PRASASTI)</b><br>
        Seluruh data prasasti yang digunakan untuk validasi dan analisis sistem zodiak 
        bersumber dari publikasi ilmiah:<br>
        <b>Louis-Charles Damais</b> (1955). 
        <i>"II. Études d'épigraphie indonésienne : IV. Discussion de la date des inscriptions"</i>, 
        <b>Bulletin de l'École française d'Extrême-Orient</b>, tome 47, n°1, pp. 7-290. 
        DOI: <a href="https://doi.org/10.3406/befeo.1955.5406" target="_blank">10.3406/befeo.1955.5406</a>.
        <br><br>
        <b>📜 KONVERSI PRASASTI SAKA → MASEHI (Ω-STHAPATI)</b><br>
        Metode <b>smart parsing</b> dikembangkan berdasarkan metodologi 
        <b>Damais (1955)</b> dan <b>Proudfoot (2013)</b> untuk deteksi 
        interkalasi (<i>punaḥ</i>), dikombinasikan dengan sistem 
        <b>4 komponen utama</b> (Tahun, Bulan, Wara, Wuku) dan skor 
        <b>TPDP (Temporal Probabilistic Dating Protocol)</b> yang 
        dikembangkan khusus untuk arkeoastronomi Jawa Kuno oleh 
        <b>Jolotundo Obsv (2024)</b>.
        <br><br>
        <b>⏱️ KOREKSI WAKTU (ΔT) – SUMBER HISTORIS &amp; MODERN</b><br>
        ΔT dihitung dengan metode hybrid: data eksplisit <b>IERS/HMNAO</b> 
        (era modern), jangkar gerhana historis Jolotundo 702–1299 M 
        (<i>Morrison &amp; Stephenson, 2004</i>), dan polinomial 
        <b>Espenak &amp; Meeus (2006)</b> untuk era di luar jangkauan data.
        <br><br>
        <b>🌏 KOORDINAT HORIZONTAL &amp; KOREKSI ATMOSFER</b><br>
        Koreksi refraksi atmosfer menggunakan formulasi <b>Bennett (1982)</b> 
        dengan koreksi suhu/tekanan dari <b>Meeus (1998)</b>. 
        Paralaks diurnal dihitung dengan metode vektor 
        <b>JPL Horizons style</b> (<i>Meeus, 1998</i>).
        <br><br>
        <b>📍 LOKASI ACUAN – JOLOTUNDO</b><br>
        Observatorium Jolotundo, Jawa Timur (−7.609444°, 112.595556°, elev. 554.5 m) 
        dengan parameter atmosfer lokal dari model <b>GPT3 + VMF3</b> (epoch 2026.445).
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="jae-card"><h3>☀️ Matahari</h3><p>VSOP87D (IMCCE)<br>Bretagnon &amp; Francou, 1988</p></div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="jae-card"><h3>🌙 Bulan</h3><p>ELP2000-82B (SYRTE)<br>Chapront-Touzé, Chapront &amp; Francou, 2001</p></div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="jae-card"><h3>📜 Prasasti</h3><p>Ω-STHAPATI<br>Damais + Proudfoot + (smart parsing) Jolotundo Obsv</p></div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="footer">
        OSS ΩLDJAVA-astro • Open Source • Data: IMCCE VSOP87D / SYRTE ELP2000-82B • Jolotundo Obsv
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# PAGE: REAL-TIME
# ============================================================================
elif nav == "🌞 Real-time":
    st.title("🌞 Real-time Astronomy")
    st.caption("Data berdasarkan waktu sistem lokal (dianggap WIB)")

    if st.button("🔄 Refresh Sekarang", use_container_width=True):
        st.rerun()

    wib_tz = timezone(timedelta(hours=7))
    now = datetime.now(wib_tz)
    year, month, day = now.year, now.month, now.day
    hour = now.hour + now.minute / 60.0 + now.second / 3600.0

    st.markdown(f"""
    <div style="background: #1a1e2a; border-radius: 10px; padding: 16px; margin: 8px 0 20px 0; border-left: 4px solid #d4b896;">
        <b style="color: #d4b896;">🕐 Waktu:</b> 
        <span style="color: #f0e6d0;">{year:04d}-{month:02d}-{day:02d} {int(hour):02d}:{int((hour-int(hour))*60):02d}:{int(((hour-int(hour))*60-int((hour-int(hour))*60))*60):02d} WIB</span>
    </div>
    """, unsafe_allow_html=True)

    jd_utc = time_sys.wib_to_jd_utc(year, month, day, int(hour), int((hour-int(hour))*60), int(((hour-int(hour))*60-int((hour-int(hour))*60))*60))
    jd_tt = time_sys.wib_to_jd_tt_extended(year, month, day, int(hour), int((hour-int(hour))*60), int(((hour-int(hour))*60-int((hour-int(hour))*60))*60))
    ka = mech_engine.date_to_ka(year, month, day)
    wuku_info, epoch_info = get_wuku_display(ka)

    col1, col2, col3, col4 = st.columns(4)
    with col1: show_metric("KA (Kali Ahargana)", format_ka(ka))
    with col2: show_metric("Wuku", f"{wuku_info['wuku_name']} (#{wuku_info['wuku_number']})")
    with col3: show_metric("Wara Triple", wuku_info['wara_triple_full'])
    with col4: show_metric("TU-PA-Ā", "✅ YA" if wuku_info['is_tu_pa_a'] else "❌ TIDAK")

    with st.spinner("Menghitung ephemeris..."):
        try:
            jrc_data = jrc_archaeo.get_complete_ephemeris(
                year_astro=year, month=month, day=day,
                hour=int(hour), minute=int((hour-int(hour))*60), second=int(((hour-int(hour))*60-int((hour-int(hour))*60))*60),
                use_current_time=False
            )
            sun = jrc_data["sun"]
            moon = jrc_data["moon"]

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""<div class="jae-card"><h3>☀️ Matahari</h3>""", unsafe_allow_html=True)
                st.metric("Altitude", f"{sun['horizontal_apparent']['altitude_deg']:.2f}°")
                st.metric("Azimuth", f"{sun['horizontal_apparent']['azimuth_deg']:.2f}°")
                st.metric("RA", f"{sun['geocentric']['equatorial']['ra_deg']:.4f}°")
                st.metric("Dec", f"{sun['geocentric']['equatorial']['dec_deg']:.4f}°")
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown("""<div class="jae-card"><h3>🌙 Bulan</h3>""", unsafe_allow_html=True)
                st.metric("Altitude", f"{moon['horizontal_apparent']['altitude_deg']:.2f}°")
                st.metric("Azimuth", f"{moon['horizontal_apparent']['azimuth_deg']:.2f}°")
                st.metric("Fase", f"{moon['phase']['phase_name']}")
                st.metric("Iluminasi", f"{moon['phase']['illumination_fraction']*100:.1f}%")
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("""<div class="jae-card"><h3>🌅 Waktu Matahari</h3>""", unsafe_allow_html=True)
            sr = jrc_data["sun"]["times"]
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Terbit", sr.get("sunrise_wib", "--:--:--"))
            with c2: st.metric("Transit", sr.get("transit_wib", "--:--:--"))
            with c3: st.metric("Terbenam", sr.get("sunset_wib", "--:--:--"))
            st.metric("Panjang Siang", f"{sr.get('day_length_hours', 0):.2f} jam")
            st.markdown("</div>", unsafe_allow_html=True)

            mr = moon.get("times", {})
            if mr and "error" not in mr:
                st.markdown("""<div class="jae-card"><h3>🌙 Waktu Bulan</h3>""", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1: st.metric("Terbit", mr.get("moonrise", {}).get("wib", "--:--:--"))
                with c2: st.metric("Transit", mr.get("transit", {}).get("wib", "--:--:--"))
                with c3: st.metric("Terbenam", mr.get("moonset", {}).get("wib", "--:--:--"))
                st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Error menghitung ephemeris: {str(e)}")

    with st.expander("📆 Detail Wuku & Wara", expanded=False):
        cols = st.columns(2)
        with cols[0]:
            st.markdown(f"""
            **Wuku:** {wuku_info['wuku_name']} (#{wuku_info['wuku_number']})  
            **Hari dalam Wuku:** {wuku_info['day_in_wuku']}/7  
            **Sadwara:** {wuku_info['sadwara_full']} ({wuku_info['sadwara']})  
            **Pancawara:** {wuku_info['pancawara_full']} ({wuku_info['pancawara']})  
            **Saptawara:** {wuku_info['saptawara_full']} ({wuku_info['saptawara']})  
            """)
        with cols[1]:
            st.markdown(f"""
            **Triple Wara:** {wuku_info['wara_triple_full']}  
            **Kode:** {wuku_info['wara_triple']}  
            **Hari sejak epoch:** {epoch_info['days_since_epoch']:,} ({epoch_info['direction']})  
            **Siklus:** {epoch_info['cycle_number']}, hari {epoch_info['day_in_cycle']}/210  
            **TU-PA-Ā berikutnya:** {epoch_info['days_to_next_tu_pa_a']} hari  
            """)

# ============================================================================
# PAGE: TANGGAL SPESIFIK
# ============================================================================
elif nav == "📅 Tanggal Spesifik":
    st.title("📅 Tanggal Spesifik")
    st.caption("Masukkan tanggal dan waktu (WIB) untuk perhitungan lengkap")
    st.caption("📅 Gunakan tahun negatif untuk tahun SM (contoh: -3101 = 3102 SM, 0 = 1 SM)")

    col1, col2, col3 = st.columns(3)
    with col1:
        year = st.number_input("Tahun (negatif untuk SM)", value=2024, step=1, format="%d")
        st.caption("ℹ️ Contoh: -3101 = 3102 SM, 0 = 1 SM, 1 = 1 M")
    with col2:
        month = st.selectbox("Bulan", list(range(1, 13)), index=datetime.now().month - 1)
    with col3:
        day = st.number_input("Hari", value=1, min_value=1, max_value=31, step=1)

    time_input = st.text_input("Jam (HH:MM:SS atau desimal)", value="12:00:00")
    if st.button("🔍 Hitung", use_container_width=True):
        try:
            hour = parse_time(time_input)
            st.markdown(f"""
            <div style="background: #1a1e2a; border-radius: 10px; padding: 12px 16px; margin: 8px 0 16px 0; border-left: 4px solid #d4b896;">
                <b style="color: #d4b896;">📅 Data untuk:</b> 
                <span style="color: #f0e6d0;">{year:04d}-{month:02d}-{day:02d} {int(hour):02d}:{int((hour-int(hour))*60):02d} WIB</span>
            </div>
            """, unsafe_allow_html=True)

            with st.spinner("Menghitung data astronomi..."):
                jd_utc = time_sys.wib_to_jd_utc(year, month, day, int(hour), int((hour-int(hour))*60), int(((hour-int(hour))*60-int((hour-int(hour))*60))*60))
                jd_tt = time_sys.wib_to_jd_tt_extended(year, month, day, int(hour), int((hour-int(hour))*60), int(((hour-int(hour))*60-int((hour-int(hour))*60))*60))
                ka = mech_engine.date_to_ka(year, month, day)
                wuku_info, epoch_info = get_wuku_display(ka)

                c1, c2, c3, c4 = st.columns(4)
                with c1: show_metric("KA", format_ka(ka))
                with c2: show_metric("Wuku", f"{wuku_info['wuku_name']} (#{wuku_info['wuku_number']})")
                with c3: show_metric("Wara Triple", wuku_info['wara_triple_full'])
                with c4: show_metric("TU-PA-Ā", "✅" if wuku_info['is_tu_pa_a'] else "❌")

                jrc_data = jrc_archaeo.get_complete_ephemeris(
                    year_astro=year, month=month, day=day,
                    hour=int(hour), minute=int((hour-int(hour))*60), second=int(((hour-int(hour))*60-int((hour-int(hour))*60))*60),
                    use_current_time=False
                )
                sun = jrc_data["sun"]
                moon = jrc_data["moon"]

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("""<div class="jae-card"><h3>☀️ Matahari</h3>""", unsafe_allow_html=True)
                    st.metric("Altitude", f"{sun['horizontal_apparent']['altitude_deg']:.2f}°")
                    st.metric("Azimuth", f"{sun['horizontal_apparent']['azimuth_deg']:.2f}°")
                    st.metric("RA", f"{sun['geocentric']['equatorial']['ra_deg']:.4f}°")
                    st.metric("Dec", f"{sun['geocentric']['equatorial']['dec_deg']:.4f}°")
                    st.markdown("</div>", unsafe_allow_html=True)

                with col2:
                    st.markdown("""<div class="jae-card"><h3>🌙 Bulan</h3>""", unsafe_allow_html=True)
                    st.metric("Altitude", f"{moon['horizontal_apparent']['altitude_deg']:.2f}°")
                    st.metric("Azimuth", f"{moon['horizontal_apparent']['azimuth_deg']:.2f}°")
                    st.metric("Fase", f"{moon['phase']['phase_name']}")
                    st.metric("Iluminasi", f"{moon['phase']['illumination_fraction']*100:.1f}%")
                    st.markdown("</div>", unsafe_allow_html=True)

                with st.expander("📖 Pancanga & Vedic Time (Old Java Astronomy)", expanded=True):
                    try:
                        import io, contextlib
                        f = io.StringIO()
                        with contextlib.redirect_stdout(f):
                            display_info(year, month, day, hour)
                        st.code(clean_ansi(f.getvalue()), language="text")
                    except Exception as e:
                        st.warning(f"Detail Old Java: {str(e)}")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE: WUKU & WARA
# ============================================================================
elif nav == "📆 Wuku & Wara":
    st.title("📆 Wuku & Wara System")
    st.caption("Sistem Wuku 210-hari dengan KA (Kali Ahargana)")

    tab1, tab2, tab3 = st.tabs(["🔍 Cari Wuku", "📊 TU-PA-Ā", "📋 Informasi"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            search_type = st.radio("Cari berdasarkan:", ["KA", "Tanggal"], horizontal=True)
        if search_type == "KA":
            ka_input = st.number_input("Masukkan KA", value=0, step=1, format="%d")
            if st.button("Cari KA"):
                info = mech_engine.get_wuku_by_ka(ka_input)
                epoch = mech_engine.get_detailed_wuku_epoch_info(ka_input)
                display_wuku_detail(info, epoch, ka_input)
        else:
            y = st.number_input("Tahun (negatif untuk SM)", value=2024, step=1, format="%d")
            st.caption("ℹ️ Contoh: -3101 = 3102 SM, 0 = 1 SM")
            m = st.selectbox("Bulan", list(range(1, 13)), index=0)
            d = st.number_input("Hari", value=1, min_value=1, max_value=31, step=1)
            if st.button("Cari Tanggal"):
                ka = mech_engine.date_to_ka(y, m, d)
                info = mech_engine.get_wuku_by_ka(ka)
                epoch = mech_engine.get_detailed_wuku_epoch_info(ka)
                st.info(f"KA: {format_ka(ka)}")
                display_wuku_detail(info, epoch, ka)

    with tab2:
        st.subheader("📍 TU-PA-Ā (Tungleh-Pahing-Aditya)")
        st.caption("Hari pertama siklus wuku, referensi absolut")
        tpa_year = st.number_input("Tahun (negatif untuk SM) untuk mencari TU-PA-Ā", value=2024, step=1, format="%d")
        st.caption("ℹ️ Contoh: -3101 = 3102 SM")
        if st.button("🔍 Cari TU-PA-Ā di tahun ini"):
            tpa_list = mech_engine.find_tu_pa_a_in_year(tpa_year)
            if tpa_list:
                data = []
                for tpa in tpa_list:
                    ka = tpa["ka"]
                    w_info = mech_engine.get_wuku_by_ka(ka)
                    y, m, d = tpa["date"]
                    data.append({
                        "Tanggal": f"{int(y)}-{int(m):02d}-{int(d):02d}",
                        "KA": format_ka(ka),
                        "Wuku": w_info["wuku_name"],
                        "Wara": w_info["wara_triple"]
                    })
                st.dataframe(data, use_container_width=True)
            else:
                st.warning("Tidak ditemukan TU-PA-Ā di tahun ini.")

    with tab3:
        st.subheader("📋 Informasi Sistem Wuku")
        st.markdown("""
        **Sistem Wuku 210-hari** adalah kalender tradisional Jawa yang terdiri dari:
        - **30 Wuku** (masing-masing 7 hari)
        - **Siklus 210 hari** (30 × 7)
        - **Epoch absolut:** 8 Februari 1 SM (KA 1132630)
        - **TU-PA-Ā:** Tungleh-Pahing-Aditya (hari pertama siklus)

        **Komponen Wara:**
        - **Sadwara (6):** Tungleh, Haryang, Wurukung, Paniron, Was, Maulu
        - **Pancawara (5):** Pahing, Pon, Wage, Kaliwon, Umanis
        - **Saptawara (7):** Aditya, Soma, Anggara, Budha, Wrhaspati, Sukra, Saniscara

        **30 Wuku:**
        Sinta, Landep, Wukir, Kurantil, Tolu, Gumbreg, Warigalit, Warigagung,
        Julungwangi, Sungsang, Galungan, Kuningan, Langkir, Mandasiya, Julungpujut,
        Pahang, Kuruwelut, Marakeh, Tambir, Medangkungan, Maktal, Wuye, Manahil,
        Prangbakat, Bala, Wugu, Wayang, Kulawu, Dukut, Watugunung
        """)

# ============================================================================
# PAGE: KONVERSI PRASASTI
# ============================================================================
elif nav == "📜 Konversi Prasasti":
    st.title("📜 Konversi Prasasti Saka → Masehi")
    st.caption("Ω-STHAPATI v301.4 – 4 komponen utama: Tahun, Bulan, Wara, Wuku")

    with st.expander("📖 Panduan Input", expanded=False):
        st.markdown("""
        **Field yang diperlukan:**
        - **Tahun Śaka:** tahun dalam penanggalan Saka (contoh: 851)
        - **Bulan Śaka:** Caitra, Vaisakha, Jyestha, Asadha, Sravana, Bhadrapada, Asvini, Kartika, Margasira, Pausa, Magha, Phalguna
        - **Tithi:** 1-15 (hari dalam paksa, misal Sukla 5 atau Krsna 12)
        - **Paksa:** Sukla (paruh terang/waxing) atau Krsna (paruh gelap/waning)
        - **Wuku:** (opsional) nama wuku
        - **Wara:** (opsional) bisa lengkap (Tungleh-Pahing-Aditya) atau parsial (Jumat-Wage)
        - **Nakṣatra:** (opsional) nama naksatra

        **Aturan konversi tahun:**
        - Pausa: Śaka +78 atau +79 (ambigu)
        - Magha/Phalguna: Śaka +79
        - Lainnya: Śaka +78
        """)

    col1, col2 = st.columns(2)
    with col1:
        saka_year = st.number_input("Tahun Śaka", value=851, step=1, format="%d")
        masa = st.selectbox(
            "Bulan Śaka (Masa)",
            ["Caitra", "Vaisakha", "Jyestha", "Asadha", "Sravana",
             "Bhadrapada", "Asvini", "Kartika", "Margasira", "Pausa",
             "Magha", "Phalguna"],
            index=8
        )
        tithi = st.number_input("Tithi dalam Paksa (1-15)", value=1, min_value=1, max_value=15, step=1)
        paksa = st.selectbox("Paksa (Sukla = waxing, Krsna = waning)", ["Sukla", "Krsna"], index=0)

    with col2:
        wuku = st.text_input("Wuku (opsional)", placeholder="Contoh: Wugu")
        wara = st.text_input("Wara (opsional, bisa parsial)", placeholder="Contoh: Tungleh-Pahing-Sukra atau Jumat-Wage")
        nakshatra = st.text_input("Nakṣatra (opsional)", placeholder="Contoh: Aswini")

    if st.button("🔄 Konversi Prasasti", use_container_width=True):
        if not saka_year or not masa:
            st.warning("Masukkan tahun Śaka dan bulan.")
        else:
            with st.spinner("Memproses konversi..."):
                try:
                    data = {
                        "saka_year": int(saka_year),
                        "masa": masa,
                        "tithi": int(tithi),
                        "paksa": paksa,
                        "wuku": wuku if wuku else "",
                        "wara_string": wara if wara else "",
                        "nakshatra": nakshatra if nakshatra else ""
                    }

                    results = sthapati.convert_prasasti_with_smart_parsing(data, verbose=False)

                    if not results:
                        st.error("❌ Tidak ditemukan kandidat yang valid.")
                    else:
                        st.success(f"✅ Ditemukan {len(results)} kandidat")

                        best = results[0]
                        cand = best["candidate"]
                        y, m, d = cand["date"]
                        ka = cand["ka"]
                        w_info = mech_engine.get_wuku_by_ka(ka)

                        st.markdown(f"""
                        <div style="background: #1a1e2a; border-radius: 12px; padding: 20px; border: 1px solid #d4b896; margin: 12px 0;">
                            <h3 style="color: #d4b896; margin-top: 0;">✨ Kandidat Terbaik</h3>
                            <p style="color: #f0e6d0; font-size: 1.1rem;">
                                <b>{int(y)}-{int(m):02d}-{int(d):02d}</b>
                                &nbsp;·&nbsp; KA: <b>{format_ka(ka)}</b>
                                &nbsp;·&nbsp; Wuku: <b>{w_info['wuku_name']}</b>
                            </p>
                            <p style="color: #8899bb; font-size: 0.9rem;">
                                Skor: {best['score']:.3f} &nbsp;·&nbsp; Confidence: {best['confidence']}
                                &nbsp;·&nbsp; Wara: {w_info['wara_triple_full']}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                        table_data = []
                        for i, res in enumerate(results[:5]):
                            c = res["candidate"]
                            yy, mm, dd = c["date"]
                            w_info_tbl = mech_engine.get_wuku_by_ka(c["ka"])
                            table_data.append({
                                "Rank": i + 1,
                                "Tanggal": f"{int(yy)}-{int(mm):02d}-{int(dd):02d}",
                                "KA": format_ka(c["ka"]),
                                "Wuku": w_info_tbl["wuku_name"],
                                "Wara": w_info_tbl["wara_triple"],
                                "Skor": f"{res['score']:.3f}",
                                "Confidence": res["confidence"]
                            })
                        st.dataframe(table_data, use_container_width=True)

                        st.markdown("""<div class="jae-card"><h3>🔍 Verifikasi Input</h3>""", unsafe_allow_html=True)

                        tithi_input = data.get("tithi")
                        paksa_input = data.get("paksa")
                        if tithi_input and paksa_input:
                            hh = 12
                            try:
                                astro_engine = AstronomicalEngine()
                                jd_tt_calc = time_sys.wib_to_jd_tt_extended(int(y), int(m), int(d), hh, 0, 0)
                                sun_data = astro_engine.calculate_sun_position_ultra(jd_tt_calc)
                                moon_data = astro_engine.calculate_moon_position_ultra(jd_tt_calc, sun_data["longitude_deg"])
                                ayanamsa = astro_engine.calculate_ayanamsa_precise(jd_tt_calc)
                                sun_nirayana = (sun_data["longitude_deg"] - ayanamsa) % 360
                                moon_nirayana = (moon_data["longitude"] - ayanamsa) % 360
                                moon_tropical = moon_data["longitude"]

                                tithi_calc = astro_engine.calculate_tithi(sun_nirayana, moon_nirayana, "nirayana")
                                tithi_num = tithi_calc["tithi"]
                                paksa_calc = tithi_calc["paksa"]
                                if paksa_calc == "Sukla":
                                    tithi_display = tithi_num
                                else:
                                    tithi_display = tithi_num - 15

                                st.write(f"**Tithi input:** {tithi_input} {paksa_input}")
                                st.write(f"**Tithi hitung:** {tithi_display} {paksa_calc}")

                                if tithi_input == tithi_display and paksa_input.lower() == paksa_calc.lower():
                                    st.success("✅ Tithi cocok persis")
                                elif abs(tithi_input - tithi_display) <= 1 and paksa_input.lower() == paksa_calc.lower():
                                    st.warning(f"⚠️ Tithi cocok dengan toleransi 1 (selisih {abs(tithi_input - tithi_display)})")
                                else:
                                    st.error("❌ Tithi tidak cocok")

                                naks_input = data.get("nakshatra")
                                if naks_input:
                                    old_norm = OldJavaNormalizer()
                                    naks_norm = old_norm.normalize(naks_input)

                                    naks_nirayana = astro_engine.calculate_nakshatra(moon_nirayana, "nirayana")
                                    naks_sayana = astro_engine.calculate_nakshatra(moon_tropical, "tropical")

                                    st.write(f"**Nakṣatra input:** {naks_norm}")
                                    st.write(f"**Nakṣatra hitung (Nirayana):** {naks_nirayana['nakshatra']}")
                                    st.write(f"**Nakṣatra hitung (Sayana):** {naks_sayana['nakshatra']}")

                                    if naks_norm == naks_nirayana["nakshatra"]:
                                        st.success("✅ Nakṣatra cocok dengan Nirayana")
                                    elif naks_norm == naks_sayana["nakshatra"]:
                                        st.success("✅ Nakṣatra cocok dengan Sayana")
                                    else:
                                        st.warning("⚠️ Nakṣatra tidak cocok dengan kedua sistem (cek ejaan atau sistem)")

                            except Exception as e:
                                st.warning(f"Tidak dapat verifikasi tithi/naksatra: {str(e)}")

                        st.markdown("</div>", unsafe_allow_html=True)

                        with st.expander("📊 Evaluasi 4 Komponen Utama", expanded=False):
                            try:
                                import io, contextlib
                                f = io.StringIO()
                                with contextlib.redirect_stdout(f):
                                    sthapati.display_main_components_evaluation(results)
                                st.code(clean_ansi(f.getvalue()), language="text")
                            except Exception as e:
                                st.warning(f"Tidak dapat menampilkan evaluasi: {str(e)}")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE: DATABASE DAMAIS
# ============================================================================
elif nav == "📊 Database Damais":
    st.title("📊 Database Prasasti Damais")
    st.caption("📚 Sumber: Damais, L.-C. (1955). BEFEO 47.1, pp. 7-290. DOI: 10.3406/befeo.1955.5406")
    st.caption("112 prasasti dari database Damais dengan hasil validasi sistem zodiak")

    if not validation_df.empty:
        total = len(validation_df)
        exact = validation_df[validation_df["status"] == "✅ EXACT MATCH"].shape[0]
        col1, col2, col3 = st.columns(3)
        with col1: show_metric("Total Prasasti", total)
        with col2: show_metric("Exact Match", f"{exact}/{total} ({exact/total*100:.1f}%)")
        with col3:
            sys_counts = {}
            for _, row in validation_df.iterrows():
                jrc = row.get("jrc_verification")
                if jrc and isinstance(jrc, dict):
                    sys = jrc.get("system_detected")
                    if sys:
                        sys_counts[sys] = sys_counts.get(sys, 0) + 1
            if sys_counts:
                show_metric("Sistem Zodiak", f"{sys_counts.get('nirayana',0)} Nirayana, {sys_counts.get('sayana',0)} Sayana")
            else:
                show_metric("Sistem Zodiak", "Belum ada data")
    else:
        st.info("Data validasi belum tersedia. Jalankan quick_test_ijcc.py untuk menghasilkan data.")

    st.subheader("📋 Daftar Prasasti")

    col1, col2, col3 = st.columns(3)
    with col1:
        filter_system = st.selectbox("Filter Sistem Zodiak", ["Semua", "Sayana", "Nirayana", "Both", "None"])
    with col2:
        centuries = sorted(set([(ins["saka"] // 100) * 100 for ins in DAMAIS_INSCRIPTIONS if ins.get("saka")]))
        century_options = ["Semua"] + [f"{c}-{c+99}" for c in centuries]
        filter_century = st.selectbox("Filter Abad", century_options)
    with col3:
        search_text = st.text_input("Cari (nama/ID)", "")

    display_data = []
    for ins in DAMAIS_INSCRIPTIONS:
        row = {
            "No": ins.get("no"),
            "ID": ins.get("id"),
            "Nama": ins.get("name"),
            "Śaka": ins.get("saka"),
            "Masa": ins.get("masa"),
            "Tithi": ins.get("tithi"),
            "Paksa": ins.get("paksa"),
            "Wara": ins.get("wara_string"),
            "Wuku": ins.get("wuku"),
            "Nakṣatra": ins.get("nakshatra"),
            "Tanggal Damais": f"{ins['julian_date'][0]}-{ins['julian_date'][1]:02d}-{ins['julian_date'][2]:02d}" if ins.get("julian_date") else "",
        }
        if not validation_df.empty:
            match = validation_df[validation_df["no"] == ins.get("no")]
            if not match.empty:
                row["Status"] = match.iloc[0].get("status", "")
                row["KA"] = match.iloc[0].get("ka")
                row["Skor"] = match.iloc[0].get("score")
                jrc = match.iloc[0].get("jrc_verification")
                if jrc and isinstance(jrc, dict):
                    row["Sistem Zodiak"] = jrc.get("system_detected") or "N/A"
                    row["Sistem Zodiak (Tol ±1)"] = jrc.get("system_detected_tolerance") or "N/A"
                else:
                    row["Sistem Zodiak"] = "N/A"
                    row["Sistem Zodiak (Tol ±1)"] = "N/A"
            else:
                row["Status"] = "Belum diproses"
                row["KA"] = ""
                row["Skor"] = ""
                row["Sistem Zodiak"] = "N/A"
        display_data.append(row)

    df = pd.DataFrame(display_data)

    if filter_system != "Semua":
        df = df[df["Sistem Zodiak"] == filter_system]
    if filter_century != "Semua":
        century_start = int(filter_century.split("-")[0])
        df = df[(df["Śaka"] >= century_start) & (df["Śaka"] < century_start + 100)]
    if search_text:
        df = df[df.apply(lambda row: search_text.lower() in str(row["Nama"]).lower() or search_text.lower() in str(row["ID"]).lower(), axis=1)]

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("🔍 Detail Prasasti")
    if not df.empty:
        selected_id = st.selectbox("Pilih Prasasti (ID)", df["ID"].tolist())
        if selected_id:
            detail = df[df["ID"] == selected_id]
            if not detail.empty:
                row = detail.iloc[0]
                st.markdown(f"""
                <div class="jae-card">
                    <h3>{row['ID']} - {row['Nama']}</h3>
                    <p><b>Śaka:</b> {row['Śaka']} &nbsp;·&nbsp; <b>Masa:</b> {row['Masa']}</p>
                    <p><b>Tithi:</b> {row['Tithi']} {row['Paksa']} &nbsp;·&nbsp; <b>Wara:</b> {row['Wara']} &nbsp;·&nbsp; <b>Wuku:</b> {row['Wuku']}</p>
                    <p><b>Nakṣatra:</b> {row['Nakṣatra']} &nbsp;·&nbsp; <b>Tanggal Damais:</b> {row['Tanggal Damais']}</p>
                    <p><b>Status:</b> {row.get('Status', 'N/A')} &nbsp;·&nbsp; <b>KA:</b> {row.get('KA', 'N/A')} &nbsp;·&nbsp; <b>Skor:</b> {row.get('Skor', 'N/A')}</p>
                    <p><b>Sistem Zodiak (Exact):</b> {row.get('Sistem Zodiak', 'N/A')} &nbsp;·&nbsp; <b>Sistem Zodiak (Tol ±1):</b> {row.get('Sistem Zodiak (Tol ±1)', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)

# ============================================================================
# PAGE: ANALISIS SISTEM ZODIAK
# ============================================================================
elif nav == "📈 Analisis Sistem Zodiak":
    st.title("📈 Analisis Sistem Zodiak (Sayana vs Nirayana)")
    st.caption("Distribusi sistem zodiak berdasarkan hasil validasi 112 prasasti Damais (1955)")

    if validation_df.empty:
        st.warning("Belum ada data validasi. Jalankan quick_test_ijcc.py terlebih dahulu.")
    else:
        # Ekstrak data sistem
        systems = []
        centuries = []
        for _, row in validation_df.iterrows():
            jrc = row.get("jrc_verification")
            if jrc and isinstance(jrc, dict):
                sys = jrc.get("system_detected")
                if sys and sys != "none" and sys != "both":
                    systems.append(sys)
                    saka = row.get("saka", 0)
                    centuries.append((saka // 100) * 100)

        if systems:
            df_sys = pd.DataFrame({"Sistem": systems, "Abad": centuries})
            counts = df_sys["Sistem"].value_counts().reset_index()
            counts.columns = ["Sistem", "Jumlah"]

            if HAVE_PLOTLY:
                fig = px.bar(counts, x="Sistem", y="Jumlah", color="Sistem",
                             title="Distribusi Sistem Zodiak (Exact Match)",
                             color_discrete_map={"sayana": "#f1c40f", "nirayana": "#3498db"})
                fig.update_layout(
                    plot_bgcolor="#1a1e2a",
                    paper_bgcolor="#1a1e2a",
                    font_color="#c0c8d8",
                    title_font_color="#d4b896"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.bar_chart(counts.set_index("Sistem"))

            # Grafik timeline per abad
            if not df_sys.empty:
                df_century = df_sys.groupby(["Abad", "Sistem"]).size().reset_index(name="Jumlah")
                if HAVE_PLOTLY:
                    fig2 = px.bar(df_century, x="Abad", y="Jumlah", color="Sistem",
                                  title="Sistem Zodiak per Abad",
                                  color_discrete_map={"sayana": "#f1c40f", "nirayana": "#3498db"})
                    fig2.update_layout(
                        plot_bgcolor="#1a1e2a",
                        paper_bgcolor="#1a1e2a",
                        font_color="#c0c8d8",
                        title_font_color="#d4b896"
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    pivot = df_century.pivot(index="Abad", columns="Sistem", values="Jumlah").fillna(0)
                    st.bar_chart(pivot)

        # Statistik tambahan
        st.subheader("📊 Statistik Sistem Zodiak")
        total_naks = 0
        count_sayana = 0
        count_nirayana = 0
        count_both = 0
        count_none = 0

        for _, row in validation_df.iterrows():
            jrc = row.get("jrc_verification")
            if jrc and isinstance(jrc, dict):
                sys = jrc.get("system_detected")
                if sys:
                    total_naks += 1
                    if sys == "sayana":
                        count_sayana += 1
                    elif sys == "nirayana":
                        count_nirayana += 1
                    elif sys == "both":
                        count_both += 1
                    elif sys == "none":
                        count_none += 1

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            show_metric("Total dg Naksatra", total_naks)
        with col2:
            show_metric("Sayana (Tropis)", f"{count_sayana} ({count_sayana/total_naks*100:.1f}%)" if total_naks > 0 else "0")
        with col3:
            show_metric("Nirayana (Sideris)", f"{count_nirayana} ({count_nirayana/total_naks*100:.1f}%)" if total_naks > 0 else "0")
        with col4:
            show_metric("Both", f"{count_both} ({count_both/total_naks*100:.1f}%)" if total_naks > 0 else "0")
        with col5:
            show_metric("None", f"{count_none} ({count_none/total_naks*100:.1f}%)" if total_naks > 0 else "0")

        st.markdown("""
        <div class="description-box">
            <b>📌 Kesimpulan</b><br>
            Berdasarkan validasi 112 prasasti Damais, sistem zodiak <b>Nirayana (sidereal)</b> mendominasi 
            dibandingkan <b>Sayana (tropical)</b>. Grafik per abad menunjukkan bahwa penggunaan 
            Nirayana meningkat pada periode Śaka 800–900 dan menjadi dominan setelah abad ke-10.
            <br><br>
            Beberapa prasasti menunjukkan <b>kedua sistem cocok</b> (Both), yang berarti pada tanggal 
            tersebut naksatra yang sama muncul di kedua sistem zodiak. Kasus <b>None</b> (tidak cocok) 
            mungkin disebabkan oleh kesalahan penulisan atau sistem zodiak yang berbeda.
            <br><br>
            <b>Referensi:</b> Damais, L.-C. (1955). <i>II. Études d'épigraphie indonésienne : IV. Discussion de la date des inscriptions</i>, BEFEO 47.1, pp. 7-290. DOI: 10.3406/befeo.1955.5406.
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# PAGE: KONVERSI WAKTU
# ============================================================================
elif nav == "🔄 Konversi Waktu":
    st.title("🔄 Konversi Waktu")
    st.caption("JD, KA, Gregorian, Julian – konversi antar sistem")
    st.caption("📅 Gunakan tahun negatif untuk tahun SM (contoh: -3101 = 3102 SM)")

    tab1, tab2, tab3, tab4 = st.tabs(["📅 Tanggal → JD/KA", "📊 JD → Tanggal/KA", "📊 KA → Tanggal/JD", "📆 Gregorian ↔ Julian"])

    with tab1:
        y = st.number_input("Tahun (negatif untuk SM)", value=2024, step=1, format="%d", key="conv_t1_y")
        st.caption("ℹ️ Contoh: -3101 = 3102 SM, 0 = 1 SM")
        m = st.selectbox("Bulan", list(range(1, 13)), index=0, key="conv_t1_m")
        d = st.number_input("Hari", value=1, min_value=1, max_value=31, step=1, key="conv_t1_d")
        h = st.number_input("Jam (0-23)", value=12, min_value=0, max_value=23, step=1, key="conv_t1_h")
        mi = st.number_input("Menit (0-59)", value=0, min_value=0, max_value=59, step=1, key="conv_t1_mi")
        s = st.number_input("Detik (0-59)", value=0, min_value=0, max_value=59, step=1, key="conv_t1_s")

        if st.button("Konversi → JD / KA", key="conv_t1_btn"):
            jd = time_sys.date_to_jd_utc(int(y), int(m), int(d), int(h), int(mi), int(s))
            ka = mech_engine.julian_day_to_ka(jd)
            st.metric("JD UTC", f"{jd:.8f}")
            st.metric("KA (Kali Ahargana)", format_ka(ka))
            w_info = mech_engine.get_wuku_by_ka(ka)
            st.metric("Wuku", f"{w_info['wuku_name']} ({w_info['wara_triple']})")

    with tab2:
        jd_input = st.number_input("JD UTC", value=2460000.0, step=0.0001, format="%.6f", key="conv_t2_jd")
        if st.button("Konversi → Tanggal / KA", key="conv_t2_btn"):
            date = time_sys.jd_to_gregorian(jd_input)
            ka = mech_engine.julian_day_to_ka(jd_input)
            st.write(f"**Tahun astronomi:** {date['year_astronomical']} ({date['year_display']})")
            st.write(f"**Tanggal:** {date['year_astronomical']:04d}-{date['month']:02d}-{date['day']:02d} {date['hour']:02d}:{date['minute']:02d}:{date['second']:02d}")
            st.metric("KA", format_ka(ka))
            w_info = mech_engine.get_wuku_by_ka(ka)
            st.metric("Wuku", f"{w_info['wuku_name']} ({w_info['wara_triple']})")

    with tab3:
        ka_input = st.number_input("KA", value=0, step=1, format="%d", key="conv_t3_ka")
        if st.button("Konversi → Tanggal / JD", key="conv_t3_btn"):
            jd = mech_engine.ka_to_julian_day(ka_input)
            y, m, d = mech_engine.ka_to_date(ka_input)
            st.metric("JD UTC", f"{jd:.8f}")
            st.write(f"**Tanggal:** {int(y):04d}-{int(m):02d}-{int(d):02d}")
            w_info = mech_engine.get_wuku_by_ka(ka_input)
            st.metric("Wuku", f"{w_info['wuku_name']} ({w_info['wara_triple']})")

    with tab4:
        st.subheader("Gregorian → Julian")
        yg = st.number_input("Tahun Gregorian (negatif untuk SM)", value=2024, step=1, format="%d", key="conv_t4_yg")
        st.caption("ℹ️ Contoh: -3101 = 3102 SM")
        mg = st.selectbox("Bulan", list(range(1, 13)), index=0, key="conv_t4_mg")
        dg = st.number_input("Hari", value=1, min_value=1, max_value=31, step=1, key="conv_t4_dg")
        if st.button("→ Julian", key="conv_t4_btn1"):
            jd = CC.gregorian_to_jd(int(yg), int(mg), int(dg))
            yj, mj, dj = CC.jd_to_julian(jd)
            st.write(f"**Julian:** {int(yj):04d}-{int(mj):02d}-{int(dj):02d}")

        st.subheader("Julian → Gregorian")
        yj2 = st.number_input("Tahun Julian (negatif untuk SM)", value=2024, step=1, format="%d", key="conv_t4_yj")
        st.caption("ℹ️ Contoh: -3101 = 3102 SM")
        mj2 = st.selectbox("Bulan", list(range(1, 13)), index=0, key="conv_t4_mj")
        dj2 = st.number_input("Hari", value=1, min_value=1, max_value=31, step=1, key="conv_t4_dj")
        if st.button("→ Gregorian", key="conv_t4_btn2"):
            jd = CC.julian_to_jd(int(yj2), int(mj2), int(dj2))
            yg2, mg2, dg2 = CC.jd_to_gregorian(jd)
            st.write(f"**Gregorian:** {int(yg2):04d}-{int(mg2):02d}-{int(dg2):02d}")

# ============================================================================
# PAGE: OFFSET WAKTU
# ============================================================================
elif nav == "⏱️ Offset Waktu":
    st.title("⏱️ Offset Waktu")
    st.caption("Hitung tanggal baru + informasi wuku dengan offset berbagai satuan")

    offset_type = st.selectbox(
        "Jenis offset",
        [
            "Hari solar (hari biasa)",
            "Bulan solar rata-rata (30.44 hari)",
            "Tahun solar rata-rata (365.24 hari)",
            "Bulan lunar sinodik (29.53 hari)",
            "Tahun lunar sinodik (354.37 hari)",
            "Tithi rata-rata (0.984 hari)"
        ],
        index=0
    )

    col1, col2 = st.columns(2)
    with col1:
        year0 = st.number_input("Tahun awal (negatif untuk SM)", value=2024, step=1, format="%d", key="off_y")
        st.caption("ℹ️ Contoh: -3101 = 3102 SM")
    with col2:
        month0 = st.selectbox("Bulan awal", list(range(1, 13)), index=0, key="off_m")
    day0 = st.number_input("Hari awal", value=1, min_value=1, max_value=31, step=1, key="off_d")

    offset_val = st.number_input("Jumlah offset (bisa negatif)", value=0, step=1, format="%d", key="off_val")

    if st.button("🔄 Hitung Offset", use_container_width=True):
        if offset_val == 0:
            st.warning("Masukkan jumlah offset (bisa positif atau negatif).")
        else:
            try:
                date_str = f"{int(year0):04d}-{int(month0):02d}-{int(day0):02d}"
                mapping = {
                    "Hari solar (hari biasa)": "solar_days",
                    "Bulan solar rata-rata (30.44 hari)": "solar_months",
                    "Tahun solar rata-rata (365.24 hari)": "solar_years",
                    "Bulan lunar sinodik (29.53 hari)": "lunar_months",
                    "Tahun lunar sinodik (354.37 hari)": "lunar_years",
                    "Tithi rata-rata (0.984 hari)": "tithi"
                }
                key = mapping[offset_type]
                func = offset_funcs[key]
                res = func(date_str, int(offset_val))

                if "error" in res:
                    st.error(f"❌ {res['error']}")
                else:
                    ny, nm, nd = res["date"]
                    st.markdown(f"""
                    <div style="background: #1a1e2a; border-radius: 12px; padding: 20px; border: 1px solid #d4b896; margin: 12px 0;">
                        <h3 style="color: #d4b896; margin-top: 0;">📅 Hasil Offset</h3>
                        <p style="color: #f0e6d0; font-size: 1.1rem;">
                            <b>{int(ny)}-{int(nm):02d}-{int(nd):02d}</b>
                            &nbsp;·&nbsp; KA: <b>{format_ka(res['ka'])}</b>
                            &nbsp;·&nbsp; Wuku: <b>{res['wuku_name']}</b>
                        </p>
                        <p style="color: #8899bb; font-size: 0.9rem;">
                            Wara: {res['wara_triple_full']} &nbsp;·&nbsp;
                            Hari ke-{res['day_in_wuku']}/7 &nbsp;·&nbsp;
                            TU-PA-Ā: {'✅' if res['is_tu_pa_a'] else '❌'}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    ka0 = mech_engine.date_to_ka(int(year0), int(month0), int(day0))
                    st.write(f"**KA awal:** {format_ka(ka0)} → **KA baru:** {format_ka(res['ka'])} (selisih: {res['ka'] - ka0:,} hari)")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ============================================================================
# GLOBAL FOOTER
# ============================================================================
st.markdown("""
<div class="global-footer">
    <b>OSS ΩLDJAVA-astro</b> &nbsp;·&nbsp; Open Source &nbsp;·&nbsp; 
    Data: IMCCE VSOP87D / SYRTE ELP2000-82B &nbsp;·&nbsp; 
    Prasasti: Damais (1955) – BEFEO 47.1 &nbsp;·&nbsp; 
    <a href="https://github.com/rakawi182/OSS" target="_blank">GitHub</a> &nbsp;·&nbsp;
    Jolotundo Research Consortium
</div>
""", unsafe_allow_html=True)

# ============================================================================
# END OF FILE
# ============================================================================