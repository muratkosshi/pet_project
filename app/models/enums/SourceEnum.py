import enum


class SourceEnum(enum.IntEnum):
    BILIMAL = 1

    @classmethod
    def get_display_name(cls, value):
        # Проверяем, существует ли значение в Enum
        if value in cls._value2member_map_:
            return cls(value).display_name
        return "Неизвестный источник"

    @property
    def display_name(self):
        return {
            SourceEnum.BILIMAL: "Бiлiмал",
        }.get(self, "Неизвестный источник")
