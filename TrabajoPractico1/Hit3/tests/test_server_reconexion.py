import threading
import time
import os
from dotenv import load_dotenv
from TrabajoPractico1.Hit3.NodoB import start_server
from TrabajoPractico1.Hit3.NodoA import start_client

load_dotenv()

RETRY_DELAY = int(os.getenv("RETRY_DELAY"))

def run_server(stop_event):
    start_server(stop_event)

def run_client(result_container):
    response = start_client()
    result_container.append(response)

def test_server_survives_client_disconnect():
    result = []

    stop_event = threading.Event()

    # Levanto el servidor en un hilo
    server_thread = threading.Thread(
        target=run_server,
        args=(stop_event,),
        daemon=True)
    server_thread.start()

    time.sleep(1)  # espero que el servidor arranque

    # Primer cliente
    client1_result = []
    client1_thread = threading.Thread(target=run_client, args=(client1_result,))
    client1_thread.start()
    client1_thread.join()

    assert len(client1_result) > 0
    assert "Mensaje Recibido" in client1_result[0]

    # Simulo que el cliente se desconecta (el hilo termina)
    print("Cliente 1 desconectado.")

    time.sleep(1)  # espero un poco

    # Segundo cliente
    client2_result = []
    client2_thread = threading.Thread(target=run_client, args=(client2_result,))
    client2_thread.start()
    client2_thread.join()

    assert len(client2_result) > 0
    assert "Mensaje Recibido" in client2_result[0]

    print("Servidor respondió correctamente a ambos clientes.")

    # detengo el servidor
    stop_event.set()
    server_thread.join(timeout=2)

    
