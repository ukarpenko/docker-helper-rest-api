import requests
from fastapi import HTTPException
import yaml
import os

# Указываем путь к файлу settings.yaml в подкаталоге config
settings_path = os.path.join("config", "settings.yaml")

# Загрузка конфигурации из YAML файла
with open(settings_path, 'r') as f:
    config = yaml.safe_load(f)

# Извлекаем URL MinIO из загруженной конфигурации
MINIO_SERVICE_URL = config.get('minio_service_url', '')

# Загрузка конфигурации из YAML файла
with open(settings_path, 'r') as f:
    config = yaml.safe_load(f)

# Функция для скачивания скрипта из MinIO-сервиса
def download_script_from_minio(script_name: str):
    payload = {"script_name": script_name}
    
    # Отправляем POST-запрос с телом в формате JSON
    response = requests.post(f"{MINIO_SERVICE_URL}/download_script/", json=payload)
    if response.status_code == 200:
        return response.json()['script_path']
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)
