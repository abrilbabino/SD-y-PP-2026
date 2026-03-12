import socket

HOST = "127.0.0.1"
PORT = 5000

def iniciar_cliente():
    #Se crea el socket del cliente. af_inet= ipv4 -- sock_stream = tcp
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    # envio mensaje al server
    client.sendall("Hola servidor!".encode())

    #recivo la data del server
    data = client.recv(1024).decode()
    print("Respuesta del servidor:", data)

    #cierro conexion socket - señal de fin tcp 
    client.close()
    #devuelvo la respuesta
    return data

#llamada a la funcion
if __name__ == "__main__":
    iniciar_cliente()