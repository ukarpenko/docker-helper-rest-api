from fastapi import FastAPI, HTTPException
import docker
import os
import subprocess

docker_app = FastAPI()

client = docker.from_env()

@docker_app.get("/")
def read_mess():
    return {"message": "You first simple FastAPI alive!"}

#ручка для получения id контейнеров на хосте
@docker_app.get("/containers")
def get_cont_ids():
    containers = client.containers.list(all=True)

    #обработчик пустого списка контейнеров
    if not containers:
        raise HTTPException(status_code=404, detail = "Oops! No containers on host.")
  
    #формирование списка контейнеров
    result = []
    for container in containers:
        result.append({
            "container id": container.id,
            "container name": container.name,
            "container status": container.status
        })

    return result

#ручка для получения id up контейнеров на хосте
@docker_app.get("/containers/up")
def get_cont_ids():
    containers = client.containers.list(filters={"status": "running"})

    #обработчик пустого списка alive контейнеров
    if not containers:
        raise HTTPException(status_code=404, detail = "Oops! No alive containers on host.")

    #формирование списка контейнеров
    result = []
    for container in containers:
        result.append({
            "container id": container.id,
            "container name": container.name,
            "container status": container.status
        })

    return result

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




