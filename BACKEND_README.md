# Purposeful Live Coaching - Backend API

## Overview

Production-ready Flask backend for the Purposeful Live Coaching platform. Handles user authentication, onboarding, payment processing, appointment scheduling, and integrations with Calendly, Zoom, Stripe, WhatsApp, and Google Workspace.

## Architecture

```
backend/
├── app.py                      # Flask application factory
├── config.py                   # Configuration management
├── models.py                   # Core database models
├── models_extended.py          # Extended models for onboarding
├── blueprints/                 # API endpoints
│   ├── auth.py                 # Authentication endpoints
│   ├── api.py                  # Core API endpoints
│   ├── admin.py                # Admin endpoints
│   ├── admin_extended.py       # Extended admin analytics
│   ├── coach.py                # Coach endpoints
│   ├── onboarding.py           # Client onboarding flow
│   ├── webhooks.py             # External service webhooks
│   ├── dashboard.py            # Client dashboard
│   └── health.py               # Health checks
├── services/                   # External service integrations
│   ├── calendly_service.py     # Calendly API
│   ├── zoom_service.py         # Zoom API
│   ├── whatsapp_service.py     # WhatsApp/Twilio
│   ├── google_workspace_service.py  # Google Calendar/Gmail
│   ├── enhanced_payment_service.py  # Stripe payments
│   ├── notification_scheduler.py    # Automated reminders
│   └── error_monitoring.py     # Error tracking
├── migrations/                 # Database migrations
│   ├── create_onboarding_tables.py
│   └── add_user_fields.sql
├── cron_reminders.py          # Scheduled reminder job
└── test_integrations.py       # Integration tests
```

## Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (Client, Coach, Admin)
- Secure password hashing with bcrypt
- Email verification support

### Client Onboarding
- Multi-step onboarding workflow
- AI-powered wellness assessment
- Crisis detection and alerting
- Tier recommendation based on needs
- Payment processing integration
- Automated appointment scheduling

### Payment Processing
- Stripe integration for payments
- One-time and subscription payments
- Three tier system: Shift Session ($35), Clarity+ ($75), Mastery ($195)
- Webhook-driven payment status updates
- Customer portal for self-service

### Appointment Management
- Calendly integration for scheduling
- Automatic Zoom meeting creation
- Appointment reminders (24h and 1h before)
- Post-session follow-ups
- Recording storage and delivery
- Cancellation handling

### Notifications
- WhatsApp notifications via Twilio
- Email notifications via Google Workspace
- Automated reminders
- Crisis alerts
- Payment confirmations
- Welcome messages

### Admin Dashboard
- User management
- Analytics and reporting
- Crisis alert monitoring
- Webhook log viewing
- System health monitoring

### Monitoring & Health
- Health check endpoints
- Readiness and liveness probes
- Error monitoring and alerting
- Webhook event logging
- Integration status checks

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL or SQLite
- pip3

### Setup

1. **Clone repository**
```bash
git clone https://github.com/carlvisagie/purposeful-ai-backend.git
cd purposeful-ai-backend
```

2. **Install dependencies**
```bash
pip3 install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API credentials
```

4. **Run database migrations**
```bash
python3 backend/migrations/create_onboarding_tables.py
# Run the SQL in backend/migrations/add_user_fields.sql
```

5. **Start the server**
```bash
python3 backend/app.py
```

Server will start on `http://localhost:5000`

## Configuration

### Required Environment Variables

```bash
# Core
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=sqlite:///purposeful.db
OPENAI_API_KEY=your-openai-key

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_SHIFT_SESSION=price_...
STRIPE_PRICE_ID_CLARITY_PLUS=price_...
STRIPE_PRICE_ID_MASTERY=price_...

# Calendly
CALENDLY_API_KEY=your-calendly-token
CALENDLY_WEBHOOK_SIGNING_KEY=your-signing-key

# Zoom
ZOOM_API_KEY=your-zoom-api-key
ZOOM_API_SECRET=your-zoom-api-secret

# Twilio/WhatsApp
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_NUMBER=+14155238886

# Google Workspace (Optional)
GOOGLE_SERVICE_ACCOUNT_FILE=path/to/credentials.json

# Frontend
FRONTEND_URL=https://purposefullivecoaching.academy
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

### Onboarding
- `POST /api/onboarding/start` - Start onboarding
- `POST /api/onboarding/assessment` - Submit assessment
- `POST /api/onboarding/payment/create-intent` - Create payment
- `GET /api/onboarding/scheduling/get-link` - Get Calendly link
- `POST /api/onboarding/complete` - Complete onboarding
- `GET /api/onboarding/progress` - Get progress

### Dashboard
- `GET /api/dashboard/profile` - Get user profile
- `GET /api/dashboard/appointments` - List appointments
- `GET /api/dashboard/stats` - Get dashboard stats
- `PUT /api/dashboard/update-profile` - Update profile

### Webhooks
- `POST /api/webhooks/calendly` - Calendly events
- `POST /api/webhooks/zoom` - Zoom events
- `POST /api/webhooks/stripe` - Stripe events

### Health
- `GET /api/health` - Basic health check
- `GET /api/status` - Detailed system status
- `GET /api/ready` - Readiness probe
- `GET /api/live` - Liveness probe

### Admin
- `GET /api/admin/analytics/overview` - Analytics dashboard
- `GET /api/admin/users` - List users
- `GET /api/admin/appointments` - List appointments
- `GET /api/admin/crisis-alerts` - List crisis alerts
- `GET /api/admin/webhooks/logs` - Webhook logs

See `API_DOCUMENTATION.md` for complete API reference.

## Testing

### Run Integration Tests
```bash
python3 backend/test_integrations.py
```

### Use Postman Collection
Import `Postman_Collection.json` into Postman for interactive testing.

### Test Endpoints
```bash
# Health check
curl http://localhost:5000/api/health

# Status check
curl http://localhost:5000/api/status

# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","first_name":"John","last_name":"Doe"}'
```

## Deployment

### Production Checklist
1. Set all environment variables
2. Run database migrations
3. Configure webhooks in external services
4. Set up SSL/HTTPS
5. Configure domain and CORS
6. Set up automated backups
7. Configure monitoring and alerting

See `DEPLOYMENT_CHECKLIST.md` for detailed deployment guide.

### Webhook Configuration

**Stripe:**
1. Go to https://dashboard.stripe.com/webhooks
2. Add endpoint: `https://your-domain.com/api/webhooks/stripe`
3. Select events: `payment_intent.*`, `customer.subscription.*`, `invoice.*`
4. Copy signing secret to `STRIPE_WEBHOOK_SECRET`

**Calendly:**
1. Go to https://calendly.com/integrations/api_webhooks
2. Add webhook: `https://your-domain.com/api/webhooks/calendly`
3. Select events: `invitee.created`, `invitee.canceled`
4. Copy signing key to `CALENDLY_WEBHOOK_SIGNING_KEY`

**Zoom:**
1. Go to https://marketplace.zoom.us/
2. Enable Event Subscriptions
3. Add endpoint: `https://your-domain.com/api/webhooks/zoom`
4. Subscribe to: `meeting.started`, `meeting.ended`, `recording.completed`

## Automated Tasks

### Appointment Reminders
Set up cron job to run every 15 minutes:

```bash
*/15 * * * * cd /path/to/purposeful-ai-backend && /usr/bin/python3 backend/cron_reminders.py >> /var/log/purposeful-reminders.log 2>&1
```

This will:
- Send 24-hour reminders for upcoming appointments
- Send 1-hour reminders for imminent appointments
- Send post-session follow-ups for completed appointments

## Monitoring

### Health Checks
- `/api/health` - Basic health check
- `/api/status` - Detailed status with integration checks
- `/api/ready` - Kubernetes readiness probe
- `/api/live` - Kubernetes liveness probe

### Error Monitoring
Errors are logged to:
- Application logs (stdout)
- Error log file (`/var/log/purposeful-errors.log`)
- Database (webhook logs, crisis alerts)

### Metrics to Monitor
- API response times
- Error rates
- Payment success rate
- Appointment booking rate
- Webhook delivery rate
- Database connection pool
- Active subscriptions

## Security

### Best Practices Implemented
- ✅ JWT token authentication
- ✅ Password hashing with bcrypt
- ✅ Environment variables for secrets
- ✅ Webhook signature verification
- ✅ CORS configuration
- ✅ Input validation
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ XSS prevention
- ✅ Rate limiting ready

### Security Checklist
- [ ] Enable HTTPS in production
- [ ] Set strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Rotate API keys regularly
- [ ] Enable rate limiting
- [ ] Set up firewall rules
- [ ] Configure CORS properly
- [ ] Enable audit logging
- [ ] Set up intrusion detection

## Troubleshooting

### Common Issues

**Issue: Import errors**
```bash
pip3 install -r requirements.txt
```

**Issue: Database tables don't exist**
```bash
python3 backend/migrations/create_onboarding_tables.py
```

**Issue: Webhook signature verification fails**
- Check that webhook secrets are correctly set in `.env`
- Verify webhook URLs are configured in external services

**Issue: Service integration returns None**
- Check API credentials in `.env`
- Verify services are properly configured
- Check service status pages

**Issue: Appointments not creating Zoom meetings**
- Verify Zoom API credentials
- Check Zoom API rate limits
- Review webhook logs

## Development

### Adding New Endpoints
1. Create or edit blueprint in `backend/blueprints/`
2. Register blueprint in `backend/app.py`
3. Add tests to `backend/test_integrations.py`
4. Update `API_DOCUMENTATION.md`
5. Update Postman collection

### Adding New Services
1. Create service class in `backend/services/`
2. Initialize in appropriate blueprint
3. Add configuration to `.env.example`
4. Add tests
5. Document in README

### Database Migrations
1. Create migration script in `backend/migrations/`
2. Test on development database
3. Document in deployment checklist
4. Run on production with backup

## Support

### Documentation
- `API_DOCUMENTATION.md` - Complete API reference
- `DEPLOYMENT_CHECKLIST.md` - Production deployment
- `QUICK_START_FRIDAY.md` - Quick setup guide

### Resources
- GitHub: https://github.com/carlvisagie/purposeful-ai-backend
- Issues: https://github.com/carlvisagie/purposeful-ai-backend/issues

## License

Proprietary - Purposeful Live Coaching Academy

## Version

**Version:** 1.0.0  
**Last Updated:** January 2025  
**Status:** Production Ready

