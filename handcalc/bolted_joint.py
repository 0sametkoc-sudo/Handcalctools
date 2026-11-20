"""Bolted joint, single fastener - reference implementation.

Independent Python implementation of the method used in Bolted_Joint_Tool.xlsx.
Units: N, mm, MPa, torque in N.m.

Method summary (see docs/Bolted_Joint_Tool.md for the full description):
* Fastener stiffness: bolt/screw  kf = 1 / (lt/(At Ef) + ld/(Ad Ef))
                      stud        kf = 1 / (lt_nut/(At,n Ef) + LT_s/(At,s Ef) + ld/(Ad Ef))
* Member stiffness:   pressure-cone frustums from the top and bottom bearing faces,
  meeting at mid-grip; every layer is split at the mid-plane; frusta in series.
* Load sharing:       C = kf/(kf+km), Pf = C Pex, Pm = (1-C) Pex
* Preload:            Fpre = T/(K d); max = Fpre (1+G); min = Fpre (1-G) - Fz
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import log, pi, radians, sqrt, tan
from typing import Optional

TYPES = ("BOLT", "SCREW", "STUD")


@dataclass
class Layer:
    t: float          # thickness, mm
    E: float          # Young's modulus, MPa
    name: str = ""


@dataclass
class BoltedJointInput:
    fastener_type: str
    # thread (nut end; for SCREW the single thread)
    d: float
    dp: float
    dr: float
    # loads (limit level)
    Pex: float
    Pshear: float
    # tightening
    T: float                  # N.m
    K: float = 0.2            # nut factor
    mu: float = 0.2           # friction coefficient between clamped parts
    Gamma: float = 0.0        # preload scatter +/- (fraction)
    fz: float = 0.0           # embedment (settlement), mm
    # geometry
    L: float = 0.0            # fastener length (bolt/screw under head; stud total)
    LT: float = 0.0           # threaded length (nut-end thread for a stud)
    LT_s: float = 0.0         # STUD: stud-end thread length (engaged in housing)
    Le_nut: float = 0.0       # BOLT/STUD: thread engagement length in the nut
    Le_h: float = 0.0         # SCREW: thread engagement length in the housing
    d_shank: Optional[float] = None
    # stud end thread (STUD only)
    d_s: Optional[float] = None
    dp_s: Optional[float] = None
    dr_s: Optional[float] = None
    # joint stack, top (head / nut of stud) to bottom
    layers: list = field(default_factory=list)
    Dw_top: float = 0.0
    Dw_bot: Optional[float] = None
    alpha: float = 30.0
    # materials
    Ef: float = 200000.0
    Fty: float = 0.0
    Ftu: float = 0.0
    Fsu: Optional[float] = None       # fastener ultimate shear strength
    Fsu_nut: Optional[float] = None   # nut material shear strength
    Fsu_h: Optional[float] = None     # housing material shear strength
    # factors
    UF: float = 1.5
    FF: float = 1.15
    CF: float = 1.0
    # optional checks
    threads_in_shear_plane: bool = False
    D_hole: Optional[float] = None
    p_allow: Optional[float] = None
    t_min: Optional[float] = None
    Fbru: Optional[float] = None
    P_alt: Optional[float] = None
    P_mean: Optional[float] = None
    Se: Optional[float] = None


def frustum_compliance(t, D, d, E, alpha_deg):
    """1/k of a hollow cone frustum (Shigley eq. 8-20 form). t=0 -> 0."""
    if t <= 0:
        return 0.0
    ta = tan(radians(alpha_deg))
    num = (2 * t * ta + D - d) * (D + d)
    den = (2 * t * ta + D + d) * (D - d)
    return log(num / den) / (pi * ta * E * d)


def member_stiffness(layers, d, Dw_top, Dw_bot, alpha):
    """Return (km, details). details: per layer (t_upper, D_upper, t_lower, D_lower, compliance)."""
    ta = tan(radians(alpha))
    l = sum(L.t for L in layers)
    mid = l / 2
    z = 0.0
    total = 0.0
    det = []
    for L in layers:
        z_top, z_bot = z, z + L.t
        tu = max(0.0, min(z_bot, mid) - z_top)
        tl = L.t - tu
        Du = Dw_top + 2 * z_top * ta
        Dl = Dw_bot + 2 * (l - z_bot) * ta
        c = frustum_compliance(tu, Du, d, L.E, alpha) + frustum_compliance(tl, Dl, d, L.E, alpha)
        det.append((tu, Du, tl, Dl, c))
        total += c
        z = z_bot
    return 1.0 / total, det


def _area(dt):
    return pi * dt ** 2 / 4


def analyse(inp: BoltedJointInput) -> dict:
    ty = inp.fastener_type.upper()
    assert ty in TYPES
    r = {}
    Dw_bot = inp.Dw_bot if inp.Dw_bot else inp.Dw_top
    d_shank = inp.d_shank if inp.d_shank else inp.d
    Fsu = inp.Fsu if inp.Fsu else 0.577 * inp.Ftu

    # sections
    At_n = _area((inp.dp + inp.dr) / 2)
    Ad = _area(d_shank)
    if ty == "STUD":
        At_s = _area((inp.dp_s + inp.dr_s) / 2)
        At = min(At_n, At_s)
    else:
        At_s = None
        At = At_n
    r.update(At_n=At_n, At_s=At_s, At=At, Ad=Ad)

    # grip and fastener stiffness
    l = sum(L.t for L in inp.layers)
    E = inp.Ef
    if ty == "STUD":
        lt = inp.LT - (inp.L - l)
        ld = inp.L - inp.LT - inp.LT_s
        kf = 1 / (lt / (At_n * E) + inp.LT_s / (At_s * E) + ld / (Ad * E))
    else:
        ld = min(max(inp.L - inp.LT, 0.0), l)
        lt = l - ld
        kf = 1 / (lt / (At_n * E) + ld / (Ad * E))
    km, det = member_stiffness(inp.layers, inp.d, inp.Dw_top, Dw_bot, inp.alpha)
    C = kf / (kf + km)
    Pex = max(inp.Pex, 0.0)
    Pf, Pm = C * Pex, (1 - C) * Pex
    r.update(l=l, lt=lt, ld=ld, kf=kf, km=km, ktot=kf + km, C=C, Pf=Pf, Pm=Pm, layers=det)

    # preload
    Fpre = inp.T * 1000 / (inp.K * inp.d)
    Fz = inp.fz * kf * km / (kf + km)
    Fmax = Fpre * (1 + inp.Gamma)
    Fmin = Fpre * (1 - inp.Gamma) - Fz
    r.update(Fpre=Fpre, Fz=Fz, Fpre_max=Fmax, Fpre_min=Fmin)

    UF, FF, CF = inp.UF, inp.FF, inp.CF
    P_lim = Fmax + Pf
    P_ult = Fmax + UF * Pf
    r.update(P_lim=P_lim, P_ult=P_ult, sig_lim=P_lim / At, sig_ult=P_ult / At)

    fm = {}

    def put(key, applies, rf, missing=False):
        if not applies:
            fm[key] = (None, "N/A")
        elif missing:
            fm[key] = (None, "NOT EVALUATED")
        else:
            fm[key] = (rf, "PASS" if rf >= 1 else "FAIL")

    put("FM01", True, inp.Fty / (FF * P_lim / At))
    put("FM02", True, inp.Ftu / (FF * P_ult / At))

    # thread stripping: 1.5 (UF) on the total limit load (preload included)
    As_nut = pi * inp.dp * 5 / 8 * inp.Le_nut
    Fsu_n = min(Fsu, inp.Fsu_nut) if inp.Fsu_nut else Fsu
    if ty in ("BOLT", "STUD"):
        fs_n = P_lim / As_nut
        put("FM03", True, Fsu_n / (UF * FF * fs_n))
    else:
        As_nut = None
        put("FM03", False, None)
    if ty == "SCREW":
        dp_h, Le_h = inp.dp, inp.Le_h
    elif ty == "STUD":
        dp_h, Le_h = inp.dp_s, inp.LT_s
    if ty in ("SCREW", "STUD"):
        As_h = pi * dp_h * 3 / 4 * Le_h
        if inp.Fsu_h:   # housing shear strength is required (weaker mating thread governs)
            Fsu_hh = min(Fsu, inp.Fsu_h)
            put("FM04", True, Fsu_hh / (UF * CF * P_lim / As_h))
        else:
            Fsu_hh = None
            put("FM04", True, None, missing=True)
    else:
        As_h, Fsu_hh = None, None
        put("FM04", False, None)
    r.update(As_nut=As_nut, As_h=As_h)

    # separation
    put("FM05", Pm > 0, Fmin / (FF * Pm) if Pm > 0 else None)
    put("FM06", Pm > 0, Fmin / (UF * FF * Pm) if Pm > 0 else None)
    # slip
    sh = inp.Pshear > 0
    put("FM07", sh, max(Fmin - Pm, 0) * inp.mu / inp.Pshear if sh else None)
    put("FM08", sh, max(Fmin - UF * Pm, 0) * inp.mu / (UF * inp.Pshear) if sh else None)
    # shear of the fastener (bearing-type behaviour after slip)
    A_sh = At_n if inp.threads_in_shear_plane else Ad
    tau = UF * FF * inp.Pshear / A_sh
    rf_sh = Fsu / tau if sh else None
    put("FM09", sh, rf_sh)
    # combined tension + shear (elliptic)
    if sh:
        Rt = FF * P_ult / (At * inp.Ftu)
        Rs = tau / Fsu
        put("FM10", True, 1 / sqrt(Rt ** 2 + Rs ** 2))
    else:
        put("FM10", False, None)
    # bearing under head / nut
    miss = inp.D_hole is None or inp.p_allow is None
    if not miss:
        Dw_b = min(inp.Dw_top, Dw_bot) if ty == "BOLT" else inp.Dw_top
        Ab = pi / 4 * (Dw_b ** 2 - inp.D_hole ** 2)
        put("FM11", True, inp.p_allow / (FF * P_lim / Ab))
    else:
        put("FM11", True, None, missing=True)
    # hole wall bearing
    miss = inp.t_min is None or inp.Fbru is None
    if sh and not miss:
        put("FM12", True, inp.Fbru / (UF * FF * inp.Pshear / (inp.d * inp.t_min)))
    else:
        put("FM12", sh, None, missing=miss)
    # fatigue (Goodman, Shigley eq. 8-38)
    miss = inp.P_alt is None or inp.Se is None
    if not miss and inp.P_alt > 0:
        Pmean = inp.P_mean if inp.P_mean is not None else inp.P_alt
        si = Fmax / At
        sa = C * inp.P_alt / At
        sm = si + C * Pmean / At
        nf = inp.Se * (inp.Ftu - si) / (inp.Ftu * sa + inp.Se * (sm - si))
        put("FM13", True, nf / FF)
    else:
        put("FM13", True, None, missing=True)
    # tightening torque window
    F_req = UF * Pm + UF * inp.Pshear / inp.mu
    T_min = inp.K * inp.d * (F_req + Fz) / (1 - inp.Gamma) / 1000
    caps = [inp.Fty * At / FF - Pf, inp.Ftu * At / FF - UF * Pf]
    if ty in ("BOLT", "STUD"):
        caps.append(Fsu_n * As_nut / (UF * FF) - Pf)
    if ty in ("SCREW", "STUD") and Fsu_hh:
        caps.append(Fsu_hh * As_h / (UF * CF) - Pf)
    F_cap = min(caps)
    T_max = inp.K * inp.d * F_cap / (1 + inp.Gamma) / 1000
    r.update(F_req=F_req, T_min=T_min, F_cap=F_cap, T_max=T_max)
    if T_min > 0:
        put("FM14", True, min(inp.T / T_min, T_max / inp.T))
    else:
        put("FM14", True, T_max / inp.T)

    r["fm"] = fm
    vals = [(v[0], k) for k, v in fm.items() if v[0] is not None]
    rf, key = min(vals)
    r.update(RF_gov=rf, FM_gov=key)
    return r
