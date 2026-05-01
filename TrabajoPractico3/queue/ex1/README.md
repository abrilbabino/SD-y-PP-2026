# Ejemplo 1 - Work Queue con RabbitMQ

Este ejemplo implementa el patron **Work Queue** o **Maestro/Esclavo**. Un productor publica 10 tareas en la cola `task_queue` y uno o mas workers las consumen. Al escalar el Deployment de workers a 2 replicas se puede observar el reparto round-robin de RabbitMQ.

## Arquitectura

```mermaid
flowchart LR
    P["Producer Deployment<br/>producer.py<br/>/health:8080"] --> Q["RabbitMQ<br/>task_queue"]
    Q --> W1["Worker Pod 1<br/>worker.py<br/>/health:8081"]
    Q --> W2["Worker Pod 2<br/>worker.py<br/>/health:8081"]
```

## Estructura

```text
TrabajoPractico3/queue/ex1/
├── src/
│   ├── producer.py
│   └── worker.py
├── k3s/
│   ├── rabbitmq.yaml
│   ├── producer-dep.yaml
│   └── worker-dep.yaml
├── tests/
│   └── test_integration.py
├── Dockerfile
├── .env.example
└── README.md
```

## Paso a paso de ejecucion

Situarse en la raiz del ejemplo:

```bash
cd TrabajoPractico3/queue/ex1/
```

Construir la imagen unica para producer y worker:

```bash
docker build -f Dockerfile -t app-ex1:latest .
```

Importar la imagen local al cluster k3d `sobel`:

```bash
k3d image import app-ex1:latest -c sobel
```

Desplegar RabbitMQ, producer y worker:

```bash
kubectl apply -f k3s/
```

Verificar Pods:

```bash
kubectl get pods
```

Ver logs del productor:

```bash
kubectl logs -f deployment/producer-deployment
```

Ver logs del worker:

```bash
kubectl logs -f deployment/worker-deployment
```

## Escalar y observar round-robin

Escalar el worker a 2 replicas:

```bash
kubectl scale deployment worker-deployment --replicas=2
```

Ver logs de todos los workers:

```bash
kubectl logs -f -l app=worker --prefix=true
```

Si el producer ya envio las 10 tareas antes de escalar, reiniciarlo para generar otra tanda:

```bash
kubectl rollout restart deployment/producer-deployment
```

Con 2 workers se espera observar que algunas tareas las procesa un Pod y otras tareas el otro. RabbitMQ entrega cada mensaje a un solo consumidor y reparte los mensajes entre los consumidores disponibles.

## Health-checks

El producer expone:

```text
GET /health en puerto 8080
```

El worker expone:

```text
GET /health en puerto 8081
```

Ambos devuelven:

```json
{"servicio": "status"}
```

## Variables de entorno

Ver [.env.example](.env.example).

```bash
RABBITMQ_USER=tp3
RABBITMQ_PASS=tp3
RABBIT_HOST=rabbitmq
RABBITMQ_PORT=5672
QUEUE_NAME=task_queue
```

En Kubernetes, usuario y password se configuran mediante `Secret`. La configuracion externa de la aplicacion se maneja con el `ConfigMap` `rabbitmq-config`, definido en `k3s/rabbitmq.yaml`:

```yaml
data:
  RABBIT_HOST: rabbitmq
  RABBITMQ_PORT: "5672"
  QUEUE_NAME: task_queue
```

El producer y el worker leen `RABBIT_HOST` para conectarse al Service de RabbitMQ y `QUEUE_NAME` para declarar y consumir la cola.

## Logging

Los procesos escriben logs en:

- STDOUT, visible con `kubectl logs`.
- Archivo rotativo en disco:
  - Producer: `/var/log/ex1/producer.log`
  - Worker: `/var/log/ex1/worker.log`

## Tests

Ejecutar desde esta carpeta:

```bash
python -m unittest tests/test_integration.py
```

## Limpieza

```bash
kubectl delete -f k3s/
```
