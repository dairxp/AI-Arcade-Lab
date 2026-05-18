import type { CollisionBoxLike } from './types';

export class CollisionBox implements CollisionBoxLike {
  constructor(
    public x: number,
    public y: number,
    public width: number,
    public height: number
  ) {}
}
