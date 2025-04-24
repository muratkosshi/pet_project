# auth/context.py
from contextvars import ContextVar

from app.models import ExternalUserModel, InternalUserModel

current_internal_user: ContextVar[InternalUserModel] = ContextVar("current_internal_user_context", default=None)
current_user: ContextVar[ExternalUserModel] = ContextVar("current_user_context", default=None)
