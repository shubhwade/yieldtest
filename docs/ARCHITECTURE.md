# YieldLens System Architecture

YieldLens is designed as a modern, modular, and scalable fixed-income intelligence platform. It follows a decoupled frontend-backend architecture with a dedicated analytics layer and multi-service orchestration.

## High-Level Design

The system consists of three primary layers:
1.  **Frontend (Presentation Layer)**: A Next.js 15 application utilizing React, TypeScript, and Tailwind CSS.
2.  **Backend (Service Layer)**: A Flask REST API that orchestrates data flow, handles authentication, and integrates with external services.
3.  **Analytics (Quant Layer)**: A dedicated Python-based engine for bond math, risk modeling, and backtesting.

## Folder Structure

```text
yieldlens/
├── frontend/             # Next.js 15 client application
│   ├── src/
│   │   ├── app/          # Next.js App Router (pages & layouts)
│   │   ├── components/   # Reusable UI components
│   │   ├── charts/       # Specialized data visualization components
│   │   ├── layouts/      # Application structural components (Shell, Sidebar)
│   │   ├── hooks/        # Custom React hooks
│   │   ├── services/     # API and external service integrations
│   │   ├── utils/        # Frontend utility functions
│   │   ├── styles/       # Global styles and Tailwind configuration
│   │   ├── assets/       # Static images, fonts, and icons
│   │   └── types/        # TypeScript type definitions
├── backend/              # Flask REST API and Analytics engine
│   ├── routes/           # API endpoint definitions (Blueprints)
│   ├── services/         # Business logic and external API wrappers
│   ├── models/           # Data models and schema definitions
│   ├── database/         # MongoDB and Redis connection/repository layer
│   ├── analytics/        # Quant engine (bond math, risk, stress testing)
│   ├── workers/          # Background tasks and telemetry refreshers
│   ├── ai/               # AI/LLM integration layer
│   ├── middleware/       # Auth and security middleware
│   ├── utils/            # Shared backend utilities and constants
│   └── config/           # Application configuration management
├── tests/                # Comprehensive test suite (Unit, Integration, E2E)
├── scripts/              # Devops, security, and maintenance scripts
└── docs/                 # Technical documentation and deployment guides
```

## Data Flow

1.  **Market Ingestion**: Backend workers fetch real-time data from FRED, Alpha Vantage, and News APIs.
2.  **Normalization & Caching**: Data is normalized by the `analytics` engine and cached in Redis for high-speed retrieval.
3.  **Client Request**: The Next.js frontend makes authenticated requests to the Flask API.
4.  **Analytics Processing**: For complex bond calculations (YTM, Duration), the API invokes the Quant Math engine.
5.  **AI Enrichment**: The `ai` service provides summaries and credit analysis using LLMs (Gemini) with structured fallbacks.

## Security

- **Authentication**: JWT-based stateless authentication with secure password hashing (bcrypt).
- **Middleware**: Role-based access control and request validation.
- **Environment**: Strict separation of secrets via `.env` management.
