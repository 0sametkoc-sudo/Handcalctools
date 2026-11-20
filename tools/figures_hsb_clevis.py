"""Figures for the HSB clevis tool (Input sheet sketch + manual).

python tools/figures_hsb_clevis.py  ->  docs/figures/hsb_*.png
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from handcalc.hsb_clevis import H_factor, ktb1_straight, ktb1_tapered, rbry  # noqa: E402

OUT = os.path.join(ROOT, "docs", "figures")
C_LUG, C_LUG2, C_BUSH, C_BOLT, C_DIM, C_RED = "#BDD7EE", "#9DC3E6", "#A9D18E", "#F4B183", "#1F4E78", "#C00000"
plt.rcParams.update({"font.size": 9})


def dim(ax, p0, p1, text, off=(0, 0), ha="center", color=C_DIM):
    ax.annotate("", xy=p0, xytext=p1, arrowprops=dict(arrowstyle="<->", color=color, lw=0.9))
    ax.text((p0[0] + p1[0]) / 2 + off[0], (p0[1] + p1[1]) / 2 + off[1], text, ha=ha, va="center", color=color,
            fontsize=9)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=170, bbox_inches="tight")
    plt.close(fig)


def lug_geometry():
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10, 5.2), gridspec_kw={"width_ratios": [1.6, 1]})
    r, d, da, beta = 2.4, 2.0, 1.4, 25
    # lug outline: arc of radius r around the hole centre (0,0), tapered sides down to a shank
    th = np.linspace(np.radians(-beta), np.radians(180 + beta), 80)
    arc = np.c_[r * np.cos(th), r * np.sin(th)]
    xs = r * np.cos(np.radians(-beta))
    ys = r * np.sin(np.radians(-beta))
    tb = np.tan(np.radians(beta))
    y_low = -4.2
    x_low = xs + (ys - y_low) * tb * 0.35
    outline = np.vstack([arc, [[-x_low, y_low], [x_low, y_low]]])
    ax.add_patch(Polygon(outline, closed=True, fc=C_LUG, ec="k"))
    ax.add_patch(Circle((0, 0), d / 2, fc=C_BUSH, ec="k"))
    ax.add_patch(Circle((0, 0), da / 2, fc=C_BOLT, ec="k"))
    ax.plot([0, 0], [y_low - 0.3, r + 0.6], ls="-.", color="grey", lw=0.7)
    ax.plot([-r - 0.6, r + 0.6], [0, 0], ls="-.", color="grey", lw=0.7)
    dim(ax, (0, 0), (r * np.cos(np.radians(130)), r * np.sin(np.radians(130))), "r", off=(-0.15, 0.15))
    dim(ax, (-d / 2, -1.15), (d / 2, -1.15), "d (hole / bushing OD)", off=(0, -0.28))
    dim(ax, (-da / 2, -0.35), (da / 2, -0.35), "", off=(0, 0))
    ax.text(-2.2, -0.7, "da (bolt)", color=C_DIM, fontsize=9)
    # load arrow (load on the lug from the bolt, angle phi from the axis)
    phi = 30
    p = np.radians(90 - phi)
    ax.add_patch(FancyArrowPatch((0, 0), (2.9 * np.cos(p), 2.9 * np.sin(p)), arrowstyle="-|>", mutation_scale=16,
                                 color=C_RED, lw=1.8))
    ax.text(3.0 * np.cos(p) + 0.1, 3.0 * np.sin(p), "F (bolt load\non the lug)", color=C_RED, fontsize=8.5)
    a = np.linspace(np.radians(90), p, 20)
    ax.plot(1.6 * np.cos(a), 1.6 * np.sin(a), color=C_RED, lw=0.8)
    ax.text(0.55, 1.75, r"$\varphi$", color=C_RED, fontsize=11)
    ax.text(x_low + 0.1, y_low + 1.0, r"taper $\beta$", fontsize=9)
    ax.text(-r - 0.4, r + 0.5, "h: eccentricity of the head contour (HSB Fig. 1);\nh = r for a concentric head.\n"
            "e and w: measured relative to the load direction (see below)",
            fontsize=8.5)
    ax.set_xlim(-r - 1.0, r + 2.4)
    ax.set_ylim(y_low - 0.5, r + 1.3)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Lug plan view", fontsize=10, weight="bold")
    # side view: thickness
    ax2.add_patch(Rectangle((-0.5, -4.2), 1.0, 4.2 + 2.4, fc=C_LUG, ec="k"))
    ax2.add_patch(Rectangle((-0.5, -1.0), 1.0, 2.0, fc=C_BUSH, ec="k"))
    ax2.add_patch(Rectangle((-1.6, -0.7), 3.2, 1.4, fc=C_BOLT, ec="k", alpha=0.8))
    dim(ax2, (-0.5, 2.8), (0.5, 2.8), "t", off=(0, 0.3))
    ax2.text(0.7, -2.5, "female lug: t = ONE prong\nmale lug: t = inner lug", fontsize=8.5)
    ax2.set_xlim(-2.0, 3.6)
    ax2.set_ylim(-4.7, 3.7)
    ax2.set_aspect("equal")
    ax2.axis("off")
    ax2.set_title("Side view", fontsize=10, weight="bold")
    save(fig, "hsb_lug_geometry.png")


def joint_figure():
    fig, ax = plt.subplots(figsize=(8, 4.2))
    tf, tm, g = 0.8, 1.6, 0.1
    # bolt horizontal, lugs vertical plates seen in section
    xs = [-tm / 2 - g - tf, -tm / 2, tm / 2 + g]
    for x, w, c, lab in [(xs[0], tf, C_LUG2, "female\nprong"), (xs[1], tm, C_LUG, "male lug"),
                         (xs[2], tf, C_LUG2, "female\nprong")]:
        if lab == "male lug":
            ax.add_patch(Rectangle((x, -0.9), w, 4.0, fc=c, ec="k"))
        else:
            ax.add_patch(Rectangle((x, -3.1), w, 4.0, fc=c, ec="k"))
        if lab == "male lug":
            ax.text(x + w + 0.15, 2.6, lab, ha="left", va="center", fontsize=8.5)
        else:
            ax.text(x + w / 2, -1.2, lab.replace("\n", " "), ha="center", va="center", fontsize=7.5, rotation=90)
    ax.add_patch(Rectangle((-2.6, -0.4), 5.2, 0.8, fc=C_BOLT, ec="k"))
    ax.text(2.7, 0, "bolt (not checked\nby HSB 26101-01)", va="center", fontsize=8.5)
    ax.add_patch(FancyArrowPatch((0, 3.1), (0, 4.2), arrowstyle="-|>", mutation_scale=15, color=C_RED, lw=1.8))
    ax.text(0.15, 3.9, "P", color=C_RED, fontsize=11)
    for x in (xs[0] + tf / 2, xs[2] + tf / 2):
        ax.add_patch(FancyArrowPatch((x, -3.1), (x, -4.4), arrowstyle="-|>", mutation_scale=15, color=C_RED, lw=1.8))
        ax.text(x + (0.5 if x > 0 else -0.5), -4.1, "s P", color=C_RED, fontsize=10, ha="left" if x > 0 else "right")
    ax.text(-7.4, 2.9, "Male lug: carries P\nFemale lug: each prong carries s P\n(s = 0.5 symmetric)\n\n"
                        "Each lug: Cases 1, 2, 3 + bushing\nJoint RF = lowest of all (HSB 3.4)", fontsize=8.8,
            va="center")
    ax.set_xlim(-7.6, 4.8)
    ax.set_ylim(-5.6, 4.6)
    ax.set_aspect("equal")
    ax.axis("off")
    save(fig, "hsb_joint.png")


def ktb_chart():
    fig, ax = plt.subplots(figsize=(6.2, 4))
    x = np.linspace(1.35, 3.4, 200)
    ax.plot(x, [ktb1_straight(v, 0)[0] for v in x], label=r"straight, $\varphi$ = 0", color=C_DIM)
    ax.plot(x, [ktb1_straight(v, 90)[0] for v in x], label=r"straight, $\varphi$ = 90", color=C_RED)
    ax.plot(x, [ktb1_tapered(v, 0) for v in x], "--", label=r"tapered $\beta$ = 45, $\varphi$ = 0", color=C_DIM)
    ax.plot(x, [ktb1_tapered(v, 90) for v in x], "--", label=r"tapered $\beta$ = 45, $\varphi$ = 90", color=C_RED)
    ax.set_xlabel("2r/d")
    ax.set_ylabel(r"$K_{tb,1}$")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    save(fig, "hsb_ktb1.png")


def kbr_chart():
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.4))
    k = np.linspace(1.5, 5, 100)
    axs[0].plot(k, 7.502 * (k + 1.125) ** -1.637, color=C_DIM)
    axs[0].set_xlabel(r"$K_{tb}$")
    axs[0].set_ylabel(r"$K_{BR}$")
    axs[0].set_title(r"$K_{BR} = 7.502\,(K_{tb}+1.125)^{-1.637}$", fontsize=9)
    axs[0].grid(alpha=0.3)
    hr = np.linspace(0.6, 2.0, 100)
    for phi, c in ((0, C_DIM), (45, "#7030A0"), (90, C_RED)):
        axs[1].plot(hr, [H_factor(v, phi) for v in hr], label=rf"$\varphi$ = {phi}", color=c)
    axs[1].set_xlabel("h/r")
    axs[1].set_ylabel("H")
    axs[1].set_title("Eccentricity factor H", fontsize=9)
    axs[1].grid(alpha=0.3)
    axs[1].legend(fontsize=8)
    fig.tight_layout()
    save(fig, "hsb_kbr_h.png")


def rbry_chart():
    fig, ax = plt.subplots(figsize=(5.6, 3.3))
    ed = np.linspace(0.5, 2.5, 200)
    ax.plot(ed, [rbry(v, 495, 595) for v in ed], color=C_DIM)
    ax.plot([1.5, 2.0], [495, 595], "o", color=C_RED)
    ax.text(1.52, 470, r"$R_{bry,1.5}$", color=C_RED)
    ax.text(2.02, 570, r"$R_{bry,2.0}$", color=C_RED)
    ax.set_xlabel("e/d")
    ax.set_ylabel(r"$R_{bry}$ used [MPa]")
    ax.set_title("Bearing yield strength versus e/d (example: female lug of HSB)", fontsize=9)
    ax.grid(alpha=0.3)
    save(fig, "hsb_rbry.png")


def ew_definition():
    """e and w are measured relative to the LOAD direction."""
    fig, axs = plt.subplots(1, 2, figsize=(9.5, 4.4))
    r, d, w0 = 2.0, 1.6, 2.0
    for ax, phi in zip(axs, (0, 90)):
        th = np.linspace(0, np.pi, 60)
        outline = np.vstack([np.c_[r * np.cos(th), r * np.sin(th)], [[-w0, -3.6], [w0, -3.6]]])
        ax.add_patch(Polygon(outline, closed=True, fc=C_LUG, ec="k"))
        ax.add_patch(Circle((0, 0), d / 2, fc="white", ec="k"))
        p = np.radians(90 - phi)
        u = np.array([np.cos(p), np.sin(p)])
        ax.add_patch(FancyArrowPatch((0, 0), tuple(3.3 * u), arrowstyle="-|>", mutation_scale=16, color=C_RED,
                                     lw=1.8))
        ax.text(*(3.35 * u + np.array([0.05, 0.1])), "F", color=C_RED, fontsize=11)
        if phi == 0:
            dim(ax, (0.25, 0), (0.25, r), "e", off=(0.2, 0.3))
            dim(ax, (0, -1.6), (w0, -1.6), "w = half width", off=(0.2, -0.3))
        else:
            dim(ax, (0, 0.25), (w0, 0.25), "e", off=(0, 0.25))
            dim(ax, (-0.25, 0), (-0.25, r), "w = smaller\nperpendicular\ndistance", off=(-1.25, 0.5))
        ax.set_title(rf"$\varphi$ = {phi} deg", fontsize=10, weight="bold")
        ax.set_xlim(-3.4, 4.0)
        ax.set_ylim(-3.9, 3.9)
        ax.set_aspect("equal")
        ax.axis("off")
    fig.suptitle("e: edge distance ALONG the load.   w: smaller edge distance PERPENDICULAR to the load.",
                 fontsize=10)
    save(fig, "hsb_ew_definition.png")


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in (lug_geometry, joint_figure, ew_definition, ktb_chart, kbr_chart, rbry_chart):
        f()
    print(OUT)


if __name__ == "__main__":
    main()
