"""Initial migration with pgvector support

Revision ID: 001
Revises: 
Create Date: 2025-10-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('USER', 'RECRUITER', 'ADMIN', name='userrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create resumes table
    op.create_table('resumes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('owner_id', sa.String(), nullable=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('PROCESSING', 'COMPLETED', 'FAILED', name='resumestatus'), nullable=False),
        sa.Column('visibility', sa.Enum('PRIVATE', 'TEAM', 'PUBLIC', name='resumevisibility'), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('file_hash', sa.String(), nullable=True),
        sa.Column('parsing_hash', sa.String(), nullable=True),
        sa.Column('parsed_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resumes_owner_id'), 'resumes', ['owner_id'], unique=False)
    op.create_index(op.f('ix_resumes_uploaded_at'), 'resumes', ['uploaded_at'], unique=False)
    op.create_index(op.f('ix_resumes_file_hash'), 'resumes', ['file_hash'], unique=False)
    
    # Create resume_chunks table with vector column
    op.create_table('resume_chunks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('resume_id', sa.String(), nullable=False),
        sa.Column('page', sa.Integer(), nullable=False),
        sa.Column('start_offset', sa.Integer(), nullable=False),
        sa.Column('end_offset', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_chunks_resume_id'), 'resume_chunks', ['resume_id'], unique=False)
    
    # Create jobs table
    op.create_table('jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('owner_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('parsed_requirements', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_owner_id'), 'jobs', ['owner_id'], unique=False)
    
    # Create idempotency_keys table
    op.create_table('idempotency_keys',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('request_hash', sa.String(), nullable=False),
        sa.Column('response_json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )
    op.create_index(op.f('ix_idempotency_keys_user_id'), 'idempotency_keys', ['user_id'], unique=False)
    op.create_index(op.f('ix_idempotency_keys_expires_at'), 'idempotency_keys', ['expires_at'], unique=False)
    
    # Create ask_cache table
    op.create_table('ask_cache',
        sa.Column('query_hash', sa.String(), nullable=False),
        sa.Column('response_json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('query_hash')
    )
    op.create_index(op.f('ix_ask_cache_expires_at'), 'ask_cache', ['expires_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ask_cache_expires_at'), table_name='ask_cache')
    op.drop_table('ask_cache')
    op.drop_index(op.f('ix_idempotency_keys_expires_at'), table_name='idempotency_keys')
    op.drop_index(op.f('ix_idempotency_keys_user_id'), table_name='idempotency_keys')
    op.drop_table('idempotency_keys')
    op.drop_index(op.f('ix_jobs_owner_id'), table_name='jobs')
    op.drop_table('jobs')
    op.drop_index(op.f('ix_resume_chunks_resume_id'), table_name='resume_chunks')
    op.drop_table('resume_chunks')
    op.drop_index(op.f('ix_resumes_file_hash'), table_name='resumes')
    op.drop_index(op.f('ix_resumes_uploaded_at'), table_name='resumes')
    op.drop_index(op.f('ix_resumes_owner_id'), table_name='resumes')
    op.drop_table('resumes')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS resumevisibility')
    op.execute('DROP TYPE IF EXISTS resumestatus')
    op.execute('DROP TYPE IF EXISTS userrole')
