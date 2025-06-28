# Purposeful Live AI Coaching Platform - Phase 1 Implementation

## 🎯 Phase 1 Critical Infrastructure Complete

This implementation provides the foundational infrastructure for the Purposeful Live AI coaching platform, focusing on security, scalability, and compliance.

## ✅ Implemented Features

### 1. Database Infrastructure (PostgreSQL)
- **Complete schema** with proper relationships and constraints
- **User management** with role-based access (Client, Coach, Admin)
- **Session tracking** with diagnostic flags and risk assessment
- **Payment records** with Stripe integration support
- **Crisis alerts** with escalation tracking
- **Audit logging** for compliance and security

### 2. Authentication & Authorization (JWT + RBAC)
- **Secure JWT authentication** with access/refresh token pattern
- **Role-based access control** with decorators (@admin_required, @coach_required, etc.)
- **Password security** with bcrypt hashing and validation
- **Session management** with automatic token refresh
- **User registration** with email validation

### 3. Payment Processing (Stripe Integration)
- **Subscription management** for three tiers (Shift Session, Clarity+, Mastery)
- **One-time payments** and recurring billing
- **Webhook handling** for payment status updates
- **Payment history** and invoice tracking
- **Secure customer data** handling with Stripe

### 4. Crisis Detection & Escalation
- **Advanced scoring algorithm** analyzing text input for crisis indicators
- **Severity levels** (Low, Moderate, High, Critical, Emergency)
- **Automatic escalation** to coaches and emergency contacts
- **Email notifications** for crisis alerts
- **Behavioral pattern analysis** (late-night activity, missed sessions, sentiment decline)
- **Manual resolution** tracking with notes

### 5. Coach Dashboard
- **Client management** with risk level indicators
- **Session tracking** and scheduling
- **Crisis alert monitoring** with resolution capabilities
- **Analytics overview** (client count, active sessions, risk distribution)
- **Real-time notifications** for high-priority alerts

### 6. Admin Panel
- **User management** (create, edit, activate/deactivate users)
- **Business analytics** (revenue, user growth, session statistics)
- **System monitoring** (active sessions, crisis alerts)
- **Role assignment** and permission management
- **Audit trail** viewing

### 7. React Frontend
- **Modern React 19** with Vite build system
- **Responsive design** with mobile support
- **Protected routes** with role-based access
- **Real-time updates** and state management
- **Stripe integration** for payment processing
- **Crisis analysis interface** for clients

## 🔒 Security & Compliance

### HIPAA Compliance
- **Data encryption** at rest and in transit
- **Access controls** with role-based permissions
- **Audit logging** for all sensitive operations
- **Secure session management**
- **Data retention** policies

### GDPR Compliance
- **Data export** capabilities
- **Right to deletion** implementation
- **Consent management**
- **Privacy by design** architecture

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Node.js 16+
- Stripe account (for payments)

### Backend Setup

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Initialize database:**
   ```bash
   python init_db.py
   ```

4. **Run the application:**
   ```bash
   python ai_api.py
   ```

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd "frontend-app Primary  – Modern ReactVite app (primary frontend)"
   npm install
   ```

2. **Configure environment:**
   ```bash
   # Create .env file with API base URL
   echo "VITE_API_BASE_URL=http://localhost:5000/api" > .env
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile

### Payments
- `POST /api/payments/create-payment-intent` - Create payment
- `POST /api/payments/create-subscription` - Create subscription
- `GET /api/payments/history` - Payment history
- `POST /api/payments/webhook` - Stripe webhook

### Crisis Management
- `POST /api/crisis/analyze` - Analyze text for crisis indicators
- `GET /api/crisis/alerts` - Get crisis alerts
- `POST /api/crisis/alerts/{id}/resolve` - Resolve crisis alert

### Dashboard
- `GET /api/dashboard/coach/overview` - Coach dashboard data
- `GET /api/dashboard/coach/clients` - Coach's clients
- `GET /api/dashboard/admin/overview` - Admin dashboard data
- `GET /api/dashboard/admin/users` - User management

## 🔧 Configuration

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://username:password@localhost/purposeful_live

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email (for crisis alerts)
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Crisis Management
CRISIS_ALERT_EMAIL=crisis@yourcompany.com
CRISIS_ALERT_PHONE=+1234567890

# AI
OPENAI_API_KEY=your-openai-key
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/
```

### Frontend Tests
```bash
cd "frontend-app Primary  – Modern ReactVite app (primary frontend)"
npm test
```

## 📈 Monitoring & Analytics

The platform includes comprehensive analytics:
- **User engagement** metrics
- **Revenue tracking** and forecasting
- **Crisis intervention** statistics
- **Session effectiveness** analysis
- **Coach performance** indicators

## 🔄 Next Steps (Phase 2+)

After Phase 1 stabilization, consider:
- Advanced AI features (sentiment analysis, personalized recommendations)
- Video calling integration
- Mobile applications
- Advanced analytics and reporting
- Third-party integrations (calendar, CRM)

## 🆘 Crisis Management

The platform includes robust crisis detection:
- **Keyword analysis** for suicide ideation, self-harm, substance abuse
- **Behavioral pattern** recognition
- **Automatic escalation** to qualified professionals
- **Emergency contact** notification
- **Follow-up tracking** and resolution

## 📞 Support

For technical support or questions about the implementation:
- Review the code documentation
- Check the audit logs for debugging
- Monitor the crisis alert system
- Ensure all environment variables are properly configured

---

**⚠️ Important:** This is a mental health platform. Ensure proper crisis management protocols are in place and that all staff are trained in emergency procedures.
