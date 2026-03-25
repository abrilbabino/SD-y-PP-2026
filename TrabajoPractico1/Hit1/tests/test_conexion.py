import threading
import time
from ..NodoB import start_server
from ..NodoA import start_client


def run_server():
    start_server()

def test_client_server_conn():
    # creo un hilo, que va a ejecutar la funcion run_server para levantar el servidor.
    server_thread = threading.Thread(target=run_server)  
    server_thread.daemon = True
    server_thread.start()

    time.sleep(1)

    response = start_client()

    assert "Mensaje Recibido" in response