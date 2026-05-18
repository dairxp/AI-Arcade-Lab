import { BALL_SIZE, CANVAS_WIDTH, CANVAS_HEIGHT } from './config';
import { Paddle } from './Paddle';

export class Ball {
  x: number;
  y: number;
  vx: number;
  vy: number;
  speed: number;
  isHidden: boolean = false;
  lastTouch: Paddle | null = null;

  constructor(x: number, y: number, speed = 8, vx?: number, vy?: number) {
    this.x = x;
    this.y = y;
    this.speed = speed;
    this.vx = vx !== undefined ? vx : (Math.random() > 0.5 ? 1 : -1) * this.speed;
    this.vy = vy !== undefined ? vy : (Math.random() * 2 - 1) * this.speed;
  }

  reset() {
    this.x = CANVAS_WIDTH / 2;
    this.y = CANVAS_HEIGHT / 2;
    this.speed = 8;
    this.isHidden = false;
    this.lastTouch = null;
    this.vx = (Math.random() > 0.5 ? 1 : -1) * this.speed;
    this.vy = (Math.random() * 2 - 1) * this.speed;
  }

  draw(ctx: CanvasRenderingContext2D) {
    if (this.isHidden) {
      // Dibujar solo chispas tenues
      ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
      ctx.fillRect(this.x - 2, this.y - 2, 4, 4);
      return;
    }

    if (Math.abs(this.vx) > this.speed * 1.5) {
      ctx.fillStyle = '#ff6b81';
      ctx.fillRect(this.x - (BALL_SIZE+4)/2, this.y - (BALL_SIZE+4)/2, BALL_SIZE+4, BALL_SIZE+4);
    } else {
      ctx.fillStyle = '#fff';
      ctx.fillRect(this.x - BALL_SIZE/2, this.y - BALL_SIZE/2, BALL_SIZE, BALL_SIZE);
    }
  }

  update(player: Paddle, ai: Paddle): boolean {
    this.x += this.vx;
    this.y += this.vy;

    // Rebote vertical
    if (this.y - BALL_SIZE/2 <= 0 || this.y + BALL_SIZE/2 >= CANVAS_HEIGHT) {
      this.vy *= -1;
    }

    // Colisión Izquierda (Player)
    if (
      this.x - BALL_SIZE/2 <= player.x + player.width &&
      this.x + BALL_SIZE/2 >= player.x &&
      this.y >= player.y &&
      this.y <= player.y + player.height &&
      this.vx < 0
    ) {
      this.speed += 0.5;
      this.vx = player.isTurboActive ? this.speed * 2 : this.speed; 
      let hitPoint = this.y - (player.y + player.height/2);
      this.vy = hitPoint * (player.isTurboActive ? 0.25 : 0.15);
      
      if (player.lastMoveDir !== 0) this.vy += player.lastMoveDir * 5; 
      
      this.lastTouch = player;
      this.isHidden = false; // Reaparece al chocar
    }

    // Colisión Derecha (AI)
    if (
      this.x + BALL_SIZE/2 >= ai.x &&
      this.x - BALL_SIZE/2 <= ai.x + ai.width &&
      this.y >= ai.y &&
      this.y <= ai.y + ai.height &&
      this.vx > 0
    ) {
      this.speed += 0.5;
      this.vx = -(ai.isTurboActive ? this.speed * 2 : this.speed);
      let hitPoint = this.y - (ai.y + ai.height/2);
      this.vy = hitPoint * (ai.isTurboActive ? 0.25 : 0.15);
      
      if (ai.lastMoveDir !== 0) this.vy += ai.lastMoveDir * 5;
      
      this.lastTouch = ai;
      this.isHidden = false;
    }

    // Puntuación
    if (this.x < 0) {
      ai.score++;
      return true; // Alguien anotó
    } else if (this.x > CANVAS_WIDTH) {
      player.score++;
      return true;
    }
    return false;
  }
}
