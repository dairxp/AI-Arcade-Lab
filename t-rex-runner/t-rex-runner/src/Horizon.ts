import { Cloud } from './Cloud';
import { HorizonLine } from './HorizonLine';
import { NightMode } from './NightMode';
import { Obstacle, OBSTACLE_TYPES } from './Obstacle';
import { RUNNER_CONFIG } from './constants';
import { getContext } from './canvas';
import type { Dimensions, ObstacleTypeName, SpriteSet } from './types';
import { getRandomNum } from './utils';

const CONFIG = {
  BG_CLOUD_SPEED: 0.2,
  CLOUD_FREQUENCY: 0.5,
  MAX_CLOUDS: 6
};

export class Horizon {
  private ctx: CanvasRenderingContext2D;
  obstacles: Obstacle[] = [];
  private obstacleHistory: ObstacleTypeName[] = [];
  private clouds: Cloud[] = [];
  private cloudSpeed = CONFIG.BG_CLOUD_SPEED;
  private cloudFrequency = CONFIG.CLOUD_FREQUENCY;
  private horizonLine: HorizonLine;
  private nightMode: NightMode;

  constructor(
    private canvas: HTMLCanvasElement,
    private spritePos: SpriteSet,
    private dimensions: Dimensions,
    private gapCoefficient: number
  ) {
    this.ctx = getContext(canvas);
    this.addCloud();
    this.horizonLine = new HorizonLine(this.canvas, this.spritePos.HORIZON);
    this.nightMode = new NightMode(this.canvas, this.spritePos.MOON, this.dimensions.WIDTH);
  }

  update(deltaTime: number, currentSpeed: number, updateObstacles: boolean, showNightMode = false): void {
    this.horizonLine.update(deltaTime, currentSpeed);
    this.nightMode.update(showNightMode);
    this.updateClouds(deltaTime, currentSpeed);
    if (updateObstacles) this.updateObstacles(deltaTime, currentSpeed);
  }

  private updateClouds(deltaTime: number, speed: number): void {
    const cloudSpeed = (this.cloudSpeed / 1000) * deltaTime * speed;
    const numClouds = this.clouds.length;

    if (numClouds) {
      for (let i = numClouds - 1; i >= 0; i--) {
        this.clouds[i]!.update(cloudSpeed);
      }

      const lastCloud = this.clouds[numClouds - 1]!;

      if (
        numClouds < CONFIG.MAX_CLOUDS &&
        this.dimensions.WIDTH - lastCloud.xPos > lastCloud.cloudGap &&
        this.cloudFrequency > Math.random()
      ) {
        this.addCloud();
      }

      this.clouds = this.clouds.filter((c) => !c.remove);
    } else {
      this.addCloud();
    }
  }

  private updateObstacles(deltaTime: number, currentSpeed: number): void {
    const updatedObstacles = this.obstacles.slice(0);

    for (const obstacle of this.obstacles) {
      obstacle.update(deltaTime, currentSpeed);
      if (obstacle.remove) updatedObstacles.shift();
    }
    this.obstacles = updatedObstacles;

    if (this.obstacles.length > 0) {
      const lastObstacle = this.obstacles[this.obstacles.length - 1]!;
      if (
        !lastObstacle.followingObstacleCreated &&
        lastObstacle.isVisible() &&
        lastObstacle.xPos + lastObstacle.width + lastObstacle.gap < this.dimensions.WIDTH
      ) {
        this.addNewObstacle(currentSpeed);
        lastObstacle.followingObstacleCreated = true;
      }
    } else {
      this.addNewObstacle(currentSpeed);
    }
  }

  private addNewObstacle(currentSpeed: number): void {
    const obstacleTypeIndex = getRandomNum(0, OBSTACLE_TYPES.length - 1);
    const obstacleType = OBSTACLE_TYPES[obstacleTypeIndex]!;

    if (this.duplicateObstacleCheck(obstacleType.type) || currentSpeed < obstacleType.minSpeed) {
      this.addNewObstacle(currentSpeed);
      return;
    }

    const obstacleSpritePos = this.spritePos[obstacleType.type];

    this.obstacles.push(
      new Obstacle(
        this.ctx,
        obstacleType,
        obstacleSpritePos,
        this.dimensions,
        this.gapCoefficient,
        currentSpeed,
        obstacleType.width
      )
    );

    this.obstacleHistory.unshift(obstacleType.type);
    if (this.obstacleHistory.length > 1) {
      this.obstacleHistory.splice(RUNNER_CONFIG.MAX_OBSTACLE_DUPLICATION);
    }
  }

  private duplicateObstacleCheck(nextObstacleType: ObstacleTypeName): boolean {
    let duplicateCount = 0;
    for (const type of this.obstacleHistory) {
      duplicateCount = type === nextObstacleType ? duplicateCount + 1 : 0;
    }
    return duplicateCount >= RUNNER_CONFIG.MAX_OBSTACLE_DUPLICATION;
  }

  reset(): void {
    this.obstacles = [];
    this.horizonLine.reset();
    this.nightMode.reset();
  }

  resize(width: number, height: number): void {
    this.canvas.width = width;
    this.canvas.height = height;
  }

  private addCloud(): void {
    this.clouds.push(new Cloud(this.canvas, this.spritePos.CLOUD, this.dimensions.WIDTH));
  }
}
