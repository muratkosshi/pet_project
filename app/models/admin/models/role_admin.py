import json
from fastapi import Request
from sqladmin import ModelView
from app.models import RoleModel  # Импорт модели ролей

class RoleAdmin(ModelView, model=RoleModel):
    name = "Роли"
    name_plural = "Роли"
    column_list = ["id", "name", "source_id", "permissions"]  # Поля для отображения
    column_searchable_list = ["name"]  # Поле поиска
    column_sortable_list = ["id", "source_id"]  # Поля для сортировки
    icon = "fa-solid fa-address-card"
    form_columns = ["id", "name", "source_id", "permissions"]  # Поля, доступные для редактирования
    column_formatters = {
        "permissions": lambda m, a: json.dumps(m.permissions, ensure_ascii=False, indent=2) if m.permissions else "{}"
    }
    def is_accessible(self, request: Request) -> bool:
        user = getattr(request.state, "user", None)  # Получаем пользователя из request.state
        return user and user.is_superuser

