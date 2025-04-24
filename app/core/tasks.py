import asyncio
from datetime import datetime
import os
import logging

from sqlalchemy.future import select
from app.core.celery.celery import celery_app
from app.dependencies.db.database import async_session_factory
from app.dependencies.redis.redis import redis
from app.engine.generation.gen_ppt_outline import GenOutline, GenBody
from app.engine.mdtree.tree2ppt import Tree2PPT
from app.common.helpers.FFHelper import FFHelper
from app.models import PresentationFile, FileModel, TaskStatus

# 🚀 Подключение к Redis


async def update_task_status(session, task_id, status, uuid):
    try:
        result = await session.execute(select(TaskStatus).where(TaskStatus.task_id == task_id))
        task_status = result.scalars().first()

        if task_status:
            task_status.status = status
            task_status.updated_at = datetime.utcnow()
        else:
            new_task_status = TaskStatus(task_id=task_id, status=status)
            session.add(new_task_status)

        await session.commit()
        logging.info(f"✅ [DB] Task ID {task_id} обновлен до {status} uuid {uuid}")

    except Exception as e:
        await session.rollback()
        logging.error(f"❌ Ошибка при обновлении TaskStatus для {task_id}, uuid: {uuid}: {e}", exc_info=True)


@celery_app.task(name="app.core.tasks.generate_outline_task")
def generate_outline_task(uuid: str, title: str, topic_num: int, language: str):
    task_id = generate_outline_task.request.id
    logging.info(f"🚀 Начало генерации Outline для UUID {uuid}, Task ID: {task_id}")

    async def async_run():
        async with async_session_factory() as session:
            try:
                await update_task_status(session, task_id, "IN_PROGRESS", uuid)

                result = await session.execute(select(PresentationFile).where(PresentationFile.uuid == uuid))
                presentation_file = result.scalars().first()

                if not presentation_file:
                    await update_task_status(session, task_id, "FAILURE", uuid)
                    return "Error: Presentation Not Found"

                presentation_file.theme = title
                presentation_file.language = language
                await session.commit()

                gen_outline = GenOutline(uuid, session)
                generated_text = await gen_outline.predict_outline_v2(title, topic_num, language)

                presentation_file.stage_text = generated_text
                presentation_file.stage_number = 1
                await session.commit()

                await update_task_status(session, task_id, "SUCCESS", uuid)
                return generated_text

            except Exception as e:
                await update_task_status(session, task_id, "FAILURE", uuid)
                await session.rollback()
                logging.error(f"❌ Ошибка в Celery-задаче generate_outline_task: {str(e)}", exc_info=True)
                raise

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_run())


@celery_app.task(name="app.core.tasks.generate_body_task")
def generate_body_task(uuid: str, outline: str, language: str, outlines: list):
    task_id = generate_body_task.request.id
    logging.info(f"🚀 Начало генерации Body для UUID {uuid}, Task ID: {task_id}")

    async def async_run():
        async with async_session_factory() as session:
            try:
                # 🚀 Устанавливаем `IN_PROGRESS` и публикуем в Redis
                await update_task_status(session, task_id, "IN_PROGRESS", uuid)

                result = await session.execute(select(PresentationFile).where(PresentationFile.uuid == uuid))
                presentation_file = result.scalars().first()

                if not presentation_file:
                    await update_task_status(session, task_id, "FAILURE", uuid)
                    return "Error: Presentation Not Found"

                outlines_text = "\n".join([f"# {outline['title']}" for outline in outlines])
                presentation_file.stage_text = outlines_text
                presentation_file.language = language
                await session.commit()

                gen_body = GenBody(uuid, session)
                generated_body = await gen_body.predict_body(fix_outline=outline, language=language)

                if not generated_body:
                    await update_task_status(session, task_id, "FAILURE", uuid)
                    return "Error: Body Generation Failed"

                presentation_file.stage_text = generated_body
                presentation_file.stage_number = 2
                await session.commit()

                # 🚀 Отправляем SUCCESS в Redis сразу после обновления БД
                await update_task_status(session, task_id, "SUCCESS", uuid)

                return generated_body

            except Exception as e:
                await update_task_status(session, task_id, "FAILURE", uuid)
                logging.error(f"❌ Ошибка: {str(e)}", exc_info=True)
                raise

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_run())



@celery_app.task(name="app.core.tasks.generate_ppt_task")
def generate_ppt_task(uuid: str, theme_title: str, paper: str, theme: str):
    task_id = generate_ppt_task.request.id
    logging.info(f"🚀 Начало генерации PPT для UUID {uuid}, Task ID: {task_id}")

    async def async_run():
        async with async_session_factory() as session:
            ppt = None
            try:
                await update_task_status(session, task_id, "IN_PROGRESS", uuid)

                result = await session.execute(select(PresentationFile).where(PresentationFile.uuid == uuid))
                presentation_file = result.scalars().first()

                if not presentation_file:
                    await update_task_status(session, task_id, "FAILURE", uuid)
                    raise

                presentation_file.stage_text = paper
                await session.commit()

                ppt = Tree2PPT(paper, theme_title, theme, '', uuid)
                ppt_stream = ppt.save_stream()

                with open(ppt.path, "wb") as f:
                    f.write(ppt_stream.getvalue())

                uploaded_file = await FFHelper.upload_file(ppt.path, session)
                if not uploaded_file:
                    await update_task_status(session, task_id, "FAILURE", uuid)
                    raise

                existing_file_query = await session.execute(select(FileModel).where(FileModel.path == uploaded_file["url"]))
                existing_file = existing_file_query.scalars().first()

                if existing_file:
                    file_id = existing_file.id
                else:
                    new_file = FileModel(path=uploaded_file["url"], is_deleted=False)
                    session.add(new_file)
                    await session.flush()
                    file_id = new_file.id

                if not file_id:
                    await update_task_status(session, task_id, "FAILURE", uuid)
                    raise

                presentation_file.file_id = file_id
                presentation_file.stage_number = 3
                session.add(presentation_file)
                await session.commit()

                await update_task_status(session, task_id, "SUCCESS", uuid)
                return {"file_url": uploaded_file["url"]}

            except Exception as e:
                await update_task_status(session, task_id, "FAILURE", uuid)
                await session.rollback()
                logging.error(f"❌ Ошибка: {str(e)}", exc_info=True)
                raise

            finally:
                if ppt and hasattr(ppt, "path") and os.path.exists(ppt.path):
                    try:
                        os.remove(ppt.path)
                        logging.info(f"✅ Успешно удален файл: {ppt.path}")
                    except Exception as e:
                        logging.error(f"⚠️ Ошибка при удалении файла: {e}")

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_run())
