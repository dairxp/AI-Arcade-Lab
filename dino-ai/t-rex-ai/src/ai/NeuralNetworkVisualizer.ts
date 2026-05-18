import type { NeuralNetwork } from './NeuralNetwork';

/**
 * NeuralNetworkVisualizer  — estilo retro dino
 *
 * Paleta igual que el juego Chrome Dino:
 *   Fondo:       blanco  (#fff)
 *   Líneas/texto: gris oscuro (#535353)
 *   Peso +       verde oscuro retro (#2e7d32)
 *   Peso −       rojo oscuro retro  (#c62828)
 *   Neurona activa  → relleno gris oscuro (#535353)
 *   Neurona inactiva → solo contorno gris
 *   Salida activa   → relleno negro con borde negro
 *
 * Capas: [5 entradas] → [8 oculta] → [6 oculta] → [2 salidas]
 */
export class NeuralNetworkVisualizer {
  private ctx: CanvasRenderingContext2D;

  private readonly INPUT_LABELS  = ['Distancia', 'Ancho', 'Altura', 'Pos Y', 'Velocidad'];
  private readonly OUTPUT_LABELS = ['SALTAR', 'AGACHAR'];
  private readonly LAYER_SIZES   = [5, 8, 6, 2];

  // Paleta retro — misma que el juego dino
  private readonly C = {
    bg:        '#ffffff',   // fondo blanco
    border:    '#535353',   // gris oscuro (contorno neuronas, texto)
    dim:       '#aaaaaa',   // gris claro (neuronas inactivas, texto secundario)
    active:    '#535353',   // relleno neurona activa
    outOn:     '#212121',   // salida ON  (negro)
    outOff:    '#e0e0e0',   // salida OFF (gris muy claro)
    wPos:      '#2e7d32',   // peso positivo  (verde retro oscuro)
    wNeg:      '#c62828',   // peso negativo  (rojo  retro oscuro)
    label:     '#535353',   // etiquetas
    labelDim:  '#aaaaaa',   // etiquetas secundarias
  };

  constructor(private canvas: HTMLCanvasElement) {
    this.ctx = canvas.getContext('2d')!;
    // Lee la paleta de noche si el body tiene .inverted
    this.syncTheme();
  }

  /** Ajusta la paleta si el juego está en modo noche */
  private syncTheme(): void {
    const night = document.body.classList.contains('inverted');
    if (night) {
      this.C.bg       = '#1a1a1a';
      this.C.border   = '#888888';
      this.C.dim      = '#555555';
      this.C.active   = '#cccccc';
      this.C.outOn    = '#f5f5f5';
      this.C.outOff   = '#333333';
      this.C.label    = '#cccccc';
      this.C.labelDim = '#666666';
    } else {
      this.C.bg       = '#ffffff';
      this.C.border   = '#535353';
      this.C.dim      = '#cccccc';
      this.C.active   = '#535353';
      this.C.outOn    = '#212121';
      this.C.outOff   = '#e0e0e0';
      this.C.label    = '#535353';
      this.C.labelDim = '#aaaaaa';
    }
  }

  /** Llamado cada frame — dibuja la red con los valores actuales */
  draw(nn: NeuralNetwork, inputs: number[], outputs: number[]): void {
    this.syncTheme();

    const W = this.canvas.width;
    const H = this.canvas.height;
    const ctx = this.ctx;

    // --- Fondo ---
    ctx.fillStyle = this.C.bg;
    ctx.fillRect(0, 0, W, H);

    // --- Activaciones de cada capa ---
    const h1 = this.forwardLayer((nn as any).w1, (nn as any).b1, inputs, 'tanh');
    const h2 = this.forwardLayer((nn as any).w2, (nn as any).b2, h1,     'tanh');

    const activations: number[][] = [
      inputs.map(v => Math.max(0, Math.min(1, v))),
      h1.map(v => (v + 1) / 2),   // tanh -1..1  → 0..1
      h2.map(v => (v + 1) / 2),
      outputs,
    ];

    // --- Posiciones de las neuronas ---
    const padX    = 72;   // espacio para etiquetas de entrada
    const padY    = 18;
    const padRight = 60;  // espacio para etiquetas de salida
    const usableW = W - padX - padRight;
    const usableH = H - padY * 2;

    const xs = this.LAYER_SIZES.map((_, l) =>
      padX + (l / (this.LAYER_SIZES.length - 1)) * usableW
    );

    const positions: { x: number; y: number }[][] = this.LAYER_SIZES.map((size, l) =>
      Array.from({ length: size }, (_, n) => ({
        x: xs[l]!,
        y: padY + (n + 0.5) * (usableH / size),
      }))
    );

    // --- Matrices de pesos ---
    const weights: number[][][] = [
      (nn as any).w1,
      (nn as any).w2,
      (nn as any).w3,
    ];

    // --- Conexiones ---
    for (let l = 0; l < positions.length - 1; l++) {
      const from  = positions[l]!;
      const to    = positions[l + 1]!;
      const W_mat = weights[l]!;

      for (let j = 0; j < to.length; j++) {
        for (let i = 0; i < from.length; i++) {
          const w   = W_mat[j]?.[i] ?? 0;
          const abs = Math.min(Math.abs(w), 1);
          if (abs < 0.12) continue;         // ignora pesos muy débiles

          const alpha = 0.20 + abs * 0.60;
          ctx.strokeStyle = w > 0
            ? `rgba(46, 125, 50,  ${alpha})` // verde retro
            : `rgba(198, 40, 40, ${alpha})`; // rojo retro
          ctx.lineWidth = 0.8 + abs * 1.2;
          ctx.beginPath();
          ctx.moveTo(from[i]!.x, from[i]!.y);
          ctx.lineTo(to[j]!.x,   to[j]!.y);
          ctx.stroke();
        }
      }
    }

    // --- Neuronas ---
    for (let l = 0; l < positions.length; l++) {
      const isInput  = l === 0;
      const isOutput = l === positions.length - 1;
      const r = isInput || isOutput ? 11 : 8;

      for (let n = 0; n < positions[l]!.length; n++) {
        const { x, y } = positions[l]![n]!;
        const act = activations[l]![n] ?? 0;

        ctx.lineWidth = 1.5;

        if (isOutput) {
          // Salida: negro sólido si activa, gris claro si no
          ctx.fillStyle   = act > 0.5 ? this.C.outOn  : this.C.outOff;
          ctx.strokeStyle = act > 0.5 ? this.C.outOn  : this.C.border;
        } else {
          // Capas ocultas e inputs: interpolamos blanco→gris oscuro
          const t   = act;                          // 0..1
          const grey = Math.floor(255 - t * (255 - 50)); // 255 (blanco) → 50 (casi negro)
          ctx.fillStyle   = `rgb(${grey},${grey},${grey})`;
          ctx.strokeStyle = this.C.border;
        }

        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        // Valor numérico en entradas y salidas
        if (isInput || isOutput) {
          ctx.fillStyle  = act > 0.5 ? '#fff' : this.C.label;
          ctx.font       = '7px monospace';
          ctx.textAlign  = 'center';
          ctx.fillText(act.toFixed(2), x, y + 3);
        }
      }
    }

    // --- Etiquetas de entrada (izquierda) ---
    ctx.font      = '9px monospace';
    ctx.textAlign = 'right';
    ctx.fillStyle = this.C.label;
    this.INPUT_LABELS.forEach((label, i) => {
      const { x, y } = positions[0]![i]!;
      ctx.fillText(label, x - 14, y + 3);
    });

    // --- Etiquetas de salida (derecha) ---
    ctx.textAlign = 'left';
    this.OUTPUT_LABELS.forEach((label, i) => {
      const { x, y } = positions[positions.length - 1]![i]!;
      const act = activations[activations.length - 1]![i] ?? 0;
      ctx.fillStyle = act > 0.5 ? this.C.outOn : this.C.labelDim;
      ctx.font      = act > 0.5 ? 'bold 9px monospace' : '9px monospace';
      ctx.fillText(label, x + 14, y + 3);
    });

    // --- Leyenda ---
    ctx.font      = '9px monospace';
    ctx.textAlign = 'left';

    ctx.fillStyle = 'rgba(46, 125, 50, 0.9)';
    ctx.fillText('■', 8, H - 6);
    ctx.fillStyle = this.C.labelDim;
    ctx.fillText(' peso +', 18, H - 6);

    ctx.fillStyle = 'rgba(198, 40, 40, 0.9)';
    ctx.fillText('■', 72, H - 6);
    ctx.fillStyle = this.C.labelDim;
    ctx.fillText(' peso −', 82, H - 6);
  }

  /** Propagación hacia adelante de una capa */
  private forwardLayer(
    w: number[][],
    b: number[],
    x: number[],
    fn: 'tanh' | 'sigmoid'
  ): number[] {
    return w.map((row, i) => {
      const sum = row.reduce((s, wij, j) => s + wij * (x[j] ?? 0), 0) + (b[i] ?? 0);
      return fn === 'tanh' ? Math.tanh(sum) : 1 / (1 + Math.exp(-sum));
    });
  }
}
