# Soldaditos RTS - Juego de Estrategia 2D con PPO

Juego de estrategia en tiempo real (RTS) 2D donde dos equipos de agentes PPO se enfrentan en combate.

## Características

- **Motor del juego**: Pygame
- **RL Framework**: Stable-Baselines3 (PPO)
- **Entrenamiento**: Self-play
- **Tipo de juego**: RTS simplificado con unidades que se mueven y atacan

## Estructura del Proyecto

```
soldaditoss/
├── src/
│   ├── game/          # Lógica del juego RTS
│   ├── env/           # Entorno Gymnasium
│   └── agents/        # Configuración de agentes PPO
├── scripts/           # Scripts de entrenamiento y visualización
├── models/            # Modelos entrenados guardados
├── logs/              # Logs de TensorBoard
└── requirements.txt   # Dependencias
```


## Entrenamiento - prueba rápida
```bash
python scripts/train.py --timesteps 30000 --save-freq 10000
python scripts/play.py
```

## Instalación

```bash
.\venv\Scripts\activate 
```

```bash
pip install -r requirements.txt
```

## Uso

### Entrenar agentes
```bash
python scripts/train.py
```

### Visualizar partida
```bash
python scripts/play.py --model models/best_model.zip
```

## Mecánicas del Juego

- Dos equipos (Azul vs Rojo)
- Unidades que pueden moverse y atacar
- Victoria por eliminación de todas las unidades enemigas
- Observaciones: posiciones de unidades aliadas y enemigas, salud, etc.
- Acciones: mover unidades, atacar objetivos

## Entrenamiento

El sistema usa self-play donde los agentes mejoran jugando entre ellos, creando una competición evolutiva.
