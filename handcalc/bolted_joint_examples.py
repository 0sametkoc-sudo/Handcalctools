"""Example input cases for the bolted joint tool (used by the tests and the Examples sheet)."""
from handcalc.bolted_joint import BoltedJointInput, Layer

# Worked example of the in-house method document (stud into housing, Fig. 3 / Tables 2-5).
DOC_STUD = BoltedJointInput(
    fastener_type="STUD", d=7.75, d_shank=7.887,  # Table 4: Ad = 48.85 mm2
    dp=7.18, dr=6.58, d_s=11.11, dp_s=10.33, dr_s=9.40,
    Pex=627, Pshear=1008, T=20, K=0.2, mu=0.2,
    L=43.82, LT=17.48, LT_s=13.95, Le_nut=6.5,
    layers=[Layer(0.8128, 199948, "Washer 1"), Layer(0.8128, 68258, "Washer 2"),
            Layer(12, 71000, "Plate 1"), Layer(17.62, 71000, "Housing")],
    Dw_top=13.21, Dw_bot=13.21, Ef=199948, Fty=871, Ftu=1103, Fsu=636, Fsu_h=165,
    UF=1.5, FF=1.15, CF=1.0)

# Bolt sheet example of the previous Bolted_Joint_Tool (M12x1.75, two washers under the head).
OLD_BOLT = BoltedJointInput(
    fastener_type="BOLT", d=12, dp=10.863, dr=9.853, Pex=1800, Pshear=10, T=131, K=0.2, mu=0.2,
    L=50, LT=38, Le_nut=10,
    layers=[Layer(3, 210000), Layer(3, 210000), Layer(12, 210000), Layer(21.245, 210000)],
    Dw_top=18, Dw_bot=18, Ef=207000, Fty=1080, Ftu=1200, Fsu=720, UF=1.5, FF=1.0)

SCREW_M16 = BoltedJointInput(
    fastener_type="SCREW", d=16, dp=14.701, dr=13.84, Pex=100, Pshear=300, T=90, K=0.15, mu=0.12,
    L=50, LT=38, Le_h=16,
    layers=[Layer(3, 210000), Layer(20, 210000), Layer(26, 210000)],
    Dw_top=30, Dw_bot=30, Ef=207000, Fty=1170, Ftu=1300, Fsu=780, Fsu_h=213,
    UF=1.5, FF=1.15, CF=1.0, D_hole=17, p_allow=700, t_min=20, Fbru=900,
    P_alt=50, P_mean=50, Se=162, Gamma=0.25, fz=0.008, threads_in_shear_plane=True)

ALL = {"DOC_STUD": DOC_STUD, "OLD_BOLT": OLD_BOLT, "SCREW_M16": SCREW_M16}
