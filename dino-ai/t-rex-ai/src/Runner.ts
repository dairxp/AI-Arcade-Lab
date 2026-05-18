import { createCanvas, getContext, updateCanvasScaling } from './canvas';
import {
  CLASSES,
  DEFAULT_DIMENSIONS,
  DEFAULT_WIDTH,
  EVENTS,
  FPS,
  RUNNER_CONFIG
} from './constants';
import { DistanceMeter } from './DistanceMeter';
import { Horizon } from './Horizon';
import { Trex } from './Trex';
import { checkForCollision } from './collision';
import { loadSpriteImage, sprite } from './sprite';
import type { Dimensions } from './types';
import { getTimeStamp } from './utils';
import { GeneticAlgorithm, DinoBrain } from './ai/GeneticAlgorithm';
import { NeuralNetworkVisualizer } from './ai/NeuralNetworkVisualizer';

const POPULATION = 200;

export class Runner implements EventListenerObject {
  private outerContainerEl: HTMLElement;
  private containerEl!: HTMLElement;

  private canvas!: HTMLCanvasElement;
  private canvasCtx!: CanvasRenderingContext2D;

  private dimensions: Dimensions = { ...DEFAULT_DIMENSIONS };
  private config = RUNNER_CONFIG;
  private msPerFrame = 1000 / FPS;

  // ── IA ───────────────────────────────────────────────────────────────────
  private ga: GeneticAlgorithm = new GeneticAlgorithm(POPULATION);
  private activeBrains: DinoBrain[] = [];
  private tRexes: Trex[] = [];
  private alive: boolean[] = [];
  private survivalTime: number[] = [];
  private obstaclesPassed: number[] = [];
  private lastObstacleRight: number = 9999;

  /** Visualizador de la red neuronal */
  private visualizer!: NeuralNetworkVisualizer;
  /** Último conjunto de inputs/outputs del mejor dino vivo (para visualizar) */
  private lastInputs: number[] = [0, 0, 0, 0, 0];
  private lastOutputs: number[] = [0, 0];

  // ── Estado del juego ─────────────────────────────────────────────────────
  private horizon!: Horizon;
  private distanceMeter!: DistanceMeter;

  private currentSpeed: number = RUNNER_CONFIG.SPEED;
  private distanceRan = 0;
  private highestScore = 0;
  private runningTime = 0;
  private time = 0;
  private raqId = 0;
  private updatePending = false;

  private inverted = false;
  private invertTimer = 0;
  private invertTrigger = false;
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

    this.containerEl = document.createElement('div');
    this.containerEl.className = CLASSES.CONTAINER;
    this.containerEl.style.width = `${this.dimensions.WIDTH}px`;
    this.containerEl.style.height = `${this.dimensions.HEIGHT}px`;

    this.canvas = createCanvas(this.containerEl, this.dimensions.WIDTH, this.dimensions.HEIGHT);
    this.canvasCtx = getContext(this.canvas);
    updateCanvasScaling(this.canvas);

    this.horizon = new Horizon(
      this.canvas,
      sprite.set,
      this.dimensions,
      this.config.GAP_COEFFICIENT
    );
    this.distanceMeter = new DistanceMeter(
      this.canvas,
      sprite.set.TEXT_SPRITE,
      this.dimensions.WIDTH
    );

    this.outerContainerEl.appendChild(this.containerEl);
    document.body.classList.add(CLASSES.ARCADE_MODE);

    // Conectar visualizador de la red neuronal
    // Ajusta la resolución interna del canvas a su tamaño real en pantalla
    const nnCanvas = document.getElementById('nn-canvas') as HTMLCanvasElement | null;
    if (nnCanvas) {
      const rect = nnCanvas.getBoundingClientRect();
      if (rect.width > 0) {
        nnCanvas.width  = Math.floor(rect.width);
        nnCanvas.height = Math.floor(rect.height);
      }
      this.visualizer = new NeuralNetworkVisualizer(nnCanvas);
    }

    window.addEventListener(EVENTS.RESIZE, this.debounceResize);
    document.addEventListener(EVENTS.KEYDOWN, this);

    this.startNewGeneration();
  }

  private stopLoop(): void {
    if (this.raqId) {
      cancelAnimationFrame(this.raqId);
      this.raqId = 0;
    }
    this.updatePending = false;
  }

  private startNewGeneration(): void {
    this.stopLoop();

    this.activeBrains = this.ga.dinos;
    this.tRexes = [];
    this.alive = [];
    this.survivalTime = [];
    this.obstaclesPassed = [];
    this.lastObstacleRight = 9999;

    for (let i = 0; i < POPULATION; i++) {
      const t = new Trex(this.canvas, sprite.set.TREX);
      t.update(0, 'RUNNING');
      this.tRexes.push(t);
      this.alive.push(true);
      this.survivalTime.push(0);
      this.obstaclesPassed.push(0);
    }

    this.distanceRan = 0;
    this.runningTime = 0;
    this.currentSpeed = this.config.SPEED;
    this.time = getTimeStamp();
    this.invertTimer = 0;
    this.invertTrigger = false;
    this.invert(true);

    // Actualiza header del panel
    this.updatePanelHeader(POPULATION);

    this.scheduleNextUpdate();
  }

  private update(): void {
    this.updatePending = false;

    const now = getTimeStamp();
    const deltaTime = now - (this.time || now);
    this.time = now;

    this.canvasCtx.clearRect(0, 0, this.dimensions.WIDTH, this.dimensions.HEIGHT);

    const hasObstacles = this.runningTime > 3000;
    this.horizon.update(deltaTime, this.currentSpeed, hasObstacles, this.inverted);

    const closestObstacle = this.horizon.obstacles[0] ?? null;

    // Detecta si el obstáculo pasó al dino (para el bonus de obstáculo)
    const obstacleRight = closestObstacle
      ? closestObstacle.xPos + closestObstacle.width
      : 9999;

    if (obstacleRight < 40 && this.lastObstacleRight >= 40) {
      for (let i = 0; i < POPULATION; i++) {
        if (this.alive[i]) this.obstaclesPassed[i]++;
      }
    }
    this.lastObstacleRight = obstacleRight;

    let aliveCount = 0;
    /** Índice del dino vivo con el mayor survivalTime (el "líder") */
    let leaderIdx = -1;
    let leaderTime = -1;

    for (let i = 0; i < POPULATION; i++) {
      if (!this.alive[i]) continue;

      const tRex = this.tRexes[i]!;
      const brain = this.activeBrains[i]!;

      if (tRex.jumping) tRex.updateJump(deltaTime);

      // ── Red Neuronal: decide la acción ──────────────────────────────────
      let inputs: number[] = [0, 0, 0, 0, 0];
      let output: number[] = [0, 0];

      if (hasObstacles && closestObstacle) {
        let target = closestObstacle;
        if (
          target.xPos + target.width < tRex.xPos &&
          this.horizon.obstacles[1]
        ) {
          target = this.horizon.obstacles[1];
        }

        inputs = [
          Math.max(0, target.xPos - tRex.xPos) / this.dimensions.WIDTH, // Distancia
          target.width / 150,                                              // Ancho
          target.typeConfig.height / 100,                                  // Altura
          tRex.yPos / this.dimensions.HEIGHT,                              // Pos Y
          this.currentSpeed / this.config.MAX_SPEED                        // Velocidad
        ];

        output = brain.brain.predict(inputs);

        if (output[0]! > 0.5 && !tRex.jumping && !tRex.ducking) {
          tRex.startJump(this.currentSpeed);
        } else if (output[1]! > 0.5) {
          if (tRex.jumping) tRex.setSpeedDrop();
          else if (!tRex.ducking) tRex.setDuck(true);
        } else {
          tRex.speedDrop = false;
          if (tRex.ducking) tRex.setDuck(false);
        }
      }
      // ────────────────────────────────────────────────────────────────────

      const collision =
        hasObstacles &&
        closestObstacle !== null &&
        checkForCollision(closestObstacle, tRex);

      if (collision) {
        tRex.update(100, 'CRASHED');
        this.alive[i] = false;

        // ── Sistema de recompensas ────────────────────────────────────────
        // Recompensa = distancia + bonus por cada obstáculo superado + tiempo
        const score = this.distanceRan
          + this.obstaclesPassed[i]! * 500
          + this.survivalTime[i]! * 0.1;
        brain.score = score;
        this.ga.savedDinos.push(brain);
      } else {
        tRex.update(deltaTime);
        this.survivalTime[i]! += deltaTime;
        aliveCount++;

        // Determina el líder (el que más tiempo lleva vivo)
        if (this.survivalTime[i]! > leaderTime) {
          leaderTime = this.survivalTime[i]!;
          leaderIdx = i;
          this.lastInputs = inputs;
          this.lastOutputs = output;
        }
      }
    }

    // ── HUD mínimo (solo info que el juego NO muestra) ────────────────────
    this.drawHUD(aliveCount);

    // ── Actualiza visualizador de la red neuronal ─────────────────────────
    if (leaderIdx >= 0 && this.visualizer) {
      const leaderBrain = this.activeBrains[leaderIdx]!;
      this.visualizer.draw(leaderBrain.brain, this.lastInputs, this.lastOutputs);
    }

    // Actualiza el header del panel
    this.updatePanelHeader(aliveCount);

    // Avanza el juego
    this.runningTime += deltaTime;
    this.distanceRan += (this.currentSpeed * deltaTime) / this.msPerFrame;
    if (this.currentSpeed < this.config.MAX_SPEED) {
      this.currentSpeed += this.config.ACCELERATION;
    }
    this.distanceMeter.update(deltaTime, Math.ceil(this.distanceRan));
    this.updateInvertMode();

    // ── ¿Todos muertos? → Evolución ──────────────────────────────────────
    if (aliveCount === 0) {
      if (this.distanceRan > this.highestScore) {
        this.highestScore = Math.ceil(this.distanceRan);
        this.distanceMeter.setHighScore(this.highestScore);
      }
      this.horizon.reset();
      this.ga.nextGeneration();
      this.startNewGeneration();
      return;
    }

    this.scheduleNextUpdate();
  }

  /** HUD mínimo dentro del canvas: solo GEN y VIVOS (sin duplicar HI/score) */
  private drawHUD(aliveCount: number): void {
    const ctx = this.canvasCtx;
    ctx.save();
    ctx.fillStyle = this.inverted ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.06)';
    ctx.fillRect(5, 5, 105, 42);

    ctx.fillStyle = this.inverted ? '#ccc' : '#444';
    ctx.font = 'bold 10px monospace';
    ctx.fillText(`GEN:   ${this.ga.generation}`, 10, 20);

    // Barra de supervivencia
    const progress = aliveCount / POPULATION;
    ctx.fillStyle = this.inverted ? 'rgba(180,180,180,0.3)' : 'rgba(0,0,0,0.1)';
    ctx.fillRect(10, 26, 90, 5);
    ctx.fillStyle = progress > 0.5 ? '#4caf50' : progress > 0.2 ? '#ff9800' : '#f44336';
    ctx.fillRect(10, 26, 90 * progress, 5);

    ctx.fillStyle = this.inverted ? '#aaa' : '#555';
    ctx.font = '9px monospace';
    ctx.fillText(`${aliveCount}/${POPULATION} vivos`, 10, 42);

    ctx.restore();
  }

  private updatePanelHeader(aliveCount: number): void {
    const genEl = document.getElementById('nn-gen');
    const aliveEl = document.getElementById('nn-alive');
    if (genEl) genEl.textContent = `GEN ${this.ga.generation}`;
    if (aliveEl) aliveEl.textContent = `VIVOS ${aliveCount}`;
  }

  private updateInvertMode(): void {
    if (this.invertTimer > this.config.INVERT_FADE_DURATION) {
      this.invertTimer = 0;
      this.invertTrigger = false;
      this.invert(false);
    } else if (this.invertTimer) {
      this.invertTimer += 16;
    } else {
      const actualDistance = this.distanceMeter.getActualDistance(Math.ceil(this.distanceRan));
      if (actualDistance > 0) {
        this.invertTrigger = !(actualDistance % this.config.INVERT_DISTANCE);
        if (this.invertTrigger && this.invertTimer === 0) {
          this.invertTimer += 16;
          this.invert(false);
        }
      }
    }
  }

  handleEvent(e: Event): void {
    if (e.type !== EVENTS.KEYDOWN) return;
    const ke = e as KeyboardEvent;
    if (ke.code === 'KeyR') {
      this.stopLoop();
      this.ga = new GeneticAlgorithm(POPULATION);
      this.highestScore = 0;
      this.horizon.reset();
      this.distanceMeter.reset();
      this.startNewGeneration();
    }
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
      this.containerEl.style.width = `${this.dimensions.WIDTH}px`;
    }
  }

  private scheduleNextUpdate(): void {
    if (this.updatePending) return;
    this.updatePending = true;
    this.raqId = requestAnimationFrame(() => this.update());
  }

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
