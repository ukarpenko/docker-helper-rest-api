from fastapi import FastAPI, HTTPException
import docker

app = FastAPI()

client = docker.from_env()
#TODO: add exceptions 

#ручка для получения id контейнеров на хосте
@app.get("/containers")
def get_cont_ids():
    containers = client.containers.list(all=True)
    #формирование списка id контейнеров
    container_ids = [container.id for container in containers]
    return {"container_ids": container_ids}