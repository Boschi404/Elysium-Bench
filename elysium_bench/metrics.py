"""Improvement metrics — measures Elysium's self-learning claims."""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any

from .scoring import ScoreBreakdown


@dataclass
class ImprovementMetrics:
    """Captures learning/improvement signals across a benchmark run."""

    category: str

    # Scores from the improvement loop
    task1_first_score: ScoreBreakdown | None = None
    task1_rerun_score: ScoreBreakdown | None = None
    sequence_scores: list[ScoreBreakdown] = field(default_factory=list)  # tasks 2-N

    # Computed metrics
    delta_absolute: float = 0.0
    delta_percent: float = 0.0
    learning_rate: float = 0.0  # delta / first_score × 100
    transfer_efficiency: float = 0.0  # mean(sequence) / first_score
    stability: float = 0.0  # 1 - std/mean for sequence
    convergence_speed: int = 0  # tasks until plateau (score stabilizes within 5%)
    learning_detected: bool = False

    def compute(self, learning_threshold: float = 5.0) -> "ImprovementMetrics":
        """Compute all improvement metrics from collected scores."""
        if self.task1_first_score and self.task1_rerun_score:
            first = self.task1_first_score.total
            rerun = self.task1_rerun_score.total

            self.delta_absolute = rerun - first
            self.delta_percent = (self.delta_absolute / first * 100) if first > 0 else 0.0
            self.learning_rate = self.delta_percent
            self.learning_detected = self.learning_rate >= learning_threshold

        if self.sequence_scores and self.task1_first_score:
            seq_totals = [s.total for s in self.sequence_scores]
            mean_seq = statistics.mean(seq_totals) if seq_totals else 0.0
            first = self.task1_first_score.total

            self.transfer_efficiency = (mean_seq / first) if first > 0 else 0.0

            if len(seq_totals) > 1:
                std = statistics.stdev(seq_totals)
                self.stability = max(0.0, 1.0 - (std / mean_seq)) if mean_seq > 0 else 0.0

            # Convergence speed: find first point where score stabilizes
            self.convergence_speed = self._find_convergence(seq_totals)

        return self

    @staticmethod
    def _find_convergence(scores: list[float], threshold: float = 0.05) -> int:
        """Find how many tasks until scores stabilize within threshold%."""
        if len(scores) < 3:
            return len(scores)

        for i in range(2, len(scores)):
            window = scores[max(0, i - 2) : i + 1]
            mean = statistics.mean(window)
            if mean > 0:
                variation = max(abs(s - mean) / mean for s in window)
                if variation <= threshold:
                    return i + 1

        return len(scores)

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "task1_first": self.task1_first_score.to_dict() if self.task1_first_score else None,
            "task1_rerun": self.task1_rerun_score.to_dict() if self.task1_rerun_score else None,
            "sequence_scores": [s.to_dict() for s in self.sequence_scores],
            "delta_absolute": self.delta_absolute,
            "delta_percent": round(self.delta_percent, 2),
            "learning_rate": round(self.learning_rate, 2),
            "transfer_efficiency": round(self.transfer_efficiency, 2),
            "stability": round(self.stability, 2),
            "convergence_speed": self.convergence_speed,
            "learning_detected": self.learning_detected,
        }

    def summary(self) -> str:
        """Human-readable summary."""
        lines = [
            f"📈 Improvement Metrics — {self.category}",
            f"   Task 1 first run:  {self.task1_first_score.total:.1f}/100" if self.task1_first_score else "",
            f"   Task 1 re-run:     {self.task1_rerun_score.total:.1f}/100" if self.task1_rerun_score else "",
        ]
        if self.task1_first_score and self.task1_rerun_score:
            direction = "📈" if self.delta_absolute > 0 else "📉" if self.delta_absolute < 0 else "➡️"
            lines.append(f"   Δ Score:           {direction} {self.delta_absolute:+.1f} ({self.delta_percent:+.1f}%)")
        lines.append(f"   Transfer Efficiency: {self.transfer_efficiency:.2f}")
        lines.append(f"   Stability:           {self.stability:.2f}")
        lines.append(f"   Convergence:         {self.convergence_speed} tasks")
        lines.append(f"   Learning Detected:   {'✅ YES' if self.learning_detected else '❌ NO'}")
        return "\n".join(lines)
