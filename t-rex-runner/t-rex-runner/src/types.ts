export interface Dimensions {
  WIDTH: number;
  HEIGHT: number;
}

export interface SpritePos {
  x: number;
  y: number;
}

export interface SpriteSet {
  CACTUS_LARGE: SpritePos;
  CACTUS_SMALL: SpritePos;
  CLOUD: SpritePos;
  HORIZON: SpritePos;
  MOON: SpritePos;
  PTERODACTYL: SpritePos;
  RESTART: SpritePos;
  TEXT_SPRITE: SpritePos;
  TREX: SpritePos;
  STAR: SpritePos;
}

export interface SpriteDefinition {
  LDPI: SpriteSet;
  HDPI: SpriteSet;
}

export type ObstacleTypeName = 'CACTUS_SMALL' | 'CACTUS_LARGE' | 'PTERODACTYL';

export interface ObstacleType {
  type: ObstacleTypeName;
  width: number;
  height: number;
  yPos: number | number[];
  yPosMobile?: number[];
  multipleSpeed: number;
  minGap: number;
  minSpeed: number;
  collisionBoxes: CollisionBoxLike[];
  numFrames?: number;
  frameRate?: number;
  speedOffset?: number;
}

export interface CollisionBoxLike {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Star {
  x: number;
  y: number;
  sourceY: number;
}
