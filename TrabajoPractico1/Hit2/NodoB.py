import socket
import os
from dotenv import load_dotenv
from ..common.logger import log_event


# cargo las variables del .env
load_dotenv()

HOST, PORT = os.getenv("SERVER_1_ADDR_TP1").split(":")
PORT = int(PORT)


def start_server():
    log_event("INFO", "Nodo B (servidor) iniciado")
    # Creo el socket con el tipo de direccionamiento ipv4 (AF_INET) y el tipo de protocolo (SOCK_TREAM para TCP)
    NodoB = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Esto permite reutilizar el puerto para que el SO no lo ponga en time wait al ejecutar varias pruebas seguidas
    NodoB.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # hago que el servicio escuche en la direccion y puerto indicado y lo pongo en listening
    NodoB.bind((HOST, PORT))
    NodoB.listen()

    log_event("INFO", f"Servidor escuchando en {HOST}:{PORT}")

    # Bloquea el programa y cuando alguien se conecta devuelve un nuevo socket dedicado a la conexion con el cliente (conn) y la direccion del cliente (addr)
    conn, addr = NodoB.accept()

    with conn:

        log_event("INFO", f"Conexion recibida desde {addr}")

        # el server espera que el cliente envie datos (hasta 1024 bytes) por eso se usa el decode() para convertirlos a string
        data = conn.recv(1024).decode()

        if data:

            log_event("INFO", f"Mensaje recibido: {data}")
            response = "Mensaje Recibido"

            # Convierto el string del mensaje a bytes y lo envio
            conn.sendall(response.encode())
            log_event("INFO", "Respuesta enviada al cliente")


    # cierro la conexion
    NodoB.close()
    conn.close()
    log_event("INFO", "Servidor cerrado")

if __name__ == "__main__":
    start_server()    
