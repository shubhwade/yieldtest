# YieldLens Deployment Guide

YieldLens is designed to be deployed in a containerized environment or as separate services on platforms like Vercel and Railway/Render.

## Vercel Deployment (Full-Stack Monorepo)

The project is now optimized as a **Vercel Full-Stack Monorepo**. This means both the Next.js frontend and the Python Flask API are deployed together as a single Vercel project.

1.  **Deployment Steps**:
    - Connect your GitHub repository to Vercel.
    - Vercel will automatically detect the Next.js framework.
    - Ensure the **Root Directory** is set to the repository root (not `frontend/` or `api/`).
    - The `api/` directory will be automatically treated as Vercel Serverless Functions.

2.  **Environment Variables**:
    - `MONGODB_URI`: Your MongoDB connection string (e.g., from MongoDB Atlas).
    - `MONGODB_DB_NAME`: Your database name (default: `yieldlens`).
    - `FRED_API_KEY`: Federal Reserve Economic Data API key.
    - `GEMINI_API_KEY`: Google Gemini AI API key.
    - `JWT_SECRET`: A secure string for token signing.
    - `NEXT_PUBLIC_API_URL`: (Optional) Leave empty to use relative paths in production.


## Backend Deployment (Railway / Render / Docker)

The backend can be deployed as a Docker container or directly as a Python service.

### Option 1: Docker (Recommended)

```bash
# Build and start the entire stack
docker compose up -d --build
```

The `docker-compose.yml` orchestrates the API, MongoDB, and Redis.

### Option 2: Railway / Render

1.  **Environment Variables**:
    - `MONGODB_URI`: Your MongoDB connection string.
    - `REDIS_URL`: Your Redis connection string.
    - `FRED_API_KEY`: (Optional) For market data.
    - `GEMINI_API_KEY`: (Optional) For AI insights.
    - `JWT_SECRET`: A strong secret for authentication.

2.  **Configuration**:
    - Root directory: `backend/`.
    - Build command: `pip install -r requirements.txt`.
    - Start command: `gunicorn -k eventlet -w 1 app:app`.

## Database Deployment

- **MongoDB**: Use [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) for a managed production database.
- **Redis**: Use [Upstash](https://upstash.com) or Redis Cloud for managed caching.

## CI/CD Pipeline

The project includes GitHub Actions workflows in `.github/workflows/` for:
- Automated testing (Pytest & Jest).
- Security scanning (Gitleaks).
- Production deployment triggers.
