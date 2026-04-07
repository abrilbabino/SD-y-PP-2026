from fastapi import APIRouter, HTTPException 
from fastapi.responses import FileResponse
from pydantic import BaseModel 
import docker 
import requests 
import time
import os 
import threading

router4 = APIRouter() 
# creo un cliente que interactua con el daemon de docker local (debe estar corriendo). 
# no inicia docker, solo se conecta a él para pedirle que ejecute contenedores.
try:
    client = docker.from_env()
except Exception as e:
    print(f"Advertencia: No se pudo conectar a Docker: {e}")
    client = None

# Autenticación Docker Hub si hay credenciales 
token = os.environ.get("DOCKER_HUB_TOKEN")
username = os.environ.get("DOCKER_HUB_USERNAME") 


if token and username:
    try: 
        client.login(username=username, password=token)
        print("Docker Hub login successful") 
        
    except Exception as e:
        print(f"Docker Hub login failed: {e}")
        
else: 
    print("No Docker Hub credentials provided, using local auth")
    

# esto es un modelo de datos que define la estructura del request que se espera recibir en el endpoint.
# FastAPI lo usa para validar y parsear el JSON entrante. 
# convierte automáticamente el JSON del request en una instancia de TaskRequest, con los campos image, task y params.

class TaskRequest(BaseModel): 
    image: str
    task: str
    params: dict

# VARIABLES DE ESTADO DEL WORKER

# ID del worker obtenido desde variable de entorno. Esto es útil para identificar cada worker 
# en un sistema distribuido, especialmente si hay múltiples instancias de este servidor corriendo en paralelo.
worker_id = int(os.environ.get("WORKER_ID", "1"))

# ID del líder actual del sistema.
# Puede cambiar si se realiza una nueva elección.
leader_id = None

# Indica si el worker está ocupado ejecutando una tarea.
is_busy = False

# Lista de workers conocidos en el sistema.
# Se usa para consultar estado y realizar elección de líder.
# Cada worker conoce la dirección de los otros nodos.
WORKERS = [
    {"id": 1, "url": "http://worker1:8000"},
    {"id": 2, "url": "http://worker2:8000"},
    {"id": 3, "url": "http://worker3:8000"},
]

# -------------------------------------------------------------------
# FUNCION DE ELECCIÓN DE LÍDER
# -------------------------------------------------------------------

def elegir_lider():
    """
    Implementa una elección de coordinador.

    Estrategia:
    - Se ordenan los workers de mayor a menor ID.
    - Se consulta el endpoint /status de cada worker.
    - El primer worker que responda se convierte en líder.

    Esto evita definir el coordinador manualmente y permite
    recuperar el sistema si el líder actual cae.
    """

    global leader_id

    #lambda es una función anónima que se usa para ordenar la lista de workers por su ID de mayor a menor.
    #reverse=True indica que el orden es descendente.
    workers_ordenados = sorted(WORKERS, key=lambda x: x["id"], reverse=True)

    for w in workers_ordenados:
        try:
            # Si el worker en la lista es yo mismo, asignarme como líder sin hacer GET
            if w["id"] == worker_id:
                leader_id = w["id"]
                print(f"[Elección] Yo soy el líder (Worker {leader_id})")
                # Notificar a todos los workers el nuevo líder
                notificar_lider(leader_id)
                return leader_id
            
            r = requests.get(f"{w['url']}/status", timeout=2)
            if r.status_code == 200:
                leader_id = w["id"]
                print(f"[Elección] Líder elegido: Worker {leader_id}")
                # Notificar a todos los workers el nuevo líder
                notificar_lider(leader_id)
                return leader_id
        except Exception as e:
            print(f"[Elección] No se pudo contactar a {w['url']}: {e}")
            continue

    print(f"[Elección] No se pudo elegir un líder")
    return None


def notificar_lider(new_leader_id):
    """Notifica a todos los workers cuál es el nuevo líder"""
    for w in WORKERS:
        try:
            requests.post(
                f"{w['url']}/coordinador",
                json={"leader": new_leader_id},
                timeout=1
            )
        except:
            pass  # Ignorar errores de notificación


def get_leader():
    return next((w for w in WORKERS if w["id"] == leader_id), None)


def asignar_Tarea_Worker(worker, req: TaskRequest):
    """Enviar la tarea a un worker remoto."""
    resp = requests.post(
        f"{worker['url']}/getRemoteTask3",
        json=req.model_dump(),
        timeout=20
    )

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Worker {worker['id']} respondió con error")

    return resp.json()


def encontrar_worker_disponible():
    """Buscar el primer worker libre en la lista."""
    for worker in WORKERS:
        try:
            r = requests.get(f"{worker['url']}/status", timeout=2)
            if r.status_code == 200:
                estado = r.json()
                if not estado.get("is_busy", True):
                    return worker
        except:
            continue

    return None


# -------------------------------------------------------------------
# ENDPOINTS
# -------------------------------------------------------------------

@router4.get("/status")
def status():
    """Devuelve el estado del worker."""
    return {"worker_id": worker_id, "leader_id": leader_id, "is_busy": is_busy}

@router4.post("/coordinador")
def coordinador(data: dict):
    """Recibe notificación del líder desde otro worker y actualiza estado local."""
    global leader_id
    new_leader = data.get("leader")
    if new_leader is not None:
        leader_id = new_leader
        print(f"[Coordinador] Líder actualizado a: {new_leader}")
    return {"status": "ok", "leader_id": leader_id}


@router4.post("/asignar_tarea")
def asignar_tarea(req: TaskRequest):

    global leader_id

    # Caso 1: soy el líder
    if leader_id == worker_id:

        worker = encontrar_worker_disponible()

        if worker is None:
            raise HTTPException(status_code=503, detail="No hay workers disponibles")

        result = asignar_Tarea_Worker(worker, req)

        return {
            "msg": f"Tarea asignada al worker {worker['id']}",
            "result": result
        }

    # Caso 2: no soy el líder → reenviar
    leader = get_leader()

    if leader is None:
        raise HTTPException(status_code=503, detail="No hay líder conocido")

    try:
        r = requests.post(
            f"{leader['url']}/asignar_tarea",
            json=req.model_dump(),
            timeout=5
        )

        return r.json()

    except Exception as e:
        print("Error reenviando al líder:", e)
        raise HTTPException(status_code=503, detail="Error al comunicarse con el líder")

@router4.post("/getRemoteTask3")
def ejecutarTareaRemota(req: TaskRequest):
    '''la idea es que cada vez que se recibe una solicitud para ejecutar una tarea, se levanta un nuevo contenedor con la imagen especificada, se le asigna un puerto dinámico, y se invoca el endpoint /execute del servicio dentro del contenedor para que ejecute la tarea con los parámetros dados. Luego se devuelve la respuesta al cliente y se detiene el contenedor para liberar recursos.'''

    # esta es la referencia al contenedor que se va a levantar. Se inicializa en None para poder manejar el caso de error
    # donde no se levanta el contenedor y evitar intentar detener algo que no existe.
    container = None
    global is_busy
    is_busy = True

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
            ports={'8000/tcp': None},  # puerto dinámico
            remove=True
        )
        
        # una vez que el contenedor esta levantado, se refresca el estado del contenedor para obtener la información actualizada,
        # incluyendo el puerto asignado dinámicamente. Esto es necesario porque el puerto se asigna en el momento de levantar el contenedor y no se conoce de antemano.
        container.reload()
       
        # port = container.attrs['NetworkSettings']['Ports']['5000/tcp'][0]['HostPort']
        # # esperar a que el servicio esté listo
        time.sleep(2)
        port = None
        for _ in range(10):
            container.reload()
            ports = container.attrs['NetworkSettings']['Ports']
            if ports and ports['8000/tcp']:
                port = ports['8000/tcp'][0]['HostPort']
                break
            time.sleep(5)
        if not port:
            raise Exception("No se pudo obtener el puerto del contenedor")
        
        # hacer la solicitud al servicio dentro del contenedor para ejecutar la tarea.
        # Se hace una solicitud POST al endpoint /EjecutarTarea del servicio, pasando el nombre de la tarea y los parámetros en el cuerpo de la solicitud.
        # es decir, el server hace un HTTP POST al contenedor recién levantado, diciéndole que ejecute la tarea que se le pidió ejecutar a este server, con los parámetros dados.
        response = requests.post(
            f"http://host.docker.internal:{port}/EjecutarTarea",
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
                container.remove()
            except:
                pass
        is_busy = False


@router4.get("/test3")
def test():
    return FileResponse("api/static/index3.html")


# -------------------------------------------------------------------
# MONITOREO DEL LÍDER
# -------------------------------------------------------------------

def monitor_lider():
    global leader_id
    print(f"[Monitor] Iniciado para worker {worker_id}")
    time.sleep(5)
    while True:
        print(f"[Monitor] Verificando líder actual: {leader_id}")

        if leader_id is None:
            print("[Monitor] Sin líder, iniciando elección...")
            elegir_lider()

        elif leader_id != worker_id:
            leader = get_leader()
            if leader:
                try:
                    r = requests.get(f"{leader['url']}/status", timeout=2)
                    if r.status_code != 200:
                        print("[Monitor] Líder no responde, iniciando elección...")
                        elegir_lider()
                except Exception as e:
                    print(f"[Monitor] Error al contactar líder: {e}")
                    elegir_lider()

        else:
            print("[Monitor] Soy el líder, sistema estable")
        
        time.sleep(5)


# Iniciar el hilo de monitoreo del líder
threading.Thread(target=monitor_lider, daemon=True).start()
