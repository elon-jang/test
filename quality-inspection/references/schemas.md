# Quality Inspection - Data Schemas

## Schema A: LLM Output (judged_data.json)

```json
{
  "meta": {
    "inspection_date": "YYYY-MM-DD",
    "total_parts": 0,
    "total_measurements": 0,
    "processing_date": "ISO 8601"
  },
  "results": [
    {
      "part_id": "string",
      "part_name": "string",
      "category": "mechanical | electrical | safety",
      "measurement_type": "string",
      "measured_value": 0.0,
      "unit": "string",
      "spec_min": 0.0,
      "spec_max": 0.0,
      "critical": true,
      "margin_pct": 0.0,
      "initial_class": "PASS | BORDERLINE | FAIL",
      "final_result": "PASS | CONDITIONAL PASS | FAIL",
      "rationale": "string (LLM 판단 근거)",
      "defect_code": "string | null",
      "corrective_action": "string | null",
      "priority": "critical | high | medium | low | null"
    }
  ],
  "system_issues": [
    {
      "description": "string",
      "affected_parts": ["string"],
      "suggested_investigation": "string"
    }
  ],
  "summary": {
    "overall_assessment": "string",
    "pass_rate": 0.0,
    "key_findings": ["string"],
    "recommended_actions": ["string"]
  }
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `initial_class` | string | Script가 계산한 초기 분류 (PASS/BORDERLINE/FAIL) |
| `final_result` | string | LLM이 최종 판정한 결과 (PASS/CONDITIONAL PASS/FAIL) |
| `rationale` | string | LLM의 판단 근거 (한국어) |
| `defect_code` | string | FAIL 시 결함 코드 (config/settings.yaml 참조) |
| `corrective_action` | string | FAIL 시 시정 조치 내용 |
| `priority` | string | 시정 조치 우선순위 (critical/high/medium/low) |
| `system_issues` | array | 동일 부품 복수 항목 경계/불합격 시 시스템 이슈 |

---

## Schema B: Intermediate Data (raw_data.json)

extract.py가 생성하는 중간 데이터입니다.

```json
{
  "meta": {
    "measurements_file": "string",
    "specifications_file": "string",
    "extraction_timestamp": "ISO 8601"
  },
  "items": [
    {
      "part_id": "string",
      "part_name": "string",
      "category": "string",
      "measurement_type": "string",
      "measured_value": 0.0,
      "unit": "string",
      "spec_min": 0.0,
      "spec_max": 0.0,
      "critical": true,
      "margin_pct": 0.0,
      "initial_class": "PASS | BORDERLINE | FAIL",
      "inspector": "string",
      "date": "string"
    }
  ],
  "parts_summary": {
    "part_id": {
      "part_name": "string",
      "category": "string",
      "measurement_count": 0,
      "all_items_indices": [0]
    }
  }
}
```

---

## Schema C: Final Report (inspection_report.json)

```json
{
  "meta": {},
  "results": [],
  "system_issues": [],
  "summary": {},
  "statistics": {
    "total_measurements": 0,
    "pass_count": 0,
    "conditional_pass_count": 0,
    "fail_count": 0,
    "pass_rate_pct": 0.0,
    "by_category": {},
    "by_defect_code": {},
    "by_priority": {}
  }
}
```
