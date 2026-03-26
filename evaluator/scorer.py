import argparse
import json
import os
import re
import sys
from pathlib import Path

from groq import Groq
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn
from rich.table import Table
from rich.console import Console

JUDGE_MODEL = "llama-3.1-8b-instant"
RESULTS_DIR = Path(__file__).parent.parent / "results"

JUDGE_PROMPT = """\
You are a physics educator grading a student's answer.

Question: {question}

Correct answer: {correct_answer}

Student's response: {model_response}

Score the response using this rubric:
0 - Wrong or completely irrelevant
1 - Partially correct but missing the key physical insight
2 - Correct but explanation is weak or incomplete
3 - Fully correct with clear physical reasoning

Respond in this exact format:
SCORE: <integer 0-3>
REASONING: <one or two sentences>"""


def parse_judge_response(text: str) -> tuple[int, str]:
    score_match = re.search(r"SCORE:\s*([0-3])", text)
    reasoning_match = re.search(r"REASONING:\s*(.+)", text, re.DOTALL)

    score = int(score_match.group(1)) if score_match else 0
    reasoning = reasoning_match.group(1).strip() if reasoning_match else text.strip()
    return score, reasoning


def judge_response(client: Groq, question: dict) -> tuple[int, str]:
    prompt = JUDGE_PROMPT.format(
        question=question["question"],
        correct_answer=question["correct_answer"],
        model_response=question["model_response"],
    )
    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return parse_judge_response(response.choices[0].message.content)


def print_summary(results: list[dict], console: Console) -> None:
    overall_avg = sum(r["score"] for r in results) / len(results)

    by_category: dict[str, list[int]] = {}
    by_difficulty: dict[str, list[int]] = {}
    for r in results:
        by_category.setdefault(r["category"], []).append(r["score"])
        by_difficulty.setdefault(r["difficulty"], []).append(r["score"])

    console.print(f"\n[bold]Overall average score:[/bold] [cyan]{overall_avg:.2f}[/cyan] / 3.00\n")

    cat_table = Table(title="Score by Category", show_lines=False)
    cat_table.add_column("Category", style="bold")
    cat_table.add_column("Avg Score", justify="right")
    cat_table.add_column("Questions", justify="right")
    for category, scores in sorted(by_category.items()):
        cat_table.add_row(category, f"{sum(scores)/len(scores):.2f}", str(len(scores)))
    console.print(cat_table)

    diff_order = ["easy", "medium", "hard"]
    diff_table = Table(title="Score by Difficulty", show_lines=False)
    diff_table.add_column("Difficulty", style="bold")
    diff_table.add_column("Avg Score", justify="right")
    diff_table.add_column("Questions", justify="right")
    for difficulty in diff_order:
        if difficulty in by_difficulty:
            scores = by_difficulty[difficulty]
            diff_table.add_row(difficulty.capitalize(), f"{sum(scores)/len(scores):.2f}", str(len(scores)))
    console.print(diff_table)


def score(run_path: Path) -> Path:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable is not set.")
        sys.exit(1)

    with open(run_path, encoding="utf-8") as f:
        run_data = json.load(f)

    client = Groq(api_key=api_key)
    results = run_data["results"]

    with Progress(
        SpinnerColumn("line"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
    ) as progress:
        task = progress.add_task(f"Scoring with {JUDGE_MODEL}", total=len(results))

        for result in results:
            progress.update(task, description=f"[cyan]{result['id']}[/cyan]")
            result["score"], result["judge_reasoning"] = judge_response(client, result)
            progress.advance(task)

    output_path = RESULTS_DIR / f"scored_{run_path.name}"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(run_data, f, indent=2, ensure_ascii=False)

    console = Console()
    print_summary(results, console)
    console.print(f"\nScored results saved to [green]{output_path}[/green]")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Score a benchmark run using an LLM judge")
    parser.add_argument("run_file", type=Path, help="Path to results/run_*.json file")
    args = parser.parse_args()

    if not args.run_file.exists():
        print(f"Error: file not found: {args.run_file}")
        sys.exit(1)

    score(args.run_file)


if __name__ == "__main__":
    main()
