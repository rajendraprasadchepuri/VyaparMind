# VyaparMind: Intelligent Retail Operating System 🧠

![VyaparMind Logo](logo_no_text_3.svg)

> **Growth • Purity • Success**

VyaparMind is a next-generation Retail Management System designed to modernize small to medium businesses. It combines a lightning-fast Point of Sale (POS), robust Inventory Management, and AI-driven Analytics into a single, seamless platform.

## 🚀 Key Features

### 1. Point of Sale (POS) 💳

* **Fast Billing**: Add products via barcode search or name. Real-time stock verification prevents overselling.
* **Customer Loyalty**: Built-in CRM tracks customer visits and points.
  * **Earn**: Automatic point accumulation on purchases.
  * **Redeem**: Seamless redemption logic during checkout.
* **Hold / Resume**: Pause billing for a customer and resume anytime without losing cart data.
* **Professional Invoicing**: Generates GST-compliant, printable HTML receipts with customizable store details.

### 2. Smart Inventory 📦

* **Live Tracking**: Monitor stock levels, cost prices, and selling prices.
* **Low Stock Alerts**: Automatic warnings for items running low.
* **Bulk Updates**: Efficiently update multiple product details just by editing the grid.

### 3. Business Intelligence (AI) 🧠

* **Smart Restock**: Algorithms calculate "Days of Cover" based on sales velocity and recommend exact reorder quantities.
* **Market Basket Analysis**: Identifies products frequently bought together to suggest profitable combos.

### 4. Analytics Dashboard 📊

* **Real-time KPIs**: Revenue, Net Profit, and Item Volume tracking.
* **Visual Insights**: Interactive charts for daily sales trends and category performance.
* **Customer Insights**: Identify VIP customers and retention rates.

---

## 🛠️ Technical Architecture

VyaparMind is built for **Performance** and **Scale** by a Data Structures Expert.

* **Backend**: Python & SQLite (Optimized)
* **Frontend**: Streamlit (Reactive UI)
* **Performance Optimizations**:
  * **WAL Mode**: SQLite configured for Write-Ahead Logging to enable non-blocking concurrent reads/writes.
  * **Indexing**: Strategic B-Tree indexes on `products(name)`, `customers(phone)`, and `transactions(timestamp)` for $O(\log N)$ query performance.
  * **Batch Processing**: Transaction write paths use `executemany` to minimize I/O overhead.
  * **Smart Caching**: Implemented memoization (`@st.cache_data`) for instant data loading, with intelligent cache invalidation on write events.

---

## 💻 Installation & Setup

1. **Clone the Repository**

    ```bash
    git clone https://github.com/yourusername/vyaparmind.git
    cd vyaparmind
    ```

2. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Application**

    ```bash
    streamlit run app.py
    ```

4. **Login Credentials**
    * **Default Admin**: `admin` / `admin`
    * *You can create new users from the login screen.*

---

## ⚙️ Configuration

Go to the **Settings** page to verify:

* Store Name & Address
* GSTIN / Tax ID
* Footer Messages
* Logo Preferences

---

*Built with ❤️ for Modern Retail.*
