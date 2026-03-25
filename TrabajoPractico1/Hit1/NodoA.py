import socket
import os
from dotenv import load_dotenv
from ..common.logger import log_event

load_dotenv()


HOST, PORT = os.getenv("SERVER_1_ADDR_TP1").split(":")
PORT = int(PORT)


def start_client():

    log_event("INFO", "Nodo A iniciado")
    NodoA = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    NodoA.connect((HOST, PORT))

    msg = "Me conecte, soy el nodo A"
    log_event("INFO", f"Enviando mensaje: {msg}")
    NodoA.sendall(msg.encode())

    response = NodoA.recv(1024).decode()
    log_event("INFO", f"Respuesta del servidor: {response}")
    NodoA.close()

    return response

if __name__ == "__main__":
    print(start_client())