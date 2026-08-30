# saka_year_month.py
# Kelas SakaYearMonth – dipisahkan dari Old_Java_Astronomy untuk stabilitas import

import sys
sys.dont_write_bytecode = True

from JRC_Ephemeris import TimeSystem as JRC_TimeSystem
from solar_lunar_events import SolarEvents, LunarEvents
from saka_calendar import get_months_in_year


class SakaYearMonth:
    """
    Menghitung tahun dan bulan Saka dari JD UTC.
    Menggunakan lookup interkalasi dari saka_calendar.py.
    TIDAK menghitung tithi – ambil dari AstronomicalEngine.
    """

    def __init__(self, time_system, solar_events, lunar_events):
        self.time_sys = time_system
        self.solar = solar_events
        self.lunar = lunar_events
        self.cache_start = {}

    def _jd_to_tt(self, jd_utc):
        return self.time_sys.jd_utc_to_tt_extended(jd_utc)

    def _tt_to_utc(self, jd_tt):
        jd_utc = jd_tt - 69.0 / 86400.0
        for _ in range(3):
            date = self.time_sys.jd_to_gregorian(jd_utc)
            dt = self.time_sys.delta_t_jolotundo_calibrated(date['year_astronomical'])
            new = jd_tt - (dt + 32.184) / 86400.0
            if abs(new - jd_utc) < 1e-8:
                break
            jd_utc = new
        return jd_utc

    def _find_amavasya(self, jd_approx):
        jd_tt = self._jd_to_tt(jd_approx)
        jd_tt_new = self.lunar.find_new_moon(jd_tt)
        return self._tt_to_utc(jd_tt_new)

    def _find_purnima(self, jd_approx):
        jd_tt = self._jd_to_tt(jd_approx)
        jd_tt_new = self.lunar.find_full_moon(jd_tt)
        return self._tt_to_utc(jd_tt_new)

    def get_chaitra_sukla_1(self, saka_year):
        """JD UTC hari pertama tahun Saka (Chaitra Sukla 1)."""
        if saka_year in self.cache_start:
            return self.cache_start[saka_year]

        if saka_year == 0:
            # Tanggal 3 Maret 78 M, jam 00:00 UTC -> JD UTC
            jd = self.time_sys.date_to_jd_utc(78, 3, 3, 0, 0, 0)
        else:
            ce = 78 + saka_year
            jd_eq_tt = self.solar.find_event(ce, 0)[0]
            jd_eq = self._tt_to_utc(jd_eq_tt)
            am = self._find_amavasya(jd_eq)
            if am > jd_eq:
                am = self._find_amavasya(am - 15)
            jd = am + 1.0

        self.cache_start[saka_year] = jd
        return jd

    def jd_to_saka_year_month(self, jd_utc):
        epoch_jd = self.get_chaitra_sukla_1(0)
        approx = int((jd_utc - epoch_jd) / 365.242190)

        for delta in range(-5, 6):
            sy = approx + delta
            start = self.get_chaitra_sukla_1(sy)
            try:
                end = self.get_chaitra_sukla_1(sy + 1)
            except:
                end = start + 380

            if start <= jd_utc < end:
                month_names = get_months_in_year(sy)
                current = start
                for i, mname in enumerate(month_names):
                    purn = self._find_purnima(current + 14.77)
                    next_am = self._find_amavasya(purn + 14.77)
                    next_start = next_am + 1.0
                    if jd_utc < next_start:
                        return {
                            'saka_year': sy,
                            'month_name': mname,
                            'is_adhika': mname.startswith('Punah'),
                            'month_start_jd': current,
                            'month_index': i
                        }
                    current = next_start
                return {
                    'saka_year': sy,
                    'month_name': month_names[-1],
                    'is_adhika': month_names[-1].startswith('Punah'),
                    'month_start_jd': current,
                    'month_index': len(month_names)-1
                }

        raise ValueError(f"Tidak dapat menentukan tahun Saka untuk JD {jd_utc:.6f}")