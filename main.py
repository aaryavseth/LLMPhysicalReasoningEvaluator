import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "llama-3.3-70b-versatile"

USAGE = """
Physical Reasoning Benchmark — powered by Groq

Commands:
  run        Send questions to the model and save responses
  score      Judge a completed run with an LLM scorer
  visualize  Generate an HTML dashboard from a scored run
  full       Run all three steps in sequence

Examples:
  python main.py run --model llama-3.3-70b-versatile
  python main.py run --model llama-3.3-70b-versatile --category "Gravity & Projectiles"
  python main.py score --results results/run_20250325_120000.json
  python main.py visualize --results results/scored_run_20250325_120000.json
  python main.py full --model llama-3.3-70b-versatile
"""


def require_api_key() -> None:
    if not os.environ.get("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY environment variable is not set.")
        print("Export it with: export GROQ_API_KEY=your_key_here")
        sys.exit(1)


def cmd_run(args: argparse.Namespace) -> Path:
    from evaluator.runner import run
    require_api_key()
    return run(args.model, args.category)


def cmd_score(args: argparse.Namespace) -> Path:
    from evaluator.scorer import score
    require_api_key()
    return score(Path(args.results))


def cmd_visualize(args: argparse.Namespace) -> Path:
    from visualizer.dashboard import build
    return build(Path(args.results))


def cmd_full(args: argparse.Namespace) -> None:
    from evaluator.runner import run
    from evaluator.scorer import score
    from visualizer.dashboard import build
    require_api_key()
    run_path = run(args.model, args.category)
    scored_path = score(run_path)
    build(scored_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="LLM Physical Reasoning Evaluator",
        add_help=True,
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the benchmark against a model")
    run_parser.add_argument("--model", default=DEFAULT_MODEL)
    run_parser.add_argument("--category", default=None)

    score_parser = subparsers.add_parser("score", help="Score a completed run file")
    score_parser.add_argument("--results", required=True, metavar="FILE")

    viz_parser = subparsers.add_parser("visualize", help="Generate an HTML dashboard from a scored run")
    viz_parser.add_argument("--results", required=True, metavar="FILE")

    full_parser = subparsers.add_parser("full", help="Run, score, and visualize in one step")
    full_parser.add_argument("--model", default=DEFAULT_MODEL)
    full_parser.add_argument("--category", default=None)

    args = parser.parse_args()

    if args.command is None:
        print(USAGE)
        sys.exit(0)

    dispatch = {
        "run": cmd_run,
        "score": cmd_score,
        "visualize": cmd_visualize,
        "full": cmd_full,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
