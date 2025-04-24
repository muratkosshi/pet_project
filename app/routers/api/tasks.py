from datetime import datetime

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select

from app.core.tasks import update_task_status
from app.dependencies.db.database import get_async_session
from app.models import TaskStatus, PresentationFile

router = APIRouter()

@router.get("/task_status/{task_id}")
async def get_task_status(task_id: str):
    """
    Проверяет статус задачи Celery.
    """
    result = AsyncResult(task_id)
    return {"task_id": task_id, "status": result.status, "result": result.result}


@router.post("/cancel_task/{task_id}")
async def cancel_task(task_id: str, session: AsyncSession = Depends(get_async_session)):
    """
    Отменяет задачу Celery по `task_id`, обновляет ее статус в `TaskStatus` и возвращает `uuid` презентации.
    """
    result = AsyncResult(task_id)

    if not result:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    # 🔥 Отменяем задачу Celery
    result.revoke(terminate=True, signal="SIGKILL")

    try:
        # ✅ Найти `uuid` презентации по `task_id`
        presentation_query = await session.execute(
            select(PresentationFile).where(PresentationFile.task_id == task_id)
        )
        presentation = presentation_query.scalars().first()

        if not presentation:
            raise HTTPException(status_code=404, detail="Презентация для этой задачи не найдена")

        uuid = presentation.uuid  # ✅ Получаем `uuid` презентации
        await update_task_status(session=session, task_id=task_id, status="CANCELLED", uuid=presentation.uuid)
        # ✅ Обновляем статус в `TaskStatus`
        await session.execute(
            update(TaskStatus)
            .where(TaskStatus.task_id == task_id)
            .values(status="CANCELLED", updated_at=datetime.utcnow())
        )

        await session.commit()

        return {"message": f"Задача {task_id} была отменена и статус обновлен.", "presentation_uuid": uuid}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при отмене задачи: {str(e)}")
