from datetime import datetime

from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean

from app.models import Base


class InternalUserModel(Base):
    __tablename__ = 'internal_user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False)
    username = Column(String, nullable=False)
    registered_at = Column(TIMESTAMP, default=datetime.utcnow)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    __labels__ = {
        "id": "ID",
        "email": "Электронная почта",
        "username": "Имя пользователя",
        "registered_at": "Дата регистрации",
        "hashed_password": "Пароль",
        "is_active": "Активен",
        "is_superuser": "Суперпользователь",
        "is_verified": "Подтвержден",
    }
