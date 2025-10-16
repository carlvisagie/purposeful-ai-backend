# Purposeful Live Coaching Platform - API Documentation

## Base URL
```
Development: http://localhost:5000
Production: https://zmhqivcgz979.manus.space
```

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

### Get JWT Token
**Endpoint:** `POST /api/auth/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

---

## Onboarding Endpoints

### 1. Start Onboarding
**Endpoint:** `POST /api/onboarding/start`  
**Auth:** Required

Initializes the onboarding process for an authenticated user.

**Response:**
```json
{
  "message": "Onboarding started",
  "progress": {
    "id": 1,
    "user_id": 1,
    "current_step": 2,
    "is_completed": false,
    "steps": {
      "registration": true,
      "assessment": false,
      "tier_selection": false,
      "payment": false,
      "scheduling": false,
      "confirmation": false
    }
  },
  "next_step": "assessment"
}
```

---

### 2. Complete Assessment
**Endpoint:** `POST /api/onboarding/assessment`  
**Auth:** Required

Processes the initial wellness assessment and recommends a tier.

**Request:**
```json
{
  "text": "I've been feeling stressed and anxious lately...",
  "age": 35,
  "chronic": ["anxiety", "insomnia"],
  "habits": ["smoking"],
  "client_data": {
    "sleep_hours": 5,
    "exercise_frequency": "rarely",
    "stress_level": 8
  }
}
```

**Response:**
```json
{
  "message": "Assessment completed",
  "assessment_results": {
    "crisis_level": "ELEVATED",
    "mortality_risk": "elevated",
    "red_flags": ["sleep deprivation", "high stress"],
    "recommendations": ["immediate coaching", "stress management"]
  },
  "recommended_tier": "Clarity+",
  "tier_prices": {
    "Shift Session": 35,
    "Clarity+": 75,
    "Mastery": 195
  },
  "next_step": "payment"
}
```

---

### 3. Create Payment Intent
**Endpoint:** `POST /api/onboarding/payment/create-intent`  
**Auth:** Required

Creates a Stripe payment intent for the selected tier.

**Request:**
```json
{
  "tier": "Clarity+",
  "payment_type": "subscription"
}
```

**Response:**
```json
{
  "message": "Payment intent created",
  "client_secret": "pi_xxx_secret_xxx",
  "amount": 7500,
  "tier": "Clarity+"
}
```

---

### 4. Get Scheduling Link
**Endpoint:** `GET /api/onboarding/scheduling/get-link`  
**Auth:** Required

Returns a personalized Calendly scheduling link (requires completed payment).

**Response:**
```json
{
  "message": "Scheduling link generated",
  "scheduling_url": "https://calendly.com/purposeful-live/coaching?email=user@example.com&name=John+Doe",
  "event_type": "Coaching Session - 60 min"
}
```

---

### 5. Complete Onboarding
**Endpoint:** `POST /api/onboarding/complete`  
**Auth:** Required

Marks the onboarding process as complete.

**Response:**
```json
{
  "message": "Onboarding completed",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "onboarding_completed": true
  },
  "redirect_to": "/dashboard"
}
```

---

### 6. Get Onboarding Progress
**Endpoint:** `GET /api/onboarding/progress`  
**Auth:** Required

Retrieves the current onboarding progress for the user.

**Response:**
```json
{
  "progress": {
    "id": 1,
    "user_id": 1,
    "current_step": 4,
    "is_completed": false,
    "steps": {
      "registration": true,
      "assessment": true,
      "tier_selection": true,
      "payment": true,
      "scheduling": false,
      "confirmation": false
    },
    "recommended_tier": "Clarity+",
    "started_at": "2025-01-15T10:30:00Z"
  }
}
```

---

## Webhook Endpoints

### 1. Calendly Webhook
**Endpoint:** `POST /api/webhooks/calendly`  
**Auth:** None (verified via signature)

Receives webhook events from Calendly when appointments are booked or cancelled.

**Events Handled:**
- `invitee.created` - New appointment booked
- `invitee.canceled` - Appointment cancelled

**Calendly Payload Example:**
```json
{
  "event": "invitee.created",
  "payload": {
    "event": {
      "uri": "https://api.calendly.com/scheduled_events/xxx",
      "name": "Coaching Session",
      "start_time": "2025-01-20T15:00:00Z",
      "end_time": "2025-01-20T16:00:00Z"
    },
    "invitee": {
      "email": "user@example.com",
      "name": "John Doe"
    }
  }
}
```

**Response:**
```json
{
  "status": "success"
}
```

---

### 2. Zoom Webhook
**Endpoint:** `POST /api/webhooks/zoom`  
**Auth:** None (verified via token)

Receives webhook events from Zoom for meeting lifecycle.

**Events Handled:**
- `meeting.started` - Meeting started
- `meeting.ended` - Meeting ended
- `recording.completed` - Recording available

**Zoom Payload Example:**
```json
{
  "event": "meeting.ended",
  "payload": {
    "object": {
      "id": "123456789",
      "duration": 58
    }
  }
}
```

**Response:**
```json
{
  "status": "success"
}
```

---

### 3. Stripe Webhook
**Endpoint:** `POST /api/webhooks/stripe`  
**Auth:** None (verified via signature)

Receives webhook events from Stripe for payment processing.

**Events Handled:**
- `payment_intent.succeeded` - Payment successful
- `payment_intent.payment_failed` - Payment failed
- `customer.subscription.created` - New subscription
- `customer.subscription.updated` - Subscription updated
- `customer.subscription.deleted` - Subscription cancelled
- `invoice.paid` - Invoice paid
- `invoice.payment_failed` - Invoice payment failed

**Stripe Payload Example:**
```json
{
  "id": "evt_xxx",
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_xxx",
      "amount": 7500,
      "customer": "cus_xxx",
      "status": "succeeded"
    }
  }
}
```

**Response:**
```json
{
  "status": "success"
}
```

---

## Dashboard Endpoints

### 1. Get User Appointments
**Endpoint:** `GET /api/dashboard/appointments`  
**Auth:** Required

Returns all appointments for the authenticated user.

**Response:**
```json
{
  "appointments": [
    {
      "id": 1,
      "scheduled_time": "2025-01-20T15:00:00Z",
      "duration_minutes": 60,
      "status": "scheduled",
      "zoom_join_url": "https://zoom.us/j/123456789",
      "coach_id": 2
    }
  ]
}
```

---

### 2. Get Appointment Details
**Endpoint:** `GET /api/dashboard/appointments/<appointment_id>`  
**Auth:** Required

Returns detailed information about a specific appointment.

**Response:**
```json
{
  "appointment": {
    "id": 1,
    "scheduled_time": "2025-01-20T15:00:00Z",
    "duration_minutes": 60,
    "status": "completed",
    "zoom_join_url": "https://zoom.us/j/123456789",
    "recording_url": "https://zoom.us/rec/share/xxx",
    "ai_summary": "Session focused on stress management...",
    "action_items": "1. Practice daily meditation\n2. Exercise 3x per week",
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

---

### 3. Get User Notifications
**Endpoint:** `GET /api/dashboard/notifications`  
**Auth:** Required

Returns notification history for the authenticated user.

**Response:**
```json
{
  "notifications": [
    {
      "id": 1,
      "type": "whatsapp",
      "category": "appointment",
      "subject": "Appointment Confirmation",
      "status": "delivered",
      "sent_at": "2025-01-15T10:35:00Z"
    }
  ]
}
```

---

## Service Integration Details

### Calendly Service

**Purpose:** Appointment scheduling

**Key Methods:**
- `get_current_user()` - Get authenticated Calendly user
- `get_user_event_types()` - List available event types
- `create_scheduling_link()` - Generate personalized booking link
- `get_scheduled_events()` - List scheduled events
- `cancel_event()` - Cancel an event
- `handle_webhook()` - Process webhook events

---

### Zoom Service

**Purpose:** Video meeting management

**Key Methods:**
- `create_meeting()` - Create a new Zoom meeting
- `get_meeting()` - Get meeting details
- `update_meeting()` - Update meeting settings
- `delete_meeting()` - Cancel a meeting
- `get_recording()` - Retrieve meeting recording
- `handle_webhook()` - Process webhook events

---

### WhatsApp Service

**Purpose:** Client communication via WhatsApp Business

**Key Methods:**
- `send_message()` - Send plain text message
- `send_appointment_confirmation()` - Send appointment confirmation
- `send_reminder()` - Send appointment reminder
- `send_post_session_followup()` - Send post-session follow-up
- `send_crisis_alert()` - Send crisis support message
- `send_payment_confirmation()` - Send payment confirmation
- `send_welcome_message()` - Send welcome message to new clients
- `handle_incoming_message()` - Process incoming messages

---

### Payment Service (Stripe)

**Purpose:** Payment processing and subscription management

**Key Methods:**
- `create_customer()` - Create Stripe customer
- `create_payment_intent()` - Create one-time payment
- `create_subscription()` - Create recurring subscription
- `cancel_subscription()` - Cancel subscription
- `update_subscription()` - Change subscription tier
- `create_customer_portal_session()` - Generate customer portal link
- `handle_webhook_event()` - Process webhook events

---

### Google Workspace Service

**Purpose:** Calendar and email integration

**Key Methods:**
- `create_calendar_event()` - Create calendar event
- `update_calendar_event()` - Update event
- `delete_calendar_event()` - Delete event
- `send_email()` - Send email via Gmail API
- `send_appointment_confirmation_email()` - Send confirmation email
- `send_session_summary_email()` - Send post-session summary

---

## Error Responses

All endpoints return standard error responses:

**400 Bad Request:**
```json
{
  "error": "Invalid tier"
}
```

**401 Unauthorized:**
```json
{
  "msg": "Missing Authorization Header"
}
```

**403 Forbidden:**
```json
{
  "error": "Payment required before scheduling"
}
```

**404 Not Found:**
```json
{
  "error": "User not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Failed to create payment intent"
}
```

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- Authentication endpoints: 5 requests per minute
- General endpoints: 100 requests per hour
- Webhook endpoints: No limit (verified via signature)

---

## Testing

### Test Credentials (Development)

**Test User:**
```
Email: test@purposefullivecoaching.academy
Password: TestPassword123!
```

**Stripe Test Cards:**
```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
3D Secure: 4000 0027 6000 3184
```

### Webhook Testing

Use ngrok or similar tool to expose local server:
```bash
ngrok http 5000
```

Configure webhook URLs in respective services:
- Calendly: `https://your-ngrok-url.ngrok.io/api/webhooks/calendly`
- Zoom: `https://your-ngrok-url.ngrok.io/api/webhooks/zoom`
- Stripe: `https://your-ngrok-url.ngrok.io/api/webhooks/stripe`

---

## Production Deployment

### Environment Variables Required

See `.env.example` for complete list. Critical variables:
- `STRIPE_SECRET_KEY` - Stripe API key
- `CALENDLY_API_KEY` - Calendly API key
- `ZOOM_API_KEY` & `ZOOM_API_SECRET` - Zoom credentials
- `TWILIO_ACCOUNT_SID` & `TWILIO_AUTH_TOKEN` - Twilio credentials
- `OPENAI_API_KEY` - OpenAI API key

### Database Migration

Run migration before first deployment:
```bash
python backend/migrations/create_onboarding_tables.py
```

### Webhook Configuration

Configure webhook URLs in production:
- Calendly: Dashboard → Webhooks → Add webhook
- Zoom: Marketplace → Build App → Feature → Event Subscriptions
- Stripe: Dashboard → Developers → Webhooks → Add endpoint

---

## Support

For technical support or questions:
- Email: support@purposefullivecoaching.academy
- Documentation: https://docs.purposefullivecoaching.academy
- GitHub: https://github.com/carlvisagie/purposeful-ai-backend

