import socket
import threading
import time
import os
from dotenv import load_dotenv
from ..NodoB import start_server
from ..NodoA import start_client

load_dotenv()

HOST = os.getenv("HOST_SERVER_TCP_TP1")
PORT = int(os.getenv("PORT_SERVER_TCP_TP1"))

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