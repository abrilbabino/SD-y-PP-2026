# Informe Técnico: Patrones de Mensajería con RabbitMQ (TP3)

Este documento describe la arquitectura, diferencias y casos de uso de los patrones de mensajería implementados en el **Trabajo Práctico 3 (Queue)**.

---

## 1. Diagramas de Arquitectura y Descripción

### EJEMPLO 1 — MESSAGE QUEUE (Punto a Punto)

Un productor envía mensajes a una cola y un solo consumidor los recibe. Es el modelo base para la distribución de carga.
[Image of RabbitMQ Work Queue architecture with multiple consumers and round-robin distribution]

- **Arquitectura:** `Producer -> Queue -> [Consumer 1, Consumer 2]`.
- **Comportamiento:** Implementamos un productor de 10 tareas. Al levantar 2 consumidores, observamos un reparto **Round-Robin** (mensajes 1, 3, 5... al Consumidor A y 2, 4, 6... al Consumidor B).

### EJEMPLO 2 — EVENT BUS / PUB-SUB (Fan-out)

Se utiliza un `Exchange` de tipo `fanout`. El mensaje se ignora si no hay colas conectadas, o se copia a todas las colas suscritas.
[Image of RabbitMQ Fanout Exchange architecture showing one producer and multiple queues receiving the same message]

- **Arquitectura:** `Producer -> Fanout Exchange -> [Queue A, Queue B, Queue C]`.
- **Caso Nodos:** Se verificó que al emitir "nuevo bloque minado", los 3 nodos recibieron la copia exacta del evento simultáneamente.

### EJEMPLO 3 — DEAD LETTER QUEUE (DLQ)

Mecanismo para capturar mensajes que fallan o son rechazados, evitando que bloqueen la cola principal o se pierdan.
[Image of RabbitMQ Dead Letter Exchange architecture showing message redirection on rejection]

- **Arquitectura:** `Main Queue (with DLX config) -> Consumer (nack) -> DLX -> Dead Letter Queue`.
- **Lógica:** El consumidor descarta mensajes con `"error": true`. Un segundo consumidor monitorea la DLQ para procesar los fallos.

### EJEMPLO 4 — RETRY CON EXPONENTIAL BACKOFF

Estrategia de reintento para errores temporales, incrementando el tiempo de espera entre intentos.
[Image of Exponential Backoff retry strategy flowchart in messaging systems]

- **Arquitectura:** `Consumer -> Failure -> Wait (2^n) -> Re-queue -> DLQ (after 4 attempts)`.
- **Implementación:** Simulamos fallos del 50%. Los reintentos siguen la serie: 1s, 2s, 4s, 8s antes de rendirse y enviar a la DLQ.

---

## 2. Diferencias entre Patrones

| Patrón            | Tipo de Exchange | Entrega de Mensaje    | Objetivo Principal                     |
| :---------------- | :--------------- | :-------------------- | :------------------------------------- |
| **Message Queue** | Default (Direct) | 1 a 1 (Round-robin)   | Escalabilidad y balanceo de carga.     |
| **Pub-Sub**       | Fanout           | 1 a N (Todos)         | Notificación masiva y desacoplamiento. |
| **DLQ**           | Configurable     | Redirección por fallo | Tolerancia a fallos y auditoría.       |
| **Backoff**       | Delay Exchange   | Reintento programado  | Manejo de errores transitorios.        |

---

## 3. Escenarios de Uso

### ¿Cuándo usar cada uno?

1.  **Message Queue:** En sistemas de **procesamiento de imágenes o facturación**. Si el volumen de facturas sube, añades más consumidores y el sistema escala linealmente.
2.  **Pub-Sub:** En arquitecturas de **Microservicios**. Cuando un usuario se registra, el servicio de "Auth" publica el evento y los servicios de "Email", "Puntos de Fidelidad" y "Analytics" reaccionan de forma independiente.
3.  **Dead Letter Queue:** En **Sistemas Críticos (Finanzas/Salud)**. Si un mensaje de "Transacción" falla por un formato inesperado, la DLQ permite que un humano o un proceso de limpieza analice el error sin detener el flujo principal.
4.  **Exponential Backoff:** En **Integraciones con APIs Externas** (ej. Stripe, AWS). Si el servicio externo devuelve un "Rate Limit", el backoff espera a que el servicio se recupere antes de intentar de nuevo, evitando saturar la red.

---

## 4. Notas de Resiliencia (Ejercicio 2)

Para garantizar la entrega en todos los patrones, se aplicó:

- **Acknowledge (ack):** El mensaje no se borra de RabbitMQ hasta que el consumidor confirma éxito.
- **Persistencia:** Colas y mensajes configurados como `durable` para resistir reinicios del broker.
- **Prefetch Count:** Limitado a 1 para asegurar un despacho equitativo (Fair Dispatch).
