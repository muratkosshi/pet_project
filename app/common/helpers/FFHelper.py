import logging
import mimetypes
from http.client import HTTPException

import aiohttp
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file_model import FileModel


class FFHelper:
    UPLOAD_URL = "https://ff.bilimal.kz/upload"

    @staticmethod
    async def upload_file(file_path: str, session: AsyncSession) -> Optional[dict]:
        """
        Загружает файл на сервер с использованием ключа, который включает структуру директорий.

        :param file_path: Путь к файлу на диске.
        :param session: Сессия SQLAlchemy.
        :return: Ответ от сервера.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден.")

        # Определение имени файла
        file_name = os.path.basename(file_path)

        # Получение текущего года
        current_year = datetime.now().year

        # Создание ключа для структуры директорий
        name = f"Ai-Pitchmaker/presentations/{current_year}/{file_name}"

        # Определение MIME-типа файла
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"  # MIME по умолчанию

        # Формируем данные для отправки
        form_data = aiohttp.FormData()
        form_data.add_field(
            "Upload[file]",
            open(file_path, "rb"),
            filename=file_name,
            content_type=mime_type
        )
        form_data.add_field("Upload[name]", name)  # Добавляем ключ
        form_data.add_field("Upload[key]", name)  # Добавляем ключ

        async with aiohttp.ClientSession() as client:
            async with client.post(FFHelper.UPLOAD_URL, data=form_data) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Ошибка загрузки файла: {await response.text()}"
                    )
                response_data = await response.json()

        if "host" in response_data and "url" in response_data:
            # Сохраняем информацию о файле в базе данных
            file_record = FileModel(path=response_data["url"], is_deleted=False)
            session.add(file_record)
            await session.commit()
            return response_data
        return None

    @staticmethod
    def get_ff_by_file(file_path: str) -> Optional[dict]:
        """
        Получает сохраненные данные о файле из локального кеша.

        :param file_path: Путь к файлу.
        :return: Данные о файле или None.
        """
        md5_hash = hashlib.md5(Path(file_path).read_bytes()).hexdigest()
        cache_path = Path("/tmp") / md5_hash
        if cache_path.exists():
            with open(cache_path, "r") as f:
                return json.load(f)
        return None

    @staticmethod
    def set_ff_by_file(file_path: str, ff_file: dict):
        """
        Сохраняет данные о файле в локальный кеш.

        :param file_path: Путь к файлу.
        :param ff_file: Данные о файле для сохранения.
        """
        md5_hash = hashlib.md5(Path(file_path).read_bytes()).hexdigest()
        cache_path = Path("/tmp") / md5_hash
        with open(cache_path, "w") as f:
            json.dump(ff_file, f)

    @staticmethod
    async def mark_file_as_deleted(file_path: str, session: AsyncSession) -> bool:
        """
        Помечает файл как удаленный в базе данных.
        """
        result = await session.execute(
            select(FileModel).where(FileModel.path == file_path)
        )
        file_record = result.scalars().first()

        if file_record:
            file_record.is_deleted = True
        else:
            logging.info(f"⚠️ Файл {file_path} отсутствует в базе, создаём запись...")
            file_record = FileModel(path=file_path, is_deleted=True)
            session.add(file_record)

        try:
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            raise RuntimeError(f"Ошибка при обновлении файла: {str(e)}")