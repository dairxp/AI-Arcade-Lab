import { getContext } from './canvas';
import { CollisionBox } from './CollisionBox';
import { DEFAULT_DIMENSIONS, FPS, IS_HIDPI, RUNNER_CONFIG } from './constants';
import { getSpriteImage } from './sprite';
import type { SpritePos } from './types';
import { getTimeStamp } from './utils';

export type TrexStatus = 'CRASHED' | 'DUCKING' | 'JUMPING' | 'RUNNING' | 'WAITING';

const TREX_CONFIG = {
  DROP_VELOCITY: -5,
  GRAVITY: 0.6,
  HEIGHT: 47,
  HEIGHT_DUCK: 25,
  INITIAL_JUMP_VELOCITY: -10,
  INTRO_DURATION: 1500,
  MAX_JUMP_HEIGHT: 30,
  MIN_JUMP_HEIGHT: 30,
  SPEED_DROP_COEFFICIENT: 3,
  START_X_POS: 50,
  WIDTH: 44,
  WIDTH_DUCK: 59
};

export const TREX_COLLISION_BOXES = {
  DUCKING: [new CollisionBox(1, 18, 55, 25)],
  RUNNING: [
    new CollisionBox(22, 0, 17, 16),
    new CollisionBox(1, 18, 30, 9),
    new CollisionBox(10, 35, 14, 8),
    new CollisionBox(1, 24, 29, 5),
    new CollisionBox(5, 30, 21, 4),
    new CollisionBox(9, 34, 15, 4)
  ]
};

const BLINK_TIMING = 7000;

const ANIM_FRAMES: Record<TrexStatus, { frames: number[]; msPerFrame: number }> = {
  WAITING: { frames: [44, 0], msPerFrame: 1000 / 3 },
  RUNNING: { frames: [88, 132], msPerFrame: 1000 / 12 },
  CRASHED: { frames: [220], msPerFrame: 1000 / 60 },
  JUMPING: { frames: [0], msPerFrame: 1000 / 60 },
  DUCKING: { frames: [264, 323], msPerFrame: 1000 / 8 }
};

export class Trex {
  static readonly config = TREX_CONFIG;

  private ctx: CanvasRenderingContext2D;
  xPos = 0;
  yPos = 0;
  private groundYPos = 0;
  private minJumpHeight = 0;

  private currentFrame = 0;
  private currentAnimFrames: number[] = [];
  private msPerFrame = 1000 / FPS;
  private timer = 0;
  private animStartTime = 0;

  private blinkDelay = 0;
  blinkCount = 0;

  status: TrexStatus = 'WAITING';
  jumping = false;
  ducking = false;
  speedDrop = false;
  jumpCount = 0;
  jumpVelocity = 0;
  reachedMinHeight = false;
  playingIntro = false;

  constructor(canvas: HTMLCanvasElement, private spritePos: SpritePos) {
    this.ctx = getContext(canvas);
    this.init();
  }

  private init(): void {
    this.groundYPos =
      DEFAULT_DIMENSIONS.HEIGHT - TREX_CONFIG.HEIGHT - RUNNER_CONFIG.BOTTOM_PAD;
    this.yPos = this.groundYPos;
    this.minJumpHeight = this.groundYPos - TREX_CONFIG.MIN_JUMP_HEIGHT;

    this.draw(0, 0);
    this.update(0, 'WAITING');
  }

  setJumpVelocity(setting: number): void {
    TREX_CONFIG.INITIAL_JUMP_VELOCITY = -setting;
    TREX_CONFIG.DROP_VELOCITY = -setting / 2;
  }

  update(deltaTime: number, optStatus?: TrexStatus): void {
    this.timer += deltaTime;

    if (optStatus) {
      this.status = optStatus;
      this.currentFrame = 0;
      this.msPerFrame = ANIM_FRAMES[optStatus].msPerFrame;
      this.currentAnimFrames = ANIM_FRAMES[optStatus].frames;

      if (optStatus === 'WAITING') {
        this.animStartTime = getTimeStamp();
        this.setBlinkDelay();
      }
    }

    if (this.playingIntro && this.xPos < TREX_CONFIG.START_X_POS) {
      this.xPos += Math.round(
        (TREX_CONFIG.START_X_POS / TREX_CONFIG.INTRO_DURATION) * deltaTime
      );
    }

    if (this.status === 'WAITING') {
      this.blink(getTimeStamp());
    } else {
      this.draw(this.currentAnimFrames[this.currentFrame] ?? 0, 0);
    }

    if (this.timer >= this.msPerFrame) {
      this.currentFrame =
        this.currentFrame === this.currentAnimFrames.length - 1
          ? 0
          : this.currentFrame + 1;
      this.timer = 0;
    }

    if (this.speedDrop && this.yPos === this.groundYPos) {
      this.speedDrop = false;
      this.setDuck(true);
    }
  }

  private draw(x: number, y: number): void {
    let sourceX = x;
    let sourceY = y;
    let sourceWidth =
      this.ducking && this.status !== 'CRASHED'
        ? TREX_CONFIG.WIDTH_DUCK
        : TREX_CONFIG.WIDTH;
    let sourceHeight = TREX_CONFIG.HEIGHT;

    if (IS_HIDPI) {
      sourceX *= 2;
      sourceY *= 2;
      sourceWidth *= 2;
      sourceHeight *= 2;
    }

    sourceX += this.spritePos.x;
    sourceY += this.spritePos.y;

    const image = getSpriteImage();

    if (this.ducking && this.status !== 'CRASHED') {
      this.ctx.drawImage(
        image,
        sourceX,
        sourceY,
        sourceWidth,
        sourceHeight,
        this.xPos,
        this.yPos,
        TREX_CONFIG.WIDTH_DUCK,
        TREX_CONFIG.HEIGHT
      );
    } else {
      if (this.ducking && this.status === 'CRASHED') {
        this.xPos++;
      }
      this.ctx.drawImage(
        image,
        sourceX,
        sourceY,
        sourceWidth,
        sourceHeight,
        this.xPos,
        this.yPos,
        TREX_CONFIG.WIDTH,
        TREX_CONFIG.HEIGHT
      );
    }
  }

  private setBlinkDelay(): void {
    this.blinkDelay = Math.ceil(Math.random() * BLINK_TIMING);
  }

  private blink(time: number): void {
    const deltaTime = time - this.animStartTime;
    if (deltaTime >= this.blinkDelay) {
      this.draw(this.currentAnimFrames[this.currentFrame] ?? 0, 0);
      if (this.currentFrame === 1) {
        this.setBlinkDelay();
        this.animStartTime = time;
        this.blinkCount++;
      }
    }
  }

  startJump(speed: number): void {
    if (this.jumping) return;
    this.update(0, 'JUMPING');
    this.jumpVelocity = TREX_CONFIG.INITIAL_JUMP_VELOCITY - speed / 10;
    this.jumping = true;
    this.reachedMinHeight = false;
    this.speedDrop = false;
  }

  endJump(): void {
    if (this.reachedMinHeight && this.jumpVelocity < TREX_CONFIG.DROP_VELOCITY) {
      this.jumpVelocity = TREX_CONFIG.DROP_VELOCITY;
    }
  }

  updateJump(deltaTime: number): void {
    const msPerFrame = ANIM_FRAMES[this.status].msPerFrame;
    const framesElapsed = deltaTime / msPerFrame;

    if (this.speedDrop) {
      this.yPos += Math.round(
        this.jumpVelocity * TREX_CONFIG.SPEED_DROP_COEFFICIENT * framesElapsed
      );
    } else {
      this.yPos += Math.round(this.jumpVelocity * framesElapsed);
    }

    this.jumpVelocity += TREX_CONFIG.GRAVITY * framesElapsed;

    if (this.yPos < this.minJumpHeight || this.speedDrop) {
      this.reachedMinHeight = true;
    }

    if (this.yPos < TREX_CONFIG.MAX_JUMP_HEIGHT || this.speedDrop) {
      this.endJump();
    }

    if (this.yPos > this.groundYPos) {
      this.reset();
      this.jumpCount++;
    }

    this.update(deltaTime);
  }

  setSpeedDrop(): void {
    this.speedDrop = true;
    this.jumpVelocity = 1;
  }

  setDuck(isDucking: boolean): void {
    if (isDucking && this.status !== 'DUCKING') {
      this.update(0, 'DUCKING');
      this.ducking = true;
    } else if (this.status === 'DUCKING') {
      this.update(0, 'RUNNING');
      this.ducking = false;
    }
  }

  reset(): void {
    this.yPos = this.groundYPos;
    this.jumpVelocity = 0;
    this.jumping = false;
    this.ducking = false;
    this.update(0, 'RUNNING');
    this.speedDrop = false;
    this.jumpCount = 0;
  }
}
