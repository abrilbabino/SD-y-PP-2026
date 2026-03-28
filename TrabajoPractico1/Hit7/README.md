# HIT #7 – Sistema de Inscripciones por Ventanas de Tiempo

## Descripción

En este HIT se extiende el sistema distribuido incorporando un mecanismo de inscripción basado en ventanas de tiempo coordinadas por el nodo D.

El sistema funciona con intervalos fijos de 1 minuto donde:
- Los nodos C se registran en el nodo D
- Las inscripciones no son inmediatas
- Cada nodo registrado participa en la siguiente ventana de tiempo

Esto introduce un modelo de consistencia eventual y desacople temporal entre los nodos.

---

## Arquitectura

El sistema está compuesto por dos tipos de nodos:

- Nodo C: Cliente/Servidor TCP que se registra y se comunica con otros nodos
- Nodo D: Registro central implementado con FastAPI

### Diagrama de Arquitectura

https://drive.google.com/file/d/14SN1-odijBdUXbsUAQoRbiFkKjXRElf3/view?usp=sharing

---

## Funcionamiento

### Registro de nodos

Cuando un nodo C se registra:

POST /register
{
  "host": "127.0.0.1",
  "port": 5001
}

- Se guarda en nodos_futuros

---

### Ventanas de tiempo

El nodo D ejecuta un scheduler que cada 60 segundos:
- Mueve nodos_futuros a nodos_actuales
- Reinicia nodos_futuros

Esto garantiza:
- Separación entre ventanas
- Consistencia temporal
- Desacople entre registro y uso

---

### Comunicación entre nodos

Los nodos C:
1. Se registran en D
2. Obtienen los nodos futuros (los pares que se inscribieron en la misma ventana)
3. Se conectan vía TCP
4. Intercambian mensajes en formato JSON

---

## Instrucciones de Ejecución

### 1. Variables de entorno

Crear archivo .env:

RETRY_DELAY=3
---

### 2. Ejecutar Nodo D
Estar dentro de la carpeta Hit7 y ejecutar:
```bash
uvicorn TrabajoPractico1.Hit7.NodoD:app --host 127.0.0.1 --port 8000
```
---

### 3. Ejecutar Nodo C
```bash
python -m TrabajoPractico1.Hit7.NodoC "127.0.0.1" 8000 "127.0.0.1"
```
Parámetros:
python NodoC.py <host_D> <port_D> <host_C>

---

### 4. Ejecutar múltiples nodos

Ejecutar en diferentes terminales:

```bash
python -m TrabajoPractico1.Hit7.NodoC  "127.0.0.1" 8000 "127.0.0.1"
python -m TrabajoPractico1.Hit7.NodoC  "127.0.0.1" 8000 "127.0.0.1"
python -m TrabajoPractico1.Hit7.NodoC  "127.0.0.1" 8000 "127.0.0.1"
```

---

### 5. Health Check

GET http://127.0.0.1:8000/health

Ejemplo de respuesta:
{
  "status": "ok",
  "nodosActuales": 2,
  "nodosFuturos": 1,
  "uptime": 120
}

---

## Persistencia

El nodo D guarda el estado en un archivo:
inscripciones.json

Ejemplo:

{
  "timestamp": 1710000000,
  "actuales": [
    {"host": "127.0.0.1", "port": 5001}
  ],
  "futuros": [
    {"host": "127.0.0.1", "port": 5002}
  ]
}

---

## Decisiones de Diseño

### Separación en listas (actual / futuro)

Se utilizan dos estructuras:
- nodos_actuales
- nodos_futuros

Esto permite:
- Evitar inconsistencias
- Garantizar aislamiento temporal
- Implementar ventanas de inscripción

---

### Scheduler basado en tiempo
Se utiliza un hilo que ejecuta el cambio de ventana cada 60 segundos, asegurando sincronización global.

---

### Uso de JSON
Se utiliza JSON para:
- Comunicación TCP
- Requests HTTP
- Persistencia

Ventajas:
- Estándar
- Legible
- Extensible

---

### Concurrencia controlada
Se utiliza threading.Lock para evitar condiciones de carrera al modificar estructuras compartidas.

---

### Puerto dinámico en Nodo C

El nodo C usa puertos dinámicos:
server.bind((host, 0))
Permite ejecutar múltiples instancias sin conflictos.

---

### Desacople entre nodos

Los nodos C no conocen a sus pares directamente, sino que dependen del nodo D.
Esto mejora:
- Escalabilidad
- Flexibilidad
- Mantenibilidad

---

## Pruebas
Se incluyen tests que validan:
- Registro diferido
- Cambio de ventana
- Endpoint /health

Ejecutar:
```bash
pytest
```
---
