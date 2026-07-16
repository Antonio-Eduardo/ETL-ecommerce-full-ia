"""Gera visualizações para os 3 achados críticos de ANALISE_NEGOCIO.md.

Cada gráfico corresponde a uma decisão de negócio do rank crítico:
1. Atraso de entrega x nota de review
2. Frete desproporcional ao preço do produto
3. Concentração de receita em vendedores (curva de Pareto)

Lê os datasets já processados em output/*.parquet e grava PNGs em output/charts/.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"

# Paleta validada (dataviz skill): ink, grid, hue sequencial e status.
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BLUE = "#2a78d6"      # magnitude neutra / dentro do esperado
CRITICAL = "#d03b3b"  # status crítico
WARNING = "#fab219"   # status alerta
GOOD = "#0ca30c"       # status bom

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": INK_SECONDARY,
    "text.color": INK_PRIMARY,
    "xtick.color": INK_MUTED,
    "ytick.color": INK_MUTED,
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
})


def _load():
    fact_orders = pd.read_parquet(OUTPUT_DIR / "fact_orders.parquet")
    fact_items = pd.read_parquet(OUTPUT_DIR / "fact_order_items.parquet")
    return fact_orders, fact_items


def chart_delay_vs_review(fact_orders: pd.DataFrame) -> None:
    """Achado crítico #1: atraso de entrega derruba a nota do cliente."""
    delivered = fact_orders[fact_orders["order_status"] == "delivered"].copy()
    bins = [-999, -7, 0, 7, 999]
    labels = ["Adiantado\n(>7d antes)", "No prazo", "Atraso\naté 7d", "Atraso\n>7d"]
    delivered["faixa"] = pd.cut(delivered["delivery_delay_days"], bins=bins, labels=labels)
    avg_by_bin = delivered.groupby("faixa", observed=True)["review_score"].mean().reindex(labels)

    colors = [BLUE, BLUE, WARNING, CRITICAL]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(avg_by_bin.index, avg_by_bin.values, color=colors, width=0.6)
    for rect, value in zip(bars, avg_by_bin.values):
        ax.text(rect.get_x() + rect.get_width() / 2, value + 0.08, f"{value:.2f}",
                 ha="center", va="bottom", fontsize=11, color=INK_PRIMARY, fontweight="bold")

    ax.set_ylim(0, 5.5)
    ax.set_ylabel("Nota média do review (1–5)")
    ax.set_title("Atraso de entrega derruba a satisfação do cliente", loc="left",
                  fontsize=13, fontweight="bold", color=INK_PRIMARY, pad=14)
    ax.text(0, 1.02, "Pedidos entregues, agrupados pela diferença entre entrega real e prazo estimado",
             transform=ax.transAxes, fontsize=9.5, color=INK_SECONDARY)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "01_atraso_vs_review.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)


def chart_frete_desproporcional(fact_items: pd.DataFrame) -> None:
    """Achado crítico #2: frete maior que o preço do produto em parte relevante dos itens."""
    ratio = fact_items["freight_value"] / fact_items["price"].replace(0, pd.NA)
    bins = [0, 0.25, 0.5, 0.75, 1.0, float("inf")]
    labels = ["até 25%", "25–50%", "50–75%", "75–100%", "acima de 100%\n(frete > preço)"]
    faixa = pd.cut(ratio, bins=bins, labels=labels, right=True)
    dist = faixa.value_counts(normalize=True).reindex(labels) * 100

    colors = [BLUE, BLUE, BLUE, WARNING, CRITICAL]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(dist.index, dist.values, color=colors, width=0.6)
    for rect, value in zip(bars, dist.values):
        ax.text(rect.get_x() + rect.get_width() / 2, value + 0.5, f"{value:.1f}%",
                 ha="center", va="bottom", fontsize=11, color=INK_PRIMARY, fontweight="bold")

    ax.set_ylim(0, max(dist.values) * 1.25)
    ax.set_ylabel("% dos itens vendidos")
    ax.set_xlabel("Frete como proporção do preço do produto")
    ax.set_title("Frete desproporcional ao valor do produto", loc="left",
                  fontsize=13, fontweight="bold", color=INK_PRIMARY, pad=14)
    ax.text(0, 1.02, "3,66% dos itens têm frete maior que o próprio preço do produto",
             transform=ax.transAxes, fontsize=9.5, color=INK_SECONDARY)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "02_frete_desproporcional.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)


def chart_concentracao_vendedores(fact_items: pd.DataFrame) -> None:
    """Achado crítico #3: concentração de receita nos vendedores top (curva de Pareto)."""
    seller_rev = fact_items.groupby("seller_id")["total_item_value"].sum().sort_values(ascending=False)
    n = len(seller_rev)
    cum_pct_revenue = (seller_rev.cumsum() / seller_rev.sum() * 100).values
    pct_sellers = [(i + 1) / n * 100 for i in range(n)]

    idx_10pct = int(n * 0.10) - 1
    revenue_at_10pct = cum_pct_revenue[idx_10pct]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(pct_sellers, cum_pct_revenue, color=BLUE, linewidth=2.5)
    ax.fill_between(pct_sellers, cum_pct_revenue, color=BLUE, alpha=0.08)

    ax.axvline(10, color=CRITICAL, linestyle="--", linewidth=1.5)
    ax.axhline(revenue_at_10pct, color=CRITICAL, linestyle="--", linewidth=1.5)
    ax.plot([10], [revenue_at_10pct], "o", color=CRITICAL, markersize=8, zorder=5)
    ax.annotate(
        f"Top 10% dos vendedores\n= {revenue_at_10pct:.1f}% da receita",
        xy=(10, revenue_at_10pct), xytext=(28, revenue_at_10pct - 18),
        fontsize=10.5, color=INK_PRIMARY, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=INK_SECONDARY, lw=1.2),
    )

    ax.set_xlim(0, 100)
    ax.set_ylim(0, 105)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter())
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.set_xlabel("% dos vendedores (ordenados do maior para o menor faturamento)")
    ax.set_ylabel("% acumulado da receita")
    ax.set_title("Concentração de receita entre vendedores", loc="left",
                  fontsize=13, fontweight="bold", color=INK_PRIMARY, pad=14)
    ax.text(0, 1.02, "Curva de Pareto — receita acumulada por vendedor",
             transform=ax.transAxes, fontsize=9.5, color=INK_SECONDARY)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "03_concentracao_vendedores.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)


def run() -> None:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    fact_orders, fact_items = _load()
    chart_delay_vs_review(fact_orders)
    chart_frete_desproporcional(fact_items)
    chart_concentracao_vendedores(fact_items)
    print(f"3 graficos gerados em {CHARTS_DIR}")


if __name__ == "__main__":
    run()
