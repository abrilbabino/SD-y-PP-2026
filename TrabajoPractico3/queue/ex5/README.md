# Informe Técnico: Patrones de Mensajería con RabbitMQ (TP3)

Este documento describe la arquitectura, diferencias y casos de uso de los patrones de mensajería implementados en el **Trabajo Práctico 3 (Queue)**.

---

## 1. Diagramas de Arquitectura y Descripción

### EJEMPLO 1 — MESSAGE QUEUE (Punto a Punto)

- **Descripción del Patrón:** Un productor envía mensajes a una cola y un solo consumidor los recibe. Es el modelo base para la distribución de carga.
- **Arquitectura y Componentes:** La solución involucra un Producer, una cola persistente `task_queue` en RabbitMQ, y múltiples Workers (consumidores).
  ![Arquitectura-ex1](../ex1/Arquitectura-ex1.png)
- **Comportamiento Observado:** Implementamos un productor de 10 tareas. Al levantar 2 consumidores, observamos un **reparto Round-Robin** (mensajes 1, 3, 5... al Consumidor A y 2, 4, 6... al Consumidor B), distribuyendo equitativamente la carga.

### EJEMPLO 2 — EVENT BUS / PUB-SUB (Fan-out)

- **Descripción del Patrón:** Notificación masiva donde el productor emite un evento sin importar quién lo reciba, logrando el patrón de Publicación/Suscripción.
- **Arquitectura y Componentes:** El Producer envía mensajes a un exchange de tipo `fanout`. Cada Worker genera una cola temporal y exclusiva en RabbitMQ al iniciar.
  ![Arquitectura-ex2](../ex2/Arquitectura-ex2.png)
- **Comportamiento Observado:** Se verificó que al emitir un "nuevo bloque minado", el exchange `fanout` realiza un **Broadcast (1 a N)**. Todos los nodos (colas conectadas) recibieron una copia exacta del evento simultáneamente.

### EJEMPLO 3 — DEAD LETTER QUEUE (DLQ)

- **Descripción del Patrón:** Mecanismo para capturar mensajes que fallan o son rechazados, evitando que bloqueen la cola principal o se pierdan irremediablemente.
- **Arquitectura y Componentes:** Intervienen una cola principal (con configuración DLX) y un exchange de "letra muerta" (`dlx_exchange`) que enruta a la `dead_letter_queue`. Hay un consumidor principal y un consumidor especializado en la DLQ.
  ![Arquitectura-ex3](../ex3/Arquitectura-ex3.png)
- **Comportamiento Observado:** El consumidor principal procesa los mensajes y cuando descarta mensajes con `"error": true`, realiza un rechazo explícito (`nack`). RabbitMQ redirige automáticamente esos mensajes al DLX y terminan en la DLQ, donde un segundo consumidor monitorea los fallos.

### EJEMPLO 4 — RETRY CON EXPONENTIAL BACKOFF

- **Descripción del Patrón:** Estrategia de reintento para errores temporales, incrementando el tiempo de espera entre intentos.
- **Arquitectura y Componentes:** Se utiliza el exchange principal, un exchange/cola de reintentos (`retry_queue`) y finalmente la DLQ. No requiere plugins externos.
  ![Arquitectura-ex4](../ex4/Arquitectura-ex4.png)
- **Comportamiento Observado:** Simulamos fallos del 50%. En vez de rechazar definitivamente, el mensaje se envía a la cola de reintento usando un **TTL (Time-To-Live)** creciente (1s, 2s, 4s, 8s). Cuando expira, vuelve a la cola principal. Si supera 4 reintentos, el mensaje se transfiere definitivamente a la DLQ. Este flujo logra un **Exponential Backoff** de manera nativa.

---

## 2. Diferencias entre Patrones

| Patrón            | Tipo de Exchange | Entrega de Mensaje    | Objetivo Principal                     |
| :---------------- | :--------------- | :-------------------- | :------------------------------------- |
| **Message Queue** | Default (Direct) | 1 a 1 (Round-Robin)   | Escalabilidad y balanceo de carga.     |
| **Pub-Sub**       | Fanout           | 1 a N (Broadcast)     | Notificación masiva y desacoplamiento. |
| **DLQ**           | Direct/Config.   | Redirección vía nack  | Tolerancia a fallos y auditoría.       |
| **Backoff**       | Direct           | Reintento vía TTL     | Manejo de errores transitorios.        |

---

## 3. Escenarios de Uso

### ¿Cuándo usar cada uno?

1.  **Message Queue:** En sistemas de **procesamiento de imágenes o facturación**. Si el volumen sube, añades más consumidores y el sistema escala repartiendo mediante **Round-Robin**.
2.  **Pub-Sub:** En arquitecturas de **Microservicios**. Cuando un usuario se registra, el "Auth" publica y todos los servicios interesados reaccionan simultáneamente mediante un exchange **fanout**.
3.  **Dead Letter Queue:** En **Sistemas Críticos (Finanzas/Salud)**. Si una transacción falla (ej. error de formato), el rechazo (**nack**) la envía a la DLQ para que se analice sin detener el flujo principal.
4.  **Exponential Backoff:** En **Integraciones con APIs Externas** (ej. Stripe, AWS). Si hay un "Rate Limit", se programa un reintento utilizando **TTL**. El **Exponential Backoff** espera más tiempo en cada intento, evitando saturar la red externa.

---
