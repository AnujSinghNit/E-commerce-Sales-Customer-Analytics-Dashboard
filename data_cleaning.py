"""
data_cleaning.py — Data Cleaning & Preprocessing Module
========================================================
Handles all data loading, validation, cleaning, and preprocessing for
the E-commerce Sales & Customer Analytics Dashboard.

Cleaning decisions are documented inline and summarised via the
`get_cleaning_report()` function.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any


# ---------------------------------------------------------------------------
# 1. LOADING
# ---------------------------------------------------------------------------

def load_dataset(filepath: str) -> pd.DataFrame:
    """
    Load a dataset from a file path (CSV or Excel).

    Parameters
    ----------
    filepath : str
        Path to the data file (.csv, .xlsx, .xls).

    Returns
    -------
    pd.DataFrame
        Raw dataframe as-is from the file.
    """
    ext = filepath.rsplit(".", 1)[-1].lower()
    if ext == "csv":
        return pd.read_csv(filepath, encoding="ISO-8859-1")
    elif ext in ("xlsx", "xls"):
        return pd.read_excel(filepath, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported file format: .{ext}. Use .csv or .xlsx.")


# ---------------------------------------------------------------------------
# 2. VALIDATION
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "InvoiceNo", "StockCode", "Description",
    "Quantity", "InvoiceDate", "UnitPrice",
    "CustomerID", "Country",
]


def validate_columns(df: pd.DataFrame) -> Tuple[bool, list]:
    """
    Check whether the dataframe contains all required columns.

    Returns
    -------
    (is_valid, missing_cols)
    """
    existing = set(c.strip() for c in df.columns)
    missing = [c for c in REQUIRED_COLUMNS if c not in existing]
    return len(missing) == 0, missing


# ---------------------------------------------------------------------------
# 3. CLEANING PIPELINE
# ---------------------------------------------------------------------------

def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Full cleaning pipeline.  Returns the cleaned DataFrame **and** a dict
    with statistics about every step (used to build the cleaning report).

    Cleaning steps
    --------------
    1. Standardise column names (strip whitespace).
    2. Drop exact duplicate rows.
    3. Convert InvoiceDate to datetime.
    4. Ensure Quantity and UnitPrice are numeric.
    5. Remove cancelled / returned orders (InvoiceNo starts with 'C').
    6. Remove rows where Quantity <= 0 or UnitPrice <= 0.
    7. Drop rows with missing CustomerID (cannot attribute to a customer).
    8. Fill missing Description with 'Unknown'.
    9. Create Revenue column (Quantity × UnitPrice).
    10. Reset index.
    """
    report: Dict[str, Any] = {}
    report["rows_original"] = len(df)

    # --- Step 1: Strip column names ---
    df.columns = df.columns.str.strip()

    # --- Step 2: Drop exact duplicates ---
    before = len(df)
    df = df.drop_duplicates().copy()
    report["duplicates_removed"] = before - len(df)

    # --- Step 3: Convert InvoiceDate ---
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    bad_dates = df["InvoiceDate"].isna().sum()
    df = df.dropna(subset=["InvoiceDate"])
    report["invalid_dates_removed"] = int(bad_dates)

    # --- Step 4: Ensure numeric Quantity & UnitPrice ---
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    bad_nums = df[["Quantity", "UnitPrice"]].isna().any(axis=1).sum()
    df = df.dropna(subset=["Quantity", "UnitPrice"])
    report["non_numeric_removed"] = int(bad_nums)

    # --- Step 5: Remove cancelled / returned orders ---
    cancelled_mask = df["InvoiceNo"].astype(str).str.startswith("C")
    report["cancelled_orders_removed"] = int(cancelled_mask.sum())
    df = df[~cancelled_mask]

    # --- Step 6: Remove rows with Quantity <= 0 or UnitPrice <= 0 ---
    invalid_qty_price = ((df["Quantity"] <= 0) | (df["UnitPrice"] <= 0)).sum()
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]
    report["invalid_qty_price_removed"] = int(invalid_qty_price)

    # --- Step 7: Drop rows without CustomerID ---
    missing_cust = df["CustomerID"].isna().sum()
    df = df.dropna(subset=["CustomerID"])
    df["CustomerID"] = df["CustomerID"].astype(int).astype(str)
    report["missing_customer_removed"] = int(missing_cust)

    # --- Step 8: Fill missing Description ---
    missing_desc = df["Description"].isna().sum()
    df["Description"] = df["Description"].fillna("Unknown")
    report["missing_desc_filled"] = int(missing_desc)

    # --- Step 9: Create Revenue column ---
    df["Revenue"] = (df["Quantity"] * df["UnitPrice"]).round(2)

    # --- Step 10: Reset index ---
    df = df.reset_index(drop=True)

    report["rows_cleaned"] = len(df)
    report["rows_removed_total"] = report["rows_original"] - report["rows_cleaned"]

    return df, report


def get_cleaning_summary(report: Dict[str, Any]) -> str:
    """Return a human-readable multi-line summary of cleaning actions."""
    lines = [
        "## Data Cleaning Summary",
        f"- **Original rows:** {report['rows_original']:,}",
        f"- **Duplicate rows removed:** {report['duplicates_removed']:,}",
        f"- **Invalid dates removed:** {report['invalid_dates_removed']:,}",
        f"- **Non-numeric Quantity/UnitPrice removed:** {report['non_numeric_removed']:,}",
        f"- **Cancelled/returned orders removed:** {report['cancelled_orders_removed']:,}",
        f"- **Invalid Quantity/UnitPrice (≤0) removed:** {report['invalid_qty_price_removed']:,}",
        f"- **Missing CustomerID rows removed:** {report['missing_customer_removed']:,}",
        f"- **Missing Description filled:** {report['missing_desc_filled']:,}",
        f"- **Final cleaned rows:** {report['rows_cleaned']:,}",
        f"- **Total rows removed:** {report['rows_removed_total']:,}",
    ]
    return "\n".join(lines)
