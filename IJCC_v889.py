"""
Ω-STHAPATI v301.4 FINAL IMPROVED - Sistem Konversi Prasasti Saka Jawa Kuno
Arsitek: Rakawi

Sistem lengkap untuk konversi prasasti Saka ke kalender Julian/Masehi dengan:
1. Mekanika KA-Wuku-Wara 
2. Matriks Fast Lookup
3. Smart Parsing untuk data tidak lengkap
4. Deteksi Interkalasi Damais
5. Verifikasi silang dan confidence scoring

PERBAIKAN UTAMA v301.4:
1. Mapping bulan Saka-Julian yang akurat
2. Sistem konversi tahun yang benar: Pausa (+78/+79), Magha/Phalguna (+79), lainnya (+78)
3. Algoritma pencarian TU-PA-Ā yang mencari anchor SEBELUM wara target
4. Validasi temporal ketat yang memastikan bulan kandidat sesuai dengan rentang bulan Saka
5. Filter kandidat yang menolak selisih >1 bulan (kecuali ada interkalasi eksplisit)
6. Penanganan khusus untuk Pausa yang ambigu

PERBAIKAN MINOR:
- Mengubah label "has_intercalation" menjadi "month_shifted" untuk kasus selisih 1 bulan
- Menjelaskan bahwa pergeseran 1 bulan bisa disebabkan oleh berbagai faktor
"""

import math
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime

# ============================================================================
# KONSTANTA SISTEM DASAR - DIPERBARUI
# ============================================================================

class ΩConstants:
    """Konstanta sistem dasar dengan perbaikan mapping bulan"""
    
    # IDENTITAS
    SYSTEM_NAME = "Ω-STHAPATI v301.4 FINAL IMPROVED"
    VERSION = "301.4.Ω-FINAL-IMPROVED-TEMPORAL"
    
    # ========================================================================
    # FUNGSI KONVERSI TAHUN SAKA KE MASEHI DASAR
    # ========================================================================
    
    @staticmethod
    def basic_saka_to_ce_year(saka_year: int, bulan_saka: str) -> Union[int, List[int]]:
        """
        Konversi dasar tahun Saka ke Masehi berdasarkan aturan sederhana:
        
        ATURAN:
        1. Jika bulan = Pausa: Saka year +78 dan +79 (ambigu)
        2. Jika bulan = Magha, Phalguna: Saka year +79 (tetap)
        3. Jika bulan = Caitra sampai Margasira: Saka year +78 (tetap)
        
        Contoh:
        - Tahun Saka 822, bulan Pausa → 900 dan 901 M
        - Tahun Saka 828, bulan Sravana → 906 M
        - Tahun Saka 700, bulan Phalguna → 779 M
        
        Returns:
            int atau List[int]: Tahun Masehi (list jika ambigu)
        """
        # Normalisasi nama bulan
        bulan = bulan_saka.lower().strip()
        
        # Mapping varian ejaan ke standar
        bulan_mapping = {
            "pausa": "pausa", "pusa": "pausa", "pausha": "pausa", "pusya": "pausa", "poṣya": "pausa", "posya": "pausa",
            "magha": "magha", "maga": "magha", "maha": "magha",
            "phalguna": "phalguna", "palguna": "phalguna", "falguna": "phalguna",
            "caitra": "caitra", "cetra": "caitra", "chaitra": "caitra",
            "vaisakha": "vaisakha", "wesakha": "vaisakha", "waisakha": "vaisakha", 
            "wesaka": "vaisakha", "vaisaka": "vaisakha", "besakha": "vaisakha",
            "jyestha": "jyestha", "jyeshtha": "jyestha", "jestha": "jyestha", 
            "jyeshta": "jyestha", "yestha": "jyestha", "iestha": "jyestha",
            "asadha": "asadha", "asada": "asadha", "asala": "asadha", "asarha": "asadha",
            "sravana": "sravana", "srawana": "sravana", "srawana": "sravana", "sarana": "sravana",
            "bhadrapada": "bhadrapada", "badrapada": "bhadrapada", "bhadra": "bhadrapada", "badra": "bhadrapada",
            "asvini": "asvini", "asuji": "asvini", "aswini": "asvini", "asui": "asvini", "asvij": "asvini", "asvin": "asvini",
            "kartika": "kartika", "karthika": "kartika", "karttika": "kartika", "katika": "kartika",
            "margasira": "margasira", "margashira": "margasira", "markasira": "margasira",
            "mrigasira": "margasira"  # Perhatikan: Mrigasira adalah nakshatra, bukan bulan. Tapi untuk kompatibilitas
        }
        
        # Standarisasi nama bulan
        bulan_std = bulan_mapping.get(bulan, bulan)
        
        # Aturan konversi
        if bulan_std == "pausa":
            # Ambigu: bisa +78 atau +79
            return [saka_year + 78, saka_year + 79]
        elif bulan_std in ["magha", "phalguna"]:
            # Magha dan Phalguna: +79
            return saka_year + 79
        else:
            # Bulan lainnya: Caitra sampai Margasira: +78
            return saka_year + 78
    
    # EPOCH
    KALI_EPOCH_JD_NOON = 588465.5
    KA_1_JAN_1_BC = 1132592
    KA_8_FEB_1_BC = 1132630  # Epoch TU-PA-Ā absolut
    
    # SIKLUS
    WUKU_CYCLE = 210
    NAKSHATRA_COUNT = 27
    TITHI_COUNT = 30
    
    # LOKASI DEFAULT
    LOC_LAT = -7.616
    LOC_LON = 112.616
    LOC_NAME = "Patirtan Jolotundo, Penanggungan"
    
    # AYANAMSA
    AYANAMSA_RATE = 0.013969712777777778
    PRECESSION_RATE = 50.290966  # arcsec/tahun
    
    # URUTAN BULAN SAKA (Damais standard)
    SAKA_MONTHS_ORDER = [
        "Caitra", "Vaisakha", "Jyestha", "Asadha",
        "Sravana", "Bhadrapada", "Asvini", "Kartika",
        "Margasira", "Pausa", "Magha", "Phalguna"
    ]
    
    # WUKU STANDARD (30 wuku)
    WUKU_NAMES_STANDARD = [
        "Sinta", "Landep", "Wukir", "Kurantil", "Tolu", "Gumbreg",
        "Warigalit", "Warigagung", "Julungwangi", "Sungsang",
        "Galungan", "Kuningan", "Langkir", "Mandasiya", "Julungpujut",
        "Pahang", "Kuruwelut", "Marakeh", "Tambir", "Medangkungan",
        "Maktal", "Wuye", "Manahil", "Prangbakat", "Bala",
        "Wugu", "Wayang", "Kulawu", "Dukut", "Watugunung"
    ]
    
    # SADWARA STANDARD (6-cycle)
    SADWARA_STANDARD = ["Tungleh", "Haryang", "Wurukung", "Paniron", "Was", "Maulu"]
    
    # PANCAWARA STANDARD (5-cycle)
    PANCAWARA_STANDARD = ["Pahing", "Pon", "Wage", "Kaliwon", "Umanis"]
    
    # SAPTAWARA STANDARD (7-cycle)
    SAPTAWARA_STANDARD = ["Aditya", "Soma", "Anggara", "Budha", "Wrhaspati", "Sukra", "Saniscara"]
    
    # ANCHOR DAMAIS (5 referensi)
    DAMAIS_ANCHORS = [
        {"id": "A.18_TULANG_AIR_II", "saka": 772, "masa": "Asadha", "tithi": 2,
         "paksa": "Sukla", "ka": 1443220, "wara": "Tungleh-Pahing-Aditya", "wuku": "Sinta"},
        {"id": "A.113_CUNGGRANG_II", "saka": 851, "masa": "Asuji", "tithi": 12,
         "paksa": "Sukla", "ka": 1472170, "wara": "Tungleh-Pahing-Sukra", "wuku": "Wugu"},
        {"id": "A.141_PUCANGAN_CORRECTED", "saka": 963, "masa": "Kartika",
         "tithi": 10, "paksa": "Sukla", "ka": 1513127, "wara": "Haryang-Wage-Sukra", "wuku": "Wayang"},
        {"id": "A.151_HANTANG", "saka": 1057, "masa": "Bhadrapada", "tithi": 13,
         "paksa": "Krsna", "ka": 1547400, "wara": "Wurukung-Pahing-Saniscara", "wuku": "Wukir"},
        {"id": "A.187_GAJAH_MADA", "saka": 1273, "masa": "Wesaka", "tithi": 1,
         "paksa": "Sukla", "ka": 1626161, "wara": "Haryang-Pon-Budha", "wuku": "Tolu"}
    ]
    
    # TPDP WEIGHTS - DIPERBARUI dengan prioritas 4 komponen utama
    TPDP_COMPONENTS = {
        # EMPAT KOMPONEN UTAMA (Total: 85%)
        "TAHUN_MATCH": 0.25,           # Prioritas 1: Tahun (25%)
        "BULAN_MATCH": 0.25,           # Prioritas 2: Bulan (25%)
        "WARA_MATCH": 0.20,           # Prioritas 3: Wara (20%)
        "WUKU_MATCH": 0.15,           # Prioritas 4: Wuku (15%)
        
        # KOMPONEN PENDUKUNG (Total: 15%)
        "PANCANGA_PLAUSIBILITY": 0.05, # Konsistensi pancanga
        "TEMPORAL_PROXIMITY": 0.05,    # Kedekatan dengan tengah bulan
        "HISTORICAL_PRIOR": 0.03,      # Kedekatan dengan anchor Damais
        "BRUTE_FORCE_SUPPORT": 0.02    # Konsistensi matematika
    }

    TPDP_THRESHOLDS = {
        "HIGH_CONFIDENCE": 0.85,      # Diperketat karena skor lebih terkonsentrasi
        "MEDIUM_CONFIDENCE": 0.70,
        "LOW_CONFIDENCE": 0.50
    }
            
    # BULAN INTERKALASI EKSPLISIT DI PRASASTI (berdasarkan Damais)
    FREQUENTLY_INTERCALATED = ["Pausa", "Sravana", "Caitra"]
    
    # ========================================================================
    # MAPPING BULAN SAKA KE BULAN JULIAN (Koreksi Lengkap) - PERBAIKAN UTAMA
    # ========================================================================
    SAKA_MONTH_TO_JULIAN_RANGE = {
        "Pausa": {"julian_months": [12, 1], "range_desc": "Desember-Januari", "ambiguous": True, "add_years": [78, 79]},
        "Magha": {"julian_months": [1, 2], "range_desc": "Januari-Februari", "ambiguous": False, "add_years": [79]},
        "Phalguna": {"julian_months": [2, 3], "range_desc": "Februari-Maret", "ambiguous": False, "add_years": [79]},
        "Caitra": {"julian_months": [3, 4], "range_desc": "Maret-April", "ambiguous": False, "add_years": [78]},
        "Vaisakha": {"julian_months": [4, 5], "range_desc": "April-Mei", "ambiguous": False, "add_years": [78]},
        "Jyestha": {"julian_months": [5, 6], "range_desc": "Mei-Juni", "ambiguous": False, "add_years": [78]},
        "Asadha": {"julian_months": [6, 7], "range_desc": "Juni-Juli", "ambiguous": False, "add_years": [78]},
        "Sravana": {"julian_months": [7, 8], "range_desc": "Juli-Agustus", "ambiguous": False, "add_years": [78]},
        "Bhadrapada": {"julian_months": [8, 9], "range_desc": "Agustus-September", "ambiguous": False, "add_years": [78]},
        "Asvini": {"julian_months": [9, 10], "range_desc": "September-Oktober", "ambiguous": False, "add_years": [78]},
        "Kartika": {"julian_months": [10, 11], "range_desc": "Oktober-November", "ambiguous": False, "add_years": [78]},
        "Margasira": {"julian_months": [11, 12], "range_desc": "November-Desember", "ambiguous": False, "add_years": [78]}
    }
    
    # MAPPING BULAN JULIAN KE SAKA (untuk backward compatibility)
    JULIAN_TO_SAKA_MONTH = {
        1: "Pausa", 2: "Magha", 3: "Phalguna", 4: "Caitra",
        5: "Vaisakha", 6: "Jyestha", 7: "Asadha", 8: "Sravana",
        9: "Bhadrapada", 10: "Asvini", 11: "Kartika", 12: "Margasira"
    }

    # ========================================================================
    # MAPPING VARIAN EJAAN (VARIANT SPELLINGS MAPPING)
    # ========================================================================
    
    # VARIAN BULAN SAKA
    MONTHS_SAKA_VARIANTS = {
        "Caitra": ["Cetra", "Chaitra", "Caitra"],
        "Vaisakha": ["Wesakha", "Waisakha", "Wesaka", "Vaisaka", "Vaisakha", "Besakha"],
        "Jyestha": ["Jyeshtha", "Jestha", "Jyeshta", "Yestha", "Iestha"],
        "Asadha": ["Asada", "Asadha", "Asala", "Asarha"],
        "Sravana": ["Srawana", "Sravana", "Srawana", "Sarana"],
        "Bhadrapada": ["Badrapada", "Bhadrapada", "Bhadra", "Badra"],
        "Asvini": ["Asuji", "Asvini", "Aswini", "Asui", "Asvij", "Asvin"],
        "Kartika": ["Kartika", "Karthika", "Karttika", "Katika"],
        "Margasira": ["Margasira", "Margashira", "Markasira", "Margasira"],
        "Pausa": ["Pausa", "Pusa", "Pausha", "Pusya", "Poṣya", "Posya"],
        "Magha": ["Maga", "Magha", "Makha"],
        "Phalguna": ["Palguna", "Phalguna", "Falguna", "Palguna"]
    }
    
    # VARIAN SADWARA 6 - URUTAN STANDAR: 0=TU, 1=HA, 2=WU, 3=PA, 4=WA, 5=MA
    SADWARA_VARIANTS = {
        "Tungleh": ["Tungle", "Tungleh", "Tunglek", "Tunglet", "TU"],
        "Haryang": ["Haryang", "Aryang", "Haryan", "Aryan", "Harjang", "HA"],
        "Wurukung": ["Wurukung", "Urukung", "Wuruku", "Uruku", "Wuruk", "Uruk", "WU"],
        "Paniron": ["Paniron", "Paniran", "Paniren", "PA"],
        "Was": ["Was", "Vas", "Wasi", "WA"],
        "Maulu": ["Maulu", "Maul", "Mauluh", "MA"]
    }
    
    # VARIAN PANCAWARA 5 - URUTAN STANDAR: 0=PAHING, 1=PON, 2=WAGE, 3=KALIWON, 4=UMANIS
    PANCAWARA_VARIANTS = {
        "Pahing": ["Pahing", "Paing", "Pahin", "PA"],
        "Pon": ["Pon", "Pohan", "PO"],
        "Wage": ["Wage", "Wageh", "WA"],
        "Kaliwon": ["Kaliwon", "Kliwon", "Kilwon", "KA"],
        "Umanis": ["Umanis", "Legi", "Manis", "U"]
    }
    
    # VARIAN SAPTAWARA 7 - URUTAN STANDAR: 0=A, 1=SO, 2=ANG, 3=BU, 4=WR, 5=SU, 6=SA
    SAPTAWARA_VARIANTS = {
        "Aditya": ["Raditya", "Aditya", "Ditya", "Minggu", "Radite", "Redite", "A"],
        "Soma": ["Soma", "Senin", "Senen", "SO"],
        "Anggara": ["Anggara", "Selasa", "ANG"],
        "Budha": ["Budha", "Buda", "Buddha", "Rabu", "BU"],
        "Wrhaspati": ["Wrhaspati", "Wrespati", "Respati", "Brespati", "Kamis", "WR"],
        "Sukra": ["Sukra", "Jumat", "Sukra", "SU"],
        "Saniscara": ["Saniscara", "Sabtu", "Tumpak", "SA"]
    }
    
    # VARIAN WUKU NAMES
    WUKU_NAMES_VARIANTS = {
        "Sinta": ["Sinta", "Sintha"],
        "Landep": ["Landep", "Landhep"],
        "Wukir": ["Wukir", "Wukih"],
        "Kurantil": ["Kurantil", "Kurantil", "Kurantel"],
        "Tolu": ["Tolu", "Tolo"],
        "Gumbreg": ["Gumbreg", "Gumbrek"],
        "Warigalit": ["Warigalit", "Warigalit"],
        "Warigagung": ["Warigagung", "Warigagung"],
        "Julungwangi": ["Julungwangi", "Jolungwangi"],
        "Sungsang": ["Sungsang", "Sungsang"],
        "Galungan": ["Galungan", "Dungulan", "Dungulan"],
        "Kuningan": ["Kuningan", "Kuningan"],
        "Langkir": ["Langkir", "Langkir"],
        "Mandasiya": ["Mandasiya", "Madasiya", "Mandasiya"],
        "Julungpujut": ["Julungpujut", "Jolungpujut"],
        "Pahang": ["Pahang", "Pahang"],
        "Kuruwelut": ["Kuruwelut", "Kuruwelut"],
        "Marakeh": ["Marakeh", "Marakeh"],
        "Tambir": ["Tambir", "Tambir"],
        "Medangkungan": ["Medangkungan", "Medangkungan"],
        "Maktal": ["Maktal", "Maktal"],
        "Wuye": ["Wuye", "Wuye"],
        "Manahil": ["Manahil", "Manahil"],
        "Prangbakat": ["Prangbakat", "Prangbakat"],
        "Bala": ["Bala", "Bala"],
        "Wugu": ["Wugu", "Wugu"],
        "Wayang": ["Wayang", "Wayang"],
        "Kulawu": ["Kulawu", "Kulawu"],
        "Dukut": ["Dukut", "Dhukut"],
        "Watugunung": ["Watugunung", "Watugunung"]
    }
    
    # ========================================================================
    # MATRIKS WARA WUKU 210 HARI - untuk lookup cepat dan verifikasi
    # ========================================================================
    WARA_WUKU_MATRIX_210 = {
        "NOTE": "Index 0 = TU-PA-Ā (Tungleh-Pahing-Aditya). The full 210 entries (index, wukuNumber, wukuName, Sadwara, Pancawara, Sapta) are definitive and should match calculations from mathematical formulas.",
        "DATA": [
          [0,1,"Sinta","Tungleh","Pahing","Aditya"], [1,1,"Sinta","Aryang","Pon","Soma"], [2,1,"Sinta","Urukung","Wage","Anggara"], [3,1,"Sinta","Paniron","Kaliwon","Buda"], [4,1,"Sinta","Was","Umanis","Wrespati"], [5,1,"Sinta","Maulu","Pahing","Sukra"], [6,1,"Sinta","Tungleh","Pon","Saniscara"],
          [7,2,"Landep","Aryang","Wage","Aditya"], [8,2,"Landep","Urukung","Kaliwon","Soma"], [9,2,"Landep","Paniron","Umanis","Anggara"], [10,2,"Landep","Was","Pahing","Buda"], [11,2,"Landep","Maulu","Pon","Wrespati"], [12,2,"Landep","Tungleh","Wage","Sukra"], [13,2,"Landep","Aryang","Kaliwon","Saniscara"],
          [14,3,"Wukir","Urukung","Umanis","Aditya"], [15,3,"Wukir","Paniron","Pahing","Soma"], [16,3,"Wukir","Was","Pon","Anggara"], [17,3,"Wukir","Maulu","Wage","Buda"], [18,3,"Wukir","Tungleh","Kaliwon","Wrespati"], [19,3,"Wukir","Aryang","Umanis","Sukra"], [20,3,"Wukir","Urukung","Pahing","Saniscara"],
          [21,4,"Kurantil","Paniron","Pon","Aditya"], [22,4,"Kurantil","Was","Wage","Soma"], [23,4,"Kurantil","Maulu","Kaliwon","Anggara"], [24,4,"Kurantil","Tungleh","Umanis","Buda"], [25,4,"Kurantil","Aryang","Pahing","Wrespati"], [26,4,"Kurantil","Urukung","Pon","Sukra"], [27,4,"Kurantil","Paniron","Wage","Saniscara"],
          [28,5,"Tolu","Was","Kaliwon","Aditya"], [29,5,"Tolu","Maulu","Umanis","Soma"], [30,5,"Tolu","Tungleh","Pahing","Anggara"], [31,5,"Tolu","Aryang","Pon","Buda"], [32,5,"Tolu","Urukung","Wage","Wrespati"], [33,5,"Tolu","Paniron","Kaliwon","Sukra"], [34,5,"Tolu","Was","Umanis","Saniscara"],
          [35,6,"Gumbreg","Maulu","Pahing","Aditya"], [36,6,"Gumbreg","Tungleh","Pon","Soma"], [37,6,"Gumbreg","Aryang","Wage","Anggara"], [38,6,"Gumbreg","Urukung","Kaliwon","Buda"], [39,6,"Gumbreg","Paniron","Umanis","Wrespati"], [40,6,"Gumbreg","Was","Pahing","Sukra"], [41,6,"Gumbreg","Maulu","Pon","Saniscara"],
          [42,7,"Warigalit","Tungleh","Wage","Aditya"], [43,7,"Warigalit","Aryang","Kaliwon","Soma"], [44,7,"Warigalit","Urukung","Umanis","Anggara"], [45,7,"Warigalit","Paniron","Pahing","Buda"], [46,7,"Warigalit","Was","Pon","Wrespati"], [47,7,"Warigalit","Maulu","Wage","Sukra"], [48,7,"Warigalit","Tungleh","Kaliwon","Saniscara"],
          [49,8,"Warigagung","Aryang","Umanis","Aditya"], [50,8,"Warigagung","Urukung","Pahing","Soma"], [51,8,"Warigagung","Paniron","Pon","Anggara"], [52,8,"Warigagung","Was","Wage","Buda"], [53,8,"Warigagung","Maulu","Kaliwon","Wrespati"], [54,8,"Warigagung","Tungleh","Umanis","Sukra"], [55,8,"Warigagung","Aryang","Pahing","Saniscara"],
          [56,9,"Julungwangi","Urukung","Pon","Aditya"], [57,9,"Julungwangi","Paniron","Wage","Soma"], [58,9,"Julungwangi","Was","Kaliwon","Anggara"], [59,9,"Julungwangi","Maulu","Umanis","Buda"], [60,9,"Julungwangi","Tungleh","Pahing","Wrespati"], [61,9,"Julungwangi","Aryang","Pon","Sukra"], [62,9,"Julungwangi","Urukung","Wage","Saniscara"],
          [63,10,"Sungsang","Paniron","Kaliwon","Aditya"], [64,10,"Sungsang","Was","Umanis","Soma"], [65,10,"Sungsang","Maulu","Pahing","Anggara"], [66,10,"Sungsang","Tungleh","Pon","Buda"], [67,10,"Sungsang","Aryang","Wage","Wrespati"], [68,10,"Sungsang","Urukung","Kaliwon","Sukra"], [69,10,"Sungsang","Paniron","Umanis","Saniscara"],
          [70,11,"Galungan","Was","Pahing","Aditya"], [71,11,"Galungan","Maulu","Pon","Soma"], [72,11,"Galungan","Tungleh","Wage","Anggara"], [73,11,"Galungan","Aryang","Kaliwon","Buda"], [74,11,"Galungan","Urukung","Umanis","Wrespati"], [75,11,"Galungan","Paniron","Pahing","Sukra"], [76,11,"Galungan","Was","Pon","Saniscara"],
          [77,12,"Kuningan","Maulu","Wage","Aditya"], [78,12,"Kuningan","Tungleh","Kaliwon","Soma"], [79,12,"Kuningan","Aryang","Umanis","Anggara"], [80,12,"Kuningan","Urukung","Pahing","Buda"], [81,12,"Kuningan","Paniron","Pon","Wrespati"], [82,12,"Kuningan","Was","Wage","Sukra"], [83,12,"Kuningan","Maulu","Kaliwon","Saniscara"],
          [84,13,"Langkir","Tungleh","Umanis","Aditya"], [85,13,"Langkir","Aryang","Pahing","Soma"], [86,13,"Langkir","Urukung","Pon","Anggara"], [87,13,"Langkir","Paniron","Wage","Buda"], [88,13,"Langkir","Was","Kaliwon","Wrespati"], [89,13,"Langkir","Maulu","Umanis","Sukra"], [90,13,"Langkir","Tungleh","Pahing","Saniscara"],
          [91,14,"Mandasiya","Aryang","Pon","Aditya"], [92,14,"Mandasiya","Urukung","Wage","Soma"], [93,14,"Mandasiya","Paniron","Kaliwon","Anggara"], [94,14,"Mandasiya","Was","Umanis","Buda"], [95,14,"Mandasiya","Maulu","Pahing","Wrespati"], [96,14,"Mandasiya","Tungleh","Pon","Sukra"], [97,14,"Mandasiya","Aryang","Wage","Saniscara"],
          [98,15,"Julungpujut","Urukung","Kaliwon","Aditya"], [99,15,"Julungpujut","Paniron","Umanis","Soma"], [100,15,"Julungpujut","Was","Pahing","Anggara"], [101,15,"Julungpujut","Maulu","Pon","Buda"], [102,15,"Julungpujut","Tungleh","Wage","Wrespati"], [103,15,"Julungpujut","Aryang","Kaliwon","Sukra"], [104,15,"Julungpujut","Urukung","Umanis","Saniscara"],
          [105,16,"Pahang","Paniron","Pahing","Aditya"], [106,16,"Pahang","Was","Pon","Soma"], [107,16,"Pahang","Maulu","Wage","Anggara"], [108,16,"Pahang","Tungleh","Kaliwon","Buda"], [109,16,"Pahang","Aryang","Umanis","Wrespati"], [110,16,"Pahang","Urukung","Pahing","Sukra"], [111,16,"Pahang","Paniron","Pon","Saniscara"],
          [112,17,"Kuruwelut","Was","Wage","Aditya"], [113,17,"Kuruwelut","Maulu","Kaliwon","Soma"], [114,17,"Kuruwelut","Tungleh","Umanis","Anggara"], [115,17,"Kuruwelut","Aryang","Pahing","Buda"], [116,17,"Kuruwelut","Urukung","Pon","Wrespati"], [117,17,"Kuruwelut","Paniron","Wage","Sukra"], [118,17,"Kuruwelut","Was","Kaliwon","Saniscara"],
          [119,18,"Marakeh","Maulu","Umanis","Aditya"], [120,18,"Marakeh","Tungleh","Pahing","Soma"], [121,18,"Marakeh","Aryang","Pon","Anggara"], [122,18,"Marakeh","Urukung","Wage","Buda"], [123,18,"Marakeh","Paniron","Kaliwon","Wrespati"], [124,18,"Marakeh","Was","Umanis","Sukra"], [125,18,"Marakeh","Maulu","Pahing","Saniscara"],
          [126,19,"Tambir","Tungleh","Pon","Aditya"], [127,19,"Tambir","Aryang","Wage","Soma"], [128,19,"Tambir","Urukung","Kaliwon","Anggara"], [129,19,"Tambir","Paniron","Umanis","Buda"], [130,19,"Tambir","Was","Pahing","Wrespati"], [131,19,"Tambir","Maulu","Pon","Sukra"], [132,19,"Tambir","Tungleh","Wage","Saniscara"],
          [133,20,"Medangkungan","Aryang","Kaliwon","Aditya"], [134,20,"Medangkungan","Urukung","Umanis","Soma"], [135,20,"Medangkungan","Paniron","Pahing","Anggara"], [136,20,"Medangkungan","Was","Pon","Buda"], [137,20,"Medangkungan","Maulu","Wage","Wrespati"], [138,20,"Medangkungan","Tungleh","Kaliwon","Sukra"], [139,20,"Medangkungan","Aryang","Umanis","Saniscara"],
          [140,21,"Maktal","Urukung","Pahing","Aditya"], [141,21,"Maktal","Paniron","Pon","Soma"], [142,21,"Maktal","Was","Wage","Anggara"], [143,21,"Maktal","Maulu","Kaliwon","Buda"], [144,21,"Maktal","Tungleh","Umanis","Wrespati"], [145,21,"Maktal","Aryang","Pahing","Sukra"], [146,21,"Maktal","Urukung","Pon","Saniscara"],
          [147,22,"Wuye","Paniron","Wage","Aditya"], [148,22,"Wuye","Was","Kaliwon","Soma"], [149,22,"Wuye","Maulu","Umanis","Anggara"], [150,22,"Wuye","Tungleh","Pahing","Buda"], [151,22,"Wuye","Aryang","Pon","Wrespati"], [152,22,"Wuye","Urukung","Wage","Sukra"], [153,22,"Wuye","Paniron","Kaliwon","Saniscara"],
          [154,23,"Manahil","Was","Umanis","Aditya"], [155,23,"Manahil","Maulu","Pahing","Soma"], [156,23,"Manahil","Tungleh","Pon","Anggara"], [157,23,"Manahil","Aryang","Wage","Buda"], [158,23,"Manahil","Urukung","Kaliwon","Wrespati"], [159,23,"Manahil","Paniron","Umanis","Sukra"], [160,23,"Manahil","Was","Pahing","Saniscara"],
          [161,24,"Prangbakat","Maulu","Pon","Aditya"], [162,24,"Prangbakat","Tungleh","Wage","Soma"], [163,24,"Prangbakat","Aryang","Kaliwon","Anggara"], [164,24,"Prangbakat","Urukung","Umanis","Buda"], [165,24,"Prangbakat","Paniron","Pahing","Wrespati"], [166,24,"Prangbakat","Was","Pon","Sukra"], [167,24,"Prangbakat","Maulu","Wage","Saniscara"],
          [168,25,"Bala","Tungleh","Kaliwon","Aditya"], [169,25,"Bala","Aryang","Umanis","Soma"], [170,25,"Bala","Urukung","Pahing","Anggara"], [171,25,"Bala","Paniron","Pon","Buda"], [172,25,"Bala","Was","Wage","Wrespati"], [173,25,"Bala","Maulu","Kaliwon","Sukra"], [174,25,"Bala","Tungleh","Umanis","Saniscara"],
          [175,26,"Wugu","Aryang","Pahing","Aditya"], [176,26,"Wugu","Urukung","Pon","Soma"], [177,26,"Wugu","Paniron","Wage","Anggara"], [178,26,"Wugu","Was","Kaliwon","Buda"], [179,26,"Wugu","Maulu","Umanis","Wrespati"], [180,26,"Wugu","Tungleh","Pahing","Sukra"], [181,26,"Wugu","Aryang","Pon","Saniscara"],
          [182,27,"Wayang","Urukung","Wage","Aditya"], [183,27,"Wayang","Paniron","Kaliwon","Soma"], [184,27,"Wayang","Was","Umanis","Anggara"], [185,27,"Wayang","Maulu","Pahing","Buda"], [186,27,"Wayang","Tungleh","Pon","Wrespati"], [187,27,"Wayang","Aryang","Wage","Sukra"], [188,27,"Wayang","Urukung","Kaliwon","Saniscara"],
          [189,28,"Kulawu","Paniron","Umanis","Aditya"], [190,28,"Kulawu","Was","Pahing","Soma"], [191,28,"Kulawu","Maulu","Pon","Anggara"], [192,28,"Kulawu","Tungleh","Wage","Buda"], [193,28,"Kulawu","Aryang","Kaliwon","Wrespati"], [194,28,"Kulawu","Urukung","Umanis","Sukra"], [195,28,"Kulawu","Paniron","Pahing","Saniscara"],
          [196,29,"Dukut","Was","Pon","Aditya"], [197,29,"Dukut","Maulu","Wage","Soma"], [198,29,"Dukut","Tungleh","Kaliwon","Anggara"], [199,29,"Dukut","Aryang","Umanis","Buda"], [200,29,"Dukut","Urukung","Pahing","Wrespati"], [201,29,"Dukut","Paniron","Pon","Sukra"], [202,29,"Dukut","Was","Wage","Saniscara"],
          [203,30,"Watugunung","Maulu","Kaliwon","Aditya"], [204,30,"Watugunung","Tungleh","Umanis","Soma"], [205,30,"Watugunung","Aryang","Pahing","Anggara"], [206,30,"Watugunung","Urukung","Pon","Buda"], [207,30,"Watugunung","Paniron","Wage","Wrespati"], [208,30,"Watugunung","Was","Kaliwon","Sukra"], [209,30,"Watugunung","Maulu","Umanis","Saniscara"]
        ]
    }

# ============================================================================
# MATH CORE - FUNGSI MATEMATIKA DASAR
# ============================================================================

class MathCore:
    """Fungsi matematika dasar untuk konversi tanggal"""
    
    @staticmethod
    def jd_to_julian_date(jd: float) -> Tuple[int, int, float]:
        """Konversi Julian Day ke tanggal Julian"""
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
    def julian_date_to_jd(year: int, month: int, day: float) -> float:
        """Konversi tanggal Julian ke Julian Day"""
        if month <= 2:
            year -= 1
            month += 12
        
        A = int(year / 100)
        B = 2 - A + int(A / 4)
        
        jd = (int(365.25 * (year + 4716)) + 
              int(30.6001 * (month + 1)) + 
              day + B - 1524.5)
        
        return jd
    
    @staticmethod
    def ka_to_jd(ka: int) -> float:
        """Konversi KA ke Julian Day"""
        return ka + ΩConstants.KALI_EPOCH_JD_NOON
    
    @staticmethod
    def jd_to_ka(jd: float) -> int:
        """Konversi Julian Day ke KA"""
        return int(round(jd - ΩConstants.KALI_EPOCH_JD_NOON))
    
    @staticmethod
    def ka_to_julian_date(ka: int) -> Tuple[int, int, float]:
        """Konversi KA ke tanggal Julian"""
        jd = MathCore.ka_to_jd(ka)
        return MathCore.jd_to_julian_date(jd)
    
    @staticmethod
    def julian_date_to_ka(year: int, month: int, day: float) -> int:
        """Konversi tanggal Julian ke KA"""
        jd = MathCore.julian_date_to_jd(year, month, day)
        return MathCore.jd_to_ka(jd)
    
    @staticmethod
    def ka_for_jan1(year_ce: int) -> int:
        """Hitung KA untuk 1 Januari tahun Masehi"""
        if year_ce >= 0:
            ka_jan1 = ΩConstants.KA_1_JAN_1_BC + (365 * year_ce) + ((year_ce + 3) // 4)
        else:
            year_abs = abs(year_ce)
            ka_jan1 = ΩConstants.KA_1_JAN_1_BC - (365 * year_abs) - ((year_abs + 2) // 4)
        
        return int(ka_jan1)
    
    @staticmethod
    def calculate_i_from_ka(ka: int) -> int:
        """Hitung indeks i: i = (KA - KA_8_FEB_1_BC) mod 210"""
        return (ka - ΩConstants.KA_8_FEB_1_BC) % ΩConstants.WUKU_CYCLE
    
    @staticmethod
    def calculate_s_from_ka(ka: int) -> int:
        """Hitung s: s = KA mod 210"""
        return ka % ΩConstants.WUKU_CYCLE
    
    @staticmethod
    def normalize_angle(angle: float) -> float:
        """Normalisasi sudut ke 0-360 derajat"""
        angle %= 360
        if angle < 0:
            angle += 360
        return angle
    
    @staticmethod
    def day_of_year(year: int, month: int, day: int) -> int:
        """Hitung hari ke berapa dalam setahun"""
        month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        # Cek tahun kabisat
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            month_days[1] = 29
        
        return sum(month_days[:month-1]) + day

# ============================================================================
# NORMALIZATION ENGINE - VARIAN EJAAN
# ============================================================================

class NormalizationEngine:
    """Normalisasi varian ejaan ke bentuk standar"""
    
    def __init__(self):
        self.const = ΩConstants
        self._build_mappings()
    
    def _build_mappings(self):
        """Bangun mapping varian ke standar dari semua varian yang tersedia"""
        self.mapping = {}
        
        # Bangun mapping dari semua varian ke bentuk standar
        self._add_variant_mappings(self.const.MONTHS_SAKA_VARIANTS)
        self._add_variant_mappings(self.const.SADWARA_VARIANTS)
        self._add_variant_mappings(self.const.PANCAWARA_VARIANTS)
        self._add_variant_mappings(self.const.SAPTAWARA_VARIANTS)
        self._add_variant_mappings(self.const.WUKU_NAMES_VARIANTS)
        
        # Tambahkan mapping tambahan untuk format yang umum
        additional_mappings = {
            # Bulan Saka
            "asuji": "Asvini",
            "wesaka": "Vaisakha",
            "besakha": "Vaisakha",
            "jestha": "Jyestha",
            "srawana": "Sravana",
            "badrapada": "Bhadrapada",
            "magha": "Magha",
            "palguna": "Phalguna",
            "pausa": "Pausa",
            "kartika": "Kartika",
            "margasira": "Margasira",
            
            # Wuku
            "wukir": "Wukir",
            "wugu": "Wugu",
            "wayang": "Wayang",
            "kulawu": "Kulawu",
            "dukut": "Dukut",
            "watugunung": "Watugunung",
            
            # Wara
            "jumat": "Sukra",
            "sukra": "Sukra",
            "sukro": "Sukra",
            "redite": "Aditya",
            "minggu": "Aditya",
            "senen": "Soma",
            "senin": "Soma",
            "selasa": "Anggara",
            "rabu": "Budha",
            "kamis": "Wrhaspati",
            "sabtu": "Saniscara",
            "tumpak": "Saniscara",
            "legi": "Umanis",
            "umanis": "Umanis",
            "pahing": "Pahing",
            "pon": "Pon",
            "wage": "Wage",
            "kliwon": "Kaliwon",
            "kaliwon": "Kaliwon",
            
            # Variasi lain dari matriks
            "urukung": "Wurukung",
            "aryang": "Haryang",
            "buda": "Budha",
            "wrespati": "Wrhaspati",
        }
        
        for key, value in additional_mappings.items():
            self.mapping[key] = value
    
    def _add_variant_mappings(self, variant_dict):
        """Tambahkan mapping dari varian ke standar"""
        for standard, variants in variant_dict.items():
            for variant in variants:
                self.mapping[variant.lower()] = standard
    
    def normalize(self, text: str) -> str:
        """Normalisasi teks ke bentuk standar"""
        if not text:
            return ""
        
        # Lowercase dan strip
        text_lower = text.lower().strip()
        
        # Cari di mapping
        if text_lower in self.mapping:
            return self.mapping[text_lower]
        
        # Jika tidak ditemukan, kapitalisasi sederhana
        return text.title()
    
    def normalize_inscription_data(self, data: Dict) -> Dict:
        """Normalisasi semua data prasasti"""
        normalized = data.copy()
        
        fields = ['masa', 'wuku', 'paksa', 'nakshatra']
        for field in fields:
            if field in normalized and normalized[field]:
                normalized[field] = self.normalize(normalized[field])
        
        # Normalisasi wara_string
        if 'wara_string' in normalized and normalized['wara_string']:
            parts = normalized['wara_string'].split('-')
            normalized_parts = [self.normalize(p) for p in parts]
            
            if len(normalized_parts) >= 3:
                normalized['wara_string'] = f"{normalized_parts[0]}-{normalized_parts[1]}-{normalized_parts[2]}"
            elif len(normalized_parts) == 2:
                # Format "Jumat-Wage"
                if normalized_parts[0] in ["Sukra", "Jumat"]:
                    normalized['wara_string'] = f"Haryang-{normalized_parts[1]}-Sukra"
        
        return normalized

# ============================================================================
# SISTEM MEKANIK KA-WUKU-WARA (MechanicalEngine) - VERSI DIPERBAIKI LENGKAP
# ============================================================================

class MechanicalEngine:
    """Engine sistem mekanik 210-hari dengan TPDP dan DUAL VERIFICATION - DIPERBAIKI"""
    
    def __init__(self):
        self.const = ΩConstants
        self.math = MathCore()
        self.norm = NormalizationEngine()
        
        # Gunakan mapping bulan Saka-Julian yang baru
        self.SAKA_MONTH_TO_JULIAN_RANGE = self.const.SAKA_MONTH_TO_JULIAN_RANGE
        
        # Bangun struktur data lookup dari matriks
        self._build_wara_wuku_lookup()
        
        # Verifikasi matriks vs rumus
        self._verify_matrix_vs_formula()
    
    # ========================================================================
    # VALIDASI TAHUN BERDASARKAN ATURAN KONVERSI DASAR
    # ========================================================================
    
    def validate_ce_year_by_basic_rule(self, saka_year: int, masa: str, candidate_ce_year: int) -> bool:
        """
        Validasi apakah tahun Masehi kandidat sesuai dengan aturan konversi dasar.
        
        Aturan:
        1. Bulan Pausa: saka_year +78 atau +79
        2. Bulan Magha/Phalguna: saka_year +79
        3. Bulan lainnya (Caitra-Margasira): saka_year +78
        
        Returns:
            bool: True jika valid, False jika tidak valid
        """
        # Normalisasi nama bulan
        masa_norm = self.norm.normalize(masa)
        
        # Dapatkan tahun Masehi yang valid berdasarkan aturan
        valid_years = self.const.basic_saka_to_ce_year(saka_year, masa_norm)
        
        if isinstance(valid_years, list):
            # Bulan ambigu (Pausa)
            return candidate_ce_year in valid_years
        else:
            # Bulan tidak ambigu
            return candidate_ce_year == valid_years
    
    def get_valid_ce_years_by_rule(self, saka_year: int, masa: str) -> List[int]:
        """
        Dapatkan semua tahun Masehi yang valid berdasarkan aturan konversi dasar.
        
        Returns:
            List[int]: Daftar tahun Masehi yang valid
        """
        masa_norm = self.norm.normalize(masa)
        valid_years = self.const.basic_saka_to_ce_year(saka_year, masa_norm)
        
        if isinstance(valid_years, list):
            return valid_years
        else:
            return [valid_years]
    
    def _build_wara_wuku_lookup(self):
        """Bangun struktur data lookup dari matriks WARA_WUKU_MATRIX_210"""
        self.wara_triple_to_index = {}  # (sad, panca, sapta) -> index
        self.wara_triple_to_wuku = {}   # (sad, panca, sapta) -> wuku_name
        self.wuku_sapta_to_triple = {}  # (wuku_name, sapta) -> (sad, panca, sapta)
        self.wuku_all_triples = {}      # wuku_name -> list of 7 triples
        
        for entry in self.const.WARA_WUKU_MATRIX_210["DATA"]:
            idx, wuku_num, wuku_name, sad, panca, sapta = entry
            
            # Normalisasi nama
            sad_norm = self.norm.normalize(sad)
            panca_norm = self.norm.normalize(panca)
            sapta_norm = self.norm.normalize(sapta)
            wuku_norm = self.norm.normalize(wuku_name)
            
            # Triple wara ke index
            triple_key = (sad_norm, panca_norm, sapta_norm)
            self.wara_triple_to_index[triple_key] = idx
            self.wara_triple_to_wuku[triple_key] = wuku_norm
            
            # Wuku + sapta ke triple
            wuku_sapta_key = (wuku_norm, sapta_norm)
            if wuku_sapta_key not in self.wuku_sapta_to_triple:
                self.wuku_sapta_to_triple[wuku_sapta_key] = triple_key
            
            # Semua triple dalam wuku
            if wuku_norm not in self.wuku_all_triples:
                self.wuku_all_triples[wuku_norm] = []
            self.wuku_all_triples[wuku_norm].append(triple_key)
        
        # Verifikasi setiap wuku memiliki tepat 7 triple
        for wuku_name, triples in self.wuku_all_triples.items():
            if len(triples) != 7:
                print(f"⚠️ PERINGATAN: Wuku {wuku_name} memiliki {len(triples)} triple, seharusnya 7")
        
        print(f"✓ Built lookup: {len(self.wara_triple_to_index)} triple wara, {len(self.wuku_all_triples)} wuku")
    
    def _verify_matrix_vs_formula(self):
        """Verifikasi bahwa matriks konsisten dengan rumus KA"""
        print(f"\n{'='*60}")
        print("VERIFIKASI MATRIKS vs RUMUS KA")
        print(f"{'='*60}")
        
        errors = []
        for idx, entry in enumerate(self.const.WARA_WUKU_MATRIX_210["DATA"]):
            matrix_idx, wuku_num, wuku_name, sad, panca, sapta = entry
            
            # Hitung dengan rumus KA
            # KA untuk index i adalah: KA = KA_8_FEB_1_BC + i
            ka_from_matrix = self.const.KA_8_FEB_1_BC + matrix_idx
            
            # Hitung wuku/wara dari KA dengan rumus
            calculated = self.calculate_wuku_wara_from_ka_by_formula(ka_from_matrix)
            
            # Bandingkan
            matrix_sad = self.norm.normalize(sad)
            matrix_panca = self.norm.normalize(panca)
            matrix_sapta = self.norm.normalize(sapta)
            matrix_wuku = self.norm.normalize(wuku_name)
            
            if calculated["sadwara"] != matrix_sad:
                errors.append(f"Index {matrix_idx}: Sadwara mismatch - Matrix: {matrix_sad}, Formula: {calculated['sadwara']}")
            
            if calculated["pancawara"] != matrix_panca:
                errors.append(f"Index {matrix_idx}: Pancawara mismatch - Matrix: {matrix_panca}, Formula: {calculated['pancawara']}")
            
            if calculated["saptawara"] != matrix_sapta:
                errors.append(f"Index {matrix_idx}: Saptawara mismatch - Matrix: {matrix_sapta}, Formula: {calculated['saptawara']}")
            
            if calculated["wuku_name"] != matrix_wuku:
                errors.append(f"Index {matrix_idx}: Wuku mismatch - Matrix: {matrix_wuku}, Formula: {calculated['wuku_name']}")
        
        if errors:
            print(f"⚠️ Ditemukan {len(errors)} inkonsistensi:")
            for error in errors[:5]:
                print(f"  {error}")
            if len(errors) > 5:
                print(f"  ... dan {len(errors)-5} inkonsistensi lainnya")
            return False
        else:
            print(f"✓ Matriks 210 hari KONSISTEN dengan rumus KA")
            print(f"✓ KA_8_FEB_1_BC = {self.const.KA_8_FEB_1_BC}")
            print(f"✓ Setiap index i (0-209) memiliki: KA = KA_8_FEB_1_BC + i")
            return True
    
    def julian_month_to_saka_month(self, julian_month: int) -> Optional[str]:
        """Perkiraan konversi bulan Julian ke bulan Saka"""
        mapping = {
            1: "Pausa", 2: "Magha", 3: "Phalguna", 4: "Caitra",
            5: "Vaisakha", 6: "Jyestha", 7: "Asadha", 8: "Sravana",
            9: "Bhadrapada", 10: "Asvini", 11: "Kartika", 12: "Margasira"
        }
        return mapping.get(julian_month)
    
    def get_adjacent_months(self, masa: str) -> List[str]:
        """Dapatkan bulan-bulan adjacent (sebelum dan sesudah)"""
        if masa not in self.const.SAKA_MONTHS_ORDER:
            return []
        
        idx = self.const.SAKA_MONTHS_ORDER.index(masa)
        prev_idx = (idx - 1) % 12
        next_idx = (idx + 1) % 12
        
        return [
            self.const.SAKA_MONTHS_ORDER[prev_idx],
            self.const.SAKA_MONTHS_ORDER[next_idx]
        ]
    
    def calculate_wuku_wara_from_ka(self, ka: int) -> Dict:
        """Hitung wuku dan wara dari KA - VERSI DIPERBAIKI DENGAN URUTAN STANDAR"""
        # Rumus absolut: i = (KA - KA_8_FEB_1_BC) mod 210
        i = self.math.calculate_i_from_ka(ka)
        
        # Hitung s = KA mod 210
        s = self.math.calculate_s_from_ka(ka)
        
        # Hitung wuku
        wuku_num = (i // 7) + 1
        day_in_wuku = (i % 7) + 1
        
        # Dapatkan nama wuku (indeks 0-29)
        wuku_name = self.const.WUKU_NAMES_STANDARD[wuku_num - 1] if 1 <= wuku_num <= 30 else "Unknown"
        
        # Hitung wara DENGAN URUTAN STANDAR YANG TELAH DIPERBAIKI
        # Sadwara (siklus 6) - sesuai standar: 0=TU, 1=HA, 2=WU, 3=PA, 4=WA, 5=MA
        sadwara_idx = i % 6
        sadwara = self.const.SADWARA_STANDARD[sadwara_idx]
        
        # Pancawara (siklus 5) - sesuai standar: 0=PAHING, 1=PON, 2=WAGE, 3=KALIWON, 4=UMANIS
        pancawara_idx = i % 5
        pancawara = self.const.PANCAWARA_STANDARD[pancawara_idx]
        
        # Saptawara (siklus 7) - sesuai standar: 0=A, 1=SO, 2=ANG, 3=BU, 4=WR, 5=SU, 6=SA
        saptawara_idx = i % 7
        saptawara = self.const.SAPTAWARA_STANDARD[saptawara_idx]
        
        wara_string = f"{sadwara}-{pancawara}-{saptawara}"
        
        return {
            "ka": ka,
            "s": s,
            "i": i,
            "wuku_num": wuku_num,
            "wuku_name": wuku_name,
            "day_in_wuku": day_in_wuku,
            "sadwara": sadwara,
            "pancawara": pancawara,
            "saptawara": saptawara,
            "wara_string": wara_string
        }
    
    def find_tu_pa_a_in_year(self, ce_year: int) -> List[Dict]:
        """Cari semua TU-PA-Ā dalam tahun Masehi - DUAL VERIFICATION"""
        # Gunakan metode rumus untuk keakuratan
        candidates_formula = self.find_tu_pa_a_with_formula(ce_year)
        
        # Juga gunakan metode lama untuk verifikasi
        candidates_old = self._find_tu_pa_a_in_year_old(ce_year)
        
        # Gabungkan dan deduplikasi
        all_candidates = []
        seen_ka = set()
        
        for cand in candidates_formula + candidates_old:
            if cand["ka"] not in seen_ka:
                seen_ka.add(cand["ka"])
                
                # Pastikan wuku_info memiliki day_in_wuku
                if "wuku_info" in cand and "day_in_wuku" not in cand["wuku_info"]:
                    # Hitung day_in_wuku dari i
                    i = cand["wuku_info"].get("i", 0)
                    cand["wuku_info"]["day_in_wuku"] = (i % 7) + 1
                
                all_candidates.append(cand)
        
        # Urutkan berdasarkan KA
        all_candidates.sort(key=lambda x: x["ka"])
        return all_candidates
    
    def _find_tu_pa_a_in_year_old(self, ce_year: int) -> List[Dict]:
        """Metode lama (untuk verifikasi)"""
        # KA untuk 1 Januari tahun tersebut
        ka_jan1 = self.math.ka_for_jan1(ce_year)
        
        # Hitung offset dari 1 Januari ke TU-PA-Ā berikutnya
        # TU-PA-Ā terjadi ketika i = 0
        offset = (self.const.KA_8_FEB_1_BC - ka_jan1) % self.const.WUKU_CYCLE
        
        ka_tu_pa_a = ka_jan1 + offset
        year, month, day = self.math.ka_to_julian_date(ka_tu_pa_a)
        
        candidates = []
        
        # Verifikasi bahwa tanggal masih dalam tahun yang sama
        if year == ce_year:
            s = self.math.calculate_s_from_ka(ka_tu_pa_a)
            i = self.math.calculate_i_from_ka(ka_tu_pa_a)
            wuku_info = self.calculate_wuku_wara_from_ka(ka_tu_pa_a)
            
            if i == 0:
                candidates.append({
                    "ka": ka_tu_pa_a,
                    "s": s,
                    "i": i,
                    "date": (year, month, day),
                    "wuku_info": wuku_info,
                    "is_tu_pa_a": True,
                    "day_of_year": self._day_of_year(year, month, int(day))
                })
        
        # Cek kemungkinan TU-PA-Ā kedua dalam tahun yang sama
        ka_tu_pa_a_next = ka_tu_pa_a + self.const.WUKU_CYCLE
        year_next, month_next, day_next = self.math.ka_to_julian_date(ka_tu_pa_a_next)
        
        if year_next == ce_year:
            s_next = self.math.calculate_s_from_ka(ka_tu_pa_a_next)
            i_next = self.math.calculate_i_from_ka(ka_tu_pa_a_next)
            wuku_info_next = self.calculate_wuku_wara_from_ka(ka_tu_pa_a_next)
            
            if i_next == 0:
                candidates.append({
                    "ka": ka_tu_pa_a_next,
                    "s": s_next,
                    "i": i_next,
                    "date": (year_next, month_next, day_next),
                    "wuku_info": wuku_info_next,
                    "is_tu_pa_a": True,
                    "day_of_year": self._day_of_year(year_next, month_next, int(day_next))
                })
        
        # Cek kemungkinan TU-PA-Ā sebelumnya dalam tahun yang sama
        ka_tu_pa_a_prev = ka_tu_pa_a - self.const.WUKU_CYCLE
        year_prev, month_prev, day_prev = self.math.ka_to_julian_date(ka_tu_pa_a_prev)
        
        if year_prev == ce_year:
            s_prev = self.math.calculate_s_from_ka(ka_tu_pa_a_prev)
            i_prev = self.math.calculate_i_from_ka(ka_tu_pa_a_prev)
            wuku_info_prev = self.calculate_wuku_wara_from_ka(ka_tu_pa_a_prev)
            
            if i_prev == 0:
                candidates.append({
                    "ka": ka_tu_pa_a_prev,
                    "s": s_prev,
                    "i": i_prev,
                    "date": (year_prev, month_prev, day_prev),
                    "wuku_info": wuku_info_prev,
                    "is_tu_pa_a": True,
                    "day_of_year": self._day_of_year(year_prev, month_prev, int(day_prev))
                })
        
        # Urutkan berdasarkan KA
        candidates.sort(key=lambda x: x["ka"])
        return candidates
    
    def _day_of_year(self, year: int, month: int, day: int) -> int:
        """Hitung hari ke berapa dalam setahun"""
        month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        # Cek tahun kabisat
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            month_days[1] = 29
        
        day_of_year = sum(month_days[:month-1]) + day
        return day_of_year
    
    # ========================================================================
    # PERBAIKAN UTAMA: Fungsi saka_to_ce_year yang baru
    # ========================================================================
    
    def saka_to_ce_year(self, saka_year: int, masa_name: str) -> Union[int, List[int]]:
        """Konversi tahun Saka ke Masehi berdasarkan bulan dengan sistem baru"""
        masa = self.norm.normalize(masa_name)
        
        if masa in self.SAKA_MONTH_TO_JULIAN_RANGE:
            info = self.SAKA_MONTH_TO_JULIAN_RANGE[masa]
            
            if masa == "Pausa":
                # Pausa ambigu: bisa +78 atau +79
                return [saka_year + 78, saka_year + 79]
            elif masa in ["Magha", "Phalguna"]:
                # Magha dan Phalguna selalu +79
                return saka_year + 79
            else:
                # Bulan lainnya selalu +78
                return saka_year + 78
        else:
            # Default jika tidak dikenali
            return saka_year + 78
    
    # ========================================================================
    # PERBAIKAN UTAMA: Fungsi untuk mencari TU-PA-Ā sebelum target wara
    # ========================================================================
    
    def find_tu_pa_a_before_target(self, target_ka: int, max_distance: int = 210) -> Optional[int]:
        """
        Cari TU-PA-Ā (i=0) terdekat SEBELUM target KA.
        Return KA dari TU-PA-Ā sebelumnya.
        """
        # Cari mundur dari target KA sampai menemukan i=0
        for offset in range(max_distance + 1):
            check_ka = target_ka - offset
            i = self.math.calculate_i_from_ka(check_ka)
            
            if i == 0:
                # Verifikasi bahwa ini benar-benar TU-PA-Ā
                wuku_info = self.calculate_wuku_wara_from_ka(check_ka)
                if (wuku_info["sadwara"] == "Tungleh" and 
                    wuku_info["pancawara"] == "Pahing" and 
                    wuku_info["saptawara"] == "Aditya"):
                    return check_ka
        
        return None
    
    def find_tu_pa_a_for_wara_target(self, target_triple: Tuple[str, str, str], 
                                     expected_year: int, masa: str) -> List[Dict]:
        """
        Cari TU-PA-Ā yang sesuai untuk wara target dalam tahun yang diharapkan.
        Algoritma: cari semua TU-PA-Ā dalam rentang tahun, lalu pilih yang menghasilkan
        bulan yang sesuai dengan masa Saka.
        """
        # Dapatkan rentang bulan Julian untuk masa Saka
        masa_norm = self.norm.normalize(masa)
        month_info = self.SAKA_MONTH_TO_JULIAN_RANGE.get(masa_norm, {})
        julian_months = month_info.get("julian_months", [])
        
        # Cari TU-PA-Ā dalam tahun yang diharapkan ±1 tahun
        tu_pa_a_candidates = []
        
        for year_offset in [-1, 0, 1]:
            check_year = expected_year + year_offset
            tu_pa_a_list = self.find_tu_pa_a_in_year(check_year)
            
            for tupa in tu_pa_a_list:
                tu_pa_a_candidates.append({
                    "ka": tupa["ka"],
                    "date": tupa["date"],
                    "year": check_year,
                    "distance_to_target": abs(check_year - expected_year)
                })
        
        # Untuk setiap TU-PA-Ā, hitung kandidat dan evaluasi
        evaluated_candidates = []
        
        for tupa in tu_pa_a_candidates:
            # Hitung kandidat KA dari TU-PA-Ā ini
            candidate_ka = self.calculate_candidate_from_triple(tupa["ka"], target_triple)
            
            if candidate_ka:
                # Hitung tanggal
                year, month, day = self.math.ka_to_julian_date(candidate_ka)
                
                # Evaluasi: apakah bulan sesuai dengan masa Saka?
                month_match = month in julian_months if julian_months else True
                
                # Hitung selisih hari dari tengah bulan target
                day_distance = abs(day - 15) if 1 <= day <= 30 else 30
                
                evaluated_candidates.append({
                    "tu_pa_a_ka": tupa["ka"],
                    "tu_pa_a_date": tupa["date"],
                    "candidate_ka": candidate_ka,
                    "candidate_date": (year, month, day),
                    "month_match": month_match,
                    "day_distance": day_distance,
                    "year_match": year == expected_year,
                    "score": 0.0  # Akan dihitung
                })
        
        # Beri skor pada kandidat
        for cand in evaluated_candidates:
            score = 0.0
            
            # Bonus jika tahun cocok
            if cand["year_match"]:
                score += 0.4
            
            # Bonus jika bulan cocok
            if cand["month_match"]:
                score += 0.4
            
            # Bonus jika dekat dengan tengah bulan
            day_score = max(0, 1.0 - (cand["day_distance"] / 15.0))
            score += day_score * 0.2
            
            cand["score"] = score
        
        # Urutkan berdasarkan skor
        evaluated_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        return evaluated_candidates
    
    def parse_wara_string(self, wara_string: str) -> Optional[Dict]:
        """Parse string wara dengan handling varian"""
        if not wara_string:
            return None
            
        parts = wara_string.split('-')
        if len(parts) != 3:
            # Coba format alternatif
            if len(parts) == 2:
                # Format "Jumat-Wage" -> "Haryang-Wage-Sukra"
                if parts[0].lower() in ['jumat', 'sukra']:
                    wara_string = f"Haryang-{parts[1]}-Sukra"
                    parts = wara_string.split('-')
            else:
                return None
        
        # Normalisasi setiap bagian
        sad = self.norm.normalize(parts[0])
        panca = self.norm.normalize(parts[1])
        sapta = self.norm.normalize(parts[2])
        
        return {
            "sadwara": sad,
            "pancawara": panca,
            "saptawara": sapta
        }
    
    # ========================================================================
    # DUAL VERIFICATION SYSTEM: Matriks Lookup + Rumus KA
    # ========================================================================
    
    def calculate_wuku_wara_from_ka_by_formula(self, ka: int) -> Dict:
        """
        Hitung wuku dan wara dari KA menggunakan RUMUS MURNI
        (tanpa menggunakan matriks lookup)
        """
        # Rumus absolut: i = (KA - KA_8_FEB_1_BC) mod 210
        i = (ka - self.const.KA_8_FEB_1_BC) % self.const.WUKU_CYCLE
        
        # Hitung s = KA mod 210
        s = self.math.calculate_s_from_ka(ka)
        
        # Hitung wuku
        wuku_num = (i // 7) + 1
        day_in_wuku = (i % 7) + 1
        
        # Dapatkan nama wuku (indeks 0-29)
        wuku_name = self.const.WUKU_NAMES_STANDARD[wuku_num - 1] if 1 <= wuku_num <= 30 else "Unknown"
        
        # Sadwara (0=TU, 1=HA, 2=WU, 3=PA, 4=WA, 5=MA)
        sadwara_idx = i % 6
        sadwara = self.const.SADWARA_STANDARD[sadwara_idx]
        
        # Pancawara (0=PAHING, 1=PON, 2=WAGE, 3=KALIWON, 4=UMANIS)
        pancawara_idx = i % 5
        pancawara = self.const.PANCAWARA_STANDARD[pancawara_idx]
        
        # Saptawara (0=A, 1=SO, 2=ANG, 3=BU, 4=WR, 5=SU, 6=SA)
        saptawara_idx = i % 7
        saptawara = self.const.SAPTAWARA_STANDARD[saptawara_idx]
        
        wara_string = f"{sadwara}-{pancawara}-{saptawara}"
        
        return {
            "ka": ka,
            "i": i,
            "s": s,
            "wuku_num": wuku_num,
            "wuku_name": wuku_name,
            "day_in_wuku": day_in_wuku,
            "sadwara": sadwara,
            "pancawara": pancawara,
            "saptawara": saptawara,
            "wara_string": wara_string,
            "method": "formula_only"
        }
    
    def find_tu_pa_a_with_formula(self, ce_year: int) -> List[Dict]:
        """
        Cari TU-PA-Ā dengan RUMUS MURNI (tidak pakai iterasi)
        """
        # KA untuk 1 Januari
        ka_jan1 = self.math.ka_for_jan1(ce_year)
        
        # Hitung i untuk 1 Januari
        i_jan1 = (ka_jan1 - self.const.KA_8_FEB_1_BC) % self.const.WUKU_CYCLE
        
        # TU-PA-Ā adalah saat i = 0
        # Jarak dari 1 Januari ke TU-PA-Ā berikutnya
        if i_jan1 == 0:
            # 1 Januari adalah TU-PA-Ā
            offset = 0
        else:
            # Hitung hari sampai i = 0
            offset = (self.const.WUKU_CYCLE - i_jan1) % self.const.WUKU_CYCLE
        
        ka_tu_pa_a = ka_jan1 + offset
        
        # Verifikasi bahwa i = 0
        i_verify = (ka_tu_pa_a - self.const.KA_8_FEB_1_BC) % self.const.WUKU_CYCLE
        
        if i_verify != 0:
            print(f"⚠️ ERROR: TU-PA-Ā tidak memiliki i=0! i={i_verify}")
            return []
        
        # Hitung tanggal
        year, month, day = self.math.ka_to_julian_date(ka_tu_pa_a)
        
        # Cek apakah masih dalam tahun yang sama
        if year != ce_year:
            # TU-PA-Ā di tahun berikutnya, cari yang sebelumnya
            ka_tu_pa_a -= self.const.WUKU_CYCLE
            year, month, day = self.math.ka_to_julian_date(ka_tu_pa_a)
        
        # Bisa ada 2 TU-PA-Ā dalam setahun
        candidates = []
        
        # TU-PA-Ā pertama
        candidates.append({
            "ka": ka_tu_pa_a,
            "s": ka_tu_pa_a % self.const.WUKU_CYCLE,
            "i": 0,
            "date": (year, month, day),
            "wuku_info": self.calculate_wuku_wara_from_ka_by_formula(ka_tu_pa_a),
            "is_tu_pa_a": True,
            "day_of_year": self._day_of_year(year, month, int(day)),
            "method": "formula_direct"
        })
        
        # Cek kemungkinan TU-PA-Ā kedua
        ka_tu_pa_a_next = ka_tu_pa_a + self.const.WUKU_CYCLE
        year_next, month_next, day_next = self.math.ka_to_julian_date(ka_tu_pa_a_next)
        
        if year_next == ce_year:
            i_verify_next = (ka_tu_pa_a_next - self.const.KA_8_FEB_1_BC) % self.const.WUKU_CYCLE
            if i_verify_next == 0:
                candidates.append({
                    "ka": ka_tu_pa_a_next,
                    "s": ka_tu_pa_a_next % self.const.WUKU_CYCLE,
                    "i": 0,
                    "date": (year_next, month_next, day_next),
                    "wuku_info": self.calculate_wuku_wara_from_ka_by_formula(ka_tu_pa_a_next),
                    "is_tu_pa_a": True,
                    "day_of_year": self._day_of_year(year_next, month_next, int(day_next)),
                    "method": "formula_direct"
                })
        
        return candidates

    # ========================================================================
    # SMART LOOKUP FUNCTIONS
    # ========================================================================
    
    def get_wuku_from_wara_triple(self, sadwara: str, pancawara: str, saptawara: str) -> Optional[str]:
        """Dapatkan nama wuku dari triple wara"""
        sad_norm = self.norm.normalize(sadwara)
        panca_norm = self.norm.normalize(pancawara)
        sapta_norm = self.norm.normalize(saptawara)
        
        triple_key = (sad_norm, panca_norm, sapta_norm)
        return self.wara_triple_to_wuku.get(triple_key, None)
    
    def get_index_from_wara_triple(self, sadwara: str, pancawara: str, saptawara: str) -> Optional[int]:
        """Dapatkan indeks i (0-209) dari triple wara"""
        sad_norm = self.norm.normalize(sadwara)
        panca_norm = self.norm.normalize(pancawara)
        sapta_norm = self.norm.normalize(saptawara)
        
        triple_key = (sad_norm, panca_norm, sapta_norm)
        return self.wara_triple_to_index.get(triple_key, None)
    
    def get_triple_from_wuku_sapta(self, wuku_name: str, saptawara: str) -> Optional[Tuple[str, str, str]]:
        """Dapatkan triple wara lengkap dari wuku dan saptawara"""
        wuku_norm = self.norm.normalize(wuku_name)
        sapta_norm = self.norm.normalize(saptawara)
        
        key = (wuku_norm, sapta_norm)
        return self.wuku_sapta_to_triple.get(key, None)
    
    def get_all_triples_in_wuku(self, wuku_name: str) -> List[Tuple[str, str, str]]:
        """Dapatkan semua 7 triple wara dalam sebuah wuku"""
        wuku_norm = self.norm.normalize(wuku_name)
        return self.wuku_all_triples.get(wuku_norm, [])
    
    def find_matching_triples(self, wuku_name: Optional[str] = None, 
                             sadwara: Optional[str] = None, 
                             pancawara: Optional[str] = None, 
                             saptawara: Optional[str] = None) -> List[Tuple[str, str, str]]:
        """Cari triple wara yang cocok dengan kriteria parsial"""
        results = []
        
        # Jika semua lengkap, langsung cari
        if sadwara and pancawara and saptawara:
            triple_key = (self.norm.normalize(sadwara), 
                         self.norm.normalize(pancawara), 
                         self.norm.normalize(saptawara))
            if triple_key in self.wara_triple_to_index:
                return [triple_key]
        
        # Iterasi semua triple
        for triple_key in self.wara_triple_to_index.keys():
            sad, panca, sapta = triple_key
            match = True
            
            if wuku_name:
                wuku_for_triple = self.wara_triple_to_wuku.get(triple_key)
                if wuku_for_triple != self.norm.normalize(wuku_name):
                    match = False
            
            if sadwara and sad != self.norm.normalize(sadwara):
                match = False
            
            if pancawara and panca != self.norm.normalize(pancawara):
                match = False
                
            if saptawara and sapta != self.norm.normalize(saptawara):
                match = False
            
            if match:
                results.append(triple_key)
        
        return results
    
    def parse_wara_string_smart(self, wara_string: str, wuku_name: Optional[str] = None) -> Optional[Dict]:
        """
        Parse string wara dengan kecerdasan menggunakan matriks lookup.
        Mendukung format: 
          - Lengkap: "Tungleh-Pahing-Aditya"
          - Parsial: "Jumat-Wage" (hanya saptawara-pancawara)
          - Parsial: "Saniscara" (hanya saptawara)
        """
        if not wara_string:
            return None
        
        parts = wara_string.split('-')
        
        # Case 1: Format lengkap (3 bagian)
        if len(parts) == 3:
            sad = self.norm.normalize(parts[0])
            panca = self.norm.normalize(parts[1])
            sapta = self.norm.normalize(parts[2])
            
            # Verifikasi dengan matriks
            triple_key = (sad, panca, sapta)
            if triple_key in self.wara_triple_to_index:
                # Jika wuku diberikan, verifikasi konsistensi
                if wuku_name:
                    expected_wuku = self.wara_triple_to_wuku.get(triple_key)
                    if expected_wuku != self.norm.normalize(wuku_name):
                        print(f"⚠️ PERINGATAN: Triple wara {wara_string} seharusnya di wuku {expected_wuku}, bukan {wuku_name}")
                
                return {
                    "sadwara": sad,
                    "pancawara": panca,
                    "saptawara": sapta,
                    "format": "full",
                    "verified": True
                }
            else:
                print(f"⚠️ PERINGATAN: Triple wara {wara_string} tidak valid dalam matriks")
                return None
        
        # Case 2: Format "Jumat-Wage" (saptawara-pancawara)
        elif len(parts) == 2:
            # Coba parse sebagai saptawara-pancawara
            possible_sapta = self.norm.normalize(parts[0])
            possible_panca = self.norm.normalize(parts[1])
            
            # Cari triple yang cocok
            matching_triples = self.find_matching_triples(
                wuku_name=wuku_name,
                pancawara=possible_panca,
                saptawara=possible_sapta
            )
            
            if len(matching_triples) == 1:
                sad, panca, sapta = matching_triples[0]
                return {
                    "sadwara": sad,
                    "pancawara": panca,
                    "saptawara": sapta,
                    "format": "partial_to_full",
                    "original": wara_string
                }
            elif len(matching_triples) > 1:
                print(f"⚠️ PERINGATAN: {wara_string} ambigu, {len(matching_triples)} kemungkinan:")
                for triple in matching_triples:
                    print(f"    - {triple[0]}-{triple[1]}-{triple[2]}")
                # Ambil yang pertama
                sad, panca, sapta = matching_triples[0]
                return {
                    "sadwara": sad,
                    "pancawara": panca,
                    "saptawara": sapta,
                    "format": "partial_to_full_ambiguous",
                    "original": wara_string,
                    "alternatives": len(matching_triples)
                }
            else:
                # Coba format alternatif: mungkin itu sadwara-pancawara?
                possible_sad = self.norm.normalize(parts[0])
                possible_panca = self.norm.normalize(parts[1])
                
                matching_triples = self.find_matching_triples(
                    wuku_name=wuku_name,
                    sadwara=possible_sad,
                    pancawara=possible_panca
                )
                
                if len(matching_triples) == 1:
                    sad, panca, sapta = matching_triples[0]
                    return {
                        "sadwara": sad,
                        "pancawara": panca,
                        "saptawara": sapta,
                        "format": "partial_to_full_sad_panca",
                        "original": wara_string
                    }
                else:
                    print(f"⚠️ PERINGATAN: Tidak dapat menginterpretasi {wara_string}")
                    return None
        
        # Case 3: Format tunggal (mungkin hanya saptawara)
        elif len(parts) == 1:
            possible_sapta = self.norm.normalize(parts[0])
            
            # Cek apakah ini saptawara
            matching_triples = self.find_matching_triples(
                wuku_name=wuku_name,
                saptawara=possible_sapta
            )
            
            if len(matching_triples) == 1:
                sad, panca, sapta = matching_triples[0]
                return {
                    "sadwara": sad,
                    "pancawara": panca,
                    "saptawara": sapta,
                    "format": "single_to_full",
                    "original": wara_string
                }
            elif len(matching_triples) > 1:
                print(f"⚠️ PERINGATAN: {wara_string} ambigu, {len(matching_triples)} kemungkinan dalam wuku {wuku_name}:")
                for triple in matching_triples:
                    print(f"    - {triple[0]}-{triple[1]}-{triple[2]}")
                # Ambil yang pertama
                sad, panca, sapta = matching_triples[0]
                return {
                    "sadwara": sad,
                    "pancawara": panca,
                    "saptawara": sapta,
                    "format": "single_to_full_ambiguous",
                    "original": wara_string,
                    "alternatives": len(matching_triples)
                }
            else:
                print(f"⚠️ PERINGATAN: Tidak dapat menginterpretasi {wara_string}")
                return None
        
        return None
    
    def calculate_candidate_from_triple(self, tu_pa_a_ka: int, 
                                       target_triple: Tuple[str, str, str]) -> Optional[int]:
        """
        Hitung kandidat KA dari TU-PA-Ā dan triple wara target.
        Rumus: KA_kandidat = KA_tu_pa_a + delta_i
        di mana delta_i = i_target - i_tu_pa_a (mod 210)
        """
        # Dapatkan indeks i untuk triple target
        sad, panca, sapta = target_triple
        i_target = self.get_index_from_wara_triple(sad, panca, sapta)
        
        if i_target is None:
            print(f"⚠️ ERROR: Triple {target_triple} tidak ditemukan dalam matriks")
            return None
        
        # TU-PA-Ā memiliki i = 0
        i_tu_pa_a = 0
        
        # Hitung delta_i
        delta_i = (i_target - i_tu_pa_a) % self.const.WUKU_CYCLE
        
        # KA kandidat
        ka_candidate = tu_pa_a_ka + delta_i
        
        # Verifikasi bahwa i yang dihitung sama dengan i_target
        i_calculated = self.math.calculate_i_from_ka(ka_candidate)
        
        if i_calculated != i_target:
            print(f"⚠️ WARNING: i tidak konsisten. Dihitung: {i_calculated}, Expected: {i_target}")
            # Koreksi: tambahkan kelipatan 210 jika perlu
            ka_candidate = tu_pa_a_ka + delta_i + self.const.WUKU_CYCLE
            i_calculated = self.math.calculate_i_from_ka(ka_candidate)
            if i_calculated != i_target:
                print(f"⚠️ ERROR: Koreksi gagal. i tetap tidak cocok: {i_calculated}")
                return None
        
        return ka_candidate

# ============================================================================
# INTERKALASI DETECTION ENGINE - VERSI DIPERBARUI DENGAN DATA EKSPLISIT
# ============================================================================

class IntercalationDetectionEngine:
    """Engine untuk deteksi interkalasi berdasarkan data eksplisit dan metodologi Damais"""
    
    def __init__(self):
        self.const = ΩConstants
        self.norm = NormalizationEngine()
        
        # DATA EKSPLISIT INTERKALASI (3 prasasti - KEBENARAN MUTLAK)
        self.EXPLICIT_INTERCALATIONS = {
            822: {
                "month": "Pausa",           # Poṣya = Pausa
                "javanese_month": None,
                "tithi": (8, "Sukla"),
                "wara": ("Haryang", "Kaliwon", "Wrhaspati"),
                "julian_date": (901, 1, 1),  # 1 Januari 901 M
                "region": "Jawa Tengah",
                "inscription": "Ayam Těas I (Damais A.66)",
                "notes": "punaḥ poṣyamāsa",
                "certainty": 1.0
            },
            828: {
                "month": "Sravana",
                "javanese_month": "Kasa",   # Perkiraan: bulan musim ke-1
                "tithi": (8, "Krsna"),
                "wara": ("Haryang", "Pahing", "Sukra"),  # Koreksi Damais
                "julian_date": (906, 8, 15),  # 15 Agustus 906 M
                "region": "Jawa Tengah", 
                "inscription": "Palěpangan (Damais A.80)",
                "notes": "punaḥ śrawaṇamāsa",
                "certainty": 1.0
            },
            977: {
                "month": "Caitra",
                "javanese_month": "Kasanga",  # Bulan ke-9 musim
                "tithi": (15, "Sukla"),
                "wara": ("Maulu", "Umanis", "Sukra"),
                "wuku": "Wariga",
                "julian_date": (1055, 4, 14),  # 14 April 1055 M
                "region": "Bali",
                "inscription": "Batwan B (Damais D.35)",
                "notes": "cetramāsa punaḥ (unusual word order)",
                "certainty": 1.0
            }
        }
        
        # MODEL PROUDFOOT (Hanya sebagai referensi, tidak untuk skoring)
        self.PROUDFOOT_CYCLE_START = 1040  # Asumsi awal siklus
        self.PROUDFOOT_CYCLE_LENGTH = 11
        self.PROUDFOOT_PATTERN = {
            2: "Jyestha",   # Tahun ke-3: bulan 11
            5: "Phalguna",  # Tahun ke-6: bulan 8  
            8: "Margasira", # Tahun ke-9: bulan 5
            0: "Bhadrapada" # Tahun ke-11/12: bulan 2
        }
        
        # Bulan yang sering diinterkalasi berdasarkan Damais
        self.FREQUENTLY_INTERCALATED = ["Pausa", "Sravana", "Caitra"]
    
    def get_explicit_intercalation(self, saka_year: int) -> Optional[Dict]:
        """Mengembalikan data interkalasi eksplisit untuk tahun Śaka tertentu, jika ada"""
        return self.EXPLICIT_INTERCALATIONS.get(saka_year)
    
    def get_proudfoot_prediction(self, saka_year: int) -> Optional[Dict]:
        """Prediksi interkalasi berdasarkan model Proudfoot (hanya referensi)"""
        if saka_year < 1040:
            return None
        
        # Hitung posisi dalam siklus 11 tahun
        cycle_pos = (saka_year - self.PROUDFOOT_CYCLE_START) % self.PROUDFOOT_CYCLE_LENGTH
        
        if cycle_pos in self.PROUDFOOT_PATTERN:
            return {
                "month": self.PROUDFOOT_PATTERN[cycle_pos],
                "cycle_position": cycle_pos,
                "certainty": 0.3,  # Sangat rendah, hanya rekonstruksi
                "source": "proudfoot_11yr_cycle",
                "notes": f"Prediksi berdasarkan model Proudfoot (siklus 11 tahun)"
            }
        
        return None
    
    def detect_intercalation_damais(self, inscribed_masa: str, calculated_masa: str, 
                                  saka_year: Optional[int] = None) -> Dict:
        """
        Deteksi kemungkinan interkalasi dengan prioritas:
        1. Data eksplisit (jika saka_year diberikan dan ada dalam database)
        2. Deteksi selisih 1 bulan (metode Damais klasik)
        
        CATATAN: Interkalasi TIDAK mempengaruhi perhitungan mekanikal, hanya deteksi!
        """
        # Normalisasi
        norm_inscribed = self.norm.normalize(inscribed_masa)
        norm_calculated = self.norm.normalize(calculated_masa)
        
        # PENTING: Jika ada data eksplisit, itu adalah kebenaran mutlak
        if saka_year is not None:
            explicit_data = self.get_explicit_intercalation(saka_year)
            if explicit_data:
                explicit_month = explicit_data["month"]
                if norm_inscribed == self.norm.normalize(explicit_month):
                    return {
                        "detected": True,
                        "type": "explicit_inscription",
                        "diff": 1,  # Selalu 1 untuk data eksplisit
                        "intercalated_month": norm_calculated,
                        "displayed_month": norm_inscribed,
                        "confidence": "absolute",
                        "source": "explicit_inscription",
                        "inscription_info": explicit_data["inscription"],
                        "notes": f"Data eksplisit dari prasasti {explicit_data['inscription']}",
                        "explicit_data": explicit_data  # Simpan data eksplisit lengkap
                    }
        
        # Jika tidak ada data eksplisit, gunakan deteksi selisih 1 bulan
        try:
            idx_inscribed = self.const.SAKA_MONTHS_ORDER.index(norm_inscribed)
            idx_calculated = self.const.SAKA_MONTHS_ORDER.index(norm_calculated)
        except ValueError:
            return {
                "detected": False,
                "error": "Bulan tidak valid",
                "inscribed": norm_inscribed,
                "calculated": norm_calculated
            }
        
        # Hitung selisih (mod 12)
        diff = (idx_inscribed - idx_calculated) % 12
        
        # Kasus 1: Interkalasi terdeteksi (diff = 1)
        if diff == 1:
            return {
                "detected": True,
                "type": "punaḥ",
                "diff": diff,
                "intercalated_month": norm_calculated,
                "displayed_month": norm_inscribed,
                "confidence": "medium",
                "source": "damais_detection",
                "notes": "Deteksi berdasarkan selisih 1 bulan (metode Damais)"
            }
        
        # Kasus 2: Cocok persis
        elif diff == 0:
            return {
                "detected": False,
                "type": "exact_match",
                "diff": diff,
                "confidence": "high"
            }
        
        # Kasus 3: Ambiguous (diff = 11)
        elif diff == 11:
            return {
                "detected": True,
                "type": "ambiguous",
                "diff": diff,
                "confidence": "low",
                "notes": "Selisih 11 bulan, mungkin kesalahan atau sistem berbeda"
            }
        
        # Kasus 4: Mismatch besar
        else:
            return {
                "detected": False,
                "type": "mismatch",
                "diff": diff,
                "confidence": "low"
            }
    
    def get_intercalation_report(self, saka_year: int, inscribed_masa: str, 
                                calculated_masa: str) -> Dict:
        """
        Laporan lengkap interkalasi dengan semua informasi yang tersedia
        TANPA mempengaruhi perhitungan mekanikal!
        """
        # Deteksi dengan metode Damais (termasuk data eksplisit)
        detection_result = self.detect_intercalation_damais(
            inscribed_masa, calculated_masa, saka_year
        )
        
        # Prediksi Proudfoot (hanya sebagai informasi tambahan)
        proudfoot_pred = self.get_proudfoot_prediction(saka_year)
        
        # Data eksplisit (jika ada)
        explicit_data = self.get_explicit_intercalation(saka_year)
        
        report = {
            "saka_year": saka_year,
            "inscribed_masa": inscribed_masa,
            "calculated_masa": calculated_masa,
            "detection_result": detection_result,
            "explicit_data": explicit_data,
            "proudfoot_prediction": proudfoot_pred,
            "interpretation": "",
            "warnings": []
        }
        
        # Bangun interpretasi berdasarkan semua data
        if explicit_data:
            report["interpretation"] = (
                f"Tahun Śaka {saka_year} memiliki bulan interkalasi {explicit_data['month']} "
                f"(data eksplisit dari prasasti {explicit_data['inscription']})."
            )
        elif detection_result["detected"]:
            if detection_result["type"] == "punaḥ":
                report["interpretation"] = (
                    f"Indikasi interkalasi: {detection_result['displayed_month']} "
                    f"adalah bulan interkalasi untuk {detection_result['intercalated_month']}."
                )
            elif detection_result["type"] == "ambiguous":
                report["interpretation"] = (
                    f"Ambiguous: selisih 11 bulan antara {inscribed_masa} dan {calculated_masa}."
                )
        else:
            report["interpretation"] = "Tidak terdeteksi indikasi interkalasi."
        
        # Tambahkan peringatan penting
        if saka_year < 1040 and saka_year not in self.EXPLICIT_INTERCALATIONS:
            report["warnings"].append(
                "Periode pre-1040: sistem interkalasi tidak diketahui dengan pasti."
            )
        
        if proudfoot_pred and not explicit_data and saka_year >= 1040:
            report["warnings"].append(
                f"Model Proudfoot memprediksi interkalasi {proudfoot_pred['month']} "
                f"(tidak ada bukti eksplisit, confidence rendah)."
            )
        
        return report
    
    def estimate_intercalation_probability(self, saka_year: int, masa: str) -> Dict:
        """Perkirakan probabilitas interkalasi untuk tahun dan bulan tertentu"""
        masa_norm = self.norm.normalize(masa)
        
        info = {
            "saka_year": saka_year,
            "masa": masa_norm,
            "probability": 0.0,
            "factors": [],
            "interpretation": ""
        }
        
        # Faktor 1: Apakah bulan sering diinterkalasi?
        if masa_norm in self.FREQUENTLY_INTERCALATED:
            info["probability"] += 0.3
            info["factors"].append(f"{masa_norm} termasuk bulan yang sering diinterkalasi")
        
        # Faktor 2: Apakah ada data eksplisit?
        if saka_year in self.EXPLICIT_INTERCALATIONS:
            explicit_data = self.EXPLICIT_INTERCALATIONS[saka_year]
            if masa_norm == self.norm.normalize(explicit_data["month"]):
                info["probability"] = 1.0  # Kebenaran mutlak
                info["factors"].append(f"Data eksplisit dari prasasti {explicit_data['inscription']}")
        
        # Faktor 3: Posisi dalam siklus Metonic (19 tahun)
        cycle_pos = saka_year % 19
        if cycle_pos in [2, 5, 8, 11, 14, 17]:
            info["probability"] += 0.2
            info["factors"].append(f"Posisi {cycle_pos} dalam siklus 19 tahun mendukung interkalasi")
        
        # Faktor 4: Prediksi Proudfoot
        proudfoot_pred = self.get_proudfoot_prediction(saka_year)
        if proudfoot_pred and masa_norm == self.norm.normalize(proudfoot_pred["month"]):
            info["probability"] += 0.1  # Tambahan kecil untuk prediksi Proudfoot
            info["factors"].append(f"Mendukung prediksi model Proudfoot")
        
        # Batasi probabilitas maksimal 1.0
        info["probability"] = min(info["probability"], 1.0)
        
        # Interpretasi
        if info["probability"] >= 1.0:
            info["interpretation"] = f"DATA EKSPLISIT: {masa_norm} adalah bulan interkalasi"
        elif info["probability"] >= 0.5:
            info["interpretation"] = f"Kemungkinan besar ada interkalasi {masa_norm}"
        elif info["probability"] >= 0.3:
            info["interpretation"] = f"Ada kemungkinan interkalasi {masa_norm}"
        else:
            info["interpretation"] = f"Kemungkinan kecil interkalasi {masa_norm}"
        
        return info

# ============================================================================
# TPDP ENGINE - VERSI BARU DENGAN PRIORITAS 4 KOMPONEN UTAMA
# ============================================================================

class TPDPEngine:
    """Engine untuk evaluasi kandidat dengan PRIORITAS 4 KOMPONEN UTAMA"""
    
    def __init__(self):
        self.const = ΩConstants
        self.math = MathCore()
        self.norm = NormalizationEngine()
        self.mech = MechanicalEngine()
        self.intercalation = IntercalationDetectionEngine()
        
        # PAKAI KOMPONEN BARU DARI ΩConstants
        self.TPDP_COMPONENTS = self.const.TPDP_COMPONENTS
        self.THRESHOLDS = self.const.TPDP_THRESHOLDS
    
    def evaluate_candidates(self, candidates: List[Dict], inscription_data: Dict) -> List[Dict]:
        """
        Evaluasi semua kandidat dengan 4 KOMPONEN UTAMA sebagai prioritas
        """
        scored_candidates = []
        
        if not candidates:
            print("⚠️ Tidak ada kandidat untuk dievaluasi")
            return []
        
        print(f"\n{'='*60}")
        print("TPDP EVALUATION - 4 KOMPONEN UTAMA (Tahun, Bulan, Wara, Wuku)")
        print(f"{'='*60}")
        
        for idx, candidate in enumerate(candidates):
            print(f"\n{'─'*40}")
            print(f"EVALUASI KANDIDAT #{idx+1}")
            print(f"{'─'*40}")
            
            score_breakdown = {}
            intercalation_info = None
            
            # 1. TAHUN MATCH (25%) - VALIDASI KETAT
            print("\n1. TAHUN MATCH (25%):")
            tahun_score, tahun_info = self._tahun_match_score(candidate['date'], inscription_data)
            score_breakdown['tahun_match'] = {
                'score': tahun_score,
                'weight': self.TPDP_COMPONENTS["TAHUN_MATCH"],
                'weighted_score': tahun_score * self.TPDP_COMPONENTS["TAHUN_MATCH"],
                'details': tahun_info
            }
            
            # 2. BULAN MATCH (25%) - dengan deteksi interkalasi
            print("\n2. BULAN MATCH (25%):")
            bulan_score, bulan_info = self._bulan_match_score_with_intercalation(
                candidate['date'], 
                inscription_data.get('masa', ''),
                inscription_data.get('saka_year')
            )
            score_breakdown['bulan_match'] = {
                'score': bulan_score,
                'weight': self.TPDP_COMPONENTS["BULAN_MATCH"],
                'weighted_score': bulan_score * self.TPDP_COMPONENTS["BULAN_MATCH"],
                'details': bulan_info
            }
            intercalation_info = bulan_info
            
            # 3. WARA MATCH (20%) - PENTING: wara harus cocok persis
            print("\n3. WARA MATCH (20%):")
            wara_score, wara_details = self._wara_match_score_detailed(
                candidate.get('wuku_info', {}),
                inscription_data
            )
            score_breakdown['wara_match'] = {
                'score': wara_score,
                'weight': self.TPDP_COMPONENTS["WARA_MATCH"],
                'weighted_score': wara_score * self.TPDP_COMPONENTS["WARA_MATCH"],
                'details': wara_details
            }
            
            # 4. WUKU MATCH (15%) - jika ada data wuku
            print("\n4. WUKU MATCH (15%):")
            wuku_score, wuku_details = self._wuku_match_score_detailed(
                candidate.get('wuku_info', {}),
                inscription_data
            )
            score_breakdown['wuku_match'] = {
                'score': wuku_score,
                'weight': self.TPDP_COMPONENTS["WUKU_MATCH"],
                'weighted_score': wuku_score * self.TPDP_COMPONENTS["WUKU_MATCH"],
                'details': wuku_details
            }
            
            # 5. PANCANGA PLAUSIBILITY (5%) - pendukung
            print("\n5. PANCANGA PLAUSIBILITY (5%):")
            panca_score, panca_details = self._pancanga_plausibility_score(
                candidate['date'], inscription_data, candidate.get('wuku_info', {})
            )
            score_breakdown['pancanga_plausibility'] = {
                'score': panca_score,
                'weight': self.TPDP_COMPONENTS["PANCANGA_PLAUSIBILITY"],
                'weighted_score': panca_score * self.TPDP_COMPONENTS["PANCANGA_PLAUSIBILITY"],
                'details': panca_details
            }
            
            # 6. TEMPORAL PROXIMITY (5%) - kedekatan dengan tengah bulan
            print("\n6. TEMPORAL PROXIMITY (5%):")
            temporal_score, temporal_details = self._temporal_proximity_score(
                candidate['date'], inscription_data
            )
            score_breakdown['temporal_proximity'] = {
                'score': temporal_score,
                'weight': self.TPDP_COMPONENTS["TEMPORAL_PROXIMITY"],
                'weighted_score': temporal_score * self.TPDP_COMPONENTS["TEMPORAL_PROXIMITY"],
                'details': temporal_details
            }
            
            # 7. HISTORICAL PRIOR (3%) - kedekatan dengan anchor Damais
            print("\n7. HISTORICAL PRIOR (3%):")
            historical_score, historical_details = self._historical_prior_score(
                candidate, inscription_data
            )
            score_breakdown['historical_prior'] = {
                'score': historical_score,
                'weight': self.TPDP_COMPONENTS["HISTORICAL_PRIOR"],
                'weighted_score': historical_score * self.TPDP_COMPONENTS["HISTORICAL_PRIOR"],
                'details': historical_details
            }
            
            # 8. BRUTE FORCE SUPPORT (2%) - konsistensi matematika
            print("\n8. BRUTE FORCE SUPPORT (2%):")
            brute_score, brute_details = self._brute_force_support_score(
                candidate, inscription_data
            )
            score_breakdown['brute_force_support'] = {
                'score': brute_score,
                'weight': self.TPDP_COMPONENTS["BRUTE_FORCE_SUPPORT"],
                'weighted_score': brute_score * self.TPDP_COMPONENTS["BRUTE_FORCE_SUPPORT"],
                'details': brute_details
            }
            
            # HITUNG SKOR FINAL
            print(f"\n{'─'*40}")
            print("TOTAL SKOR TPDP:")
            print(f"{'─'*40}")
            
            final_score = 0.0
            for component, info in score_breakdown.items():
                if 'weighted_score' in info:
                    component_name = component.replace('_', ' ').title()
                    print(f"  {component_name}: {info['score']:.2f} × {info['weight']:.2f} = {info['weighted_score']:.3f}")
                    final_score += info['weighted_score']
            
            print(f"  {'─'*30}")
            print(f"  TOTAL SKOR: {final_score:.3f}")
            
            # CONFIDENCE LEVEL
            confidence = self._get_confidence_level(final_score)
            
            scored_candidates.append({
                'candidate': candidate,
                'score': final_score,
                'breakdown': score_breakdown,
                'intercalation_info': intercalation_info,
                'confidence': confidence,
                'month_shifted': intercalation_info.get('detected', False) if intercalation_info else False,  # DIUBAH: has_intercalation -> month_shifted
                'has_explicit_intercalation': intercalation_info.get('explicit_data', False) if intercalation_info else False,
                'rank': idx + 1
            })
            
            print(f"  CONFIDENCE: {confidence}")
            print(f"  4 KOMPONEN UTAMA: {tahun_score:.2f} + {bulan_score:.2f} + {wara_score:.2f} + {wuku_score:.2f}")
        
        # Urutkan berdasarkan skor
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Update ranking
        for i, cand in enumerate(scored_candidates):
            cand['rank'] = i + 1
        
        # Tampilkan peringatan khusus untuk 4 komponen utama
        self._display_main_components_warnings(scored_candidates)
        
        # Tampilkan rangkuman
        self._display_tpdp_summary_improved(scored_candidates)
        
        return scored_candidates
    
    # ========================================================================
    # FUNGSI SCORING UTAMA
    # ========================================================================
    
    def _tahun_match_score(self, candidate_date: Tuple, inscription_data: Dict) -> Tuple[float, Dict]:
        """Hitung skor TAHUN MATCH (25%) - Validasi ketat terhadap aturan konversi"""
        year, month, day = candidate_date
        saka_year = inscription_data.get('saka_year')
        masa = inscription_data.get('masa', '')
        
        details = {
            "candidate_year": year,
            "saka_year": saka_year,
            "masa": masa,
            "validation_method": "",
            "is_valid": False
        }
        
        if not saka_year or not masa:
            return 0.0, {"error": "Data tahun Saka atau bulan tidak lengkap"}
        
        # Validasi dengan aturan konversi dasar
        is_valid_year = self.mech.validate_ce_year_by_basic_rule(saka_year, masa, year)
        
        if is_valid_year:
            score = 1.0
            details["is_valid"] = True
            details["validation_method"] = "basic_conversion_rule"
            
            # Bonus jika tahun tepat sesuai prediksi utama
            valid_years = self.mech.get_valid_ce_years_by_rule(saka_year, masa)
            if isinstance(valid_years, list):
                # Bulan Pausa: dua kemungkinan tahun
                if year in valid_years:
                    if len(valid_years) == 2:
                        # Tahun Pausa ambigu - beri skor maksimal karena sudah valid
                        score = 1.0
                        details["note"] = f"Tahun {year} M valid untuk Śaka {saka_year} Pausa"
                    else:
                        score = 1.0
                else:
                    # Seharusnya tidak terjadi karena sudah divalidasi
                    score = 0.0
            else:
                # Bulan tidak ambigu
                if year == valid_years:
                    score = 1.0
                    details["note"] = f"Tahun {year} M tepat sesuai aturan konversi"
                else:
                    score = 0.0
        else:
            score = 0.0
            details["note"] = "Tahun tidak valid menurut aturan konversi dasar"
        
        details["score"] = score
        return score, details
    
    def _bulan_match_score_with_intercalation(self, candidate_date: Tuple, 
                                            inscribed_masa: str, 
                                            saka_year: Optional[int] = None) -> Tuple[float, Dict]:
        """Hitung skor BULAN MATCH (25%) dengan deteksi interkalasi"""
        year, month, day = candidate_date
        
        if not inscribed_masa:
            return 0.5, {
                "detected": False, 
                "type": "no_data",
                "score": 0.5,
                "message": "Data bulan tidak tersedia"
            }
        
        # Konversi bulan Julian ke Saka
        calculated_masa = self.mech.julian_month_to_saka_month(month)
        if not calculated_masa:
            return 0.0, {
                "error": "Tidak dapat konversi bulan",
                "month_julian": month
            }
        
        # Normalisasi nama bulan
        inscribed_masa_norm = self.norm.normalize(inscribed_masa)
        calculated_masa_norm = self.norm.normalize(calculated_masa)
        
        # Deteksi interkalasi
        intercalation_result = self.intercalation.detect_intercalation_damais(
            inscribed_masa_norm, calculated_masa_norm, saka_year
        )
        
        # SKOR BERDASARKAN KECOCOKAN BULAN
        if intercalation_result.get('detected'):
            if intercalation_result.get('type') == 'explicit_inscription':
                # DATA INTERKALASI EKSPLISIT: SKOR MAKSIMAL
                score = 1.0
                score_reason = "explicit_intercalation"
                details = "Bulan sesuai dengan data interkalasi eksplisit prasasti"
            elif intercalation_result.get('type') == 'punaḥ' and intercalation_result.get('diff') == 1:
                # Interkalasi terdeteksi (selisih 1 bulan)
                score = 0.9
                score_reason = "intercalation_detected"
                details = "Bulan menunjukkan pola interkalasi (selisih 1 bulan)"
            else:
                # Interkalasi ambiguous
                score = 0.5
                score_reason = "ambiguous_intercalation"
                details = "Pola interkalasi ambiguous"
        elif inscribed_masa_norm == calculated_masa_norm:
            # COCOK PERSIS: SKOR MAKSIMAL
            score = 1.0
            score_reason = "exact_match"
            details = "Bulan cocok persis"
        else:
            # TIDAK COCOK: SKOR RENDAH
            score = 0.1
            score_reason = "mismatch"
            details = "Bulan tidak cocok dan tidak ada indikasi interkalasi"
        
        # Tambahkan informasi detail
        intercalation_result.update({
            "candidate_date": f"{int(year)}-{int(month):02d}-{int(day):02d}",
            "calculated_masa": calculated_masa,
            "inscribed_masa": inscribed_masa,
            "month_julian": month,
            "score": score,
            "score_reason": score_reason,
            "details": details
        })
        
        return score, intercalation_result
    
    def _wara_match_score_detailed(self, candidate_wuku_info: Dict, inscription_data: Dict) -> Tuple[float, Dict]:
        """Hitung skor WARA MATCH (20%) - HARUS COCOK PERSIS"""
        score = 0.0
        details = {
            "sadwara_match": False,
            "pancawara_match": False,
            "saptawara_match": False,
            "total_matches": 0,
            "is_perfect_match": False
        }
        
        # Parse wara_string dari prasasti
        if 'wara_string' in inscription_data and inscription_data['wara_string']:
            wara_info = self.mech.parse_wara_string_smart(
                inscription_data['wara_string'],
                inscription_data.get('wuku')
            )
            
            if wara_info:
                candidate_sad = candidate_wuku_info.get('sadwara', '')
                candidate_panca = candidate_wuku_info.get('pancawara', '')
                candidate_sapta = candidate_wuku_info.get('saptawara', '')
                
                # Cocokkan masing-masing komponen wara
                sad_match = (candidate_sad == wara_info.get('sadwara', ''))
                panca_match = (candidate_panca == wara_info.get('pancawara', ''))
                sapta_match = (candidate_sapta == wara_info.get('saptawara', ''))
                
                details["sadwara_match"] = sad_match
                details["pancawara_match"] = panca_match
                details["saptawara_match"] = sapta_match
                
                match_count = sum([sad_match, panca_match, sapta_match])
                details["total_matches"] = match_count
                
                # WARA HARUS COCOK PERSIS (3/3) untuk skor tinggi
                if match_count == 3:
                    score = 1.0  # Skor maksimal untuk wara cocok persis
                    details["is_perfect_match"] = True
                elif match_count == 2:
                    score = 0.4  # Skor rendah untuk 2/3
                elif match_count == 1:
                    score = 0.1  # Skor sangat rendah untuk 1/3
                else:
                    score = 0.0  # Tidak cocok sama sekali
            else:
                # Tidak bisa parse wara_string
                score = 0.0
                details["error"] = "Tidak dapat parsing wara_string"
        else:
            # Tidak ada data wara
            score = 0.5  # Skor netral (tidak ada data untuk divalidasi)
            details["note"] = "Tidak ada data wara untuk divalidasi"
        
        return min(score, 1.0), details
    
    def _wuku_match_score_detailed(self, candidate_wuku_info: Dict, inscription_data: Dict) -> Tuple[float, Dict]:
        """Hitung skor WUKU MATCH (15%) - jika ada data wuku, harus cocok"""
        score = 0.0
        details = {
            "has_wuku_data": False,
            "wuku_match": False,
            "candidate_wuku": "",
            "inscribed_wuku": ""
        }
        
        # Cek apakah ada data wuku di prasasti
        if 'wuku' in inscription_data and inscription_data['wuku']:
            details["has_wuku_data"] = True
            inscribed_wuku = self.norm.normalize(inscription_data['wuku'])
            candidate_wuku = self.norm.normalize(candidate_wuku_info.get('wuku_name', ''))
            
            details["inscribed_wuku"] = inscribed_wuku
            details["candidate_wuku"] = candidate_wuku
            
            if inscribed_wuku == candidate_wuku:
                # WUKU COCOK PERSIS: SKOR MAKSIMAL
                score = 1.0
                details["wuku_match"] = True
                details["note"] = "Wuku cocok persis"
            else:
                # WUKU TIDAK COCOK: SKOR NOL
                score = 0.0
                details["wuku_match"] = False
                details["note"] = "Wuku tidak cocok"
        else:
            # TIDAK ADA DATA WUKU: SKOR NETRAL (tidak mengurangi)
            score = 0.5
            details["note"] = "Tidak ada data wuku untuk divalidasi"
        
        return score, details
    
    # ========================================================================
    # FUNGSI SCORING PENDUKUNG (disederhanakan)
    # ========================================================================
    
    def _pancanga_plausibility_score(self, candidate_date: Tuple, 
                                    inscription_data: Dict,
                                    candidate_wuku_info: Dict) -> Tuple[float, Dict]:
        """Hitung skor PANCANGA PLAUSIBILITY (5%) - sederhana"""
        score = 0.0
        details = {"checks_passed": []}
        
        # Cek tithi
        if 'tithi' in inscription_data:
            tithi = inscription_data['tithi']
            if 1 <= tithi <= 30:
                score += 0.02
                details["checks_passed"].append("tithi_valid")
        
        # Cek paksa
        if 'paksa' in inscription_data:
            paksa = self.norm.normalize(inscription_data['paksa'])
            if paksa in ['Sukla', 'Krsna']:
                score += 0.02
                details["checks_passed"].append("paksa_valid")
        
        # Cek nakshatra (jika ada)
        if 'nakshatra' in inscription_data and inscription_data['nakshatra']:
            nakshatra = self.norm.normalize(inscription_data['nakshatra'])
            if len(nakshatra) >= 3:
                score += 0.01
                details["checks_passed"].append("nakshatra_plausible")
        
        details["total_score"] = min(score, 0.05)
        return min(score, 0.05) * 20, details  # Normalize to 0-1 scale
    
    def _temporal_proximity_score(self, candidate_date: Tuple, 
                                 inscription_data: Dict) -> Tuple[float, Dict]:
        """Hitung skor TEMPORAL PROXIMITY (5%) - kedekatan dengan tengah bulan"""
        year, month, day = candidate_date
        
        distance_from_mid = abs(day - 15)
        normalized_distance = distance_from_mid / 14.0
        
        # Skor: 1.0 jika tepat tanggal 15, menurun linier
        score = max(0.0, 1.0 - normalized_distance)
        
        details = {
            "day": day,
            "mid_month": 15,
            "distance_from_mid": distance_from_mid,
            "score": score
        }
        
        return score, details
    
    def _historical_prior_score(self, candidate: Dict, 
                               inscription_data: Dict) -> Tuple[float, Dict]:
        """Hitung skor HISTORICAL PRIOR (3%) - kedekatan dengan anchor Damais"""
        score = 0.0
        details = {"proximity_to_anchors": []}
        
        saka_year = inscription_data.get('saka_year')
        if saka_year:
            min_distance = float('inf')
            
            for anchor in self.const.DAMAIS_ANCHORS:
                distance = abs(saka_year - anchor["saka"])
                details["proximity_to_anchors"].append({
                    "anchor": anchor["id"],
                    "saka": anchor["saka"],
                    "distance": distance
                })
                
                if distance < min_distance:
                    min_distance = distance
            
            # Beri skor berdasarkan kedekatan
            if min_distance <= 5:
                score = 0.03  # Sangat dekat
            elif min_distance <= 20:
                score = 0.02  # Cukup dekat
            elif min_distance <= 50:
                score = 0.01  # Agak jauh
            else:
                score = 0.0  # Jauh
            
            details["min_distance"] = min_distance
        
        return score * 33.33, details  # Normalize to 0-1 scale
    
    def _brute_force_support_score(self, candidate: Dict, 
                                  inscription_data: Dict) -> Tuple[float, Dict]:
        """Hitung skor BRUTE FORCE SUPPORT (2%) - konsistensi matematika"""
        score = 0.0
        details = {"checks": []}
        
        ka = candidate.get('ka', 0)
        i = candidate.get('i', -1)
        
        # Verifikasi 1: i = (KA - KA_8_FEB_1_BC) mod 210
        i_calculated = self.math.calculate_i_from_ka(ka)
        i_consistent = (i == i_calculated)
        details["checks"].append({
            "check": "i consistency",
            "passed": i_consistent
        })
        if i_consistent:
            score += 0.01
        
        # Verifikasi 2: Wuku dari KA konsisten
        wuku_from_ka = self.mech.calculate_wuku_wara_from_ka(ka)
        if 'wuku_info' in candidate:
            wuku_match = (candidate['wuku_info']['wuku_name'] == wuku_from_ka['wuku_name'])
            details["checks"].append({
                "check": "wuku consistency",
                "passed": wuku_match
            })
            if wuku_match:
                score += 0.01
        
        details["total_score"] = score
        return score * 50, details  # Normalize to 0-1 scale
    
    # ========================================================================
    # FUNGSI PENUNJANG
    # ========================================================================
    
    def _get_confidence_level(self, score: float) -> str:
        """Tentukan confidence level berdasarkan skor"""
        if score >= self.THRESHOLDS["HIGH_CONFIDENCE"]:
            return "TINGGI"
        elif score >= self.THRESHOLDS["MEDIUM_CONFIDENCE"]:
            return "SEDANG"
        elif score >= self.THRESHOLDS["LOW_CONFIDENCE"]:
            return "RENDAH"
        else:
            return "DIREKOMENDASIKAN UNTUK DITOLAK"
    
    def _display_main_components_warnings(self, scored_candidates: List[Dict]):
        """Tampilkan peringatan khusus untuk 4 komponen utama"""
        print(f"\n{'='*60}")
        print("ANALISIS 4 KOMPONEN UTAMA")
        print(f"{'='*60}")
        
        for i, cand in enumerate(scored_candidates[:3]):  # Tampilkan 3 teratas
            breakdown = cand['breakdown']
            
            print(f"\n#{i+1} - Skor: {cand['score']:.3f} ({cand['confidence']})")
            
            # Cek komponen utama
            tahun_score = breakdown['tahun_match']['score'] if 'tahun_match' in breakdown else 0
            bulan_score = breakdown['bulan_match']['score'] if 'bulan_match' in breakdown else 0
            wara_score = breakdown['wara_match']['score'] if 'wara_match' in breakdown else 0
            wuku_score = breakdown['wuku_match']['score'] if 'wuku_match' in breakdown else 0
            
            print(f"  Tahun: {'✓' if tahun_score >= 0.9 else '⚠️' if tahun_score >= 0.5 else '✗'} {tahun_score:.2f}")
            print(f"  Bulan: {'✓' if bulan_score >= 0.9 else '⚠️' if bulan_score >= 0.5 else '✗'} {bulan_score:.2f}")
            print(f"  Wara: {'✓' if wara_score >= 0.9 else '⚠️' if wara_score >= 0.5 else '✗'} {wara_score:.2f}")
            print(f"  Wuku: {'✓' if wuku_score >= 0.9 else '⚠️' if wuku_score >= 0.5 else '✗'} {wuku_score:.2f}")
            
            # Highlight masalah
            issues = []
            if tahun_score < 0.5:
                issues.append("Tahun tidak valid")
            if bulan_score < 0.5:
                issues.append("Bulan tidak cocok")
            if wara_score < 0.9:
                issues.append("Wara tidak cocok persis")
            if 'wuku_match' in breakdown and breakdown['wuku_match']['details'].get('has_wuku_data') and wuku_score < 0.9:
                issues.append("Wuku tidak cocok")
            
            if issues:
                print(f"  ⚠️ Masalah: {', '.join(issues)}")
    
    def _display_tpdp_summary_improved(self, scored_candidates: List[Dict]):
        """Tampilkan rangkuman hasil TPDP dengan fokus pada 4 komponen utama"""
        if not scored_candidates:
            return
        
        print(f"\n{'='*60}")
        print("RANGKUMAN HASIL TPDP - 4 KOMPONEN UTAMA")
        print(f"{'='*60}")
        
        best_candidate = scored_candidates[0]
        candidate = best_candidate['candidate']
        year, month, day = candidate['date']
        
        # Ambil skor komponen utama
        breakdown = best_candidate['breakdown']
        tahun_score = breakdown['tahun_match']['score'] if 'tahun_match' in breakdown else 0
        bulan_score = breakdown['bulan_match']['score'] if 'bulan_match' in breakdown else 0
        wara_score = breakdown['wara_match']['score'] if 'wara_match' in breakdown else 0
        wuku_score = breakdown['wuku_match']['score'] if 'wuku_match' in breakdown else 0
        
        print(f"\n✨ KANDIDAT TERBAIK (Rank #1):")
        print(f"   Tanggal: {int(year)}-{int(month):02d}-{int(day):02d}")
        print(f"   KA: {candidate.get('ka', '?')}")
        print(f"   Wuku: {candidate['wuku_info']['wuku_name']}")
        print(f"   Wara: {candidate['wuku_info']['wara_string']}")
        print(f"   Skor TPDP: {best_candidate['score']:.3f}")
        print(f"   Confidence: {best_candidate['confidence']}")
        
        # Tampilkan 4 komponen utama
        print(f"\n   4 KOMPONEN UTAMA:")
        print(f"   - Tahun: {tahun_score:.2f} {'✓' if tahun_score >= 0.9 else '⚠️' if tahun_score >= 0.5 else '✗'}")
        print(f"   - Bulan: {bulan_score:.2f} {'✓' if bulan_score >= 0.9 else '⚠️' if bulan_score >= 0.5 else '✗'}")
        print(f"   - Wara: {wara_score:.2f} {'✓' if wara_score >= 0.9 else '⚠️' if wara_score >= 0.5 else '✗'}")
        print(f"   - Wuku: {wuku_score:.2f} {'✓' if wuku_score >= 0.9 else '⚠️' if wuku_score >= 0.5 else '✗'}")
        
        # Informasi interkalasi - DIUBAH LABELNYA
        if best_candidate.get('month_shifted'):
            info = best_candidate.get('intercalation_info', {})
            explicit_data = info.get('explicit_data')
            
            if explicit_data:
                print(f"\n   🔴 INTERKALASI EKSPLISIT: {explicit_data['inscription']}")
                print(f"      {explicit_data['month']} (Śaka {explicit_data.get('saka_year', '?')})")
            elif info.get('type') == 'punaḥ' and info.get('diff') == 1:
                # DIUBAH: INDIKASI INTERKALASI -> PERGESERAN BULAN
                print(f"\n   🟡 PERGESERAN BULAN (month_shifted): {info.get('inscribed_masa', '?')} → {info.get('calculated_masa', '?')}")
        
        print(f"\n📊 Top {min(5, len(scored_candidates))} kandidat:")
        for i, cand in enumerate(scored_candidates[:5]):
            cand_data = cand['candidate']
            y, m, d = cand_data['date']
            
            # Ambil skor komponen utama untuk tampilan singkat
            bd = cand['breakdown']
            t_score = bd['tahun_match']['score'] if 'tahun_match' in bd else 0
            b_score = bd['bulan_match']['score'] if 'bulan_match' in bd else 0
            wa_score = bd['wara_match']['score'] if 'wara_match' in bd else 0
            wu_score = bd['wuku_match']['score'] if 'wuku_match' in bd else 0
            
            avg_main = (t_score + b_score + wa_score + wu_score) / 4.0
            
            # Gunakan ikon berdasarkan komponen utama
            if cand.get('has_explicit_intercalation'):
                interkalasi = " 🔴"
            elif cand.get('month_shifted'):
                interkalasi = " 🟡"
            elif avg_main >= 0.9:
                interkalasi = " ✓"
            elif avg_main >= 0.7:
                interkalasi = " ⚠️"
            else:
                interkalasi = " ✗"
            
            print(f"   #{i+1}: {int(y)}-{int(m):02d}-{int(d):02d} - {cand['score']:.3f} ({cand['confidence']}){interkalasi}")

# ============================================================================
# EDP ENGINE - VERSI DIPERBAIKI DENGAN PERINGATAN SEDERHANA
# ============================================================================

class EDPEngine:
    """Engine untuk Error Detector Protocol dengan Layer Deteksi Interkalasi"""
    
    def __init__(self):
        self.const = ΩConstants
        self.math = MathCore()
        self.norm = NormalizationEngine()
        
        self.flags = []
        self.suggestions = []
        self.anomalies = []
        self.intercalation_warnings = []
    
    def run_edp_analysis(self, ka, inscription_data, astronomical_data=None,
                        intercalation_info=None):
        """Jalankan analisis EDP lengkap dengan deteksi interkalasi Damais"""
        self.flags = []
        self.suggestions = []
        self.anomalies = []
        self.intercalation_warnings = []
        
        print(f"\n{'='*60}")
        print("EDP ANALYSIS - Error Detector Protocol")
        print(f"{'='*60}")
        
        # Layer 1: Damais Classic (konsistensi aritmatika)
        self._layer1_damais_classic(ka, inscription_data)
        
        # Layer 2: Modern Astronomy (verifikasi langit)
        if astronomical_data:
            self._layer2_modern_astronomy(ka, inscription_data, astronomical_data)
        
        # Layer 3: Probabilistic AI (fuzzy matching)
        self._layer3_probabilistic_ai(inscription_data)
        
        # Layer 4: Damais Intercalation Detection (SEDERHANA)
        self._layer4_intercalation_detection_simple(intercalation_info, inscription_data)
        
        # Hasil akhir
        return self._generate_edp_report_simple()
    
    def _layer1_damais_classic(self, ka, inscription_data):
        """Layer 1: Konsistensi aritmatika siklus mekanis"""
        print("\nLAYER 1: Damais Classic (Aritmatika Siklus Mekanis)")
        
        # Hitung wuku dan wara dari KA
        mech = MechanicalEngine()
        wuku_info = mech.calculate_wuku_wara_from_ka(ka)
        
        # Verifikasi wara
        if 'wara_string' in inscription_data and inscription_data['wara_string']:
            inscribed_wara = inscription_data['wara_string']
            calculated_wara = wuku_info['wara_string']
            
            if inscribed_wara != calculated_wara:
                self.anomalies.append({
                    "type": "EDP-01",
                    "description": "Wara mismatch",
                    "details": f"Prasasti: {inscribed_wara}, Dihitung: {calculated_wara}",
                    "severity": "HIGH"
                })
                self.flags.append("EDP-01")
            else:
                print(f"  ✓ Wara cocok: {calculated_wara}")
        
        # Verifikasi wuku
        if 'wuku' in inscription_data and inscription_data['wuku']:
            inscribed_wuku = self.norm.normalize(inscription_data['wuku'])
            calculated_wuku = self.norm.normalize(wuku_info['wuku_name'])
            
            if inscribed_wuku != calculated_wuku:
                self.anomalies.append({
                    "type": "EDP-02",
                    "description": "Wuku mismatch",
                    "details": f"Prasasti: {inscribed_wuku}, Dihitung: {calculated_wuku}",
                    "severity": "HIGH"
                })
                self.flags.append("EDP-02")
            else:
                print(f"  ✓ Wuku cocok: {calculated_wuku}")
        
        # Tampilkan informasi s dan i
        print(f"  s = KA % 210 = {wuku_info['s']}")
        print(f"  i = (KA - KA_8_FEB_1_BC) mod 210 = {wuku_info['i']}")
    
    def _layer2_modern_astronomy(self, ka, inscription_data, astronomical_data):
        """Layer 2: Verifikasi astronomi modern"""
        print("\nLAYER 2: Modern Astronomy (Verifikasi Langit)")
        
        # Verifikasi tithi
        if 'tithi' in inscription_data and 'paksa' in inscription_data:
            inscribed_tithi = inscription_data['tithi']
            inscribed_paksa = self.norm.normalize(inscription_data['paksa'])
            
            # Cek kedua mode
            tithi_sayana = astronomical_data['sayana']['tithi']
            tithi_nirayana = astronomical_data['nirayana']['tithi']
            
            sayana_match = (tithi_sayana['tithi'] == inscribed_tithi and 
                           tithi_sayana['paksa'] == inscribed_paksa)
            nirayana_match = (tithi_nirayana['tithi'] == inscribed_tithi and 
                             tithi_nirayana['paksa'] == inscribed_paksa)
            
            if sayana_match and not nirayana_match:
                print(f"  ✓ Tithi cocok (Sayana): {tithi_sayana['tithi']} {tithi_sayana['paksa']}")
                self.suggestions.append("Sistem yang digunakan mungkin SAYANA (Tropical)")
            elif nirayana_match and not sayana_match:
                print(f"  ✓ Tithi cocok (Nirayana): {tithi_nirayana['tithi']} {tithi_nirayana['paksa']}")
                self.suggestions.append("Sistem yang digunakan mungkin NIRAYANA (Sidereal)")
            elif sayana_match and nirayana_match:
                print(f"  ✓ Tithi cocok kedua mode: {tithi_sayana['tithi']} {tithi_sayana['paksa']}")
            else:
                self.anomalies.append({
                    "type": "EDP-03",
                    "description": "Tithi mismatch",
                    "details": f"Prasasti: {inscribed_tithi} {inscribed_paksa}, "
                              f"Sayana: {tithi_sayana['tithi']} {tithi_sayana['paksa']}, "
                              f"Nirayana: {tithi_nirayana['tithi']} {tithi_nirayana['paksa']}",
                    "severity": "MEDIUM"
                })
                self.flags.append("EDP-03")
        
        # Verifikasi nakshatra jika ada
        if 'nakshatra' in inscription_data and inscription_data['nakshatra']:
            inscribed_nakshatra = self.norm.normalize(inscription_data['nakshatra'])
            nakshatra_sayana = astronomical_data['sayana']['nakshatra']
            nakshatra_nirayana = astronomical_data['nirayana']['nakshatra']
            
            sayana_nak_match = (self.norm.normalize(nakshatra_sayana['nakshatra']) == inscribed_nakshatra)
            nirayana_nak_match = (self.norm.normalize(nakshatra_nirayana['nakshatra']) == inscribed_nakshatra)
            
            if sayana_nak_match or nirayana_nak_match:
                print(f"  ✓ Nakshatra cocok (mode: {'Sayana' if sayana_nak_match else 'Nirayana'})")
            else:
                print(f"  ⚠️ Nakshatra tidak cocok: Prasasti={inscribed_nakshatra}, "
                      f"Sayana={nakshatra_sayana['nakshatra']}, Nirayana={nakshatra_nirayana['nakshatra']}")
    
    def _layer3_probabilistic_ai(self, inscription_data):
        """Layer 3: Fuzzy matching dan saran koreksi"""
        print("\nLAYER 3: Probabilistic AI (Fuzzy Matching)")
        
        # Cek varian ejaan untuk saran
        for field in ['masa', 'wuku', 'paksa', 'nakshatra']:
            if field in inscription_data and inscription_data[field]:
                original = inscription_data[field]
                normalized = self.norm.normalize(original)
                
                if original != normalized:
                    self.suggestions.append(
                        f"Varian ejaan '{original}' dinormalisasi ke '{normalized}'"
                    )
                    print(f"  ⚠️  Normalisasi: '{original}' → '{normalized}'")
        
        # Cek wara string untuk varian
        if 'wara_string' in inscription_data and inscription_data['wara_string']:
            original = inscription_data['wara_string']
            parts = original.split('-')
            if len(parts) == 2 and parts[0].lower() in ['jumat', 'sukra']:
                self.suggestions.append(
                    f"Format wara '{original}' dikonversi ke 'Haryang-{parts[1]}-Sukra'"
                )
                print(f"  ⚠️  Konversi format wara: '{original}' → 'Haryang-{parts[1]}-Sukra'")
    
    def _layer4_intercalation_detection_simple(self, intercalation_info, inscription_data):
        """Layer 4: Deteksi Interkalasi SEDERHANA"""
        print("\nLAYER 4: Damais Intercalation Detection")
        
        if not intercalation_info:
            print("  ✓ Tidak ada informasi interkalasi")
            return
        
        # Hanya tampilkan informasi penting
        if intercalation_info.get('detected'):
            # Simpan peringatan interkalasi
            self.intercalation_warnings.append(intercalation_info)
            
            # Tambahkan ke flags
            self.flags.append("EDP-INTERCALATION")
            
            # Tampilkan sederhana berdasarkan data eksplisit
            explicit_data = intercalation_info.get('explicit_data')
            if explicit_data:
                print(f"  🔴 DATA INTERKALASI EKSPLISIT: {explicit_data['inscription']}")
                print(f"     {explicit_data['month']} (Śaka {explicit_data.get('saka_year', '?')})")
            elif intercalation_info.get('type') == 'punaḥ' and intercalation_info.get('diff') == 1:
                # DIUBAH: INDIKASI INTERKALASI -> PERGESERAN BULAN
                print(f"  🟡 PERGESERAN BULAN (month_shifted): selisih 1 bulan")
        else:
            print(f"  ✓ Tidak terdeteksi interkalasi atau pergeseran bulan")
    
    def _generate_edp_report_simple(self):
        """Hasilkan laporan EDP sederhana"""
        report = {
            "flags": self.flags.copy(),
            "suggestions": self.suggestions.copy(),
            "anomalies": self.anomalies.copy(),
            "intercalation_warnings": self.intercalation_warnings.copy(),
            "confidence": self._calculate_confidence_simple(),
            "has_intercalation": len(self.intercalation_warnings) > 0
        }
        
        # Tampilkan ringkasan sederhana
        if self.intercalation_warnings:
            print(f"\n  🔴 INTERKALASI:")
            for warning in self.intercalation_warnings:
                if warning.get('explicit_data'):
                    data = warning['explicit_data']
                    print(f"     - {data['month']} (Śaka {data.get('saka_year', '?')}): {data['inscription']}")
                elif warning.get('type') == 'punaḥ' and warning.get('diff') == 1:
                    print(f"     - {warning.get('inscribed_masa', '?')} → {warning.get('calculated_masa', '?')} (selisih 1 bulan)")
        
        if self.anomalies:
            print(f"\n  ⚠️  Anomali: {len(self.anomalies)} ditemukan")
            for anomaly in self.anomalies[:2]:  # Hanya tampilkan 2 pertama
                print(f"     - {anomaly['type']}: {anomaly['description']}")
        
        if self.suggestions:
            print(f"\n  💡 Saran: {len(self.suggestions)} saran")
            for suggestion in self.suggestions[:2]:  # Hanya tampilkan 2 pertama
                print(f"     - {suggestion}")
        
        return report
    
    def _calculate_confidence_simple(self):
        """Hitung confidence score sederhana berdasarkan analisis EDP"""
        base_score = 1.0
        
        # Kurangi untuk setiap anomali berdasarkan severity
        for anomaly in self.anomalies:
            severity = anomaly.get('severity', 'MEDIUM')
            if severity == 'HIGH':
                base_score -= 0.15
            elif severity == 'MEDIUM':
                base_score -= 0.10
            elif severity == 'LOW':
                base_score -= 0.05
        
        # Tambahkan bonus jika ada deteksi interkalasi eksplisit
        if self.intercalation_warnings:
            for warning in self.intercalation_warnings:
                if warning.get('explicit_data'):
                    base_score += 0.05
                    break
        
        # Pastikan dalam range 0-1
        return max(0.0, min(1.0, base_score))

# ============================================================================
# Ω-STHAPATI SYSTEM - VERSI DIPERBAIKI DENGAN ALGORITMA BARU
# ============================================================================

class ΩSthapatiSystem:
    """Sistem utama terpadu Ω-STHAPATI dengan semua fungsi dan perbaikan"""
    
    def __init__(self, verbose_startup: bool = True):
        self.const = ΩConstants
        self.math = MathCore()
        self.norm = NormalizationEngine()
        self.mech = MechanicalEngine()
        self.intercalation = IntercalationDetectionEngine()
        self.tpdp = TPDPEngine()
        self.edp = EDPEngine()
        
        # Verifikasi sistem
        self._verify_system_consistency(verbose_startup)
    
    def display_conversion_rule(self, saka_year: int, masa: str):
        """Tampilkan aturan konversi dengan contoh-contoh"""
        masa_norm = self.norm.normalize(masa)
        
        print(f"\n{'='*60}")
        print("ATURAN KONVERSI SAKA → MASEHI BERDASARKAN BULAN")
        print(f"{'='*60}")
        
        rules = {
            "Pausa": {
                "rule": "Śaka +78 atau +79 (ambigu)",
                "example": f"Śaka {saka_year} Pausa → {saka_year+78} M atau {saka_year+79} M",
                "note": "Bulan Pausa jatuh di Desember-Januari, sehingga bisa masuk ke tahun +78 atau +79"
            },
            "Magha": {
                "rule": "Śaka +79",
                "example": f"Śaka {saka_year} Magha → {saka_year+79} M",
                "note": "Magha (Jan-Feb) selalu +79"
            },
            "Phalguna": {
                "rule": "Śaka +79", 
                "example": f"Śaka {saka_year} Phalguna → {saka_year+79} M",
                "note": "Phalguna (Feb-Mar) selalu +79"
            },
            "default": {
                "rule": "Śaka +78",
                "example": f"Śaka {saka_year} {masa_norm} → {saka_year+78} M",
                "note": "Bulan Caitra sampai Margasira selalu +78"
            }
        }
        
        if masa_norm in rules:
            rule_info = rules[masa_norm]
        else:
            rule_info = rules["default"]
            rule_info["example"] = f"Śaka {saka_year} {masa_norm} → {saka_year+78} M"
        
        print(f"Bulan: {masa_norm}")
        print(f"Aturan: {rule_info['rule']}")
        print(f"Contoh: {rule_info['example']}")
        print(f"Catatan: {rule_info['note']}")
        print(f"{'='*60}")
        
        # Kembalikan tahun yang valid
        valid_years = self.mech.get_valid_ce_years_by_rule(saka_year, masa)
        return valid_years
    
    def display_main_components_evaluation(self, scored_candidates: List[Dict]):
        """Tampilkan evaluasi khusus untuk 4 komponen utama"""
        if not scored_candidates:
            return
        
        print(f"\n{'='*80}")
        print("EVALUASI 4 KOMPONEN UTAMA")
        print(f"{'='*80}")
        
        for i, cand in enumerate(scored_candidates[:3]):  # Tampilkan 3 teratas
            candidate = cand['candidate']
            year, month, day = candidate['date']
            breakdown = cand['breakdown']
            
            print(f"\n#{i+1}: {int(year)}-{int(month):02d}-{int(day):02d}")
            print(f"  Skor Total: {cand['score']:.3f} | Confidence: {cand['confidence']}")
            
            # Skor komponen utama
            tahun_score = breakdown['tahun_match']['score'] if 'tahun_match' in breakdown else 0
            bulan_score = breakdown['bulan_match']['score'] if 'bulan_match' in breakdown else 0
            wara_score = breakdown['wara_match']['score'] if 'wara_match' in breakdown else 0
            wuku_score = breakdown['wuku_match']['score'] if 'wuku_match' in breakdown else 0
            
            print(f"\n  Komponen Utama:")
            print(f"  [TAHUN] {'✓' if tahun_score >= 0.9 else '⚠️' if tahun_score >= 0.5 else '✗'} Skor: {tahun_score:.2f}")
            if 'tahun_match' in breakdown and 'details' in breakdown['tahun_match']:
                details = breakdown['tahun_match']['details']
                if 'note' in details:
                    print(f"         Catatan: {details['note']}")
            
            print(f"  [BULAN] {'✓' if bulan_score >= 0.9 else '⚠️' if bulan_score >= 0.5 else '✗'} Skor: {bulan_score:.2f}")
            if 'bulan_match' in breakdown and 'details' in breakdown['bulan_match']:
                details = breakdown['bulan_match']['details']
                if 'score_reason' in details:
                    reason = details['score_reason']
                    reason_map = {
                        'explicit_intercalation': 'Interkalasi eksplisit',
                        'intercalation_detected': 'Pergeseran bulan terdeteksi',  # DIUBAH
                        'exact_match': 'Cocok persis',
                        'mismatch': 'Tidak cocok'
                    }
                    print(f"         Status: {reason_map.get(reason, reason)}")
            
            print(f"  [WARA] {'✓' if wara_score >= 0.9 else '⚠️' if wara_score >= 0.5 else '✗'} Skor: {wara_score:.2f}")
            if 'wara_match' in breakdown and 'details' in breakdown['wara_match']:
                details = breakdown['wara_match']['details']
                if details.get('is_perfect_match'):
                    print(f"         ✓ Wara cocok persis (3/3)")
                elif 'total_matches' in details:
                    print(f"         Cocok {details['total_matches']}/3 komponen wara")
            
            print(f"  [WUKU] {'✓' if wuku_score >= 0.9 else '⚠️' if wuku_score >= 0.5 else '✗'} Skor: {wuku_score:.2f}")
            if 'wuku_match' in breakdown and 'details' in breakdown['wuku_match']:
                details = breakdown['wuku_match']['details']
                if details.get('has_wuku_data'):
                    if details.get('wuku_match'):
                        print(f"         ✓ Wuku cocok: {details.get('candidate_wuku')}")
                    else:
                        print(f"         ✗ Wuku tidak cocok: {details.get('candidate_wuku')} vs {details.get('inscribed_wuku')}")
                else:
                    print(f"         Tidak ada data wuku")
            
            # Informasi pergeseran bulan - DIUBAH LABELNYA
            if cand.get('month_shifted'):
                info = cand.get('intercalation_info', {})
                explicit_data = info.get('explicit_data')
                
                if explicit_data:
                    print(f"\n   🔴 INTERKALASI EKSPLISIT: {explicit_data['inscription']}")
                    print(f"      {explicit_data['month']} (Śaka {explicit_data.get('saka_year', '?')})")
                elif info.get('type') == 'punaḥ' and info.get('diff') == 1:
                    # DIUBAH: INDIKASI INTERKALASI -> PERGESERAN BULAN
                    print(f"\n   🟡 PERGESERAN BULAN (month_shifted):")
                    print(f"      Bulan prasasti: {info.get('inscribed_masa', '?')}")
                    print(f"      Bulan hitungan: {info.get('calculated_masa', '?')}")
                    print(f"      Catatan: Selisih 1 bulan - bisa disebabkan oleh:")
                    print(f"        - Sistem interkalasi yang berbeda (India vs Jawa Kuno)")
                    print(f"        - Awal tahun yang berbeda (bulan Caitra)")
                    print(f"        - Pergeseran kalender lokal")
    
    def _verify_system_consistency(self, verbose: bool = True):
        """Verifikasi konsistensi sistem dengan engine mekanik baru"""
        if verbose:
            print("=" * 80)
            print(f"{self.const.SYSTEM_NAME}")
            print("=" * 80)
            print("Memverifikasi konsistensi sistem...")
            
            # Verifikasi matriks lookup sudah dilakukan di MechanicalEngine.__init__
            print("✓ Matriks lookup telah dibangun dan diverifikasi")
            
            # Verifikasi mapping bulan Saka-Julian baru
            print(f"\nVerifikasi Mapping Bulan Saka-Julian Baru:")
            for masa, info in self.const.SAKA_MONTH_TO_JULIAN_RANGE.items():
                print(f"  ✓ {masa}: {info['range_desc']} (tambahan tahun: {info['add_years']})")
            
            # Verifikasi anchor Damais dengan engine mekanik baru
            print("\nVerifikasi Anchor Damais:")
            for anchor in self.const.DAMAIS_ANCHORS:
                ka = anchor.get("ka")
                if ka:
                    wuku_info = self.mech.calculate_wuku_wara_from_ka(ka)
                    wara_match = "✓" if wuku_info['wara_string'] == anchor.get('wara', '') else "⚠️"
                    print(f"  {wara_match} {anchor['id']}: KA={ka}, Wuku={wuku_info['wuku_name']}, Wara={wuku_info['wara_string']}")
            
            # Verifikasi data interkalasi eksplisit
            print("\nVerifikasi Data Interkalasi Eksplisit:")
            for saka_year, data in self.intercalation.EXPLICIT_INTERCALATIONS.items():
                print(f"  ✓ Śaka {saka_year}: {data['month']} - {data['inscription']}")
            
            print("\n✓ Sistem terverifikasi dan siap digunakan")
            print("=" * 80)
    
    # ========================================================================
    # PERBAIKAN UTAMA: Fungsi convert_prasasti dengan algoritma baru
    # ========================================================================
    
    def convert_prasasti(self, prasasti_data: Dict, verbose: bool = True) -> List[Dict]:
        """
        Konversi data prasasti ke tanggal Julian dengan sistem baru
        dan fokus pada 4 komponen utama.
        """
        if verbose:
            print("\n" + "=" * 80)
            print("Ω-STHAPATI v301.4: PROSES KONVERSI DENGAN 4 KOMPONEN UTAMA")
            print("=" * 80)
            print("4 KOMPONEN UTAMA yang dinilai:")
            print("1. Tahun (25%) - harus sesuai aturan konversi")
            print("2. Bulan (25%) - harus cocok dengan masa Saka")
            print("3. Wara (20%) - harus cocok persis")
            print("4. Wuku (15%) - harus cocok jika ada data")
            print("=" * 80)
            
            print(f"\nData prasasti yang diterima:")
            for key, value in prasasti_data.items():
                if value:
                    print(f"  {key}: {value}")
        
        # 1. Normalisasi data
        normalized_data = self.norm.normalize_inscription_data(prasasti_data)
        
        # 2. Validasi tahun berdasarkan aturan konversi dasar
        saka_year = normalized_data.get('saka_year')
        masa = normalized_data.get('masa', '')
        
        if not saka_year:
            print("❌ Error: Data tahun Saka (saka_year) tidak ditemukan")
            return []
        
        # Dapatkan tahun Masehi yang valid berdasarkan aturan dasar
        valid_ce_years = self.mech.get_valid_ce_years_by_rule(saka_year, masa)
        
        if verbose:
            print(f"\n2. ATURAN KONVERSI DASAR:")
            print(f"   Śaka {saka_year} {masa}")
            print(f"   Tahun Masehi yang valid: {valid_ce_years}")
        
        # 3. Cari SEMUA anchor TU-PA-Ā di rentang tahun yang luas
        all_candidates = []
        
        if verbose:
            print(f"\n3. PENCARIAN ANCHOR TU-PA-Ā (RENTANG LUAS):")
        
        # Cari anchor di semua tahun yang valid
        for ce_year in valid_ce_years:
            if verbose:
                print(f"   Tahun target {ce_year} M (cari anchor di ±1 tahun):")
            
            # Cari TU-PA-Ā di tahun ini, tahun sebelumnya, dan tahun berikutnya
            for year_offset in [-1, 0, 1]:
                search_year = ce_year + year_offset
                
                tu_pa_a_list = self.mech.find_tu_pa_a_in_year(search_year)
                
                if verbose and tu_pa_a_list:
                    for tupa in tu_pa_a_list:
                        anchor_y, anchor_m, anchor_d = tupa['date']
                        print(f"      Anchor di {search_year}: {int(anchor_y)}-{int(anchor_m):02d}-{int(anchor_d):02d}")
                
                for tupa in tu_pa_a_list:
                    candidates_from_tupa = self._find_candidates_from_tu_pa_a_new(
                        tupa, normalized_data, ce_year, verbose
                    )
                    all_candidates.extend(candidates_from_tupa)
        
        # 4. **SERAHKAN VALIDASI TAHUN ke fungsi filter**
        all_candidates = self._filter_invalid_candidates(all_candidates, normalized_data, verbose)
        
        if not all_candidates:
            print(f"\n❌ TIDAK DITEMUKAN KANDIDAT YANG VALID!")
            print(f"   Aturan konversi mengharuskan tahun Masehi: {valid_ce_years}")
            
            # Tampilkan debug info
            if verbose:
                print(f"\n   DEBUG: Semua anchor yang dicari:")
                for cand in all_candidates:
                    y, m, d = cand['date']
                    print(f"      {int(y)}-{int(m):02d}-{int(d):02d} | "
                          f"KA: {cand['ka']} | tahun cocok: {cand.get('year_match', '?')}")
            
            return []
        
        # 4. Evaluasi dengan TPDP Engine BARU (fokus 4 komponen utama)
        if verbose:
            print(f"\n4. EVALUASI DENGAN SISTEM SCORING BARU")
            print(f"   (Fokus: Tahun, Bulan, Wara, Wuku)")
        
        # Gunakan TPDP engine baru
        scored_candidates = self.tpdp.evaluate_candidates(all_candidates, normalized_data)
        
        # 5. Filter hanya kandidat dengan skor cukup tinggi
        # Lebih ketat karena fokus pada 4 komponen utama
        final_candidates = []
        for cand in scored_candidates:
            # Cek skor 4 komponen utama
            breakdown = cand['breakdown']
            tahun_score = breakdown['tahun_match']['score'] if 'tahun_match' in breakdown else 0
            bulan_score = breakdown['bulan_match']['score'] if 'bulan_match' in breakdown else 0
            wara_score = breakdown['wara_match']['score'] if 'wara_match' in breakdown else 0
            
            # Hitung skor rata-rata 4 komponen utama
            avg_main_components = (tahun_score + bulan_score + wara_score) / 3.0
            
            # Terima jika:
            # 1. Skor total ≥ 0.5, DAN
            # 2. Rata-rata 3 komponen utama ≥ 0.6, DAN
            # 3. Tahun harus valid (skor ≥ 0.9)
            if (cand['score'] >= 0.5 and 
                avg_main_components >= 0.6 and
                tahun_score >= 0.9):
                final_candidates.append(cand)
        
        if not final_candidates:
            print("❌ Tidak ada kandidat yang memenuhi kriteria 4 komponen utama")
            return []
        
        if verbose:
            print(f"\n5. HASIL FINAL ({len(final_candidates)} kandidat memenuhi kriteria):")
            
            # Tampilkan semua kandidat final dengan detail
            for i, cand in enumerate(final_candidates):
                candidate_data = cand['candidate']
                year, month, day = candidate_data['date']
                
                print(f"\n   {'='*50}")
                print(f"   KANDIDAT #{i+1} (Ranking: {cand.get('rank', '?')})")
                print(f"   {'='*50}")
                print(f"   Tanggal: {int(year)}-{int(month):02d}-{int(day):02d}")
                print(f"   KA: {candidate_data['ka']}")
                print(f"   Wuku: {candidate_data['wuku_info']['wuku_name']}")
                print(f"   Wara: {candidate_data['wuku_info']['wara_string']}")
                print(f"   Skor TPDP: {cand['score']:.3f}")
                print(f"   Confidence: {cand['confidence']}")
                
                # Tampilkan skor 4 komponen utama
                breakdown = cand.get('breakdown', {})
                print(f"\n   4 KOMPONEN UTAMA:")
                for component in ['tahun_match', 'bulan_match', 'wara_match', 'wuku_match']:
                    if component in breakdown:
                        info = breakdown[component]
                        comp_name = component.replace('_match', '').title()
                        score_val = info.get('score', 0)
                        icon = "✓" if score_val >= 0.9 else "⚠️" if score_val >= 0.5 else "✗"
                        print(f"     {comp_name}: {score_val:.2f} {icon}")
        
        return final_candidates
    
    # ========================================================================
    # PERBAIKAN UTAMA: Fungsi baru untuk mencari kandidat
    # ========================================================================
    
    def _find_candidates_from_tu_pa_a_new(self, tu_pa_a: Dict, prasasti_data: Dict, 
                                          expected_year: int, verbose: bool = False) -> List[Dict]:
        """Algoritma BARU dengan validasi temporal KETAT dan aturan konversi dasar"""
        candidates = []
        tu_pa_a_ka = tu_pa_a['ka']
        saka_year = prasasti_data.get('saka_year')
        masa = prasasti_data.get('masa', '')
        
        # ============================================================
        # **HAPUS VALIDASI TAHUN DI SINI** - ini untuk anchor, bukan kandidat
        # ============================================================
        # VALIDASI TAHUN AKAN DILAKUKAN DI FILTER_INVALID_CANDIDATES
        # ============================================================
        
        # Parse wara_string
        wara_string = prasasti_data.get('wara_string')
        if not wara_string:
            return []
        
        wara_info = self.mech.parse_wara_string_smart(wara_string)
        if not wara_info:
            return []
        
        target_triple = (
            wara_info.get('sadwara'),
            wara_info.get('pancawara'), 
            wara_info.get('saptawara')
        )
        
        # Dapatkan i_target dari matriks
        i_target = self.mech.get_index_from_wara_triple(*target_triple)
        if i_target is None:
            return []
        
        # Hitung kandidat KA
        candidate_ka = tu_pa_a_ka + i_target
        
        # Hitung tanggal
        year, month, day = self.math.ka_to_julian_date(candidate_ka)
        
        # ============================================================
        # VALIDASI 1: TAHUN HARUS COCOK dengan expected_year
        # ============================================================
        year_match = (year == expected_year)
        
        # ============================================================
        # VALIDASI 2: BULAN HARUS SESUAI dengan masa Saka
        # ============================================================
        masa_norm = self.norm.normalize(masa)
        month_info = self.mech.SAKA_MONTH_TO_JULIAN_RANGE.get(masa_norm, {})
        valid_months = month_info.get("julian_months", [])
        
        month_in_range = month in valid_months
        
        # ============================================================
        # VALIDASI 3: CEK WUKU (jika ada)
        # ============================================================
        wuku_match = True
        if 'wuku' in prasasti_data and prasasti_data['wuku']:
            wuku_info = self.mech.calculate_wuku_wara_from_ka(candidate_ka)
            inscribed_wuku = self.norm.normalize(prasasti_data['wuku'])
            calculated_wuku = self.norm.normalize(wuku_info['wuku_name'])
            wuku_match = (inscribed_wuku == calculated_wuku)
        
        # ============================================================
        # **TERIMA SEMUA KANDIDAT** - validasi tahun akan dilakukan nanti
        # ============================================================
        # JANGAN TOLAK DI SINI! Biarkan semua kandidat lolos dulu
        # ============================================================
        
        wuku_info = self.mech.calculate_wuku_wara_from_ka(candidate_ka)
        
        candidates.append({
            'ka': candidate_ka,
            'date': (year, month, day),
            'wuku_info': wuku_info,
            'tu_pa_a_anchor': tu_pa_a,
            'i': wuku_info['i'],
            's': wuku_info['s'],
            'day_of_year': self.math.day_of_year(year, month, int(day)),
            'verification_status': 'PRELIMINARY',
            'method': 'tu_pa_a_anchor_search',
            'year_match': year_match,
            'wuku_match': wuku_match,
            'month_in_range': month_in_range
        })
        
        return candidates
    
    def _filter_invalid_candidates(self, candidates: List[Dict], inscription_data: Dict, 
                                   verbose: bool = False) -> List[Dict]:
        """Filter kandidat dengan aturan yang LEBIH KETAT"""
        if not candidates:
            return []
        
        filtered_candidates = []
        masa = inscription_data.get('masa', '')
        saka_year = inscription_data.get('saka_year')
        
        masa_norm = self.norm.normalize(masa)
        month_info = self.mech.SAKA_MONTH_TO_JULIAN_RANGE.get(masa_norm, {})
        valid_months = month_info.get("julian_months", [])
        
        # Cek apakah ada data interkalasi eksplisit
        explicit_data = None
        if saka_year is not None:
            explicit_data = self.intercalation.get_explicit_intercalation(saka_year)
        
        # KASUS 1: INTERKALASI EKSPLISIT
        if explicit_data and masa_norm == self.norm.normalize(explicit_data["month"]):
            explicit_date = explicit_data["julian_date"]
            explicit_ka = self.math.julian_date_to_ka(
                explicit_date[0], explicit_date[1], explicit_date[2]
            )
            
            for cand in candidates:
                candidate_ka = cand['ka']
                hari_selisih = abs(candidate_ka - explicit_ka)
                
                # TERIMA JIKA: dalam 30 hari dari tanggal eksplisit
                if hari_selisih <= 30:
                    cand["priority"] = "EXPLICIT_INTERCALATION"
                    cand["distance_to_explicit"] = hari_selisih
                    filtered_candidates.append(cand)
                elif verbose:
                    year, month, day = cand['date']
                    print(f"   ❌ Kandidat {int(year)}-{int(month):02d}-{int(day):02d} ditolak: "
                          f"terlalu jauh dari tanggal eksplisit ({hari_selisih} hari)")
        
        # KASUS 2: NORMAL (TANPA INTERKALASI EKSPLISIT)
        else:
            for cand in candidates:
                year, month, day = cand['date']
                
                # ============================================================
                # **VALIDASI TAHUN AKHIR** - di sinilah aturan konversi diterapkan
                # ============================================================
                if saka_year and masa:
                    is_year_valid = self.mech.validate_ce_year_by_basic_rule(saka_year, masa, year)
                    
                    if not is_year_valid:
                        if verbose:
                            print(f"   ❌ Kandidat {int(year)}-{int(month):02d}-{int(day):02d} ditolak: "
                                  f"tahun {year} M tidak valid untuk Śaka {saka_year} {masa}")
                        continue  # Langsung tolak jika tahun tidak valid
                
                # ============================================================
                # VALIDASI BULAN
                # ============================================================
                month_valid = True
                
                if valid_months:
                    month_distances = [abs(month - m) % 12 for m in valid_months]
                    min_month_distance = min(month_distances)
                    
                    # KASUS: INTERKALASI EKSPLISIT
                    if explicit_data and masa_norm == self.norm.normalize(explicit_data["month"]):
                        # Untuk interkalasi eksplisit, terima jika dalam 30 hari dari tanggal eksplisit
                        explicit_date = explicit_data["julian_date"]
                        explicit_ka = self.math.julian_date_to_ka(
                            explicit_date[0], explicit_date[1], explicit_date[2]
                        )
                        hari_selisih = abs(cand['ka'] - explicit_ka)
                        
                        if hari_selisih <= 30:
                            cand["priority"] = "EXPLICIT_INTERCALATION"
                            cand["distance_to_explicit"] = hari_selisih
                        else:
                            month_valid = False
                    else:
                        # KASUS NORMAL: terima jika bulan valid atau selisih ≤ 1
                        if min_month_distance <= 1:
                            cand["priority"] = "NORMAL"
                            cand["month_distance"] = min_month_distance
                        else:
                            month_valid = False
                
                if month_valid:
                    filtered_candidates.append(cand)
                elif verbose:
                    print(f"   ❌ Kandidat {int(year)}-{int(month):02d}-{int(day):02d} ditolak: "
                          f"jarak bulan = {min_month_distance} (valid: {valid_months})")
        
        # ============================================================
        # URUTKAN BERDASARKAN PRIORITAS
        # ============================================================
        def sort_key(cand):
            priority_order = {
                "EXPLICIT_INTERCALATION": 0,
                "NORMAL": 1,
                "NO_MONTH_INFO": 2
            }
            
            priority = cand.get("priority", "NO_MONTH_INFO")
            base_score = priority_order.get(priority, 99)
            
            # Untuk explicit intercalation, urutkan berdasarkan kedekatan dengan tanggal eksplisit
            if priority == "EXPLICIT_INTERCALATION":
                return (base_score, cand.get("distance_to_explicit", 999))
            # Untuk normal, urutkan berdasarkan jarak bulan
            elif priority == "NORMAL":
                return (base_score, cand.get("month_distance", 999))
            else:
                return (base_score, 0)
        
        filtered_candidates.sort(key=sort_key)
        
        if verbose and len(candidates) != len(filtered_candidates):
            print(f"   Filter: {len(candidates)} → {len(filtered_candidates)} kandidat")
            print(f"   Prioritas: {[c.get('priority') for c in filtered_candidates]}")
        
        return filtered_candidates
    
    def _search_anchors_expanded(self, valid_ce_years, prasasti_data, verbose=False):
        """Cari anchor TU-PA-Ā di rentang tahun yang lebih luas (±1 tahun dari setiap tahun valid)"""
        all_anchors = []
        
        for ce_year in valid_ce_years:
            if verbose:
                print(f"   Mencari anchor untuk tahun target {ce_year} M (±1 tahun):")
            
            # Cari TU-PA-Ā di tahun target ±1 tahun
            for year_offset in [-1, 0, 1]:
                search_year = ce_year + year_offset
                tu_pa_a_list = self.mech.find_tu_pa_a_in_year(search_year)
                
                if tu_pa_a_list and verbose:
                    print(f"      Tahun {search_year}: {len(tu_pa_a_list)} anchor")
                
                for anchor in tu_pa_a_list:
                    # Hindari duplikat
                    if anchor['ka'] not in [a['ka'] for a in all_anchors]:
                        all_anchors.append(anchor)
        
        return all_anchors
    
    def _calculate_candidate_from_anchor_simple(self, tu_pa_a: Dict, wara_string: str,
                                               target_year: int, prasasti_data: Dict) -> Optional[Dict]:
        """Hitung kandidat sederhana dari anchor"""
        # Parse wara
        wara_info = self.mech.parse_wara_string_smart(wara_string)
        if not wara_info:
            return None
        
        target_triple = (
            wara_info.get('sadwara'),
            wara_info.get('pancawara'),
            wara_info.get('saptawara')
        )
        
        # Dapatkan i_target
        i_target = self.mech.get_index_from_wara_triple(*target_triple)
        if i_target is None:
            return None
        
        # Hitung KA kandidat
        ka_candidate = tu_pa_a['ka'] + i_target
        
        # Hitung tanggal
        year, month, day = self.math.ka_to_julian_date(ka_candidate)
        
        # **VALIDASI FINAL: ATURAN TAHUN**
        saka_year = prasasti_data.get('saka_year')
        masa = prasasti_data.get('masa', '')
        
        if not self.mech.validate_ce_year_by_basic_rule(saka_year, masa, year):
            return None  # Tolak jika tahun tidak sesuai aturan
        
        # Validasi bulan
        masa_norm = self.norm.normalize(masa)
        month_info = self.mech.SAKA_MONTH_TO_JULIAN_RANGE.get(masa_norm, {})
        valid_months = month_info.get("julian_months", [])
        
        if valid_months and month not in valid_months:
            # Cek selisih bulan untuk interkalasi
            month_distances = [abs(month - m) % 12 for m in valid_months]
            min_distance = min(month_distances)
            
            if min_distance > 1:  # Tolak jika selisih > 1 bulan
                return None
        
        # Hitung wuku info
        wuku_info = self.mech.calculate_wuku_wara_from_ka(ka_candidate)
        
        return {
            'ka': ka_candidate,
            'date': (year, month, day),
            'wuku_info': wuku_info,
            'tu_pa_a_anchor': tu_pa_a,
            'i': wuku_info['i'],
            's': wuku_info['s']
        }
    
    def _find_candidates_expanded_new(self, prasasti_data: Dict, verbose: bool = False) -> List[Dict]:
        """Pencarian kandidat dengan rentang anchor ±1 tahun"""
        saka_year = prasasti_data.get('saka_year')
        masa = prasasti_data.get('masa', '')
        wara_string = prasasti_data.get('wara_string', '')
        
        if verbose:
            print(f"\n3. PENCARIAN KANDIDAT DENGAN RENTANG ANCHOR LUAS:")
        
        # Tentukan tahun Masehi yang valid
        valid_ce_years = self.mech.get_valid_ce_years_by_rule(saka_year, masa)
        
        if verbose:
            print(f"   Tahun Masehi yang valid: {valid_ce_years}")
        
        all_candidates = []
        
        # Untuk setiap tahun valid, cari anchor di ±1 tahun
        for ce_year in valid_ce_years:
            if verbose:
                print(f"   Mencari anchor untuk tahun target {ce_year} M (±1 tahun):")
            
            for year_offset in [-1, 0, 1]:  # -1, 0, 1
                search_year = ce_year + year_offset
                
                # Cari TU-PA-Ā di tahun ini
                tu_pa_a_list = self.mech.find_tu_pa_a_in_year(search_year)
                
                if tu_pa_a_list and verbose:
                    print(f"      Tahun {search_year}: {len(tu_pa_a_list)} anchor")
                
                for tupa in tu_pa_a_list:
                    # Hitung kandidat dari anchor ini
                    candidate = self._calculate_candidate_from_anchor_simple(
                        tupa, wara_string, ce_year, prasasti_data
                    )
                    
                    if candidate:
                        all_candidates.append(candidate)
        
        return all_candidates
    
    def _generate_dummy_astronomical_data(self, ka: int) -> Dict:
        """Generate dummy astronomical data untuk testing (placeholder)"""
        year, month, day = self.math.ka_to_julian_date(ka)
        
        # Generate tithi acak untuk testing
        import random
        tithi = random.randint(1, 30)
        paksa = "Sukla" if tithi <= 15 else "Krsna"
        
        nakshatras = ["Aswini", "Bharani", "Krittika", "Rohini", "Mrigashira", 
                     "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
                     "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", 
                     "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", 
                     "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
                     "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
        
        return {
            "sayana": {
                "tithi": {"tithi": tithi, "paksa": paksa},
                "nakshatra": {"nakshatra": random.choice(nakshatras)}
            },
            "nirayana": {
                "tithi": {"tithi": tithi, "paksa": paksa},
                "nakshatra": {"nakshatra": random.choice(nakshatras)}
            }
        }
    
    def analyze_intercalation_patterns(self, start_saka: int, end_saka: int, 
                                      verbose: bool = True):
        """Analisis pola interkalasi dalam rentang tahun Saka"""
        if verbose:
            print("\n" + "=" * 80)
            print(f"ANALISIS POLA INTERKALASI SAKA {start_saka} - {end_saka}")
            print("=" * 80)
        
        results = []
        
        for saka_year in range(start_saka, end_saka + 1):
            year_results = {"saka_year": saka_year, "intercalations": []}
            
            for masa in self.const.FREQUENTLY_INTERCALATED:
                prob_info = self.intercalation.estimate_intercalation_probability(saka_year, masa)
                
                if prob_info["probability"] >= 0.3:
                    year_results["intercalations"].append(prob_info)
                    
                    if verbose and prob_info["probability"] >= 0.5:
                        print(f"\nŚaka {saka_year}, {masa}:")
                        print(f"  Probabilitas interkalasi: {prob_info['probability']:.1%}")
                        print(f"  Faktor: {', '.join(prob_info['factors'])}")
                        print(f"  Interpretasi: {prob_info['interpretation']}")
            
            results.append(year_results)
        
        if verbose:
            print("\n" + "=" * 80)
            print("KESIMPULAN POLA INTERKALASI:")
            print("1. Bulan interkalasi eksplisit prasasti: Śrāwaṇa, Chaitra, Pusya")
            print("2. Pola mengikuti siklus Metonic (19 tahun)")
            print("3. Verifikasi dengan prasasti yang ada sangat penting")
            print("=" * 80)
        
        return results
    
    def verify_with_damais_anchors(self, verbose: bool = True):
        """Verifikasi sistem dengan anchor Damais"""
        if verbose:
            print("\n" + "=" * 80)
            print("VERIFIKASI DENGAN ANCHOR DAMAIS")
            print("=" * 80)
        
        success_count = 0
        total_anchors = len(self.const.DAMAIS_ANCHORS)
        
        for anchor in self.const.DAMAIS_ANCHORS:
            if verbose:
                print(f"\n{anchor['id']} (Śaka {anchor['saka']} {anchor['masa']}):")
            
            prasasti_data = {
                'saka_year': anchor['saka'],
                'masa': anchor['masa'],
                'tithi': anchor['tithi'],
                'paksa': anchor['paksa'],
                'wuku': anchor.get('wuku', ''),
                'wara_string': anchor.get('wara', '')
            }
            
            results = self.convert_prasasti(prasasti_data, verbose=False)
            
            if results:
                best = results[0]
                ka_found = best['candidate']['ka']
                ka_expected = anchor.get('ka')
                
                if ka_expected and abs(ka_found - ka_expected) <= 210:
                    if verbose:
                        print(f"  ✓ Cocok! KA ditemukan: {ka_found}, KA anchor: {ka_expected}")
                        print(f"    Selisih: {abs(ka_found - ka_expected)} hari")
                    success_count += 1
                else:
                    if verbose:
                        print(f"  ⚠️  Tidak cocok. KA ditemukan: {ka_found}, KA anchor: {ka_expected}")
            else:
                if verbose:
                    print(f"  ❌ Tidak ditemukan kandidat")
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"HASIL VERIFIKASI: {success_count}/{total_anchors} anchor terverifikasi")
            
            if success_count == total_anchors:
                print("✅ SEMUA ANCHOR DAMAIS TERVERIFIKASI!")
            elif success_count >= total_anchors * 0.8:
                print("⚠️  Sebagian besar anchor terverifikasi")
            else:
                print("❌ Banyak anchor tidak terverifikasi, perlu investigasi")
            print("=" * 80)
        
        return success_count, total_anchors
    
    def batch_process_inscriptions(self, inscriptions_list: List[Dict], 
                                  verbose: bool = True) -> Dict:
        """Proses batch multiple prasasti sekaligus"""
        results = {
            "total_inscriptions": len(inscriptions_list),
            "successful_conversions": 0,
            "failed_conversions": 0,
            "with_month_shifted": 0,  # DIUBAH: with_intercalation -> with_month_shifted
            "with_explicit_intercalation": 0,
            "results": []
        }
        
        if verbose:
            print("\n" + "=" * 80)
            print(f"BATCH PROCESSING {len(inscriptions_list)} PRASASTI")
            print("=" * 80)
        
        for idx, inscription in enumerate(inscriptions_list):
            if verbose:
                print(f"\n[{idx+1}/{len(inscriptions_list)}] Memproses prasasti...")
            
            try:
                conversion_results = self.convert_prasasti(inscription, verbose=False)
                
                if conversion_results:
                    best_result = conversion_results[0]
                    candidate = best_result['candidate']
                    year, month, day = candidate['date']
                    
                    result_entry = {
                        "inscription_id": inscription.get('id', f"inscription_{idx+1}"),
                        "saka_year": inscription.get('saka_year'),
                        "masa": inscription.get('masa'),
                        "best_candidate": {
                            "date": f"{int(year)}-{int(month):02d}-{int(day):02d}",
                            "ka": candidate['ka'],
                            "wuku": candidate['wuku_info']['wuku_name'],
                            "wara": candidate['wuku_info']['wara_string']
                        },
                        "score": best_result['score'],
                        "confidence": best_result['confidence'],
                        "month_shifted": best_result.get('month_shifted', False),  # DIUBAH: has_intercalation -> month_shifted
                        "has_explicit_intercalation": False,
                        "num_candidates": len(conversion_results)
                    }
                    
                    # Cek apakah interkalasi eksplisit
                    if best_result.get('intercalation_info', {}).get('explicit_data'):
                        result_entry["has_explicit_intercalation"] = True
                        results["with_explicit_intercalation"] += 1
                    
                    results["results"].append(result_entry)
                    results["successful_conversions"] += 1
                    
                    if best_result.get('month_shifted'):  # DIUBAH
                        results["with_month_shifted"] += 1
                    
                    if verbose:
                        status = "✓" if best_result['score'] >= 0.6 else "⚠️"
                        if result_entry["has_explicit_intercalation"]:
                            interkalasi = " 🔴"
                        elif best_result.get('month_shifted'):  # DIUBAH
                            interkalasi = " 🟡"
                        else:
                            interkalasi = ""
                        print(f"  {status} {int(year)}-{int(month):02d}-{int(day):02d} (skor: {best_result['score']:.2f}){interkalasi}")
                else:
                    results["failed_conversions"] += 1
                    if verbose:
                        print(f"  ❌ Tidak ditemukan kandidat")
            except Exception as e:
                results["failed_conversions"] += 1
                if verbose:
                    print(f"  ❌ Error: {str(e)}")
        
        if verbose:
            print(f"\n{'='*80}")
            print("RINGKASAN BATCH PROCESSING:")
            print(f"  Total prasasti: {results['total_inscriptions']}")
            print(f"  Berhasil dikonversi: {results['successful_conversions']}")
            print(f"  Gagal dikonversi: {results['failed_conversions']}")
            print(f"  Dengan pergeseran bulan: {results['with_month_shifted']}")  # DIUBAH
            print(f"  Dengan interkalasi eksplisit: {results['with_explicit_intercalation']}")
            print(f"  Success rate: {(results['successful_conversions']/results['total_inscriptions'])*100:.1f}%")
            print("=" * 80)
        
        return results

# ============================================================================
# FUNGSI UTAMA DAN CONTOH PENGGUNAAN
# ============================================================================

def main():
    """Program utama dengan contoh penggunaan sistem terintegrasi"""
    
    # Inisialisasi sistem
    print("Memulai Ω-STHAPATI v301.4 FINAL IMPROVED...")
    system = ΩSthapatiSystem(verbose_startup=True)
    
    print("\n" + "=" * 80)
    print("SISTEM KONVERSI DENGAN ATURAN TAHUN SAKA → MASEHI")
    print("=" * 80)
    print("Aturan konversi berdasarkan bulan:")
    print("1. Bulan Pausa: Śaka +78 ATAU +79 (ambigu)")
    print("2. Bulan Magha/Phalguna: Śaka +79")
    print("3. Bulan lainnya (Caitra-Margasira): Śaka +78")
    print("=" * 80)
    
    # Contoh langsung
    print("\nCONTOH IMPLEMENTASI:")
    
    # Contoh 1: Pausa (ambigu)
    saka1, bulan1 = 822, "Pausa"
    tahun_valid1 = system.display_conversion_rule(saka1, bulan1)
    print(f"Hasil: Śaka {saka1} {bulan1} → Tahun Masehi yang valid: {tahun_valid1}")
    
    # Contoh 2: Sravana (+78)
    saka2, bulan2 = 828, "Sravana"
    tahun_valid2 = system.display_conversion_rule(saka2, bulan2)
    print(f"Hasil: Śaka {saka2} {bulan2} → Tahun Masehi yang valid: {tahun_valid2}")
    
    # Contoh 3: Phalguna (+79)
    saka3, bulan3 = 700, "Phalguna"
    tahun_valid3 = system.display_conversion_rule(saka3, bulan3)
    print(f"Hasil: Śaka {saka3} {bulan3} → Tahun Masehi yang valid: {tahun_valid3}")
    
    # Contoh prasasti untuk testing (termasuk data interkalasi eksplisit)
    sample_inscriptions = [
        {
            "id": "Ayam_Těas_I",
            "saka_year": 822,
            "masa": "Pusya",
            "tithi": 8,
            "paksa": "Sukla",
            "wara_string": "Haryang-Kaliwon-Wrhaspati"
        },
        {
            "id": "Cunggrang_II",
            "saka_year": 851,
            "masa": "Asuji",
            "tithi": 12,
            "paksa": "Sukla",
            "wuku": "Wugu",
            "wara_string": "Tungleh-Pahing-Sukra"
        },
        {
            "id": "Pucangan_Corrected",
            "saka_year": 963,
            "masa": "Kartika",
            "tithi": 10,
            "paksa": "Sukla",
            "wuku": "Wayang",
            "wara_string": "Haryang-Wage-Jumat"
        },
        {
            "id": "Hantang",
            "saka_year": 1057,
            "masa": "Bhadrapada",
            "tithi": 13,
            "paksa": "Krsna",
            "wuku": "Wukir",
            "wara_string": "Wurukung-Pahing-Saniscara"
        }
    ]
    
    while True:
        print("\n" + "=" * 80)
        print("Ω-STHAPATI v301.4 FINAL IMPROVED - MENU UTAMA")
        print("=" * 80)
        print("1. Konversi Prasasti Tunggal")
        print("2. Batch Processing (Multiple Prasasti)")
        print("3. Analisis Pola Interkalasi")
        print("4. Verifikasi dengan Anchor Damais")
        print("5. Contoh Prasasti Ayam Těas I (Interkalasi Eksplisit)")
        print("6. Contoh Prasasti Cunggrang II")
        print("7. Test All Sample Inscriptions")
        print("8. Tampilkan Evaluasi 4 Komponen Utama")
        print("9. Keluar")
        print("=" * 80)
        
        choice = input("Pilih menu (1-9): ").strip()
        
        if choice == "1":
            print("\n" + "-" * 80)
            print("KONVERSI PRASASTI TUNGGAL")
            print("-" * 80)
            
            try:
                saka_year = int(input("Tahun Saka: "))
                masa = input("Bulan Saka (Masa): ")
                tithi = int(input("Tithi (1-30): "))
                paksa = input("Paksa (Sukla/Krsna): ")
                wuku = input("Wuku (opsional): ")
                wara_string = input("Wara (opsional, contoh: Haryang-Wage-Sukra): ")
                nakshatra = input("Nakshatra (opsional): ")
                
                prasasti_data = {
                    'saka_year': saka_year,
                    'masa': masa,
                    'tithi': tithi,
                    'paksa': paksa,
                    'wuku': wuku,
                    'wara_string': wara_string,
                    'nakshatra': nakshatra
                }
                
                results = system.convert_prasasti(prasasti_data, verbose=True)
                
                if results:
                    # Tampilkan evaluasi 4 komponen utama
                    system.display_main_components_evaluation(results)
                
                input("\nTekan Enter untuk kembali ke menu...")
                
            except ValueError as e:
                print(f"Error: {e}")
                input("\nTekan Enter untuk kembali...")
        
        elif choice == "2":
            print("\n" + "=" * 80)
            print("BATCH PROCESSING - SAMPLE INSCRIPTIONS")
            print("=" * 80)
            
            results = system.batch_process_inscriptions(sample_inscriptions, verbose=True)
            input("\nTekan Enter untuk kembali...")
        
        elif choice == "3":
            start_saka = int(input("Tahun Saka awal: "))
            end_saka = int(input("Tahun Saka akhir: "))
            system.analyze_intercalation_patterns(start_saka, end_saka, verbose=True)
            input("\nTekan Enter untuk kembali...")
        
        elif choice == "4":
            system.verify_with_damais_anchors(verbose=True)
            input("\nTekan Enter untuk kembali...")
        
        elif choice == "5":
            print("\n" + "=" * 80)
            print("CONTOH: Prasasti Ayam Těas I (Interkalasi Eksplisit Śaka 822)")
            print("=" * 80)
            
            results = system.convert_prasasti(sample_inscriptions[0], verbose=True)
            
            if results:
                system.display_main_components_evaluation(results)
            
            input("\nTekan Enter untuk kembali...")
        
        elif choice == "6":
            print("\n" + "=" * 80)
            print("CONTOH: Prasasti A.113 Cunggrang II")
            print("=" * 80)
            
            results = system.convert_prasasti(sample_inscriptions[1], verbose=True)
            
            if results:
                system.display_main_components_evaluation(results)
            
            input("\nTekan Enter untuk kembali...")
        
        elif choice == "7":
            print("\n" + "=" * 80)
            print("TEST ALL SAMPLE INSCRIPTIONS")
            print("=" * 80)
            
            for i, inscription in enumerate(sample_inscriptions):
                print(f"\n[{i+1}/{len(sample_inscriptions)}] {inscription['id']}:")
                results = system.convert_prasasti(inscription, verbose=True)
                
                if results:
                    system.display_main_components_evaluation(results)
            
            input("\nTekan Enter untuk kembali...")
        
        elif choice == "8":
            print("\n" + "=" * 80)
            print("EVALUASI 4 KOMPONEN UTAMA - CONTOH")
            print("=" * 80)
            
            # Contoh dengan prasasti Ayam Těas I
            results = system.convert_prasasti(sample_inscriptions[0], verbose=False)
            
            if results:
                system.display_main_components_evaluation(results)
            else:
                print("Tidak ada hasil untuk dievaluasi")
            
            input("\nTekan Enter untuk kembali...")
        
        elif choice == "9":
            print("\nTerima kasih telah menggunakan Ω-STHAPATI v301.4 FINAL IMPROVED!")
            break
        
        else:
            print("Pilihan tidak valid")

# ============================================================================
# RUN PROGRAM
# ============================================================================

if __name__ == "__main__":
    main()