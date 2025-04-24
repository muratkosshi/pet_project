import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.tasks import generate_outline_task, generate_body_task, generate_ppt_task
from app.dependencies.db.database import get_async_session
from app.core.auth.auth import verify_token
from app.models import PresentationFile, TaskStatus
from app.models.external_user_model import ExternalUserModel

router = APIRouter()


class OutlineRequest(BaseModel):
    uuid: str
    title: str
    topic_num: int
    language: str

@router.post("/generate_outline")
async def generate_outline(
    request: Request,
    outline_request: OutlineRequest,
    user: ExternalUserModel = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        ip_address = request.client.host
        logging.info(f"IP address: {ip_address} UUID: {outline_request.uuid} Generating outline")

        # 🚀 Отправляем задачу в Celery
        task = generate_outline_task.delay(
            outline_request.uuid,
            outline_request.title,
            outline_request.topic_num,
            outline_request.language
        )

        # ✅ Получаем объект TaskStatus
        task_status_result = await session.execute(
            select(TaskStatus).where(TaskStatus.task_id == task.id)
        )
        task_status = task_status_result.scalars().first()

        if not task_status:
            task_status = TaskStatus(task_id=task.id, status="PENDING")
            session.add(task_status)

        # ✅ Обновляем task_id в PresentationFile
        result = await session.execute(select(PresentationFile).where(PresentationFile.uuid == outline_request.uuid))
        presentation_file = result.scalars().first()

        if presentation_file:
            presentation_file.task_id = task.id  # ✅ Используем `task.id`
            session.add(presentation_file)
        else:
            raise HTTPException(status_code=404, detail="Презентация не найдена")

        await session.commit()  # ✅ Один коммит для всех изменений
        return {"message": "Генерация запущена", "task_id": task.id}

    except Exception as e:
        await session.rollback()
        logging.error(f"Ошибка при запуске генерации outline: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Произошла ошибка при обработке запроса")





class BodyRequest(BaseModel):
    uuid: str
    outline: str
    language: str
    outlines: list


@router.post("/generate_body")
async def generate_body(
    request: Request,
    body_request: BodyRequest,
    user: ExternalUserModel = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        ip_address = request.client.host
        logging.info(f'IP address: {ip_address} | UUID: {body_request.uuid} | Generating body')

        # 🚀 Отправляем задачу в Celery
        task = generate_body_task.delay(
            body_request.uuid,
            body_request.outline,
            body_request.language,
            body_request.outlines
        )

        # ✅ Получаем объект TaskStatus
        task_status_result = await session.execute(
            select(TaskStatus).where(TaskStatus.task_id == task.id)
        )
        task_status = task_status_result.scalars().first()

        if not task_status:
            # ✅ Создаем TaskStatus только если его нет
            task_status = TaskStatus(task_id=task.id, status="PENDING")
            session.add(task_status)

        # ✅ Обновляем task_id в PresentationFile
        result = await session.execute(select(PresentationFile).where(PresentationFile.uuid == body_request.uuid))
        presentation_file = result.scalars().first()

        if presentation_file:
            old_task_id = presentation_file.task_id
            if old_task_id:
                # ❌ Удаляем старую запись TaskStatus
                await session.execute(delete(TaskStatus).where(TaskStatus.task_id == old_task_id))

            presentation_file.task_id = task.id  # ✅ Используем `task.id`
            session.add(presentation_file)

        else:
            raise HTTPException(status_code=404, detail="Презентация не найдена")

        await session.commit()  # ✅ Один коммит для всех изменений
        return {"message": "Генерация запущена", "task_id": task.id}

    except Exception as e:
        await session.rollback()
        logging.error(f"Ошибка при запуске генерации тела: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при обработке запроса")





class PPTRequest(BaseModel):
    theme_title: str
    paper: str  # Assuming this is a string containing Markdown content
    theme: str
    uuid: str


@router.post("/generate_ppt")
async def generate_ppt(
    ppt_request: PPTRequest,
    request: Request,
    user: ExternalUserModel = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Отправляет генерацию PPT в Celery и сразу возвращает `task_id`.
    """
    try:
        ip_address = request.client.host
        logging.info(f"📄 Запуск генерации PPT | IP: {ip_address} | UUID: {ppt_request.uuid}")

        # 🚀 Отправляем задачу в Celery
        task = generate_ppt_task.delay(
            ppt_request.uuid,
            ppt_request.theme_title,
            ppt_request.paper,
            ppt_request.theme
        )

        # ✅ Создаем запись в `TaskStatus`
        existing_task_status = await session.execute(
            select(TaskStatus).where(TaskStatus.task_id == task.id)
        )
        if not existing_task_status.scalars().first():
            # ✅ Создаем запись в `TaskStatus`, только если ее нет
            new_task_status = TaskStatus(task_id=task.id, status="PENDING")
            session.add(new_task_status)

        # ✅ Обновляем task_id в `PresentationFile`
        result = await session.execute(select(PresentationFile).where(PresentationFile.uuid == ppt_request.uuid))
        presentation_file = result.scalars().first()
        if presentation_file:
            old_task_id = presentation_file.task_id
            if old_task_id:
                # ❌ Удаляем старую запись из `task_statuses`
                await session.execute(
                    delete(TaskStatus).where(TaskStatus.task_id == old_task_id)
                )
            presentation_file.task_id = task.id
            session.add(presentation_file)
        else:
            raise
        await session.commit()  # ✅ Один коммит для всех изменений
        return {"message": "Генерация PPT запущена", "task_id": task.id}

    except Exception as e:
        await session.rollback()  # ❌ Откатываем, если ошибка
        logging.error(f"❌ Ошибка при запуске генерации PPT: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при обработке запроса")
