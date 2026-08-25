#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
precession_nutation.py – IAU 2006/2000A_R06 precession‑nutation model

Implementasi lengkap mengikuti IERS Conventions 2010.
Mendukung perhitungan GMST (mean) dan GAST (apparent).

Fungsi utama:
    - compute_nutation(t, nut_long_data, nut_obl_data, mean)
    - compute_cip_xy(t, x_data, y_data)
    - compute_cio_s(t, X_arcsec, Y_arcsec, s_data)
    - compute_equation_of_origins(t, eo_data, delta_psi, eps_A, mean)
    - compute_precession_angles(t)
    - compute_era(ut1_jd)
    - compute_gst(t, ut1_jd, eo_data, nut_long_data, nut_obl_data, mean)
"""

import math
import re
import os
import numpy as np

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
EPS0 = 84381.406                 # J2000 mean obliquity (arcsec)
DAS2R = math.pi / (180.0 * 3600.0)   # arcsec → radian
R2UAS = 1.0 / DAS2R * 1e6            # radian → microarcsec
UAS2R = DAS2R * 1e-6                 # microarcsec → radian

# -----------------------------------------------------------------------------
# Fundamental arguments (lunisolar)
# -----------------------------------------------------------------------------
def fundamental_args(t: float) -> np.ndarray:
    """
    Delaunay arguments l, l', F, D, Ω (radians).
    t : Julian centuries since J2000.0 (TT).
    """
    l_deg = 134.96340251 + (1717915923.2178*t + 31.8792*t**2 + 0.051635*t**3 - 0.00024470*t**4) / 3600.0
    lp_deg = 357.52910918 + (129596581.0481*t - 0.5532*t**2 + 0.000136*t**3 - 0.00001149*t**4) / 3600.0
    F_deg = 93.27209062 + (1739527262.8478*t - 12.7512*t**2 - 0.001037*t**3 + 0.00000417*t**4) / 3600.0
    D_deg = 297.85019547 + (1602961601.2090*t - 6.3706*t**2 + 0.006593*t**3 - 0.00003169*t**4) / 3600.0
    Om_deg = 125.04455501 + (-6962890.5431*t + 7.4722*t**2 + 0.007702*t**3 - 0.00005939*t**4) / 3600.0
    return np.radians([l_deg, lp_deg, F_deg, D_deg, Om_deg])

# -----------------------------------------------------------------------------
# Planetary arguments
# -----------------------------------------------------------------------------
def planetary_args(t: float) -> np.ndarray:
    """
    Planetary mean longitudes L_Me, L_Ve, L_E, L_Ma, L_J, L_Sa, L_U, L_Ne
    and general precession p_A (radians).
    """
    L_Me = 4.402608842 + 2608.7903141574 * t
    L_Ve = 3.176146697 + 1021.3285546211 * t
    L_E  = 1.753470314 + 628.3075849991 * t
    L_Ma = 6.203480913 + 334.0612426700 * t
    L_J  = 0.599546497 + 52.9690962641 * t
    L_Sa = 0.874016757 + 21.3299104960 * t
    L_U  = 5.481293872 + 7.4781598567 * t
    L_Ne = 5.311886287 + 3.8133035638 * t
    p_A  = 0.02438175 * t + 0.00000538691 * t**2
    return np.array([L_Me, L_Ve, L_E, L_Ma, L_J, L_Sa, L_U, L_Ne, p_A])

# -----------------------------------------------------------------------------
# IERS table loader
# -----------------------------------------------------------------------------
def load_table(filename: str) -> dict:
    """
    Read an IERS table file and return a dict {j: np.ndarray(rows, columns)}
    where columns: [a_sin, a_cos, mult_l, mult_lp, mult_F, mult_D, mult_Om,
                    mult_LMe, mult_LVe, mult_LE, mult_LMa, mult_LJ, mult_LSa,
                    mult_LU, mult_LNe, mult_pA]
    """
    data = {}
    if not os.path.exists(filename):
        return data

    with open(filename, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if 'j =' in line:
            parts = line.split()
            j = int(parts[2])
            i += 1
            while i < len(lines):
                l = lines[i].strip()
                if l and not l.startswith('--') and not l.startswith('===') and not l.startswith('j ='):
                    if re.match(r'^\s*[0-9]', l):
                        break
                i += 1
            rows = []
            while i < len(lines):
                l = lines[i].strip()
                if l == '':
                    i += 1
                    continue
                if l.startswith('j =') or l.startswith('--') or l.startswith('==='):
                    break
                cols = l.split()
                if len(cols) >= 17:
                    try:
                        a_sin = float(cols[1])
                        a_cos = float(cols[2])
                        mult = [float(x) for x in cols[3:17]]
                        rows.append([a_sin, a_cos] + mult)
                    except ValueError:
                        pass
                i += 1
            if rows:
                data[j] = np.array(rows)
        else:
            i += 1
    return data

# -----------------------------------------------------------------------------
# Nutation (IAU 2000A_R06) – dapat dimatikan untuk mean
# -----------------------------------------------------------------------------
def compute_nutation(t: float, nut_long_data: dict, nut_obl_data: dict,
                     mean: bool = True) -> tuple:
    """
    Returns (Δψ, Δε) in arcseconds.
    If mean=True, returns (0,0) – useful for GMST.
    """
    if mean:
        return 0.0, 0.0

    args_lun = fundamental_args(t)
    args_pl = planetary_args(t)
    args_all = np.concatenate([args_lun, args_pl])

    dpsi = 0.0
    deps = 0.0
    for j in (0, 1):
        if j in nut_long_data:
            rows = nut_long_data[j]
            if rows.size:
                mult = rows[:, 2:17]
                arg = np.dot(mult, args_all)
                a = rows[:, 0]          # sin coefficient (A_i)
                b = rows[:, 1]          # cos coefficient (A''_i)
                dpsi += np.sum(a * np.sin(arg) + b * np.cos(arg)) * (t ** j)

        if j in nut_obl_data:
            rows = nut_obl_data[j]
            if rows.size:
                mult = rows[:, 2:17]
                arg = np.dot(mult, args_all)
                a = rows[:, 0]          # sin coefficient (B''_i)
                b = rows[:, 1]          # cos coefficient (B_i)
                deps += np.sum(a * np.sin(arg) + b * np.cos(arg)) * (t ** j)

    # microarcsec → arcsec + IAU 2006 adjustments
    dpsi = dpsi * 1e-6 + 47.78 * t * math.sin(args_lun[4]) - 8.08 * math.sin(args_lun[4])
    deps = deps * 1e-6 - 25.57 * t * math.cos(args_lun[4])
    return dpsi, deps

# -----------------------------------------------------------------------------
# CIP coordinates X, Y (arcseconds)
# -----------------------------------------------------------------------------
def compute_cip_xy(t: float, x_data: dict, y_data: dict) -> tuple:
    args_lun = fundamental_args(t)
    args_pl = planetary_args(t)
    args_all = np.concatenate([args_lun, args_pl])

    X_poly = (-16617.0 + 2004191898.0*t - 429782.9*t**2
              - 198618.34*t**3 + 7.578*t**4 + 5.9285*t**5)
    Y_poly = (-6951.0 - 25896.0*t - 22407274.7*t**2
              + 1900.59*t**3 + 1112.526*t**4 + 0.1358*t**5)

    X_ser = 0.0
    Y_ser = 0.0
    for j in range(5):
        if j in x_data:
            rows = x_data[j]
            if rows.size:
                mult = rows[:, 2:17]
                arg = np.dot(mult, args_all)
                a = rows[:, 0]
                b = rows[:, 1]
                X_ser += np.sum(a * np.sin(arg) + b * np.cos(arg)) * (t ** j)
        if j in y_data:
            rows = y_data[j]
            if rows.size:
                mult = rows[:, 2:17]
                arg = np.dot(mult, args_all)
                a = rows[:, 0]
                b = rows[:, 1]
                Y_ser += np.sum(a * np.sin(arg) + b * np.cos(arg)) * (t ** j)

    return (X_poly + X_ser) * 1e-6, (Y_poly + Y_ser) * 1e-6

# -----------------------------------------------------------------------------
# CIO locator s (microarcseconds)
# -----------------------------------------------------------------------------
def compute_cio_s(t: float, X_arcsec: float, Y_arcsec: float,
                  s_data: dict) -> float:
    args_lun = fundamental_args(t)
    args_pl = planetary_args(t)
    args_all = np.concatenate([args_lun, args_pl])

    poly = 94.0 + 3808.65*t - 122.68*t**2 - 72574.11*t**3 + 27.98*t**4 + 15.62*t**5
    ser = 0.0
    for j in range(5):
        if j in s_data:
            rows = s_data[j]
            if rows.size:
                mult = rows[:, 2:17]
                arg = np.dot(mult, args_all)
                a = rows[:, 0]
                b = rows[:, 1]
                ser += np.sum(a * np.sin(arg) + b * np.cos(arg)) * (t ** j)

    s_plus_XY2 = poly + ser
    XY2_rad = 0.5 * (X_arcsec * DAS2R) * (Y_arcsec * DAS2R)
    return s_plus_XY2 - XY2_rad * R2UAS

# -----------------------------------------------------------------------------
# Equation of the Origins (EO) – arcseconds
# -----------------------------------------------------------------------------
def compute_equation_of_origins(t: float, eo_data: dict,
                                delta_psi: float, eps_A: float,
                                mean: bool = True) -> float:
    args_lun = fundamental_args(t)
    args_pl = planetary_args(t)
    args_all = np.concatenate([args_lun, args_pl])

    # Polynomial part (arcsec) – lengkap sampai t^5
    poly = (-0.014506 - 4612.156534*t - 1.3915817*t**2
            + 0.00000044*t**3 + 0.000029956*t**4 + 0.0000000368*t**5)

    # Complementary series: Σ Ck sin(αk) (dari tab5.2e)
    comp = 0.0
    for j in (0, 1):
        if j in eo_data:
            rows = eo_data[j]
            if rows.size:
                mult = rows[:, 2:17]
                arg = np.dot(mult, args_all)
                a_sin = rows[:, 0]
                a_cos = rows[:, 1]
                comp += np.sum(a_sin * np.sin(arg) + a_cos * np.cos(arg)) * (t ** j)

    comp_arcsec = comp * 1e-6   # µas → arcsec

    if mean:
        return poly - comp_arcsec
    else:
        return poly - delta_psi * math.cos(math.radians(eps_A)) - comp_arcsec

# -----------------------------------------------------------------------------
# IAU 2006 precession angles (arcseconds)
# -----------------------------------------------------------------------------
def compute_precession_angles(t: float) -> tuple:
    psi = (5038.481507*t - 1.0790069*t**2 - 0.00114045*t**3
           + 0.000132851*t**4 - 0.0000000951*t**5)
    omega = (EPS0 - 0.025754*t + 0.0512623*t**2 - 0.00772503*t**3
             - 0.000000467*t**4 + 0.0000003337*t**5)
    eps = (EPS0 - 46.836769*t - 0.0001831*t**2 + 0.00200340*t**3
           - 0.000000576*t**4 - 0.0000000434*t**5)
    chi = (10.556403*t - 2.3814292*t**2 - 0.00121197*t**3
           + 0.000170663*t**4 - 0.0000000560*t**5)
    return psi, omega, eps, chi

# -----------------------------------------------------------------------------
# Earth Rotation Angle (radians)
# -----------------------------------------------------------------------------
def compute_era(ut1_jd: float) -> float:
    T = ut1_jd - 2451545.0
    return 2.0 * math.pi * (0.7790572732640 + 1.00273781191135448 * T)

# -----------------------------------------------------------------------------
# Greenwich Sidereal Time (radians) – mean atau apparent
# -----------------------------------------------------------------------------
def compute_gst(t: float, ut1_jd: float,
                eo_data: dict, nut_long_data: dict, nut_obl_data: dict,
                mean: bool = True) -> float:
    """
    mean=True → GMST (tanpa nutasi)
    mean=False → GAST (apparent, dengan nutasi)
    """
    dpsi, _ = compute_nutation(t, nut_long_data, nut_obl_data, mean=mean)
    _, _, eps_A, _ = compute_precession_angles(t)
    EO_arcsec = compute_equation_of_origins(t, eo_data, dpsi, eps_A, mean=mean)
    return compute_era(ut1_jd) - EO_arcsec * DAS2R

# -----------------------------------------------------------------------------
# Elementary rotation matrices (right-handed, positive = CCW)
# -----------------------------------------------------------------------------
def Rx(angle: float) -> np.ndarray:
    c = math.cos(angle); s = math.sin(angle)
    return np.array([[1.0, 0.0, 0.0],
                     [0.0,   c,   s],
                     [0.0,  -s,   c]])

def Ry(angle: float) -> np.ndarray:
    c = math.cos(angle); s = math.sin(angle)
    return np.array([[  c, 0.0,  -s],
                     [0.0, 1.0, 0.0],
                     [  s, 0.0,   c]])

def Rz(angle: float) -> np.ndarray:
    c = math.cos(angle); s = math.sin(angle)
    return np.array([[  c,   s, 0.0],
                     [ -s,   c, 0.0],
                     [0.0, 0.0, 1.0]])

# -----------------------------------------------------------------------------
# Frame bias matrix (GCRS → mean J2000 equator & equinox)
# -----------------------------------------------------------------------------
def frame_bias_matrix() -> np.ndarray:
    """Bias rotasi dari GCRS ke mean equator/equinox J2000.0."""
    # IAU 2000A bias (IERS 2010)
    xi0   = -0.041775 * DAS2R          # arcsec → rad
    eta0  = -0.0068192 * DAS2R
    dalpha0 = -0.0146 * DAS2R
    return Rx(-eta0) @ Ry(xi0) @ Rz(-dalpha0)

# -----------------------------------------------------------------------------
# Build BPN matrix (classical equinox-based)
# -----------------------------------------------------------------------------
def build_bpn_matrix(t: float, dpsi: float, deps: float) -> np.ndarray:
    """
    Matriks bias × precession × nutation (GCRS → true equator & equinox).
    t         : Julian centuries since J2000.0 (TT)
    dpsi, deps: nutation in longitude and obliquity (radians)
    """
    # Precession angles (arcsec → rad)
    psiA, omegaA, epsA, chiA = compute_precession_angles(t)
    psiA_r = psiA * DAS2R
    omegaA_r = omegaA * DAS2R
    epsA_r = epsA * DAS2R
    chiA_r = chiA * DAS2R
    eps0 = EPS0 * DAS2R

    B = frame_bias_matrix()
    P = Rz(-chiA_r) @ Rx(omegaA_r) @ Rz(-psiA_r) @ Rx(eps0)
    N = Rx(-epsA_r) @ Rz(-dpsi) @ Rx(epsA_r + deps)
    return N @ P @ B

# -----------------------------------------------------------------------------
# Transformasi GCRS ↔ true equator
# -----------------------------------------------------------------------------
def gcrs_to_true(vec: np.ndarray, t: float, dpsi: float, deps: float) -> np.ndarray:
    return build_bpn_matrix(t, dpsi, deps) @ vec

def true_to_gcrs(vec: np.ndarray, t: float, dpsi: float, deps: float) -> np.ndarray:
    return build_bpn_matrix(t, dpsi, deps).T @ vec

# -----------------------------------------------------------------------------
# Build Q matrix (CIP–CIO based)
# -----------------------------------------------------------------------------
def build_q_matrix(X: float, Y: float, s: float) -> np.ndarray:
    """GCRS → CIRS (tanpa Earth rotation)"""
    Z = math.sqrt(max(0.0, 1.0 - X*X - Y*Y))
    a = 1.0 / (1.0 + Z)
    Qcore = np.array([[1.0 - a*X*X,    -a*X*Y,      X],
                      [   -a*X*Y,   1.0 - a*Y*Y,    Y],
                      [       -X,          -Y,      Z]])
    return Qcore @ Rz(s)

def build_q_inverse(X: float, Y: float, s: float) -> np.ndarray:
    return build_q_matrix(X, Y, s).T

# -----------------------------------------------------------------------------
# Transformasi GCRS ↔ CIRS
# -----------------------------------------------------------------------------
def gcrs_to_cirs(vec: np.ndarray, X: float, Y: float, s: float) -> np.ndarray:
    return build_q_matrix(X, Y, s) @ vec

def cirs_to_gcrs(vec: np.ndarray, X: float, Y: float, s: float) -> np.ndarray:
    return build_q_matrix(X, Y, s).T @ vec

# =============================================================================
# Self‑test: menampilkan GMST dan GAST
# =============================================================================
if __name__ == "__main__":
    # Load tables
    nut_long = load_table('tab5.3a.txt')
    nut_obl = load_table('tab5.3b.txt')
    x_tab = load_table('tab5.2a.txt')
    y_tab = load_table('tab5.2b.txt')
    s_tab = load_table('tab5.2d.txt')
    eo_tab = load_table('tab5.2e.txt')

    # Contoh epoch: 2006-01-15 21:24:37 UTC → TT
    jd_tt = 2455374.392855
    t_val = (jd_tt - 2451545.0) / 36525.0
    ut1_jd = jd_tt + 0.3341 / 86400.0

    print("=== IERS table loaded ===")
    def nterms(d, j):
        return d[j].shape[0] if j in d and d[j].size else 0
    print(f"Nut. long.  : j=0: {nterms(nut_long,0):4d}, j=1: {nterms(nut_long,1):4d}")
    print(f"Nut. obl.   : j=0: {nterms(nut_obl,0):4d}, j=1: {nterms(nut_obl,1):4d}")
    print(f"X series    : j=0: {nterms(x_tab,0):4d}, j=1: {nterms(x_tab,1):4d}, "
          f"j=2: {nterms(x_tab,2):4d}, j=3: {nterms(x_tab,3):4d}, j=4: {nterms(x_tab,4):4d}")
    print(f"Y series    : j=0: {nterms(y_tab,0):4d}, j=1: {nterms(y_tab,1):4d}, "
          f"j=2: {nterms(y_tab,2):4d}, j=3: {nterms(y_tab,3):4d}, j=4: {nterms(y_tab,4):4d}")
    print(f"s series    : j=0: {nterms(s_tab,0):4d}, j=1: {nterms(s_tab,1):4d}, "
          f"j=2: {nterms(s_tab,2):4d}, j=3: {nterms(s_tab,3):4d}, j=4: {nterms(s_tab,4):4d}")
    print(f"EO series   : j=0: {nterms(eo_tab,0):4d}, j=1: {nterms(eo_tab,1):4d}")
    print()

    # ------------------------------------------------------------------------
    # 1. GMST (mean, nutasi = 0)
    # ------------------------------------------------------------------------
    mean_mode = True
    dpsi, deps = compute_nutation(t_val, nut_long, nut_obl, mean=mean_mode)
    psi_A, omega_A, eps_A, chi_A = compute_precession_angles(t_val)
    X, Y = compute_cip_xy(t_val, x_tab, y_tab)
    s_val = compute_cio_s(t_val, X, Y, s_tab)
    EO = compute_equation_of_origins(t_val, eo_tab, dpsi, eps_A, mean=mean_mode)
    ERA = compute_era(ut1_jd)
    GST_mean = compute_gst(t_val, ut1_jd, eo_tab, nut_long, nut_obl, mean=True)

    print("=== GREENWICH MEAN SIDEREAL TIME (GMST) ===")
    print(f"t           = {t_val:.6f}")
    print(f"Δψ          = {dpsi:.6f} arcsec  (mean mode)")
    print(f"Δε          = {deps:.6f} arcsec")
    print(f"ψ_A         = {psi_A:.6f} arcsec")
    print(f"ω_A         = {omega_A:.6f} arcsec")
    print(f"ε_A         = {eps_A:.6f} arcsec")
    print(f"χ_A         = {chi_A:.6f} arcsec")
    print(f"X           = {X:.6f} arcsec")
    print(f"Y           = {Y:.6f} arcsec")
    print(f"s           = {s_val:.6f} microarcsec")
    print(f"EO          = {EO:.6f} arcsec")
    print(f"ERA         = {ERA:.12f} rad")
    print(f"GMST (rad)  = {GST_mean:.12f} rad")
    print()

    # ------------------------------------------------------------------------
    # 2. GAST (apparent, dengan nutasi)
    # ------------------------------------------------------------------------
    mean_mode = False
    dpsi_app, deps_app = compute_nutation(t_val, nut_long, nut_obl, mean=mean_mode)
    EO_app = compute_equation_of_origins(t_val, eo_tab, dpsi_app, eps_A, mean=mean_mode)
    GST_app = compute_gst(t_val, ut1_jd, eo_tab, nut_long, nut_obl, mean=False)

    print("=== GREENWICH APPARENT SIDEREAL TIME (GAST) ===")
    print(f"Δψ (apparent) = {dpsi_app:.6f} arcsec")
    print(f"Δε (apparent) = {deps_app:.6f} arcsec")
    print(f"EO (apparent) = {EO_app:.6f} arcsec")
    print(f"ERA           = {ERA:.12f} rad")
    print(f"GAST (rad)    = {GST_app:.12f} rad")
    print()

    print("Perbedaan GAST − GMST (persamaan equinox):")
    print(f"ΔGST = {(GST_app - GST_mean):.12f} rad  = {(GST_app - GST_mean) * 3600 * 180 / math.pi:.6f} arcsec")