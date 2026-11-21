"""
visualizations.py — Plotly Chart Builder Module
================================================
Each function returns a Plotly figure object that the Streamlit app
renders with st.plotly_chart().
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ===================================================================
# COLOUR PALETTE — standard, professional tones
# ===================================================================
PALETTE = ["#2563eb", "#059669", "#d97706", "#dc2626", "#7c3aed",
           "#0891b2", "#65a30d", "#c026d3", "#ea580c", "#4f46e5"]
PRIMARY = "#2563eb"      # Blue
SECONDARY = "#1e40af"    # Darker blue
ACCENT = "#0369a1"       # Teal-blue
SUCCESS = "#16a34a"      # Green
WARNING = "#d97706"      # Amber
DANGER = "#dc2626"       # Red


def _default_layout(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply a consistent professional layout."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color="#1a1a2e")),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, sans-serif", size=13, color="#333"),
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(200,200,200,0.3)")
    return fig


# ===================================================================
# 1.  REVENUE LINE CHART  (Monthly Trends)
# ===================================================================

def plot_monthly_revenue(df: pd.DataFrame) -> go.Figure:
    """Line chart of monthly revenue trends."""
    fig = px.line(
        df, x="Month", y="Revenue",
        markers=True,
        labels={"Revenue": "Revenue (£)", "Month": ""},
    )
    fig.update_traces(
        line=dict(color=PRIMARY, width=3),
        marker=dict(size=7),
        hovertemplate="<b>%{x|%b %Y}</b><br>Revenue: £%{y:,.2f}<extra></extra>",
    )
    return _default_layout(fig, "Monthly Revenue Trend")


# ===================================================================
# 2.  BAR CHART — Top-Selling Products
# ===================================================================

def plot_top_products(df: pd.DataFrame, by: str = "TotalQuantity") -> go.Figure:
    """Horizontal bar chart of top products."""
    label = "Units Sold" if by == "TotalQuantity" else "Revenue (£)"
    fig = px.bar(
        df.sort_values(by, ascending=True),
        x=by, y="Description", orientation="h",
        labels={by: label, "Description": ""},
        color_discrete_sequence=[PRIMARY],
    )
    hover_fmt = "%{x:,}" if by == "TotalQuantity" else "£%{x:,.2f}"
    fig.update_traces(
        hovertemplate=f"<b>%{{y}}</b><br>{label}: {hover_fmt}<extra></extra>",
    )
    title = "Top 10 Products by Quantity" if by == "TotalQuantity" else "Top 10 Products by Revenue"
    return _default_layout(fig, title)


# ===================================================================
# 3.  PIE / DONUT CHART — Country-wise Revenue
# ===================================================================

def plot_country_revenue_pie(df: pd.DataFrame, n: int = 10) -> go.Figure:
    """Donut chart showing top N countries' revenue share."""
    top = df.head(n).copy()
    if len(df) > n:
        other = pd.DataFrame([{
            "Country": "Other",
            "TotalRevenue": df.iloc[n:]["TotalRevenue"].sum(),
        }])
        top = pd.concat([top, other], ignore_index=True)

    fig = px.pie(
        top, values="TotalRevenue", names="Country",
        hole=0.45,
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(
        textposition="inside", textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Revenue: £%{value:,.2f}<br>Share: %{percent}<extra></extra>",
    )
    return _default_layout(fig, "Revenue Distribution by Country")


# ===================================================================
# 4.  BAR CHART — Top Customers
# ===================================================================

def plot_top_customers(df: pd.DataFrame) -> go.Figure:
    """Bar chart of top customers by revenue."""
    fig = px.bar(
        df.sort_values("TotalRevenue", ascending=True),
        x="TotalRevenue", y="CustomerID", orientation="h",
        labels={"TotalRevenue": "Revenue (£)", "CustomerID": "Customer ID"},
        color_discrete_sequence=[ACCENT],
    )
    fig.update_traces(
        hovertemplate="<b>Customer %{y}</b><br>Revenue: £%{x:,.2f}<extra></extra>",
    )
    return _default_layout(fig, "Top 10 Customers by Revenue")


# ===================================================================
# 5.  BAR CHART — Country-wise Sales
# ===================================================================

def plot_country_sales_bar(df: pd.DataFrame) -> go.Figure:
    """Bar chart of top countries by revenue."""
    fig = px.bar(
        df,
        x="Country", y="TotalRevenue",
        labels={"TotalRevenue": "Revenue (£)", "Country": ""},
        color_discrete_sequence=[PRIMARY],
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Revenue: £%{y:,.2f}<extra></extra>",
    )
    return _default_layout(fig, "Top Countries by Revenue")


# ===================================================================
# 6.  DAILY REVENUE LINE CHART
# ===================================================================

def plot_daily_revenue(df: pd.DataFrame) -> go.Figure:
    """Line chart of daily revenue."""
    fig = px.line(
        df, x="Date", y="Revenue",
        labels={"Revenue": "Revenue (£)", "Date": ""},
    )
    fig.update_traces(
        line=dict(color=SECONDARY, width=1.5),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Revenue: £%{y:,.2f}<extra></extra>",
    )
    return _default_layout(fig, "Daily Revenue Trend")


# ===================================================================
# 7.  MoM GROWTH BAR CHART
# ===================================================================

def plot_mom_growth(df: pd.DataFrame) -> go.Figure:
    """Bar chart showing month-over-month revenue growth %."""
    colors = [SUCCESS if v >= 0 else DANGER for v in df["Growth_pct"]]
    fig = go.Figure(go.Bar(
        x=df["MonthLabel"],
        y=df["Growth_pct"],
        marker_color=colors,
        hovertemplate="<b>%{x}</b><br>Growth: %{y:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        yaxis_title="Growth (%)",
        xaxis_title="",
    )
    return _default_layout(fig, "Month-over-Month Revenue Growth")


# ===================================================================
# 8.  CUSTOMER SEGMENTS BAR CHART
# ===================================================================

def plot_customer_segments(df: pd.DataFrame) -> go.Figure:
    """Bar chart of customer frequency segments."""
    fig = px.bar(
        df, x="Segment", y="Customers",
        labels={"Customers": "Number of Customers", "Segment": "Purchase Frequency"},
        color_discrete_sequence=[ACCENT],
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Customers: %{y:,}<extra></extra>",
    )
    return _default_layout(fig, "Customer Purchase Frequency Distribution")


# ===================================================================
# 9.  REPEAT vs ONE-TIME PIE
# ===================================================================

def plot_repeat_vs_onetime(repeat: int, onetime: int) -> go.Figure:
    """Donut chart for repeat vs one-time customers."""
    fig = px.pie(
        values=[repeat, onetime],
        names=["Repeat Customers", "One-Time Customers"],
        hole=0.5,
        color_discrete_sequence=[SUCCESS, WARNING],
    )
    fig.update_traces(
        textinfo="value+percent",
        hovertemplate="<b>%{label}</b><br>Count: %{value:,}<br>%{percent}<extra></extra>",
    )
    return _default_layout(fig, "Repeat vs One-Time Customers")


# ===================================================================
# 10.  YEARLY COMPARISON BAR
# ===================================================================

def plot_yearly_revenue(df: pd.DataFrame) -> go.Figure:
    """Bar chart comparing yearly revenue."""
    fig = px.bar(
        df, x="Year", y="Revenue",
        labels={"Revenue": "Revenue (£)", "Year": ""},
        color_discrete_sequence=[SECONDARY],
        text_auto=",.0f",
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Revenue: £%{y:,.2f}<extra></extra>",
    )
    fig.update_xaxes(type="category")
    return _default_layout(fig, "Yearly Revenue Comparison")


# ===================================================================
# 11.  PRODUCT REVENUE CONTRIBUTION DONUT
# ===================================================================

def plot_product_contribution(df: pd.DataFrame) -> go.Figure:
    """Donut chart for product revenue contribution."""
    fig = px.pie(
        df, values="Revenue", names="Description",
        hole=0.45,
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(
        textposition="inside", textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Revenue: £%{value:,.2f}<br>Share: %{percent}<extra></extra>",
    )
    return _default_layout(fig, "Product Revenue Contribution")
