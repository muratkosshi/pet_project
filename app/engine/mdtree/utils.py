import random
bg_base_path = "./pptx_static/static/bg"


def get_random_theme():
    root_path = bg_base_path
    folders = [folder for folder in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, folder))]

    random_folder = random.choice(folders)

    random_folder_path = os.path.join(root_path, random_folder)
    return random_folder_path


import os

def get_themes_with_images():
    root_path = bg_base_path
    themes = []

    # Получение всех папок в корневом каталоге
    folders = [folder for folder in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, folder))]

    for folder in folders:
        folder_path = os.path.join(root_path, folder)
        # Получение списка файлов в папке
        files = os.listdir(folder_path)
        # Фильтрация списка файлов, чтобы оставить только картинки
        images = [file for file in files if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
        # Если в папке есть картинки, добавляем информацию в список
        if images:
            # Получаем абсолютный путь к изображению
            image_path = os.path.join(folder_path, images[0])
            # Разбиваем путь на части
            path_parts = image_path.split(os.path.sep)
            # Удаляем точки из всех частей, кроме последней (расширение файла)
            cleaned_parts = [part.replace('.', '') for part in path_parts[:-1]] + [path_parts[-1]]
            # Собираем путь обратно
            cleaned_image_path = os.path.sep.join(cleaned_parts)
            themes.append({
                "theme": folder,
                "image_path": cleaned_image_path
            })

    return themes



def read_md_file(file_path, encoding='utf-8'):
    with open(file_path, 'r', encoding=encoding) as file:
        content = file.read()
    return content


def get_random_file(path):
    folder_path = path

    files = os.listdir(folder_path)

    random_file = random.choice(files)

    random_file_path = os.path.join(folder_path, random_file)
    return random_file_path