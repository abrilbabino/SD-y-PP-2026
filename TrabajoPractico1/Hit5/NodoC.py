import socket
import threading
import os
import time
import json

RETRY_DELAY = 3



def handle_conn(conn, addr):
    print(f"[SERVER] Conectado con {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = json.loads(data.decode())
            print(f"[SERVER] Mensaje Recibido: {msg['msg']}")

            response = {
                "type": "msgRecibido",
                "msg": "Mensaje Recibido"
            }
            conn.sendall(json.dumps(response).encode())

    finally:
        conn.close()
        print(f"[SERVER] Conexion cerrada con {addr}")


def start_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((host, port))
    server.listen()

    print(f"Server Listening on {host}:{port} ...")

    while True:
        conn, addr = server.accept()

        thread = threading.Thread(
            target=handle_conn,
            args=(conn, addr),
            daemon=True
        )
        thread.start()


def start_client(target_host, target_port):

    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((target_host, target_port))
            print("[CLIENT] Conectado al servidor")

            msg = {
                "type": "ClienteConectado",
                "msg": "Me conecte"
            }

            client.sendall(json.dumps(msg).encode())

            response_json = client.recv(1024).decode()

            response = json.loads(response_json)

            client.close()

            return response["msg"]

        except ConnectionRefusedError:
            print(f"[CLIENT] Servidor no disponible, reintentando en {RETRY_DELAY} segundos...")
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

    # Pequeña espera para asegurar que el server levante
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
