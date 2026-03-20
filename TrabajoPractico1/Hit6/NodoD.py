import time
from fastapi import APIRouter
from pydantic import BaseModel

# creo una app para exponer los endpoint
router1 = APIRouter()

start_time = time.time()

nodos = []

class Nodo(BaseModel):
    host: str
    port: int

@router.post("/Hit6/register")
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

@router.get("/Hit6/health")
def health():
    uptime = int(time.time() - start_time)

    response = {
        "status": "ok",
        "nodosRegistrados": len(nodos),
        "uptime": uptime,
    }

    return response

