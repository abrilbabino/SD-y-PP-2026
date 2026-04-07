# Hit2 - Worker Pool con Reloj de Lamport para Ejecución Remota de Tareas

## Descripción General

Este proyecto extiende el sistema de ejecución remota en contenedores Docker incorporando dos conceptos clave de sistemas distribuidos:

1. **Worker Pool** (`router3`): Pool de workers concurrentes que procesan tareas en paralelo mediante una cola compartida
2. **Reloj de Lamport**: Mecanismo de sincronización de timestamps lógicos para ordenar eventos en el sistema distribuido

El sistema permite recibir múltiples solicitudes simultáneas, encolarlas con un timestamp de Lamport asignado y distribuirlas entre los workers disponibles para su ejecución en contenedores Docker efímeros.

---

## Instrucciones de Ejecución

### Requisitos Previos

- **Python 3.10+** instalado
- **Docker** instalado y corriendo (daemon activo)
- **pip** para instalar dependencias Python

### Crear archivo `.env`**
Crear un archivo `.env` con la siguiente configuración:

```
DOCKER_HUB_TOKEN = Token de acceso personal generado en la cuenta de Docker Hub.
```
Donde:
- **DOCKER_HUB_TOKEN** → Se utiliza como contraseña en el proceso de autenticación del cliente Docker, permite que la aplicación tenga permiso para ejecutar docker pull sobre las imágenes necesarias para crear los contenedores que ejecutan las tareas.

```
DOCKER_HUB_USERNAME = Nombre de usuario de la cuenta en Docker Hub.
```

Donde:
- **DOCKER_HUB_USERNAME** →  Se utiliza para autenticarse contra el registro y permitir que el servidor pueda descargar imágenes privadas.
---

### Instalación de Dependencias

```bash
# Navegar a la carpeta del proyecto
cd TrabajoPractico2/Hit2

# Instalar dependencias
pip install fastapi uvicorn docker requests pydantic

# O usar el archivo requirements.txt si existe
pip install -r requirements.txt
```

### Levantar la API Principal

```bash
uvicorn api.main:app --host 0.0.0.0 --port 3000
```

El servidor estará disponible en `http://localhost:3000`

### Ejecutar una Tarea Remota

```bash
curl -X POST "http://localhost:3000/getRemoteTask2" \
  -H "Content-Type: application/json" \
  -d '{
    "image": "juanbrero/servicio-tarea:1.0",
    "task": "suma",
    "params": {"a": 1, "b": 2},
    "timestamp": 0
  }'
```

**Respuesta esperada:**
```json
{
  "lamport_ts": 3,
  "result": {"result": 3}
}
```

### Probar Concurrencia (PowerShell)

Para simular múltiples requests simultáneos y verificar el comportamiento del worker pool:

```powershell
# Lanzar 8 requests en paralelo
1..8 | ForEach-Object {
  Start-Job {
    Invoke-RestMethod -Uri "http://localhost:3000/getRemoteTask2" `
      -Method POST `
      -ContentType "application/json" `
      -Body '{"image":"juanbrero/servicio-tarea:1.0","task":"suma","params":{"a":1,"b":2},"timestamp":0}'
  }
}

# Esperar a que terminen todos los jobs
Get-Job | Wait-Job

# Ver resultados
Get-Job | Receive-Job
```
### Depuración

Para monitorear los contenedores que se crean y destruyen:

```bash
# En otra terminal, ver contenedores en tiempo real
docker ps -a --follow

# Ver logs de un contenedor específico
docker logs <container_id>

# Ver todas las imágenes disponibles
docker images
```

---

## Diagrama de Arquitectura
LINK

## Reloj de Lamport

### Funcionamiento

El reloj de Lamport implementado sigue las reglas clásicas del algoritmo:

```
Al enviar un evento:     clock += 1
Al recibir un evento:    clock = max(clock_local, clock_recibido) + 1
```

### Implementación en el Código

```python
lamport_clock = 0

def increment_clock(received_ts=None):
    global lamport_clock
    with queue_lock:
        if received_ts is not None:
            lamport_clock = max(lamport_clock, received_ts)
        lamport_clock += 1
        return lamport_clock
```

### Flujo de Timestamps

```
Cliente envía timestamp=0  →  servidor calcula max(0, 0)+1 = 1  →  encola con TS=1
Cliente envía timestamp=5  →  servidor calcula max(1, 5)+1 = 6  →  encola con TS=6
Cliente envía timestamp=3  →  servidor calcula max(6, 3)+1 = 7  →  encola con TS=7
```

La respuesta siempre incluye el `lamport_ts` actualizado para que el cliente pueda sincronizar su propio reloj.

---

## Decisiones de Diseño

### 1. **Worker Pool con Threads**
   - **Decisión**: Crear `MAX_WORKERS = 4` threads daemon al arrancar el servidor
   - **Razón**:
     - Permite procesar hasta 4 tareas en paralelo sin crear un thread por request
     - Los threads daemon se destruyen automáticamente al cerrar el proceso principal
     - Evita la sobrecarga de crear/destruir threads constantemente
   - **Trade-off**: límite fijo de concurrencia vs. mayor control de recursos

### 2. **Cola Compartida (task_queue)**
   - **Decisión**: Usar `queue.Queue()` de Python (thread-safe) como buffer de tareas
   - **Razón**:
     - Implementación FIFO thread-safe sin locking manual
     - Desacopla la recepción de requests de su ejecución
     - Permite absorber picos de carga (backpressure natural)
   - **Comportamiento**: si los 4 workers están ocupados, las tareas esperan en cola

### 3. **Reloj de Lamport para Ordenamiento**
   - **Decisión**: Implementar reloj de Lamport con timestamp opcional en el request
   - **Razón**:
     - Permite ordenar causalmente los eventos en un sistema distribuido
     - El cliente puede proporcionar su timestamp local para sincronización
     - Si `timestamp=0` o `None`, el servidor asigna el siguiente valor local
   - **Protección de concurrencia**: `queue_lock` garantiza que la actualización del reloj sea atómica

### 4. **Espera Bloqueante con Polling**
   - **Decisión**: El endpoint bloquea con `while task["result"] is None: time.sleep(0.05)`
   - **Razón**:
     - Simplicidad: el cliente recibe el resultado directamente en la misma conexión HTTP
     - Evita la necesidad de un sistema de callbacks o webhooks
     - Intervalos de 50ms ofrecen buen balance entre latencia y CPU
   - **Limitación**: puede generar timeouts en clientes con ventanas cortas si la cola está saturada

### 5. **Aislamiento por Contenedor con Auto-eliminación**
   - **Decisión**: cada tarea levanta su propio contenedor con `remove=True`
   - **Razón**:
     - Aislamiento total entre tareas concurrentes
     - Sin acumulación de contenedores detenidos
     - Permite escalar workers sin conflictos de recursos
   - **Puerto dinámico**: `ports={'5000/tcp': None}` evita colisiones entre contenedores simultáneos

### 6. **Lock Compartido para Cola y Reloj**
   - **Decisión**: reutilizar `queue_lock` tanto para proteger el reloj como para encolar tareas
   - **Razón**:
     - Garantiza que el timestamp asignado a una tarea sea coherente con su posición en la cola
     - Evita condiciones de carrera donde dos tareas podrían recibir el mismo timestamp

---

## Flujo de Ejecución Detallado

```
1.  Cliente envía: POST /getRemoteTask2 con {image, task, params, timestamp}
                   ↓
2.  Servidor actualiza Reloj de Lamport: max(clock, timestamp) + 1
                   ↓
3.  Servidor crea objeto task con timestamp asignado y result=None
                   ↓
4.  Servidor encola la tarea en task_queue (thread-safe)
                   ↓
5.  Servidor entra en loop de polling (cada 50ms)
                   ↓
6.  Worker disponible toma la tarea de la cola
                   ↓
7.  Worker descarga imagen Docker (si no está cacheada)
                   ↓
8.  Worker levanta contenedor con puerto dinámico
                   ↓
9.  Worker espera 2s + loop de reintentos para obtener puerto
                   ↓
10. Worker envía POST a localhost:{puerto}/EjecutarTarea
                   ↓
11. Contenedor ejecuta la tarea y devuelve {"result": valor}
                   ↓
12. Worker escribe resultado en task["result"]
                   ↓
13. Worker detiene/destruye el contenedor (remove=True)
                   ↓
14. Loop de polling del endpoint detecta result != None
                   ↓
15. Servidor actualiza Reloj de Lamport y devuelve {lamport_ts, result}
```
