from sqlalchemy import Column, Integer, String, Boolean, Float
from app.models import Base


class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)  # Уникальный ключ настройки
    value = Column(String, nullable=False)            # Значение настройки в строковом формате
    description = Column(String, nullable=True)       # Описание настройки для админов
    value_type = Column(String, nullable=False)       # Тип данных (например, "int", "float", "bool", "str")

    def cast_value(self):
        """Преобразует значение из строки в нужный тип данных."""
        if self.value_type == "int":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ["true", "1", "yes"]
        return self.value
