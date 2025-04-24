# Метод для удаления содержимого папок
import os
import shutil

from apscheduler.schedulers.asyncio import AsyncIOScheduler


def delete_folder_contents(folder_path: str):
    try:
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        print(f'Файл удален: {file_path}')
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        print(f'Папка удалена: {file_path}')
                except Exception as e:
                    print(f'Ошибка при удалении {file_path}: {e}')
            print(f'Содержимое папки {folder_path} успешно удалено.')
        else:
            print(f'Папка {folder_path} не существует.')
    except Exception as e:
        print(f'Ошибка при очистке папки {folder_path}: {e}')


def start_scheduler_delete_folder_contents():
    scheduler = AsyncIOScheduler()

    # Задачи на очистку папок
    scheduler.add_job(
        delete_folder_contents,
        'cron',  # Запуск в определенное время каждый день
        hour=1,  # Указываем время запуска
        minute=0,
        args=['./temp_images']
    )
    scheduler.add_job(
        delete_folder_contents,
        'cron',  # Запуск в определенное время каждый день
        hour=1,  # Указываем время запуска
        minute=0,
        args=['./myppt']
    )


    scheduler.start()
    print("APScheduler запущен. Задачи на очистку папок добавлены.")