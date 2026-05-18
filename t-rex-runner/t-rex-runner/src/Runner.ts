import { createCanvas, getContext, updateCanvasScaling } from './canvas';
import {
  CLASSES,
  DEFAULT_DIMENSIONS,
  DEFAULT_WIDTH,
  EVENTS,
  FPS,
  IS_MOBILE,
  KEYCODES,
  RUNNER_CONFIG
} from './constants';
import { DistanceMeter } from './DistanceMeter';
import { GameOverPanel } from './GameOverPanel';
import { Horizon } from './Horizon';
import { Trex } from './Trex';
import { checkForCollision } from './collision';
import { loadSpriteImage, sprite } from './sprite';
import type { Dimensions } from './types';
import { getTimeStamp, vibrate } from './utils';

export class Runner implements EventListenerObject {
  private outerContainerEl: HTMLElement;
  private containerEl!: HTMLElement;
  private touchController?: HTMLElement;

  private canvas!: HTMLCanvasElement;
  private canvasCtx!: CanvasRenderingContext2D;

  private dimensions: Dimensions = { ...DEFAULT_DIMENSIONS };
  private config = RUNNER_CONFIG;
  private msPerFrame = 1000 / FPS;

  private tRex!: Trex;
  private horizon!: Horizon;
  private distanceMeter!: DistanceMeter;
  private gameOverPanel: GameOverPanel | null = null;

  private currentSpeed: number = RUNNER_CONFIG.SPEED;
  private distanceRan = 0;
  private highestScore = 0;
  private runningTime = 0;
  private time = 0;
  private raqId = 0;
  private updatePending = false;

  private activated = false;
  private playing = false;
  private crashed = false;
  private paused = false;
  private playingIntro = false;
  private inverted = false;
  private invertTimer = 0;
  private invertTrigger = false;
  private playCount = 0;

  private resizeTimerId: number | null = null;

  constructor(outerContainerId: string) {
    const el = document.querySelector<HTMLElement>(outerContainerId);
    if (!el) throw new Error(`Container ${outerContainerId} not found`);
    this.outerContainerEl = el;
    void this.loadAndInit();
  }

  private async loadAndInit(): Promise<void> {
    sprite.image = await loadSpriteImage();
    this.init();
  }

  private init(): void {
    this.adjustDimensions();
    this.setSpeed();

    this.containerEl = document.createElement('div');
    this.containerEl.className = CLASSES.CONTAINER;

    this.canvas = createCanvas(this.containerEl, this.dimensions.WIDTH, this.dimensions.HEIGHT);
    this.canvasCtx = getContext(this.canvas);
    this.canvasCtx.fillStyle = '#f7f7f7';
    this.canvasCtx.fill();
    updateCanvasScaling(this.canvas);

    this.horizon = new Horizon(this.canvas, sprite.set, this.dimensions, this.config.GAP_COEFFICIENT);
    this.distanceMeter = new DistanceMeter(
      this.canvas,
      sprite.set.TEXT_SPRITE,
      this.dimensions.WIDTH
    );
    this.tRex = new Trex(this.canvas, sprite.set.TREX);

    this.outerContainerEl.appendChild(this.containerEl);

    if (IS_MOBILE) this.createTouchController();

    this.startListening();
    this.update();

    window.addEventListener(EVENTS.RESIZE, this.debounceResize);
  }

  private createTouchController(): void {
    this.touchController = document.createElement('div');
    this.touchController.className = CLASSES.TOUCH_CONTROLLER;
    this.outerContainerEl.appendChild(this.touchController);
  }

  private debounceResize = (): void => {
    if (!this.resizeTimerId) {
      this.resizeTimerId = window.setInterval(() => this.adjustDimensions(), 250);
    }
  };

  private adjustDimensions(): void {
    if (this.resizeTimerId !== null) {
      window.clearInterval(this.resizeTimerId);
      this.resizeTimerId = null;
    }

    const boxStyles = window.getComputedStyle(this.outerContainerEl);
    const padding = Number.parseFloat(boxStyles.paddingLeft) || 0;

    this.dimensions.WIDTH = Math.min(
      DEFAULT_WIDTH,
      this.outerContainerEl.offsetWidth - padding * 2
    );

    if (this.canvas) {
      this.canvas.width = this.dimensions.WIDTH;
      this.canvas.height = this.dimensions.HEIGHT;
      updateCanvasScaling(this.canvas);

      this.distanceMeter.calcXPos(this.dimensions.WIDTH);
      this.clearCanvas();
      this.horizon.update(0, 0, true);
      this.tRex.update(0);

      if (this.playing || this.crashed || this.paused) {
        this.containerEl.style.width = `${this.dimensions.WIDTH}px`;
        this.containerEl.style.height = `${this.dimensions.HEIGHT}px`;
        this.distanceMeter.update(0, Math.ceil(this.distanceRan));
        this.stop();
      }

      if (this.crashed && this.gameOverPanel) {
        this.gameOverPanel.updateDimensions(this.dimensions.WIDTH);
        this.gameOverPanel.draw();
      }
    }
  }

  private setSpeed(optSpeed?: number): void {
    const speed = optSpeed ?? this.currentSpeed;
    if (this.dimensions.WIDTH < DEFAULT_WIDTH) {
      const mobileSpeed =
        (speed * this.dimensions.WIDTH) / DEFAULT_WIDTH * this.config.MOBILE_SPEED_COEFFICIENT;
      this.currentSpeed = mobileSpeed > speed ? speed : mobileSpeed;
    } else if (optSpeed !== undefined) {
      this.currentSpeed = optSpeed;
    }
  }

  private playIntro(): void {
    if (!this.activated && !this.crashed) {
      this.playingIntro = true;
      this.tRex.playingIntro = true;

      const keyframes =
        '@-webkit-keyframes intro { ' +
        `from { width:${Trex.config.WIDTH}px }` +
        `to { width: ${this.dimensions.WIDTH}px }` +
        '}';

      const sheet = document.createElement('style');
      sheet.textContent = keyframes;
      document.head.appendChild(sheet);

      this.containerEl.addEventListener(EVENTS.ANIM_END, () => this.startGame(), { once: true });
      this.containerEl.style.webkitAnimation = 'intro .4s ease-out 1 both';
      this.containerEl.style.width = `${this.dimensions.WIDTH}px`;

      this.playing = true;
      this.activated = true;
    } else if (this.crashed) {
      this.restart();
    }
  }

  private startGame(): void {
    this.setArcadeMode();
    this.runningTime = 0;
    this.playingIntro = false;
    this.tRex.playingIntro = false;
    this.containerEl.style.webkitAnimation = '';
    this.playCount++;

    document.addEventListener(EVENTS.VISIBILITY, this.onVisibilityChange);
    window.addEventListener(EVENTS.BLUR, this.onVisibilityChange);
    window.addEventListener(EVENTS.FOCUS, this.onVisibilityChange);
  }

  private clearCanvas(): void {
    this.canvasCtx.clearRect(0, 0, this.dimensions.WIDTH, this.dimensions.HEIGHT);
  }

  private update(): void {
    this.updatePending = false;

    const now = getTimeStamp();
    let deltaTime = now - (this.time || now);
    this.time = now;

    if (this.playing) {
      this.clearCanvas();

      if (this.tRex.jumping) this.tRex.updateJump(deltaTime);

      this.runningTime += deltaTime;
      const hasObstacles = this.runningTime > this.config.CLEAR_TIME;

      if (this.tRex.jumpCount === 1 && !this.playingIntro) {
        this.playIntro();
      }

      if (this.playingIntro) {
        this.horizon.update(0, this.currentSpeed, hasObstacles);
      } else {
        deltaTime = !this.activated ? 0 : deltaTime;
        this.horizon.update(deltaTime, this.currentSpeed, hasObstacles, this.inverted);
      }

      const collision =
        hasObstacles &&
        this.horizon.obstacles[0] &&
        checkForCollision(this.horizon.obstacles[0], this.tRex);

      if (!collision) {
        this.distanceRan += (this.currentSpeed * deltaTime) / this.msPerFrame;
        if (this.currentSpeed < this.config.MAX_SPEED) {
          this.currentSpeed += this.config.ACCELERATION;
        }
      } else {
        this.gameOver();
      }

      this.distanceMeter.update(deltaTime, Math.ceil(this.distanceRan));

      if (this.invertTimer > this.config.INVERT_FADE_DURATION) {
        this.invertTimer = 0;
        this.invertTrigger = false;
        this.invert(false);
      } else if (this.invertTimer) {
        this.invertTimer += deltaTime;
      } else {
        const actualDistance = this.distanceMeter.getActualDistance(Math.ceil(this.distanceRan));
        if (actualDistance > 0) {
          this.invertTrigger = !(actualDistance % this.config.INVERT_DISTANCE);
          if (this.invertTrigger && this.invertTimer === 0) {
            this.invertTimer += deltaTime;
            this.invert(false);
          }
        }
      }
    }

    if (
      this.playing ||
      (!this.activated && this.tRex.blinkCount < RUNNER_CONFIG.MAX_BLINK_COUNT)
    ) {
      this.tRex.update(deltaTime);
      this.scheduleNextUpdate();
    }
  }

  handleEvent(e: Event): void {
    switch (e.type) {
      case EVENTS.KEYDOWN:
      case EVENTS.TOUCHSTART:
      case EVENTS.MOUSEDOWN:
        this.onKeyDown(e as KeyboardEvent | TouchEvent | MouseEvent);
        break;
      case EVENTS.KEYUP:
      case EVENTS.TOUCHEND:
      case EVENTS.MOUSEUP:
        this.onKeyUp(e as KeyboardEvent | TouchEvent | MouseEvent);
        break;
    }
  }

  private startListening(): void {
    document.addEventListener(EVENTS.KEYDOWN, this);
    document.addEventListener(EVENTS.KEYUP, this);

    if (IS_MOBILE && this.touchController) {
      this.touchController.addEventListener(EVENTS.TOUCHSTART, this);
      this.touchController.addEventListener(EVENTS.TOUCHEND, this);
      this.containerEl.addEventListener(EVENTS.TOUCHSTART, this);
    } else {
      document.addEventListener(EVENTS.MOUSEDOWN, this);
      document.addEventListener(EVENTS.MOUSEUP, this);
    }
  }

  private onKeyDown(e: KeyboardEvent | TouchEvent | MouseEvent): void {
    if (IS_MOBILE && this.playing) e.preventDefault();

    const isKeyboard = e instanceof KeyboardEvent;
    const isTouch = e.type === EVENTS.TOUCHSTART;
    const code = isKeyboard ? e.code : '';

    const isJumpTrigger = (isKeyboard && KEYCODES.JUMP.has(code)) || isTouch;

    if (!this.crashed && isJumpTrigger) {
      if (!this.playing) {
        this.playing = true;
        this.update();
      }
      if (!this.tRex.jumping && !this.tRex.ducking) {
        this.tRex.startJump(this.currentSpeed);
      }
    }

    if (this.crashed && isTouch && e.currentTarget === this.containerEl) {
      this.restart();
    }

    if (this.playing && !this.crashed && isKeyboard && KEYCODES.DUCK.has(code)) {
      e.preventDefault();
      if (this.tRex.jumping) this.tRex.setSpeedDrop();
      else if (!this.tRex.ducking) this.tRex.setDuck(true);
    }
  }

  private onKeyUp(e: KeyboardEvent | TouchEvent | MouseEvent): void {
    const isKeyboard = e instanceof KeyboardEvent;
    const code = isKeyboard ? e.code : '';
    const isJumpKey =
      (isKeyboard && KEYCODES.JUMP.has(code)) ||
      e.type === EVENTS.TOUCHEND ||
      e.type === EVENTS.MOUSEDOWN;

    if (this.isRunning() && isJumpKey) {
      this.tRex.endJump();
    } else if (isKeyboard && KEYCODES.DUCK.has(code)) {
      this.tRex.speedDrop = false;
      this.tRex.setDuck(false);
    } else if (this.crashed) {
      const deltaTime = getTimeStamp() - this.time;
      if (
        (isKeyboard && KEYCODES.RESTART.has(code)) ||
        this.isLeftClickOnCanvas(e) ||
        (deltaTime >= this.config.GAMEOVER_CLEAR_TIME && isKeyboard && KEYCODES.JUMP.has(code))
      ) {
        this.restart();
      }
    } else if (this.paused && isJumpKey) {
      this.tRex.reset();
      this.play();
    }
  }

  private isLeftClickOnCanvas(e: Event): boolean {
    if (!(e instanceof MouseEvent)) return false;
    return e.button < 2 && e.type === EVENTS.MOUSEUP && e.target === this.canvas;
  }

  private scheduleNextUpdate(): void {
    if (this.updatePending) return;
    this.updatePending = true;
    this.raqId = requestAnimationFrame(() => this.update());
  }

  private isRunning(): boolean {
    return Boolean(this.raqId);
  }

  private gameOver(): void {
    vibrate(200);

    this.stop();
    this.crashed = true;

    this.tRex.update(100, 'CRASHED');

    if (!this.gameOverPanel) {
      this.gameOverPanel = new GameOverPanel(
        this.canvas,
        sprite.set.TEXT_SPRITE,
        sprite.set.RESTART,
        this.dimensions
      );
    } else {
      this.gameOverPanel.draw();
    }

    if (this.distanceRan > this.highestScore) {
      this.highestScore = Math.ceil(this.distanceRan);
      this.distanceMeter.setHighScore(this.highestScore);
    }

    this.time = getTimeStamp();
  }

  private stop(): void {
    this.playing = false;
    this.paused = true;
    cancelAnimationFrame(this.raqId);
    this.raqId = 0;
  }

  private play(): void {
    if (this.crashed) return;
    this.playing = true;
    this.paused = false;
    this.tRex.update(0, 'RUNNING');
    this.time = getTimeStamp();
    this.update();
  }

  restart(): void {
    if (this.raqId) return;
    this.playCount++;
    this.runningTime = 0;
    this.playing = true;
    this.crashed = false;
    this.distanceRan = 0;
    this.setSpeed(this.config.SPEED);
    this.time = getTimeStamp();
    this.containerEl.classList.remove(CLASSES.CRASHED);
    this.clearCanvas();
    this.distanceMeter.reset();
    this.horizon.reset();
    this.tRex.reset();
    this.invert(true);
    this.update();
  }

  private setArcadeMode(): void {
    document.body.classList.add(CLASSES.ARCADE_MODE);
  }

  private onVisibilityChange = (e: Event): void => {
    if (document.hidden || e.type === 'blur' || document.visibilityState !== 'visible') {
      this.stop();
    } else if (!this.crashed) {
      this.tRex.reset();
      this.play();
    }
  };

  private invert(reset: boolean): void {
    if (reset) {
      document.body.classList.toggle(CLASSES.INVERTED, false);
      this.invertTimer = 0;
      this.inverted = false;
    } else {
      this.inverted = document.body.classList.toggle(CLASSES.INVERTED, this.invertTrigger);
    }
  }
}
