import os
from minio import Minio
from minio.error import S3Error
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yaml

# Загрузка конфигурации из YAML файла
with open("settings.yaml", 'r') as f:
    config = yaml.safe_load(f)

# Получение данных из конфигурации
MINIO_ENDPOINT = config['MINIO_ENDPOINT']
MINIO_ACCESS_KEY = config['MINIO_ACCESS_KEY']
MINIO_SECRET_KEY = config['MINIO_SECRET_KEY']
S3_BUCKET = config['S3_BUCKET']
MINIO_ALIAS = config['MINIO_ALIAS']

# Создаем клиент MinIO
minio_client = Minio(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  
)

# Модель данных для API
class ScriptRequest(BaseModel):
    script_name: str  # Имя скрипта, который нужно скачать

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "MinIO download service is running!"}

@app.post("/download_script/")
def download_script(request: ScriptRequest):
    script_name = request.script_name

    # Путь, куда будем сохранять файл
    local_script_path = f"/tmp/{script_name}"

    # Проверяем, существует ли файл на MinIO
    try:
        # Проверяем наличие объекта в бакете
        minio_client.stat_object(S3_BUCKET, script_name)
    except S3Error as e:
        raise HTTPException(status_code=404, detail=f"Script {script_name} not found in MinIO: {str(e)}")

    # Скачиваем файл с MinIO
    try:
        minio_client.fget_object(S3_BUCKET, script_name, local_script_path)
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"Failed to download script {script_name} from MinIO: {str(e)}")

    # Проверка, что файл был скачан
    if not os.path.exists(local_script_path):
        raise HTTPException(status_code=404, detail=f"Script {script_name} not found in the local storage.")

    return {"status": "success", "script_path": local_script_path}