"""add roles to role table

Revision ID: e9dc54464029
Revises: df17568e5539
Create Date: 2025-01-30 12:03:52.652475

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import json

# revision identifiers, used by Alembic.
revision: str = 'e9dc54464029'
down_revision: Union[str, None] = 'df17568e5539'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ID, имена ролей и source_id
ROLES = [
    (48, "mapadmin", 1),
    (50, "simple_user", 1),
    (41, "statistic", 1),
    (35, "newsmaker", 1),
    (36, "newstranslater", 1),
    (38, "newsadmin", 1),
    (49, "superadmin_wocp", 1),
    (40, "admin", 1),
    (4, "teacher", 1),
    (44, "blogger", 1),
    (42, "tehspec", 1),
    (46, "likeadmin", 1),
    (2, "parent", 1),
    (45, "voter", 1),
    (-1, "guest", 1),
    (1, "superadmin", 1),
    (52, "school_administrator", 1),
    (43, "headblogs", 1),
    (3, "pupil", 1),
    (51, "mendeleev_translate", 1),
    (6, "librarian", 1),
    (8, "librarian_admin", 1),
    (53, "ddirector", 1),
    (99, "api_admin_journal", 1),
    (54, "page_editor", 1),
    (7, "director", 1),
]

# Настройки доступа
ACCESS_ROLES = {
    4: {"can_login": True, "permissions": ["create_presentation", "edit_presentation", "delete_presentation"]},
    7: {"can_login": True, "permissions": ["create_presentation", "edit_presentation", "delete_presentation"]}
}

# Остальные роли получают запрет на вход
DEFAULT_PERMISSIONS = {"can_login": False, "permissions": []}

TABLE_NAME = "role"

def upgrade():
    """Добавление ролей в таблицу role."""
    conn = op.get_bind()

    # Проверяем существующие роли
    existing_roles = conn.execute(sa.text(f"SELECT id FROM {TABLE_NAME}")).fetchall()
    existing_role_ids = {row[0] for row in existing_roles}

    # Добавляем роли с настройками доступа
    for role_id, role_name, source_id in ROLES:
        if role_id not in existing_role_ids:
            permissions = json.dumps(ACCESS_ROLES.get(role_id, DEFAULT_PERMISSIONS))
            conn.execute(
                sa.text(f"""
                    INSERT INTO {TABLE_NAME} (id, name, source_id, permissions) 
                    VALUES (:id, :name, :source_id, :permissions)
                """),
                {"id": role_id, "name": role_name, "source_id": source_id, "permissions": permissions}
            )

def downgrade():
    """Удаление ролей при откате миграции."""
    conn = op.get_bind()
    for role_id, _, _ in ROLES:
        conn.execute(sa.text(f"DELETE FROM {TABLE_NAME} WHERE id = :id"), {"id": role_id})
