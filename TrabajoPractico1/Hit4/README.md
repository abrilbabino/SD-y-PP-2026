# HIT #4 – Cliente + Servidor Bidireccional 

## **Descripción**
En este ejercicio se refactoriza la arquitectura cliente-servidor del HIT anterior en un único programa denominado Nodo C.
La mejora principal consiste en que ****, permitiendo **** sin necesidad de …

El sistema está compuesto por:
- **Nodo C (Cliente-Servidor)**: Función cliente, intenta conectarse al servidor para enviar un mensaje. Si el servidor no está disponible o la conexión se pierde, el cliente reintenta la conexión automáticamente.
También cumple con la función de servidor y escucha conexiones entrantes en un loop infinito y puede atender y dar respuesta al mensaje de múltiples clientes de manera secuencial.

---

# **Arquitectura**
https://drive.google.com/file/d/1JFKFG0tbbGVuQZT2RI9Q_5lIVPxu1dkM/view?usp=sharing
---

# **Flujo de comunicación**
1. **Nodo C1** inicia su servidor y comienza a escuchar conexiones.
2. **Nodo C2** inicia su servidor y comienza a escuchar conexiones.
3. **Nodo C1** intenta conectarse al puerto del Nodo C2.
4. **Nodo C2** intenta conectarse al puerto del Nodo C1.
5. Cuando se establece la conexión el cliente envía el mensaje `"Me conecte"`.
6. El servidor del nodo receptor:
- recibe el mensaje
- responde `"Mensaje Recibido"`.
7. El cliente recibe la confirmación.
8. Ambos nodos continúan escuchando nuevas conexiones.

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
```bash
pip install python-dotenv pytest
```
o con:
```bash
pip install -r requirements.txt
```

---

## **2. Crear archivo `.env`**
Crear un archivo `.env` con la siguiente configuración:
```
SERVER_1_ADDR_TP1= 127.0.0.1:9000
SERVER_2_ADDR_TP1= 127.0.0.1:9001
RETRY_DELAY= 3
```
Donde:
- **SERVER_1_ADDR_TP1** → dirección IP y puerto del servidor de la primer instancia de NodoC 
- **SERVER_2_ADDR_TP1** → dirección IP y puerto del servidor  de la segunda instancia de NodoC
- **RETRY_DELAY** → tiempo de espera antes de reintentar conexión  

---

## **3. Ejecutar primera instancia (Nodo C)**
En una terminal ejecutar:
```bash
python .\TrabajoPractico1\Hit4\NodoC.py 9000 9001
```
El servidor quedará **ejecutándose continuamente**, esperando nuevas conexiones en el puerto 9000 el cliente se va a conectar al Nodo C que escucha en el puerto 9001:
- se conectará al servidor
- enviará un mensaje
- recibirá una respuesta
Si el servidor no está disponible, el cliente seguirá intentando conectarse.

---

## **4. Ejecutar  segunda instancia (Nodo C)**
En otra terminal ejecutar:
```bash
python .\TrabajoPractico1\Hit4\NodoC.py 9001 9000
```
El servidor quedará **ejecutándose continuamente**, esperando nuevas conexiones en el puerto 9001 el cliente se va a conectar al Nodo C que escucha en el puerto 9000:
- se conectará al servidor
- enviará un mensaje
- recibirá una respuesta
Si el servidor no está disponible, el cliente seguirá intentando conectarse.

---

# **Ejecución de tests**
El proyecto incluye un **test automatizado con pytest** que verifica que el servidor **sigue funcionando después de que un cliente se desconecta**.
Para ejecutar los tests:
```bash
pytest
```

### **El test realiza lo siguiente**
1. Levanta **dos servidores en hilos separados**, cada uno escuchando en un puerto distinto.  
2. Espera brevemente para asegurar que ambos servidores estén activos.  
3. Inicia **dos clientes en hilos separados**.  
4. El **cliente 1 se conecta al servidor del nodo 2**.  
5. El **cliente 2 se conecta al servidor del nodo 1**.  
6. Cada cliente envía el mensaje `"Me conecte"`.  
7. Cada servidor recibe el mensaje y responde `"Mensaje Recibido"`.  
8. El test espera que ambos clientes finalicen su ejecución.  
9. Se verifica que **cada cliente haya recibido la respuesta `"Mensaje Recibido"`**.  

Esto confirma que **los nodos pueden comunicarse correctamente entre sí funcionando simultáneamente como cliente y servidor**.

---

# **Diagrama de funcionamiento**
```
Nodo C1 (Cliente + Servidor)        Nodo C2 (Cliente + Servidor)
accept() 	<----------------------  		connect()
recv()	 	<---------------- 		send("Me conecte")

send("Mensaje Recibido")     -------------------> recv()
close()

connect()  	---------------------->  		accept()
send("Me conecte")	 ----------------> 		recv()

recv()      <---------------------- 		send("Mensaje Recibido")

close()                                   	

	   Servidores siguen escuchando

```

---

# **Decisiones de diseño**

### **Loop infinito en el servidor**
El servidor utiliza:

```
while True
```
para aceptar múltiples conexiones, evitando que el proceso termine después de atender a un cliente.

---

### **Detección de desconexión del cliente**
Cuando el cliente cierra la conexión:
```
data = conn.recv(...)
```
retorna vacío, lo que permite detectar que el cliente se desconectó y salir del loop interno.

---

### **Reconexión automática del cliente**

El cliente captura excepciones como:
- `ConnectionRefusedError`
- `ConnectionResetError`
y vuelve a intentar la conexión después de un tiempo definido por `RETRY_DELAY`.

---

### **Uso de threads en los tests**
Los tests utilizan **threads** para simular múltiples clientes conectándose al servidor mientras este continúa ejecutándose, reproduciendo el comportamiento de un sistema distribuido real.
