import datetime
import os
import shutil
from io import BytesIO

from google_images_search import GoogleImagesSearch
from pptx import Presentation
from pptx.util import Inches

# Подключаем класс для генерации слайдов из MD
from app.engine.mdtree.MdToSlide import MD2Slide
# Обновлённый парсер (parse_string, Out, Heading),
# где нет лишней логики skip
from app.engine.mdtree.parser import parse_string, Out, Heading

# Для выбора темы (опционально)

gis = GoogleImagesSearch(
    'AIzaSyCRgzHIaIcCW47-kIfF1sKQEpvpA_ZIeSo',
    'b42caca75b4a340f1'
)


class Tree2PPT:
    prs: Presentation = None
    md_str: str = None
    out: Out = None
    theme: str = None
    theme_title: str = None
    filename: str = None
    prompt: str = None
    path: str = None
    uuid: str = None

    def __init__(self, md_str1, theme_title, theme, prompt, uuid):
        """
        :param md_str1: исходный markdown-текст
        :param theme_title: строка темы (может использоваться для генерации картинок)
        :param theme: папка с фоновыми картинками (добавляем к ./pptx_static/static/bg/)
        :param prompt: промт для генератора изображений
        """
        self.theme = "./pptx_static/static/bg/" + theme
        self.theme_title = theme_title
        self.prompt = prompt
        self.uuid = uuid

        # Инициализация презентации
        self.init_pptx()

        # Парсим markdown-текст
        self.init_markdown(md_str1)

        # Обходим все топовые заголовки (out.main + out.children) и их потомков
        self.traverse_all_headings()

        # Сохраняем результат
        now = datetime.datetime.now().timestamp()
        self.path = './myppt/' + str(now) + '.pptx'
        self.filename = now

        if not os.path.exists('./myppt'):
            os.makedirs('./myppt')
        self.prs.save(self.path)
        self.delete_files_and_folders_in_folder(f"./temp_images/{self.uuid}")

    def delete_files_and_folders_in_folder(self, folder_path: str):
        try:
            # Проверяем, существует ли папка
            if os.path.exists(folder_path):
                # Удаляем содержимое папки
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    try:
                        if os.path.isfile(file_path):
                            # Удаляем файл
                            os.remove(file_path)
                            print(f'Файл удален: {file_path}')
                        elif os.path.isdir(file_path):
                            # Удаляем папку и её содержимое
                            shutil.rmtree(file_path)
                            print(f'Папка удалена: {file_path}')
                    except Exception as e:
                        print(f'Ошибка при удалении {file_path}. {e}')

                # Удаляем саму папку
                os.rmdir(folder_path)
                print(f'Папка удалена: {folder_path}')
            else:
                print(f'Папка {folder_path} не существует.')
        except Exception as e:
            print(f'Ошибка при удалении папки {folder_path}. {e}')

    def init_pptx(self):
        """
        Создаём презентацию и выставляем размер слайдов (16:9 Wide).
        """
        self.prs = Presentation()
        self.prs.slide_width = Inches(20)
        self.prs.slide_height = Inches(11.25)

    def init_markdown(self, md_str):
        """
        Парсим MD-текст обновлённым парсером, сохраняем результат в self.out.
        """
        self.md_str = md_str
        self.out = parse_string(md_str)

    def traverse_all_headings(self):
        """
        Проходим по ВСЕМ заголовкам верхнего уровня:
          - out.main (если есть)
          - out.children (если там тоже есть заголовки уровня 1)
        Каждый из них, а также их вложенные children, превращаем в слайды.
        """
        # 1) Если есть out.main, обходим его ветку
        if self.out.main is not None:
            self.traverse_tree(self.out.main, self.theme_title, self.prompt)

        # 2) Кроме того, out.children могут содержать ещё заголовки уровня 1
        for child in self.out.children:
            # Проверяем, что child - это Heading (если в children могут быть другие элементы)
            if isinstance(child, Heading):
                # обходим это поддерево
                self.traverse_tree(child, self.theme_title, self.prompt)

    def traverse_tree(self, heading: Heading, theme_title: str, prompt: str):
        """
        Рекурсивно обходим дерево заголовков,
        На каждый делаем слайд. heading.text => title, heading.source => content
        """
        if heading is None:
            return

        content = heading.source or ""  # Если source нет, будет ""
        MD2Slide(
            presentation=self.prs,
            theme_path=self.theme,
            title=heading.text,
            theme_title=theme_title,
            content=content,
            prompt=prompt,
            uuid=self.uuid
        )

        # Дальше обходим дочерние заголовки
        for child in heading.children:
            self.traverse_tree(child, theme_title, prompt)

    def save_stream(self):
        """
        Сохранение презентации в поток (например, для отдачи через HTTP).
        """
        stream = BytesIO()
        self.prs.save(stream)
        stream.seek(0)
        return stream
