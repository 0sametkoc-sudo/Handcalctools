"""AFSAM Section 9 worked examples (imperial data converted to SI) used by tests and the Examples sheet."""
from handcalc.afsam_lug import AxialLug, DoubleShearJoint

KSI = 6.89476
IN = 25.4


def ex96(auto_charts=False):
    """AFSAM 9.6: 2024-T351 outer lugs, 7075-T651 inner lug, Al-bronze bushings, 4130 pin.
    With auto_charts=False the published chart readings (K 1.46/1.33, Kn 0.74/0.87) are used."""
    outer = AxialLug(D=1.0 * IN, e=1.25 * IN, w=2.5 * IN, t=0.5 * IN, Ftux=64 * KSI, Ftyx=40 * KSI,
                     E=10.5e3 * KSI, eu=0.12, Fcy_B=60 * KSI,
                     K=None if auto_charts else 1.46, Kn=None if auto_charts else 0.74)
    inner = AxialLug(D=1.0 * IN, e=1.5 * IN, w=3.0 * IN, t=0.75 * IN, Ftux=77 * KSI, Ftyx=66 * KSI,
                     E=10.3e3 * KSI, eu=0.09, Fcy_B=60 * KSI,
                     K=None if auto_charts else 1.33, Kn=None if auto_charts else 0.87)
    return DoubleShearJoint(outer=outer, inner=inner, Dp=0.75 * IN, Fsu_P=82 * KSI, Ftu_P=125 * KSI, kb_P=1.56,
                            g=0.10 * IN, Ftu_T1=64 * KSI, wT1=2.5 * IN, Ftu_T2=77 * KSI, wT2=3.0 * IN, kb_T=1.4,
                            variant=1, P_limit=20000.0, UF=1.5, FF=1.15)


# published answers of 9.6 (converted to N / mm), from the AFSAM text
PUB_96 = dict(outer_Pbru=127219.138, outer_PuB=130332.893, outer_PuLB=127219.138, inner_Pbru=342513.064,
              inner_PuB=195721.751, inner_PuLB=195721.751, PuLB=195721.751, Pus=322051.245, Pub=133891.471,
              C=5078.678, Pubmax=168587.599, b1=8.4074, b2=16.4084, P_all=168587.599, PT1=412350.144,
              PT2=770876.806)
CHART_96 = dict(K_outer=1.46, K_inner=1.33, Kn_outer=0.74, Kn_inner=0.87)

# AFSAM 9.14.1.3 design example
DESIGN_9141 = dict(P=168587.599218373, Ftux1=64 * KSI, Ftyx1=40 * KSI, Ftux2=77 * KSI, Ftyx2=66 * KSI,
                   FcyB1=60 * KSI, FcyB2=60 * KSI, Fsu_P=82 * KSI, Ftu_P=125 * KSI, kb_P=1.56, g=0.1 * IN,
                   tB=0.125 * IN, K=1.02, D_Dp=1.0, eD=1.24, t1=0.339 * IN, t2=0.654 * IN)
PUB_9141 = dict(fb1=366.11161226724, fb2=539.170020325766, R=3.4, Dp_shear=13.7414, Dp_bend1=18.8214,
                D=25.1714, aD=0.74, wD=2.48, Dp_bend2=19.177, Dp_opt=19.05)
