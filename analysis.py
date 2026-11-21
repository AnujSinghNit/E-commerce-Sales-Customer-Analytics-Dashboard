"""
analysis.py — Exploratory Data Analysis & KPI Calculation Module
=================================================================
Pure Pandas-based analysis functions.  Each function takes a cleaned
DataFrame and returns results (scalars, Series, or DataFrames) that
the Streamlit app and visualisation layer consume.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


# ===================================================================
# 1.  OVERALL SALES KPIs
# ===================================================================

def calculate_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Return a dictionary of top-level KPIs.

    Keys
    ----
    total_revenue, total_orders, total_products_sold, total_customers,
    avg_order_value, repeat_customer_pct, revenue_growth_pct
    """
    total_revenue = round(df["Revenue"].sum(), 2)
    total_orders = df["InvoiceNo"].nunique()
    total_products_sold = int(df["Quantity"].sum())
    total_customers = df["CustomerID"].nunique()

    # Average Order Value = Total Revenue / Total Orders
    aov = round(total_revenue / total_orders, 2) if total_orders else 0

    # Repeat customers: customers with more than 1 unique invoice
    orders_per_customer = df.groupby("CustomerID")["InvoiceNo"].nunique()
    repeat_customers = int((orders_per_customer > 1).sum())
    repeat_pct = round(repeat_customers / total_customers * 100, 2) if total_customers else 0

    # Revenue growth %: compare last month to the one before it
    revenue_growth_pct = _revenue_growth(df)

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_products_sold": total_products_sold,
        "total_customers": total_customers,
        "avg_order_value": aov,
        "repeat_customers": repeat_customers,
        "one_time_customers": total_customers - repeat_customers,
        "repeat_customer_pct": repeat_pct,
        "revenue_growth_pct": revenue_growth_pct,
    }


def _revenue_growth(df: pd.DataFrame) -> float:
    """Month-over-month revenue growth for the two most recent months."""
    monthly = (
        df.set_index("InvoiceDate")
        .resample("M")["Revenue"]
        .sum()
        .sort_index()
    )
    if len(monthly) < 2:
        return 0.0
    last, prev = monthly.iloc[-1], monthly.iloc[-2]
    if prev == 0:
        return 0.0
    return round((last - prev) / prev * 100, 2)


# ===================================================================
# 2.  PRODUCT ANALYSIS
# ===================================================================

def top_products_by_quantity(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N products by total quantity sold."""
    return (
        df.groupby("Description")["Quantity"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
        .rename(columns={"Quantity": "TotalQuantity"})
    )


def top_products_by_revenue(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N products by total revenue."""
    return (
        df.groupby("Description")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
        .rename(columns={"Revenue": "TotalRevenue"})
    )


def lowest_performing_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Bottom N products by total revenue."""
    return (
        df.groupby("Description")["Revenue"]
        .sum()
        .sort_values(ascending=True)
        .head(n)
        .reset_index()
        .rename(columns={"Revenue": "TotalRevenue"})
    )


def product_revenue_contribution(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Revenue contribution % for top N products (rest grouped as 'Other')."""
    total = df["Revenue"].sum()
    prod = (
        df.groupby("Description")["Revenue"]
        .sum()
        .sort_values(ascending=False)
    )
    top = prod.head(n).reset_index()
    top.columns = ["Description", "Revenue"]
    other_rev = prod.iloc[n:].sum()
    other_row = pd.DataFrame([{"Description": "Other", "Revenue": other_rev}])
    result = pd.concat([top, other_row], ignore_index=True)
    result["Percentage"] = (result["Revenue"] / total * 100).round(2)
    return result


# ===================================================================
# 3.  CUSTOMER ANALYSIS
# ===================================================================

def top_customers_by_revenue(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N customers by total revenue."""
    return (
        df.groupby("CustomerID")["Revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
        .rename(columns={"Revenue": "TotalRevenue"})
    )


def customer_purchase_frequency(df: pd.DataFrame) -> pd.DataFrame:
    """Number of unique orders per customer."""
    return (
        df.groupby("CustomerID")["InvoiceNo"]
        .nunique()
        .reset_index()
        .rename(columns={"InvoiceNo": "OrderCount"})
        .sort_values("OrderCount", ascending=False)
    )


def customer_segments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Segment customers into frequency buckets.
    """
    freq = customer_purchase_frequency(df)
    bins = [0, 1, 3, 5, 10, float("inf")]
    labels = ["1 order", "2-3 orders", "4-5 orders", "6-10 orders", "10+ orders"]
    freq["Segment"] = pd.cut(freq["OrderCount"], bins=bins, labels=labels)
    return freq.groupby("Segment", observed=False).size().reset_index(name="Customers")


# ===================================================================
# 4.  TIME-BASED ANALYSIS
# ===================================================================

def monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly aggregated revenue."""
    monthly = (
        df.set_index("InvoiceDate")
        .resample("M")["Revenue"]
        .sum()
        .reset_index()
    )
    monthly.columns = ["Month", "Revenue"]
    monthly["MonthLabel"] = monthly["Month"].dt.strftime("%b %Y")
    return monthly


def daily_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Daily aggregated revenue."""
    daily = (
        df.set_index("InvoiceDate")
        .resample("D")["Revenue"]
        .sum()
        .reset_index()
    )
    daily.columns = ["Date", "Revenue"]
    return daily


def yearly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Yearly aggregated revenue (useful when multiple years exist)."""
    df = df.copy()
    df["Year"] = df["InvoiceDate"].dt.year
    return (
        df.groupby("Year")["Revenue"]
        .sum()
        .reset_index()
    )


def mom_revenue_growth(df: pd.DataFrame) -> pd.DataFrame:
    """Month-over-month revenue growth %."""
    monthly = monthly_revenue(df)
    monthly["PrevRevenue"] = monthly["Revenue"].shift(1)
    monthly["Growth_pct"] = (
        (monthly["Revenue"] - monthly["PrevRevenue"]) / monthly["PrevRevenue"] * 100
    ).round(2)
    return monthly.dropna(subset=["Growth_pct"])


# ===================================================================
# 5.  COUNTRY ANALYSIS
# ===================================================================

def country_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue by country, sorted descending."""
    return (
        df.groupby("Country")
        .agg(TotalRevenue=("Revenue", "sum"), OrderCount=("InvoiceNo", "nunique"))
        .sort_values("TotalRevenue", ascending=False)
        .reset_index()
    )


def top_countries(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N countries by revenue."""
    return country_revenue(df).head(n)


# ===================================================================
# 6.  BUSINESS INSIGHTS  (auto-generated from data)
# ===================================================================

def generate_insights(df: pd.DataFrame, kpis: Dict[str, Any]) -> list:
    """
    Return a list of plain-English insight strings derived
    from actual data — nothing hard-coded.
    """
    insights = []

    # --- Highest revenue country ---
    cr = country_revenue(df)
    if not cr.empty:
        top_country = cr.iloc[0]
        insights.append(
            f"🌍 **{top_country['Country']}** is the highest revenue-generating "
            f"country, contributing **£{top_country['TotalRevenue']:,.2f}** "
            f"across **{top_country['OrderCount']:,}** orders."
        )

    # --- Best-selling product ---
    tp = top_products_by_revenue(df, 1)
    if not tp.empty:
        insights.append(
            f"🏆 **{tp.iloc[0]['Description']}** is the top revenue-generating "
            f"product with **£{tp.iloc[0]['TotalRevenue']:,.2f}** in total sales."
        )

    # --- Best & worst months ---
    mr = monthly_revenue(df)
    if len(mr) >= 2:
        best = mr.loc[mr["Revenue"].idxmax()]
        worst = mr.loc[mr["Revenue"].idxmin()]
        insights.append(
            f"📈 The best month for revenue was **{best['MonthLabel']}** "
            f"(£{best['Revenue']:,.2f}), while the lowest was "
            f"**{worst['MonthLabel']}** (£{worst['Revenue']:,.2f})."
        )

    # --- Customer retention ---
    insights.append(
        f"🔁 **{kpis['repeat_customer_pct']:.1f}%** of customers are repeat "
        f"buyers ({kpis['repeat_customers']:,} out of {kpis['total_customers']:,}). "
        f"Investing in loyalty programmes could convert the "
        f"**{kpis['one_time_customers']:,}** one-time buyers into regulars."
    )

    # --- AOV insight ---
    insights.append(
        f"💰 The Average Order Value is **£{kpis['avg_order_value']:,.2f}**. "
        f"Strategies like bundling or upselling could increase this further."
    )

    # --- Revenue growth ---
    growth = kpis["revenue_growth_pct"]
    direction = "grew" if growth >= 0 else "declined"
    insights.append(
        f"📊 Month-over-month revenue **{direction}** by "
        f"**{abs(growth):.2f}%** in the most recent period."
    )

    # --- Top customer ---
    tc = top_customers_by_revenue(df, 1)
    if not tc.empty:
        insights.append(
            f"👤 Customer **{tc.iloc[0]['CustomerID']}** is the highest spender "
            f"with **£{tc.iloc[0]['TotalRevenue']:,.2f}** in total purchases."
        )

    return insights
