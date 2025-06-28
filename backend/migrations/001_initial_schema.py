"""Initial database schema migration

Revision ID: 001
Revises: 
Create Date: 2025-06-28 14:58:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('email', sa.String(120), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('CLIENT', 'COACH', 'ADMIN', name='userrole'), nullable=False),
        sa.Column('first_name', sa.String(50), nullable=False),
        sa.Column('last_name', sa.String(50), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table('clients',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('emergency_contact_name', sa.String(100), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(20), nullable=True),
        sa.Column('emergency_contact_relationship', sa.String(50), nullable=True),
        sa.Column('medical_conditions', sa.Text(), nullable=True),
        sa.Column('medications', sa.Text(), nullable=True),
        sa.Column('allergies', sa.Text(), nullable=True),
        sa.Column('subscription_tier', sa.Enum('SHIFT_SESSION', 'CLARITY_PLUS', 'MASTERY', name='subscriptiontier'), nullable=True),
        sa.Column('stripe_customer_id', sa.String(100), nullable=True),
        sa.Column('assigned_coach_id', sa.String(36), nullable=True),
        sa.Column('risk_level', sa.Integer(), nullable=True, default=1),
        sa.ForeignKeyConstraint(['assigned_coach_id'], ['coaches.id'], ),
        sa.ForeignKeyConstraint(['id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('coaches',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('license_number', sa.String(50), nullable=True),
        sa.Column('specializations', sa.Text(), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('availability', sa.Text(), nullable=True),
        sa.Column('max_clients', sa.Integer(), nullable=True, default=20),
        sa.ForeignKeyConstraint(['id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('sessions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('client_id', sa.String(36), nullable=False),
        sa.Column('coach_id', sa.String(36), nullable=True),
        sa.Column('session_type', sa.String(50), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('client_feedback', sa.Text(), nullable=True),
        sa.Column('coach_feedback', sa.Text(), nullable=True),
        sa.Column('diagnostic_flags', sa.JSON(), nullable=True),
        sa.Column('risk_level', sa.Integer(), nullable=True, default=1),
        sa.Column('session_rating', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['coach_id'], ['coaches.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('payments',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('stripe_payment_intent_id', sa.String(100), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(100), nullable=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED', name='paymentstatus'), nullable=False),
        sa.Column('subscription_tier', sa.Enum('SHIFT_SESSION', 'CLARITY_PLUS', 'MASTERY', name='subscriptiontier'), nullable=True),
        sa.Column('billing_period_start', sa.DateTime(), nullable=True),
        sa.Column('billing_period_end', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('crisis_alerts',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('client_id', sa.String(36), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=True),
        sa.Column('severity', sa.Enum('LOW', 'MODERATE', 'HIGH', 'CRITICAL', 'EMERGENCY', name='crisisseverity'), nullable=False),
        sa.Column('trigger_flags', sa.JSON(), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('escalated_to', sa.String(100), nullable=True),
        sa.Column('escalation_method', sa.String(50), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(36), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('audit_logs',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(36), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('audit_logs')
    op.drop_table('crisis_alerts')
    op.drop_table('payments')
    op.drop_table('sessions')
    op.drop_table('coaches')
    op.drop_table('clients')
    op.drop_table('users')
    
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS subscriptiontier')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS crisisseverity')
