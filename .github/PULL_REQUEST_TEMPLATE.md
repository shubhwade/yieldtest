## Release Prep: Vercel Frontend

Summary of changes:

- Add CI for tests and frontend build
- Add Vercel deployment workflow
- Add `.env.example` and deployment docs
- Run Python autoflake/isort/black on backend code (formatting only)

Checklist before merging:
- [ ] Confirm `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` are set in GitHub secrets
- [ ] Confirm `BACKEND_URL` is set in Vercel environment variables
- [ ] Run `npm ci` and `npm run build` locally in `frontend/`
- [ ] Run `pytest` locally in the backend (requires dependencies)
- [ ] Review `vulture-report.txt` in repository root for possible dead code

Deployment steps after merge:
1. Push to `main`.
2. GitHub Action will run CI build and deploy to Vercel (production).
3. Validate live site and API connectivity.
