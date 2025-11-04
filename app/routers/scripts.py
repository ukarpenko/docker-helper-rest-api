# routers/scripts.py
from fastapi import APIRouter, HTTPException
import subprocess
import os
import docker
from models.script import MinioScriptExecutionRequest, LocalScriptExecutionRequest
from utils.utils import download_script_from_minio

# Подключение к Docker
client = docker.from_env()

# Инициализация роутера для скриптов
router = APIRouter()

# Ручка для скачивания и выполнения скрипта из MinIO
@router.post("/containers/s3/exec_script/")
async def download_and_exec_script(request: MinioScriptExecutionRequest):
    minio_container_name = request.minio_container_name
    target_container_name = request.target_container_name
    script_name = request.script_name

    try:
        minio_container = client.containers.get(minio_container_name)
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail=f"MinIO client container '{minio_container_name}' not found.")

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


# Ручка для выполнения локального скрипта в нескольких контейнерах
@router.post("/containers/exec_script/")
def exec_script_in_container(request: LocalScriptExecutionRequest):
    container_names = request.container_names
    script_path = request.script_path
    results = []

    # Проверка существования скрипта на хосте
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail=f"Script at {script_path} does not exist on host.")

    # Для каждого контейнера из списка
    for container_name in container_names:
        try:
            container = client.containers.get(container_name)

            # Проверяем, что контейнер в статусе 'running'
            if container.status != 'running':
                results.append({
                    "container": container_name,
                    "status": "failed",
                    "detail": "Container is not running."
                })
                continue  # Переходим к следующему контейнеру

            # Копируем скрипт в контейнер
            script_name = os.path.basename(script_path)
            copy_command = ["docker", "cp", script_path, f"{container_name}:/tmp/{script_name}"]
            subprocess.run(copy_command, check=True)

            # Даем права на выполнение скрипта
            container.exec_run(f'chmod +x /tmp/{script_name}')

            # Запускаем скрипт в контейнере
            exec_result = container.exec_run(f'/tmp/{script_name}', tty=True)

            results.append({
                "container": container_name,
                "status": "success",
                "output": exec_result.output.decode("utf-8")
            })

        except Exception as e:
            results.append({
                "container": container_name,
                "status": "failed",
                "detail": str(e)
            })
    
    return {"results": results}
