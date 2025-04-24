from passlib.context import CryptContext
from password_strength import PasswordPolicy
from sqladmin import ModelView
from wtforms import ValidationError
from wtforms.fields import PasswordField

from app.core.auth.security import pwd_context
from app.models.internal_user_model import InternalUserModel
from fastapi import Request
# Настраиваем политику проверки надежности пароля
policy = PasswordPolicy.from_names(
    length=8,  # Минимальная длина пароля
    uppercase=1,  # Минимум 1 заглавная буква
    numbers=1,  # Минимум 1 цифра
    special=1,  # Минимум 1 специальный символ
    nonletters=1,  # Минимум 1 не буквенный символ
)
class InternalUserAdmin(ModelView, model=InternalUserModel):
    """Админка для InternalUserModel."""
    name = "Внутренний пользователь"
    name_plural = "Внутренние пользователи"
    icon = "fa-solid fa-user"
    category = "Пользователи"
    column_list = [
        "id",
        "email",
        "username",
        "registered_at",
        "is_active",
        "is_superuser",
        "is_verified",
    ]
    # Display labels in Russian
    column_labels = InternalUserModel.__labels__
    # Fields to display in the create and edit forms
    form_create_rules = ["email", "username", "hashed_password", "confirm_password", "is_active", "is_superuser",
                         "is_verified"]
    form_edit_rules = ["email", "username", "hashed_password", "confirm_password", "is_active", "is_superuser",
                       "is_verified"]
    async def scaffold_form(self, rules):
        """Override the form for custom password handling."""
        form_class = await super().scaffold_form(rules)
        # Replace "hashed_password" field with a plaintext PasswordField
        if hasattr(form_class, "hashed_password"):
            original_password_field = form_class.hashed_password
            class PlainTextPasswordField(PasswordField):
                """Custom password field for displaying and handling plain-text passwords."""
                def process_data(self, value):
                    # Show an empty field instead of the hashed password
                    self.data = ""
                def process_formdata(self, valuelist):
                    """Handle form submission for password field."""
                    if valuelist:
                        self.data = valuelist[0]
            # Replace the "hashed_password" field with a new password field
            form_class.hashed_password = PlainTextPasswordField(
                label="Новый пароль",  # Rename field to "Новый пароль"
                description=original_password_field.kwargs.get("description", ""),
                render_kw=original_password_field.kwargs.get("render_kw", None),
            )
            # Add a confirm password field
            form_class.confirm_password = PasswordField(
                label="Подтверждение пароля",
                render_kw=original_password_field.kwargs.get("render_kw", None),
            )
        return form_class
    async def on_model_change(self, data, model, is_created, request) -> None:
        """Hook to modify the model before saving to the database."""
        # Check for password confirmation
        if "hashed_password" in data and "confirm_password" in data:
            if data["hashed_password"] != data["confirm_password"]:
                raise ValidationError("Пароли не совпадают.")
        # Check password strength
        if "hashed_password" in data and data["hashed_password"] and data["hashed_password"] != "******":
            # Validate password strength
            validation_errors = policy.test(data["hashed_password"])
            if validation_errors:
                error_messages = [
                    "Пароль должен быть длиной не менее 8 символов",
                    "Пароль должен содержать хотя бы одну заглавную букву",
                    "Пароль должен содержать хотя бы одну цифру",
                    "Пароль должен содержать хотя бы один специальный символ",
                ]
                raise ValidationError(", ".join(error_messages))
        # Handle password hashing
        if is_created:
            # Hash the password before saving to the database on creation
            if "hashed_password" in data and data["hashed_password"]:
                data["hashed_password"] = pwd_context.hash(data["hashed_password"])
        else:
            # Check if the password field is empty during editing
            if "hashed_password" in data:
                if not data["hashed_password"]:  # If empty, retain the current password
                    data["hashed_password"] = model.hashed_password
                elif data["hashed_password"] != "******":  # Hash only if password is updated
                    data["hashed_password"] = pwd_context.hash(data["hashed_password"])
        # Remove confirm_password from data as it is not part of the database model
        if "confirm_password" in data:
            del data["confirm_password"]
    def is_accessible(self, request: Request) -> bool:
        user = getattr(request.state, "user", None)  # Получаем пользователя из request.state
        return user and user.is_superuser