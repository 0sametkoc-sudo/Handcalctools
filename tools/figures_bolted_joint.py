"""Schematic figures for the bolted joint tool (Excel sheet + user manual).

python tools/figures_bolted_joint.py  ->  docs/figures/bj_*.png
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon, Rectangle  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "figures")
C_PLATE = "#BDD7EE"
C_PLATE2 = "#9DC3E6"
C_HOUS = "#C9C9C9"
C_WASH = "#404040"
C_BOLT = "#F4B183"
C_THREAD = "#C55A11"
C_DIM = "#1F4E78"


def dim_v(ax, x, y0, y1, text, side="right", off=0.25):
    ax.annotate("", xy=(x, y0), xytext=(x, y1), arrowprops=dict(arrowstyle="<->", color=C_DIM, lw=0.9))
    ha = "left" if side == "right" else "right"
    ax.text(x + (off if side == "right" else -off) * 0.4, (y0 + y1) / 2, text, ha=ha, va="center",
            fontsize=8, color=C_DIM)


def dim_h(ax, y, x0, x1, text):
    ax.annotate("", xy=(x0, y), xytext=(x1, y), arrowprops=dict(arrowstyle="<->", color=C_DIM, lw=0.9))
    ax.text((x0 + x1) / 2, y + 0.12, text, ha="center", va="bottom", fontsize=8, color=C_DIM)


def rect(ax, x, y, w, h, fc, hatch=None, ec="black", lw=0.6):
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, hatch=hatch))


def plate(ax, y, h, fc, label, num, w=3.2, hole=0.55):
    rect(ax, -w, y, w - hole, h, fc)
    rect(ax, hole, y, w - hole, h, fc)
    ax.text(-w + 0.15, y + h / 2, label, fontsize=7.5, va="center")
    ax.text(w + 0.1, y + h / 2, f"{num}", fontsize=8, va="center", weight="bold", color="#C00000")


def shank(ax, y0, y1, thread_from, d=1.0, thread_to=None):
    """fastener from y0 (bottom) to y1 (top); threaded between thread_from and thread_to."""
    rect(ax, -d / 2, y0, d, y1 - y0, C_BOLT)
    tt = thread_to if thread_to is not None else y0
    rect(ax, -d / 2, tt, d, thread_from - tt, C_BOLT, hatch="////", ec=C_THREAD)


def config_figure(path):
    fig, axs = plt.subplots(1, 3, figsize=(11, 4.6))
    # ------------------------------------------------ BOLT
    ax = axs[0]
    ax.set_title("BOLT  (head + nut)", fontsize=10, weight="bold")
    top = 4.0
    rect(ax, -1.1, top + 0.3, 2.2, 0.7, C_BOLT)            # head
    rect(ax, -1.2, top, 2.4, 0.3, C_WASH)                   # washer
    plate(ax, top - 1.3, 1.3, C_PLATE, "plate", 2)
    plate(ax, top - 3.0, 1.7, C_PLATE2, "plate", 3)
    rect(ax, -1.2, top - 3.3, 2.4, 0.3, C_WASH)             # washer
    rect(ax, -1.1, top - 4.1, 2.2, 0.8, "#A9D18E")          # nut
    ax.text(1.3, top + 0.15, "1", fontsize=8, weight="bold", color="#C00000", va="center")
    ax.text(1.3, top - 3.15, "4", fontsize=8, weight="bold", color="#C00000", va="center")
    shank(ax, top - 4.6, top + 0.3, thread_from=top - 1.9)
    dim_v(ax, -3.6, top - 3.3, top + 0.3, "grip l", side="left")
    dim_v(ax, 4.4, top - 4.6, top + 0.3, "L")
    dim_v(ax, 3.7, top - 4.6, top - 1.9, "LT")
    dim_v(ax, -1.5, top - 4.1, top - 3.3, "Le,nut", side="left")
    dim_h(ax, top + 1.2, -1.2, 1.2, "Dw,top")
    # ------------------------------------------------ SCREW
    ax = axs[1]
    ax.set_title("SCREW  (tapped housing)", fontsize=10, weight="bold")
    rect(ax, -1.1, top + 0.3, 2.2, 0.7, C_BOLT)
    rect(ax, -1.2, top, 2.4, 0.3, C_WASH)
    plate(ax, top - 1.6, 1.6, C_PLATE, "plate", 2)
    rect(ax, -3.2, top - 5.0, 6.4, 3.4, C_HOUS)
    rect(ax, -0.55, top - 3.9, 1.1, 2.3, "white", lw=0.3)
    ax.text(-3.05, top - 4.6, "housing", fontsize=7.5)
    ax.text(3.3, top - 2.6, "3", fontsize=8, weight="bold", color="#C00000", va="center")
    ax.text(1.3, top + 0.15, "1", fontsize=8, weight="bold", color="#C00000", va="center")
    shank(ax, top - 3.6, top + 0.3, thread_from=top - 2.0)
    ax.plot([-3.2, 3.2], [top - 3.6, top - 3.6], ls="--", lw=0.7, color=C_DIM)
    dim_v(ax, -3.6, top - 3.6, top + 0.3, "grip l", side="left")
    dim_v(ax, 1.9, top - 3.6, top - 1.6, "Le,h")
    dim_v(ax, 3.9, top - 3.6, top + 0.3, "L")
    ax.text(0.0, top - 4.15, "layer 3 = housing down to\nend of engaged thread", fontsize=7, ha="center", va="top")
    # ------------------------------------------------ STUD
    ax = axs[2]
    ax.set_title("STUD  (housing + nut)", fontsize=10, weight="bold")
    rect(ax, -1.1, top + 0.3, 2.2, 0.8, "#A9D18E")          # nut on top
    rect(ax, -1.2, top + 0.15, 2.4, 0.15, C_WASH)
    rect(ax, -1.2, top, 2.4, 0.15, C_WASH)
    plate(ax, top - 1.4, 1.4, C_PLATE, "plate", 3)
    rect(ax, -3.2, top - 5.0, 6.4, 3.6, C_HOUS)
    rect(ax, -0.55, top - 3.9, 1.1, 2.5, "white", lw=0.3)
    ax.text(-3.05, top - 4.6, "housing", fontsize=7.5)
    ax.text(3.3, top - 2.6, "4", fontsize=8, weight="bold", color="#C00000", va="center")
    ax.text(1.3, top + 0.25, "1,2", fontsize=8, weight="bold", color="#C00000", va="center")
    rect(ax, -0.5, top - 3.6, 1.0, 5.3, C_BOLT)
    rect(ax, -0.5, top - 3.6, 1.0, 1.4, C_BOLT, hatch="\\\\\\\\", ec=C_THREAD)     # stud end
    rect(ax, -0.5, top - 0.4, 1.0, 2.1, C_BOLT, hatch="////", ec=C_THREAD)        # nut end
    ax.plot([-3.2, 3.2], [top - 3.6, top - 3.6], ls="--", lw=0.7, color=C_DIM)
    dim_v(ax, -3.6, top - 3.6, top + 0.3, "grip l", side="left")
    dim_v(ax, 3.9, top - 3.6, top + 1.7, "L")
    dim_v(ax, 1.8, top - 0.4, top + 1.7, "LT")
    dim_v(ax, 1.8, top - 3.6, top - 2.2, "LT,s")
    dim_v(ax, -1.6, top + 0.3, top + 1.1, "Le,nut", side="left")
    for ax in axs:
        ax.set_xlim(-4.6, 5.2)
        ax.set_ylim(-1.3, 6.0)
        ax.set_aspect("equal")
        ax.axis("off")
    fig.text(0.5, 0.02, "Red numbers: row in the joint-stack table (top -> bottom). Hatched: threaded length.",
             ha="center", fontsize=8.5)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def cone_figure(path):
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    t1, t2 = 1.6, 3.0
    l = t1 + t2
    Dw, d = 2.0, 1.0
    ta = 0.57735
    y_top, y_bot = l, 0.0
    W = 6
    rect(ax, -W, t2, W - d / 2, t1, C_PLATE)
    rect(ax, d / 2, t2, W - d / 2, t1, C_PLATE)
    rect(ax, -W, 0, W - d / 2, t2, C_PLATE2)
    rect(ax, d / 2, 0, W - d / 2, t2, C_PLATE2)
    mid = l / 2
    Dm = Dw + 2 * mid * ta
    for s in (1, -1):
        ax.add_patch(Polygon([(s * Dw / 2, y_top), (s * Dm / 2, mid), (s * d / 2, mid), (s * d / 2, y_top)],
                             closed=True, fc="#FFE699", ec="#BF9000", alpha=0.8))
        ax.add_patch(Polygon([(s * Dw / 2, y_bot), (s * Dm / 2, mid), (s * d / 2, mid), (s * d / 2, y_bot)],
                             closed=True, fc="#FFE699", ec="#BF9000", alpha=0.8))
    rect(ax, -d / 2, -0.8, d, l + 1.6, C_BOLT)
    rect(ax, -Dw / 2 - 0.3, y_top, Dw + 0.6, 0.5, C_BOLT)
    rect(ax, -Dw / 2 - 0.3, -0.5, Dw + 0.6, 0.5, "#A9D18E")
    ax.plot([-W, W], [mid, mid], ls="--", color="#C00000", lw=1)
    ax.text(W + 0.1, mid, "mid-plane  l/2", color="#C00000", va="center", fontsize=8.5)
    ax.text(-W + 0.2, t2 + t1 / 2, "layer 1", fontsize=8.5, va="center")
    ax.text(-W + 0.2, t2 / 2 + 0.6, "layer 2", fontsize=8.5, va="center")
    # split annotation of layer 2
    dim_v(ax, 4.2, mid, t2, "t,upper", off=0.4)
    dim_v(ax, 4.2, 0, mid, "t,lower", off=0.4)
    dim_h(ax, l + 0.75, -Dw / 2, Dw / 2, "Dw,top")
    dim_h(ax, t2 + 0.12, -(Dw / 2 + t1 * ta), Dw / 2 + t1 * ta, "")
    ax.text(Dw / 2 + t1 * ta + 0.15, t2 + 0.35, "D,upper = Dw,top + 2 z,top tan a", fontsize=8, color=C_DIM)
    ax.set_xlim(-W - 0.3, W + 2.6)
    ax.set_ylim(-1.2, l + 1.9)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Pressure cones from both bearing faces meet at mid-grip.\n"
                 "Cone half angle a = 30 deg. Layer 2 is split: its upper part belongs to the top cone, its lower part to the bottom cone.",
                 fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def load_figure(path):
    """Joint diagram: fastener and member force versus elongation."""
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    kf, km, F0, P = 1.0, 2.0, 6.0, 3.0
    C = kf / (kf + km)
    xb = F0 / kf
    xm = F0 / km
    dx = P / (kf + km)
    ax.plot([0, xb + 2.5], [0, kf * (xb + 2.5)], color=C_THREAD, lw=1.6, label="fastener (slope kf)")
    ax.plot([xb - 0.5, xb + xm], [F0 + km * 0.5, 0], color="#2E75B6", lw=1.6, label="members (slope -km)")
    ax.plot([xb, xb + dx], [F0, F0 + C * P], color="k", lw=0.8)
    ax.annotate("", xy=(xb + dx, F0 + C * P), xytext=(xb + dx, F0 - (1 - C) * P),
                arrowprops=dict(arrowstyle="<->", color="k"))
    ax.text(xb + dx + 0.1, F0, "Pex", fontsize=9)
    ax.annotate("", xy=(xb - 0.15, F0), xytext=(xb - 0.15, F0 + C * P), arrowprops=dict(arrowstyle="<->", color=C_THREAD))
    ax.text(xb - 0.25, F0 + C * P / 2, "Pf = C Pex", ha="right", fontsize=8.5, color=C_THREAD)
    ax.axhline(F0, color="grey", lw=0.5, ls=":")
    ax.text(0.1, F0 + 0.15, "Fpre", fontsize=9)
    ax.text(xb + dx + 0.1, F0 - (1 - C) * P - 0.3, "Fm = Fpre - Pm (clamp left)", fontsize=8.5, color="#2E75B6")
    ax.set_xlabel("elongation / compression")
    ax.set_ylabel("force")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(fontsize=8, loc="upper left")
    ax.set_title("Load sharing: C = kf / (kf + km)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    config_figure(os.path.join(OUT, "bj_configurations.png"))
    cone_figure(os.path.join(OUT, "bj_cone.png"))
    load_figure(os.path.join(OUT, "bj_load_sharing.png"))
    print(OUT)


if __name__ == "__main__":
    main()
