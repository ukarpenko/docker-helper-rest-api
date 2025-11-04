from fastapi import APIRouter, HTTPException
import docker

# Подключение к Docker
client = docker.from_env()

# Инициализация роутера
router = APIRouter()

# Ручка для получения id контейнеров на хосте
@router.get("/containers")
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
@router.get("/containers/up")
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
