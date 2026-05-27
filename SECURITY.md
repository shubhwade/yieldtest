# Security Policy

We take the security of YieldLens seriously. This document outlines secure deployment guidelines, coding practices, and instructions on how to report potential vulnerabilities.

---

## 🔒 Secure Deployment Guidelines

When deploying YieldLens to a public server or production-like environment, please follow these security configurations:

1. **Disable Flask Debug Mode**: 
   - Never set `FLASK_DEBUG=True` or `FLASK_DEBUG=1` in public networks. Werkzeug’s interactive debugger allows arbitrary code execution from the browser if a traceback is displayed.
   - Always run the server with a production WSGI engine (like Gunicorn, uWSGI, or Waitress) instead of `flask run` or `python app.py` directly.
   
2. **Rotate Secrets**:
   - Change `JWT_SECRET` in `.env` to a long, cryptographically secure random string. Do not use the default dev secret.
   
3. **API Key Isolation**:
   - Never hardcode API keys (FRED, Gemini, Alpha Vantage) in the repository or upload them to Git.
   - Use our provided environment variable setup (`.env`) or Docker environment injections to pass keys securely.

---

## 🛡️ Reporting a Vulnerability

If you discover a security vulnerability within YieldLens, please **do not** open a public GitHub issue. This protects our users and systems from immediate exploitation.

Instead, please report the vulnerability confidentially by contacting the maintainers directly at `security@yieldlens.app` (or contact via your organization's private channels). 

We will investigate all reports promptly and coordinate a secure release patch within 48 to 72 hours.
