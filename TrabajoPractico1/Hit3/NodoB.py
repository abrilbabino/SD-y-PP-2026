import socket
import os
import time

HOST = "127.0.0.1"
PORT = 8888

def start_server():
    # Creo el socket con el tipo de direccionamiento ipv4 (AF_INET) y el tipo de protocolo (SOCK_TREAM para TCP)
    NodoB = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Esto permite reutilizar el puerto para que el SO no lo ponga en time wait al ejecutar varias pruebas seguidas
    NodoB.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # hago que el servicio escuche en la direccion y puerto indicado y lo pongo en listening
    NodoB.bind((HOST, PORT))
    NodoB.listen()

    print(f"Server (NodoB) Listening on {HOST}:{PORT} ...")

  # Loop infinito para aceptar múltiples conexiones
    while True:
        conn, addr = NodoB.accept()
        with conn:
            print(f"Conexion recibida desde {addr}")

            while True:
                data = conn.recv(1024).decode()
                if data == "":
                    # si el cliente cerró la conexión, salgo del loop interno
                    print(f"Cliente {addr} desconectado.")
                    break

                print(f"Cliente Dice: {data}")
                response = "Mensaje Recibido"
                conn.sendall(response.encode())

    # nunca llegamos acá porque el servidor queda corriendo
    NodoB.close()

if __name__ == "__main__":
    start_server()