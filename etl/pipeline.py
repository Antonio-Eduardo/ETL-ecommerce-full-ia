"""Orquestrador do pipeline ETL: Extract -> Transform -> Load."""
from etl import extract, transform, load


def run() -> dict:
    raw = extract.extract_all()

    dim_customers = transform.transform_customers(raw["customers"])
    dim_sellers = transform.transform_sellers(raw["sellers"])
    dim_products = transform.transform_products(raw["products"])
    dim_geolocation = transform.transform_geolocation(raw["geolocation"])

    orders_clean = transform.transform_orders(raw["orders"])
    order_items_clean = transform.transform_order_items(raw["order_items"])
    order_payments_clean = transform.transform_order_payments(raw["order_payments"])
    order_reviews_clean = transform.transform_order_reviews(raw["order_reviews"])

    fact_order_items = transform.build_fact_order_items(
        order_items_clean, orders_clean, dim_customers, dim_products, dim_sellers
    )
    fact_orders = transform.build_fact_orders(
        orders_clean, order_payments_clean, order_reviews_clean
    )

    result = {
        "dim_customers": dim_customers,
        "dim_sellers": dim_sellers,
        "dim_products": dim_products,
        "dim_geolocation": dim_geolocation,
        "fact_orders": fact_orders,
        "fact_order_items": fact_order_items,
    }

    load.load_all(result)
    return result


if __name__ == "__main__":
    datasets = run()
    for name, df in datasets.items():
        print(f"{name}: {len(df)} registros, {len(df.columns)} colunas")
