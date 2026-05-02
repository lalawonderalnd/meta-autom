"""Initial schema - all tables

Revision ID: 4b9feb8e_dea
Revises: 
Create Date: 2026-05-02T18:07:48.859238

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4b9feb8e_dea'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums first
    sa.Enum('ONLINE', 'OFFLINE', 'BUSY', 'MAINTENANCE', name='devicestatus').create(op.get_bind())
    sa.Enum('NEW', 'WARMING', 'ACTIVE', 'IDLE', 'COOLDOWN', 'NEEDS_ATTENTION', 'BANNED', name='accountstatus').create(op.get_bind())
    sa.Enum('INSTAGRAM', 'TIKTOK', 'FACEBOOK', name='platform').create(op.get_bind())
    sa.Enum('WARMUP', 'ENGAGEMENT', 'FOLLOW_UNFOLLOW', 'CONTENT_POST', 'STORY_VIEW', 'HEALTH_CHECK', name='jobkind').create(op.get_bind())
    sa.Enum('QUEUED', 'RUNNING', 'SUCCESS', 'FAILED', 'CANCELLED', name='jobstatus').create(op.get_bind())
    
    # Clients table
    op.create_table('clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('link_in_bio', sa.String(length=500), nullable=True),
        sa.Column('niche', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_clients_slug'), 'clients', ['slug'], unique=True)
    
    # Proxies table
    op.create_table('proxies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('protocol', sa.String(length=10), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('password_encrypted', sa.Text(), nullable=True),
        sa.Column('country_code', sa.String(length=2), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('carrier', sa.String(length=100), nullable=True),
        sa.Column('sticky_session_id', sa.String(length=255), nullable=True),
        sa.Column('last_ip', sa.String(length=45), nullable=True),
        sa.Column('last_ip_check_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_alive', sa.Boolean(), nullable=False),
        sa.Column('bandwidth_used_mb', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Devices table
    op.create_table('devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('serial', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('adb_port', sa.Integer(), nullable=False),
        sa.Column('android_version', sa.String(length=20), nullable=True),
        sa.Column('manufacturer', sa.String(length=100), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('ONLINE', 'OFFLINE', 'BUSY', 'MAINTENANCE', name='devicestatus'), nullable=False),
        sa.Column('max_clones', sa.Integer(), nullable=False),
        sa.Column('current_clone_count', sa.Integer(), nullable=False),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('serial')
    )
    op.create_index(op.f('ix_devices_serial'), 'devices', ['serial'], unique=True)
    
    # Accounts table (depends on devices and clients)
    op.create_table('accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.Enum('INSTAGRAM', 'TIKTOK', 'FACEBOOK', name='platform'), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_encrypted', sa.Text(), nullable=False),
        sa.Column('package_name', sa.String(length=255), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('NEW', 'WARMING', 'ACTIVE', 'IDLE', 'COOLDOWN', 'NEEDS_ATTENTION', 'BANNED', name='accountstatus'), nullable=False),
        sa.Column('warmup_day', sa.Integer(), nullable=False),
        sa.Column('posts_count', sa.Integer(), nullable=False),
        sa.Column('followers_count', sa.Integer(), nullable=False),
        sa.Column('following_count', sa.Integer(), nullable=False),
        sa.Column('proxy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('identity', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('profile_picture_url', sa.String(length=500), nullable=True),
        sa.Column('last_session_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_health_check_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['proxy_id'], ['proxies.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('health_score >= 0.0 AND health_score <= 1.0', name='check_health_score_range')
    )
    op.create_index(op.f('ix_accounts_status'), 'accounts', ['status'], unique=False)
    op.create_index(op.f('ix_accounts_username'), 'accounts', ['username'], unique=False)
    
    # Add proxy account_id foreign key (accounts must exist first)
    op.create_foreign_key(None, 'proxies', 'accounts', ['account_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_proxies_account_id'), 'proxies', ['account_id'], unique=False)
    
    # Jobs table
    op.create_table('jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('kind', sa.Enum('WARMUP', 'ENGAGEMENT', 'FOLLOW_UNFOLLOW', 'CONTENT_POST', 'STORY_VIEW', 'HEALTH_CHECK', name='jobkind'), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('QUEUED', 'RUNNING', 'SUCCESS', 'FAILED', 'CANCELLED', name='jobstatus'), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attempt', sa.Integer(), nullable=False),
        sa.Column('max_attempts', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('celery_task_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('priority >= 1 AND priority <= 9', name='check_priority_range'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_account_id'), 'jobs', ['account_id'], unique=False)
    op.create_index(op.f('ix_jobs_celery_task_id'), 'jobs', ['celery_task_id'], unique=False)
    op.create_index(op.f('ix_jobs_device_id'), 'jobs', ['device_id'], unique=False)
    op.create_index(op.f('ix_jobs_kind'), 'jobs', ['kind'], unique=False)
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)
    
    # Sessions table
    op.create_table('sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('ig_app_version', sa.String(length=20), nullable=True),
        sa.Column('actions_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('ended_reason', sa.String(length=50), nullable=True),
        sa.Column('ended_with_warning', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_account_id'), 'sessions', ['account_id'], unique=False)
    op.create_index(op.f('ix_sessions_job_id'), 'sessions', ['job_id'], unique=False)
    
    # Actions table
    op.create_table('actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('kind', sa.String(length=50), nullable=False),
        sa.Column('target', sa.String(length=255), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_actions_kind'), 'actions', ['kind'], unique=False)
    op.create_index(op.f('ix_actions_session_id'), 'actions', ['session_id'], unique=False)
    
    # Content items table
    op.create_table('content_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('storage_url', sa.String(length=500), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('hashtag_pool', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('content_type', sa.String(length=20), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('is_posted', sa.Boolean(), nullable=False),
        sa.Column('posted_account_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_items_client_id'), 'content_items', ['client_id'], unique=False)


def downgrade() -> None:
    op.drop_table('content_items')
    op.drop_table('actions')
    op.drop_table('sessions')
    op.drop_table('jobs')
    op.drop_table('accounts')
    op.drop_table('devices')
    op.drop_table('proxies')
    op.drop_table('clients')
    
    # Drop enums
    sa.Enum(name='jobstatus').drop(op.get_bind())
    sa.Enum(name='jobkind').drop(op.get_bind())
    sa.Enum(name='platform').drop(op.get_bind())
    sa.Enum(name='accountstatus').drop(op.get_bind())
    sa.Enum(name='devicestatus').drop(op.get_bind())
