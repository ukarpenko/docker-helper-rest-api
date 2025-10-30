import os
import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yaml

# Загрузите конфигурацию из YAML файла
with open("settings.yaml", 'r') as f:
    config = yaml.safe_load(f)

# Получите данные из конфигурации
MINIO_ENDPOINT = config['MINIO_ENDPOINT']
MINIO_ACCESS_KEY = config['MINIO_ACCESS_KEY']
MINIO_SECRET_KEY = config['MINIO_SECRET_KEY']
S3_BUCKET = config['S3_BUCKET']
MINIO_ALIAS = config['MINIO_ALIAS']

# Регистрация alias MinIO с помощью клиента mc
def register_minio_alias():
    subprocess.run(
        [
            "mc", "alias", "set", MINIO_ALIAS, MINIO_ENDPOINT,
            MINIO_ACCESS_KEY, MINIO_SECRET_KEY
        ],
        check=True
    )

# Модель данных для API
class ScriptRequest(BaseModel):
    script_name: str  # Имя скрипта, который нужно скачать

app = FastAPI()

@app.on_event("startup")
async def startup():
    # Регистрируем MinIO alias при старте приложения
    try:
        register_minio_alias()
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Failed to register MinIO alias: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "MinIO download service is running!"}

@app.post("/download_script/")
def download_script(request: ScriptRequest):
    script_name = request.script_name

    # Путь, куда будем сохранять файл
    local_script_path = f"/tmp/{script_name}"

    # Скачиваем файл с MinIO
    try:
        subprocess.run(
            [
                "mc", "cp", f"{MINIO_ALIAS}/{S3_BUCKET}/{script_name}", local_script_path
            ],
            check=True
        )
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail=f"Failed to download script {script_name} from MinIO.")

    # Проверка, что файл был скачан
    if not os.path.exists(local_script_path):
        raise HTTPException(status_code=404, detail=f"Script {script_name} not found in MinIO.")

    return {"status": "success", "script_path": local_script_path}
