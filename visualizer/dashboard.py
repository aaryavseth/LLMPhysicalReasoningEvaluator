import argparse
import json
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

RESULTS_DIR = Path(__file__).parent.parent / "results"
DIFF_ORDER = ["easy", "medium", "hard"]

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Benchmark Results</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:              #0a0a0a;
      --surface:         #111111;
      --surface-raised:  #161616;
      --border:          rgba(255,255,255,0.08);
      --border-subtle:   rgba(255,255,255,0.04);
      --text-primary:    rgba(255,255,255,0.92);
      --text-secondary:  rgba(255,255,255,0.55);
      --text-muted:      rgba(255,255,255,0.32);
      --accent:          #00aaff;
      --accent-warn:     #f59e0b;
      --accent-neg:      #ff3366;
      --accent-teal:     #00c8b4;
      --score-0-bg: rgba(255,51,102,0.12);   --score-0-fg: #ff3366;
      --score-1-bg: rgba(245,158,11,0.12);   --score-1-fg: #f59e0b;
      --score-2-bg: rgba(0,200,180,0.12);    --score-2-fg: #00c8b4;
      --score-3-bg: rgba(0,170,255,0.12);    --score-3-fg: #00aaff;
      --diff-easy-bg:   rgba(0,170,255,0.1);   --diff-easy-fg:   #00aaff;
      --diff-medium-bg: rgba(245,158,11,0.1);  --diff-medium-fg: #f59e0b;
      --diff-hard-bg:   rgba(255,51,102,0.1);  --diff-hard-fg:   #ff3366;
    }

    body {
      font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
      font-size: 15px;
      line-height: 1.5;
      background: var(--bg);
      color: var(--text-primary);
    }

    .topbar {
      background: #080808;
      border-bottom: 1px solid var(--accent);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 32px;
      height: 52px;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    .topbar-left { display: flex; align-items: center; gap: 20px; }
    .topbar-title { font-weight: 500; font-size: 14px; color: var(--text-primary); }
    .topbar-model {
      font-family: "SF Mono", "Fira Code", "Consolas", monospace;
      font-size: 12px;
      color: var(--text-muted);
    }
    .topbar-right { display: none; }

    main { max-width: 1280px; margin: 0 auto; padding: 32px 32px 64px; }

    .cards {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 24px 24px 20px;
    }
    .card-label {
      font-size: 12px;
      font-weight: 400;
      color: var(--text-muted);
      margin-bottom: 10px;
    }
    .card-value {
      font-size: 28px;
      font-weight: 500;
      font-variant-numeric: tabular-nums;
      line-height: 1.1;
      color: var(--text-primary);
    }
    .card-sub {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 6px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .val-blue  { color: var(--accent);      text-shadow: 0 0 22px rgba(0,170,255,0.5); }
    .val-amber { color: var(--accent-warn);  text-shadow: 0 0 22px rgba(245,158,11,0.4); }
    .val-red   { color: var(--accent-neg);   text-shadow: 0 0 22px rgba(255,51,102,0.45); }

    .charts {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 24px;
    }
    .chart-box {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 24px;
    }
    .chart-box h2 {
      font-size: 13px;
      font-weight: 400;
      color: var(--text-secondary);
      margin-bottom: 20px;
    }
    .chart-box canvas { display: block; width: 100% !important; }

    .table-section {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }
    .table-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 18px 20px;
      border-bottom: 1px solid var(--border);
    }
    .table-header h2 {
      font-size: 13px;
      font-weight: 400;
      color: var(--text-secondary);
    }
    .table-hint { font-size: 12px; color: var(--text-muted); }

    .table-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; }
    thead th {
      padding: 10px 16px;
      text-align: left;
      font-size: 12px;
      font-weight: 400;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
      background: var(--surface);
    }
    th[data-sort] { cursor: pointer; user-select: none; }
    th[data-sort]:hover { color: var(--text-primary); }
    th[aria-sort="ascending"]::after  { content: " \2191"; opacity: 1; }
    th[aria-sort="descending"]::after { content: " \2193"; opacity: 1; }
    th[data-sort]::after { content: " \2195"; opacity: 0.3; }

    tbody tr {
      border-left: 3px solid transparent;
      transition: border-left-color 150ms ease-out, background 150ms ease-out;
    }
    tbody tr:nth-child(even) { background: var(--surface-raised); }
    tbody tr:hover {
      border-left-color: var(--accent);
      background: rgba(0,170,255,0.04);
    }
    tbody td {
      padding: 11px 16px;
      vertical-align: top;
      border-bottom: 1px solid var(--border-subtle);
    }
    tbody tr:last-child td { border-bottom: none; }
    .td-question { max-width: 320px; color: var(--text-primary); }
    .td-question-text { overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
    .td-category { color: var(--text-secondary); white-space: nowrap; }
    .td-score { white-space: nowrap; }
    .td-reasoning { color: var(--text-secondary); font-size: 12px; line-height: 1.6; max-width: 380px; }

    .badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 28px;
      height: 22px;
      padding: 0 7px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 500;
      font-variant-numeric: tabular-nums;
    }
    .badge-score-0 { background: var(--score-0-bg); color: var(--score-0-fg); }
    .badge-score-1 { background: var(--score-1-bg); color: var(--score-1-fg); }
    .badge-score-2 { background: var(--score-2-bg); color: var(--score-2-fg); }
    .badge-score-3 { background: var(--score-3-bg); color: var(--score-3-fg); }

    .badge-diff {
      display: inline-flex;
      align-items: center;
      height: 20px;
      padding: 0 7px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 400;
    }
    .badge-diff-easy   { background: var(--diff-easy-bg);   color: var(--diff-easy-fg); }
    .badge-diff-medium { background: var(--diff-medium-bg); color: var(--diff-medium-fg); }
    .badge-diff-hard   { background: var(--diff-hard-bg);   color: var(--diff-hard-fg); }

    @media (max-width: 900px) {
      .cards { grid-template-columns: repeat(2, 1fr); }
      .charts { grid-template-columns: 1fr; }
    }
    @media (max-width: 600px) {
      .cards { grid-template-columns: 1fr 1fr; }
      main { padding: 16px 16px 48px; }
      .topbar { padding: 0 16px; }
    }
  </style>
</head>
<body>

<header class="topbar" role="banner">
  <div class="topbar-left">
    <span class="topbar-title">Physical Reasoning Benchmark</span>
    <span class="topbar-model" id="topbarModel"></span>
  </div>
  <div class="topbar-right"></div>
</header>

<main>
  <div class="cards" role="region" aria-label="Summary metrics">
    <div class="card">
      <div class="card-label">Overall score</div>
      <div class="card-value" id="metricOverallPct"></div>
      <div class="card-sub" id="metricOverallAvg"></div>
    </div>
    <div class="card">
      <div class="card-label">Best category</div>
      <div class="card-value val-blue" id="metricBestPct"></div>
      <div class="card-sub" id="metricBestName"></div>
    </div>
    <div class="card">
      <div class="card-label">Worst category</div>
      <div class="card-value val-red" id="metricWorstPct"></div>
      <div class="card-sub" id="metricWorstName"></div>
    </div>
    <div class="card">
      <div class="card-label">Avg judge score</div>
      <div class="card-value" id="metricAvgScore"></div>
      <div class="card-sub">out of 3.00</div>
    </div>
  </div>

  <div class="charts" role="region" aria-label="Charts">
    <div class="chart-box">
      <h2>Accuracy by category</h2>
      <canvas id="categoryChart" aria-label="Horizontal bar chart of accuracy percentage per category"></canvas>
    </div>
    <div class="chart-box">
      <h2>Score distribution by difficulty</h2>
      <canvas id="difficultyChart" aria-label="Stacked bar chart of score distribution by difficulty"></canvas>
    </div>
  </div>

  <div class="table-section" role="region" aria-label="Results table">
    <div class="table-header">
      <h2>All results</h2>
      <span class="table-hint">Click column headers to sort</span>
    </div>
    <div class="table-wrap">
      <table id="resultsTable">
        <thead>
          <tr>
            <th scope="col">Question</th>
            <th scope="col" data-sort="category" aria-sort="none">Category</th>
            <th scope="col" data-sort="difficulty" aria-sort="none">Difficulty</th>
            <th scope="col" data-sort="score" aria-sort="none">Score</th>
            <th scope="col">Judge reasoning</th>
          </tr>
        </thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>
  </div>
</main>

<script>
  const DATA = __BENCHMARK_DATA__;

  Chart.defaults.color = 'rgba(255,255,255,0.45)';
  Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
  Chart.defaults.font.family = "system-ui, -apple-system, 'Segoe UI', sans-serif";
  Chart.defaults.font.size = 12;

  const SCORE_COLORS = ['#ff3366', '#f59e0b', '#00c8b4', '#00aaff'];
  const SCORE_LABELS = ['Score 0', 'Score 1', 'Score 2', 'Score 3'];

  function pctColor(pct) {
    if (pct >= 75) return '#00aaff';
    if (pct >= 50) return '#f59e0b';
    return '#ff3366';
  }

  function pctColorClass(pct) {
    if (pct >= 75) return 'val-blue';
    if (pct >= 50) return 'val-amber';
    return 'val-red';
  }

  function setText(id, text) {
    document.getElementById(id).textContent = text;
  }

  setText('topbarModel', DATA.model);

  const overallEl = document.getElementById('metricOverallPct');
  overallEl.textContent = DATA.overallPct + '%';
  overallEl.classList.add(pctColorClass(DATA.overallPct));
  setText('metricOverallAvg', DATA.overallAvg.toFixed(2) + ' avg score');

  setText('metricBestPct', DATA.bestCategory.pct + '%');
  setText('metricBestName', DATA.bestCategory.name);
  setText('metricWorstPct', DATA.worstCategory.pct + '%');
  setText('metricWorstName', DATA.worstCategory.name);

  const avgEl = document.getElementById('metricAvgScore');
  avgEl.textContent = DATA.overallAvg.toFixed(2);
  avgEl.classList.add(pctColorClass(DATA.overallPct));

  const catLabels = DATA.categories.map(c => c.name);
  const catPcts = DATA.categories.map(c => c.pct);
  const catColors = catPcts.map(p => pctColor(p));

  new Chart(document.getElementById('categoryChart'), {
    type: 'bar',
    data: {
      labels: catLabels,
      datasets: [{
        data: catPcts,
        backgroundColor: catColors,
        borderWidth: 0,
        borderRadius: 3,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ' ' + ctx.parsed.x.toFixed(1) + '%'
          }
        }
      },
      scales: {
        x: {
          min: 0,
          max: 100,
          ticks: { callback: v => v + '%' },
          grid: { color: 'rgba(255,255,255,0.06)' }
        },
        y: {
          grid: { display: false },
          ticks: { font: { size: 12 } }
        }
      }
    }
  });

  const diffLabels = DATA.difficultyDistribution.map(d => d.label);
  const diffDatasets = [0, 1, 2, 3].map(i => ({
    label: SCORE_LABELS[i],
    data: DATA.difficultyDistribution.map(d => d.counts[i]),
    backgroundColor: SCORE_COLORS[i],
    borderWidth: 0,
    borderRadius: i === 3 ? 3 : 0,
  }));

  new Chart(document.getElementById('difficultyChart'), {
    type: 'bar',
    data: { labels: diffLabels, datasets: diffDatasets },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { boxWidth: 12, padding: 16, font: { size: 12 }, color: 'rgba(255,255,255,0.55)' }
        },
        tooltip: { mode: 'index' }
      },
      scales: {
        x: { stacked: true, grid: { display: false } },
        y: {
          stacked: true,
          ticks: { stepSize: 1 },
          grid: { color: 'rgba(255,255,255,0.06)' }
        }
      }
    }
  });

  const DIFF_RANK = { easy: 0, medium: 1, hard: 2 };
  let sortCol = null;
  let sortDir = 1;
  let rows = [...DATA.rows];

  function renderTable() {
    const tbody = document.getElementById('tableBody');
    tbody.innerHTML = '';
    rows.forEach(r => {
      const tr = document.createElement('tr');

      const tdQ = document.createElement('td');
      tdQ.className = 'td-question';
      const qText = document.createElement('div');
      qText.className = 'td-question-text';
      qText.textContent = r.question;
      qText.title = r.question;
      tdQ.appendChild(qText);

      const tdCat = document.createElement('td');
      tdCat.className = 'td-category';
      tdCat.textContent = r.category;

      const tdDiff = document.createElement('td');
      const diffBadge = document.createElement('span');
      diffBadge.className = 'badge badge-diff badge-diff-' + r.difficulty.toLowerCase();
      diffBadge.textContent = r.difficulty;
      tdDiff.appendChild(diffBadge);

      const tdScore = document.createElement('td');
      tdScore.className = 'td-score';
      const scoreBadge = document.createElement('span');
      scoreBadge.className = 'badge badge-score-' + r.score;
      scoreBadge.textContent = r.score;
      scoreBadge.setAttribute('aria-label', 'Score ' + r.score + ' out of 3');
      tdScore.appendChild(scoreBadge);

      const tdReason = document.createElement('td');
      tdReason.className = 'td-reasoning';
      tdReason.textContent = r.reasoning;

      tr.append(tdQ, tdCat, tdDiff, tdScore, tdReason);
      tbody.appendChild(tr);
    });
  }

  function sortBy(col) {
    document.querySelectorAll('th[data-sort]').forEach(th => th.setAttribute('aria-sort', 'none'));

    if (sortCol === col) {
      sortDir *= -1;
    } else {
      sortCol = col;
      sortDir = 1;
    }

    document.querySelector('th[data-sort="' + col + '"]')
      .setAttribute('aria-sort', sortDir === 1 ? 'ascending' : 'descending');

    rows.sort((a, b) => {
      if (col === 'score') return (a[col] - b[col]) * sortDir;
      if (col === 'difficulty') return (DIFF_RANK[a[col].toLowerCase()] - DIFF_RANK[b[col].toLowerCase()]) * sortDir;
      return a[col].localeCompare(b[col]) * sortDir;
    });

    renderTable();
  }

  document.querySelectorAll('th[data-sort]').forEach(th => {
    th.addEventListener('click', () => sortBy(th.dataset.sort));
  });

  renderTable();
</script>
</body>
</html>
"""


def compute_payload(run_data: dict, run_timestamp: str) -> dict:
    results = run_data["results"]
    model = run_data.get("model", "unknown")

    scores = [r["score"] for r in results]
    overall_avg = sum(scores) / len(scores)

    cat_buckets: dict[str, list[int]] = {}
    diff_buckets: dict[str, list[int]] = {}
    for r in results:
        cat_buckets.setdefault(r["category"], []).append(r["score"])
        diff_buckets.setdefault(r["difficulty"].lower(), []).append(r["score"])

    cat_avgs = {c: sum(s) / len(s) for c, s in cat_buckets.items()}
    best_cat = max(cat_avgs, key=cat_avgs.__getitem__)
    worst_cat = min(cat_avgs, key=cat_avgs.__getitem__)

    categories = [
        {
            "name": c,
            "avg": round(sum(s) / len(s), 2),
            "pct": round(sum(s) / len(s) / 3 * 100, 1),
            "count": len(s),
        }
        for c, s in sorted(cat_buckets.items())
    ]

    diff_dist = [
        {
            "label": d.capitalize(),
            "counts": [sum(1 for x in diff_buckets[d] if x == i) for i in range(4)],
        }
        for d in DIFF_ORDER
        if d in diff_buckets
    ]

    rows = [
        {
            "id": r["id"],
            "question": r["question"],
            "category": r["category"],
            "difficulty": r["difficulty"].capitalize(),
            "score": r["score"],
            "reasoning": r.get("judge_reasoning", ""),
        }
        for r in results
    ]

    return {
        "model": model,
        "timestamp": run_timestamp,
        "totalQuestions": len(results),
        "overallAvg": round(overall_avg, 2),
        "overallPct": round(overall_avg / 3 * 100, 1),
        "bestCategory": {"name": best_cat, "pct": round(cat_avgs[best_cat] / 3 * 100, 1)},
        "worstCategory": {"name": worst_cat, "pct": round(cat_avgs[worst_cat] / 3 * 100, 1)},
        "categories": categories,
        "difficultyDistribution": diff_dist,
        "rows": rows,
    }


def parse_run_timestamp(filename: str) -> str:
    match = re.search(r"(\d{8}_\d{6})", filename)
    if match:
        return datetime.strptime(match.group(1), "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def build(scored_path: Path) -> Path:
    with open(scored_path, encoding="utf-8") as f:
        run_data = json.load(f)

    if not run_data.get("results") or "score" not in run_data["results"][0]:
        print(f"Error: {scored_path.name} does not appear to be a scored results file.")
        sys.exit(1)

    run_timestamp = parse_run_timestamp(scored_path.name)
    payload = compute_payload(run_data, run_timestamp)
    html = HTML_TEMPLATE.replace("__BENCHMARK_DATA__", json.dumps(payload, ensure_ascii=False))

    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"dashboard_{timestamp}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    webbrowser.open(output_path.resolve().as_uri())
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate an HTML dashboard from a scored benchmark run")
    parser.add_argument("scored_file", type=Path, help="Path to results/scored_run_*.json file")
    args = parser.parse_args()

    if not args.scored_file.exists():
        print(f"Error: file not found: {args.scored_file}")
        sys.exit(1)

    output_path = build(args.scored_file)
    print(f"Dashboard saved to {output_path}")


if __name__ == "__main__":
    main()
