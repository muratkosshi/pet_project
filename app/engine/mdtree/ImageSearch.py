import json
from urllib.parse import urlparse
import hashlib
import os
import random
import requests
from PIL import Image


class ImageSearch:
    theme_title: str = None
    title: str = None
    temp_folder_path: str = None
    image_path: str = None

    def __init__(self, title, theme_title, temp_folder_path, generate, prompt, own_domain):
        self.title = title
        self.theme_title = theme_title
        self.temp_folder_path = temp_folder_path
        self.subscription_key = '74f0e315d21b4d27bf2503a120bb8618'  # Укажите ваш ключ Azure
        self.endpoint = 'https://api.bing.microsoft.com/v7.0/images/search'  # Убедитесь, что здесь только один слэш
        self.image_path = self.find_and_download_image(title, theme_title, temp_folder_path)

        if self.image_path:  # Проверяем наличие загруженного изображения
            self.resize_image(self.image_path)

    def shorten_filename(self, filename, max_length=250):
        base_name, extension = os.path.splitext(filename)
        if len(filename) > max_length:
            hash_name = hashlib.md5(base_name.encode()).hexdigest()
            filename = f"{hash_name[:max_length - len(extension)]}{extension}"
        return filename

    def convert_image_if_needed(self, image_path):
        base, ext = os.path.splitext(image_path)
        if ext.lower() == '.webp':
            img = Image.open(image_path).convert('RGB')
            new_image_path = base + '.jpeg'
            img.save(new_image_path, 'jpeg')
            os.remove(image_path)
            return new_image_path
        return image_path

    def resize_image(self, image_path, max_size=(1024, 768)):
        if os.path.isfile(image_path):
            with Image.open(image_path) as img:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(image_path)
        else:
            print(f"Error: {image_path} is not a regular file.")

    def find_and_download_image(self, title, theme_title, temp_folder_path):
        print('ПОИСК:', title)

        if not self.subscription_key or not self.endpoint:
            print("Azure ключ или endpoint не указаны.")
            return None

        # Параметры запроса
        params = {
            'q': theme_title,  # Запрос на тему
            'mkt': 'en-US',  # Регион
            'count': 20  # Количество результатов
        }
        headers = {
            'Ocp-Apim-Subscription-Key': self.subscription_key
        }

        try:
            # Отправка запроса к Bing Search API с таймаутом
            response = requests.get(self.endpoint, headers=headers, params=params, timeout=10)
            response.raise_for_status()  # Проверяем статус ответа
            results = response.json()

            # Извлекаем список изображений
            images = results.get('value', [])
            if images:
                # Выбираем случайное изображение
                random_image = random.choice(images)
                image_url = random_image.get('contentUrl')  # URL изображения

                if image_url:
                    # Скачивание изображения
                    image_filename = self.shorten_filename(os.path.basename(image_url))
                    image_path = os.path.join(temp_folder_path, image_filename)
                    self.download_image(image_url, image_path)

                    # Преобразование изображения, если нужно
                    converted_image_path = self.convert_image_if_needed(image_path)
                    return converted_image_path
            else:
                print("Не удалось найти изображения.")
                return None

        except requests.exceptions.Timeout:
            print("Ошибка: Превышено время ожидания запроса.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Ошибка во время поиска: {e}")
            return None
    def download_image(self, url, save_path):
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                print(f"Изображение успешно сохранено: {save_path}")
            else:
                print(f"Не удалось скачать изображение: {url}")
        except Exception as e:
            print(f"Ошибка при скачивании изображения: {e}")

    def generate_image(self, prompt, temp_folder_path, own_domain):

        url = f"{own_domain}/v1/generation/text-to-image"  # Замените на ваш URL
        print(url)
        data = {
            "prompt": prompt,
            "negative_prompt": "",
            "style_selections": [
                "Fooocus V2",
                "Fooocus Enhance",
                "Fooocus Sharp"
            ],
            "performance_selection": "Speed",
            "aspect_ratios_selection": "1152*896",
            "image_number": 1,
            "image_seed": -1,
            "sharpness": 2,
            "guidance_scale": 4,
            "base_model_name": "juggernautXL_version6Rundiffusion.safetensors",
            "refiner_model_name": "None",
            "refiner_switch": 0.5,
            "loras": [
                {
                    "model_name": "sd_xl_offset_example-lora_1.0.safetensors",
                    "weight": 0.1
                }
            ],
            "advanced_params": {
                "adaptive_cfg": 7,
                "adm_scaler_end": 0.3,
                "adm_scaler_negative": 0.8,
                "adm_scaler_positive": 1.5,
                "canny_high_threshold": 128,
                "canny_low_threshold": 64,
                "controlnet_softness": 0.25,
                "debugging_cn_preprocessor": False,
                "debugging_inpaint_preprocessor": False,
                "disable_preview": False,
                "freeu_b1": 1.01,
                "freeu_b2": 1.02,
                "freeu_enabled": False,
                "freeu_s1": 0.99,
                "freeu_s2": 0.95,
                "inpaint_disable_initial_latent": False,
                "inpaint_engine": "v1",
                "inpaint_erode_or_dilate": 0,
                "inpaint_respective_field": 1,
                "inpaint_strength": 1,
                "invert_mask_checkbox": False,
                "mixing_image_prompt_and_inpaint": False,
                "mixing_image_prompt_and_vary_upscale": False,
                "overwrite_height": -1,
                "overwrite_step": -1,
                "overwrite_switch": -1,
                "overwrite_upscale_strength": -1,
                "overwrite_vary_strength": -1,
                "overwrite_width": -1,
                "refiner_swap_method": "joint",
                "sampler_name": "dpmpp_2m_sde_gpu",
                "scheduler_name": "karras",
                "skipping_cn_preprocessor": False
            },
            "require_base64": False,
            "async_process": False,
            "webhook_url": ""
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response and response.status_code == 200:
            response_data = response.json()
            if response_data:
                image_url = response_data[0]["url"]
                parsed_url = urlparse(image_url)
                print("parsed_url",parsed_url)
                # Заменяем домен
                own_domain = own_domain.replace("https://", "")
                replaced_url = parsed_url._replace(scheme= "https", netloc=own_domain)
                print("replaced_url", replaced_url)
                new_image_url = replaced_url.geturl()
                image_filename = os.path.basename(new_image_url)
                print("image_filename", image_filename)
                # image_filename = self.shorten_filename(image_filename)  # Сокращаем имя файла
                image_path = os.path.join(temp_folder_path, image_filename)
                print("image_path", image_path)
                with open(image_path, 'wb') as f:
                    print("КАРТИНКА ССЫЛКА: ",new_image_url)
                    f.write(requests.get(new_image_url).content)
                converted_image_path = self.convert_image_if_needed(image_path)
                return converted_image_path
            else:
                return None
        else:
            return None
