"""HTML/CSS report generator for Elysium-Bench results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def generate_html_report(report: dict[str, Any], output_path: Path) -> str:
    """Generate a standalone HTML dashboard from benchmark results."""
    categories = report.get("categories", {})

    # Build category rows
    rows_html = ""
    for cat_id, data in categories.items():
        t1 = data.get("task1_first", {}) or {}
        t1r = data.get("task1_rerun", {}) or {}
        first = t1.get("total", 0)
        rerun = t1r.get("total", 0)
        delta = data.get("delta_absolute", 0)
        learning = "✅" if data.get("learning_detected") else "❌"
        transfer = data.get("transfer_efficiency", 0)
        stability = data.get("stability", 0)

        delta_class = "positive" if delta > 0 else "negative" if delta < 0 else "neutral"
        delta_sign = "+" if delta > 0 else ""

        rows_html += f"""
        <tr>
            <td class="cat-name">{cat_id}</td>
            <td>{first:.1f}</td>
            <td>{rerun:.1f}</td>
            <td class="{delta_class}">{delta_sign}{delta:.1f}</td>
            <td>{learning}</td>
            <td>{transfer:.2f}</td>
            <td>{stability:.2f}</td>
        </tr>"""

    # Score bar
    overall = report.get("overall_score", 0)
    bar_color = "#22c55e" if overall >= 85 else "#eab308" if overall >= 60 else "#ef4444"
    bar_width = min(overall, 100)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Elysium-Bench Results</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        .header {{ margin-bottom: 2rem; }}
        .meta {{ color: #94a3b8; font-size: 0.9rem; }}
        .score-card {{
            background: #1e293b;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            text-align: center;
        }}
        .score-value {{ font-size: 4rem; font-weight: 700; color: {bar_color}; }}
        .score-bar {{
            height: 12px;
            background: #334155;
            border-radius: 6px;
            margin: 1rem auto;
            max-width: 400px;
            overflow: hidden;
        }}
        .score-bar-fill {{
            height: 100%;
            width: {bar_width}%;
            background: {bar_color};
            border-radius: 6px;
            transition: width 0.5s ease;
        }}
        .improvement {{
            font-size: 1.2rem;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            display: inline-block;
            margin-top: 1rem;
        }}
        .improvement.yes {{ background: #064e3b; color: #4ade80; }}
        .improvement.no {{ background: #451a03; color: #fbbf24; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #1e293b;
            border-radius: 12px;
            overflow: hidden;
        }}
        th {{
            text-align: left;
            padding: 1rem;
            background: #334155;
            color: #94a3b8;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        td {{
            padding: 0.75rem 1rem;
            border-top: 1px solid #334155;
        }}
        .cat-name {{ color: #67e8f9; font-weight: 600; }}
        .positive {{ color: #4ade80; font-weight: 600; }}
        .negative {{ color: #f87171; font-weight: 600; }}
        .neutral {{ color: #94a3b8; }}
        .methodology {{
            margin-top: 2rem;
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
        }}
        .methodology h2 {{ margin-bottom: 0.5rem; }}
        .methodology ul {{ list-style: disc inside; color: #94a3b8; line-height: 1.8; }}
        footer {{
            margin-top: 2rem;
            text-align: center;
            color: #475569;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Elysium-Bench Results</h1>
        <p class="meta">Version {report.get('version', '?')} · {report.get('timestamp', '?')}</p>
    </div>

    <div class="score-card">
        <div class="score-value">{overall:.0f}<span style="font-size:1.5rem;color:#94a3b8">/100</span></div>
        <div class="score-bar"><div class="score-bar-fill"></div></div>
        <div class="improvement {'yes' if report.get('improvement_detected') else 'no'}">
            {'✅ Improvement Detected' if report.get('improvement_detected') else '❌ No Improvement Detected'}
        </div>
    </div>

    <h2 style="margin-bottom: 1rem;">📊 Category Breakdown</h2>
    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>Task 1 First</th>
                <th>Task 1 Re-run</th>
                <th>Δ Score</th>
                <th>Learning?</th>
                <th>Transfer Eff.</th>
                <th>Stability</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <div class="methodology">
        <h2>📐 Methodology</h2>
        <ul>
            <li><strong>Scoring:</strong> Functional Correctness (40) + Code Quality (25) + Efficiency (15) + Robustness (10) + Integration (10) = 100</li>
            <li><strong>Improvement Loop:</strong> Task 1 → Tasks 2-10 → Task 1 re-run → Compare delta</li>
            <li><strong>Pass Threshold:</strong> ≥ 60/100</li>
            <li><strong>Learning Threshold:</strong> ≥ 5% improvement on re-run</li>
        </ul>
    </div>

    <footer>
        Elysium-Bench · Multi-Agent Self-Improvement Benchmark · v{report.get('version', '0.1.0')}
    </footer>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    return str(output_path)
