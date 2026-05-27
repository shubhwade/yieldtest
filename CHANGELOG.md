# Changelog

All notable changes to the **YieldLens** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-05-27

This marks the official production-ready release of YieldLens, transforming it into a mathematically rigorous, enterprise-grade fixed-income intelligence suite.

### Added
- **Production Startup Orchestrator**: Added `run.py` to provide a single-command startup experience with automatic package resolution and infrastructure connection checking.
- **Docker Compose Orchestration**: Added multi-container support (`docker-compose.yml`, custom Dockerfiles for frontend/backend) to build and deploy the entire Next.js, Flask, MongoDB, and Redis stack in one command.
- **Resilient Semantic Keyword Router**: Added an institution-grade query router in the AI local fallback engine (`ai_service.py`), yielding highly detailed, custom-structured JSON answers for standard financial queries (convexity, yield curve inversion, rate cuts, safest bonds, TIPS, and default risks).
- **Merton Distance-to-Default (DD)**: Implemented structural Merton default models estimating physical probabilities of default.
- **Altman Z-Score & Piotroski F-Score**: Solvency and credit metrics added to issuer dashboards.
- **Institutional Backtesting Simulation Engine**: Implemented a 14-step daily historical timeline backtest loop supporting ladder, barbell, and risk-parity models with transaction costs, slippage, and capital gains tax rules.
- **Option-Adjusted Spread (OAS)**: Calibrated binomial trees for callable corporate bonds.
- **Mathematical Validation Test Suite**: Implemented automatic pricing, YTM, and duration tests with strict error tolerances (< 0.001%).

### Fixed
- **Chatbot Repetitive Fallback Issue**: Fixed incorrect query propagation and static boilerplate repetitions in the rule-based local fallback mode.

---

## [0.9.0] - 2026-05-15
### Added
- Basic 11-point benchmark US Treasury yield curves loaded dynamically from FRED.
- Next.js dark-theme Bloomberg-inspired dashboard.
- Active portfolio allocation tracking and watchlists.
