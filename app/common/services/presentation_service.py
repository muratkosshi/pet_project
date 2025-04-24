from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.models.presentation_file_model import PresentationFile
from app.models.external_user_model import ExternalUserModel
from app.models.file_model import FileModel
from fastapi import HTTPException


class PresentationService:
    @staticmethod
    async def add_presentation(
            session: AsyncSession, external_user_id: int, file_path: str, theme: str
    ) -> PresentationFile:
        """
        Добавляет новую презентацию, включая создание записи о файле.

        :param session: Асинхронная сессия базы данных.
        :param external_user_id: ID внешнего пользователя.
        :param file_path: Путь к файлу.
        :param theme: Тема презентации.
        :return: Созданная презентация.
        """
        # Проверка существования внешнего пользователя
        user_query = await session.execute(
            select(ExternalUserModel).where(ExternalUserModel.id == external_user_id)
        )
        user = user_query.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="External user not found")

        # Создание записи о файле
        file = FileModel(path=file_path)
        session.add(file)
        await session.commit()
        await session.refresh(file)

        # Создание новой презентации
        presentation = PresentationFile(
            external_user_id=external_user_id,
            file_id=file.id,
            theme=theme
        )
        session.add(presentation)
        await session.commit()
        await session.refresh(presentation)

        return presentation

    @staticmethod
    def get_presentation_by_id(session: Session, presentation_id: int) -> PresentationFile:
        """
        Получает презентацию по ID.

        :param session: Сессия базы данных.
        :param presentation_id: ID презентации.
        :return: Презентация.
        """
        presentation = session.query(PresentationFile).filter_by(id=presentation_id).first()
        if not presentation:
            raise HTTPException(status_code=404, detail="Presentation not found")
        return presentation

    @staticmethod
    def update_presentation_theme(session: Session, presentation_id: int, new_theme: str) -> PresentationFile:
        """
        Обновляет тему презентации.

        :param session: Сессия базы данных.
        :param presentation_id: ID презентации.
        :param new_theme: Новая тема.
        :return: Обновленная презентация.
        """
        presentation = session.query(PresentationFile).filter_by(id=presentation_id).first()
        if not presentation:
            raise HTTPException(status_code=404, detail="Presentation not found")

        presentation.theme = new_theme
        session.commit()
        session.refresh(presentation)

        return presentation

    @staticmethod
    def get_all_presentations_by_user(session: Session, external_user_id: int) -> list[PresentationFile]:
        """
        Получает все презентации пользователя.

        :param session: Сессия базы данных.
        :param external_user_id: ID внешнего пользователя.
        :return: Список презентаций.
        """
        presentations = session.query(PresentationFile).filter_by(external_user_id=external_user_id).all()
        return presentations
