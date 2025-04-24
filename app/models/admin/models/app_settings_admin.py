from sqladmin import ModelView
from app.models.app_settings_model import AppSettings
from fastapi import Request
class AppSettingsAdmin(ModelView, model=AppSettings):
    """Админка для управления настройками."""
    name = "Настройки"
    name_plural = "Настройки"
    icon = "fa-solid fa-cogs"

    def is_accessible(self, request: Request) -> bool:
        user = getattr(request.state, "user", None)  # Получаем пользователя из request.state
        return user and user.is_superuser

    column_list = ["id", "key", "value", "description", "value_type"]
    form_columns = ["value", "description"]

    column_labels = {
        "id": "ID",
        "key": "Ключ",
        "value": "Значение",
        "description": "Описание",
        "value_type": "Тип значения",
    }

    form_widget_args = {
        "description": {"rows": 3},  # Настраиваем поле описания
    }
