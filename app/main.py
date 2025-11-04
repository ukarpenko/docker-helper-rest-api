from fastapi import FastAPI
from routers import containers, scripts

docker_app = FastAPI()

docker_app.include_router(containers.router)
docker_app.include_router(scripts.router)