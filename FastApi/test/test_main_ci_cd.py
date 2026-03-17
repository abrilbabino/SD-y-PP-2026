from fastapi.testclient import TestClient #TestClient permite simular requests HTTP a la API sin levantar un servidor real.
from ..prueba_ci_cd import app 

client = TestClient(app) #aca creamos al cliente 

"""Aquí se crea un cliente que puede enviar requests a la API.
Conceptualmente:
client → simula un navegador o cliente HTTP"""

def test_root():
    response = client.get("/")  #Enviar una request GET
    assert response.status_code == 200  #Verificar el código HTTP
    assert response.json() == {"message": "CI/CD funcionando, soy crack"}

def test_saludo():
    response = client.get("/saludo")
    assert response.status_code == 200
    assert response.json() == {"mensaje": "Hola, este es otro endpoint ;)"}