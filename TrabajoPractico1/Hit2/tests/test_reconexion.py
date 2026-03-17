import threading
import time
import os
#from dotenv import load_dotenv
from ..NodoB import start_server
from ..NodoA import start_client

#load_dotenv()

RETRY_DELAY = 3


def run_server():
    start_server()

def run_client(result_container):
    response = start_client()
    result_container.append(response)

def test_client_server_reconn():

    result = []

    # Levanto primero el cliente en un hilo para obtener el error de server no disponible y hacer reconexion
    client_thread = threading.Thread(target=run_client, args=(result,))
    client_thread.start()

    time.sleep(RETRY_DELAY)

    # creo un hilo, que va a ejecutar la funcion run_server para levantar el servidor.
    server_thread = threading.Thread(target=run_server)  
    server_thread.start()

    # esto bloquea el test hasta que el cliente recibe la respuesta de conexion y finaliza la ejecucion
    client_thread.join()

    assert len(result) > 0
    assert "Mensaje Recibido" in result[0]