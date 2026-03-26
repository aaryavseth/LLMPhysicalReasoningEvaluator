import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from groq import Groq
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

QUESTIONS_PATH = Path(__file__).parent.parent / "benchmark" / "questions.json"
RESULTS_DIR = Path(__file__).parent.parent / "results"
SYSTEM_PROMPT = "You are being tested on physical reasoning. Answer concisely and directly."


def load_questions(category: str | None) -> list[dict]:
    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        all_questions = json.load(f)["questions"]
    if category:
        filtered = [q for q in all_questions if q["category"].lower() == category.lower()]
        if not filtered:
            available = sorted({q["category"] for q in all_questions})
            print(f"[red]No questions found for category '{category}'.[/red]")
            print("Available categories:")
            for c in available:
                print(f"  {c}")
            sys.exit(1)
        return filtered
    return all_questions


def query_model(client: Groq, question: str, model: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content


def run(model: str, category: str | None) -> Path:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable is not set.")
        sys.exit(1)

    client = Groq(api_key=api_key)
    questions = load_questions(category)
    results = []

    with Progress(
        SpinnerColumn("line"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
    ) as progress:
        task = progress.add_task(f"Running {model}", total=len(questions))

        for q in questions:
            progress.update(task, description=f"[cyan]{q['id']}[/cyan]")
            model_response = query_model(client, q["question"], model)
            results.append({
                "id": q["id"],
                "category": q["category"],
                "question": q["question"],
                "correct_answer": q["correct_answer"],
                "model_response": model_response,
                "difficulty": q["difficulty"],
                "explanation": q["explanation"],
            })
            progress.advance(task)

    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"run_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"model": model, "results": results}, f, indent=2, ensure_ascii=False)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Run physical reasoning benchmark against Groq API")
    parser.add_argument("--model", default="llama-3.3-70b-versatile")
    parser.add_argument("--category", default=None)
    args = parser.parse_args()

    output_path = run(args.model, args.category)
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
