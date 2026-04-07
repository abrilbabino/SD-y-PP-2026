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
# Instalar dependencias del servidor principal
pip install fastapi uvicorn docker requests pydantic

# O usar el archivo requirements.txt si existe
pip install -r requirements.txt
```

### Ejecutar el Servidor Principal 

```bash
# Opción 1: Con uvicorn directamente
uvicorn api.main:app --host 0.0.0.0 --port 3000
```
El servidor estará disponible en `http://localhost:3000/test`

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

```json
{"result": 28}
```  

```json
{"result": 256}
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
https://drive.google.com/file/d/1Ay3mVwRVHgSczJeYEBlt38s3qhZpKXjT/view?usp=sharing
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

