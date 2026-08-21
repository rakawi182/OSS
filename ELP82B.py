#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ELP82B.py – Lunar solution ELP 2000-82B

Implementasi Python dari subroutine FORTRAN ELP82B untuk menghitung
koordinat geosentrik Bulan (X, Y, Z) dalam kilometer, mengacu pada
mean dynamical ecliptic dan inertial equinox J2000.

Referensi ilmiah:
    Chapront-Touzé M., Chapront J. (1983): The lunar Ephemeris ELP 2000,
    Astronomy and Astrophysics, 124, 50.
    Chapront-Touzé M., Chapront J. (1988): ELP 2000-85: a semi-analytical
    lunar ephemeris adequate for historical times,
    Astronomy and Astrophysics, 190, 342.
    Chapront-Touzé M., Chapront J., Francou G. (2001):
    Lunar solution ELP, version ELP 2000-82B (internal document).

Penggunaan:
    from ELP82B import ELP82B
    elp = ELP82B(data_dir='.', ext='.txt')
    x, y, z = elp.compute(2469000.5, trunk=0.0)

Metode:
    - Membaca 36 file data (ELP01–ELP36) sesuai format fixed-width yang dijelaskan
      dalam dokumen (Bagian 2.2).
    - Menggunakan konstanta dan argumen fundamental dari Bagian 4–7.
    - Menerapkan koreksi konstanta fitting ke DE200/LE200 (Bagian 7).
    - Menghitung longitude, latitude, distance dengan penjumlahan seri Fourier
      dan Poisson (Bagian 8).
    - Mengkonversi ke koordinat kartesian dan merotasi ke sistem J2000
      menggunakan polinomial P dan Q Laskar (Bagian 8).
"""

import math
import os
import sys
from typing import List, Tuple, Optional

# ============================================================================
# Konstanta dasar (sesuai Bagian 2.3 dan 6)
# ============================================================================
CPI = math.pi
CPI2 = 2.0 * CPI
PIS2 = CPI / 2.0
RAD = 648000.0 / CPI          # detik busur per radian (206264.806")
DEG = CPI / 180.0
DJ2000 = 2451545.0            # Julian Date epoch J2000.0
SC = 36525.0                  # hari per abad Julian
ATH = 384747.9806743165       # km, skala jarak (dari FORTRAN)
A0 = 384747.9806448954        # km, semi-major axis Keplerian (Bagian 6)


class ELP82B:
    """
    Kelas utama untuk ephemeris Bulan ELP 2000-82B.
    """

    def __init__(self, data_dir: str = '.', ext: str = '.txt', verbose: bool = False):
        """
        Inisialisasi dengan membaca 36 file data.

        Parameters:
            data_dir : str, direktori tempat file ELP01–ELP36 berada.
            ext      : str, ekstensi file (misal '.txt' atau '').
            verbose  : bool, cetak pesan peringatan jika baris tidak sesuai format.
        """
        self.data_dir = data_dir
        self.ext = ext
        self.verbose = verbose

        # Inisialisasi konstanta dan argumen fundamental (Bagian 4–6)
        self._init_constants()

        # Membaca semua seri dari file data (Bagian 2.2)
        self._read_all_series()

    # ------------------------------------------------------------------------
    # 1. Inisialisasi konstanta fundamental
    # ------------------------------------------------------------------------
    def _init_constants(self):
        """
        Menginisialisasi semua konstanta dan argumen fundamental sesuai
        Bagian 4, 5, 6, dan 7 dari dokumen ELP 2000-82B.
        """
        # --- Konstanta koreksi dari fitting DE200/LE200 (Bagian 7) ---
        # Nilai-nilai ini diambil dari FORTRAN (delnu, dele, delg, delnp, delep)
        self.am = 0.074801329518
        self.alpha = 0.002571881335
        self.dtasm = 2.0 * self.alpha / (3.0 * self.am)

        w11 = 1732559343.73604 / RAD   # ν (mean motion Bulan) dalam rad/cy
        self.delnu = 0.55604 / RAD / w11
        self.dele = 0.01789 / RAD
        self.delg = -0.08066 / RAD
        self.delnp = -0.06424 / RAD / w11
        self.delep = -0.12879 / RAD

        # --- Argumen fundamental W1, W2, W3, T, π' (Bagian 4, persamaan 1) ---
        # W1 = mean longitude of Moon
        self.w1 = [
            self._dms_to_rad(218, 18, 59.95571),   # W1^(0)
            1732559343.73604 / RAD,                # W1^(1)
            -5.8883 / RAD,                         # W1^(2)
            0.006604 / RAD,                        # W1^(3)
            -0.00003169 / RAD                      # W1^(4)
        ]
        # W2 = mean longitude of lunar perigee
        self.w2 = [
            self._dms_to_rad(83, 21, 11.67475),
            14643420.2632 / RAD,
            -38.2776 / RAD,
            -0.045047 / RAD,
            0.00021301 / RAD
        ]
        # W3 = mean longitude of ascending node
        self.w3 = [
            self._dms_to_rad(125, 2, 40.39816),
            -6967919.3622 / RAD,
            6.3622 / RAD,
            0.007625 / RAD,
            -0.00003586 / RAD
        ]
        # T = mean heliocentric longitude of Earth-Moon barycenter
        self.eart = [
            self._dms_to_rad(100, 27, 59.22059),
            129597742.2758 / RAD,
            -0.0202 / RAD,
            0.000009 / RAD,
            0.00000015 / RAD
        ]
        # π' = mean longitude of perihelion of Earth-Moon barycenter
        self.peri = [
            self._dms_to_rad(102, 56, 14.42753),
            1161.2283 / RAD,    # catatan: di FORTRAN, koef t adalah 1161.2283/rad
            0.5327 / RAD,
            -0.000138 / RAD,
            0.0
        ]

        # Precession constant p (Bagian 4, ζ = W1 + p*t)
        self.precess = 5029.0966 / RAD   # "/cy -> rad/cy

        # --- Delaunay arguments D, l', l, F (Bagian 4) ---
        # D = W1 - T + π  (π ditambahkan di konstanta)
        # l' = T - π'
        # l = W1 - W2
        # F = W1 - W3
        # Indeks 0..4 untuk t^0, t^1, t^2, t^3, t^4
        self.del0 = [
            self.w1[0] - self.eart[0] + CPI,
            self.eart[0] - self.peri[0],
            self.w1[0] - self.w2[0],
            self.w1[0] - self.w3[0]
        ]
        self.del1 = [
            self.w1[1] - self.eart[1],
            self.eart[1] - self.peri[1],
            self.w1[1] - self.w2[1],
            self.w1[1] - self.w3[1]
        ]
        self.del2 = [
            self.w1[2] - self.eart[2],
            self.eart[2] - self.peri[2],
            self.w1[2] - self.w2[2],
            self.w1[2] - self.w3[2]
        ]
        self.del3 = [
            self.w1[3] - self.eart[3],
            self.eart[3] - self.peri[3],
            self.w1[3] - self.w2[3],
            self.w1[3] - self.w3[3]
        ]
        self.del4 = [
            self.w1[4] - self.eart[4],
            self.eart[4] - self.peri[4],
            self.w1[4] - self.w2[4],
            self.w1[4] - self.w3[4]
        ]

        # ζ = W1 + p*t (linear)
        self.zeta0 = self.w1[0]
        self.zeta1 = self.w1[1] + self.precess

        # --- Planetary longitudes (Me, V, Ma, J, S, U, N) dan T (Bagian 4, Tabel F) ---
        # planet0 dan planet1 adalah konstanta dan koef t untuk masing-masing planet
        self.planet0 = [
            self._dms_to_rad(252, 15, 3.25986),    # Me
            self._dms_to_rad(181, 58, 47.28305),   # V
            self.eart[0],                          # T (Earth-Moon barycenter)
            self._dms_to_rad(355, 25, 59.78866),   # Ma
            self._dms_to_rad(34, 21, 5.34212),     # J
            self._dms_to_rad(50, 4, 38.89694),     # S
            self._dms_to_rad(314, 3, 18.01841),    # U
            self._dms_to_rad(304, 20, 55.19575)    # N
        ]
        self.planet1 = [
            538101628.68898 / RAD,
            210664136.43355 / RAD,
            self.eart[1],
            68905077.59284 / RAD,
            10925660.42861 / RAD,
            4399609.65932 / RAD,
            1542481.19393 / RAD,
            786550.32074 / RAD
        ]

        # --- Koefisien P dan Q untuk rotasi ke J2000 (Bagian 8, Laskar 1986) ---
        self.p1 = 0.10180391e-4
        self.p2 = 0.47020439e-6
        self.p3 = -0.5417367e-9
        self.p4 = -0.2507948e-11
        self.p5 = 0.463486e-14
        self.q1 = -0.113469002e-3
        self.q2 = 0.12372674e-6
        self.q3 = 0.1265417e-8
        self.q4 = -0.1371808e-11
        self.q5 = -0.320334e-14

    @staticmethod
    def _dms_to_rad(deg: float, arcmin: float, arcsec: float) -> float:
        """Konversi derajat, menit, detik ke radian."""
        return (deg + arcmin / 60.0 + arcsec / 3600.0) * DEG

    # ------------------------------------------------------------------------
    # 2. Membaca file data (sesuai Bagian 2.2)
    # ------------------------------------------------------------------------
    def _read_all_series(self):
        """
        Membaca 36 file data dan menyimpan seri Fourier dalam struktur internal.

        Format file dijelaskan di Bagian 2.2:
        - ELP01–ELP03: format 4I3,2X,F13.5,6(2X,F10.2)
        - ELP04–ELP09 dan ELP22–ELP36: 5I3,1X,F9.5,1X,F9.3
        - ELP10–ELP15: 11I3,1X,F9.5,1X,F9.5
        - ELP16–ELP21: 11I3,1X,F9.5,1X,F9.5

        Untuk menghindari masalah spasi dan token gabungan (misal '4-11'),
        kita menggunakan pembacaan berbasis indeks karakter (fixed-width),
        bukan split().
        """
        # Wadah seri:
        # main_terms[iv] berisi tuple (amp, c0, c1, c2, c3, c4) untuk iv=0(long),1(lat),2(dist)
        self.main_terms = [[], [], []]
        # non_main_terms[iv] berisi tuple (itab, amp, arg0, arg1)
        self.non_main_terms = [[], [], []]

        for ific in range(1, 37):
            filename = f"ELP{ific:02d}{self.ext}"
            filepath = os.path.join(self.data_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    lines = f.readlines()
            except FileNotFoundError:
                raise FileNotFoundError(f"File data tidak ditemukan: {filepath}")

            if not lines:
                continue

            # Baris pertama adalah judul, diabaikan
            data_lines = lines[1:]

            # itab = kelompok (1..12), iv = jenis koordinat (0,1,2)
            itab = (ific + 2) // 3
            iv = (ific - 1) % 3

            if 1 <= ific <= 3:
                # --- ELP01–ELP03 : Main problem ---
                terms = self.main_terms[iv]
                for line in data_lines:
                    line = line.rstrip('\n')
                    if len(line) < 60:
                        if self.verbose:
                            print(f"Skip short line in {filename}: {line}")
                        continue
                    # Parsing fixed-width:
                    # i1: col 0-2, i2: 3-5, i3: 6-8, i4: 9-11
                    # A: col 14-26 (F13.5), B1..B6: col 29-38, 41-50, 53-62, ...
                    try:
                        i1 = int(line[0:3])
                        i2 = int(line[3:6])
                        i3 = int(line[6:9])
                        i4 = int(line[9:12])
                        A = float(line[14:27])
                        B1 = float(line[29:39]) if len(line) > 39 else 0.0
                        B2 = float(line[41:51]) if len(line) > 51 else 0.0
                        B3 = float(line[53:63]) if len(line) > 63 else 0.0
                        B4 = float(line[65:75]) if len(line) > 75 else 0.0
                        B5 = float(line[77:87]) if len(line) > 87 else 0.0
                        B6 = float(line[89:99]) if len(line) > 99 else 0.0
                    except (ValueError, IndexError):
                        if self.verbose:
                            print(f"Parse error in {filename}: {line}")
                        continue

                    # Koreksi konstanta seperti di FORTRAN (Bagian 7)
                    if ific == 3:   # distance
                        A = A - (2.0 / 3.0) * A * self.delnu
                    tgv = B1 + self.dtasm * B5
                    amp = A + tgv * (self.delnp - self.am * self.delnu) \
                          + B2 * self.delg + B3 * self.dele + B4 * self.delep

                    # Argumen polinomial derajat 4: Σ A sin(i1*D + i2*l' + i3*l + i4*F)
                    c0 = i1 * self.del0[0] + i2 * self.del0[1] + i3 * self.del0[2] + i4 * self.del0[3]
                    c1 = i1 * self.del1[0] + i2 * self.del1[1] + i3 * self.del1[2] + i4 * self.del1[3]
                    c2 = i1 * self.del2[0] + i2 * self.del2[1] + i3 * self.del2[2] + i4 * self.del2[3]
                    c3 = i1 * self.del3[0] + i2 * self.del3[1] + i3 * self.del3[2] + i4 * self.del3[3]
                    c4 = i1 * self.del4[0] + i2 * self.del4[1] + i3 * self.del4[2] + i4 * self.del4[3]
                    terms.append((amp, c0, c1, c2, c3, c4))

            elif 4 <= ific <= 9 or 22 <= ific <= 36:
                # --- ELP04–ELP09 dan ELP22–ELP36 ---
                # Format: 5I3,1X,F9.5,1X,F9.3
                terms = self.non_main_terms[iv]
                for line in data_lines:
                    line = line.rstrip('\n')
                    if len(line) < 30:
                        if self.verbose:
                            print(f"Skip short line in {filename}: {line}")
                        continue
                    try:
                        i1 = int(line[0:3])
                        i2 = int(line[3:6])
                        i3 = int(line[6:9])
                        i4 = int(line[9:12])
                        i5 = int(line[12:15])
                        phi = float(line[16:25]) * DEG
                        amp = float(line[26:35])
                    except (ValueError, IndexError):
                        if self.verbose:
                            print(f"Parse error in {filename}: {line}")
                        continue

                    # Argumen linear: i1*ζ + i2*D + i3*l' + i4*l + i5*F + φ
                    arg0 = i1 * self.zeta0 + i2 * self.del0[0] + i3 * self.del0[1] \
                           + i4 * self.del0[2] + i5 * self.del0[3] + phi
                    arg1 = i1 * self.zeta1 + i2 * self.del1[0] + i3 * self.del1[1] \
                           + i4 * self.del1[2] + i5 * self.del1[3]
                    terms.append((itab, amp, arg0, arg1))

            elif 10 <= ific <= 15 or 16 <= ific <= 21:
                # --- ELP10–ELP21 : Planetary perturbations (Table 1 & 2) ---
                # Format: 11I3,1X,F9.5,1X,F9.5
                terms = self.non_main_terms[iv]
                for line in data_lines:
                    line = line.rstrip('\n')
                    if len(line) < 45:
                        if self.verbose:
                            print(f"Skip short line in {filename}: {line}")
                        continue
                    try:
                        i1 = int(line[0:3]); i2 = int(line[3:6]); i3 = int(line[6:9])
                        i4 = int(line[9:12]); i5 = int(line[12:15]); i6 = int(line[15:18])
                        i7 = int(line[18:21]); i8 = int(line[21:24]); i9 = int(line[24:27])
                        i10 = int(line[27:30]); i11 = int(line[30:33])
                        phi = float(line[34:43]) * DEG
                        amp = float(line[44:53])
                    except (ValueError, IndexError):
                        if self.verbose:
                            print(f"Parse error in {filename}: {line}")
                        continue

                    if ific <= 15:  # Table 1
                        # Argumen: i1*Me + i2*V + i3*T + i4*Ma + i5*J + i6*S + i7*U + i8*N
                        #         + i9*D + i10*l + i11*F + phi
                        arg0 = (i1 * self.planet0[0] + i2 * self.planet0[1] + i3 * self.planet0[2] +
                                i4 * self.planet0[3] + i5 * self.planet0[4] + i6 * self.planet0[5] +
                                i7 * self.planet0[6] + i8 * self.planet0[7] +
                                i9 * self.del0[0] + i10 * self.del0[2] + i11 * self.del0[3] + phi)
                        arg1 = (i1 * self.planet1[0] + i2 * self.planet1[1] + i3 * self.planet1[2] +
                                i4 * self.planet1[3] + i5 * self.planet1[4] + i6 * self.planet1[5] +
                                i7 * self.planet1[6] + i8 * self.planet1[7] +
                                i9 * self.del1[0] + i10 * self.del1[2] + i11 * self.del1[3])
                    else:  # Table 2
                        # Argumen: i1*Me + i2*V + i3*T + i4*Ma + i5*J + i6*S + i7*U
                        #         + i8*D + i9*l' + i10*l + i11*F + phi
                        arg0 = (i1 * self.planet0[0] + i2 * self.planet0[1] + i3 * self.planet0[2] +
                                i4 * self.planet0[3] + i5 * self.planet0[4] + i6 * self.planet0[5] +
                                i7 * self.planet0[6] +
                                i8 * self.del0[0] + i9 * self.del0[1] + i10 * self.del0[2] + i11 * self.del0[3] + phi)
                        arg1 = (i1 * self.planet1[0] + i2 * self.planet1[1] + i3 * self.planet1[2] +
                                i4 * self.planet1[3] + i5 * self.planet1[4] + i6 * self.planet1[5] +
                                i7 * self.planet1[6] +
                                i8 * self.del1[0] + i9 * self.del1[1] + i10 * self.del1[2] + i11 * self.del1[3])
                    terms.append((itab, amp, arg0, arg1))

            else:
                # Seharusnya tidak terjadi
                continue

    # ------------------------------------------------------------------------
    # 3. Komputasi koordinat (Bagian 8)
    # ------------------------------------------------------------------------
    def compute(self, tjj: float, trunk: float = 0.0) -> Tuple[float, float, float]:
        """
        Menghitung koordinat geosentrik Bulan (X, Y, Z) dalam km.

        Parameters:
            tjj   : float, Julian Date TDB (misal 2469000.5)
            trunk : float, level truncation dalam radian. Term dengan amplitudo
                    lebih kecil dari trunk akan diabaikan. trunk=0 berarti semua term.

        Returns:
            (X, Y, Z) dalam km, referensi mean ecliptic dan equinox J2000.
        """
        # Waktu dalam abad Julian sejak J2000.0
        t = (tjj - DJ2000) / SC
        t2 = t * t
        t3 = t2 * t
        t4 = t3 * t

        # Ambang batas untuk truncation (dalam satuan asli)
        prec_lon_lat = trunk * RAD      # arcsec
        prec_dist = trunk * ATH         # km

        # Inisialisasi penjumlahan
        sum_lon = 0.0   # arcsec
        sum_lat = 0.0   # arcsec
        sum_dist = 0.0  # km

        # --- 3a. Main problem (itab=1) ---
        # Longitude
        for amp, c0, c1, c2, c3, c4 in self.main_terms[0]:
            if trunk > 0 and abs(amp) < prec_lon_lat:
                continue
            y = c0 + c1*t + c2*t2 + c3*t3 + c4*t4
            sum_lon += amp * math.sin(y)
            
        # Latitude
        for amp, c0, c1, c2, c3, c4 in self.main_terms[1]:
            if trunk > 0 and abs(amp) < prec_lon_lat:
                continue
            y = c0 + c1*t + c2*t2 + c3*t3 + c4*t4
            sum_lat += amp * math.sin(y)
            
        # Distance (BENAR: Gunakan Cosine)
        for amp, c0, c1, c2, c3, c4 in self.main_terms[2]:
            if trunk > 0 and abs(amp) < prec_dist:
                continue
            y = c0 + c1*t + c2*t2 + c3*t3 + c4*t4
            sum_dist += amp * math.cos(y) 

        # --- 3b. Non-main terms (itab=2..12) ---
        # Longitude
        for itab, amp, arg0, arg1 in self.non_main_terms[0]:
            if trunk > 0 and abs(amp) < prec_lon_lat:
                continue
            mult = 1.0
            if itab in (3, 5, 7, 9):   # Poisson terms dengan faktor t
                mult = t
            elif itab == 12:           # t^2 terms (ELP34–ELP36)
                mult = t2
            y = arg0 + arg1 * t
            sum_lon += amp * math.sin(y) * mult

        # Latitude
        for itab, amp, arg0, arg1 in self.non_main_terms[1]:
            if trunk > 0 and abs(amp) < prec_lon_lat:
                continue
            mult = 1.0
            if itab in (3, 5, 7, 9):
                mult = t
            elif itab == 12:
                mult = t2
            y = arg0 + arg1 * t
            sum_lat += amp * math.sin(y) * mult

        # Distance (Non-main terms)
        for itab, amp, arg0, arg1 in self.non_main_terms[2]:
            if trunk > 0 and abs(amp) < prec_dist:
                continue
            mult = 1.0
            if itab in (3, 5, 7, 9):
                mult = t
            elif itab == 12:
                mult = t2
            y = arg0 + arg1 * t
            sum_dist += amp * math.sin(y) * mult

        # --- 3c. Koordinat spherical dalam sistem referensi ELP82B (Bagian 8) ---
        # Longitude V = sum_lon / RAD + W1(t)
        W1 = self.w1[0] + self.w1[1]*t + self.w1[2]*t2 + self.w1[3]*t3 + self.w1[4]*t4
        V = sum_lon / RAD + W1
        U = sum_lat / RAD
        R = sum_dist * (A0 / ATH)   # skala jarak (≈ sum_dist)

        # --- 3d. Konversi ke kartesian (sistem ecliptic of date) ---
        cosU = math.cos(U)
        sinU = math.sin(U)
        cosV = math.cos(V)
        sinV = math.sin(V)
        x1 = R * cosU * cosV
        x2 = R * cosU * sinV
        x3 = R * sinU

        # --- 3e. Rotasi ke mean ecliptic J2000 menggunakan P dan Q (Laskar, 1986) ---
        pw = (self.p1 + self.p2*t + self.p3*t2 + self.p4*t3 + self.p5*t4) * t
        qw = (self.q1 + self.q2*t + self.q3*t2 + self.q4*t3 + self.q5*t4) * t

        ra = 2.0 * math.sqrt(max(0.0, 1.0 - pw*pw - qw*qw))
        pwqw = 2.0 * pw * qw
        pw2 = 1.0 - 2.0 * pw * pw
        qw2 = 1.0 - 2.0 * qw * qw
        pw = pw * ra
        qw = qw * ra

        X = pw2 * x1 + pwqw * x2 + pw * x3
        Y = pwqw * x1 + qw2 * x2 - qw * x3
        Z = -pw * x1 + qw * x2 + (pw2 + qw2 - 1.0) * x3

        return X, Y, Z

    def compute_spherical(self, tjj: float, trunk: float = 0.0) -> Tuple[float, float, float]:
        """
        Menghitung longitude (rad), latitude (rad), dan distance (km)
        dalam mean dynamical ecliptic of date dan departure point gamma'2000
        (sistem natural ELP2000-82B, SEBELUM rotasi ke J2000).

        Parameters:
            tjj   : float, Julian Date TDB
            trunk : float, level truncation dalam radian (default 0 = semua term)

        Returns:
            (longitude_rad, latitude_rad, distance_km)
        """
        t = (tjj - DJ2000) / SC
        t2 = t * t
        t3 = t2 * t
        t4 = t3 * t

        prec_lon_lat = trunk * RAD
        prec_dist = trunk * ATH

        sum_lon = 0.0
        sum_lat = 0.0
        sum_dist = 0.0

        # --- Main problem (itab=1) ---
        # Longitude
        for amp, c0, c1, c2, c3, c4 in self.main_terms[0]:
            if trunk > 0 and abs(amp) < prec_lon_lat:
                continue
            y = c0 + c1*t + c2*t2 + c3*t3 + c4*t4
            sum_lon += amp * math.sin(y)
        # Latitude
        for amp, c0, c1, c2, c3, c4 in self.main_terms[1]:
            if trunk > 0 and abs(amp) < prec_lon_lat:
                continue
            y = c0 + c1*t + c2*t2 + c3*t3 + c4*t4
            sum_lat += amp * math.sin(y)
        # Distance (cosine)
        for amp, c0, c1, c2, c3, c4 in self.main_terms[2]:
            if trunk > 0 and abs(amp) < prec_dist:
                continue
            y = c0 + c1*t + c2*t2 + c3*t3 + c4*t4
            sum_dist += amp * math.cos(y)

        # --- Non-main terms (itab=2..12) ---
        # Longitude
        for itab, amp, arg0, arg1 in self.non_main_terms[0]:
            if trunk > 0 and abs(amp) < prec_lon_lat:
                continue
            mult = 1.0
            if itab in (3, 5, 7, 9):
                mult = t
            elif itab == 12:
                mult = t2
            y = arg0 + arg1 * t
            sum_lon += amp * math.sin(y) * mult

        # Latitude
        for itab, amp, arg0, arg1 in self.non_main_terms[1]:
            if trunk > 0 and abs(amp) < prec_lon_lat:
                continue
            mult = 1.0
            if itab in (3, 5, 7, 9):
                mult = t
            elif itab == 12:
                mult = t2
            y = arg0 + arg1 * t
            sum_lat += amp * math.sin(y) * mult

        # Distance
        for itab, amp, arg0, arg1 in self.non_main_terms[2]:
            if trunk > 0 and abs(amp) < prec_dist:
                continue
            mult = 1.0
            if itab in (3, 5, 7, 9):
                mult = t
            elif itab == 12:
                mult = t2
            y = arg0 + arg1 * t
            sum_dist += amp * math.sin(y) * mult

        # Mean longitude W1 (rad)
        W1 = (self.w1[0] + self.w1[1]*t + self.w1[2]*t2 +
              self.w1[3]*t3 + self.w1[4]*t4)

        lon = sum_lon / RAD + W1
        lat = sum_lat / RAD
        dist = sum_dist * (A0 / ATH)   # skala jarak

        return lon, lat, dist


# ============================================================================
# Contoh penggunaan dan uji dengan nilai check dari Tabel H (Bagian 9)
# ============================================================================
if __name__ == "__main__":
    # Inisialisasi engine ELP82B
    elp = ELP82B()
    
    # Nilai check dari Tabel H
    test_dates = [2469000.5, 2449000.5, 2429000.5, 2409000.5, 2389000.5]
    expected = [
        (-361602.985, 44996.995, -30696.653),
        (-363132.342, 35863.654, -33196.004),
        (-371577.582, 75271.143, -32227.946),
        (-373896.159, 127406.791, -30037.792),
        (-346331.774, 206365.404, -28502.117),
    ]

    # Kode ANSI untuk teks tebal (Bold) dan reset
    B = "\033[1m"
    R = "\033[0m"
    W = 72  # Lebar layar konsol
    
    # Mencetak Header
    print(f"{B}{'=' * W}{R}")
    print(f"{B}{'ELP 2000-82B Check Values (Tabel H)':^{W}}{R}")
    print(f"{B}{'=' * W}{R}")
    
    # Header kolom
    header_cols = f"{'TJJ / Label':<14}{'X (km)':>18}{'Y (km)':>18}{'Z (km)':>20}"
    print(f"{B}{header_cols}{R}")
    print(f"{B}{'-' * W}{R}")

    # Mencetak Data
    for jd, ex in zip(test_dates, expected):
        # Hitung koordinat (trunk=0.0 berarti presisi penuh)
        x, y, z = elp.compute(jd, trunk=0.0)
        
        # Hitung selisih absolut
        dx = abs(x - ex[0])
        dy = abs(y - ex[1])
        dz = abs(z - ex[2])
        
        # Cetak TJJ sebagai pemisah bagian (Tebal)
        print(f"{B}{jd:<14.1f}{R}")
        
        # Baris Referensi (3 desimal sesuai dokumen asli)
        print(f"{'  Referensi  :':<14}{ex[0]:18.3f}{ex[1]:18.3f}{ex[2]:20.3f}")
        
        # Baris Hasil Komputasi (6 desimal)
        print(f"{'  Komputasi  :':<14}{x:18.6f}{y:18.6f}{z:20.6f}")
        
        # Baris Selisih (Label Tebal)
        print(f"{B}{'  [Δ] Selisih:':<14}{R}{dx:18.6f}{dy:18.6f}{dz:20.6f}")
        
        # Garis pembatas antar JD
        print(f"{B}{'-' * W}{R}")

