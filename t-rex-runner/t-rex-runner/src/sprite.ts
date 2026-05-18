import sprite1xUrl from './assets/100-offline-sprite.png';
import sprite2xUrl from './assets/200-offline-sprite.png';
import { IS_HIDPI, SPRITE_DEFINITION } from './constants';
import type { SpriteSet } from './types';

export const sprite = {
  image: null as HTMLImageElement | null,
  set: (IS_HIDPI ? SPRITE_DEFINITION.HDPI : SPRITE_DEFINITION.LDPI) as SpriteSet
};

export function loadSpriteImage(): Promise<HTMLImageElement> {
  const img = new Image();
  img.src = IS_HIDPI ? sprite2xUrl : sprite1xUrl;
  return new Promise((resolve, reject) => {
    if (img.complete) {
      resolve(img);
      return;
    }
    img.addEventListener('load', () => resolve(img), { once: true });
    img.addEventListener('error', reject, { once: true });
  });
}

export function getSpriteImage(): HTMLImageElement {
  if (!sprite.image) throw new Error('Sprite image not loaded');
  return sprite.image;
}
