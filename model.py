import numpy as np
import pandas as pd
from math import ceil


def forecast_demand(ingredient_df: pd.DataFrame, window: int = 7) -> dict:
    """
    Simple AI-style demand forecasting using moving average.
    Returns daily and weekly forecasts.
    """
    ingredient_df = ingredient_df.sort_values("date")
    sales = ingredient_df["quantity_sold"].values

    if len(sales) == 0:
        avg_daily = 0
    else:
        avg_daily = np.mean(sales[-window:])

    weekly_forecast = avg_daily * 7

    return {
        "avg_daily": round(float(avg_daily), 2),
        "weekly_forecast": round(float(weekly_forecast), 2),
    }


def optimize_inventory(
    forecast: dict,
    current_stock: float,
    lead_time_days: int,
    service_level: float,
) -> dict:
    """
    Basic inventory optimization logic using reorder point + safety stock.
    """
    avg_daily = forecast["avg_daily"]
    demand_during_lead = avg_daily * lead_time_days

    # Simple safety stock approximation
    safety_stock = avg_daily * lead_time_days * (1 - service_level)

    reorder_point = demand_during_lead + safety_stock
    order_qty = max(0, reorder_point - current_stock)

    return {
        "demand_during_lead": round(demand_during_lead, 2),
        "safety_stock": round(safety_stock, 2),
        "reorder_point": round(reorder_point, 2),
        "recommended_order": round(order_qty, 2),
        "current_stock": round(current_stock, 2),
    }


def generate_alerts(decision: dict) -> list:
    alerts = []
    if decision["current_stock"] < decision["reorder_point"]:
        alerts.append("Stock below reorder point. Place an order soon.")
    if decision["recommended_order"] == 0:
        alerts.append("Stock is sufficient for the lead time.")
    return alerts
