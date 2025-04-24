from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.models import Base
from app.models.enums.SourceEnum import SourceEnum

class RoleModel(Base):
    __tablename__ = 'role'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    permissions = Column(JSON, nullable=True)
    source_id = Column(Integer, nullable=False, default=SourceEnum.BILIMAL.value)  # Связь с источником

    users = relationship("ExternalUserModel", back_populates="role")
