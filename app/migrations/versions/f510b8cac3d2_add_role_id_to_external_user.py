"""Add role_id to external_user

Revision ID: f510b8cac3d2
Revises: 2bb21ca0a10e
Create Date: 2025-01-30 11:45:13.883908

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f510b8cac3d2'
down_revision: Union[str, None] = '2bb21ca0a10e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('external_user', sa.Column('role_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'external_user', 'role', ['role_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'external_user', type_='foreignkey')
    op.drop_column('external_user', 'role_id')
    # ### end Alembic commands ###
