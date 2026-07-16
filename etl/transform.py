"""Transform: limpeza, padronização e modelagem em dimensões/fatos."""
import pandas as pd

DATE_COLUMNS_ORDERS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


def _standardize_text(series: pd.Series) -> pd.Series:
    return series.str.strip().str.title()


def transform_customers(customers: pd.DataFrame) -> pd.DataFrame:
    df = customers.copy()
    df["customer_city"] = _standardize_text(df["customer_city"])
    df["customer_state"] = df["customer_state"].str.strip().str.upper()
    return df.drop_duplicates(subset="customer_id")


def transform_sellers(sellers: pd.DataFrame) -> pd.DataFrame:
    df = sellers.copy()
    df["seller_city"] = _standardize_text(df["seller_city"])
    df["seller_state"] = df["seller_state"].str.strip().str.upper()
    return df.drop_duplicates(subset="seller_id")


def transform_products(products: pd.DataFrame) -> pd.DataFrame:
    df = products.copy()
    # Categoria ausente vira rótulo explícito em vez de nulo silencioso,
    # já que "sem categoria" é uma informação de negócio válida.
    df["product_category_name"] = df["product_category_name"].fillna("outros").str.strip()
    numeric_cols = [
        "product_name_lenght", "product_description_lenght", "product_photos_qty",
        "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.drop_duplicates(subset="product_id")


def transform_geolocation(geolocation: pd.DataFrame) -> pd.DataFrame:
    """Agrega múltiplas coordenadas por CEP em uma única linha (média),
    já que o uso pretendido é localização aproximada, não endereço exato.
    """
    df = geolocation.drop_duplicates()
    df["geolocation_city"] = _standardize_text(df["geolocation_city"])
    df["geolocation_state"] = df["geolocation_state"].str.strip().str.upper()
    agg = (
        df.groupby("geolocation_zip_code_prefix")
        .agg(
            geolocation_lat=("geolocation_lat", "mean"),
            geolocation_lng=("geolocation_lng", "mean"),
            geolocation_city=("geolocation_city", lambda s: s.mode().iloc[0]),
            geolocation_state=("geolocation_state", lambda s: s.mode().iloc[0]),
        )
        .reset_index()
    )
    return agg


def transform_orders(orders: pd.DataFrame) -> pd.DataFrame:
    df = orders.copy()
    for col in DATE_COLUMNS_ORDERS:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["order_status"] = df["order_status"].str.strip().str.lower()

    # Colunas derivadas de negócio: SLA de entrega e tempo de aprovação.
    # Nulas quando a etapa correspondente não ocorreu (ex.: pedido cancelado).
    df["delivery_delay_days"] = (
        df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]
    ).dt.days
    df["approval_time_hours"] = (
        df["order_approved_at"] - df["order_purchase_timestamp"]
    ).dt.total_seconds() / 3600

    return df.drop_duplicates(subset="order_id")


def transform_order_items(order_items: pd.DataFrame) -> pd.DataFrame:
    df = order_items.copy()
    df["shipping_limit_date"] = pd.to_datetime(df["shipping_limit_date"], errors="coerce")
    df["total_item_value"] = df["price"] + df["freight_value"]
    return df


def transform_order_payments(order_payments: pd.DataFrame) -> pd.DataFrame:
    df = order_payments.copy()
    df["payment_type"] = df["payment_type"].str.strip().str.lower()
    return df


def transform_order_reviews(order_reviews: pd.DataFrame) -> pd.DataFrame:
    df = order_reviews.copy()
    df["review_creation_date"] = pd.to_datetime(df["review_creation_date"], errors="coerce")
    df["review_answer_timestamp"] = pd.to_datetime(df["review_answer_timestamp"], errors="coerce")
    # Ausência de comentário é informação válida (nem todo review tem texto),
    # não um erro de coleta — por isso vira flag em vez de ser tratada como nulo a imputar.
    df["has_comment"] = df["review_comment_message"].notna() | df["review_comment_title"].notna()
    return df


def build_fact_order_items(
    order_items: pd.DataFrame,
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    sellers: pd.DataFrame,
) -> pd.DataFrame:
    """Fato de grão fino (um item de pedido por linha), com FKs validadas 1:1/N:1."""
    fact = (
        order_items
        .merge(orders[["order_id", "customer_id", "order_status", "order_purchase_timestamp"]],
               on="order_id", how="inner")
        .merge(customers[["customer_id", "customer_state", "customer_city"]],
                on="customer_id", how="left")
        .merge(products[["product_id", "product_category_name"]], on="product_id", how="left")
        .merge(sellers[["seller_id", "seller_state", "seller_city"]], on="seller_id", how="left")
    )
    return fact


def build_fact_orders(
    orders: pd.DataFrame,
    order_payments: pd.DataFrame,
    order_reviews: pd.DataFrame,
) -> pd.DataFrame:
    """Fato de grão pedido, com pagamento agregado (soma, pois um pedido pode ter
    N parcelas/métodos) e review mais recente (pode haver mais de uma por pedido).
    """
    payments_agg = (
        order_payments.groupby("order_id")
        .agg(total_payment_value=("payment_value", "sum"),
             payment_installments_max=("payment_installments", "max"),
             payment_types=("payment_type", lambda s: ",".join(sorted(set(s)))))
        .reset_index()
    )

    reviews_latest = (
        order_reviews.sort_values("review_answer_timestamp")
        .drop_duplicates(subset="order_id", keep="last")
        [["order_id", "review_score", "has_comment"]]
    )

    fact = (
        orders
        .merge(payments_agg, on="order_id", how="left")
        .merge(reviews_latest, on="order_id", how="left")
    )
    return fact
