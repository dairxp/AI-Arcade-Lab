import { NeuralNetwork } from './NeuralNetwork';

/**
 * DinoBrain - Encapsula el cerebro (red neuronal) y el historial de fitness
 * de un único dinosaurio en la población.
 */
export class DinoBrain {
  brain: NeuralNetwork;
  /** Distancia recorrida en la partida actual */
  score: number = 0;
  /** Fitness normalizado (0..1), calculado al morir */
  fitness: number = 0;

  constructor(brain?: NeuralNetwork) {
    this.brain = brain ? brain.copy() : new NeuralNetwork();
  }

  /** Aplica mutación gaussiana al cerebro */
  mutate(rate = 0.1, strength = 0.25): void {
    this.brain.mutate(rate, strength);
  }
}

/**
 * GeneticAlgorithm - Gestiona la evolución de la población de dinosaurios
 *
 * Estrategia:
 *  - Elitismo: los mejores 2 cerebros pasan intactos a la siguiente generación
 *  - Selección proporcional al fitness (ruleta de fitness^2)
 *  - Crossover uniforme entre dos padres seleccionados
 *  - Mutación gaussiana con tasa y fuerza configurables
 */
export class GeneticAlgorithm {
  readonly populationSize: number;
  dinos: DinoBrain[] = [];

  /** Almacena los cerebros de los dinos que murieron esta generación */
  savedDinos: DinoBrain[] = [];
  generation: number = 1;

  /** Mejor distancia de TODAS las generaciones */
  allTimeBest: number = 0;
  /** Mejor cerebro de TODAS las generaciones (para mostrarlo) */
  bestBrain: NeuralNetwork | null = null;

  private readonly ELITE_COUNT = 2;
  private readonly MUTATION_RATE = 0.12;
  private readonly MUTATION_STRENGTH = 0.3;

  constructor(populationSize: number) {
    this.populationSize = populationSize;
    this.dinos = this.generatePopulation();
  }

  /** Genera una población completamente aleatoria */
  generatePopulation(): DinoBrain[] {
    return Array.from({ length: this.populationSize }, () => new DinoBrain());
  }

  /**
   * Avanza a la siguiente generación:
   * 1. Calcula el fitness de todos los que murieron
   * 2. Guarda élite (los mejores intactos)
   * 3. Llena el resto con hijos: crossover + mutación
   */
  nextGeneration(): void {
    if (this.savedDinos.length === 0) {
      // Nadie corrió — generación aleatoria de emergencia
      this.dinos = this.generatePopulation();
      this.generation++;
      return;
    }

    this.calculateFitness();

    // Actualiza el mejor cerebro histórico
    const bestThisGen = this.savedDinos.reduce((a, b) => (a.score > b.score ? a : b));
    if (bestThisGen.score > this.allTimeBest) {
      this.allTimeBest = bestThisGen.score;
      this.bestBrain = bestThisGen.brain.copy();
    }

    // Ordena por score descendente para élite
    const sorted = [...this.savedDinos].sort((a, b) => b.score - a.score);

    const next: DinoBrain[] = [];

    // 1. Elitismo: los mejores pasan intactos
    for (let i = 0; i < Math.min(this.ELITE_COUNT, sorted.length); i++) {
      next.push(new DinoBrain(sorted[i]!.brain));
    }

    // 2. Rellena el resto con crossover + mutación
    while (next.length < this.populationSize) {
      const parentA = this.pickOne();
      const parentB = this.pickOne();
      const childBrain = NeuralNetwork.crossover(parentA.brain, parentB.brain);
      const child = new DinoBrain(childBrain);
      child.mutate(this.MUTATION_RATE, this.MUTATION_STRENGTH);
      next.push(child);
    }

    this.dinos = next;
    this.savedDinos = [];
    this.generation++;
  }

  /**
   * Selección proporcional al fitness (ruleta)
   * Se usa fitness^2 para favorecer más a los mejores
   */
  private pickOne(): DinoBrain {
    let r = Math.random();
    for (const dino of this.savedDinos) {
      r -= dino.fitness;
      if (r <= 0) return dino;
    }
    // Fallback al último
    return this.savedDinos[this.savedDinos.length - 1]!;
  }

  /**
   * Calcula el fitness normalizado de cada individuo.
   * Fitness = score^2 / suma(score^2) para dar más peso a los mejores.
   */
  private calculateFitness(): void {
    let sum = 0;
    for (const d of this.savedDinos) {
      d.score = d.score * d.score; // fitness cuadrático
      sum += d.score;
    }
    if (sum === 0) {
      const eq = 1 / this.savedDinos.length;
      for (const d of this.savedDinos) d.fitness = eq;
    } else {
      for (const d of this.savedDinos) d.fitness = d.score / sum;
    }
  }
}
