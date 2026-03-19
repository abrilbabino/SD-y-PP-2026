import socket
import threading
import os
import time
import json
from dotenv import load_dotenv
import requests

# cargo las variables del .env
load_dotenv()

RETRY_DELAY = int(os.getenv("RETRY_DELAY"))
HOST = os.getenv("HOST_SERVER1_TCP_TP1")


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
    # Creo el socket con el tipo de direccionamiento ipv4 (AF_INET) y el tipo de protocolo (SOCK_TREAM para TCP)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Esto permite reutilizar el puerto para que el SO no lo ponga en time wait al ejecutar varias pruebas seguidas
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # hago que el servicio escuche en la direccion y puerto indicado y lo pongo en listening
    # port 0 para que escuche en un puerto aleatorio
    server.bind((host, 0))

    # obtengo el puerto en que esta escuchando
    port = server.getsockname()[1]

    server.listen()

    print(f"Server Listening on {host}:{port} ...")

    # creo el hilo del server con los datos del socket
    threading.Thread(
        target=aceptarConn,
        args=(server,),
        daemon=True
    ).start()

    return port

def aceptarConn (server):
    # Loop infinito para aceptar múltiples conexiones
    while True:
        conn, addr = server.accept()
        
        # creo el hilo del server con los datos del socket
        threading.Thread(
            target=handle_conn,
            args=(conn,addr),
            daemon=True
        ).start()



def register (serverHost, serverPort, nodoHost, nodoPort):

    url = f"http://{serverHost}:{serverPort}/register"

    payload = {
        "host": nodoHost, 
        "port": nodoPort,
    }

    while True:
        try:

            response = requests.post(url, json=payload)
            return response.json()["nodosPares"]
        except:
            time.sleep(RETRY_DELAY)



def conectarAnodo (host, port):
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))

        msg = {
                "type": "Saludo",
                "msg": "Hola, me conecte",
            }

        msg_json = json.dumps(msg)
        client.sendall(msg_json.encode())

        response = json.loads(client.recv(1024).decode())
        client.close()

    except Exception as e:
        print("[CLIENTE] error: ", e)




def start_nodo(target_host, target_port, host):

    port = start_server(host)

    nodosPares = register(target_host, target_port, host, port)

    print("[NODO] Pares encontrados: ", nodosPares)

    for n in nodosPares:
        conectarAnodo(n["host"],n["port"])

    while True:
        time.sleep(1)

if __name__ == "__main__":
    import sys

    target_host = sys.argv[1]
    target_port = int(sys.argv[2])
    host = sys.argv[3]

    start_nodo(target_host, target_port, host)
