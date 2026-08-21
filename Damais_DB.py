"""
DAMAIS DATABASE - 112 PRASASTI LENGKAP DENGAN SEMUA FIELD
Semua data prasasti konversi Damais - DIKOREKSI UNTUK KONSISTENSI DENGAN OJCC
"""

import json

DAMAIS_INSCRIPTIONS = [
    # ============================================================
    # PRASASTI 1-50
    # ============================================================
    {
        "no": 1, "id": "A.8", "name": "Kamalagi", "saka": 743,
        "masa": "Vaisakha", "tithi": 10, "paksa": "Krsna",
        "wara_string": "Tungleh-Wage-Anggara",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (821, 4, 30), "category": "1.a"
    },
    {
        "no": 2, "id": "A.12", "name": "Kuti", "saka": 762,
        "masa": "Sravana", "tithi": 15, "paksa": "Sukla",
        "wara_string": "Maulu-Pon-Aditya",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": "Prangbakat",
        "julian_date": (840, 7, 18), "category": "1.a"
    },
    {
        "no": 3, "id": "A.15", "name": "Payung Perak (Parasol)", "saka": 765,
        "masa": "Caitra", "tithi": 15, "paksa": "Sukla",
        "wara_string": "Haryang-Pahing-Soma",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (843, 3, 19), "category": "1.a"
    },
    {
        "no": 4, "id": "A.17_18", "name": "Tulang Air I & II", "saka": 772,
        "masa": "Asadha", "tithi": 2, "paksa": "Sukla",
        "wara_string": "Tungleh-Pahing-Aditya",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": "Sinta",
        "julian_date": (850, 6, 15), "category": "1.a", "is_anchor": True
    },
    {
        "no": 5, "id": "A.19", "name": "Wayuku", "saka": 776,
        "masa": "Caitra", "tithi": 14, "paksa": "Sukla",
        "wara_string": "Wurukung-Pahing-Sukra",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (854, 3, 16), "category": "1.a"
    },
    {
        "no": 6, "id": "A.20", "name": "Śiwagṛha", "saka": 778,
        "masa": "Margasira", "tithi": 11, "paksa": "Sukla",
        "wara_string": "Wurukung-Wage-Wrhaspati",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (856, 11, 12), "category": "1.a"
    },
    {
        "no": 7, "id": "A.22", "name": "Bulai C", "saka": 782,
        "masa": "Vaisakha", "tithi": 2, "paksa": "Sukla",
        "wara_string": "Paniron-Kaliwon-Budha",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (860, 3, 27), "category": "1.a"
    },
    {
        "no": 8, "id": "A.23", "name": "Kañcana (Bungur A)", "saka": 782,
        "masa": "Kartika", "tithi": 13, "paksa": "Sukla",
        "wara_string": "Maulu-Pon-Wrhaspati",
        "nakshatra": "Aswini", "yoga": "Wyatipata", "karana": "Taitila",
        "wuku": None, "julian_date": (860, 10, 31), "category": "1.a"
    },
    {
        "no": 9, "id": "A.25", "name": "Talaga Tañjung", "saka": 783,
        "masa": "Magha", "tithi": 1, "paksa": "Sukla",
        "wara_string": "Was-Wage-Soma",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (862, 1, 5), "category": "1.a"
    },
    {
        "no": 10, "id": "A.27_28", "name": "Wanua Těngah I & II", "saka": 785,
        "masa": "Jyestha", "tithi": 5, "paksa": "Krsna",
        "wara_string": "Paniron-Kaliwon-Wrhaspati",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (863, 6, 10), "category": "1.a"
    },
    {
        "no": 11, "id": "A.32", "name": "Candi Abang", "saka": 794,
        "masa": "Bhadrapada", "tithi": 4, "paksa": "Krsna",
        "wara_string": "Wurukung-Kaliwon-Anggara",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (872, 8, 26), "category": "1.a"
    },
    {
        "no": 12, "id": "A.33", "name": "Tunahan (Polengan I)", "saka": 794,
        "masa": "Magha", "tithi": 12, "paksa": "Sukla",
        "wara_string": "Maulu-Umanis-Budha",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (873, 1, 14), "category": "1.a"
    },
    {
        "no": 13, "id": "A.34", "name": "Waharu I", "saka": 795,
        "masa": "Vaisakha", "tithi": 5, "paksa": "Krsna",
        "wara_string": "Maulu-Pahing-Soma",
        "nakshatra": "Mula", "yoga": "Siddhiyoga", "karana": None,
        "wuku": "Manahil", "julian_date": (873, 4, 20), "category": "1.a"
    },
    {
        "no": 14, "id": "A.35", "name": "Śrī Manggala II", "saka": 796,
        "masa": "Caitra", "tithi": 2, "paksa": "Sukla",
        "wara_string": "Haryang-Kaliwon-Budha",
        "nakshatra": "Krittika", "yoga": None, "karana": None, "wuku": None,
        "julian_date": (874, 3, 24), "category": "1.a"
    },
    {
        "no": 15, "id": "A.37", "name": "Anggěhan", "saka": 796,
        "masa": "Phalguna", "tithi": 1, "paksa": "Krsna",
        "wara_string": "Paniron-Pon-Sukra",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (875, 2, 25), "category": "1.a"
    },
    {
        "no": 16, "id": "A.38", "name": "Humanding (Polengan II)", "saka": 797,
        "masa": "Vaisakha", "tithi": 2, "paksa": "Sukla",
        "wara_string": "Tungleh-Pon-Soma",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (875, 4, 11), "category": "1.a"
    },
    {
        "no": 17, "id": "A.39", "name": "Jurungan (Polengan III)", "saka": 798,
        "masa": "Pausa", "tithi": 11, "paksa": "Sukla",
        "wara_string": "Maulu-Pahing-Aditya",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (876, 12, 30), "category": "1.a"
    },
    {
        "no": 18, "id": "A.40", "name": "Haliwangbang (Polengan IV)", "saka": 799,
        "masa": "Margasira", "tithi": 13, "paksa": "Sukla",
        "wara_string": "Wurukung-Wage-Sukra",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (877, 11, 22), "category": "1.a"
    },
    {
        "no": 19, "id": "A.43", "name": "Mulak I", "saka": 800,
        "masa": "Kartika", "tithi": 3, "paksa": "Sukla",
        "wara_string": "Maulu-Wage-Sukra",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (878, 10, 3), "category": "1.a"
    },
    {
        "no": 20, "id": "A.44", "name": "Mamali (Polengan V)", "saka": 800,
        "masa": "Margasira", "tithi": 10, "paksa": "Krsna",
        "wara_string": "Wurukung-Kaliwon-Aditya",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (878, 11, 23), "category": "1.a"
    },
    {
        "no": 21, "id": "A.46", "name": "Kwak I", "saka": 801,
        "masa": "Sravana", "tithi": 5, "paksa": "Sukla",
        "wara_string": "Wurukung-Umanis-Soma",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (879, 7, 27), "category": "1.a"
    },
    {
        "no": 22, "id": "A.47", "name": "Kwak II", "saka": 801,
        "masa": "Sravana", "tithi": 5, "paksa": "Sukla",
        "wara_string": "Wurukung-Umanis-Soma",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (879, 7, 27), "category": "1.a"
    },
    {
        "no": 23, "id": "A.49", "name": "Salimar I", "saka": 802,
        "masa": "Kartika", "tithi": 3, "paksa": "Sukla",
        "wara_string": "Maulu-Pahing-Soma",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (880, 10, 10), "category": "1.a"
    },
    {
        "no": 24, "id": "A.50", "name": "Salimar II", "saka": 802,
        "masa": "Kartika", "tithi": 3, "paksa": "Sukla",
        "wara_string": "Maulu-Pahing-Soma",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (880, 10, 10), "category": "1.a"
    },
    {
        "no": 25, "id": "A.51", "name": "Salimar III", "saka": 802,
        "masa": "Kartika", "tithi": 3, "paksa": "Sukla",
        "wara_string": "Maulu-Pahing-Soma",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (880, 10, 10), "category": "1.a"
    },
    {
        "no": 26, "id": "A.53", "name": "Taragal (Polengan VI)", "saka": 802,
        "masa": "Phalguna", "tithi": 3, "paksa": "Krsna",
        "wara_string": "Tungleh-Kaliwon-Soma",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (881, 2, 20), "category": "1.a"
    },
    {
        "no": 27, "id": "A.54", "name": "Pěnděm", "saka": 803,
        "masa": "Caitra", "tithi": 15, "paksa": "Sukla",
        "wara_string": "Paniron-Pahing-Aditya",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (881, 3, 19), "category": "1.a"
    },
    {
        "no": 28, "id": "A.55", "name": "Ra Tawun I", "saka": 803,
        "masa": "Sravana", "tithi": 14, "paksa": "Sukla",
        "wara_string": "Tungleh-Wage-Sukra",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (881, 7, 14), "category": "1.a"
    },
    {
        "no": 29, "id": "A.56", "name": "Ra Tawun II", "saka": 803,
        "masa": "Sravana", "tithi": 14, "paksa": "Sukla",
        "wara_string": "Tungleh-Wage-Sukra",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (881, 7, 14), "category": "1.a"
    },
    {
        "no": 30, "id": "A.57", "name": "Paṣtika", "saka": 803,
        "masa": "Bhadrapada", "tithi": 2, "paksa": "Sukla",
        "wara_string": "Maulu-Umanis-Soma",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (881, 7, 31), "category": "1.a"
    },
    {
        "no": 31, "id": "A.58", "name": "Ra Mwi", "saka": 804,
        "masa": "Caitra", "tithi": 6, "paksa": "Sukla",
        "wara_string": "Tungleh-Pahing-Wrhaspati",
        "nakshatra": "Pushya", "yoga": "Waidhrti", "karana": None,
        "wuku": None, "julian_date": (882, 3, 29), "category": "1.a"
    },
    {
        "no": 32, "id": "A.61", "name": "Munggu Antan", "saka": 808,
        "masa": "Phalguna", "tithi": 13, "paksa": "Sukla",
        "wara_string": "Wurukung-Kaliwon-Wrhaspati",
        "nakshatra": "Pushya", "yoga": "Sobhana", "karana": None,
        "wuku": None, "julian_date": (887, 2, 9), "category": "1.a"
    },
    {
        "no": 33, "id": "A.63", "name": "Balingawan", "saka": 813,
        "masa": "Vaisakha", "tithi": 1, "paksa": "Sukla",
        "wara_string": "Wurukung-Wage-Anggara",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (891, 4, 13), "category": "1.a"
    },
    {
        "no": 34, "id": "A.66", "name": "Ayam Těas I", "saka": 822,
        "masa": "Pausa", "tithi": 8, "paksa": "Sukla",
        "wara_string": "Haryang-Kaliwon-Wrhaspati",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (901, 1, 1), "category": "1.a", "has_intercalation": True
    },
    {
        "no": 35, "id": "A.68", "name": "Taji", "saka": 823,
        "masa": "Caitra", "tithi": 2, "paksa": "Krsna",
        "wara_string": "Wurukung-Pahing-Budha",
        "nakshatra": "Anuradha", "yoga": "Wariyan", "karana": "Taitila",
        "wuku": None, "julian_date": (901, 4, 8), "category": "1.a"
    },
    {
        "no": 36, "id": "A.69", "name": "Kayu Ara Hiwang", "saka": 823,
        "masa": "Asvini", "tithi": 5, "paksa": "Krsna",  # DIPERBAIKI: "Asuji" → "Asvini"
        "wara_string": "Wurukung-Pahing-Soma",
        "nakshatra": "Mrgasira", "yoga": "Siwa", "karana": None,
        "wuku": None, "julian_date": (901, 10, 5), "category": "1.a"
    },
    {
        "no": 37, "id": "A.72", "name": "Panggumulan A", "saka": 824,
        "masa": "Pausa", "tithi": 10, "paksa": "Krsna",
        "wara_string": "Tungleh-Kaliwon-Soma",
        "nakshatra": "Jyeshtha", "yoga": "Sukarmma", "karana": None,
        "wuku": None, "julian_date": (902, 12, 27), "category": "1.a"
    },
    {
        "no": 38, "id": "A.74", "name": "Tělang II", "saka": 825,
        "masa": "Pausa", "tithi": 6, "paksa": "Krsna",
        "wara_string": "Wurukung-Kaliwon-Budha",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (904, 1, 11), "category": "1.a"
    },
    {
        "no": 39, "id": "A.76", "name": "Poh", "saka": 827,
        "masa": "Sravana", "tithi": 13, "paksa": "Sukla",
        "wara_string": "Paniron-Pon-Budha",
        "nakshatra": "Purva Ashadha", "yoga": "Wiskambha", "karana": None,
        "wuku": None, "julian_date": (905, 7, 17), "category": "1.a"
    },
    {
        "no": 40, "id": "A.77", "name": "Kubu Kubu", "saka": 827,
        "masa": "Kartika", "tithi": 1, "paksa": "Krsna",
        "wara_string": "Maulu-Kaliwon-Wrhaspati",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (905, 10, 17), "category": "1.a"
    },
    {
        "no": 41, "id": "A.78_79", "name": "Kikil Batu I & II", "saka": 827,
        "masa": "Margasira", "tithi": 14, "paksa": "Krsna",
        "wara_string": "Maulu-Pahing-Wrhaspati",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (905, 11, 28), "category": "1.a"
    },
    {
        "no": 42, "id": "A.81", "name": "Kandangan", "saka": 828,
        "masa": "Bhadrapada", "tithi": 5, "paksa": "Krsna",
        "wara_string": "Was-Wage-Wrhaspati",
        "nakshatra": "Swati", "yoga": "Byatipada", "karana": None,
        "wuku": None, "julian_date": (906, 9, 11), "category": "1.a"
    },
    {
        "no": 43, "id": "A.82", "name": "Mantyasih I", "saka": 829,
        "masa": "Caitra", "tithi": 11, "paksa": "Krsna",
        "wara_string": "Tungleh-Umanis-Saniscara",
        "nakshatra": "Purva Bhadrapada", "yoga": "Indra", "karana": None,
        "wuku": None, "julian_date": (907, 4, 11), "category": "1.a"
    },
    {
        "no": 44, "id": "A.84", "name": "Sangsang", "saka": 829,
        "masa": "Vaisakha", "tithi": 4, "paksa": "Krsna",
        "wara_string": "Maulu-Wage-Soma",
        "nakshatra": "Uttara Ashadha", "yoga": "Sukla", "karana": None,
        "wuku": None, "julian_date": (907, 5, 4), "category": "1.a"
    },
    {
        "no": 45, "id": "A.86", "name": "Kasugihan", "saka": 829,
        "masa": "Margasira", "tithi": 10, "paksa": "Sukla",
        "wara_string": "Maulu-Pahing-Budha",
        "nakshatra": "Aswini", "yoga": "Wariyan", "karana": None,
        "wuku": None, "julian_date": (907, 11, 18), "category": "1.a"
    },
    {
        "no": 46, "id": "A.87", "name": "Kiněwu (Ganesa)", "saka": 829,
        "masa": "Margasira", "tithi": 12, "paksa": "Sukla",
        "wara_string": "Haryang-Wage-Sukra",
        "nakshatra": "Bharani", "yoga": "Siddha", "karana": None,
        "wuku": None, "julian_date": (907, 11, 20), "category": "1.a"
    },
    {
        "no": 47, "id": "A.88", "name": "Kaladi", "saka": 831,
        "masa": "Asadha", "tithi": 8, "paksa": "Sukla",
        "wara_string": "Was-Wage-Anggara",
        "nakshatra": "Hasta", "yoga": "Siwa", "karana": "Wisti",
        "wuku": None, "julian_date": (909, 6, 27), "category": "1.a"
    },
    {
        "no": 48, "id": "A.91", "name": "Wuru Tunggal", "saka": 833,
        "masa": "Phalguna", "tithi": 2, "paksa": "Krsna",
        "wara_string": "Maulu-Wage-Aditya",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (912, 3, 8), "category": "1.a"
    },
    {
        "no": 49, "id": "A.93_94", "name": "Pěsindon I & II", "saka": 836,
        "masa": "Sravana", "tithi": 5, "paksa": "Krsna",
        "wara_string": "Tungleh-Pon-Aditya",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (914, 8, 14), "category": "1.a"
    },
    {
        "no": 50, "id": "A.95", "name": "Sugih Manek", "saka": 837,
        "masa": "Asvini", "tithi": 2, "paksa": "Sukla",  # DIPERBAIKI: "Asuji" → "Asvini"
        "wara_string": "Maulu-Pon-Budha",
        "nakshatra": "Chitra", "yoga": "Wedhrti", "karana": None,
        "wuku": None, "julian_date": (915, 9, 13), "category": "1.a"
    },
    # ============================================================
    # PRASASTI 51-112 (TAMBAHAN BARU)
    # ============================================================
    {
        "no": 51, "id": "A.80", "name": "Palĕpangan", "saka": 828,
        "masa": "Sravana", "tithi": 8, "paksa": "Krsna",
        "wara_string": "Haryang-Pahing-Sukra",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (906, 8, 15), "category": "1.a", "has_intercalation": True
    },
    {
        "no": 52, "id": "A.96", "name": "Kiringan", "saka": 839,
        "masa": "Kartika", "tithi": 12, "paksa": "Krsna",
        "wara_string": "Tungleh-Umanis-Sukra",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (917, 11, 14), "category": "1.a"
    },
    {
        "no": 53, "id": "A.97", "name": "Lintakan", "saka": 841,
        "masa": "Sravana", "tithi": 12, "paksa": "Sukla",
        "wara_string": "Maulu-Umanis-Soma",
        "nakshatra": "Mula", "yoga": "Waidhrti", "karana": None, "wuku": None,
        "julian_date": (919, 7, 12), "category": "1.a"
    },
    {
        "no": 54, "id": "A.98", "name": "Wintang Mas B", "saka": 841,
        "masa": "Kartika", "tithi": 15, "paksa": "Sukla",
        "wara_string": "Haryang-Pon-Anggara",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (919, 10, 12), "category": "1.a"
    },
    {
        "no": 55, "id": "A.99", "name": "Hariñjing B", "saka": 843,
        "masa": "Asvini", "tithi": 15, "paksa": "Sukla",  # DIPERBAIKI: "Asuji" → "Asvini"
        "wara_string": "Haryang-Umanis-Budha",
        "nakshatra": "Uttara Bhadrapada", "yoga": "Dhruwa", "karana": None, "wuku": None,
        "julian_date": (921, 9, 19), "category": "1.a"
    },
    {
        "no": 56, "id": "A.100", "name": "Wurudu Kidul A", "saka": 844,
        "masa": "Vaisakha", "tithi": 6, "paksa": "Krsna",
        "wara_string": "Was-Wage-Saniscara",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (922, 4, 20), "category": "1.a"
    },
    {
        "no": 57, "id": "A.101", "name": "Wurudu Kidul B", "saka": 844,
        "masa": "Jyestha", "tithi": 7, "paksa": "Sukla",
        "wara_string": "Wurukung-Kaliwon-Soma",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (922, 5, 6), "category": "1.a"
    },
    {
        "no": 58, "id": "A.105", "name": "Kinawě", "saka": 849,
        "masa": "Phalguna", "tithi": 5, "paksa": "Sukla",
        "wara_string": "Wurukung-Wage-Wrhaspati",
        "nakshatra": "Krittika", "yoga": "Wiskambha", "karana": None, "wuku": "Tolu",
        "julian_date": (928, 2, 28), "category": "1.a"
    },
    {
        "no": 59, "id": "A.108", "name": "Waharu II", "saka": 851,
        "masa": "Jyestha", "tithi": 13, "paksa": "Sukla",
        "wara_string": "Paniron-Kaliwon-Aditya",
        "nakshatra": "Vishakha", "yoga": "Wyatipata", "karana": "Taitila", "wuku": "Sungsang",
        "julian_date": (929, 5, 24), "category": "1.a"
    },
    {
        "no": 60, "id": "A.109", "name": "Turyyan", "saka": 851,
        "masa": "Sravana", "tithi": 15, "paksa": "Sukla",
        "wara_string": "Was-Umanis-Sukra",
        "nakshatra": "Sravana", "yoga": "Sobhagya", "karana": None, "wuku": None,
        "julian_date": (929, 7, 24), "category": "1.a"
    },
    {
        "no": 61, "id": "A.110", "name": "Sarangan", "saka": 851,
        "masa": "Sravana", "tithi": 12, "paksa": "Krsna",
        "wara_string": "Was-Pon-Budha",
        "nakshatra": "Pushya", "yoga": "Siwa", "karana": None, "wuku": None,
        "julian_date": (929, 8, 5), "category": "1.a"
    },
    {
        "no": 62, "id": "A.111", "name": "Linggasuntan", "saka": 851,
        "masa": "Bhadrapada", "tithi": 12, "paksa": "Krsna",
        "wara_string": "Paniron-Pahing-Wrhaspati",
        "nakshatra": "Magha", "yoga": "Parigha", "karana": None, "wuku": None,
        "julian_date": (929, 9, 3), "category": "1.a"
    },
    {
        "no": 63, "id": "A.113", "name": "Cunggrang II", "saka": 851,
        "masa": "Asvini", "tithi": 12, "paksa": "Sukla",  # DIPERBAIKI: "Asuji" → "Asvini"
        "wara_string": "Tungleh-Pahing-Sukra",
        "nakshatra": "Shatabhisha", "yoga": "Ganda", "karana": None, "wuku": "Wugu",
        "julian_date": (929, 9, 18), "category": "1.a", "is_anchor": True
    },
    {
        "no": 64, "id": "A.114", "name": "Poh Rinting", "saka": 851,
        "masa": "Kartika", "tithi": 8, "paksa": "Krsna",
        "wara_string": "Was-Pahing-Budha",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": None,
        "julian_date": (929, 10, 28), "category": "1.a"
    },
    {
        "no": 65, "id": "A.117", "name": "Gěwěg", "saka": 855,
        "masa": "Sravana", "tithi": 6, "paksa": "Krsna",
        "wara_string": "Was-Pon-Budha",
        "nakshatra": "Hasta", "yoga": "Dhrti", "karana": None, "wuku": None,
        "julian_date": (933, 8, 14), "category": "1.a"
    },
    {
        "no": 66, "id": "A.118", "name": "Sumbut", "saka": 855,
        "masa": "Asvini", "tithi": 11, "paksa": "Sukla",  # DIPERBAIKI: "Asuji" → "Asvini"
        "wara_string": "Maulu-Pahing-Budha",
        "nakshatra": "Dhanishta", "yoga": "Dhrti", "karana": "Wisti", "wuku": "Wayang",
        "julian_date": (933, 10, 2), "category": "1.a"
    },
    {
        "no": 67, "id": "A.122", "name": "Wulig", "saka": 856,
        "masa": "Magha", "tithi": 1, "paksa": "Sukla",
        "wara_string": "Tungleh-Kaliwon-Wrhaspati",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": "Wukir",
        "julian_date": (935, 1, 8), "category": "1.a"
    },
    {
        "no": 68, "id": "A.124", "name": "Sobhaměrta", "saka": 861,
        "masa": "Vaisakha", "tithi": 11, "paksa": "Sukla",
        "wara_string": "Paniron-Kaliwon-Wrhaspati",
        "nakshatra": "Hasta", "yoga": "Bajra", "karana": None, "wuku": "Marakeh",
        "julian_date": (939, 5, 2), "category": "1.a"
    },
    {
        "no": 69, "id": "A.126", "name": "Paradah II", "saka": 865,
        "masa": "Sravana", "tithi": 5, "paksa": "Sukla",
        "wara_string": "Paniron-Kaliwon-Soma",
        "nakshatra": "Hasta", "yoga": "Siwa", "karana": "Kolawa", "wuku": None,
        "julian_date": (943, 7, 10), "category": "1.a"
    },
    {
        "no": 70, "id": "A.127", "name": "Muñcang", "saka": 866,
        "masa": "Caitra", "tithi": 6, "paksa": "Sukla",
        "wara_string": "Tungleh-Pahing-Aditya",
        "nakshatra": "Rohini", "yoga": "Priti", "karana": None, "wuku": None,
        "julian_date": (944, 3, 3), "category": "1.a"
    },
    {
        "no": 71, "id": "A.130", "name": "Kawambang Kulwan", "saka": 913,
        "masa": "Magha", "tithi": 13, "paksa": "Sukla",
        "wara_string": "Maulu-Umanis-Budha",
        "nakshatra": "Purva Phalguni", "yoga": "Aswini", "karana": None, "wuku": None,
        "julian_date": (992, 1, 20), "category": "1.a"
    },
    {
        "no": 72, "id": "A.131", "name": "Wirāṭaparwwa A", "saka": 918,
        "masa": "Asvini", "tithi": 15, "paksa": "Krsna",  # DIPERBAIKI: "Asuji" → "Asvini"
        "wara_string": "Tungleh-Kaliwon-Budha",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": "Pahang",
        "julian_date": (996, 10, 14), "category": "1.a"
    },
    {
        "no": 73, "id": "A.132", "name": "Wirāṭaparwwa B", "saka": 918,
        "masa": "Kartika", "tithi": 14, "paksa": "Krsna",
        "wara_string": "Maulu-Wage-Wrhaspati",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": "Medangkungan",
        "julian_date": (996, 11, 12), "category": "1.a"
    },
    {
        "no": 74, "id": "A.135", "name": "Cane", "saka": 943,
        "masa": "Kartika", "tithi": 4, "paksa": "Krsna",
        "wara_string": "Tungleh-Wage-Sukra",
        "nakshatra": "Punarvasu", "yoga": "Subha", "karana": "Wawa", "wuku": "Landep",
        "julian_date": (1021, 10, 27), "category": "1.a"
    },
    {
        "no": 75, "id": "A.136", "name": "Munggut", "saka": 944,
        "masa": "Caitra", "tithi": 14, "paksa": "Krsna",
        "wara_string": "Wurukung-Pahing-Anggara",
        "nakshatra": "Krittika", "yoga": "Ayusman", "karana": "Wanija", "wuku": "Bala",
        "julian_date": (1022, 4, 3), "category": "1.a"
    },
    {
        "no": 76, "id": "A.137", "name": "Kakurugan", "saka": 945,
        "masa": "Asvini", "tithi": 9, "paksa": "Sukla",  # DIPERBAIKI: "Asuji" → "Asvini"
        "wara_string": "Paniron-Pon-Wrhaspati",
        "nakshatra": "Uttara Ashadha", "yoga": "Dhrti", "karana": "Kolawa", "wuku": "Kuningan",
        "julian_date": (1023, 9, 26), "category": "1.a"
    },
    {
        "no": 77, "id": "A.139", "name": "Těrěp I", "saka": 954,
        "masa": "Kartika", "tithi": 15, "paksa": "Sukla",
        "wara_string": "Was-Umanis-Saniscara",
        "nakshatra": "Bharani", "yoga": "Siddha", "karana": "Walawa", "wuku": "Tolu",
        "julian_date": (1032, 10, 21), "category": "1.a"
    },
    {
        "no": 78, "id": "A.141", "name": "Pucangan", "saka": 963,
        "masa": "Kartika", "tithi": 10, "paksa": "Sukla",
        "wara_string": "Haryang-Wage-Sukra",
        "nakshatra": "Uttara Bhadrapada", "yoga": "Bajra", "karana": "Garadi", "wuku": "Wayang",
        "julian_date": (1041, 11, 6), "category": "1.a", "is_anchor": True
    },
    {
        "no": 79, "id": "A.142", "name": "Gandhakuṭi", "saka": 964,
        "masa": "Margasira", "tithi": 9, "paksa": "Sukla",
        "wara_string": "Tungleh-Pahing-Budha",
        "nakshatra": "Uttara Bhadrapada", "yoga": "Ahirbudhnya", "karana": None, "wuku": "Wuye",
        "julian_date": (1042, 11, 24), "category": "1.a"
    },
    {
        "no": 80, "id": "A.145", "name": "Padlěgan I", "saka": 1038,
        "masa": "Magha", "tithi": 7, "paksa": "Sukla",
        "wara_string": "Maulu-Wage-Wrhaspati",
        "nakshatra": "Revati", "yoga": "Wyatipata", "karana": "Taitila", "wuku": "Medangkungan",
        "julian_date": (1117, 1, 11), "category": "1.a"
    },
    {
        "no": 81, "id": "A.146", "name": "Pānumbāngan", "saka": 1042,
        "masa": "Sravana", "tithi": 6, "paksa": "Sukla",
        "wara_string": "Wurukung-Pon-Soma",
        "nakshatra": "Swati", "yoga": "Bajra", "karana": "Wanija", "wuku": "Wugu",
        "julian_date": (1120, 8, 2), "category": "1.a"
    },
    {
        "no": 82, "id": "A.148", "name": "Candi Tuban", "saka": 1051,
        "masa": "Vaisakha", "tithi": 12, "paksa": "Krsna",
        "wara_string": "Wurukung-Pon-Sukra",
        "nakshatra": "Aswini", "yoga": "Siwa", "karana": "Wawa", "wuku": "Kurantil",
        "julian_date": (1129, 5, 17), "category": "1.a"
    },
    {
        "no": 83, "id": "A.149", "name": "Tangkilan", "saka": 1052,
        "masa": "Jyestha", "tithi": 5, "paksa": "Sukla",
        "wara_string": "Was-Kaliwon-Budha",
        "nakshatra": "Ashlesha", "yoga": None, "karana": "Wisti", "wuku": "Wugu",
        "julian_date": (1130, 5, 14), "category": "1.a"
    },
    {
        "no": 84, "id": "A.151", "name": "Hantang", "saka": 1057,
        "masa": "Bhadrapada", "tithi": 13, "paksa": "Krsna",
        "wara_string": "Wurukung-Pahing-Saniscara",
        "nakshatra": "Magha", "yoga": "Subha", "karana": "Wanija", "wuku": "Wukir",
        "julian_date": (1135, 9, 7), "category": "1.a", "is_anchor": True
    },
    {
        "no": 85, "id": "A.152", "name": "Talan", "saka": 1058,
        "masa": "Sravana", "tithi": 11, "paksa": "Krsna",
        "wara_string": "Tungleh-Wage-Soma",
        "nakshatra": "Punarvasu", "yoga": "Siddhi", "karana": "Wawa", "wuku": "Prangbakat",
        "julian_date": (1136, 8, 24), "category": "1.a"
    },
    {
        "no": 86, "id": "A.154", "name": "Bhāratayuddha", "saka": 1079,
        "masa": "Asvini", "tithi": 1, "paksa": "Sukla",  # DIPERBAIKI: "Asuji" → "Asvini"
        "wara_string": "Paniron-Pahing-Sukra",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": "Galungan",
        "julian_date": (1157, 9, 6), "category": "1.a"
    },
    {
        "no": 87, "id": "A.155", "name": "Padlěgan II", "saka": 1081,
        "masa": "Asvini", "tithi": 10, "paksa": "Sukla",  # DIPERBAIKI: "Asuji" → "Asvini"
        "wara_string": "Tungleh-Wage-Budha",
        "nakshatra": "Sravana", "yoga": "Siwa", "karana": None, "wuku": "Kulawu",
        "julian_date": (1159, 9, 23), "category": "1.a"
    },
    {
        "no": 88, "id": "A.156", "name": "Kahyunān", "saka": 1082,
        "masa": "Magha", "tithi": 12, "paksa": "Krsna",
        "wara_string": "Paniron-Pon-Wrhaspati",
        "nakshatra": "Sravana", "yoga": "Siwa", "karana": "Kolawa", "wuku": "Kuningan",
        "julian_date": (1161, 2, 23), "category": "1.a"
    },
    {
        "no": 89, "id": "A.158", "name": "Angin", "saka": 1093,
        "masa": "Caitra", "tithi": 5, "paksa": "Sukla",
        "wara_string": "Haryang-Pon-Saniscara",
        "nakshatra": "Krittika", "yoga": "Priti", "karana": "Wawa", "wuku": "Wugu",
        "julian_date": (1171, 3, 13), "category": "1.a"
    },
    {
        "no": 90, "id": "A.159", "name": "Jaring", "saka": 1103,
        "masa": "Margasira", "tithi": 11, "paksa": "Sukla",
        "wara_string": "Maulu-Pahing-Wrhaspati",
        "nakshatra": "Mula", "yoga": None, "karana": "Walawa", "wuku": "Mandasiya",
        "julian_date": (1181, 11, 19), "category": "1.a"
    },
    {
        "no": 91, "id": "A.160", "name": "Sěmanding", "saka": 1104,
        "masa": "Asadha", "tithi": 15, "paksa": "Sukla",
        "wara_string": "Maulu-Pahing-Wrhaspati",
        "nakshatra": "Aswini", "yoga": "Brahma", "karana": "Wisti", "wuku": "Mandasiya",
        "julian_date": (1182, 6, 17), "category": "1.a"
    },
    {
        "no": 92, "id": "A.161", "name": "Cěkěr", "saka": 1107,
        "masa": "Bhadrapada", "tithi": 15, "paksa": "Sukla",
        "wara_string": "Maulu-Wage-Budha",
        "nakshatra": "Purva Bhadrapada", "yoga": "Wrddhi", "karana": "Wisti", "wuku": "Wukir",
        "julian_date": (1185, 9, 11), "category": "1.a"
    },
    {
        "no": 93, "id": "A.163", "name": "Kěmulan", "saka": 1116,
        "masa": "Bhadrapada", "tithi": 13, "paksa": "Sukla",
        "wara_string": "Maulu-Kaliwon-Budha",
        "nakshatra": "Sravana", "yoga": "Dhrti", "karana": "Taitila", "wuku": "Maktal",
        "julian_date": (1194, 8, 31), "category": "1.a"
    },
    {
        "no": 94, "id": "A.165", "name": "Subhasitā", "saka": 1120,
        "masa": "Kartika", "tithi": 15, "paksa": "Sukla",
        "wara_string": "Haryang-Pon-Saniscara",
        "nakshatra": "Bharani", "yoga": "Wyatighata", "karana": "Taitila", "wuku": "Wugu",
        "julian_date": (1198, 10, 17), "category": "1.a"
    },
    {
        "no": 95, "id": "A.166", "name": "Galunggung", "saka": 1122,
        "masa": "Vaisakha", "tithi": 5, "paksa": "Sukla",
        "wara_string": "Tungleh-Wage-Wrhaspati",
        "nakshatra": "Punarvasu", "yoga": "Subha", "karana": "Wawa", "wuku": "Julungpujut",
        "julian_date": (1200, 4, 20), "category": "1.a"
    },
    {
        "no": 96, "id": "A.172", "name": "Pakis Wetan", "saka": 1188,
        "masa": "Magha", "tithi": 13, "paksa": "Sukla",
        "wara_string": "Was-Wage-Anggara",
        "nakshatra": "Pushya", "yoga": "Sobhana", "karana": "Taitila", "wuku": "Maktal",
        "julian_date": (1267, 2, 8), "category": "1.a"
    },
    {
        "no": 97, "id": "A.173", "name": "Sarwwadharmma", "saka": 1191,
        "masa": "Kartika", "tithi": 5, "paksa": "Sukla",
        "wara_string": "Was-Kaliwon-Wrhaspati",
        "nakshatra": "Uttara Ashadha", "yoga": "Ganda", "karana": "Walawa", "wuku": "Langkir",
        "julian_date": (1269, 10, 31), "category": "1.a"
    },
    {
        "no": 98, "id": "A.174", "name": "Wurare", "saka": 1211,
        "masa": "Asvini", "tithi": 5, "paksa": "Sukla",  # DIPERBAIKI: "Asuji" → "Asvini"
        "wara_string": "Paniron-Kaliwon-Budha",
        "nakshatra": "Anuradha", "yoga": "Saubhagya", "karana": "Wisti", "wuku": "Sinta",
        "julian_date": (1289, 9, 21), "category": "1.a"
    },
    {
        "no": 99, "id": "A.177", "name": "Kudadu", "saka": 1216,
        "masa": "Bhadrapada", "tithi": 5, "paksa": "Krsna",
        "wara_string": "Haryang-Umanis-Saniscara",
        "nakshatra": "Rohini", "yoga": "Siddhi", "karana": "Taitila", "wuku": "Medangkungan",
        "julian_date": (1294, 9, 11), "category": "1.a"
    },
    {
        "no": 100, "id": "A.178", "name": "Sukaměrta", "saka": 1218,
        "masa": "Kartika", "tithi": 2, "paksa": "Sukla",
        "wara_string": "Tungleh-Kaliwon-Soma",
        "nakshatra": "Ardra", "yoga": "Atiganda", "karana": "Walawa", "wuku": "Kuningan",
        "julian_date": (1296, 10, 29), "category": "1.a"
    },
    {
        "no": 101, "id": "A.180", "name": "Tuhañaru", "saka": 1245,
        "masa": "Margasira", "tithi": 15, "paksa": "Sukla",
        "wara_string": "Tungleh-Umanis-Anggara",
        "nakshatra": "Ardra", "yoga": "Brahma", "karana": "Wawa", "wuku": "Kuruwelut",
        "julian_date": (1323, 12, 13), "category": "1.a"
    },
    {
        "no": 102, "id": "A.182", "name": "Gěněng II", "saka": 1251,
        "masa": "Bhadrapada", "tithi": 1, "paksa": "Krsna",
        "wara_string": "Was-Wage-Aditya",
        "nakshatra": None, "yoga": None, "karana": "Kolawa", "wuku": None,
        "julian_date": (1329, 9, 10), "category": "1.a"
    },
    {
        "no": 103, "id": "A.183", "name": "Palungan", "saka": 1252,
        "masa": "Bhadrapada", "tithi": 15, "paksa": "Krsna",
        "wara_string": "Tungleh-Pahing-Wrhaspati",
        "nakshatra": "Uttara Phalguni", "yoga": None, "karana": "Naga", "wuku": "Julungwangi",
        "julian_date": (1330, 9, 13), "category": "1.a"
    },
    {
        "no": 104, "id": "A.185", "name": "Watukura B", "saka": 1270,
        "masa": "Asadha", "tithi": 11, "paksa": "Sukla",
        "wara_string": "Paniron-Wage-Soma",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": "Julungwangi",
        "julian_date": (1348, 7, 7), "category": "1.a"
    },
    {
        "no": 105, "id": "A.186", "name": "Kuśmala", "saka": 1272,
        "masa": "Margasira", "tithi": 15, "paksa": "Sukla",
        "wara_string": "Maulu-Wage-Anggara",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": "Pahang",
        "julian_date": (1350, 12, 14), "category": "1.a"
    },
    {
        "no": 106, "id": "A.187", "name": "Gajah Mada B", "saka": 1273,
        "masa": "Vaisakha", "tithi": 1, "paksa": "Sukla",  # DIPERBAIKI: "Wesaka" → "Vaisakha"
        "wara_string": "Haryang-Pon-Budha",
        "nakshatra": "Mrgasira", "yoga": "Sobhana", "karana": "Kistughna", "wuku": "Tolu",
        "julian_date": (1351, 4, 27), "category": "1.a", "is_anchor": True
    },
    {
        "no": 107, "id": "A.188", "name": "Canggu", "saka": 1280,
        "masa": "Sravana", "tithi": 1, "paksa": "Sukla",
        "wara_string": "Haryang-Umanis-Saniscara",
        "nakshatra": "Pushya", "yoga": "Bajra", "karana": "Naga", "wuku": "Medangkungan",
        "julian_date": (1358, 7, 7), "category": "1.a"
    },
    {
        "no": 108, "id": "A.204", "name": "Walandit B", "saka": 1327,
        "masa": "Asadha", "tithi": 9, "paksa": "Krsna",
        "wara_string": "Was-Pahing-Aditya",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": "Galungan",
        "julian_date": (1405, 6, 21), "category": "1.a"
    },
    {
        "no": 109, "id": "A.206", "name": "Patapān II", "saka": 1340,
        "masa": "Pausa", "tithi": 5, "paksa": "Sukla",
        "wara_string": "Paniron-Kaliwon-Saniscara",
        "nakshatra": None, "yoga": None, "karana": None, "wuku": "Wuye",
        "julian_date": (1418, 12, 3), "category": "1.a"
    },
    {
        "no": 110, "id": "A.207", "name": "Waringin Pitu", "saka": 1369,
        "masa": "Margasira", "tithi": 15, "paksa": "Sukla",
        "wara_string": "Tungleh-Umanis-Budha",
        "nakshatra": "Rohini", "yoga": "Sadhya", "karana": "Wawa", "wuku": "Kurantil",
        "julian_date": (1447, 11, 22), "category": "1.a"
    },
    {
        "no": 111, "id": "A.209", "name": "Pamintihan", "saka": 1395,
        "masa": "Vaisakha", "tithi": 3, "paksa": "Krsna",
        "wara_string": "Maulu-Umanis-Sukra",
        "nakshatra": "Mula", "yoga": "Subha", "karana": "Wanija", "wuku": "Langkir",
        "julian_date": (1473, 5, 14), "category": "1.a"
    },
    {
        "no": 112, "id": "A.210", "name": "Pětak", "saka": 1408,
        "masa": "Jyestha", "tithi": 10, "paksa": "Sukla",
        "wara_string": "Maulu-Pahing-Aditya",
        "nakshatra": "Chitra", "yoga": None, "karana": None, "wuku": "Gumbreg",
        "julian_date": (1486, 6, 11), "category": "1.a"
    },
]
