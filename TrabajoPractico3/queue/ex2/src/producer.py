import os
import time
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import pika
import hashlib

# Configuración de logs
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('producer')
logger.setLevel(logging.INFO)

# Salida estándar (para Kubernetes/Docker logs)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

# Salida a archivo
os.makedirs('/var/log', exist_ok=True)
try:
    file_handler = logging.FileHandler('/var/log/app.log')
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
except PermissionError:
    logger.warning("No se pudo escribir en /var/log/app.log, continuando solo con stdout.")

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            
    def log_message(self, format, *args):
        # Evitar loguear cada healthcheck en info
        pass

def start_health_server():
    server = HTTPServer(('0.0.0.0', 8080), HealthCheckHandler)
    logger.info("Health server listening on port 8080")
    server.serve_forever()

def get_rabbitmq_connection():
    host = os.getenv('RABBIT_HOST', 'localhost')
    user = os.getenv('RABBIT_USER', 'guest')
    password = os.getenv('RABBIT_PASS', 'guest')
    
    credentials = pika.PlainCredentials(user, password)
    parameters = pika.ConnectionParameters(host=host, credentials=credentials)
    
    # Retry mechanism para esperar a que RabbitMQ levante
    max_retries = 10
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            connection = pika.BlockingConnection(parameters)
            logger.info("Conectado a RabbitMQ exitosamente")
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            logger.warning(f"Intento {attempt + 1}/{max_retries} fallido al conectar a RabbitMQ: {e}")
            time.sleep(retry_delay)
    
    raise Exception("No se pudo conectar a RabbitMQ después de varios intentos.")

def main():
    # Iniciar endpoint healthcheck
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    connection = get_rabbitmq_connection()
    channel = connection.channel()

    # Declarar el exchange fanout
    exchange_name = 'block_events'
    channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')
    
    logger.info(f"Exchange '{exchange_name}' declarado. Iniciando minado simulado...")
    
    block_index = 0
    try:
        while True:
            # Simular minado de bloque
            time.sleep(5)
            block_index += 1
            block_data = f"Block {block_index} data {time.time()}"
            block_hash = hashlib.sha256(block_data.encode()).hexdigest()
            
            message = {
                "block_index": block_index,
                "hash": block_hash
            }
            message_body = json.dumps(message)
            
            channel.basic_publish(
                exchange=exchange_name,
                routing_key='', # Fanout ignora la routing key
                body=message_body
            )
            logger.info(f"[x] Bloque minado enviado: {message_body}")
            
    except KeyboardInterrupt:
        logger.info("Interrumpido por el usuario")
    finally:
        connection.close()

if __name__ == '__main__':
    main()
