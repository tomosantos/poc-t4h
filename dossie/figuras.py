"""
figuras.py — Gera as 4 figuras para o dossier de pesquisa.
Derivado dos resultados empíricos do POC (benchmark/results/).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import json
import os
import numpy as np

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_JSON = os.path.join(BASE, "benchmark", "results", "results.json")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figuras")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────────
with open(RESULTS_JSON, encoding="utf-8") as f:
    rows = json.load(f)

# ── Style ──────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "figure.dpi": 150,
})

MODO_STYLE = {
    "single":   {"color": "#1f77b4", "marker": "o", "label": "single-pass", "hatch": ""},
    "two_step": {"color": "#d62728", "marker": "s", "label": "duas etapas", "hatch": "//"},
}

MODEL_SHORT = {
    "google/gemini-2.5-flash-lite":     "Gemini-Flash-Lite",
    "openai/gpt-4o-mini":               "GPT-4o-mini",
    "qwen/qwen2.5-vl-72b-instruct":     "Qwen2.5-VL-72B",
}


# ══════════════════════════════════════════════════════════════════════════════
# FIGURA 1 — Diagrama de arquitetura (esquemático)
# ══════════════════════════════════════════════════════════════════════════════
def draw_box(ax, x, y, w, h, text, color="#e8f4f8", edgecolor="#2c7bb6",
             fontsize=8, bold=False, wrap_width=None):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                         facecolor=color, edgecolor=edgecolor, linewidth=1.5, zorder=3)
    ax.add_patch(box)
    weight = "bold" if bold else "normal"
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, fontweight=weight, zorder=4, wrap=True,
            multialignment="center")

def draw_arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color="#333333", lw=1.5), zorder=5)


def figura1_arquitetura():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_facecolor("#fafafa")
    fig.patch.set_facecolor("#fafafa")

    # ── Row labels ─────────────────────────────────────────────────────────
    row_colors = {"(a)": "#fff3cd", "(b)": "#d4edda", "(c)": "#d1ecf1"}
    rows_info = [
        ("(a) ATUAL", 4.2, "#fff3cd", "#856404"),
        ("(b) PROPOSTA", 2.5, "#d4edda", "#155724"),
        ("(c) HÍBRIDO\n(doc extenso)", 0.7, "#d1ecf1", "#0c5460"),
    ]
    for label, y_center, bg, fg in rows_info:
        rect = FancyBboxPatch((0.05, y_center - 0.55), 1.5, 1.1,
                              boxstyle="round,pad=0.03", facecolor=bg,
                              edgecolor=fg, linewidth=1, zorder=2)
        ax.add_patch(rect)
        ax.text(0.8, y_center, label, ha="center", va="center",
                fontsize=8, fontweight="bold", color=fg, zorder=4)

    # ── (a) ATUAL ─────────────────────────────────────────────────────────
    y = 4.2
    draw_box(ax, 1.75, y - 0.4, 1.3, 0.8, "Documento\n(imagem/PDF)",
             color="#fff3cd", edgecolor="#856404", fontsize=7.5)
    draw_arrow(ax, 3.05, y, 3.4, y)
    draw_box(ax, 3.4, y - 0.4, 1.8, 0.8, "LLM: interpretação\n(1ª inferência)",
             color="#ffc107", edgecolor="#856404", fontsize=7.5)
    draw_arrow(ax, 5.2, y, 5.55, y)
    draw_box(ax, 5.55, y - 0.4, 1.8, 0.8, "LLM: formatação\nJSON (2ª inferência)",
             color="#ffc107", edgecolor="#856404", fontsize=7.5)
    draw_arrow(ax, 7.35, y, 7.7, y)
    draw_box(ax, 7.7, y - 0.4, 1.1, 0.8, "JSON",
             color="#fff3cd", edgecolor="#856404", fontsize=7.5)
    ax.text(5.5, 3.55, "2 inferências LLM", ha="center", va="top",
            fontsize=7, color="#856404", style="italic")

    # ── (b) PROPOSTA ─────────────────────────────────────────────────────
    y = 2.5
    draw_box(ax, 1.75, y - 0.4, 1.3, 0.8, "Documento\n(imagem/PDF)",
             color="#d4edda", edgecolor="#155724", fontsize=7.5)
    draw_arrow(ax, 3.05, y, 3.4, y)
    draw_box(ax, 3.4, y - 0.4, 2.8, 0.8,
             "VLM single-pass\n+ structured output (1 inferência)",
             color="#28a745", edgecolor="#155724", fontsize=7.5)
    draw_arrow(ax, 6.2, y, 6.55, y)
    draw_box(ax, 6.55, y - 0.4, 1.1, 0.8, "JSON",
             color="#d4edda", edgecolor="#155724", fontsize=7.5)
    ax.text(5.0, 1.85, "1 inferência VLM", ha="center", va="top",
            fontsize=7, color="#155724", style="italic")

    # ── (c) HÍBRIDO ───────────────────────────────────────────────────────
    y_top = 1.25
    y_bot = 0.65
    y_mid = (y_top + y_bot) / 2
    draw_box(ax, 1.75, y_mid - 0.35, 1.3, 0.7, "PDF\n(extenso)",
             color="#d1ecf1", edgecolor="#0c5460", fontsize=7.5)
    # split arrow
    ax.annotate("", xy=(3.4, y_top), xytext=(3.05, y_mid),
                arrowprops=dict(arrowstyle="->", color="#333333", lw=1.2), zorder=5)
    ax.annotate("", xy=(3.4, y_bot), xytext=(3.05, y_mid),
                arrowprops=dict(arrowstyle="->", color="#333333", lw=1.2), zorder=5)
    draw_box(ax, 3.4, y_top - 0.27, 2.0, 0.55, "PyMuPDF: texto +\ntabelas (0 custo)",
             color="#17a2b8", edgecolor="#0c5460", fontsize=7)
    draw_box(ax, 3.4, y_bot - 0.27, 2.0, 0.55, "VLM: só figuras\n(1 inferência)",
             color="#17a2b8", edgecolor="#0c5460", fontsize=7)
    # merge arrows
    ax.annotate("", xy=(6.5, y_mid), xytext=(5.4, y_top),
                arrowprops=dict(arrowstyle="->", color="#333333", lw=1.2), zorder=5)
    ax.annotate("", xy=(6.5, y_mid), xytext=(5.4, y_bot),
                arrowprops=dict(arrowstyle="->", color="#333333", lw=1.2), zorder=5)
    draw_box(ax, 6.5, y_mid - 0.3, 1.3, 0.6, "Markdown\nestruturado",
             color="#d1ecf1", edgecolor="#0c5460", fontsize=7.5)

    ax.set_title("Figura 1 — Arquiteturas comparadas: atual, proposta e híbrida",
                 fontsize=11, fontweight="bold", pad=10)
    fig.tight_layout()
    out = os.path.join(OUT_DIR, "figura1_arquitetura.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Salvo: {out}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURA 2 — Scatter trade-off latência × custo (CNH + fatura)
# ══════════════════════════════════════════════════════════════════════════════
def figura2_tradeoff():
    subset = [r for r in rows if r["doc"] in ("cnh", "fatura")]

    fig, ax = plt.subplots(figsize=(8, 5))

    # aggregate per (modelo, modo): mean over docs
    from collections import defaultdict
    agg = defaultdict(lambda: {"lat": [], "custo": []})
    for r in subset:
        key = (r["modelo"], r["modo"])
        agg[key]["lat"].append(r["latencia_s"])
        agg[key]["custo"].append(r["custo_usd"])

    plotted = {}
    for (modelo, modo), vals in sorted(agg.items()):
        lat = np.mean(vals["lat"])
        custo = np.mean(vals["custo"])
        style = MODO_STYLE[modo]
        sc = ax.scatter(lat, custo, color=style["color"], marker=style["marker"],
                        s=100, zorder=4, edgecolors="black", linewidths=0.6)
        label = MODEL_SHORT.get(modelo, modelo)
        # offset annotation to avoid overlap
        offset = (6, 6) if modo == "single" else (-6, -14)
        ax.annotate(f"{label}\n({modo[:1].upper()})",
                    (lat, custo), textcoords="offset points", xytext=offset,
                    fontsize=7, color=style["color"])
        plotted[modo] = style

    handles = [mpatches.Patch(color=v["color"], label=v["label"]) for v in MODO_STYLE.values()]
    ax.legend(handles=handles, title="Modo", fontsize=8, title_fontsize=8)
    ax.set_xlabel("Latência (s)")
    ax.set_ylabel("Custo (US$/documento)")
    ax.set_title("Figura 2 — Trade-off latência × custo por modelo e modo\n"
                 "(média CNH + fatura)", fontweight="bold")
    fig.tight_layout()
    out = os.path.join(OUT_DIR, "figura2_tradeoff.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Salvo: {out}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURA 3 — Barras agrupadas single vs two_step (latência e custo)
# ══════════════════════════════════════════════════════════════════════════════
def figura3_2para1():
    # Use fatura (status ok for all three models) — most reliable comparison
    docs_used = ["cnh", "fatura"]
    subset = [r for r in rows if r["doc"] in docs_used]

    models = sorted(set(r["modelo"] for r in subset))
    modos = ["single", "two_step"]
    model_labels = [MODEL_SHORT.get(m, m) for m in models]

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=False)

    metrics = [
        ("latencia_s", "Latência (s)", axes[0]),
        ("custo_usd", "Custo (US$)", axes[1]),
    ]

    x = np.arange(len(models))
    width = 0.35

    for metric_key, ylabel, ax in metrics:
        for i, modo in enumerate(modos):
            vals = []
            for m in models:
                v = [r[metric_key] for r in subset if r["modelo"] == m and r["modo"] == modo]
                vals.append(np.mean(v) if v else 0)
            style = MODO_STYLE[modo]
            bars = ax.bar(x + (i - 0.5) * width, vals, width,
                          color=style["color"], label=style["label"],
                          hatch=style["hatch"], edgecolor="black",
                          linewidth=0.8, alpha=0.85)
            # value labels
            for bar, val in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.01 * max(vals) * 1.5,
                        f"{val:.3f}" if val < 0.01 else f"{val:.2f}",
                        ha="center", va="bottom", fontsize=7)

        ax.set_xticks(x)
        ax.set_xticklabels(model_labels, rotation=15, ha="right", fontsize=8)
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=8)

    axes[0].set_title("Latência (s)\n(média CNH + fatura)", fontweight="bold")
    axes[1].set_title("Custo (US$)\n(média CNH + fatura)", fontweight="bold")
    fig.suptitle("Figura 3 — Single-pass vs. duas etapas: latência e custo",
                 fontweight="bold", fontsize=12)
    fig.tight_layout()
    out = os.path.join(OUT_DIR, "figura3_2para1.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Salvo: {out}")


# ══════════════════════════════════════════════════════════════════════════════
# FIGURA 4 — Documento extenso: ingênuo vs híbrido
# ══════════════════════════════════════════════════════════════════════════════
def figura4_hibrido():
    # Numbers from paper_hibrido.md (exact values)
    lat_ingenuo = 615.1       # seconds (timed out / provider error)
    lat_hibrido_pymupdf = 4.71  # deterministic text extraction
    lat_hibrido_vlm = 4.3       # VLM on single figure page
    lat_hibrido_total = lat_hibrido_pymupdf + lat_hibrido_vlm

    custo_ingenuo = 0.0         # failed — None recorded as 0
    custo_hibrido = 0.0003855   # VLM on one page; PyMuPDF = $0

    labels = ["VLM ingênuo\n(PDF inteiro)", "Híbrido\n(PyMuPDF + VLM\nna figura)"]
    lats = [lat_ingenuo, lat_hibrido_total]
    custos = [custo_ingenuo, custo_hibrido]
    colors_lat = ["#d62728", "#2ca02c"]
    colors_cost = ["#d62728", "#2ca02c"]
    hatches = ["xx", ""]

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))

    # ── Latência ──
    ax = axes[0]
    bars = ax.bar(labels, lats, color=colors_lat, hatch=hatches,
                  edgecolor="black", linewidth=0.8, width=0.5)
    ax.set_ylabel("Latência (s)")
    ax.set_title("Latência (s)", fontweight="bold")
    # Annotate failure
    ax.text(0, lat_ingenuo + 5, "FALHA\n(erro do provedor)", ha="center",
            fontsize=9, color="#d62728", fontweight="bold")
    ax.text(1, lat_hibrido_total + 5,
            f"{lat_hibrido_total:.1f}s total\n(texto: {lat_hibrido_pymupdf}s\nVLM: {lat_hibrido_vlm}s)",
            ha="center", fontsize=8, color="#155724")
    # scale bar: add 15% headroom
    ax.set_ylim(0, lat_ingenuo * 1.18)
    # Red X on failed bar
    ax.text(0, lat_ingenuo * 0.5, "✗", ha="center", va="center",
            fontsize=40, color="white", fontweight="bold", alpha=0.6)

    # ── Custo ──
    ax2 = axes[1]
    bars2 = ax2.bar(labels, custos, color=colors_cost, hatch=hatches,
                    edgecolor="black", linewidth=0.8, width=0.5)
    ax2.set_ylabel("Custo (US$)")
    ax2.set_title("Custo (US$)", fontweight="bold")
    ax2.text(0, custo_ingenuo + 0.00002, "N/A (falhou)", ha="center",
             fontsize=9, color="#d62728", fontweight="bold")
    ax2.text(1, custo_hibrido + 0.00002, f"US$ {custo_hibrido:.5f}\n(só VLM na figura)",
             ha="center", fontsize=8, color="#155724")
    ax2.set_ylim(0, custo_hibrido * 3)

    fig.suptitle("Figura 4 — Documento extenso (42 págs): VLM ingênuo vs. abordagem híbrida",
                 fontweight="bold", fontsize=11)
    fig.tight_layout()
    out = os.path.join(OUT_DIR, "figura4_hibrido.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Salvo: {out}")


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    figura1_arquitetura()
    figura2_tradeoff()
    figura3_2para1()
    figura4_hibrido()
    print("\nTodas as figuras geradas em:", OUT_DIR)
    # report sizes
    for fname in ["figura1_arquitetura.png", "figura2_tradeoff.png",
                  "figura3_2para1.png", "figura4_hibrido.png"]:
        p = os.path.join(OUT_DIR, fname)
        size_kb = os.path.getsize(p) / 1024
        print(f"  {fname}: {size_kb:.1f} KB")
