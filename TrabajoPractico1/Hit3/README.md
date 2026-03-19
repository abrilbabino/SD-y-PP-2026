# HIT #3 – Servidor resiliente a desconexión de clientes

## **Descripción**
En este ejercicio se mejora la implementación del sistema **cliente-servidor TCP** de los HIT anteriores.
La mejora principal consiste en que **el servidor puede seguir funcionando incluso cuando los clientes se desconectan**, permitiendo aceptar **nuevas conexiones de otros clientes** sin necesidad de reiniciar el servidor.

El sistema está compuesto por:
- **Nodo A (Cliente)**: intenta conectarse al servidor. Si el servidor no está disponible o la conexión se pierde, el cliente reintenta la conexión automáticamente.
- **Nodo B (Servidor)**: escucha conexiones entrantes en un loop infinito y puede atender múltiples clientes de manera secuencial.
Este ejercicio introduce un concepto clave en sistemas distribuidos: **la resiliencia del servidor frente a desconexiones de clientes**.

---

# **Arquitectura**
https://drive.google.com/file/d/1s1Xn4kV-n4AYPb3m2u32OJcS_2ZfXFif/view?usp=sharing
---

# **Flujo de comunicación**
1. **Nodo B** inicia el servidor y comienza a escuchar conexiones.
2. **Nodo A** intenta conectarse al servidor.
3. Si el servidor no está disponible, el cliente entra en modo **reintento automático**.
4. Cuando el cliente logra conectarse:
   - envía un mensaje
   - el servidor recibe el mensaje
   - el servidor responde `"Mensaje Recibido"`
5. Si el cliente se desconecta:
   - el servidor detecta la desconexión
   - continúa escuchando nuevas conexiones.
6. Otro cliente puede conectarse posteriormente sin reiniciar el servidor.

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
SERVER_1_ADDR_TP1 = 127.0.0.1:5000
RETRY_DELAY=3
```
Donde:
- **SERVER_1_ADDR_TP1** → dirección IP y puerto del servidor  
- **RETRY_DELAY** → tiempo de espera antes de reintentar conexión  

---

## **3. Ejecutar el servidor (Nodo B)**
En una terminal ejecutar:
```bash
python .\TrabajoPractico1\Hit3\NodoB.py
```
El servidor quedará **ejecutándose continuamente**, esperando nuevas conexiones.

---

## **4. Ejecutar el cliente (Nodo A)**
En otra terminal ejecutar:
```bash
python .\TrabajoPractico1\Hit3\NodoA.py
```
El cliente:
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
1. Levanta el **servidor en un hilo**.
2. Inicia un **primer cliente** que se conecta al servidor.
3. Verifica que el cliente recibe `"Mensaje Recibido"`.
4. El cliente termina su ejecución (simulando una desconexión).
5. Se inicia un **segundo cliente**.
6. El servidor acepta la nueva conexión.
7. Se verifica nuevamente que el servidor responde correctamente.
Esto confirma que **el servidor sigue operativo después de que un cliente se desconecta**.

---

# **Diagrama de funcionamiento**
```
Cliente 1             Servidor               

connect() ---------> accept()
send() ------------> recv()
recv() <------------ send()
close()

      sigue escuchando


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
