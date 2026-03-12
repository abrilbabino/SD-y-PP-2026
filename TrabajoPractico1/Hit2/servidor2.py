import socket

#definicion de host y puerto
HOST = "0.0.0.0"
PORT = 5000

def iniciar_servidor():
    #crear socket AF.INT = IPV4 --- SOCK_STREAM = TCP
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

    server.bind((HOST, PORT))

    #CONVIERTE AL SOCKET EN SERVER TCP
    server.listen()
    print("Servidor esperando conexión...")

    """
    accept() hace tres cosas: - espera a que un cliente se conecte - establece la conexión TCP 
    - Crea un nuevo socket para comunicarse con ese cliente
    conn  -> socket de comunicación con el cliente
    addr  -> dirección del cliente
    """
    conn, addr = server.accept()
    print("Conectado por:", addr)


    """
    recv - Lee datos que llegan del cliente.1024 Es el tamaño máximo del buffer
    decode - Los datos llegan como bytes.
    """
    data = conn.recv(1024).decode()
    print("Mensaje recibido:", data)

    #sendall envía datos al cliente. . encode convierte el string en bytes
    conn.sendall("Hola cliente! :)".encode())

    #cierro conexion
    conn.close()

    #libero el puerto
    server.close()

#Llamada a la funcion
if __name__ == "__main__":
    iniciar_servidor()