#!/usr/bin/env python3
"""
Phase 1-1: Input format conversion for Quality Inspection.
Normalizes xlsx/csv input files into CSV intermediate format.
"""

import argparse
import csv
import subprocess
import sys
from pathlib import Path


def convert_file(input_path: Path, output_path: Path) -> bool:
    """Convert a single input file to CSV intermediate format."""
    suffix = input_path.suffix.lower()
    print(f"[CONVERT] {input_path.name} -> {output_path.name}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if suffix == ".csv":
        # CSV: copy as-is
        content = input_path.read_text(encoding="utf-8")
        output_path.write_text(content, encoding="utf-8")
        print(f"  [OK] CSV copied: {output_path}")
        return True

    elif suffix == ".xlsx":
        # XLSX: convert via markitdown to markdown, then extract tables
        try:
            result = subprocess.run(
                ["markitdown", str(input_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            # Parse markdown tables into CSV
            rows = []
            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    cells = [c.strip() for c in line.split("|")[1:-1]]
                    if cells and not all(c.startswith("-") for c in cells):
                        rows.append(cells)

            with open(output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                for row in rows:
                    writer.writerow(row)

            print(f"  [OK] XLSX converted: {output_path} ({len(rows)} rows)")
            return True
        except FileNotFoundError:
            print("  [ERROR] markitdown not found. Install: pip install markitdown")
            return False
        except subprocess.CalledProcessError as e:
            print(f"  [ERROR] Conversion failed: {e.stderr}")
            return False
    else:
        print(f"  [ERROR] Unsupported format: {suffix}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Quality Inspection - Input Conversion (Phase 1-1)"
    )
    parser.add_argument(
        "--measurements",
        required=True,
        help="검사 측정 데이터 파일 경로 (.csv / .xlsx)",
    )
    parser.add_argument(
        "--specifications",
        required=True,
        help="사양 기준서 파일 경로 (.csv / .xlsx)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        required=True,
        help="변환 파일 출력 디렉토리",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="기존 파일 덮어쓰기",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    success = True

    # Convert measurements
    meas_path = Path(args.measurements).resolve()
    if not meas_path.exists():
        print(f"[ERROR] File not found: {meas_path}")
        sys.exit(1)

    meas_out = output_dir / "measurements.csv"
    if meas_out.exists() and not args.force:
        print(f"[SKIP] Already exists: {meas_out}")
    else:
        if not convert_file(meas_path, meas_out):
            success = False

    # Convert specifications
    spec_path = Path(args.specifications).resolve()
    if not spec_path.exists():
        print(f"[ERROR] File not found: {spec_path}")
        sys.exit(1)

    spec_out = output_dir / "specifications.csv"
    if spec_out.exists() and not args.force:
        print(f"[SKIP] Already exists: {spec_out}")
    else:
        if not convert_file(spec_path, spec_out):
            success = False

    if not success:
        sys.exit(1)

    print(f"\n[OK] Conversion complete: {output_dir}")


if __name__ == "__main__":
    main()
