# Production Deployment Guide (VPS / Bare Metal)

This directory contains the production configuration files for deploying the Bluestock MF Analytics platform to a Linux Virtual Private Server (VPS) such as AWS EC2, DigitalOcean, or Linode.

## Prerequisites
1. A Linux server (Ubuntu 22.04 LTS recommended)
2. A registered domain name (e.g. `yourdomain.com`) with two subdomains pointing to your server's IP address:
   * `dashboard.yourdomain.com` (for Streamlit)
   * `auth.yourdomain.com` (for FastAPI)

---

## 1. Initial Server Setup
Connect to your server via SSH and install the required system packages:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx certbot python3-certbot-nginx -y
```

Clone your repository and set up a Python virtual environment:
```bash
git clone https://github.com/prathmeshnanda2007-sudo/MUTUAL-FUND-ANALYSIS.git mf-analytics
cd mf-analytics
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 2. Environment Variables
Create your `.env` file in the root of the project. **Crucially, update the URLs for production:**
```env
ENVIRONMENT=production
SECRET_KEY=your_secure_random_key

DB_URI_POOLED=postgresql://...
DB_URI_NON_POOLED=postgresql://...

# Update these to match your actual domains
AUTH_BASE_URL=https://auth.yourdomain.com
STREAMLIT_URL=https://dashboard.yourdomain.com

# Important: Both domains need to be in ALLOWED_ORIGINS
ALLOWED_ORIGINS=https://dashboard.yourdomain.com,https://auth.yourdomain.com

# Add your SMTP and Google OAuth credentials here too
```

---

## 3. Configure Systemd Services

To ensure both applications start automatically if the server reboots, configure them as `systemd` services.

### A. Auth Gateway (Gunicorn + Uvicorn)
Create the service file:
```bash
sudo nano /etc/systemd/system/mf-auth.service
```
Add the following (adjust `/path/to/mf-analytics` and your username):
```ini
[Unit]
Description=Gunicorn daemon for MF Auth Gateway
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/path/to/mf-analytics
Environment="PATH=/path/to/mf-analytics/venv/bin"
ExecStart=/path/to/mf-analytics/venv/bin/gunicorn auth_gateway.main:app -c deploy/gunicorn.conf.py

[Install]
WantedBy=multi-user.target
```

### B. Streamlit Dashboard
Create the service file:
```bash
sudo nano /etc/systemd/system/mf-dashboard.service
```
Add the following:
```ini
[Unit]
Description=Streamlit daemon for MF Dashboard
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/path/to/mf-analytics
Environment="PATH=/path/to/mf-analytics/venv/bin"
ExecStart=/path/to/mf-analytics/venv/bin/streamlit run dashboard/app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true

[Install]
WantedBy=multi-user.target
```

Start and enable both services:
```bash
sudo systemctl daemon-reload
sudo systemctl start mf-auth
sudo systemctl enable mf-auth
sudo systemctl start mf-dashboard
sudo systemctl enable mf-dashboard
```

---

## 4. Configure Nginx Reverse Proxy
Copy the provided Nginx configuration file to your sites-available directory:
```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/mf-analytics
```

Edit the file to replace `example.com` with your actual domains:
```bash
sudo nano /etc/nginx/sites-available/mf-analytics
```

Enable the configuration and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/mf-analytics /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 5. Secure with SSL (HTTPS)
Streamlit requires HTTPS to work securely with WebSockets on many modern browsers, and OAuth requires HTTPS. Use Certbot to automatically configure SSL for your subdomains:
```bash
sudo certbot --nginx -d dashboard.yourdomain.com -d auth.yourdomain.com
```

Certbot will ask if you want to redirect HTTP traffic to HTTPS. Choose **Yes (Option 2)**.

**You're done! Your application is now live and running in a production-ready environment.**
