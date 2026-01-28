---
name: quality-inspection-auto
description: "Automated execution preset for Quality Inspection Report"
---

# Quality Inspection Report - AIP Preset Prompt

## Execution Mode

This preset enables automated execution of the Quality Inspection pipeline.

## Auto-Execution Flow

1. **Validate Input**: Check measurement and specification files exist
2. **Phase 1-1 - Conversion**: Run `scripts/convert.py` with provided files
3. **Phase 1-2 - Extraction**: Run `scripts/extract.py` to join data and compute margins
4. **Phase 2 - Judgment**: Apply Decision Tree (SKILL.md) with Mapping Table (config) and Before/After examples (references/examples.md)
5. **Phase 3 - Generation**: Run `scripts/generate.py` to produce final report

## Phase 2 Judgment Instructions

When performing LLM judgment on `raw_data.json`:

1. Read `config/settings.yaml` for Mapping Tables (defect codes per category)
2. Read `references/examples.md` for Before/After judgment examples
3. Follow the Decision Tree in SKILL.md:
   - PASS items: confirm with brief note
   - BORDERLINE items: check critical flag → check related measurements → judge
   - FAIL items: classify root cause using Mapping Table
4. Detect system issues (same part with multiple borderline/fail)
5. Output `judged_data.json` per references/schemas.md Schema A

## Input Requirements

- **검사 측정 데이터 (Measurements)**: 부품별 측정값 (`.csv` / `.xlsx`)
- **사양 기준서 (Specifications)**: 부품별 규격 범위 (`.csv` / `.xlsx`)

## Expected Output

- `inspection_report.json` - 구조화된 품질 검사 보고서
- `inspection_report.md` - Markdown 보고서

## Error Handling

- If input files not found, report paths and stop
- If measurement has no matching specification, flag as "UNMATCHED" for manual review
- If margin computation fails, log warning and skip item
- If LLM judgment is uncertain on root cause, choose most likely and note "low confidence"

## Quality Checks

After generation, verify:
- [ ] All measurements from input are present in output
- [ ] BORDERLINE + critical=true → always FAIL
- [ ] FAIL items have defect_code assigned
- [ ] System issues detected for parts with multiple failures
- [ ] Statistics totals match item counts
