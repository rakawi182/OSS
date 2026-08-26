# quick_test_ijcc.py
"""
Quick Test untuk IJCC - Uji Akurasi Sistem dengan 112 Prasasti Damais
Mode batch: setiap batch memproses sejumlah prasasti (default 10)
"""

import sys
import os
import json
from datetime import datetime

# Cegah pembuatan __pycache__
sys.dont_write_bytecode = True

# Import modul utama
print("Memuat sistem Ω-STHAPATI...")
from IJCC_v889 import ΩSthapatiSystem, NormalizationEngine
print("Memuat database Damais...")
from Damais_DB import DAMAIS_INSCRIPTIONS

# ============================================================================
# Tambahan: Import engine JRC untuk verifikasi astronomi
# ============================================================================
from Old_Java_Astronomy import AstronomicalEngine, NormalizationEngine as OldJavaNormalizer
from Old_Java_Astronomy import ΩConstants

def get_nakshatra_index(name):
    """Mendapatkan indeks naksatra (0-26) dari nama standar"""
    try:
        return ΩConstants.NAKSHATRAS_STANDARD.index(name)
    except ValueError:
        return None

def inscription_tithi_to_standard(t_ins, p_ins):
    """
    Konversi representasi tithi prasasti (1-15 dengan paksa) ke nomor standar 30-hari.
    Contoh: (1, Krsna) -> 16
    """
    p = p_ins.lower() if p_ins else ''
    if p == "sukla":
        return t_ins
    elif p == "krsna":
        if t_ins <= 15:
            return t_ins + 15
        else:
            return t_ins
    else:
        return None

def verify_with_jrc(converted_date, inscription_data):
    """
    Verifikasi tithi (dengan toleransi drift 1) dan naksatra (sayana/nirayana)
    menggunakan engine JRC ephemeris.
    Mengembalikan dict lengkap dengan nilai hitung dan status toleransi.
    """
    year, month, day = converted_date
    hour = 12.0
    hh = int(hour)
    mm = int((hour - hh) * 60)
    ss = 0

    astro = AstronomicalEngine()
    jd_tt = astro.time_system.wib_to_jd_tt_extended(year, month, day, hh, mm, ss)

    sun_data = astro.calculate_sun_position_ultra(jd_tt)
    moon_data = astro.calculate_moon_position_ultra(jd_tt, sun_data['longitude_deg'])
    ayanamsa = astro.calculate_ayanamsa_precise(jd_tt)

    sun_nirayana = (sun_data['longitude_deg'] - ayanamsa) % 360
    moon_nirayana = (moon_data['longitude'] - ayanamsa) % 360

    # Hitung tithi nirayana
    tithi_nirayana = astro.calculate_tithi(sun_nirayana, moon_nirayana, "nirayana")
    # Hitung naksatra sayana dan nirayana
    naks_sayana = astro.calculate_nakshatra(moon_data['longitude'], "tropical")
    naks_nirayana = astro.calculate_nakshatra(moon_nirayana, "nirayana")

    # Data prasasti
    prasasti_tithi = inscription_data.get('tithi')
    prasasti_paksa = inscription_data.get('paksa')
    prasasti_naks = inscription_data.get('nakshatra')

    # Verifikasi tithi (dengan mapping ke standar 30-hari)
    tithi_exact_match = False
    tithi_tolerance_match = False
    tithi_std_ins = None
    tithi_diff = None
    if prasasti_tithi is not None and prasasti_paksa is not None:
        tithi_std_ins = inscription_tithi_to_standard(prasasti_tithi, prasasti_paksa)
        if tithi_std_ins is not None:
            tithi_calc = tithi_nirayana['tithi']
            tithi_exact_match = (tithi_calc == tithi_std_ins)
            # Toleransi drift 1: basis 15 (karena tithi 1-15 per paksa)
            diff = abs(tithi_calc - tithi_std_ins)
            if diff <= 1 or (15 - diff) <= 1:
                tithi_tolerance_match = True
            else:
                tithi_tolerance_match = False
        else:
            tithi_exact_match = False
            tithi_tolerance_match = False

    # Verifikasi naksatra dengan toleransi drift 1 (indeks bersebelahan)
    naks_sayana_exact = False
    naks_nirayana_exact = False
    naks_sayana_tolerance = False
    naks_nirayana_tolerance = False
    system_detected = None
    system_detected_tolerance = None
    if prasasti_naks:
        norm = OldJavaNormalizer()
        prasasti_naks_norm = norm.normalize(prasasti_naks)
        idx_ins = get_nakshatra_index(prasasti_naks_norm)
        idx_sayana = get_nakshatra_index(naks_sayana['nakshatra'])
        idx_nirayana = get_nakshatra_index(naks_nirayana['nakshatra'])

        if idx_ins is not None and idx_sayana is not None:
            naks_sayana_exact = (naks_sayana['nakshatra'] == prasasti_naks_norm)
            diff_s = abs(idx_sayana - idx_ins)
            if diff_s <= 1 or (27 - diff_s) <= 1:
                naks_sayana_tolerance = True

        if idx_ins is not None and idx_nirayana is not None:
            naks_nirayana_exact = (naks_nirayana['nakshatra'] == prasasti_naks_norm)
            diff_n = abs(idx_nirayana - idx_ins)
            if diff_n <= 1 or (27 - diff_n) <= 1:
                naks_nirayana_tolerance = True

        # Sistem detected berdasarkan exact match
        if naks_sayana_exact and naks_nirayana_exact:
            system_detected = "both"
        elif naks_sayana_exact:
            system_detected = "sayana"
        elif naks_nirayana_exact:
            system_detected = "nirayana"
        else:
            system_detected = "none"

        # Sistem detected berdasarkan tolerance match
        if naks_sayana_tolerance and naks_nirayana_tolerance:
            system_detected_tolerance = "both"
        elif naks_sayana_tolerance:
            system_detected_tolerance = "sayana"
        elif naks_nirayana_tolerance:
            system_detected_tolerance = "nirayana"
        else:
            system_detected_tolerance = "none"
    else:
        system_detected = None
        system_detected_tolerance = None

    return {
        'tithi_match': tithi_exact_match,
        'tithi_tolerance_match': tithi_tolerance_match,
        'tithi_std_ins': tithi_std_ins,
        'tithi_calculated': {
            'tithi': tithi_nirayana['tithi'],
            'paksa': tithi_nirayana['paksa']
        },
        'naks_sayana_exact': naks_sayana_exact,
        'naks_nirayana_exact': naks_nirayana_exact,
        'naks_sayana_tolerance': naks_sayana_tolerance,
        'naks_nirayana_tolerance': naks_nirayana_tolerance,
        'naks_sayana': naks_sayana['nakshatra'],
        'naks_nirayana': naks_nirayana['nakshatra'],
        'system_detected': system_detected,
        'system_detected_tolerance': system_detected_tolerance,
        'ayanamsa': ayanamsa
    }

def normalize_damais_data(inscription_data, norm_engine):
    """Normalisasi data prasasti Damais menggunakan normalizer IJCC"""
    normalized = inscription_data.copy()
    
    # Normalisasi bulan (masa)
    if 'masa' in normalized and normalized['masa']:
        normalized['masa'] = norm_engine.normalize(normalized['masa'])
    
    # Normalisasi wuku
    if 'wuku' in normalized and normalized['wuku']:
        normalized['wuku'] = norm_engine.normalize(normalized['wuku'])
    
    # Normalisasi wara_string
    if 'wara_string' in normalized and normalized['wara_string']:
        parts = normalized['wara_string'].split('-')
        if len(parts) == 3:
            sad = norm_engine.normalize(parts[0])
            panca = norm_engine.normalize(parts[1])
            sapta = norm_engine.normalize(parts[2])
            normalized['wara_string'] = f"{sad}-{panca}-{sapta}"
    
    return normalized

def run_quick_test_batch(batch_number=1, batch_size=10, verbose=True):
    """
    Jalankan quick test untuk batch tertentu.
    batch_number: nomor batch (1-based)
    batch_size: jumlah prasasti per batch
    """
    total_inscriptions = len(DAMAIS_INSCRIPTIONS)
    start_idx = (batch_number - 1) * batch_size
    end_idx = min(start_idx + batch_size, total_inscriptions)
    
    if start_idx >= total_inscriptions:
        print(f"❌ Batch {batch_number} melebihi total prasasti ({total_inscriptions})")
        return None
    
    print("\n" + "="*100)
    print(f"QUICK TEST BATCH {batch_number} - Prasasti {start_idx+1} s/d {end_idx}")
    print("Menggunakan Ω-STHAPATI v301.4 FINAL IMPROVED + JRC Verification")
    print("="*100)
    
    # Inisialisasi sistem
    system = ΩSthapatiSystem(verbose_startup=False)
    norm_engine = NormalizationEngine()
    
    results = []
    
    # Statistik per kategori untuk batch ini
    categories = {
        "exact_match": 0,
        "within_3_days": 0,
        "within_7_days": 0,
        "within_30_days": 0,
        "failed": 0,
        "no_result": 0
    }

    # Statistik deteksi sistem ayanamsa
    system_counts = {"sayana": 0, "nirayana": 0, "both": 0, "none": 0, "no_naks_data": 0}
    system_counts_tolerance = {"sayana": 0, "nirayana": 0, "both": 0, "none": 0, "no_naks_data": 0}
    
    print(f"\nMemproses {end_idx - start_idx} prasasti...")
    print("-"*100)
    
    for idx in range(start_idx, end_idx):
        i = idx + 1  # nomor urut global
        inscription = DAMAIS_INSCRIPTIONS[idx]
        
        print(f"\n[{i:3d}/{total_inscriptions}] {inscription['id']} - {inscription['name']}")
        print(f"   Śaka {inscription['saka']} {inscription['masa']}")
        
        # Data yang diperlukan oleh IJCC
        prasasti_data = {
            'saka_year': inscription['saka'],
            'masa': inscription['masa'],
            'tithi': inscription['tithi'],
            'paksa': inscription['paksa'],
            'wuku': inscription['wuku'],
            'wara_string': inscription['wara_string'],
            'nakshatra': inscription['nakshatra']
        }
        
        # Normalisasi data
        normalized_data = normalize_damais_data(prasasti_data, norm_engine)
        
        # Jalankan konversi
        try:
            conversion_results = system.convert_prasasti(normalized_data, verbose=False)
            
            if conversion_results:
                # Ambil kandidat terbaik
                best_result = conversion_results[0]
                candidate = best_result['candidate']
                year, month, day = candidate['date']
                
                # Tanggal hasil konversi
                converted_date = (int(year), int(month), int(day))
                
                # Tanggal yang diharapkan dari Damais
                expected_date = inscription['julian_date']
                
                # Hitung selisih hari
                from datetime import date as dt_date
                conv_dt = dt_date(converted_date[0], converted_date[1], converted_date[2])
                exp_dt = dt_date(expected_date[0], expected_date[1], expected_date[2])
                days_diff = abs((conv_dt - exp_dt).days)
                
                # Tentukan status
                if days_diff == 0:
                    status = "✅ EXACT MATCH"
                    categories["exact_match"] += 1
                elif days_diff <= 3:
                    status = "✅ CLOSE (≤3 hari)"
                    categories["within_3_days"] += 1
                elif days_diff <= 7:
                    status = "⚠️  NEAR (≤7 hari)"
                    categories["within_7_days"] += 1
                elif days_diff <= 30:
                    status = "⚠️  WITHIN 30 HARI"
                    categories["within_30_days"] += 1
                else:
                    status = "❌ DIFF >30 HARI"
                    categories["failed"] += 1
                
                # ============================================================
                # Verifikasi dengan JRC
                # ============================================================
                jrc_verification = verify_with_jrc(converted_date, normalized_data)
                
                # Update statistik sistem ayanamsa (exact)
                if jrc_verification['system_detected']:
                    sys_det = jrc_verification['system_detected']
                    if sys_det in system_counts:
                        system_counts[sys_det] += 1
                else:
                    system_counts["no_naks_data"] += 1

                # Update statistik sistem ayanamsa (tolerance)
                if jrc_verification['system_detected_tolerance']:
                    sys_det_tol = jrc_verification['system_detected_tolerance']
                    if sys_det_tol in system_counts_tolerance:
                        system_counts_tolerance[sys_det_tol] += 1
                else:
                    system_counts_tolerance["no_naks_data"] += 1
                
                # ============================================================
                # Cetak informasi tithi dan naksatra
                # ============================================================
                if normalized_data.get('tithi') and normalized_data.get('paksa'):
                    t_ins = normalized_data['tithi']
                    p_ins = normalized_data['paksa']
                    t_std = jrc_verification['tithi_std_ins']
                    tithi_pras = f"{t_ins} {p_ins}"
                    if t_std and t_std != t_ins:
                        tithi_pras += f" (std {t_std})"
                    tithi_hitung = f"{jrc_verification['tithi_calculated']['tithi']} {jrc_verification['tithi_calculated']['paksa']}"
                    match_status = "✓" if jrc_verification['tithi_match'] else "✗"
                    tol_status = "✓" if jrc_verification['tithi_tolerance_match'] else "✗"
                    print(f"   Tithi prasasti: {tithi_pras:20} | Tithi hitung: {tithi_hitung:15} | Exact {match_status} | Tol±1 {tol_status}")
                
                if normalized_data.get('nakshatra'):
                    naks_pras = normalized_data['nakshatra']
                    naks_say = jrc_verification['naks_sayana']
                    naks_nir = jrc_verification['naks_nirayana']
                    sys_det = jrc_verification['system_detected']
                    sys_det_tol = jrc_verification['system_detected_tolerance']
                    print(f"   Naksatra prasasti: {naks_pras:15} | Sayana: {naks_say:15} | Nirayana: {naks_nir:15}")
                    print(f"     Exact: {sys_det.upper() if sys_det else 'NONE'} | Tol±1: {sys_det_tol.upper() if sys_det_tol else 'NONE'}")
                
                # Simpan hasil
                result_entry = {
                    "no": inscription['no'],
                    "id": inscription['id'],
                    "name": inscription['name'],
                    "saka": inscription['saka'],
                    "masa": inscription['masa'],
                    "expected_date": expected_date,
                    "converted_date": converted_date,
                    "days_diff": days_diff,
                    "status": status,
                    "ka": candidate['ka'],
                    "wuku": candidate['wuku_info']['wuku_name'],
                    "wara": candidate['wuku_info']['wara_string'],
                    "score": best_result['score'],
                    "confidence": best_result['confidence'],
                    "month_shifted": best_result.get('month_shifted', False),
                    "jrc_verification": jrc_verification
                }
                
                print(f"   Expected: {expected_date[0]}-{expected_date[1]:02d}-{expected_date[2]:02d}")
                print(f"   Converted: {converted_date[0]}-{converted_date[1]:02d}-{converted_date[2]:02d}")
                print(f"   Selisih: {days_diff} hari | {status}")
                print(f"   Wuku: {candidate['wuku_info']['wuku_name']} | Wara: {candidate['wuku_info']['wara_string']}")
                print(f"   Skor: {best_result['score']:.3f} | Confidence: {best_result['confidence']}")
                
            else:
                # Tidak ada hasil konversi
                status = "❌ NO RESULT"
                categories["no_result"] += 1
                system_counts["no_naks_data"] += 1
                system_counts_tolerance["no_naks_data"] += 1
                
                result_entry = {
                    "no": inscription['no'],
                    "id": inscription['id'],
                    "name": inscription['name'],
                    "saka": inscription['saka'],
                    "masa": inscription['masa'],
                    "expected_date": inscription['julian_date'],
                    "converted_date": None,
                    "days_diff": None,
                    "status": status,
                    "ka": None,
                    "wuku": None,
                    "wara": None,
                    "score": 0,
                    "confidence": "FAILED",
                    "month_shifted": False,
                    "jrc_verification": None
                }
                
                print(f"   Expected: {inscription['julian_date'][0]}-{inscription['julian_date'][1]:02d}-{inscription['julian_date'][2]:02d}")
                print(f"   {status}: Sistem tidak menghasilkan kandidat")
                
        except Exception as e:
            # Error dalam proses konversi
            status = f"❌ ERROR: {str(e)[:50]}"
            categories["failed"] += 1
            system_counts["no_naks_data"] += 1
            system_counts_tolerance["no_naks_data"] += 1
            
            result_entry = {
                "no": inscription['no'],
                "id": inscription['id'],
                "name": inscription['name'],
                "saka": inscription['saka'],
                "masa": inscription['masa'],
                "expected_date": inscription['julian_date'],
                "converted_date": None,
                "days_diff": None,
                "status": status,
                "ka": None,
                "wuku": None,
                "wara": None,
                "score": 0,
                "confidence": "ERROR",
                "month_shifted": False,
                "jrc_verification": None
            }
            
            print(f"   Expected: {inscription['julian_date'][0]}-{inscription['julian_date'][1]:02d}-{inscription['julian_date'][2]:02d}")
            print(f"   {status}")
        
        results.append(result_entry)
    
    # Hitung statistik batch
    total_in_batch = len(results)
    exact_matches = categories["exact_match"]
    close_matches = categories["within_3_days"]
    near_matches = categories["within_7_days"]
    within_30 = categories["within_30_days"]
    failed = categories["failed"] + categories["no_result"]
    
    print("\n" + "="*100)
    print(f"HASIL BATCH {batch_number} - RINGKASAN")
    print("="*100)
    print(f"Total prasasti dalam batch: {total_in_batch}")
    print(f"Exact Match (0 hari): {exact_matches} ({exact_matches/total_in_batch*100:.1f}%)")
    print(f"Close Match (≤3 hari): {close_matches} ({close_matches/total_in_batch*100:.1f}%)")
    print(f"Near Match (≤7 hari): {near_matches} ({near_matches/total_in_batch*100:.1f}%)")
    print(f"Within 30 hari: {within_30} ({within_30/total_in_batch*100:.1f}%)")
    print(f"Failed/No Result: {failed} ({failed/total_in_batch*100:.1f}%)")
    
    accuracy_exact = exact_matches / total_in_batch * 100
    accuracy_3days = (exact_matches + close_matches) / total_in_batch * 100
    accuracy_7days = (exact_matches + close_matches + near_matches) / total_in_batch * 100
    accuracy_30days = (exact_matches + close_matches + near_matches + within_30) / total_in_batch * 100
    
    print(f"\nAkurasi Batch {batch_number}:")
    print(f"  Exact Match: {accuracy_exact:.1f}%")
    print(f"  Within 3 days: {accuracy_3days:.1f}%")
    print(f"  Within 7 days: {accuracy_7days:.1f}%")
    print(f"  Within 30 days: {accuracy_30days:.1f}%")
    
    # ============================================================
    # STATISTIK DETEKSI SISTEM AYANAMSA (dalam batch)
    # ============================================================
    print("\nSTATISTIK SISTEM AYANAMSA (berdasarkan naksatra) - EXACT MATCH:")
    total_with_naks = sum(system_counts.values()) - system_counts["no_naks_data"]
    if total_with_naks > 0:
        print(f"  Sayana : {system_counts['sayana']} ({system_counts['sayana']/total_with_naks*100:.1f}%)")
        print(f"  Nirayana: {system_counts['nirayana']} ({system_counts['nirayana']/total_with_naks*100:.1f}%)")
        print(f"  Both   : {system_counts['both']} ({system_counts['both']/total_with_naks*100:.1f}%)")
        print(f"  None   : {system_counts['none']} ({system_counts['none']/total_with_naks*100:.1f}%)")
    else:
        print("  Tidak ada data naksatra yang cukup.")
    
    print("\nSTATISTIK SISTEM AYANAMSA (berdasarkan naksatra) - DENGAN TOLERANSI ±1:")
    total_with_naks_tol = sum(system_counts_tolerance.values()) - system_counts_tolerance["no_naks_data"]
    if total_with_naks_tol > 0:
        print(f"  Sayana : {system_counts_tolerance['sayana']} ({system_counts_tolerance['sayana']/total_with_naks_tol*100:.1f}%)")
        print(f"  Nirayana: {system_counts_tolerance['nirayana']} ({system_counts_tolerance['nirayana']/total_with_naks_tol*100:.1f}%)")
        print(f"  Both   : {system_counts_tolerance['both']} ({system_counts_tolerance['both']/total_with_naks_tol*100:.1f}%)")
        print(f"  None   : {system_counts_tolerance['none']} ({system_counts_tolerance['none']/total_with_naks_tol*100:.1f}%)")
    else:
        print("  Tidak ada data naksatra yang cukup.")
    
    # Simpan hasil batch ke file JSON
    output_file = f"quick_test_results_batch_{batch_number}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "batch_number": batch_number,
            "batch_size": batch_size,
            "start_idx": start_idx,
            "end_idx": end_idx,
            "test_date": datetime.now().isoformat(),
            "system": "Ω-STHAPATI v301.4 FINAL IMPROVED + JRC Verification",
            "total_in_batch": total_in_batch,
            "statistics": categories,
            "accuracy": {
                "exact": accuracy_exact,
                "within_3_days": accuracy_3days,
                "within_7_days": accuracy_7days,
                "within_30_days": accuracy_30days
            },
            "ayanamsa_stats": system_counts,
            "ayanamsa_stats_tolerance": system_counts_tolerance,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\nHasil batch {batch_number} disimpan ke: {output_file}")
    print("="*100)
    
    return results, categories

def run_all_batches(batch_size=10, verbose=True):
    """Jalankan semua batch secara berurutan (opsional)"""
    total = len(DAMAIS_INSCRIPTIONS)
    num_batches = (total + batch_size - 1) // batch_size
    
    all_results = []
    all_categories = {
        "exact_match": 0,
        "within_3_days": 0,
        "within_7_days": 0,
        "within_30_days": 0,
        "failed": 0,
        "no_result": 0
    }
    all_system_counts = {"sayana": 0, "nirayana": 0, "both": 0, "none": 0, "no_naks_data": 0}
    all_system_counts_tol = {"sayana": 0, "nirayana": 0, "both": 0, "none": 0, "no_naks_data": 0}
    
    for batch in range(1, num_batches + 1):
        print(f"\n{'='*100}")
        print(f"MENJALANKAN BATCH {batch}/{num_batches}")
        print(f"{'='*100}")
        res, cat = run_quick_test_batch(batch, batch_size, verbose)
        if res:
            all_results.extend(res)
            for k in all_categories:
                all_categories[k] += cat.get(k, 0)
            # Akumulasi statistik ayanamsa (perlu diambil dari file atau dari res)
            # Untuk sederhana, kita bisa baca dari file batch atau simpan sementara.
            # Di sini kita asumsikan kita tidak perlu all_system_counts.
    
    # Simpan hasil gabungan
    output_file = "quick_test_results_all.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "system": "Ω-STHAPATI v301.4 FINAL IMPROVED + JRC Verification",
            "total_tests": total,
            "batch_size": batch_size,
            "num_batches": num_batches,
            "statistics": all_categories,
            "results": all_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\nHasil semua batch disimpan ke: {output_file}")
    return all_results, all_categories

def main():
    """Menu untuk memilih batch"""
    print("\n" + "="*80)
    print("Ω-STHAPATI v301.4 FINAL IMPROVED - UJI BATCH PRASASTI DAMAIS")
    print("="*80)
    print("Database: 112 prasasti")
    print("Ukuran batch: 10 prasasti per batch")
    print("Total batch: 12 batch (batch 1-12)")
    print("-"*80)
    
    while True:
        print("\nPilih batch yang akan dijalankan (1-12), atau 0 untuk keluar:")
        try:
            choice = int(input("Batch nomor: "))
        except ValueError:
            print("Masukkan angka yang valid.")
            continue
        
        if choice == 0:
            print("Keluar dari uji batch.")
            break
        elif 1 <= choice <= 12:
            run_quick_test_batch(choice, batch_size=10, verbose=True)
        else:
            print("Batch tidak valid. Pilih 1-12.")

if __name__ == "__main__":
    main()