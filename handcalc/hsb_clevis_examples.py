"""Example cases for the HSB clevis tool (tests and the Examples sheet)."""
from handcalc.hsb_clevis import Lug

# HSB 26101-01 Issue E worked example (pages 7-8): female and male lug of one double-shear joint.
HSB_FEMALE = Lug(d=24, r=24, h=24, e=24, w=24, t=5, Rm=430, Rp02=290, Rbry15=495, Rbry20=595,
                 beta=45, phi=30, bushing=True, da=16, Rc02=600, name="female")
HSB_MALE = Lug(d=26, r=24, h=24, e=24, w=24, t=12, Rm=470, Rp02=395, Rbry15=560, Rbry20=670,
               beta=0, phi=0, bushing=True, da=16, Rc02=600, name="male")
HSB_J = 1.5

# published results: (female, male)
PUBLISHED = {
    "Ktb1": (2.6987, 3.0786), "H": (1.0, 1.0), "Ktb": (2.6987, 3.0786), "KBR": (0.8349, 0.715),
    "F_Lu": (36188, 88072), "F_Ly1": (52200, 156420), "ratio": (0.701, 0.6), "C": (1.1, 1.1),
    "F_Ly2": (40270, 122130), "Rbry": (247.5, 236.9), "F_Lybr": (44550, 110869), "F_B": (133200, 319680),
}

# second case: eccentric, partly transverse, no bushing on the female lug (exercises the other branches)
ECC_FEMALE = Lug(d=20, r=26, h=34, e=34, w=30, t=8, Rm=480, Rp02=420, Rbry15=650, Rbry20=800,
                 beta=20, phi=60, bushing=False, name="female")
ECC_MALE = Lug(d=20, r=22, h=22, e=40, w=25, t=14, Rm=1000, Rp02=900, Rbry15=1300, Rbry20=1600,
               beta=0, phi=75, bushing=True, da=14, Rc02=700, name="male")
