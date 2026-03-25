import time
import json
import threading
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

ARCHIVO = "inscripciones.json"

start_time = time.time()

nodos_actuales = []
nodos_futuros = []

lock = threading.Lock()


class Nodo(BaseModel):
    host: str
    port: int


# -------------------------------
# Persistencia
# -------------------------------
def guardar_estado():
    data = {
        "timestamp": int(time.time()),
        "actuales": nodos_actuales,
        "futuros": nodos_futuros
    }
    with open(ARCHIVO, "w") as f:
        json.dump(data, f, indent=4)


# -------------------------------
# Ventana de tiempo (cada 60s)
# -------------------------------
def scheduler():
    global nodos_actuales, nodos_futuros

    while True:
        ahora = int(time.time())
        sleep_time = 60 - (ahora % 60)
        time.sleep(sleep_time)

        with lock:
            print("[D] Cambio de ventana")

            nodos_actuales = nodos_futuros
            nodos_futuros = []

            guardar_estado()


# -------------------------------
# Registro
# -------------------------------
@app.post("/register")
def registrar_nodo(nodo: Nodo):

    newNodo = {
        "host": nodo.host,
        "port": nodo.port,
    }

    with lock:
        if newNodo not in nodos_futuros:
            nodos_futuros.append(newNodo)

        guardar_estado()
        
        # SOLO devuelve los actuales
        return {"nodosPares": nodos_actuales}


# -------------------------------
# Health
# -------------------------------
@app.get("/health")
def health():
    uptime = int(time.time() - start_time)

    return {
        "status": "ok",
        "nodosActuales": len(nodos_actuales),
        "nodosFuturos": len(nodos_futuros),
        "uptime": uptime,
    }


# -------------------------------
# Inicio del scheduler
# -------------------------------
threading.Thread(target=scheduler, daemon=True).start()