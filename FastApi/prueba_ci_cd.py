from fastapi import FastAPI #importacion de framework


"""
Creación de la aplicación FastAPI.
La app maneja rutas HTTP y respuestas.
"""
app = FastAPI(title="SD-y-PP-GRUPO-NAJ API", version="1.0.0") #creacion de la app 

@app.get("/")  # definición de ruta: cuando llegue una request GET a "/"
def read_root():  # función que responde la request
    """
    Endpoint raíz de la API.
    Devuelve un mensaje simple en JSON.
    """
    return {"mensaje": " La API grupo NAJ esta funcionando correctamente "}

#agrego otro endpoint para probar
@app.get("/saludo")
def saludo():
    return {"mensaje": " Hola, Bienvenido a la API del GRUPO NAJ :) "}
