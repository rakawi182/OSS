"""
VSOP87D_earth.py

Modul untuk menghitung posisi dan kecepatan Bumi dalam koordinat sferis
heliosentris (longitude, latitude, radius) menggunakan teori VSOP87D.

Mengacu pada file data VSOP87D_ear.txt yang berisi deret trigonometri untuk Bumi.
Mengembalikan longitude (rad), latitude (rad), radius (AU), dan kecepatannya
(rad/hari, rad/hari, AU/hari) pada epoch dinamis dan ekliptika tanggal.

Fungsi uji: test_with_check_file() membandingkan hasil dengan referensi
dari vsop87_chk.txt untuk semua titik data Earth.
"""

import re
import math
import os

class VSOP87D_Earth:
    """
    Memuat dan mengolah deret VSOP87D untuk Bumi.

    Atribut:
        terms_L, terms_B, terms_R : list of tuple (it, A, B, C)
            Setiap term: A * T^it * cos(B + C*T), dengan T = (JD-2451545)/365250.
    """

    def __init__(self, file_path=None, data_text=None):
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.data = f.read()
        elif data_text:
            self.data = data_text
        else:
            raise ValueError("Harus menyediakan file_path atau data_text")

        self.terms_L = []
        self.terms_B = []
        self.terms_R = []
        self._parse()

    def _parse(self):
        lines = self.data.splitlines()
        i = 0
        n_lines = len(lines)

        while i < n_lines:
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            if "VARIABLE" in line and "LBR" in line:
                var_match = re.search(r"VARIABLE\s+(\d+)\s+\(LBR\)", line)
                if not var_match:
                    i += 1
                    continue
                var_idx = int(var_match.group(1))

                it_match = re.search(r"\*T\*\*(\d+)", line)
                it = int(it_match.group(1)) if it_match else 0

                terms_match = re.search(r"(\d+)\s+TERMS", line)
                if not terms_match:
                    i += 1
                    continue
                n_terms = int(terms_match.group(1))

                terms = []
                for _ in range(n_terms):
                    i += 1
                    if i >= n_lines:
                        break
                    term_line = lines[i]
                    if len(term_line) >= 132:
                        try:
                            A = float(term_line[79:97].strip())
                            B = float(term_line[97:111].strip())
                            C = float(term_line[111:131].strip())
                        except ValueError:
                            continue
                        terms.append((it, A, B, C))

                if var_idx == 1:
                    self.terms_L.extend(terms)
                elif var_idx == 2:
                    self.terms_B.extend(terms)
                elif var_idx == 3:
                    self.terms_R.extend(terms)

                i += 1
            else:
                i += 1

    def compute(self, jd):
        T = (jd - 2451545.0) / 365250.0

        def evaluate(terms):
            val = 0.0
            dval = 0.0
            for it, A, B, C in terms:
                if it == 0:
                    powT = 1.0
                    d_powT = 0.0
                else:
                    powT = T ** it
                    d_powT = it * (T ** (it - 1)) if it > 0 else 0.0

                angle = B + C * T
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)

                val += A * powT * cos_a
                dval += A * (d_powT * cos_a - powT * C * sin_a)

            return val, dval / 365250.0

        L, dL = evaluate(self.terms_L)
        B_lat, dB = evaluate(self.terms_B)
        R, dR = evaluate(self.terms_R)

        L = L % (2.0 * math.pi)

        return L, B_lat, R, dL, dB, dR


def test_with_check_file(check_file_path, data_file_path="VSOP87D_ear.txt", tol=1e-8):
    """
    Uji akurasi modul dengan membandingkan hasil perhitungan terhadap 
    nilai referensi dari file vsop87_chk.txt untuk Earth (VSOP87D).

    Args:
        check_file_path (str): Path ke file vsop87_chk.txt.
        data_file_path (str): Path ke file VSOP87D_ear.txt.
        tol (float): Toleransi absolut untuk selisih.

    Returns:
        dict: Statistik selisih untuk setiap variabel, atau None jika gagal.
    """
    earth = VSOP87D_Earth(data_file_path)

    with open(check_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Kumpulkan blok data referensi
    data_blocks = []
    i = 0
    while i < len(lines):
        if "VSOP87D  EARTH" in lines[i]:
            header = lines[i]
            jd_match = re.search(r"JD([\d.]+)", header)
            if not jd_match:
                i += 1
                continue
            jd = float(jd_match.group(1))

            if i + 2 >= len(lines):
                i += 1
                continue

            line1 = lines[i+1].strip()
            line2 = lines[i+2].strip()

            # Parsing baris pertama: l, b, r
            parts1 = line1.split()
            # Contoh: ['l', '1.7519238681', 'rad', 'b', '-.0000039656', 'rad', 'r', '.9833276819', 'au']
            if len(parts1) < 9:
                i += 1
                continue
            try:
                L_ref = float(parts1[1])
                B_ref = float(parts1[4])
                R_ref = float(parts1[7])
            except (IndexError, ValueError):
                i += 1
                continue

            # Parsing baris kedua: l', b', r'
            parts2 = line2.split()
            # Contoh: ["l'", '.0177924465', 'rad/d', "b'", '.0000001146', 'rad/d', "r'", '-.0000073533', 'au/d']
            if len(parts2) < 9:
                i += 1
                continue
            try:
                dL_ref = float(parts2[1])
                dB_ref = float(parts2[4])
                dR_ref = float(parts2[7])
            except (IndexError, ValueError):
                i += 1
                continue

            data_blocks.append((jd, L_ref, B_ref, R_ref, dL_ref, dB_ref, dR_ref))
            i += 3  # lewati header + 2 baris
        else:
            i += 1

    if not data_blocks:
        print("Tidak ditemukan data referensi untuk VSOP87D EARTH.")
        return None

    # Inisialisasi statistik
    stats = {key: {'max_diff': 0.0, 'max_jd': None, 'count': 0, 'sum_abs': 0.0}
             for key in ['L', 'B', 'R', 'dL', 'dB', 'dR']}
    keys = ['L', 'B', 'R', 'dL', 'dB', 'dR']

    print(f"{'JD':>14} {'ΔL (rad)':>12} {'ΔB (rad)':>12} {'ΔR (AU)':>12} "
          f"{'ΔdL (rad/d)':>14} {'ΔdB (rad/d)':>14} {'ΔdR (AU/d)':>14}")
    print("-" * 94)

    for jd, L_ref, B_ref, R_ref, dL_ref, dB_ref, dR_ref in data_blocks:
        L, B, R, dL, dB, dR = earth.compute(jd)

        diffs = [abs(L - L_ref), abs(B - B_ref), abs(R - R_ref),
                 abs(dL - dL_ref), abs(dB - dB_ref), abs(dR - dR_ref)]

        for i, key in enumerate(keys):
            stats[key]['count'] += 1
            stats[key]['sum_abs'] += diffs[i]
            if diffs[i] > stats[key]['max_diff']:
                stats[key]['max_diff'] = diffs[i]
                stats[key]['max_jd'] = jd

        print(f"{jd:14.1f} {diffs[0]:12.3e} {diffs[1]:12.3e} {diffs[2]:12.3e} "
              f"{diffs[3]:14.3e} {diffs[4]:14.3e} {diffs[5]:14.3e}")

    print("\n" + "=" * 94)
    print("Ringkasan selisih absolut maksimum dan rata-rata:")
    for key in keys:
        max_diff = stats[key]['max_diff']
        avg_diff = stats[key]['sum_abs'] / stats[key]['count']
        max_jd = stats[key]['max_jd']
        print(f"{key:>4} : maks = {max_diff:.3e} pada JD {max_jd:.1f}, "
              f"rata-rata = {avg_diff:.3e}")

    all_pass = all(stats[key]['max_diff'] <= tol for key in keys)
    if all_pass:
        print(f"\n✅ Semua selisih dalam toleransi {tol:.0e}.")
    else:
        print(f"\n❌ Beberapa selisih melebihi toleransi {tol:.0e}.")
        for key in keys:
            if stats[key]['max_diff'] > tol:
                print(f"   - {key} melampaui (maks = {stats[key]['max_diff']:.3e})")

    return stats


if __name__ == "__main__":
    data_file = "VSOP87D_ear.txt"
    check_file = "vsop87_chk.txt"

    if not os.path.exists(data_file):
        print(f"File {data_file} tidak ditemukan.")
    elif not os.path.exists(check_file):
        print(f"File {check_file} tidak ditemukan.")
    else:
        # Uji tunggal pada J2000
        earth = VSOP87D_Earth(data_file)
        jd = 2451545.0
        L, B, R, dL, dB, dR = earth.compute(jd)
        print(f"Hasil pada JD {jd:.1f}:")
        print(f"L  = {L:.10f} rad")
        print(f"B  = {B:.10f} rad")
        print(f"R  = {R:.10f} AU")
        print(f"dL = {dL:.10f} rad/hari")
        print(f"dB = {dB:.10f} rad/hari")
        print(f"dR = {dR:.10f} AU/hari\n")

        # Uji penuh dengan semua data referensi
        test_with_check_file(check_file, data_file, tol=1e-8)