from sqlalchemy import Column, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models import Base


class TaskStatus(Base):
    __tablename__ = "task_statuses"

    task_id = Column(String, primary_key=True, index=True)
    status = Column(Enum("PENDING", "IN_PROGRESS", "SUCCESS", "FAILURE", "CANCELLED", name="task_status"), default="PENDING")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 🔗 Связь с PresentationFile
    presentation = relationship("PresentationFile", back_populates="task_status", uselist=False)
