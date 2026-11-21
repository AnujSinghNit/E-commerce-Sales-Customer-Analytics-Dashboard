# 📊 E-commerce Sales & Customer Analytics Dashboard

An interactive **Data Analytics** web application built with **Python**, **SQL**, **Pandas**, and **Streamlit** to analyse real-world e-commerce sales data.

The dashboard helps businesses understand sales performance, customer purchasing behaviour, product performance, revenue trends, and business growth through interactive visualisations and data-driven insights.

**Technologies:** Python | Streamlit | Pandas | Plotly | SQLite
---

## 🚀 Features

### 📌 Executive Dashboard
- KPI cards (Revenue, Orders, Customers, Products Sold, AOV, Growth)
- Monthly revenue trend chart
- Auto-generated business insights from actual data

### 📦 Product Analytics
- Top 10 best-selling products (by quantity and revenue)
- Product revenue contribution (donut chart)
- Lowest-performing products table

### 👥 Customer Analytics
- Repeat vs one-time customer breakdown
- Customer purchase frequency distribution
- Top 10 customers by revenue

### 📈 Sales Analytics
- Monthly & daily revenue trends
- Month-over-month revenue growth
- Yearly comparison (when multiple years exist)
- Country-wise sales performance (bar + donut chart)

### 🔎 Data Explorer
- View, search, and filter the cleaned dataset
- Download cleaned data and filtered reports as CSV
- Run custom SQL queries against the database
- Sample SQL queries provided

### 🔍 Interactive Filters
- Date range filter
- Country filter
- Product filter
- Customer ID filter

All charts, KPIs, and tables update dynamically when filters change.

---

## 📂 Project Structure

```
├── app.py                  # Main Streamlit application
├── data_cleaning.py        # Data cleaning & preprocessing
├── analysis.py             # EDA & KPI calculations
├── database.py             # SQLite database & SQL queries
├── visualizations.py       # Plotly chart builders
├── data/
│   └── online_retail.csv   # UCI Online Retail dataset
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 📊 Dataset

This project uses the **UCI Online Retail Dataset** — a real-world transactional dataset containing all transactions occurring between 01/12/2010 and 09/12/2011 for a UK-based online retail company.

| Column      | Description                                      |
|-------------|--------------------------------------------------|
| InvoiceNo   | Invoice number (prefix 'C' = cancellation)       |
| StockCode   | Product code                                     |
| Description | Product name                                     |
| Quantity    | Quantity purchased per transaction                |
| InvoiceDate | Date and time of the transaction                  |
| UnitPrice   | Unit price in GBP (£)                             |
| CustomerID  | Unique customer identifier                       |
| Country     | Customer's country                               |

**Source:** [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/datasets/Online+Retail)

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/ecommerce-analytics-dashboard.git
   cd ecommerce-analytics-dashboard
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```

4. Open **http://localhost:8501** in your browser.

---

## ☁️ Deploy on Streamlit Cloud

1. Push all project files to a **GitHub repository**.
2. Go to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **"New app"**.
4. Connect your GitHub repository.
5. Set `app.py` as the entry-point file.
6. Click **Deploy**.

> **Note:** The dataset (`data/online_retail.csv`) is included in the repository. If the file exceeds GitHub's size limit, consider using Git LFS or providing a download script.

---

## 🧹 Data Cleaning Pipeline

The following cleaning steps are applied automatically:

1. Strip whitespace from column names
2. Remove exact duplicate rows
3. Convert `InvoiceDate` to datetime format
4. Ensure `Quantity` and `UnitPrice` are numeric
5. Remove cancelled/returned orders (InvoiceNo starting with 'C')
6. Remove rows where Quantity ≤ 0 or UnitPrice ≤ 0
7. Drop rows with missing `CustomerID`
8. Fill missing `Description` with 'Unknown'
9. Create `Revenue` column (Quantity × UnitPrice)

All cleaning statistics are available in the **Data Explorer** tab.

---

## 📈 KPIs Calculated

| KPI                       | Formula                                     |
|---------------------------|---------------------------------------------|
| Total Revenue             | Sum of all Revenue                          |
| Total Orders              | Count of unique InvoiceNo                   |
| Total Products Sold       | Sum of Quantity                              |
| Total Customers           | Count of unique CustomerID                  |
| Average Order Value (AOV) | Total Revenue ÷ Total Orders                |
| Repeat Customer %         | Customers with >1 order ÷ Total Customers   |
| Revenue Growth (MoM)      | (Current Month - Previous Month) ÷ Previous |

---

## 🗃️ SQL Queries

The cleaned data is stored in an **SQLite** database. You can run custom SQL queries in the **Data Explorer** tab. Example queries:

```sql
-- Total Revenue
SELECT ROUND(SUM(Revenue), 2) AS TotalRevenue FROM transactions;

-- Monthly Sales
SELECT strftime('%Y-%m', InvoiceDate) AS Month,
       ROUND(SUM(Revenue), 2) AS Revenue
FROM transactions
GROUP BY Month ORDER BY Month;

-- Top 5 Products
SELECT Description, ROUND(SUM(Revenue), 2) AS Revenue
FROM transactions
GROUP BY Description
ORDER BY Revenue DESC LIMIT 5;
```

---

## 🧰 Tech Stack

| Technology | Purpose                        |
|------------|--------------------------------|
| Python     | Core programming language      |
| Pandas     | Data manipulation & analysis   |
| NumPy      | Numerical operations           |
| SQLite     | Database storage & SQL queries |
| Streamlit  | Web application framework      |
| Plotly     | Interactive data visualisation |

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

- **Dataset:** [UCI Machine Learning Repository — Online Retail Dataset](https://archive.ics.uci.edu/ml/datasets/Online+Retail)
- **Framework:** [Streamlit](https://streamlit.io/)
- **Charts:** [Plotly](https://plotly.com/python/)
