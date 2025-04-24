import asyncio
import logging
import time
from asyncio import create_task
from traceback import format_exc

from fastapi import FastAPI, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.dependencies.db.database import get_async_session
from app.models import LogEntry


class DatabaseLogHandler(logging.Handler):
    """Лог-хендлер для записи логов в базу данных асинхронно."""

    def __init__(self):
        super().__init__()

    def emit(self, record):
        """Синхронный вызов emit, но работа с БД идёт в фоновой задаче."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._emit_async(record))  # Создаём задачу в текущем event loop
        except RuntimeError:
            # Если event loop отсутствует, отправляем лог в отдельный поток
            asyncio.run(self._emit_async(record))

    async def _emit_async(self, record):
        """Асинхронная запись лога в БД."""
        async for session in get_async_session():
            async with session.begin():
                log_entry = LogEntry(
                    level=record.levelname,
                    message=record.getMessage(),
                    traceback=record.exc_text if record.exc_info else None,
                )
                session.add(log_entry)
            await session.commit()  # Коммит транзакции
    def format_message(self, record):
        """Генерируем кастомные сообщения в зависимости от уровня логирования."""
        level = record.levelname

        if level == "INFO":
            return f"ℹ️ INFO: {record.getMessage()}"
        elif level == "WARNING":
            return f"⚠️ WARNING: {record.getMessage()}"
        elif level == "ERROR":
            return f"❌ ERROR: {record.getMessage()}"
        elif level == "CRITICAL":
            return f"🔥 CRITICAL ERROR: {record.getMessage()}"
        else:
            return f"🔍 DEBUG: {record.getMessage()}"

# Создаем и добавляем кастомный лог-хендлер
db_handler = DatabaseLogHandler()
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)
logger.addHandler(db_handler)

# Настройка логирования (Консоль + Файл)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # Логирование в файл
        logging.StreamHandler(),         # Логирование в консоль
        db_handler,                      # Логирование в БД
    ]
)


async def save_log_to_db(session: AsyncSession, level: str, message: str, exc_info=None):
    """Сохраняет логи в базу данных."""
    traceback_text = None

    if exc_info:
        # Получаем полный traceback
        logging.exception(message, exc_info=exc_info)
        traceback_text = format_exc()

    async with session.begin():
        log_entry = LogEntry(level=level, message=message, traceback=traceback_text)
        session.add(log_entry)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования запросов и ответов."""

    def __init__(self, app: FastAPI):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        async for session in get_async_session():  # Убираем session_factory
            try:
                # Логируем входящий запрос
                log_message = f"📥 Request: {request.method} {request.url.path} from {request.client.host}"
                logging.info(log_message)
                await save_log_to_db(session, "INFO", log_message)

                response = await call_next(request)
                process_time = time.time() - start_time
                response_message = f"✅ Response: {response.status_code} ({process_time:.2f}s)"
                logging.info(response_message)
                await save_log_to_db(session, "INFO", response_message)

                return response

            except Exception as e:
                process_time = time.time() - start_time
                error_message = f"❌ Error: {str(e)} ({process_time:.2f}s)"
                logging.error(error_message, exc_info=True)
                await save_log_to_db(session, "ERROR", error_message, exc_info=e)
                return Response("Internal Server Error", status_code=500)
