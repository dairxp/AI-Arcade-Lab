import './style.css';
import { Paddle } from './game/Paddle';
import { Ball } from './game/Ball';
import { PowerUp } from './game/PowerUp';
import { PADDLE_WIDTH, PADDLE_HEIGHT, CANVAS_WIDTH, CANVAS_HEIGHT } from './game/config';

const canvas = document.getElementById('gameCanvas') as HTMLCanvasElement;
const ctx = canvas.getContext('2d')!;
canvas.width = CANVAS_WIDTH;
canvas.height = CANVAS_HEIGHT;

const player = new Paddle(20, CANVAS_HEIGHT / 2 - PADDLE_HEIGHT / 2);
const ai = new Paddle(CANVAS_WIDTH - 20 - PADDLE_WIDTH, CANVAS_HEIGHT / 2 - PADDLE_HEIGHT / 2, true);
let balls: Ball[] = [new Ball(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2)];
let powerUp: PowerUp | null = null;
let framesSinceLastPowerUp = 0;

let isRunning = false;
let isPaused = false;
let isTrainingMode = false;

// Variables de RL
let currentReward = 0;
let isDone = false;
let accumulatedEpisodeReward = 0;
let episodeRewards: number[] = [];

const keys = { w: false, s: false, d: false };

window.addEventListener('keydown', (e) => {
  if (e.key === 'w' || e.key === 'W') keys.w = true;
  if (e.key === 's' || e.key === 'S') keys.s = true;
  if (e.key === 'd' || e.key === 'D') keys.d = true;
  if (e.key === 'p' || e.key === 'P' || e.key === 'Escape') togglePause();
});

window.addEventListener('keyup', (e) => {
  if (e.key === 'w' || e.key === 'W') keys.w = false;
  if (e.key === 's' || e.key === 'S') keys.s = false;
  if (e.key === 'd' || e.key === 'D') keys.d = false;
});

const btnStart = document.getElementById('btn-start');
const btnPause = document.getElementById('btn-pause');
const statusText = document.getElementById('status-text');
const chkTraining = document.getElementById('chk-training') as HTMLInputElement;

chkTraining?.addEventListener('change', (e) => {
  isTrainingMode = (e.target as HTMLInputElement).checked;
  if (!isTrainingMode && isRunning && !isPaused) {
    requestAnimationFrame(gameLoop);
  }
});

function updateStatus(text: string) {
  if (statusText) statusText.innerText = text;
}

btnStart?.addEventListener('click', () => {
  if (!isRunning) {
    isRunning = true;
    isPaused = false;
    
    if (isTrainingMode) {
      updateStatus("Entrenando a máxima velocidad...");
      sendStateToServer();
    } else {
      updateStatus("Juego en curso...");
      requestAnimationFrame(gameLoop);
    }
  }
});

btnPause?.addEventListener('click', togglePause);

function togglePause() {
  if (!isRunning) return;
  isPaused = !isPaused;
  if (isPaused) {
    updateStatus("Juego Pausado");
    ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    ctx.fillStyle = '#fff';
    ctx.font = '40px monospace';
    ctx.textAlign = 'center';
    ctx.fillText("PAUSADO", CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2);
  } else {
    updateStatus(isTrainingMode ? "Entrenando a máxima velocidad..." : "Juego en curso...");
    if (!isTrainingMode) requestAnimationFrame(gameLoop);
    else sendStateToServer(); 
  }
}

function drawScore() {
  ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
  ctx.font = '48px monospace';
  ctx.textAlign = 'center';
  ctx.fillText(player.score.toString(), CANVAS_WIDTH / 4, 60);
  ctx.fillText(ai.score.toString(), 3 * CANVAS_WIDTH / 4, 60);
  
  ctx.setLineDash([10, 15]);
  ctx.beginPath();
  ctx.moveTo(CANVAS_WIDTH / 2, 0);
  ctx.lineTo(CANVAS_WIDTH / 2, CANVAS_HEIGHT);
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
  ctx.stroke();
  ctx.setLineDash([]);
}

let socket: WebSocket;
let aiAction = 0; 

function connectWebSocket() {
  socket = new WebSocket('ws://localhost:8000/ws/pong');
  socket.onopen = () => updateStatus('Conectado a IA Python | (W/S)');
  
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    aiAction = data.action;
    
    if (isRunning && !isPaused && isTrainingMode) {
      runGameFrame(); 
      // Nivel intermedio: setTimeout a 5ms. 
      // Entrena rápido (aprox x5) sin sobrecalentar ni forzar tu procesador.
      setTimeout(sendStateToServer, 5); 
    }
  };

  socket.onclose = () => {
    updateStatus('Desconectado de IA. Reintentando...');
    setTimeout(connectWebSocket, 2000);
  };
}
connectWebSocket();

function applyPowerUp(type: number, beneficiary: Paddle | null, ball: Ball) {
  if (type === 0 && beneficiary) beneficiary.makeGiant();
  else if (type === 1) ball.isHidden = true;
  else if (type === 2) {
    balls.push(new Ball(ball.x, ball.y, ball.speed, ball.vx, -ball.vy - 2));
    balls.push(new Ball(ball.x, ball.y, ball.speed, ball.vx, -ball.vy + 2));
  }
}

function sendStateToServer() {
  if (socket && socket.readyState === WebSocket.OPEN && balls.length > 0) {
    socket.send(JSON.stringify({
      ball_y: balls[0].y,
      ai_y: ai.y,
      ball_x: balls[0].x,
      ball_vx: balls[0].vx,
      ball_vy: balls[0].vy,
      reward: currentReward,
      done: isDone
    }));
    currentReward = 0; 
    
    if (isDone) {
      episodeRewards.push(accumulatedEpisodeReward);
      if (episodeRewards.length > 20) episodeRewards.shift();
      let avg = episodeRewards.reduce((a,b) => a+b, 0) / episodeRewards.length;
      const metricEl = document.getElementById('metric-reward');
      if (metricEl) metricEl.innerText = `Recompensa: ${avg.toFixed(2)}`;
      
      accumulatedEpisodeReward = 0;
      isDone = false;
    }
  }
}

// Extraemos la lógica de un solo "Frame"
function runGameFrame() {
  // 1. Actualizar Movimientos Player
  player.lastMoveDir = 0;
  if (isTrainingMode && balls.length > 0) {
    // CURRICULUM LEARNING: El maestro es bueno, pero falla el 15% de las veces.
    // Esto es crucial para que la IA anote goles y descubra el premio de +10.
    if (Math.random() > 0.15) {
      player.y = balls[0].y - player.height / 2;
    }
    if (Math.random() < 0.05) player.pushForward();
    else player.relax();
  } else {
    // Humano real
    if (keys.w) player.moveUp();
    if (keys.s) player.moveDown();
    if (keys.d) player.pushForward();
    else player.relax();
  }

  // 2. Aplicar acción de IA
  ai.lastMoveDir = 0;
  if (aiAction === 1 || aiAction === 3) ai.moveUp();
  if (aiAction === 2 || aiAction === 4) ai.moveDown();
  if (aiAction === 3 || aiAction === 4 || aiAction === 5) ai.pushForward();
  else ai.relax();

  // 3. PowerUps
  framesSinceLastPowerUp++;
  if (!powerUp && framesSinceLastPowerUp > 500 && Math.random() < 0.01) {
    powerUp = new PowerUp();
  }

  // Dibujar Fondo
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
  drawScore();
  if (powerUp) powerUp.draw(ctx);

  // RECOMPENSA DENSA (DENSE REWARD):
  // Le damos un premio minúsculo cada frame si se mantiene alineado a la pelota.
  // Esto acelera el aprendizaje un 500% porque la IA ya no adivina a ciegas.
  if (balls.length > 0) {
    let aiCenter = ai.y + ai.height / 2;
    let dist = Math.abs(aiCenter - balls[0].y);
    let denseReward = dist < ai.height / 2 ? 0.01 : -0.01;
    currentReward += denseReward;
    accumulatedEpisodeReward += denseReward;
  }

  // 4. Actualizar Pelotas y Recompensas Mayores
  for (let i = balls.length - 1; i >= 0; i--) {
    let b = balls[i];
    let scored = b.update(player, ai);
    
    // Premios menores por tocar la pelota
    if (b.lastTouch === ai && !scored) {
      currentReward += 1;
      accumulatedEpisodeReward += 1;
      b.lastTouch = null; 
    }

    if (powerUp && powerUp.checkCollision(b)) {
      applyPowerUp(powerUp.type, b.lastTouch, b);
      powerUp = null;
      framesSinceLastPowerUp = 0;
    }

    if (scored) {
      if (b.x < 0) {
        currentReward += 10;
        accumulatedEpisodeReward += 10;
      } else if (b.x > CANVAS_WIDTH) {
        currentReward -= 10;
        accumulatedEpisodeReward -= 10;
      }
      isDone = true; 
      balls.splice(i, 1);
    } else {
      b.draw(ctx);
    }
  }

  if (balls.length === 0) {
    balls.push(new Ball(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2));
    powerUp = null; 
  }

  player.draw(ctx);
  ai.draw(ctx);
}

// Bucle normal de Juego (Humano a 60 FPS)
function gameLoop() {
  if (isRunning && !isPaused && !isTrainingMode) {
    runGameFrame();
    
    // Si estamos jugando nosotros, igual le enviamos la info al servidor 
    // para que la IA decida su próximo movimiento en tiempo real
    if (socket && socket.readyState === WebSocket.OPEN) {
      sendStateToServer();
    }
    
    requestAnimationFrame(gameLoop);
  }
}

ctx.fillStyle = '#000';
ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
drawScore();
player.draw(ctx);
ai.draw(ctx);
if (balls.length > 0) balls[0].draw(ctx);
