import { CLASSES } from './constants';

export function createCanvas(
  container: HTMLElement,
  width: number,
  height: number,
  className?: string
): HTMLCanvasElement {
  const canvas = document.createElement('canvas');
  canvas.className = className ? `${CLASSES.CANVAS} ${className}` : CLASSES.CANVAS;
  canvas.width = width;
  canvas.height = height;
  container.appendChild(canvas);
  return canvas;
}

export function getContext(canvas: HTMLCanvasElement): CanvasRenderingContext2D {
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Could not get 2D rendering context');
  return ctx;
}

export function updateCanvasScaling(
  canvas: HTMLCanvasElement,
  optWidth?: number,
  optHeight?: number
): boolean {
  const context = getContext(canvas);
  const devicePixelRatio = Math.floor(window.devicePixelRatio) || 1;
  const backingStoreRatio =
    Math.floor((context as unknown as { webkitBackingStorePixelRatio?: number }).webkitBackingStorePixelRatio ?? 1) ||
    1;
  const ratio = devicePixelRatio / backingStoreRatio;

  if (devicePixelRatio !== backingStoreRatio) {
    const oldWidth = optWidth ?? canvas.width;
    const oldHeight = optHeight ?? canvas.height;

    canvas.width = oldWidth * ratio;
    canvas.height = oldHeight * ratio;

    canvas.style.width = `${oldWidth}px`;
    canvas.style.height = `${oldHeight}px`;

    context.scale(ratio, ratio);
    return true;
  } else if (devicePixelRatio === 1) {
    canvas.style.width = `${canvas.width}px`;
    canvas.style.height = `${canvas.height}px`;
  }
  return false;
}
