import { getContext } from './canvas';
import { IS_HIDPI } from './constants';
import { getSpriteImage } from './sprite';
import type { SpritePos } from './types';

const DIMENSIONS = {
  WIDTH: 10,
  HEIGHT: 13,
  DEST_WIDTH: 11
};

const CONFIG = {
  MAX_DISTANCE_UNITS: 5,
  ACHIEVEMENT_DISTANCE: 100,
  COEFFICIENT: 0.025,
  FLASH_DURATION: 1000 / 4,
  FLASH_ITERATIONS: 3
};

export class DistanceMeter {
  private ctx: CanvasRenderingContext2D;
  private x = 0;
  private y = 5;

  private maxScore = 0;
  private highScore: string[] = [];
  private digits: string[] = [];
  private defaultString = '';
  private maxScoreUnits = CONFIG.MAX_DISTANCE_UNITS;

  private achievement = false;
  private flashTimer = 0;
  private flashIterations = 0;

  constructor(canvas: HTMLCanvasElement, private spritePos: SpritePos, canvasWidth: number) {
    this.ctx = getContext(canvas);
    this.init(canvasWidth);
  }

  private init(width: number): void {
    let maxDistanceStr = '';
    this.calcXPos(width);
    this.maxScore = this.maxScoreUnits;
    for (let i = 0; i < this.maxScoreUnits; i++) {
      this.draw(i, 0);
      this.defaultString += '0';
      maxDistanceStr += '9';
    }
    this.maxScore = parseInt(maxDistanceStr, 10);
  }

  calcXPos(canvasWidth: number): void {
    this.x = canvasWidth - DIMENSIONS.DEST_WIDTH * (this.maxScoreUnits + 1);
  }

  private draw(digitPos: number, value: number, optHighScore = false): void {
    let sourceWidth = DIMENSIONS.WIDTH;
    let sourceHeight = DIMENSIONS.HEIGHT;
    let sourceX = DIMENSIONS.WIDTH * value;
    let sourceY = 0;

    const targetX = digitPos * DIMENSIONS.DEST_WIDTH;
    const targetY = this.y;

    if (IS_HIDPI) {
      sourceWidth *= 2;
      sourceHeight *= 2;
      sourceX *= 2;
    }

    sourceX += this.spritePos.x;
    sourceY += this.spritePos.y;

    this.ctx.save();
    if (optHighScore) {
      const highScoreX = this.x - this.maxScoreUnits * 2 * DIMENSIONS.WIDTH;
      this.ctx.translate(highScoreX, this.y);
    } else {
      this.ctx.translate(this.x, this.y);
    }

    this.ctx.drawImage(
      getSpriteImage(),
      sourceX,
      sourceY,
      sourceWidth,
      sourceHeight,
      targetX,
      targetY,
      DIMENSIONS.WIDTH,
      DIMENSIONS.HEIGHT
    );

    this.ctx.restore();
  }

  getActualDistance(distance: number): number {
    return distance ? Math.round(distance * CONFIG.COEFFICIENT) : 0;
  }

  update(deltaTime: number, distance: number): boolean {
    let paint = true;
    let playSound = false;

    if (!this.achievement) {
      distance = this.getActualDistance(distance);

      if (distance > this.maxScore && this.maxScoreUnits === CONFIG.MAX_DISTANCE_UNITS) {
        this.maxScoreUnits++;
        this.maxScore = parseInt(this.maxScore + '9', 10);
      }

      if (distance > 0) {
        if (distance % CONFIG.ACHIEVEMENT_DISTANCE === 0) {
          this.achievement = true;
          this.flashTimer = 0;
          playSound = true;
        }
        const distanceStr = (this.defaultString + distance).slice(-this.maxScoreUnits);
        this.digits = distanceStr.split('');
      } else {
        this.digits = this.defaultString.split('');
      }
    } else {
      if (this.flashIterations <= CONFIG.FLASH_ITERATIONS) {
        this.flashTimer += deltaTime;
        if (this.flashTimer < CONFIG.FLASH_DURATION) {
          paint = false;
        } else if (this.flashTimer > CONFIG.FLASH_DURATION * 2) {
          this.flashTimer = 0;
          this.flashIterations++;
        }
      } else {
        this.achievement = false;
        this.flashIterations = 0;
        this.flashTimer = 0;
      }
    }

    if (paint) {
      for (let i = this.digits.length - 1; i >= 0; i--) {
        this.draw(i, parseInt(this.digits[i]!, 10));
      }
    }

    this.drawHighScore();
    return playSound;
  }

  private drawHighScore(): void {
    this.ctx.save();
    this.ctx.globalAlpha = 0.8;
    for (let i = this.highScore.length - 1; i >= 0; i--) {
      this.draw(i, parseInt(this.highScore[i]!, 10), true);
    }
    this.ctx.restore();
  }

  setHighScore(distance: number): void {
    distance = this.getActualDistance(distance);
    const highScoreStr = (this.defaultString + distance).slice(-this.maxScoreUnits);
    this.highScore = ['10', '11', ''].concat(highScoreStr.split(''));
  }

  reset(): void {
    this.update(0, 0);
    this.achievement = false;
  }
}
