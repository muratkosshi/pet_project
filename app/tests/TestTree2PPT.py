import datetime
import unittest
import os

from app.engine.mdtree.tree2ppt import Tree2PPT


class TestTree2PPT(unittest.TestCase):
    def test_presentation_creation(self):
        # Тестовая Markdown-строка
        markdown_file_path = 'txt.md'

        # Откройте файл и прочитайте его содержимое
        with open(markdown_file_path, 'r', encoding='utf-8') as file:
            md_str = file.read()

        theme_title = "Фотосинтез"

        # Создаем презентацию
        ppt = Tree2PPT(md_str, theme_title)

        # Проверяем, что презентация создана
        self.assertIsNotNone(ppt.prs, "Презентация не была создана")

        # Проверяем, что в презентации есть слайды
        self.assertGreater(len(ppt.prs.slides), 0, "В презентации нет слайдов")

        # Проверяем, что файл презентации был сохранен
        now = datetime.datetime.now().timestamp()
        expected_path = './myppt/test' + str(now) + '.pptx'
        print(expected_path)
        self.assertTrue(os.path.exists(expected_path), "Файл презентации не был сохранен")


if __name__ == '__main__':
    unittest.main()