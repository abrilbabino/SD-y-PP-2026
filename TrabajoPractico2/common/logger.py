import time
import json

# Lista en memoria donde se almacenan los logs durante la ejecución
logs_memoria = []

def log_event(nivel, mensaje):
    # Genera un timestamp con fecha y hora actual en formato legible
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # Crea un diccionario (estructura JSON) con la información del log
    log = {
        "timestamp": timestamp,   # momento en que ocurrió el evento
        "nivel": nivel,           # tipo de log: INFO, ERROR, DEBUG, etc.
        "mensaje": mensaje        # descripción del evento
    }

    # ===== LOG EN MEMORIA =====
    # Guarda el log en la lista en RAM (se pierde al cerrar el programa)
    logs_memoria.append(log)

    # ===== LOG EN DISCO =====
    # Abre (o crea) el archivo app.log en modo "append" (agregar al final)
    with open("app.log", "a") as f:
        # Convierte el diccionario a JSON string y lo escribe en una línea
        f.write(json.dumps(log) + "\n")

    # ===== LOG EN CONSOLA =====
    # Muestra el log en pantalla para debugging en tiempo real
    print(f"[{timestamp}] [{nivel}] {mensaje}")