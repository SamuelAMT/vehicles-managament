"""initial

Revision ID: 0001
Revises:
Create Date: 2025-04-26
"""
import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.Enum("USER", "ADMIN", native_enum=False), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "vehicles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("placa", sa.String(10), nullable=False),
        sa.Column("marca", sa.String(100), nullable=False),
        sa.Column("modelo", sa.String(100), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("cor", sa.String(50), nullable=False),
        sa.Column("preco_usd", sa.Numeric(12, 2), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("placa"),
    )
    op.create_index("ix_vehicles_placa", "vehicles", ["placa"])
    op.create_index("ix_vehicles_marca", "vehicles", ["marca"])


def downgrade() -> None:
    op.drop_table("vehicles")
    op.drop_table("users")
