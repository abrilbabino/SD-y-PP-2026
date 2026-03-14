import socket
import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("HOST_SERVER1_TCP_TP1")
PORT = int(os.getenv("PORT_SERVER1_TCP_TP1"))

def start_client():

    NodoA = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    NodoA.connect((HOST, PORT))

    msg = "Me conecte, soy el nodo A"
    NodoA.sendall(msg.encode())

    response = NodoA.recv(1024).decode()
    print("Respuesta del servidor:", response)

    NodoA.close()

    return response

if __name__ == "__main__":
    print(start_client())