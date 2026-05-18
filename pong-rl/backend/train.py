import gymnasium as gym
from gymnasium import spaces
import numpy as np
import threading
import queue
import uvicorn
import logging
from fastapi import FastAPI, WebSocket
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
import os

action_queue = queue.Queue()
state_queue = queue.Queue()

app = FastAPI()

from starlette.websockets import WebSocketDisconnect

@app.websocket("/ws/pong")
async def pong_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("\n[+] Frontend conectado.")
    
    try:
        # Recibir estado inicial
        state_data = await websocket.receive_json()
        state_queue.put(state_data)
        
        while True:
            action = action_queue.get()
            await websocket.send_json({"action": int(action)})
            
            state_data = await websocket.receive_json()
            state_queue.put(state_data)
            
    except WebSocketDisconnect:
        print("\n[-] Frontend desconectado (Actualizaste la página). Esperando reconexión...")
    except Exception as e:
        print(f"\n[-] Error en WebSocket: {e}")

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")

class PongEnv(gym.Env):
    def __init__(self):
        super(PongEnv, self).__init__()
        self.action_space = spaces.Discrete(6) 
        self.observation_space = spaces.Box(low=-2000, high=2000, shape=(5,), dtype=np.float32)
        
    def reset(self, seed=None):
        while not state_queue.empty():
            state_queue.get()
            
        action_queue.put(0)
        state_data = state_queue.get()
        obs = np.array([
            state_data['ball_y'], 
            state_data['ai_y'], 
            state_data['ball_x'], 
            state_data['ball_vx'], 
            state_data['ball_vy']
        ], dtype=np.float32)
        return obs, {}

    def step(self, action):
        action_queue.put(action)
        state_data = state_queue.get()
        
        obs = np.array([
            state_data['ball_y'], 
            state_data['ai_y'], 
            state_data['ball_x'], 
            state_data['ball_vx'], 
            state_data['ball_vy']
        ], dtype=np.float32)
        
        reward = float(state_data['reward'])
        done = bool(state_data['done'])
        
        return obs, reward, done, False, {}

if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    print("\n" + "="*50)
    print("SERVIDOR DE ENTRENAMIENTO INICIADO")
    print("Abre tu navegador en http://localhost:5173/")
    print("Marca 'Modo Entrenamiento (x10)' y presiona 'Iniciar Juego'")
    print("="*50 + "\n")
    
    env = PongEnv()
    
    os.makedirs("./models", exist_ok=True)
    
    from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback, CallbackList
    
    eval_callback = EvalCallback(
        env, 
        best_model_save_path='./models/',
        log_path='./logs/', 
        eval_freq=5000, 
        deterministic=True, 
        render=False
    )
    
    # Guardar versiones del modelo cada 20,000 pasos (para que el usuario tenga niveles)
    checkpoint_callback = CheckpointCallback(
        save_freq=20000,
        save_path='./models/',
        name_prefix='pong_nivel'
    )
    
    callbacks = CallbackList([eval_callback, checkpoint_callback])
    
    model = PPO("MlpPolicy", env, verbose=1)
    
    try:
        model.learn(total_timesteps=100000, callback=callbacks)
        print("Entrenamiento completado y guardado en ./models/")
    except KeyboardInterrupt:
        print("\nEntrenamiento pausado manualmente. Guardando progreso...")
    finally:
        model.save("./models/best_model_interrupt.zip")
        print("Progreso guardado.")
        import os
        os._exit(0)
