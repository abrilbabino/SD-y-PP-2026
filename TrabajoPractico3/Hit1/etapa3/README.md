# Etapa 3 — Sobel Distribuido con Tolerancia a Fallas (Kubernetes)

## Arquitectura

Misma lógica de Etapa 2 (Master-Worker con RabbitMQ), con dos mejoras para tolerancia a fallas:

1. **ACK Manual (RabbitMQ)**: Los Workers usan `auto_ack=False` y hacen `basic_ack` solo después de publicar
   el resultado. Si un Worker muere antes del ACK, RabbitMQ re-encola el mensaje automáticamente.
2. **Kubernetes**: Los Workers corren como un `Deployment` (3 réplicas). Si un Pod muere, K8s lo reemplaza.
   El Master corre como un `Job`.

### Diagrama de flujo ante falla

```
1. Master publica 4 chunks en sobel_tasks
2. Worker-A toma chunk 2, empieza a procesar
3. Worker-A muere (Pod eliminado)
   → RabbitMQ detecta conexión cortada → re-encola chunk 2
   → K8s detecta Pod faltante → levanta Worker-D
4. Worker-B o Worker-C (o Worker-D) toma chunk 2 re-encolado
5. Master recibe los 4 resultados y ensambla la imagen
```

### Cambios respecto a Etapa 2

| Aspecto | Etapa 2 | Etapa 3 |
|---------|---------|---------|
| `auto_ack` | `True` (mensaje se pierde si el worker cae) | `False` (ACK manual tras publicar resultado) |
| `prefetch_count` | No configurado (sin límite) | `1` (un mensaje a la vez por worker) |
| Orquestación | Docker Compose | Kubernetes (Deployment + Job + StatefulSet) |
| Resiliencia | Ninguna | RabbitMQ re-encola + K8s reemplaza Pods |

## Archivos

```
etapa3/
├── master.py              # Master (Job en K8s)
├── worker.py              # Worker (Deployment en K8s)
├── Dockerfile             # Imagen compartida master/worker
├── requirements.txt       # Dependencias Python
└── k8s/
    ├── rabbitmq-statefulset.yaml   # Service + StatefulSet para RabbitMQ
    ├── worker-deployment.yaml      # Deployment con 3 réplicas
    └── master-job.yaml             # Job con initContainer + hostPath
```

## Prerrequisitos

- **k3d** instalado (K3s in Docker)
- Docker Desktop corriendo (k3d lo usa como runtime)
- `kubectl` configurado
- La imagen `inputSobel.jpeg` en `TrabajoPractico3/Hit1/`

## Despliegue paso a paso (k3d)

### 1. Crear el cluster k3d con volumen montado

```bash
k3d cluster create sobel-hit1 \
  --volume "C:\Users\Usuario\Documents\SD-Y-PP\SD-y-PP-2026\TrabajoPractico3\Hit1:/data/hit1@server:0"
```

> Esto monta la carpeta `Hit1` del host en `/data/hit1` dentro del nodo k3d.
> El Master accederá a `inputSobel.jpeg` y escribirá `outputSobel.png` desde ahí.

### 2. Construir la imagen Docker

```bash
cd TrabajoPractico3/Hit1/etapa3
docker build -t sobel-etapa3:latest .
```

### 3. Importar la imagen al cluster k3d

```bash
k3d image import sobel-etapa3:latest -c sobel-hit1
```

### 4. Aplicar los manifiestos

```bash
# Desde la carpeta etapa3/
kubectl apply -f k8s/rabbitmq-statefulset.yaml
kubectl apply -f k8s/worker-deployment.yaml

# Esperar a que RabbitMQ esté ready
kubectl wait --for=condition=ready pod -l app=rabbitmq --timeout=120s

# Lanzar el Master
kubectl apply -f k8s/master-job.yaml
```

### 5. Verificar ejecución

```bash
# Ver todos los pods
kubectl get pods -w

# Ver logs del master
kubectl logs job/sobel-master -f

# Ver logs de un worker
kubectl logs -l app=sobel-worker --tail=50
```

El Job del Master debe terminar con estado `Completed` y la imagen de salida
estará en `TrabajoPractico3/Hit1/outputSobel.png` (montado via el volumen k3d).

## Simulación de falla (prueba de tolerancia)

Para demostrar que la tolerancia a fallas funciona:

### Paso 1: Verificar Workers corriendo

```bash
kubectl get pods -l app=sobel-worker
# Deberías ver 3 pods en estado Running
```

### Paso 2: Matar un Worker mientras procesa

```bash
# Elegir un pod worker y eliminarlo forzosamente
kubectl delete pod <nombre-del-pod-worker> --grace-period=0 --force
```

### Paso 3: Verificar recuperación

```bash
# K8s levanta un nuevo Pod automáticamente
kubectl get pods -l app=sobel-worker -w

# El chunk no-ACKeado se re-encola en RabbitMQ
# Verificar en los logs que otro worker toma el chunk
kubectl logs -l app=sobel-worker --tail=20
```

### Paso 4: Confirmar resultado

```bash
# El master debe completar normalmente
kubectl get jobs
# NAME           COMPLETIONS   DURATION   AGE
# sobel-master   1/1           Xs         Xm
```

## Limpieza

```bash
# Opción rápida: eliminar todo el cluster k3d
k3d cluster delete sobel

# O bien, eliminar recursos individuales:
kubectl delete job sobel-master
kubectl delete deployment sobel-worker
kubectl delete statefulset rabbitmq
kubectl delete service rabbitmq-service
```

## Notas técnicas

- **`prefetch_count=1`**: Cada Worker toma un solo mensaje a la vez. Esto garantiza
  distribución justa y minimiza la pérdida de trabajo si un Worker cae.
- **`basic_ack` después de `basic_publish`**: El ACK se envía solo después de que
  el resultado fue publicado en `sobel_results`. Si el Worker muere entre el publish
  y el ack, el resultado puede duplicarse, pero es idempotente (`results[cid]` se sobreescribe).
- **`basic_nack(requeue=False)`**: Si un mensaje produce una excepción (ej: datos corruptos),
  se descarta sin re-encolarlo para evitar loops infinitos.
