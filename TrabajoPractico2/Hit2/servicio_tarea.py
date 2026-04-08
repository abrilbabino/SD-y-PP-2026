from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class TaskInput(BaseModel):
    task: str
    params: dict


def ejecutar_tarea(task: str, params: dict):
    if task == "suma":
        return params["a"] + params["b"]
    if task == "multiplicacion":
        return params["a"] * params["b"]
    if task == "potencia":
        return params["a"] ** params["b"]
    return "tarea no soportada"


@app.post("/EjecutarTarea")
def exec_task(data: TaskInput):
    resultado = ejecutar_tarea(data.task, data.params)
    return {"result": resultado}