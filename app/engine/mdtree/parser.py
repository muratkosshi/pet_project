import re
from typing import Optional


def parse_string(string, debug_level=0):
    """
    Функция: удобная обёртка для парсинга строки.
    """
    return Parser(debug_level).parse(string)


def parse_file(file_path, debug_level=0, encoding='utf-8'):
    """
    Функция: обёртка для чтения файла и парсинга.
    """
    with open(file_path, encoding=encoding) as f:
        return parse_string(f.read(), debug_level)


class Element:
    """
    Базовый элемент структуры (корневой или заголовок).
    """
    def __init__(self):
        self.source = None        # Хранит текст (не-заголовочные строки)
        self.children = []        # Дочерние элементы (Heading)

    @property
    def full_source(self):
        """
        Собирает full_source из всех children рекурсивно.
        """
        if len(self.children) == 0:
            return ''
        return '\n' + '\n'.join([x.full_source for x in self.children])

    def add_child(self, el):
        self.children.append(el)

    def add_source(self, source):
        """
        Добавляет текст (обычные строки) внутрь элемента.
        """
        if self.source is None:
            self.source = source
        else:
            self.source += '\n' + source

    def __getitem__(self, item):
        return self.children[item]

    def __len__(self):
        return len(self.children)


class Out(Element):
    """
    Корневой элемент. level=0.
    Может хранить первый заголовок (main) и прочие дочерние heading.
    """
    main = None
    level = 0

    @property
    def title(self):
        if self.main is not None:
            return self.main.text

    @property
    def full_source(self):
        """
        Собирает source (если есть) + full_source главного заголовка (если есть) + full_source children.
        """
        result = ''
        if self.source is not None:
            result += f'{self.source}\n'
        if self.main:
            result += self.main.full_source
        result += super().full_source
        return result

    def __str__(self):
        return 'Out'


class Heading(Element):
    """
    Элемент-заголовок. Имеет:
    - root, parent: ссылки на корень и родителя
    - level: уровень заголовка (1=#, 2=##, ...)
    - text: сам текст заголовка
    - text_source: исходная строка (с символами #, пробелами и т.д.)
    """
    def __init__(self, root, parent, level, text, text_source):
        super().__init__()
        self.root = root
        self.parent = parent
        self.level = level
        self._text = text
        self._text_source = text_source

    text = property()

    @text.getter
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        # При изменении текста - обновляем text_source
        self._text_source = self._text_source.replace(self._text, value)
        self._text = value

    @property
    def text_source(self):
        return self._text_source

    @property
    def full_source(self):
        """
        Собирает: text_source + source (если есть) + children (рекурсивно).
        """
        result = f'{self._text_source}'
        if self.source is not None:
            result += f'\n{self.source}'
        result += super().full_source
        return result

    def __str__(self):
        return self._text


class Parser:
    """
    Основной парсер. Ищет заголовки (подчёркивающие и #) и формирует дерево (Out -> Heading).
    """

    def __init__(self, debug_level=0):

        self.DEBUG = debug_level
        self.out = Out()
        self.current: Optional[Heading] = None
        self.last_heading_index = -999

    def parse(self, text):
        self.strings = text.split("\n")
        self.out = Out()
        self.current = None
        code_block = False  # если встретим тройные кавычки ```, переключим True/False

        strings = text.split('\n')
        for index in range(len(strings)):


            string = strings[index]
            is_heading = False

            # Проверка: не находимся ли мы в блоке кода ```...```
            if re.search(r'^\s*```.*$', string) is not None:
                code_block = not code_block

            if not code_block:
                # Проверим, есть ли следующая строка (для подчёркивания === / ---)
                next_string = strings[index + 1] if (index + 1) < len(strings) else None

                # 1) Подчёркивающие заголовки:
                for level in range(1, 3):
                    is_heading = self._parse_heading_var_one(level, string, next_string)
                    if is_heading:
                        self.last_heading_index = index
                        break

                # 2) Markdown-подобные заголовки (#, ##, ###, ...)
                if not is_heading:
                    for level in range(1, 7):
                        is_heading = self._parse_heading_var_two(level, string, index)
                        if is_heading:
                            self.last_heading_index = index
                            break

            # Если строка не определилась как заголовок -> считаем её обычным текстом
            if not is_heading:
                if self.current is None:
                    self.out.add_source(string)
                else:
                    self.current.add_source(string)

        return self.out

    def _parse_heading_var_one(self, level, string, next_string):
        """
        Подчёркивающие заголовки: "Заголовок\n====" или "Заголовок\n----"
        level=1 -> ===
        level=2 -> ---
        """
        if next_string is None or re.search(r'^\s*$', string) is not None:
            return False

        if self.DEBUG >= 2:
            print(f'- parse_heading_var_one with level: {level}, next_string: "{next_string}"')

        if level == 1:
            tmpl = '='
        elif level == 2:
            tmpl = '-'
        else:
            raise Exception(f'Not support level: {level}')

        regex = r'^\s?' + tmpl + r'{3,}\s*$'
        result = re.search(regex, next_string)

        if result is None:
            return False

        return self._parse_heading_action(
            level=level,
            text=string.strip(),
            text_source=f'{string}\n{next_string}'
        )

    def _parse_heading_var_two(self, level, string, index):
        """
        Заголовки Markdown: "# text", "## text", "### text", ...
        """
        if self.DEBUG >= 2:
            print(f'- parse_heading_var_two with level: {level}, string: "{string}"')

        # Ровно level решёток, затем пробел, затем текст
        # ^(\s?#{N}\s+)(.*)$
        regex = r'^(\s?#{' + str(level) + r'}\s+)(.*)$'
        result = re.search(regex, string)
        if result is None:
            return False

        # Текст исходный
        text_source = result[1] + result[2]
        # Сам текст заголовка (без решёток)
        text = result[2].strip()

        pattern_level = level  # оставляем уровни как есть (1=>#,2=>##,3=>###,...)

        return self._parse_heading_action(
            level=pattern_level,
            text=text,
            text_source=text_source,
            index=index
        )

    def _is_contiguous(self, current_index):
        """
        Возвращает True, если все строки между self.last_heading_index+1 и current_index
        пустые (или содержат только пробелы), то есть нет существенного контента.
        """
        # Если строк между нет, считаем, что они идут подряд
        if current_index <= self.last_heading_index + 1:
            return True
        for i in range(self.last_heading_index + 1, current_index):
            if self.strings[i].strip() != "":
                return False
        return True

    def _parse_heading_action(self, level, text, text_source, index=None):
        # Если существует текущий заголовок и новый заголовок находится "рядом"
        # (то есть либо непосредственно следующей строкой, либо между ними только пустые строки),
        # и уровень нового заголовка больше текущего, объединяем их.
        if self.current is not None and index is not None and (
                index == self.last_heading_index + 1 or self._is_contiguous(index)):
            if level > self.current.level:
                # Объединяем текст заголовков, разделяя переносом строки
                merged_text = self.current.text + "\n" + text
                self.current.text = merged_text  # через сеттер обновится _text и _text_source
                # Явно объединяем исходное представление, если требуется
                self.current._text_source += "\n" + text_source
                if self.DEBUG >= 1:
                    print("Merged contiguous header into previous header:", self.current.text)
                self.last_heading_index = index
                return True

        # Если условие объединения не выполнено – стандартная логика создания нового заголовка.
        if self.current is None:
            parent = self.out
        elif level > self.current.level:
            parent = self.current
        else:
            parent = self.current.parent
            while parent.level >= level:
                parent = parent.parent

        self.current = Heading(self.out, parent, level, text, text_source)
        if level == 1 and self.out.main is None:
            self.out.main = self.current
        else:
            parent.add_child(self.current)

        if self.DEBUG >= 1:
            spaces = '  ' * (parent.level + 1) if parent != self.out else ''
            print(f'{spaces}<{str(parent)}>')
            spaces = '  ' * (self.current.level + 1)
            print(f'{spaces}(+) <{str(self.current)}>')

        self.last_heading_index = index if index is not None else self.last_heading_index
        return True
