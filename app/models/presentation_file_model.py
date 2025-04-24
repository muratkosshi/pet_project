from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, func, Text, Boolean
from sqlalchemy.orm import relationship
from uuid import uuid4
from app.models import Base

class PresentationFile(Base):
    __tablename__ = "presentation_files"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=True)
    external_user_id = Column(Integer, ForeignKey("external_user.id", ondelete="CASCADE"), nullable=False)
    theme = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    uuid = Column(String, default=lambda: str(uuid4()), unique=True, nullable=False)
    stage_number = Column(Integer, nullable=False, default=0)
    stage_text = Column(Text, nullable=True)
    language = Column(String, nullable=False, default="ru")
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 🔗 Связь с TaskStatus
    task_id = Column(String, ForeignKey("task_statuses.task_id", ondelete="SET NULL"), nullable=True)
    task_status = relationship("TaskStatus", back_populates="presentation")

    # Отношения
    file = relationship("FileModel", back_populates="presentations")
    external_user = relationship("ExternalUserModel", back_populates="presentations")

    __labels__ = {
        "file_id": "ID файла",
        "external_user_id": "ID внешнего пользователя",
        "theme": "Тема презентации",
        "created_at": "Дата создания",
        "uuid": "Уникальный UUID",
        "stage_number": "Номер этапа",
        "stage_text": "Текст этапа",
        "language": "Язык презентации",
        "task_id": "ID задачи",
    }
