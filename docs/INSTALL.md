# Installation Guide

Follow these steps to set up YieldLens for local development.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **MongoDB** (Local or Atlas)
- **Redis** (Optional but recommended for caching)

## Quick Start (Automated)

The easiest way to start is using the root orchestrator:

```bash
python run.py
```

This script will:
1.  Check for required runtimes (Python, Node).
2.  Install backend dependencies in a virtual environment.
3.  Install frontend dependencies via npm.
4.  Verify database connectivity.
5.  Start both services in parallel.

## Manual Setup

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python app.py
```

### 2. Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your backend URL
npm run dev
```

## Environment Configuration

Key environment variables in `.env`:

| Variable | Description | Default |
| --- | --- | --- |
| `MONGODB_URI` | MongoDB Connection String | `mongodb://localhost:27017/yieldlens` |
| `FRED_API_KEY` | Federal Reserve Data Key | (Get at fred.stlouisfed.org) |
| `GEMINI_API_KEY` | Google AI Key | (Get at aistudio.google.com) |
| `JWT_SECRET` | Secret for Auth Tokens | `dev-secret-change-me` |

## Troubleshooting

- **MongoDB Connection**: Ensure MongoDB is running on `localhost:27017`.
- **Node Versions**: If you face build issues, ensure you are on Node 18 or 20.
- **Python Path**: If imports fail, ensure the `backend/` directory is in your `PYTHONPATH`.
