/**
 * NeuralNetwork - Red Neuronal Feed-Forward con 2 capas ocultas
 * Arquitectura: 5 entradas → 8 neuronas → 6 neuronas → 2 salidas
 * Activación oculta: tanh (mejor que sigmoid para RL)
 * Activación salida: sigmoid (probabilidad 0..1)
 */
export class NeuralNetwork {
  // Capa 1: input → hidden1
  private w1: number[][];
  private b1: number[];
  // Capa 2: hidden1 → hidden2
  private w2: number[][];
  private b2: number[];
  // Capa 3: hidden2 → output
  private w3: number[][];
  private b3: number[];

  readonly inputSize: number;
  readonly hidden1Size: number;
  readonly hidden2Size: number;
  readonly outputSize: number;

  constructor(
    inputSize: number = 5,
    hidden1Size: number = 8,
    hidden2Size: number = 6,
    outputSize: number = 2
  ) {
    this.inputSize = inputSize;
    this.hidden1Size = hidden1Size;
    this.hidden2Size = hidden2Size;
    this.outputSize = outputSize;

    this.w1 = NeuralNetwork.randomMatrix(hidden1Size, inputSize);
    this.b1 = NeuralNetwork.randomVector(hidden1Size);
    this.w2 = NeuralNetwork.randomMatrix(hidden2Size, hidden1Size);
    this.b2 = NeuralNetwork.randomVector(hidden2Size);
    this.w3 = NeuralNetwork.randomMatrix(outputSize, hidden2Size);
    this.b3 = NeuralNetwork.randomVector(outputSize);
  }

  /** Forward pass: devuelve las activaciones de salida */
  predict(inputs: number[]): number[] {
    const h1 = NeuralNetwork.activate(NeuralNetwork.matVecMul(this.w1, inputs, this.b1), 'tanh');
    const h2 = NeuralNetwork.activate(NeuralNetwork.matVecMul(this.w2, h1, this.b2), 'tanh');
    const out = NeuralNetwork.activate(NeuralNetwork.matVecMul(this.w3, h2, this.b3), 'sigmoid');
    return out;
  }

  /** Crea una copia exacta de esta red */
  copy(): NeuralNetwork {
    const nn = new NeuralNetwork(
      this.inputSize,
      this.hidden1Size,
      this.hidden2Size,
      this.outputSize
    );
    nn.w1 = this.w1.map(r => [...r]);
    nn.b1 = [...this.b1];
    nn.w2 = this.w2.map(r => [...r]);
    nn.b2 = [...this.b2];
    nn.w3 = this.w3.map(r => [...r]);
    nn.b3 = [...this.b3];
    return nn;
  }

  /**
   * Crossover uniforme: mezcla genes de dos redes padre
   * Cada peso tiene 50% de probabilidad de venir de padre A o padre B
   */
  static crossover(a: NeuralNetwork, b: NeuralNetwork): NeuralNetwork {
    const child = a.copy();
    child.w1 = NeuralNetwork.crossoverMatrix(a.w1, b.w1);
    child.b1 = NeuralNetwork.crossoverVector(a.b1, b.b1);
    child.w2 = NeuralNetwork.crossoverMatrix(a.w2, b.w2);
    child.b2 = NeuralNetwork.crossoverVector(a.b2, b.b2);
    child.w3 = NeuralNetwork.crossoverMatrix(a.w3, b.w3);
    child.b3 = NeuralNetwork.crossoverVector(a.b3, b.b3);
    return child;
  }

  /**
   * Mutación gaussiana: cada peso tiene `rate` probabilidad de ser perturbado
   * con ruido gaussiano de desviación `strength`
   */
  mutate(rate: number = 0.1, strength: number = 0.3): void {
    const mutFn = (v: number) =>
      Math.random() < rate ? v + NeuralNetwork.gaussianRandom() * strength : v;

    this.w1 = this.w1.map(r => r.map(mutFn));
    this.b1 = this.b1.map(mutFn);
    this.w2 = this.w2.map(r => r.map(mutFn));
    this.b2 = this.b2.map(mutFn);
    this.w3 = this.w3.map(r => r.map(mutFn));
    this.b3 = this.b3.map(mutFn);
  }

  // ── Utilidades privadas ──────────────────────────────────────────────────

  private static matVecMul(w: number[][], x: number[], b: number[]): number[] {
    return w.map((row, i) => row.reduce((sum, wij, j) => sum + wij * (x[j] ?? 0), 0) + (b[i] ?? 0));
  }

  private static activate(z: number[], fn: 'tanh' | 'sigmoid'): number[] {
    if (fn === 'tanh') return z.map(v => Math.tanh(v));
    return z.map(v => 1 / (1 + Math.exp(-v)));
  }

  private static crossoverMatrix(a: number[][], b: number[][]): number[][] {
    return a.map((row, i) => row.map((v, j) => (Math.random() < 0.5 ? v : (b[i]?.[j] ?? v))));
  }

  private static crossoverVector(a: number[], b: number[]): number[] {
    return a.map((v, i) => (Math.random() < 0.5 ? v : (b[i] ?? v)));
  }

  private static randomMatrix(rows: number, cols: number): number[][] {
    // Inicialización Xavier/Glorot para mejor convergencia
    const limit = Math.sqrt(6 / (rows + cols));
    return Array.from({ length: rows }, () =>
      Array.from({ length: cols }, () => (Math.random() * 2 - 1) * limit)
    );
  }

  private static randomVector(size: number): number[] {
    return Array.from({ length: size }, () => 0); // Bias inicializado en 0
  }

  /** Box-Muller transform para ruido gaussiano */
  private static gaussianRandom(): number {
    const u = 1 - Math.random();
    const v = Math.random();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }
}
