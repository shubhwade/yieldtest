# Contributing to YieldLens

First off, thank you for considering contributing to YieldLens! We build this platform to offer professional Bloomberg-grade bond intelligence to retail investors for free.

By contributing, you help make institutional fixed-income tools accessible to all.

---

## 🛠️ Local Development Setup

YieldLens runs a Next.js (TypeScript) client application alongside a Flask (Python) REST backend.

### 1. Prerequisites
- **Python 3.10+** (with virtualenv tool)
- **Node.js 18+**
- **MongoDB Community Server** (running locally on port 27017)
- **Redis Cache Server** (running locally on port 6379)

### 2. Startup Utility
Instead of booting services in separate terminals, simply use our automated orchestration tool:
```bash
python run.py
```
This automatically configures missing virtualenvs, runs `npm install`, runs system connection tests, starts backend and frontend servers, and opens the app in your default browser.

---

## 🧪 Testing and Validation

All quantitative financial calculations and API integrations must pass rigorous unit tests. We maintain a relative calculation error tolerance threshold of **0.001%** compared to analytical benchmarks.

Before submitting a pull request, verify that all backend tests pass:
```bash
# Run backend test suite
cd backend
.venv\Scripts\pytest ..\tests\
```

---

## 📜 Development Guidelines

- **Clean Coding**: Follow PEP 8 style guidelines for Python and ESLint/Prettier defaults for TypeScript.
- **Defensive API Fallbacks**: Ensure that any new API services are fully wrapped in try-except/failover layers. If external keys are missing, the system must degrade gracefully to rule-based fallback generators without crashing or showing blank layouts.
- **Maintain Dark Theme aesthetics**: Keep the high-end Bloomberg-style dark layouts (`#000000` base, `#FF9900` orange accents).

---

## 🔀 Branching and PRs

1. Fork the repository and create a feature branch: `git checkout -b feature/your-awesome-feature`.
2. Commit your changes with professional, descriptive messages.
3. Make sure all automated tests pass.
4. Push to your branch and open a Pull Request against `main`.
