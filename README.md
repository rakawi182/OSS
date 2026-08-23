OSS — Oldjavanese Saka Stellaris

https://img.shields.io/badge/License-Non--Commercial-red.svg
https://img.shields.io/badge/Research-Only-blue.svg
https://img.shields.io/badge/Education-Use-green.svg
https://img.shields.io/badge/python-3.8+-blue.svg
https://img.shields.io/badge/IMCCE-VSOP87-ELP82B-purple.svg

OSS — Oldjavanese Saka Stellaris — A toolkit for archaeoastronomical analysis of ancient Javanese inscriptions, calendars, and temple alignments, using high‑precision ephemerides (VSOP87D & ELP2000‑82B).

---

📖 Overview

OSS is a Python‑based archaeoastronomy suite developed for the study of Old Javanese astronomical records, Śaka‑dated inscriptions, and temple orientations. It combines:

· VSOP87D (Bretagnon & Francou, 1988) for the Earth’s heliocentric spherical coordinates
· ELP2000‑82B (Chapront & Chapront, 1983, 1988) for the Moon’s geocentric rectangular coordinates
· Wuku 210‑day cycle and the full Old Javanese calendar system (Pancawara, Saptawara, Sadwara)
· Ω‑STHAPATI engine for converting Śaka inscriptions to Julian/Gregorian dates using a 4‑component scoring system
· Archaeoastronomical analysis – solar/lunar positions, eclipses, standstills, and temple horizon alignments

The code is calibrated for Jolotundo (Patirtan Jolotundo, Mount Penanggungan, East Java), a site of significant archaeological interest.

---

🚀 Core Features

Ephemerides (Earth–Moon System)

Module Description Output Reference
VSOP87D.py Earth heliocentric spherical coordinates Longitude, latitude, radius (rad & AU) VSOP87D (Bretagnon & Francou, 1988)
ELP82B.py Lunar geocentric rectangular coordinates Cartesian X, Y, Z (km) ELP2000‑82B (Chapront & Chapront, 1983, 1988)
solar_lunar_events.py Solar/lunar event calculator Equinoxes, solstices, new/full moons, perigee/apogee, eclipses, standstills Based on VSOP87D + ELP82B

Old Javanese Calendar & Epigraphy

Module Description
wuku_system.py Infinite‑range Wuku 210‑day cycle with KA (Kali Ahargana) conversion
SPICA_v18.py / IJCC_v889.py Śaka inscription dating engine (Ω‑STHAPATI v301.4) with weighted scoring (Tahun, Bulan, Wara, Wuku)
Damais_DB.py Database of 112 Damais inscriptions with full astronomical metadata
Old_Java_Astronomy.py Complete panchanga, Vedic time, Grahacara Astha, Dewata, Mandala, planetary positions

Integrated Interface

Module Description
main.py Unified interactive menu combining all components
display.py Formatted terminal output utilities
quick_test_ijcc.py Batch testing of Damais inscriptions (10 per batch)

---

📂 Repository Structure

```
OSS/
├── JRC_Ephemeris.py           # Unified ephemeris engine (VSOP87D + ELP82B)
├── VSOP87D.py                 # VSOP87D Earth spherical coordinates
├── ELP82B.py                  # ELP2000‑82B lunar ephemeris
├── solar_lunar_events.py      # Solar/lunar event calculator
│
├── wuku_system.py             # Wuku 210‑day cycle engine
├── SPICA_v18.py               # Ω‑STHAPATI inscription dating engine
├── IJCC_v889.py               # IJCC v889 (SPICA v301.4)
├── Damais_DB.py               # 112 Damais inscriptions database
│
├── Old_Java_Astronomy.py      # Full Old Javanese astronomy system
├── main.py                    # Unified interactive menu
├── display.py                 # Formatted display utilities
├── quick_test_ijcc.py         # Batch testing for Damais inscriptions
│
├── Data files
│   ├── VSOP87D_ear.txt        # VSOP87D Earth series
│   ├── ELP01.txt – ELP36.txt  # ELP2000‑82B series (36 files)
│   └── Damais_DB.py           # (already listed above)
│
└── README.md                  # This file
```

⚠️ All data files must be present in the same directory as the corresponding Python modules, or adjust the file paths accordingly.

---

🔧 Installation

```bash
git clone https://github.com/yourusername/OSS.git
cd OSS
```

Requirements: Python 3.8+, NumPy (for JRC_Ephemeris.py and ELP_MPP02_full.py if used). No other external dependencies.

---

💻 Usage

1. Quick Ephemeris

```python
from JRC_Ephemeris import JolotundoArchaeoastronomySystem
jrc = JolotundoArchaeoastronomySystem()
ephem = jrc.get_complete_ephemeris(use_current_time=True)
from JRC_Ephemeris import display_ephemeris
display_ephemeris(ephem)
```

2. Wuku & Wara

```python
from wuku_system import WukuMechanicalEngine
engine = WukuMechanicalEngine()
info = engine.get_wuku_by_date(2024, 12, 25)
print(f"Wuku: {info['wuku_name']} (#{info['wuku_number']})")
```

3. Śaka Inscription Dating (Ω‑STHAPATI)

```python
from SPICA_v18 import ΩSthapatiSystem
system = ΩSthapatiSystem()
inscription = {'saka_year': 822, 'masa': 'Pausa', 'tithi': 8, 'paksa': 'Sukla', 'wara_string': 'Haryang-Kaliwon-Wrhaspati'}
results = system.convert_prasasti(inscription, verbose=True)
```

4. Interactive Menu

```bash
python main.py
```

---

✅ Validation

All core modules include validation routines:

Module Validation Reference
VSOP87D.py Compare with vsop87_chk.txt 10 JD epochs
ELP82B.py Compare with Table H values 5 JD epochs
JRC_Ephemeris.py JPL Horizons comparison (Sun & Moon) 2024-12-25
llib04.py (if used) LLIB04 reference 20 JD epochs

Archaeoastronomy tolerances:

· Position (RA/Dec): ≤ 10 arcsec
· Azimuth/Altitude: ≤ 1 arcmin
· Wuku/Wara: exact match
· Śaka dating: ±1 day (high confidence)

---

📚 References

· VSOP87: Bretagnon, P. & Francou, G. (1988). Astron. Astrophys. 202, 309.
· ELP2000‑82B: Chapront‑Touzé, M. & Chapront, J. (1983, 1988). A&A 124, 50; A&A 190, 342.
· Damais: Damais, L.-C. (1952). Études d'épigraphie indonésienne.
· Proudfoot: Proudfoot, I. (2006). Old Javanese Calendrical Systems.
· Gomperts: Gomperts, A. (2013). Astronomical Dating of Old Javanese Inscriptions.

---

📝 License & Terms

```
NON‑COMMERCIAL USE ONLY.  
This software is provided for educational and research purposes.  
Commercial use is strictly prohibited without explicit permission from the copyright holders (IMCCE, Observatoire de Paris, and the Jolotundo Research Consortium).  
All data and algorithms are provided "as‑is" with no warranty.
```

Third‑Party Attribution

· VSOP87 and ELP series are from the IMCCE (Paris Observatory).
· Used with permission for non‑commercial research and education.

---

🏛️ About the Jolotundo Research Consortium

The Jolotundo Research Consortium (JRC) is an independent, non‑institutional research collective for archaeoastronomy and epigraphy in Indonesia. It is not a registered legal entity; it serves as a scholarly identity for the developers of this software.

---

👥 Author

Rakawi
Jolotundo Research Consortium

---

🤝 Contributing

Contributions that improve accuracy, fix bugs, add documentation, or extend validation are welcome. This repository focuses on the Earth–Moon system and Old Javanese astronomy; full planetary implementations are out of scope.

---

⚠️ Disclaimer

```
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
```

---

🌟 Acknowledgements

· IMCCE / Paris Observatory – for VSOP87 and ELP series
· Dr. L.-C. Damais – for foundational epigraphic studies
· Dr. I. Proudfoot – for Old Javanese calendrical research
· JPL/NASA – for DE ephemerides used in validation

---

Last updated: 2026‑08‑24
OSS — Oldjavanese Saka Stellaris
Jolotundo Research Consortium
