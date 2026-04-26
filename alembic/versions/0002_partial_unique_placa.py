"""partial unique index on placa for active vehicles

Revision ID: 0002
Revises: 0001
Create Date: 2025-04-26
"""
import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_vehicles_placa", table_name="vehicles")
    op.drop_constraint("vehicles_placa_key", table_name="vehicles", type_="unique")
    op.create_index(
        "ix_vehicles_placa",
        "vehicles",
        ["placa"],
        unique=True,
        postgresql_where=sa.text("ativo = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_vehicles_placa", table_name="vehicles")
    op.create_unique_constraint("vehicles_placa_key", "vehicles", ["placa"])
    op.create_index("ix_vehicles_placa", "vehicles", ["placa"])
