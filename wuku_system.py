# ============================================================================
# KONSTANTA SISTEM WUKU INFINITE RANGE (HANYA UNTUK WUKU) STANDALONE WUKU
# ============================================================================

import math
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime, timezone, timedelta

class ΩWukuConstants:
    """Konstanta sistem untuk perhitungan Wuku murni dengan range tak terbatas"""
    
    # IDENTITAS SISTEM
    SYSTEM_NAME = "Ω-WUKU-ENGINE"
    VERSION = "2.0.WUKU-INFINITE"
    ARCHITECT = "RAKAWI"
    BUILD_DATE = "2026-01-02"
    
    # KONSTANTA EPOCH (dengan dukungan negatif)
    KALI_EPOCH_JD_NOON = 588465.5  # 18 FEBRUARI 3102 SM/-3101 (tahun astronomi)
    KA_1_JAN_1_BC = 1132592       # 1 Januari 1 SM (tahun astronomi 0)
    KA_8_FEB_1_BC = 1132630       # EPOCH TU-PA-Ā (8 Februari 1 SM)
    SAKA0_EPOCH_JD = 1749608.5    # 3 Maret 78 M
    
    # JD untuk referensi
    JD_EPOCH_JULIAN = 1721424.5   # 1 Januari 1 M (Julian)
    JD_EPOCH_GREGORIAN = 2299160.5 # 15 Oktober 1582
    JD_EPOCH_J2000 = 2451545.0    # 1 Januari 2000, 12:00 TT
    
    # Konstanta untuk perhitungan tahun astronomi
    YEAR_ASTRONOMICAL_EPOCH = -4712  # Tahun 4713 SM sebagai tahun astronomi -4712
    
    # SIKLUS DASAR
    WUKU_CYCLE = 210  # Siklus wuku dalam hari
    JULIAN_280_YEAR_CYCLE = 280  # Siklus 280 tahun Julian
    DAYS_IN_JULIAN_280_YEAR = 102270  # 280 × 365.25
    
    # KONSTANTA KALENDER
    DAYS_IN_JULIAN_YEAR = 365.25
    DAYS_IN_GREGORIAN_YEAR = 365.2425
    
    # SIKLUS BULAN (untuk referensi kalender)
    SYNODIC_MONTH = 29.530589  # hari (bulan sinodik)
    SIDEREAL_MONTH = 27.321661  # hari (bulan sideris)
    TROPICAL_MONTH = 27.321582  # hari (bulan tropis)
    ANOMALISTIC_MONTH = 27.55455  # hari
    DRACONIC_MONTH = 27.21222  # hari
    
    # SIKLUS TAHUN
    TROPICAL_YEAR = 365.242190  # hari (tahun tropis)
    SIDEREAL_YEAR = 365.256363  # hari (tahun sideris)
    
    # SIKLUS GERHANA
    SAROS_CYCLE = 6585.32  # hari (~18 tahun)
    METONIC_CYCLE = 6939.69  # hari (~19 tahun)
    
    # ==================== KONSTANTA TAMBAHAN UNTUK OFFSET RATA-RATA ====================
    SOLAR_DAY = 1.0
    SOLAR_MONTH_MEAN = TROPICAL_YEAR / 12  # 30.436875 hari
    SOLAR_YEAR_MEAN = TROPICAL_YEAR        # 365.242190 hari

    LUNAR_SYNODIC_MONTH = SYNODIC_MONTH    # 29.530589 hari
    LUNAR_SIDEREAL_MONTH = SIDEREAL_MONTH  # 27.321661 hari
    LUNAR_YEAR_SYNODIC = 12 * SYNODIC_MONTH  # 354.367068 hari
    LUNAR_YEAR_SIDEREAL = 12 * SIDEREAL_MONTH  # 327.859932 hari (jarang dipakai)

    TITHI_MEAN_DAY = SYNODIC_MONTH / 30     # 0.984353 hari
    # ====================================================================================
    
    # WARA VARIAN
    SADWARA_VARIANTS = {
        "Tungleh": ["Tungle", "Tungleh", "Tunglek", "Tunglet", "TU", "Tunggal", "Tunggal", "Tunggel"],
        "Haryang": ["Haryang", "Aryang", "Haryan", "Aryan", "Harjang", "HA", "Haryang", "Aryang"],
        "Wurukung": ["Wurukung", "Urukung", "Wuruku", "Uruku", "Wuruk", "Uruk", "WU", "Wurukung"],
        "Paniron": ["Paniron", "Paniran", "Paniren", "PA", "Paniron", "Panirang"],
        "Was": ["Was", "Vas", "Wasi", "WA", "Was", "Vas"],
        "Maulu": ["Maulu", "Maul", "Mauluh", "MA", "Maulu", "Maulu"]
    }
    
    PANCAWARA_VARIANTS = {
        "Pahing": ["Pahing", "Paing", "Pahin", "PA", "Pahing", "Pahing"],
        "Pon": ["Pon", "Pohan", "PO", "Pon", "Pon"],
        "Wage": ["Wage", "Wageh", "WA", "Wage", "Wage"],
        "Kaliwon": ["Kaliwon", "Kliwon", "Kilwon", "KA", "Kaliwon", "Kliwon"],
        "Umanis": ["Umanis", "Legi", "Manis", "U", "Umanis", "Legi"]
    }
    
    SAPTAWARA_VARIANTS = {
        "Aditya": ["Raditya", "Aditya", "Ditya", "Minggu", "Radite", "Redite", "A", "Minggu"],
        "Soma": ["Soma", "Senin", "Senen", "SO", "Soma", "Senin"],
        "Anggara": ["Anggara", "Selasa", "ANG", "Anggara", "Selasa"],
        "Budha": ["Budha", "Buda", "Buddha", "Rabu", "BU", "Budha", "Rabu"],
        "Wrhaspati": ["Wrhaspati", "Wrespati", "Respati", "Brespati", "Kamis", "WR", "Wrhaspati", "Kamis"],
        "Sukra": ["Sukra", "Jumat", "Sukra", "SU", "Sukra", "Jumat"],
        "Saniscara": ["Saniscara", "Sabtu", "Tumpak", "SA", "Saniscara", "Sabtu"]
    }
    
    # NAMA WUKU STANDAR (30 WUKU)
    WUKU_NAMES = [
        "Sinta", "Landep", "Wukir", "Kurantil", "Tolu", "Gumbreg",
        "Warigalit", "Warigagung", "Julungwangi", "Sungsang",
        "Galungan", "Kuningan", "Langkir", "Mandasiya", "Julungpujut",
        "Pahang", "Kuruwelut", "Marakeh", "Tambir", "Medangkungan",
        "Maktal", "Wuye", "Manahil", "Prangbakat", "Bala", "Wugu",
        "Wayang", "Kulawu", "Dukut", "Watugunung"
    ]
    
    # VARIAN NAMA WUKU
    WUKU_NAMES_VARIANTS = {
        "Sinta": ["Sinta", "Sintha", "Sinta"],
        "Landep": ["Landep", "Landhep", "Landep"],
        "Wukir": ["Wukir", "Wukih", "Wukir"],
        "Kurantil": ["Kurantil", "Kurantil", "Kurantel", "Kurantil"],
        "Tolu": ["Tolu", "Tolo", "Tolu"],
        "Gumbreg": ["Gumbreg", "Gumbrek", "Gumbreg"],
        "Warigalit": ["Warigalit", "Warigalit", "Warigalit"],
        "Warigagung": ["Warigagung", "Warigagung", "Warigagung"],
        "Julungwangi": ["Julungwangi", "Jolungwangi", "Julungwangi"],
        "Sungsang": ["Sungsang", "Sungsang", "Sungsang"],
        "Galungan": ["Galungan", "Dungulan", "Dungulan", "Galungan"],
        "Kuningan": ["Kuningan", "Kuningan", "Kuningan"],
        "Langkir": ["Langkir", "Langkir", "Langkir"],
        "Mandasiya": ["Mandasiya", "Madasiya", "Mandasiya", "Mandasiya"],
        "Julungpujut": ["Julungpujut", "Jolungpujut", "Julungpujut"],
        "Pahang": ["Pahang", "Pahang", "Pahang"],
        "Kuruwelut": ["Kuruwelut", "Kuruwelut", "Kuruwelut"],
        "Marakeh": ["Marakeh", "Marakeh", "Marakeh"],
        "Tambir": ["Tambir", "Tambir", "Tambir"],
        "Medangkungan": ["Medangkungan", "Medangkungan", "Medangkungan"],
        "Maktal": ["Maktal", "Maktal", "Maktal"],
        "Wuye": ["Wuye", "Wuye", "Wuye"],
        "Manahil": ["Manahil", "Manahil", "Manahil"],
        "Prangbakat": ["Prangbakat", "Prangbakat", "Prangbakat"],
        "Bala": ["Bala", "Bala", "Bala"],
        "Wugu": ["Wugu", "Wugu", "Wugu"],
        "Wayang": ["Wayang", "Wayang", "Wayang"],
        "Kulawu": ["Kulawu", "Kulawu", "Kulawu"],
        "Dukut": ["Dukut", "Dukut", "Dukut"],
        "Watugunung": ["Watugunung", "Watugunung", "Watugunung"]
    }
    
    # MAPPING WARA STANDAR
    SADWARA_MAP = ["TU", "HA", "WU", "PA", "WA", "MA"]
    PANCAWARA_MAP = ["PA", "PO", "WA", "KA", "U"]
    SAPTAWARA_MAP = ["A", "SO", "ANG", "BU", "WR", "SU", "SA"]
    
    # Mapping ke nama lengkap
    SADWARA_FULL = {
        "TU": "Tungleh", "HA": "Haryang", "WU": "Wurukung",
        "PA": "Paniron", "WA": "Was", "MA": "Maulu"
    }
    
    PANCAWARA_FULL = {
        "PA": "Pahing", "PO": "Pon", "WA": "Wage",
        "KA": "Kaliwon", "U": "Umanis"
    }
    
    SAPTAWARA_FULL = {
        "A": "Aditya", "SO": "Soma", "ANG": "Anggara",
        "BU": "Budha", "WR": "Wrhaspati", "SU": "Sukra", 
        "SA": "Saniscara"
    }
    
    # MATRIKS WARA WUKU 210 HARI - REFERENSI
    WARA_WUKU_MATRIX_210 = {
        "NOTE": "Index 0 = TU-PA-Ā (Tungleh-Pahing-Aditya)",
        "DATA": [
            [0,1,"Sinta","Tungleh","Pahing","Aditya"], [1,1,"Sinta","Aryang","Pon","Soma"], 
            [2,1,"Sinta","Urukung","Wage","Anggara"], [3,1,"Sinta","Paniron","Kliwon","Buda"], 
            [4,1,"Sinta","Was","Legi","Wrespati"], [5,1,"Sinta","Maulu","Pahing","Sukra"], 
            [6,1,"Sinta","Tungleh","Pon","Saniscara"],
            [7,2,"Landep","Aryang","Wage","Aditya"], [8,2,"Landep","Urukung","Kliwon","Soma"], 
            [9,2,"Landep","Paniron","Legi","Anggara"], [10,2,"Landep","Was","Pahing","Buda"], 
            [11,2,"Landep","Maulu","Pon","Wrespati"], [12,2,"Landep","Tungleh","Wage","Sukra"], 
            [13,2,"Landep","Aryang","Kliwon","Saniscara"],
            [14,3,"Wukir","Urukung","Legi","Aditya"], [15,3,"Wukir","Paniron","Pahing","Soma"], 
            [16,3,"Wukir","Was","Pon","Anggara"], [17,3,"Wukir","Maulu","Wage","Buda"], 
            [18,3,"Wukir","Tungleh","Kliwon","Wrespati"], [19,3,"Wukir","Aryang","Legi","Sukra"], 
            [20,3,"Wukir","Urukung","Pahing","Saniscara"],
            [21,4,"Kurantil","Paniron","Pon","Aditya"], [22,4,"Kurantil","Was","Wage","Soma"], 
            [23,4,"Kurantil","Maulu","Kliwon","Anggara"], [24,4,"Kurantil","Tungleh","Legi","Buda"], 
            [25,4,"Kurantil","Aryang","Pahing","Wrespati"], [26,4,"Kurantil","Urukung","Pon","Sukra"], 
            [27,4,"Kurantil","Paniron","Wage","Saniscara"],
            [28,5,"Tolu","Was","Kliwon","Aditya"], [29,5,"Tolu","Maulu","Legi","Soma"], 
            [30,5,"Tolu","Tungleh","Pahing","Anggara"], [31,5,"Tolu","Aryang","Pon","Buda"], 
            [32,5,"Tolu","Urukung","Wage","Wrespati"], [33,5,"Tolu","Paniron","Kliwon","Sukra"], 
            [34,5,"Tolu","Was","Legi","Saniscara"],
            [35,6,"Gumbreg","Maulu","Pahing","Aditya"], [36,6,"Gumbreg","Tungleh","Pon","Soma"], 
            [37,6,"Gumbreg","Aryang","Wage","Anggara"], [38,6,"Gumbreg","Urukung","Kliwon","Buda"], 
            [39,6,"Gumbreg","Paniron","Legi","Wrespati"], [40,6,"Gumbreg","Was","Pahing","Sukra"], 
            [41,6,"Gumbreg","Maulu","Pon","Saniscara"],
            [42,7,"Warigalit","Tungleh","Wage","Aditya"], [43,7,"Warigalit","Aryang","Kliwon","Soma"], 
            [44,7,"Warigalit","Urukung","Legi","Anggara"], [45,7,"Warigalit","Paniron","Pahing","Buda"], 
            [46,7,"Warigalit","Was","Pon","Wrespati"], [47,7,"Warigalit","Maulu","Wage","Sukra"], 
            [48,7,"Warigalit","Tungleh","Kliwon","Saniscara"],
            [49,8,"Warigagung","Aryang","Legi","Aditya"], [50,8,"Warigagung","Urukung","Pahing","Soma"], 
            [51,8,"Warigagung","Paniron","Pon","Anggara"], [52,8,"Warigagung","Was","Wage","Buda"], 
            [53,8,"Warigagung","Maulu","Kliwon","Wrespati"], [54,8,"Warigagung","Tungleh","Legi","Sukra"], 
            [55,8,"Warigagung","Aryang","Pahing","Saniscara"],
            [56,9,"Julungwangi","Urukung","Pon","Aditya"], [57,9,"Julungwangi","Paniron","Wage","Soma"], 
            [58,9,"Julungwangi","Was","Kliwon","Anggara"], [59,9,"Julungwangi","Maulu","Legi","Buda"], 
            [60,9,"Julungwangi","Tungleh","Pahing","Wrespati"], [61,9,"Julungwangi","Aryang","Pon","Sukra"], 
            [62,9,"Julungwangi","Urukung","Wage","Saniscara"],
            [63,10,"Sungsang","Paniron","Kliwon","Aditya"], [64,10,"Sungsang","Was","Legi","Soma"], 
            [65,10,"Sungsang","Maulu","Pahing","Anggara"], [66,10,"Sungsang","Tungleh","Pon","Buda"], 
            [67,10,"Sungsang","Aryang","Wage","Wrespati"], [68,10,"Sungsang","Urukung","Kliwon","Sukra"], 
            [69,10,"Sungsang","Paniron","Legi","Saniscara"],
            [70,11,"Galungan","Was","Pahing","Aditya"], [71,11,"Galungan","Maulu","Pon","Soma"], 
            [72,11,"Galungan","Tungleh","Wage","Anggara"], [73,11,"Galungan","Aryang","Kliwon","Buda"], 
            [74,11,"Galungan","Urukung","Legi","Wrespati"], [75,11,"Galungan","Paniron","Pahing","Sukra"], 
            [76,11,"Galungan","Was","Pon","Saniscara"],
            [77,12,"Kuningan","Maulu","Wage","Aditya"], [78,12,"Kuningan","Tungleh","Kliwon","Soma"], 
            [79,12,"Kuningan","Aryang","Legi","Anggara"], [80,12,"Kuningan","Urukung","Pahing","Buda"], 
            [81,12,"Kuningan","Paniron","Pon","Wrespati"], [82,12,"Kuningan","Was","Wage","Sukra"], 
            [83,12,"Kuningan","Maulu","Kliwon","Saniscara"],
            [84,13,"Langkir","Tungleh","Legi","Aditya"], [85,13,"Langkir","Aryang","Pahing","Soma"], 
            [86,13,"Langkir","Urukung","Pon","Anggara"], [87,13,"Langkir","Paniron","Wage","Buda"], 
            [88,13,"Langkir","Was","Kliwon","Wrespati"], [89,13,"Langkir","Maulu","Legi","Sukra"], 
            [90,13,"Langkir","Tungleh","Pahing","Saniscara"],
            [91,14,"Mandasiya","Aryang","Pon","Aditya"], [92,14,"Mandasiya","Urukung","Wage","Soma"], 
            [93,14,"Mandasiya","Paniron","Kliwon","Anggara"], [94,14,"Mandasiya","Was","Legi","Buda"], 
            [95,14,"Mandasiya","Maulu","Pahing","Wrespati"], [96,14,"Mandasiya","Tungleh","Pon","Sukra"], 
            [97,14,"Mandasiya","Aryang","Wage","Saniscara"],
            [98,15,"Julungpujut","Urukung","Kliwon","Aditya"], [99,15,"Julungpujut","Paniron","Legi","Soma"], 
            [100,15,"Julungpujut","Was","Pahing","Anggara"], [101,15,"Julungpujut","Maulu","Pon","Buda"], 
            [102,15,"Julungpujut","Tungleh","Wage","Wrespati"], [103,15,"Julungpujut","Aryang","Kliwon","Sukra"], 
            [104,15,"Julungpujut","Urukung","Legi","Saniscara"],
            [105,16,"Pahang","Paniron","Pahing","Aditya"], [106,16,"Pahang","Was","Pon","Soma"], 
            [107,16,"Pahang","Maulu","Wage","Anggara"], [108,16,"Pahang","Tungleh","Kliwon","Buda"], 
            [109,16,"Pahang","Aryang","Legi","Wrespati"], [110,16,"Pahang","Urukung","Pahing","Sukra"], 
            [111,16,"Pahang","Paniron","Pon","Saniscara"],
            [112,17,"Kuruwelut","Was","Wage","Aditya"], [113,17,"Kuruwelut","Maulu","Kliwon","Soma"], 
            [114,17,"Kuruwelut","Tungleh","Legi","Anggara"], [115,17,"Kuruwelut","Aryang","Pahing","Buda"], 
            [116,17,"Kuruwelut","Urukung","Pon","Wrespati"], [117,17,"Kuruwelut","Paniron","Wage","Sukra"], 
            [118,17,"Kuruwelut","Was","Kliwon","Saniscara"],
            [119,18,"Marakeh","Maulu","Legi","Aditya"], [120,18,"Marakeh","Tungleh","Pahing","Soma"], 
            [121,18,"Marakeh","Aryang","Pon","Anggara"], [122,18,"Marakeh","Urukung","Wage","Buda"], 
            [123,18,"Marakeh","Paniron","Kliwon","Wrespati"], [124,18,"Marakeh","Was","Legi","Sukra"], 
            [125,18,"Marakeh","Maulu","Pahing","Saniscara"],
            [126,19,"Tambir","Tungleh","Pon","Aditya"], [127,19,"Tambir","Aryang","Wage","Soma"], 
            [128,19,"Tambir","Urukung","Kliwon","Anggara"], [129,19,"Tambir","Paniron","Legi","Buda"], 
            [130,19,"Tambir","Was","Pahing","Wrespati"], [131,19,"Tambir","Maulu","Pon","Sukra"], 
            [132,19,"Tambir","Tungleh","Wage","Saniscara"],
            [133,20,"Medangkungan","Aryang","Kliwon","Aditya"], [134,20,"Medangkungan","Urukung","Legi","Soma"], 
            [135,20,"Medangkungan","Paniron","Pahing","Anggara"], [136,20,"Medangkungan","Was","Pon","Buda"], 
            [137,20,"Medangkungan","Maulu","Wage","Wrespati"], [138,20,"Medangkungan","Tungleh","Kliwon","Sukra"], 
            [139,20,"Medangkungan","Aryang","Legi","Saniscara"],
            [140,21,"Maktal","Urukung","Pahing","Aditya"], [141,21,"Maktal","Paniron","Pon","Soma"], 
            [142,21,"Maktal","Was","Wage","Anggara"], [143,21,"Maktal","Maulu","Kliwon","Buda"], 
            [144,21,"Maktal","Tungleh","Legi","Wrespati"], [145,21,"Maktal","Aryang","Pahing","Sukra"], 
            [146,21,"Maktal","Urukung","Pon","Saniscara"],
            [147,22,"Wuye","Paniron","Wage","Aditya"], [148,22,"Wuye","Was","Kliwon","Soma"], 
            [149,22,"Wuye","Maulu","Legi","Anggara"], [150,22,"Wuye","Tungleh","Pahing","Buda"], 
            [151,22,"Wuye","Aryang","Pon","Wrespati"], [152,22,"Wuye","Urukung","Wage","Sukra"], 
            [153,22,"Wuye","Paniron","Kliwon","Saniscara"],
            [154,23,"Manahil","Was","Legi","Aditya"], [155,23,"Manahil","Maulu","Pahing","Soma"], 
            [156,23,"Manahil","Tungleh","Pon","Anggara"], [157,23,"Manahil","Aryang","Wage","Buda"], 
            [158,23,"Manahil","Urukung","Kliwon","Wrespati"], [159,23,"Manahil","Paniron","Legi","Sukra"], 
            [160,23,"Manahil","Was","Pahing","Saniscara"],
            [161,24,"Prangbakat","Maulu","Pon","Aditya"], [162,24,"Prangbakat","Tungleh","Wage","Soma"], 
            [163,24,"Prangbakat","Aryang","Kliwon","Anggara"], [164,24,"Prangbakat","Urukung","Legi","Buda"], 
            [165,24,"Prangbakat","Paniron","Pahing","Wrespati"], [166,24,"Prangbakat","Was","Pon","Sukra"], 
            [167,24,"Prangbakat","Maulu","Wage","Saniscara"],
            [168,25,"Bala","Tungleh","Kliwon","Aditya"], [169,25,"Bala","Aryang","Legi","Soma"], 
            [170,25,"Bala","Urukung","Pahing","Anggara"], [171,25,"Bala","Paniron","Pon","Buda"], 
            [172,25,"Bala","Was","Wage","Wrespati"], [173,25,"Bala","Maulu","Kliwon","Sukra"], 
            [174,25,"Bala","Tungleh","Legi","Saniscara"],
            [175,26,"Wugu","Aryang","Pahing","Aditya"], [176,26,"Wugu","Urukung","Pon","Soma"], 
            [177,26,"Wugu","Paniron","Wage","Anggara"], [178,26,"Wugu","Was","Kliwon","Buda"], 
            [179,26,"Wugu","Maulu","Legi","Wrespati"], [180,26,"Wugu","Tungleh","Pahing","Sukra"], 
            [181,26,"Wugu","Aryang","Pon","Saniscara"],
            [182,27,"Wayang","Urukung","Wage","Aditya"], [183,27,"Wayang","Paniron","Kliwon","Soma"], 
            [184,27,"Wayang","Was","Legi","Anggara"], [185,27,"Wayang","Maulu","Pahing","Buda"], 
            [186,27,"Wayang","Tungleh","Pon","Wrespati"], [187,27,"Wayang","Aryang","Wage","Sukra"], 
            [188,27,"Wayang","Urukung","Kliwon","Saniscara"],
            [189,28,"Kulawu","Paniron","Legi","Aditya"], [190,28,"Kulawu","Was","Pahing","Soma"], 
            [191,28,"Kulawu","Maulu","Pon","Anggara"], [192,28,"Kulawu","Tungleh","Wage","Buda"], 
            [193,28,"Kulawu","Aryang","Kliwon","Wrespati"], [194,28,"Kulawu","Urukung","Legi","Sukra"], 
            [195,28,"Kulawu","Paniron","Pahing","Saniscara"],
            [196,29,"Dukut","Was","Pon","Aditya"], [197,29,"Dukut","Maulu","Wage","Soma"], 
            [198,29,"Dukut","Tungleh","Kliwon","Anggara"], [199,29,"Dukut","Aryang","Legi","Buda"], 
            [200,29,"Dukut","Urukung","Pahing","Wrespati"], [201,29,"Dukut","Paniron","Pon","Sukra"], 
            [202,29,"Dukut","Was","Wage","Saniscara"],
            [203,30,"Watugunung","Maulu","Kliwon","Aditya"], [204,30,"Watugunung","Tungleh","Legi","Soma"], 
            [205,30,"Watugunung","Aryang","Pahing","Anggara"], [206,30,"Watugunung","Urukung","Pon","Buda"], 
            [207,30,"Watugunung","Paniron","Wage","Wrespati"], [208,30,"Watugunung","Was","Kliwon","Sukra"], 
            [209,30,"Watugunung","Maulu","Legi","Saniscara"]
        ]
    }


# ============================================================================
# KALENDER KONVERTER (JD, TANGGAL JULIAN/GREGORIAN)
# ============================================================================

class CalendarConverter:
    """Kelas untuk konversi antara kalender Julian, Gregorian, dan Julian Day dengan dukungan range tak terbatas"""
    
    @staticmethod
    def is_julian_leap_year(year: int) -> bool:
        """Cek tahun kabisat Julian (mendukung tahun astronomi negatif)"""
        return year % 4 == 0
    
    @staticmethod
    def is_gregorian_leap_year(year: int) -> bool:
        """Cek tahun kabisat Gregorian (mendukung tahun astronomi negatif)"""
        if year < 1582:
            return CalendarConverter.is_julian_leap_year(year)
        return (year % 4 == 0) and (year % 100 != 0 or year % 400 == 0)
    
    @staticmethod
    def gregorian_to_jd(year: int, month: int, day: int) -> float:
        """Konversi tanggal Gregorian ke Julian Day (support untuk tahun negatif)"""
        if month <= 2:
            year -= 1
            month += 12
        
        A = year // 100
        B = 2 - A + (A // 4)
        
        if year < 1582 or (year == 1582 and month < 10) or (year == 1582 and month == 10 and day < 15):
            B = 0
        
        jd = (int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + 
              day + B - 1524.5)
        return jd
    
    @staticmethod
    def jd_to_gregorian(jd: float) -> Tuple[int, int, int]:
        """Konversi Julian Day ke tanggal Gregorian (support untuk JD negatif)"""
        jd += 0.5
        Z = int(jd)
        F = jd - Z
        
        if Z < 2299161:
            A = Z
        else:
            alpha = int((Z - 1867216.25) / 36524.25)
            A = Z + 1 + alpha - (alpha // 4)
        
        B = A + 1524
        C = int((B - 122.1) / 365.25)
        D = int(365.25 * C)
        E = int((B - D) / 30.6001)
        
        day = B - D - int(30.6001 * E) + F
        month = E - 1 if E < 14 else E - 13
        year = C - 4716 if month > 2 else C - 4715
        
        return year, month, int(day)
    
    @staticmethod
    def julian_to_jd(year: int, month: int, day: int) -> float:
        """Konversi tanggal Julian ke Julian Day (support untuk tahun negatif)"""
        if month <= 2:
            year -= 1
            month += 12
        
        jd = (int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + 
              day - 1524.5)
        return jd
    
    @staticmethod
    def jd_to_julian(jd: float) -> Tuple[int, int, int]:
        """Konversi Julian Day ke tanggal Julian (support untuk JD negatif)"""
        jd += 0.5
        Z = int(jd)
        F = jd - Z
        
        A = Z
        B = A + 1524
        C = int((B - 122.1) / 365.25)
        D = int(365.25 * C)
        E = int((B - D) / 30.6001)
        
        day = B - D - int(30.6001 * E) + F
        month = E - 1 if E < 14 else E - 13
        year = C - 4716 if month > 2 else C - 4715
        
        return year, month, int(day)
    
    @staticmethod
    def date_to_jd(year: int, month: int, day: int, 
                   calendar_type: str = "gregorian") -> float:
        """Konversi tanggal ke Julian Day berdasarkan jenis kalender"""
        if calendar_type.lower() == "julian":
            return CalendarConverter.julian_to_jd(year, month, day)
        else:
            return CalendarConverter.gregorian_to_jd(year, month, day)
    
    @staticmethod
    def jd_to_date(jd: float, calendar_type: str = "gregorian") -> Tuple[int, int, int]:
        """Konversi Julian Day ke tanggal berdasarkan jenis kalender"""
        if calendar_type.lower() == "julian":
            return CalendarConverter.jd_to_julian(jd)
        else:
            return CalendarConverter.jd_to_gregorian(jd)
    
    @staticmethod
    def astronomical_year_to_bc_ad(year: int) -> str:
        """Konversi tahun astronomi ke format BC/AD"""
        if year <= 0:
            return f"{1-year} BC"
        else:
            return f"{year} AD"
    
    @staticmethod
    def bc_ad_to_astronomical_year(bc_ad_str: str) -> int:
        """Konversi format BC/AD ke tahun astronomi"""
        bc_ad_str = bc_ad_str.strip().upper()
        if "BC" in bc_ad_str:
            year = int(bc_ad_str.replace("BC", "").strip())
            return 1 - year
        elif "AD" in bc_ad_str:
            year = int(bc_ad_str.replace("AD", "").strip())
            return year
        else:
            return int(bc_ad_str)

    @staticmethod
    def datetime_to_jd(dt: datetime) -> float:
        """Konversi datetime UTC ke Julian Day (dengan fraksi hari)."""
        year = dt.year
        month = dt.month
        day = dt.day
        hour = dt.hour
        minute = dt.minute
        second = dt.second
        microsecond = dt.microsecond

        # Tentukan kalender berdasarkan tanggal
        if year < 1582 or (year == 1582 and month < 10) or (year == 1582 and month == 10 and day < 15):
            jd_noon = CalendarConverter.julian_to_jd(year, month, day)
        else:
            jd_noon = CalendarConverter.gregorian_to_jd(year, month, day)

        # Fraksi hari: JD noon = 12:00 UT, jadi hour=12 -> fraksi=0
        day_fraction = (hour - 12) / 24.0 + minute / 1440.0 + second / 86400.0 + microsecond / 86400e6
        return jd_noon + day_fraction


# ============================================================================
# NORMALISASI VARIAN
# ============================================================================

class VariantNormalizer:
    """Kelas untuk normalisasi varian input ke bentuk standar"""
    
    def __init__(self, constants: ΩWukuConstants):
        self.constants = constants
        
    def normalize_sadwara(self, input_str: str) -> str:
        """Normalisasi varian Sadwara ke bentuk standar"""
        input_str = input_str.strip().title()
        
        for standard, variants in self.constants.SADWARA_VARIANTS.items():
            if input_str in variants or input_str.upper() in variants:
                return standard
        
        for standard, variants in self.constants.SADWARA_VARIANTS.items():
            for variant in variants:
                if input_str in variant or variant in input_str:
                    return standard
        return input_str
    
    def normalize_pancawara(self, input_str: str) -> str:
        """Normalisasi varian Pancawara ke bentuk standar"""
        input_str = input_str.strip().title()
        
        for standard, variants in self.constants.PANCAWARA_VARIANTS.items():
            if input_str in variants or input_str.upper() in variants:
                return standard
        
        for standard, variants in self.constants.PANCAWARA_VARIANTS.items():
            for variant in variants:
                if input_str in variant or variant in input_str:
                    return standard
        return input_str
    
    def normalize_saptawara(self, input_str: str) -> str:
        """Normalisasi varian Saptawara ke bentuk standar"""
        input_str = input_str.strip().title()
        
        for standard, variants in self.constants.SAPTAWARA_VARIANTS.items():
            if input_str in variants or input_str.upper() in variants:
                return standard
        
        for standard, variants in self.constants.SAPTAWARA_VARIANTS.items():
            for variant in variants:
                if input_str in variant or variant in input_str:
                    return standard
        return input_str
    
    def normalize_wuku_name(self, input_str: str) -> str:
        """Normalisasi varian nama Wuku ke bentuk standar"""
        input_str = input_str.strip().title()
        
        for standard, variants in self.constants.WUKU_NAMES_VARIANTS.items():
            if input_str in variants:
                return standard
        
        for standard, variants in self.constants.WUKU_NAMES_VARIANTS.items():
            for variant in variants:
                if input_str in variant or variant in input_str:
                    return standard
        return input_str
    
    def get_wara_code(self, wara_name: str, wara_type: str) -> str:
        """Mendapatkan kode wara dari nama"""
        wara_type = wara_type.lower()
        
        if wara_type == "sadwara":
            mapping = {"Tungleh": "TU", "Haryang": "HA", "Wurukung": "WU",
                      "Paniron": "PA", "Was": "WA", "Maulu": "MA"}
        elif wara_type == "pancawara":
            mapping = {"Pahing": "PA", "Pon": "PO", "Wage": "WA",
                      "Kaliwon": "KA", "Umanis": "U"}
        elif wara_type == "saptawara":
            mapping = {"Aditya": "A", "Soma": "SO", "Anggara": "ANG",
                      "Budha": "BU", "Wrhaspati": "WR", "Sukra": "SU",
                      "Saniscara": "SA"}
        else:
            return ""
        return mapping.get(wara_name, "")


# ============================================================================
# MECHANICAL ENGINE WUKU UTAMA - DIUPDATE UNTUK RANGE TAK TERBATAS
# ============================================================================

class WukuMechanicalEngine:
    """
    Mechanical Engine murni untuk perhitungan Wuku 210 hari
    dengan dukungan range waktu tak terbatas
    """
    
    def __init__(self):
        """Inisialisasi engine dengan konstanta wuku"""
        self.constants = ΩWukuConstants()
        self.converter = CalendarConverter()
        self.normalizer = VariantNormalizer(self.constants)
        self._build_wuku_matrix()
        self._validate_engine_infinite()
    
    def _build_wuku_matrix(self) -> None:
        """Membangun matriks wuku 210 hari secara programatik"""
        self.wuku_matrix = np.zeros(210, dtype=[
            ('index', 'i8'),
            ('wuku_number', 'i4'),
            ('wuku_name', 'U20'),
            ('sadwara', 'U10'),
            ('pancawara', 'U10'),
            ('saptawara', 'U10'),
            ('day_in_wuku', 'i4'),
            ('is_tu_pa_a', 'bool')
        ])
        
        for i in range(210):
            wuku_num = (i // 7) + 1
            day_in_wuku = (i % 7) + 1
            wuku_name = self.constants.WUKU_NAMES[wuku_num - 1]
            
            sadwara_idx = i % 6
            pancawara_idx = i % 5
            saptawara_idx = i % 7
            
            is_tu_pa_a = (sadwara_idx == 0 and pancawara_idx == 0 and saptawara_idx == 0)
            
            self.wuku_matrix[i] = (
                i, wuku_num, wuku_name,
                self.constants.SADWARA_MAP[sadwara_idx],
                self.constants.PANCAWARA_MAP[pancawara_idx],
                self.constants.SAPTAWARA_MAP[saptawara_idx],
                day_in_wuku,
                is_tu_pa_a
            )
    
    def _validate_engine_infinite(self) -> None:
        """Validasi engine untuk range tak terbatas"""
        print("Ω-WUKU ENGINE INFINITE - Initializing...")
        
        if not self.wuku_matrix[0]['is_tu_pa_a']:
            raise ValueError("Engine validation failed: Index 0 is not TU-PA-A")
        
        test_cases = [
            (0, 1, "Sinta", "TU", "PA", "A", 1, True),
            (187, 27, "Wayang", "HA", "WA", "SU", 6, False),
            (209, 30, "Watugunung", "MA", "U", "SA", 7, False),
            (110, 16, "Pahang", "WU", "PA", "SU", 6, False)
        ]
        
        for idx, wuku_num, wuku_name, sad, panc, sapt, day, is_tpa in test_cases:
            entry = self.wuku_matrix[idx]
            if not (entry['wuku_number'] == wuku_num and
                   entry['wuku_name'] == wuku_name and
                   entry['sadwara'] == sad and
                   entry['pancawara'] == panc and
                   entry['saptawara'] == sapt and
                   entry['day_in_wuku'] == day and
                   entry['is_tu_pa_a'] == is_tpa):
                raise ValueError(f"Engine validation failed at index {idx}")
        
        print("✓ Engine validation passed")
        print(f"✓ Wuku Matrix: {len(self.wuku_matrix)} entries")
        print("=" * 60)
    
    # ========================================================================
    # KONVERSI DASAR: KA ↔ JD ↔ TANGGAL
    # ========================================================================
    
    def ka_to_julian_day(self, ka: int) -> float:
        """Konversi KA ke Julian Day (mendukung KA negatif)"""
        return self.constants.KALI_EPOCH_JD_NOON + float(ka)
    
    def julian_day_to_ka(self, jd: float) -> int:
        """Konversi Julian Day ke KA (mendukung JD negatif)"""
        return int(round(jd - self.constants.KALI_EPOCH_JD_NOON))
    
    def date_to_ka(self, year: int, month: int, day: int, 
                   calendar_type: str = "gregorian") -> int:
        """Konversi tanggal ke KA (mendukung tahun negatif)"""
        jd = self.converter.date_to_jd(year, month, day, calendar_type)
        return self.julian_day_to_ka(jd)
    
    def ka_to_date(self, ka: int, calendar_type: str = "gregorian") -> Tuple[int, int, int]:
        """Konversi KA ke tanggal (mendukung KA negatif)"""
        jd = self.ka_to_julian_day(ka)
        return self.converter.jd_to_date(jd, calendar_type)
    
    # ========================================================================
    # PERHITUNGAN WUKU DARI KA/TANGGAL
    # ========================================================================
    
    def safe_mod(self, a: int, n: int) -> int:
        """Modulo aman untuk bilangan negatif besar, hasil dalam [0, n-1]"""
        result = a % n
        return result if result >= 0 else result + n
    
    def ka_to_wuku_index(self, ka: int) -> int:
        """Konversi KA ke indeks wuku (0-209)"""
        delta = ka - self.constants.KA_8_FEB_1_BC
        return self.safe_mod(delta, 210)
    
    def get_wuku_by_ka(self, ka: int) -> Dict[str, Any]:
        """Mendapatkan informasi wuku lengkap berdasarkan KA (mendukung KA negatif)"""
        i = self.ka_to_wuku_index(ka)
        entry = self.wuku_matrix[i]
        
        wuku_position_in_cycle = i
        cycle_number = (ka - self.constants.KA_8_FEB_1_BC - i) // 210
        
        return {
            'ka': ka,
            'julian_day': self.ka_to_julian_day(ka),
            'wuku_index': i,
            'wuku_number': int(entry['wuku_number']),
            'wuku_name': str(entry['wuku_name']),
            'sadwara': str(entry['sadwara']),
            'pancawara': str(entry['pancawara']),
            'saptawara': str(entry['saptawara']),
            'sadwara_full': self.constants.SADWARA_FULL.get(str(entry['sadwara'])),
            'pancawara_full': self.constants.PANCAWARA_FULL.get(str(entry['pancawara'])),
            'saptawara_full': self.constants.SAPTAWARA_FULL.get(str(entry['saptawara'])),
            'day_in_wuku': int(entry['day_in_wuku']),
            'is_tu_pa_a': bool(entry['is_tu_pa_a']),
            'wara_triple': f"{entry['sadwara']} {entry['pancawara']} {entry['saptawara']}",
            'wara_triple_full': f"{self.constants.SADWARA_FULL.get(entry['sadwara'])} "
                               f"{self.constants.PANCAWARA_FULL.get(entry['pancawara'])} "
                               f"{self.constants.SAPTAWARA_FULL.get(entry['saptawara'])}",
            'cycle_number': cycle_number,
            'position_in_cycle': wuku_position_in_cycle
        }
    
    def get_wuku_by_date(self, year: int, month: int, day: int,
                         calendar_type: str = "gregorian") -> Dict[str, Any]:
        """Mendapatkan informasi wuku dari tanggal (mendukung tahun negatif)"""
        ka = self.date_to_ka(year, month, day, calendar_type)
        return self.get_wuku_by_ka(ka)
    
    def get_wara_triple(self, ka: int) -> str:
        """Mendapatkan triple wara (contoh: "TU PA A") dari KA"""
        return self.get_wuku_by_ka(ka)['wara_triple']
    
    def get_wara_triple_from_date(self, year: int, month: int, day: int,
                                  calendar_type: str = "gregorian") -> str:
        """Mendapatkan triple wara dari tanggal"""
        return self.get_wuku_by_date(year, month, day, calendar_type)['wara_triple']
    
    # ========================================================================
    # FUNGSI VERIFIKASI UNTUK RANGE TAK TERBATAS
    # ========================================================================
    
    def verify_kali_yuga_epoch(self) -> Dict[str, Any]:
        """Verifikasi epoch Kali Yuga (18 Februari 3102 SM)"""
        ka = 0
        engine_result = self.get_wuku_by_ka(ka)
        date_result = self.ka_to_date(ka, "julian")
        jd = self.ka_to_julian_day(ka)
        
        delta = ka - self.constants.KA_8_FEB_1_BC
        i = self.safe_mod(delta, 210)
        
        sadwara_idx = i % 6
        pancawara_idx = i % 5
        saptawara_idx = i % 7
        wuku_num = (i // 7) + 1
        day_in_wuku = (i % 7) + 1
        sad_code = self.constants.SADWARA_MAP[sadwara_idx]
        panc_code = self.constants.PANCAWARA_MAP[pancawara_idx]
        sapt_code = self.constants.SAPTAWARA_MAP[saptawara_idx]
        
        manual_result = {
            'ka': ka, 'delta': delta, 'i': i, 'wuku_number': wuku_num,
            'wuku_name': self.constants.WUKU_NAMES[wuku_num - 1],
            'day_in_wuku': day_in_wuku, 'sadwara': sad_code,
            'pancawara': panc_code, 'saptawara': sapt_code,
            'sadwara_full': self.constants.SADWARA_FULL.get(sad_code),
            'pancawara_full': self.constants.PANCAWARA_FULL.get(panc_code),
            'saptawara_full': self.constants.SAPTAWARA_FULL.get(sapt_code)
        }
        
        verification_passed = (
            engine_result['wuku_index'] == i and
            engine_result['wuku_name'] == manual_result['wuku_name'] and
            engine_result['wara_triple'] == f"{sad_code} {panc_code} {sapt_code}"
        )
        
        return {
            'engine_result': engine_result,
            'manual_calculation': manual_result,
            'date': date_result,
            'julian_day': jd,
            'verification_passed': verification_passed,
            'description': 'Epoch Kali Yuga (18 Februari 3102 SM) - Hari Jumat'
        }
    
    # ========================================================================
    # PERHITUNGAN TU-PA-A (WUKU SINTA HARI 1)
    # ========================================================================
    
    def is_tu_pa_a(self, ka: int) -> bool:
        """Cek apakah KA adalah TU-PA-A (KA mod 210 = 100)"""
        return self.safe_mod(ka, 210) == 100
    
    def is_tu_pa_a_date(self, year: int, month: int, day: int,
                        calendar_type: str = "gregorian") -> bool:
        """Cek apakah tanggal adalah TU-PA-A"""
        ka = self.date_to_ka(year, month, day, calendar_type)
        return self.is_tu_pa_a(ka)
    
    def find_tu_pa_a_in_year(self, year: int,
                              calendar_type: str = "gregorian") -> List[Dict[str, Any]]:
        """Mencari semua TU-PA-A dalam tahun tertentu"""
        ka_jan1 = self.date_to_ka(year, 1, 1, calendar_type)
        current_mod = self.safe_mod(ka_jan1, 210)
        
        if current_mod <= 100:
            first_ka = ka_jan1 + (100 - current_mod)
        else:
            first_ka = ka_jan1 + (210 - current_mod + 100)
        
        try:
            ka_dec31 = self.date_to_ka(year, 12, 31, calendar_type)
        except:
            ka_dec31 = self.date_to_ka(year, 12, 30, calendar_type)
        
        results = []
        current_ka = first_ka
        while current_ka <= ka_dec31:
            info = self.get_wuku_by_ka(current_ka)
            info['date'] = self.ka_to_date(current_ka, calendar_type)
            results.append(info)
            current_ka += 210
        return results
    
    def find_next_tu_pa_a(self, from_ka: int = None,
                          from_date: Tuple[int, int, int] = None,
                          calendar_type: str = "gregorian") -> Dict[str, Any]:
        """Mencari TU-PA-A berikutnya"""
        if from_ka is None:
            if from_date is None:
                raise ValueError("Harus menyediakan from_ka atau from_date")
            from_ka = self.date_to_ka(*from_date, calendar_type)
        
        current_mod = self.safe_mod(from_ka, 210)
        if current_mod <= 100:
            days_to_next = 100 - current_mod
        else:
            days_to_next = 210 - current_mod + 100
        
        next_ka = from_ka + days_to_next
        result = self.get_wuku_by_ka(next_ka)
        result['date'] = self.ka_to_date(next_ka, calendar_type)
        result['days_until'] = days_to_next
        return result
    
    # ========================================================================
    # SIKLUS 280 TAHUN JULIAN
    # ========================================================================
    
    def verify_280_year_cycle(self) -> Dict[str, Any]:
        """Verifikasi siklus 280 tahun Julian"""
        print("\nVerifying 280-year Julian cycle...")
        epoch_ka = self.constants.KA_8_FEB_1_BC
        epoch_date = self.ka_to_date(epoch_ka, "julian")
        future_ka = epoch_ka + self.constants.DAYS_IN_JULIAN_280_YEAR
        future_date = self.ka_to_date(future_ka, "julian")
        epoch_is_tpa = self.is_tu_pa_a(epoch_ka)
        future_is_tpa = self.is_tu_pa_a(future_ka)
        
        result = {
            'epoch': {'ka': epoch_ka, 'date': epoch_date, 'is_tu_pa_a': epoch_is_tpa},
            'future': {'ka': future_ka, 'date': future_date, 'is_tu_pa_a': future_is_tpa},
            'cycle_days': self.constants.DAYS_IN_JULIAN_280_YEAR,
            'cycle_years': self.constants.JULIAN_280_YEAR_CYCLE,
            'verified': epoch_is_tpa and future_is_tpa and 
                       (epoch_ka % 210 == 100) and (future_ka % 210 == 100)
        }
        print(f"✓ Epoch: {epoch_date}, TU-PA-A: {epoch_is_tpa}")
        print(f"✓ 280 years later: {future_date}, TU-PA-A: {future_is_tpa}")
        print(f"✓ Cycle verified: {result['verified']}")
        return result
    
    def find_tu_pa_a_in_280_year_cycle(self, start_year: int = 0,
                                       cycles: int = 3) -> List[Dict[str, Any]]:
        """Mencari TU-PA-A dalam siklus 280 tahun"""
        first_tpa = self.find_tu_pa_a_in_year(start_year, "julian")
        if not first_tpa:
            next_tpa = self.find_next_tu_pa_a(from_date=(start_year, 1, 1), 
                                              calendar_type="julian")
            start_ka = next_tpa['ka']
        else:
            start_ka = first_tpa[0]['ka']
        
        results = []
        for i in range(cycles):
            ka = start_ka + (i * self.constants.DAYS_IN_JULIAN_280_YEAR)
            info = self.get_wuku_by_ka(ka)
            date = self.ka_to_date(ka, "julian")
            results.append({
                'cycle': i + 1,
                'ka': ka,
                'date': date,
                'wuku': info['wuku_name'],
                'wara_triple': info['wara_triple']
            })
        return results
    
    # ========================================================================
    # PERHITUNGAN UNTUK RANGE EKSTREM
    # ========================================================================
    
    def calculate_wuku_for_extreme_date(self, year: int, month: int, day: int,
                                         calendar_type: str = "gregorian") -> Dict[str, Any]:
        """Menghitung wuku untuk tanggal ekstrem (ribuan/tahun sebelum Masehi)"""
        ka = self.date_to_ka(year, month, day, calendar_type)
        info = self.get_wuku_by_ka(ka)
        jd = self.ka_to_julian_day(ka)
        ka_from_epoch = ka - self.constants.KA_8_FEB_1_BC
        cycle_number = ka_from_epoch // 210
        position_in_cycle = self.safe_mod(ka_from_epoch, 210)
        years_since_kali_yuga = ka / 365.2425
        
        if year <= 0:
            year_display = f"{1-year} BC"
        else:
            year_display = f"{year} AD"
        
        return {
            'input_date': f"{year_display}-{month:02d}-{day:02d}",
            'astronomical_year': year,
            'ka': ka,
            'julian_day': jd,
            'wuku_name': info['wuku_name'],
            'wuku_number': info['wuku_number'],
            'wara_triple': info['wara_triple'],
            'wara_triple_full': info['wara_triple_full'],
            'day_in_wuku': info['day_in_wuku'],
            'is_tu_pa_a': info['is_tu_pa_a'],
            'cycle_number': cycle_number,
            'position_in_cycle': position_in_cycle,
            'years_since_kali_yuga': years_since_kali_yuga,
            'description': f"Hari {info['saptawara_full']} ({info['saptawara']})"
        }
    
    # ========================================================================
    # GENERASI MATRIKS DAN DATA
    # ========================================================================
    
    def generate_wuku_matrix(self, start_ka: int, end_ka: int) -> np.ndarray:
        """Generate matriks wuku untuk rentang KA"""
        num_days = end_ka - start_ka + 1
        dtype = [
            ('ka', 'i8'), ('julian_day', 'f8'), ('wuku_index', 'i4'),
            ('wuku_number', 'i4'), ('wuku_name', 'U20'), ('sadwara', 'U10'),
            ('pancawara', 'U10'), ('saptawara', 'U10'), ('day_in_wuku', 'i4'),
            ('is_tu_pa_a', 'bool'), ('wara_triple', 'U20')
        ]
        matrix = np.zeros(num_days, dtype=dtype)
        
        for i in range(num_days):
            ka = start_ka + i
            info = self.get_wuku_by_ka(ka)
            matrix[i] = (
                ka, info['julian_day'], info['wuku_index'],
                info['wuku_number'], info['wuku_name'],
                info['sadwara'], info['pancawara'], info['saptawara'],
                info['day_in_wuku'], info['is_tu_pa_a'], info['wara_triple']
            )
        return matrix
    
    def generate_date_matrix(self, start_year: int, end_year: int,
                             calendar_type: str = "gregorian") -> np.ndarray:
        """Generate matriks untuk rentang tanggal"""
        start_ka = self.date_to_ka(start_year, 1, 1, calendar_type)
        end_ka = self.date_to_ka(end_year, 12, 31, calendar_type)
        matrix = self.generate_wuku_matrix(start_ka, end_ka)
        
        date_dtype = np.dtype(matrix.dtype.descr + [
            ('year', 'i4'), ('month', 'i4'), ('day', 'i4'), ('date_str', 'U20')
        ])
        result = np.zeros(len(matrix), dtype=date_dtype)
        
        for i, row in enumerate(matrix):
            ka = row['ka']
            year, month, day = self.ka_to_date(ka, calendar_type)
            result[i] = tuple(row) + (year, month, day, f"{year:04d}-{month:02d}-{day:02d}")
        return result
    
    # ========================================================================
    # UTILITAS DAN HELPER FUNCTIONS
    # ========================================================================
    
    def _day_of_year(self, year: int, month: int, day: int) -> int:
        """Menghitung hari ke-N dalam tahun Gregorian"""
        month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if self.converter.is_gregorian_leap_year(year):
            month_lengths[1] = 29
        return sum(month_lengths[:month-1]) + day
    
    def _day_of_year_julian(self, year: int, month: int, day: int) -> int:
        """Hari ke-N dalam tahun Julian"""
        month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if year % 4 == 0:
            month_lengths[1] = 29
        return sum(month_lengths[:month-1]) + day
    
    def calculate_ka_for_julian_date(self, year: int, month: int, day: int) -> int:
        """Menghitung KA untuk tanggal Julian dengan formula"""
        ka_jan1 = (self.constants.KA_1_JAN_1_BC + 365 * year + ((year + 3) // 4))
        n = self._day_of_year_julian(year, month, day)
        return ka_jan1 + (n - 1)
    
    def find_date_by_wara_triple(self, wara_triple: str,
                                  start_year: int = 2000, end_year: int = 2100,
                                  calendar_type: str = "gregorian") -> List[Dict[str, Any]]:
        """Mencari tanggal berdasarkan triple wara"""
        results = []
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                month_days = 31
                if month in [4, 6, 9, 11]:
                    month_days = 30
                elif month == 2:
                    if calendar_type == "gregorian":
                        month_days = 29 if self.converter.is_gregorian_leap_year(year) else 28
                    else:
                        month_days = 29 if self.converter.is_julian_leap_year(year) else 28
                for day in range(1, month_days + 1):
                    if self.get_wara_triple_from_date(year, month, day, calendar_type) == wara_triple:
                        results.append({
                            'date': (year, month, day),
                            'ka': self.date_to_ka(year, month, day, calendar_type),
                            'wuku_info': self.get_wuku_by_date(year, month, day, calendar_type)
                        })
        return results
    
    def format_year_for_display(self, year: int) -> str:
        """Format tahun untuk display dengan notasi BC/AD"""
        if year <= 0:
            return f"{1-year:,} BC"
        else:
            return f"{year:,} AD"
    
    # ========================================================================
    # FUNGSI TAMBAHAN: HARI KE TU-PA-A BERIKUTNYA
    # ========================================================================
    
    def get_days_to_next_tu_pa_a(self, ka: int) -> int:
        """Hitung jumlah hari hingga TU-PA-A berikutnya dari KA tertentu."""
        pos = self.safe_mod(ka, 210)
        return (100 - pos) if pos <= 100 else (210 - pos + 100)
    
    def get_days_to_next_tu_pa_a_from_date(self, year: int, month: int, day: int,
                                            calendar_type: str = "gregorian") -> int:
        """Hitung jumlah hari hingga TU-PA-A berikutnya dari tanggal tertentu."""
        ka = self.date_to_ka(year, month, day, calendar_type)
        return self.get_days_to_next_tu_pa_a(ka)
    
    # ========================================================================
    # FUNGSI TAMBAHAN: HARI SEJAK EPOCH WUKU
    # ========================================================================
    
    def get_days_since_wuku_epoch(self, ka: int) -> int:
        """Hitung jumlah hari sejak epoch wuku (8 Februari 1 SM)."""
        return ka - self.constants.KA_8_FEB_1_BC
    
    def get_days_since_wuku_epoch_from_date(self, year: int, month: int, day: int,
                                             calendar_type: str = "gregorian") -> int:
        """Hitung jumlah hari sejak epoch wuku dari tanggal tertentu."""
        ka = self.date_to_ka(year, month, day, calendar_type)
        return self.get_days_since_wuku_epoch(ka)
    
    def get_detailed_wuku_epoch_info(self, ka: int) -> Dict[str, Any]:
        """Dapatkan informasi detail tentang posisi relatif terhadap epoch wuku."""
        days_since_epoch = ka - self.constants.KA_8_FEB_1_BC
        pos_since_epoch = self.safe_mod(days_since_epoch, 210)
        cycle_number = days_since_epoch // 210
        day_in_cycle = pos_since_epoch + 1
        progress_percent = (pos_since_epoch / 210.0) * 100.0
        wuku_info = self.get_wuku_by_ka(ka)
        is_tu_pa_a_today = (pos_since_epoch == 0)
        days_to_next_tpa = 210 - pos_since_epoch if not is_tu_pa_a_today else 210
        
        epoch_date = self.ka_to_date(self.constants.KA_8_FEB_1_BC, "julian")
        epoch_year, epoch_month, epoch_day = epoch_date
        if epoch_year <= 0:
            epoch_formatted = f"{1-epoch_year} SM-{epoch_month:02d}-{epoch_day:02d}"
        else:
            epoch_formatted = f"{epoch_year} M-{epoch_month:02d}-{epoch_day:02d}"
        
        direction = "sesudah epoch" if days_since_epoch >= 0 else "sebelum epoch"
        
        return {
            'ka_current': ka,
            'ka_epoch': self.constants.KA_8_FEB_1_BC,
            'days_since_epoch': days_since_epoch,
            'direction': direction,
            'cycle_number': cycle_number,
            'position_in_cycle': pos_since_epoch,
            'day_in_cycle': day_in_cycle,
            'progress_percent': progress_percent,
            'is_tu_pa_a_today': is_tu_pa_a_today,
            'days_to_next_tu_pa_a': days_to_next_tpa,
            'epoch_date': epoch_date,
            'epoch_date_formatted': epoch_formatted,
            'epoch_description': "8 Februari 1 SM (Kalender Julian) - Hari pertama TU-PA-A (Tungleh-Pahing-Aditya)",
            'current_wuku_name': wuku_info['wuku_name'],
            'current_wuku_number': wuku_info['wuku_number'],
            'current_wara_triple': wuku_info['wara_triple'],
            'current_wara_triple_full': wuku_info['wara_triple_full'],
            'current_day_in_wuku': wuku_info['day_in_wuku'],
            'interpretation': {
                'abs_days': abs(days_since_epoch),
                'cycle_text': f"Siklus {cycle_number}, Hari {day_in_cycle}/210",
                'progress_text': f"Progres {progress_percent:.1f}%",
                'direction_text': f"{abs(days_since_epoch):,} hari {direction}",
                'tpa_status': "Hari ini adalah TU-PA-A" if is_tu_pa_a_today else f"TU-PA-A berikutnya dalam {days_to_next_tpa} hari"
            }
        }
    
    def get_detailed_wuku_epoch_info_from_date(self, year: int, month: int, day: int,
                                                calendar_type: str = "gregorian") -> Dict[str, Any]:
        """Dapatkan informasi detail tentang posisi relatif terhadap epoch wuku dari tanggal."""
        ka = self.date_to_ka(year, month, day, calendar_type)
        return self.get_detailed_wuku_epoch_info(ka)
    
    # ========================================================================
    # FUNGSI UTILITY TAMBAHAN
    # ========================================================================
    
    def find_tu_pa_a_within_days(self, start_ka: int, max_days: int = 365) -> List[Dict[str, Any]]:
        """Cari semua TU-PA-A dalam rentang hari tertentu dari KA awal."""
        results = []
        if self.is_tu_pa_a(start_ka):
            info = self.get_wuku_by_ka(start_ka)
            info['date'] = self.ka_to_date(start_ka, "gregorian")
            info['days_from_start'] = 0
            results.append(info)
        
        days_to_first = self.get_days_to_next_tu_pa_a(start_ka)
        current_ka = start_ka + days_to_first
        while current_ka - start_ka <= max_days:
            info = self.get_wuku_by_ka(current_ka)
            info['date'] = self.ka_to_date(current_ka, "gregorian")
            info['days_from_start'] = current_ka - start_ka
            results.append(info)
            current_ka += 210
        return results
    
    def get_wuku_phase_percentage(self, ka: int) -> Dict[str, Any]:
        """Hitung persentase fase dalam siklus wuku."""
        days_since_epoch = ka - self.constants.KA_8_FEB_1_BC
        pos_in_210 = self.safe_mod(days_since_epoch, 210)
        cycle_210_percent = (pos_in_210 / 210.0) * 100.0
        
        day_in_wuku = (pos_in_210 % 7) + 1
        wuku_percent = (day_in_wuku / 7.0) * 100.0
        
        # Verifikasi dengan data wuku
        wuku_info = self.get_wuku_by_ka(ka)
        actual_day_in_wuku = wuku_info['day_in_wuku']
        if day_in_wuku != actual_day_in_wuku:
            day_in_wuku = actual_day_in_wuku
            wuku_percent = (day_in_wuku / 7.0) * 100.0
        
        return {
            'cycle_210_day_percent': cycle_210_percent,
            'wuku_7_day_percent': wuku_percent,
            'day_in_wuku': day_in_wuku,
            'position_in_210_cycle': pos_in_210,
            'days_since_epoch': days_since_epoch,
            'interpretation': {
                'cycle_progress': f"{cycle_210_percent:.1f}% dari siklus 210 hari",
                'wuku_progress': f"{wuku_percent:.1f}% dari wuku saat ini",
                'day_in_wuku_text': f"Hari ke-{day_in_wuku} dari 7 hari dalam wuku"
            }
        }

    def get_current_wuku_info(self, use_utc: bool = True) -> Dict[str, Any]:
        """
        Mendapatkan informasi wuku untuk waktu sekarang.
        use_utc=True menggunakan UTC, False menggunakan waktu lokal sistem.
        """
        if use_utc:
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now()

        jd = self.converter.datetime_to_jd(now)
        ka = self.julian_day_to_ka(jd)

        # Ambil info detail epoch
        epoch_info = self.get_detailed_wuku_epoch_info(ka)

        # Tambahkan informasi waktu
        epoch_info['current_datetime_utc'] = now.isoformat() if use_utc else None
        epoch_info['current_datetime_local'] = now.isoformat() if not use_utc else None
        epoch_info['jd'] = jd

        return epoch_info
    
    # ============================================================================
    # FUNGSI-FUNGSI OFFSET WAKTU (BERDASARKAN RATA-RATA)
    # ============================================================================
    
    def add_solar_days(self, ka: int, days: int) -> Dict[str, Any]:
        """Menambahkan sejumlah hari solar (integer) ke KA."""
        ka_baru = ka + days
        info = self.get_wuku_by_ka(ka_baru)
        info['date'] = self.ka_to_date(ka_baru)
        info['method'] = 'solar_day'
        info['days_added'] = days
        info['ka_awal'] = ka
        return info

    def add_solar_months(self, ka: int, months: int) -> Dict[str, Any]:
        """Menambahkan sejumlah bulan solar rata‑rata (tropis/12)."""
        days = months * self.constants.SOLAR_MONTH_MEAN
        ka_baru = ka + int(round(days))
        info = self.get_wuku_by_ka(ka_baru)
        info['date'] = self.ka_to_date(ka_baru)
        info['method'] = 'solar_month'
        info['months_added'] = months
        info['ka_awal'] = ka
        return info

    def add_solar_years(self, ka: int, years: int) -> Dict[str, Any]:
        """Menambahkan sejumlah tahun solar rata‑rata (tropis)."""
        days = years * self.constants.SOLAR_YEAR_MEAN
        ka_baru = ka + int(round(days))
        info = self.get_wuku_by_ka(ka_baru)
        info['date'] = self.ka_to_date(ka_baru)
        info['method'] = 'solar_year'
        info['years_added'] = years
        info['ka_awal'] = ka
        return info

    def add_lunar_months(self, ka: int, months: int) -> Dict[str, Any]:
        """Menambahkan sejumlah bulan sinodik rata‑rata."""
        days = months * self.constants.LUNAR_SYNODIC_MONTH
        ka_baru = ka + int(round(days))
        info = self.get_wuku_by_ka(ka_baru)
        info['date'] = self.ka_to_date(ka_baru)
        info['method'] = 'lunar_month'
        info['months_added'] = months
        info['ka_awal'] = ka
        return info

    def add_lunar_years(self, ka: int, years: int) -> Dict[str, Any]:
        """Menambahkan sejumlah tahun lunar (12 sinodik) rata‑rata."""
        days = years * self.constants.LUNAR_YEAR_SYNODIC
        ka_baru = ka + int(round(days))
        info = self.get_wuku_by_ka(ka_baru)
        info['date'] = self.ka_to_date(ka_baru)
        info['method'] = 'lunar_year'
        info['years_added'] = years
        info['ka_awal'] = ka
        return info

    def add_tithi(self, ka: int, tithi: int) -> Dict[str, Any]:
        """Menambahkan sejumlah tithi (1/30 sinodik) rata‑rata."""
        days = tithi * self.constants.TITHI_MEAN_DAY
        ka_baru = ka + int(round(days))
        info = self.get_wuku_by_ka(ka_baru)
        info['date'] = self.ka_to_date(ka_baru)
        info['method'] = 'tithi'
        info['tithi_added'] = tithi
        info['ka_awal'] = ka
        return info
    
    def print_wuku_info(self, ka: int = None,
                        date: Tuple[int, int, int] = None,
                        calendar_type: str = "gregorian") -> None:
        """Mencetak informasi wuku."""
        if ka is None and date is None:
            raise ValueError("Harus menyediakan ka atau date")
        if ka is None:
            ka = self.date_to_ka(*date, calendar_type)
        
        info = self.get_wuku_by_ka(ka)
        date_info = self.ka_to_date(ka, calendar_type)
        year_disp = self.format_year_for_display(date_info[0])
        
        print("=" * 60)
        print("WUKU INFORMATION")
        print("=" * 60)
        print(f"Date       : {date_info[0]:04d}-{date_info[1]:02d}-{date_info[2]:02d}")
        print(f"           : {year_disp}")
        print(f"KA         : {ka:,}")
        print(f"Julian Day : {info['julian_day']:.2f}")
        print(f"Wuku       : {info['wuku_name']} (#{info['wuku_number']})")
        print(f"Day in Wuku: {info['day_in_wuku']}/7")
        print(f"Wara Triple: {info['wara_triple_full']}")
        print(f"           : {info['wara_triple']}")
        print(f"TU-PA-A    : {'YES' if info['is_tu_pa_a'] else 'NO'}")
        print("=" * 60)


# ============================================================================
# FUNGSI UTILITY CEPAT
# ============================================================================

def get_wara_triple_for_date(year: int, month: int, day: int,
                              calendar_type: str = "gregorian") -> str:
    """Fungsi cepat untuk mendapatkan triple wara"""
    engine = WukuMechanicalEngine()
    return engine.get_wara_triple_from_date(year, month, day, calendar_type)

def find_tu_pa_a_dates(year: int, calendar_type: str = "gregorian") -> List[Tuple[int, int, int]]:
    """Fungsi cepat untuk mencari tanggal TU-PA-A"""
    engine = WukuMechanicalEngine()
    tpa_list = engine.find_tu_pa_a_in_year(year, calendar_type)
    return [tpa['date'] for tpa in tpa_list]

def calculate_wuku_phase(year: int, month: int, day: int,
                         calendar_type: str = "gregorian") -> Dict[str, Any]:
    """Menghitung fase wuku lengkap"""
    engine = WukuMechanicalEngine()
    info = engine.get_wuku_by_date(year, month, day, calendar_type)
    phase_in_wuku = info['day_in_wuku'] / 7
    phase_in_cycle = info['wuku_index'] / 210
    ka = engine.date_to_ka(year, month, day, calendar_type)
    next_tpa = engine.find_next_tu_pa_a(from_ka=ka, calendar_type=calendar_type)
    info.update({
        'phase_in_wuku': phase_in_wuku,
        'phase_in_cycle': phase_in_cycle,
        'days_to_next_tu_pa_a': next_tpa['days_until'],
        'next_tu_pa_a_date': next_tpa['date']
    })
    return info

def get_days_to_next_tu_pa_a(year: int, month: int, day: int,
                              calendar_type: str = "gregorian") -> int:
    """Fungsi cepat untuk mendapatkan hari hingga TU-PA-A berikutnya."""
    engine = WukuMechanicalEngine()
    return engine.get_days_to_next_tu_pa_a_from_date(year, month, day, calendar_type)

def get_days_since_wuku_epoch(year: int, month: int, day: int,
                               calendar_type: str = "gregorian") -> int:
    """Fungsi cepat untuk mendapatkan hari sejak epoch wuku."""
    engine = WukuMechanicalEngine()
    return engine.get_days_since_wuku_epoch_from_date(year, month, day, calendar_type)

def get_wuku_phase(year: int, month: int, day: int,
                   calendar_type: str = "gregorian") -> Dict[str, Any]:
    """Fungsi cepat untuk mendapatkan fase wuku lengkap."""
    engine = WukuMechanicalEngine()
    ka = engine.date_to_ka(year, month, day, calendar_type)
    wuku_info = engine.get_wuku_by_ka(ka)
    phase_percent = engine.get_wuku_phase_percentage(ka)
    epoch_info = engine.get_detailed_wuku_epoch_info(ka)
    days_to_next_tpa = engine.get_days_to_next_tu_pa_a(ka)
    
    result = {
        'date': f"{year:04d}-{month:02d}-{day:02d}",
        'ka': ka,
        'wuku_info': wuku_info,
        'phase_percentage': phase_percent,
        'epoch_relation': epoch_info,
        'days_to_next_tu_pa_a': days_to_next_tpa,
        'next_tu_pa_a_info': None
    }
    if days_to_next_tpa > 0:
        next_ka = ka + days_to_next_tpa
        next_info = engine.get_wuku_by_ka(next_ka)
        next_info['date'] = engine.ka_to_date(next_ka, calendar_type)
        result['next_tu_pa_a_info'] = next_info
    return result

def quick_wuku_lookup(date_str: str, calendar_type: str = "gregorian") -> Dict[str, Any]:
    """Lookup cepat dari string tanggal (format: YYYY-MM-DD)"""
    try:
        if date_str.startswith('-'):
            parts = date_str[1:].split('-')
            year = -int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
        else:
            year, month, day = map(int, date_str.split('-'))
        engine = WukuMechanicalEngine()
        return engine.get_wuku_by_date(year, month, day, calendar_type)
    except:
        return {"error": "Format tanggal tidak valid. Gunakan YYYY-MM-DD atau -YYYY-MM-DD untuk tahun BC"}

def batch_wuku_calculation(dates: List[str],
                           calendar_type: str = "gregorian") -> List[Dict[str, Any]]:
    """Perhitungan batch untuk beberapa tanggal"""
    engine = WukuMechanicalEngine()
    results = []
    for date_str in dates:
        try:
            if date_str.startswith('-'):
                parts = date_str[1:].split('-')
                year = -int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
            else:
                year, month, day = map(int, date_str.split('-'))
            result = engine.get_wuku_by_date(year, month, day, calendar_type)
            result['input_date'] = date_str
            results.append(result)
        except:
            results.append({"error": f"Invalid date: {date_str}", "input_date": date_str})
    return results

def wuku_realtime_info():
    """Menampilkan informasi wuku untuk waktu sekarang (berdasarkan zona lokal)."""
    engine = WukuMechanicalEngine()
    # Ambil waktu lokal sistem (dengan zona waktu)
    now_local = datetime.now().astimezone()
    now_utc = now_local.astimezone(timezone.utc)

    # Hitung wuku berdasarkan tanggal lokal
    year = now_local.year
    month = now_local.month
    day = now_local.day
    info = engine.get_wuku_by_date(year, month, day, "gregorian")
    ka = info['ka']
    jd = info['julian_day']

    # Dapatkan informasi epoch detail
    epoch_info = engine.get_detailed_wuku_epoch_info(ka)

    # Hitung next TU-PA-A
    next_tpa_ka = ka + epoch_info['days_to_next_tu_pa_a']
    next_tpa_date = engine.ka_to_date(next_tpa_ka)

    # Format tanggal
    date_local_str = format_date_display(year, month, day)
    time_local_str = now_local.strftime("%H:%M:%S %Z")
    date_utc_str = format_date_display(now_utc.year, now_utc.month, now_utc.day)
    time_utc_str = now_utc.strftime("%H:%M:%S UTC")

    print("\n" + "="*100)
    print("INFORMASI WUKU REALTIME (SEKARANG)")
    print("="*100)
    print(f"\n[WAKTU LOKAL]")
    print(f"  Tanggal : {date_local_str}")
    print(f"  Jam     : {time_local_str}")
    print(f"\n[WAKTU UTC]")
    print(f"  Tanggal : {date_utc_str}")
    print(f"  Jam     : {time_utc_str}")
    print(f"\n  JD      : {jd:.6f}")
    print(f"  KA      : {ka:,}")

    print(f"\n[INFORMASI WUKU]")
    print(f"  Wuku: {info['wuku_name']} (#{info['wuku_number']})")
    print(f"  Hari dalam Wuku: {info['day_in_wuku']}/7")
    print(f"  Wara Triple: {info['wara_triple_full']}")
    print(f"  Kode Triple: {info['wara_triple']}")
    print(f"  TU-PA-A: {'YA (Sekarang TU-PA-A)' if info['is_tu_pa_a'] else 'TIDAK'}")

    print(f"\n[POSISI RELATIF TERHADAP EPOCH WUKU]")
    print(f"  Hari sejak epoch: {epoch_info['days_since_epoch']:,} hari")
    print(f"  Arah waktu: {epoch_info['direction']}")
    print(f"  Siklus Wuku: {epoch_info['cycle_number']}")
    print(f"  Posisi dalam siklus: {epoch_info['position_in_cycle']}/210")
    print(f"  Hari dalam siklus: {epoch_info['day_in_cycle']}/210")
    print(f"  Progres siklus: {epoch_info['progress_percent']:.1f}%")

    print(f"\n[INFORMASI TU-PA-A]")
    print(f"  Status: {epoch_info['interpretation']['tpa_status']}")
    if not info['is_tu_pa_a']:
        print(f"  Hari ke TU-PA-A berikutnya: {epoch_info['days_to_next_tu_pa_a']} hari")
        print(f"  Tanggal TU-PA-A berikutnya: {format_date_display(*next_tpa_date)}")
        print(f"  KA TU-PA-A berikutnya: {next_tpa_ka:,}")

    print(f"\n[EPOCH WUKU (REFERENSI)]")
    print(f"  Tanggal Epoch: {epoch_info['epoch_date_formatted']}")
    print(f"  KA Epoch: {epoch_info['ka_epoch']:,}")
    print(f"  Deskripsi: {epoch_info['epoch_description']}")

    print(f"\n[INTERPRETASI]")
    print(f"  {epoch_info['interpretation']['direction_text']}")
    print(f"  {epoch_info['interpretation']['cycle_text']}")
    print(f"  {epoch_info['interpretation']['progress_text']}")

    phase_info = engine.get_wuku_phase_percentage(ka)
    print(f"\n[FASE WUKU TAMBAHAN]")
    print(f"  Progres siklus 210-hari: {phase_info['cycle_210_day_percent']:.1f}%")
    print(f"  Progres wuku 7-hari: {phase_info['wuku_7_day_percent']:.1f}%")
    print(f"  {phase_info['interpretation']['day_in_wuku_text']}")
    print("="*100)

# ============================================================================
# FUNGSI OFFSET CEPAT (UNTUK DIPANGGIL LANGSUNG)
# ============================================================================

def offset_solar_days(date_str: str, days: int, calendar_type: str = "gregorian") -> Dict[str, Any]:
    """Menambahkan hari solar ke tanggal (format YYYY-MM-DD)."""
    engine = WukuMechanicalEngine()
    year, month, day = map(int, date_str.split('-'))
    ka = engine.date_to_ka(year, month, day, calendar_type)
    return engine.add_solar_days(ka, days)

def offset_solar_months(date_str: str, months: int, calendar_type: str = "gregorian") -> Dict[str, Any]:
    """Menambahkan bulan solar rata‑rata ke tanggal."""
    engine = WukuMechanicalEngine()
    year, month, day = map(int, date_str.split('-'))
    ka = engine.date_to_ka(year, month, day, calendar_type)
    return engine.add_solar_months(ka, months)

def offset_solar_years(date_str: str, years: int, calendar_type: str = "gregorian") -> Dict[str, Any]:
    """Menambahkan tahun solar rata‑rata ke tanggal."""
    engine = WukuMechanicalEngine()
    year, month, day = map(int, date_str.split('-'))
    ka = engine.date_to_ka(year, month, day, calendar_type)
    return engine.add_solar_years(ka, years)

def offset_lunar_months(date_str: str, months: int, calendar_type: str = "gregorian") -> Dict[str, Any]:
    """Menambahkan bulan sinodik rata‑rata ke tanggal."""
    engine = WukuMechanicalEngine()
    year, month, day = map(int, date_str.split('-'))
    ka = engine.date_to_ka(year, month, day, calendar_type)
    return engine.add_lunar_months(ka, months)

def offset_lunar_years(date_str: str, years: int, calendar_type: str = "gregorian") -> Dict[str, Any]:
    """Menambahkan tahun lunar (12 sinodik) rata‑rata ke tanggal."""
    engine = WukuMechanicalEngine()
    year, month, day = map(int, date_str.split('-'))
    ka = engine.date_to_ka(year, month, day, calendar_type)
    return engine.add_lunar_years(ka, years)

def offset_tithi(date_str: str, tithi: int, calendar_type: str = "gregorian") -> Dict[str, Any]:
    """Menambahkan tithi rata‑rata ke tanggal."""
    engine = WukuMechanicalEngine()
    year, month, day = map(int, date_str.split('-'))
    ka = engine.date_to_ka(year, month, day, calendar_type)
    return engine.add_tithi(ka, tithi)


# ============================================================================
# MENU INTERFACE DAN FUNGSI UTILITAS - VERSI DIPERBAIKI DENGAN SISTEM WUKU
# ============================================================================

def format_date_display(year: int, month: int, day: int) -> str:
    """Format tanggal untuk display"""
    if year <= 0:
        year_display = f"{1-year} SM"
    else:
        year_display = f"{year} M"
    return f"{year_display}-{month:02d}-{day:02d}"

def display_conversion_menu():
    print("\n" + "="*100)
    print("KONVERSI JD <-> KA <-> TANGGAL")
    print("="*100)
    print("1. JD ke Tanggal Gregorian/Julian")
    print("2. Tanggal ke JD")
    print("3. JD ke KA")
    print("4. KA ke JD")
    print("5. KA ke Tanggal")
    print("6. Tanggal ke KA")
    print("7. Informasi Wuku Lengkap (dengan hari sejak epoch)")
    print("8. Kembali ke menu utama")
    print("="*100)

def jd_to_date_conversion():
    try:
        jd = float(input("Masukkan Julian Day: "))
        engine = WukuMechanicalEngine()
        if jd < 2299160.5:
            calendar_type = "julian"
        else:
            calendar_type = "gregorian"
        year, month, day = engine.converter.jd_to_date(jd, calendar_type)
        date_str = format_date_display(year, month, day)
        print(f"\nHasil Konversi:")
        print(f"JD: {jd:.6f}")
        print(f"Tanggal: {date_str}")
        print(f"Kalender: {calendar_type.capitalize()}")
        ka = engine.julian_day_to_ka(jd)
        print(f"KA: {ka:,}")
        wuku_info = engine.get_wuku_by_ka(ka)
        print(f"Wuku: {wuku_info['wuku_name']} ({wuku_info['wara_triple']})")
    except ValueError:
        print("Input tidak valid!")

def date_to_jd_conversion():
    try:
        year = int(input("Tahun (contoh: 2024, -100 untuk 101 SM): "))
        month = int(input("Bulan (1-12): "))
        day = int(input("Hari (1-31): "))
        hour = int(input("Jam (0-23, default 0): ") or 0)
        minute = int(input("Menit (0-59, default 0): ") or 0)
        second = int(input("Detik (0-59, default 0): ") or 0)
        
        engine = WukuMechanicalEngine()
        if year < 1582 or (year == 1582 and month < 10) or (year == 1582 and month == 10 and day < 15):
            calendar_type = "julian"
        else:
            calendar_type = "gregorian"
        
        jd = engine.converter.date_to_jd(year, month, day, calendar_type)
        day_fraction = (hour + minute/60.0 + second/3600.0) / 24.0
        jd += day_fraction
        ka = engine.julian_day_to_ka(jd)
        date_str = format_date_display(year, month, day)
        
        print(f"\nHasil Konversi:")
        print(f"Tanggal: {date_str} {hour:02d}:{minute:02d}:{second:02d}")
        print(f"Kalender: {calendar_type.capitalize()}")
        print(f"JD: {jd:.6f}")
        print(f"KA: {ka:,}")
        wuku_info = engine.get_wuku_by_ka(ka)
        print(f"Wuku: {wuku_info['wuku_name']} ({wuku_info['wara_triple']})")
    except ValueError:
        print("Input tidak valid!")

def jd_to_ka_conversion():
    try:
        jd = float(input("Masukkan Julian Day: "))
        engine = WukuMechanicalEngine()
        ka = engine.julian_day_to_ka(jd)
        print(f"\nHasil Konversi:")
        print(f"JD: {jd:.6f}")
        print(f"KA: {ka:,}")
        if jd < 2299160.5:
            calendar_type = "julian"
        else:
            calendar_type = "gregorian"
        year, month, day = engine.converter.jd_to_date(jd, calendar_type)
        date_str = format_date_display(year, month, day)
        print(f"Tanggal: {date_str}")
        wuku_info = engine.get_wuku_by_ka(ka)
        print(f"Wuku: {wuku_info['wuku_name']} ({wuku_info['wara_triple']})")
    except ValueError:
        print("Input tidak valid!")

def ka_to_jd_conversion():
    try:
        ka = int(input("Masukkan KA: "))
        engine = WukuMechanicalEngine()
        jd = engine.ka_to_julian_day(ka)
        print(f"\nHasil Konversi:")
        print(f"KA: {ka:,}")
        print(f"JD: {jd:.6f}")
        year, month, day = engine.ka_to_date(ka)
        date_str = format_date_display(year, month, day)
        print(f"Tanggal: {date_str}")
        wuku_info = engine.get_wuku_by_ka(ka)
        print(f"Wuku: {wuku_info['wuku_name']} ({wuku_info['wara_triple']})")
    except ValueError:
        print("Input tidak valid!")

def ka_to_date_conversion():
    try:
        ka = int(input("Masukkan KA: "))
        engine = WukuMechanicalEngine()
        year, month, day = engine.ka_to_date(ka)
        date_str = format_date_display(year, month, day)
        print(f"\nHasil Konversi:")
        print(f"KA: {ka:,}")
        print(f"Tanggal: {date_str}")
        print(f"Tahun: {year}")
        print(f"Bulan: {month:02d}")
        print(f"Hari: {day:02d}")
        print(f"JD: {engine.ka_to_julian_day(ka):.6f}")
        wuku_info = engine.get_wuku_by_ka(ka)
        print(f"Wuku: {wuku_info['wuku_name']} ({wuku_info['wara_triple']})")
    except ValueError:
        print("Input tidak valid!")

def date_to_ka_conversion():
    try:
        year = int(input("Tahun (contoh: 2024, -100 untuk 101 SM): "))
        month = int(input("Bulan (1-12): "))
        day = int(input("Hari (1-31): "))
        engine = WukuMechanicalEngine()
        ka = engine.date_to_ka(year, month, day)
        jd = engine.ka_to_julian_day(ka)
        date_str = format_date_display(year, month, day)
        print(f"\nHasil Konversi:")
        print(f"Tanggal: {date_str}")
        print(f"KA: {ka:,}")
        print(f"JD: {jd:.6f}")
        wuku_info = engine.get_wuku_by_ka(ka)
        print(f"Wuku: {wuku_info['wuku_name']} ({wuku_info['wara_triple']})")
    except ValueError:
        print("Input tidak valid!")

def wuku_extended_info():
    try:
        year = int(input("Tahun (contoh: 2024, -100 untuk 101 SM): "))
        month = int(input("Bulan (1-12): "))
        day = int(input("Hari (1-31): "))
        engine = WukuMechanicalEngine()
        ka = engine.date_to_ka(year, month, day)
        epoch_info = engine.get_detailed_wuku_epoch_info(ka)
        wuku_info = engine.get_wuku_by_ka(ka)
        next_tpa_ka = ka + epoch_info['days_to_next_tu_pa_a']
        next_tpa_date = engine.ka_to_date(next_tpa_ka)
        date_str = format_date_display(year, month, day)
        
        print("\n" + "="*100)
        print("INFORMASI WUKU LENGKAP DENGAN DETAIL EPOCH")
        print("="*100)
        print(f"\n[INFORMASI TANGGAL]")
        print(f"  Tanggal Input: {date_str}")
        print(f"  KA: {ka:,}")
        print(f"  JD: {engine.ka_to_julian_day(ka):.6f}")
        
        print(f"\n[INFORMASI WUKU]")
        print(f"  Wuku: {wuku_info['wuku_name']} (#{wuku_info['wuku_number']})")
        print(f"  Hari dalam Wuku: {wuku_info['day_in_wuku']}/7")
        print(f"  Wara Triple: {wuku_info['wara_triple_full']}")
        print(f"  Kode Triple: {wuku_info['wara_triple']}")
        print(f"  TU-PA-A: {'YA (Hari ini TU-PA-A)' if wuku_info['is_tu_pa_a'] else 'TIDAK'}")
        
        print(f"\n[POSISI RELATIF TERHADAP EPOCH WUKU]")
        print(f"  Hari sejak epoch: {epoch_info['days_since_epoch']:,} hari")
        print(f"  Arah waktu: {epoch_info['direction']}")
        print(f"  Siklus Wuku: {epoch_info['cycle_number']}")
        print(f"  Posisi dalam siklus: {epoch_info['position_in_cycle']}/210")
        print(f"  Hari dalam siklus: {epoch_info['day_in_cycle']}/210")
        print(f"  Progres siklus: {epoch_info['progress_percent']:.1f}%")
        
        print(f"\n[INFORMASI TU-PA-A]")
        print(f"  Status: {epoch_info['interpretation']['tpa_status']}")
        if not epoch_info['is_tu_pa_a_today']:
            print(f"  Hari ke TU-PA-A berikutnya: {epoch_info['days_to_next_tu_pa_a']} hari")
            print(f"  Tanggal TU-PA-A berikutnya: {format_date_display(*next_tpa_date)}")
            print(f"  KA TU-PA-A berikutnya: {next_tpa_ka:,}")
        
        print(f"\n[EPOCH WUKU (REFERENSI)]")
        print(f"  Tanggal Epoch: {epoch_info['epoch_date_formatted']}")
        print(f"  KA Epoch: {epoch_info['ka_epoch']:,}")
        print(f"  Deskripsi: {epoch_info['epoch_description']}")
        
        print(f"\n[INTERPRETASI]")
        print(f"  {epoch_info['interpretation']['direction_text']}")
        print(f"  {epoch_info['interpretation']['cycle_text']}")
        print(f"  {epoch_info['interpretation']['progress_text']}")
        
        phase_info = engine.get_wuku_phase_percentage(ka)
        print(f"\n[FASE WUKU TAMBAHAN]")
        print(f"  Progres siklus 210-hari: {phase_info['cycle_210_day_percent']:.1f}%")
        print(f"  Progres wuku 7-hari: {phase_info['wuku_7_day_percent']:.1f}%")
        print(f"  {phase_info['interpretation']['day_in_wuku_text']}")
        print("="*100)
    except Exception as e:
        print(f"ERROR: {e}")

def display_wuku_menu():
    print("\n" + "="*100)
    print("SISTEM WUKU (210-hari)")
    print("="*100)
    print("1. Hitung Wuku untuk tanggal tertentu")
    print("2. Cari TU-PA-A dalam tahun tertentu")
    print("3. Informasi Wuku lengkap (dengan hari sejak epoch)")
    print("4. Konversi JD-KA-Tanggal")
    print("5. Cari TU-PA-A dalam rentang hari")
    print("6. Wuku Realtime (sekarang)")
    print("7. Offset Waktu (hitung tanggal baru)")   # <-- BARU
    print("8. Kembali ke menu utama")                 # <-- GESER
    print("="*100)

def wuku_offset_menu():
    """Submenu untuk menghitung offset waktu"""
    print("\n" + "="*100)
    print("OFFSET WAKTU - Hitung tanggal baru + informasi wuku")
    print("="*100)
    print("Pilih jenis offset:")
    print("1. Hari solar (hari biasa)")
    print("2. Bulan solar rata-rata (30.44 hari)")
    print("3. Tahun solar rata-rata (365.24 hari)")
    print("4. Bulan lunar (sinodik) rata-rata (29.53 hari)")
    print("5. Tahun lunar rata-rata (354.37 hari)")
    print("6. Tithi rata-rata (0.984 hari)")
    print("7. Kembali")
    print("="*100)

def wuku_offset_calculation():
    """Fungsi untuk menghitung offset berdasarkan pilihan user"""
    try:
        # Input tanggal awal
        year = int(input("Tahun awal (contoh: 2024, -100 untuk 101 SM): "))
        month = int(input("Bulan awal (1-12): "))
        day = int(input("Hari awal (1-31): "))
        
        # Tampilkan submenu offset
        wuku_offset_menu()
        pilihan = input("Pilih jenis offset (1-7): ").strip()
        if pilihan == '7':
            return
        
        jumlah = int(input("Jumlah offset (bisa positif/negatif): "))
        
        engine = WukuMechanicalEngine()
        ka_awal = engine.date_to_ka(year, month, day)
        
        # Panggil fungsi sesuai pilihan
        if pilihan == '1':
            info = engine.add_solar_days(ka_awal, jumlah)
            jenis = "hari solar"
        elif pilihan == '2':
            info = engine.add_solar_months(ka_awal, jumlah)
            jenis = "bulan solar"
        elif pilihan == '3':
            info = engine.add_solar_years(ka_awal, jumlah)
            jenis = "tahun solar"
        elif pilihan == '4':
            info = engine.add_lunar_months(ka_awal, jumlah)
            jenis = "bulan lunar"
        elif pilihan == '5':
            info = engine.add_lunar_years(ka_awal, jumlah)
            jenis = "tahun lunar"
        elif pilihan == '6':
            info = engine.add_tithi(ka_awal, jumlah)
            jenis = "tithi"
        else:
            print("Pilihan tidak valid.")
            return
        
        # Tampilkan hasil
        print(f"\nHASIL OFFSET {jumlah} {jenis}:")
        print("="*50)
        print(f"Tanggal awal : {format_date_display(year, month, day)}")
        print(f"KA awal      : {ka_awal:,}")
        print(f"\nTanggal baru : {format_date_display(*info['date'])}")
        print(f"KA baru      : {info['ka']:,}")
        print(f"Wuku         : {info['wuku_name']} (#{info['wuku_number']})")
        print(f"Hari dalam Wuku: {info['day_in_wuku']}/7")
        print(f"Wara Triple  : {info['wara_triple_full']}")
        print(f"Kode Triple  : {info['wara_triple']}")
        print(f"TU-PA-A      : {'YA' if info['is_tu_pa_a'] else 'TIDAK'}")
        print("="*50)
        
    except ValueError:
        print("Input tidak valid!")
    except Exception as e:
        print(f"Error: {e}")

def wuku_calculation():
    try:
        year = int(input("Tahun (contoh: 2024, -100 untuk 101 SM): "))
        month = int(input("Bulan (1-12): "))
        day = int(input("Hari (1-31): "))
        engine = WukuMechanicalEngine()
        info = engine.get_wuku_by_date(year, month, day)
        date_str = format_date_display(year, month, day)
        print(f"\nHASIL PERHITUNGAN WUKU:")
        print("="*50)
        print(f"Tanggal: {date_str}")
        print(f"KA: {info['ka']:,}")
        print(f"JD: {info['julian_day']:.6f}")
        print()
        print(f"Wuku: {info['wuku_name']} (#{info['wuku_number']})")
        print(f"Hari dalam Wuku: {info['day_in_wuku']}/7")
        print(f"Wara Triple: {info['wara_triple_full']}")
        print(f"Kode Triple: {info['wara_triple']}")
        print(f"TU-PA-A: {'YA' if info['is_tu_pa_a'] else 'TIDAK'}")
        days_to_next = engine.get_days_to_next_tu_pa_a(info['ka'])
        if days_to_next > 0:
            print(f"Hari ke TU-PA-A berikutnya: {days_to_next} hari")
        print("="*50)
    except ValueError:
        print("Input tidak valid!")

def find_tu_pa_a_year():
    try:
        year = int(input("Tahun (contoh: 2024): "))
        engine = WukuMechanicalEngine()
        tpa_list = engine.find_tu_pa_a_in_year(year)
        print(f"\nTU-PA-A dalam tahun {year}:")
        print("="*60)
        if not tpa_list:
            print("Tidak ditemukan TU-PA-A pada tahun ini.")
        else:
            for i, tpa in enumerate(tpa_list, 1):
                date_info = tpa.get('date')
                if isinstance(date_info, tuple) and len(date_info) >= 3:
                    y, m, d = date_info[0], date_info[1], date_info[2]
                    date_str = format_date_display(y, m, d)
                else:
                    date_str = str(date_info)
                print(f"{i}. {date_str}")
                print(f"   KA: {tpa.get('ka', 'N/A'):,}")
                print(f"   Wuku: {tpa.get('wuku_name', 'N/A')}")
                print(f"   Wara: {tpa.get('wara_triple', 'N/A')}")
                print()
        print("="*60)
    except ValueError:
        print("Input tidak valid!")

def find_tu_pa_a_in_range():
    try:
        year = int(input("Tahun awal (contoh: 2024): "))
        month = int(input("Bulan awal (1-12): "))
        day = int(input("Hari awal (1-31): "))
        max_days = int(input("Rentang hari pencarian (default 365): ") or 365)
        engine = WukuMechanicalEngine()
        ka_start = engine.date_to_ka(year, month, day)
        tu_pa_a_list = engine.find_tu_pa_a_within_days(ka_start, max_days)
        print(f"\nTU-PA-A dalam {max_days} hari dari {format_date_display(year, month, day)}:")
        print("="*70)
        if not tu_pa_a_list:
            print("Tidak ditemukan TU-PA-A dalam rentang ini.")
        else:
            for i, tpa_info in enumerate(tu_pa_a_list, 1):
                date_info = tpa_info['date']
                date_str = format_date_display(*date_info)
                days_from_start = tpa_info['days_from_start']
                print(f"{i}. {date_str}")
                print(f"   KA: {tpa_info['ka']:,}")
                print(f"   Hari dari awal: {days_from_start}")
                print(f"   Wuku: {tpa_info['wuku_name']} ({tpa_info['wara_triple']})")
                print()
        print("="*70)
    except ValueError:
        print("Input tidak valid!")

def main_menu():
    while True:
        print("\n" + "="*100)
        print("Ω-WUKU ENGINE INFINITE - SISTEM WUKU 210 HARI")
        print("="*100)
        print("1. Sistem Wuku")
        print("2. Konversi JD-KA-Tanggal")
        print("3. Wuku Realtime")
        print("4. Keluar")
        print("="*100)
        pilihan = input("Pilih menu (1-4): ").strip()

        if pilihan == '1':
            while True:
                display_wuku_menu()
                sub = input("Pilih submenu (1-7): ").strip()
                if sub == '1':
                    wuku_calculation()
                elif sub == '2':
                    find_tu_pa_a_year()
                elif sub == '3':
                    wuku_extended_info()
                elif sub == '4':
                    while True:
                        display_conversion_menu()
                        conv = input("Pilih konversi (1-8): ").strip()
                        if conv == '1':
                            jd_to_date_conversion()
                        elif conv == '2':
                            date_to_jd_conversion()
                        elif conv == '3':
                            jd_to_ka_conversion()
                        elif conv == '4':
                            ka_to_jd_conversion()
                        elif conv == '5':
                            ka_to_date_conversion()
                        elif conv == '6':
                            date_to_ka_conversion()
                        elif conv == '7':
                            wuku_extended_info()
                        elif conv == '8':
                            break
                        else:
                            print("Pilihan tidak valid!")
                        input("\nTekan Enter untuk melanjutkan...")
                elif sub == '5':
                    find_tu_pa_a_in_range()
                elif sub == '6':
                    wuku_realtime_info()
                elif sub == '7':
                    wuku_offset_calculation()
                elif sub == '8':
                    break
                else:
                    print("Pilihan tidak valid!")
                input("\nTekan Enter untuk melanjutkan...")
        elif pilihan == '2':
            while True:
                display_conversion_menu()
                conv = input("Pilih konversi (1-8): ").strip()
                if conv == '1':
                    jd_to_date_conversion()
                elif conv == '2':
                    date_to_jd_conversion()
                elif conv == '3':
                    jd_to_ka_conversion()
                elif conv == '4':
                    ka_to_jd_conversion()
                elif conv == '5':
                    ka_to_date_conversion()
                elif conv == '6':
                    date_to_ka_conversion()
                elif conv == '7':
                    wuku_extended_info()
                elif conv == '8':
                    break
                else:
                    print("Pilihan tidak valid!")
                input("\nTekan Enter untuk melanjutkan...")
        elif pilihan == '3':
            wuku_realtime_info()
            input("\nTekan Enter untuk melanjutkan...")
        elif pilihan == '4':
            print("Terima kasih telah menggunakan Ω-WUKU ENGINE.")
            break
        else:
            print("Pilihan tidak valid!")
            input("\nTekan Enter untuk melanjutkan...")

if __name__ == "__main__":
    main_menu()