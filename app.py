# ============================================================================
# app.py - OSS OLDJAVA-astro Web Application
# Open Source System for Old Javanese Archaeoastronomy
# Streamlit Cloud Deployment Ready
# ============================================================================
"""
OSS OLDJAVA-astro – Open Source System for Old Javanese Archaeoastronomy
Akses publik melalui browser cloud (Streamlit Cloud / Hugging Face Spaces)
"""

import sys
import os
import time
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# STREAMLIT IMPORTS
# ============================================================================
import streamlit as st

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="OSS OLDJAVA-astro – Open Source Old Javanese Astronomy",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS – dark theme professional
# ============================================================================
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0e1117;
    }
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #f0e6d0 !important;
        font-family: 'Georgia', serif;
    }
    /* Sidebar */
    .css-1d391kg, .css-12oz5g7 {
        background-color: #1a1e2a;
    }
    /* Cards */
    .jae-card {
        background: linear-gradient(145deg, #1e2230, #151926);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #2a3040;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        margin-bottom: 16px;
    }
    .jae-card h3 {
        color: #d4b896;
        border-bottom: 1px solid #2a3040;
        padding-bottom: 8px;
        margin-bottom: 12px;
    }
    /* Metric boxes */
    .metric-box {
        background: #1a1e2a;
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 3px solid #d4b896;
        margin: 4px 0;
    }
    .metric-label {
        color: #8899bb;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #f0e6d0;
        font-size: 1.1rem;
        font-weight: 600;
        font-family: 'Courier New', monospace;
    }
    /* Tables */
    .dataframe {
        background: #1a1e2a !important;
        border-radius: 8px !important;
        border: 1px solid #2a3040 !important;
    }
    .dataframe th {
        background: #252b3d !important;
        color: #d4b896 !important;
        font-weight: 600 !important;
    }
    .dataframe td {
        color: #c0c8d8 !important;
    }
    /* Buttons */
    .stButton button {
        background: #2a3040 !important;
        color: #f0e6d0 !important;
        border: 1px solid #3a4050 !important;
        border-radius: 8px !important;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background: #3a4050 !important;
        border-color: #d4b896 !important;
    }
    /* Expanders */
    .streamlit-expanderHeader {
        background: #1a1e2a !important;
        color: #d4b896 !important;
        border-radius: 8px !important;
    }
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: #1a1e2a;
        border-radius: 8px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #8899bb;
        border-radius: 6px;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background: #2a3040 !important;
        color: #f0e6d0 !important;
    }
    /* Status indicators */
    .status-good { color: #6fcf97; }
    .status-warn { color: #f2c94a; }
    .status-bad { color: #eb5757; }
    /* Footer */
    .footer {
        text-align: center;
        color: #556688;
        font-size: 0.75rem;
        padding: 20px 0 10px 0;
        border-top: 1px solid #1a1e2a;
        margin-top: 30px;
    }
    /* OSS branding */
    .oss-badge {
        display: inline-block;
        background: #2a3040;
        color: #d4b896;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        letter-spacing: 1px;
        border: 1px solid #3a4050;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INIT
# ============================================================================
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_year = datetime.now().year
    st.session_state.current_month = datetime.now().month
    st.session_state.current_day = datetime.now().day
    st.session_state.current_hour = datetime.now().hour + datetime.now().minute/60.0

# ============================================================================
# IMPORTS – with lazy loading to improve startup time
# ============================================================================
@st.cache_resource
def load_core_modules():
    """Load core modules with caching."""
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
        ΩConstants
    )
    from SPICA_v18 import ΩSthapatiSystem
    from display import print_panel, print_table, print_header, print_info

    return {
        'jrc_const': IAU2023UltraPrecision(),
        'time_sys': JRC_TimeSystem(),
        'jrc_archaeo': JRC_ArchaeoSystem(),
        'mech_engine': WukuMechanicalEngine(),
        'sthapati': ΩSthapatiSystem(verbose_startup=False),
        'CalendarConverter': CalendarConverter,
        'offset_solar_days': offset_solar_days,
        'offset_solar_months': offset_solar_months,
        'offset_solar_years': offset_solar_years,
        'offset_lunar_months': offset_lunar_months,
        'offset_lunar_years': offset_lunar_years,
        'offset_tithi': offset_tithi,
        'display_comprehensive_info': display_comprehensive_info,
        'parse_time_input': parse_time_input,
        'OldJavaNormalizer': OldJavaNormalizer,
        'AstronomicalEngine': AstronomicalEngine,
        'VedicTimeEngine': VedicTimeEngine,
        'GrahacaraAsthaEngine': GrahacaraAsthaEngine,
        'DewataMandalaEngine': DewataMandalaEngine,
        'ΩConstants': ΩConstants,
        'VSOP87SolarEngine': VSOP87SolarEngine,
        'LunarELP82Engine': LunarELP82Engine,
        'UnifiedCoordinateTransformer': UnifiedCoordinateTransformer,
        'JPLStyleTopocentricCorrections': JPLStyleTopocentricCorrections,
        'print_panel': print_panel,
        'print_table': print_table,
        'print_header': print_header,
        'print_info': print_info
    }

# ============================================================================
# LOAD MODULES
# ============================================================================
with st.spinner("⏳ Memuat OSS OLDJAVA-astro..."):
    mods = load_core_modules()
    jrc_const = mods['jrc_const']
    time_sys = mods['time_sys']
    jrc_archaeo = mods['jrc_archaeo']
    mech_engine = mods['mech_engine']
    sthapati = mods['sthapati']
    CC = mods['CalendarConverter']
    display_info = mods['display_comprehensive_info']
    parse_time = mods['parse_time_input']
    OldJavaNormalizer = mods['OldJavaNormalizer']
    AstronomicalEngine = mods['AstronomicalEngine']
    VedicTimeEngine = mods['VedicTimeEngine']
    GrahacaraAsthaEngine = mods['GrahacaraAsthaEngine']
    DewataMandalaEngine = mods['DewataMandalaEngine']
    ΩConst = mods['ΩConstants']
    offset_funcs = {
        'solar_days': mods['offset_solar_days'],
        'solar_months': mods['offset_solar_months'],
        'solar_years': mods['offset_solar_years'],
        'lunar_months': mods['offset_lunar_months'],
        'lunar_years': mods['offset_lunar_years'],
        'tithi': mods['offset_tithi']
    }

st.success("✅ Sistem siap!")

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
st.sidebar.image("https://img.icons8.com/fluency/96/000000/sun.png", width=60)
st.sidebar.title("🌙 OSS OLDJAVA-astro")
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
        "🔄 Konversi Waktu",
        "⏱️ Offset Waktu"
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.caption(f"v301.5.Ω • {datetime.now().strftime('%Y-%m-%d')}")
st.sidebar.caption("Open Source • Jolotundo Research Consortium")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def format_ka(ka):
    return f"{ka:,}".replace(',', '.')

def format_date_astro(year, month, day):
    if year <= 0:
        return f"{1-year} SM-{month:02d}-{day:02d}"
    return f"{year:04d}-{month:02d}-{day:02d}"

def get_wuku_display(ka):
    info = mech_engine.get_wuku_by_ka(ka)
    epoch = mech_engine.get_detailed_wuku_epoch_info(ka)
    return info, epoch

def show_metric(label, value, help_text=None):
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# PAGE: BERANDA
# ============================================================================
if nav == "🏠 Beranda":
    st.title("🏛️ OSS OLDJAVA-astro")
    st.markdown("""
    <div style="background: linear-gradient(145deg, #1a1e2a, #0e1117); 
                border-radius: 16px; padding: 24px; border: 1px solid #2a3040; 
                margin-bottom: 20px;">
        <p style="color: #c0c8d8; font-size: 1.05rem; line-height: 1.7;">
            <b style="color: #d4b896;">Open Source System for Old Javanese Archaeoastronomy</b> – 
            sistem terpadu untuk astronomi arkeologi Jawa Kuno.
        </p>
        <p style="color: #8899bb; font-size: 0.9rem;">
            Menggabungkan <b>JRC Ephemeris</b> (VSOP87D + ELP2000-82B), 
            <b>Wuku System</b> (210-hari), 
            <b>Old Java Astronomy</b> (Pancanga, Yoga, Karana, Lagna),
            dan <b>Ω-STHAPATI</b> (konversi prasasti Saka).
        </p>
        <div style="margin-top: 12px;">
            <span class="oss-badge">🌍 OPEN SOURCE</span>
            <span class="oss-badge" style="margin-left: 8px;">🔓 PUBLIC</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="jae-card">
            <h3>☀️ Matahari</h3>
            <p style="color: #8899bb;">Posisi presisi tinggi<br>VSOP87D + nutasi + aberasi</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="jae-card">
            <h3>🌙 Bulan</h3>
            <p style="color: #8899bb;">ELP2000-82B<br>+ topocentrik + fase</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="jae-card">
            <h3>📜 Prasasti</h3>
            <p style="color: #8899bb;">Konversi Saka→Masehi<br>+ 4 komponen utama</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="footer">
        OSS OLDJAVA-astro v301.5.Ω • Open Source • Data: JRC Ephemeris (IAU2023) • Jolotundo Observatory
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

    now = datetime.now()
    year, month, day = now.year, now.month, now.day
    hour = now.hour + now.minute/60.0 + now.second/3600.0

    st.markdown(f"""
    <div style="background: #1a1e2a; border-radius: 10px; padding: 16px; margin: 8px 0 20px 0; border-left: 4px solid #d4b896;">
        <b style="color: #d4b896;">🕐 Waktu:</b> 
        <span style="color: #f0e6d0;">{year:04d}-{month:02d}-{day:02d} {int(hour):02d}:{int((hour-int(hour))*60):02d}:{int(((hour-int(hour))*60-int((hour-int(hour))*60))*60):02d} WIB</span>
    </div>
    """, unsafe_allow_html=True)

    # Compute data
    jd_utc = time_sys.wib_to_jd_utc(year, month, day, int(hour), int((hour-int(hour))*60), int(((hour-int(hour))*60-int((hour-int(hour))*60))*60))
    jd_tt = time_sys.wib_to_jd_tt_extended(year, month, day, int(hour), int((hour-int(hour))*60), int(((hour-int(hour))*60-int((hour-int(hour))*60))*60))
    ka = mech_engine.date_to_ka(year, month, day)
    wuku_info, epoch_info = get_wuku_display(ka)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        show_metric("KA (Kali Ahargana)", format_ka(ka))
    with col2:
        show_metric("Wuku", f"{wuku_info['wuku_name']} (#{wuku_info['wuku_number']})")
    with col3:
        show_metric("Wara Triple", wuku_info['wara_triple_full'])
    with col4:
        show_metric("TU-PA-Ā", "✅ YA" if wuku_info['is_tu_pa_a'] else "❌ TIDAK")

    # JRC Ephemeris data
    with st.spinner("Menghitung ephemeris..."):
        try:
            jrc_data = jrc_archaeo.get_complete_ephemeris(
                year_astro=year, month=month, day=day,
                hour=int(hour), minute=int((hour-int(hour))*60),
                second=int(((hour-int(hour))*60-int((hour-int(hour))*60))*60),
                use_current_time=False
            )

            sun = jrc_data['sun']
            moon = jrc_data['moon']

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                <div class="jae-card">
                    <h3>☀️ Matahari</h3>
                """, unsafe_allow_html=True)
                st.metric("Altitude", f"{sun['horizontal_apparent']['altitude_deg']:.2f}°")
                st.metric("Azimuth", f"{sun['horizontal_apparent']['azimuth_deg']:.2f}°")
                st.metric("RA", f"{sun['geocentric']['equatorial']['ra_deg']:.4f}°")
                st.metric("Dec", f"{sun['geocentric']['equatorial']['dec_deg']:.4f}°")
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown("""
                <div class="jae-card">
                    <h3>🌙 Bulan</h3>
                """, unsafe_allow_html=True)
                st.metric("Altitude", f"{moon['horizontal_apparent']['altitude_deg']:.2f}°")
                st.metric("Azimuth", f"{moon['horizontal_apparent']['azimuth_deg']:.2f}°")
                st.metric("Fase", f"{moon['phase']['phase_name']}")
                st.metric("Iluminasi", f"{moon['phase']['illumination_fraction']*100:.1f}%")
                st.markdown("</div>", unsafe_allow_html=True)

            # Sunrise/Sunset
            st.markdown("""
            <div class="jae-card">
                <h3>🌅 Waktu Matahari</h3>
            """, unsafe_allow_html=True)
            sr = jrc_data['sun']['times']
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Terbit", sr.get('sunrise_wib', '--:--:--'))
            with c2:
                st.metric("Transit", sr.get('transit_wib', '--:--:--'))
            with c3:
                st.metric("Terbenam", sr.get('sunset_wib', '--:--:--'))
            st.metric("Panjang Siang", f"{sr.get('day_length_hours', 0):.2f} jam")
            st.markdown("</div>", unsafe_allow_html=True)

            # Moon rise/set
            mr = moon.get('times', {})
            if mr and 'error' not in mr:
                st.markdown("""
                <div class="jae-card">
                    <h3>🌙 Waktu Bulan</h3>
                """, unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Terbit", mr.get('moonrise', {}).get('wib', '--:--:--'))
                with c2:
                    st.metric("Transit", mr.get('transit', {}).get('wib', '--:--:--'))
                with c3:
                    st.metric("Terbenam", mr.get('moonset', {}).get('wib', '--:--:--'))
                st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Error menghitung ephemeris: {str(e)}")

    # Wuku details expander
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

    col1, col2, col3 = st.columns(3)
    with col1:
        year = st.number_input("Tahun", value=2024, step=1, format="%d")
    with col2:
        month = st.selectbox("Bulan", list(range(1, 13)), index=datetime.now().month-1)
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
                # Compute basic data
                jd_utc = time_sys.wib_to_jd_utc(year, month, day, int(hour), int((hour-int(hour))*60), int(((hour-int(hour))*60-int((hour-int(hour))*60))*60))
                jd_tt = time_sys.wib_to_jd_tt_extended(year, month, day, int(hour), int((hour-int(hour))*60), int(((hour-int(hour))*60-int((hour-int(hour))*60))*60))
                ka = mech_engine.date_to_ka(year, month, day)
                wuku_info, epoch_info = get_wuku_display(ka)

                # Display metrics
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    show_metric("KA", format_ka(ka))
                with c2:
                    show_metric("Wuku", f"{wuku_info['wuku_name']} (#{wuku_info['wuku_number']})")
                with c3:
                    show_metric("Wara Triple", wuku_info['wara_triple_full'])
                with c4:
                    show_metric("TU-PA-Ā", "✅" if wuku_info['is_tu_pa_a'] else "❌")

                # JRC Ephemeris
                jrc_data = jrc_archaeo.get_complete_ephemeris(
                    year_astro=year, month=month, day=day,
                    hour=int(hour), minute=int((hour-int(hour))*60),
                    second=int(((hour-int(hour))*60-int((hour-int(hour))*60))*60),
                    use_current_time=False
                )

                sun = jrc_data['sun']
                moon = jrc_data['moon']

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("""
                    <div class="jae-card">
                        <h3>☀️ Matahari</h3>
                    """, unsafe_allow_html=True)
                    st.metric("Altitude", f"{sun['horizontal_apparent']['altitude_deg']:.2f}°")
                    st.metric("Azimuth", f"{sun['horizontal_apparent']['azimuth_deg']:.2f}°")
                    st.metric("RA", f"{sun['geocentric']['equatorial']['ra_deg']:.4f}°")
                    st.metric("Dec", f"{sun['geocentric']['equatorial']['dec_deg']:.4f}°")
                    st.markdown("</div>", unsafe_allow_html=True)

                with col2:
                    st.markdown("""
                    <div class="jae-card">
                        <h3>🌙 Bulan</h3>
                    """, unsafe_allow_html=True)
                    st.metric("Altitude", f"{moon['horizontal_apparent']['altitude_deg']:.2f}°")
                    st.metric("Azimuth", f"{moon['horizontal_apparent']['azimuth_deg']:.2f}°")
                    st.metric("Fase", f"{moon['phase']['phase_name']}")
                    st.metric("Iluminasi", f"{moon['phase']['illumination_fraction']*100:.1f}%")
                    st.markdown("</div>", unsafe_allow_html=True)

                # Expand with Old Java details
                with st.expander("📖 Pancanga & Vedic Time (Old Java Astronomy)", expanded=True):
                    try:
                        # Use Old Java display function
                        import io
                        import contextlib
                        f = io.StringIO()
                        with contextlib.redirect_stdout(f):
                            display_info(year, month, day, hour)
                        output = f.getvalue()
                        st.text(output)
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
                _display_wuku_detail(info, epoch, ka_input)
        else:
            y = st.number_input("Tahun", value=2024, step=1, format="%d")
            m = st.selectbox("Bulan", list(range(1, 13)), index=0)
            d = st.number_input("Hari", value=1, min_value=1, max_value=31, step=1)
            if st.button("Cari Tanggal"):
                ka = mech_engine.date_to_ka(y, m, d)
                info = mech_engine.get_wuku_by_ka(ka)
                epoch = mech_engine.get_detailed_wuku_epoch_info(ka)
                st.info(f"KA: {format_ka(ka)}")
                _display_wuku_detail(info, epoch, ka)

    with tab2:
        st.subheader("📍 TU-PA-Ā (Tungleh-Pahing-Aditya)")
        st.caption("Hari pertama siklus wuku, referensi absolut")

        tpa_year = st.number_input("Tahun untuk mencari TU-PA-Ā", value=2024, step=1, format="%d")
        if st.button("🔍 Cari TU-PA-Ā di tahun ini"):
            tpa_list = mech_engine.find_tu_pa_a_in_year(tpa_year)
            if tpa_list:
                data = []
                for tpa in tpa_list:
                    y, m, d = tpa['date']
                    data.append({
                        "Tanggal": f"{int(y)}-{int(m):02d}-{int(d):02d}",
                        "KA": format_ka(tpa['ka']),
                        "Wuku": tpa['wuku_info']['wuku_name'],
                        "Wara": tpa['wuku_info']['wara_triple']
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

def _display_wuku_detail(info, epoch, ka):
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

# ============================================================================
# PAGE: KONVERSI PRASASTI
# ============================================================================
elif nav == "📜 Konversi Prasasti":
    st.title("📜 Konversi Prasasti Saka → Masehi")
    st.caption("Ω-STHAPATI v301.4 – 4 komponen utama: Tahun, Bulan, Wara, Wuku")

    with st.expander("📖 Panduan Input", expanded=False):
        st.markdown("""
        **Field yang diperlukan:**
        - **Tahun Śaka:** tahun dalam penanggalan Saka
        - **Bulan Śaka:** Caitra, Vaisakha, Jyestha, Asadha, Sravana, Bhadrapada,
          Asvini, Kartika, Margasira, Pausa, Magha, Phalguna
        - **Tithi:** 1-30
        - **Paksa:** Sukla atau Krsna
        - **Wuku:** (opsional) nama wuku
        - **Wara:** (opsional) bisa lengkap (Tungleh-Pahing-Aditya) atau parsial (Jumat-Wage)

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
        tithi = st.number_input("Tithi (1-30)", value=12, min_value=1, max_value=30, step=1)
        paksa = st.selectbox("Paksa", ["Sukla", "Krsna"], index=0)

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
                        'saka_year': int(saka_year),
                        'masa': masa,
                        'tithi': int(tithi),
                        'paksa': paksa,
                        'wuku': wuku if wuku else "",
                        'wara_string': wara if wara else "",
                        'nakshatra': nakshatra if nakshatra else ""
                    }

                    results = sthapati.convert_prasasti_with_smart_parsing(data, verbose=False)

                    if not results:
                        st.error("❌ Tidak ditemukan kandidat yang valid.")
                    else:
                        st.success(f"✅ Ditemukan {len(results)} kandidat")

                        # Best candidate
                        best = results[0]
                        cand = best['candidate']
                        y, m, d = cand['date']

                        st.markdown(f"""
                        <div style="background: #1a1e2a; border-radius: 12px; padding: 20px; border: 1px solid #d4b896; margin: 12px 0;">
                            <h3 style="color: #d4b896; margin-top: 0;">✨ Kandidat Terbaik</h3>
                            <p style="color: #f0e6d0; font-size: 1.2rem;">
                                <b>{int(y)}-{int(m):02d}-{int(d):02d}</b>
                                &nbsp;·&nbsp; KA: <b>{format_ka(cand['ka'])}</b>
                                &nbsp;·&nbsp; Wuku: <b>{cand['wuku_info']['wuku_name']}</b>
                            </p>
                            <p style="color: #8899bb;">
                                Skor: {best['score']:.3f} &nbsp;·&nbsp; Confidence: {best['confidence']}
                                &nbsp;·&nbsp; Wara: {cand['wuku_info']['wara_triple_full']}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                        # Table of top candidates
                        table_data = []
                        for i, res in enumerate(results[:5]):
                            c = res['candidate']
                            yy, mm, dd = c['date']
                            table_data.append({
                                "Rank": i+1,
                                "Tanggal": f"{int(yy)}-{int(mm):02d}-{int(dd):02d}",
                                "KA": format_ka(c['ka']),
                                "Wuku": c['wuku_info']['wuku_name'],
                                "Wara": c['wuku_info']['wara_triple'],
                                "Skor": f"{res['score']:.3f}",
                                "Confidence": res['confidence']
                            })
                        st.dataframe(table_data, use_container_width=True)

                        # Verification against input
                        st.markdown("""
                        <div class="jae-card">
                            <h3>🔍 Verifikasi Input</h3>
                        """, unsafe_allow_html=True)

                        # Tithi verification
                        tithi_input = data.get('tithi')
                        paksa_input = data.get('paksa')
                        if tithi_input and paksa_input:
                            # Get tithi from Old Java for the candidate date
                            hh = 12
                            try:
                                astro_engine = AstronomicalEngine()
                                jd_tt_calc = time_sys.wib_to_jd_tt_extended(int(y), int(m), int(d), hh, 0, 0)
                                sun_data = astro_engine.calculate_sun_position_ultra(jd_tt_calc)
                                moon_data = astro_engine.calculate_moon_position_ultra(jd_tt_calc, sun_data['longitude_deg'])
                                ayanamsa = astro_engine.calculate_ayanamsa_precise(jd_tt_calc)
                                sun_nirayana = (sun_data['longitude_deg'] - ayanamsa) % 360
                                moon_nirayana = (moon_data['longitude'] - ayanamsa) % 360
                                tithi_calc = astro_engine.calculate_tithi(sun_nirayana, moon_nirayana, "nirayana")

                                st.write(f"**Tithi input:** {tithi_input} {paksa_input}")
                                st.write(f"**Tithi hitung:** {tithi_calc['tithi']} {tithi_calc['paksa']}")

                                if tithi_input == tithi_calc['tithi'] and paksa_input.lower() == tithi_calc['paksa'].lower():
                                    st.success("✅ Tithi cocok persis")
                                elif abs(tithi_input - tithi_calc['tithi']) <= 1 and paksa_input.lower() == tithi_calc['paksa'].lower():
                                    st.warning(f"⚠️ Tithi cocok dengan toleransi 1 (selisih {abs(tithi_input - tithi_calc['tithi'])})")
                                else:
                                    st.error("❌ Tithi tidak cocok")

                                # Nakshatra verification
                                naks_input = data.get('nakshatra')
                                if naks_input:
                                    old_norm = OldJavaNormalizer()
                                    naks_norm = old_norm.normalize(naks_input)
                                    naks_calc = astro_engine.calculate_nakshatra(moon_nirayana, "nirayana")
                                    st.write(f"**Nakṣatra input:** {naks_norm}")
                                    st.write(f"**Nakṣatra hitung (Nirayana):** {naks_calc['nakshatra']}")
                                    if naks_norm == naks_calc['nakshatra']:
                                        st.success("✅ Nakṣatra cocok (Nirayana)")
                                    else:
                                        st.warning("⚠️ Nakṣatra tidak cocok (cek ejaan atau sistem)")

                            except Exception as e:
                                st.warning(f"Tidak dapat verifikasi tithi/naksatra: {str(e)}")

                        st.markdown("</div>", unsafe_allow_html=True)

                        # Show 4 components evaluation
                        with st.expander("📊 Evaluasi 4 Komponen Utama", expanded=False):
                            try:
                                # Re-run with verbose to capture evaluation
                                import io
                                import contextlib
                                f = io.StringIO()
                                with contextlib.redirect_stdout(f):
                                    sthapati.display_main_components_evaluation(results)
                                st.text(f.getvalue())
                            except Exception as e:
                                st.warning(f"Tidak dapat menampilkan evaluasi: {str(e)}")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE: KONVERSI WAKTU
# ============================================================================
elif nav == "🔄 Konversi Waktu":
    st.title("🔄 Konversi Waktu")
    st.caption("JD, KA, Gregorian, Julian – konversi antar sistem")

    tab1, tab2, tab3, tab4 = st.tabs(["📅 Tanggal → JD/KA", "📊 JD → Tanggal/KA", "📊 KA → Tanggal/JD", "📆 Gregorian ↔ Julian"])

    with tab1:
        y = st.number_input("Tahun", value=2024, step=1, format="%d", key="conv_t1_y")
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
        yg = st.number_input("Tahun Gregorian", value=2024, step=1, format="%d", key="conv_t4_yg")
        mg = st.selectbox("Bulan", list(range(1, 13)), index=0, key="conv_t4_mg")
        dg = st.number_input("Hari", value=1, min_value=1, max_value=31, step=1, key="conv_t4_dg")
        if st.button("→ Julian", key="conv_t4_btn1"):
            jd = CC.gregorian_to_jd(int(yg), int(mg), int(dg))
            yj, mj, dj = CC.jd_to_julian(jd)
            st.write(f"**Julian:** {int(yj):04d}-{int(mj):02d}-{int(dj):02d}")

        st.subheader("Julian → Gregorian")
        yj2 = st.number_input("Tahun Julian", value=2024, step=1, format="%d", key="conv_t4_yj")
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
        year0 = st.number_input("Tahun awal", value=2024, step=1, format="%d", key="off_y")
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

                if 'error' in res:
                    st.error(f"❌ {res['error']}")
                else:
                    ny, nm, nd = res['date']
                    st.markdown(f"""
                    <div style="background: #1a1e2a; border-radius: 12px; padding: 20px; border: 1px solid #d4b896; margin: 12px 0;">
                        <h3 style="color: #d4b896; margin-top: 0;">📅 Hasil Offset</h3>
                        <p style="color: #f0e6d0; font-size: 1.1rem;">
                            <b>{int(ny)}-{int(nm):02d}-{int(nd):02d}</b>
                            &nbsp;·&nbsp; KA: <b>{format_ka(res['ka'])}</b>
                            &nbsp;·&nbsp; Wuku: <b>{res['wuku_name']}</b>
                        </p>
                        <p style="color: #8899bb;">
                            Wara: {res['wara_triple_full']} &nbsp;·&nbsp;
                            Hari ke-{res['day_in_wuku']}/7 &nbsp;·&nbsp;
                            TU-PA-Ā: {'✅' if res['is_tu_pa_a'] else '❌'}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Show comparison
                    ka0 = mech_engine.date_to_ka(int(year0), int(month0), int(day0))
                    st.write(f"**KA awal:** {format_ka(ka0)} → **KA baru:** {format_ka(res['ka'])} (selisih: {res['ka'] - ka0:,} hari)")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ============================================================================
# FOOTER
# ============================================================================
st.sidebar.markdown("---")
st.sidebar.caption("🌏 Jolotundo, Indonesia")
st.sidebar.caption(f"📍 {ΩConst.LOC_LAT:.4f}°, {ΩConst.LOC_LON:.4f}°")

# Run with: streamlit run app.py