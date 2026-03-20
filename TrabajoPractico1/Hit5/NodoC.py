import sys
import socket
import threading
import os
import time
import json
from dotenv import load_dotenv
from ..common.logger import log_event

# cargo las variables del .env
load_dotenv()

RETRY_DELAY = int(os.getenv("RETRY_DELAY"))


def handle_conn(conn, addr):

    log_event("INFO", f"[SERVER] Conexion establecida con {addr}")

    try:
       
        while True:

            data = conn.recv(1024)

            if not data:
                log_event("INFO", f"[SERVER] Cliente {addr} desconectado")
                break

            # deserializo el mensaje con formato json para obtener un diccionario.
            msg = json.loads(data.decode())
            log_event("INFO", f"[SERVER] Mensaje recibido de {addr}: {msg}")

            response = {
                "type"  : "msgRecibido",
                "msg"   : "Mensaje Recibido",  
            }

            # serializo la respuesta
            response_json = json.dumps(response)
            conn.sendall(response_json.encode())
            log_event("INFO", f"[SERVER] Respuesta enviada a {addr}: {response}")


    finally:
        conn.close()
        log_event("INFO", f"[SERVER] Conexion cerrada con {addr}")


def start_server(host, port, stop_event):
    # Creo el socket con el tipo de direccionamiento ipv4 (AF_INET) y el tipo de protocolo (SOCK_TREAM para TCP)
    log_event("INFO", f"Servidor iniciando en {host}:{port}")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Esto permite reutilizar el puerto para que el SO no lo ponga en time wait al ejecutar varias pruebas seguidas
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # hago que el servicio escuche en la direccion y puerto indicado y lo pongo en listening
    server.bind((host, port))
    server.listen()

    server.settimeout(1)

    log_event("INFO", f"Server listening on {host}:{port}")

  # Loop infinito para aceptar múltiples conexiones
    while not stop_event.is_set():

        try:
            conn, addr = server.accept()
            log_event("INFO", f"Nueva conexion desde {addr}")
        except socket.timeout:
            continue
        
        # creo el hilo del server con los datos del socket
        server_thread = threading.Thread(
            target=handle_conn,
            args=(conn,addr),
            daemon=True
        )

        server_thread.start()

    server.close()
    log_event("INFO", f"Servidor {host}:{port} cerrado")


def start_client(target_host, target_port):

    log_event("INFO", f"[CLIENT] Iniciando cliente hacia {target_host}:{target_port}")

    # meto la conexion del cliente en un loop infinito
    while True:
        
        # Intenta conectarse al servidor y si no puede se queda reintentando
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            log_event("INFO", "[CLIENT] Intentando conectar...")
            client.connect((target_host, target_port))
            log_event("INFO", "[CLIENT] Conectado al servidor")
            msg = {
                "type": "ClienteConectado",
                "msg": "[CLIENTE] Me conecte",
            }
            # serializo msg para convertirlo en json
            msg_json = json.dumps(msg)
            client.sendall(msg_json.encode())
            log_event("INFO", f"[CLIENT] JSON Enviado: {msg}")


            while True:

                response_json = client.recv(1024).decode()

                if not response_json:
                    client.close()
                    raise ConnectionError("conexion cerrada")

                response = json.loads(response_json)
                log_event("INFO", f"[CLIENT] Respuesta recibida: {response}")

                client.close()
                log_event("INFO", "[CLIENT] Conexion cerrada")


                return response["msg"]
        except ConnectionRefusedError:

            log_event("ERROR", f"[CLIENT] Servidor no disponible, reintentando en {RETRY_DELAY} segundos...")
            time.sleep(RETRY_DELAY)


        
