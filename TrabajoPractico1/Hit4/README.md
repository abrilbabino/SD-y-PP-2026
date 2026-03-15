# HIT #4 – Nodo híbrido cliente-servidor

## **Descripción**
En este ejercicio se refactoriza la implementación de los programas **Nodo A (cliente)** y **Nodo B (servidor)** de los HIT anteriores en **un único programa llamado Nodo C**.
Este nuevo programa funciona **simultáneamente como cliente y como servidor**. Esto significa que cada instancia del programa puede:
- **escuchar conexiones entrantes de otros nodos**
- **conectarse activamente a otro nodo**

Al iniciar el programa **Nodo C**, se deben proporcionar por **parámetros**:
- la **dirección IP y el puerto donde el nodo escuchará conexiones**
- la **dirección IP y el puerto de otro nodo C al cual se conectará**

De esta manera, al ejecutar **dos instancias del programa C**, cada una configurada con los parámetros de la otra, ambos nodos:
- establecen una conexión  
- intercambian mensajes de saludo  
- responden confirmando la recepción del mensaje  

Este modelo refleja un patrón común en **sistemas distribuidos peer-to-peer**, donde cada nodo puede cumplir **tanto el rol de cliente como el de servidor dentro de la red**.

---

# **Arquitectura**
Cada nodo ejecuta **dos comportamientos simultáneos**:
- un **servidor TCP** que escucha conexiones entrantes  
- un **cliente TCP** que intenta conectarse al otro nodo  

---

# **Flujo de comunicación**
1. Se inicia el **Nodo C1**, indicando:
   - la IP y puerto donde escuchará conexiones
   - la IP y puerto del **Nodo C2**
2. Se inicia el **Nodo C2**, indicando:
   - la IP y puerto donde escuchará conexiones
   - la IP y puerto del **Nodo C1**
3. Cada nodo inicia su **servidor TCP**.
4. Luego cada nodo intenta **conectarse al otro nodo**.
5. Cuando se establece la conexión:
   - un nodo envía un **mensaje de saludo**
   - el nodo receptor recibe el mensaje
   - el nodo receptor responde `"Mensaje Recibido"`
6. Ambos nodos terminan **saludándose mutuamente**, cada uno a través de su propio canal de comunicación.
---

# **Instrucciones para ejecutar el proyecto**
## **1. Instalar dependencias**
El proyecto utiliza la librería **python-dotenv**.
En el repositorio existe un **pipeline de CI/CD configurado con GitHub Actions** que se encarga automáticamente de:
- instalar dependencias  
- ejecutar tests  
- ejecutar verificaciones de seguridad  
- generar el build  
Por lo tanto, **no es necesario instalar las dependencias manualmente cuando el código se ejecuta en el pipeline**.
Para ejecutar el proyecto localmente se pueden instalar con:
~~~bash
pip install python-dotenv pytest
~~~
o con:
~~~bash
pip install -r requirements.txt
~~~
---

## **2. Crear archivo `.env`**
Crear un archivo `.env` con la siguiente configuración:
~~~
RETRY_DELAY=3
HOST_SERVER1_TCP_TP1= ...
PORT_SERVER1_TCP_TP1= ...
HOST_SERVER2_TCP_TP1= ...
PORT_SERVER2_TCP_TP1= ...
~~~

Donde:
- **RETRY_DELAY** → tiempo de espera antes de reintentar una conexión si el nodo remoto aún no está disponible.
- **HOST_SERVER_TCP_TP1** → dirección del servidor
- **PORT_SERVER_TCP_TP1** → puerto del servidor
---

## **3. Ejecutar el primer nodo (Nodo C1)**
En una terminal ejecutar:
~~~bash
python NodoC.py 127.0.0.1 5000 127.0.0.1 5001
~~~

Esto indica que el nodo:
- **escucha conexiones en `127.0.0.1:5000`**
- intenta conectarse al nodo **`127.0.0.1:5001`**

---

## **4. Ejecutar el segundo nodo (Nodo C2)**
En otra terminal ejecutar:
~~~bash
python NodoC.py 127.0.0.1 5001 127.0.0.1 5000
~~~
Esto indica que el nodo:
- **escucha conexiones en `127.0.0.1:5001`**
- intenta conectarse al nodo **`127.0.0.1:5000`** 
De esta forma, **ambos nodos se conectan entre sí y se envían mensajes de saludo**.

---

# **Ejecución de tests**
El proyecto incluye **tests automatizados utilizando pytest** que verifican el funcionamiento del nodo híbrido.
Para ejecutar los tests:
~~~bash
pytest
~~~

### **El test realiza lo siguiente**
1. Inicia **dos nodos C en hilos separados**.  
2. Cada nodo inicia su **servidor TCP**.  
3. Ambos nodos intentan conectarse entre sí.  
4. Se establece la conexión entre los nodos.  
5. Cada nodo envía un **mensaje de saludo**.  
6. Se verifica que ambos nodos reciben la respuesta `"Mensaje Recibido"`.

Esto confirma que **cada nodo puede actuar simultáneamente como cliente y servidor**.
---

# **Diagrama de funcionamiento**
~~~
Nodo C1                    Nodo C2
start_server()             start_server()
connect() ---------> accept()
send() ------------> recv()
recv() <------------ send()

accept() <--------- connect()
recv() <----------- send()
send() ------------> recv()
~~~

Esto demuestra que **la comunicación ocurre en ambos sentidos**, ya que cada nodo cumple ambos roles.

---

# **Decisiones de diseño**
### **Arquitectura híbrida cliente-servidor**
Se decidió unificar la lógica del cliente y del servidor en un único programa para permitir que cada nodo pueda **iniciar conexiones y recibirlas**, simulando el comportamiento de nodos en sistemas distribuidos.

### **Uso de parámetros al iniciar el programa**
Las direcciones IP y puertos se pasan como **parámetros de ejecución**, lo que permite ejecutar múltiples nodos con configuraciones diferentes sin modificar el código.

### **Reintento automático de conexión**
Si el nodo remoto todavía no está disponible, el cliente **vuelve a intentar la conexión automáticamente** después de un tiempo definido por `RETRY_DELAY`.
Esto permite que los nodos puedan **iniciarse en cualquier orden**.

### **Uso de threads**
El servidor se ejecuta en un **hilo independiente**, permitiendo que el nodo continúe escuchando conexiones mientras simultáneamente intenta conectarse al otro nodo.
