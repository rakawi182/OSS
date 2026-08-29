#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Hindari pembuatan __pycache__
import sys
sys.dont_write_bytecode = True

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Union

# Impor dari modul eksternal (diasumsikan tersedia)
from JRC_Ephemeris import (
    TimeSystem as JRC_TimeSystem,
    VSOP87SolarEngine,
    LunarELP82Engine,
    UnifiedCoordinateTransformer,
    JPLStyleTopocentricCorrections,
    AtmosphericModel
)
from solar_lunar_events import LunarEvents
from wuku_system import WukuMechanicalEngine, CalendarConverter
from SPICA_v18 import NormalizationEngine
from Old_Java_Astronomy import (
    AstronomicalEngine,
    VedicTimeEngine,
    GrahacaraAsthaEngine,
    DewataMandalaEngine,
    ΩConstants,
    MathCore
)


# ============================================================================
# saka_calendar.py
# ============================================================================

class SakaConstants:
    MONTH_NAMES = [
        "Chaitra", "Vaisakha", "Jyestha", "Asadha",
        "Sravana", "Bhadrapada", "Asvini", "Kartika",
        "Margasira", "Pausa", "Magha", "Phalguna"
    ]
    RASIS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
             "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    RASI_LENGTH = 30.0
    PAKSA = ["Sukla", "Krsna"]
    TITHI_MAX = 15
    ADHIKA_PREFIX = "Punah"
    SYNODIC_MONTH_MEAN = 29.530588861
    TROPICAL_YEAR_MEAN = 365.242190

    @staticmethod
    def epoch_jd() -> float:
        return CalendarConverter.julian_to_jd(78, 3, 3)


class SakaCalendar:
    def __init__(self):
        self.const = SakaConstants
        self.time_sys = JRC_TimeSystem()
        
        # --- LAZY LOADING: engine diset None, dibuat saat dibutuhkan ---
        self._sun_calc = None
        self._moon_calc = None
        self._lunar_events = None
        self._transformer = None
        
        self.cal_conv = CalendarConverter()
        self.norm = NormalizationEngine()
        self.jd_epoch = self.const.epoch_jd()

    # ========== GETTER LAZY LOADING ==========
    
    def _get_sun_engine(self):
        if self._sun_calc is None:
            self._sun_calc = VSOP87SolarEngine()
        return self._sun_calc

    def _get_moon_engine(self):
        if self._moon_calc is None:
            self._moon_calc = LunarELP82Engine()
        return self._moon_calc

    def _get_lunar_events(self):
        if self._lunar_events is None:
            self._lunar_events = LunarEvents(
                lunar_engine=self._get_moon_engine(),
                sun_engine=self._get_sun_engine(),
                time_sys=self.time_sys
            )
        return self._lunar_events

    def _get_transformer(self):
        if self._transformer is None:
            self._transformer = UnifiedCoordinateTransformer()
        return self._transformer

    # ========== FUNGSI UNTUK MEMBEBASKAN ENGINE (OPSIONAL) ==========
    
    def clear_engines(self):
        """Bebaskan engine berat untuk menghemat memory (misal di Pydroid3)."""
        self._sun_calc = None
        self._moon_calc = None
        self._lunar_events = None
        self._transformer = None
        import gc
        gc.collect()

    # ========== FUNGSI BANTU ASTRONOMI ==========
    
    def _jd_to_tt(self, jd_utc: float) -> float:
        return self.time_sys.jd_utc_to_tt_extended(jd_utc)

    def _tt_to_utc(self, jd_tt: float) -> float:
        jd_utc = jd_tt - 69.0 / 86400.0
        for _ in range(3):
            date = self.time_sys.jd_to_gregorian(jd_utc)
            delta_t = self.time_sys.delta_t_jolotundo_calibrated(date['year_astronomical'])
            jd_utc_new = jd_tt - (delta_t + 32.184) / 86400.0
            if abs(jd_utc_new - jd_utc) < 1e-8:
                break
            jd_utc = jd_utc_new
        return jd_utc

    def _find_amavasya(self, jd_approx: float) -> float:
        jd_tt = self._get_lunar_events().find_new_moon(self._jd_to_tt(jd_approx))
        return self._tt_to_utc(jd_tt)

    def _find_purnima(self, jd_approx: float) -> float:
        jd_tt = self._get_lunar_events().find_full_moon(self._jd_to_tt(jd_approx))
        return self._tt_to_utc(jd_tt)

    def _get_sun_lon(self, jd_tt: float) -> float:
        sun = self._get_sun_engine()
        return sun.calculate_sun_position_vsop87d(jd_tt, 'ecliptic_apparent')['longitude_deg']

    def _compute_tithi_at_jd(self, jd_utc):
        jd_tt = self._jd_to_tt(jd_utc)
        sun_lon = self._get_sun_lon(jd_tt)
        moon = self._get_moon_engine()
        moon_data = moon.calculate_position(jd_tt, output_frame='ecliptic_apparent')
        moon_lon = moon_data['ecliptic_apparent']['longitude_deg']
        elong = (moon_lon - sun_lon) % 360
        tithi_index = int(elong // 12) + 1
        paksa = "Sukla" if elong < 180 else "Krsna"
        return tithi_index, paksa

    # ========== METHOD UTAMA ==========
    
    def get_chaitra_sukla_1(self, saka_year: int) -> float:
        if saka_year == 0:
            return self.jd_epoch
        from solar_lunar_events import SolarEvents
        solar = SolarEvents(self._get_sun_engine(), self.time_sys)
        ce_approx = 78 + saka_year
        jd_equinox_tt = solar.find_event(ce_approx, 0)[0]
        jd_equinox = self._tt_to_utc(jd_equinox_tt)
        jd_am = self._find_amavasya(jd_equinox)
        if jd_am > jd_equinox:
            jd_am = self._find_amavasya(jd_am - 15)
        return jd_am + 1.0

    def get_months_in_saka_year(self, saka_year: int) -> List[Dict]:
        chaitra_start = self.get_chaitra_sukla_1(saka_year)
        months = []
        current_start = chaitra_start

        for _ in range(13):
            amavasya = current_start - 1.0
            purnima = self._find_purnima(amavasya + 14.77)
            purnima_tt = self._jd_to_tt(purnima)
            rasi = int(self._get_sun_lon(purnima_tt) // 30) % 12
            month_name = self.const.MONTH_NAMES[rasi]

            is_adhika = False
            if months:
                prev_rasi = months[-1]['sun_rasi_at_purnima']
                if rasi == prev_rasi:
                    is_adhika = True
                    month_name = f"{self.const.ADHIKA_PREFIX} {month_name}"

            months.append({
                'month_name': month_name,
                'is_adhika': is_adhika,
                'start_jd': current_start,
                'purnima_jd': purnima,
                'sun_rasi_at_purnima': rasi,
                'index': len(months)
            })

            next_amavasya = self._find_amavasya(purnima + 14.77)
            current_start = next_amavasya + 1.0

            if current_start - chaitra_start > 380:
                break

        return months

    def jd_to_saka(self, jd_utc: float) -> Dict:
        year_approx = int((jd_utc - self.jd_epoch) / self.const.TROPICAL_YEAR_MEAN)

        for delta in range(-20, 21):
            saka_year = year_approx + delta
            try:
                months = self.get_months_in_saka_year(saka_year)
                if not months:
                    continue
                start_first = months[0]['start_jd']
                try:
                    next_months = self.get_months_in_saka_year(saka_year + 1)
                    end_last = next_months[0]['start_jd']
                except:
                    end_last = start_first + 380

                if start_first <= jd_utc < end_last:
                    for m in months:
                        next_start = months[m['index']+1]['start_jd'] if m['index']+1 < len(months) else end_last
                        if m['start_jd'] <= jd_utc < next_start:
                            day_offset = jd_utc - m['start_jd']
                            if day_offset < 15:
                                tithi = int(day_offset) + 1
                                paksa = "Sukla"
                            else:
                                tithi = int(day_offset) - 14
                                paksa = "Krsna"
                            return {
                                'saka_year': saka_year,
                                'month_name': m['month_name'],
                                'tithi': tithi,
                                'paksa': paksa,
                                'is_adhika': m['is_adhika'],
                                'jd_utc': jd_utc,
                                'start_jd': m['start_jd'],
                                'note': 'akurat'
                            }
            except Exception:
                continue

        raise ValueError(f"Tidak dapat menemukan tanggal Saka untuk JD {jd_utc:.6f}")

    def saka_to_jd(self, saka_year, month_name, tithi, paksa):
        month_norm = self.norm.normalize(month_name)
        paksa_norm = self.norm.normalize(paksa)

        months = self.get_months_in_saka_year(saka_year)

        candidates = []
        for m in months:
            base = m['month_name'].replace(f"{self.const.ADHIKA_PREFIX} ", "")
            if self.norm.normalize(base) == month_norm:
                candidates.append(m)

        if not candidates:
            raise ValueError(f"Bulan {month_name} tidak ditemukan dalam tahun Saka {saka_year}")

        if len(candidates) == 1:
            month = candidates[0]
            start = month['start_jd']
            if paksa_norm == "Sukla":
                offset = tithi - 1
            else:
                offset = 14 + tithi
            return start + offset

        best_jd = None
        best_diff = float('inf')
        expected_index = tithi if paksa_norm == "Sukla" else tithi + 15

        for month in candidates:
            start = month['start_jd']
            if paksa_norm == "Sukla":
                offset = tithi - 1
            else:
                offset = 14 + tithi
            jd_candidate = start + offset

            tithi_calc, paksa_calc = self._compute_tithi_at_jd(jd_candidate)
            calc_index = tithi_calc if paksa_calc == "Sukla" else tithi_calc + 15

            diff = abs(calc_index - expected_index)
            if diff < best_diff:
                best_diff = diff
                best_jd = jd_candidate

        return best_jd

    def get_tithi_bounds(self, saka_year: int, month_name: str, tithi: int, paksa: str) -> Tuple[float, float]:
        jd_month_start = self.saka_to_jd(saka_year, month_name, 1, "Sukla")
        
        paksa_norm = self.norm.normalize(paksa)
        if paksa_norm == "Sukla":
            elong_start = (tithi - 1) * 12.0
            elong_end   = tithi * 12.0
        else:
            elong_start = 180.0 + (tithi - 1) * 12.0
            elong_end   = 180.0 + tithi * 12.0

        synodic = 29.530588861
        approx_offset = (tithi - 0.5) * synodic / 30.0
        jd_tt_guess_start = self._jd_to_tt(jd_month_start) + approx_offset
        jd_tt_guess_end   = jd_tt_guess_start + 1.0

        jd_tt_start = self._get_lunar_events().find_elongation_time(jd_tt_guess_start, elong_start)
        jd_tt_end   = self._get_lunar_events().find_elongation_time(jd_tt_guess_end, elong_end)

        jd_start_utc = self._tt_to_utc(jd_tt_start)
        jd_end_utc   = self._tt_to_utc(jd_tt_end)

        return jd_start_utc, jd_end_utc

    def tampilkan_pola_kabisat(self, tahun_awal: int, tahun_akhir: int):
        print(f"\nPola Kabisat Saka {tahun_awal} - {tahun_akhir}")
        print("-" * 70)
        print(f"{'Tahun':>6} {'Jml Bulan':>10} {'Kabisat':<10} {'Bulan Kabisat'}")
        print("-" * 70)
        for saka in range(tahun_awal, tahun_akhir + 1):
            months = self.get_months_in_saka_year(saka)
            jumlah = len(months)
            kabisat = [m['month_name'] for m in months if m['is_adhika']]
            if kabisat:
                print(f"{saka:6} {jumlah:10} {'YA':<10} {kabisat[0]}")
            else:
                print(f"{saka:6} {jumlah:10} {'TIDAK':<10} -")


# ============================================================================
# jawa_astronomy_interface.py (digabungkan) - TIDAK DIUBAH
# ============================================================================

def format_time_jam(desimal: float) -> str:
    desimal %= 24.0
    h = int(desimal)
    m = int((desimal - h) * 60)
    s = int(((desimal - h) * 60 - m) * 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def format_angle_dms(deg: float) -> str:
    sign = '-' if deg < 0 else '+'
    d = abs(deg)
    dd = int(d)
    m = int((d - dd) * 60)
    s = ((d - dd) * 60 - m) * 60
    return f"{sign}{dd:02d}° {m:02d}' {s:05.2f}\""

def format_ra_hms(ra_deg: float) -> str:
    hours = ra_deg / 15.0
    h = int(hours)
    m = int((hours - h) * 60)
    s = ((hours - h) * 60 - m) * 60
    return f"{h:02d}h {m:02d}m {s:05.2f}s"

def format_ribuan(x: float, desimal: int = 0) -> str:
    if desimal == 0:
        return f"{x:,.0f}".replace(',', '.')
    else:
        return f"{x:,.{desimal}f}".replace(',', '.')


class JawaAstronomyInterface:
    def __init__(self):
        self.time_sys = JRC_TimeSystem()
        self.sun_calc = VSOP87SolarEngine()
        self.moon_calc = LunarELP82Engine()
        self.transformer = UnifiedCoordinateTransformer()
        self.topo_corr = JPLStyleTopocentricCorrections()
        self.atmos = AtmosphericModel()
        self.wuku_engine = WukuMechanicalEngine()
        self.saka_cal = SakaCalendar()
        self.astro_engine = AstronomicalEngine()
        self.vedic_engine = VedicTimeEngine()
        self.graha_engine = GrahacaraAsthaEngine()
        self.dewata_engine = DewataMandalaEngine()
        self.math = MathCore()

        self.lat = ΩConstants.LOC_LAT
        self.lon = ΩConstants.LOC_LON
        self.elev = ΩConstants.LOC_ELEV
        self.tz_offset = ΩConstants.LOC_TZ_OFFSET

    def get_comprehensive_info(self, dt_utc: datetime) -> dict:
        jd_utc = self.time_sys.date_to_jd_utc(
            dt_utc.year, dt_utc.month, dt_utc.day,
            dt_utc.hour, dt_utc.minute, dt_utc.second
        )
        jd_tt = self.time_sys.jd_utc_to_tt_extended(jd_utc)
        delta_t_seconds = (jd_tt - jd_utc) * 86400.0 - 32.184

        dt_wib = dt_utc + timedelta(hours=7)
        jam_wib = dt_wib.hour + dt_wib.minute/60.0 + dt_wib.second/3600.0

        ka = self.wuku_engine.julian_day_to_ka(jd_utc)
        wuku_info = self.wuku_engine.get_wuku_by_ka(ka)
        wuku_epoch_info = self.wuku_engine.get_detailed_wuku_epoch_info(ka)

        try:
            saka_info = self.saka_cal.jd_to_saka(jd_utc)
        except Exception:
            saka_info = {"saka_year": None, "month_name": None, "tithi": None, "paksa": None}

        sun_data = self.astro_engine.calculate_sun_position_ultra(jd_tt)
        ayanamsa = self.astro_engine.calculate_ayanamsa_precise(jd_tt)
        sun_nirayana = (sun_data['longitude_deg'] - ayanamsa) % 360
        sun_rasi_idx = int(sun_nirayana // 30)
        sun_rasi_name = ΩConstants.ZODIAC[sun_rasi_idx]

        moon_data = self.astro_engine.calculate_moon_position_ultra(jd_tt, sun_data['longitude_deg'])
        moon_nirayana = (moon_data['longitude'] - ayanamsa) % 360
        moon_nakshatra = self.astro_engine.calculate_nakshatra(moon_nirayana, "nirayana")
        moon_nakshatra_sayana = self.astro_engine.calculate_nakshatra(moon_data['longitude'], "tropical")

        jd_utc_float = jd_utc
        altaz_sun = self.transformer.equatorial_to_altaz(
            sun_data['ra_deg'], sun_data['dec_deg'], jd_utc_float,
            self.lat, self.lon, 1010.0, 25+273.15, 0.5
        )
        altaz_moon = self.transformer.equatorial_to_altaz(
            moon_data['ra'], moon_data['dec'], jd_utc_float,
            self.lat, self.lon, 1010.0, 25+273.15, 0.5
        )

        sunrise_info = self.astro_engine.calculate_sunrise_sunset_precise(jd_utc_float)

        tithi = self.astro_engine.calculate_tithi(sun_nirayana, moon_nirayana, "nirayana")

        tithi_duration_info = {}
        try:
            elong = moon_data.get('elongation')
            if elong is not None:
                tithi_idx = tithi['tithi']
                if tithi['paksa'] == 'Sukla':
                    elong_start = (tithi_idx - 1) * 12.0
                    elong_end   = tithi_idx * 12.0
                else:
                    elong_start = 180.0 + (tithi_idx - 1) * 12.0
                    elong_end   = 180.0 + tithi_idx * 12.0

                jd_tt_start = self.saka_cal._get_lunar_events().find_elongation_time(jd_tt - 0.5, elong_start)
                jd_tt_end   = self.saka_cal._get_lunar_events().find_elongation_time(jd_tt + 0.5, elong_end)

                jd_start_utc = self.saka_cal._tt_to_utc(jd_tt_start)
                jd_end_utc   = self.saka_cal._tt_to_utc(jd_tt_end)

                duration_hours = (jd_end_utc - jd_start_utc) * 24
                progress = ((jd_utc - jd_start_utc) / (jd_end_utc - jd_start_utc)) * 100

                jd_start_wib = jd_start_utc + 7/24
                jd_end_wib   = jd_end_utc + 7/24
                date_start_wib = self.time_sys.jd_to_gregorian(jd_start_wib)
                date_end_wib   = self.time_sys.jd_to_gregorian(jd_end_wib)

                def fmt_time(d):
                    return f"{d['hour']:02d}:{d['minute']:02d}:{d['second']:02d}"

                tithi_duration_info = {
                    'start_utc': fmt_time(self.time_sys.jd_to_gregorian(jd_start_utc)),
                    'end_utc': fmt_time(self.time_sys.jd_to_gregorian(jd_end_utc)),
                    'start_wib': fmt_time(date_start_wib),
                    'end_wib': fmt_time(date_end_wib),
                    'duration_hours': duration_hours,
                    'progress': progress,
                    'crosses_days': (date_start_wib['day'] != date_end_wib['day'] or
                                     date_start_wib['month'] != date_end_wib['month'] or
                                     date_start_wib['year'] != date_end_wib['year'])
                }
        except Exception as e:
            tithi_duration_info = {'error': str(e)}  
               
        yoga = self.vedic_engine.calculate_yoga(sun_nirayana, moon_nirayana)
        karana = self.vedic_engine.calculate_karana(sun_nirayana, moon_nirayana)
        parwesa = self.vedic_engine.calculate_parwesa_gompers(ka)
        dewata_mandala = self.dewata_engine.get_dewata_mandala_from_nakshatra(moon_nakshatra['nakshatra'])

        muhurta = self.vedic_engine.calculate_muhurta_jawa_kuno(ka, jam_wib)
        tabeh = self.vedic_engine.calculate_tabeh_precise(ka, jam_wib)

        graha_results = self.graha_engine.analyze_all_planets_by_date(
            dt_wib.year, dt_wib.month, dt_wib.day, jam_wib
        )

        return {
            "waktu": {
                "utc": dt_utc,
                "wib": dt_wib,
                "jd_utc": jd_utc,
                "jd_tt": jd_tt,
                "delta_t": delta_t_seconds,
                "ka": ka,
            },
            "wuku": {
                **wuku_info,
                "epoch_info": wuku_epoch_info,
            },
            "saka": saka_info,
            "panchanga": {
                "tithi": tithi,
                "tithi_duration": tithi_duration_info,
                "nakshatra": {
                    "nirayana": moon_nakshatra,
                    "sayana": moon_nakshatra_sayana,
                },
                "yoga": yoga,
                "karana": karana,
                "parwesa": parwesa,
                "dewata": dewata_mandala["dewata"],
                "mandala": dewata_mandala["mandala"],
            },
            "sun": {
                "tropical_lon": sun_data['longitude_deg'],
                "nirayana_lon": sun_nirayana,
                "rasi": sun_rasi_name,
                "ra": sun_data['ra_deg'],
                "dec": sun_data['dec_deg'],
                "altitude": altaz_sun['altitude_apparent'],
                "azimuth": altaz_sun['azimuth'],
                "equation_of_time": sun_data.get('equation_of_time_minutes', 0),
                "distance_au": sun_data.get('radius_au', 1),
            },
            "moon": {
                "tropical_lon": moon_data['longitude'],
                "nirayana_lon": moon_nirayana,
                "nakshatra": moon_nakshatra['nakshatra'],
                "pada": moon_nakshatra['pada'],
                "ra": moon_data['ra'],
                "dec": moon_data['dec'],
                "altitude": altaz_moon['altitude_apparent'],
                "azimuth": altaz_moon['azimuth'],
                "elongation": moon_data['elongation'],
                "illumination": moon_data['illumination'],
                "age_days": moon_data['age_days'],
                "distance_km": moon_data['distance_km'],
            },
            "sun_times": sunrise_info,
            "muhurta": muhurta,
            "tabeh": tabeh,
            "graha": graha_results,
        }

    def display_info(self, info: dict):
        print("\n" + "=" * 100)
        print("  SISTEM INFORMASI ASTRONOMI JAWA KUNO – JRC ENHANCED")
        print("=" * 100)

        print("\n📅  WAKTU DASAR")
        print("-" * 100)
        dt_wib = info['waktu']['wib']
        dt_utc = info['waktu']['utc']
        print(f"  Waktu Lokal (WIB)  : {dt_wib.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Waktu UTC          : {dt_utc.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Julian Day (UTC)   : {info['waktu']['jd_utc']:.6f}")
        print(f"  Julian Day (TT)    : {info['waktu']['jd_tt']:.6f}")
        print(f"  ΔT (TT – UT)       : {info['waktu']['delta_t']:.2f} detik")
        print(f"  Kali Ahargana (KA) : {format_ribuan(info['waktu']['ka'])}")

        w = info['wuku']
        print(f"\n  Wuku                : {w['wuku_name']} (#{w['wuku_number']})")
        print(f"  Hari dalam Wuku     : {w['day_in_wuku']}/7")
        print(f"  Wara Triple         : {w['wara_triple_full']} ({w['wara_triple']})")
        print(f"  TU-PA-Ā             : {'YA' if w['is_tu_pa_a'] else 'TIDAK'}")
        print(f"  Siklus Wuku         : {w['cycle_number']} (hari ke-{w['position_in_cycle']+1}/210)")

        s = info['saka']
        if s.get('saka_year') is not None:
            print(f"\n  Tahun Saka          : {s['saka_year']}")
            print(f"  Bulan Saka          : {s['month_name']}")
            t = info['panchanga']['tithi']
            if t['paksa'] == 'Sukla':
                tithi_paksha = t['tithi']
            else:
                tithi_paksha = t['tithi'] - 15
            print(f"  Tithi & Paksa       : {tithi_paksha} {t['paksa']}")
        else:
            print("\n  (Tanggal Saka tidak dapat ditentukan)")

        print("\n🌟  PANCAṄGA (5 ELEMEN WAKTU)")
        print("-" * 100)
        p = info['panchanga']
        t = p['tithi']
        if t['paksa'] == 'Sukla':
            tithi_paksha = t['tithi']
        else:
            tithi_paksha = t['tithi'] - 15
        print(f"  Tithi     : {tithi_paksha} {t['paksa']} ({t['percent']:.1f}%)")

        if 'tithi_duration' in p and p['tithi_duration'] and 'error' not in p['tithi_duration']:
            dur = p['tithi_duration']
            print(f"  Durasi    : {dur['duration_hours']:.2f} jam")
            print(f"  Progress  : {dur['progress']:.1f}%")
            print(f"  Waktu     : {dur['start_wib']} – {dur['end_wib']} WIB")
            if dur['crosses_days']:
                print(f"              (melintasi batas hari)")
            print()

        print(f"  Nakṣatra  : {p['nakshatra']['nirayana']['nakshatra']} (pada {p['nakshatra']['nirayana']['pada']})")
        print(f"            : (Sayana: {p['nakshatra']['sayana']['nakshatra']})")
        print(f"  Yoga      : {p['yoga']['name']} ({p['yoga']['percent']:.1f}%)")
        print(f"  Karana    : {p['karana']['name']}")
        print(f"  Parwesa   : {p['parwesa']['name']}")
        print(f"  Dewata    : {p['dewata']}")
        print(f"  Maṇḍala   : {p['mandala']}")

        print("\n☀️  MATAHARI")
        print("-" * 100)
        sun = info['sun']
        print(f"  Bujur Tropis       : {sun['tropical_lon']:.6f}°")
        print(f"  Bujur Nirayana     : {sun['nirayana_lon']:.6f}°")
        print(f"  Rasi               : {sun['rasi']}")
        print(f"  Right Ascension    : {format_ra_hms(sun['ra'])}")
        print(f"  Declination        : {format_angle_dms(sun['dec'])}")
        print(f"  Altitude           : {sun['altitude']:+.2f}°")
        print(f"  Azimuth            : {sun['azimuth']:7.2f}°")
        print(f"  Equation of Time   : {sun['equation_of_time']:.2f} menit")
        print(f"  Jarak              : {sun['distance_au']:.6f} AU")

        print("\n🌙  BULAN")
        print("-" * 100)
        moon = info['moon']
        print(f"  Bujur Tropis       : {moon['tropical_lon']:.6f}°")
        print(f"  Bujur Nirayana     : {moon['nirayana_lon']:.6f}°")
        print(f"  Nakṣatra           : {moon['nakshatra']} (pada {moon['pada']})")
        print(f"  Right Ascension    : {format_ra_hms(moon['ra'])}")
        print(f"  Declination        : {format_angle_dms(moon['dec'])}")
        print(f"  Altitude           : {moon['altitude']:+.2f}°")
        print(f"  Azimuth            : {moon['azimuth']:7.2f}°")
        print(f"  Elongasi           : {moon['elongation']:.2f}°")
        print(f"  Iluminasi          : {moon['illumination']:.1f}%")
        print(f"  Usia (umur)        : {moon['age_days']:.2f} hari")
        print(f"  Jarak              : {format_ribuan(moon['distance_km'], 1)} km")

        print("\n⏰  WAKTU MATAHARI")
        print("-" * 100)
        st = info['sun_times']
        if st and 'sunrise' in st:
            print(f"  Matahari Terbit    : {st['sunrise']['wib']} WIB")
            print(f"  Matahari Transit   : {st['transit']['wib']} WIB")
            print(f"  Matahari Terbenam  : {st['sunset']['wib']} WIB")
            print(f"  Panjang Siang      : {st['day_length']:.2f} jam")
        else:
            print("  (Data tidak tersedia)")

        print("\n⏳  MUHURTA & TABEH")
        print("-" * 100)
        muh = info['muhurta']
        if muh and 'error' not in muh:
            if 'period_start' in muh and 'muhurta_length' in muh and 'index' in muh:
                h, m_, s = map(int, muh['period_start'].split(':'))
                period_start_float = h + m_/60.0 + s/3600.0
                start_muhurta = period_start_float + muh['index'] * muh['muhurta_length']
                end_muhurta = start_muhurta + muh['muhurta_length']
                start_str = format_time_jam(start_muhurta)
                end_str = format_time_jam(end_muhurta)
            else:
                start_str = 'N/A'
                end_str = 'N/A'
            
            print(f"  Muhurta             : {muh['name']} ({muh['period']})")
            print(f"  Waktu Muhurta       : {start_str} – {end_str}")
            print(f"  Durasi Muhurta      : {muh.get('muhurta_length', 0):.2f} jam")
            print(f"  Progress            : {muh.get('progress', 0):.1f}%")
        else:
            print("  Muhurta tidak tersedia")

        tb = info['tabeh']
        if tb:
            print(f"\n  Tabeh               : {tb['tabeh_name']} ({tb['period_type']})")
            print(f"  Waktu Tabeh         : {tb['start_time']} – {tb['end_time']}")

        print("\n🪐  GRAHACARA ASTHA")
        print("-" * 100)
        print(f"  {'Planet':<10} {'Zona Ashta':<20} {'LHA':>8} {'Altitude':>9} {'Rasi':<10}")
        print(f"  {'-'*9:<10} {'-'*19:<20} {'-'*8:>8} {'-'*9:>9} {'-'*9:<10}")
        for planet, data in info['graha'].items():
            if "error" not in data:
                lha_str = f"{data['lha']:+.1f}°"
                alt_str = f"{data['astronomical_data']['altitude']:+.1f}°"
                rasi = data['astronomical_data']['rasi_nirayana']
                print(f"  {planet:<10} {data['zona_astha']:<20} {lha_str:>8} {alt_str:>9} {rasi:<10}")

        print("\n📝  CATATAN")
        print("-" * 100)
        print("  • Perhitungan: VSOP87D (Matahari) dan ELP2000‑82B (Bulan)")
        print("  • ΔT eclipse untuk tahun 700‑1300 M, Espenak & Meeus")
        print("  • Ayanamsa Lahiri dengan nutasi IAU2000A")
        print("  • Lokasi: Jolotundo (-7.618°, 112.617°, elev. 512 m)")
        print("  • WIB = UTC+7")
        print("  • Tithi, Naksatra, Yoga, Karana (VSOP87/ELP2000).")
        print("  • Tahun Saka dengan modifikasi interkalasi Metonik.")
        print("  • Epoch Saka 0 = 3 Maret 78 M (Chaitra Sukla 1).")

        print("\n" + "=" * 100 + "\n")

    def display_realtime(self):
        now_utc = datetime.now(timezone.utc)
        info = self.get_comprehensive_info(now_utc)
        self.display_info(info)

    def display_for_datetime(self, tahun: int, bulan: int, hari: int,
                             jam: int = 12, menit: int = 0, detik: int = 0,
                             is_wib: bool = True):
        if is_wib:
            dt_wib = datetime(tahun, bulan, hari, jam, menit, detik)
            dt_utc = dt_wib - timedelta(hours=7)
        else:
            dt_utc = datetime(tahun, bulan, hari, jam, menit, detik, tzinfo=timezone.utc)
        info = self.get_comprehensive_info(dt_utc)
        self.display_info(info)

    def run_menu(self):
        while True:
            print("\n" + "=" * 60)
            print("  JAWA ASTRONOMY INTERFACE – JRC ENHANCED")
            print("=" * 60)
            print("1. Informasi Realtime (waktu sekarang)")
            print("2. Informasi untuk Tanggal/Waktu Tertentu")
            print("3. Konversi Tanggal Saka → Masehi")
            print("4. Pola interkalasi untuk rentang tahun Saka")
            print("5. Keluar")
            print("-" * 60)

            pilihan = input("Pilih menu (1-5): ").strip()

            if pilihan == "1":
                self.display_realtime()
                input("\nTekan Enter untuk kembali ke menu...")

            elif pilihan == "2":
                try:
                    print("\nMasukkan tanggal dan waktu (WIB):")
                    tahun = int(input("  Tahun: "))
                    bulan = int(input("  Bulan (1-12): "))
                    hari = int(input("  Hari (1-31): "))
                    jam = int(input("  Jam (0-23, default 12): ") or "12")
                    menit = int(input("  Menit (0-59, default 0): ") or "0")
                    detik = int(input("  Detik (0-59, default 0): ") or "0")
                    self.display_for_datetime(tahun, bulan, hari, jam, menit, detik, is_wib=True)
                except Exception as e:
                    print(f"❌ Input tidak valid: {e}")
                input("\nTekan Enter untuk kembali ke menu...")

            elif pilihan == "3":
                try:
                    print("\nMasukkan tanggal Saka:")
                    saka_year = int(input("  Tahun Saka: "))
                    bulan = input("  Nama bulan Saka (misal: Kartika): ")
                    tithi = int(input("  Tithi (1-15): "))
                    paksa = input("  Paksa (Sukla/Krsna): ")

                    jd_start, jd_end = self.saka_cal.get_tithi_bounds(saka_year, bulan, tithi, paksa)

                    def fmt_date(d):
                        return f"{d['year_astronomical']:04d}-{d['month']:02d}-{d['day']:02d} {d['hour']:02d}:{d['minute']:02d}:{d['second']:02d}"

                    date_start = self.time_sys.jd_to_gregorian(jd_start)
                    date_end   = self.time_sys.jd_to_gregorian(jd_end)

                    print(f"\n📅 Hasil Konversi (rentang waktu tithi dalam UTC):")
                    print(f"  {bulan} {paksa} {tithi} Śaka {saka_year}")
                    print(f"  Mulai  : {fmt_date(date_start)} UTC")
                    print(f"  Akhir  : {fmt_date(date_end)} UTC")
                    print(f"  Julian Day: {jd_start:.6f} – {jd_end:.6f}")

                    jd_start_wib = jd_start + 7/24
                    jd_end_wib   = jd_end   + 7/24
                    date_start_wib = self.time_sys.jd_to_gregorian(jd_start_wib)
                    date_end_wib   = self.time_sys.jd_to_gregorian(jd_end_wib)

                    print(f"\n  (WIB = UTC+7):")
                    print(f"  Mulai  : {fmt_date(date_start_wib)} WIB")
                    print(f"  Akhir  : {fmt_date(date_end_wib)} WIB")

                    if (date_start_wib['day'] != date_end_wib['day'] or
                        date_start_wib['month'] != date_end_wib['month'] or
                        date_start_wib['year'] != date_end_wib['year']):
                        print(f"  Catatan: Tithi ini mencakup dua hari kalender (WIB).")
                    else:
                        print(f"  Catatan: Tithi ini berada dalam satu hari kalender (WIB).")

                except Exception as e:
                    print(f"❌ Error: {e}")
                input("\nTekan Enter untuk kembali ke menu...")

            elif pilihan == "4":
                try:
                    print("\nMasukkan rentang tahun Saka:")
                    tahun1 = int(input("  Tahun awal: "))
                    tahun2 = int(input("  Tahun akhir: "))
                    self.saka_cal.tampilkan_pola_kabisat(tahun1, tahun2)
                except Exception as e:
                    print(f"❌ Error: {e}")
                input("\nTekan Enter untuk kembali ke menu...")

            elif pilihan == "5":
                print("\nTerima kasih telah menggunakan Jawa Astronomy Interface!")
                break
            else:
                print("Pilihan tidak valid.")


if __name__ == "__main__":
    app = JawaAstronomyInterface()
    app.run_menu()