import socket

HOST = "127.0.0.1"
PORT = 5000

#Se crea el socket del cliente. af_inet= ipv4 -- sock_stream = tcp
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# emvio mensaje al server
client.sendall("Hola servidor!".encode())

#resivo la data del server
data = client.recv(1024).decode()
print("Respuesta del servidor:", data)

#cierro conexion socket - señal de fin tcp 
client.close()