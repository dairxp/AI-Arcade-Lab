from fastapi import FastAPI, WebSocket
from stable_baselines3 import PPO
import uvicorn
import numpy as np
import os
import logging
from starlette.websockets import WebSocketDisconnect

# Silenciar errores falsos positivos de Windows asyncio (WinError 10054)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

app = FastAPI()

# Cargar el modelo experto (el mejor que guardó el entrenamiento)
MODEL_PATH = "models/best_model.zip"

#Modelo SEMI TORPE
#MODEL_PATH = "models/pong_nivel_20000_steps.zip"

if os.path.exists(MODEL_PATH):
    model = PPO.load(MODEL_PATH)
    print("==================================================")
    print("MODELO EXPERTO CARGADO CON ÉXITO")
    print("==================================================")
else:
    print("No se encontró el modelo. Asegúrate de haber entrenado primero.")
    exit()

@app.websocket("/ws/pong")
async def pong_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("\n[+] Humano conectado. ¡Prepárate para perder!")
    
    try:
        while True:
            state_data = await websocket.receive_json()
            
            # Leer exactamente lo mismo que leíamos en el entrenamiento
            obs = np.array([
                state_data['ball_y'], 
                state_data['ai_y'], 
                state_data['ball_x'], 
                state_data['ball_vx'], 
                state_data['ball_vy']
            ], dtype=np.float32)
            
            # Pedirle a la IA entrenada que decida su movimiento (0 a 5)
            # deterministic=True asegura que use su mejor estrategia sin experimentar
            action, _states = model.predict(obs, deterministic=True)
            
            await websocket.send_json({"action": int(action)})
            
    except WebSocketDisconnect:
        print("\n[-] Humano desconectado.")
    except Exception as e:
        print(f"\n[-] Error: {e}")

if __name__ == '__main__':
    import threading
    import time
    
    # Ejecutamos uvicorn en un hilo en segundo plano
    server_thread = threading.Thread(
        target=uvicorn.run, 
        args=(app,), 
        kwargs={"host": "0.0.0.0", "port": 8000, "log_level": "warning"}, 
        daemon=True
    )
    server_thread.start()
    
    try:
        # El hilo principal se queda esperando para poder atrapar el Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[+] Servidor apagado correctamente a peticion del usuario (Ctrl+C).")
        import os
        os._exit(0)
