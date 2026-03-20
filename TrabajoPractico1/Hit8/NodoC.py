import socket
import threading
import os
import time
import json
from dotenv import load_dotenv
import grpc
from concurrent import futures
import nodos_pb2
import nodos_pb2_grpc


# cargo las variables del .env
load_dotenv()

RETRY_DELAY = int(os.getenv("RETRY_DELAY"))

class NodeServiceServicer(nodos_pb2_grpc.NodeServiceServicer):
    def SendMessage(self, request, context):
        print(f"[SERVER] Mensaje recibido: {request.msg}")
        return nodos_pb2.ServerResponse(type="msgRecibido", msg="Mensaje Recibido")


def start_server(host, port):
    # Creo un servidor gRPC con un pool de hilos (máx. 10) para manejar múltiples llamadas concurrentes
    server = grpc.server(futures.ThreadPoolExecutor(max_workers = 10))

    # Registro la implementación del servicio definido en nodos.proto dentro del servidor
    nodos_pb2_grpc.add_NodeServiceServicer_to_server(NodeServiceServicer(), server)
   
   # Hago que el servidor escuche en la dirección y puerto indicados
    server.add_insecure_port(f"{host}:{port}")

    # Inicio el servidor gRPC
    server.start()

    print(f"Server Listening on {host}:{port} ...")

    # Mantengo el servidor corriendo indefinidamente para aceptar múltiples conexiones
    server.wait_for_termination()


def start_client(target_host, target_port):
    # meto la conexion del cliente en un loop infinito
    while True:
        try:
            # Creo un canal gRPC hacia el servidor en la dirección y puerto indicados
            with grpc.insecure_channel(f'{target_host}:{target_port}') as channel:
                # Inicializo el stub del servicio definido en nodos.proto
                stub = nodos_pb2_grpc.NodeServiceStub(channel)
                # Construyo el mensaje usando la clase generada por Protobuf
                msg = nodos_pb2.ClientMessage(type = "Cliente Conectado", msg = "[CLIENTE] Me Conecte")
               # Envío el mensaje al servidor mediante la llamada RPC SendMessage
                response = stub.SendMessage(msg)
                return response.msg

        except grpc.RpcError:
            print("[CLIENTE] Servidor no disponible, reintentando en {RETRY_DELAY} segundos...")
            time.sleep(RETRY_DELAY)


if __name__ == "__main__":
    import sys

    my_port = int(sys.argv[1])
    peer_port = int(sys.argv[2])

    HOST = "127.0.0.1"

    #Thread del servidor (escucha conexiones entrantes)
    thread_server = threading.Thread(
        target=start_server,
        args=(HOST, my_port),
        daemon=True
    )
    thread_server.start()

    # Espera para asegurar que el server levante
    time.sleep(1)

    #Thread del cliente (intenta conectarse al otro nodo continuamente)
    thread_client = threading.Thread(
        target=start_client,
        args=(HOST, peer_port),
        daemon=True
    )
    thread_client.start()

    print(f"[NODE {my_port}] Nodo iniciado. Escuchando en {my_port} y conectando a {peer_port}")

    # Mantiene vivo el proceso principal
    while True:
        time.sleep(1)
        
