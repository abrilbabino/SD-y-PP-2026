# Ejemplo 3 - Dead Letter Queue con RabbitMQ

Este ejemplo implementa el patron **Dead Letter Queue (DLQ)** usando una **Dead Letter Exchange (DLX)**. El productor publica mensajes JSON en `main_queue`. El consumidor principal procesa los mensajes correctos y rechaza con `basic_nack(requeue=False)` aquellos que contienen `"error": true`. RabbitMQ redirige automaticamente esos mensajes a `dlx_exchange` y los almacena en `dead_letter_queue`.

Este patron evita perder mensajes no procesables y permite analizarlos, reintentarlos o corregirlos fuera del flujo principal.

## Arquitectura

La solución se despliega en un cluster de Kubernetes (K3s local) e implementa el patrón Dead Letter Queue (DLQ) utilizando un Dead Letter Exchange (DLX). Este diseño permite la gestión de mensajes fallidos sin interrumpir el flujo principal de la aplicación. La arquitectura consta de los siguientes componentes:RabbitMQ:

- Broker de mensajería que gestiona dos exchanges y dos colas principales para el flujo de errores. Producer: Un pod que publica mensajes en formato JSON hacia el main_exchange con la routing key tasks.
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

## ConfigMap y Secret

En Kubernetes, las credenciales se generan de forma dinámica utilizando el archivo `.env` mediante un `Secret` (`rabbit-credentials-ex3`). El resto de la configuración no sensible se encuentra definida de forma declarativa en el archivo `k3s/configmap.yaml` bajo el nombre `config-ex3`.

## Paso a paso de ejecucion

**Paso 1: Build desde la Raíz**
Construir la imagen única posicionándose en la raíz del repositorio (`TrabajoPractico3/`). El `.` al final es fundamental para que Docker acceda al archivo `requirements.txt` ubicado en la raíz.

```bash
docker build -f TrabajoPractico3/queue/ex3/Dockerfile -t app-ex3:latest .
```

**Paso 2: Importar Imagen**
Importar la imagen local al cluster k3d `sobel`:

```bash
k3d image import app-ex3:latest -c sobel
```

**Paso 3: Cambio de Directorio**
Situarse en el directorio del ejercicio para crear los recursos de configuración y aplicar los manifiestos:

```bash
cd TrabajoPractico3/queue/ex3/
cp .env.example .env
# Completar los valores en el archivo .env si es necesario
kubectl create secret generic rabbit-credentials-ex3 --from-env-file=.env
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
{ "error": true }
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
{ "servicio": "status" }
```

Para ver el endpoint health del producer:

```bash
kubectl port-forward deployment/producer-ex3 8080:8080
```

En el buscador

```bash
http://localhost:8080/health
```

Para ver el el endpoint health del consumer principal:

```bash
kubectl port-forward deployment/consumer-ex3 8081:8081
```

En el buscador

```bash
http://localhost:8081/health
```
Para ver el el endpoint health del consumer dlq:

```bash
kubectl port-forward deployment/dlq-consumer-ex3 8082:8082
```

En el buscador

```bash
http://localhost:8082/health
```
## Variables de entorno

Ver [.env.example](.env.example):

```bash
RABBITMQ_USER=tu-usuario
RABBITMQ_PASS=tu-contraseña
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
