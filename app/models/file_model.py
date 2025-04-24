from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.models import Base


class FileModel(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Отношение к PresentationFile
    presentations = relationship("PresentationFile", back_populates="file", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<File(id={self.id}, path='{self.path}', is_deleted={self.is_deleted})>"
