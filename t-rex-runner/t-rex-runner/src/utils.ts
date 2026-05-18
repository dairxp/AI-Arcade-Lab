import { IS_IOS, IS_MOBILE } from './constants';

export function getRandomNum(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function vibrate(duration: number): void {
  if (IS_MOBILE && window.navigator.vibrate) {
    window.navigator.vibrate(duration);
  }
}

export function getTimeStamp(): number {
  return IS_IOS ? Date.now() : performance.now();
}
