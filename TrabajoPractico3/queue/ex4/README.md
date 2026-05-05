# Ejemplo 4 - Retry con Exponential Backoff

Este ejemplo implementa el patron **Retry con Exponential Backoff** usando RabbitMQ, una cola intermedia con TTL por mensaje y una **Dead Letter Queue (DLQ)**. El consumidor principal intenta procesar cada mensaje y simula un fallo aleatorio con probabilidad del 50%. Si falla, reencola el mensaje con una espera creciente de `1s`, `2s`, `4s` y `8s`. Despues de 4 reintentos fallidos, el mensaje se envia a `dead_letter_queue`.

El delay se implementa sin plugins externos: el consumidor publica el mensaje fallido en `retry_queue` con la propiedad AMQP `expiration`. Cuando vence ese TTL, RabbitMQ lo mueve mediante DLX de vuelta a `main_exchange`, y el mensaje vuelve a entrar en `main_queue`.

## Arquitectura
La solución se despliega en un cluster de Kubernetes (K3s local) e implementa el patrón Retry con Exponential Backoff utilizando una arquitectura de colas intermedias con TTL (Time-To-Live). Este diseño permite gestionar fallos transitorios de manera eficiente sin necesidad de plugins externos en RabbitMQ.  La arquitectura se compone de los siguientes elementos:
- RabbitMQ: Gestiona tres exchanges (main, retry y dlx) para controlar el ciclo de vida del mensaje y sus reintentos.  
- Producer: Envía mensajes iniciales a la main_queue a través del main_exchange.  
- Consumer Principal: Intenta procesar los mensajes y simula fallos aleatorios con un 50% de probabilidad. Es el encargado de calcular el tiempo de espera y gestionar el contador de reintentos.  
- Retry Queue: Una cola intermedia "de espera" donde los mensajes aguardan antes de volver a ser procesados.  
- DLQ Consumer: Procesa los mensajes que han agotado el límite de 4 reintentos y han sido movidos a la dead_letter_queue.  

## Mecanismo de Exponential Backoff
El flujo de reintento utiliza las propiedades nativas de RabbitMQ para simular retrasos crecientes:  
- Lógica de Reintento: Ante un fallo, el consumidor publica el mensaje en el retry_exchange en lugar de rechazarlo. El número de intento se registra en el encabezado x-retry-attempt.  
- Espera Incremental (TTL): El mensaje se envía a la retry_queue con la propiedad expiration configurada según el intento actual: 1s, 2s, 4s u 8s.  
- Expiración y Reenvío: La retry_queue tiene configurado un x-dead-letter-exchange que apunta de vuelta al main_exchange. Cuando el TTL del mensaje expira, RabbitMQ lo mueve automáticamente de regreso a la cola principal para un nuevo intento de procesamiento.  
- Salida a DLQ: Si un mensaje alcanza los 4 reintentos fallidos, el consumidor lo envía al dlx_exchange para su almacenamiento definitivo en la dead_letter_queue, evitando bucles infinitos.  

## Diagrama de Arquitectura
![Arquitectura-ex4](Arquitectura_ex4.png)

## Configuracion RabbitMQ

La topologia declarada por el codigo es:

- `main_exchange`: exchange principal de tipo `direct`.
- `main_queue`: cola principal durable donde consume `consumer.py`.
- `retry_exchange`: exchange de tipo `direct` para publicar reintentos.
- `retry_queue`: cola intermedia durable. Recibe mensajes con TTL por mensaje.
- `retry_queue` tiene `x-dead-letter-exchange: main_exchange`.
- `retry_queue` tambien usa `x-dead-letter-routing-key: tasks`.
- `dlx_exchange`: exchange de tipo `direct` para fallos definitivos.
- `dead_letter_queue`: cola donde quedan los mensajes agotados.
- Binding `main_exchange -> main_queue` con routing key `tasks`.
- Binding `retry_exchange -> retry_queue` con routing key `retry`.
- Binding `dlx_exchange -> dead_letter_queue` con routing key `dead`.

El intento actual viaja en el header `x-retry-attempt`. El body JSON original se mantiene sin modificar.

## ConfigMap

El sistema maneja configuracion externa con el `ConfigMap` `rabbitmq-config-ex4`:

```yaml
data:
  RABBITMQ_HOST: rabbitmq-ex4
  RABBITMQ_PORT: "5672"
  MAIN_EXCHANGE: main_exchange
  MAIN_QUEUE: main_queue
  MAIN_ROUTING_KEY: tasks
  RETRY_EXCHANGE: retry_exchange
  RETRY_QUEUE: retry_queue
  RETRY_ROUTING_KEY: retry
  DLX_EXCHANGE: dlx_exchange
  DEAD_LETTER_QUEUE: dead_letter_queue
  DLQ_ROUTING_KEY: dead
```

Las credenciales van en `Secret`, no hardcodeadas en el codigo.

## Paso a paso de ejecucion

Ubicarse en la raiz del proyecto:

```bash
cd TrabajoPractico3/queue/ex4/
```

Build de la imagen:

```bash
docker build -f Dockerfile -t app-ex4:latest .
```

Importar a k3d:

```bash
k3d image import app-ex4:latest -c sobel
```

Desplegar:

```bash
kubectl apply -f k3s/
```

Ver Pods:

```bash
kubectl get pods
```

Ver logs del productor:

```bash
kubectl logs -f deployment/producer-ex4
```

Ver logs del consumidor principal:

```bash
kubectl logs -f deployment/consumer-ex4
```

Ver logs del consumidor DLQ:

```bash
kubectl logs -f deployment/dlq-consumer-ex4
```

## Validacion esperada

El productor envia 10 mensajes JSON. El consumidor principal registra los mensajes exitosos:

```text
Mensaje procesado correctamente en intento
```

Cuando ocurre un fallo aleatorio, registra el numero de intento y la espera del reintento:

```text
Fallo al procesar mensaje id=3. Intento 2/4. Reencolando con espera de 2s.
```

Si un mensaje falla mas de 4 veces, se envia a DLQ:

```text
Mensaje enviado a DLQ luego de 4 reintentos fallidos
Mensaje recibido desde DLQ tras 4 reintentos
```

## Health-checks

- Producer: `GET /health` en puerto `8080`.
- Consumer principal: `GET /health` en puerto `8081`.
- Consumer DLQ: `GET /health` en puerto `8082`.

Respuesta:

```json
{"servicio": "status"}
```

## Variables de entorno

Ver [.env.example](.env.example):

```bash
RABBITMQ_USER=tp3
RABBITMQ_PASS=tp3
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
MAIN_EXCHANGE=main_exchange
MAIN_QUEUE=main_queue
MAIN_ROUTING_KEY=tasks
RETRY_EXCHANGE=retry_exchange
RETRY_QUEUE=retry_queue
RETRY_ROUTING_KEY=retry
DLX_EXCHANGE=dlx_exchange
DEAD_LETTER_QUEUE=dead_letter_queue
DLQ_ROUTING_KEY=dead
FAILURE_PROBABILITY=0.5
```

## Tests

Ejecutar:

```bash
python -m unittest tests/test_integration.py
```

## Limpieza

```bash
kubectl delete -f k3s/
```
