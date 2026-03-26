# LLM Physical Reasoning Evaluator

Benchmarks LLM performance on physical reasoning questions and generates an interactive HTML report.

Inspired by the [NEWTON](https://arxiv.org/abs/2310.07445) physical intuition benchmark paper.

---

## How it works

40 questions across 8 categories test whether a model can reason about the physical world:

- Gravity & Projectiles
- Collisions & Momentum
- Fluid Dynamics
- Levers & Torque
- Thermal Expansion
- Center of Mass
- Friction & Inclines
- Buoyancy

Each question is sent to the target model via the Groq API. A second Groq call uses `llama3-8b-8192` as an LLM judge to score the response on a 0–3 rubric:

| Score | Meaning |
|-------|---------|
| 0 | Wrong or completely irrelevant |
| 1 | Partially correct, missing the key physical insight |
| 2 | Correct but explanation is weak or incomplete |
| 3 | Fully correct with clear physical reasoning |

Results are saved as JSON and rendered as a self-contained HTML dashboard with per-category and per-difficulty breakdowns.

Groq is used throughout for fast, free inference.

---

## Quick start

**1. Clone and install**

```bash
git clone https://github.com/yourname/llm-physical-reasoning-evaluator
cd llm-physical-reasoning-evaluator
pip install -r requirements.txt
```

**2. Export your Groq API key**

```bash
export GROQ_API_KEY=your_key_here
```

Get a free key at [console.groq.com](https://console.groq.com).

**3. Run the full benchmark**

```bash
python main.py full
```

This runs all 40 questions, scores them, and opens the dashboard in your browser.

---

## CLI

```
python main.py run        Run questions against a model, save raw responses
python main.py score      Score a saved run file with the LLM judge
python main.py visualize  Generate the HTML dashboard from a scored run
python main.py full       Run all three steps in sequence
```

**Options**

```
run / full:
  --model      Model to evaluate (default: llama-3.3-70b-versatile)
  --category   Restrict to one category (default: all)

score:
  --results    Path to results/run_*.json

visualize:
  --results    Path to results/scored_run_*.json
```

**Examples**

```bash
# Evaluate a specific category
python main.py run --model llama-3.3-70b-versatile --category "Fluid Dynamics"

# Score an existing run
python main.py score --results results/run_20250325_120000.json

# Regenerate the dashboard without re-running
python main.py visualize --results results/scored_run_20250325_120000.json
```

---

## Extending

- **Add questions** — edit `benchmark/questions.json`. Each entry needs `id`, `category`, `question`, `correct_answer`, `difficulty`, and `explanation`. The runner picks up all questions automatically.

- **Swap models** — pass any model ID supported by Groq via `--model`. The judge model is hardcoded to `llama3-8b-8192` in `evaluator/scorer.py`; change `JUDGE_MODEL` there to use a different one.

- **Add categories** — add questions with a new `category` string. No other changes needed; the dashboard groups by category dynamically.

---

## Why this exists

Physical reasoning is a documented weak spot for LLMs. Models trained on text learn to pattern-match physics terminology without developing reliable intuitions about how objects actually behave — a gap that becomes critical in robotics and embodied AI, where a planning model needs to predict the real-world consequences of actions before they are executed. Standard benchmarks focus on mathematical problem-solving; this one focuses on conceptual understanding of the kind a robot needs when reasoning about manipulation, locomotion, or tool use.
