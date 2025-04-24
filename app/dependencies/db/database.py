from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import DB_NAME, DB_PORT, DB_HOST, DB_PASS, DB_USER

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_async_engine(DATABASE_URL)
async_session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)





# Функция для получения сессии
async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

