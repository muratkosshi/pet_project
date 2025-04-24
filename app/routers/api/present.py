import os
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import FileResponse

from app.dependencies.db.database import get_async_session
from app.core.auth.auth import verify_token
from app.core.auth.auth_context import current_user
from app.engine.mdtree.utils import get_themes_with_images
from app.models import PresentationFile, ExternalUserModel

router = APIRouter()

async def check_generation_limit(session: AsyncSession = Depends(get_async_session)) -> ExternalUserModel:
    user = current_user.get()
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # Reset the generation count if more than a month has passed
    if user.last_generation_at:
        time_since_last_generation = datetime.utcnow() - user.last_generation_at
        if time_since_last_generation > timedelta(days=30):
            user.generation_count = 0  # Reset the count
            user.last_generation_at = None
            session.add(user)
            await session.commit()

    # Check if the user has reached their generation limit
    if user.generation_limit is not None and user.generation_count >= user.generation_limit:

        print(user)
        raise HTTPException(status_code=403, detail="Достигнут предел генерации")

    # Allow the request to proceed
    return user
@router.get("/themes/")
async def get_themes():
    themes = get_themes_with_images()
    if not themes:
        raise HTTPException(status_code=404, detail="No themes with images found")
    return themes

@router.get("/get_present/{name_present}")
def get_present(name_present: str):
    # Путь к директории с презентациями
    directory = "./myppt/"
    # Полный путь к файлу презентации

    file_path = os.path.join(directory, f"{name_present}.pptx")
    print("ПУТЬ:", file_path)
    # Проверяем, существует ли файл
    if os.path.isfile(file_path):
        # Отдаем файл пользователю
        return FileResponse(path=file_path,
                            media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                            filename=f"{name_present}.pptx")
    else:
        # Если файл не найден, возвращаем ошибку 404
        raise HTTPException(status_code=404, detail="Presentation not found")

@router.get("/presentations")
async def get_presentations(
    session: AsyncSession = Depends(get_async_session),
    user: ExternalUserModel = Depends(verify_token),
):
    """
    Получение списка презентаций для текущего пользователя с их статусом генерации.
    """
    query = (
        select(PresentationFile)
        .options(joinedload(PresentationFile.task_status))  # ✅ Загружаем связанные статусы
        .where(
            PresentationFile.external_user_id == user.id,
            PresentationFile.is_deleted == False
        )
    )
    result = await session.execute(query)
    presentations = result.scalars().all()

    return [
        {
            "uuid": presentation.uuid,
            "theme": presentation.theme,
            "stage_number": presentation.stage_number,
            "created_at": presentation.created_at,
            "language": presentation.language,
            "status": presentation.task_status.status if presentation.task_status else "NOT_STARTED",
            "task_id": presentation.task_id if presentation.task_status and presentation.task_status.status in ["IN_PROGRESS", "PENDING"] else None
        }
        for presentation in presentations
    ]



@router.post("/create", dependencies=[Depends(check_generation_limit)])
async def create_presentation(
    session: AsyncSession = Depends(get_async_session),
    user: ExternalUserModel = Depends(verify_token),
):
    """
    Создание новой презентации.
    """
    # Создаем новую запись для презентации
    new_presentation = PresentationFile(
        external_user_id=user.id,  # Используем ID текущего пользователя
        theme="Новая презентация",
        stage_number=0,
        language="ru",  # Язык по умолчанию
    )
    user.generation_count += 1
    user.last_generation_at = datetime.utcnow()
    session.add(new_presentation)
    await session.commit()
    await session.refresh(new_presentation)

    return {"uuid": new_presentation.uuid, "theme": new_presentation.theme}


@router.get("/presentations/{uuid}")
async def get_presentation_by_uuid(
    uuid: str,
    session: AsyncSession = Depends(get_async_session),
    user: ExternalUserModel = Depends(verify_token),
):
    """
    Получение данных презентации по UUID.
    """
    query = (
        select(PresentationFile)
        .options(
            joinedload(PresentationFile.file),       # Загрузка связанного файла
            joinedload(PresentationFile.task_status) # Загрузка статуса задачи
        )
        .where(
            PresentationFile.uuid == uuid,
            PresentationFile.external_user_id == user.id,
            PresentationFile.is_deleted == False
        )
    )
    result = await session.execute(query)
    presentation = result.scalars().first()

    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")

    # ✅ Теперь task_status загружен заранее и ошибка исчезнет
    task_status = presentation.task_status.status if presentation.task_status else None
    task_id = presentation.task_id if presentation.task_id and task_status in ["IN_PROGRESS", "PENDING"] else None

    return {
        "uuid": presentation.uuid,
        "theme": presentation.theme,
        "stage_number": presentation.stage_number,
        "stage_text": presentation.stage_text,
        "language": presentation.language,
        "created_at": presentation.created_at,
        "task_id": task_id,
        "file_url": presentation.file.path if presentation.file else None  # Проверяем, есть ли файл
    }
from sqlalchemy.orm import joinedload

@router.delete("/presentations/{uuid}")
async def delete_presentation(
    uuid: str,
    session: AsyncSession = Depends(get_async_session),
    user: ExternalUserModel = Depends(verify_token),
):
    """
    Логическое удаление презентации по UUID.
    """
    # Загружаем презентацию с присоединенным файлом, если он есть
    query = (
        select(PresentationFile)
        .options(joinedload(PresentationFile.file))  # Загружаем файл заранее
        .where(
            PresentationFile.uuid == uuid,
            PresentationFile.external_user_id == user.id,
            PresentationFile.is_deleted == False  # Фильтруем только не удаленные презентации
        )
    )

    result = await session.execute(query)
    presentation = result.scalars().first()

    if not presentation:
        raise HTTPException(status_code=404, detail="Презентация не найдена")

    # Устанавливаем флаг `is_deleted = True`
    presentation.is_deleted = True

    # Если есть файл, также помечаем его как удаленный
    if presentation.file:
        presentation.file.is_deleted = True

    # Фиксируем изменения в БД
    await session.commit()

    return {"message": "Презентация успешно удалена"}

