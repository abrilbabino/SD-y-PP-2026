# Ejemplo 3 - Dead Letter Queue con RabbitMQ

Este ejemplo implementa el patron **Dead Letter Queue (DLQ)** usando una **Dead Letter Exchange (DLX)**. El productor publica mensajes JSON en `main_queue`. El consumidor principal procesa los mensajes correctos y rechaza con `basic_nack(requeue=False)` aquellos que contienen `"error": true`. RabbitMQ redirige automaticamente esos mensajes a `dlx_exchange` y los almacena en `dead_letter_queue`.

Este patron evita perder mensajes no procesables y permite analizarlos, reintentarlos o corregirlos fuera del flujo principal.

## Arquitectura
La solución se despliega en un cluster de Kubernetes (K3s local) e implementa el patrón Dead Letter Queue (DLQ) utilizando un Dead Letter Exchange (DLX). Este diseño permite la gestión de mensajes fallidos sin interrumpir el flujo principal de la aplicación.  La arquitectura consta de los siguientes componentes:RabbitMQ: 
- Broker de mensajería que gestiona dos exchanges y dos colas principales para el flujo de errores.  Producer: Un pod que publica mensajes en formato JSON hacia el main_exchange con la routing key tasks.  
- Consumer Principal: Procesa los mensajes de la main_queue. Cuando detecta un mensaje con el campo "error": true, lo rechaza explícitamente.  
- DLQ Consumer: Un consumidor dedicado que escucha exclusivamente la dead_letter_queue para procesar o auditar los mensajes que fallaron en el primer intento.  

## Patrón Dead Letter Exchange (DLX)
Para evitar la pérdida de información y permitir el análisis de errores, se configura la siguiente lógica de reenvío automático:  
- Configuración de la Cola Principal: La main_queue se declara con el argumento x-dead-letter-exchange apuntando a dlx_exchange y un x-dead-letter-routing-key configurado como dead.  
- Mecanismo de Rechazo (Nack): El consumidor principal utiliza la instrucción basic_nack(requeue=False) al encontrar un mensaje con error. Al no ser reencolado en la cola original, RabbitMQ redirige el mensaje automáticamente al exchange de "letra muerta" (DLX).  
- Redirección y Almacenamiento: El dlx_exchange (de tipo direct) recibe el mensaje rechazado y, basándose en la routing key dead, lo deposita en la dead_letter_queue.  
- Persistencia de Errores: Este patrón asegura que cualquier mensaje no procesable sea capturado en una cola de soporte, donde el DLQ Consumer puede imprimir los fallos para su posterior corrección o reintento manual.  

## Diagrama de Arquitectura

![Arquitectura-ex3](Arquitectura-ex3.png)

## Configuracion RabbitMQ

La topologia declarada por el codigo es:

- `main_exchange`: exchange principal de tipo `direct`.
- `main_queue`: cola principal durable.
- `main_queue` tiene el argumento `x-dead-letter-exchange: dlx_exchange`.
- `main_queue` tambien usa `x-dead-letter-routing-key: dead`.
- `dlx_exchange`: Dead Letter Exchange de tipo `direct`.
- `dead_letter_queue`: cola donde quedan los mensajes fallidos.
- Binding `main_exchange -> main_queue` con routing key `tasks`.
- Binding `dlx_exchange -> dead_letter_queue` con routing key `dead`.

## ConfigMap

El sistema maneja configuracion externa con el `ConfigMap` `rabbitmq-config-ex3`:

```yaml
data:
  RABBITMQ_HOST: rabbitmq-ex3
  RABBITMQ_PORT: "5672"
  MAIN_EXCHANGE: main_exchange
  MAIN_QUEUE: main_queue
  MAIN_ROUTING_KEY: tasks
  DLX_EXCHANGE: dlx_exchange
  DEAD_LETTER_QUEUE: dead_letter_queue
  DLQ_ROUTING_KEY: dead
```

Las credenciales van en `Secret`, no hardcodeadas en el codigo.

## Paso a paso de ejecucion

Ubicarse en la raiz del proyecto:

```bash
cd TrabajoPractico3/queue/ex3/
```

Build de la imagen:

```bash
docker build -f Dockerfile -t app-ex3:latest .
```

Importar a k3d:

```bash
k3d image import app-ex3:latest -c sobel
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
kubectl logs -f deployment/producer-ex3
```

Ver logs del consumidor principal:

```bash
kubectl logs -f deployment/consumer-ex3
```

Ver logs del consumidor DLQ:

```bash
kubectl logs -f deployment/dlq-consumer-ex3
```

## Validacion esperada

El productor envia 10 mensajes JSON. Algunos incluyen:

```json
{"error": true}
```

El consumidor principal debe mostrar logs indicando que esos mensajes fueron rechazados:

```text
Mensaje rechazado y enviado a DLQ
```

El consumidor de DLQ debe mostrar:

```text
Mensaje recibido desde DLQ
```

Esto valida que los mensajes con `"error": true` no se pierden, salen de `main_queue` y terminan en `dead_letter_queue`.

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
```

## Tests

Ejecutar:

```bash
pytest
```

## Limpieza

```bash
kubectl delete -f k3s/
```
