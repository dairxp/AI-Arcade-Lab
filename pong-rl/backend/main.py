import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/pong")
async def pong_websocket(websocket: WebSocket):
    await websocket.accept()
    print("¡Cliente Frontend conectado!")
    
    try:
        while True:
            # Recibir estado del juego desde JS
            data = await websocket.receive_text()
            state = json.loads(data)
            
            # state contiene: ball_y, ai_paddle_y, etc.
            ball_y = state.get("ball_y", 0)
            ai_y = state.get("ai_y", 0)
            
            # Lógica DUMMY de IA por ahora (solo sigue la pelota)
            # 0: Nada, 1: Arriba, 2: Abajo
            action = 0
            paddle_center = ai_y + 50 # PADDLE_HEIGHT/2
            
            if ball_y < paddle_center - 10:
                action = 1
            elif ball_y > paddle_center + 10:
                action = 2
                
            # Enviar acción al Frontend
            await websocket.send_json({"action": action})
            
    except WebSocketDisconnect:
        print("Cliente desconectado")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
