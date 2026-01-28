# 데이터 스키마

## Schema A: LLM 출력 (judged_data.json)

```json
{
  "meta": {
    "total_items": 12,
    "total_amount": 3500000,
    "processing_date": "2026-01-28T15:00:00"
  },
  "items": [
    {
      "id": "INV-001",
      "date": "2025-01-15",
      "vendor": "스타벅스 강남역점",
      "description": "팀 미팅 커피",
      "amount": 25200,
      "category": "식비",
      "gl_code": "GL-5300",
      "policy_status": "APPROVED",
      "rationale": "LLM 판단 근거",
      "flag": null
    }
  ],
  "summary": {
    "by_category": {"식비": {"count": 3, "total": 530200}, ...},
    "by_status": {"APPROVED": 8, "PENDING": 2, "FLAG": 1, "REVIEW": 1},
    "flagged_items": ["INV-005", "INV-009"],
    "overall_assessment": "LLM 종합 평가"
  }
}
```

## Schema B: 중간 데이터 (extracted_data.json)

```json
{
  "meta": { ... },
  "items": [
    {
      "id": "INV-001",
      "date": "2025-01-15",
      "vendor": "스타벅스 강남역점",
      "description": "팀 미팅 커피",
      "amount": 25200,
      "category_hint": "식비",
      "gl_code_hint": "GL-5300",
      "policy_flag": "NONE | OVER_LIMIT | DUPLICATE_SUSPECT | OUTLIER"
    }
  ]
}
```

## Schema C: Template 구조

Excel 템플릿 (`templates/template.xlsx`) 시트별 헤더:

### 요약 시트 (Row 3)
- 좌측: 카테고리 | GL코드 | 건수 | 합계 | 비율
- 우측: 상태 | 건수

### 상세 시트 (Row 3)
번호 | 날짜 | 거래처 | 내역 | 금액 | GL코드 | 카테고리 | 정책상태 | 비고

### 플래그 시트 (Row 3)
번호 | 날짜 | 거래처 | 내역 | 금액 | 상태 | 사유 | 조치
