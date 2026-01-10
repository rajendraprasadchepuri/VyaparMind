
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

1. **🌡️ IsoBar (Demand Sensing)**
    * **Context-Aware**: Predicts sales based on Weather (Rain? Heatwave?) and Events (Cricket Match? Diwali?).
    * **Forecasting**: "If tomorrow is Rainy, stock 200% more Tea."

2. **👥 ShiftSmart (Workforce Planner)**
    * **AI Rostering**: Uses IsoBar forecasts to calculate exact staffing needs.
    * **Optimization**: Prevents overstaffing on slow days and chaos on busy days.

### C. Growth (The Heart) ❤️

1. **🛡️ ChurnGuard (Retention Autopilot)**
    * **Ghost Detection**: Identifies VIPs who haven't visited in 30 days.
    * **Win-Back**: Auto-generates "We Miss You" offers to bring them back.

2. **🗺️ GeoViz (Catchment Analysis)**
    * **Heatmaps**: Visualizes exactly which neighborhoods/cities your revenue comes from.
    * **Strategy**: Helps you decide where to market or open your next store.

### D. Blue Ocean Innovations (The Edge) 🚀

1. **🕸️ StockSwap (Retailer Mesh)**
    * **Peer-to-Peer**: Exchange dead stock with other nearby retailers.
    * **Efficiency**: Liquify your stuck inventory instead of writing it off.

2. **🧬 ShelfSense (Science of Merchandising)**
    * **Molecular Intelligence**: Knows that *Apples release Ethylene* and spoils *Bananas*.
    * **Psychology**: Suggests placing impulse buys at eye level near checkout.

3. **🔮 CrowdStock (Zero-Risk Inventory)**
    * **Pre-Launch**: List new items (e.g., "Vegan Cheese") and stock only if 50 people vote for it.
    * **No Risk**: Eliminate demand-side uncertainty.

---

## 🔐 Security & Enterprise Features

* **RBAC (Role-Based Access Control)**:
  * **Admin**: Full access.
  * **Manager**: Operations & Reports.
  * **Staff**: POS & VoiceAudit only.
* **Subscription Tiers**:
  * **Starter**: Core features (Free).
  * **Business**: + FreshFlow, VendorTrust (₹999/mo).
  * **Enterprise**: + AI Forecasting & Blue Ocean Modules (₹2999/mo).

## 🧪 Simulation Data (Enterprise Demo)

VyaparMind comes with a robust **Enterprise Simulator** script.

* **`seed_enterprise.py`**: Injects **6 Months** of realistic data:
  * **15,000+ Transactions** with seasonality.
  * **1,000 Customers** across Hyderabad, Warangal, Karimnagar.
  * **Realistic Chaos**: Expiring batches, late suppliers, and staffing rosters.

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

2. **Populate Data (Optional)**

    This will inject 6 months of demo data.

    ```bash
    python seed_enterprise.py
    ```

3. **Run Application**

    ```bash
    streamlit run app.py
    ```

4. **Login Credentials**
    * **Admin**: `admin` / `admin` (Role: Admin)
    * **Staff**: `sita` / [password from DB or create new]

---

*Built for the Future of Retail.*
