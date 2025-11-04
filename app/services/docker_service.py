from fastapi import FastAPI, HTTPException, APIRouter
import docker
import requests
from pydantic import BaseModel
import subprocess

# Создаем объект FastAPI
docker_app = FastAPI()

# Создаем объект APIRouter для роутеров
docker_router = APIRouter()

# Подключение к Docker
client = docker.from_env()

MINIO_SERVICE_URL = "http://127.0.0.1:8000"  # URL minio-client

class ScriptExecutionRequest(BaseModel):
    minio_container_name: str
    target_container_name: str
    script_name: str


# Функция для скачивания скрипта из MinIO-сервиса
def download_script_from_minio(script_name: str):
    # Формируем тело запроса с параметром script_name
    payload = {"script_name": script_name}
    
    # Отправляем POST-запрос с телом в формате JSON
    response = requests.post(f"{MINIO_SERVICE_URL}/download_script/", json=payload)
    if response.status_code == 200:
        return response.json()['script_path']
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


# Ручка для получения id контейнеров на хосте
@docker_router.get("/containers")
def get_cont_ids():
    containers = client.containers.list(all=True)

    if not containers:
        raise HTTPException(status_code=404, detail="No containers on host.")
  
    result = []
    for container in containers:
        result.append({
            "container id": container.id,
            "container name": container.name,
            "container status": container.status
        })

    return result


# Ручка для получения id работающих контейнеров на хосте
@docker_router.get("/containers/up")
def get_cont_ids_up():
    containers = client.containers.list(filters={"status": "running"})

    if not containers:
        raise HTTPException(status_code=404, detail="No running containers on host.")

    result = []
    for container in containers:
        result.append({
            "container id": container.id,
            "container name": container.name,
            "container status": container.status
        })

    return result


# Ручка для выполнения скрипта в контейнере
@docker_router.post("/containers/s3/exec_script/")
async def download_and_exec_script(request: ScriptExecutionRequest):
    minio_container_name = request.minio_container_name
    target_container_name = request.target_container_name
    script_name = request.script_name

    try:
        minio_container = client.containers.get(minio_container_name)
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"MinIO client container '{minio_container_name}' not found.")

    # Проверяем, что контейнер с MinIO-клиентом в статусе 'running'
    if minio_container.status != 'running':
        raise HTTPException(status_code=400, detail="MinIO client container is not running.")

    try:
        script_path_in_minio_container = download_script_from_minio(script_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while downloading script from MinIO: {str(e)}")

    # Получаем TAR-архив с файлами из minio-контейнера
    try:
        stream, stat = client.api.get_archive(minio_container.id, script_path_in_minio_container)
        tar_bytes = b"".join(chunk for chunk in stream)

        # Пишем архив в целевой контейнер в директорию /tmp
        success = client.api.put_archive(target_container_name, "/tmp", tar_bytes)
        if not success:
            raise HTTPException(status_code=500, detail="put_archive returned False")

    except docker.errors.APIError as e:
        raise HTTPException(status_code=500, detail=f"Docker API error during archive transfer: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to transfer file between containers: {str(e)}")

    # Даем права на выполнение и запускаем скрипт в целевом контейнере
    try:
        target_container = client.containers.get(target_container_name)
        target_container.exec_run(f"chmod +x /tmp/{script_name}", user="root")

        exec_result = target_container.exec_run(f"/tmp/{script_name}", tty=True)
        output = exec_result.output.decode("utf-8", errors="replace") if exec_result.output else ""

        return {"status": "success", "output": output}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while executing script in target container: {str(e)}")


# Включаем роутер в основное приложение
docker_app.include_router(docker_router)


# Ручка для копирования скрипта в контейнер и его выполнения
@docker_app.post("/containers/{container_name}/exec_script/")
def exec_script_in_container(container_name: str, script_path: str):
    container = client.containers.get(container_name)

    # Проверяем, что контейнер в статусе 'running'
    if container.status != 'running':
        raise HTTPException(status_code=400, detail="Container is not running.")

    # Проверяем, существует ли указанный скрипт на хосте
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail=f"Script at {script_path} does not exist on host.")

    # Копируем скрипт в контейнер
    try:
        script_name = os.path.basename(script_path)
        copy_command = ["docker", "cp", script_path, f"{container_name}:/tmp/{script_name}"]
        subprocess.run(copy_command, check=True)

        # Даем права на выполнение скрипта
        container.exec_run('chmod +x /tmp/' + os.path.basename(script_path))

        # Запускаем скрипт в контейнере
        exec_result = container.exec_run(f'/tmp/{os.path.basename(script_path)}', tty=True)
        
        return {"status": "success", "output": exec_result.output.decode("utf-8")}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while executing the script: {str(e)}")




