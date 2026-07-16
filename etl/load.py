"""Load: grava os datasets finais em Parquet (colunar, tipado, compacto)."""
import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def load_all(datasets: dict[str, pd.DataFrame]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    for name, df in datasets.items():
        df.to_parquet(OUTPUT_DIR / f"{name}.parquet", index=False)
