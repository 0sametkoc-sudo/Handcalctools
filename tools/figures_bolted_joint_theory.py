"""Theory figures for the bolted joint manual (derivations, diagrams, example plots).

python tools/figures_bolted_joint_theory.py  ->  docs/figures/bjt_*.png
"""
import dataclasses
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from handcalc.bolted_joint import analyse  # noqa: E402
from handcalc.bolted_joint_examples import DOC_STUD  # noqa: E402

OUT = os.path.join(ROOT, "docs", "figures")
C_PLATE, C_PLATE2, C_BOLT, C_THREAD = "#BDD7EE", "#9DC3E6", "#F4B183", "#C55A11"
C_DIM, C_RED, C_GREEN, C_BLUE = "#1F4E78", "#C00000", "#548235", "#2E75B6"
plt.rcParams.update({"font.size": 9})


def arrow(ax, x0, y0, x1, y1, color="k", lw=1.2, style="-|>", ms=10):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=ms, color=color, lw=lw))


def dim(ax, x0, y0, x1, y1, text, color=C_DIM, off=(0.1, 0), ha="left"):
    ax.annotate("", xy=(x0, y0), xytext=(x1, y1), arrowprops=dict(arrowstyle="<->", color=color, lw=0.8))
    ax.text((x0 + x1) / 2 + off[0], (y0 + y1) / 2 + off[1], text, color=color, ha=ha, va="center", fontsize=8.5)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=170, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- spring model
def spring(ax, x, y0, y1, n=6, w=0.25, color="k"):
    ys = np.linspace(y0, y1, 2 * n + 3)
    xs = [x] + [x + (w if i % 2 else -w) for i in range(2 * n + 1)] + [x]
    ax.plot(xs, ys, color=color, lw=1.4)


def spring_model():
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.8), gridspec_kw={"width_ratios": [1, 1.2]})
    ax = axs[0]
    ax.add_patch(Rectangle((-1.6, 3.0), 3.2, 0.25, fc="#D9D9D9", ec="k"))
    ax.add_patch(Rectangle((-1.6, 0.0), 3.2, 0.25, fc="#D9D9D9", ec="k"))
    spring(ax, -0.8, 0.25, 3.0, color=C_THREAD)
    spring(ax, 0.8, 0.25, 3.0, color=C_BLUE)
    ax.text(-1.15, 1.6, "kf\nfastener\n(tension)", ha="right", va="center", color=C_THREAD, fontsize=8.5)
    ax.text(1.15, 1.6, "km\nmembers\n(compression)", ha="left", va="center", color=C_BLUE, fontsize=8.5)
    arrow(ax, 0, 3.25, 0, 4.1)
    arrow(ax, 0, 0.0, 0, -0.85)
    ax.text(0.1, 3.85, "Pex", fontsize=9)
    ax.text(0.1, -0.6, "Pex", fontsize=9)
    ax.set_xlim(-3, 3)
    ax.set_ylim(-1.1, 4.3)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Parallel springs, same extra deformation", fontsize=9.5)
    ax = axs[1]
    ax.axis("off")
    txt = (r"Compatibility: both springs change length by the same $\Delta\delta$" "\n\n"
           r"$\Delta F_f = k_f\,\Delta\delta$  (fastener force increases)" "\n"
           r"$\Delta F_m = k_m\,\Delta\delta$  (clamp force decreases)" "\n\n"
           r"Equilibrium:  $\Delta F_f + \Delta F_m = P_{ex}$" "\n\n"
           r"$\Rightarrow\ \Delta\delta = \dfrac{P_{ex}}{k_f + k_m}$" "\n\n"
           r"$P_f = \Delta F_f = \dfrac{k_f}{k_f+k_m}P_{ex} = C\,P_{ex}$" "\n"
           r"$P_m = \Delta F_m = (1-C)\,P_{ex}$" "\n\n"
           r"Valid while the joint is closed ($F_{pre} > P_m$).")
    ax.text(0.0, 0.5, txt, va="center", fontsize=9.5)
    save(fig, "bjt_spring_model.png")


# --------------------------------------------------------------------------- frustum derivation
def frustum_derivation():
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    D, d, t, ta = 2.0, 1.0, 2.2, np.tan(np.radians(30))
    Do = D + 2 * t * ta
    for s in (1, -1):
        ax.add_patch(Polygon([(s * d / 2, 0), (s * D / 2, 0), (s * Do / 2, -t), (s * d / 2, -t)],
                             fc="#FFE699", ec="#BF9000"))
    x = 1.1
    rx = D / 2 + x * ta
    for s in (1, -1):
        ax.add_patch(Rectangle((min(s * d / 2, s * rx), -x - 0.12), abs(rx - d / 2), 0.12, fc=C_BLUE, alpha=0.6))
    ax.plot([0, 0], [0.6, -t - 0.6], ls="-.", color="grey", lw=0.8)
    dim(ax, -D / 2, 0.25, D / 2, 0.25, "D (smallest diameter)", off=(0, 0.18), ha="center")
    dim(ax, -d / 2, -t - 0.3, d / 2, -t - 0.3, "d", off=(0, -0.18), ha="center")
    dim(ax, Do / 2 + 0.3, 0, Do / 2 + 0.3, -t, "t")
    dim(ax, -Do / 2 - 0.3, 0, -Do / 2 - 0.3, -x, "x", ha="right", off=(-0.1, 0))
    ax.text(rx + 0.15, -x - 0.05, r"element $dx$, radius $r(x) = D/2 + x\tan\alpha$", fontsize=8.5, color=C_BLUE)
    ax.text(D / 2 + 0.05, -0.55, r"$\alpha$", fontsize=10)
    ax.set_xlim(-3.3, 5.2)
    ax.set_ylim(-t - 0.8, 0.8)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "bjt_frustum.png")


# --------------------------------------------------------------------------- similar triangles stack
def similar_triangles():
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ta = np.tan(np.radians(30))
    layers = [("washer 1", 0.35, "#404040"), ("washer 2", 0.35, "#7F7F7F"), ("plate 1", 2.0, C_PLATE),
              ("housing", 2.8, C_PLATE2)]
    l = sum(t for _, t, _ in layers)
    Dw, d, W = 2.4, 1.0, 5.5
    y = l
    zs = []
    for name, t, c in layers:
        ax.add_patch(Rectangle((-W, y - t), W - d / 2, t, fc=c, ec="k", lw=0.5))
        ax.add_patch(Rectangle((d / 2, y - t), W - d / 2, t, fc=c, ec="k", lw=0.5))
        zs.append((name, l - y, t))
        y -= t
    mid = l / 2
    Dm = Dw + 2 * mid * ta
    for s in (1, -1):
        ax.plot([s * Dw / 2, s * Dm / 2, s * Dw / 2], [l, mid, 0], color="#BF9000", lw=1.3)
    ax.plot([-W, W], [mid, mid], ls="--", color=C_RED, lw=1)
    ax.text(-W + 1.2, mid + 0.12, "mid-plane l/2", color=C_RED, va="bottom", fontsize=8.5)
    # diameter labels at top of each layer
    for name, z, t in zs:
        Dz = Dw + 2 * z * ta
        yy = l - z
        if z < mid:
            ax.plot([Dz / 2, W + 0.05], [yy, yy], color="grey", lw=0.4)
        ax.text(-W + 0.1, yy - min(t, 0.9) / 2 - 0.02, name, fontsize=8, va="center",
                color="white" if "washer" in name else "k")
    ax.text(W + 0.1, l, r"$D_{w1} = D_{w,top}$", fontsize=8.5, va="center")
    ax.text(W + 0.1, l - 0.35, r"$D_{w2} = D_{w1}(h_u + t_{w1})/h_u$", fontsize=8.5, va="center")
    ax.text(W + 0.1, l - 0.85, r"$D_{n1} = D_{w1}(h_u + t_{w1} + t_{w2})/h_u$", fontsize=8.5, va="center")
    ax.text(W + 0.1, l - 2.7, r"$D^{*} = D_{w1}(h_u + t_{w1} + t_{w2} + t_1)/h_u$", fontsize=8.5, va="center")
    ax.text(W + 0.1, 0.1, r"$D_{n2} = D_{w,bot}$ (bottom cone)", fontsize=8.5, va="center")
    # apex
    hu = Dw / (2 * ta)
    ax.plot([-Dw / 2, 0, Dw / 2], [l, l + hu, l], ls=":", color="#BF9000")
    dim(ax, -0.3, l, -0.3, l + hu, r"$h_u = \dfrac{D_{w,top}}{2\tan\alpha}$", ha="right", off=(-0.15, 0))
    ax.set_xlim(-W - 0.2, W + 4.6)
    ax.set_ylim(-0.3, l + hu + 0.3)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "bjt_similar_triangles.png")


# --------------------------------------------------------------------------- thread shear
def thread_shear():
    fig, ax = plt.subplots(figsize=(8, 3.6))
    P, H = 1.0, 0.866
    x = np.arange(-0.5, 5.6, P)
    # external thread profile (fastener) teeth pointing up
    prof_x, prof_y = [], []
    for xi in x:
        prof_x += [xi, xi + P / 2, xi + P]
        prof_y += [0, 0.62, 0]
    ax.fill_between(prof_x, -0.6, prof_y, color=C_BOLT, ec=C_THREAD)
    # internal (nut / housing) above
    ax.fill_between(prof_x, [y + 0.12 for y in prof_y], 1.4, color=C_PLATE, ec="k", lw=0.5)
    ax.plot([-0.5, 5.6], [0.31, 0.31], ls="--", color=C_RED, lw=1)
    ax.text(5.65, 0.31, r"pitch line $d_p$ (shear cylinder)", color=C_RED, va="center", fontsize=8.5)
    ax.text(5.65, -0.3, "fastener (external thread)", va="center", fontsize=8.5)
    ax.text(5.65, 1.05, "nut / housing (internal thread)", va="center", fontsize=8.5)
    dim(ax, 0.0, -0.75, 4.0, -0.75, r"engaged length $L_e$", off=(0, -0.15), ha="center")
    dim(ax, 0.0, 1.55, 1.0, 1.55, r"$P$", off=(0, 0.15), ha="center")
    ax.set_xlim(-0.7, 8.6)
    ax.set_ylim(-1.1, 1.9)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(r"Shear area = $\pi\,d_p\,L_e\times$ (fraction of the engaged length that is solid material "
                 r"on the shear cylinder)", fontsize=9)
    save(fig, "bjt_thread_shear.png")


# --------------------------------------------------------------------------- free body
def free_body():
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.add_patch(Rectangle((-3, 1.0), 2.6, 1.0, fc=C_PLATE, ec="k"))
    ax.add_patch(Rectangle((0.4, 1.0), 2.6, 1.0, fc=C_PLATE, ec="k"))
    ax.add_patch(Rectangle((-0.4, 0.0), 0.8, 3.0, fc=C_BOLT, ec="k"))
    ax.add_patch(Rectangle((-0.9, 2.0), 1.8, 0.35, fc=C_BOLT, ec="k"))
    # cut at interface y=1.0
    ax.plot([-3.3, 3.3], [1.0, 1.0], ls="--", color="grey", lw=0.8)
    arrow(ax, 0, 3.0, 0, 3.8, color=C_THREAD)
    ax.text(0.12, 3.55, r"$F_{pre} + P_f$  (fastener)", color=C_THREAD, fontsize=8.5)
    for s in (-1, 1):
        arrow(ax, s * 1.7, 2.0, s * 1.7, 2.7)
        ax.text(s * 1.7 + 0.1, 2.5, r"$P_{ex}/2$", fontsize=8.5)
        arrow(ax, s * 1.7, 0.2, s * 1.7, 1.0, color=C_BLUE)
        ax.text(s * 1.7 + 0.1, 0.45, r"$F_m/2$", color=C_BLUE, fontsize=8.5)
    arrow(ax, 3.0, 1.5, 4.0, 1.5)
    ax.text(3.2, 1.7, r"$P_{shear}$", fontsize=8.5)
    arrow(ax, 1.4, 1.0, 0.6, 1.0, color=C_GREEN)
    ax.text(0.8, 0.75, r"$\mu F_m$", color=C_GREEN, fontsize=8.5)
    ax.text(-3.1, -0.45, r"Upper part cut free at the interface:  $F_m = F_{pre} + P_f - P_{ex} = F_{pre} - P_m$"
            "\n"
            r"No separation: $F_m > 0 \Leftrightarrow F_{pre} > P_m$.    No slip: $\mu F_m \geq P_{shear}$.",
            fontsize=8.8, va="top")
    ax.set_xlim(-3.4, 4.6)
    ax.set_ylim(-1.3, 4.0)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "bjt_free_body.png")


# --------------------------------------------------------------------------- interaction
def interaction():
    fig, ax = plt.subplots(figsize=(4.6, 4.0))
    th = np.linspace(0, np.pi / 2, 100)
    ax.plot(np.cos(th), np.sin(th), color=C_DIM, lw=1.8, label=r"$R_t^2 + R_s^2 = 1$")
    p = (0.45, 0.35)
    ax.plot(*p, "o", color=C_RED)
    s = 1 / np.hypot(*p)
    ax.plot([0, p[0] * s], [0, p[1] * s], ls="--", color=C_RED, lw=0.9)
    ax.text(p[0] + 0.03, p[1] - 0.06, "load point", color=C_RED, fontsize=8.5)
    ax.text(p[0] * s * 0.62, p[1] * s * 0.62 + 0.07, r"RF = $\dfrac{1}{\sqrt{R_t^2+R_s^2}}$", color=C_RED,
            fontsize=9)
    ax.set_xlabel(r"$R_t$ = tension stress / $F_{tu}$")
    ax.set_ylabel(r"$R_s$ = shear stress / $F_{su}$")
    ax.set_xlim(0, 1.1)
    ax.set_ylim(0, 1.1)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper right")
    save(fig, "bjt_interaction.png")


# --------------------------------------------------------------------------- goodman
def goodman():
    fig, ax = plt.subplots(figsize=(6, 3.8))
    Se, Sut, si = 162.0, 1040.0, 600.0
    sm = np.linspace(0, Sut, 50)
    ax.plot(sm, Se * (1 - sm / Sut), color=C_DIM, lw=1.8, label="Goodman line  $S_a = S_e(1 - S_m/S_{ut})$")
    sa = 40.0
    ax.plot([si, si + sa], [0, sa], color=C_THREAD, lw=1.5, label=r"load line from $\sigma_i$ (slope 1)")
    ax.plot(si + sa, sa, "o", color=C_RED)
    Sa = Se * (Sut - si) / (Sut + Se)
    ax.plot(si + Sa, Sa, "s", color=C_GREEN)
    ax.annotate(r"failure point $S_a$", (si + Sa, Sa), (si + Sa + 60, Sa + 25), fontsize=8.5,
                arrowprops=dict(arrowstyle="->"))
    ax.annotate(r"operating point $(\sigma_m, \sigma_a)$", (si + sa, sa), (si - 330, sa + 55), fontsize=8.5,
                arrowprops=dict(arrowstyle="->"))
    ax.text(si, -12, r"$\sigma_i$", ha="center", fontsize=9)
    ax.set_xlabel("mean stress [MPa]")
    ax.set_ylabel("alternating stress [MPa]")
    ax.set_xlim(0, Sut * 1.05)
    ax.set_ylim(-20, Se * 1.15)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    save(fig, "bjt_goodman.png")


# --------------------------------------------------------------------------- torque window (example)
def torque_window():
    base = DOC_STUD
    r0 = analyse(base)
    Ts = np.linspace(2, r0["T_max"] * 1.3, 120)
    curves = {"FM01 yield": [], "FM03 nut thread": [], "FM04 housing thread": [], "FM06 separation (ult)": [],
              "FM08 slip (ult)": []}
    keys = {"FM01 yield": "FM01", "FM03 nut thread": "FM03", "FM04 housing thread": "FM04",
            "FM06 separation (ult)": "FM06", "FM08 slip (ult)": "FM08"}
    for T in Ts:
        r = analyse(dataclasses.replace(base, T=float(T)))
        for k, fid in keys.items():
            curves[k].append(r["fm"][fid][0])
    fig, ax = plt.subplots(figsize=(7, 3.9))
    cols = [C_THREAD, "#7030A0", "#BF9000", C_BLUE, C_GREEN]
    for (k, v), c in zip(curves.items(), cols):
        ax.plot(Ts, v, label=k, color=c, lw=1.5)
    ax.axhline(1, color="k", lw=0.8)
    ax.axvspan(r0["T_min"], r0["T_max"], color="#C6EFCE", alpha=0.6, label="allowable window")
    ax.axvline(base.T, color=C_RED, ls="--", lw=1)
    ax.text(base.T, 0.45, f" applied T = {base.T:g} N.m", color=C_RED, fontsize=8.5)
    ax.text(r0["T_min"], 0.15, f" Tmin = {r0['T_min']:.1f}", fontsize=8.5)
    ax.text(r0["T_max"], 0.15, f" Tmax = {r0['T_max']:.1f}", fontsize=8.5)
    ax.set_ylim(0, 5)
    ax.set_xlabel("tightening torque T [N.m]")
    ax.set_ylabel("reserve factor")
    ax.legend(fontsize=7.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.17))
    ax.grid(alpha=0.3)
    ax.set_title("Worked example (stud): RF of the torque-dependent modes versus torque", fontsize=9.5)
    save(fig, "bjt_torque_window.png")


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in (spring_model, frustum_derivation, similar_triangles, thread_shear, free_body, interaction, goodman,
              torque_window):
        f()
    print(OUT)


if __name__ == "__main__":
    main()
