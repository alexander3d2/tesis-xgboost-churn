"""create score_riesgo table

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-09-28 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "score_riesgo",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("affiliate_id", sa.Integer(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("scored_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_score_riesgo_affiliate_id", "score_riesgo", ["affiliate_id"])


def downgrade() -> None:
    op.drop_index("ix_score_riesgo_affiliate_id", table_name="score_riesgo")
    op.drop_table("score_riesgo")
