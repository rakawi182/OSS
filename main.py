#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JAE INTEGRATED – Jolotundo Archaeoastronomy Engine
Menggabungkan JRC_Ephemeris, wuku_system, Old_Java_Astronomy, dan SPICA_v18
dengan tampilan panel yang menyesuaikan lebar terminal.

Tambahan: Uji batch 112 prasasti Damais (10 per batch) menggunakan IJCC v889
"""

import sys
sys.dont_write_bytecode = True

from datetime import datetime

# ============================================================================
# Impor semua komponen
# ============================================================================
from JRC_Ephemeris import (
    IAU2023UltraPrecision,
    TimeSystem as JRC_TimeSystem,
    JolotundoArchaeoastronomySystem as JRC_ArchaeoSystem
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
    NormalizationEngine as OldJavaNormalizer
)

from SPICA_v18 import (
    ΩSthapatiSystem
)

# ============================================================================
# Impor untuk uji cepat Damais (IJCC v889)
# ============================================================================
from quick_test_ijcc import run_quick_test_batch

# ============================================================================
# Impor modul display
# ============================================================================
from display import (
    print_header,
    print_panel,
    print_table,
    print_info,
    print_separator
)

# ============================================================================
# Inisialisasi global
# ============================================================================
jrc_const      = IAU2023UltraPrecision()
time_sys       = JRC_TimeSystem()
mech_engine    = WukuMechanicalEngine()
sthapati       = ΩSthapatiSystem(verbose_startup=False)
jrc_archaeo    = JRC_ArchaeoSystem()

# ============================================================================
# Fungsi tampilan utama (dengan panel otomatis)
# ============================================================================
def display_complete_info(year, month, day, hour):
    hh = int(hour)
    mm = int((hour - hh) * 60)
    ss = int(((hour - hh) * 60 - mm) * 60)

    jd_utc = time_sys.wib_to_jd_utc(year, month, day, hh, mm, ss)
    jd_tt  = time_sys.wib_to_jd_tt_extended(year, month, day, hh, mm, ss)
    ka = mech_engine.date_to_ka(year, month, day)

    wuku_info = mech_engine.get_wuku_by_ka(ka)
    epoch_info = mech_engine.get_detailed_wuku_epoch_info(ka)

    print_header("JOLOTUNDO RESEARCH CONSORTIUM – EPHEMERIS")

    # Panel WAKTU
    dt = (jd_tt - jd_utc) * 86400 - jrc_const.TT_TAI
    time_lines = [
        f"📅 Tanggal WIB      : {year:04d}-{month:02d}-{day:02d} {hh:02d}:{mm:02d}:{ss:02d}",
        f"🕒 JD UTC           : {jd_utc:.8f}",
        f"🕒 JD TT            : {jd_tt:.8f}",
        f"⏱️ ΔT (TT-UT)       : {dt:.2f} detik",
        f"📆 KA (Kali Ahargana): {ka:,}",
    ]
    print_panel("WAKTU", time_lines)

    # Panel WUKU & WARA
    wuku_lines = [
        f"Wuku             : {wuku_info['wuku_name']} (#{wuku_info['wuku_number']})",
        f"Hari dalam Wuku  : {wuku_info['day_in_wuku']}/7",
        f"Sadwara          : {wuku_info['sadwara_full']} ({wuku_info['sadwara']})",
        f"Pancawara        : {wuku_info['pancawara_full']} ({wuku_info['pancawara']})",
        f"Saptawara        : {wuku_info['saptawara_full']} ({wuku_info['saptawara']})",
        f"Triple Wara      : {wuku_info['wara_triple_full']}  [{wuku_info['wara_triple']}]",
        f"Hari sejak epoch : {epoch_info['days_since_epoch']:,} hari ({epoch_info['direction']})",
        f"Siklus wuku ke-  : {epoch_info['cycle_number']}, hari ke-{epoch_info['day_in_cycle']}/210",
        f"Progres siklus   : {epoch_info['progress_percent']:.1f}%",
        f"Hari ke TU-PA-Ā  : {epoch_info['days_to_next_tu_pa_a']} hari",
    ]
    print_panel("WUKU & WARA", wuku_lines)

    # Bagian Old Java Astronomy
    print_header("OLD JAVA ASTRONOMY")
    display_comprehensive_info(year, month, day, hour)

    # Panel KOORDINAT JRC
    jrc_data = jrc_archaeo.get_complete_ephemeris(
        year_astro=year, month=month, day=day,
        hour=hh, minute=mm, second=ss, use_current_time=False
    )
    sun = jrc_data['sun']
    moon = jrc_data['moon']

    coord_lines = [
        "☀️ MATAHARI",
        f"   Geocentric App : RA={sun['geocentric']['equatorial']['ra_deg']:.6f}° Dec={sun['geocentric']['equatorial']['dec_deg']:.6f}°",
        f"   Topocentric    : RA={sun['topocentric_equatorial']['ra_deg']:.6f}° Dec={sun['topocentric_equatorial']['dec_deg']:.6f}°",
        f"   Horizontal     : Az={sun['horizontal_apparent']['azimuth_deg']:.2f}° Alt={sun['horizontal_apparent']['altitude_deg']:.2f}°",
        "",
        "🌙 BULAN",
        f"   Geocentric App : RA={moon['geocentric']['equatorial']['ra_deg']:.6f}° Dec={moon['geocentric']['equatorial']['dec_deg']:.6f}°",
        f"   Topocentric    : RA={moon['topocentric_equatorial']['ra_deg']:.6f}° Dec={moon['topocentric_equatorial']['dec_deg']:.6f}°",
        f"   Horizontal     : Az={moon['horizontal_apparent']['azimuth_deg']:.2f}° Alt={moon['horizontal_apparent']['altitude_deg']:.2f}°",
        f"   Fase           : {moon['phase']['phase_name']} ({moon['phase']['illumination_fraction']*100:.1f}%)",
    ]
    print_panel("KOORDINAT (JRC Ephemeris)", coord_lines)

    print_separator()

# ============================================================================
# Fungsi input dan menu
# ============================================================================
def input_int(prompt, minv=None, maxv=None):
    while True:
        try:
            v = int(input(prompt))
            if minv is not None and v < minv:
                print(f"  Nilai minimal {minv}")
                continue
            if maxv is not None and v > maxv:
                print(f"  Nilai maksimal {maxv}")
                continue
            return v
        except ValueError:
            print("  Masukkan bilangan bulat")

def input_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("  Masukkan angka")

def clear_screen():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def menu_realtime():
    now = datetime.now()
    jam = now.hour + now.minute/60.0 + now.second/3600.0
    print(f"\n🕐 Waktu sekarang (lokal/WIB): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    display_complete_info(now.year, now.month, now.day, jam)

def menu_tanggal_spesifik():
    try:
        tahun = input_int("Tahun (misal 2024, -100 untuk 101 SM): ")
        bulan = input_int("Bulan (1-12): ", 1, 12)
        hari  = input_int("Hari (1-31): ", 1, 31)
        jam_input = input("Jam (format HH:MM:SS atau desimal, kosong = 12:00): ").strip()
        jam = parse_time_input(jam_input)
        print(f"\n📅 Menampilkan data untuk {tahun:04d}-{bulan:02d}-{hari:02d} pukul {jam:.2f} WIB")
        display_complete_info(tahun, bulan, hari, jam)
    except Exception as e:
        print(f"❌ Error: {e}")

def submenu_konversi_waktu():
    while True:
        print_header("KONVERSI WAKTU")
        print("1. Tanggal → Julian Day (JD)")
        print("2. JD → Tanggal")
        print("3. JD → KA")
        print("4. KA → JD")
        print("5. KA → Tanggal")
        print("6. Tanggal → KA")
        print("7. Gregorian ↔ Julian (konversi tanggal)")
        print("8. Kembali")
        p = input("Pilih (1-8): ").strip()

        if p == '1':
            y = input_int("Tahun: ")
            m = input_int("Bulan: ", 1, 12)
            d = input_int("Hari: ", 1, 31)
            h = input_int("Jam (0-23): ", 0, 23)
            mi = input_int("Menit (0-59): ", 0, 59)
            s = input_int("Detik (0-59): ", 0, 59)
            jd = time_sys.date_to_jd_utc(y, m, d, h, mi, s)
            print(f"JD UTC = {jd:.8f}")

        elif p == '2':
            jd = input_float("Julian Day (UTC): ")
            date = time_sys.jd_to_gregorian(jd)
            print(f"Tahun astronomi: {date['year_astronomical']} ({date['year_display']})")
            print(f"Tanggal: {date['year_astronomical']:04d}-{date['month']:02d}-{date['day']:02d} {date['hour']:02d}:{date['minute']:02d}:{date['second']:02d}")

        elif p == '3':
            jd = input_float("Julian Day (UTC): ")
            ka = mech_engine.julian_day_to_ka(jd)
            print(f"KA = {ka:,}")

        elif p == '4':
            ka = input_int("KA: ")
            jd = mech_engine.ka_to_julian_day(ka)
            print(f"JD = {jd:.8f}")

        elif p == '5':
            ka = input_int("KA: ")
            y, m, d = mech_engine.ka_to_date(ka)
            print(f"Tanggal: {y:04d}-{m:02d}-{d:02d}")

        elif p == '6':
            y = input_int("Tahun: ")
            m = input_int("Bulan: ", 1, 12)
            d = input_int("Hari: ", 1, 31)
            ka = mech_engine.date_to_ka(y, m, d)
            print(f"KA = {ka:,}")

        elif p == '7':
            print("\nGregorian → Julian:")
            y = input_int("Tahun Gregorian: ")
            m = input_int("Bulan: ", 1, 12)
            d = input_int("Hari: ", 1, 31)
            jd_greg = CalendarConverter.gregorian_to_jd(y, m, d)
            yj, mj, dj = CalendarConverter.jd_to_julian(jd_greg)
            print(f"Tanggal Julian: {yj:04d}-{mj:02d}-{dj:02d}")
            print("\nJulian → Gregorian:")
            yj = input_int("Tahun Julian: ")
            mj = input_int("Bulan: ", 1, 12)
            dj = input_int("Hari: ", 1, 31)
            jd_jul = CalendarConverter.julian_to_jd(yj, mj, dj)
            yg, mg, dg = CalendarConverter.jd_to_gregorian(jd_jul)
            print(f"Tanggal Gregorian: {yg:04d}-{mg:02d}-{dg:02d}")

        elif p == '8':
            break
        else:
            print("Pilihan tidak valid")
        input("\nTekan Enter...")

def menu_konversi_prasasti():
    print_header("KONVERSI PRASASTI SAKA → MASEHI (Ω‑STHAPATI)")
    try:
        saka = input_int("Tahun Śaka: ")
        masa = input("Bulan Śaka (masa): ").strip()
        tithi = input_int("Tithi (1-30): ", 1, 30)
        paksa = input("Paksa (Sukla/Krsna): ").strip()
        wuku = input("Wuku (opsional): ").strip()
        wara = input("Wara (opsional, bisa parsial): ").strip()
        naks = input("Nakṣatra (opsional): ").strip()

        data = {
            'saka_year': saka,
            'masa': masa,
            'tithi': tithi,
            'paksa': paksa,
            'wuku': wuku,
            'wara_string': wara,
            'nakshatra': naks
        }
        results = sthapati.convert_prasasti_with_smart_parsing(data, verbose=True)
        if not results:
            print("❌ Tidak ditemukan kandidat yang valid.")
        else:
            print("\n✨ KANDIDAT TERBAIK:")
            headers = ["No", "Tanggal", "KA", "Wuku", "Skor", "Confidence"]
            rows = []
            for i, res in enumerate(results[:3]):
                cand = res['candidate']
                y, m, d = cand['date']
                rows.append([
                    f"#{i+1}",
                    f"{int(y)}-{int(m):02d}-{int(d):02d}",
                    f"{cand['ka']:,}",
                    cand['wuku_info']['wuku_name'],
                    f"{res['score']:.3f}",
                    res['confidence']
                ])
            print_table(headers, rows)

            best = results[0]['candidate']
            year, month, day = best['date']
            print("\n" + "="*70)
            print("📊 DATA ASTRONOMI UNTUK TANGGAL TERSEBUT (JAM 12:00 WIB)")
            print("="*70)

            # Tampilkan data astronomi dan simpan hasilnya
            astro_result = display_comprehensive_info(year, month, int(day), 12.0)

            # --- Verifikasi Tithi & Naksatra ---
            print("\n" + "="*70)
            print("🔍 VERIFIKASI TITHI & NAKSATRA")
            print("="*70)

            tithi_input = data.get('tithi')
            paksa_input = data.get('paksa')
            naks_input = data.get('nakshatra')

            if tithi_input and paksa_input:
                tithi_hitung = astro_result['tithi']['tithi']
                paksa_hitung = astro_result['tithi']['paksa']
                print(f"Tithi input : {tithi_input} {paksa_input}")
                print(f"Tithi hitung: {tithi_hitung} {paksa_hitung}")

                if tithi_input == tithi_hitung and paksa_input.lower() == paksa_hitung.lower():
                    print("✅ Tithi cocok persis.")
                else:
                    if abs(tithi_input - tithi_hitung) <= 1 and paksa_input.lower() == paksa_hitung.lower():
                        print(f"⚠️ Tithi cocok dengan toleransi 1 (selisih {abs(tithi_input - tithi_hitung)} tithi).")
                    else:
                        print("❌ Tithi tidak cocok.")
            else:
                print("Tidak ada data tithi untuk diverifikasi.")

            if naks_input:
                # Gunakan normalizer dari Old Java, bukan SPICA
                old_norm = OldJavaNormalizer()
                naks_norm = old_norm.normalize(naks_input)
                naks_nirayana = astro_result['nakshatra']['nakshatra']
                naks_sayana = astro_result['nakshatra_sayana']['nakshatra']
                print(f"\nNaksatra data input: {naks_norm}")
                print(f"Naksatra sistem (Nirayana): {naks_nirayana}")
                print(f"Naksatra sistem (Sayana)  : {naks_sayana}")

                if naks_norm == naks_nirayana:
                    print("✅ Naksatra cocok dengan sistem Nirayana (sidereal).")
                    if naks_norm != naks_sayana:
                        print("   (Tidak cocok dengan Sayana)")
                elif naks_norm == naks_sayana:
                    print("✅ Naksatra cocok dengan sistem Sayana (tropical).")
                else:
                    print("❌ Naksatra tidak cocok dengan kedua sistem.")
            else:
                print("\nTidak ada data naksatra untuk diverifikasi.")

            # Tampilkan evaluasi 4 komponen utama dari Ω‑STHAPATI
            sthapati.display_main_components_evaluation(results)

    except Exception as e:
        print(f"❌ Error: {e}")

def submenu_offset():
    while True:
        print_header("HITUNG OFFSET WAKTU")
        print("1. Tambah hari solar")
        print("2. Tambah bulan solar (rata‑rata)")
        print("3. Tambah tahun solar (rata‑rata)")
        print("4. Tambah bulan lunar (sinodik)")
        print("5. Tambah tahun lunar (sinodik)")
        print("6. Tambah tithi (rata‑rata)")
        print("7. Kembali")
        p = input("Pilih (1-7): ").strip()

        if p in ('1','2','3','4','5','6'):
            tanggal_str = input("Tanggal awal (YYYY-MM-DD): ").strip()
            try:
                y, m, d = map(int, tanggal_str.split('-'))
            except:
                print("Format tanggal salah.")
                input("Tekan Enter...")
                continue
            jumlah = input_int("Jumlah offset (bisa negatif): ")
            if p == '1':
                res = offset_solar_days(tanggal_str, jumlah)
            elif p == '2':
                res = offset_solar_months(tanggal_str, jumlah)
            elif p == '3':
                res = offset_solar_years(tanggal_str, jumlah)
            elif p == '4':
                res = offset_lunar_months(tanggal_str, jumlah)
            elif p == '5':
                res = offset_lunar_years(tanggal_str, jumlah)
            elif p == '6':
                res = offset_tithi(tanggal_str, jumlah)

            if 'error' in res:
                print(f"❌ {res['error']}")
            else:
                ny, nm, nd = res['date']
                print(f"\nTanggal baru : {int(ny)}-{int(nm):02d}-{int(nd):02d}")
                print(f"KA baru      : {res['ka']:,}")
                print(f"Wuku         : {res['wuku_name']} (#{res['wuku_number']})")
                print(f"Hari dalam wuku: {res['day_in_wuku']}/7")
                print(f"Wara triple  : {res['wara_triple_full']}")
                print(f"TU-PA-A      : {'YA' if res['is_tu_pa_a'] else 'TIDAK'}")
        elif p == '7':
            break
        else:
            print("Pilihan tidak valid")
        input("\nTekan Enter...")

def submenu_uji_batch():
    """Submenu untuk menjalankan uji batch prasasti Damais (10 per batch)"""
    while True:
        clear_screen()
        print_header("UJI BATCH PRASASTI DAMAIS (IJCC v889)")
        print("Database: 112 prasasti, ukuran batch: 10")
        print("Pilih batch yang akan dijalankan:")
        for i in range(1, 13):
            start = (i-1)*10 + 1
            end = min(i*10, 112)
            print(f"  {i}. Batch {i} (prasasti {start} - {end})")
        print("  0. Kembali ke menu utama")
        print_separator()
        pilihan = input("Pilih batch (0-12): ").strip()
        
        if pilihan == '0':
            break
        try:
            batch = int(pilihan)
            if 1 <= batch <= 12:
                run_quick_test_batch(batch, batch_size=10, verbose=True)
                input("\nTekan Enter untuk kembali ke menu batch...")
            else:
                print("Pilihan tidak valid.")
                input("Tekan Enter...")
        except ValueError:
            print("Masukkan angka yang valid.")
            input("Tekan Enter...")

def main():
    while True:
        clear_screen()
        print_header("JOLOTUNDO RESEARCH CONSORTIUM – OLDJAVA ASTRONOMY")
        print("Menggabungkan: JRC Ephemeris, Wuku, Old Java Astro, Ω‑STHAPATI")
        print_separator()
        print("1. Realtime (waktu sekarang WIB)")
        print("2. Waktu spesifik (tanggal tertentu)")
        print("3. Konversi Waktu (JD, KA, Gregorian/Julian)")
        print("4. Konversi Prasasti Saka → Masehi (Ω‑STHAPATI)")
        print("5. Hitung Offset (hari, bulan, tahun, tithi)")
        print("6. Keluar")
        print("7. Uji Batch Prasasti Damais (IJCC v889)")   # Opsi baru
        print_separator()
        pilihan = input("Pilih menu (1-7): ").strip()

        if pilihan == '1':
            menu_realtime()
            input("\nTekan Enter untuk kembali ke menu...")
        elif pilihan == '2':
            menu_tanggal_spesifik()
            input("\nTekan Enter untuk kembali ke menu...")
        elif pilihan == '3':
            submenu_konversi_waktu()
        elif pilihan == '4':
            menu_konversi_prasasti()
            input("\nTekan Enter untuk kembali ke menu...")
        elif pilihan == '5':
            submenu_offset()
        elif pilihan == '6':
            print("\nTerima kasih telah menggunakan JAE Integrated System.")
            sys.exit(0)
        elif pilihan == '7':
            submenu_uji_batch()
        else:
            print("Pilihan tidak valid.")
            input("Tekan Enter untuk melanjutkan...")

if __name__ == "__main__":
    main()