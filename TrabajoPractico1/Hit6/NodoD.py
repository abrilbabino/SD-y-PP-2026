import time
from fastapi import FastAPI
from pydantic import BaseModel

# creo una app para exponer los endpoint
app = FastAPI()

start_time = time.time()

nodos = []

class Nodo(BaseModel):
    host: str
    port: int

@app.post("/register")
def registrar_nodo(nodo: Nodo):


    newNodo = {
        "host": nodo.host,
        "port": nodo.port,
    }

    # si el nodo no esta registrado lo agrego, evitando duplicaciones
    if newNodo not in nodos:
        nodos.append(newNodo)

    # devuelvo los otros nodos pares
    nodosPares = []
    for n in nodos:
        if n != newNodo:
            nodosPares.append(n)

    return {"nodosPares": nodosPares}

@app.get("/health")
def health():
    uptime = int(time.time() - start_time)

    response = {
        "status": "ok",
        "nodosRegistrados": len(nodos),
        "uptime": uptime,
    }

    return response

