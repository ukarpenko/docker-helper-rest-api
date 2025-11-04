from pydantic import BaseModel
from typing import List

class MinioScriptExecutionRequest(BaseModel):
    minio_container_name: str
    target_container_name: str
    script_name: str

class LocalScriptExecutionRequest(BaseModel):
    container_names: List[str]
    script_path: str