from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import docker
import requests
import time
import os

router2 = APIRouter()

# creo un cliente que interactua con el daemon de docker local (debe estar corriendo). no inicia docker, solo se conecta a él para pedirle que ejecute contenedores.
client = docker.from_env()

# Autenticación Docker Hub si hay credenciales
token = os.environ.get("DOCKER_HUB_TOKEN")
username = os.environ.get("DOCKER_HUB_USER")
if token and username:
    try:
        client.login(username=username, password=token)
        print("Docker Hub login successful")
    except Exception as e:
        print(f"Docker Hub login failed: {e}")
else:
    print("No Docker Hub credentials provided, using local auth")


# esto es un modelo de datos que define la estructura del request que se espera recibir en el endpoint. FastAPI lo usa para validar y parsear el JSON entrante.
# convierte automáticamente el JSON del request en una instancia de TaskRequest, con los campos image, task y params. 
class TaskRequest(BaseModel):
    image: str
    task: str
    params: dict


'''la idea es que cada vez que se recibe una solicitud para ejecutar una tarea, se levanta un nuevo contenedor con la imagen especificada,
se le asigna un puerto dinámico, y se invoca el endpoint /execute del servicio dentro del contenedor para que ejecute la tarea con los parámetros dados.
Luego se devuelve la respuesta al cliente y se detiene el contenedor para liberar recursos.'''

@router2.post("/getRemoteTask")
def ejecutarTareaRemota(req: TaskRequest):
    
    # esta es la referencia al contenedor que se va a levantar. Se inicializa en None para poder manejar el caso de error 
    # donde no se levanta el contenedor y evitar intentar detener algo que no existe.
    container = None
    try:
        # descargar imagen (si no está local) o usarla si ya está descargada. Esto es necesario para poder levantar el contenedor con esa imagen.
        client.images.pull(req.image)

        # levantar contenedor con la imagen especificada, en modo detached (en segundo plano, seria el parametro -d en la terminal),
        # asignando un puerto dinámico para exponer el servicio que va a correr dentro del contenedor.
        # lo que hace es mapear el puerto 5000 del contenedor a un puerto aleatorio del host, que es el que se va a usar para comunicarse con el servicio dentro del contenedor.
        # remove=True hace que el contenedor se elimine automáticamente cuando se detiene, para no acumular contenedores detenidos.
        container = client.containers.run(
            req.image,
            detach=True,
            ports={'5000/tcp': None},  # puerto dinámico
            remove=True
        )

        # una vez que el contenedor esta levantado, se refresca el estado del contenedor para obtener la información actualizada,
        # incluyendo el puerto asignado dinámicamente. Esto es necesario porque el puerto se asigna en el momento de levantar el contenedor y no se conoce de antemano.
        container.reload()

        port = container.attrs['NetworkSettings']['Ports']['5000/tcp'][0]['HostPort']

        # esperar a que el servicio esté listo
        time.sleep(2)

        # hacer la solicitud al servicio dentro del contenedor para ejecutar la tarea.
        # Se hace una solicitud POST al endpoint /EjecutarTarea del servicio, pasando el nombre de la tarea y los parámetros en el cuerpo de la solicitud.
        # es decir, el server hace un HTTP POST al contenedor recién levantado, diciéndole que ejecute la tarea que se le pidió ejecutar a este server, con los parámetros dados.
        response = requests.post(
            f"http://localhost:{port}/EjecutarTarea",
            json={
                "task": req.task,
                "params": req.params
            },
            timeout=10
        )

        # devuelve la respuesta al cliente original, por lo que el servidor actua como un intermedioario o una especie de proxy.
        return response.json()

    except Exception as e:
        # en caso de cualquier error, se devuelve un error 500 con el detalle del error.
        # Esto puede incluir errores al levantar el contenedor, errores de conexión, errores en la solicitud al servicio dentro del contenedor, etc.
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # independientemente de si hubo un error o no, se intenta detener el contenedor para liberar recursos. Si el contenedor no se levantó correctamente,
        # container seguirá siendo None y se evitará intentar detenerlo.
        if container:
            try:
                container.stop()
            except:
                pass



@router2.get("/test")
def test():
    return FileResponse("api/static/index.html")
