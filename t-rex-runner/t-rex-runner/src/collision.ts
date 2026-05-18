import { CollisionBox } from './CollisionBox';
import type { Obstacle } from './Obstacle';
import { Trex, TREX_COLLISION_BOXES } from './Trex';

function boxCompare(tRexBox: CollisionBox, obstacleBox: CollisionBox): boolean {
  return (
    tRexBox.x < obstacleBox.x + obstacleBox.width &&
    tRexBox.x + tRexBox.width > obstacleBox.x &&
    tRexBox.y < obstacleBox.y + obstacleBox.height &&
    tRexBox.height + tRexBox.y > obstacleBox.y
  );
}

function createAdjustedCollisionBox(box: CollisionBox, adjustment: CollisionBox): CollisionBox {
  return new CollisionBox(
    box.x + adjustment.x,
    box.y + adjustment.y,
    box.width,
    box.height
  );
}

function drawCollisionBoxes(
  ctx: CanvasRenderingContext2D,
  tRexBox: CollisionBox,
  obstacleBox: CollisionBox
): void {
  ctx.save();
  ctx.strokeStyle = '#f00';
  ctx.strokeRect(tRexBox.x, tRexBox.y, tRexBox.width, tRexBox.height);
  ctx.strokeStyle = '#0f0';
  ctx.strokeRect(obstacleBox.x, obstacleBox.y, obstacleBox.width, obstacleBox.height);
  ctx.restore();
}

export function checkForCollision(
  obstacle: Obstacle,
  tRex: Trex,
  debugCtx?: CanvasRenderingContext2D
): CollisionBox[] | null {
  const tRexBox = new CollisionBox(
    tRex.xPos + 1,
    tRex.yPos + 1,
    Trex.config.WIDTH - 2,
    Trex.config.HEIGHT - 2
  );

  const obstacleBox = new CollisionBox(
    obstacle.xPos + 1,
    obstacle.yPos + 1,
    obstacle.typeConfig.width * obstacle.size - 2,
    obstacle.typeConfig.height - 2
  );

  if (debugCtx) drawCollisionBoxes(debugCtx, tRexBox, obstacleBox);

  if (!boxCompare(tRexBox, obstacleBox)) return null;

  const collisionBoxes = obstacle.collisionBoxes;
  const tRexCollisionBoxes = tRex.ducking
    ? TREX_COLLISION_BOXES.DUCKING
    : TREX_COLLISION_BOXES.RUNNING;

  for (const tRexFrameBox of tRexCollisionBoxes) {
    for (const obstacleFrameBox of collisionBoxes) {
      const adjTrexBox = createAdjustedCollisionBox(tRexFrameBox, tRexBox);
      const adjObstacleBox = createAdjustedCollisionBox(obstacleFrameBox, obstacleBox);

      if (debugCtx) drawCollisionBoxes(debugCtx, adjTrexBox, adjObstacleBox);

      if (boxCompare(adjTrexBox, adjObstacleBox)) {
        return [adjTrexBox, adjObstacleBox];
      }
    }
  }

  return null;
}
