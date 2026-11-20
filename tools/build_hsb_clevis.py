"""Build excel/HSB_Clevis_Tool.xlsx (HSB 26101-01 double-shear lug joint).

Every calculation is a live formula using named cells; the workbook stays fully editable.
Run:  python tools/build_hsb_clevis.py
"""
from __future__ import annotations

import os
import sys

import xlsxwriter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
from xlsx_common import formats, status_cf, rf_fail_cf, readme  # noqa: E402
from handcalc import hsb_clevis_examples as ex  # noqa: E402
from handcalc.hsb_clevis import joint, lug  # noqa: E402

OUT = os.path.join(ROOT, "excel", "HSB_Clevis_Tool.xlsx")
VERSION = "7.0"
SUF = {"f": "D", "m": "E"}   # female lug column D, male lug column E

# per-lug inputs: (key, label, symbol, female default, male default, unit, description, kind)
LUG_INPUTS = [
    ("sec", "1. LUG GEOMETRY  (HSB Figure 1; see the sketch on the right)"),
    ("d", "Hole diameter in the lug", "d", 24, 26, "mm",
     "If a bushing is fitted: the hole in the lug = bushing OUTER diameter.", "num"),
    ("r", "Outer radius of the lug head", "r", 24, 24, "mm", "Hole centre to the outer contour.", "num"),
    ("h", "Eccentricity", "h", 24, 24, "mm", "h = r for a concentric lug head.", "num"),
    ("e", "Edge distance in the load direction", "e", 24, 24, "mm", "Hole centre to the lug edge along the load.", "num"),
    ("w", "Smaller edge distance perpendicular to the load", "w", 24, 24, "mm",
     "HALF width, not the full lug width (most common input error). Net section uses (w - d/2).", "num"),
    ("t", "Thickness", "t", 5, 12, "mm", "Female: ONE prong.  Male: the single inner lug.", "num"),
    ("beta", "Taper angle", "beta", 45, 0, "deg", "0 = straight (parallel-sided) lug, 45 = tapered. Valid 0-45.", "num"),
    ("phi", "Load angle", "phi", 30, 0, "deg", "0 = along the lug axis, 90 = transverse. Valid 0-90.", "num"),
    ("sec", "2. LUG MATERIAL"),
    ("Rm", "Tensile ultimate strength", "Rm", 430, 470, "MPa", "Material specification (cross-grain if relevant).", "num"),
    ("Rp", "Tensile yield strength (0.2 %)", "Rp0.2", 290, 395, "MPa", "", "num"),
    ("Rb15", "Bearing yield strength at e/d = 1.5", "Rbry,1.5", 495, 560, "MPa", "Material data (HSB Fig. 2 / MMPDS).", "num"),
    ("Rb20", "Bearing yield strength at e/d = 2.0", "Rbry,2.0", 595, 670, "MPa", "", "num"),
    ("sec", "3. BUSHING  (HSB section 3.3)"),
    ("bush", "Bushing fitted?", "-", "YES", "YES", "-", "NO = section 3.3 does not apply (N/A).", ("list", ["YES", "NO"])),
    ("da", "Bolt diameter (= bushing bore)", "da", 16, 16, "mm",
     "Outer diameter of the bolt, i.e. the bore of the bushing. Smaller than d when a bushing is fitted.", "num"),
    ("Rc", "Bushing compressive yield strength", "Rc0.2", 600, 600, "MPa", "Compressive, not tensile, yield.", "num"),
]

JOINT_INPUTS = [
    ("P_lim", "Applied LIMIT load on the joint", "P", 20000, "N",
     "Total load on the joint (bolt load). Female prongs share it, the male lug carries all of it."),
    ("j_sf", "Safety (ultimate) factor j", "j", 1.5, "-",
     "HSB j: converts the yield allowables (Cases 2, 3, bushing) to the ultimate level. Usually 1.5."),
    ("FF_fit", "Fitting factor", "FF", 1.15, "-", "Company / programme standard. 1.0 if not required."),
    ("share", "Load share of ONE female prong", "s", 0.5, "-",
     "0.5 for a symmetric clevis. Larger for an asymmetric joint (e.g. different prong thicknesses)."),
]

# calc rows: (key, description, symbol, formula template with {s}, unit, equation / HSB ref)
CALC = [
    ("sec", "3.2.1  Geometric parameters"),
    ("x", "Radius ratio", "2r/d", "=2*r_{s}/d_{s}", "-", "Fig. 1"),
    ("hr", "Eccentricity ratio", "h/r", "=h_{s}/r_{s}", "-", "Fig. 1"),
    ("ed", "Edge distance ratio", "e/d", "=e_{s}/d_{s}", "-", "Fig. 1"),
    ("sec", "3.2.1a-b  Basic stress concentration factor Ktb,1"),
    ("k0", "Ktb,1 straight lug, phi = 0", "", "=2.75*(x_{s}-1)^(-0.675)", "-", "2.75 (2r/d - 1)^-0.675"),
    ("k90", "Ktb,1 straight lug, phi = 90", "", "=IF(x_{s}<=1.723,9.33*x_{s}^(-1.667),7.78*x_{s}^(-1.333))", "-",
     "2r/d <= 1.723: 9.33 (2r/d)^-1.667;  else 7.78 (2r/d)^-1.333"),
    ("ks", "Ktb,1 straight lug at phi", "", "=k0_{s}+phi_{s}/90*(k90_{s}-k0_{s})", "-", "linear in phi"),
    ("kt", "Ktb,1 tapered lug (beta = 45) at phi", "",
     "=2.417*(1+0.00633*phi_{s}-0.0000815*phi_{s}^2)*(x_{s}-1)^(-0.63)", "-",
     "2.417 (1 + 0.00633 phi - 0.0000815 phi^2)(2r/d - 1)^-0.63"),
    ("k1", "Ktb,1 at beta and phi", "Ktb,1",
     "=IF(beta_{s}<=0,ks_{s},IF(beta_{s}>=45,kt_{s},ks_{s}+beta_{s}/45*(kt_{s}-ks_{s})))", "-", "linear in beta"),
    ("sec", "3.2.1c-e  Eccentricity correction, Ktb and bearing efficiency"),
    ("H0", "H at phi = 0", "", "=hr_{s}^(-0.916)+0.284*LOG10(hr_{s})", "-", "(h/r)^-0.916 + 0.284 lg(h/r)"),
    ("H45", "H at phi = 45", "", "=hr_{s}^(-1.177)+1.737*LOG10(hr_{s})", "-", "(h/r)^-1.177 + 1.737 lg(h/r)"),
    ("H90", "H at phi = 90", "", "=hr_{s}^(-0.495)+0.715*LOG10(hr_{s})", "-", "(h/r)^-0.495 + 0.715 lg(h/r)"),
    ("Hc", "Eccentricity factor H at phi", "H",
     "=IF(phi_{s}<=45,H0_{s}+phi_{s}/45*(H45_{s}-H0_{s}),H45_{s}+(phi_{s}-45)/45*(H90_{s}-H45_{s}))", "-",
     "linear in phi between 0, 45, 90"),
    ("Ktb", "Stress concentration factor", "Ktb", "=Hc_{s}*k1_{s}", "-", "Ktb = H Ktb,1"),
    ("KBR", "Bearing efficiency factor", "KBR", "=7.502*(Ktb_{s}+1.125)^(-1.637)", "-", "7.502 (Ktb + 1.125)^-1.637"),
    ("sec", "3.2.2  Static failure loads (allowables, N)"),
    ("FLu", "Case 1  lug ultimate strength", "F_Lu", "=0.84*KBR_{s}*d_{s}*t_{s}*Rm_{s}", "N", "0.84 KBR d t Rm  (no j)"),
    ("FLy1", "Case 2  net-section yield, route 1", "F_Ly1", "=2*j_sf*(w_{s}-d_{s}/2)*t_{s}*Rp_{s}", "N",
     "2 j (w - d/2) t Rp0.2"),
    ("ratio", "Ratio", "F_Lu/(d t Rm)", "=FLu_{s}/(d_{s}*t_{s}*Rm_{s})", "-", ""),
    ("Cc", "Coefficient C", "C", "=IF(ratio_{s}<=1.25,1.1,1.379-0.223*ratio_{s})", "-",
     "<= 1.25: 1.1;  else 1.379 - 0.223 ratio"),
    ("FLy2", "Case 2  net-section yield, route 2", "F_Ly2", "=j_sf*Cc_{s}*(Rp_{s}/Rm_{s})*FLu_{s}", "N",
     "j C (Rp0.2/Rm) F_Lu"),
    ("FLy", "Case 2  lug net-section yield", "F_Ly", "=MIN(FLy1_{s},FLy2_{s})", "N", "min of the two routes"),
    ("Rbry", "Bearing yield strength at e/d", "Rbry",
     "=IF(ed_{s}<=1.5,Rb15_{s}*(ed_{s}-0.5),IF(ed_{s}<=2,Rb15_{s}+2*(ed_{s}-1.5)*(Rb20_{s}-Rb15_{s}),Rb20_{s}))",
     "MPa", "0.5-1.5: Rbry,1.5 (e/d - 0.5);  1.5-2.0: linear;  >2: Rbry,2.0"),
    ("FLybr", "Case 3  lug bearing yield", "F_Ly,br", "=j_sf*d_{s}*t_{s}*Rbry_{s}", "N", "j d t Rbry"),
    ("FB", "3.3  bushing bearing strength", "F_B", '=IF(bush_{s}="YES",1.85*j_sf*da_{s}*t_{s}*Rc_{s},"")', "N",
     "1.85 j da t Rc0.2  (bushing fitted only)"),
    ("Fcap", "Load carrying capability of the lug", "F_cap", "=MIN(FLu_{s},FLy_{s},FLybr_{s},FB_{s})", "N",
     "3.4: lowest value governs"),
    ("sec", "Applied load and reserve factors"),
    ("Plug", "Limit load on this lug", "P_lug", None, "N", "female prong: s P;  male: P"),
    ("Pu", "Ultimate design load on this lug", "P_u", "=j_sf*FF_fit*Plug_{s}", "N", "P_u = j FF P_lug"),
    ("RF1", "RF Case 1", "", "=FLu_{s}/Pu_{s}", "-", "F_Lu / P_u"),
    ("RF2", "RF Case 2", "", "=FLy_{s}/Pu_{s}", "-", "F_Ly / P_u"),
    ("RF3", "RF Case 3", "", "=FLybr_{s}/Pu_{s}", "-", "F_Ly,br / P_u"),
    ("RFB", "RF bushing", "", '=IF(bush_{s}="YES",FB_{s}/Pu_{s},"")', "-", "F_B / P_u"),
]
PLUG = {"f": "=share*P_lim", "m": "=P_lim"}

CHECKS = [  # (description, condition template)
    ("2r/d within 1.332 - 3.400 (range of Ktb,1)", "AND(x_{s}>=1.332,x_{s}<=3.4)"),
    ("beta within 0 - 45 deg", "AND(beta_{s}>=0,beta_{s}<=45)"),
    ("phi within 0 - 90 deg", "AND(phi_{s}>=0,phi_{s}<=90)"),
    ("h > 0", "h_{s}>0"),
    ("e/d > 0.5 (Case 3 defined)", "ed_{s}>0.5"),
    ("w > d/2 (net section exists)", "w_{s}>d_{s}/2"),
    ("t > 0 and Rm > Rp0.2 > 0", "AND(t_{s}>0,Rp_{s}>0,Rm_{s}>Rp_{s})"),
    ("Rbry,2.0 >= Rbry,1.5 > 0", "AND(Rb15_{s}>0,Rb20_{s}>=Rb15_{s})"),
    ("Bushing: 0 < da <= d and Rc0.2 > 0", 'OR(bush_{s}="NO",AND(da_{s}>0,da_{s}<=d_{s},Rc_{s}>0))'),
]

MODES = [  # (lug key, case key, label, HSB ref, meaning)
    ("case1", "Case 1  lug ultimate", "3.2.2 Case 1",
     "The lug breaks at the hole (tension, shear-out, hoop): empirical Ekvall strength, compared with the ultimate load."),
    ("case2", "Case 2  net-section yield", "3.2.2 Case 2",
     "The net section beside the hole yields (permanent set at limit load)."),
    ("case3", "Case 3  bearing yield", "3.2.2 Case 3",
     "The hole ovalises: local bearing yield of the lug against the bolt/bushing."),
    ("bushing", "3.3  bushing bearing", "3.3",
     "The bushing crushes against the bolt (compressive yield)."),
]
RFKEY = {"case1": "RF1", "case2": "RF2", "case3": "RF3", "bushing": "RFB"}
INFO_MODES = [
    ("Bolt / pin shear and bending", "Not covered by HSB 26101-01. Check the bolt with HSB 26101-02 or the AFSAM "
     "Lug tool (Section 9.4: pin shear, pin bending, balanced design)."),
    ("Lug fatigue", "Static method only. Check fatigue separately (stress concentration Ktb is a useful input)."),
    ("Bushing press fit / migration", "Interference-fit stresses and bushing rotation are not covered."),
]


def build(path=OUT):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wb = xlsxwriter.Workbook(path)
    wb.set_properties({"title": "HSB Clevis Tool", "comments": f"Version {VERSION}"})
    F = formats(wb)
    rd = wb.add_worksheet("README")
    inp = wb.add_worksheet("Input")
    res = wb.add_worksheet("Results")
    calc = wb.add_worksheet("Calc")
    exs = wb.add_worksheet("Examples")

    # ------------------------------------------------------------------ Input
    inp.set_column("A:A", 2)
    inp.set_column("B:B", 46)
    inp.set_column("C:C", 9)
    inp.set_column("D:E", 15)
    inp.set_column("F:F", 6)
    inp.set_column("G:G", 80)
    inp.write("B1", "HSB 26101-01 CLEVIS TOOL - INPUT", F["title"])
    inp.write("B2", "Double-shear lug joint: female lug (two prongs) + male lug. Fill the blue cells. "
                    "Units: N, mm, MPa.", F["sub"])
    inp.write_row(3, 1, ["Parameter", "Symbol", "Female lug\n(one prong)", "Male lug", "Unit",
                         "Description / where to get it"], F["hdr"])
    inp.set_row(3, 28)
    r = 4
    for spec in LUG_INPUTS:
        if spec[0] == "sec":
            inp.merge_range(r, 1, r, 6, spec[1], F["sec"])
            r += 1
            continue
        key, label, sym, df, dm, unit, desc, kind = spec
        inp.write(r, 1, label)
        inp.write(r, 2, sym)
        for s, col, val in (("f", 3, df), ("m", 4, dm)):
            if isinstance(kind, tuple):
                inp.write(r, col, val, F["intxt"])
                inp.data_validation(r, col, r, col, {"validate": "list", "source": kind[1]})
            else:
                inp.write_number(r, col, val, F["in"])
            wb.define_name(f"{key}_{s}", f"=Input!${SUF[s]}${r + 1}")
        inp.write(r, 5, unit)
        inp.write(r, 6, desc, F["txt"])
        r += 1
    inp.merge_range(r, 1, r, 6, "4. JOINT LOAD AND FACTORS", F["sec"])
    r += 1
    for key, label, sym, val, unit, desc in JOINT_INPUTS:
        inp.write(r, 1, label)
        inp.write(r, 2, sym)
        inp.write_number(r, 3, val, F["in"])
        inp.write(r, 5, unit)
        inp.write(r, 6, desc, F["txt"])
        wb.define_name(key, f"=Input!$D${r + 1}")
        r += 1
    r += 1
    inp.merge_range(r, 1, r, 6, "INPUT CHECKS (HSB 3.2.1 validity) - all must read OK", F["sec"])
    r += 1
    c0 = r
    for desc, cond in CHECKS:
        inp.write(r, 1, desc)
        for s in ("f", "m"):
            col = 3 if s == "f" else 4
            inp.write_formula(r, col, f'=IF(IFERROR({cond.format(s=s)},FALSE),"OK","CHECK")', F["calcg"])
        r += 1
    inp.write(r, 1, "Joint: P >= 0, j >= 1, FF >= 1, 0 < s <= 1")
    inp.write_formula(r, 3, '=IF(IFERROR(AND(P_lim>=0,j_sf>=1,FF_fit>=1,share>0,share<=1),FALSE),"OK","CHECK")',
                      F["calcg"])
    r += 1
    wb.define_name("chk_list", f"=Input!$D${c0 + 1}:$E${r}")
    inp.write(r, 1, "ALL INPUT CHECKS", F["bold"])
    n_chk = 2 * len(CHECKS) + 1
    inp.write_formula(r, 3, f'=IF(COUNTIF(chk_list,"OK")={n_chk},"ALL OK","CHECK INPUTS")', F["rest"])
    wb.define_name("chk_all", f"=Input!$D${r + 1}")
    status_cf(inp, f"D{c0 + 1}:E{r + 1}", F)
    fig = os.path.join(ROOT, "docs", "figures", "hsb_lug_geometry.png")
    if os.path.exists(fig):
        inp.write("I4", "LUG GEOMETRY - symbols used on this sheet", F["bold"])
        inp.insert_image("I5", fig, {"x_scale": 0.5, "y_scale": 0.5, "object_position": 3})
    fig2 = os.path.join(ROOT, "docs", "figures", "hsb_joint.png")
    if os.path.exists(fig2):
        inp.insert_image("I32", fig2, {"x_scale": 0.5, "y_scale": 0.5, "object_position": 3})
    inp.freeze_panes(4, 0)
    inp.set_landscape()
    inp.fit_to_pages(1, 0)
    inp.print_area(0, 0, r, 6)

    # ------------------------------------------------------------------ Calc
    calc.set_column("A:A", 2)
    calc.set_column("B:B", 40)
    calc.set_column("C:C", 13)
    calc.set_column("D:E", 15)
    calc.set_column("F:F", 6)
    calc.set_column("G:G", 60)
    calc.write("B1", "HSB 26101-01 CLEVIS TOOL - CALCULATION", F["title"])
    calc.write("B2", "Live formulas with named cells (suffix _f = female prong, _m = male lug). Do not type here.",
               F["sub"])
    calc.write_row(3, 1, ["Quantity", "Symbol", "Female lug\n(one prong)", "Male lug", "Unit", "Equation / HSB ref."],
                   F["hdr"])
    calc.set_row(3, 28)
    r = 4
    for spec in CALC:
        if spec[0] == "sec":
            calc.merge_range(r, 1, r, 6, spec[1], F["sec"])
            r += 1
            continue
        key, desc, sym, tmpl, unit, eq = spec
        calc.write(r, 1, desc)
        calc.write(r, 2, sym)
        for s, col in (("f", 3), ("m", 4)):
            formula = PLUG[s] if key == "Plug" else tmpl.format(s=s)
            f = F["calc0"] if unit == "N" else F["calc"]
            calc.write_formula(r, col, formula, f)
            wb.define_name(f"{key}_{s}", f"=Calc!${SUF[s]}${r + 1}")
        calc.write(r, 5, unit)
        calc.write(r, 6, eq, F["small"])
        r += 1
    calc.freeze_panes(4, 0)
    calc.set_landscape()
    calc.fit_to_pages(1, 0)

    # ------------------------------------------------------------------ Results
    res.set_column("A:A", 2)
    res.set_column("B:B", 13)
    res.set_column("C:C", 28)
    res.set_column("D:D", 13)
    res.set_column("E:F", 14)
    res.set_column("G:G", 10)
    res.set_column("H:H", 16)
    res.set_column("I:I", 70)
    res.write("B1", "HSB 26101-01 CLEVIS TOOL - RESULTS", F["title"])
    res.write("B2", "All lugs of the joint are checked; HSB 3.4: the lowest RF governs. RF = allowable / (j FF P_lug).",
              F["sub"])
    labels = [("Input checks", "=chk_all", "rest"),
              ("GOVERNING RESERVE FACTOR", None, "big"),
              ("Governing lug and mode", None, "rest"),
              ("OVERALL STATUS", None, "big"),
              ("Allowable joint LIMIT load  (= RF x P)", None, "big0")]
    for i, (lab, f, fm) in enumerate(labels):
        res.write(3 + i, 1, lab, F["bold"])
        res.merge_range(3 + i, 3, 3 + i, 5, "", F[fm])
        if f:
            res.write_formula(3 + i, 3, f, F[fm])
    h = 10
    res.write_row(h, 1, ["Lug", "Failure mode", "HSB ref.", "Allowable\nF [N] (incl. j)", "Ultimate load\nj FF P_lug [N]",
                         "RF", "Status", "What it means"], F["hdr"])
    res.set_row(h, 30)
    r = h + 1
    first = r
    for s, lugname in (("f", "Female prong"), ("m", "Male lug")):
        for case, label, ref, mean in MODES:
            alw = {"case1": "FLu", "case2": "FLy", "case3": "FLybr", "bushing": "FB"}[case]
            res.write(r, 1, lugname, F["bold"])
            res.write(r, 2, label, F["txtb"])
            res.write(r, 3, ref, F["small"])
            res.write_formula(r, 4, f"={alw}_{s}", F["res0"])
            res.write_formula(r, 5, f"=Pu_{s}", F["res0"])
            res.write_formula(r, 6, f"={RFKEY[case]}_{s}", F["res"])
            if case == "bushing":
                st = f'=IF(bush_{s}<>"YES","N/A",IF({RFKEY[case]}_{s}>=1,"PASS","FAIL"))'
            else:
                st = f'=IF({RFKEY[case]}_{s}>=1,"PASS","FAIL")'
            res.write_formula(r, 7, st, F["rest"])
            res.write(r, 8, mean, F["small"])
            res.set_row(r, 26)
            r += 1
    last = r
    for lab, mean in INFO_MODES:
        res.write(r, 1, "Joint", F["bold"])
        res.write(r, 2, lab, F["txtb"])
        res.write(r, 3, "-", F["small"])
        res.write(r, 6, "", F["res"])
        res.write(r, 7, "INFO", F["rest"])
        res.write(r, 8, mean, F["small"])
        res.set_row(r, 26)
        r += 1
    status_cf(res, f"H{first + 1}:H{r}", F)
    status_cf(res, "D4:D7", F)
    rf_fail_cf(res, f"G{first + 1}:G{last}", f"G{first + 1}", F)
    rf = f"$G${first + 1}:$G${last}"
    st = f"$H${first + 1}:$H${last}"
    res.write_formula("D5", f"=MIN({rf})", F["big"])
    res.write_formula("D6", f'=INDEX($B${first + 1}:$B${last},MATCH(D5,{rf},0))&" - "&'
                            f'INDEX($C${first + 1}:$C${last},MATCH(D5,{rf},0))', F["rest"])
    res.write_formula("D7", f'=IF(chk_all<>"ALL OK","INPUT ERROR - see input checks",'
                            f'IF(COUNTIF({st},"FAIL")>0,"FAIL - "&D6,"PASS - all lugs and modes"))', F["big"])
    res.write_formula("D8", "=D5*P_lim", F["big0"])
    wb.define_name("RF_gov", "=Results!$D$5")
    wb.define_name("status_all", "=Results!$D$7")
    res.write(r + 1, 1, "Notes", F["bold"])
    notes = [
        "Case 1 is an ultimate strength (no j inside); Cases 2, 3 and the bushing are yield strengths multiplied by j, "
        "which puts them on the ultimate scale. All four are therefore compared with the same ultimate load j FF P_lug.",
        "Female lug = one prong carrying s P (s = 0.5 symmetric). Male lug carries P. HSB 3.4: apply the method to the "
        "female lug, the male lug and their bushings; the lowest result is the capability of the joint.",
    ]
    for i, t in enumerate(notes):
        res.merge_range(r + 2 + i, 1, r + 2 + i, 8, t, F["small"])
        res.set_row(r + 2 + i, 26)
    res.freeze_panes(h + 1, 0)
    res.set_landscape()
    res.fit_to_pages(1, 0)

    # ------------------------------------------------------------------ Examples
    exs.set_column("A:A", 2)
    exs.set_column("B:B", 36)
    exs.set_column("C:H", 14)
    exs.write("B1", "EXAMPLES - verification and regression cases", F["title"])
    exs.write("B2", "Case A is the HSB 26101-01 worked example (pages 7-8). It is also the default input of this "
                    "workbook. The automated tests check the workbook against the published values.", F["sub"])
    exs.write_row(3, 1, ["Case A: HSB worked example", "Female", "Male", "Published F", "Published M",
                         "This tool F", "This tool M"], F["hdr"])
    fem, mal = lug(ex.HSB_FEMALE, ex.HSB_J), lug(ex.HSB_MALE, ex.HSB_J)
    r = 4
    for attr, lab in [("d", "d"), ("r", "r"), ("h", "h"), ("e", "e"), ("w", "w"), ("t", "t"), ("beta", "beta"),
                      ("phi", "phi"), ("Rm", "Rm"), ("Rp02", "Rp0.2"), ("Rbry15", "Rbry,1.5"), ("Rbry20", "Rbry,2.0"),
                      ("da", "da"), ("Rc02", "Rc0.2")]:
        exs.write(r, 1, lab)
        exs.write(r, 2, getattr(ex.HSB_FEMALE, attr))
        exs.write(r, 3, getattr(ex.HSB_MALE, attr))
        r += 1
    exs.write(r, 1, "j")
    exs.write(r, 2, ex.HSB_J)
    exs.write(r, 3, ex.HSB_J)
    r += 2
    for key, (pf, pm) in ex.PUBLISHED.items():
        exs.write(r, 1, key)
        exs.write(r, 4, pf)
        exs.write(r, 5, pm)
        exs.write_number(r, 6, round(fem[key], 4))
        exs.write_number(r, 7, round(mal[key], 4))
        r += 1
    r += 1
    exs.write_row(r, 1, ["Case B: eccentric / oblique, no female bushing", "Female", "Male"], F["hdr"])
    r += 1
    fb, mb = lug(ex.ECC_FEMALE, 1.5), lug(ex.ECC_MALE, 1.5)
    for attr in ["d", "r", "h", "e", "w", "t", "beta", "phi", "Rm", "Rp02", "Rbry15", "Rbry20", "bushing", "da", "Rc02"]:
        exs.write(r, 1, attr)
        for c, L in ((2, ex.ECC_FEMALE), (3, ex.ECC_MALE)):
            v = getattr(L, attr)
            if isinstance(v, bool):
                v = "YES" if v else "NO"
            if v is not None:
                exs.write(r, c, v)
        r += 1
    for key in ["Ktb1", "H", "KBR", "F_Lu", "F_Ly", "F_Lybr", "F_B"]:
        exs.write(r, 1, f"expected {key}  (j = 1.5)")
        for c, rr in ((2, fb), (3, mb)):
            v = rr[key]
            exs.write(r, c, round(v, 4) if v is not None else "N/A")
        r += 1

    # ------------------------------------------------------------------ README
    readme(rd, [
        ("title", f"HSB 26101-01 CLEVIS TOOL  -  static strength of metallic double-shear lugs  -  version {VERSION}"),
        ("sub", "Ekvall method as given in HSB 26101-01 Issue E (2006). Female lug (two prongs), male lug and their "
                "bushings are checked together. Units: N, mm, MPa."),
        ("sec", "HOW TO USE"),
        ("txt", "1. Sheet Input: fill the blue cells for the female lug (one prong) and the male lug, then the joint "
                "load and factors. The sketch on the right shows every symbol. The most common error is w: it is the "
                "HALF width (smaller edge distance perpendicular to the load)."),
        ("txt", "2. INPUT CHECKS at the bottom of Input must read ALL OK (HSB validity limits)."),
        ("txt", "3. Sheet Results: all four HSB cases for both lugs, the governing lug/mode, the allowable joint limit "
                "load, and the modes that are NOT covered by HSB 26101-01 (listed as INFO with where to check them)."),
        ("txt", "4. Sheet Calc shows every intermediate value with its HSB section. Sheet Examples holds the HSB "
                "worked example with its published values."),
        ("sec", "THE SAFETY FACTOR j"),
        ("txt", "Case 1 (F_Lu) is an ultimate strength and has no j. Cases 2, 3 and the bushing are yield strengths "
                "multiplied by j, which places them on the ultimate scale. All cases are then compared with the "
                "ultimate load j FF P_lug. Do not apply j again elsewhere."),
        ("sec", "COLOUR CODE"),
        ("txt", "Blue = input.  Grey = calculated.  Yellow = result.  Green / red = pass / fail."),
        ("sec", "EDITING"),
        ("txt", "Nothing is locked or hidden. Formulas use named cells (Formulas > Name Manager), e.g. "
                "=0.84*KBR_f*d_f*t_f*Rm_f. After changing a formula run the repository tests."),
    ], F)
    rd.activate()
    wb.close()
    return path


if __name__ == "__main__":
    print(build())
