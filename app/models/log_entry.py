from sqlalchemy import Column, Integer, String, DateTime, func, Text

from app.models import Base


class LogEntry(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String, index=True)
    message = Column(Text)  # Используем Text для хранения длинных сообщений
    traceback = Column(Text, nullable=True)  # Отдельное поле для полного traceback
    timestamp = Column(DateTime, default=func.now())

