from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import docker
import requests
import time
import os
import threading
import queue

router3 = APIRouter()

client = docker.from_env()

token = os.environ.get("DOCKER_HUB_TOKEN")
username = os.environ.get("DOCKER_HUB_USERNAME")

if token and username:
    try:
        client.login(username=username, password=token)
        print("Docker Hub login successful")
    except Exception as e:
        print(f"Docker Hub login failed: {e}")
else:
    print("Using local Docker auth")


# MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 4))
MAX_WORKERS = 4

task_queue = queue.Queue()
queue_lock = threading.Lock()

lamport_clock = 0

def increment_clock(received_ts=None):
    global lamport_clock
    with queue_lock:
        if received_ts is not None:
            lamport_clock = max(lamport_clock, received_ts)
        lamport_clock += 1
        return lamport_clock


class TaskRequest(BaseModel):
    image: str
    task: str
    params: dict
    timestamp: int | None = None



def ejecutar_task(task):
    req = task["req"]
    container = None

    try:
        client.images.pull(req.image)

        container = client.containers.run(
            req.image,
            detach=True,
            ports={'5000/tcp': None},
            remove=True
        )

        time.sleep(2)

        port = None
        for _ in range(10):
            container.reload()
            ports = container.attrs['NetworkSettings']['Ports']
            if ports and ports['5000/tcp']:
                port = ports['5000/tcp'][0]['HostPort']
                break
            time.sleep(0.5)

        if not port:
            raise Exception("No se pudo obtener puerto")

        response = requests.post(
            f"http://localhost:{port}/EjecutarTarea",
            json={
                "task": req.task,
                "params": req.params
            },
            timeout=10
        )

        task["result"] = response.json()

    except Exception as e:
        task["result"] = {"error": str(e)}

    finally:
        if container:
            try:
                container.stop()

                print(f"[DONE] TS={task['timestamp']}")
            except:
                pass


def worker_loop(worker_id):
    while True:
        task = task_queue.get()
        print(f"[WORKER {worker_id}] ejecutando TS={task['timestamp']}")
        try:
            ejecutar_task(task)
        except Exception as e:
            print(f"Worker {worker_id} error: {e}")
        finally:
            task_queue.task_done()

def start_workers():
    for i in range(MAX_WORKERS):
        t = threading.Thread(target=worker_loop, args=(i,), daemon=True)
        t.start()

start_workers()


@router3.post("/getRemoteTask2")
def ejecutarTareaRemota(req: TaskRequest):
    print("ENTRO AL HIT 2")
    ts = increment_clock(req.timestamp)

    task = {
        "req": req,
        "timestamp": ts,
        "result": None
    }

    print(f"[ENQUEUE] TS={ts} task={req.task}")
    with queue_lock:
        
        task_queue.put(task)

    # espera bloqueante simple
    while task["result"] is None:
        time.sleep(0.05)

    return {
        "lamport_ts": increment_clock(),
        "result": task["result"]
    }

@router3.get("/test2")
def test():
    return FileResponse("api/static/index2.html")