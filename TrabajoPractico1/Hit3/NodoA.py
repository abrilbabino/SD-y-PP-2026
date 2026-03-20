import socket
import os
import time
from dotenv import load_dotenv
from ..common.logger import log_event

load_dotenv()

HOST, PORT = os.getenv("SERVER_1_ADDR_TP1").split(":")
PORT = int(PORT)
RETRY_DELAY = int(os.getenv("RETRY_DELAY"))

def start_client():
    log_event("INFO", "Nodo A (cliente con reconexion) iniciado")

    # meto la conexion del cliente en un loop infinito
    while True:

        # Intenta conectarse al servidor
        try:

            log_event("INFO", f"Intentando conectar a {HOST}:{PORT}")

            NodoA = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            NodoA.connect((HOST, PORT))
            log_event("INFO", "Conexion establecida")


            msg = "Me conecte, soy el nodo A"
            NodoA.sendall(msg.encode())
            log_event("INFO", f"Enviando mensaje: {msg}")


            response = NodoA.recv(1024).decode()
            log_event("INFO", f"Respuesta recibida: {response}")

            NodoA.close()
            log_event("INFO", "Conexion cerrada correctamente")

            return response
        
        # si el servidor esta caido lanza una excepcion e intenta reconectarse en 3 segundos
        except ConnectionRefusedError:

            log_event("ERROR", f"Servidor no disponible. Reintentando en {RETRY_DELAY} segundos...")
            time.sleep(RETRY_DELAY)

        # lo mismo en caso de que el servidor se caiga durante la conexion.
        except ConnectionResetError:

            log_event("ERROR", f"Conexion perdida. Reintentando en {RETRY_DELAY} segundos...")
            time.sleep(RETRY_DELAY)
        

if __name__ == "__main__":
    print(start_client())