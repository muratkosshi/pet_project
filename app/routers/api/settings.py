from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.db.database import get_async_session
from app.common.services.settings_service import SettingsService

router = APIRouter()


@router.get("/{key}")
async def get_setting(
        key: str,
        session: AsyncSession = Depends(get_async_session)
):
    """
    Эндпоинт для получения значения настройки по ключу.
    """
    try:
        # Получаем значение настройки с указанным ключом
        value = await SettingsService.get_or_set(
        session=session,
        key=key,
        default=10,
        value_type="int",
        description="Максимальное количество генерации слайдов"
    )
        if value is None:
            raise HTTPException(status_code=404, detail=f"Setting with key '{key}' not found.")

        return {"key": key, "value": value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving setting: {str(e)}")