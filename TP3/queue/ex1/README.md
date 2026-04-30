# TP3 - Queue - Ejemplo 1

Ejemplo de **Message Queue punto a punto** con RabbitMQ, AMQP 0-9-1, Python y `pika`.

En este patron, un productor envia mensajes a una cola y cada mensaje es consumido por exactamente un consumidor. Si hay dos consumidores escuchando la misma cola, RabbitMQ reparte el trabajo entre ambos.

## Archivos

```text
TP3/queue/ex1/
├── producer.py
├── consumer.py
├── Dockerfile.producer
├── Dockerfile.consumer
├── README.md
└── manifests/
    ├── rabbitmq-deployment.yaml
    ├── consumer-deployment.yaml
    └── producer-job.yaml
```

## Como correrlo localmente

Levantar RabbitMQ local con Docker:

```bash
docker run --rm --name rabbitmq-local \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=tp3 \
  -e RABBITMQ_DEFAULT_PASS=tp3 \
  rabbitmq:3-management
```

En otra terminal, instalar `pika` y ejecutar el consumidor:

```bash
pip install pika
RABBITMQ_URL=amqp://tp3:tp3@localhost:5672/ CONSUMER_ID=local-1 python consumer.py
```

En otra terminal, ejecutar el productor:

```bash
RABBITMQ_URL=amqp://tp3:tp3@localhost:5672/ python producer.py
```

El productor envia 10 mensajes con el formato `Tarea N de 10`.

## Desplegar en k3d

El cluster del curso se llama `sobel`. Desde esta carpeta:

```bash
cd TP3/queue/ex1
```

Construir las imagenes locales:

```bash
docker build -f Dockerfile.producer -t rabbitmq-producer:ex1 .
docker build -f Dockerfile.consumer -t rabbitmq-consumer:ex1 .
```

Importar al cluster k3d solo las imagenes construidas localmente:

```bash
k3d image import rabbitmq-producer:ex1 -c sobel
k3d image import rabbitmq-consumer:ex1 -c sobel
```

No hace falta importar `rabbitmq:3-management`: es una imagen publica de Docker Hub y k3d la descarga automaticamente cuando se aplica el manifiesto.

En k3d no se usa `docker save`, archivos `.tar`, ni `sudo k3s ctr images import`. Ese flujo corresponde a k3s nativo sobre Linux, no al setup del curso en macOS con k3d.

Aplicar los manifiestos en orden:

```bash
kubectl apply -f manifests/rabbitmq-deployment.yaml
kubectl wait --for=condition=available deployment/rabbitmq --timeout=120s

kubectl apply -f manifests/consumer-deployment.yaml
kubectl wait --for=condition=available deployment/rabbitmq-consumer --timeout=120s

kubectl apply -f manifests/producer-job.yaml
kubectl wait --for=condition=complete job/rabbitmq-producer --timeout=120s
```

El orden importa: si el consumidor arranca antes de que RabbitMQ este listo, puede fallar la conexion y el Pod puede entrar en `CrashLoopBackOff`. El `kubectl wait` evita avanzar antes de que cada componente este disponible.

## Ver resultados

Logs del productor:

```bash
kubectl logs job/rabbitmq-producer
```

Logs del consumidor:

```bash
kubectl logs -f deployment/rabbitmq-consumer
```

## Experimento: 2 consumidores y round-robin

Escalar el consumidor a 2 replicas:

```bash
kubectl scale deployment/rabbitmq-consumer --replicas=2
```

Relanzar el Job del productor:

```bash
kubectl delete job rabbitmq-producer
kubectl apply -f manifests/producer-job.yaml
kubectl wait --for=condition=complete job/rabbitmq-producer --timeout=120s
```

Ver los logs de ambos consumidores con prefijo del Pod:

```bash
kubectl logs -f -l app=rabbitmq-consumer --prefix=true
```

Salida esperada aproximada:

```text
[pod/rabbitmq-consumer-xxxxx] 2026-04-29T12:00:01 [rabbitmq-consumer-xxxxx] Recibio: Tarea 1 de 10
[pod/rabbitmq-consumer-yyyyy] 2026-04-29T12:00:02 [rabbitmq-consumer-yyyyy] Recibio: Tarea 2 de 10
[pod/rabbitmq-consumer-xxxxx] 2026-04-29T12:00:03 [rabbitmq-consumer-xxxxx] Recibio: Tarea 3 de 10
[pod/rabbitmq-consumer-yyyyy] 2026-04-29T12:00:04 [rabbitmq-consumer-yyyyy] Recibio: Tarea 4 de 10
```

RabbitMQ distribuye los mensajes entre los consumidores disponibles. Con dos replicas, se espera observar que algunos mensajes los procese un Pod y otros mensajes el otro. La distribucion suele ser round-robin, aunque puede variar levemente segun tiempos de procesamiento y disponibilidad.

## ACK manual vs auto ACK

Este ejemplo usa `auto_ack=False`, que es el comportamiento cuando se llama a `basic_ack` manualmente despues de procesar cada mensaje.

Con ACK manual, RabbitMQ considera procesado el mensaje solo cuando el consumidor confirma con `basic_ack`. Si el consumidor muere antes de confirmar, RabbitMQ puede reenviar ese mensaje a otro consumidor.

Con `auto_ack=True`, RabbitMQ considera el mensaje entregado apenas lo manda al consumidor. Si el consumidor falla antes de procesarlo, el mensaje puede perderse. Por eso el ACK manual es importante en sistemas distribuidos.

## Comportamiento observado

Completar despues de ejecutar:

```text
Con 1 consumidor:
...

Con 2 consumidores:
...

Si se mata un consumidor durante el procesamiento:
...
```

## RabbitMQ Management UI

```bash
kubectl port-forward service/rabbitmq 15672:15672
```

Abrir `http://localhost:15672`.

- Usuario: `tp3`
- Password: `tp3`

## Limpiar recursos

```bash
kubectl delete -f manifests/producer-job.yaml
kubectl delete -f manifests/consumer-deployment.yaml
kubectl delete -f manifests/rabbitmq-deployment.yaml
```
