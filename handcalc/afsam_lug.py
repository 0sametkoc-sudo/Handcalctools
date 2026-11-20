"""AFSAM (Air Force Stress Analysis Manual, 1986) Section 9 lug analysis - reference implementation.

Independent Python implementation of excel/AFSAM_Lug_Tool.xlsx. Units: N, mm, MPa.
Chart coefficients are read automatically from the digitized figures in handcalc/afsam_charts.py,
or can be overridden with a hand-read value.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, radians, sin, sqrt
from typing import Optional

import numpy as np

from handcalc import afsam_charts as ch

R1304 = 1.304   # = 1.5 / 1.15, ultimate / yield factor ratio built into AFSAM


# ----------------------------------------------------------------------------- chart lookups
def _lin(x, xs, ys):
    """Linear interpolation on an equally spaced grid, clamped to the ends (as the Excel formulas do)."""
    xs = np.asarray(xs, float)
    ys = np.asarray(ys, float)
    return float(np.interp(min(max(x, xs[0]), xs[-1]), xs, ys))


def k_fig9_2(ed):
    return _lin(ed, ch.FIG9_2_ED, ch.FIG9_2_K)


def k_fig9_3(ed, Dt, cutoff="NONE"):
    """Fig 9-3 is entered with the hole-centre-to-edge distance over D (e/D in AFSAM notation)."""
    dts = ch.FIG9_3_DT
    Dt = min(max(Dt, dts[0]), dts[-1])
    vals = [_lin(ed, ch.FIG9_3_AD, ch.FIG9_3_K[d]) for d in dts]
    k = float(np.interp(Dt, dts, vals))
    if cutoff in ("A", "B"):
        tbl = ch.FIG9_3_CUT_A if cutoff == "A" else ch.FIG9_3_CUT_B
        xs = np.asarray(ch.FIG9_3_AD)
        i = int(np.clip(round((min(max(ed, xs[0]), xs[-1]) - xs[0]) / 0.05), 0, len(xs) - 1))
        # cut-off defined from its start; interpolate on defined points
        pts = [(x, v) for x, v in zip(xs, tbl) if v is not None]
        if pts and ed >= pts[0][0]:
            c = float(np.interp(min(ed, xs[-1]), [p[0] for p in pts], [p[1] for p in pts]))
            k = min(k, c)
    return k


def kn_fig9_4(Dw, fy_fu, q):
    panels = ch.FIG9_4_FTY_FTU
    fr = min(max(fy_fu, panels[0]), panels[-1])
    q = min(max(q, ch.FIG9_4_Q[0]), ch.FIG9_4_Q[-1])
    pv = []
    for p in panels:
        vals = [_lin(Dw, ch.FIG9_4_DW, ch.FIG9_4_KN[p][qq]) for qq in ch.FIG9_4_Q]
        pv.append(float(np.interp(q, ch.FIG9_4_Q, vals)))
    return float(np.interp(fr, panels, pv))


def k_fig9_8(havD):
    return _lin(havD, ch.FIG9_8_HAVD, ch.FIG9_8_KTRU), _lin(havD, ch.FIG9_8_HAVD, ch.FIG9_8_KTRY)


# ----------------------------------------------------------------------------- one lug, axial load
@dataclass
class AxialLug:
    D: float          # hole diameter (bushing OD if bushed)
    e: float          # hole centre to lug edge, along the load
    w: float          # lug width (full width across the net section)
    t: float
    Ftux: float
    Ftyx: float
    E: float = 70000.0
    eu: float = 0.10
    Fcy_B: Optional[float] = None    # bushing compressive yield (None = no bushing)
    K: Optional[float] = None        # override (None = automatic)
    Kn: Optional[float] = None       # override
    cutoff: str = "NONE"             # Fig 9-3 cut-off curve A / B
    thick_al_cap: bool = False       # Fig 9-3 note: K <= 2.0 for >= 0.5 in aluminium plate/bar/billet
    B_ratio: float = 1.0             # AFSAM 9.15 knockdown B/B0.05 (1.0 if eu >= 5 %)
    Fbru_mat: Optional[float] = None  # material bearing allowables at e/D = 2 (optional caps)
    Fbry_mat: Optional[float] = None


def axial_lug(L: AxialLug, Dp: float) -> dict:
    a = L.e - L.D / 2
    ed, aD, Dt, Dw = L.e / L.D, a / L.D, L.D / L.t, L.D / L.w
    fig = "9-2" if Dt <= 5 else "9-3"
    if L.K is not None:
        K = L.K
    elif fig == "9-2":
        K = k_fig9_2(ed)
    else:
        K = k_fig9_3(ed, Dt, L.cutoff)
    if fig == "9-3" and L.thick_al_cap:
        K = min(K, 2.0)
    # Fig 9-2: K a t F for e/D < 1.5 (Eq 9-1a/9-2a); Fig 9-3: K D t F (bearing efficiency factor)
    factor = aD if (fig == "9-2" and ed < 1.5) else 1.0
    Fbru = K * factor * L.Ftux * L.B_ratio
    Fbry = K * factor * L.Ftyx * L.B_ratio
    if L.Fbru_mat:
        Fbru = min(Fbru, L.Fbru_mat)
    if L.Fbry_mat:
        Fbry = min(Fbry, L.Fbry_mat)
    Pbru = Fbru * L.D * L.t if L.Ftux <= R1304 * L.Ftyx else R1304 * Fbry * L.D * L.t
    q = L.Ftux / (L.E * L.eu)
    Kn = L.Kn if L.Kn is not None else kn_fig9_4(Dw, L.Ftyx / L.Ftux, q)
    Fnu, Fny = Kn * L.Ftux, Kn * L.Ftyx
    Pnu = Fnu * (L.w - L.D) * L.t if L.Ftux <= R1304 * L.Ftyx else R1304 * Fny * (L.w - L.D) * L.t
    PuL = min(Pbru, Pnu)
    PuB = R1304 * L.Fcy_B * Dp * L.t if L.Fcy_B else None
    PuLB = min(PuL, PuB) if PuB is not None else PuL
    return dict(a=a, ed=ed, aD=aD, Dt=Dt, Dw=Dw, fig=fig, K=K, factor=factor, Fbru=Fbru, Fbry=Fbry, Pbru=Pbru,
                q=q, Kn=Kn, Fnu=Fnu, Fny=Fny, Pnu=Pnu, PuL=PuL, PuB=PuB, PuLB=PuLB)


# ----------------------------------------------------------------------------- double shear joint 9.3 / 9.4
@dataclass
class DoubleShearJoint:
    outer: AxialLug
    inner: AxialLug
    Dp: float
    Fsu_P: float
    Ftu_P: float
    Di: float = 0.0
    kb_P: float = 1.56
    g: float = 0.0
    Ftu_T1: Optional[float] = None
    wT1: Optional[float] = None
    Ftu_T2: Optional[float] = None
    wT2: Optional[float] = None
    kb_T: float = 1.4
    variant: int = 1
    P_limit: float = 0.0
    UF: float = 1.5
    FF: float = 1.15


def double_shear(J: DoubleShearJoint) -> dict:
    o, i = axial_lug(J.outer, J.Dp), axial_lug(J.inner, J.Dp)
    t1, t2 = J.outer.t, J.inner.t
    P1, P2 = o["PuLB"], i["PuLB"]
    PuLB = min(2 * P1, P2)
    Pus = 1.571 * (J.Dp ** 2 - J.Di ** 2) * J.Fsu_P
    arm = t1 / 2 + t2 / 4 + J.g
    S = (J.Dp ** 4 - J.Di ** 4) / J.Dp
    Mu = 0.0982 * J.kb_P * S * J.Ftu_P
    Pub = 0.1963 * J.kb_P * S * J.Ftu_P / arm
    crit_bending = Pub < min(PuLB, Pus)
    C = P1 * P2 / (P1 * t2 + P2 * t1)
    Pubmax = 2 * C * (sqrt((Pub / C) * arm + J.g ** 2) - J.g)
    b1 = Pubmax * t1 / (2 * P1)
    b2 = Pubmax * t2 / (2 * P2) if J.variant == 2 else Pubmax * t2 / P2
    P_all_pin = min(Pus, Pubmax) if crit_bending else min(PuLB, Pus)
    PT1 = PT2 = None
    if J.Ftu_T1 and J.wT1:
        PT1 = 2 * J.Ftu_T1 * J.wT1 * t1
        if crit_bending:
            PT1 = PT1 / (1 + (3 / J.kb_T) * (1 - b1 / t1))
    if J.Ftu_T2 and J.wT2:
        PT2 = J.Ftu_T2 * J.wT2 * t2
    PT = min([v for v in (PT1, PT2) if v is not None], default=None)
    P_all = min(P_all_pin, PT) if PT is not None else P_all_pin
    Pdu = J.P_limit * J.UF * J.FF
    rf = (lambda F: F / Pdu if (F is not None and Pdu > 0) else None)
    modes = {
        "outer_bearing": rf(2 * o["Pbru"]), "outer_net": rf(2 * o["Pnu"]),
        "outer_bushing": rf(2 * o["PuB"]) if o["PuB"] else None,
        "inner_bearing": rf(i["Pbru"]), "inner_net": rf(i["Pnu"]),
        "inner_bushing": rf(i["PuB"]) if i["PuB"] else None,
        "pin_shear": rf(Pus), "pin_bending": rf(Pubmax if crit_bending else Pub),
        "tangs": rf(PT) if PT is not None else None,
    }
    return dict(outer=o, inner=i, PuLB=PuLB, Pus=Pus, arm=arm, Mu=Mu, Pub=Pub, crit_bending=crit_bending, C=C,
                Pubmax=Pubmax, b1=b1, b2=b2, PT1=PT1, PT2=PT2, PT=PT, P_all=P_all, Pdu=Pdu, modes=modes,
                RF_joint=rf(P_all))


# ----------------------------------------------------------------------------- single shear 9.5
def single_shear(L: AxialLug, Dp, Fsu_P, Ftu_P, P_limit, M_limit, kb_L=1.4, kb_P=1.56, Di=0.0, UF=1.5, FF=1.15):
    r = axial_lug(L, Dp)
    P, M = P_limit * UF * FF, M_limit * UF * FF
    D, t = L.D, L.t
    s_br = P / (D * t) + 6 * M / (kb_L * D * t ** 2)
    a_br = min(r["Fbru"], R1304 * r["Fbry"])
    s_net = P / ((L.w - D) * t) + 6 * M / (kb_L * (L.w - D) * t ** 2)
    a_net = min(r["Fnu"], R1304 * r["Fny"])
    s_bu = P / (Dp * t) + 6 * M / (kb_L * Dp * t ** 2)
    a_bu = R1304 * L.Fcy_B if L.Fcy_B else None
    m = M / (P * t)
    u = 2 * m
    A = Dp ** 2 - Di ** 2
    tau = 1.273 * P / A if m <= 2 / 3 else 1.273 * P / A * (sqrt(u ** 2 + 1) - 1) / (u + 1 - sqrt(u ** 2 + 1))
    S = (Dp ** 4 - Di ** 4) / Dp
    sb = 10.19 * M / (kb_P * S) * (P * t / (2 * M) - 1) if m <= 3 / 8 else 10.19 * M / (kb_P * S) * (sqrt(u ** 2 + 1) - 1) / u
    modes = {"lug_bearing": a_br / s_br, "lug_net": a_net / s_net,
             "bushing": (a_bu / s_bu) if a_bu else None, "pin_shear": Fsu_P / tau, "pin_bending": Ftu_P / sb}
    return dict(lug=r, s_br=s_br, a_br=a_br, s_net=s_net, a_net=a_net, s_bu=s_bu, a_bu=a_bu, m=m, tau=tau, sb=sb,
                modes=modes)


# ----------------------------------------------------------------------------- transverse 9.7 and oblique 9.10
def transverse_oblique(L: AxialLug, Dp, h1, h2, h3, h4, P_limit, alpha, UF=1.5, FF=1.15,
                       Ktru: Optional[float] = None, Ktry: Optional[float] = None):
    hav = 6 / (3 / h1 + 1 / h2 + 1 / h3 + 1 / h4)
    havD = hav / L.D
    ku, ky = k_fig9_8(havD)
    ku = Ktru if Ktru is not None else ku
    ky = Ktry if Ktry is not None else ky
    Fbru, Fbry = ku * L.Ftux * L.B_ratio, ky * L.Ftyx * L.B_ratio
    Ptru = Fbru * L.D * L.t if L.Ftux <= R1304 * L.Ftyx else R1304 * Fbry * L.D * L.t
    ax = axial_lug(L, Dp)
    PuL = ax["PuL"]
    ca, sa = abs(cos(radians(alpha))), abs(sin(radians(alpha)))
    Palpha = ((ca / PuL) ** 1.6 + (sa / Ptru) ** 1.6) ** (-1 / 1.6)
    PuB = R1304 * L.Fcy_B * Dp * L.t if L.Fcy_B else None
    Pdu = P_limit * UF * FF
    modes = {"lug_oblique": Palpha / Pdu if Pdu else None,
             "bushing": (PuB / Pdu) if (PuB and Pdu) else None}
    return dict(hav=hav, havD=havD, Ktru=ku, Ktry=ky, Ptru=Ptru, axial=ax, PuL=PuL, Palpha=Palpha, PuB=PuB,
                Pdu=Pdu, modes=modes)


# ----------------------------------------------------------------------------- multiple shear 9.13
# AFSAM Table 9-2: n -> (C, max pin shear / P1, bending arm b / ((t' + t'')/2))
TABLE_9_2 = {5: (0.35, 0.50, 0.28), 7: (0.40, 0.53, 0.33), 9: (0.43, 0.54, 0.37), 11: (0.44, 0.54, 0.39)}


def multi_shear(n, P_limit, t_in, t_out, Dp, Fsu_P, Ftu_P, kb_P=1.56, Di=0.0, UF=1.5, FF=1.15,
                Pu_inner_lug: Optional[float] = None):
    C, kshear, kb = TABLE_9_2[n]
    P = P_limit * UF * FF
    P1 = P / (n - 1)
    V = kshear * P1
    b = kb * (t_in + t_out) / 2
    M = P1 * b / 2
    tau = 1.273 * V / (Dp ** 2 - Di ** 2)
    sb = 10.19 * M / (kb_P * (Dp ** 4 - Di ** 4) / Dp)
    modes = {"pin_shear": Fsu_P / tau if tau else None, "pin_bending": Ftu_P / sb if sb else None,
             "inner_lug": (Pu_inner_lug / P1) if (Pu_inner_lug and P1) else None}
    return dict(C=C, P1=P1, V=V, b=b, M=M, tau=tau, sb=sb, t_out_min=C * t_in, modes=modes)


# ----------------------------------------------------------------------------- design 9.14
def design(P, Ftux1, Ftyx1, Ftux2, Ftyx2, FcyB1, FcyB2, Fsu_P, Ftu_P, kb_P, g, tB, K, D_Dp, eD, t1=0.0, t2=0.0,
           Di=0.0):
    fb1 = min(K * Ftux1 * D_Dp, R1304 * K * Ftyx1 * D_Dp, R1304 * FcyB1)
    fb2 = min(K * Ftux2 * D_Dp, R1304 * K * Ftyx2 * D_Dp, R1304 * FcyB2)
    R = 3.141592653589793 * Fsu_P / (kb_P * Ftu_P) * (Fsu_P / fb1 + Fsu_P / fb2)
    ft1, ft2 = min(Ftux1, R1304 * Ftyx1), min(Ftux2, R1304 * Ftyx2)
    Dp_s = sqrt(Di ** 2 + 0.798 ** 2 * P / Fsu_P)
    Dp_b1 = (Di ** 4 + (1.273 / kb_P) * (P / Ftu_P) ** 2 * (Ftu_P / ft1 + Ftu_P / ft2)) ** 0.25
    Dp1 = max(Dp_s, Dp_b1)
    D = Dp1 + 2 * tB
    out = dict(fb1=fb1, fb2=fb2, R=R, Dp_shear=Dp_s, Dp_bend1=Dp_b1, Dp1=Dp1, D=D, e=eD * D, aD=eD - 0.5,
               a=(eD - 0.5) * D, wD=2 * eD, w=2 * eD * D)
    if t1 > 0 and t2 > 0:
        q = 2.55 * P / (kb_P * Ftu_P) * (t1 + t2 / 2 + 2 * g)
        x = max(q ** (1 / 3), Di + 0.001)
        for _ in range(5):
            x = x - (x ** 4 - q * x - Di ** 4) / (4 * x ** 3 - q)
        out.update(q=q, Dp_bend2=x, Dp_opt=Dp_b1 / 3 + 2 * x / 3, Dp_opt_avg=(Dp_b1 + x) / 2)
    return out
