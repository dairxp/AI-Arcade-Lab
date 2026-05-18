import { BALL_SIZE, CANVAS_WIDTH, CANVAS_HEIGHT } from './config';
import { Ball } from './Ball';

export class PowerUp {
  x: number;
  y: number;
  size: number = 30;
  type: number; // 0: Gigante, 1: Fantasma, 2: Multiball
  color: string;

  constructor() {
    this.x = CANVAS_WIDTH / 2 - this.size / 2;
    this.y = Math.random() * (CANVAS_HEIGHT - this.size * 2) + this.size;
    this.type = Math.floor(Math.random() * 3);
    
    if (this.type === 0) this.color = '#f1c40f'; // Amarillo (Gigante)
    else if (this.type === 1) this.color = '#9b59b6'; // Morado (Fantasma)
    else this.color = '#3498db'; // Azul (Multiball)
  }

  draw(ctx: CanvasRenderingContext2D) {
    ctx.fillStyle = this.color;
    ctx.fillRect(this.x, this.y, this.size, this.size);
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.strokeRect(this.x, this.y, this.size, this.size);
  }

  checkCollision(ball: Ball): boolean {
    if (
      ball.x + BALL_SIZE/2 >= this.x &&
      ball.x - BALL_SIZE/2 <= this.x + this.size &&
      ball.y + BALL_SIZE/2 >= this.y &&
      ball.y - BALL_SIZE/2 <= this.y + this.size
    ) {
      return true;
    }
    return false;
  }
}
