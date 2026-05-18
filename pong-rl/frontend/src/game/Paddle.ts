import { PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_SPEED, CANVAS_HEIGHT } from './config';

export class Paddle {
  x: number;
  baseX: number;
  y: number;
  width: number;
  height: number;
  score: number = 0;
  isAI: boolean;
  isTurboActive: boolean = false;
  lastMoveDir: number = 0;
  isGiant: boolean = false;
  giantTimer: number | null = null;

  constructor(x: number, y: number, isAI: boolean = false) {
    this.x = x;
    this.baseX = x;
    this.y = y;
    this.width = PADDLE_WIDTH;
    this.height = PADDLE_HEIGHT;
    this.isAI = isAI;
  }

  draw(ctx: CanvasRenderingContext2D) {
    ctx.fillStyle = this.isGiant ? '#f1c40f' : (this.isTurboActive ? '#ff4757' : '#fff'); 
    ctx.fillRect(this.x, this.y, this.width, this.height);
  }

  moveUp() {
    this.y = Math.max(0, this.y - PADDLE_SPEED);
    this.lastMoveDir = -1;
  }

  moveDown() {
    this.y = Math.min(CANVAS_HEIGHT - this.height, this.y + PADDLE_SPEED);
    this.lastMoveDir = 1;
  }

  pushForward() {
    if (!this.isTurboActive) {
      this.width = PADDLE_WIDTH + 40;
      if (this.isAI) {
        this.x = this.baseX - 40;
      } else {
        this.width = PADDLE_WIDTH + 40; // visual representation
      }
      this.isTurboActive = true;
    }
  }

  relax() {
    this.x = this.baseX;
    this.width = PADDLE_WIDTH;
    this.isTurboActive = false;
  }

  makeGiant() {
    this.isGiant = true;
    this.height = PADDLE_HEIGHT * 2;
    // Asegurar que no se salga de la pantalla al crecer
    this.y = Math.max(0, Math.min(CANVAS_HEIGHT - this.height, this.y - PADDLE_HEIGHT/2));
    
    // Si ya era gigante, limpiamos el timer anterior
    if (this.giantTimer !== null) clearTimeout(this.giantTimer);

    this.giantTimer = window.setTimeout(() => {
      this.isGiant = false;
      this.height = PADDLE_HEIGHT;
      // Ajustar Y al encogerse para que no se salga
      this.y = Math.min(CANVAS_HEIGHT - this.height, this.y);
      this.giantTimer = null;
    }, 10000);
  }
}
