"""add reset_generation_at

Revision ID: 1df688c3e6b1
Revises: f21bf9f0517e
Create Date: 2025-01-29 12:49:13.791031

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1df688c3e6b1'
down_revision: Union[str, None] = 'f21bf9f0517e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Добавляем колонку с временным разрешением NULL
    op.add_column('external_user', sa.Column('reset_generation_at', sa.TIMESTAMP(), nullable=True))

    # 2. Устанавливаем значение: registered_at + 30 дней
    op.execute("""
        UPDATE external_user
        SET reset_generation_at = registered_at + interval '30 days'
        WHERE reset_generation_at IS NULL;
    """)

    # 3. Делаем колонку обязательной (NOT NULL)
    op.alter_column('external_user', 'reset_generation_at', nullable=False)

def downgrade() -> None:
    op.drop_column('external_user', 'reset_generation_at')
