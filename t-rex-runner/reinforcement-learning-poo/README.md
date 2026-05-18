# reinforcement-learning-poo

Reinforcement learning agent that learns to play the T-Rex Runner game.

## Goal

Train an agent using pixel observations (or game state) from `t-rex-runner` to maximize the distance score without crashing.

## Planned approach

- **Environment**: headless browser (Playwright) wrapping `t-rex-runner`, or a Python reimplementation of the physics for faster training.
- **Algorithm**: Proximal Policy Optimization (PPO) via [Stable-Baselines3](https://stable-baselines3.readthedocs.io/) or [Ray RLlib](https://docs.ray.io/en/latest/rllib/).
- **Observations**: game state (tRex position/speed, obstacle positions) or raw canvas pixels.
- **Reward**: +1 per frame survived, −10 on crash.

## Setup (coming soon)

```bash
cd reinforcement-learning-poo
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python train.py
```

## Structure (planned)

```
reinforcement-learning-poo/
├── env/           game environment (Gymnasium wrapper)
├── agents/        RL agent definitions
├── train.py       training entry point
├── eval.py        evaluation and demo
└── requirements.txt
```
