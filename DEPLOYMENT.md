# Production Deployment Guide

This guide details best practices and deployment pipelines for hosting the complete **YieldLens** platform on public cloud servers (AWS, GCP, DigitalOcean, or private VPS infrastructure).

---

## 🐋 1. Rapid Cloud Deployment with Docker Compose

The fastest and most stable method for deploying YieldLens is through our structured multi-container Docker Compose configuration:

### Steps
1. **Clone and enter the repository**:
   ```bash
   git clone https://github.com/shubhwade/yieldtest.git
   cd yieldlens
   ```
2. **Configure production variables**:
   Modify `docker-compose.yml` to include your production credentials and secure values:
   - Generate a strong `JWT_SECRET`.
   - Update `FLASK_DEBUG=False`.
   - Ensure the ports (3000 and 5000) are protected or mapped correctly behind a reverse proxy.
3. **Launch the services**:
   ```bash
   docker compose up -d --build
   ```
   This will spin up Next.js frontend, Flask API, MongoDB database, and Redis cache in isolated container networks.

---

## 🖥️ 2. Manual Bare-Metal VPS Deployment

If deploying manually without containers on a Ubuntu 22.04 LTS server, follow this enterprise blueprint:

```
                  ┌───────────────────────────────┐
                  │          Nginx Proxy          │
                  │       (Port 80 / 443 SSL)     │
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
      ┌───────────────────────┐       ┌───────────────────────┐
      │     Next.js App       │       │    Flask API Server   │
      │       (PM2)           │       │    (Gunicorn WSGI)    │
      │    http://127.0.0.1:3000      │    http://127.0.0.1:5000      │
      └───────────────────────┘       └───────────────────────┘
```

### Step A: Flask API with Gunicorn and systemd
1. Install Gunicorn in the virtual environment:
   ```bash
   cd backend
   .venv/bin/pip install gunicorn
   ```
2. Define a systemd service file (`/etc/systemd/system/yieldlens-backend.service`):
   ```ini
   [Unit]
   Description=YieldLens Flask Backend Daemon
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/yieldlens/backend
   ExecStart=/home/ubuntu/yieldlens/backend/.venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. Start and enable the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start yieldlens-backend
   sudo systemctl enable yieldlens-backend
   ```

### Step B: Next.js Frontend with PM2
1. Install PM2 globally:
   ```bash
   sudo npm install -g pm2
   ```
2. Build and start Next.js application:
   ```bash
   cd ../frontend
   npm run build
   pm2 start npm --name "yieldlens-frontend" -- start
   pm2 save
   pm2 startup
   ```

### Step C: Nginx Reverse Proxy Setup
1. Install Nginx:
   ```bash
   sudo apt install -y nginx
   ```
2. Configure Nginx Server Blocks (`/etc/nginx/sites-available/yieldlens`):
   ```nginx
   server {
       listen 80;
       server_name yieldlens.yourdomain.com;

       # Frontend Routing
       location / {
           proxy_pass http://127.0.0.1:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }

       # Backend API Routing
       location /api {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
3. Enable site and restart Nginx:
   ```bash
   sudo ln -s /etc/nginx/sites-available/yieldlens /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```
4. Obtain SSL certificates via Let's Encrypt Certbot:
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d yieldlens.yourdomain.com
   ```
