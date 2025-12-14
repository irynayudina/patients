"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create patients table
    op.create_table(
        'patients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('sex', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Create devices table
    op.create_table(
        'devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('serial', sa.String(100), nullable=False, unique=True),
        sa.Column('firmware', sa.String(50), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    )
    
    # Create threshold_profiles table
    op.create_table(
        'threshold_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('hr_min', sa.Float(), nullable=False),
        sa.Column('hr_max', sa.Float(), nullable=False),
        sa.Column('spo2_min', sa.Float(), nullable=False),
        sa.Column('temp_min', sa.Float(), nullable=False),
        sa.Column('temp_max', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    )


def downgrade() -> None:
    op.drop_table('threshold_profiles')
    op.drop_table('devices')
    op.drop_table('patients')

