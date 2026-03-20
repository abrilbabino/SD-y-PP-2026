import sys
import socket
import threading
import os
import time
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

            msg = data.decode()

            print(f"[SERVER] Mensaje Recibido: {msg}")

            response = "Mensaje Recibido"
            conn.sendall(response.encode())

    finally:
        conn.close()
        print(f"[SERVER] Conexion cerrada con {addr}")


def start_server(host, port, stop_event):
    # Creo el socket con el tipo de direccionamiento ipv4 (AF_INET) y el tipo de protocolo (SOCK_TREAM para TCP)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Esto permite reutilizar el puerto para que el SO no lo ponga en time wait al ejecutar varias pruebas seguidas
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # hago que el servicio escuche en la direccion y puerto indicado y lo pongo en listening
    server.bind((host, port))
    server.listen()

    server.settimeout(1)

    print(f"Server Listening on {host}:{port} ...")

  # Loop infinito para aceptar múltiples conexiones
    while not stop_event.is_set():
        try:
            conn, addr = server.accept()
        except socket.timeout:
            continue

        # creo el hilo del server con los datos del socket
        threading.Thread(
            target=handle_conn,
            args=(conn,addr),
            daemon=True
        ).start()

    server.close()
    print(f"Server {host}:{port} cerrado")


def start_client(target_host, target_port):

    # meto la conexion del cliente en un loop infinito
    while True:

        # Intenta conectarse al servidor y si no puede se queda reintentando
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((target_host, target_port))
            print("[CLIENT] Conectado al servidor")
            msg = "Me conecte"
            client.sendall(msg.encode())

            response = client.recv(1024).decode()
            client.close()

            return response
        
        except ConnectionRefusedError:

            print("[CLIENT] Servidor no disponible, reintentando en {RETRY_DELAY} segundos...")
            time.sleep(RETRY_DELAY)

if __name__ == "__main__":
    my_port = int(sys.argv[1])
    peer_port = int(sys.argv[2])

    HOST = "127.0.0.1"

    #Thread del servidor (escucha conexiones entrantes)
    stop_event = threading.Event()
    thread_server = threading.Thread(
        target=start_server,
        args=(HOST, my_port, stop_event),
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
