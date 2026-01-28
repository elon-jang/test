# Before/After Examples - 경비 분류 판단 보정

> LLM이 경비 항목을 분류할 때 참고하는 판단 예시 5건

## Example 1: 정상 승인 (단순 건)

**Before** (Script 추출):
```json
{
  "date": "2025-01-15",
  "vendor": "스타벅스 강남역점",
  "description": "팀 미팅 커피",
  "amount": 25200,
  "category_hint": "식비",
  "gl_code_hint": "GL-5300",
  "policy_flag": "NONE"
}
```

**After** (LLM 판단):
```json
{
  "category": "식비",
  "gl_code": "GL-5300",
  "policy_status": "APPROVED",
  "rationale": "팀 미팅 중 음료 구매. 식비 한도(100,000원) 이내. 업무 관련성 명확.",
  "flag": null
}
```
> 포인트: 카테고리 힌트와 일치, 한도 이내, 단순 승인

---

## Example 2: 한도 초과 → PENDING

**Before**:
```json
{
  "date": "2025-01-20",
  "vendor": "한우마을",
  "description": "부서 신년회 회식 (8명)",
  "amount": 480000,
  "category_hint": "식비",
  "gl_code_hint": "GL-5300",
  "policy_flag": "OVER_LIMIT"
}
```

**After**:
```json
{
  "category": "식비",
  "gl_code": "GL-5300",
  "policy_status": "PENDING",
  "rationale": "식비 건당 한도(100,000원) 4.8배 초과. 단체 회식(8명)으로 1인당 60,000원은 합리적 수준이나 사전승인 필요.",
  "flag": "한도초과: 480,000원 > 100,000원. 부서 회식 사전승인 확인 필요."
}
```
> 포인트: 한도 초과지만 1인당 금액은 합리적 → PENDING(거부가 아님). 맥락 고려.

---

## Example 3: 중복 의심 → FLAG

**Before** (두 건):
```json
[
  {
    "date": "2025-01-22",
    "vendor": "카카오택시",
    "description": "고객사 미팅 이동",
    "amount": 45000,
    "category_hint": "교통비",
    "gl_code_hint": "GL-5100",
    "policy_flag": "DUPLICATE_SUSPECT"
  },
  {
    "date": "2025-01-22",
    "vendor": "카카오택시",
    "description": "사무실 복귀",
    "amount": 45000,
    "category_hint": "교통비",
    "gl_code_hint": "GL-5100",
    "policy_flag": "DUPLICATE_SUSPECT"
  }
]
```

**After**:
```json
[
  {
    "category": "교통비",
    "gl_code": "GL-5100",
    "policy_status": "APPROVED",
    "rationale": "같은 날 동일 금액이나, '고객사 미팅 이동'과 '사무실 복귀'로 왕복 이용이 확인됨. 중복이 아닌 정상 왕복.",
    "flag": null
  },
  {
    "category": "교통비",
    "gl_code": "GL-5100",
    "policy_status": "APPROVED",
    "rationale": "상기 건의 복귀편. 왕복 택시 이용으로 판단.",
    "flag": null
  }
]
```
> 포인트: 동일 날짜+금액이지만 내역 확인 시 왕복 이용 → 중복 아님. **내역(description)을 반드시 확인**

---

## Example 4: 카테고리 재분류 + 사전승인

**Before**:
```json
{
  "date": "2025-01-10",
  "vendor": "Adobe Inc.",
  "description": "Creative Cloud 연간 구독",
  "amount": 792000,
  "category_hint": "기타",
  "gl_code_hint": "GL-5900",
  "policy_flag": "OVER_LIMIT"
}
```

**After**:
```json
{
  "category": "소프트웨어",
  "gl_code": "GL-5200",
  "policy_status": "PENDING",
  "rationale": "Script가 '기타'로 분류했으나 Adobe Creative Cloud는 소프트웨어 구독. GL-5200 재분류. 소프트웨어 한도(500,000원) 초과로 사전승인 필요.",
  "flag": "카테고리 재분류: 기타→소프트웨어. 사전승인 필요: 792,000원 > 500,000원."
}
```
> 포인트: Script의 카테고리 힌트가 부정확할 수 있음 → LLM이 재분류. **vendor+description으로 정확한 카테고리 판단**

---

## Example 5: 이상치 → REVIEW

**Before**:
```json
{
  "date": "2025-01-25",
  "vendor": "쿠팡",
  "description": "사무실 비품 구매",
  "amount": 1250000,
  "category_hint": "사무용품",
  "gl_code_hint": "GL-5400",
  "policy_flag": "OUTLIER"
}
```

**After**:
```json
{
  "category": "사무용품",
  "gl_code": "GL-5400",
  "policy_status": "REVIEW",
  "rationale": "사무용품 한도(300,000원) 4.2배 초과. '사무실 비품'이라는 내역이 모호하며 구체적 품목 미기재. 금액 규모로 볼 때 자산 계정(GL-1400) 분류 가능성도 있음.",
  "flag": "이상치: 1,250,000원은 사무용품 평균 대비 현저히 높음. 품목 상세 확인 필요. 자산 vs 비용 구분 검토."
}
```
> 포인트: 큰 금액 + 모호한 내역 → REVIEW. **자산/비용 구분 가능성까지 제시**
