import logging
from fastapi import HTTPException
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, select
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from app.core.auth.security import pwd_context
from app.models import Base
from app.models.enums.SourceEnum import SourceEnum
from app.models.enums.UserTypeEnum import UserTypeEnum
from sqlalchemy.ext.asyncio import AsyncSession

def get_settings_service():
    from app.common.services.settings_service import SettingsService
    return SettingsService
class ExternalUserModel(Base):
    __tablename__ = 'external_user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(Integer, nullable=False)  # ID from external service
    login = Column(String, unique=True, nullable=True)  # ✅ Добавили логин
    password = Column(String, nullable=True)  # ✅ Добавили хешированный пароль
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    user_type = Column(Integer, nullable=False)
    source = Column(Integer, nullable=False, default=1)  # Default value set to 1
    generation_count = Column(Integer, default=0)
    generation_limit = Column(Integer, default=10)
    registered_at = Column(TIMESTAMP, default=datetime.utcnow)
    last_generation_at = Column(TIMESTAMP, nullable=True)
    reset_generation_at = Column(TIMESTAMP, nullable=True)
    access_token = Column(String, nullable=True)  # Access token field
    role_id = Column(Integer, ForeignKey("role.id"), nullable=True)  # ForeignKey для роли

    role = relationship("RoleModel", back_populates="users")  # Связь с RoleModel
    presentations = relationship(
        "PresentationFile", back_populates="external_user", cascade="all, delete-orphan"
    )

    __labels__ = {
        "external_id": "Внешний ID",
        "login": "Логин",
        "password": "Пароль (хешированный)",
        "first_name": "Имя",
        "last_name": "Фамилия",
        "generation_count": "Количество генераций",
        "registered_at": "Дата регистрации",
        "user_type": "Тип пользователя",
        "source": "Источник",
        "generation_limit": "Лимит генераций",
        "last_generation_at": "Дата последней генерации",
        "presentation_links_and_titles": "Презентации",
        "reset_generation_at": "Дата обновления количества генераций"
    }

    @staticmethod
    async def set_default_generation_limit(session: AsyncSession):
        """
        Получить значение лимита генераций из настроек и применить его,
        если текущий лимит для пользователя отсутствует.
        """
        serviceSettings = get_settings_service()
        default_limit = await serviceSettings.get_or_set(
            session,
            key="default_generation_limit",
            default=10,
            value_type="int",
            description="Лимит генераций по умолчанию для пользователей"
        )
        return default_limit

    @classmethod
    async def create_with_default_limit(cls, session: AsyncSession, **kwargs):
        """Создаёт пользователя с применением лимита генераций"""
        try:
            default_limit = await cls.set_default_generation_limit(session)
            kwargs.setdefault("generation_limit", default_limit)

            user = cls(**kwargs)
            session.add(user)
            await session.commit()

            query = await session.execute(select(cls).where(cls.id == user.id))
            existing_user = query.scalars().first()
            if not existing_user:
                raise ValueError("User was not found after commit")

            await session.refresh(existing_user)  # Обновляем объект

            existing_user.reset_generation_at = existing_user.registered_at + timedelta(days=30)
            await session.commit()  # Второй коммит

            return existing_user

        except Exception as e:
            await session.rollback()
            logging.error(f"Ошибка при создании пользователя: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Ошибка при создании пользователя")

    def set_password(self, password: str):
        """Устанавливает хешированный пароль"""
        self.password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Проверяет пароль"""
        return pwd_context.verify(password, self.password)

    @property
    def user_type_enum(self):
        """Преобразует числовое значение в Enum."""
        return UserTypeEnum(self.user_type)

    @property
    def source_enum(self):
        """Преобразует числовое значение в Enum."""
        return SourceEnum(self.source)

    @property
    def user_type_display(self):
        """Возвращает читаемое название типа пользователя."""
        return self.user_type_enum.display_name

    @property
    def source_display(self):
        """Возвращает читаемое название источника."""
        return self.source_enum.display_name

    @property
    def presentation_links_and_titles(self):
        """
        Возвращает ссылки и названия презентаций пользователя.
        """
        return [
            {"url": presentation.file.path, "theme": presentation.theme}
            for presentation in self.presentations
            if presentation.file and not presentation.file.is_deleted
        ]
