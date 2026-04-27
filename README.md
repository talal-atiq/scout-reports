<div align="center">
  <!-- Replace with actual logo if available -->
  <h1>⚽ StatScout</h1>
  <p><strong>Professional-Grade Football Analytics & Scouting Platform</strong></p>
  
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
  [![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
</div>

<br />

StatScout is an advanced, full-stack football (soccer) analytics platform built for modern data-driven scouting. It processes millions of raw event data points via a custom ETL pipeline, applies unsupervised machine learning algorithms to map player styles, and surfaces these insights through an interactive, visually stunning React dashboard.

## ✨ Key Features

- **📊 Comprehensive Spatial Profiles:** Generates deep statistical profiles for players based on event data, breaking down metrics into Percentiles with Bayesian Gravity adjustments for low-minute anomalies.
- **🗺️ Advanced Visualizations:** Features interactive Pizza Charts, Expected Threat (xT) Maps, Pass Networks, Shot Maps, and dynamic Scatter Plot Explorers.
- **👯‍♂️ Tactical Twins:** Uses K-Means clustering and PCA (Principal Component Analysis) to group players by stylistic fingerprints, allowing scouts to find stylistically identical replacements using Euclidean distance calculations.
- **📈 League Projection Engine:** Translates a player's underlying Z-scores into projected impact in different European leagues based on live UEFA Country Coefficients.
- **🤖 AI Scout Annotations:** Integrates with the Groq API to automatically generate professional, context-aware scouting summaries based on raw player data.
- **⚡ High-Performance ETL:** A robust data pipeline built with `pyarrow` and `pandera` to extract, validate, and load millions of raw `.parquet` event logs into MongoDB seamlessly.

---

## 📸 Screenshots

<table>
  <tr>
    <td align="center" width="50%">
      <img src="docs/screenshot_dashboard.png" alt="Main Dashboard" width="100%"/>
      <br/><sub><b>Main Dashboard</b></sub>
    </td>
    <td align="center" width="50%">
      <img src="docs/screenshot_pizza_chart.png" alt="Player Pizza Chart" width="100%"/>
      <br/><sub><b>Player Pizza Chart</b></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <img src="docs/screenshot_scatter_plot.png" alt="Scatter Plot Explorer" width="100%"/>
      <br/><sub><b>Scatter Plot Explorer</b></sub>
    </td>
    <td align="center" width="50%">
      <img src="docs/screenshot_league_projection.png" alt="League Projection Map" width="100%"/>
      <br/><sub><b>League Projection Map</b></sub>
    </td>
  </tr>
</table>

---

## 🏗️ Architecture & Tech Stack

### Backend
* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) for high-performance async REST APIs.
* **Database:** [MongoDB](https://www.mongodb.com/) (Motor AsyncIO) for flexible, document-based storage.
* **Data Science / ML:** `scikit-learn` (K-Means, PCA), `scipy` (percentile calculations), `numpy`, `pandas`.
* **ETL Pipeline:** `pyarrow` (Parquet parsing), `pandera` (schema validation).
* **AI Integration:** Groq LLM API for natural language scouting summaries.

### Frontend
* **Core:** React 18, TypeScript, Vite.
* **Styling:** CSS/Tailwind CSS with responsive, modern glassmorphism design principles.
* **Visualizations:** Recharts and custom canvas/SVG implementations for pitch maps.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB instance (local or Atlas)

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Environment variables
cp .env.example .env
```

**Configure `.env`:**
Open `.env` and configure your `MONGODB_URL` and `GROQ_API_KEY`.

**Run the API:**
```bash
python run.py
```
*The API will be available at `http://localhost:8000` (Swagger docs at `/api/docs`).*

### 2. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```
*The application will be available at `http://localhost:5173`.*

---

## 🗄️ Data Pipeline (ETL)

StatScout relies on raw event data (in `.parquet` format) to generate insights. The ETL pipeline is decoupled from the main backend to allow independent scheduling and scaling.

1. **Extract:** Reads granular event-level data (passes, shots, defensive actions) from Parquet files.
2. **Transform:** Aggregates events into per-90 metrics, builds spatial fingerprints, and calculates league-specific percentiles.
3. **Load:** Upserts validated player profiles and season distributions into MongoDB.

*Note: The raw `.parquet` files are strictly `.gitignore`'d due to size constraints. To run the pipeline locally, you must acquire the relevant data files and place them in `backend/data/`.*

---

## 📂 Project Structure

```text
scout-reports/
├── backend/
│   ├── app/                  # FastAPI application (routes, models, schemas, services)
│   ├── data/                 # Raw event data (Parquet) & ETL dropzones
│   ├── etl/                  # Data pipeline scripts & ETL requirements
│   ├── models/               # Serialized ML models (PCA, Scalers)
│   ├── spatial_aggregator.py # Core data transformation logic
│   ├── style_clusterer.py    # Unsupervised ML classification pipeline
│   └── run.py                # Uvicorn entry point
└── frontend/
    ├── public/               # Static assets
    └── src/
        ├── api/              # Axios API clients
        ├── components/       # Reusable React UI components & Visualizations
        ├── pages/            # Full-page views
        └── types/            # TypeScript interfaces
```

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'feat: Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

<div align="center">
  <sub>Built with ❤️ for the love of the beautiful game.</sub>
</div>
