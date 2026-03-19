# HIT #2 – Cliente con reconexión automática

## **Descripción**
En este ejercicio se extiende la implementación del **cliente-servidor TCP del HIT #1** agregando un mecanismo de **reconexión automática del cliente**.

El sistema sigue compuesto por dos nodos:
- **Nodo A (Cliente)**: intenta conectarse al servidor. Si el servidor no está disponible o la conexión se pierde, el cliente reintenta la conexión automáticamente después de un tiempo configurado.
- **Nodo B (Servidor)**: escucha conexiones entrantes, recibe un mensaje del cliente y responde confirmando la recepción.
Este ejercicio introduce conceptos de **tolerancia a fallos en sistemas distribuidos**, permitiendo que el cliente siga intentando conectarse hasta que el servidor esté disponible.

---

# **Arquitectura**
https://drive.google.com/file/d/1s1Xn4kV-n4AYPb3m2u32OJcS_2ZfXFif/view?usp=sharing

### **Flujo de comunicación**

1. **Nodo A** intenta conectarse al servidor.
2. Si el servidor no está disponible, el cliente captura la excepción.
3. El cliente espera un tiempo definido (`RETRY_DELAY`).
4. El cliente vuelve a intentar conectarse.
5. Cuando el servidor está disponible:
   - El cliente envía un mensaje.
   - El servidor responde con `"Mensaje Recibido"`.
6. El cliente recibe la respuesta y finaliza.

---

# **Instrucciones para ejecutar el proyecto**

## **1. Instalar dependencias**
El proyecto utiliza la librería **python-dotenv**.
En el repositorio existe un **pipeline de CI/CD configurado con GitHub Actions** que se encarga automáticamente de:
- instalar las dependencias
- ejecutar los tests
- verificar seguridad
- generar el build
Por lo tanto, **no es necesario instalar las dependencias manualmente cuando el código se ejecuta en el pipeline**.
Si se desea ejecutar el proyecto **de forma local**, se pueden instalar con:

```bash
pip install python-dotenv pytest
```

o utilizando:

```bash
pip install -r requirements.txt
```

---

## **2. Crear archivo `.env`**
Crear un archivo `.env` con la siguiente configuración:
```
SERVER_1_ADDR_TP1 = 127.0.0.1:5000
RETRY_DELAY=3
```
Donde:
- **SERVER_1_ADDR_TP1** → dirección IP y puerto del servidor  
- **RETRY_DELAY** → tiempo de espera antes de reintentar la conexión  

---
## **3. Ejecutar el servidor (Nodo B)**
En una terminal ejecutar:
```bash
python ./TrabajoPractico1/Hit2 NodoB.py
```
El servidor comenzará a escuchar conexiones.

---

## **4. Ejecutar el cliente (Nodo A)**
En otra terminal ejecutar:
```bash
python ./TrabajoPractico1/Hit2 NodoA.py
```
Si el servidor no está disponible, el cliente mostrará:
```
Servidor no disponible. Reintentando en X segundos...
```
y seguirá intentando conectarse hasta que el servidor esté activo.

---

# **Ejecución de tests**
El proyecto incluye un **test automatizado con pytest** que verifica el mecanismo de reconexión.
Para ejecutar los tests:
```bash
pytest
```

### **El test realiza lo siguiente**
1. Inicia el **cliente en un hilo**.
2. El cliente intenta conectarse al servidor.
3. Como el servidor aún no está activo, el cliente entra en modo **reintento**.
4. El test inicia el **servidor en otro hilo**.
5. El cliente se conecta correctamente.
6. Se verifica que el cliente reciba `"Mensaje Recibido"`.

---

# **Diagrama de funcionamiento con reconexión**

```
Cliente (NodoA)

connect()
   │
   │ servidor no disponible
   ▼
ConnectionRefusedError
   │
   ▼
sleep(RETRY_DELAY)
   │
   ▼
retry connect()
   │
   ▼
Servidor disponible
   │
   ▼
send() ---------> servidor
recv() <--------- servidor
```

---

# **Decisiones de diseño**

### **Uso de excepciones para detectar fallos**
El cliente captura:
- `ConnectionRefusedError`
- `ConnectionResetError`
Esto permite detectar cuando el servidor:
- no está disponible
- se cae durante la conexión

---

### **Mecanismo de reconexión**
El cliente utiliza un **loop infinito (`while True`)** para seguir intentando conectarse hasta que el servidor esté disponible.
Este patrón es común en **sistemas distribuidos**, donde los servicios pueden estar temporalmente fuera de línea.

---

### **Uso de variables de entorno**
Se utilizan variables de entorno para configurar:
- host del servidor
- puerto
- tiempo de reconexión
Esto evita hardcodear configuraciones en el código.

---
### **Uso de threads en el test**
El test utiliza **threads** para simular la ejecución concurrente del cliente y el servidor, replicando el comportamiento real de dos procesos en red.
