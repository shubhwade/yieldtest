# YieldLens — Bloomberg Terminal for Bond Investors

> **The Bloomberg Terminal for bond investors who aren't banks.**
> Built on free public data. Production-grade fixed-income analytics, institutional backtesting, and AI credit research.

![YieldLens](https://img.shields.io/badge/YieldLens-v1.0.0-FF9900?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNGRjk5MDAiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cG9seWdvbiBwb2ludHM9IjEzIDIgMyAxNCA4IDE0IDcgMjIgMTcgMTAgMTIgMTAgMTMgMiI+PC9wb2x5Z29uPjwvc3ZnPg==)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Docker Support](https://img.shields.io/badge/Docker-Supported-blue?style=for-the-badge&logo=docker)](docker-compose.yml)

---

## ⚡ Terminal-First Experience

YieldLens features a fully automated, terminal-first startup experience. A single startup orchestrator verifies system environments, checks local dependencies, tests infrastructure connectivity, spins up all microservices, and auto-connects your browser.

```bash
# Clone the repository
git clone https://github.com/shubhwade/yieldtest.git
cd yieldlens

# Run the single startup orchestrator
python run.py

# OR run via npm wrapper
npm start
```

### Automatic System Verification Included:
- **Runtime Environment**: Validates Python, Node.js, and npm package managers.
- **Infrastructure Verification**: Health checks MongoDB connection and Redis caching server.
- **API Services Verification**: Validates optional API credentials (FRED, Gemini AI, Alpha Vantage).
- **Auto-Installation**: Detects and automatically builds missing node modules and virtualenvs.
- **Service Orchestration**: Spawns clean, non-verbose Flask (Port 5000) and Next.js (Port 3000) background daemons.
- **Auto-Connector**: Launches your default browser pointing directly to `http://localhost:3000`.

---

## 🐳 Docker Container Orchestration

YieldLens is fully containerized and configured for rapid multi-service launch. Start the entire ecosystem (Next.js client, Flask API, MongoDB, and Redis Cache) with one command:

```bash
# Start all containers in the background
docker compose up -d
```

- **Next.js Client**: `http://localhost:3000`
- **Flask REST Engine**: `http://localhost:5000`
- **MongoDB Server**: `localhost:27017`
- **Redis Cache Server**: `localhost:6379`

To stop and remove all container volumes, simply run: `docker compose down -v`

---

## 🏗️ Architecture & Documentation

YieldLens is built with a decoupled, modular architecture designed for high-performance financial analytics.

- **[Architecture Deep Dive](docs/ARCHITECTURE.md)**: Detailed breakdown of the system design and folder structure.
- **[Installation Guide](docs/INSTALL.md)**: Step-by-step setup for local development.
- **[Deployment Guide](docs/DEPLOYMENT.md)**: Production deployment instructions for Vercel, Railway, and Docker.
- **[Contributing](CONTRIBUTING.md)**: How to get involved and coding standards.

---

## 📊 Features

### 1. Advanced Bond Screener
- Screen across U.S. Treasuries, municipal bonds, agency debt, and high-quality corporate bonds.
- Filter by maturity schedules, coupon rates, yields-to-worst (YTW), modified duration, and credit ratings.
- Real-time calculations with custom mathematical validations.

### 2. Yield Analytics Engine
- **Yield-to-Maturity (YTM)**: Exact Newton-Raphson pricing model solver.
- **Option-Adjusted Spread (OAS)**: Binomial interest rate tree models for callable corporate bonds.
- **Duration & Risk**: Exact calculations of Macaulay Duration, Modified Duration, Convexity, and DV01.
- **Scenario Matrices**: Stress-test holdings under parallel rate shocks (±100 bps, ±200 bps).

### 3. Institutional Backtesting Simulation
- 14-step daily historical timeline backtest engine.
- Rebalance models (ladder, barbell, risk-parity) with customizable frequencies.
- Incorporate commissions, slippage, and capital gains tax rules.
- Performance attribution (yield return vs. price return) with rolling Sharpe and Sortino ratios.

### 4. Corporate Credit Intelligence
- Altman Z-Score solvency calculations and Piotroski F-Score financial metrics.
- Merton Distance-to-Default (DD) and physical default probability estimators.
- Generates 16-section corporate credit memos powered by resilient AI failovers.
- Interactive maturity ladders and peer comparison matrices.

---

## 📁 Directory Structure

```
yieldlens/
├── frontend/                    # Next.js 14 + TypeScript Client
│   ├── src/
│   │   ├── app/                 # App Router (Dashboard, Backtest, Screener, Credit)
│   │   └── components/          # Reusable layout and chart components
│   └── Dockerfile               # Multi-stage production build Dockerfile
│
├── backend/                     # Flask REST Engine + Quant Analytics
│   ├── app.py                   # Main Entrypoint
│   ├── analytics/               # Quant yield, portfolio, risk, backtest, and stress engines
│   ├── routes/                  # API router controllers
│   ├── services/                # External data integrations (FRED, Gemini AI, Alpha Vantage)
│   └── Dockerfile               # Lightweight python REST deployment container
│
├── run.py                       # Automated system environment orchestrator
├── docker-compose.yml           # Complete four-container environment deployment configuration
└── README.md                    # Platform documentation

## 🚀 Vercel Deployment (Frontend Only)

The frontend lives in the `frontend/` folder and is configured to deploy to Vercel. To enable automatic deployments:

1. Create a Vercel project and connect your GitHub repository.
2. Set the following Environment Variables in your Vercel project settings:
    - `BACKEND_URL` — URL of your backend API (e.g., https://api.yourdomain.com)
    - Any API keys needed by the frontend (e.g., `NEWS_API_KEY`), if used client-side.
3. Add the following secrets to your GitHub repository (for CI deploys):
    - `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`
4. Push to `main` — the `Deploy Frontend to Vercel` GitHub Action will build and deploy the frontend.

Note: For full-stack production, host the backend on a server (Railway/Render) and point `BACKEND_URL` to it. Vercel is used here for the frontend hosting only.
```

---

## 🔌 Core API Endpoints

| Category | Endpoint | Description |
|----------|-----------|-------------|
| **AI Insights** | `POST /api/v1/ai/query` | Structured chatbot queries with 3-tier fallback |
| **Credit** | `GET /api/v1/credit/issuer/<ticker>` | Structural default risk, Z-scores, Merton models |
| **Backtesting**| `POST /api/v1/backtest/run` | Executes 14-step timeline backtest simulation |
| **FRED** | `GET /api/v1/fred/yield-curve` | Active 11-point benchmark Treasury yield curves |
| **Screener** | `POST /api/v1/screener/search` | Dynamic multi-attribute corporate/muni screener |

---

## 💰 Operational Cost

| Component | Provider | Cost |
|-----------|----------|------|
| **Treasury & Macro data** | FRED API | $0 (Free) |
| **Market ETF pricing** | Alpha Vantage API | $0 (Free tier) |
| **Financial AI Copilot** | Google Gemini AI | $0 (Free tier, 15 RPM) |
| **Caching & Persistence**| Local MongoDB / Redis | $0 (Local) |
| **Total Platform Cost** | | **$0 / month** |

---

## 📜 License

MIT License. Built as an open-source, mathematically defensible alternative to professional institutional suites.
