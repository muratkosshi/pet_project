from sqladmin import Admin
from fastapi import FastAPI, Depends

from app.common.middlewares.logging_middleware import LoggingMiddleware
from app.core.auth.auth import AdminAuthBackend, SECRET_KEY
from app.dependencies.db.database import engine, get_async_session
from fastapi import Request
from starlette.responses import Response

from app.models.admin.models.app_settings_admin import AppSettingsAdmin
from app.models.admin.models.external_user_admin import ExternalUserAdmin
from app.models.admin.models.file_model_admin import FileModelAdmin
from app.models.admin.models.internal_user_admin import InternalUserAdmin
from app.models.admin.models.log_admin import LogAdmin
from app.models.admin.models.presentation_file_admin import PresentationFileAdmin
from app.models.admin.models.role_admin import RoleAdmin


class CustomAdmin(Admin):
    def __init__(self, app, engine, authentication_backend=None):
        super().__init__(app, engine, authentication_backend=authentication_backend)
    async def login(self, request: Request) -> Response:
        assert self.authentication_backend is not None

        context = {}
        if request.method == "GET":
            return await self.templates.TemplateResponse(request, "sqladmin/login.html")

        ok = await self.authentication_backend.login(request)
        if not ok:
            context["error"] = "Invalid credentials."
            return await self.templates.TemplateResponse(
                request, "sqladmin/login.html", context, status_code=400
            )

        return ok

    async def logout(self, request: Request) -> Response:
        assert self.authentication_backend is not None

        return await self.authentication_backend.logout(request)

def setup_admin(app: FastAPI):
    """Функция для настройки админки."""

    admin = CustomAdmin(app, engine, authentication_backend=AdminAuthBackend(SECRET_KEY))
    admin.title = 'Ai-Pitchmaker'
    admin.add_view(InternalUserAdmin)
    admin.add_view(ExternalUserAdmin)
    admin.add_view(AppSettingsAdmin)
    admin.add_view(RoleAdmin)
    admin.add_view(LogAdmin)
    admin.add_view(PresentationFileAdmin)
    admin.add_view(FileModelAdmin)
