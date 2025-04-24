import enum


class UserTypeEnum(enum.Enum):
    MAPADMIN = 48
    SIMPLE_USER = 50
    STATISTIC = 41
    NEWSMAKER = 35
    NEWSTRANSLATER = 36
    NEWSADMIN = 38
    SUPERADMIN_WOCP = 49
    ADMIN = 40
    TEACHER = 4
    BLOGGER = 44
    TEHSPEC = 42
    LIKEADMIN = 46
    PARENT = 2
    VOTER = 45
    GUEST = -1
    SUPERADMIN = 1
    SCHOOL_ADMINISTRATOR = 52
    HEADBLOGS = 43
    PUPIL = 3
    MENDELEEV_TRANSLATE = 51
    LIBRARIAN = 6
    LIBRARIAN_ADMIN = 8
    DDIRECTOR = 53
    API_ADMIN_JOURNAL = 99
    PAGE_EDITOR = 54
    DIRECTOR = 7

    @classmethod
    def get_display_name(cls, value):
        """Безопасно пытаемся получить значение, если оно есть в Enum"""
        if value in cls._value2member_map_:
            return cls(value).display_name
        return "Неизвестный тип"

    @property
    def display_name(self):
        """Читаемые названия ролей"""
        return {
            UserTypeEnum.MAPADMIN: "Картографический администратор",
            UserTypeEnum.SIMPLE_USER: "Обычный пользователь",
            UserTypeEnum.STATISTIC: "Статист",
            UserTypeEnum.NEWSMAKER: "Редактор новостей",
            UserTypeEnum.NEWSTRANSLATER: "Переводчик новостей",
            UserTypeEnum.NEWSADMIN: "Администратор новостей",
            UserTypeEnum.SUPERADMIN_WOCP: "Суперадмин (без контроля прав)",
            UserTypeEnum.ADMIN: "Администратор",
            UserTypeEnum.TEACHER: "Учитель",
            UserTypeEnum.BLOGGER: "Блогер",
            UserTypeEnum.TEHSPEC: "Технический специалист",
            UserTypeEnum.LIKEADMIN: "Лайк-администратор",
            UserTypeEnum.PARENT: "Родитель",
            UserTypeEnum.VOTER: "Голосующий",
            UserTypeEnum.GUEST: "Гость",
            UserTypeEnum.SUPERADMIN: "Суперадмин",
            UserTypeEnum.SCHOOL_ADMINISTRATOR: "Школьный администратор",
            UserTypeEnum.HEADBLOGS: "Главный блогер",
            UserTypeEnum.PUPIL: "Ученик",
            UserTypeEnum.MENDELEEV_TRANSLATE: "Переводчик Менделеева",
            UserTypeEnum.LIBRARIAN: "Библиотекарь",
            UserTypeEnum.LIBRARIAN_ADMIN: "Администратор библиотеки",
            UserTypeEnum.DDIRECTOR: "Заместитель директора",
            UserTypeEnum.API_ADMIN_JOURNAL: "API администратор журнала",
            UserTypeEnum.PAGE_EDITOR: "Редактор страниц",
            UserTypeEnum.DIRECTOR: "Директор",
        }.get(self, "Неизвестный тип")
