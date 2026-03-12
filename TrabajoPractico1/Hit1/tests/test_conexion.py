import threading
import time

from TrabajoPractico1.Hit1.server import iniciar_servidor
from TrabajoPractico1.Hit1.cliente import iniciar_cliente


def test_conexion_cliente_servidor():
    #CREAR HILO PARA SERVER 
    hilo_servidor = threading.Thread(target=iniciar_servidor)
    hilo_servidor.start() 
    #Da tiempo al servidor para que inicie 
    time.sleep(0.5) 
    #Ejecutamos el cliente 
    respuesta = iniciar_cliente() 
    #Testeamos que sea correcto
    assert respuesta == "Hola cliente! :)"