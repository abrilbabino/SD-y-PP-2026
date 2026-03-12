import threading
import time
from TrabajoPractico1.Hit2.servidor2 import iniciar_servidor
from TrabajoPractico1.Hit2.cliente2 import iniciar_cliente

def test_conexion_cliente_servidor2():
    #Levanta el servidor en un hilo
    hilo_servidor = threading.Thread(target=iniciar_servidor)
    hilo_servidor.start()

    #Da tiempo al servidor para que inicie
    time.sleep(0.5)

    #Ejecutamos el cliente
    respuesta = iniciar_cliente()

    #Testeamos que sea correcto
    assert respuesta == "Hola cliente! :)"
