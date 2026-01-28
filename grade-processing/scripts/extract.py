#!/usr/bin/env python3
"""
Phase 1-2: Data extraction & scoring for Grade Processing.
Calculates weighted scores, assigns letter grades, identifies at-risk students.
"""

import argparse
import json
import sys
from pathlib import Path

import yaml


def load_config(config_path: Path) -> dict:
    """Load settings.yaml."""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def compute_weighted_score(student: dict, weights: dict) -> float:
    """Compute weighted total score."""
    midterm = student["midterm"] * weights["midterm"] / 100
    final = student["final"] * weights["final"] / 100
    assignments = student.get("assignments", [])
    assignment_avg = sum(assignments) / len(assignments) if assignments else 0
    assignment_score = assignment_avg * weights["assignments"] / 100
    attendance = student["attendance_pct"] * weights["attendance"] / 100
    return round(midterm + final + assignment_score + attendance, 1)


def assign_grade(score: float, scale: list) -> str:
    """Assign letter grade based on score and scale."""
    for entry in scale:
        if score >= entry["min"]:
            return entry["grade"]
    return "F"


def main():
    parser = argparse.ArgumentParser(
        description="Grade Processing - Extraction & Scoring (Phase 1-2)"
    )
    parser.add_argument("--raw-data", required=True, help="변환된 JSON (raw_data.json)")
    parser.add_argument("--config", required=True, help="설정 파일 (settings.yaml)")
    parser.add_argument("--output", "-o", required=True, help="출력 JSON 파일")
    args = parser.parse_args()

    raw_path = Path(args.raw_data).resolve()
    config_path = Path(args.config).resolve()

    if not raw_path.exists():
        print(f"[ERROR] File not found: {raw_path}")
        sys.exit(1)

    with open(raw_path, encoding="utf-8") as f:
        data = json.load(f)

    config = load_config(config_path)
    weights = config["weights"]
    scale = config["grade_scale"]
    thresholds = config["thresholds"]

    print(f"\n=== Extraction & Scoring ===\n")

    students = data["students"]
    results = []
    at_risk = []

    for s in students:
        assignments = s.get("assignments", [])
        assignment_avg = round(sum(assignments) / len(assignments), 1) if assignments else 0
        total = compute_weighted_score(s, weights)
        grade = assign_grade(total, scale)

        record = {
            "student_id": s["student_id"],
            "name": s["name"],
            "midterm": s["midterm"],
            "final": s["final"],
            "assignment_avg": assignment_avg,
            "attendance_pct": s["attendance_pct"],
            "total_score": total,
            "grade": grade,
        }
        results.append(record)

        # At-risk detection
        issues = []
        if total < thresholds["at_risk_score"]:
            issues.append("총점 미달")
        if s["attendance_pct"] < thresholds["attendance_warning"]:
            issues.append("출석 부족")
        if s["final"] < s["midterm"] - 15:
            issues.append("기말 성적 급락")

        if issues:
            at_risk.append({
                **record,
                "issues": issues,
            })

    # Class statistics
    scores = [r["total_score"] for r in results]
    from collections import Counter
    grade_dist = Counter(r["grade"] for r in results)

    stats = {
        "student_count": len(results),
        "score_avg": round(sum(scores) / len(scores), 1),
        "score_max": max(scores),
        "score_min": min(scores),
        "at_risk_count": len(at_risk),
        "grade_distribution": dict(grade_dist),
        "attendance_avg": round(
            sum(r["attendance_pct"] for r in results) / len(results), 1
        ),
    }

    output = {
        "meta": {
            "student_count": len(results),
            "at_risk_count": len(at_risk),
        },
        "results": results,
        "at_risk": at_risk,
        "statistics": stats,
    }

    print(f"  Students: {len(results)}")
    print(f"  Average: {stats['score_avg']}")
    print(f"  At-risk: {len(at_risk)}")
    print(f"  Grades: {dict(grade_dist)}")

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n  [OK] {output_path}")


if __name__ == "__main__":
    main()
