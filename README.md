# LLM Physical Reasoning Evaluator

Benchmarks large language models on physical reasoning across 8 categories using an LLM-as-judge scoring rubric.

[Live results dashboard](https://aaryavseth.github.io/LLMPhysicalReasoningEvaluator/)

---

## Motivation

Physical reasoning requires a model to simulate how the world behaves rather than recall facts. This makes it one of the harder failure modes for LLMs, and a critical one for robotics, where models must anticipate how objects move and interact before acting. The [NEWTON benchmark](https://arxiv.org/abs/2310.07445) (Wang et al., 2023) showed that even strong LLMs fail surprisingly often on intuitive physics questions. This project builds a focused, runnable version of that idea.

---

## Benchmark design

### Categories

| Category | Description |
|---|---|
| Gravity & Projectiles | Freefall, horizontal throws, parabolic motion |
| Buoyancy | Archimedes' principle, floating and sinking |
| Friction & Inclines | Static vs kinetic friction, inclined planes |
| Fluid Dynamics | Flow rate, pressure, Bernoulli's principle |
| Collisions & Momentum | Conservation of momentum, elastic and inelastic collisions |
| Center of Mass | Balance, stability, distributed mass |
| Levers & Torque | Mechanical advantage, rotational equilibrium |
| Thermal Expansion | Volume and length changes with temperature |

### Difficulty

Each question is tagged easy, medium, or hard based on the number of reasoning steps required and whether the answer is counterintuitive.

### Scoring rubric

| Score | Meaning |
|---|---|
| 3 | Correct answer with sound physical reasoning |
| 2 | Correct answer but incomplete or shallow explanation |
| 1 | Partially correct, right direction but wrong details |
| 0 | Incorrect or fundamentally flawed reasoning |

---

## Results: llama-3.3-70b-versatile

| Metric | Value |
|---|---|
| Overall accuracy | 63.3% |
| Avg judge score | 1.90 / 3.00 |
| Best category | Thermal Expansion (80%) |
| Worst category | Buoyancy (46.7%) |

The model performs well on rule-based categories like Thermal Expansion and Friction but struggles with Buoyancy, which requires counterintuitive reasoning about displaced volume rather than object weight. This is consistent with NEWTON's finding that LLMs tend to apply surface-level heuristics rather than simulate physical principles.

---

## Quick start
```bash
git clone https://github.com/aaryavseth/LLMPhysicalReasoningEvaluator
cd LLMPhysicalReasoningEvaluator
pip install -r requirements.txt
```

Set your Groq API key (free tier works):
```bash
export GROQ_API_KEY=your_key_here
```

Run the full benchmark:
```bash
python main.py full --model llama-3.3-70b-versatile
```

Results are saved to `results/` and the dashboard opens automatically in your browser.

---

## Project structure
```
LLMPhysicalReasoningEvaluator/
├── benchmark/        # 40 questions across 8 categories
├── evaluator/        # Runner and LLM judge scorer
├── visualizer/       # Dashboard generator
├── results/          # JSON output from each run
├── docs/             # GitHub Pages dashboard
│   └── index.html
├── main.py           # CLI entrypoint
└── README.md
```

---

## Limitations

- Question set is a pilot of 40 questions. A larger peer-validated set is the obvious next step.
- Only one model evaluated so far. Multi-model comparison is planned.
- The judge model introduces its own biases. Prompt sensitivity analysis has not been conducted.

---

## References

Wang et al. (2023). NEWTON: Are Large Language Models Capable of Physical Reasoning? EMNLP 2023. https://arxiv.org/abs/2310.07445

---

## License

MIT
