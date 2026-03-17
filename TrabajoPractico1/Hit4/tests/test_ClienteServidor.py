import threading
import time
import os
from ..NodoC import start_server, start_client

HOST1 = "127.0.0.1"
PORT1 = 5000
HOST2 = "127.0.0.1"
PORT2 = 8888
RETRY_DELAY = 3


def run_client(target_host, target_port, result_container):
    response = start_client(target_host, target_port)
    result_container.append(response)


def test_ClienteServidor():
    responses_nodo1 = []
    responses_nodo2 = []

    # Levanto los servidores
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

    time.sleep(1)  # espero que el servidor arranque

    # levanto los clientes, client1 contra server2 y client2 contra server1
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

    # espero que termine el cliente1 y el cliente2
    client1_thread.join(timeout=5)
    client2_thread.join(timeout=5)

    time.sleep(RETRY_DELAY)

    assert len(responses_nodo1) > 0
    assert len(responses_nodo2) > 0
    assert "Mensaje Recibido" in responses_nodo1[0]
    assert "Mensaje Recibido" in responses_nodo2[0]

   