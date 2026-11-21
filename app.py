"""
app.py — E-commerce Sales & Customer Analytics Dashboard
=========================================================
Main Streamlit application.  Run with:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os
import tempfile

# Local modules
from data_cleaning import load_dataset, validate_columns, clean_data, get_cleaning_summary
from analysis import (
    calculate_kpis,
    top_products_by_quantity, top_products_by_revenue,
    lowest_performing_products, product_revenue_contribution,
    top_customers_by_revenue, customer_purchase_frequency, customer_segments,
    monthly_revenue, daily_revenue, yearly_revenue, mom_revenue_growth,
    country_revenue, top_countries,
    generate_insights,
)
from database import get_connection, store_data, run_custom_query
from visualizations import (
    plot_monthly_revenue, plot_top_products, plot_country_revenue_pie,
    plot_top_customers, plot_country_sales_bar, plot_daily_revenue,
    plot_mom_growth, plot_customer_segments, plot_repeat_vs_onetime,
    plot_yearly_revenue, plot_product_contribution,
)


# ===================================================================
# PAGE CONFIG
# ===================================================================
st.set_page_config(
    page_title="E-commerce Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===================================================================
# CUSTOM CSS
# ===================================================================
st.markdown("""
<style>
    /* KPI card styling — clean white cards with subtle border */
    div[data-testid="stMetric"] {
        background: #ffffff;
        padding: 16px 20px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    div[data-testid="stMetric"] label {
        color: #6b7280 !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #1f2937 !important;
        font-weight: 600 !important;
    }
    /* Sidebar — light neutral background */
    section[data-testid="stSidebar"] {
        background: #f8f9fa;
        border-right: 1px solid #e5e7eb;
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: #374151;
    }
    /* Tab styling */
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# ===================================================================
# DATA LOADING & CACHING
# ===================================================================

DEFAULT_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "online_retail.csv")


@st.cache_data(show_spinner="Loading and cleaning data…")
def load_and_clean(filepath: str) -> tuple:
    """Load, validate, clean, and cache the dataset."""
    df_raw = load_dataset(filepath)
    is_valid, missing = validate_columns(df_raw)
    if not is_valid:
        return None, None, f"Missing required columns: {', '.join(missing)}"
    df_clean, report = clean_data(df_raw)
    return df_clean, report, None


@st.cache_resource(show_spinner="Initialising database…")
def init_database(df_hash: str, _df: pd.DataFrame):
    """Create SQLite connection and store data (cached by data hash)."""
    conn = get_connection()
    store_data(_df, conn)
    return conn


# ===================================================================
# SIDEBAR — Data Source & Filters
# ===================================================================

def render_sidebar():
    """Build the sidebar: data source toggle, filters, and info."""
    with st.sidebar:
        st.markdown("## 📊 Analytics Dashboard")
        st.divider()

        # --- Data source ---
        st.markdown("### 📁 Data Source")
        data_source = st.radio(
            "Choose data source:",
            ["Default Dataset (UCI Online Retail)", "Upload CSV"],
            label_visibility="collapsed",
        )

        filepath = None
        uploaded_file = None
        if data_source == "Upload CSV":
            uploaded_file = st.file_uploader("Upload your CSV", type=["csv"])
            if uploaded_file is not None:
                # Save to a temp file so load_dataset can use a path
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
                tmp.write(uploaded_file.getvalue())
                tmp.close()
                filepath = tmp.name
        else:
            if os.path.exists(DEFAULT_DATA_PATH):
                filepath = DEFAULT_DATA_PATH
            else:
                st.error(
                    "Default dataset not found. Please place `online_retail.csv` "
                    "in the `data/` folder or upload your own CSV."
                )
                st.stop()

        return filepath, uploaded_file


def render_filters(df: pd.DataFrame):
    """Sidebar filters — date range, country, product, customer."""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔍 Filters")

        # Date range
        min_date = df["InvoiceDate"].min().date()
        max_date = df["InvoiceDate"].max().date()
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        # Country
        countries = ["All"] + sorted(df["Country"].unique().tolist())
        selected_country = st.selectbox("Country", countries)

        # Product (top 50 for performance)
        top_prods = (
            df["Description"].value_counts().head(50).index.tolist()
        )
        products = ["All"] + top_prods
        selected_product = st.selectbox("Product", products)

        # Customer
        selected_customer = st.text_input("Customer ID (blank = all)")

        st.markdown("---")
        st.markdown(
            "<small>Built with ❤️ using Streamlit, Pandas & Plotly</small>",
            unsafe_allow_html=True,
        )

    return date_range, selected_country, selected_product, selected_customer


def apply_filters(
    df: pd.DataFrame,
    date_range,
    country: str,
    product: str,
    customer_id: str,
) -> pd.DataFrame:
    """Apply all sidebar filters and return the filtered DataFrame."""
    filtered = df.copy()

    # Date range filter
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        filtered = filtered[
            (filtered["InvoiceDate"] >= start) & (filtered["InvoiceDate"] <= end)
        ]

    # Country filter
    if country != "All":
        filtered = filtered[filtered["Country"] == country]

    # Product filter
    if product != "All":
        filtered = filtered[filtered["Description"] == product]

    # Customer ID filter
    if customer_id.strip():
        filtered = filtered[filtered["CustomerID"] == customer_id.strip()]

    return filtered


# ===================================================================
# MAIN APP
# ===================================================================

def main():
    # --- Sidebar: data source ---
    filepath, uploaded_file = render_sidebar()

    if filepath is None:
        st.info("👆 Please upload a CSV file to get started.")
        st.stop()

    # --- Load & clean ---
    df_clean, report, error = load_and_clean(filepath)

    if error:
        st.error(error)
        st.stop()

    if df_clean is None or df_clean.empty:
        st.warning("The cleaned dataset is empty. Check your data.")
        st.stop()

    # --- Sidebar: filters ---
    date_range, country, product, customer_id = render_filters(df_clean)
    df_filtered = apply_filters(df_clean, date_range, country, product, customer_id)

    if df_filtered.empty:
        st.warning("No records match the current filters. Try adjusting them.")
        st.stop()

    # --- Database ---
    df_hash = str(hash(df_clean.shape))
    conn = init_database(df_hash, df_clean)

    # --- KPIs (from filtered data) ---
    kpis = calculate_kpis(df_filtered)

    # --- Header ---
    st.markdown("# 📊 E-commerce Sales & Customer Analytics")
    st.caption(
        "Interactive dashboard for sales performance, "
        "customer behaviour, and business intelligence"
    )

    # --- Navigation Tabs ---
    tabs = st.tabs([
        "🏠 Executive Dashboard",
        "📦 Product Analytics",
        "👥 Customer Analytics",
        "📈 Sales Analytics",
        "🔎 Data Explorer",
    ])

    # ==== TAB 1: EXECUTIVE DASHBOARD ====
    with tabs[0]:
        _render_executive(df_filtered, kpis, report)

    # ==== TAB 2: PRODUCT ANALYTICS ====
    with tabs[1]:
        _render_products(df_filtered)

    # ==== TAB 3: CUSTOMER ANALYTICS ====
    with tabs[2]:
        _render_customers(df_filtered, kpis)

    # ==== TAB 4: SALES ANALYTICS ====
    with tabs[3]:
        _render_sales(df_filtered, conn)

    # ==== TAB 5: DATA EXPLORER ====
    with tabs[4]:
        _render_explorer(df_filtered, df_clean, conn, report)


# -------------------------------------------------------------------
# TAB RENDERERS
# -------------------------------------------------------------------

def _render_executive(df, kpis, report):
    """Executive Dashboard tab."""
    # --- KPI Cards ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"£{kpis['total_revenue']:,.2f}")
    c2.metric("Total Orders", f"{kpis['total_orders']:,}")
    c3.metric("Total Customers", f"{kpis['total_customers']:,}")
    c4.metric("Products Sold", f"{kpis['total_products_sold']:,}")

    c5, c6, c7 = st.columns(3)
    c5.metric("Avg Order Value", f"£{kpis['avg_order_value']:,.2f}")
    c6.metric("Repeat Customers", f"{kpis['repeat_customer_pct']:.1f}%")
    growth = kpis['revenue_growth_pct']
    c7.metric(
        "Revenue Growth (MoM)",
        f"{growth:+.2f}%",
        delta=f"{growth:+.2f}%",
    )

    st.markdown("---")

    # --- Monthly Revenue ---
    mr = monthly_revenue(df)
    st.plotly_chart(plot_monthly_revenue(mr), use_container_width=True)

    # --- Business Insights ---
    st.markdown("### 💡 Key Business Insights")
    insights = generate_insights(df, kpis)
    for insight in insights:
        st.markdown(f"- {insight}")


def _render_products(df):
    """Product Analytics tab."""
    st.markdown("### 📦 Product Performance")

    col1, col2 = st.columns(2)
    with col1:
        tp_qty = top_products_by_quantity(df)
        st.plotly_chart(plot_top_products(tp_qty, "TotalQuantity"), use_container_width=True)
    with col2:
        tp_rev = top_products_by_revenue(df)
        st.plotly_chart(plot_top_products(tp_rev, "TotalRevenue"), use_container_width=True)

    st.markdown("---")

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("#### 📊 Product Revenue Contribution")
        contrib = product_revenue_contribution(df)
        st.plotly_chart(plot_product_contribution(contrib), use_container_width=True)
    with col4:
        st.markdown("#### ⬇️ Lowest Performing Products")
        low = lowest_performing_products(df)
        st.dataframe(
            low.style.format({"TotalRevenue": "£{:,.2f}"}),
            use_container_width=True,
            hide_index=True,
        )


def _render_customers(df, kpis):
    """Customer Analytics tab."""
    st.markdown("### 👥 Customer Behaviour")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            plot_repeat_vs_onetime(kpis["repeat_customers"], kpis["one_time_customers"]),
            use_container_width=True,
        )
    with col2:
        seg = customer_segments(df)
        st.plotly_chart(plot_customer_segments(seg), use_container_width=True)

    st.markdown("---")

    st.markdown("#### 🏆 Top 10 Customers by Revenue")
    tc = top_customers_by_revenue(df)
    st.plotly_chart(plot_top_customers(tc), use_container_width=True)

    st.markdown("#### 📋 Customer Purchase Frequency")
    freq = customer_purchase_frequency(df).head(20)
    st.dataframe(freq, use_container_width=True, hide_index=True)


def _render_sales(df, conn):
    """Sales Analytics tab."""
    st.markdown("### 📈 Sales Trends")

    # Monthly
    mr = monthly_revenue(df)
    st.plotly_chart(plot_monthly_revenue(mr), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        # MoM Growth
        mom = mom_revenue_growth(df)
        if not mom.empty:
            st.plotly_chart(plot_mom_growth(mom), use_container_width=True)
    with col2:
        # Yearly
        yr = yearly_revenue(df)
        if len(yr) > 1:
            st.plotly_chart(plot_yearly_revenue(yr), use_container_width=True)
        else:
            st.info("Only one year of data available; yearly comparison skipped.")

    st.markdown("---")

    # Daily
    dr = daily_revenue(df)
    st.plotly_chart(plot_daily_revenue(dr), use_container_width=True)

    st.markdown("---")

    # Country-wise
    st.markdown("#### 🌍 Country-wise Sales Performance")
    cr = top_countries(df, 10)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(plot_country_sales_bar(cr), use_container_width=True)
    with col4:
        cr_all = country_revenue(df)
        st.plotly_chart(plot_country_revenue_pie(cr_all), use_container_width=True)


def _render_explorer(df_filtered, df_clean, conn, report):
    """Data Explorer tab — view, search, download, and run SQL."""
    st.markdown("### 🔎 Data Explorer")

    # --- Cleaning report ---
    with st.expander("📋 Data Cleaning Report", expanded=False):
        st.markdown(get_cleaning_summary(report))

    # --- Search & Filter ---
    st.markdown("#### 🔍 Search Records")
    search_term = st.text_input("Search by product description or Invoice No:")
    display_df = df_filtered
    if search_term.strip():
        mask = (
            df_filtered["Description"].str.contains(search_term, case=False, na=False)
            | df_filtered["InvoiceNo"].astype(str).str.contains(search_term, case=False, na=False)
        )
        display_df = df_filtered[mask]

    st.dataframe(display_df.head(500), use_container_width=True, hide_index=True)
    st.caption(f"Showing {min(500, len(display_df)):,} of {len(display_df):,} records")

    # --- Downloads ---
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Download Cleaned Dataset (CSV)",
            data=df_clean.to_csv(index=False).encode("utf-8"),
            file_name="cleaned_ecommerce_data.csv",
            mime="text/csv",
        )
    with col2:
        st.download_button(
            "⬇️ Download Filtered Report (CSV)",
            data=df_filtered.to_csv(index=False).encode("utf-8"),
            file_name="filtered_sales_report.csv",
            mime="text/csv",
        )

    # --- SQL Explorer ---
    st.markdown("---")
    st.markdown("#### 🗃️ SQL Data Explorer")
    st.info(
        "Run SELECT queries against the `transactions` table. "
        "Available columns: InvoiceNo, StockCode, Description, Quantity, "
        "InvoiceDate, UnitPrice, CustomerID, Country, Revenue."
    )
    sample_queries = {
        "Total Revenue": "SELECT ROUND(SUM(Revenue), 2) AS TotalRevenue FROM transactions;",
        "Top 5 Products": "SELECT Description, ROUND(SUM(Revenue),2) AS Revenue FROM transactions GROUP BY Description ORDER BY Revenue DESC LIMIT 5;",
        "Monthly Sales": "SELECT strftime('%Y-%m', InvoiceDate) AS Month, ROUND(SUM(Revenue),2) AS Revenue, COUNT(DISTINCT InvoiceNo) AS Orders FROM transactions GROUP BY Month ORDER BY Month;",
        "Top 5 Countries": "SELECT Country, ROUND(SUM(Revenue),2) AS Revenue FROM transactions GROUP BY Country ORDER BY Revenue DESC LIMIT 5;",
        "Top 5 Customers": "SELECT CustomerID, ROUND(SUM(Revenue),2) AS Revenue, COUNT(DISTINCT InvoiceNo) AS Orders FROM transactions GROUP BY CustomerID ORDER BY Revenue DESC LIMIT 5;",
    }
    selected_sample = st.selectbox("💡 Sample queries:", ["Custom"] + list(sample_queries.keys()))
    if selected_sample != "Custom":
        default_query = sample_queries[selected_sample]
    else:
        default_query = "SELECT * FROM transactions LIMIT 10;"

    sql_query = st.text_area("SQL Query:", value=default_query, height=100)

    if st.button("▶️ Run Query"):
        try:
            result = run_custom_query(conn, sql_query)
            st.dataframe(result, use_container_width=True, hide_index=True)
            st.caption(f"{len(result):,} rows returned")
        except Exception as e:
            st.error(f"Query error: {e}")


# ===================================================================
# ENTRY POINT
# ===================================================================

if __name__ == "__main__":
    main()
