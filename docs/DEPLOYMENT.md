# YieldLens Deployment Guide

YieldLens is designed to be deployed in a containerized environment or as separate services on platforms like Vercel and Railway/Render.

## Frontend Deployment (Vercel)

The frontend is optimized for [Vercel](https://vercel.com).

1.  **Environment Variables**:
    - `NEXT_PUBLIC_API_URL`: The URL of your deployed backend API.
    - `NEXT_PUBLIC_WS_URL`: The URL of your WebSocket server (usually the same as the backend).

2.  **Deployment Steps**:
    - Connect your GitHub repository to Vercel.
    - Set the root directory to `frontend/`.
    - Vercel will automatically detect Next.js settings.
    - Deploy.

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
