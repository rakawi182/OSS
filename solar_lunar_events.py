#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
solar_lunar_events.py
Modul untuk menghitung fenomena matahari dan bulan dengan tampilan menu interaktif.
Dapat dijalankan secara mandiri.
"""

import sys
sys.dont_write_bytecode = True

import math
from datetime import datetime, timedelta

from JRC_Ephemeris import (
    VSOP87SolarEngine,
    LunarELP82Engine,
    TimeSystem,
    IAU2023UltraPrecision,
    UnifiedCoordinateTransformer,
    AtmosphericModel,
    HighPrecisionNutation,
    JPLStyleTopocentricCorrections    
)


# ============================================================================
# KELAS UNTUK FENOMENA MATAHARI
# ============================================================================

class SolarEvents:
    def __init__(self, sun_engine=None, time_sys=None):
        self.sun_engine = sun_engine if sun_engine else VSOP87SolarEngine()
        self.time_sys = time_sys if time_sys else TimeSystem()
        self.const = IAU2023UltraPrecision()

    def _sun_longitude(self, jd_tt):
        data = self.sun_engine.calculate_sun_position_vsop87d(jd_tt, 'ecliptic_apparent')
        return data['longitude_deg']

    def _sun_longitude_derivative(self, jd_tt, delta=0.1):
        l1 = self._sun_longitude(jd_tt + delta/2)
        l2 = self._sun_longitude(jd_tt - delta/2)
        diff = (l1 - l2 + 180) % 360 - 180
        return diff / delta

    def find_event(self, year, target_lon):
        """Cari JD TT dari event dengan bujur target (0,90,180,270) pada tahun tertentu."""
        if target_lon == 0:      day_of_year = 79   # 20 Maret
        elif target_lon == 90:   day_of_year = 172  # 21 Juni
        elif target_lon == 180:  day_of_year = 265  # 22 September
        elif target_lon == 270:  day_of_year = 355  # 21 Desember
        else:
            raise ValueError("target_lon harus 0, 90, 180, atau 270")

        jd_utc_jan1 = self.time_sys.date_to_jd_utc(year, 1, 1, 0, 0, 0)
        jd_tt_jan1 = self.time_sys.jd_utc_to_tt_extended(jd_utc_jan1)
        guess = jd_tt_jan1 + day_of_year

        for _ in range(10):
            lon = self._sun_longitude(guess)
            diff = (lon - target_lon + 180) % 360 - 180
            if abs(diff) < 1e-6:
                break
            deriv = self._sun_longitude_derivative(guess)
            if abs(deriv) < 1e-12:
                break
            guess -= diff / deriv

        lon_final = self._sun_longitude(guess)
        diff_final = (lon_final - target_lon + 180) % 360 - 180
        return guess, lon_final, diff_final

    def find_aphelion(self, year):
        jd_utc_jan1 = self.time_sys.date_to_jd_utc(year, 1, 1, 0, 0, 0)
        jd_tt_jan1 = self.time_sys.jd_utc_to_tt_extended(jd_utc_jan1)
        guess = jd_tt_jan1 + 185  # sekitar 4 Juli

        def _sun_dist(jd):
            data = self.sun_engine.calculate_sun_position_vsop87d(jd, 'ecliptic_apparent')
            return data['radius_au']

        def _sun_dist_deriv(jd, delta=0.1):
            r1 = _sun_dist(jd + delta/2)
            r2 = _sun_dist(jd - delta/2)
            return (r1 - r2) / delta

        for _ in range(10):
            drdt = _sun_dist_deriv(guess)
            if abs(drdt) < 1e-8:
                break
            drdt_plus = _sun_dist_deriv(guess + 0.1)
            drdt_minus = _sun_dist_deriv(guess - 0.1)
            d2rdt2 = (drdt_plus - drdt_minus) / 0.2
            if abs(d2rdt2) < 1e-12:
                break
            guess -= drdt / d2rdt2

        return guess, _sun_dist(guess)

    def find_perihelion(self, year):
        jd_utc_jan1 = self.time_sys.date_to_jd_utc(year, 1, 1, 0, 0, 0)
        jd_tt_jan1 = self.time_sys.jd_utc_to_tt_extended(jd_utc_jan1)
        guess = jd_tt_jan1 + 2  # sekitar 3 Januari

        def _sun_dist(jd):
            data = self.sun_engine.calculate_sun_position_vsop87d(jd, 'ecliptic_apparent')
            return data['radius_au']

        def _sun_dist_deriv(jd, delta=0.1):
            r1 = _sun_dist(jd + delta/2)
            r2 = _sun_dist(jd - delta/2)
            return (r1 - r2) / delta

        for _ in range(10):
            drdt = _sun_dist_deriv(guess)
            if abs(drdt) < 1e-8:
                break
            drdt_plus = _sun_dist_deriv(guess + 0.1)
            drdt_minus = _sun_dist_deriv(guess - 0.1)
            d2rdt2 = (drdt_plus - drdt_minus) / 0.2
            if abs(d2rdt2) < 1e-12:
                break
            guess -= drdt / d2rdt2

        return guess, _sun_dist(guess)


# ============================================================================
# KELAS LUNAR EVENTS - VERSI LENGKAP DENGAN SEMUA METHOD
# ============================================================================

class LunarEvents:
    def __init__(self, lunar_engine=None, sun_engine=None, time_sys=None):
        self.lunar_engine = lunar_engine if lunar_engine else LunarELP82Engine()
        self.sun_engine = sun_engine if sun_engine else VSOP87SolarEngine()
        self.time_sys = time_sys if time_sys else TimeSystem()
        self.const = IAU2023UltraPrecision()
        self.synodic_month = 29.530588861  # rata-rata bulan sinodik (hari)

    # ---------- Fungsi dasar posisi ----------
    def _moon_longitude(self, jd_tt):
        data = self.lunar_engine.calculate_position(jd_tt, output_frame='ecliptic_apparent')
        return data['ecliptic_apparent']['longitude_deg']

    def _sun_longitude(self, jd_tt):
        data = self.sun_engine.calculate_sun_position_vsop87d(jd_tt, 'ecliptic_apparent')
        return data['longitude_deg']

    def _moon_distance(self, jd_tt):
        data = self.lunar_engine.calculate_position(jd_tt, output_frame='ecliptic_apparent')
        return data['distance_km']

    def _moon_declination(self, jd_tt):
        data = self.lunar_engine.calculate_position(jd_tt, output_frame='equatorial_apparent')
        return data['equatorial_apparent']['dec_deg']

    # ---------- Turunan numerik ----------
    def _moon_longitude_deriv(self, jd_tt, delta=0.1):
        l1 = self._moon_longitude(jd_tt + delta)
        l2 = self._moon_longitude(jd_tt - delta)
        diff = (l1 - l2 + 180) % 360 - 180
        return diff / (2 * delta)

    def _sun_longitude_deriv(self, jd_tt, delta=0.1):
        l1 = self._sun_longitude(jd_tt + delta)
        l2 = self._sun_longitude(jd_tt - delta)
        diff = (l1 - l2 + 180) % 360 - 180
        return diff / (2 * delta)

    def _moon_distance_deriv(self, jd_tt, delta=0.1):
        r1 = self._moon_distance(jd_tt + delta)
        r2 = self._moon_distance(jd_tt - delta)
        return (r1 - r2) / (2 * delta)

    def _moon_declination_deriv(self, jd_tt, delta=0.1):
        d1 = self._moon_declination(jd_tt + delta)
        d2 = self._moon_declination(jd_tt - delta)
        return (d1 - d2) / (2 * delta)

    # ---------- Pencarian new moon & full moon ----------
    def find_new_moon(self, jd_tt_guess):
        """Cari new moon terdekat dari tebakan JD TT."""
        for _ in range(15):
            lon_m = self._moon_longitude(jd_tt_guess)
            lon_s = self._sun_longitude(jd_tt_guess)
            diff = (lon_m - lon_s + 180) % 360 - 180
            if abs(diff) < 1e-6:
                break
            dm = self._moon_longitude_deriv(jd_tt_guess)
            ds = self._sun_longitude_deriv(jd_tt_guess)
            deriv = dm - ds
            if abs(deriv) < 1e-12:
                break
            jd_tt_guess -= diff / deriv
        return jd_tt_guess

    def find_full_moon(self, jd_tt_guess):
        """Cari full moon terdekat dari tebakan JD TT."""
        for _ in range(15):
            lon_m = self._moon_longitude(jd_tt_guess)
            lon_s = self._sun_longitude(jd_tt_guess)
            diff = (lon_m - lon_s - 180 + 180) % 360 - 180
            if abs(diff) < 1e-6:
                break
            dm = self._moon_longitude_deriv(jd_tt_guess)
            ds = self._sun_longitude_deriv(jd_tt_guess)
            deriv = dm - ds
            if abs(deriv) < 1e-12:
                break
            jd_tt_guess -= diff / deriv
        return jd_tt_guess

    def find_elongation_time(self, jd_tt_guess: float, target_elong_deg: float) -> float:
        """
        Cari JD TT ketika elongasi (bulan - matahari) mencapai target_elong_deg (0-360°).
        Menggunakan iterasi Newton.
        """
        jd = jd_tt_guess
        for _ in range(15):
            lon_m = self._moon_longitude(jd)
            lon_s = self._sun_longitude(jd)
            elong = (lon_m - lon_s) % 360
            diff = (elong - target_elong_deg + 180) % 360 - 180
            if abs(diff) < 1e-6:
                break
            dm = self._moon_longitude_deriv(jd)
            ds = self._sun_longitude_deriv(jd)
            deriv = dm - ds
            if abs(deriv) < 1e-12:
                break
            jd -= diff / deriv
        return jd

    # ---------- New moon & full moon pertama dalam tahun ----------
    def find_first_new_moon_after(self, jd_tt_start):
        """Cari new moon pertama pada atau setelah JD TT tertentu."""
        jd = self.find_new_moon(jd_tt_start)
        if jd < jd_tt_start - 1e-6:
            jd += self.synodic_month
            jd = self.find_new_moon(jd)
        return jd

    def find_first_full_moon_after(self, jd_tt_start):
        """Cari full moon pertama pada atau setelah JD TT tertentu."""
        jd = self.find_full_moon(jd_tt_start)
        if jd < jd_tt_start - 1e-6:
            jd += self.synodic_month
            jd = self.find_full_moon(jd)
        return jd

    # ---------- Semua fase dalam satu tahun ----------
    def get_all_lunar_phases_in_year(self, year):
        """
        Mengembalikan daftar semua new moon dan full moon dalam tahun tertentu.
        Output: list of (jd_tt, type) dengan type 'New' atau 'Full'.
        """
        # Tentukan rentang JD untuk tahun tersebut (1 Jan 00:00 UTC s/d 1 Jan tahun berikutnya)
        jd_utc_start = self.time_sys.date_to_jd_utc(year, 1, 1, 0, 0, 0)
        jd_tt_start = self.time_sys.jd_utc_to_tt_extended(jd_utc_start)
        jd_utc_end = self.time_sys.date_to_jd_utc(year + 1, 1, 1, 0, 0, 0)
        jd_tt_end = self.time_sys.jd_utc_to_tt_extended(jd_utc_end)

        phases = []

        # New moons
        jd_new = self.find_first_new_moon_after(jd_tt_start)
        while jd_new < jd_tt_end:
            phases.append((jd_new, 'New'))
            jd_new += self.synodic_month
            jd_new = self.find_new_moon(jd_new)

        # Full moons
        jd_full = self.find_first_full_moon_after(jd_tt_start)
        while jd_full < jd_tt_end:
            phases.append((jd_full, 'Full'))
            jd_full += self.synodic_month
            jd_full = self.find_full_moon(jd_full)

        # Urutkan berdasarkan waktu
        phases.sort(key=lambda x: x[0])
        return phases

    # ---------- Perigee & Apogee pertama dalam tahun ----------
    def find_first_perigee(self, year):
        """Cari perigee pertama dalam tahun tertentu (jarak minimum)."""
        jd_utc_jan1 = self.time_sys.date_to_jd_utc(year, 1, 1, 12, 0, 0)
        jd_tt_jan1 = self.time_sys.jd_utc_to_tt_extended(jd_utc_jan1)
        best_jd = jd_tt_jan1
        best_r = self._moon_distance(best_jd)
        # scanning 60 hari ke depan (karena perigee terjadi setiap ~27.5 hari)
        for offset in range(0, 60):
            jd_test = jd_tt_jan1 + offset
            r_test = self._moon_distance(jd_test)
            if r_test < best_r:
                best_r = r_test
                best_jd = jd_test
        # Newton-Raphson untuk memperhalus
        jd_tt_guess = best_jd
        for _ in range(10):
            drdt = self._moon_distance_deriv(jd_tt_guess)
            if abs(drdt) < 1e-8:
                break
            drdt_plus = self._moon_distance_deriv(jd_tt_guess + 0.1)
            drdt_minus = self._moon_distance_deriv(jd_tt_guess - 0.1)
            d2rdt2 = (drdt_plus - drdt_minus) / 0.2
            if abs(d2rdt2) < 1e-12:
                break
            jd_tt_guess -= drdt / d2rdt2
        return jd_tt_guess

    def find_first_apogee(self, year):
        """Cari apogee pertama dalam tahun tertentu (jarak maksimum)."""
        jd_utc_jan1 = self.time_sys.date_to_jd_utc(year, 1, 1, 12, 0, 0)
        jd_tt_jan1 = self.time_sys.jd_utc_to_tt_extended(jd_utc_jan1)
        best_jd = jd_tt_jan1
        best_r = self._moon_distance(best_jd)
        for offset in range(0, 60):
            jd_test = jd_tt_jan1 + offset
            r_test = self._moon_distance(jd_test)
            if r_test > best_r:
                best_r = r_test
                best_jd = jd_test
        jd_tt_guess = best_jd
        for _ in range(10):
            drdt = self._moon_distance_deriv(jd_tt_guess)
            if abs(drdt) < 1e-8:
                break
            drdt_plus = self._moon_distance_deriv(jd_tt_guess + 0.1)
            drdt_minus = self._moon_distance_deriv(jd_tt_guess - 0.1)
            d2rdt2 = (drdt_plus - drdt_minus) / 0.2
            if abs(d2rdt2) < 1e-12:
                break
            jd_tt_guess -= drdt / d2rdt2
        return jd_tt_guess

    # ---------- Perigee & Apogee terdekat dari suatu tanggal ----------
    def find_nearest_perigee(self, jd_tt_center):
        """Cari perigee terdekat dengan suatu waktu (minimum lokal)."""
        best_jd = jd_tt_center
        best_r = self._moon_distance(best_jd)
        for offset in range(-20, 21):
            jd_test = jd_tt_center + offset
            r_test = self._moon_distance(jd_test)
            if r_test < best_r:
                best_r = r_test
                best_jd = jd_test
        jd_tt_guess = best_jd
        for _ in range(10):
            drdt = self._moon_distance_deriv(jd_tt_guess)
            if abs(drdt) < 1e-8:
                break
            drdt_plus = self._moon_distance_deriv(jd_tt_guess + 0.1)
            drdt_minus = self._moon_distance_deriv(jd_tt_guess - 0.1)
            d2rdt2 = (drdt_plus - drdt_minus) / 0.2
            if abs(d2rdt2) < 1e-12:
                break
            jd_tt_guess -= drdt / d2rdt2
        return jd_tt_guess

    def find_nearest_apogee(self, jd_tt_center):
        """Cari apogee terdekat dengan suatu waktu (maksimum lokal)."""
        best_jd = jd_tt_center
        best_r = self._moon_distance(best_jd)
        for offset in range(-20, 21):
            jd_test = jd_tt_center + offset
            r_test = self._moon_distance(jd_test)
            if r_test > best_r:
                best_r = r_test
                best_jd = jd_test
        jd_tt_guess = best_jd
        for _ in range(10):
            drdt = self._moon_distance_deriv(jd_tt_guess)
            if abs(drdt) < 1e-8:
                break
            drdt_plus = self._moon_distance_deriv(jd_tt_guess + 0.1)
            drdt_minus = self._moon_distance_deriv(jd_tt_guess - 0.1)
            d2rdt2 = (drdt_plus - drdt_minus) / 0.2
            if abs(d2rdt2) < 1e-12:
                break
            jd_tt_guess -= drdt / d2rdt2
        return jd_tt_guess

    # ---------- Lunar standstill ----------
    def find_major_standstill(self, jd_tt_guess):
        """Cari major standstill terdekat (maksimum deklinasi)."""
        # scanning lokal untuk mendapatkan tebakan yang baik
        best_jd = jd_tt_guess
        best_dec = self._moon_declination(best_jd)
        for offset in range(-20, 21):
            jd_test = jd_tt_guess + offset
            dec = self._moon_declination(jd_test)
            if dec > best_dec:
                best_dec = dec
                best_jd = jd_test
        jd_tt_guess = best_jd
        for _ in range(10):
            ddec_dt = self._moon_declination_deriv(jd_tt_guess)
            if abs(ddec_dt) < 1e-8:
                break
            ddec_plus = self._moon_declination_deriv(jd_tt_guess + 0.1)
            ddec_minus = self._moon_declination_deriv(jd_tt_guess - 0.1)
            d2dec_dt2 = (ddec_plus - ddec_minus) / 0.2
            if abs(d2dec_dt2) < 1e-12:
                break
            jd_tt_guess -= ddec_dt / d2dec_dt2
        return jd_tt_guess

    def find_minor_standstill(self, jd_tt_guess):
        """Cari minor standstill terdekat (minimum deklinasi)."""
        best_jd = jd_tt_guess
        best_dec = self._moon_declination(best_jd)
        for offset in range(-20, 21):
            jd_test = jd_tt_guess + offset
            dec = self._moon_declination(jd_test)
            if dec < best_dec:
                best_dec = dec
                best_jd = jd_test
        jd_tt_guess = best_jd
        for _ in range(10):
            ddec_dt = self._moon_declination_deriv(jd_tt_guess)
            if abs(ddec_dt) < 1e-8:
                break
            ddec_plus = self._moon_declination_deriv(jd_tt_guess + 0.1)
            ddec_minus = self._moon_declination_deriv(jd_tt_guess - 0.1)
            d2dec_dt2 = (ddec_plus - ddec_minus) / 0.2
            if abs(d2dec_dt2) < 1e-12:
                break
            jd_tt_guess -= ddec_dt / d2dec_dt2
        return jd_tt_guess

    # ---------- Standstill pertama dalam tahun ----------
    def find_first_major_standstill(self, year):
        jd_utc_jan1 = self.time_sys.date_to_jd_utc(year, 1, 1, 12, 0, 0)
        jd_tt_jan1 = self.time_sys.jd_utc_to_tt_extended(jd_utc_jan1)
        best_jd = jd_tt_jan1
        best_dec = self._moon_declination(best_jd)
        for offset in range(0, 60):
            jd_test = jd_tt_jan1 + offset
            dec = self._moon_declination(jd_test)
            if dec > best_dec:
                best_dec = dec
                best_jd = jd_test
        return self.find_major_standstill(best_jd)

    def find_first_minor_standstill(self, year):
        jd_utc_jan1 = self.time_sys.date_to_jd_utc(year, 1, 1, 12, 0, 0)
        jd_tt_jan1 = self.time_sys.jd_utc_to_tt_extended(jd_utc_jan1)
        best_jd = jd_tt_jan1
        best_dec = self._moon_declination(best_jd)
        for offset in range(0, 60):
            jd_test = jd_tt_jan1 + offset
            dec = self._moon_declination(jd_test)
            if dec < best_dec:
                best_dec = dec
                best_jd = jd_test
        return self.find_minor_standstill(best_jd)


# ============================================================================
# ECLIPSE CALCULATOR – Versi Lengkap dan Akurat
# ============================================================================

class EclipseCalculator:
    def __init__(self, solar_engine=None, lunar_engine=None, time_sys=None):
        self.solar = solar_engine if solar_engine else SolarEvents()
        self.lunar = lunar_engine if lunar_engine else LunarEvents()
        self.time_sys = time_sys if time_sys else TimeSystem()
        self.const = IAU2023UltraPrecision()
        self.ATMOSPHERIC_ENLARGEMENT = 1.02         

        # Batas lintang Bulan untuk kemungkinan gerhana (derajat)
        self.MAX_LAT_FOR_LUNAR_ECLIPSE = 1.5
        self.MAX_LAT_FOR_SOLAR_ECLIPSE = 1.5

        # Konstanta fisik
        self.SUN_RADIUS_KM = self.const.SUN_RADIUS / 1000.0
        self.MOON_RADIUS_KM = self.const.MOON_RADIUS / 1000.0
        self.EARTH_RADIUS_KM = self.const.EARTH_EQUATORIAL_RADIUS / 1000.0

        # Muat data Saros
        self._lunar_saros_data = self._load_lunar_saros_data()
        self._solar_saros_data = self._load_solar_saros_data()

    # ------------------------------------------------------------------------
    # Fungsi bantu posisi (dari ephemeris)
    # ------------------------------------------------------------------------
    def _sun_geocentric(self, jd_tt):
        """Mengembalikan (bujur, lintang, jarak_au) Matahari geosentrik apparent."""
        data = self.solar.sun_engine.calculate_sun_position_vsop87d(jd_tt, 'ecliptic_apparent')
        return data['longitude_deg'], data['latitude_deg'], data['radius_au']

    def _moon_geocentric(self, jd_tt):
        """Mengembalikan (bujur, lintang, jarak_km, jarak_au) Bulan geosentrik apparent."""
        data = self.lunar.lunar_engine.calculate_position(jd_tt, output_frame='ecliptic_apparent')
        lon = data['ecliptic_apparent']['longitude_deg']
        lat = data['ecliptic_apparent']['latitude_deg']
        dist_km = data['distance_km']
        dist_au = data['distance_au']
        return lon, lat, dist_km, dist_au

    # ------------------------------------------------------------------------
    # Pencarian puncak gerhana dengan presisi tinggi
    # ------------------------------------------------------------------------
    def _find_peak(self, jd_approx):
        """
        Mencari puncak gerhana dengan interpolasi parabola dilanjutkan iterasi Newton.
        Mengembalikan (jd_peak, mag_umbra, mag_penumbra, eclipse_type)
        """
        # Fungsi jarak sudut ke titik anti-matahari
        def dist_to_shadow(jd):
            slon, slat, _ = self._sun_geocentric(jd)
            mlon, mlat, _, _ = self._moon_geocentric(jd)
            shadow_lon = (slon + 180.0) % 360.0
            shadow_lat = -slat
            d_lon = math.radians(mlon - shadow_lon)
            mlat_rad = math.radians(mlat)
            slat_rad = math.radians(shadow_lat)
            cos_d = math.sin(mlat_rad) * math.sin(slat_rad) + \
                    math.cos(mlat_rad) * math.cos(slat_rad) * math.cos(d_lon)
            cos_d = max(-1.0, min(1.0, cos_d))
            return math.degrees(math.acos(cos_d))

        # Ambil tiga titik sekitar jd_approx dengan step 10 menit
        step = 10 / (24 * 60)  # 10 menit dalam hari
        jd1 = jd_approx - step
        jd2 = jd_approx
        jd3 = jd_approx + step

        d1 = dist_to_shadow(jd1)
        d2 = dist_to_shadow(jd2)
        d3 = dist_to_shadow(jd3)

        # Interpolasi parabola untuk mencari minimum
        if d2 <= d1 and d2 <= d3:
            jd_peak = jd2
        else:
            x1, x2, x3 = jd1, jd2, jd3
            y1, y2, y3 = d1, d2, d3
            # Hitung koefisien parabola y = a(x-x2)^2 + b(x-x2) + c
            a = ((y1 - y2) * (x2 - x3) - (y3 - y2) * (x1 - x2)) / ((x1 - x2) * (x2 - x3) * (x1 - x3))
            b = (y1 - y2) / (x1 - x2) - a * (x1 + x2 - 2*x2)
            if a != 0:
                jd_peak = x2 - b / (2 * a)
            else:
                jd_peak = x2

        # Iterasi Newton untuk mempertajam posisi minimum
        for _ in range(5):
            d0 = dist_to_shadow(jd_peak)
            h = 1e-6  # langkah ~0.086 detik
            d_plus = dist_to_shadow(jd_peak + h)
            d_minus = dist_to_shadow(jd_peak - h)
            deriv = (d_plus - d_minus) / (2 * h)
            if abs(deriv) < 1e-10:
                break
            deriv2 = (d_plus - 2*d0 + d_minus) / (h**2)
            if abs(deriv2) < 1e-12:
                break
            jd_peak -= deriv / deriv2

        # Hitung magnitudo puncak
        sun_lon, _, dist_sun_au = self._sun_geocentric(jd_peak)
        moon_lon, moon_lat, dist_moon_km, _ = self._moon_geocentric(jd_peak)
        dist_sun_km = dist_sun_au * self.const.AU_TO_KM

        pi_moon = math.asin(self.EARTH_RADIUS_KM / dist_moon_km)
        pi_sun  = math.asin(self.EARTH_RADIUS_KM / dist_sun_km)
        s_moon  = math.asin(self.MOON_RADIUS_KM / dist_moon_km)
        s_sun   = math.asin(self.SUN_RADIUS_KM / dist_sun_km)

        r_umbra_rad = self.ATMOSPHERIC_ENLARGEMENT * (pi_moon + pi_sun - s_sun)
        r_penumbra_rad = self.ATMOSPHERIC_ENLARGEMENT * (pi_moon + pi_sun + s_sun)

        lat_rad = math.radians(moon_lat)
        d = abs(lat_rad)

        if d < r_umbra_rad:
            mag_umbra = (r_umbra_rad + s_moon - d) / (2 * s_moon)
        else:
            mag_umbra = 0.0

        if d < r_penumbra_rad:
            mag_penumbra = (r_penumbra_rad + s_moon - d) / (2 * s_moon)
        else:
            mag_penumbra = 0.0

        if mag_umbra >= 1.0:
            etype = 'total'
        elif mag_umbra > 0.0:
            etype = 'partial'
        elif mag_penumbra > 0.0:
            etype = 'penumbral'
        else:
            etype = 'none'

        return jd_peak, mag_umbra, mag_penumbra, etype

    # ------------------------------------------------------------------------
    # Pencarian kontak dengan biseksi (dibatasi ±4 jam)
    # ------------------------------------------------------------------------
    def _lunar_contact_times(self, jd_peak, moon_lat_peak, dist_moon_km, dist_sun_km):
        # Hitung parameter radius dalam derajat dengan presisi
        pi_moon = math.degrees(math.asin(self.EARTH_RADIUS_KM / dist_moon_km))
        pi_sun  = math.degrees(math.asin(self.EARTH_RADIUS_KM / dist_sun_km))
        s_moon  = math.degrees(math.asin(self.MOON_RADIUS_KM / dist_moon_km))
        s_sun   = math.degrees(math.asin(self.SUN_RADIUS_KM / dist_sun_km))

        r_umbra = self.ATMOSPHERIC_ENLARGEMENT * (pi_moon + pi_sun - s_sun)
        r_penumbra = self.ATMOSPHERIC_ENLARGEMENT * (pi_moon + pi_sun + s_sun)

        # Target jarak sudut presisi (pusat Bulan ke pusat bayangan Bumi)
        target_penumbra = r_penumbra + s_moon
        target_umbra = r_umbra + s_moon
        target_total = r_umbra - s_moon

        # Kalkulasi jarak sudut absolut menggunakan Spherical Law of Cosines
        def dist_to_shadow(jd):
            slon, slat, _ = self._sun_geocentric(jd)
            mlon, mlat, _, _ = self._moon_geocentric(jd)
            
            # Anti-solar point (Pusat bayangan Bumi)
            shadow_lon = (slon + 180.0) % 360.0
            shadow_lat = -slat
            
            d_lon = math.radians(mlon - shadow_lon)
            mlat_rad = math.radians(mlat)
            slat_rad = math.radians(shadow_lat)
            
            # Hukum Kosinus Bola untuk presisi tinggi di koordinat sferis
            cos_d = math.sin(mlat_rad) * math.sin(slat_rad) + \
                    math.cos(mlat_rad) * math.cos(slat_rad) * math.cos(d_lon)
            cos_d = max(-1.0, min(1.0, cos_d)) # Hindari error floating point out-of-bounds
            return math.degrees(math.acos(cos_d))

        # Fungsi pencarian waktu menggunakan Bisection Method untuk presisi sub-detik
        def cari_waktu(target, arah, jam_max=6):
            step = 1 / (24 * 60)  # Lompatan awal 1 menit
            jd = jd_peak
            dist_prev = dist_to_shadow(jd)
            
            for _ in range(int(jam_max * 60)):
                jd += arah * step
                dist_curr = dist_to_shadow(jd)
                
                # Jika melewati batas target, gunakan Bisection untuk mencari titik presisi
                if dist_curr >= target and dist_prev < target:
                    jd_low = jd - arah * step if arah > 0 else jd
                    jd_high = jd if arah > 0 else jd - arah * step
                    
                    # 10 Iterasi bisection memberikan presisi waktu kurang dari 0.1 detik
                    for _ in range(10):
                        jd_mid = (jd_low + jd_high) / 2
                        if dist_to_shadow(jd_mid) < target:
                            if arah > 0: jd_low = jd_mid
                            else: jd_high = jd_mid
                        else:
                            if arah > 0: jd_high = jd_mid
                            else: jd_low = jd_mid
                            
                    return (jd_low + jd_high) / 2
                
                dist_prev = dist_curr
            return None

        peak_dist = dist_to_shadow(jd_peak)

        # Inisialisasi variabel kontak
        P1 = P4 = U1 = U4 = U2 = U3 = None
        
        # Eksekusi pencarian waktu kontak
        if peak_dist < target_penumbra:
            P1 = cari_waktu(target_penumbra, -1, 6)
            P4 = cari_waktu(target_penumbra, +1, 6)

        if peak_dist < target_umbra:
            U1 = cari_waktu(target_umbra, -1, 4)
            U4 = cari_waktu(target_umbra, +1, 4)
            
        if target_total > 0 and peak_dist < target_total:
            U2 = cari_waktu(target_total, -1, 3)
            U3 = cari_waktu(target_total, +1, 3)

        return {
            'P1': P1, 'U1': U1, 'U2': U2, 'U3': U3, 'U4': U4, 'P4': P4,
            'duration_penumbral_hours': (P4 - P1) * 24 if P1 and P4 else 0.0,
            'duration_umbral_hours': (U4 - U1) * 24 if U1 and U4 else 0.0,
            'duration_total_hours': (U3 - U2) * 24 if U2 and U3 else 0.0,
        }

    def _sun_altitude(self, jd_tt, lat, lon):
        """Hitung altitude Matahari di lokasi tertentu (derajat)."""
        # Dapatkan koordinat ekuatorial Matahari
        sun_lon, sun_lat, dist_au = self._sun_geocentric(jd_tt)
        eps = self._calc_true_obliquity(jd_tt)
        ra_sun, dec_sun = self._ecliptic_to_equatorial(sun_lon, sun_lat, eps)
        # Konversi ke waktu UTC
        year = self.time_sys.jd_to_gregorian(jd_tt)['year_astronomical']
        delta_t = self.time_sys.delta_t_espenak_extended(year)
        jd_utc = jd_tt - (delta_t + self.const.TT_TAI) / 86400.0
        # Hitung altitude
        from JRC_Ephemeris import UnifiedCoordinateTransformer
        trans = UnifiedCoordinateTransformer()
        altaz = trans.equatorial_to_altaz(ra_sun, dec_sun, jd_utc, lat, lon)
        return altaz['altitude_apparent']

    # ------------------------------------------------------------------------
    # Gerhana Bulan – utama
    # ------------------------------------------------------------------------
    def find_lunar_eclipses(self, year):
        """
        Mengembalikan daftar gerhana Bulan dalam tahun tertentu.
        Setiap elemen adalah dict dengan kunci:
            jd_tt, datetime_wib, eclipse_type, magnitude_umbra,
            magnitude_penumbra, lunar_latitude_deg, distance_moon_km
        """
        eclipses = []
        jd_start_utc = self.time_sys.date_to_jd_utc(year, 1, 1, 0, 0, 0)
        jd_tt_start = self.time_sys.jd_utc_to_tt_extended(jd_start_utc)
        jd_end_utc = self.time_sys.date_to_jd_utc(year + 1, 1, 1, 0, 0, 0)
        jd_tt_end = self.time_sys.jd_utc_to_tt_extended(jd_end_utc)

        step = 1.0
        jd = jd_tt_start
        prev_diff = None

        while jd < jd_tt_end:
            sun_lon, _, _ = self._sun_geocentric(jd)
            moon_lon, _, _, _ = self._moon_geocentric(jd)
            diff = (moon_lon - sun_lon) % 360

            if prev_diff is not None:
                if prev_diff < 180 and diff >= 180:
                    fraction = (180 - prev_diff) / (diff - prev_diff) if diff != prev_diff else 0.5
                    jd_approx = jd - step + fraction * step

                    jd_peak, mag_u, mag_p, etype = self._find_peak(jd_approx)
                    if etype != 'none':
                        # Cegah duplikasi
                        if eclipses and abs(jd_peak - eclipses[-1]['jd_tt']) < 10:
                            continue

                        # Ambil data lintang dan jarak
                        _, moon_lat, dist_moon_km, _ = self._moon_geocentric(jd_peak)

                        # Konversi waktu ke WIB
                        delta_t = self.time_sys.delta_t_espenak_extended(year)
                        jd_utc = jd_peak - (delta_t + self.const.TT_TAI) / 86400.0
                        jd_wib = jd_utc + 7/24
                        dt = self.time_sys.jd_to_gregorian(jd_wib)
                        wib_str = f"{dt['year_astronomical']:04d}-{dt['month']:02d}-{dt['day']:02d} {dt['hour']:02d}:{dt['minute']:02d}:{dt['second']:02d}"

                        eclipses.append({
                            'jd_tt': jd_peak,
                            'datetime_wib': wib_str,
                            'eclipse_type': etype,
                            'magnitude_umbra': round(mag_u, 3),
                            'magnitude_penumbra': round(mag_p, 3),
                            'lunar_latitude_deg': round(moon_lat, 4),
                            'distance_moon_km': round(dist_moon_km, 1)
                        })

            prev_diff = diff
            jd += step

        return eclipses

    # ------------------------------------------------------------------------
    # Gerhana Matahari (dari kode lama, tidak diubah)
    # ------------------------------------------------------------------------
    def find_solar_eclipses(self, year):
        """
        Mengembalikan daftar gerhana Matahari dalam tahun tertentu.
        Setiap elemen adalah dict dengan kunci:
            jd_tt, datetime_wib, eclipse_type, magnitude_geocentric,
            lunar_latitude_deg, distance_moon_km, distance_sun_km,
            sun_angular_radius_arcmin, moon_angular_radius_arcmin,
            max_duration_seconds
        """
        # Kecepatan sudut relatif Bulan terhadap Matahari (rad/detik)
        # 0.5 detik busur per detik = 0.5 / 206264.806 rad/detik
        v_rel_rad = 0.5 / 206264.806

        eclipses = []
        jd_start_utc = self.time_sys.date_to_jd_utc(year, 1, 1, 0, 0, 0)
        jd_tt_start = self.time_sys.jd_utc_to_tt_extended(jd_start_utc)
        jd_end_utc = self.time_sys.date_to_jd_utc(year + 1, 1, 1, 0, 0, 0)
        jd_tt_end = self.time_sys.jd_utc_to_tt_extended(jd_end_utc)

        step = 1.0
        jd = jd_tt_start
        prev_diff = None

        while jd < jd_tt_end:
            sun_lon, _, _ = self._sun_geocentric(jd)
            moon_lon, _, _, _ = self._moon_geocentric(jd)
            diff = (moon_lon - sun_lon) % 360

            if prev_diff is not None:
                # Deteksi bulan baru (transisi melewati 0°)
                if prev_diff > 350 and diff < 10:
                    fraction = (360 - prev_diff) / ((360 - prev_diff) + diff)
                    jd_exact = jd - step + fraction * step

                    # Cek lintang
                    _, moon_lat, dist_moon_km, _ = self._moon_geocentric(jd_exact)
                    if abs(moon_lat) <= self.MAX_LAT_FOR_SOLAR_ECLIPSE:
                        # Hitung parameter gerhana
                        sun_lon_exact, _, dist_sun_au = self._sun_geocentric(jd_exact)
                        dist_sun_km = dist_sun_au * self.const.AU_TO_KM

                        s_sun = math.asin(self.SUN_RADIUS_KM / dist_sun_km)
                        s_moon = math.asin(self.MOON_RADIUS_KM / dist_moon_km)
                        pi_moon = math.asin(self.EARTH_RADIUS_KM / dist_moon_km)
                        pi_sun = math.asin(self.EARTH_RADIUS_KM / dist_sun_km)

                        r_umbra_rad = pi_moon + pi_sun - s_sun
                        r_antumbra_rad = pi_moon + pi_sun + s_sun
                        r_penumbra_rad = pi_moon + pi_sun + s_sun

                        lat_rad = math.radians(moon_lat)

                        # Inisialisasi
                        mag = 0.0
                        etype = 'none'
                        duration = 0.0

                        if abs(lat_rad) < r_umbra_rad:
                            mag = (r_umbra_rad - abs(lat_rad)) / (2 * s_sun)
                            if r_umbra_rad > s_moon:
                                etype = 'total'
                                # Diameter sudut Bulan - Matahari
                                delta_rad = 2 * (s_moon - s_sun)
                            else:
                                etype = 'annular'
                                delta_rad = 2 * (s_sun - s_moon)
                            duration = delta_rad / v_rel_rad
                        elif abs(lat_rad) < r_antumbra_rad:
                            mag = (r_antumbra_rad - abs(lat_rad)) / (2 * s_sun)
                            etype = 'annular'
                            delta_rad = 2 * (s_sun - s_moon)
                            duration = delta_rad / v_rel_rad
                        elif abs(lat_rad) < r_penumbra_rad:
                            mag = (r_penumbra_rad - abs(lat_rad)) / (2 * s_sun)
                            etype = 'partial'
                            duration = 0.0
                        else:
                            continue

                        # Deteksi hybrid (hampir sama ukuran)
                        if abs(r_umbra_rad - s_moon) < 0.0001 and abs(lat_rad) < r_umbra_rad:
                            etype = 'hybrid'
                            delta_rad = 2 * abs(s_sun - s_moon)
                            duration = delta_rad / v_rel_rad

                        # Cegah duplikasi
                        if eclipses and abs(jd_exact - eclipses[-1]['jd_tt']) < 10:
                            continue

                        # Diameter sudut dalam menit busur
                        sun_angular_radius_arcmin = math.degrees(s_sun) * 60
                        moon_angular_radius_arcmin = math.degrees(s_moon) * 60

                        # Konversi waktu
                        delta_t = self.time_sys.delta_t_espenak_extended(year)
                        jd_utc = jd_exact - (delta_t + self.const.TT_TAI) / 86400.0
                        jd_wib = jd_utc + 7/24
                        dt = self.time_sys.jd_to_gregorian(jd_wib)
                        wib_str = f"{dt['year_astronomical']:04d}-{dt['month']:02d}-{dt['day']:02d} {dt['hour']:02d}:{dt['minute']:02d}:{dt['second']:02d}"

                        eclipses.append({
                            'jd_tt': jd_exact,
                            'datetime_wib': wib_str,
                            'eclipse_type': etype,
                            'magnitude_geocentric': round(mag, 3),
                            'lunar_latitude_deg': round(moon_lat, 4),
                            'distance_moon_km': round(dist_moon_km, 1),
                            'distance_sun_km': round(dist_sun_km, 1),
                            'sun_angular_radius_arcmin': round(sun_angular_radius_arcmin, 2),
                            'moon_angular_radius_arcmin': round(moon_angular_radius_arcmin, 2),
                            'max_duration_seconds': round(duration, 1)
                        })

            prev_diff = diff
            jd += step

        return eclipses

    # ------------------------------------------------------------------------
    # Nomor Saros (gerhana bulan dan matahari)
    # ------------------------------------------------------------------------
    def _parse_nasa_date(self, date_str):
        """
        Mengonversi string tanggal dari tabel NASA (contoh: "-2570 Mar 14") ke JD TT.
        Mengembalikan JD TT (float).
        """
        parts = date_str.split()
        if len(parts) != 3:
            raise ValueError(f"Format tanggal tidak dikenal: {date_str}")
        year_str, month_str, day_str = parts
        year = int(year_str)
        month = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6,
                 "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}[month_str[:3]]
        day = int(day_str)
        # Konversi ke JD UTC (asumsikan tengah hari UTC, karena waktu tidak disebut)
        jd_utc = self.time_sys.date_to_jd_utc(year, month, day, 12, 0, 0)
        # Konversi ke JD TT (ΔT menggunakan Espenak, cukup untuk rentang)
        jd_tt = self.time_sys.jd_utc_to_tt_extended(jd_utc)
        return jd_tt

    def _load_lunar_saros_data(self):
        """Memuat data Saros Bulan dari tabel NASA dan mengonversi ke JD TT."""
        # Data dari method get_saros_number() yang sudah ada
        raw_data = [
            (1, "-2570 Mar 14", "-1272 Apr 30"),
            (2, "-2523 Mar 03", "-1225 Apr 22"),
            (3, "-2567 Dec 30", "-1214 Mar 21"),
            (4, "-2646 Oct 06", "-1131 Apr 02"),
            (5, "-2455 Dec 22", "-1084 Mar 24"),
            (6, "-2624 Aug 04", "-1091 Feb 10"),
            (7, "-2595 Jul 16", "-1008 Feb 22"),
            (8, "-2494 Aug 08", "-0961 Feb 13"),
            (9, "-2501 Jun 26", "-1167 Sep 05"),
            (10, "-2454 Jun 17", "-1138 Aug 15"),
            (11, "-2371 Jun 29", "-1055 Aug 27"),
            (12, "-2360 May 28", "-1062 Jul 17"),
            (13, "-2313 May 20", "-1015 Jul 06"),
            (14, "-2230 Jun 01", "-0932 Jul 19"),
            (15, "-2219 Apr 30", "-0921 Jun 19"),
            (16, "-2172 Apr 21", "-0874 Jun 08"),
            (17, "-2089 May 04", "-0809 Jun 11"),
            (18, "-2078 Apr 02", "-0780 May 21"),
            (19, "-2031 Mar 24", "-0733 May 11"),
            (20, "-1948 Apr 05", "-0668 May 12"),
            (21, "-1955 Feb 22", "-0639 Apr 23"),
            (22, "-1926 Feb 02", "-0610 Apr 02"),
            (23, "-1825 Feb 25", "-0527 Apr 14"),
            (24, "-2031 Sep 16", "-0516 Mar 14"),
            (25, "-2038 Aug 06", "-0487 Feb 21"),
            (26, "-1919 Sep 09", "-0404 Mar 06"),
            (27, "-1926 Jul 28", "-0411 Jan 23"),
            (28, "-1897 Jul 09", "-0581 Sep 06"),
            (29, "-1814 Jul 21", "-0336 Dec 24"),
            (30, "-1803 Jun 19", "-0487 Aug 18"),
            (31, "-1774 May 30", "-0476 Jul 17"),
            (32, "-1673 Jun 23", "-0375 Aug 09"),
            (33, "-1662 May 22", "-0364 Jul 10"),
            (34, "-1615 May 13", "-0335 Jun 19"),
            (35, "-1532 May 25", "-0252 Jul 01"),
            (36, "-1521 Apr 24", "-0223 Jun 11"),
            (37, "-1492 Apr 03", "-0212 May 10"),
            (38, "-1391 Apr 27", "-0111 Jun 03"),
            (39, "-1380 Mar 26", "-0082 May 14"),
            (40, "-1369 Feb 24", "-0071 Apr 12"),
            (41, "-1268 Mar 18", "0030 May 06"),
            (42, "-1275 Feb 04", "0041 Apr 05"),
            (43, "-1463 Sep 07", "0052 Mar 04"),
            (44, "-1199 Jan 06", "0153 Mar 27"),
            (45, "-1351 Aug 29", "0164 Feb 25"),
            (46, "-1358 Jul 19", "-0006 Oct 08"),
            (47, "-1275 Jul 31", "0258 Feb 05"),
            (48, "-1228 Jul 21", "0106 Sep 30"),
            (49, "-1217 Jun 21", "0081 Aug 08"),
            (50, "-1134 Jul 03", "0164 Aug 20"),
            (51, "-1105 Jun 13", "0193 Jul 31"),
            (52, "-1076 May 23", "0204 Jun 29"),
            (53, "-0993 Jun 05", "0287 Jul 12"),
            (54, "-0946 May 26", "0334 Jul 03"),
            (55, "-0935 Apr 25", "0345 Jun 01"),
            (56, "-0852 May 07", "0428 Jun 13"),
            (57, "-0823 Apr 16", "0475 Jun 05"),
            (58, "-0812 Mar 16", "0486 May 04"),
            (59, "-0711 Apr 09", "0551 May 06"),
            (60, "-0700 Mar 08", "0598 Apr 27"),
            (61, "-0780 Dec 13", "0609 Mar 26"),
            (62, "-0624 Feb 08", "0692 Apr 06"),
            (63, "-0722 Nov 03", "0739 Mar 29"),
            (64, "-0783 Aug 20", "0714 Feb 04"),
            (65, "-0736 Aug 11", "0797 Feb 16"),
            (66, "-0671 Aug 12", "0826 Jan 27"),
            (67, "-0660 Jul 11", "0638 Aug 30"),
            (68, "-0595 Jul 14", "0685 Aug 20"),
            (69, "-0530 Jul 15", "0768 Sep 01"),
            (70, "-0519 Jun 13", "0761 Jul 21"),
            (71, "-0472 Jun 04", "0808 Jul 11"),
            (72, "-0389 Jun 17", "0891 Jul 25"),
            (73, "-0378 May 16", "0902 Jun 23"),
            (74, "-0331 May 07", "0949 Jun 13"),
            (75, "-0266 May 08", "1014 Jun 15"),
            (76, "-0255 Apr 07", "1043 May 26"),
            (77, "-0190 Apr 09", "1090 May 16"),
            (78, "-0125 Apr 10", "1155 May 18"),
            (79, "-0132 Feb 27", "1166 Apr 17"),
            (80, "-0103 Feb 07", "1213 Apr 06"),
            (81, "-0020 Feb 19", "1296 Apr 19"),
            (82, "-0208 Sep 21", "1289 Mar 08"),
            (83, "-0197 Aug 22", "1300 Feb 05"),
            (84, "-0096 Sep 13", "1401 Feb 28"),
            (85, "-0103 Aug 02", "1249 Oct 23"),
            (86, "-0074 Jul 13", "1224 Aug 30"),
            (87, "0027 Aug 06", "1325 Sep 23"),
            (88, "0038 Jul 05", "1318 Aug 12"),
            (89, "0067 Jun 15", "1347 Jul 23"),
            (90, "0150 Jun 27", "1430 Aug 04"),
            (91, "0179 Jun 07", "1459 Jul 15"),
            (92, "0208 May 17", "1470 Jun 13"),
            (93, "0291 May 30", "1553 Jun 25"),
            (94, "0320 May 09", "1582 Jun 06"),
            (95, "0349 Apr 19", "1611 May 26"),
            (96, "0432 May 01", "1694 Jun 07"),
            (97, "0443 Mar 31", "1723 May 20"),
            (98, "0436 Feb 18", "1752 Apr 28"),
            (99, "0555 Mar 24", "1835 May 12"),
            (100, "0439 Dec 06", "1846 Apr 11"),
            (101, "0360 Sep 11", "1839 Feb 28"),
            (102, "0461 Oct 05", "1958 Apr 04"),
            (103, "0472 Sep 03", "1933 Feb 10"),
            (104, "0483 Aug 04", "1763 Sep 22"),
            (105, "0566 Aug 16", "1864 Oct 15"),
            (106, "0595 Jul 27", "1893 Sep 25"),
            (107, "0606 Jun 26", "1886 Aug 14"),
            (108, "0689 Jul 08", "1969 Aug 27"),
            (109, "0736 Jun 27", "1998 Aug 08"),
            (110, "0747 May 28", "2027 Jul 18"),
            (111, "0830 Jun 10", "2092 Jul 19"),
            (112, "0859 May 20", "2139 Jul 12"),
            (113, "0888 Apr 29", "2150 Jun 10"),
            (114, "0971 May 13", "2233 Jun 22"),
            (115, "1000 Apr 21", "2280 Jun 13"),
            (116, "0993 Mar 11", "2291 May 14"),
            (117, "1094 Apr 03", "2356 May 15"),
            (118, "1105 Mar 02", "2403 May 07"),
            (119, "0935 Oct 14", "2396 Mar 25"),
            (120, "1000 Oct 16", "2479 Apr 07"),
            (121, "1047 Oct 06", "2508 Mar 18"),
            (122, "1022 Aug 14", "2338 Oct 29"),
            (123, "1087 Aug 16", "2367 Oct 08"),
            (124, "1152 Aug 17", "2450 Oct 21"),
            (125, "1163 Jul 17", "2443 Sep 09"),
            (126, "1228 Jul 18", "2472 Aug 19"),
            (127, "1275 Jul 09", "2555 Sep 02"),
            (128, "1304 Jun 18", "2566 Aug 02"),
            (129, "1351 Jun 10", "2613 Jul 24"),
            (130, "1416 Jun 10", "2678 Jul 26"),
            (131, "1427 May 10", "2707 Jul 07"),
            (132, "1492 May 12", "2754 Jun 26"),
            (133, "1557 May 13", "2819 Jun 29"),
            (134, "1550 Apr 01", "2830 May 28"),
            (135, "1615 Apr 13", "2877 May 18"),
            (136, "1680 Apr 13", "2960 Jun 01"),
            (137, "1564 Dec 17", "2953 Apr 20"),
            (138, "1521 Oct 15", "2982 Mar 30"),
            (139, "1658 Dec 09", "3065 Apr 13"),
            (140, "1597 Sep 25", "2968 Jan 06"),
            (141, "1608 Aug 25", "2888 Oct 11"),
            (142, "1709 Sep 19", "3007 Nov 17"),
            (143, "1720 Aug 18", "3000 Oct 05"),
            (144, "1749 Jul 29", "3011 Sep 04"),
            (145, "1832 Aug 11", "3094 Sep 16"),
            (146, "1843 Jul 11", "3123 Aug 29"),
            (147, "1890 Jul 02", "3134 Jul 28"),
            (148, "1973 Jul 15", "3217 Aug 09"),
            (149, "1984 Jun 13", "3246 Jul 20"),
            (150, "2013 May 25", "3275 Jun 30"),
            (151, "2096 Jun 06", "3358 Jul 13"),
            (152, "2107 May 07", "3387 Jun 23"),
            (153, "2136 Apr 16", "3398 May 22"),
            (154, "2237 May 10", "3499 Jun 16"),
            (155, "2212 Mar 18", "3510 May 17"),
            (156, "2060 Nov 08", "3503 Apr 05"),
            (157, "2306 Mar 01", "3604 Apr 27"),
            (158, "2154 Oct 21", "3597 Mar 17"),
            (159, "2147 Sep 09", "3445 Nov 07"),
            (160, "2248 Oct 03", "3528 Nov 19"),
            (161, "2259 Sep 02", "3557 Oct 31"),
            (162, "2288 Aug 12", "3550 Sep 19"),
            (163, "2371 Aug 27", "3615 Sep 20"),
            (164, "2400 Aug 05", "3662 Sep 11"),
            (165, "2411 Jul 06", "3673 Aug 11"),
            (166, "2494 Jul 18", "3738 Aug 13"),
            (167, "2541 Jul 09", "3803 Aug 16"),
            (168, "2552 Jun 08", "3814 Jul 15"),
            (169, "2635 Jun 22", "3879 Jul 17"),
            (170, "2664 Jun 01", "3926 Jul 09"),
            (171, "2675 May 01", "3937 Jun 07"),
            (172, "2758 May 15", "4002 Jun 08"),
            (173, "2787 Apr 24", "4067 Jun 11"),
            (174, "2635 Dec 16", "4042 Apr 18"),
            (175, "2791 Feb 11", "4107 Apr 20"),
            (176, "2747 Dec 09", "4154 Apr 11"),
            (177, "2704 Oct 05", "4002 Dec 03"),
            (178, "2769 Oct 07", "4013 Nov 01"),
            (179, "2816 Sep 27", "4114 Nov 26"),
            (180, "2827 Aug 28", "4089 Oct 03"),
        ]
        result = []
        for saros, first_str, last_str in raw_data:
            try:
                jd_first = self._parse_nasa_date(first_str)
                jd_last = self._parse_nasa_date(last_str)
                result.append((saros, jd_first, jd_last))
            except Exception:
                # Abaikan jika gagal parsing (seharusnya tidak terjadi)
                continue
        return result

    def _load_solar_saros_data(self):
        """Memuat data Saros Matahari dari tabel NASA (0–180) dan mengonversi ke JD TT."""
        # Data diambil langsung dari tabel yang diberikan
        data_text = """
0	72	1280.1	-2955 May 23	-1675 Jun 29	11P 1T 1H 4A 3P 45A 7P
1	72	1280.1	-2872 Jun 04	-1592 Jul 11	9P 39A 5H 12T 7P
2	73	1298.1	-2861 May 04	-1563 Jun 21	8P 43T 12H 3A 7P
3	72	1280.1	-2814 Apr 24	-1534 Jun 01	8P 5T 2H 50A 7P
4	72	1280.1	-2731 May 06	-1451 Jun 13	7P 29A 17H 11T 8P
5	73	1298.1	-2720 Apr 04	-1422 May 24	7P 44T 4H 11A 7P
6	72	1280.1	-2673 Mar 27	-1393 May 03	7P 7T 2H 47A 9P
7	72	1280.1	-2590 Apr 08	-1310 May 16	6P 30A 6H 21T 9P
8	73	1298.1	-2579 Mar 07	-1281 Apr 26	7P 45T 1H 10A 10P
9	74	1316.2	-2568 Feb 06	-1252 Apr 04	9P 8T 3H 32A 22P
10	73	1298.1	-2467 Feb 28	-1169 Apr 18	8P 30A 3H 9T 23P
11	76	1352.2	-2492 Jan 06	-1140 Mar 28	10P 44T 22P
12	86	1532.5	-2662 Aug 20	-1129 Feb 25	23P 8T 3H 30A 22P
13	85	1514.5	-2543 Sep 23	-1028 Mar 19	20P 30A 3H 8T 24P
14	85	1514.5	-2550 Aug 11	-1035 Feb 06	21P 43T 21P
15	75	1334.2	-2557 Jul 01	-1223 Sep 08	24P 10T 3H 29A 9P
16	85	1514.5	-2456 Jul 23	-0941 Jan 18	22P 33A 2H 7T 21P
17	74	1316.2	-2427 Jul 03	-1111 Sep 01	21P 44T 9P
18	73	1298.1	-2416 Jun 02	-1118 Jul 21	22P 13T 3H 28A 7P
19	73	1298.1	-2333 Jun 15	-1035 Aug 01	21P 36A 2H 6T 8P
20	72	1280.1	-2286 Jun 05	-1006 Jul 13	8P 12A 2H 43T 7P
21	72	1280.1	-2275 May 05	-0995 Jun 11	8P 26T 4H 28A 6P
22	71	1262.1	-2174 May 28	-0912 Jun 23	8P 49A 2H 5T 7P
23	72	1280.1	-2145 May 07	-0865 Jun 15	6P 14A 3H 42T 7P
24	72	1280.1	-2134 Apr 06	-0854 May 14	8P 15T 16H 26A 7P
25	71	1262.1	-2033 Apr 30	-0771 May 26	7P 52A 1H 3T 8P
26	72	1280.1	-2004 Apr 08	-0724 May 17	6P 10A 7H 41T 8P
27	72	1280.1	-1993 Mar 09	-0713 Apr 16	8P 14T 15H 20A 15P
28	72	1280.1	-1910 Mar 22	-0630 Apr 28	7P 42A 23P
29	73	1298.1	-1881 Mar 01	-0583 Apr 19	7P 3A 14H 28T 21P
30	83	1478.4	-2051 Oct 12	-0572 Mar 18	19P 14T 5H 24A 21P
31	74	1316.2	-1805 Jan 31	-0489 Mar 31	10P 40A 24P
32	84	1496.5	-1957 Sep 24	-0460 Mar 10	19P 2A 3H 39T 21P
33	84	1496.5	-1982 Aug 02	-0485 Jan 17	23P 15T 4H 23A 19P
34	86	1532.5	-1917 Aug 04	-0384 Feb 09	23P 40A 23P
35	84	1496.5	-1870 Jul 25	-0373 Jan 09	22P 3A 2H 38T 19P
36	73	1298.1	-1859 Jun 23	-0561 Aug 11	22P 18T 3H 23A 7P
37	73	1298.1	-1794 Jun 25	-0496 Aug 12	24P 40A 9P
38	73	1298.1	-1729 Jun 26	-0431 Aug 14	17P 8A 2H 38T 8P
39	72	1280.1	-1718 May 26	-0438 Jul 03	9P 32T 3H 22A 6P
40	72	1280.1	-1653 May 28	-0373 Jul 04	11P 53A 8P
41	72	1280.1	-1588 May 28	-0308 Jul 05	7P 19A 2H 37T 7P
42	72	1280.1	-1577 Apr 28	-0297 Jun 05	8P 34T 3H 21A 6P
43	72	1280.1	-1512 Apr 29	-0232 Jun 05	8P 55A 9P
44	72	1280.1	-1447 Apr 30	-0167 Jun 07	6P 21A 2H 35T 8P
45	72	1280.1	-1436 Mar 30	-0156 May 07	7P 36T 3H 18A 8P
46	72	1280.1	-1371 Apr 01	-0091 May 08	8P 43A 21P
47	72	1280.1	-1306 Apr 02	-0026 May 10	6P 21A 3H 30T 12P
48	74	1316.2	-1331 Feb 08	-0015 Apr 09	9P 37T 2H 6A 20P
49	72	1280.1	-1248 Feb 22	0032 Mar 29	9P 40A 23P
50	73	1298.1	-1201 Feb 11	0097 Apr 01	8P 22A 3H 18T 22P
51	85	1514.5	-1407 Sep 02	0108 Feb 29	21P 36T 4H 3A 21P
52	86	1532.5	-1378 Aug 14	0155 Feb 19	24P 40A 22P
53	84	1496.5	-1277 Sep 06	0220 Feb 21	20P 22A 4H 17T 21P
54	74	1316.2	-1284 Jul 25	0032 Sep 23	21P 26T 15H 3A 9P
55	73	1298.1	-1255 Jul 06	0043 Aug 23	24P 41A 8P
56	74	1316.2	-1172 Jul 17	0144 Sep 15	21P 13A 15H 15T 10P
57	73	1298.1	-1161 Jun 17	0137 Aug 04	14P 33T 13H 6A 7P
58	72	1280.1	-1114 Jun 07	0166 Jul 14	21P 44A 7P
59	72	1280.1	-1031 Jun 19	0249 Jul 27	9P 23A 16H 16T 8P
60	72	1280.1	-1020 May 18	0260 Jun 26	8P 40T 4H 14A 6P
61	71	1262.1	-0973 May 10	0289 Jun 05	8P 3T 1H 52A 7P
62	71	1262.1	-0890 May 22	0372 Jun 17	7P 25A 5H 27T 7P
63	72	1280.1	-0879 Apr 20	0401 May 29	7P 42T 2H 14A 7P
64	71	1262.1	-0832 Apr 11	0430 May 08	8P 4T 2H 46A 11P
65	71	1262.1	-0749 Apr 24	0513 May 20	6P 27A 4H 25T 9P
66	73	1298.1	-0756 Mar 12	0542 May 01	8P 43T 1H 4A 17P
67	72	1280.1	-0709 Mar 04	0571 Apr 10	9P 5T 2H 34A 22P
68	72	1280.1	-0626 Mar 16	0654 Apr 22	7P 28A 3H 11T 23P
69	78	1388.3	-0724 Dec 09	0665 Mar 22	14P 43T 21P
70	84	1496.5	-0821 Sep 05	0676 Feb 19	23P 5T 3H 32A 21P
71	82	1460.4	-0684 Oct 19	0777 Mar 14	18P 29A 3H 9T 23P
72	83	1478.4	-0727 Aug 16	0752 Jan 21	22P 43T 18P
73	72	1280.1	-0698 Jul 27	0582 Sep 03	23P 7T 3H 31A 8P
74	75	1334.2	-0615 Aug 08	0719 Oct 18	22P 30A 3H 8T 12P
75	73	1298.1	-0604 Jul 07	0694 Aug 26	21P 44T 8P
76	72	1280.1	-0575 Jun 18	0705 Jul 25	22P 8T 5H 30A 7P
77	71	1262.1	-0474 Jul 11	0788 Aug 06	18P 36A 2H 7T 8P
78	72	1280.1	-0463 Jun 09	0817 Jul 18	9P 9A 2H 45T 7P
79	71	1262.1	-0434 May 21	0828 Jun 16	8P 11T 16H 30A 6P
80	71	1262.1	-0333 Jun 13	0929 Jul 09	7P 48A 2H 6T 8P
81	72	1280.1	-0322 May 12	0958 Jun 19	7P 5A 9H 44T 7P
82	71	1262.1	-0293 Apr 22	0969 May 19	8P 11T 5H 39A 8P
83	71	1262.1	-0210 May 05	1052 May 30	7P 51A 1H 3T 9P
84	72	1280.1	-0181 Apr 14	1099 May 22	7P 1A 11H 43T 10P
85	72	1280.1	-0170 Mar 14	1110 Apr 20	8P 12T 4H 29A 19P
86	71	1262.1	-0069 Apr 06	1193 May 02	7P 41A 23P
87	73	1298.1	-0076 Feb 23	1222 Apr 13	9P 2H 42T 20P
88	83	1478.4	-0246 Oct 06	1233 Mar 12	20P 13T 4H 26A 20P
89	73	1298.1	0018 Feb 04	1316 Mar 24	10P 40A 23P
90	83	1478.4	-0134 Sep 28	1345 Mar 04	20P 2H 40T 21P
91	75	1334.2	-0159 Aug 06	1175 Oct 16	23P 14T 3H 25A 10P
92	74	1316.2	-0076 Aug 19	1240 Oct 16	23P 40A 11P
93	74	1316.2	-0029 Aug 09	1287 Oct 08	20P 3A 1H 40T 10P
94	72	1280.1	-0018 Jul 09	1262 Aug 16	21P 18T 2H 24A 7P
95	71	1262.1	0047 Jul 11	1309 Aug 06	22P 41A 8P
96	72	1280.1	0094 Jul 01	1374 Aug 08	10P 14A 2H 39T 7P
97	71	1262.1	0123 Jun 11	1385 Jul 08	8P 32T 2H 23A 6P
98	71	1262.1	0188 Jun 12	1450 Jul 09	9P 54A 8P
99	72	1280.1	0235 Jun 03	1515 Jul 11	7P 18A 2H 37T 8P
100	71	1262.1	0264 May 13	1526 Jun 10	7P 34T 2H 21A 7P
101	71	1262.1	0329 May 15	1591 Jun 21	8P 53A 10P
102	71	1262.1	0376 May 05	1638 Jun 12	7P 19A 3H 34T 8P
103	72	1280.1	0387 Apr 04	1667 May 22	8P 34T 3H 13A 14P
104	70	1244.0	0470 Apr 17	1714 May 13	7P 41A 22P
105	72	1280.1	0499 Mar 27	1779 May 16	7P 20A 4H 21T 20P
106	75	1334.2	0456 Jan 23	1790 Apr 14	12P 34T 4H 5A 20P
107	72	1280.1	0557 Feb 15	1837 Apr 05	10P 40A 22P
108	76	1352.2	0550 Jan 04	1902 Apr 08	12P 20A 5H 18T 21P
109	81	1442.4	0416 Sep 07	1859 Feb 03	21P 24T 15H 4A 17P
110	72	1280.1	0463 Aug 30	1743 Oct 17	23P 39A 10P
111	79	1406.3	0528 Aug 30	1935 Jan 05	21P 11A 14H 17T 16P
112	72	1280.1	0539 Jul 31	1819 Sep 19	21P 24T 14H 5A 8P
113	71	1262.1	0586 Jul 22	1848 Aug 28	23P 40A 8P
114	72	1280.1	0651 Jul 23	1931 Sep 12	18P 13A 16H 17T 8P
115	72	1280.1	0662 Jun 21	1942 Aug 12	10P 37T 4H 14A 7P
116	70	1244.0	0727 Jun 23	1971 Jul 22	10P 53A 7P
117	71	1262.1	0792 Jun 24	2054 Aug 03	8P 23A 5H 28T 7P
118	72	1280.1	0803 May 24	2083 Jul 15	8P 40T 2H 15A 7P
119	71	1262.1	0850 May 15	2112 Jun 24	8P 2T 1H 51A 9P
120	71	1262.1	0933 May 27	2195 Jul 07	7P 25A 4H 26T 9P
121	71	1262.1	0944 Apr 25	2206 Jun 07	7P 42T 2H 11A 9P
122	70	1244.0	0991 Apr 17	2235 May 17	8P 3T 2H 37A 20P
123	70	1244.0	1074 Apr 29	2318 May 31	6P 27A 3H 14T 20P
124	73	1298.1	1049 Mar 06	2347 May 11	9P 43T 1H 20P
125	73	1298.1	1060 Feb 04	2358 Apr 09	12P 4T 2H 34A 21P
126	72	1280.1	1179 Mar 10	2459 May 03	8P 28A 3H 10T 23P
127	82	1460.4	0991 Oct 10	2452 Mar 21	20P 42T 20P
128	73	1298.1	0984 Aug 29	2282 Nov 01	24P 4T 4H 32A 9P
129	80	1424.3	1103 Oct 03	2528 Feb 21	20P 29A 3H 9T 19P
130	73	1298.1	1096 Aug 20	2394 Oct 25	21P 43T 9P
131	70	1244.0	1125 Aug 01	2369 Sep 02	22P 6T 5H 30A 7P
132	71	1262.1	1208 Aug 13	2470 Sep 25	20P 33A 2H 7T 9P
133	72	1280.1	1219 Jul 13	2499 Sep 05	12P 6A 1H 46T 7P
134	71	1262.1	1248 Jun 22	2510 Aug 06	10P 8T 16H 30A 7P
135	71	1262.1	1331 Jul 05	2593 Aug 17	10P 45A 2H 6T 8P
136	71	1262.1	1360 Jun 14	2622 Jul 30	8P 6A 6H 44T 7P
137	70	1244.0	1389 May 25	2633 Jun 28	8P 10T 6H 4A 3H 32A 7P
138	70	1244.0	1472 Jun 06	2716 Jul 11	7P 50A 1H 3T 9P
139	71	1262.1	1501 May 17	2763 Jul 03	7P 12H 43T 9P
140	71	1262.1	1512 Apr 16	2774 Jun 01	8P 11T 4H 32A 16P
141	70	1244.0	1613 May 19	2857 Jun 13	7P 41A 22P
142	72	1280.1	1624 Apr 17	2904 Jun 05	8P 1H 43T 20P
143	72	1280.1	1617 Mar 07	2897 Apr 23	10P 12T 4H 26A 20P
144	70	1244.0	1736 Apr 11	2980 May 05	8P 39A 23P
145	77	1370.3	1639 Jan 04	3009 Apr 17	14P 1A 1H 41T 20P
146	76	1352.2	1541 Sep 19	2893 Dec 29	22P 13T 4H 24A 13P
147	80	1424.3	1624 Oct 12	3049 Feb 24	21P 40A 19P
148	75	1334.2	1653 Sep 21	2987 Dec 12	20P 2A 1H 40T 12P
149	71	1262.1	1664 Aug 21	2926 Sep 28	21P 17T 3H 23A 7P
150	71	1262.1	1729 Aug 24	2991 Sep 29	22P 40A 9P
151	72	1280.1	1776 Aug 14	3056 Oct 01	18P 6A 1H 39T 8P
152	70	1244.0	1805 Jul 26	3049 Aug 20	9P 30T 3H 22A 6P
153	70	1244.0	1870 Jul 28	3114 Aug 22	13P 49A 8P
154	71	1262.1	1917 Jul 19	3179 Aug 25	7P 17A 3H 36T 8P
155	71	1262.1	1928 Jun 17	3190 Jul 24	8P 33T 3H 20A 7P
156	69	1226.0	2011 Jul 01	3237 Jul 14	8P 52A 9P
157	70	1244.0	2058 Jun 21	3302 Jul 17	6P 19A 3H 34T 8P
158	70	1244.0	2069 May 20	3313 Jun 16	7P 35T 2H 16A 10P
159	70	1244.0	2134 May 23	3378 Jun 17	8P 41A 21P
160	71	1262.1	2181 May 13	3443 Jun 20	7P 20A 3H 22T 19P
161	72	1280.1	2174 Apr 01	3454 May 20	9P 35T 3H 5A 20P
162	70	1244.0	2257 Apr 15	3501 May 10	9P 39A 22P
163	72	1280.1	2286 Mar 25	3566 May 13	9P 20A 4H 18T 21P
164	80	1424.3	2098 Oct 24	3523 Mar 10	20P 36T 4H 3A 17P
165	72	1280.1	2145 Oct 16	3425 Dec 02	22P 39A 11P
166	77	1370.3	2228 Oct 29	3599 Feb 08	19P 21A 5H 16T 16P
167	72	1280.1	2203 Sep 06	3483 Oct 24	21P 26T 14H 3A 8P
168	70	1244.0	2250 Aug 28	3494 Sep 22	23P 40A 7P
169	71	1262.1	2333 Sep 10	3595 Oct 16	19P 13A 16H 15T 8P
170	71	1262.1	2344 Aug 09	3606 Sep 15	11P 36T 11H 6A 7P
171	69	1226.0	2391 Aug 01	3617 Aug 14	14P 48A 7P
172	70	1244.0	2474 Aug 13	3718 Sep 08	8P 23A 16H 15T 8P
173	70	1244.0	2485 Jul 12	3729 Aug 08	7P 41T 3H 12A 7P
174	69	1226.0	2532 Jul 04	3758 Jul 18	8P 1T 2H 50A 8P
175	70	1244.0	2597 Jul 05	3841 Jul 31	7P 26A 5H 24T 8P
176	71	1262.1	2608 Jun 04	3870 Jul 12	7P 43T 2H 10A 9P
177	69	1226.0	2655 May 27	3881 Jun 10	8P 3T 3H 37A 18P
178	70	1244.0	2738 Jun 09	3982 Jul 04	6P 28A 4H 11T 21P
179	71	1262.1	2731 Apr 28	3993 Jun 03	8P 44T 19P
180	70	1244.0	2760 Apr 08	4004 May 02	10P 5T 2H 33A 20P
        """
        lines = data_text.strip().split('\n')
        saros_dict = {}  # untuk menghindari duplikasi
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 9:
                continue
            try:
                saros = int(parts[0])
            except ValueError:
                continue
            if saros in saros_dict:
                continue  # ambil yang pertama
            first_date_str = f"{parts[3]} {parts[4]} {parts[5]}"
            last_date_str = f"{parts[6]} {parts[7]} {parts[8]}"
            try:
                jd_first = self._parse_nasa_date(first_date_str)
                jd_last = self._parse_nasa_date(last_date_str)
                saros_dict[saros] = (saros, jd_first, jd_last)
            except Exception:
                continue
        return list(saros_dict.values())

    def get_saros_number(self, jd_tt, eclipse_type='L'):
        """
        Menentukan nomor Saros untuk gerhana dengan mencocokkan JD puncak
        ke dalam rentang waktu setiap seri Saros.
        """
        if eclipse_type == 'L':
            saros_data = self._lunar_saros_data
        elif eclipse_type == 'S':
            saros_data = self._solar_saros_data
        else:
            return None

        best_saros = None
        min_rem = 99999.0
        SAROS_CYCLE_DAYS = 6585.321347

        for saros, first, last in saros_data:
            # Beri sedikit toleransi pada rentang
            if first - 30 <= jd_tt <= last + 30:
                delta = jd_tt - first
                cycles = round(delta / SAROS_CYCLE_DAYS)
                expected_jd = first + cycles * SAROS_CYCLE_DAYS
                rem = abs(jd_tt - expected_jd)
                if rem < min_rem:
                    min_rem = rem
                    best_saros = saros

        if min_rem < 3.0:  # toleransi maksimal 3 hari
            return best_saros
        return None

    # ------------------------------------------------------------------------
    # Visibilitas di Jolotundo
    # ------------------------------------------------------------------------
    def is_visible_at_jolotundo(self, jd_tt, eclipse_type='L'):
        """
        Mengecek apakah gerhana pada JD TT tertentu terlihat di Jolotundo.
        Untuk gerhana bulan: hitung altitude Bulan.
        Untuk gerhana matahari: hitung posisi topocentric dan altitude Matahari.
        """
        lat_jolo = self.const.JOLOTUNDO_LOCATION['coordinates']['latitude']
        lon_jolo = self.const.JOLOTUNDO_LOCATION['coordinates']['longitude']
        elev_jolo = self.const.JOLOTUNDO_LOCATION['elevation']['orthometric']

        if eclipse_type == 'L':
            # Dapatkan koordinat ekuatorial Bulan
            moon_lon, moon_lat, _, _ = self._moon_geocentric(jd_tt)
            eps = self._calc_true_obliquity(jd_tt)
            ra_moon, dec_moon = self._ecliptic_to_equatorial(moon_lon, moon_lat, eps)
            # Konversi ke waktu UTC
            year = self.time_sys.jd_to_gregorian(jd_tt)['year_astronomical']
            delta_t = self.time_sys.delta_t_espenak_extended(year)
            jd_utc = jd_tt - (delta_t + self.const.TT_TAI) / 86400.0
            # Hitung altitude
            from JRC_Ephemeris import UnifiedCoordinateTransformer
            trans = UnifiedCoordinateTransformer()
            altaz = trans.equatorial_to_altaz(ra_moon, dec_moon, jd_utc, lat_jolo, lon_jolo)
            altitude = altaz['altitude_apparent']
            return {
                'visible': altitude > 0,
                'altitude': altitude,
                'azimuth': altaz['azimuth'],
                'explanation': f"Bulan berada {altitude:.1f}° di atas horizon" if altitude > 0 else f"Bulan {altitude:.1f}° di bawah horizon"
            }

        else:  # eclipse_type == 'S' (gerhana Matahari)
            # 1. Dapatkan posisi geosentrik Matahari dan Bulan (equatorial apparent)
            sun_data = self.solar.sun_engine.calculate_sun_position_vsop87d(jd_tt, 'equatorial_apparent')
            moon_data = self.lunar.lunar_engine.calculate_position(jd_tt, output_frame='equatorial_apparent')

            ra_sun_geo = sun_data['ra_deg']
            dec_sun_geo = sun_data['dec_deg']
            dist_sun_au = sun_data['radius_au']

            ra_moon_geo = moon_data['equatorial_apparent']['ra_deg']
            dec_moon_geo = moon_data['equatorial_apparent']['dec_deg']
            dist_moon_au = moon_data['distance_au']

            # 2. Koreksi topocentric
            topo_corr = JPLStyleTopocentricCorrections()
            topo_sun = topo_corr.geocentric_to_topocentric_equatorial(
                ra_sun_geo, dec_sun_geo, dist_sun_au, jd_tt, lat_jolo, lon_jolo, elev_jolo
            )
            topo_moon = topo_corr.geocentric_to_topocentric_equatorial(
                ra_moon_geo, dec_moon_geo, dist_moon_au, jd_tt, lat_jolo, lon_jolo, elev_jolo
            )

            # 3. Hitung jarak sudut topocentric
            ra_sun = topo_sun['ra_topo_deg']
            dec_sun = topo_sun['dec_topo_deg']
            ra_moon = topo_moon['ra_topo_deg']
            dec_moon = topo_moon['dec_topo_deg']

            d_ra = math.radians(ra_moon - ra_sun)
            sin_dec_sun = math.sin(math.radians(dec_sun))
            cos_dec_sun = math.cos(math.radians(dec_sun))
            sin_dec_moon = math.sin(math.radians(dec_moon))
            cos_dec_moon = math.cos(math.radians(dec_moon))

            cos_theta = sin_dec_sun * sin_dec_moon + cos_dec_sun * cos_dec_moon * math.cos(d_ra)
            cos_theta = max(-1.0, min(1.0, cos_theta))
            angular_distance = math.degrees(math.acos(cos_theta))

            # 4. Hitung radius sudut topocentric
            R_sun_km = self.const.SUN_RADIUS / 1000.0
            R_moon_km = self.const.MOON_RADIUS / 1000.0
            dist_sun_topo_km = topo_sun['distance_topo_au'] * self.const.AU_TO_KM
            dist_moon_topo_km = topo_moon['distance_topo_au'] * self.const.AU_TO_KM

            ang_rad_sun = math.degrees(math.atan(R_sun_km / dist_sun_topo_km))
            ang_rad_moon = math.degrees(math.atan(R_moon_km / dist_moon_topo_km))
            sum_radii = ang_rad_sun + ang_rad_moon

            # 5. Hitung altitude Matahari topocentric
            transformer = UnifiedCoordinateTransformer()
            altaz_sun = transformer.equatorial_to_altaz(
                ra_sun, dec_sun, jd_tt, lat_jolo, lon_jolo
            )
            sun_alt = altaz_sun['altitude_apparent']

            # 6. Tentukan visibilitas
            is_eclipsed = angular_distance < sum_radii
            visible = is_eclipsed and sun_alt > 0

            return {
                'visible': visible,
                'sun_altitude': sun_alt,
                'angular_distance_arcmin': angular_distance * 60,
                'sum_radii_arcmin': sum_radii * 60,
                'explanation': (
                    f"Matahari {'di atas' if sun_alt>0 else 'di bawah'} horizon ({sun_alt:.1f}°), "
                    f"jarak sudut topocentric {angular_distance*60:.2f}' (batas {sum_radii*60:.2f}')"
                )
            }

    # ------------------------------------------------------------------------
    # Helper: true obliquity
    # ------------------------------------------------------------------------
    def _calc_true_obliquity(self, jd_tt):
        T = (jd_tt - 2451545.0) / 36525.0
        from JRC_Ephemeris import HighPrecisionNutation
        nut = HighPrecisionNutation()
        dPsi_deg, dEps_deg = nut.compute(T)
        eps_mean_deg = 23.4392911 - 0.0130042 * T - 0.00000016 * T**2
        return math.radians(eps_mean_deg + dEps_deg)

    # ------------------------------------------------------------------------
    # Helper: konversi ekliptika ke ekuatorial
    # ------------------------------------------------------------------------
    def _ecliptic_to_equatorial(self, lon_deg, lat_deg, eps_rad):
        lon_rad = math.radians(lon_deg)
        lat_rad = math.radians(lat_deg)
        sin_lon = math.sin(lon_rad)
        cos_lon = math.cos(lon_rad)
        sin_lat = math.sin(lat_rad)
        cos_lat = math.cos(lat_rad)
        sin_eps = math.sin(eps_rad)
        cos_eps = math.cos(eps_rad)

        y = sin_lon * cos_eps - math.tan(lat_rad) * sin_eps
        x = cos_lon
        ra_rad = math.atan2(y, x)
        if ra_rad < 0:
            ra_rad += 2 * math.pi

        sin_dec = sin_lat * cos_eps + cos_lat * sin_eps * sin_lon
        dec_rad = math.asin(max(min(sin_dec, 1.0), -1.0))

        return math.degrees(ra_rad), math.degrees(dec_rad)

    # ------------------------------------------------------------------------
    # Gerhana berikutnya (sederhana)
    # ------------------------------------------------------------------------
    def next_lunar_eclipse(self, jd_start_utc):
        """
        Mencari gerhana bulan berikutnya setelah jd_start_utc.
        """
        jd_start_tt = self.time_sys.jd_utc_to_tt_extended(jd_start_utc)
        dt_start = self.time_sys.jd_to_gregorian(jd_start_utc)
        year_start = dt_start['year_astronomical']
        # Cari hingga 3 tahun ke depan untuk memastikan
        for offset in range(4):
            year = year_start + offset
            ecl_list = self.find_lunar_eclipses(year)
            for e in ecl_list:
                if e['jd_tt'] > jd_start_tt:
                    return {
                        'datetime_wib': e['datetime_wib'],
                        'eclipse_type': e['eclipse_type']
                    }
        return None

    def next_solar_eclipse(self, jd_start_utc):
        """
        Mencari gerhana matahari berikutnya setelah jd_start_utc.
        """
        jd_start_tt = self.time_sys.jd_utc_to_tt_extended(jd_start_utc)
        dt_start = self.time_sys.jd_to_gregorian(jd_start_utc)
        year_start = dt_start['year_astronomical']
        for offset in range(4):
            year = year_start + offset
            ecl_list = self.find_solar_eclipses(year)
            for e in ecl_list:
                if e['jd_tt'] > jd_start_tt:
                    return {
                        'datetime_wib': e['datetime_wib'],
                        'eclipse_type': e['eclipse_type']
                    }
        return None


# ============================================================================
# FUNGSI PEMBANTU KONVERSI WAKTU
# ============================================================================

def jd_tt_to_wib(jd_tt, time_sys):
    """Konversi JD TT ke tuple (tahun, bulan, hari, jam, menit, detik) WIB."""
    jd_utc = jd_tt - 69.0 / 86400.0
    for _ in range(3):
        date_utc = time_sys.jd_to_gregorian(jd_utc)
        year = date_utc['year_astronomical']
        delta_t = time_sys.delta_t_jolotundo_calibrated(year)
        jd_utc_new = jd_tt - (delta_t + time_sys.const.TT_TAI) / 86400.0
        if abs(jd_utc_new - jd_utc) < 1e-8:
            break
        jd_utc = jd_utc_new
    jd_wib = jd_utc + 7.0 / 24.0
    date_wib = time_sys.jd_to_gregorian(jd_wib)
    return (date_wib['year_astronomical'], date_wib['month'], date_wib['day'],
            date_wib['hour'], date_wib['minute'], date_wib['second'])

def datetime_wib_to_jd_tt(dt_wib, time_sys):
    """Konversi datetime WIB ke JD TT."""
    jd_utc = time_sys.date_to_jd_utc(dt_wib.year, dt_wib.month, dt_wib.day,
                                      dt_wib.hour, dt_wib.minute, dt_wib.second)
    return time_sys.jd_utc_to_tt_extended(jd_utc)

def day_of_week(jd):
    """
    Mengembalikan nama hari untuk suatu Julian Day (TT).
    Menggunakan proleptic Gregorian.
    """
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    jd_int = int(jd + 0.5)  # pembulatan ke integer (JD pada tengah hari)
    idx = (jd_int - 2451545) % 7
    return days[(idx + 5) % 7]  # karena 2451545 adalah Sabtu (indeks 5)


# ============================================================================
# FUNGSI DISPLAY - DENGAN ANSI UNTUK TEKS TEBAL
# ============================================================================

# ANSI escape codes
BOLD = '\033[1m'
RESET = '\033[0m'

def print_header(title):
    """Cetak header dengan garis ganda dan teks tebal."""
    print(f"\n{BOLD}{'=' * 70}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'=' * 70}{RESET}")

def print_table(headers, rows):
    """
    Cetak tabel dengan format fixed-width (tanpa garis pembatas).
    Gaya klasik FORTRAN/IERS, kolom rapi dengan lebar tetap.
    Header dicetak tebal.
    """
    # Hitung lebar maksimum setiap kolom dari header dan data
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Tentukan jumlah spasi antar kolom
    gap = 4
    # Buat format string untuk setiap kolom (rata kiri) dengan lebar tetap
    fmt = (" " * gap).join(f"{{:<{w}}}" for w in col_widths)

    # Cetak header dengan tebal
    header_line = fmt.format(*headers)
    print(BOLD + header_line + RESET)

    # Cetak baris data (biasa)
    for row in rows:
        print(fmt.format(*[str(cell) for cell in row]))

def print_eclipse_detail(title, data_dict):
    """
    Cetak detail gerhana dalam format dua kolom sederhana.
    Lebar kolom pertama 25 karakter (rata kiri), kolom kedua bebas.
    """
    print(f"\n--- {title} ---")
    if not data_dict:
        print("  (tidak ada data)")
        return
    for label, value in data_dict.items():
        print(f"  {label:<25} : {value}")
    print("-" * 50)

def day_of_week(jd):
    """Mengembalikan nama hari (Indonesia) untuk Julian Day TT."""
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    jd_int = int(jd + 0.5)
    idx = (jd_int - 2451545) % 7
    return days[(idx + 5) % 7]

def format_datetime(y, m, d, hh, mm, ss=0):
    return f"{y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d}:{ss:02d}"


# ============================================================================
# FUNGSI MENU UTAMA
# ============================================================================

def clear_screen():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

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

def menu_solar():
    solar = SolarEvents()
    time_sys = TimeSystem()

    while True:
        clear_screen()
        print_header("FENOMENA MATAHARI")
        print("1. Equinox & Solstice untuk tahun tertentu")
        print("2. Aphelion & Perihelion untuk tahun tertentu")
        print("3. Jarak ke titik balik/ekuinoks (realtime atau tanggal tertentu)")
        print("4. Kembali ke menu utama")
        pilihan = input("Pilih (1-4): ").strip()

        if pilihan == '4':
            break

        if pilihan in ('1','2'):
            tahun = input_int("Masukkan tahun (astronomi, misal 2024): ")
            if pilihan == '1':
                events = [
                    ('Spring Equinox', 0),
                    ('Summer Solstice', 90),
                    ('Autumn Equinox', 180),
                    ('Winter Solstice', 270)
                ]
                rows = []
                for name, lon in events:
                    jd_tt, lon_calc, diff = solar.find_event(tahun, lon)
                    y,m,d,hh,mm,ss = jd_tt_to_wib(jd_tt, time_sys)
                    rows.append([
                        name,
                        format_datetime(y,m,d,hh,mm,ss),
                        f"{lon_calc:.6f}°",
                        f"{diff*3600:+.2f}\""
                    ])
                print_header(f"EQUINOX & SOLSTICE TAHUN {tahun}")
                print_table(["Event", "Waktu WIB", "Bujur", "Selisih target"], rows)
            else:
                jd_ap, r_ap = solar.find_aphelion(tahun)
                jd_per, r_per = solar.find_perihelion(tahun)
                y_ap,m_ap,d_ap,hh_ap,mm_ap,ss_ap = jd_tt_to_wib(jd_ap, time_sys)
                y_per,m_per,d_per,hh_per,mm_per,ss_per = jd_tt_to_wib(jd_per, time_sys)
                print_header(f"APHELION & PERIHELION TAHUN {tahun}")
                print(f"Aphelion  : {format_datetime(y_ap,m_ap,d_ap,hh_ap,mm_ap,ss_ap)} WIB, jarak {r_ap:.6f} AU")
                print(f"Perihelion: {format_datetime(y_per,m_per,d_per,hh_per,mm_per,ss_per)} WIB, jarak {r_per:.6f} AU")

        elif pilihan == '3':
            print("\nHitung jarak ke titik balik/ekuinoks")
            print("Gunakan waktu sekarang? (y/n): ", end="")
            if input().strip().lower() == 'y':
                now = datetime.now()
                tahun = now.year
                bulan = now.month
                hari = now.day
                jam = now.hour
                menit = now.minute
                detik = now.second
            else:
                tahun = input_int("Tahun: ")
                bulan = input_int("Bulan (1-12): ", 1, 12)
                hari = input_int("Hari (1-31): ", 1, 31)
                jam = input_int("Jam (0-23): ", 0, 23)
                menit = input_int("Menit (0-59): ", 0, 59)
                detik = input_int("Detik (0-59): ", 0, 59)

            # Konversi ke JD TT
            jd_utc = time_sys.date_to_jd_utc(tahun, bulan, hari, jam, menit, detik)
            jd_tt_target = time_sys.jd_utc_to_tt_extended(jd_utc)

            # Cari keempat event untuk tahun tersebut
            events = [
                ('Spring Equinox', 0),
                ('Summer Solstice', 90),
                ('Autumn Equinox', 180),
                ('Winter Solstice', 270)
            ]
            event_list = []
            for name, lon in events:
                jd_tt, _, _ = solar.find_event(tahun, lon)
                event_list.append((name, jd_tt))

            # Urutkan berdasarkan waktu
            event_list.sort(key=lambda x: x[1])

            # Buat tabel untuk semua titik dengan arah lalu/mendatang
            rows = []
            for name, jd in event_list:
                selisih_hari = (jd_tt_target - jd) * 1.0
                if selisih_hari > 0:
                    arah = "lalu"
                    jarak = selisih_hari
                else:
                    arah = "mendatang"
                    jarak = -selisih_hari
                rows.append([
                    name,
                    arah,
                    f"{jarak:.4f} hari ({jarak*24:.2f} jam)"
                ])

            print_header(f"JARAK KE TITIK BALIK/EKUINOKS (waktu input: {tahun}-{bulan:02d}-{hari:02d} {jam:02d}:{menit:02d})")
            print_table(["Event", "Arah (dari input)", "Selisih"], rows)

        input("\nTekan Enter untuk kembali...")


def menu_lunar():
    lunar = LunarEvents()
    time_sys = TimeSystem()

    while True:
        clear_screen()
        print_header("FENOMENA BULAN")
        print("1. Semua New Moon & Full Moon dalam tahun tertentu")
        print("2. Perigee & Apogee pertama dalam tahun tertentu")
        print("3. Major & Minor Standstill pertama dalam tahun tertentu")
        print("4. Cari fenomena terdekat dengan tanggal tertentu")
        print("5. Kembali ke menu utama")
        pilihan = input("Pilih (1-5): ").strip()

        if pilihan == '5':
            break

        if pilihan == '1':
            tahun = input_int("Masukkan tahun (astronomi, misal 2024): ")
            phases = lunar.get_all_lunar_phases_in_year(tahun)
            if not phases:
                print("Tidak ada fase bulan ditemukan.")
            else:
                print_header(f"SEMUA NEW MOON & FULL MOON TAHUN {tahun}")
                headers = ["No", "Jenis", "Tanggal WIB", "Hari ke-"]
                rows = []
                for i, (jd, typ) in enumerate(phases, 1):
                    y,m,d,hh,mm,ss = jd_tt_to_wib(jd, time_sys)
                    jd_utc_jan1 = time_sys.date_to_jd_utc(tahun, 1, 1, 0, 0, 0)
                    jd_tt_jan1 = time_sys.jd_utc_to_tt_extended(jd_utc_jan1)
                    day_of_year = int((jd - jd_tt_jan1) + 1)
                    rows.append([i, typ, format_datetime(y,m,d,hh,mm,ss), day_of_year])
                print_table(headers, rows)

        elif pilihan == '2':
            tahun = input_int("Masukkan tahun (astronomi, misal 2024): ")
            jd_peri = lunar.find_first_perigee(tahun)
            jd_apo = lunar.find_first_apogee(tahun)
            y_p,m_p,d_p,hh_p,mm_p,ss_p = jd_tt_to_wib(jd_peri, time_sys)
            y_a,m_a,d_a,hh_a,mm_a,ss_a = jd_tt_to_wib(jd_apo, time_sys)
            r_peri = lunar._moon_distance(jd_peri)
            r_apo = lunar._moon_distance(jd_apo)
            print_header(f"PERIGEE & APOGEE PERTAMA TAHUN {tahun}")
            print(f"Perigee: {format_datetime(y_p,m_p,d_p,hh_p,mm_p,ss_p)} WIB, jarak {r_peri:.1f} km")
            print(f"Apogee : {format_datetime(y_a,m_a,d_a,hh_a,mm_a,ss_a)} WIB, jarak {r_apo:.1f} km")

        elif pilihan == '3':
            tahun = input_int("Masukkan tahun (astronomi, misal 2024): ")
            jd_major = lunar.find_first_major_standstill(tahun)
            jd_minor = lunar.find_first_minor_standstill(tahun)
            y_mj,m_mj,d_mj,hh_mj,mm_mj,ss_mj = jd_tt_to_wib(jd_major, time_sys)
            y_mn,m_mn,d_mn,hh_mn,mm_mn,ss_mn = jd_tt_to_wib(jd_minor, time_sys)
            dec_major = lunar._moon_declination(jd_major)
            dec_minor = lunar._moon_declination(jd_minor)
            print_header(f"LUNAR STANDSTILL PERTAMA TAHUN {tahun}")
            print(f"Major: {format_datetime(y_mj,m_mj,d_mj,hh_mj,mm_mj,ss_mj)} WIB, deklinasi {dec_major:.2f}°")
            print(f"Minor: {format_datetime(y_mn,m_mn,d_mn,hh_mn,mm_mn,ss_mn)} WIB, deklinasi {dec_minor:.2f}°")

        elif pilihan == '4':
            print("\nMasukkan tanggal (WIB) untuk mencari fenomena terdekat:")
            tahun = input_int("Tahun: ")
            bulan = input_int("Bulan (1-12): ", 1, 12)
            hari = input_int("Hari (1-31): ", 1, 31)
            jam = input_int("Jam (0-23): ", 0, 23)
            menit = input_int("Menit (0-59): ", 0, 59)
            detik = input_int("Detik (0-59): ", 0, 59)

            jd_utc = time_sys.date_to_jd_utc(tahun, bulan, hari, jam, menit, detik)
            jd_tt_target = time_sys.jd_utc_to_tt_extended(jd_utc)

            # Fenomena bulan
            jd_new = lunar.find_new_moon(jd_tt_target)
            jd_full = lunar.find_full_moon(jd_tt_target)
            jd_peri = lunar.find_nearest_perigee(jd_tt_target)
            jd_apo = lunar.find_nearest_apogee(jd_tt_target)
            jd_major = lunar.find_major_standstill(jd_tt_target)
            jd_minor = lunar.find_minor_standstill(jd_tt_target)

            # Gerhana
            ecl = EclipseCalculator()
            # Cari gerhana bulan terdekat
            bulan_terdekat = None
            selisih_min = float('inf')
            for yr in [tahun-1, tahun, tahun+1]:
                for e in ecl.find_lunar_eclipses(yr):
                    selisih = abs(e['jd_tt'] - jd_tt_target)
                    if selisih < selisih_min:
                        selisih_min = selisih
                        bulan_terdekat = e
            # Cari gerhana matahari terdekat
            matahari_terdekat = None
            selisih_min = float('inf')
            for yr in [tahun-1, tahun, tahun+1]:
                for e in ecl.find_solar_eclipses(yr):
                    selisih = abs(e['jd_tt'] - jd_tt_target)
                    if selisih < selisih_min:
                        selisih_min = selisih
                        matahari_terdekat = e

            def delta_days(jd):
                return (jd - jd_tt_target) * 1.0

            rows = []
            # Fenomena bulan
            for name, jd in [("New Moon", jd_new), ("Full Moon", jd_full),
                             ("Perigee", jd_peri), ("Apogee", jd_apo),
                             ("Major Standstill", jd_major), ("Minor Standstill", jd_minor)]:
                y,m,d,hh,mm,ss = jd_tt_to_wib(jd, time_sys)
                rows.append([name, format_datetime(y,m,d,hh,mm,ss), f"{delta_days(jd):+.4f} hari"])

            # Gerhana
            if bulan_terdekat:
                y,m,d,hh,mm,ss = jd_tt_to_wib(bulan_terdekat['jd_tt'], time_sys)
                rows.append([f"Gerhana Bulan ({bulan_terdekat['eclipse_type']})",
                             format_datetime(y,m,d,hh,mm,ss),
                             f"{delta_days(bulan_terdekat['jd_tt']):+.4f} hari"])
            if matahari_terdekat:
                y,m,d,hh,mm,ss = jd_tt_to_wib(matahari_terdekat['jd_tt'], time_sys)
                rows.append([f"Gerhana Matahari ({matahari_terdekat['eclipse_type']})",
                             format_datetime(y,m,d,hh,mm,ss),
                             f"{delta_days(matahari_terdekat['jd_tt']):+.4f} hari"])

            print_header("FENOMENA TERDEKAT DENGAN TANGGAL INPUT")
            headers = ["Fenomena", "Waktu WIB", "Selisih"]
            # Hitung lebar kolom
            col_widths = [max(len(str(row[i])) for row in rows + [headers]) for i in range(3)]
            # Cetak header
            print("  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)))
            print("-" * (sum(col_widths) + 2 * (len(headers) - 1)))
            for row in rows:
                print("  ".join(str(row[i]).ljust(col_widths[i]) for i in range(3)))

        input("\nTekan Enter untuk kembali...")


def menu_realtime():
    solar = SolarEvents()
    lunar = LunarEvents()
    ecl = EclipseCalculator()
    time_sys = TimeSystem()

    clear_screen()
    print_header("FENOMENA REALTIME (WIB SEKARANG)")

    now = datetime.now()
    tahun = now.year
    print(f"Tahun berjalan: {tahun}\n")

    # 1. Equinox & Solstice tahun ini
    events = [
        ('Spring Equinox', 0),
        ('Summer Solstice', 90),
        ('Autumn Equinox', 180),
        ('Winter Solstice', 270)
    ]
    rows = []
    for name, lon in events:
        jd_tt, lon_calc, diff = solar.find_event(tahun, lon)
        y,m,d,hh,mm,ss = jd_tt_to_wib(jd_tt, time_sys)
        rows.append([name, format_datetime(y,m,d,hh,mm,ss), f"{diff*3600:+.2f}\""])
    print("EQUINOX & SOLSTICE TAHUN INI:")
    print_table(["Event", "Waktu WIB", "Selisih target"], rows)

    # 2. Aphelion & Perihelion
    jd_ap, r_ap = solar.find_aphelion(tahun)
    jd_per, r_per = solar.find_perihelion(tahun)
    y_ap,m_ap,d_ap,hh_ap,mm_ap,ss_ap = jd_tt_to_wib(jd_ap, time_sys)
    y_per,m_per,d_per,hh_per,mm_per,ss_per = jd_tt_to_wib(jd_per, time_sys)
    print("\nAPHELION & PERIHELION:")
    print(f"Aphelion  : {format_datetime(y_ap,m_ap,d_ap,hh_ap,mm_ap,ss_ap)} WIB, jarak {r_ap:.6f} AU")
    print(f"Perihelion: {format_datetime(y_per,m_per,d_per,hh_per,mm_per,ss_per)} WIB, jarak {r_per:.6f} AU")

    # 3. Jarak ke semua titik balik/ekuinoks dari sekarang
    jd_utc_now = time_sys.date_to_jd_utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
    jd_tt_now = time_sys.jd_utc_to_tt_extended(jd_utc_now)

    event_jds = []
    for name, lon in events:
        jd_tt, _, _ = solar.find_event(tahun, lon)
        event_jds.append((name, jd_tt))
    event_jds.sort(key=lambda x: x[1])

    rows = []
    for name, jd in event_jds:
        selisih_hari = (jd_tt_now - jd) * 1.0
        if selisih_hari > 0:
            arah = "lalu"
            jarak = selisih_hari
        else:
            arah = "mendatang"
            jarak = -selisih_hari
        rows.append([name, arah, f"{jarak:.4f} hari ({jarak*24:.2f} jam)"])
    print("\nJARAK KE TITIK BALIK/EKUINOKS DARI SEKARANG:")
    print_table(["Event", "Arah", "Selisih"], rows)

    # 4. Fenomena bulan terdekat dari sekarang
    jd_new = lunar.find_new_moon(jd_tt_now)
    jd_full = lunar.find_full_moon(jd_tt_now)
    jd_peri = lunar.find_nearest_perigee(jd_tt_now)
    jd_apo = lunar.find_nearest_apogee(jd_tt_now)
    jd_major = lunar.find_major_standstill(jd_tt_now)
    jd_minor = lunar.find_minor_standstill(jd_tt_now)

    def delta_days(jd):
        return (jd - jd_tt_now) * 1.0

    rows = []
    for name, jd in [("New Moon", jd_new), ("Full Moon", jd_full),
                     ("Perigee", jd_peri), ("Apogee", jd_apo),
                     ("Major Standstill", jd_major), ("Minor Standstill", jd_minor)]:
        y,m,d,hh,mm,ss = jd_tt_to_wib(jd, time_sys)
        rows.append([name, format_datetime(y,m,d,hh,mm,ss), f"{delta_days(jd):+.4f} hari"])
    print("\nFENOMENA BULAN TERDEKAT DARI SEKARANG:")
    print_table(["Fenomena", "Waktu WIB", "Selisih"], rows)

    # 5. Gerhana terdekat dari sekarang
    # Cari gerhana bulan terdekat dalam rentang tahun
    bulan_terdekat = None
    selisih_min = float('inf')
    for yr in [tahun-1, tahun, tahun+1]:
        for e in ecl.find_lunar_eclipses(yr):
            selisih = abs(e['jd_tt'] - jd_tt_now)
            if selisih < selisih_min:
                selisih_min = selisih
                bulan_terdekat = e
    matahari_terdekat = None
    selisih_min = float('inf')
    for yr in [tahun-1, tahun, tahun+1]:
        for e in ecl.find_solar_eclipses(yr):
            selisih = abs(e['jd_tt'] - jd_tt_now)
            if selisih < selisih_min:
                selisih_min = selisih
                matahari_terdekat = e

    rows = []
    if bulan_terdekat:
        y,m,d,hh,mm,ss = jd_tt_to_wib(bulan_terdekat['jd_tt'], time_sys)
        rows.append([f"Gerhana Bulan ({bulan_terdekat['eclipse_type']})",
                     format_datetime(y,m,d,hh,mm,ss),
                     f"{delta_days(bulan_terdekat['jd_tt']):+.4f} hari"])
    if matahari_terdekat:
        y,m,d,hh,mm,ss = jd_tt_to_wib(matahari_terdekat['jd_tt'], time_sys)
        rows.append([f"Gerhana Matahari ({matahari_terdekat['eclipse_type']})",
                     format_datetime(y,m,d,hh,mm,ss),
                     f"{delta_days(matahari_terdekat['jd_tt']):+.4f} hari"])
    if rows:
        print("\nGERHANA TERDEKAT DARI SEKARANG:")
        print_table(["Fenomena", "Waktu WIB", "Selisih"], rows)

    input("\nTekan Enter untuk kembali ke menu utama...")


def menu_eclipse():
    """Submenu untuk perhitungan gerhana dengan detail durasi, visibilitas, dan Saros."""
    ecl = EclipseCalculator()
    time_sys = TimeSystem()

    while True:
        clear_screen()
        print_header("KALKULATOR GERHANA")
        print("1. Gerhana Bulan dalam tahun tertentu")
        print("2. Gerhana Matahari dalam tahun tertentu")
        print("3. Gerhana berikutnya dari sekarang")
        print("4. Kembali ke menu utama")
        sub = input("Pilih (1-4): ").strip()

        if sub == '4':
            break

        elif sub == '1':
            tahun = input_int("Masukkan tahun (astronomi, misal 2024): ")
            daftar = ecl.find_lunar_eclipses(tahun)
            if not daftar:
                print(f"\nTidak ada gerhana Bulan pada tahun {tahun}.")
            else:
                print_header(f"GERHANA BULAN TAHUN {tahun}")
                # Tampilkan tabel ringkas
                headers = ["No", "Tanggal WIB", "Jenis", "Mag.Umbra", "Mag.Penumbra"]
                rows = []
                for i, e in enumerate(daftar, 1):
                    rows.append([
                        i,
                        e['datetime_wib'],
                        e['eclipse_type'],
                        f"{e['magnitude_umbra']:.3f}",
                        f"{e['magnitude_penumbra']:.3f}"
                    ])
                print_table(headers, rows)

                pilih = input("\nPilih nomor gerhana untuk detail (0 untuk kembali): ").strip()
                if pilih.isdigit():
                    idx = int(pilih)
                    if 1 <= idx <= len(daftar):
                        e = daftar[idx-1]
                        jd_tt = e['jd_tt']
                        # Ambil data tambahan
                        _, moon_lat, dist_moon_km, _ = ecl._moon_geocentric(jd_tt)
                        _, _, dist_sun_au = ecl._sun_geocentric(jd_tt)
                        contacts = ecl._lunar_contact_times(jd_tt, moon_lat, dist_moon_km, dist_sun_au * ecl.const.AU_TO_KM)
                        vis = ecl.is_visible_at_jolotundo(jd_tt, eclipse_type='L')
                        saros = ecl.get_saros_number(jd_tt, eclipse_type='L')

                        hari = day_of_week(e['jd_tt'])
                        
                        detail = {
                            "Hari": hari,
                            "Waktu Puncak (WIB)": e['datetime_wib'],
                            "Jenis": e['eclipse_type'],
                            "Magnitudo Umbra": f"{e['magnitude_umbra']:.3f}",
                            "Magnitudo Penumbra": f"{e['magnitude_penumbra']:.3f}",
                            "Lintang Bulan": f"{e['lunar_latitude_deg']:.4f}°",
                            "Jarak Bulan": f"{e['distance_moon_km']:.1f} km",
                        }
                        
                        if contacts.get('P1') and contacts.get('P4'):
                            detail["Durasi Penumbra"] = f"{contacts['duration_penumbral_hours']:.2f} jam"
                        if contacts.get('U1') and contacts.get('U4'):
                            detail["Durasi Umbra"] = f"{contacts['duration_umbral_hours']:.2f} jam"
                        if contacts.get('U2') and contacts.get('U3'):
                            detail["Durasi Total"] = f"{contacts['duration_total_hours']:.2f} jam"
                        
                        detail["Visibilitas di Jolotundo"] = "YA" if vis['visible'] else "TIDAK"
                        if vis['visible']:
                            detail["Altitude Bulan"] = f"{vis['altitude']:.1f}°"
                            detail["Azimuth"] = f"{vis['azimuth']:.1f}°"
                        
                        if saros:
                            detail["Nomor Saros"] = saros
                        
                        print_eclipse_detail("DETAIL GERHANA BULAN", detail)
                    else:
                        print("Nomor tidak valid.")
            input("\nTekan Enter...")

        elif sub == '2':
            tahun = input_int("Masukkan tahun (astronomi, misal 2024): ")
            daftar = ecl.find_solar_eclipses(tahun)
            if not daftar:
                print(f"\nTidak ada gerhana Matahari pada tahun {tahun}.")
            else:
                print_header(f"GERHANA MATAHARI TAHUN {tahun}")
                headers = ["No", "Tanggal WIB", "Jenis", "Magnitudo"]
                rows = []
                for i, e in enumerate(daftar, 1):
                    rows.append([
                        i,
                        e['datetime_wib'],
                        e['eclipse_type'],
                        f"{e['magnitude_geocentric']:.3f}"
                    ])
                print_table(headers, rows)

                pilih = input("\nPilih nomor gerhana untuk detail (0 untuk kembali): ").strip()
                if pilih.isdigit():
                    idx = int(pilih)
                    if 1 <= idx <= len(daftar):
                        e = daftar[idx-1]
                        jd_tt = e['jd_tt']

                        # Hitung altitude di Jolotundo
                        lat_jolo = ecl.const.JOLOTUNDO_LOCATION['coordinates']['latitude']
                        lon_jolo = ecl.const.JOLOTUNDO_LOCATION['coordinates']['longitude']
                        alt_sun = ecl._sun_altitude(jd_tt, lat_jolo, lon_jolo)

                        vis = alt_sun > 0
                        saros = ecl.get_saros_number(jd_tt, eclipse_type='S')

                        hari = day_of_week(e['jd_tt'])
                        
                        detail = {
                            "Hari": hari,
                            "Waktu Puncak (WIB)": e['datetime_wib'],
                            "Jenis": e['eclipse_type'],
                            "Magnitudo Geosentrik": f"{e['magnitude_geocentric']:.3f}",
                            "Lintang Bulan": f"{e['lunar_latitude_deg']:.4f}°",
                            "Jarak Bulan": f"{e['distance_moon_km']:.1f} km",
                            "Jarak Matahari": f"{e['distance_sun_km']:.1f} km",
                            "Diameter Bulan": f"{e['moon_angular_radius_arcmin']:.2f}'",
                            "Diameter Matahari": f"{e['sun_angular_radius_arcmin']:.2f}'",
                        }
                        
                        if e['max_duration_seconds'] > 0:
                            menit = e['max_duration_seconds'] / 60
                            detail["Durasi Maksimum"] = f"{e['max_duration_seconds']:.1f} dtk ({menit:.2f} mnt)"
                        
                        detail["Altitude Matahari di Jolotundo"] = f"{alt_sun:.1f}°"
                        detail["Visibilitas di Jolotundo"] = "YA" if vis else "TIDAK"
                        
                        if saros:
                            detail["Nomor Saros"] = saros
                        
                        print_eclipse_detail("DETAIL GERHANA MATAHARI", detail)
                    else:
                        print("Nomor tidak valid.")
                input("\nTekan Enter...")

        elif sub == '3':
            from datetime import datetime
            now = datetime.now()
            jd_now = time_sys.date_to_jd_utc(now.year, now.month, now.day,
                                             now.hour, now.minute, now.second)
            next_lunar = ecl.next_lunar_eclipse(jd_now)
            next_solar = ecl.next_solar_eclipse(jd_now)

            print("\nGerhana berikutnya dari sekarang:")
            if next_lunar:
                print(f"  Bulan   : {next_lunar['datetime_wib']} – {next_lunar['eclipse_type']}")
            else:
                print("  Bulan   : tidak ditemukan dalam 2 tahun ke depan")
            if next_solar:
                print(f"  Matahari: {next_solar['datetime_wib']} – {next_solar['eclipse_type']}")
            else:
                print("  Matahari: tidak ditemukan dalam 2 tahun ke depan")
            input("\nTekan Enter...")

        else:
            print("Pilihan tidak valid.")
            input("Tekan Enter...")


def main_menu():
    while True:
        clear_screen()
        print_header("JOLOTUNDO - SOLAR & LUNAR EVENTS")
        print("1. Fenomena Matahari")
        print("2. Fenomena Bulan")
        print("3. Realtime (sekarang)")
        print("4. Gerhana Matahari & Bulan")
        print("5. Keluar")
        pilihan = input("Pilih (1-5): ").strip()

        if pilihan == '5':
            print("\nTerima kasih!")
            break

        elif pilihan == '1':
            menu_solar()

        elif pilihan == '2':
            menu_lunar()

        elif pilihan == '3':
            menu_realtime()

        elif pilihan == '4':
            menu_eclipse()   # submenu gerhana

        else:
            print("Pilihan tidak valid.")
            input("Tekan Enter...")


if __name__ == "__main__":
    main_menu()