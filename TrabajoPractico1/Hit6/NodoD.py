import socket
import threading
import json
import time

#Defino un array en memoria que va actuar como registro de nodos C 
#en este caso permitimos el registro de hasta 10 instancias
tamanio = 10
registro = [None] * tamanio

#Guardamos el momento en que inicia el nodo D para calcular el uptime del servicio
start_time = time.time()

#Maneja las conexiones al server HTTP /Health
def handle_health(conn):
    #Armamos una con los nodos activos
    activos = [n for n in registro if n is not None]

    #Calculamos el tiempo que lleva ejecutandose el servicio
    uptime = int(time.time() - start_time)

    #Hacemos que el cuerpo de la respuesta este en formato json
    body = json.dumps({
        "nodos_registrados": len(activos),
        "uptime": str(uptime) + "s",
        "estado_general": "ok"
    })

    #Armamos una respuesta HTTP valida
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: " + str(len(body)) + "\r\n"
        "\r\n" +
        body
    )

    #Enviamos la respuesta al cliente
    conn.sendall(response.encode())

    #Cerramos la conexion HTTP
    conn.close()

#Endpoint para el servidor HTTP \health
def iniciar_server_health(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    while True:
        conn, addr = server.accept()
        #Lee la peticion
        request = conn.recv(1024).decode()
        
        #Si la peticion es al endpoint /health entonces maneja la conexion
        if "GET /health" in request:
            handle_health(conn)
        else:
            conn.close()

#Manejo conexion TCP de nodosC
def handle_conn(conn, addr):
    print(f"[SERVER] Conectado con {addr}")
    try:
        while True: 
            data = conn.recv(1024)

            if not data:
                #Si el nodo deja de estar conectado lo elimino del registro
                eliminarNodo(addr[1])
                conn.close()
                return

            msg = json.loads(data.decode())
            
            # si el mensaje indica que el nodo quiere registrarse
            if msg["type"] == "registro":

                ip = msg["ip"]
                puerto = msg["puerto"]

                #Se envia la respuesta con la lista de nodos
                
                nodos_activos = [n for n in registro if n is not None]

                respuesta = {
                    "type": "lista_nodos",
                    "nodos": nodos_activos
                }

                #Se registra el nodo (ESTO NO SE SI ASI O AL REVES PQ AL REVES SE VA A SALUDAR A EL MISMO)
                registrarNodo(ip, puerto)
                
                respuesta_json = json.dumps(respuesta)
                conn.sendall(respuesta_json.encode())

    finally:
        conn.close()
        print(f"[SERVER] Conexion cerrada con {addr}")

#Servidor TCP
def iniciar_server_registro(host, port):

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((host, port))
    server.listen()

    print("Nodo D escuchando registros")

    while True:

        conn, addr = server.accept()

        thread = threading.Thread(
            target=handle_conn,
            args=(conn, addr),
            daemon=True
        )

        thread.start()

#Registro la instancia de NodoC y envio la lista para que realice los saludos
def registrarNodo(ip, puerto):
    nodoC = {"ip": ip, "puerto": puerto}
    i = 0
    while  i < tamanio and registro[i] is not None :
        i = i + 1
    if i < tamanio:
        registro[i] = nodoC

#Elimino los registros de nodos inactivos   
def eliminarNodo(puerto):
    i=0
    while i < tamanio and registro[i]["puerto"] != puerto:
        i = i + 1
    
    if i < tamanio and registro[i]["puerto"] == puerto:
        registro[i] = None
        
if __name__ == "__main__":
    thread = threading.Thread(
        target=iniciar_server_registro,
        args=("0.0.0.0", 9000),
        daemon=True
    )

    thread.start()

    iniciar_server_health("0.0.0.0", 8080)