"""Thread dimension tables used by the bolted joint tool.

Columns: designation, standard, d (major, mm), P (pitch, mm), d2 (pitch dia, mm),
d3 (minor dia used for the tensile stress area, mm).

* ISO metric (ISO 261 sizes, ISO 724 basic profile):
      d2 = d - 0.649519 P,  d3 = d - 1.226869 P
  -> pi/4 ((d2+d3)/2)^2 is exactly the ISO 898-1 tensile stress area As.
* UNC / UNF (ASME B1.1 basic sizes):
      d2 = d - 0.649519 P,  d3 = d - 1.299038 P
  d3 is the *stress-area equivalent* minor diameter: pi/4 ((d2+d3)/2)^2 equals the
  ASME B1.1 tensile stress area pi/4 (d - 0.9743 P)^2.
* UNJF (Class 3A): minimum pitch and minimum minor diameter of the external thread
  (conservative), major diameter = basic size.

All values are basic/minimum values. For a specific tolerance class enter the actual
minimum diameters in the override cells of the tool.
"""

INCH = 25.4

METRIC_COARSE = [
    (1.6, 0.35), (2, 0.4), (2.5, 0.45), (3, 0.5), (4, 0.7), (5, 0.8), (6, 1.0),
    (8, 1.25), (10, 1.5), (12, 1.75), (14, 2.0), (16, 2.0), (18, 2.5), (20, 2.5),
    (22, 2.5), (24, 3.0), (27, 3.0), (30, 3.5), (33, 3.5), (36, 4.0), (39, 4.0),
    (42, 4.5), (45, 4.5), (48, 5.0), (52, 5.0), (56, 5.5), (60, 5.5), (64, 6.0),
]
METRIC_FINE = [
    (8, 1.0), (10, 1.25), (10, 1.0), (12, 1.5), (12, 1.25), (14, 1.5), (16, 1.5),
    (18, 1.5), (20, 1.5), (22, 1.5), (24, 2.0), (27, 2.0), (30, 2.0), (33, 2.0),
    (36, 3.0), (39, 3.0), (42, 3.0), (45, 3.0), (48, 3.0),
]
# (label, basic major diameter in inch, threads per inch)
UNC = [
    ("#2-56", 0.086, 56), ("#4-40", 0.112, 40), ("#5-40", 0.125, 40), ("#6-32", 0.138, 32),
    ("#8-32", 0.164, 32), ("#10-24", 0.190, 24), ("1/4-20", 0.25, 20), ("5/16-18", 0.3125, 18),
    ("3/8-16", 0.375, 16), ("7/16-14", 0.4375, 14), ("1/2-13", 0.5, 13), ("9/16-12", 0.5625, 12),
    ("5/8-11", 0.625, 11), ("3/4-10", 0.75, 10), ("7/8-9", 0.875, 9), ("1-8", 1.0, 8),
    ("1 1/8-7", 1.125, 7), ("1 1/4-7", 1.25, 7), ("1 3/8-6", 1.375, 6), ("1 1/2-6", 1.5, 6),
]
UNF = [
    ("#0-80", 0.060, 80), ("#2-64", 0.086, 64), ("#4-48", 0.112, 48), ("#6-40", 0.138, 40),
    ("#8-36", 0.164, 36), ("#10-32", 0.190, 32), ("1/4-28", 0.25, 28), ("5/16-24", 0.3125, 24),
    ("3/8-24", 0.375, 24), ("7/16-20", 0.4375, 20), ("1/2-20", 0.5, 20), ("9/16-18", 0.5625, 18),
    ("5/8-18", 0.625, 18), ("3/4-16", 0.75, 16), ("7/8-14", 0.875, 14), ("1-12", 1.0, 12),
    ("1 1/8-12", 1.125, 12), ("1 1/4-12", 1.25, 12), ("1 3/8-12", 1.375, 12), ("1 1/2-12", 1.5, 12),
]
# (label, basic size inch, tpi, pitch dia min mm, minor dia min mm)  - Class 3A external
UNJF = [
    ("#0-80", 0.060, 80, 1.29, 1.10), ("#2-64", 0.086, 64, 1.89, 1.67),
    ("#4-48", 0.112, 48, 2.46, 2.16), ("#6-40", 0.138, 40, 3.04, 2.68),
    ("#8-36", 0.164, 36, 3.66, 3.26), ("#10-32", 0.190, 32, 4.25, 3.80),
    ("1/4-28", 0.25, 28, 5.70, 5.18), ("5/16-24", 0.3125, 24, 7.18, 6.58),
    ("3/8-24", 0.375, 24, 8.76, 8.16), ("7/16-20", 0.4375, 20, 10.21, 9.49),
    ("1/2-20", 0.5, 20, 11.79, 11.07), ("9/16-18", 0.5625, 18, 13.28, 12.49),
    ("5/8-18", 0.625, 18, 14.87, 14.07), ("3/4-16", 0.75, 16, 17.92, 17.02),
    ("7/8-14", 0.875, 14, 20.94, 19.92), ("1-12", 1.0, 12, 23.91, 22.72),
    ("1 1/8-12", 1.125, 12, 27.09, 25.89), ("1 1/4-12", 1.25, 12, 30.26, 29.06),
    ("1 3/8-12", 1.375, 12, 33.43, 32.23), ("1 1/2-12", 1.5, 12, 36.60, 35.41),
]


def _fmt(x):
    return ("%g" % x)


def thread_table():
    """Return list of rows (designation, standard, d, P, d2, d3)."""
    rows = []
    for d, p in METRIC_COARSE:
        rows.append((f"M{_fmt(d)}x{_fmt(p)}", "ISO metric coarse", d, p,
                     round(d - 0.649519 * p, 4), round(d - 1.226869 * p, 4)))
    for d, p in METRIC_FINE:
        rows.append((f"M{_fmt(d)}x{_fmt(p)} fine", "ISO metric fine", d, p,
                     round(d - 0.649519 * p, 4), round(d - 1.226869 * p, 4)))
    for lab, din, tpi in UNC:
        d, p = din * INCH, INCH / tpi
        rows.append((f"{lab} UNC", "UNC (ASME B1.1)", round(d, 4), round(p, 4),
                     round(d - 0.649519 * p, 4), round(d - 1.299038 * p, 4)))
    for lab, din, tpi in UNF:
        d, p = din * INCH, INCH / tpi
        rows.append((f"{lab} UNF", "UNF (ASME B1.1)", round(d, 4), round(p, 4),
                     round(d - 0.649519 * p, 4), round(d - 1.299038 * p, 4)))
    for lab, din, tpi, d2, d3 in UNJF:
        rows.append((f"{lab} UNJF", "UNJF 3A (min)", round(din * INCH, 4), round(INCH / tpi, 4), d2, d3))
    return rows


def lookup(designation):
    for row in thread_table():
        if row[0] == designation:
            return dict(d=row[2], P=row[3], d2=row[4], d3=row[5])
    raise KeyError(designation)
