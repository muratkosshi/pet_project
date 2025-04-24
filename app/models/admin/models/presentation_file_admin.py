from uuid import uuid4

from sqladmin import ModelView

from app.models import PresentationFile


class PresentationFileAdmin(ModelView, model=PresentationFile):
    column_list = [
        "id",
        "file_id",
        "external_user_id",
        "theme",
        "created_at",
        "uuid",
        "stage_number",
        "stage_text",
        "language",
        "is_deleted",
    ]

    column_labels = {
        "file_id": "ID файла",
        "external_user_id": "ID внешнего пользователя",
        "theme": "Тема презентации",
        "created_at": "Дата создания",
        "uuid": "Уникальный UUID",
        "stage_number": "Номер этапа",
        "stage_text": "Текст этапа",
        "language": "Язык презентации",
        "is_deleted": "Удалено",
    }

    column_searchable_list = ["theme", "language"]
    column_sortable_list = ["created_at", "stage_number"]
    column_filters = ["language", "stage_number", "is_deleted"]

    form_columns = ["file_id", "external_user_id", "theme", "stage_number", "stage_text", "language", "is_deleted"]

    async def on_model_change(self, form, model, is_created):
        """Автоматически устанавливает UUID при создании"""
        if is_created and not model.uuid:
            model.uuid = str(uuid4())

