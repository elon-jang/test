# Meeting Minutes Processor - Data Schemas

## Schema A: LLM Output (judged_data.json)

LLM이 Phase 2에서 생성해야 하는 출력 포맷입니다.

```json
{
  "meta": {
    "meeting_title": "string",
    "meeting_date": "YYYY-MM-DD",
    "attendees": ["string"],
    "processing_date": "ISO 8601 datetime"
  },
  "summary": "string (회의 전체 요약, 2-3문장)",
  "decisions": [
    {
      "id": "D-001",
      "content": "string (의사결정 내용)",
      "context": "string (배경/근거)"
    }
  ],
  "action_items": [
    {
      "id": "A-001",
      "title": "string (액션 아이템 제목)",
      "description": "string (상세 설명)",
      "owner": "string (담당자)",
      "priority": "high | medium | low",
      "category": "development | design | review | research | admin",
      "due_date": "YYYY-MM-DD | null",
      "source": "explicit | implicit",
      "original_text": "string (원문에서 관련 부분)"
    }
  ],
  "unresolved": [
    {
      "id": "U-001",
      "topic": "string (미결 주제)",
      "context": "string (토론 내용 요약)",
      "suggested_next": "string (다음 단계 제안)"
    }
  ],
  "tracker_updates": [
    {
      "tracker_id": "string (기존 트래커 ID)",
      "status_update": "string (상태 변경 내용)",
      "mentioned_by": "string (언급자)"
    }
  ]
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `meeting_title` | string | 회의 제목 |
| `meeting_date` | string | 회의 일자 (YYYY-MM-DD) |
| `attendees` | array | 참석자 이름 목록 |
| `summary` | string | 회의 전체 요약 (2-3문장) |
| `decisions[].content` | string | 의사결정 내용 |
| `action_items[].source` | string | `explicit` = 명시적 기재, `implicit` = LLM이 맥락에서 식별 |
| `action_items[].priority` | string | `high` / `medium` / `low` |
| `action_items[].category` | string | `development` / `design` / `review` / `research` / `admin` |
| `unresolved[].topic` | string | 결론 없이 끝난 토론 주제 |

---

## Schema B: Intermediate Data (raw_data.json)

extract.py가 Phase 1-2에서 생성하는 중간 데이터입니다.

```json
{
  "meta": {
    "source_file": "string",
    "extraction_timestamp": "ISO 8601 datetime"
  },
  "attendees_raw": ["string"],
  "explicit_actions": [
    {
      "line_number": 0,
      "matched_keyword": "string",
      "text": "string"
    }
  ],
  "decisions_raw": [
    {
      "line_number": 0,
      "matched_keyword": "string",
      "text": "string"
    }
  ],
  "dates_found": [
    {
      "line_number": 0,
      "date_text": "string"
    }
  ],
  "tracker_refs": [
    {
      "line_number": 0,
      "tracker_id": "string",
      "context": "string"
    }
  ],
  "sections": [
    {
      "header": "string",
      "start_line": 0,
      "content": "string"
    }
  ],
  "full_text": "string"
}
```

---

## Schema C: Final Report (action_report.json)

generate.py가 Phase 3에서 생성하는 최종 보고서입니다.

```json
{
  "meta": {
    "meeting_title": "string",
    "meeting_date": "string",
    "attendees": ["string"],
    "generated_at": "ISO 8601 datetime"
  },
  "summary": "string",
  "decisions": [],
  "action_items": [],
  "unresolved": [],
  "tracker_updates": [],
  "statistics": {
    "total_actions": 0,
    "by_priority": { "high": 0, "medium": 0, "low": 0 },
    "by_category": {},
    "by_owner": {},
    "explicit_count": 0,
    "implicit_count": 0
  }
}
```
