import socket
import os
from dotenv import load_dotenv

# cargo las variables del .env
load_dotenv()

HOST = os.getenv("HOST_SERVER_TCP_TP1")
PORT = int(os.getenv("PORT_SERVER_TCP_TP1"))

def start_server():
    # Creo el socket con el tipo de direccionamiento ipv4 (AF_INET) y el tipo de protocolo (SOCK_TREAM para TCP)
    NodoB = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # hago que el servicio escuche en la direccion y puerto indicado y lo pongo en listening
    NodoB.bind((HOST, PORT))
    NodoB.listen()

    print(f"Server (NodoB) Listening on {HOST}:{PORT} ...")

    # Bloquea el programa y cuando alguien se conecta devuelve un nuevo socket dedicado a la conexion con el cliente (conn) y la direccion del cliente (addr)
    conn, addr = NodoB.accept()

    print(f"Conexion recibida desde {addr}")

    # el server espera que el cliente envie datos (hasta 1024 bytes) por eso se usa el decode() para convertirlos a string
    data = conn.recv(1024).decode()

    print(f"Cliente Dice: {data}")

    response = "Mensaje Recibido"

    # Convierto el string del mensaje a bytes y lo envio
    conn.sendall(response.encode())

    # cierro la conexion
    NodoB.close()

if __name__ == "__main__":
    start_server()    
