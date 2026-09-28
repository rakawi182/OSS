#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
astro_smart_parser_experimental.py
================================================================================
ASTRONOMICAL SMART PARSER
Modul verifikasi astronomis independen untuk Ω-STHAPATI v301.4
================================================================================

Latar Belakang
--------------
Sistem Ω-STHAPATI (SPICA_v18.py) mengonversi prasasti Saka Jawa Kuno ke
kalender Masehi melalui jalur mekanik berbasis wara-wuku (siklus 210 hari).
Jalur ini deterministik, presisi absolut, dan telah terverifikasi 100% pada
112 prasasti Damais. Namun jalur ini bergantung mutlak pada keberadaan
wara_string sebagai anchor (indeks absolut dalam siklus).

Modul ini menyediakan jalur independen berbasis astronomi murni — menggunakan
VSOP87D (Matahari) dan ELP82B (Bulan) — untuk tiga tujuan:

  1. Sebagai jalur alternatif ketika wara tidak tersedia.
  2. Sebagai cross-verifier independen ketika wara tersedia.
  3. Sebagai fallback ketika jalur mekanik gagal.

Arsitektur Tiga Jalur (Dispatcher)
----------------------------------
    Jalur 1 — Mekanik murni     : wara ada, astronomi tidak ada
    Jalur 2 — Astronomis murni  : wara tidak ada, astronomi ada
    Jalur 3 — Cross-verifikasi  : keduanya ada

Jalur 1 tetap menggunakan SPICA tanpa modifikasi. Modul ini tidak menyentuh
SPICA_v18.py maupun modul lain.

Skema Skor (Proporsional)
-------------------------
Untuk setiap field astronomi yang tersedia (tithi, nakshatra, yoga, karana),
kandidat menerima nilai parsial:

    exact (diff = 0)      →  1.0
    near  (diff = 1)      →  0.4
    miss  (diff > 1)      →  0.0

Skor akhir = sum(partial) / n_available

Skema proporsional ini membuat skor selalu berada di rentang [0.0, 1.0],
terlepas dari berapa field yang tersedia. Confidence dihitung dari skor
dan jumlah bukti (n_match vs n_available).

Sistem Ganda (Sayana / Nirayana)
--------------------------------
Sebagian field bersifat invariant terhadap ayanamsa, sebagian tidak:

    Invariant  : tithi, karana, paksa (berbasis elongasi)
    Bergantung : nakshatra, yoga        (berbasis posisi absolut)

Untuk nakshatra dan yoga, kandidat diuji di kedua sistem (sayana dan
nirayana) dan diambil yang terbaik. Sistem yang menang dicatat untuk
keperluan diagnostik.

Sampling dan Konvensi Hari
--------------------------
Acuan hari = state astronomis pada sunrise (06:00 WIB). Konvensi ini
mendekati praktik penyusunan prasasti Jawa Kuno. Untuk mendeteksi hari-hari
batas (ketika tithi atau nakshatra berganti di tengah hari), tiga jam
sampling digunakan (06:00, 12:00, 18:00 WIB). Hasil stability hanya
digunakan sebagai anotasi, bukan penalti.

Window Scan dan Ambiguitas Bawaan
---------------------------------
Window scan ditentukan dari tabel SAKA_MONTH_TO_JULIAN_RANGE di SPICA
(1–2 bulan Julian per masa). Window ±60 hari ini menyisakan satu kelemahan
yang secara sadar diterima sebagai batas desain:

    Dalam window 60 hari, tithi yang sama muncul 2× (jarak ~29,5 hari).
    Keduanya mendapat skor identik. Sistem tidak dapat membedakan tanpa
    anchor tambahan (wara). Ini bukan bug, melainkan konsekuensi resolusi
    astronomis murni.

Selisih ±1 bulan Julian juga diterima sebagai konsekuensi inkonsistensi
historis sistem interkalasi. Selisih 1 tithi ditoleransi (konvensi awal
tithi yang berbeda antar sumber).

Batasan
-------
- Modul ini bukan pengganti SPICA mekanik. Ia adalah jalur independen
  yang saling melengkapi.
- Tidak ada fuzzy matching. Normalisasi ejaan menggunakan dict statis.
- Tidak ada pencarian new moon. Ambiguitas bulan lunar dibiarkan eksplisit.
- Tidak ada adhika-masa handling. Interkalasi hanya dari data eksplisit
  yang sudah ada di SPICA.

Output
------
Setiap kandidat dikembalikan dalam format yang kompatibel dengan SPICA:

    {
        'candidate'      : {ka, date, wuku_info, i, s, ...},
        'score'          : float,
        'confidence'     : 'TINGGI' | 'SEDANG' | 'RENDAH' | 'DITOLAK',
        'n_available'    : int,
        'n_match'        : int,
        'match_breakdown': dict,
        'matched_systems': dict,
        'astro_state'    : dict (state lengkap pada hari itu),
        'stability'      : dict (info stabilitas harian),
        'boundary_flags' : list,
        'is_strongest'   : bool (True untuk rank #1),
        'rank'           : int,
    }

Referensi
---------
- Bretagnon & Francou (1988) — VSOP87D
- Chapront-Touzé & Chapront (1983) — ELP2000-82B
- Damais, L.-C. — Études d'épigraphie indonésienne (1951–1957)
- IERS Conventions (2010) — nutation IAU 2000A

Penulis
-------
Jolotundo Research Consortium
================================================================================
"""

from __future__ import annotations

import heapq
from typing import Optional, List, Dict, Any, Iterator, Tuple

from SPICA_v18 import MathCore, ΩConstants, ΩSthapatiSystem
from JRC_Ephemeris import (
    VSOP87SolarEngine,
    LunarELP82Engine,
    TimeSystem as JRC_TimeSystem,
    HighPrecisionNutation,
)


# =============================================================================
# BAGIAN 1 — TABEL NAMA STANDAR
# -----------------------------------------------------------------------------
# Nama-nama kanonik untuk field astronomis. Digunakan sebagai referensi
# indexing dan untuk menampilkan state ke pengguna.
# =============================================================================

NAKSHATRA_NAMES: List[str] = [
    "Aswini", "Bharani", "Krittika", "Rohini", "Mrigasira", "Ardra",
    "Punarvasu", "Pushya", "Aslesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Visakha",
    "Anuradha", "Jyestha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Sravana", "Dhanistha", "Satabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]

YOGAS: List[str] = [
    "Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Sobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva",
    "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan",
    "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
    "Brahma", "Indra", "Vaidhriti",
]

KARANA_CYCLE_7: List[str] = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
]
KARANA_SPECIAL_HEAD: str = "Kimstughna"
KARANA_SPECIAL_TAIL: List[str] = ["Sakuni", "Catuspada", "Naga"]


# =============================================================================
# BAGIAN 2 — TABEL VARIAN EJAAN
# -----------------------------------------------------------------------------
# Prasasti Jawa Kuno memiliki banyak varian ejaan — campuran Sanskerta,
# Jawa Kuno, dan pengaruh lokal. Tabel-tabel di bawah ini memetakan varian
# ke bentuk kanonik. Pencocokan bersifat exact-match (dict lookup) —
# tidak ada fuzzy matching, untuk menjaga konsumsi memori tetap rendah.
# =============================================================================

NAKSHATRA_VARIANTS: Dict[str, List[str]] = {
    "Aswini": ["Aswini", "Asvini", "Asuji", "Asvij", "Aswi"],
    "Bharani": ["Bharani", "Barani"],
    "Krittika": ["Krittika", "Kartika", "Krtika"],
    "Rohini": ["Rohini"],
    "Mrigasira": ["Mrigasira", "Margasira", "Mrgasira"],
    "Ardra": ["Ardra"],
    "Punarvasu": ["Punarvasu"],
    "Pushya": ["Pushya", "Pusya", "Tisya"],
    "Aslesha": ["Aslesha", "Aslesa", "Ashlesha"],
    "Magha": ["Magha", "Maga"],
    "Purva Phalguni": ["Purva Phalguni", "Purwa Palguna", "Purvaphalguni"],
    "Uttara Phalguni": ["Uttara Phalguni", "Utara Palguna", "Uttaraphalguni"],
    "Hasta": ["Hasta"],
    "Chitra": ["Chitra", "Citra"],
    "Swati": ["Swati"],
    "Visakha": ["Visakha", "Vishakha", "Wesakha", "Besakha"],
    "Anuradha": ["Anuradha"],
    "Jyestha": ["Jyestha", "Jyeshtha", "Jyesta", "Jestha", "Yestha"],
    "Mula": ["Mula"],
    "Purva Ashadha": ["Purva Ashadha", "Purwa Asada", "Purvasadha"],
    "Uttara Ashadha": ["Uttara Ashadha", "Utara Asada", "Uttarasadha"],
    "Sravana": ["Sravana", "Srawana"],
    "Dhanistha": ["Dhanistha", "Danista", "Dhanishta"],
    "Satabhisha": ["Satabhisha", "Satabisa", "Shatabhisha"],
    "Purva Bhadrapada": ["Purva Bhadrapada", "Purwa Badra", "Purvabhadrapada"],
    "Uttara Bhadrapada": ["Uttara Bhadrapada", "Utara Badra",
                          "Uttarabadra", "Uttarabhadrapada"],
    "Revati": ["Revati", "Rewati"],
}

YOGA_VARIANTS: Dict[str, List[str]] = {
    "Vishkumbha": ["Vishkumbha", "Wiskambha", "Viskambha", "Wiskumbha"],
    "Priti": ["Priti"],
    "Ayushman": ["Ayushman", "Ayusman"],
    "Saubhagya": ["Saubhagya", "Sobhagya"],
    "Sobhana": ["Sobhana", "Shobhana"],
    "Atiganda": ["Atiganda"],
    "Sukarma": ["Sukarma", "Sukarmma", "Shukarma"],
    "Dhriti": ["Dhriti", "Dhrti"],
    "Shula": ["Shula", "Sula"],
    "Ganda": ["Ganda"],
    "Vriddhi": ["Vriddhi", "Wrddhi", "Vrddhi"],
    "Dhruva": ["Dhruva", "Dhruwa"],
    "Vyaghata": ["Vyaghata", "Byatipada", "Wyaghata", "Wyatighata"],
    "Harshana": ["Harshana", "Harsana"],
    "Vajra": ["Vajra", "Bajra", "Wajra"],
    "Siddhi": ["Siddhi"],
    "Vyatipata": ["Vyatipata", "Wyatipata", "Byatipata"],
    "Variyan": ["Variyan", "Wariyan"],
    "Parigha": ["Parigha"],
    "Shiva": ["Shiva", "Siwa"],
    "Siddha": ["Siddha"],
    "Sadhya": ["Sadhya"],
    "Shubha": ["Shubha", "Subha"],
    "Shukla": ["Shukla", "Sukla"],
    "Brahma": ["Brahma"],
    "Indra": ["Indra"],
    "Vaidhriti": ["Vaidhriti", "Waidhrti", "Vaidhrti", "Waidhriti", "Wedhrti"],
}

KARANA_VARIANTS: Dict[str, List[str]] = {
    "Kimstughna": ["Kimstughna", "Kistughna", "Kistugna", "Kimstugna"],
    "Bava": ["Bava", "Wawa", "Vava", "Bawa"],
    "Balava": ["Balava", "Walawa", "Balawa"],
    "Kaulava": ["Kaulava", "Kolawa", "Kulava"],
    "Taitila": ["Taitila", "Taitilla", "Tetila"],
    "Gara": ["Gara", "Garadi"],
    "Vanija": ["Vanija", "Wanija", "Banija"],
    "Vishti": ["Vishti", "Wisti", "Wishti", "Vishtih"],
    "Sakuni": ["Sakuni", "Cakuni"],
    "Catuspada": ["Catuspada", "Chatuspada"],
    "Naga": ["Naga"],
}


def _build_rev(variants_dict: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Bangun kamus reverse: lowercase varian → bentuk kanonik.

    Operasi satu kali saat inisialisasi parser. Ukuran total ±150 entri.
    """
    rev: Dict[str, str] = {}
    for std, variants in variants_dict.items():
        for v in variants:
            rev[v.lower().strip()] = std
    return rev


# =============================================================================
# BAGIAN 3 — KALKULATOR STATE ASTRONOMIS
# -----------------------------------------------------------------------------
# Komponen ini menjembatani modul JRC_Ephemeris (VSOP87D + ELP82B) dengan
# parser. Tanggung jawabnya tunggal: diberikan satu momen dalam UTC,
# menghasilkan snapshot lengkap state astronomis — tithi, nakshatra, yoga,
# karana — dalam kedua sistem (sayana dan nirayana).
# =============================================================================

class AstroStateCalculator:
    """
    Kalkulator state astronomis pada satu momen UTC.

    Menyediakan kedua sistem sekaligus:
      - Sayana   : koordinat tropis apa adanya
      - Nirayana : koordinat sidereal (dikurangi ayanamsa)

    Tithi, karana, dan paksa bersifat invariant terhadap ayanamsa karena
    keduanya berbasis elongasi (Moon − Sun). Nakshatra dan yoga bergantung
    pada posisi absolut dan dihitung untuk kedua sistem.

    Parameters
    ----------
    None — semua engine diinisialisasi internal.

    Notes
    -----
    - Sun  : menggunakan VSOP87D via JRC (koordinat apparent).
    - Moon : menggunakan ELP82B via JRC (koordinat apparent).
    - Ayanamsa: model Lahiri sederhana dengan koreksi nutasi.
    """

    def __init__(self) -> None:
        self.time_sys = JRC_TimeSystem()
        self.sun_calc = VSOP87SolarEngine()
        self.moon_calc = LunarELP82Engine()
        self.nutation = HighPrecisionNutation()

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def state_at(self, jd_utc: float) -> Dict[str, Any]:
        """
        Hitung state astronomis lengkap pada satu momen UTC.

        Parameters
        ----------
        jd_utc : float
            Julian Day dalam skala UTC.

        Returns
        -------
        dict
            Snapshot lengkap dengan field-field berikut:

            Invariant (sama di kedua sistem):
                tithi_abs         : int   1..30 (Sukla 1..15, Krsna 1..15)
                karana_name       : str   nama karana (11-nama klasik)
                elongation_deg    : float elongasi Bulan−Matahari (0..360)
                ayanamsa          : float derajat

            Dual-system:
                nakshatra_sayana_idx      : int  1..27
                nakshatra_nirayana_idx    : int  1..27
                nakshatra_sayana_name     : str
                nakshatra_nirayana_name   : str
                yoga_sayana_idx           : int  1..27
                yoga_nirayana_idx         : int  1..27
                yoga_sayana_name          : str
                yoga_nirayana_name        : str

            Raw:
                sun_sayana, sun_nirayana, moon_sayana, moon_nirayana : float
                jd_tt, jd_utc : float
        """
        jd_tt = self.time_sys.jd_utc_to_tt_extended(jd_utc)

        sun = self.sun_calc.calculate_sun_position_vsop87d(
            jd_tt, 'equatorial_apparent'
        )
        moon = self.moon_calc.calculate_position(
            jd_utc, output_frame='equatorial_apparent'
        )

        ayanamsa = self._ayanamsa(jd_tt)

        sun_trop = sun['longitude_deg'] % 360.0
        moon_trop = moon['ecliptic_apparent']['longitude_deg'] % 360.0
        sun_nir = (sun_trop - ayanamsa) % 360.0
        moon_nir = (moon_trop - ayanamsa) % 360.0

        elong = (moon_trop - sun_trop) % 360.0
        tithi_abs = int(elong / 12.0) + 1
        karana_name = self._karana_name_from_elong(elong)

        naks_say = int(moon_trop / (360.0 / 27.0)) + 1
        naks_nir = int(moon_nir / (360.0 / 27.0)) + 1

        yoga_say = int(((sun_trop + moon_trop) % 360.0) / (360.0 / 27.0)) + 1
        yoga_nir = int(((sun_nir + moon_nir) % 360.0) / (360.0 / 27.0)) + 1

        return {
            'tithi_abs': tithi_abs,
            'karana_name': karana_name,
            'elongation_deg': elong,
            'ayanamsa': ayanamsa,
            'nakshatra_sayana_idx': naks_say,
            'nakshatra_nirayana_idx': naks_nir,
            'nakshatra_sayana_name': NAKSHATRA_NAMES[naks_say - 1],
            'nakshatra_nirayana_name': NAKSHATRA_NAMES[naks_nir - 1],
            'yoga_sayana_idx': yoga_say,
            'yoga_nirayana_idx': yoga_nir,
            'yoga_sayana_name': YOGAS[yoga_say - 1],
            'yoga_nirayana_name': YOGAS[yoga_nir - 1],
            'sun_sayana': sun_trop,
            'sun_nirayana': sun_nir,
            'moon_sayana': moon_trop,
            'moon_nirayana': moon_nir,
            'jd_tt': jd_tt,
            'jd_utc': jd_utc,
        }

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _karana_name_from_elong(elong_deg: float) -> str:
        """
        Konversi elongasi (0..360) ke nama karana (11-nama klasik).

        Skema klasik dalam satu bulan sinodik (60 karana):
            idx60 = 0        → Kimstughna
            idx60 = 1..56    → Bava..Vishti (siklus 7, berulang 8×)
            idx60 = 57..59   → Sakuni, Catuspada, Naga
        """
        idx60 = int(elong_deg / 6.0)
        if idx60 == 0:
            return KARANA_SPECIAL_HEAD
        if idx60 >= 57:
            return KARANA_SPECIAL_TAIL[idx60 - 57]
        return KARANA_CYCLE_7[(idx60 - 1) % 7]

    def _ayanamsa(self, jd_tt: float) -> float:
        """
        Ayanamsa Lahiri sederhana dengan koreksi nutasi.

        Model linear dari epoch J2000, disesuaikan dengan koreksi dPsi
        (nutasi in longitude) untuk presisi orde orde arkeoastronomi.
        """
        T = (jd_tt - 2451545.0) / 36525.0
        mean_ay = 23.856858 + 1.3969712777777778 * T
        dPsi_deg, _ = self.nutation.compute(T)
        return (mean_ay + dPsi_deg) % 360.0


# =============================================================================
# BAGIAN 4 — PARSER ASTRONOMIS
# -----------------------------------------------------------------------------
# Komponen inti. Melakukan scan window, mengevaluasi setiap hari,
# dan mengembalikan daftar kandidat dalam format yang kompatibel dengan SPICA.
# =============================================================================

class AstronomicalSmartParser:
    """
    Parser berbasis astronomi murni.

    Alur kerja:
        1. Resolusi target dari input prasasti (tithi, nakshatra, yoga, karana)
        2. Tentukan window scan berdasarkan masa (bulan Julian dari SPICA)
        3. Iterasi setiap hari dalam window
        4. Untuk setiap hari, ambil state pada sunrise (06:00 WIB)
        5. Hitung skor proporsional
        6. Simpan top-N kandidat
        7. Kembalikan terurut dengan rank #1 ditandai is_strongest

    Atribut kelas
    -------------
    SUNRISE_HOUR_WIB : float
        Jam acuan hari dalam WIB (default 6.0).
    SUNRISE_HOUR_UT : float
        Ekuivalen UT (WIB − 7).
    STABILITY_HOURS_UT : tuple
        Tiga jam sampling untuk deteksi boundary harian.
    """

    SUNRISE_HOUR_WIB: float = 6.0
    SUNRISE_HOUR_UT: float = SUNRISE_HOUR_WIB - 7.0    # = -1.0
    STABILITY_HOURS_UT: Tuple[float, float, float] = (
        SUNRISE_HOUR_UT, 5.0, 11.0
    )  # 06:00, 12:00, 18:00 WIB

    def __init__(
        self,
        sthapati: ΩSthapatiSystem,
        astro_calc: AstroStateCalculator,
    ) -> None:
        """
        Parameters
        ----------
        sthapati : ΩSthapatiSystem
            Instance SPICA yang sudah diinisialisasi. Digunakan untuk
            mengakses mechanical engine, normalizer, dan konstanta.
        astro_calc : AstroStateCalculator
            Kalkulator state astronomis yang sudah diinisialisasi.
        """
        self.sthapati = sthapati
        self.astro = astro_calc
        self.mech = sthapati.mech
        self.math = sthapati.math
        self.norm = sthapati.norm
        self.const = sthapati.const

        # Reverse dicts — dibangun sekali saat inisialisasi
        self._naks_rev = _build_rev(NAKSHATRA_VARIANTS)
        self._yoga_rev = _build_rev(YOGA_VARIANTS)
        self._karana_rev = _build_rev(KARANA_VARIANTS)

    # -------------------------------------------------------------------------
    # Core: scan satu kumpulan window
    # -------------------------------------------------------------------------

    def _do_scan(
        self,
        windows: List[Tuple[int, Optional[int]]],
        targets: Dict[str, Any],
        top_n: int = 10,
    ) -> Tuple[List[Tuple], Dict[str, int]]:
        """
        Scan satu kumpulan window dan kembalikan top-N kandidat.

        Algoritma:
            - Untuk setiap window (ce_year, month), iterasi hari dalam bulan
            - Untuk setiap hari, ambil state pada sunrise
            - Pre-filter tithi: jika |diff| > 2 → skip (hemat ephemeris call)
            - Hitung skor proporsional
            - Simpan ke heap berukuran tetap

        Struktur entry tuple:
            (score, -h_ut, -counter, stab_count,
             jd_mid, state, brk, stability)

            - score      : float, makin tinggi makin baik
            - -h_ut      : negatif dari jam UT sampling. Makin kecil h_ut
                           (yaitu makin pagi), makin tinggi nilainya, sehingga
                           dalam sort ascending kandidat pagi muncul lebih dulu.
            - -counter   : negatif dari urutan discovery. Kandidat yang ditemukan
                           lebih awal (counter lebih kecil) menang tie-break.
            - stab_count : JUMLAH field yang stabil sepanjang hari (lihat
                           _count_stable). Field ini disimpan di tuple HANYA
                           sebagai diagnostik dan untuk diteruskan ke output
                           (via _to_sthapati_format), BUKAN sebagai tie-break.
                           Lihat catatan panjang di bawah.
            - jd_mid     : Julian Day tengah hari (referensi tanggal)
            - state      : dict state astronomis pada sunrise
            - brk        : dict breakdown skor per field
            - stability  : dict info stabilitas harian

        Catatan tentang stab_count sebagai tie-break
        --------------------------------------------
        Sebelum revisi ini, stab_count ditempatkan di posisi kedua tuple dan
        ikut menentukan ranking melalui key sort di parse(). Analisis empiris
        pada 112 prasasti Damais mengungkap bahwa ini secara sistematis
        MENGHASILKAN pilihan yang salah pada prasasti yang tanggalnya jatuh
        tepat di peralihan tithi.

        Alasannya: prasasti yang menyebut tithi tertentu (misal "tithi 2 Sukla")
        sering merujuk pada hari ketika tithi tersebut BARU MULAI — yaitu hari
        yang secara astronomis berada di BATAS tithi. Hari seperti itu punya
        stab_count rendah karena tithi berubah di tengah hari. Sementara
        kandidat palsu satu bulan kemudian (tithi sama, tapi di TENGAH sel)
        punya stab_count tinggi. Tie-break lama karena itu memilih kandidat
        yang salah pada tepat kasus-kasus yang paling membutuhkannya.

        Bukti konkret: prasasti A.22 (Śaka 782, tithi 2 Sukla, ref 860-03-27)
        dan A.57 (Śaka 803, tithi 2 Sukla, ref 881-07-31). Pada keduanya,
        kandidat yang benar (+1 hari dari ref) kalah dari kandidat salah
        (+30 hari) meski skor identik 1.000. Penyebab tunggal: stab_count.

        Revisi ini menghapus stab_count dari peran tie-break. Tie-break
        sekarang murni mekanis: jam sampling lebih pagi menang, lalu urutan
        discovery menang. Stabilitas tetap dihitung dan dilaporkan, tetapi
        tidak pernah menentukan peringkat.

        Parameters
        ----------
        windows : list of (ce_year, month)
            Daftar window untuk di-scan. month=None berarti seluruh tahun.
        targets : dict
            Target astronomi dari _resolve_targets.
        top_n : int
            Jumlah kandidat terbaik yang disimpan.

        Returns
        -------
        entries : list
            Daftar entry (unsorted; hanya top-N dalam heap).
        stats : dict
            Statistik: 'scanned' (hari yang diperiksa),
                       'matched' (hari dengan skor > 0).
        """
        heap: List[Tuple] = []
        counter = 0
        scanned = 0
        matched = 0

        for ce_year, month in windows:
            for jd_mid in self._iter_days(ce_year, month):
                scanned += 1

                # State pada sunrise = acuan hari
                jd_sunrise = jd_mid + self.SUNRISE_HOUR_UT / 24.0
                state = self.astro.state_at(jd_sunrise)

                # Pre-filter tithi: hemat ephemeris call
                if targets['tithi'] is not None:
                    d_t = self._tithi_distance(
                        targets['tithi'], state['tithi_abs']
                    )
                    if d_t > 2:
                        continue

                score, brk = self._score(state, targets)
                if score <= 0.0:
                    continue

                # Stability check dari 3 jam — disimpan sebagai anotasi.
                # TIDAK dipakai sebagai tie-break (lihat docstring di atas).
                hours_states = [state]
                for h_ut_extra in (5.0, 11.0):
                    hours_states.append(
                        self.astro.state_at(jd_mid + h_ut_extra / 24.0)
                    )
                stability = self._check_stability(hours_states)
                stab_count = self._count_stable(stability, targets)

                matched += 1
                counter += 1

                h_ut_used = self.SUNRISE_HOUR_UT

                # Urutan tuple: (skor, tie-break-1, tie-break-2, diagnostik, data...)
                # stab_count diletakkan SETELAH tie-break, bukan sebelumnya.
                entry = (
                    score, -h_ut_used, -counter, stab_count,
                    jd_mid, state, brk, stability,
                )
                heapq.heappush(heap, entry)
                if len(heap) > top_n:
                    heapq.heappop(heap)

        stats = {'scanned': scanned, 'matched': matched}
        return list(heap), stats

    # -------------------------------------------------------------------------
    # Public: parse satu data prasasti
    # -------------------------------------------------------------------------

    def parse(self, data: Dict[str, Any], verbose: bool = False) -> List[Dict[str, Any]]:
        """
        Konversi data prasasti astronomis menjadi daftar kandidat KA.

        Parameters
        ----------
        data : dict
            Data prasasti dengan field opsional:
                saka_year  : int (wajib)
                masa       : str (opsional; jika ada membatasi window)
                tithi      : int (1..15)
                paksa      : str ('Sukla' / 'Krsna')
                nakshatra  : str
                yoga       : str
                karana     : str
        verbose : bool
            Cetak diagnostik.

        Returns
        -------
        list of dict
            Daftar kandidat dalam format yang kompatibel dengan SPICA.
            Kandidat #1 (rank tertinggi) ditandai `is_strongest=True`.
            Kosong jika tidak ada kandidat.

        Catatan tentang urutan ranking
        ------------------------------
        Ranking final ditentukan oleh, secara berurutan:

            1. score       — skor proporsional dari _score() (descending)
            2. -h_ut       — jam sampling lebih pagi menang
            3. -counter    — kandidat yang ditemukan lebih awal menang

        stab_count SENGAJA TIDAK dipakai sebagai tie-break dalam revisi ini.
        Alasan lengkap ada di docstring _do_scan di atas. Singkatnya:
        stab_count memilih kandidat yang salah pada prasasti yang tithinya
        jatuh tepat di batas hari, yang justru kasus paling penting untuk
        diselesaikan dengan benar.

        stab_count tetap dibaca dari tuple dan diteruskan ke output
        (via _to_sthapati_format) supaya tetap tersedia untuk diagnostik
        dan untuk verifikasi di jalur 3.
        """
        saka = data.get('saka_year')
        if not saka:
            return []

        masa = data.get('masa')
        targets = self._resolve_targets(data, verbose)
        if targets is None or targets['n_available'] == 0:
            return []

        top_n = 10

        # Scan window dari tabel masa → bulan Julian
        windows = list(self._scan_windows(saka, masa))
        entries, stats = self._do_scan(windows, targets, top_n)

        if verbose:
            print(
                f"  [Astro] Hari dipindai: {stats['scanned']}, "
                f"kandidat skor > 0: {stats['matched']}"
            )

        # Sort final: score DESC, jam lebih pagi, discovery lebih awal.
        # stab_count TIDAK termasuk dalam key sort.
        entries = sorted(entries, key=lambda x: (-x[0], -x[1], -x[2]))

        n_cand = len(entries)
        results: List[Dict[str, Any]] = []
        for i, entry in enumerate(entries):
            (score, neg_h_ut, neg_counter, stab_count,
             jd_mid, state, brk, stability) = entry
            h_ut = -neg_h_ut
            r = self._to_sthapati_format(
                score, jd_mid, h_ut, state, brk, stability,
                targets['n_available'], n_cand,
            )
            r['rank'] = i + 1
            r['is_strongest'] = (i == 0)
            results.append(r)

        return results

    # -------------------------------------------------------------------------
    # Resolusi target
    # -------------------------------------------------------------------------

    def _resolve_targets(
        self,
        data: Dict[str, Any],
        verbose: bool,
    ) -> Optional[Dict[str, Any]]:
        """
        Konversi input prasasti ke bentuk internal yang siap dinilai.

        Field input yang didukung:
            tithi + paksa  → tithi_abs (1..30)
            nakshatra      → nakshatra index (1..27)
            yoga           → yoga index (1..27)
            karana         → nama karana kanonik

        Minimal: tithi ATAU nakshatra ATAU karana (yoga tidak bisa sendiri).

        Returns
        -------
        dict atau None
            Jika input tidak valid atau tidak cukup untuk anchor, return None.
        """
        tithi_in = data.get('tithi')
        paksa_in = data.get('paksa')
        naks_in = data.get('nakshatra')
        yoga_in = data.get('yoga')
        karana_in = data.get('karana')

        # Minimal: tithi / nakshatra / karana (yoga sendiri tidak cukup)
        if tithi_in is None and not naks_in and not karana_in:
            if verbose:
                print("  [Astro] Butuh tithi / nakshatra / karana")
            return None

        target_tithi = None
        if tithi_in is not None:
            target_tithi = self._to_abs_tithi(tithi_in, paksa_in)
            if target_tithi is None or not (1 <= target_tithi <= 30):
                if verbose:
                    print(f"  [Astro] Tithi tidak valid: {tithi_in} {paksa_in}")
                return None

        target_naks = None
        if naks_in:
            n = self._naks_rev.get(str(naks_in).lower().strip())
            if n is None:
                if verbose:
                    print(f"  [Astro] Nakshatra tidak dikenali: {naks_in}")
                return None
            target_naks = NAKSHATRA_NAMES.index(n) + 1

        target_yoga = None
        if yoga_in:
            y = self._yoga_rev.get(str(yoga_in).lower().strip())
            if y is not None:
                target_yoga = YOGAS.index(y) + 1
            elif verbose:
                print(f"  [Astro] Yoga tidak dikenali: {yoga_in} (diabaikan)")

        target_karana = None
        if karana_in:
            k = self._karana_rev.get(str(karana_in).lower().strip())
            if k is not None:
                target_karana = k
            elif verbose:
                print(f"  [Astro] Karana tidak dikenali: {karana_in} (diabaikan)")

        n_available = sum(
            1 for x in (target_tithi, target_naks, target_yoga, target_karana)
            if x is not None
        )

        return {
            'tithi': target_tithi,
            'nakshatra': target_naks,
            'yoga': target_yoga,
            'karana': target_karana,
            'n_available': n_available,
        }

    # -------------------------------------------------------------------------
    # Stability
    # -------------------------------------------------------------------------

    @staticmethod
    def _check_stability(hours_states: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        Cek apakah setiap field astronomis stabil sepanjang hari.

        Field dianggap stabil jika nilainya sama di semua jam sampling
        (06:00, 12:00, 18:00 WIB). Field yang tidak stabil menunjukkan
        hari batas (transisi field di tengah hari).
        """
        if not hours_states:
            return {}
        return {
            'tithi_stable': len({s['tithi_abs'] for s in hours_states}) == 1,
            'karana_stable': len({s['karana_name'] for s in hours_states}) == 1,
            'nakshatra_sayana_stable':
                len({s['nakshatra_sayana_idx'] for s in hours_states}) == 1,
            'nakshatra_nirayana_stable':
                len({s['nakshatra_nirayana_idx'] for s in hours_states}) == 1,
            'yoga_sayana_stable':
                len({s['yoga_sayana_idx'] for s in hours_states}) == 1,
            'yoga_nirayana_stable':
                len({s['yoga_nirayana_idx'] for s in hours_states}) == 1,
        }

    @staticmethod
    def _count_stable(stability: Dict[str, bool], targets: Dict[str, Any]) -> int:
        """
        Hitung berapa field yang dinilai DAN stabil.

        Field yang tidak ada di target (None) tidak dihitung. Untuk field
        dual-system (nakshatra, yoga), dianggap stabil jika salah satu
        sistem stabil.
        """
        count = 0
        if targets['tithi'] is not None and stability.get('tithi_stable'):
            count += 1
        if targets['karana'] is not None and stability.get('karana_stable'):
            count += 1
        if targets['nakshatra'] is not None:
            if (stability.get('nakshatra_sayana_stable') or
                    stability.get('nakshatra_nirayana_stable')):
                count += 1
        if targets['yoga'] is not None:
            if (stability.get('yoga_sayana_stable') or
                    stability.get('yoga_nirayana_stable')):
                count += 1
        return count

    # -------------------------------------------------------------------------
    # Skor proporsional
    # -------------------------------------------------------------------------

    def _score(
        self,
        state: Dict[str, Any],
        targets: Dict[str, Any],
    ) -> Tuple[float, Dict[str, Dict[str, Any]]]:
        """
        Hitung skor proporsional untuk satu state terhadap target.

        Untuk setiap field yang tersedia:
            exact (diff = 0)  → 1.0
            near  (diff = 1)  → 0.4
            miss  (diff > 1)  → 0.0

        Skor akhir = sum(partial) / n_available.

        Untuk field dual-system (nakshatra, yoga), jarak dihitung di
        kedua sistem dan diambil yang terkecil. Sistem yang menang dicatat
        di breakdown untuk diagnostik.
        """
        parts: Dict[str, Dict[str, Any]] = {}
        total = 0.0

        t_tithi = targets['tithi']
        t_naks = targets['nakshatra']
        t_yoga = targets['yoga']
        t_karana = targets['karana']
        n_available = targets['n_available']

        # --- Tithi (invariant) ---
        if t_tithi is not None:
            d = self._tithi_distance(t_tithi, state['tithi_abs'])
            v = 1.0 if d == 0 else (0.4 if d == 1 else 0.0)
            parts['tithi'] = {'value': v, 'system': None, 'detail': d}
            total += v

        # --- Nakshatra (dual-system) ---
        if t_naks is not None:
            d_say = self._circular_distance(
                t_naks, state['nakshatra_sayana_idx'], 27
            )
            d_nir = self._circular_distance(
                t_naks, state['nakshatra_nirayana_idx'], 27
            )
            # Bila kedua sistem memberi jarak 0 (exact), catat sebagai 'both'.
            # Bila hanya satu, catat yang exact.
            # Bila keduanya > 0 dan seri, prefer nirayana (konvensi Jawa Kuno).
            if d_say == 0 and d_nir == 0:
                d, sys_used = 0, 'both'
            elif d_say < d_nir:
                d, sys_used = d_say, 'sayana'
            elif d_nir < d_say:
                d, sys_used = d_nir, 'nirayana'
            else:
                d, sys_used = d_nir, 'nirayana'
            v = 1.0 if d == 0 else (0.4 if d == 1 else 0.0)
            parts['nakshatra'] = {
                'value': v,
                'system': sys_used,
                'detail': d,
                'd_sayana': d_say,
                'd_nirayana': d_nir,
            }
            total += v

        # --- Yoga (dual-system) ---
        if t_yoga is not None:
            d_say = self._circular_distance(
                t_yoga, state['yoga_sayana_idx'], 27
            )
            d_nir = self._circular_distance(
                t_yoga, state['yoga_nirayana_idx'], 27
            )
            if d_say == 0 and d_nir == 0:
                d, sys_used = 0, 'both'
            elif d_say < d_nir:
                d, sys_used = d_say, 'sayana'
            elif d_nir < d_say:
                d, sys_used = d_nir, 'nirayana'
            else:
                d, sys_used = d_nir, 'nirayana'
            v = 1.0 if d == 0 else (0.4 if d == 1 else 0.0)
            parts['yoga'] = {
                'value': v,
                'system': sys_used,
                'detail': d,
                'd_sayana': d_say,
                'd_nirayana': d_nir,
            }
            total += v

        # --- Karana (invariant) ---
        if t_karana is not None:
            v = 1.0 if t_karana == state['karana_name'] else 0.0
            parts['karana'] = {
                'value': v,
                'system': None,
                'detail': state['karana_name'],
            }
            total += v

        if n_available == 0:
            return 0.0, parts
        return total / n_available, parts

    # -------------------------------------------------------------------------
    # Window & iterasi
    # -------------------------------------------------------------------------

    def _scan_windows(
        self,
        saka: int,
        masa: Optional[str],
    ) -> Iterator[Tuple[int, Optional[int]]]:
        """
        Tentukan window scan dari masa Saka.

        Peta bulan Saka → bulan Julian diambil dari SAKA_MONTH_TO_JULIAN_RANGE
        di SPICA. Setiap masa memetakan ke satu atau dua bulan Julian.

        Untuk Pausa (menyeberangi batas tahun CE), window dipecah menjadi
        Desember tahun +78 dan Januari tahun +79.

        Jika masa tidak diberikan, scan seluruh tahun (12 bulan).
        """
        if not masa:
            yield (saka + 78, None)
            yield (saka + 79, None)
            return

        masa_norm = self.norm.normalize(masa)
        info = self.const.SAKA_MONTH_TO_JULIAN_RANGE.get(masa_norm)
        if not info:
            yield (saka + 78, None)
            yield (saka + 79, None)
            return

        jm = info['julian_months']
        add = info['add_years']

        if masa_norm == 'Pausa':
            yield (saka + 78, 12)
            yield (saka + 79, 1)
        else:
            ce_year = saka + add[0]
            for m in jm:
                yield (ce_year, m)

    def _iter_days(
        self,
        ce_year: int,
        month: Optional[int],
    ) -> Iterator[float]:
        """Iterasi hari dalam window. month=None berarti seluruh tahun."""
        if month is None:
            for m in range(1, 13):
                for d in self._iter_days_of_month(ce_year, m):
                    yield d
        else:
            for d in self._iter_days_of_month(ce_year, month):
                yield d

    def _iter_days_of_month(self, ce_year: int, month: int) -> Iterator[float]:
        """Iterasi semua hari dalam satu bulan, dengan JD dari MathCore."""
        days = self._days_in_month(ce_year, month)
        for d in range(1, days + 1):
            yield self.math.julian_date_to_jd(ce_year, month, d)

    @staticmethod
    def _days_in_month(year: int, month: int) -> int:
        """Jumlah hari dalam bulan (proleptic Gregorian)."""
        if month in (1, 3, 5, 7, 8, 10, 12):
            return 31
        if month in (4, 6, 9, 11):
            return 30
        leap = (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))
        return 29 if leap else 28

    # -------------------------------------------------------------------------
    # Helper konversi
    # -------------------------------------------------------------------------

    @staticmethod
    def _to_abs_tithi(tithi, paksa) -> Optional[int]:
        """
        Konversi (tithi, paksa) → tithi absolut (1..30).

        Sukla 1..15 → 1..15
        Krsna 1..15 → 16..30
        """
        try:
            t = int(tithi)
        except (TypeError, ValueError):
            return None
        if not (1 <= t <= 15):
            return None
        if paksa and str(paksa).lower().strip() in (
            'krsna', 'kresna', 'cemeng', 'tilem'
        ):
            return t + 15
        return t

    @staticmethod
    def _tithi_distance(t1: int, t2: int) -> int:
        """Jarak melingkar pada siklus 30."""
        d = abs(t1 - t2)
        return min(d, 30 - d)

    @staticmethod
    def _circular_distance(v1: int, v2: int, mod: int) -> int:
        """Jarak melingkar pada siklus `mod`."""
        d = abs(v1 - v2)
        return min(d, mod - d)

    # -------------------------------------------------------------------------
    # Format output
    # -------------------------------------------------------------------------

    def _to_sthapati_format(
        self,
        score: float,
        jd_mid: float,
        h_ut: float,
        state: Dict[str, Any],
        brk: Dict[str, Dict[str, Any]],
        stability: Dict[str, bool],
        n_available: int,
        n_cand: int,
    ) -> Dict[str, Any]:
        """
        Konversi internal entry ke format yang kompatibel dengan SPICA.

        `wuku_info` diturunkan dari KA via mechanical engine — bukan dari
        input. Ini menjadikan output jalur 2 setara dengan output jalur 1
        dalam hal struktur.
        """
        ka = MathCore.jd_to_ka(jd_mid)
        date = MathCore.ka_to_julian_date(ka)
        wuku_info = self.mech.calculate_wuku_wara_from_ka(ka)

        n_match = sum(1 for p in brk.values() if p['value'] >= 1.0)

        matched_systems: Dict[str, str] = {}
        for fname in ('nakshatra', 'yoga'):
            p = brk.get(fname)
            if p and p['value'] > 0:
                matched_systems[fname] = p['system']

        # Boundary flags = field yang dinilai tapi tidak stabil
        boundary_flags: List[str] = []
        if 'tithi' in brk and not stability.get('tithi_stable', True):
            boundary_flags.append('tithi')
        if 'nakshatra' in brk:
            if not (stability.get('nakshatra_sayana_stable', True) or
                    stability.get('nakshatra_nirayana_stable', True)):
                boundary_flags.append('nakshatra')
        if 'yoga' in brk:
            if not (stability.get('yoga_sayana_stable', True) or
                    stability.get('yoga_nirayana_stable', True)):
                boundary_flags.append('yoga')
        if 'karana' in brk and not stability.get('karana_stable', True):
            boundary_flags.append('karana')

        confidence = self._confidence(score, n_available, n_match)

        return {
            'candidate': {
                'ka': ka,
                'date': date,
                'wuku_info': wuku_info,
                'i': wuku_info['i'],
                's': wuku_info['s'],
                'day_of_year': MathCore.day_of_year(
                    int(date[0]), int(date[1]), int(date[2])
                ),
                'method': 'astronomical_scan',
                'sample_hour_ut': h_ut,
            },
            'score': score,
            'confidence': confidence,
            'n_available': n_available,
            'n_match': n_match,
            'match_breakdown': brk,
            'matched_systems': matched_systems,
            'astro_state': state,
            'stability': stability,
            'boundary_flags': boundary_flags,
            'is_strongest': False,
            'month_shifted': False,
            'has_explicit_intercalation': False,
        }

    @staticmethod
    def _confidence(score: float, n_available: int, n_match: int) -> str:
        """
        Tentukan level kepercayaan dari skor dan jumlah bukti.

        Aturan:
            n_available ≥ 3, n_match ≥ 3, score ≥ 0.95   → TINGGI
            n_available ≥ 2, n_match ≥ 2, score ≥ 0.95   → TINGGI
            n_available ≥ 2, score ≥ 0.75                → SEDANG
            score ≥ 0.95, n_available = 1                → SEDANG
            score ≥ 0.4                                  → RENDAH
            else                                         → DITOLAK
        """
        if n_available >= 3 and n_match >= 3 and score >= 0.95:
            return 'TINGGI'
        if n_available >= 2 and n_match >= 2 and score >= 0.95:
            return 'TINGGI'
        if n_available >= 2 and score >= 0.75:
            return 'SEDANG'
        if score >= 0.95 and n_available == 1:
            return 'SEDANG'
        if score >= 0.4:
            return 'RENDAH'
        return 'DITOLAK'

    # -------------------------------------------------------------------------
    # Verifikasi (untuk jalur 3)
    # -------------------------------------------------------------------------

    def verify(
        self,
        results: List[Dict[str, Any]],
        data: Dict[str, Any],
        verbose: bool = False,
    ) -> None:
        """
        Verifikasi setiap hasil SPICA terhadap state astronomis.

        Untuk setiap kandidat (yang sudah memiliki KA dari jalur mekanik),
        hitung state astronomis pada KA tersebut, bandingkan dengan target,
        dan simpan hasil di key `astro_verification`.

        Efek:
            - Menambahkan `astro_verification` ke setiap result.
            - Upgrade confidence ke TINGGI jika n_match == n_available ≥ 2.
            - Downgrade satu level jika n_match == 0.

        Catatan: tidak mengubah `candidate['ka']`. KA tetap milik jalur
        mekanik. Verifikasi hanya menambah kepercayaan atau menandai
        ketidakcocokan.
        """
        targets = self._resolve_targets(data, verbose=False)
        if targets is None or targets['n_available'] == 0:
            return

        n_available = targets['n_available']

        for r in results:
            cand = r.get('candidate')
            if not cand:
                continue

            ka = cand['ka']
            jd_mid = MathCore.ka_to_jd(ka)

            jd_sunrise = jd_mid + self.SUNRISE_HOUR_UT / 24.0
            state = self.astro.state_at(jd_sunrise)

            hours_states = [state]
            for h_ut_extra in (5.0, 11.0):
                hours_states.append(
                    self.astro.state_at(jd_mid + h_ut_extra / 24.0)
                )
            stability = self._check_stability(hours_states)

            score, brk = self._score(state, targets)
            n_match = sum(1 for p in brk.values() if p['value'] >= 1.0)

            matched_systems: Dict[str, str] = {}
            for fname in ('nakshatra', 'yoga'):
                p = brk.get(fname)
                if p and p['value'] > 0:
                    matched_systems[fname] = p['system']

            boundary_flags: List[str] = []
            if 'tithi' in brk and not stability.get('tithi_stable', True):
                boundary_flags.append('tithi')
            if 'nakshatra' in brk:
                if not (stability.get('nakshatra_sayana_stable', True) or
                        stability.get('nakshatra_nirayana_stable', True)):
                    boundary_flags.append('nakshatra')
            if 'yoga' in brk:
                if not (stability.get('yoga_sayana_stable', True) or
                        stability.get('yoga_nirayana_stable', True)):
                    boundary_flags.append('yoga')
            if 'karana' in brk and not stability.get('karana_stable', True):
                boundary_flags.append('karana')

            r['astro_verification'] = {
                'state': state,
                'sample_hour_ut': self.SUNRISE_HOUR_UT,
                'score': score,
                'n_available': n_available,
                'n_match': n_match,
                'breakdown': brk,
                'matched_systems': matched_systems,
                'stability': stability,
                'boundary_flags': boundary_flags,
                'all_match': n_match == n_available,
            }

            # Update confidence
            if n_match == n_available and n_available >= 2:
                r['confidence'] = 'TINGGI'
            elif n_match == 0:
                r['confidence'] = self._downgrade(
                    r.get('confidence', 'RENDAH')
                )

            if verbose:
                icon = '✓' if n_match == n_available else '⚠'
                sys_info = ''
                if matched_systems:
                    sys_info = ' [' + ','.join(
                        f"{k}:{v}" for k, v in matched_systems.items()
                    ) + ']'
                bstr = (
                    f" ↔[{','.join(boundary_flags)}]"
                    if boundary_flags else ''
                )
                print(
                    f"  [Verify] KA={ka} @06:00WIB → "
                    f"{n_match}/{n_available} {icon}{sys_info}{bstr}"
                )

    @staticmethod
    def _downgrade(level: str) -> str:
        """Turunkan level confidence satu tingkat."""
        return {
            'TINGGI': 'SEDANG',
            'SEDANG': 'RENDAH',
            'RENDAH': 'DITOLAK',
        }.get(level, level)


# =============================================================================
# BAGIAN 5 — DISPATCHER
# -----------------------------------------------------------------------------
# Memilih jalur berdasarkan data yang tersedia. Tidak menyentuh logika
# internal SPICA maupun parser.
# =============================================================================

def convert_prasasti_experimental(
    sthapati: ΩSthapatiSystem,
    data: Dict[str, Any],
    astro_calc: Optional[AstroStateCalculator] = None,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    Dispatcher tiga jalur.

    Aturan pemilihan:
        Jalur 1 (mekanik)   : wara ada, astronomi tidak ada
        Jalur 2 (astronomis): wara tidak ada, astronomi ada
        Jalur 3 (cross)     : keduanya ada

    Parameters
    ----------
    sthapati : ΩSthapatiSystem
        Instance SPICA.
    data : dict
        Data prasasti.
    astro_calc : AstroStateCalculator, optional
        Wajib untuk jalur 2 dan 3. Jika None, jalur 2 akan return [].
    verbose : bool
        Cetak diagnostik.

    Returns
    -------
    list of dict
        Kandidat dalam format SPICA.
    """
    has_wara = bool(data.get('wara_string'))
    has_astro = any([
        data.get('tithi') is not None,
        data.get('nakshatra'),
        data.get('yoga'),
        data.get('karana'),
    ])

    if not has_wara and not has_astro:
        if verbose:
            print("[Dispatch] Tidak ada wara maupun data astronomis → batal")
        return []

    # -------------------------------------------------------------------------
    # Jalur 1 — Mekanik murni
    # -------------------------------------------------------------------------
    if has_wara and not has_astro:
        if verbose:
            print("[Dispatch] Jalur 1 — mekanik murni (SPICA)")
        return sthapati.convert_prasasti_with_smart_parsing(data, verbose=verbose)

    # -------------------------------------------------------------------------
    # Jalur 2 — Astronomis murni
    # -------------------------------------------------------------------------
    if not has_wara and has_astro:
        if astro_calc is None:
            if verbose:
                print("[Dispatch] Jalur 2 — butuh AstroStateCalculator")
            return []
        if verbose:
            print("[Dispatch] Jalur 2 — scan astronomis murni")
        parser = AstronomicalSmartParser(sthapati, astro_calc)
        return parser.parse(data, verbose=verbose)

    # -------------------------------------------------------------------------
    # Jalur 3 — Cross-verifikasi
    # -------------------------------------------------------------------------
    if verbose:
        print("[Dispatch] Jalur 3 — SPICA + verifikasi astronomis")

    results = sthapati.convert_prasasti_with_smart_parsing(
        data, verbose=verbose
    )

    if astro_calc is None:
        if verbose:
            print("  (tanpa astro_calc → verifikasi dilewati)")
        return results

    if not results:
        if verbose:
            print("  SPICA kosong → fallback scan astronomis")
        parser = AstronomicalSmartParser(sthapati, astro_calc)
        return parser.parse(data, verbose=verbose)

    parser = AstronomicalSmartParser(sthapati, astro_calc)
    parser.verify(results, data, verbose=verbose)
    return results


# =============================================================================
# BAGIAN 6 — UJI SWA (self-test)
# -----------------------------------------------------------------------------
# Dijalankan saat modul dieksekusi langsung (python astro_smart_parser_experimental.py).
# Menguji tiga jalur dengan contoh dari prasasti Damais.
# =============================================================================

if __name__ == '__main__':
    print("=" * 72)
    print("ASTRONOMICAL SMART PARSER — SELF TEST")
    print("=" * 72)

    sthapati = ΩSthapatiSystem(verbose_startup=False)
    calc = AstroStateCalculator()

    # -------------------------------------------------------------------------
    # Helper tampilan
    # -------------------------------------------------------------------------
    def print_full_row(i: int, res: Dict[str, Any]) -> None:
        c = res['candidate']
        y, m, d = c['date']
        st = res['astro_state']
        hh = int((c['sample_hour_ut'] + 7) % 24)
        bflags = res.get('boundary_flags', [])
        bstr = f" ↔{bflags}" if bflags else ""
        mark = '⭐' if res.get('is_strongest') else '  '

        print(
            f"{mark} #{i+1}: {int(y)}-{int(m):02d}-{int(d):02d} @{hh:02d}WIB | "
            f"KA={c['ka']} | Wuku={c['wuku_info']['wuku_name']}"
        )
        print(
            f"       Tithi    : {st['tithi_abs']:>2} "
            f"(elong {st['elongation_deg']:.2f}°)"
        )
        print(
            f"       Nakshatra: sayana={st['nakshatra_sayana_name']:<18} "
            f"nirayana={st['nakshatra_nirayana_name']}"
        )
        print(
            f"       Yoga     : sayana={st['yoga_sayana_name']:<18} "
            f"nirayana={st['yoga_nirayana_name']}"
        )
        print(f"       Karana   : {st['karana_name']}")

        sys_str = ''
        if res.get('matched_systems'):
            sys_str = ' [' + ','.join(
                f"{k}:{v}" for k, v in res['matched_systems'].items()
            ) + ']'
        print(
            f"       Skor     : {res['score']:.3f} | {res['confidence']} | "
            f"match={res['n_match']}/{res['n_available']}{sys_str}{bstr}"
        )
        print()

    # -------------------------------------------------------------------------
    # Uji 1 — Jalur 2 dengan tithi saja
    # -------------------------------------------------------------------------
    print("\n[1] Jalur 2 — tithi 12 Sukla saja (Śaka 851, Asvini)")
    data = {
        'saka_year': 851,
        'masa': 'Asvini',
        'tithi': 12,
        'paksa': 'Sukla',
    }
    r = convert_prasasti_experimental(sthapati, data, calc, verbose=True)
    for i, res in enumerate(r[:5]):
        print_full_row(i, res)

    # -------------------------------------------------------------------------
    # Uji 2 — Jalur 2 dengan tithi + nakshatra
    # -------------------------------------------------------------------------
    print("\n[2] Jalur 2 — tithi 12 + nakshatra Satabhisha")
    data = {
        'saka_year': 851,
        'masa': 'Asvini',
        'tithi': 12,
        'paksa': 'Sukla',
        'nakshatra': 'Satabhisha',
    }
    r = convert_prasasti_experimental(sthapati, data, calc, verbose=True)
    for i, res in enumerate(r[:5]):
        print_full_row(i, res)

    # -------------------------------------------------------------------------
    # Uji 3 — Jalur 3 (cross-verify)
    # -------------------------------------------------------------------------
    print("\n[3] Jalur 3 — Cunggrang II lengkap (wara + tithi + nakshatra + yoga)")
    data = {
        'saka_year': 851,
        'masa': 'Asvini',
        'tithi': 12,
        'paksa': 'Sukla',
        'nakshatra': 'Satabhisha',
        'yoga': 'Ganda',
        'wuku': 'Wugu',
        'wara_string': 'Tungleh-Pahing-Sukra',
    }
    r = convert_prasasti_experimental(sthapati, data, calc, verbose=True)
    for i, res in enumerate(r[:3]):
        mark = '⭐' if res.get('is_strongest') else '  '
        cand = res['candidate']
        y, m, d = cand['date']
        verify = res.get('astro_verification', {})
        print(
            f"{mark} #{i+1}: {int(y)}-{int(m):02d}-{int(d):02d} | "
            f"{res['confidence']} | verify={verify.get('n_match')}/"
            f"{verify.get('n_available')}"
        )

    print("\nSelf test selesai.")