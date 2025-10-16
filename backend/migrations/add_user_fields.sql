-- Migration: Add onboarding and communication fields to users table
-- Run this SQL script against your database after creating the new tables

-- Add onboarding fields
ALTER TABLE users ADD COLUMN IF NOT EXISTS calendly_user_uri VARCHAR(200);
ALTER TABLE users ADD COLUMN IF NOT EXISTS whatsapp_number VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS whatsapp_opt_in BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_calendar_id VARCHAR(200);
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_communication VARCHAR(20) DEFAULT 'email';
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMP;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_whatsapp_number ON users(whatsapp_number);
CREATE INDEX IF NOT EXISTS idx_users_calendly_uri ON users(calendly_user_uri);
CREATE INDEX IF NOT EXISTS idx_users_onboarding_completed ON users(onboarding_completed);

-- Verify changes
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'users'
AND column_name IN (
    'calendly_user_uri',
    'whatsapp_number',
    'whatsapp_opt_in',
    'google_calendar_id',
    'preferred_communication',
    'onboarding_completed',
    'onboarding_completed_at'
)
ORDER BY column_name;

