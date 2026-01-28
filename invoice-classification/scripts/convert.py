#!/usr/bin/env python3
"""
Phase 1-1: Input conversion for Invoice Classification.
Converts expenses CSV/XLSX to standardized JSON.
"""

import argparse
import csv
import json
import sys
from pathlib import Path


def parse_csv(path: Path) -> list:
    """Parse expenses CSV file."""
    records = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                "id": row["id"].strip(),
                "date": row["date"].strip(),
                "vendor": row["vendor"].strip(),
                "description": row["description"].strip(),
                "amount": int(row["amount"]),
            })
    return records


def main():
    parser = argparse.ArgumentParser(
        description="Invoice Classification - Input Conversion (Phase 1-1)"
    )
    parser.add_argument("--input", "-i", required=True, help="입력 파일 (CSV/XLSX)")
    parser.add_argument("--output", "-o", required=True, help="출력 JSON 파일")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"[ERROR] File not found: {input_path}")
        sys.exit(1)

    print(f"\n=== Input Conversion ===\n")

    if input_path.suffix.lower() == ".csv":
        records = parse_csv(input_path)
    else:
        print(f"[ERROR] Unsupported format: {input_path.suffix}")
        sys.exit(1)

    total_amount = sum(r["amount"] for r in records)
    print(f"  Items: {len(records)}")
    print(f"  Total: {total_amount:,}원")

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"items": records}, f, ensure_ascii=False, indent=2)

    print(f"  [OK] {output_path}")


if __name__ == "__main__":
    main()
