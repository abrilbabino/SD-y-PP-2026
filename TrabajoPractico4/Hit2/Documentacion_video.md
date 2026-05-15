# Pintando con código
## Documentación
El video expone la creación de un paisaje fotorrealista evaluando el color RGB de cada píxel en el lienzo mediante una única y extensa función matemática compuesta. 

En lugar de procesar mallas tridimensionales clásicas, el autor emplea programación de shaders para modelar el terreno subdividiéndolo en celdas espaciales continuas manejadas por polinomios cúbicos (f(x)=ax^3 + bx^2 + cx + d), garantizando transiciones suaves con derivadas nulas en sus uniones. 

Elementos orgánicos como nubes y vegetación se generan proceduralmente mediante funciones de ruido, operaciones interpoladas (smoothstep) y funciones de campos de distancia firmada (SDF) convertidas en periódicas al confinarlas a sistemas de coordenadas locales. 

Simultáneamente, los cálculos de iluminación direccional, proyecciones de sombras y atenuación atmosférica se resuelven aplicando operaciones vectoriales directas, productos punto entre vectores normales y exponenciales analíticas (e^x) para emular el comportamiento físico de la luz sin sobrecargar los cálculos del programa.

## Conclusiones
- La técnica de generar coordenadas locales mediante empaquetado para evaluar una única función SDF periódica, logrando renderizar millones de esferas (árboles), sortea de lleno el cuello de botella secuencial de la CPU que supondría almacenar, iterar y calcular vértices individuales para cada instancia geométrica.

- La sustitución de cálculos trigonométricos (senos y cosenos) por triples pitagóricos en las matrices de rotación, sumado a la simplificación de resolutores numéricos complejos por ecuaciones matemáticas aproximadas, evidencia una optimización algorítmica pensada para maximizar el rendimiento y el balance de carga de trabajo computacional en las arquitecturas masivamente paralelas de las GPU.

- El autor redefine el uso del pipeline de renderizado al prescindir casi por completo de la carga en memoria y el procesamiento en los Vertex Shaders. Toda la complejidad visual recae enteramente en un Pixel Shader monumental que, píxel a píxel, ejecuta esta gran función singular para devolver el vector de color RGB correspondiente a las coordenadas (x, y) de la pantalla.
