"""Sketches for the AFSAM Lug tool (Input sheet + manual).   python tools/figures_afsam.py"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "figures")
C_LUG, C_LUG2, C_BUSH, C_PIN, C_DIM, C_RED = "#BDD7EE", "#9DC3E6", "#A9D18E", "#F4B183", "#1F4E78", "#C00000"


def dim(ax, p0, p1, text, off=(0, 0), ha="center"):
    ax.annotate("", xy=p0, xytext=p1, arrowprops=dict(arrowstyle="<->", color=C_DIM, lw=0.9))
    ax.text((p0[0] + p1[0]) / 2 + off[0], (p0[1] + p1[1]) / 2 + off[1], text, ha=ha, va="center", color=C_DIM,
            fontsize=9.5)


def lug_sketch():
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10, 4.6), gridspec_kw={"width_ratios": [1.6, 1]})
    W, D, Dp, e = 2.4, 1.6, 1.1, 2.2
    th = np.linspace(0, np.pi, 80)
    out = np.vstack([np.c_[W * np.cos(th), W * np.sin(th)], [[-W, -3.5], [W, -3.5]]])
    ax.add_patch(Polygon(out, closed=True, fc=C_LUG, ec="k"))
    ax.add_patch(Circle((0, 0), D / 2, fc=C_BUSH, ec="k"))
    ax.add_patch(Circle((0, 0), Dp / 2, fc=C_PIN, ec="k"))
    ax.plot([0, 0], [-3.8, 3.0], ls="-.", color="grey", lw=0.7)
    ax.plot([-W - 0.4, W + 0.4], [0, 0], ls="-.", color="grey", lw=0.7)
    dim(ax, (0.25, 0), (0.25, W), "e", off=(0.2, 0.5))
    dim(ax, (-0.35, D / 2), (-0.35, W), "a", off=(-0.25, 0))
    dim(ax, (-D / 2, -1.25), (D / 2, -1.25), "D (bushing OD)", off=(0, -0.3))
    dim(ax, (-Dp / 2, 0.35), (Dp / 2, 0.35), "", off=(0, 0))
    ax.text(0.7, 0.55, "Dp", color=C_DIM, fontsize=9.5)
    dim(ax, (-W, -2.6), (W, -2.6), "w (full width)", off=(0, -0.3))
    ax.add_patch(FancyArrowPatch((0, 0), (0, 3.3), arrowstyle="-|>", mutation_scale=16, color=C_RED, lw=1.8))
    ax.text(0.12, 3.1, "P (pin load on the lug)", color=C_RED, fontsize=9)
    ax.text(-W - 0.3, -3.3, "net section = (w - D) t", fontsize=8.5)
    ax.set_xlim(-W - 0.8, W + 1.8)
    ax.set_ylim(-3.9, 3.7)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Lug (AFSAM Fig 9-1)", fontsize=10, weight="bold")
    ax2.add_patch(Rectangle((-0.5, -3.5), 1.0, 3.5 + W, fc=C_LUG, ec="k"))
    ax2.add_patch(Rectangle((-0.5, -D / 2), 1.0, D, fc=C_BUSH, ec="k"))
    ax2.add_patch(Rectangle((-1.5, -Dp / 2), 3.0, Dp, fc=C_PIN, ec="k", alpha=0.85))
    dim(ax2, (-0.5, W + 0.4), (0.5, W + 0.4), "t", off=(0, 0.3))
    ax2.text(0.7, -2.4, "outer lug: t1 = ONE outer lug\ninner lug: t2", fontsize=8.5)
    ax2.set_xlim(-1.9, 3.4)
    ax2.set_ylim(-3.9, 3.7)
    ax2.set_aspect("equal")
    ax2.axis("off")
    ax2.set_title("Side view", fontsize=10, weight="bold")
    fig.savefig(os.path.join(OUT, "afsam_lug_sketch.png"), dpi=170, bbox_inches="tight")
    plt.close(fig)


def joint_sketch():
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    t1, t2, g = 0.8, 1.5, 0.15
    xo1, xi, xo2 = -t2 / 2 - g - t1, -t2 / 2, t2 / 2 + g
    for x, w, c in [(xo1, t1, C_LUG2), (xo2, t1, C_LUG2)]:
        ax.add_patch(Rectangle((x, -3.2), w, 4.0, fc=c, ec="k"))
    ax.add_patch(Rectangle((xi, -0.8), t2, 4.0, fc=C_LUG, ec="k"))
    ax.add_patch(Rectangle((-2.6, -0.35), 5.2, 0.7, fc=C_PIN, ec="k"))
    dim(ax, (xo1, 1.2), (xo1 + t1, 1.2), "t1", off=(0, 0.25))
    dim(ax, (xi, 2.9), (xi + t2, 2.9), "t2", off=(0.45, 0.25))
    dim(ax, (xi - g, 1.2), (xi, 1.2), "", off=(0, 0))
    ax.text(xi - g / 2, 1.55, "g", ha="center", color=C_DIM, fontsize=9.5)
    ax.text(2.7, 0, "pin Dp (Di if hollow)", va="center", fontsize=8.8)
    ax.add_patch(FancyArrowPatch((0, 3.2), (0, 4.2), arrowstyle="-|>", mutation_scale=15, color=C_RED, lw=1.8))
    ax.text(0.12, 3.95, "P", color=C_RED, fontsize=11)
    for x in (xo1 + t1 / 2, xo2 + t1 / 2):
        ax.add_patch(FancyArrowPatch((x, -3.2), (x, -4.2), arrowstyle="-|>", mutation_scale=15, color=C_RED, lw=1.8))
        ax.text(x + (0.45 if x > 0 else -0.45), -3.95, "P/2", color=C_RED, fontsize=10, ha="left" if x > 0 else "right")
    ax.text(-7.6, 2.4, "Outer lugs (one of two): column 'Outer lug'\nInner lug: column 'Inner lug'\n"
                       "Tangs: straight parts behind the heads,\nwidth wT1 (outer), wT2 (inner)", fontsize=8.8, va="center")
    ax.set_xlim(-7.8, 4.8)
    ax.set_ylim(-4.6, 4.6)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(os.path.join(OUT, "afsam_joint_sketch.png"), dpi=170, bbox_inches="tight")
    plt.close(fig)


def fig93_interpretation():
    """Fig 9-3 entered with centre-to-edge distance: comparison with Fig 9-2."""
    import sys
    sys.path.insert(0, ROOT)
    from handcalc.afsam_lug import k_fig9_2, k_fig9_3
    ed = np.linspace(0.55, 2.4, 80)
    f92 = [k_fig9_2(v) * ((v - 0.5) if v < 1.5 else 1.0) for v in ed]
    f93 = [k_fig9_3(v, 2) for v in ed]
    # previous workbook: K read at a/D = e/D - 0.5, then K (a/D) F for e/D < 1.5 and K F above
    f93a = [(k_fig9_3(v - 0.5, 2) if v - 0.5 >= 0.5 else 0.0) * ((v - 0.5) if v < 1.5 else 1.0) for v in ed]
    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    ax.plot(ed, f92, color=C_DIM, lw=2, label="Fig 9-2 (D/t <= 5):  K (a/D), e/D < 1.5;  K above")
    ax.plot(ed, f93, color=C_RED, lw=1.6, label="Fig 9-3 (D/t <= 2) entered with e/D:  K")
    ax.plot(ed, f93a, color="#7F7F7F", lw=1.2, ls="--",
            label="Fig 9-3 entered with a/D, Eq 9-1a/b factor (previous workbook)")
    ax.set_xlabel("e/D  (hole centre to edge / D)")
    ax.set_ylabel(r"$F_{bru} / F_{tu}$")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7.6, loc="upper left")
    fig.savefig(os.path.join(OUT, "afsam_fig93_interpretation.png"), dpi=170, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    lug_sketch()
    joint_sketch()
    fig93_interpretation()
    print(OUT)
