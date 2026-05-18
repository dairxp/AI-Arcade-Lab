import { getContext } from './canvas';
import { IS_HIDPI } from './constants';
import { getSpriteImage } from './sprite';
import type { SpritePos } from './types';
import { getRandomNum } from './utils';

const CONFIG = {
  HEIGHT: 14,
  MAX_CLOUD_GAP: 400,
  MAX_SKY_LEVEL: 30,
  MIN_CLOUD_GAP: 100,
  MIN_SKY_LEVEL: 71,
  WIDTH: 46
};

export class Cloud {
  static readonly WIDTH = CONFIG.WIDTH;

  private ctx: CanvasRenderingContext2D;
  xPos: number;
  yPos = 0;
  remove = false;
  cloudGap: number;

  constructor(canvas: HTMLCanvasElement, private spritePos: SpritePos, containerWidth: number) {
    this.ctx = getContext(canvas);
    this.xPos = containerWidth;
    this.cloudGap = getRandomNum(CONFIG.MIN_CLOUD_GAP, CONFIG.MAX_CLOUD_GAP);
    this.init();
  }

  private init(): void {
    this.yPos = getRandomNum(CONFIG.MAX_SKY_LEVEL, CONFIG.MIN_SKY_LEVEL);
    this.draw();
  }

  draw(): void {
    this.ctx.save();
    let sourceWidth = CONFIG.WIDTH;
    let sourceHeight = CONFIG.HEIGHT;
    if (IS_HIDPI) {
      sourceWidth *= 2;
      sourceHeight *= 2;
    }
    this.ctx.drawImage(
      getSpriteImage(),
      this.spritePos.x,
      this.spritePos.y,
      sourceWidth,
      sourceHeight,
      this.xPos,
      this.yPos,
      CONFIG.WIDTH,
      CONFIG.HEIGHT
    );
    this.ctx.restore();
  }

  update(speed: number): void {
    if (this.remove) return;
    this.xPos -= Math.ceil(speed);
    this.draw();
    if (!this.isVisible()) this.remove = true;
  }

  isVisible(): boolean {
    return this.xPos + CONFIG.WIDTH > 0;
  }
}
