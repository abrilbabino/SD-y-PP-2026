import socket
import os
from dotenv import load_dotenv

# cargo las variables del .env
load_dotenv()

HOST, PORT = os.getenv("SERVER_1_ADDR_TP1").split(":")
PORT = int(PORT)

def start_server(stop_event):
    # Creo el socket con el tipo de direccionamiento ipv4 (AF_INET) y el tipo de protocolo (SOCK_TREAM para TCP)
    NodoB = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Esto permite reutilizar el puerto para que el SO no lo ponga en time wait al ejecutar varias pruebas seguidas
    NodoB.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # hago que el servicio escuche en la direccion y puerto indicado y lo pongo en listening
    NodoB.bind((HOST, PORT))
    NodoB.listen()

    NodoB.settimeout(1)

    print(f"Server (NodoB) Listening on {HOST}:{PORT} ...")

  # Loop infinito para aceptar múltiples conexiones. el stop event es para finalizar explicitamente el servidor luego de los test y que no quede levantado.
    while not stop_event.is_set():
        try:
            conn, addr = NodoB.accept()
        except socket.timeout:
            continue #vuelve a checkear el stop event
        
        with conn:
            print(f"Conexion recibida desde {addr}")

            while True:
                data = conn.recv(1024).decode()
                if data == "":
                    # si el cliente cerró la conexión, salgo del loop interno
                    print(f"Cliente {addr} desconectado.")
                    conn.close()
                    break

                print(f"Cliente Dice: {data}")
                response = "Mensaje Recibido"
                conn.sendall(response.encode())

    
    NodoB.close()
    print ("Servidor cerrado correctamente")

if __name__ == "__main__":
    start_server()