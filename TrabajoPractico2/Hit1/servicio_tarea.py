from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# defino el modelo de datos para el request que se espera recibir en el endpoint /execute. Este modelo tiene dos campos:
# task, que es una cadena que indica la tarea a ejecutar, y params, que es un diccionario con los parámetros necesarios para ejecutar la tarea.
class TaskInput(BaseModel):
    task: str
    params: dict


# esta función es la que realmente ejecuta la tarea solicitada. Recibe el nombre de la tarea y los parámetros, y dependiendo del valor de task, 
# realiza la operación correspondiente.
def ejecutarTarea(task: str, params: dict):
    if task == "suma":
        return params["a"] + params["b"]

    if task == "multiplicacion":
        
        return params["a"] * params["b"]

    if task == "potencia":
        return params["a"] ** params["b"]

    return "tarea no soportada"

# este es el endpoint que se expone para ejecutar tareas. 
@app.post("/EjecutarTarea")
def exec(data: TaskInput):
    # dependiendo de la tarea solicitada, se llama a la función ejecutarTarea con los parámetros dados, y se devuelve el resultado en un diccionario.
    resultado = ejecutarTarea(data.task, data.params)
    return {"result": resultado}