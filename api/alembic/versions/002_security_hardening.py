"""Security hardening

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add account security fields to users table
    op.add_column('users', sa.Column('failed_login_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('last_failed_login', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_users_locked_until'), 'users', ['locked_until'], unique=False)
    
    # Create refresh_tokens table
    op.create_table('refresh_tokens',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_expires_at'), 'refresh_tokens', ['expires_at'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_revoked'), 'refresh_tokens', ['revoked'], unique=False)
    
    # Create pii_store table
    op.create_table('pii_store',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('resume_id', sa.String(), nullable=False),
        sa.Column('field_name', sa.String(), nullable=False),
        sa.Column('encrypted_value', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pii_store_resume_id'), 'pii_store', ['resume_id'], unique=False)
    
    # Create pii_access_log table
    op.create_table('pii_access_log',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('actor_user_id', sa.String(), nullable=False),
        sa.Column('resume_id', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pii_access_log_actor_user_id'), 'pii_access_log', ['actor_user_id'], unique=False)
    op.create_index(op.f('ix_pii_access_log_resume_id'), 'pii_access_log', ['resume_id'], unique=False)
    op.create_index(op.f('ix_pii_access_log_request_id'), 'pii_access_log', ['request_id'], unique=False)
    op.create_index(op.f('ix_pii_access_log_created_at'), 'pii_access_log', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop pii_access_log table
    op.drop_index(op.f('ix_pii_access_log_created_at'), table_name='pii_access_log')
    op.drop_index(op.f('ix_pii_access_log_request_id'), table_name='pii_access_log')
    op.drop_index(op.f('ix_pii_access_log_resume_id'), table_name='pii_access_log')
    op.drop_index(op.f('ix_pii_access_log_actor_user_id'), table_name='pii_access_log')
    op.drop_table('pii_access_log')
    
    # Drop pii_store table
    op.drop_index(op.f('ix_pii_store_resume_id'), table_name='pii_store')
    op.drop_table('pii_store')
    
    # Drop refresh_tokens table
    op.drop_index(op.f('ix_refresh_tokens_revoked'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_expires_at'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    
    # Remove account security fields from users table
    op.drop_index(op.f('ix_users_locked_until'), table_name='users')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'last_failed_login')
    op.drop_column('users', 'failed_login_count')
