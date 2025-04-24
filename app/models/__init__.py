from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

metadata = MetaData()

Base = declarative_base(metadata=metadata)

from app.models.file_model import FileModel
from app.models.external_user_model import ExternalUserModel
from app.models.internal_user_model import InternalUserModel
from app.models.role_model import RoleModel
from app.models.presentation_file_model import PresentationFile
from app.models.app_settings_model import AppSettings
from app.models.log_entry import LogEntry
from app.models.task_status import TaskStatus
