#!/usr/bin/env python3
"""
Phase 1-1: Input format conversion for Meeting Minutes Processor.
Converts txt/docx meeting notes to markdown intermediate format.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def convert_file(input_path: Path, output_path: Path) -> bool:
    """Convert a single input file to markdown intermediate format."""
    suffix = input_path.suffix.lower()
    print(f"[CONVERT] {input_path.name} -> {output_path.name}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if suffix == ".txt":
        # Plain text: copy as-is (already readable)
        content = input_path.read_text(encoding="utf-8")
        output_path.write_text(content, encoding="utf-8")
        print(f"  [OK] Text copied: {output_path}")
        return True

    elif suffix == ".docx":
        # DOCX: convert via markitdown
        try:
            result = subprocess.run(
                ["markitdown", str(input_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            output_path.write_text(result.stdout, encoding="utf-8")
            print(f"  [OK] DOCX converted: {output_path}")
            return True
        except FileNotFoundError:
            print("  [ERROR] markitdown not found. Install: pip install markitdown")
            return False
        except subprocess.CalledProcessError as e:
            print(f"  [ERROR] Conversion failed: {e.stderr}")
            return False

    elif suffix == ".md":
        # Markdown: copy as-is
        content = input_path.read_text(encoding="utf-8")
        output_path.write_text(content, encoding="utf-8")
        print(f"  [OK] Markdown copied: {output_path}")
        return True

    else:
        print(f"  [ERROR] Unsupported format: {suffix}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Meeting Minutes Processor - Input Conversion (Phase 1-1)"
    )
    parser.add_argument(
        "--meeting-notes",
        required=True,
        help="회의록 파일 경로 (.txt / .docx)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        required=True,
        help="변환 파일 출력 디렉토리",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="기존 파일 덮어쓰기",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    input_path = Path(args.meeting_notes).resolve()
    if not input_path.exists():
        print(f"[ERROR] File not found: {input_path}")
        sys.exit(1)

    output_path = output_dir / "meeting_notes.md"
    if output_path.exists() and not args.force:
        print(f"[SKIP] Already exists: {output_path}")
    else:
        if not convert_file(input_path, output_path):
            sys.exit(1)

    print(f"\n[OK] Conversion complete: {output_dir}")


if __name__ == "__main__":
    main()
