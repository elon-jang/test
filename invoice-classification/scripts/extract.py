#!/usr/bin/env python3
"""
Phase 1-2: Data extraction & pre-classification for Invoice Classification.
Applies mapping table for category hints, detects policy flags.

★ Mapping Table: config의 gl_accounts에서 keywords → category 매칭
★ Decision Tree: policy 규칙 기반 초기 flag 분류 (NONE/OVER_LIMIT/DUPLICATE_SUSPECT/OUTLIER)
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml


def load_config(config_path: Path) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def match_category(vendor: str, description: str, gl_accounts: dict) -> tuple:
    """
    ★ Mapping Table lookup: keywords → category + GL code.
    Returns (category, gl_code).
    """
    text = (vendor + " " + description).lower()
    for category, info in gl_accounts.items():
        for keyword in info.get("keywords", []):
            if keyword.lower() in text:
                return category, info["code"]
    return "기타", gl_accounts.get("기타", {}).get("code", "GL-5900")


def detect_policy_flags(items: list, policy: dict) -> list:
    """
    ★ Decision Tree: initial policy flag classification.

    NONE          → 한도 내, 이상 없음
    OVER_LIMIT    → 카테고리별 한도 초과
    DUPLICATE_SUSPECT → 동일 날짜 + 동일 금액
    OUTLIER       → 카테고리 평균 대비 N배 초과
    """
    limits = policy.get("limits", {})
    outlier_mult = policy.get("outlier_multiplier", 3.0)

    # Compute per-category averages for outlier detection
    cat_amounts = defaultdict(list)
    for item in items:
        cat_amounts[item["category_hint"]].append(item["amount"])

    cat_avg = {}
    for cat, amounts in cat_amounts.items():
        cat_avg[cat] = sum(amounts) / len(amounts) if amounts else 0

    # Detect duplicates: same date + same amount
    date_amount_map = defaultdict(list)
    for item in items:
        key = (item["date"], item["amount"])
        date_amount_map[key].append(item["id"])

    duplicate_ids = set()
    for key, ids in date_amount_map.items():
        if len(ids) > 1:
            duplicate_ids.update(ids)

    # Apply decision tree
    for item in items:
        flags = []
        cat = item["category_hint"]
        amount = item["amount"]

        # Branch 1: Over limit?
        limit = limits.get(cat, limits.get("기타", 100000))
        if amount > limit:
            flags.append("OVER_LIMIT")

        # Branch 2: Duplicate suspect?
        if item["id"] in duplicate_ids:
            flags.append("DUPLICATE_SUSPECT")

        # Branch 3: Outlier?
        avg = cat_avg.get(cat, 0)
        if avg > 0 and amount > avg * outlier_mult:
            flags.append("OUTLIER")

        # Set primary flag (priority: OUTLIER > DUPLICATE > OVER_LIMIT > NONE)
        if "OUTLIER" in flags:
            item["policy_flag"] = "OUTLIER"
        elif "DUPLICATE_SUSPECT" in flags:
            item["policy_flag"] = "DUPLICATE_SUSPECT"
        elif "OVER_LIMIT" in flags:
            item["policy_flag"] = "OVER_LIMIT"
        else:
            item["policy_flag"] = "NONE"

        item["all_flags"] = flags

    return items


def main():
    parser = argparse.ArgumentParser(
        description="Invoice Classification - Extraction & Pre-classification (Phase 1-2)"
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
    gl_accounts = config["gl_accounts"]
    policy = config["policy"]

    print(f"\n=== Extraction & Pre-classification ===\n")

    items = data["items"]

    # Step 1: Mapping Table → category + GL code hints
    for item in items:
        cat, gl_code = match_category(item["vendor"], item["description"], gl_accounts)
        item["category_hint"] = cat
        item["gl_code_hint"] = gl_code

    # Step 2: Decision Tree → policy flags
    items = detect_policy_flags(items, policy)

    # Statistics
    cat_counts = Counter(item["category_hint"] for item in items)
    flag_counts = Counter(item["policy_flag"] for item in items)
    total_amount = sum(item["amount"] for item in items)

    print(f"  Items: {len(items)}")
    print(f"  Total: {total_amount:,}원")
    print(f"  Categories: {dict(cat_counts)}")
    print(f"  Flags: {dict(flag_counts)}")

    output = {
        "meta": {
            "total_items": len(items),
            "total_amount": total_amount,
        },
        "items": items,
    }

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n  [OK] {output_path}")


if __name__ == "__main__":
    main()
