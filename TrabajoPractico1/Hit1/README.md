# HIT #1 – Comunicación Cliente-Servidor con Sockets TCP

## **Descripción**
En este ejercicio se implementa un sistema simple de **comunicación cliente-servidor utilizando sockets TCP en Python**.
El sistema está compuesto por dos nodos:
- **Nodo A (Cliente)**: inicia la conexión con el servidor, envía un mensaje y espera una respuesta.
- **Nodo B (Servidor)**: escucha conexiones entrantes, recibe un mensaje del cliente y responde confirmando la recepción.
Este ejercicio demuestra el funcionamiento básico de la **comunicación en red mediante sockets**.

---

# **Arquitectura**
https://drive.google.com/file/d/1s1Xn4kV-n4AYPb3m2u32OJcS_2ZfXFif/view?usp=sharing

### **Flujo de comunicación**
1. **Nodo B** inicia el servidor y queda escuchando conexiones.
2. **Nodo A** crea un socket e intenta conectarse al servidor.
3. **Nodo A** envía un mensaje al servidor.
4. **Nodo B** recibe el mensaje.
5. **Nodo B** envía una respuesta al cliente.
6. **Nodo B** cierra la conexión. 
7. **Nodo A** recibe la respuesta y finaliza la conexión.

---

# **Instrucciones para ejecutar el proyecto**

## **1. Instalar dependencias**
El proyecto utiliza la librería **python-dotenv** para cargar variables de entorno.
En el repositorio existe un **pipeline de CI/CD configurado con GitHub Actions** que se encarga automáticamente de:
- instalar las dependencias
- ejecutar los tests
- verificar seguridad
- generar el build
Por lo tanto, **no es necesario instalar las dependencias manualmente cuando el código se ejecuta en el pipeline**.
Sin embargo, si se desea ejecutar el proyecto **de forma local**, se pueden instalar las dependencias con:

```bash
pip install python-dotenv
```

---

## **2. Crear archivo `.env`**
Crear un archivo `.env` con la siguiente configuración:

```
SERVER_1_ADDR_TP1= 127.0.0.1:5000
```
Donde:
- **SERVER_1_ADDR_TP1** → dirección IP y puerto del servidor
---

## **3. Ejecutar el servidor (Nodo B)**
En una terminal ejecutar:
```bash
python .\TrabajoPractico1\Hit1\NodoB.py
```
El servidor comenzará a escuchar conexiones en el puerto configurado.

---

## **4. Ejecutar el cliente (Nodo A)**
En otra terminal ejecutar:
```bash
python ./TrabajoPractico1/Hit1 NodoA.py
```
El cliente se conectará al servidor, enviará un mensaje y mostrará la respuesta recibida.

---

# **Ejecución de tests**
El proyecto incluye un **test automatizado utilizando pytest** para verificar la comunicación entre cliente y servidor.
Para ejecutar los tests:
```bash
pytest
```

### **El test realiza lo siguiente:**
1. Levanta el **servidor en un hilo**.
2. Espera a que el servidor esté listo.
3. Ejecuta el **cliente**.
4. Verifica que el cliente reciba la respuesta **"Mensaje Recibido"**.

---

# **Diagrama del flujo de comunicación**

```
Cliente (NodoA)              Servidor (NodoB)

socket()                     socket()
connect()  ----------------> bind()
send()     ----------------> listen()
                             accept()
                             recv()
recv()     <---------------- send()
close()                     close()
```

---

# **Decisiones de diseño**

### **Uso de variables de entorno**
Se utilizan **variables de entorno** para configurar:
- dirección del servidor
- puerto de escucha

Esto evita **hardcodear valores en el código** y facilita modificar la configuración sin cambiar el programa.

---

### **Uso de threads en el test**
Durante la ejecución del test, el servidor se ejecuta en **un hilo separado**.  
Esto permite que el cliente pueda ejecutarse al mismo tiempo y conectarse al servidor, simulando el comportamiento real de dos procesos en red.
