"""Fix ENUM task_status, add CANCELLED

Revision ID: 5d4af66fcb67
Revises: 8d26ab3252a1
Create Date: 2025-02-19 08:38:51.869222
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '5d4af66fcb67'
down_revision = '0ea74752f28b'
branch_labels = None
depends_on = None

def upgrade():
    # ✅ Добавляем новое значение 'CANCELLED' в существующий ENUM `task_status`
    op.execute("ALTER TYPE task_status ADD VALUE 'CANCELLED';")

def downgrade():
    # ⚠️ PostgreSQL НЕ поддерживает удаление значений из ENUM напрямую.
    # Единственный способ отката — создание нового ENUM без CANCELLED и обновление таблицы.
    op.execute("ALTER TYPE task_status RENAME TO task_status_old;")
    op.execute("CREATE TYPE task_status AS ENUM ('PENDING', 'IN_PROGRESS', 'SUCCESS', 'FAILURE');")
    op.execute("ALTER TABLE task_statuses  ALTER COLUMN status TYPE task_status USING status::text::task_status;")
    op.execute("DROP TYPE task_status_old;")
