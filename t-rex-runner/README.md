# T-Rex Runner — Monorepo

> Chrome's offline T-Rex easter egg, modernized and extended with reinforcement learning.

```
repo/
├── t-rex-runner/              the game (Vite + TypeScript)
└── reinforcement-learning-poo/ RL agent training
```

---

## t-rex-runner

The classic Chrome dino game, ported from legacy Chromium JavaScript to a clean Vite + TypeScript codebase with one class per module.

```bash
cd t-rex-runner
npm install
npm run dev       # http://localhost:5173
npm run build
npm run typecheck
```

| Key | Action |
|-----|--------|
| `Space` / `↑` | Jump |
| `↓` | Duck |
| `Enter` | Restart after crash |

See [`t-rex-runner/README.md`](t-rex-runner/README.md) for full details.

---

## reinforcement-learning-poo

Reinforcement learning agent that learns to play T-Rex Runner autonomously.

See [`reinforcement-learning-poo/README.md`](reinforcement-learning-poo/README.md).

---

## Credits

- Original game: [Chromium Authors](https://chromium.googlesource.com/chromium/src/+/main/components/neterror/resources/) — BSD 3-Clause.
- Standalone extraction: [wayou/t-rex-runner](https://github.com/wayou/t-rex-runner).
- Vite + TypeScript port & RL extension: [Aldair Andrade](https://github.com/aymefreyson), 2026.

## License

BSD 3-Clause — see [LICENSE](LICENSE).
