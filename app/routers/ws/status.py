from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from sqlalchemy.future import select
import asyncio
import logging
from starlette.websockets import WebSocketState

from sqlalchemy.orm import joinedload
from app.dependencies.db.database import async_session_maker
from app.dependencies.redis.redis import redis
from app.models import PresentationFile

router = APIRouter()
active_connections = {}

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def get_presentation_data(uuid: str):
    async with async_session_maker() as session:
        result = await session.execute(
            select(PresentationFile)
            .options(joinedload(PresentationFile.task_status))
            .where(PresentationFile.uuid == uuid)
        )
        presentation = result.scalars().first()

        if presentation:
            return {
                "uuid": uuid,
                "status": presentation.task_status.status if presentation.task_status else None,
                "stage_number": presentation.stage_number,
                "stage_text": presentation.stage_text,
                "theme": presentation.theme,
                "file_id": presentation.file_id
            }
        return None


@router.websocket("/{uuid}")
async def websocket_status_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    active_connections[uuid] = websocket
    logger.info(f"✅ WebSocket подключен: {uuid}")

    try:
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"presentation_updates:{uuid}")

        # 🔹 1️⃣ Отправляем актуальные данные сразу при подключении
        initial_data = await get_presentation_data(uuid)
        if initial_data:
            await websocket.send_json(initial_data)

        while uuid in active_connections:
            # 🔄 2️⃣ Получаем новое сообщение
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)

            if message:
                logger.info(f"📩 Обновление из Redis: {message['data']}")
                updated_data = await get_presentation_data(uuid)

                if updated_data and uuid in active_connections and websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(updated_data)

                # ✅ Закрываем WebSocket, если задача завершена
                if updated_data and updated_data["stage_number"] == 3 and updated_data["status"] == "SUCCESS":
                    logger.info(f"✅ Презентация {uuid} завершена, закрываем WebSocket.")
                    break
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info(f"❌ WebSocket отключен: {uuid}")
    except Exception as e:
        logger.error(f"🚨 Ошибка WebSocket для {uuid}: {e}")
    finally:
        active_connections.pop(uuid, None)
        await pubsub.unsubscribe(f"presentation_updates:{uuid}")
        await websocket.close()
