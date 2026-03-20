import threading
import time
import os
from dotenv import load_dotenv
from ..NodoC import start_server, start_client

load_dotenv()

HOST1, PORT1 = os.getenv("SERVER_1_ADDR_TP1").split(":")
PORT1 = int(PORT1)
HOST2, PORT2 = os.getenv("SERVER_2_ADDR_TP1").split(":")
PORT2 = int(PORT2)
RETRY_DELAY = int(os.getenv("RETRY_DELAY"))

def run_client(target_host, target_port, result_container):
    response = start_client(target_host, target_port)
    result_container.append(response)

def test_ClienteServidor_gRPC():
    responses_nodo1 = []
    responses_nodo2 = []

    stop_event1 = threading.Event()
    stop_event2 = threading.Event()

    # Levanto los servidores gRPC
    server1_thread = threading.Thread(
        target=start_server,
        args=(HOST1, PORT1),
        daemon=True
    )
    server2_thread = threading.Thread(
        target=start_server,
        args=(HOST2, PORT2),
        daemon=True
    )

    server1_thread.start()
    server2_thread.start()

    time.sleep(1)  # espero que los servidores arranquen

    # Levanto los clientes: client1 contra server2 y client2 contra server1
    client1_thread = threading.Thread(
        target=run_client,
        args=(HOST2, PORT2, responses_nodo1),
        daemon=True
    )
    client2_thread = threading.Thread(
        target=run_client,
        args=(HOST1, PORT1, responses_nodo2),
        daemon=True
    )

    client1_thread.start()
    client2_thread.start()

    # espero que terminen los clientes
    client1_thread.join()
    client2_thread.join()

    time.sleep(RETRY_DELAY)

    # verifico que ambos recibieron la respuesta esperada
    assert len(responses_nodo1) > 0
    assert len(responses_nodo2) > 0
    assert "Mensaje Recibido" in responses_nodo1[0]
    assert "Mensaje Recibido" in responses_nodo2[0]

    # en gRPC se quedan bloqueados en wait_for_termination,por lo que en este test simplemente dejamos los threads como daemon)