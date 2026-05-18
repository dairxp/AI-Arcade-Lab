import { CollisionBox } from './CollisionBox';
import { FPS, IS_HIDPI, IS_MOBILE } from './constants';
import { getSpriteImage } from './sprite';
import type { Dimensions, ObstacleType, SpritePos } from './types';
import { getRandomNum } from './utils';

const MAX_GAP_COEFFICIENT = 1.5;
const MAX_OBSTACLE_LENGTH = 3;

export const OBSTACLE_TYPES: ObstacleType[] = [
  {
    type: 'CACTUS_SMALL',
    width: 17,
    height: 35,
    yPos: 105,
    multipleSpeed: 4,
    minGap: 120,
    minSpeed: 0,
    collisionBoxes: [
      new CollisionBox(0, 7, 5, 27),
      new CollisionBox(4, 0, 6, 34),
      new CollisionBox(10, 4, 7, 14)
    ]
  },
  {
    type: 'CACTUS_LARGE',
    width: 25,
    height: 50,
    yPos: 90,
    multipleSpeed: 7,
    minGap: 120,
    minSpeed: 0,
    collisionBoxes: [
      new CollisionBox(0, 12, 7, 38),
      new CollisionBox(8, 0, 7, 49),
      new CollisionBox(13, 10, 10, 38)
    ]
  },
  {
    type: 'PTERODACTYL',
    width: 46,
    height: 40,
    yPos: [100, 75, 50],
    yPosMobile: [100, 50],
    multipleSpeed: 999,
    minSpeed: 8.5,
    minGap: 150,
    collisionBoxes: [
      new CollisionBox(15, 15, 16, 5),
      new CollisionBox(18, 21, 24, 6),
      new CollisionBox(2, 14, 4, 3),
      new CollisionBox(6, 10, 4, 7),
      new CollisionBox(10, 8, 6, 9)
    ],
    numFrames: 2,
    frameRate: 1000 / 6,
    speedOffset: 0.8
  }
];

export class Obstacle {
  size: number;
  xPos: number;
  yPos = 0;
  width = 0;
  collisionBoxes: CollisionBox[] = [];
  remove = false;
  followingObstacleCreated = false;
  gap = 0;

  private speedOffset = 0;
  private currentFrame = 0;
  private timer = 0;

  constructor(
    private ctx: CanvasRenderingContext2D,
    public readonly typeConfig: ObstacleType,
    private spritePos: SpritePos,
    dimensions: Dimensions,
    private gapCoefficient: number,
    speed: number,
    xOffset = 0
  ) {
    this.size = getRandomNum(1, MAX_OBSTACLE_LENGTH);
    this.xPos = dimensions.WIDTH + xOffset;
    this.init(speed);
  }

  private init(speed: number): void {
    this.cloneCollisionBoxes();

    if (this.size > 1 && this.typeConfig.multipleSpeed > speed) {
      this.size = 1;
    }

    this.width = this.typeConfig.width * this.size;

    if (Array.isArray(this.typeConfig.yPos)) {
      const yPosConfig =
        IS_MOBILE && this.typeConfig.yPosMobile
          ? this.typeConfig.yPosMobile
          : this.typeConfig.yPos;
      this.yPos = yPosConfig[getRandomNum(0, yPosConfig.length - 1)]!;
    } else {
      this.yPos = this.typeConfig.yPos;
    }

    this.draw();

    if (this.size > 1) {
      const boxes = this.collisionBoxes;
      boxes[1]!.width = this.width - boxes[0]!.width - boxes[2]!.width;
      boxes[2]!.x = this.width - boxes[2]!.width;
    }

    if (this.typeConfig.speedOffset) {
      this.speedOffset =
        Math.random() > 0.5
          ? this.typeConfig.speedOffset
          : -this.typeConfig.speedOffset;
    }

    this.gap = this.getGap(this.gapCoefficient, speed);
  }

  draw(): void {
    let sourceWidth = this.typeConfig.width;
    let sourceHeight = this.typeConfig.height;

    if (IS_HIDPI) {
      sourceWidth *= 2;
      sourceHeight *= 2;
    }

    let sourceX = sourceWidth * this.size * (0.5 * (this.size - 1)) + this.spritePos.x;
    if (this.currentFrame > 0) sourceX += sourceWidth * this.currentFrame;

    this.ctx.drawImage(
      getSpriteImage(),
      sourceX,
      this.spritePos.y,
      sourceWidth * this.size,
      sourceHeight,
      this.xPos,
      this.yPos,
      this.typeConfig.width * this.size,
      this.typeConfig.height
    );
  }

  update(deltaTime: number, speed: number): void {
    if (this.remove) return;

    if (this.typeConfig.speedOffset) speed += this.speedOffset;
    this.xPos -= Math.floor((speed * FPS) / 1000 * deltaTime);

    if (this.typeConfig.numFrames && this.typeConfig.frameRate) {
      this.timer += deltaTime;
      if (this.timer >= this.typeConfig.frameRate) {
        this.currentFrame =
          this.currentFrame === this.typeConfig.numFrames - 1
            ? 0
            : this.currentFrame + 1;
        this.timer = 0;
      }
    }

    this.draw();

    if (!this.isVisible()) this.remove = true;
  }

  private getGap(gapCoefficient: number, speed: number): number {
    const minGap = Math.round(this.width * speed + this.typeConfig.minGap * gapCoefficient);
    const maxGap = Math.round(minGap * MAX_GAP_COEFFICIENT);
    return getRandomNum(minGap, maxGap);
  }

  isVisible(): boolean {
    return this.xPos + this.width > 0;
  }

  private cloneCollisionBoxes(): void {
    const source = this.typeConfig.collisionBoxes;
    for (let i = source.length - 1; i >= 0; i--) {
      const box = source[i]!;
      this.collisionBoxes[i] = new CollisionBox(box.x, box.y, box.width, box.height);
    }
  }
}
