"""
database.py — SQLite Database & SQL Query Module
=================================================
Stores cleaned data in an in-memory (or file-based) SQLite database
and exposes helper functions that run SQL queries via pandas.
"""

import sqlite3
import pandas as pd
from typing import Optional


# ===================================================================
# CONNECTION MANAGEMENT
# ===================================================================

def get_connection(db_path: str = ":memory:") -> sqlite3.Connection:
    """Return a SQLite connection (defaults to in-memory)."""
    return sqlite3.connect(db_path, check_same_thread=False)


def store_data(df: pd.DataFrame, conn: sqlite3.Connection, table: str = "transactions") -> None:
    """Write a cleaned DataFrame into the SQLite database."""
    df.to_sql(table, conn, if_exists="replace", index=False)


# ===================================================================
# SQL QUERY HELPERS
# ===================================================================

def sql_total_revenue(conn: sqlite3.Connection) -> float:
    """Total revenue from all transactions."""
    query = "SELECT ROUND(SUM(Revenue), 2) AS TotalRevenue FROM transactions;"
    result = pd.read_sql_query(query, conn)
    return result.iloc[0, 0]


def sql_monthly_sales(conn: sqlite3.Connection) -> pd.DataFrame:
    """Monthly sales aggregation."""
    query = """
        SELECT
            strftime('%Y-%m', InvoiceDate) AS Month,
            ROUND(SUM(Revenue), 2)        AS TotalRevenue,
            COUNT(DISTINCT InvoiceNo)      AS OrderCount,
            SUM(Quantity)                  AS TotalQuantity
        FROM transactions
        GROUP BY Month
        ORDER BY Month;
    """
    return pd.read_sql_query(query, conn)


def sql_top_products(conn: sqlite3.Connection, n: int = 10) -> pd.DataFrame:
    """Top N products by revenue."""
    query = f"""
        SELECT
            Description,
            ROUND(SUM(Revenue), 2) AS TotalRevenue,
            SUM(Quantity)          AS TotalQuantity
        FROM transactions
        GROUP BY Description
        ORDER BY TotalRevenue DESC
        LIMIT {n};
    """
    return pd.read_sql_query(query, conn)


def sql_top_customers(conn: sqlite3.Connection, n: int = 10) -> pd.DataFrame:
    """Top N customers by revenue."""
    query = f"""
        SELECT
            CustomerID,
            ROUND(SUM(Revenue), 2)    AS TotalRevenue,
            COUNT(DISTINCT InvoiceNo) AS OrderCount
        FROM transactions
        GROUP BY CustomerID
        ORDER BY TotalRevenue DESC
        LIMIT {n};
    """
    return pd.read_sql_query(query, conn)


def sql_country_sales(conn: sqlite3.Connection) -> pd.DataFrame:
    """Country-wise sales breakdown."""
    query = """
        SELECT
            Country,
            ROUND(SUM(Revenue), 2)    AS TotalRevenue,
            COUNT(DISTINCT InvoiceNo) AS OrderCount,
            COUNT(DISTINCT CustomerID) AS CustomerCount
        FROM transactions
        GROUP BY Country
        ORDER BY TotalRevenue DESC;
    """
    return pd.read_sql_query(query, conn)


def sql_order_customer_counts(conn: sqlite3.Connection) -> pd.DataFrame:
    """Order count and customer count summary."""
    query = """
        SELECT
            COUNT(DISTINCT InvoiceNo)  AS TotalOrders,
            COUNT(DISTINCT CustomerID) AS TotalCustomers
        FROM transactions;
    """
    return pd.read_sql_query(query, conn)


def run_custom_query(conn: sqlite3.Connection, query: str) -> pd.DataFrame:
    """
    Execute an arbitrary read-only SQL query and return a DataFrame.
    Wraps errors to prevent SQL injection side-effects.
    """
    # Only allow SELECT statements for safety
    stripped = query.strip().upper()
    if not stripped.startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed for safety.")
    return pd.read_sql_query(query, conn)
