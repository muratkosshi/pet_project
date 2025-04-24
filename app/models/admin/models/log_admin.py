from sqladmin import ModelView
from sqlalchemy import desc
from app.models.log_entry import LogEntry
from fastapi import Request
class LogAdmin(ModelView, model=LogEntry):
    name = "Логи"
    name_plural = "Логи"
    can_create = False  # Отключаем возможность добавления записей
    can_edit = False    # Отключаем возможность редактирования записей
    icon = "fa-solid fa-clock"
    column_list = [LogEntry.id, LogEntry.level, LogEntry.message, LogEntry.timestamp]
    column_searchable_list = ["level", "message"]

    # ✅ Разрешаем сортировку по этим полям
    column_sortable_list = [LogEntry.timestamp, LogEntry.id]

    # ✅ По умолчанию сортируем по timestamp (от новых к старым)
    column_default_sort = (LogEntry.timestamp, True)  # True == DESCENDING
    def is_accessible(self, request: Request) -> bool:
        user = getattr(request.state, "user", None)  # Получаем пользователя из request.state
        return user and user.is_superuser