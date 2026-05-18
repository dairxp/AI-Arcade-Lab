import { getContext } from './canvas';
import { IS_HIDPI } from './constants';
import { getSpriteImage } from './sprite';
import type { Dimensions, SpritePos } from './types';

const DIMENSIONS = {
  TEXT_X: 0,
  TEXT_Y: 13,
  TEXT_WIDTH: 191,
  TEXT_HEIGHT: 11,
  RESTART_WIDTH: 36,
  RESTART_HEIGHT: 32
};

export class GameOverPanel {
  private ctx: CanvasRenderingContext2D;

  constructor(
    canvas: HTMLCanvasElement,
    private textImgPos: SpritePos,
    private restartImgPos: SpritePos,
    private canvasDimensions: Dimensions
  ) {
    this.ctx = getContext(canvas);
    this.draw();
  }

  updateDimensions(width: number, height?: number): void {
    this.canvasDimensions.WIDTH = width;
    if (height !== undefined) this.canvasDimensions.HEIGHT = height;
  }

  draw(): void {
    const centerX = this.canvasDimensions.WIDTH / 2;

    let textSourceX = DIMENSIONS.TEXT_X;
    let textSourceY = DIMENSIONS.TEXT_Y;
    let textSourceWidth = DIMENSIONS.TEXT_WIDTH;
    let textSourceHeight = DIMENSIONS.TEXT_HEIGHT;

    const textTargetX = Math.round(centerX - DIMENSIONS.TEXT_WIDTH / 2);
    const textTargetY = Math.round((this.canvasDimensions.HEIGHT - 25) / 3);

    let restartSourceWidth = DIMENSIONS.RESTART_WIDTH;
    let restartSourceHeight = DIMENSIONS.RESTART_HEIGHT;
    const restartTargetX = centerX - DIMENSIONS.RESTART_WIDTH / 2;
    const restartTargetY = this.canvasDimensions.HEIGHT / 2;

    if (IS_HIDPI) {
      textSourceX *= 2;
      textSourceY *= 2;
      textSourceWidth *= 2;
      textSourceHeight *= 2;
      restartSourceWidth *= 2;
      restartSourceHeight *= 2;
    }

    textSourceX += this.textImgPos.x;
    textSourceY += this.textImgPos.y;

    const image = getSpriteImage();

    this.ctx.drawImage(
      image,
      textSourceX,
      textSourceY,
      textSourceWidth,
      textSourceHeight,
      textTargetX,
      textTargetY,
      DIMENSIONS.TEXT_WIDTH,
      DIMENSIONS.TEXT_HEIGHT
    );

    this.ctx.drawImage(
      image,
      this.restartImgPos.x,
      this.restartImgPos.y,
      restartSourceWidth,
      restartSourceHeight,
      restartTargetX,
      restartTargetY,
      DIMENSIONS.RESTART_WIDTH,
      DIMENSIONS.RESTART_HEIGHT
    );
  }
}
