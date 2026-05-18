from __future__ import annotations

from dataclasses import dataclass

from .models import Product, SalesRecord


@dataclass(frozen=True)
class SimulationMetrics:
    base_sales: int
    base_profit: float
    new_price: float
    predicted_sales: int
    predicted_profit: float
    price_change_rate: float
    sales_change_rate: float


def compute_baseline(product: Product) -> tuple[int, float]:
    qs = SalesRecord.objects.filter(product=product)
    base_sales = qs.values_list("quantity", flat=True)
    base_sales_total = int(sum(base_sales)) if base_sales else 0

    base_profit = 0.0
    for r in qs:
        base_profit += (float(r.price) - float(product.cost)) * int(r.quantity)

    return base_sales_total, float(base_profit)


def simulate_price_change(
    *,
    product: Product,
    price_change_rate: float,
    base_sales: int,
) -> SimulationMetrics:
    sensitivity = float(product.price_sensitivity)
    sales_change_rate = float(price_change_rate) * sensitivity

    predicted_sales = int(round(base_sales * (1 - sales_change_rate)))
    if predicted_sales < 0:
        predicted_sales = 0

    new_price = float(product.price) * (1 + float(price_change_rate))
    predicted_profit = (new_price - float(product.cost)) * predicted_sales

    base_profit = (float(product.price) - float(product.cost)) * base_sales

    return SimulationMetrics(
        base_sales=base_sales,
        base_profit=float(base_profit),
        new_price=float(new_price),
        predicted_sales=int(predicted_sales),
        predicted_profit=float(predicted_profit),
        price_change_rate=float(price_change_rate),
        sales_change_rate=float(sales_change_rate),
    )
