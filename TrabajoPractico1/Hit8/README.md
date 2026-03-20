------------------------------------------------------------------------------
# HIT #8 – Comunicación con gRPC y Protocol Buffers

## Descripción

En este ejercicio se refactoriza la comunicación entre nodos del sistema distribuido reemplazando el uso de JSON sobre TCP (implementado en el HIT #5) por **gRPC** utilizando **Protocol Buffers (Protobuf)**.

El objetivo principal es mejorar:
- La eficiencia en la serialización de mensajes
- La latencia de comunicación
- La mantenibilidad del código mediante generación automática

En este modelo, cada nodo C actúa simultáneamente como:
- **Servidor gRPC** (recibe mensajes)
- **Cliente gRPC** (envía mensajes)

---

## Arquitectura del Sistema
https://drive.google.com/file/d/1ktfaoIQF5cye1qx8eNHjeMNHqN6KiqRf/view?usp=sharing

## Definición del Servicio (Protobuf)

El archivo `nodos.proto` define:

- Mensaje de cliente: `ClientMessage`
- Mensaje de respuesta: `ServerResponse`
- Servicio: `NodeService`
- Método RPC: `SendMessage`

Esto permite generar automáticamente:
- Stub de cliente
- Base del servidor

---
### Flujo de Comunicación
1. El **Nodo C1** inicia su servidor gRPC en su puerto.
2. El **Nodo C2** inicia su servidor gRPC en su puerto.
3. Cada nodo crea un cliente gRPC hacia el otro.
4. - El cliente construye un mensaje Protobuf **ClientMessage** y lo envía con **stub.SendMessage()**.
5. - El servidor recibe el objeto Protobuf, lo procesa y responde con un **ServerResponse**.
6. - El cliente recibe la respuesta, la deserializa y la muestra.

—

## Ejecución del Proyecto

### 1. Instalar dependencias

```bash
pip install grpcio grpcio-tools python-dotenv
```
###2. Generar código a partir de Protobuf
```bash
cd TrabajoPractico/Hit8
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. nodos.proto
```
###3. Configurar variables de entorno  
Crear archivo .env:   
 ```bash 
- RETRY_DELAY=3
```

## 4. Ejecutar Nodos

Abrir dos terminales:

**Nodo C1**
 ```bash 
python -m TrabajoPractico1.Hit8.NodoC 5000 5001
```

**Nodo C2**  
 ```bash 
python -m TrabajoPractico1.Hit8.NodoC 5001 5000
```

### Concurrencia

Se utilizan threads:  
- 1 para el servidor  
- 1 para el cliente  

El servidor gRPC usa internamente un ThreadPoolExecutor (max_workers=10),  
permitiendo múltiples llamadas concurrentes.  

### Manejo de Errores
Si el servidor no está disponible:  
- Se captura grpc.RpcError  
- Se reintenta conexión en loop infinito  

### Diagrama de Funcionamiento
```
        Nodo C1 (Servidor gRPC + Cliente)                   Nodo C2 (Servidor gRPC + Cliente)
[Servidor] grpc.server(...) escucha en puerto      [Servidor] grpc.server(...) escucha en puerto
[Cliente] grpc.insecure_channel()  ----------------->  [Servidor] acepta conexión internamente
stub.SendMessage(ClientMessage) -------------------->  [Servidor] recibe objeto Protobuf
                                                                             procesa y responde con ServerResponse
[Cliente] recibe respuesta como objeto Protobuf <------- stub devuelve ServerResponse
							        {msg: “Mensaje Recibido”}
[Servidor] acepta conexión internamente  <-------------  [Cliente] grpc.insecure_channel() 
[Servidor] recibe objeto Protobuf <----------------------  stub.SendMessage(ClientMessage)
 procesa y responde con ServerResponse
stub devuelve ServerResponse  -------------> [Cliente] recibe respuesta como objeto Protobuf
 {msg: “Mensaje Recibido”}
 Ambos servidores siguen escuchando nuevas conexiones RPC
```

### Decisiones de Diseño
**Uso de gRPC sobre TCP + JSON**  
Se reemplaza JSON porque:  
- Reduce el tamaño de los mensajes (binario vs texto)  
- Mejora la performance  
- Evita errores manuales de serialización/deserialización  
- Genera automáticamente cliente y servidor  

**Uso de Protocol Buffers**  
Permite:  
- Definir contratos de comunicación estrictos  
- Tipado fuerte  
- Evolución controlada del sistema (versionado)  

**Nodo híbrido (cliente + servidor)**  
Se mantiene el diseño del HIT #5:  
- Cada nodo puede iniciar comunicación  
- No hay jerarquía fija  
- Modelo distribuido descentralizado  

**Reintento automático**  
Se implementa un loop infinito en el cliente  
Permite tolerancia a fallos  
Hace el sistema más resiliente  

**Concurrencia con threads**  
Permite ejecutar cliente y servidor simultáneamente  
Simula comportamiento real en sistemas distribuidos  
