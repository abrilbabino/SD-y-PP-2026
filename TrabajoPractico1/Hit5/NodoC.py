import socket
import threading
import os
import time
import json
from dotenv import load_dotenv

# cargo las variables del .env
load_dotenv()

RETRY_DELAY = int(os.getenv("RETRY_DELAY"))


def handle_conn(conn, addr):

    print(f"[SERVER] Conectado con {addr}")

    try:
       
        while True:

            data = conn.recv(1024)

            if not data:
                break

            # deserializo el mensaje con formato json para obtener un diccionario.
            msg = json.loads(data.decode())

            print("[SERVER] Mensaje Recibido: " + msg["msg"])

            response = {
                "type"  : "msgRecibido",
                "msg"   : "Mensaje Recibido",  
            }

            # serializo la respuesta
            response_json = json.dumps(response)

            conn.sendall(response_json.encode())

    finally:
        conn.close()
        print(f"[SERVER] Conexion cerrada con {addr}")


def start_server(host, port):
    # Creo el socket con el tipo de direccionamiento ipv4 (AF_INET) y el tipo de protocolo (SOCK_TREAM para TCP)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Esto permite reutilizar el puerto para que el SO no lo ponga en time wait al ejecutar varias pruebas seguidas
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # hago que el servicio escuche en la direccion y puerto indicado y lo pongo en listening
    server.bind((host, port))
    server.listen()

    print(f"Server Listening on {host}:{port} ...")

  # Loop infinito para aceptar múltiples conexiones
    while True:
        conn, addr = server.accept()
        
        # creo el hilo del server con los datos del socket
        server_thread = threading.Thread(
            target=handle_conn,
            args=(conn,addr),
            daemon=True
        )

        server_thread.start()


def start_client(target_host, target_port):

    # meto la conexion del cliente en un loop infinito
    while True:

        # Intenta conectarse al servidor y si no puede se queda reintentando
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((target_host, target_port))
            print("[CLIENT] Conectado al servidor")
            msg = {
                "type": "ClienteConectado",
                "msg": "[CLIENTE] Me conecte",
            }
            # serializo msg para convertirlo en json
            msg_json = json.dumps(msg)

            client.sendall(msg_json.encode())

            while True:

                response_json = client.recv(1024).decode()

                if not response_json:
                    continue

                response = json.loads(response_json)
                client.close()

                return response["msg"]
        except ConnectionRefusedError:

            print("[CLIENT] Servidor no disponible, reintentando en {RETRY_DELAY} segundos...")
            time.sleep(RETRY_DELAY)

if __name__ == "__main__":
    import sys

    my_port = int(sys.argv[1])
    peer_port = int(sys.argv[2])

    HOST = "127.0.0.1"

    #Thread del servidor (escucha conexiones entrantes)
    thread_server = threading.Thread(
        target=start_server,
        args=(HOST, my_port),
        daemon=True
    )
    thread_server.start()

    # Espera para asegurar que el server levante
    time.sleep(1)

    #Thread del cliente (intenta conectarse al otro nodo continuamente)
    thread_client = threading.Thread(
        target=start_client,
        args=(HOST, peer_port),
        daemon=True
    )
    thread_client.start()

    print(f"[NODE {my_port}] Nodo iniciado. Escuchando en {my_port} y conectando a {peer_port}")

    # Mantiene vivo el proceso principal
    while True:
        time.sleep(1)
        
