import { getContext } from './canvas';
import { IS_HIDPI, SPRITE_DEFINITION } from './constants';
import { getSpriteImage } from './sprite';
import type { SpritePos, Star } from './types';
import { getRandomNum } from './utils';

const CONFIG = {
  FADE_SPEED: 0.035,
  HEIGHT: 40,
  MOON_SPEED: 0.25,
  NUM_STARS: 2,
  STAR_SIZE: 9,
  STAR_SPEED: 0.3,
  STAR_MAX_Y: 70,
  WIDTH: 20
};

const PHASES = [140, 120, 100, 60, 40, 20, 0];

export class NightMode {
  private ctx: CanvasRenderingContext2D;
  private xPos: number;
  private yPos = 30;
  private currentPhase = 0;
  private opacity = 0;
  private stars: Star[] = [];
  private drawStars = false;

  constructor(canvas: HTMLCanvasElement, private spritePos: SpritePos, private containerWidth: number) {
    this.ctx = getContext(canvas);
    this.xPos = containerWidth - 50;
    this.placeStars();
  }

  update(activated: boolean): void {
    if (activated && this.opacity === 0) {
      this.currentPhase++;
      if (this.currentPhase >= PHASES.length) this.currentPhase = 0;
    }

    if (activated && (this.opacity < 1 || this.opacity === 0)) {
      this.opacity += CONFIG.FADE_SPEED;
    } else if (this.opacity > 0) {
      this.opacity -= CONFIG.FADE_SPEED;
    }

    if (this.opacity > 0) {
      this.xPos = this.updateXPos(this.xPos, CONFIG.MOON_SPEED);
      if (this.drawStars) {
        for (let i = 0; i < CONFIG.NUM_STARS; i++) {
          this.stars[i]!.x = this.updateXPos(this.stars[i]!.x, CONFIG.STAR_SPEED);
        }
      }
      this.draw();
    } else {
      this.opacity = 0;
      this.placeStars();
    }
    this.drawStars = true;
  }

  private updateXPos(currentPos: number, speed: number): number {
    if (currentPos < -CONFIG.WIDTH) return this.containerWidth;
    return currentPos - speed;
  }

  private draw(): void {
    let moonSourceWidth =
      this.currentPhase === 3 ? CONFIG.WIDTH * 2 : CONFIG.WIDTH;
    let moonSourceHeight = CONFIG.HEIGHT;
    let moonSourceX = this.spritePos.x + PHASES[this.currentPhase]!;
    const moonOutputWidth = moonSourceWidth;
    let starSize = CONFIG.STAR_SIZE;
    let starSourceX = SPRITE_DEFINITION.LDPI.STAR.x;

    if (IS_HIDPI) {
      moonSourceWidth *= 2;
      moonSourceHeight *= 2;
      moonSourceX = this.spritePos.x + PHASES[this.currentPhase]! * 2;
      starSize *= 2;
      starSourceX = SPRITE_DEFINITION.HDPI.STAR.x;
    }

    this.ctx.save();
    this.ctx.globalAlpha = this.opacity;

    const image = getSpriteImage();

    if (this.drawStars) {
      for (let i = 0; i < CONFIG.NUM_STARS; i++) {
        const star = this.stars[i]!;
        this.ctx.drawImage(
          image,
          starSourceX,
          star.sourceY,
          starSize,
          starSize,
          Math.round(star.x),
          star.y,
          CONFIG.STAR_SIZE,
          CONFIG.STAR_SIZE
        );
      }
    }

    this.ctx.drawImage(
      image,
      moonSourceX,
      this.spritePos.y,
      moonSourceWidth,
      moonSourceHeight,
      Math.round(this.xPos),
      this.yPos,
      moonOutputWidth,
      CONFIG.HEIGHT
    );

    this.ctx.globalAlpha = 1;
    this.ctx.restore();
  }

  private placeStars(): void {
    const segmentSize = Math.round(this.containerWidth / CONFIG.NUM_STARS);
    for (let i = 0; i < CONFIG.NUM_STARS; i++) {
      const sourceY = IS_HIDPI
        ? SPRITE_DEFINITION.HDPI.STAR.y + CONFIG.STAR_SIZE * 2 * i
        : SPRITE_DEFINITION.LDPI.STAR.y + CONFIG.STAR_SIZE * i;
      this.stars[i] = {
        x: getRandomNum(segmentSize * i, segmentSize * (i + 1)),
        y: getRandomNum(0, CONFIG.STAR_MAX_Y),
        sourceY
      };
    }
  }

  reset(): void {
    this.currentPhase = 0;
    this.opacity = 0;
    this.update(false);
  }
}
