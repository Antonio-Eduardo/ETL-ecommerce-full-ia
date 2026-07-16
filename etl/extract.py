"""Extract: leitura dos CSVs brutos em assets/."""
import pandas as pd
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

# IDs e códigos são tratados como string para preservar zeros à esquerda
# e porque não são grandezas numéricas (não faz sentido somar/multiplicar).
_ID_COLUMNS_AS_STRING = [
    "customer_id", "customer_unique_id", "customer_zip_code_prefix",
    "order_id", "product_id", "seller_id", "seller_zip_code_prefix",
    "review_id", "geolocation_zip_code_prefix",
]


def _read_csv(filename: str) -> pd.DataFrame:
    # dtype=str na leitura evita que pandas infira zip codes como int e
    # descarte zeros à esquerda (ex.: "01037" -> 1037) antes que possamos corrigir.
    dtype_map = {col: str for col in _ID_COLUMNS_AS_STRING}
    df = pd.read_csv(ASSETS_DIR / filename, dtype=dtype_map)
    for col in _ID_COLUMNS_AS_STRING:
        if col in df.columns:
            df[col] = df[col].str.strip()
    zip_cols = [c for c in df.columns if c.endswith("zip_code_prefix")]
    for col in zip_cols:
        df[col] = df[col].str.zfill(5)
    return df


def extract_all() -> dict[str, pd.DataFrame]:
    """Carrega os 8 datasets brutos na ordem: dimensões primeiro, depois fatos."""
    return {
        "customers": _read_csv("olist_customers_dataset.csv"),
        "sellers": _read_csv("olist_sellers_dataset.csv"),
        "products": _read_csv("olist_products_dataset.csv"),
        "geolocation": _read_csv("olist_geolocation_dataset.csv"),
        "orders": _read_csv("olist_orders_dataset.csv"),
        "order_items": _read_csv("olist_order_items_dataset.csv"),
        "order_payments": _read_csv("olist_order_payments_dataset.csv"),
        "order_reviews": _read_csv("olist_order_reviews_dataset.csv"),
    }
