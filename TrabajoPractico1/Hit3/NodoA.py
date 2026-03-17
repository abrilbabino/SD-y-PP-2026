import socket
import os
import time

HOST = "127.0.0.1"
PORT = 5000
RETRY_DELAY = 3

def start_client():

    # meto la conexion del cliente en un loop infinito
    while True:

        # Intenta conectarse al servidor
        try:

            print("Conectando con el Servidor...")

            NodoA = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            NodoA.connect((HOST, PORT))

            msg = "Me conecte, soy el nodo A"
            NodoA.sendall(msg.encode())

            response = NodoA.recv(1024).decode()

            NodoA.close()

            return response
        
        # si el servidor esta caido lanza una excepcion e intenta reconectarse en 3 segundos
        except ConnectionRefusedError:

            print(f"Servidor no disponible. Reintentando en {RETRY_DELAY} segundos...")

            time.sleep(RETRY_DELAY)

        # lo mismo en caso de que el servidor se caiga durante la conexion.
        except ConnectionResetError:

            print(f"Conexion perdida. Reintentando en {RETRY_DELAY} segundos...")

            time.sleep(RETRY_DELAY)
        

if __name__ == "__main__":
    print(start_client())