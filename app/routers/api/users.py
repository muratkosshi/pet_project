from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db.database import get_async_session
from app.models.presentation_file_model import PresentationFile
from app.models.external_user_model import ExternalUserModel
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
router = APIRouter()

@router.get("/{user_id}/presentations")
async def get_user_presentations(user_id: int, session: AsyncSession = Depends(get_async_session)):
    # Явная загрузка данных пользователя вместе с презентациями и файлами
    result = await session.execute(
        select(ExternalUserModel)
        .where(ExternalUserModel.id == user_id)
        .options(joinedload(ExternalUserModel.presentations).joinedload(PresentationFile.file))
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    # Формируем список презентаций
    presentations = [
        {"theme": presentation.theme, "file_path": presentation.file.path, 'created_at': presentation.file.created_at}
        for presentation in user.presentations
        if presentation.file and not presentation.file.is_deleted
    ]
    return presentations
