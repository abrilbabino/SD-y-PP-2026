
# Hit3: Coordinación y Tolerancia a Fallos

## Descripción General

Hit3 es un sistema distribuido que implementa **elección de líder descentralizada** y **orquestación dinámica de contenedores Docker**. 

El sistema consta de:
- **3 workers** que se comunican entre sí mediante HTTP
- **Mecanismo de elección de líder**: elige dinámicamente cuál worker actúa como coordinador
- **Orquestación de contenedores**: cada worker puede levantar contenedores Docker para ejecutar tareas en paralelo
- **Balanceador de carga (Nginx)**: distribuye las solicitudes entre los workers
- **Monitoreo y recuperación automática**: detecta cuando el líder falla y reinicia una elección

## Arquitectura

link


## Inicio Rápido

### Requisitos
- Docker y Docker Compose instalados
- PowerShell o terminal compatible

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

### Levantar el sistema
```powershell
cd TrabajoPractico2/Hit3
docker-compose up -d --build
Start-Sleep -Seconds 10
```

(El retraso de 10 segundos permite que los workers establezcan la comunicación inicial y elijan un líder)

##  Pruebas del Sistema

### Fase 1: Todos los workers corriendo

Verifica que los 3 workers estén en línea y que uno de ellos sea elegido como líder:

```powershell
iwr http://localhost:8001/status -UseBasicParsing | Select-Object -ExpandProperty Content
iwr http://localhost:8002/status -UseBasicParsing | Select-Object -ExpandProperty Content
iwr http://localhost:9000/status -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Salida esperada:**
```json
{"worker_id":1,"leader_id":3,"is_busy":false}
{"worker_id":2,"leader_id":3,"is_busy":false}
{"worker_id":3,"leader_id":3,"is_busy":false}
```

En este caso, Worker 3 es el líder elegido.

### Fase 2: Simular caída del líder

Detén el worker que actúa como líder:

```powershell
docker-compose stop worker3
Start-Sleep -Seconds 6
```

Verifica que los workers restantes **eligieron un nuevo líder**:

```powershell
iwr http://localhost:8001/status -UseBasicParsing | Select-Object -ExpandProperty Content
iwr http://localhost:8002/status -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Salida esperada:**
```json
{"worker_id":1,"leader_id":2,"is_busy":false}
{"worker_id":2,"leader_id":2,"is_busy":false}
```

Worker 2 ha sido elegido como nuevo líder.

### Fase 3: Recuperación

Reinicia el worker que se cayó:

```powershell
docker-compose start worker3
Start-Sleep -Seconds 8
```

Verifica que el sistema se **recuperó completamente**:

```powershell
iwr http://localhost:8001/status -UseBasicParsing | Select-Object -ExpandProperty Content
iwr http://localhost:8002/status -UseBasicParsing | Select-Object -ExpandProperty Content
iwr http://localhost:9000/status -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Salida esperada:**
```json
{"worker_id":1,"leader_id":3,"is_busy":false}
{"worker_id":2,"leader_id":3,"is_busy":false}
{"worker_id":3,"leader_id":3,"is_busy":false}
```

El sistema vuelve a su estado original.

## Ejecutar una Tarea

### Interfaz web

1. Abre el navegador en `http://localhost:8080/test3`
2. Espera **10 segundos** a que se cargue la interfaz
3. Selecciona una tarea (suma, multiplicación, potencia)
4. Ingresa los parámetros
5. Presiona "Ejecutar"

### Cómo funciona

1. La solicitud se envía a Nginx (puerto 8080)
2. Nginx la distribuye a uno de los 3 workers
3. Si el worker no es el líder, reenvía la solicitud al líder
4. El líder **busca un worker disponible** (no ocupado)
5. El líder solicita al worker disponible que **levante un contenedor Docker** con la imagen especificada
6. El contenedor ejecuta la tarea y devuelve el resultado
7. El contenedor se **elimina automáticamente** para liberar recursos


## Endpoints del Sistema

### GET `/status`
Devuelve el estado actual del worker.

**Respuesta:**
```json
{
  "worker_id": 1,
  "leader_id": 3,
  "is_busy": false
}
```

### POST `/asignar_tarea`
Asigna una tarea al sistema. El líder la ejecutará.

**Body:**
```json
{
  "image": "nombre-imagen-docker",
  "task": "suma",
  "params": {"a": 5, "b": 3}
}
```

**Tareas soportadas:**
- `suma`: suma dos números
- `multiplicacion`: multiplica dos números
- `potencia`: calcula a elevado a b

### POST `/coordinador`
Recibe notificación del líder cuando hay cambios.

### GET `/test3`
Devuelve la interfaz HTML para probar el sistema de forma interactiva.

## Mecanismo de Elección de Líder

El sistema implementa una **estrategia de elección descentralizada**:

1. Se ordenan los workers por ID (de mayor a menor)
2. Se intenta contactar a cada worker en ese orden
3. El primer worker que responde se convierte en líder
4. El líder se **notifica a todos los otros** workers
5. Un monitor en cada worker verifica cada 5 segundos si el líder sigue vivo
6. Si el líder no responde, se inicia una nueva elección automáticamente

## Orquestación de Contenedores

Cuando un worker recibe una tarea:

1. **Descarga la imagen Docker** (si no está local)
2. **Levanta un contenedor** con un puerto dinámico
3. **Ejecuta la tarea** enviando HTTP POST al contenedor
4. **Detiene y elimina el contenedor** (libera recursos)

Esto permite ejecutar **múltiples tareas en paralelo** sin interferencia.

## Configuración

### Variables de Entorno

Cada worker recibe un `WORKER_ID` único definido en `docker-compose.yml`:

```yaml
environment:
  - WORKER_ID=1
```

### Puertos

- **Nginx (balanceador):** `8080`
- **Worker 1:** `8001` (interno: 8000)
- **Worker 2:** `8002` (interno: 8000)
- **Worker 3:** `9000` (interno: 8000)


## Monitoreo

Los workers imprimen logs de:
- Elecciones de líder
- Cambios de estado
- Tareas ejecutadas
- Errores de conectividad

Visualiza los logs con:

```powershell
docker-compose logs -f
```

## Decisiones de Diseño

### Elección de Líder
- **Algoritmo simple**: Se ordenan los workers por ID descendente y el primero que responde se convierte en líder
- **Ventaja**: Fácil de implementar y entender
- **Desventaja**: No es el algoritmo más eficiente (como Bully o Ring), pero suficiente para 3 nodos
- **Justificación**: Para un sistema pequeño, la simplicidad prima sobre la complejidad

### Comunicación entre Workers
- **Protocolo HTTP**: Comunicación síncrona mediante REST API
- **Ventaja**: Simple, no requiere middleware adicional
- **Desventaja**: No maneja reconexiones automáticas avanzadas
- **Justificación**: Suficiente para un sistema de prueba; en producción se usaría gRPC o message queues

### Gestión de Estado
- **Variables globales en memoria**: Estado del worker (ID, líder, ocupado)
- **Ventaja**: Rápido acceso, simple
- **Desventaja**: No persistente; se pierde al reiniciar
- **Justificación**: Para un sistema de demostración, la persistencia no es crítica

### Orquestación de Contenedores
- **Contenedores efímeros**: Se crean por tarea y se destruyen inmediatamente
- **Ventaja**: Aislamiento completo, no hay contaminación entre tareas
- **Desventaja**: Overhead de creación/destrucción
- **Justificación**: Ideal para tareas independientes; maximiza recursos y seguridad

### Monitoreo y Recuperación
- **Polling cada 5 segundos**: Cada worker verifica si el líder responde
- **Ventaja**: Simple implementación
- **Desventaja**: No es real-time; latencia de hasta 5 segundos
- **Justificación**: Adecuado para sistemas no críticos; en producción se usaría heartbeats o WebSockets

### Balanceo de Carga
- **Nginx round-robin**: Distribución equitativa de solicitudes
- **Ventaja**: Configuración simple, confiable
- **Desventaja**: No considera carga real de workers
- **Justificación**: Suficiente para distribución básica; para producción se usaría load balancing inteligente

### Autenticación Docker
- **Opcional con tokens**: Soporte para Docker Hub privado
- **Ventaja**: Permite usar imágenes privadas
- **Desventaja**: Requiere configuración manual
- **Justificación**: Flexibilidad para diferentes entornos de despliegue

### Arquitectura General
- **Sin base de datos**: Todo en memoria
- **Ventaja**: Simplicidad, rápido desarrollo
- **Desventaja**: No escalable, datos se pierden
- **Justificación**: Sistema de prueba/demostración, no para producción
