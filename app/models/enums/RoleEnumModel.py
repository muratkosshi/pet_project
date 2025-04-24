import enum

class RoleEnum(enum.IntEnum):
    TEACHER = 4
    DIRECTOR = 7

    @classmethod
    def is_allowed(cls, role_id):
        """Проверяем, имеет ли пользователь доступ"""
        return role_id in {cls.TEACHER, cls.DIRECTOR}
