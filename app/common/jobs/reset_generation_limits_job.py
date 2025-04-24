import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select

from app.models import ExternalUserModel


async def reset_generation_limits(session_maker):
    """
    Асинхронная функция для сброса лимитов генерации.
    :param session_maker: Фабрика сессий SQLAlchemy.
    """
    print("Проверка и сброс лимита генераций...")
    async with session_maker() as session:
        async with session.begin():
            users_query = await session.execute(
                select(ExternalUserModel).where(
                    ExternalUserModel.reset_generation_at <= datetime.utcnow()
                )
            )
            users = users_query.scalars().all()

            for user in users:
                user.generation_count = 0
                user.reset_generation_at = user.reset_generation_at + timedelta(days=30)
                print(f"Лимит генераций сброшен для пользователя {user.id}")

            await session.commit()
    print("Сброс лимитов завершен.")


def start_scheduler_reset_generation_limits(session_maker):
    """
    Запускает APScheduler для регулярного сброса лимитов.
    :param session_maker: Фабрика сессий SQLAlchemy.
    """
    scheduler = AsyncIOScheduler()

    async def wrapper():
        await reset_generation_limits(session_maker)

    scheduler.add_job(
        wrapper,
        'cron',  # Запуск в определенное время каждый день
        hour=1,  # Указываем время запуска
        minute=0,
    )
    scheduler.start()
    print("Scheduler started")
