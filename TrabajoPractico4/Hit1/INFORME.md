# Referencia de Shaders, WebGL y ShaderToy

---

## 1. Tipos de shaders

Un **shader** es una operación programable que se aplica a los datos mientras atraviesan el pipeline de renderizado, corriendo en la GPU en paralelo masivo.

### Vertex shaders
Se ejecutan una vez por cada vértice 3D. Transforman la posición 3D en espacio virtual a la coordenada 2D de pantalla (más el valor de profundidad para el Z-buffer). Pueden manipular posición, color y coordenadas de textura, pero **no pueden crear nuevos vértices**.

### Geometry shaders
Se ejecutan tras los vertex shaders. Reciben como entrada una primitiva completa (por ejemplo, los tres vértices de un triángulo) y pueden emitir cero o más primitivas nuevas. Usos típicos: generación de sprites, teselación de geometría, extrusión de shadow volumes.

### Fragment shaders (pixel shaders)
Calculan el color y otros atributos de cada fragmento — una unidad de trabajo que afecta como máximo a un píxel de salida. Operan en 2D: tienen acceso a la coordenada de pantalla pero **no a la geometría de la escena**. Son el tipo central de este práctico.

### Tessellation shaders
Añaden dos etapas — **hull shader** (control) y **domain shader** (evaluación) — que subdividen mallas simples en mallas más finas en tiempo de ejecución, típicamente en función de la distancia a la cámara (level-of-detail).

### Primitive and Mesh shaders
Introducidos por AMD (Vega, 2017) y Nvidia (Turing, 2018). Modelados sobre los compute shaders pero con acceso a datos de geometría. Permiten que la GPU maneje algoritmos más complejos, descargando trabajo de la CPU y aumentando significativamente la cantidad de triángulos procesables por frame.

### Ray-tracing shaders
Soportados vía DirectX Raytracing (Microsoft), Vulkan/GLSL/SPIR-V (Khronos) y Metal (Apple). Ejecutan algoritmos de trazado de rayos en hardware especializado (Nvidia los llama "ray tracing cores").

---

## 2. Pipeline de renderizado WebGL

WebGL expone un pipeline de rasterización con seis etapas fundamentales:

| Etapa | Nombre | Descripción | Espacio |
|-------|--------|-------------|---------|
| 1 | **Vertex data** | Se suministran posiciones, colores y coordenadas de textura desde buffers CPU | 3D |
| 2 | **Vertex shader** | Transforma cada vértice de espacio 3D a clip space | 3D |
| 3 | **Rasterización** | Ensamblado de primitivas (triángulos) y conversión a fragmentos 2D | 3D → 2D |
| 4 | **Fragment shader** | Calcula el color de cada fragmento/píxel | 2D |
| 5 | **Testing & blending** | Depth test, stencil test, alpha blending | 2D |
| 6 | **Framebuffer** | Escritura del píxel final en la imagen de salida | 2D |

### División 3D / 2D

- **Etapas 1–3** corresponden al procesamiento 3D: manipulan geometría, vértices y la proyección al plano de pantalla.
- **Etapas 4–6** corresponden al procesamiento 2D: trabajan sobre fragmentos ya proyectados, sin acceso a la geometría original de la escena.

---

## 3. Video post-processing

El post-processing es el proceso de mejorar la calidad percibida de un video o imagen tras el proceso de decodificación/renderizado. En renderizado 3D en tiempo real, en lugar de renderizar los objetos 3D directamente a pantalla, la escena se renderiza primero a un buffer en la memoria de la tarjeta gráfica. Luego se utilizan pixel shaders para aplicar filtros de post-procesado a ese buffer de imagen antes de mostrarlo.

**Efectos típicos:** ambient occlusion (SSAO), anti-aliasing (FXAA, SMAA), bloom, tone mapping, corrección de color, depth of field, motion blur.

Los efectos de post-processing ocurren **después de la etapa 6** (framebuffer), pero antes de la presentación final. Técnicamente se implementan como un nuevo pase del fragment shader (etapa 4) sobre un quad que cubre toda la pantalla, tomando como entrada el framebuffer renderizado. Es decir, la escena 3D completa se convierte en una textura 2D y el pixel shader la procesa píxel a píxel.

---

## 4. Entradas del shader en ShaderToy

ShaderToy provee las siguientes entradas (uniforms) a los shaders de imagen:

| Tipo | Nombre | Descripción |
|------|--------|-------------|
| `vec3` | `iResolution` | Resolución del viewport en píxeles (x, y, aspect ratio) |
| `float` | `iTime` | Tiempo de reproducción del shader en segundos |
| `float` | `iTimeDelta` | Tiempo de renderizado del último frame en segundos |
| `float` | `iFrameRate` | Frames por segundo actuales |
| `int` | `iFrame` | Número de frame actual desde el inicio |
| `float[4]` | `iChannelTime` | Tiempo de reproducción de cada canal de entrada |
| `vec3[4]` | `iChannelResolution` | Resolución de cada canal de entrada en píxeles |
| `vec4` | `iMouse` | Coordenadas del mouse: `xy` = posición actual (si botón izq. presionado), `zw` = posición del último click |
| `samplerXX` | `iChannel0..3` | Canales de entrada (texturas 2D, cubemaps, buffers, video, audio) |
| `vec4` | `iDate` | Fecha: (año, mes, día, segundos del día) |
| `float` | `iSampleRate` | Frecuencia de muestreo de audio (p. ej., 44100 Hz) |

### Salidas posibles de los pixel shaders en ShaderToy

| Tipo | Nombre | Descripción |
|------|--------|-------------|
| `vec4` | `fragColor` | Salida principal de color del fragmento actual. Componentes: (R, G, B, A) en rango [0.0, 1.0]. Se recomienda dejar alpha = 1.0. |
| `vec2` | retorno de `mainSound()` | Solo en sound shaders: devuelve el valor de onda estéreo (canal izquierdo, canal derecho) para la muestra actual. |

En los **image shaders** (el tipo normal) solo existe `fragColor`. Los **buffer shaders** (A, B, C, D) también escriben en `fragColor`, pero su salida alimenta una textura offscreen que puede ser leída por otros shaders como `iChannel`.

### Firma de la función

`mainImage` recibe `fragCoord` como entrada (`in`) — las coordenadas en píxeles del fragmento actual — y escribe el resultado en `fragColor` como salida (`out`). El shader se ejecuta en paralelo en la GPU, una vez por cada píxel de la pantalla.

### Coordenadas UV normalizadas

`uv` es el vector de coordenadas normalizadas del píxel actual, con valores entre 0.0 y 1.0 en ambos ejes. Se calcula dividiendo las coordenadas absolutas en píxeles (`fragCoord`) por la resolución total del canvas (`iResolution.xy`).

Al dividir cada coordenada por el valor máximo posible de la pantalla, el valor UV se mantiene constante aunque cambie el tamaño del canvas. Si se usaran coordenadas absolutas (`fragCoord` directamente), un mismo shader produciría resultados distintos en pantallas de 800×600 y 1920×1080 — las formas y patrones quedarían distorsionados o cortados.

Las UV son independientes de la resolución:
- El píxel de la esquina inferior izquierda siempre es `(0, 0)`
- El píxel de la esquina superior derecha siempre es `(1, 1)`

### Animación con `iTime`

La entrada `iTime` avanza continuamente en segundos a medida que el shader se re-ejecuta en cada frame. Al incorporar `iTime` dentro de una función periódica como `cos()`, el argumento cambia constantemente, desplazando el valor calculado frame a frame. El valor de `iTime` se incrementa gradualmente, lo que provoca que el coseno cambie suavemente con el tiempo.

El resultado visible es una animación continua, aunque el propio shader sea una función matemática estática: cada frame recibe un `iTime` distinto y produce una imagen distinta.

### Operaciones vectoriales en GLSL

GLSL soporta operaciones vectoriales escalares y **broadcasting**: cuando se opera un escalar (`0.5`) con un vector (`vec3`), el escalar se aplica a cada componente del vector automáticamente. Además, `cos()` en GLSL está sobrecargada — acepta tanto `float` como `vec2`, `vec3`, `vec4` y devuelve el mismo tipo.

Ejemplo de flujo con swizzle:

```glsl
uv.xyx                          // vec3(uv.x, uv.y, uv.x)
iTime + uv.xyx + vec3(0,2,4)   // vec3 (suma componente a componente)
cos(vec3)                       // vec3 con coseno aplicado a cada componente
0.5 * vec3                      // vec3 (escalar × vector)
0.5 + vec3                      // vec3 (broadcast del escalar)
```

El resultado es que `col.r`, `col.g` y `col.b` reciben valores distintos porque `vec3(0,2,4)` desplaza el argumento del coseno para cada canal, evitando que los tres colores sean idénticos.

### Construcción de `vec4`

`vec4` acepta múltiples formas de construcción en GLSL:

```glsl
vec4(r, g, b, a)    // 4 floats individuales
vec4(vec3, a)       // vec3 + 1 float  ← forma común en shaders
vec4(vec2, vec2)    // 2 vec2
vec4(float)         // repite el mismo valor en los 4 componentes
vec4(vec4)          // copia
```

Los componentes de `fragColor` representan `(R, G, B, A)` en `[0.0, 1.0]`. Por ejemplo, `fragColor = vec4(col, 1.0)` empaqueta el color calculado con alpha completamente opaco.

### Swizzling

**Swizzling** es la capacidad de GLSL de reordenar y replicar componentes de un vector usando sufijos de letras. Los conjuntos disponibles son intercambiables pero no mezclables entre sí:

| Conjunto | Uso semántico | Componentes |
|----------|---------------|-------------|
| `x y z w` | posición / genérico | 1°, 2°, 3°, 4° componente |
| `r g b a` | color | ídem |
| `s t p q` | coordenadas de textura | ídem |

Se puede leer cualquier combinación de hasta 4 letras del mismo conjunto:

```glsl
// Dado: vec2 uv = vec2(0.3, 0.7)
uv.x        // float  → 0.3
uv.yx       // vec2   → vec2(0.7, 0.3)      (invertido)
uv.xyx      // vec3   → vec3(0.3, 0.7, 0.3) (swizzle típico en shaders)
uv.xyxy     // vec4   → vec4(0.3, 0.7, 0.3, 0.7)
uv.xx       // vec2   → vec2(0.3, 0.3)      (replicado)
```

Propiedades de swizzle disponibles por tipo:

- `vec2`: combinaciones de `x,y` → produce `float`, `vec2`
- `vec3`: combinaciones de `x,y,z` → produce `float`, `vec2`, `vec3`
- `vec4`: combinaciones de `x,y,z,w` → produce `float`, `vec2`, `vec3`, `vec4`

El swizzle también puede usarse como **lvalue** para asignar:

```glsl
vec4 v;
v.rgb = vec3(1.0, 0.5, 0.0);  // asigna solo los primeros 3 componentes
v.ba  = vec2(0.0, 1.0);       // asigna b y a
```