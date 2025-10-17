# Purposeful Live Coaching - Backend Deployment Guide

Complete guide for deploying the Purposeful Live Coaching backend to production.

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/carlvisagie/purposeful-ai-backend.git
cd purposeful-ai-backend

# Run setup script
./setup_environment.sh

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run migrations
python backend/migrations/create_onboarding_tables.py

# Start server
python backend/app.py
```

## 📋 Prerequisites

### Required Accounts
- **Stripe** - Payment processing
- **Calendly** - Appointment scheduling
- **Zoom** - Video conferencing
- **Twilio** - WhatsApp notifications
- **OpenAI** - AI-powered assessments
- **Hosting** - Render, Railway, or VPS

### Required Tools
- Python 3.11+
- PostgreSQL 13+
- Git

## 🔧 Environment Configuration

### Core Settings
```bash
SECRET_KEY=<generate-64-char-random-string>
JWT_SECRET_KEY=<generate-64-char-random-string>
DATABASE_URL=postgresql://user:pass@host:5432/dbname
FLASK_ENV=production
```

### API Keys
```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_SHIFT_SESSION=price_...
STRIPE_PRICE_ID_CLARITY_PLUS=price_...
STRIPE_PRICE_ID_MASTERY=price_...

# Calendly
CALENDLY_API_KEY=...
CALENDLY_WEBHOOK_SIGNING_KEY=...

# Zoom
ZOOM_API_KEY=...
ZOOM_API_SECRET=...

# Twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=+14155238886

# Frontend
FRONTEND_URL=https://your-domain.com
```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended for Development)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Using Docker (Production)
```bash
# Build image
docker build -t purposeful-backend .

# Run container
docker run -d \
  --name purposeful-backend \
  -p 5000:5000 \
  --env-file .env \
  purposeful-backend
```

## ☁️ Cloud Deployment

### Option 1: Render (Recommended)

**1. Create PostgreSQL Database**
- Go to Render dashboard
- New → PostgreSQL
- Copy Internal Database URL

**2. Create Web Service**
- New → Web Service
- Connect GitHub repository
- Configure:
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app`
- Add environment variables
- Deploy

**3. Run Migrations**
- Open Shell in Render dashboard
- Run: `python backend/migrations/create_onboarding_tables.py`

### Option 2: Railway

**1. Create Project**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize
railway init

# Add PostgreSQL
railway add postgresql

# Deploy
railway up
```

**2. Configure**
- Add environment variables in Railway dashboard
- Set custom domain
- Run migrations via Railway shell

### Option 3: VPS (Ubuntu)

**1. Server Setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3-pip postgresql nginx certbot

# Create user
sudo adduser purposeful
sudo usermod -aG sudo purposeful
```

**2. Application Setup**
```bash
# Clone repository
git clone https://github.com/carlvisagie/purposeful-ai-backend.git
cd purposeful-ai-backend

# Setup environment
./setup_environment.sh

# Configure .env
cp .env.example .env
nano .env
```

**3. Database Setup**
```bash
# Create database
sudo -u postgres psql
CREATE DATABASE purposeful;
CREATE USER purposeful WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE purposeful TO purposeful;
\q

# Run migrations
python backend/migrations/create_onboarding_tables.py
```

**4. Systemd Service**
```bash
# Create service file
sudo nano /etc/systemd/system/purposeful-backend.service
```

```ini
[Unit]
Description=Purposeful Backend
After=network.target

[Service]
User=purposeful
WorkingDirectory=/home/purposeful/purposeful-ai-backend
Environment="PATH=/home/purposeful/purposeful-ai-backend/venv/bin"
ExecStart=/home/purposeful/purposeful-ai-backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable purposeful-backend
sudo systemctl start purposeful-backend
```

**5. Nginx Configuration**
```bash
# Create nginx config
sudo nano /etc/nginx/sites-available/purposeful-backend
```

```nginx
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/purposeful-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Setup SSL
sudo certbot --nginx -d api.your-domain.com
```

## 🔗 Webhook Configuration

### Stripe Webhooks
1. Go to https://dashboard.stripe.com/webhooks
2. Add endpoint: `https://api.your-domain.com/api/webhooks/stripe`
3. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Copy signing secret to `.env`

### Calendly Webhooks
1. Go to https://calendly.com/integrations/api_webhooks
2. Create webhook: `https://api.your-domain.com/api/webhooks/calendly`
3. Select events:
   - `invitee.created`
   - `invitee.canceled`
4. Copy signing key to `.env`

### Zoom Webhooks
1. Go to https://marketplace.zoom.us
2. Create JWT app
3. Add event subscription: `https://api.your-domain.com/api/webhooks/zoom`
4. Select events:
   - `meeting.started`
   - `meeting.ended`
   - `recording.completed`

## ⏰ Cron Jobs

### Setup Automated Reminders

**On Render/Railway:**
- Create Cron Job
- Command: `python backend/cron_reminders.py`
- Schedule: `*/15 * * * *` (every 15 minutes)

**On VPS:**
```bash
crontab -e
```

Add:
```bash
*/15 * * * * cd /home/purposeful/purposeful-ai-backend && /home/purposeful/purposeful-ai-backend/venv/bin/python backend/cron_reminders.py >> /var/log/purposeful-reminders.log 2>&1
```

## 🧪 Testing

### Run Test Suite
```bash
# All tests
python test_complete_flow.py

# Integration tests
python backend/test_integrations.py

# Health check
curl http://localhost:5000/api/health
```

### Using Postman
Import `Postman_Collection.json` and test all endpoints.

## 📊 Monitoring

### Health Checks
- **Basic**: `GET /api/health`
- **Detailed**: `GET /api/status`
- **Readiness**: `GET /api/ready`
- **Liveness**: `GET /api/live`

### Logs
```bash
# Application logs
tail -f logs/app.log

# Systemd logs (VPS)
sudo journalctl -u purposeful-backend -f

# Docker logs
docker logs -f purposeful-backend
```

### Setup Monitoring
1. Create account at https://uptimerobot.com
2. Add monitor for health endpoint
3. Configure email alerts

## 🔐 Security

### SSL/TLS
- Use Let's Encrypt for free SSL certificates
- Ensure HTTPS is enforced
- Update certificates automatically

### Environment Variables
- Never commit `.env` to git
- Use secrets management in production
- Rotate keys regularly

### Database
- Use strong passwords
- Enable SSL connections
- Regular backups
- Restrict network access

## 💾 Backup

### Database Backup Script
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U purposeful purposeful > /backups/purposeful_$DATE.sql
find /backups -name "*.sql" -mtime +7 -delete
```

### Automated Backups
```bash
# Add to crontab
0 2 * * * /path/to/backup-script.sh
```

## 🔄 Updates

### Update Application
```bash
# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run migrations
python backend/migrations/create_onboarding_tables.py

# Restart service
sudo systemctl restart purposeful-backend
```

## 🐛 Troubleshooting

### Backend Not Starting
```bash
# Check logs
sudo journalctl -u purposeful-backend -n 50

# Test manually
python backend/app.py
```

### Database Connection Issues
```bash
# Test connection
psql -U purposeful -d purposeful

# Check DATABASE_URL
echo $DATABASE_URL
```

### Webhook Not Working
- Verify webhook URL is publicly accessible
- Check signing secrets are correct
- Review webhook logs in admin dashboard

## 📚 API Documentation

Full API documentation available at:
- `API_DOCUMENTATION.md` in repository
- Postman collection: `Postman_Collection.json`

## 🆘 Support

- **Documentation**: See `BACKEND_README.md`
- **Issues**: https://github.com/carlvisagie/purposeful-ai-backend/issues
- **Email**: support@purposefullivecoaching.academy

## 📝 License

Proprietary - All rights reserved

---

**Version**: 1.0.0  
**Last Updated**: January 2025  
**Status**: Production Ready

