# VyaparMind: The Intelligent Retail OS 🧠

![VyaparMind Logo](logo_no_text_3.svg)

> **Growth • Purity • Success**

VyaparMind is not just a POS. It is a complete **AI Operating System** for modern retail, designed to optimize every aspect of your business: Inventory, Suppliers, Staff, and Customers.

## 🚀 Key Modules

### A. Operations (The Brain) 🧠

1. **💳 Point of Sale (POS)**
    * Lightning-fast billing with barcode support.
    * Holds bills, redeems loyalty points, and handles GST invoices.

2. **🍏 FreshFlow (Zero-Waste Engine)**
    * **Dead Stock Prevention**: Tracks expiry dates at the batch level.
    * **Dynamic Pricing**: Automatically suggests discounts (e.g., 50% off) for items expiring soon to recover costs.

3. **🚚 VendorTrust (Control Tower)**
    * **Supplier Scorecards**: AI rates every supplier on "On-Time Reliability" and "Quality".
    * **Risk Warnings**: Alerts you before you place a PO with a high-risk vendor.

4. **🗣️ VoiceAudit (Hands-Free Inventory)**
    * **Voice Command**: "Add 50 Maggi" or "Set Coke Stock to 20".
    * **NLP Engine**: Understands natural language to make stock-taking 10x faster.

### B. Intelligence (The Vision) 🔮

5. **🌡️ IsoBar (Demand Sensing)**
    * **Context-Aware**: Predicts sales based on Weather (Rain? Heatwave?) and Events (Cricket Match? Diwali?).
    * **Forecasting**: "If tomorrow is Rainy, stock 200% more Tea."

2. **👥 ShiftSmart (Workforce Planner)**
    * **AI Rostering**: Uses IsoBar forecasts to calculate exact staffing needs.
    * **Optimization**: Prevents overstaffing on slow days and chaos on busy days.

### C. Growth (The Heart) ❤️

7. **🛡️ ChurnGuard (Retention Autopilot)**
    * **Ghost Detection**: Identifies VIPs who haven't visited in 30 days.
    * **Win-Back**: Auto-generates "We Miss You" offers to bring them back.

2. **🗺️ GeoViz (Catchment Analysis)**
    * **Heatmaps**: Visualizes exactly which neighborhoods/cities your revenue comes from.
    * **Strategy**: Helps you decide where to market or open your next store.

---

## 🛠️ Technical Architecture

* **Backend**: Python (Optimized for Speed)
* **Database**: SQLite with **WAL Mode** (Write-Ahead Logging) for high concurrency.
* **Performance**:
  * **Indexing**: B-Tree indexes on all critical keys.
  * **Caching**: aggressive `@st.cache_data` with smart invalidation.
  * **Batching**: `executemany` for bulk inserts.

## 💻 Installation

1. **Clone & Install**

    ```bash
    git clone https://github.com/yourusername/vyaparmind.git
    pip install -r requirements.txt
    ```

2. **Run**

    ```bash
    streamlit run app.py
    ```

3. **Login**
    * Default: `admin` / `admin`

---

*Built for the Future of Retail.*
