from sqladmin import ModelView
from app.models.external_user_model import ExternalUserModel
from app.models.enums.SourceEnum import SourceEnum
from app.models.enums.UserTypeEnum import UserTypeEnum
from markupsafe import Markup


class ExternalUserAdmin(ModelView, model=ExternalUserModel):
    """Админка для ExternalUserModel."""
    name = "Внешние пользователи"
    name_plural = "Внешние пользователи"
    icon = "fa-solid fa-users"
    category = "Пользователи"
    column_list = [
        ExternalUserModel.id,
        ExternalUserModel.external_id,
        ExternalUserModel.first_name,
        ExternalUserModel.last_name,
        ExternalUserModel.generation_count,
        ExternalUserModel.generation_limit,
        ExternalUserModel.registered_at,
        ExternalUserModel.last_generation_at,
        "presentation_links_and_titles"
    ]

    column_details_list = [
        "id",
        "external_id",
        "first_name",
        "last_name",
        "generation_count",
        "generation_limit",
        "registered_at",
        "reset_generation_at",
        "presentation_links_and_titles",
        "user_type",
        "source",
        "access_token",
        "password", "login"
    ]
    # Page size for admin listing
    page_size = 20
    # Добавляем пользовательский форматтер для отображения виртуальных полей
    column_formatters = {
        "presentation_links_and_titles": lambda obj, _: Markup(
            "".join(
                f'<a href="{item["url"]}" target="_blank">{item["theme"]}</a><br>'
                for item in obj.presentation_links_and_titles
            )
        ),  # Используем метод
        "user_type": lambda obj, _: UserTypeEnum.get_display_name(obj.user_type),
        "source": lambda obj, _: SourceEnum.get_display_name(obj.source),
    }
    form_excluded_columns = (
        "presentations", "external_id", "source", "access_token", "role", "reset_generation_at", "last_generation_at",
        "registered_at", "user_type", "generation_count", "password", "login")

    column_formatters_detail = {
        "presentation_links_and_titles": lambda obj, _: Markup(
            "".join(
                f'<a href="{item["url"]}" target="_blank">{item["theme"]}</a><br>'
                for item in obj.presentation_links_and_titles
            )
        ),
        "user_type": lambda obj, _: UserTypeEnum.get_display_name(obj.user_type),  # Преобразование user_type
        "source": lambda obj, _: SourceEnum.get_display_name(obj.source),  # Преобразование source
    }

    # Добавляем виртуальные поля в список отображаемых колонок
    column_list = column_list + ["user_type", "source"]
    # Russian labels for columns
    column_labels = ExternalUserModel.__labels__
