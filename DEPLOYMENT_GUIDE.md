# YieldLens Vercel Deployment Guide

This guide provides step-by-step instructions for deploying YieldLens to Vercel.

## Prerequisites

- GitHub account with the YieldLens repository
- Vercel account (free at https://vercel.com)
- Backend deployed (Railway, Render, or self-hosted)
- API keys for external services (FRED, Gemini, etc.)

## Part 1: Frontend Deployment (Next.js on Vercel)

### Step 1: Connect GitHub Repository to Vercel

1. Go to https://vercel.com/new
2. Select "Import Git Repository"
3. Search for your YieldLens repository
4. Click "Import"

### Step 2: Configure Project Settings

1. **Project Name:** yieldlens (or your preferred name)
2. **Framework:** Next.js (auto-detected)
3. **Root Directory:** ./ (already set correctly)

### Step 3: Set Environment Variables

In the Vercel dashboard, add these environment variables:

```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

**Important:**
- `NEXT_PUBLIC_API_URL` is the ONLY environment variable needed for the frontend
- This URL must point to your backend API
- It will be publicly exposed in the browser, so ensure proper CORS configuration

### Step 4: Deploy

1. Click "Deploy"
2. Wait for the build to complete (typically 2-3 minutes)
3. You'll receive a unique URL (e.g., `https://yieldlens-abc123.vercel.app`)

### Step 5: Custom Domain (Optional)

1. Go to Project Settings → Domains
2. Click "Add Domain"
3. Enter your custom domain (e.g., `yieldlens.com`)
4. Follow DNS configuration instructions

---

## Part 2: Backend Deployment

### Option A: Railway (Recommended)

1. Connect GitHub to Railway: https://railway.app
2. Create new project from GitHub
3. Set root directory: `./api`
4. Configure environment variables in Railway dashboard:

```
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/yieldlens
MONGODB_DB_NAME=yieldlens
FRED_API_KEY=your_key
GEMINI_API_KEY=your_key
JWT_SECRET=generate_secure_secret
FLASK_PORT=5000
REDIS_URL=redis://your-redis-url
```

5. Railway will auto-deploy on git push

### Option B: Render

1. Go to https://render.com
2. Create new Web Service
3. Connect GitHub repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python api/index.py`
6. Add environment variables in Settings
7. Deploy

### Option C: Self-Hosted (AWS, GCP, Azure, etc.)

```bash
# Clone repository
git clone https://github.com/yourusername/yieldlens.git
cd yieldlens

# Install backend dependencies
pip install -r requirements.txt

# Set environment variables
export MONGODB_URI=mongodb://...
export FRED_API_KEY=...
# ... set all required variables

# Run backend
python api/index.py
```

---

## Part 3: Verify Deployment

### Test Frontend

```bash
# Check frontend is accessible
curl https://yieldlens-abc123.vercel.app

# Should return HTML (Next.js page)
```

### Test API Connection

```bash
# Check API endpoint
curl https://api.yourdomain.com/api/health

# Should return: {"status": "healthy", "platform": "vercel-serverless"}
```

### Test Full Integration

1. Open frontend URL in browser
2. Check browser console for errors
3. Navigate to different pages
4. Verify data loads from backend

---

## Part 4: Monitoring & Maintenance

### Enable Vercel Analytics

1. Go to Project Settings → Analytics
2. Enable "Web Vitals"
3. Monitor performance metrics

### Set Up Error Tracking

Option 1: Vercel Built-in
- Errors are automatically tracked
- View in Deployments → Logs

Option 2: External Service (Sentry, LogRocket)
```
# Add Sentry to frontend
npm install @sentry/nextjs

# Configure in next.config.mjs
import * as Sentry from "@sentry/nextjs";
```

### Automatic Deployments

- Vercel automatically deploys on push to `main` branch
- Preview deployments for pull requests
- Automatic rollback available

---

## Part 5: Troubleshooting

### Issue: "Cannot connect to API"

**Solution:**
1. Check `NEXT_PUBLIC_API_URL` is set correctly
2. Verify backend is running and accessible
3. Check CORS headers in backend (already configured in `vercel.json`)
4. Look for errors in browser console (F12)

### Issue: "Build fails with TypeScript errors"

**Solution:**
```bash
# These should already be fixed, but if needed:
npm run lint
npm run build

# Push to GitHub to re-trigger Vercel build
```

### Issue: "Production build is slow"

**Solution:**
1. Check bundle size: `npm run build` output
2. Enable Vercel Analytics to identify bottlenecks
3. Consider code-splitting large routes

### Issue: "Environment variables not loaded"

**Solution:**
1. Verify variables are set in Vercel dashboard
2. Redeploy after adding variables: `vercel redeploy`
3. Check variable names don't have typos
4. Frontend vars must start with `NEXT_PUBLIC_`

---

## Rollback Plan

If deployment has issues:

### Quick Rollback in Vercel

```bash
# In Vercel dashboard:
# Deployments → Click previous successful build → More → Promote to Production
```

### Local Rollback

```bash
# Revert to previous commit
git revert HEAD

# Push to trigger new deployment
git push origin main
```

---

## Performance Optimization

### Current Metrics
- Build time: ~12 seconds
- First Load JS: 102 kB (shared) + route-specific JS
- Page sizes: 1-10 kB each

### Recommendations

1. **Images:** Compress and optimize images
2. **Code splitting:** Already done with Next.js
3. **Caching:** Configure Redis for backend
4. **CDN:** Vercel automatically uses edge network

---

## Security Checklist

- [x] HTTPS enforced (Vercel default)
- [x] Security headers configured in `vercel.json`
- [x] Environment variables not committed to git
- [x] API routes have CORS configured
- [ ] Set up DDoS protection (Vercel default for Enterprise)
- [ ] Enable authentication (to implement)
- [ ] Set rate limiting (configured in backend)

---

## Environment Variables Reference

### Frontend (Vercel)
```
NEXT_PUBLIC_API_URL    # Backend API URL (REQUIRED)
```

### Backend (Railway/Render)
```
MONGODB_URI            # MongoDB connection string (REQUIRED)
MONGODB_DB_NAME        # Database name
FRED_API_KEY           # Federal Reserve API key (optional)
GEMINI_API_KEY         # Google Gemini AI key (optional)
ALPHA_VANTAGE_API_KEY  # Stock data API key (optional)
NEWS_API_KEY           # News API key (optional)
JWT_SECRET             # Secret for JWT tokens (REQUIRED)
FLASK_PORT             # Server port (default: 5000)
REDIS_URL              # Redis cache URL (optional)
```

See `.env.example` for complete list.

---

## Post-Deployment

### Week 1: Monitoring
- Watch error logs for any issues
- Monitor API response times
- Check user feedback

### Month 1: Optimization
- Analyze analytics data
- Optimize slow pages
- Update dependencies if needed

### Ongoing
- Monthly security updates
- Quarterly dependency updates
- Annual Next.js/Node.js updates

---

## Support

For issues or questions:
1. Check Vercel logs: Dashboard → Deployments → Logs
2. Check browser console: F12 → Console
3. Review AUDIT_REPORT.md for build information
4. Check GitHub Issues

---

**Deployment Status:** Ready for Production ✅

Last updated: May 31, 2026
