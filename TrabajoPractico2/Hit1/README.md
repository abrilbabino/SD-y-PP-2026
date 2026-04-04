# TrabajoPractico2 Hit1 - Remote Task Server

## Descripción
Servidor HTTP (FastAPI) que expone `/getRemoteTask` y arranca un contenedor Docker de servicio de tarea para ejecutar `ejecutarTarea`.

## Contenerización y Despliegue

### Construir y Ejecutar Localmente

1. Construir la imagen sample task service:
```bash
docker build -t local/task-service:latest sample_task_service
```

2. Construir la imagen del servidor:
```bash
docker build -t tp2-hit1-server .
```

3. Ejecutar el servidor (montando el socket de Docker):
```bash
docker run --rm -p 5000:5000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e DOCKER_HUB_USER=<usuario> \
  -e DOCKER_HUB_TOKEN=<token> \
  tp2-hit1-server
```

### Publicación en Docker Hub

La imagen se publica automáticamente via el job `tp2-hit1` en el pipeline CI/CD existente (`pipelineCI-CD.yml`).

Para configurar:
1. Ir a Settings > Secrets and variables > Actions en el repo
2. Agregar secrets:
   - `DOCKER_HUB_USERNAME`: tu usuario de Docker Hub
   - `DOCKER_HUB_TOKEN`: token de acceso (no contraseña)

El job `tp2-hit1`:
- Se ejecuta después del job `cd`
- Solo si hay cambios en `TrabajoPractico2/Hit1/` o en push a main
- Build y push la imagen a `${DOCKER_HUB_USERNAME}/tp2-hit1-server:latest`

### Ejecutar desde Docker Hub

```bash
docker run --rm -p 5000:5000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e DOCKER_HUB_USER=<usuario> \
  -e DOCKER_HUB_TOKEN=<token> \
  <tu_usuario>/tp2-hit1-server:latest
```

## Seguridad Docker Registro

- Usa variables de entorno `DOCKER_HUB_USER` y `DOCKER_HUB_TOKEN`.
- No envíes credenciales en payload.
- El login se hace automáticamente en el código si las variables están presentes.

## Test

```bash
pytest -q
```

## Crear y Subir Imagen del Task Service

1. Construir la imagen:
```bash
cd sample_task_service
docker build -t <tu_usuario>/servicio-tarea:latest .
```

2. Hacer login a Docker Hub:
```bash
docker login
```

3. Subir la imagen:
```bash
docker push <tu_usuario>/servicio-tarea:latest
```

4. En el cliente, usar:
```json
{
  "image": "<tu_usuario>/servicio-tarea:latest",
  "task": "sumar",
  "params": {"a": 3, "b": 5}
}
```
