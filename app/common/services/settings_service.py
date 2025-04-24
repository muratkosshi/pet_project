from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.app_settings_model import AppSettings

class SettingsService:
    @staticmethod
    async def get_setting(session: AsyncSession, key: str, default=None):
        """Получить настройку по ключу."""
        result = await session.execute(select(AppSettings).where(AppSettings.key == key))
        setting = result.scalars().first()
        if setting:
            return setting.cast_value()
        return default

    @staticmethod
    async def set_setting(session: AsyncSession, key: str, value, value_type="str", description=None):
        """Установить или обновить настройку."""
        result = await session.execute(select(AppSettings).where(AppSettings.key == key))
        setting = result.scalars().first()

        if setting:
            setting.value = str(value)
            setting.value_type = value_type
            if description:
                setting.description = description
        else:
            setting = AppSettings(
                key=key, value=str(value), value_type=value_type, description=description
            )
            session.add(setting)

        await session.commit()

    @staticmethod
    async def get_or_set(session: AsyncSession, key: str, default=None, value_type="str", description=None):
        """
        Получить настройку по ключу или создать её, если отсутствует.

        :param session: Сессия базы данных.
        :param key: Ключ настройки.
        :param default: Значение по умолчанию.
        :param value_type: Тип значения (str, int, bool и т.д.).
        :param description: Описание настройки.
        :return: Значение настройки.
        """
        # Попытка получить существующую настройку
        result = await session.execute(select(AppSettings).where(AppSettings.key == key))
        setting = result.scalars().first()

        if setting:
            return setting.cast_value()

        # Создание настройки, если она отсутствует
        new_setting = AppSettings(
            key=key,
            value=str(default) if default is not None else "",
            value_type=value_type,
            description=description or f"Default setting for {key}",
        )
        session.add(new_setting)
        await session.commit()

        return default
