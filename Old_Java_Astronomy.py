# ============================================================================
# Old Java Astronomy - JRC Enhanced Version
# Based on Ω-STHAPATI ASTRONOMI v301.5 with JRC high-precision ephemeris
# Includes: Panchanga, Vedic Time, Grahacara Astha, Dewata, Mandala, and full planetary positions
# ============================================================================

# ============================================================================
# Prevent __pycache__ creation
# ============================================================================
import sys
sys.dont_write_bytecode = True

import math
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from datetime import datetime

# ============================================================================
# JRC EPHEMERIS IMPORTS
# ============================================================================
from JRC_Ephemeris import (
    IAU2023UltraPrecision,
    TimeSystem as JRC_TimeSystem,
    VSOP87SolarEngine,
    LunarELP82Engine,
    UnifiedCoordinateTransformer,
    JPLStyleTopocentricCorrections,
    AtmosphericModel,
    GlobalCacheManager,
    HighPrecisionNutation,
    _DELTA_T_TABLE          
)

# ============================================================================
# DISPLAY HELPER - FORMATTING KONSISTEN
# ============================================================================
BOLD = "\033[1m"
RESET = "\033[0m"

def print_labeled(label: str, value: str, width: int = 30) -> None:
    """Cetak label dengan lebar tetap, titik dua sejajar vertikal."""
    print(f"   {label:<{width}} : {value}")

def print_section_header(title: str, char: str = "─", width: int = 72) -> None:
    """Cetak header bagian dengan garis di atas dan bawah."""
    print(f"\n{BOLD}{char * width}{RESET}")
    print(f"{BOLD}{title:^{width}}{RESET}")
    print(f"{BOLD}{char * width}{RESET}")

# ============================================================================
# CONSTANTS - IAU2023 ULTRA PRECISION (JRC)
# ============================================================================
JRC = IAU2023UltraPrecision()

# ============================================================================
# TIME SYSTEM - ENHANCED WITH YUGA INFO (extends JRC TimeSystem)
# ============================================================================
class TimeSystem(JRC_TimeSystem):
    """Extended time system with Yuga information"""

    def astronomical_year_to_yuga_info(self, year_astro):
        kali_yuga_start = -3101
        years_since_kali_start = year_astro - kali_yuga_start
        yuga_cycles = {
            'Kali Yuga': 432000,
            'Dvapara Yuga': 864000,
            'Treta Yuga': 1296000,
            'Satya Yuga': 1728000
        }
        total_yuga_cycle = sum(yuga_cycles.values())
        if years_since_kali_start >= 0:
            current_yuga = 'Kali Yuga'
            years_in_current = years_since_kali_start
        else:
            current_yuga = 'Sebelum Kali Yuga'
            years_in_current = abs(years_since_kali_start)
        years_in_mahayuga = years_since_kali_start % total_yuga_cycle
        if years_in_mahayuga < 0:
            years_in_mahayuga += total_yuga_cycle
        kalpa_number = (years_since_kali_start // total_yuga_cycle) + 1
        return {
            'astronomical_year': year_astro,
            'kali_yuga_start_astronomical': kali_yuga_start,
            'years_since_kali_start': years_since_kali_start,
            'current_yuga': current_yuga,
            'years_in_current_yuga': abs(years_in_current),
            'years_in_mahayuga': years_in_mahayuga,
            'kalpa': f"Kalpa ke-{kalpa_number}",
            'description': f"Tahun astronomi {year_astro} = {self.format_astronomical_year(year_astro)}"
        }

# ============================================================================
# ATMOSPHERIC & LOCATION CONSTANTS - JOLOTUNDO (JRC)
# ============================================================================
class AtmosphericConstants:
    """Konstanta atmosfer dan lokasi spesifik untuk Jolotundo (from JRC)"""

    JOLOTUNDO = JRC.JOLOTUNDO_LOCATION

    ATMOSPHERIC_MODELS = {
        "STANDARD_JAVA": {
            "latitude": JOLOTUNDO['coordinates']['latitude'],
            "longitude": JOLOTUNDO['coordinates']['longitude'],
            "elevation": JOLOTUNDO['elevation']['orthometric'],
            "temperature": 24.0,
            "pressure": 952.5,
            "humidity": 0.728,
            "turbidity": 0.05,
            "wavelength": 0.55,
        },
        "REFRACTION_MODELS": {
            "BENNETT_1982": {
                "formula": "R = 1 / tan(h + 7.31/(h+4.4))",
                "accuracy": "Good for h > 5°"
            }
        },
        "HORIZON_REFRACTION": {
            "standard": 0.5667,
            "tropical": 0.5833,
        },
        "ELEVATION_CORRECTION": {
            "scale_height": 8435.0,
            "temperature_lapse_rate": 0.0065
        }
    }

    INDONESIA_TIMEZONES = {
        "WIB": {
            "name": "Waktu Indonesia Barat",
            "utc_offset": 7.0,
            "longitude_standard": 105.0,
        }
    }

    @classmethod
    def get_jolotundo_params(cls):
        return {
            "latitude": -7.609444,
            "longitude": 112.595556,
            "elevation": 554.509,
            "temperature": 24.0,
            "pressure": 952.5,
            "humidity": 0.728,
        }

# ============================================================================
# MATH CORE - PRESISI TINGGI (untuk KA dan konversi tanggal)
# ============================================================================
class MathCore:
    """Fungsi matematika presisi tinggi untuk konversi tanggal"""

    KALI_EPOCH_JD_NOON = 588465.5

    @staticmethod
    def is_gregorian_date(year_astro, month, day):
        if year_astro < 1582:
            return False
        elif year_astro > 1582:
            return True
        else:
            if month < 10:
                return False
            elif month > 10:
                return True
            else:
                return day >= 15

    @staticmethod
    def jd_to_julian_date(jd):
        jd += 0.5
        Z = int(jd)
        F = jd - Z
        if Z < 2299161:
            A = Z
        else:
            alpha = int((Z - 1867216.25) / 36524.25)
            A = Z + 1 + alpha - int(alpha / 4)
        B = A + 1524
        C = int((B - 122.1) / 365.25)
        D = int(365.25 * C)
        E = int((B - D) / 30.6001)
        day = B - D - int(30.6001 * E) + F
        month = E - 1 if E < 14 else E - 13
        year = C - 4716 if month > 2 else C - 4715
        if year <= 0:
            year -= 1
        return year, month, day

    @staticmethod
    def julian_date_to_jd(year_astro, month, day):
        if month <= 2:
            y = year_astro - 1
            m = month + 12
        else:
            y = year_astro
            m = month
        if MathCore.is_gregorian_date(year_astro, month, day):
            A = y // 100
            B = 2 - A + (A // 4)
        else:
            B = 0
        jd_ut = (int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + day + B - 1524.5)
        return jd_ut - 7.0/24.0

    @staticmethod
    def ka_to_jd(ka):
        return ka + MathCore.KALI_EPOCH_JD_NOON

    @staticmethod
    def jd_to_ka(jd):
        return int(round(jd - MathCore.KALI_EPOCH_JD_NOON))

    @staticmethod
    def ka_to_julian_date(ka):
        jd = MathCore.ka_to_jd(ka)
        return MathCore.jd_to_julian_date(jd)

    @staticmethod
    def julian_date_to_ka(year, month, day):
        # Tahun sudah dalam format astronomi, tidak perlu diubah
        year_astro = year
        jd = MathCore.julian_date_to_jd(year_astro, month, day)
        return MathCore.jd_to_ka(jd)

    @staticmethod
    def normalize_angle(angle):
        angle %= 360
        if angle < 0:
            angle += 360
        return angle

    @staticmethod
    def sin_d(degrees):
        return math.sin(math.radians(degrees))

    @staticmethod
    def cos_d(degrees):
        return math.cos(math.radians(degrees))

    @staticmethod
    def tan_d(degrees):
        return math.tan(math.radians(degrees))

    @staticmethod
    def asin_d(x):
        return math.degrees(math.asin(max(-1, min(1, x))))

    @staticmethod
    def acos_d(x):
        return math.degrees(math.acos(max(-1, min(1, x))))

    @staticmethod
    def atan2_d(y, x):
        return math.degrees(math.atan2(y, x))

    @staticmethod
    def julian_centuries_from_j2000(jd):
        return (jd - 2451545.0) / 36525.0

# ============================================================================
# Ω CONSTANTS - SEMUA KONSTANTA VEDIC DAN MAPPING (menggunakan JRC untuk nilai astronomi)
# ============================================================================
class ΩConstants:
    """Konstanta sistem astronomi Vedic - menggunakan JRC untuk nilai astronomi"""

    IAU = JRC

    # EPOCH KONSTANTA
    KALI_EPOCH_JD = 588465.5
    KALI_EPOCH_DATE = "18 Februari 3102 SM"
    KALI_EPOCH_DESCRIPTION = "Awal Kali Yuga (tradisi Hindu, berdasarkan perhitungan astronomi)"
    J2000_EPOCH_JD = JRC.J2000_JD

    # LOKASI DEFAULT - Jolotundo (JRC)
    LOC_LAT = -7.609444
    LOC_LON = 112.595556
    LOC_ELEV = 554.509
    LOC_NAME = "Jolotundo Obsv"
    LOC_TZ_OFFSET = 7.744
    LOC_PRESSURE = 952.5
    LOC_TEMPERATURE = 24.0

    # OBLIQUITY J2000
    OBLIQUITY = JRC.OBLIQUITY_J2000

    # SIKLUS
    WUKU_CYCLE = 210
    NAKSHATRA_COUNT = 27
    TITHI_COUNT = 30

    # MAPPING VARIAN EJAAN
    MONTHS_SAKA = {
        "Caitra": ["Cetra", "Chaitra", "Caitra"],
        "Vaisakha": ["Wesakha", "Waisakha", "Wesaka", "Vaisaka", "Vaisakha", "Besakha"],
        "Jyestha": ["Jyeshtha", "Jestha", "Jyesta", "Yestha", "Iestha"],
        "Asadha": ["Asada", "Asadha", "Asala", "Asarha"],
        "Sravana": ["Srawana", "Sravana", "Srawana", "Sarana"],
        "Bhadrapada": ["Badrapada", "Bhadrapada", "Bhadra", "Badra"],
        "Asvini": ["Asuji", "Asvini", "Aswini", "Asui", "Asvij", "Asvin"],
        "Kartika": ["Kartika", "Karthika", "Karttika", "Katika"],
        "Margasira": ["Margasira", "Margashira", "Markasira", "Margasira"],
        "Pausa": ["Pausa", "Pusa", "Pausha", "Pusa"],
        "Magha": ["Maga", "Magha", "Maha"],
        "Phalguna": ["Palguna", "Phalguna", "Falguna", "Palguna"]
    }

    NAKSHATRA_VARIANTS = {
        "Aswini": ["Aswini", "Asvini", "Asuji", "Asvij"],
        "Bharani": ["Bharani", "Barani"],
        "Krittika": ["Krittika", "Kartika", "Krtika"],
        "Rohini": ["Rohini", "Rohini"],
        "Mrigasira": ["Mrigasira", "Mrigasira", "Margasira"],
        "Ardra": ["Ardra", "Ardra"],
        "Punarvasu": ["Punarvasu", "Punarvasu"],
        "Pushya": ["Pushya", "Pusya", "Tisya"],
        "Aslesha": ["Aslesha", "Aslesa"],
        "Magha": ["Magha", "Maga"],
        "Purva Phalguni": ["Purva Phalguni", "Purwa Palguna"],
        "Uttara Phalguni": ["Uttara Phalguni", "Utara Palguna"],
        "Hasta": ["Hasta", "Hasta"],
        "Chitra": ["Chitra", "Citra"],
        "Swati": ["Swati", "Swati"],
        "Visakha": ["Visakha", "Wesakha", "Besakha"],
        "Anuradha": ["Anuradha", "Anuradha"],
        "Jyestha": ["Jyesta", "Jestha", "Yestha"],
        "Mula": ["Mula", "Mula"],
        "Purva Ashadha": ["Purva Ashadha", "Purwa Asada", "Purvasadha", "PurvaAshadha"],
        "Uttara Ashadha": ["Uttara Ashadha", "Utara Asada", "Uttarasadha", "UttaraAshadha"],
        "Sravana": ["Sravana", "Srawana"],
        "Dhanistha": ["Dhanistha", "Danista"],
        "Satabhisha": ["Satabhisha", "Satabisa"],
        "Purva Bhadrapada": ["Purva Bhadrapada", "Purwa Badra", "Purvabhadrapada", "PurvaBhadrapada"],
        "Uttara Bhadrapada": ["Uttara Bhadrapada", "Utara Badra", "Uttarabhadrapada", "UttaraBhadrapada", "Uttarabadra", "Uttar Bhadrapada"],
        "Revati": ["Revati", "Rewati"]
    }

    PAKSA_VARIANTS = {
        "Sukla": ["Sukla", "Suklapaksa", "Shukla", "Sula", "Terang"],
        "Krsna": ["Krsna", "Krishnapaksa", "Kresna", "Cemeng", "Tilem"]
    }

    NAKSHATRAS_STANDARD = list(NAKSHATRA_VARIANTS.keys())

    YOGAS = [
        "Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Sobhana", "Atiganda",
        "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva",
        "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan",
        "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
        "Brahma", "Indra", "Vaidhriti"
    ]

    KARANAS = [
        "Kimstughna", "Bava", "Balava", "Kaulava", "Taitila", "Gara",
        "Vanija", "Vishti", "Sakuni", "Catuspada", "Naga"
    ]

    PARWESA = ["Brahma", "Sasi", "Indra", "Kuwera", "Baruna", "Agni", "Yama"]

    ZODIAC = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
              "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

    ZODIAC_SANSKRIT = [
        "Meṣa", "Vṛṣabha", "Mithuna", "Karkaṭa", "Siṃha", "Kanyā",
        "Tulā", "Vṛścika", "Dhanuṣa", "Makara", "Kumbha", "Mīna"
    ]

    ZODIAC_PAIRS = list(zip(ZODIAC, ZODIAC_SANSKRIT))

    PARWESA_G0MPERS = {
        "P_PERIOD": 1219.11,
        "C_OFFSET": -1.2,
        "MAPPING": ["Brahmā", "Śaśi", "Indra", "Kuwera", "Baruṇa", "Agni", "Yama"]
    }

    MUHURTA_AUDAYIKA = [
        "Rodra (Rudra)", "Śweta", "Maitra", "Sārabhaṭa", "Sāwitrī",
        "Wairājya", "Wiswabasu", "Abhijit", "Rauhiṇa", "Bala",
        "Wijaya", "Nerṛti (Nairṛta)", "Bāruṇa (Varuṇa)", "Saumya", "Baga (Bhaga)"
    ]

    RASIMANA_TABLE = {
        0: 115.0, 1: 118.0, 2: 120.0, 3: 122.0, 4: 120.0,
        5: 118.18, 6: 118.17, 7: 124.07, 8: 125.0, 9: 124.0,
        10: 122.0, 11: 118.0
    }

    # KONSTANTA PLANET UPGRADED
    PLANET_ACCURACY_MODEL = {
        "HIGH": {"range": 2000, "accuracy_deg": 0.01, "model": "VSOP87_Compact"},
        "MEDIUM": {"range": 4000, "accuracy_deg": 0.05, "model": "Improved_Keplerian"},
        "LOW": {"range": 10000, "accuracy_deg": 0.5, "model": "Sidi_LongTerm"}
    }

    # GRAHACARA ASTHA
    ASTHA_DIRECTIONS = {
        270: "Udaya - Terbit",
        0: "Transit - Ūrdhva",
        90: "Asta - Terbenam",
        180: "Nadir - Adhaḥ"
    }

    ASTHA_ZONES = {
        "Nṛttiasthā": {"range": (0, 45), "lha_range": (0, 45), "waktu": "Setelah kulminasi, menuju barat", "status": "Menurun dari puncak"},
        "Paścimasthā": {"range": (45, 90), "lha_range": (45, 90), "waktu": "Menuju terbenam", "status": "Mendekati horizon barat"},
        "Vāyavyasthā": {"range": (90, 135), "lha_range": (90, 135), "waktu": "Setelah terbenam", "status": "Di bawah horizon barat"},
        "Uttarasthā": {"range": (135, 180), "lha_range": (135, 180), "waktu": "Mendekati nadir", "status": "Menuju titik terendah"},
        "Āirāṇyasthā": {"range": (180, 225), "lha_range": (180, 225), "waktu": "Setelah nadir", "status": "Menuju timur"},
        "Pūrvasthā": {"range": (225, 270), "lha_range": (225, 270), "waktu": "Menjelang terbit", "status": "Mendekati horizon timur"},
        "Āgneyasthā": {"range": (270, 315), "lha_range": (270, 315), "waktu": "Setelah terbit", "status": "Naik dari horizon timur"},
        "Dakṣiṇasthā": {"range": (315, 360), "lha_range": (315, 360), "waktu": "Menuju kulminasi", "status": "Mendekati puncak"}
    }

    TABEH_NAMES = {
        "siang": ["Tabeh I", "Tabeh II", "Tabeh III", "Tabeh IV", "Tabeh V", "Tabeh VI", "Tabeh VII", "Tabeh VIII"],
        "malam": ["Tabeh I", "Tabeh II", "Tabeh III", "Tabeh IV", "Tabeh V", "Tabeh VI", "Tabeh VII", "Tabeh VIII"]
    }

    # GERAKAN RATA-RATA (untuk referensi, tidak digunakan langsung karena pakai JRC)
    PLANET_MEAN_MOTION = {
        "Surya": 0.98560267,
        "Candra": 13.17639639,
        "Mangala": 0.52402068,
        "Budha": 4.09233470,
        "Brihaspati": 0.08308529,
        "Sukra": 1.60213034,
        "Sani": 0.03344414,
        "Rahu": -0.052953,
        "Ketu": -0.052953
    }

    PLANET_EPOCH_LONGITUDE = {
        "Surya": 280.4664567,
        "Candra": 218.3164477,
        "Mangala": 355.433,
        "Budha": 252.250,
        "Brihaspati": 34.404,
        "Sukra": 181.979,
        "Sani": 50.077,
        "Rahu": 180.0,
        "Ketu": 0.0
    }

    PLANET_NAME_MAPPING = {
        "Surya": ["Matahari", "Sun", "Ravi"],
        "Candra": ["Bulan", "Moon", "Chandra"],
        "Mangala": ["Mars", "Angaraka", "Kuja"],
        "Budha": ["Merkurius", "Mercury", "Budha"],
        "Brihaspati": ["Jupiter", "Guru", "Bṛhaspati"],
        "Sukra": ["Venus", "Shukra", "Shukracharya"],
        "Sani": ["Saturnus", "Saturn", "Shani"],
        "Rahu": ["Node Bulan Naik", "Ascending Node", "Rāhu"],
        "Ketu": ["Node Bulan Turun", "Descending Node", "Ketu"]
    }


# ============================================================================
# NORMALIZATION ENGINE (untuk varian ejaan)
# ============================================================================
class NormalizationEngine:
    def __init__(self):
        self.const = ΩConstants
        self._build_reverse_mapping()

    def _build_reverse_mapping(self):
        self.reverse_mapping = {}
        for std, variants in self.const.MONTHS_SAKA.items():
            for var in variants:
                self.reverse_mapping[var.lower()] = std
        for std, variants in self.const.NAKSHATRA_VARIANTS.items():
            for var in variants:
                self.reverse_mapping[var.lower()] = std
        for std, variants in self.const.PAKSA_VARIANTS.items():
            for var in variants:
                self.reverse_mapping[var.lower()] = std

    def normalize(self, text: str) -> str:
        if not text:
            return text
        text_lower = text.lower().strip()
        if text_lower in self.reverse_mapping:
            return self.reverse_mapping[text_lower]
        return text.title()

# ============================================================================
# ASTRONOMICAL ENGINE - JRC ENHANCED
# ============================================================================
class AstronomicalEngine:
    """Engine astronomi presisi tinggi menggunakan JRC ephemeris"""

    def __init__(self, latitude=None, longitude=None, elevation=None):
        self.const = ΩConstants
        self.math = MathCore()
        self.norm = NormalizationEngine()

        self.lat = latitude if latitude is not None else self.const.LOC_LAT
        self.lon = longitude if longitude is not None else self.const.LOC_LON
        self.elev = elevation if elevation is not None else self.const.LOC_ELEV

        self.time_system = TimeSystem()
        self.sun_calc = VSOP87SolarEngine()
        self.moon_calc = LunarELP82Engine()
        self.transformer = UnifiedCoordinateTransformer()
        self.topo_corr = JPLStyleTopocentricCorrections()
        self.atmos = AtmosphericModel()
        self.nutation = HighPrecisionNutation()

        self.pressure = self.const.LOC_PRESSURE
        self.temperature = self.const.LOC_TEMPERATURE

        self.planet_system = PlanetarySystemUpgraded(self.time_system, self.const)

    def calculate_lunar_nodes_precise(self, jd_tt, node_name="Rahu"):
        T = (jd_tt - 2451545.0) / 36525.0
        D = (297.8501921 + 445267.1114034 * T) % 360
        M = (357.5291092 + 35999.0502909 * T) % 360
        M_prime = (134.9633964 + 477198.8675055 * T) % 360
        F = (93.2720950 + 483202.0175233 * T) % 360
        Omega_mean = (125.04452 - 1934.136261 * T) % 360

        periodic_terms = [
            (-1.4979, 0, 0, 0, 1),
            (-0.1500, 0, 2, 0, 0),
            (-0.1226, 0, 2, 0, 2),
            (0.1176, 0, 0, 0, 2),
            (-0.0801, 0, 2, 0, 1),
            (0.0518, 0, 0, 0, 0),
            (-0.0348, 0, 1, 0, 0),
            (-0.0304, 0, 0, 2, 0),
        ]

        Delta_Omega = 0.0
        for coeff, d_mult, m_mult, m_prime_mult, f_mult in periodic_terms:
            arg = d_mult * D + m_mult * M + m_prime_mult * M_prime + f_mult * F
            Delta_Omega += coeff * math.sin(math.radians(arg))

        Delta_Omega_deg = Delta_Omega / 3600.0
        Omega_true = Omega_mean + Delta_Omega_deg

        if node_name == "Rahu":
            return self.math.normalize_angle(Omega_true)
        else:
            return self.math.normalize_angle(Omega_true + 180.0)

    def calculate_true_obliquity(self, jd_tt):
        T = (jd_tt - 2451545.0) / 36525.0
        dPsi_deg, dEps_deg = self.nutation.compute(T)
        U = T / 100.0
        eps0_arcsec = (84381.406
                       - 46.836769 * U
                       - 0.0001831 * U**2
                       + 0.00200340 * U**3
                       - 0.000000576 * U**4
                       - 0.0000000434 * U**5)
        eps0_deg = eps0_arcsec / 3600.0
        true_obliquity = eps0_deg + dEps_deg
        return true_obliquity

    # ========================================================================
    # FORMAT BANTUAN
    # ========================================================================
    def _degrees_to_hms(self, degrees):
        hours = degrees / 15.0
        h = int(hours)
        m = int((hours - h) * 60)
        s = ((hours - h) * 60 - m) * 60
        return f"{h:02d}h{m:02d}m{s:06.3f}s"

    def _degrees_to_dms(self, degrees):
        sign = '+' if degrees >= 0 else '-'
        deg_abs = abs(degrees)
        d = int(deg_abs)
        m = int((deg_abs - d) * 60)
        s = ((deg_abs - d) * 60 - m) * 60
        return f"{sign}{d:02d}°{m:02d}'{s:06.3f}\""

    # ========================================================================
    # MATAHARI - JRC
    # ========================================================================
    def calculate_sun_position_ultra(self, jd_tt, use_long_term=False):
        """Posisi Matahari presisi tinggi menggunakan VSOP87D JRC"""
        # use_long_term diabaikan karena VSOP87 sudah jangka panjang
        sun_data = self.sun_calc.calculate_sun_position_vsop87d(jd_tt, 'equatorial_apparent')
        # Tambahkan format HMS/DMS
        sun_data['ra_hms'] = self._degrees_to_hms(sun_data['ra_deg'])
        sun_data['dec_dms'] = self._degrees_to_dms(sun_data['dec_deg'])
        # Pastikan ada kunci yang diperlukan
        sun_data['longitude'] = sun_data.get('longitude_deg', 0)
        return sun_data

    # ========================================================================
    # BULAN - JRC
    # ========================================================================
    def calculate_moon_position_ultra(self, jd_tt, sun_longitude=None, use_long_term=False):
        """Posisi Bulan presisi tinggi menggunakan ELP2000-82B JRC"""
        moon_data = self.moon_calc.calculate_position(jd_tt, output_frame='equatorial_apparent')
        # Ambil data penting
        result = {
            'longitude': moon_data['ecliptic_apparent']['longitude_deg'],
            'ra': moon_data['equatorial_apparent']['ra_deg'],
            'dec': moon_data['equatorial_apparent']['dec_deg'],
            'distance_km': moon_data['distance_km'],
            'distance_au': moon_data['distance_au'],
            'ra_hms': self._degrees_to_hms(moon_data['equatorial_apparent']['ra_deg']),
            'dec_dms': self._degrees_to_dms(moon_data['equatorial_apparent']['dec_deg']),
            'phase': None,
            'illumination': None,
            'age_days': None,
            'elongation': None
        }
        if sun_longitude is not None:
            elongation = (result['longitude'] - sun_longitude) % 360
            result['elongation'] = elongation
            result['phase'] = elongation / 360.0
            result['illumination'] = 0.5 * (1 - math.cos(math.radians(elongation))) * 100
            result['age_days'] = result['phase'] * 29.530588861
        return result

    # ========================================================================
    # AYANAMSA (Lahiri)
    # ========================================================================
    def calculate_ayanamsa_precise(self, jd_tt):
        """Ayanamsa berdasarkan J2000 dan nutasi"""
        T = (jd_tt - 2451545.0) / 36525.0
        mean_ayanamsa = 23.856858 + 0.013969712777777778 * T * 100
        # Nutasi
        dPsi_deg, _ = self.nutation.compute(T)
        true_ayanamsa = mean_ayanamsa + dPsi_deg
        return self.math.normalize_angle(true_ayanamsa)

    # ========================================================================
    # EQUATION OF TIME
    # ========================================================================
    def calculate_equation_of_time(self, jd_tt):
        sun = self.calculate_sun_position_ultra(jd_tt)
        return sun.get('equation_of_time_minutes', 0)

    # ========================================================================
    # SUNRISE/SUNSET - JRC
    # ========================================================================
    def calculate_sunrise_sunset_precise(self, jd_utc):
        """Gunakan JRC transformer untuk sunrise/sunset"""
        jd_tt = self.time_system.jd_utc_to_tt_extended(jd_utc)
        sun_data = self.sun_calc.calculate_sun_position_vsop87d(jd_tt, 'equatorial_apparent')
        result = self.transformer.get_sunrise_sunset(
            jd_utc, self.lat, self.lon,
            pressure=self.pressure,
            temperature=self.temperature,
            sun_data=sun_data
        )
        return result

    # ========================================================================
    # ALTITUDE/AZIMUTH MATAHARI
    # ========================================================================
    def calculate_sun_altitude_precise(self, jd_tt, lat=None, lon=None):
        if lat is None:
            lat = self.lat
        if lon is None:
            lon = self.lon
        sun = self.calculate_sun_position_ultra(jd_tt)
        jd_utc = jd_tt - (self.time_system.delta_t_hybrid(2000) + 32.184) / 86400.0
        altaz = self.transformer.equatorial_to_altaz(
            sun['ra_deg'], sun['dec_deg'], jd_utc,
            lat, lon, self.pressure, self.temperature+273.15, 0.5
        )
        return {
            "altitude": altaz['altitude_apparent'],
            "azimuth": altaz['azimuth'],
            "right_ascension": sun['ra_deg'],
            "declination": sun['dec_deg'],
            "longitude": sun['longitude_deg'],
            "hour_angle": altaz['hour_angle']
        }

    # ========================================================================
    # DUAL POSITIONS (Matahari & Bulan)
    # ========================================================================
    def calculate_dual_positions(self, jd_tt):
        sun_data = self.calculate_sun_position_ultra(jd_tt)
        moon_data = self.calculate_moon_position_ultra(jd_tt, sun_data['longitude_deg'])
        ayanamsa = self.calculate_ayanamsa_precise(jd_tt)

        sun_nirayana = self.math.normalize_angle(sun_data['longitude_deg'] - ayanamsa)
        moon_nirayana = self.math.normalize_angle(moon_data['longitude'] - ayanamsa)

        return {
            "jd": jd_tt,
            "ayanamsa": ayanamsa,
            "sun": {
                "tropical": sun_data['longitude_deg'],
                "nirayana": sun_nirayana,
                "ra": sun_data['ra_deg'],
                "dec": sun_data['dec_deg'],
            },
            "moon": {
                "tropical": moon_data['longitude'],
                "nirayana": moon_nirayana,
                "ra": moon_data['ra'],
                "dec": moon_data['dec'],
            },
            "equation_of_time": sun_data.get('equation_of_time_minutes', 0)
        }

    # ========================================================================
    # TITHI, NAKSHATRA, RASI (sama seperti sebelumnya)
    # ========================================================================
    def calculate_tithi(self, sun_long, moon_long, mode="tropical"):
        delta_long = (moon_long - sun_long) % 360
        tithi_index = int(delta_long / 12) + 1
        paksa = "Sukla" if delta_long < 180 else "Krsna"
        degrees_in_tithi = delta_long % 12
        return {
            "tithi": tithi_index,
            "paksa": paksa,
            "elongation": delta_long,
            "degrees_in_tithi": degrees_in_tithi,
            "mode": mode,
            "percent": (degrees_in_tithi / 12) * 100
        }

    def calculate_nakshatra(self, moon_long, mode="tropical"):
        nakshatra_span = 360 / self.const.NAKSHATRA_COUNT
        nakshatra_index = int(moon_long / nakshatra_span) + 1
        nakshatra_name = self.const.NAKSHATRAS_STANDARD[nakshatra_index - 1]
        degrees_in_nakshatra = moon_long % nakshatra_span
        pada = int(degrees_in_nakshatra / (nakshatra_span / 4)) + 1
        return {
            "nakshatra": nakshatra_name,
            "index": nakshatra_index,
            "degrees_in_nakshatra": degrees_in_nakshatra,
            "pada": pada,
            "mode": mode
        }

    def calculate_solar_ingress(self, sun_long, mode="tropical"):
        rasi_idx = int(sun_long / 30)
        rasi_name = self.const.ZODIAC[rasi_idx]
        degrees_in_rasi = sun_long % 30
        return {
            "rasi": rasi_name,
            "index": rasi_idx,
            "degrees_in_rasi": degrees_in_rasi,
            "mode": mode
        }

    # ========================================================================
    # PANCAṄGA ULTRA
    # ========================================================================
    def calculate_pancanga_ultra(self, year, month, day, hour=12, minute=0, second=0):
        jd_tt = self.time_system.wib_to_jd_tt_extended(year, month, day, hour, minute, second)
        sun_data = self.calculate_sun_position_ultra(jd_tt)
        moon_data = self.calculate_moon_position_ultra(jd_tt, sun_data['longitude_deg'])
        ayanamsa = self.calculate_ayanamsa_precise(jd_tt)

        sun_nirayana = (sun_data['longitude_deg'] - ayanamsa) % 360
        moon_nirayana = (moon_data['longitude'] - ayanamsa) % 360

        tithi = self.calculate_tithi(sun_nirayana, moon_nirayana, "nirayana")
        nakshatra = self.calculate_nakshatra(moon_nirayana, "nirayana")
        solar_ingress = self.calculate_solar_ingress(sun_nirayana, "nirayana")

        jd_utc = self.time_system.wib_to_jd_utc(year, month, day, hour, minute, second)
        sunrise_info = self.calculate_sunrise_sunset_precise(jd_utc)

        return {
            "date": f"{day:02d}/{month:02d}/{year}",
            "time": f"{hour:02d}:{minute:02d}:{second:02d} WIB",
            "jd_tt": jd_tt,
            "ayanamsa": ayanamsa,
            "sun": {
                "tropical": sun_data['longitude_deg'],
                "nirayana": sun_nirayana,
                "ra": sun_data['ra_hms'],
                "dec": sun_data['dec_dms']
            },
            "moon": {
                "tropical": moon_data['longitude'],
                "nirayana": moon_nirayana,
                "ra": moon_data['ra_hms'],
                "dec": moon_data['dec_dms'],
                "phase": moon_data['phase'],
                "illumination": moon_data['illumination']
            },
            "tithi": tithi,
            "nakshatra": nakshatra,
            "solar_ingress": solar_ingress,
            "sunrise_sunset": sunrise_info,
            "calculation_model": "JRC-VSOP87+ELP2000"
        }

    # ========================================================================
    # PLANET (menggunakan sistem lama, tetapi dengan JD TT yang benar)
    # ========================================================================
    def calculate_planet_position_enhanced(self, planet_name, jd_tt, precision='MEDIUM'):
        """Menggunakan sistem planet lama, dengan JD TT"""
        if planet_name == "Surya":
            sun = self.calculate_sun_position_ultra(jd_tt)
            return {
                'longitude': sun['longitude_deg'],
                'longitude_nirayana': (sun['longitude_deg'] - self.calculate_ayanamsa_precise(jd_tt)) % 360,
                'latitude': 0,
                'distance_au': sun['radius_au'],
                'model': 'JRC-VSOP87',
                'accuracy_deg': 0.1/3600,
                'calculation_type': 'geocentric'
            }
        elif planet_name == "Candra":
            moon = self.calculate_moon_position_ultra(jd_tt)
            return {
                'longitude': moon['longitude'],
                'longitude_nirayana': (moon['longitude'] - self.calculate_ayanamsa_precise(jd_tt)) % 360,
                'latitude': 0,
                'distance_au': moon['distance_au'],
                'model': 'JRC-ELP2000',
                'accuracy_deg': 0.5/3600,
                'calculation_type': 'geocentric'
            }
        elif planet_name in ["Rahu", "Ketu"]:
            long = self.calculate_lunar_nodes_precise(jd_tt, planet_name)
            ayanamsa = self.calculate_ayanamsa_precise(jd_tt)
            long_nirayana = (long - ayanamsa) % 360
            return {
                'longitude': long,
                'longitude_nirayana': long_nirayana,
                'latitude': 0.0,
                'distance_au': 0.0,
                'model': 'Lunar Nodes (IAU2000)',
                'accuracy_deg': 0.1,
                'calculation_type': 'geocentric'
            }
        else:
            # Planet lain menggunakan sistem lama
            sun_helio = {
                'longitude': (self.calculate_sun_position_ultra(jd_tt)['longitude_deg'] + 180) % 360,
                'distance_au': self.calculate_sun_position_ultra(jd_tt)['radius_au']
            }
            planet_result = self.planet_system.calculate_geocentric_position(
                planet_name, jd_tt, sun_helio
            )
            ayanamsa = self.calculate_ayanamsa_precise(jd_tt)
            longitude_nirayana = (planet_result['longitude'] - ayanamsa) % 360
            return {
                'longitude': planet_result['longitude'],
                'longitude_nirayana': longitude_nirayana,
                'latitude': planet_result['latitude'],
                'distance_au': planet_result['distance_au'],
                'model': planet_result['model'],
                'accuracy_deg': planet_result['accuracy_deg'],
                'calculation_type': 'geocentric',
                'ayanamsa': ayanamsa,
                'precision': precision
            }

    def calculate_all_planets_enhanced(self, jd_tt, precision='MEDIUM'):
        """Hitung semua planet dengan model baru"""
        planets = ["Surya", "Candra", "Budha", "Sukra", "Mangala",
                  "Brihaspati", "Sani", "Rahu", "Ketu"]

        results = {}
        for planet in planets:
            try:
                results[planet] = self.calculate_planet_position_enhanced(
                    planet, jd_tt, precision
                )
            except Exception as e:
                results[planet] = {
                    'error': str(e),
                    'longitude': 0.0,
                    'model': 'ERROR'
                }

        return results


# ============================================================================
# SISTEM PLANET UPGRADED - DIPERTAHANKAN DARI VERSI LAMA, DENGAN KONSTANTA JRC
# ============================================================================
class VSOP87Compact:
    """VSOP87 Compact untuk 5 planet utama - menggunakan konstanta JRC"""

    def __init__(self, time_sys, const):
        self.time_sys = time_sys
        self.const = const
        self.planet_coeffs = self._load_compact_coefficients()

    def _load_compact_coefficients(self):
        """Koefisien VSOP87 terkompresi (100 term terbesar)"""
        return {
            "Merkurius": {
                "L": [
                    (4.402608842, 0.000000000, 0.000000000),
                    (0.149058303, 4.083049922, 26087.903141574),
                    (0.075976756, 1.260508824, 52175.806283148),
                    (0.005849879, 4.220904666, 78263.709424723),
                    (0.003034701, 3.055654724, 52171.924947790),
                    (0.000635536, 4.354898733, 104351.612566297),
                    (0.000196766, 2.809651117, 130439.515707871),
                    (0.000051040, 5.794323535, 156527.418849445),
                    (0.000013592, 2.372136924, 182615.321991019),
                ],
                "accuracy": 0.01
            },
            "Venus": {
                "L": [
                    (3.176146667, 0.000000000, 0.000000000),
                    (0.013539684, 5.593133196, 10213.285546211),
                    (0.000898916, 5.306500477, 20426.571092422),
                    (0.000054758, 4.926406896, 7860.419392439),
                    (0.000034557, 2.699644478, 11790.629088659),
                    (0.000023720, 2.993775396, 3930.209696220),
                    (0.000013171, 5.186682284, 26.298319800),
                    (0.000016641, 4.250189100, 1577.343542448),
                ],
                "accuracy": 0.005
            },
            "Mars": {
                "L": [
                    (6.203477116, 0.000000000, 0.000000000),
                    (0.186563681, 5.050371003, 3340.612426700),
                    (0.011082168, 5.400998369, 6681.224853400),
                    (0.000917984, 5.754787451, 10021.837280099),
                    (0.000277450, 5.970495131, 3.523118349),
                    (0.000106102, 2.939585250, 2281.230496511),
                    (0.000123158, 0.849560813, 2810.921461605),
                    (0.000089267, 4.156978464, 0.017253652),
                ],
                "accuracy": 0.02
            },
            "Jupiter": {
                "L": [
                    (0.599546915, 0.000000000, 0.000000000),
                    (0.096958987, 5.061917931, 529.690965095),
                    (0.005736101, 1.444062060, 7.113547001),
                    (0.003063892, 5.417347300, 1059.381930189),
                    (0.000972146, 4.142647088, 632.783739313),
                    (0.000729030, 3.640429093, 522.577418094),
                    (0.000642640, 3.411451852, 103.092774219),
                    (0.000398060, 2.293767449, 419.484643875),
                ],
                "accuracy": 0.01
            },
            "Saturnus": {
                "L": [
                    (0.874013540, 0.000000000, 0.000000000),
                    (0.111076598, 3.962050902, 213.299095438),
                    (0.014141510, 4.585815159, 7.113547001),
                    (0.003983793, 0.521120528, 206.185548437),
                    (0.003507692, 3.303299030, 426.598190876),
                    (0.002068163, 0.246583669, 103.092774219),
                    (0.000792713, 3.840070785, 220.412642439),
                    (0.000239903, 4.669769349, 110.206321219),
                ],
                "accuracy": 0.015
            }
        }

    def calculate_planet_heliocentric(self, planet_name: str, T: float):
        if planet_name not in self.planet_coeffs:
            raise ValueError(f"Planet {planet_name} tidak didukung")

        coeffs = self.planet_coeffs[planet_name]["L"]

        L = 0.0
        for A, B, C in coeffs:
            L += A * np.cos(B + C * T)

        if planet_name in ["Merkurius", "Venus"]:
            M = 174.7947 + 149472.515 * T if planet_name == "Merkurius" else 50.4161 + 58517.815 * T
            e = 0.205635 + 0.000020 * T if planet_name == "Merkurius" else 0.006777 - 0.000041 * T
            C_deg = (2 * e - e**3/4) * np.sin(np.radians(M)) + \
                   (5/4 * e**2) * np.sin(np.radians(2*M)) + \
                   (13/12 * e**3) * np.sin(np.radians(3*M))
            L += C_deg

        L = L % 360

        if planet_name == "Merkurius":
            R = 0.387099
        elif planet_name == "Venus":
            R = 0.723332
        elif planet_name == "Mars":
            R = 1.523679
        elif planet_name == "Jupiter":
            R = 5.202603
        elif planet_name == "Saturnus":
            R = 9.554910
        else:
            R = 0.0

        return {
            "longitude": L,
            "latitude": 0.0,
            "distance_au": R,
            "accuracy_deg": self.planet_coeffs[planet_name]["accuracy"],
            "model": "VSOP87_Compact"
        }


class SidiPlanetaryTheory:
    """Model Sidi untuk ±10,000 tahun - akurasi 0.5°"""

    def __init__(self, time_sys, const):
        self.time_sys = time_sys
        self.const = const

    def calculate_planet_long_term(self, planet_name: str, T: float):
        if planet_name == "Merkurius":
            L = 252.250 + 149472.515 * T + 0.00003 * T**2
            a = 0.387099 + 0.00000037 * T
            e = 0.205636 - 0.000019 * T
        elif planet_name == "Venus":
            L = 181.979 + 58517.815 * T + 0.00002 * T**2
            a = 0.723336 + 0.0000039 * T
            e = 0.006777 - 0.000041 * T
        elif planet_name == "Mars":
            L = 355.433 + 19141.696 * T + 0.00031 * T**2
            a = 1.523679
            e = 0.093400
            L += 0.0071 * np.sin(np.radians(53.47 * T + 144.96))
            L += 0.0057 * np.sin(np.radians(30.35 * T + 55.19))
        elif planet_name == "Jupiter":
            L = 34.351 + 3034.906 * T + 0.00029 * T**2
            a = 5.202603
            e = 0.048495
            L += 0.0033 * np.sin(np.radians(882.0 * T + 123.6))
        elif planet_name == "Saturnus":
            L = 50.077 + 1222.114 * T + 0.00052 * T**2
            a = 9.554910
            e = 0.055509
        else:
            raise ValueError(f"Planet {planet_name} tidak didukung")

        M = L % 360
        E = self._solve_kepler(M, e)
        nu = 2 * np.arctan2(np.sqrt(1+e) * np.sin(E/2), np.sqrt(1-e) * np.cos(E/2))
        true_longitude = (np.degrees(nu) + L - M) % 360

        return {
            "longitude": true_longitude,
            "latitude": 0.0,
            "distance_au": a,
            "accuracy_deg": 0.05 if abs(T) < 40 else 0.5,
            "model": "Sidi_LongTerm"
        }

    def _solve_kepler(self, M_deg: float, e: float) -> float:
        M_rad = np.radians(M_deg)
        E = M_rad
        for _ in range(10):
            delta = E - e * np.sin(E) - M_rad
            if abs(delta) < 1e-12:
                break
            E = E - delta / (1 - e * np.cos(E))
        return E


class ImprovedKeplerian:
    """Model Keplerian dengan perturbasi selektif - akurasi 0.05°"""

    def __init__(self, time_sys, const):
        self.time_sys = time_sys
        self.const = const
        self.perturbation_terms = self._load_perturbation_terms()

    def _load_perturbation_terms(self):
        return {
            "Mars": [
                {"amplitude": 0.0071, "frequency": 53.47, "phase": 144.96},
                {"amplitude": 0.0057, "frequency": 30.35, "phase": 55.19},
            ],
            "Jupiter": [
                {"amplitude": 0.0033, "frequency": 882.0, "phase": 123.6},
            ],
            "Saturnus": [
                {"amplitude": 0.0022, "frequency": 882.0, "phase": 303.6},
            ]
        }

    def calculate_planet_with_perturbations(self, planet_name: str, T: float):
        elements = self._get_orbital_elements(planet_name, T)

        M = elements["L"] - elements["pi"]
        M = M % 360

        E = self._solve_kepler(M, elements["e"])

        nu = 2 * np.arctan2(
            np.sqrt(1 + elements["e"]) * np.sin(E/2),
            np.sqrt(1 - elements["e"]) * np.cos(E/2)
        )

        true_longitude = (np.degrees(nu) + elements["pi"]) % 360

        if planet_name in self.perturbation_terms:
            perturbation = 0.0
            for term in self.perturbation_terms[planet_name]:
                perturbation += term["amplitude"] * np.sin(
                    np.radians(term["frequency"] * T + term["phase"])
                )
            true_longitude += perturbation

        r = elements["a"] * (1 - elements["e"] * np.cos(E))

        return {
            "longitude": true_longitude % 360,
            "latitude": 0.0,
            "distance_au": r,
            "accuracy_deg": 0.1,
            "model": "Keplerian_Improved"
        }

    def _get_orbital_elements(self, planet_name: str, T: float):
        if planet_name == "Merkurius":
            return {
                "a": 0.38709927 + 0.00000037 * T,
                "e": 0.20563593 + 0.00001906 * T,
                "L": 252.2503235 + 149472.6741118 * T,
                "pi": 77.45611904 + 0.1588643 * T
            }
        elif planet_name == "Venus":
            return {
                "a": 0.72333566 + 0.00000390 * T,
                "e": 0.00677672 - 0.00004107 * T,
                "L": 181.97909985 + 58517.81538729 * T,
                "pi": 131.56370700 + 0.0048646 * T
            }
        elif planet_name == "Mars":
            return {
                "a": 1.52367934,
                "e": 0.09340065,
                "L": 355.433 + 19141.696447 * T,
                "pi": 336.060234 + 0.443901 * T
            }
        elif planet_name == "Jupiter":
            return {
                "a": 5.202603191 + 0.0000001913 * T,
                "e": 0.04849485 + 0.000163244 * T,
                "L": 34.351484 + 3034.9056746 * T,
                "pi": 14.331309 + 0.2155525 * T
            }
        elif planet_name == "Saturnus":
            return {
                "a": 9.554909595 - 0.0000021389 * T,
                "e": 0.05550862 - 0.0003448181 * T,
                "L": 50.077471 + 1222.1137943 * T,
                "pi": 93.056787 + 0.5665496 * T
            }
        else:
            raise ValueError(f"Planet {planet_name} tidak didukung")

    def _solve_kepler(self, M_deg: float, e: float) -> float:
        M_rad = np.radians(M_deg)
        E = M_rad
        for _ in range(10):
            delta = E - e * np.sin(E) - M_rad
            if abs(delta) < 1e-10:
                break
            E = E - delta / (1 - e * np.cos(E))
        return E


class PlanetarySystemUpgraded:
    """Sistem hierarki presisi planet - DIPERTAHANKAN DENGAN KONSTANTA JRC"""

    def __init__(self, time_sys, const):
        self.time_sys = time_sys
        self.const = const
        self.vsop87_compact = VSOP87Compact(time_sys, const)
        self.sidi_theory = SidiPlanetaryTheory(time_sys, const)
        self.improved_keplerian = ImprovedKeplerian(time_sys, const)

        self.planet_mapping = {
            "Budha": "Merkurius",
            "Sukra": "Venus",
            "Mangala": "Mars",
            "Brihaspati": "Jupiter",
            "Sani": "Saturnus"
        }

    def get_planet_position(self, planet_name: str, jd_tt: float,
                          required_precision: str = 'MEDIUM'):
        """
        Dapatkan posisi planet dengan presisi yang diminta
        required_precision: 'LOW', 'MEDIUM', 'HIGH'
        """
        astro_name = self.planet_mapping.get(planet_name, planet_name)
        T = (jd_tt - 2451545.0) / 36525.0

        if required_precision == 'HIGH' and abs(T) < 20:
            result = self.vsop87_compact.calculate_planet_heliocentric(astro_name, T)
            result['heliocentric'] = True
            return result

        elif required_precision == 'MEDIUM' and abs(T) < 40:
            result = self.improved_keplerian.calculate_planet_with_perturbations(astro_name, T)
            result['heliocentric'] = True
            return result

        else:
            result = self.sidi_theory.calculate_planet_long_term(astro_name, T)
            result['heliocentric'] = True
            return result

    def calculate_geocentric_position(self, planet_name: str, jd_tt: float,
                                    earth_heliocentric: Dict[str, float]):
        """
        Konversi heliosentrik ke geosentrik
        """
        planet_helio = self.get_planet_position(planet_name, jd_tt, 'MEDIUM')

        lon_geo = (planet_helio['longitude'] - earth_heliocentric['longitude'] + 180) % 360

        return {
            'longitude': lon_geo,
            'latitude': 0.0,
            'distance_au': planet_helio['distance_au'],
            'model': planet_helio['model'],
            'accuracy_deg': planet_helio['accuracy_deg'],
            'calculation_type': 'geocentric_simplified'
        }


# ============================================================================
# VEDIC TIME ENGINE - DITINGKATKAN DENGAN JRC
# ============================================================================
class VedicTimeEngine:
    """Engine untuk menghitung Yoga, Karana, Parwesa, Muhurta, dan Lagna"""

    def __init__(self, latitude=None, longitude=None, timezone_offset=None):
        self.const = ΩConstants
        self.math = MathCore()
        self.norm = NormalizationEngine()

        self.lat = latitude if latitude is not None else self.const.LOC_LAT
        self.lon = longitude if longitude is not None else self.const.LOC_LON
        self.tz_offset = timezone_offset if timezone_offset is not None else self.const.LOC_TZ_OFFSET

        # Sistem baru
        self.time_system = TimeSystem()
        self.astro = AstronomicalEngine(self.lat, self.lon)
        self.transformer = UnifiedCoordinateTransformer()

    def calculate_yoga(self, sun_long, moon_long):
        """Hitung Yoga berdasarkan bujur Matahari dan Bulan"""
        total_long = (sun_long + moon_long) % 360
        yoga_index = int(total_long // (360/27))
        if yoga_index >= 27:
            yoga_index = 26
        yoga_name = self.const.YOGAS[yoga_index]
        degrees_in_yoga = total_long % (360/27)
        return {
            "index": yoga_index,
            "name": yoga_name,
            "total_longitude": total_long,
            "degrees_in_yoga": degrees_in_yoga,
            "percent": (degrees_in_yoga / (360/27)) * 100
        }

    def calculate_karana(self, sun_long, moon_long):
        """
        Hitung Karana berdasarkan bujur Matahari dan Bulan (derajat).
        Mengembalikan dictionary berisi informasi karana lengkap.
        """
        elongation = (moon_long - sun_long) % 360
        # Karana number 1..60 (setiap 6° satu karana)
        karana_num = int(elongation // 6) + 1

        # Daftar 60 karana dalam urutan yang benar
        base_7 = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
        karana_60 = ["Kimstughna"]                     # karana pertama
        for i in range(56):                            # 56 karana berikutnya (2–57)
            karana_60.append(base_7[i % 7])
        karana_60.append("Sakuni")                     # karana ke-58
        karana_60.append("Catuspada")                  # karana ke-59
        karana_60.append("Naga")                       # karana ke-60

        # Ambil nama karana (indeks 0‑based)
        karana_name = karana_60[karana_num - 1]

        # Informasi tambahan untuk kompatibilitas
        tithi_index = int(elongation // 12) + 1          # 1..30
        paksa = "Sukla" if elongation < 180 else "Krsna"
        degrees_in_karana = elongation % 6                # 0..6°

        # Indeks dalam daftar 11 karana (untuk kompatibilitas)
        if karana_name in self.const.KARANAS:
            karana_type = self.const.KARANAS.index(karana_name)
        else:
            karana_type = -1

        return {
            "name": karana_name,
            "index": karana_num - 1,                     # 0‑based (0..59)
            "type": karana_type,                          # indeks dalam daftar 11 karana
            "karana_num": karana_num,                     # 1‑based
            "tithi": tithi_index,
            "paksa": paksa,
            "elongation": elongation,
            "degrees_in_karana": degrees_in_karana
        }

    def calculate_parwesa_gompers(self, ka):
        """Hitung Parwesa berdasarkan sistem Gomperts"""
        P = self.const.PARWESA_G0MPERS["P_PERIOD"]
        C = self.const.PARWESA_G0MPERS["C_OFFSET"]
        parwesa_index = int((7 * ((ka + C) % P)) / P) + 1
        if parwesa_index < 1:
            parwesa_index = 1
        elif parwesa_index > 7:
            parwesa_index = 7
        parwesa_name = self.const.PARWESA_G0MPERS["MAPPING"][parwesa_index - 1]
        return {
            "system": "Gomperts",
            "index": parwesa_index,
            "name": parwesa_name,
            "ka": ka,
            "position_in_period": ((ka + C) % P) / P
        }

    def calculate_dynamic_rasimana(self, jd):
        """
        Hitung durasi terbit (Rasimana) setiap rasi secara dinamis
        berdasarkan Obliquity dan Latitude saat itu.
        """
        T = (jd - 2451545.0) / 36525.0
        eps0 = self.const.OBLIQUITY
        obliquity = eps0 - 46.84024 * T / 3600.0
        lat = self.lat
        rasimanas = {}
        ascensional_diffs = []
        for i in range(0, 13):
            long_deg = i * 30
            sin_dec = self.math.sin_d(long_deg) * self.math.sin_d(obliquity)
            dec = self.math.asin_d(sin_dec)
            ad_val = self.math.tan_d(lat) * self.math.tan_d(dec)
            ad_val = max(-1, min(1, ad_val))
            asc_diff = self.math.asin_d(ad_val)
            ascensional_diffs.append(asc_diff)
        oblique_ascensions = []
        for i in range(13):
            long_deg = i * 30
            y = self.math.cos_d(obliquity) * self.math.sin_d(long_deg)
            x = self.math.cos_d(long_deg)
            ra = self.math.atan2_d(y, x)
            if ra < 0:
                ra += 360
            oa = ra - ascensional_diffs[i]
            if oa < 0:
                oa += 360
            oblique_ascensions.append(oa)
        for i in range(12):
            diff = oblique_ascensions[i+1] - oblique_ascensions[i]
            if diff < 0:
                diff += 360
            rasimanas[i] = diff * 4.0
        return rasimanas

    def calculate_sunrise_sunset(self, jd_noon):
        """Hitung waktu matahari terbit dan terbenam lokal"""
        return self.astro.calculate_sunrise_sunset_precise(jd_noon)

    def calculate_muhurta_jawa_kuno(self, ka, current_hour=10.5):
        """Hitung Muhurta Jawa Kuno (15 muhurta siang, 15 muhurta malam)"""
        jd_noon = self.math.ka_to_jd(ka)
        sunrise_info = self.calculate_sunrise_sunset(jd_noon)
        if not sunrise_info:
            return None

        def parse_time(time_str):
            parts = time_str.split(':')
            return float(parts[0]) + float(parts[1])/60.0 + float(parts[2])/3600.0

        sunrise = parse_time(sunrise_info.get('sunrise', {}).get('wib', '06:00:00'))
        sunset = parse_time(sunrise_info.get('sunset', {}).get('wib', '18:00:00'))

        if sunset < sunrise:
            sunset += 24

        if sunrise <= current_hour < sunset:
            day_length = sunset - sunrise
            muhurta_length = day_length / 15
            time_from_sunrise = current_hour - sunrise
            muhurta_index = int(time_from_sunrise / muhurta_length)
            if muhurta_index < 0:
                muhurta_index = 0
            elif muhurta_index >= 15:
                muhurta_index = 14
            muhurta_name = self.const.MUHURTA_AUDAYIKA[muhurta_index]
            return {
                "system": "Jawa Kuno",
                "period": "Siang",
                "index": muhurta_index,
                "total_muhurta": 15,
                "name": muhurta_name,
                "sunrise": sunrise_info.get('sunrise', {}).get('wib', ''),
                "sunset": sunrise_info.get('sunset', {}).get('wib', ''),
                "period_start": sunrise_info.get('sunrise', {}).get('wib', ''),
                "period_end": sunrise_info.get('sunset', {}).get('wib', ''),
                "period_length": day_length,
                "muhurta_length": muhurta_length,
                "time_from_start": time_from_sunrise,
                "ishta_kala": time_from_sunrise * 60,
                "current_hour": current_hour,
                "progress": (time_from_sunrise % muhurta_length) / muhurta_length * 100
            }
        else:
            if current_hour < sunrise:
                night_length = (24 - sunset) + sunrise
                time_from_sunset = (24 - sunset) + current_hour
            else:
                night_length = sunrise + 24 - sunset
                time_from_sunset = current_hour - sunset
            muhurta_length = night_length / 15
            muhurta_index = int(time_from_sunset / muhurta_length)
            if muhurta_index < 0:
                muhurta_index = 0
            elif muhurta_index >= 15:
                muhurta_index = 14
            muhurta_name = self.const.MUHURTA_AUDAYIKA[muhurta_index]
            return {
                "system": "Jawa Kuno",
                "period": "Malam",
                "index": muhurta_index,
                "total_muhurta": 15,
                "name": muhurta_name,
                "sunrise": sunrise_info.get('sunrise', {}).get('wib', ''),
                "sunset": sunrise_info.get('sunset', {}).get('wib', ''),
                "period_start": sunrise_info.get('sunset', {}).get('wib', ''),
                "period_end": sunrise_info.get('sunrise', {}).get('wib', ''),
                "period_length": night_length,
                "muhurta_length": muhurta_length,
                "time_from_start": time_from_sunset,
                "ishta_kala": time_from_sunset * 60,
                "current_hour": current_hour,
                "progress": (time_from_sunset % muhurta_length) / muhurta_length * 100
            }

    def calculate_tabeh_precise(self, ka, current_hour=10.5):
        """Hitung Tabeh (8 bagian waktu siang atau malam)"""
        jd_noon = self.math.ka_to_jd(ka)
        sunrise_info = self.calculate_sunrise_sunset(jd_noon)
        if not sunrise_info:
            return None

        def parse_time(time_str):
            parts = time_str.split(':')
            return float(parts[0]) + float(parts[1])/60.0 + float(parts[2])/3600.0

        sunrise = parse_time(sunrise_info.get('sunrise', {}).get('wib', '06:00:00'))
        sunset = parse_time(sunrise_info.get('sunset', {}).get('wib', '18:00:00'))

        if sunset < sunrise:
            sunset += 24

        day_length = sunset - sunrise
        night_length = 24 - day_length

        current_hour_norm = current_hour % 24

        if sunset < sunrise:
            if current_hour_norm >= sunrise and current_hour_norm < sunset + 24:
                period_type = "siang"
                if current_hour_norm < sunrise:
                    current_hour_norm += 24
            else:
                period_type = "malam"
        else:
            if current_hour_norm >= sunrise and current_hour_norm < sunset:
                period_type = "siang"
            else:
                period_type = "malam"

        if period_type == "siang":
            period_start = sunrise
            period_length = day_length
            calc_hour = current_hour_norm
            if calc_hour < period_start:
                calc_hour += 24
        else:
            if current_hour_norm < sunrise:
                period_start = sunset - 24
                period_length = night_length
                calc_hour = current_hour_norm
            else:
                period_start = sunset
                period_length = night_length
                calc_hour = current_hour_norm
                if calc_hour < period_start:
                    calc_hour += 24

        if period_length <= 0:
            period_length = 12.0

        tabeh_duration_hours = period_length / 8
        hours_from_start = calc_hour - period_start
        if hours_from_start < 0:
            hours_from_start += 24
        elif hours_from_start > period_length:
            hours_from_start -= 24

        tabeh_index = int(hours_from_start / tabeh_duration_hours)
        if tabeh_index >= 8:
            tabeh_index = 7
        elif tabeh_index < 0:
            tabeh_index = 0

        tabeh_name = self.const.TABEH_NAMES[period_type][tabeh_index]

        def hour_to_hhmm(hour_float):
            hour_norm = hour_float % 24
            h = int(hour_norm)
            m = int((hour_norm - h) * 60)
            s = int(((hour_norm - h) * 60 - m) * 60)
            return f"{h:02d}:{m:02d}:{s:02d}"

        start_hour = period_start + tabeh_index * tabeh_duration_hours
        end_hour = start_hour + tabeh_duration_hours

        return {
            "period_type": period_type,
            "tabeh_index": tabeh_index + 1,
            "tabeh_name": tabeh_name,
            "start_time": hour_to_hhmm(start_hour),
            "end_time": hour_to_hhmm(end_hour),
            "current_time": hour_to_hhmm(current_hour_norm),
            "duration_hours": tabeh_duration_hours,
            "duration_minutes": tabeh_duration_hours * 60,
            "sunrise": hour_to_hhmm(sunrise),
            "sunset": hour_to_hhmm(sunset),
            "day_length_hours": day_length,
            "night_length_hours": night_length,
        }

    def calculate_nadi_vinadi(self, ishta_kala_minutes: float) -> Dict[str, Any]:
        """
        Convert Ishta Kala (minutes since sunrise) into traditional Vedic units:
        Nadi (1 Nadi = 24 minutes), Vinadi (1 Vinadi = 24 seconds), and Lipta (1 Lipta = 0.4 seconds).
        """
        total_seconds = ishta_kala_minutes * 60
        nadi = int(total_seconds // (24 * 60))
        remaining_seconds = total_seconds % (24 * 60)
        vinadi = int(remaining_seconds // 24)
        remaining_seconds %= 24
        lipta = int(remaining_seconds / 0.4) if remaining_seconds > 0 else 0

        return {
            'nadi': nadi,
            'vinadi': vinadi,
            'lipta': lipta,
            'total_vinadi': total_seconds / 24,
            'description': f"{nadi} Nadi {vinadi} Vinadi {lipta} Lipta",
            'since_sunrise_minutes': ishta_kala_minutes,
            'since_sunrise_seconds': total_seconds
        }

    def calculate_lagna_precise(self, sun_long, ishta_kala_minutes, jd):
        """Hitung Lagna menggunakan Rasimana Dinamis"""
        rasimana_table = self.calculate_dynamic_rasimana(jd)

        sun_long_norm = sun_long % 360
        sun_rasi_idx = int(sun_long_norm // 30)
        sun_deg_rem = sun_long_norm % 30

        rasi_duration = rasimana_table[sun_rasi_idx]

        time_passed_in_rasi = (sun_deg_rem / 30.0) * rasi_duration
        time_remaining_in_rasi = rasi_duration - time_passed_in_rasi

        if ishta_kala_minutes < 0:
            time_to_go_back = abs(ishta_kala_minutes)
            if time_to_go_back > time_passed_in_rasi:
                time_to_go_back -= time_passed_in_rasi
                curr_idx = (sun_rasi_idx - 1) % 12
                while time_to_go_back > rasimana_table[curr_idx]:
                    time_to_go_back -= rasimana_table[curr_idx]
                    curr_idx = (curr_idx - 1) % 12
                fraction = (rasimana_table[curr_idx] - time_to_go_back) / rasimana_table[curr_idx]
                deg_lagna = fraction * 30.0
            else:
                curr_idx = sun_rasi_idx
                time_remaining = time_passed_in_rasi - time_to_go_back
                fraction = time_remaining / rasi_duration
                deg_lagna = fraction * 30.0
        else:
            rem_time = ishta_kala_minutes
            curr_idx = sun_rasi_idx
            if rem_time > time_remaining_in_rasi:
                rem_time -= time_remaining_in_rasi
                curr_idx = (curr_idx + 1) % 12
                while rem_time > rasimana_table[curr_idx]:
                    rem_time -= rasimana_table[curr_idx]
                    curr_idx = (curr_idx + 1) % 12
                fraction = rem_time / rasimana_table[curr_idx]
                deg_lagna = fraction * 30.0
            else:
                total_time = time_passed_in_rasi + rem_time
                fraction = total_time / rasi_duration
                deg_lagna = fraction * 30.0

        deg_lagna = deg_lagna % 30
        if deg_lagna < 0:
            deg_lagna += 30

        abs_deg = curr_idx * 30 + deg_lagna
        abs_deg = abs_deg % 360

        return {
            "lagna_rasi_index": curr_idx,
            "lagna_rasi_name": self.const.ZODIAC[curr_idx],
            "deg_in_rasi": deg_lagna,
            "absolute_ecliptic_deg": abs_deg,
            "mode": "nirayana",
            "rasimana_table": rasimana_table,
            "ishta_kala": ishta_kala_minutes,
            "sun_longitude": sun_long_norm,
            "sun_rasi_index": sun_rasi_idx,
            "sun_deg_in_rasi": sun_deg_rem,
            "calculation_method": "Rasimana Dinamis (JRC Enhanced)"
        }

    def calculate_all_vedic_time(self, ka, current_hour=10.5):
        """Hitung semua komponen waktu Vedic"""
        jd_noon = self.math.ka_to_jd(ka)
        jd_current = jd_noon + (current_hour - 12) / 24

        positions = self.astro.calculate_dual_positions(jd_current)

        yoga_sayana = self.calculate_yoga(
            positions["sun"]["tropical"],
            positions["moon"]["tropical"]
        )
        yoga_nirayana = self.calculate_yoga(
            positions["sun"]["nirayana"],
            positions["moon"]["nirayana"]
        )

        karana_sayana = self.calculate_karana(
            positions["sun"]["tropical"],
            positions["moon"]["tropical"]
        )
        karana_nirayana = self.calculate_karana(
            positions["sun"]["nirayana"],
            positions["moon"]["nirayana"]
        )

        parwesa = self.calculate_parwesa_gompers(ka)

        sunrise_info = self.calculate_sunrise_sunset(jd_noon)
        if sunrise_info:
            sunrise_str = sunrise_info.get('sunrise', {}).get('wib', '06:00:00')
            def parse_time(time_str):
                parts = time_str.split(':')
                return float(parts[0]) + float(parts[1])/60.0 + float(parts[2])/3600.0
            sunrise_hour = parse_time(sunrise_str)
            if current_hour < sunrise_hour:
                ishta_kala = ((current_hour + 24) - sunrise_hour) * 60
            else:
                ishta_kala = (current_hour - sunrise_hour) * 60
        else:
            ishta_kala = 0

        muhurta = self.calculate_muhurta_jawa_kuno(ka, current_hour)
        tabeh = self.calculate_tabeh_precise(ka, current_hour)

        lagna_nirayana = self.calculate_lagna_precise(
            positions["sun"]["nirayana"],
            ishta_kala,
            jd_current
        )

        return {
            "ka": ka,
            "julian_day": jd_current,
            "current_hour": current_hour,
            "ishta_kala_minutes": ishta_kala,
            "sunrise_hour": sunrise_hour if sunrise_info else None,
            "yoga": {"sayana": yoga_sayana, "nirayana": yoga_nirayana},
            "karana": {"sayana": karana_sayana, "nirayana": karana_nirayana},
            "parwesa": parwesa,
            "muhurta": muhurta,
            "tabeh": tabeh,
            "lagna": {"nirayana": lagna_nirayana},
            "positions": positions
        }


# ============================================================================
# GRAHACARA ASTHA ENGINE - JRC ENHANCED
# ============================================================================
class GrahacaraAsthaEngine:
    """Engine Grahacara Astha - BERDASARKAN LHA (Local Hour Angle)"""

    def __init__(self, latitude=None, longitude=None, timezone_offset=None):
        self.const = ΩConstants
        self.math = MathCore()
        self.norm = NormalizationEngine()

        self.lat = latitude if latitude is not None else self.const.LOC_LAT
        self.lon = longitude if longitude is not None else self.const.LOC_LON
        self.tz_offset = timezone_offset if timezone_offset is not None else self.const.LOC_TZ_OFFSET

        self.time_system = TimeSystem()
        self.astro = AstronomicalEngine(self.lat, self.lon)
        self.transformer = UnifiedCoordinateTransformer()

    def calculate_lha(self, ra: float, jd_utc: float, lon: float = None) -> float:
        if lon is None:
            lon = self.lon
        T = (jd_utc - 2451545.0) / 36525.0
        GMST = 280.46061837 + 360.98564736629 * (jd_utc - 2451545.0) + \
               0.000387933 * T**2 - T**3/38710000.0
        GMST = GMST % 360
        LST = GMST + lon
        LST = LST % 360
        LHA = LST - ra
        if LHA > 180:
            LHA -= 360
        elif LHA < -180:
            LHA += 360
        return LHA

    def lha_to_diagram_angle(self, lha: float) -> float:
        if lha < 0:
            diagram = 360 + lha
        else:
            diagram = lha
        return diagram

    def get_astha_zone_from_lha(self, lha: float) -> Dict:
        diagram_angle = self.lha_to_diagram_angle(lha)
        for zone_name, zone_info in self.const.ASTHA_ZONES.items():
            start, end = zone_info["range"]
            if start <= diagram_angle < end:
                return {
                    "zone": zone_name,
                    "lha": lha,
                    "diagram_angle": diagram_angle,
                    "range": zone_info["range"],
                    "description": zone_info["waktu"],
                    "status": zone_info["status"]
                }
        if diagram_angle == 360:
            zone_name = "Dakṣiṇasthā"
            zone_info = self.const.ASTHA_ZONES[zone_name]
            return {
                "zone": zone_name,
                "lha": lha,
                "diagram_angle": diagram_angle,
                "range": zone_info["range"],
                "description": zone_info["waktu"],
                "status": zone_info["status"]
            }
        return {
            "zone": "Unknown",
            "lha": lha,
            "diagram_angle": diagram_angle,
            "range": (0, 0),
            "description": "Zona tidak diketahui",
            "status": "Tidak terdefinisi"
        }

    def analyze_planet_position(self, planet_name: str, jd_tt: float,
                               current_hour: float = None) -> Dict:
        date_info = self.time_system.jd_to_gregorian(jd_tt)
        year_astro = date_info['year_astronomical']
        delta_t_seconds = self.time_system.delta_t_hybrid(year_astro)
        jd_utc = jd_tt - (delta_t_seconds + 32.184) / 86400.0

        if planet_name == "Surya":
            sun_data = self.astro.calculate_sun_position_ultra(jd_tt)
            ra = sun_data['ra_deg']
            dec = sun_data['dec_deg']
            long = sun_data['longitude_deg']
        elif planet_name == "Candra":
            moon_data = self.astro.calculate_moon_position_ultra(jd_tt)
            ra = moon_data['ra']
            dec = moon_data['dec']
            long = moon_data['longitude']
        elif planet_name in ["Rahu", "Ketu"]:
            # Gunakan metode baru dari AstronomicalEngine
            long = self.astro.calculate_lunar_nodes_precise(jd_tt, planet_name)
            # Dapatkan true obliquity untuk konversi ke ekuatorial
            eps = self.astro.calculate_true_obliquity(jd_tt)
            ra, dec = self.transformer.ecliptic_to_equatorial(long, 0, eps)
        else:
            planet_data = self.astro.calculate_planet_position_enhanced(planet_name, jd_tt)
            long = planet_data['longitude']
            eps = self.astro.calculate_true_obliquity(jd_tt)  # Gunakan true obliquity
            ra, dec = self.transformer.ecliptic_to_equatorial(long, 0, eps)

        lha = self.calculate_lha(ra, jd_utc, self.lon)
        altaz = self.transformer.equatorial_to_altaz(
            ra, dec, jd_utc, self.lat, self.lon,
            self.astro.pressure, self.astro.temperature+273.15, 0.5
        )
        altitude = altaz['altitude_apparent']
        azimuth = altaz['azimuth']
        astha_zone = self.get_astha_zone_from_lha(lha)
        hours_from_transit = lha / 15.0
        is_above_horizon = altitude >= 0

        ayanamsa = self.astro.calculate_ayanamsa_precise(jd_tt)
        planet_nirayana = (long - ayanamsa) % 360
        rasi_idx = int(planet_nirayana // 30)
        rasi_name = self.const.ZODIAC[rasi_idx]

        return {
            "planet": planet_name,
            "lha": lha,
            "lha_hours": hours_from_transit,
            "diagram_angle": astha_zone["diagram_angle"],
            "zona_astha": astha_zone["zone"],
            "astha_description": astha_zone["description"],
            "astha_status": astha_zone["status"],
            "astronomical_data": {
                "right_ascension": ra,
                "declination": dec,
                "altitude": altitude,
                "azimuth": azimuth,
                "is_above_horizon": is_above_horizon,
                "hour_angle": lha,
                "longitude_tropical": long,
                "longitude_nirayana": planet_nirayana,
                "rasi_nirayana": rasi_name,
                "rasi_degrees": planet_nirayana % 30,
                "ayanamsa": ayanamsa
            },
            "time_data": {
                "jd_tt": jd_tt,
                "jd_utc": jd_utc,
                "current_hour": current_hour,
                "hours_from_transit": abs(hours_from_transit),
                "direction_from_transit": "Barat" if lha > 0 else "Timur"
            }
        }

    def analyze_all_planets_by_date(self, year: int, month: int, day: int,
                                   current_hour: float = 10.5) -> Dict:
        hour_int = int(current_hour)
        minute_int = int((current_hour - hour_int) * 60)
        second_int = int(((current_hour - hour_int) * 60 - minute_int) * 60)
        jd_tt = self.time_system.wib_to_jd_tt_extended(year, month, day, hour_int, minute_int, second_int)

        planets = ["Surya", "Candra", "Mangala", "Budha", "Brihaspati",
                  "Sukra", "Sani", "Rahu", "Ketu"]

        results = {}
        for planet in planets:
            try:
                results[planet] = self.analyze_planet_position(planet, jd_tt, current_hour)
            except Exception as e:
                results[planet] = {
                    "planet": planet,
                    "error": str(e),
                    "lha": 0,
                    "zona_astha": "Unknown"
                }
        return results

    def calculate_planet_transit_time(self, planet_name: str, jd_tt_noon: float) -> Dict:
        # Dapatkan RA pada noon
        if planet_name == "Surya":
            sun = self.astro.calculate_sun_position_ultra(jd_tt_noon)
            ra_noon = sun['ra_deg']
        elif planet_name == "Candra":
            moon = self.astro.calculate_moon_position_ultra(jd_tt_noon)
            ra_noon = moon['ra']
        else:
            planet = self.astro.calculate_planet_position_enhanced(planet_name, jd_tt_noon)
            eps = 23.44
            ra_noon, _ = self.transformer.ecliptic_to_equatorial(planet['longitude'], 0, eps)

        date_info = self.time_system.jd_to_gregorian(jd_tt_noon)
        year_astro = date_info['year_astronomical']
        delta_t_seconds = self.time_system.delta_t_hybrid(year_astro)
        jd_utc_noon = jd_tt_noon - (delta_t_seconds + 32.184) / 86400.0

        T = (jd_utc_noon - 2451545.0) / 36525.0
        GMST_noon = 280.46061837 + 360.98564736629 * (jd_utc_noon - 2451545.0) + \
                   0.000387933 * T**2 - T**3/38710000.0
        GMST_noon = GMST_noon % 360

        target_GMST = ra_noon - self.lon
        target_GMST = target_GMST % 360

        delta_GMST = target_GMST - GMST_noon
        if delta_GMST > 180:
            delta_GMST -= 360
        elif delta_GMST < -180:
            delta_GMST += 360

        delta_days = delta_GMST / 360.98564736629
        transit_jd_utc = jd_utc_noon + delta_days

        for i in range(3):
            transit_jd_tt = transit_jd_utc + (delta_t_seconds + 32.184) / 86400.0
            if planet_name == "Surya":
                sun = self.astro.calculate_sun_position_ultra(transit_jd_tt)
                ra_transit = sun['ra_deg']
            elif planet_name == "Candra":
                moon = self.astro.calculate_moon_position_ultra(transit_jd_tt)
                ra_transit = moon['ra']
            else:
                planet = self.astro.calculate_planet_position_enhanced(planet_name, transit_jd_tt)
                ra_transit, _ = self.transformer.ecliptic_to_equatorial(planet['longitude'], 0, 23.44)

            T = (transit_jd_utc - 2451545.0) / 36525.0
            GMST_transit = 280.46061837 + 360.98564736629 * (transit_jd_utc - 2451545.0) + \
                           0.000387933 * T**2 - T**3/38710000.0
            GMST_transit = GMST_transit % 360
            LST_transit = (GMST_transit + self.lon) % 360
            error = ra_transit - LST_transit
            if error > 180:
                error -= 360
            elif error < -180:
                error += 360
            delta_days_correction = error / 360.98564736629
            transit_jd_utc += delta_days_correction

        transit_wib = ((transit_jd_utc + 0.5) % 1) * 24 + 7
        if transit_wib >= 24:
            transit_wib -= 24
        elif transit_wib < 0:
            transit_wib += 24

        transit_jd_tt = transit_jd_utc + (delta_t_seconds + 32.184) / 86400.0
        if planet_name == "Surya":
            sun = self.astro.calculate_sun_position_ultra(transit_jd_tt)
            ra_final = sun['ra_deg']
            dec_final = sun['dec_deg']
        elif planet_name == "Candra":
            moon = self.astro.calculate_moon_position_ultra(transit_jd_tt)
            ra_final = moon['ra']
            dec_final = moon['dec']
        else:
            planet = self.astro.calculate_planet_position_enhanced(planet_name, transit_jd_tt)
            ra_final, dec_final = self.transformer.ecliptic_to_equatorial(planet['longitude'], 0, 23.44)

        altaz = self.transformer.equatorial_to_altaz(
            ra_final, dec_final, transit_jd_utc, self.lat, self.lon,
            self.astro.pressure, self.astro.temperature+273.15, 0.5
        )
        transit_altitude = altaz['altitude_apparent']

        def hour_to_hhmm(h):
            hh = int(h)
            mm = int((h - hh) * 60)
            ss = int(((h - hh) * 60 - mm) * 60)
            return f"{hh:02d}:{mm:02d}:{ss:02d}"

        return {
            "planet": planet_name,
            "transit_ra": ra_final,
            "transit_dec": dec_final,
            "transit_time_wib": transit_wib,
            "transit_time_formatted": hour_to_hhmm(transit_wib),
            "transit_altitude": transit_altitude,
            "transit_jd_utc": transit_jd_utc,
            "note": "Perhitungan transit dengan koreksi JD (+0.5) untuk konversi waktu sipil"
        }

    def get_astha_summary(self, results: Dict) -> str:
        summary = []
        for planet, data in results.items():
            if "error" not in data:
                summary.append(
                    f"{planet:10}: {data['zona_astha']:20} "
                    f"(LHA: {data['lha']:6.1f}°, Alt: {data['astronomical_data']['altitude']:5.1f}°)"
                )
        return "\n".join(summary)

    def _hour_to_hhmm(self, hour_float: float) -> str:
        hours = int(hour_float)
        minutes = int((hour_float - hours) * 60)
        seconds = int(((hour_float - hours) * 60 - minutes) * 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# ============================================================================
# DEWATA & MAṆḌALA ENGINE (sama seperti sebelumnya)
# ============================================================================
class DewataMandalaEngine:
    """Engine untuk menghitung Dewata dan Maṇḍala berdasarkan Nakṣatra"""

    def __init__(self):
        self.const = ΩConstants
        self.math = MathCore()
        self.norm = NormalizationEngine()

        self.DEWATA_MAPPING = {
            "Aswini": {"dewata": "Aświ", "varian": ["Aświno", "Aświṇi", "Aśvī", "Aśviṇī", "Ashwini"]},
            "Bharani": {"dewata": "Yama", "varian": ["Yamarāja", "Yama"]},
            "Krittika": {"dewata": "Agni", "varian": ["Dahana", "Anala", "Agni"]},
            "Rohini": {"dewata": "Prajāpati", "varian": ["Karṣalaśa", "Kamalaja", "Prajāpati", "Prajapati"]},
            "Mrigasira": {"dewata": "Śaśi", "varian": ["Śaśin", "Soma", "Chandra", "Candra"]},
            "Ardra": {"dewata": "Rudra", "varian": ["Śulabhṛt", "Śulabhṛd", "Rudra", "Śiva"]},
            "Punarvasu": {"dewata": "Aditi", "varian": ["Ariditī", "Aditi", "Mātā"]},
            "Pushya": {"dewata": "Brhaspati", "varian": ["Gurudewa", "Jīva", "Bṛhaspati", "Guru"]},
            "Aslesha": {"dewata": "Sarpāḥ", "varian": ["Phaṇi", "Ahideva", "Sārpa", "Sarpāḥ", "Nāga"]},
            "Magha": {"dewata": "Pitaraḥ", "varian": ["Pitṛ", "Pitara", "Pitṛdeva", "Pitarah"]},
            "Purva Phalguni": {"dewata": "Yoṇi", "varian": ["Yoṇi", "Bhaga"]},
            "Uttara Phalguni": {"dewata": "Aryama", "varian": ["Aryaman", "Aryama"]},
            "Hasta": {"dewata": "Sāvitra", "varian": ["Dinakṛt", "Āyusmān", "Sāvitra", "Savitar"]},
            "Chitra": {"dewata": "Twaṣṭā", "varian": ["Twaṣṭa", "Tvaṣṭṛ", "Tvashtri", "Vishvakarma"]},
            "Swati": {"dewata": "Pawana", "varian": ["Pavana", "Anila", "Vāyu", "Bayu"]},
            "Visakha": {"dewata": "Śakragni", "varian": ["Śakra", "Śakrāgni", "Indrāgni", "Indra"]},
            "Anuradha": {"dewata": "Mitra", "varian": ["Mitrā", "Mitra", "Maitra"]},
            "Jyestha": {"dewata": "Śakraindra", "varian": ["Indra", "Śakra", "Devendra"]},
            "Mula": {"dewata": "Nairiti", "varian": ["Nirṛti", "Nairiti", "Alakshmi"]},
            "Purva Ashadha": {"dewata": "Apah", "varian": ["Toya", "Apya", "Āpye", "Varuna", "Apas"]},
            "Uttara Ashadha": {"dewata": "Wiśwa", "varian": ["Viśve", "Viśvedevā", "Vishvadeva", "Sarvadeva"]},
            "Sravana": {"dewata": "Hari", "varian": ["Wiṣṇu", "Vishnu", "Hari", "Narayana"]},
            "Dhanistha": {"dewata": "Piwāśya", "varian": ["Hariḥ", "Wiṣṇu", "Vasu", "Ashwini Kumar"]},
            "Satabhisha": {"dewata": "Baruṇa", "varian": ["Bāruṇa", "Varuṇa", "Waruna", "Jalapati"]},
            "Purva Bhadrapada": {"dewata": "Ajapāda", "varian": ["Ekapāda", "Ajaikapad", "Aja Ekapada"]},
            "Uttara Bhadrapada": {"dewata": "Ahibuddhā", "varian": ["Ahirbudhnya", "Ananta", "Shesha"]},
            "Revati": {"dewata": "Pūṣan", "varian": ["Pūṣa", "Pushan", "Bṛhaspati"]}
        }

        self.MANDALA_MAPPING = {
            "Māhendra": {
                "nakṣatra_indices": [3, 16, 17, 20, 21, 22],
                "nakṣatra_names": ["Rohini", "Anuradha", "Jyestha", "Uttara Ashadha", "Sravana", "Dhanistha"],
                "varian": ["Mahendra", "Indra", "Śakra"]
            },
            "Agneya": {
                "nakṣatra_indices": [1, 2, 7, 9, 10, 15, 24],
                "nakṣatra_names": ["Bharani", "Krittika", "Pushya", "Magha", "Purva Phalguni", "Visakha", "Purva Bhadrapada"],
                "varian": ["Āgneya", "Agni", "Anala"]
            },
            "Baruṇa": {
                "nakṣatra_indices": [5, 8, 18, 19, 23, 25, 26],
                "nakṣatra_names": ["Ardra", "Aslesha", "Mula", "Purva Ashadha", "Satabhisha", "Uttara Bhadrapada", "Revati"],
                "varian": ["Varuṇa", "Waruna", "Jalendra", "Baruṇya"]
            },
            "Bāyabya": {
                "nakṣatra_indices": [0, 4, 6, 11, 12, 13, 14],
                "nakṣatra_names": ["Aswini", "Mrigasira", "Punarvasu", "Uttara Phalguni", "Hasta", "Chitra", "Swati"],
                "varian": ["Wāyawya", "Vāyavya", "Maruta", "Pawana"]
            }
        }

        self._build_nakshatra_to_mandala()

    def _build_nakshatra_to_mandala(self):
        self.nakshatra_to_mandala = {}
        for mandala_name, mandala_info in self.MANDALA_MAPPING.items():
            for nakshatra_name in mandala_info["nakṣatra_names"]:
                std_nakshatra = self.norm.normalize(nakshatra_name)
                self.nakshatra_to_mandala[std_nakshatra] = mandala_name

    def get_dewata_from_nakshatra(self, nakshatra_name: str) -> Dict:
        std_nakshatra = self.norm.normalize(nakshatra_name)
        if std_nakshatra in self.DEWATA_MAPPING:
            dewata_info = self.DEWATA_MAPPING[std_nakshatra]
            return {
                "nakṣatra": std_nakshatra,
                "dewata": dewata_info["dewata"],
                "varian_dewata": dewata_info.get("varian", []),
                "description": f"{dewata_info['dewata']} adalah dewata penguasa nakṣatra {std_nakshatra}",
                "status": "Ditemukan"
            }
        for nak_key, dewata_info in self.DEWATA_MAPPING.items():
            if std_nakshatra == nak_key or std_nakshatra in self.norm.normalize(nak_key):
                return {
                    "nakṣatra": nak_key,
                    "dewata": dewata_info["dewata"],
                    "varian_dewata": dewata_info.get("varian", []),
                    "description": f"{dewata_info['dewata']} adalah dewata penguasa nakṣatra {nak_key}",
                    "status": "Ditemukan"
                }
        return {
            "nakṣatra": std_nakshatra,
            "dewata": "Unknown",
            "description": f"Dewata untuk nakṣatra {std_nakshatra} tidak ditemukan",
            "status": "Tidak ditemukan"
        }

    def get_mandala_from_nakshatra(self, nakshatra_name: str) -> Dict:
        std_nakshatra = self.norm.normalize(nakshatra_name)
        if std_nakshatra in self.nakshatra_to_mandala:
            mandala_name = self.nakshatra_to_mandala[std_nakshatra]
            mandala_info = self.MANDALA_MAPPING[mandala_name]
            return {
                "nakṣatra": std_nakshatra,
                "mandala": mandala_name,
                "varian_mandala": mandala_info.get("varian", []),
                "nakṣatra_dalam_mandala": mandala_info["nakṣatra_names"],
                "indices_nakṣatra": mandala_info["nakṣatra_indices"],
                "description": f"Maṇḍala {mandala_name} menguasai nakṣatra {std_nakshatra}",
                "status": "Ditemukan"
            }
        for mandala_name, mandala_info in self.MANDALA_MAPPING.items():
            nakṣatra_list_lower = [n.lower() for n in mandala_info["nakṣatra_names"]]
            if std_nakshatra.lower() in nakṣatra_list_lower:
                return {
                    "nakṣatra": std_nakshatra,
                    "mandala": mandala_name,
                    "varian_mandala": mandala_info.get("varian", []),
                    "nakṣatra_dalam_mandala": mandala_info["nakṣatra_names"],
                    "indices_nakṣatra": mandala_info["nakṣatra_indices"],
                    "description": f"Maṇḍala {mandala_name} menguasai nakṣatra {std_nakshatra}",
                    "status": "Ditemukan"
                }
        return {
            "nakṣatra": std_nakshatra,
            "mandala": "Unknown",
            "description": f"Maṇḍala untuk nakṣatra {std_nakshatra} tidak ditemukan",
            "status": "Tidak ditemukan"
        }

    def get_dewata_mandala_from_nakshatra(self, nakshatra_name: str) -> Dict:
        dewata_info = self.get_dewata_from_nakshatra(nakshatra_name)
        mandala_info = self.get_mandala_from_nakshatra(nakshatra_name)
        return {
            "nakṣatra": dewata_info["nakṣatra"],
            "dewata": dewata_info["dewata"],
            "mandala": mandala_info["mandala"],
            "dewata_info": dewata_info,
            "mandala_info": mandala_info,
            "combined_description": f"Nakṣatra {dewata_info['nakṣatra']} Dewata {dewata_info['dewata']} dan Maṇḍala {mandala_info['mandala']}"
        }

    def get_all_dewata(self) -> List[Dict]:
        all_dewata = []
        for nakshatra_name in self.const.NAKSHATRAS_STANDARD:
            dewata_info = self.get_dewata_from_nakshatra(nakshatra_name)
            mandala_info = self.get_mandala_from_nakshatra(nakshatra_name)
            all_dewata.append({
                "index": self.const.NAKSHATRAS_STANDARD.index(nakshatra_name) + 1,
                "nakṣatra": nakshatra_name,
                "dewata": dewata_info["dewata"],
                "mandala": mandala_info["mandala"],
                "varian_dewata": dewata_info.get("varian_dewata", []),
                "varian_mandala": mandala_info.get("varian_mandala", [])
            })
        return all_dewata


# ============================================================================
# FUNGSI INFORMASI LENGKAP & REALTIME
# ============================================================================

def parse_time_input(time_str):
    """
    Parse input waktu yang bisa berupa:
    - format HH:MM:SS (contoh: 14:30:15)
    - format HH:MM (contoh: 14:30)
    - format desimal (contoh: 14.5)
    - kosong -> return 12.0 (default)
    """
    if not time_str or time_str.strip() == "":
        return 12.0
    time_str = time_str.strip()
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = map(float, parts)
        elif len(parts) == 2:
            h, m = map(float, parts)
            s = 0
        else:
            raise ValueError("Format waktu tidak dikenal. Gunakan HH:MM:SS atau angka desimal.")
        return h + m/60.0 + s/3600.0
    else:
        return float(time_str)

def display_comprehensive_info(year: int, month: int, day: int, hour: float = None):
    """Tampilkan informasi lengkap astronomi dan astrologi Veda dengan format profesional.
       Menggunakan JRC Ephemeris untuk koordinat horizontal toposentrik Matahari & Bulan.
    """
    # Header utama
    print("\n" + "=" * 72)
    print(f"{BOLD}{'VSOP87D/ELP82B & VEDIC TIME (JRC_Epm)':^72}{RESET}")
    print("=" * 72)

    if hour is None:
        import datetime
        now = datetime.datetime.now()
        hour = now.hour + now.minute/60.0 + now.second/3600.0
        print(f"{BOLD}Tanggal:{RESET} {day:02d}/{month:02d}/{year}")
        print(f"{BOLD}Waktu:{RESET} {hour:.2f} WIB ({int(hour):02d}:{int((hour-int(hour))*60):02d})")
    else:
        print(f"{BOLD}Tanggal:{RESET} {day:02d}/{month:02d}/{year}")
        print(f"{BOLD}Waktu:{RESET} {hour:.2f} WIB ({int(hour):02d}:{int((hour-int(hour))*60):02d})")

    # Lokasi dalam satu baris
    print(f"{BOLD}Lokasi:{RESET} {ΩConstants.LOC_NAME} | {ΩConstants.LOC_LAT:.6f}°, {ΩConstants.LOC_LON:.6f}°, {ΩConstants.LOC_ELEV:.1f} m")
    print("-" * 72)

    # Inisialisasi engine
    math_core = MathCore()
    astro = AstronomicalEngine()
    vedic = VedicTimeEngine()
    graha = GrahacaraAsthaEngine()
    dewata = DewataMandalaEngine()
    time_sys = TimeSystem()

    # ================================================================
    # 1. AMBIL DATA TOPOSENTRIK DARI JRC EPHEMERIS (Matahari & Bulan)
    # ================================================================
    from JRC_Ephemeris import JolotundoArchaeoastronomySystem
    jrc_system = JolotundoArchaeoastronomySystem()
    
    # Konversi jam ke integer
    hour_int = int(hour)
    minute_int = int((hour - hour_int) * 60)
    second_int = int(((hour - hour_int) * 60 - minute_int) * 60)

    jrc_ephem = jrc_system.get_complete_ephemeris(
        year, month, day, hour_int, minute_int, second_int,
        use_current_time=False
    )

    # Ekstrak koordinat horizontal (sudah toposentrik + refraksi)
    sun_az_jrc   = jrc_ephem['sun']['horizontal_apparent']['azimuth_deg']
    sun_alt_jrc  = jrc_ephem['sun']['horizontal_apparent']['altitude_deg']
    moon_az_jrc  = jrc_ephem['moon']['horizontal_apparent']['azimuth_deg']
    moon_alt_jrc = jrc_ephem['moon']['horizontal_apparent']['altitude_deg']

    # ================================================================
    # 2. PERHITUNGAN WAKTU & POSISI (ASTRO ENGINE)
    # ================================================================
    # Konversi waktu
    jd_utc = time_sys.wib_to_jd_utc(year, month, day, hour_int, minute_int, second_int)
    jd_tt = time_sys.wib_to_jd_tt_extended(year, month, day, hour_int, minute_int, second_int)

    # Ayanamsa
    ayanamsa = astro.calculate_ayanamsa_precise(jd_tt)

    # ΔT dan metode
    mjd = jd_utc - 2400000.5
    delta_t_seconds = time_sys.delta_t_hybrid(year, mjd)
    if 702 <= year <= 1299:
        delta_t_method = "Jolotundo eclipse‑anchored"
    elif _DELTA_T_TABLE and _DELTA_T_TABLE[0][0] <= mjd <= _DELTA_T_TABLE[-1][0]:
        delta_t_method = "IERS/HMNAO"
    else:
        delta_t_method = "Espenak & Meeus (NASA)"

    # Kali Ahargana
    ka = math_core.julian_date_to_ka(year, month, day)

    # Yuga info
    yuga_info = time_sys.astronomical_year_to_yuga_info(year)

    # Fungsi pembantu format angka ribuan
    def ribuan(x, desimal=0):
        if desimal == 0:
            return f"{x:,.0f}".replace(',', '.')
        else:
            return f"{x:,.{desimal}f}".replace(',', '.')

    # --- Hitung posisi benda langit (geosentrik) untuk pancanga ---
    sun_data = astro.calculate_sun_position_ultra(jd_tt)
    sun_nirayana = (sun_data['longitude_deg'] - ayanamsa) % 360
    sun_rasi = astro.calculate_solar_ingress(sun_nirayana, "nirayana")

    moon_data = astro.calculate_moon_position_ultra(jd_tt, sun_data['longitude_deg'])
    moon_nirayana = (moon_data['longitude'] - ayanamsa) % 360
    moon_nakshatra = astro.calculate_nakshatra(moon_nirayana, "nirayana")
    moon_nakshatra_sayana = astro.calculate_nakshatra(moon_data['longitude'], "tropical")

    # --- Grahacara Astha (untuk zona LHA dan tabel planet) ---
    graha_info = graha.analyze_all_planets_by_date(year, month, day, hour)
    # Timpa azimuth dan altitude Matahari & Bulan dengan nilai JRC (toposentrik)
    if 'Surya' in graha_info and 'error' not in graha_info['Surya']:
        graha_info['Surya']['astronomical_data']['azimuth'] = sun_az_jrc
        graha_info['Surya']['astronomical_data']['altitude'] = sun_alt_jrc
    if 'Candra' in graha_info and 'error' not in graha_info['Candra']:
        graha_info['Candra']['astronomical_data']['azimuth'] = moon_az_jrc
        graha_info['Candra']['astronomical_data']['altitude'] = moon_alt_jrc

    # --- INFORMASI DASAR WAKTU ---
    print_section_header("INFORMASI DASAR WAKTU")
    print_labeled("Kali Ahargana (KA)", f"{ribuan(ka)}")
    print_labeled("Julian Day (UTC)", f"{jd_utc:.6f}")
    print_labeled("Julian Day (TT)", f"{jd_tt:.6f}")
    print_labeled("ΔT (TT – UT)", f"{delta_t_seconds:.2f} detik ({delta_t_method})")
    print_labeled("Ayanamsa (Lahiri)", f"{ayanamsa:.6f}° (Sayana → Nirayana)")
    print_labeled("Periode Yuga", yuga_info['current_yuga'])
    print_labeled("Tahun dalam Yuga", ribuan(yuga_info['years_in_current_yuga']))
    print_labeled("Epoch Kali Yuga", f"{ΩConstants.KALI_EPOCH_DATE} (JD {ΩConstants.KALI_EPOCH_JD:.1f})")

    # --- POSISI MATAHARI & BULAN (menggunakan azimuth/altitude dari JRC) ---
    print_section_header("MATAHARI & BULAN")
    print(f"{BOLD}   MATAHARI (Surya):{RESET}")
    print_labeled("  - Bujur Tropical", f"{sun_data['longitude_deg']:.6f}°")
    print_labeled("  - Bujur Nirayana", f"{sun_nirayana:.6f}°")
    print_labeled("  - Rasi", f"{sun_rasi['rasi']} ({sun_rasi['degrees_in_rasi']:.2f}°)")
    print_labeled("  - RA", f"{sun_data['ra_hms']}, Dec: {sun_data['dec_dms']}")
    print_labeled("  - Azimuth", f"{sun_az_jrc:.2f}°")
    print_labeled("  - Altitude", f"{sun_alt_jrc:.1f}°")

    print(f"\n{BOLD}   BULAN (Candra):{RESET}")
    print_labeled("  - Bujur Tropical", f"{moon_data['longitude']:.6f}°")
    print_labeled("  - Bujur Nirayana", f"{moon_nirayana:.6f}°")
    print_labeled("  - RA", f"{moon_data['ra_hms']}, Dec: {moon_data['dec_dms']}")
    print_labeled("  - Azimuth", f"{moon_az_jrc:.2f}°")
    print_labeled("  - Altitude", f"{moon_alt_jrc:.1f}°")

    if moon_data.get('elongation') is not None:
        elong = moon_data['elongation']
        phase_name = _phase_name_helper(elong)
        print_labeled("  - Elongasi", f"{elong:.2f}° ({phase_name})")
        print_labeled("  - Iluminasi", f"{moon_data['illumination']:.1f}%")
        print_labeled("  - Usia (umur) Bulan", f"{moon_data['age_days']:.2f} hari")

    # --- PANCAṄGA ---
    print_section_header("PANCAṄGA")
    tithi = astro.calculate_tithi(sun_nirayana, moon_nirayana, "nirayana")
    yoga = vedic.calculate_yoga(sun_nirayana, moon_nirayana)
    karana = vedic.calculate_karana(sun_nirayana, moon_nirayana)
    parwesa = vedic.calculate_parwesa_gompers(ka)

    print_labeled("Tithi", f"{tithi['tithi']} {tithi['paksa']} ({tithi['percent']:.1f}%)")
    print_labeled("Nakṣatra (Nirayana)", f"{moon_nakshatra['nakshatra']} (pada {moon_nakshatra['pada']})")
    print_labeled("Nakṣatra (Sayana)", f"{moon_nakshatra_sayana['nakshatra']} (pada {moon_nakshatra_sayana['pada']})")
    print_labeled("Yoga", f"{yoga['name']} ({yoga['percent']:.1f}%)")
    print_labeled("Karana", karana['name'])
    print_labeled("Parwesa", parwesa['name'])

    # --- LAGNA ---
    print_section_header("LAGNA (ASCENDANT)")
    sunrise_info = astro.calculate_sunrise_sunset_precise(
        time_sys.wib_to_jd_utc(year, month, day, hour_int, minute_int, second_int)
    )
    if sunrise_info and 'sunrise' in sunrise_info:
        sunrise_str = sunrise_info['sunrise']['wib']
        def parse_time(time_str):
            parts = time_str.split(':')
            return float(parts[0]) + float(parts[1])/60.0 + float(parts[2])/3600.0
        sunrise_hour = parse_time(sunrise_str)
        if hour < sunrise_hour:
            ishta_kala = ((hour + 24) - sunrise_hour) * 60
        else:
            ishta_kala = (hour - sunrise_hour) * 60
        lagna_info = vedic.calculate_lagna_precise(sun_nirayana, ishta_kala, jd_tt)
        print_labeled("Rasi Lagna", lagna_info['lagna_rasi_name'])
        print_labeled("Derajat dalam Rasi", f"{lagna_info['deg_in_rasi']:.2f}°")
        print_labeled("Bujur Ekliptik", f"{lagna_info['absolute_ecliptic_deg']:.2f}°")
        print_labeled("Ishta Kala", f"{ishta_kala:.1f} menit")
        print_labeled("Metode", lagna_info['calculation_method'])
    else:
        print("   Tidak dapat menghitung Lagna (data sunrise tidak tersedia)")

    # Helper konversi waktu
    def str_time_to_float(tstr):
        h, m, s = map(int, tstr.split(':'))
        return h + m/60.0 + s/3600.0

    def float_to_hhmmss(f):
        f_mod = f % 24.0
        h = int(f_mod)
        remainder = (f_mod - h) * 60
        m = int(remainder)
        s = int((remainder - m) * 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    # --- MUHURTA & TABEH ---
    print_section_header("MUHURTA & TABEH")
    muhurta_info = vedic.calculate_muhurta_jawa_kuno(ka, hour)
    tabeh_info = vedic.calculate_tabeh_precise(ka, hour)

    if muhurta_info and 'error' not in muhurta_info:
        period_start_str = muhurta_info.get('period_start')
        period_end_str   = muhurta_info.get('period_end')
        muhurta_length   = muhurta_info.get('muhurta_length')
        muhurta_index    = muhurta_info.get('index')
        if period_start_str and muhurta_length is not None and muhurta_index is not None:
            start_period = str_time_to_float(period_start_str)
            start_muhurta = start_period + muhurta_index * muhurta_length
            end_muhurta   = start_muhurta + muhurta_length
            start_str = float_to_hhmmss(start_muhurta)
            end_str   = float_to_hhmmss(end_muhurta)
        else:
            start_str = end_str = "N/A"

        print(f"{BOLD}   Muhurta Jawa Kuno:{RESET}")
        print_labeled("  - Periode", muhurta_info['period'])
        print_labeled("  - Muhurta", f"{muhurta_info['name']} ({muhurta_info['index']+1}/{muhurta_info['total_muhurta']})")
        print_labeled("  - Waktu", f"{start_str} - {end_str}")
        print_labeled("  - Durasi", f"{muhurta_info['muhurta_length']:.2f} jam")
        print_labeled("  - Progress", f"{muhurta_info['progress']:.1f}%")

    if tabeh_info:
        print(f"\n{BOLD}   Tabeh:{RESET}")
        print_labeled("  - Periode", tabeh_info['period_type'])
        print_labeled("  - Tabeh", f"{tabeh_info['tabeh_name']} ({tabeh_info['tabeh_index']}/8)")
        print_labeled("  - Waktu", f"{tabeh_info['start_time']} - {tabeh_info['end_time']}")
        print_labeled("  - Durasi", f"{tabeh_info['duration_hours']:.2f} jam")

    # --- DEWATA & MAṆḌALA ---
    print_section_header("DEWATA & MAṆḌALA")
    dewata_info = dewata.get_dewata_mandala_from_nakshatra(moon_nakshatra['nakshatra'])
    print_labeled("Nakṣatra Bulan", moon_nakshatra['nakshatra'])
    print_labeled("Dewata Penguasa", dewata_info['dewata'])
    print_labeled("Maṇḍala", dewata_info['mandala'])

    # --- GRAHACARA ASTHA (tabel planet) ---
    print_section_header("GRAHACARA (POSISI PLANET)")
    print(f"   {'Planet':<10} {'Zona Astha':<20} {'LHA':>8} {'Altitude':>9} {'Rasi':<10}")
    print(f"   {'-'*9:<10} {'-'*19:<20} {'-'*8:>8} {'-'*9:>9} {'-'*9:<10}")
    for planet, data in graha_info.items():
        if "error" not in data:
            lha_str = f"{data['lha']:+.1f}°"
            alt_str = f"{data['astronomical_data']['altitude']:+.1f}°"
            rasi = data['astronomical_data']['rasi_nirayana']
            print(f"   {planet:<10} {data['zona_astha']:<20} {lha_str:>8} {alt_str:>9} {rasi:<10}")

    # --- SUNRISE & SUNSET ---
    print_section_header("SUNRISE & SUNSET")
    if sunrise_info:
        print_labeled("Matahari terbit", sunrise_info.get('sunrise', {}).get('wib', 'N/A'))
        print_labeled("Matahari terbenam", sunrise_info.get('sunset', {}).get('wib', 'N/A'))
        print_labeled("Transit (kulminasi)", sunrise_info.get('transit', {}).get('wib', 'N/A'))
        print_labeled("Panjang siang", f"{sunrise_info.get('day_length', 0):.2f} jam")
        print_labeled("Equation of Time", f"{sun_data.get('equation_of_time_minutes', 0):.1f} menit")

    # --- POSISI PLANET LAINNYA (menggunakan astro) ---
    print_section_header("POSISI PLANET LAINNYA")
    planets_to_show = ["Mangala", "Budha", "Sukra", "Brihaspati", "Sani", "Rahu", "Ketu"]
    print(f"   {'Planet':<10} {'Bujur Nirayana':>12} {'Rasi':<12} {'Status':<10}")
    print(f"   {'-'*9:<10} {'-'*12:>12} {'-'*11:<12} {'-'*9:<10}")
    for planet in planets_to_show:
        try:
            planet_data = astro.calculate_planet_position_enhanced(planet, jd_tt)
            if 'error' not in planet_data:
                long_nirayana = planet_data.get('longitude_nirayana', planet_data.get('longitude', 0))
                rasi_idx = int(long_nirayana // 30)
                rasi_name = ΩConstants.ZODIAC[rasi_idx]
                print(f"   {planet:<10} {long_nirayana:>11.2f}°   {rasi_name:<12} {'OK':<10}")
            else:
                print(f"   {planet:<10} {'N/A':>12}   {'N/A':<12} {'Error':<10}")
        except:
            print(f"   {planet:<10} {'N/A':>12}   {'N/A':<12} {'Error':<10}")

    print("\n" + "=" * 72)
    print(f"{BOLD}{'INFORMASI SELESAI':^72}{RESET}")
    print("=" * 72 + "\n")

    # Kembalikan dictionary untuk kompatibilitas
    return {
        'sun': sun_data,
        'moon': moon_data,
        'tithi': tithi,
        'nakshatra': moon_nakshatra,
        'nakshatra_sayana': moon_nakshatra_sayana,
        'yoga': yoga,
        'karana': karana,
        'parwesa': parwesa,
        'lagna': lagna_info if 'lagna_info' in locals() else None,
        'muhurta': muhurta_info,
        'tabeh': tabeh_info,
        'dewata': dewata_info,
        'graha': graha_info,
        'sunrise': sunrise_info,
        'ayanamsa': ayanamsa,
        # tambahkan data JRC jika diperlukan
        'jrc_ephemeris': jrc_ephem
    }

# Helper untuk nama fase Bulan (bisa diletakkan di luar fungsi)
def _phase_name_helper(elongation_deg):
    a = elongation_deg % 360.0
    if a < 22.5 or a >= 337.5:
        return "New Moon"
    elif 22.5 <= a < 67.5:
        return "Waxing Crescent"
    elif 67.5 <= a < 112.5:
        return "First Quarter"
    elif 112.5 <= a < 165.0:
        return "Waxing Gibbous"
    elif 165.0 <= a < 195.0:
        return "Full Moon"
    elif 195.0 <= a < 247.5:
        return "Waning Gibbous"
    elif 247.5 <= a < 292.5:
        return "Last Quarter"
    else:
        return "Waning Crescent"


def main():
    """Menu utama yang disederhanakan: Realtime atau Tanggal Tertentu"""
    print("\n" + "="*80)
    print("  OLD JAVA ASTRONOMY - JRC ENHANCED EDITION")
    print("  Informasi Lengkap: Matahari, Bulan, Planet, Pancanga, Lagna, Muhurta, Tabeh, Dewata, Grahacara Astha")
    print("="*80)

    while True:
        print("\n" + "="*50)
        print("MENU UTAMA")
        print("="*50)
        print("1. Informasi Realtime (waktu sekarang)")
        print("2. Informasi untuk Tanggal Tertentu")
        print("0. Keluar")
        print("-"*50)

        pilihan = input("Pilih menu (0-2): ").strip()

        if pilihan == "0":
            print("\nTerima kasih telah menggunakan Old Java Astronomy JRC Enhanced!")
            break

        elif pilihan == "1":
            # Realtime
            import datetime
            now = datetime.datetime.now()
            tahun = now.year
            bulan = now.month
            tanggal = now.day
            jam = now.hour + now.minute/60.0 + now.second/3600.0
            print(f"\nMengambil data untuk waktu sekarang: {tanggal:02d}/{bulan:02d}/{tahun} {int(jam):02d}:{now.minute:02d}:{now.second:02d} WIB")
            display_comprehensive_info(tahun, bulan, tanggal, jam)

        elif pilihan == "2":
            # Tanggal tertentu
            try:
                tahun_input = input("Tahun (misal: 2024 atau -3101 untuk SM): ").strip()
                if not tahun_input:
                    print("Input tahun tidak boleh kosong.")
                    continue
                tahun = int(tahun_input)

                bulan = int(input("Bulan (1-12): "))
                tanggal = int(input("Tanggal: "))

                jam_input = input("Jam (format: HH:MM:SS atau desimal, kosong = 12:00): ").strip()
                jam = parse_time_input(jam_input)

                print(f"\nMenampilkan informasi untuk {tanggal:02d}/{bulan:02d}/{tahun} pukul {jam:.2f} WIB")
                display_comprehensive_info(tahun, bulan, tanggal, jam)

            except ValueError as e:
                print(f"❌ Input tidak valid: {e}. Silakan ulangi.")
            except Exception as e:
                print(f"❌ Terjadi kesalahan: {e}")

        else:
            print("Pilihan tidak valid. Silakan pilih 0, 1, atau 2.")

        input("\nTekan Enter untuk kembali ke menu utama...")


if __name__ == "__main__":
    main()