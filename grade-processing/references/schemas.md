# 데이터 스키마

## Schema A: LLM 출력 (judged_data.json)

```json
{
  "meta": {
    "student_count": 10,
    "at_risk_count": 3
  },
  "results": [
    {
      "student_id": "2024001",
      "name": "김민준",
      "midterm": 85,
      "final": 92,
      "assignment_avg": 91.0,
      "attendance_pct": 100,
      "total_score": 89.2,
      "grade": "B+",
      "comment": "LLM이 생성한 개인화된 코멘트"
    }
  ],
  "at_risk": [
    {
      "student_id": "2024006",
      "name": "강하은",
      "total_score": 45.9,
      "grade": "F",
      "issues": ["총점 미달", "출석 부족"],
      "recommendation": "LLM이 생성한 개입 권고"
    }
  ],
  "statistics": {
    "student_count": 10,
    "score_avg": 76.5,
    "score_max": 97.4,
    "score_min": 45.9,
    "at_risk_count": 3,
    "grade_distribution": {"A+": 1, "A": 1, "B+": 2, ...},
    "attendance_avg": 89.5,
    "class_insight": "LLM이 생성한 반 전체 인사이트"
  }
}
```

## Schema B: 중간 데이터 (extracted_data.json)

Phase 1-2에서 생성. Schema A와 동일하나 `comment`, `recommendation`, `class_insight` 필드 없음.

## Schema C: Template 구조

Excel 템플릿 (`templates/template.xlsx`)의 시트별 헤더:

### 성적표 시트 (Row 4)
학번 | 이름 | 중간고사 | 기말고사 | 과제평균 | 출석률 | 총점 | 등급 | 코멘트

### 반 요약 시트 (Row 3)
- 좌측: 항목 | 값 | 비고
- 우측: 등급 | 인원 | 비율

### 관찰 대상 시트 (Row 3)
학번 | 이름 | 총점 | 등급 | 주요 문제 | 권고 사항
