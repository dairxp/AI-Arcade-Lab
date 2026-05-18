import { getContext } from './canvas';
import { FPS, IS_HIDPI } from './constants';
import { getSpriteImage } from './sprite';
import type { SpritePos } from './types';

const DIMENSIONS = {
  WIDTH: 600,
  HEIGHT: 12,
  YPOS: 127
};

const BUMP_THRESHOLD = 0.5;

export class HorizonLine {
  private ctx: CanvasRenderingContext2D;
  private sourceWidth: number;
  private sourceHeight: number;
  private sourceXPos: [number, number];
  private xPos: [number, number] = [0, DIMENSIONS.WIDTH];
  private yPos = DIMENSIONS.YPOS;

  constructor(canvas: HTMLCanvasElement, private spritePos: SpritePos) {
    this.ctx = getContext(canvas);
    this.sourceWidth = IS_HIDPI ? DIMENSIONS.WIDTH * 2 : DIMENSIONS.WIDTH;
    this.sourceHeight = IS_HIDPI ? DIMENSIONS.HEIGHT * 2 : DIMENSIONS.HEIGHT;
    this.sourceXPos = [spritePos.x, spritePos.x + DIMENSIONS.WIDTH];
    this.draw();
  }

  private getRandomType(): number {
    return Math.random() > BUMP_THRESHOLD ? DIMENSIONS.WIDTH : 0;
  }

  private draw(): void {
    const image = getSpriteImage();

    this.ctx.drawImage(
      image,
      this.sourceXPos[0],
      this.spritePos.y,
      this.sourceWidth,
      this.sourceHeight,
      this.xPos[0],
      this.yPos,
      DIMENSIONS.WIDTH,
      DIMENSIONS.HEIGHT
    );

    this.ctx.drawImage(
      image,
      this.sourceXPos[1],
      this.spritePos.y,
      this.sourceWidth,
      this.sourceHeight,
      this.xPos[1],
      this.yPos,
      DIMENSIONS.WIDTH,
      DIMENSIONS.HEIGHT
    );
  }

  private updateXPos(pos: 0 | 1, increment: number): void {
    const other = pos === 0 ? 1 : 0;
    this.xPos[pos] -= increment;
    this.xPos[other] = this.xPos[pos] + DIMENSIONS.WIDTH;

    if (this.xPos[pos] <= -DIMENSIONS.WIDTH) {
      this.xPos[pos] += DIMENSIONS.WIDTH * 2;
      this.xPos[other] = this.xPos[pos] - DIMENSIONS.WIDTH;
      this.sourceXPos[pos] = this.getRandomType() + this.spritePos.x;
    }
  }

  update(deltaTime: number, speed: number): void {
    const increment = Math.floor((speed * FPS) / 1000 * deltaTime);
    if (this.xPos[0] <= 0) this.updateXPos(0, increment);
    else this.updateXPos(1, increment);
    this.draw();
  }

  reset(): void {
    this.xPos[0] = 0;
    this.xPos[1] = DIMENSIONS.WIDTH;
  }
}
