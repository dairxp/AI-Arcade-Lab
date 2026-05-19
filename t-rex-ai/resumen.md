# Resumen del Proyecto: T-Rex AI (El Juego Original)

---

## BASE DE DATOS
**No se utiliza ninguna Base de Datos (ni SQL, ni NoSQL).** 
El sistema no aprende de partidas pregrabadas ni datasets externos. Se utiliza una "población" generada de manera procedimental que vive en la Memoria RAM del navegador durante la ejecución. Los pesos (genes) de los cerebros de los dinosaurios que logran aprender se almacenan algorítmicamente en tiempo de ejecución. 

## ALGORITMO USADO
El proyecto emplea **Neuroevolución con Algoritmos Genéticos** junto con una **Red Neuronal Perceptrón Multicapa (Feed-Forward)** customizada en TypeScript (`src/ai/NeuralNetwork.ts`), sin librerías pesadas como TensorFlow.
*   **Capas:** 1 Capa de Entrada (5 neuronas), 2 Capas Ocultas (8 y 6 neuronas respectivamente) y 1 Capa de Salida (2 neuronas).
*   **Función de Activación:** `tanh` (Tangente hiperbólica) en las capas ocultas y `sigmoid` en la salida.
*   **Inputs (Capa de Entrada):** Es la forma en que el T-Rex "percibe" su entorno en cada fotograma. Está compuesta por **5 neuronas** que reciben los siguientes datos exactos:
    1.  **Distancia al obstáculo:** Proximidad horizontal exacta hacia el peligro más cercano.
    2.  **Ancho del obstáculo:** Sirve para saber si es un cactus pequeño o una fila de varios cactus (le ayuda a la red a predecir si el salto debe ser largo).
    3.  **Altura del obstáculo:** Clave para distinguir si el peligro es terrestre (cactus / hay que saltar) o aéreo (pterodáctilo / hay que agacharse).
    4.  **Posición Y del Dinosaurio:** Le avisa a su propio cerebro si actualmente está en el suelo o flotando en el aire.
    5.  **Velocidad del Entorno:** Ya que el juego acelera progresivamente, este input es crucial para que la IA "ajuste sus reflejos" y salte unas fracciones de segundo antes cuando el juego va a máxima velocidad.
*   **Outputs (Capa de Salida):** Existe **una sola Capa de Salida**, pero esta capa contiene **2 neuronas distintas** en su interior. Tras procesar toda la matemática de las capas ocultas, la red escupe 2 valores de probabilidad (entre 0 y 1, gracias a la función sigmoide):
    *   **Neurona 1 (Índice 0):** Si su valor de encendido supera el `0.5`, la IA decide accionar el **Salto (Simula la tecla Espacio)**.
    *   **Neurona 2 (Índice 1):** Si su valor de encendido supera el `0.5`, la IA decide **Agacharse (Simula la Flecha Abajo)**. Si la IA ya estuviera en el aire, apretar esta neurona provoca una maniobra de **Caída Rápida** hacia el suelo.
    *   *(Si ninguna de las 2 neuronas supera el umbral de 0.5, el dinosaurio simplemente sigue corriendo sin alterar su estado)*.
*   **Genética:** Emplea de cruza uniforme (Crossover), Mutación Gaussiana, Elitismo (pasar los mejores directamente a la siguiente ola sin tocar), y Selección por Ruleta.

## REGLAS DEL JUEGO
Este es el juego **clásico y original de Chrome**, concebido inicialmente para ser jugado por humanos utilizando la **barra espaciadora o la flecha arriba** para saltar, y la flecha abajo para agacharse (evadir pterodáctilos voladores).
*   Desplazamiento lateral infinito.
*   El juego acelera progresivamente (haciéndolo cada vez más difícil).
*   Cualquier colisión (con cactus o pterodáctilo) resulta en inhabilitación/muerte.

## PROCESO DE ENTRENAMIENTO DE DATOS
Se desecha el Backpropagation regular (como haría Python). En su lugar, el entrenamiento ocurre por **supervivencia del más fuerte**:
1. Se clonan **múltiples individuos (dinosaurios)** por cada generación. Todos empiezan saltando a lo loco (genes aleatorios).
2. Se evalúa a cada individuo en un entorno "acelerado" ciego que salta la restricción visual de 60 FPS, permitiendo que la simulación ocurra lo más rápido que la CPU local lo permita.
3. El dinosaurio que llega más lejos obtiene mayor **Fitness** y sus matrices se cruzarán para la siguiente generación. 
4. Todo el entrenamiento está acoplado en tiempo real dentro del ciclo de requestAnimationFrame del frontend (Vite + TS).

## NIVEL MÁXIMO DE ENTRENAMIENTO
No hay un "número de steps" estático como límite. El algoritmo evoluciona generación tras generación. El nivel máximo, visualizado como `allTimeBest` en la UI, es un clímax donde **la red neuronal ha aprendido a sincronizar su altura, salto y caída en caída rápida de manera perfecta contra la máxima velocidad del sistema**. Alguien en este nivel salta obstáculos evadiéndolos eternamente sin nunca fallar un cálculo probabilístico.

## ACCURACY (PRECISIÓN / FITNESS)
Dado que no es Aprendizaje Supervisado, la palabra *Accuracy* no existe aquí. El progreso de la matriz red/genética del dinosaurio se cuantifica en función de su **Fitness (Recompensa)**, la cual escala a partir de la distancia sobrevivída:
*   `Puntuación = Distancia (Pixeles Reales Evadidos)`
*   `Fitness = (Puntuación)² / Suma de Puntuaciones de toda la Población` (Matemática cuadrática para beneficiar drásticamente al que sobrevivió más).
El modelo posee aprendizaje exitoso cuando su distancia transita al infinito con un margen de error nulo ante los espawneos del entorno.