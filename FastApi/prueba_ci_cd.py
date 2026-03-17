from fastapi import FastAPI #importacion de framework

"""
Creación de la aplicación FastAPI.
La app maneja rutas HTTP y respuestas.
"""
app = FastAPI() #creacion de la app 

@app.get("/")  # definición de ruta: cuando llegue una request GET a "/"
def read_root():  # función que responde la request
    """
    Endpoint raíz de la API.
    Devuelve un mensaje simple en JSON.
    """
    return {"message": "CI/CD funcionando, soy crack"}

#agrego otro endpoint para probar
@app.get("/saludo")
def saludo():
    return {"mensaje": "Hola, este es otro endpoint ;)"}