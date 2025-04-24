from sqladmin import ModelView
from app.models.file_model import FileModel

class FileModelAdmin(ModelView, model=FileModel):
    """Админ-панель для управления файлами"""

    column_list = [
        "id",
        "path",
        "is_deleted",
        "created_at",
        "updated_at",
    ]

    column_labels = {
        "id": "ID",
        "path": "Путь к файлу",
        "is_deleted": "Удалено",
        "created_at": "Дата создания",
        "updated_at": "Дата обновления",
    }

    column_searchable_list = ["path"]
    column_sortable_list = ["created_at", "updated_at"]
    column_filters = ["is_deleted"]

    form_columns = ["path", "is_deleted"]

