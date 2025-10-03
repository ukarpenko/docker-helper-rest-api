# 📌 Managing Script Execution in Docker Containers

## 🎯 Description

This project provides an application with a REST API that allows you to execute custom scripts in any running Docker container **without restarting them**.

The scripts will be executed **inside the container** as a **secondary process**.

Scripts are stored in the **client directory** (**[TODO]**: in the future, store them in S3).

The project is intended to serve as an initial **prototype** for the development of [k8s-helper-rest-api](https://github.com/ukarpenko/k8s-helper-rest-api) and is currently under active development.

### Key Components:

1. **FastAPI**:

   * API handler for receiving requests to run scripts. The API will accept a command to execute a script inside a container.
   * Each request will be mapped to the container where the script should be executed.

2. **Docker Interaction Service**:

   * The `docker exec` command will be used to execute scripts in containers.
   * The example code will use the `docker-py` library, which allows you to execute commands inside a container as if you were using `docker exec` manually.

3. **docker-compose**:

   * Containers will be managed by `docker-compose`, and the commands will be executed within these containers.

### How It Will Work:

* **The API receives a request** to execute a script.
* **The API selects the container** in which the script will be executed (e.g., through the container ID passed in the request).
* **The API executes the `docker exec` command** to run the script inside the container using the `docker-py` library.
* **The API returns the result** of the script execution to the client (including logs or execution errors).

## Future Architecture:

### Architectural Approach:

1. **Using a Container Cluster**:

   * You have several containers (e.g., 3) deployed using `docker-compose`.
   * Containers will run the main processes, while scripts will be executed in these containers concurrently via `docker exec`.

2. **API for Script Execution**:

   * FastAPI will receive requests from the client and then send commands to the containers through `docker exec` to run the scripts.
   * The request will specify in which container the script should be executed.

3. **Script Execution Logic**:

   * When a request to execute a script arrives, the server selects one of the containers and runs the script via the `docker exec` command.
   * The execution result will be returned to the client via the API.

4. **Access to Containers**:

   * Under development


## Future Structure:

```plaintext
docker-helper-rest-api/
│
├── app/                            # Main FastAPI project
│   ├── main.py                     # Main file with FastAPI server
│   ├── models/                     # Data models for reqs & resps
│   │   └── script.py               # Model for a script (e.g., name, content, etc.)
│   ├── services/                   # Logic for interacting with containers and Docker
│   │   └── docker_service.py       # Logic for interacting with containers (docker exec)
│   ├── config/                     # Server and Docker configurations
│   │   └── settings.py             # Settings for Docker and the application
│   └── utils/                      # Utility functions (e.g., validators)
│       └── docker_utils.py         # Helper functions for working with Docker
│
├── docker/                         # Docker files
│   ├── docker-compose.yml          # Docker Compose for cluster
│   └── Dockerfile                  # Dockerfile for the base container
│
├── requirements.txt                # Python deps
└── README.md                       # Project documentation
```
## Test Infrastructure:

- **[DONE]** docker-compose:
  - 3 PostgreSQL (custom image psql-custom) containers **NOT IN CLUSTER** - tag: psql-custom:1.0
  - +python3

## Test scripts

- **[DONE]** bash
- **[DONE]** python


## Dev Toolset:
- **PL**: `Python`
- **Frameworks && libs**: `FastAPI` , `docker-py`
