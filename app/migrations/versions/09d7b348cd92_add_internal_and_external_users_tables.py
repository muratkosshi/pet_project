"""Add internal and external users tables

Revision ID: 09d7b348cd92
Revises: c759c0c34852
Create Date: 2025-01-09 12:49:48.168737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '09d7b348cd92'
down_revision: Union[str, None] = 'c759c0c34852'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Удаляем индексы, если они существуют
    op.execute("DROP INDEX IF EXISTS ix_user_email")


    # Обновляем столбец user_type
    op.execute(
        "ALTER TABLE external_user ALTER COLUMN user_type TYPE INTEGER USING "
        "CASE user_type WHEN 'TEACHER' THEN 1 WHEN 'STUDENT' THEN 2 END"
    )

    # Обновляем столбец source
    op.execute(
        "ALTER TABLE external_user ALTER COLUMN source TYPE INTEGER USING "
        "CASE source WHEN 'BILIMAL' THEN 1 END"
    )

    # Удаляем старые ENUM-типы
    op.execute("DROP TYPE IF EXISTS usertypeenum")
    op.execute("DROP TYPE IF EXISTS sourceenum")


def downgrade() -> None:
    # Создаем ENUM-типы заново
    usertype_enum = postgresql.ENUM('TEACHER', 'STUDENT', name='usertypeenum')
    source_enum = postgresql.ENUM('BILIMAL', name='sourceenum')
    usertype_enum.create(op.get_bind())
    source_enum.create(op.get_bind())

    # Преобразуем обратно столбцы в ENUM
    op.execute(
        "ALTER TABLE external_user ALTER COLUMN user_type TYPE usertypeenum USING "
        "CASE user_type WHEN 1 THEN 'TEACHER' WHEN 2 THEN 'STUDENT' END"
    )
    op.execute(
        "ALTER TABLE external_user ALTER COLUMN source TYPE sourceenum USING "
        "CASE source WHEN 1 THEN 'BILIMAL' END"
    )

    # Восстанавливаем таблицу user, если требуется
    op.create_table(
        'user',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('username', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('registered_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('role_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('email', sa.VARCHAR(length=320), autoincrement=False, nullable=False),
        sa.Column('hashed_password', sa.VARCHAR(length=1024), autoincrement=False, nullable=False),
        sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column('is_superuser', sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column('is_verified', sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], name='user_role_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='user_pkey')
    )
    op.create_index('ix_user_email', 'user', ['email'], unique=True)
