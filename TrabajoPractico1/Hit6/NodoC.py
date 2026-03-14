import socket
import threading
import os
import time
import json

from dotenv import load_dotenv

# cargo las variables del .env
load_dotenv()

RETRY_DELAY = int(os.getenv("RETRY_DELAY"))

# Variable global donde se guardará el puerto en el que queda escuchando
# el servidor del nodo C. para que luego el cliente la use para registrarse en el nodo D.
PUERTO_SERVER = None

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


def start_server(host):
    global PUERTO_SERVER
    # Creo el socket con el tipo de direccionamiento ipv4 (AF_INET) y el tipo de protocolo (SOCK_TREAM para TCP)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Esto permite reutilizar el puerto para que el SO no lo ponga en time wait al ejecutar varias pruebas seguidas
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # hago que el servicio escuche en la direccion y puerto indicado y lo pongo en listening
    server.bind((host, 0))
    server.listen()

    PUERTO_SERVER = server.getsockname()[1]

    print(f"Server Listening on {host}:{PUERTO_SERVER} ...")

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

def saludarNodos(nodos):
    for nodo in nodos:

        try:
            ip = nodo["ip"]
            puerto = nodo["puerto"]

            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((ip, puerto))

            msg = {
                "type": "saludo",
                "msg": "hola desde otro nodo C"
            }

            client.sendall(json.dumps(msg).encode())

            respuesta = client.recv(1024)

            print("[NODO C] respuesta:", json.loads(respuesta.decode()))

            client.close()

        except:
            print("[NODO C] no se pudo conectar al nodo", nodo)

def start_client(target_host, target_port):

    # meto la conexion del cliente en un loop infinito
    while True:

        # Intenta conectarse al servidor y si no puede se queda reintentando
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((target_host, target_port))
            print("[CLIENT] Conectado al servidor")            

            ip = "127.0.0.1"
            puerto = PUERTO_SERVER

            msg = {
                "type": "registro",
                "ip": ip,
                "puerto": puerto 
            }

            # serializo msg para convertirlo en json
            msg_json = json.dumps(msg)

            client.sendall(msg_json.encode())

            while True:

                response_json = client.recv(1024).decode()

                if not response_json:
                    continue

                response = json.loads(response_json)
                nodos = response["nodos"]
                saludarNodos(nodos)

        except ConnectionRefusedError:
            client.close()
            print("[CLIENT] Servidor no disponible, reintentando en {RETRY_DELAY} segundos...")
            time.sleep(RETRY_DELAY)

if __name__ == "__main__":
    thread_server = threading.Thread(
        target=start_server,
        args=("127.0.0.1",),
        daemon=True
    )

    thread_server.start()
    
    start_client("127.0.0.1", 9000)