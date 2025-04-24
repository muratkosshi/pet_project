import os

from app.engine.mdtree import ImageSearch


def test_image_search():
    title = "Введение"
    theme_title = "Фотосинтез картинка"
    temp_folder_path = "temp_images"  # Укажите существующий путь
    image_search = ImageSearch(title, theme_title, temp_folder_path)

    assert image_search.image_path is not None, "ImageSearch не нашел изображение"
    assert os.path.exists(image_search.image_path), "Файл изображения не существует по пути image_path"
    print("Тест успешно пройден!")

test_image_search()
