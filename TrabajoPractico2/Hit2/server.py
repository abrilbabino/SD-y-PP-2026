from fastapi import APIRouter, HTTPException, FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import docker
import requests
import time
import os
import threading
import heapq
import uuid


router2 = APIRouter()
client = docker.from_env()

app = FastAPI()
app.include_router(router2)

# ================================
# CONFIG
# ================================
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))

# ================================
# LAMPORT
# ================================
lamport_clock = 0
clock_lock = threading.Lock()

def update_lamport(received_ts):
    global lamport_clock
    with clock_lock:
        lamport_clock = max(lamport_clock, received_ts) + 1
        return lamport_clock

# ================================
# COLA DE TAREAS (PRIORIDAD)
# ================================
task_queue = []
queue_lock = threading.Lock()
queue_condition = threading.Condition(queue_lock)

sequence = 0
seq_lock = threading.Lock()

def next_seq():
    global sequence
    with seq_lock:
        sequence += 1
        return sequence

# ================================
# RESULTADOS
# ================================
results = {}
results_lock = threading.Lock()

# ================================
# MODELO
# ================================
class TaskRequest(BaseModel):
    image: str
    task: str
    params: dict
    lamport_ts: int = 0

# ================================
# EJECUCION EN CONTENEDOR
# ================================
def ejecutar_en_contenedor(req: TaskRequest):
    container = None
    try:
        # asegurar imagen
        try:
            client.images.get(req.image)
        except:
            client.images.pull(req.image)

        container = client.containers.run(
            req.image,
            detach=True,
            ports={'5000/tcp': None},
            remove=True
        )

        # buscar puerto
        port = None
        for _ in range(20):
            container.reload()
            ports = container.attrs['NetworkSettings']['Ports']
            if ports and ports['5000/tcp']:
                port = ports['5000/tcp'][0]['HostPort']
                break
            time.sleep(0.2)

        if not port:
            raise Exception("No hay puerto")

        # llamar al servicio tarea
        response = requests.post(
            f"http://localhost:{port}/EjecutarTarea",
            json={
                "task": req.task,
                "params": req.params
            },
            timeout=10
        )

        return response.json()

    finally:
        if container:
            try:
                container.stop()
            except:
                pass

# ================================
# WORKER
# ================================
def worker(worker_id):
    while True:
        with queue_condition:
            while not task_queue:
                queue_condition.wait()

            _, _, job_id = heapq.heappop(task_queue)

        with results_lock:
            job = results[job_id]
            job["status"] = "running"
            job["worker"] = worker_id

        try:
            req = TaskRequest(**job["req"])
            result = ejecutar_en_contenedor(req)

            with results_lock:
                job["status"] = "done"
                job["result"] = result

        except Exception as e:
            with results_lock:
                job["status"] = "error"
                job["error"] = str(e)

        finally:
            job["event"].set()

# ================================
# INICIAR WORKERS
# ================================
def start_workers():
    for i in range(MAX_WORKERS):
        t = threading.Thread(target=worker, args=(i+1,), daemon=True)
        t.start()

start_workers()

# ================================
# ENDPOINT PRINCIPAL
# ================================
@router2.post("/getRemoteTask")
def ejecutarTareaRemota(req: TaskRequest):

    # actualizar Lamport
    ts = update_lamport(req.lamport_ts)

    # crear job
    job_id = str(uuid.uuid4())

    event = threading.Event()

    with results_lock:
        results[job_id] = {
            "status": "queued",
            "req": req.dict(),
            "result": None,
            "error": None,
            "event": event
        }

    # encolar tarea
    seq = next_seq()
    with queue_condition:
        heapq.heappush(task_queue, (ts, seq, job_id))
        queue_condition.notify()

    # esperar resultado
    event.wait(timeout=30)

    with results_lock:
        job = results[job_id]

    if job["status"] == "error":
        raise HTTPException(status_code=500, detail=job["error"])

    return {
        "job_id": job_id,
        "status": job["status"],
        "result": job["result"]
    }

# ================================
# STATUS
# ================================
@router2.get("/status")
def status():
    with results_lock:
        total = len(results)
        done = sum(1 for j in results.values() if j["status"] == "done")
        running = sum(1 for j in results.values() if j["status"] == "running")
        queued = sum(1 for j in results.values() if j["status"] == "queued")

    return {
        "total": total,
        "done": done,
        "running": running,
        "queued": queued
    }

@router2.get("/test")
def test():
    return FileResponse("api/static/index.html")