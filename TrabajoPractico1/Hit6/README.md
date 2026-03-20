# HIT #6 – Registro de contactos y descubrimiento dinámico de nodos

## **Descripción**
En este ejercicio se extiende el sistema distribuido incorporando un nuevo componente: el **Nodo D (Registro de contactos)**.

El objetivo es eliminar la necesidad de configurar manualmente las direcciones de los nodos pares. En su lugar, cada nodo **C**:
- se registra automáticamente en el nodo D
- obtiene la lista de otros nodos activos
- se conecta a ellos e intercambia mensajes

El sistema ahora está compuesto por:
- **Nodo C**: nodo híbrido cliente/servidor TCP que se registra y se conecta a otros nodos
- **Nodo D**: servicio HTTP que mantiene un registro en memoria de los nodos activos

Este ejercicio introduce un concepto fundamental en sistemas distribuidos:
> **descubrimiento dinámico de nodos (service discovery)**

---

# **Arquitectura**
https://drive.google.com/file/d/1s1Xn4kV-n4AYPb3m2u32OJcS_2ZfXFif/view?usp=sharing

---

# **Flujo de comunicación**
1. El **Nodo D** inicia y expone el endpoint `/register`.
2. Un **Nodo C** inicia:
   - levanta un servidor TCP en un **puerto dinámico**
3. El Nodo C se registra en D enviando:
   - su `host`
   - su `port`
4. D:
   - guarda el nodo en memoria
   - devuelve la lista de otros nodos registrados
5. El Nodo C:
   - recibe los nodos pares
   - se conecta a cada uno
   - envía un mensaje en formato JSON
6. Los nodos receptores:
   - reciben el mensaje
   - responden `"Mensaje Recibido"`
7. El sistema permite múltiples nodos C ejecutándose simultáneamente sin configuración manual.

---

# **Instrucciones para ejecutar el proyecto**

## **1. Instalar dependencias**
El proyecto utiliza:
- `fastapi`
- `uvicorn`
- `requests`
- `python-dotenv`

Instalar con:
```bash
pip install fastapi uvicorn requests python-dotenv pytest





# HIT #6 – Registro de contactos y descubrimiento dinámico de nodos

## **Descripción**
En este ejercicio se extiende el sistema distribuido incorporando un nuevo componente: el **Nodo D (Registro de contactos)**.

El objetivo es eliminar la necesidad de configurar manualmente las direcciones de los nodos pares. En su lugar, cada nodo **C**:
- se registra automáticamente en el nodo D
- obtiene la lista de otros nodos activos
- se conecta a ellos e intercambia mensajes

El sistema está compuesto por:
- **Nodo C**: nodo híbrido cliente/servidor TCP
- **Nodo D**: servicio HTTP que mantiene un registro de nodos activos

Este ejercicio introduce un concepto clave en sistemas distribuidos:
**descubrimiento dinámico de nodos (service discovery)**

---

# **Arquitectura**
https://drive.google.com/file/d/14SN1-odijBdUXbsUAQoRbiFkKjXRElf3/view?usp=sharing

---

# **Flujo de comunicación**
1. El **Nodo D** inicia y expone el endpoint `/register`.
2. Un **Nodo C** inicia:
   - levanta un servidor TCP en un puerto dinámico
3. El Nodo C se registra en D enviando:
   - su `host`
   - su `port`
4. El nodo D:
   - guarda el nodo en memoria
   - devuelve la lista de otros nodos registrados
5. El Nodo C:
   - recibe los nodos pares
   - se conecta a cada uno
   - envía un mensaje en formato JSON
6. Los nodos receptores:
   - reciben el mensaje
   - responden `"Mensaje Recibido"`
7. El sistema permite múltiples nodos ejecutándose sin configuración manual.

---

# **Instrucciones para ejecutar el proyecto**

## **1. Instalar dependencias**
El proyecto utiliza:
- fastapi
- uvicorn
- requests
- python-dotenv

Instalar con:
```bash
pip install fastapi uvicorn requests python-dotenv pytest
```

o:
```bash
pip install -r requirements.txt
```

---

## **2. Crear archivo `.env`**
Crear un archivo `.env` con:

```
RETRY_DELAY = 3
```

---

## **3. Ejecutar el Nodo D (registro)**
```bash
uvicorn TrabajoPractico1.Hit6.NodoD:app --host 0.0.0.0 --port 5000
```

---

## **4. Ejecutar nodos C**

Abrir **dos o más terminales**:

### Terminal 1
```bash
python .\TrabajoPractico1\Hit6\NodoC.py “127.0.0.1” 5000 “127.0.0.1”
```

### Terminal 2
```bash
python .\TrabajoPractico1\Hit6\NodoC.py “127.0.0.1” 5000 “127.0.0.1”
```

### Terminal 3 (opcional)
```bash
python .\TrabajoPractico1\Hit6\NodoC.py “127.0.0.1” 5000 “127.0.0.1”
```

---

# **Ejecución esperada**

### Nodo 1
```
[NODO] Pares encontrados: []
```

### Nodo 2
```
[NODO] Pares encontrados: [{'host': '127.0.0.1', 'port': XXXX}]
[CLIENTE] respuesta: {'type': 'msgRecibido', 'msg': 'Mensaje Recibido'}
```

### Nodo 1 recibe:
```
[SERVER] Mensaje Recibido: Hola, me conecte
```

Esto confirma:
- registro correcto
- descubrimiento de nodos
- comunicación entre pares

---

# **Ejecución de tests**
El proyecto puede incluir tests con pytest:

```bash
pytest
```

### **El test debería verificar**
1. Se levanta el nodo D.
2. Se ejecuta un nodo C.
3. Se ejecuta un segundo nodo C.
4. El segundo obtiene al primero como par.
5. Se establece conexión TCP.
6. Se intercambian mensajes correctamente.

---

# **Diagrama de funcionamiento**
```
Nodo C1 (Cliente + Servidor)              Nodo D (Registro)                 Nodo C2 (Cliente + Servidor)
start_server()
listen()
aceptarConn()                                           
            POST /register --------------------->
               {host, port}                                                               
                <----------- nodosPares:[] -------
									start_server()
listen()
aceptarConn()                                           
            				       <------------------------------POST /register
 									 {host, port}                                                               
                					----------- nodosPares:[C1] ------->

connect(C1)                                        
accept()<---------------------------------------------------------------------  send(JSON saludo) 
recv(JSON)
send(JSON respuesta) -------------------------------------------------------> recv(JSON)
      
   close()
                 Servidores TCP de C1 y C2 continúan escuchando nuevas conexiones

```

---

# **Decisiones de diseño**

### **Puerto dinámico en Nodo C**
```
server.bind((host, 0))
```

Permite evitar conflictos y ejecutar múltiples nodos en una misma máquina.

---

### **Registro centralizado**
```
nodos = []
```

Nodo D mantiene los nodos activos en memoria para simplificar el descubrimiento.

---

### **Evitar duplicados**
```
if newNodo not in nodos:
    nodos.append(newNodo)
```

---

### **Comunicación con JSON**
```
json.dumps()
json.loads()
```

Permite estructurar y transmitir datos de forma estándar.

---

### **Arquitectura híbrida**
Cada nodo C funciona como:
- servidor (recibe conexiones)
- cliente (inicia conexiones)

---

### **Reintentos en registro**
```
while True:
    try:
        ...
    except:
        sleep(RETRY_DELAY)
```

Permite tolerancia a fallos en la comunicación con D.

---

### **Uso de threads**
```
threading.Thread(...)
```

Permite manejar múltiples conexiones simultáneamente.

---
