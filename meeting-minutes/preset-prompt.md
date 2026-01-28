---
name: meeting-minutes-auto
description: "Automated execution preset for Meeting Minutes Processor"
---

# Meeting Minutes Processor - AIP Preset Prompt

## Execution Mode

This preset enables automated execution of the Meeting Minutes Processor pipeline.

## Auto-Execution Flow

1. **Validate Input**: Check meeting notes file exists
2. **Phase 1-1 - Conversion**: Run `scripts/convert.py` to convert input to markdown
3. **Phase 1-2 - Extraction**: Run `scripts/extract.py` to extract structured data
4. **Phase 2 - Judgment**: LLM reads `raw_data.json` and applies judgment logic per SKILL.md Phase 2 instructions
5. **Phase 3 - Generation**: Run `scripts/generate.py` to produce final reports

## Input Requirements

- **회의록 (Meeting Notes)**: 회의 녹취록 또는 메모 (`.txt` / `.docx`)
- **프로젝트 트래커 (선택)**: 기존 액션 아이템 목록 (`.json`)

## Expected Output

- `action_report.json` - 구조화된 액션 아이템 보고서
- `action_report.md` - Markdown 보고서

## Error Handling

- If input file not found, report path and stop
- If markitdown not installed (for .docx), report installation command
- If extraction produces empty data, flag for manual review
- If LLM judgment is uncertain, mark items with "low confidence" flag
- If generation fails, save intermediate data for debugging

## Quality Checks

After generation, verify:
- [ ] action_report.json is valid JSON and non-empty
- [ ] action_report.md is readable and well-formatted
- [ ] All explicitly marked action items are captured
- [ ] Attendees list matches meeting notes
- [ ] Statistics counts are consistent
