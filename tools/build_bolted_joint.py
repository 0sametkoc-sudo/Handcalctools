"""Build excel/Bolted_Joint_Tool.xlsx.

Every calculation in the workbook is a live Excel formula that uses named cells, so the
workbook stays fully editable. This script only lays the workbook out; it is not needed
to use the tool. Run:  python tools/build_bolted_joint.py
"""
from __future__ import annotations

import os
import sys

import xlsxwriter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from handcalc.threads import thread_table  # noqa: E402
from handcalc import bolted_joint_examples as ex  # noqa: E402
from handcalc.bolted_joint import analyse  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "excel", "Bolted_Joint_Tool.xlsx")
VERSION = "2.0"
N_LAYERS = 8

# ----------------------------------------------------------------------------- inputs
# (name, label, symbol, default, unit, description, used_by, kind)
# kind: "num" | ("list", [...]) | "thread" | "text"
INPUTS = [
    ("sec", "1. FASTENER TYPE AND THREAD"),
    ("ftype", "Fastener type", "-", "STUD", "-",
     "BOLT = head + nut.  SCREW = head, threaded into a tapped hole (no nut).  "
     "STUD = threaded both ends: stud end in a tapped housing, nut on the other end.",
     "all", ("list", ["BOLT", "SCREW", "STUD"])),
    ("thread_n", "Thread (nut end; for a SCREW its only thread)", "-", "5/16-24 UNJF", "-",
     "Pick from the list (sheet Threads) or choose CUSTOM and type the three diameters below. "
     "Table values are basic / minimum sizes.", "all", "thread"),
    ("d_in", "  Major (nominal) diameter d - override", "d", 7.75, "mm",
     "Leave blank to use the table value (shown on the right). Type a value to override it, e.g. "
     "the minimum major diameter of the tolerance class. Used for preload, cone stiffness, hole bearing.",
     "FM01-FM14", "num"),
    ("dp_in", "  Pitch diameter dp - override", "dp", None, "mm",
     "Blank = table value. Minimum pitch diameter is conservative.", "FM01-04,FM14", "num"),
    ("dr_in", "  Minor diameter dr - override", "dr", None, "mm",
     "Blank = table value. Tensile diameter dt = (dp + dr)/2.", "FM01-02,FM14", "num"),
    ("thread_s", "Stud-end thread (STUD only)", "-", "7/16-20 UNJF", "-",
     "The end screwed into the housing. Ignored for BOLT and SCREW.", "STUD", "thread"),
    ("ds_in", "  Stud-end major diameter - override", "d,s", 11.11, "mm", "Blank = table value.", "STUD", "num"),
    ("dps_in", "  Stud-end pitch diameter - override", "dp,s", 10.33, "mm",
     "Blank = table value. Used for the housing thread shear area.", "STUD", "num"),
    ("drs_in", "  Stud-end minor diameter - override", "dr,s", 9.40, "mm", "Blank = table value.", "STUD", "num"),
    ("dsh_in", "Unthreaded shank diameter", "dsh", 7.887, "mm",
     "Blank = d. Diameter of the plain shank (reduced-shank bolts / studs differ from d).",
     "FM09,stiffness", "num"),

    ("sec", "2. FASTENER LENGTHS"),
    ("L_f", "Fastener length", "L", 43.82, "mm",
     "BOLT / SCREW: under-head length.  STUD: overall length end to end.", "stiffness", "num"),
    ("LT_f", "Threaded length (nut end)", "LT", 17.48, "mm",
     "BOLT / SCREW: total threaded length.  STUD: length of the nut-end thread. "
     "If unknown (ISO bolts): 2d+6 (L<=125), 2d+12 (125<L<=200), 2d+25 (L>200).", "stiffness", "num"),
    ("LT_s", "Stud-end thread length (engaged in housing)", "LT,s", 13.95, "mm",
     "STUD only. Also used as the thread engagement length in the housing.", "STUD: FM04", "num"),
    ("Le_nut", "Thread engagement length in the nut", "Le,nut", 6.5, "mm",
     "BOLT / STUD. Normally the nut height (full threads engaged).", "FM03,FM14", "num"),
    ("Le_h", "Thread engagement length in the tapped housing", "Le,h", None, "mm",
     "SCREW only. Depth of full thread engagement in the tapped hole.", "SCREW: FM04", "num"),

    ("sec", "3. JOINT STACK - clamped layers (fill the table below)"),
    ("Dw_top", "Bearing diameter at the top face (head, or nut of a stud)", "Dw,top", 13.21, "mm",
     "Outer diameter of the contact under the head / nut / washer. Unknown: about 1.5 d.", "stiffness,FM11", "num"),
    ("Dw_bot_in", "Bearing diameter at the bottom face", "Dw,bot", None, "mm",
     "Blank = same as top. BOLT: under the nut. SCREW / STUD: cone start at the end of the "
     "engaged thread in the housing.", "stiffness,FM11", "num"),
    ("alpha_deg", "Pressure-cone half angle", "alpha", 30, "deg", "30 deg is the usual value.", "stiffness", "num"),

    ("sec", "4. MATERIALS"),
    ("Ef", "Young's modulus of the fastener", "Ef", 199948, "MPa", "", "stiffness", "num"),
    ("Fty", "Fastener tensile yield strength", "Fty", 871, "MPa", "From the fastener specification.", "FM01,FM14", "num"),
    ("Ftu", "Fastener tensile ultimate strength", "Ftu", 1103, "MPa", "", "FM02,FM10,FM13,FM14", "num"),
    ("Fsu_in", "Fastener ultimate shear strength", "Fsu", 636, "MPa",
     "Blank = 0.577 Ftu. Used for fastener shear and for thread shear.", "FM03,FM04,FM09,FM10", "num"),
    ("Fsu_nut", "Nut material ultimate shear strength", "Fsu,nut", None, "MPa",
     "Optional. If lower than the fastener's, it governs the nut-end thread shear.", "FM03", "num"),
    ("Fsu_h", "Housing material ultimate shear strength", "Fsu,h", 165, "MPa",
     "SCREW / STUD: required. The weaker of housing and fastener governs.", "FM04", "num"),

    ("sec", "5. LOADS AT THE FASTENER (limit level) AND FACTORS"),
    ("Pex_in", "External axial load (tension +)", "Pex", 627, "N",
     "Limit load from FEM / hand calc. A compressive value is set to zero (not carried by the fastener).",
     "FM01-08,FM10,FM11,FM14", "num"),
    ("Pshear", "External shear load", "Pshear", 1008, "N", "Limit load. 0 or blank = no shear.",
     "FM07-FM10,FM12,FM14", "num"),
    ("UF_ult", "Ultimate factor", "UF", 1.5, "-", "Limit-to-ultimate factor.", "most", "num"),
    ("FF_fit", "Fitting factor", "FF", 1.15, "-", "Per company / programme standard.", "most", "num"),
    ("CF_cast", "Casting factor (housing thread)", "CF", 1.0, "-", "1.0 if the housing is not a casting.", "FM04", "num"),

    ("sec", "6. TIGHTENING"),
    ("T_tq", "Tightening torque", "T", 20, "N.m", "Nominal installation torque. Unit is N.m.", "all", "num"),
    ("K_nut", "Nut factor", "K", 0.2, "-", "T = K d Fpre. About 0.2 dry steel, 0.15 lubricated.", "all", "num"),
    ("mu_f", "Friction coefficient between clamped parts", "mu", 0.2, "-",
     "About 0.2 dry, 0.12 lubricated / wet.", "FM07,FM08,FM14", "num"),
    ("Gamma_s", "Preload scatter (+/-)", "Gamma", 0, "-",
     "0 = nominal preload. Typical torque-controlled: 0.25-0.35. Max preload = Fpre(1+Gamma) for "
     "strength checks, min = Fpre(1-Gamma) for separation and slip.", "all", "num"),
    ("fz_e", "Embedment (settlement) loss", "fz", 0, "mm",
     "Optional. Sum over all interfaces, about 0.002-0.003 mm each. Reduces the minimum preload.",
     "FM05-08,FM14", "num"),

    ("sec", "7. INPUTS FOR THE OPTIONAL CHECKS (leave blank to skip; the mode then shows NOT EVALUATED)"),
    ("thr_sh", "Threads in the shear plane?", "-", "NO", "-",
     "YES = shear area is the tensile stress area; NO = shank area.", "FM09,FM10", ("list", ["NO", "YES"])),
    ("D_hole", "Hole diameter under the head / nut", "Dh", None, "mm", "Inner diameter of the bearing ring.", "FM11", "num"),
    ("p_allow", "Allowable bearing pressure under head / nut", "p,allow", None, "MPa",
     "Of the softer clamped part, from material data.", "FM11", "num"),
    ("t_plate", "Thinnest plate loaded in shear", "t,min", None, "mm", "", "FM12", "num"),
    ("Fbru", "Allowable bearing stress of that plate", "Fbru", None, "MPa", "Ultimate bearing allowable.", "FM12", "num"),
    ("P_alt", "Cyclic external axial load amplitude", "Pa", None, "N", "(Pmax - Pmin)/2 at the fastener.", "FM13", "num"),
    ("P_mean_in", "Cyclic external axial mean load", "Pm,cyc", None, "N", "Blank = equal to the amplitude (0 to 2Pa cycle).", "FM13", "num"),
    ("Se_f", "Fastener endurance limit (amplitude)", "Se", None, "MPa",
     "Fully corrected for the thread. Rolled threads: 8.8: 129, 10.9: 162, 12.9: 190 MPa (Shigley).", "FM13", "num"),
]

DEFAULT_LAYERS = [("Washer 1", 0.8128, 199948), ("Washer 2", 0.8128, 68258),
                  ("Plate 1", 12, 71000), ("Housing (to end of engaged thread)", 17.62, 71000)]

# ----------------------------------------------------------------------------- failure modes
# (id, name, applies-to, app, miss, rf, criterion, required inputs, meaning)
FMODES = [
    ("FM01", "Fastener tensile yield (limit)", "all",
     "TRUE", "FALSE", "Fty/(FF_fit*sig_lim)",
     "RF = Fty / (FF . (Fpre,max + Pf)/At)", "Fty, thread, T, K, Pex",
     "The fastener yields under maximum preload plus its share of the limit load."),
    ("FM02", "Fastener tensile ultimate", "all",
     "TRUE", "FALSE", "Ftu/(FF_fit*sig_ult)",
     "RF = Ftu / (FF . (Fpre,max + UF.Pf)/At)", "Ftu, thread, T, K, Pex",
     "The fastener breaks in tension at ultimate load."),
    ("FM03", "Nut-end thread stripping", "BOLT, STUD",
     "NOT(is_screw)", "FALSE", "Fsu_n/(UF_ult*FF_fit*fs_nut)",
     "RF = Fsu / (UF . FF . (Fpre,max + Pf)/As,nut),  As,nut = pi.dp.(5/8).Le,nut",
     "Fsu (or Fsu,nut), Le,nut",
     "Threads between fastener and nut shear off. The weaker of fastener and nut material governs."),
    ("FM04", "Housing thread stripping", "SCREW, STUD",
     "NOT(is_bolt)", "NOT(ISNUMBER(Fsu_h))", "Fsu_hh/(UF_ult*CF_cast*fs_h)",
     "RF = Fsu / (UF . CF . (Fpre,max + Pf)/As,h),  As,h = pi.dp.(3/4).Le",
     "Fsu,h, engagement length",
     "Threads tapped into the housing shear off (usually the weakest link in light-alloy housings)."),
    ("FM05", "Joint separation (limit)", "all, Pex > 0",
     "Pm>0", "FALSE", "Fpre_min/(FF_fit*Pm)",
     "RF = Fpre,min / (FF . Pm)", "T, K, Pex, stack",
     "The clamped parts open (gap) at limit load: the clamp load is used up by the external load."),
    ("FM06", "Joint separation (ultimate)", "all, Pex > 0",
     "Pm>0", "FALSE", "Fpre_min/(UF_ult*FF_fit*Pm)",
     "RF = Fpre,min / (UF . FF . Pm)", "T, K, Pex, stack",
     "As FM05 at ultimate load. After separation the fastener carries the full external load."),
    ("FM07", "Slip (limit)", "all, Pshear > 0",
     "Pshear>0", "FALSE", "MAX(Fpre_min-Pm,0)*mu_f/Pshear",
     "RF = (Fpre,min - Pm) . mu / Pshear", "mu, T, K, Pshear",
     "Friction no longer holds the shear load; the parts slide. Repeated slip loosens the nut "
     "(self-loosening) and loads the fastener in shear/bending."),
    ("FM08", "Slip (ultimate)", "all, Pshear > 0",
     "Pshear>0", "FALSE", "MAX(Fpre_min-UF_ult*Pm,0)*mu_f/(UF_ult*Pshear)",
     "RF = (Fpre,min - UF.Pm) . mu / (UF . Pshear)", "mu, T, K, Pshear",
     "As FM07 at ultimate load."),
    ("FM09", "Fastener shear (after slip)", "all, Pshear > 0",
     "Pshear>0", "FALSE", "Fsu_f/tau",
     "RF = Fsu / (UF . FF . Pshear / A),  A = Ad or At", "Fsu, threads in shear plane?",
     "If the joint slips, the fastener itself carries the shear. Conservative: always checked."),
    ("FM10", "Combined tension + shear", "all, Pshear > 0",
     "Pshear>0", "FALSE", "1/SQRT((FF_fit*sig_ult/Ftu)^2+(tau/Fsu_f)^2)",
     "Rt^2 + Rs^2 = 1  ->  RF = 1/sqrt(Rt^2 + Rs^2)", "Ftu, Fsu",
     "Interaction of ultimate tension (preload included, conservative) and shear in the fastener."),
    ("FM11", "Bearing pressure under head / nut", "all",
     "TRUE", "OR(NOT(ISNUMBER(D_hole)),NOT(ISNUMBER(p_allow)))", "p_allow*A_brg/(FF_fit*P_lim)",
     "RF = p,allow / (FF . (Fpre,max + Pf)/Ab),  Ab = pi/4 (Dw^2 - Dh^2)", "Dh, p,allow",
     "The head / nut / washer crushes the clamped surface, which causes preload loss."),
    ("FM12", "Hole-wall bearing (plate)", "all, Pshear > 0",
     "Pshear>0", "OR(NOT(ISNUMBER(t_plate)),NOT(ISNUMBER(Fbru)))", "Fbru*d_u*t_plate/(UF_ult*FF_fit*Pshear)",
     "RF = Fbru / (UF . FF . Pshear / (d . t,min))", "t,min, Fbru",
     "After slip the fastener bears on the hole wall of the thinnest plate."),
    ("FM13", "Fatigue (Goodman)", "all, cyclic load",
     "TRUE", "OR(NOT(ISNUMBER(P_alt)),NOT(ISNUMBER(Se_f)),N(P_alt)<=0)",
     "Se_f*(Ftu-sig_i)/(Ftu*sig_a+Se_f*(sig_m-sig_i))/FF_fit",
     "nf = Se(Ftu - si) / (Ftu.sa + Se(sm - si)),  RF = nf/FF  (Shigley eq. 8-38)", "Pa, Se",
     "Fatigue failure at the thread root under the cyclic part of the external load."),
    ("FM14", "Tightening torque window", "all",
     "TRUE", "FALSE", "IF(T_min>0,MIN(T_tq/T_min,T_max/T_tq),T_max/T_tq)",
     "RF = min(T/Tmin, Tmax/T)", "T, K and the above",
     "Tmin: preload needed for no separation and no slip at ultimate.  Tmax: preload at which "
     "yield, ultimate or thread stripping reaches RF = 1. RF < 1: torque outside the window."),
]
INFO_MODES = [
    ("FM15", "Self-loosening (vibration)", "all",
     "Not calculated. Main cause is transverse slip (Junker). Keep FM07/FM08 >= 1 under vibration, or use a "
     "locking feature (self-locking nut, safety wire, adhesive)."),
    ("FM16", "Galling / thread seizure", "all",
     "Not calculated. Risk with stainless-on-stainless or titanium threads, especially dry. Use lubrication or "
     "coated / dissimilar materials."),
]

# ----------------------------------------------------------------------------- calc rows
# (name or None, description, symbol, formula, unit, equation text, note)
CALC = [
    ("sec", "A. Inputs resolved (table / override / defaults)"),
    ("is_bolt", "Configuration is BOLT", "", '=ftype="BOLT"', "", "", ""),
    ("is_screw", "Configuration is SCREW", "", '=ftype="SCREW"', "", "", ""),
    ("is_stud", "Configuration is STUD", "", '=ftype="STUD"', "", "", ""),
    ("tbl_d", "Table: major diameter", "", '=IFERROR(INDEX(thr_d,MATCH(thread_n,thr_name,0)),"")', "mm", "", "sheet Threads"),
    ("tbl_dp", "Table: pitch diameter", "", '=IFERROR(INDEX(thr_d2,MATCH(thread_n,thr_name,0)),"")', "mm", "", ""),
    ("tbl_dr", "Table: minor diameter", "", '=IFERROR(INDEX(thr_d3,MATCH(thread_n,thr_name,0)),"")', "mm", "", ""),
    ("d_u", "Major diameter used", "d", "=IF(ISNUMBER(d_in),d_in,tbl_d)", "mm", "", "override if given"),
    ("dp_u", "Pitch diameter used", "dp", "=IF(ISNUMBER(dp_in),dp_in,tbl_dp)", "mm", "", ""),
    ("dr_u", "Minor diameter used", "dr", "=IF(ISNUMBER(dr_in),dr_in,tbl_dr)", "mm", "", ""),
    ("tbl_ds", "Table: stud-end major diameter", "", '=IFERROR(INDEX(thr_d,MATCH(thread_s,thr_name,0)),"")', "mm", "", ""),
    ("tbl_dps", "Table: stud-end pitch diameter", "", '=IFERROR(INDEX(thr_d2,MATCH(thread_s,thr_name,0)),"")', "mm", "", ""),
    ("tbl_drs", "Table: stud-end minor diameter", "", '=IFERROR(INDEX(thr_d3,MATCH(thread_s,thr_name,0)),"")', "mm", "", ""),
    ("ds_u", "Stud-end major diameter used", "d,s", "=IF(ISNUMBER(ds_in),ds_in,tbl_ds)", "mm", "", "STUD only"),
    ("dps_u", "Stud-end pitch diameter used", "dp,s", "=IF(ISNUMBER(dps_in),dps_in,tbl_dps)", "mm", "", ""),
    ("drs_u", "Stud-end minor diameter used", "dr,s", "=IF(ISNUMBER(drs_in),drs_in,tbl_drs)", "mm", "", ""),
    ("d_sh", "Shank diameter used", "dsh", "=IF(ISNUMBER(dsh_in),dsh_in,d_u)", "mm", "", "blank = d"),
    ("Fsu_f", "Fastener shear strength used", "Fsu", "=IF(ISNUMBER(Fsu_in),Fsu_in,0.577*Ftu)", "MPa", "Fsu = 0.577 Ftu if blank", ""),
    ("Dw_bot", "Bottom bearing diameter used", "Dw,bot", "=IF(ISNUMBER(Dw_bot_in),Dw_bot_in,Dw_top)", "mm", "", "blank = Dw,top"),
    ("Pex_e", "Axial load used (tension only)", "Pex", "=MAX(N(Pex_in),0)", "N", "Pex = max(Pex, 0)", "compression -> 0"),
    ("P_mean", "Cyclic mean load used", "Pm,cyc", '=IF(ISNUMBER(P_mean_in),P_mean_in,N(P_alt))', "N", "", "blank = Pa"),
    ("tanA", "tan(alpha)", "", "=TAN(RADIANS(alpha_deg))", "-", "", ""),

    ("sec", "B. Fastener sections"),
    ("dt_n", "Tensile diameter, nut end", "dt", "=(dp_u+dr_u)/2", "mm", "dt = (dp + dr)/2", ""),
    ("At_n", "Tensile stress area, nut end", "At", "=PI()*dt_n^2/4", "mm2", "At = pi dt^2 / 4", ""),
    ("At_s", "Tensile stress area, stud end", "At,s", '=IF(is_stud,PI()*((dps_u+drs_u)/2)^2/4,"")', "mm2", "", "STUD only"),
    ("At_g", "Tensile stress area used for strength", "At", "=IF(is_stud,MIN(At_n,At_s),At_n)", "mm2", "smaller of the two ends", ""),
    ("Ad", "Shank area", "Ad", "=PI()*d_sh^2/4", "mm2", "Ad = pi dsh^2 / 4", ""),

    ("sec", "C. Grip and fastener stiffness"),
    ("l_grip", "Grip length (sum of layers)", "l", "=SUM(lay_t)", "mm", "l = sum t_i", ""),
    ("ld_g", "Unthreaded length in grip", "ld", "=IF(is_stud,L_f-LT_f-LT_s,MIN(MAX(L_f-LT_f,0),l_grip))", "mm",
     "bolt/screw: ld = L - LT (<= l);  stud: ld = L - LT - LT,s", ""),
    ("lt_g", "Threaded length in grip (nut end)", "lt", "=IF(is_stud,LT_f-(L_f-l_grip),l_grip-ld_g)", "mm",
     "bolt/screw: lt = l - ld;  stud: lt = LT - (L - l)", ""),
    ("kf", "Fastener stiffness", "kf",
     "=IF(is_stud,1/(lt_g/(At_n*Ef)+LT_s/(At_s*Ef)+ld_g/(Ad*Ef)),1/(lt_g/(At_n*Ef)+ld_g/(Ad*Ef)))", "N/mm",
     "1/kf = lt/(At Ef) + ld/(Ad Ef)  [+ LT,s/(At,s Ef) for a stud]", "springs in series"),

    ("sec", "D. Member stiffness - see layer table below"),
    ("km", "Member stiffness", "km", "=1/SUM(lay_c)", "N/mm", "1/km = sum of frustum compliances", ""),
    ("ktot", "Joint stiffness", "ktot", "=kf+km", "N/mm", "ktot = kf + km", "parallel"),
    ("C_j", "Joint constant (fastener share)", "C", "=kf/ktot", "-", "C = kf / (kf + km)", ""),
    ("Pf", "External load carried by the fastener", "Pf", "=C_j*Pex_e", "N", "Pf = C Pex", ""),
    ("Pm", "External load taken from the members", "Pm", "=(1-C_j)*Pex_e", "N", "Pm = (1 - C) Pex", "separating force"),

    ("sec", "E. Preload"),
    ("Fpre", "Nominal preload from torque", "Fpre", "=T_tq*1000/(K_nut*d_u)", "N", "Fpre = T / (K d)", ""),
    ("Fz", "Preload loss from embedment", "Fz", "=N(fz_e)*kf*km/(kf+km)", "N", "Fz = fz kf km / (kf + km)", ""),
    ("Fpre_max", "Maximum preload", "Fpre,max", "=Fpre*(1+N(Gamma_s))", "N", "Fpre,max = Fpre (1 + Gamma)", "strength checks"),
    ("Fpre_min", "Minimum preload", "Fpre,min", "=Fpre*(1-N(Gamma_s))-Fz", "N", "Fpre,min = Fpre (1 - Gamma) - Fz", "separation, slip"),

    ("sec", "F. Fastener loads and stresses"),
    ("P_lim", "Fastener load, limit", "Ptot", "=Fpre_max+Pf", "N", "Ptot = Fpre,max + Pf", ""),
    ("P_ult", "Fastener load, ultimate", "Ptot,u", "=Fpre_max+UF_ult*Pf", "N", "Ptot,u = Fpre,max + UF Pf", ""),
    ("sig_lim", "Tensile stress, limit", "s,lim", "=P_lim/At_g", "MPa", "", ""),
    ("sig_ult", "Tensile stress, ultimate", "s,ult", "=P_ult/At_g", "MPa", "", ""),
    ("As_nut", "Nut-end thread shear area", "As,nut", '=IF(is_screw,"",PI()*dp_u*5/8*Le_nut)', "mm2", "As = pi dp (5/8) Le,nut", ""),
    ("Fsu_n", "Shear strength, nut-end thread", "Fsu", "=IF(ISNUMBER(Fsu_nut),MIN(Fsu_f,Fsu_nut),Fsu_f)", "MPa", "weaker of fastener and nut", ""),
    ("fs_nut", "Nut-end thread shear stress (limit)", "fs", '=IF(is_screw,"",P_lim/As_nut)', "MPa", "fs = Ptot / As", ""),
    ("dp_h", "Housing thread pitch diameter", "dp,h", "=IF(is_stud,dps_u,dp_u)", "mm", "", ""),
    ("Le_hh", "Housing thread engagement length", "Le,h", "=IF(is_stud,LT_s,N(Le_h))", "mm", "stud: LT,s", ""),
    ("As_h", "Housing thread shear area", "As,h", '=IF(is_bolt,"",PI()*dp_h*3/4*Le_hh)', "mm2", "As = pi dp (3/4) Le", ""),
    ("Fsu_hh", "Shear strength, housing thread", "Fsu", '=IF(ISNUMBER(Fsu_h),MIN(Fsu_f,Fsu_h),"")', "MPa", "weaker of fastener and housing", ""),
    ("fs_h", "Housing thread shear stress (limit)", "fs", '=IF(is_bolt,"",P_lim/As_h)', "MPa", "", ""),
    ("A_sh", "Fastener shear area", "A", '=IF(thr_sh="YES",At_n,Ad)', "mm2", "", ""),
    ("tau", "Fastener shear stress (ultimate, incl. FF)", "tau", "=UF_ult*FF_fit*N(Pshear)/A_sh", "MPa", "tau = UF FF Pshear / A", ""),
    ("A_brg", "Bearing area under head / nut", "Ab",
     '=IF(ISNUMBER(D_hole),PI()/4*(IF(is_bolt,MIN(Dw_top,Dw_bot),Dw_top)^2-D_hole^2),"")', "mm2",
     "Ab = pi/4 (Dw^2 - Dh^2)", "bolt: smaller face"),
    ("sig_i", "Preload stress (max)", "si", "=Fpre_max/At_g", "MPa", "", "fatigue"),
    ("sig_a", "Alternating stress", "sa", "=C_j*N(P_alt)/At_g", "MPa", "sa = C Pa / At", ""),
    ("sig_m", "Mean stress", "sm", "=sig_i+C_j*P_mean/At_g", "MPa", "sm = si + C Pm,cyc / At", ""),

    ("sec", "G. Tightening torque window"),
    ("F_req", "Preload required (no separation, no slip at ultimate)", "Freq",
     "=UF_ult*Pm+UF_ult*N(Pshear)/mu_f", "N", "Freq = UF Pm + UF Pshear / mu", ""),
    ("T_min", "Minimum torque", "Tmin", "=K_nut*d_u*(F_req+Fz)/(1-N(Gamma_s))/1000", "N.m",
     "Tmin = K d (Freq + Fz) / (1 - Gamma)", ""),
    ("cap_y", "Max preload: yield", "", "=Fty*At_g/FF_fit-Pf", "N", "", ""),
    ("cap_u", "Max preload: ultimate", "", "=Ftu*At_g/FF_fit-UF_ult*Pf", "N", "", ""),
    ("cap_n", "Max preload: nut-end thread", "", '=IF(is_screw,"",Fsu_n*As_nut/(UF_ult*FF_fit)-Pf)', "N", "", ""),
    ("cap_h", "Max preload: housing thread", "", '=IF(OR(is_bolt,NOT(ISNUMBER(Fsu_h))),"",Fsu_hh*As_h/(UF_ult*CF_cast)-Pf)', "N", "", ""),
    ("F_cap", "Max allowable preload", "Fcap", "=MIN(cap_y,cap_u,cap_n,cap_h)", "N", "smallest of the above", ""),
    ("T_max", "Maximum torque", "Tmax", "=K_nut*d_u*F_cap/(1+N(Gamma_s))/1000", "N.m", "Tmax = K d Fcap / (1 + Gamma)", ""),
]

# input checks: (description, condition formula)
CHECKS = [
    ("Fastener type is BOLT, SCREW or STUD", 'OR(ftype="BOLT",ftype="SCREW",ftype="STUD")'),
    ("Thread diameters available, d > dp > dr", "AND(d_u>dp_u,dp_u>dr_u,dr_u>0)"),
    ("STUD: stud-end diameters available", "OR(NOT(is_stud),AND(ds_u>dps_u,dps_u>drs_u,drs_u>0))"),
    ("Bearing diameters larger than d", "AND(Dw_top>d_u,Dw_bot>d_u)"),
    ("Grip length > 0 and every layer with t > 0 has E > 0",
     "AND(l_grip>0,SUMPRODUCT((lay_t>0)*(N(+lay_E)<=0))=0)"),
    ("Lengths consistent (BOLT/SCREW: 0 < LT <= L;  STUD: lt > 0, ld >= 0)",
     "IF(is_stud,AND(lt_g>0,ld_g>=0),AND(LT_f>0,LT_f<=L_f))"),
    ("Thread engagement length given", "IF(is_screw,N(Le_h)>0,N(Le_nut)>0)"),
    ("Materials: Ef > 0, 0 < Fty < Ftu", "AND(Ef>0,Fty>0,Ftu>Fty)"),
    ("Tightening: T > 0, K > 0, mu > 0, 0 <= Gamma < 1", "AND(T_tq>0,K_nut>0,mu_f>0,N(Gamma_s)>=0,N(Gamma_s)<1)"),
    ("Factors UF, FF, CF >= 1", "AND(UF_ult>=1,FF_fit>=1,CF_cast>=1)"),
]


def build(path=OUT):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wb = xlsxwriter.Workbook(path)
    wb.set_properties({"title": "Bolted Joint Tool", "subject": "Single fastener bolted joint analysis",
                       "comments": f"Version {VERSION}"})
    F = {}

    def fmt(name, **kw):
        base = {"font_name": "Calibri", "font_size": 10, "valign": "vcenter"}
        base.update(kw)
        F[name] = wb.add_format(base)
    fmt("title", bold=True, font_size=16, font_color="#1F4E78")
    fmt("sub", italic=True, font_color="#595959")
    fmt("sec", bold=True, bg_color="#1F4E78", font_color="white")
    fmt("hdr", bold=True, bg_color="#D9E1F2", border=1, text_wrap=True)
    fmt("txt", text_wrap=True)
    fmt("txtb", text_wrap=True, border=1, border_color="#BFBFBF")
    fmt("bold", bold=True)
    fmt("in", bg_color="#DDEBF7", border=1, border_color="#5B9BD5", locked=False, num_format="General")
    fmt("intxt", bg_color="#DDEBF7", border=1, border_color="#5B9BD5", locked=False)
    fmt("calc", bg_color="#F2F2F2", border=1, border_color="#BFBFBF", num_format="#,##0.000")
    fmt("calcg", bg_color="#F2F2F2", border=1, border_color="#BFBFBF", num_format="General")
    fmt("res", bg_color="#FFF2CC", border=1, border_color="#BF9000", num_format="0.00", bold=True, align="center")
    fmt("rest", bg_color="#FFF2CC", border=1, border_color="#BF9000", bold=True, align="center", text_wrap=True)
    fmt("big", bg_color="#FFF2CC", border=2, border_color="#BF9000", bold=True, font_size=13, align="center",
        num_format="0.00", text_wrap=True)
    fmt("small", font_size=9, font_color="#595959", text_wrap=True)
    fmt("pass", bg_color="#C6EFCE", font_color="#006100", bold=True)
    fmt("fail", bg_color="#FFC7CE", font_color="#9C0006", bold=True)
    fmt("na", bg_color="#EDEDED", font_color="#7F7F7F")
    fmt("ne", bg_color="#FCE4D6", font_color="#833C0B", bold=True)

    def status_cf(ws, rng):
        ws.conditional_format(rng, {"type": "text", "criteria": "begins with", "value": "FAIL", "format": F["fail"]})
        ws.conditional_format(rng, {"type": "text", "criteria": "begins with", "value": "CHECK", "format": F["fail"]})
        ws.conditional_format(rng, {"type": "text", "criteria": "begins with", "value": "INPUT", "format": F["fail"]})
        ws.conditional_format(rng, {"type": "text", "criteria": "begins with", "value": "PASS", "format": F["pass"]})
        ws.conditional_format(rng, {"type": "text", "criteria": "begins with", "value": "OK", "format": F["pass"]})
        ws.conditional_format(rng, {"type": "text", "criteria": "begins with", "value": "ALL OK", "format": F["pass"]})
        ws.conditional_format(rng, {"type": "text", "criteria": "begins with", "value": "N/A", "format": F["na"]})
        ws.conditional_format(rng, {"type": "text", "criteria": "begins with", "value": "INFO", "format": F["na"]})
        ws.conditional_format(rng, {"type": "text", "criteria": "begins with", "value": "NOT EVAL", "format": F["ne"]})

    readme = wb.add_worksheet("README")
    inp = wb.add_worksheet("Input")
    res = wb.add_worksheet("Results")
    calc = wb.add_worksheet("Calc")
    thr = wb.add_worksheet("Threads")
    exs = wb.add_worksheet("Examples")

    # ------------------------------------------------------------------ Threads
    rows = thread_table()
    thr.write_row(0, 0, ["Designation", "Standard", "d [mm]", "P [mm]", "d2 = dp [mm]", "d3 = dr [mm]"], F["hdr"])
    for i, r in enumerate(rows, start=1):
        thr.write_row(i, 0, r)
    n = len(rows)
    thr.write(n + 1, 0, "CUSTOM", F["bold"])
    thr.write(n + 1, 1, "type d, dp, dr in the override cells")
    thr.set_column(0, 0, 18)
    thr.set_column(1, 1, 30)
    thr.set_column(2, 5, 13)
    thr.freeze_panes(1, 0)
    thr.write(0, 7, "Notes", F["bold"])
    notes = [
        "ISO metric: d2 = d - 0.649519 P, d3 = d - 1.226869 P (ISO 724 basic profile). pi/4((d2+d3)/2)^2 = As of ISO 898-1.",
        "UNC / UNF: d2 = d - 0.649519 P, d3 = d - 1.299038 P = stress-area equivalent minor diameter (ASME B1.1 As).",
        "UNJF: Class 3A minimum pitch and minor diameters (conservative), d = basic size.",
        "Basic / minimum values. For a tolerance class enter the actual minimum diameters as overrides on Input.",
        "Rows can be added: insert them above the CUSTOM row (keep the CUSTOM row last).",
    ]
    for i, t in enumerate(notes, start=1):
        thr.write(i, 7, t)
    wb.define_name("thr_name", f"=Threads!$A$2:$A${n + 2}")
    wb.define_name("thr_d", f"=Threads!$C$2:$C${n + 2}")
    wb.define_name("thr_d2", f"=Threads!$E$2:$E${n + 2}")
    wb.define_name("thr_d3", f"=Threads!$F$2:$F${n + 2}")

    # ------------------------------------------------------------------ Input
    inp.set_column("A:A", 2)
    inp.set_column("B:B", 50)
    inp.set_column("C:C", 9)
    inp.set_column("D:D", 16)
    inp.set_column("E:E", 7)
    inp.set_column("F:F", 78)
    inp.set_column("G:G", 16)
    inp.set_column("H:H", 12)
    inp.write("B1", "BOLTED JOINT TOOL - INPUT", F["title"])
    inp.write("B2", "Fill the blue cells. Grey/yellow cells are calculated. Results are on sheet Results. "
                    "Units: N, mm, MPa, N.m.", F["sub"])
    inp.write_row(3, 1, ["Parameter", "Symbol", "Value", "Unit", "Description / where to get it", "Used by", "Table value"],
                  F["hdr"])
    r = 4
    cell_of = {}
    for spec in INPUTS:
        if spec[0] == "sec":
            inp.merge_range(r, 1, r, 7, spec[1], F["sec"])
            r += 1
            if spec[1].startswith("3."):
                # layer table
                inp.write_row(r, 1, ["Layer (top -> bottom). Top = under the head (BOLT/SCREW) or under the nut (STUD).",
                                     "#", "t [mm]", "", "Young's modulus E [MPa]", "", ""], F["hdr"])
                r += 1
                first = r
                for i in range(N_LAYERS):
                    nm, t, E = DEFAULT_LAYERS[i] if i < len(DEFAULT_LAYERS) else ("", None, None)
                    inp.write(r, 1, nm, F["intxt"])
                    inp.write(r, 2, i + 1)
                    if t is None:
                        inp.write_blank(r, 3, None, F["in"])
                    else:
                        inp.write_number(r, 3, t, F["in"])
                    inp.write(r, 4, "mm")
                    if E is None:
                        inp.write_blank(r, 5, None, F["in"])
                    else:
                        inp.write_number(r, 5, E, F["in"])
                    inp.data_validation(r, 3, r, 3, {"validate": "decimal", "criteria": ">=", "value": 0,
                                                     "ignore_blank": True})
                    r += 1
                wb.define_name("lay_t", f"=Input!$D${first + 1}:$D${r}")
                wb.define_name("lay_E", f"=Input!$F${first + 1}:$F${r}")
                wb.define_name("lay_name", f"=Input!$B${first + 1}:$B${r}")
                inp.merge_range(r, 1, r, 7, "Washers and plates are springs in series. Leave unused rows blank. "
                                "For SCREW / STUD the last layer is the housing, measured down to the end of the "
                                "engaged thread. See the joint sketch on the right.", F["small"])
                inp.set_row(r, 28)
                r += 1
            continue
        name, label, sym, default, unit, desc, used, kind = spec
        inp.write(r, 1, label)
        inp.write(r, 2, sym)
        if kind == "thread":
            inp.write(r, 3, default, F["intxt"])
            inp.data_validation(r, 3, r, 3, {"validate": "list", "source": "=thr_name"})
        elif isinstance(kind, tuple):
            inp.write(r, 3, default, F["intxt"])
            inp.data_validation(r, 3, r, 3, {"validate": "list", "source": kind[1]})
        elif default is None:
            inp.write_blank(r, 3, None, F["in"])
        else:
            inp.write_number(r, 3, default, F["in"])
        inp.write(r, 4, unit)
        inp.write(r, 5, desc, F["txt"])
        inp.write(r, 6, used, F["small"])
        wb.define_name(name, f"=Input!$D${r + 1}")
        cell_of[name] = (r, 3)
        tblmap = {"d_in": "tbl_d", "dp_in": "tbl_dp", "dr_in": "tbl_dr",
                  "ds_in": "tbl_ds", "dps_in": "tbl_dps", "drs_in": "tbl_drs"}
        if name in tblmap:
            inp.write_formula(r, 7, f"={tblmap[name]}", F["calc"])
        if len(desc) > 95:
            inp.set_row(r, 27)
        r += 1
    # checks
    r += 1
    inp.merge_range(r, 1, r, 7, "INPUT CHECKS - all must read OK", F["sec"])
    r += 1
    chk_first = r
    for desc, cond in CHECKS:
        inp.write(r, 1, desc)
        inp.merge_range(r, 3, r, 5, "", F["calcg"])
        inp.write_formula(r, 3, f'=IF(IFERROR({cond},FALSE),"OK","CHECK - {desc}")', F["calcg"])
        r += 1
    wb.define_name("chk_list", f"=Input!$D${chk_first + 1}:$D${r}")
    inp.write(r, 1, "ALL INPUT CHECKS", F["bold"])
    inp.write_formula(r, 3, f'=IF(COUNTIF(chk_list,"OK")={len(CHECKS)},"ALL OK","CHECK INPUTS")', F["rest"])
    wb.define_name("chk_all", f"=Input!$D${r + 1}")
    status_cf(inp, f"D{chk_first + 1}:D{r + 1}")
    fig = os.path.join(os.path.dirname(OUT), "..", "docs", "figures", "bj_configurations.png")
    if os.path.exists(fig):
        inp.write("J4", "JOINT SKETCH - symbols used on this sheet", F["bold"])
        inp.insert_image("J5", fig, {"x_scale": 0.55, "y_scale": 0.55, "object_position": 3})
    inp.freeze_panes(4, 0)
    inp.set_landscape()
    inp.fit_to_pages(1, 0)
    inp.print_area(0, 0, r, 7)

    # ------------------------------------------------------------------ Calc
    calc.set_column("A:A", 2)
    calc.set_column("B:B", 46)
    calc.set_column("C:C", 9)
    calc.set_column("D:D", 15)
    calc.set_column("E:E", 7)
    calc.set_column("F:F", 52)
    calc.set_column("G:L", 14)
    calc.write("B1", "BOLTED JOINT TOOL - CALCULATION", F["title"])
    calc.write("B2", "Every value is a live formula using named cells (Formulas > Name Manager). Do not type here.", F["sub"])
    calc.write_row(3, 1, ["Quantity", "Symbol", "Value", "Unit", "Equation", "Note"], F["hdr"])
    r = 4
    for spec in CALC:
        if spec[0] == "sec":
            calc.merge_range(r, 1, r, 6, spec[1], F["sec"])
            r += 1
            if spec[1].startswith("D."):
                # layer table
                hdr = ["Layer", "#", "t", "E", "z,top", "z,bot", "t,upper", "D,upper", "t,lower", "D,lower",
                       "compliance [mm/N]"]
                calc.write_row(r, 1, hdr, F["hdr"])
                r += 1
                first = r
                last = r + N_LAYERS
                # columns: B name, C #, D t, E E, F ztop, G zbot, H tu, I Du, J tl, K Dl, L compliance
                for i in range(N_LAYERS):
                    row = first + i
                    rr = row + 1
                    calc.write_number(row, 2, i + 1)
                    calc.write_formula(row, 1, f'=IF(N(INDEX(lay_t,{i + 1}))>0,INDEX(lay_name,{i + 1}),"")', F["calcg"])
                    calc.write_formula(row, 3, f"=N(INDEX(lay_t,{i + 1}))", F["calc"])
                    calc.write_formula(row, 4, f"=N(INDEX(lay_E,{i + 1}))", F["calcg"])
                    calc.write_formula(row, 5, f"=SUM($D${first + 1}:D{rr})-D{rr}", F["calc"])
                    calc.write_formula(row, 6, f"=F{rr}+D{rr}", F["calc"])
                    calc.write_formula(row, 7, f"=MAX(0,MIN(G{rr},l_grip/2)-F{rr})", F["calc"])
                    calc.write_formula(row, 8, f"=Dw_top+2*F{rr}*tanA", F["calc"])
                    calc.write_formula(row, 9, f"=D{rr}-H{rr}", F["calc"])
                    calc.write_formula(row, 10, f"=Dw_bot+2*(l_grip-G{rr})*tanA", F["calc"])
                    fr = ("IF({t}<=0,0,LN((2*{t}*tanA+{D}-d_u)*({D}+d_u)/((2*{t}*tanA+{D}+d_u)*({D}-d_u)))"
                          "/(PI()*tanA*E{rr}*d_u))")
                    calc.write_formula(row, 11, "=" + fr.format(t=f"H{rr}", D=f"I{rr}", rr=rr) + "+" +
                                       fr.format(t=f"J{rr}", D=f"K{rr}", rr=rr), wb.add_format(
                                           {"bg_color": "#F2F2F2", "border": 1, "border_color": "#BFBFBF",
                                            "num_format": "0.000E+00", "font_size": 10}))
                wb.define_name("lay_c", f"=Calc!$L${first + 1}:$L${last}")
                calc.merge_range(last, 1, last, 11,
                                 "Each layer is split at mid-grip. The upper part belongs to the cone from the top bearing "
                                 "face (D,upper = Dw,top + 2 z,top tan a), the lower part to the cone from the bottom face "
                                 "(D,lower = Dw,bot + 2 (l - z,bot) tan a). Frustum: 1/k = ln[(2t tan a + D - d)(D + d) / "
                                 "((2t tan a + D + d)(D - d))] / (pi tan a E d).", F["small"])
                calc.set_row(last, 40)
                r = last + 1
            continue
        name, desc, sym, formula, unit, eq, note = spec
        calc.write(r, 1, desc)
        calc.write(r, 2, sym)
        f = F["calcg"] if name.startswith("is_") else F["calc"]
        calc.write_formula(r, 3, formula, f)
        calc.write(r, 4, unit)
        calc.write(r, 5, eq, F["small"])
        calc.write(r, 6, note, F["small"])
        wb.define_name(name, f"=Calc!$D${r + 1}")
        r += 1

    # reserve factors block
    r += 1
    calc.merge_range(r, 1, r, 6, "H. Reserve factors (blank = not applicable / input missing)", F["sec"])
    r += 1
    calc.write_row(r, 1, ["Failure mode", "ID", "RF", "Applies?", "Criterion", "Input missing?"], F["hdr"])
    r += 1
    for fid, nm, appl, app, miss, rf, crit, req, mean in FMODES:
        calc.write(r, 1, nm)
        calc.write(r, 2, fid)
        calc.write_formula(r, 4, f"={app}", F["calcg"])
        calc.write_formula(r, 6, f"={miss}", F["calcg"])
        calc.write_formula(r, 3, f'=IF(OR(NOT(E{r + 1}),G{r + 1}),"",{rf})', F["calc"])
        calc.write(r, 5, crit, F["small"])
        wb.define_name(f"rf_{fid}", f"=Calc!$D${r + 1}")
        wb.define_name(f"app_{fid}", f"=Calc!$E${r + 1}")
        wb.define_name(f"miss_{fid}", f"=Calc!$G${r + 1}")
        r += 1
    calc.freeze_panes(4, 0)
    calc.set_landscape()
    calc.fit_to_pages(1, 0)

    # ------------------------------------------------------------------ Results
    res.set_column("A:A", 2)
    res.set_column("B:B", 7)
    res.set_column("C:C", 36)
    res.set_column("D:D", 15)
    res.set_column("E:E", 10)
    res.set_column("F:F", 16)
    res.set_column("G:G", 46)
    res.set_column("H:H", 24)
    res.set_column("I:I", 60)
    res.write("B1", "BOLTED JOINT TOOL - RESULTS", F["title"])
    res.write("B2", "Every failure mode is always listed. N/A = does not apply to this configuration. "
                    "NOT EVALUATED = optional input missing (see column H). RF >= 1 required.", F["sub"])
    res.write("C4", "Input checks", F["bold"])
    res.merge_range("D4:E4", "", F["rest"])
    res.write_formula("D4", "=chk_all", F["rest"])
    res.write("C5", "Configuration", F["bold"])
    res.merge_range("D5:E5", "", F["rest"])
    res.write_formula("D5", '=ftype&"  /  "&thread_n', F["rest"])
    res.write("C6", "GOVERNING RESERVE FACTOR", F["bold"])
    res.merge_range("D6:E6", "", F["big"])
    res.write("C7", "Governing failure mode", F["bold"])
    res.merge_range("D7:G7", "", F["rest"])
    res.write("C8", "OVERALL STATUS", F["bold"])
    res.merge_range("D8:G8", "", F["big"])
    r0 = 10
    res.write_row(r0, 1, ["ID", "Failure mode", "RF", "Status", "Applies to", "Criterion", "Required inputs",
                          "What it means"], F["hdr"])
    r = r0 + 1
    first = r
    for fid, nm, appl, app, miss, rf, crit, req, mean in FMODES:
        res.write(r, 1, fid, F["bold"])
        res.write(r, 2, nm, F["txtb"])
        res.write_formula(r, 3, f"=rf_{fid}", F["res"])
        res.write_formula(r, 4, f'=IF(NOT(app_{fid}),"N/A",IF(miss_{fid},"NOT EVALUATED",IF(rf_{fid}>=1,"PASS","FAIL")))',
                          F["rest"])
        res.write(r, 5, appl, F["small"])
        res.write(r, 6, crit, F["small"])
        res.write(r, 7, req, F["small"])
        res.write(r, 8, mean, F["small"])
        res.set_row(r, 38)
        r += 1
    last_rf = r
    for fid, nm, appl, mean in INFO_MODES:
        res.write(r, 1, fid, F["bold"])
        res.write(r, 2, nm, F["txtb"])
        res.write(r, 3, "", F["res"])
        res.write(r, 4, "INFO", F["rest"])
        res.write(r, 5, appl, F["small"])
        res.write(r, 6, "qualitative", F["small"])
        res.write(r, 7, "-", F["small"])
        res.write(r, 8, mean, F["small"])
        res.set_row(r, 38)
        r += 1
    status_cf(res, f"E{first + 1}:E{r}")
    status_cf(res, "D4:D4")
    status_cf(res, "D8:D8")
    rf_rng = f"$D${first + 1}:$D${last_rf}"
    st_rng = f"$E${first + 1}:$E${last_rf}"
    nm_rng = f"$C${first + 1}:$C${last_rf}"
    res.write_formula("D6", f'=IF(COUNT({rf_rng})=0,"",MIN({rf_rng}))', F["big"])
    res.write_formula("D7", f'=IF(D6="","",INDEX({nm_rng},MATCH(D6,{rf_rng},0)))', F["rest"])
    res.write_formula(
        "D8",
        f'=IF(chk_all<>"ALL OK","INPUT ERROR - see input checks",IF(COUNTIF({st_rng},"FAIL")>0,"FAIL - "&D7,'
        f'IF(COUNTIF({st_rng},"NOT EVALUATED")>0,"PASS - "&COUNTIF({st_rng},"NOT EVALUATED")&'
        f'" optional mode(s) not evaluated","PASS - all applicable modes")))', F["big"])
    wb.define_name("RF_gov", "=Results!$D$6")
    wb.define_name("status_all", "=Results!$D$8")
    res.conditional_format(f"D{first + 1}:D{last_rf}", {"type": "formula",
                                                        "criteria": f"=AND(ISNUMBER(D{first + 1}),D{first + 1}<1)",
                                                        "format": F["fail"]})
    # torque window + key values
    r += 1
    res.merge_range(r, 2, r, 4, "TIGHTENING TORQUE WINDOW", F["sec"])
    r += 1
    for lab, nm, u in [("Applied torque T", "T_tq", "N.m"), ("Minimum torque Tmin", "T_min", "N.m"),
                       ("Maximum torque Tmax", "T_max", "N.m")]:
        res.write(r, 2, lab)
        res.write_formula(r, 3, f"={nm}", F["res"])
        res.write(r, 4, u)
        r += 1
    res.merge_range(r, 2, r, 8, "Tmin: no separation and no slip at ultimate with minimum preload. Tmax: maximum "
                    "preload reaches RF = 1 in yield, ultimate or thread stripping. Tmin > Tmax: no torque satisfies both.",
                    F["small"])
    r += 2
    res.merge_range(r, 2, r, 4, "KEY INTERMEDIATE VALUES", F["sec"])
    r += 1
    for lab, nm, u in [("Nominal preload Fpre", "Fpre", "N"), ("Maximum preload", "Fpre_max", "N"),
                       ("Minimum preload", "Fpre_min", "N"), ("Fastener stiffness kf", "kf", "N/mm"),
                       ("Member stiffness km", "km", "N/mm"), ("Joint constant C = kf/(kf+km)", "C_j", "-"),
                       ("Fastener share of Pex, Pf", "Pf", "N"), ("Separating force Pm", "Pm", "N"),
                       ("Grip length l", "l_grip", "mm"), ("Tensile stress area At", "At_g", "mm2")]:
        res.write(r, 2, lab)
        res.write_formula(r, 3, f"={nm}", F["calc"])
        res.write(r, 4, u)
        r += 1
    res.freeze_panes(r0 + 1, 0)
    res.set_landscape()
    res.fit_to_pages(1, 0)

    # ------------------------------------------------------------------ Examples
    exs.set_column("A:A", 2)
    exs.set_column("B:B", 44)
    exs.set_column("C:E", 18)
    exs.write("B1", "EXAMPLES - regression cases", F["title"])
    exs.write("B2", "Type a column into Input to reproduce it. Expected results come from the independent Python "
                    "implementation (handcalc/bolted_joint.py); the automated tests check the workbook against it.",
              F["sub"])
    cases = list(ex.ALL.items())
    exs.write_row(3, 1, ["Input"] + [c[0] for c in cases], F["hdr"])
    r = 4
    fields = [("Fastener type", "fastener_type"), ("d", "d"), ("dp", "dp"), ("dr", "dr"), ("d,s", "d_s"),
              ("dp,s", "dp_s"), ("dr,s", "dr_s"), ("Shank diameter", "d_shank"), ("L", "L"), ("LT", "LT"),
              ("LT,s", "LT_s"), ("Le,nut", "Le_nut"), ("Le,h", "Le_h"), ("Dw,top", "Dw_top"), ("Dw,bot", "Dw_bot"),
              ("Ef", "Ef"), ("Fty", "Fty"), ("Ftu", "Ftu"), ("Fsu", "Fsu"), ("Fsu,h", "Fsu_h"), ("Pex", "Pex"),
              ("Pshear", "Pshear"), ("UF", "UF"), ("FF", "FF"), ("CF", "CF"), ("T [N.m]", "T"), ("K", "K"),
              ("mu", "mu"), ("Gamma", "Gamma"), ("fz", "fz"), ("Threads in shear plane", "threads_in_shear_plane"),
              ("Dh", "D_hole"), ("p,allow", "p_allow"), ("t,min", "t_min"), ("Fbru", "Fbru"), ("Pa", "P_alt"),
              ("Pm,cyc", "P_mean"), ("Se", "Se")]
    for lab, attr in fields:
        exs.write(r, 1, lab)
        for j, (_, c) in enumerate(cases):
            v = getattr(c, attr)
            if isinstance(v, bool):
                v = "YES" if v else "NO"
            if v is not None:
                exs.write(r, 2 + j, v)
        r += 1
    exs.write(r, 1, "Layers top -> bottom (t / E)")
    for j, (_, c) in enumerate(cases):
        exs.write(r, 2 + j, "; ".join(f"{L.t:g} / {L.E:g}" for L in c.layers), F["txt"])
    exs.set_row(r, 40)
    r += 2
    exs.write_row(r, 1, ["Expected result"] + [c[0] for c in cases], F["hdr"])
    r += 1
    results = [analyse(c) for _, c in cases]
    for key, lab in [("kf", "kf [N/mm]"), ("km", "km [N/mm]"), ("Fpre", "Fpre [N]"), ("T_min", "Tmin [N.m]"),
                     ("T_max", "Tmax [N.m]")]:
        exs.write(r, 1, lab)
        for j, rr in enumerate(results):
            exs.write_number(r, 2 + j, round(rr[key], 3))
        r += 1
    for fid, nm, *_ in FMODES:
        exs.write(r, 1, f"{fid} {nm}")
        for j, rr in enumerate(results):
            v, st = rr["fm"][fid]
            exs.write(r, 2 + j, round(v, 3) if v is not None else st)
        r += 1
    exs.write(r + 1, 1, "DOC_STUD reproduces the worked example of the in-house method document "
                        "(Table 5: km = 620 902 N/mm, kf = 351 941 N/mm).", F["small"])

    # ------------------------------------------------------------------ README
    readme.set_column("A:A", 2)
    readme.set_column("B:B", 120)
    lines = [
        ("title", f"BOLTED JOINT TOOL  -  single fastener  -  version {VERSION}"),
        ("sub", "Static strength, separation, slip, fatigue and tightening-torque window of one bolted joint "
                "(BOLT, SCREW or STUD). Units: N, mm, MPa, torque in N.m."),
        ("sec", "HOW TO USE"),
        ("txt", "1. Sheet Input: fill the blue cells from top to bottom. Pick the fastener type and the thread from the "
                "lists. The description column says what every input is and where it comes from."),
        ("txt", "2. Fill the joint stack table (washers and plates from the head/nut down). "
                "Leave unused rows blank."),
        ("txt", "3. Check that INPUT CHECKS at the bottom of Input reads ALL OK."),
        ("txt", "4. Sheet Results: every failure mode is listed with its RF and status, plus the governing mode and "
                "the allowable tightening-torque window."),
        ("txt", "5. Sheet Calc shows every intermediate value with its equation. Sheet Threads holds the thread "
                "tables; sheet Examples holds regression cases."),
        ("sec", "STATUS VALUES"),
        ("txt", "PASS / FAIL: RF >= 1 / RF < 1.   N/A: the mode does not exist for this configuration "
                "(e.g. nut thread for a SCREW).   NOT EVALUATED: an optional input is blank; the mode is real, "
                "fill the input listed in 'Required inputs' to evaluate it.   INFO: qualitative mode, guidance only."),
        ("sec", "COLOUR CODE"),
        ("txt", "Blue = input.  Grey = calculated.  Yellow = result.  Green / red = pass / fail."),
        ("sec", "METHOD (full description in the user manual docs/Bolted_Joint_Tool.docx)"),
        ("txt", "Fastener stiffness: springs in series (thread in grip, shank; stud: + stud-end thread). "
                "Member stiffness: 30 deg pressure cones from both bearing faces meeting at mid-grip; every layer is "
                "split at the mid-plane and treated as a frustum; frusta in series."),
        ("txt", "Load sharing: C = kf/(kf+km); fastener carries Pf = C Pex, members lose Pm = (1-C) Pex. "
                "Preload Fpre = T/(K d); scatter Gamma gives Fpre,max for strength and Fpre,min for separation/slip."),
        ("txt", "Thread stripping: RF = Fsu / (1.5 . FF (or CF) . (Fpre + Pf)/As) with As = pi dp (5/8) Le (nut) or "
                "pi dp (3/4) Le (housing); the weaker mating material governs."),
        ("sec", "EDITING"),
        ("txt", "Nothing is locked or hidden. Formulas use named cells (Formulas > Name Manager), e.g. =Fty/(FF_fit*sig_lim). "
                "If you change a formula, re-run the automated tests (see repository README) to confirm the "
                "reference examples still match."),
    ]
    for i, (k, t) in enumerate(lines):
        readme.write(i, 1, t, F[k])
        if k == "txt":
            readme.set_row(i, 30)
    readme.activate()
    wb.close()
    return path


if __name__ == "__main__":
    print(build())
