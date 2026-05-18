from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor
from typing import Optional, Dict, Any
import torch

# TrainingCallback ahora está en src.training.callbacks
# Este archivo solo maneja la creación de agentes PPO


def create_ppo_agent(env,
                     policy: str = "MlpPolicy",
                     learning_rate: float = 3e-4,
                     n_steps: int = 2048,
                     batch_size: int = 64,
                     n_epochs: int = 10,
                     gamma: float = 0.99,
                     gae_lambda: float = 0.95,
                     clip_range: float = 0.2,
                     ent_coef: float = 0.01,
                     vf_coef: float = 0.5,
                     max_grad_norm: float = 0.5,
                     policy_kwargs: Optional[Dict[str, Any]] = None,
                     tensorboard_log: Optional[str] = "./logs/",
                     verbose: int = 1,
                     device: str = "auto") -> PPO:
    """
    Crea un agente PPO con configuración optimizada para RTS

    Args:
        env: Entorno Gymnasium
        policy: Tipo de política ('MlpPolicy' para observaciones vectoriales)
        learning_rate: Tasa de aprendizaje
        n_steps: Número de steps antes de actualizar la política
        batch_size: Tamaño del minibatch
        n_epochs: Número de épocas por actualización
        gamma: Factor de descuento
        gae_lambda: Factor para GAE (Generalized Advantage Estimation)
        clip_range: Rango de clipping para la función objetivo
        ent_coef: Coeficiente de entropía para exploración
        vf_coef: Coeficiente de la función de valor
        max_grad_norm: Valor máximo para clipping de gradientes
        policy_kwargs: Argumentos adicionales para la política
        tensorboard_log: Directorio para logs de TensorBoard
        verbose: Nivel de verbosidad
        device: Dispositivo ('auto', 'cuda', 'cpu')

    Returns:
        Modelo PPO configurado
    """

    # Configuración por defecto de la red neuronal
    if policy_kwargs is None:
        policy_kwargs = {
            "net_arch": dict(pi=[256, 256], vf=[256, 256]),  # Redes separadas para política y valor
            "activation_fn": torch.nn.ReLU
        }

    # Crear el modelo PPO
    # NOTA: Para políticas MLP (vectoriales), CPU suele ser más rápido que GPU
    # debido al overhead de transferencia de datos. GPU solo ayuda con CNN (imágenes).
    model = PPO(
        policy=policy,
        env=env,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        gamma=gamma,
        gae_lambda=gae_lambda,
        clip_range=clip_range,
        ent_coef=ent_coef,
        vf_coef=vf_coef,
        max_grad_norm=max_grad_norm,
        policy_kwargs=policy_kwargs,
        tensorboard_log=tensorboard_log,
        verbose=verbose,
        device=device
    )

    return model


def load_agent(path: str, env, device: str = "cpu") -> PPO:
    """
    Carga un agente PPO desde un archivo

    Args:
        path: Ruta al archivo .zip del modelo
        env: Entorno para el agente
        device: Dispositivo ('auto', 'cuda', 'cpu')

    Returns:
        Modelo PPO cargado
    """
    return PPO.load(path, env=env, device=device)


def save_agent(model: PPO, path: str) -> None:
    """
    Guarda un agente PPO

    Args:
        model: Modelo a guardar
        path: Ruta donde guardar (sin extensión)
    """
    model.save(path)
    print(f"Model saved to {path}.zip")
