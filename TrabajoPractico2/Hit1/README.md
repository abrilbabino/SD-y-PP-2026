# Hit1 - Ejecución Remota de Tareas en Contenedores Docker

## Descripción General

Este proyecto implementa un sistema distribuido que permite ejecutar tareas remotas dentro de contenedores Docker bajo demanda. La arquitectura comprende dos componentes principales:

1. **Servidor Principal** (`server.py`): Orquestador que levanta contenedores dinámicamente para ejecutar tareas
2. **Servicio de Tarea** (`servicio_tarea.py`): Microservicio que ejecuta operaciones matemáticas dentro del contenedor

El sistema permite una escalabilidad eficiente al crear instancias de contenedores solo cuando se necesitan, ejecutar la tarea solicitada y luego destruir el contenedor para liberar recursos.

---

## Instrucciones de Ejecución

### Requisitos Previos

- **Python 3.10+** instalado
- **Docker** instalado y corriendo (daemon activo)
- **pip** para instalar dependencias Python

### Instalación de Dependencias

```bash
# Navegar a la carpeta del proyecto
cd TrabajoPractico2/Hit1

# Instalar dependencias del servidor principal
pip install fastapi uvicorn docker requests pydantic

# O usar el archivo requirements.txt si existe
pip install -r requirements.txt
```

### Construir la Imagen Docker

La imagen Docker contiene el servicio de tarea que se ejecutará en los contenedores:

```bash
# Desde la carpeta Hit1
docker build -t servicio-tarea:latest .
```

Verificar que la imagen se creó correctamente:

```bash
docker images | grep servicio-tarea
```

### Ejecutar el Servidor Principal    (VER, PORQUE EN REALIDAD SE LEVANTA EL API MAIN)

```bash
# Opción 1: Con uvicorn directamente
uvicorn server:router2 --host 0.0.0.0 --port 8000

# Opción 2: Con Python (si tienes main.py que importa el router)
python server.py
```

El servidor estará disponible en `http://localhost:8000`

### Ejecutar una Tarea Remota

```bash
# Ejemplo: Sumar dos números
curl -X POST "http://localhost:8000/getRemoteTask" \
  -H "Content-Type: application/json" \
  -d '{
    "image": "servicio-tarea:latest",
    "task": "suma",
    "params": {"a": 5, "b": 3}
  }'

# Ejemplo: Multiplicación
curl -X POST "http://localhost:8000/getRemoteTask" \
  -H "Content-Type: application/json" \
  -d '{
    "image": "servicio-tarea:latest",
    "task": "multiplicacion",
    "params": {"a": 4, "b": 7}
  }'

# Ejemplo: Potencia
curl -X POST "http://localhost:8000/getRemoteTask" \
  -H "Content-Type: application/json" \
  -d '{
    "image": "servicio-tarea:latest",
    "task": "potencia",
    "params": {"a": 2, "b": 8}
  }'
```

**Respuesta esperada:**
```json
{"result": 8}
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

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENTE HTTP                             │
│              (curl, Postman, navegador, etc)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ POST /getRemoteTask
                         │ {image, task, params}
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVIDOR PRINCIPAL                            │
│                    (server.py - localhost:8000)                  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  1. Valida request (TaskRequest model)                    │ │
│  │  2. Autentica con Docker Hub (si es necesario)            │ │
│  │  3. Descarga/valida imagen Docker                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                         │                                        │
│                         ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  4. Levanta contenedor con puerto dinámico mapeado         │ │
│  │  5. Espera a que el servicio dentro esté listo (2s)        │ │
│  │  6. Obtiene puerto asignado dinámicamente                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                         │                                        │
│                         ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  7. HTTP POST a http://localhost:{puerto}/EjecutarTarea   │ │
│  │     con {task, params}                                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                         │                                        │
└─────────────────────────┼────────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
   ┌─────────────────┐         ┌──────────────────────┐
   │ Docker Daemon   │         │ CONTENEDOR TEMPORAL  │
   │ (en el host)    │────────▶│ (servicio_tarea.py) │
   └─────────────────┘         │                      │
                               │ Puerto: 5000 (interno)
                               │ Puerto: XXXX (host)  │
                               │                      │
                               │ ┌──────────────────┐ │
                               │ │ Servicio FastAPI │ │
                               │ │ /EjecutarTarea   │ │
                               │ │ - suma           │ │
                               │ │ - multiplicación │ │
                               │ │ - potencia       │ │
                               │ └──────────────────┘ │
                               └──────────────────────┘
                                        │
                                        ▼
                               Devuelve resultado
                               {"result": valor}
                                        │
(Contenedor se destruye automáticamente)│
                                        │
          ┌─────────────────────────────┘
          │
          ▼
┌────────────────────────────┐
│   SERVIDOR PRINCIPAL       │
│   (procesa respuesta)      │
└────────────────────────────┘
          │
          ▼
      ┌────────┐
      │ CLIENTE│
      │Respuesta
      │{result}
      └────────┘
```

---

## Decisiones de Diseño

### 1. **Orquestación Dinámica de Contenedores**
   - **Decisión**: Levantar un nuevo contenedor por cada solicitud de tarea
   - **Razón**: 
     - Aislamiento de recursos: cada tarea corre en su propio entorno
     - Escalabilidad: podemos procesar múltiples tareas en paralelo
     - Limpieza automática: `remove=True` evita acumular contenedores detenidos
   - **Trade-off**: mayor latencia inicial (levantamiento del contenedor) vs. mayor aislamiento

### 2. **Mapeo Dinámico de Puertos**
   - **Decisión**: Asignar un puerto del host aleatorio que se mapea al puerto 5000 del contenedor
   - **Razón**:
     - Permite ejecutar múltiples contenedores simultáneamente sin conflictos de puerto
     - El puerto exacto se obtiene dinámicamente tras levantar el contenedor
   - **Implementación**: `ports={'5000/tcp': None}` en `client.containers.run()`

### 3. **Autenticación Opcional con Docker Hub**
   - **Decisión**: Intentar autenticar con Docker Hub usando variables de entorno
   - **Razón**:
     - Permite usar imágenes privadas
     - No falla si las credenciales no están disponibles (usa imágenes públicas/locales)
   - **Variables de entorno requeridas**: `DOCKER_HUB_TOKEN`, `DOCKER_HUB_USERNAME`

### 4. **Tiempo de Espera (Sleep) Explícito**
   - **Decisión**: `time.sleep(2)` inicial + loop de reintentos para obtener el puerto
   - **Razón**:
     - Los contenedores necesitan tiempo para iniciarse completamente
     - El puerto podría no estar disponible inmediatamente
   - **Mejora**: Loop de reintentos (10 intentos, 0.5s cada uno) para obtener el puerto de forma robusta

### 5. **Arquitectura de Servidor y Servicio Separados**
   - **Decisión**: `server.py` (orquestador) y `servicio_tarea.py` (worker) en archivos separados
   - **Razón**:
     - Separación de responsabilidades
     - `servicio_tarea.py` se encapsula en la imagen Docker
     - `server.py` puede escalar a múltiples workers
   - **Flujo**: Cliente → server.py → Docker → contenedor:5000/servicio_tarea.py

### 6. **Modelos Pydantic para Validación**
   - **Decisión**: Usar `BaseModel` de Pydantic para `TaskRequest` y `TaskInput`
   - **Razón**:
     - Validación automática de tipos en el request
     - Documentación automática (OpenAPI)
     - Mejor manejo de errores
     - Type hints para mejor IDE support

### 7. **Operaciones Matemáticas Soportadas**
   - **Tareas implementadas**: suma, multiplicación, potencia
   - **Extensibilidad**: la función `ejecutarTarea()` puede extenderse fácilmente con nuevas operaciones
   - **Formato**: cada tarea requiere parámetros específicos en el diccionario `params`

### 8. **Timeout en Requests HTTP**
   - **Decisión**: `timeout=10` en el request al contenedor
   - **Razón**: Evitar que el servidor principal se quede esperando indefinidamente si el contenedor no responde
   - **Manejo de errores**: Deberia capturarse la excepción para operaciones más robustas

---

## Flujo de Ejecución Detallado

```
1. Cliente envía: POST /getRemoteTask con {image, task, params}
                  ↓
2. Server valida TaskRequest
                  ↓
3. Server intenta login en Docker Hub (si hay credenciales)
                  ↓
4. Server descarga imagen si no está disponible localmente
                  ↓
5. Server crea contenedor con:
   - Imagen especificada
   - Puerto 5000 mapeado dinámicamente
   - Auto-eliminación al detener (remove=True)
                  ↓
6. Server espera 2 segundos
                  ↓
7. Server obtiene puerto asignado (con reintentos)
                  ↓
8. Server envía: HTTP POST a localhost:{puerto}/EjecutarTarea
                  ↓
9. Contenedor recibe solicitud y ejecuta tarea
                  ↓
10. Contenedor devuelve: {"result": valor}
                  ↓
11. Server devuelve respuesta al cliente
                  ↓
12. Contenedor se destruye automáticamente
```

---

## Casos de Uso

### Caso 1: Computación Pesada
- Levantar un contenedor especializado con librerías científicas para ejecutar cálculos complejos
- Útil para procesamiento de datos bajo demanda

### Caso 2: Integración Heterogénea
- Ejecutar servicios en diferentes lenguajes/entornos en contenedores separados
- El servidor actúa como punto de entrada común

### Caso 3: Testing Distribuido
- Cada test corre en su propio contenedor aislado
- Garantiza que los tests no interfieren entre sí

### Caso 4: Escalado Horizontal
- Múltiples servidores principales distribuidos
- Todos orquestando contenedores en diferentes hosts con Docker

---

## Limitaciones y Mejoras Futuras

### Limitaciones Actuales
1. Sin persistencia de datos entre contenedores
2. Sin límites de recursos (CPU, memoria) en contenedores
3. Sin logging centralizado de tareas
4. Sin retry automático si el contenedor falla

### Mejoras Sugeridas
1. Agregar limits en recursos (`cpu_quota`, `mem_limit`)
2. Implementar logging estructurado con ELK stack
3. Agregar base de datos para persistencia de resultados
4. Implementar queue de tareas (RabbitMQ, Celery)
5. Health checks antes de ejecutar tareas
6. Métricas y monitoreo (Prometheus)

---

## Troubleshooting

| Problema | Causa | Solución |
|----------|-------|----------|
| `ConnectionError: Cannot connect to Docker daemon` | Docker no está corriendo | Verificar: `docker ps` |
| `404 Client Error: Image not found` | Imagen no existe | `docker build -t servicio-tarea:latest .` |
| `Port is already in use` | Puerto ocupado | Cambiar puerto en uvicorn o liberar el puerto |
| `TimeoutError` en request a contenedor | Servicio dentro no responde | Aumentar `time.sleep()` o `timeout` |
| `No Docker Hub credentials provided` | Variables de entorno no configuradas | Opcional; usa imágenes públicas o locales |

