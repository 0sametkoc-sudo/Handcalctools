"""HSB 26101-01 (Issue E, 2006) static strength of metallic double-shear lugs - reference implementation.

Independent Python implementation of the method used in excel/HSB_Clevis_Tool.xlsx.
Units: N, mm, MPa.

One double-shear joint = female lug (two prongs) + male lug + bolt. Each lug is checked for
Case 1 (lug ultimate), Case 2 (net-section yield), Case 3 (bearing yield) and section 3.3
(bushing bearing). HSB 3.4: the lowest value governs. The bolt is not covered (HSB 26101-02).
"""
from __future__ import annotations

from dataclasses import dataclass
from math import log10
from typing import Optional


@dataclass
class Lug:
    d: float            # hole diameter in the lug (bushing outer diameter if a bushing is fitted)
    r: float            # outer radius of the lug head
    h: float            # eccentricity (h = r for a concentric lug)
    e: float            # edge distance in load direction, hole centre to edge
    w: float            # smaller edge distance perpendicular to the load (half width)
    t: float            # thickness (one prong for the female lug)
    Rm: float           # tensile ultimate strength
    Rp02: float         # tensile yield strength
    Rbry15: float       # bearing yield strength at e/d = 1.5
    Rbry20: float       # bearing yield strength at e/d = 2.0
    beta: float = 0.0   # taper angle, deg (0..45)
    phi: float = 0.0    # load angle, deg (0..90)
    bushing: bool = False
    da: Optional[float] = None    # bolt diameter (= bushing bore) for section 3.3
    Rc02: Optional[float] = None  # bushing compressive yield strength
    name: str = ""


def ktb1_straight(x, phi):
    k0 = 2.75 * (x - 1) ** -0.675
    k90 = 9.33 * x ** -1.667 if x <= 1.723 else 7.78 * x ** -1.333
    return k0 + phi / 90 * (k90 - k0), k0, k90


def ktb1_tapered(x, phi):
    return 2.417 * (1 + 0.00633 * phi - 0.0000815 * phi ** 2) * (x - 1) ** -0.63


def H_factor(hr, phi):
    H0 = hr ** -0.916 + 0.284 * log10(hr)
    H45 = hr ** -1.177 + 1.737 * log10(hr)
    H90 = hr ** -0.495 + 0.715 * log10(hr)
    if phi <= 45:
        return H0 + phi / 45 * (H45 - H0)
    return H45 + (phi - 45) / 45 * (H90 - H45)


def rbry(ed, R15, R20):
    if ed <= 1.5:
        return R15 * (ed - 0.5)
    if ed <= 2.0:
        return R15 + 2 * (ed - 1.5) * (R20 - R15)
    return R20


def lug(L: Lug, j: float) -> dict:
    x = 2 * L.r / L.d
    hr = L.h / L.r
    ed = L.e / L.d
    k_s, k0, k90 = ktb1_straight(x, L.phi)
    k_t = ktb1_tapered(x, L.phi)
    if L.beta <= 0:
        k1 = k_s
    elif L.beta >= 45:
        k1 = k_t
    else:
        k1 = k_s + L.beta / 45 * (k_t - k_s)
    H = H_factor(hr, L.phi)
    Ktb = H * k1
    KBR = 7.502 * (Ktb + 1.125) ** -1.637
    F_Lu = 0.84 * KBR * L.d * L.t * L.Rm
    F_Ly1 = 2 * j * (L.w - L.d / 2) * L.t * L.Rp02
    ratio = F_Lu / (L.d * L.t * L.Rm)
    C = 1.1 if ratio <= 1.25 else 1.379 - 0.223 * ratio
    F_Ly2 = j * C * (L.Rp02 / L.Rm) * F_Lu
    F_Ly = min(F_Ly1, F_Ly2)
    Rb = rbry(ed, L.Rbry15, L.Rbry20)
    F_Lybr = j * L.d * L.t * Rb
    F_B = 1.85 * j * L.da * L.t * L.Rc02 if L.bushing else None
    caps = {"case1": F_Lu, "case2": F_Ly, "case3": F_Lybr}
    if F_B is not None:
        caps["bushing"] = F_B
    gov = min(caps, key=caps.get)
    return dict(x=x, hr=hr, ed=ed, Ktb1_0=k0, Ktb1_90=k90, Ktb1_straight=k_s, Ktb1_tapered=k_t, Ktb1=k1, H=H,
                Ktb=Ktb, KBR=KBR, F_Lu=F_Lu, F_Ly1=F_Ly1, ratio=ratio, C=C, F_Ly2=F_Ly2, F_Ly=F_Ly, Rbry=Rb,
                F_Lybr=F_Lybr, F_B=F_B, F_cap=caps[gov], governing=gov)


def joint(female: Lug, male: Lug, P_limit: float, j: float = 1.5, FF: float = 1.0, share: float = 0.5) -> dict:
    """Female lug = one prong carrying share*P; male lug carries P. RF = F / (j FF P_lug)."""
    rf_f = lug(female, j)
    rf_m = lug(male, j)
    out = {"female": rf_f, "male": rf_m, "modes": {}}
    for tag, res, P in (("F", rf_f, share * P_limit), ("M", rf_m, P_limit)):
        Pu = j * FF * P
        for case in ("case1", "case2", "case3", "bushing"):
            F = res["F_Lu"] if case == "case1" else res["F_Ly"] if case == "case2" else \
                res["F_Lybr"] if case == "case3" else res["F_B"]
            if F is None:
                out["modes"][f"{tag}-{case}"] = (None, "N/A")
            else:
                r = F / Pu
                out["modes"][f"{tag}-{case}"] = (r, "PASS" if r >= 1 else "FAIL")
    vals = [(v[0], k) for k, v in out["modes"].items() if v[0] is not None]
    out["RF_gov"], out["mode_gov"] = min(vals)
    # joint ultimate capability in terms of the joint load P (ultimate, incl. FF)
    out["P_joint_cap"] = min(rf_f["F_cap"] / share, rf_m["F_cap"]) / FF
    return out
